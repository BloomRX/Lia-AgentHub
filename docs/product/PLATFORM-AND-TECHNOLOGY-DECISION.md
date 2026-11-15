# Plataforma e stack inicial

**Documento:** `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Branch:** `arena/a92004be-lia-agenthub`
**Status:** `PROPOSED` — recomendação para decisão humana (`D-14`, `D-17`, `D-27`). **Não autoriza implementação.**
**Data:** 2026-11-15 (UTC)

---

## 1. O que precisa ser decidido

| ID | Pergunta | Este documento recomenda |
|---|---|---|
| `D-14` | Tecnologia da aplicação (Electron, web local ou outra) | **Seção 5** |
| `D-17` | **Sistemas operacionais** do primeiro MVP | **Seção 6** |
| `D-27` | **Biblioteca de interface** (`pywebview`, navegador do sistema ou opção híbrida) | **Seção 5.5.4** |
| — | O Hub deve ser mobile? | **Não** (Seção 4.3) |
| — | O Hub deve ter API local? | **Não no MVP** (Seção 7) |

---

## 2. Critérios — definidos **antes** de olhar as opções

Para não escolher por preferência, os critérios e seus pesos são fixados primeiro:

| # | Critério | Peso | Como se mede |
|---|---|---:|---|
| K1 | **"Baixou, abriu, funciona" sem Python/Node/console** (regra nº 2) | **25 %** | Usuário leigo instala e usa sem erro de dependência |
| K2 | **Domínio puro separado da interface** (não prender regra à UI) | **20 %** | Testável sem SO, sem rede, sem framework |
| K3 | **Custo de manutenção** num produto de escopo largo | 15 % | Nº de runtimes, lockfiles, toolchains por release |
| K4 | **Capacidade de editar texto e mostrar diff** (é um editor de Markdown/JSON) | 12 % | Editor, diff, árvore de arquivos, busca |
| K5 | **Tamanho e tempo de instalação** | 8 % | MB do instalador; segundos até a primeira tela |
| K6 | **Coerência com o ecossistema** (sem copiar cegamente) | 8 % | Reuso de padrões e conhecimento já pago |
| K7 | **Custo de validação real no Windows** (quem testa é o Dev) | 7 % | Quantas metades "na máquina" cada release exige |
| K8 | **Facilidade de embutir binário auxiliar** (hash, zip, eventuais ferramentas) | 5 % | Cross-compile, PATH, antivírus |

**Regra de leitura:** K1+K2 = **45 %**. Um candidato que falhe em qualquer um dos dois **não pode vencer**, independentemente dos outros.

---

## 3. Inventário do ecossistema (evidência, não preferência)

Antes de comparar opções, o que os produtos Lia já usam — e o resultado real de cada escolha:

| Produto | Stack real | Evidência | Resultado observado |
|---|---|---|---|
| **Lia Studio** | Python 3.9+ declarado no `README` dele — **já em EOL**; núcleo **stdlib apenas** (`app/lia/`) + SPA estática (`app/static/`) servida localmente + `desktop.py` opcional com WebView2 | `arena/01a0f4ab-lia-gamedev`, `README.md`, `app/lia/*.py` | Núcleo auditável e sem dependência; a Alpha roda com `python run.py`. **Mas:** usuário final ainda precisa de Python (o `.exe` não foi validado) |
| **Lia Forge** | Electron + React/Vite (`electron/`, `src/`) + launcher Python de desenvolvimento + MCP server Node | `arena/649f88bd-3dspritesheet`, `package.json` | App completo, packaging NSIS configurado; **nenhum `.exe` produzido ou assinado**; `postinstall: install-electron` baixa runtime |
| **Lia Project (Waifu)** | Electron + TypeScript (`lia/`, `airi/`) | `main` e branches; ~366 MB | Produto mais maduro em volume; custo estrutural conhecido: **segundo Electron completo** para o Stage (registrado no próprio repo) |
| **Lia-Go** | Capacitor + web, monorepo com `packages/domain` separado, `engines.node >= 22.12.0` | citado em `KIT-PROJETO-NOVO.zip` → `APP-MOBILE-OU-WEB/PADRAO-MOBILE-WEB.md` §1 | Molde do padrão mobile/web do kit |

**Três observações que orientam a decisão:**

1. **A stack mais bem-sucedida em honestidade técnica é o Studio**, e ela é Python stdlib + SPA. O núcleo é testável sem I/O.
2. **A stack mais completa em experiência é o Forge/Project (Electron)** — ao custo de dois runtimes (Node + Python de desenvolvimento) e de um instalador grande.
3. **A regra do kit é em camadas, não "Electron ou nada":** núcleo sem dependência de terceiro; shell, adaptadores e build podem usar dependência fixada; **usuário final nunca instala nada**.

---

## 4. Opções de plataforma

### 4.1 Desktop nativo empacotado (Windows `.exe`) — via Python + WebView2

**Desenho:** núcleo Python stdlib (padrão Studio) + interface web local servida pelo próprio processo + janela WebView2 (`pywebview` ou `desktop.py`-like) + empacotamento PyInstaller.

| Critério | Avaliação | Peso | Nota |
|---|---|---:|---:|
| K1 sem runtime para o usuário | Empacotado entrega tudo; WebView2 já vem no Windows 10/11 | 25 % | **9/10** — ressalva: WebView2 ausente em Windows antigo exige pré-checagem (o Studio já faz) |
| K2 domínio puro | Python sem framework, funções puras — **já provado no Studio** | 20 % | **10/10** |
| K3 manutenção | **Um** runtime (Python) + PyInstaller; sem `node_modules` | 15 % | **9/10** |
| K4 editor/diff | Editor é web (qualquer lib), servido local | 12 % | **8/10** |
| K5 tamanho/instalação | ~25–60 MB típico com PyInstaller | 8 % | **7/10** |
| K6 coerência com ecossistema | **Alta** — padrões já pagos no Studio e no kit Windows | 8 % | **9/10** |
| K7 validação Windows | Uma metade: gerar `.exe` e abrir | 7 % | **8/10** |
| K8 binário auxiliar | Python puro resolve hash/zip; binário externo é possível | 5 % | **7/10** |

**Riscos:** PyInstaller e antivírus (falso positivo é comum em binário Python recém-gerado); WebView2 é dependência do sistema (mas redistribuível); `sys._MEIPASS`/`sys.frozen` exige centralizar caminho (**o kit já exige isso**).

### 4.2 Desktop nativo empacotado — via Electron + Node

| Critério | Avaliação | Peso | Nota |
|---|---|---:|---:|
| K1 | Instalador NSIS entrega tudo | 25 % | **8/10** — mas `postinstall` baixa runtime; instalador grande |
| K2 domínio puro | Possível (`packages/domain`, padrão Lia-Go), **mas** a tentação de importar Electron no domínio é alta — o Project tem 70 arquivos não-teste importando Electron | 20 % | **7/10** na prática |
| K3 manutenção | Node + npm + electron-builder + possivelmente Python de dev | 15 % | **5/10** |
| K4 | Excelente | 12 % | **10/10** |
| K5 | 150–250 MB típico | 8 % | **4/10** |
| K6 | Alta (Forge e Project usam) | 8 % | **8/10** |
| K7 | Build e assinatura no Windows; `npm ci` obrigatório | 7 % | **6/10** |
| K8 | `child_process` nativo, fácil | 5 % | **9/10** |

**Riscos:** três ou quatro runtimes na cadeia de release; `npm ci` em cada build; auditoria de dependências transitivas (o Forge tem 47 arquivos em `tests/` (41 smoke) e um `package-lock` grande); o Project documenta que o segundo Electron é problema estrutural.

### 4.3 Web / mobile

| Critério | Avaliação | Motivo |
|---|---|---|
| K1 | **Falha** | Web exige servidor; mobile exige loja, conta de desenvolvedor e iOS exige macOS |
| K3 | Falha | Navegador não tem acesso a sistema de arquivos arbitrário — **e o Hub é sobre arquivos** |
| K8 | Falha | Não há como rodar binário auxiliar local confiável |
| Regra nº 3 da marca | **Falha** | No celular não existe pasta que o usuário copia; o kit exige exportação obrigatória para compensar. Para o Hub, isso significaria exportar a biblioteca pela interface — pior experiência que abrir a pasta |

**Veredito: `REJECTED` para o Hub.** Motivo específico: **o produto é um editor de arquivos com validador.** Um ambiente sem sistema de arquivos real é o ambiente errado. Não é incapacidade técnica — é incompatibilidade de natureza.

### 4.4 CLI primeiro (sem interface)

| Critério | Avaliação |
|---|---|
| K1 | **Alcança** — um `.exe` único, zero dependência |
| K2 | **Ótima** — domínio puro é natural |
| K4 | **Falha parcial** | Editar `SKILL.md` no terminal é hostil para o público da marca |
| K7 | Ótima |
| Valor sozinho | **Real**: validar, empacotar e exportar não precisa de janela |

**Veredito: `ACCEPTED` como fase 1 técnica, não como produto final.** Ver §5.3.

### 4.5 Scripts + arquivos, sem aplicação (a alternativa mais barata)

A visão de produto admite (§14): *"Se a pesquisa mostrar que um aplicativo independente seria prematuro, a alternativa deve ser manter a biblioteca e os contratos como componentes independentes, adiando a interface própria."*

| Critério | Avaliação |
|---|---|
| K1 | Falha para o usuário leigo (exige terminal) |
| K2 | Perfeita |
| Custo | Mínimo |
| Valor | **Médio** — resolve L-01/L-03/L-07 para quem já é técnico |

**Veredito: `DEFERRED`.** É o fallback se `D-13` rejeitar o MVP de aplicativo. Não recomendo como escolha principal porque o produto precisa ser usável por quem não usa terminal — é a razão de existir da marca.

---

## 5. Recomendação

### 5.1 Veredito

> **Plataforma: aplicativo desktop Windows, instalador por usuário, sem admin.**
> **Núcleo: Python 3.11+ biblioteca padrão apenas** (corrigido na Fase 0.1 — ver `§5.5`).
> **Interface: web local (HTML/CSS/JS) servida pelo próprio processo em `127.0.0.1`; janela por navegador do sistema no MVP, `pywebview` como opção.**
> **Empacotamento: PyInstaller, instalador por usuário em `%LOCALAPPDATA%\Programs\Lia\AgentHub`.**
> **Distribuição: `run.py` do repositório e `.exe` empacotado produzem o mesmo comportamento e as mesmas pastas.**

### 5.2 Por que esta combinação

1. **K1+K2 = 45 %, e é aqui que a combinação ganha.** Núcleo stdlib é o único desenho que dá domínio puro **de verdade** (não por disciplina) e que já foi provado no ecossistema (`permissions.py`, `tool_registry.py`, `skills.py` — funções puras, `type(x) is`, sem I/O).
2. **Um runtime, não quatro.** O release do Hub precisa de: Python + PyInstaller. O do Electron precisa de Node + npm + electron-builder + lockfile auditado + download do runtime Electron.
3. **O produto é um editor de texto e arquivos.** A interface não precisa de nada que só o Electron oferece (sem GPU, sem WebGL, sem áudio, sem render). WebView2 serve, e é o que o Studio já usa.
4. **Coerência sem cópia cega.** Adota-se o **padrão de camadas** do Studio (núcleo stdlib + shell + build) e o **padrão de pastas** do kit. **Não** se copia a SPA específica dele, nem sua estrutura de projetos.
5. **Honestidade sobre validação.** PyInstaller tem falso positivo de antivírus e é um risco conhecido; está declarado em §8, não escondido.

### 5.3 Desenho de fases que reduz risco

| Fase | Entrega | Precisa de UI? | Valida o quê |
|---|---|---|---|
| **F1a** | Núcleo de domínio + CLI de desenvolvimento (`python run.py validate`, `pack`, `export`) | Não | Que o domínio é puro e que o formato funciona |
| **F1b** | Interface web local, aberta pelo navegador | Não (navegador) | Que a experiência é utilizável |
| **F1c** | Janela WebView2 + `.exe` | Sim | Que "baixou, abriu, funciona" |

Isso permite **entregar valor antes de resolver empacotamento** e permite que o Dev valide no Windows em etapas, em vez de num salto grande. É a divisão do kit (§3.1: "toda tarefa de setup se parte em duas") aplicada ao roadmap.

### 5.4 O que a stack **rejeita** deliberadamente

| Rejeitado | Por quê |
|---|---|
| Framework web de front-end obrigatório (React/Vue) no MVP | Adiciona build step e Node ao release sem ganho proporcional num editor de textos e listas. Pode entrar depois **se** a UI exigir |
| ORM / banco | O dado é arquivo |
| TypeScript no núcleo | O núcleo não é a interface |
| Electron | Custo de runtime desproporcional ao tipo de app |
| Tauri/Rust | Excelente, mas traz um segundo toolchain (Rust) a um produto que já precisa de build Windows — sem ganho que justifique |
| Docker/WSL como requisito | O produto precisa rodar no Windows nativo do usuário leigo |

**Nota sobre Tauri:** é tecnicamente atraente (binário pequeno, WebView do sistema). Não recomendo **nesta fase** por K3/K7: exigiria Rust + Node na cadeia de release e ninguém no ecossistema tem essa cadeia validada. Fica como opção de reavaliação se o `.exe` Python se mostrar problemático em distribuição.

### 5.5 Versão do Python — correção da Fase 0.1

> **A Fase 0 recomendou "Python 3.9+". Isso estava errado: 3.9 e 3.10 estão em end-of-life.**
> Correção verificada em `https://devguide.python.org/versions/` em 2026-11-15.

#### 5.5.1 Status oficial das linhas

| Branch | Status | End of life | Situação |
|---|---|---|---|
| 3.15 | bugfix | 2031-10 | Suportada |
| 3.14 | bugfix | 2030-10 | Suportada |
| 3.13 | security | 2029-10 | Suportada |
| 3.12 | security | 2028-10 | Suportada |
| **3.11** | **security** | **2027-10** | **Suportada — é o piso** |
| **3.10** | **end-of-life** | **2026-10-01** | **Sem correções, de nenhum tipo** |
| **3.9** | **end-of-life** | **2025-10-31** | **Sem correções, de nenhum tipo** |

`end-of-life` não significa "antiga": significa que **nenhuma vulnerabilidade encontrada a partir
daquela data será corrigida**. Recomendar 3.9 como piso é recomendar que o produto nasça sem
capacidade de receber patch de segurança do runtime.

#### 5.5.2 Decisão corrigida

| Item | Valor | Justificativa |
|---|---|---|
| **Piso do núcleo** | **Python 3.11** | Linha suportada mais antiga (EOL 2027-10). Maximiza quantas máquinas de desenvolvimento rodam sem instalar nada, dentro do conjunto que recebe patch |
| **Alvo do bundle `.exe`** | **Python 3.13.x** | Primeira linha com 2 anos de bugfix (PEP 719); EOL 2029-10; suportada pelo PyInstaller 6.22.3 |
| **Matriz de CI** | 3.11 e 3.13 | 3.11 prova o piso, 3.13 prova o alvo |
| **Não usar** | 3.9, 3.10 | EOL |

Se o usuário preferir **3.12** como alvo, nada na arquitetura muda — 3.12 tem EOL 2028-10 e
passa em todos os critérios. É variação legítima de `D-14`, não uma consequência técnica.

#### 5.5.3 Metadados verificados dos componentes (PyPI, 2026-11-15)

| Pacote | Versão | `requires_python` | Licença |
|---|---|---|---|
| `pyinstaller` | 6.22.3 | `<3.16,>=3.8` | GPLv2-or-later **+ exceção** para empacotar software proprietário |
| `pywebview` | 6.2.1 | `>=3.8` | BSD 3-Clause |
| `pythonnet` | 3.2.1 | **`<3.16,>=3.11`** | **não declarada no metadado** |
| `electron` (npm) | 45.3.2 | Node **≥ 22.12.0** | MIT |
| `@tauri-apps/cli` (npm) | 2.12.4 | — | Apache-2.0 OR MIT |

**A descoberta que força a correção:** `pywebview` declara `pythonnet; sys_platform == "win32"`
como dependência **incondicional** no Windows, e `pythonnet` 3.2.x exige **Python ≥ 3.11**. A
recomendação original ("Python 3.9+" **e** "considerar `pywebview` para a interface") não podia
ser satisfeita: uma instalação em 3.9 resolveria para um `pythonnet` antigo (≤3.0.5) ou falharia.

Isso é registrado como achado **I-03** da revisão de consistência.

#### 5.5.4 Interface — três opções, com custo medido

A Fase 0 dizia "janela WebView2" como se fosse uma coisa só. Não é.

| Opção | Dependências | Peso no instalador | Fallback se WebView2 ausente | Veredito |
|---|---|---|---|---|
| **A — Navegador do sistema** (`webbrowser.open`) | **Nenhuma** | **0** | É o navegador, por definição | **Recomendada para o MVP (F1b)** |
| **B — `pywebview`** | `pythonnet`, `bottle`, `proxy_tools`, `typing_extensions` | +~10–20 MB estimado | Janela própria; sem navegador de fallback | Viável; adia o ganho estético, cobra dependência CLR |
| **C — `pywebview` atrás de `EXTRA` opcional** | Só se instalado | 0 se ausente | Navegador | **Evolução natural de A** |

**Por que A no MVP:** o argumento central do desenho é "núcleo stdlib, sem dependência". Adicionar
uma ponte CLR (`.NET`) a um produto cujo valor é ser auditável e portátil troca o ativo mais
valioso por uma moldura de janela. Em F1b o objetivo é **provar o domínio**, não a estética.

**Por que B não está rejeitada:** se a experiência de "aba do navegador" se mostrar inaceitável
em teste com usuário real, B passa a valer o custo. A decisão é `D-27`.

#### 5.5.5 WebView2 pode estar ausente — e o que fazer

Evidência (documentação Microsoft, obtida por extração de busca — **não lida por HTTP direto**):

- Evergreen **pré-instalado no Windows 11**.
- Instalado "em todos os dispositivos elegíveis" do Windows 10 — **não em todos**: instalações
  limpas antigas, **LTSC**, **Windows Server** e máquinas gerenciadas podem não ter.
- A Microsoft recomenda distribuir o runtime mesmo no modo Evergreen, "to cover edge cases".
- Detecção documentada: valor de registro `pv` em `HKLM` (per-machine) ou `HKCU` (per-user);
  ao menos um deve existir com versão > `0.0.0.0`.
- Bootstrapper Evergreen: ~2 MB, aceita `/silent /install`.

| Situação | Comportamento do Hub |
|---|---|
| Runtime presente | UI normal |
| Ausente, **online** | Abre no navegador do sistema e oferece **link** para a página oficial da Microsoft — **nunca** download silencioso |
| Ausente, **offline** | Abre no navegador do sistema e instrui a usar o instalador offline da Microsoft |
| Presente mas quebrado | Abre no navegador do sistema, com diagnóstico |

**Consequência arquitetural:** como a UI é **web servida em `127.0.0.1`**, a ausência do WebView2
**não inutiliza o produto**. Essa é a razão técnica de a UI ser web local: o fallback é gratuito.

#### 5.5.6 Bind local e proteção de origem — quatro controles obrigatórios

Nenhum é automático. Todos precisam estar no código desde a primeira linha de F1b.

| Risco | Controle |
|---|---|
| Outra máquina acessa a UI | Bind **exclusivo** em `127.0.0.1` — **nunca** `0.0.0.0` |
| Outro processo local acessa a UI | **Token de sessão** gerado no start, exigido em toda requisição |
| Página web externa faz requisição à UI (CSRF / DNS rebinding) | `Origin` e `Host` validados contra `127.0.0.1:<porta>`; rejeitar `null` e origem externa; **sem** CORS permissivo |
| Colisão de porta | Porta efêmera + URL real injetada na janela |

**Distinção que a Fase 0 não explicitava:**

| | Interface local | API de integração |
|---|---|---|
| Para quem | O usuário, na tela | Outros programas |
| Transporte | HTTP em `127.0.0.1:<porta efêmera>` | **Nenhum no MVP** — arquivo em disco |
| Estabilidade | Pode mudar entre versões | Seria contrato versionado |
| **No MVP?** | **Sim (F1b)** | **Não** |

O contrato de integração do MVP continua sendo **arquivo**, não HTTP.

#### 5.5.7 Comparação revalidada com dados verificados

Critérios K1–K8 mantidos (K1 + K2 = 45 %, ambos veto).

| | **A: Python stdlib + web local** | **B: Electron** | **C: Tauri 2** |
|---|---|---|---|
| Runtime exigido do usuário | **Nenhum** | Chromium ~150–200 MB **por app** | WebView2 (nativo no W11) |
| Runtime de build | Python + PyInstaller | Node **≥ 22.12** | Rust + Node |
| Licença da ferramenta | GPLv2 **+ exceção** | MIT | Apache-2.0 OR MIT |
| Núcleo independente de framework | **Sim, por desenho** | Não — main process é Node | Não — core é Rust |
| Fallback se a UI faltar | **Navegador** | Nenhum | Teria que ser construído |
| Instalador estimado | ~15–30 MB | ~80–150 MB | ~5–10 MB |
| Custo de contribuição | Baixo (Python) | Médio (Node) | **Alto (Rust)** |

**Conclusão revalidada: A continua recomendada — e com margem maior que na Fase 0**, porque a
estratégia de fallback (5.5.5) transforma a fragilidade do WebView2 em degradação controlada, e
porque B/C pagam exatamente o custo que K1 proíbe.

---

## 6. Matriz de sistemas operacionais

| SO | MVP | Justificativa |
|---|---|---|
| **Windows 10/11 x64** | **Sim, obrigatório** | Alvo do kit; máquina do Dev; público da marca |
| **Linux x64** | **Sim, secundário** | O ambiente de desenvolvimento das sessões é Linux; o build precisa rodar lá. Baixo custo adicional em Python puro |
| **macOS** | **Não no MVP** | Sem máquina de validação; exige assinatura e notarização; nada no público-alvo atual pede isso |
| **Windows ARM** | Não | Sem hardware de teste |
| **Mobile** | **Não** | §4.3 |
| **WSL2** | Suporte **acidental**, não declarado | Se rodar, ótimo; não é promessa |

**Regra de honestidade (kit §6):** o produto **não** pode afirmar suporte a plataforma que não foi executada naquela plataforma. O README declara: *"escrito para Windows, validado em <commit>; Linux verificado em CI; macOS não suportado nesta versão."*

---

## 7. API local — recomendação

| Aspecto | Recomendação |
|---|---|
| API local no MVP | **Não** |
| Mecanismo de integração no MVP | **Arquivos** (diretório `Comum\Capacidades\` + `.lia-capability`) |
| Quando reconsiderar | Quando um host real precisar de consulta que arquivo não resolve — ex.: listar com filtro sem varrer o disco, ou receber notificação de nova versão |
| Se vier | Loopback `127.0.0.1` apenas, porta efêmera, token de sessão em arquivo `owner-only`, bind explícito, `Origin` verificado |

**Fundamento:** a §7.1 de `PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` compara as duas opções; arquivo ganha em T2/T3 (funciona com o Hub desinstalado, inspecionável por humano). Uma API local é superfície de rede em um app que edita arquivos.

**Ressalva técnica importante:** se algum dia houver API local **e** interface web servida localmente, ela precisa de proteção contra CSRF e contra acesso de outra origem. Isso é `PROPOSED` e exige revisão de segurança dedicada — **não implementar por analogia**.

---

## 8. Riscos da stack recomendada

| # | Risco | Severidade | Mitigação |
|---|---|---|---|
| S-01 | **Falso positivo de antivírus** em `.exe` PyInstaller | **Alta** | Build reproduzível, sem UPX, assinatura de código quando houver orçamento, versão do PyInstaller fixada, testar em máquina limpa antes de publicar |
| S-02 | **WebView2 ausente** em Windows antigo | Média | Pré-checagem com mensagem clara (o Studio já faz); nunca falhar em silêncio |
| S-03 | **Path relativo vs. empacotado** (`sys.frozen`/`sys._MEIPASS`) | **Alta** | Um único módulo resolve caminho (kit §2.1 regra 2); nenhum outro módulo monta caminho |
| S-04 | **`.exe` e repositório com comportamento diferente** | Alta | Pastas de dados idênticas nos dois modos (kit §2.1 regra 3); `--diagnostico` imprime cada caminho e a fonte |
| S-05 | Núcleo "puro" virar impuro sob pressão | Média | Teste de camadas que falha se L3 importar I/O (o Studio tem `test_dependency_layers.py`) |
| S-06 | Interface web local exposta em rede | Média | Bind `127.0.0.1` apenas; nunca `0.0.0.0`; porta efêmera |
| S-07 | **Piso de Python em fim de vida** (risco originalmente subestimado como "Baixa") | **Média** | Piso **3.11** e alvo **3.13** — ambos recebem patch hoje (`§5.5`). O Studio declara 3.9+, que está em EOL desde 2025-10-31; **não copiar esse piso** |
| S-08 | Migração futura de stack custa caro | Média | Domínio puro é o que torna a troca de UI barata — o risco é aceitável **porque** a arquitetura o reduz |

---

## 9. O que esta decisão **não** decide

Para não transformar recomendação em aprovação:

| Não decidido aqui | Onde |
|---|---|
| Nome final do produto | `D-01` |
| Se haverá interface gráfica no MVP ou só CLI | `D-13` |
| Se o app será distribuído como open source ou produto | `D-16` |
| Biblioteca de editor de Markdown, se houver | Fase de implementação |
| Assinatura de código / certificado | Requer orçamento — decisão humana |
| Política de publicação de release | `BRANCH-AND-RELEASE-FLOW.md` |

---

## 10. Conclusões

1. **A recomendação é desktop Windows empacotado, núcleo Python stdlib, UI web local, WebView2, PyInstaller.** É a única combinação que satisfaz simultaneamente os dois critérios de 45 % (K1 e K2) e já tem precedente validado dentro do ecossistema.
2. **Electron é viável e não é recomendado** para este produto: o custo de runtime não se paga num app que edita texto e arquivos. Está registrado com nota por critério, não como opinião.
3. **Web e mobile são rejeitados por natureza do produto**, não por incapacidade: o Hub depende de sistema de arquivos real e de pastas que o usuário copia.
4. **CLI primeiro é a estratégia de menor risco** e permite entregar valor antes de resolver empacotamento.
5. **Um runtime, um módulo de caminho, pastas idênticas em `.exe` e fonte** — três regras que evitam os três bugs clássicos, todas herdadas do kit.
6. **Os oito riscos estão declarados.** O mais sério (antivírus) não tem solução gratuita; tem mitigação e teste em máquina limpa.

---

## Referências

- `KIT-PROJETO-NOVO.zip` → `LEIA-ME.md`; `APP-WINDOWS/{GUIA-APP-NOVO,PADRAO-DA-MARCA,GLOSSARIO}.md` §1–§3, §6, §7; `APP-MOBILE-OU-WEB/{PADRAO-MOBILE-WEB,GLOSSARIO}.md`
- `docs/research/REPOSITORY-AND-BRANCH-AUDIT.md` §1, §2, §3 — stacks reais por repositório e branch
- `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §5 — camadas e regra de dependência
- `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` §3 — layout de pastas adotado
- `docs/product/MVP-AND-ROADMAP.md` — fases F1a/F1b/F1c
- `docs/DECISION-REGISTER.md` — `D-13`, `D-14`, `D-17` (sistemas operacionais), `D-27` (biblioteca de interface)
- Evidência de código: `BloomRX/Lia-Studio@arena/01a0f4ab-lia-gamedev` (`README.md`, `app/lia/*.py`, `desktop.py`); `BloomRX/Lia-Forge@arena/649f88bd-3dspritesheet` (`package.json`, `README.md`); `BloomRX/Lia-Project@arena/01a10290-lia-project` (volume de código, auditoria de runtime Electron)
