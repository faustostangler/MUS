"""Unit tests for SoundfileAudioIO adapter verifying WAV and MP3 read/write (SPEC-002 S1)."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import SampleRate
from mus.voice_modeling.infrastructure.soundfile_audio_io import SoundfileAudioIO


@pytest.fixture
def sample_signal() -> AudioSignal:
    sr = SampleRate(44100)
    # 0.5s sine tone at 440 Hz
    t = np.linspace(0, 0.5, int(sr.value * 0.5), endpoint=False)
    samples = 0.5 * np.sin(2 * np.pi * 440.0 * t).astype(np.float64)
    return AudioSignal(samples=samples, sample_rate=sr)


def test_write_and_read_mp3(tmp_path: Path, sample_signal: AudioSignal) -> None:
    io = SoundfileAudioIO()
    mp3_path = tmp_path / "test_tone.mp3"

    io.write(sample_signal, mp3_path)

    assert mp3_path.exists()
    assert mp3_path.stat().st_size > 0

    info = sf.info(str(mp3_path))
    assert info.format == "MP3"

    read_signal = io.read(mp3_path, target_rate=sample_signal.sample_rate)
    assert isinstance(read_signal, AudioSignal)
    assert read_signal.sample_rate == sample_signal.sample_rate
    assert len(read_signal.samples) > 0
    assert read_signal.samples.dtype == np.float64


def test_write_and_read_wav_preserves_compatibility(
    tmp_path: Path, sample_signal: AudioSignal
) -> None:
    io = SoundfileAudioIO()
    wav_path = tmp_path / "test_tone.wav"

    io.write(sample_signal, wav_path)

    assert wav_path.exists()
    assert wav_path.stat().st_size > 0

    read_signal = io.read(wav_path, target_rate=sample_signal.sample_rate)
    assert isinstance(read_signal, AudioSignal)
    expected = sample_signal.samples
    actual = read_signal.samples[: len(expected)]
    assert np.allclose(actual, expected, atol=1e-3)
