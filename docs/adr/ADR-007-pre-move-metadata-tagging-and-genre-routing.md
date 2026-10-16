# ADR-007: Pre-Move Metadata Tagging, Genre Routing, and Resilient Timeout

**Status:** Accepted (2026-10-15, approved by Lead Architect)
**Date:** 2026-10-15
**Decision Makers:** Lead Architect (Fausto Stangler), High-Performance Implementer (AI pair)
**Supersedes:** ADR-006 (refines ingestion lifecycle and staging flow)
**Superseded by:** —

## Context

In ADR-006, the output hierarchy was promoted to `./library/{genre_slug}/{artist} - {track}/` with the full track master placed directly in `./library/{genre_slug}/{artist} - {track}.mp3`.

However, during end-to-end execution, audio files were downloaded directly into `./library/` before metadata resolution occurred. Due to an aggressive 3.0-second HTTP timeout in `OllamaMetadataTagger`, cold LLM inference failed, triggering a heuristic fallback that assigned `genre="Other"` and `artist="Unknown Artist"`. Consequently:
1. Master tracks were relocated to `library/other/` instead of their respective musical genres (`rock`, `country`, `samba-reggae`).
2. Stems were encapsulated under non-canonical directory names (e.g. `library/other/Don't Stop Me Now/` rather than `library/rock/Queen - Don't Stop Me Now/`).
3. Catalog history lost the authentic YouTube `video_id`, creating orphaned and duplicate records in `history.json`.

## Decision

**D1 — Resilient Ollama Timeout.**
Set `OLLAMA_TIMEOUT_SECONDS = 120.0` in `MusSettings` (configurable via environment variable `MUS_OLLAMA_TIMEOUT_SECONDS`). In `OllamaMetadataTagger`, inject the configurable timeout into HTTP calls, eliminating premature aborts during model loading.

**D2 — Staging Before Genre Resolution.**
Raw downloads must NOT be deposited directly into the root `./library/`. The downloader deposits raw files into a staging directory `./library/.staging/`.

**D3 — Mandatory Metadata Tagging Before Moving.**
Before moving or renaming any downloaded file:
1. Extract authentic `video_id` from the source URL or download result.
2. Query catalog history or Ollama with the raw title to extract `artist`, `track`, and `genre`.
3. If Ollama or network fails, fall back gracefully to catalog history before heuristic fallback.
4. Compute `genre_dir = library_dir / sanitize_genre(metadata.genre)`.
5. Compute `canonical_title = build_canonical_title(metadata.artist, metadata.track, default=raw_title)`.
6. Atomically move and rename the staged audio file to `genre_dir / f"{canonical_title}.mp3"`.

**D4 — Track-Level Stem Encapsulation & Catalog Preservation.**
Demucs stem separation is executed with output directed to `genre_dir / canonical_title/`. The authentic YouTube `video_id` is preserved in `TrackMetadata` and recorded into `history.json`.

## Consequences

### Positive
- Strict order of operations: download -> Ollama tagging (120s timeout) -> genre resolution -> move to `library/{genre}/{artist} - {track}.mp3` -> stem separation inside `library/{genre}/{artist} - {track}/`.
- Clean library root with zero unclassified loose files.
- Resilient Ollama queries that do not time out under GPU load.
- Accurate catalog entries with proper YouTube video IDs.

### Negative / Neutral
- Ollama inference may take longer on cold model start (up to 120s), but ensures accurate genre categorization.
