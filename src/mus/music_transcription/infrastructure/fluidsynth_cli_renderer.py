"""FluidSynth CLI adapter for rendering MIDI to acoustic audio (Route 4A)."""

import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from mus.music_transcription.application.ports import SynthesizerPort
from mus.shared_kernel.errors import ConfigurationError, ExternalToolMissingError


def _default_subprocess_runner(cmd: list[str]) -> int:
    """Executes a subprocess command returning the exit code."""
    res = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if res.returncode != 0:
        raise RuntimeError(
            f"FluidSynth command failed with exit code {res.returncode}: {res.stderr.strip()}"
        )
    return res.returncode


class FluidSynthCliRenderer(SynthesizerPort):
    """Renders MIDI files to WAV using FluidSynth CLI and SoundFont banks."""

    def __init__(
        self,
        soundfont_path: Path,
        binary_path: str = "fluidsynth",
        command_runner: Callable[[list[str]], int] | None = None,
        check_binary_exists: bool = True,
    ) -> None:
        self._soundfont_path = Path(soundfont_path).resolve()
        self._binary_path = binary_path
        self._runner = command_runner or _default_subprocess_runner

        if not self._soundfont_path.is_file():
            raise ConfigurationError(
                f"SoundFont file not found at: {self._soundfont_path}. "
                "Ensure MUS_SOUNDFONT_PATH points to a valid .sf2 file."
            )

        if check_binary_exists:
            resolved_bin = shutil.which(binary_path)
            if not resolved_bin:
                raise ExternalToolMissingError(
                    f"FluidSynth binary '{binary_path}' not found in system PATH."
                )

    def render_midi(
        self,
        midi_path: Path,
        output_wav_path: Path,
        sample_rate: int = 44100,
        gain: float = 0.2,
    ) -> Path:
        """Renders a MIDI file to an audio file using FluidSynth."""
        midi_path = Path(midi_path).resolve()
        output_wav_path = Path(output_wav_path).resolve()
        output_wav_path.parent.mkdir(parents=True, exist_ok=True)

        # S4A-01 Command: ["fluidsynth", "-ni", "-F", out, "-r", sr, "-g", gain, sf2, mid]
        cmd = [
            self._binary_path,
            "-ni",
            "-F",
            str(output_wav_path),
            "-r",
            str(sample_rate),
            "-g",
            str(gain),
            str(self._soundfont_path),
            str(midi_path),
        ]
        ret = self._runner(cmd)
        if ret != 0:
            raise RuntimeError(f"FluidSynth command failed with exit code {ret}")
        return output_wav_path
