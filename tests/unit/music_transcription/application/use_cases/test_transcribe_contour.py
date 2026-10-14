"""Unit tests for TranscribeContour use case."""

from pathlib import Path
from unittest.mock import MagicMock

import numpy as np

from mus.music_transcription.application.ports import MidiWriterPort
from mus.music_transcription.application.use_cases.transcribe_contour import (
    TranscribeContour,
    TranscribeContourCommand,
)
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod


def test_transcribe_contour_segments_and_returns_sequence() -> None:
    # 440 Hz (A4 -> MIDI 69) for 100 frames at 5ms = 0.5s
    f0 = np.full(100, 440.0, dtype=np.float64)
    contour = PitchContour(f0=f0, frame_period=FramePeriod(5.0))

    use_case = TranscribeContour()
    cmd = TranscribeContourCommand(contour=contour, tempo_bpm=120.0)

    seq = use_case.execute(cmd)
    assert len(seq.notes) == 1
    assert seq.notes[0].pitch.value == 69


def test_transcribe_contour_calls_midi_writer_when_path_provided(tmp_path: Path) -> None:
    f0 = np.full(100, 440.0, dtype=np.float64)
    contour = PitchContour(f0=f0, frame_period=FramePeriod(5.0))

    mock_writer = MagicMock(spec=MidiWriterPort)
    use_case = TranscribeContour(midi_io=mock_writer)

    out_mid = tmp_path / "out.mid"
    cmd = TranscribeContourCommand(
        contour=contour,
        tempo_bpm=120.0,
        output_midi_path=out_mid,
        program_number=52,
    )

    seq = use_case.execute(cmd)
    mock_writer.write.assert_called_once_with(
        sequence=seq,
        output_path=out_mid,
        program_number=52,
        song_metrics=None,
    )
