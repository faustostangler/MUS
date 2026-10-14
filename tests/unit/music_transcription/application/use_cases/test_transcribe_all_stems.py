"""Unit tests for multi-stem MIDI transcription (SPEC-003 S1)."""

from pathlib import Path

import numpy as np
import pretty_midi
import pytest

from mus.music_transcription.application.use_cases.transcribe_all_stems import (
    SynthesizeStemMidi,
    SynthesizeStemMidiCommand,
    TranscribeBass,
    TranscribeDrums,
    TranscribeHarmonic,
    TranscribeStem,
    TranscribeStemCommand,
)
from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.metrics import SongMetrics
from mus.shared_kernel.units import SampleRate


@pytest.fixture
def sample_rate() -> SampleRate:
    return SampleRate(44100)


def test_transcribe_bass_generates_midi_with_gm_33(tmp_path: Path, sample_rate: SampleRate) -> None:
    # 1.0s sine wave at 55.0 Hz (A1 bass note)
    t = np.linspace(0, 1.0, sample_rate.value, endpoint=False)
    samples = 0.8 * np.sin(2 * np.pi * 55.0 * t).astype(np.float64)
    signal = AudioSignal(samples=samples, sample_rate=sample_rate)

    out_midi = tmp_path / "test_bass.mid"
    transcriber = TranscribeBass()
    transcriber.execute(signal, out_midi)

    assert out_midi.exists()
    pm = pretty_midi.PrettyMIDI(str(out_midi))
    assert len(pm.instruments) >= 1
    assert pm.instruments[0].program == 33  # Electric Bass Finger
    assert len(pm.instruments[0].notes) > 0


def test_transcribe_drums_generates_channel_10_midi(
    tmp_path: Path, sample_rate: SampleRate
) -> None:
    # Synthetic drum pulses: low frequency pulse (kick) and high frequency noise (hihat)
    t = np.linspace(0, 1.0, sample_rate.value, endpoint=False)
    # 0.1s kick at 60 Hz
    kick = np.sin(2 * np.pi * 60.0 * t[: int(0.1 * sample_rate.value)])
    samples = np.zeros(sample_rate.value, dtype=np.float64)
    samples[: len(kick)] = kick

    signal = AudioSignal(samples=samples, sample_rate=sample_rate)
    out_midi = tmp_path / "test_drums.mid"
    transcriber = TranscribeDrums()
    transcriber.execute(signal, out_midi)

    assert out_midi.exists()
    pm = pretty_midi.PrettyMIDI(str(out_midi))
    assert len(pm.instruments) >= 1
    drum_inst = pm.instruments[0]
    assert drum_inst.is_drum is True
    assert len(drum_inst.notes) > 0
    # Kick note is 36
    assert any(note.pitch == 36 for note in drum_inst.notes)


def test_transcribe_harmonic_generates_polyphonic_midi(
    tmp_path: Path, sample_rate: SampleRate
) -> None:
    # Synthetic C4 + E4 + G4 chord
    t = np.linspace(0, 1.0, sample_rate.value, endpoint=False)
    chord = (
        0.3 * np.sin(2 * np.pi * 261.63 * t)
        + 0.3 * np.sin(2 * np.pi * 329.63 * t)
        + 0.3 * np.sin(2 * np.pi * 392.0 * t)
    ).astype(np.float64)
    signal = AudioSignal(samples=chord, sample_rate=sample_rate)

    out_midi = tmp_path / "test_piano.mid"
    transcriber = TranscribeHarmonic()
    transcriber.execute(signal, out_midi, program_number=0)

    assert out_midi.exists()
    pm = pretty_midi.PrettyMIDI(str(out_midi))
    assert len(pm.instruments) >= 1
    inst = pm.instruments[0]
    assert inst.program == 0
    assert len(inst.notes) >= 1


def test_transcribe_stem_dispatches_correctly(tmp_path: Path, sample_rate: SampleRate) -> None:
    t = np.linspace(0, 1.0, sample_rate.value, endpoint=False)
    bass_samples = 0.8 * np.sin(2 * np.pi * 55.0 * t).astype(np.float64)
    bass_sig = AudioSignal(samples=bass_samples, sample_rate=sample_rate)

    transcriber = TranscribeStem()

    # Test Bass dispatch
    bass_mid = tmp_path / "bass.mid"
    transcriber.execute(
        TranscribeStemCommand(stem_name="bass", audio=bass_sig, output_midi_path=bass_mid)
    )
    assert bass_mid.exists()
    pm_bass = pretty_midi.PrettyMIDI(str(bass_mid))
    assert pm_bass.instruments[0].program == 33

    # Test Guitar dispatch
    chord = (0.3 * np.sin(2 * np.pi * 329.63 * t)).astype(np.float64)
    guitar_sig = AudioSignal(samples=chord, sample_rate=sample_rate)
    guitar_mid = tmp_path / "guitar.mid"
    transcriber.execute(
        TranscribeStemCommand(stem_name="guitar", audio=guitar_sig, output_midi_path=guitar_mid)
    )
    assert guitar_mid.exists()
    pm_guitar = pretty_midi.PrettyMIDI(str(guitar_mid))
    assert pm_guitar.instruments[0].program == 25


def test_transcribe_stem_applies_unified_song_metrics(
    tmp_path: Path, sample_rate: SampleRate
) -> None:
    transcriber = TranscribeStem()
    t = np.linspace(0, 1.0, sample_rate.value, endpoint=False)
    sig = AudioSignal(
        samples=(0.5 * np.sin(2 * np.pi * 55.0 * t)).astype(np.float64),
        sample_rate=sample_rate,
    )

    metrics = SongMetrics(
        tempo_bpm=82.5,
        duration_seconds=240.0,
        time_signature_numerator=4,
        time_signature_denominator=4,
    )

    for stem in ["bass", "drums", "guitar"]:
        midi_file = tmp_path / f"{stem}.mid"
        transcriber.execute(
            TranscribeStemCommand(
                stem_name=stem,
                audio=sig,
                output_midi_path=midi_file,
                song_metrics=metrics,
            )
        )
        assert midi_file.exists()
        pm = pretty_midi.PrettyMIDI(str(midi_file))
        tempi = pm.get_tempo_changes()[1]
        assert pytest.approx(float(tempi[0]), abs=0.01) == 82.5
        assert len(pm.time_signature_changes) > 0
        assert pm.time_signature_changes[0].numerator == 4
        assert pm.time_signature_changes[0].denominator == 4
        assert pytest.approx(pm.get_end_time(), abs=0.01) == 240.0


def test_synthesize_stem_midi_renders_and_writes_audio(
    tmp_path: Path, sample_rate: SampleRate
) -> None:
    # Create a simple MIDI file
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=33)
    inst.notes.append(pretty_midi.Note(velocity=100, pitch=40, start=0.0, end=0.5))
    pm.instruments.append(inst)
    midi_path = tmp_path / "source.mid"
    pm.write(str(midi_path))

    out_mp3 = tmp_path / "synthesized - mid.mp3"
    synthesizer = SynthesizeStemMidi()
    result_path = synthesizer.execute(
        SynthesizeStemMidiCommand(
            midi_path=midi_path,
            output_path=out_mp3,
            sample_rate=sample_rate,
        )
    )

    assert result_path == out_mp3
    assert out_mp3.exists()
    assert out_mp3.stat().st_size > 0


def test_synthesize_stem_midi_handles_percussion_drum_channel_without_nan(
    tmp_path: Path, sample_rate: SampleRate
) -> None:
    # Regression test for AudioSignal NaN error on drum channels (is_drum=True)
    pm = pretty_midi.PrettyMIDI()
    drum_inst = pretty_midi.Instrument(program=0, is_drum=True, name="Drums")
    drum_inst.notes.append(pretty_midi.Note(velocity=100, pitch=36, start=0.0, end=0.1))
    drum_inst.notes.append(pretty_midi.Note(velocity=90, pitch=38, start=0.5, end=0.6))
    drum_inst.notes.append(pretty_midi.Note(velocity=80, pitch=42, start=1.0, end=1.1))
    pm.instruments.append(drum_inst)

    midi_path = tmp_path / "drums.mid"
    pm.write(str(midi_path))

    out_mp3 = tmp_path / "drums - mid.mp3"
    synthesizer = SynthesizeStemMidi()
    result_path = synthesizer.execute(
        SynthesizeStemMidiCommand(
            midi_path=midi_path,
            output_path=out_mp3,
            sample_rate=sample_rate,
        )
    )

    assert result_path == out_mp3
    assert out_mp3.exists()
    assert out_mp3.stat().st_size > 0


def test_synthesize_stem_midi_handles_empty_midi_without_nan(
    tmp_path: Path, sample_rate: SampleRate
) -> None:
    # Regression test for completely empty or silent MIDI
    pm = pretty_midi.PrettyMIDI()
    inst = pretty_midi.Instrument(program=0, is_drum=False, name="Empty")
    pm.instruments.append(inst)

    midi_path = tmp_path / "empty.mid"
    pm.write(str(midi_path))

    out_mp3 = tmp_path / "empty - mid.mp3"
    synthesizer = SynthesizeStemMidi()
    result_path = synthesizer.execute(
        SynthesizeStemMidiCommand(
            midi_path=midi_path,
            output_path=out_mp3,
            sample_rate=sample_rate,
        )
    )

    assert result_path == out_mp3
    assert out_mp3.exists()
    assert out_mp3.stat().st_size > 0
