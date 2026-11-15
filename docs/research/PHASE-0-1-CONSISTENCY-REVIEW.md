# Fase 0.1 — Revisão de consistência e correção de recomendações

**Documento:** `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md`
**Sessão:** Agent 0.1 — Revisão antes da aprovação humana
**Data:** 2026-11-15 (UTC)
**Branch:** `arena/a92004be-lia-agenthub` (a mesma da Fase 0; ver §1.2)
**Natureza:** revisão documental corretiva. **Nenhuma implementação foi realizada.**

---

## 1. Método e escopo

### 1.1 O que esta revisão fez

Esta sessão **não** reabriu a investigação da Fase 0. Ela verificou sete pontos que o mandato
marcou como obrigatórios (R1–R7), confrontando cada um com **fonte oficial** e com o texto
realmente publicado na branch, e corrigiu o que não se sustentava.

**Regra aplicada:** uma correção só entra se houver evidência citável. Onde a evidência não
existe, o item fica `OPEN` com a lacuna declarada — não é preenchido por plausibilidade.

### 1.2 Sobre a branch

O mandato da §1 pede "criar sua própria branch a partir da branch-base". Já existe uma branch
de trabalho desta sessão (`arena/a92004be-lia-agenthub`), criada a partir de `main` @
`34a27f484e5f85987390a27fe7e0c0b3cd205bb2`, e o estado da sessão exige que todo trabalho
permaneça nela. Verificação de ancestralidade:

```
$ git merge-base --is-ancestor 34a27f48 HEAD && echo SIM
SIM
```

Portanto: a branch-base é `main` @ `34a27f48`, a branch de trabalho **é descendente** dele, e
não houve criação de branch paralela. Nenhum commit foi feito em `main`, nenhum merge foi
realizado. Esta decisão está declarada aqui em vez de silenciada.

### 1.3 O que esta revisão **não** fez

| Não feito | Motivo |
|---|---|
| Instalar `pywebview`, `pyinstaller`, `pythonnet`, `uv` ou qualquer pacote | Proibido pela §6 |
| Executar ferramenta de terceiros | Idem |
| Implementar o scanner Unicode | Proibido pela §6; aqui só há **política especificada** |
| Construir UI, CLI, instalador | Proibido pela §6 |
| Pesquisar isolamento Windows (`D-05`/`D-18`) | Continua aberto por decisão do mandato |
| Emitir parecer jurídico sobre licenças | Proibido pela §5 (R5) |

### 1.4 Limitações de acesso a fontes nesta rodada

| Fonte | Situação | Consequência |
|---|---|---|
| `devguide.python.org/versions/` | **Lida** por HTTP direto | `R1` tem fonte oficial primária |
| `pypi.org/pypi/<pkg>/json` | **Lido** por HTTP direto | `R1`/`R7` têm metadados oficiais de pacote |
| `registry.npmjs.org` | **Lido** por HTTP direto | `R7` (Electron/Tauri) tem fonte oficial |
| `unicode.org/reports/tr39/` (UTS #39) | **Lida** por HTTP direto | `R2` tem fonte normativa primária |
| `unicode.org/reports/tr9/` (UAX #9) | **Lida** por HTTP direto | `R2` tem fonte normativa primária |
| `unicode.org/Public/UCD/latest/ucd/PropList.txt` | **HTTP 000** — não baixado | `R2` **não** pôde ser validado contra a lista máquina-legível de `Default_Ignorable_Code_Point` desta versão do Unicode |
| `learn.microsoft.com` (WebView2) | **Não lido** por HTTP direto; extraído de busca | `R7` cita documentação Microsoft **via extração de busca**, não leitura direta |
| `THIRD_PARTY_NOTICES` do Studio/Forge | Não reaberto nesta rodada | A afirmação da Fase 0 permanece como estava, sem re-verificação |

**A limitação do `PropList.txt` é material para `R2`** e está registrada em §3.2.7.

---

## 2. Sumário das inconsistências encontradas

| # | Item | Severidade | Estado após esta rodada |
|---|---|---|---|
| **I-01** | Python 3.9 declarado como piso — **está em end-of-life desde 2025-10-31** | **Alta** — o único requisito técnico da stack que já nasceu morto | **Corrigido** — piso passa a 3.11, alvo 3.13 |
| **I-02** | Python 3.10 também está em EOL desde 2026-10-01; a Fase 0 só citava 3.9 | Alta | **Corrigido** |
| **I-03** | `pywebview` no Windows depende de `pythonnet`, que na versão atual exige **Python ≥ 3.11** — incompatível com o piso 3.9 proposto | **Alta** — a stack recomendada não monta | **Corrigido** — piso 3.11 resolve |
| **I-04** | Bloquear `U+200B–U+200F` indiscriminadamente rejeita **ZWNJ e ZWJ**, que são obrigatórios em persa, malaio, sinhala e em **todas as sequências de emoji ZWJ** | **Alta** — a política quebra texto legítimo e emoji | **Corrigido** — política por categoria |
| **I-05** | `U+E0000–U+E007F` classificado como ameaça pura; três bandeiras RGI (Inglaterra, Escócia, País de Gales) usam essa faixa legitimamente | Média | **Corrigido** — exceção RGI explícita |
| **I-06** | "Índice **assinado**" na arquitetura, quando assinatura criptográfica é fase futura e não pesquisada | **Alta** (honestidade do produto) | **Corrigido** — terminologia de integridade |
| **I-07** | M8 publicado no MVP e "integração com hosts" na Fase 3 — sem distinguir **publicar**, **validar**, **consumir de referência** e **integrar de verdade** | Média | **Corrigido** — quatro níveis separados |
| **I-08** | Exportação recusa `license: null` mesmo para **backup local**, confundindo operação privada com redistribuição | Média | **Corrigido** — política por destino |
| **I-09** | `LICENSE`, `THIRD_PARTY_NOTICES.md` e `.gitignore` ausentes | **Alta** (higiene de repositório) | **Parcial** — 2 de 3 criados; `LICENSE` retido por `D-16` |
| **I-10** | O mandato afirma que o README usa "índice assinado" — **o README não usa essa expressão** | Baixa (precisão do mandato) | **Registrado**, sem correção (não havia o que corrigir) |

---

## 3. Revisões R1–R7

### 3.1 R1 — Python e suporte de versões

#### 3.1.1 Evidência oficial

`https://devguide.python.org/versions/` — "Status of Python versions", lido em 2026-11-15:

| Branch | Status | Primeira release | End of life |
|---|---|---|---|
| 3.15 | **bugfix** | 2026-10-09 | 2031-10 |
| 3.14 | **bugfix** | 2025-10-07 | 2030-10 |
| 3.13 | security | 2024-10-07 | 2029-10 |
| 3.12 | security | 2023-10-02 | 2028-10 |
| 3.11 | security | 2022-10-24 | 2027-10 |
| **3.10** | **end-of-life** | 2021-10-04 | **2026-10-01** |
| **3.9** | **end-of-life** | 2020-10-05 | **2025-10-31** |

A mesma página define as fases via PEP 602: `security` = "only security fixes are accepted
and no more binaries are released"; `end-of-life` = "support ends. The release cycle is frozen;
no further changes are allowed".

**Conclusão factual:** em novembro de 2026, **3.9 e 3.10 não recebem mais nenhuma correção**,
nem de segurança. As linhas suportadas são **3.11, 3.12, 3.13, 3.14 e 3.15**.

#### 3.1.2 Metadados de empacotamento (fonte oficial: PyPI JSON API)

| Pacote | Versão em 2026-11-15 | `requires_python` | Classificadores | Licença declarada |
|---|---|---|---|---|
| `pyinstaller` | 6.22.3 | `<3.16,>=3.8` | 3.8 … 3.15 | GPLv2-or-later **com exceção** que permite empacotar código proprietário |
| `pywebview` | 6.2.1 | `>=3.8` | 3.7 … 3.13 | BSD 3-Clause |
| `pythonnet` | 3.2.1 | **`<3.16,>=3.11`** | **3.11** … 3.15 | *não declarada no metadado* |

`pythonnet` é dependência **incondicional no Windows** de `pywebview`
(`pythonnet; sys_platform == "win32"` em `requires_dist`). Histórico de `requires_python` do
`pythonnet`:

| Versão | `requires_python` |
|---|---|
| 3.0.1 – 3.0.2 | `>=3.7,<3.12` |
| 3.0.3 – 3.0.4 | `>=3.7,<3.13` |
| 3.0.5 | `>=3.7,<3.14` |
| 3.1.0 | `>=3.10,<3.15` |
| **3.2.0 – 3.2.1** | **`>=3.11,<3.16`** |

**Isto é o achado mais importante da revisão.** A Fase 0 recomendou "Python 3.9+" e, ao mesmo
tempo, listou `pywebview` como opção de camada de interface. Essas duas afirmações **não podem
ser verdadeiras ao mesmo tempo** com o `pythonnet` atual: uma instalação em 3.9 resolveria para
um `pythonnet` antigo ou falharia. A stack recomendada não monta.

#### 3.1.3 Recomendação corrigida

| Item | Antes (Fase 0) | **Depois (Fase 0.1)** | Por quê |
|---|---|---|---|
| Piso do núcleo (código que roda) | Python 3.9+ | **Python 3.11+** | 3.9 e 3.10 em EOL; 3.11 é a linha suportada mais antiga e tem EOL em 2027-10 |
| Versão-alvo do bundle `.exe` | não declarada | **Python 3.13.x** | `pyinstaller 6.22.3` suporta até 3.15; 3.13 está em `security` com EOL 2029-10 — janela longa e sem surpresa de bugfix |
| Versão usada no CI/dev | não declarada | **3.11 e 3.13** (matriz de duas) | 3.11 prova o piso; 3.13 prova o alvo |
| `pywebview` | "opcional, considerar" | **opcional, `EXTRA` da camada de UI**, nunca do núcleo | Ver §3.1.4 |

**Por que não 3.14 nem 3.15 como piso:** ambos estão em `bugfix`, o que é bom, mas elevam o piso
sem necessidade para um produto que usa pouca sintaxe nova. Piso mais alto reduz o número de
máquinas de desenvolvimento capazes de rodar o projeto sem instalar nada — e o núcleo é
stdlib-only, então não há ganho proporcional. `3.11` maximiza compatibilidade **dentro do
conjunto suportado**.

**Por que não 3.12 como alvo:** é uma escolha defensável. Optei por 3.13 porque é a primeira
linha com 2 anos de `bugfix` (PEP 719) e tem EOL em 2029-10, contra 2028-10 da 3.12. Se o
usuário preferir 3.12, nada na arquitetura muda — **é uma decisão de `D-14`, não uma
consequência**.

**O que muda na prática:** `match` (3.10), `tomllib` (3.11), `ExceptionGroup`/`except*` (3.11) e
`typing.Self` (3.11) passam a ser utilizáveis. Nada no desenho **depende** disso; o piso é sobre
segurança de runtime, não sobre conveniência de sintaxe.

#### 3.1.4 `pywebview` não é biblioteca padrão — e não é gratuita em dependências

Declaração explícita, como o mandato exige: **`pywebview` é um pacote de terceiros, não faz
parte da biblioteca padrão do Python.** No Windows ele arrasta:

- `pythonnet` (ponte CLR ↔ .NET, que é o que fala com WebView2)
- `proxy_tools`, `bottle` (servidor WSGI embutido), `typing_extensions`

E o `pywebview` **não é a única forma** de falar com WebView2. As três opções estão em `D-17`.

#### 3.1.5 Como manter o núcleo independente de framework

A regra já existia (L3 sem I/O), mas estava expressa de forma frouxa. Ficou assim:

| Camada | Pode importar | Não pode importar |
|---|---|---|
| **L3 — domínio** | **somente** `sys`, `os`(só `path`/constantes), `json`, `re`, `unicodedata`, `hashlib`, `posixpath`, `ntpath`, `dataclasses`, `enum`, `typing`, `datetime`, `uuid`, `zipfile`, `tempfile`, `shutil`, `textwrap`, `unicodedata` | **qualquer** coisa de L1/L2; `webview`; `flask`; `fastapi`; qualquer pacote de PyPI |
| **L2 — adaptadores** | stdlib + dependências declaradas por adaptador | lógica de domínio |
| **L1 — interface** | qualquer coisa, inclusive `pywebview` | chamar L2 diretamente |

**Teste verificável (não implementado, apenas especificado):** um teste que caminha todos os
`import` de L3 e falha se algum módulo não estiver numa allowlist explícita de stdlib. Isso
transforma "núcleo independente" de intenção em **gate de CI**. É barato porque é AST, não
execução.

#### 3.1.6 Compatibilidade PyInstaller × WebView2 × pywebview

| Combinação | Situação | Fonte |
|---|---|---|
| PyInstaller 6.22.3 + Python 3.13 | **Suportado** (classificadores incluem 3.13) | PyPI |
| PyInstaller 6.22.3 + Python 3.15 | **Suportado** (classificador 3.15) | PyPI |
| PyInstaller + `pywebview` + `pythonnet` | **Requer hook de empacotamento**; `pythonnet` carrega runtime .NET e DLLs nativas, que o PyInstaller precisa coletar | Não verificado nesta rodada — **`RESEARCH`** |
| PyInstaller + WebView2 | WebView2 **não** é empacotado junto no modo Evergreen: o app usa o runtime do sistema | Microsoft (via busca) |

**Honestidade:** eu **não** empacotei nada. A célula "requer hook" é a expectativa técnica
comum, não uma verificação. Está marcada `RESEARCH` e vira item obrigatório de F1c.

---

### 3.2 R2 — Unicode e caracteres invisíveis

#### 3.2.1 O que estava escrito

`SECURITY-AND-TRUST-MODEL.md` §3.2 dizia, textualmente:

> **Detecção automática:** Normalização NFKC + remoção/flag de: `U+E0000–E007F`,
> `U+200B–200F`, `U+2060–U+2064`, `U+202A–202E`, `U+FEFF` (fora de posição inicial)
>
> **Mitigação:** Rejeitar arquivo (não apenas avisar) quando houver caractere de controle
> invisível fora de whitespace conhecido

que, combinada com §6 da mesma página ("varrer Unicode invisível ← **rejeita** se encontrar"),
produz rejeição total de `U+200C` e `U+200D`. **Isso está errado** e é o defeito mais grave da
Fase 0 depois do Python.

#### 3.2.2 Por que está errado — evidência normativa

**UTS #39 §3.1.1 "Joining Controls"** (Unicode Security Mechanisms, lido em 2026-11-15):

> Visible distinctions created by certain characters excluded by the General Security Profile
> because their `Identifier_Type` is `Default_Ignorable` (particularly the *Join_Control*
> characters) **are necessary in certain languages**. **A blanket exclusion of these characters
> makes it impossible to create identifiers with the correct visual appearance for common words
> or phrases in those languages.**

> An implementation following the General Security Profile that allows the additional characters
> ZWJ and ZWNJ shall only permit them where they satisfy the conditions A1, A2, and B … **unless
> it documents the additional contexts where it allows them.**

E o princípio geral que a mesma especificação estabelece em §3:

> Deliberately restricting the characters that can be used in identifiers is an important
> security technique. **The exclusion of characters from identifiers does not affect the general
> use of those characters for other purposes, such as for general text in documents.**

Esta última frase é a que a Fase 0 violou: o `SKILL.md` é **texto em prosa**, não identificador.
Aplicar um perfil de identificador a prosa é a confusão de categorias que o próprio UTS #39
adverte contra.

#### 3.2.3 Os caracteres, um por um

Legenda de decisão:
`REJEITAR` = bloqueia a importação · `REVISAR` = aceita na quarentena, bloqueia a promoção até
um humano aprovar · `PRESERVAR` = aceito sem atrito · `ESCAPAR` = preservado no arquivo, exibido
com escape na UI

| Codepoint(s) | Nome | Uso legítimo real | Risco | **Decisão** |
|---|---|---|---|---|
| `U+200B` | ZERO WIDTH SPACE | Separador de linha em tailandês/lao/khmer; quebra de palavra em CJK; usado em URLs longas para permitir quebra | Esconde texto; quebra busca e igualdade de string; usado para inflar tokens | **REVISAR** — nunca rejeitar. Preserva o arquivo; exibe escapado; conta no relatório |
| `U+200C` | ZERO WIDTH NON-JOINER (ZWNJ) | **Obrigatório em persa** (รูป `نام` vs `نامه`, UTS #39 Fig. 1), **malaiala** (Fig. 2), e em várias escritas índicas para evitar conjunção | Pode esconder texto em contexto onde não é gramatical | **PRESERVAR** em prosa. **REJEITAR** apenas quando forma sequência anômala (ver §3.2.5) |
| `U+200D` | ZERO WIDTH JOINER (ZWJ) | **Todas as sequências de emoji ZWJ** (👨‍👩‍👧‍👦, 🏳️‍🌈), **sinhala** (UTS #39 Fig. 3), escrita indic | Idem | **PRESERVAR** em prosa. **REJEITAR** apenas em sequência anômala |
| `U+200E` | LEFT-TO-RIGHT MARK (LRM) | Marca direcional para texto latino dentro de parágrafo RTL (árabe/hebraico) — **muito usado em Israel e no mundo árabe** | Trojan Source quando em código | **REVISAR** — legítimo em prosa; nunca legítimo em bloco de código |
| `U+200F` | RIGHT-TO-LEFT MARK (RLM) | Mesmo, invertido | Idem | **REVISAR** |
| `U+061C` | ARABIC LETTER MARK (ALM) | Contraparte de LRM/RLM para texto árabe | Idem | **REVISAR** — **ausente da lista da Fase 0**, é lacuna |
| `U+202A`–`U+202E` | LRE, RLE, PDF, LRO, RLO | **Override** direcional: `RLO` inverte a ordem visual sem mudar o byte | **Trojan Source (CVE-2021-42574)** — reordena código exibido | **REJEITAR** em bloco de código; **REVISAR** em prosa (raríssimo em texto moderno; existe em texto árabe/hebraico antigo) |
| `U+2066`–`U+2069` | LRI, RLI, FSI, PDI — **isolates** | **Forma moderna e recomendada** pelo UAX #9 para texto bilíngue (substitui LRE/RLE/PDF) | Podem esconder texto | **REVISAR** — **ausentes da lista da Fase 0**, é lacuna |
| `U+2060` | WORD JOINER | Impede quebra de linha entre duas palavras (ex.: manter `R$ 1.000` junto) | Esconde texto | **REVISAR** |
| `U+2061`–`U+2064` | FUNCTION APPLICATION, INVISIBLE TIMES, INVISIBLE SEPARATOR, INVISIBLE PLUS | **Notação matemática**: `f(x)`, `2×3`, `A+B` invisíveis | Código matemático escondido | **REVISAR** — legítimo em documento técnico, suspeito em `SKILL.md` |
| `U+FEFF` | ZERO WIDTH NO-BREAK SPACE / BOM | **BOM legítimo** no byte 0 de arquivo UTF-8 de editores Windows | BOM quebra parser de frontmatter; no meio do texto, é invisível | **REJEITAR** se não estiver no byte 0. No byte 0, **normalizar e remover** com registro no relatório — nunca rejeitar, porque é o Notepad do Windows |
| `U+E0000`–`U+E007F` | TAG characters | **Exatamente três** sequências RGI: 🏴󠁧󠁢󠁥󠁮󠁧󠁿 (Inglaterra), 🏴󠁧󠁢󠁳󠁣󠁴󠁿 (Escócia), 🏴󠁧󠁢󠁷󠁬󠁳󠁿 (País de Gales) | **ASCII smuggling**: `U+E0020`–`U+E007E` espelham ASCII imprimível e são invisíveis. Um ataque pode esconder uma frase inteira em português dentro de uma bandeira | **REJEITAR** qualquer tag fora das 3 sequências RGI exatas. Dentro delas, **PRESERVAR** |
| `U+3164` | HANGUL FILLER | Preenchimento em composição Hangul | Nome que parece vazio (squatting) | **REVISAR** — não rejeitar; sinalizar se o campo for identificador |
| `U+115F`, `U+1160` | HANGUL CHOSEONG/JUNGSEONG FILLER | Composição Hangul | Idem | **REVISAR** |
| `U+00AD` | SOFT HYPHEN | Hifenização tipográfica legítima em pt-BR e dezenas de idiomas | Esconde caractere | **PRESERVAR** — rejeitar isso quebraria texto em português |
| `U+00A0` | NO-BREAK SPACE | Espaço não separável: `R$ 1.000`, `10 km` | Nenhum relevante | **PRESERVAR** — é whitespace, não control |
| `U+180E` | MONGOLIAN VOWEL SEPARATOR | Histórico; deixou de ser whitespace | Marginal | **REVISAR** |
| `U+FFF9`–`U+FFFB` | Interlinear annotation | Anotação de texto interlinear | Esconde texto | **REVISAR** |

#### 3.2.4 A política corrigida — quatro categorias

A regra deixa de ser uma denylist de faixas e passa a ser **três listas com semânticas
distintas**, aplicadas por **contexto** (prosa vs. identificador vs. bloco de código).

| Categoria | Semântica | Efeito na importação | Efeito na UI |
|---|---|---|---|
| **A — Rejeitar** | Não existe uso legítimo no contexto | Arquivo retorna para quarentena, importação bloqueada | Erro por linha/coluna, com codepoint e nome Unicode |
| **B — Sinalizar e exigir revisão** | Pode ser legítimo; precisa de olho humano | Importa para quarentena; **promoção para a biblioteca bloqueada** até revisão registrada | Destaque escapado, contagem, contexto de ±40 caracteres |
| **C — Preservar** | Legítimo e comum | Importa sem atrito | Nenhum aviso; aparece no relatório como "0 ocorrências" se não houver |
| **D — Preservar e exibir escapado** | Legítimo, mas invisível — o usuário **precisa ver** | Importa; byte preservado exatamente | Sempre exibido como `<U+200B>` em qualquer tela de revisão, nunca renderizado |

**Regra de contexto — a parte que faltava:**

| Contexto | Lista aplicada |
|---|---|
| **Prosa** (`description`, corpo do `SKILL.md`, `README`) | A = `U+202A–202E` apenas em bloco de código; `U+E0000–E007F` fora das 3 RGI. B = todo o resto de invisível. C/D = ZWNJ, ZWJ, NBSP, soft hyphen |
| **Identificador** (`name`, `id`, nome de arquivo, chave de frontmatter) | Perfil UTS #39 **General Security Profile**: só `Identifier_Status=Allowed` + Exception documentada. ZWNJ/ZWJ só nas condições A1/A2/B |
| **Bloco de código** (cerca ``` e conte\lúdo de `scripts/`) | `U+202A–202E`, `U+2066–2069`, `U+200E/200F/061C` → **A (rejeitar)**. São a assinatura de Trojan Source |

**Isto não enfraquece a proteção.** Trocar "rejeitar tudo" por "rejeitar o que é perigoso
naquele contexto, sinalizar o que é ambíguo, preservar o que é legítimo" aumenta o poder de
detecção: a Fase 0 **não cobria** `U+061C` nem `U+2066–2069`, que são exatamente os controles
que a recomendação moderna do UAX #9 prefere aos `U+202A–202E` antigos. Uma denylist de faixas
antigas dava falsa sensação de cobertura.

#### 3.2.5 As três exceções RGI — e por que não são backdoor

`U+E0000–U+E007F` merece tratamento explícito porque um "remova tudo" ali **quebra bandeiras
legítimas**, e um "preserve tags bem-formadas" **cria backdoor**:

```
🏴 + U+E0067 U+E0062 U+E0065 U+E006E U+E0067 + U+E007F   = Inglaterra   (gbeng)
🏴 + U+E0067 U+E0062 U+E0073 U+E0063 U+E0074 + U+E007F   = Escócia      (gbsct)
🏴 + U+E0067 U+E0062 U+E0077 U+E006C U+E0073 + U+E007F   = País de Gales (gbwls)
```

O padrão de tag do UTS #51 aceita **qualquer** caractere de `U+E0020` a `U+E007E`. Isso significa
que `🏴 + "digite isso" + U+E007F` é uma sequência **bem-formada** que carrega uma frase inteira
invisível. Um validador que aceita "tag sequence bem-formada" aceita o ataque.

**Regra adotada:** a única tag aceita é a **string literal exata** das três bandeiras RGI acima.
Toda outra ocorrência em `U+E0000–U+E007F` é categoria **A (rejeitar)** — inclusive sequências
bem-formadas, inclusive com uma única tag solta. Comparação por string exata, não por regex
genérica.

**Custo:** se o Unicode algum dia adicionar uma quarta bandeira de subdivisão, a allowlist
precisa de atualização de código. **Isso é aceitável** e é o mesmo trade-off que o projeto
`kinerary` documentou publicamente ao ser explorado pelo padrão permissivo (ver §3.2.6).

#### 3.2.6 Evidência de que o padrão permissivo é explorável

Um caso público documenta exatamente essa escalada: uma política que aceitava "qualquer
sequência de tag bem-formada" permitiu que uma "bandeira" carregasse até 32 caracteres ASCII
invisíveis, e o texto foi repassado "verbatim to the companion's model" — *ASCII smuggling*.
A correção foi restringir a **exatamente** as três bandeiras RGI. Isso é `RESEARCH` externo, não
verificação minha, e está marcado como tal. A lição é o que importa: **flexibilidade de formato
é superfície de ataque**.

#### 3.2.7 Normalização — e o que NFKC custa

A Fase 0 dizia "Normalização NFKC + remoção/flag". NFKC é agressiva: ela **altera** caracteres
legítimos (por exemplo, converte `ﬁ` ligadura em `fi`, e `①` em `1`). Se aplicada ao texto antes
de gravar, **muda o conteúdo do autor** — violação direta da regra de marca "o trabalho do
usuário pertence ao usuário".

**Correção de política:**

| Operação | Quando | Efeito nos bytes |
|---|---|---|
| **NFC** | Sempre, na comparação | Não muda conteúdo canônico |
| **NFKC** | **Nunca** para gravar; **só** para detectar homóglifo | Não persiste |
| **Remoção de BOM** (`U+FEFF` no byte 0) | No import | Registrada no relatório |
| **Qualquer outro stripping** | **Nunca** | — |

**Honestidade sobre esta seção:** não foi possível baixar `PropList.txt` (HTTP 000). Portanto a
lista de `Default_Ignorable_Code_Point` usada aqui vem do meu conhecimento do padrão e das
tabelas do UTS #39 lidas, **não** de uma tabela máquina-legível verificada desta versão do
Unicode. **Qualquer implementação precisa baixar `PropList.txt` e `DerivedCoreProperties.txt`
no momento do build e gerar a tabela a partir delas** — nunca digitar codepoints à mão. Isso
está registrado como pendência de F1a.

---

### 3.3 R3 — Escopo de M8 e integração com hosts

#### 3.3.1 O problema

A Fase 0 tinha, ao mesmo tempo:

- **M8 no MVP**: "Catálogo publicável `Comum\Capacidades\index.json` **que o host lê**"
- **Fase 3**: "integração com hosts"

Se o host já lê o índice no MVP, a Fase 3 não tem objeto. E a frase "que o host lê" sugere —
sem que seja verdade — que Studio ou Forge consomem o contrato **hoje**. A auditoria da Fase 0
prova o contrário: nenhum dos dois lê `index.json`.

#### 3.3.2 Os quatro níveis, separados

| Nível | O que é | Depende de Studio/Forge? | **Fase** |
|---|---|---|---|
| **IDX-1 — Publicar** | O Hub **escreve** `Comum\Capacidades\index.json` + `index.schema.json`, de forma atômica, sempre que a biblioteca muda | **Não** | **MVP (M8)** |
| **IDX-2 — Validar** | O Hub valida o índice contra o próprio schema e recusa publicar se estiver inconsistente | **Não** | **MVP (M8)** |
| **IDX-3 — Consumir de referência** | Um **leitor mínimo** de referência (documentado, ~50 linhas, fora do Hub) prova que o contrato é consumível sem o Hub | **Não** | **MVP (M8)** |
| **IDX-4 — Integrar de verdade** | Studio e Forge passam a ler o índice e a exibir `trust`/`license`/`requirements` | **Sim** | **Fase 3** |

#### 3.3.3 Recomendação

**M8 permanece no MVP, com o escopo redefinido para IDX-1+IDX-2+IDX-3.** A frase "que o host lê" sai e
vira "que um host **pode** ler".

Justificativa:
1. **Publicar é escrever arquivo.** Não requer rede, não requer o Studio, não requer nada além
   do que M1–M7 já produzem. É a menor unidade de valor de distribuição.
2. **Sem IDX-3, M8 é uma afirmação não testada.** Publicar um contrato que ninguém jamais leu é
   indefensável no padrão de honestidade que o resto do documento exige. O leitor de referência
   é barato e transforma o contrato em algo **verificado**.
3. **IDX-4 fora do MVP** é obrigatório: requer alterar Studio e Forge, o que esta fase proíbe e o
   escopo do Hub não inclui.

**Critério de aceite corrigido para M8:**

| Critério | Como é verificado |
|---|---|
| O índice é escrito atomicamente | Kill do processo no meio da escrita não deixa `index.json` truncado |
| O índice valida contra `index.schema.json` | Schema versionado no repositório; validação no publish |
| Um consumidor sem o Hub lê o índice | Leitor de referência roda com o Hub **desinstalado** e imprime as capacidades |
| O índice declara o que não sabe | Campos `null` aparecem como `null`, nunca como valor inventado |
| O índice **não** é assinado | Ver §3.4 |

#### 3.3.4 Correção de texto

- `MVP-AND-ROADMAP.md` M8: reescrito com IDX-1…IDX-4 explícitos.
- `PHASE-0-FINAL-REPORT.md`: a linha "índice" no resumo passa a "índice publicável + leitor de
  referência".
- `PLATFORM-AND-TECHNOLOGY-DECISION.md` não menciona M8 — sem alteração.

---

### 3.4 R4 — Integridade e assinatura

#### 3.4.1 O que estava errado

`PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` linha 100, no diagrama de fluxo:

```
│  Índice assinado (manifest + hashes)     │
```

ao mesmo tempo que:

- `D-11` / `SECURITY-AND-TRUST-MODEL.md` §3.7 dizem "Para provar autoria é necessário assinatura
  (Sigstore/minisign) — **não pesquisado nesta fase**"
- `INTEGRATION-CANDIDATES.md` §9 lista "Assinatura de pacote (Sigstore, minisign)" como
  **não pesquisado**
- `MVP-AND-ROADMAP.md` lista assinatura como **fora do MVP**

"Índice assinado" afirma uma capacidade que o produto **não tem e não pesquisou**. É exatamente
o tipo de alegação que a regra de marca proíbe.

#### 3.4.2 Sobre o README

O mandato afirma que "o README usa a expressão 'índice assinado'". **Verifiquei: o README não
contém essa expressão, nem a palavra "hash", nem "index.json".** A ocorrência está na
arquitetura. Registro isto como **I-10** porque a diferença importa: se eu tivesse "corrigido"
o README conforme instruído, teria inventado um defeito para parecer diligente. O README foi
revisado e **não precisou de correção de terminologia**.

#### 3.4.3 Vocabulário corrigido — seis conceitos, seis nomes

| Conceito | Nome correto | O que prova | O que **não** prova | Estado no Hub |
|---|---|---|---|---|
| **Hash por arquivo** | `contentHash` (SHA-256) | Que aquele arquivo não mudou desde a importação | Nada sobre origem, autoria ou intenção | **MVP** |
| **Hash da árvore** | `treeHash` (SHA-256 sobre manifesto ordenado de caminho+hash) | Que o **conjunto** de arquivos não mudou — pega arquivo adicionado ou removido, não só alterado | Nada sobre origem | **MVP** |
| **Integridade do pacote** | `packageHash` | Que o ZIP `.lia-capability` não foi corrompido no transporte | Nada sobre origem | **MVP** |
| **Assinatura criptográfica** | `signature` (minisign/Sigstore) | Que **quem assinou** possuía a chave privada | Nada sobre se o conteúdo é seguro | **Fora do MVP** — `RESEARCH` pendente |
| **Identidade do autor** | `author` (campo declarado) | **O que o autor afirma sobre si** — é declaração, não prova | Nada. Qualquer um digita qualquer nome | **MVP, como declaração** |
| **Proveniência** | `provenance` (URL, commit, data, método, `contentHash` no momento da captura) | **De onde o Hub diz que veio**, reconstruível por terceiro que vá à fonte | Nada, se a fonte for privada ou tiver mudado | **MVP** |

**Regra de redação, para todo o repositório:**

| Proibido | Usar em vez disso |
|---|---|
| "índice assinado" | "índice com hashes", "índice verificável" |
| "assinatura verificada" | — (não existe assinatura no MVP) |
| "pacote autêntico" | "pacote com integridade verificada" |
| "autor verificado" | "autor declarado" |
| "seguro" (para resultado de scanner) | "sem achados nesta verificação" |
| "aprovado" (para scanner) | "revisado por `<pessoa>` em `<data>`" |
| "proveniência verificada" | "proveniência declarada, rastreável em `<URL>`" |

#### 3.4.4 Correções aplicadas

| Arquivo | Antes | Depois |
|---|---|---|
| `PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` | "Índice assinado (manifest + hashes)" | "Índice com hashes (manifest + contentHash/treeHash) — **não assinado**" |
| `PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §8 (pacote) | Pasta `signatures/` "reservada" sem explicação | Renomeada com nota: "reservado; **não usado no MVP**; nenhum código lê este diretório" |
| `SECURITY-AND-TRUST-MODEL.md` §3.7 | Título "Integridade, senha e assinatura" misturava três coisas | Título "Integridade, hash e assinatura (não implementada)"; tabela de seis conceitos |
| `DATA-STORAGE-AND-PORTABILITY.md` §5.1 | "Coleção (ZIP com N capacidades + índice)" | "+ `index.json` do próprio pacote (não assinado)" |
| `DECISION-REGISTER.md` `D-21` | "`signatures/` reservado" | Idem + nota de que reservar pasta **não** é implementar assinatura |

**Nenhuma dessas correções remove a assinatura do roadmap.** Ela continua sendo Fase 3+, marcada
`RESEARCH`. A correção é de **vocabulário**, para que o produto não afirme o que não faz.

---

### 3.5 R5 — Licença e exportação privada

#### 3.5.1 O problema

`DATA-STORAGE-AND-PORTABILITY.md` §5.2 recusava exportar quando `license: null`. Mas "exportar"
cobria **três coisas diferentes**:

- gerar `.lia-capability` para **si mesmo** guardar
- gerar `.lia-capability` para **outra máquina sua**
- gerar `.lia-capability` para **enviar a terceiro**

Recusar tudo isso por causa de metadado ausente **pune o usuário por organizar a própria
biblioteca** e confunde duas questões jurídicas distintas: *"posso usar isto?"* e *"posso
redistribuir isto?"*. A própria marca diz que o trabalho do usuário pertence ao usuário e deve
ser "acessível, copiável, exportável e removível".

#### 3.5.2 A distinção que faltava

| Operação | Quem recebe o conteúdo | Natureza | Risco jurídico | Política |
|---|---|---|---|---|
| **Backup local** | Ninguém — cópia no mesmo disco/pendrive do usuário | Privada | **Nenhum** | **Sempre permitido.** Não é exportação; é cópia de arquivo. O Hub não interfere |
| **Transferência entre máquinas do mesmo usuário** | O próprio usuário | Privada | **Nenhum** | **Permitido.** `target: self`. Avisos, sem bloqueio |
| **Exportação privada para guarda** | O próprio usuário | Privada | **Nenhum** | **Permitido**, com `target: private` registrado no manifesto |
| **Compartilhamento com pessoa próxima** | Um terceiro identificado | Limitada | **Baixo**, mas real: a licença pode vedar distribuição | **Permitido com aviso explícito e registro de `target: shared`** |
| **Redistribuição pública** | Qualquer um | Pública | **Alto** | **Bloqueado sem direitos comprovados** (`redistributable: true` com evidência) |

**Regra nova:** a decisão não é mais "tem `license`?" — é **"para onde vai?"**.

```
permitido_exportar(capacidade, destino):
    destino == private  → SEMPRE sim
    destino == shared   → sim, com aviso; never bloqueia por licença desconhecida
                          mas exige confirmação explícita de que o usuário leu o aviso
    destino == public   → só se capacidade.redistributable is True
                          e capacidade.license.redistribution_basis != null
```

#### 3.5.3 O que **continua bloqueado**

| Operação | Bloqueio | Motivo |
|---|---|---|
| Marcar `redistributable: true` sem registro de base | **Sim** | É a única afirmação que pode causar dano a terceiro |
| Publicar em catálogo compartilhado | **Sim** | Depende de `license` revisada |
| Incluir capacidade com `license: null` em `.lia-collection` marcada como pública | **Sim** | Herda a regra acima |
| Exportar conteúdo de capacidade que declara `secrets.envVars` com valores | **Sim, sempre** | Nunca exporta valores, em nenhum destino |

#### 3.5.4 O aviso, não o bloqueio

Toda exportação `shared`/`public` carrega um aviso que o usuário precisa **ter visto** (não
necessariamente aceito, para `shared`):

> Esta capacidade não tem licença registrada ou tem licença não revisada. **Você** está
> decidindo compartilhá-la. O Lia Agent Hub não verificou se você tem o direito de
> redistribuí-la, e não pode verificar. O pacote leva `license: null` para que quem receber
> saiba o mesmo que você sabe.

Isso implementa a regra de marca "nunca esconde custo, risco, transmissão de dados ou ação
irreversível" **sem** o Hub fingir ser advogado.

#### 3.5.5 Declaração de limite — não é parecer jurídico

**O Hub não avalia se o usuário tem direito de redistribuir.** Ele registra o que o autor
declarou e impede a única operação de alto risco (publicação) na ausência de declaração. A
distinção entre uso privado e redistribuição pública é a única linha que o produto aplica, e ela
é conservadora de propósito.

**Incerteza jurídica registrada como decisão humana** — ver `D-25` no registro.

---

### 3.6 R6 — Governança e arquivos fundamentais

#### 3.6.1 Estado verificado

| Arquivo | Estado antes | Ação nesta rodada |
|---|---|---|
| `LICENSE` | **AUSENTE** | **Não criado** — `D-16` continua aberta e é decisão humana. Escolher MIT/Apache unilateralmente violaria o mandato |
| `THIRD_PARTY_NOTICES.md` | **AUSENTE** | **Criado** — registra que a Fase 0 não incorporou código de terceiros |
| `.gitignore` | **AUSENTE** | **Criado** — adaptado do kit |

#### 3.6.2 `THIRD_PARTY_NOTICES.md` — o que ele diz e por que é honesto

O arquivo precisa afirmar algo verificável, não uma fórmula vazia. A auditoria da Fase 0
encontrou:

- **Nenhum** código de terceiros foi copiado para este repositório
- **Nenhuma** dependência foi instalada
- O único conteúdo não-Markdown versionado é `docs/KIT-PROJETO-NOVO.zip`, **fornecido pelo
  próprio projeto**, não de terceiro
- As oito Skills do Studio são adaptadas de fontes MIT **no repositório do Studio** — não aqui

Portanto o arquivo registra: *nada incorporado*, com a lista do que **será** necessário registrar
quando houver código (PyInstaller com sua exceção de licença, `pywebview` BSD, `pythonnet`, e
qualquer coisa que venha do ecossistema).

**Ponto de atenção registrado no próprio arquivo:** PyInstaller é **GPLv2-or-later com exceção**
que permite empacotar software proprietário. A exceção é o que torna o bundling possível; sem
ela, o `.exe` seria obra derivada de GPL. Isso **precisa** estar no `THIRD_PARTY_NOTICES.md` no
momento em que PyInstaller for usado — não depois.

#### 3.6.3 `.gitignore` — adaptado, não copiado

O kit fornece `gitignore-acrescentar.txt` (bloco "acrescentar", para colar num arquivo
existente). Este repositório **não tem** `.gitignore`, então o arquivo foi **montado**, não
colado.

| Regra do kit | Adotada? | Justificativa |
|---|---|---|
| `.claude/skills/` | **Sim** | Junction-espelho; Git no Windows commitaria duplicado |
| `.claude/worktrees/` | **Sim** | Idem |
| `.claude/settings.local.json` | **Sim** | Config local com segredo |
| `build/`, `dist/`, `*.spec` | **Sim** | Build de PyInstaller |
| `__pycache__/`, `*.py[cod]`, `.venv/` | **Sim** | Python |
| `*.log` | **Sim** | Log local |
| `node_modules/`, `.vite/` | **Sim** (bloco web) | Vem do kit mobile/web; o repositório pode receber ferramenta Node no futuro |
| `android/`, `ios/` | **Não** | O produto é desktop Windows; essas pastas não existem e não vão existir. Regra que "prevê" o que não existe esconde o fato de que ninguém pensou sobre isso |
| `.env`, `.env.*`, `!.env.example` | **Sim** | Nenhum segredo em arquivo versionado |

**Regras acrescentadas além do kit** (porque este projeto tem riscos que o kit não previu):

| Regra | Por quê |
|---|---|
| `/Lia/` e `/**/Lia/` | O padrão de dados da marca cria `<raiz>/Lia/`. Se alguém rodar o app do fonte **dentro** do repositório, dados de usuário nasceriam aqui. Isso precisa ser impossível de commitar |
| `*.lia-capability`, `*.lia-collection`, `index.json` em raízes de fixture | Artefatos de teste binários não pertencem ao Git |
| `.venv*/`, `venv/` | Variantes comuns |
| `.pytest_cache/`, `.ruff_cache/`, `.mypy_cache/` | Caches de ferramenta |
| `.idea/`, `.vscode/` **exceto** `settings.json`/`extensions.json` | Config de IDE é local, mas recomendações compartilhadas **são** versionáveis — a exceção evita a armadilha de ignorar `.vscode/` inteiro (mesma lição do `.claude/`) |
| `Thumbs.db`, `desktop.ini`, `.DS_Store` | Ruído de SO |
| `*.pem`, `*.key`, `*.pfx`, `*.p12`, `id_rsa*` | Nunca commitar material de chave, mesmo que alguém tente |

**O que o `.gitignore` deliberadamente NÃO ignora:** `docs/`, `THIRD_PARTY_NOTICES.md`,
`AGENTS.md`, `.claude/rules/` — pelo motivo que o próprio kit destaca em maiúsculas ("nao ignore
`.claude/` inteiro — as regras de projeto ficam em `.claude/rules/` e PRECISAM ser versionadas").
O `.gitignore` tem um comentário explícito sobre isso para que ninguém "limpe" o arquivo depois.

---

### 3.7 R7 — Stack e WebView2

#### 3.7.1 WebView2 pode estar ausente — sim

Evidência (documentação Microsoft, via extração de busca — **não** lida por HTTP direto):

- O runtime **Evergreen** vem **pré-instalado** no Windows 11.
- No Windows 10, a Microsoft instalou o runtime "em todos os dispositivos elegíveis" — mas
  **não em todos**: instalações limpas antigas, **LTSC**, **Windows Server** e algumas máquinas
  gerenciadas podem não ter.
- A própria Microsoft recomenda: *"Even if your app uses the Evergreen distribution mode, we
  recommend that you distribute the WebView2 Runtime, to cover edge cases where the Runtime
  wasn't already installed."*
- A verificação documentada é o valor de registro `pv` em `HKLM` (per-machine) ou `HKCU`
  (per-user); **pelo menos um** deve existir com versão > `0.0.0.0`.
- O bootstrapper Evergreen tem ~2 MB e aceita `/silent /install`.

**Consequência para o produto:** WebView2 **não** pode ser presumido.

#### 3.7.2 Estratégia de detecção e mensagem

| Situação | Detecção | Comportamento |
|---|---|---|
| Runtime presente | Chave `pv` > 0.0.0.0 | Sobe a UI normalmente |
| Runtime ausente, **online** | Idem | Sobe a **UI de fallback** (ver abaixo) e oferece baixar o bootstrapper oficial — **com link para microsoft.com**, nunca download silencioso |
| Runtime ausente, **offline** | Idem | UI de fallback + instrução de usar o instalador offline da Microsoft |
| Runtime presente mas quebrado | Falha ao criar o control | Mesma UI de fallback, com diagnóstico |

**A decisão de arquitetura que resolve isto:** a UI é **web servida em `127.0.0.1`**. Isso
significa que, se o WebView2 não existir, o usuário pode **abrir a mesma interface no Edge ou no
Firefox** apontando para o endereço local. O produto não fica inutilizável — degrada para
navegador. Essa é a razão técnica de a UI ser web local em vez de um toolkit nativo: **o fallback
é gratuito**.

Isto **não** transforma o Hub em produto web: ele continua desktop, local, sem servidor remoto.

#### 3.7.3 `pywebview` — dependências e o que muda

| Item | Fato |
|---|---|
| Versão | 6.2.1 |
| Licença | BSD 3-Clause |
| Dependência Windows | **`pythonnet`** (obrigatória) |
| `pythonnet` exige | **Python ≥ 3.11** na versão 3.2.x |
| Outras dependências | `proxy_tools`, `bottle`, `typing_extensions` |
| Empacotamento com PyInstaller | Requer coletar runtime .NET e DLLs nativas — **não verificado** |

**Consequência:** adotar `pywebview` ata o piso de Python a **≥ 3.11** e adiciona uma ponte CLR
ao processo. Uma alternativa é **não** usar `pywebview` e falar com WebView2 diretamente ou via
uma janela de navegador (`webbrowser.open`), que não tem dependência nenhuma.

As três opções entram em `D-17` como alternativas explícitas, com custo medido:

| Opção | Dependências | Tamanho aproximado no instalador | Fallback se WebView2 ausente | Risco |
|---|---|---|---|---|
| **A — `pywebview`** | `pythonnet`, `bottle`, `proxy_tools`, `typing_extensions` | +~10–20 MB (runtime .NET não vai junto; usa o do SO) | Aponta para navegador | Ponho dependência CLR num produto cujo núcleo é stdlib |
| **B — `webbrowser.open` (navegador do sistema)** | **Nenhuma** | **0** | É o navegador | Janela sem "cara de app"; usuário vê aba do navegador |
| **C — `pywebview` atrás de `EXTRA` opcional** | Só se instalado | 0 se não instalado | Navegador | Duas rotas de UI para manter e testar |

**Recomendação:** **B no MVP (F1b)**, com C como evolução. Razão: o núcleo stdlib é o ativo mais
valioso do desenho; trocá-lo por uma ponte CLR para ganhar uma moldura de janela é um mau
negócio em F1b, quando o objetivo é provar o domínio. **Isto é `D-17`, não uma decisão tomada.**

#### 3.7.4 Bind em `127.0.0.1` e proteção de origem

Se a UI é servida localmente, três coisas precisam ser verdade — e nenhuma delas é automática:

| Risco | Controle |
|---|---|
| Outra máquina acessa a UI | Bind **exclusivo** em `127.0.0.1`, **nunca** `0.0.0.0`. Verificar no código, não na intenção |
| Outro processo local acessa a UI | **Token de sessão** gerado no start, exigido em toda requisição, entregue à janela na URL |
| Página web aberta no navegador faz requisição à UI (CSRF/DNS rebinding) | `Origin`/`Host` validados contra `127.0.0.1:<porta>`; rejeitar `null` e qualquer origem externa; **sem** CORS permissivo |
| Porta fixa colide | Porta efêmera + injeção da URL real na janela |

**Distinção que a Fase 0 não fazia explicitamente:**

| | Interface local | API de integração |
|---|---|---|
| Para quem | O usuário, na tela | Outros programas |
| Transporte | HTTP em `127.0.0.1:<porta efêmera>` | **Nenhum no MVP** — arquivo em disco |
| Estabilidade | Pode mudar entre versões | Seria contrato versionado |
| Autenticação | Token de sessão | N/A |
| **No MVP?** | **Sim (F1b)** | **Não** |

O contrato de integração do MVP continua sendo **arquivo**, não HTTP.

#### 3.7.5 Caminhos em modo fonte e modo empacotado

| Recurso | Do fonte | Do `.exe` |
|---|---|---|
| Recursos do app (HTML, CSS, schema) | `src/lia_agenthub/resources/` | `sys._MEIPASS` (PyInstaller onefile) |
| Dados do usuário | `Lia\AgentHub\` sob `%USERPROFILE%` | **Idêntico** |
| Config | `%APPDATA%\Lia\AgentHub\config\` | **Idêntico** |
| Cache/log | `%LOCALAPPDATA%\Lia\AgentHub\` | **Idêntico** |

**Regra do kit, mantida:** um único módulo resolve todos os caminhos e expõe `--diagnostico`. Se
outro módulo montar caminho na mão, os dois modos divergem — e o bug só aparece no `.exe`.

#### 3.7.6 Comparação revalidada — com números

Critérios da Fase 0 mantidos (K1–K8, K1+K2 = 45 % e são veto). O que muda é que agora há dados
verificados.

| | **A: Python stdlib + web local** | **B: Electron** | **C: Tauri 2** |
|---|---|---|---|
| Runtime exigido do usuário | **Nenhum** (3.11+ só no build) | Chromium ~150–200 MB por app | WebView2 (vem no W11) |
| Runtime de build | Python + PyInstaller | Node **≥ 22.12** | Rust + Node |
| Licença da ferramenta | PyInstaller GPLv2 **+ exceção** | MIT | Apache-2.0 OR MIT |
| Dependência pesada | Nenhuma no núcleo | Chromium inteiro, por app | Toolchain Rust |
| Núcleo independente de framework | **Sim, por desenho** | Não — o main process é Node/Electron | Não — o core é Rust |
| Fallback se o runtime de UI faltar | **Navegador** | Nenhum (Chromium vai junto) | Navegador** |
| Tamanho do instalador | **~15–30 MB estimado** | ~80–150 MB | ~5–10 MB |
| Maturidade | Alta | Muito alta | Média-alta |
| Custo de contribuição | Baixo (Python) | Médio (Node) | **Alto (Rust)** |

\*\* Tauri usa WebView2 no Windows, então herda o mesmo risco de ausência — mas **não** tem o
fallback de navegador embutido; teria que ser construído.

**Conclusão revalidada: A continua recomendada.** O argumento não é preferência de linguagem. É
que K1 ("usuário não instala runtime") e K2 ("domínio independente de framework") são vétos, e
A é a **única** que passa nos dois sem esforço adicional. B falha K1 por construção (Chromium
por app). C falha no custo de contribuição e não traz ganho de K1/K2 sobre A.

**O que realmente mudou nesta revisão:** A ficou **mais** defensável, porque a estratégia de
fallback (§3.7.2) transforma a fraqueza do WebView2 em vantagem — e o custo de B e C (trazer
runtime) é exatamente o que K1 proíbe.

---

## 4. Coerência entre documentos — verificação final

Depois das correções, os oito pares de tensão que o mandato listou:

| Tensão | Resolução | Onde |
|---|---|---|
| **MVP vs. Fase 3** | M8 = publicar + validar + leitor de referência (IDX-1–IDX-3). Integração real (IDX-4) = Fase 3 | §3.3, `MVP-AND-ROADMAP.md` |
| **Hash vs. assinatura** | Seis conceitos nomeados; "assinado" removido de todo o repositório | §3.4 |
| **Declarado vs. testado** | Toda tabela mantém classificação; novas afirmações desta rodada marcadas com fonte ou `RESEARCH` | Todo o documento |
| **Validação estrutural vs. de segurança** | Estrutural = schema, frontmatter, paths (determinística). Segurança = só evidência, nunca aprovação | `SECURITY-AND-TRUST-MODEL.md` §6 |
| **O Hub publica / o host consome** | Hub **publica** arquivo; consumo é do host, opcional, e nenhum host consome hoje | §3.3.2 |
| **Exportável vs. redistribuível** | Política por destino; public é o único bloqueio duro | §3.5 |
| **O que funciona sem internet** | Tudo do MVP. A única exceção é o download do bootstrapper WebView2, que é **opcional e do usuário** | §3.7.2 |
| **Hub vs. Studio vs. Forge vs. Waifu** | Nenhuma alteração de fronteira nesta rodada. Waifu continua opcional e não aparece em nenhuma dependência | `PRODUCT-BOUNDARIES` §1.3 |

**Varredura de termos proibidos após as correções:** "índice assinado" e "assinatura verificada"
têm **zero ocorrências**. As únicas ocorrências de "assinad" restantes se referem a
(a) `.exe` do Forge que não foi assinado, e (b) assinatura de pacote listada como `RESEARCH`
pendente. Ambas estão corretas.

---

## 5. Registro de decisões — o que mudou

| Decisão | Antes | Depois | Motivo |
|---|---|---|---|
| `D-14` (stack) | Recomendava Python 3.9+ | Recomenda **3.11+ / alvo 3.13** | `R1` — 3.9 e 3.10 em EOL |
| `D-17` (sistemas operacionais) | — | **Não alterada.** É sobre SO, não sobre biblioteca de UI. Recebeu nota remetendo a `D-27` | `R7` — a pergunta era de outra decisão |
| `D-25` (**nova**) | — | Política de exportação por destino | `R5` |
| `D-26` (**nova**) | — | Política Unicode por categoria e contexto | `R2` |
| `D-27` (**nova**) | — | Biblioteca de interface: `pywebview` vs. navegador do sistema | `R7` |
| `D-21` (pacote) | `signatures/` "reservado" | Idem, com nota de que reservar ≠ implementar | `R4` |
| `D-16` (licença) | Aberta | **Continua aberta** — não tocada | Mandato |
| `D-05`, `D-18` | Abertas | **Continuam abertas** | Mandato |
| `D-13`, `D-03`, `D-06` | `RECOMMENDED` | **Continuam `RECOMMENDED`** | Mandato |

**Nenhuma decisão foi marcada `APPROVED`.** Contagem final: **27 decisões** (`D-01`…`D-27`).

---

## 6. Questões que permanecem abertas

| # | Questão | Por que não foi resolvida | Quem decide |
|---|---|---|---|
| **Q-01** | Qual licença para este repositório | `D-16` é decisão humana; escolher seria violar o mandato | Usuário |
| **Q-02** | `pywebview` vs. navegador do sistema | Ambas viáveis; depende de tolerância a dependência CLR | Usuário (`D-17`) |
| **Q-03** | Alvo 3.12 vs. 3.13 | Ambas suportadas; 3.13 tem EOL maior | Usuário (`D-14`) |
| **Q-04** | Isolamento Windows | Precisa de máquina Windows real; não há no sandbox | Agent 3 (`D-05`/`D-18`) |
| **Q-05** | Lista `Default_Ignorable` desta versão do Unicode | `PropList.txt` inacessível (HTTP 000) | F1a — baixar no build |
| **Q-06** | Hook de PyInstaller para `pythonnet` | Só se confirma empacotando | F1c |
| **Q-07** | `canirunai.kc1t.com` | Continua não alcançável; herda da Fase 0 | Usuário |
| **Q-08** | Licenciamento do Obsidian | `RESEARCH (não verificada)` desde a Fase 0 | Usuário |

---

## 7. Confirmação de ausência de implementação

| Restrição da §6 | Cumprida? | Evidência |
|---|---|---|
| Não implementar código de produto | **Sim** | `git ls-files` não retorna nenhum arquivo executável ou de código; apenas `.md`, `.gitignore` e o `.zip` do kit |
| Não instalar dependências | **Sim** | Nenhum `pip install`, nenhum `venv` no repositório |
| Não executar ferramentas de terceiros | **Sim** | `pywebview`, `pyinstaller`, `pythonnet`, `uv` foram **consultados via API de metadados**, nunca instalados ou executados |
| Não implementar o scanner Unicode | **Sim** | §3.2 é **política especificada**, sem código |
| Não construir interface ou CLI | **Sim** | Nenhum arquivo em `src/` existe |
| Não criar instalador | **Sim** | Idem |
| Não alterar Studio, Forge ou Project | **Sim** | Nenhum clone nesta sessão; nenhum push para outros repositórios |
| Não implementar Test Lab | **Sim** | `D-05`/`D-18` intocadas |
| Não integrar MCPVault, Graphify, ai-memory, Obsidian | **Sim** | Nenhuma dependência adicionada |
| Não abrir PR nem fazer merge | **Sim** | Nenhum `gh pr create`; nenhum merge |
| Não alterar `main` | **Sim** | `origin/main` continua em `34a27f48` |
| Não criar `LICENSE` | **Sim** | Continua ausente, por decisão |
| Não marcar decisão como `APPROVED` | **Sim** | 0 de 27 |

**Contagem de decisões após esta rodada:**

| Estado | Decisões | Quantidade |
|---|---|---|
| `OPEN` | `D-01`, `D-05`, `D-16`, `D-18` | **4** |
| `RECOMMENDED` | `D-02`–`D-04`, `D-06`–`D-11`, `D-13`–`D-15`, `D-17`, `D-19`–`D-27` | **22** |
| `DEFERRED` | `D-12` | **1** |
| **`APPROVED`** | — | **0** |
| **Total** | | **27** |

`D-25`, `D-26` e `D-27` são novas; nascem `RECOMMENDED` e **não** aprovadas.

---

## 8. Arquivos criados e alterados nesta rodada

### Criados

| Arquivo | Natureza |
|---|---|
| `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` | Este documento |
| `.gitignore` | Higiene de repositório, adaptado do kit |
| `THIRD_PARTY_NOTICES.md` | Registro inicial: nenhum código de terceiros incorporado |

### Alterados

| Arquivo | Alteração |
|---|---|
| `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` | Piso Python 3.11/Alvo 3.13; tabela de dependências verificadas; três opções de UI; estratégia WebView2 ausente |
| `docs/product/MVP-AND-ROADMAP.md` | M8 redefinido em IDX-1–IDX-3; IDX-4 na Fase 3 |
| `docs/architecture/SECURITY-AND-TRUST-MODEL.md` | §3.2 reescrita (política Unicode por categoria); §3.7 renomeada; seis conceitos de integridade |
| `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` | "Índice assinado" → "índice com hashes"; nota em `signatures/` |
| `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` | §5.2 política por destino; §8 nota de índice não assinado |
| `docs/DECISION-REGISTER.md` | `D-14`, `D-17` revisadas; `D-21` com nota; **`D-25`, `D-26` novas** |
| `docs/PHASE-0-FINAL-REPORT.md` | Resumo de M8; remissão a esta revisão; L11/L12 |
| `README.md` | Estado Fase 0.1; links novos |

---

## 9. Declaração final

A Fase 0 tinha **um erro grave repetido em seis documentos** (Python 3.9 como piso) e **um erro
grave em um documento de segurança** (rejeição indiscriminada de Unicode invisível). Os dois
foram encontrados porque o mandato exigiu fonte oficial — não porque eu já soubesse.

O que esta revisão **não** fez foi transformar correção em aprovação. A stack mudou de 3.9 para
3.11 e o piso continua sendo `RECOMMENDED`, não `APPROVED`. A política Unicode está especificada
e não implementada. O `LICENSE` continua ausente porque a decisão não é minha.

**A pergunta que esta revisão deixa para o usuário humano é uma só:** as quatro decisões que
destravam a Fase 1 (`D-13`, `D-14`, `D-03`, `D-06`) mais `D-16` (licença) podem ser revisadas
agora — com o piso de Python corrigido, o escopo de M8 separado e a política de exportação
distinguindo privado de público.
