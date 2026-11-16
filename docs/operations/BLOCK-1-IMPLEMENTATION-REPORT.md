# Bloco 1 — Relatório de implementação

**Data:** 2026-11-16 (UTC)
**Branch:** `arena/a92004be-lia-agenthub`
**HEAD inicial desta rodada:** `704dfd3f7138a0c300639d9f9a29bf37bb947578`
**HEAD ao iniciar a edição:** `704dfd3` (após fast-forward, ver §1)
**Natureza:** relatório de execução. Separa o que foi **corrigido e testado**
do que está **bloqueado**.

---

## 0. Resumo

| Correção | Tema | Estado |
|---|---|---|
| C1 | Tolerância de `Source` | ✅ **PASS** |
| C2 | Preservação de `notice_required` | ✅ **PASS** |
| C3 | Bloqueio de `.lia/` no payload | ✅ **PASS** |
| C4 | `check_references` unificado | ✅ **PASS** |
| C5 | `folder_name` nos dois pontos | ✅ **PASS** |
| C6 | Implementação de P-E1 | ⛔ **BLOCKED** |
| C7 | Implementação de P-E2 | ⛔ **BLOCKED** |
| C8 | Schema do índice | ✅ **PASS** |

**6 de 8 completas.** C6 e C7 dependem de `P-E1`/`P-E2`, que só existem no
relatório de revisão — e esse arquivo **não existe em nenhuma branch deste
repositório** (§2). Não inventei o escopo.

**Suíte:** 285 → **361 testes**, todos passando.
**`main`:** `34a27f4`, intacta, local e remoto.

---

## 1. Estado Git

### 1.1 Antes de editar

| Item | Valor observado |
|---|---|
| Branch | `arena/a92004be-lia-agenthub` |
| HEAD local | `7cec491` |
| HEAD remoto | `704dfd3` |
| Upstream | **nenhum** (configurado ou não, `git rev-parse @{u}` falha) |
| Árvore de trabalho | limpa |
| `main` local e remoto | `34a27f4` |

**Divergência encontrada e tratada.** O prompt informava o HEAD de referência
`704dfd3`; meu HEAD local era `7cec491`, três commits atrás. Verifiquei antes
de agir:

- `git merge-base --is-ancestor HEAD origin/…` → **verdadeiro**: o local é
  ancestral do remoto.
- Commits que só o remoto tinha: `42d39b7`, `b4eb85f`, `704dfd3`.
- Commits que só o local tinha: **nenhum**.

Portanto havia fast-forward limpo, sem trabalho meu em risco. Avancei com
`git merge --ff-only`, que não descarta nem reescreve nada. Nenhum trabalho de
outro agente foi sobrescrito.

Os três commits trazidos:

| Hash | Assunto |
|---|---|
| `42d39b7` | fix(windows): preserve exclusive bind and resolve build Python |
| `b4eb85f` | docs(windows): record validation evidence and distribution blockers |
| `704dfd3` | docs: add capability host and distribution proposal |

### 1.2 Depois

| Item | Valor |
|---|---|
| HEAD | `2951910` (mais o commit deste relatório) |
| Commits desta rodada | 2 (correções + testes) + 1 (este relatório) |
| Push | ver §9 |
| `main` | `34a27f4` — **intacta**, local e remoto |
| Merge / PR | nenhum |
| `docs/research/` | **não alterado** (verificado por `git diff`) |
| `docs/review/` | **não alterado** (não existe) |
| `LICENSE` | **ausente** — correto |

---

## 2. BLOCKED — a fonte obrigatória não existe

O prompt determina: *"Leia integralmente `docs/review/ARCHITECTURE-SECURITY-CROSS-REVIEW.md`"*,
e sobre ele dependem C6 e C7 (P-E1, P-E2).

**O arquivo não existe.** Verificado, não presumido:

| Verificação | Resultado |
|---|---|
| `ls docs/review/` | `No such file or directory` |
| `find` por `*CROSS-REVIEW*` / `*ARCHITECTURE-SECURITY*` | nenhum resultado |
| `git ls-tree` em `origin/main` | 0 arquivos em `docs/review/` |
| `git ls-tree` em `origin/arena/a92004be-…` | 0 |
| `git ls-tree` em `origin/arena/db625478-…` (branch de revisão) | 0 |
| `git ls-tree` em `origin/arena/b6febe41-…` | 0 |
| `git grep "P-E1\|P-E2\|P-E3"` em **todas** as refs remotas | 0 |
| `grep -rn "notice_required"` em `docs/**.md` | 0 |
| `docs/review/evidence/` (scripts de sonda) | não existe |

**Não existe em nenhum lugar do repositório.** Portanto:
- Não li os achados E-1…E-12, a análise A-3, nem as propostas P-E1/P-E2.
- Não executei as sondas de `docs/review/evidence/` — elas não estão aqui (§5.4).

### 2.1 Por que C1–C5 e C8 puderam avançar mesmo assim

O prompt descreve C1–C5 e C8 de forma **operacional**: sintoma, arquivo, causa
provável, comportamento esperado. Para essas, a descrição bastou — e em todos
os seis casos eu **reproduzi o defeito antes de corrigir**, com resultado
registrado (§4). Não trabalhei de memória nem de suposição.

C6 e C7 são diferentes: o prompt diz *"Implemente somente o escopo
explicitamente descrito em P-E1/P-E2"*. Sem a proposta, não há escopo. Inventar
seria pior do que bloquear — implementaria algo com nome de P-E1, sem relação
com o que a revisão pediu.

**O que destrava:** trazer `docs/review/ARCHITECTURE-SECURITY-CROSS-REVIEW.md`
(ou ao menos a seção 16 e o texto de P-E1/P-E2) para esta branch. Com isso,
C6 e C7 são implementáveis em uma rodada curta.

### 2.2 Uma correção no prompt, registrada

O prompt afirma que as correções vêm *"da seção 16 do relatório"* e que os
achados são E-1…E-12. Não pude confirmar a numeração: os identificadores
(C1…C8) e as descrições vieram do prompt, que é a única fonte disponível. Se
o relatório real numerar diferente, o mapeamento precisa ser refeito — o
trabalho técnico permanece válido, porque cada correção foi verificada contra
comportamento observado, não contra um número de item.

---

## 3. As correções, uma por uma

### C1 — Tolerância de `Source` → **PASS**

**Sintoma reproduzido.** Biblioteca com 3 registros, um deles com campo extra
em `source`:

```
list_all() -> 0 itens: []
```

Os três registros ficaram inacessíveis. Causa: `Source(**d)` levanta `TypeError`
em chave desconhecida, e `list_all()` capturava apenas `KeyError`/`ValueError`.

```
Source(**d) -> TypeError: Source.__init__() got an unexpected keyword argument 'campoFuturo'
```

**Correção.**
- `Source.from_dict()` separa chaves conhecidas de desconhecidas. As
  desconhecidas vão para `extra` e voltam à gravação no nível de cima — o
  arquivo em disco não muda de forma.
- `Repository._ler_entradas()` substitui o `try/except (KeyError, ValueError)`
  por `except Exception` **com registro obrigatório** em `erros_de_leitura`
  (id da pasta + motivo). Não é `pass`.
- Registro sem `capability.json` legível também é registrado.

**Decisão que vale explicitar.** Preservar `extra` em vez de descartar é
deliberado: descartar perderia procedência (um futuro campo de assinatura ou
origem de build) na primeira vez que o Hub tocasse no registro. Mas `extra`
**não** participa de nenhuma decisão — há teste específico para isso
(`test_extra_nao_influencia_confianca_nem_ciclo`).

**Arquivos:** `domain/model.py`, `adapters/repository.py`.
**Testes:** 7.

---

### C2 — `notice_required` → **PASS**

**Sintoma reproduzido.** Recurso com `LICENSE` contendo texto MIT:

```
notice_required no registro: False
NOTICE presente no pacote:   False
```

Um recurso MIT era exportado sem o aviso que o texto MIT exige que acompanhe a
redistribuição. Não era decisão: era omissão — o importador construía
`License(...)` sem o campo.

**Correção.**
- `notice_required` é **derivado** da licença identificada, por tabela
  explícita em `domain/model.py` (`_NOTICE_POR_LICENCA`).
- Conteúdo importado **não** decide obrigação legal sobre si mesmo: o valor vem
  da licença identificada, nunca de um campo do payload.
- Registro antigo sem o campo → deriva da tabela. Registro com valor explícito
  → respeitado (`False` de Unlicense continua `False`).
- O `NOTICE` agora carrega o **texto** da licença encontrada na raiz do
  payload. Antes só apontava o nome, o que não cumpre MIT/BSD/Apache.
- Sem texto legível, o `NOTICE` **diz isso** em vez de fingir que está completo.

**O que não mudou.** `redistributable` continua `False` por padrão. Exportação
pública continua exigindo base registrada — há teste garantindo que C2 não
relaxou a política por destino. MIT continua **não** sendo permissão de nada.

**Arquivos:** `domain/model.py`, `adapters/importer.py`, `adapters/packager.py`.
**Testes:** 12.

**Risco residual, declarado.** A tabela cobre as licenças que o detector
reconhece mais as variantes comuns de GPL/LGPL/AGPL/MPL/CC0. Uma licença cuja
família exija aviso e que não esteja na tabela ficaria `False`. Mitigação: o
detector é conservador (devolve `None`/rótulo genérico para texto não
reconhecido, e `CC (ver arquivo)` está como exigindo). Ampliar a tabela é
mudança de dados, não de código.

---

### C3 — Bloqueio de `.lia/` → **PASS**

**Sintoma reproduzido.** Payload com `.lia/capability.json` declarando
`trust: first-party`:

```
import ok?  True
payload: .lia/capability.json
pacote exportado contém: ['payload/.lia/capability.json']
```

O `trust` real continuou `unreviewed` (o Hub não lê trust do payload — bom),
mas o metadado interno forjado **viajou para dentro do pacote**.

**Correção, em dois pontos.**
1. **Entrada:** `.lia` em `DENY_NAMES` (`domain/paths.py`). O canonicalizador
   existente já colapsa `.LIA`, `.Lia` e `.lia.`, então uma entrada cobre as
   variantes. Vale em qualquer profundidade, para diretório, ZIP e
   `.lia-capability`.
2. **Saída:** o packager remove `.lia/` de registros importados antes da
   correção **e avisa**. Sem isso, um registro legado contaminado propagaria
   metadado forjado para quem recebesse o pacote. Se o payload só tiver `.lia`,
   a exportação é recusada.

**Por que a defesa na saída importa.** A correção na entrada não limpa o
passado. Testei o cenário legado e ele ainda vazava — só fechou com a segunda
metade.

**Arquivos:** `domain/paths.py`, `adapters/packager.py`.
**Testes:** 12 (7 variações de caminho + ZIP + pacote + legado + controle).

---

### C4 — `check_references` → **PASS**

**Sintomas reproduzidos.**

```
referenced_files("[x](../fora.md)")        -> []      # fuga invisível
escaping_references(...)  (antes: inexistente)
```

Uma tentativa de sair do recurso parecia "sem referências". E não havia
distinção entre citar arquivo ausente, citar outra Skill e tentar escapar.

**Correção.**
- Um único `check_references`, com `folder_name` opcional, que classifica em
  três códigos:
  - `REFERENCE_MISSING` (aviso) — o arquivo não está no recurso;
  - `REFERENCE_CROSS_SKILL` (aviso) — aponta para outra Skill. Detectado por a
    pasta conter `SKILL.md` próprio, **não** por ter subpasta: `docs/guia.md` é
    conteúdo desta Skill, não outra Skill;
  - `REFERENCE_INVALID` (erro) — `..`, absoluto, UNC ou drive.
- `escaping_references()` existe para a fuga ser **reportada**. O filtro antigo
  descartava em silêncio, o que é a pior forma de tratar tentativa de escape.
- Regex ampliado para pegar caminhos com drive em crase, que antes não casavam
  (`C:/x.md` não termina em extensão de conteúdo, mas é fuga).

**Referência quebrada continua aviso, nunca bloqueio** — há teste garantindo
que uma Skill legítima com referência ausente ainda importa. O produto promete
não inventar reparos.

**Sobre a divergência "2 avisos vs 29 Skills"** relatada na revisão: não pude
reproduzi-la, porque a comparação era contra o gerador de catálogo dos 48
`SKILL.md` reais, que **não está neste repositório** (§4.2). O que corrigi é a
causa estrutural: agora existe **uma** função de verificação, e quem gerar
catálogo deve chamá-la em vez de reimplementar.

**Arquivos:** `domain/skills.py`.
**Testes:** 16.

---

### C5 — `folder_name` nos dois pontos → **PASS**

**Sintoma reproduzido.** O que `folder_name` virava, por layout:

| Layout do recurso | `folder_name` antes |
|---|---|
| flat (`SKILL.md` + `apoio.md`) | `None` |
| com subpasta (`scripts/run.py`) | `"scripts"` |
| aninhado (`docs/guia.md`) | `"docs"` |

Nunca era a pasta do recurso. Nos dois pontos (`importer.from_extraction` e
`AgentHub.validate`), o valor vinha do primeiro segmento de qualquer caminho
**interno**. Resultado: a checagem `NAME_FOLDER_MISMATCH` comparava o nome com
uma subpasta de conteúdo, ou não rodava.

**Correção.** `folder_name_do_recurso(upstream, files)` deriva do **caminho de
origem** — o diretório que o usuário apontou. Semântica documentada na própria
função:
- diretório apontado → último segmento;
- `.zip` / `.lia-capability` → `None` (arquivo compactado não tem pasta);
- arquivo solto → `None`;
- `None` → `None`.

Semântica registrada no docstring, que é o contrato do módulo (o repositório
não tem arquivo de contrato separado para `skills.py`).

Os **dois** pontos foram verificados por espião em teste, não por leitura:
`test_importador_usa_a_pasta_de_origem` e `test_validacao_usa_a_pasta_de_origem`.

**Arquivos:** `domain/skills.py`, `adapters/importer.py`, `app.py`.
**Testes:** 9.

---

### C6 — P-E1 → **BLOCKED**

`P-E1` não existe em nenhuma ref deste repositório (§2). Implementar exigiria
inventar o escopo. **Não implementado por decisão, não por falta de tempo.**
Nenhum arquivo tocado em nome de C6.

**Para destravar:** trazer o texto de P-E1. Estimativa: pequeno, se P-E1 for
uma proposta pontual como as outras do bloco.

---

### C7 — P-E2 → **BLOCKED**

Mesma situação de C6. **Nenhum arquivo tocado em nome de C7.**

---

### C8 — Schema do índice → **PASS**

**Sintoma reproduzido.** Com uma capacidade `superseded` no disco:

```
entradas no índice:        0     ← correto: índice publica só `active`
check_consistency ok:      True
notIndexed:                ['skill-valida-…']   ← falso alarme
schema tem lifecycle:      False
```

Dois problemas: o índice não declarava **por que** um recurso está fora, e
`check_consistency` tratava "no disco e fora do índice" como erro — então
`superseded`/`archived`, que estão fora **por desenho**, viravam inconsistência.

**Correção.**
- Índice declara `scope: "active"` e `scopeNote` explicando que ausência no
  índice não significa ausência no disco.
- Cada entrada traz `lifecycle`.
- `check_consistency` lê o estado de cada registro do disco e separa:
  - `notIndexed` → **só ativos** fora do índice (erro real);
  - `notIndexedByState` → fora por estado (normal), listado à parte.
- `validate_index` recusa entrada com `lifecycle: "quarantined"` no índice:
  índice é lista de consumo, quarentena não pode estar nele.

**Quarentena continua fora — e isso é de segurança, não de schema.** Publicar
quarentena num arquivo feito para compartilhar converteria "não revisado" em
"disponível". Há teste para isso.

**Compatibilidade.** `scope` e `lifecycle` são **aditivos**: `validate_index`
aceita índice antigo sem eles (há teste). Exigir presença invalidaria todo
índice já publicado por uma mudança que não perde informação.

**Arquivos:** `adapters/index_builder.py`.
**Testes:** 11.

---

## 4. Verificação

### 4.1 Comandos executados

```bash
# estado
git branch --show-current; git rev-parse HEAD; git status --short
git merge-base --is-ancestor HEAD origin/arena/a92004be-lia-agenthub
git merge --ff-only origin/arena/a92004be-lia-agenthub

# suíte
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m pytest tests/integration/test_block1_fixes.py -q

# validadores
bash scripts/validate.sh
.venv/bin/python docs/research/verify-consistency.py

# sondas antes/depois
PYTHONPATH=src .venv/bin/python /tmp/probe_before.py
```

### 4.2 Resultados exatos

| Comando | Resultado |
|---|---|
| `pytest tests/` (antes das correções) | **285 passed** |
| `pytest tests/` (depois) | **361 passed** em 14,55 s |
| `pytest tests/integration/test_block1_fixes.py` | **76 passed** |
| `scripts/validate.sh` | 4/4, **nenhum segredo encontrado**, OK |
| `verify-consistency.py` | **44/44 PASS**, incluindo "LICENSE ausente" |
| `main` local / remoto | `34a27f4` / `34a27f4` |

### 4.3 Sondas antes/depois

`docs/operations/evidence/block1-probe-before.json` e `…-after.json` estão
versionados. Comparação:

| Sonda | Antes | Depois |
|---|---|---|
| `C1_list_all` | **FALHA** `TypeError` | ok, 3 de 3 acessíveis |
| `C2_notice_no_registro` | `False` | `True` |
| `C2_NOTICE_no_pacote` | `False` | `True` |
| `C3_lia_no_payload` | `['.lia/capability.json']` | recusado |
| `C3_lia_no_pacote` | `['payload/.lia/capability.json']` | `None` |
| `C5_folder_name_flat` | `None` | pasta real |
| `C5_folder_name_subpasta` | `'scripts'` | pasta real |
| `C8_notIndexed` | `['skill-valida-…']` | `[]` |
| `C8_schema_tem_lifecycle` | `False` | `True` |

Oito de onze valores mudaram de "defeito" para "correto". Os três restantes
(`C8_entradas_no_indice`, `C8_consistencia_ok`) estavam certos antes e
continuam — como deveriam.

### 4.4 Compatibilidade com registros antigos

Teste dedicado, com quatro formatos legados:

| Registro | Legível | Observação |
|---|---|---|
| mínimo (sem `license`, sem `source`) | sim | trust/ciclo preservados |
| sem `license` | sim | `license=None` |
| sem `source` + `license: MIT` **sem** `notice_required` | sim | deriva `notice=True` |
| só `id/name/version/type` | sim | `lifecycle=quarantined` por padrão |

**4 de 4 legíveis, zero em `erros_de_leitura`.** Índice gerado e validado.
Nenhum registro antigo válido se tornou ilegível.

### 4.5 Sondas da revisão

**Não executadas.** `docs/review/evidence/` não existe (§2). Registrado como
limitação, não como sucesso.

---

## 5. Limitações e riscos remanescentes

1. **C6/C7 bloqueados** (§2). Nenhum código escrito em nome deles.
2. **A divergência "2 avisos vs 29 Skills"** não foi reproduzida: o gerador de
   catálogo dos 48 `SKILL.md` reais não está neste repositório. Corrigi a causa
   estrutural (uma função só), não o sintoma numérico.
3. **Tabela de NOTICE** cobre o que o detector reconhece. Famílias fora da
   tabela ficam `False`. Ampliar é mudança de dados.
4. **`folder_name`** usa `upstream` registrado na importação. Recurso importado
   antes da correção tem `upstream` correto em todos os casos observados, mas a
   pasta não é revalidada retroativamente — não há migração, por desenho.
5. **Nada foi executado no Windows.** As correções são de lógica de domínio e
   filesystem portátil; o bloqueio `.lia` usa o canonicalizador que já trata
   regras do Windows, mas a validação real continua dependendo do ambiente
   Windows documentado em `WINDOWS-VALIDATION-AND-BUILD-PLAN.md`.
6. **Nenhuma Skill das 48 foi importada**, nenhum payload de terceiro copiado,
   nenhum código importado executado (§7).

---

## 6. Itens bloqueados por decisões humanas

Nenhuma decisão de licenciamento foi tomada ou alterada:

- `LICENSE`: não criado.
- Licença do ecossistema Lia: não escolhida.
- Titularidade/marca: não definida.
- D-A…D-O: não tocadas.
- `docs/DECISION-REGISTER.md`: não alterado.
- P-E3, P-E4, P-E8: não implementadas.
- Capability Host: não modificado.

A tabela `_NOTICE_POR_LICENCA` **não** é escolha de licença: é o que cada
licença já identificada exige sobre aviso. Ela não licencia nada sob nada.

---

## 7. Confirmações finais

| Item | Estado |
|---|---|
| Nenhuma Skill das 48 importada | ✅ nenhum payload externo usado |
| Nenhum código importado executado | ✅ testes usam fixtures sintéticas |
| `docs/research/` alterado | ✅ **não** (`git diff` vazio) |
| `docs/review/` alterado | ✅ **não** (não existe) |
| `main` alterada | ✅ **não** — `34a27f4` local e remoto |
| Merge / PR criado | ✅ **não** |
| `LICENSE` criado | ✅ **não** |
| Segredo/token no diff | ✅ nenhum (`validate.sh` 4/4) |
| Force push | ✅ não usado |

**Este relatório não declara o Hub pronto para distribuição nem para a
importação das 48 Skills.** O que existe é: seis defeitos independentes de
decisão humana, corrigidos com regressão e compatibilidade verificadas;
dois bloqueados por fonte ausente.
