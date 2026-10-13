"""Unit tests for FluidSynthCliRenderer adapter in instrument_rendering context (ADR-001 D2)."""

from pathlib import Path

from mus.instrument_rendering.infrastructure.fluidsynth_cli_renderer import (
    FluidSynthCliRenderer,
)
from mus.shared_kernel.notes import NoteEvent, NoteSequence
from mus.shared_kernel.units import MidiPitch


def test_fluidsynth_renders_note_sequence(tmp_path: Path) -> None:
    """Verifies render() converts NoteSequence to temporary MIDI and invokes fluidsynth CLI."""
    executed_commands: list[list[str]] = []

    def fake_runner(cmd: list[str]) -> int:
        executed_commands.append(cmd)
        return 0

    sf2_path = tmp_path / "soundfont.sf2"
    sf2_path.touch()

    renderer = FluidSynthCliRenderer(
        soundfont_path=sf2_path,
        command_runner=fake_runner,
        check_binary_exists=False,
    )

    seq = NoteSequence(
        notes=[
            NoteEvent(pitch=MidiPitch(60), onset_seconds=0.0, offset_seconds=0.5),
            NoteEvent(pitch=MidiPitch(64), onset_seconds=0.5, offset_seconds=1.0),
        ],
        tempo_bpm=120.0,
    )

    out_wav = tmp_path / "rendered.wav"
    result = renderer.render(
        sequence=seq,
        output_wav_path=out_wav,
        soundfont_path=sf2_path,
        sample_rate=48000,
        gain=0.3,
        program_number=52,
    )

    assert result == out_wav
    assert len(executed_commands) == 1
    cmd = executed_commands[0]
    assert "-ni" in cmd
    assert "-F" in cmd
    assert str(out_wav) in cmd
    assert "-r" in cmd
    assert "48000" in cmd
    assert "-g" in cmd
    assert "0.3" in cmd
