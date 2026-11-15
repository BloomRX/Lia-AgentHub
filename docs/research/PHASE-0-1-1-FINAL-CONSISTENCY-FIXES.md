# Fase 0.1.1 — Correções finais de consistência

**Documento:** `docs/research/PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md`
**Sessão:** Agent 0.1.1 — Correções finais antes da decisão humana
**Data:** 2026-11-15 (UTC)
**Branch:** `arena/a92004be-lia-agenthub`
**Commit de partida:** `d6c303313a4b36aa5defe73f54044c08d1d43d3d`
**Natureza:** correção documental pontual. **Nenhuma implementação foi realizada.** A Fase 1 **não** está aprovada.

---

## 0. Resultado em uma frase

Duas inconsistências apontadas pela revisão humana foram corrigidas — **12 referências** de
`D-17`/`D-27` reclassificadas e **1 divergência de conteúdo** na política Unicode reconciliada,
com **16 verificações automatizadas** confirmando que os três documentos agora expressam a
mesma regra. Nenhuma decisão foi promovida a `APPROVED`.

---

## 1. Escopo e método

### 1.1 O que foi feito

| Item | Ação |
|---|---|
| Correção 1 — `D-17` vs. `D-27` | Auditoria global de todas as 26 ocorrências; 12 estavam ou ambíguas ou erradas; corrigidas |
| Correção 2 — Política Unicode | Comparação lado a lado de três fontes; 1 divergência de conteúdo e 2 ambiguidades; reconciliadas em tabela normativa única |
| Verificação | Script de 16 asserções cruzando os três documentos — **16/16 PASS** |
| Relatório | Este documento |

### 1.2 O que **não** foi feito

| Não feito | Motivo |
|---|---|
| Reabrir pesquisa | Fora do escopo declarado |
| Implementar o scanner Unicode | Proibido pela §6 |
| Criar `LICENSE` | `D-16` continua aberta (decisão humana) |
| Aprovar qualquer decisão | Proibido; o objetivo é consistência, não aprovação |
| Alterar `main` | Proibido |
| Abrir PR ou fazer merge | Proibido |
| Tocar `D-05`, `D-16`, `D-18` | Continuam `OPEN` por decisão do mandato |

### 1.3 Integridade do ponto de partida

```
$ git rev-parse HEAD
d6c303313a4b36aa5defe73f54044c08d1d43d3d     ← coincide com o commit informado
$ git merge-base --is-ancestor 34a27f48 HEAD && echo SIM
SIM                                            ← base ainda é ancestral
$ git rev-parse origin/main
34a27f484e5f85987390a27fe7e0c0b3cd205bb2       ← main intacta
```

---

## 2. Correção 1 — `D-17` vs. `D-27`

### 2.1 A distinção estabelecida

| Decisão | Objeto | Seção no doc de plataforma |
|---|---|---|
| **`D-17`** | **Sistemas operacionais** do primeiro MVP | **§6** (Matriz de sistemas operacionais) |
| **`D-27`** | **Biblioteca de interface** (`pywebview`, navegador do sistema ou híbrido) | **§5.5.4** |

As duas decisões continuam com **o mesmo significado** de antes. O que mudou foi **para onde as
referências apontam** — não o conteúdo de nenhuma delas.

### 2.2 Referências corrigidas

| # | Arquivo | Linha | Antes | Depois | Tipo |
|---|---|---|---:|---|---|
| 1 | `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` | 6 | `(D-14, D-17)` | `(D-14, D-17, D-27)` | cabeçalho |
| 2 | `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` | 16–17 | `D-17` = "Sistemas operacionais" apenas | `D-17` = **Sistemas operacionais** (§6) **+ linha nova** `D-27` = **Biblioteca de interface** (§5.5.4) | índice |
| 3 | `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` | 239 | "A decisão é `D-17`" (sobre `pywebview`) | "A decisão é `D-27`" | **atribuição errada** |
| 4 | `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` | 383 | `D-13`, `D-14`, `D-17` | `D-17` (sistemas operacionais), `D-27` (biblioteca de interface) | referências |
| 5 | `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | 165 | "As três opções estão em `D-17`" | "…em `D-27`" | **atribuição errada** |
| 6 | `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | 662 | "As três opções entram em `D-17`" | "…em `D-27`" | **atribuição errada** |
| 7 | `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | 672 | "**Isto é `D-17`**" | "**Isto é `D-27`**" | **atribuição errada** |
| 8 | `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | 785 | "Usuário (`D-17`)" em Q-02 (`pywebview` vs. navegador) | "Usuário (`D-27`)" | **atribuição errada** |
| 9 | `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | 846 | "`D-14`, `D-17` revisadas" | "`D-14` revisada; `D-17` com nota remetendo a `D-27`" | resumo impreciso |
| 10 | `THIRD_PARTY_NOTICES.md` | 47 | "### 2.2 Interface (se `D-17` escolher `pywebview`)" | "…(se `D-27` escolher `pywebview`)" | **atribuição errada** |

**Total: 10 linhas editadas em 3 arquivos**, cobrindo 12 referências (a linha 16–17 do índice
produziu duas entradas).

### 2.3 O que foi deliberadamente **mantido** em `D-17`

Sete referências permanecem apontando para `D-17` porque **estão corretas**:

| Arquivo | Ocorrência | Por que está correta |
|---|---|---|
| `DECISION-REGISTER.md` | `### D-17 — Sistemas operacionais do primeiro MVP` | É a definição |
| `DECISION-REGISTER.md` | Nota da Fase 0.1 remetendo a `D-27` | É a ponte, e está certa |
| `DECISION-REGISTER.md` | Índice de estados (`D-17` entre as `RECOMMENDED`) | Estado correto |
| `PLATFORM…` | Linha 6 (cabeçalho) e 16 (índice) | Agora corretas |
| `REVIEW` | Tabela §5: "`D-17` (sistemas operacionais) — **Não alterada**" | Registro histórico correto |
| `REVIEW` | Índice de estados | Estado correto |

### 2.4 Verificação de atribuição equivocada residual

```
$ grep -rn "pywebview\|navegador do sistema" docs/ README.md THIRD_PARTY_NOTICES.md \
    | grep -E "D-1[3-9]|D-2[0-9]"
```

| Ocorrência | Veredito |
|---|---|
| `REVIEW:165` — "as três opções estão em `D-27`" | correta |
| `REVIEW:770` — `D-27` = "Biblioteca de interface: `pywebview` vs. navegador" | correta |
| `REVIEW:785` — Q-02, dono `D-27` | correta |
| `REGISTER:263` — nota de `D-17` remetendo a `D-27` | correta |
| `REGISTER:452` — definição de `D-27` | correta |
| `PLATFORM:17` — índice, `D-27` | correta |
| `THIRD_PARTY:47` — `D-27` | correta |

**Nenhuma atribuição equivocada residual.** `D-14` menciona `pywebview` apenas como **evidência**
do piso de Python (é a dependência que força `≥3.11`), não como decisão de interface — o que é
legítimo e foi mantido.

---

## 3. Correção 2 — Política Unicode reconciliada

### 3.1 As três fontes comparadas

| Fonte | O que dizia |
|---|---|
| `PHASE-0-1-CONSISTENCY-REVIEW.md` §3.2.3 | Tabela por codepoint: `U+202A–202E` = **REJEITAR** em código, **REVISAR** em prosa |
| `PHASE-0-1-CONSISTENCY-REVIEW.md` §3.2.4 | Tabela por contexto: prosa listava `U+202A–202E` dentro de "A = … apenas em bloco de código" — **ambíguo** |
| `docs/DECISION-REGISTER.md` `D-26` | Genérico: "`U+202A–202E` e `U+2066–2069` em bloco de código" — **não dizia nada sobre prosa** |
| `SECURITY-AND-TRUST-MODEL.md` §3.2.2 | Tabela por codepoint: `U+202A–202E` = **A** em prosa ← **DIVERGÊNCIA** |

### 3.2 A divergência encontrada

| Faixa | Contexto | Review | D-26 | Segurança | **Brief** | Veredito |
|---|---|---|---|---|---|---|
| `U+202A`–`U+202E` | Prosa | B | (implícito B) | **A** | **B** | **Segurança errada** |
| `U+202A`–`U+202E` | Código | A | A | A | **A** | OK |
| `U+202A`–`U+202E` | Identificador | A | (implícito A) | A | **A** | OK |
| `U+2066`–`U+2069` | Prosa | B | (implícito B) | B | **B** | OK |
| `U+2066`–`U+2069` | Código | A | A | A | **A** | OK |
| `U+2066`–`U+2069` | Identificador | A | (implícito A) | A | **A** | OK |

**Uma única divergência de conteúdo:** a segurança classificava `U+202A–202E` como **A** em
prosa, quando o canônico é **B**.

### 3.3 A reconciliação

A tabela normativa passou a existir em **um lugar só**, e os outros dois documentos remetem a
ela. Isso elimina a possibilidade de divergência futura por edição parcial.

**`SECURITY-AND-TRUST-MODEL.md` §3.2.2.1 — nova "Tabela normativa das duas faixas bidi":**

| Faixa | **Prosa** | **Bloco de código** | **Identificador** |
|---|---|---|---|
| `U+202A`–`U+202E` | **B** | **A** | **A** |
| `U+2066`–`U+2069` | **B** | **A** | **A** |

E as duas seções que a consultam foram alinhadas:

| Documento | Alteração |
|---|---|
| `SECURITY-AND-TRUST-MODEL.md` §3.2.2 | `U+202A–202E` prosa **A → B** |
| `SECURITY-AND-TRUST-MODEL.md` §3.2.2.1 | **Nova** tabela normativa, com justificativa e regra de precedência |
| `SECURITY-AND-TRUST-MODEL.md` (nota de precedência) | Substituída por "análise por região", mais a nota de que `A` vence **dentro da mesma região**, sem propagar entre regiões |
| `PHASE-0-1-CONSISTENCY-REVIEW.md` §3.2.4 | Tabela de contexto reescrita com as três listas **explícitas** (A, B, C/D) por contexto, removendo a ambiguidade |
| `PHASE-0-1-CONSISTENCY-REVIEW.md` §3.2.4 | Nota "Fonte única da verdade" remetendo a §3.2.2.1 |
| `DECISION-REGISTER.md` `D-26` | Três linhas novas: regra das duas faixas, justificativa da diferença em prosa, o que permanece em `A` |

### 3.4 Tabela Unicode reconciliada — catálogo completo

Resultado final, idêntico nos três documentos. `A` = rejeitar · `B` = sinalizar e exigir revisão
· `C` = preservar · `D` = preservar e exibir escapado.

| Codepoint(s) | Nome | Prosa | Código | Identificador |
|---|---|---|---|---|
| `U+200B` | ZERO WIDTH SPACE | B | B | A |
| `U+200C` | ZWNJ | **D** | B | B (só A1/A2) |
| `U+200D` | ZWJ | **D** | B | B (só B) |
| `U+200E` | LRM | B | **A** | A |
| `U+200F` | RLM | B | **A** | A |
| `U+061C` | ALM | B | **A** | A |
| **`U+202A`–`U+202E`** | **LRE, RLE, PDF, LRO, RLO** | **B** | **A** | **A** |
| **`U+2066`–`U+2069`** | **LRI, RLI, FSI, PDI** | **B** | **A** | **A** |
| `U+2060` | WORD JOINER | B | B | A |
| `U+2061`–`U+2064` | FUNCTION APPLICATION, INVISIBLE ×/÷/+ | B | B | A |
| `U+FEFF` | BOM / ZWNBSP | byte 0: normaliza e remove · meio: **A** | A | A |
| `U+E0000`–`U+E007F` | TAG characters | **A** (exceto as 3 RGI) | **A** | A |
| `U+3164`, `U+115F`, `U+1160` | HANGUL FILLER / CHOSEONG·JUNGSEONG | B | B | A |
| `U+00AD` | SOFT HYPHEN | **C** | C | A |
| `U+00A0` | NO-BREAK SPACE | **C** | C | A |
| `U+180E` | MONGOLIAN VOWEL SEPARATOR | B | B | A |
| `U+FFF9`–`U+FFFB` | Interlinear annotation | B | **A** | A |

### 3.5 Justificativa normativa — por que as duas faixas não são idênticas

Esta é a parte que precisa estar explícita, porque a diferença entre as faixas é o ponto onde
uma "harmonização" apressada poderia enfraquecer a política.

| | `U+202A`–`U+202E` | `U+2066`–`U+2069` |
|---|---|---|
| O que fazem | Embeddings e **overrides** | **Isolates** |
| `LRO`/`RLO` | **Invertem a ordem visual sem mudar o byte** | Não existem — isolates não reordenam |
| Recomendação do UAX #9 | Forma **legada** | Forma **recomendada** para texto bilíngue |
| Uso legítimo em prosa | Raríssimo; texto árabe/hebraico antigo | Comum e correto em texto bilíngue moderno |
| **Categoria em prosa** | **B** | **B** |
| **Categoria em código** | **A** | **A** |

**Por que ambas ficam em `B` na prosa e não em `A`:** mesmo `U+202A–U+202E` aparece em conteúdo
árabe/hebraico legítimo, e o usuário precisa poder importar esse conteúdo. **B** preserva o
arquivo e bloqueia a promoção até revisão — não destrói nem aceita silenciosamente.

**Por que ambas ficam em `A` no código:** em bloco de código não existe prosa bilíngue legítima
que exija controle bidi. Qualquer ocorrência é sinal de injeção. Trojan Source (CVE-2021-42574)
atua exatamente aqui.

**Nada foi enfraquecido.** A classificação em prosa mudou de `A` para `B` apenas na tabela da
segurança, que era a exceção. As outras cinco células já eram `B` ou `A` antes desta rodada. A
política em bloco de código — onde o ataque realmente atua — permaneceu **`A` em todas as seis
células**, sem exceção.

### 3.6 Análise por região — preservada e explicitada

O brief exige que a análise seja **por região**, não por arquivo. Isso está agora afirmado em
três lugares, com a mesma redação:

> Um `SKILL.md` com `U+202E` em prosa (categoria **B**) e sem controles em bloco de código é
> **importado para quarentena e sinalizado**, não rejeitado. O mesmo caractere dentro de uma
> cerca tripla é **rejeitado**.

E a nota de precedência foi corrigida para não sugerir propagação entre regiões:

> A categoria `A` vence **dentro da mesma região** — se um identificador aparece dentro de um
> bloco de código, a regra do identificador e a do bloco de código coincidem (`A`). Não há caso
> em que `A` em uma região force `A` em outra região do mesmo arquivo.

A formulação anterior ("`A` em qualquer contexto vence") podia ser lida como precedência global,
o que contradiria a análise por região. Agora não pode.

---

## 4. Verificações realizadas

### 4.1 Script de consistência cruzada — 16 asserções

| # | Verificação | Resultado |
|---:|---|---|
| 1 | `SECURITY` §3.2.2.1 existe | **PASS** |
| 2 | `SECURITY` tabela normativa `U+202A–202E` = B \| A \| A | **PASS** |
| 3 | `SECURITY` tabela normativa `U+2066–2069` = B \| A \| A | **PASS** |
| 4 | `SECURITY` §3.2.2 catálogo `U+202A–202E` = B \| A \| A | **PASS** |
| 5 | `SECURITY` §3.2.2 catálogo `U+2066–2069` = B \| A \| A | **PASS** |
| 6 | `REVIEW` §3.2.4 prosa: `U+202A–202E` na lista **B** | **PASS** |
| 7 | `REVIEW` §3.2.4 prosa: `U+2066–2069` na lista **B** | **PASS** |
| 8 | `REVIEW` §3.2.4 código: `U+202A–202E` em **A** | **PASS** |
| 9 | `REVIEW` §3.2.4 código: `U+2066–2069` em **A** | **PASS** |
| 10 | `REVIEW` §3.2.3 `U+202A–202E`: rejeitar em código, revisar em prosa | **PASS** |
| 11 | `REVIEW` §3.2.3 `U+2066–2069`: revisar | **PASS** |
| 12 | `D-26` regra `U+202A–202E` explícita (B / A / A) | **PASS** |
| 13 | `D-26` regra `U+2066–2069` explícita (B / A / A) | **PASS** |
| 14 | `D-26` análise por região | **PASS** |
| 15 | `D-26` pendência `PropList.txt` + `DerivedCoreProperties.txt` | **PASS** |
| 16 | `D-26` exige fixar a versão do Unicode | **PASS** |

**16/16 PASS.**

### 4.2 Verificações de integridade do repositório

| Verificação | Resultado |
|---|---|
| Links relativos quebrados em 16 arquivos `.md` | **0** |
| Decisões no registro | **27** (`D-01`…`D-27`) |
| Decisões com estado `APPROVED` | **0** |
| `D-01`, `D-05`, `D-16`, `D-18` ainda `OPEN` | **Sim** |
| `LICENSE` presente | **Não** (correto — `D-16` aberta) |
| `main` alterada | **Não** (`34a27f48`) |
| Arquivos de código de produto | **0** |

### 4.3 Nota sobre uma leitura falsa positiva

Uma verificação por `grep` de `APPROVED` retornou **1** ocorrência. A investigação mostrou que é
o **placeholder do template** de aceite (`**Estado:** APPROVED | REJECTED | DEFERRED`), não o
estado de uma decisão. O parse correto por bloco de decisão confirma **0 `APPROVED`**.

Registro isto porque a diferença entre "grep achou 1" e "existe 1 decisão aprovada" é exatamente
o tipo de conclusão que este projeto não pode errar.

---

## 5. Limitações que continuam abertas

| # | Limitação | Estado | O que destrava |
|---|---|---|---|
| **L-α** | **Versão do Unicode não fixada.** `unicode.org/Public/` deu HTTP 000; `PropList.txt` e `DerivedCoreProperties.txt` **não** foram baixados nesta sessão | **Aberta** — registrada em `D-26` | Antes do scanner: fixar a versão, baixar as duas tabelas **daquela versão**, gerar a tabela de codepoints a partir delas. Nunca digitar à mão |
| **L-β** | Homóglifos entre escritas não detectados | **Aberta** — herdada | Exigiria `confusables.txt`; fora desta fase |
| **L-γ** | Nenhum scanner implementado | **Correto** — proibido nesta fase | F1a, após aprovação |
| **L-δ** | `D-05`/`D-18` (isolamento Windows) | **`OPEN`** | Agent 3, com máquina Windows real |
| **L-ε** | `D-16` (licença do repositório) | **`OPEN`** | Decisão humana |
| **L-ζ** | `canirunai.kc1t.com` não alcançável | **Aberta** — herdada da Fase 0 | Esclarecimento do usuário |
| **L-η** | Licenciamento do Obsidian não verificado | **Aberta** — herdada | Reverificação humana |

**A limitação L-α é a que o brief destaca e a que mais importa:** a política Unicode está
consistente **entre os documentos**, mas isso não significa que a **lista de codepoints** esteja
verificada contra uma fonte oficial. Ela é derivada do UTS #39 lido nesta sessão e de
conhecimento do padrão. Consistência documental ≠ verificação normativa.

---

## 6. Arquivos alterados

Medido por `git diff --numstat` contra `d6c3033`:

| Arquivo | Alteração | +linhas | −linhas |
|---|---|---:|---:|
| `docs/architecture/SECURITY-AND-TRUST-MODEL.md` | §3.2.2 `U+202A–202E` prosa A→B; **nova** §3.2.2.1 tabela normativa; nota de precedência reescrita para "por região" | 35 | 5 |
| `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | 4 atribuições `D-17`→`D-27`; §3.2.4 tabela de contexto com listas explícitas; nota "fonte única"; resumo de arquivos | 12 | 8 |
| `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` | cabeçalho com `D-27`; índice com linha `D-27`; §5.5.4 "A decisão é `D-27`"; referências | 5 | 4 |
| `docs/DECISION-REGISTER.md` | `D-26`: 3 linhas de regra explícita + pendência reforçada (versão do Unicode) | 5 | 2 |
| `THIRD_PARTY_NOTICES.md` | §2.2 "se `D-27` escolher `pywebview`" | 1 | 1 |
| `docs/research/PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md` | **Novo** — este relatório (não contado no diff acima) | — | — |
| **Total nos 5 arquivos editados** | | **58** | **20** |

**Nenhum outro arquivo foi tocado. Nenhuma linha de código foi criada.**

> **Nota de honestidade sobre estes números.** Na primeira redação desta seção eu estimei as
> contagens de memória, e estavam erradas. Foram substituídas pela medição de `git diff
> --numstat`. Registro o erro porque um documento que pede precisão de contagem em outros
> documentos não pode apresentar contagem estimada como medida.

---

## 7. Declaração final

As duas inconsistências apontadas foram corrigidas: **10 linhas** de referência em **3 arquivos**
para `D-17`/`D-27`, e **1 divergência de conteúdo** na política Unicode com a criação de uma
tabela normativa única que os três documentos consultam em vez de duplicarem.

O que esta rodada **não** fez foi transformar consistência em aprovação. A documentação está
pronta para a decisão humana — **não** para a implementação.

**Nenhuma decisão está `APPROVED`. `D-05`, `D-16` e `D-18` continuam `OPEN`. Não existe
`LICENSE`. `main` não foi tocada. Não há PR e não houve merge. Não há código de produto.**

A Fase 1 continua **não autorizada**.

---

## 8. Identificação da entrega

| Item | Valor |
|---|---|
| Branch | `arena/a92004be-lia-agenthub` |
| Branch-base | `main` @ `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` |
| Commit de partida | `d6c303313a4b36aa5defe73f54044c08d1d43d3d` |
| **Commit final** | ver abaixo |
| Push | `origin/arena/a92004be-lia-agenthub` |
| PR | **Nenhum** |
| Merge | **Nenhum** |
| Alteração de `main` | **Nenhuma** |

> **Sobre o hash final.** Este relatório está no **segundo** commit desta rodada; o hash do
> `HEAD` final é registrado no **terceiro**, que só toca esta tabela. Isso evita o problema de
> um documento que grava o hash do commit que o contém — impossível, porque o hash depende do
> conteúdo do documento.
>
> **Verificação reproduzível, para qualquer revisão futura:**
>
> ```bash
> git log --oneline d6c3033..HEAD      # os commits desta rodada, em ordem
> git rev-parse HEAD                   # o HEAD final
> ```
>
> A entrega informa o hash no corpo da mensagem de commit final e na resposta ao usuário; o
> histórico do Git é a fonte de verdade.
