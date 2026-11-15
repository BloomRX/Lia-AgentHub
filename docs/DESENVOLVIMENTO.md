# Desenvolvimento

## Requisitos

| Item | Versão | Observação |
|---|---|---|
| Python | 3.11 mínima, 3.13 alvo | 3.11 tem suporte de segurança até 2027-10 |
| pytest | 8+ | para a suíte |
| pywebview | 6.2+ | opcional; sem ele abre no navegador |
| PyInstaller | 6.0+ | só para gerar o `.exe` |

O núcleo **não tem dependências de terceiros** — só biblioteca padrão.
`pywebview` e `pyinstaller` são extras, não requisitos de execução.

## Começar

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

## Comandos

| Comando | O que faz |
|---|---|
| `bash scripts/dev.sh` | Sobe o Hub em modo desenvolvimento |
| `python3 scripts/run_dev.py 8000` | Sobe escutando em `0.0.0.0` para preview |
| `bash scripts/test.sh` | Roda a suíte inteira |
| `bash scripts/validate.sh` | Docs + sintaxe + testes + varredura de segredos |
| `python3 scripts/seed_demo.py` | Cria dados sintéticos para ver a interface |
| `powershell scripts\build_windows.ps1` | Gera `dist\LiaAgentHub.exe` |

`scripts/run_dev.py` **relaxa** a checagem de token e de Origem. Ele não é o
produto: serve para ver a interface por um proxy de preview. O bind de
produção é `127.0.0.1` com token de sessão.

## Arquitetura

Quatro camadas, dependência só para baixo:

```
interface/     L1  servidor local + ativos estáticos
   ↓
app.py             serviço de aplicação (a UI fala só com isto)
   ↓
adapters/      L2  toca o sistema: arquivos, ZIP, índice, plataforma
   ↓
domain/        L3  puro, sem I/O: regras e modelos
```

**Regra que não se quebra:** `domain/` não importa `adapters/`, não abre
arquivo, não usa rede. É o que permite testar as regras de segurança sem
tocar o disco.

### Módulos

| Módulo | Responsabilidade |
|---|---|
| `domain/unicode_policy.py` | Categorias A/B/C/D por região (prosa vs código) |
| `domain/paths.py` | Contenção de caminho C1–C13 |
| `domain/skills.py` | Validação estrutural de `SKILL.md` |
| `domain/risk.py` | Risco por regras transparentes + o que não foi avaliado |
| `domain/integrity.py` | SHA-256 por arquivo e de árvore |
| `domain/model.py` | `Capability`, `License`, `Trust`, `Lifecycle` |
| `adapters/safe_extract.py` | ZIP e diretório: toda defesa de entrada |
| `adapters/repository.py` | Biblioteca em disco; índice é derivado |
| `adapters/importer.py` | Pipeline de 6 passos, staging antes da promoção |
| `adapters/packager.py` | `.lia-capability` exportar e verificar |
| `adapters/index_builder.py` | `index.json` + schema + consistência |
| `adapters/platform_check.py` | WebView2, plataforma, fallback |

### Adicionar um tipo de capacidade

1. Acrescente o valor em `ResourceType` (`domain/model.py`).
2. Se tiver validação própria, crie `domain/<tipo>.py` devolvendo `list[Issue]`.
3. Em `adapters/importer.py`, `_detect_type()` decide o tipo e o passo 3
   chama o validador.
4. Se tiver campos próprios, estenda `Capability` com valor padrão — os
   metadados já gravados continuam válidos.

O contrato de saída (`.lia-capability`, `index.json`) não muda: o `type` é
string, não enum fechado. É por isso que adicionar um tipo não quebra quem lê.

## Decisões de implementação

| Tema | Escolha | Por quê |
|---|---|---|
| Armazenamento | Arquivos + JSON, sem SQLite | Índice é derivado; disco é a verdade |
| Escrita | `mkstemp` + `fsync` + `os.replace` | Não deixa arquivo parcial |
| ID | `<nome>-<8 hex do conteúdo>` | Mesmo conteúdo ⇒ mesmo id ⇒ dedup honesto |
| WebView2 ausente | Cai para o navegador | Nunca baixa runtime silenciosamente |
| Risco | Soma de pesos visíveis | Auditável; o que não foi avaliado está escrito |
| Unicode em prosa | Não bloqueia, marca revisão | Bloquear quebraria texto legítimo |
| Unicode em código | Bloqueia | Não há uso legítimo ali |

## Testes

```
tests/
├─ unit/            regras puras: unicode, skills, risco
├─ integration/     fluxos: importação, persistência, servidor HTTP
└─ security/        traversal, arquivos, integridade, pacotes
```

Só dados sintéticos. Nenhum teste executa conteúdo importado.

O ambiente de desenvolvimento não tem Windows nem WebView2, então:

- **Não validado aqui:** janela nativa em WebView2, geração e execução do
  `.exe`, comportamento do SmartScreen, caminhos `%APPDATA%` reais.
- **Validado aqui:** tudo o mais, incluindo o servidor HTTP que a janela
  nativa também carrega.

## Build

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_windows.ps1
```

O script cria o venv, instala as dependências de build, **roda os testes** e
aborta se algum falhar, e só então empacota.

O `.exe` resultante **não é assinado**. Isso é uma decisão registrada: não há
certificado de assinatura de código no projeto (ver D-16), e o Hub não deve
alegar uma garantia que não tem.
