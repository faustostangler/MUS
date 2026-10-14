"""Tests for SongMetrics value object and estimate_song_metrics domain service (SPEC-005)."""

import numpy as np
import pytest

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.metrics import SongMetrics, estimate_song_metrics
from mus.shared_kernel.units import SampleRate


def test_song_metrics_validation() -> None:
    metrics = SongMetrics(
        tempo_bpm=85.0,
        duration_seconds=180.5,
        time_signature_numerator=4,
        time_signature_denominator=4,
    )
    assert metrics.tempo_bpm == 85.0
    assert metrics.duration_seconds == 180.5
    assert metrics.time_signature_numerator == 4
    assert metrics.time_signature_denominator == 4

    # Invalid tempo
    with pytest.raises(ValueError, match=r"Tempo .* must be between"):
        SongMetrics(tempo_bpm=10.0, duration_seconds=60.0)

    # Invalid duration
    with pytest.raises(ValueError, match="Duration must be positive"):
        SongMetrics(tempo_bpm=120.0, duration_seconds=-5.0)

    # Invalid time signature
    with pytest.raises(ValueError, match="Invalid time signature"):
        SongMetrics(
            tempo_bpm=120.0,
            duration_seconds=60.0,
            time_signature_numerator=0,
            time_signature_denominator=4,
        )


def test_estimate_song_metrics_with_preferred_bpm() -> None:
    sr = SampleRate(44100)
    # 2 seconds of audio
    samples = np.zeros(88200, dtype=np.float64)
    # Add minor noise so it is not silent
    samples[100] = 0.5
    signal = AudioSignal(samples=samples, sample_rate=sr)

    metrics = estimate_song_metrics(signal, preferred_bpm=96.0)
    assert metrics.tempo_bpm == 96.0
    assert pytest.approx(metrics.duration_seconds, rel=1e-3) == 2.0
    assert metrics.time_signature_numerator == 4
    assert metrics.time_signature_denominator == 4


def test_estimate_song_metrics_automatic_detection() -> None:
    sr = 44100
    # Create 4 seconds of rhythmic clicks at 120 BPM (every 0.5 seconds)
    duration = 4.0
    samples = np.zeros(int(sr * duration), dtype=np.float64)
    beat_interval = int(sr * 0.5)
    for i in range(0, len(samples), beat_interval):
        hit_len = min(1000, len(samples) - i)
        samples[i : i + hit_len] = np.sin(np.linspace(0, 2 * np.pi * 10, hit_len))

    signal = AudioSignal(samples=samples, sample_rate=SampleRate(sr))
    metrics = estimate_song_metrics(signal)

    assert 110.0 <= metrics.tempo_bpm <= 130.0
    assert pytest.approx(metrics.duration_seconds, rel=1e-3) == 4.0
    assert metrics.time_signature_numerator == 4
    assert metrics.time_signature_denominator == 4
