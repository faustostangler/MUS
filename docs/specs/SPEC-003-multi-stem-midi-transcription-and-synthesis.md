# SPEC-003: Multi-Stem MIDI Transcription and Synthesis Specification

**Linked ADR:** [ADR-003](../adr/ADR-003-multi-stem-midi-transcription-and-synthesis.md)

## Acceptance Criteria

### S1: Stem Transcriptions
- **S1-01 (Bass):** `TranscribeBass` converts a bass audio signal into a MIDI file with GM Program 33 (Electric Bass Finger).
- **S1-02 (Drums):** `TranscribeDrums` detects transients across low, mid, and high frequency bands and outputs a MIDI percussion track on Channel 10 (`is_drum=True`) containing Kick (36), Snare (38), and Hi-hat (42).
- **S1-03 (Harmonic Stems):** `TranscribeHarmonic` extracts multi-peak notes for guitar (GM 25), piano (GM 0), and other (GM 48) and writes a valid `.mid` file.

### S2: Acoustic MP3 Resynthesis
- **S2-01:** Every non-vocal transcribed MIDI file (`bass.mid`, `drums.mid`, `guitar.mid`, `piano.mid`, `other.mid`) is rendered to an acoustic audio signal and persisted as 320 kbps MP3 named `{track_stem} - {stem} - synt.mp3`.
- **S2-02:** Vocals continue to be resynthesized via WORLD vocoder as `{track_stem} - vocals - synt.mp3`.

### S3: Full Pipeline Execution and Idempotency
- **S3-01:** `pipeline run` processes each available stem, creating `{stem}.mid` and `{stem} - synt.mp3` in the track's genre folder.
- **S3-02:** `is_track_fully_processed()` returns `True` only when all available stems have their corresponding `.mid` and `- synt.mp3` files present on disk.
