# Validação e instalação posterior

Windows, Node 24.22.2 e Python 3.14.3.

- node --check: 108/108 aprovados. Falhas: nenhuma.
- JSON: 8 arquivos analisados.
- Python: compilação estática de todos os fontes .py aprovada.
- tests/imaging-smoke.mjs: PASS
- tests/qa-content-smoke.mjs: PASS
- tests/glb-inspect-smoke.mjs: PASS
- tests/navigation-guard-smoke.cjs: PASS
- tests/lia-paths-smoke.cjs: FAIL (exit 1)
- O smoke de caminhos falhou na assertiva de APPDATA: a resolução nativa Windows acrescenta a unidade à fixture sem drive. A falha foi mantida para Arena revisar.
- Entrada Electron, versões diretas do manifesto e lockfile coerentes.

NOT_TESTED: npm ci, suíte npm completa, execução Python integral, Electron, build e instalador. Dependências e ferramentas externas ficaram fora desta execução.

Após aprovação, extraia e confira os hashes, copie o conteúdo de Lia-Forge para o novo repositório e confirme Node >=22.12.0 e Python 3. Revise package.json e lockfile antes de npm ci. Em projeto de demonstração, execute npm test, python -m unittest discover -s tests -p "test_*.py", npm run build, npm run desktop e npm run package:win. Configure MCP e ferramentas externas somente conforme autorização e licenças. Arena deve conferir referências de documentação e a troca do ícone de empacotamento antes da publicação.

## Referências relativas sem alvo no snapshot

A lista cobre links Markdown simples. Referências em código, imagens citadas em prosa, âncoras e destinos com espaços exigem revisão complementar.

- memory-bank/estado.md → README.md
