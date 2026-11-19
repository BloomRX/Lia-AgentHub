# Revisão Arena — Lia Forge

Origem BloomRX/Lia-Forge, branch arena/649f88bd-3dspritesheet, commit 018b4e1a4113e7b3280efe10bc1ff7176ab86e32.
O ZIP de migração foi verificado com SHA-256 44571843685bc74628012985f0055bdde640e3a7f185125a7d845cf4d00de531. A comparação lê a árvore Git desse commit e compara bytes por caminho. Resultado: 189 idênticos, 25 ajustados, 13 excluídos e 6 documentos adicionados.

- reports/ contém os seis relatórios verificados byte a byte contra o ZIP original, incluindo detalhes dos ajustes e exclusões.
- manifest/ contém hashes dos 220 arquivos do snapshot e a comparação completa. O conteúdo e os hashes de origem dos arquivos excluídos ficaram fora.
- source-audit/snapshot/ contém código, documentação, configurações e testes do snapshot. Consulte electron/main.cjs e electron/paths.cjs para desktop e APPDATA, scripts/spriteforge-mcp.mjs para MCP, workflows/comfyui/ e scripts/blender_spritesheet.py para pipelines.
- source-audit/DOCUMENT-LINKS.tsv lista destinos internos candidatos a revisão. A busca cobre links Markdown inline; âncoras, referências indiretas e falsos positivos exigem revisão manual.
- tests/ contém comandos e códigos de saída, stdout e stderr integrais com caminhos locais mascarados. Os logs são de uma reexecução isolada; os resultados da migração original estão em reports/.
- licenses/ contém LICENSE e THIRD_PARTY_NOTICES.md. O parecer de proveniência está em reports/.

Foram executadas 117 verificações e consultas de versão. Falhas: lia-paths. No smoke APPDATA, uma fixture sem drive é normalizada pelo Windows com unidade. Compare a assertiva com o resolvedor antes de classificar impacto de produto. Instalação, Electron em execução, Blender, ComfyUI e build ficaram pendentes. O pacote não contém histórico Git, modelos, os binários visuais excluídos nem os ZIPs proprietários. O arquivo local-renderer-test/scripts/runner-smoke.cjs consta no inventário original, mas sua cópia foi omitida deste pacote por conter nomes de perfil em caminhos de fixture. As verificações por padrões têm cobertura limitada.

## Ponte privada de auditoria

Uso exclusivo para auditoria. Capacidades, dependências e recursos aguardam decisão individual sobre integração. Nenhuma instalação, execução do aplicativo ou teste novo foi feito para publicar esta cópia.

- SHA-256 do ZIP de revisão recebido: 2b13d87d762854b3ad888797f952e38b0a6d36f04fe982763f27f52c159865fb
- SHA-256 do ZIP original: 44571843685bc74628012985f0055bdde640e3a7f185125a7d845cf4d00de531
- Inventário de hashes da publicação: [PUBLISHED.sha256](manifest/PUBLISHED.sha256). O hash do próprio inventário é informado separadamente.
- [Comparação com a origem](manifest/ORIGIN-COMPARISON.tsv), [25 ajustes da migração](reports/MIGRATION-SECURITY-AUDIT.md), [13 exclusões da migração](reports/MIGRATION-EXCLUSIONS.md) e [resultados com códigos de saída](tests/RESULTS.json).

A ponte passou por leitura textual, checagem de integridade, filtragem de formatos e busca por padrões de chaves, e-mails, nomes e caminhos locais. Os hashes em SNAPSHOT.sha256 ainda identificam o snapshot original. A sanitização é seletiva e o resultado de triagem tem cobertura limitada.

### Cópias sanitizadas nesta publicação

- `licenses/THIRD_PARTY_NOTICES.md`
- `source-audit/snapshot/docs/guia-externo/00-PADRAO-DA-MARCA.md`
- `source-audit/snapshot/package-lock.json`
- `source-audit/snapshot/scripts/generate_third_party_notices.py`

### Cópias omitidas nesta publicação

- `source-audit/snapshot/assets/lia-forge.svg` — arte visual dispensável à revisão.
- `source-audit/snapshot/tests/external-tools-smoke.cjs` — fixture com caminho local, fora da investigação de APPDATA.

A cópia de runner-smoke.cjs já estava ausente do pacote de revisão. Os ZIPs de migração e revisão permanecem locais. Os logs são os da reexecução anterior, com caminhos pessoais mascarados.
