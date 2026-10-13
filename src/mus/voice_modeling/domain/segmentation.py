"""Audio segmentation on silence to enforce bounded memory usage (ADR-001 D5)."""

from dataclasses import dataclass

import numpy as np

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.units import SampleRate


@dataclass(frozen=True, slots=True)
class AnalysisSegment:
    """Sample slice boundary for an independent analysis segment."""

    start_sample: int
    end_sample: int

    @property
    def num_samples(self) -> int:
        """Returns the number of samples in the segment."""
        return self.end_sample - self.start_sample


def split_on_silence(
    signal: AudioSignal,
    silence_dbfs: float = -50.0,
    min_silence_seconds: float = 0.2,
    max_segment_seconds: float = 30.0,
    hop_samples: int = 512,
) -> list[AnalysisSegment]:
    """Splits an AudioSignal into AnalysisSegments delimited by silent regions."""
    samples = signal.samples
    fs = signal.sample_rate.value
    total_samples = len(samples)

    min_silence_samples = int(min_silence_seconds * fs)
    max_segment_samples = int(max_segment_seconds * fs)

    # Frame-wise RMS computation
    n_frames = total_samples // hop_samples
    if n_frames == 0:
        return [AnalysisSegment(0, total_samples)]

    trimmed = samples[: n_frames * hop_samples].reshape(n_frames, hop_samples)
    rms = np.sqrt(np.mean(trimmed**2, axis=1) + 1e-12)
    dbfs = 20.0 * np.log10(np.maximum(rms, 1e-6))
    is_silent = dbfs < silence_dbfs

    # Identify continuous silent runs
    segments: list[AnalysisSegment] = []
    seg_start = 0

    silent_run_start: int | None = None

    for i, silent in enumerate(is_silent):
        sample_idx = i * hop_samples

        if silent:
            if silent_run_start is None:
                silent_run_start = sample_idx
            run_length = sample_idx - silent_run_start
            current_seg_len = sample_idx - seg_start

            # If silence is long enough or segment hit max duration
            if run_length >= min_silence_samples or current_seg_len >= max_segment_samples:
                if silent_run_start > seg_start:
                    segments.append(AnalysisSegment(seg_start, silent_run_start))
                seg_start = sample_idx
                silent_run_start = None
        else:
            silent_run_start = None
            if (sample_idx - seg_start) >= max_segment_samples:
                segments.append(AnalysisSegment(seg_start, sample_idx))
                seg_start = sample_idx

    if seg_start < total_samples:
        segments.append(AnalysisSegment(seg_start, total_samples))

    return [s for s in segments if s.num_samples > 0]


def stitch_segments(
    signals: list[AudioSignal],
    overlap_samples: int = 128,
) -> AudioSignal:
    """Concatenates AudioSignals using raised-cosine crossfade on overlapping boundaries."""
    if not signals:
        raise ValueError("Cannot stitch an empty list of signals.")
    if len(signals) == 1:
        return signals[0]

    sr: SampleRate = signals[0].sample_rate
    output_parts: list[np.ndarray] = [signals[0].samples]

    fade_out = 0.5 * (1.0 + np.cos(np.linspace(0, np.pi, overlap_samples)))
    fade_in = 1.0 - fade_out

    for i in range(1, len(signals)):
        prev = output_parts[-1]
        curr = signals[i].samples

        if len(prev) < overlap_samples or len(curr) < overlap_samples:
            output_parts.append(curr)
            continue

        blended = prev[-overlap_samples:] * fade_out + curr[:overlap_samples] * fade_in
        output_parts[-1] = prev[:-overlap_samples]
        output_parts.append(blended)
        output_parts.append(curr[overlap_samples:])

    concatenated = np.concatenate(output_parts)
    return AudioSignal(samples=concatenated, sample_rate=sr)
