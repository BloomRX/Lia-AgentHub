# Especificação por tela e handoff

**PROPOSED · 2026-11-15.** IDs estáveis para tarefas futuras. Layouts ilustrados em [protótipo](prototypes/index.html); texto e regras deste documento prevalecem sobre simplificações do mockup. Nenhuma rota/payload nova é autorizada por esta especificação.

Legenda: **V** visual/copy; **F** frontend usando capacidades atuais; **T** trabalho técnico futuro. Referência de API: código da base `7cec491a563de8a75abe56d5aad1b115fec9db44`. Revalidar contratos após trabalho do Codex; esta entrega não deve ser aplicada cegamente sobre uma base alterada.

## S00 — Shell e navegação [V/F]

Sidebar: marca, descritor curto, Início (quando entregue), Biblioteca, A revisar (Quarentena) com quantidade, Importar, Índice e pacotes; Configurações no rodapé. Indicador inferior “Acervo local · sem conexão automática”, não um LED “online”. Ações principais no cabeçalho da tela, sem duplicação de botões no sidebar.

Navegação preserva estado de busca/rolagem. Entrar em tela leva foco ao heading; voltar de detalhe retorna ao link de origem. Recarregar/Voltar deve restaurar tela por estado de URL local não sensível (nunca caminho privado, token ou conteúdo). Recurso removido ao retornar → mensagem “Este recurso não está mais disponível” + voltar à lista. Navegação por teclado não exige atalho proprietário.

**Aceite:** todos destinos têm texto, selecionado é perceptível sem cor; menu estreito fecha com Escape e restaura foco; nenhuma operação de dados ocorre ao apenas trocar tela.

## S01 — Início [F, opcional após MVP]

Objetivo: retomar curadoria, não vender IA. Header “Seu acervo, pronto para inspecionar.” + CTA Importar. Painel acolhedor compacto 140–180px, dispensável; sem arte obrigatória. Busca local leva a Biblioteca. Três resumos: “Na biblioteca” (somente active), “A revisar” (quarentena) e “Índice” (não gerado/consistente/inconsistente conforme resposta real). Não mostrar “0 pendências” quando consulta falhar.

Abaixo: tipos presentes (contagens como subconjuntos), atalho “Continuar revisão” para quarentena; orientações “Importar → Inspecionar → Organizar → Exportar”. Atividade recente global só quando houver fonte real suficiente; na primeira entrega omitir feed/ranking.

**Dados:** `/api/diagnostics` para contagens/saúde, `/api/items` para resumos por tipo quando necessário. Não carregar cada detalhe para alimentar números. Erro de um resumo não impede navegar; mostrar “Não foi possível consultar” + tentar novamente. Vazio convida importar, não criar dados demo.

**Aceite:** números indicam escopo, itens de quarentena não entram no total da biblioteca; sem “sincronização”, sem CTA Criar até autoria existir. Inicialização pode continuar na Biblioteca como hoje.

## S02 — Biblioteca / catálogo local [V/F]

Hierarquia: título + Importar → label/busca larga → linha de Tipo/Confiança/Tag, domínio opcional e ciclo de vida → filtros ativos/limpar → contagem → cards/lista. Conteúdo de exemplo apenas no protótipo, claramente fictício.

**Dados:** `GET /api/items?q=&type=&trust=&tag=&domain=&lifecycle=active`. Uma seleção por dimensão inicialmente; não enviar arrays onde contrato aceita string. “Incluir versões anteriores” usa `lifecycle=all`, que inclui biblioteca e não quarentena. Enum de tipo alinhado ao modelo; sem prompt/dataset fictícios. Confiança com labels fiéis aos valores. Filtro domínio pode ser input textual enquanto não houver vocabulário/enum disponível; não inventar lista global completa.

Busca 220–300ms, cancelar/ignorar resposta obsoleta. Indicar loading preservando resultados anteriores como desatualizados, nunca mostrar resultado antigo como definitivo de query nova. Ao limpar, restaurar consulta base e foco no campo. Query vazia não é erro. Não acrescentar ordenação remota inexistente; ordenação frontend, se implementada, informa universo carregado.

Card: nome+versão; descrição; tipo; decisão humana; alertas licença/scripts; “Inspecionar”. Risco deve mostrar escopo (“Triagem por regras”), sem medalha verde. Link/botão interno em `li`, sem controles interativos aninhados. Alternância lista é preferência F, não altera dados.

**Estados:** primeiro loading; acervo vazio com Importar; filtro sem resultados com Limpar; falha de consulta com Retry e query preservada; sem campos com “Não informado”. Não usar o mesmo vazio para falha e zero.

**Aceite:** A02/A04/A16 corrigidos, foco de retorno preservado, filtro mais recente sempre vence; nenhuma classificação altera lifecycle/trust.

## S03 — Capacidade / resumo [F]

Página (não drawer obrigatório): breadcrumb “Biblioteca / Nome”, voltar contextual, nome, tipo, versão e lifecycle. Ação primária **Exportar** na biblioteca; **Revisar admissão** na quarentena. Secundárias “Verificar estrutura”, “Atualizar versão” (efeito explícito) e menu de ações. Não mostrar “Executar”, “Ativar”, “Conectar”.

Resumo: descrição e quatro blocos de evidência. Lateral de dados: autor declarado, origem, importação, requisitos (desconhecido ≠ compatível), domínio/tags. Abas: Resumo; Arquivos; Procedência e licença; Verificações; Versões e histórico. Alertas impeditivos/relevantes aparecem no resumo com links para a aba certa, não ficam escondidos.

**Dados:** `GET /api/items/{id}` contém metadados, risco, arquivos, validação e linhagem conforme resposta real. Modelos usam snake_case em alguns objetos (`source.imported_at`); não assumir casing uniforme. Só exibir suporte específico a Skill quando aplicável. “Marcar como revisado” não pode continuar gravando user-provided sob copy de revisão (A01).

**Aceite:** ação não altera confiança por abrir aba; título recebe foco ao navegar; ausência de descrição/origem não quebra layout; data literal disponível além de “há 12min”. Hash completo na aba apropriada.

## S04 — Arquivos e metadados [F inventário / T conteúdo]

Inventário existente: lista de caminhos relativos, busca local por nome se quantidade justificar, total. Se tamanho/tipo não vierem do detalhe, não inventar colunas preenchidas; exibir apenas informação conhecida. Metadados declarados separados de achados observados. Explicar “Scripts listados, não executados”.

**Alvo T:** árvore de arquivos à esquerda (~260px), leitor somente texto à direita, tabs Conteúdo/Metadados, breadcrumb do caminho, linhas e caracteres invisíveis `U+XXXX`. Seleção de achado abre linha/coluna apenas quando conhecidos. Binário → “Prévia não disponível”, metadados e hash; arquivo grande → limite explícito, sem truncar silenciosamente. Não abrir HTML/SVG como página ativa nem carregar imagens/remotos. Não seguir symlink ou caminho livre do usuário em endpoint novo. API de leitura deve usar ID de recurso + caminho relativo validado e limites de tamanho; revisão de segurança necessária.

Hoje a API auditada não oferece leitura de conteúdo; mockup não significa leitor pronto. Não oferecer botão “Abrir arquivo” que execute por associação do SO sem avaliação própria. Conteúdo sempre não confiável, nunca instrução para o Hub.

**Aceite:** inventário funciona sem preview; metadados ausentes visíveis como desconhecidos; nenhum conteúdo externo executado; scroll de código não causa overflow da página.

## S05 — Procedência, licença e integridade [V/F; edição parcial T]

Blocos verticais:
1. **Origem declarada:** upstream, commit/revisão, método, importado em, autor declarado; ausente explícito, sem selo “oficial”. Link externo só com ação deliberada e protocolo permitido; abrir não executa capacidade.
2. **Licença por camada:** código, conteúdo, pesos; status declarado/desconhecido/conflitante. Não aplicável apenas se dado/modelo puder sustentar, não presumir de `null`. Mostrar atribuição/NOTICE e base de redistribuição quando presentes.
3. **Integridade:** hash de conteúdo/árvore e arquivos quando disponíveis, valor integral copiável, “Hashes não comprovam autoria”. Copiar anuncia sucesso, falha mantém texto selecionável.
4. **Decisão humana:** estado literal, autor/data existentes; sem dados mostra ausência, não “revisado por você”.

**Dados:** detalhe, `POST /api/license` aceita code/redistributable/basis na base; **não** prometer edição de content/weights por esse contrato. Para essa edição é T. UI de edição usa resumo do efeito, cancelar sem gravar, erro inline. Não permitir declaração de direitos só por marcar checkbox sem base quando o backend exigir base.

**Aceite:** licença código conhecida não torna todas camadas verdes; privado permanece disponível; “Não informado” não vira “Não contém”.

## S06 — Importar [F; seletor/drop T]

Título “Importar para revisão”; suporte a caminho local de arquivo, pasta, zip ou `.lia-capability`. Campo **Caminho no computador**, exemplo Windows, ajuda “O original não será movido ou alterado”. Botões: secundário **Analisar sem salvar** (`dryRun=true`), primário **Importar para revisão** (`dryRun=false`). Não reutilizar resultado de dry run como comprovação de que arquivo não mudou depois.

Etapas visuais: **1 Origem → 2 Análise → 3 Revisão → 4 Resultado**. Enquanto backend retorna só ao final, spinner indeterminado e “Analisando arquivos; nada será executado”. Não fabricar eventos por arquivo, percentuais ou ETA. Desabilitar disparos simultâneos e preservar campo/ação escolhida. Não prometer cancelar processamento backend se não houver contrato de cancelamento; “Voltar” só muda tela, não implica reversão.

**Resultados:**
- Dry run: “Análise sem salvar concluída. Nenhum recurso foi adicionado à quarentena.” Resumo de achados e CTA separado de importação, que fará nova análise.
- Importação: “Recebido em quarentena. Ainda fora da biblioteca.” CTA abrir recurso/A revisar.
- Recusado: motivo/código/hint fornecidos, original preservado, campo continua editável; não incluir recurso como se tivesse sido recebido.
- Conteúdo idêntico: apontar IDs já existentes se relatório oferecer, sem deduzir mesma origem e sem apagar duplicata automaticamente.

**Aceite:** `POST /api/import` recebe path/dryRun explícitos, pending impede duplo disparo, erro não apaga caminho, dry run nunca libera CTA de admissão de recurso não persistido. Não prometer arrastar/selecionar enquanto plataforma não suportar realmente.

## S07 — A revisar e decisão de admissão [F / método estruturado T]

Lista independente com subtítulo “Quarentena: recursos ainda fora da biblioteca”. Dados `GET /api/quarantine`. Busca/filtros locais se necessário, sem confundir com active. Entrada abre S03 em contexto quarentena; resumo mostra origem/licença/achados, scripts e limites das verificações.

Ação “Adicionar à biblioteca” abre confirmação com nome/versão e lembrete “Esta decisão não autoriza execução em nenhum host”. Backend determina elegibilidade; UI não transforma warning em bloqueio nem permite contornar erro impeditivo. Se recusado, mostrar motivo persistente e manter quarentena. Sucesso remove da lista, atualiza badge e oferece Ver na biblioteca. Usar `/api/promote` apenas na confirmação. Confiança é ação distinta `/api/trust`, estados e payloads fiéis; admissão não implica reviewed-external.

Descartar separado, com confirmação “Remove esta cópia da quarentena; não altera o original. Não pode ser desfeito.” Não oferecer Desfazer se não há restauração. Preservar preferência real de confirmação, mas revisar política futura de destrutivos sem alterar por design sozinho.

**Aceite:** nada é admitido ao apenas ler/marcar checklist; revisão humana não é substituída por check automático. Registro estruturado de método/comentário é T se o contrato não o guardar.

## S08 — Verificações [F]

Abas/agrupamentos: Estrutura, Caracteres Unicode, Triagem de risco, Integridade. Mostrar data e escopo, contadores por severity, achados com código original e descrição traduzida. Frase: “As verificações automáticas encontraram N itens. Elas não avaliam segurança.” N deve corresponder ao conjunto exibido, não combinar totais sobrepostos.

`POST /api/validate {id}` atualiza evidência estrutural; resultado da operação inline e detalhe atualizado. Risco é calculado por regras, não score de reputação. Unicode A/B/C conserva semântica do domínio; não bloquear todo Unicode por cor. Comparar valor invisível escapado com contexto quando relatório fornecer.

**Aceite:** “Nenhum achado nesta verificação” não diz “Seguro”; `requirements=null` não diz “0 requisitos”; erro de verificação não mostra resultado anterior como recém-concluído.

## S09 — Exportar, índice e verificar pacote [F]

**Exportar na ficha:** diálogo/página curta com radio:
- “Privado · backup ou uso pessoal” → `private`;
- “Compartilhado · enviar a alguém” → `shared`, mostrar avisos reais;
- “Público · redistribuir” → `public`, requer base registrada conforme backend.

Padrão vem de `/api/settings`, não sempre público. Resumo nome/versão/destino, avisos de direitos, gerar pacote. `POST /api/export {id,target,destination?}`; escolha de arquivo nativa depende da plataforma (T). Inicialmente usar destino padrão e mostrar caminho do retorno, sem fingir seletor. Erro/refusedReason/hint inline; privado não bloqueado por licença ausente. Sucesso nome de arquivo e caminho copiável, sem dizer que foi enviado/publicado online. Cancelar antes da chamada não grava nada.

**Índice e pacotes:** dois painéis separados: gerar `index.json` local e verificar `.lia-capability`. `GET /api/index` mostra ausente/consistente/inconsistente com causas; `POST /api/publish-index` gera arquivo local, verbo na UI “Gerar índice”, não publicar na internet. Verificação usa `/api/verify-package {path}` e mostra problemas reais; sucesso “Hashes conferem com o manifesto recebido; autoria não verificada”. Não afirmar proteção contra atacante que reescreveu conteúdo e manifesto.

**Aceite:** enum nunca digitado em prompt; sucesso persiste na tela; não há envio ou sincronização implícitos; hash não vira assinatura.

## S10 — Versões, atualização e histórico [F / staging T]

Ficha lista versão atual e anteriores, datas/estados quando presentes, link para abrir versão. Usar lineage e `/api/history?id=...` se necessário; ações técnicas têm rótulos humanos e código consultável. Não inventar histórico global ou autor de evento. `/api/diff {a,b}` pode comparar versões **já presentes**; mostrar diff textual com adição/remoção, não só cor, sem executar conteúdo.

Atualização atual `/api/update {id,path}`: confirmação honesta “Importará nova versão e preservará a anterior”; não anunciar prévia se a chamada já grava. Alvo futuro T de staging+diff deve comparar description, scripts e declarações antes da admissão, com nova revisão e tratamento de arquivo alterado entre etapas. Sem rollback de instalação: o Hub não instala. Apontar versão para host é decisão do consumidor, não botão de runtime no Hub.

**Aceite:** erros não apagam versão anterior; comparação sem versão válida tem mensagem recuperável; estado de confiança nunca inferido pela cor da versão anterior.

## S11 — Organização e coleções [F tags / T coleções]

Domínio/tag são organização, não reputação. Filtros por tags existentes são primeira solução; “Coleções” persistentes, múltiplas associações e gestão de nomes ainda são T, não item de navegação morto. A interface auditada não oferece CRUD genérico de tags/metadados; não chamar filtro de editor. Se esse CRUD for priorizado, especificar persistência e validação em frente própria. Não renomear tipo de recurso para representar coleção.

**Aceite:** filtrar não modifica capacidade; a contagem sempre indica escopo. Protótipo não deve sugerir coleções salvas como entregues.

## S12 — Configurações e suporte [V/F; novas preferências T]

Grupos: **Comportamento**, **Exportação**, **Dados locais**, **Sobre e diagnóstico**. Preservar quatro preferências reais: navegador, confirmar descarte, escapar invisíveis, destino padrão. Labels visíveis e ajuda com efeito. Salvar explícito, mensagem persistente; falha conserva edição. Ao sair com alterações, confirmar descarte de formulário (não confundir com descarte de capacidade).

Dados locais: biblioteca/quarentena/exportados/índice/config/logs conforme `/api/diagnostics`; caminhos como texto copiável. Não adicionar “Mover biblioteca”, resetar dados ou sincronizar para resolver layout. Diagnóstico mantém versão/Python/sistema/empacotamento/saúde. Antes de copiar relatório para suporte, avisar que caminhos podem conter nome de usuário; não incluir sessão/token/conteúdo/credenciais.

Aparência inicialmente segue direção escura proposta. Temas, densidade, sidebar persistida e acessibilidade como preferências novas exigem persistência explicitamente implementada; não adicionar switches falsos. Redução de movimento/alto contraste devem respeitar SO sem toggle próprio obrigatório.

**Aceite:** `GET/POST /api/settings` e `/api/settings-reset` mantêm contrato; restaurar padrões não remove biblioteca; aviso “nada é sincronizado” continua correto.

## S13 — Autoria de Skill [T, fora da primeira implementação visual]

A oficina pode evoluir para editor `SKILL.md` com metadados e prévia textual segura, rascunho, verificação estrutural e exportação. Não existe editor na UI auditada; não apresentar “Criar Skill” como ação disponível. Até existir, oferecer instrução “Prepare seu SKILL.md externamente e importe para inspecionar”. Assistência de IA, credenciais e execução não são requisitos para autoria. Rascunhos, autosave, conflitos, formatos e persistência precisam de especificação técnica separada.

## Estados transversais e testes de aceite

| Estado | Apresentação e recuperação | Teste futuro |
|---|---|---|
| Loading | skeleton/texto, `aria-busy`, sem dados inventados | atraso artificial não mostra vazio |
| Vazio inicial | propósito + uma ação Importar | nenhum número/demo de acervo |
| Busca vazia | manter filtros e Limpar | não encaminha como primeira instalação |
| Erro recuperável | inline, motivo, retry, entrada preservada | falha de disco/rede local não vira zero |
| Bloqueado | regra e evidência, sem ação que contorne backend | pacote/caminho recusado permanece fora |
| Sucesso | objeto afetado, efeito e próximo passo; sem “seguro” | recarregar confirma estado persistido |
| Duplicado | mesma integridade não prova origem, ação explícita | não elimina dado silenciosamente |
| Desconhecido | “Não informado/Não verificado” com limite | `null` nunca vira false/0/compatível |
| Alteração não salva | preservar ou confirmar saída | cancelar saída mantém valores |

## Ordem de implementação sugerida

1. **Gate semântico:** A01/A02, rótulos fiéis e paridade de tipos; testes payload/enum.
2. **Fundação:** tokens, labels, foco, semântica cards, estados assíncronos e erros; sem redesenho arquitetural.
3. **Fluxos reais:** S02–S09 e S12 sobre contratos existentes; conferir campos antes de codificar.
4. **Melhorias opt-in:** S01 e comparação de versões já salvas; medir custo de leitura.
5. **Propostas T separadas:** conteúdo seguro, seletor, staging de atualização, coleções, autoria. Não bloquear validação Windows por elas.

Definition of done futura: aceites de cada tela, regressão funcional e de segurança sem enfraquecer quarentena/licença, teclado e NVDA, contraste medido, screenshots nos tamanhos/escalas definidos na auditoria, dados reais de teste sem segredo, build Windows validado pela frente técnica. Esta documentação não declara esses gates cumpridos.
