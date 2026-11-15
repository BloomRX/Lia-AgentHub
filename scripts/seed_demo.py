#!/usr/bin/env python3
"""Cria dados SINTÉTICOS para a pré-visualização. Nunca executa nada.

Uso: python3 scripts/seed_demo.py [home]
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lia_agenthub.adapters.paths_resolver import resolve_locations  # noqa: E402
from lia_agenthub.app import AgentHub                               # noqa: E402

DEMOS = {
    "resumo-de-contratos/SKILL.md": """---
name: resumo-de-contratos
description: Resume contratos em português, destacando prazos, multas e obrigações.
version: 1.2.0
metadata: tags:juridico,resumo,portugues
---

# Resumo de contratos

Leia o contrato e produza um resumo com três seções: prazos, multas e obrigações.

## Limites

Não substitui análise jurídica. Sempre indique os trechos originais.
""",
    "resumo-de-contratos/LICENSE": "MIT License\n\nCopyright (c) 2026 Pessoa Sintética\n",
    "checklist-de-acessibilidade/SKILL.md": """---
name: checklist-de-acessibilidade
description: Revisa interfaces contra WCAG 2.2 AA e aponta o que falta.
version: 0.4.0
metadata: tags:acessibilidade,wcag,ui
---

# Checklist de acessibilidade

Percorra a interface e marque cada critério WCAG 2.2 AA.

## Saída

Uma tabela com critério, estado e evidência.
""",
    "conversor-de-planilhas/SKILL.md": """---
name: conversor-de-planilhas
description: Converte CSV em JSON e relata linhas inconsistentes.
version: 2.0.1
metadata: tags:dados,csv,json
---

# Conversor de planilhas

Converta o CSV de entrada em JSON.

## Scripts

Use scripts/converter.py. O hub não executa este arquivo.
""",
    "conversor-de-planilhas/scripts/converter.py": "#!/usr/bin/env python3\nimport csv, json, sys\n\ndef main():\n    pass\n\nif __name__ == '__main__':\n    main()\n",
}


def seed(home: Path) -> AgentHub:
    hub = AgentHub(resolve_locations(home))
    with tempfile.TemporaryDirectory() as tmp:
        for rel, body in DEMOS.items():
            pass
        grouped: dict[str, dict[str, str]] = {}
        for rel, body in DEMOS.items():
            folder, _, inner = rel.partition("/")
            grouped.setdefault(folder, {})[inner] = body
        made = []
        for folder, files in grouped.items():
            d = Path(tmp) / folder
            for inner, body in files.items():
                target = d / inner
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(body, encoding="utf-8")
            made.append((folder, d))

        for folder, d in made:
            rep = hub.import_path(str(d))
            if not rep.ok:
                print(f"  ! {folder}: {rep.blocked_reason}")
                continue
            hub.promote(rep.capability_id)
            print(f"  + {folder} → {rep.capability_id}")

        # uma capacidade fica na quarentena de propósito, para mostrar o fluxo
        q = Path(tmp) / "skill-incompleta"
        q.mkdir()
        (q / "SKILL.md").write_text(
            "---\nname:  skill-incompleta\ndescription: Falta ajustar o nome.\n---\n",
            encoding="utf-8")
        rep = hub.import_path(str(q))
        print(f"  ~ quarentena: ok={rep.ok} {rep.capability_id or rep.blocked_reason}")

        # um recurso com caractere invisível, para a UI mostrar o fluxo de revisão
        u = Path(tmp) / "texto-com-marcador"
        u.mkdir()
        (u / "SKILL.md").write_text(
            "---\nname: texto-com-marcador\ndescription: Contém um marcador invisível.\n---\n\n"
            "Corpo normal. Aqui há um texto com \u202eele invertido\u202c de propósito.\n",
            encoding="utf-8")
        rep2 = hub.import_path(str(u))
        if rep2.ok:
            hub.promote(rep2.capability_id)
            print(f"  + texto-com-marcador → {rep2.capability_id} "
                  f"(revisão: {rep2.requires_review})")

        for stored in hub.repo.list_all():
            hub.validate(stored.capability.id)

        idx = hub.publish_index()
        print(f"  índice: {idx['count']} capacidade(s)")
    return hub


if __name__ == "__main__":
    home = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / ".devhome"
    print(f"Semeando dados sintéticos em {home}")
    seed(home)
    print("Pronto. Nada foi executado.")
