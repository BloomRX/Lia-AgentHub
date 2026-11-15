# Fase 1 — Relatório final da implementação do MVP

**Data:** 2026-11-15 (UTC)
**Branch:** `arena/a92004be-lia-agenthub`
**Natureza:** relatório de execução. Separa o que foi **validado** do que foi
apenas **implementado** e do que **não foi possível validar** neste ambiente.

---

## 1. Estado Git

| Item | Valor |
|---|---|
| Branch | `arena/a92004be-lia-agenthub` |
| HEAD inicial desta rodada | `a1ea55e` |
| HEAD final | `aabd5ba` |
| Commits desta rodada | 7 |
| Push | `b62c125..aabd5ba` → origin, sem force |
| `main` | `34a27f48` — **intacta**, local e remoto |
| Árvore de trabalho | limpa |
| Merge / PR | nenhum |

### Commits

| Hash | Assunto |
|---|---|
| `9377360` | núcleo funcional — biblioteca, importação, validação, pacotes, UI |
| `474791c` | 212 testes — funcional, segurança, persistência, interface |
| `993eb98` | empacotamento Windows, WebView2, scripts de operação |
| `79955ca` | Etapa B — adoção para implementação, sem aprovação |
| `37c764e` | Configurações, atualização versionada, correções de metadados |
| `91bffe2` | referências a arquivos no `SKILL.md` |
| `aabd5ba` | coerência estrutural HTML/CSS/JS |

**Volume:** 55 arquivos, +7.800 linhas (3.817 em `src/`, 2.000 em `tests/`).

---

## 2. Implementação

### Arquitetura

Quatro camadas, dependência só para baixo. `domain/` é puro: não abre arquivo,
não usa rede, não importa `adapters/`. É o que permite testar as regras de
segurança sem tocar o disco.

```
interface/  L1  servidor local (token, Origin, Host, CSP) + ativos estáticos
app.py          serviço de aplicação — a UI fala só com ele
adapters/   L2  arquivos, ZIP, índice, configurações, plataforma
domain/     L3  unicode, caminhos, skills, risco, integridade, modelo
```

| Módulo | Linhas | Responsabilidade |
|---|---|---|
| `domain/unicode_policy.py` | — | categorias A/B/C/D por região (prosa vs código) |
| `domain/paths.py` | — | contenção de caminho C1–C13 |
| `domain/skills.py` | — | validação estrutural + referências a arquivos |
| `domain/risk.py` | — | risco por regras + o que NÃO foi avaliado |
| `domain/integrity.py` | — | SHA-256 por arquivo e de árvore |
| `adapters/safe_extract.py` | — | toda defesa de entrada (ZIP e diretório) |
| `adapters/repository.py` | — | biblioteca em disco; índice é derivado |
| `adapters/importer.py` | — | pipeline de 6 passos, staging antes da promoção |
| `adapters/packager.py` | — | `.lia-capability` exportar e verificar |
| `adapters/index_builder.py` | — | `index.json` + schema + consistência |
| `adapters/settings.py` | — | preferências atômicas com coerção |
| `adapters/platform_check.py` | — | WebView2, plataforma, fallback |

### Dependências adicionadas

**Zero no núcleo.** Só biblioteca padrão. Extras opcionais: `pywebview` (janela
nativa) e `pytest`/`pyinstaller` (desenvolvimento e build).

### Decisões tomadas nesta rodada

| Tema | Escolha | Por quê |
|---|---|---|
| ID de capacidade | `<nome>-<8 hex do conteúdo>` | mesmo conteúdo ⇒ mesmo id ⇒ dedup honesto |
| Reimportação idêntica | reportada como `alreadyPresent` | é identidade, não conflito |
| Atualização | antiga vira `superseded`, nunca apagada | perda silenciosa é o que se quer evitar |
| Licença detectada | registrada com código, `redistributable=False` | detectar arquivo não é revisar licença |
| Referência quebrada | aviso, não erro | bloquear recusaria skill legítima |
| Unicode em prosa | não bloqueia, marca revisão | bloquear quebraria texto legítimo |
| Unicode em código | bloqueia | não há uso legítimo ali |
| ZIP aninhado | recusa (era aviso) | esconde conteúdo da revisão |
| Exportação `public` | recusa sem base registrada | decisão humana, não inferência |

---

## 3. Validação — o que foi executado

### Testes

```
258 passed in 13.72s
```

| Arquivo | Testes | Foco |
|---|---|---|
| `security/test_path_traversal.py` | 38 | traversal, absoluto, UNC, NTFS, symlink, escrita fora |
| `security/test_archives.py` | 19 | ZIP malformado, bomba, CRC, colisão, aninhado |
| `security/test_integrity_and_packages.py` | 20 | adulteração, segredo, integridade, exportação |
| `integration/test_persistence.py` | 26 | escrita atômica, recuperação, índice, backup |
| `integration/test_import_flow.py` | 25 | fluxo ponta a ponta, licença, referências |
| `integration/test_ui.py` | 29 | servidor, token, Origin, a11y, estados vazios |
| `integration/test_settings_and_versions.py` | 17 | configurações, versionamento, linhagem |
| `integration/test_ui_structure.py` | 8 | coerência HTML/CSS/JS |
| `unit/test_unicode_policy.py` | 32 | categorias por região |
| `unit/test_skills.py` | 33 | frontmatter, formatos, referências |
| `unit/test_risk.py` | 11 | fatores, limites declarados |

Todos com dados sintéticos. **Nenhum teste executa conteúdo importado.**

### Falhas reais encontradas pelos testes e corrigidas

| Bug | Impacto |
|---|---|
| `payload_files`/`detail`/`history` liam só a biblioteca | validar item em quarentena falhava |
| ZIP aninhado só gerava aviso | conteúdo escondido passava |
| CRC declarado não era conferido | adulteração silenciosa passava |
| Manifesto de pacote não chegava ao importador | verificação de declarações era pulada |
| Reimportação aninhava `payload/payload/` | round-trip perdia o hash original |
| Índice aceitava capacidade inexistente | índice prometia o que não existia |
| Versão do frontmatter ignorada | tudo virava 0.1.0 |
| `domain` recebia a string crua de `metadata` | rótulo errado em toda skill |
| Licença detectada era descartada | LICENSE MIT aparecia como "desconhecida" |
| Vínculo índice↔pacote partia em `-0.` | quebrava em qualquer versão ≠ 0.x |
| API sem `lifecycle` devolvia lista vazia | biblioteca parecia vazia |
| Campo de caminho do pacote sem rótulo | falha de acessibilidade |

### Verificação de sensibilidade das asserções

Uma verificação que não pode falhar não prova nada. Regressões injetadas:

| Regressão | Resultado |
|---|---|
| D-16 → `APPROVED` | 41/44 (3 FAILs) |
| D-13 → `APPROVED` | 40/44 (4 FAILs) |
| D-14 sem marca de adoção | 43/44 (1 FAIL) |
| Restaurado | **44/44** |

### Consistência documental

```
python3 docs/research/verify-consistency.py  →  44/44 PASS
```

### Segurança validada

- 20 caminhos perigosos recusados; caminho absoluto, UNC, drive e fluxo NTFS bloqueados.
- ZIP: traversal, colisão de caixa, aninhado, criptografado, bomba, CRC, excesso de entradas.
- Symlink recusado; original nunca movido nem alterado.
- Nada escrito fora da área autorizada (verificado por teste).
- Token de sessão exigido; Origin e Host validados; CSP `frame-ancestors 'none'`.
- Nenhum segredo versionado (varredura em `validate.sh`).
- Exportação pública recusada sem base de redistribuição.

### Build

`packaging/lia_agenthub.spec` + `scripts/build_windows.ps1`. O script roda os
testes e **aborta** se algum falhar antes de empacotar.

### Limitações do ambiente — declaradas, não contornadas

Ambiente: Linux, Python 3.11.2, sem Windows, sem WebView2, sem navegador.

| Não validado | Por quê |
|---|---|
| Geração do `.exe` | PyInstaller precisa de Windows para produzir `.exe` |
| Janela nativa em WebView2 | sem WebView2 nem display no ambiente |
| SmartScreen / instalação limpa | exige Windows real |
| Caminhos `%APPDATA%` / `%LOCALAPPDATA%` reais | exige Windows real |
| Renderização visual da interface | sem navegador; validada por estrutura e testes HTTP |

O servidor HTTP que a janela nativa carrega **foi** validado — token, Origin,
Host, CSP, travessia em estático, estados vazios. O que falta é a moldura nativa.

---

## 4. Pendências

### Técnicas

- Executável Windows não gerado (ambiente). Comando pronto e testado logicamente.
- Teste de interface visual não automatizado (sem navegador no ambiente).
- Test Lab futuro (execução isolada) — fora de escopo por decisão D-05.

### Jurídicas

- **Licença do repositório não escolhida; nenhum arquivo `LICENSE` criado.**
  D-16 continua `OPEN`. Exige decisão humana. Não bloqueou nada do MVP.

### Decisões ainda abertas

| Decisão | Assunto | Estado |
|---|---|---|
| D-01 | nome do produto | `OPEN` — mantido "Lia Agent Hub" como nome de trabalho |
| D-05 | execução de terceiros | `OPEN` — nada é executado |
| D-16 | licença | `OPEN` — sem `LICENSE` |
| D-18 | modelo de risco | `OPEN` — implementado por regras transparentes |

Adotadas para implementação, **sem** virar `APPROVED`: D-03, D-06, D-13, D-14,
D-27. Quatro verificações automáticas falham se essa distinção for violada.

---

## 5. Avaliação por capacidade

| # | Capacidade | Estado | Evidência |
|---|---|---|---|
| C1 | Aplicação desktop | **IMPLEMENTADA, MAS NÃO VALIDADA** | `__main__.py`, servidor HTTP testado; janela nativa não executada |
| C2 | Biblioteca | **CONCLUÍDA E VALIDADA** | busca, filtro por tipo/confiança/tag, detalhe, histórico — testes HTTP |
| C3 | Importação | **CONCLUÍDA E VALIDADA** | arquivo, pasta, `.zip`, `.lia-capability`; quarentena; 38 testes de contenção |
| C4 | Inspeção e validação | **CONCLUÍDA E VALIDADA** | 33 testes de `SKILL.md` + 32 de Unicode + referências a arquivos |
| C5 | Procedência, licença, risco | **CONCLUÍDA E VALIDADA** | licença detectada ≠ permissão; risco com o que não foi avaliado |
| C6 | Versionamento e integridade | **CONCLUÍDA E VALIDADA** | 17 testes; versão anterior preservada; diff; duplicata por árvore |
| C7 | Empacotamento e exportação | **CONCLUÍDA E VALIDADA** | pacote, verificação de adulteração, exportação múltipla, política por destino |
| C8 | Índice compartilhável | **CONCLUÍDA E VALIDADA** | `index.json` + schema; detecta pacote ausente e capacidade fantasma |
| C9 | Gestão e experiência | **IMPLEMENTADA, MAS NÃO VALIDADA** | 6 áreas, a11y e estrutura verificadas; renderização não observada |
| — | Build Windows | **IMPLEMENTADA, MAS NÃO VALIDADA** | spec + script; execução exige Windows |
| — | Documentação | **CONCLUÍDA E VALIDADA** | guia de uso, guia de desenvolvimento, README atualizado |

**Nenhuma capacidade está marcada como concluída sem evidência.** As duas que
dependem de Windows estão explicitamente separadas.

---

## 6. Veredito

O MVP está **implementado e validado no que este ambiente permite validar**.
Núcleo, biblioteca, importação, validação, procedência, integridade,
versionamento, empacotamento e índice: validados por 258 testes automatizados.

O que falta é a **moldura nativa do Windows**, que este ambiente não tem como
executar. O bloqueio é externo, está isolado em dois itens, e não impede o uso:
o Hub funciona no navegador, e o caminho HTTP que a janela nativa carrega está
testado.

**Não afirmo que o `.exe` funciona.** Não foi gerado nem executado aqui.
