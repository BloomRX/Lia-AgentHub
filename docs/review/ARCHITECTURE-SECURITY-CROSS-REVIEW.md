# Revisão cruzada — Architecture/Security: Skills, licenciamento, proveniência e contratos

**Documento:** `docs/review/ARCHITECTURE-SECURITY-CROSS-REVIEW.md`
**Papel:** revisão independente (Architecture/Security) da pesquisa de Skills do ecossistema Lia.
**Branch desta revisão:** `arena/1a7ed773-lia-agenthub` — **HEAD `b4e63eae800b2713dcda294e3c2dfe8d60eb0b04`**
**Data:** 2026-11-15 (UTC)
**Natureza:** auditoria documental e de código. **Nenhuma alteração foi feita nos documentos da pesquisa, no código do Hub, em `main`, ou na biblioteca real.** Nenhuma Skill foi executada, instalada ou importada.

---

## 0. Nota de método e aviso de branch

### 0.1 Um fato de repositório que muda a leitura do pedido

O pedido descreve `arena/a92004be-lia-agenthub` como "branch principal de desenvolvimento". **Isso não corresponde ao estado do remoto em 2026-11-15.**

| Fato verificado | Evidência |
|---|---|
| `origin/main` = `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` ("Kit Marca Lia"), **7 arquivos**, nenhum código | `git ls-tree -r --name-only origin/main` |
| `arena/a92004be-lia-agenthub` = `704dfd3f`, **79 arquivos**, 44 commits, contém `src/lia_agenthub/**`, `tests/**`, `packaging/**` | `git ls-tree -r --name-only origin/arena/a92004be` |
| `arena/db625478-lia-agenthub` (pesquisa) = `b4e63ea`, **20 arquivos**, 5 commits, parte de `main` | `git show b4e63ea --stat` |
| **`main` não é ancestral da branch de pesquisa e não contém o código do Hub** | `git merge-base main b4e63ea` → falha por ausência de base comum na profundidade disponível; `git diff --name-status main b4e63ea` → **13 arquivos, todos `A`** |

**Consequências para esta revisão (e para o proprietário):**

1. O código do Hub **existe apenas em `arena/a92004be-lia-agenthub`** e não está em `main`. A afirmação "branch principal de desenvolvimento" é `PARTIALLY_CONFIRMED` — ela é a branch de desenvolvimento *de fato*, mas **não é `main`** e o README da pesquisa já registrava isso corretamente. A formulação do briefing é que está imprecisa.
2. Portanto **toda a auditoria de contrato (E-1…E-9, P-E1…P-E8) foi feita contra `704dfd3f`**, que é o HEAD real do Hub — e não contra `b4eb85f` como a pesquisa fez. **O código de `domain/` e `adapters/` é idêntico entre os dois commits** (verificado arquivo a arquivo); a diferença é o documento `CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md` e o relatório Windows. Isso **confirma** a afirmação da pesquisa (§1 do relatório de importação) de que "nenhum arquivo do modelo de dados mudou".
3. O compare `main..db625478` **tem 13 arquivos**, como o briefing afirma. `CONFIRMED`.

### 0.2 O que esta revisão fez além de ler os documentos

O mandato exige conferir o código, não aceitar a descrição da pesquisa. Foram executados, em ambiente Linux, **somente o código do próprio Hub e ferramentas de pesquisa** (nunca Skills, CLIs ou MCPs de terceiros):

| Atividade | Classe de evidência |
|---|---|
| Leitura integral de 13 arquivos de pesquisa + 4 `records.json` + `sources.json` + gerador | `IMPLEMENTED` / `RESEARCH` (do outro agente) |
| Leitura integral de `domain/{model,integrity,skills,risk,paths}.py`, `adapters/{importer,repository,index_builder,packager,safe_extract}.py`, `app.py`, `interface/server.py` | `IMPLEMENTED` |
| Execução da suíte do Hub em cópia limpa (`git archive` de `704dfd3f` → `/tmp`): **284 passed** | `EXECUTED` |
| 5 sondas sintéticas contra o código do Hub, em diretório temporário (nenhum payload de terceiro) | `EXECUTED` (scripts preservados em `docs/review/evidence/`) — **não `VALIDATED` em Windows** |
| Recalculo independente de `contentHash`/`treeHash` de **4 + 3** registros a partir dos bytes reais do GitHub | `VALIDATED` (fonte primária) |
| Verificação de 10 repositórios externos via API do GitHub (SPDX, árvore, `LICENSE`, commits fixados) | `VALIDATED` (fonte primária) |
| Detecção de referências quebradas (`REFERENCE_MISSING`) em **48 de 48** Skills via API + `domain/skills.py` do Hub | `EXECUTED` sobre conteúdo real |

**Não foi feito e não se deve inferir:** nada em Windows; nenhuma importação real na biblioteca; nenhum teste de execução de Skill; nenhum parecer jurídico.

---

## 1. Resumo executivo

### 1.1 Veredito em uma frase

**A pesquisa é, em qualidade de evidência, substancialmente melhor do que a média: seus nove gaps se confirmam no código, seus hashes se reproduzem byte a byte contra o upstream, sua separação de camadas de licença está correta e seu instinto de não aprovar nada é o comportamento certo. Mas ela subestima o problema de importação, porque mediu as lacunas do *modelo de dados* e não as do *pipeline de importação* — e é no pipeline que os 48 registros vão falhar.**

### 1.2 Os cinco achados que mudam a decisão

| # | Achado | Classificação | Por que importa |
|---|---|---|---|
| **A-1** | **`REFERENCE_MISSING` atinge 29 das 48 Skills (81 referências ausentes).** 12 das 13 Skills adaptadas do Studio citam `THIRD_PARTY_NOTICES.md` em code-span; o arquivo não está no payload. O Hub emite `REFERENCE_MISSING` para todas. | `CONFIRMED` (executado sobre conteúdo real) | O relatório de importação afirma "Issues estruturais: 2 × `NAME_FOLDER_MISMATCH`". O número real é **2 + 81 avisos de referência**, que a ferramenta de pesquisa **não reproduziu** porque não chama `check_references`. O catálogo está subdeclarado. |
| **A-2** | **A migração dos 48 registros para a biblioteca real é impossível pelo produto como ele é hoje.** `ImportReport` só escreve `description`/`version`/`domain`/`tags`/`author` a partir de *payload*; o `capability.json` de pesquisa **não é lido pelo importador**. Não existe importação em lote, nem importação a partir de registro. | `CONFIRMED` (leitura de `importer.py` + sonda 04) | A proposta P-E5 ("detecção de tipo por manifesto") **não funciona** para `manifest.json` de diretório: o Hub deriva tipo por marcador implícito e o teste mostrou `type: template` no manifesto → `reference` no registro. O caminho "importar os 48 registros" precisa ser **reimportar os 48 payloads**, não aplicar os registros. |
| **A-3** | **`source.derivedFrom` (P-E4) quebra o contrato, ao contrário do que a pesquisa afirma.** `Source(**d.get("source", {}))` estoura `TypeError` com chave desconhecida, e `Repository.list_all()` **captura apenas `KeyError`/`ValueError`** — o `TypeError` sobe e derruba a listagem inteira. | `CONFIRMED` (executado) | O texto "aditiva; leitores antigos ignoram chave desconhecida" está **errado**. Um registro gravado por uma versão nova torna a biblioteca **inutilizável** por uma versão antiga. Isso não é retrocompatibilidade — é corrupção de disponibilidade. |
| **A-4** | **`license.notice_required` nunca é verdadeiro no Hub real.** Importador cria `License(...)` sem tocar no campo (default `False`); `set_license` não o define. O empacotador só escreve `NOTICE` quando `notice_required` é `true`. Resultado: **exportação de Skill MIT sai sem texto de licença** — exatamente a obrigação que A-1 identifica como não cumprida. | `CONFIRMED` (executado; o Hub produziu `notice_required: false` para payload MIT, enquanto o registro de pesquisa diz `true`) | O achado de licença mais consequente da pesquisa (L-01: aviso não viaja com a Skill) **tem uma segunda causa, no produto, que a pesquisa não viu** — e ela está *depois* do import, na exportação. |
| **A-5** | **Os registros de pesquisa são fielmente reproduzíveis.** `contentHash` de 4 Skills e `treeHash` de 3 (incluindo `alethe`, 23 arquivos) batem byte a byte com os bytes reais do GitHub nos commits fixados. | `VALIDATED` | A ferramenta de pesquisa está correta quanto a hash/ID. O problema não é integridade dos registros; é **cobertura de campos** e **semântica de `imported_at`/`source.commit`**. |

### 1.3 O que a premissa de autoria do proprietário muda — e o que não muda

A declaração do proprietário ("as `lia-*` foram criadas por mim ou por IA a meu pedido") **resolve o problema de titularidade** e **não resolve o problema de licença**:

| Dimensão | Efeito da declaração | Classificação |
|---|---|---|
| Titularidade das 47 Skills autorais/adaptadas | Presumida do proprietário. **A pesquisa errou ao tratá-las como "direitos reservados de terceiros"** | `PARTIALLY_CONFIRMED` — a pesquisa aplicou a regra correta ("sem licença = reservado") à conclusão errada (que o titular é terceiro) |
| Licença concedida a terceiros | **Não resolvida.** Titularidade ≠ licença outorgada. Sem `LICENSE`, terceiros não têm permissão | `OWNER_DECISION` |
| 12 Skills adaptadas (Studio) | **Titularidade dividida.** Há conteúdo MIT de Donchitos e Mr. Mak. O proprietário é titular *da adaptação*, não do upstream | `CONFIRMED` — a pesquisa acertou (A-1, A-2 da auditoria) |
| `alethe` (vendorizada) | **Titular é terceiro** (Kauã Miguel, MIT). O proprietário não pode relicenciar | `CONFIRMED` |
| Assinatura de IA como fator | **Juridicamente irrelevante para esta auditoria.** A questão é quem encomendou e quem titulariza, não qual ferramenta escreveu | `OWNER_DECISION` (com nota de que a maioria das jurisdições não exige autoria humana para *direitos autorais* de obra encomendada, mas isso é parecer jurídico — fora do escopo) |
| Marca e identidade `lia-` | **Separada.** A declaração não licencia a marca; a própria pesquisa encontrou que Studio e Forge já excluem marca da MIT | `CONFIRMED` |

**Consequência direta:** a classificação da pesquisa para as 47 (`RESEARCH_ONLY para redistribuição a terceiros`) estava **correta como regra jurídica e errada como diagnóstico de titularidade**. A revisão reclassifica (ver §4): as 34 `LIA_ORIGINAL` passam a **A — Originais Lia, prontas para receber licença**; não ficam bloqueadas por terceiros, ficam bloqueadas **apenas pela decisão P-1**.

### 1.4 Estado de autorização

> **A importação NÃO está autorizada tecnicamente.** Há quatro bloqueios independentes, e três deles não são decisão humana — são defeitos. Ver §13.

---

## 2. Escopo e metodologia

### 2.1 Escopo examinado

| Objeto | Commit | Método |
|---|---|---|
| `docs/research/**` (7 documentos + 4 `records.json` + `sources.json` + gerador) | `b4e63ea` | leitura integral |
| Hub — domínio e adaptadores | `704dfd3f` (`origin/arena/a92004be`) | leitura integral + execução |
| `docs/architecture/CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md` | `704dfd3f` | leitura integral |
| `docs/architecture/{PRODUCT-BOUNDARIES-AND-ARCHITECTURE,SECURITY-AND-TRUST-MODEL}.md` | `704dfd3f` | leitura das seções de modelo, licença e integridade |
| `docs/DECISION-REGISTER.md`, `THIRD_PARTY_NOTICES.md`, `docs/operations/WINDOWS-VALIDATION-REPORT.md` | `704dfd3f` | leitura |
| 10 repositórios externos | HEAD em 2026-11-15 | API do GitHub: metadados, árvore, `LICENSE` por diretório, commits fixados |
| 48 Skills Lia | commits de `sources.json` | API do GitHub: `SKILL.md` real por skill |

### 2.2 O que **não** foi feito

- Nenhuma modificação em `docs/research/**`, em `main`, no código do Hub ou em qualquer outro repositório.
- Nenhum merge, PR, branch nova, rebase ou force-push.
- Nenhuma Skill, script, CLI, MCP ou modelo executado/instalado.
- Nenhuma cópia de payload entre repositórios.
- Nenhum parecer jurídico. Nenhuma licença escolhida em nome do proprietário.
- Nenhuma validação Windows. **Tudo que é `EXECUTED` aqui é Linux.**

### 2.3 Vocabulário de classificação usado

O pedido define sete rótulos (`CONFIRMED`, `PARTIALLY_CONFIRMED`, `NOT_CONFIRMED`, `OWNER_DECISION`, `TECHNICAL_ACTION`, `BLOCKED`, `READY_FOR_NEXT_PHASE`). Foram usados com uma regra adicional: **um item só recebe `READY_FOR_NEXT_PHASE` se nenhuma licença pendente o afetar** — e nenhum dos 48 recebeu esse rótulo (ver §4.4).

---

## 3. Premissa de autoria, titularidade e licença

### 3.1 As seis perguntas do pedido, respondidas com evidência

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| 1 | **Quem solicitou a criação** | O proprietário, para 47 das 48 (declaração do proprietário, 2026-11-15). A exceção é `alethe`: solicitada por terceiro (Kauã Miguel) e apenas *vendorizada* no Lia-Project | `Lia-Project@0093de09:.agents/skills/alethe/UPSTREAM.md`; `LICENSE` interno © 2026 Kauã Miguel |
| 2 | **Quem produziu o conteúdo** | Não determinável a partir do repositório e **irrelevante** para a auditoria. Os 48 `SKILL.md` não carregam campo de autoria de ferramenta; `researchNotes.frontmatter.author` é `null` em **48/48** | `all_records.json`: `capability.author == null` em 48/48 |
| 3 | **Quem detém os direitos** | 34 autorais: proprietário. 12 adaptadas: proprietário **da adaptação**, com obrigações MIT de Donchitos (7) e Mr. Mak (5). 1 vendorizada: terceiro | §4.2 |
| 4 | **Componentes de terceiros incorporados** | **13 dos 48**: 7 de `Donchitos/Claude-Code-Game-Studios`, 5 de `witnesstodark/mr-mak-workspace`, 1 de `Kc1t/alethe-orchestrate-skill`. **Mais** 1 sinal distintivo de terceiros dentro de `alethe` (5 arquivos em `assets/brands/`) | commits verificados: `05ad7c8a5b…` (2026-10-19), `cf1e126025…` (2026-11-06), `c36c341c34…` (2026-10-28) — **todos existem** |
| 5 | **Obrigações de atribuição** | MIT: preservar copyright + texto da licença nas cópias e derivações. **Não cumprida hoje**: o aviso vive na raiz do repositório, fora do payload, e o Hub não detecta licença fora da raiz | §6 (E-2), §5 (P-E2), §12 (risco R-3) |
| 6 | **Qual licença o proprietário pretende conceder** | Declarado como intenção; **ainda não escolhida**. É `P-1` | — |

### 3.2 Diferenciação que o pedido exige, e o erro específico a evitar

> **Titularidade ≠ licença concedida ≠ instrumento formal.**

| Situação | Quem pode usar internamente | Quem pode redistribuir | Existe instrumento formal? |
|---|---|---|---|
| Skill autoral em repo sem `LICENSE` (caso de 21 Skills do Project, 9 do Model-Lab, 4 do Studio, 1 do Forge) | O proprietário, sim | **Ninguém, hoje.** Ausência de licença = direitos reservados | **Não** |
| Skill autoral em repo **com** `LICENSE` MIT na branch (16 do Studio, 1 do Forge) | Sim | Sim, com aviso — **mas só se o `LICENSE` estiver na branch onde a Skill vive**, e ele não está em `main` | **Sim, na branch** |
| `alethe` vendorizada com `LICENSE` MIT dentro do payload | Sim | Sim, com aviso de © Kauã Miguel; **não** as marcas | **Sim** |

**A afirmação da pesquisa de que "a ausência de `LICENSE` não invalida a titularidade" está correta e o pedido está certo em insistir nisso.** O que a ausência de `LICENSE` faz é uma coisa só: **não concede nada a terceiros**. Ela não contesta o proprietário, não contesta a autoria e não impede o uso interno.

**Um ponto que a pesquisa e o pedido deixam implícito e que precisa ficar explícito:** o Hub **é** um distribuidor. No momento em que ele exporta um `.lia-capability` com `target: shared` ou `public`, ele está exercendo a licença — e a licença do repositório de origem deixa de ser um detalhe documental. Isso já está implementado corretamente como política (`packager.py`: `public` recusado sem `redistributable` + `redistribution_basis`), e a instrução de que **importar não é aprovar** está correta. Mas o modo `shared` **só emite aviso** e prossegue — ver risco R-3.

---

## 4. Classificação individual das 48 Skills

### 4.1 Critério aplicado

| Grupo | Definição operacional | Teste de evidência |
|---|---|---|
| **A — Originais Lia** | Nenhum conteúdo protegido de terceiro no payload; pode receber licença definida pelo proprietário | `originClass == LIA_ORIGINAL` **e** `upstreamProject` ausente ou explicitamente "assunto, não fonte" |
| **B — Adaptadas de terceiros** | Derivação de upstream identificado, com obrigação de atribuição | `originClass == LIA_ADAPTED_FROM_THIRD_PARTY` |
| **C — Terceiros incorporados** | Origem não integralmente Lia | `originClass == THIRD_PARTY_VENDORED_WITH_LOCAL_PATCHES` |

**Confirmação independente do grupo A:** a pesquisa diz "as 4 originais do Studio declaram origem conceitual **sem copiar conteúdo**". Verifiquei por sobreposição lexical (Jaccard sobre tokens ≥7 caracteres) entre 5 Skills adaptadas e seus upstreams:

| Skill | Tamanho local | Tamanho upstream | Jaccard |
|---|---|---|---|
| `lia-game-qa-plan` | 1.784 B | 17.391 B | **0,027** |
| `lia-game-balance-review` | 1.747 B | 9.123 B | **0,011** |
| `lia-game-design-review` | 1.777 B | 27.811 B | **0,010** |
| `lia-game-vfx-plan` | 1.742 B | 3.581 B | **0,018** |
| `lia-game-story-readiness` | 1.777 B | 15.400 B | **0,019** |

Classificação: `PARTIALLY_CONFIRMED` para a **classificação de grupo** (a separação A/B/C é a correta), com a observação de que a **magnitude da derivação é baixa** — são reescritas procedurais em pt-BR com `## Origem` explícita, não cópias. Isso é relevante para P-1: o risco de "contaminação" MIT→licença nova é pequeno em volume, mas **a obrigação de atribuição existe de qualquer forma**, porque o `## Origem` reconhece a derivação.

### 4.2 Classificação — 48 de 48

Legenda de colunas: **Gr** = grupo (A/B/C) · **CS** = `containsScripts` · **Derivação** = upstream e commit quando houver · **Bloqueio**.

#### Grupo A — Originais Lia (34)

| # | Skill | Repo | CS | Bloqueio para redistribuição |
|---|---|---|---:|---|
| 1 | `lia-brand-check` | Forge | não | **P-1** (Forge tem MIT só na branch); sem terceiro no payload |
| 2 | `capability-mapping` | Model-Lab | não | **P-1** (sem `LICENSE` no repo) |
| 3 | `dataset-governance` | Model-Lab | não | **P-1** |
| 4 | `experiment-reproducibility` | Model-Lab | não | **P-1** |
| 5 | `finetuning-plan` | Model-Lab | não | **P-1** |
| 6 | `lia-brand-consistency-review` | Model-Lab | não | **P-1**; sobrepõe #1 (L-07) |
| 7 | `model-candidate-research` | Model-Lab | não | **P-1** |
| 8 | `model-evaluation` | Model-Lab | não | **P-1** |
| 9 | `model-license-release-review` | Model-Lab | não | **P-1** |
| 10 | `multi-agent-orchestration` | Model-Lab | não | **P-1**; sobrepõe #24 e `alethe` (L-07) |
| 11 | `airi-upstream-integration` | Project | não | **P-1**. **Nota:** o upstream `moeru-ai/airi` é *assunto*, não fonte. `PARTIALLY_CONFIRMED` — nenhuma cópia de AIRI no payload desta Skill |
| 12 | `lia-agent-evaluation` | Project | não | **P-1** |
| 13 | `lia-agent-orchestration` | Project | não | **P-1**; sobrepõe #10 e #33 |
| 14 | `lia-ai-sdk-integration` | Project | não | **P-1** |
| 15 | `lia-browser-automation` | Project | não | **P-1**; declara dependência de `agent-browser` (ferramenta externa) |
| 16 | `lia-electron-cdp-debugging` | Project | não | **P-1** |
| 17 | `lia-eventa-ipc` | Project | não | **P-1**. Único com `license: MIT` no frontmatter, **ignorado pelo Hub** (E-2) |
| 18 | `lia-pnpm-workspaces` | Project | não | **P-1** |
| 19 | `lia-regression-investigation` | Project | não | **P-1** |
| 20 | `lia-release-gate` | Project | não | **P-1**; exige Windows |
| 21 | `lia-safe-change` | Project | não | **P-1** |
| 22 | `lia-security-review` | Project | não | **P-1** |
| 23 | `lia-test-discipline` | Project | não | **P-1** |
| 24 | `lia-ui-quality-review` | Project | não | **P-1** |
| 25 | `lia-unocss-ui` | Project | não | **P-1** |
| 26 | `lia-visual-evidence` | Project | não | **P-1**; depende de Vishot |
| 27 | `lia-voice-diagnostics` | Project | não | **P-1** |
| 28 | `lia-vue-development` | Project | não | **P-1** |
| 29 | `lia-vue-testing` | Project | não | **P-1** |
| 30 | `lia-windows-electron-validation` | Project | não | **P-1**; exige Windows |
| 31 | `stage-runtime-debugging` | Project | não | **P-1** |
| 32 | `lia-game-project-bootstrap` | Studio | não | **P-1**; único com `templates/` + `references/` (8 arquivos) |
| 33 | `lia-module-planning` | Studio | não | **P-1** |
| 34 | `lia-project-resume` | Studio | não | **P-1** |
| 35 | `lia-task-handoff` | Studio | não | **P-1**; sobrepõe fluxos do Project/Forge (L-07) |

> **Contagem verificada** (não estimada): `originClass` = `LIA_ORIGINAL` em **35**, `LIA_ADAPTED_FROM_THIRD_PARTY` em **12**, `THIRD_PARTY_VENDORED_WITH_LOCAL_PATCHES` em **1** → **48**. A tabela acima lista os **35** do grupo A (linhas 1–35), os **12** do grupo B (linhas 36–47) e o **1** do grupo C (linha 48).

#### Grupo B — Adaptadas de terceiros (12)

| # | Skill | Upstream | Commit | Licença | Obrigação | Bloqueio |
|---|---|---|---|---|---|---|
| 36 | `lia-game-audio-plan` | `witnesstodark/mr-mak-workspace` (`game-audio-workflow`) | `cf1e126025…` | MIT © Mr. Mak contributors | aviso + texto | **P-1** + aviso não viaja |
| 37 | `lia-game-level-design` | `witnesstodark/mr-mak-workspace` | `cf1e126025…` | MIT | aviso + texto | idem |
| 38 | `lia-game-ui-plan` | `witnesstodark/mr-mak-workspace` | `cf1e126025…` | MIT | aviso + texto | idem |
| 39 | `lia-game-vfx-plan` | `witnesstodark/mr-mak-workspace` | `cf1e126025…` | MIT | aviso + texto | idem |
| 40 | `lia-game-visual-review` | `witnesstodark/mr-mak-workspace` | `cf1e126025…` | MIT | aviso + texto | idem |
| 41 | `lia-game-balance-review` | `Donchitos/Claude-Code-Game-Studios` (`balance-check`) | `05ad7c8a5b…` | MIT © Donchitos | aviso + texto | idem |
| 42 | `lia-game-bug-triage` | `Donchitos/…` (`bug-triage`) | `05ad7c8a5b…` | MIT | aviso + texto | idem |
| 43 | `lia-game-design-review` | `Donchitos/…` (`design-review`) | `05ad7c8a5b…` | MIT | aviso + texto | idem |
| 44 | `lia-game-playtest-report` | `Donchitos/…` (`playtest-report`) | `05ad7c8a5b…` | MIT | aviso + texto | idem |
| 45 | `lia-game-qa-plan` | `Donchitos/…` (`qa-plan`) | `05ad7c8a5b…` | MIT | aviso + texto | idem |
| 46 | `lia-game-story-readiness` | `Donchitos/…` (`story-readiness`) | `05ad7c8a5b…` | MIT | aviso + texto | idem |
| 47 | `lia-game-test-evidence-review` | `Donchitos/…` (`test-evidence-review`) | `05ad7c8a5b…` | MIT | aviso + texto | idem |

**Compatibilidade com a licença que o proprietário pretende usar (P-1):** MIT e Apache-2.0 são **compatíveis em ambas as direções** para este caso de uso — o material MIT pode ser incorporado em obra licenciada sob MIT ou Apache-2.0, desde que o aviso MIT sobreviva. **A incompatibilidade não está na licença; está no empacotamento:** hoje o aviso não entra no payload (§5-P-E2, §12-R-3).

**O que foi mantido e o que foi removido (verificado em `lia-game-qa-plan`):** o `## Origem` declara *"Não contém hooks, scripts ou assets do upstream"*. O upstream `qa-plan` tem 17.391 B, `allowed-tools` com `Bash(...)`, `model: sonnet` e uma linha de injeção `` !`bash "${CLAUDE_SKILL_DIR}/../../hooks/yaml-helper.sh"` ``. **Nada disso está na versão Lia** (1.784 B, frontmatter de 2 campos). Confirma a remoção declarada. `CONFIRMED` — e é um mérito real do Studio.

#### Grupo C — Terceiros incorporados (1)

| # | Skill | Upstream | Licença | O que há dentro | Bloqueio |
|---|---|---|---|---|---|
| 48 | `alethe` | `Kc1t/alethe-orchestrate-skill` v19 | **MIT** © 2026 Kauã Miguel | `LICENSE` (1.069 B), `UPSTREAM.md` (1.393 B), `SKILL.md` (21.461 B), `playbooks.yaml` (22.394 B), `prices.json` (8.944 B), `scripts/{orchestrate,diagram}.py`, **`assets/brands/` com 5 sinais distintivos de terceiros** | **Autorização: sim** para o código/conteúdo MIT. **`BLOCKED` para redistribuição de `assets/brands/`** até decisão de marca (§9) |

**Verificação direta de `assets/brands/`** via API no commit `0093de09`: `antigravity-official.svg`, `claude-official.png.b64`, `kimi-official.png.b64`, `openai-official-white.svg`, `router9-official.svg`. `CONFIRMED` — a pesquisa estava certa, e este é o achado de marca mais concreto do acervo.

### 4.3 O que os registros **não** capturam sobre a classificação

A classificação A/B/C da pesquisa **existe apenas em `researchNotes.originClass`**, que está **fora do contrato** (§6-E-4). Se os 48 registros forem importados pelo caminho convencional (`payload → capability.json`), **a classificação se perde inteiramente** e o Hub volta a ver 48 Skills indistinguíveis, todas `license.unknown`, todas `unreviewed`. Isso está registrado como risco **R-1**.

### 4.4 Estado de avanço

| Grupo | Quantidade | Rótulo | Condição |
|---|---:|---|---|
| A | 35 | `BLOCKED` | Depende de **P-1** (decisão do proprietário). Nada mais bloqueia |
| B | 12 | `BLOCKED` | **P-1** + correção de empacotamento do aviso (§5-P-E2, §12-R-3) |
| C (`alethe`) | 1 | `BLOCKED` | Autorização MIT **temos**; `assets/brands/` **não temos** + `containsScripts` exige revisão humana |

**Nenhuma das 48 recebe `READY_FOR_NEXT_PHASE`.** A condição mínima comum a todas é P-1; a condição específica de 13 é o aviso de terceiro; a de 1 é a marca.

---

## 5. Revisão da decisão P-1 — política de licença

### 5.1 O que P-1 realmente decide

P-1 não é "qual licença". São **três** decisões encadeadas:

| # | Subdecisão | Consequência se não decidida |
|---|---|---|
| P-1a | O proprietário **concede** licença a terceiros, ou mantém tudo reservado? | Sem isso, nenhum dos 48 pode sair do Hub em `shared`/`public` |
| P-1b | **Qual** licença, e ela é uniforme ou por repositório? | Define compatibilidade com 13 Skills derivadas |
| P-1c | Onde o instrumento vive: `LICENSE` na raiz, `LICENSE` no payload, ou ambos? | Define se o aviso viaja com a Skill (§5-P-E2) |

### 5.2 Comparação MIT × Apache-2.0 × terceira via

| Critério | **MIT** | **Apache-2.0** | **MPL-2.0** (terceira via) | **CC0 / Unlicense** |
|---|---|---|---|---|
| Uso comercial | Sim | Sim | Sim | Sim |
| Modificação | Sim | Sim (indicar alteração) | Sim (arquivo modificado fica MPL) | Sim |
| Redistribuição | Sim, com aviso | Sim, com aviso + `NOTICE` | Sim, com fonte do arquivo modificado | Sim, sem obrigação |
| Atribuição | **Aviso de copyright + texto** | Aviso + texto + `NOTICE` + **indicar alterações** | Aviso + fonte dos arquivos MPL | Nenhuma |
| Patentes | **Silente** (sem concessão explícita) | **Concessão explícita + retaliação** | Concessão explícita | Silente |
| Compatível com material MIT de terceiros (13 Skills) | Sim | Sim (o MIT sobrevive na parte derivada) | Sim | Sim |
| Compatível com material Apache-2.0 de terceiros (candidatos B-1) | Sim | Sim | Sim | Sim |
| Compatível com material **CC-BY-NC-ND** (1 fonte) | **Não** — NC/ND proíbe derivar | **Não** | **Não** | **Não** |
| Compatível com **AGPL** (2 fontes) | **Não** para obra combinada | **Não** | **Não** | **Não** |
| Manutenção em 6 repositórios | **Trivial** (1 arquivo de 21 linhas) | Média (`LICENSE` + `NOTICE` + indicar alterações em cada fork) | Média | Trivial |
| Consequência para Skill isolada (payload de 1 arquivo) | `LICENSE` de 21 linhas cabe no payload sem ruído | `LICENSE` de ~11 KB + `NOTICE` por skill; ruído relevante em payloads de 1,7 KB | `LICENSE` de ~16 KB por arquivo | Nenhum ruído |
| Consequência para pacote do Hub | Simples | O `packager.py` **já** escreve `NOTICE` e `THIRD_PARTY_NOTICES.md` — encaixe natural | Exigiria rastrear arquivos modificados, que o Hub não modela | — |
| Expectativa do ecossistema | Studio e Forge **já declaram MIT** nas branches | Anthropic e a especificação Agent Skills usam Apache-2.0 | — | — |

### 5.3 Recomendação (não é escolha)

**Recomendação: política uniforme MIT nas criações originais, com três complementos obrigatórios.**

Fundamento concreto, não preferência:

1. **Coerência interna:** Studio (`LICENSE` MIT, © 2026 BloomRX e colaboradores, verificado na branch `203b60f`) e Forge (MIT, © 2026 Lia Forge contributors) **já declaram MIT**. Escolher Apache-2.0 só para o Hub criaria dois regimes no mesmo ecossistema, e o Hub é justamente quem empacota as Skills dos outros dois.
2. **Custo de manutenção:** MIT é um arquivo por repositório. Apache-2.0 exige `NOTICE` e "indicar alterações" em cada fork — e o Hub **não modela "arquivos modificados"**, o que tornaria a obrigação Apache impossível de cumprir com o contrato atual.
3. **Tamanho do payload:** 46 das 48 Skills têm **1 arquivo** (1.361–2.662 B). Um `LICENSE` Apache de ~11 KB por Skill multiplicaria o payload por ~5. O MIT de 21 linhas é compatível com "o aviso viaja com a Skill".
4. **A perda real do MIT é só patente.** Se o proprietário pretende distribuir para uso empresarial e quer a cláusula de patentes, Apache-2.0 passa a ter vantagem — e o custo de manutenção é absorvível **se** ao mesmo tempo se decidir (P-E3) que o `NOTICE` por Skill é obrigatório. Isto é uma troca legítima, e é **exatamente o tipo de troca que o agente não deve decidir**.
5. **Uma terceira via defensável:** **MIT para o código e as Skills, com `TRADEMARK.md` separado** — que é o padrão que Studio e Forge já praticam (marca fora da MIT) e que o pedido §7 pede para o Hub representar.

**Não recomendo CC0/Unlicense:** abriria mão da exigência de atribuição, que é justamente o mecanismo que preserva a cadeia de proveniência das 12 adaptações e o crédito a Donchitos/Mr. Mak/Kauã. `CONFIRMED` como inadequado para este ecossistema.

### 5.4 Os quatro repositórios sem `LICENSE` — análise separada

Verificado por API em 2026-11-15: `BloomRX/{Lia-Project, Lia-Model-Lab, Lia-Go, Lia-AgentHub, Lia-Studio, Lia-Forge}` → **`license.spdx_id = null` em todos os seis**. `CONFIRMED` — inclusive Studio e Forge, porque o `LICENSE` está na branch, não em `main`.

| Repositório | `LICENSE` na raiz? | `LICENSE` na branch? | Titularidade | Licença a terceiros | Instrumento formal |
|---|---|---|---|---|---|
| **Lia-Project** | não | **não** (nem `main 9c7ac183`, nem `arena/c6b02f64 0093de09`) | proprietário (21 Skills) + Kauã (1) + Neko Ayaka (AIRI, 29 vendadas) | **não outorgada** | **ausente** |
| **Lia-Model-Lab** | não | não | proprietário (9 Skills) | **não outorgada** | **ausente** |
| **Lia Go** | não | não | proprietário | não outorgada | ausente |
| **Lia-AgentHub** | não | **não** — e é **o exportador** | proprietário | não outorgada | ausente |
| *Lia-Studio* (referência) | não | **sim, MIT** em `203b60f` | proprietário + Donchitos + Mr. Mak | **outorgada na branch** | presente na branch |
| *Lia-Forge* (referência) | não | **sim, MIT** em `35b207f` | proprietário | **outorgada na branch** | presente na branch |

**Conclusão sobre a pergunta do pedido ("a ausência de LICENSE invalida a titularidade?"):** **não.** `CONFIRMED`. Ela produz um efeito único e específico — **não há outorga a terceiros** — e três efeitos secundários que importam ao produto:

1. **O GitHub não detecta licença** (`license.spdx_id: null`), então qualquer consumidor externo que consulte a API conclui "sem licença" — e a conclusão dele está correta.
2. **O próprio `THIRD_PARTY_NOTICES.md` do Hub já declara isso como deliberado** e remete a `D-16`: *"Este repositório não tem `LICENSE`. Isso é deliberado nesta fase… sem `LICENSE`, o direito de reutilização deste material não está concedido por padrão."* **A decisão P-1 do briefing é a mesma `D-16` do registro de decisões.** `CONFIRMED` — é uma duplicação de identificador que precisa ser resolvida para não gerar duas trilhas de aprovação do mesmo assunto.
3. **`Lia-Go` e `Lia-AgentHub` não têm Skills** (Go tem `.agents/skills/.gitkeep`; o Hub não tem `.agents/`). Para esses dois, P-1 é sobre **o produto**, não sobre Skills. São casos diferentes e devem ser decididos separadamente do Project/Model-Lab.

### 5.5 A licença na raiz basta? Ou cada Skill precisa de informação própria?

**Não basta, e a evidência é operacional, não teórica.**

| Razão | Evidência |
|---|---|
| O Hub **só detecta licença na raiz do payload** | `_detect_license`: `if "/" in rel: continue`. Verificado: `sub/LICENSE` → `(None, 'unknown')`. 47/48 hoje `unknown` |
| O aviso **não viaja** com a Skill exportada | `packager.py` escreve `NOTICE` só se `cap.license.notice_required`, e o importador **nunca o define como `true`** (A-4) |
| A licença da raiz do repositório **não cobre** material de terceiro derivado | `lia-game-qa-plan` é MIT-do-Donchitos + reescrita Lia. A raiz diz "MIT © BloomRX". As duas afirmações são verdadeiras e insuficientes sozinhas |
| A licença da raiz **não cobre** marca | Studio e Forge já excluem marca explicitamente do escopo da MIT |

**Recomendação (forma, não conteúdo):** `LICENSE` na raiz **por repositório** (uma vez) **+** `LICENSE`/`NOTICE` **dentro do payload de cada Skill** que incorpore terceiro **+** `TRADEMARK.md` na raiz. O Hub já tem onde guardar tudo isso (`License.code/content/weights`, `notice_required`, e o formato `.lia-capability` já reserva `NOTICE` e `THIRD_PARTY_NOTICES.md`) — **o que falta é a convenção e a detecção, não o campo.**

---

## 6. Auditoria E-1…E-9 — conferência no código

Método: cada gap foi localizado no código de `704dfd3f`, reproduzido por sonda quando possível, e classificado. **A pesquisa acertou os nove. A revisão acrescenta três defeitos que ela não viu (E-10, E-11, E-12) e corrige a severidade de dois.**

### 6.1 Tabela de auditoria

| # | Gap | Existe? | Evidência (código + sonda) | Impacto | Proposta resolve? | Prioridade | Teste necessário |
|---|---|---|---|---|---|---|---|
| **E-1** | Descrição só vem do manifesto | **`CONFIRMED`** | `importer.py`: `description=(manifest or {}).get("description","") or ""`. Sonda: frontmatter com `description` completa → `capability.description == ""` | 48/48 sem descrição no catálogo e no índice (`description` é campo do índice, `index_builder`) | **Sim** (P-E1) | **P0** | Unit: importar SKILL.md com `description` e sem manifesto → `description` preenchida. Regressão: manifesto **vence** sobre frontmatter |
| **E-2** | Licença só por arquivo na raiz do payload | **`CONFIRMED`** | `_detect_license`: `if "/" in rel: continue`; `license:` do frontmatter nunca lido. Sonda: `license: MIT` no frontmatter → `license.code = null`, `status = unknown` | 47/48 `unknown`; `lia-eventa-ipc` (MIT declarado) entra como desconhecida; `risk.py` adiciona fator `UNKNOWN_LICENSE` e eleva o risco | **Sim, parcialmente** (P-E2). **Falta o complemento de `notice_required`** (ver A-4 / E-11) | **P0** | Unit: `license: MIT` no frontmatter → `code=MIT, status=declared, redistributable=false`. **Teste negativo obrigatório:** declarado **não** implica redistribuível |
| **E-3** | `metadata:` aninhado descartado | **`CONFIRMED`** | `skills.py::parse_frontmatter`: `if line.startswith((" ", "\t")): continue`. Sonda com o `SKILL.md` real de `alethe`: `metadata` → `''`, `version` ausente → `0.1.0` | `alethe` v19 importada como 0.1.0. Qualquer Skill que use `metadata.author/version/tags` (formato do **exemplo oficial** da spec) perde os três | **Sim** (P-E3), com ressalva de escopo (§7.3) | **P1** | Unit: `metadata:\n  version: "19"` → `version == "19"`; `metadata.author` → `author`. Regressão: chaves fora de `KNOWN_FIELDS` continuam gerando `UNKNOWN_FIELD` (não silenciar) |
| **E-4** | Sem campo de derivação | **`CONFIRMED`** | `model.py::Source` tem 5 campos, nenhum de derivação; `versionOf` é linhagem de versões. **13 registros** carregam 7 campos de derivação **só** em `researchNotes`: `upstreamProject`, `upstreamSkill`, `upstreamCommit`, `upstreamLicense`, `attributionWhere`, `derivationUrl`, `reuseAcrossLia` | A cadeia "adaptada de X no commit Y" não sobrevive a uma importação convencional | **Não como proposto** — P-E4 **quebra** o contrato (ver §7.4 / A-3) | **P0** | Teste de **compatibilidade bidirecional**: registro novo → leitor antigo **não pode** derrubar `list_all()`. Hoje derruba |
| **E-5** | Detecção de tipo limitada | **`CONFIRMED`** | `_detect_type`: `SKILL.md→agent-skill`, `package.json→mcp-server`, `.md/.txt→reference`, senão `unknown`. Sonda: `{'a.toml'}` → `unknown`; `{'MODEL-CARD.md'}` → `reference` | 7 perfis `.toml` e 5 templates não representáveis | **Não como proposto** — P-E5 diz "detecção por manifesto", mas o **tipo do manifesto é ignorado** (sonda: manifesto com `"type":"template"` → registro `reference`) | **P2** | Unit: manifesto com `type` explícito deve vencer o marcador implícito. Hoje não vence |
| **E-6** | Nome da pasta derivado da primeira subpasta | **`CONFIRMED`** | `importer.py`: `folder = next((p.split("/")[0] for p in files if "/" in p), None)` | Aviso espúrio `NAME_FOLDER_MISMATCH` em **2** Skills (`alethe` → "assets", `lia-game-project-bootstrap` → "references") | **Sim** (P-E6) | **P1** | Unit: importar pasta cujo `name` bate com o diretório de origem e contém subpastas → **sem** `NAME_FOLDER_MISMATCH`. E o caso inverso: nome realmente diferente → aviso **deve** aparecer |
| **E-7** | `requirements` sempre `null` | **`CONFIRMED`** | Nenhum caminho de importação preenche `requirements`; `Capability.as_dict` serializa `None` | 11 Skills com `compatibility` em prosa não viram requisito estruturado; `risk.py` adiciona "Requisitos de sistema (não medidos)" | **Parcialmente** (P-E7). Ver §7.7: converter prosa em estrutura é inferência, e o modelo proíbe inventar | **P2** | Unit: **não é possível** preencher `requirements` sem declaração estruturada → o campo deve permanecer `null` e a UI deve dizer "não medido". Teste de que prosa **não** vira número |
| **E-8** | Sem camada de marca | **`CONFIRMED`** | `License` tem `code/content/weights`; não há `trademark`/`brand`. `alethe` tem 5 sinais distintivos e nenhum campo onde registrar o impedimento | Nenhum mecanismo impede exportar `assets/brands/` em `shared`/`public` | **Sim** (P-E8), mas o **lugar** é discutível (§7.8) | **P1** | Teste: `alethe` com marca sinalizada → `export(shared)` **recusa ou avisa de forma bloqueante**; `export(private)` prossegue |
| **E-9** | Índice só lista `ACTIVE` | **`CONFIRMED`** | `index_builder.build_index`: `if cap.lifecycle is not Lifecycle.ACTIVE: continue` | Os 48, em quarentena, ficam invisíveis no índice compartilhado. **Comportamento correto** | **N/A** — não é defeito. É política; falta **comunicação** ao usuário | **P3** | Nenhum teste de correção. Teste de **mensagem**: publicar índice com 0 ativos e 48 em quarentena não pode parecer "índice vazio" |

### 6.2 Os três gaps que a pesquisa **não** encontrou

| # | Gap novo | Evidência | Impacto | Prioridade |
|---|---|---|---|---|
| **E-10** | **`check_references` não é reproduzido pela ferramenta de pesquisa; o catálogo está subdeclarado em 81 avisos** | `build-catalog-records.py` **não chama** `check_references` (grep: 0 ocorrências). O importador chama (2 ocorrências). Executado sobre os 48 `SKILL.md` reais: **29 Skills com `REFERENCE_MISSING`, 81 referências ausentes** — das quais **10 são cross-skill** (`.agents/skills/<outra>/SKILL.md`) | O relatório diz "2 avisos estruturais". O correto é **2 + 81**. A decisão de importar foi tomada sobre um risco medido 40× menor do que o real | **P0** |
| **E-11** | **`notice_required` nunca é `true` no Hub** | `importer.py` cria `License(code=…, status=…, redistributable=False)` — **sem `notice_required`**, default `False`. `app.set_license` também não o define. `packager.py`: `if cap.license.notice_required:` → `NOTICE` **não é escrito**. Sonda: payload MIT → Hub produz `notice_required: false`; a pesquisa registrou `true` no mesmo caso | **A exportação de Skill MIT sai sem o texto de licença** — violando a obrigação MIT que a própria pesquisa identificou (L-01). O registro de pesquisa está **mais correto** que o produto | **P0** |
| **E-12** | **`.lia/` do payload atravessa o pipeline e vira `payload/.lia/capability.json` no pacote exportado** | Sonda: diretório com `.lia/capability.json` forjado (`trust: first-party`, `redistributable: true`) é importado com sucesso, o `.lia/` é **copiado para o payload**, e a exportação produz `payload/.lia/capability.json` — um manifesto de capacidade **dentro** do payload, que qualquer host ingênuo pode ler. `DENY_NAMES` de `paths.py` não inclui `.lia` | Contradiz `SECURITY §3.7.1` ("`.lia/provenance.json` somente leitura pelo Hub, nunca escrita por capacidade"). Não é execução, mas é **confusão de fronteira de metadado** e um vetor de "capacidade que se declara `first-party`" | **P1** |

### 6.3 Severidades corrigidas em relação à pesquisa

| Gap | Pesquisa | Revisão | Motivo |
|---|---|---|---|
| E-9 | Listado como gap | **Política correta, não defeito** (`NOT_CONFIRMED` como defeito) | O comportamento é exatamente o que `SECURITY` e `CAPABILITY-HOST` §7.4 exigem ("quarentena não é aprovação"). Chamar de lacuna convida a "corrigir" removendo o filtro — que seria um erro grave |
| E-5 | Gap de modelo | **`CONFIRMED`, mas prioridade menor (P2)** | Nenhum dos 48 é template ou `.toml`. O gap é real e não afeta esta importação |
| E-7 | Gap de modelo | **`PARTIALLY_CONFIRMED` como gap; P-E7 é a proposta mais fraca (P2/adiar)** | Ver §7.7 |

---

## 7. Avaliação P-E1…P-E8

### 7.1 Regra de avaliação

Para cada proposta: **já existe equivalente?** · **é necessária?** · **o campo pertence ao manifesto da Skill, ao registro do Hub, ou a documento complementar?** · **compatibilidade com o contrato atual** · **dependências** · **duplicação de conceito?**

O contrato separa três lugares, e a distinção decide quase todas as propostas:

| Lugar | O que é | Quem escreve | Compatibilidade |
|---|---|---|---|
| **`SKILL.md` frontmatter** | Formato **Agent Skills** (spec externa, Apache-2.0) — 6 campos | O autor da Skill | **Não pode** receber semântica Lia (`D-03`, `CAPABILITY-HOST` §5.3) |
| **`.lia/capability.json`** | Registro do Hub (`schemaVersion 1`) | O Hub | Pode evoluir **se** retrocompatível de fato |
| **`manifest.json` do pacote** | Metadado de transporte `.lia-capability` | O empacotador | Formato já existe |

### 7.2 Tabela de veredito

| # | Proposta | Já existe equivalente? | Necessária? | Lugar correto | Compatibilidade hoje | Veredito | Prio |
|---|---|---|---|---|---|---|---|
| **P-E1** | `description` do frontmatter como fallback | Não | **Sim** | Registro (importador) | Aditiva de fato (só preenche vazio) | **APROVAR** | P0 |
| **P-E2** | Ler `license` do frontmatter como **declaração**, nunca permissão | Não | **Sim** | Registro (importador) | Aditiva; preserva "presença ≠ permissão" **se** `redistributable` continuar `false` | **APROVAR COM AJUSTE** — incluir `notice_required` e detecção de `LICENSE` em subpasta (A-4/E-11) | P0 |
| **P-E3** | Aceitar `metadata:` aninhado **ou** documentar a restrição | Não | **Sim** | Parser (`skills.py`) | Aditiva **se** o parser tolerar; a spec oficial **usa** aninhamento | **APROVAR COM AJUSTE** — parser tolerante **de uma camada só**, stdlib, sem PyYAML (ver 7.5) | P1 |
| **P-E4** | `source.derivedFrom[]` | Não | **Sim** | Registro | **A pesquisa afirma aditiva — é FALSO.** `Source(**d)` estoura `TypeError`; `list_all()` não o captura → **biblioteca inteira inacessível** | **APROVAR COM AJUSTE OBRIGATÓRIO** — ver 7.4 | P0 |
| **P-E5** | Tipo por manifesto | Não | **Sim, mas não como descrito** | Registro (importador) | O importador **ignora** `manifest["type"]` (sonda) | **AJUSTAR E ADIAR** — o manifesto de **pacote** já pode; o manifesto **de diretório** não é lido como tipo. Escopo: reescrever como "respeitar `type` do `manifest.json` quando presente" | P2 |
| **P-E6** | Nome da pasta do **caminho de origem**, não do primeiro `/` | Não | **Sim** | Importador | Correção de comportamento; `folder_name` também é usado em `app.validate()` | **APROVAR** (dois pontos de chamada) | P1 |
| **P-E7** | Popular `requirements` a partir de `compatibility` + inventário | Não | **Não agora** | Registro | Converter prosa em estrutura **é inferência**, e o modelo proíbe (`null = não medido`, "nunca inventar zero") | **ADIAR** — ver 7.7 | P2 |
| **P-E8** | `license.trademark` + recusa de export `shared`/`public` com marca de terceiro | Não | **Sim** | **Discussão:** registro **e** política de exportação | Muda política de exportação. `packager.export` já tem o ponto de recusa para `public` | **APROVAR O CONCEITO; AJUSTAR O LUGAR** — ver 7.8 | P1 |

### 7.3 Dependências entre propostas

```
P-E2 (licença declarada) ──→ E-11 (notice_required) ──→ aviso viaja no pacote
                                    │
P-E1 (description) ─────────────────┼──→ índice deixa de ter 48 linhas vazias
                                    │
P-E4 (derivedFrom) ──→ precisa de tolerância a chave desconhecida (pré-requisito)
                                    │
P-E6 (nome da pasta) ──→ remove 2 falsos positivos → validação fica utilizável
                                    │
P-E8 (marca) ──→ depende de P-E2 (licença declarada) estar correta
```

**Ordem de execução recomendada se aprovado:** tolerância a chave desconhecida → P-E1 → P-E2+E-11 → P-E6 → P-E4 → P-E3 → P-E8 → P-E5 → (P-E7 adiada).

### 7.4 P-E4 — o problema de compatibilidade, com prova

A afirmação da pesquisa é: *"aditiva; leitores antigos ignoram chave desconhecida"*. **Isso não é verdade neste contrato.** Prova executada:

```
>>> Capability.from_dict({'id':'x','name':'x','source':{'upstream':'u','derivedFrom':[{'project':'p'}]}})
TypeError: Source.__init__() got an unexpected keyword argument 'derivedFrom'

>>> Repository.list_all()   # com um capability.json contendo source.derivedFrom
TypeError: Source.__init__() got an unexpected keyword argument 'derivedFrom'
```

Porque `model.py` faz `source=Source(**d.get("source", {}))` e `repository.list_all()` só captura `except (KeyError, ValueError)`.

**Diferença crucial que a pesquisa não distinguiu:** o contrato é tolerante a chave desconhecida **no topo** (`Capability.from_dict` lê campo a campo e **descarta** o desconhecido — verificado: `createdBy`, `rightsHolder`, `derivedFrom` no topo são ignorados e **perdidos** na releitura). Ele é **intolerante a chave desconhecida dentro de `source` e `license`** (`License.from_dict` ignora desconhecidas — verificado com `trademark`).

**Consequência:** qualquer campo novo aninhado é uma **mudança incompatível**, não aditiva. Se o Hub gravar `derivedFrom` e o usuário reabrir com versão anterior (ou o pacote for lido por host com versão anterior), a biblioteca inteira para de listar.

**Ajuste obrigatório:** `Source.from_dict()` explícito (como `License.from_dict` já faz) **antes** de qualquer campo novo. Este é o pré-requisito técnico de P-E4, P-E8 e de qualquer evolução futura.

### 7.5 P-E3 — o ajuste de escopo do parser

A proposta oferece duas saídas ("aceitar aninhamento **ou** documentar a restrição"). A segunda é insuficiente: o **exemplo oficial da especificação** usa `metadata:` aninhado, então metade do ecossistema escreverá nesse formato, e "documentar" produz um Hub que recusa o formato canônico.

Escopo recomendado: **um nível de aninhamento, chaves string, stdlib**, preservando a decisão de não introduzir PyYAML. Testes obrigatórios: (a) `metadata.version` vira `version`; (b) `metadata` com aninhamento de dois níveis **não** quebra — degrada para issue, nunca exceção; (c) chave desconhecida fora de `metadata` **continua** gerando `UNKNOWN_FIELD`.

**Risco não mencionado pela pesquisa:** o kit do próprio ecossistema (`docs/KIT-PROJETO-NOVO.zip` → `arquivos-prontos/skill-exemplo--SKILL.md`) recomenda campos **`paths`, `context: fork`** que **não estão** nos `KNOWN_FIELDS` do Hub. Verificado: o validador emite `UNKNOWN_FIELD` para ambos. Ou seja, **o Hub acusará como "campo desconhecido" Skills escritas segundo o kit do próprio proprietário**. Isso precisa ser decidido junto com P-E3 (`CONFIRMED`).

### 7.6 P-E6 — dois pontos de chamada, não um

`folder_name` é derivado em **dois** lugares com a mesma expressão: `importer.py` (linha da validação estrutural) e `app.py::validate()` (revalidação sob demanda). Corrigir só o importador faria a mesma Skill passar na importação e falhar na revalidação. `TECHNICAL_ACTION`.

### 7.7 P-E7 — por que adiar

`compatibility` é prosa. Exemplos reais dos 48: *"Exige Windows e checkout local. Automação controlada prova critérios observáveis; áudio físico exige teste apropriado."* Converter isso em `requirements {os, gpu, vramMb…}` exige **inferência de texto**, e o contrato do Hub proíbe exatamente isso (`PRODUCT-BOUNDARIES §6.2`: "`null` significa não medido, nunca zero"; `risk.py` já trata `requirements is None` como "não avaliado").

**Recomendação:** não popular `requirements` a partir de prosa. Manter `null` e **exibir a prosa de `compatibility`** ao usuário. Se estrutura for necessária, ela deve vir de **declaração explícita** (manifesto complementar), não de parsing. `ADIAR` + reescopo.

### 7.8 P-E8 — o conceito é certo, o lugar é discutível

A pesquisa propõe `license.trademark`. Duas objeções:

1. **Marca não é licença.** `License` tem `status ∈ {declared, unknown, conflicting}` e `redistributable`/`redistribution_basis`. Marca é uma **restrição de uso independente** que coexiste com qualquer licença — um mesmo payload pode ser MIT (código) + sem licença de marca. Encaixá-la como mais uma "camada de licença" repete o erro conceitual que `PRODUCT-BOUNDARIES §6.4` já descreve corretamente ao listar **Marca** como camada separada.
2. **O mesmo vale para `created_by`/`rights_holder`/`attribution`, que o pedido §5 pede para diferenciar.** Ver §7.9.

**Ajuste recomendado:** representar marca como **fato sobre o payload** (lista de sinais distintivos detectados + `authorization: none|granted|unknown`), não como valor de licença. E a **política** de recusa pertence ao `packager`, onde já existe o ponto de decisão por `Target`. `APROVAR O CONCEITO; mover o campo`.

### 7.9 Os seis conceitos que o pedido pede para diferenciar — onde cada um cabe

O pedido avisa: "esses nomes são conceitos para avaliação, não uma determinação". Correta a advertência. Situação real:

| Conceito | Já tem representação? | Onde | Verdicto |
|---|---|---|---|
| `created_by` (origem da criação) | **Parcialmente:** `author` (nunca preenchido em 48/48) e `source.original_name` | Registro | Já cabe em `author`. **Não criar campo novo**; corrigir o preenchimento (P-E1/P-E3) |
| `rights_holder` (titularidade declarada) | **Não** | — | **Conceito novo e necessário**, mas a titularidade é **por repositório/por Skill**, não por importação. Cabe melhor no manifesto complementar + `LICENSE` do repo do que como campo por registro |
| `license` | **Sim**, por camada | `License.code/content/weights` + `status`/`redistributable`/`basis` | Manter. **Existe e está bem desenhado** |
| `derived_from` | **Não** | — | **Necessário** (E-4). Ver P-E4 e o ajuste de compatibilidade |
| `attribution` (obrigações) | **Parcialmente:** `notice_required` (nunca `true` — E-11), `THIRD_PARTY_NOTICES.md` no pacote | Registro + pacote | Corrigir E-11 antes de criar qualquer campo. A obrigação é binária e já tem campo |
| `trademark` | **Não** | — | **Necessário** (E-8), lugar a decidir (7.8) |

**Conclusão sobre "criar seis campos novos":** dois já existem (`license`, e `created_by`→`author`); dois existem pela metade e precisam de **correção**, não de campo (`attribution`→`notice_required`, `created_by`→preenchimento); dois são novos e necessários (`derived_from`, `trademark`); um é de outro lugar (`rights_holder`). **Criar os seis como campos obrigatórios do `capability.json` seria duplicar conceito e engordar um registro que serve a 48 Skills de 1,7 KB.** `TECHNICAL_ACTION` + `OWNER_DECISION` (o proprietário decide o que é obrigatório).

---

## 8. Auditoria dos 48 registros

### 8.1 Verificação de contrato — resultado

| Verificação | Resultado | Evidência |
|---|---|---|
| Chaves de `capability` == `Capability.as_dict()` | **48/48 exatas** (0 divergência) | comparação programática contra o código |
| Chaves de `provenance` | **48/48** com `{schemaVersion, upstream, importedAt, method, files, hashes, note}` — idêntico ao que `importer.py` grava | idem |
| `schemaVersion` | **1** em 48/48 | idem |
| `id` válido (`ID_RE`, ≤64) | **48/48**, nenhum duplicado, máx. 40 chars | `re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")` |
| **`contentHash` correto** (recalculado do GitHub) | **4/4 amostrados `MATCH`**: `lia-game-qa-plan`, `lia-brand-check`, `capability-mapping`, `lia-eventa-ipc` | bytes reais do GitHub nos commits de `sources.json` |
| **`treeHash` correto** (recalculado do GitHub) | **3/3 `MATCH`**: `alethe` (23 arquivos), `lia-game-project-bootstrap` (8), `lia-game-qa-plan` (1) | algoritmo de `integrity.py` reimplementado sobre a árvore real |
| Consistência interna registro↔payload | **48/48** — `treeHash` recomputado a partir de `provenance.files` bate; `contentHash` = sha256 do `SKILL.md` | recomputo local |
| Commits de `sources.json` existem | **4/4** verificados por API | `203b60f`, `0093de09`, `3ec4313`, `35b207f` |
| Payload total | **1.572.502 B** — confere | soma de `researchNotes.payloadBytes` |
| Payloads com >1 arquivo | **2** (`alethe` 23, `lia-game-project-bootstrap` 8) — confere | idem |
| `containsScripts: true` | **1** (`alethe`) — confere | idem |

**Veredicto:** `VALIDATED` quanto a **integridade e identificação**. `CONFIRMED` integralmente. A ferramenta de pesquisa reproduz o algoritmo do Hub corretamente — o que é um resultado melhor do que a própria pesquisa reivindicou (ela se classificou `EXECUTED`, e merecia mais).

### 8.2 Pode o modelo atual representar os 48 sem perda?

**Não.** Perda contabilizada, com onde ela ocorre:

| Informação existente nos 48 | Sobrevive a uma importação convencional? | Por quê |
|---|---|---|
| `description` (48/48 têm) | **Não** → vira `""` | E-1 |
| `license` declarada em 1 frontmatter (`lia-eventa-ipc`) | **Não** → `unknown` | E-2 |
| `version` de `alethe` (v19 em `metadata.version`) | **Não** → `0.1.0` | E-3 |
| `compatibility` (11 Skills, até 142 chars) | **Não** → descartado silenciosamente | E-7 |
| Derivação de 13 Skills (7 campos cada) | **Não** → perdida | E-4 |
| Classificação A/B/C (`originClass`) | **Não** → perdida | E-4 |
| Sinais de marca de `alethe` (5 arquivos) | **Não** | E-8 |
| `containsScripts` | **Sim** | — |
| `contentHash`/`treeHash` | **Sim** (recalculados) | — |
| **81 referências ausentes** | **Não** — nem aparecem no catálogo | E-10 |
| `source.commit` do repositório de origem | **Não** — os 48 registros têm `source.commit: null` **e** `source.imported_at: null` | ver 8.3 |
| **`imported_at` data real** | **Não** — `None` em 48/48 (a sonda do Hub preenche com `now`) | ver 8.3 |

Contagem: **9 dos 12 blocos de informação perdem dados**. `CONFIRMED` — "representável sem perda" é falso.

### 8.3 Duas imprecisões nos próprios registros

| # | Achado | Evidência | Severidade |
|---|---|---|---|
| **R-8.1** | **`source.commit` é `null` em 48/48** embora o commit de origem seja conhecido e esteja em `researchNotes.sourceCommit` | `all_records.json`: `Counter({'None': 48})`; o gerador grava `"commit": None` e não copia `src['commit']` | Média — o Hub **tem** o campo (`Source.commit`) e ele está vazio. Corrigível sem mudar contrato |
| **R-8.2** | **`imported_at`/`importedAt` é `null` em 48/48** | idem | Média — num catálogo "pronto para importação", a data de coleta é parte da proveniência. `null` é honesto (não houve importação) mas **subt utiliza** o campo, que descreve a coleta |

Nenhuma das duas invalida os registros; ambas são corrigíveis no gerador, sem tocar no contrato.

### 8.4 Atenção especial pedida pelo briefing

| Foco | Resultado |
|---|---|
| **`alethe`** | `license: MIT` ✓ (único com licença no payload) · `containsScripts: true` ✓ · `version: 0.1.0` — **errado**, deveria ser `19` (E-3) · `NAME_FOLDER_MISMATCH` espúrio ✓ · **`REFERENCE_MISSING` × 4 omitido** (E-10) · **5 sinais de marca sem campo** (E-8) · **`treeHash` recomputado do GitHub: `MATCH`** ✓ |
| **7 adaptadas do Donchitos + 5 do Mr. Mak** | Derivação correta em `researchNotes` (upstream, skill, commit, licença) ✓ · `license: unknown` por ausência de `LICENSE` no payload ✓ (correto pelo contrato atual, **errado pelo direito**: a derivação é MIT) · **12 citam `THIRD_PARTY_NOTICES.md` e geram `REFERENCE_MISSING`** ✗ · `description: ""` ✗ |
| **Skill com licença no frontmatter (`lia-eventa-ipc`)** | `license: MIT` no frontmatter, `license.code: null` no registro ✓ (confirma E-2) · **nenhum aviso de importação sobre a licença declarada e ignorada** — o registro diz "nenhum arquivo de licença encontrado", que é tecnicamente verdade e materialmente enganoso |
| **`lia-game-project-bootstrap`** | 8 arquivos ✓ · `templates/` e `references/` presentes ✓ · **`REFERENCE_MISSING` × 7 omitido** (E-10): o corpo cita `PROJECT_BRIEF.md`, `GDD.md`, `SCOPE.md`, `DECISIONS.md`, `REFERENCIAS.md` sem o prefixo `templates/` — só 1 das 8 referências resolve |

### 8.5 O que o hash **não** prova (reforço do pedido)

`contentHash` e `treeHash` provam uma coisa e apenas uma: *este conteúdo é idêntico ao que foi medido*. Eles **não** provam autoria, **não** provam autorização de distribuição e **não** são assinatura. Verifiquei que os 48 são reproduzíveis — o que eleva a confiança no **processo de catalogação**, e **não altera em nada** o estado de licença de nenhum dos 48. O próprio código diz isso (`integrity.py`: "`hash` ≠ assinatura"; não existe campo `signed`; `index_builder` força `signed: false`). `CONFIRMED` e corretamente implementado.

---

## 9. Marca e atribuição

### 9.1 Sinais distintivos encontrados — verificação direta

| Onde | Sinais | Licença do código | Licença da marca |
|---|---|---|---|
| `Lia-Project@0093de09:.agents/skills/alethe/assets/brands/` | `antigravity-official.svg`, `claude-official.png.b64`, `kimi-official.png.b64`, `openai-official-white.svg`, `router9-official.svg` | MIT (@ Kauã Miguel) | **Nenhuma.** Nenhum dos 5 titulares licenciou a marca para este pacote |
| `Lia-Studio@203b60f:THIRD_PARTY_NOTICES.md` | — | MIT | **Exclui explicitamente** a identidade Lia da MIT |
| `Lia-Forge@35b207f:THIRD_PARTY_NOTICES.md` | `assets/lia-forge.svg`, `.ico` | MIT | **Exclui explicitamente** nome, marca e os dois assets |
| `anthropics/skills/skills/brand-guidelines` | identidade visual Anthropic | Apache-2.0 (verificado: `LICENSE.txt` = Apache 2.0) | **Não licenciada** |

`CONFIRMED` para todos. **O ecossistema já pratica a separação marca/código de forma correta e explícita** — isso é um ativo, não um problema.

### 9.2 O que o Hub precisa representar

Separação correta em cinco camadas, cada uma com um instrumento diferente:

| Camada | Instrumento | Estado no Hub |
|---|---|---|
| **Licença do código** | `LICENSE` (SPDX) | `License.code` ✓ (detecção falha — E-2) |
| **Licença do conteúdo/documentação** | pode divergir do código (ex.: `modelcontextprotocol/servers`: código Apache-2.0, docs CC-BY-4.0 — **verificado no `LICENSE` real**) | `License.content` ✓ (nunca preenchido) |
| **Direitos sobre nome e marca** | `TRADEMARK.md` / aviso, **nunca** a licença do código | **Ausente** (E-8) |
| **Identidade visual (assets)** | licença própria por asset ou exclusão explícita | Ausente |
| **Atribuição obrigatória** | `NOTICE` / `THIRD_PARTY_NOTICES.md` **dentro do payload** | Campo existe, **nunca é `true`** (E-11); arquivo **não é gerado** |

### 9.3 Como evitar que uma Skill adaptada pareça produto oficial de terceiro — e vice-versa

**Não recomendo remover as referências a upstream.** Elas são obrigação MIT e são o melhor ativo de proveniência do ecossistema (o `## Origem` do Studio com link para o arquivo no commit exato é acima da média do mercado). O que resolve o problema de percepção é **rótulo de estado**, não remoção de crédito:

| Risco de confusão | Mecanismo proposto | Onde |
|---|---|---|
| Usuário acha que `lia-game-qa-plan` é produto do Donchitos | Campo explícito de derivação visível na listagem (`derived_from` + `transformation: adapted`), e `author` = BloomRX | Registro + UI |
| Usuário acha que Skills Lia são endossadas por Anthropic/OpenAI | `trademark.authorization: none` + aviso no pacote | Registro + pacote |
| Receptor acha que `alethe` é produto Lia | Manter nome original (a pesquisa acertou: renomear quebra rastreabilidade) + `author` = Kauã Miguel + `UPSTREAM.md` no payload | Registro |
| Marca Lia usada por fork de terceiro | `TRADEMARK.md` no repo (já é a prática de Studio/Forge) | Repositório |

**Decisão do proprietário:** a política de marca é `P-2` do pedido (§15). O agente não decide o que é "sinal distintivo permitido".

---

## 10. Auditoria das fontes externas

Verificação **direta por API em 2026-11-15**, não por descrição de README.

| Fonte | API `spdx_id` | Árvore verificada | Conclusão da pesquisa | Veredicto da revisão |
|---|---|---|---|---|
| **`anthropics/skills`** | **`null`** | 544 blobs, **19 `LICENSE.txt`** (um por skill) + `THIRD_PARTY_NOTICES.md` | "licença por skill, Apache-2.0; não tratar como repo Apache" | **`CONFIRMED` integralmente.** Li os 8 `LICENSE.txt` relevantes (`skill-creator`, `mcp-builder`, `webapp-testing`, `brand-guidelines`, `docx`, `pdf`, `pptx`, `xlsx`) — **todos Apache 2.0**. A pesquisa leu 1 de 19 e **declarou a confiança** como "Média para as demais 18". Honesto e correto. **Agora são 8 de 19 verificados** |
| **`vercel-labs/agent-skills`** | **`null`** | 477 entradas, **0 arquivos `LICENSE`/`NOTICE`**, 9 `SKILL.md` | `RESEARCH_ONLY` até confirmação escrita | **`CONFIRMED`.** A conclusão mais conservadora do relatório é a correta. Ausência de arquivo com declaração em README **não** é licença suficiente para redistribuir — e a pesquisa não a tratou como tal |
| **`modelcontextprotocol/servers`** | **`NOASSERTION`** | `LICENSE` lido: **transição MIT→Apache-2.0**; docs CC-BY-4.0; contribuições sem consentimento **permanecem MIT** | "pesquisa por padrão; ADAPT só por arquivo; nunca citar 'o repo é MIT/Apache'" | **`CONFIRMED` literalmente**, incluindo o texto de transição. É o melhor item de auditoria de licença do relatório |
| **`hesreallyhim/awesome-claude-code`** | **`NOASSERTION`** | `LICENSE` lido via Contents API: **CC-BY-NC-ND 4.0**, com pedido de contato para uso modificado | `RESEARCH_ONLY` / `BLOCKED` para republicação | **`CONFIRMED`.** NC + ND impedem catálogo derivado. A pesquisa acertou e a distinção "leitura ≠ republicação" está correta |
| **`multica-ai/andrej-karpathy-skills`** | **`null`** | sem `LICENSE` | `BLOCKED` | **`CONFIRMED`.** Ausência de licença **não** virou permissão em nenhum ponto |
| **`travisvn/awesome-claude-skills`** | **`null`** | 3 arquivos na raiz | `BLOCKED` | **`CONFIRMED`** |
| `agentskills/agentskills` | **`Apache-2.0`** | — | `USE_AS_IS` (norma) | **`CONFIRMED`** |
| `Donchitos/Claude-Code-Game-Studios` | **`MIT`** | commit `05ad7c8a5b…` **existe** (2026-10-19, "Release 1.2.0") | MIT, `ADAPT_ALLOWED` | **`CONFIRMED`**, commit verificado |
| `Kc1t/alethe-orchestrate-skill` | **`MIT`** | commit `c36c341c34…` **existe** (2026-10-28) | MIT com bloqueio de marca | **`CONFIRMED`**, commit verificado |
| `witnesstodark/mr-mak-workspace` | **`MIT`** | commit `cf1e126025…` **existe** (2026-11-06) | MIT; `img2threejs` Apache-2.0 separado | **`CONFIRMED`** |

### 10.1 As cinco diferenciações pedidas — como a pesquisa se saiu

| Diferenciação | Aplicada corretamente? | Evidência |
|---|---|---|
| Licença do código | **Sim** — distingue `spdx_id` da API de licença real em 3 casos | `anthropics/skills`, `vercel-labs`, `modelcontextprotocol` |
| Licença por diretório/Skill | **Sim** — `anthropics` é o exemplo central; `sickn33` (648 arquivos de licença) também | §2, §3 do catálogo |
| Licença dos assets | **Sim** — `img2threejs` Apache-2.0 separado; ícones Simple Icons/SVGL no `sickn33`; marcas no `alethe` | §A-2, §B-5, §5 |
| Licença de modelos e dados | **Sim** — separa `license.code/content/weights`; caso `f5-tts` (código MIT, pesos CC-BY-NC) | §B-12 |
| Ausência de licença ≠ permissão | **Sim, sem exceção** — 11 repositórios `BLOCKED` por ausência, incluindo populares | §B-10 |
| Incompatibilidade com redistribuição | **Sim** — AGPL e CC-BY-NC-ND tratados como bloqueio, não como "usar com cuidado" | §B-11 |

**Veredicto da seção 10: `CONFIRMED` em 10 de 10 fontes verificadas.** Nenhuma conclusão de bloqueio ou permissão foi encontrada baseada apenas em README. A única fragilidade é a que a própria pesquisa declarou: `skills.sh` não foi lido na fonte primária e está marcado como tal — tratamento correto.

---

## 11. Compatibilidade com o Capability Host

### 11.1 Confronto com `CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md` (`704dfd3f`)

| Item do contrato | Status | Tensão com a pesquisa? |
|---|---|---|
| Duas classes de host (`development-host`, `product-runtime-host`) | **PROPOSED** | **Nenhuma.** A pesquisa catalogou 48 Skills que são, todas, `development-only` por natureza (são procedimentos de engenharia de jogo/Vue/Windows). Nenhuma é candidata a `product-runtime-host` |
| Três perfis de distribuição (`development-only`, `app-bundled`, `user-installed`) | **PROPOSED** | **Tensão real:** os 48 registros **não têm** campo de perfil de distribuição. O contrato prevê o campo; o modelo implementado **não**. Isso é um gap que a pesquisa não listou (E-13, §11.3) |
| Manifesto complementar `.lia/capability.json` sem tocar `SKILL.md` | **PROPOSED**, coincide com **implementado** | **Alinhamento total.** A pesquisa usou exatamente esse arquivo, e a revisão confirma que a decisão `D-03` (Agent Skills + complemento em `.lia/`) está implementada em `model.py` |
| "Ausência do manifesto não invalida Agent Skill padrão" | PROPOSED | **Alinhado** — `_detect_type` classifica por `SKILL.md` sem exigir `.lia/` |
| Preservar metadado desconhecido na importação/exportação | **PROPOSED** | **Conflito `CONFIRMED`:** o Hub **descarta** chave desconhecida no topo (verificado) e **derruba** a listagem em chave desconhecida aninhada (A-3). O contrato §5.3 pede "preserve unknown metadata"; o código não preserva |
| Hash sobre "representação precisamente definida" | PROPOSED | **Parcialmente implementado.** `treeHash` cobre `path\0sha256\n` — definido e reproduzível (verifiquei 3 registros). Mas **`contentHash` é só o `SKILL.md`**, o que não cobre payloads multi-arquivo (`alethe`: 23 arquivos, `contentHash` descreve 1) |
| "Integrity mismatch deve impedir ativação" | PROPOSED | Implementado: `verify_integrity` existe; `repository.recompute_hashes` expõe divergência em `detail.integrityNow`. **Mas não há bloqueio automático de promoção por divergência** — é informativo |
| "Hashes não estabelecem autoria/assinatura" | PROPOSED | **Implementado e correto** (`integrity.py` docstring, `index.schema.json` com `signed: false` constante) |
| "Quarentena não é aprovação" | PROPOSED | **Implementado** (`stage` → `quarantine`; `promote` separado; `build_index` filtra `ACTIVE`) |
| "Host é autoritativo para executar/permitir" | PROPOSED | **Implementado por ausência** — o Hub não tem executor, credenciais nem orquestração em nenhum arquivo |
| Sem API Hub-host obrigatória; distribuição por arquivo | PROPOSED | **Alinhado** — `.lia-capability` é ZIP; hosts leem sem o Hub |

### 11.2 Fronteira Hub × outros produtos — confirmação dos números

| Recurso | Número da pesquisa | Verificação | Veredicto |
|---|---:|---|---|
| Capacidades no `registry.mjs` da Forge | 49 | **49 ids encontrados** (`character.*`, `env.*`, `export.*`…); `implemented` 16, `partial` 5, `proposed` 5, `planned` 24 | `CONFIRMED` exato |
| Tools do MCP `lia-forge` | 10 | **10 nomes `spriteforge_*` únicos** (`get_status`, `comfyui_status`, `list_comfyui_workflows`, `list_free_models`, `list_assets`, `create_asset`, `add_reference`, `prepare_task`, `update_stage`, `open_panel`) | `CONFIRMED` exato |
| Perfis Codex (Model-Lab) | 7 | **7 `.toml`**: `brand-reviewer`, `capability-architect`, `dataset-auditor`, `evaluation-reviewer`, `license-reviewer`, `model-researcher`, `training-planner` | `CONFIRMED` exato |
| Registros de modelo (Lia-Project) | 44 catalogados | não re-verificado arquivo a arquivo nesta revisão | `PARTIALLY_CONFIRMED` (referência cruzada) |
| Skills por repositório | Studio 16 · Project 22 · Model-Lab 9 · Forge 1 | **16** (17 entradas − `README.md`) · **22** · **9** (10 − `README.md`) · **1** | `CONFIRMED` exato, os quatro |

### 11.3 O gap de fronteira que a pesquisa não registrou

| # | Gap | Evidência | Impacto |
|---|---|---|---|
| **E-13** | **Nenhum dos 48 registros tem perfil de distribuição**, embora o contrato de host os exija e o modelo não tenha campo | `CAPABILITY-HOST` §4.2 propõe `distribution_profiles`; `model.py::Capability.as_dict()` não tem o campo; os 48 `capability.json` não têm a chave | Sem ele, um host não consegue distinguir "instrução de dev" de "capacidade de produto" pelo pacote — exatamente o risco que o contrato §2 lista em primeiro lugar. `TECHNICAL_ACTION` (campo) + `OWNER_DECISION` (quais perfis) |

### 11.4 Risco de transformar o Hub em outra coisa — avaliado

O pedido lista cinco coisas que o Hub **não** deve virar. Estado verificado:

| Anti-padrão | Evidência de que **não** ocorre | Risco residual |
|---|---|---|
| Runtime universal de Skills | Não há executor em `src/lia_agenthub/`; nenhum `subprocess`, `exec`, `import` dinâmico de payload | **Baixo** |
| Gerenciador de sessões de agentes | Não há conceito de sessão, agente, ou fila | **Baixo** |
| Gerenciador de credenciais | `secrets.envVars` guarda **nomes**; nada persiste valor; `DENY_NAMES` bloqueia `.env`, `.ssh`, `credentials` | **Baixo** |
| Orquestrador de execução | `app.py` só orquestra adaptadores de arquivo | **Baixo** |
| Executor automático de MCPs/CLIs importados | `_detect_type` classifica `mcp-server` por `package.json`, mas **não há conexão, spawn ou health-check** | **Baixo.** Ressalva: catalogar um `mcp-server` declara `containsScripts`/`egress`/`requirements` incompletos (E-7) |

**Conclusão:** a fronteira está **implementada**, não apenas declarada. Nenhuma das cinco degradações ocorre hoje. `CONFIRMED` e este é um mérito do produto.

**Uma observação sobre o nome, que é risco de arquitetura e não de código:** a Forge já chama de **"Hub"** seu `shared/hub/provider-hub.mjs` e de **"capability"** suas 49 capacidades de produção de assets. O Lia Agent Hub usa as mesmas duas palavras para outro domínio. A pesquisa registrou isso (§6.1 do inventário) e não propôs remédio. **Recomendação:** glossário de fronteira obrigatório em `docs/`, com os dois vocabulários lado a lado, antes de qualquer integração Forge↔Hub. `TECHNICAL_ACTION`, prioridade P2.

---

## 12. Revisão das decisões P-1…P-10

> As dez decisões do pedido §10. Quando a pesquisa usa o mesmo intervalo `P-1…P-10` com **outro conteúdo** (a auditoria de licença tem um `P-1…P-10` próprio: P-6 = ZIP Mr-Mak, P-7 = `derivedFrom`, etc.), há **colisão de identificador** com o registro `D-1…D-27` e com `P-1` do briefing. Isso precisa ser resolvido: `TECHNICAL_ACTION` P2. Abaixo, uso a numeração do **pedido**, e mapeio para os identificadores existentes.

| ID | Decisão necessária | Evidências disponíveis | Impacto | Dependências | Recomendação | Quem decide |
|---|---|---|---|---|---|---|
| **P-1** (= `D-16`) | Licença das criações Lia | 6 repos com `spdx_id: null`; Studio e Forge com MIT na branch; `THIRD_PARTY_NOTICES.md` do Hub já declara a ausência como deliberada; 13 Skills com material MIT de terceiro | **Destrava 35 Skills do grupo A.** Sem ela, nada sai em `shared`/`public` | P-1a/b/c (§5.1); P-2 para marca | **Recomendação §5.3: MIT uniforme + `TRADEMARK.md`.** Não decidir em nome do proprietário | **PROPRIETÁRIO** |
| **P-2** | Política de marca como camada | 5 sinais em `alethe`; exclusões explícitas em Studio e Forge; `brand-guidelines` da Anthropic | Define se `alethe` pode ser exportada | P-1; E-8/P-E8 | Tratar marca separada da licença, com `authorization` explícita e recusa em `shared`/`public` quando `none` | **PROPRIETÁRIO** |
| **P-3** | `assets/brands/` do `alethe`: manter, remover ou substituir | 5 arquivos verificados no commit `0093de09` | `BLOCKED` para redistribuição hoje | P-2 | **Recomendação técnica:** substituir por texto neutro, registrando a alteração (MIT permite; sem marca de terceiro). Não remover o crédito ao upstream | **PROPRIETÁRIO** (+ ação técnica) |
| **P-4** | Licença do `vercel-labs/agent-skills` (MIT só em README) | API `null`; 0 arquivos de licença em 477 entradas; README declara MIT | Nenhum dos 48 depende disso | — | Manter `RESEARCH_ONLY` até confirmação escrita. **Nada a fazer agora** | **PROPRIETÁRIO** (se quiser usar) |
| **P-5** | Adaptar `skill-creator`/`mcp-builder`/`webapp-testing` de `anthropics/skills` | **8 de 19 `LICENSE.txt` lidos: Apache-2.0** (incluindo as 3 alvo + `brand-guidelines`) | Escopo do Skill Creator/MCP Workshop | P-1 (compatibilidade Apache→MIT **é** compatível) | **`ADAPT_ALLOWED`** com aviso Apache + `NOTICE` + indicar alterações. Bloquear `brand-guidelines` por marca | **PROPRIETÁRIO** |
| **P-6** | ZIP `Mr-Mak-Skills-Free.zip` versionado no Lia-Studio | 9,9 MB, 764 arquivos, conteúdo de terceiros dentro de repo Lia | Risco de confusão de proveniência | — | Remover do repo e apontar ao upstream `cf1e126025…` | **PROPRIETÁRIO** |
| **P-7** | Aceitar `source.derivedFrom` | **A afirmação de compatibilidade está errada** (A-3). Necessário para 13 Skills | Sem ele, a derivação não sobrevive | **Pré-requisito: `Source.from_dict` tolerante** | **Aprovar o conceito; implementar só depois da correção de compatibilidade** | **TÉCNICA** (+ anuência sobre o campo) |
| **P-8** | Risco aceitável para Skills com `scripts/` | 1 dos 48 (`alethe`); `containsScripts: true`; `scripts/{orchestrate,diagram}.py` | Define se `alethe` pode ser promovida | P-3 | `alethe` exige revisão humana de scripts antes de `ACTIVE`. Os outros 47 não têm script | **PROPRIETÁRIO** (política) |
| **P-9** | Egress de Skills que orquestram serviço pago | 0 dos 48 declara `egress`; `alethe` coordena CLIs externas | Nenhum dos 48 faz egress próprio | — | Nenhuma ação para os 48. Relevante para `fal-ai-generation`/`higgsfield` (não catalogadas) | **PROPRIETÁRIO** |
| **P-10** | Skills `BLOCKED` podem ser **referenciadas** por URL sem cópia | `D-20` já formula o princípio; `guanyang/open-agent-hub` prova viabilidade de "link em vez de cópia" | Nenhum dos 48 é `BLOCKED` por ausência de licença de terceiro | — | **Referenciar metadado é aceitável**; copiar payload não. Modelo já permite (`source.upstream` guarda URL) | **PROPRIETÁRIO** |

### 12.1 Separação exigida pelo pedido

**Decisões do proprietário (não podem ser tomadas pelo agente):** P-1 (licença), P-1a (conceder ou não), P-2 (marca), P-3 (marca do `alethe`), P-4, P-5, P-6, P-8 (risco), P-9, P-10.
**Decisões técnicas (recomendação do agente, sujeitas a aceite):** pré-requisito de compatibilidade de `Source`; formato de `derivedFrom`; lugar de `trademark`; escopo do parser `metadata`; correção de `notice_required`; dois pontos de chamada de `folder_name`; reconciliação `index.schema.json` × `build_index`; glossário Forge×Hub; resolução da colisão `P-N`×`D-N`.
**Decisões operacionais:** procedimento de importação (§14); critério de aceitação (§14.4); plano de testes Windows (§14.6); política de quarentena.

**Aviso explícito:** as decisões técnicas **não estão aprovadas** por ter o proprietário declarado autoria. A declaração de autoria atualiza P-1 (o titular é ele, logo ele *pode* licenciar) — e não aprova nenhuma alteração de contrato.

---

## 13. Roteiro seguro de importação (desenhado, não executado)

### 13.1 Pré-condições — nenhuma é opcional

| # | Pré-condição | Estado hoje |
|---|---|---|
| G-0 | **P-1 decidida e registrada** (licença escolhida + `LICENSE` no repo de origem) | ❌ `OPEN` |
| G-1 | **P-2/P-3 decididas** (marca) | ❌ `OPEN` |
| G-2 | **A-4/E-11 corrigido** (`notice_required` refletir a licença) | ❌ defeito aberto |
| G-3 | **A-3 corrigido** (`Source.from_dict` tolerante) | ❌ defeito aberto |
| G-4 | **E-10 corrigido** (gerador chamar `check_references`; relatório reconhecer 81 avisos) | ❌ defeito aberto |
| G-5 | **Decisão sobre as 10 referências cross-skill** (E-10): importar em coorte ou aceitar aviso | ❌ não decidido |
| G-6 | Hub **mergeado em `main`** (ou decisão explícita de operar a partir da branch) | ❌ não integrado |
| G-7 | Ambiente Windows de validação disponível | ❌ `BLOQUEADO` no relatório Windows (D-01…D-09) |

### 13.2 Sequência

| Fase | Passos | Saída exigida | Portão |
|---|---|---|---|
| **F0 — Política** | 1. Registrar P-1, P-2, P-3 com `APPROVED` + responsável + data. 2. Publicar `LICENSE` nos repositórios. 3. Publicar `TRADEMARK.md` | Decisão registrada em `DECISION-REGISTER.md` | **Nenhuma importação antes disso** |
| **F1 — Classificação** | 4. Fixar a classificação A/B/C dos 48 num documento **revisável e versionado** (hoje só existe em `researchNotes`) | `SKILL-CLASSIFICATION.md` com as 48 linhas e evidência por linha | Revisão humana da classificação |
| **F2 — Contratos** | 5. Corrigir `notice_required`. 6. Tornar `Source.from_dict` tolerante. 7. Corrigir o gerador (E-10). 8. Implementar P-E1, P-E2, P-E6. 9. Decidir P-E3, P-E4, P-E8. 10. Reconciliar `index.schema.json` com `build_index` | Suíte verde + testes novos de compatibilidade | **Teste obrigatório: registro com campo novo não derruba `list_all()` de versão antiga** |
| **F3 — Validação de manifesto** | 11. Regerar os 48 registros com o gerador corrigido. 12. Conferir `id`/`contentHash`/`treeHash` contra o Hub real (1 por vez) | Relatório de divergência. **Critério: zero divergência.** Qualquer divergência invalida a ferramenta, não é "diferença aceitável" | Aceite do critério |
| **F4 — Importação controlada** | 13. Importar **1** Skill (`lia-game-qa-plan`, 1 arquivo, sem script) numa biblioteca temporária. 14. Comparar `id`/hashes. 15. Importar em coortes de 5, **sempre em quarentena**. 16. `alethe` **sozinha e por último**, após P-3 | 48 itens em `Quarentena`, **0 em `Biblioteca`** | **Nenhuma promoção automática** |
| **F5 — Quarentena e revisão** | 17. Revisão humana item a item: licença resolvida? aviso presente no payload? derivação registrada? marca ok? | Decisão por item, registrada em `history.json` | **A importação não pode transformar `BLOCKED` em aprovado** |
| **F6 — Windows** | 18. Repetir F3–F5 em Windows, com o mesmo critério de hash | Evidência revisável | `VALIDATED` só existe depois disto |
| **F7 — Aceitação** | 19. Relatório final assinado. 20. `lifecycle: ACTIVE` só com licença resolvida | Aceite formal | — |

### 13.3 Regras invioláveis do roteiro

1. **Nenhuma Skill é executada durante a importação.** O Hub não tem executor; o roteiro não pode introduzir um.
2. **Nenhum `BLOCKED` vira aprovado por ter sido importado.** `trust: unreviewed` e `lifecycle: quarantined` são o estado final da importação.
3. **Origem, histórico, hashes, licença e atribuições são preservados.** Se um campo não couber no contrato, ele **não é descartado** — fica em documento complementar, nunca em chave inventada dentro de `capability.json`.
4. **`alethe` é a última e não entra em coorte.** 23 arquivos, scripts, e 5 marcas de terceiro.
5. **Divergência de hash interrompe a fase.** Não é aviso.

---

## 14. Matriz de riscos

| ID | Risco | Prob. | Impacto | Severidade | Mitigação | Estado |
|---|---|---|---|---|---|---|
| **R-1** | **Perda da classificação A/B/C na importação**: `originClass` só existe em `researchNotes`; 48 Skills entram indistinguíveis, todas `unreviewed`/`unknown` | **Alta** | **Alto** | **Crítico** | Fase F1 (documento versionado) **antes** de F4. Não depender de `researchNotes` em produção | `BLOCKED` |
| **R-2** | **Redistribuição sem aviso de terceiro**: 13 Skills derivadas de MIT, aviso fora do payload, `notice_required` nunca `true`, `NOTICE` nunca gerado | **Alta** | **Alto** (violação MIT) | **Crítico** | A-4/E-11 + convenção §7.4 da auditoria + teste de exportação verificando `NOTICE` no ZIP | `TECHNICAL_ACTION` |
| **R-3** | **`shared` só avisa e prossegue**, mesmo com licença desconhecida ou marca de terceiro | **Média** | **Alto** | **Alto** | P-E8: recusa em `shared`/`public` quando houver marca de terceiro sem autorização. Hoje `public` já é recusado; `shared` não | `TECHNICAL_ACTION` |
| **R-4** | **Biblioteca inutilizável por campo novo aninhado** (A-3) | **Média se P-E4 for implementado como proposto** | **Alto** (perda de acesso a toda a biblioteca) | **Crítico se não corrigido** | Corrigir `Source.from_dict` **antes**; teste bidirecional obrigatório | `TECHNICAL_ACTION` |
| **R-5** | **Marca de terceiros distribuída** (`alethe/assets/brands/`) | Média | Alto (direito marcário) | **Alto** | P-3 + P-E8 | `BLOCKED` (P-2) |
| **R-6** | **`.lia/` do payload vira manifesto dentro do pacote** (E-12) | Média | Médio (confusão de metadado / capacidade auto-declarada `first-party`) | Médio | Adicionar `.lia` a `DENY_NAMES` de `paths.py`; decidir se o payload pode conter metadado do Hub | `TECHNICAL_ACTION` |
| **R-7** | **81 referências ausentes tratadas como "2 avisos"** (E-10) | **Certa** | Médio (decisão tomada sobre risco subdeclarado) | **Alto** | Regerar com `check_references`; decidir coorte | `TECHNICAL_ACTION` |
| **R-8** | **47 Skills sem `LICENSE` no payload** — cada exportação individual fica sem base de licença visível | **Certa** | Médio | **Alto** | P-1 + convenção de payload | `BLOCKED` (P-1) |
| **R-9** | **Nenhuma validação Windows** de nada desta importação | **Certa** | Médio | Médio | F6 | `BLOCKED` (ambiente) |
| **R-10** | **Confusão Forge×Hub** ("Hub" e "capability" com dois sentidos) | Média | Médio (arquitetura/comunicação) | Médio | Glossário de fronteira | `TECHNICAL_ACTION` |
| **R-11** | **Skills escritas segundo o kit do proprietário geram `UNKNOWN_FIELD`** (`paths`, `context: fork`) | **Certa** | Baixo-Médio | Médio | Decidir junto com P-E3 | `TECHNICAL_ACTION` |
| **R-12** | **Colisão de identificador `P-1…P-10`** entre briefing, auditoria e registro `D-N` | **Certa** | Baixo (processo) | Baixo | Unificar em `D-*` no `DECISION-REGISTER.md` | `TECHNICAL_ACTION` |
| **R-13** | **Confiar em hash como aprovação** | Baixa (código diz o contrário em 4 lugares) | Alto se ocorrer | Baixo | Já mitigado; manter | Monitorar |
| **R-14** | **`index.schema.json` não descreve o que `build_index` emite** (5 campos fora do schema: `author`, `description`, `domain`, `redistributable`, `tags`) | **Certa** | Baixo (host que validar pelo schema publicado pode rejeitar índice válido) | Médio | Reconciliar schema × emissor | `TECHNICAL_ACTION` |

---

## 15. Decisões que dependem do proprietário — consolidado

> Nenhuma destas pode ser tomada pelo agente. Nenhuma foi assumida neste documento.

| # | Decisão | Bloqueia | O que o agente pode oferecer |
|---|---|---|---|
| **D-A** | **P-1a:** o proprietário concede licença a terceiros para as 35 Skills do grupo A? | 35 Skills | Recomendação de forma (§5.3) |
| **D-B** | **P-1b:** MIT, Apache-2.0 ou outra? Uniforme ou por repositório? | 47 Skills | Comparação completa (§5.2) + recomendação MIT fundamentada |
| **D-C** | **P-1c:** `LICENSE` na raiz, no payload, ou ambos? | Empacotamento de todas | Convenção proposta (§5.5) |
| **D-D** | **P-1 separado para `Lia-Go` e `Lia-AgentHub`**, que não têm Skills | O produto, não o catálogo | Análise separada (§5.4) |
| **D-E** | **P-2:** política de marca como camada separada | `alethe`; toda exportação | Estrutura proposta (§7.8, §9.2) |
| **D-F** | **P-3:** `alethe/assets/brands/` — manter, remover ou substituir? | `alethe` | Recomendação técnica: substituir por texto neutro |
| **D-G** | **P-8:** risco aceitável para `containsScripts` | `alethe` | — |
| **D-H** | Aprovar as 10 referências **cross-skill** como aviso aceitável, ou importar em coorte? | 5 Skills do Project | — |
| **D-I** | Aprovar ou rejeitar **P-E3** (parser `metadata` aninhado) | 1+ Skills hoje, todas as futuras | Escopo recomendado (§7.5) |
| **D-J** | Aprovar ou rejeitar **P-E4** (`source.derivedFrom`) | 13 Skills | Formato + pré-requisito de compatibilidade (§7.4) |
| **D-K** | Aprovar ou rejeitar **P-E8** e onde o campo mora | `alethe` | Recomendação: fora de `License` (§7.8) |
| **D-L** | O que é **obrigatório** entre os seis conceitos (`created_by`, `rights_holder`, `license`, `derived_from`, `attribution`, `trademark`) | Contrato | Análise de onde cada um já cabe (§7.9) |
| **D-M** | **P-5:** adaptar `skill-creator`/`mcp-builder`/`webapp-testing` | Fase 1 | 8 de 19 `LICENSE.txt` já verificados: Apache-2.0 |
| **D-N** | **P-6:** remover o ZIP Mr-Mak do Lia-Studio | Proveniência do Studio | — |
| **D-O** | **P-10:** referenciar Skills `BLOCKED` por URL | Catálogo futuro | — |

---

## 16. Próxima sequência de implementação

> Ordem por **desbloqueio**, não por esforço. Cada item indica o que ele destrava.

### Bloco 1 — Correções técnicas que não dependem de nenhuma decisão (podem começar já, em branch própria, com autorização de implementação)

| # | Ação | Destrava | Teste |
|---|---|---|---|
| 1 | `Source.from_dict()` tolerante a chave desconhecida (espelhar `License.from_dict`) | **Toda evolução futura do contrato.** Sem isto, P-E4/P-E8 criam R-4 | Bidirecional: registro novo → `list_all()` de versão antiga **não** pode levantar |
| 2 | `notice_required` refletir a licença detectada/declarada (E-11) | R-2; obrigação MIT | Exportar Skill MIT → ZIP **contém** `NOTICE` |
| 3 | Adicionar `.lia` a `DENY_NAMES` (E-12) | R-6 | Importar payload com `.lia/` → recusa ou exclusão explícita |
| 4 | `check_references` no gerador de pesquisa (E-10) | R-7; base para F3 | Gerar 48 → **29 com `REFERENCE_MISSING`**, 81 avisos |
| 5 | Corrigir `folder_name` nos **dois** pontos (`importer.py`, `app.validate`) (E-6) | 2 falsos positivos | `alethe` e `bootstrap` sem `NAME_FOLDER_MISMATCH` |
| 6 | `description` do frontmatter como fallback (P-E1) | 48 registros utilizáveis | 48/48 com descrição |
| 7 | Licença do frontmatter como **declaração** (P-E2) | 1 Skill hoje, todas as futuras | `code=MIT, status=declared, redistributable=false` |
| 8 | Reconciliar `index.schema.json` × `build_index` (R-14) | Índice validável por terceiro | Índice real valida contra o schema publicado |

### Bloco 2 — depois de D-A…D-C (P-1)

| # | Ação |
|---|---|
| 9 | Publicar `LICENSE` nos 4 repositórios + `TRADEMARK.md` |
| 10 | Publicar `SKILL-CLASSIFICATION.md` com as 48 linhas (F1) — **fecha R-1** |
| 11 | Implementar P-E4 e P-E8 conforme decisão (D-J, D-K) |

### Bloco 3 — depois de Bloco 1+2, com Windows

| # | Ação |
|---|---|
| 12 | Resolver `P-3` (marca do `alethe`) |
| 13 | Executar F3→F7 do roteiro (§13.2) |
| 14 | Validar no Windows. **Só depois disso algo é `VALIDATED`** |

### O que **não** fazer

- **Não** importar os 48 "aplicando os registros". Isso não é suportado pelo produto (A-2) e perderia 9 blocos de informação (§8.2).
- **Não** implementar P-E7 (`requirements` a partir de prosa) — é inferência contra o contrato.
- **Não** implementar P-E5 como descrito — o manifesto de diretório não é lido como tipo (E-5).
- **Não** "corrigir" E-9 removendo o filtro de `ACTIVE` no índice. O comportamento atual está correto e é exigido por `SECURITY` e `CAPABILITY-HOST §7.4`.
- **Não** tratar hash válido como autorização. Os 48 são reproduzíveis — e isso não autoriza nenhum deles.

---

## 17. Fechamento — respostas objetivas às perguntas do pedido

### 17.1 O que foi examinado

**Branch examinada:** `arena/1a7ed773-lia-agenthub` (esta sessão), com leitura de `origin/arena/db625478-lia-agenthub` (pesquisa), `origin/arena/a92004be-lia-agenthub` (Hub) e `origin/main`.

**HEAD observado:** `b4e63eae800b2713dcda294e3c2dfe8d60eb0b04` nesta branch; `704dfd3f7138a0c300639d9f9a29bf37bb947578` no Hub; `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` em `main`.

**Arquivos examinados (34):**

- *Pesquisa (13):* `docs/research/{README,LIA-SKILLS-INVENTORY,THIRD-PARTY-SKILLS-CATALOG,SKILL-LICENSE-AND-PROVENANCE-AUDIT,LIA-SKILLS-ROADMAP,SKILL-CATALOG-IMPORT-REPORT}.md`, `docs/research/catalog/{README,sources,lia-studio.records,lia-project.records,lia-model-lab.records,lia-forge.records}`, `docs/research/tools/build-catalog-records.py`
- *Hub — código (12):* `src/lia_agenthub/domain/{model,integrity,skills,risk,paths}.py`, `src/lia_agenthub/adapters/{importer,repository,index_builder,packager,safe_extract}.py`, `src/lia_agenthub/app.py`, `src/lia_agenthub/interface/server.py`
- *Hub — documentos (5):* `docs/architecture/{CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT,PRODUCT-BOUNDARIES-AND-ARCHITECTURE,SECURITY-AND-TRUST-MODEL}.md`, `docs/DECISION-REGISTER.md`, `docs/operations/WINDOWS-VALIDATION-REPORT.md`, `THIRD_PARTY_NOTICES.md`
- *Testes e kit (4):* `tests/unit/test_skills.py`, `tests/integration/test_settings_and_versions.py`, `tests/integration/test_import_flow.py`, `docs/KIT-PROJETO-NOVO.zip`
- *Externos (10 repositórios via API)* + **48 `SKILL.md` reais** nos commits fixados

### 17.2 Evidências confirmadas (resumo)

| Classe | Quantidade | Destaque |
|---|---:|---|
| `CONFIRMED` | 24 | Os 9 gaps E-1…E-9, todos os 10 repositórios externos, os 4 números de fronteira (49/10/7/44), a contagem de 48/16/22/9/1 |
| `CONFIRMED` (defeito **novo**, não na pesquisa) | 4 | E-10 (81 referências ausentes), E-11 (`notice_required` nunca `true`), E-12 (`.lia/` atravessa o pipeline), E-13 (sem perfil de distribuição no registro) |
| `VALIDATED` | 7 | 4 `contentHash` + 3 `treeHash` recalculados do GitHub com `MATCH`; 4 commits de origem existentes; 8 `LICENSE.txt` Apache-2.0 lidos; `LICENSE` de `modelcontextprotocol` e `hesreallyhim` lidos |
| `PARTIALLY_CONFIRMED` | 5 | Titularidade (a pesquisa acertou a regra, errou o diagnóstico); `airi-upstream-integration` como "origem AIRI"; E-7 como gap; os 44 registros de modelo; a magnitude da derivação das 12 adaptadas |
| `NOT_CONFIRMED` | 1 | **E-9 como defeito.** É política correta, não lacuna |
| `OWNER_DECISION` | 15 | §15 |
| `TECHNICAL_ACTION` | 14 | §16 Bloco 1 + P-E3/P-E4/P-E6/P-E8 + glossário + colisão de IDs |
| `BLOCKED` | 3 conjuntos | 35 (grupo A, por P-1) · 12 (grupo B, por P-1 + aviso) · 1 (`alethe`, por marca + scripts) |

### 17.3 Limitações desta revisão

1. **Nada foi validado em Windows.** Toda execução foi Linux. O relatório Windows do Hub (`704dfd3f`) registra `D-01…D-09` como `BLOQUEADO`. `VALIDATED` para Windows continua não existindo no ecossistema.
2. **A validação de hash é por amostragem:** 4 de 48 `contentHash`, 3 de 48 `treeHash`. Foram escolhidas as de maior risco (multi-arquivo, com script, adaptada, autoral). Reprodução total exige os checkouts locais e o gerador.
3. **O `REFERENCE_MISSING` foi calculado com o código do Hub sobre conteúdo real**, mas **não** pela importação real — a contagem (29 Skills / 81 referências) é do algoritmo, não de uma execução do produto sobre pasta local. A classe é `EXECUTED`, não `VALIDATED`.
4. **Não re-verifiquei os 44 registros de modelo do Lia-Project** nem as 29 Skills do AIRI nem as 20 do ZIP Mr-Mak — referência cruzada, como a pesquisa declarou.
5. **Não é parecer jurídico.** Classificações A/B/C e comparações de licença são engenharia/compliance documental.
6. **Não li os 19 `LICENSE.txt` da Anthropic** — li 8 dos 19 mais relevantes. Os outros 11 continuam "por nome de arquivo".
7. **`skills.sh` não foi alcançado** — mantida a limitação declarada pela pesquisa.

### 17.4 A importação está autorizada tecnicamente?

# ❌ NÃO.

**Quatro bloqueios independentes, e três deles são defeitos, não decisões:**

| # | Bloqueio | Natureza | Fecha com |
|---|---|---|---|
| 1 | **G-0: P-1 não decidida** — nenhuma das 48 tem licença de distribuição outorgada | **Decisão do proprietário** | D-A, D-B, D-C |
| 2 | **G-2/G-3: dois defeitos críticos abertos** — `notice_required` nunca `true` (viola MIT na exportação) e `Source` intolerante (inviabiliza o campo de derivação sem derrubar a biblioteca) | **Defeito técnico** | §16 Bloco 1, itens 1–2 |
| 3 | **G-4: o catálogo está subdeclarado em 81 avisos** — a decisão de importar foi tomada sobre "2 avisos"; o real é 2 + 81, incluindo 10 referências cross-skill | **Defeito técnico** | §16 Bloco 1, item 4 + D-H |
| 4 | **G-6/G-7: o Hub não está em `main` e não há validação Windows** da importação | **Processo/ambiente** | F6 do roteiro |

**Nenhum dos 48 registros pode ser promovido a `ACTIVE` hoje.** E — importante — **nem se tudo acima fosse resolvido**: a importação em si é uma operação de **reimportar 48 payloads**, não de aplicar 48 registros.

### 17.5 Quais decisões dependem do proprietário

**Quinze** (D-A…D-O, §15). As cinco que travam tudo:

1. **D-A/D-B/D-C — P-1:** conceder licença? qual? onde o instrumento vive?
2. **D-E/D-F — P-2/P-3:** política de marca e o destino de `alethe/assets/brands/`.
3. **D-L:** quais dos seis conceitos (`created_by`, `rights_holder`, `license`, `derived_from`, `attribution`, `trademark`) são **obrigatórios** no registro — e quais ficam em documento complementar.
4. **D-I/D-J/D-K:** aprovar P-E3, P-E4, P-E8 (as três mudanças de contrato).
5. **D-H:** aceitar as 10 referências cross-skill como aviso, ou importar essas 5 Skills em coorte.

### 17.6 Recomendação objetiva da próxima etapa

**Executar o Bloco 1 de §16 — oito correções técnicas que não dependem de nenhuma decisão do proprietário** —, em paralelo a levar D-A…D-O ao proprietário. O Bloco 1 é pequeno, é testável, corrige os três defeitos críticos (R-2, R-4, R-6/R-7) e **não toca em licença, marca ou política**. É o único trabalho que pode avançar hoje sem violar o mandato.

Em seguida, e só depois de P-1: F1 (classificação versionada) → F3 (regeneração com o gerador corrigido) → F4 (importação em quarentena) → F6 (Windows).

> **Um último julgamento sobre a pesquisa, que é o motivo desta revisão existir.** Ela acertou nos nove gaps, nos hashes, na separação de licença por camada, na recusa de transformar ausência de licença em permissão e na disciplina de não aprovar nada. Seu erro de método foi único e sistemático: **ela mediu o modelo de dados e chamou o resultado de auditoria de importação** — por isso não viu que o pipeline não reproduz `check_references` (81 avisos), que `notice_required` nunca liga, que `Source` não é tolerante, e que os registros não são o insumo da importação. Um revisor que aceitasse o relatório como está teria aprovado uma importação sobre um risco 40× menor do que o real. **A conclusão prática é que a pesquisa é confiável como inventário e como auditoria de licença, e não é confiável como especificação de importação.**

---

## Anexo A — Artefatos de evidência reproduzíveis

Preservados em `docs/review/evidence/` (somente leitura, sintéticos — nenhum payload de terceiro):

| Arquivo | O que prova |
|---|---|
| `probe-01-e1-e3-e6.py` | E-1 (`description` vazia), E-3 (`metadata` aninhado perdido), E-6 (`NAME_FOLDER_MISMATCH` espúrio) |
| `probe-03-e9-listing.py` | E-9 (listagem só de `ACTIVE`) + o comportamento de `SearchQuery(lifecycle="all")` |
| `probe-04-dot-lia-passthrough.py` | E-12 (`.lia/capability.json` do payload chega ao pacote exportado) |
| `probe-05-provenance-roundtrip.py` | Perda de `source.*` no ciclo exportar→reimportar |

Execução: `git archive origin/arena/a92004be-lia-agenthub | tar -x -C /tmp/hub && cd /tmp/hub && python3 <probe>`. Requer apenas Python 3 (stdlib). Nenhum arquivo fora de diretório temporário é tocado.

## Anexo B — Comandos de verificação independente

```bash
# 1. Pesquisa: 13 arquivos no compare com main
git diff --name-status origin/main origin/arena/db625478-lia-agenthub | wc -l   # → 13

# 2. Hub: 79 arquivos, 44 commits, não integrado em main
git ls-tree -r --name-only origin/arena/a92004be-lia-agenthub | wc -l           # → 79

# 3. Suíte do Hub (284 passed)
git archive origin/arena/a92004be-lia-agenthub | tar -x -C /tmp/hubfull
cd /tmp/hubfull && python3 -m venv /tmp/venv && /tmp/venv/bin/pip install -q pytest
/tmp/venv/bin/python -m pytest -q

# 4. Licença: nenhum dos 6 repositórios Lia tem SPDX
for r in Lia-Project Lia-Model-Lab Lia-Go Lia-AgentHub Lia-Studio Lia-Forge; do
  curl -s "https://api.github.com/repos/BloomRX/$r" | python3 -c \
    'import sys,json;print(json.load(sys.stdin).get("license"))'; done
```
