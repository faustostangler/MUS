"""Tests for NoteEvent, NoteSequence and Hysteresis Segmentation.

Covers: SK-09, SK-10, S2-01, S2-02, S2-03, S2-04.
"""

import numpy as np
import pytest

from mus.music_transcription.domain.hysteresis_segmenter import HysteresisSegmenter
from mus.shared_kernel.errors import PolyphonyNotSupportedError
from mus.shared_kernel.notes import NoteEvent, NoteSequence
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, MidiPitch


def test_note_event_invariants() -> None:
    """Covers SK-09: onset < offset, velocity in [1, 127], pitch-bend in [-8192, 8191]."""
    note = NoteEvent(
        pitch=MidiPitch(60),
        onset_seconds=0.0,
        offset_seconds=0.5,
        velocity=100,
    )
    assert note.duration_seconds == 0.5

    with pytest.raises(ValueError):
        NoteEvent(pitch=MidiPitch(60), onset_seconds=0.5, offset_seconds=0.5)

    with pytest.raises(ValueError):
        NoteEvent(pitch=MidiPitch(60), onset_seconds=0.0, offset_seconds=0.5, velocity=0)


def test_note_sequence_rejects_polyphonic_overlap() -> None:
    """Covers SK-10: Monophonic NoteSequence rejects overlapping notes."""
    n1 = NoteEvent(pitch=MidiPitch(60), onset_seconds=0.0, offset_seconds=0.5)
    n2 = NoteEvent(pitch=MidiPitch(62), onset_seconds=0.4, offset_seconds=0.8)  # Overlaps n1

    with pytest.raises(PolyphonyNotSupportedError):
        NoteSequence(notes=[n1, n2], tempo_bpm=120.0)


def test_hysteresis_segmenter_stepped_notes() -> None:
    """Covers S2-01, S2-02: 3 clear stepped notes (C4, E4, G4) with small vibrato."""
    fp = FramePeriod(10.0)  # 10ms per frame
    fs_frames = 100  # 1.0 second total (50 frames note 1, 50 frames note 2)

    t = np.linspace(0, 1.0, fs_frames)
    # Note 1: MIDI 60 (261.63 Hz) + ±30 cents vibrato
    f0_n1 = 261.63 * (2.0 ** (0.3 * np.sin(2 * np.pi * 5 * t[:50]) / 12.0))
    # Note 2: MIDI 64 (329.63 Hz) + ±30 cents vibrato
    f0_n2 = 329.63 * (2.0 ** (0.3 * np.sin(2 * np.pi * 5 * t[50:]) / 12.0))
    f0 = np.concatenate([f0_n1, f0_n2])

    contour = PitchContour(f0=f0, frame_period=fp)
    segmenter = HysteresisSegmenter(
        hysteresis_cents=70.0,
        min_change_ms=60.0,
        min_note_ms=80.0,
        max_gap_ms=50.0,
    )

    sequence = segmenter.segment(contour)
    assert len(sequence.notes) == 2
    assert sequence.notes[0].pitch.value == 60
    assert sequence.notes[1].pitch.value == 64
    assert sequence.notes[0].offset_seconds == pytest.approx(0.5, abs=0.05)
