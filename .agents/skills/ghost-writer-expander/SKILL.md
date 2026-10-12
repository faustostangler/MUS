---
name: ghost-writer-expander
description: Performs deep epistemic gap analysis and conceptual expansion on text drafts using a two-pass Socratic and historical-scientific audit. Enriches the text and footnotes with verified numerical data, realistic real-world examples, precursors, historical context, and persuasive journalistic tone without losing the core narrative spine. Use whenever text needs deep factual enrichment, epistemic gap filling, or persuasive reporting expansion.
---

# Ghost Writer Expander

## Overview

The `ghost-writer-expander` skill performs systematic knowledge gap audits and narrative expansions on existing drafts. Using a two-stage process—an internal Socratic & Historical-Scientific audit followed by textual expansion—it enriches drafts with realistic data, precise statistics, verified real-world examples, and precursor history, applying the author's baroque-naturalist prose identity as defined in the `ghost-writer-style` guide.

All outputs generated must be saved directly to Markdown (.md) files (such as `03_expanded.md`). Outputs must consist strictly of structured hierarchical paragraphs (Markdown headers and narrative prose), never using tables, diagrams, lists, or bullets.

**Style Dependency**: Before generating any output, read and apply the authorial style guide at [`ghost-writer-style/references/style-guide.md`](file:///home/stangler/gamer_d/Fausto%20Stangler/Documentos/Python/PES/.agents/skills/ghost-writer-style/references/style-guide.md). The expander is the primary stage where the authorial identity is most fully expressed.

---

## Operating Protocol & Execution Rules

1. Two-Stage Process:
   - Stage 1 (Internal Audit): Run Socratic audit across 6 epistemic dimensions + 6 historical-scientific directives internally without showing output. Iterate 3 times.
   - Stage 2 (Textual Expansion): Expand gaps while maintaining the narrative spine. Place secondary expansions in numbered footnotes.
2. Real-World Anchoring: Replace generic terms with exact factual data, real historical cases, precise dates, and confirmed statistics verified on the web.
3. Baroque-Naturalist Authorial Voice: Apply the full 7-pillar authorial identity from `ghost-writer-style`. Use alternância borgiana de registros (natural scientist, analytical philosopher, prose poet, secular preacher). Avoid accessible journalism, academic legalese, and moralistic denunciation.
4. Concept Creation: When expansion reveals mechanisms lacking satisfactory existing terms, always create new original Latin coinages following the style guide protocol. Existing terms across the ecosystem are illustrative examples only — never recycle them.
5. Payload Formatting: Save the final expanded article directly to a Markdown (.md) file (e.g., `03_expanded.md`). The output MUST consist exclusively of structured hierarchical paragraphs (Markdown headers and narrative prose). Never use tables, diagrams, lists, or bullets.

---

## Detailed Prompt Directives (Diretrizes de Auditoria e Expansão)

Sua tarefa é identificar todos os gaps de conhecimento tanto do corpo principal quanto das notas acessórias através de um método de revisão e auditoria (método sistemático de auditoria) de lacunas de conhecimento (gap analysis) em textos e anotações existentes seguindo um processo em duas etapas.

### Passo 1: Auditoria Interna de Gaps (Não Apresentar Resultados do Passo 1)

#### A - Auditoria Socrática Intra-Texto
**A1 - Seis Dimensões Epistêmicas**:
1. Clareza e Delimitação Conceitual (O que é?): Qual é a definição precisa dos termos fundamentais deste texto? Quais são as fronteiras desse conceito? Onde ele deixa de ser aplicável? Há tautologia?
2. Pressupostos e Fundações (O que está sendo assumido?): Quais premissas o autor assume como verdadeiras sem apresentar provas no texto? O que o leitor precisa saber previamente para que este texto faça sentido?
3. Evidência e Validação (Como sabemos disso?): Qual é a base empírica, lógica ou factual que sustenta cada afirmação principal? Onde o texto substitui dados concretos por generalizações ou adjetivos?
4. Mecanismo e Causalidade (Como funciona?): O texto explica as etapas intermediárias de cada processo mencionado? Existe alguma transição de estado ou evento que ocorre sem uma explicação física, lógica ou histórica? Há vazio de significado e ausência de engrenagens intermediárias, ou tautologia causal?
5. Implicações e Consequências (E daí?): Quais são as consequências lógicas das afirmações feitas? O texto aborda os efeitos colaterais ou as limitações da solução apresentada?
6. Perspectivas Alternativas (O que foi ignorado?): Quais são as visões concorrentes, contra-argumentos ou exceções a esta tese? Quais perguntas um crítico cético faria a este texto que permanecem sem resposta? O que deveria estar escrito, mas foi omitido?

**A2 - Cognitive Domain Mapping**:
Mapeie o conhecimento em três níveis: conceitual (o que é), procedimental (como funciona) e causal (por que funciona).

#### B - Análise Histórico-Científica
1. Auditoria de Atribuição e Genealogia Intelectual: Rastreamento de Precursores, Identificação de Colaboradores Omitidos, Investigação de Propriedade e Fama.
2. Mapeamento da Transição entre Teoria Abstrata e Concreta: Elos de Transição, Integração Teórico-Prática, Mecanismos de Influência.
3. Rigor de Classificação e Limitações Técnicas: Separação entre Modelo e Implementação, Combate ao Anacronismo, Limites Conceituais Originais.
4. Reconstituição de Redes e Contextos de Convergência: Mapeamento de Redes Pessoais, Espaços de Convergência Interdisciplinar, Geografia do Conhecimento.
5. Mapeamento de Ancestralidade e Posteridade Epistêmica: Raízes/Ancestralidade Epistêmica, Ramificações/Posteridade, Tensão de Ruptura vs. Continuidade.
6. Auditoria de Silenciamento, Viés de Sobrevivência e Assimetria de Registro: Viés Documental, Apropriação/Trabalho Invisível, Geopolítica do Conhecimento.

*Revise iterativamente por 3 vezes a veracidade e completude dos gaps identificados.*

---

### Passo 2: Condução da Expansão Conceitual Textual

1. Use a causalidade profunda para substituir abstrações e preencher gaps no corpo principal e nas notas acessórias.
2. Evite a explosão combinatória: mantenha a espinha dorsal narrativa do texto.
3. Mova expansões secundárias ou tangenciais para notas informativas de rodapé ao final do texto.

---

### Passo 3: Reescrever o Texto Expandido

#### Estilo e Tom
Aplique integralmente a identidade autoral barroca-naturalista do guia `ghost-writer-style`. O texto deve integrar explicação científica, especulação filosófica e linguagem literária numa única estrutura argumentativa.
Execute a alternância borgiana de registros: oscile deliberadamente entre cientista natural, filósofo analítico, poeta em prosa e pregador secular. Nunca permaneça em um único registro por mais de três parágrafos consecutivos.
Texto altamente persuasivo por densidade factual e arquitetura causal, não por denúncia moral ou adjetivos ruidosos.
Quando a expansão identificar mecanismos sem termo satisfatório, crie novos conceitos latinos originais seguindo o protocolo do guia de estilo. Os conceitos devem ser inéditos — nunca transplante termos de outros textos.

#### Fatos Tangíveis e Dados Reais
Ancore a narrativa em elementos realistas do mundo real: números exatos, estatísticas precisas, datas confirmadas, nomes próprios e casos reais pesquisados e validados na web.

#### Estrutura
Divida em macropartes (`##`) e micropartes (`###`). Use ordem cronológica linear ou encadeamento lógico estrito.
Aplique negrito (`**...**`) apenas na primeira ocorrência de nomes próprios relevantes, conceitos fundamentais e termos técnicos cruciais.
Aplique itálico (`_..._`) estritamente para obras culturais, softwares, hardwares e termos estrangeiros.
Sem imagens, diagramas, tabelas, fórmulas, LaTeX, blocos de destaque, bullets ou listas.

#### Saída Automatizada em Arquivo Markdown
A saída expandida deve ser gravada diretamente em um arquivo Markdown (.md) no local designado (como `playground/ghost-writer/<article_slug>/03_expanded.md`).
O arquivo deve conter estritamente o texto formatado em parágrafos estruturados hierarquicamente.
É proibido utilizar tabelas, diagramas, listas ou bullets. Não faça comentários nem introduções/conclusões conversacionais.
