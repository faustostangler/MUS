"""TranscribeContour use case converting F0 contour into MIDI NoteSequence."""

from dataclasses import dataclass
from pathlib import Path

from mus.music_transcription.application.ports import MidiWriterPort
from mus.music_transcription.domain.hysteresis_segmenter import HysteresisSegmenter
from mus.music_transcription.infrastructure.pretty_midi_io import PrettyMidiIO
from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.notes import NoteSequence
from mus.shared_kernel.pitch import PitchContour


@dataclass(frozen=True, slots=True)
class TranscribeContourCommand:
    """Input parameters for pitch contour transcription."""

    contour: PitchContour
    tempo_bpm: float = 120.0
    output_midi_path: Path | None = None
    program_number: int = 52  # Default Choir Aahs (GM 52)
    signal: AudioSignal | None = None
    extract_pitch_bends: bool = False
    quantize: bool = False
    grid_division: int = 16


class TranscribeContour:
    """Coordinates segmentation and MIDI export for Track A."""

    def __init__(
        self,
        segmenter: HysteresisSegmenter | None = None,
        midi_io: MidiWriterPort | None = None,
    ) -> None:
        self._segmenter = segmenter or HysteresisSegmenter()
        self._midi_io = midi_io or PrettyMidiIO()

    def execute(self, command: TranscribeContourCommand) -> NoteSequence:
        """Segments the continuous contour and optionally exports to MIDI."""
        sequence = self._segmenter.segment(
            contour=command.contour,
            tempo_bpm=command.tempo_bpm,
            signal=command.signal,
            extract_pitch_bends=command.extract_pitch_bends,
            quantize=command.quantize,
            grid_division=command.grid_division,
        )

        if command.output_midi_path:
            self._midi_io.write(
                sequence=sequence,
                output_path=command.output_midi_path,
                program_number=command.program_number,
            )

        return sequence
