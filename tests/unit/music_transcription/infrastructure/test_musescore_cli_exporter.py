"""Unit tests for MuseScoreCliExporter adapter."""

from pathlib import Path

import pytest

from mus.music_transcription.infrastructure.musescore_cli_exporter import (
    MuseScoreCliExporter,
)
from mus.shared_kernel.errors import ExternalToolMissingError


def test_musescore_cli_exporter_builds_correct_argv(tmp_path: Path) -> None:
    executed_commands: list[list[str]] = []

    def fake_runner(cmd: list[str]) -> int:
        executed_commands.append(cmd)
        return 0

    exporter = MuseScoreCliExporter(
        binary_path="musescore",
        command_runner=fake_runner,
        check_binary_exists=False,
    )

    midi_path = tmp_path / "song.mid"
    midi_path.touch()
    out_score = tmp_path / "song.mscz"

    result = exporter.export_score(midi_path, out_score)

    assert result == out_score
    assert len(executed_commands) == 1
    assert executed_commands[0] == ["musescore", "-o", str(out_score), str(midi_path)]


def test_musescore_cli_exporter_raises_on_non_zero_exit(tmp_path: Path) -> None:
    def failing_runner(cmd: list[str]) -> int:
        return 1

    exporter = MuseScoreCliExporter(
        binary_path="musescore",
        command_runner=failing_runner,
        check_binary_exists=False,
    )

    midi_path = tmp_path / "song.mid"
    midi_path.touch()
    out_score = tmp_path / "song.musicxml"

    with pytest.raises(RuntimeError, match="MuseScore command failed with exit code 1"):
        exporter.export_score(midi_path, out_score)


def test_musescore_cli_exporter_raises_when_binary_missing(tmp_path: Path) -> None:
    with pytest.raises(ExternalToolMissingError):
        MuseScoreCliExporter(binary_path="non_existent_musescore_binary_xyz_123")
