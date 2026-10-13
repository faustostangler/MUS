"""Spike-001: WORLD round-trip calibration (throwaway, KISS, never imports src/).

Answers PLAN-001 Step 0.2 questions with numbers:
  1. harvest vs dio+stonemask: real-time factor, voiced ratio, octave-jump rate
  2. round-trip F0 RMSE (cents) and MCD (dB)
  3. peak RSS for a full take
  4. LPC formant estimation accuracy on synthetic vowels
  5. listening WAVs (transpose / tract scale) in ./out

Run: uv run python sandbox/spike-001-world-roundtrip/spike.py [--seconds 60]
"""

import argparse
import json
import resource
import time
from pathlib import Path

import librosa
import numpy as np
import pyworld as pw
import scipy.linalg
import soundfile as sf

HERE = Path(__file__).parent
OUT = HERE / "out"
OUT.mkdir(exist_ok=True)
LIB = HERE.parents[1] / "data" / "library"
FS = 44100
FP = 5.0
STEMS = [
    "Jazz/Frank Sinatra - I've Got You Under My Skin - vocals.mp3",
    "Country/John Denver - Take Me Home, Country Roads (Original Version) - vocals.mp3",
    "Folk/Simon & Garfunkel - The Sound of Silence (Acoustic Version) - vocals.mp3",
]
VOWELS = {  # Peterson & Barney 1952, adult male
    "a": (730, 1090, 2440),
    "e": (530, 1840, 2480),
    "i": (270, 2290, 3010),
    "o": (570, 840, 2410),
    "u": (300, 870, 2240),
}


def rss_mb():
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024


def analyze(x, method):
    t0 = time.perf_counter()
    if method == "harvest":
        f0, t = pw.harvest(x, FS, f0_floor=65, f0_ceil=1100, frame_period=FP)
    else:
        f0, t = pw.dio(x, FS, f0_floor=65, f0_ceil=1100, frame_period=FP)
        f0 = pw.stonemask(x, f0, t, FS)
    t_f0 = time.perf_counter() - t0
    sp = pw.cheaptrick(x, f0, t, FS)
    ap = pw.d4c(x, f0, t, FS)
    return f0, sp, ap, t_f0, time.perf_counter() - t0


def f0_rmse_cents(a, b):
    n = min(len(a), len(b))
    a, b = a[:n], b[:n]
    m = (a > 0) & (b > 0)
    if not m.any():
        return float("nan")
    return float(np.sqrt(np.mean((1200 * np.log2(a[m] / b[m])) ** 2)))


def mcd(sp_a, sp_b, f0):
    n = min(len(sp_a), len(sp_b), len(f0))
    ca = pw.code_spectral_envelope(sp_a[:n], FS, 25)[:, 1:]
    cb = pw.code_spectral_envelope(sp_b[:n], FS, 25)[:, 1:]
    m = f0[:n] > 0
    d = np.sqrt(2 * np.sum((ca[m] - cb[m]) ** 2, axis=1))
    return float((10 / np.log(10)) * d.mean())


def octave_jump_rate(f0):
    v = f0 > 0
    a, b = f0[:-1], f0[1:]
    both = v[:-1] & v[1:]
    jumps = np.abs(1200 * np.log2(b[both] / a[both])) > 900
    return float(jumps.mean()) if both.any() else 0.0


def allpole_envelope(formants, fft_size, bws=(60, 90, 120), tilt_db_oct=-12.0):
    freqs = np.linspace(0, FS / 2, fft_size // 2 + 1)
    z = np.exp(1j * 2 * np.pi * freqs / FS)
    h = np.ones_like(z)
    for f, bw in zip(formants, bws, strict=False):
        r = np.exp(-np.pi * bw / FS)
        p = r * np.exp(1j * 2 * np.pi * f / FS)
        h = h / ((1 - p / z) * (1 - np.conj(p) / z))
    mag = np.abs(h) ** 2
    tilt = 10 ** ((tilt_db_oct * np.log2(np.maximum(freqs, 50) / 100)) / 10)
    return np.maximum(mag * tilt, 1e-16)


def synthetic_vowel(v, f0_hz=196.0, seconds=2.0):
    fft = pw.get_cheaptrick_fft_size(FS)
    n = int(seconds * 1000 / FP) + 1
    env = allpole_envelope(VOWELS[v], fft)
    sp = np.tile(env, (n, 1)) * 1e-4
    ap = np.tile(np.clip(np.linspace(0.02, 0.6, fft // 2 + 1), 0, 1), (n, 1))
    f0 = np.full(n, f0_hz)
    y = pw.synthesize(f0, sp, ap, FS, FP)
    return y / (np.abs(y).max() + 1e-9) * 0.8


def lpc_formants(sp_frame, order):
    # Decimate envelope to 0..5.5 kHz band to concentrate poles on F1..F3.
    nbins = len(sp_frame)
    cut = int(nbins * 5500 / (FS / 2))
    band = sp_frame[:cut]
    fs_eff = 2 * 5500
    r = np.fft.irfft(band)[: order + 1]
    a = scipy.linalg.solve_toeplitz(r[:order], -r[1 : order + 1])
    roots = np.roots(np.concatenate([[1.0], a]))
    roots = roots[np.imag(roots) > 0]
    f = np.angle(roots) * fs_eff / (2 * np.pi)
    bw = -np.log(np.abs(roots)) * fs_eff / np.pi
    keep = (bw < 400) & (f > 90) & (f < 5000)
    return np.sort(f[keep])[:3]


def main():
    ap_ = argparse.ArgumentParser()
    ap_.add_argument("--seconds", type=float, default=60.0)
    args = ap_.parse_args()
    report = {"real_stems": [], "synthetic": {}, "formants": {}}

    # Q4 + synthetic round-trip
    for v in VOWELS:
        x = synthetic_vowel(v)
        f0, sp, ap, _, _ = analyze(x, "harvest")
        y = pw.synthesize(f0, sp, ap, FS, FP)
        f0b, spb, _, _, _ = analyze(y, "harvest")
        report["synthetic"][v] = {
            "f0_rmse_cents": round(f0_rmse_cents(f0, f0b), 2),
            "mcd_db": round(mcd(sp, spb, f0), 3),
            "median_f0": round(float(np.median(f0[f0 > 0])), 2),
        }
        mid = sp[len(sp) // 2]
        report["formants"][v] = {
            str(order): [round(float(q)) for q in lpc_formants(mid, order)]
            for order in (10, 12, 14, 18)
        }
        report["formants"][v]["truth"] = VOWELS[v]
        sf.write(OUT / f"synthetic_{v}.wav", x, FS)

    # Q1-3, Q5 on real stems
    for rel in STEMS:
        path = LIB / rel
        if not path.exists():
            print("missing", path)
            continue
        x, _ = librosa.load(path, sr=FS, mono=True, duration=args.seconds, offset=30.0)
        x = np.ascontiguousarray(x, dtype=np.float64)
        dur = len(x) / FS
        entry = {"stem": rel, "seconds": round(dur, 1)}
        for method in ("dio", "harvest"):
            rss0 = rss_mb()
            f0, sp, ap, t_f0, t_all = analyze(x, method)
            y = pw.synthesize(f0, sp, ap, FS, FP)
            f0b, spb, _, _, _ = analyze(y, method)
            entry[method] = {
                "rtf_f0": round(t_f0 / dur, 3),
                "rtf_total": round(t_all / dur, 3),
                "voiced_ratio": round(float((f0 > 0).mean()), 3),
                "octave_jump_rate": round(octave_jump_rate(f0), 5),
                "f0_rmse_cents": round(f0_rmse_cents(f0, f0b), 2),
                "mcd_db": round(mcd(sp, spb, f0), 3),
                "sp_mb_float64": round(sp.nbytes / 2**20, 1),
                "peak_rss_mb": round(rss_mb(), 1),
                "rss_delta_mb": round(rss_mb() - rss0, 1),
            }
            if method == "harvest":
                stem_name = Path(rel).stem.replace(" ", "_")[:40]
                sf.write(OUT / f"{stem_name}_roundtrip.wav", y / max(1, np.abs(y).max()), FS)
                for st in (-7, -3, 3, 7):
                    y2 = pw.synthesize(f0 * 2 ** (st / 12), sp, ap, FS, FP)
                    sf.write(OUT / f"{stem_name}_tr{st:+d}.wav", y2 / max(1, np.abs(y2).max()), FS)
                fft = sp.shape[1]
                freqs = np.linspace(0, FS / 2, fft)
                for alpha in (0.88, 1.18):
                    sp2 = np.array([np.exp(np.interp(freqs / alpha, freqs, np.log(r))) for r in sp])
                    y3 = pw.synthesize(f0, sp2, ap, FS, FP)
                    sf.write(OUT / f"{stem_name}_alpha{alpha}.wav", y3 / max(1, np.abs(y3).max()), FS)
        report["real_stems"].append(entry)
        print(json.dumps(entry, indent=1))

    (HERE / "results.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report["synthetic"], indent=1))
    print(json.dumps(report["formants"], indent=1))


if __name__ == "__main__":
    main()
