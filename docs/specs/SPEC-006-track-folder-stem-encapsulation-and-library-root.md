# SPEC-006: Track-Folder Stem Encapsulation and Direct Library Root Specification

**Linked ADR:** [ADR-006](../adr/ADR-006-track-folder-stem-encapsulation-and-library-root.md)

## Acceptance Criteria

### S1: Root Topology & Cache Location
- **S1-01:** System configuration defaults `LIBRARY_DIR` to `./library`.
- **S1-02:** Voice model NPZ cache is stored at `./library/cache`.
- **S1-03:** The legacy `./outputs` directory is superseded and no longer created by default.

### S2: Genre Directory Hierarchy
- **S2-01:** Genre directories are direct children of `library/` formatted in lowercase slug (e.g. `library/samba-reggae/`).
- **S2-02:** The full master track MP3 is located directly at `library/{genre_slug}/{artist} - {track}.mp3`.
- **S2-03:** A dedicated subfolder `library/{genre_slug}/{artist} - {track}/` contains all stem assets for that song.

### S3: Stem Triplet Encapsulation
- **S3-01:** For each of the 6 stems (`vocals`, `bass`, `drums`, `guitar`, `piano`, `other`), the three corresponding files reside inside `library/{genre_slug}/{artist} - {track}/`:
  1. `{artist} - {track} - {stem}.mp3`
  2. `{artist} - {track} - {stem}.mid`
  3. `{artist} - {track} - {stem} - mid.mp3`

### S4: Ingestion and Idempotency Invariants
- **S4-01:** `IngestAndSeparateTrack` outputs stems into `genre_dir / canonical_title /`.
- **S4-02:** `is_track_fully_processed()` returns `True` when `library/{genre_slug}/{artist} - {track}/` contains completed triplets for all stems.
