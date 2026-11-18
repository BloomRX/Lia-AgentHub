# Checklist de prontidão do produto — Lia Agent Hub

**Data:** 2026-11-15 (UTC)
**Base:** `docs/operations/FUNCTIONAL-COMPLETION-REPORT.md`
**Uso:** marcar antes de qualquer entrega a outra pessoa. Um item não marcado
não é falha de vergonha — é informação para quem decide entregar.

---

## 1. Pronto para uso pessoal hoje

Estes itens foram executados e verificados **neste ambiente** (Linux):

- [x] Importar pasta, `.zip` e `.lia-capability`, com quarentena obrigatória
- [x] Ver proveniência, licença, risco e os fatores que compõem o risco
- [x] Validar estrutura de `SKILL.md` contra a spec
- [x] Comparar duas versões com diff de frontmatter e de corpo
- [x] Exportar pacote privado, inclusive com licença desconhecida
- [x] Verificar integridade de um pacote recebido, com motivo da recusa
- [x] Publicar `index.json` e lê-lo **sem o Hub** (leitor de referência)
- [x] Ler a biblioteca inteira em editor de texto, sem o aplicativo
- [x] Usar a CLI (`validate`, `pack`, `index`, `verify-package`, `diagnostico`)
- [x] Registrar servidor MCP e gerar configuração de host para colar
- [x] Rodar tudo offline — `socket.connect` proibido nos testes de fronteira

**Veredito:** o produto entrega valor hoje, sozinho, offline, sem conta.

---

## 2. Pronto para entregar a outra pessoa (distribuição)

- [x] **Executável Windows gerado e testado no host de homologação**. A cópia
      externa abriu em WebView2 e passou pelos fluxos de diagnóstico, importação,
      exportação, persistência e encerramento.
- [ ] **Execução em máquina sem Python** — bloqueada por falta de Windows limpo.
- [ ] **Zero egress na janela nativa (D-09)** — o controle chegou ao runtime.
      O NetLog ainda registrou DNS sobre HTTPS externo.
- [ ] **`D-16` — licença do projeto** — sem `LICENSE`, o direito de reutilização
      não está concedido por padrão
- [ ] **Assinatura de código** — sem ela, o SmartScreen mostra aviso

**Veredito:** build utilizável no host testado, distribuição pública bloqueada.
A matriz e as medições estão no [relatório Windows](WINDOWS-VALIDATION-REPORT.md).

---

## 3. Pronto para o design visual (a próxima etapa)

- [x] Funcionalidade concluída: 22 rotas HTTP, todas com caminho na UI
- [x] Contrato de dados estável e fixado por teste (`test_ui_api_contract`)
- [x] Estados de erro, vazio e recuperação existem e são testados
- [x] Doutrina de honestidade no código, não só no doc:
      - nunca verde para "importado"; verde só para revisado por humano
      - sufixo `-NAO-REVISADO` explicado ao usuário, não só no nome do arquivo
      - "isto prova integridade, não autoria" no leitor e no verificador
      - `connectivityVerified: false` em todo registro de MCP
- [x] Design brief completo em `docs/stitch/design-brief-hub/` (6 docs)
- [x] Sete prompts autossuficientes prontos para o Stitch

**Veredito:** a UI pode ser redesenhada sem tocar em contrato. O que a nova
interface **não pode** fazer: sugerir confiança que o Hub não verificou,
esconder qual licença é desconhecida, ou apresentar catálogo como operacional.

---

## 4. Nunca deve ser verdade — guardas ativos

Estes itens são negativos de propósito. Cada um tem teste que falha se mudar:

- [x] Nada é executado — `TestFronteirasStitch` prova que script importado não roda
- [x] Nenhum segredo em schema, log, índice ou exemplo
- [x] Hash nunca é chamado de assinatura
- [x] Hub não conecta MCP — importação e geração de config não abrem socket
- [x] Quarentena nunca é publicada no índice
- [x] Exportação pública recusada sem base de redistribuição
- [x] `null` nunca vira `0`, `false` ou "não" na exibição
- [x] Nenhuma decisão foi aprovada por sessão de código

---

## 5. Como verificar cada item marcado

```bash
# estado geral
.venv/bin/python -m pytest -o addopts="" -q                    # 822 passed, 2 skipped

# os guardas de honestidade
.venv/bin/python -m pytest tests/integration/test_ui_api_contract.py -q
.venv/bin/python -m pytest tests/integration/test_ui_wiring.py -q
.venv/bin/python -m pytest tests/security/test_network_boundary.py -q
.venv/bin/python -m pytest tests/integration/test_decision_register.py -q
.venv/bin/python -m pytest tests/integration/test_report_consistency.py -q

# contrato consumível sem o Hub
python -S docs/examples/independent-reader/read_index.py <index.json> --check

# intake de inventários v1 (P0 do registro central)
.venv/bin/python -m pytest tests/unit/test_inventory_domain.py -q
.venv/bin/python -m pytest tests/integration/test_inventory_intake.py -q
.venv/bin/python -m pytest tests/security/test_inventory_boundary.py -q
PYTHONPATH=src python -m lia_agenthub.cli inventory preview docs/examples/intake/demo-lia-studio.valid.json --json

# corpus real (53 skills do ecossistema)
.venv/bin/python docs/operations/evidence/corpus_probe.py
```

---

## 6. Escopo da evidência

A seção de distribuição usa os resultados do Windows de 18 de novembro de
2026. As demais seções refletem a execução funcional do Arena em Linux.
