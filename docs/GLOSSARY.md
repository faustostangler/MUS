# Glossary — Ubiquitous Language (MUS)

> Status: Draft (pending approval together with ADR-001).

| Term | Context | Definition | Code symbol |
|---|---|---|---|
| **Stem** | stem_catalog | One source-separated track (vocals, drums, bass, other, guitar, piano) produced by HTDemucs. | — |
| **Vocal Stem** | stem_catalog | The `vocals` Stem of a track; input of the vocal pipeline. | `VocalStemRef` |
| **Take** | shared_kernel | One processing unit of a Vocal Stem identified by a content hash. | `TakeId` |
| **Audio Signal** | shared_kernel | Mono `float64` PCM samples + Sample Rate. | `AudioSignal` |
| **Sample Rate** | shared_kernel | Samples per second; allowed: 44 100 or 48 000 Hz. | `SampleRate` |
| **Frame Period** | shared_kernel | Hop between analysis frames; fixed 5.0 ms. | `FramePeriod` |
| **Pitch Contour (F0)** | shared_kernel | Per-frame fundamental frequency in Hz; 0 = unvoiced. The "source". | `PitchContour` |
| **Voiced Frame** | shared_kernel | Frame with F0 > 0 (vocal folds vibrating). | — |
| **Spectral Envelope (SP)** | voice_modeling | Per-frame smoothed power spectrum of the vocal tract, free of source harmonics. The "filter". | `SpectralEnvelope` |
| **Aperiodicity (AP)** | voice_modeling | Per-frame, per-bin ratio [0,1] of noise vs periodic energy (breath, fricatives). | `Aperiodicity` |
| **Parametric Voice** | voice_modeling | Aggregate (PitchContour, SpectralEnvelope, Aperiodicity, SampleRate, FramePeriod) with aligned frames. | `ParametricVoice` |
| **Decomposition** | voice_modeling | Audio Signal → Parametric Voice (WORLD analysis). | `DecomposeVoice` |
| **Resynthesis** | voice_modeling | Parametric Voice → Audio Signal (WORLD synthesis). | `ResynthesizeVoice` |
| **Round-Trip Fidelity** | voice_modeling | Agreement between a Take and its unmodified Resynthesis (F0 RMSE in cents, MCD in dB). | `RoundTripReport` |
| **Pitch Modulation** | voice_modeling | Any transformation of the Pitch Contour only (transpose, phrase-end ramp, vibrato control). | `PitchModulation` |
| **Semitone Shift** | shared_kernel | Signed pitch interval; F0 × 2^(n/12). | `Semitones` |
| **Formant** | voice_modeling | Resonance peak of the vocal tract (F1, F2, F3…). | `Formant` |
| **Formant Target** | voice_modeling | Desired (F1, F2, F3) for a Vowel at a Voice Category. | `FormantTarget` |
| **Cardinal Vowel** | voice_modeling | One of /a/, /e/, /i/, /o/, /u/ with reference formants. | `Vowel` |
| **Vowel Table** | voice_modeling | Reference Formant Targets per Cardinal Vowel at α = 1.0 (adult male baseline). | `VOWEL_TABLE` |
| **Vocal Tract Scale (α)** | voice_modeling | Scalar frequency dilation of the Spectral Envelope modeling tract length (bass ≈ 0.88, tenor 1.00, soprano ≈ 1.18). | `VocalTractScale` |
| **Voice Category** | voice_modeling | Named preset of α (bass, baritone, tenor, alto, mezzo, soprano). | `VoiceCategory` |
| **Vowel Window** | voice_modeling | Time span where a vowel substitution applies, with crossfade edges. | `VowelWindow` |
| **Spectral Warping** | voice_modeling | Piecewise-linear remap of the SP frequency axis moving formants to targets. | `warp_envelope` |
| **Envelope Overwrite** | voice_modeling | Replacement of SP by a synthetic all-pole response built from a Formant Target. | `overwrite_envelope` |
| **Vocalise** | voice_modeling | Singing without lyrics on assigned vowels, synthesized from a Note Sequence (Route 4B). | `SingVocalise` |
| **Note Event** | shared_kernel | Discrete note: MIDI pitch, onset, offset, velocity, optional pitch-bend curve. | `NoteEvent` |
| **Note Sequence** | shared_kernel | Time-ordered, non-overlapping (monophonic) Note Events + tempo. | `NoteSequence` |
| **MIDI Pitch** | shared_kernel | Integer 0–127; `69 + 12·log2(F0/440)`. | `MidiPitch` |
| **Hysteresis Segmentation** | music_transcription | Grouping of voiced frames into Note Events; a new note starts only when deviation exceeds a cents threshold for a minimum duration. | `HysteresisSegmenter` |
| **Tempo Grid** | music_transcription | Beat-aligned quantization grid (BPM + subdivision) used for score-friendly onsets. | `TempoGrid` |
| **Transcription Track A / B** | music_transcription | A = analytic from Pitch Contour; B = neural (basic-pitch). | `TranscriptionTrack` |
| **Render Route** | instrument_rendering | 4A = Note Sequence → acoustic instrument (SoundFont); 4B = Note Sequence → Vocalise. | — |
| **GM Program** | instrument_rendering | General MIDI instrument number 0–127 (0 = Acoustic Grand Piano, 42 = Cello). | `GmProgram` |
| **Analysis Segment** | voice_modeling | Silence-delimited chunk processed independently to bound memory. | `AnalysisSegment` |
