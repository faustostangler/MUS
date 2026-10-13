"""CLI subcommands for symbolic music transcription."""

from pathlib import Path

import typer

from mus.config import get_settings
from mus.music_transcription.application.use_cases.transcribe_contour import (
    TranscribeContour,
    TranscribeContourCommand,
)
from mus.music_transcription.infrastructure.musescore_cli_exporter import (
    MuseScoreCliExporter,
)
from mus.shared_kernel.units import SampleRate
from mus.voice_modeling.application.use_cases.decompose_voice import (
    DecomposeVoice,
    DecomposeVoiceCommand,
)
from mus.voice_modeling.infrastructure.npz_voice_cache import NpzVoiceCache
from mus.voice_modeling.infrastructure.pyworld_vocoder import PyWorldVocoder
from mus.voice_modeling.infrastructure.soundfile_audio_io import SoundfileAudioIO

app = typer.Typer(help="Symbolic music transcription and MIDI export commands.")


@app.command()
def to_midi(  # noqa: PLR0917
    audio_path: Path = typer.Argument(..., help="Vocal audio file path"),
    output_midi: Path = typer.Option(..., "--out", "-o", help="Target output .mid path"),
    bpm: float = typer.Option(120.0, "--bpm", help="Initial tempo BPM"),
    program: int = typer.Option(
        52, "--program", "-p", help="General MIDI program (default 52: Choir Aahs)"
    ),
    quantize: bool = typer.Option(False, "--quantize", "-q", help="Snap onsets to 1/16th grid"),
    bends: bool = typer.Option(False, "--bends", help="Extract residual pitch bends"),
) -> None:
    """Transcribes continuous vocal pitch contour to a discrete MIDI Type 1 file."""
    settings = get_settings()
    reader = SoundfileAudioIO()
    vocoder = PyWorldVocoder()
    cache = NpzVoiceCache(cache_dir=settings.OUTPUT_DIR / "cache")

    cache_key = audio_path.stem
    voice = cache.load(cache_key)
    signal = None

    if voice is None:
        target_sr = SampleRate(settings.SAMPLE_RATE)
        signal = reader.read(audio_path, target_rate=target_sr)
        decompose_uc = DecomposeVoice(vocoder=vocoder, cache=cache)
        voice = decompose_uc.execute(
            DecomposeVoiceCommand(
                signal=signal,
                method=settings.F0_ESTIMATOR,
                cache_key=cache_key,
            )
        )
    else:
        target_sr = SampleRate(settings.SAMPLE_RATE)
        if audio_path.exists():
            signal = reader.read(audio_path, target_rate=target_sr)

    transcriber = TranscribeContour()
    sequence = transcriber.execute(
        TranscribeContourCommand(
            contour=voice.f0,
            tempo_bpm=bpm,
            output_midi_path=output_midi,
            program_number=program,
            signal=signal,
            extract_pitch_bends=bends,
            quantize=quantize,
        )
    )

    typer.echo(
        f"✓ Transcription completed: {len(sequence.notes)} notes identified | "
        f"MIDI saved with GM program {program} at: {output_midi}"
    )


@app.command()
def to_score(
    midi_path: Path = typer.Argument(..., help="Source MIDI file path"),
    output_score: Path = typer.Option(
        ..., "--out", "-o", help="Target score path (.mscz or .musicxml)"
    ),
) -> None:
    """Exports a MIDI file to a sheet music score using MuseScore CLI (S2-10)."""
    exporter = MuseScoreCliExporter()
    out = exporter.export_score(midi_path, output_score)
    typer.echo(f"✓ Sheet music score exported to: {out}")
