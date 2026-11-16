# Pacote de design brief — Lia Agent Hub

Material pronto para entregar o UI/UX do Hub ao Stitch. Não contém tela final:
contém o que é necessário para produzi-las sem repetir a investigação
arquitetural.

**Regra que vale para todo este pacote:** nada aqui inventa funcionalidade. Cada
tela listada corresponde a rota e método que existem hoje em
`src/lia_agenthub/interface/server.py` e `src/lia_agenthub/app.py`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `01-POSITIONING.md` | público, proposta de valor, o que o Hub não é |
| `02-INFORMATION-ARCHITECTURE.md` | mapa de telas derivado das rotas reais |
| `03-DESIGN-SYSTEM.md` | tokens e componentes iniciais |
| `04-STATES-AND-INTERACTIONS.md` | estados por tela, mensagens, erros |
| `05-PROMPTS.md` | prompts completos, prontos para colar no Stitch |

## Quantidades reais (medidas, não estimadas)

| Item | Quantidade | Fonte |
|---|---|---|
| Rotas HTTP | 20 | `interface/server.py` |
| Métodos públicos de `AgentHub` | 24 | `app.py` |
| Tipos de recurso | 11 | `domain/model.py` `ResourceType` |
| Estados de ciclo de vida | 5 | `Lifecycle` |
| Níveis de confiança | 4 | `Trust` |

## Antes de gerar

Ler, nesta ordem: `MCP-SETUP.md` (conectar), `CATALOG.md` (capacidades
disponíveis), `workflow/lia-uiux-workflow.md` (processo).

O projeto Stitch do usuário é `14298534195629906316`. **Nesta sessão não houve
acesso autenticado ao MCP**, então nenhuma tela foi criada nem alterada — ver
`../STITCH-INTEGRATION-REPORT.md` §4. Os prompts estão prontos para uso por
quem tiver a conexão.

## Princípio de projeto

O Hub é uma ferramenta de **curadoria e distribuição**, não um runtime. A UI
precisa deixar visível a diferença entre:

- o que está catalogado (existe registro),
- o que foi revisado por humano (`trust`),
- o que pode ser redistribuído (`license.redistributable`),
- o que está em quarentena (não publicado).

Uma tela que esconde essas diferenças produz usuário que acredita ter algo que
não tem. Esse é o risco de design mais sério deste produto.
