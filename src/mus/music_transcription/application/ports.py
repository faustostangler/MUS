from abc import ABC, abstractmethod
from pathlib import Path
from typing import Protocol

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.metrics import SongMetrics
from mus.shared_kernel.notes import NoteSequence


class AudioWriterPort(Protocol):
    """Port to atomically write an AudioSignal to disk."""

    def write(self, signal: AudioSignal, path: Path) -> None:
        """Writes audio signal atomically."""
        ...


class MidiWriterPort(ABC):
    """Port for exporting NoteSequence to MIDI."""

    @abstractmethod
    def write(
        self,
        sequence: NoteSequence,
        output_path: Path,
        program_number: int = 52,
        song_metrics: SongMetrics | None = None,
    ) -> None:
        """Exports a NoteSequence to a Standard MIDI file."""


class MidiReaderPort(ABC):
    """Port for reading NoteSequence from MIDI."""

    @abstractmethod
    def read(self, midi_path: Path) -> NoteSequence:
        """Reads a MIDI file and extracts the monophonic sequence."""


class ScoreExporterPort(ABC):
    """Port for converting MIDI files to sheet music scores (.mscz, .musicxml, etc.)."""

    @abstractmethod
    def export_score(self, midi_path: Path, output_path: Path) -> Path:
        """Converts a MIDI file to a score file and returns the generated score path."""


class SynthesizerPort(ABC):
    """Port for rendering MIDI files into acoustic audio signals (Route 4A)."""

    @abstractmethod
    def render_midi(
        self,
        midi_path: Path,
        output_wav_path: Path,
        sample_rate: int = 44100,
        gain: float = 0.2,
    ) -> Path:
        """Renders a MIDI file to an audio file using an acoustic synthesizer engine."""
