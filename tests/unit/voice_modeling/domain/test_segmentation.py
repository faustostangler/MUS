"""Tests for silence-based audio segmentation and stitching.

Covers: S1-04, S1-05.
"""

import numpy as np

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import SampleRate
from mus.voice_modeling.domain.segmentation import (
    split_on_silence,
    stitch_segments,
)


def test_split_on_silence_detects_gap() -> None:
    """Covers S1-04: two tones separated by 400ms silence."""
    sr = SampleRate(44100)
    fs = sr.value

    tone1 = np.sin(2 * np.pi * 220 * np.linspace(0, 1.0, fs, endpoint=False)) * 0.5
    silence = np.zeros(int(0.4 * fs))  # 400ms silence
    tone2 = np.sin(2 * np.pi * 440 * np.linspace(0, 1.0, fs, endpoint=False)) * 0.5

    samples = np.concatenate([tone1, silence, tone2])
    signal = AudioSignal(samples=samples, sample_rate=sr)

    segments = split_on_silence(
        signal=signal,
        silence_dbfs=-40.0,
        min_silence_seconds=0.2,
        max_segment_seconds=30.0,
    )

    assert len(segments) == 2
    assert segments[0].start_sample == 0
    assert segments[1].end_sample == len(samples)


def test_stitch_segments_reconstructs_continuous_signal() -> None:
    """Covers S1-04: stitch reconstructed signals without clicks."""
    sr = SampleRate(44100)
    fs = sr.value

    part1 = np.ones(fs, dtype=np.float64) * 0.3
    part2 = np.ones(fs, dtype=np.float64) * 0.3

    sig1 = AudioSignal(samples=part1, sample_rate=sr)
    sig2 = AudioSignal(samples=part2, sample_rate=sr)

    stitched = stitch_segments([sig1, sig2], overlap_samples=100)
    assert len(stitched) == 2 * fs - 100
    assert not np.any(np.isnan(stitched.samples))
