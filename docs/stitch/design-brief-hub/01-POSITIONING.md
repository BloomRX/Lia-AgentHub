# 01 — Posicionamento

## O que o Hub é

Infraestrutura de **curadoria e distribuição de capacidades** para o
ecossistema Lia. O usuário importa uma Skill ou servidor MCP, o Hub calcula
hash, registra proveniência e licença, coloca em quarentena, e o usuário
decide — com evidência à vista — se aquilo vira parte da biblioteca.

## Para quem

| Perfil | O que faz na ferramenta |
|---|---|
| **Curador** (principal) | importa, inspeciona, decide confiança e licença, publica |
| **Autor** (Lia Studio) | valida o próprio trabalho antes de importar (`dry_run`) |
| **Consumidor técnico** (Lia Go, Forge, Model Lab) | lê índice, exporta pacote, verifica integridade |

O curador é o usuário real da UI. Os outros dois consomem por API, não por
tela — projetar tela "bonita" para eles seria trabalho desperdiçado.

## Proposta de valor em uma frase

> Você sabe exatamente o que está entrando, de onde veio, e o que pode fazer
> com aquilo — antes de usar.

## O que o Hub não é — e a UI não pode sugerir que seja

| Não é | Consequência de design |
|---|---|
| Repositório de apps | Não há "instalar e rodar". Há importar e distribuir. |
| Gerenciador de plugins em execução | Nunca mostrar "ativo", "rodando", "conectado" |
| Loja de Skills | Não há download em um clique sem revisão |
| Cofre de credenciais | Nunca pedir, exibir ou sugerir armazenar segredo |
| Verificador de segurança | O risco é heurístico e isso precisa estar visível |

## As quatro distinções que a UI deve tornar impossíveis de confundir

Este é o requisito de design mais importante do produto.

| Distinção | Erro que evita |
|---|---|
| **Catalogado ≠ confiável** | `trust: unreviewed` é o padrão. Não é selo de aprovação. |
| **Licença declarada ≠ permissão** | `redistributable` nasce `false`. |
| **Integridade ≠ autenticidade** | Hash detecta alteração; não prova autoria. |
| **Disponível ≠ executável** | O Hub nunca executa conteúdo importado. |

Uma tela que mostre um recurso importado com visual de "pronto para usar" está
mentindo, mesmo com texto correto ao lado — a percepção visual pesa mais que a
letra miúda.

## Referências visuais

- Os outros projetos Lia (Studio, Project, Forge) usam interface desktop
  escura quando há UI própria; o Hub deve parecer da mesma família, sem copiar
  layout que não resolve o problema dele.
- O Hub roda em **janela desktop (pywebview)** e também no navegador
  (`--no-window`). A UI precisa funcionar nos dois: sem dependência de
  recurso exclusivo de SO.

## Tensão a resolver no design

O público é técnico, mas o produto precisa ser usável por quem não lê hash.
A saída não é esconder o hash — é **hierarquizar**: o veredito ("integro",
"alterado", "não sei") em primeiro plano, o valor verificável atrás.
