"""ParametricVoice Aggregate, SpectralEnvelope, and Aperiodicity domain models."""

from dataclasses import dataclass

import numpy as np

from mus.shared_kernel.errors import MisalignedFramesError
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import SampleRate


@dataclass(frozen=True, slots=True)
class SpectralEnvelope:
    """Smoothed power spectral envelope matrix (n_frames x n_bins). Log-safe, strictly > 0."""

    data: np.ndarray

    def __post_init__(self) -> None:
        if not isinstance(self.data, np.ndarray):
            raise TypeError("SpectralEnvelope data must be a numpy ndarray.")

        if self.data.ndim != 2:
            raise ValueError(f"SpectralEnvelope data must be 2D, got {self.data.ndim}D.")

        if not np.all(np.isfinite(self.data)):
            raise ValueError("SpectralEnvelope contains NaN or Inf values.")

        if np.any(self.data <= 0.0):
            raise ValueError(
                "SpectralEnvelope values must be strictly positive (> 0.0) for log safety."
            )

        if self.data.dtype != np.float64 or not self.data.flags.c_contiguous:
            c_arr = np.ascontiguousarray(self.data, dtype=np.float64)
            object.__setattr__(self, "data", c_arr)

        self.data.flags.writeable = False

    @property
    def shape(self) -> tuple[int, int]:
        """Returns (n_frames, n_bins)."""
        return int(self.data.shape[0]), int(self.data.shape[1])


@dataclass(frozen=True, slots=True)
class Aperiodicity:
    """Aperiodicity ratio matrix (n_frames x n_bins) with values strictly in [0.0, 1.0]."""

    data: np.ndarray

    def __post_init__(self) -> None:
        if not isinstance(self.data, np.ndarray):
            raise TypeError("Aperiodicity data must be a numpy ndarray.")

        if self.data.ndim != 2:
            raise ValueError(f"Aperiodicity data must be 2D, got {self.data.ndim}D.")

        if not np.all(np.isfinite(self.data)):
            raise ValueError("Aperiodicity contains NaN or Inf values.")

        if np.any((self.data < 0.0) | (self.data > 1.0)):
            raise ValueError("Aperiodicity values must be strictly in [0.0, 1.0].")

        if self.data.dtype != np.float64 or not self.data.flags.c_contiguous:
            c_arr = np.ascontiguousarray(self.data, dtype=np.float64)
            object.__setattr__(self, "data", c_arr)

        self.data.flags.writeable = False

    @property
    def shape(self) -> tuple[int, int]:
        """Returns (n_frames, n_bins)."""
        return int(self.data.shape[0]), int(self.data.shape[1])


@dataclass(frozen=True, slots=True)
class ParametricVoice:
    """Parametric Voice Aggregate decoupling Pitch (F0), Filter (SP), and Noise (AP)."""

    f0: PitchContour
    sp: SpectralEnvelope
    ap: Aperiodicity
    sample_rate: SampleRate

    def __post_init__(self) -> None:
        n_f0 = len(self.f0)
        n_sp, bins_sp = self.sp.shape
        n_ap, bins_ap = self.ap.shape

        if not (n_f0 == n_sp == n_ap):
            raise MisalignedFramesError(
                f"Misaligned frame lengths: F0={n_f0}, SP={n_sp}, AP={n_ap}."
            )

        if bins_sp != bins_ap:
            raise ValueError(
                f"Spectral bin mismatch: SP has {bins_sp} bins, AP has {bins_ap} bins."
            )

    @property
    def n_frames(self) -> int:
        """Returns the number of time frames."""
        return len(self.f0)

    @property
    def n_bins(self) -> int:
        """Returns the number of frequency bins."""
        return self.sp.shape[1]

    @property
    def fft_size(self) -> int:
        """Returns the FFT size associated with the spectral bins (2 * (n_bins - 1))."""
        return 2 * (self.n_bins - 1)

    @property
    def duration_seconds(self) -> float:
        """Returns total duration in seconds."""
        return self.f0.duration_seconds

    def with_f0(self, new_f0: PitchContour) -> "ParametricVoice":
        """Returns a new ParametricVoice with replaced PitchContour."""
        return ParametricVoice(
            f0=new_f0,
            sp=self.sp,
            ap=self.ap,
            sample_rate=self.sample_rate,
        )

    def with_sp(self, new_sp: SpectralEnvelope) -> "ParametricVoice":
        """Returns a new ParametricVoice with replaced SpectralEnvelope."""
        return ParametricVoice(
            f0=self.f0,
            sp=new_sp,
            ap=self.ap,
            sample_rate=self.sample_rate,
        )
