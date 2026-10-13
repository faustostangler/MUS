"""PrettyMIDI adapter for MIDI I/O export."""

from pathlib import Path

import pretty_midi

from mus.music_transcription.application.ports import MidiReaderPort, MidiWriterPort
from mus.shared_kernel.notes import NoteEvent, NoteSequence
from mus.shared_kernel.units import MidiPitch


class PrettyMidiIO(MidiWriterPort, MidiReaderPort):
    """Reads and writes NoteSequence as MIDI Type 1 files using pretty_midi."""

    def write(
        self,
        sequence: NoteSequence,
        output_path: Path,
        program_number: int = 52,  # Default Choir Aahs (GM 52) per MT-02
    ) -> None:
        """Exports a NoteSequence to a Standard MIDI file."""
        output_path = Path(output_path).resolve()
        output_path.parent.mkdir(parents=True, exist_ok=True)

        midi = pretty_midi.PrettyMIDI(initial_tempo=sequence.tempo_bpm)
        instrument = pretty_midi.Instrument(program=program_number)

        for n in sequence.notes:
            pm_note = pretty_midi.Note(
                velocity=n.velocity,
                pitch=n.pitch.value,
                start=n.onset_seconds,
                end=n.offset_seconds,
            )
            instrument.notes.append(pm_note)

            for step_idx, bend in enumerate(n.pitch_bends):
                bend_time = n.onset_seconds + step_idx * 0.01
                instrument.pitch_bends.append(pretty_midi.PitchBend(pitch=bend, time=bend_time))

        midi.instruments.append(instrument)
        midi.write(str(output_path))

    def read(self, midi_path: Path) -> NoteSequence:
        """Reads a MIDI file and extracts the monophonic sequence."""
        midi_path = Path(midi_path).resolve()
        midi = pretty_midi.PrettyMIDI(str(midi_path))

        tempo_changes = midi.get_tempo_changes()
        tempo = float(tempo_changes[1][0]) if len(tempo_changes[1]) > 0 else 120.0
        notes: list[NoteEvent] = []

        if midi.instruments:
            inst = midi.instruments[0]
            for n in inst.notes:
                notes.append(
                    NoteEvent(
                        pitch=MidiPitch(n.pitch),
                        onset_seconds=float(n.start),
                        offset_seconds=float(n.end),
                        velocity=int(n.velocity),
                    )
                )

        return NoteSequence(notes=notes, tempo_bpm=tempo)
