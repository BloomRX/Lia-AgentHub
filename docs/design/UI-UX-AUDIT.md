# Auditoria da interface atual

**2026-11-15 · RESEARCH por inspeção estática**, código da base `7cec491a563de8a75abe56d5aad1b115fec9db44`. Não é auditoria visual de aplicativo executado nem certificação de acessibilidade. Fontes e limites em [RESEARCH-REFERENCES](RESEARCH-REFERENCES.md).

## 1. Retrato fiel do que existe

`resources/static/index.html` oferece Biblioteca, Quarentena, Importar, Índice e pacotes, Configurações e Diagnóstico. `app.js` alterna seções sem rota navegável; abre detalhes em drawer fixo; usa `fetch` local e texto via `textContent`. `app.css` usa Segoe UI, tema escuro azulado, cartões e quebra de layout a 720px. Não existe dashboard, editor de Skill, navegador remoto de catálogo ou coleções nessa interface.

Pontos a preservar: aviso de não execução no cabeçalho; biblioteca e quarentena separadas; estados vazios diferentes para busca e acervo; skip link, `lang=pt-BR`, foco visível e live region de toast; hashes explicitamente diferentes de assinatura; exportação pública sujeita a base de redistribuição; renderização textual sem HTML arbitrário; preferências locais e caminhos visíveis. O redesign não deve regredir esses controles.

## 2. Achados rastreáveis

Prioridade: **P0** decisão humana semanticamente incorreta; **P1** tarefa central/acessibilidade; **P2** eficiência/clareza; **P3** acabamento. Natureza: **V** visual/copy; **F** comportamento frontend; **T** lógica, persistência ou contrato — não resolver por CSS.

| ID / prioridade | Evidência e problema concreto | Efeito na tarefa | Recomendação / natureza / aceite |
|---|---|---|---|
| A01 P0 | `app.js/renderDetail`: “Marcar como revisado” chama `setTrust(id,"user-provided")`; `TRUST_LABEL` traduz isso como “Fornecido por você” | Revisão é confundida com origem/fornecimento; histórico pode expressar outra decisão | Separar conceito e verbo. Enquanto contrato não for revisto, dizer “Registrar como fornecido por você”, não “revisado”. Exibir valor e consequência antes de confirmar. V+F; modelo mais claro é T. Testar payload e histórico |
| A02 P1 | `index.html/#ftype`, `app.js/TYPE_LABEL` versus `domain/model.py/ResourceType`: prompt/dataset não estão no enum; CLI/API/framework/provider estão ausentes da UI | Filtro pode oferecer universo inexistente e omitir recursos catalogáveis | Alinhar opções ao enum real; rótulo “metadados apenas” quando cabível. F; teste de paridade enum/opções |
| A03 P1 | `openDetail`, handlers de fechar/Escape e `<aside id=drawer>`: nenhum foco inicial/restauração, modal/inert ou navegação interna | Teclado continua no fundo; abertura pode não ser percebida; fechamento perde contexto | Preferir página de detalhe; drawer só de prévia não modal com salto explícito, ou diálogo modal completo. F; teste teclado ida/volta |
| A04 P1 | `loadLibrary` faz debounce de 220ms, mas não aborta nem ordena respostas | Resposta antiga pode sobrescrever filtro novo | AbortController ou contador de requisição; manter query associada ao resultado. F; simular respostas invertidas |
| A05 P1 | `runImport`, publicação e ações assíncronas não bloqueiam repetição enquanto aguardam | Cliques repetidos podem gerar operações concorrentes e feedback ambíguo | Estado pendente por ação, botão indisponível temporário e resultado persistente. F; idempotência adicional é T. Testar duplo clique |
| A06 P1 | Importação exige texto de caminho; dica promete arrastar, mas não há handlers `drop/dragover` em `app.js` | Leigo não consegue cumprir a ação sugerida | Remover promessa não implementada; manter caminho com exemplo. Seletor nativo é integração T, drop depende da plataforma. Nunca simular upload de pasta |
| A07 P1 | `renderDetail` reduz licença a `d.license.code`, embora modelo tenha content/weights/status/basis | Usuário pode interpretar uma licença como autorização sobre tudo | Expor camadas, desconhecido e base de redistribuição. V+F com dados existentes; edição além de `/api/license` atual exige T |
| A08 P1 | `doExport` pede string private/shared/public em `prompt`; recusas ficam no toast temporário | Erro de digitação; decisão distributiva sem contexto durável | Formulário com opções explicadas, destino e recusa inline; nunca bloquear backup privado por licença ausente. F; manter regras backend |
| A09 P2 | `renderDetail` é sequência longa de risco, arquivos, validação, versões, histórico e ações ao final | Inspeção e ação dependem de rolagem extensa num drawer de até 560px | Página com resumo, abas e ação contextual; evidência rastreável. F |
| A10 P2 | `renderDetail` trunca hash a 16 caracteres, sem controle para copiar completo | Verificação manual fica incompleta | Prefixo na lista, valor integral e copiar em Integridade. F; não rotular como assinatura |
| A11 P2 | Card exibe risco baixo em verde (`RISK_CLASS.low=ok`) com vários chips de igual peso | Leitura rápida pode interpretar verde como segurança garantida | Usar “Triagem: poucos fatores sinalizados” e limites próximos; confiança separada. V; não recalcular score |
| A12 P2 | `show` não registra URL/histórico; `filters()` fixa lifecycle active embora servidor aceite all/domain | Voltar não restaura detalhe/query; versões e domínio têm baixa descoberta | Estado de navegação e filtros recuperáveis; versões anteriores acessíveis. F, sem mudar API |
| A13 P2 | `banner` global persiste até ser explicitamente limpo; catches não oferecem retry; toast desaparece em 4/7s | Falha pode acompanhar outra seção ou sumir antes de leitura | Erro local persistente com retry e preservação de entrada; toast apenas confirmação complementar. F |
| A14 P2 | Cabeçalho sticky com seis itens quebrando em várias linhas; grids têm mínimos 290/320px; nenhum tratamento de alto zoom além de 720px | Em baixa altura/zoom, navegação consome espaço e podem existir overflows | Sidebar adaptável; uma coluna em viewport estreito; testar 800×600 e 200% zoom, não inferir bug Windows já reproduzido. V+F |
| A15 P2 | `.chip` em .72rem, `.small` .82rem e múltiplas fontes reduzidas; rótulos de filtro só `.sr` | Densidade visual alta; significado do filtro depende do placeholder/valor | Metadados 13px, labels visíveis e alvos de 40px. V; medir contraste real de todos estados |
| A16 P2 | `card` cria `button role=listitem` dentro de `role=list` | Role sobrescreve semântica nativa do botão | `ul/li` com botão/link interno; nome acessível inclui tipo/versão e descrição ligada. F; revisar árvore acessível |
| A17 P2 | `doUpdate` aplica atualização após `prompt`; existe `/api/diff`, mas não há comparação no fluxo | Usuário não revisa alteração antes da operação | Não prometer prévia transacional com endpoint atual. Especificar etapa futura de staging+diff+confirmação T; primeiro esclarecer efeito e preservar versões |
| A18 P3 | Paleta azul e símbolo ◈ não expressam direção de família nos BRAND-STANDARDS | Produto fica visualmente desconectado dos Lia | Tokens ameixa/Sakura, sem trocar stack ou adicionar biblioteca. V |

## 3. Cobertura por área

- **Navegação/IA:** seis áreas reais; Quarentena precisa de explicação cotidiana. Diagnóstico é suporte, não tarefa principal. Biblioteca deve continuar sendo atalho direto para usuário recorrente.
- **Dashboard:** ausente; oportunidade proposta, não defeito funcional. Não inventar atividade global, ranking ou estado de sincronização.
- **Busca/filtros:** pesquisa por nome/descrição/tag existe; erros de paridade e concorrência são mais importantes que criar filtros adicionais. Categoria de domínio não deve ser confundida com tipo de recurso.
- **Detalhe/importação:** metadados e inventário existem, mas lista de nomes não é leitor de conteúdo. Inspeção de texto, diff antes de atualização e criação de Skill não podem ser anunciados como presentes.
- **Procedência/licença/risco:** boa base de disclaimers; exposição desigual das camadas e semântica de confiança precisam de correção prioritária.
- **Feedback:** vazio de busca e biblioteca já são distintos. Falta robustez de loading, retry e conclusão persistente. Nunca mostrar vazio antes de concluir a primeira consulta.
- **Desktop/acessibilidade:** há fundações positivas; gestão de foco, roles e redimensionamento necessitam teste específico. Sem execução não afirmar conformidade WCAG nem compatibilidade NVDA/WebView2.

## 4. Leitura crítica do concept anexado

Imagem em `references/gpt-concept-user.png`, fornecida pelo usuário como gerada por GPT; não evidência do estado atual. Boa direção: identidade reconhecível, navegação textual, ações iniciais explicadas e separação “não conecta nem executa” no cartão MCP. Biblioteca/oficina é metáfora útil.

Ajustes necessários:

1. “Tudo sincronizado” não tem base: não há sincronização; usar “Acervo local”, e estado do índice apenas quando consultado.
2. “Tudo o que seus agentes podem aprender” sugere aprendizagem/treino. Preferir “Capacidades para seus agentes. Organizadas por você.”
3. “Criar uma Skill” e “Nova capacidade” só aparecem se houver autoria real; nesta fase, CTA “Importar capacidade”.
4. Hero de personagem ocupa aproximadamente um terço da área útil e compete com tarefas; usar acolhimento compacto, dispensável e sem personagem na revisão de risco.
5. Contagens 24/12/6/3 e atividade são exemplos fictícios, nunca preencher estado real com dados demonstrativos. “Mais exploradas” exigiria medição: eliminar.
6. Cards Capacidades e Skills sobrepõem total/subconjunto; apresentar total com denominador explícito e pendências separadas, não somar os dois.
7. Borda/glow rosa em quase tudo enfraquece seleção/foco; reservar saturação para CTA, selecionado e foco. Não dar à flor função de sinalizador de risco.
8. Textos pequenos sobre fundos ilustrados prejudicam leitura; alertas em superfície sólida. A imagem não permite medir contraste de cada componente de implementação futura.
9. Não usar check verde “Validada” isolado: escrever resultado estrutural exato com limite de escopo.
10. “Biblioteca local / Offline” deve significar armazenamento local, não estado de conexão inferido.

**Decisão:** reter a atmosfera e a clareza das entradas; não reproduzir densidade decorativa, personagem obrigatória nem funcionalidades fictícias. Direitos de personagem/logotipo precisam de confirmação antes de distribuir; imagem fica como referência, não asset de produção.

## 5. Validação futura e priorização

P0 A01 antes de redesenho. P1 A02–A08 na primeira rodada de UX após gate técnico. P2/P3 em sequência, sem bloquear build do Codex.

Roteiro manual futuro: iniciar vazio; importar caminho inválido; simular sem persistir; importar pacote com scripts/licença desconhecida; inspecionar; registrar decisão sem trocar significado; admitir; filtrar; abrir/voltar mantendo filtros; exportar privado e tentar público sem base; atualizar preservando versão anterior; falhar leitura do disco sem mostrar zero. Executar só teclado, NVDA, alto contraste Windows, redução de movimento, 800×600/1024×768/1366×768/1920×1080 e escalas 100/150/200%. A comprovação exige capturas e ambiente/versão, ainda não obtidas.
