"""Integration tests for PyWorldVocoder and SoundfileAudioIO adapters.

Covers: S1-01, S1-02, S1-03.
"""

from pathlib import Path

import numpy as np
import pytest

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import FramePeriod, Hertz, SampleRate
from mus.voice_modeling.infrastructure.pyworld_vocoder import PyWorldVocoder
from mus.voice_modeling.infrastructure.soundfile_audio_io import SoundfileAudioIO
from tests.fixtures.signals import harmonic_tone


@pytest.mark.integration
def test_soundfile_audio_io_write_and_read(tmp_path: Path) -> None:
    """Covers S1-02: Writes PCM_24 WAV and reads it back as mono float64 AudioSignal."""
    io = SoundfileAudioIO()
    sr = SampleRate(44100)
    samples = harmonic_tone(f0_hz=220.0, seconds=0.5, sr=sr.value)
    signal = AudioSignal(samples=samples, sample_rate=sr)

    wav_file = tmp_path / "test_tone.wav"
    io.write(signal, wav_file)
    assert wav_file.exists()

    loaded = io.read(wav_file, target_rate=sr)
    assert loaded.sample_rate == sr
    assert len(loaded) == len(signal)
    assert np.allclose(loaded.samples, signal.samples, atol=1e-4)


@pytest.mark.integration
def test_pyworld_vocoder_decompose_and_resynthesize() -> None:
    """Covers S1-01, S1-03: Decompose harmonic tone and resynthesize back to AudioSignal."""
    vocoder = PyWorldVocoder()
    sr = SampleRate(44100)
    samples = harmonic_tone(f0_hz=220.0, seconds=1.0, sr=sr.value)
    signal = AudioSignal(samples=samples, sample_rate=sr)

    voice = vocoder.analyze(
        signal=signal,
        f0_floor=Hertz(65.0),
        f0_ceil=Hertz(1100.0),
        frame_period=FramePeriod(5.0),
        method="dio",
    )

    assert voice.n_frames == pytest.approx(1000 / 5 + 1, abs=5)
    assert voice.fft_size == 2048
    assert voice.n_bins == 1025

    # Voiced frames should be close to 220 Hz
    voiced_f0 = voice.f0.f0[voice.f0.voiced_mask]
    assert len(voiced_f0) > 0
    assert np.median(voiced_f0) == pytest.approx(220.0, rel=0.05)

    # Resynthesis
    resynthesized = vocoder.synthesize(voice)
    assert isinstance(resynthesized, AudioSignal)
    assert resynthesized.sample_rate == sr
    # Length within ±1 frame
    assert abs(len(resynthesized) - len(signal)) <= int(0.005 * sr.value) + 1
