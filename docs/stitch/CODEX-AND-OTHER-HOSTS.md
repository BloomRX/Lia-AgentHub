# Instalação no Codex e em outros hosts

Duas coisas independentes, frequentemente confundidas:

- **Skills** — instruções em `SKILL.md`, consumidas pelo agente.
- **MCP server** — serviço remoto, configurado no cliente (ver `MCP-SETUP.md`).

Uma não instala a outra. Ter as Skills não dá acesso ao Stitch; ter o MCP não
faz o agente saber *como* conduzir o trabalho de design.

## 1. Codex — marketplace (recomendado)

O repositório oficial publica três plugins registráveis como marketplace.

### Via CLI

```bash
codex plugin marketplace add google-labs-code/stitch-skills --ref main \
  --sparse .agents/plugins \
  --sparse plugins/stitch-design \
  --sparse plugins/stitch-build \
  --sparse plugins/stitch-utilities
```

Os `--sparse` são opcionais; limitam o checkout para clone mais rápido.

### Via UI

**Settings → Plugin Marketplaces → Add**:

| Campo | Valor |
|---|---|
| Source | `https://github.com/google-labs-code/stitch-skills` |
| Git ref | `main` |
| Sparse paths | *(opcional)* `.agents/plugins`, `plugins/stitch-design`, `plugins/stitch-build`, `plugins/stitch-utilities` |

Depois de registrar o marketplace, instalar a combinação necessária de
`stitch-design`, `stitch-build` e `stitch-utilities` — pela UI do Codex
(**Settings → Plugin Marketplaces**), que lista os plugins disponíveis após o
registro.

> **Não documentamos um comando de instalação por CLI porque a documentação
> oficial do repositório não publica um.** O README mostra `codex plugin
> marketplace add` e, em seguida, diz "install any combination of" sem
> apresentar a sintaxe de instalação. Inventar `codex plugin install ...` com
> flags plausíveis produziria instrução que pode não existir — e o usuário
> descobriria isso falhando. A UI é o caminho verificado.
>
> Para Claude Code e Cursor há comando publicado (§2), e é o que usamos.

**Regra prática:** instalar por projeto, não globalmente. Dezesseis Skills
instaladas no usuário poluem o contexto de sessões que não fazem design, e
criam 16 cópias a atualizar quando o upstream andar.

## 2. Claude Code e Cursor

```bash
npx plugins add google-labs-code/stitch-skills --scope project --target claude-code
npx plugins add google-labs-code/stitch-skills --scope workspace --target cursor
```

## 3. OpenCode e hosts sem marketplace

Instalação manual: copiar as pastas de Skill necessárias para um caminho
descoberto pelo host, e configurar o MCP separadamente (`MCP-SETUP.md`).
OpenCode não usa `npx plugins` nem o layout de marketplace do Codex/Claude.

## 4. os três grupos

| Plugin | Skills | Uso |
|---|---|---|
| `stitch-design` | 6: `generate-design`, `code-to-design`, `manage-design-system`, `extract-design-md`, `extract-static-html`, `upload-to-stitch` | criar e extrair design |
| `stitch-build` | 5: `react-components`, `react-native`, `react-vite-dashboard`, `remotion`, `shadcn-ui` | transformar design em código |
| `stitch-utilities` | 5: `design-md`, `enhance-prompt`, `site-md`, `stitch-loop`, `taste-design` | apoio: prompt, DESIGN.md, iteração |

Detalhe por Skill, com dependências, em `CATALOG.md`.

## 5. Atualização

```bash
codex plugin marketplace update google-labs-code/stitch-skills
```

Skills upstream mudam. O Hub registra o commit do catálogo
(`google-stitch.records.json` → `source.commit`); quando o upstream andar, o
catálogo precisa ser regenerado para não descrever uma versão que não existe
mais:

```bash
git -C /tmp/stitch/repo pull
PYTHONPATH=src .venv/bin/python docs/stitch/tools/build-stitch-catalog.py \
  --repo /tmp/stitch/repo --out docs/stitch/catalog
```

## 6. Quatro estados — de novo, porque é aqui que se erra

| Estado | Pergunta | Quem responde |
|---|---|---|
| **Catalogada no Hub** | Existe registro com hash e licença? | `docs/stitch/catalog/google-stitch.records.json` |
| **Instalada no agente** | O host carrega o `SKILL.md`? | Configuração do host (marketplace ou cópia manual) |
| **MCP configurado** | O cliente tem o endpoint? | Arquivo de config do cliente |
| **Disponível na sessão** | O agente vê a ferramenta agora? | Sessão em execução |

Cada uma depende da anterior e nenhuma implica a seguinte. O Hub cobre a
primeira — só ela.

**O Hub nunca afirma que um recurso está operacional porque foi catalogado.**
Um registro com `connectivityVerified: false` diz exatamente isso: o Hub sabe
que o serviço existe e como se conectar; não sabe se você está conectado.

## 7. O que o Hub NÃO deve fazer

- **Não copiar todas as Skills para todos os projetos.** O marketplace existe
  para isso. Despejar 16 Skills em todo repositório enche o contexto do agente
  com instruções irrelevantes e ainda cria 16 cópias para atualizar.
- **Não instalar automaticamente.** Instalar muda o ambiente do host; é
  decisão do usuário.
- **Não esconder a dependência externa.** Usar Stitch exige conta Google. Um
  projeto que documenta "design feito com Stitch" tem uma dependência de
  serviço de terceiros, e isso deve estar visível.

## 8. Alternativa sem Stitch

As etapas 1, 2, 6 e 7 do `workflow/lia-uiux-workflow.md` funcionam com
qualquer ferramenta de design. Stitch é integração de primeira classe no Hub
porque já é usado no Lia-Project — não porque seja obrigatório. Um projeto Lia
pode adotar o padrão de handoff (`handoff/README.md`) sem adotar Stitch.
