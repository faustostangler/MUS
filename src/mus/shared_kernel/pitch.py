"""PitchContour domain representation representing the fundamental frequency (F0)."""

from dataclasses import dataclass

import numpy as np

from mus.shared_kernel.units import FramePeriod


@dataclass(frozen=True, slots=True)
class PitchContour:
    """Continuous F0 time-series contour in Hertz (0.0 represents unvoiced)."""

    f0: np.ndarray
    frame_period: FramePeriod

    def __post_init__(self) -> None:
        if not isinstance(self.f0, np.ndarray):
            raise TypeError("PitchContour f0 must be a numpy ndarray.")

        if self.f0.ndim != 1:
            raise ValueError(f"PitchContour f0 must be 1-dimensional, got {self.f0.ndim}D.")

        if not np.all(np.isfinite(self.f0)):
            raise ValueError("PitchContour contains non-finite (NaN/Inf) values.")

        if np.any(self.f0 < 0.0):
            raise ValueError("PitchContour contains negative frequency values.")

        # Guarantee C-contiguous float64 and enforce immutability
        if self.f0.dtype != np.float64 or not self.f0.flags.c_contiguous:
            c_arr = np.ascontiguousarray(self.f0, dtype=np.float64)
            object.__setattr__(self, "f0", c_arr)

        self.f0.flags.writeable = False

    def __len__(self) -> int:
        return len(self.f0)

    @property
    def duration_seconds(self) -> float:
        """Returns the total duration spanned by the contour in seconds."""
        return float(len(self.f0) * (self.frame_period.ms / 1000.0))

    @property
    def voiced_mask(self) -> np.ndarray:
        """Boolean mask where True denotes voiced frames (F0 > 0)."""
        return self.f0 > 0.0

    def to_midi(self) -> np.ndarray:
        """Converts F0 in Hz to fractional MIDI pitch values, filling unvoiced frames with NaN."""
        midi_arr = np.full_like(self.f0, fill_value=np.nan)
        voiced = self.voiced_mask
        if np.any(voiced):
            midi_arr[voiced] = 69.0 + 12.0 * np.log2(self.f0[voiced] / 440.0)
        return midi_arr
