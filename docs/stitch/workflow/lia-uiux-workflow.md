---
name: lia-uiux-workflow
description: Fluxo completo de UI/UX para projetos Lia usando Google Stitch, de discovery a feedback de implementação. Use quando o trabalho envolver desenhar, revisar ou entregar interface — não para implementar a tela.
license: none-declared
metadata:
  domain: design
  tags: ui, ux, stitch, design-system, handoff
  author: Lia Agent Hub
  version: "1.0.0"
---

# Workflow de UI/UX do ecossistema Lia

Sete etapas, do entendimento à conferência da implementação. Provider-neutral
onde faz sentido; Stitch é integração de primeira classe porque já é usado no
Lia-Project, não porque seja obrigatório.

**Princípio que atravessa tudo:** Stitch é a fonte de referência **visual** do
design aprovado. Código, contratos e requisitos do projeto Lia continuam sendo
a fonte da verdade **funcional e arquitetural**. Nenhuma etapa aqui autoriza
mudar um contrato para acomodar um mockup.

## 1. Discovery

Objetivo: entender o problema antes de desenhar qualquer tela.

1. Ler a documentação do produto no próprio projeto (`docs/`, README, ADRs).
2. Identificar usuários, plataformas e restrições reais (não as supostas).
3. Localizar o design system existente, se houver, e o que já está em uso.
4. Levantar o que o produto **já faz**: a UI representa funcionalidade
   existente. Inventar tela para recurso inexistente é escopo, não design.

Saída: `docs/design/DESIGN-DECISIONS.md` com o que foi entendido e as dúvidas
abertas. Dúvida não resolvida é registrada, não preenchida com suposição.

## 2. Design brief

Traduzir requisito em direção visual e funcional.

- Arquitetura de navegação: quais áreas, como se chega a cada uma.
- Inventário de telas e, para cada uma, os **estados** (vazio, carregando,
  erro, sucesso, sem permissão) — não só o caminho feliz.
- Responsividade: o que muda e em qual ponto de quebra.
- Acessibilidade: contraste, foco, alvo de toque, leitor de tela, teclado.
- Interações e transições que o usuário percebe.

Saída: seção de brief em `DESIGN-DECISIONS.md`, pronta para virar prompt.

## 3. Prompt engineering

Usar a Skill `enhance-prompt` antes de gerar. Um prompt para Stitch precisa
de: tipo de tela, público, densidade de informação, identidade visual,
componentes esperados e o que **não** deve aparecer.

Exige consistência entre telas: o mesmo botão, a mesma cor semântica, o mesmo
espaçamento. Prompt isolado por tela produz UI coerente apenas por acidente.

Saída: `docs/design/stitch/prompts/<tela>.md`, versionado. Prompt é artefato,
não conversa perdida.

## 4. Design generation

- Criar telas e variantes no Stitch (via MCP, no host conectado).
- Usar o design system quando existir (`create_design_system` /
  `apply_design_system`), em vez de reescrever tokens em cada prompt.
- Gerar **mais de uma** variante para as telas importantes.

**Não aceitar a primeira geração.** A primeira geração é rascunho. Comparar,
refinar, e só então promover para revisão.

## 5. Design validation

Checklist objetivo, na ordem:

| Verificação | Como |
|---|---|
| Hierarquia visual | O que o olho vê primeiro é o que importa primeiro? |
| Consistência de componente | Mesmo componente aparece igual em todas as telas? |
| Estados | Vazio, carregando, erro, sucesso, sem permissão existem? |
| Responsividade | Layout sobrevive a 360 px e a 1920 px? |
| Acessibilidade | Contraste, foco visível, alvos ≥ 44 px, ordem de tabulação |
| Usabilidade | Dá para completar a tarefa sem instrução externa? |
| Elementos genéricos | Avatar fake, "Lorem ipsum", ícone sem sentido — remover |

Design reprovado aqui volta para a etapa 4. Reprovar é o resultado normal.

## 6. Handoff

Produzir o que a implementação precisa, na estrutura de
`docs/design/README.md`:

- screenshots e referências de cada tela aprovada;
- HTML/CSS exportado quando o Stitch fornecer (`extract-static-html`);
- `DESIGN.md` gerado ou atualizado (`design-md` / `extract-design-md`);
- assets e componentes com nome e localização;
- especificação de estados e comportamentos;
- mapa tela → componente/módulo **real** do projeto
  (`implementation-mapping/`).

Saída: design aprovado registrado em `docs/design/approved/` com a revisão do
Stitch e a data. Aprovar sem registrar revisão torna impossível saber qual
design foi implementado.

## 7. Implementation feedback

Depois que a tela é implementada:

1. Comparar implementação com o design aprovado, lado a lado.
2. Registrar divergências em `implementation-mapping/divergences.md` com
   decisão: corrigir o código, ou ajustar o design (e por quê).
3. Voltar ao Stitch quando o design é que está errado.
4. **Nunca** modificar contrato, regra de negócio ou comportamento do produto
   só para acomodar o mockup. Se o mockup não cabe na arquitetura, o mockup
   está errado.

## Onde cada etapa vive

| Etapa | Artefato | Fonte da verdade |
|---|---|---|
| 1 Discovery | `docs/design/DESIGN-DECISIONS.md` | projeto |
| 2 Brief | `DESIGN-DECISIONS.md` § brief | projeto |
| 3 Prompt | `stitch/prompts/*.md` | projeto |
| 4 Geração | projeto Stitch (remoto) | Stitch |
| 5 Validação | checklist nesta Skill | projeto |
| 6 Handoff | `approved/`, `exports/`, `DESIGN.md` | ambos |
| 7 Feedback | `implementation-mapping/` | projeto |

## O que este workflow não faz

- Não implementa a tela. A Skill descreve o processo; a implementação é do
  agente no repositório do projeto.
- Não executa nada. É texto de instrução; o Hub nunca roda Skill importada.
- Não conecta no Stitch. Se o host não tiver MCP autenticado, as etapas 4 e 5
  ficam bloqueadas — e o trabalho independente (1, 2, 3, 6, 7) continua.
