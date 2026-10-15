# ADR-006: Track-Folder Stem Encapsulation and Direct Library Root

**Status:** Accepted (2026-10-15, approved by Lead Architect)
**Date:** 2026-10-15
**Decision Makers:** Lead Architect (Fausto Stangler), High-Performance Implementer (AI pair)
**Supersedes:** ADR-004 (amends root path and genre folder hierarchy)
**Superseded by:** —

## Context

In ADR-004, the system consolidated audio outputs under `outputs/library/{genre_slug}/`. With multi-stem separation, symbolic transcription, and resynthesis, each track produces 19 distinct files (1 master mix MP3 + 6 stems × 3 triplet files: `.mp3`, `.mid`, `- mid.mp3`).

When multiple tracks are processed within the same genre (e.g. `samba-reggae`), having all stems co-located in a single flat directory creates severe clutter, cognitive friction, and potential filename collisions across tracks sharing identical sub-names.

Furthermore, the nested path `outputs/library/` introduced unnecessary indirection. The canonical root for all library assets and internal caches should be directly `library/`, containing `library/cache/` for intermediate voice models and `library/{genre_slug}/` for categorized tracks.

## Decision

**D1 — Direct Library Root & Internal Cache Directory.**
The root directory for all system outputs is promoted to `./library/`. The voice model decomposition cache is relocated to `./library/cache/`. The legacy `./outputs/` directory is abolished.

**D2 — Track-Level Stem Encapsulation.**
Within each genre folder (`library/{genre_slug}/`):
1. The full song master MP3 is placed directly in the genre folder:
   `library/{genre_slug}/{artist} - {track}.mp3`
2. A dedicated directory named `{artist} - {track}` encapsulates all stem-related assets:
   `library/{genre_slug}/{artist} - {track}/`
3. All 6 stem triplets are co-located inside this track directory:
   - `{artist} - {track} - {stem}.mp3`
   - `{artist} - {track} - {stem}.mid`
   - `{artist} - {track} - {stem} - mid.mp3`

**D3 — Ingestion, Separation & Pipeline Topology.**
- `IngestAndSeparateTrack`: places `{canonical_title}.mp3` in `genre_dir`, creates `track_dir = genre_dir / canonical_title`, and directs Demucs to deposit stems into `track_dir`.
- `pipeline.py`: coordinates vocal decomposition (using cache in `library/cache`), contour transcription, and multi-stem synthesis entirely within `vocal_stem_path.parent` (the encapsulated `track_dir`).
- `is_track_fully_processed()`: checks `library/{genre_slug}/{artist} - {track}/` to verify the presence of all stem triplets.

## Consequences

### Positive
- Clean, modular file organization: genre folders contain high-level tracks, while stem details are neatly encapsulated in individual track subfolders.
- Direct root (`./library/`) aligns with domain ubiquitous language, removing redundant `outputs/` indirection.
- Cache co-located cleanly at `./library/cache/`.
- Zero file clutter when dozens of tracks exist within the same genre.

### Negative / Neutral
- Existing files in `outputs/` require migration to the new topology (completed as part of transition).
