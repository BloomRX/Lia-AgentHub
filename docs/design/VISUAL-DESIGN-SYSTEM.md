# Sistema visual — Lia Agent Hub

**PROPOSED · v0.1 · 2026-11-15.** Especificação própria do Hub, consistente com BRAND-STANDARDS da família, sem impor biblioteca/stack. Valores abaixo não são tokens oficiais de todos os Lia. Relação com fontes em [RESEARCH-REFERENCES](RESEARCH-REFERENCES.md).

## 1. Princípio de composição

**Superfícies quietas, ação nítida, evidência legível.** A marca aparece no nome, no monograma provisório e no acento Sakura; não em bordas brilhantes repetidas. Fundo sem imagem em Biblioteca, revisão e formulários. Flor decorativa no máximo no acolhimento, `aria-hidden`, nunca indicador de severidade. Nenhum texto sobre arte. Não utilizar personagem do concept como assistente ativa ou sinal de aprovação.

Uma ação primária por região de decisão. Cabeçalho de página: breadcrumb opcional, título, descrição em uma linha e ação. Conteúdo com largura de leitura de 65–80 caracteres; tabelas/inventários podem ocupar o espaço disponível. No máximo dois painéis concorrentes em desktop; navegação separada do conteúdo.

## 2. Tokens de cor

| Token semântico proposto | Hex | Aplicação |
|---|---|---|
| `--lia-bg-app` | `#100D16` | fundo geral |
| `--lia-bg-surface` | `#191420` | sidebar/cartões |
| `--lia-bg-surface-raised` | `#241C2C` | hover, inputs, menu |
| `--lia-border-subtle` | `#44374E` | separação decorativa, não única identificação de campo |
| `--lia-border-control` | `#897794` | borda necessária de input/controle |
| `--lia-text-primary` | `#F5EFF8` | texto e títulos |
| `--lia-text-secondary` | `#C3B4CB` | descrição e metadados relevantes |
| `--lia-text-muted` | `#A596AF` | apoio, nunca erro essencial |
| `--lia-accent` | `#F472C6` | CTA, link, marca, selecionado |
| `--lia-accent-hover` | `#FA9BD7` | hover primário |
| `--lia-accent-pressed` | `#DE5BB0` | pressionado |
| `--lia-accent-contrast` | `#190D19` | texto sobre botão rosa; não usar branco |
| `--lia-accent-soft` | `#392039` | fundo selecionado, texto accent |
| `--lia-focus` | `#E4C2FF` | outline externo de foco |
| `--lia-status-success` | `#72D8B1` | operação concluída, não “seguro” |
| `--lia-status-success-bg` | `#132C25` | fundo sucesso |
| `--lia-status-warning` | `#F2C66D` | aviso/licença desconhecida |
| `--lia-status-warning-bg` | `#322819` | fundo aviso |
| `--lia-status-error` | `#FF9BA8` | impedimento/erro |
| `--lia-status-error-bg` | `#351D28` | fundo erro |
| `--lia-status-info` | `#A9C7FF` | informação/limite da análise |
| `--lia-status-info-bg` | `#1C263A` | fundo informação |

Cores de status sempre com ícone e rótulo. “Não revisado” usa neutro/lilás, não vermelho automático. “Risco baixo” não usa selo verde autossuficiente. Não usar magenta tanto para erro quanto CTA. Não depender de opacidade sobre arte para contraste.

Metas: texto normal ≥4,5:1; títulos grandes ≥3:1; limite de controle/foco necessário ≥3:1 contra fundo adjacente. Checar combinações propostas com cálculo sRGB e depois no render real, incluindo hover/pressed/selecionado. Contraste de uma borda decorativa pode ser menor; borda do input não. Validar modo de alto contraste Windows com cores do sistema, sem travar cores de foco. Tema claro é alternativa futura, não toggle inoperante.

## 3. Tipografia e escala

Família `"Segoe UI", system-ui, sans-serif`; sem fonte remota e sem pacote novo. Monoespaçada `Consolas, "Cascadia Mono", monospace` para caminhos/hashes/código; fallback obrigatório. Não depender de fonte instalada exclusiva.

| Papel | Tamanho / entrelinha / peso |
|---|---|
| Título de página | 28 / 36 / 600 |
| Título de seção | 20 / 28 / 600 |
| Título de card/diálogo | 16 / 24 / 600 |
| Corpo e controles | 15 / 24 / 400; botão 600 |
| Metadados/ajuda | 13 / 20 / 400 |
| Código | 13 / 20 / 400 |
| Contagem principal | 28 / 36 / 600; números tabulares |

Unidades em rem no produto para zoom. Texto de risco/legal nunca menor que 13px. Títulos em sentence case, não caixa alta contínua. Descrições de card até duas linhas visuais, com texto integral acessível no detalhe. Não truncar mensagem de erro nem nome de arquivo que diferencia um achado.

## 4. Espaçamento, geometria e layout

Escala 4/8/12/16/24/32/48px, compatível com padrão encontrado no Lia Project. Margem de página 32px (desktop), 24px (médio), 16px (estreito). Gap de cards 16px, seções 32px, label–controle 8px. Padding de painel 24px, card 20/24px.

Raios: 8px controle, 10px card, 14px diálogo, pill só badge/tag. Borda 1px. Sombra apenas menus/diálogos: `0 12px 40px #0006`, nunca glow. Outline de foco 2px, offset 3px; gap sólido separa foco do acento.

- ≥1280 CSS px: sidebar 224px; header de conteúdo 72px; grade 3 cards (mínimo 264px); detalhe duas colunas 2fr/1fr, máximo útil 1440px centralizado.
- 1000–1279: sidebar 208px; grade 2 cards; resumo de detalhe pode ficar acima das abas.
- 720–999: menu textual recolhível com botão “Navegação”; duas colunas só se conteúdo comportar 264px por card. Filtros em linhas, nunca sobrepostos.
- <720: uma coluna; filtros em disclosure, contagem e filtros ativos sempre visíveis; metadados `dt/dd` empilhados; ações com wrap. Tablist pode quebrar ou virar seletor rotulado. Tabela só rola horizontalmente em região própria identificada; página não.
- Janela baixa (≤650px): acolhimento removível/compacto; nenhum hero alto. Evitar vários sticky empilhados. Ação fixa deve reservar espaço no final e não cobrir foco/erro. No zoom 200%, usar viewport CSS resultante, não resolução física.

Alvos de interação: 40px altura mínima habitual; 44px para botões ícone/primários em importação; distância mínima 8px. Modo compacto eventual não pode reduzir legibilidade/teclado. Não criar title bar customizada; preservar chrome nativo e controles Windows.

## 5. Componentes e contratos visuais

| Componente | Anatomia e comportamento |
|---|---|
| Navegação | ícone 20px + texto + badge opcional; selecionado com barra 3px e fundo soft; `aria-current=page`; badge com nome “3 capacidades a revisar” |
| Botão primário | fundo accent, texto escuro, 40–44px; hover mais claro, pressed mais escuro; foco externo; pendente “Importando…” + indicador e `aria-busy`; não alterar largura |
| Secundário | surface-raised, borda control, texto primary; hover eleva superfície, não usa o mesmo preenchimento do primário |
| Destrutivo | texto/borda error, confirmação com recurso e efeito; separado do CTA de admissão; Enter não dispara descarte por padrão |
| Input/select | label visível, exemplo separado, ajuda persistente, erro associado por `aria-describedby`; estado inválido com texto e ícone. Placeholder não é label |
| Busca | label “Buscar na biblioteca”, botão limpar nomeado, contagem e filtros ativos; debounce com controle de respostas; não interceptar Ctrl+F nativo |
| Filtro | select simples inicial; valor claro; chips removíveis com nome “Remover filtro Tipo: Skill”; AND entre dimensões; multivalor só com suporte explícito |
| Card de capacidade | ícone tipo, nome/versão, descrição, tipo, lifecycle quando relevante, confiança textual e no máximo dois alertas prioritários; link “Inspecionar”; alertas adicionais “+2 avisos” leva à ficha |
| Lista/tabela | alternativa densa para acervo grande; cabeçalhos semânticos e ordenação anunciada; nome é link, não linha inteira com controles aninhados |
| Badge | informação, não botão; 13px, fundo neutro/semântico; confiança, lifecycle e triagem não se fundem |
| Resumo de evidências | quatro blocos: estrutura, integridade, direitos, decisão humana; estado não informado explícito; cada resumo leva à evidência correspondente |
| Abas de detalhe | Resumo / Arquivos / Procedência e licença / Verificações / Versões e histórico; teclado setas/Home/End, seleção/foco distinguíveis; não perder estado da aba ao copiar hash |
| Inventário | caminho relativo, tamanho quando disponível, marcador script/executável; nome completo com wrap; leitura textual futura nunca executa conteúdo |
| Achado | severidade em português + código original, mensagem, arquivo/linha/coluna quando conhecidos, limite da regra e link à evidência; não inventar localização |
| Confirmação | título verbal, resumo do efeito, recurso/versão, cancelar e confirmar; foco inicial na opção segura; Escape cancela sem persistir |
| Mensagem inline | título, descrição, ação de recuperação; alerta bloqueante usa `role=alert` sem repetição; sucesso usa `role=status`; resultado permanece na tela |
| Toast | apoio de sucesso sem ser único comprovante; `aria-live=polite`; dispensável, não para decisões/recusas de exportação |
| Skeleton | estrutura estável, `aria-busy=true`, texto “Carregando biblioteca”; sem shimmer obrigatório, esconder linhas falsas da árvore acessível |

Ícones: família de traço única, 20/24px, espessura 1,75–2; livro (biblioteca), caixa (capacidade), documento (Skill), nós (MCP), terminal (CLI), globo (API), peça (plugin), camadas (framework), chip (provider), fluxo (workflow), arquivo (referência), bandeja (revisão), seta para dentro (importar), para fora (exportar), engrenagem. Não usar play/power como ação de catálogo. SVG local curado é suficiente; adoção de biblioteca exige licença e necessidade registradas, não é dependência desta proposta. Monograma “L” do protótipo é provisório, não novo logo oficial.

## 6. Estados interativos e movimento

Default → hover (contraste/fundo) → pressed → pendente → sucesso/erro. Foco é independente de hover/seleção. Disabled só se razão visível; não criar cartões indisponíveis para funcionalidades futuras. Tooltip apenas complementa, com teclado e Escape, nunca contém informação exclusiva.

Transições 150ms para cor/fundo/opacidade; sem parallax, partículas ou blur animado. `prefers-reduced-motion` remove movimento não essencial; progresso indeterminado tem texto. Não fabricar porcentagem/ETA quando operação só retorna ao final.

## 7. Regras de linguagem

| Evitar | Usar |
|---|---|
| Tudo sincronizado | Acervo local / Índice consistente com o disco (se verificado) |
| Seguro / Aprovado pelo scanner | Nenhum achado desta verificação; segurança não avaliada |
| Instalar MCP | Importar metadados do servidor MCP |
| Validar | Verificar estrutura (com escopo explícito) |
| Livre (sem LICENSE) | Licença não informada — ausência não é permissão |
| Assinado (hash) | Hashes conferem — autoria não verificada |
| Ativo | Na biblioteca; preservar enum active no dado técnico |
| Confiança 98% | Decisão humana registrada, com estado literal do contrato |

## 8. Checklist para implementação futura

- Medir tokens em todos os fundos reais; não supor que design escuro é acessível.
- Testar foco inicial/retorno, tabulação e atalhos; nenhum controle só por hover.
- `ul/li` + link/botão nativo nos cards; landmarks e headings ordenados; não sobrescrever role nativo interativo.
- Diálogo usa foco contido e fundo inert; página usa heading/landmark e retorno contextual. Não misturar os modelos.
- Evitar leituras repetidas de status enquanto digita; anunciar contagem final, não cada skeleton.
- Preservar `textContent` e proteção contra conteúdo externo. Markdown futuro deve ser sanitizado, sem HTML ativo, imagens remotas ou links autoabertos.
- Testar Segoe UI e fallback, nomes longos, caminhos profundos, Unicode escapado, ausência de campos, 10 mil arquivos e lista grande. Volume grande exige avaliação técnica, não prometer performance sem medir.
