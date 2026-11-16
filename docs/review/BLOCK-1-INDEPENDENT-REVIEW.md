# Bloco 1 — Revisão Técnica Independente

**Revisor:** sessão Architecture/Security (revisão independente, sem alteração de código)
**Data:** 2026-11-15
**Baseline:** `704dfd3f7138a0c300639d9f9a29bf37bb947578`
**Alvo revisado:** `891a1d93fcd646856353483f1769205a6a3b82aa` (`origin/arena/a92004be-lia-agenthub`)
**Escopo solicitado:** C1, C2, C3, C4, C5, C8 (C6 e C7 reportados BLOCKED)
**Natureza:** revisão adversarial com reprodução. Nenhum teste do repositório foi alterado.

---

## 1. Sumário executivo

**Recomendação: Bloco 1 NÃO está validado para avançar. Rejeitar o merge no estado `891a1d9`.**

O trabalho é de boa qualidade estrutural. Os números do relatório do Principal são **verdadeiros e integralmente reproduzíveis**: 285 → 361 testes, +76 novos, 4/4 validações, 44/44 checagens de consistência. C1, C3, C5 e C8 são correções reais, verificadas por mim contra casos adversariais e contra dados reais; C3 em particular resistiu a nove tentativas de contorno.

O problema não está nos testes que passam — está no que o diff **introduziu de novo e nenhum teste cobre**:

1. **Bloqueio funcional de um terço do acervo real (C4, severidade ALTA).** A unificação do verificador de referências trouxe duas regexes novas que classificam como `ERROR` impeditivo aquilo que é prosa legítima: caminhos absolutos citados como **endpoint HTTP** (`` `/json/list` ``, `` `/api/v1/x` ``) e **rotas de servidor** (`` `/` ``). Resultado medido: **16 das 48 Skills reais (33%) são recusadas na importação** — todas importavam com sucesso no baseline. O `blocked_reason` apresentado ao usuário é *"O arquivo SKILL.md é estruturalmente inválido"*, o que é falso: o frontmatter está válido.
2. **A detecção cross-skill de C4 nunca dispara (severidade MÉDIA).** O código existe, o texto do relatório o descreve como entregue, e não há um único teste para ele. `pastas_de_skill` é derivada só de `available`, e `importer.py:249`/`app.py:161` **não passam `folder_name`** para `check_references`. O caso que a função pretende detectar é inalcançável na prática.
3. **C2 cobre o arquivo de licença na raiz e ignora o resto (severidade MÉDIA).** O `NOTICE` do pacote é gerado a partir de `_texto_da_licenca`, que só olha a raiz do payload. Para o acervo real — onde a licença mora por Skill, em `LICENSE.txt` dentro de subpastas — o pacote sai declarando "NÃO DECLARADA". Isto não é hipótese: no `anthropics/skills` verifiquei que a licença existe apenas por Skill.
4. **O relatório do Principal afirma um fato falso (severidade MÉDIA, governança).** A §2 sustenta que P-E1/P-E2 não existem "em nenhum lugar do repositório" após varrer todas as refs remotas. Elas existem, e eu as recuperei literalmente. C6/C7 estão **BLOCKED por diagnóstico errado**, não por ausência de escopo.

Nenhum destes é um vazamento, uma escrita fora de diretório ou uma execução indevida: a fronteira de segurança do Hub (biblioteca/oficina, sem execução de Skill/MCP/CLI) **permanece intacta**. São defeitos de correção funcional e de fidelidade de relatório.

| Item | Classificação | Frase de uma linha |
|---|---|---|
| C1 — tolerância de `Source` | **PASS** | Round-trip preserva campos desconhecidos e isola registro defeituoso; `License` ficou fora (nota). |
| C2 — notice/obrigações | **PARTIAL** | Tabela e derivação corretas; `NOTICE` só acha licença na raiz e perde o caso per-Skill. |
| C3 — bloqueio de `.lia` | **PASS** | Resiste a 9 variantes de contorno; defesa em profundidade na exportação funciona. |
| C4 — referências cross-skill | **FAIL** | 33% do acervo real bloqueado por falso positivo + cross-skill inalcançável. |
| C5 — `folder_name` | **PASS** | 11/11 casos corretos; sem falso positivo no acervo real. |
| C8 — índice/lifecycle | **PASS** | Escopo `active` correto, quarentena rejeitada, consistência separada. |
| C6 — P-E1 (`description`) | **BLOCKED (diagnóstico errado)** | Escopo recuperável e recuperado; 48/48 descrições seguem vazias. |
| C7 — P-E2 (`license` declarada) | **BLOCKED (diagnóstico errado)** | Escopo recuperável e recuperado; 47/48 licenças seguem `unknown`. |

---

## 2. Commits e arquivos examinados

### 2.1 Alcance do diff

```
git diff --stat 704dfd3 891a1d9   →  12 arquivos, +1597 / −61
```

| Arquivo | Δ | Papel na revisão |
|---|---|---|
| `src/lia_agenthub/domain/model.py` | +113 | C1 (`Source.from_dict`), C2 (`_NOTICE_POR_LICENCA`, `notice_obrigatorio`) |
| `src/lia_agenthub/domain/skills.py` | +168 | C4 (verificador unificado), C5 (`folder_name_do_recurso`) |
| `src/lia_agenthub/domain/paths.py` | +7 | C3 (`.lia` em `DENY_NAMES`) |
| `src/lia_agenthub/adapters/importer.py` | +17 | C1/C4/C5 pontos de chamada |
| `src/lia_agenthub/adapters/packager.py` | +81 | C2 (`NOTICE`), C3 (strip de exportação) |
| `src/lia_agenthub/adapters/index_builder.py` | +75 | C8 (escopo, `lifecycle`, consistência) |
| `src/lia_agenthub/adapters/repository.py` | +59 | C1 (tolerância de leitura) |
| `src/lia_agenthub/app.py` | +9 | C4/C5 ponto de chamada da validação |
| `tests/integration/test_block1_fixes.py` | +596 | 76 testes novos |
| `docs/operations/BLOCK-1-IMPLEMENTATION-REPORT.md` | novo | Relatório do Principal |
| `docs/operations/evidence/block1-probe-{before,after}.json` | novos | Evidência declarada |

### 2.2 Método

Trabalhei sobre uma extração limpa (`git archive 891a1d9`) e a baseline igualmente limpa (`git archive 704dfd3`), em ambientes separados, para poder rodar **o mesmo experimento nos dois lados**. Todos os números abaixo vêm de execução, não de leitura do relatório. Para C4 contra dados reais, baixei os 48 `SKILL.md` originais via API do GitHub nos commits exatos registrados em `capability.source.upstream`, e rodei o verificador do baseline e do alvo sobre o mesmo conjunto de arquivos.

### 2.3 Refutação de um fato do relatório do Principal

A §2 de `BLOCK-1-IMPLEMENTATION-REPORT.md` afirma que P-E1/P-E2 não existem "em nenhum lugar do repositório", após varredura de todas as refs remotas. **Isso é falso.** As duas propostas estão em `docs/research/SKILL-CATALOG-IMPORT-REPORT.md` §4.3, linhas 147–148, no branch `arena/db625478`:

> **P-E1** — `description`: usar o frontmatter como *fallback* quando não há manifesto; aditivo (só preenche o que hoje está vazio); impacto de não fazer: catálogo com 48 descrições vazias.
>
> **P-E2** — ler o campo `license` do frontmatter **como declaração** (nunca como permissão) e registrar `license.status: declared` com `redistribution_basis` apontando para o arquivo/texto; aditivo; preserva "presença ≠ permissão"; impacto de não fazer: 47 recursos "sem licença" que **têm** licença declarada no texto.

A varredura do Principal **encontrou** o arquivo — ele contém `P-E1` e foi retornado pelo `git grep`. A conclusão não seguiu a evidência. Isto importa porque converteu dois itens recuperáveis em "bloqueados por ausência", o que é uma classe de erro diferente e mais grave do que um item pendente: é uma afirmação factual incorreta em documento de governança.

---

## 3. Matriz C1–C8

### C1 — Tolerância de `Source` a campos desconhecidos — **PASS**

**Implementação:** `Source.from_dict` separa campos conhecidos (`_CAMPO_CONHECIDOS`) de desconhecidos, guardando os últimos em `extra`; `as_dict` re-achata com `{**extras, **d}`. `Repository._ler_entradas` captura `Exception` (`# noqa: BLE001`) e registra em `self.erros_de_leitura` em vez de derrubar a listagem inteira.

**Evidência reproduzida:**

| Cenário | Resultado |
|---|---|
| `derivedFrom` (campo futuro) round-trip | **preservado** (`PRESERVADO: True`) |
| `source` não-dict (`"texto"`) | vira `extra={"_valorOriginal": "texto"}`, sem exceção |
| `source=[]` | não-dict tratado sem exceção |
| biblioteca com 1 registro futuro + 1 corrompido | `list_all()` devolve **3 de 3**; `erros_de_leitura` registra, listagem não cai |
| baseline, mesmo caso | `Source.from_dict` **não existe** (`AttributeError`) — C1 é correção real, não cosmética |

**Ressalvas (não rebaixam C1, mas devem constar):**

- **R-1.1 (BAIXA) — `extra` é nome de campo, não namespace reservado.** `Source.from_dict({"extra": {...}})` guarda o dict em `extra`, e `as_dict` o re-achata. Um campo futuro chamado literalmente `extra` colidiria. Sem impacto hoje; documentar como chave reservada.
- **R-1.2 (MÉDIA) — `License` não recebeu a mesma tolerância.** `License.from_dict` (`model.py:105-121`) lê campo a campo e **descarta silenciosamente** qualquer chave desconhecida. Verificado: `{"code": "MIT", "trademark": "third-party"}` → `trademark` **desaparece** do round-trip. C1 resolveu o sintoma que quebrava a listagem (o `TypeError` do `Source(**d)`) e deixou o mesmo padrão de perda de dados em `License`. Isto é exatamente a classe de perda de procedência que o docstring de `Source` diz querer evitar.
  - *Local:* `src/lia_agenthub/domain/model.py`, `License.from_dict`.
  - *Reprodução:* `License.from_dict({"code":"MIT","trademark":"x"}).as_dict()` → sem `trademark`.
  - *Impacto:* metadado de licença por camada some na primeira gravação. Com P-E2 (C7) entrando, `redistribution_basis` e campos correlatos tendem a crescer — a perda passa a doer mais.
  - *Correção:* replicar o padrão `extra` de `Source` em `License`.
  - *Teste que provaria:* `License.from_dict({"code":"MIT","campoFuturo":1}).as_dict()["campoFuturo"] == 1`.
- **R-1.3 (BAIXA) — `erros_de_leitura` nunca é limpo.** Lista de instância, só cresce. Duas chamadas a `list_all()` com um JSON inválido produzem **2** entradas para o mesmo arquivo (verificado). Não é corrupção, é diagnóstico acumulado: um consumidor que exiba "N erros" superestima. *Correção:* resetar no início de `list_all`/`list_quarantine`.

### C2 — `notice_required` e obrigações de aviso — **PARTIAL**

**Implementação:** tabela `_NOTICE_POR_LICENCA`; `notice_obrigatorio(codigo)`; `License.from_dict` deriva quando a chave está ausente e respeita valor explícito; importer grava `notice_required`; packager emite `NOTICE`.

**Evidência reproduzida:** tabela correta em 16/16 códigos testados — MIT/Apache-2.0/BSD-3-Clause/ISC/MPL-2.0/GPL-3.0/AGPL-3.0 → `True`; Unlicense/CC0-1.0 → `False`; desconhecido/`None` → `False` (e o docstring diz explicitamente que `False` **não** significa livre — elogio: a heurística não foi vendida como garantia legal).

Ressalvas:

- **R-2.1 (MÉDIA) — `NOTICE` só procura licença na raiz do payload.** `_texto_da_licenca` (`packager.py:75-89`) filtra `if "/" in rel: continue`. Para o acervo real isso falha: importei uma Skill com `license: Apache-2.0` e `LICENSE.txt` em subpasta de Skill, o pacote saiu com `THIRD_PARTY_NOTICES.md` dizendo **"Licença declarada: NÃO DECLARADA"**, sem `NOTICE`. Isto é o cenário dominante em `anthropics/skills` (licença por Skill, não na raiz). O comentário do código justifica a restrição dizendo que um `LICENSE` em `vendor/` "é de outra pessoa" — raciocínio correto em geral, mas o filtro não distingue `vendor/` de `skills/<nome>/`, e o resultado é omitir o aviso que a própria C2 existe para emitir.
  - *Local:* `packager.py:75-89`, `_texto_da_licenca`.
  - *Reprodução:* Skill com `LICENSE.txt` em `skills/alpha/` e nenhum na raiz → pacote sem `NOTICE`, `THIRD_PARTY_NOTICES.md` com "NÃO DECLARADA".
  - *Impacto:* pacote redistribuído sem o texto que a licença exige que o acompanhe. É falha de conformidade do artefato, na direção conservadora (o Hub *deveria* embutir e não embute).
  - *Correção:* aceitar arquivos de licença em subpastas quando a Skill declarante for a raiz do recurso; ou emitir `NOTICE` listando todos os arquivos de licença encontrados com seu caminho.
  - *Teste que provaria:* importar Skill com `license: Apache-2.0` e `LICENSE.txt` só em subpasta; assertar `NOTICE` presente **e** contendo o texto.
- **R-2.2 (BAIXA) — helper morto.** `exige_notice_conhecido` (`model.py:324`) não tem nenhum chamador (`grep` em `src/`: só a definição). O docstring diz que serve para "não confundir não exige com não sei" — intenção boa, implementação não ligada. Código morto que sugere cobertura inexistente.
- **R-2.3 (BAIXA) — `notice_required` não é recalculado para licença detectada só por arquivo.** Quando não há `LICENSE` na raiz, `detected_license` é `None` e o registro fica `unknown`, mesmo com `license: Apache-2.0` no frontmatter (verificado: `('None', 'unknown')`). É o mesmo buraco que C7/P-E2 existe para fechar — coerente com C2 estar *parcialmente* dependente de C7.

### C3 — Bloqueio de `.lia` nos dois sentidos — **PASS**

**Implementação:** `".lia"` em `DENY_NAMES` (`domain/paths.py`); na exportação, `_e_metadado_interno(rel)` canonicaliza cada segmento (`rstrip(" .").lower()`, trata `\`) e remove arquivos `.lia/` com aviso; se só sobrar metadado interno, recusa o pacote inteiro.

**Evidência reproduzida — 9 tentativas de contorno, todas bloqueadas:**

| Entrada | Resultado |
|---|---|
| `.lia/capability.json` | recusado |
| `.LIA/…` (maiúsculo) | recusado |
| `.lia./…` (ponto à direita) | recusado |
| `.lia /…` (espaço) | recusado |
| `sub/.lia/…` (aninhado) | recusado |
| `sub/deep/.lia/…` (aninhado profundo) | recusado |
| `.lia` (nome puro) | recusado |
| diretório com `.lia/` | recusado |
| `.liax/`, `mylia/` (controle negativo) | **aceitos** (correto — não é bloqueio por substring ingênuo) |

**Defesa em profundidade na exportação (registro legado, importado antes da correção):** gravei um registro com `.lia/capability.json` forjado dentro do payload e exportei. Resultado: `export ok=True`, aviso explícito de que 1 arquivo `.lia/` foi **EXCLUÍDO**, e o pacote final **não contém `.lia`** (`['payload/SKILL.md', 'manifest.json', 'provenance.json', 'THIRD_PARTY_NOTICES.md']`). A correção protege o acervo já existente, não só importações futuras. Isto é o comportamento certo e é o que o relatório promete.

**Ressalva menor:** R-3.1 (BAIXA) — a exportação **avisa mas não falha** ao descartar `.lia/`. Para um payload que *precisa* daquele arquivo, o pacote sai incompleto com `ok=True`. Conservador seria `ok=False` exigindo confirmação. Não rebaixo porque o aviso é inequívoco e o resultado é o seguro.

### C4 — Referências entre Skills — **FAIL**

Este é o item mais consequente. Três defeitos independentes, todos introduzidos por este diff.

**O que a implementação pretendia:** um único `check_references` para catálogo, validação e importação, distinguindo `REFERENCE_MISSING` (aviso), `REFERENCE_CROSS_SKILL` (aviso) e `REFERENCE_INVALID` (erro). A intenção é correta e resolve uma divergência real que a revisão anterior já apontava.

#### R-4.1 (ALTA) — Falso positivo bloqueante: caminho absoluto em prosa vira `ERROR`

`_CODE_PathAmplo_RE = re.compile(r"`((?:[A-Za-z]:)?[^`\s:]*[\\/][^`\s]*)`")` (`skills.py:206`) captura **qualquer** trecho em crase que contenha `/`. `_ESCAPE_RE` (`skills.py:199`) trata como fuga tudo que comece com `/`. Juntas, classificam como `REFERENCE_INVALID` (severidade `ERROR`) caminhos absolutos citados como **endpoint HTTP ou rota de servidor**, que são conteúdo legítimo e comum em Skills de operação.

Verificado sobre os 48 recursos reais:

| Skill real | Trecho citado no `SKILL.md` | Classificação |
|---|---|---|
| `lia-browser-automation` | `` `/json/list` `` (endpoint CDP) | `REFERENCE_INVALID` / **error** |
| `lia-electron-cdp-debugging` | `` `/json/version` ``, `` `/json/list` `` | `REFERENCE_INVALID` / **error** |
| `lia-vue-development` | `` `/` `` (rota) | `REFERENCE_INVALID` / **error** |
| `lia-game-project-bootstrap`, `lia-project-resume`, `stage-runtime-debugging` | `` `/` `` | `REFERENCE_INVALID` / **error** |

Texto real, linha 10 de `lia-browser-automation/SKILL.md`:

> "4. Para Electron, enumere `/json/list` no endpoint CDP e escolha o alvo por URL…"

Isso é um endpoint, não um caminho de arquivo. O verificador não distingue.

**Impacto medido (o número que decide o item):**

```
BASELINE 704dfd3:  skills com aviso = 29/48   | refs = 92  | erros bloqueantes = 0
ALVO     891a1d9:  skills com issue = 42/48   | refs = 153 | erros bloqueantes = 38
                   SKILLS BLOQUEADAS NA IMPORTAÇÃO = 16/48  (33%)
```

Prova de ponta a ponta — importação real de um recurso do acervo:

```
capability-mapping-9dddebe4
  ok = False
  blocked_reason = 'O arquivo SKILL.md é estruturalmente inválido.'
  issues = REFERENCE_INVALID (error) × '../../../docs/02-LIA-CAPABILITY-MATRIX.md'
```

O mesmo recurso no baseline: `ok = True`, zero erros. **16 recursos que importavam passaram a não importar.** O `blocked_reason` ainda mente ao usuário sobre a causa (o frontmatter está válido) e o `hint` ("Corrija os campos apontados como erro") manda corrigir o que não está errado.

Vale notar que `../../../docs/...` é uma referência **deliberada e legítima** dentro de um monorepo: a Skill aponta para a documentação do projeto que a hospeda. A própria docstring do verificador reconhece que fuga pode ser legítima — e ainda assim a promove a `ERROR` impeditivo.

- *Local:* `src/lia_agenthub/domain/skills.py:199` (`_ESCAPE_RE`), `:206` (`_CODE_PathAmplo_RE`), `:262-268` (promoção a `ERROR`).
- *Reprodução:* `check_references("Enumere `/json/list` no endpoint CDP.", {"SKILL.md"})` → `[REFERENCE_INVALID, error]`. Ou importar `lia-browser-automation` do acervo real.
- *Correção:* (a) `REFERENCE_INVALID` deve ser `WARNING` quando o alvo não é distinguível de URL/rota; (b) `_CODE_PathAmplo_RE` não deve capturar caminhos de segmento único (`/json/list`, `/`) — exigir profundidade ou extensão; (c) tratar `..` como aviso de portabilidade, não como erro, quando o alvo não é alcançável a partir do payload mas é plausivelmente um caminho do repositório hospedeiro; (d) `blocked_reason` deve citar o código real.
- *Testes que provariam:* importar os 6 recursos citados e assertar `ok is True`; `check_references("Rode `/json/list`.", {"SKILL.md"})` sem `error`.

#### R-4.2 (MÉDIA) — `REFERENCE_CROSS_SKILL` é inalcançável e não tem teste

`pastas_de_skill` (`skills.py:258`) é derivada **exclusivamente** de `available`, considerando pasta de Skill só o primeiro segmento de entradas terminadas em `/skill.md`. Logo:

- Skill B aninhada dentro do payload de A → único caso que dispara. Confirmei que funciona (`{'SKILL.md','outra/SKILL.md'}` + `` `outra/SKILL.md` `` → `CROSS_SKILL`).
- Skill B **fora** do payload de A → `available` de A não contém B, `pastas_de_skill` fica vazia, e a referência cai em `REFERENCE_MISSING`. **Este é o caso real**: as Skills do acervo citam `.agents/skills/<outra>/SKILL.md`, que nunca estão no próprio payload.

Verificado: `` `.agents/skills/lia-vue-testing/SKILL.md` `` → `REFERENCE_MISSING`, nunca `CROSS_SKILL`.

Agravantes:
- **`folder_name` não é passado.** `importer.py:249` e `app.py:161` chamam `check_references(text, set(files))` sem `folder_name`, embora ambas as funções **calculem** `folder_name` uma linha antes (para `validate_skill`). O parâmetro novo de C4 não é usado em nenhum ponto de produção — só em teste.
- **Zero testes.** `grep CROSS_SKILL` em `tests/`: nenhuma ocorrência. Um dos três códigos que o relatório lista como entregues não tem cobertura alguma.

Consequência: C4 entrega 2 dos 3 comportamentos que descreve, e o terceiro está codificado de forma que não alcança o caso real.

- *Local:* `skills.py:258`, `:274-282`; `importer.py:249`; `app.py:161`.
- *Correção:* derivar pastas de Skill conhecidas de uma fonte externa ao `available` (registro de Skills conhecidas, ou o conjunto completo do catálogo) e passar `folder_name` nos dois chamadores.
- *Teste que provaria:* `check_references("Veja `.agents/skills/outra/SKILL.md`.", {"SKILL.md"}, folder_name="esta")` → `REFERENCE_CROSS_SKILL`.

#### R-4.3 (BAIXA) — O teste novo consagra o comportamento defeituoso

`test_caminho_de_exemplo_citado_e_avisado_como_ausente` (`test_block1_fixes.py:388`) afirma explicitamente que citar `path/to/file.md` **deve** gerar aviso. É defensável como decisão de produto. O problema é que **não há teste equivalente para caminho absoluto e `..`**, que são justamente os que viraram `ERROR`, e `test_importacao_com_fuga_de_fronteira_registra_erro` (`:408`) usa `assert "REFERENCE_INVALID" in codigos or r.ok is False` — um `or` que passa em qualquer um dos dois ramos e portanto **não testa bloqueio**. O conjunto de testes valida a intenção, não o comportamento em dados reais.

### C5 — `folder_name` — **PASS**

**Implementação:** `folder_name_do_recurso(upstream, files)` (`skills.py:299+`) escolhe `PureWindowsPath` se houver `\` ou `:`, senão `PurePosixPath`; devolve `None` para sem upstream, separador final, `.zip`/`.lia-capability` e arquivo solto.

**Evidência reproduzida — 11/11 casos sintéticos corretos** (POSIX, Windows, barra final, `.zip`, `.lia-capability`, arquivo solto, diretório pontuado, `None`), e **4/4 casos reais via `Importer.from_path`:**

| Caso real | Resultado |
|---|---|
| pasta `pasta-errada` com `name: nome-certo` | `NAME_FOLDER_MISMATCH` disparado (verdadeiro positivo) |
| pasta com subpasta `docs/` e nome coerente | **sem** aviso (falso positivo eliminado — este era o bug) |
| pasta simples coerente | limpo |
| ZIP (sem pasta) | sem aviso, `None` (correto: não inventa pasta) |

C5 resolve exatamente o defeito que se propunha: antes, `folder_name` virava `scripts` ou `docs` (o último segmento de qualquer caminho de arquivo) e a coerência comparava nome com coisa errada.

**Ressalvas:** R-5.1 (BAIXA) — o bloco do recurso "flat" devolve a **mesma expressão** da linha final (`skills.py:330-340`): ramo redundante/morto. Sem impacto funcional, mas convida a erro numa futura edição. R-5.2 (BAIXA) — via ZIP `folder_name` é `None` e a checagem de coerência nome↔pasta silenciosamente não roda; é a decisão certa (não inventar), mas convém que o relatório diga que a checagem é inaplicável a ZIP.

### C8 — Índice e `lifecycle` — **PASS**

**Implementação:** `SCHEMA` ganha `scope: const "active"`, `scopeNote` e `lifecycle` por entrada; `build_index` inclui **apenas** `active`; `validate_index` rejeita entrada `quarantined`; `check_consistency` separa `notIndexed` (só ativos) de `notIndexedByState`.

**Evidência reproduzida** (1 ativo + 1 em quarentena):

- índice contém `['ativo-1']` e `scope='active'` — quarentena **não** entra;
- entrada forjada com `lifecycle: quarantined` → `validate_index` a rejeita: *"está em quarentena mas aparece no índice público"*;
- `check_consistency` → `ok=True`, `notIndexed=[]`, `notIndexedByState={}`;
- rejeição de quarentena é defesa de segurança real: publicar recurso não revisado converteria quarentena em vitrine.

**Ressalvas:**
- **R-8.1 (BAIXA) — renomeação de campo é ruptura de contrato não declarada.** `notIndexed` mudou de semântica (antes: tudo não indexado; agora: só ativos) e surgiu `notIndexedByState`. Verifiquei consumidores: `app.py:305` só devolve o campo num caminho sem índice, e a UI (`resources/static/app.js`) usa `index.ok`, `problems.length`, `missingPackages.length`, `exists` — **nenhum consumidor lê `notIndexed`**. Logo não há quebra hoje. Mas a mudança de semântica do mesmo nome deveria estar no relatório e/ou virar `notIndexedActive`.
- **R-8.2 (MÉDIA) — R-14 da revisão anterior segue aberto.** Chaves emitidas por entrada e **ausentes** do `SCHEMA`: `author`, `description`, `domain`, `redistributable`, `tags`; no topo, `signatureNote`. Verificado por diferença de conjuntos contra um índice gerado. O Bloco 1 adicionou três campos ao schema e deixou seis fora. Um consumidor que valide contra o schema publicado rejeita índice legítimo.

---

## 4. Achados de segurança por severidade

Varredura transversal sobre o diff. **Nenhum achado Crítico ou Alto de segurança** — os problemas de severidade ALTA são de correção funcional (§3, R-4.1), não de fronteira.

| Sev. | ID | Achado | Arquivo | Estado |
|---|---|---|---|---|
| **ALTA** | R-4.1 | Falso positivo promove prosa legítima a `ERROR` impeditivo; 16/48 recursos bloqueados. Negação de serviço de importação auto-infligida, com `blocked_reason` enganoso | `domain/skills.py:199,206,262-268` | Confirmado |
| **MÉDIA** | R-4.2 | Detecção cross-skill inalcançável; `folder_name` nunca passado nos pontos de produção | `skills.py:258`; `importer.py:249`; `app.py:161` | Confirmado |
| **MÉDIA** | R-2.1 | `NOTICE` omite texto de licença fora da raiz; caso per-Skill (dominante no acervo real) sai "NÃO DECLARADA" | `packager.py:75-89` | Confirmado |
| **MÉDIA** | R-1.2 | `License` descarta campos desconhecidos (perda de metadado de licença) | `model.py:105-121` | Confirmado |
| **MÉDIA** | R-8.2 | 6 chaves emitidas ausentes do schema publicado (R-14) | `index_builder.py:24-67` | Confirmado |
| **MÉDIA** | — | Relatório do Principal afirma fato falso sobre P-E1/P-E2 | `BLOCK-1-IMPLEMENTATION-REPORT.md §2` | Confirmado |
| **BAIXA** | R-1.1 | `extra` não é chave reservada | `model.py` `Source` | Verificado |
| **BAIXA** | R-1.3 | `erros_de_leitura` acumula entre chamadas | `repository.py:48,86,96` | Confirmado |
| **BAIXA** | R-2.2 | `exige_notice_conhecido` sem chamador | `model.py:324` | Confirmado |
| **BAIXA** | R-3.1 | Exportação descarta `.lia/` com aviso mas `ok=True` | `packager.py` | Confirmado |
| **BAIXA** | R-5.1 | Ramo morto em `folder_name_do_recurso` | `skills.py:330-340` | Verificado |
| **BAIXO** | R-8.1 | `notIndexed` mudou de semântica sem renomear | `index_builder.py:268` | Sem consumidor |

**Controles que resistiram (verificados, não presumidos):**

- **Travessia em pacote:** `../../evil.md` em ZIP → `SecurityError` do `safe_extract`.✅
- **Symlink em ZIP:** entrada com `external_attr` de symlink → `SecurityError: "O pacote contém um link simbólico"`. ✅
- **Escrita fora de diretório permitido:** nenhuma no diff; todos os caminhos derivam de `locations`. ✅
- **Desserialização permissiva:** só `json.loads`, sem `pickle`/`eval`/`yaml.load` inseguro. ✅
- **Confusão metadado-confiável × conteúdo-importado:** `.lia` fechado nas duas direções (C3), `trust` nunca derivado de conteúdo. ✅
- **Execução:** o Hub continua biblioteca/oficina — nenhuma execução de Skill/MCP/CLI introduzida. ✅
- **Sobrescrita silenciosa de registro:** reimportar o mesmo recurso com `upstream` diferente **sobrescreve** o registro em quarentena sem aviso e `already_present=False` sempre. **Porém confirmei que é pré-existente** (baseline idêntico) — não é regressão deste diff; registro como débito herdado, não como achado do Bloco 1.

---

## 5. Testes executados e resultados

Tudo abaixo foi **executado por mim**, em cópias limpas de cada commit.

| # | Comando | Onde | Resultado | Veredito |
|---|---|---|---|---|
| 1 | `python -m pytest` | `704dfd3` | **285 passed** | número do relatório confere |
| 2 | `python -m pytest` | `891a1d9` | **361 passed** em 15,34s | número do relatório confere |
| 3 | `pytest tests/integration/test_block1_fixes.py --collect-only` | `891a1d9` | **76** | "+76 novos" confere |
| 4 | `bash scripts/validate.sh` | `891a1d9` | **44/44 PASS**, 24 arquivos compilados, suíte verde, "nenhum segredo encontrado", "Validação completa: OK" | 4/4 confere |
| 5 | `python docs/research/verify-consistency.py` | `891a1d9` | **44/44 PASS** | confere, e é independente do passo 4 |

**Reafirmo: os cinco números do relatório do Principal são verdadeiros.** A divergência desta revisão não é sobre os testes passarem — é sobre o que eles não cobrem. 361 testes verdes convivem com 33% do acervo real bloqueado.

### 5.1 Evidência própria (não do relatório)

| Experimento | Baseline `704dfd3` | Alvo `891a1d9` |
|---|---|---|
| `check_references` sobre os **48 `SKILL.md` reais** | 29/48 com aviso, 92 refs, **0 erros** | 42/48 com issue, 153 refs, **38 erros**, **16/48 bloqueadas** |
| `Importer.from_path` em 6 recursos reais | 6/6 `ok=True` | **6/6 `ok=False`** |
| C3: 9 variantes de contorno | — | 7 bloqueadas, 2 controles negativos aceitos |
| C3: exportação de registro legado com `.lia` | — | `.lia` removido, aviso explícito, pacote limpo |
| C5: 11 casos sintéticos + 4 reais | — | 15/15 corretos |
| C1: round-trip `Source` / isolamento de registro ruim | `from_dict` inexistente | preservado, 3/3 listados |
| C2: `NOTICE` com licença na raiz | — | texto real embutido (404 chars) |
| C2: `NOTICE` com licença em subpasta | — | **sem `NOTICE`, "NÃO DECLARADA"** |

### 5.2 Crítica à evidência declarada pelo Principal

`docs/operations/evidence/block1-probe-after.json` não demonstra o que as chaves afirmam:

```json
"C5_folder_name_flat": "s",
"C5_folder_name_subpasta": "s",
"C8_entradas_no_indice": 0,
"C8_consistencia_ok": true
```

- `C5_folder_name_* = "s"` não é nome de pasta de nenhum caso plausível — é artefato do caminho do laboratório (segmento final de um caminho tipo `…/skills`). O probe **não** mediu `folder_name`; mediu o último caractere/segmento de outro caminho.
- `C8_entradas_no_indice = 0` com `C8_consistencia_ok = true` é vacuamente verdadeiro: um índice vazio trivially é consistente. Não demonstra que ativos entram nem que quarentena sai — justamente o que C8 mudou.

A medição correta existe: **a minha**. Em 15/15 casos C5 e com 1 ativo + 1 quarentena em C8. Mas o ponto para a governança é que a evidência anexada ao relatório não sustenta as conclusões que acompanha — e foi aceita como se sustentasse.

---

## 6. Regressões

**Confirmadas (todas introduzidas por `704dfd3..891a1d9`):**

1. **Importação de 16 dos 48 recursos reais deixou de funcionar** (R-4.1). Baseline: 6/6 dos amostrados `ok=True`. Alvo: 6/6 `ok=False`. Regressão funcional direta, com mensagem de erro incorreta.
2. **Contagem de "referências ausentes" subiu de 92 para 153** e ganhou 38 erros onde havia zero. Parte do aumento é detecção nova e legítima; a parcela que importa é a que virou `ERROR`.
3. **`NOTICE` deixou de refletir a licença em cenário per-Skill** — não é regressão contra o baseline (o baseline não emitia `NOTICE` algum), é cobertura incompleta da feature nova. Classifico como lacuna de C2, não regressão.

**Não é regressão (verificado):** sobrescrita silenciosa de registro na reimportação — idêntica no baseline. `erros_de_leitura` acumulativo — comportamento novo de C1, mas de diagnóstico, não de dados.

**Regressões de contrato:** `notIndexed` mudou de semântica (R-8.1), sem consumidor quebrado hoje.

---

## 7. Status de P-E1 / P-E2 (C6 / C7)

**Classificação: BLOCKED por diagnóstico incorreto — não por ausência de escopo.**

O escopo **foi recuperado**, literalmente, de `docs/research/SKILL-CATALOG-IMPORT-REPORT.md` §4.3, linhas 147–148, branch `arena/db625478` (texto reproduzido em §2.3). Não inventei escopo: os dois itens estão citados verbatim.

**Refs examinadas:** `origin/HEAD`, `origin/main`, `origin/arena/a92004be-lia-agenthub` (`891a1d9`), `origin/arena/b6febe41-lia-agenthub`, `origin/arena/db625478-lia-agenthub` (`b4e63ea`). `git grep -l P-E1` retorna 2 arquivos em `db625478`.

**Impacto de continuarem não implementados — medido, não estimado:**

| Item | Métrica medida no acervo real |
|---|---|
| P-E1 (`description` do frontmatter) | **48/48** registros com `description` vazia |
| P-E2 (`license` do frontmatter como declaração) | **1/48** tem `license` no frontmatter; **47/48** ficam `unknown`; 19/48 mencionam licença no texto |

Confirmei a causa: o importer grava `description: ''` e `license: None / unknown` mesmo quando o frontmatter traz `description: Uma descricao REAL e util.` e `license: MIT`. O campo é lido em `parse_frontmatter` e **descartado** na gravação.

**Recomendação sobre C6/C7:** reclassificar de `BLOCKED` para `PENDING`, com escopo já definido (P-E1 e P-E2 acima), e corrigir a §2 do relatório de implementação. Nada material falta; falta executar.

---

## 8. Revisão anterior e anexos

**`docs/review/ARCHITECTURE-SECURITY-CROSS-REVIEW.md` — NÃO recuperada do Git.**

Verificação por `git cat-file -e` em todas as refs remotas:

| Ref | Presente? |
|---|---|
| `origin/HEAD` | ausente |
| `origin/main` | ausente |
| `origin/arena/a92004be-lia-agenthub` | ausente |
| `origin/arena/b6febe41-lia-agenthub` | ausente |
| `origin/arena/db625478-lia-agenthub` | ausente |

**Status real:** a revisão existe **apenas** como arquivo não rastreado (`?? docs/review/`) na árvore de trabalho local, com 98.561 bytes, e **nunca foi publicada**. Não houve recuperação — houve constatação de que ela está fora do controle de versão. Não recrio nada a partir de memória.

**Anexos:** os 4 scripts de evidência (`probe-01-e1-e3-e6.py`, `probe-03-e9-listing.py`, `probe-04-dot-lia-passthrough.py`, `probe-05-provenance-roundtrip.py`) estão no mesmo estado — presentes em `docs/review/evidence/`, igualmente não rastreados, nunca publicados.

**Consequência:** as conclusões substantivas da revisão anterior só são citáveis enquanto o arquivo existir nesta árvore. Enquanto não for commitada, qualquer clonagem nova do repositório as perde. Recomendo commitá-la junto com este relatório.

---

## 9. Pendências que bloqueiam o próximo passo

**Bloqueiam (impedem validar Bloco 1):**

1. **R-4.1** — rebaixar `REFERENCE_INVALID` a `WARNING` para alvos não distinguíveis de URL/rota; restringir `_CODE_PathAmplo_RE`; corrigir `blocked_reason`. **Critério objetivo de saída:** os 48 recursos reais importam com `ok=True` (o baseline importa todos), ou as recusas são justificadas por código real e não por prosa citada.
2. **R-4.2** — derivar pastas de Skill conhecidas fora de `available` e passar `folder_name` em `importer.py:249` e `app.py:161`. **Saída:** um teste que dispare `REFERENCE_CROSS_SKILL` no cenário real (`.agents/skills/<outra>/SKILL.md`).
3. **Correção factual** da §2 do relatório de implementação sobre P-E1/P-E2.
4. **Evidência:** substituir `block1-probe-after.json` por um probe que meça de fato `folder_name` e um índice não vazio.

**Não bloqueiam, mas devem constar:**

5. R-2.1 (NOTICE fora da raiz) — é a lacuna que mais aproxima C2 de falha de conformidade do artefato.
6. R-1.2 (`License` sem tolerância a campo desconhecido) — vira mais relevante quando C7 entrar.
7. R-8.2 / R-14 — reconciliar as 6 chaves emitidas fora do schema.
8. R-1.3, R-2.2, R-3.1, R-5.1, R-8.1 — higiene.
9. Publicar `ARCHITECTURE-SECURITY-CROSS-REVIEW.md` + `evidence/` sob controle de versão.

---

## 10. Recomendação objetiva

**Bloco 1 NÃO está validado. Recomendo não avançar até R-4.1 e R-4.2 serem corrigidos e reproduzidos contra os 48 recursos reais.**

Justificativa, em ordem de peso:

1. **C4 é FAIL, não PARTIAL.** A instrução desta revisão era manter C4 em `PARTIAL` até haver reprodução contra os dados originais. Fiz a reprodução, e ela é pior do que "parcial": o diff bloqueia **um terço do acervo real**, com mensagem de erro falsa. Não é ausência de cobertura — é regressão funcional medida. Meu alerta inicial (`PARTIAL`) se converteu em `FAIL` com os dados em mãos.
2. **O critério de "pronto" foi medido no lugar errado.** 361 testes verdes medem o comportamento que o autor imaginou; os 48 recursos reais medem o comportamento que o produto terá. O primeiro está impecável, o segundo regrediu. Foi exatamente o risco que a revisão anterior apontava ao insistir em reprodução contra dados reais.
3. **O que está bom é bom de verdade.** C1, C3, C5 e C8 são correções reais, e C3 é a melhor peça do bloco: resistiu a nove contornos e protege também o acervo legado. Não recomendo descartar o Bloco 1 — recomendo **corrigir C4 e C2 e reenviar**. O trabalho restante é focado e mensurável.
4. **A confiança foi abalada por um fato falso, não por um bug.** Afirmar que P-E1/P-E2 não existem, quando o `git grep` retorna o arquivo, é o achado de governança mais sério desta revisão depois de R-4.1. Um relatório que declara uma varredura negativa que não foi negativa torna os outros números não verificados por padrão — motivo adicional para eu ter reproduzido tudo independentemente.

**Para destravar C6/C7 sem redesenho:** o escopo está recuperado (§2.3/§7), medido e pequeno. Reclassificar de `BLOCKED` para `PENDING` é a ação correta e imediata.

---

### Anexo A — Comandos de reprodução

```bash
# base de comparação limpa
mkdir -p /tmp/rev704 /tmp/rev891
git archive 704dfd3 | tar -x -C /tmp/rev704
git archive 891a1d9 | tar -x -C /tmp/rev891
python -m venv /tmp/venv2 && /tmp/venv2/bin/pip install pytest

# números do relatório
cd /tmp/rev704 && /tmp/venv2/bin/python -m pytest         # 285 passed
cd /tmp/rev891 && /tmp/venv2/bin/python -m pytest         # 361 passed
cd /tmp/rev891 && /tmp/venv2/bin/python -m pytest \
     tests/integration/test_block1_fixes.py --collect-only -q   # 76
cd /tmp/rev891 && ln -sfn /tmp/venv2 .venv && bash scripts/validate.sh   # 44/44, OK
cd /tmp/rev891 && /tmp/venv2/bin/python docs/research/verify-consistency.py  # 44/44

# regressão de C4 contra os 48 recursos reais
# (baixar cada capability.source.upstream via API do GitHub para /tmp/skills/<id>/)
PYTHONPATH=/tmp/rev704/src /tmp/venv2/bin/python /tmp/c4cmp.py    # 29/48, 92 refs, 0 erros
PYTHONPATH=/tmp/rev891/src /tmp/venv2/bin/python /tmp/c4impact.py  # 16/48 bloqueadas
```

Os scripts de sonda usados nesta revisão estão descritos em §5.1; os do ciclo anterior permanecem intactos em `docs/review/evidence/`.

### Anexo B — Nota sobre método

Nenhum arquivo de código foi alterado. Nenhum arquivo em `docs/research/` foi tocado. A revisão anterior e seus anexos foram preservados como estavam. Todos os números neste documento vêm de execução nesta sessão, em cópias limpas dos dois commits, com exceção explicitamente marcada no §8.
