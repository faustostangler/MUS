"""Unit tests for phonetic modeling, formant manipulation, and vocal tract scaling."""

import numpy as np
import pytest

from mus.shared_kernel.units import FramePeriod, SampleRate
from mus.voice_modeling.domain.parametric_voice import SpectralEnvelope
from mus.voice_modeling.domain.phonetics import (
    IPA_VOWEL_TABLE,
    FormantTarget,
    VocalTractScale,
    VoiceCategory,
    estimate_formants_lpc,
    generate_allpole_envelope,
    substitute_vowel,
    warp_spectral_envelope,
)


def test_vocal_tract_scale_validation() -> None:
    # Valid alpha in [0.70, 1.40]
    scale = VocalTractScale(1.0)
    assert scale.alpha == 1.0

    scale_soprano = VocalTractScale(1.18)
    assert scale_soprano.alpha == 1.18

    with pytest.raises(ValueError, match="alpha must be in"):
        VocalTractScale(0.69)

    with pytest.raises(ValueError, match="alpha must be in"):
        VocalTractScale(1.41)


def test_voice_category_scales() -> None:
    assert VoiceCategory.BASS.tract_scale.alpha == pytest.approx(0.88)
    assert VoiceCategory.BARITONE.tract_scale.alpha == pytest.approx(0.94)
    assert VoiceCategory.TENOR.tract_scale.alpha == pytest.approx(1.00)
    assert VoiceCategory.ALTO.tract_scale.alpha == pytest.approx(1.08)
    assert VoiceCategory.MEZZO.tract_scale.alpha == pytest.approx(1.12)
    assert VoiceCategory.SOPRANO.tract_scale.alpha == pytest.approx(1.18)


def test_formant_target_invariants() -> None:
    target = FormantTarget(f1=730.0, f2=1090.0, f3=2440.0)
    assert target.f1 == 730.0
    assert target.f2 == 1090.0

    with pytest.raises(ValueError, match="F2 must be greater than F1"):
        FormantTarget(f1=1200.0, f2=1000.0)

    with pytest.raises(ValueError, match="Formant frequencies must be positive"):
        FormantTarget(f1=-100.0, f2=1000.0)


def test_ipa_vowel_table_coverage() -> None:
    # Must cover European languages (EN, PT, ES, FR, IT) and Portuguese/French nasals
    required_vowels = [
        "i",
        "e",
        "ɛ",
        "a",
        "ɔ",
        "o",
        "u",  # Cardinal oral
        "ã",
        "õ",
        "ẽ",
        "ĩ",
        "ũ",  # Portuguese nasals
        "y",
        "ø",
        "œ",
        "ə",  # French / central
    ]
    for v in required_vowels:
        assert v in IPA_VOWEL_TABLE, f"Missing IPA vowel: {v}"
        target = IPA_VOWEL_TABLE[v]
        assert target.f2 > target.f1 > 0


def test_warp_spectral_envelope_c4_peak_shift() -> None:
    # S3-01: SP with a single peak at 1000 Hz, alpha=1.18 -> peak at 1180 Hz +- 1 bin;
    # alpha=1.0 -> output equals input; total log-energy change < 0.5 dB.
    sr = 44100
    n_bins = 1025
    freqs = np.linspace(0, sr / 2, n_bins)
    bin_hz = (sr / 2) / (n_bins - 1)

    # Synthetic SP frame with a Gaussian peak at 1000 Hz
    peak_idx = round(1000.0 / bin_hz)
    sp_frame = np.exp(-0.5 * ((np.arange(n_bins) - peak_idx) / 3.0) ** 2) + 1e-6
    sp_matrix = np.tile(sp_frame, (5, 1))
    sp = SpectralEnvelope(data=sp_matrix)

    # alpha = 1.0 -> identical
    sp_identity = warp_spectral_envelope(sp, VocalTractScale(1.0), SampleRate(sr))
    assert np.allclose(sp_identity.data, sp.data, rtol=1e-4)

    # alpha = 1.18 -> peak at 1180 Hz +- 1 bin
    scale = VocalTractScale(1.18)
    sp_warped = warp_spectral_envelope(sp, scale, SampleRate(sr))

    warped_peak_bin = int(np.argmax(sp_warped.data[0]))
    warped_peak_hz = freqs[warped_peak_bin]
    expected_peak_hz = 1000.0 * 1.18  # 1180 Hz

    assert abs(warped_peak_hz - expected_peak_hz) <= (bin_hz * 1.5)

    # Total log-energy change < 0.5 dB
    orig_energy = np.sum(sp.data[0])
    warped_energy = np.sum(sp_warped.data[0])
    delta_db = abs(10.0 * np.log10(warped_energy / orig_energy))
    assert delta_db < 0.5


def test_lpc_formant_estimation_accuracy() -> None:
    # S3-03: For synthetic vowel, LPC estimate of F1/F2 within <= 8% of target
    sr = 44100
    fft_size = 2048
    vowel_a = IPA_VOWEL_TABLE["a"]  # (730, 1090)

    env = generate_allpole_envelope(
        formants=[vowel_a.f1, vowel_a.f2, vowel_a.f3],
        sample_rate=sr,
        fft_size=fft_size,
    )

    f1_est, f2_est = estimate_formants_lpc(
        sp_frame=env,
        sample_rate=SampleRate(sr),
        order=16,
    )

    assert abs(f1_est - vowel_a.f1) / vowel_a.f1 <= 0.08
    assert abs(f2_est - vowel_a.f2) / vowel_a.f2 <= 0.08


def test_vowel_substitution_warp_mode() -> None:
    # S3-04: /a/ take, window [0.5 s, 1.5 s] -> /o/
    # inside window F1/F2 close to target, outside window bit-identical
    sr = 44100
    n_frames = 400  # 400 * 5ms = 2.0s
    fft_size = 2048
    vowel_a = IPA_VOWEL_TABLE["a"]
    vowel_o = IPA_VOWEL_TABLE["o"]

    frame_a = generate_allpole_envelope(
        formants=[vowel_a.f1, vowel_a.f2, vowel_a.f3],
        sample_rate=sr,
        fft_size=fft_size,
    )
    sp_matrix = np.tile(frame_a, (n_frames, 1))
    sp = SpectralEnvelope(data=sp_matrix)
    fp = FramePeriod(5.0)

    # Window from 0.5s to 1.5s -> frames 100 to 300
    modified_sp = substitute_vowel(
        spectral_envelope=sp,
        target_vowel=vowel_o,
        start_seconds=0.5,
        end_seconds=1.5,
        frame_period=fp,
        sample_rate=SampleRate(sr),
    )

    # Outside the window (frames 0..80 and 320..399) must be bit-identical
    assert np.array_equal(modified_sp.data[:80], sp.data[:80])
    assert np.array_equal(modified_sp.data[320:], sp.data[320:])

    # Mid-window frame (frame 200, 1.0s) should match vowel_o formants within 10%
    mid_frame = modified_sp.data[200]
    f1_est, f2_est = estimate_formants_lpc(
        sp_frame=mid_frame,
        sample_rate=SampleRate(sr),
        order=16,
    )
    assert abs(f1_est - vowel_o.f1) / vowel_o.f1 <= 0.10
    assert abs(f2_est - vowel_o.f2) / vowel_o.f2 <= 0.10
