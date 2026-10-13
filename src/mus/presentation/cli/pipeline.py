"""Unified end-to-end pipeline CLI commands (ADR-001 D12)."""

from pathlib import Path

import typer

from mus.config import get_settings
from mus.music_transcription.application.use_cases.transcribe_contour import (
    TranscribeContour,
    TranscribeContourCommand,
)
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


@app.command()
def run(  # noqa: PLR0917
    source: str = typer.Argument(..., help="YouTube video/playlist URL or local audio file"),
    output_dir: Path = typer.Option(Path("./outputs"), "--out", "-o", help="Output directory"),
    to_midi: bool = typer.Option(True, "--midi/--no-midi", help="Transcribe vocal melody to MIDI"),
    bpm: float = typer.Option(120.0, "--bpm", help="Initial tempo BPM for transcription"),
    transpose_st: float | None = typer.Option(
        None, "--transpose", "-t", help="Transpose vocal stem"
    ),
    scale_alpha: float | None = typer.Option(
        None, "--alpha", "-a", help="Scale vocal tract formants"
    ),
) -> None:
    """Runs the complete end-to-end pipeline from audio/URL to stems, MIDI, and modulated voice."""
    settings = get_settings()
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(f"=== Starting MUS Pipeline for: {source} ===")

    # Step 1: Ingestion & Stem Separation
    tagger = OllamaMetadataTagger(ollama_host=settings.OUTPUT_DIR.as_uri())  # or config
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
            source=source,
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
        f"✓ Parametric voice decomposed: {voice.n_frames} frames ({voice.duration_seconds:.2f}s)"
    )

    # Step 3: Symbolic Transcription (Track A: Monophonic Vocal Lead -> MIDI Choir Aahs GM 52)
    if to_midi:
        midi_path = output_dir / f"{vocal_stem_path.stem}.mid"
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

    # Step 4: Optional Parametric Modulation (Pitch Transpose & Vocal Tract Scale)
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

    if transpose_st is not None or scale_alpha is not None:
        resynth_out = output_dir / f"{vocal_stem_path.stem}_modulated.wav"
        resynth_uc = ResynthesizeVoice(vocoder=vocoder, writer=writer)
        resynth_uc.execute(
            ResynthesizeVoiceCommand(
                voice=modulated_voice,
                output_path=resynth_out,
            )
        )
        typer.echo(f"✓ Modulated vocal resynthesized and saved to: {resynth_out}")

    typer.echo("=== Pipeline Run Finished Successfully ===")
