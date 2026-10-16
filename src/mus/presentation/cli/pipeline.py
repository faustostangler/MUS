import re
from pathlib import Path

import typer

from mus.config import get_settings
from mus.music_transcription.application.use_cases.transcribe_all_stems import (
    SynthesizeStemMidi,
    SynthesizeStemMidiCommand,
    TranscribeStem,
    TranscribeStemCommand,
)
from mus.music_transcription.application.use_cases.transcribe_contour import (
    TranscribeContour,
    TranscribeContourCommand,
)
from mus.shared_kernel.metrics import estimate_song_metrics
from mus.shared_kernel.playlist import load_youtube_playlist
from mus.shared_kernel.units import Hertz, SampleRate, Semitones
from mus.stem_separation.application.use_cases.ingest_and_separate import (
    IngestAndSeparateCommand,
    IngestAndSeparateTrack,
    sanitize_genre,
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


def is_track_fully_processed(source: str, library_dir: Path, history_file: Path) -> bool:
    """Checks if a track has already been fully processed with all expected artifacts."""
    catalog = JsonCatalogHistory(history_file=history_file)
    tracks = catalog._cache.get("tracks", {})

    # 1. Match by YouTube video ID in catalog history
    vid_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11})", source)
    video_id = vid_match.group(1) if vid_match else None

    if video_id and video_id in tracks:
        entry = tracks[video_id]
        genre = sanitize_genre(entry.get("genre", "unknown"))
        target_dir = library_dir / genre
        track_name = entry.get("track", "")
        search_dirs = [target_dir] if target_dir.exists() else []
        if library_dir.exists() and library_dir not in search_dirs:
            search_dirs.append(library_dir)
        for s_dir in search_dirs:
            for v_path in s_dir.rglob("*vocals.mp3"):
                if track_name and track_name.lower() not in v_path.name.lower():
                    continue
                prefix = v_path.name.rsplit(" - vocals.mp3", 1)[0]
                stem_dir = v_path.parent
                stem_files = [
                    f
                    for f in stem_dir.iterdir()
                    if f.is_file()
                    and f.name.startswith(f"{prefix} - ")
                    and f.name.endswith(".mp3")
                    and not f.name.endswith("- mid.mp3")
                ]
                if stem_files and all(
                    f.with_suffix(".mid").exists() and (f.parent / f"{f.stem} - mid.mp3").exists()
                    for f in stem_files
                ):
                    return True

    # 2. Match by file path or local file name
    source_stem = Path(source).stem
    if library_dir.exists():
        for v_path in library_dir.rglob(f"*{source_stem}*vocals.mp3"):
            prefix = v_path.name.rsplit(" - vocals.mp3", 1)[0]
            stem_dir = v_path.parent
            stem_files = [
                f
                for f in stem_dir.iterdir()
                if f.is_file()
                and f.name.startswith(f"{prefix} - ")
                and f.name.endswith(".mp3")
                and not f.name.endswith("- mid.mp3")
            ]
            if stem_files and all(
                f.with_suffix(".mid").exists() and (f.parent / f"{f.stem} - mid.mp3").exists()
                for f in stem_files
            ):
                return True

    return False


@app.command()
def run(  # noqa: PLR0912, PLR0915, PLR0917
    source: str | None = typer.Argument(
        None,
        help="YouTube URL, local audio file, or playlist.txt. If omitted, reads from playlist.",
    ),
    output_dir: Path = typer.Option(Path("./library"), "--out", "-o", help="Output directory"),
    to_midi: bool = typer.Option(True, "--midi/--no-midi", help="Transcribe vocal melody to MIDI"),
    bpm: float | None = typer.Option(
        None, "--bpm", help="Initial tempo BPM for transcription (auto-detected if omitted)"
    ),
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
    library_dir = output_dir
    library_dir.mkdir(parents=True, exist_ok=True)

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
        if is_track_fully_processed(target_source, library_dir, settings.HISTORY_FILE):
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
            timeout=settings.OLLAMA_TIMEOUT_SECONDS,
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
                output_dir=library_dir,
            )
        )
        vocal_stem_path = stems.vocals_path
        typer.echo(f"✓ Vocal stem isolated: {vocal_stem_path}")

        # Step 2: Voice Decomposition
        reader = SoundfileAudioIO()
        writer = SoundfileAudioIO()
        vocoder = PyWorldVocoder()
        cache = NpzVoiceCache(cache_dir=library_dir / "cache")

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

        # Resolve unified SongMetrics (BPM, duration, time signature) across all stems (ADR-005)
        ref_signal = signal
        if stems.other_stems and "drums" in stems.other_stems:
            try:
                ref_signal = reader.read(stems.other_stems["drums"], target_rate=target_sr)
            except Exception:
                ref_signal = signal

        song_metrics = estimate_song_metrics(ref_signal, preferred_bpm=bpm)
        meter_str = (
            f"{song_metrics.time_signature_numerator}/{song_metrics.time_signature_denominator}"
        )
        typer.echo(
            f"✓ Song metrics resolved: {song_metrics.tempo_bpm} BPM, "
            f"{meter_str} meter, {song_metrics.duration_seconds:.2f}s duration"
        )

        # Step 3: Symbolic Transcription (Track A: Monophonic Vocal Lead -> MIDI Choir Aahs GM 52)
        if to_midi:
            midi_path = vocal_stem_path.parent / f"{vocal_stem_path.stem}.mid"
            transcribe_uc = TranscribeContour()
            sequence = transcribe_uc.execute(
                TranscribeContourCommand(
                    contour=voice.f0,
                    tempo_bpm=song_metrics.tempo_bpm,
                    output_midi_path=midi_path,
                    program_number=52,  # Choir Aahs GM 52
                    song_metrics=song_metrics,
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
        resynth_out = vocal_stem_path.parent / f"{vocal_stem_path.stem} - mid.mp3"
        resynth_uc = ResynthesizeVoice(vocoder=vocoder, writer=writer)
        resynth_uc.execute(
            ResynthesizeVoiceCommand(
                voice=modulated_voice,
                output_path=resynth_out,
            )
        )
        typer.echo(f"✓ Resynthesized vocal stem saved to: {resynth_out}")

        # Step 5: Multi-Stem Transcription & Resynthesis for remaining stems (ADR-003 D1, D2)
        if to_midi and stems.other_stems:
            transcribe_stem_uc = TranscribeStem()
            synthesizer_uc = SynthesizeStemMidi(writer=writer)

            for stem_name, stem_path in stems.other_stems.items():
                stem_midi_path = stem_path.parent / f"{stem_path.stem}.mid"
                stem_signal = reader.read(stem_path, target_rate=target_sr)

                # Transcribe stem to MIDI
                transcribe_stem_uc.execute(
                    TranscribeStemCommand(
                        stem_name=stem_name,
                        audio=stem_signal,
                        output_midi_path=stem_midi_path,
                        song_metrics=song_metrics,
                    )
                )
                typer.echo(f"✓ Transcribed {stem_name} stem to MIDI: {stem_midi_path}")

                # Synthesize acoustic MP3 preview
                stem_synt_path = stem_path.parent / f"{stem_path.stem} - mid.mp3"
                synthesizer_uc.execute(
                    SynthesizeStemMidiCommand(
                        midi_path=stem_midi_path,
                        output_path=stem_synt_path,
                        sample_rate=target_sr,
                    )
                )
                typer.echo(f"✓ Synthesized {stem_name} stem saved to: {stem_synt_path}")

    typer.echo("=== Pipeline Run Finished Successfully ===")
