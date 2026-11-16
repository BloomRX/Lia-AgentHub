# 03 — Design system inicial

Tokens de partida, não lei. O Stitch deve propor refinamento; o que **não** é
negociável são os estados semânticos, porque eles carregam significado de
segurança.

## Cor — semântica de estado

A paleta é a linguagem do produto. Cada cor responde a uma pergunta de
curadoria e não pode ser usada decorativamente.

| Token | Papel | Uso |
|---|---|---|
| `--state-quarantine` | não decidido | âmbar. Quarentena, `trust: unreviewed` |
| `--state-verified` | verificado por humano | verde. `trust` ≥ reviewed, hash confere |
| `--state-mismatch` | alterado | vermelho. Hash não confere, pacote inválido |
| `--state-unknown` | não sei | cinza-azulado. Licença desconhecida, risco não avaliado |
| `--state-caution` | atenção sem alarme | violeta suave. Risco médio, avisos |

**Regra:** nunca usar verde para "importado". Importação bem-sucedida é âmbar,
não verde — o recurso entrou, mas não foi revisado. Verde é reservado para
decisão humana registrada.

## Tipografia

- Interface: sans de sistema (a UI roda em pywebview; fonte web externa
  adicionaria dependência de rede).
- Dados técnicos (hash, IDs, caminhos): monoespaçada, corpo menor, cor de
  detalhe. Nunca no mesmo peso do veredito.
- Escala: 12 / 14 / 16 / 20 / 24 / 32 px. Máximo três tamanhos por tela.

## Espaçamento e densidade

Grid de 4 px. Densidade média-alta: o usuário é técnico e trabalha com listas.
Não é produto de marketing — espaço em branco generoso desperdiça área útil.

## Componentes

| Componente | Variantes | Observação |
|---|---|---|
| `CapabilityCard` | list, compact | nome, tipo, `trust`, licença, estado de quarentena |
| `TrustBadge` | 4 níveis | cor por nível; texto sempre presente |
| `LicenseBadge` | declared, unknown, redistributable | **nunca** verde por padrão |
| `IntegrityChip` | ok, mismatch, unknown | clicável abre hash completo |
| `RiskMeter` | low, medium, high | acompanhado de `notEvaluated`, obrigatório |
| `IssueList` | error, warning, info | erro e aviso distinguíveis sem cor |
| `StateBadge` | 5 lifecycle | |
| `DryRunPanel` | — | mostra o que seria gravado, sem gravar |
| `ConfirmAction` | normal, destructive | destrutivo exige digitar o nome |
| `ProvenanceTimeline` | — | histórico de eventos |
| `FileTree` | read-only | arquivos do payload |
| `HashDisplay` | short, full | curto na lista, completo no detalhe |
| `EmptyState` | — | sempre com próxima ação |
| `FilterBar` | — | texto + tipo + domínio + tag + confiança |

## Acessibilidade — mínimo verificável

- Contraste ≥ 4.5:1 em texto, ≥ 3:1 em ícone e borda de estado.
- **Nenhum estado depende só de cor.** `TrustBadge` e `IntegrityChip` têm
  forma/ícone/texto distintos.
- Foco visível em todo elemento interativo, com anel de 2 px.
- Alvo de toque ≥ 44 × 44 px.
- Ordem de tabulação segue a ordem visual.
- `prefers-reduced-motion`: desligar transições, não só encurtar.
- Modais prendem o foco e devolvem ao gatilho ao fechar.

## Responsividade

- Janela desktop: 1024 px é o alvo principal. Sidebar fixa a partir de 1024.
- Abaixo de 1024: sidebar colapsa em ícones.
- Abaixo de 768: navegação vira barra inferior, lista vira coluna única.
- O produto **não** é para celular hoje; o layout só precisa não quebrar.

## Tema

Escuro é o padrão (família Lia). Tema claro deve existir porque o conteúdo
inclui capturas de tela e export de design, e fundo escuro distorce avaliação
de cor — quem trabalha com design frequentemente precisa do claro.

## Anti-padrões proibidos

| Anti-padrão | Por que é proibido aqui |
|---|---|
| Selo de "verificado" sem humano | `trust` só muda por decisão humana |
| Barra de progresso infinita "validando" | Validar é local e rápido; progresso falso mente |
| Confete/celebração após importar | Importar não é conquista; é entrada em quarentena |
| Ícone de cadeado como "seguro" | Não há assinatura no produto |
| Esconder hash em tooltip | Integridade é informação primária |
| Contagem de "usuários" ou popularidade | Não existe esse dado |
