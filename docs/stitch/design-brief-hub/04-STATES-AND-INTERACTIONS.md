# 04 — Estados e interações

Toda tela precisa dos estados abaixo. "Caminho feliz" é o menor dos casos: o
valor desta ferramenta está justamente em mostrar o que deu errado.

## Estados por tela

### Biblioteca

| Estado | O que mostra |
|---|---|
| Vazia | "Nenhuma capacidade ativa." + botão **Importar** |
| Só quarentena | "Nada na biblioteca ainda. Há N itens na quarentena." + link |
| Filtro sem resultado | "Nenhum item corresponde a <filtro>." + **limpar filtros** |
| Cheia | Lista paginada com contagem por tipo |
| Erro de leitura | Banner: "N registros não puderam ser lidos." + ação **Diagnóstico** |

O estado "erro de leitura" importa: o repositório registra `erros_de_leitura`
justamente para não mostrar biblioteca menor em silêncio. A UI que o ignora
desfaz a proteção.

### Detalhe

| Estado | O que mostra |
|---|---|
| Íntegro | `IntegrityChip: ok` + quando foi verificado |
| Alterado | `IntegrityChip: mismatch` em vermelho + "o conteúdo mudou desde a importação" |
| Licença desconhecida | `LicenseBadge: unknown` + "não significa livre" |
| Risco alto | `RiskMeter: high` + **lista de `notEvaluated`** |
| Sem licença declarada | base da evidência vazia, explicitamente "não declarada" |
| Substituída | badge `superseded` + link para a versão atual |

### Importar

| Estado | O que mostra |
|---|---|
| Simulando | lista do que seria gravado, com hash por arquivo |
| Simulação ok | "Nada foi gravado." + **Confirmar importação** |
| Simulação com avisos | avisos agrupados, importação ainda possível |
| Bloqueado | motivo com **código** (`NAME_FORMAT`, `NO_FRONTMATTER`, `SECURITY`) |
| Importado | "Está na quarentena." + **Promover** / **Ver detalhes** |
| Já existia | "Conteúdo idêntico já está aqui." + link para o existente |

### Exportar

| Estado | O que mostra |
|---|---|
| Destino privado | permitido, sem aviso |
| Destino compartilhado | aviso de redistribuição |
| Destino público | **recusado** se `redistributable: false`, com motivo |
| Sucesso | caminho do pacote + hash |
| Lote parcial | tabela: N sucessos, M falhas, motivo por falha |

### Verificar pacote

| Estado | O que mostra |
|---|---|
| Íntegro | "Hash confere." + **"Isso não prova quem criou."** |
| Alterado | "O conteúdo não corresponde ao manifesto." |
| Malformado | "Não é um pacote válido." + detalhe |

## Interações críticas

### Promover

Diálogo de confirmação com resumo do que muda:

> **Promover para a biblioteca**
> `nome` — versão `x` — tipo
> Confiança atual: `unreviewed` · Licença: `unknown`
> Promover **não** marca como confiável nem autoriza redistribuição.
> [ Cancelar ] [ Promover ]

A frase de efeito é obrigatória: o usuário confunde promover com aprovar.

### Descartar

Destrutivo. Exige digitar o nome do recurso. Mostra o que se perde (o payload
não é recuperável pela UI).

### Definir confiança

Seletor com os 4 níveis e consequência textual de cada um. Registrar
`decided_by`. Nunca pré-selecionar acima de `unreviewed`.

### Definir licença

Campo de código SPDX + toggle `redistributable` + base da decisão (texto).
`redistributable` só habilita export público.

## Mensagens — princípios

1. **Dizer o que aconteceu, não o que o usuário fez de errado.**
   "O arquivo não começa com frontmatter" > "Entrada inválida".
2. **Sempre com próxima ação** quando houver ação possível.
3. **Nunca prometer segurança.** "Hash confere" ≠ "é seguro".
4. **Códigos visíveis** para erro estrutural: o usuário precisa poder buscar.
5. **Sem exclamação, sem "Ups!".** O tom é de ferramenta técnica.

## Microinterações

- Importação e exportação são lentas o suficiente para precisar de progresso
  **real** (contagem de arquivos), nunca indeterminado.
- Verificar pacote: resultado imediato, sem animação de "pensando".
- Filtros aplicam sem recarregar a lista inteira.
- Hover em hash mostra o valor completo; cópia com um clique.

## Foco e teclado

- `/` foca a busca (padrão de ferramenta técnica).
- `Esc` fecha modal sem perder o que foi digitado no formulário de importação.
- `Enter` na lista abre o detalhe.
- Navegação completa por teclado: nenhuma ação exclusiva de mouse.
