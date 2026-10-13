# ADR-001: Source-Filter Vocal Decomposition, Modulation and Resynthesis Pipeline

**Status:** Accepted (2026-10-12, approved with PLAN-001)
**Date:** 2026-10-12
**Decision Makers:** Lead Architect (Fausto Stangler), High-Performance Implementer (AI pair)
**Supersedes:** —
**Superseded by:** —

## Context

The current system (`src/separate_stems.py`, legacy single-file script) downloads tracks
(yt-dlp), tags them (Ollama), and isolates six **Stems** with HTDemucs (`htdemucs_6s`),
persisting them as `"{artist} - {track} - {stem}.mp3"` (320 kbps, stereo, 44.1 kHz) under
`src/library/{genre}/`, with completion tracked in `src/history.json`.

The new business capability is to treat the **Vocal Stem** as a parametric object rather
than as a waveform: decouple **Pitch Contour** (source, F0), **Spectral Envelope**
(filter, formants) and **Aperiodicity** (stochastic component), manipulate each axis
independently, and route the result to (a) a resynthesized **Vocal Take**, (b) a
symbolic **Note Sequence** (MIDI / MuseScore score), (c) an acoustic-instrument rendering
(SoundFont), or (d) a formant-driven **Vocalise** sung from arbitrary MIDI.

Forces at play:

- **Physics:** Direct STFT-magnitude manipulation couples source harmonics with filter
  poles (chipmunk effect on transposition) and requires phase reconstruction (Griffin-Lim
  artifacts). The source-filter model `s(t) = e(t) * h(t) + n(t)` removes both problems.
- **Input quality:** Vocal Stems are lossy MP3, stereo, and contain Demucs bleed, reverb
  tails and backing vocals (residual polyphony). F0 estimation will produce octave errors
  and spurious voicing that the domain must tolerate.
- **Saturation:** WORLD's `CheapTrick` spectral envelope at 44.1 kHz has
  `fft_size = 2048 → 1025 bins` per 5 ms frame. A 4-minute take is ~48 000 frames:
  SP alone ≈ 394 MB in `float64`, SP + AP ≈ 790 MB, doubled on every immutable copy.
- **Toolchain:** `uv`, `ffmpeg`, `libfluidsynth3`, and MuseScore (snap) are present;
  `fluidsynth` CLI, `pytest`, `ruff`, `mypy`, `mutmut` are not installed globally.
  `basic-pitch` carries a heavy ML runtime (TensorFlow/ONNX) that may conflict with the
  existing `torch`/`demucs` stack on Python 3.12.
- **Team:** Single developer + AI pair, CLI-first batch workloads, no network service yet.

Ubiquitous Language: see `docs/GLOSSARY.md` (Vocal Stem, Parametric Voice, Pitch Contour,
Spectral Envelope, Aperiodicity, Vocal Tract Scale, Formant Target, Vowel Window,
Note Sequence, Hysteresis Segmentation, Round-Trip Fidelity, Vocalise, Render Route).

## Decision

**D1 — Model.** We will adopt the classic **Source-Filter Model** implemented by the
**WORLD vocoder (`pyworld`)** as the single analysis/synthesis engine
(`Harvest|DIO+StoneMask` → F0, `CheapTrick` → SP, `D4C` → AP, `synthesize` → waveform),
at a fixed **Frame Period** of 5.0 ms, because it decouples the three physical axes,
avoids phase reconstruction, and makes symbolic transformations O(frames) instead of
O(STFT bins × iterations).

**D2 — Bounded Contexts.** We will introduce three new bounded contexts inside a
**Modular Monolith** package `mus`, plus a **Shared Kernel**, because pitch physics,
symbolic music and instrument rendering evolve at different rates and have different
external dependencies:

| Context | Subdomain | Owns | External deps (infra only) |
|---|---|---|---|
| `voice_modeling` | **Core** | Parametric Voice, pitch modulation, formant estimation/warping, vowel substitution, Vocalise synthesis, resynthesis | `pyworld`, `soundfile`, `scipy` |
| `music_transcription` | Supporting | Pitch Contour → Note Sequence (Hysteresis Segmentation), tempo grid, MIDI/score export | `pretty_midi`, `librosa` (tempo), `basic-pitch` (optional), MuseScore CLI |
| `instrument_rendering` | Generic | Note Sequence → audio via General MIDI SoundFont | `fluidsynth` CLI |
| `shared_kernel` | — | Units (`Hertz`, `Seconds`, `Semitones`, `SampleRate`, `FramePeriod`, `TimeWindow`), `PitchContour`, `NoteEvent`, `NoteSequence`, `AudioSignal` | `numpy` only |
| `stem_catalog` (ACL) | Generic | Read-only lookup of Vocal Stems produced by the legacy script | filesystem (`history.json`) |

**D3 — All vocal synthesis goes through one Port.** Route 4B (MIDI → Vocalise) will NOT
implement a separate glottal-pulse + IIR synthesizer. It will build a synthetic
`ParametricVoice` (F0 from the Note Sequence with portamento/vibrato, SP from the
Formant Target all-pole response, AP from a voiced template) and call the same
`VocoderPort.synthesize`, because one engine means one fidelity contract, one test
harness and zero duplicated DSP.

**D4 — Formant manipulation strategy.** Vocal Tract Scale (α) is applied as a
frequency-axis warp of each SP frame (`SP'(f) = SP(f / α)`, log-magnitude interpolation,
energy-preserving). Vowel substitution defaults to **piecewise-linear spectral warping**
anchored at (0, F1→F1', F2→F2', F3, Nyquist), with formants estimated per frame via LPC
on the autocorrelation derived from SP (inverse FFT of the power spectrum +
Levinson-Durbin). Envelope **overwrite** with a synthetic all-pole response is an
explicit secondary mode. Edits are confined to a **Vowel Window** with raised-cosine
crossfades (default 30 ms). Warping is the default because it preserves the singer's
spectral tilt and fine envelope detail, keeping coherence with untouched frames.

**D5 — Memory budget via segmentation.** Analysis and synthesis operate on
**Analysis Segments** split at silences (≥ 200 ms below a dBFS threshold) with a
configurable `max_segment_seconds` (default 30 s). Domain arrays are `float64`,
C-contiguous, and marked read-only (`flags.writeable = False`) to enforce immutability.
Disk cache of a Parametric Voice uses `numpy.savez_compressed` with `float32` SP/AP and
`allow_pickle=False` (never `pickle`).

**D6 — Transcription tracks.** Track A (analytic, from Pitch Contour, Hysteresis
Segmentation) is the default and a pure-domain algorithm. Track B (`basic-pitch`) is an
**optional extra** (`mus[neural]`) behind `NeuralTranscriberPort`; if Spike-002 shows
dependency conflicts, the adapter invokes `basic-pitch` in an isolated `uv tool`
environment via subprocess (process-level ACL).

**D7 — Instrument rendering.** We will call the `fluidsynth` CLI through a subprocess
adapter (`FluidSynthCliRenderer`) instead of `midi2audio`, because `midi2audio` is an
unmaintained thin wrapper over the same CLI and adds no value; the SoundFont path is
configuration (`MUS_SOUNDFONT_PATH`, default `FluidR3_GM.sf2`).

**D8 — Legacy coexistence.** The legacy `separate_stems.py` is NOT refactored in this
ADR. The new pipeline consumes its output read-only through `LegacyStemCatalogAdapter`
(ACL translating `history.json` + file-naming convention into `VocalStemRef`). Strangling
the legacy script into a `stem_separation` context is deferred to a future ADR.

**D9 — Presentation.** A thin `typer` CLI (`mus voice …`, `mus transcribe …`,
`mus render …`) is the only entrypoint; one Dockerfile manifests all roles.

## Consequences

### Positive
- C1: Transposition without chipmunk effect: F0 changes while SP is untouched.
- C2: Round-Trip Fidelity becomes a measurable contract (F0 cents error, MCD in dB).
- C3: Symbolic export (MIDI Type 1, tempo-aware) importable by MuseScore and DAWs.
- C4: Vocal Tract Scale and vowel substitution are deterministic, unit-testable
  functions over arrays, independent of `pyworld`.
- C5: Route 4B reuses the vocoder: no second synthesizer to maintain (D3).
- C6: Each context is extractable to a microservice: contexts exchange only Shared
  Kernel types (`PitchContour`, `NoteSequence`, `AudioSignal`).

### Negative
- N1: WORLD is lossy; Round-Trip is not sample-identical. Thresholds must be calibrated
  empirically (Spike-001) before being frozen in SPEC-001.
- N2: Harvest is slow (order of real-time on CPU); DIO is faster but less robust.
  Segment-level parallelism (`ProcessPoolExecutor`) may be required.
- N3: Demucs bleed/backing vocals degrade F0 → needs voicing gating, median smoothing
  and octave-jump correction in the domain.
- N4: New system dependencies: `fluidsynth` CLI, a GM SoundFont, MuseScore (snap
  confinement restricts file access outside `$HOME`; non-home mounts need the
  `removable-media` interface).
- N5: Immutable array entities double peak memory per transformation; mitigated by D5.

### Neutral
- Audio library must move out of `src/` to `data/library/` (12-Factor: config via
  `MUS_LIBRARY_DIR`); 3.1 GB of audio must never enter Git.
- No database, no LLM in this pipeline; Langfuse not applicable.

## Alternatives Considered

### Alternative A: STFT magnitude manipulation + Griffin-Lim / phase vocoder
- **Pros:** Simple, `librosa` only, no C-extension.
- **Cons:** Phase artifacts; source/filter coupling (chipmunk effect); no explicit
  formant control.
- **Why rejected:** Violates the core requirement of independent physical axes.

### Alternative B: Neural vocoder / voice conversion (DDSP, RVC, so-vits-svc, HiFi-GAN)
- **Pros:** Higher perceptual quality, timbre transfer.
- **Cons:** Training data, GPU contention with Demucs, opaque latent space (no explicit
  F1/F2 control), non-deterministic outputs hard to unit-test.
- **Why rejected:** Opposes the analytic, explainable modulation goal. Revisit as a
  future `VocoderPort` adapter.

### Alternative C: Praat / Parselmouth (PSOLA + LPC formant manipulation)
- **Pros:** Mature formant tracking, scientific pedigree.
- **Cons:** PSOLA degrades on large shifts; GPL licensing; Praat object model leaks
  into code.
- **Why rejected:** WORLD gives cleaner decoupling; Parselmouth may still be used in
  tests as an independent formant oracle.

### Alternative D: Separate glottal-pulse (Rosenberg/LF) + IIR cascade synth for Route 4B
- **Pros:** Classic Klatt formant synthesis, full control of glottal shape.
- **Cons:** Second DSP engine, separate fidelity harness, duplicated formant code.
- **Why rejected:** D3 reuses WORLD; Rosenberg source remains a possible later adapter.

### Alternative E: `midi2audio` for rendering
- **Why rejected:** See D7.

## Cross-Context State Strategy

- **Boundary Violations check:** No context reads another context's storage. Each
  context writes its own artifacts under `MUS_OUTPUT_DIR/{context}/{take_id}/`.
  `stem_catalog` exposes Vocal Stems through a Port; nobody else parses
  `history.json`. **Result: no violation.**
- **Consistency Model:** In-process, synchronous orchestration by an application-level
  `VocalPipeline` use case (Orchestration style) passing immutable Shared Kernel values
  in memory. No cross-context transaction exists; there is no shared mutable state.
  Domain events (`VoiceDecomposed`, `NoteSequenceTranscribed`, `InstrumentRendered`)
  are emitted to an in-memory EventBus for observability only.
- **Failure Modes & Compensation:** Every stage is a pure function of
  `(input content hash, parameters hash)`. Artifacts are written atomically
  (`*.tmp` → `rename`). On failure the stage leaves no partial artifact; re-running is
  idempotent (cache hit by key `sha256(input)[:16] + params_hash`). No compensation
  events required. SLA: not applicable (batch CLI).
- **Transactional Outbox:** Not required (single process, no broker, no DB). Must be
  revisited if any context is deployed as a separate service (per stangler-doctor §3).

## Langfuse Ingestion Strategy

Not applicable: this ADR contains no LLM/generative-AI interaction. (The legacy Ollama
tagging is out of scope, D8.)

## Observability Plan

- **Logs:** `structlog` JSON to stdout (Loki-ready), bound fields: `take_id`, `stage`,
  `segment_index`, `params_hash`.
- **Golden Signals (Prometheus, pushed via Pushgateway when `MUS_PUSHGATEWAY_URL` set,
  else textfile):** `mus_stage_duration_seconds{stage}` (latency histogram),
  `mus_takes_processed_total{stage,outcome}` (traffic/errors),
  `mus_peak_rss_bytes{stage}` and `mus_realtime_factor{stage}` (saturation).
- **Domain Metrics:** `mus_voiced_ratio`, `mus_f0_octave_jump_rate`,
  `mus_roundtrip_f0_rmse_cents`, `mus_roundtrip_mcd_db`, `mus_notes_per_minute`,
  `mus_transcription_pitch_agreement_ratio` (Track A vs re-analysis),
  `mus_formant_target_error_ratio`.
- **Errors:** Sentry optional (`MUS_SENTRY_DSN`), tagged with `GIT_SHA`.

## Security / LGPD

No personal data processed. Audio is copyrighted third-party material: library and
outputs live outside `src/` and are git-ignored; no audio is committed as a test
fixture (tests use synthetic signals). Subprocess adapters (fluidsynth, MuseScore,
basic-pitch) receive argument lists (never `shell=True`) and validated paths.

## Compliance

- [x] Hexagonal Architecture layers respected (domain → application ports → infra)
- [x] No framework dependencies in Domain layer (numpy/scipy math only; no pyworld,
      soundfile, pretty_midi in domain)
- [x] Value Objects for all business concepts (Hertz, Semitones, VocalTractScale, Vowel…)
- [x] Entities enforce invariants at construction (`ParametricVoice` shape/range checks)
- [x] Domain ≠ persistence (npz cache DTO lives in infrastructure)
- [x] Test strategy defined (synthetic-signal oracles, hermetic unit tests, marked
      integration tests for pyworld/fluidsynth/MuseScore)
- [x] Observability plan included
- [x] LGPD/Security assessed
- [ ] Ubiquitous Language terms added to `docs/GLOSSARY.md` (draft present, pending approval)
- [x] Alternatives documented
- [x] Cross-Context State Strategy complete

## References

- Related ADRs: future ADR-002 (strangle legacy `stem_separation`), ADR-003 (lossless
  WAV stems from Demucs)
- Spikes: `sandbox/spike-001-world-roundtrip/`, `sandbox/spike-002-basic-pitch-deps/`
- Specs: `docs/specs/SPEC-001-source-filter-vocal-pipeline.md`
- Morise, Yokomori, Ozawa (2016), *WORLD: a vocoder-based high-quality speech synthesis
  system for real-time applications*, IEICE.
- Peterson & Barney (1952); Hillenbrand et al. (1995) — vowel formant references.
