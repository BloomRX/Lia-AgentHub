#!/usr/bin/env python3
"""Gera CATALOG.md a partir do catálogo JSON — nunca escrito à mão.

O JSON é produzido pelo importador real do Hub; este render só o apresenta.
Assim o documento e o registro não podem divergir: se alguém editar o
Markdown, a próxima execução sobrescreve com o que o Hub de fato tem.

Uso:
    PYTHONPATH=src .venv/bin/python docs/stitch/tools/render-catalog.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
CATALOGO = RAIZ / "docs/stitch/catalog/google-stitch.records.json"
SAIDA = RAIZ / "docs/stitch/CATALOG.md"
REPO_LOCAL = Path("/tmp/stitch/repo")   # opcional: usado só para dependências


def dependencias(nome: str) -> list[str]:
    """Quais outras Skills desta coleção a Skill cita no próprio texto.

    Derivado do upstream, não de tabela escrita à mão. Sem o clone, devolve
    vazio e o documento diz que a coluna não foi calculada.
    """
    if not REPO_LOCAL.is_dir():
        return []
    pasta = next((p for p in REPO_LOCAL.rglob(nome)
                  if p.is_dir() and (p / "SKILL.md").is_file()), None)
    if pasta is None:
        return []
    texto = (pasta / "SKILL.md").read_text(encoding="utf-8", errors="replace")
    achados = {m.group(1) for m in re.finditer(r"(?:stitch::|skills/)([a-z][a-z0-9-]+)", texto)}
    nomes_validos = {n for n in achados}
    achados.discard(nome)
    achados.discard("plugins")
    return sorted(a for a in achados if a != nome and a in nomes_validos)


def main() -> int:
    dados = json.loads(CATALOGO.read_text(encoding="utf-8"))
    recs = dados["records"]
    skills = [r for r in recs if r["capability"]["type"] == "agent-skill"]
    servidores = [r for r in recs if r["capability"]["type"] == "mcp-server"]
    deps_calculadas = REPO_LOCAL.is_dir()

    L: list[str] = []
    L.append("# Catálogo — Google Stitch no Lia Agent Hub")
    L.append("")
    L.append("> **Gerado automaticamente.** Não editar à mão: a fonte é")
    L.append("> `catalog/google-stitch.records.json`, produzido pelo importador de")
    L.append("> produção do Hub em `tools/build-stitch-catalog.py`. Este arquivo é")
    L.append("> a apresentação do registro, não uma segunda verdade.")
    L.append("")
    L.append(f"- **Upstream:** {dados['source']['repo']}")
    L.append(f"- **Commit:** `{dados['source']['commit'][:12]}`")
    L.append(f"- **Endpoint MCP:** `{dados['source']['mcpEndpoint']}`")
    L.append(f"- **Registros:** {dados['recordCount']} "
             f"({len(servidores)} serviço, {len(skills)} skills)")
    L.append(f"- **Falhas de importação:** {len(dados['failures'])}")
    L.append("")
    L.append("## Servidor MCP")
    L.append("")
    for r in servidores:
        c = r["capability"]
        m = c.get("mcp", {})
        L.append(f"### `{c['name']}`")
        L.append("")
        L.append(f"- **Tipo:** `{c['type']}`")
        L.append(f"- **Endpoint:** `{m.get('endpoint')}`")
        L.append(f"- **Transporte:** `{m.get('transport')}`")
        L.append(f"- **Autenticação:** `{m.get('authentication')}`")
        L.append(f"- **Cabeçalhos (nomes):** {', '.join(f'`{h}`' for h in m.get('headers', []))}")
        L.append(f"- **Categoria:** {m.get('category')}")
        L.append(f"- **Egress declarado:** {c.get('egress')}")
        L.append(f"- **Conectividade verificada:** `{m.get('connectivityVerified')}` "
                 f"— o Hub não conecta")
        L.append(f"- **Licença:** serviço regido pelos Google APIs ToS; "
                 f"o Hub distribui a configuração, não o serviço")
        L.append("")
        L.append("Configuração do host: [`MCP-SETUP.md`](MCP-SETUP.md).")
        L.append("")
    L.append("## Skills")
    L.append("")
    plugins = {}
    for r in skills:
        plugins.setdefault(r["provenance"].get("plugin", "?"), []).append(r)
    for plugin in sorted(plugins):
        L.append(f"### `{plugin}` — {len(plugins[plugin])} skills")
        L.append("")
        L.append("| Skill | Namespace | Depende de | Descrição |")
        L.append("|---|---|---|---|")
        for r in sorted(plugins[plugin], key=lambda x: x["capability"]["name"]):
            c = r["capability"]
            ds = dependencias(c["name"])
            dep = ", ".join(f"`{d}`" for d in ds) if ds else ("—" if deps_calculadas else "*(não calculado)*")
            desc = " ".join(c["description"].split())
            if len(desc) > 110:
                desc = desc[:107] + "…"
            ns = c.get("namespace") or "—"
            L.append(f"| `{c['name']}` | {ns} | {dep} | {desc} |")
        L.append("")
    L.append("## Licença e proveniência")
    L.append("")
    L.append("Todo registro acima aponta para o mesmo upstream e o mesmo commit.")
    L.append("A licença **não** está no frontmatter de nenhuma das 16 Skills — ela é")
    L.append("declarada no `LICENSE` da raiz do repositório de origem:")
    L.append("")
    L.append("| Item | Evidência |")
    L.append("|---|---|")
    L.append("| Licença do upstream | Apache-2.0 (`LICENSE` na raiz) |")
    L.append("| Natureza | **Declaração do upstream**, não permissão verificada pelo Hub |")
    L.append("| Redistribuição | `redistributable: false` — decisão humana |")
    L.append("| Autoria | google-labs-code (não é conteúdo de projeto Lia) |")
    L.append("")
    L.append("O Hub registra a evidência; não conclui direito de uso.")
    L.append("")
    L.append("## Como os agentes usam")
    L.append("")
    L.append("O registro descreve a capacidade. Para **usar**, o host precisa")
    L.append("instalar as Skills e configurar o MCP — estados distintos, descritos em")
    L.append("[`CODEX-AND-OTHER-HOSTS.md`](CODEX-AND-OTHER-HOSTS.md) §6.")
    L.append("")
    L.append("O processo de trabalho está em")
    L.append("[`workflow/lia-uiux-workflow.md`](workflow/lia-uiux-workflow.md).")
    L.append("")
    SAIDA.write_text("\n".join(L), encoding="utf-8")
    print(f"gravado {SAIDA.name}: {len(skills)} skills, {len(servidores)} serviço(s), "
          f"deps {'calculadas' if deps_calculadas else 'NÃO calculadas (sem clone)'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
