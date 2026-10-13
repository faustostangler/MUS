"""Compressed NPZ Voice Cache adapter implementing VoiceCachePort (ADR-001 D5)."""

import os
from pathlib import Path

import numpy as np

from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, SampleRate
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)


class NpzVoiceCache:
    """Stores ParametricVoice as compressed npz with float64 F0 and float32 SP/AP."""

    def __init__(self, cache_dir: Path) -> None:
        self._cache_dir = Path(cache_dir).resolve()
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_key(self, key: str) -> Path:
        return self._cache_dir / f"{key}.npz"

    def load(self, key: str) -> ParametricVoice | None:
        """Loads voice from disk cache if it exists, using allow_pickle=False for security."""
        file_path = self._path_for_key(key)
        if not file_path.exists():
            return None

        try:
            with np.load(str(file_path), allow_pickle=False) as data:
                sr_val = int(data["sample_rate"])
                fp_val = float(data["frame_period"])
                f0_arr = data["f0"].astype(np.float64)
                sp_arr = data["sp"].astype(np.float64)
                ap_arr = data["ap"].astype(np.float64)

                sr = SampleRate(sr_val)
                fp = FramePeriod(fp_val)

                return ParametricVoice(
                    f0=PitchContour(f0=f0_arr, frame_period=fp),
                    sp=SpectralEnvelope(data=sp_arr),
                    ap=Aperiodicity(data=ap_arr),
                    sample_rate=sr,
                )
        except Exception:
            return None

    def save(self, key: str, voice: ParametricVoice) -> None:
        """Atomically saves ParametricVoice as compressed npz."""
        target_path = self._path_for_key(key)
        tmp_path = target_path.with_suffix(".tmp")

        try:
            np.savez_compressed(
                str(tmp_path),
                f0=voice.f0.f0.astype(np.float64),
                sp=voice.sp.data.astype(np.float32),  # Halves disk size per ADR-001 D5
                ap=voice.ap.data.astype(np.float32),
                sample_rate=np.int64(voice.sample_rate.value),
                frame_period=np.float64(voice.f0.frame_period.ms),
            )
            # Ensure the target has the expected .npz suffix after rename
            actual_tmp = tmp_path.with_suffix(".tmp.npz")
            if actual_tmp.exists():
                os.replace(str(actual_tmp), str(target_path))
            elif tmp_path.exists():
                os.replace(str(tmp_path), str(target_path))
        except Exception as e:
            for p in (tmp_path, tmp_path.with_suffix(".tmp.npz")):
                if p.exists():
                    p.unlink()
            raise e
