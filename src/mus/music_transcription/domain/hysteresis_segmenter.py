"""Hysteresis segmentation algorithm for continuous pitch to discrete notes conversion."""

from dataclasses import dataclass

import numpy as np

from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.notes import NoteEvent, NoteSequence
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import MidiPitch


@dataclass(frozen=True, slots=True)
class HysteresisSegmenter:
    """Segments continuous F0 PitchContour into discrete NoteEvents using hysteresis."""

    hysteresis_cents: float = 70.0
    min_change_ms: float = 60.0
    min_note_ms: float = 80.0
    max_gap_ms: float = 50.0

    def _calculate_velocity(
        self, signal: AudioSignal | None, onset_sec: float, offset_sec: float
    ) -> int:
        """Maps note frame RMS in dBFS [-50, 0] linearly to MIDI velocity [20, 127] (S2-05)."""
        if signal is None:
            return 100
        start_samp = max(0, round(onset_sec * signal.sample_rate.value))
        end_samp = min(len(signal.samples), round(offset_sec * signal.sample_rate.value))
        if end_samp <= start_samp:
            return 100
        segment = signal.samples[start_samp:end_samp]
        rms = float(np.sqrt(np.mean(segment**2)))
        if rms <= 1e-5:
            return 20
        dbfs = float(20.0 * np.log10(rms))
        clipped_db = float(np.clip(dbfs, -50.0, 0.0))
        norm = (clipped_db - (-50.0)) / (0.0 - (-50.0))
        return round(20.0 + norm * (127.0 - 20.0))

    def _extract_pitch_bends(
        self, contour: PitchContour, note_pitch: int, start_f: int, end_f: int
    ) -> tuple[int, ...]:
        """Extracts continuous residual pitch deviations into 10 ms pitch wheel events (S2-06)."""
        fp_sec = contour.frame_period.ms / 1000.0
        onset_sec = start_f * fp_sec
        offset_sec = end_f * fp_sec
        step_sec = 0.01  # 10 ms resolution
        times = np.arange(onset_sec, offset_sec, step_sec)
        if len(times) == 0:
            return ()
        midi = contour.to_midi()
        bends: list[int] = []
        for t in times:
            f_idx = round(t / fp_sec)
            if 0 <= f_idx < len(midi) and not np.isnan(midi[f_idx]):
                diff_semitones = float(midi[f_idx] - note_pitch)
                delta_cents = diff_semitones * 100.0
                norm = float(np.clip(delta_cents / 200.0, -1.0, 1.0))
                val = round(norm * 8192.0)
                bends.append(max(-8192, min(8191, val)))
            else:
                bends.append(0)
        return tuple(bends)

    def _bridge_unvoiced_gaps(self, midi: np.ndarray, frame_period_ms: float) -> np.ndarray:
        """Interpolates short unvoiced gaps below max_gap_ms."""
        bridged = midi.copy()
        n_frames = len(bridged)
        gap_frames_threshold = int(self.max_gap_ms / frame_period_ms)

        unvoiced_indices = np.where(np.isnan(bridged))[0]
        if len(unvoiced_indices) == 0:
            return bridged

        diffs = np.diff(unvoiced_indices)
        splits = np.where(diffs > 1)[0]
        gap_groups = np.split(unvoiced_indices, splits + 1)
        for grp in gap_groups:
            if len(grp) > gap_frames_threshold:
                continue
            left_idx = grp[0] - 1
            right_idx = grp[-1] + 1
            if left_idx >= 0 and right_idx < n_frames:
                left_val = bridged[left_idx]
                right_val = bridged[right_idx]
                if not np.isnan(left_val) and not np.isnan(right_val):
                    bridged[grp] = 0.5 * (left_val + right_val)

        return bridged

    def _track_raw_notes(
        self,
        bridged_midi: np.ndarray,
        frame_period_ms: float,
    ) -> list[tuple[int, int, float]]:
        """Tracks raw pitch segments using hysteresis thresholds."""
        n_frames = len(bridged_midi)
        min_change_frames = max(1, int(self.min_change_ms / frame_period_ms))
        raw_notes: list[tuple[int, int, float]] = []

        curr_start: int | None = None
        curr_pitches: list[float] = []
        candidate_count = 0

        for i, pitch in enumerate(bridged_midi):
            if np.isnan(pitch):
                if curr_start is not None and curr_pitches:
                    raw_notes.append((curr_start, i, float(np.median(curr_pitches))))
                    curr_start = None
                    curr_pitches = []
                    candidate_count = 0
                continue

            if curr_start is None:
                curr_start = i
                curr_pitches = [pitch]
                candidate_count = 0
                continue

            running_center = float(np.median(curr_pitches))
            deviation_cents = abs(pitch - running_center) * 100.0

            if deviation_cents > self.hysteresis_cents:
                candidate_count += 1
                if candidate_count >= min_change_frames:
                    split_idx = i - candidate_count + 1
                    raw_notes.append((curr_start, split_idx, running_center))
                    curr_start = split_idx
                    curr_pitches = [bridged_midi[p] for p in range(split_idx, i + 1)]
                    candidate_count = 0
            else:
                candidate_count = 0
                curr_pitches.append(pitch)

        if curr_start is not None and curr_pitches:
            raw_notes.append((curr_start, n_frames, float(np.median(curr_pitches))))

        return raw_notes

    def segment(  # noqa: PLR0917
        self,
        contour: PitchContour,
        tempo_bpm: float = 120.0,
        signal: AudioSignal | None = None,
        extract_pitch_bends: bool = False,
        quantize: bool = False,
        grid_division: int = 16,
    ) -> NoteSequence:
        """Converts PitchContour into NoteSequence with velocity/quantization."""
        midi = contour.to_midi()
        fp_sec = contour.frame_period.ms / 1000.0
        n_frames = len(midi)

        if n_frames == 0 or np.all(np.isnan(midi)):
            return NoteSequence(notes=[], tempo_bpm=tempo_bpm)

        bridged_midi = self._bridge_unvoiced_gaps(midi, contour.frame_period.ms)
        raw_notes = self._track_raw_notes(bridged_midi, contour.frame_period.ms)

        min_note_frames = int(self.min_note_ms / contour.frame_period.ms)
        notes: list[NoteEvent] = []

        for start_f, end_f, med_pitch in raw_notes:
            if (end_f - start_f) >= min_note_frames:
                rounded_midi = round(med_pitch)
                onset_sec = start_f * fp_sec
                offset_sec = end_f * fp_sec
                vel = self._calculate_velocity(signal, onset_sec, offset_sec)
                bends = (
                    self._extract_pitch_bends(contour, rounded_midi, start_f, end_f)
                    if extract_pitch_bends
                    else ()
                )
                notes.append(
                    NoteEvent(
                        pitch=MidiPitch(rounded_midi),
                        onset_seconds=onset_sec,
                        offset_seconds=offset_sec,
                        velocity=vel,
                        pitch_bends=bends,
                    )
                )

        if quantize and notes:
            grid_step = 60.0 / (tempo_bpm * (grid_division / 4.0))
            quantized_notes: list[NoteEvent] = []
            last_offset = 0.0
            for n in notes:
                snapped_onset = round(n.onset_seconds / grid_step) * grid_step
                snapped_onset = max(snapped_onset, last_offset)
                snapped_offset = max(
                    snapped_onset + grid_step,
                    round(n.offset_seconds / grid_step) * grid_step,
                )
                quantized_notes.append(
                    NoteEvent(
                        pitch=n.pitch,
                        onset_seconds=snapped_onset,
                        offset_seconds=snapped_offset,
                        velocity=n.velocity,
                        pitch_bends=n.pitch_bends,
                    )
                )
                last_offset = snapped_offset
            notes = quantized_notes

        return NoteSequence(notes=notes, tempo_bpm=tempo_bpm)
