#!/usr/bin/env python3
"""Gera os registros de catálogo do Google Stitch usando o Hub REAL.

Por que este script existe em vez de um JSON escrito à mão
    Um catálogo escrito à mão é uma afirmação. Este roda o importador de
    produção num Hub temporário e grava o que ele de fato produziu. Se o
    importador mudar, o catálogo muda junto — e a divergência aparece no
    diff em vez de virar documentação de algo que não acontece mais.

O que ele faz
    - Importa, para um Hub TEMPORÁRIO, o descritor MCP e as 16 Skills
      oficiais de google-labs-code/stitch-skills.
    - Grava `<Biblioteca>/<id>/.lia/capability.json` como `capability` e a
      procedência ao lado, no formato nativo do Hub.
    - Preserva hash, licença, namespace, egress e o descritor MCP.

O que ele NÃO faz
    - Não copia o payload de terceiros para dentro deste repositório.
    - Não conecta no MCP, não autentica, não executa Skill alguma.
    - Não promove nada para a biblioteca do usuário.

Uso
    git clone --depth 200 https://github.com/google-labs-code/stitch-skills /tmp/stitch/repo
    PYTHONPATH=src .venv/bin/python docs/stitch/tools/build-stitch-catalog.py \
        --repo /tmp/stitch/repo --out docs/stitch/catalog
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import shutil
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "src"))

from lia_agenthub.adapters.paths_resolver import resolve_locations  # noqa: E402
from lia_agenthub.app import AgentHub  # noqa: E402

REPO_OFICIAL = "https://github.com/google-labs-code/stitch-skills"


def commit_do_repo(repo: Path) -> str:
    import subprocess

    try:
        return subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return ""


def registro(hub: AgentHub, cap_id: str, origem: str) -> dict:
    """Monta o registro no formato nativo: capability + provenance."""
    det = hub.detail(cap_id)
    # `detail()` acrescenta visão de UI (risk, files, lineage). O registro
    # persistido é só o que vive em capability.json.
    from lia_agenthub.domain.model import Capability

    cap = hub.repo._load_any(cap_id).capability
    return {
        "capability": json.loads(cap.to_json()),
        "provenance": {
            "upstream": origem,
            "upstreamRepo": REPO_OFICIAL,
            "origin": "official",
            "originNote": ("Publicado por google-labs-code. Não é conteúdo de "
                           "projeto Lia; a licença é do repositório de origem."),
            "hashes": {"contentHash": det["contentHash"],
                       "treeHash": det["treeHash"]},
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="clone de stitch-skills")
    ap.add_argument("--out", default=str(RAIZ / "docs/stitch/catalog"))
    ap.add_argument("--mcp-descriptor",
                    default=str(RAIZ / "docs/stitch/mcp/google-stitch.mcp.json"))
    args = ap.parse_args()

    repo = Path(args.repo).resolve()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    commit = commit_do_repo(repo)

    temporario = Path(tempfile.mkdtemp())
    hub = AgentHub(resolve_locations(temporario / "hub"))
    registros: list[dict] = []
    falhas: list[dict] = []

    # ---- 1. descritor MCP (serviço remoto) ------------------------------
    mcp_src = Path(args.mcp_descriptor)
    if mcp_src.is_file():
        pacote = temporario / "mcp-pacote"
        pacote.mkdir(parents=True, exist_ok=True)
        shutil.copy(mcp_src, pacote / "mcp.json")
        r = hub.import_path(str(pacote))
        if r.ok:
            reg = registro(hub, r.capability_id, "Google Stitch (descritor do Hub)")
            reg["provenance"]["documentedFrom"] = (
                "https://stitch.google.com/docs/mcp/setup")
            reg["provenance"]["connectivityVerified"] = False
            # O nome local do descritor é o do arquivo; renomeia para o
            # rótulo público que o catálogo usa.
            reg["capability"]["name"] = "google-stitch-mcp"
            reg["capability"]["description"] = (
                "Servidor MCP remoto do Google Stitch: gera e edita telas, "
                "gerencia design systems e projetos de UI/UX. O Hub registra "
                "endpoint e fluxo de autenticação; a conexão é do host.")
            reg["capability"]["license"] = {
                "code": None, "content": None, "notice_required": False,
                "redistributable": False, "redistribution_basis": None,
                "status": "unknown", "weights": None,
                "extra": {}}
            reg["provenance"]["licenseNote"] = (
                "O serviço é regido pelos Google APIs Terms of Service. Não há "
                "licença de redistribuição de conteúdo associada: o que o Hub "
                "distribui é a CONFIGURAÇÃO, não o serviço.")
            registros.append(reg)
        else:
            falhas.append({"item": "google-stitch-mcp",
                           "motivo": r.blocked_reason})

    # ---- 2. as 16 Skills oficiais ---------------------------------------
    skills = sorted((repo / "plugins").rglob("SKILL.md"))
    for sk in skills:
        pasta = sk.parent
        plugin = pasta.parent.parent.name
        origem = (f"google-labs-code/stitch-skills@"
                  f"{commit[:7]}:plugins/{plugin}/skills/{pasta.name}")
        r = hub.import_path(str(pasta))
        if not r.ok:
            falhas.append({"item": pasta.name, "motivo": r.blocked_reason})
            continue
        reg = registro(hub, r.capability_id, origem)
        reg["provenance"]["plugin"] = plugin
        reg["provenance"]["origin"] = "official"
        # Licença: o repositório é Apache-2.0 no LICENSE da raiz. Nenhuma
        # Skill declara licença no próprio frontmatter — deixar `unknown`
        # seria dizer "não sei" quando o repositório responde.
        reg["provenance"]["licenseEvidence"] = {
            "kind": "repository-root-LICENSE",
            "path": "LICENSE",
            "spdx": "Apache-2.0",
            "note": ("As 16 SKILL.md não trazem campo `license`. A licença é "
                     "declarada no LICENSE da raiz do repositório de origem; "
                     "registrada como declaração do upstream, não como "
                     "permissão verificada pelo Hub."),
        }
        registros.append(reg)

    registros.sort(key=lambda x: x["capability"]["name"])
    saida = {
        "generator": "docs/stitch/tools/build-stitch-catalog.py (Hub real)",
        "schemaNote": ("Registros produzidos pelo importador de produção do "
                       "Lia Agent Hub em Hub temporário. Nenhum payload de "
                       "terceiros é copiado para este repositório."),
        "generatedAt": _dt.datetime.now(_dt.timezone.utc).isoformat(
            timespec="seconds"),
        "source": {
            "repo": REPO_OFICIAL,
            "commit": commit,
            "mcpDocs": "https://stitch.google.com/docs/mcp/setup",
            "mcpEndpoint": "https://stitch.googleapis.com/mcp",
        },
        "recordCount": len(registros),
        "failures": falhas,
        "records": registros,
    }
    alvo = out / "google-stitch.records.json"
    alvo.write_text(json.dumps(saida, ensure_ascii=False, indent=2,
                               sort_keys=True), encoding="utf-8")
    print(f"gravado {alvo.name}: {len(registros)} registros, "
          f"{len(falhas)} falhas")
    for f in falhas:
        print(f"  FALHA {f['item']}: {f['motivo']}")
    shutil.rmtree(temporario, ignore_errors=True)
    return 0 if not falhas else 1


if __name__ == "__main__":
    raise SystemExit(main())
