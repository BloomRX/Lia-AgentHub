# Pesquisa e registro de referências

Consulta: **2026-11-15**, via arquivos locais e GitHub API (`gh api`); sem executar aplicações externas, sem copiar componentes, fontes ou ícones. Observações externas são **RESEARCH**, não testes de usabilidade. Todas as descobertas desta frente destinam-se ao **Hub como referência de UX**; execução permanece no host.

## 1. Fontes internas e ecossistema

| Fonte examinada | Revisão/arquivos | Evidência e uso |
|---|---|---|
| Lia Agent Hub | `arena/a92004be-lia-agenthub` na base `7cec491a563de8a75abe56d5aad1b115fec9db44`; `src/lia_agenthub/resources/static/{index.html,app.css,app.js}`, `interface/server.py`, `domain/model.py` | IMPLEMENTED por leitura: telas, payloads, enum, campos. Origem dos achados A01–A18 |
| Documentação Hub | Mesma base: `AGENTS.md`, `README.md`, `docs/{PRODUCT-VISION,PHASE-0-ARENA-BRIEF,DECISION-REGISTER,BRANCH-AND-RELEASE-FLOW}.md`, `architecture/{PRODUCT-BOUNDARIES-AND-ARCHITECTURE,SECURITY-AND-TRUST-MODEL}.md`, `pyproject.toml` | Limites de produto e evidência. Visão antiga mais ampla não autoriza execução ou autoria nesta entrega |
| Biblioteca local | `docs/KIT-PROJETO-NOVO.zip` → `APP-WINDOWS/PADRAO-DA-MARCA.md` | Título interno é “Padrão de pastas, distribuição e a regra do pip”: não é manual de cores. Diretriz útil: transparência de caminhos e diagnóstico. Não importar propostas de armazenamento para o Hub por razões estéticas |
| [Lia Studio](https://github.com/BloomRX/Lia-Studio/tree/ba70d224359b84a8e114f87b545d83f260f2deb1) | `main@ba70d224359b84a8e114f87b545d83f260f2deb1`: `README.md`, `docs/BRAND-STANDARDS.md`, `docs/UI-UX-DESIGN-SYSTEM-LIA-STUDIO.md` | Último arquivo contém somente `PLACEHOLDER`; **não** existe evidência ali para atribuir-lhe um design system completo. BRAND-STANDARDS orienta família, não componentes obrigatórios |
| [Lia Forge](https://github.com/BloomRX/Lia-Forge/tree/6bd9a5a7006c7c6ccf5edcb5d577283d61a39949) | `main@6bd9a5a7006c7c6ccf5edcb5d577283d61a39949`: `README.md`, `docs/BRAND-STANDARDS.md` | Autonomia, transparência, personalidade moderada; README não prova funções de branches não integradas |
| [Lia Project](https://github.com/BloomRX/Lia-Project/tree/9c7ac183fd54b8eae0425038190a2c56ec237ff8) | `main@9c7ac183fd54b8eae0425038190a2c56ec237ff8`: `README.md`, `docs/BRAND-STANDARDS.md`, `airi/apps/lia-app/src/renderer/src/styles/lia-tokens.css` | Tokens semânticos, Segoe UI, escala 4px, raios 8/10/14/18, foco e 150ms identificados em código. Os valores crus da paleta não foram auditados; valores hex desta proposta são próprios, não “oficiais”. AIRI é legado/referência, não arquitetura obrigatória |
| Concept do usuário | `references/gpt-concept-user.png`, anexo original `image-1.png`, 1586×992 (dimensões lidas do cabeçalho PNG) | Referência visual fornecida, descrita como gerada por GPT; sem licença explícita. Não autoriza redistribuir marca/personagem como asset. Análise na auditoria §4 |

Consulta à biblioteca conectada Google Drive: busca ampla por nomes Lia retornou resultados de workflows/assets 3D, primeira página de 30 com paginação; não se concluiu inventário completo. Busca focada `trashed = false and (name contains 'BRAND' or name contains 'UI-UX' or name contains 'PADRAO' or name contains 'KIT-PROJETO')` retornou zero, sem próxima página. Uma primeira query teve sintaxe rejeitada e foi corrigida. Não se leu nem copiou conteúdo privado irrelevante; nenhum documento visual adicional foi encontrado **nessa busca**, não é afirmação de inexistência na conta.

## 2. Aplicações externas: padrões, não cópias

| Referência primária e revisão exata | O que foi realmente consultado | Padrão aproveitado / limite |
|---|---|---|
| [Code OSS / VS Code](https://github.com/microsoft/vscode/tree/d03edc4b18d687c45af067195bad9544b5b07475) | `README.md`; [`extensionsViewlet.ts`](https://github.com/microsoft/vscode/blob/d03edc4b18d687c45af067195bad9544b5b07475/src/vs/workbench/contrib/extensions/browser/extensionsViewlet.ts): contextos de busca, installed, recommended, outdated e unsupported | Separar pertencimento, descoberta e compatibilidade; oferecer filtro antes de sintaxe avançada. No Hub: Biblioteca vs A revisar; não copiar instalação, execução, marketplace ou ranking. Código MIT segundo README; marca do VS Code distinta. Sem copiar código |
| [Microsoft PowerToys](https://github.com/microsoft/PowerToys/blob/4d72a8b17553e674d75bdfe5618580414a26460f/README.md) | README, catálogo nomeado de utilitários com ícones e links específicos, seção de instalação por usuário | Ferramentas técnicas apresentadas por nome e finalidade; adaptação: resumo cotidiano + detalhes técnicos progressivos. Não se auditou o aplicativo de configurações ou WinUI em execução; não prescrever switches de habilitação no Hub. Licença não revisada nesta pesquisa; nenhum asset reutilizado |
| [Obsidian releases / diretório de plugins](https://github.com/obsidianmd/obsidian-releases/blob/a1fbdf2311765ca3930cc8fbaa2ac753613a3ea4/README.md) | README descreve busca por name/author/description, ficha via manifest/README e compatibilidade por versões | Separar registro resumido, detalhe e artefato versionado. No Hub: procedência e versão visíveis; não buscar README remoto automaticamente nem instalar. O próprio README diz que Obsidian não é open source; não usar licença do diretório para atribuir licença ao aplicativo |

Não foram visitados os links de documentação externos citados pelos READMEs fora dos hosts disponíveis. Não alegar observação visual do software instalado a partir de leitura de código. As decisões de layout desta entrega são síntese própria, não reprodução de screenshots externas.

## 3. Princípios de acessibilidade adotados como metas

Alvo proposto: WCAG 2.2 AA, incluindo contraste de texto (1.4.3), contraste não textual (1.4.11), teclado (2.1.1), foco visível/não encoberto (2.4.7/2.4.11), tamanho mínimo de alvo (2.5.8), identificação de erros (3.3.1) e mensagens de estado (4.1.3). Referência normativa para revisão futura: https://www.w3.org/TR/WCAG22/ — **não consultada via rede nesta sessão**; não tratada como nova pesquisa verificada. Não declarar conformidade antes de medição/renderização e testes assistivos reais.

## 4. Licenças, dados e limites

Design e mockups são artefatos propostos nesta branch; sua inclusão não resolve D-16 (licença do repositório). O concept anexado não deve entrar em pacote distribuído sem direitos esclarecidos. Não foram baixadas fontes, bibliotecas de ícones, pesos, plugins ou executáveis. Nenhuma credencial foi solicitada ou documentada. Nenhuma integração entre produtos foi criada.
