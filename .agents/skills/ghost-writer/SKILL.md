---
name: ghost-writer
description: Master orchestrator skill for ghost-writing, text transformation, deep knowledge extraction, article production, and stylistic editing. Coordinates the ghost-writer family (ghost-writer-griller, ghost-writer-detranscriptor, ghost-writer-expander, ghost-writer-downgrader, ghost-writer-extractor) and the styler subskills suite (ghost-writer-styler-lapidador, ghost-writer-styler-cartunista, ghost-writer-styler-flechada, ghost-writer-styler-flechadinha, ghost-writer-styler-frasista, ghost-writer-styler-jurista). Use whenever the user requests complex text processing, transcript conversion, narrative expansion, text editing, lexical polishing, legal auditing, or full-cycle article generation.
---

# Ghost Writer Master Orchestrator

## Overview

The `ghost-writer` master skill orchestrates and coordinates the specialized sub-skills in the Ghost Writer ecosystem. It manages the complete lifecycle of text processing—from initial idea grilling and raw transcript detranscription to factual expansion, structural downgrading/de-bloating, lexical polishing, visual cartooning, legal shielding, and semantic knowledge graph extraction.

All outputs generated across all pipeline stages must be saved directly to Markdown (.md) files. Outputs must consist strictly of structured hierarchical paragraphs (Markdown headers and narrative prose), never using tables, diagrams, lists, or bullets.

---

## Ecosystem Sub-Skills Registry

### Core Pipeline Sub-Skills

#### ghost-writer-griller
Socratic interactive interview to extract deep intent, stress-test assumptions, and fill conceptual gaps. Reads raw idea or user prompt, outputting clarified concept and semantic graph directly to a Markdown file.
Target Skill File: [`ghost-writer-griller`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-griller/SKILL.md)

#### ghost-writer-detranscriptor
Purges speech noise, oralities, hesitations, and first-person dialogue from raw transcripts; fact-checks names and dates. Reads raw audio transcript or notes, outputting structured Markdown directly to a Markdown file.
Target Skill File: [`ghost-writer-detranscriptor`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-detranscriptor/SKILL.md)

#### ghost-writer-expander
Two-pass Socratic and historical audit to enrich text with real-world statistics, historical context, and persuasive journalistic tone. Reads draft text or article, outputting factually expanded Markdown directly to a Markdown file.
Target Skill File: [`ghost-writer-expander`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-expander/SKILL.md)

#### ghost-writer-downgrader
De-bloats text, removes substrate-independent micro-details, and delegates secondary/biographical details to numbered footnotes. Reads dense or overwritten text, outputting streamlined Markdown with footnotes directly to a Markdown file.
Target Skill File: [`ghost-writer-downgrader`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-downgrader/SKILL.md)

#### ghost-writer-extractor
Extracts semantic knowledge graph constructs (NER, Concepts, Timelines, Triples, Processes, Causal Logic) into natural language sentences. Reads cleaned article or text, outputting standardized semantic graph directly to a Markdown file.
Target Skill File: [`ghost-writer-extractor`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-extractor/SKILL.md)

#### ghost-writer-style
Cross-cutting dependency. Centralized authorial style guide defining the baroque-naturalist prose identity. Not a pipeline stage. Provides style directives for all prose-producing stages.
Target Skill File: [`ghost-writer-style`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-style/SKILL.md)

---

### Styler Sub-Skills Suite

#### ghost-writer-styler-lapidador
Advanced stylistic editor and copyeditor. Evaluates text word-by-word/expression-by-expression, replacing common vocabulary with precise technical terms from Law, Philosophy, and Medicine, controlling rhythm and cadence.
Target Skill File: [`ghost-writer-styler-lapidador`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-styler-lapidador/SKILL.md)

#### ghost-writer-styler-cartunista
Visual editorial strategist. Conceptualizes image prompts and layouts using "Bureaucratic Realism" and "Modernist Editorial Collage" to illustrate political and institutional articles.
Target Skill File: [`ghost-writer-styler-cartunista`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-styler-cartunista/SKILL.md)

#### ghost-writer-styler-flechada
Investigative libertarian journalist persona ("O Jornalista Libertário Pontudo"). Drafts sharp, theoretical, high-conviction critiques that dissect power relations without meta-explanations.
Target Skill File: [`ghost-writer-styler-flechada`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-styler-flechada/SKILL.md)

#### ghost-writer-styler-flechadinha
Persuasive non-confrontational journalist persona ("O Jornalista Libertário Rombo"). Plants seeds of doubt about state power for moderate/center-left readers using subtle irony and unpretentious prose.
Target Skill File: [`ghost-writer-styler-flechadinha`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-styler-flechadinha/SKILL.md)

#### ghost-writer-styler-frasista
Viral quote extractor ("O Frasista Impossível"). Extracts concise, visual, and corrosive social media quotes categorized into frases-imagem, inversão moral, frases-cicatriz, and aparentemente neutras.
Target Skill File: [`ghost-writer-styler-frasista`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-styler-frasista/SKILL.md)

#### ghost-writer-styler-jurista
Legal auditor and shield ("O Jurista Protetor"). Audits texts for defamation/libel risks, replacing ad hominem with ad methodum attacks and ensuring complete legal and constitutional compliance.
Target Skill File: [`ghost-writer-styler-jurista`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-styler-jurista/SKILL.md)

---

## Orchestration Pipelines & Execution Modes

`ghost-writer` evaluates the user's intent and executes one of the following orchestration modes:

### Full Pre-configured Pipeline (5-Stage Master Flow)
Sequence execution follows: ghost-writer-griller -> ghost-writer-detranscriptor -> ghost-writer-expander -> ghost-writer-downgrader -> ghost-writer-extractor. Optionally chained with `ghost-writer-styler-lapidador` and `ghost-writer-styler-jurista` for final polishing and legal auditing.

### Transcript-to-Article Pipeline
Sequence execution follows: ghost-writer-detranscriptor -> ghost-writer-expander -> ghost-writer-downgrader.

### Concept-to-Graph Pipeline
Sequence execution follows: ghost-writer-griller -> ghost-writer-extractor.

### Direct Sub-Skill Routing
Use case applies when the user explicitly requests a single isolated task, such as polishing vocabulary via `ghost-writer-styler-lapidador`, auditing legal risks via `ghost-writer-styler-jurista`, generating editorial cartoons via `ghost-writer-styler-cartunista`, or extracting social media quotes via `ghost-writer-styler-frasista`.

---

## Inter-Skill Data Contracts & Anti-Corruption Layer (ACL)

When chaining sub-skills in multi-stage pipelines, `ghost-writer` enforces the following data transfer rules:

### Direct File Reading and Writing
Sub-skills write their processed output directly to designated Markdown (.md) files. Downstream pipeline stages read directly from the Markdown file written by the preceding stage.

### Footnote Preservation
Expander and downgrader populate numbered footnotes at the end of the text payload. `ghost-writer` ensures that footnote indices and text anchors remain intact across pipeline transitions.

### Output Formatting Compliance
All sub-skills MUST output exclusively in structured hierarchical paragraphs (Markdown headings and narrative prose). Tables, diagrams, lists, and bullets are strictly forbidden in all output files.

### Authorial Style Consistency
All prose-producing stages MUST apply the `ghost-writer-style` reference guide.

---

## File Storage & Workspace Structure

All generated outputs, intermediate pipeline stage files, final polished articles, and extracted semantic knowledge graphs MUST be persisted locally in Markdown (.md) files under individualized folders for each text/article:

Base Path: `playground/ghost-writer/<article_slug>/`
Stage 1 Output File: `01_griller_brief.md`
Stage 2 Output File: `02_detranscribed.md`
Stage 3 Output File: `03_expanded.md`
Stage 4 Output File: `04_final_article.md`
Stage 5 Output File: `05_semantic_graph.md`
Style Guidelines File: `writer-guidelines.md`

---

## Operational Execution Protocol

First, analyze the user request to determine whether the user needs a full 5-stage pipeline, a specialized sub-pipeline, or a single sub-skill execution.
Second, load the authorial style guide from `ghost-writer-style/references/style-guide.md` and pass its directives as context to all prose-producing pipeline stages.
Third, initialize the workspace by creating `playground/ghost-writer/<article_slug>/` for the target topic.
Fourth, execute Stage 1 by invoking the target initial skill with the user's input and style guide context, saving the result to its corresponding Markdown (.md) file.
Fifth, propagate and persist payloads sequentially by executing remaining pipeline stages, reading from and writing to their respective Markdown (.md) files in `playground/ghost-writer/<article_slug>/`.
Sixth, present final delivery confirmation in clean Markdown, providing the exact file paths saved in `playground/ghost-writer/<article_slug>/`.
