"""PyWorld Vocoder adapter implementing VocoderPort."""

import numpy as np
import pyworld as pw

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, Hertz
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)


class PyWorldVocoder:
    """WORLD vocoder adapter (Harvest / DIO + StoneMask, CheapTrick, D4C)."""

    def analyze(
        self,
        signal: AudioSignal,
        f0_floor: Hertz,
        f0_ceil: Hertz,
        frame_period: FramePeriod,
        method: str = "dio",
    ) -> ParametricVoice:
        """Decomposes an AudioSignal into a ParametricVoice."""
        x = signal.samples
        fs = signal.sample_rate.value
        fp = frame_period.ms

        # WORLD C-routines strictly require float64 C-contiguous memory
        if method == "harvest":
            f0, t = pw.harvest(
                x,
                fs,
                f0_floor=f0_floor.value,
                f0_ceil=f0_ceil.value,
                frame_period=fp,
            )
        else:
            f0_raw, t = pw.dio(
                x,
                fs,
                f0_floor=f0_floor.value,
                f0_ceil=f0_ceil.value,
                frame_period=fp,
            )
            f0 = pw.stonemask(x, f0_raw, t, fs)

        sp = pw.cheaptrick(x, f0, t, fs)
        ap = pw.d4c(x, f0, t, fs)

        # Clamping SP to strictly positive for log safety (VM-03)
        sp = np.maximum(sp, 1e-16)
        # Clamping AP to strictly [0.0, 1.0] (VM-04)
        ap = np.clip(ap, 0.0, 1.0)

        pitch_contour = PitchContour(f0=f0, frame_period=frame_period)
        sp_env = SpectralEnvelope(data=sp)
        ap_mat = Aperiodicity(data=ap)

        return ParametricVoice(
            f0=pitch_contour,
            sp=sp_env,
            ap=ap_mat,
            sample_rate=signal.sample_rate,
        )

    def synthesize(self, voice: ParametricVoice) -> AudioSignal:
        """Synthesizes a ParametricVoice back into a continuous AudioSignal."""
        fs = voice.sample_rate.value
        fp = voice.f0.frame_period.ms

        # pyworld Cython MemoryViews require writable, contiguous float64 buffers
        f0 = np.array(voice.f0.f0, dtype=np.float64, copy=True)
        sp = np.array(voice.sp.data, dtype=np.float64, copy=True)
        ap = np.array(voice.ap.data, dtype=np.float64, copy=True)

        y = pw.synthesize(f0, sp, ap, fs, frame_period=fp)

        # Normalization guard against clipping > 1.0
        peak = float(np.max(np.abs(y)))
        if peak > 1.0:
            y = y / peak * 0.99

        c_samples = np.ascontiguousarray(y, dtype=np.float64)
        return AudioSignal(samples=c_samples, sample_rate=voice.sample_rate)
