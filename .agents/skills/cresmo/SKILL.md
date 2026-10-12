---
name: cresmo
description: Master orchestrator skill for processing raw transcripts, lecture notes, and draft texts into rich, interlinked atomic Obsidian notes and managing Maps of Content (MOCs). Coordinates the Cresmo family pipeline (cresmo-fluid-prose, cresmo-gap-filler, cresmo-long-expander, cresmo-wide-expander, cresmo-atomic, cresmo-moc-manager). Use whenever the user requests full-cycle transcript processing, speech detranscription, gap expansion, atomic note generation, Obsidian Second Brain vault integration, WikiLink mapping, or MOC management. Make sure to use this skill whenever the user mentions transcripts, audio transcriptions, atomic notes, Obsidian vaults, WikiLinks, or MOCs, even if they do not explicitly mention "cresmo".
---

# Cresmo Master Orchestrator

## Overview

The `cresmo` master skill orchestrates and coordinates the specialized sub-skills in the Cresmo ecosystem. It manages the complete end-to-end lifecycle of knowledge extraction from raw audio/speech transcripts—starting from Socratic gap expansion and diagram suppression, proceeding to atomic note extraction with Obsidian WikiLinks, and concluding with vault entity reconciliation and Map of Content (MOC) narrative integration.

### Input Specification & YAML Metadata Protocol

Input transcripts are supplied with a standardized YouTube YAML frontmatter header, as this example:

```yaml
---
video_title: [video_title]
video_id: [video_id]
channel_name: [channel_name]
channel_id: [channel_id]
channel_category: [channel_category]
url: [url]
video_date: [video_date]
video_description: description of video
---
[Raw transcript content follows]
```

**`video_id` & `channel_name` Extraction Rule**: The `video_id` (e.g., `eYFTRQHaPgw`) and `channel_name` extracted from the input YAML frontmatter govern the directory topology across all pipeline stages.

All pipeline artifacts are systematically stored under:
- `playground/cresmo/raw/<channel_name>/<video_id>.txt` (Stage 1)
- `playground/cresmo/enriched/<channel_name>/<video_id>.md` (Stage 2 & Stage 2.5)
- `playground/cresmo/enriched/<channel_name>/<video_id>.json` (Stage 3)
- `playground/cresmo/wiki/<note_type>/[Exact Note Title].md` and `_index.json` (Stage 4)
- `playground/cresmo/wiki/MOCs/MOC_*.md` (Stage 5)
- `playground/cresmo/enriched/<channel_name>/<video_id>_reconciliation.md` (Stage 6)
- `playground/cresmo/processed_cresmo.json` (Pipeline tracking log)

---

## Ecosystem Sub-Skills Registry

### Core Pipeline Sub-Skills

#### cresmo-fluid-prose
Purges speech noise, oralities, hesitations, verbal crutches, direct audience interactions, diagrams, tables, formulas, and bullet lists. Conducts fact-checking and Named Entity (NER) normalization, producing continuous fluid Markdown prose in third-person neutral narrative without conversational noise. Executed during Stage 1 (`fluid_prose`) before conceptual indexing.
Target Skill File: [`cresmo-fluid-prose`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-fluid-prose/SKILL.md)

#### cresmo-gap-filler
Conducts Socratic gap audit across 6 Epistemic Dimensions, causal stratification (structural, conjunctural, triggers), precursor tracking, and multi-pass epistemic densification on fluid prose transcripts. Constructs and enriches the mandatory `## Informações Complementares` section with numbered continuous paragraphs for secondary lineages, biographies, and granular data. Executed during Stage 3 (`gap_filler`).
Target Skill File: [`cresmo-gap-filler`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-gap-filler/SKILL.md)

#### cresmo-long-expander
Deep longitudinal expander grounded in the Annales School and Fernand Braudel's *longue durée*, performing multi-secular structural analysis and historical palimpsest deconstruction. Dissects causation across three tiers (first-order determinants, second-order structures, third-order opportunities) and plural temporalities, employing Reversed Longue Durée to trace modern concepts back to foundational institutional, infrastructural, geopolitical, and cognitive strata.
Target Skill File: [`cresmo-long-expander`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-long-expander/SKILL.md)

#### cresmo-wide-expander
Synchronic horizontal expander specializing in Axial Time (*Achsenzeit* - Karl Jaspers), connected global history, and comparative civilizational cross-sections. Analyzes synchronous global moments across two modalities: Synchrony & Connectivity (events linked by global networks, trade flows, silver circuits, and planetary climatic shocks) and Parallelism & Analogy (independent societies responding similarly to common systemic pressures with zero or minimal contact).
Target Skill File: [`cresmo-wide-expander`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-wide-expander/SKILL.md)

#### cresmo-atomic
Transforms expanded fluid text into autonomous, semantically dense Atomic Notes formatted for an Obsidian Second Brain vault. Enforces strict typologies (`entity`, `concept`, `event`, `process`), Big-Endian event titles, YAML frontmatter, declarative triple connections, causal attribution matrices, and bi-directional WikiLinks, outputting a JSON array. Extracts `channel_name` and `video_id` from the source header to construct source tags `#fonte/[channel_name]/[video_id]`.
Target Skill File: [`cresmo-atomic`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-atomic/SKILL.md)

#### cresmo-moc-manager
Reconciles incoming JSON atomic notes with an active Obsidian Vault environment. Executes a 3-tier lookup protocol (`_index.json` -> Category MOCs -> Semantic audit), performs non-destructive incremental note merging, updates reciprocal back-links trans-textually, enforces tag governance (`#fonte/[channel_name]/[video_id]`), and integrates every note into narrative Maps of Content (MOCs) with zero orphaned notes.
Target Skill File: [`cresmo-moc-manager`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-moc-manager/SKILL.md)

### Cross-Cutting Style Dependency

#### cresmo-style-guide
Defines and enforces the centralized authorial voice across the entire Cresmo ecosystem: multi-level technical depth (structuring explanations across two or three implicit levels of detail with precision words for specialists and metaphorical explanations for non-specialists), high conceptual density, low verbosity, second-order explanations, methodological naturalism, structuring metaphors, methodological caution, literary DNA (Dennett, Cioran, Nietzsche, Borges, Taleb), and strict anti-patterns (zero em-dashes `—`, zero antitheses, zero lists or tables, and pure continuous prose). All sub-skills producing or editing prose must comply with its standards.
Target Skill File: [`cresmo-style-guide`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-style-guide/SKILL.md)

---

## Orchestration Pipelines & Execution Modes

`cresmo` analyzes the user request and selects one of the following execution pipelines:

### 1. Full Master Pipeline (Linear Stage Progression: fluid_prose -> raw_indexing -> gap_filler -> expansion -> inventory -> atomic_batch -> mocs -> dedup)
Executed when raw YouTube transcripts need full end-to-end processing into an Obsidian Vault via `cresmo run`.
Sequence: Ingestion -> `cresmo-fluid-prose` -> `raw_indexing` -> `cresmo-gap-filler` -> `cresmo-long-expander` & `cresmo-wide-expander` -> `cresmo-atomic` -> Proliferation -> `cresmo-moc-manager` -> `dedup`
- **Stage 1 (Raw Ingestion)**: Ingests YouTube audio/playlists to `playground/cresmo/raw/<channel_name>/<video_id>.txt` with YAML metadata.
- **Stage 1.5 (Fluid Prose - `cresmo-fluid-prose`)**: Purges speech noise, oralities, hesitations, verbal crutches, diagrams, tables, and bullet lists. Conducts fact-checking and NER normalization, producing continuous fluid Markdown prose (`FluidTranscript`).
- **Stage 2 (Catalog Indexing - `raw_indexing`)**: Extracts concise key concepts, summaries, and paratactic synthesis exclusively from the clean `FluidTranscript`, updating `_canal.md` and `brain.csv`. Standalone indexing of unnormalized raw files is strictly prohibited.
- **Stage 3 (Gap Filler & Socratic Audit - `cresmo-gap-filler`)**: Multi-pass Socratic gap audit across 6 Epistemic Dimensions, causal stratification (structural, conjunctural, triggers), and construction of the mandatory `## Informações Complementares` section into `playground/cresmo/enriched/<channel_name>/<video_id>.md`.
- **Stage 4 (Expander - Longitudinal & Synchronic Deep Expansion)**: In-place enrichment of `playground/cresmo/enriched/<channel_name>/<video_id>.md` via `cresmo-long-expander` (*longue durée* and structural palimpsests) followed by `cresmo-wide-expander` (Axial Time and synchronic connected history).
- **Stage 5 (Atomic Note Generation - `cresmo-atomic`)**: Scans expanded compendium and extracts candidate inventory and autonomous atomic note objects in `playground/cresmo/enriched/<channel_name>/<video_id>.json`.
- **Stage 6 (Proliferation & Indexing)**: Deterministically unpacks JSON into individual atomic `.md` files under `playground/cresmo/wiki/<note_type>/[Exact Note Title].md` and updates `playground/cresmo/wiki/_index.json`.
- **Stage 7 & 8 (MOC Management, Vault Graph Sync, & Duplicate Unification)**: Integrates notes into `playground/cresmo/wiki/MOCs/MOC_*.md`, enforces reciprocal back-links, unifies duplicates, and saves reconciliation report.

### 2. Processing Pipeline (Stages 1.5 through 8)
Executed when raw transcripts already exist under `playground/cresmo/raw/<channel_name>/<video_id>.txt`.
Sequence: `cresmo-fluid-prose` -> `raw_indexing` -> `cresmo-gap-filler` -> `cresmo-long-expander` -> `cresmo-wide-expander` -> `cresmo-atomic` -> `cresmo-moc-manager` -> `dedup`

### 3. Direct Sub-Skill Routing
Executed when the user requests a single isolated task (e.g., pure fluid prose detranscription via `cresmo-fluid-prose`, gap expansion via `cresmo-gap-filler`, longitudinal expansion via `cresmo-long-expander`, synchronic expansion via `cresmo-wide-expander`, atomic note extraction via `cresmo-atomic`, or MOC reconciliation via `cresmo-moc-manager`).

---

## Inter-Skill Data Contracts & Anti-Corruption Layer (ACL)

When chaining sub-skills in multi-stage pipelines, `cresmo` enforces the following data transfer rules:

### Directory & File Conventions
All outputs MUST be saved under the designated pipeline structure:
- Raw Transcripts Input: `playground/cresmo/raw/<channel_name>/<video_id>.txt`
- Enriched Expander Output: `playground/cresmo/enriched/<channel_name>/<video_id>.md` (CRITICAL: Stage 3 and Stage 4 outputs are ALWAYS saved in `enriched/` and NEVER in `raw/`).
- Atomic JSON Output: `playground/cresmo/enriched/<channel_name>/<video_id>.json`
- Atomic notes wiki proliferation directory: `playground/cresmo/wiki/<note_type>/` (where `<note_type>` is `entity`, `concept`, `event`, or `process`).
- Obsidian Index SSOT: `playground/cresmo/wiki/_index.json`
- MOC Files: `playground/cresmo/wiki/MOCs/MOC_*.md`
- Reconciliation Report: `playground/cresmo/enriched/<channel_name>/<video_id>_reconciliation.md`
- Idempotency Tracking Log: `playground/cresmo/processed_cresmo.json`

Stage Outputs:
- **Stage 1 Output (Raw Ingestion - `cresmo_ingestion`)**: `playground/cresmo/raw/<channel_name>/<video_id>.txt` (Raw transcript text with YouTube YAML frontmatter metadata).
- **Stage 1.5 Output (Fluid Prose - `cresmo-fluid-prose`)**: Clean, authoritative, continuous Markdown prose in third-person neutral narrative without speech noise or conversational markers (`FluidTranscript`).
- **Stage 2 Output (Catalog Indexing - `raw_indexing`)**: Incremental append to `playground/cresmo/wiki/_canal.md` and global tabular catalog (`brain.csv`).
- **Stage 3 Output (Gap Filler - `cresmo-gap-filler`)**: `playground/cresmo/enriched/<channel_name>/<video_id>.md` (Progressive multi-pass Socratic gap densification with mandatory `## Informações Complementares`).
- **Stage 4 Output (Expander - `cresmo-long-expander` & `cresmo-wide-expander`)**: In-place expansion of `playground/cresmo/enriched/<channel_name>/<video_id>.md` across Braudelian *longue durée* and Jaspers Axial Time.
- **Stage 5 Output (Atomic Note Generation - `cresmo-atomic`)**: `playground/cresmo/enriched/<channel_name>/<video_id>.json` (Strictly autonomous JSON array of note objects with Obsidian YAML frontmatter, strict typologies, and WikiLinks).
- **Stage 6 Output (Proliferation & Indexing - `parse_and_proliferate_notes`)**: Individual Atomic Note `.md` files placed in `playground/cresmo/wiki/<note_type>/[Exact Note Title].md` and global registry updates in `playground/cresmo/wiki/_index.json`.
- **Stage 7 & 8 Output (MOC Management & Graph Reconciliation - `cresmo-moc-manager`)**: MOC updates (`playground/cresmo/wiki/MOCs/MOC_*.md`), trans-text reciprocal bi-directional link synchronization, duplicate unification, and final Reconciliation Report (`playground/cresmo/enriched/<channel_name>/<video_id>_reconciliation.md`).

---

## Large Payload Strategy & Temporary Artifact Lifecycle Protocol

When pipeline stages (specifically Stage 3/4 narrative densification and Stage 5 atomic extraction) generate large payloads that challenge LLM output token limits, tool payload thresholds, or combinatorial graph operations, the agent is explicitly authorized to adopt an intermediate staged architectural pattern.

### Operational Thresholds Defining a "Large Payload":
- **File / Payload Size Threshold**: Estimated or measured text/JSON payload $> 50\text{ KB}$ (or $> 25,000\text{ characters}$ / $\approx 10,000\text{ tokens}$).
- **Entity / Note Count Threshold**: Batches containing $> 30$ atomic notes or multi-era historical compendiums with $> 15$ complementary annotations.
- **Relational Complexity**: High-density intra-batch relational hyperlinking requiring programmatic graph closure ($A \to B \iff B \to A$) and orphan closure against `_index.json`.

---

## Operational Execution Protocol

1. **Analyze Intent**: Determine whether the user requires the full end-to-end pipeline (Stages 1 through 8), the processing pipeline, an intermediate stage, or a single isolated sub-skill.
2. **Resolve Topology**: Extract `channel_name` and `video_id` from the source YAML metadata and resolve standard directory paths (`playground/cresmo/raw/`, `playground/cresmo/enriched/`, `playground/cresmo/wiki/`).
3. **Execute Stage 1 (Raw Ingestion)**: Ingest transcript from source URL or YouTube channel, outputting `playground/cresmo/raw/<channel_name>/<video_id>.txt` with standardized YAML header.
4. **Execute Stage 1.5 (Fluid Prose - `cresmo-fluid-prose`)**: Purge all speech noise, conversational filler, diagrams, and bullet lists, standardizing Named Entities (NER) into continuous narrative prose (`FluidTranscript`).
5. **Execute Stage 2 (Catalog Indexing - `raw_indexing`)**: Extract key concept, summary, and paratactic synthesis from `FluidTranscript`, appending to channel catalog and `brain.csv`.
6. **Execute Stage 3 (Gap Filler - `cresmo-gap-filler`)**: Process fluid prose through multi-pass Socratic gap audit, stratifying causality (structural, conjunctural, triggers) and constructing the mandatory `## Informações Complementares` section in `playground/cresmo/enriched/<channel_name>/<video_id>.md`.
7. **Execute Stage 4 (Expander - Longitudinal & Synchronic Deep Expansion)**: In-place deepen `playground/cresmo/enriched/<channel_name>/<video_id>.md`:
   - Step 1: Run `cresmo-long-expander` to incorporate Fernand Braudel's *longue durée*, multi-secular structural forces, 3-tier causal stratification, and historical palimpsests.
   - Step 2: Run `cresmo-wide-expander` to incorporate Karl Jaspers' Axial Time (*Achsenzeit*), synchronic horizontal cross-sections, and trans-civilizational comparative dossiers.
8. **Execute Stage 5 (Atomic Note Generation - `cresmo-atomic`)**: Process enriched Markdown compendium into autonomous atomic notes formatted as a JSON array. Enforce typologies, frontmatter metadata, source tags (`#fonte/[channel_name]/[video_id]`), and WikiLinks. Save result to `playground/cresmo/enriched/<channel_name>/<video_id>.json`.
9. **Execute Stage 6 (Proliferation & Indexing - `parse_and_proliferate_notes`)**: Unpack JSON note objects into individual Markdown files under `playground/cresmo/wiki/<note_type>/[Exact Note Title].md` and update `playground/cresmo/wiki/_index.json`.
10. **Execute Stages 7 & 8 (MOC Management, Vault Graph Sync, & Reconciliation - `cresmo-moc-manager`)**:
   - Reconcile notes against `_index.json`, perform incremental merges, update trans-text reciprocal back-links, and weave each note into the appropriate narrative Map of Content under `playground/cresmo/wiki/MOCs/MOC_*.md`.
   - Save the definitive audit and reconciliation report to `playground/cresmo/enriched/<channel_name>/<video_id>_reconciliation.md`.
11. **Update Idempotency Log & Deliver Summary**: Record video completion in `playground/cresmo/processed_cresmo.json` and present a structured delivery summary with exact clickable links to all generated files.
