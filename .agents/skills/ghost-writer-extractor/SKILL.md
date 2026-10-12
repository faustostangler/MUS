---
name: ghost-writer-extractor
description: Extracts semantic information and knowledge graph constructs from text into standard natural language representations (NER, Abstract Concepts, Timelines, Triples, Dynamic Processes, and Argumentative Cause-and-Effect). Eliminates code syntax, arrows, or brackets in favor of fluid human sentences. Use whenever the user wants to convert a document into a structured knowledge graph representation or extract semantic entities and relationships.
---

# Ghost Writer Extractor

## Overview

The `ghost-writer-extractor` skill extracts semantic knowledge graphs from scientific, philosophical, or technical texts. It converts natural language concepts into standard semantic dimensions (Named Entities, Abstract Concepts, Timelines, Triples, Dynamic Processes, and Argumentative Logic) using strictly natural human sentences, completely omitting programming symbols, code syntax, or graph arrows (`->`, `[]`).

All extracted semantic graphs MUST be persisted directly into Markdown (.md) files (such as `05_semantic_graph.md`). Outputs must consist strictly of structured hierarchical paragraphs (Markdown headers and narrative prose), never using tables, diagrams, lists, or bullets.

**Style Reference**: When processing texts produced by the ghost-writer ecosystem, consult [`ghost-writer-style/SKILL.md`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-style/SKILL.md) to recognize the author's coined concepts (Latin neologisms, novel terms) and structural metaphors as first-class entities. These are not ornamental — they are load-bearing conceptual constructions that must be extracted as primary entities in the NER and Concepts dimensions.

---

## Operating Protocol & Execution Rules

1. Strict Natural Language: Express all relations as grammatically complete, human-readable sentences.
2. Zero Code Syntax: Omit code symbols like `->`, `[Subject]`, `(RELATION)`. Express connections through direct conjugated verbs.
3. Standardized Parentheses: Place secondary descriptive metadata inside parentheses immediately following the primary entity or concept name.
4. Rigorous Extraction: Cover all 6 semantic dimensions exhaustively without summarizing or omitting secondary actors.
5. Clean Output in Markdown File: Save the final semantic graph directly to a Markdown (.md) file (e.g., `05_semantic_graph.md`). Output strictly in structured hierarchical paragraphs (`#`, `##`, `###`). Never use tables, diagrams, lists, or bullets.

---

## Detailed Prompt Directives (Manual Consolidado de Extração Semântica)

Sua tarefa é realizar a extração de informações semânticas a partir de textos fornecidos. O objetivo é padronizar a conversão de linguagem natural em nós, arestas e propriedades para a futura montagem de um grafo de conhecimento.

### Diretrizes Gerais de Redação e Estilo

Toda e qualquer relação extraída deve ser redigida como uma frase gramaticalmente completa e inteligível para um leitor humano.
É mandatório omitir símbolos de modelagem (como `->`, `[Sujeito]`, `(RELAÇÃO)`). As conexões devem ser expressas por verbos conjugados de forma direta em parágrafos fluídos.
Elementos descritivos secundários de entidades e conceitos devem constar entre parênteses, logo após o termo principal.
A resposta deve ser gravada diretamente em um arquivo Markdown (.md) e ser estruturada exclusivamente por títulos e parágrafos hierarquizados, sendo proibido o uso de tabelas, diagramas, listas ou bullets.

---

### Manual de Extração por Dimensões Semânticas

#### Entidades Nomeadas (NER)
A extração de entidades nomeadas registra o nome da entidade seguido de seu papel, profissão ou classificação contextualizada entre parênteses. NUNCA omita ou resuma personagens secundários, inventores, autores ou organizações associadas a um feito, patente, obra ou crítica no texto. É estritamente proibido inserir anos, datas ou marcos temporais dentro dos parênteses das Entidades Nomeadas. As entidades devem ser descritas em parágrafos textuais contínuos. Por exemplo, Marie Curie é contextualizada como física e química polonesa. George Devol é registrado como inventor e detentor das patentes originais de robótica industrial de 1954.

#### Conceitos, Teorias e Ideias
A extração conceitual registra o nome do conceito seguido da área do conhecimento ou campo de estudo afiliado entre parênteses. Evite copiar expressões adjetivadas ou literais se puderem ser reduzidas ao seu termo enciclopédico padrão. Os conceitos devem ser apresentados em prosa fluida. Por exemplo, Lógica Universal é registrada como campo da filosofia e da matemática, evitando-se fórmulas adjetivadas como Lógica Universal e Determinista.

#### Marcos Temporais
Marcos temporais registram o ano ou data acompanhados da descrição fluida do evento histórico e de suas implicações teóricas ou práticas em formato de parágrafo narrativo. Por exemplo, em 1953, a publicação do modelo de dupla hélice do DNA revolucionou a compreensão da genética e inaugurou a era da biologia molecular moderna.

#### Triplas (Fatos e Relações)
As triplas registram fatos e relações em orações diretas no formato de sujeito, verbo de ação ou ligação e objeto, escritas de forma contínua em prosa sem pontuação intermediária artificial. Transforme todas as conexões em declarações afirmativas simples. Para relações taxonômicas, utilize estritamente a expressão pertence a ou é um tipo de. Por exemplo, Alexander Fleming descobriu a Penicilina. Termodinâmica pertence à Física Clássica.

#### Processos e Fluxos Dinâmicos
Processos e fluxos dinâmicos registram o nome do processo geral sob um subtítulo dedicado, seguido por parágrafos explicativos que detalham como cada etapa é uma divisão do processo geral e como cada etapa conduz à próxima. Por exemplo, sob o processo geral Fotossíntese, a absorção de luz solar é descrita como uma divisão da Fotossíntese, detalhando-se em seguida como a absorção de luz solar leva à fotólise da água.

#### Raciocínio Argumentativo (Causas e Efeitos)
O raciocínio argumentativo registra em parágrafos narrativos como um fator causal leva a um efeito resultante, indicando a entidade proponente entre parênteses. Por exemplo, a conversação automatizada com o chatbot ELIZA provoca a atribuição inconsciente de sentimentos e inteligência a sistemas de texto, tese proposta por Joseph Weizenbaum.

---

### Regra de Resposta e de Registração em Arquivo Markdown

A saída da extração semântica deve ser gravada diretamente em um arquivo Markdown (.md) no caminho especificado (como `playground/ghost-writer/<article_slug>/05_semantic_graph.md`).

O arquivo deve conter estritamente parágrafos estruturados hierarquicamente (`#`, `##`, `###`).

Não faça comentários no começo ou ao final da resposta. Não se ofereça para aprofundar e não mostre links ou vídeos externos.
