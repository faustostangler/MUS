"""Pitch contour transformations (transposition, ramps, vibrato scaling, clipping)."""

import numpy as np

from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import Hertz, Semitones, TimeWindow


def transpose(contour: PitchContour, shift: Semitones) -> PitchContour:
    """Transposes the pitch contour by a specified semitone interval.

    Leaves unvoiced frames untouched.
    """
    f0 = contour.f0.copy()
    voiced = contour.voiced_mask
    if np.any(voiced):
        f0[voiced] = f0[voiced] * shift.ratio()
    return PitchContour(f0=f0, frame_period=contour.frame_period)


def apply_ramp(
    contour: PitchContour,
    window: TimeWindow,
    target_shift: Semitones,
) -> PitchContour:
    """Applies a smooth linear pitch ramp inside a designated temporal window."""
    f0 = contour.f0.copy()
    fp_sec = contour.frame_period.ms / 1000.0
    times = np.arange(len(f0)) * fp_sec

    in_window = (times >= window.start_seconds) & (times <= window.end_seconds)
    if not np.any(in_window):
        return contour

    # Linear progression in semitones: 0 -> target_shift
    w_dur = max(window.duration, 1e-6)
    progress = np.clip((times[in_window] - window.start_seconds) / w_dur, 0.0, 1.0)
    st_shifts = progress * target_shift.value
    ratios = 2.0 ** (st_shifts / 12.0)

    voiced_in_window = in_window & contour.voiced_mask
    if np.any(voiced_in_window):
        f0[voiced_in_window] = f0[voiced_in_window] * ratios[contour.voiced_mask[in_window]]

    return PitchContour(f0=f0, frame_period=contour.frame_period)


def clip_to_range(
    contour: PitchContour,
    floor: Hertz,
    ceil: Hertz,
) -> tuple[PitchContour, int]:
    """Clips voiced F0 to [floor, ceil] bounds and returns count of clipped frames."""
    f0 = contour.f0.copy()
    voiced = contour.voiced_mask

    clipped_below = voiced & (f0 < floor.value)
    clipped_above = voiced & (f0 > ceil.value)

    f0[clipped_below] = floor.value
    f0[clipped_above] = ceil.value

    count = int(np.sum(clipped_below) + np.sum(clipped_above))
    return PitchContour(f0=f0, frame_period=contour.frame_period), count
