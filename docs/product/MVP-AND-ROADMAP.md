# MVP e roadmap

**Documento:** `docs/product/MVP-AND-ROADMAP.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Branch:** `arena/a92004be-lia-agenthub`
**Status:** `PROPOSED` — requer aprovação humana (`D-13`). **Não autoriza implementação.**
**Data:** 2026-11-15 (UTC)

---

## 1. O teste do MVP

> **O MVP é o menor produto que faz alguém dizer "eu não consigo mais trabalhar sem isso" — sozinho, offline, sem Studio e sem Forge.**

Concretamente, o MVP precisa que esta sequência funcione numa máquina Windows limpa, **sem internet, sem conta, sem Python instalado**:

```
1. Abrir o Agent Hub
2. Receber uma SKILL.md de um colega (pendrive, pasta, zip)
3. Importar e ver: o que é, de onde veio, o que declara, o que contém,
   o que as verificações viram e NÃO viram
4. Revisar o texto e registrar a decisão
5. Empacotar e exportar como .lia-capability
6. Copiar para .agents/skills/ de um projeto
7. O Studio (ou Claude Code, ou Codex) usa — sem saber que o Hub existiu
```

Se essa sequência funciona, o produto tem valor. Se ela exige o Studio instalado, não tem.

---

## 2. O que o MVP **não** faz — e por quê

Cada exclusão tem motivo técnico, não de prazo:

| Excluído | Motivo real |
|---|---|
| **Executa qualquer capacidade** | Não há sandbox comprovado em Windows. `D-05`/`D-18` bloqueiam. Prometer "testado" sem sandbox é a mentira mais cara que o produto poderia contar |
| **Conecta MCP** | Conexão é do host. O Hub catalogaria um MCP — mas sem catálogo remoto e sem execução, isso é uma ficha de metadado, não uma funcionalidade |
| **Catálogo remoto / marketplace** | `D-12`. Exige backend, conta, moderação, custo e política de conteúdo |
| **Busca semântica / embeddings** | Exige modelo, rede e vetor — três coisas que contradizem local-first de forma gratuita. Busca textual resolve |
| **Assistência de IA para escrever Skill** | Exige provider, chave, custo e egress. É a funcionalidade que mais facilmente transforma um app honesto num app que "acha" coisas |
| **Importação por URL ou git** | Rede + consentimento + política de egress. Pode virar Fase 3 |
| **Sincronização / nuvem** | Contradiz a regra nº 3 (o dado é do usuário, em pasta visível) |
| **App mobile** | `PLATFORM-AND-TECHNOLOGY-DECISION.md` §4.3 |
| **Editor de código embutido** | O usuário tem editor. O Hub edita `SKILL.md` e metadado |

---

## 3. MVP — escopo mínimo

### 3.1 Capacidades obrigatórias (M1–M8)

| # | Capacidade | Por que é obrigatória | Lacuna coberta | Teste de aceite |
|---|---|---|---|---|
| **M1** | **Biblioteca local em arquivos** com estrutura `Lia\AgentHub\Biblioteca\<id>\` | É o produto. Sem ela não há nada | L-01 | Copiar a pasta para outra máquina e ler tudo em editor de texto |
| **M2** | **Importar + inspecionar** com relatório honesto de verificações | É o que separa o Hub de um gerenciador de arquivos | L-01, L-02, L-06 | Skill com `U+202E` em bloco de código → **rejeitada** com linha e coluna. Skill com **ZWNJ em texto persa** → **preservada**, sem rejeição (`§3.2` do doc de segurança) |
| **M3** | **Validador estrutural** de Agent Skills (frontmatter contra a spec) | Único verificador com confiabilidade alta | L-02 | Skill com `name` de 65 chars ou hífen duplo → erro com a regra citada |
| **M4** | **Contenção de caminho** (C1–C12 do doc de segurança) | Vetor real já explorado em projeto público | L-02 | Pacote com `../../evil.md` e com symlink → rejeitado antes de extrair |
| **M5** | **Proveniência** (`provenance.json` + `source`) e **licença por camada** | Resolve a lacuna central e o risco jurídico | L-01, L-04 | Toda capacidade importada tem `source.upstream` + `commit` + `contentHash`. Export **privado** com `license: null` funciona; export **público** é recusado |
| **M6** | **Versionamento** (semver + `contentHash` + `history.json` + diff entre versões) | Atualização sem diff é atualização silenciosa | L-07 | Duas versões da mesma Skill → diff de corpo, `description` e `declaredPermissions` |
| **M7** | **Empacotar / exportar** `.lia-capability` com `manifest.json` + hashes | É o formato de distribuição do produto | L-03 | Pacote abre no Explorer; `payload.files[]` confere; arquivo a mais no zip → erro |
| **M8** | **Catálogo publicável** `Comum\Capacidades\index.json` — **publicar + validar + leitor de referência** (`§3.1.1`) | É o contrato de distribuição, e o único artefato que sobrevive ao Hub | L-05 | O índice valida contra o schema; **o leitor de referência roda com o Hub desinstalado** e imprime `trust`, `license`, `requirements` |

#### 3.1.1 M8 — os quatro níveis que a Fase 0 confundiu

A Fase 0 dizia "catálogo publicável **que o host lê**" no MVP, e ao mesmo tempo colocava
"integração com hosts" na Fase 3. As duas coisas não podem ser verdade. Separação corrigida:

| Nível | O que é | Depende de Studio/Forge? | Fase |
|---|---|---|---|
| **IDX-1 — Publicar** | O Hub **escreve** `Comum\Capacidades\index.json` + `index.schema.json`, atomicamente, quando a biblioteca muda | **Não** | **MVP (M8)** |
| **IDX-2 — Validar** | O Hub valida o índice contra o próprio schema e **recusa publicar** se estiver inconsistente | **Não** | **MVP (M8)** |
| **IDX-3 — Consumir de referência** | Um **leitor mínimo documentado** (~50 linhas, fora do Hub) prova que o contrato é consumível sem o Hub | **Não** | **MVP (M8)** |
| **IDX-4 — Integrar de verdade** | Studio e Forge passam a ler o índice e exibir `trust`/`license`/`requirements` | **Sim** | **Fase 3** |

**Por que IDX-3 está no MVP e não na Fase 3:** sem ele, M8 é a afirmação de que um contrato
funciona sem que ninguém jamais o tenha lido. O leitor de referência é barato e é o que
transforma "publicável" em **verificado**.

**Por que IDX-4 não está no MVP:** requer alterar Studio e Forge — proibido nesta fase e fora do
escopo do Hub.

**Critérios de aceite de M8:**

| Critério | Verificação |
|---|---|
| Escrita atômica | Kill do processo no meio não deixa `index.json` truncado |
| Valida contra o schema | `index.schema.json` versionado; validação no publish |
| Consumível sem o Hub | Leitor de referência roda com o Hub **desinstalado** |
| Declara o que não sabe | Campos desconhecidos são `null`, nunca valor inventado |
| **Não é assinado** | Nenhum campo `signed`; nenhuma pasta `signatures/` é lida |

### 3.2 Capacidades desejáveis se houver folga (IDX-1–IDX-3)

| # | Capacidade | Valor | Risco se entrar |
|---|---|---|---|
| **N1** | Criar Skill a partir de template (o kit já traz `skill-exemplo--SKILL.md`) | Alto para autoria | Duplica o editor do Studio — mitigar deixando claro "biblioteca", não "projeto" |
| **N2** | Coleções (agrupar capacidades por domínio/projeto) | Médio | Nada relevante |
| **N3** | Importar diretório de conhecimento (Markdown) como capacidade `knowledge` | Médio — atende o caso Obsidian sem depender dele | Pode inflar escopo para indexação; limitar a "declarar a fonte", não indexar |

### 3.3 Critérios de aceite do MVP (todos precisam passar)

**Do produto:**
1. Abre em máquina Windows **sem Python, sem Node, sem git e sem console**.
2. A primeira abertura **não pede nada** além do que só o usuário pode dar (nada, no MVP).
3. Funciona com internet ausente; nenhuma requisição de rede em operação normal.
4. Funciona com Studio, Forge e Waifu ausentes.
5. O trabalho do usuário está em pasta que ele acha, copia e apaga sozinho.
6. `--diagnostico` imprime cada caminho resolvido, a fonte que decidiu e ✓/✗ de existência.
7. Desinstalar remove o programa e **pergunta** sobre os dados, mostrando tamanho.
8. Nenhum segredo em repositório, log, índice ou interface.
9. O README diz o que **não** está pronto com a mesma clareza do que está.
10. Nada no app afirma ter executado o que não executou.

**Do domínio:**
11. Núcleo (L3) não importa I/O, framework, rede nem SO — verificado por teste de camadas.
12. Toda regra de validação tem teste com entrada inválida.
13. Import cancelado **não** deixa resíduo fora do temporário.
14. `null` nunca é convertido em `0`, `false` ou "não" na exibição.

**Da honestidade (os mais importantes):**
15. Nenhuma tela usa "seguro", "aprovado", "validado" ou "testado" para descrever análise estática.
16. Relatório de import lista explicitamente o que **não** foi verificado.
17. Exportar capacidade `unreviewed` produz nome de arquivo com sufixo `-NAO-REVISADO`.
18. Capacidade com `scripts/` é sinalizada como "contém código executável — não executado pelo Hub".

### 3.4 O que prova "MVP pronto"

| Evidência | Quem produz |
|---|---|
| Execução real no Windows do `.exe`, com abrir/fechar/reabrir | **Dev** (não a sessão) |
| Sequência de §1 executada ponta a ponta numa máquina limpa | **Dev** |
| Biblioteca copiada para outra máquina e lida sem o Hub | **Dev** |
| Suíte de testes verde em Linux (CI) | Sessão |
| Teste de camadas provando que L3 é puro | Sessão |
| Teste negativo de path traversal, symlink, zip-slip, Unicode invisível | Sessão |

**Regra do kit:** teste automatizado verde **não** é PASS de produto. O gate é Windows real. A sessão nunca declara "funciona no Windows" — declara *"escrito para Windows, não executado — gate pendente"*.

---

## 4. Fases

### Fase 0 — Pesquisa, auditoria, especificação ✅ (este trabalho)

Entregáveis: os nove documentos desta branch. **Sem código.**

**Critério de saída:** revisão humana aprova, ajusta ou rejeita escopo, fronteiras, arquitetura, segurança e MVP.

### Fase 1 — Núcleo e biblioteca (MVP)

| Entrega | Notas |
|---|---|
| Domínio puro (L3) | `Capability`, `Provenance`, `License`, `TrustLevel`, `ValidationResult` |
| Validador Agent Skills | Contra a spec; mensagens citando a regra |
| Contenção de caminho | C1–C12 |
| Import + quarentena + relatório | Fluxo de 6 passos de `SECURITY-AND-TRUST-MODEL.md` §8 |
| Biblioteca + `index.json` | Derivado; disco vence |
| Pacote `.lia-capability` | `manifest.json`, hashes, `NOTICE` |
| Proveniência, licença, versão, diff | Modelo de dados completo |
| CLI de desenvolvimento | `validate`, `pack`, `export`, `diagnostico` |
| Interface local | Lista, import, revisão, diff, export |
| `.exe` | PyInstaller, por usuário, sem admin |

**Divisão F1a/F1b/F1c** conforme `PLATFORM-AND-TECHNOLOGY-DECISION.md` §5.3.

### Fase 2 — MCP Workshop (somente catálogo)

**Só o que é honesto sem executar:**

| Entrega | O que **não** faz |
|---|---|
| Ficha de MCP: fonte, commit, comando de inicialização, **nomes** de variáveis de ambiente, capabilities declaradas, requisitos | Não conecta, não inicia processo, não testa |
| Análise estática de manifesto MCP (`server.json`-like) | Não valida comportamento |
| Modelo de egress declarado | Não verifica |
| Exportação de configuração para o host (bloco JSON para o usuário copiar) | Não escreve na config de outro app |

**Por que esta fase pode existir sem execução:** catalogar um MCP é catalogar metadado. O host conecta. É o mesmo padrão do M1–M8.

### Fase 3 — Distribuição e integração com hosts

| Entrega | Observação |
|---|---|
| `Comum\Capacidades\index.json` estável e versionado | Contrato de leitura |
| Guia de integração para o Studio (ler índice + copiar `.agents/skills/`) | **Documentação, não alteração do Studio** |
| Guia de integração para o Forge (consumir `mcp-server`/`cli`) | Documentação |
| Importação por URL/git **opt-in**, com consentimento de egress | Requer `D-12` |
| Assinatura de pacote (minisign/Sigstore) | Requer pesquisa pendente |

### Fase 4 — Test Lab (bloqueado)

**Pré-requisitos não negociáveis:**

1. Decisão humana sobre isolamento (`D-05`) com **prova** em Windows.
2. Decisão humana sobre risco aceitável (`D-18`).
3. Modelo de ameaças específico do sandbox — o atual cobre import, não execução.
4. Prova de que cancelar/crash **não** deixa processo, rede ou arquivo residual.

**Se essas quatro não existirem, esta fase não começa** — não importa a pressão.

### Fase 5 — Ecossistema

| Entrega | Condição |
|---|---|
| SDK/CLI público | Só se houver consumidor externo real (`D-08`) |
| Catálogo remoto opcional | Só com `D-12` e plano de custo/moderação |
| Comunidade/publicação | Só com `D-16` definido (open source vs. produto) |
| API local | Só se arquivo provar insuficiente (`D-09`) |

---

## 5. Roadmap em uma tela

```
FASE 0  ████████████ CONCLUÍDA (documentação)
        └─ gate: revisão humana

FASE 1  ░░░░░░░░░░░░ MVP — biblioteca, import, validação, pacote
        F1a domínio + CLI      (valor sem UI)
        F1b interface web      (valor com navegador)
        F1c .exe Windows       (valor "baixou, abriu, funciona")
        └─ gate: execução real no Windows pelo Dev

FASE 2  ░░░░░░░░░░░░ MCP Workshop (catálogo, sem conectar)
        └─ gate: revisão de que "catalogar ≠ testar"

FASE 3  ░░░░░░░░░░░░ Distribuição + guias de integração
        └─ gate: um host real consumiu o índice

FASE 4  ░░░░░░░░░░░░ Test Lab  ⛔ BLOQUEADO
        └─ gate: D-05 + D-18 + modelo de ameaças + prova de não-resíduo

FASE 5  ░░░░░░░░░░░░ SDK, catálogo remoto, comunidade
        └─ gate: D-08, D-12, D-16
```

---

## 6. Comparação de escopos candidatos

Para deixar a decisão de `D-13` explícita, três escopos possíveis:

| Escopo | Conteúdo | Esforço relativo | Valor sozinho | Risco |
|---|---|---|---|---|
| **A — Só biblioteca + pacote** | M1, M5, M6, M7 (sem importação interativa, sem validador rico) | 1× | Médio — útil para quem já sabe o que quer | Baixo |
| **B — MVP recomendado** | M1–M8 | 2,5× | **Alto** — o produto tem opinião sobre confiança | Baixo-médio |
| **C — MVP + Test Lab** | B + execução isolada | 5–8× (estimativa) | Alto, mas com afirmação que não se sustenta | **Alto** |

**Recomendação: B.** A é um utilitário; C é uma promessa que não se cumpre hoje. **B é o único que entrega a proposta de valor do produto — confiança verificável — sem afirmar o que não pode.**

---

## 7. O que pertence a outros produtos (fora do Hub)

Listado explicitamente para que nenhuma fase futura os absorva:

| Item | Dono | Por quê |
|---|---|---|
| Orquestração de agentes, sessões, handoff | **Studio** | Já implementado/contratado lá |
| Execução de tarefas, jobs, cancelamento | **Studio** | Idem |
| Permissões e approvals em runtime | **Studio/Forge/Project** | Cada host tem sua política |
| Cofre de credenciais | **Host** | Cada um já tem o seu |
| Conexão MCP em produção | **Host** | Ciclo de vida é do host |
| Produção e validação de assets | **Forge** | Especialização |
| Providers e pipelines de geração | **Forge** | Especialização |
| Catálogo e admissão de modelos/pesos | **Forge** (+ Project catálogo mestre) | Já implementado |
| Download e hash de pesos | **Forge** | Já implementado |
| Memória de convivência | **Project** | Privada do usuário |
| Memória de sessão de agente | **Studio** | Contexto de execução |
| QA de gameplay, build, release de jogo | **Studio** | Especialização |
| QA visual de asset | **Forge** | Especialização |
| Runtime de agente | **Ninguém no Hub** | Proibido por arquitetura |

---

## 8. Ideias futuras (não comprometidas)

Registradas para não se perderem, **sem** virar promessa:

| Ideia | Valor potencial | Por que não agora |
|---|---|---|
| Análise de licença assistida (detecção de SPDX, comparação de compatibilidade) | Alto | Não é automatizável de forma confiável; exigiria base de regras jurídicas |
| Grafo de dependências entre capacidades | Médio | Só faz sentido com biblioteca grande |
| Índice de conhecimento local (capacidade `knowledge` com busca textual) | Médio | Indexação é Fase 2+ |
| Compatibilidade verificada com hosts (matriz real, não declarada) | Alto | Exige que hosts informem; nada a medir hoje |
| Análise de hardware local para `requirements` | Médio | `CanIRunAI` é `REFERENCE`; medir hardware é do host |
| Comparação entre duas versões de um MCP (tool surface diff) | Alto para segurança | Fase 2+, com catálogo de MCP existindo |
| Assinatura de pacote | Alto | Pesquisa pendente |
| SBOM por pacote | Médio | Fase 2 |

---

## 9. Riscos do roadmap

| # | Risco | Consequência | Mitigação |
|---|---|---|---|
| R-01 | **Escopo inflar para Test Lab antes da Fase 4** | O produto passa a afirmar segurança que não tem | Fase 4 marcada como bloqueada, com pré-requisitos escritos |
| R-02 | **MVP virar "marketplace"** por pressão de visão | Perde local-first, ganha backend e custo | §2 e §7 explícitos; `D-12` exige decisão humana |
| R-03 | **Duplicar o editor do Studio** | Dois editores, confusão de usuário | Fronteira: Hub = biblioteca/pacote; Studio = projeto. Precisa aparecer na interface |
| R-04 | **Domínio impuro por conveniência** | Perde a única garantia arquitetural forte | Teste de camadas como gate de merge |
| R-05 | **Empacotamento Windows travar a entrega** | Valor pronto, produto não entregue | F1a/F1b entregam valor antes do `.exe` |
| R-06 | **Falso positivo de antivírus** minar confiança | Usuário não instala | Declarado; build reproduzível; assinatura quando houver orçamento |
| R-07 | **"MVP" crescer para 20 funcionalidades** | Nada fica pronto | Lista M1–M8 fechada; N1–N3 só com folga; §2 é a cerca |

---

## 10. Conclusões

1. **O MVP tem oito capacidades e todas cabem no que já está especificado.** Nenhuma exige execução, rede, modelo ou conta.
2. **O valor central é a confiança com evidência** — e ele é entregue por M2, M3, M5 e M7, não por execução.
3. **O MVP funciona sozinho** porque o contrato é arquivo. Isso não é uma aspiração: é a consequência de T1–T5 na arquitetura.
4. **Test Lab é a fase 4 e está bloqueada por decisão pendente**, não por tempo. Colocá-la no MVP transformaria o produto em algo que afirma o que não pode provar.
5. **Três escopos foram comparados** e o recomendado (B) é o do meio: mais que um utilitário, menos que uma promessa.
6. **A cerca é explícita:** §2 (o que não faz), §7 (o que é de outro produto), §9 (riscos). Escopo sem cerca não é escopo.

---

## Referências

- `docs/research/REPOSITORY-AND-BRANCH-AUDIT.md` §5 — as oito lacunas que o MVP cobre
- `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §1.3 — teste T1–T5; §8 — formato de pacote
- `docs/architecture/SECURITY-AND-TRUST-MODEL.md` §8 — fluxo de importação; §11 — Test Lab bloqueado
- `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` §3 — layout; §5.4 — interoperabilidade com Studio
- `docs/product/PLATFORM-AND-TECHNOLOGY-DECISION.md` §5.3 — F1a/F1b/F1c
- `docs/DECISION-REGISTER.md` — `D-05`, `D-09`, `D-12`, `D-13`, `D-18`
- `KIT-PROJETO-NOVO.zip` → `APP-WINDOWS/GUIA-APP-NOVO.md` §7 ("pronto é quando"); §6 ("o que não foi verificado")
