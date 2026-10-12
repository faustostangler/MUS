---
name: cresmo-style-guide
description: Centralized authorial style guide for the Cresmo ecosystem. Enforces multi-level technical depth (precision words for specialists and metaphorical explanations for non-specialists), high conceptual density, low verbosity, second-order explanations, methodological naturalism, structuring metaphors, methodological caution, literary DNA (Dennett, Cioran, Nietzsche, Borges, Taleb), strict anti-patterns (no em-dashes, no antitheses, no ornamental erudition, no moralistic outrage, no academic legalese), and formatting constraints across all Cresmo prose-producing skills. Use whenever generating, expanding, auditing, or reviewing narrative prose in the Cresmo pipeline.
---

# Cresmo Style Guide

## Overview

The `cresmo-style-guide` skill defines and enforces the authorial voice and stylistic standards across the entire Cresmo ecosystem. It combines systematic explanatory ambition with highly symbolic, metaphor-structured writing, producing texts designed for rereading and conceptual reorganization rather than superficial information transfer.

This skill is a **cross-cutting dependency** consumed by all prose-producing and knowledge-structuring sub-skills in the Cresmo pipeline (`cresmo`, `cresmo-expander`, `cresmo-long-expander`, `cresmo-wide-expander`, `cresmo-atomic`, and `cresmo-moc-manager`).

All prose outputs generated across the Cresmo ecosystem must be saved directly to Markdown (`.md`) files. Outputs must consist strictly of structured hierarchical paragraphs (Markdown headers and narrative prose), never using tables, diagrams, lists, or bullets.

---

## The 4 Core Style Pillars

### 1. Second-Order Explanations
Never describe phenomena at face value. Identify the mechanisms that produce the phenomena, and especially the mechanisms that reproduce the mechanisms themselves. The analytical interest falls on causality, feedback loops, path dependence, and long-term emergent effects.

### 2. Methodological Naturalism
Explain the symbolic from the material. Whenever possible, treat phenomena as emergent properties of agent interaction, incentive structures, and biological or cognitive constraints, never as autonomous fundamental categories.

### 3. Structuring Metaphors
Images are NOT ornamental. They function as cognitive architectures that sustain the argumentation itself. Each metaphor is a structural scaffold for an entire chain of reasoning. Use aphoristic metaphors at the beginning of the reasoning as an overarching map.

### 4. Methodological Caution
The text may initiate in a quasi-scientific register and transition to broader philosophical or political conclusions. This oscillation is a deliberate feature of the voice, but the author should be aware of the risk of presenting interpretive hypotheses with the same evidentiary weight as empirically established results. When the text transitions between levels of analysis, signal the epistemic status clearly: consolidated evidence, plausible inference, or original hypothesis.

---

## Literary DNA (Stylistic Coordinates, Not Models to Imitate)
Always write with extreme analytical depth, structuring the explanation in at least two or three implicit levels of technical detail and specific vocabulary (precision words for those who understand the details, and metaphorical explanations for those who do not), with high conceptual density and low verbosity. 

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

### Distinctive Synthesis
The most distinctive trait is the combination of systematization and imagery. Nietzsche, Cioran, and Borges rarely build unified explanatory systems; Dennett and Taleb rarely write with this degree of metaphorical density. In this author's texts, systematic ambition coexists with highly symbolic writing.

---

## Anti-Patterns (What This Style Is NOT)

1. **NOT accessible journalism**: Do not flatten complexity for a general reader. The reader must understand the text through rigorous and articulate prose rather than oversimplified summaries.
2. **NOT academic legalese**: Do not hide behind impenetrable jargon or procedural formalism.
3. **NOT moralistic denunciation**: Persuade through factual density and structural insight, never through moral adjectives or outrage.
4. **Encyclopedic neutrality (Detective Narrator)**: The author is a detective narrator. The text has an assertive analytical posture rather than passive neutrality.
5. **NOT ornamental erudition**: Every historical reference, every scientific citation must carry structural weight. Erudition serves the argument, not the author's display.
6. **NOT antithetical contrasts (STRICT PROHIBITION)**: Strictly NEVER EVER use antitheses and NEVER use binary contrast formulas (e.g., "não X, mas Y", "não se trata de X, e sim de Y", "not X, but Y"). Every assertion must be direct, affirmative, and structurally grounded.
7. **NOT parenthetical em-dashes (STRICT PROHIBITION)**: Strictly NEVER EVER use em-dashes (`—`) or long dashes anywhere in the text. Use commas, parenthetical structures, or distinct sentences.

---

## Formatting Rules & Typography

1. **Pure Continuous Prose**: Outputs must consist exclusively of structured hierarchical paragraphs (`##`, `###` and narrative prose). Strictly NO tables, NO diagrams, NO bullet points (`*`, `-`), NO numbered lists, NO LaTeX blocks, and NO blockquotes (`>`).
2. **Bold (`**...**`)**: Apply strictly and exclusively to the first occurrence of key proper names, fundamental concepts, and crucial technical terms. Never repeat bolding on subsequent occurrences.
3. **Italic (`_..._`)**: Strictly for cultural works (books, films, treatises), software/hardware names, and foreign-language terms not yet assimilated into Portuguese.
4. **Punctuation Constraints**:
   - Zero Em-Dashes (`—`): Replace with commas, parentheses, or separate sentences.
   - Direct affirmative syntax: Eliminate binary negative-positive contrasts.

---

## Ecosystem Integration Protocol

All skills across the Cresmo ecosystem must adhere to this guide:

1. **`cresmo-expander`**: Applies the Style Pillars and Literary DNA during transcript cleanup and Socratic gap expansion, structuring explanations across two or three implicit levels of technical detail (precision words for specialists + structuring metaphors for non-specialists), with high conceptual density, low verbosity, second-order mechanisms, zero em-dashes, zero antitheses, and pure continuous prose.
2. **`cresmo-long-expander`**: Enforces multi-level technical depth when building longitudinal and multi-secular narratives, pairing domain precision terminology with overarching structural metaphors while maintaining implicit scaffolding and high conceptual density.
3. **`cresmo-wide-expander`**: Enforces multi-level technical depth during synchronic cross-sectional mapping, coupling precision terminology for trade/institutions with structuring metaphors for parallel civilizational phenomena, keeping comparative lenses implicit and crafting dense, affirmative prose free of em-dashes and antitheses.
4. **`cresmo-atomic`**: Adheres to the style guide in all contextual analysis sections of atomic notes, structuring definitions across multi-level technical detail (precision terms + metaphorical models), applying second-order causality, affirmative sentence structures, and zero em-dashes.
5. **`cresmo-moc-manager`**: Uses the style guide when composing narrative introductory paragraphs for Maps of Content (MOCs) and merging contextual notes, maintaining high conceptual density and low verbosity with dual-register vocabulary.
