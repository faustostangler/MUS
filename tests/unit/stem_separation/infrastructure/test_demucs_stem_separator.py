"""Unit tests for DemucsStemSeparator adapter."""

from pathlib import Path

from mus.stem_separation.infrastructure.demucs_stem_separator import DemucsStemSeparator


def test_demucs_stem_separator_command_and_file_resolution(tmp_path: Path) -> None:
    executed_commands: list[list[str]] = []

    def fake_runner(cmd: list[str]) -> None:
        executed_commands.append(cmd)
        # Emulate demucs output structure
        out_idx = cmd.index("-o")
        temp_dir = Path(cmd[out_idx + 1])
        model_idx = cmd.index("-n")
        model = cmd[model_idx + 1]

        # cmd[-1] is audio_path
        audio_stem = Path(cmd[-1]).stem
        stem_dir = temp_dir / model / audio_stem
        stem_dir.mkdir(parents=True, exist_ok=True)
        (stem_dir / "vocals.mp3").touch()
        (stem_dir / "drums.mp3").touch()
        (stem_dir / "bass.mp3").touch()

    separator = DemucsStemSeparator(
        model_name="htdemucs_6s",
        device="cpu",
        runner=fake_runner,
    )

    audio_file = tmp_path / "song.mp3"
    audio_file.touch()
    out_dir = tmp_path / "stems"

    stems = separator.separate(audio_path=audio_file, output_dir=out_dir)

    assert stems.vocals_path.exists()
    assert stems.vocals_path.name == "song - vocals.mp3"
    assert "drums" in stems.other_stems
    assert "bass" in stems.other_stems
    assert len(executed_commands) == 1
    assert "-n" in executed_commands[0]
    assert "htdemucs_6s" in executed_commands[0]
