# Consolidação de branches — Lia Agent Hub — 2026-11-26

**Estado:** implementação promovida a `main` por fast-forward; **arquivamento por tags e remoção das refs antigas pendentes de execução**.

**Autorização:** solicitação do responsável para concentrar os projetos de produto em `main`, com Codex como integrador e Arena somente em missões temporárias.

**Base desta preparação:** `c81d85013827402254c55177cf0e13613e2d59b1`.

**Escopo:** organização Git e regras de trabalho; nenhum código de produto, teste ou decisão de funcionalidade alterado.

## Mapa anterior à consolidação

Refs registradas no snapshot de **2026-11-26T08:37:35Z**:

| Branch | SHA | Relação com a base `c81d850` | Destino previsto |
|---|---|---|---|
| `main` | `34a27f484e5f85987390a27fe7e0c0b3cd205bb2` | Ancestral; 192 commits atrás | Avançar por fast-forward para a implementação publicada e integrar esta documentação |
| `arena/a92004be-lia-agenthub` | `c81d85013827402254c55177cf0e13613e2d59b1` | Base da implementação publicada | Integrar em `main`; remover a branch após preservação verificada |
| `arena/b6febe41-lia-agenthub` | `3b234f5047ae584beed3eac319b3d38032420ce0` | Divergente: 1 commit exclusivo, 152 atrás | Preservar como histórico de design; remover a branch após preservação verificada |
| `arena/db625478-lia-agenthub` | `b4e63eae800b2713dcda294e3c2dfe8d60eb0b04` | Divergente: 5 commits exclusivos, 192 atrás | Preservar como histórico de pesquisa; remover a branch após preservação verificada |
| `arena/1a7ed773-lia-agenthub` | `bd4bfbb9ed8065be1e571940926d293689985682` | Divergente: 6 commits exclusivos, 192 atrás | Preservar histórico de pesquisa e revisão; remover a branch após preservação verificada |

`bd4bfbb9` tem `b4e63eae` como pai direto. Seus seis arquivos adicionais de revisão já estão presentes na base com os mesmos hashes de blob; o [relatório de implementação](FINAL-IMPLEMENTATION-REPORT.md) registra o cherry-pick `47f5da7`. Isso não incorpora os treze arquivos de pesquisa herdados dessa linha.

## Conteúdo histórico exclusivo

A comparação das árvores identificou **22 arquivos ausentes da base**, sem o mesmo blob em outro caminho: nove de design e treze de pesquisa. Os links abaixo fixam o commit de origem. Eles são referências históricas, não aprovação dessas especificações como regras vigentes do produto. Os objetos também estão preservados no bundle descrito adiante.

### Design — nove arquivos em `3b234f50`

- [docs/design/DELIVERY-VALIDATION.md](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/DELIVERY-VALIDATION.md)
- [docs/design/README.md](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/README.md)
- [docs/design/RESEARCH-REFERENCES.md](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/RESEARCH-REFERENCES.md)
- [docs/design/SCREEN-BY-SCREEN-SPEC.md](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/SCREEN-BY-SCREEN-SPEC.md)
- [docs/design/UI-UX-AUDIT.md](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/UI-UX-AUDIT.md)
- [docs/design/UI-UX-CONCEPT.md](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/UI-UX-CONCEPT.md)
- [docs/design/VISUAL-DESIGN-SYSTEM.md](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/VISUAL-DESIGN-SYSTEM.md)
- [docs/design/prototypes/index.html](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/prototypes/index.html)
- [docs/design/references/gpt-concept-user.png](https://github.com/BloomRX/Lia-AgentHub/blob/3b234f5047ae584beed3eac319b3d38032420ce0/docs/design/references/gpt-concept-user.png)

### Pesquisa — treze arquivos em `b4e63eae`

- [docs/research/LIA-SKILLS-INVENTORY.md](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/LIA-SKILLS-INVENTORY.md)
- [docs/research/LIA-SKILLS-ROADMAP.md](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/LIA-SKILLS-ROADMAP.md)
- [docs/research/README.md](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/README.md)
- [docs/research/SKILL-CATALOG-IMPORT-REPORT.md](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/SKILL-CATALOG-IMPORT-REPORT.md)
- [docs/research/SKILL-LICENSE-AND-PROVENANCE-AUDIT.md](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/SKILL-LICENSE-AND-PROVENANCE-AUDIT.md)
- [docs/research/THIRD-PARTY-SKILLS-CATALOG.md](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/THIRD-PARTY-SKILLS-CATALOG.md)
- [docs/research/catalog/README.md](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/catalog/README.md)
- [docs/research/catalog/lia-forge.records.json](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/catalog/lia-forge.records.json)
- [docs/research/catalog/lia-model-lab.records.json](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/catalog/lia-model-lab.records.json)
- [docs/research/catalog/lia-project.records.json](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/catalog/lia-project.records.json)
- [docs/research/catalog/lia-studio.records.json](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/catalog/lia-studio.records.json)
- [docs/research/catalog/sources.json](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/catalog/sources.json)
- [docs/research/tools/build-catalog-records.py](https://github.com/BloomRX/Lia-AgentHub/blob/b4e63eae800b2713dcda294e3c2dfe8d60eb0b04/docs/research/tools/build-catalog-records.py)

O relatório de implementação ainda cita `docs/research/catalog/sources.json`; o link histórico acima permite recuperar a fonte citada sem afirmar que ela existe na árvore atual. A incorporação de documentos antigos ao produto exige avaliar sua atualidade separadamente desta limpeza de branches.

## Backup verificável

Snapshot: **2026-11-26T08:37:35Z**. O pacote foi gerado fora do repositório antes de qualquer alteração de refs desta consolidação.

- ZIP: `lia-git-backup-2026-11-26T08-37-35Z.zip` — 13.462.694 bytes.
- SHA-256 do ZIP: `a4d33b5dc1e2d945bd428d3c42afa4d8a1acc0346e6c3ca3d28e037efec9872f`.
- Bundle deste repositório: `Lia-AgentHub.bundle` — 3.542.500 bytes; inclui as cinco refs da tabela.
- SHA-256 do bundle: `86f83c3a4e9dfb7ed4510d740e9665abec365dc367917e194883a00ad59441bf`.
- O pacote também contém os bundles de Lia-Studio e Lia-Research, `inventory.json`, `SHA256SUMS` e instruções de restauração em `README.md`.

Verificações executadas: `git fsck --full --strict` no mirror de origem, `git bundle verify`, conferência de todas as refs, clone mirror independente do bundle, igualdade integral das refs restauradas e novo `fsck` na restauração. O ZIP passou na verificação de CRC.

Nenhuma tag foi criada até esta publicação. O backup não inclui trabalho não commitado de sessões locais.

## Execução

Concluído: `main` avançou de `34a27f4` para `c81d850` por fast-forward, com comparação do SHA esperado e sem force-push. Os três checks de CI desse commit estavam aprovados: pytest em Ubuntu, pytest em Windows e verificação do pacote Windows. Esta publicação alinha as regras documentais ao fluxo autorizado.

Ainda pendente:

1. Reconsultar as refs remotas e comparar com os SHAs registrados antes de modificar qualquer uma.
2. Criar e verificar tags de arquivo para os tips históricos, registrando seus nomes e SHAs neste documento; o bundle é a cópia independente já verificada.
3. Remover as quatro branches Arena antigas após confirmar preservação e destino das entregas. Atualizar este estado somente com evidência da operação remota.

Após a consolidação, novas missões partem da `main` atual conforme o [fluxo de branches e releases](../BRANCH-AND-RELEASE-FLOW.md). A integração não publica automaticamente uma versão do produto.
