# MUS Phoneme, Formant & Melodic Score Lab (Spike-002)

Interactive acoustic lab for calibrating and auditioning formants (F1, F2, F3) for the 7 Portuguese cardinal vowels across 4 vocal registers, plus consonant articulation (plosives, fricatives, nasals, liquids) and **Melodic Score Solfeggio Sequencing (Vocalise Route 4B)** for the MUS vocal pipeline.

---

## 1. Quick Start

### A. Web Application (`index.html`)
Open [`index.html`](file:///home/stangler/Documents/Python/MUS/sandbox/phoneme_synth/index.html) directly in any modern browser:
```bash
# Option 1: Open directly
xdg-open sandbox/phoneme_synth/index.html

# Option 2: Run local HTTP server
python3 -m http.server 8080 --directory sandbox/phoneme_synth/
# Browse to http://localhost:8080
```

#### Dual-Tab Interface:
1. **🎙️ Tab 1: Trato Vocal & Cantor (Formant Tuning)**:
   - **Voice Classification Presets**: Baixo/Barítono, Tenor, Contralto/Mezzo, Soprano.
   - **Formant Resonators (Klatt Parallel Architecture)**: Independent tuning of F1, F2, F3 and bandwidths B1, B2, B3 with boosted F2 clarity.
   - **F0 Carrier Body Slider**: Balance between pure formant resonances (0%) and natural fundamental bleed.
   - **Solo Formants**: Isolate F1 (jaw/throat), F2 (tongue/frontness), or F3 (tract/brilliance) individually.
   - **Interactive 2D Acoustic Vowel Chart**: Drag inside the IPA Vowel Trapezoid (`/i/ → /e/ → /ɛ/ → /a/ → /ɔ/ → /o/ → /u/`) with real-time audio morphing and similarity matching.
2. **🎼 Tab 2: Partitura & Solfejo (Melodic Score Sequencer)**:
   - **Melodic Roll**: Add, edit, reorder, or delete notes and syllables.
   - **Parameters per Note**: Pitch (C2–C5), Rhythmic Duration (𝅝 Semibreve, 𝅗𝅥 Mínima, 𝅘𝅥 Semínima, 𝅘𝅥𝅮 Colcheia, 𝅘𝅥𝅯 Semicolcheia), and Syllable/Vowel (e.g. `/a/`, `/e/`, `/dó/`, `/ré/`, `/mi/`).
   - **Tempo BPM**: 40 to 240 BPM.
   - **Interactive Piano Note Insertion**: Toggle "🎹 Inserir notas clicando no piano" to compose by clicking keys!
   - **Real-Time Playhead Tracking**: Visual animated pulse highlighting each note in sync with audio.
   - **WAV Export da Melodia**: Download the complete sung melody as an uncompressed 16-bit 44.1 kHz `.wav` file.

---

### B. Python CLI Synthesizer (`phoneme_synth.py`)

```bash
# 1. Melodic Score Synthesis: Dó-Ré-Mi em colcheia (0.25s cada a 120 BPM) com solfejo 'a-a-a':
uv run python sandbox/phoneme_synth/phoneme_synth.py --score "C4:0.25:a,D4:0.25:a,E4:0.25:a" --voice tenor --out sandbox/phoneme_synth/out/doremi_colcheia.wav

# 2. Solfeggio with articulated syllables (Dó-Ré-Mi-Fá-Sol):
uv run python sandbox/phoneme_synth/phoneme_synth.py --score "C4:0.25:o:d,D4:0.25:e:r,E4:0.25:i:m,F4:0.25:a:f,G4:0.5:o:s" --voice tenor --out sandbox/phoneme_synth/out/solfejo_doremifasol.wav

# 3. Single Vowel Synthesis:
uv run python sandbox/phoneme_synth/phoneme_synth.py --vowel a --voice tenor --note A3 --duration 1.0

# 4. Batch Demonstration (Generates all 28 vowel-voice combinations and sample syllables):
uv run python sandbox/phoneme_synth/phoneme_synth.py --batch-demo
```

Generated `.wav` files are saved to [`sandbox/phoneme_synth/out/`](file:///home/stangler/Documents/Python/MUS/sandbox/phoneme_synth/out/).

---

## 2. Directory Layout

```text
sandbox/phoneme_synth/
├── index.html            # Standalone Dual-Tab Web Audio GUI (Formant Lab + Score Sequencer)
├── phoneme_synth.py      # Standalone Python CLI generator with score & syllable synthesis
├── presets.json          # Machine-readable JSON matrix of all vowels and consonants
├── README.md             # Documentation and usage guide
└── out/                  # Synthesized WAV files output directory
```
