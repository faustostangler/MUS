"""Tests for NpzVoiceCache adapter.

Covers: S1-06.
"""

from pathlib import Path

import numpy as np

from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, SampleRate
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)
from mus.voice_modeling.infrastructure.npz_voice_cache import NpzVoiceCache


def test_npz_voice_cache_roundtrip(tmp_path: Path) -> None:
    """Covers S1-06: Persists voice to compressed NPZ and loads it.

    Ensures exact F0 and float32 SP/AP fidelity.
    """
    cache = NpzVoiceCache(cache_dir=tmp_path)
    sr = SampleRate(44100)
    fp = FramePeriod(5.0)

    n_frames = 20
    n_bins = 1025
    f0_arr = np.linspace(200.0, 400.0, n_frames, dtype=np.float64)
    sp_arr = np.ones((n_frames, n_bins), dtype=np.float64) * 0.5
    ap_arr = np.zeros((n_frames, n_bins), dtype=np.float64)

    original_voice = ParametricVoice(
        f0=PitchContour(f0=f0_arr, frame_period=fp),
        sp=SpectralEnvelope(data=sp_arr),
        ap=Aperiodicity(data=ap_arr),
        sample_rate=sr,
    )

    cache_key = "test_cache_hash_123"
    assert cache.load(cache_key) is None

    cache.save(cache_key, original_voice)
    loaded_voice = cache.load(cache_key)

    assert loaded_voice is not None
    assert loaded_voice.sample_rate == sr
    assert loaded_voice.f0.frame_period == fp
    assert np.allclose(loaded_voice.f0.f0, original_voice.f0.f0, atol=1e-12)
    assert np.allclose(loaded_voice.sp.data, original_voice.sp.data, rtol=1e-6)
    assert np.allclose(loaded_voice.ap.data, original_voice.ap.data, rtol=1e-6)
