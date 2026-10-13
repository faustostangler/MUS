"""Use case for decomposing an AudioSignal into a ParametricVoice."""

from dataclasses import dataclass, field

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import FramePeriod, Hertz
from mus.voice_modeling.application.ports import VocoderPort, VoiceCachePort
from mus.voice_modeling.domain.parametric_voice import ParametricVoice


@dataclass(frozen=True, slots=True)
class DecomposeVoiceCommand:
    """Input payload for voice decomposition."""

    signal: AudioSignal
    f0_floor: Hertz = field(default_factory=lambda: Hertz(65.0))
    f0_ceil: Hertz = field(default_factory=lambda: Hertz(1100.0))
    frame_period: FramePeriod = field(default_factory=lambda: FramePeriod(5.0))
    method: str = "dio"
    cache_key: str | None = None


class DecomposeVoice:
    """Use case coordinating vocoder analysis and optional voice caching."""

    def __init__(
        self,
        vocoder: VocoderPort,
        cache: VoiceCachePort | None = None,
    ) -> None:
        self._vocoder = vocoder
        self._cache = cache

    def execute(self, command: DecomposeVoiceCommand) -> ParametricVoice:
        """Executes voice decomposition, checking cache first if a key is provided."""
        if self._cache and command.cache_key:
            cached = self._cache.load(command.cache_key)
            if cached is not None:
                return cached

        voice = self._vocoder.analyze(
            signal=command.signal,
            f0_floor=command.f0_floor,
            f0_ceil=command.f0_ceil,
            frame_period=command.frame_period,
            method=command.method,
        )

        if self._cache and command.cache_key:
            self._cache.save(command.cache_key, voice)

        return voice
