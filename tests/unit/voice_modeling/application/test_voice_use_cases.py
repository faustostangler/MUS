"""Tests for DecomposeVoice and ResynthesizeVoice use cases using fakes."""

import numpy as np
import pytest

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.errors import WindowOutOfRangeError
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, Hertz, SampleRate
from mus.voice_modeling.application.use_cases.decompose_voice import (
    DecomposeVoice,
    DecomposeVoiceCommand,
)
from mus.voice_modeling.application.use_cases.reshape_formants import (
    ReshapeFormants,
    ReshapeFormantsCommand,
)
from mus.voice_modeling.application.use_cases.resynthesize_voice import (
    ResynthesizeVoice,
    ResynthesizeVoiceCommand,
)
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)
from mus.voice_modeling.domain.phonetics import IPA_VOWEL_TABLE, VocalTractScale


class FakeVocoder:
    """In-memory fake vocoder for hermetic use case testing."""

    def analyze(
        self,
        signal: AudioSignal,
        f0_floor: Hertz,
        f0_ceil: Hertz,
        frame_period: FramePeriod,
        method: str = "dio",
    ) -> ParametricVoice:
        n_frames = 10
        f0 = PitchContour(np.full(n_frames, 220.0, dtype=np.float64), frame_period)
        sp = SpectralEnvelope(np.ones((n_frames, 1025), dtype=np.float64))
        ap = Aperiodicity(np.zeros((n_frames, 1025), dtype=np.float64))
        return ParametricVoice(f0=f0, sp=sp, ap=ap, sample_rate=signal.sample_rate)

    def synthesize(self, voice: ParametricVoice) -> AudioSignal:
        samples = np.ones(100, dtype=np.float64) * 0.5
        return AudioSignal(samples=samples, sample_rate=voice.sample_rate)


class FakeVoiceCache:
    """In-memory fake voice cache."""

    def __init__(self) -> None:
        self.store: dict[str, ParametricVoice] = {}

    def load(self, key: str) -> ParametricVoice | None:
        return self.store.get(key)

    def save(self, key: str, voice: ParametricVoice) -> None:
        self.store[key] = voice


def test_decompose_voice_use_case_with_cache() -> None:
    """DecomposeVoice should utilize and populate the voice cache."""
    vocoder = FakeVocoder()
    cache = FakeVoiceCache()
    use_case = DecomposeVoice(vocoder=vocoder, cache=cache)

    sr = SampleRate(44100)
    sig = AudioSignal(samples=np.ones(100, dtype=np.float64) * 0.1, sample_rate=sr)

    cmd = DecomposeVoiceCommand(signal=sig, cache_key="test_take_1")
    voice1 = use_case.execute(cmd)

    assert "test_take_1" in cache.store
    # Second execution should return from cache
    voice2 = use_case.execute(cmd)
    assert voice1 is voice2


def test_resynthesize_voice_use_case() -> None:
    """ResynthesizeVoice should return an AudioSignal from the vocoder."""
    vocoder = FakeVocoder()
    use_case = ResynthesizeVoice(vocoder=vocoder)

    sr = SampleRate(44100)
    f0 = PitchContour(np.full(10, 220.0, dtype=np.float64), FramePeriod(5.0))
    sp = SpectralEnvelope(np.ones((10, 1025), dtype=np.float64))
    ap = Aperiodicity(np.zeros((10, 1025), dtype=np.float64))
    voice = ParametricVoice(f0=f0, sp=sp, ap=ap, sample_rate=sr)

    res = use_case.execute(ResynthesizeVoiceCommand(voice=voice))
    assert isinstance(res, AudioSignal)
    assert len(res) == 100


def test_reshape_formants_use_case_with_vocal_tract_scale() -> None:
    sr = SampleRate(44100)
    f0 = PitchContour(np.full(10, 220.0, dtype=np.float64), FramePeriod(5.0))
    sp = SpectralEnvelope(np.ones((10, 1025), dtype=np.float64))
    ap = Aperiodicity(np.zeros((10, 1025), dtype=np.float64))
    voice = ParametricVoice(f0=f0, sp=sp, ap=ap, sample_rate=sr)

    use_case = ReshapeFormants()
    reshaped = use_case.execute(
        ReshapeFormantsCommand(voice=voice, tract_scale=VocalTractScale(1.18))
    )

    assert reshaped.sp is not voice.sp
    assert reshaped.f0 is voice.f0


def test_reshape_formants_out_of_range_window_raises() -> None:
    sr = SampleRate(44100)
    # 10 frames at 5ms = 0.05s
    f0 = PitchContour(np.full(10, 220.0, dtype=np.float64), FramePeriod(5.0))
    sp = SpectralEnvelope(np.ones((10, 1025), dtype=np.float64))
    ap = Aperiodicity(np.zeros((10, 1025), dtype=np.float64))
    voice = ParametricVoice(f0=f0, sp=sp, ap=ap, sample_rate=sr)

    use_case = ReshapeFormants()
    with pytest.raises(WindowOutOfRangeError):
        use_case.execute(
            ReshapeFormantsCommand(
                voice=voice,
                target_vowel=IPA_VOWEL_TABLE["o"],
                vowel_window=(0.0, 1.0),  # Exceeds 0.05s
            )
        )
