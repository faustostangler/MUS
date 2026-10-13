"""MuseScore CLI adapter for sheet music score export (.mscz, .musicxml)."""

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from mus.music_transcription.application.ports import ScoreExporterPort
from mus.shared_kernel.errors import ExternalToolMissingError


def _default_subprocess_runner(cmd: list[str]) -> int:
    """Executes a subprocess command returning the exit code."""
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(
            f"MuseScore command failed with exit code {res.returncode}: {res.stderr.strip()}"
        )
    return res.returncode


class MuseScoreCliExporter(ScoreExporterPort):
    """Converts MIDI files to MuseScore scores (.mscz or .musicxml) via CLI."""

    def __init__(
        self,
        binary_path: str = "musescore",
        command_runner: Callable[[list[str]], int] | None = None,
        check_binary_exists: bool = True,
    ) -> None:
        self._binary_path = binary_path
        self._runner = command_runner or _default_subprocess_runner

        if check_binary_exists:
            resolved_bin = shutil.which(binary_path)
            if not resolved_bin:
                raise ExternalToolMissingError(
                    f"MuseScore binary '{binary_path}' not found in system PATH."
                )

    def export_score(self, midi_path: Path, output_path: Path) -> Path:
        """Converts a MIDI file to a score file and returns the generated score path."""
        midi_path = Path(midi_path).resolve()
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build command: ["musescore", "-o", out, mid]
        cmd = [self._binary_path, "-o", str(output_path), str(midi_path)]
        ret = self._runner(cmd)
        if ret != 0:
            raise RuntimeError(f"MuseScore command failed with exit code {ret}")
        return output_path
