# Fluxo de branches e releases

**Status:** fluxo atualizado por solicitação do responsável do projeto em 2026-11-26. Substitui a regra inicial de Arena permanente e `main` apenas documental.

## Objetivo

Manter código e documentação canônicos em `main`, com integração coordenada pelo Codex e branches Arena temporárias quando uma missão específica precisar delas.

## Regras

1. **`main`**
   - Contém a implementação integrada, a documentação vigente e as decisões aceitas.
   - É a base de novas missões e a referência das versões lançadas.
   - Recebe código e documentação dentro do escopo autorizado, após as verificações aplicáveis.
   - A integração em `main` não equivale, por si só, a publicar uma release.

2. **Missões temporárias do Arena**
   - Abrir uma sessão quando houver uma missão específica; sua branch parte da `main` atual.
   - Cada sessão trabalha na própria branch, conforme o limite da plataforma.
   - A branch deve ter nome identificável, por exemplo `arena/<session-id>-lia-agenthub`.
   - O escopo vem da missão autorizada; uma nova sessão não reinicia automaticamente a Fase 0.

3. **Sessões seguintes**
   - Devem iniciar da `main` atual, salvo quando o usuário indicar outra base.
   - Cada agente trabalha apenas na branch atribuída à sua sessão.
   - Especialistas podem pesquisar outras branches, mas não modificá-las.

4. **Codex e integração**
   - Codex é o integrador de código e documentação dentro do escopo aprovado.
   - Arena e Codex não devem editar simultaneamente os mesmos arquivos/branch.
   - Integrações entre branches devem ser sequenciais, revisadas e rastreáveis.
   - Antes de remover uma branch de missão, registrar seu SHA e o destino da entrega; preservar conteúdo exclusivo em arquivo histórico verificável. A branch não permanece como linha paralela de desenvolvimento.

5. **Release**
   - Uma versão só é lançada após revisão humana, testes aplicáveis, documentação e aprovação.
   - Releases partem de `main`; branches de missão podem ser integradas antes do ciclo de release, conforme autorização e revisão aplicáveis.
   - Não fazer merge automático, force-push ou alteração da branch padrão sem autorização explícita.
   - Registrar versão/tag e notas de release após o aceite.

## Observação sobre a branch padrão

A branch padrão permanece `main`. O [registro da consolidação de 2026-11-26](operations/BRANCH-CONSOLIDATION-2026-11-26.md) identifica o estado anterior, os backups e as ações ainda pendentes. A política nova não transforma a preparação documental em evidência de que refs remotas já foram alteradas.
