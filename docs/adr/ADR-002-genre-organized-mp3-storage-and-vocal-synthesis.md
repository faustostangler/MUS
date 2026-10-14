# ADR-002: Genre-Organized MP3 Storage, Vocal Resynthesis and Multi-Stem MIDI Roadmap

**Status:** Accepted (2026-10-13, approved by Lead Architect)
**Date:** 2026-10-13
**Decision Makers:** Lead Architect (Fausto Stangler), High-Performance Implementer (AI pair)
**Supersedes:** —
**Superseded by:** —

## Context

In ADR-001, the system established hexagonal bounded contexts (`stem_separation`, `voice_modeling`, `music_transcription`, `instrument_rendering`, `shared_kernel`). During pipeline execution, separated stems were placed in a flat `outputs/stems/` directory, while synthesized artifacts (`_midi_preview.wav`, `_vocals_synth.wav`) and the transcribed MIDI file were written to the root `outputs/` directory in uncompressed PCM WAV format.

The legacy architecture (`legacy/stem_separation/separate_stems.py`) maintained an organized music library sorted by musical genre:
`outputs/stems/{genre}/{artist} - {track}.mp3` and `outputs/stems/{genre}/{artist} - {track} - {stem}.mp3`.

Furthermore, the user experience requires:
1. **Universal MP3 Encoding:** Storage consumption for raw WAV files (24-bit/44.1 kHz is ~32 MB for a 4-minute take) is excessive. All generated audio must be compressed to 320 kbps MP3 instead of WAV.
2. **Preview Elimination:** Acoustic previews (`_midi_preview.wav`) rendered via rudimentary MIDI synthesis pollute the filesystem and are redundant. Only high-fidelity vocoder resyntheses are needed.
3. **Co-located Output Topology:** The synthesized vocal audio (`{artist} - {track} - vocals - synt.mp3`) and the transcribed melody (`{artist} - {track} - vocals.mid`) must live directly alongside the separated stems inside the genre directory: `outputs/stems/{genre}/`.
4. **Multi-Stem MIDI Roadmap:** Prepare the system architecture for future multi-stem transcription (Bass F0 contour and Drum onset/transient mapping).

Forces at play:
- **I/O Efficiency & Disk Footprint:** 320 kbps MP3 is ~10x smaller than 24-bit WAV, maintaining acoustic fidelity for listening while drastically saving disk space.
- **Library Organization:** Storing tracks grouped by genre matches the user's legacy curation workflow.
- **Port Contracts:** `AudioWriterPort` must support writing `.mp3` transparently based on target file extension without breaking existing WAV capabilities when needed.

## Decision

**D1 — Genre-Partitioned Stem Ingestion.**
In `IngestAndSeparateTrack` (`stem_separation`), the target output directory is dynamically partitioned by the sanitized genre tag produced by `MetadataTaggerPort` (defaulting to `"Unknown"` if untagged):
`target_dir = base_output_dir / sanitize_genre(metadata.genre)`.
All isolated stems and original audio are placed in this directory.

**D2 — Universal MP3 Audio Persistence.**
`SoundfileAudioIO` (`voice_modeling.infrastructure`) is updated to inspect the output path suffix. When `.mp3` is targeted, it encodes the `AudioSignal` as MPEG-1/2 Audio (MP3 at 320 kbps) using `soundfile.write(..., format="MP3")`.

**D3 — Elimination of Acoustic Preview WAV.**
The legacy generation of `_midi_preview.wav` in the unified pipeline CLI is permanently decommissioned. The pipeline produces symbolic MIDI and true vocoder resynthesis only.

**D4 — Resynthesized Vocal Naming & Co-location.**
The resynthesized vocal take is saved as `{artist} - {track} - vocals - synt.mp3` and the symbolic MIDI as `{artist} - {track} - vocals.mid`, both co-located inside `outputs/stems/{genre}/`.

**D5 — Multi-Stem MIDI Architecture (Phase 2 Roadmap).**
To enable MIDI transcription for non-vocal stems:
- **Bass:** Will utilize an F0 contour estimator tuned to the 30 Hz – 400 Hz range and segment into General MIDI Program 33 (Electric Bass Finger).
- **Drums:** Will utilize multi-band transient/onset detection (Low < 150 Hz -> Kick Note 36, Mid 200–800 Hz -> Snare Note 38, High > 5 kHz -> Hi-hat Note 42) mapped to General MIDI Channel 10.
- **Polyphonic Stems (Guitar/Piano):** Will route to a dedicated polyphonic transcription port (e.g., `basic-pitch` adapter).

## Consequences

### Positive
- Strict alignment with the legacy library structure (`stems/{genre}/`).
- 90% reduction in disk storage by avoiding uncompressed WAV files.
- Clean directory layout without transient preview files.
- Resynthesized voice and MIDI files are immediately discoverable alongside original stems.

### Negative / Neutral
- Lossy compression: MP3 is lossy, though 320 kbps is acoustically transparent for human evaluation.
- Tagging dependency: If Ollama metadata tagging fails or is offline, genre falls back to `"Unknown"`.

## Compliance Checks

- [x] Hexagonal Architecture layers respected (Domain agnostic, I/O in infrastructure).
- [x] No framework dependencies in Domain layer.
- [x] Test strategy defined (Unit tests with synthetic data, regression verification).
- [x] No boundary violations across bounded contexts.
