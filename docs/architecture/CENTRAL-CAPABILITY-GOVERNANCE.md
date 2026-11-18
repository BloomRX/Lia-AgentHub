# Governança central de capacidades Lia

**Proposta técnica · 18 de novembro de 2026.** O Agent Hub mantém o catálogo,
a quarentena e as evidências de admissão. Cada projeto mantém a autoridade sobre
seu host. O [contrato de inventário](CAPABILITY-INVENTORY-CONTRACT.md) define o
intercâmbio proposto. O [contrato de hosts](CAPABILITY-HOST-AND-DISTRIBUTION-CONTRACT.md)
continua definindo o índice, os pacotes e a superfície de consumo existentes.

## Autoridade sobre o registro

| Papel | Responsabilidade | Evidência que assina como autoria do registro |
| --- | --- | --- |
| Mantenedor de origem | Declara identidade, revisão, autoria, licença, dependências e requisitos | Inventário versionado, revisão de origem, atribuições e avisos |
| Curador do Hub | Confere procedência, integridade, esquema, duplicatas e compatibilidade declarada | Relatório de validação e eventuais conflitos |
| Responsável humano por distribuição | Decide sobre um artefato, canal, público, território e obrigações aplicáveis | Decisão rastreável vinculada a versão, hash e documentos de base |
| Mantenedor ou operador do host | Decide o que configurar, revisa o material exportado e controla instalação, credenciais e execução | Evidência sanitizada de configuração ou operação, vinculada ao host e à revisão |
| Lia-Research | Mantém pesquisa, proveniência, referências LR-* e questões em aberto | Fonte e classificação histórica da evidência |

Cada projeto escolhe explicitamente quais capacidades consome. O Hub prepara e
valida arquivos e descritores. Segredos, sessões, instalação, conexão, Grants,
Leases e execução pertencem ao host. Integrações usam arquivos e o contrato já
existente, sem dependência de um Hub em execução. D-05 e D-18 preservam a
restrição de execução no Hub. D-16 e as propostas DR pendentes exigem decisão
humana. A oficina visual permanece no Stitch.

## Receber e revisar um inventário

1. **Receber.** O mantenedor entrega JSON UTF-8 com revisão do inventário,
   registros, referências LR-* e evidências. Conferir identidade do remetente
   e registrar origem, data, revisão, digest do arquivo e responsável. Abrir
   como dados. A descoberta começa pelos inventários entregues, resultados
   do Lia-Research e metadados do catálogo. O Hub apresenta candidatos
   para revisão sem disparar fetch, instalação ou conexão automática.
2. **Verificar.** Validar esquema, limites, caminhos relativos, integridade e
   referências. Comparar com a árvore Git da revisão autorizada, quando
   disponível, e recalcular hashes em bytes locais em modo de inspeção.
   Registrar origem declarada e correspondência separadamente. Evidência
   indisponível conserva os campos como desconhecidos.
3. **Classificar.** Procurar mesmos IDs, aliases, hashes, nomes e relações.
   Registrar dependências obrigatórias e opcionais, versões e conflitos.
   Comparar descritores de MCP por transporte, contrato, tools, recursos,
   permissões, autenticação e egress. Comparar Skills por conteúdo, versão,
   frontmatter, requisitos e licença. Comparar a capacidade com requisitos
   explícitos de cada host e registrar o nível de evidência.
4. **Registrar e importar.** Catalogar metadados ou referências revisados.
   Quando houver payload autorizado e tipo admitido pelo Hub atual, usar
   `import_path(..., dry_run=True)`. Com ação explícita do usuário, repetir a
   importação para a quarentena. Conferir o hash novamente se origem ou revisão
   mudou. Promover é um passo humano separado e habilita a biblioteca local.
5. **Decidir distribuição.** Conferir o escopo de cada componente, atribuição,
   avisos, origem, dependências, pesos, conteúdo e eventuais restrições
   contratuais. Um conflito bloqueia a ação afetada e registra motivo e
   responsável. Materiais sem base de redistribuição podem permanecer como
   metadados ou referência, preservadas as regras existentes de backup privado.
6. **Preparar entrega.** Selecionar revisão e hash exatos. Exportar somente o
   artefato e o canal permitidos. Para um descritor MCP compatível, gerar
   configuração de exemplo com campos não preenchidos para revisão do usuário.
   O destinatário verifica o hash e revisa requisitos, ferramentas, mudanças,
   destino, termos e permissões. Qualquer configuração ou instalação é feita
   no host por ação explícita e sujeita às suas políticas.
7. **Reportar e reavaliar.** Por projeto e revisão, entregar totais por tipo e
   estado, lacunas de autoria, colisões, diferenças de versão, dependências
   pendentes, escopo de licença, compatibilidade, bloqueios com responsável e
   hashes dos artefatos exportados. Uma retificação é um novo evento com
   referência ao anterior. Aprovação revogada ou evidência vencida é refletida
   na projeção vigente, com histórico preservado.

## Procedimento por projeto

| Origem | Evidência a entregar | Tratamento no Hub e decisão do host |
| --- | --- | --- |
| Lia Desktop / Lia-Project | Snapshot de Skills, perfis, providers, MCPs e integrações declaradas. Incluir formato esperado, permissões e requisitos do Desktop | Relacionar providers e ferramentas a perfis sem publicar configurações locais. Desktop decide provisionamento, permissões e credenciais |
| Lia Forge | Snapshot de Skills, workflows de asset, CLIs, plugins e dependências de engine, DCC ou modelo. Separar licenças de código, assets e pesos | Manter vínculos com proveniência de assets. Forge verifica versões do pipeline e decide ativação e execução |
| Lia Studio | Snapshot de Skills, extensões, CLIs e MCPs de editor ou gameplay. Informar versão de engine e escopo de projeto | Entregar referências ou configuração revisável. Studio decide quais recursos entram nas sessões e quais permissões são concedidas |
| Lia Model Lab | Snapshot de modelos, providers, rotinas de avaliação e dependências. Incluir pesos, revisão, backend, hardware e medição separadamente | Catalogar resultados com metodologia e ambiente. Model Lab mantém a evidência de avaliação e decide execução de experimentos |
| Lia Agent Hub | Snapshot de capacidades próprias e referências de terceiros em quarentena ou biblioteca. Preservar o projeto de autoria e o registro local | Hub audita metadados, valida estrutura e prepara artefatos. Para configuração e operação, aponta para um host responsável |

## Duplicatas, versões e compartilhamento

| Sinal | Tratamento |
| --- | --- |
| Mesmo emissor, ID, revisão e hash | Recepção idempotente. Acrescentar referência ao recebimento, quando necessário |
| Mesmo ID e revisão com hashes diferentes | Bloquear publicação da revisão disputada. Preservar ambos os relatos e investigar sem sobrescrever |
| Mesmo ID com revisões diferentes | Preservar versões e comparar alterações. Um downgrade ou reativação exige escolha explícita do host |
| Mesmo hash em IDs ou origens diferentes | Candidato a conteúdo idêntico. Preservar todos os aliases, autores, atribuições e bases de licença. O hash não identifica autoria |
| Mesmo nome ou função com conteúdo diferente | Candidato a sobreposição. Manter registros separados. Registrar variante, fork ou substituição apenas com evidência |

O registro compartilhado liga um ID persistente a mantenedores, origens
versionadas e consumidores. Uma origem canônica só é adotada após concordância
dos mantenedores e resolução de atribuição, dependências e licenças. A licença
mais permissiva de um alias não é herdada por outro. O compartilhamento referencia
a revisão e hash, com escopo de aprovação por canal. Uma cópia modificada pode
ter direitos próprios sem adquirir direitos sobre o upstream.

Os grupos de revisão de marca e de orquestração do DR-0007 entram como
candidatos a revisão. O Hub não funde as Skills de Forge, Model Lab e Project
nem transforma Alethe em conteúdo de autoria Lia.

## Pesquisa reaproveitada

Leitura direta do Lia-Research no commit
`ba08631235da84fcf7765493cfcde013a60c2455`. A matriz de responsabilidades
adota o mapa de propriedade. O termo de orquestração usado na pesquisa para o
Hub se aplica à curadoria e à preparação de artefatos nesta proposta.
[Índice fixado do Lia-Research](https://github.com/BloomRX/Lia-Research/blob/ba08631235da84fcf7765493cfcde013a60c2455/RESEARCH-INDEX.md).

| Referência | Uso nesta proposta |
| --- | --- |
| LR-MCP-002, DR-0011 e DR-0012 | Descritores versionados, tools, transporte, credenciais por referência, egress e instalação explícita. Propostas DR seguem pendentes |
| LR-LIC-001, LR-LIC-003 e DR-0007 | Atribuição por componente, conflitos por origem e revisão humana da consolidação |
| LR-LIC-004 | Referência para proveniência de assets e anexos. Adoção fica sujeita à decisão do Forge |
| LR-MODEL-004 e LR-MODEL-005 | Distinguir catálogo, compatibilidade declarada e medição por alvo. Preservar a matriz como evidência de pesquisa |
| LR-SEC-001 e LR-SEC-005 | Segredos no host. Metadados de evidência do host sem copiar Grants, Leases ou dados de sessão |

Ver [matriz, lacunas e plano de implementação](../operations/CAPABILITY-REGISTRY-READINESS.md).
