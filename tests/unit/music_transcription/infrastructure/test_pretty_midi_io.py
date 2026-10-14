"""Tests for PrettyMidiIO adapter and MIDI Type 1 export.

Covers: S2-08, MT-02.
"""

from pathlib import Path

import pretty_midi
import pytest

from mus.music_transcription.infrastructure.pretty_midi_io import PrettyMidiIO
from mus.shared_kernel.metrics import SongMetrics
from mus.shared_kernel.notes import NoteEvent, NoteSequence
from mus.shared_kernel.units import MidiPitch


def test_pretty_midi_io_write_and_read(tmp_path: Path) -> None:
    """Covers S2-08, MT-02: Writes MIDI Type 1 with Choir Aahs (GM 52) and reads it back."""
    io = PrettyMidiIO()
    n1 = NoteEvent(pitch=MidiPitch(60), onset_seconds=0.0, offset_seconds=0.5, velocity=80)
    n2 = NoteEvent(pitch=MidiPitch(64), onset_seconds=0.5, offset_seconds=1.0, velocity=90)
    sequence = NoteSequence(notes=[n1, n2], tempo_bpm=120.0)

    midi_path = tmp_path / "vocal_melody.mid"
    io.write(sequence, midi_path, program_number=52)

    assert midi_path.exists()
    loaded = io.read(midi_path)

    assert loaded.tempo_bpm == 120.0
    assert len(loaded.notes) == 2
    assert loaded.notes[0].pitch.value == 60
    assert loaded.notes[1].pitch.value == 64
    assert loaded.notes[0].velocity == 80
    assert loaded.notes[1].velocity == 90


def test_pretty_midi_io_writes_song_metrics_meta_events(tmp_path: Path) -> None:
    """Covers SPEC-005 S2: PrettyMidiIO writes tempo, time signature, and end marker."""
    io = PrettyMidiIO()
    n1 = NoteEvent(pitch=MidiPitch(60), onset_seconds=0.0, offset_seconds=0.5, velocity=80)
    sequence = NoteSequence(notes=[n1], tempo_bpm=120.0)

    metrics = SongMetrics(
        tempo_bpm=85.5,
        duration_seconds=120.0,
        time_signature_numerator=3,
        time_signature_denominator=4,
    )

    midi_path = tmp_path / "metrics_test.mid"
    io.write(sequence, midi_path, program_number=52, song_metrics=metrics)

    pm = pretty_midi.PrettyMIDI(str(midi_path))
    _, tempi = pm.get_tempo_changes()
    assert pytest.approx(float(tempi[0]), abs=0.01) == 85.5
    assert len(pm.time_signature_changes) > 0
    assert pm.time_signature_changes[0].numerator == 3
    assert pm.time_signature_changes[0].denominator == 4
    assert pytest.approx(pm.get_end_time(), abs=0.01) == 120.0
