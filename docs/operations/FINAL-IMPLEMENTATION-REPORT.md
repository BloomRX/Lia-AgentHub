# Relatório Final de Implementação — Lia Agent Hub

**Data:** 2026-11-15
**Branch:** `arena/a92004be-lia-agenthub`
**Base:** `main` = `34a27f4` (intacta, local e remoto)
**HEAD na entrega:** ver §8 (hash e estado final)

---

## 1. Resumo executivo

O Lia Agent Hub está utilizável como infraestrutura pelos demais projetos Lia.
C1–C8 estão resolvidos, as propostas P-E1 e P-E2 estão implementadas e testadas,
e os cinco contratos de integração (Lia Go, Lia Studio, Lia-Project, Lia Forge,
Lia Model Lab) têm testes executáveis — não apenas documentação.

O fato mais importante deste relatório não é o que foi concluído, é o que foi
**revertido**. O bloco anterior aprovou a correção C4 e eu a declarei `PASS`. A
revisão independente reprovou: ela recusava **16 de 53 Skills reais (30%)** na
importação. Reproduzi a falha, achei a causa e corrigi a decisão de projeto, não
só o código. Está registrado em §3.1 e no próprio relatório do Bloco 1, sem
apagar a afirmação original.

| Métrica | Antes do Bloco 1 | Bloco 1 (`891a1d9`) | Agora |
|---|---|---|---|
| Testes passando | 285 | 361 | **447** |
| Skills reais que importam | 53/53 | **37/53** | **53/53** |
| Skills reais bloqueadas | 0 | **16** | **0** |
| Erros falsos de referência | 0 | **42** | **0** |
| `NAME_FOLDER_MISMATCH` espúrio | 25 | 25 | **0** |
| Descrições vazias no catálogo | 53/53 | 53/53 | **0/53** |
| `author` de terceiro perdido | 8/53 | 8/53 | **0/53** |
| `validate.sh` | 4/4 | 4/4 | **4/4** |
| `verify-consistency` (padrão) | 44/44 | 44/44 | **44/44** |

Os números da coluna "Agora" foram medidos com
`docs/operations/evidence/corpus_probe.py` contra os `SKILL.md` reais dos quatro
repositórios Lia, nos commits registrados em
`docs/research/catalog/sources.json`.

---

## 2. Método de validação

Todo número deste relatório é reproduzível. O que **não** foi executado está
marcado como tal (§6).

### 2.1 Corpus real

Os payloads reais **não estão vendorizados** neste repositório (são conteúdo de
terceiros e de outros projetos). O harness `corpus_probe.py` espera os clones em
`$LIA_CORPUS` (padrão `/tmp/liacorpus`) e mede sem gravar nada:

```bash
# obtenção (reproduz o que foi feito nesta rodada)
GIT_LFS_SKIP_SMUDGE=1 git clone --filter=blob:none --no-checkout \
  https://github.com/BloomRX/Lia-Studio.git /tmp/liacorpus/studio
# ... demais repos; checkout nos commits de docs/research/catalog/sources.json
# Lia-Studio 203b60f | Lia-Model-Lab 3ec4313 | Lia-Project 0093de09 | Lia-Forge 35b207f

PYTHONPATH=src .venv/bin/python docs/operations/evidence/corpus_probe.py
```

> **Nota sobre contagem.** O relatório de pesquisa fala em 48 Skills. Medi 53
> `SKILL.md` nos quatro repositórios no estado atual — o repositório Lia-Project
> tem Skills em mais de uma raiz (`.agents/skills` e `airi/.agents/skills`). Uso
> **53**, o número que efetivamente medi, em vez de 48, que é o número que
> esperava encontrar. A diferença não muda nenhuma conclusão: as duas contagens
> passam de 16 bloqueadas para 0.

### 2.2 Suítes

```bash
.venv/bin/python -m pytest tests/     # 447 passed
bash scripts/validate.sh              # 4/4, 44/44, 24 arquivos, sem segredos
```

### 2.3 Distribuição dos testes

| Arquivo | Testes | Cobre |
|---|---|---|
| `integration/test_block1_fixes.py` | 80 | C1–C5, C8 do Bloco 1 |
| `integration/test_review_fixes.py` | 52 | **cada achado da revisão** |
| `security/test_path_traversal.py` | 40 | travessia, symlink, nomes |
| `integration/test_ui.py` | 34 | UI |
| `unit/test_skills.py` | 33 | parser e validação |
| `unit/test_unicode_policy.py` | 32 | bidi, tag, homoglifo |
| `integration/test_host_contracts.py` | 30 | **contratos dos 5 hosts** |
| `integration/test_persistence.py` | 26 | registro e recuperação |
| `integration/test_import_flow.py` | 24 | importação ponta a ponta |
| `security/test_integrity_and_packages.py` | 19 | hash, pacote, adulteração |
| `security/test_archives.py` | 17 | ZIP, bomb, symlink |
| `integration/test_settings_and_versions.py` | 17 | lifecycle |
| `integration/test_windows_readiness.py` | 14 | caminhos Windows |
| `integration/test_packaging.py` | 13 | exportação |
| `unit/test_risk.py` | 8 | risco |
| `integration/test_ui_structure.py` | 8 | estrutura de UI |

---

## 3. Defeito mais grave encontrado e corrigido

### 3.1 C4 recusava 30% do acervo real

**Sintoma.** A revisão independente mediu, em cópia limpa, que o commit
`891a1d9` recusava a importação de 16 de 48 Skills reais. Reproduzi de forma
independente: **16 de 53**, com 42 erros falsos.

**Causa.** Eu tratei referência em prosa como gate de segurança. Consequências
concretas:

- `lia-browser-automation` cita `` `/json/list` `` — endpoint do protocolo CDP que
  a própria Skill ensina a usar. Virou `REFERENCE_INVALID` com severidade
  `ERROR`, e `ERROR` bloqueia a importação. **Uma Skill não podia ser importada
  por descrever o endpoint que ela mesma opera.**
- `capability-mapping` cita `../../../docs/02-LIA-CAPABILITY-MATRIX.md` — caminho
  legítimo dentro do monorepo. Idem.
- `lia-vue-development` cita `` `/` `` — rota. Idem.

**A decisão de projeto estava errada, não só a implementação.** Referência é
texto: descreve a intenção do autor. Não é um caminho que o Hub vá abrir. A
segurança real de caminho acontece onde arquivos são lidos e escritos
(`domain/paths.py`, `adapters/safe_extract.py`) e nunca dependeu disso. Uma
verificação que recusa um recurso por causa do que ele *escreve* é um falso
positivo estrutural, porque o texto nunca vira acesso.

**Correção.** `check_references` é lint de prosa e não recusa nada:

| Código | Severidade | Significado |
|---|---|---|
| `REFERENCE_CROSS_SKILL` | info | cita outra Skill — normal em monorepo |
| `REFERENCE_ESCAPE` | warning | `..`/drive/UNC — portabilidade, não ataque |
| `REFERENCE_MISSING` | warning | citado e ausente do payload |
| `REFERENCE_EXTERNAL` | info | rota/endpoint, não é arquivo |

Efeito colateral: `NAME_FOLDER_MISMATCH` espúrio caiu de 25 para 0.

**Contraprova.** A relaxação não abriu buraco: `escaping_references` continua
detectando `../../etc/passwd`, `C:/Windows/win.ini` e `\\servidor\share`. Há
teste para cada um, e as proteções de arquivo continuam sendo exercitadas por
`security/test_path_traversal.py` (40 testes).

### 3.2 Outros dois defeitos que ninguém tinha visto

Encontrados ao escrever os testes dos achados da revisão.

**`SKILL.md` vazio importava sem uma única issue.** A linha
`files.get("SKILL.md") or files.get("skill.md")` parece inofensiva. Mas `b""` é
**falso** em Python, então a expressão caía no segundo termo (`None`) e toda a
validação estrutural era **pulada**. Um arquivo sem uma linha de frontmatter era
estagiado com zero issues. Corrigido testando presença de chave.

**Atalho de reimportação devolvia relatório sem hash.** Quando o conteúdo já
existia, a função voltava antes de calcular os hashes — justamente no caso em
que o chamador mais precisa comparar com o que já tem. Hashes agora são
calculados antes de qualquer atalho.

---

## 4. C1–C8: estado final

| # | Item | Estado | Como foi validado |
|---|---|---|---|
| C1 | `Source` tolerante | ✅ | 5 formatos legados lidos, 0 erros; campo desconhecido sobrevive ao roundtrip |
| C2 | Licenças / NOTICE | ✅ | NOTICE com texto real, per-Skill, com caminho; verificado com Skill de terceiro |
| C3 | Segurança de `.lia/` | ✅ | travessia, symlink, bomb, falsificação de trust: 4/4 bloqueados |
| C4 | Referências | ✅ | 53/53 Skills reais importam; cross-skill alcançável e testado |
| C5 | `folder_name` | ✅ | 8 casos de borda, ramo morto removido, rótulo ≠ pasta |
| C6 | P-E1 | ✅ | descrição 53/53 (era 0) |
| C7 | P-E2 | ✅ | declaração registrada; `redistributable` continua `False` |
| C8 | Índice / lifecycle | ✅ | quarentena nunca publicada; adulteração detectada por `index_health` |

### 4.1 C1 — tolerância de `Source`

Cinco formatos legados plausíveis lidos sem erro: sem `license`; `license` sem
`status`; `source` parcial; campo desconhecido; `notice_required` explícito.

Dois comportamentos que valem registro:

- `license: {code: MIT}` **sem** `notice_required` deriva `True` da tabela de
  obrigações. Errar para cima produz arquivo a mais; errar para baixo produz
  violação de licença.
- `notice_required: false` **explícito** é respeitado, não sobrescrito.

Campo desconhecido agora sobrevive ao roundtrip em **dois** níveis —
`License` (R-1.2) e `Capability` (achado desta rodada). Sem isso, um Hub antigo
lia um registro de um Hub novo e perdia o campo em silêncio.

### 4.2 C2 — licenças e NOTICE

Descoberta em quatro lugares, nesta ordem de confiança: (1) arquivo de licença
no payload — inclusive em subpasta, que é a forma dominante no acervo real;
(2) frontmatter `license`; (3) `metadata:` aninhado; (4) ausência declarada.

O `NOTICE` carrega o **texto real**, com o marcador de copyright do autor
original e o caminho do arquivo de onde veio. Verificado ponta a ponta com
`vue-best-practices` (Skill real de terceiro, MIT):

```
license.code: MIT | status: declared | redistributable: False
NOTICE cita o copyright do terceiro?  True   ("hyf0, SerKo")
NOTICE cita caminho do arquivo?       True   ("LICENSE.md")
THIRD_PARTY_NOTICES diz 'NÃO DECLARADA'?  False
```

**Nenhuma licença foi escolhida por mim.** Não criei `LICENSE` nem
`TRADEMARK.md`. A situação jurídica de cada recurso continua sendo decisão do
proprietário; o que está implementado é o **mecanismo** de atribuição.

### 4.3 C3 — segurança

Vetores testados e bloqueados:

| Vetor | Resultado |
|---|---|
| ZIP `../../evil.md` | recusado |
| symlink no ZIP (`external_attr`) | recusado |
| zip bomb (50 MB → 50 KB, 1028:1) | recusado por taxa de compressão |
| `.lia/` no payload (falsificar `trust`) | recusado |
| `CON`, `aux.txt`, `a:b.md` | recusado |
| travessia de escrita fora de `locations` | recusado |

**Vetor novo encontrado nesta rodada: nome de arquivo.** O scanner Unicode só
inspecionava o *corpo* de `.md/.txt/.json`. `a\u202egnp.exe` (U+202E inverte o
que o usuário vê — ele lê `aexe.png`) passava sem sinalização. Um script com
nome forjado não precisa de extensão de texto para enganar quem revisa. Agora
todo nome passa por `scan(context=IDENTIFIER)` → `UNICODE_FILENAME` + revisão
humana obrigatória.

### 4.4 C4 — referências

Ver §3.1 para o defeito e a correção.

- **Cross-skill funciona.** Antes era inalcançável: `pastas_de_skill` derivava
  apenas de `available`, então uma Skill citando *outra* (que por definição não
  está neste payload) nunca casava. Agora reconhece a convenção real
  `.agents/skills/<nome>/SKILL.md`. `folder_name` passou a ser realmente
  passado nos dois pontos de produção — antes era calculado uma linha antes e
  descartado.
- **`/json/list` não é erro estrutural.** Há 4 testes só para endpoints, mais o
  contrapositivo de que escape de verdade continua detectado.

### 4.5 C5 — `folder_name`

Comportamento aprovado mantido; 8 casos de borda cobertos. Ramo morto removido.
Novo: um `upstream` que é **rótulo** (`probe`, `repo@commit:caminho`) não é
tratado como caminho — inventar uma pasta ali produziria comparação falsa, que
era a origem do `NAME_FOLDER_MISMATCH` espúrio.

### 4.6 C6 / C7 — P-E1 e P-E2

O bloqueio anterior estava **errado** e a correção está registrada em
`BLOCK-1-IMPLEMENTATION-REPORT.md`. Texto literal de §4.3, respeitado:

> **P-E1** — "`description`: usar frontmatter como fallback quando não houver
> manifesto — aditiva (só preenche o que hoje é vazio)".
> **P-E2** — "Ler o campo `license` do frontmatter **como declaração** (nunca
> como permissão) e registrar `license.status: declared` com
> `redistribution_basis` apontando o arquivo/texto — aditiva; preserva o
> princípio 'presença ≠ permissão'".

**P-E1:** descrição vazia em **0 de 53** (era 53 de 53). Aditivo: manifesto tem
prioridade; o frontmatter só preenche o vazio.

**P-E2:** três casos testados —

| Situação | `code` | `status` | `redistributable` |
|---|---|---|---|
| só frontmatter `license: Apache-2.0` | Apache-2.0 | declared | **False** |
| frontmatter Apache **e** arquivo MIT | MIT | declared | **False** |
| nenhum dos dois | `None` | unknown | **False** |

Arquivo vence frontmatter: evidência física > afirmação textual. Divergência
entre os dois é informação preservada, não resolvida por conta própria.

**Ressalva honesta.** A proposta previa "47 recursos que **têm** licença
declarada no texto". No corpus que medi, apenas **2 de 53** têm `license:` no
frontmatter e **4** têm arquivo no payload. O mecanismo está correto e testado;
o número da proposta não se confirma neste corpus. Registro o medido.

### 4.7 C8 — índice e lifecycle

- Índice declara `scope: "active"` e `scopeNote` — ausência no índice não
  significa ausência no disco.
- **Quarentena nunca é publicada.** Publicar converteria "não revisado" em
  "disponível". Teste garante.
- Índice editado à mão para listar quarentena **passa** em `validate_index` (a
  forma é válida — o schema não conhece o estado do disco) e é pego por
  `index_health` via `indexedButMissingOnDisk`. A separação está correta e
  agora tem teste, justamente para ninguém "consertar" movendo a checagem para
  o validador de forma, que não tem como saber.
- 6 chaves emitidas e ausentes do schema documentadas (R-8.2).

**Evidências não são vacuamente verdadeiras.** Toda asserção de existência
verifica o dado esperado: o NOTICE é conferido pelo copyright do autor; a
integridade por comparação de hash entre dois Hubs; o cross-skill pelo código
exato. Um teste que só verificasse `ok == True` teria passado durante todo o
período em que 30% do acervo era recusado.

---

## 5. Contratos de integração

`docs/architecture/CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md` §15 agora
declara o que existe e o que continua decisão. A decisão arquitetural segue
`PROPOSED`; os mecanismos deixaram de ser hipotéticos.

`tests/integration/test_host_contracts.py` — **30 testes, uma classe por host**.
Se um teste quebrar, um host real quebra.

| Host | Precisa | Verificado |
|---|---|---|
| **Lia Go** (referência) | índice consumível, sem promessa falsa | 5 testes |
| **Lia Studio** (dev) | validar antes de importar | 5 testes |
| **Lia-Project** (infra) | distribuir e provar integridade | 4 testes |
| **Lia Forge** (criativo) | descobrir e usar | 4 testes |
| **Model Lab** (catálogo) | roundtrip sem perda | 3 testes |
| **Fronteiras** | não virar runtime | 4 testes |
| **Adversarial** | resistir a ataque | 5 testes |

Superfície estável: 10 métodos de `AgentHub`, todos verificados como existentes.
Três invariantes que valem em todos:

1. **Nada é ativado implicitamente.** Importação vai para quarentena; `promote`
   é chamada separada e explícita.
2. **Nada é autorizado implicitamente.** `redistributable` é `False` a menos que
   um humano mude; licença declarada não autoriza.
3. **Hash prova integridade, nunca autoria.** Não existe campo `signed` que
   possa virar `True`.

**O Hub não virou runtime.** Testes negativos garantem: importar não executa
(um script com `touch` de prova não roda), não grava fora do Hub, não guarda
valor de credencial, e confiança exige humano — a escala
(`unreviewed`/`user-provided`/`reviewed-external`/`first-party`) diferencia
*quem* revisou em vez de ter um "trusted" binário.

---

## 6. Limitações objetivas

Nada aqui está escondido; é o que **não** foi feito ou não foi possível validar.

### 6.1 Limitações de plataforma (não resolvíveis neste ambiente)

| Item | Situação |
|---|---|
| Windows / WebView2 / PyInstaller | **Não executado.** Sem Windows e sem os binários. Roteiro e scripts existem (`docs/operations/WINDOWS-VALIDATION-AND-BUILD-PLAN.md`); a validação em si continua pendente e depende de máquina Windows. |
| PowerShell (`build_windows.ps1`) | **Não executado.** Sintaxe não verificada em runtime. |
| UI em navegador real | **Não executado.** Testes cobrem estrutura e lógica (`test_ui.py`, `test_ui_structure.py`), não interação visual. |

### 6.2 Decisões deliberadamente não tomadas

- **Licença global.** Não escolhi licença, não criei `LICENSE` nem
  `TRADEMARK.md`. É decisão jurídica do proprietário. Implementei só os
  mecanismos técnicos de atribuição, NOTICE e proveniência.
- **P-E3…P-E8.** Não implementadas — fora do escopo autorizado. Impacto
  concreto: `requirements` do frontmatter não é extraído (P-E7), então o campo
  existe no modelo e devolve `None`. O teste verifica que "nada declarado" lê
  como `None`, nunca como `0` ou `"ok"`.

### 6.3 Limitações conhecidas do produto

- **Sem formato de troca para quarentena.** Só ativas são publicáveis. É
  deliberado (§4.7), mas significa que dois Hubs não espelham o trabalho não
  revisado um do outro.
- **Aninhamento de frontmatter é de um nível.** `metadata:` com `author`,
  `domain`, `tags` funciona. Mais profundo não é interpretado — chaves são
  achatadas no caminho do pai (nenhum dado é descartado, mas a estrutura se
  perde). PyYAML foi rejeitado como dependência desnecessária: nenhuma Skill do
  corpus real aninha mais de um nível. Verificado e documentado com a saída
  real do parser.

### 6.4 Débito herdado que **não** é regressão

Nenhum defeito conhecido permanece aberto por falta de tempo. O que existe é
limitação de ambiente (§6.1) e escopo não autorizado (§6.2).

---

## 7. Decisões registradas

Decisões `OPEN` e `RECOMMENDED` do registro continuam como estavam — **adotado
não é `APPROVED`**, e nada aqui promove uma decisão pendente. Em particular:

- D-01 (nome "Lia Agent Hub"), D-05 (sem execução de terceiros / sem sandbox),
  D-16, D-18 (risco rule-based transparente) — `OPEN`, preservadas.
- D-03, D-06, D-13, D-14, D-27 — `RECOMMENDED`/`ADOPTED`, não `APPROVED`.

Decisões técnicas tomadas nesta rodada, todas reversíveis e com o porquê no
commit correspondente:

| Decisão | Motivo | Alternativa rejeitada |
|---|---|---|
| Referência em prosa nunca bloqueia | 30% do acervo real era recusado | manter regex e afrouxar caso a caso |
| Arquivo de licença vence frontmatter | evidência física > afirmação | confiar no frontmatter |
| Quarentena publicável em nenhuma hipótese | "não revisado" ≠ "disponível" | incluir com marcação |
| Um nível de aninhamento, sem PyYAML | nenhuma Skill real aninha mais | adicionar dependência |
| `exists()` responde só sobre a biblioteca | é a pergunta "promoveu sozinho?" | sobrecarregar com quarentena |

---

## 8. Commits

Todos nesta branch. Nenhum force push, nenhum merge, `main` intocada.

| Hash | Conteúdo |
|---|---|
| `47f5da7` | cherry-pick da revisão independente (`bd4bfbb`) — docs e sondas |
| `e6bd051` | correção de C4 e C2 conforme a revisão; implementação de P-E1/P-E2 |
| `c013b2e` | 47 testes travando os achados da revisão + 2 bugs novos |
| `72305c5` | correção do relatório do Bloco 1 (duas afirmações falsas) |
| `b33b68b` | contratos executáveis dos 5 hosts + frontmatter aninhado |
| `e359b96` | status de implementação verificado no contrato de hosts |
| `1ac38d7` | segurança: varredura do NOME do arquivo |
| `43de9cd` | `Capability` tolerante a campo desconhecido |
| *(este commit)* | este relatório |

Anteriores relevantes: `891a1d9` (relatório do Bloco 1), `2951910` (76 testes),
`3e0e0b5` (correções do Bloco 1), `704dfd3` (fim da rodada 6).

---

## 9. Como reproduzir a validação completa

```bash
# ambiente
python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# suíte completa (447)
.venv/bin/python -m pytest tests/

# validação do repositório (4/4 etapas, 44/44 checagens)
bash scripts/validate.sh

# corpus real (requer os clones; ver §2.1)
PYTHONPATH=src .venv/bin/python docs/operations/evidence/corpus_probe.py

# sondas da revisão independente
PYTHONPATH=src .venv/bin/python docs/review/evidence/probe-01-e1-e3-e6.py
PYTHONPATH=src .venv/bin/python docs/review/evidence/probe-03-e9-listing.py
PYTHONPATH=src .venv/bin/python docs/review/evidence/probe-04-dot-lia-passthrough.py
PYTHONPATH=src .venv/bin/python docs/review/evidence/probe-05-provenance-roundtrip.py
```

**Sobre `probe-04`:** ela sai com código 1 e imprime `TypeError` no final — e
isso é o resultado **correto** aqui, não uma falha. A sonda foi escrita pela
revisão sobre o baseline `704dfd3`, quando um payload com `.lia/` era aceito;
o objetivo dela era medir se o metadado interno atravessava a importação. Com
a correção, o `.lia/` é **recusado antes** de ser estagiado:

```
import ok= False blocked= Entrada proibida no pacote: `.lia`.
files staged: []
```

Como a importação é bloqueada, `r.capability_id` é `None` e a linha seguinte da
sonda tenta montar um caminho com ele — daí o `TypeError`. As outras três
(01, 03, 05) executam até o fim. A sonda não foi alterada: é artefato da
revisão, e reescrevê-la para "passar" destruiria a evidência de como o defeito
foi demonstrado na época.

---

## 10. Conclusão

O que mudou de forma durável não é a contagem de testes — é o critério. A versão
anterior tinha 361 testes verdes e recusava 30% do acervo real, porque nenhum
teste importava uma Skill que citasse um endpoint. Agora a validação é feita
contra material real, e os testes que provam C4 falham se a regressão voltar.

O Hub entrega metadado, integridade e proveniência; não executa, não autoriza,
não guarda segredo e não decide confiança. Essa fronteira está testada por
ataque, não por afirmação.
