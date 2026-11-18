# Relatório de conclusão funcional — Lia Agent Hub

**Data:** 2026-11-15 (UTC)
**Branch:** `arena/a92004be-lia-agenthub`
**Base do HEAD na abertura:** `90b6e5c`
**Contrato do MVP:** `docs/product/MVP-AND-ROADMAP.md` §3.1
**Pesquisa consultada:** `BloomRX/Lia-Research` @ `arena/7cf9c65e-lia-research` (`61fb956`), sem alteração

---

## 1. Como ler este relatório

Cada requisito recebe uma das quatro classificações:

| Classe | Significado |
|---|---|
| **PASS** | Implementado e **comprovado** por execução neste ambiente |
| **PARTIAL** | Implementado, mas alguma parte do critério não foi exercida aqui |
| **BLOCKED** | Depende de condição externa (máquina Windows, decisão humana, credencial) |
| **NOT APPLICABLE** | Fora do MVP por decisão registrada |

**Regra do kit, respeitada:** suíte verde **não** é homologação de produto. O gate
é execução em Windows real. Nada aqui declara "funciona no Windows".

**Números desta rodada:** **655 testes**, 0 falhas — 124 unit, 437 integration,
94 security (soma exata: 655). Corpus real do ecossistema: **53/53 importam, 0
bloqueadas**. Stitch: 16/16.

---

## 2. Placar M1–M8

| # | Requisito | Classe | Evidência principal |
|---|---|---|---|
| **M1** | Biblioteca local em arquivos | **PASS** | Estrutura lida por `json.loads` puro, sem o Hub |
| **M2** | Importar + inspecionar com relatório honesto | **PASS** | U+202E em código rejeitado; ZWNJ em persa preservado |
| **M3** | Validador estrutural | **PASS** (corrigido) | 15 testes; defeito de campo vazio corrigido |
| **M4** | Contenção de caminho C1–C12 | **PASS** (Linux) / **PARTIAL** (symlink) | 40 testes de traversal, 17 de arquivo |
| **M5** | Proveniência e licença por camada | **PASS** | Privado passa com licença nula; público recusado |
| **M6** | Versionamento, hashes e diff | **PASS** (corrigido) | Diff semântico novo; critério literal coberto |
| **M7** | Pacote `.lia-capability` | **PASS** | Intruso no zip detectado com motivo |
| **M8** | Índice publicável + leitor independente | **PASS** (corrigido) | IDX-3 criado; leitor roda com `-S` e sem o Hub |

---

## 3. O que estava faltando e foi feito

### 3.1 M8 — o leitor de referência nunca existiu

O doc do MVP diz, com todas as letras: *"sem IDX-3, M8 é a afirmação de que um
contrato funciona sem que ninguém jamais o tivesse lido"*. IDX-3 estava previsto
e não havia sido implementado.

Criado `docs/examples/independent-reader/read_index.py`: stdlib puro, não importa
`lia_agenthub`, não escreve nada. Tem `--check` que valida o próprio contrato.

A prova é ativa, não declarativa: `test_independent_reader.py` roda o leitor em
subprocesso com `-S` e `PYTHONPATH` apontando para uma pasta vazia, **e faz a
contraprova** de que `import lia_agenthub` falha naquele ambiente. Isolamento
medido, não prometido.

Dois defeitos foram encontrados ao escrever o próprio leitor:

- `sys.exit("texto")` sai com código **1**, não com 2. O leitor documentava 2 e
  entregava 1 — indistinguível de "índice inconsistente" para um script que
  chama.
- A primeira diferença do corpo era numerada a partir da linha vazia após o
  `---`, então apontava linha 4 para o que o editor mostra na 2.

### 3.2 M6 — o diff não respondia a pergunta que importa

O diff comparava nomes de arquivo. O critério de aceite pede corpo,
`description` e `declaredPermissions`.

O caso que expõe o problema: uma Skill que passa de `allowed-tools: []` para
`allowed-tools: [Bash]`. Nenhum arquivo muda de nome. O contrato declarado muda
inteiro. O diff anterior dizia "SKILL.md mudou" e parava ali.

`diff_frontmatter` e `diff_corpo` (domínio puro) agora reportam campo por campo.
Ausente é `None`, nunca string vazia. Corpo acima de 400 linhas omite o detalhe
em vez de despejar conteúdo num JSON.

### 3.3 M3 — campo presente e vazio passava como válido

`name: ""` era aceito. `name` ausente era rejeitado. O host que lesse o
frontmatter receberia uma Skill sem nome e nenhum aviso.

Novo código `FIELD_EMPTY`, distinto de `MISSING_FIELD`. Só-espaços conta como
vazio. Revalidado contra o corpus real: 53/53 continuam importando — a regra nova
não gera falso positivo em material de terceiro.

### 3.4 Nenhuma das 20 rotas HTTP ficou órfã

Cinco rotas existiam no servidor e **nenhum botão as chamava**: `/api/license`,
`/api/diff`, `/api/export-many`, `/api/history`, `/api/lineage`. A API passava
nos testes; o usuário simplesmente não tinha a funcionalidade, e não sabia.

Todas ganharam caminho: licença com base de redistribuição, comparação com
versão anterior, seleção múltipla na biblioteca, histórico completo.

`test_ui_wiring.py` impede a volta: falha se qualquer rota ficar sem chamador ou
se a UI chamar rota inexistente.

Dead code removido: `duplicates` e `already_present` não tinham chamador;
`detail()` já entrega os dois.

### 3.5 A UI lia um campo que a API não tem

`detail()` devolve `treeHash` e `contentHash` na raiz. O JavaScript lia
`d.hashes.treeHash`. Optional chaining não estoura — então a tela mostrava "…"
em **toda** capacidade, sem erro em log. O usuário concluía que o recurso não
tinha hash.

Corrigido, com hash de árvore e de conteúdo separados e uma linha de integridade
conferida contra o disco. `test_ui_api_contract.py` fixa o contrato.

### 3.6 CLI de desenvolvimento — prevista na Fase 1, nunca implementada

A Fase 1 listava `validate`, `pack`, `export`, `diagnostico`. Só `--diagnostico`
existia.

`src/lia_agenthub/cli.py` implementa os cinco (`index` e `verify-package`
inclusos), com o mesmo `AgentHub` da interface — não há dois comportamentos.
Códigos de saída estáveis: 0 sucesso, 1 recusado, 2 uso/leitura. Testada por
subprocesso, porque o contrato da CLI é o que sai no stdout e o código de saída.

### 3.7 MCP Workshop — exportação de configuração para o host

A Fase 2 promete "bloco JSON para o usuário copiar". Não existia.

`config_para_host` gera o bloco para `mcp-json`, `antigravity` (que usa
`serverUrl`, diferença real entre clientes) e `claude-code`. Cabeçalho entra como
**nome** com placeholder `<SUA_CHAVE>`, nunca valor. Formato desconhecido e
transporte `stdio` são **recusados com explicação** em vez de emitir bloco que
não funcionaria.

---

## 4. Segurança e Windows

### 4.1 D-09 — as conexões do WebView2

O relatório de validação em Windows registrou três destinos externos em
processos filhos `msedgewebview2.exe` (depois, dois na versão final). O
relatório registrou corretamente: *"A finalidade do tráfego ficou
indeterminada"*.

**Investigação desta rodada — o que se sabe e o que não se sabe:**

| Pergunta | Resposta | Base |
|---|---|---|
| O tráfego é do aplicativo? | **Não** | `test_network_boundary` proíbe `connect`, `connect_ex`, `create_connection` e `getaddrinfo` durante import, promoção, export, publicação e diagnóstico — tudo passa |
| É do runtime do navegador? | **Sim, os processos são do runtime** | Propriedade por PID no relatório original |
| Qual componente inicia? | **O Chromium embutido**, não o Hub | O Hub não tem cliente HTTP; a UI é estática e a CSP é `connect-src 'self'` |
| Pode ser controlado? | **Parcialmente** | Ver 4.2 |
| Destino e finalidade? | **Indeterminados** | Não há evidência coletada do conteúdo das conexões |

**Não presumi que fossem inofensivas.** O que os dados sustentam é a separação:
o app não as faz; o runtime do navegador sim. O destino continua sem prova.

### 4.2 Controle implementado e o que ele NÃO garante

`aplicar_controle_de_rede()` define `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` antes
da janela abrir, desligando por nome os recursos do Chromium que geram tráfego:
background networking, component update, domain reliability, sync, telemetria
(`MetricsReportingEnabled`), Safe Browsing, Translate, OptimizationHints, barras
do Edge.

O mecanismo foi escolhido porque a API do pywebview 6.2.1 **fixa**
`AdditionalBrowserArguments = '--disable-features=ElasticOverscroll'` e não
aceita argumentos extras. A documentação da Microsoft diz que a variável de
ambiente é **anexada** aos argumentos do host — é o que permite controlar o
runtime sem fork do pywebview.

Três decisões que estão no código:

1. **Não sobrescreve** valor já definido. Se suporte ou depuração puseram
   argumentos, misturar quebraria a janela de um jeito difícil de diagnosticar.
2. **Não declara zero egress.** O resumo diz literalmente: *"reduz o tráfego do
   runtime; NÃO é firewall e não garante zero egress"*.
3. **O custo está registrado:** sem Safe Browsing a janela não consulta listas de
   reputação. Ela só carrega `127.0.0.1`, então o risco é baixo — mas é uma
   escolha, não um efeito colateral escondido.

`TestD09ContinuaAberto` falha se alguém "resolver" o item afrouxando o critério
no documento.

**O que falta:** medição de rede em Windows com o controle aplicado. Sem isso,
D-09 continua **BLOCKED**, não PASS.

### 4.3 Controles verificados nesta rodada

| Controle | Estado | Evidência |
|---|---|---|
| Bind exclusivo em 127.0.0.1 | PASS | `SO_EXCLUSIVEADDRUSE` no Windows; testes de bind |
| Token de sessão | PASS | comparação por `secrets.compare_digest`; 403 sem token |
| Validação de Origin/Host | PASS | 403 para Host e Origin externos |
| Portas efêmeras | PASS | porta 0 quando a preferida está ocupada |
| Traversal / symlink / zip-slip | PASS (Linux) | 40 testes de traversal, 17 de arquivo |
| Escritas atômicas | PASS | `atomic.py` + teste de kill |
| Integridade de pacote | PASS | intruso no zip detectado com motivo |
| Ausência de segredos | PASS | varredura de descritor, catálogo, exportação |
| Logs sem vazamento | PASS | token ausente dos logs de evidência |

**PARTIAL conhecido:** symlink é *pulado* no Windows no ambiente original
(criação de symlink exige privilégio). O caminho de recusa está implementado e
testado em Linux.

---

## 5. Decisões humanas — situação

Separadas por consequência real, não por data.

### 5.1 Bloqueiam publicação

| ID | Decisão | Por que bloqueia |
|---|---|---|
| `D-16` | Licença do projeto | Sem `LICENSE`, não há direito de reutilização concedido. Publicar sem isso é ambíguo por construção |

### 5.2 Bloqueiam funcionalidade futura (não o MVP)

| ID | Decisão | O que fica bloqueado |
|---|---|---|
| `D-05` | Isolamento de execução | Test Lab inteiro; nada que execute código de terceiro |
| `D-18` | Risco aceitável | Mesma trava, do lado do produto |
| `D-12` | Catálogo remoto | Marketplace, importação por URL/git |
| `D-08` | SDK público | Só se houver consumidor externo real |
| `D-09` | API local | Só se arquivo em disco provar insuficiente |

### 5.3 Não bloqueiam nada agora

`D-01` (nome), `D-03`, `D-06`, `D-13`, `D-14`, `D-27` — `RECOMMENDED` ou
`ADOPTED`, **não `APPROVED`**. Nenhuma foi promovida nesta rodada.

### 5.4 Exigem o proprietário

`D-16` acima, e a decisão comercial sobre assinatura de código (SmartScreen
mostra aviso em executável não assinado — `Get-AuthenticodeSignature` retornou
`NotSigned`).

**Nada foi escolhido por mim.** Não criei `LICENSE`, não criei `TRADEMARK.md`,
não alterei `main`.

---

## 6. Pesquisa consultada (Lia-Research)

Consultado sem alteração: `RESEARCH-INDEX.md`, `projects/lia-agent-hub/INDEX.md`,
`decisions/PENDING/`, `cross-project/`.

| ID | O que aportou | Como apareceu no código |
|---|---|---|
| `LR-MCP-002` (via `DR-0011`) | Campos que um servidor MCP precisa declarar: transporte, licença, tools, egress, credenciais | Modelo `MCPServer` já os cobre; `config_para_host` expõe `pendencias` |
| `DR-0012` (política de instalação) | Instalação nunca automática; servidor sem licença não é instalável | Hub não instala nada; `pendencias` declara o que falta |
| `LR-SEC-005` (permissões por execução) | Grant/Lease/AuditRecord | Fora de escopo (execução bloqueada por D-05/D-18); não implementado |
| `LR-LIC-001`, `LR-LIC-003` | Licença por componente, não uniforme | Já aplicado no catálogo Stitch |
| Gaps `E-1…E-9` | Lacunas herdadas | E-1 fechado no Hub (licença por arquivo **ou** frontmatter); os demais seguem abertos |

Nenhuma pesquisa foi repetida. As lacunas `CONFIRMED`/`BLOCKED` do índice
(tempos, benchmarks de GPU, WER) não afetam o Hub.

---

## 7. O que ainda falta para "funcionalmente pronto"

Lista curta e ordenada por consequência:

1. **Medição de rede em Windows com o controle aplicado** — é o único item da
   promessa *local-first* sem prova. D-09 continua BLOCKED.
2. **Build do `.exe` e execução em máquina sem Python** — o spec está validado
   estaticamente, mas não empacotado aqui (`libpython3.11.so` ausente) nem
   executado em Windows por esta sessão.
3. **`D-16`** — sem licença definida, distribuição para terceiros é ambígua.
4. **Assinatura de código** — decisão do proprietário; sem ela, SmartScreen
   avisa.
5. **Symlink no Windows** — o caminho existe e é testado em Linux; a execução
   Windows exige privilégio de criação de link.

Nenhum desses depende de código novo. Todos dependem de ambiente ou de decisão.

---

## 8. Comandos reproduzíveis

```bash
# suíte completa
.venv/bin/python -m pytest -o addopts="" -q            # 644 passed

# por classe de segurança
.venv/bin/python -m pytest tests/security -q

# corpus real do ecossistema (53 skills)
.venv/bin/python docs/operations/evidence/corpus_probe.py

# leitor independente do índice (roda sem o Hub)
python -S docs/examples/independent-reader/read_index.py <index.json>
python -S docs/examples/independent-reader/read_index.py <index.json> --check

# CLI de desenvolvimento
PYTHONPATH=src .venv/bin/python -m lia_agenthub --home /tmp/h diagnostico
PYTHONPATH=src .venv/bin/python -m lia_agenthub --home /tmp/h validate ./minha-skill
PYTHONPATH=src .venv/bin/python -m lia_agenthub --home /tmp/h index --publish

# build (exige ambiente com libpython compartilhada)
.venv/bin/python -m PyInstaller packaging/lia_agenthub.spec
```

---

## 9. Declaração de limites desta sessão

- Não executei Windows. Nenhum item marcado PASS depende de Windows.
- Não empacotei o `.exe`. O spec foi validado estaticamente; o build falhou aqui
  por falta de `libpython3.11.so`, e isso está registrado em vez de contornado.
- Não medi rede do WebView2 com o controle aplicado — não há Windows disponível.
- Não alterei `main`, não criei branch, não fiz merge nem PR.
- Não escolhi licença e não criei arquivo de licença.
