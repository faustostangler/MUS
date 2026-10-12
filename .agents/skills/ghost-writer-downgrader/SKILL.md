---
name: ghost-writer-downgrader
description: Reduces text overwriting, conceptual obesity, and off-topic micro-details. Strips narrative clutter from the main body while preserving core conceptual transition links, delegating secondary explanations, biographical noise, and collateral details into numbered footnotes. Use whenever a document is overly bloated, verbose, or contains excessive tangential details that disrupt the narrative spine.
---

# Ghost Writer Downgrader

## Overview

The `ghost-writer-downgrader` skill performs structural de-bloating and conceptual reduction on dense, overly detailed, or "conceptually obese" texts. It purges substrate-independent micro-details, tangential biographical noise, and deep domain incursions from the main body text, relocating secondary details into explanatory footnotes to leave only the core narrative spine in the primary text.

All outputs generated must be saved directly to Markdown (.md) files (such as `04_final_article.md`). Outputs must consist strictly of structured hierarchical paragraphs (Markdown headers and narrative prose), never using tables, diagrams, lists, or bullets.

**Style Dependency**: Before generating any output, read and apply the authorial style guide at [`ghost-writer-style/references/style-guide.md`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-style/references/style-guide.md). The downgrader preserves the author's baroque-naturalist prose identity while reducing textual obesity.

---

## Operating Protocol & Execution Rules

1. Substrate Independence: Eliminate granular micro-details that obscure the central thesis. Note: the author's deliberate second-order explanations (mechanisms that produce mechanisms) and emergent-effect analyses are NOT substrate-independent details — they are part of the core argumentative structure and must be preserved.
2. Noise Suppression: Remove biographical digressions, collateral attributions, and off-topic narrative diversions from the main text.
3. Transition Preservation: Keep all essential logical and causal transition links intact in the primary body.
4. Concept & Metaphor Preservation: The author's coined concepts (Latin neologisms, novel terms) and structural metaphors (images that sustain argumentation, not ornament it) must NEVER be removed during de-bloating. They are load-bearing elements of the narrative architecture.
5. Footnote Delegation: Move all secondary, collateral, and accessory information into numbered footnotes.
6. Payload Formatting: Save the final processed text directly to a Markdown (.md) file (e.g., `04_final_article.md`). The output MUST consist exclusively of structured hierarchical paragraphs (Markdown headers and narrative prose). Never use tables, diagrams, lists, or bullets.

---

## Detailed Prompt Directives (Diretrizes de Redução)

Você vai receber um texto com *overwriting* e com obesidade conceitual e informações que se afastam da espinha dorsal do texto e invadem de forma profunda outros campos e domínios sem contribuir para a estrutura do texto. Muitas informações já estão em notas explicativas de rodapé.

### Diretrizes Principais

#### 1. Eliminação de Microdetalhes e Ruído
Faça a Eliminação de Microdetalhes (*Substrate Independence*), Supressão de Ruído Biográfico e Atribuições Paralelas.
Faça a Preservação dos Elos de Transição Conceitual (Informações Relevantes).
Deixe no texto principal apenas a essência, e mova para as notas explicativas todo o restante.

#### 2. Formatação e Estilo
Apresente a resposta em formato Markdown (.md), sem imagens, sem diagramas, sem tabelas, sem fórmulas, sem LaTeX, sem blocos de destaque, sem bullets e sem listas, consistindo exclusivamente de parágrafos narrativos estruturados hierarquicamente (`#`, `##`, `###`), mantendo o manual de estilo do texto original.

#### 3. Regra de Saída Automatizada em Arquivo Markdown
A resposta processada deve ser gravada diretamente em um arquivo Markdown (.md) no caminho designado (como `playground/ghost-writer/<article_slug>/04_final_article.md`).
Não faça comentários no começo ou no final da resposta. Não se ofereça para aprofundar e não mostre links externos nem vídeos. Apresente restritamente a gravação direta no arquivo Markdown.
