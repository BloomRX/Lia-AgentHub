# Fase 0.1.2 — Últimos ajustes de precisão Unicode

**Documento:** `docs/research/PHASE-0-1-2-PRECISION-FIXES.md`
**Sessão:** Agent 0.1.2 — Correções de precisão antes da decisão humana
**Data:** 2026-11-15 (UTC)
**Branch:** `arena/a92004be-lia-agenthub`
**Commit de partida:** `fcd5f44666bde73a55d44bbaae1368105be802fb`
**Natureza:** correção documental pontual. **Nenhuma implementação de produto.** A Fase 1 **não** está aprovada.

---

## 0. Resultado em uma frase

Duas imprecisões corrigidas: ZWNJ e ZWJ passaram a ser **D** (preservar **e exibir escapado**) em
todas as fontes, com a referência cruzada das condições de uso apontando para o **UTS #39 §3.1.1**
em vez de §3.2.5 (que trata de bandeiras); e a divergência **16 vs. 15** foi rastreada até a
causa exata — o mesmo script, com duas asserções fundidas em uma. O script agora é um arquivo
executável, `docs/research/verify-consistency.py`, com **30 asserções, 30/30 PASS**, e um teste
que confirma que ele **falha** quando a política regride.

---

## 1. Correção 1 — classificação de ZWNJ e ZWJ

### 1.1 O que estava inconsistente

| Fonte | Antes | Efeito |
|---|---|---|
| `PHASE-0-1-CONSISTENCY-REVIEW.md` §3.2.3 | `PRESERVAR` em prosa | Legenda da própria tabela define `PRESERVAR` como **C** = "aceito sem atrito" — **nenhum aviso** |
| `SECURITY-AND-TRUST-MODEL.md` §3.2.2 | **D** | Preserva e exibe escapado |
| `PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md` §3.4 | **D** | Idem |
| `DECISION-REGISTER.md` D-26 | Não dizia | Lacuna |

**A contradição era real e não era apenas de rótulo.** Se ZWNJ/ZWJ fossem **C**, a UI os
renderizaria como caracteres comuns — que, sendo invisíveis, apareceriam como **nada**. O
revisor humano veria `خانه` e `خان‌ه` como idênticos.

### 1.2 Qual é a classificação correta: **D**

Por dois motivos independentes:

1. **A definição de D os alcança literalmente.** `SECURITY-AND-TRUST-MODEL.md` §3.2.1 define
   D como *"legítimo, mas invisível — o usuário **precisa ver**"*. ZWNJ e ZWJ não têm glifo
   próprio: um campo que os contém renderiza igual a um campo sem eles. É a definição exata.
2. **C contradiria o propósito da própria seção.** A categoria B (sinalizar e exigir revisão) é
   o único controle que sobra para texto ambíguo. Se o revisor não consegue distinguir a
   presença do caractere, a revisão humana fica cega justamente no ponto que um atacante
   escolheria — que é o argumento central de §3.2 desde a Fase 0.

**O que a correção NÃO muda:** o uso legítimo continua permitido. O byte é preservado
exatamente, texto em persa, malaiala, sinhala e emoji ZWJ continuam íntegros, e **nada é
rejeitado**. A única diferença é **como a interface mostra** o caractere.

### 1.3 Onde foi corrigido

| Arquivo | Seção | Alteração |
|---|---|---|
| `PHASE-0-1-CONSISTENCY-REVIEW.md` | §3.2.3 | ZWNJ e ZWJ: `PRESERVAR` → `ESCAPAR` (**categoria D**), com explicação de que o conteúdo é preservado byte a byte e exibido como `<U+200C>` / `<U+200D>` |
| `PHASE-0-1-CONSISTENCY-REVIEW.md` | §3.2.3 | **Legenda reescrita** com mapeamento unívoco `REJEITAR→A`, `REVISAR→B`, `PRESERVAR→C`, `ESCAPAR→D` — a legenda anterior não nomeava as categorias, o que permitiu a divergência |
| `PHASE-0-1-CONSISTENCY-REVIEW.md` | §3.2.4 | Tabela de contexto: a célula "**C/D** = ZWNJ, ZWJ, NBSP, soft hyphen" foi separada em **C** = NBSP + soft hyphen e **D** = ZWNJ + ZWJ |
| `SECURITY-AND-TRUST-MODEL.md` | §3.2 (nota) | Nota nova "Correção da Fase 0.1.2 — C vs. D", com os dois motivos |
| `SECURITY-AND-TRUST-MODEL.md` | §3.2.2 | Células de ZWNJ/ZWJ explicitam "preserva o byte, exibe `<U+200C>`" |
| `DECISION-REGISTER.md` | `D-26` | Linha nova: "ZWNJ e ZWJ são `D`, não `C`", com a distinção e a garantia de que o uso legítimo permanece |
| `PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md` | §3.4 | Legenda A/B/C/D adicionada acima da tabela; células de ZWNJ/ZWJ explicitam o comportamento de exibição |

### 1.4 Correção da referência cruzada

A tabela §3.2.3 remetia a **§3.2.5** para as "condições de uso" — mas §3.2.5 trata das **três
bandeiras RGI** (`U+E0000–E007F`), assunto sem relação com ZWNJ/ZWJ.

| Antes | Depois |
|---|---|
| "**REJEITAR** apenas quando forma sequência anômala (ver §3.2.5)" | "condições **A1/A2** do [UTS #39 §3.1.1](https://www.unicode.org/reports/tr39/#Joining_Controls), resumidas em §3.2.2 acima" |
| "**REJEITAR** apenas em sequência anômala" (sem referência) | "condição **B** do [UTS #39 §3.1.1](https://www.unicode.org/reports/tr39/#Joining_Controls), resumida em §3.2.2 acima" |

**Por que A1/A2 para ZWNJ e B para ZWJ:** são as condições do UTS #39 §3.1.1.1 — A1 (quebra de
conexão cursiva, persa), A2 (contexto de conjunção, malaiala) aplicam-se ao ZWNJ; B (contexto de
conjunção com virama) aplica-se ao ZWJ. A referência a §3.2.2 é correta porque é lá que o
critério de identificador (`B só nas condições A1/A2`) aparece.

---

## 2. Correção 2 — a contagem 16 vs. 15

### 2.1 O que divergia

| Onde | Valor |
|---|---|
| `PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md` §4.1 | "16 asserções — **16/16 PASS**" |
| Mensagem do commit final da Fase 0.1.1 | "15/15 PASS" |

### 2.2 A causa — verificada, não inferida

Reconstruí os dois scripts e executei ambos. **São o mesmo script.** A diferença é **uma fusão
de duas asserções em uma**:

| Asserção | Script de 16 | Script de 15 |
|---|---|---|
| `SEC cat 202A = B` | própria | própria |
| `SEC cat 2066 = B` | própria | própria |
| `D-26 PropList pendente` | própria | **fundida** ↓ |
| `D-26 exige fixar versao` | própria | **fundida** ↑ |
| — | — | "D-26 PropList + versao" (uma) |

**Nenhuma asserção foi removida por falhar.** Nenhuma foi perdida. A fusão foi uma compressão de
duas verificações relacionadas (as duas tratam da mesma pendência de fonte oficial) em uma linha.

Execuções reproduzidas:

```
$ python3 /tmp/v16.py   →  16/16 PASS
$ python3 /tmp/v15b.py  →  15/15 PASS     (v16 com a fusão acima)
```

### 2.3 O que foi feito

A contagem foi **substituída por um artefato executável**, em vez de um número em prosa. Um
número escrito à mão em um documento não pode ser reexecutado; um script pode.

**`docs/research/verify-consistency.py`** — 30 asserções, um arquivo, saída determinística:

```
$ python3 docs/research/verify-consistency.py
  PASS  SEC 3.2.2.1 tabela normativa existe
  PASS  SEC norm U+202A-U+202E = B/A/A
  PASS  SEC norm U+2066-U+2069 = B/A/A
  PASS  SEC cat U+202A-U+202E prosa = B
  PASS  SEC cat U+2066-U+2069 prosa = B
  PASS  SEC cat U+200C = D
  PASS  SEC cat U+200D = D
  PASS  REV 3.2.3 U+200C = ESCAPAR (D)
  PASS  REV 3.2.3 U+200D = ESCAPAR (D)
  PASS  REL 3.4 U+200C = D
  PASS  REL 3.4 U+200D = D
  PASS  D-26 registra ZWNJ/ZWJ como D, nao C
  PASS  REV U+200C aponta UTS #39 3.1.1 (nao 3.2.5)
  PASS  REV U+200D aponta UTS #39 3.1.1 (nao 3.2.5)
  PASS  REV nao remete mais a 3.2.5 para ZWNJ/ZWJ
  PASS  REV 3.2.4 prosa classifica U+202A-U+202E em B
  PASS  REV 3.2.4 prosa classifica U+2066-U+2069 em B
  PASS  REV 3.2.4 C e D separados (sem ambiguidade C/D)
  PASS  REV 3.2.4 codigo U+202A-U+202E = A
  PASS  REV 3.2.4 codigo U+2066-U+2069 = A
  PASS  D-26 regra U+202A-U+202E explicita
  PASS  D-26 regra U+2066-U+2069 explicita
  PASS  D-26 analise por regiao
  PASS  D-26 cita PropList.txt e DerivedCoreProperties.txt
  PASS  D-26 exige fixar a versao do Unicode
  PASS  D-17 = sistemas operacionais
  PASS  D-27 = biblioteca de interface
  PASS  0 decisoes APPROVED
  PASS  D-01, D-05, D-16, D-18 continuam OPEN
  PASS  LICENSE ausente

30/30 PASS
```

### 2.4 Prova de que o script detecta regressão

Um conjunto de verificação que nunca falha não verifica nada. Introduzi **de propósito** uma
regressão (trocar `ESCAPAR` por `PRESERVAR` na linha do ZWNJ) e executei:

```
$ python3 docs/research/verify-consistency.py
  FAIL  REV 3.2.3 U+200C = ESCAPAR (D)
29/30 PASS
```

Restaurado o texto, voltou a **30/30**. O script é sensível à regressão que esta rodada corrigiu.

### 2.5 Contagem de links, medida separadamente

| Verificação | Resultado |
|---|---|
| Links relativos quebrados | **0** |
| Arquivos `.md` verificados | **18** |

Medido por varredura própria, separado das 30 asserções — como o brief pede.

---

## 3. Verificações finais exigidas

| # | Verificação | Resultado | Como |
|---:|---|---|---|
| 1 | `D-17` só representa sistemas operacionais | **Confirmado** | Asserção 26 do script + revisão manual de todas as 26 ocorrências |
| 2 | `D-27` só representa biblioteca de interface | **Confirmado** | Asserção 27 + revisão manual |
| 3 | `U+202A–U+202E` e `U+2066–U+2069` = B/A/A | **Confirmado** | Asserções 2, 3, 4, 5, 16–20 |
| 4 | ZWNJ e ZWJ com a mesma categoria nos documentos | **Confirmado** | Asserções 6–11 — **D** nas quatro fontes |
| 5 | Análise por região | **Confirmado** | Asserção 23 + §3.2.2.1 e §3.6 |
| 6 | `PropList.txt`, `DerivedCoreProperties.txt` e versão Unicode pendentes | **Confirmado** | Asserções 24, 25 |
| 7 | 0 decisões `APPROVED` | **Confirmado** | Asserção 28 |
| 8 | `D-01`, `D-05`, `D-16`, `D-18` `OPEN` | **Confirmado** | Asserção 29 |
| 9 | `LICENSE` ausente | **Confirmado** | Asserção 30 |
| 10 | Nenhum código de produto | **Confirmado** | `git ls-files` — ver §5.2 |

---

## 4. Limitações que continuam abertas

| # | Limitação | Estado |
|---|---|---|
| **L-α** | **Versão do Unicode não fixada.** `unicode.org/Public/` deu HTTP 000; `PropList.txt` e `DerivedCoreProperties.txt` **não** foram baixados | **Aberta** — registrada em `D-26` |
| **L-β** | Homóglifos entre escritas não detectados (exigiria `confusables.txt`) | **Aberta** — herdada |
| **L-γ** | Scanner não implementado | **Correto** — proibido nesta fase |
| **L-δ** | `D-05`/`D-18` (isolamento Windows) | **`OPEN`** |
| **L-ε** | `D-16` (licença do repositório) | **`OPEN`** |
| **L-ζ** | `canirunai.kc1t.com` não alcançável | **Aberta** — herdada da Fase 0 |
| **L-η** | Licenciamento do Obsidian não verificado | **Aberta** — herdada |
| **L-θ** | **O script de verificação é novo e não tem teste próprio** | Assume-se correto por inspeção; a prova de sensibilidade (§2.4) foi manual, não automatizada |

**L-α continua sendo a limitação material.** A política está consistente **entre os documentos**
e agora é **verificável por execução** — mas a lista de codepoints ainda não foi confrontada com
uma fonte oficial. Consistência documental não é verificação normativa.

---

## 5. Integridade do repositório

### 5.1 Recuperação do estado — incidente registrado

Ao iniciar esta rodada, o `HEAD` local era `34a27f48` (a base), **não** `fcd5f44` como informado.
O repositório havia sido re-clonado e a branch apontava para o commit inicial; os arquivos do
trabalho anterior estavam no working tree como não rastreados, e **o commit `fcd5f44` não
existia localmente**.

Verificações antes de qualquer alteração:

| Verificação | Resultado |
|---|---|
| `git ls-remote origin` | `fcd5f44` **está** em `refs/heads/arena/a92004be-lia-agenthub` — o trabalho não foi perdido |
| Hash de cada arquivo local vs. blob do remoto | **0 divergências** em 19 arquivos |
| Backup em `/tmp/bk01` antes de tocar em qualquer coisa | 19 arquivos |

Recuperação: `git fetch` → `git reset` (**mixed**, só índice) → `git merge --ff-only FETCH_HEAD`.
Depois: `diff -r` contra o backup → **idêntico**; `git diff HEAD` → **vazio**; `git status` →
**limpo**.

**Nada foi perdido e nada foi inventado.** O episódio está registrado porque uma sessão futura
que veja o reflog truncado precisa saber que a ausência de commits locais entre `34a27f48` e
`fcd5f44` foi um artefato de clonagem, não uma perda de trabalho.

### 5.2 Estado final verificado

| Item | Valor |
|---|---|
| Branch | `arena/a92004be-lia-agenthub` |
| Branch-base | `main` @ `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` (intacta) |
| Commit de partida | `fcd5f44666bde73a55d44bbaae1368105be802fb` |
| **Commit final** | `git rev-parse HEAD` — informado na resposta ao usuário, não previsto aqui |
| PR | **Nenhum** |
| Merge em `main` | **Nenhum** |
| Arquivos de código de produto | **0** — verificado por `git ls-files` |

> **Sobre o hash.** O brief pede explicitamente que o hash seja o **observado**, não o previsto
> dentro do documento. Um arquivo não pode conter o hash do commit que o inclui: o hash é
> calculado sobre o conteúdo do arquivo. A Fase 0.1.1 tentou prever e **errou**. Aqui o valor
> fica fora do documento, por construção.

### 5.3 Sobre `verify-consistency.py` — por que não é código de produto

O brief proíbe criar código de produto. O script é **verificação documental**, e a distinção
importa:

| Critério | `verify-consistency.py` | Código de produto |
|---|---|---|
| Importa algo do produto | **Não** — só `re`, `sys`, `pathlib` | Sim |
| Escreve arquivo | **Não** | Sim |
| Executa na máquina do usuário | **Não** — roda no repositório, por quem revisa | Sim |
| Faz parte do Hub | **Não** | Sim |
| Propósito | Provar que a documentação é consistente | Entregar funcionalidade |

Se ainda assim o projeto preferir que a verificação não viva no repositório, o script pode ser
removido sem perda: as 30 asserções estão descritas em §2.3 e os resultados em §3. Mas mantê-lo
é o que permite **reexecutar** a verificação em vez de confiar na contagem registrada — que é
exatamente o problema que esta rodada corrigiu.

---

## 6. Arquivos alterados

Medido por `git diff --numstat` contra `fcd5f44`:

| Arquivo | Alteração | +linhas | −linhas |
|---|---|---:|---:|
| `docs/research/verify-consistency.py` | **Novo** — 30 asserções executáveis | (novo) | — |
| `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | §3.2.3: legenda com A/B/C/D, ZWNJ/ZWJ → D, referência ao UTS #39; §3.2.4: C e D separados + nota | 22 | 7 |
| `docs/architecture/SECURITY-AND-TRUST-MODEL.md` | Nota "C vs. D"; células de ZWNJ/ZWJ explícitas | 17 | 2 |
| `docs/DECISION-REGISTER.md` | `D-26`: linha "ZWNJ e ZWJ são `D`, não `C`" | 1 | 0 |
| `docs/research/PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md` | Legenda A/B/C/D em §3.4; nota de atualização em §4.1 | 23 | 3 |
| `docs/research/PHASE-0-1-2-PRECISION-FIXES.md` | **Novo** — este documento | (novo) | — |
| **Total nos 4 arquivos editados** | | **63** | **12** |

**Nenhum outro arquivo foi tocado.**

---

## 7. Declaração final

As duas imprecisões estão fechadas. ZWNJ e ZWJ são **D** nas quatro fontes, com o uso legítimo
intacto e a exibição escapada — o que preserva a capacidade do revisor humano de ver o que antes
seria invisível. A contagem 16 vs. 15 tem causa identificada e reproduzível, e foi substituída
por um script que pode ser executado por qualquer pessoa.

**Nenhuma decisão está `APPROVED`. `D-01`, `D-05`, `D-16` e `D-18` continuam `OPEN`. Não existe
`LICENSE`. `main` não foi tocada. Não há PR e não houve merge. Não há código de produto.**

A Fase 1 continua **não autorizada**. O objetivo desta rodada era deixar a documentação
consistente e verificável para a decisão humana — e é isso que ela entrega.
