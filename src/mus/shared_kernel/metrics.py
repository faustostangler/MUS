"""SongMetrics value object and estimation domain service (SPEC-005)."""

import math
from dataclasses import dataclass

import librosa
import numpy as np

from mus.shared_kernel.audio import AudioSignal


@dataclass(frozen=True, slots=True)
class SongMetrics:
    """Immutable musical metrics shared by all stems of a master song track."""

    tempo_bpm: float
    duration_seconds: float
    time_signature_numerator: int = 4
    time_signature_denominator: int = 4

    def __post_init__(self) -> None:
        if not (20.0 <= self.tempo_bpm <= 400.0):
            raise ValueError(f"Tempo {self.tempo_bpm} BPM must be between 20.0 and 400.0.")

        if not (math.isfinite(self.duration_seconds) and self.duration_seconds > 0.0):
            raise ValueError(f"Duration must be positive and finite, got {self.duration_seconds}.")

        if not (1 <= self.time_signature_numerator <= 32):
            raise ValueError(f"Invalid time signature numerator: {self.time_signature_numerator}.")

        if self.time_signature_denominator not in {1, 2, 4, 8, 16, 32}:
            raise ValueError(
                f"Invalid time signature denominator: {self.time_signature_denominator}."
            )


def estimate_song_metrics(
    signal: AudioSignal,
    preferred_bpm: float | None = None,
    time_signature_numerator: int = 4,
    time_signature_denominator: int = 4,
) -> SongMetrics:
    """Estimates or constructs global musical metrics from an audio signal."""
    tempo: float
    if preferred_bpm is not None and 20.0 <= preferred_bpm <= 400.0:
        tempo = float(preferred_bpm)
    else:
        try:
            detected_tempo, _ = librosa.beat.beat_track(
                y=signal.samples,
                sr=signal.sample_rate.value,
            )
            detected_scalar = float(np.atleast_1d(detected_tempo)[0])
            if math.isfinite(detected_scalar) and 20.0 <= detected_scalar <= 400.0:
                tempo = round(detected_scalar, 2)
            else:
                tempo = 120.0
        except Exception:
            tempo = 120.0

    try:
        duration = float(signal.duration_seconds)
    except (TypeError, ValueError):
        duration = 180.0
    if not (math.isfinite(duration) and duration > 0.0):
        duration = 180.0

    return SongMetrics(
        tempo_bpm=tempo,
        duration_seconds=duration,
        time_signature_numerator=time_signature_numerator,
        time_signature_denominator=time_signature_denominator,
    )
