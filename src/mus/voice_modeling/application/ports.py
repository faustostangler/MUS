"""Application ports and contracts for voice modeling."""

from pathlib import Path
from typing import Protocol

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import FramePeriod, Hertz, SampleRate
from mus.voice_modeling.domain.parametric_voice import ParametricVoice


class AudioReaderPort(Protocol):
    """Port to read and normalize audio files into an AudioSignal."""

    def read(self, path: Path, target_rate: SampleRate) -> AudioSignal:
        """Reads audio file, converts to mono float64, and resamples if needed."""
        ...


class AudioWriterPort(Protocol):
    """Port to atomically write an AudioSignal to disk."""

    def write(self, signal: AudioSignal, path: Path) -> None:
        """Writes audio signal atomically."""
        ...


class VocoderPort(Protocol):
    """Port for parametric source-filter vocoder analysis and synthesis."""

    def analyze(
        self,
        signal: AudioSignal,
        f0_floor: Hertz,
        f0_ceil: Hertz,
        frame_period: FramePeriod,
        method: str = "dio",
    ) -> ParametricVoice:
        """Decomposes an AudioSignal into a ParametricVoice."""
        ...

    def synthesize(self, voice: ParametricVoice) -> AudioSignal:
        """Synthesizes a ParametricVoice back into a continuous AudioSignal."""
        ...


class VoiceCachePort(Protocol):
    """Port to load and store cached ParametricVoice instances on disk."""

    def load(self, key: str) -> ParametricVoice | None:
        """Loads cached ParametricVoice if it exists, else None."""
        ...

    def save(self, key: str, voice: ParametricVoice) -> None:
        """Persists ParametricVoice to cache."""
        ...
