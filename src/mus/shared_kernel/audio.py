"""Immutable mono AudioSignal domain representation."""

from dataclasses import dataclass

import numpy as np

from mus.shared_kernel.errors import SilentTakeError
from mus.shared_kernel.units import SampleRate


@dataclass(frozen=True, slots=True)
class AudioSignal:
    """Monophonic audio PCM signal in float64 with immutable buffer."""

    samples: np.ndarray
    sample_rate: SampleRate

    def __post_init__(self) -> None:
        if not isinstance(self.samples, np.ndarray):
            raise TypeError("AudioSignal samples must be a numpy ndarray.")

        if self.samples.ndim != 1:
            raise ValueError(f"AudioSignal must be 1-dimensional (mono), got {self.samples.ndim}D.")

        if self.samples.size == 0 or np.all(self.samples == 0.0):
            raise SilentTakeError("AudioSignal is empty or completely silent.")

        if not np.all(np.isfinite(self.samples)):
            raise ValueError("AudioSignal contains NaN or Inf values.")

        max_peak = float(np.max(np.abs(self.samples)))
        if max_peak > 1.0:
            raise ValueError(f"AudioSignal peak {max_peak} exceeds normalized range [-1.0, 1.0].")

        # Guarantee C-contiguous float64 and enforce immutability
        if self.samples.dtype != np.float64 or not self.samples.flags.c_contiguous:
            c_arr = np.ascontiguousarray(self.samples, dtype=np.float64)
            object.__setattr__(self, "samples", c_arr)

        self.samples.flags.writeable = False

    def __len__(self) -> int:
        return len(self.samples)

    @property
    def duration_seconds(self) -> float:
        """Returns the duration of the audio signal in seconds."""
        return float(len(self.samples) / self.sample_rate.value)
