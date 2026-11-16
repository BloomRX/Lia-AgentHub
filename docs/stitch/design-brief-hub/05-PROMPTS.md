# 05 — Prompts para o Stitch

Prontos para uso. Cada um é autossuficiente: colar no Stitch com o design
system aplicado (`apply_design_system`) produz resultado utilizável sem
conversa adicional.

**Projeto Stitch:** `14298534195629906316`

Ordem de execução recomendada: 0 → 1 → 2 → 3 → 4 → 5 → 6. O prompt 0 é a
semente visual; gerar as telas antes dele produz UI incoerente entre telas.

Antes de gerar, ler `03-DESIGN-SYSTEM.md`. Colar o bloco **Contexto** de cada
prompt junto com o pedido — sem ele o modelo inventa funcionalidade.

## Contexto comum (colar em todos)

```
Aplicativo desktop técnico chamado "Lia Agent Hub". Ferramenta de curadoria
de capacidades (Agent Skills e servidores MCP) para o ecossistema Lia.
Público: pessoa técnica que importa recursos de terceiros, inspeciona
proveniência e licença, e decide o que entra na biblioteca.

Princípios visuais OBRIGATÓRIOS:
- Tema escuro padrão, densidade média-alta, tipografia de sistema.
- Âmbar = quarentena / não decidido. Verde = revisado por humano. Vermelho =
  conteúdo alterado. Cinza-azulado = desconhecido. NUNCA verde para "importado".
- Nenhum estado indicado só por cor: sempre ícone + texto.
- Nada de celebração, confete, emoji, "Ups!". Tom de ferramenta técnica.
- Sem ícone de cadeado ou selo de "seguro": o produto não assina nada.
- Não mostrar chat, execução de código, credenciais ou "instalar e rodar".
```

---

## Prompt 0 — Semente visual (identidade)

```
Crie uma tela de identidade visual para o Lia Agent Hub, não uma tela de
produto. Mostre:
- a palavra "Lia Agent Hub" em tipografia de interface;
- uma amostra da paleta com RÓTULOS de significado (quarentena, revisado,
  alterado, desconhecido, atenção) — não apenas quadrados de cor;
- três amostras de tipografia (interface, dado técnico monoespaçado, título);
- um exemplo de badge de confiança nos 4 níveis, cada um com forma e texto
  distintos além da cor;
- um exemplo de chip de integridade: íntegro / alterado / desconhecido.

Estética: ferramenta de engenharia, séria, escura, alta legibilidade.
Referência de densidade: editor de código, não site de marketing.
Não inclua telas de produto nesta geração.
```

---

## Prompt 1 — Biblioteca

```
Tela principal "Biblioteca" do Lia Agent Hub.

Layout: sidebar fixa à esquerda com 4 itens — Biblioteca (selecionado),
Quarentena (com contador de pendências), Distribuição, Diagnóstico. Barra
superior com campo de busca, botão primário "Importar" e ícone de
configurações.

Conteúdo: lista de capacidades. Cada linha mostra nome, tipo (skill /
servidor MCP / workflow), versão, badge de confiança, badge de licença e
indicador de integridade. Linhas agrupáveis por tipo.

Barra de filtros acima da lista: texto livre, tipo, domínio, tag, confiança.
Filtros ativos aparecem como chips removíveis.

Use dados de exemplo realistas e NÃO genéricos:
- "code-to-design" — agent-skill, v1.0.0, confiança não revisada,
  licença Apache-2.0 declarada, integridade OK
- "google-stitch-mcp" — mcp-server, endpoint https://stitch.googleapis.com/mcp,
  autenticação por API key, confiança não revisada, licença desconhecida
- "lia-uiux-workflow" — workflow, confiança revisada externa, integridade OK

Inclua uma variante com o estado vazio: "Nenhuma capacidade ativa ainda",
texto explicando que a biblioteca começa vazia, e botão "Importar".

Mostre 3 items na sidebar com contagem. Densidade alta, sem espaço morto.
```

---

## Prompt 2 — Detalhe da capacidade

```
Tela de detalhe de uma capacidade no Lia Agent Hub. É a tela mais densa do
produto; o usuário decide aqui.

Capacidade de exemplo: "react-components", agent-skill v1.0.0, importada de
github.com/google-labs-code/stitch-skills, namespace "stitch".

Organize em coluna principal + coluna lateral de decisão.

Coluna principal, em seções com título:
1. Resumo: descrição real ("Converts Stitch designs into modular Vite and
   React components…"), tipo, versão, namespace.
2. Integridade: hash de conteúdo e hash de árvore, com valor curto e botão de
   copiar; estado "confere" em verde.
3. Risco: nível ALTO com fatores listados (contém scripts, licença não
   declarada, não revisado). OBRIGATÓRIO: bloco "O que esta análise NÃO
   avalia" visível, listando: instruções maliciosas em prosa, segurança do
   código em scripts, homoglifos entre escritas, comportamento em execução.
4. Proveniência: linha do tempo com importação, validação e eventos;
   upstream com repositório e commit.
5. Arquivos: árvore somente leitura, scripts marcados visualmente.

Coluna lateral: painel de decisão com confiança atual (não revisada), licença
(Apache-2.0 declarada, redistribuição NÃO autorizada), e ações: Validar,
Definir confiança, Definir licença, Exportar.

A distinção "licença declarada" vs "redistribuição autorizada" precisa ser
visualmente óbvia, não uma nota de rodapé.
```

---

## Prompt 3 — Importar (simulação)

```
Tela "Importar" do Lia Agent Hub, no passo de SIMULAÇÃO.

O usuário aponta uma origem (caminho local, arquivo .zip ou .lia-capability)
e o produto mostra o que ACONTECERIA, sem gravar nada.

Mostre:
- Origem selecionada: /home/user/stitch/repo/plugins/stitch-design/skills/code-to-design
- Bloco grande e destacado: "Simulação — nada foi gravado ainda"
- Resultado: nome detectado, tipo, versão, hash de conteúdo (curto, copiável)
- Lista de arquivos que seriam gravados, com tamanho
- Avisos agrupados: 1 informativo (nome usa namespace "stitch"), 4 avisos de
  portabilidade (o texto cita caminhos relativos que saem do payload), 0 erros
- Rodapé com duas ações: "Cancelar" (secundária) e "Confirmar importação"
  (primária)

Inclua, ao lado ou abaixo, uma variante do MESMO layout com resultado
BLOQUEADO por erro estrutural: código "NAME_FORMAT" visível, explicação de
que o nome deve ser minúsculo com hífens, e o botão de confirmar
desabilitado. Não use vermelho de erro genérico: use o vermelho de "alterado".
```

---

## Prompt 4 — Quarentena

```
Tela "Quarentena" do Lia Agent Hub.

Conceito visual central: esta é a área de espera. Nada aqui é usado ainda.
Fundo levemente âmbar, diferente do resto do app.

Cada item é um cartão com: nome, tipo, quando foi importado, de onde veio,
motivo de estar na quarentena, e os avisos da importação em texto curto.

Dados de exemplo:
- "lia-game-qa-plan" — importada há 2 horas, de BloomRX/Lia-Studio, aviso:
  nenhum arquivo de licença encontrado.
- "react-native" — importada há 5 minutos, de google-labs-code/stitch-skills,
  namespace "stitch", 3 referências a arquivos ausentes.

Cada cartão tem duas ações claramente hierarquizadas: "Ver detalhes"
(secundária) e "Promover" (primária), com "Descartar" como terceira opção
menos proeminente e em cor de risco.

Inclua o diálogo de confirmação de promover como sobreposição: título
"Promover para a biblioteca", resumo do item, e a frase obrigatória
"Promover não marca como confiável nem autoriza redistribuição."
Botões: Cancelar / Promover.

Inclua também a variante vazia: "Nada aguardando decisão."
```

---

## Prompt 5 — Distribuição e verificação

```
Duas telas do Lia Agent Hub nesta geração.

TELA A — "Distribuir":
Exportar uma capacidade para outro projeto. Seletor de destino com 4 opções e
consequência escrita em cada uma:
- Privado — só para mim. Permitido.
- Uso próprio — permitido.
- Compartilhado — outros poderão acessar. Exige atenção à licença.
- Público — RECUSADO quando a redistribuição não está autorizada.
Mostre o caso recusado: a opção "Público" desabilitada com o motivo
"Redistribuição não autorizada para esta licença".
Abaixo: botão "Exportar" e, depois do sucesso, caminho do pacote e hash.

TELA B — "Verificar pacote":
O usuário arrasta um arquivo .lia-capability e recebe um veredito.
Estado 1 (íntegro): selo verde "Hash confere" e, logo abaixo e com peso
próprio, a frase "Isso prova integridade, não autoria."
Estado 2 (alterado): selo vermelho "O conteúdo não corresponde ao manifesto".
Estado 3 (malformado): "Não é um pacote válido" com detalhe técnico.

Não use ícone de cadeado em nenhum estado.
```

---

## Prompt 6 — Diagnóstico

```
Tela "Diagnóstico" do Lia Agent Hub. Área para quem precisa investigar
problema, não para uso diário.

Cartões de situação, cada um com número grande e rótulo:
- Capacidades na biblioteca: 12
- Aguardando decisão na quarentena: 3
- Registros ilegíveis: 1 (âmbar, com ação "Ver detalhes")
- Integridade: 11 conferem, 1 alterada (vermelho)
- Índice publicado: 9 itens, 3 não indexados por estado
- Pacotes ausentes: 0

Abaixo, tabela "Saúde do índice" com colunas: id, situação, detalhe.
Linhas de exemplo com problemas reais: pacote ausente no disco, órfão sem
registro, item no índice mas ausente.

Por fim, seção "Configurações" com caminhos da biblioteca, quarentena e
exportados, e um botão destrutivo "Restaurar padrões" claramente separado.

Tom: painel de instrumentação. Sem gráficos decorativos; números e listas.
```
