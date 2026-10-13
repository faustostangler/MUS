"""Synthetic audio and music signal generators for deterministic test fixtures.

Zero copyrighted audio: all tests use mathematical signals with known ground truth.
"""

from typing import Final

import numpy as np

DEFAULT_SR: Final[int] = 44100


def harmonic_tone(
    f0_hz: float,
    seconds: float = 2.0,
    sr: int = DEFAULT_SR,
    n_harmonics: int = 8,
) -> np.ndarray:
    """Generates a synthetic sawtooth-like harmonic tone with ground-truth F0."""
    t = np.linspace(0, seconds, int(seconds * sr), endpoint=False, dtype=np.float64)
    signal = np.zeros_like(t)
    for k in range(1, n_harmonics + 1):
        freq = k * f0_hz
        if freq >= sr / 2:
            break
        amplitude = 1.0 / k
        signal += amplitude * np.sin(2 * np.pi * freq * t)
    max_val = np.max(np.abs(signal))
    if max_val > 0:
        signal = signal / max_val * 0.8
    return signal
