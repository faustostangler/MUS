"""Tests for AudioSignal and PitchContour domain arrays.

Covers: SK-06, SK-07.
"""

import numpy as np
import pytest

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.errors import SilentTakeError
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, SampleRate


def test_audio_signal_valid_and_immutable() -> None:
    """Covers SK-06: 1-D float64, C-contiguous, read-only, non-empty, finite, |x| <= 1.0."""
    samples = np.array([0.0, 0.5, -0.5, 0.2], dtype=np.float64)
    sr = SampleRate(44100)
    audio = AudioSignal(samples=samples, sample_rate=sr)

    assert audio.duration_seconds == pytest.approx(4 / 44100, rel=1e-5)
    assert len(audio) == 4
    assert not audio.samples.flags.writeable  # Immutability check

    with pytest.raises(ValueError):
        audio.samples[0] = 1.0  # Cannot modify read-only array


def test_audio_signal_rejects_silent_or_invalid() -> None:
    """Covers SK-06 & SilentTakeError."""
    sr = SampleRate(44100)
    with pytest.raises(SilentTakeError):
        AudioSignal(samples=np.zeros(100, dtype=np.float64), sample_rate=sr)

    with pytest.raises(SilentTakeError):
        AudioSignal(samples=np.array([], dtype=np.float64), sample_rate=sr)

    with pytest.raises(ValueError):
        # Peak > 1.0
        AudioSignal(samples=np.array([1.2, 0.5], dtype=np.float64), sample_rate=sr)

    with pytest.raises(ValueError):
        # 2-D array
        AudioSignal(samples=np.ones((2, 100), dtype=np.float64) * 0.1, sample_rate=sr)


def test_pitch_contour_invariants_and_conversions() -> None:
    """Covers SK-07: 1-D float64, read-only, all >= 0, voiced_mask, to_midi()."""
    f0_arr = np.array([0.0, 440.0, 261.6256, 0.0], dtype=np.float64)
    fp = FramePeriod(5.0)
    contour = PitchContour(f0=f0_arr, frame_period=fp)

    assert contour.duration_seconds == pytest.approx(4 * 0.005, rel=1e-5)
    assert not contour.f0.flags.writeable
    assert np.array_equal(contour.voiced_mask, np.array([False, True, True, False]))

    midi = contour.to_midi()
    assert np.isnan(midi[0])
    assert midi[1] == pytest.approx(69.0, abs=0.01)
    assert midi[2] == pytest.approx(60.0, abs=0.01)
    assert np.isnan(midi[3])


def test_pitch_contour_rejects_negative_or_infinite() -> None:
    """Covers SK-07 invariants."""
    fp = FramePeriod(5.0)
    with pytest.raises(ValueError):
        PitchContour(f0=np.array([-10.0, 200.0], dtype=np.float64), frame_period=fp)

    with pytest.raises(ValueError):
        PitchContour(f0=np.array([np.nan, 200.0], dtype=np.float64), frame_period=fp)
