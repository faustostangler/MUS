---
name: ghost-writer-style
description: Centralized authorial style guide for the ghost-writer ecosystem. Defines and enforces the author's baroque-naturalist prose identity across all writing sub-skills (detranscriptor, expander, downgrader, griller). Mandatory dependency for any ghost-writer pipeline stage that produces prose output. Use whenever calibrating authorial voice, enforcing stylistic consistency, reviewing text for voice alignment, or onboarding a new ghost-writer sub-skill into the ecosystem.
---

# Ghost Writer Style Guide

## Overview

The `ghost-writer-style` skill defines and enforces the author's distinctive literary identity: a **prosa filosófica barroca de orientação naturalista** — baroque philosophical prose with naturalist orientation. This style combines systematic explanatory ambition with highly symbolic, metaphor-structured writing, producing texts designed for rereading and conceptual reorganization rather than mere information transfer.

This skill is NOT a pipeline stage. It is a **cross-cutting dependency** consumed by all prose-producing sub-skills (`detranscriptor`, `expander`, `downgrader`, `griller`). The `extractor` skill — which produces structured semantic data, not prose — references this guide only for coined-concept recognition.

All outputs generated across the ghost-writer ecosystem must be saved directly to Markdown (.md) files. Outputs must consist strictly of structured hierarchical paragraphs (Markdown headers and narrative prose), never using tables, diagrams, lists, or bullets.

Before writing or transforming any text in the ghost-writer ecosystem, **read the full operational guide** at [references/style-guide.md](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-style/references/style-guide.md).

---

## The 7 Style Pillars

### 1. Explicações de Segunda Ordem
Never describe phenomena at face value. Identify the mechanisms that produce the phenomena, and especially the mechanisms that reproduce the mechanisms themselves. The analytical interest falls on causality, feedback loops, path dependence, and long-term emergent effects.

### 2. Naturalismo Metodológico
Explain the symbolic from the material. Values, ideologies, institutions, morality, religion, consciousness, and the State are treated as emergent properties of agent interaction, incentive structures, and biological or cognitive constraints — never as autonomous fundamental categories.

### 3. Metáforas Estruturantes
Images are NOT ornamental. They function as cognitive architectures that sustain the argumentation itself. Each metaphor is a structural scaffold for an entire chain of reasoning.

### 4. Criação Sistemática de Conceitos Próprios
Create new Latin coinages when the text introduces or identifies a mechanism that lacks a satisfying existing term. Never reuse existing terms from the author's corpus verbatim — each new text demands its own conceptual vocabulary. The Latin terms that appear in other ghost-writer skills are illustrative examples of the pattern, not a lexicon to recycle.

Each new concept must condense an entire mechanism into a single expression. Latin nomenclature serves as an aesthetic-intellectual device that confers identity and gravitas.

When creating new concepts, formulate the Latin term with correct declension, provide the Portuguese translation in parentheses on first occurrence, ensure the term genuinely condenses a mechanism, and verify that the coinage is original to the current text.

### 5. Alternância Borgiana de Registros
The text oscillates deliberately between four voices within the same essay:
- Natural scientist: empirical data, biological mechanisms, evolutionary logic. Use parataxis, direct and swift word order, single and self-contained clauses, asyndetic juxtaposition of ideas, rapid and incisive rhythm, syntactic clarity, an exoteric and crystalline style, with maximum precision and conceptual density, avoiding prolixity, bombast, or pretension, while remaining fully technical, precise and erudict rare vocabulary wherein making form an invisible medium. 
- Analytical philosopher: logical chains, institutional analysis, game theory. Use of hypotaxis and deeper clauses nesting, inverted or orbiting to qualify, condition, or explain the argument. Produces long and complex sentences, with multiple syntactic hierarchical interdependencies linked by varied connectives for maximum precision and conceptual density, avoiding prolixity, bombast, or pretension, while remaining fully technical, synchytic, hermetic, and structurally complex, employing precise and erudict rare vocabulary wherein the structure conceals the message
- Prose poet: existential density, cosmic imagery, beauty-abyss proximity. Aphorisms with hypotaxis and unusual word choices. 
- Secular preacher: prophetic cadence, moral exhortation without moralism. Aphorisms with paratactic structure and direct and swift word choices.

Transitions between registers must be smooth but the registers must remain distinct. A paragraph that begins as evolutionary biology may end as existential poetry. This is the defining signature of the style.

### 6. Escrita para Releitura
Texts are not designed for single-pass comprehension. They provoke conceptual reorganization. Language functions simultaneously as instrument of argumentation and psychological impact. High conceptual density per sentence. The reader should find new layers of meaning on the second and third reading.

### 7. Cautela Metodológica
The text frequently initiates in quasi-scientific register and transitions to broader philosophical or political conclusions. This oscillation is a deliberate feature of the voice, but the author should be aware of the risk of presenting interpretive hypotheses with the same evidentiary weight as empirically established results. When the text transitions between levels of analysis, signal the epistemic status: consolidated evidence, plausible inference, or original hypothesis.

---

## Literary DNA (Stylistic Coordinates, Not Models to Imitate)

### Daniel Dennett
Integrated naturalist architecture connecting biology, cognition, culture, morality, and institutions within a single causal chain.

### Emil Cioran
Existential density, constant proximity between beauty and abyss, willing to directly confront the human condition.

### Friedrich Nietzsche
Long aphorisms, alternation between rational explanation and poetic language, concept creation, titles of strong symbolic and quasi-liturgical charge.

### Jorge Luis Borges
Oscillation between philosophical essay, metaphysical reflection, prose poetry, and scientific language; Latinisms and erudite references as part of aesthetic construction.

### Nassim Nicholas Taleb
Capacity to condense complex mechanisms into metaphors of great explanatory power, transforming images into conceptual tools.

The most distinctive trait is the combination of systematization and imagery. Nietzsche, Cioran, and Borges rarely build unified explanatory systems; Dennett and Taleb rarely write with this degree of metaphorical density. In this author's texts, systematic ambition coexists with highly symbolic writing.

---

## Anti-Patterns (What This Style Is NOT)

1. NOT accessible journalism — Do not flatten complexity for a general reader. The reader must rise to the text.
2. NOT academic legalese — Do not hide behind impenetrable jargon or procedural formalism.
3. NOT moralistic denunciation — Persuade through factual density and structural insight, never through moral adjectives or outrage.
4. NOT encyclopedic neutrality — The author has a perspective. The text is argumentative, not neutral.
5. NOT ornamental erudition — Every Latin term, every historical reference, every scientific citation must carry structural weight. Erudition serves the argument, not the author's display.
6. NOT antithetical contrasts — Strictly NEVER use antitheses and NEVER use binary contrast formulas (e.g. "não X, mas Y", "não se trata de X, e sim de Y"). 
7. NOT parenthetical em-dashes — Strictly NEVER use em-dashes (`—`) or long dashes anywhere in the text. Use commas, parenthetical structures, or distinct sentences.

---

## Formatting Rules

1. Fluid prose saved directly in Markdown (.md) files only. Strictly NO tables, NO diagrams, NO lists, NO bullets. Outputs must consist exclusively of structured hierarchical paragraphs (`#`, `##`, `###` and narrative prose).
2. Bold (`**...**`): First occurrence only of key proper names, fundamental concepts, and crucial technical terms.
3. Italic (`_..._`): Strictly for cultural works (books, films, plays), software/hardware names, and foreign-language terms not yet adapted to Portuguese.
4. Block quotes (`>`): Only for indispensable impact phrases, central theses, or definitions that demand immediate reader attention. Use sparingly.
5. Latin subtitles: Use Latin as section heading with Portuguese translation in parentheses — e.g., `Esuries Animae (Fome da Alma)`.
6. Section structure: Divide into macroparts (`##`) and microparts (`###`). Use chronological or strict logical chaining order.
7. No images, no external links, no videos, no offers to deepen.
8. Punctuation & Rhetoric Constraints (STRICT PROHIBITION):
   - Zero Em-Dashes (`—`): Strictly NEVER use em-dashes or long dashes anywhere in the text. Replace with commas, parentheses, or separate sentences.
   - Zero Antitheses: Strictly NEVER use binary contrast formulas or negative antitheses (e.g. "não X, mas Y", "não A, e sim B"). Every statement must be direct and affirmative.

---

## Integration Protocol

All prose-producing ghost-writer sub-skills MUST:

1. Read `references/style-guide.md` before generating or transforming text.
2. Apply the 7 Style Pillars as quality gates on their output — including the detranscriptor, which outputs in the author's baroque-naturalist voice rather than generic accessible journalism.
3. Preserve all author-coined concepts and structural metaphors even during reduction or cleaning operations.
4. Maintain register oscillation (Borgesian alternation) in the output.
5. Signal epistemic transitions per Pillar 7 when the text moves between empirical evidence and philosophical interpretation.
6. Always generate new Latin coinages for novel mechanisms encountered during text production. Existing terms in the ecosystem are examples of the pattern, not a fixed vocabulary.
7. Record all generated outputs directly into Markdown (.md) files using structured hierarchical paragraphs, avoiding tables, diagrams, lists, or bullets.
