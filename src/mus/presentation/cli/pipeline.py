import re
from pathlib import Path

import typer

from mus.config import get_settings
from mus.music_transcription.application.use_cases.transcribe_contour import (
    TranscribeContour,
    TranscribeContourCommand,
)
from mus.shared_kernel.playlist import load_youtube_playlist
from mus.shared_kernel.units import Hertz, SampleRate, Semitones
from mus.stem_separation.application.use_cases.ingest_and_separate import (
    IngestAndSeparateCommand,
    IngestAndSeparateTrack,
)
from mus.stem_separation.infrastructure.demucs_stem_separator import DemucsStemSeparator
from mus.stem_separation.infrastructure.json_catalog_history import JsonCatalogHistory
from mus.stem_separation.infrastructure.ollama_metadata_tagger import OllamaMetadataTagger
from mus.stem_separation.infrastructure.yt_dlp_audio_downloader import YtDlpAudioDownloader
from mus.voice_modeling.application.use_cases.decompose_voice import (
    DecomposeVoice,
    DecomposeVoiceCommand,
)
from mus.voice_modeling.application.use_cases.reshape_formants import (
    ReshapeFormants,
    ReshapeFormantsCommand,
)
from mus.voice_modeling.application.use_cases.resynthesize_voice import (
    ResynthesizeVoice,
    ResynthesizeVoiceCommand,
)
from mus.voice_modeling.domain.phonetics import VocalTractScale
from mus.voice_modeling.domain.pitch_modulation import transpose
from mus.voice_modeling.infrastructure.npz_voice_cache import NpzVoiceCache
from mus.voice_modeling.infrastructure.pyworld_vocoder import PyWorldVocoder
from mus.voice_modeling.infrastructure.soundfile_audio_io import SoundfileAudioIO

app = typer.Typer(help="End-to-end ingestion, decomposition, and resynthesis pipeline.")


def is_track_fully_processed(source: str, stems_dir: Path, history_file: Path) -> bool:
    """Checks if a track has already been fully processed with all expected artifacts."""
    catalog = JsonCatalogHistory(history_file=history_file)
    tracks = catalog._cache.get("tracks", {})

    # 1. Match by YouTube video ID in catalog history
    vid_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", source)
    video_id = vid_match.group(1) if vid_match else None

    if video_id and video_id in tracks:
        entry = tracks[video_id]
        genre = entry.get("genre", "Unknown")
        target_dir = stems_dir / genre
        if target_dir.exists():
            for v_path in target_dir.glob("*vocals.mp3"):
                synt_path = v_path.parent / f"{v_path.stem} - synt.mp3"
                midi_path = v_path.parent / f"{v_path.stem}.mid"
                if synt_path.exists() and midi_path.exists():
                    return True

    # 2. Match by file path or local file name
    source_stem = Path(source).stem
    if stems_dir.exists():
        for v_path in stems_dir.rglob(f"*{source_stem}*vocals.mp3"):
            synt_path = v_path.parent / f"{v_path.stem} - synt.mp3"
            midi_path = v_path.parent / f"{v_path.stem}.mid"
            if synt_path.exists() and midi_path.exists():
                return True

    return False


@app.command()
def run(  # noqa: PLR0915, PLR0917
    source: str | None = typer.Argument(
        None,
        help="YouTube URL, local audio file, or playlist.txt. If omitted, reads from playlist.",
    ),
    output_dir: Path = typer.Option(Path("./outputs"), "--out", "-o", help="Output directory"),
    to_midi: bool = typer.Option(True, "--midi/--no-midi", help="Transcribe vocal melody to MIDI"),
    bpm: float = typer.Option(120.0, "--bpm", help="Initial tempo BPM for transcription"),
    transpose_st: float | None = typer.Option(
        None, "--transpose", "-t", help="Transpose vocal stem"
    ),
    scale_alpha: float | None = typer.Option(
        None, "--alpha", "-a", help="Scale vocal tract formants"
    ),
    limit: int | None = typer.Option(
        None, "--limit", "-l", help="Limit number of tracks from playlist to process"
    ),
) -> None:
    """Runs the complete end-to-end pipeline from audio/URL to stems, MIDI, and modulated voice."""
    settings = get_settings()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    sources: list[str] = []
    if source is None:
        playlist_path = settings.PLAYLIST_FILE
        if not playlist_path.exists() and Path("./data/playlist.txt").exists():
            playlist_path = Path("./data/playlist.txt").resolve()
        typer.echo(f"No source specified. Loading playlist: {playlist_path}")
        sources = load_youtube_playlist(playlist_path)
    elif source.endswith(".txt") and Path(source).is_file():
        typer.echo(f"Loading playlist file: {source}")
        sources = load_youtube_playlist(Path(source))
    else:
        sources = [source]

    if not sources:
        typer.secho("No valid sources or YouTube URLs found to process.", fg=typer.colors.RED)
        raise typer.Exit(code=1)

    if limit is not None and limit > 0:
        sources = sources[:limit]

    typer.echo(f"Total track(s) to process: {len(sources)}")

    for idx, target_source in enumerate(sources, start=1):
        if is_track_fully_processed(target_source, output_dir / "stems", settings.HISTORY_FILE):
            typer.secho(
                f"\n=== [{idx}/{len(sources)}] ⚡ [Skipped] Already completed: {target_source} ===",
                fg=typer.colors.YELLOW,
            )
            continue

        typer.echo(f"\n=== [{idx}/{len(sources)}] Starting MUS Pipeline for: {target_source} ===")

        # Step 1: Ingestion & Stem Separation
        tagger = OllamaMetadataTagger(
            ollama_host=settings.OLLAMA_HOST,
            model=settings.OLLAMA_MODEL,
        )
        downloader = YtDlpAudioDownloader()
        separator = DemucsStemSeparator(model_name="htdemucs_6s")
        catalog = JsonCatalogHistory(history_file=settings.HISTORY_FILE)

        ingest_uc = IngestAndSeparateTrack(
            downloader=downloader,
            tagger=tagger,
            separator=separator,
            catalog=catalog,
            vram_cleaner=tagger.unload_vram,
        )

        stems = ingest_uc.execute(
            IngestAndSeparateCommand(
                source=target_source,
                output_dir=output_dir / "stems",
            )
        )
        vocal_stem_path = stems.vocals_path
        typer.echo(f"✓ Vocal stem isolated: {vocal_stem_path}")

        # Step 2: Voice Decomposition
        reader = SoundfileAudioIO()
        writer = SoundfileAudioIO()
        vocoder = PyWorldVocoder()
        cache = NpzVoiceCache(cache_dir=settings.OUTPUT_DIR / "cache")

        target_sr = SampleRate(settings.SAMPLE_RATE)
        signal = reader.read(vocal_stem_path, target_rate=target_sr)

        decompose_uc = DecomposeVoice(vocoder=vocoder, cache=cache)
        voice = decompose_uc.execute(
            DecomposeVoiceCommand(
                signal=signal,
                f0_floor=Hertz(settings.F0_FLOOR_HZ),
                f0_ceil=Hertz(settings.F0_CEIL_HZ),
                method=settings.F0_ESTIMATOR,
                cache_key=vocal_stem_path.stem,
            )
        )
        typer.echo(
            f"✓ Parametric voice decomposed: {voice.n_frames} frames "
            f"({voice.duration_seconds:.2f}s)"
        )

        # Step 3: Symbolic Transcription (Track A: Monophonic Vocal Lead -> MIDI Choir Aahs GM 52)
        if to_midi:
            midi_path = vocal_stem_path.parent / f"{vocal_stem_path.stem}.mid"
            transcribe_uc = TranscribeContour()
            sequence = transcribe_uc.execute(
                TranscribeContourCommand(
                    contour=voice.f0,
                    tempo_bpm=bpm,
                    output_midi_path=midi_path,
                    program_number=52,  # Choir Aahs GM 52
                )
            )
            typer.echo(
                f"✓ Transcribed {len(sequence.notes)} notes to MIDI (GM 52 Choir Aahs): {midi_path}"
            )

        # Step 4: Parametric Modulation & Resynthesis (ADR-002 D2, D4)
        modulated_voice = voice
        if transpose_st is not None:
            shifted_f0 = transpose(modulated_voice.f0, Semitones(transpose_st))
            modulated_voice = modulated_voice.with_f0(shifted_f0)
            typer.echo(f"✓ Pitch transposed by {transpose_st:+.1f} semitones")

        if scale_alpha is not None:
            reshape_uc = ReshapeFormants()
            modulated_voice = reshape_uc.execute(
                ReshapeFormantsCommand(
                    voice=modulated_voice,
                    tract_scale=VocalTractScale(scale_alpha),
                )
            )
            typer.echo(f"✓ Vocal tract scaled with alpha={scale_alpha:.2f}")

        # Always synthesize and persist the vocal take as MP3 alongside stems (SPEC-002 S3)
        resynth_out = vocal_stem_path.parent / f"{vocal_stem_path.stem} - synt.mp3"
        resynth_uc = ResynthesizeVoice(vocoder=vocoder, writer=writer)
        resynth_uc.execute(
            ResynthesizeVoiceCommand(
                voice=modulated_voice,
                output_path=resynth_out,
            )
        )
        typer.echo(f"✓ Resynthesized vocal stem saved to: {resynth_out}")

    typer.echo("=== Pipeline Run Finished Successfully ===")
