# SPEC-004: Library Topology, Canonical Naming, and Stem Triplet Synthesis Specification

**Linked ADR:** [ADR-004](../adr/ADR-004-library-topology-canonical-naming-and-stem-triplet-synthesis.md)

## Acceptance Criteria

### S1: Directory Topology & Genre Slug Normalization
- **S1-01:** All pipeline track outputs are housed under `outputs/library/`.
- **S1-02:** `sanitize_genre()` produces lowercase alphanumeric hyphen-separated slugs (e.g. `"samba-reggae"`, `"pop-rock"`, `"jazz"`).
- **S1-03:** Unknown or missing genres default to `"unknown"` slug subfolder.

### S2: Canonical Track Title Formatting
- **S2-01:** `build_canonical_title()` generates `{artist} - {track}` when artist is present and distinct from track.
- **S2-02:** Redundant artist prefixes are omitted when already embedded in the track title string.

### S3: Triplet Artifact Invariant per Stem
- **S3-01:** For every stem `$STEM` (`vocals`, `bass`, `drums`, `guitar`, `piano`, `other`), the system outputs exactly three files:
  1. `{artist} - {track} - {stem}.mp3`
  2. `{artist} - {track} - {stem}.mid`
  3. `{artist} - {track} - {stem} - mid.mp3`
- **S3-02:** Full mix audio is saved as `{artist} - {track}.mp3`.
- **S3-03:** Resynthesized MIDI stems carry the suffix `- mid.mp3` (superseding `- synt.mp3`).

### S4: Drum Synthesis & AudioSignal Safety
- **S4-01:** Drum instrument tracks (`is_drum=True` or MIDI Channel 10) are synthesized via dedicated percussive waveform rendering.
- **S4-02:** Resynthesized waveforms contain neither `NaN` nor `Inf` values and do not trigger `SilentTakeError`.

### S5: Idempotency Verification
- **S5-01:** `is_track_fully_processed()` returns `True` if all stem `.mp3` files have corresponding `.mid` and `- mid.mp3` files in `outputs/library/{genre_slug}/`.
- **S5-02:** Subsequent pipeline executions bypass already processed tracks in `< 0.5s`.
