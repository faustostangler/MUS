"""Application ports for instrument rendering context (ADR-001 D2)."""

from abc import ABC, abstractmethod
from pathlib import Path

from mus.shared_kernel.notes import NoteSequence


class InstrumentRendererPort(ABC):
    """Port for rendering symbolic NoteSequence or MIDI into acoustic audio."""

    @abstractmethod
    def render_midi_file(
        self,
        midi_path: Path,
        output_wav_path: Path,
        soundfont_path: Path,
        sample_rate: int = 44100,
        gain: float = 0.5,
    ) -> Path:
        """Renders an existing MIDI file to a WAV audio file via SoundFont."""
        ...

    @abstractmethod
    def render(  # noqa: PLR0917
        self,
        sequence: NoteSequence,
        output_wav_path: Path,
        soundfont_path: Path,
        sample_rate: int = 44100,
        gain: float = 0.5,
        program_number: int = 52,
    ) -> Path:
        """Renders a domain NoteSequence to a WAV file."""
        ...
