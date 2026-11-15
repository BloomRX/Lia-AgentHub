# Registro de decisões — Lia Agent Hub

**Status inicial:** as questões abaixo estão abertas para pesquisa e proposta.
**Regra:** Arena pode pesquisar e recomendar; decisões de produto, risco, publicação e autorização de implementação exigem aceite humano.
**Última atualização:** 2026-11-15 (Agent 0 — Fase 0), branch `arena/a92004be-lia-agenthub`, base `main` @ `34a27f48`.
**Natureza desta atualização:** anexar evidência, alternativas e recomendação. **Nenhuma decisão foi aprovada.** Onde há recomendação, o campo diz `RECOMMENDED (Agent 0)`, nunca `APPROVED`.

---

## Direções já estabelecidas no briefing

| Tema | Direção atual | Estado |
|---|---|---|
| Nome | Lia Agent Hub | Nome adotado para o repositório e produto de trabalho; marca final pode ser validada depois |
| Posicionamento | Produto independente e transversal | Direção proposta |
| Domínios | Não limitar a Game Development | Direção proposta |
| Local-first | Funções essenciais sem nuvem obrigatória | Princípio definido |
| Providers | Neutralidade entre opções locais, gratuitas e pagas | Princípio definido |
| Separação de responsabilidades | Hub cria/curadoria/distribui; hosts autorizam e executam | Princípio definido |
| Autonomia dos hosts | Studio, Forge e agentes externos não dependem de runtime central do Hub | Princípio definido |
| Segurança | Conteúdo externo não confiável por padrão; controle humano | Princípio definido |
| Implementação | Não autorizada durante a Fase 0 | Decisão atual |

---

## Como ler as tabelas de decisão

| Campo | Significado |
|---|---|
| **Estado** | `OPEN` · `RESEARCHING` · `RECOMMENDED` · `APPROVED` · `REJECTED` · `DEFERRED` |
| **Recomendação Agent 0** | Proposta da sessão, com evidência. **Não é aprovação** |
| **Impacto de adiar** | O que fica bloqueado enquanto a decisão não é tomada |
| **Humano?** | Se exige aceite do responsável do produto antes da implementação que dela dependa |

---

## Parte I — Decisões abertas do briefing original (D-01 a D-14)

### D-01 — Nome final e posicionamento da marca

| | |
|---|---|
| **Estado** | `OPEN` |
| **Questão original** | Confirmar o nome final e posicionamento da marca |
| **Evidências** | `Lia-Project` é a Waifu (nome histórico engana); kit `GLOSSARIO.md` §7 registra o problema. O Ecossistema já tem 4 repositórios com prefixo `Lia-` |
| **Alternativas** | (a) manter **Lia Agent Hub**; (b) `Lia Capability Hub`; (c) `Lia Skills`; (d) outro |
| **Vantagens (a)** | Já no repositório, no `README` e nos documentos; "Agent" descreve o consumidor; "Hub" descreve a função |
| **Desvantagens (a)** | "Hub" pode sugerir marketplace/serviço residente — o que o produto **não** é. "Agent Hub" pode sugerir orquestração — que é do **Studio** |
| **Recomendação Agent 0** | **Manter `Lia Agent Hub`** como nome de trabalho e resolver a ambiguidade na **descrição**, não no nome: *"biblioteca e oficina de capacidades"*, nunca *"hub de agentes"*. Mudar o nome agora custaria atualização em 9 documentos sem ganho |
| **Impacto de adiar** | Nenhum técnico. Afeta comunicação e identidade visual (Fase 1b) |
| **Humano?** | **Sim**, se houver mudança |

### D-02 — Escopo do catálogo inicial

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Apenas Skills/MCPs ou catálogo amplo desde o começo? |
| **Evidências** | Auditoria §5: as 8 lacunas são de **registro**, não de tipo. Forge já distingue Tool/Provider/Adapter/Plugin/Workflow/Skill/Agent (`TOOL-PROVIDER-HUB.md`); `PRODUCT-VISION.md` §6 lista 10 tipos |
| **Alternativas** | (a) só Skill; (b) Skill + MCP; (c) 10 tipos com implementação profunda só em Skill |
| **Vantagens (c)** | O **modelo de dados** nasce completo (tipo é campo), então adicionar um tipo não exige migração. Implementação profunda (editor, validador) fica só em `skill` no MVP |
| **Desvantagens (c)** | Mais campos para preencher cedo; risco de parecer que suporta o que não suporta |
| **Riscos** | Se o tipo for decidido depois, todo registro já gravado precisa de migração |
| **Recomendação Agent 0** | **(c)**, com rótulo explícito na interface do que está **implementado** vs. **apenas catalogável**. Um tipo catalogável tem ficha de metadado, não editor |
| **Impacto de adiar** | Bloqueia o schema do MVP. **É a decisão de maior custo de adiamento** |
| **Humano?** | **Sim** |

### D-03 — Formatos canônicos de Skill e metadados

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Quais formatos canônicos, preservando formatos abertos? |
| **Evidências** | `INTEGRATION-CANDIDATES.md` §2: Agent Skills é padrão aberto (2025-12-18), Apache-2.0/CC-BY-4.0, 6 campos de frontmatter, governança neutra. **O Studio já usa `.agents/skills/<id>/SKILL.md` com `name`+`description`** e declara compatibilidade. Clientes estritos **rejeitam** chave desconhecida |
| **Alternativas** | (a) Agent Skills puro; (b) Agent Skills + frontmatter estendido; (c) formato próprio Lia |
| **Vantagens (a)** | Interoperabilidade gratuita com 40+ clientes; zero migração no Studio; spec governada |
| **Desvantagens (a)** | A spec não tem versão, proveniência, hash nem trust obrigatórios |
| **Por que (b) é rejeitada** | Quebra clientes estritos — o oposto do objetivo |
| **Por que (c) é rejeitada** | Repetiria o trabalho que o ecossistema já fez; ilegível por qualquer cliente |
| **Recomendação Agent 0** | **(a) + manifesto complementar em `.lia/`**: `SKILL.md` no formato padrão, sem uma chave a mais; `capability.json`/`provenance.json` ao lado. Resolve a tensão sem quebrar nada |
| **Impacto de adiar** | Bloqueia M2, M3, M7 (import, validação, pacote) |
| **Humano?** | **Sim** |

### D-04 — Modelo de dependências entre Skills, MCPs, CLIs e APIs

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Como representar dependências entre tipos de recurso? |
| **Evidências** | Forge já tem `requirements {os,gpu,vramMb,ramMb,diskMb,network,runtimes,tools}` com **`null` = não medido** (`registry.mjs`). `PRODUCT-VISION.md` §6 exige "registradas separadamente, com versões, fontes e riscos próprios" |
| **Alternativas** | (a) só declarar, sem resolver; (b) resolver dependências no Hub; (c) declarar + indicar quem resolve |
| **Vantagens (c)** | O Hub não assume execução (não "instala" dependência) mas o host sabe o que precisa |
| **Desvantagens (c)** | Exige que o host interprete; documentação de contrato |
| **Riscos** | Resolver dependência no Hub (b) o transformaria em gerenciador de pacotes de execução — **fora de escopo** |
| **Recomendação Agent 0** | **(c)**: `dependsOn[]` com `{id, kind, versionRange, optional, resolvableBy: hub\|host\|user}`. `null` semântico obrigatório. Range de versão compatível com semver |
| **Impacto de adiar** | Bloqueia M5/M6 parciais; não bloqueia M1 |
| **Humano?** | **Sim** (para o vocabulário final) |

### D-05 — Estratégia reproduzível de teste e isolamento (Windows e Linux)

| | |
|---|---|
| **Estado** | `OPEN` — **esta é a decisão menos resolvida do registro** |
| **Questão original** | Como testar Skills e servidores MCP de maneira reproduzível e isolada? |
| **Evidências** | `SECURITY-AND-TRUST-MODEL.md` §11: `uv tool install` **não é sandbox**; `--allowedTools` **não é sandbox** (documentado pelo próprio Studio); contêiner no Windows para app desktop com GUI não é isolamento por padrão; Windows Sandbox isola mas é VM interativa. **Não houve pesquisa de SBOM nem de assinatura nesta fase** |
| **Alternativas** | (a) contêiner/WSL2 por capacidade; (b) VM descartável (Windows Sandbox); (c) processo separado com usuário restrito e perfis de SO; (d) **não testar** e declarar isso |
| **Vantagens (d)** | É a única opção **verdadeira hoje**. O produto não afirma o que não pode provar |
| **Desvantagens (d)** | Limita o valor do Hub a curadoria, sem execução |
| **Recomendação Agent 0** | **(d) no MVP, explicitamente.** Fase 4 bloqueada até decisão com prova real. **Recomendo sessão de pesquisa dedicada** a isolamento em Windows antes de qualquer compromisso |
| **Impacto de adiar** | Bloqueia Test Lab. **Não bloqueia o MVP** |
| **Humano?** | **Sim, e com força** — é decisão de risco |

### D-06 — Armazenamento local, versionamento, backup e exportação

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Qual estratégia local-first? |
| **Evidências** | `DATA-STORAGE-AND-PORTABILITY.md` §3: arquivos + índice derivado; padrão `Lia\` do kit; Forge usa workspace visível; Project usa wiki Markdown com índice reconstruível |
| **Alternativas** | (a) arquivos + `index.json`; (b) SQLite como fonte; (c) SQLite como índice; (d) git obrigatório |
| **Vantagens (a)** | Inspecionável, copiável, `grep`ável, sobrevive ao produto |
| **Desvantagens (a)** | Consulta não indexada; escala limitada (irrelevante para uso pessoal) |
| **Por que (b)/(d) são rejeitadas** | (b) dado do usuário em binário opaco; (d) exclui usuário leigo |
| **Recomendação Agent 0** | **(a)**, com: backup **manual** (não automático), quarentena **sem expiração automática**, escrita atômica, import em duas fases, biblioteca em `Lia\AgentHub\` separada de `Lia\Studio\Skills\`. SQLite **só como índice** se medição provar necessidade |
| **Impacto de adiar** | Bloqueia M1 |
| **Humano?** | **Sim** — inclusive sobre backup automático (recomendo **não**) e sobre o desvio de pasta |

### D-07 — Como Studio e Forge recebem atualizações

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Importação, pacote local, API ou alternativa? |
| **Evidências** | Forge: `REQUIRES_HUMAN_DECISION` sobre protocolo entre apps (`STUDIO-FORGE-CONSISTENCY-ARCHITECTURE.md`); Studio: `forge_brief.py` com `sent: False`, preview + hash + confirmação — padrão correto de "não envia sem aprovação" |
| **Alternativas** | (a) arquivo `.lia-capability` + `index.json`; (b) API local; (c) IPC nativo; (d) banco compartilhado |
| **Vantagens (a)** | Funciona com Hub desinstalado (T2/T3); inspecionável; versionável em git; zero superfície de rede |
| **Desvantagens (a)** | Sem notificação em tempo real; host precisa varrer/relendo |
| **Por que (d) é rejeitada** | Acopla stores internos — exatamente o que `PRODUCT-VISION.md` §10 e a §2.1 da arquitetura proíbem |
| **Recomendação Agent 0** | **(a)**, com o **mesmo desenho de confirmação** do `forge_brief.py`: host mostra o que vai copiar, hash, e só então copia. **O Hub não sabe que o host existe** |
| **Impacto de adiar** | Bloqueia M8 e a Fase 3 |
| **Humano?** | **Sim** |

### D-08 — Necessidade de SDK/CLI

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | O Hub deve ter SDK/CLI para integração externa? |
| **Evidências** | `PLATFORM-AND-TECHNOLOGY-DECISION.md` §4.4: CLI é **fase 1 técnica**, não produto final. Nenhum consumidor externo existe hoje além de Studio/Forge, e eles precisam de **arquivo**, não de SDK |
| **Alternativas** | (a) CLI interna de desenvolvimento; (b) CLI pública estável; (c) SDK por linguagem; (d) só interface gráfica |
| **Vantagens (a)** | Permite F1a antes da UI; valida o domínio; desbloqueia empacotamento gradualmente |
| **Desvantagens (b)/(c)** | SDK público sem consumidor é manutenção sem receita; versionar API sem uso real é adivinhação |
| **Recomendação Agent 0** | **(a) agora**; **CLI pública só quando houver consumidor externo real**; SDK **não recomendado nesta fase** |
| **Impacto de adiar** | Nenhum para o MVP (CLI interna é decisão de implementação) |
| **Humano?** | Sim para publicar como produto |

### D-09 — Quais recursos por API local e quais por arquivo/pacote

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | O que deve ser API e o que deve ser arquivo? |
| **Evidências** | `PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §7.1 (comparação); T2/T3 (funciona desinstalado, inspecionável) |
| **Alternativas** | (a) tudo arquivo; (b) tudo API; (c) arquivo primário + API opcional |
| **Recomendação Agent 0** | **(a) no MVP.** Reconsiderar **só** quando um host precisar de consulta que arquivo não resolve (filtro por metadado sem varrer disco, ou notificação de nova versão). Se vier: loopback apenas, porta efêmera, token `owner-only`, `Origin` verificado. **API local exige revisão de segurança dedicada** |
| **Impacto de adiar** | Nenhum no MVP |
| **Humano?** | Sim |

### D-10 — Como impedir mudanças silenciosas de comportamento

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Como evitar que atualizações alterem silenciosamente o comportamento dos agentes? |
| **Evidências** | `SECURITY-AND-TRUST-MODEL.md` §9. Precedente negativo concreto e público: README de MCPVault recomenda `npx @bitbonsai/mcpvault@latest`. `description` **é** o gatilho de ativação, então mudá-la muda comportamento mesmo sem tocar o corpo |
| **Alternativas** | (a) pinagem por hash + diff obrigatório; (b) semver + confiança no autor; (c) "latest" com changelog |
| **Recomendação Agent 0** | **(a)**, obrigatoriamente: pin por `contentHash`; **nenhum campo "latest"** no índice; diff obrigatório de **corpo + `description` + `declaredPermissions` + `egress` + `requirements`**; atualização **não herda** `reviewed-external` |
| **Impacto de adiar** | Bloqueia M6 |
| **Humano?** | **Sim** |

### D-11 — Preservação de licenças e avisos em pacotes distribuídos

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Como preservar licenças e avisos de terceiros? |
| **Evidências** | `PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §6.4 (quatro camadas com divergência real). Kit: *"Apache-2.0 não é MIT. Exige preservar o arquivo `NOTICE`"*; *"Biblioteca ≠ pesos de modelo"* (caso XTTS-v2). Forge registra item externo sem `LICENSE` (`license: null`) |
| **Alternativas** | (a) licença única no pacote; (b) licença por camada + `NOTICE` + `THIRD_PARTY_NOTICES.md` gerado; (c) nenhum campo, aviso no README |
| **Recomendação Agent 0** | **(b)**: `license {code, content, weights}` separados, `null` quando não revisado; **exportação falha** com `license` não revisada; `NOTICE` preservado quando a licença exigir; `THIRD_PARTY_NOTICES.md` **gerado do manifesto**, não escrito à mão |
| **Impacto de adiar** | Bloqueia M7; risco jurídico |
| **Humano?** | **Sim** — e o aceite de qualquer licença de terceiro é sempre humano |

### D-12 — Quando catálogo remoto ou comunidade fariam sentido

| | |
|---|---|
| **Estado** | `DEFERRED` |
| **Questão original** | Em que momento um catálogo remoto ou comunidade faria sentido? |
| **Evidências** | Registro de incidentes (Snyk ToxicSkills, ClawHavoc) mostra que catálogo público **concentra risco**. Requer backend, moderação, política de conteúdo, custo recorrente e `D-16` |
| **Alternativas** | (a) nunca; (b) depois do MVP com distribuição manual; (c) cedo, como diferencial |
| **Recomendação Agent 0** | **(b)**, e só depois de: MVP entregue e validado; `D-16` definido; política de moderação escrita; plano de custo. **Importação por URL/git pode entrar na Fase 3** (opt-in, com consentimento de egress) |
| **Impacto de adiar** | Nenhum. **Não é pré-requisito de nada no MVP** |
| **Humano?** | **Sim** |

### D-13 — Funcionalidades essenciais do MVP vs. adiáveis

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Quais funcionalidades são essenciais no primeiro MVP? |
| **Evidências** | `MVP-AND-ROADMAP.md` §3, §6. As oito lacunas (L-01…L-08) da auditoria mapeiam 1:1 nas capacidades M1–M8 |
| **Alternativas** | (a) só biblioteca + pacote (A); (b) **M1–M8** (B); (c) B + Test Lab (C) |
| **Recomendação Agent 0** | **(b)**. A é utilitário sem opinião sobre confiança; C afirma segurança que não se pode provar hoje |
| **Impacto de adiar** | **Bloqueia toda a Fase 1** |
| **Humano?** | **Sim — é a autorização que a Fase 0 pede** |

### D-14 — Tecnologia da aplicação

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão original** | Electron, web local ou outra arquitetura? |
| **Evidências** | `PLATFORM-AND-TECHNOLOGY-DECISION.md` §3 (stacks reais), §4 (8 critérios, K1+K2 = 45 %), §5 |
| **Alternativas** | (a) Python stdlib + WebView2 + PyInstaller; (b) Electron + Node; (c) Tauri; (d) web pura; (e) CLI |
| **Recomendação Agent 0** | **(a)**: núcleo Python 3.9+ stdlib, UI web local em WebView2, PyInstaller, instalação por usuário. Electron é **viável e não recomendado** (custo de runtime desproporcional a um editor de texto/arquivo). Web/mobile **rejeitados por natureza do produto** (depende de sistema de arquivos real). Tauri como reavaliação futura |
| **Impacto de adiar** | Bloqueia Fase 1 inteira |
| **Humano?** | **Sim** |

---

## Parte II — Questões adicionais (D-15 a D-20)

### D-15 — Quem é o usuário primário do MVP

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Observação original** | Propor personas e priorização |
| **Recomendação Agent 0** | **Persona primária: o autor individual técnico-mas-não-necessariamente-programador** — alguém que usa Claude Code/Codex/Studio e quer organizar o que já usa. Razão: é o público que **sente** a dor das 8 lacunas hoje. Persona secundária: pequena equipe que precisa compartilhar biblioteca. **Não** priorizar marketplace público |
| **Humano?** | Sim |

### D-16 — Ferramenta pessoal, produto ou open source

| | |
|---|---|
| **Estado** | `OPEN` |
| **Observação original** | Não presumir política de publicação/licença |
| **Evidências** | O arquivo `LICENSE` (MIT) **existe** nas branches de desenvolvimento do Studio e do Forge, com a marca explicitamente fora da MIT em `THIRD_PARTY_NOTICES.md`. Porém: (a) o endpoint `GET /repos/BloomRX/<repo>/license` retorna **404 nos quatro repositórios**, inclusive neste — o GitHub não detecta licença porque o arquivo não está na branch padrão; (b) **este repositório (`Lia-AgentHub`) não tem `LICENSE` em nenhuma branch** |
| **Alternativas** | (a) MIT público como os demais; (b) fonte disponível, licença restritiva; (c) fechado |
| **Recomendação Agent 0** | Nenhuma — **é decisão do responsável**. Observo apenas que (a) é coerente com o ecossistema e que a separação marca/código já está resolvida no kit |
| **Humano?** | **Sim** |

### D-17 — Sistemas operacionais do primeiro MVP

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Recomendação Agent 0** | **Windows 10/11 x64 obrigatório; Linux x64 secundário** (ambiente de desenvolvimento das sessões). macOS **não** no MVP (sem máquina de validação, exige notarização, sem demanda). Mobile **não**. WSL2: suporte acidental, não declarado |
| **Humano?** | **Sim** |

### D-18 — Nível de risco aceitável ao testar MCPs e código de terceiros

| | |
|---|---|
| **Estado** | `OPEN` |
| **Observação original** | A pesquisa apresenta limites técnicos; a política final é humana |
| **Evidências** | `SECURITY-AND-TRUST-MODEL.md` §3.4, §7, §11, §13. Análise estática de script tem confiabilidade **nenhuma**. Sete riscos residuais ficam abertos |
| **Alternativas** | (a) nenhum teste no Hub (recomendado no MVP); (b) teste em VM descartável por ação explícita; (c) teste em contêiner; (d) teste em processo separado |
| **Recomendação Agent 0** | **(a) para o MVP.** Qualquer outra opção exige prova em Windows real e aceite explícito do risco. **Nenhuma opção permite execução automática em importação** |
| **Humano?** | **Sim, obrigatório** |

### D-19 — Quais dados podem sair da máquina

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Observação original** | Local-first não resolve todos os casos de egress |
| **Evidências** | MVP não tem nenhuma operação de rede. `egress.consentRequired: true` por padrão; `destinations[]` explícito |
| **Recomendação Agent 0** | **Nenhum dado sai da máquina no MVP.** Quando houver (Fase 3+): declaração por capacidade, exibição do destino **na tela** antes do envio, e opt-in por ato — não por configuração global. **Nunca** enviar memória de convivência, caminho de projeto ou conteúdo de capacidade sem ato do usuário |
| **Humano?** | **Sim** |

### D-20 — Recursos não redistribuíveis mas referenciáveis

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Observação original** | Separar metadados, código, conteúdo, pesos e licenças |
| **Evidências** | Forge já trata isso: item externo **sem `LICENSE`** é registrado com `license: null` e `trust: unreviewed`, e o README diz "não copiar". Mesmo padrão serve ao Hub |
| **Recomendação Agent 0** | Criar o conceito explícito de **ponteiro** vs. **cópia** no registro: `source.kind: "pointer"` significa *"registro de metadado; nenhum byte foi copiado"*, com `redistributable: false`. Exportar capacidade-ponteiro gera um pacote **sem payload**, apenas com instruções de obtenção e o hash esperado. **Nunca** embutir conteúdo não redistribuível |
| **Humano?** | **Sim** |

---

## Parte III — Decisões incorporadas pela Fase 0 (D-21 a D-24)

Estas não estavam no briefing; surgiram da pesquisa e precisam de registro para não ficarem implícitas.

### D-21 — Formato do pacote de distribuição

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão** | Qual o formato de pacote exportável? |
| **Recomendação Agent 0** | ZIP com extensão `.lia-capability`, contendo `manifest.json` obrigatório na raiz, `payload/`, `provenance.json`, `NOTICE` (quando exigido), `THIRD_PARTY_NOTICES.md`, e `signatures/` reservado. Inspecionável com o Explorer do Windows. `formatVersion` independente da versão da capacidade |
| **Alternativas** | diretório puro (perde atomicidade); tar.gz (menos nativo no Windows); OCI artifact (exige ferramenta) |
| **Humano?** | **Sim** |

### D-22 — Escala de confiança e quem promove

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão** | Como representar confiança e quem pode mudá-la? |
| **Recomendação Agent 0** | Adotar `unreviewed / user-provided / reviewed-external / first-party` do Forge. **Só humano promove para `reviewed-external`**, com autor + data + método + achados. Scanner verde gera `evidence`, não `trust`. Nunca promover por tempo, popularidade ou ausência de incidente |
| **Humano?** | **Sim** |

### D-23 — Mecanismo de detecção obrigatório no import

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão** | Qual verificação é obrigatória (não opcional) na importação? |
| **Recomendação Agent 0** | **Três, todas determinísticas e baratas:** (1) varredura de caracteres invisíveis Unicode com **rejeição**; (2) contenção de caminho C1–C12 com rejeição; (3) validação de frontmatter contra a spec Agent Skills. Nenhuma delas afirma segurança — afirmam *bem-formação*. **Análise estática de script não é oferecida como proteção** |
| **Humano?** | **Sim** (confirmar o conjunto mínimo) |

### D-24 — Diretório de troca entre Hub e hosts

| | |
|---|---|
| **Estado** | `RECOMMENDED` |
| **Questão** | Onde o Hub publica e onde o host lê? |
| **Recomendação Agent 0** | `%USERPROFILE%\Lia\Comum\Capacidades\` com `index.json` + `<id>\<versao>\`. Hub escreve; host lê. **Nenhum escreve na pasta do outro.** Escrita atômica obrigatória. Marcador `.lia-home` para validar raiz |
| **Alternativas** | pasta do host; diretório dentro do app; banco compartilhado (rejeitado) |
| **Humano?** | **Sim** |

---

## Resumo por estado

| Estado | IDs |
|---|---|
| `OPEN` | **D-01**, **D-05**, **D-16**, **D-18** |
| `RECOMMENDED` | D-02, D-03, D-04, D-06, D-07, D-08, D-09, D-10, D-11, D-13, D-14, D-15, D-17, D-19, D-20, D-21, D-22, D-23, D-24 |
| `DEFERRED` | **D-12** |
| `APPROVED` | **nenhuma** |

**As quatro decisões que realmente bloqueiam o início da Fase 1:**

| # | Decisão | Por que bloqueia |
|---|---|---|
| 1 | **D-13** (escopo do MVP) | É a autorização |
| 2 | **D-14** (stack) | Define o que será construído |
| 3 | **D-03** (formato) | Define o schema e o pacote |
| 4 | **D-06** (armazenamento) | Define o que fica no disco do usuário |

**As duas decisões que bloqueiam apenas a Fase 4:** `D-05` e `D-18`.

---

## Como atualizar este registro

Para cada decisão:
1. anexar evidências e fontes;
2. listar opções reais e consequências;
3. registrar recomendação do Arena separadamente da decisão humana;
4. registrar decisão aprovada, responsável e data somente após aceite;
5. não transformar recomendação ou silêncio em aprovação.

**Nenhuma decisão aberta bloqueia o início da Fase 0** (concluída). Questões de produto/risco que exigem aceite devem ser resolvidas antes da implementação que delas dependa.

### Template para registrar aceite

```markdown
### D-XX — <título>

**Estado:** APPROVED | REJECTED | DEFERRED
**Decisão:** <o que foi decidido, em uma frase>
**Decidido por:** <pessoa>
**Data:** AAAA-MM-DD
**Base:** <documento/evidência consultados>
**Condições:** <o que precisa valer para a decisão continuar válida>
**Revisão prevista:** <quando reavaliar, se aplicável>
```

---

## Referências

- `docs/research/REPOSITORY-AND-BRANCH-AUDIT.md` — evidência de repositórios, branches e módulos
- `docs/research/INTEGRATION-CANDIDATES.md` — evidência externa (Agent Skills, MCPVault, Graphify, ai-memory, uv, CanIRunAI)
- `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` — fronteiras, modelo de dados, contratos
- `docs/architecture/SECURITY-AND-TRUST-MODEL.md` — ameaças, confiança, limites de automação
- `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` — armazenamento, backup, portabilidade
- `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` — stack e plataforma
- `docs/product/MVP-AND-ROADMAP.md` — escopo e fases
- `docs/PHASE-0-FINAL-REPORT.md` — relatório executivo e pendências
- `KIT-PROJETO-NOVO.zip` — padrões de marca, pastas e licenciamento
