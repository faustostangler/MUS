"""CLI subcommands for voice analysis, modulation, and resynthesis."""

from pathlib import Path

import typer

from mus.config import get_settings
from mus.shared_kernel.units import Hertz, SampleRate, Semitones
from mus.voice_modeling.application.use_cases.decompose_voice import (
    DecomposeVoice,
    DecomposeVoiceCommand,
)
from mus.voice_modeling.application.use_cases.resynthesize_voice import (
    ResynthesizeVoice,
    ResynthesizeVoiceCommand,
)
from mus.voice_modeling.domain.pitch_modulation import transpose
from mus.voice_modeling.infrastructure.npz_voice_cache import NpzVoiceCache
from mus.voice_modeling.infrastructure.pyworld_vocoder import PyWorldVocoder
from mus.voice_modeling.infrastructure.soundfile_audio_io import SoundfileAudioIO

app = typer.Typer(help="Voice modeling and modulation commands.")


@app.command()
def analyze(
    audio_path: Path = typer.Argument(..., help="Path to vocal audio file (WAV or MP3)"),
    method: str = typer.Option("dio", help="Pitch estimation algorithm (dio or harvest)"),
) -> None:
    """Decomposes a vocal stem into a ParametricVoice and caches it."""
    settings = get_settings()
    reader = SoundfileAudioIO()
    vocoder = PyWorldVocoder()
    cache = NpzVoiceCache(cache_dir=settings.OUTPUT_DIR / "cache")

    target_sr = SampleRate(settings.SAMPLE_RATE)
    signal = reader.read(audio_path, target_rate=target_sr)

    cache_key = audio_path.stem
    use_case = DecomposeVoice(vocoder=vocoder, cache=cache)
    voice = use_case.execute(
        DecomposeVoiceCommand(
            signal=signal,
            f0_floor=Hertz(settings.F0_FLOOR_HZ),
            f0_ceil=Hertz(settings.F0_CEIL_HZ),
            method=method,
            cache_key=cache_key,
        )
    )

    voiced_ratio = float((voice.f0.f0 > 0).mean()) * 100.0
    typer.echo(
        f"✓ Analisado com sucesso: {voice.n_frames} frames ({voice.duration_seconds:.2f}s) | "
        f"Voiced: {voiced_ratio:.1f}% | Cache salvo: {cache_key}.npz"
    )


@app.command()
def transpose_voice(
    audio_path: Path = typer.Argument(..., help="Input audio or cached voice key"),
    semitones: float = typer.Option(..., "--semitones", "-s", help="Semitones shift [-24, 24]"),
    output_path: Path = typer.Option(..., "--out", "-o", help="Target output WAV path"),
) -> None:
    """Transposes a vocal stem without modifying its formants (no chipmunk effect)."""
    settings = get_settings()
    reader = SoundfileAudioIO()
    writer = SoundfileAudioIO()
    vocoder = PyWorldVocoder()
    cache = NpzVoiceCache(cache_dir=settings.OUTPUT_DIR / "cache")

    target_sr = SampleRate(settings.SAMPLE_RATE)
    cache_key = audio_path.stem
    voice = cache.load(cache_key)

    if voice is None:
        signal = reader.read(audio_path, target_rate=target_sr)
        decompose_uc = DecomposeVoice(vocoder=vocoder, cache=cache)
        voice = decompose_uc.execute(
            DecomposeVoiceCommand(
                signal=signal,
                method=settings.F0_ESTIMATOR,
                cache_key=cache_key,
            )
        )

    # Apply pure pitch transposition
    shifted_f0 = transpose(voice.f0, Semitones(semitones))
    transposed_voice = voice.with_f0(shifted_f0)

    # Resynthesize and write
    resynth_uc = ResynthesizeVoice(vocoder=vocoder, writer=writer)
    resynth_uc.execute(
        ResynthesizeVoiceCommand(
            voice=transposed_voice,
            output_path=output_path,
        )
    )

    typer.echo(f"✓ Faixa transposta em {semitones:+.1f} semitons e salva em: {output_path}")
