"""Use cases for multi-stem MIDI transcription (bass, drums, harmonic) (ADR-003 D1)."""

from dataclasses import dataclass
from pathlib import Path

import librosa
import numpy as np
import pretty_midi
from scipy import signal as sp_signal

from mus.music_transcription.application.ports import AudioWriterPort
from mus.shared_kernel.audio import AudioSignal
from mus.shared_kernel.metrics import SongMetrics
from mus.shared_kernel.units import SampleRate


def _get_note_start(note: pretty_midi.Note) -> float:
    """Returns the start timestamp of a pretty_midi Note."""
    return float(note.start)


def _init_pretty_midi(
    song_metrics: SongMetrics | None = None,
    fallback_duration: float = 0.0,
) -> pretty_midi.PrettyMIDI:
    """Initializes a PrettyMIDI instance with unified tempo, time signature, and duration marker."""
    tempo = song_metrics.tempo_bpm if song_metrics else 120.0
    pm = pretty_midi.PrettyMIDI(initial_tempo=tempo)

    num = song_metrics.time_signature_numerator if song_metrics else 4
    den = song_metrics.time_signature_denominator if song_metrics else 4
    pm.time_signature_changes.append(pretty_midi.TimeSignature(num, den, 0.0))

    duration = song_metrics.duration_seconds if song_metrics else fallback_duration
    if duration > 0.0:
        pm.text_events.append(pretty_midi.Text("END_TRACK", duration))
    return pm


class TranscribeBass:
    """Transcribes bass stem using low-register F0 pitch tracking to GM Program 33."""

    def __init__(self, fmin: float = 30.0, fmax: float = 400.0) -> None:
        self._fmin = fmin
        self._fmax = fmax

    def execute(
        self,
        audio: AudioSignal,
        output_midi_path: Path,
        song_metrics: SongMetrics | None = None,
    ) -> Path:
        """Estimates F0 contour and writes a bass MIDI file."""
        output_midi_path = Path(output_midi_path).resolve()
        output_midi_path.parent.mkdir(parents=True, exist_ok=True)

        sr = audio.sample_rate.value
        samples = audio.samples

        f0 = librosa.yin(
            samples,
            fmin=self._fmin,
            fmax=self._fmax,
            sr=sr,
            frame_length=4096,
            hop_length=512,
        )
        hop_time = 512.0 / sr

        pm = _init_pretty_midi(song_metrics, fallback_duration=audio.duration_seconds)
        bass_inst = pretty_midi.Instrument(program=33, is_drum=False, name="Bass")

        current_pitch: int | None = None
        start_time: float = 0.0

        for idx, freq in enumerate(f0):
            t = idx * hop_time
            if not np.isnan(freq) and freq > self._fmin:
                midi_note = int(np.round(librosa.hz_to_midi(freq)))
                if current_pitch is None:
                    current_pitch = midi_note
                    start_time = t
                elif midi_note != current_pitch:
                    if t - start_time >= 0.08:
                        bass_inst.notes.append(
                            pretty_midi.Note(
                                velocity=90,
                                pitch=current_pitch,
                                start=start_time,
                                end=t,
                            )
                        )
                    current_pitch = midi_note
                    start_time = t
            elif current_pitch is not None:
                if t - start_time >= 0.08:
                    bass_inst.notes.append(
                        pretty_midi.Note(
                            velocity=90,
                            pitch=current_pitch,
                            start=start_time,
                            end=t,
                        )
                    )
                current_pitch = None

        if current_pitch is not None and (len(f0) * hop_time) - start_time >= 0.08:
            bass_inst.notes.append(
                pretty_midi.Note(
                    velocity=90,
                    pitch=current_pitch,
                    start=start_time,
                    end=len(f0) * hop_time,
                )
            )

        bass_inst.notes.sort(key=_get_note_start)
        pm.instruments.append(bass_inst)
        pm.write(str(output_midi_path))
        return output_midi_path


class TranscribeDrums:
    """Transcribes drum transients across low/mid/high sub-bands to GM Channel 10."""

    def execute(
        self,
        audio: AudioSignal,
        output_midi_path: Path,
        song_metrics: SongMetrics | None = None,
    ) -> Path:
        """Detects kicks, snares and hi-hats, generating a percussion MIDI file."""
        output_midi_path = Path(output_midi_path).resolve()
        output_midi_path.parent.mkdir(parents=True, exist_ok=True)

        sr = audio.sample_rate.value
        samples = audio.samples
        nyquist = sr / 2.0

        pm = _init_pretty_midi(song_metrics, fallback_duration=audio.duration_seconds)
        drum_inst = pretty_midi.Instrument(program=0, is_drum=True, name="Drums")

        # 1. Low band for Kick Drum (Note 36)
        low_sos = sp_signal.butter(4, min(150.0 / nyquist, 0.99), btype="lowpass", output="sos")
        kick_band = sp_signal.sosfilt(low_sos, samples)
        kick_onsets = librosa.onset.onset_detect(
            y=kick_band, sr=sr, hop_length=512, backtrack=False, units="time"
        )
        for t in kick_onsets:
            drum_inst.notes.append(
                pretty_midi.Note(velocity=100, pitch=36, start=float(t), end=float(t + 0.1))
            )

        # 2. Mid band for Snare Drum (Note 38)
        mid_low = max(200.0 / nyquist, 0.01)
        mid_high = min(2000.0 / nyquist, 0.99)
        if mid_low < mid_high:
            mid_sos = sp_signal.butter(4, [mid_low, mid_high], btype="bandpass", output="sos")
            snare_band = sp_signal.sosfilt(mid_sos, samples)
            snare_onsets = librosa.onset.onset_detect(
                y=snare_band, sr=sr, hop_length=512, backtrack=False, units="time"
            )
            for t in snare_onsets:
                drum_inst.notes.append(
                    pretty_midi.Note(velocity=95, pitch=38, start=float(t), end=float(t + 0.1))
                )

        # 3. High band for Closed Hi-Hat (Note 42)
        high_sos = sp_signal.butter(4, max(3000.0 / nyquist, 0.01), btype="highpass", output="sos")
        hihat_band = sp_signal.sosfilt(high_sos, samples)
        hihat_onsets = librosa.onset.onset_detect(
            y=hihat_band, sr=sr, hop_length=512, backtrack=False, units="time"
        )
        for t in hihat_onsets:
            drum_inst.notes.append(
                pretty_midi.Note(velocity=85, pitch=42, start=float(t), end=float(t + 0.08))
            )

        drum_inst.notes.sort(key=_get_note_start)
        pm.instruments.append(drum_inst)
        pm.write(str(output_midi_path))
        return output_midi_path


class TranscribeHarmonic:
    """Transcribes harmonic stems (guitar, piano, other) using spectral peak tracking."""

    def __init__(self, fmin: float = 65.0, fmax: float = 2000.0) -> None:
        self._fmin = fmin
        self._fmax = fmax

    def execute(
        self,
        audio: AudioSignal,
        output_midi_path: Path,
        program_number: int = 0,
        name: str = "Harmonic",
        song_metrics: SongMetrics | None = None,
    ) -> Path:
        """Extracts prominent pitch peaks across frames and writes a polyphonic MIDI file."""
        output_midi_path = Path(output_midi_path).resolve()
        output_midi_path.parent.mkdir(parents=True, exist_ok=True)

        sr = audio.sample_rate.value
        samples = audio.samples
        hop_length = 512
        hop_time = hop_length / sr

        pitches, mags = librosa.piptrack(
            y=samples,
            sr=sr,
            fmin=self._fmin,
            fmax=self._fmax,
            hop_length=hop_length,
        )

        pm = _init_pretty_midi(song_metrics, fallback_duration=audio.duration_seconds)
        inst = pretty_midi.Instrument(program=program_number, is_drum=False, name=name)

        n_frames = pitches.shape[1]
        active_notes: dict[int, float] = {}
        max_mag = float(np.max(mags)) if np.any(mags > 0) else 0.0
        threshold = 0.15 * max_mag if max_mag > 0 else 1.0

        for f_idx in range(n_frames):
            t = f_idx * hop_time
            frame_mags = mags[:, f_idx]
            frame_pitches = pitches[:, f_idx]

            peak_indices = np.where((frame_mags >= threshold) & (frame_pitches > 0))[0]
            current_frame_notes: set[int] = set()

            if len(peak_indices) > 0:
                sorted_peaks = peak_indices[np.argsort(frame_mags[peak_indices])[-4:]]
                for p_idx in sorted_peaks:
                    midi_p = int(np.round(librosa.hz_to_midi(frame_pitches[p_idx])))
                    if 21 <= midi_p <= 108:
                        current_frame_notes.add(midi_p)

            for note_p in list(active_notes.keys()):
                if note_p not in current_frame_notes:
                    note_start = active_notes.pop(note_p)
                    if t - note_start >= 0.08:
                        inst.notes.append(
                            pretty_midi.Note(
                                velocity=80,
                                pitch=note_p,
                                start=note_start,
                                end=t,
                            )
                        )

            for note_p in current_frame_notes:
                if note_p not in active_notes:
                    active_notes[note_p] = t

        total_time = n_frames * hop_time
        for note_p, note_start in active_notes.items():
            if total_time - note_start >= 0.08:
                inst.notes.append(
                    pretty_midi.Note(
                        velocity=80,
                        pitch=note_p,
                        start=note_start,
                        end=total_time,
                    )
                )

        inst.notes.sort(key=_get_note_start)
        pm.instruments.append(inst)
        pm.write(str(output_midi_path))
        return output_midi_path


@dataclass(frozen=True, slots=True)
class TranscribeStemCommand:
    """Input command to transcribe a specific audio stem to MIDI."""

    stem_name: str
    audio: AudioSignal
    output_midi_path: Path
    song_metrics: SongMetrics | None = None


class TranscribeStem:
    """Dispatches transcription to the specialized stem transcriber based on stem name."""

    def __init__(
        self,
        bass_transcriber: TranscribeBass | None = None,
        drums_transcriber: TranscribeDrums | None = None,
        harmonic_transcriber: TranscribeHarmonic | None = None,
    ) -> None:
        self._bass = bass_transcriber or TranscribeBass()
        self._drums = drums_transcriber or TranscribeDrums()
        self._harmonic = harmonic_transcriber or TranscribeHarmonic()

    def execute(self, command: TranscribeStemCommand) -> Path:
        """Executes stem transcription for bass, drums, or harmonic stems."""
        stem = command.stem_name.lower().strip()
        if stem == "bass":
            return self._bass.execute(
                command.audio, command.output_midi_path, song_metrics=command.song_metrics
            )
        if stem == "drums":
            return self._drums.execute(
                command.audio, command.output_midi_path, song_metrics=command.song_metrics
            )
        if stem == "guitar":
            return self._harmonic.execute(
                command.audio,
                command.output_midi_path,
                program_number=25,
                name="Guitar",
                song_metrics=command.song_metrics,
            )
        if stem == "piano":
            return self._harmonic.execute(
                command.audio,
                command.output_midi_path,
                program_number=0,
                name="Piano",
                song_metrics=command.song_metrics,
            )
        # Fallback for "other" or unmapped stem types
        stem_title = stem.capitalize() if stem else "Other"
        return self._harmonic.execute(
            command.audio,
            command.output_midi_path,
            program_number=48,
            name=stem_title,
            song_metrics=command.song_metrics,
        )


@dataclass(frozen=True, slots=True)
class SynthesizeStemMidiCommand:
    """Input command to render a MIDI file into an acoustic audio file."""

    midi_path: Path
    output_path: Path
    sample_rate: SampleRate


def _synthesize_drum_instrument(drum_inst: pretty_midi.Instrument, fs: int) -> np.ndarray:
    """Synthesizes drum transients into percussive acoustic waveforms."""
    end_time = drum_inst.get_end_time()
    if end_time <= 0 or not drum_inst.notes:
        return np.zeros(0, dtype=np.float64)

    total_samples = int(fs * (end_time + 1.0))
    audio = np.zeros(total_samples, dtype=np.float64)
    rng = np.random.RandomState(42)

    for note in drum_inst.notes:
        start_sample = int(note.start * fs)
        dur = max(note.end - note.start, 0.05)
        n_samples = int(dur * fs)
        if start_sample >= total_samples:
            continue
        actual_len = min(n_samples, total_samples - start_sample)
        if actual_len <= 0:
            continue

        t = np.linspace(0, actual_len / fs, actual_len, endpoint=False)
        vel = note.velocity / 127.0

        if note.pitch == 36:  # Bass / Kick Drum (decaying low frequency sweep)
            env = np.exp(-t * 25.0)
            freq = 45.0 + 75.0 * np.exp(-t * 40.0)
            phase = 2 * np.pi * np.cumsum(freq) / fs
            hit = np.sin(phase) * env * vel
        elif note.pitch == 38:  # Snare Drum (mid tone + white noise burst)
            env = np.exp(-t * 22.0)
            noise = rng.uniform(-1.0, 1.0, actual_len)
            tone = np.sin(2 * np.pi * 180.0 * t)
            hit = (0.65 * noise + 0.35 * tone) * env * vel
        elif note.pitch == 42:  # Closed Hi-Hat (crisp metallic noise transient)
            env = np.exp(-t * 55.0)
            noise = rng.uniform(-1.0, 1.0, actual_len)
            hit = noise * env * vel * 0.6
        else:  # Generic percussive transient
            env = np.exp(-t * 35.0)
            noise = rng.uniform(-1.0, 1.0, actual_len)
            tone = np.sin(2 * np.pi * 250.0 * t)
            hit = (0.5 * noise + 0.5 * tone) * env * vel

        audio[start_sample : start_sample + actual_len] += hit

    return audio


class SynthesizeStemMidi:
    """Renders a MIDI file to an acoustic audio file using PrettyMIDI synthesis and AudioWriter."""

    def __init__(self, writer: AudioWriterPort | None = None) -> None:
        if writer is None:
            from mus.voice_modeling.infrastructure.soundfile_audio_io import (  # noqa: PLC0415
                SoundfileAudioIO,
            )

            self._writer: AudioWriterPort = SoundfileAudioIO()
        else:
            self._writer = writer

    def execute(self, command: SynthesizeStemMidiCommand) -> Path:
        """Synthesizes MIDI file and writes it to command.output_path."""
        midi_path = Path(command.midi_path).resolve()
        if not midi_path.exists():
            raise FileNotFoundError(f"MIDI file not found at: {midi_path}")

        pm = pretty_midi.PrettyMIDI(str(midi_path))
        fs = command.sample_rate.value

        waveforms: list[np.ndarray] = []
        for inst in pm.instruments:
            w = _synthesize_drum_instrument(inst, fs) if inst.is_drum else inst.synthesize(fs=fs)
            if len(w) > 0:
                waveforms.append(w)

        if waveforms:
            max_len = max(len(w) for w in waveforms)
            synth_samples = np.zeros(max_len, dtype=np.float64)
            for w in waveforms:
                synth_samples[: len(w)] += w
        else:
            synth_samples = np.full(fs, 1e-7, dtype=np.float64)

        synth_samples = np.nan_to_num(synth_samples, nan=0.0, posinf=0.0, neginf=0.0)
        max_val = float(np.max(np.abs(synth_samples))) if len(synth_samples) > 0 else 0.0

        if max_val > 1e-6:
            synth_samples = (synth_samples / max_val) * 0.95
        else:
            synth_samples = np.full(fs, 1e-7, dtype=np.float64)

        c_samples = np.ascontiguousarray(synth_samples, dtype=np.float64)
        signal = AudioSignal(samples=c_samples, sample_rate=command.sample_rate)
        self._writer.write(signal, command.output_path)
        return command.output_path
