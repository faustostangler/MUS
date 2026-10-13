"""Unit tests for SingVocalise singing synthesis (Route 4B)."""

import numpy as np

from mus.shared_kernel.notes import NoteEvent, NoteSequence
from mus.shared_kernel.units import MidiPitch, SampleRate
from mus.voice_modeling.application.use_cases.sing_vocalise import (
    SingVocalise,
    SingVocaliseCommand,
)
from mus.voice_modeling.domain.phonetics import estimate_formants_lpc


def test_sing_vocalise_generates_parametric_voice_with_portamento_and_vibrato() -> None:
    # 3-note sequence: C4 (60), D4 (62), E4 (64) each 0.6s
    notes = [
        NoteEvent(pitch=MidiPitch(60), onset_seconds=0.0, offset_seconds=0.6),
        NoteEvent(pitch=MidiPitch(62), onset_seconds=0.6, offset_seconds=1.2),
        NoteEvent(pitch=MidiPitch(64), onset_seconds=1.2, offset_seconds=1.8),
    ]
    seq = NoteSequence(notes=notes, tempo_bpm=120.0)

    use_case = SingVocalise()
    cmd = SingVocaliseCommand(
        sequence=seq,
        vowels=["a", "i", "u"],
        portamento_ms=40.0,
        vibrato_hz=5.5,
        vibrato_cents=30.0,
        vibrato_onset_delay_ms=200.0,
    )

    voice = use_case.execute(cmd)

    assert len(voice.f0) > 0
    assert voice.sp.data.shape[0] == len(voice.f0)
    assert voice.ap.data.shape[0] == len(voice.f0)

    # Check steady-state F0 of first note (C4 ~ 261.63 Hz)
    # around 0.1s (after portamento, before vibrato onset at 0.2s)
    fp_ms = 5.0
    frame_100ms = int(100.0 / fp_ms)
    expected_c4 = 440.0 * (2.0 ** ((60 - 69) / 12.0))
    actual_f0 = voice.f0.f0[frame_100ms]
    assert abs(actual_f0 - expected_c4) < 1.0

    # S4B-02 Expressiveness: Vibrato present after delay (0.3s - 0.5s)
    # Pitch should oscillate
    vibrato_frames = voice.f0.f0[int(300 / fp_ms) : int(500 / fp_ms)]
    cents_dev = 1200.0 * np.log2(vibrato_frames / expected_c4)
    assert np.max(cents_dev) > 15.0
    assert np.min(cents_dev) < -15.0

    # S4B-01 LPC Formant match on first note (/a/) around 100ms
    f1, f2 = estimate_formants_lpc(
        sp_frame=voice.sp.data[frame_100ms],
        sample_rate=SampleRate(44100),
        order=16,
    )
    # Target /a/: (730, 1090) within 15%
    assert abs(f1 - 730.0) / 730.0 < 0.15
    assert abs(f2 - 1090.0) / 1090.0 < 0.15
