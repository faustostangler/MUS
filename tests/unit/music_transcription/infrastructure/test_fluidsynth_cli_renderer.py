"""Unit tests for FluidSynthCliRenderer adapter."""

from pathlib import Path

import pytest

from mus.music_transcription.infrastructure.fluidsynth_cli_renderer import (
    FluidSynthCliRenderer,
)
from mus.shared_kernel.errors import ConfigurationError, ExternalToolMissingError


def test_fluidsynth_cli_renderer_builds_correct_argv(tmp_path: Path) -> None:
    executed_commands: list[list[str]] = []

    def fake_runner(cmd: list[str]) -> int:
        executed_commands.append(cmd)
        return 0

    sf2_path = tmp_path / "soundfont.sf2"
    sf2_path.touch()

    renderer = FluidSynthCliRenderer(
        soundfont_path=sf2_path,
        binary_path="fluidsynth",
        command_runner=fake_runner,
        check_binary_exists=False,
    )

    midi_path = tmp_path / "song.mid"
    midi_path.touch()
    out_wav = tmp_path / "song.wav"

    result = renderer.render_midi(
        midi_path=midi_path,
        output_wav_path=out_wav,
        sample_rate=44100,
        gain=0.2,
    )

    assert result == out_wav
    assert len(executed_commands) == 1
    # Command per S4A-01: ["fluidsynth", "-ni", "-F", out, "-r", sr, "-g", gain, sf2, mid]
    expected_cmd = [
        "fluidsynth",
        "-ni",
        "-F",
        str(out_wav),
        "-r",
        "44100",
        "-g",
        "0.2",
        str(sf2_path),
        str(midi_path),
    ]
    assert executed_commands[0] == expected_cmd


def test_fluidsynth_cli_renderer_raises_configuration_error_when_soundfont_missing(
    tmp_path: Path,
) -> None:
    missing_sf2 = tmp_path / "non_existent.sf2"

    with pytest.raises(ConfigurationError, match="SoundFont file not found"):
        FluidSynthCliRenderer(
            soundfont_path=missing_sf2,
            binary_path="fluidsynth",
            check_binary_exists=False,
        )


def test_fluidsynth_cli_renderer_raises_when_binary_missing(tmp_path: Path) -> None:
    sf2_path = tmp_path / "soundfont.sf2"
    sf2_path.touch()

    with pytest.raises(ExternalToolMissingError):
        FluidSynthCliRenderer(
            soundfont_path=sf2_path,
            binary_path="non_existent_fluidsynth_binary_xyz_123",
        )
