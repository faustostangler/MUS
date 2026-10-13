"""Tests for pitch modulation domain transformations.

Covers: S1-07, S1-08, S1-09.
"""

import numpy as np
import pytest

from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, Hertz, Semitones, TimeWindow
from mus.voice_modeling.domain.pitch_modulation import (
    apply_ramp,
    clip_to_range,
    transpose,
)


def test_transpose_preserves_unvoiced_and_shifts_voiced() -> None:
    """Covers S1-07: Transposition shifts voiced frames and leaves unvoiced as 0.0."""
    fp = FramePeriod(5.0)
    # F0 = [0.0, 220.0, 440.0, 0.0]
    contour = PitchContour(np.array([0.0, 220.0, 440.0, 0.0], dtype=np.float64), fp)
    shifted = transpose(contour, Semitones(12.0))

    assert shifted.f0[0] == 0.0
    assert shifted.f0[1] == pytest.approx(440.0, rel=1e-5)
    assert shifted.f0[2] == pytest.approx(880.0, rel=1e-5)
    assert shifted.f0[3] == 0.0


def test_transpose_roundtrip_identity() -> None:
    """Transposing by +n then -n restores the exact pitch."""
    fp = FramePeriod(5.0)
    original = PitchContour(np.array([0.0, 220.0, 330.0], dtype=np.float64), fp)
    shifted = transpose(original, Semitones(7.0))
    restored = transpose(shifted, Semitones(-7.0))

    assert np.allclose(original.f0, restored.f0, atol=1e-9)


def test_apply_ramp_modulates_inside_window() -> None:
    """Covers S1-08: Pitch ramp at phrase end."""
    fp = FramePeriod(10.0)  # 10ms per frame
    n_frames = 100
    contour = PitchContour(np.full(n_frames, 200.0, dtype=np.float64), fp)

    # Window from 0.5s to 0.8s (frames 50 to 80), shift by -2 semitones
    window = TimeWindow(start_seconds=0.5, end_seconds=0.8)
    ramped = apply_ramp(contour, window, Semitones(-2.0))

    # Before window: untouched
    assert ramped.f0[40] == 200.0
    # Inside window: progressively decreasing
    assert ramped.f0[65] < 200.0
    # End of window: ~200 * 2^(-2/12)
    expected_end = 200.0 * (2.0 ** (-2.0 / 12.0))
    assert ramped.f0[80] == pytest.approx(expected_end, rel=1e-3)


def test_clip_to_range() -> None:
    """Covers S1-09: F0 clipping and counter."""
    fp = FramePeriod(5.0)
    contour = PitchContour(np.array([0.0, 50.0, 220.0, 1500.0], dtype=np.float64), fp)
    clipped, count = clip_to_range(contour, floor=Hertz(65.0), ceil=Hertz(1100.0))

    assert clipped.f0[0] == 0.0  # Unvoiced untouched
    assert clipped.f0[1] == 65.0
    assert clipped.f0[2] == 220.0
    assert clipped.f0[3] == 1100.0
    assert count == 2
