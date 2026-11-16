# Catálogo — Google Stitch no Lia Agent Hub

> **Gerado automaticamente.** Não editar à mão: a fonte é
> `catalog/google-stitch.records.json`, produzido pelo importador de
> produção do Hub em `tools/build-stitch-catalog.py`. Este arquivo é
> a apresentação do registro, não uma segunda verdade.

- **Upstream:** https://github.com/google-labs-code/stitch-skills
- **Commit:** `0337446dadde`
- **Endpoint MCP:** `https://stitch.googleapis.com/mcp`
- **Registros:** 17 (1 serviço, 16 skills)
- **Falhas de importação:** 0

## Servidor MCP

### `google-stitch-mcp`

- **Tipo:** `mcp-server`
- **Endpoint:** `https://stitch.googleapis.com/mcp`
- **Transporte:** `http`
- **Autenticação:** `api-key`
- **Cabeçalhos (nomes):** `X-Goog-Api-Key`
- **Categoria:** UI/UX Design
- **Egress declarado:** ['https://stitch.googleapis.com/mcp']
- **Conectividade verificada:** `False` — o Hub não conecta
- **Licença:** serviço regido pelos Google APIs ToS; o Hub distribui a configuração, não o serviço

Configuração do host: [`MCP-SETUP.md`](MCP-SETUP.md).

## Skills

### `stitch-build` — 5 skills

| Skill | Namespace | Depende de | Descrição |
|---|---|---|---|
| `react-components` | stitch | — | Converts Stitch designs into modular Vite and React components, or syncs/updates existing React components … |
| `react-native` | stitch | — | Convert Stitch HTML designs to React Native components, or syncs/updates existing native components to alig… |
| `react-vite-dashboard` | — | — | Convert Stitch designs into production React + Vite dashboards with TanStack Query, accessible tokens from … |
| `remotion` | — | — | Generate walkthrough videos from Stitch projects using Remotion with smooth transitions, zooming, and text … |
| `shadcn-ui` | — | — | Expert guidance for integrating and building applications with shadcn/ui components, including component di… |

### `stitch-design` — 6 skills

| Skill | Namespace | Depende de | Descrição |
|---|---|---|---|
| `code-to-design` | stitch | `extract-design-md`, `extract-static-html`, `manage-design-system`, `upload-to-stitch` | Convert frontend code (Vite, React, Angular, Vue, etc.) to a Stitch Design by chaining static HTML extracti… |
| `extract-design-md` | stitch | — | Extract a comprehensive design system (DESIGN.md) directly from frontend source code — React, Vue, Svelte, … |
| `extract-static-html` | stitch | — | Extract self-contained static HTML from a built web application or React components by inlining CSS and ima… |
| `generate-design` | stitch | — | Generate new screens from text prompts or images, edit existing screens with prompts and design system toke… |
| `manage-design-system` | stitch | `code-to-design`, `upload-to-stitch` | Manage design systems in Stitch using MCP tools. Includes retrieval of assets, creating/updating design sys… |
| `upload-to-stitch` | stitch | `extract-static-html` | Upload local assets (images, mockups, extracted HTML, design markdown) to a Stitch project. ALWAYS use this… |

### `stitch-utilities` — 5 skills

| Skill | Namespace | Depende de | Descrição |
|---|---|---|---|
| `design-md` | — | — | Analyze Stitch projects and synthesize a semantic design system into DESIGN.md files |
| `enhance-prompt` | — | — | Transforms vague UI ideas into polished, Stitch-optimized prompts. Enhances specificity, adds UI/UX keyword… |
| `site-md` | — | — | Analyze a project description or site requirements and synthesize a project constitution into SITE.md for t… |
| `stitch-loop` | — | — | Teaches agents to iteratively build websites using Stitch with an autonomous baton-passing loop pattern |
| `taste-design` | — | — | Semantic Design System Skill for Google Stitch. Generates agent-friendly DESIGN.md files that enforce premi… |

## Licença e proveniência

Todo registro acima aponta para o mesmo upstream e o mesmo commit.
A licença **não** está no frontmatter de nenhuma das 16 Skills — ela é
declarada no `LICENSE` da raiz do repositório de origem:

| Item | Evidência |
|---|---|
| Licença do upstream | Apache-2.0 (`LICENSE` na raiz) |
| Natureza | **Declaração do upstream**, não permissão verificada pelo Hub |
| Redistribuição | `redistributable: false` — decisão humana |
| Autoria | google-labs-code (não é conteúdo de projeto Lia) |

O Hub registra a evidência; não conclui direito de uso.

## Como os agentes usam

O registro descreve a capacidade. Para **usar**, o host precisa
instalar as Skills e configurar o MCP — estados distintos, descritos em
[`CODEX-AND-OTHER-HOSTS.md`](CODEX-AND-OTHER-HOSTS.md) §6.

O processo de trabalho está em
[`workflow/lia-uiux-workflow.md`](workflow/lia-uiux-workflow.md).
