# Fronteiras de produto, arquitetura e modelo de dados

**Documento:** `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Branch:** `arena/a92004be-lia-agenthub`
**Status:** `PROPOSED` — proposta arquitetural para revisão humana. **Não autoriza implementação.**
**Data:** 2026-11-15 (UTC)
**Cobre:** `PRODUCT-BOUNDARIES.md`, `CAPABILITY-DATA-MODEL.md` e `DISTRIBUTION-CONTRACTS.md` do briefing da Fase 0.

---

## 1. Enunciado do problema

### 1.1 O que existe hoje

A auditoria (`docs/research/REPOSITORY-AND-BRANCH-AUDIT.md`) estabelece cinco fatos:

1. **Três produtos definiram "capacidade" de três formas incompatíveis.** Project separa em 8 camadas (`03-ESQUEMA-E-DADOS.md`); Forge usa `capabilityId` + `status ∈ {implemented,partial,proposed,planned}` (`registry.mjs`); Studio usa `capability ∈ frozenset` sem taxonomia (`permissions.py`).
2. **Nenhum produto tem registro de proveniência para Skills.** Studio guarda SHA-256 do conteúdo — integridade, não origem. Forge *propõe* `source {upstream, commit, author, contentHash}` e `trust` em `SKILLS-KNOWLEDGE-ENGINE.md`, marcado `PLANNED`.
3. **Nenhum produto exporta "capacidade" como pacote portátil.** Studio exporta projeto; Forge exporta asset.
4. **O contrato de distribuição entre apps está explicitamente bloqueado:** `REQUIRES_HUMAN_DECISION` no Forge, `sent: False` no Studio.
5. **Existem oito lacunas transversais (L-01…L-08)** que nenhum produto atende.

### 1.2 O que o Hub deve ser

> **O Hub é o registro de capacidades do ecossistema: onde uma capacidade ganha identidade, origem, versão, licença, avaliação de risco e forma de pacote — e de onde ela sai como arquivo para qualquer host.**

O Hub **não** é onde a capacidade roda, nem onde ela é autorizada, nem onde credenciais vivem.

### 1.3 O teste de fronteira (usar em toda proposta futura)

Uma funcionalidade pertence ao Hub **somente** se responder "sim" a todas:

| # | Teste | Se falhar |
|---|---|---|
| T1 | O resultado útil é **um arquivo ou um pacote em disco**? | Pertence a um host |
| T2 | Funciona com o processo do Hub **encerrado**? | Pertence a um host |
| T3 | Um humano pode inspecionar o resultado **sem o Hub instalado**? | Pertence a um host |
| T4 | A operação é **determinística** dado o mesmo input? | Se precisa de modelo em tempo real, é sugestão — nunca decisão |
| T5 | Não exige **autorização de execução** nem **credencial**? | Pertence ao host |

Aplicação imediata:

| Proposta | T1 | T2 | T3 | T4 | T5 | Veredito |
|---|:-:|:-:|:-:|:-:|:-:|---|
| Catalogar uma Skill com proveniência | ✓ | ✓ | ✓ | ✓ | ✓ | **HUB** |
| Empacotar e exportar `.lia-capability` | ✓ | ✓ | ✓ | ✓ | ✓ | **HUB** |
| Validar estrutura de `SKILL.md` | ✓ | ✓ | ✓ | ✓ | ✓ | **HUB** |
| Conectar um servidor MCP | ✗ | ✗ | — | — | ✗ | **STUDIO/FORGE** |
| Executar uma Skill "para ver se funciona" | ✗ | ✗ | ✗ | ✗ | ✗ | **HOST** |
| Guardar a chave de API do MCP | ✗ | ✗ | ✗ | — | ✗ | **HOST** (cofre) |
| Baixar pesos de modelo | ✗ | ✗ | ✗ | — | ✗ | **FORGE** |
| Orquestrar subagentes | ✗ | ✗ | ✗ | ✗ | ✗ | **STUDIO** |

---

## 2. Fronteiras entre produtos

### 2.1 Tabela de propriedade

Cada domínio tem **exatamente um dono**. "Consome" não é "possui".

| Domínio | Lia Agent Hub | Lia Studio | Lia Forge | Lia Project (Waifu) | Host externo |
|---|:-:|:-:|:-:|:-:|:-:|
| **Identidade e proveniência de capacidade** | **DONO** | consome | consome | consome | consome |
| **Formato de pacote portátil** | **DONO** | consome | consome | consome | consome |
| **Validação estrutural de Skill/MCP** | **DONO** | consome | consome | — | consome |
| Catálogo de Skills **do projeto** | — | **DONO** | — | — | — |
| Seleção de Skill por agente/tarefa | — | **DONO** | consome | consome | **DONO** |
| Permissões e approvals de execução | — | **DONO** | **DONO** | **DONO** | **DONO** |
| Cofre de credenciais | — | **DONO** | **DONO** | **DONO** | **DONO** |
| Conexão e ciclo de vida de MCP | — | **DONO** | **DONO** | **DONO** | **DONO** |
| Execução de agente / orquestração | — | **DONO** | — | **DONO** | **DONO** |
| Produção de assets | — | — | **DONO** | — | — |
| Política de admissão de provider/modelo | — | **DONO** | **DONO** | **DONO** | **DONO** |
| Catálogo **público** de metadados de modelo | **DONO** (metadado) | consome | consome | consome | — |
| Download e gestão de pesos | — | — | **DONO** | **DONO** | — |
| Memória de conversa / de personagem | **proibido** | — | — | **DONO** | — |
| Memória de sessão de agente | — | **DONO** | — | **DONO** | **DONO** |
| Teste isolado de capacidade de terceiro | **DONO** (`PROPOSED`) | — | — | — | — |
| QA de gameplay / build / release | — | **DONO** | — | — | — |

### 2.2 Três proibições explícitas

1. **O Hub nunca executa capacidade importada.** Nem "só para testar", nem "em modo seguro", até que `D-05`/`D-18` tenham decisão humana com sandbox comprovado. Nesta fase, Test Lab **não existe**.
2. **O Hub nunca guarda segredo.** Nem chave de MCP, nem token de provider, nem credencial de host. Guarda **o nome** da variável de ambiente — o valor é do host.
3. **O Hub nunca é runtime obrigatório.** Nenhum consumidor pode falhar por o Hub estar desinstalado. O contrato é **arquivo em disco**.

### 2.3 Onde cada um dos três produtos Lia se encaixa

```
                    ┌──────────────────────────────────────────┐
                    │           LIA AGENT HUB                  │
                    │  Plano A — autoria, curadoria,           │
                    │  validação, versionamento, empacotamento │
                    │                                          │
                    │  Biblioteca local + proveniência         │
                    │  Ponteiro p/ recursos externos           │
                    │  Pacote .lia-capability                  │
                    │  Índice com hashes — NÃO assinado        │
                    │  (contentHash + treeHash)                │
                    └───────────────┬──────────────────────────┘
                                    │  arquivos em disco
                                    │  (sem API obrigatória,
                                    │   sem processo residente)
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
┌───────▼────────┐        ┌─────────▼─────────┐       ┌─────────▼────────┐
│  LIA STUDIO    │        │   LIA FORGE       │       │  HOST EXTERNO    │
│                │        │                   │       │ (Claude Code,    │
│ Plano B:       │        │ Plano B:          │       │  Codex, Cursor,  │
│ orquestra,     │        │ produz assets,    │       │  OpenCode…)      │
│ autoriza,      │        │ roda pipelines,   │       │                  │
│ executa        │        │ valida artefato   │       │ Plano B próprio  │
│                │        │                   │       │                  │
│ dono de:       │        │ dono de:          │       │ dono de:         │
│ sessão,        │        │ provider,         │       │ sessão,          │
│ permissão,     │        │ workflow,         │       │ permissão,       │
│ cofre, MCP     │        │ pesos, QA técnico │       │ cofre            │
└────────────────┘        └───────────────────┘       └──────────────────┘

              LIA PROJECT (Waifu) — fora do caminho:
              memória de convivência, privada, nunca
              atravessa para o Hub por padrão
```

**O que a figura afirma:** a única seta entre o Hub e os demais é *arquivo em disco*. Não há seta de "execução", "credencial", "sessão" ou "memória". Isso é a arquitetura, não um detalhe de implementação.

---

## 3. Plano A / Plano B — por que a separação resolve o problema

| | **Plano A — Hub** | **Plano B — Host** |
|---|---|---|
| Pergunta | *"O que esta capacidade é, de onde veio, e o que ela exige?"* | *"Posso, devo e vou executar isso agora, neste projeto?"* |
| Entrada | Intenção do autor, recurso importado, diretório de conhecimento | Capacidade já registrada + política + contexto |
| Saída | Arquivo/pacote versionado + relatório de confiança | Efeito no mundo (arquivo, build, chamada, gasto) |
| Frequência | Baixa, deliberada | Alta, interativa |
| Falha | "metadado incompleto" | "arquivo corrompido", "credencial expirada", "usuário negou" |
| Precisa estar rodando | **Não** | Sim |
| Precisa de rede | **Não** | Frequentemente |

**Consequência de projeto:** o Hub pode ser **um editor de arquivos com um validador**. É por isso que o MVP é defensável e barato — e é por isso que ele **não pode** virar um runtime universal.

---

## 4. Modelo de recursos — vocabulário unificado

O Hub **adota** o vocabulário já validado no ecossistema. Não inventa.

### 4.1 Os dez tipos de recurso

| # | Tipo | Definição operacional | Executável? | Dono da execução |
|---|---|---|---|---|
| `skill` | Instruções e procedimento | Prosa Markdown em formato Agent Skills | **Não** | Host (modelo lê) |
| `mcp-server` | Servidor MCP | Processo/endpoint que expõe tools/resources/prompts | Sim | Host conecta |
| `cli` | Ferramenta de linha de comando | Binário/pacote invocável | Sim | Host invoca |
| `api` | Serviço externo | Interface HTTP/RPC | Sim | Host chama |
| `plugin` | Extensão de aplicativo | Pacote para outro app | Depende | Esse app |
| `framework` | Runtime/SDK de agente | Biblioteca para construir agentes | Sim | Host embute |
| `model` | Provider/modelo | Serviço ou pesos | Sim | Host/Forge roteia |
| `workflow` | Pipeline/template | DAG ou template declarativo | Depende | Host/Forge |
| `knowledge` | Base de conhecimento | Diretório de Markdown, PDFs, corpus | **Não** | Host indexa |
| `reference` | Referência técnica | Documentação, pesquisa, exemplo | **Não** | — |

### 4.2 Adoção dos vocabulários existentes — mapa de compatibilidade

| Conceito do Hub | Origem adotada | Justificativa |
|---|---|---|
| `capabilityId` | Forge `registry.mjs` (regex `^[a-z0-9][a-z0-9._-]*$`) | Já implementado com validador |
| Separação **modelo ≠ pesos ≠ runtime ≠ provider ≠ adapter** | Project `03-ESQUEMA-E-DADOS.md` §3.1 (8 camadas) | Resolve a confusão mais cara do ecossistema |
| `status ∈ {implemented, partial, proposed, planned}` | Forge `CAPABILITY_STATUSES` | Já implementado |
| Estados de disponibilidade `ready/unknown/blocked/missing` | Forge `provider-hub.mjs` | **Do host**, não do Hub — o Hub registra o que o host informou |
| Ciclo de vida `catalogued → installable → installed → configured` | Project `03-ESQUEMA-E-DADOS.md` §3.3 | Já modelado com regra de quem promove |
| `requirements {os, gpu, vramMb, ramMb, diskMb, network, runtimes, tools}` com `null` = não medido | Forge `registry.mjs` | **Regra de ouro:** nunca inventar zero |
| `trust ∈ {reviewed-external, first-party, user-provided, unreviewed}` | Forge `SKILLS-KNOWLEDGE-ENGINE.md` (proposta) | Adotar como está |
| Taxonomia `dominio.acao` | Project `03-ESQUEMA-E-DADOS.md` §3.2 | Adotar como está |
| Classe de adapter `local-tool / internal-process / remote-service` | Forge `adapters/sdk.mjs` | Adotar |
| `EXTRACTED` / `INFERRED` para separar fato de inferência | Graphify (referência externa) | Boa prática de proveniência |

**O que o Hub acrescenta de novo (e só isto):**

| Campo novo | Por que não existe hoje | Lacuna coberta |
|---|---|---|
| `source {upstream, commit, author, contentHash}` **persistido** | Forge só propôs | L-01 |
| `license {code, content, weights, reviewedAt, spdx}` **por camada** | Cada produto tem uma noção só | L-01, L-04 |
| `provenance.chain[]` (histórico de origem até a cópia atual) | Ninguém tem | L-01 |
| `integrity {algo, digest}` do **pacote** (não do arquivo) | Studio tem hash de conteúdo de Skill | L-01 |
| `egress {destinations[], carriesUserData, consentRequired}` | Forge tem `network`; Project tem `data_egress` em prosa | L-01 |
| `secrets {envVars[]}` — **só nomes** | Ninguém modela sem guardar valor | L-01 |
| `compatibility {hosts[], produces[], consumes[]}` declarativo | Agent Skills só tem `compatibility` em prosa ≤500 | L-01 |
| Formato `.lia-capability` | Não existe | L-03 |

---

## 5. Arquitetura em camadas

### 5.1 As cinco camadas

```
┌─────────────────────────────────────────────────────────────────┐
│ L5  INTERFACE          (a ser decidida — ver PLATFORM-AND-       │
│                        TECHNOLOGY-DECISION.md)                  │
└────────────────────────────┬────────────────────────────────────┘
                             │ chama
┌────────────────────────────▼────────────────────────────────────┐
│ L4  CASOS DE USO       importar · criar · validar · versionar ·  │
│                        empacotar · exportar · catalogar         │
└────────────────────────────┬────────────────────────────────────┘
                             │ chama
┌────────────────────────────▼────────────────────────────────────┐
│ L3  DOMÍNIO            Capability · Provenance · Version ·      │
│     (puro, sem I/O)     License · Trust · Validation · Package  │
│                        REGRA: biblioteca padrão apenas.         │
│                        Sem framework. Sem rede. Sem SO.         │
└────────────────────────────┬────────────────────────────────────┘
                             │ usa
┌────────────────────────────▼────────────────────────────────────┐
│ L2  ADAPTERS           filesystem · git · archive(zip/tar) ·    │
│     (I/O substituível)  sha256 · markdown/frontmatter parser ·  │
│                         license detection · host-integration    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│ L1  ARMAZENAMENTO      biblioteca local · índice · objetos      │
│                        (ver DATA-STORAGE-AND-PORTABILITY.md)    │
└─────────────────────────────────────────────────────────────────┘

        [opcional, fora do núcleo]  CLI  ·  API local loopback
        [proibido no núcleo]        execução · MCP client · rede
```

### 5.2 Regra de dependência (não negociável)

**L3 não importa L2, L4 nem L5.** O domínio é uma biblioteca de funções puras que recebe dados e devolve decisões. Isso é o que torna possível:

- testar tudo sem tocar disco;
- trocar a interface sem reescrever regra;
- rodar o núcleo em qualquer SO;
- auditar a parte que decide confiança — que é a parte que importa.

**Precedente no ecossistema:** `permissions.py` e `tool_registry.py` do Studio já são assim (`type(x) is ...`, sem I/O). `registry.mjs` e `provider-hub.mjs` do Forge também. O Hub não está inventando um padrão — está seguindo o que já funciona.

### 5.3 As camadas na prática

| Camada | Conteúdo | Dependências permitidas | Testável sem SO? |
|---|---|---|---|
| L3 Domínio | `Capability`, `Provenance`, `TrustLevel`, `ValidationResult`, `PackageManifest` | stdlib | **Sim** |
| L2 Adapters | leitura/escrita de arquivo, zip, git, sha256, parser YAML | libs de build, fixadas | Parcial (via fake) |
| L4 Casos de uso | `import_capability`, `validate_capability`, `export_package`, `diff_versions` | L3 + L2 | Sim (via fake L2) |
| L5 Interface | a decidir | L4 | Não |

---

## 6. Modelo de dados

### 6.1 Estrutura de um registro de capacidade

O Hub separa **o que a capacidade é** (formato do padrão, interoperável) do **que o Hub sabe sobre ela** (manifesto próprio). Essa separação resolve a tensão de `D-03`:

```
minha-capacidade/                    ← pacote desempacotado
├── SKILL.md                         ← FORMATO PADRÃO (Agent Skills)
│                                      name, description, license,
│                                      compatibility, metadata
├── scripts/                         ← opcional, formato padrão
├── references/                      ← opcional, formato padrão
├── assets/                          ← opcional, formato padrão
├── .lia/
│   ├── capability.json              ← MANIFESTO DO HUB
│   ├── provenance.json              ← cadeia de custódia
│   ├── history.json                 ← versões e diffs
│   └── THIRD_PARTY_NOTICES.md       ← avisos preservados
└── .lia-capability.json             ← só no .zip exportado (ver §8)
```

**Por que `.lia/` e não campos extras no frontmatter:** a especificação Agent Skills rejeita chave desconhecida em clientes estritos. Colocar metadado do Hub no `SKILL.md` **quebraria** o cliente — que é o oposto de portabilidade.

### 6.2 `capability.json` — campos

```jsonc
{
  // ---- Identidade ----
  "schemaVersion": 1,
  "id": "lia-game-qa-plan",              // = name do SKILL.md (NFKC)
  "type": "skill",                        // um dos 10 tipos de §4.1
  "displayName": "Plano de QA para jogo",
  "summary": "≤280 chars, para listagem",

  // ---- Origem e integridade ----
  "source": {
    "kind": "authored" | "imported" | "adapted" | "forked",
    "upstream": "https://github.com/…/SKILL.md",
    "commit": "05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418",
    "author": "Donchitos",
    "contentHash": { "algo": "sha256", "digest": "…" },
    "retrievedAt": "2026-11-15T00:00:00Z"
  },
  "provenanceChain": [                   // cadeia completa, do mais antigo ao atual
    { "step": "upstream", "ref": "…", "at": "…" },
    { "step": "adapted",  "ref": "…", "at": "…", "changes": "…" }
  ],

  // ---- Licença, POR CAMADA (§6.4) ----
  "license": {
    "code":    { "spdx": "MIT",  "url": "…", "redistributable": true },
    "content": { "spdx": "MIT",  "url": "…", "redistributable": true },
    "weights": null,                     // null = não se aplica / não revisado
    "reviewedAt": "2026-11-15",
    "attributionRequired": true
  },

  // ---- Confiança ----
  "trust": "reviewed-external",          // §6.3
  "trustEvidence": {
    "reviewedBy": "humano:<id>",
    "reviewedAt": "2026-11-15",
    "method": "manual-read" | "static-scan" | "none",
    "findings": []
  },

  // ---- Estado (vocabulário do Project/Forge) ----
  "lifecycle": "catalogued",             // catalogued|installable|installed|configured
  "hostStatus": null,                    // preenchido PELO HOST; null = não informado

  // ---- Requisitos (vocabulário do Forge; null = não medido) ----
  "requirements": {
    "os": null, "gpu": null, "vramMb": null, "ramMb": null,
    "diskMb": null, "network": false,
    "runtimes": [], "tools": []
  },

  // ---- Permissões DECLARADAS (nunca concedidas) ----
  "declaredPermissions": {
    "filesystem": { "read": [], "write": [] },
    "network":    { "egress": [] },
    "process":    { "spawn": false, "shell": false },
    "secrets":    { "envVars": [] }       // SÓ NOMES. Nunca valores.
  },

  // ---- Egress e dados ----
  "egress": {
    "destinations": [],
    "carriesUserData": false,
    "consentRequired": true,              // default seguro
    "notes": ""
  },

  // ---- Compatibilidade ----
  "compatibility": {
    "hosts": ["claude-code", "codex", "cursor"],
    "produces": [], "consumes": [],
    "notes": ""
  },

  // ---- Dependências (referências, NÃO resolução) ----
  "dependsOn": [
    { "id": "…", "kind": "capability" | "runtime" | "secret-name",
      "versionRange": "^1.2.0", "optional": false,
      "resolvableBy": "hub" | "host" | "user" }
  ],

  // ---- Ciclo de vida editorial ----
  "status": "implemented",
  "createdAt": "…", "updatedAt": "…",
  "hubVersion": "0.1.0"
}
```

**Regras do modelo:**

| Regra | Motivo |
|---|---|
| **`null` significa "não medido/não revisado", nunca "zero" nem "não"** | Herdado do Forge. Impede afirmação falsa sobre hardware/licença |
| **`secrets.envVars` são nomes, jamais valores** | Hub não é cofre |
| **`declaredPermissions` é declaração, não concessão** | Quem autoriza é o host |
| **`hostStatus` é escrito pelo host, não inferido** | Evita "o Hub achou que estava instalado" |
| **`dependsOn.resolvableBy` diz quem resolve** | O Hub não resolve dependência de execução |
| **`trust` nunca é promovido automaticamente** | Só revisão humana promove |

### 6.3 Escala de confiança

Adotada do Forge, com critério de promoção explícito:

| Nível | Significado | Como se chega | Pode ser automático? |
|---|---|---|---|
| `unreviewed` | Importado, nada verificado além de estrutura | Import | **Sim** (default) |
| `user-provided` | O próprio usuário escreveu/forneceu | Declaração do usuário | Sim, com registro |
| `reviewed-external` | Terceiro, revisado por humano com método declarado | Revisão humana explícita | **Não** |
| `first-party` | Mantido pelo projeto Lia | Origem verificada (repo + commit) | Sim, se repo permitido |

**Regra dura:** `reviewed-external` e `first-party` **nunca** são atribuídos por análise estática. Um scanner verde produz `evidence`, não `trust`.

### 6.4 Licença por camada — a distinção que evita erro caro

Precedentes reais no ecossistema, citados no kit e no Forge:

| Camada | Exemplo de divergência | Consequência se confundida |
|---|---|---|
| **Código** | MIT no repositório | — |
| **Conteúdo** (prosa, texto da Skill) | Pode ser CC-BY-4.0 ou sem licença | Redistribuir prosa sem licença é violação |
| **Pesos/modelo** | "Código pode ser livre e os pesos não" — caso XTTS-v2 documentado no kit | Baixar peso achando que a licença do código cobre |
| **Dados/exemplos** | Assets, PSDs, imagens de referência | Forge já registra item externo **sem `LICENSE`** (`license: null`) |
| **Marca** | Nome/logo fora da MIT | Uso indevido de identidade |

O modelo **obriga** as três primeiras a serem campos separados. `null` quando não revisado.

---

## 7. Contratos entre componentes

### 7.1 Contrato Hub ↔ Host — arquivo, não API

**Decisão proposta para `D-09`:** a distribuição primária é **arquivo versionado em disco**. API local é opcional e secundária.

| Propriedade | Arquivo (primário) | API local (opcional) |
|---|---|---|
| Host precisa do Hub rodando | **Não** | Sim |
| Funciona desinstalado | **Sim** | Não |
| Inspecionável por humano | **Sim** | Não sem cliente |
| Versionável em git | **Sim** | Não |
| Auditável offline | **Sim** | Não |
| Complexidade | Baixa | Média (porta, auth, bind) |
| Risco de segurança | Baixo (é dado) | Médio (é superfície) |

**Por que o arquivo vence aqui:** o Host é um app de desktop local. Uma API local entre dois processos na mesma máquina resolve um problema que **arquivo já resolve**, ao custo de uma superfície de rede, autenticação e ciclo de vida. O Forge já registra a decisão: *"o contrato de mensagens e a forma de descoberta/transporte ainda precisam de decisão"* — este documento recomenda **arquivo em diretório acordado, com manifesto**.

### 7.2 Diretório de troca

```
%USERPROFILE%\Lia\Comum\Capacidades\       ← raiz visível da marca (kit §4.1)
├── LEIA-ME.txt                            ← 10 linhas, sem jargão
├── biblioteca\                            ← o que o Hub publica
│   ├── index.json                         ← catálogo publicável
│   └── <id>\<versao>\…                    ← pacotes desempacotados
└── exportados\                            ← o que o usuário mandou para fora
```

**Regra:** o host **lê** `biblioteca/`. O Hub **escreve** nela. Nenhum dos dois escreve na pasta do outro. Isso evita o bug clássico do kit (§5.6): *"ler, mesclar, gravar em arquivo temporário e renomear por cima"*.

### 7.3 Contrato com o Studio (proposta, não implementada)

O Studio já tem `forge_brief.py` com um padrão correto: preview → hash → `sent: False` → confirmação. O Hub deve seguir o **mesmo desenho**:

| Etapa | Hub faz | Studio faz |
|---|---|---|
| 1 | Publica `index.json` + pacotes | — |
| 2 | — | Lê `index.json`, mostra lista com `trust`, `license`, `requirements` |
| 3 | — | Usuário escolhe; Studio mostra **o que vai ser copiado** e o hash |
| 4 | — | Confirma; Studio copia para `.agents/skills/<id>/` do projeto |
| 5 | — | Studio registra origem (`source.commit`, hash) no próprio registro |

**O Hub não sabe que o Studio existe.** Não há callback, não há handshake, não há sessão. Isso é a garantia de T1–T3.

### 7.4 Contrato com o Forge (proposta, não implementada)

Idêntico em forma, diferente em conteúdo: o Forge consome capacidades do tipo `mcp-server`, `cli`, `api`, `model` com mais frequência que `skill`. O `requirements` do Hub (adotado do Forge) já é o vocabulário que o Forge entende.

**Limite explícito:** o Hub **não** substitui `PROVIDER-AND-MODEL-ADMISSION-POLICY.md`. O Hub registra *metadados públicos* de um provider; **a admissão é do Forge**.

---

## 8. Formato de pacote `.lia-capability`

### 8.1 Estrutura

`<id>-<versao>.lia-capability` = arquivo ZIP (extensão própria, conteúdo padrão) com:

```
manifest.json                 ← o único arquivo obrigatório na raiz
payload/                      ← a capacidade, no formato do seu tipo
  └── (SKILL.md, scripts/, references/, …)
provenance.json
NOTICE                        ← só se licença exigir (Apache-2.0)
THIRD_PARTY_NOTICES.md
signatures/                    ← RESERVADO, não usado no MVP
  └── (nenhum código lê esta pasta)
```

> **Sobre `signatures/`:** reservar o diretório **não é** implementar assinatura. No MVP, um
> arquivo colocado ali é **ignorado**, não verificado — e o manifest **não** pode declarar
> `signed: true`. Assinatura criptográfica é Fase 3+ e está `RESEARCH` pendente. Ver
> `SECURITY-AND-TRUST-MODEL.md` §3.7.1 para o vocabulário obrigatório.

**Por que ZIP:** inspecionável com qualquer ferramenta, sem runtime, sem criptografia proprietária. Um usuário pode abrir com o Explorer do Windows e ver o conteúdo. Isso satisfaz a regra nº 3 da marca (o trabalho é dele) e T3.

### 8.2 `manifest.json` — o contrato mínimo

```jsonc
{
  "formatVersion": 1,                 // schema do pacote
  "id": "…", "version": "1.2.0",      // semver
  "type": "skill",
  "createdAt": "…",
  "hubVersion": "0.1.0",              // quem produziu (padrão Graphify)
  "payload": {
    "root": "payload/",
    "files": [ { "path": "SKILL.md", "sha256": "…", "bytes": 1234 } ],
    "treeHash": "sha256:…"            // hash do conjunto, não só dos arquivos
  },
  "integrity": { "algo": "sha256", "digestOfManifest": null },
  "requires": { … §6.2 requirements },
  "license": { … §6.4 },
  "trust": "…"
}
```

**Regras:**
- `payload.files[]` é **lista completa** — o consumidor pode verificar arquivo a arquivo.
- `treeHash` detecta remoção/adição, não só alteração.
- `formatVersion` é **obrigatório** e **independente** da versão da capacidade. Mudança incompatível de formato exige incremento — padrão adotado de `graph.schema_version`.
- O manifest **não contém** instrução executável, script ou URL de instalação. É dado, não comando.

### 8.3 O que o pacote **não** faz

| Não faz | Por quê |
|---|---|
| Não instala | Instalação é do host |
| Não declara "seguro" | Nenhum campo `safe`. Só `trust` com evidência |
| Não inclui credencial | Nunca |
| Não inclui peso de modelo | Fora de escopo |
| Não resolve dependência | Só declara |

---

## 9. Alternativas consideradas e descartadas

| Alternativa | Por que foi considerada | Por que não |
|---|---|---|
| **Hub como serviço HTTP local obrigatório** | Facilitaria integração com hosts | Viola T2/T3: host pararia de funcionar com Hub desinstalado. Adiciona porta, auth, ciclo de vida e superfície de ataque a um app que **edita arquivos** |
| **Hub como plugin do Studio** | Menos código | Viola independência (regra nº 1) e o critério de §14 do `PRODUCT-VISION.md` (haveria usuários além do Studio/Forge) |
| **Hub como marketplace remoto desde o início** | Mais alcance | `D-12`; exige backend, conta, moderação, custo e política de conteúdo — nada disso é MVP. Também contradiz local-first |
| **Formato próprio de Skill (não Agent Skills)** | Liberdade de campos | Já existe padrão aberto governado com 40+ clientes; um formato Lia seria ilegível por todos eles. **Custo de adoção é menor que custo de invenção** |
| **Frontmatter estendido dentro do `SKILL.md`** | Um arquivo só | Clientes estritos **rejeitam** chave desconhecida com erro. Quebraria portabilidade — exatamente o oposto do objetivo |
| **SQLite como armazenamento primário** | Consultas rápidas | Dado do usuário ficaria em binário. Contradiz "trabalho do usuário em local acessível, copiável, removível". Ver `DATA-STORAGE-AND-PORTABILITY.md` §3 |
| **Git embutido como backend obrigatório** | Versionamento grátis | Git é ótimo **opcional**; obrigatório exclui o usuário leigo. Ver `DATA-STORAGE-AND-PORTABILITY.md` §4 |
| **Test Lab no MVP** | É o recurso mais pedido implicitamente | Sem sandbox comprovado, "testamos" vira afirmação falsa. **`D-05` e `D-18` bloqueiam.** O MVP entrega valor grande sem executar nada |

---

## 10. O que a arquitetura **impede** por construção

Uma arquitetura boa é conhecida pelo que torna impossível:

| Proibição estrutural | Como é garantida |
|---|---|
| Hub executar código importado | Núcleo (L3) não importa `subprocess`, `os.system`, `socket` nem cliente MCP. Só L2 tem I/O, e L2 só faz arquivo/zip/hash/git |
| Hub guardar credencial | Não existe campo de valor em `secrets` — só `envVars: []` de **nomes** |
| Hub ser dependência de execução | Contrato é arquivo; nenhum host importa módulo do Hub |
| Atualização silenciosa | Toda versão é explícita no manifest; pinagem por `contentHash`; `D-10` |
| Distribuição de capacidade sem licença | `license` é campo obrigatório do manifest; export falha se `null` |
| Marcar como "seguro" sem humano | Não existe campo `safe`; `trust` só por revisão registrada |
| Afirmar execução não feita | Núcleo não executa nada — logo não há como afirmar |

---

## 11. Riscos arquiteturais e mitigações

| # | Risco | Severidade | Mitigação |
|---|---|---|---|
| A-01 | **Escopo infla para runtime** — "já que temos o pacote, por que não rodar?" | **Alta** | Teste T1–T5 em toda proposta; proibição estrutural da §10; decisão humana antes de qualquer capacidade de execução |
| A-02 | **Terceiro vocabulário** de capacidade | Alta | §4.2 adota o existente; qualquer campo novo listado e justificado |
| A-03 | **Duplicar o editor de Skills do Studio** | Média | §2.1: Studio = catálogo do projeto; Hub = biblioteca e pacote. Diferença precisa constar na interface |
| A-04 | **Formato de pacote virar bitrot** | Média | `formatVersion` versionado; ZIP padrão; migração documentada |
| A-05 | **Núcleo puro virar impuro** sob pressão de prazo | Média | Regra de dependência de §5.2 verificável por teste de camada (o Studio já tem `test_dependency_layers.py`) |
| A-06 | **Modelo de dados virar schema rígido** que impede evolução | Média | `schemaVersion` + campos opcionais + `null` semântico |
| A-07 | **Hub publicar capacidade não revisada** como se fosse aprovada | **Alta** | Default `unreviewed`; export avisa; `index.json` mostra o nível |

---

## 12. Conclusões

1. **A fronteira do Hub é defensável e estreita:** identidade, proveniência, licença, confiança, validação estrutural, versionamento e empacotamento de capacidades. Oito lacunas confirmadas, nenhuma delas exige execução.
2. **O modelo de dados já tem 70 % pronto no ecossistema** — Project (8 camadas) e Forge (registry + adapter SDK + trust) fornecem o vocabulário. O Hub acrescenta proveniência persistida, licença por camada e o formato de pacote.
3. **O formato Agent Skills é o único ponto de interoperabilidade gratuito** que existe. O Hub o adota no `SKILL.md` e complementa em `.lia/`, sem tocar no frontmatter.
4. **Arquivo vence API local** para este produto, por T2/T3. API entra depois, se um host real precisar.
5. **O Hub pode ser impedido por construção de executar, guardar credencial e virar dependência.** Isso é mais forte que prometer disciplina.
6. **Test Lab não pertence ao MVP** e a razão é técnica, não conservadora: não há sandbox comprovado em Windows.

---

## Referências

- `docs/research/REPOSITORY-AND-BRANCH-AUDIT.md` — evidência de origem (módulos, commits, branches)
- `docs/research/INTEGRATION-CANDIDATES.md` — justificativa do formato Agent Skills (§2)
- `docs/architecture/SECURITY-AND-TRUST-MODEL.md` — ameaças, níveis de confiança, limites de automação
- `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` — onde os arquivos vivem, backup, portabilidade
- `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` — camada L5
- `docs/product/MVP-AND-ROADMAP.md` — o que entra primeiro
- `docs/DECISION-REGISTER.md` — D-02, D-03, D-04, D-07, D-08, D-09

**Evidência de código citada (branches, não `main`):**
- `BloomRX/Lia-Forge@arena/649f88bd-3dspritesheet` — `shared/capabilities/registry.mjs`, `shared/hub/provider-hub.mjs`, `shared/adapters/sdk.mjs`, `docs/SKILLS-KNOWLEDGE-ENGINE.md`
- `BloomRX/Lia-Project@arena/01a10290-lia-project` — `docs/research/lia-capability-catalog/03-ESQUEMA-E-DADOS.md`
- `BloomRX/Lia-Studio@arena/01a0f4ab-lia-gamedev` — `app/lia/{permissions,tool_registry,skills}.py`, `docs/LIA-FORGE-NA-PIPELINE.md` (citado no Forge `STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md`)
- `https://agentskills.io/specification` — frontmatter Agent Skills
