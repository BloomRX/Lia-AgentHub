# Dados, armazenamento e portabilidade

**Documento:** `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Branch:** `arena/a92004be-lia-agenthub`
**Status:** `PROPOSED` — proposta para revisão humana. **Não autoriza implementação.**
**Data:** 2026-11-15 (UTC)

---

## 1. Princípio que resolve os casos difíceis

> **Todo dado que o usuário criou é um arquivo que ele consegue abrir sem o produto. Todo dado derivado é descartável e reconstruível.**

Desta decomposição saem todas as decisões de armazenamento. Ela vem da regra nº 3 da marca (*"o trabalho dele é dele"*) e é consistente com dois padrões já implementados no ecossistema:

- Forge: workspace visível, `.spriteforge/` interno ao projeto escolhido.
- Project: wiki Markdown como fonte de verdade, índice derivado reconstruível.

---

## 2. Classificação dos dados

| # | Classe | Definição | Exemplo | Recriável? |
|---|---|---|---|---|
| D1 | **Trabalho do usuário** | O que ele criou ou assumiu como seu | Skill escrita por ele, notas, coleções, decisões de revisão | **Não** |
| D2 | **Curadoria** | Resultado de decisão humana registrada | `provenance.json`, `trust`, achados de revisão | **Não** (é histórico) |
| D3 | **Índice derivado** | Serve para consultar; deriva de D1+D2 | `index.json` (cache), busca, contagens | **Sim** |
| D4 | **Estado interno** | Preferências, última tela, migrações aplicadas | `config.json` | Sim (mas incômodo) |
| D5 | **Cache / temporário** | Sobreviver é irrelevante | pasta temp de import, thumbnails | Sim |
| D6 | **Log / auditoria** | Rastro de operação | `audit-YYYY-MM.jsonl` | Não (é evidência) |
| D7 | **Segredo** | Credencial | — | — |

**Ponto crítico:** D7 **nunca** é armazenado pelo Hub. Não existe campo, arquivo ou formato para ele. Ver §6.

---

## 3. Onde cada classe vive

### 3.1 Decisão principal: arquivo, não banco

| Opção | Vantagens | Desvantagens | Veredito |
|---|---|---|---|
| **Arquivos + `index.json` derivado** | Inspecionável, copiável, versionável em git, `grep`ável, sobrevive ao produto, zero dependência | Consulta não é indexada; escala limitada (mas biblioteca pessoal não é bilhão de linhas) | **ADOTADA** |
| SQLite como fonte primária | Consulta rápida, transações | Binário opaco para o usuário; contradiz "abrível sem o produto"; dificulta diff e git | **REJEITADA como fonte de verdade** |
| SQLite como **índice derivado** | Consulta rápida; reconstruível | Adiciona dependência e arquivo binário; só se consulta virar gargalo | **DEFERIDA** — permitida só se medição provar necessidade |
| Banco em memória / nenhum índice | Simples | Listagem lenta com milhares de itens | **REJEITADA** para > ~500 itens |

**Regra:** `index.json` é **cache**. Se ele sumir ou discordar do disco, o disco vence e o índice é reconstruído. Nada de "confiar no índice".

### 3.2 Layout no padrão `Lia\` do kit

Seguindo literalmente o padrão de pastas do `KIT-PROJETO-NOVO.zip` (`APP-WINDOWS/PADRAO-DA-MARCA.md` §3, §4), com a divisão por classe:

```
%USERPROFILE%\Lia\                          ← raiz visível da marca
├── LEIA-ME.txt                             ← 10 linhas, sem jargão
├── AgentHub\                               ← D1 + D2 do Hub
│   ├── Biblioteca\                         ← capacidades admitidas
│   │   └── <id>\
│   │       ├── SKILL.md                    ← formato padrão
│   │       ├── scripts\  references\  assets\
│   │       └── .lia\
│   │           ├── capability.json
│   │           ├── provenance.json
│   │           ├── history.json
│   │           └── THIRD_PARTY_NOTICES.md
│   ├── Quarentena\                         ← importado, não admitido (D5 maior, ver §4.4)
│   ├── Exportados\                         ← pacotes que o usuário gerou
│   └── Colecoes\                           ← agrupamentos por usuário (.json legível)
├── Comum\                                  ← compartilhado entre apps da marca
│   ├── Capacidades\                        ← diretório de troca Hub → hosts (§7.2 do doc de arquitetura)
│   ├── Marca\
│   └── Backups\                            ← backups explícitos, com data e tamanho
├── Studio\
├── Forge\
└── Waifu\                                  ← memória de convivência: NUNCA lida pelo Hub

%APPDATA%\Lia\AgentHub\config\               ← D4: pequeno, sobrevive a update
├── preferences.json
└── migrations.json

%LOCALAPPDATA%\Lia\AgentHub\                 ← D5 + D6: descartável / técnico
├── cache\
│   └── index.json                          ← D3 (reconstruível)
└── logs\
    └── audit-YYYY-MM.jsonl                 ← D6

%LOCALAPPDATA%\Programs\Lia\AgentHub\        ← executável e programa
```

**Justificativa por linha, contra o kit:**

| Escolha | Base no kit |
|---|---|
| `%USERPROFILE%\Lia\AgentHub\` e **não** `Documentos\` | Kit §3.3: Documentos é sincronizada com OneDrive por padrão → upload involuntário |
| Cache e logs em `%LOCALAPPDATA%` | Kit §3.2: "regenerável; não pode entrar em backup nem roaming" |
| Config em `%APPDATA%` | Kit §3.2: "pequeno, deve sobreviver a update" |
| Instalação em `%LOCALAPPDATA%\Programs\Lia\` | Kit §2.1 regra 4: por usuário, sem admin |
| `index.json` em cache e não na biblioteca | Separar derivado de fonte de verdade; a biblioteca fica limpa para git/backup |
| `Comum\Capacidades\` | Kit §4.1 já prevê `Comum\`; é a raiz neutra de troca entre apps |

### 3.3 Desvio consciente do kit

O kit propõe que o trabalho do usuário fique em `%USERPROFILE%\Lia\<App>\`. Isso é **adotado**. Mas há **um desvio**:

| Kit | Este documento | Motivo |
|---|---|---|
| Skills do usuário do Studio em `Lia\Studio\Skills\` | Hub usa `Lia\AgentHub\Biblioteca\` | O Hub não é o Studio. Skills do Hub são **biblioteca com proveniência**; Skills do Studio são **do projeto**. Duas coisas, dois lugares — e isso evita que um app sobrescreva o outro |

---

## 4. Operações de escrita — segurança de dados

### 4.1 Escrita atômica (obrigatória em todo arquivo de estado)

```
1. ler estado atual
2. mesclar apenas a própria chave
3. gravar em <arquivo>.tmp-<pid>
4. fsync
5. renomear sobre o original   ← atômico no NTFS e no POSIX
```

**Origem:** `KIT-PROJETO-NOVO.zip` → `APP-WINDOWS/PADRAO-DA-MARCA.md` §5.6 documenta o bug real: *"dois apps escrevendo o mesmo `lia.json`… o Studio lê o arquivo, o usuário atualiza a Waifu no meio, o Studio grava de volta o que tinha lido — e apaga a entrada da Waifu."*

**Aplicação no Hub:** o Hub escreve em `Comum\Capacidades\index.json` e em `%APPDATA%\Lia\AgentHub\config\`. Se algum dia dividir arquivo com outro app, a regra já está pronta.

### 4.2 Download/import em duas fases

Nunca escrever no destino final antes de estar completo:

```
temp\_parcial\<hash>\  →  validação + hash  →  rename para Biblioteca\<id>\
```

**Origem:** kit §4.4.3(b) — *"Baixe em `_parcial\` e só renomeie no fim. Um arquivo no lugar definitivo é, por definição, um arquivo completo."*

**Aplicação:** é a mesma razão pela qual um import cancelado no passo 4 (`SECURITY-AND-TRUST-MODEL.md` §8) não deixa resíduo.

### 4.3 Trava de escrita concorrente

Se dois processos do Hub (duas janelas) escreverem na biblioteca:

- trava por `id` com PID + timestamp;
- trava com mais de 1 h sem progresso é considerada morta e pode ser tomada;
- mensagem ao usuário: *"outra janela do Agent Hub está usando esta capacidade"*.

**Origem:** kit §4.4.3(a), com a regra de expiração incluída.

### 4.4 Quarentena

`Lia\AgentHub\Quarentena\<hash>\` guarda o que foi analisado mas **não admitido**. Regras:

- **Não** entra em `index.json` publicável.
- **Não** é executável (nada é).
- Mostra ao usuário o que é, com botão de **descartar** e tamanho exibido.
- Expiração sugerida: **não automática** — apagar arquivo do usuário sem aviso viola a regra nº 3. Em vez disso, aviso ao abrir o app: *"há 3 itens em quarentena ocupando 12 MB"*.
- **Nota de honestidade:** isso é uma decisão de produto; `D-06` deve confirmar.

---

## 5. Exportação e importação

### 5.1 Exportação — três saídas, todas abertas

| Saída | Formato | Para quem |
|---|---|---|
| **Capacidade individual** | `.lia-capability` (ZIP + `manifest.json`) | Compartilhar com outra pessoa ou outro host |
| **Coleção** | `.lia-collection` (ZIP com N capacidades + índice) | Levar a biblioteca inteira |
| **Biblioteca crua** | Diretório `Biblioteca\` copiado | Quem não quer o Hub: são arquivos |

**Regra dura:** a terceira saída **precisa funcionar sem o Hub**. Se o usuário copiar `Biblioteca\` para um pendrive e abrir num editor de texto, ele vê Markdown e JSON legíveis. É o teste de T3 da arquitetura.

### 5.2 O que a exportação **recusa** fazer

| Situação | Comportamento |
|---|---|
| `license` não revisada (`null`) | **Recusa** exportar, com mensagem explicando qual camada falta |
| Capacidade em `unreviewed` | Exporta, mas `manifest.json` marca `trust: unreviewed` e o nome do arquivo ganha sufixo `-NAO-REVISADO` |
| Capacidade com `scripts/` | Exporta, com aviso explícito e campo `containsScripts: true` no manifest |
| Capacidade que declara `secrets.envVars` | Exporta os **nomes**; nunca os valores |
| Capacidade com `egress.destinations` | Exporta; `manifest.json` inclui a lista, e a interface mostra |

### 5.3 Importação — o que é aceito

| Entrada | Aceito | Observação |
|---|---|---|
| `.lia-capability` | Sim | Fluxo completo de §8 do doc de segurança |
| Diretório com `SKILL.md` | Sim | Formato Agent Skills puro, **sem** `.lia/` → tudo gerado no import, `trust: unreviewed` |
| `.zip` arbitrário com `SKILL.md` na raiz | Sim | Detecção de estrutura |
| `.skill` / pacote de outro cliente | A avaliar | `D-03`; provavelmente sim, pois é o mesmo formato |
| URL remota | **Não no MVP** | Exige rede, consentimento e política de egress. `D-12` |
| Repositório git | **Não no MVP** | Mesmo motivo; seria `git clone` remoto |

### 5.4 Interoperabilidade com o Studio — o caminho mais curto

O Studio já lê `.agents/skills/<id>/SKILL.md`. Portanto:

```
Hub exporta → <id>/SKILL.md + .lia/
                      ↓
        usuário copia para .agents/skills/ do projeto
                      ↓
              Studio já funciona (não sabe do Hub)
```

**Nenhuma alteração no Studio é necessária para o Hub ser útil a ele.** É a consequência prática de T2/T3. Se depois o Studio quiser ler `capability.json` para mostrar `trust` e `license`, é uma melhoria incremental — não um pré-requisito.

---

## 6. Credenciais — ausência por desenho

| Pergunta | Resposta |
|---|---|
| O Hub guarda chave de MCP? | **Não.** |
| Guarda token de provider? | **Não.** |
| Guarda senha de repositório? | **Não.** |
| O que guarda? | O **nome** da variável de ambiente que o host deve fornecer (`secrets.envVars: ["GITHUB_TOKEN"]`) |
| Onde o valor vive? | No host que executa: cofre do SO (Windows Credential Manager), conforme regra do kit §3.1 e prática do Project (`secrets/vault.ts`) |
| O que acontece se a capacidade exigir segredo e o host não tiver? | O host reporta ausência. O Hub não resolve |

**Por que isso é estrutura e não promessa:** não existe campo de valor em nenhum schema proposto. `capability.json` §6.2 tem `secrets: { envVars: [] }` — array de strings. Não há lugar para pôr o segredo.

---

## 7. Backup

| Aspecto | Decisão proposta |
|---|---|
| Backup **automático** do Hub | **Não.** Backup automático em produto local-first cria expectativa falsa e ocupa disco sem o usuário saber |
| Backup **manual** | **Sim**: botão explícito que gera `Lia\Comum\Backups\AgentHub-YYYY-MM-DD-HHMM.zip` com tamanho e conteúdo exibidos antes |
| O que entra no backup | D1 + D2 (biblioteca completa, incluindo `.lia/`) |
| O que **não** entra | Cache, logs, temporários, quarentena (perguntar se o usuário quiser quarentena) |
| Retenção | Do usuário. O Hub **não apaga backup antigo automaticamente** |
| Backup de terceiro (OneDrive/Drive) | Permitido e **avisado**: se `Lia\` estiver dentro de pasta sincronizada, o app avisa uma vez (não a cada abertura) e informa o tamanho |
| Restauração | Restaurar = escolher o `.zip` e o destino; o Hub mostra o que será sobrescrito antes |

**Ponto que evita desastre:** o kit adverte (§4.3) que **o comportamento do OneDrive com junction precisa de teste real** — se o OneDrive seguir a junction, ele sincroniza gigabytes sem o usuário saber. Consequência aqui: **o Hub não cria junction dentro de `%USERPROFILE%\Lia\` nesta fase.** Junction só com teste real e decisão humana.

---

## 8. Portabilidade

### 8.1 Três níveis, do mais forte ao mais fraco

| Nível | O que é | O que funciona |
|---|---|---|
| **P1 — arquivos** | Copiar `Lia\AgentHub\` para outro computador | Biblioteca inteira legível. Hosts que leem arquivo funcionam. **Nada depende do Hub** |
| **P2 — pacote** | Exportar `.lia-capability` e importar no destino | Proveniência, hashes, licença viajam juntos |
| **P3 — coleção** | Exportar `.lia-collection` | Biblioteca inteira com índice |

**Compromisso:** P1 precisa funcionar **sempre**, inclusive se o Hub for abandonado. Um produto que só permite P2/P3 sequestra o dado.

### 8.2 Portabilidade entre sistemas operacionais

| Item | Windows | Linux/macOS | Risco |
|---|---|---|---|
| Caminhos | `%USERPROFILE%`, `%APPDATA%`, `%LOCALAPPDATA%` | `$HOME/Lia/…`, `$XDG_CONFIG_HOME`, `$XDG_DATA_HOME` | Médio — exige um módulo único de caminho (kit §2.1 regra 2) |
| Separador | `\` | `/` | Baixo se todo caminho no **pacote** for POSIX (`/`) |
| Case sensitivity | Insensível | Sensível | **Alto** — `SKILL.md` vs `skill.md` colide no Windows e não no Linux. Ver §8.3 |
| Nomes reservados | `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9` | Permitidos | Médio |
| Teto de caminho | 260 (sem *long path*) | 4096 | Médio |
| Fim de linha | `CRLF` | `LF` | Baixo se o hash for sobre bytes normalizados — **decidir e documentar** |
| Encoding | UTF-8 obrigatório | UTF-8 | Baixo se validado no import |
| Junction / symlink | Suportado, perigoso | Suportado | Alto — ver §5 do doc de segurança |

### 8.3 Regras de portabilidade do pacote

| Regra | Motivo |
|---|---|
| Caminhos dentro do manifest são **sempre POSIX** (`/`) | Um pacote criado no Windows precisa abrir no Linux |
| Comparação de nome de arquivo é feita **case-insensitive** na validação de colisão, **mesmo no Linux** | Garante que o pacote abrirá no Windows. Detecta `README.md` + `readme.md` |
| Nomes reservados do Windows **rejeitados** mesmo no Linux | Um pacote válido no Linux não pode falhar no Windows depois de exportado |
| Texto em **UTF-8**, sem BOM | BOM quebra parser de frontmatter (o `SKILL.md` deve começar com `---` no byte 0) |
| Fim de linha: **normalizar para LF** no payload e registrar a normalização no manifest | Torna `contentHash` estável entre plataformas |
| Nenhum caminho absoluto, nenhum drive, nenhum `\\` | §5 do doc de segurança |
| Comprimento total < 200 caracteres por caminho no payload | Margem para o destino (teto de 260 do Windows + raiz do usuário) |

**Nota de honestidade:** a normalização de CRLF→LF altera bytes. Isso significa que o `contentHash` de um arquivo importado com CRLF **não** será o hash do arquivo original no upstream. A mitigação é registrar **dois** hashes quando relevante: `contentHash.normalized` (o que o Hub guarda) e `contentHash.asReceived`. Decisão de `D-04`, mas precisa estar no schema.

---

## 9. Migração e evolução

| Situação | Regra |
|---|---|
| Mudança de `schemaVersion` do `capability.json` | Migração **explícita**, com backup antes, e relatório do que mudou |
| Mudança de `formatVersion` do pacote | Incremento obrigatório; versão nova pode ler a antiga; antiga **não** lê a nova |
| Campo novo | Opcional, com default documentado; `null` quando não aplicável |
| Campo removido | Nunca remover sem migração; marcar obsoleto primeiro |
| Migração falhou | Restaurar backup; **nunca** deixar estado meio migrado |
| Migração irreversível | Proibida sem confirmação explícita com o que se perde |

**Regra do kit aplicada:** *"Não cair no padrão em silêncio quando o registrado sumiu — pergunte."* Se a biblioteca registrada não existir (drive desconectado, pasta movida), o Hub **pergunta** e oferece procurar pelo marcador, em vez de criar uma biblioteca vazia nova.

### 9.1 Marcador de raiz

Como o kit propõe (`.lia-home`), o Hub verifica a raiz por um marcador em vez de varrer disco:

```
%USERPROFILE%\Lia\.lia-home         ← arquivo vazio, marcador da marca
%USERPROFILE%\Lia\AgentHub\.lia-hub ← marcador do Hub
```

Se o usuário apontar para uma pasta sem marcador: *"esta pasta não parece ser uma biblioteca do Agent Hub. Usar assim mesmo?"* — nunca presumir, nunca varrer o disco.

### 9.2 Desinstalação

| Passo | Regra |
|---|---|
| Remove programa | Sim, sempre |
| Remove config e cache | Sim, com aviso |
| Remove **biblioteca** | **Pergunta**, mostrando caminho e tamanho |
| Remove exports e backups | **Pergunta** separadamente |
| Remove entrada de outros apps | Nunca — o Hub não tem entrada em outros apps |

**Origem:** kit §5.8 item 5 e `GUIA-APP-NOVO.md` §7 ("desinstalar remove o programa e **pergunta** sobre os dados, mostrando o tamanho").

---

## 10. Escala — o que acontece quando cresce

| Volume | Comportamento esperado | Ponto de atenção |
|---|---|---|
| < 100 capacidades | Listar do disco a cada abertura é instantâneo | — |
| 100–1.000 | `index.json` acelera; reconstrução leva < 1 s com leitura de 8 KB por item (padrão do Studio) | Manter leitura de prefixo, não do arquivo inteiro |
| 1.000–10.000 | Índice obrigatório; busca em memória | Considerar SQLite **como índice derivado** (não fonte) |
| > 10.000 | Fora do caso de uso de um produto pessoal | Se chegar aqui, é sinal de que o produto virou outra coisa |

**Regra derivada:** o Hub **não** deve carregar corpo de `SKILL.md` para listar. Essa é a lição do Studio (`_metadata` lê só 8 KB) e do padrão Agent Skills (~100 tokens por Skill no contexto). Vale para a UI também.

---

## 11. Conformidade com as sete regras da marca

Verificação explícita de cada regra do `GUIA-APP-NOVO.md` contra este documento:

| # | Regra | Como este documento cumpre | Lacuna |
|---|---|---|---|
| 1 | Funciona sozinho | Biblioteca é arquivo; nenhuma dependência de Studio/Forge/internet/conta | — |
| 2 | Baixou, abriu, funciona | Instalação por usuário, sem admin; sem Python/Node exigido do usuário (§6 do doc de plataforma) | Depende de `D-14` |
| 3 | Trabalho do usuário é dele | §5.1 P1; §8 P1; §9.2 desinstalação pergunta | — |
| 4 | Não esconde custo nem risco | Export avisa `unreviewed`/`scripts`/`egress`; backup manual com tamanho; sem backup automático silencioso | — |
| 5 | Não mente sobre o que fez | Nenhuma execução ⇒ nada a afirmar; `trust` com evidência; `null` = não medido | — |
| 6 | Neutro de fornecedor | Nenhum provider, modelo ou runtime obrigatório | — |
| 7 | Conexão com a Waifu opcional e revogável | **Não existe conexão.** O Hub nem lê `Lia\Waifu\` | — |

**Regra 7 merece ênfase:** o produto **não** terá ponte com a Waifu na primeira versão. Não porque seja proibido, mas porque não há valor: memória de convivência não é capacidade, e o Hub não deve tocar nela.

---

## 12. Decisões embutidas que precisam de aval

| # | Decisão embutida | Alternativa | ID |
|---|---|---|---|
| 1 | Arquivos + índice derivado, sem SQLite como fonte | SQLite primário | `D-06` |
| 2 | Biblioteca em `Lia\AgentHub\`, separada de `Lia\Studio\Skills\` | Biblioteca única da marca | `D-06` |
| 3 | Sem backup automático | Backup automático diário | `D-06` |
| 4 | Quarentena sem expiração automática | Expirar em 30 dias | `D-06` |
| 5 | Normalização CRLF→LF com dois hashes | Preservar bytes originais | `D-04` |
| 6 | Sem importação por URL/git no MVP | Importar remoto desde o início | `D-12` |
| 7 | Sem junction dentro de `Lia\` nesta fase | Adotar junction do kit | `D-05` |

---

## 13. Conclusões

1. **Arquivo é a escolha certa e é a escolha que o ecossistema já validou**: Forge usa workspace visível, Project usa wiki Markdown com índice derivado. O Hub segue o mesmo padrão.
2. **O padrão `Lia\` do kit é adotado integralmente**, com um desvio justificado: a biblioteca do Hub é separada das Skills do Studio.
3. **Segredo não tem lugar no schema.** Não é uma política — é uma ausência de campo.
4. **P1 (copiar a pasta) é o compromisso de portabilidade.** Se o Hub sumir, o usuário continua com Markdown e JSON legíveis.
5. **Portabilidade entre SO exige regras no formato do pacote**, não na implementação. Case-insensitivity, nomes reservados do Windows e normalização de fim de linha precisam ser **do formato**, senão um pacote "válido" falha depois de exportado.
6. **Sete decisões de armazenamento precisam de aval humano** e estão mapeadas em `D-06`/`D-04`/`D-12`/`D-05`.

---

## Referências

- `KIT-PROJETO-NOVO.zip` → `APP-WINDOWS/PADRAO-DA-MARCA.md` §2.1, §3.2, §3.3, §4.1, §4.3, §4.4.3, §5.5–§5.8; `APP-WINDOWS/GUIA-APP-NOVO.md` §2.1, §4, §7; `APP-WINDOWS/GLOSSARIO.md`
- `KIT-PROJETO-NOVO.zip` → `APP-MOBILE-OU-WEB/PADRAO-MOBILE-WEB.md` §3.3 ("exportar é obrigatório, não é extra")
- `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §6–§8 — modelo de dados e formato de pacote
- `docs/architecture/SECURITY-AND-TRUST-MODEL.md` §5 — contenção de caminho; §10 — auditoria
- `BloomRX/Lia-Forge@arena/649f88bd-3dspritesheet`, `docs/lia-ecosystem-integration.md` — caminhos `LIA_HOME`, `SPRITEFORGE_PROJECT_ROOT`, `%LOCALAPPDATA%\Lia\Modelos`
- `BloomRX/Lia-Studio@arena/01a0f4ab-lia-gamedev`, `app/lia/skills.py` — leitura de prefixo de 8 KB para catálogo; rejeição de symlink
- `BloomRX/Lia-Project@arena/01a10290-lia-project`, `docs/research/lia-capability-catalog/03-ESQUEMA-E-DADOS.md` — wiki/índice derivado, estados de ciclo de vida
