# ADR-003: Multi-Stem MIDI Transcription and Acoustic Resynthesis

**Status:** Accepted (2026-10-13, approved by Lead Architect)
**Date:** 2026-10-13
**Decision Makers:** Lead Architect (Fausto Stangler), High-Performance Implementer (AI pair)
**Supersedes:** —
**Superseded by:** —

## Context

In ADR-001 and ADR-002, the MUS architecture established hexagonal bounded contexts and vocal lead transcription (`TranscribeContour` -> GM 52 Choir Aahs), co-locating the vocal stem, MIDI and resynthesized MP3 under `outputs/stems/{genre}/`.

The user requirement now expands transcription and synthesis from the single vocal stem to **all six Demucs stems**:
1. `vocals`: Monophonic lead voice -> MIDI GM 52 + WORLD vocoder resynthesis (`vocals - synt.mp3`).
2. `bass`: Predominantly monophonic low-frequency instrument -> MIDI GM 33 (Electric Bass) + acoustic MP3 resynthesis (`bass - synt.mp3`).
3. `drums`: Unpitched percussion and transients -> Multi-band onset detection mapped to General MIDI Channel 10 (Kick 36, Snare 38, Hi-hat 42) -> MIDI + acoustic MP3 resynthesis (`drums - synt.mp3`).
4. `guitar`: Harmonic/chords -> Multi-pitch tracking -> MIDI GM 25 (Acoustic Guitar) + acoustic MP3 resynthesis (`guitar - synt.mp3`).
5. `piano`: Harmonic/polyphonic -> Multi-pitch tracking -> MIDI GM 0 (Acoustic Grand Piano) + acoustic MP3 resynthesis (`piano - synt.mp3`).
6. `other`: Melodic/polyphonic (synths, strings, horns) -> Multi-pitch tracking -> MIDI GM 48 (String Ensemble) + acoustic MP3 resynthesis (`other - synt.mp3`).

Forces at play:
- **Acoustic Diversity:** Different stems possess distinct physical properties. Vocals and bass exhibit clear fundamental frequency (F0) contours; drums consist of unpitched impulsive transients; guitar and piano have multiple harmonic peaks.
- **Dependency Footprint:** Heavy neural transcription packages like `basic-pitch` or Magenta pull large ML dependencies (TensorFlow/ONNX) with potential version conflicts. Relying on `librosa`, `scipy`, `numpy`, and `pretty_midi` provides lightweight, fast, deterministic transcription without new external runtime dependencies.
- **Uniform Storage Topology:** All resulting `.mid` files and their acoustic MP3 renderings (`- synt.mp3`) must be co-located with the stems in `outputs/stems/{genre}/`.

## Decision

**D1 — Domain Stem Transcribers.**
In `music_transcription`, we introduce modular stem transcription services:
1. `TranscribeBass`: Uses F0 estimation clamped to bass register (30 Hz - 400 Hz) followed by hysteresis segmentation to output MIDI GM 33 (Electric Bass).
2. `TranscribeDrums`: Decomposes drum signals into sub-bands (< 150 Hz for Kick Note 36, 200 Hz - 2000 Hz for Snare Note 38, > 3000 Hz for Hi-hat Note 42) using onset detection to output a General MIDI drum track on Channel 10 (`is_drum=True`).
3. `TranscribeHarmonic`: Uses multi-peak spectral tracking (`librosa.piptrack`) to capture dominant pitches/chords and construct polyphonic `pretty_midi.Instrument` tracks for `guitar` (GM 25), `piano` (GM 0), and `other` (GM 48).

**D2 — Universal Acoustic Resynthesis to MP3.**
For non-vocal stems, their generated MIDI files are synthesized to audio via `pretty_midi.synthesize()` and saved as 320 kbps MP3 files using `SoundfileAudioIO.write(..., format="MP3")` with suffix `- synt.mp3`. Vocals continue using high-fidelity WORLD vocoder synthesis.

**D3 — Pipeline Orchestration & Idempotency.**
`pipeline.py` coordinates transcription and resynthesis for all available stems in the track. The idempotency check `is_track_fully_processed()` verifies that all active stems have both their `.mid` and `- synt.mp3` artifacts on disk before declaring the track completed.

## Consequences

### Positive
- Full symbolic transcription coverage across all 6 stems.
- Every stem receives an audition-ready `- synt.mp3` file.
- Zero new heavy external dependencies; builds purely on top of `librosa`, `scipy`, `numpy`, and `pretty_midi`.
- Complete co-location inside `outputs/stems/{genre}/`.

### Negative / Neutral
- Multi-pitch tracking on guitar/piano is heuristic-based (spectral peak picking) compared to heavy neural models, but executes in O(seconds) without GPU VRAM overhead.
