# Lia Agent Hub — proposta independente de UI/UX

**2026-11-15 · PROPOSED / RESEARCH · não é aprovação de implementação.**

Direção: **biblioteca e oficina de capacidades**, com superfícies ameixa escuras, acento Sakura contido, hierarquia editorial e evidência antes de confiança. Sem executar, instalar ferramentas, conectar MCPs, guardar credenciais ou orquestrar agentes.

## Roteiro de leitura

1. [Auditoria](UI-UX-AUDIT.md): problemas verificáveis, prioridades e limitações.
2. [Conceito](UI-UX-CONCEPT.md): arquitetura de informação, jornadas e fronteiras.
3. [Sistema visual](VISUAL-DESIGN-SYSTEM.md): tokens, componentes e acessibilidade.
4. [Especificação por tela](SCREEN-BY-SCREEN-SPEC.md): comportamento, dados e aceite.
5. [Referências e evidências](RESEARCH-REFERENCES.md): commits e fontes consultadas.
6. [Protótipo navegável](prototypes/index.html): documento HTML independente, abrir no navegador; dados fictícios, sem API ou dependências. Não é aplicativo funcional.
7. [Concept anexado](references/gpt-concept-user.png): original preservado, não screenshot do produto.

## Escopo e evidência

- Repositório trabalhado: `BloomRX/Lia-AgentHub`; branch exclusiva `arena/b6febe41-lia-agenthub`, base e código auditado `7cec491a563de8a75abe56d5aad1b115fec9db44` da referência `arena/a92004be-lia-agenthub`.
- Apenas `docs/design/` foi alterado. Nenhuma alteração em implementação, contratos, configuração, build ou outros repositórios. Nenhum merge/PR.
- **IMPLEMENTED** identifica código presente na base, não comportamento comprovado em desktop.
- **RESEARCH**: leitura de código/documentos e análise da imagem fornecida. **PROPOSED**: todas as telas e melhorias desta entrega.
- **EXECUTED** nesta frente: consultas GitHub/Drive, inspeção de arquivos e verificações documentais locais; não foram executados Hub, MCPs, scripts de capacidades ou builds. Sem teste de usabilidade ou validação Windows/WebView2. Protótipo não validado em navegador automatizado.
- Documentos históricos de Fase 0 e README divergem sobre autorização/contagem de testes; esta entrega não resolve governança nem repete contagem como evidência própria.

## Sequência sugerida após o gate técnico

1. Corrigir semântica de revisão e filtros; foco, mensagens e estados concorrentes (P0/P1 da auditoria).
2. Aplicar tokens e reorganizar telas existentes, sem novas capacidades de backend.
3. Introduzir detalhe em página, revisão guiada e exportação explícita usando contratos existentes, com testes.
4. Só depois avaliar dashboard agregado, coleções persistentes, leitura de conteúdo e autoria. Não anunciar recursos indisponíveis.

As decisões reversíveis foram tomadas aqui; alternativas estão registradas. Pendências humanas reais: direitos de arte/marca antes de distribuição, aceite da linguagem de confiança, priorização de persistência de coleções e autoria. Não bloqueiam revisão da proposta.
