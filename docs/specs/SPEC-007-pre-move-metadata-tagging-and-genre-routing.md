# SPEC-007: Pre-Move Metadata Tagging, Genre Routing, and Resilient Timeout Specification

## 1. Overview & Invariants

This specification enforces the operational ordering defined in ADR-007 for track ingestion, metadata tagging, genre folder determination, and track folder encapsulation.

### Invariants:
1. **Download Staging**: Downloads occur in `base_output_dir / ".staging"`, never directly exposing intermediate files in `library/`.
2. **Metadata Before Move**: No file is moved from staging into the genre directory until `TrackMetadata` (including `genre`, `artist`, `track`) is resolved.
3. **Ollama Timeout**: The HTTP client timeout for Ollama queries is set to `120.0` seconds by default.
4. **Canonical Relocation**: The staged audio file is moved to `base_output_dir / {genre_slug} / f"{canonical_title}.mp3"`.
5. **Stem Encapsulation**: Stems are generated into `base_output_dir / {genre_slug} / {canonical_title} /`.
6. **Video ID Fidelity**: Authentic YouTube `video_id` is retained in `TrackMetadata` and catalog history.

## 2. Component Specifications

### 2.1 Configuration (`mus.config`)
- Add `OLLAMA_TIMEOUT_SECONDS: float = 120.0` to `MusSettings`.
- Invariant: `OLLAMA_TIMEOUT_SECONDS > 0`.

### 2.2 Ports & Adapters (`stem_separation`)
- `CatalogHistoryPort`:
  - `get_entry(video_id: str) -> dict[str, Any] | None`
- `OllamaMetadataTagger`:
  - `__init__(ollama_host: str = "http://localhost:11434", model: str = "qwen2.5:latest", timeout: float = 120.0)`
- `IngestAndSeparateTrack`:
  - Accepts `staging_dir = base_output_dir / ".staging"`.
  - Downloads to `staging_dir`.
  - Queries `tagger.tag(raw_title)` and preserves `video_id`.
  - Moves and renames file to `genre_dir / f"{canonical_title}.mp3"`.
  - Separates stems into `genre_dir / canonical_title`.
