---
name: cresmo-atomic
description: Converts expanded fluid text into a collection of interconnected Atomic Notes formatted for Obsidian Second Brain as a JSON array. Maps WikiLinks, note typologies, causal matrices, and double-side linking. Use whenever expanded text needs to be broken down into structured, interlinked atomic notes formatted in JSON. Make sure to trigger this skill whenever atomic note generation for Obsidian is requested.
---

# Cresmo Atomic (Atomic Notes Generator & WikiLinks Mapper)

## Overview

The `cresmo-atomic` skill processes expanded narrative Markdown texts (from `cresmo-expander` or existing clean drafts) and extracts a **complete set** of autonomous, semantically dense **Atomic Notes** for an Obsidian Second Brain vault. It operates under an **update-first paradigm**: when entities or concepts are already cataloged in `cresmo/wiki/_index.json`, the skill targets those existing nodes for **enrichment and update** rather than generating duplicate notes or omitting them, minting new atomic notes only for genuinely unindexed entities.

All narrative prose written within the atomic notes must adhere strictly to the [`cresmo-style-guide`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-style-guide/SKILL.md), structuring explanations across two or three implicit levels of technical detail and specific vocabulary (precision words for specialists, paired with metaphorical explanations for non-specialists), with high conceptual density, low verbosity, second-order mechanisms, affirmative syntax, zero em-dashes (`—`), and zero binary antitheses.

Each note addresses a single entity, concept, event, or process, using strict YAML metadata, standardized Obsidian WikiLinks (`[[Note Title]]`), declarative triple connections, causal attribution matrices, and bi-directional cross-context linking.

Save output directly to `cresmo/enriched/<channel_name>/<video_id>.json`.

---

## Fundamental Atomic Principles

1. **Principle of Atomicity**: Each note must cover a single autonomous idea, entity, historical event, or dynamic process, containing all necessary context to be fully understandable on its own.
2. **Semantic Density & Style Compliance**: Avoid empty notes. Every note must extract full factual substance and conceptual rigor, complying with the [`cresmo-style-guide`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/cresmo-style-guide/SKILL.md): structure the explanation across two or three implicit levels of technical detail, combining domain precision words for specialists with structuring metaphorical explanations for non-specialists, high conceptual density, low verbosity, second-order mechanisms, zero em-dashes (`—`), and zero binary antitheses.
3. **Internal WikiLinks Syntax**: Every mention of another note within the vault must be formatted as `[[Exact Note Title]]` or `[[Exact Note Title|Flexed Surface Text]]`.
4. **Resolution of Orphan Terms & Update-Over-Creation Governance**: No note may reference a non-existent node. If any `[[WikiLink]]` target appears in any note body, the corresponding atomic note MUST either (a) already exist in the vault as registered in `cresmo/wiki/_index.json`, or (b) be included in the current JSON batch. Consult `cresmo/wiki/_index.json` before generating notes:
   - **Update Existing Notes (Do Not Create Duplicates)**: If an entity, concept, event, or process is already registered in `_index.json` (matched by canonical title or any registered alias), the agent MUST NOT create a new note under a different title or surface variation. The note emitted in the JSON batch MUST reuse the exact canonical title and type from `_index.json`. The note body is enriched with the new source text's facts, mechanisms, triples, and causal connections, serving as an update payload for `cresmo-moc-manager` rather than spawning a duplicate file.
   - **Create New Notes Only When Unindexed**: Only when an entity is genuinely novel and absent from `_index.json` does the agent mint a new canonical title and create a new atomic note.
5. **Principle of Exhaustive Extraction**: The entire source text, including every paragraph, sentence, and supplementary section, must be systematically scanned for extractable entities. No noteworthy item may be silently omitted. The output batch must capture the full semantic content of the source text as a self-contained knowledge graph.

---

## Exhaustive Entity Extraction Protocol

The extraction process follows a **three-pass sequential sweep** over the complete source text. No paragraph may be skipped. No section may be deprioritized.

### Pass 1: Paragraph-by-Paragraph Sequential Scan

Process the source text from beginning to end, paragraph by paragraph:

1. **Identify every proper noun**: persons, places, institutions, documents, works, organizations, infrastructure, geographic features, hydrographic features, political entities, languages, and any other named thing.
2. **Identify every dated event**: any event with an explicit temporal marker (year, month, full date, approximate period) generates an `event` note with Big-Endian date prefix.
3. **Identify every domain-specific concept**: specialized terminology, processes, social phenomena, doctrines, legal constructs, technical methods, scientific principles, philosophical frameworks, representing anything that requires domain knowledge to understand.
4. **Identify every dynamic process**: cause-and-effect chains, systemic flows, operational sequences, historical movements, and recurring phenomena that transcend a single event or entity.
5. **Harvest supplementary context**: When the source text contains a supplementary or complementary information section (numbered footnotes, biographical notes, contextual annotations), extract the factual content from these entries and integrate it into the relevant atomic notes. Each supplementary entry enriches the corresponding note's "Definição e Análise Contextual" section with additional biographical, historical, or technical depth. Entities appearing exclusively in supplementary entries still require their own atomic notes.

### Pass 2: Alias Resolution & Vault Disambiguation (Update vs. Create Protocol)

Before generating the note batch:

1. **Consult `cresmo/wiki/_index.json`**: For every candidate entity, perform a bidirectional lookup against `_index.json`. Check both primary dictionary keys (canonical titles) and every list of `aliases`.
2. **Match Found -> UPDATE MODE**: If the candidate matches an existing entry in `_index.json` (by title or alias):
   - **Exact Canonical Title**: Use the exact canonical title registered in `_index.json` as the `# [Exact Note Title]` and in all `[[WikiLinks]]`. Never use a synonymous or surface-level variant as the note title (for instance, if `1139-07-25 Batalha de Ourique` is in `_index.json`, use that exact title, avoiding separate notes like `# Batalha de Ourique`).
   - **Type Preservation**: Retain the `type:` registered in `_index.json`.
   - **Alias Inheritance & Growth**: Populate `aliases:` with all existing aliases from `_index.json` plus any new variant found in the current text.
   - **Content Enrichment**: Emit the JSON note object with the newly synthesized contextual analysis, declarative triples, causal matrix, and cross-context links from the current source. This payload updates the existing note in the vault during Stage 5/6 (`cresmo-moc-manager`) without creating a duplicate file.
3. **Match NOT Found -> CREATION MODE**: If and only if the candidate is completely absent from `_index.json`:
   - Mint a new canonical title following typology rules (Big-Endian date notation for events).
   - Register any surface variants and parenthetical annotations in `aliases:`.
   - Emit as a newly created atomic note.
4. **Grammatical flexions in text**: When the text refers to an existing or new entity in a flexed form, use `[[Canonical Title|Flexed Form]]` and ensure the flexed form is included in the note's `aliases:` list.
5. **Parenthetical annotations are alias signals**: When the source text uses constructions like `"Modern Name (Ancient Name)"`, `"Full Name (Acronym)"`, or `"Local Term (Translation)"`, the primary term becomes the note title and the parenthetical term becomes an alias in the `aliases:` YAML field. If the entity already exists in `_index.json` under either name, use the existing canonical title and add the new variant as an alias.

### Pass 3: Orphan Closure Audit

After generating all notes from Passes 1 and 2:

1. **Compile a master set** of every `[[WikiLink]]` target referenced across all note bodies in the current batch.
2. **For each target**, verify that it resolves to either (a) an existing note registered in `_index.json`, or (b) a note present in the current JSON batch.
3. **For every unresolved target**, generate an atomic note using whatever context is available from the source text. If information is minimal, apply the Minimal Note Protocol (see below).
4. **Repeat** the audit until no dangling links remain within the batch (excluding links that resolve to `_index.json` entries).

---

## Extraction Depth & Granularity Rules

These rules are **field-agnostic**, applying identically whether the source text covers history, technology, science, philosophy, law, economics, literature, or any other domain.

1. **Rule of Autonomous Meaning**: If removing a term from the sentence would leave an informational gap that a reader cannot fill from general knowledge alone, that term deserves its own note. Yeah, that may need a lot of notes. 
2. **Proper Nouns Always Generate Notes**: Every proper noun (person, place, institution, document, work, event, or named thing) generates a note. No exceptions.
3. **Dated Events Always Generate Notes**: Any event anchored to an explicit temporal marker generates an `event` note with a Big-Endian date prefix in the title.
4. **Domain-Specific Terms Generate Notes**: Specialized vocabulary requiring domain expertise to understand generates a `concept` or `entity` note, regardless of how briefly it appears in the source text.
5. **Parenthetical Annotations Are Extraction Signals**: When the source text contains parenthetical clarifications, both the primary term and the parenthetical variant produce a single note with the variant as an alias.
6. **Supplementary Sections Enrich Notes**: Content from complementary information sections, numbered footnotes, and contextual annotations feeds into the corresponding note's body. Entities that appear exclusively in these sections still generate their own atomic notes.
7. **Implicit Actors Generate Notes**: When a source text describes an action attributed to a named group, class, or unnamed individual whose identity can be inferred from context, that actor generates a note if it carries autonomous semantic value.

---

## Note Typologies & Title Nomenclatures

Every generated note must belong to one of four strict categories:

1. **Entity Notes (`type: entity`)**:
   - Scope: Named entities such as persons, institutions, organizations, geographic features, infrastructure, political units, documents, legal codes, works, languages, social classes, or any other distinctly named thing.
   - Title Convention: Official or canonical name in the vault's language.

2. **Concept Notes (`type: concept`)**:
   - Scope: Theoretical models, doctrines, laws, philosophical constructs, methodologies, technical concepts, scientific principles, and specialized domain terminology.
   - Title Convention: SSOT/Encyclopedic canonical form.

3. **Event / Temporal Milestone Notes (`type: event`)**:
   - Scope: Events, treaties, agreements, battles, foundations, investitures, births, deaths, or any occurrence delimited in time.
   - Title Convention: **Big-Endian date notation** prefix followed by event name (e.g., `[[YYYY-MM-DD Event Name]]`, `[[YYYY Event Name]]`, `[[YYYY-QN Event Name]]`).

4. **Process / Causal Synthesis Notes (`type: process`)**:
   - Scope: Operational sequences, cause-and-effect dynamics, systemic flows, recurring phenomena, and historical movements.
   - Title Convention: Flow or dynamic name describing the process.

## Metadata Extraction & Tag Propagation

Input transcripts contain a YouTube YAML frontmatter header:
- `video_id`: (e.g. `eYFTRQHaPgw`)
- `channel_name`: (e.g. `"HENI OZI CUKIER"`)

Every generated atomic note MUST extract `channel_name` and `video_id` from the source transcript header and populate the `tags:` list in the YAML frontmatter with `#source/[channel_name_slug]/[video_id]` along with category, domain, and cluster tags.

---

## Mandatory Note Structure Template

Every note MUST be formatted using this exact Markdown template:

```markdown
---
type: entity | concept | event | process
content:
  - [primary_tag]
  - [primary_tag]/[theme_subtag] (se e quantas houverem)
domain: [domain]
cluster: [cluster]
source: [channel_name_slug]/[video_id]
aliases: ["Alternative Name 1", "Acronym or Short Name"]
---
# [Exact Note Title]

## Definição e Análise Contextual
[Analytical description of 1 to 3 continuous paragraphs conforming to the cresmo-style-guide. Structures the explanation across at least two or three implicit levels of technical detail and specific vocabulary (precision words for specialists who understand the details, and metaphorical explanations for non-specialists), with high conceptual density and low verbosity. Consolidates fundamental definition, second-order mechanisms, historical/technical context, and systemic role. When supplementary information is available for this entity (from footnotes, complementary sections, or contextual annotations in the source text), integrate that content here to enrich the note's factual depth. Strictly zero em-dashes and zero binary antitheses. All domain terms must use [[WikiLink]] syntax.]

## Conexões e Relações Diretas
* [[Nota Origem ou Sujeito]] -> [Verbo de Ação ou Conector de Ligação] -> [[Nota Destino ou Objeto]], em linguagem natural similar ao texto original

## Matriz Causal e Atribuição Epistêmica
* **Causa / Premissa:** [Fator ou fatores condicionais ou eventos que originam ou sustentam esta nota]
* **Efeito / Impacto:** [Desdobramentos e consequências decorrentes desta nota]
* **Atribuição Epistêmica:** [[Entidade Proponente ou Fonte Histórica]]

## Redes de Conexão e Contexto Cruzado

* **Precursores e Ancestralidade (origem genealógica, base epistemológica ou causa histórica primária, marco antecedente necessário):** Explique a relação histórica ou conceitual com a [[Nota Precursora 1]] e a [[Nota Precursora 2]] 
* **Eventos Laterais e Paralelos (fenômeno coetâneo análogo ou mecanismo concorrente, instituição ou processo correlato sem causalidade direta):** Descreva o contexto simultâneo ou conexões horizontais com a [[Nota Lateral 1]] e a [[Nota Lateral 2]]
* **Desdobramentos e Posteridade (derivação teórica subsequente ou impacto de longo curso, ruptura sistêmica ou reação institucional deflagrada):** Aponte os impactos futuros e desdobramentos relacionados à [[Nota Posterior 1]] e a [[Nota Posterior 2]]

```

---

## Minimal Note Protocol for Sparse Entities

For entities mentioned only in passing or with minimal available context in the source text, apply a slim but complete note format:

1. **Full YAML frontmatter**: All fields (`type`, `content`, `domain`, `cluster`, `source`, `aliases`) must be populated.
2. **"Definição e Análise Contextual"**: A short text providing whatever context the source text supplies, supplemented by the note's relational position in the knowledge graph. This section will have notes to other notes. 
3. **"Conexões e Relações Diretas"**: At minimum one declarative triple linking back to the note(s) that reference this entity. This section will have notes to other notes.
4. **"Matriz Causal e Atribuição Epistêmica"**: May be abbreviated to a single cause-effect pair, but must not be omitted entirely. This section will have notes to other notes.
5. **"Redes de Conexão e Contexto Cruzado"**: At minimum one entry under "Precursores e Ancestralidade" or "Eventos Laterais e Paralelos", linking to contextually adjacent notes. This section will have notes to other notes.

Sparse notes are first-class citizens of the vault. They serve as anchoring nodes that prevent orphan links and provide attachment points for future enrichment from other sources.

---

## Bi-Directional Double-Side Linking Execution

1. **Exhaustive Hyperlinking**: Embed `[[WikiLinks]]` across every mention of named entities, treaties, historical dates, theories, and processes in text bodies.
2. **Aliasing Syntax**: Use `[[Target Title|Flexed Form]]` when text syntax requires grammatical flexions, ensuring the base `Target Title` matches the destination note exactly. Add the flexed form to the `aliases:` list in the YAML header.
3. **Declarative Triples**: In `## Conexões e Relações Diretas`, convert extracted triples into declarative statements in natural language similar to the original text.
4. **Bi-Directionality Verification**: For every note A that contains `[[B]]` in its body, note B MUST contain `[[A]]` in at least one of its sections (Conexões, Matriz Causal, or Redes de Conexão). Perform this verification for all note pairs in the batch before emitting the final JSON. Notes referencing entries that already exist in `_index.json` and are not part of the current update batch are exempt from this check within the current batch, as the `cresmo-moc-manager` handles cross-text back-linking during reconciliation.

---

## Completeness Self-Verification Checklist

Before emitting the final JSON output, verify that all conditions are met:

1. ✅ Every paragraph and every section of the source text (including supplementary/complementary sections) has been scanned for extractable entities.
2. ✅ Every candidate entity registered in `_index.json` (by title or alias) is emitted using its EXACT registered canonical title and type, guaranteeing that it updates the existing vault note rather than creating a duplicate file.
3. ✅ Newly created notes are minted exclusively for entities that do not exist in `_index.json`.
4. ✅ Every explicitly dated event has a corresponding `event` note with Big-Endian title prefix.
5. ✅ Every domain-specific term or specialized concept has a corresponding note.
6. ✅ Every `[[WikiLink]]` in any note body resolves to either an existing `_index.json` entry or a note in the current batch.
7. ✅ Every note pair within the batch satisfies bi-directional linking (A links B implies B links A).
8. ✅ All parenthetical annotations have been processed as aliases with `_index.json` disambiguation.
9. ✅ The Minimal Note Protocol has been applied to all sparse entities, ensuring no entity was silently dropped for lack of context.

---

## Automated JSON Output Specification

The complete batch of generated atomic notes MUST be presented as a **JSON array of objects** saved directly to `cresmo/enriched/<channel_name>/<video_id>.json`.

Do NOT write individual files via bash scripts or tool loops. The pipeline will automatically unpack the JSON array into individual vault markdown files and update `_index.json`.

```json
[
  {
    "title": "Guimarães",
    "type": "entity",
    "content": [
      "geografia",
      "geografia/centro_urbano"
    ],
    "domain": "geografia_historica",
    "cluster": "centros_de_poder_medieval",
    "source": "marcelo-andrade/9IbNJ0EsTxI",
    "aliases": [
      "Berço da Nação",
      "Vila de Guimarães",
      "Burgo de Guimarães"
    ],
    "definition": "Guimarães constituiu o centro administrativo, militar e simbólico original do Condado Portucalense, atuando como núcleo originário da afirmação senhorial da dinastia de Borgonha...",
    "direct_relations": [
      "[[Guimarães]] -> abrigou a corte condal de -> [[Henrique de Borgonha]]",
      "[[Guimarães]] -> serviu de local de nascimento para -> [[Afonso Henriques]]",
      "[[Guimarães]] -> testemunhou o desfecho da insurreição em -> [[1128-06-24 Batalha de São Mamede]]"
    ],
    "causal_matrix": {
      "cause": "Fundação do mosteiro e da fortaleza defensiva por Mumadona Dias para proteção contra incursões normandas e muçulmanas.",
      "effect": "Fixação do centro de gravidade político do Condado Portucalense até a transferência da capital para Coimbra.",
      "epistemic_attribution": "Documentos cartorários medievais e crônicas régias portuguesas."
    },
    "cross_context": {
      "precursors": "Origem ancorada na fortificação condal do século X e na consolidação territorial do Condado Portucalense.",
      "lateral_events": "Articulação defensiva contemporânea com a diocese metropolitana de [[Braga]].",
      "aftermath": "Perda da condição de capital administrativa com a [[1131 Transferência da Capital para Coimbra]], preservando o prestígio simbólico de berço dinástico."
    }
  }
]
```

---

## Large Payload Architecture & Intermediate Scratch Lifecycle

When processing large transcripts where the extracted atomic batch exceeds operational buffer thresholds, the agent is explicitly authorized and expected to adopt an intermediate staged architectural pattern.

### Operational Thresholds Defining a "Large Payload":
- **Total Output Size**: Estimated or measured JSON payload $> 50\text{ KB}$ (or $> 25,000\text{ characters}$ / $\approx 10,000\text{ tokens}$).
- **Node Count**: Batch containing $> 30$ atomic notes.
- **Graph Complexity**: High-density intra-batch relational cross-linking requiring mathematical closure ($A \to B \iff B \to A$) across dozens of nodes.

### Permitted Intermediate Architectural Pattern:
1. **Modular Chunk Staging**: The agent may segment note definitions across temporary modular files in the workspace scratch directory (e.g., `scratch/atomic_group*.py` or temporary JSON chunk files).
2. **Automated Programmatic Quality Gate**: The agent may write and execute an assembly/audit script in `scratch/` to:
   - Programmatically compute bidirectional graph reconciliation (adding missing reciprocal links so that $A \to B \implies B \to A$).
   - Perform orphan closure audits against `wiki/_index.json`.
   - Run regex checks enforcing zero em-dashes (`—`) and zero binary antitheses across 100% of the notes.
   - Validate each note against `AtomicNoteModel` (Pydantic V2).
3. **Single Source of Truth Target Write**: The assembled batch must be written in a single consolidated write operation directly to `cresmo/enriched/<channel_name>/<video_id>.json`.
4. **Mandatory Post-Assembly Scratch Cleanup**: Once the final JSON file is verified as valid (`is_valid_atomic_json(target_file) == True`) and non-empty, the agent **MUST immediately delete all temporary scratch scripts, chunks, and cached files** created during the intermediate stage. No temporary scratch files may be left behind in the workspace after task completion.

---

Save output directly to `cresmo/enriched/<channel_name>/<video_id>.json`.
Do not output any introductory greetings, conversational commentary, or postscripts outside the JSON payload.

