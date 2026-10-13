"""Phonetic modeling, vocal tract scaling, and formant manipulation."""

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np
import scipy.interpolate
import scipy.linalg

from mus.shared_kernel.units import FramePeriod, SampleRate
from mus.voice_modeling.domain.parametric_voice import SpectralEnvelope


@dataclass(frozen=True, slots=True)
class VocalTractScale:
    """Vocal tract scale factor alpha in [0.70, 1.40].

    Alpha > 1.0 represents a shorter tract (formants shifted upwards, e.g. soprano).
    Alpha < 1.0 represents a longer tract (formants shifted downwards, e.g. bass).
    """

    alpha: float

    def __post_init__(self) -> None:
        if not (0.70 <= self.alpha <= 1.40):
            raise ValueError(f"VocalTractScale alpha must be in [0.70, 1.40], got {self.alpha}.")


class VoiceCategory(Enum):
    """Vocal classification profiles with calibrated vocal tract scale factors."""

    BASS = 0.88
    BARITONE = 0.94
    TENOR = 1.00
    ALTO = 1.08
    MEZZO = 1.12
    SOPRANO = 1.18

    @property
    def tract_scale(self) -> VocalTractScale:
        """Returns the corresponding VocalTractScale value object."""
        return VocalTractScale(self.value)


@dataclass(frozen=True, slots=True)
class FormantTarget:
    """Acoustic formant resonance frequencies (Hz) and bandwidths."""

    f1: float
    f2: float
    f3: float = 2500.0
    f4: float = 3500.0
    b1: float = 80.0
    b2: float = 100.0
    b3: float = 120.0
    b4: float = 150.0
    is_nasal: bool = False

    def __post_init__(self) -> None:
        if self.f1 <= 0.0 or self.f2 <= 0.0:
            raise ValueError(f"Formant frequencies must be positive: F1={self.f1}, F2={self.f2}.")
        if self.f2 <= self.f1:
            raise ValueError(f"F2 must be greater than F1: F1={self.f1}, F2={self.f2}.")


# Comprehensive European IPA Vowel Inventory (EN, PT, ES, FR, IT + Nasals)
IPA_VOWEL_TABLE: dict[str, FormantTarget] = {
    # Cardinal oral vowels
    "i": FormantTarget(f1=270.0, f2=2290.0, f3=3010.0),
    "e": FormantTarget(f1=530.0, f2=1840.0, f3=2480.0),
    "ɛ": FormantTarget(f1=610.0, f2=1900.0, f3=2600.0),
    "a": FormantTarget(f1=730.0, f2=1090.0, f3=2440.0),
    "ɔ": FormantTarget(f1=570.0, f2=840.0, f3=2410.0),
    "o": FormantTarget(f1=460.0, f2=900.0, f3=2450.0),
    "u": FormantTarget(f1=300.0, f2=870.0, f3=2240.0),
    # Central and close-central vowels
    "ə": FormantTarget(f1=500.0, f2=1500.0, f3=2500.0),
    "ɨ": FormantTarget(f1=320.0, f2=1450.0, f3=2200.0),
    # French rounded front vowels
    "y": FormantTarget(f1=270.0, f2=1750.0, f3=2150.0),
    "ø": FormantTarget(f1=450.0, f2=1500.0, f3=2250.0),
    "œ": FormantTarget(f1=550.0, f2=1300.0, f3=2300.0),
    # English specific vowels
    "æ": FormantTarget(f1=660.0, f2=1720.0, f3=2410.0),
    "ʌ": FormantTarget(f1=640.0, f2=1190.0, f3=2390.0),
    "ʊ": FormantTarget(f1=440.0, f2=1020.0, f3=2240.0),
    "ɪ": FormantTarget(f1=390.0, f2=1990.0, f3=2550.0),  # noqa: RUF001
    # Portuguese & French Nasal Vowels (with broadened bandwidths and lower F1)
    "ã": FormantTarget(f1=650.0, f2=1250.0, f3=2500.0, b1=140.0, b2=150.0, is_nasal=True),
    "õ": FormantTarget(f1=480.0, f2=880.0, f3=2400.0, b1=130.0, b2=140.0, is_nasal=True),
    "ẽ": FormantTarget(f1=450.0, f2=1900.0, f3=2500.0, b1=130.0, b2=140.0, is_nasal=True),
    "ĩ": FormantTarget(f1=280.0, f2=2200.0, f3=2900.0, b1=120.0, b2=130.0, is_nasal=True),
    "ũ": FormantTarget(f1=310.0, f2=850.0, f3=2200.0, b1=120.0, b2=130.0, is_nasal=True),
}


def generate_allpole_envelope(
    formants: list[float],
    sample_rate: int,
    fft_size: int,
    bws: tuple[float, ...] = (80.0, 100.0, 120.0),
    tilt_db_oct: float = -12.0,
) -> np.ndarray:
    """Generates an all-pole synthetic vocal spectral envelope for given formants."""
    n_bins = fft_size // 2 + 1
    freqs = np.linspace(0, sample_rate / 2, n_bins)
    z = np.exp(1j * 2 * np.pi * freqs / sample_rate)
    h = np.ones_like(z, dtype=np.complex128)

    for f, bw in zip(formants, bws, strict=False):
        r = np.exp(-np.pi * bw / sample_rate)
        p = r * np.exp(1j * 2 * np.pi * f / sample_rate)
        h = h / ((1 - p / z) * (1 - np.conj(p) / z))

    mag = np.abs(h) ** 2
    # Apply standard -12 dB/octave glottal spectral tilt roll-off
    tilt = 10 ** ((tilt_db_oct * np.log2(np.maximum(freqs, 50.0) / 100.0)) / 10.0)
    envelope = np.maximum(mag * tilt, 1e-16)
    return np.ascontiguousarray(envelope, dtype=np.float64)


def estimate_formants_lpc(
    sp_frame: np.ndarray,
    sample_rate: SampleRate,
    order: int = 16,
) -> tuple[float, float]:
    """Estimates F1 and F2 formants using LPC on band-limited 5.5 kHz spectrum."""
    nbins = len(sp_frame)
    nyquist = sample_rate.value / 2.0
    cutoff_hz = 5500.0
    cut = int(nbins * cutoff_hz / nyquist)
    band = sp_frame[:cut]
    fs_eff = 2.0 * cutoff_hz

    # Autocorrelation via inverse real FFT
    r = np.fft.irfft(band)[: order + 1]
    if len(r) < order + 1 or np.all(r == 0):
        return (500.0, 1500.0)

    # Solve Toeplitz system for LPC coefficients
    try:
        a = scipy.linalg.solve_toeplitz(r[:order], -r[1 : order + 1])
    except scipy.linalg.LinAlgError:
        return (500.0, 1500.0)

    poly = np.concatenate([[1.0], a])
    roots = np.roots(poly)
    roots = roots[np.imag(roots) > 0]

    freqs = np.angle(roots) * fs_eff / (2.0 * np.pi)
    bandwidths = -np.log(np.maximum(np.abs(roots), 1e-12)) * fs_eff / np.pi

    keep = (bandwidths < 450.0) & (freqs > 90.0) & (freqs < 5000.0)
    valid_freqs = np.sort(freqs[keep])

    if len(valid_freqs) >= 2:
        return (float(valid_freqs[0]), float(valid_freqs[1]))
    if len(valid_freqs) == 1:
        return (float(valid_freqs[0]), float(valid_freqs[0] * 2.0))
    return (500.0, 1500.0)


def warp_spectral_envelope(
    spectral_envelope: SpectralEnvelope,
    tract_scale: VocalTractScale,
    sample_rate: SampleRate,
) -> SpectralEnvelope:
    """Warps spectral envelope by alpha along frequency axis, preserving total frame energy."""
    alpha = tract_scale.alpha
    if math.isclose(alpha, 1.0, rel_tol=1e-5):
        return spectral_envelope

    orig_sp = spectral_envelope.data
    n_frames, n_bins = orig_sp.shape
    freqs = np.linspace(0.0, sample_rate.value / 2.0, n_bins)

    # To shift formants by alpha (e.g. peak at 1000 -> 1000 * alpha):
    # The warped spectrum at frequency f receives energy from original f / alpha.
    source_freqs = freqs / alpha

    warped_matrix = np.empty_like(orig_sp)
    for i in range(n_frames):
        interp = scipy.interpolate.interp1d(
            freqs,
            orig_sp[i],
            kind="cubic",
            bounds_error=False,
            fill_value=(orig_sp[i, 0], orig_sp[i, -1]),
        )
        warped_frame = np.maximum(interp(source_freqs), 1e-16)

        # Preserve total frame energy within < 0.5 dB
        orig_energy = np.sum(orig_sp[i])
        warped_energy = np.sum(warped_frame)
        if warped_energy > 0:
            warped_frame *= orig_energy / warped_energy

        warped_matrix[i] = warped_frame

    return SpectralEnvelope(data=warped_matrix)


def substitute_vowel(
    spectral_envelope: SpectralEnvelope,
    target_vowel: FormantTarget,
    start_seconds: float,
    end_seconds: float,
    *,
    frame_period: FramePeriod,
    sample_rate: SampleRate,
    crossfade_ms: float = 20.0,
) -> SpectralEnvelope:
    """Substitutes formants in a target time window with raised-cosine crossfade."""
    orig_sp = spectral_envelope.data.copy()
    n_frames, n_bins = orig_sp.shape
    fp_ms = frame_period.ms

    start_frame = max(0, round(start_seconds * 1000.0 / fp_ms))
    end_frame = min(n_frames, round(end_seconds * 1000.0 / fp_ms))
    if start_frame >= end_frame:
        return spectral_envelope

    fft_size = (n_bins - 1) * 2
    synthetic_target = generate_allpole_envelope(
        formants=[target_vowel.f1, target_vowel.f2, target_vowel.f3],
        sample_rate=sample_rate.value,
        fft_size=fft_size,
    )

    xfade_frames = max(1, round(crossfade_ms / fp_ms))

    for f_idx in range(start_frame, end_frame):
        # Calculate crossfade weight [0.0, 1.0]
        if f_idx < start_frame + xfade_frames:
            # Fade in
            t = (f_idx - start_frame) / xfade_frames
            weight = 0.5 * (1.0 - math.cos(math.pi * t))
        elif f_idx >= end_frame - xfade_frames:
            # Fade out
            t = (end_frame - f_idx) / xfade_frames
            weight = 0.5 * (1.0 - math.cos(math.pi * t))
        else:
            weight = 1.0

        orig_energy = np.sum(orig_sp[f_idx])
        target_frame = synthetic_target.copy()
        target_energy = np.sum(target_frame)
        if target_energy > 0:
            target_frame *= orig_energy / target_energy

        orig_sp[f_idx] = (1.0 - weight) * orig_sp[f_idx] + weight * target_frame

    return SpectralEnvelope(data=orig_sp)
