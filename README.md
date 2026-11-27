<h1 align="center">Lia Agent Hub</h1>

<p align="center">
  <strong>Um lugar para descobrir, organizar e compartilhar capacidades de agentes de IA.</strong><br>
  Skills, servidores MCP, prompts, workflows, templates e referências, com origem, integridade e revisão humana.
</p>

<p align="center">
  <a href="#como-funciona">Como funciona</a> ·
  <a href="#principais-recursos">Recursos</a> ·
  <a href="#experimente">Começar</a> ·
  <a href="docs/MVP-GUIA.md">Guia de uso</a>
</p>

> **MVP funcional, em evolução.** O Hub mantém um catálogo local e portátil e oferece operações próprias de validação supervisionada. Não é um sistema de execução irrestrita de Skills nem uma loja que instala código automaticamente.

## Como funciona

Encontrou uma Skill, um pacote ou uma configuração de MCP que gostaria de usar em um projeto? O Hub ajuda a responder quatro perguntas: **o que é**, **de onde veio**, **quais riscos e direitos estão declarados** e **como transportá-lo com segurança**.

```text
Importar → Quarentena → Inspecionar → Revisar → Biblioteca
                                           ↓
                                Versionar e exportar
```

O conteúdo importado permanece passivo. Um hash confirma integridade de bytes, **não** autoria, permissão de uso ou segurança. Quem decide promover ou compartilhar uma capacidade é a pessoa.

## Principais recursos

| Área | O que oferece |
| --- | --- |
| **Biblioteca** | Pesquisa e filtros por categoria, confiança, tags e metadados de capacidades. |
| **Importação segura** | Entrada por arquivo, pasta, ZIP ou pacote `.lia-capability`, com quarentena e revisão antes da promoção. |
| **Skills** | Leitura e validação estrutural de `SKILL.md`; diagnósticos não equivalem a execução ou aprovação de segurança. |
| **Origem e licença** | Metadados de procedência, regras de risco e identificação de condições que exigem revisão. |
| **Integridade** | Hashes SHA-256 por arquivo e árvore, deduplicação e detecção de adulteração em pacotes. |
| **Versionamento** | Comparação semântica entre versões, incluindo descrição, conteúdo e ferramentas declaradas. |
| **Portabilidade** | Exportação `.lia-capability`, índice `index.json` e leitor de referência independente. |
| **Supervisão** | CLI e broker de operações próprias do Hub, com autorização do operador, estados e auditoria. |

### O que significa `skill.validate`

O Hub oferece uma operação **de validação estrutural de texto de Skill**. A Lia Desktop já pode acioná-la de forma supervisionada: seleciona o texto, pede confirmação, usa uma autorização temporária do operador e exibe o resultado.

Isso **não instala, não roda e não certifica** a Skill recebida. O Hub não executa os artefatos que apenas cataloga.

## Experimente

A experiência foi planejada para **Windows**, com interface local em janela WebView2 (ou navegador, quando necessário).

Para iniciar a partir do código, com **Python 3.11+**:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
lia-agenthub
```

A configuração do ambiente e a política de execução do PowerShell podem exigir passos adicionais. Consulte o [guia de instalação e uso](docs/MVP-GUIA.md) antes de testar importações de terceiros.

Ainda não há neste repositório uma GitHub Release pública de executável Windows assinada e validada. A configuração de build existe, mas distribuição exige seus gates próprios.

## Privacidade e limites

- **Local-first:** biblioteca, quarentena e pacotes ficam em diretórios controlados pelo usuário.
- **Sem confiança automática:** a presença de um arquivo `LICENSE` ou um checksum não autoriza redistribuição.
- **Sem segredos nos pacotes:** os formatos descrevem nomes de variáveis de ambiente, não seus valores.
- **Sem execução genérica:** instalar ou executar capacidades cabe ao host e a permissões específicas, não ao catálogo.

Há uma proposta de evidência detalhada por arquivo na [PR #1](https://github.com/BloomRX/Lia-AgentHub/pull/1). Até sua integração, ela não deve ser anunciada como parte da `main`.

## Estado do projeto

O MVP de catálogo, importação, revisão, versionamento, empacotamento e CLI está implementado. A execução supervisionada V1 tem contrato próprio; operações adicionais, distribuição pública, validação do executável Windows e alguns gates de rede continuam em evolução.

- [Guia para quem usa](docs/MVP-GUIA.md)
- [Arquitetura e fronteiras do produto](docs/architecture/PRODUCT-BOUNDARIES-AND-ARCHITECTURE.md)
- [Execução supervisionada V1](docs/architecture/SUPERVISED-EXECUTION-V1.md)
- [Prontidão e pendências](docs/operations/PRODUCT-READINESS-CHECKLIST.md)
- [Desenvolvimento](docs/DESENVOLVIMENTO.md)

## Dentro do ecossistema Lia

O Agent Hub é uma biblioteca independente para [Lia Desktop](https://github.com/BloomRX/Lia-Project), [Lia Studio](https://github.com/BloomRX/Lia-Studio), [Lia Forge](https://github.com/BloomRX/Lia-Forge) e outros hosts. Cada produto controla suas próprias permissões, execução e dados; consumir o índice não exige manter o Hub aberto.

Quem desenvolve com agentes deve consultar [`AGENTS.md`](AGENTS.md) e o [fluxo de branches](docs/BRANCH-AND-RELEASE-FLOW.md). A licença do repositório ainda é uma decisão aberta (D-16); não presuma uma licença geral de redistribuição. Consulte também os [avisos de terceiros](THIRD_PARTY_NOTICES.md).
