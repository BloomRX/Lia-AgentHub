# Padrão de handoff de design — projetos Lia

Estrutura documental reutilizável para qualquer projeto Lia que use Stitch.
Adapta o padrão sugerido ao que o Hub já faz; não cria estrutura paralela.

## Estrutura

```
docs/design/
├── DESIGN-SYSTEM.md            tokens, componentes, regras de uso
├── DESIGN-DECISIONS.md         o que foi decidido, quando e por quê
├── stitch/
│   ├── screens/                um arquivo por tela: id, estados, notas
│   ├── assets/                 imagens e referências visuais
│   ├── prompts/                prompt versionado por tela
│   └── exports/                HTML/CSS exportado do Stitch
├── approved/                   design aprovado + revisão + data
└── implementation-mapping/     tela -> componente/módulo; divergências
```

Por que esta forma e não outra: o Hub trata **arquivo como fonte de verdade**,
com índice JSON ao lado. Um diretório por tipo de artefato permite ao agente
encontrar o que precisa sem abrir tudo, e permite diff por etapa — o prompt de
uma tela muda sem tocar no design aprovado de outra.

## O que cada arquivo precisa registrar

Nenhum destes campos é decorativo: cada um responde a uma pergunta que aparece
depois. Um handoff sem eles obriga a reconstruir a história.

| Campo | Onde | Pergunta que responde |
|---|---|---|
| Projeto Stitch + id | `stitch/screens/<tela>.md` | De onde veio esta tela? |
| Revisão/versão do design | `approved/<tela>.md` | Qual versão foi implementada? |
| Design system usado | `DESIGN-SYSTEM.md` | Que tokens regem isto? |
| Prompt relevante | `stitch/prompts/<tela>.md` | Como reproduzir ou ajustar? |
| Decisão aprovada | `DESIGN-DECISIONS.md` | Por que está assim? |
| Assets e referências | `stitch/assets/` | O que compõe a tela? |
| Componentes esperados | `approved/<tela>.md` | O que implementar, com que nome? |
| Estados e comportamentos | `stitch/screens/<tela>.md` | E quando dá erro? E vazio? |
| Módulo correspondente | `implementation-mapping/` | Onde isto entra no código? |
| Pendências | `implementation-mapping/pending.md` | O que falta? |

## Modelo de tela

`docs/design/stitch/screens/<slug>.md`:

```markdown
# <Nome da tela>

- **Projeto Stitch:** 14298534195629906316
- **Screen id:** <id no Stitch>
- **Revisão do design:** <r1 / data>
- **Design system:** docs/design/DESIGN-SYSTEM.md

## Propósito
<uma frase: que tarefa o usuário completa aqui>

## Estados
| Estado | Descrição | Referência |
|---|---|---|
| padrão | ... | stitch/exports/<tela>-padrao.html |
| vazio | ... | stitch/exports/<tela>-vazio.html |
| carregando | ... | |
| erro | ... | |
| sem permissão | ... | |

## Componentes esperados
| Componente | Variante | Módulo previsto |
|---|---|---|
| Button | primary | ui/Button |

## Comportamentos
- ...

## Pendências
- ...
```

## Modelo de aprovação

`docs/design/approved/<slug>.md`:

```markdown
# Aprovação — <tela>

- **Aprovado em:** <data>
- **Revisão Stitch:** <id/data da revisão>
- **Aprovado por:** <humano>
- **Revisão anterior superseded:** <id>

## O que foi aprovado
<screenshot e/ou export referenciados por caminho>

## O que NÃO está aprovado
<partes geradas que foram descartadas e por quê>
```

Aprovar sem registrar revisão torna impossível responder "isto implementado é
o design aprovado?". O campo `superseded` é o que permite voltar atrás sem
apagar a decisão anterior.

## Regra de precedência

Quando design e código divergem, a ordem de decisão é:

1. **Requisito e contrato do produto** — manda sempre.
2. **Design aprovado** — referencia visual, cede ao requisito.
3. **Implementação** — deve seguir 1 e 2; divergência é bug ou design
   desatualizado, nunca licença para mudar contrato.

Se o mockup não cabe na arquitetura, o mockup está errado. Registrar a
divergência em `implementation-mapping/divergences.md` é obrigatório — silêncio
transforma divergência em dívida invisível.

## O que este padrão não faz

- Não instala Stitch nem configura MCP. Ver `docs/stitch/MCP-SETUP.md`.
- Não executa Skill. É documentação de processo.
- Não é obrigatório para projetos que não usam Stitch: as etapas 1, 2, 6 e 7
  do workflow funcionam com qualquer ferramenta de design.
