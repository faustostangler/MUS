"""SingVocalise use case for synthetic vocalise singing synthesis (Route 4B)."""

import math
from dataclasses import dataclass, field

import numpy as np

from mus.shared_kernel.notes import NoteSequence
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, SampleRate
from mus.voice_modeling.domain.parametric_voice import (
    Aperiodicity,
    ParametricVoice,
    SpectralEnvelope,
)
from mus.voice_modeling.domain.phonetics import (
    IPA_VOWEL_TABLE,
    generate_allpole_envelope,
)


@dataclass(frozen=True, slots=True)
class SingVocaliseCommand:
    """Input parameters for singing synthesis generation."""

    sequence: NoteSequence
    vowels: list[str] | str | None = None
    portamento_ms: float = 40.0
    vibrato_hz: float = 5.5
    vibrato_cents: float = 30.0
    vibrato_onset_delay_ms: float = 200.0
    frame_period: FramePeriod = field(default_factory=lambda: FramePeriod(5.0))
    sample_rate: SampleRate = field(default_factory=lambda: SampleRate(44100))


class SingVocalise:
    """Constructs a synthetic ParametricVoice aggregate from a symbolic NoteSequence."""

    def execute(self, command: SingVocaliseCommand) -> ParametricVoice:
        """Builds ParametricVoice with pitch contours, formants, and aperiodicities."""
        seq = command.sequence
        if not seq.notes:
            # Empty take fallback
            empty_f0 = np.array([0.0], dtype=np.float64)
            empty_sp = np.full((1, 1025), 1e-6, dtype=np.float64)
            empty_ap = np.ones((1, 1025), dtype=np.float64)
            return ParametricVoice(
                f0=PitchContour(f0=empty_f0, frame_period=command.frame_period),
                sp=SpectralEnvelope(data=empty_sp),
                ap=Aperiodicity(data=empty_ap),
                sample_rate=command.sample_rate,
            )

        fp_ms = command.frame_period.ms
        fp_sec = fp_ms / 1000.0
        sr = command.sample_rate.value
        fft_size = 2048
        n_bins = fft_size // 2 + 1

        total_duration = max(n.offset_seconds for n in seq.notes) + 0.1
        n_frames = math.ceil(total_duration / fp_sec) + 1

        f0 = np.zeros(n_frames, dtype=np.float64)
        sp = np.full((n_frames, n_bins), 1e-6, dtype=np.float64)
        ap = np.ones((n_frames, n_bins), dtype=np.float64)

        # Baseline aperiodicity curve for voiced frames (clean voice)
        base_ap = np.clip(np.linspace(0.02, 0.5, n_bins), 0.0, 1.0)

        # Parse vowels list
        vowels_list: list[str] = []
        if isinstance(command.vowels, str):
            vowels_list = list(command.vowels)
        elif isinstance(command.vowels, list):
            vowels_list = command.vowels
        if not vowels_list:
            vowels_list = ["a"]

        prev_note_freq: float | None = None
        portamento_sec = command.portamento_ms / 1000.0
        vibrato_delay_sec = command.vibrato_onset_delay_ms / 1000.0

        for idx, note in enumerate(seq.notes):
            vowel_char = vowels_list[idx % len(vowels_list)]
            formant_target = IPA_VOWEL_TABLE.get(vowel_char, IPA_VOWEL_TABLE["a"])

            note_envelope = generate_allpole_envelope(
                formants=[formant_target.f1, formant_target.f2, formant_target.f3],
                sample_rate=sr,
                fft_size=fft_size,
            )
            # Scale envelope amplitude
            note_envelope *= 1e-3

            target_freq = 440.0 * (2.0 ** ((note.pitch.value - 69.0) / 12.0))
            start_f = round(note.onset_seconds / fp_sec)
            end_f = round(note.offset_seconds / fp_sec)

            for f_idx in range(start_f, min(end_f, n_frames)):
                t = f_idx * fp_sec
                rel_t = t - note.onset_seconds

                # Base frequency with portamento
                if prev_note_freq is not None and rel_t < portamento_sec and portamento_sec > 0:
                    ramp_alpha = 0.5 * (1.0 - math.cos(math.pi * (rel_t / portamento_sec)))
                    curr_f0 = prev_note_freq + ramp_alpha * (target_freq - prev_note_freq)
                else:
                    curr_f0 = target_freq

                # Vibrato modulation
                if rel_t >= vibrato_delay_sec:
                    vib_time = rel_t - vibrato_delay_sec
                    mod_cents = command.vibrato_cents * math.sin(
                        2.0 * math.pi * command.vibrato_hz * vib_time
                    )
                    curr_f0 *= 2.0 ** (mod_cents / 1200.0)

                f0[f_idx] = curr_f0
                sp[f_idx] = note_envelope
                ap[f_idx] = base_ap

            prev_note_freq = target_freq

        return ParametricVoice(
            f0=PitchContour(f0=f0, frame_period=command.frame_period),
            sp=SpectralEnvelope(data=sp),
            ap=Aperiodicity(data=ap),
            sample_rate=command.sample_rate,
        )
