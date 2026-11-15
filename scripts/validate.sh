#!/usr/bin/env bash
# Validação de integridade do repositório: docs + testes + sintaxe.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=".venv/bin/python"
[ -x "$PY" ] || PY="python3"

echo "== 1/4 Documentação =="
"$PY" docs/research/verify-consistency.py

echo "== 2/4 Sintaxe dos módulos =="
"$PY" - <<'EOF'
import pathlib, py_compile, sys
falhas = []
for p in sorted(pathlib.Path("src").rglob("*.py")):
    try:
        py_compile.compile(str(p), doraise=True)
    except py_compile.PyCompileError as e:
        falhas.append(f"{p}: {e}")
print(f"  {len(list(pathlib.Path('src').rglob('*.py')))} arquivos compilados")
if falhas:
    print("\n".join(falhas)); sys.exit(1)
EOF

echo "== 3/4 Testes =="
export PYTHONPATH="src${PYTHONPATH:+:$PYTHONPATH}"
"$PY" -m pytest -q

echo "== 4/4 Sem segredos versionados =="
"$PY" - <<'EOF'
import pathlib, re, sys
padroes = [
    (re.compile(r"sk-[A-Za-z0-9]{20,}"), "chave estilo OpenAI"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "token GitHub"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "chave AWS"),
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "chave privada"),
]
achados = []
for p in pathlib.Path(".").rglob("*"):
    if not p.is_file() or any(x in p.parts for x in
            (".git", ".venv", "node_modules", "dist", "build", "__pycache__", ".devhome")):
        continue
    if p.suffix in {".png", ".jpg", ".zip", ".exe", ".pyc"}:
        continue
    try:
        t = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    for rx, nome in padroes:
        if rx.search(t):
            achados.append(f"{p}: {nome}")
if achados:
    print("POSSÍVEL SEGREDO VERSIONADO:"); print("\n".join(achados)); sys.exit(1)
print("  nenhum segredo encontrado")
EOF

echo ""
echo "Validação completa: OK"
