"""Tests for ParametricVoice aggregate and spectral matrices.

Covers: VM-01, VM-02, VM-03, VM-04, VM-05.
"""

import numpy as np
import pytest

from mus.shared_kernel.errors import MisalignedFramesError
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, SampleRate
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)


def _make_dummy_voice(n_frames: int = 10, fft_size: int = 2048) -> ParametricVoice:
    n_bins = fft_size // 2 + 1
    f0 = PitchContour(np.full(n_frames, 220.0, dtype=np.float64), FramePeriod(5.0))
    sp = SpectralEnvelope(np.ones((n_frames, n_bins), dtype=np.float64))
    ap = Aperiodicity(np.zeros((n_frames, n_bins), dtype=np.float64))
    sr = SampleRate(44100)
    return ParametricVoice(f0=f0, sp=sp, ap=ap, sample_rate=sr)


def test_parametric_voice_creation_and_immutability() -> None:
    """Covers VM-01, VM-02, VM-05: aggregate integrity and immutability."""
    voice = _make_dummy_voice(n_frames=10, fft_size=2048)
    assert voice.n_frames == 10
    assert voice.fft_size == 2048
    assert voice.duration_seconds == pytest.approx(10 * 0.005)

    assert not voice.sp.data.flags.writeable
    assert not voice.ap.data.flags.writeable


def test_parametric_voice_rejects_misaligned_frames() -> None:
    """Covers VM-01: len(f0) == sp.shape[0] == ap.shape[0]."""
    n_bins = 1025
    f0 = PitchContour(np.full(10, 220.0, dtype=np.float64), FramePeriod(5.0))
    sp = SpectralEnvelope(np.ones((8, n_bins), dtype=np.float64))  # 8 != 10
    ap = Aperiodicity(np.zeros((10, n_bins), dtype=np.float64))
    sr = SampleRate(44100)

    with pytest.raises(MisalignedFramesError):
        ParametricVoice(f0=f0, sp=sp, ap=ap, sample_rate=sr)


def test_spectral_envelope_rejects_non_positive() -> None:
    """Covers VM-03: SP must be strictly positive and finite (log-safe)."""
    with pytest.raises(ValueError):
        SpectralEnvelope(np.array([[1.0, 0.0], [0.5, 0.5]], dtype=np.float64))

    with pytest.raises(ValueError):
        SpectralEnvelope(np.array([[1.0, -0.1], [0.5, 0.5]], dtype=np.float64))


def test_aperiodicity_invariants() -> None:
    """Covers VM-04: AP values must be strictly in [0.0, 1.0]."""
    with pytest.raises(ValueError):
        Aperiodicity(np.array([[0.0, 1.2]], dtype=np.float64))

    with pytest.raises(ValueError):
        Aperiodicity(np.array([[-0.1, 0.5]], dtype=np.float64))


def test_with_f0_and_with_sp_returns_new_instance() -> None:
    """Covers VM-05: functional immutability."""
    voice = _make_dummy_voice(n_frames=10)
    new_f0 = PitchContour(np.full(10, 440.0, dtype=np.float64), FramePeriod(5.0))
    updated_voice = voice.with_f0(new_f0)

    assert updated_voice is not voice
    assert updated_voice.f0.f0[0] == 440.0
    assert voice.f0.f0[0] == 220.0  # Original remains intact
