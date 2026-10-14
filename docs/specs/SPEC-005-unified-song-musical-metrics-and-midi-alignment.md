# SPEC-005: Unified Song Musical Metrics and Multi-Stem MIDI Alignment Specification

**Linked ADR:** [ADR-005](../adr/ADR-005-unified-song-musical-metrics-and-midi-alignment.md)

## Acceptance Criteria

### S1: Value Object & Estimation Service (`SongMetrics`)
- **S1-01:** `SongMetrics` is an immutable Value Object containing `tempo_bpm: float`, `duration_seconds: float`, `time_signature_numerator: int`, `time_signature_denominator: int`.
- **S1-02:** `estimate_song_metrics(signal: AudioSignal, preferred_bpm: float | None = None)` estimates tempo using `librosa.beat.beat_track` when `preferred_bpm` is not specified, falling back to 120.0 BPM only if detection fails.
- **S1-03:** `duration_seconds` exactly reflects the length of the audio signal (`len(samples) / sample_rate`).
- **S1-04:** Time signature defaults to 4/4 meter.

### S2: MIDI Meta-Events & Temporal Alignment across All Stems
- **S2-01 (Tempo Meta-Event):** Every stem `.mid` file (`vocals.mid`, `bass.mid`, `drums.mid`, `guitar.mid`, `piano.mid`, `other.mid`) must contain the exact same `initial_tempo` matching `SongMetrics.tempo_bpm`.
- **S2-02 (Time Signature Meta-Event):** Every stem `.mid` file must contain a `pretty_midi.TimeSignature` matching `SongMetrics` numerator and denominator at time `0.0`.
- **S2-03 (Total Duration Alignment):** Every stem `.mid` file must have `pm.get_end_time() >= SongMetrics.duration_seconds`, guaranteed via an end-of-track marker `pretty_midi.Text("END_TRACK", SongMetrics.duration_seconds)`.

### S3: Orchestration & CLI Invariance
- **S3-01:** `pipeline run` estimates `SongMetrics` once per song and passes it into `TranscribeContour` and `TranscribeStem`.
- **S3-02:** CLI displays resolved song metrics: tempo BPM, duration in seconds, and time signature.
