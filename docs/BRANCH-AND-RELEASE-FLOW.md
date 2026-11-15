# Fluxo de branches e releases

**Status:** regra inicial de trabalho definida pelo responsável do projeto.

## Objetivo

Manter a documentação inicial e as versões publicadas em `main`, enquanto o desenvolvimento ativo ocorre em uma branch de trabalho criada pela sessão Arena.

## Regras

1. **`main`**
   - Contém a documentação inicial do produto e decisões aceitas.
   - É a linha estável e futura referência de versões lançadas.
   - Não recebe implementação contínua nem commits rotineiros do Arena.
   - Só recebe mudanças de release ou documentação estável aprovada.

2. **Branch inicial do Arena**
   - O Arena cria sua própria branch a partir de `main` ao iniciar a primeira sessão de trabalho.
   - A branch criada passa a ser a base ativa de desenvolvimento, após o usuário confirmar que ela é a branch correta.
   - A branch deve ter nome identificável, por exemplo `arena/<session-id>-lia-agenthub`.
   - A primeira missão é Fase 0: pesquisa, auditoria e documentação; não implementação.

3. **Sessões seguintes**
   - Devem iniciar da branch ativa de desenvolvimento, não de `main`, salvo quando o usuário indicar outra base.
   - Cada agente trabalha apenas na branch atribuída à sua sessão.
   - Especialistas podem pesquisar outras branches, mas não modificá-las.

4. **Codex e integração**
   - Codex implementa somente depois da aprovação do escopo e da especificação.
   - Arena e Codex não devem editar simultaneamente os mesmos arquivos/branch.
   - Integrações entre branches devem ser sequenciais, revisadas e rastreáveis.

5. **Release**
   - Uma versão só é lançada após revisão humana, testes aplicáveis, documentação e aprovação.
   - A promoção da branch ativa de desenvolvimento para `main` ocorre por PR/revisão de release.
   - Não fazer merge automático, force-push ou alteração da branch padrão sem autorização explícita.
   - Registrar versão/tag e notas de release após o aceite.

## Observação sobre a branch padrão

A branch padrão do GitHub pode continuar apontando para `main`. A branch Arena ativa funciona como base de desenvolvimento por escolha explícita das sessões e do usuário; não é necessário tornar a branch Arena a branch padrão do repositório para seguir este fluxo.
