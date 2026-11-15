# Auditoria de licença, direitos de uso e proveniência de Skills

**Documento:** `docs/research/SKILL-LICENSE-AND-PROVENANCE-AUDIT.md` (Missões 3 e 6)
**Agente:** Research — Lia Agent Hub · **Branch:** `arena/db625478-lia-agenthub`
**Data das consultas:** 2026-11-15 (UTC)
**Natureza:** `RESEARCH` documental. **Não é parecer jurídico.** Nenhum contrato foi aceito, nenhuma licença foi recebida, nenhum conteúdo foi copiado ou redistribuído, nada foi executado.

---

## 1. Método, classes e regras aplicadas

### 1.1 Classes de aproveitamento

| Classe | Teste aplicado nesta auditoria |
|---|---|
| **`USE_AS_IS`** | licença identificada em arquivo próprio, permissiva, obrigações compatíveis com catálogo/distribuição Lia, e nenhuma modificação necessária. Podemos usar e catalogar respeitando o aviso |
| **`ADAPT_ALLOWED`** | licença permite derivação mediante condições (atribuição, preservação de aviso, às vezes mesmo licenciamento). Adaptação é possível **cumprindo** as condições |
| **`FORK_CANDIDATE`** | há fundamento técnico/manutenção para manter fork próprio, preservando avisos, atribuição e obrigações. Exige motivo explícito — divergência de escopo, ritmo de upstream ou necessidade de patch local duradouro |
| **`INDEPENDENT_REIMPLEMENTATION`** | a **ideia, formato ou comportamento público** pode ser reimplementado de forma independente em código Lia, sem copiar material protegido (texto, código, arte). Regra: registrar a referência e o processo de criação independente |
| **`RESEARCH_ONLY`** | útil para estudo, mas falta licença, falta clareza, falta autorização, ou o destino não é o Hub. Nenhuma cópia |
| **`BLOCKED`** | licença incompatível (copyleft de rede, NC, ND), ausência de licença, ou impedimento relevante. Não copiar, não adaptar, não redistribuir |

### 1.2 Regras que foram aplicadas sem exceção

1. **Ausência de `LICENSE` não significa licença permissiva.** Repositório público não é autorização: sem licença, todos os direitos permanecem reservados ao autor.
2. **Não inferir permissão de uso a partir de visibilidade pública** nem de contagem de estrelas.
3. **Licença de código ≠ licença de conteúdo, documentação, datasets, pesos ou marca.** Cada camada foi separada.
4. **Dependências com licença diferente não foram ignoradas** — quando identificadas, aparecem no registro.
5. **Nenhum crédito, aviso ou atribuição foi removido** em qualquer operação desta pesquisa (nenhuma cópia foi feita).
6. **Ambiguidade vira pendência humana**, nunca decisão do agente.
7. **Nenhuma recomendação de distribuição comercial** foi feita sem verificar as condições pertinentes.

### 1.3 Fontes de evidência

Metadados e conteúdo via GitHub REST/Trees/Contents/Commits API em 2026-11-15; texto primário da especificação Agent Skills em `agentskills.io/specification`; arquivos `LICENSE`/`THIRD_PARTY_NOTICES.md`/`UPSTREAM.md` lidos remotamente; repositórios Lia inspecionados por tarball/clone esparso somente leitura (commits no inventário, §3).

---

## 2. Grupo A — terceiros **já consumidos** pelo ecossistema Lia

Estes cinco itens já estão dentro de repositórios Lia. A auditoria verifica se as obrigações foram cumpridas e o que falta.

### A-1 · Donchitos/Claude-Code-Game-Studios → 7 skills do Lia Studio

| Campo | Valor |
|---|---|
| Fonte | <https://github.com/Donchitos/Claude-Code-Game-Studios> |
| Autor/mantenedor | `Donchitos` (titular declarado: "Copyright (c) 2026 Donchitos") |
| Licença identificada | **MIT** |
| Arquivo de licença | raiz do upstream; cópia integral preservada pelo Studio em `Lia-Studio@203b60f:docs/licenses/CLAUDE-CODE-GAME-STUDIOS-MIT.txt`; referência no `THIRD_PARTY_NOTICES.md` |
| Versão/commit analisado | `05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418` (**verificado: existe**, 2026-10-19, "Release 1.2.0 — the main path, rebuilt and tested"); HEAD atual tem 78 skills e **as 7 adaptadas continuam presentes** |
| Obrigações de atribuição | manter o aviso de copyright e a permissão MIT nas cópias/derivações |
| Obrigações de redistribuição | incluir o texto da licença; "AS IS", sem garantia |
| Obrigações de código-fonte | nenhuma (não copyleft) |
| Restrições comerciais | nenhuma pela MIT; a **marca** do upstream não é licenciada |
| Cumprimento observado no Studio | **parcialmente adequado**: 12 skills adaptadas têm seção `## Origem` com link ao arquivo exato no commit; os textos MIT estão em `docs/licenses/`. **Porém os avisos ficam na raiz do repositório, fora do payload da skill** — se uma skill for exportada sozinha pelo Hub, o aviso **não viaja** com ela |
| Compatibilidade com distribuição pelo Hub | compatível **se** o pacote exportado incluir `NOTICE`/`THIRD_PARTY_NOTICES.md` (o formato `.lia-capability` já prevê esses arquivos) |
| Conclusão | **`ADAPT_ALLOWED`** — uso atual legítimo; exige correção de empacotamento (ver §7.4) |
| Confiança | **Alta** (licença lida, commit verificado, atribuição presente) |
| Pendências | (a) garantir aviso dentro do pacote exportado; (b) registrar que `skill-improve`, `skill-test`, `asset-audit`, `asset-spec`, `regression-suite`, `security-audit` e outras 65 skills do mesmo upstream permanecem não aproveitadas |

### A-2 · witnesstodark/mr-mak-workspace → 5 skills do Lia Studio + ZIP guardado

| Campo | Valor |
|---|---|
| Fonte | <https://github.com/witnesstodark/mr-mak-workspace> |
| Autor/mantenedor | "Mr. Mak Workspace contributors" (Copyright (c) 2026) |
| Licença identificada | **MIT** na raiz |
| Arquivo de licença | raiz do upstream; cópia em `Lia-Studio@203b60f:docs/licenses/MR-MAK-WORKSPACE-MIT.txt`; **o ZIP guardado traz o próprio `LICENSE` MIT e `THIRD_PARTY_NOTICES.md`** |
| Versão/commit analisado | `cf1e1260253a61499dc67fe2332a330bf1b85c14` (**verificado: existe**, 2026-11-06, "Align packaged service version with 0.6.3"); HEAD mantém as mesmas 20 skills |
| Exceção de camada | o subprojeto **`img2threejs` tem licença Apache-2.0 própria** (`img2threejs/LICENSE` + `README`), declarada no `THIRD_PARTY_NOTICES.md` do pacote: "img2threejs retains its Apache-2.0 licence and notices in each agent skill folder". Fonte citada no pacote: `https://github.com/img2threejs/img2threejs` |
| Obrigações de atribuição | MIT: aviso + texto. Apache-2.0 (`img2threejs`): aviso, texto, **e** `NOTICE` se existir, além de indicar alterações |
| Obrigações de redistribuição | MIT: livre com aviso. Apache-2.0: livre com aviso/NOTICE |
| Obrigações de código-fonte | nenhuma |
| Restrições comerciais | nenhuma pelas licenças; **as skills `fal-ai-generation` e `higgsfield-workflow` orquestram serviços pagos de terceiros** — a licença do texto não concede acesso ao serviço, e os termos do provedor são separados |
| Estado no Studio | o `THIRD_PARTY_NOTICES.md` do Studio registra que **o ZIP do Drive não foi comparado arquivo a arquivo com a fonte pública** e que nenhuma cópia direta do ZIP foi incluída; `img2threejs`, mídia, scripts e providers **não** foram importados |
| Conclusão | **`ADAPT_ALLOWED`** para as 5 já adaptadas e para as demais skills de jogo/asset; **`RESEARCH_ONLY`** para `img2threejs` (Apache-2.0 exige tratamento próprio e é subprojeto com código) e para `fal-ai-generation`/`higgsfield-workflow` (serviço pago + egress); o ZIP em si é **material de referência guardado**, não insumo redistribuído |
| Confiança | **Alta** para MIT; **Média** para `img2threejs` (a licença interna não foi lida nesta sessão, apenas declarada pelo pacote) |
| Pendências | (a) ler `img2threejs/LICENSE` antes de qualquer uso; (b) decidir se o ZIP continua versionado dentro do Lia-Studio (9,9 MB de conteúdo de terceiros num repositório Lia é risco de confusão de proveniência) |

### A-3 · Kc1t/alethe-orchestrate-skill → `alethe` vendorizado no Lia-Project

| Campo | Valor |
|---|---|
| Fonte | <https://github.com/Kc1t/alethe-orchestrate-skill> |
| Autor/mantenedor | **Kauã Miguel** (Copyright (c) 2026) |
| Licença identificada | **MIT** — cópia integral **dentro** do payload (`.agents/skills/alethe/LICENSE`) |
| Versão/commit analisado | versão upstream **19** (2026-10-23); commit de comparação anterior `c36c341c34360f970a07fe3e2d2600ca2bba8ed2` (**verificado: existe**, 2026-10-28, merge do PR #1); patches locais de segurança de 2026-10-28 |
| Obrigações de atribuição | cumpridas: `LICENSE` + `UPSTREAM.md` com projeto original, versão, licença, data e local de instalação |
| Obrigações de redistribuição | MIT: livre com aviso. **Atenção:** a cópia local está **modificada** (patches de segurança) — a MIT permite modificar, e o `UPSTREAM.md` documenta as modificações, o que é boa prática |
| Obrigações de código-fonte | nenhuma |
| Restrições comerciais | nenhuma pela MIT |
| **Risco de camada não-código** | `assets/brands/` contém **sinais distintivos de terceiros**: `claude-official.png.b64`, `openai-official-white.svg`, `kimi-official.png.b64`, `antigravity-official.svg`, `router9-official.svg`. **MIT sobre o código não licencia marcas.** Redistribuir essas imagens pode violar direito marcário/independente do titular de cada marca |
| Risco de execução | `scripts/orchestrate.py` e `scripts/diagram.py` → no Hub, `containsScripts: true`, o que eleva o nível de risco e exige revisão humana antes de promoção |
| Dependências | a skill coordena **CLIs externas** (Codex, Claude Code, Antigravity, Kimi ou custom) que **não** são distribuídas com ela; `prices.json` contém preços de provedores (dado volátil, não licença) |
| Conclusão | **`ADAPT_ALLOWED`** para o conteúdo MIT **com bloqueio específico**: **não redistribuir `assets/brands/`** sem autorização de cada titular de marca. Se o Hub exportar esta skill, os assets de marca devem ser removidos ou substituídos por texto neutro, com registro da alteração |
| Confiança | **Alta** (licença lida dentro do payload, `UPSTREAM.md` completo) |
| Pendências | (a) decisão humana sobre manter ou remover assets de marca; (b) revisar `docs/architecture/ALETHE-HARDENING-2026-10-28.md` e `ALETHE-VALIDATION-2026-10-28.md` antes de qualquer promoção; (c) confirmar se os patches locais serão oferecidos ao upstream |

### A-4 · moeru-ai/airi → 29 skills vendadas no Lia-Project

| Campo | Valor |
|---|---|
| Fonte | <https://github.com/moeru-ai/airi> (★51.451, push 2026-11-15) |
| Autor/mantenedor | **Neko Ayaka** ("Copyright (c) 2024-PRESENT Neko Ayaka") |
| Licença identificada | **MIT** — `airi/LICENSE` lido no checkout do Lia-Project |
| Versão/commit analisado | `v0.12.0-beta.5`, commit `2c1e223c…`, conforme `Lia-Project@main:docs/licenses/THIRD-PARTY-NOTICES.md` |
| Obrigações de atribuição | manter aviso de copyright e licença nos arquivos — o próprio notice do Lia-Project registra "Obrigatória (MIT)" |
| Obrigações de redistribuição | permitida sob MIT |
| Obrigações de código-fonte | nenhuma |
| Restrições comerciais | nenhuma pela MIT |
| Estado | as 29 skills estão **vendadas** em `airi/` e o Lia-Project as trata como **fonte temporária**, não dependência permanente; 21 skills Lia já foram criadas/derivadas conceitualmente a partir delas e auditadas uma a uma em `docs/architecture/AGENT-SKILLS-CATALOG.md` |
| Conclusão | **`ADAPT_ALLOWED`** (MIT). **Não catalogar as 29 como capacidades do Hub**: são conteúdo de um fork em processo de desacoplamento. O que interessa ao Hub são as skills Lia derivadas (já inventariadas) |
| Confiança | **Alta** para a licença; **Média** para o mapeamento skill-a-skill (auditoria pré-existente não re-verificada nesta sessão) |
| Pendências | confirmar se a remoção futura do AIRI preserva as atribuições das skills derivadas |

### A-5 · GameDevPipeline (referência de método, sem cópia)

| Campo | Valor |
|---|---|
| Fonte | citada no `THIRD_PARTY_NOTICES.md` do Studio como referência de método para a "Etapa 0" e modelos de documento |
| Licença identificada | **não determinada** — o próprio Studio registra: "a cópia local inspecionada não trazia `LICENSE` na raiz" e pede para confirmar titularidade e permissão antes de redistribuir qualquer conteúdo |
| Estado no Studio | **nenhum arquivo copiado ou redistribuído**; os templates de `lia-game-project-bootstrap` foram autorados originalmente |
| Conclusão | **`RESEARCH_ONLY`** — e, se algum dia houver cópia, hoje seria **`BLOCKED`** por ausência de licença |
| Confiança | **Média** (a afirmação de que nada foi copiado vem do notice do Studio; não foi feita comparação textual com o upstream nesta sessão) |
| Pendências | identificar URL/titular do GameDevPipeline e verificar licença antes de qualquer uso |

---

## 3. Grupo B — candidatos externos **não consumidos**

### B-1 · anthropics/skills (19 skills de exemplo, incluindo as de documento)

| Campo | Valor |
|---|---|
| Fonte | <https://github.com/anthropics/skills> · autor: **Anthropic** |
| Licença identificada | **API do GitHub reporta `none`; não há `LICENSE` na raiz.** Cada uma das **19 skills tem `LICENSE.txt`** próprio; `skills/skill-creator/LICENSE.txt` lido = **Apache License 2.0** (texto integral). Frontmatter usa `license: Complete terms in LICENSE.txt`. `README`: "Many skills in this repo are open source (Apache 2.0)" e declara que as skills de documentos (`docx`, `pdf`, `pptx`, `xlsx`) também são Apache-2.0. `THIRD_PARTY_NOTICES.md` na raiz lista dependências de terceiros (ex.: `imageio` 2.37.0 e `imageio-ffmpeg` 0.6.0, **BSD-2-Clause**) |
| Versão/commit analisado | HEAD em 2026-11-15 (push 2026-11-14); árvore confirmada: 19 `LICENSE.txt` |
| Obrigações de atribuição | Apache-2.0 §4: reproduzir aviso, texto da licença e `NOTICE` quando existir; indicar alterações |
| Obrigações de redistribuição | Apache-2.0: livre, com aviso e texto |
| Obrigações de código-fonte | nenhuma |
| Restrições comerciais | nenhuma pela Apache-2.0; **o `README` contém disclaimer**: skills fornecidas "para demonstração e fins educacionais", comportamento pode diferir do produto Claude |
| Risco de camada | várias skills têm **`scripts/`** (ex.: `docx`, `pdf`, `pptx`, `xlsx`, `webapp-testing`) que dependem de pacotes Python/Node → as dependências transitivas do `THIRD_PARTY_NOTICES.md` entram na análise se o código for distribuído |
| Conclusão | **`ADAPT_ALLOWED` por skill**, com verificação individual do `LICENSE.txt` de cada uma antes do uso. **Não tratar como "repositório Apache-2.0"**: a licença é por skill |
| Confiança | **Alta** para `skill-creator`; **Média** para as demais 18 (arquivo presente e nome consistente, texto não lido uma a uma) |
| Pendências | ler os 18 `LICENSE.txt` restantes; decidir se `brand-guidelines` (marca Anthropic) tem qualquer uso legítimo no ecossistema Lia — **provável `RESEARCH_ONLY`**, pois aplica identidade visual de terceiro |

### B-2 · agentskills/agentskills (especificação)

**Apache-2.0** (`LICENSE` lido) · ★27.310 · push 2026-11-04 · criado 2025-12-16. Obrigações: aviso + texto + indicação de alterações. Sem copyleft, sem restrição comercial. **Conclusão: `USE_AS_IS`** como norma de formato; o Hub **já** a implementa em `domain/skills.py`. Confiança **Alta**. Pendência: fixar a **data/versão da especificação** consultada em cada validador (o padrão pode evoluir; o Hub não deve digitar regras de memória).

### B-3 · obra/superpowers

**MIT** (`LICENSE` lido: © 2025 Jesse Vincent) · ★317.905 · push 2026-11-03 · 15 skills + `hooks/`, `scripts/`, `tests/`. **Atenção de camada:** `hooks/` e `scripts/` são **código executável** — a MIT cobre, mas o risco de execução é outro (no Hub: `containsScripts: true`, revisão humana). **Conclusão: `ADAPT_ALLOWED`** para as skills de método; **`REFERENCE`** para o padrão de empacotamento multi-host (12 diretórios `.*-plugin/`). Confiança **Alta**. Pendência: nenhuma legal; decidir se alguma skill de método será adaptada (há sobreposição com `lia-test-discipline`, `lia-release-gate`, `lia-regression-investigation`).

### B-4 · mattpocock/skills

**MIT** (`LICENSE` lido: © 2026 Matt Pocock) · ★324.857 · push 2026-11-13 · 39 skills em 4 categorias. **Conclusão: `ADAPT_ALLOWED`**, evitando `skills/in-progress/` (8 itens declaradamente não finalizados). Confiança **Alta**. Pendência: nenhuma.

### B-5 · sickn33/agentic-awesome-skills

**MIT na raiz** (`LICENSE` lido: © 2026 Antigravity User) **+ 648 arquivos de licença internos**, incluindo **184 `UPSTREAM-LICENSE.txt`**, `LICENSE-MICROSOFT` (2), `LICENSE-SIMPLE-ICONS.txt`, `LICENSE-SVGL.txt`, `LICENSE-PAYMENT-ICONS.txt`, `impeccable-LICENSE-Apache-2.0.txt` (3), `taste-skill-LICENSE-MIT.txt` (3). **Regra decisiva:** a MIT da raiz cobre a **obra de compilação/organização**; **cada skill continua sob a licença do seu upstream**. Além disso há **assets de terceiros com licenças próprias** (ícones Simple Icons — CC0/atribuição conforme o projeto, SVGL, payment icons, Microsoft) que **não** são cobertos pela MIT da raiz. **Conclusão: acervo = `RESEARCH_ONLY`**; qualquer item individual só entra como `ADAPT_ALLOWED`/`USE_AS_IS` **depois** de resolvida a licença daquele item e dos assets que ele carrega. **Esquemas `schemas/aas-v1/*` = `REFERENCE`** (ideias de índice/score reimplementáveis de forma independente). Confiança **Média** (a estrutura de licenças foi mapeada por nome de arquivo, não por leitura dos 648 textos). Pendência: se algum dia um item for aproveitado, ler o `UPSTREAM-LICENSE.txt` específico e os avisos de ícones.

### B-6 · vercel-labs/agent-skills

**API: `none`; nenhum arquivo `LICENSE`/`NOTICE` na árvore (444 blobs).** `README` tem seção `## License` declarando **MIT**, sem arquivo próprio e sem titular identificado. ★34.097 · push 2026-11-12 · 9 `SKILL.md` + `skills.sh.json`. **Conclusão: `RESEARCH_ONLY`** enquanto a declaração existir apenas no README. **Regra aplicada:** declaração em README é evidência mais fraca que arquivo de licença; para redistribuição, exigir `LICENSE` ou confirmação escrita do mantenedor. Confiança **Média-baixa**. Pendência: **humana** — pedir/confirmar licença antes de qualquer uso.

### B-7 · guanyang/open-agent-hub

**MIT** (`LICENSE` lido: © 2026 guanyang) · ★1.003 · push 2026-11-15 · 114 `SKILL.md`, 109 arquivos de licença, `spec/Specification.md`, `skills_index.json`, `skills_sources.json`, CLI `scripts/hub.js`. **Contaminação a verificar:** o README declara que `AGENTS.md`, `CLAUDE.md` e `GEMINI.md` do projeto "derivam de `multica-ai/andrej-karpathy-skills`", repositório **sem licença**. Isso não contamina automaticamente o código MIT do autor, mas **impede copiar esses três arquivos** e exige cautela ao reproduzir qualquer texto deles. **Conclusão: `REFERENCE`** para arquitetura (link por host, índice derivado, sync) e **`INDEPENDENT_REIMPLEMENTATION`** se quisermos comportamento equivalente; **`RESEARCH_ONLY`/`BLOCKED`** para os três arquivos derivados de fonte sem licença. Confiança **Média-alta**. Pendência: ler `spec/Specification.md` antes de propor o contrato de distribuição do Hub.

### B-8 · modelcontextprotocol/servers

**`NOASSERTION`** na API. `LICENSE` **lido**: o projeto está em **transição de MIT para Apache-2.0** — contribuições novas em Apache-2.0; documentação (exceto especificações) em **CC-BY-4.0**; contribuições de autores que não consentiram relicenciamento **permanecem MIT**. ★92.009 · push 2026-11-12. **Conclusão: `RESEARCH_ONLY` por padrão**; `ADAPT_ALLOWED` **somente por arquivo**, após identificar a licença daquela contribuição. **Nunca citar "o repositório é MIT/Apache"** — é misto. Confiança **Alta** (texto lido). Pendência: se um servidor de referência for usado, registrar arquivo, commit e licença individual.

### B-9 · Garyson26/Trident-SecOps-Skills

**MIT** (`LICENSE` lido: © 2026 Garyson26) · ★42 · push 2026-09-30 · 24 `SKILL.md`, um único `LICENSE` na raiz. **Conclusão: `ADAPT_ALLOWED`**. Confiança **Alta** para a licença; **Média** para o conteúdo (nenhuma das 24 skills foi lida integralmente). Pendência: revisão de conteúdo por segurança antes de adaptação — instrução de SecOps incorreta é risco operacional.

### B-10 · Listas e coleções **sem licença** → `BLOCKED`

| Fonte | Evidência | Conclusão |
|---|---|---|
| `travisvn/awesome-claude-skills` | raiz contém apenas `.gitignore`, `CONTRIBUTING.md`, `README.md`; API: `none`; ★15.823; sem push desde 2026-04-28 | **`BLOCKED`** para cópia/derivação. Links individuais podem ser auditados por conta própria |
| `multica-ai/andrej-karpathy-skills` | API: `none`; ★233.323; conteúdo derivado de declarações públicas de terceiro | **`BLOCKED`** — dupla fragilidade: sem licença **e** derivado de fala de terceiro |
| `Yuki001/game-dev-skills` | API: `none`; ★116 | **`BLOCKED`** |
| `Tariux/AI-Skills-Not-Awesome` | API: `none`; ★48 | **`BLOCKED`** |
| `Firmansjk/BlenderGIS-Terrain-Export-AISkill`, `ameratom/3d-text-animation-skill`, `geckse/n8n-dev-skills`, `strativd/ai-skills` | API: `none` | **`BLOCKED`** |

> **Nota de princípio:** estes repositórios são públicos e populares. Popularidade não gera direito. Para o Hub eles são **evidência de que existe oferta sem licenciamento** — o que reforça o valor de um catálogo que trata licença desconhecida como estado visível (`licenseKnown: false`), nunca como permissão.

### B-11 · Licenças incompatíveis com a distribuição pretendida

| Fonte | Licença | Por quê | Conclusão |
|---|---|---|---|
| `Ibrahim-3d/orchestrator-supaconductor` | **AGPL-3.0** | copyleft de rede: qualquer serviço derivado exige disponibilizar o código-fonte do derivado; incompatível com distribuição empacotada sem abertura total | **`BLOCKED`** para incorporação; `RESEARCH_ONLY` para padrões |
| `Comfy-Org/comfy-mcp` (via Forge T14) | **dual AGPL-3.0-or-later / comercial** | mesma razão + condição comercial | **`BLOCKED`** (a Forge já concluiu o mesmo em 2026-11-14) |
| `hesreallyhim/awesome-claude-code` | **CC-BY-NC-ND 4.0** (`LICENSE` lido) | **NC** veda uso comercial; **ND** veda derivados — um catálogo que reorganiza a lista já seria derivado | **`RESEARCH_ONLY`** (leitura), **`BLOCKED`** para qualquer republicação/adaptação |

### B-12 · Casos que dependem de terceiros **não licenciados pelo código**

| Caso | Natureza | Tratamento |
|---|---|---|
| `fal-ai-generation`, `higgsfield-workflow` (mr-mak) | skills que orquestram **serviços pagos** (fal.ai, Higgsfield) | licença do texto ≠ acesso ao serviço; exigem conta, custo e **egress** de dados → decisão humana D-19 |
| `diivi/aseprite-mcp`, `willibrandon/pixel-mcp` (via Forge T14) | código MIT, **editor Aseprite pago/EULA** | catalogar o código não autoriza o editor; registrar requisito de licença de terceiro |
| `CoplayDev/unity-mcp` (via Forge T14) | código MIT, **Unity Personal/comercial** | idem |
| `pixellab-code/pixellab-mcp` (via Forge T14) | **sem licença** + destino remoto pago | **`BLOCKED`** |
| Pesos/modelos citados em `configs/model-candidates.yaml` (Model-Lab) e no catálogo de 44 registros (Lia-Project) | licença de **pesos** ≠ licença de código (ex.: código MIT com pesos CC-BY-NC-4.0, como o Lia-Project registrou para `f5-tts`) | já tratado pelo Lia-Project em `docs/research/lia-capability-catalog/07-CATALOGO-ESTRUTURADO.md`; o Hub deve manter `license.code` / `license.content` / `license.weights` separados — o modelo implementado **já** tem esses três campos |

---

## 4. Grupo C — licença dos **próprios repositórios Lia** (bloqueio real de distribuição)

Este é o achado de maior consequência prática: antes de distribuir qualquer skill Lia, é preciso saber sob que licença **nós** a publicamos.

| Repositório | `LICENSE` na raiz? | SPDX na API | Avisos de terceiros | Consequência |
|---|---|---|---|---|
| `Lia-Studio` | **não em `main`**; **sim na branch** `arena/01a0f4ab-lia-gamedev`: MIT (© 2026 BloomRX e colaboradores da Lia Studio) | `none` | `THIRD_PARTY_NOTICES.md` + `docs/licenses/*.txt` (2 textos integrais) + política de marca explícita | 16 skills **têm** base de licença declarada, mas **só na branch** |
| `Lia-Forge` | **não em `main`**; **sim na branch** `arena/649f88bd-3dspritesheet`: MIT (© 2026 Lia Forge contributors) | `none` | `THIRD_PARTY_NOTICES.md` com **464 pacotes npm** (lockfile v3) + exclusão explícita de nome/marca/`assets/lia-forge.svg`/`.ico` | melhor SBOM do ecossistema; 1 skill coberta só na branch |
| `Lia-Project` | **não** (nem `main` `9c7ac183fd`, nem `arena/c6b02f64`) | `none` | `docs/licenses/THIRD-PARTY-NOTICES.md` (AIRI MIT) e `docs/licenses/ASSET-LICENSES.md` — **terceiros e assets apenas** | **21 skills autorais sem licença declarada do código próprio** |
| `Lia-Model-Lab` | **não** (`main` `3ec4313`) | `none` | não encontrado | **9 skills autorais sem licença declarada** |
| `Lia-Go` | **não** | `none` | não encontrado | ferramentas sem licença declarada |
| `Lia-AgentHub` | **não** (nem `main`, nem `arena/a92004be-lia-agenthub`) | `none` | `THIRD_PARTY_NOTICES.md` (presente na branch de implementação) | **o próprio Hub não declara licença** — e é ele que vai exportar pacotes |

**Regra aplicada:** sem licença declarada, os direitos permanecem reservados. Isso **não impede uso interno** pelo próprio autor (o usuário é o titular), mas **impede afirmar que terceiros podem usar, adaptar ou redistribuir** essas skills. Portanto:

- 47 skills Lia → **`RESEARCH_ONLY` para redistribuição a terceiros** até que a licença do repositório de origem seja declarada. **Uso interno no ecossistema Lia: permitido** pelo titular (decisão humana a registrar).
- Esta é uma **decisão de produto** (D-16 do `DECISION-REGISTER.md`: "O Hub será inicialmente ferramenta pessoal, produto para distribuição ou projeto open-source?") e **não** pode ser tomada pelo agente.

---

## 5. Camada de marca (independente de licença de código)

Três evidências convergentes de que o ecossistema Lia **já** separa marca de código — e um caso em que essa separação foi violada por conteúdo de terceiro:

| Evidência | Fonte |
|---|---|
| "A identidade da Lia (nome, personagem, logo, identidade visual) tem proteção de marca **separada** e **não** está licenciada pela MIT para apropriação ou representação como produto oficial. Forks não devem se apresentar como oficiais." | `Lia-Studio@203b60f:THIRD_PARTY_NOTICES.md` |
| "Nome, marca e arquivos `assets/lia-forge.svg` e `assets/lia-forge.ico` **não** recebem licença pela MIT deste repositório" | `Lia-Forge@35b207f:THIRD_PARTY_NOTICES.md` |
| `assets/brands/` com `claude-official.png.b64`, `openai-official-white.svg`, `kimi-official.png.b64`, `antigravity-official.svg`, `router9-official.svg` dentro de skill MIT vendorizada | `Lia-Project@0093de09:.agents/skills/alethe/assets/brands/` |
| Skills que aplicam identidade visual de terceiro (`brand-guidelines` da Anthropic) | `anthropics/skills/skills/brand-guidelines` |

**Política proposta (para decisão humana):** o Hub deve tratar **marca como camada separada** em qualquer pacote exportado — campo próprio no manifesto, com recusa de exportação *shared/public* quando o payload contiver sinal distintivo de terceiro sem autorização registrada. Isso é consistente com o modelo implementado, que já separa `license.code` / `license.content` / `license.weights`; falta a camada `trademark`/`brand`.

---

## 6. Dependências de ferramentas (camada que o Hub empacota sem executar)

| Dependência | Licença | Onde aparece | Observação |
|---|---|---|---|
| `pywebview` 6.2.1 | **BSD-3-Clause** | build Windows do Lia Studio (`desktop/requirements-windows.txt`) | verificado por metadados PyPI em 2026-10-18 pelo Studio; transitivas (`pythonnet`, `proxy_tools`, `bottle`) **não travadas nem auditadas** |
| `PyInstaller` 6.22.3 | **GPL-2.0-or-later com exceção** para programas empacotados | build Windows do Studio; `packaging/lia_agenthub.spec` do Hub | a exceção cobre o programa empacotado, **não** dispensa revisar transitivas (`altgraph`, `packaging`, `pefile`, `pyinstaller-hooks-contrib`, `pywin32-ctypes`, `setuptools`) |
| 464 pacotes npm | variados (tabela no notice da Forge) | `Lia-Forge@35b207f` | o próprio notice avisa: metadado de lockfile é índice, **não substitui** a revisão do texto completo |
| `@modelcontextprotocol/sdk`, `zod` | não verificados nesta sessão | `scripts/spriteforge-mcp.mjs` (Forge) | pendência: verificar antes de catalogar o servidor MCP da Forge |
| `uv` (astral-sh) | MIT/Apache (a verificar na fonte) | candidato citado pela pesquisa anterior do Hub (`docs/research/INTEGRATION-CANDIDATES.md` na branch de referência) | não re-verificado aqui — referência cruzada |

**Regra:** o Hub **não executa** nada disso; mas ao **empacotar** uma capacidade que declara dependências, ele distribui metadado que pode induzir instalação. O pacote deve portanto carregar a lista de dependências **e** o estado de licença de cada uma (campo `requirements`, já existente no modelo, hoje `null`).

---

## 7. Convenções de identidade e proveniência (Missão 6)

### 7.1 Nomenclatura

| Caso | Nome | Obrigação |
|---|---|---|
| Skill **original** da Lia | prefixo **`lia-`** + domínio + ação (`lia-license-audit`, `lia-skill-intake`) | declarar autoria Lia e licença do repositório de origem |
| Skill de **terceiro sem alteração** | **nome original preservado** (ex.: `alethe`, `skill-creator`) | não renomear: renomear quebra a rastreabilidade do upstream e a atribuição |
| **Adaptação** de terceiro | nome **`lia-`** próprio (ex.: `lia-game-qa-plan` ← `qa-plan`) + seção `## Origem` com **link ao arquivo exato no commit** | preservar aviso/licença do upstream **dentro do payload**; registrar o que foi removido (hooks, scripts, paths, seleção de modelo) |
| **Fork** mantido | nome `lia-` + `UPSTREAM.md` no payload | documentar divergência, patches locais e política de comparação com upstream |
| **Reimplementação independente** | nome `lia-` + documentação da referência e do processo | registrar a fonte da **ideia** e afirmar que nenhum material protegido foi copiado |

**Estado atual do ecossistema frente a esta convenção:** 44 de 47 skills Lia já usam `lia-`; **3 não usam** (`capability-mapping`, `dataset-governance`, `experiment-reproducibility`, `finetuning-plan`, `model-candidate-research`, `model-evaluation`, `model-license-release-review`, `multi-agent-orchestration` no Model-Lab — 8 casos; e `airi-upstream-integration`, `stage-runtime-debugging` no Project — 2 casos). **Total real: 10 skills autorais sem o prefixo.** Renomear é decisão humana (muda caminhos referenciados por testes e docs).

### 7.2 Cadeia de proveniência mínima por skill derivada

```
skill derivada
├─ origem imediata      : repo/branch/commit de onde o Hub importou
├─ upstream real        : projeto, URL do arquivo, commit, data de consulta
├─ licença do upstream  : SPDX + caminho do arquivo de licença + texto preservado
├─ transformação        : "adaptada" | "fork" | "reimplementação independente" | "sem alteração"
├─ o que foi removido   : hooks, scripts, credenciais, paths, marcas
├─ o que foi acrescido  : patches locais (com data e motivo)
└─ camadas separadas    : código | conteúdo/documentação | pesos | dados | marca
```

O padrão do Studio (`## Origem` + `THIRD_PARTY_NOTICES.md` + `docs/licenses/<UPSTREAM>-MIT.txt`) e o padrão do Project para `alethe` (`LICENSE` + `UPSTREAM.md` dentro do payload + doc de hardening) **já satisfazem** quase todos os itens. **O que falta é o local**: o aviso precisa estar **dentro** do payload para viajar com a skill.

### 7.3 Lacuna do modelo implementado (proposta compatível, sem alterar contrato em produção)

O modelo do Hub (`domain/model.py`, schemaVersion 1) tem `source.upstream`, `source.commit`, `source.method`, `source.original_name` e `versionOf` (linhagem de versões). **Não há campo para derivação** ("adaptada de X no commit Y, removendo hooks"). Proposta de evolução **aditiva** (não quebra leitores antigos, que ignoram chaves desconhecidas):

```jsonc
"source": {
  "upstream": "BloomRX/Lia-Studio@203b60f:.agents/skills/lia-game-qa-plan",
  "commit": "203b60f17d177f7faf79d293b95f078d0d0a729a",
  "method": "local",
  "originalName": "qa-plan",
  "derivedFrom": [                       // NOVO, opcional, lista ordenada
    {
      "project": "Donchitos/Claude-Code-Game-Studios",
      "url": "https://github.com/Donchitos/Claude-Code-Game-Studios/blob/05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418/.claude/skills/qa-plan/SKILL.md",
      "commit": "05ad7c8a5b8aa2aa86bbd3439ae7cf7295cac418",
      "license": "MIT",
      "transformation": "adapted",       // adapted | fork | independent | unchanged
      "removed": ["hooks", "scripts", "agent-framework", "model-selection"],
      "consultedAt": "2026-11-15"
    }
  ]
}
```

Enquanto o campo não existir, a informação vive em `researchNotes` fora do contrato (como nos registros gerados em `docs/research/catalog/`) — **nunca** inventando chaves dentro de `capability.json`.

### 7.4 Convenção de empacotamento proposta (resolve L-01)

Para que a licença viaje com a capacidade, cada payload exportado pelo Hub deve conter, na raiz:

| Arquivo | Quando | Origem do conteúdo |
|---|---|---|
| `SKILL.md` | sempre | o recurso |
| `LICENSE` | quando a licença for conhecida | texto integral da licença aplicável **àquela camada** |
| `NOTICE` | quando a licença exigir aviso (Apache-2.0, MIT em redistribuição) | avisos de atribuição |
| `THIRD_PARTY_NOTICES.md` | quando houver material de terceiros ou dependências | avisos por camada (código/conteúdo/pesos/marca) |
| `UPSTREAM.md` | quando for adaptação, fork ou cópia vendorizada | cadeia de proveniência do §7.2 |

O formato `.lia-capability` implementado **já prevê** `NOTICE` e `THIRD_PARTY_NOTICES.md` (`adapters/packager.py`) e o importador **já não reclama** desses arquivos como "não manifestados" — falta apenas a **convenção de que a skill os traga desde a origem**, porque `_detect_license` só olha a raiz do payload.

---

## 8. Pendências de decisão humana

| # | Decisão pendente | Por que não é do agente | Registro relacionado |
|---|---|---|---|
| P-1 | Declarar licença dos repositórios `Lia-Project`, `Lia-Model-Lab`, `Lia-Go` e `Lia-AgentHub` | define se 47 skills podem ser redistribuídas | D-16, D-11 |
| P-2 | Aprovar a política de marca como camada separada no pacote exportado | direito marcário, não técnico | §5 |
| P-3 | Decidir sobre `assets/brands/` do `alethe` (manter, remover ou substituir) | risco de marca de terceiros | A-3 |
| P-4 | Confirmar a licença do `vercel-labs/agent-skills` (MIT só em README) | exige contato/autorização | B-6 |
| P-5 | Autorizar adaptação de skills específicas de `anthropics/skills` (`skill-creator`, `mcp-builder`, `webapp-testing`) | escolha de escopo do Skill Creator/MCP Workshop | B-1 |
| P-6 | Decidir se o ZIP `Mr-Mak-Skills-Free.zip` continua versionado dentro do Lia-Studio | 9,9 MB de conteúdo de terceiros em repositório Lia | A-2 |
| P-7 | Aceitar ou rejeitar a evolução aditiva `source.derivedFrom` | muda contrato de dados do produto | §7.3, D-03/D-04 |
| P-8 | Definir nível de risco aceitável para skills com `scripts/` (`alethe`, `anthropics/docx|pdf|pptx|xlsx`, `mr-mak/fal-ai-generation`) | política de risco | D-18 |
| P-9 | Definir o que pode sair da máquina quando uma skill orquestra serviço pago (fal.ai, Higgsfield, PixelLab) | egress/privacidade | D-19 |
| P-10 | Decidir se skills sem licença (`BLOCKED`) podem ao menos ser **referenciadas** por URL no catálogo, sem cópia | política de catálogo | B-10, D-20 |

---

## 9. O que esta auditoria **não** afirma

- **Não é parecer jurídico.** Classificações são de engenharia/compliance documental e podem ser revistas por profissional habilitado.
- **Nenhuma licença foi aceita**, nenhum termo foi clicado, nenhuma cópia foi feita, nenhum pacote foi distribuído.
- **Nada foi executado**: nem skills, nem scripts, nem CLIs, nem servidores MCP.
- **Confiança declarada por item** (Alta/Média/Baixa) refere-se à evidência lida, não à solidez jurídica.
- Itens marcados "não lido" ou "por nome de arquivo" **não** foram verificados no texto — estão sinalizados como pendência.
- A ausência de um repositório nesta lista **não** significa que ele não exista ou não seja útil: significa que não foi alcançado nesta rodada com os critérios adotados.
