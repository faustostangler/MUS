"""Tests for Shared Kernel Unit and Value Objects.

Covers: SK-01, SK-02, SK-03, SK-04, SK-05, SK-08.
"""

import pytest

from mus.shared_kernel.errors import UnsupportedSampleRateError
from mus.shared_kernel.units import (
    FramePeriod,
    Hertz,
    MidiPitch,
    SampleRate,
    Semitones,
    TimeWindow,
)


def test_sample_rate_valid_values() -> None:
    """Covers SK-01: Sample rate must be 44100 or 48000 Hz."""
    sr44 = SampleRate(44100)
    assert sr44.value == 44100
    sr48 = SampleRate(48000)
    assert sr48.value == 48000

    with pytest.raises(UnsupportedSampleRateError):
        SampleRate(22050)


def test_frame_period_invariants() -> None:
    """Covers SK-02: Frame period in milliseconds must be in (0, 20]."""
    fp = FramePeriod(5.0)
    assert fp.ms == 5.0

    with pytest.raises(ValueError):
        FramePeriod(0.0)

    with pytest.raises(ValueError):
        FramePeriod(25.0)


def test_hertz_and_midi_pitch_conversion() -> None:
    """Covers SK-03, SK-08: Hertz and MidiPitch conversion invariants."""
    a4 = Hertz(440.0)
    midi_a4 = MidiPitch.from_hertz(a4)
    assert midi_a4.value == 69
    assert midi_a4.to_hertz().value == pytest.approx(440.0, rel=1e-3)

    c4 = Hertz(261.6256)
    midi_c4 = MidiPitch.from_hertz(c4)
    assert midi_c4.value == 60

    with pytest.raises(ValueError):
        MidiPitch(128)

    with pytest.raises(ValueError):
        MidiPitch(-1)


def test_semitones_invariants() -> None:
    """Covers SK-04: Semitones interval bounded within [-24, 24]."""
    st = Semitones(12.0)
    assert st.ratio() == pytest.approx(2.0, rel=1e-5)

    st_neg = Semitones(-12.0)
    assert st_neg.ratio() == pytest.approx(0.5, rel=1e-5)

    with pytest.raises(ValueError):
        Semitones(25.0)


def test_time_window_invariants() -> None:
    """Covers SK-05: TimeWindow invariants."""
    w = TimeWindow(start_seconds=1.0, end_seconds=3.0)
    assert w.duration == 2.0
    assert w.contains(2.0)
    assert not w.contains(3.5)

    with pytest.raises(ValueError):
        TimeWindow(start_seconds=3.0, end_seconds=1.0)
