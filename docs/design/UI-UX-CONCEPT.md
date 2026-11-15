# Conceito de experiência — Oficina Sakura

**PROPOSED · 2026-11-15.** “Oficina Sakura” é nome interno da direção, não renomeia o produto. Marca pública: **Lia Agent Hub**. Descritor: **Biblioteca e oficina de capacidades**.

## 1. Promessa e personalidade

> Capacidades para seus agentes. Organizadas por você.
>
> Descubra o que há no seu acervo, inspecione a origem e prepare pacotes para usar no host de sua escolha. O Hub não executa capacidades.

“Oficina” significa curadoria e preparação, não terminal. “Descobrir” significa encontrar recursos no acervo importado; não promete marketplace online. “Aprender” e “conectar” não são verbos de CTA do Hub. Voz acolhedora e objetiva em pt-BR, termos técnicos com explicação curta: “MCP · servidor que oferece ferramentas a um host”. Sem gamificação, chat/persona obrigatória, mensagens infantis ou selos de invulnerabilidade.

Dois públicos compartilham o mesmo fluxo: uma pessoa não técnica começa pelo propósito e pelo próximo passo; quem é técnico expande caminhos, códigos, hashes, requisitos e declarações. Não criar “modo simples” que esconda risco.

## 2. Arquitetura de informação alvo

```text
Início                      resumo opcional, sem telemetria
Biblioteca                  acervo admitido; tipos/domínios/tags são filtros
  Capacidade                página com abas e link de retorno
A revisar (Quarentena) [n]   recursos recebidos, ainda fora da biblioteca
Importar                    caminho → análise → revisão → admissão
Índice e pacotes            gerar índice local, verificar hashes
────────────────────
Configurações               preferências + dados + Sobre/Diagnóstico
```

Sidebar de 224px em desktop largo; não duplicar Criar, Validação e Importar como destinos paralelos do concept quando descrevem ações da mesma jornada. Validação é ação da capacidade/relatório, não segunda biblioteca. Diagnóstico continua acessível em um passo a partir de Configurações, não removido.

Biblioteca permanece entrada inicial enquanto dashboard não tiver dados reais úteis. Início é proposto como evolução frontend, não requisito de build. A revisar mantém o termo técnico no subtítulo e no indicador de lifecycle; biblioteca nunca inclui quarentena silenciosamente. Histórico global e coleções não viram rotas vazias nesta fase.

### Taxonomia sem falsa disponibilidade

| Tipo de domínio atual | Rótulo / experiência |
|---|---|
| agent-skill | Agent Skill · validação estrutural específica disponível |
| mcp-server | Servidor MCP · ficha de metadados; sem conectar/iniciar |
| cli-tool | CLI e ferramenta · catálogo; sem instalar/rodar |
| api-service | API e serviço · catálogo; sem chave/teste de conexão |
| plugin | Plugin e extensão · catálogo; sem habilitar |
| framework | Framework e runtime · catálogo; sem ambiente de execução |
| provider-model | Provider e modelo · catálogo; sem baixar pesos/inferir |
| workflow / template | Workflow / Template · catálogo; sem executar etapas |
| reference | Referência técnica · conteúdo documental |
| unknown | Tipo não identificado · nunca adivinhar como Skill |

Domínio (Programação, Game Dev, Arte, Pesquisa etc.) responde “para quê”; tipo responde “o quê”; tags refinam tema. São dimensões distintas. Não criar enum novo para rótulo de categoria. Dataset, prompt, SDK e coleção não são tipos canônicos atuais: eventual extensão requer proposta técnica própria; preservar unknown quando necessário, sem migração cosmética.

## 3. Jornadas e decisões

### J1 — Primeiro contato

Biblioteca vazia → “Importe sua primeira capacidade” → caminho com exemplo → análise sem execução. Explicar antes da ação: original preservado; importação cria cópia em quarentena. Preferir “Analisar sem salvar” para dry run e “Importar para revisão” para operação persistente. Não desenhar um único botão ambíguo que primeiro simula e depois importa silenciosamente.

### J2 — Revisar algo recebido

A revisar → abrir ficha → ler origem/licença, inventário e achados → inspecionar evidência → registrar decisão compatível com contrato → admitir. Admissão e confiança são eixos separados. Confirmar: “Adicionar à biblioteca não autoriza o uso em nenhum host.” Não criar score de confiança nem aprovar a partir de ausência de achados.

Os enums de confiança atuais misturam procedência e revisão; correção imediata é copy fiel, não reinterpretar os valores existentes. Registrar método de revisão estruturado, se desejado, é evolução de contrato. Sem inventar autor/data de revisão quando ausentes.

### J3 — Encontrar e acompanhar

Biblioteca → busca com contagem → filtros Tipo/Confiança/Tag e domínio quando disponível → ficha → retornar com query, rolagem e foco preservados. Versões substituídas explicitamente disponíveis, mas excluídas do padrão; nenhum resultado não significa acervo vazio.

### J4 — Preparar para outro host

Ficha → Exportar → escolher uso privado/compartilhado/público → ler condição de licença → gerar arquivo → mostrar caminho e resultado. Não há “Instalar no Studio”, “Ativar MCP” ou sincronização automática. O host decide compatibilidade, permissões e execução.

### J5 — Atualizar

Hoje `/api/update` modifica a biblioteca e guarda versão anterior. Não chamá-lo só para construir uma prévia. Primeira melhoria: confirmação explícita e resumo do efeito. Alvo futuro: staging em quarentena → comparação de conteúdo/declarações → revisão → confirmação; requer trabalho técnico transacional. Confiança de nova versão deve ser apresentada conforme dado real, nunca herdada visualmente por conveniência.

## 4. Quatro dimensões de evidência

| Dimensão | Exemplo de rótulo | Nunca concluir |
|---|---|---|
| Estrutura | “Verificação estrutural: 0 erros, 2 avisos · hoje 14:10” | Que funciona no host ou é seguro |
| Integridade | “Hashes conferem com o manifesto” | Autoria verificada ou pacote assinado |
| Direitos | “Código: MIT declarado; conteúdo: não informado” | Licença ausente = livre; código cobre pesos/assets |
| Decisão humana | “Fornecido por você · registro por … em …” | Autorização de execução ou revisão externa inexistente |

Lifecycle é uma quinta informação operacional: Em quarentena / Na biblioteca / Versão anterior / Arquivado. Não é nível de segurança. Requisitos desconhecidos mostram “Não informado”, nunca “Compatível”.

## 5. Estratégia de entrega e dependências

| Camada de mudança | Exemplos | Condição |
|---|---|---|
| **V — visual/copy** | cores, espaçamento, redução de ornamentos, labels precisos, explicação de risco | Não altera decisões/payloads; revisar contraste |
| **F — frontend com contratos atuais** | sidebar, página/abas, filtros enum corretos, foco, estado pendente, formulário exportação, exibir camadas de licença e `/api/diff` entre versões já existentes | Testes de UI; não é “só CSS”, mas não exige novo backend |
| **T — técnico/produto futuro** | seletor nativo, preview textual seguro, staging+diff pré-atualização, coleções persistentes, autoria Skill, registro de método de revisão, filtros multivalor se não suportados | Especificação e aprovação separadas; não forçar migração para atender mockup |
| **Fora do Hub** | instalar/rodar Skill, conectar MCP, API keys, permissões, orquestração, download de pesos | Não implementar nem oferecer desabilitado como promessa |

Dashboard: contagem de biblioteca/quarentena existe no diagnóstico; agregação de tipos pode vir dos itens. Eventos recentes globais não têm contrato agregado auditado; omitir, ou mostrar apenas o histórico de uma capacidade selecionada. Não simular feed real. Coleções: alternativa imediata é filtro por tag; coleção persistente é T e não deve sobrescrever tags existentes.

## 6. Alternativas decididas

- **Escolhida:** escuro ameixa de baixa saturação com Sakura no foco/CTA. Alternativa: neon completo do concept — rejeitada por competição com evidências.
- **Escolhida:** página de detalhe, com prévia opcional futura. Alternativa: drawer único — mantém usuário na lista, mas sacrifica leitura e foco.
- **Escolhida:** sidebar textual. Alternativa: barra só de ícones — economiza espaço, dificulta descoberta; usar menu textual recolhível em janela estreita.
- **Escolhida:** ilustração apenas opcional no acolhimento, nunca essencial. Alternativa: hero com personagem — identidade forte, porém depende de direitos e espaço; não necessária para reconhecer Lia.
- **Escolhida:** uma biblioteca universal filtrada. Alternativa: páginas diferentes para cada tipo — duplica navegação e implica suporte especializado inexistente.

## 7. Critérios de sucesso e pesquisa posterior

Metas de aceitação propostas (não resultados medidos): pessoa identifica em até 30s que nada é executado; conclui importação local sem orientação oral; distingue simulação de persistência; identifica licença desconhecida e localiza origem; exporta privado sem digitar enum; volta de detalhe com contexto intacto. Em teste moderado com 5–8 participantes mistos, registrar taxa de conclusão, erros de interpretação e assistência requerida, sem upload automático de conteúdo privado. Avaliar separadamente uso por teclado/leitor de tela. Se alguém interpretar verde como “seguro”, rever linguagem antes de otimizar decoração.
