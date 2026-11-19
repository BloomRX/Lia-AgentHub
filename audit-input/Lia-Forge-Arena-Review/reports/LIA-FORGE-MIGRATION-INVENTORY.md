# Inventário de migração — Lia Agent Hub

IDs oficiais: ainda não atribuídos. A origem das entradas é o código ou documentação do snapshot T13. O código próprio está acompanhado da licença MIT; os componentes instaláveis externos têm condições próprias.

| Capacidade | Estado | Evidência e dependências | Operação e limites |
| --- | --- | --- | --- |
| Studio desktop e UI | implemented | electron/main.cjs, src/, vite.config.js. Electron, React e Vite | Entradas presentes. Runtime e NSIS pendentes nesta migração. |
| Catálogo, inspeção, reconciliação e Comparison Lab | implemented | shared/assets/, shared/services/studio-service.mjs. Arquivos e registro do projeto | Fluxos no código e smokes presentes. Validação integrada no novo ambiente pendente. |
| Launcher Windows | implemented | lia-forge.cmd, scripts/spriteforge_launcher.py. Python e ambiente Node | Entradas presentes. Inicialização não executada nesta rodada. |
| MCP Lia Forge | implemented | scripts/spriteforge-mcp.mjs, scripts/mcp_config.py, docs/mcp.md. Node e SDK MCP | Servidor próprio. Handshake depende de instalar dependências e configurar cliente. |
| Workflows e adapters | implemented | shared/, docs/WORKFLOW-ENGINE.md. Node e dependências por adapter | Execução condicional a gates, ferramentas e configuração. |
| ComfyUI e Blender | partial | workflows/comfyui/, scripts/comfyui-client.mjs, scripts/blender_spritesheet.py, electron/blender-adapter.cjs | Integração própria presente. Renderização e difusão reais dependem de instalações, modelos licenciados e validação do usuário. |
| Skills de marca | implemented | .agents/skills/lia-brand-check/SKILL.md. Host compatível | Instruções disponíveis no snapshot. Carregamento em host não testado. |
| Orquestração e conhecimento expandidos | proposed | docs/INTELLIGENT-ORCHESTRATOR.md, docs/SKILLS-KNOWLEDGE-ENGINE.md | Propostas além dos componentes existentes. |
| Evoluções do roadmap | planned | docs/MASTER-ROADMAP.md, docs/CAPABILITY-BOUNDARIES-AND-ROADMAP.md | Marcos documentais aguardam execução e aceite. |
| Assets privados e pesos | blocked | Política em docs/PROVIDER-AND-MODEL-ADMISSION-POLICY.md | Proveniência e direitos precisam de aprovação individual. |
| MCPs e Skills de terceiros pesquisados | unknown | Referências de pesquisa em docs/ | Disponibilidade e licença operacional variam. Instalação não comprovada. |
