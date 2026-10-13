"""CLI subcommands for acoustic instrument synthesis and rendering (Route 4A)."""

from pathlib import Path

import typer

from mus.config import get_settings
from mus.instrument_rendering.infrastructure.fluidsynth_cli_renderer import (
    FluidSynthCliRenderer,
)

app = typer.Typer(help="Acoustic instrument rendering commands (Route 4A).")


@app.command()
def audio(
    midi_path: Path = typer.Argument(..., help="Path to MIDI file"),
    output_path: Path = typer.Option(..., "--out", "-o", help="Target output WAV path"),
    gain: float = typer.Option(0.5, "--gain", "-g", help="FluidSynth master gain [0.0, 1.0]"),
) -> None:
    """Renders a MIDI file to an acoustic audio file using FluidSynth and SoundFont."""
    settings = get_settings()
    renderer = FluidSynthCliRenderer(soundfont_path=settings.SOUNDFONT_PATH)
    out = renderer.render_midi(
        midi_path=midi_path,
        output_wav_path=output_path,
        sample_rate=settings.SAMPLE_RATE,
        gain=gain,
    )
    typer.echo(f"✓ Rendered audio saved to: {out}")
