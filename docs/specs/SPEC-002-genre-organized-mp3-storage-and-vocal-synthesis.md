# SPEC-002: Genre-Organized MP3 Storage and Vocal Resynthesis Specification

**Linked ADR:** [ADR-002](../adr/ADR-002-genre-organized-mp3-storage-and-vocal-synthesis.md)

## Acceptance Criteria

### S1: SoundfileAudioIO MP3 Encoding
- **S1-01:** When `SoundfileAudioIO.write()` is called with a path ending in `.mp3`, the file is encoded and saved as an MP3 file (MPEG audio format).
- **S1-02:** When `SoundfileAudioIO.read()` is called on an MP3 file, it successfully loads the audio as an `AudioSignal` with contiguous `float64` samples.
- **S1-03:** When `SoundfileAudioIO.write()` is called with a path ending in `.wav`, it preserves backward compatibility by writing a 24-bit PCM WAV.

### S2: Genre-Partitioned Stem Ingestion
- **S2-01:** `IngestAndSeparateTrack.execute()` writes downloaded tracks and separated stems into `{output_dir}/{genre}/` where `{genre}` is derived from the track metadata.
- **S2-02:** If the track metadata genre contains illegal filename characters (e.g., `/`, `\`, `:`), it is sanitized to safe characters.
- **S2-03:** If genre is empty or whitespace, it defaults to `"Unknown"`.

### S3: Unified Pipeline Output Co-location & Formatting
- **S3-01:** `pipeline run` produces the synthesized vocal take at `{vocal_stem_parent}/{track_stem} - vocals - synt.mp3`.
- **S3-02:** `pipeline run` writes `{vocal_stem_parent}/{track_stem} - vocals.mid` directly into the same genre stem directory.
- **S3-03:** `pipeline run` does NOT write any `_midi_preview.wav` file.
