"""Demucs source separation adapter utilizing HTDemucs (Meta AI)."""

import shutil
from collections.abc import Callable
from pathlib import Path

from mus.stem_separation.application.ports import StemSeparatorPort
from mus.stem_separation.domain.models import SeparatedStems


def _default_demucs_runner(cmd: list[str]) -> None:
    try:
        from demucs.separate import main as demucs_main  # noqa: PLC0415
    except ImportError as err:
        raise RuntimeError(
            "Demucs is not installed in the active environment. Install with 'uv sync'."
        ) from err
    demucs_main(cmd)  # type: ignore[no-untyped-call]


class DemucsStemSeparator(StemSeparatorPort):
    """Separates audio files into isolated stems using Demucs."""

    def __init__(
        self,
        model_name: str = "htdemucs_6s",
        device: str = "cpu",
        mp3_bitrate: int = 320,
        runner: Callable[[list[str]], None] | None = None,
    ) -> None:
        self._model_name = model_name
        self._device = device
        self._mp3_bitrate = mp3_bitrate
        self._runner = runner or _default_demucs_runner

    def separate(self, audio_path: Path, output_dir: Path) -> SeparatedStems:
        """Runs Demucs and moves stems to output_dir with standardized naming."""
        audio_path = Path(audio_path).resolve()
        output_dir = Path(output_dir).resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        temp_demucs_dir = output_dir / f".demucs_tmp_{audio_path.stem}"
        temp_demucs_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            "-n",
            self._model_name,
            "-o",
            str(temp_demucs_dir),
            "-d",
            self._device,
            "--mp3",
            "--mp3-bitrate",
            str(self._mp3_bitrate),
            "--mp3-preset",
            "2",
            "--clip-mode",
            "rescale",
            str(audio_path),
        ]

        self._runner(cmd)

        raw_folder = temp_demucs_dir / self._model_name / audio_path.stem
        vocals_path: Path | None = None
        other_stems: dict[str, Path] = {}

        if raw_folder.exists():
            for stem_file in raw_folder.glob("*.mp3"):
                stem_type = stem_file.stem
                target_stem_path = output_dir / f"{audio_path.stem} - {stem_type}.mp3"
                shutil.move(str(stem_file), str(target_stem_path))
                if stem_type == "vocals":
                    vocals_path = target_stem_path
                else:
                    other_stems[stem_type] = target_stem_path

            shutil.rmtree(temp_demucs_dir, ignore_errors=True)

        if vocals_path is None or not vocals_path.exists():
            raise FileNotFoundError(f"Demucs did not produce a vocal stem for: {audio_path.name}")

        return SeparatedStems(vocals_path=vocals_path, other_stems=other_stems)
