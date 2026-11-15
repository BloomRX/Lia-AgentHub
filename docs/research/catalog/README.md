# Registros de catálogo — formato oficial do Lia Agent Hub

**O que isto é:** 48 registros de Agent Skills encontradas nos repositórios Lia, já no formato implementado pelo Hub (`schemaVersion: 1`), prontos para conferência e para importação real.

**O que isto NÃO é:**
- **não** é um catálogo paralelo (usa o contrato do Hub, chave por chave);
- **não** é a biblioteca do Hub (a biblioteca real vive em `%USERPROFILE%\Lia\AgentHub\Biblioteca`, na máquina do usuário);
- **não** contém payload de skills — nenhum arquivo foi copiado de outro repositório Lia para cá (cópia entre repositórios exige autorização);
- **não** aprova nada: todos os registros estão `trust: unreviewed` e `lifecycle: quarantined`.

## Arquivos

| Arquivo | Conteúdo |
|---|---|
| `sources.json` | fontes fixadas por repositório, branch, **commit** e data, mais as notas de pesquisa de cada skill |
| `lia-studio.records.json` | 16 registros · `Lia-Studio@203b60f17d177f7faf79d293b95f078d0d0a729a` |
| `lia-project.records.json` | 22 registros · `Lia-Project@0093de090d86c291b7a85eaeacebe0a559585359` |
| `lia-model-lab.records.json` | 9 registros · `Lia-Model-Lab@3ec4313ba57ec94a7f3d93ec4f7a0d533d5077cf` |
| `lia-forge.records.json` | 1 registro · `Lia-Forge@35b207f7b1ae5bc0c104fbdd0e9cf6ae83944692` |

## Estrutura de cada registro

```jsonc
{
  "capability":    { /* formato exato de .lia/capability.json  — contrato do Hub */ },
  "provenance":    { /* formato exato de .lia/provenance.json  — contrato do Hub */ },
  "researchNotes": { /* pesquisa: origem, commit, licença, reuso, issues, avisos.
                         FORA do contrato. Não gravar em .lia/ sem decisão humana. */ }
}
```

## Como regenerar

```bash
python3 docs/research/tools/build-catalog-records.py \
  --sources docs/research/catalog/sources.json \
  --out docs/research/catalog
```

Requisito: checkouts locais dos quatro repositórios nos commits de `sources.json` (a ferramenta só lê; não clona, não instala, não executa nada dos repositórios). Somente Python 3 stdlib.

## Honestidade sobre os hashes

`id`, `contentHash`, `treeHash` e os hashes por arquivo foram calculados por **ferramenta de pesquisa** que reimplementa o algoritmo documentado em `src/lia_agenthub/domain/integrity.py` e `adapters/importer.py` (Hub @ `b4eb85f`). Classe de evidência: **EXECUTED pela pesquisa, não VALIDATED pelo Hub**. O roteiro de conferência está em [`../SKILL-CATALOG-IMPORT-REPORT.md`](../SKILL-CATALOG-IMPORT-REPORT.md) §5: importar uma pasta e comparar os três valores.

## Limitações conhecidas dos registros (detalhes no relatório de importação §4.2)

| Limitação | Efeito |
|---|---|
| descrição só vem de manifesto | 48 registros com `description: ""`, embora todas as skills tenham `description` no frontmatter |
| licença só por arquivo na raiz do payload | 47 de 48 com `license.status: "unknown"` (só `alethe` tem `LICENSE` no payload) |
| `metadata:` aninhado é ignorado pelo parser do Hub | `alethe` perde `version: "19"` → `0.1.0` |
| sem campo de derivação no contrato | a cadeia "adaptada de X no commit Y" vive em `researchNotes.derivationUrl` |
| nome da pasta derivado da primeira subpasta | `alethe` e `lia-game-project-bootstrap` recebem aviso espúrio `NAME_FOLDER_MISMATCH` |
