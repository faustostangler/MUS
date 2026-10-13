"""NoteEvent and NoteSequence domain representations for symbolic music (SK-09, SK-10)."""

import math
from dataclasses import dataclass, field

from mus.shared_kernel.errors import PolyphonyNotSupportedError
from mus.shared_kernel.units import MidiPitch


@dataclass(frozen=True, slots=True)
class NoteEvent:
    """Discrete musical note event with onset, offset, velocity, and optional pitch bend curve."""

    pitch: MidiPitch
    onset_seconds: float
    offset_seconds: float
    velocity: int = 100
    pitch_bends: tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not (math.isfinite(self.onset_seconds) and math.isfinite(self.offset_seconds)):
            raise ValueError("NoteEvent timestamps must be finite numbers.")

        if not (0.0 <= self.onset_seconds < self.offset_seconds):
            raise ValueError(
                f"NoteEvent requires 0 <= onset ({self.onset_seconds}) "
                f"< offset ({self.offset_seconds})."
            )

        if not (1 <= self.velocity <= 127):
            raise ValueError(f"NoteEvent velocity {self.velocity} must be in [1, 127].")

        for bend in self.pitch_bends:
            if not (-8192 <= bend <= 8191):
                raise ValueError(f"Pitch bend value {bend} must be in [-8192, 8191].")

    @property
    def duration_seconds(self) -> float:
        """Returns the duration of the note in seconds."""
        return self.offset_seconds - self.onset_seconds


@dataclass(frozen=True, slots=True)
class NoteSequence:
    """Time-ordered, strictly monophonic sequence of NoteEvents with a defined tempo."""

    notes: list[NoteEvent]
    tempo_bpm: float = 120.0

    def __post_init__(self) -> None:
        if not (20.0 <= self.tempo_bpm <= 300.0):
            raise ValueError(f"Tempo {self.tempo_bpm} BPM must be in [20.0, 300.0].")

        # Sort notes by onset
        sorted_notes = sorted(self.notes, key=lambda n: n.onset_seconds)
        object.__setattr__(self, "notes", sorted_notes)

        # Enforce monophonic non-overlapping invariant (SK-10)
        for i in range(len(sorted_notes) - 1):
            curr_note = sorted_notes[i]
            next_note = sorted_notes[i + 1]
            if curr_note.offset_seconds > next_note.onset_seconds + 1e-4:
                raise PolyphonyNotSupportedError(
                    f"Overlapping notes detected: Note {curr_note.pitch.value} "
                    f"(ends {curr_note.offset_seconds}s) overlaps Note {next_note.pitch.value} "
                    f"(starts {next_note.onset_seconds}s)."
                )

    def __len__(self) -> int:
        return len(self.notes)
