---
name: writer-expander
description: Performs deep systematic gap analysis (Socratic audit and historical-scientific mapping) to identify and expand knowledge gaps in text drafts and footnotes. Enriches text with real-world statistics, historical context, precursor mapping, and persuasive non-confrontational journalistic reporting wrapped in XML config_file tags. Use whenever the user asks for conceptual expansion, gap analysis, factual enrichment, historical-scientific audit, or persuasive journalistic expansion using the Writer Expander skill.
---

# Writer Expander

## Overview

The `writer-expander` skill is a specialized subskill of the `writer` ecosystem. It performs a systematic two-pass gap analysis (Socratic intra-text audit and historical-scientific mapping) to identify epistemic lacunae in draft texts and accessory notes, subsequently executing a rich, persuasive, data-anchored expansion.

The final output is written in fluid journalistic prose with exact statistics, representative real-world examples, historical anchors, and numbered footnotes, strictly formatted in Markdown and encapsulated within XML `<config_file>` tags.

---

## Directives & Operating Instructions (Manual de Expansão Conceitual)

Sua tarefa é identificar todos os gaps de conhecimento tanto do corpo principal quanto das notas acessórias através de um método sistemático de auditoria de lacunas de conhecimento (*gap analysis*) em textos e anotações existentes seguindo um processo em três passos.

---

### Passo 1: Análise Interna de Gaps (Processamento Silencioso)

> [!NOTE]
> Faça essa análise internamente por 3 iterações consecutivas. **NÃO apresente** os resultados intermediários das etapas A e B na resposta final.

#### A. Auditoria Socrática Intra-Texto (Corpo do Texto e Notas Acessórias)
**A1. Auditoria em Seis Dimensões Epistêmicas:**
1. **Clareza e Delimitação Conceitual (O que é?):** Qual é a definição precisa dos termos fundamentais deste texto? Quais são as fronteiras desse conceito? Onde ele deixa de ser aplicável? Há tautologia?
2. **Pressupostos e Fundações (O que está sendo assumido?):** Quais premissas o autor assume como verdadeiras sem apresentar provas no texto? O que o leitor precisa saber previamente para que este texto faça sentido?
3. **Evidência e Validação (Como sabemos disso?):** Qual é a base empírica, lógica ou factual que sustenta cada afirmação principal? Onde o texto substitui dados concretos por generalizações ou adjetivos?
4. **Mecanismo e Causalidade (Como funciona?):** O texto explica as etapas intermediárias de cada processo mencionado? Existe alguma transição de estado ou evento que ocorre sem uma explicação física, lógica ou histórica? Há vazio de significado, ausência de engrenagens intermediárias ou tautologia causal?
5. **Implicações e Consequências (E daí?):** Quais são as consequências lógicas das afirmações feitas? O texto aborda os efeitos colaterais ou as limitações da solução apresentada?
6. **Perspectivas Alternativas (O que foi ignorado?):** Quais são as visões concorrentes, contra-argumentos ou exceções a esta tese? Quais perguntas um crítico cético faria a este texto que permanecem sem resposta? O que deveria estar escrito, mas foi omitido?

**A2. Cognitive Domain Mapping:** Mapeie o conhecimento transversalmente em três níveis: conceitual (*o que é*), procedimental (*como funciona*) e causal (*por que funciona*).

#### B. Análise Histórico-Científica (Corpo do Texto e Notas Acessórias)
1. **Auditoria de Atribuição e Genealogia Intelectual:** Rastreamento de precursores, identificação de colaboradores omitidos, e investigação de propriedade intelectual e fama.
2. **Mapeamento da Transição entre Teoria Abstrata e Concreta:** Localização de elos de transição (artigos, experimentos, patentes), integração teórico-prática e mecanismos de influência cronologicamente comprovados.
3. **Rigor de Classificação e Limitações Técnicas:** Separação clara entre modelo teórico e implementação física, combate rigoroso ao anacronismo e identificação de limites conceituais originais.
4. **Reconstituição de Redes e Contextos de Convergência:** Mapeamento de redes pessoais e profissionais, espaços de convergência interdisciplinar (simpósios, periódicos) e geografia do conhecimento.
5. **Mapeamento de Ancestralidade e Posteridade Epistêmica:** Raízes e pré-requisitos conceituais, ramificações e desdobramentos diretos/indiretos, e avaliação da tensão entre ruptura e continuidade.
6. **Auditoria de Silenciamento, Viés de Sobrevivência e Assimetria de Registro:** Análise do viés de sobrevivência documental, apropriação do trabalho invisível e geopolítica do conhecimento.

*Após o processamento dos itens A e B, execute 3 revisões iterativas internas da matriz de cobertura antes de proceder à expansão.*

---

### Passo 2: Condução da Expansão Conceitual Textual

1. **Espinha Dorsal Narrativa:** A linha mestra orienta a expansão lateral. Use a causalidade profunda como guia para preencher gaps até entrar suavemente em disciplinas correlatas (somente aprofunde em campos distintos para corrigir injustiças ou erros históricos relevantes).
2. **Controle de Explosão Combinatória:** Não perca a espinha dorsal, não utilize listas que não alterem o desfecho narrativa e evite campos semânticos que exijam explicações excessivamente complexas.
3. **Gestão de Excedentes:** Mantenha no corpo principal as expansões que incrementam o desfecho do argumento central ou trazem correções históricas vitais. Registre todas as demais expansões em **notas de rodapé/esclarecimento numeradas** ao final do texto.

---

### Passo 3: Reescrita Persuasiva, Tom e Formatação

1. **Ancoragem Factual e Tom de Reportagem:**
   - Abandone o tom acadêmico; adote o tom de reportagem investigativa fluida e persuasiva.
   - Substitua abstrações por dados concretos tangíveis: números exatos, estatísticas precisas, datas validadas e exemplos didáticos reais e representativos.
   - Todas as informações factuais adicionadas devem ser pesquisadas e confirmadas na web como fonte da verdade. Jamais insira dados não-verificados.

2. **Estratégia de Persuasão e Convencimento por Assimilação:**
   - **Frestas de Convencimento:** Confirme a visão de mundo do leitor antes de tensioná-la. Nunca anuncie a tarefa ou missão. Proibido usar rótulos literais como "jornalista investigativo", "auditoria do poder" ou "sociologia do poder".
   - **Conforto Estético Inicial:** Proporcione sensação de sofisticação, calma e maturidade ("coisa de gente séria e ponderada").
   - **Pós-Efeito Lento e Difuso:** O convencimento ocorre por assimilação gradual pós-leitura; o leitor sente que "sempre soube disso".
   - **Fechamento Cínico:** Encerramento lúcido, sóbrio e sem ilusão moralista ou pedagógica.
   - **Princípio Master:** *Show (the tools and wheels), don't tell (the instructions).*

3. **Arquitetura Estrutural e Tipografia:**
   - Divida em macropartes (Eras, Séculos, Fases ou Conceitos Principais) e micropartes (Anos, Décadas ou Conceitos aninhados) utilizando títulos (`##`) e subtítulos (`###`) Markdown.
   - Garanta transições fluidas com conectivos formais entre todos os parágrafos.
   - **Negrito (`**...**`)**: Apenas na primeira ocorrência de nomes históricos, conceitos teóricos fundamentais, termos técnicos cruciais e instituições.
   - **Itálico (`_..._`)**: Estritamente para títulos de obras culturais, programas/softwares, equipamentos e termos estrangeiros não aportuguesados.
   - **Proibição Absoluta**: Proibido usar imagens, diagramas, tabelas, LaTeX, fórmulas, blocos de destaque (callouts), bullets ou listas numeradas. Texto narrativo puro.

---

### 4. Regra de Resposta e Saída Automatizada (XML Envelope Strict Requirement)

A resposta deve ser em formato markdown, com marcações XML de início e final de arquivo:

```xml
<config_file>
# Heading 1
texto da *resposta*
</config_file>
```

- **Restrição Absoluta**: Não faça comentários dentro do XML no começo do texto, nem ao final da resposta.
- **Sem Interação Conversacional**: Não se ofereça para aprofundar, não ofereça aprofundamentos, não mostre links externos e não apresente vídeos sobre o assunto.
- **Saída Estrita**: Apresente exclusivamente o artigo dentro das tags XML, sem introduções ou contextualizações adicionais.
