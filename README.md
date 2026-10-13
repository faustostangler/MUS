# MUS — Vocal Stem Parametric Pipeline

Source-filter decomposition (WORLD), pitch/formant modulation, MIDI transcription and
instrument/vocalise rendering of Demucs vocal stems.

- Architecture: [ADR-001](docs/adr/ADR-001-source-filter-vocal-resynthesis-pipeline.md)
- Specs: [SPEC-001](docs/specs/SPEC-001-source-filter-vocal-pipeline.md)
- Glossary: [GLOSSARY](docs/GLOSSARY.md)
- Legacy stem separation: `legacy/stem_separation/separate_stems.py` (data in `data/`)

```bash
uv sync
uv run pytest
uv run mus --help
```
