from pathlib import Path

import numpy as np
import pretty_midi

from mus.music_transcription.domain.hysteresis_segmenter import HysteresisSegmenter
from mus.music_transcription.infrastructure.pretty_midi_io import PrettyMidiIO
from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.notes import NoteEvent, NoteSequence
from mus.shared_kernel.pitch import PitchContour
from mus.shared_kernel.units import FramePeriod, MidiPitch, SampleRate


def _make_contour_with_signal(
    frequencies: list[float],
    durations_s: list[float],
    amplitudes: list[float],
    sr: int = 44100,
    fp_ms: float = 5.0,
) -> tuple[PitchContour, AudioSignal]:
    """Generates synthetic F0 contour and synchronized sine AudioSignal."""
    fp_sec = fp_ms / 1000.0
    f0_list: list[float] = []
    audio_chunks: list[np.ndarray] = []

    for freq, dur, amp in zip(frequencies, durations_s, amplitudes, strict=True):
        n_frames = round(dur / fp_sec)
        f0_list.extend([freq] * n_frames)
        t = np.linspace(0, dur, round(dur * sr), endpoint=False)
        chunk = amp * np.sin(2 * np.pi * freq * t) if freq > 0 else np.zeros_like(t)
        audio_chunks.append(chunk)

    f0_arr = np.array(f0_list, dtype=np.float64)
    audio_arr = np.concatenate(audio_chunks).astype(np.float64)

    contour = PitchContour(
        f0=f0_arr,
        frame_period=FramePeriod(fp_ms),
    )
    signal = AudioSignal(samples=audio_arr, sample_rate=SampleRate(sr))
    return contour, signal


class TestTranscriptionRefinements:
    """Verifies S2-05, S2-06, and S2-07 specifications."""

    def test_s2_05_dynamic_velocity_from_rms(self) -> None:
        """S2-05: Louder signal segment (+6 dB or more) produces strictly higher MIDI velocity."""
        # Note 1: 440 Hz at amplitude 0.1 (-20 dBFS approx)
        # Note 2: 523.25 Hz at amplitude 0.8 (-2 dBFS approx)
        contour, signal = _make_contour_with_signal(
            frequencies=[440.0, 523.251],
            durations_s=[0.4, 0.4],
            amplitudes=[0.05, 0.8],
        )

        segmenter = HysteresisSegmenter()
        seq = segmenter.segment(contour, tempo_bpm=120.0, signal=signal)

        assert len(seq.notes) == 2
        quiet_note, loud_note = seq.notes[0], seq.notes[1]
        assert loud_note.velocity > quiet_note.velocity
        assert 20 <= quiet_note.velocity <= 127
        assert 20 <= loud_note.velocity <= 127

    def test_s2_06_residual_pitch_bend_extraction(self) -> None:
        """S2-06: Vibrato/pitch deviations within note extract into pitch bends at 10 ms steps."""
        # 440 Hz (MIDI 69) with ±40 cents sinusoidal vibrato at 5 Hz for 0.5s
        fp_ms = 5.0
        fp_sec = fp_ms / 1000.0
        dur = 0.5
        n_frames = round(dur / fp_sec)
        t = np.arange(n_frames) * fp_sec

        # 40 cents is factor of 2^(40/1200) ≈ 1.02337
        f0 = 440.0 * (2.0 ** (40.0 * np.sin(2 * np.pi * 5.0 * t) / 1200.0))
        contour = PitchContour(
            f0=f0,
            frame_period=FramePeriod(fp_ms),
        )

        segmenter = HysteresisSegmenter()
        # With extract_pitch_bends=True
        seq = segmenter.segment(contour, tempo_bpm=120.0, extract_pitch_bends=True)

        assert len(seq.notes) == 1
        note = seq.notes[0]
        assert len(note.pitch_bends) > 0
        # Vibrato should produce non-zero pitch bends with both positive and negative values
        assert any(b > 0 for b in note.pitch_bends)
        assert any(b < 0 for b in note.pitch_bends)
        assert all(-8192 <= b <= 8191 for b in note.pitch_bends)

    def test_s2_07_tempo_grid_quantization(self) -> None:
        """S2-07: With quantize=True at 120 BPM, onsets snap to 1/16 grid multiples (125 ms)."""
        # Note onsets slightly off grid: e.g. at 0.118s (should snap to 0.125s)
        contour, _ = _make_contour_with_signal(
            frequencies=[0.0, 440.0, 0.0, 523.251],
            durations_s=[0.118, 0.38, 0.13, 0.35],
            amplitudes=[0.0, 0.5, 0.0, 0.5],
        )

        segmenter = HysteresisSegmenter()
        seq = segmenter.segment(contour, tempo_bpm=120.0, quantize=True, grid_division=16)

        grid_step = 60.0 / (120.0 * (16 / 4))  # 0.125 s
        for note in seq.notes:
            # Onset should be very close to a grid multiple
            remainder = note.onset_seconds % grid_step
            assert remainder < 1e-4 or abs(remainder - grid_step) < 1e-4
            assert note.duration_seconds >= grid_step - 1e-4

        # Verify monophonic invariant holds
        for i in range(len(seq.notes) - 1):
            assert seq.notes[i].offset_seconds <= seq.notes[i + 1].onset_seconds

    def test_pretty_midi_writes_pitch_bends(self, tmp_path: Path) -> None:
        """Verifies PrettyMidiIO writes pitch bend events into the MIDI track."""
        midi_file = tmp_path / "test_pitch_bends.mid"
        bends = (0, 1024, 2048, 1024, 0, -1024, -2048, -1024, 0)
        note = NoteEvent(
            pitch=MidiPitch(69),
            onset_seconds=0.0,
            offset_seconds=0.5,
            velocity=100,
            pitch_bends=bends,
        )
        seq = NoteSequence(notes=[note], tempo_bpm=120.0)

        io = PrettyMidiIO()
        io.write(seq, midi_file)

        # Read back with pretty_midi directly to inspect raw pitch bends
        pm = pretty_midi.PrettyMIDI(str(midi_file))
        assert len(pm.instruments) == 1
        inst = pm.instruments[0]
        assert len(inst.pitch_bends) == len(bends)
        for expected_val, pb in zip(bends, inst.pitch_bends, strict=True):
            assert pb.pitch == expected_val
