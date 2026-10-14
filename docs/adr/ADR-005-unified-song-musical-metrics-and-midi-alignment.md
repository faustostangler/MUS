# ADR-005: Unified Song Musical Metrics and Multi-Stem MIDI Alignment

**Status:** Accepted (2026-10-14, approved by Lead Architect)
**Date:** 2026-10-14
**Decision Makers:** Lead Architect (Fausto Stangler), High-Performance Implementer (AI pair)
**Supersedes:** ADR-003 (amends MIDI instantiation and temporal metadata)
**Superseded by:** —

## Context

In ADR-003 and ADR-004, the pipeline introduced symbolic transcription and acoustic resynthesis across all six Demucs stems (`vocals`, `bass`, `drums`, `guitar`, `piano`, `other`).

However, all stems originate from the **same musical performance** (the single master song). The user observed that shared global musical properties:
1. **Tempo (BPM):** The musical pulse of the song. Currently, non-vocal stem transcribers (`TranscribeBass`, `TranscribeDrums`, `TranscribeHarmonic`) instantiate `pretty_midi.PrettyMIDI()` with an implicit default of 120.0 BPM, while vocal lead transcription used a CLI option defaulting to 120.0 BPM without automated tempo estimation.
2. **Time Signature (Compasso):** Standard meter (e.g. 4/4) was not explicitly declared via MIDI meta-events (`pretty_midi.TimeSignature`), leaving DAWs and score notation tools to guess meter.
3. **Total Duration:** In MIDI, a file's duration is determined by its latest event timestamp. If a stem enters late or exits early (e.g. a vocal part or a guitar solo ending before the song outro), its `.mid` file appears truncated in DAWs and timeline editors, breaking multitrack alignment across tracks.

## Decision

**D1 — Domain Value Object `SongMetrics`.**
In `mus.shared_kernel.metrics` (or `music_transcription.domain`), introduce an immutable value object:
```python
@dataclass(frozen=True, slots=True)
class SongMetrics:
    tempo_bpm: float
    duration_seconds: float
    time_signature_numerator: int = 4
    time_signature_denominator: int = 4
```
And a domain estimation utility `estimate_song_metrics(signal: AudioSignal, preferred_bpm: float | None = None)` that:
- Estimates rhythmic tempo via `librosa.beat.beat_track` from audio with prominent percussive/transient energy (or fallback to user-specified BPM).
- Computes exact song duration from `signal.duration_seconds`.
- Sets standard 4/4 time signature as default.

**D2 — Uniform Multi-Stem MIDI Construction.**
All transcription use cases (`TranscribeContour`, `TranscribeBass`, `TranscribeDrums`, `TranscribeHarmonic`) must accept `SongMetrics` and construct their `PrettyMIDI` objects with:
1. `pm = pretty_midi.PrettyMIDI(initial_tempo=metrics.tempo_bpm)`
2. `pm.time_signature_changes.append(pretty_midi.TimeSignature(metrics.time_signature_numerator, metrics.time_signature_denominator, 0.0))`
3. `pm.text_events.append(pretty_midi.Text("END_TRACK", metrics.duration_seconds))`

This guarantees that `pm.get_end_time()` matches the master track duration and all metadata meta-events are identical across all stems.

**D3 — Pipeline Orchestration.**
In `pipeline.py`:
- `SongMetrics` is estimated or initialized once per song upon audio loading/separation.
- The single canonical `SongMetrics` instance is injected into `TranscribeContourCommand` and `TranscribeStemCommand`.
- The CLI logs the resolved metrics for observability.

## Consequences

### Positive
- Strict multitrack synchronization: all 6 `.mid` files have identical tempo, bar lines, meter, and exact timeline boundaries in any DAW or notation software.
- Automated tempo extraction eliminates manual `--bpm` guesswork.
- Preserves DDD principles with a dedicated domain Value Object and clean port/adapter interfaces.

### Negative / Neutral
- Librosa beat tracking adds a lightweight computation step (~1-2s per track), which can be bypassed if an explicit BPM is provided.
