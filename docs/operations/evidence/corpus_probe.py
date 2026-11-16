"""Sonda de corpus real — importa Skills reais e mede o efeito das regras.

Não versiona payloads (são de terceiros/proprietários). Espera os clones em
$LIA_CORPUS (padrão /tmp/liacorpus), nos commits registrados em
docs/research/catalog/sources.json.

Mede o que a revisão independente mede: quantas Skills reais IMPORTAM, quantas
são recusadas, e com quais códigos. Serve para provar antes/depois.
"""
from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from lia_agenthub.adapters.paths_resolver import resolve_locations  # noqa: E402
from lia_agenthub.app import AgentHub  # noqa: E402

CORPUS = Path(os.environ.get("LIA_CORPUS", "/tmp/liacorpus"))
REPOS = ("studio", "Lia-Model-Lab", "Lia-Project", "Lia-Forge")


def skills() -> list[Path]:
    achados = []
    for repo in REPOS:
        base = CORPUS / repo
        if not base.is_dir():
            continue
        for p in sorted(base.rglob("SKILL.md")):
            if "skills" in p.parts:
                achados.append(p.parent)
    return achados


def main() -> int:
    alvos = skills()
    if not alvos:
        print(json.dumps({"erro": "corpus ausente", "caminho": str(CORPUS)}))
        return 2

    home = Path(tempfile.mkdtemp())
    hub = AgentHub(resolve_locations(home / "h"))

    codigos: Counter = Counter()
    bloqueadas = []
    ok = 0
    total_refs = 0
    skills_com_issue = 0

    for pasta in alvos:
        r = hub.import_path(str(pasta), dry_run=True)
        if r.ok:
            ok += 1
        else:
            bloqueadas.append({"skill": pasta.name, "motivo": r.blocked_reason})
        if r.issues:
            skills_com_issue += 1
        for i in r.issues:
            codigos[f"{i['code']}/{i['severity']}"] += 1
            if "REFERENCE" in i["code"]:
                total_refs += 1

    shutil.rmtree(home, ignore_errors=True)
    saida = {
        "skills_no_corpus": len(alvos),
        "importam": ok,
        "bloqueadas": len(bloqueadas),
        "skills_com_issue": skills_com_issue,
        "refs_levantadas": total_refs,
        "por_codigo": dict(sorted(codigos.items())),
        "lista_bloqueadas": bloqueadas,
    }
    print(json.dumps(saida, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
