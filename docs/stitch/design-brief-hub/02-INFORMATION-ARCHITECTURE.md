# 02 — Arquitetura de informação

Derivada das **20 rotas HTTP** que existem hoje. Nenhuma tela aqui corresponde a
funcionalidade futura.

## Navegação principal

Quatro áreas. A ordem reflete o fluxo real de trabalho do curador, não uma
taxonomia abstrata.

```
┌─────────────────────────────────────────────────────┐
│ Lia Agent Hub                          [Busca] [⚙] │
├──────────┬──────────────────────────────────────────┤
│          │                                          │
│ Biblioteca│  (área selecionada)                      │
│ Quarentena│                                          │
│ Distribuição│                                        │
│ Diagnóstico│                                         │
│          │                                          │
└──────────┴──────────────────────────────────────────┘
```

| Área | Rotas que a alimentam | Pergunta do usuário |
|---|---|---|
| **Biblioteca** | `GET /api/items`, `GET /api/items/<id>`, `POST /api/items` | "O que eu tenho e posso usar?" |
| **Quarentena** | `GET /api/quarantine`, `POST /api/promote`, `POST /api/discard` | "O que entrou e precisa de decisão?" |
| **Distribuição** | `/api/export`, `/api/export-many`, `/api/verify-package`, `/api/publish-index`, `/api/index` | "Como entrego isto para outro projeto?" |
| **Diagnóstico** | `/api/diagnostics`, `/api/settings`, `/api/history`, `/api/diff` | "Está tudo íntegro? O que mudou?" |

`Importar` é ação **global** (não uma quinta área): botão persistente no topo,
porque acontece a partir de qualquer tela.

## Telas necessárias

### 1. Biblioteca (lista)

- Lista de capacidades ativas, com nome, tipo, versão, `trust`, licença.
- Busca e filtros: texto, tipo, domínio, tag, confiança
  (`GET /api/items?q=&type=&domain=&tag=&trust=`).
- Filtro de ciclo de vida para incluir substituídas (`lifecycle=all`).
- Estado vazio: explica que a biblioteca começa vazia e aponta importação.

### 2. Detalhe da capacidade

A tela mais densa do produto. Seções:

| Seção | Campos |
|---|---|
| Identidade | nome, versão, tipo, descrição, namespace |
| Confiança | nível (`Trust`), quem decidiu, quando |
| Licença | código, status, `redistributable`, base da evidência |
| Integridade | `contentHash`, `treeHash`, verificação atual |
| Risco | nível, fatores, **o que a heurística não avalia** |
| Proveniência | upstream, método, data, linha do tempo (`history`) |
| Conteúdo | lista de arquivos, presença de scripts |
| Ações | validar, confiar, licença, exportar, descartar, ver diferenças |

O bloco de risco **precisa** mostrar `notEvaluated`. Um nível "alto" sem a
lista do que não foi verificado vira alarme ignorado.

### 3. Quarentena

- Lista do que foi importado e não promovido.
- Para cada item: motivo de estar aqui, avisos da importação, o que fazer.
- Ações em par: **Promover** e **Descartar**. Promover exige confirmação
  explícita; descartar exige confirmação mais forte (é destrutivo).

### 4. Importar

Passo a passo, não um botão:

1. Origem (caminho local, ZIP, `.lia-capability`).
2. **Simulação** (`dry_run`) — mostra o que *seria* gravado, com hashes,
   avisos e problemas, sem tocar no disco.
3. Confirmação → quarentena.
4. Resultado: issues agrupados por severidade; se bloqueado, motivo com código.

A simulação existe na API e precisa ser a primeira coisa que o usuário vê.

### 5. Exportar

- Escolha do destino (`private`, `self`, `shared`, `public`).
- Aviso por destino: `public` é recusado sem direito comprovado.
- Resultado: caminho do pacote, hash, avisos.
- Lote: um resultado por item, falha não aborta os outros
  (`export_many`).

### 6. Índice / Distribuição

- Estado do índice publicado, quantos itens, quarentena excluída.
- Saúde (`index_health`): pacotes ausentes, órfãos, fantasmas, não indexados.
- Ação: publicar índice.

### 7. Verificar pacote

- Recebe um `.lia-capability` e responde: íntegro, alterado, ou ilegível.
- Sempre lembrar: **íntegro não é assinado**.

### 8. Diagnóstico e configurações

- Contagem por área, erros de leitura, saúde do índice.
- Configurações (`settings`), com reset explícito.

### 9. Comparar versões (`GET /api/diff`)

- Diferença entre duas versões: arquivos, hash, metadado.
- Onde a mudança alterou o conteúdo e onde só o metadado.

## Hierarquia de informação

Em toda tela, nesta ordem de peso visual:

1. **Veredito** — aprovado / quarentena / alterado / não sei.
2. **Consequência** — o que o usuário pode ou não fazer.
3. **Evidência** — hash, licença, proveniência.
4. **Detalhe técnico** — caminhos, IDs, JSON.

O erro comum seria inverter: começar pelo hash. Hash é evidência, não conclusão.

## O que não é uma tela

| Não criar tela para | Porque |
|---|---|
| Executar capacidade | O Hub não executa |
| Configurar credencial de MCP | É do host, não do Hub |
| Chat com o conteúdo importado | O Hub não é runtime |
| Loja / catálogo público | Não há decisão de distribuição pública |
