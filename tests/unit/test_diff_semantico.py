"""M6 — diff entre versões precisa mostrar O QUE mudou, não só que mudou.

O critério de aceite do MVP (`MVP-AND-ROADMAP.md` §3.1, M6) pede:
"Duas versões da mesma Skill → diff de corpo, `description` e
`declaredPermissions`". Um diff que só lista nomes de arquivo cumpre a forma
e falha o espírito: `allowed-tools` mudando não altera nome de arquivo algum.
"""
from __future__ import annotations

import pytest

from lia_agenthub.domain.skills import diff_corpo, diff_frontmatter


def _skill(desc="d", corpo="Corpo.", extra=""):
    return f"---\nname: alvo\ndescription: {desc}\n{extra}---\n\n{corpo}\n"


class TestDiffFrontmatter:
    def test_description_alterada_aparece(self):
        d = diff_frontmatter(_skill("Antiga"), _skill("Nova"))
        assert d["description"] == {"a": "Antiga", "b": "Nova"}

    def test_allowed_tools_alterado_aparece(self):
        """O caso que motiva o diff semântico: mesmo arquivo, outro contrato."""
        a = _skill(extra="allowed-tools: []\n")
        b = _skill(extra="allowed-tools: [Bash, Read]\n")
        d = diff_frontmatter(a, b)
        assert "allowed-tools" in d
        assert d["allowed-tools"]["b"] == "[Bash, Read]"

    def test_campo_ausente_vira_none_e_nao_string_vazia(self):
        a = _skill()
        b = _skill(extra="license: MIT\n")
        d = diff_frontmatter(a, b)
        assert d["license"] == {"a": None, "b": "MIT"}

    def test_sem_mudanca_retorna_vazio(self):
        assert diff_frontmatter(_skill(), _skill()) == {}

    def test_espaco_em_branco_nao_conta_como_mudanca(self):
        """Reformatar a descrição não é mudar o contrato."""
        a = "---\nname: alvo\ndescription: texto longo aqui\n---\n\nC\n"
        b = "---\nname: alvo\ndescription:   texto   longo aqui\n---\n\nC\n"
        assert diff_frontmatter(a, b) == {}

    def test_metadata_version_detectada(self):
        a = _skill(extra="metadata:\n  version: 1.0.0\n")
        b = _skill(extra="metadata:\n  version: 2.0.0\n")
        d = diff_frontmatter(a, b)
        assert d["metadata.version"] == {"a": "1.0.0", "b": "2.0.0"}

    def test_campo_desconhecido_trocado_nao_passa_silencioso(self):
        """Ignorar campo fora da lista fixa faria "nada mudou" ser mentira."""
        a = _skill(extra="x-campo: um\n")
        b = _skill(extra="x-campo: dois\n")
        assert "x-campo" in diff_frontmatter(a, b)

    def test_ambos_sem_frontmatter_nao_quebra(self):
        assert diff_frontmatter("sem fm", "outro sem fm") == {}

    def test_um_lado_sem_frontmatter_nao_quebra(self):
        d = diff_frontmatter("sem fm", _skill())
        assert isinstance(d, dict)


class TestDiffCorpo:
    def test_conta_adicionadas_e_removidas(self):
        a = _skill(corpo="linha um\nlinha dois")
        b = _skill(corpo="linha um\nlinha tres")
        d = diff_corpo(a, b)
        assert d["alterado"] is True
        assert d["adicionadas"] == 1
        assert d["removidas"] == 1

    def test_aponta_primeira_diferenca(self):
        a = _skill(corpo="igual\nantigo")
        b = _skill(corpo="igual\nnovo")
        assert diff_corpo(a, b)["primeiraDiferenca"] == 2

    def test_corpo_identico_nao_marca_alterado(self):
        a = _skill(corpo="mesmo")
        assert diff_corpo(a, _skill(corpo="mesmo"))["alterado"] is False

    def test_corpo_grande_omite_detalhe_em_vez_de_despejar(self):
        grande_a = "\n".join(f"l{i}" for i in range(500))
        grande_b = "\n".join(f"m{i}" for i in range(500))
        d = diff_corpo(_skill(corpo=grande_a), _skill(corpo=grande_b))
        assert d["alterado"] is True
        assert "detalheOmitido" in d
        assert "primeiraDiferenca" not in d

    def test_body_vazio_nos_dois_lados(self):
        assert diff_corpo("", "") == {}

    def test_frontmatter_nao_conta_como_corpo(self):
        """Mudar só a description não deve inflar a contagem do corpo."""
        a = _skill("um", "igual")
        b = _skill("dois", "igual")
        assert diff_corpo(a, b)["alterado"] is False


class TestDiffViaHub:
    def test_criterio_de_aceite_m6_completo(self, hub, tmp_path):
        """Diff de corpo + description + declaredPermissions, de ponta a ponta."""
        v1 = tmp_path / "v1"
        v1.mkdir()
        (v1 / "SKILL.md").write_text(
            "---\nname: evoluindo\ndescription: descreve A\n"
            "allowed-tools: []\n---\n\nCorpo antigo.\n", encoding="utf-8")
        r1 = hub.import_path(str(v1))
        hub.promote(r1.capability_id)

        v2 = tmp_path / "v2"
        v2.mkdir()
        (v2 / "SKILL.md").write_text(
            "---\nname: evoluindo\ndescription: descreve B\n"
            "allowed-tools: [Bash]\n---\n\nCorpo novo.\n", encoding="utf-8")
        upd = hub.update_capability(r1.capability_id, str(v2))

        d = hub.diff_versions(r1.capability_id, upd["id"])
        assert d["frontmatter"]["description"] == {"a": "descreve A", "b": "descreve B"}
        assert "allowed-tools" in d["frontmatter"]
        assert d["corpo"]["alterado"] is True
        assert "SKILL.md" in d["changed"]
        assert d["identical"] is False

    def test_mcp_server_nao_inventa_diff_semantico(self, hub, tmp_path):
        """Sem SKILL.md, `frontmatter` é vazio — e não "nada mudou"."""
        import json
        d1 = tmp_path / "m1"
        d1.mkdir()
        (d1 / "mcp.json").write_text(json.dumps({"endpoint": "https://a.example/mcp"}),
                                     encoding="utf-8")
        r1 = hub.import_path(str(d1))
        d2 = tmp_path / "m2"
        d2.mkdir()
        (d2 / "mcp.json").write_text(json.dumps({"endpoint": "https://b.example/mcp"}),
                                     encoding="utf-8")
        r2 = hub.import_path(str(d2))
        diff = hub.diff_versions(r1.capability_id, r2.capability_id)
        assert diff["frontmatter"] == {}
        assert diff["corpo"] == {}
        assert "mcp.json" in diff["changed"]
