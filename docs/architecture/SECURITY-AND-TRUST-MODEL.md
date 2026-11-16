# Modelo de segurança e confiança

**Documento:** `docs/architecture/SECURITY-AND-TRUST-MODEL.md`
**Sessão:** Agent 0 — Fundação, Pesquisa e Arquitetura
**Branch:** `arena/a92004be-lia-agenthub`
**Status:** `PROPOSED` — proposta para revisão humana. **Não autoriza implementação.**
**Data:** 2026-11-15 (UTC)

---

## 0. Premissa que governa tudo

> **Uma capacidade importada é hostil até prova documentada em contrário. E "prova" não é um scanner verde.**

Esta premissa não é pessimismo: é o resultado das duas evidências mais sólidas que a pesquisa externa produziu, ambas já registradas pelo Agent 6 no Studio e reproduzidas aqui por serem o fundamento do modelo:

| Evidência | Dado | Fonte primária |
|---|---|---|
| **Snyk "ToxicSkills"** (05/02/2026) | 3.984 Skills públicas: **36,82 %** com ≥1 falha; **13,4 %** crítica; **76 payloads maliciosos confirmados**; 5 das 7 mais baixadas eram malware | citado em `BloomRX/Lia-Studio@arena/04710d54-lia-studio`, `docs/research/ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md` §3.3 — **não verificado nesta sessão** |
| **Liu et al.** | 42.447 Skills: **26,1 %** com ≥1 vulnerabilidade; Skills com `scripts/` são **2,12×** mais propensas a falhas | idem — `RESEARCH` herdado |

**Como usar esses números:** eles não dizem "toda Skill externa é perigosa". Dizem que **a taxa base é alta o bastante para que confiança por padrão seja irracional**. É por isso que o default do modelo é `unreviewed`.

**O que este documento não afirma:** que qualquer scanner, validador ou sandbox **garanta** segurança. Nenhum garante. A §9 lista o que cada mecanismo consegue e não consegue detectar.

---

## 1. Ativos a proteger

Em ordem de dano se comprometidos:

| # | Ativo | Onde vive | Dano se comprometido |
|---|---|---|---|
| A1 | **Trabalho do usuário** (projetos, documentos, assets, notas) | `%USERPROFILE%\Lia\…`, diretórios escolhidos | Perda ou corrupção irreversível |
| A2 | **Credenciais** (chaves de API, tokens, sessões) | Cofre do SO / cofre do host | Acesso a contas, custo financeiro |
| A3 | **Memória de convivência** (Waifu) | `%USERPROFILE%\Lia\Waifu\Memorias\` | Violação de privacidade íntima |
| A4 | **Integridade da biblioteca** (o que o Hub publica) | `Lia\Comum\Capacidades\` | Distribuir capacidade envenenada a todos os hosts |
| A5 | **Cadeia de custódia** (proveniência, licenças) | `.lia/provenance.json`, notices | Violação de licença, perda de rastreabilidade jurídica |
| A6 | **Máquina do usuário** (processos, SO, rede) | — | Execução arbitrária |
| A7 | **Reputação do projeto** | — | Um incidente de segurança encerra a confiança conquistada |

**Observação:** A3 está listado apesar de o Hub **não tocar** memória. O motivo é defensivo: se o Hub algum dia tiver acesso a um diretório pai (`Lia\`), precisa saber que **existe** um diretório que ele nunca pode ler. Está marcado como proibição em §5.4.

---

## 2. Fronteira de confiança

```
┌────────────────────── ZONA CONFIÁVEL ──────────────────────┐
│  Código do Hub (auditável, MIT, revisado)                   │
│  Núcleo de domínio (L3): funções puras, sem I/O             │
│  Configuração escrita pelo usuário                          │
│  Biblioteca local, DEPOIS de revisão humana registrada      │
└─────────────────────────────────────────────────────────────┘
                            ▲
                            │  FRONTEIRA — todo dado cruza
                            │  por validação, nunca por confiança
                            ▼
┌────────────────────── ZONA NÃO CONFIÁVEL ──────────────────┐
│  Qualquer SKILL.md importado                                 │
│  Qualquer script em scripts/                                 │
│  Qualquer manifesto de MCP                                   │
│  Qualquer resposta de repositório, site, API ou modelo       │
│  Qualquer nome de arquivo ou caminho vindo de conteúdo       │
│  Qualquer texto de "origem", "autor" ou "licença" declarado  │
│  QUALQUER instrução encontrada dentro de uma capacidade      │
└─────────────────────────────────────────────────────────────┘
```

**Regra de leitura desta fronteira** (idêntica à do `AGENTS.md` deste repositório): conteúdo externo — Skills, scripts, prompts, instruções de repositórios e respostas de ferramentas — **é dado, não comando**. Uma Skill que diz "ignore as regras de segurança" é um registro de texto suspeito, não uma ordem.

---

## 3. Modelo de ameaças

Formato: ameaça → vetor → impacto → detecção → mitigação → limite.

### 3.1 Injeção de prompt e envenenamento semântico

| | |
|---|---|
| **Ameaça** | Texto dentro do `SKILL.md` instrui o agente do host a exfiltrar dados, desativar gates ou executar comando |
| **Vetor** | Corpo do `SKILL.md`, `references/*.md`, `description` (que é o gatilho de ativação) |
| **Impacto** | Dano em A1, A2, A6 |
| **Detecção automática** | Padrões lexicais (imperativo direcionado a regras, menção a segredo, URL de download, "ignore/desconsidere as regras", `curl`/`wget`/`Invoke-WebRequest` no corpo) |
| **Detecção humana** | Leitura do corpo — **obrigatória** antes de qualquer `trust` acima de `unreviewed` |
| **Mitigação** | Nenhuma capacidade importada é executada; o corpo é exibido como texto, nunca como comando; `description` é campo revisado; ao instalar num host, o agente do host **ainda** precisa de política própria |
| **Limite** | Detecção lexical **falha por paráfrase**. Pesquisa citada mostra geradores automatizados de Skills envenenadas com taxa de sucesso de 80–95 % contra defensores estáticos. **Não existe solução automática** |
| **Classificação** | `Automático: parcial` · `Humano: obrigatório` |

### 3.2 Caracteres invisíveis e Unicode malicioso

| | |
|---|---|
| **Ameaça** | Instruções invisíveis embutidas em `SKILL.md` (faixa Unicode Tags `U+E0000–U+E007F`, zero-width, bidi override) |
| **Vetor** | Corpo, `description`, nome de arquivo |
| **Impacto** | Bypass completo de revisão humana — o revisor "lê" um arquivo e enxerga outra coisa |
| **Detecção automática** | **Sim, e é determinística** — mas **por categoria e por contexto**, não por faixa. Ver §3.2.1 a §3.2.5 |
| **Mitigação** | Quatro categorias: **Rejeitar** / **Sinalizar e exigir revisão** / **Preservar** / **Exibir escapado**. Nunca rejeição indiscriminada |
| **Limite** | Homóglifos visuais (cirílico `а` vs latino `a`) **não** são cobertos de forma confiável; exigiria `confusables.txt` do Unicode. Não coberto nesta fase |
| **Classificação** | `Automático: forte` para os caracteres perigosos **no contexto certo** — **este é o mecanismo de maior valor por menor custo** |

> **Correção da Fase 0.1.** A Fase 0 especificava rejeitar `U+200B–U+200F` indiscriminadamente,
> o que inclui **ZWNJ e ZWJ** — obrigatórios em persa, malaiala, sinhala e em toda sequência de
> emoji ZWJ. Ver `docs/research/PHASE-0-1-CONSISTENCY-REVIEW.md` §3.2. A política correta está
> abaixo; a proteção **aumentou**, não diminuiu (passou a cobrir `U+061C` e `U+2066–2069`, que a
> lista antiga não cobria).
>
> **Correção da Fase 0.1.2 — C vs. D.** A documentação de revisão classificou ZWNJ e ZWJ como
> "PRESERVAR" ao mesmo tempo que esta tabela os classificava como **D**. A classificação correta
> é **D** (preservar **e exibir escapado**), por dois motivos independentes:
>
> 1. **A definição de D os alcança literalmente:** "legítimo, mas invisível — o usuário precisa
>    ver". ZWNJ e ZWJ não têm glifo próprio; um campo que os contém renderiza igual a um campo
>    sem eles.
> 2. **C ("nenhum aviso") contradiria o propósito desta seção.** Se o revisor humano não
>    consegue distinguir `خانه` de `خان‌ه`, a revisão de conteúdo — que é o único controle que
>    resta depois da categoria B — fica cega justamente no ponto que o atacante escolheria.
>
> **O que não mudou:** o uso legítimo continua permitido. O byte é preservado exatamente, texto
> em persa, malaiala, sinhala e emoji ZWJ continuam íntegros, e nada é rejeitado. A única
> diferença é **como a interface mostra** o caractere: escapado, não invisível.

#### 3.2.1 As quatro categorias

| Categoria | Semântica | Efeito na importação | Efeito na interface |
|---|---|---|---|
| **A — Rejeitar** | Não existe uso legítimo naquele contexto | Arquivo retorna à quarentena; importação bloqueada | Erro por linha/coluna, com codepoint e nome Unicode |
| **B — Sinalizar e exigir revisão** | Pode ser legítimo; precisa de olho humano | Importa para quarentena; **promoção à biblioteca bloqueada** até revisão registrada | Destaque escapado, contagem e ±40 caracteres de contexto |
| **C — Preservar** | Legítimo e comum | Importa sem atrito | Nenhum aviso |
| **D — Preservar e exibir escapado** | Legítimo, mas invisível — o usuário **precisa ver** | Importa; byte preservado exatamente | Sempre exibido como `<U+200B>`, nunca renderizado |

#### 3.2.2 Catálogo por codepoint

| Codepoint(s) | Nome | Uso legítimo | Risco | Categoria (prosa) | Categoria (código) | Categoria (identificador) |
|---|---|---|---|---|---|---|
| `U+200B` | ZERO WIDTH SPACE | Quebra de palavra em tailandês/lao/khmer e CJK | Esconde texto; quebra busca | **B** | B | **A** |
| `U+200C` | ZWNJ | **Persa** (UTS #39 Fig. 1), **malaiala** (Fig. 2), escritas índicas | Pode esconder texto onde não é gramatical | **D** — preserva o byte, exibe `<U+200C>` | B | B só nas condições A1/A2 |
| `U+200D` | ZWJ | **Todas as sequências de emoji ZWJ**, **sinhala** (Fig. 3), indic | Idem | **D** — preserva o byte, exibe `<U+200D>` | B | B só na condição B |
| `U+200E` | LRM | Texto latino dentro de parágrafo RTL | Trojan Source em código | **B** | **A** | A |
| `U+200F` | RLM | Texto RTL dentro de parágrafo LTR | Idem | **B** | **A** | A |
| `U+061C` | ALM | Contraparte árabe de LRM/RLM — **ausente na lista da Fase 0** | Idem | **B** | **A** | A |
| `U+202A`–`U+202E` | LRE, RLE, PDF, LRO, RLO | Formatação direcional legada; raríssimo em prosa moderna, existe em texto árabe/hebraico antigo | **Trojan Source (CVE-2021-42574)** | **B** | **A** | A |
| `U+2066`–`U+2069` | LRI, RLI, FSI, PDI | **Forma moderna recomendada pelo UAX #9** — **ausente na lista da Fase 0** | Isolamento direcional malicioso | **B** | **A** | A |
| `U+2060` | WORD JOINER | Manter `R$ 1.000` junto | Esconde texto | **B** | B | A |
| `U+2061`–`U+2064` | FUNCTION APPLICATION, INVISIBLE TIMES/SEPARATOR/PLUS | Notação matemática | Fórmula escondida | **B** | B | A |
| `U+FEFF` | BOM / ZWNBSP | **BOM legítimo** de editor Windows | Quebra o parser de frontmatter | **byte 0: normaliza e remove (registrado)** · meio: **A** | A | A |
| `U+E0000`–`U+E007F` | TAG characters | **Apenas as 3 bandeiras RGI** (§3.2.3) | **ASCII smuggling** — `U+E0020`–`U+E007E` espelham ASCII e são invisíveis | **A**, exceto as 3 RGI exatas | **A** | A |
| `U+3164`, `U+115F`, `U+1160` | HANGUL FILLER, CHOSEONG/JUNGSEONG FILLER | Composição Hangul | Nome que parece vazio | **B** | B | **A** |
| `U+00AD` | SOFT HYPHEN | **Hifenização em pt-BR** e dezenas de idiomas | Esconde caractere | **C** | C | A |
| `U+00A0` | NO-BREAK SPACE | `R$ 1.000`, `10 km` | Nenhum relevante | **C** | C | A |
| `U+180E` | MONGOLIAN VOWEL SEPARATOR | Histórico | Marginal | **B** | B | A |
| `U+FFF9`–`U+FFFB` | Interlinear annotation | Anotação interlinear | Esconde texto | **B** | **A** | A |

#### 3.2.2.1 Tabela normativa das duas faixas bidi — fonte única

Esta tabela é a **fonte única da verdade** para `U+202A–U+202E` e `U+2066–U+2069`. Qualquer
divergência em outro documento é erro daquele documento, não desta tabela. Ela é idêntica em
`PHASE-0-1-CONSISTENCY-REVIEW.md` §3.2.2 e na decisão `D-26`, e a verificação está registrada em
`PHASE-0-1-1-FINAL-CONSISTENCY-FIXES.md`.

| Faixa | Nome | **Prosa** | **Bloco de código** | **Identificador** |
|---|---|---|---|---|
| `U+202A`–`U+202E` | LRE, RLE, PDF, LRO, RLO (embeddings e overrides) | **B** — sinalizar e exigir revisão | **A** — rejeitar | **A** — rejeitar |
| `U+2066`–`U+2069` | LRI, RLI, FSI, PDI (isolates) | **B** — sinalizar e exigir revisão | **A** — rejeitar | **A** — rejeitar |

**Por que as duas faixas não têm o mesmo tratamento em prosa:** `U+202A–U+202E` inclui
**overrides** (`LRO`/`RLO`), que invertem a ordem visual sem alterar o byte — é o mecanismo do
Trojan Source. `U+2066–U+2069` são **isolates**, a construção que o UAX #9 recomenda **no lugar**
dos embeddings para texto bilíngue legítimo. Rejeitar isolates em prosa puniria exatamente o
uso correto, sem ganho de segurança: o que torna o Trojan Source perigoso é a reordenação, e
`RLI`/`PDI` isolam em vez de reordenar o texto ao redor.

**Por que ambas são rejeitadas em bloco de código:** em código não existe prosa bilíngue legítima
que exija controle bidi. Qualquer ocorrência ali é sinal de injeção. Em identificador, a mesma
razão do UTS #39: `Identifier_Status=Allowed` não as inclui, e o perfil de segurança não abre
exceção para elas.

**Regra de precedência e análise por região.** A análise é **por região do arquivo**, nunca por
arquivo inteiro. Um `SKILL.md` com `U+202E` em prosa (categoria **B**) e sem controles em bloco
de código é **importado para quarentena e sinalizado**, não rejeitado. O mesmo caractere dentro
de uma cerca tripla é **rejeitado**. Rejeitar o arquivo inteiro por uma ocorrência legítima em
prosa seria repetir o erro da Fase 0 em escala menor.

> **Nota sobre precedência de categorias.** A categoria `A` vence **dentro da mesma região** —
> se um identificador aparece dentro de um bloco de código, a regra do identificador e a do
> bloco de código coincidem (`A`). Não há caso em que `A` em uma região force `A` em outra
> região do mesmo arquivo.

#### 3.2.3 As três exceções de bandeira — allowlist literal, não regex

```
🏴 + U+E0067 U+E0062 U+E0065 U+E006E U+E0067 + U+E007F   → Inglaterra    (gbeng)
🏴 + U+E0067 U+E0062 U+E0073 U+E0063 U+E0074 + U+E007F   → Escócia       (gbsct)
🏴 + U+E0067 U+E0062 U+E0077 U+E006C U+E0073 + U+E007F   → País de Gales (gbwls)
```

O UTS #51 define `tag_spec` como **qualquer** caractere de `U+E0020` a `U+E007E`. Portanto
`🏴 + tags("qualquer frase") + U+E007F` é **bem-formada** e carrega texto invisível. Aceitar
"sequência bem-formada" é aceitar o ataque.

**Regra:** a única tag aceita é a **string literal exata** das três bandeiras acima. Toda outra
ocorrência em `U+E0000–U+E007F` é categoria **A** — inclusive uma tag solta, inclusive uma
sequência bem-formada.

**Custo declarado:** se o Unicode adicionar uma quarta bandeira de subdivisão, a allowlist exige
atualização de código. É o mesmo trade-off que um projeto público documentou após ser explorado
pelo padrão permissivo (`RESEARCH` externo, não verificação desta sessão).

#### 3.2.4 Normalização — NFC sim, NFKC não

A Fase 0 dizia "Normalização NFKC". **NFKC altera conteúdo legítimo**: converte `ﬁ` em `fi`, `①`
em `1`. Aplicá-la ao texto gravado **muda o trabalho do autor** — viola a regra de marca "o
trabalho do usuário pertence ao usuário".

| Operação | Quando | Persiste? |
|---|---|---|
| **NFC** | Sempre, para comparação | Não altera conteúdo canônico |
| **NFKC** | **Somente** para detectar homóglifo | **Nunca** |
| **Remoção de BOM** (`U+FEFF` no byte 0) | No import | Sim, registrada no relatório |
| **Qualquer outro stripping** | **Nunca** | — |

#### 3.2.5 O que esta política **não** faz

| Não faz | Consequência honesta |
|---|---|
| Não detecta homóglifos entre escritas | `раypal` (cirílico) passa. Exigiria `confusables.txt` — fora desta fase |
| Não detecta texto branco sobre branco | Não é propriedade do arquivo, é da renderização |
| Não detecta instrução maliciosa **em texto visível** | Nenhum caráter invisível envolvido; é problema de §3.1, não de §3.2 |
| Não substitui revisão humana | É **evidência** que reduz o espaço de busca, não veredito |

### 3.3 Travessia de caminho e escape de raiz

| | |
|---|---|
| **Ameaça** | Campo de capacidade resolve para fora do diretório da biblioteca; escrita sobrescreve arquivo do sistema |
| **Vetor** | `name` / `id` do frontmatter, nomes de arquivo dentro do ZIP, symlink dentro do pacote, `../`, caminho absoluto, drive letter, UNC (`\\server\share`) |
| **Impacto** | A1, A6 |
| **Detecção automática** | Sim |
| **Mitigação** | Ver §5 — é a seção mais detalhada deste documento, porque é onde projetos reais erram |
| **Classificação** | `Automático: forte` com as regras de §5 |

### 3.4 Execução arbitrária via scripts

| | |
|---|---|
| **Ameaça** | `scripts/` contém código que executa na máquina do usuário ao ser "testado" |
| **Vetor** | Qualquer arquivo executável no pacote |
| **Impacto** | A6 (crítico) |
| **Detecção automática** | Listar e classificar, **não** julgar segurança |
| **Mitigação** | **Nenhuma execução nesta fase.** `scripts/` presente ⇒ `trust` máximo permitido é `unreviewed`+`scripts-declared`; export avisa; o host decide. Quando houver Test Lab (`D-05`), só em ambiente descartável |
| **Limite** | Análise estática de script é **insuficiente por natureza** — obfuscação, download em runtime, chamada a binário do sistema |
| **Classificação** | `Automático: nenhum` · `Humano: obrigatório` |

### 3.5 Cadeia de suprimentos

| | |
|---|---|
| **Ameaça** | Upstream muda após revisão (rug pull); dependência comprometida; tag GitHub reescrita |
| **Vetor** | `source.upstream` sem pin; dependência transitiva; release substituída |
| **Impacto** | A4, A5 |
| **Detecção automática** | **Parcial e poderosa:** comparar `contentHash` registrado com o conteúdo atual; diff entre versões |
| **Mitigação** | Pinar por **commit SHA + hash de conteúdo**, nunca por tag ou `@latest`; diff obrigatório em toda atualização; `provenanceChain` registra cada passo |
| **Limite** | Não protege contra upstream comprometido **antes** da primeira revisão. Não substitui SBOM |
| **Classificação** | `Automático: forte para rug pull` · `Humano: para conteúdo` |
| **Nota** | Precedente concreto: o README do MCPVault recomenda `npx @bitmonsai/mcpvault@latest` — `@latest` é o antipadrão que esta regra proíbe |

### 3.6 Licença e redistribuição

| | |
|---|---|
| **Ameaça** | Distribuir capacidade cujo conteúdo não pode ser redistribuído; perder NOTICE Apache-2.0; confundir licença de código com a de pesos |
| **Vetor** | Copiar prosa de terceiro; empacotar peso; herdar dependência |
| **Impacto** | A5 (jurídico) |
| **Detecção automática** | Presença/ausência de `LICENSE`, `NOTICE`, SPDX no frontmatter; **heurística**, não jurídica |
| **Mitigação** | `license` por camada (§6.4 do doc de arquitetura); export **falha** com `license: null`; `NOTICE` obrigatório quando a licença exigir; `THIRD_PARTY_NOTICES.md` gerado do manifesto |
| **Limite** | **Determinar licença não é trabalho automatizável de forma confiável.** Revisão humana é o gate |
| **Classificação** | `Automático: triagem` · `Humano: decisão` |

### 3.7 Integridade, hash e assinatura (hash implementado; assinatura não)

| | |
|---|---|
| **Ameaça** | Pacote adulterado em trânsito ou em repouso; pacote trocado por outro com mesmo nome |
| **Vetor** | Disco, download, sincronização de nuvem, outro processo |
| **Impacto** | A4 |
| **Detecção automática** | Sim — SHA-256 por arquivo (`contentHash`) + hash da árvore (`treeHash`). **Implementado e testado**: adulterar um byte no payload invalida o pacote (`test_pacote_adulterado_e_detectado`); roundtrip entre dois Hubs preserva os dois hashes |
| **Mitigação** | Verificação obrigatória na carga; `formatVersion` + `hubVersion` no manifest |
| **Limite** | **Hash detecta alteração, não origem.** Provar autoria exige assinatura criptográfica (Sigstore/minisign) — **não pesquisada nesta fase**, **não implementada**, **fora do MVP** |
| **Classificação** | `Automático: forte para adulteração` · `Assinatura: fase futura, RESEARCH` |

#### 3.7.1 Seis conceitos, seis nomes — vocabulário obrigatório

A Fase 0 usou "índice **assinado**" na arquitetura enquanto a assinatura era fase futura. Isso
é uma alegação falsa sobre o produto. Vocabulário corrigido na Fase 0.1:

| Conceito | Nome no Hub | O que **prova** | O que **não** prova | Estado |
|---|---|---|---|---|
| Hash por arquivo | `contentHash` (SHA-256) | Que aquele arquivo não mudou desde a importação | Nada sobre origem ou intenção | **MVP** |
| Hash da árvore | `treeHash` | Que o **conjunto** de arquivos não mudou (pega arquivo adicionado ou removido) | Nada sobre origem | **MVP** |
| Integridade do pacote | `packageHash` | Que o ZIP não corrompeu no transporte | Nada sobre origem | **MVP** |
| Assinatura criptográfica | `signature` | Que quem assinou tinha a chave privada | Nada sobre segurança do conteúdo | **Fora do MVP**, `RESEARCH` |
| Identidade do autor | `author` | **O que o autor declara sobre si** | **Nada** — é texto livre | **MVP, como declaração** |
| Proveniência | `provenance` | De onde o Hub **diz** que veio, rastreável na fonte | Nada, se a fonte mudou ou é privada | **MVP** |

**Termos proibidos em todo o repositório enquanto a assinatura não existir:**

| Proibido | Usar |
|---|---|
| "índice assinado" | "índice com hashes" / "índice verificável" |
| "assinatura verificada" | — (não existe) |
| "pacote autêntico" | "pacote com integridade verificada" |
| "autor verificado" | "autor declarado" |
| "proveniência verificada" | "proveniência declarada, rastreável em `<URL>`" |

**Nota sobre a pasta `signatures/`:** o formato `.lia-capability` a reserva, mas **reservar um
diretório não é implementar assinatura**. Nenhum código do MVP lê essa pasta. Um arquivo lá
dentro é ignorado, não verificado — e o manifest **não** pode declarar `signed: true`.

### 3.8 Exfiltração por egress

| | |
|---|---|
| **Ameaça** | Capacidade faz o host enviar dado do usuário a destino remoto sem o usuário saber |
| **Vetor** | Campo `egress` subdeclarado; script que chama rede; MCP remoto |
| **Impacto** | A1, A2, A3 |
| **Detecção automática** | Comparar `egress.destinations` declarado contra strings de URL no corpo e nos scripts; **não** é prova |
| **Mitigação** | `egress.consentRequired: true` por padrão; `destinations` explícito; o host mostra **para onde** antes de enviar; `network: false` quando não houver egress |
| **Limite** | O Hub **não controla** a rede do host. Ele só declara e avisa |
| **Classificação** | `Automático: triagem` · `Humano/host: gate` |

### 3.9 Confusão de identidade (typosquatting)

| | |
|---|---|
| **Ameaça** | Capacidade com nome quase idêntico a uma revisada (`lia-game-qa-plan` vs `1ia-game-qa-plan`, homóglifo) |
| **Vetor** | `name` |
| **Impacto** | A4, A7 |
| **Detecção automática** | Comparação normalizada + distância de edição contra a biblioteca local |
| **Mitigação** | Identidade do Hub é `(id, version, contentHash)`, não só nome; aviso em colisão |
| **Limite** | Contra atacante remoto sem biblioteca local, só regra de namespace |
| **Classificação** | `Automático: parcial` |

### 3.10 Adulteração da biblioteca

| | |
|---|---|
| **Ameaça** | Outro processo (ou o próprio usuário por engano) altera `index.json` ou pacotes |
| **Vetor** | Acesso ao diretório |
| **Impacto** | A4 |
| **Mitigação** | Escrita atômica (ler-mesclar-gravar em temp + rename, padrão do kit §5.6); hashes verificados na leitura; nada é confiado por estar em `index.json` sem hash conferido |
| **Limite** | Se o atacante já escreve no diretório como o usuário, a integridade do **sistema** já foi comprometida — fora do escopo do Hub |
| **Classificação** | `Automático: forte` |

---

## 4. Escala de confiança — operacional

Do documento de arquitetura (§6.3), com a **evidência exigida** para cada nível:

| Nível | Evidência mínima exigida | Quem promove | Pode ser automático? | O que o Hub **pode** afirmar |
|---|---|---|---|---|
| `unreviewed` | Nenhuma (é o default do import) | — | Sim | "Estrutura válida. Nada foi revisado." |
| `user-provided` | Declaração registrada do usuário | Usuário | Sim, com registro | "Fornecido pelo usuário. Sem revisão de terceiro." |
| `reviewed-external` | Revisor identificado + data + método + lista de achados | **Humano** | **Nunca** | "Revisado por <pessoa> em <data>, método <método>. Achados: <lista>." |
| `first-party` | Origem verificada em repositório permitido + commit | Sistema, com lista de repositórios | Sim, restrito | "Mantido no repositório <repo> no commit <sha>." |

**Três regras que impedem fraude de confiança:**

1. **Scanner verde gera `evidence`, não `trust`.** Um relatório de análise estática entra em `trustEvidence.findings[]`; não muda o nível.
2. **`reviewed-external` sem revisor identificado é inválido.** Sem nome, é `unreviewed`.
3. **Nível nunca é promovido por passagem de tempo, popularidade, número de estrelas ou ausência de incidente.** Isso é explícito porque o ecossistema tem projeto com 147 k ★ criado há 7 meses — popularidade **não** é maturidade.

---

## 5. Contenção de caminho — especificação

Esta seção existe porque é onde projetos reais erram, e há evidência pública disso: o MCPVault **corrigiu** um bug (issue #128) em que o glob `node_modules/**` só pegava a raiz, deixando `.git`/`.obsidian` aninhados vazarem. A correção passou a negar segmentos **em qualquer profundidade** e a canonicalizar nomes.

### 5.1 Regras obrigatórias

| # | Regra | Motivo |
|---|---|---|
| C1 | Toda resolução parte de **uma função só**, que recebe a raiz e o caminho relativo | Impede que um módulo monte caminho na mão (mesma regra do kit, §2.1) |
| C2 | Rejeitar **caminho absoluto**, letra de drive (`C:`), UNC (`\\`), e prefixo `\\?\` | Windows aceita formas que `path.resolve` normaliza de jeitos inesperados |
| C3 | Rejeitar qualquer segmento `..` **após** normalização | `a/../../b` normaliza para fora |
| C4 | **Nunca seguir symlink ou junction** dentro do pacote; rejeitar o pacote | Studio já faz isso em `skills.py`; junction é comum no Windows |
| C5 | Denylist de segmento aplicada em **qualquer profundidade**, comparada case-insensitive | O bug #128 |
| C6 | **Canonicalizar antes de comparar:** remover pontos e espaços finais por segmento | Windows resolve `.git.` e `.git ` para `.git` |
| C7 | Validar que o caminho resolvido **começa com a raiz resolvida + separador** | Comparação de prefixo de string pura aceita `C:\Lia\Comum-Evil` para raiz `C:\Lia\Comum` |
| C8 | Checar **comprimento de caminho** (teto de 260 enquanto *long path* não for decisão) | O kit registra que projeto aninha fundo e estoura tarde, já com arquivo parcialmente gravado |
| C9 | Rejeitar nomes reservados do Windows: `CON`, `PRN`, `AUX`, `NUL`, `COM1-9`, `LPT1-9`, com ou sem extensão | `CON.md` falha de forma obscura |
| C10 | Na descompactação de `.lia-capability`: rejeitar entrada absoluta, `..`, symlink e **zip-slip**; validar antes de extrair, não depois | Zip-slip é a falha clássica de pacote |
| C11 | Validar `payload.files[]` contra o conteúdo extraído: arquivo a mais **é erro**, não aviso | Senão o manifest deixa de descrever o payload |
| C12 | Escrever **fora** da raiz somente via caminho escolhido explicitamente pelo usuário na interface | Exportação é ação do usuário, não de conteúdo |

### 5.2 Denylist de segmento (mínimo)

```
.git  .obsidian  node_modules  .trash  .DS_Store  Thumbs.db
.lia/provenance.json (somente leitura pelo Hub, nunca escrita por capacidade)
```

Além disso, o Hub **nunca** resolve caminho para dentro de:
```
%USERPROFILE%\Lia\Waifu\          ← memória de convivência (A3)
%APPDATA%\Lia\*\config\           ← configuração de outros apps
%LOCALAPPDATA%\Lia\*\{cache,logs} ← dados técnicos de outros apps
```

### 5.3 Allowlist de extensão por tipo de payload

Não é denylist. É lista fechada, por tipo de capacidade:

| Tipo | Extensões aceitas no payload |
|---|---|
| `skill` | `.md`, `.markdown`, `.txt`, `.json`, `.yaml`, `.yml`, `.csv` + `scripts/` com extensões declaradas no manifest |
| `knowledge` | `.md`, `.markdown`, `.txt`, `.pdf`, `.json`, `.csv` |
| `mcp-server` | `.json`, `.md` (configuração e doc — **nunca** binário) |
| `reference` | qualquer arquivo **não executável**, declarado no manifest |

**Regra:** extensão não declarada ⇒ pacote rejeitado. Não existe "tolerância".

### 5.4 Proibições absolutas

O Hub **nunca**:

1. Escreve fora do diretório da biblioteca ou de um destino escolhido pelo usuário naquele ato.
2. Lê A3 (memória de convivência) — nem para "indexar", nem para "verificar".
3. Grava valor de credencial — em arquivo, log, índice, cache ou mensagem de erro.
4. Executa `scripts/`, binário, comando de shell ou cliente MCP.
5. Abre porta de rede além do loopback, e mesmo no loopback só se `D-09` aprovar API.
6. Resolve caminho a partir de texto vindo de capacidade.
7. Segue symlink/junction de conteúdo importado.
8. Remove dado do usuário sem confirmação explícita com tamanho exibido.

---

## 6. Detecção automática — catálogo honesto

Esta tabela é o coração da honestidade deste documento. **Cada linha diz o que um verificador consegue e o que não consegue.**

| Verificação | Detecta | **Não** detecta | Confiabilidade |
|---|---|---|---|
| Frontmatter válido contra a spec | `name` fora de 1–64; hífen duplo; `description` >1024; chave extra | Intenção, qualidade, segurança | **Alta** (determinístico) |
| Diretório = `name` | Divergência | Divergência **intencional** de atacante com nome igual e conteúdo malicioso | Alta |
| Unicode invisível | Tags, zero-width, bidi | Homóglifos visuais | **Alta** (esta é a de maior valor) |
| Travessia / symlink / zip-slip | Vetores de §5 | — | Alta |
| Hash / treeHash | Alteração após registro | Origem | Alta |
| Diff entre versões | Mudança de conteúdo | Mudança **maliciosa irrelevante** em volume | Alta |
| Egress declarado vs. URLs no texto | URL no corpo não declarada | URL construída em runtime por script | Média |
| Dependência declarada vs. real | Import não declarado em script Python/JS | Rede, `subprocess`, eval, obfuscação | **Baixa** |
| Análise de licença (presença) | Ausência de `LICENSE`/`NOTICE`; SPDX malformado | Compatibilidade jurídica; licença de peso; licença de dado | **Baixa** |
| Scanner de conteúdo externo (ex.: `snyk/agent-scan`) | Padrões conhecidos de tool poisoning | Paráfrase, ataque novo | Média, **com falso-positivo** |
| Prompt injection no corpo | Padrões lexicais | Paráfrase, instrução indireta, multi-arquivo | **Baixa a média** |
| Segurança de script | **Nada confiável** | Praticamente tudo | **Nenhuma** |

### 6.1 A frase que o produto deve usar

> **"As verificações automáticas encontraram N itens. Elas não avaliam segurança. A revisão humana é obrigatória para elevar o nível de confiança."**

Nunca: "validado", "aprovado", "seguro", "passou nos testes".

---

## 7. O que exige julgamento humano — e não pode ser automatizado

| Julgamento | Por que não há automação confiável |
|---|---|
| **"Esta Skill faz o que diz que faz?"** | Semântica de prosa. Comparar intenção declarada com procedimento exige compreensão |
| **"Este licenciamento permite redistribuir?"** | Envolve jurisdição, termos de uso, licença de pesos, direitos de imagem/asset. Nenhum scanner é parecer jurídico |
| **"O autor é confiável?"** | Reputação não é dado em arquivo |
| **"Este comportamento é aceitável para o usuário?"** | É decisão de produto/risco, reservada ao humano (`D-18`) |
| **"Este script é seguro?"** | Indecidível na prática |
| **"A descrição foi otimizada para sequestrar a seleção?"** | Envenenamento semântico de `description` documentado; só leitura crítica pega |
| **"Este MCP é adequado ao meu projeto?"** | Depende de contexto que o Hub não tem |

**Consequência de produto:** o fluxo de revisão é **assistido**, não **substituído**. O Hub apresenta evidência organizada e registra a decisão humana com autor, data e método.

---

## 8. Fluxo de importação — o único caminho permitido

```
1. RECEBER
   ├─ caminho local, arquivo .lia-capability ou diretório
   └─ NADA é executado, NADA é copiado para a biblioteca ainda

2. ANALISAR (somente leitura, em área temporária isolada)
   ├─ descompactar em temp com C10/C11 aplicados
   ├─ validar frontmatter contra spec
   ├─ varrer Unicode por categoria e contexto ← rejeita só categoria A (§3.2)
   ├─ validar caminhos (C1–C12)
   ├─ inventariar arquivos + hashes
   ├─ extrair URLs, comandos, imports declarados
   ├─ listar `scripts/` (sem executar)
   └─ triagem de licença (presença, não parecer)

3. RELATAR  →  trust = `unreviewed` sempre neste ponto
   └─ relatório com: o que é, de onde veio, o que declara,
      o que contém, o que as verificações viram E NÃO viram

4. AGUARDAR DECISÃO HUMANA
   └─ sem revisão: fica em "quarentena", não entra no índice publicável

5. ADMITIR (após revisão registrada com autor + data + método)
   ├─ copiar para a biblioteca
   ├─ gravar provenance.json + capability.json
   ├─ gravar hash de conteúdo
   └─ status = `catalogued`, trust conforme decisão

6. PUBLICAR  →  só o que passou por 5 entra em index.json
```

**Regra dura:** os passos 1–4 **não têm efeito colateral** fora de um diretório temporário. Cancelar no passo 4 deixa a máquina como estava. Isso é verificável por teste e deve ser critério de aceite.

---

## 9. Atualização, rollback e reversão

| Requisito | Como |
|---|---|
| **Nenhuma atualização silenciosa** (`D-10`) | Cada versão é explícita; `index.json` lista versões, não "latest"; host fixa a versão que quer |
| **Diff obrigatório** | Atualizar exige exibir diff de conteúdo, de `description` (que é o gatilho!) e de `declaredPermissions` |
| **Revalidação de confiança** | Atualização **não herda** `reviewed-external`; volta a `unreviewed` até nova revisão |
| **Rollback** | Versões anteriores ficam na biblioteca; reverter = apontar para a versão anterior |
| **Reversão de instalação** | O Hub não instala. Reversão é do host. O Hub pode **declarar** o que o host deve remover |
| **Nada é apagado sem confirmação** | Desinstalar mostra tamanho e pergunta; padrão do kit |
| **Histórico append-only** | `history.json` registra eventos; não reescreve |

---

## 10. Auditoria

| Evento registrado | Campos | Onde |
|---|---|---|
| Importação analisada | timestamp, origem, hash, resultado das verificações, achados | `history.json` + log local |
| Revisão humana | autor, data, método, achados, decisão | `provenance.json` |
| Admissão na biblioteca | id, versão, hash, trust, quem admitiu | `history.json` |
| Exportação | id, versão, destino, hash do pacote | `history.json` |
| Atualização | de/para, diff resumido, nova revisão | `history.json` |
| Rejeição / quarentena | motivo, timestamp | `history.json` |
| Erro de validação de pacote recebido | hash, regra violada | log local |

**Regra:** o log **não** contém conteúdo de capacidade, caminho de memória de convivência, nem valor de credencial. Registra **metadado de operação**.

**Formato:** JSON Lines em `%LOCALAPPDATA%\Lia\AgentHub\logs\audit-YYYY-MM.jsonl` (dado técnico, segundo o kit, não vai para backup nem roaming). O `history.json` da capacidade é dado do usuário, fica junto do pacote.

---

## 11. Isolamento e Test Lab

**Estado nesta fase: `PLANNED`, bloqueado por `D-05` e `D-18`.** Não existe — e o documento não propõe construir.

O que posso afirmar com segurança:

| Afirmação | Base |
|---|---|
| `uv tool install` **não é sandbox** | É um gerenciador de ambiente por ferramenta. Instala no perfil do usuário com acesso normal ao SO |
| `--allowedTools` **não é sandbox** | O próprio Studio documenta isso em `agent_cli.py` |
| Contêiner **não é sandbox por padrão** no Windows para app de desktop que precisa de GUI | Requer configuração explícita; WSL2 é ambiente separado, não isolamento |
| Windows Sandbox **isola**, mas é uma VM interativa por sessão e não tem integração com app desktop | Comportamento documentado da Microsoft — **não verificado nesta sessão** |
| Não houve pesquisa de SBOM nem de assinatura | `RESEARCH` pendente |

**Conclusão:** Test Lab é a funcionalidade de maior risco e maior custo do Hub. Ela **não** pode entrar antes de uma sessão dedicada a isolamento em Windows com prova real. O MVP entrega valor grande sem ela (`MVP-AND-ROADMAP.md`).

---

## 12. Cadeia de suprimentos — o mínimo defensável

| Prática | Estado recomendado | Fase |
|---|---|---|
| Pinar por commit SHA, nunca tag ou `@latest` | **Obrigatório** | MVP |
| Hash de conteúdo por arquivo + `treeHash` | **Obrigatório** | MVP |
| `provenanceChain` persistida | **Obrigatório** | MVP |
| Diff obrigatório em atualização | **Obrigatório** | MVP |
| `formatVersion` + `hubVersion` no manifest | **Obrigatório** | MVP |
| `NOTICE` preservado quando exigido | **Obrigatório** | MVP |
| `THIRD_PARTY_NOTICES.md` gerado do manifesto | **Obrigatório** | MVP |
| SBOM (SPDX/CycloneDX) por pacote | Desejável | Fase 2 |
| Assinatura (minisign/Sigstore) | Desejável | Fase 3 |
| Transparência (log de assinatura público) | Não recomendado agora | Não pertence ao MVP |

**O que deliberadamente não está na lista:** bloqueio de execução, reputação de autor, "trust score" calculado. Nenhum é verificável.

---

## 13. Riscos residuais aceitos (declarados)

Estes riscos **permanecem** mesmo com todos os controles acima. O produto deve declará-los:

| # | Risco residual | Por que permanece |
|---|---|---|
| R1 | Uma Skill revisada pode ser inofensiva na revisão e maliciosa na execução pelo host | O Hub não controla o modelo do host |
| R2 | Revisão humana pode ser superficial | Processo, não garantia técnica |
| R3 | Homóglifos visuais passam | Sem confusables-mapping |
| R4 | Licença pode estar errada mesmo revisada | Não é parecer jurídico |
| R5 | Upstream pode ser comprometido antes da primeira revisão | Sem histórico anterior |
| R6 | Um host pode executar capacidade `unreviewed` por decisão própria | Fora do controle do Hub |
| R7 | Exfiltração via script não é detectável | Indecidível |

**Declaração obrigatória no produto:** *"O Lia Agent Hub organiza, valida estrutura e registra decisões humanas. Ele não garante que uma capacidade seja segura, nem executa nada. Quem autoriza e executa é o host, com a política dele."*

---

## 14. Conclusões

1. **O maior valor de segurança por menor custo é a varredura determinística de Unicode invisível + contenção de caminho.** Ambas são baratas, totalmente automatizáveis e cobrem vetores reais (o bug #128 do MCPVault é evidência).
2. **Análise estática de script não é oferecida como proteção**, porque não funciona. Isso deve estar escrito no produto, não omitido.
3. **Nenhuma capacidade importada é executada.** Isso remove a maior classe de risco e é compatível com a arquitetura proposta.
4. **Confiança é decisão humana registrada**, não score. Scanner produz evidência; humano produz nível.
5. **Sete riscos residuais ficam abertos e precisam ser declarados ao usuário.** Um produto que esconde risco residual viola a regra nº 4 da marca.
6. **Test Lab é a parte perigosa e está bloqueada** por decisão pendente, não por falta de tempo.

---

## Referências

- `docs/research/INTEGRATION-CANDIDATES.md` §3.2 — evidência de contenção de caminho no MCPVault (código lido, `src/pathfilter.ts`)
- `docs/research/INTEGRATION-CANDIDATES.md` §2 — especificação Agent Skills e seus limites de segurança
- `docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md` §6 — escala de confiança e licença por camada
- `docs/architecture/DATA-STORAGE-AND-PORTABILITY.md` §3 — onde logs e auditoria vivem
- `BloomRX/Lia-Studio@arena/04710d54-lia-studio`, `docs/research/ARENA-SKILLS-MCP-AGENT-TOOLS-RESEARCH.md` §3.3–3.4 — evidência de incidentes e scanners (**`RESEARCH` herdado, não verificado nesta sessão**)
- `BloomRX/Lia-Studio@arena/01a0f4ab-lia-gamedev`, `app/lia/{permissions,tool_registry,skills}.py` — precedentes de função pura, negação prevalecente e rejeição de symlink
- `BloomRX/Lia-Forge@arena/649f88bd-3dspritesheet`, `shared/fs/path-containment.mjs`, `docs/SKILLS-KNOWLEDGE-ENGINE.md` §"Segurança de conteúdo"
- `KIT-PROJETO-NOVO.zip` → `APP-WINDOWS/PADRAO-DA-MARCA.md` §5.6 (escrita atômica), §5.5 (validação de caminho, teto de 260)
