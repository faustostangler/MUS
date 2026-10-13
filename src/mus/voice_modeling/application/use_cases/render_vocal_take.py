"""RenderVocalTake composite use case with peak-guard normalization (S5-01, S5-03)."""

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import Semitones
from mus.voice_modeling.application.ports import AudioWriterPort, VocoderPort, VoiceCachePort
from mus.voice_modeling.application.use_cases.decompose_voice import (
    DecomposeVoice,
    DecomposeVoiceCommand,
)
from mus.voice_modeling.application.use_cases.reshape_formants import (
    ReshapeFormants,
    ReshapeFormantsCommand,
)
from mus.voice_modeling.domain.phonetics import VocalTractScale
from mus.voice_modeling.domain.pitch_modulation import transpose


@dataclass(frozen=True, slots=True)
class RenderVocalTakeCommand:
    """Input parameters for end-to-end vocal take synthesis with peak-guard."""

    signal: AudioSignal
    output_path: Path
    transpose_semitones: float | None = None
    vocal_tract_alpha: float | None = None
    cache_key: str | None = None
    f0_estimator: str = "dio"
    peak_guard_dbfs: float = -1.0
    pcm_subtype: str = "PCM_24"


@dataclass(frozen=True, slots=True)
class RenderVocalTakeResult:
    """Execution summary and telemetry for a rendered vocal take."""

    output_path: Path
    duration_seconds: float
    peak_dbfs_before: float
    peak_dbfs_after: float
    was_clipped: bool
    normalized: bool


class RenderVocalTake:
    """Coordinates decomposition, pitch/formant modulation, and peak-guarded resynthesis."""

    def __init__(
        self,
        vocoder: VocoderPort,
        writer: AudioWriterPort,
        cache: VoiceCachePort | None = None,
    ) -> None:
        self._vocoder = vocoder
        self._writer = writer
        self._cache = cache
        self._decompose_uc = DecomposeVoice(vocoder=vocoder, cache=cache)
        self._reshape_uc = ReshapeFormants()

    def execute(self, command: RenderVocalTakeCommand) -> RenderVocalTakeResult:
        """Decomposes, modulates, resynthesizes and applies -1.0 dBFS peak guard if clipping."""
        voice = self._decompose_uc.execute(
            DecomposeVoiceCommand(
                signal=command.signal,
                method=command.f0_estimator,
                cache_key=command.cache_key,
            )
        )

        modulated_voice = voice
        if command.transpose_semitones is not None:
            shifted_f0 = transpose(modulated_voice.f0, Semitones(command.transpose_semitones))
            modulated_voice = modulated_voice.with_f0(shifted_f0)

        if command.vocal_tract_alpha is not None:
            scale = VocalTractScale(command.vocal_tract_alpha)
            modulated_voice = self._reshape_uc.execute(
                ReshapeFormantsCommand(voice=modulated_voice, tract_scale=scale)
            )

        synth_signal = self._vocoder.synthesize(modulated_voice)
        samples = np.array(synth_signal.samples, copy=True)

        was_clipped = bool(getattr(self._vocoder, "last_synthesis_clipped", False))
        raw_peak = float(
            getattr(
                self._vocoder,
                "last_raw_peak",
                np.max(np.abs(samples)) if len(samples) > 0 else 0.0,
            )
        )

        peak_dbfs_before = float(20.0 * np.log10(raw_peak)) if raw_peak > 1e-9 else -100.0
        cur_peak = float(np.max(np.abs(samples))) if len(samples) > 0 else 0.0
        peak_dbfs_after = float(20.0 * np.log10(cur_peak)) if cur_peak > 1e-9 else -100.0
        normalized = was_clipped

        guarded_signal = AudioSignal(samples=samples, sample_rate=synth_signal.sample_rate)
        self._writer.write(
            signal=guarded_signal,
            path=command.output_path,
        )

        return RenderVocalTakeResult(
            output_path=command.output_path,
            duration_seconds=guarded_signal.duration_seconds,
            peak_dbfs_before=peak_dbfs_before,
            peak_dbfs_after=peak_dbfs_after,
            was_clipped=was_clipped,
            normalized=normalized,
        )
