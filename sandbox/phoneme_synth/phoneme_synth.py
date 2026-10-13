#!/usr/bin/env python3
"""Phoneme & Vowel Synthesizer (MUS Sandbox Spike-002).

Rapid-prototyping acoustic phoneme synthesizer using Source-Filter vocal modeling.
Supports 7 Brazilian Portuguese vowels (/i/, /e/, /ɛ/, /a/, /ɔ/, /o/, /u/) across 4 vocal classes
(Baixo/Barítono, Tenor, Contralto/Mezzo, Soprano), customizable F1/F2/F3 formants, and consonants
(plosives /p, t, k, b, d/, fricatives /s, ʃ, f, z/, nasals /m, n/, liquids /l/).

Run:
    uv run python sandbox/phoneme_synth/phoneme_synth.py --help
    uv run python sandbox/phoneme_synth/phoneme_synth.py --vowel a --voice tenor --note A3
    uv run python sandbox/phoneme_synth/phoneme_synth.py --consonant s --vowel a --note C4
    uv run python sandbox/phoneme_synth/phoneme_synth.py --batch-demo
"""

import argparse
import math
from pathlib import Path

import numpy as np
import scipy.signal
import soundfile as sf

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
FS = 44100  # 44.1 kHz standard audio sample rate

# Table of 16 English Vowels (Highlighting 7 Common with Brazilian Portuguese)
VOWEL_TABLE = {
    "/i/": {
        "label": "/i/ (vi / beat)",
        "sample_word_pt": "vi",
        "sample_word_en": "beat / fleece",
        "common_pt": True,
        "bass_baritone": (250, 2100, 2700),
        "tenor": (280, 2300, 2900),
        "contralto_mezzo": (320, 2500, 3100),
        "soprano": (370, 2800, 3300),
    },
    "/ɪ/": {
        "label": "/ɪ/ (bit / kit)",
        "sample_word_pt": "-",
        "sample_word_en": "bit / kit",
        "common_pt": False,
        "bass_baritone": (360, 1800, 2350),
        "tenor": (400, 1980, 2550),
        "contralto_mezzo": (450, 2150, 2750),
        "soprano": (500, 2350, 2950),
    },
    "/e/": {
        "label": "/e/ (vê / bait)",
        "sample_word_pt": "vê",
        "sample_word_en": "bait / face",
        "common_pt": True,
        "bass_baritone": (380, 1850, 2500),
        "tenor": (400, 2000, 2650),
        "contralto_mezzo": (460, 2200, 2850),
        "soprano": (520, 2400, 3100),
    },
    "/ɛ/": {
        "label": "/ɛ/ (pé / bet)",
        "sample_word_pt": "pé",
        "sample_word_en": "bet / dress",
        "common_pt": True,
        "bass_baritone": (500, 1650, 2450),
        "tenor": (550, 1800, 2600),
        "contralto_mezzo": (610, 1950, 2800),
        "soprano": (690, 2150, 3000),
    },
    "/æ/": {
        "label": "/æ/ (cat / bat)",
        "sample_word_pt": "-",
        "sample_word_en": "cat / trap",
        "common_pt": False,
        "bass_baritone": (630, 1500, 2300),
        "tenor": (700, 1660, 2500),
        "contralto_mezzo": (780, 1820, 2700),
        "soprano": (860, 2000, 2900),
    },
    "/a/": {
        "label": "/a/ (pá / palm)",
        "sample_word_pt": "pá",
        "sample_word_en": "palm / father",
        "common_pt": True,
        "bass_baritone": (650, 1200, 2400),
        "tenor": (750, 1300, 2550),
        "contralto_mezzo": (820, 1400, 2750),
        "soprano": (950, 1550, 2950),
    },
    "/ʌ/": {
        "label": "/ʌ/ (cup / but)",
        "sample_word_pt": "-",
        "sample_word_en": "cup / strut",
        "common_pt": False,
        "bass_baritone": (570, 1130, 2250),
        "tenor": (640, 1250, 2450),
        "contralto_mezzo": (700, 1380, 2650),
        "soprano": (780, 1500, 2850),
    },
    "/ə/": {
        "label": "/ə/ (about / schwa)",
        "sample_word_pt": "-",
        "sample_word_en": "about / comma",
        "common_pt": False,
        "bass_baritone": (450, 1360, 2300),
        "tenor": (500, 1500, 2500),
        "contralto_mezzo": (550, 1640, 2720),
        "soprano": (600, 1800, 2950),
    },
    "/ɜː/": {
        "label": "/ɜː/ (bird / nurse)",
        "sample_word_pt": "-",
        "sample_word_en": "bird / nurse",
        "common_pt": False,
        "bass_baritone": (440, 1220, 1550),
        "tenor": (490, 1350, 1690),
        "contralto_mezzo": (540, 1480, 1850),
        "soprano": (590, 1600, 2000),
    },
    "/ɒ/": {
        "label": "/ɒ/ (lot / pot)",
        "sample_word_pt": "-",
        "sample_word_en": "pot / lot",
        "common_pt": False,
        "bass_baritone": (620, 980, 2280),
        "tenor": (700, 1080, 2450),
        "contralto_mezzo": (760, 1180, 2650),
        "soprano": (850, 1300, 2850),
    },
    "/ɔ/": {
        "label": "/ɔ/ (pó / thought)",
        "sample_word_pt": "pó",
        "sample_word_en": "thought / law",
        "common_pt": True,
        "bass_baritone": (520, 950, 2400),
        "tenor": (560, 1050, 2500),
        "contralto_mezzo": (620, 1150, 2700),
        "soprano": (700, 1250, 2900),
    },
    "/o/": {
        "label": "/o/ (avô / boat)",
        "sample_word_pt": "avô",
        "sample_word_en": "boat / goat",
        "common_pt": True,
        "bass_baritone": (370, 800, 2350),
        "tenor": (400, 850, 2450),
        "contralto_mezzo": (450, 950, 2650),
        "soprano": (500, 1050, 2850),
    },
    "/ʊ/": {
        "label": "/ʊ/ (put / book)",
        "sample_word_pt": "-",
        "sample_word_en": "put / book",
        "common_pt": False,
        "bass_baritone": (400, 920, 2150),
        "tenor": (450, 1030, 2350),
        "contralto_mezzo": (500, 1140, 2550),
        "soprano": (550, 1250, 2750),
    },
    "/u/": {
        "label": "/u/ (tu / boot)",
        "sample_word_pt": "tu",
        "sample_word_en": "boot / goose",
        "common_pt": True,
        "bass_baritone": (280, 680, 2300),
        "tenor": (300, 720, 2400),
        "contralto_mezzo": (350, 800, 2600),
        "soprano": (400, 900, 2800),
    },
    "/aɪ/": {
        "label": "/aɪ/ (bite / price)",
        "sample_word_pt": "-",
        "sample_word_en": "bite / price",
        "common_pt": False,
        "bass_baritone": (520, 1500, 2400),
        "tenor": (580, 1650, 2600),
        "contralto_mezzo": (640, 1800, 2800),
        "soprano": (720, 1950, 3000),
    },
    "/aʊ/": {
        "label": "/aʊ/ (cow / mouth)",
        "sample_word_pt": "-",
        "sample_word_en": "cow / mouth",
        "common_pt": False,
        "bass_baritone": (540, 1000, 2250),
        "tenor": (600, 1100, 2450),
        "contralto_mezzo": (660, 1200, 2650),
        "soprano": (740, 1320, 2850),
    },
}

VOWEL_ALIASES = {
    "i": "/i/", "ee": "/i/", "vi": "/i/", "beat": "/i/",
    "ih": "/ɪ/", "bit": "/ɪ/", "kit": "/ɪ/", "ɪ": "/ɪ/",
    "e": "/e/", "eh": "/e/", "ve": "/e/", "bait": "/e/",
    "ɛ": "/ɛ/", "pe": "/ɛ/", "bet": "/ɛ/",
    "ae": "/æ/", "æ": "/æ/", "cat": "/æ/", "bat": "/æ/",
    "a": "/a/", "pa": "/a/", "palm": "/a/", "ah": "/a/",
    "ʌ": "/ʌ/", "cup": "/ʌ/", "but": "/ʌ/",
    "ə": "/ə/", "schwa": "/ə/", "about": "/ə/",
    "ɜː": "/ɜː/", "ɜ": "/ɜː/", "er": "/ɜː/", "bird": "/ɜː/", "nurse": "/ɜː/",
    "ɒ": "/ɒ/", "pot": "/ɒ/", "lot": "/ɒ/",
    "ɔ": "/ɔ/", "po": "/ɔ/", "thought": "/ɔ/", "law": "/ɔ/",
    "o": "/o/", "oh": "/o/", "avo": "/o/", "boat": "/o/",
    "ʊ": "/ʊ/", "put": "/ʊ/", "book": "/ʊ/",
    "u": "/u/", "oo": "/u/", "tu": "/u/", "boot": "/u/",
    "ai": "/aɪ/", "aɪ": "/aɪ/", "bite": "/aɪ/", "price": "/aɪ/",
    "au": "/aʊ/", "aʊ": "/aʊ/", "cow": "/aʊ/", "mouth": "/aʊ/",
}


def normalize_vowel(v_str: str) -> str:
    """Normalize input string to canonical IPA vowel key."""
    clean = v_str.strip("/ ").lower()
    if f"/{clean}/" in VOWEL_TABLE:
        return f"/{clean}/"
    if clean in VOWEL_ALIASES:
        return VOWEL_ALIASES[clean]
    for k in VOWEL_TABLE:
        if clean in k:
            return k
    return "/a/"

# Initialize custom singer profile for all vowels with tenor as default baseline
for _v in VOWEL_TABLE.values():
    _v["custom"] = _v["tenor"]

VOICE_DEFAULTS = {
    "bass_baritone": {"f0": 110.0, "note": "A2", "label": "Baixo / Barítono"},
    "tenor": {"f0": 146.83, "note": "D3", "label": "Tenor (Ref. Média)"},
    "contralto_mezzo": {"f0": 220.0, "note": "A3", "label": "Contralto / Mezzo"},
    "soprano": {"f0": 293.66, "note": "D4", "label": "Soprano"},
    "custom": {"f0": 146.83, "note": "D3", "label": "Meu Cantor (Personalizado)"},
}

NOTE_FREQS = {
    "C2": 65.41,
    "D2": 73.42,
    "E2": 82.41,
    "F2": 87.31,
    "G2": 98.00,
    "A2": 110.00,
    "B2": 123.47,
    "C3": 130.81,
    "D3": 146.83,
    "E3": 164.81,
    "F3": 174.61,
    "G3": 196.00,
    "A3": 220.00,
    "B3": 246.94,
    "C4": 261.63,
    "D4": 293.66,
    "E4": 329.63,
    "F4": 349.23,
    "G4": 392.00,
    "A4": 440.00,
    "B4": 493.88,
    "C5": 523.25,
    "D5": 587.33,
    "E5": 659.25,
    "F5": 698.46,
    "G5": 783.99,
    "A5": 880.00,
    "B5": 987.77,
    "C6": 1046.50,
}


def note_to_f0(note_or_hz: str | float) -> float:
    """Convert note name (e.g. 'A3') or numeric string to Hz. Return 0.0 for rests."""
    if isinstance(note_or_hz, (int, float)):
        return float(note_or_hz)
    clean = note_or_hz.strip().upper()
    if clean in ("REST", "SILENCE", "PAUSA", "-", "NONE", "SILENCIO"):
        return 0.0
    if clean in NOTE_FREQS:
        return NOTE_FREQS[clean]
    try:
        return float(clean)
    except ValueError:
        return 220.0  # fallback A3


def rosenberg_glottal_pulse(
    n_samples: int, f0: float, fs: int = FS, open_quotient: float = 0.6
) -> np.ndarray:
    """Generate Rosenberg pulse excitation train with natural glottal opening/closing."""
    t = np.arange(n_samples) / fs
    period_samples = fs / max(f0, 20.0)
    phase = (np.arange(n_samples) % period_samples) / period_samples

    # Rosenberg C-model: 3*(t/Tp)^2 - 2*(t/Tp)^3 during open phase, 0 during closed
    pulse = np.zeros(n_samples, dtype=np.float64)
    open_mask = phase < open_quotient
    p_norm = phase[open_mask] / open_quotient
    pulse[open_mask] = 3.0 * (p_norm**2) - 2.0 * (p_norm**3)

    # Derivative to simulate glottal volume velocity derivative (-6 dB/oct radiation impedance)
    deriv = np.diff(pulse, prepend=pulse[0])
    return deriv


def apply_biquad_resonator(x: np.ndarray, f_res: float, bw: float, fs: int = FS) -> np.ndarray:
    """Apply standard 2-pole digital acoustic resonator filter."""
    f_res = max(50.0, min(f_res, fs * 0.48))
    bw = max(20.0, min(bw, f_res * 1.5))
    r = math.exp(-math.pi * bw / fs)
    theta = 2.0 * math.pi * f_res / fs

    # Normalized unity-gain at peak
    b = np.array([1.0 - r, 0.0, 0.0], dtype=np.float64)
    a = np.array([1.0, -2.0 * r * math.cos(theta), r * r], dtype=np.float64)
    return scipy.signal.lfilter(b, a, x)


def synthesize_vowel(
    formants: tuple[float, float, float] = (750.0, 1300.0, 2550.0),
    bws: tuple[float, float, float] = (70.0, 90.0, 130.0),
    f0: float = 146.83,
    duration: float = 1.0,
    fs: int = FS,
    vibrato_rate: float = 5.5,
    vibrato_depth_cents: float = 25.0,
    breathiness: float = 0.03,
) -> np.ndarray:
    """Synthesize isolated vowel using source-filter model."""
    n_samples = int(duration * fs)
    t = np.arange(n_samples) / fs

    # Pitch contour with natural vibrato
    if vibrato_depth_cents > 0:
        vib_ratio = 2.0 ** ((vibrato_depth_cents / 1200.0) * np.sin(2.0 * np.pi * vibrato_rate * t))
        f0_contour = f0 * vib_ratio
    else:
        f0_contour = np.full(n_samples, f0)

    # Rich Glottal source with 64 harmonics (1/n^0.65 tilt)
    # Essential for exciting higher formants (F2, F3) up to 4 kHz!
    phase = 2.0 * np.pi * np.cumsum(f0_contour) / fs
    source = np.zeros(n_samples, dtype=np.float64)
    for n in range(1, 64):
        source += (1.0 / (n**0.65)) * np.sin(n * phase)

    # Add aspiration noise (aperiodicity / breathiness)
    if breathiness > 0:
        noise = np.random.normal(0, 1, n_samples)
        source = (1.0 - breathiness) * source + breathiness * noise

    # Parallel Klatt formant resonator bank
    f1, f2, f3 = formants
    b1, b2, b3 = bws
    y1 = apply_biquad_resonator(source, f1, b1, fs) * 1.0
    y2 = apply_biquad_resonator(source, f2, b2, fs) * 1.35  # boosted F2 for vowel identification
    y3 = apply_biquad_resonator(source, f3, b3, fs) * 0.75
    y4 = apply_biquad_resonator(source, 3600.0, 200.0, fs) * 0.35
    f0_body = np.sin(phase) * 0.08  # subtle fundamental carrier body

    y = y1 + y2 + y3 + y4 + f0_body

    # Apply smooth Hann attack (20ms) and release (40ms)
    attack_n = int(0.02 * fs)
    release_n = int(0.04 * fs)
    env = np.ones(n_samples)
    if attack_n > 0:
        env[:attack_n] = 0.5 * (1.0 - np.cos(np.linspace(0, np.pi, attack_n)))
    if release_n > 0:
        env[-release_n:] = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, release_n)))

    y = y * env
    # Peak normalize to -1 dBFS
    max_val = np.max(np.abs(y))
    if max_val > 1e-9:
        y = (y / max_val) * 0.89
    return y


def synthesize_consonant_vowel(
    consonant: str,
    vowel_formants: tuple[float, float, float],
    f0: float = 146.83,
    duration: float = 1.0,
    fs: int = FS,
) -> np.ndarray:
    """Synthesize Consonant-Vowel (CV) syllable with formant transitions and bursts."""
    c = consonant.lower().strip("/ ")
    vowel_dur = max(0.2, duration - 0.15)

    # 1. Pure vowel base
    vowel_sig = synthesize_vowel(
        formants=vowel_formants,
        f0=f0,
        duration=vowel_dur,
        fs=fs,
    )

    # 2. Consonant prefix synthesis
    if c in ("s", "f", "sh", "ʃ", "z"):
        # Fricative noise
        fric_dur = 0.12
        n_fric = int(fric_dur * fs)
        noise = np.random.normal(0, 1, n_fric)
        if c in ("s", "z"):
            # Alveolar sibilant: 4.5kHz - 8kHz bandpass
            sos = scipy.signal.butter(
                4,
                [4500 / (fs / 2), min(9000, fs / 2 - 500) / (fs / 2)],
                btype="bandpass",
                output="sos",
            )
            fric_sig = scipy.signal.sosfilt(sos, noise)
        elif c in ("sh", "ʃ"):
            # Postalveolar: 2.5kHz - 6kHz bandpass
            sos = scipy.signal.butter(
                4, [2500 / (fs / 2), 6000 / (fs / 2)], btype="bandpass", output="sos"
            )
            fric_sig = scipy.signal.sosfilt(sos, noise)
        else:  # "f"
            # Labiodental: wide flat noise
            sos = scipy.signal.butter(2, 2000 / (fs / 2), btype="highpass", output="sos")
            fric_sig = scipy.signal.sosfilt(sos, noise)

        # Envelope ramp
        fric_env = np.sin(np.linspace(0, np.pi / 2, n_fric))
        fric_sig = fric_sig * fric_env * 0.4
        out = np.concatenate([fric_sig, vowel_sig])

    elif c in ("t", "p", "k", "d", "b", "g"):
        # Stop burst + transient
        burst_dur = 0.02
        n_burst = int(burst_dur * fs)
        burst_noise = np.random.normal(0, 1, n_burst)
        center_f = 3800 if c in ("t", "d") else (1000 if c in ("p", "b") else 2200)
        q = 4.0
        sos = scipy.signal.butter(
            2,
            [max(100, center_f - 400) / (fs / 2), min(fs / 2 - 100, center_f + 400) / (fs / 2)],
            btype="bandpass",
            output="sos",
        )
        burst_sig = scipy.signal.sosfilt(sos, burst_noise) * np.linspace(1, 0, n_burst) * 0.7
        silence = np.zeros(int(0.03 * fs))
        out = np.concatenate([silence, burst_sig, vowel_sig])

    elif c in ("m", "n"):
        # Nasal murmur
        nasal_dur = 0.10
        n_nasal = int(nasal_dur * fs)
        t = np.arange(n_nasal) / fs
        nasal_source = np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(4 * np.pi * f0 * t)
        nasal_sig = apply_biquad_resonator(nasal_source, 270.0, 50.0, fs)
        nasal_env = np.ones(n_nasal)
        nasal_env[: int(0.02 * fs)] = np.linspace(0, 1, int(0.02 * fs))
        nasal_sig = nasal_sig * nasal_env * 0.6
        out = np.concatenate([nasal_sig, vowel_sig])

    elif c in ("l", "r"):
        # Liquid transition
        glide_dur = 0.08
        f1_start = 350.0
        f2_start = 1100.0 if c == "l" else 1500.0
        f3_start = 2800.0 if c == "l" else 1700.0  # dip for /r/
        glide_sig = synthesize_vowel(
            (f1_start, f2_start, f3_start), f0=f0, duration=glide_dur, fs=fs
        )
        out = np.concatenate([glide_sig * 0.7, vowel_sig])
    else:
        out = vowel_sig

    # Final normalization
    peak = np.max(np.abs(out))
    if peak > 0:
        out = (out / peak) * 0.89
    return out


def run_batch_demo(filter_mode: str = "all") -> int:
    """Generate audio files for vowels across voice categories (all 16, or filtered)."""
    print("=" * 80)
    print(f"MUS SPIKE-002: BATCH VOWEL SYNTHESIS (FILTER: {filter_mode.upper()})")
    print("=" * 80)
    generated_files = []

    filtered_vowels = {}
    for v_key, v_info in VOWEL_TABLE.items():
        if filter_mode == "common_pt" and not v_info.get("common_pt", False):
            continue
        if filter_mode == "exclusive_en" and v_info.get("common_pt", False):
            continue
        filtered_vowels[v_key] = v_info

    for v_key, v_info in filtered_vowels.items():
        v_clean = (
            v_key.strip("/ ")
            .replace("ː", "")
            .replace("ɪ", "ih")
            .replace("ɛ", "eh")
            .replace("æ", "ae")
            .replace("ʌ", "ah")
            .replace("ə", "schwa")
            .replace("ɜ", "er")
            .replace("ɒ", "oh")
            .replace("ɔ", "aw")
            .replace("ʊ", "uh")
            .replace("aɪ", "ai")
            .replace("aʊ", "au")
        )
        for voice_key in ["bass_baritone", "tenor", "contralto_mezzo", "soprano"]:
            formants = v_info[voice_key]
            v_default = VOICE_DEFAULTS[voice_key]
            f0 = v_default["f0"]
            filename = f"vowel_{v_clean}_{voice_key}.wav"
            filepath = OUT / filename
            audio = synthesize_vowel(formants=formants, f0=f0, duration=0.8)
            sf.write(filepath, audio, FS)
            pt_tag = " [PT+EN]" if v_info.get("common_pt", False) else " [EN-only]"
            generated_files.append(
                (v_info["label"] + pt_tag, v_default["label"], formants, f0, filepath.name)
            )

    # Sample syllables demo
    syllables = [
        ("t", "/a/", "tenor"),
        ("s", "/i/", "tenor"),
        ("p", "/o/", "bass_baritone"),
        ("m", "/u/", "contralto_mezzo"),
        ("ʃ", "/e/", "soprano"),
        ("b", "/ɪ/", "tenor"),
        ("b", "/æ/", "tenor"),
        ("b", "/ɜː/", "bass_baritone"),
    ]
    for cons, vow, voice in syllables:
        formants = VOWEL_TABLE[vow][voice]
        f0 = VOICE_DEFAULTS[voice]["f0"]
        c_clean = "sh" if cons == "ʃ" else cons
        v_clean = (
            vow.strip("/ ")
            .replace("ː", "")
            .replace("ɪ", "ih")
            .replace("æ", "ae")
            .replace("ɜ", "er")
        )
        filename = f"syllable_{c_clean}_{v_clean}_{voice}.wav"
        filepath = OUT / filename
        audio = synthesize_consonant_vowel(cons, formants, f0=f0, duration=1.0)
        sf.write(filepath, audio, FS)
        print(f"  ✓ Syllable /{cons}{vow.strip('/ ')}/ ({voice}) -> {filename}")

    print("\nSummary of Generated Vowels:")
    print(f"{'Vowel':<28} | {'Voice':<18} | {'F1, F2, F3 (Hz)':<18} | {'F0 (Hz)':<8} | {'File'}")
    print("-" * 90)
    for v_label, voice_label, formants, f0, fname in generated_files:
        f_str = f"{formants[0]}, {formants[1]}, {formants[2]}"
        print(f"{v_label:<28} | {voice_label:<18} | {f_str:<18} | {f0:<8.1f} | {fname}")

    print(f"\nAll files saved to: {OUT}")
    return len(generated_files)


def synthesize_score(
    notes: list[dict],
    voice: str = "tenor",
    bpm: float = 120.0,
    fs: int = FS,
) -> np.ndarray:
    """Synthesize a sequence of notes/syllables (melodic score/solfeggio vocalise).

    Each note dict: {'note': 'C4', 'dur': 0.25, 'vowel': 'a', 'consonant': 'none'}.
    """
    audio_segments = []
    beat_sec = 60.0 / max(30.0, bpm)

    for item in notes:
        n_str = str(item.get("note", "C4")).strip()
        dur = float(item.get("dur", 0.5))
        dur_sec = dur * beat_sec if item.get("is_beats", False) else dur

        is_rest = item.get("is_rest", False) or n_str.upper() in (
            "REST", "SILENCE", "PAUSA", "-", "NONE", "SILENCIO"
        )
        if is_rest:
            seg = np.zeros(max(1, int(round(dur_sec * fs))))
            audio_segments.append(seg)
            continue

        f0 = note_to_f0(n_str)
        v_char = item.get("vowel", "a")
        v_key = normalize_vowel(v_char)
        formants = VOWEL_TABLE[v_key][voice]
        cons = item.get("consonant", "none")

        if cons and cons != "none":
            seg = synthesize_consonant_vowel(cons, formants, f0=f0, duration=dur_sec, fs=fs)
        else:
            seg = synthesize_vowel(formants, f0=f0, duration=dur_sec, fs=fs)
        audio_segments.append(seg)

    full = np.concatenate(audio_segments) if audio_segments else np.zeros(fs)
    peak = np.max(np.abs(full))
    if peak > 0:
        full = (full / peak) * 0.89
    return full


def main() -> None:
    """CLI entry point for acoustic phoneme and score synthesis."""
    parser = argparse.ArgumentParser(description="Acoustic Phoneme & Vowel Synthesizer (MUS)")
    parser.add_argument(
        "--vowel",
        type=str,
        default="a",
        help=(
            "Vowel symbol (16 English vowels: i, ih, e, eh, ae, a, ah, "
            "schwa, er, oh, aw, o, uh, u, ai, au)"
        ),
    )
    parser.add_argument(
        "--voice",
        choices=["bass_baritone", "tenor", "contralto_mezzo", "soprano", "custom"],
        default="tenor",
        help="Voice category (or 'custom' for customized singer)",
    )
    parser.add_argument(
        "--voice-file",
        type=str,
        default=None,
        help="Path to custom singer profile (.json) exported from MUS Vocal Lab",
    )
    parser.add_argument(
        "--filter",
        choices=["all", "common_pt", "exclusive_en"],
        default="all",
        help=(
            "Filter mode for batch demo: 'all' (16 vowels), "
            "'common_pt' (7 common), 'exclusive_en' (9 EN exclusive)"
        ),
    )
    parser.add_argument(
        "--note", type=str, default="A3", help="Musical note (e.g. C3, D4, A3) or F0 in Hz"
    )
    parser.add_argument("--duration", type=float, default=1.0, help="Duration in seconds")
    parser.add_argument("--f1", type=float, default=None, help="Custom F1 formant (Hz)")
    parser.add_argument("--f2", type=float, default=None, help="Custom F2 formant (Hz)")
    parser.add_argument("--f3", type=float, default=None, help="Custom F3 formant (Hz)")
    parser.add_argument(
        "--consonant",
        type=str,
        default=None,
        help="Optional consonant prefix (/s/, /t/, /p/, /m/, /k/, etc.)",
    )
    parser.add_argument(
        "--score",
        type=str,
        default=None,
        help="Score string format: 'C4:0.25:a,D4:0.25:a,E4:0.25:a' (Note:DurationSec:Vowel)",
    )
    parser.add_argument(
        "--bpm",
        type=float,
        default=120.0,
        help="Tempo BPM for score synthesis",
    )
    parser.add_argument(
        "--batch-demo",
        action="store_true",
        help="Generate default vowels and sample syllables into out/",
    )
    parser.add_argument("--out", type=str, default=None, help="Output WAV path")
    args = parser.parse_args()

    # Load custom singer profile JSON if provided
    if args.voice_file:
        voice_path = Path(args.voice_file)
        if voice_path.exists():
            import json
            with open(voice_path, "r", encoding="utf-8") as vf:
                profile = json.load(vf)
            vowels_map = profile.get("vowels", {})
            for sym, data in vowels_map.items():
                canon = normalize_vowel(sym)
                if canon in VOWEL_TABLE:
                    VOWEL_TABLE[canon]["custom"] = (float(data["f1"]), float(data["f2"]), float(data["f3"]))
            args.voice = "custom"
            singer_name = profile.get("name", "Meu Cantor")
            print(f"🎤 Loaded custom singer profile '{singer_name}' from: {voice_path}")
        else:
            print(f"⚠️ Warning: Voice profile file not found: {voice_path}")

    if args.batch_demo:
        count = run_batch_demo(filter_mode=args.filter)
        expected = (
            28
            if args.filter == "common_pt"
            else (36 if args.filter == "exclusive_en" else 64)
        )
        assert count == expected, f"Expected {expected} combinations, got {count}"
        return

    # Handle score melodic line
    if args.score:
        notes = []
        for part in args.score.split(","):
            tokens = part.strip().split(":")
            n_name = tokens[0] if len(tokens) > 0 else "C4"
            RHYTHM_BEATS = {
                "sixteenth": 0.25,
                "semicolcheia": 0.25,
                "eighth": 0.5,
                "colcheia": 0.5,
                "quarter": 1.0,
                "seminima": 1.0,
                "semínima": 1.0,
                "half": 2.0,
                "minima": 2.0,
                "mínima": 2.0,
                "whole": 4.0,
                "semibreve": 4.0,
            }
            raw_dur = tokens[1].lower().strip() if len(tokens) > 1 else "0.5"
            if raw_dur in RHYTHM_BEATS:
                dur = RHYTHM_BEATS[raw_dur]
                is_beats = True
            else:
                try:
                    dur = float(raw_dur)
                    is_beats = False
                except ValueError:
                    dur = 0.5
                    is_beats = False

            vow = tokens[2] if len(tokens) > 2 else "a"
            cons = tokens[3] if len(tokens) > 3 else "none"
            is_rest = n_name.upper() in ("REST", "SILENCE", "PAUSA", "-", "NONE", "SILENCIO")
            notes.append({
                "note": n_name,
                "dur": dur,
                "is_beats": is_beats,
                "vowel": vow,
                "consonant": cons,
                "is_rest": is_rest,
            })

        audio = synthesize_score(notes, voice=args.voice, bpm=args.bpm)
        out_name = f"score_{args.voice}_{len(notes)}notes.wav"
        out_path = Path(args.out) if args.out else OUT / out_name
        sf.write(out_path, audio, FS)
        print(f"✓ Successfully rendered score melody: {out_path}")
        print(f"  Voice: {VOICE_DEFAULTS[args.voice]['label']}")
        print(f"  Notes count: {len(notes)}, Duration: {len(audio)/FS:.2f}s")
        return

    # Lookup defaults
    v_key = normalize_vowel(args.vowel)
    default_formants = VOWEL_TABLE[v_key][args.voice]
    f1 = args.f1 if args.f1 is not None else default_formants[0]
    f2 = args.f2 if args.f2 is not None else default_formants[1]
    f3 = args.f3 if args.f3 is not None else default_formants[2]
    formants = (f1, f2, f3)
    f0 = note_to_f0(args.note)

    # Synthesize
    if args.consonant:
        audio = synthesize_consonant_vowel(args.consonant, formants, f0=f0, duration=args.duration)
        out_name = f"synth_{args.consonant}_{v_key.strip('/ ')}_{args.voice}_{args.note}.wav"
    else:
        audio = synthesize_vowel(formants, f0=f0, duration=args.duration)
        out_name = f"synth_{v_key.strip('/ ')}_{args.voice}_{args.note}.wav"

    out_path = Path(args.out) if args.out else OUT / out_name
    sf.write(out_path, audio, FS)

    # Asserts
    assert len(audio) == int(args.duration * FS) or len(audio) > 0, "Audio buffer must not be empty"
    assert not np.isnan(audio).any(), "Audio buffer must not contain NaN"
    assert np.max(np.abs(audio)) > 0.05, "Synthesized audio should have audible amplitude"

    pt_tag = (
        " [🟢 Comum com Português]"
        if VOWEL_TABLE[v_key].get("common_pt", False)
        else " [🟠 Exclusiva do Inglês]"
    )
    print(f"✓ Successfully generated: {out_path}")
    print(f"  Vowel: {v_key} ({VOWEL_TABLE[v_key]['label']}){pt_tag}")
    print(f"  Voice: {VOICE_DEFAULTS[args.voice]['label']}")
    print(f"  F0: {f0:.2f} Hz (Note: {args.note})")
    print(f"  Formants: F1={f1} Hz, F2={f2} Hz, F3={f3} Hz")
    print(f"  Duration: {args.duration:.2f}s, Samples: {len(audio)}")


if __name__ == "__main__":
    main()
