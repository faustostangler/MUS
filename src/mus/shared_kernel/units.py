"""Physical and musical units as Value Objects.

Enforces zero primitive obsession and self-validating construction.
"""

import math
from dataclasses import dataclass
from typing import ClassVar

from mus.shared_kernel.errors import UnsupportedSampleRateError


@dataclass(frozen=True, slots=True)
class SampleRate:
    """Audio sampling rate in Hertz. Allowed: 44100 or 48000 Hz."""

    value: int
    ALLOWED: ClassVar[frozenset[int]] = frozenset({44100, 48000})

    def __post_init__(self) -> None:
        if self.value not in self.ALLOWED:
            raise UnsupportedSampleRateError(
                f"Sample rate {self.value} is not supported. Must be 44100 or 48000 Hz."
            )


@dataclass(frozen=True, slots=True)
class FramePeriod:
    """Hop size between analysis frames in milliseconds."""

    ms: float = 5.0

    def __post_init__(self) -> None:
        if not (0.0 < self.ms <= 20.0):
            raise ValueError(f"Frame period {self.ms} ms must be > 0 and <= 20 ms.")


@dataclass(frozen=True, slots=True)
class Hertz:
    """Frequency in Hertz."""

    value: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.value) or self.value < 0.0:
            raise ValueError(f"Frequency {self.value} Hz must be finite and >= 0.")


@dataclass(frozen=True, slots=True)
class MidiPitch:
    """Discrete MIDI pitch number (0 to 127)."""

    value: int

    def __post_init__(self) -> None:
        if not (0 <= self.value <= 127):
            raise ValueError(f"MIDI pitch {self.value} must be within [0, 127].")

    @classmethod
    def from_hertz(cls, hertz: Hertz) -> "MidiPitch":
        """Calculates standard MIDI pitch from frequency using 440 Hz (A4 = 69)."""
        if hertz.value <= 0.0:
            raise ValueError("Cannot convert zero or negative frequency to MIDI pitch.")
        midi_num = round(69.0 + 12.0 * math.log2(hertz.value / 440.0))
        return cls(midi_num)

    def to_hertz(self) -> Hertz:
        """Converts MIDI pitch to frequency in Hertz."""
        freq = 440.0 * (2.0 ** ((self.value - 69.0) / 12.0))
        return Hertz(freq)


@dataclass(frozen=True, slots=True)
class Semitones:
    """Musical pitch interval in semitones."""

    value: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.value) or abs(self.value) > 24.0:
            raise ValueError(f"Semitone shift {self.value} must be within [-24, 24].")

    def ratio(self) -> float:
        """Calculates the frequency multiplier: 2^(semitones / 12)."""
        return float(2.0 ** (self.value / 12.0))


@dataclass(frozen=True, slots=True)
class TimeWindow:
    """Continuous temporal interval in seconds."""

    start_seconds: float
    end_seconds: float

    def __post_init__(self) -> None:
        if not (math.isfinite(self.start_seconds) and math.isfinite(self.end_seconds)):
            raise ValueError("TimeWindow bounds must be finite numbers.")
        if not (0.0 <= self.start_seconds < self.end_seconds):
            raise ValueError(
                f"TimeWindow requires 0 <= start ({self.start_seconds}) < end ({self.end_seconds})."
            )

    @property
    def duration(self) -> float:
        """Duration of the time window in seconds."""
        return self.end_seconds - self.start_seconds

    def contains(self, t: float) -> bool:
        """Checks if timestamp t falls inside the window."""
        return self.start_seconds <= t <= self.end_seconds

    def overlaps(self, other: "TimeWindow") -> bool:
        """Checks if two time windows overlap."""
        return max(self.start_seconds, other.start_seconds) < min(
            self.end_seconds, other.end_seconds
        )
