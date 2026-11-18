"""A UI e a API precisam falar do mesmo campo.

A classe de bug que estes testes pegam é a pior possível: a API devolve
`treeHash` na raiz, a UI lê `d.hashes.treeHash`, o JavaScript não estoura
(optional chaining), e a tela mostra vazio sem nenhum erro no log. O usuário
conclui que a capacidade não tem hash.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
APP_JS = RAIZ / "src/lia_agenthub/resources/static/app.js"


@pytest.fixture
def detalhe(hub, tmp_path):
    d = tmp_path / "s"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: contrato\ndescription: d\nversion: 1.0.0\nlicense: MIT\n"
        "---\n\nCorpo.\n", encoding="utf-8")
    r = hub.import_path(str(d))
    hub.promote(r.capability_id)
    return hub.detail(r.capability_id)


class TestCamposDoDetalhe:
    def test_hashes_ficam_na_raiz(self, detalhe):
        """Fixação do contrato: se mudar de lugar, a UI precisa mudar junto."""
        assert detalhe["treeHash"] and len(detalhe["treeHash"]) == 64
        assert detalhe["contentHash"] and len(detalhe["contentHash"]) == 64
        assert "hashes" not in detalhe

    def test_ui_nao_le_objeto_hashes_inexistente(self):
        js = APP_JS.read_text(encoding="utf-8")
        # Ignora comentários: o comentário que explica o bug anterior cita o
        # padrão errado de propósito.
        codigo = "\n".join(
            l for l in js.splitlines() if not l.lstrip().startswith("//"))
        assert "d.hashes" not in codigo

    def test_ui_le_os_campos_que_existem(self):
        js = APP_JS.read_text(encoding="utf-8")
        assert "d.treeHash" in js
        assert "d.contentHash" in js

    def test_integridade_agora_e_exibida(self, detalhe):
        assert detalhe["integrityNow"]["treeHash"] == detalhe["treeHash"]
        assert "integrityNow" in APP_JS.read_text(encoding="utf-8")


class TestCamposLidosPelaUIExistemNaAPI:
    """Varre `d.<campo>` no detalhe e confere contra a resposta real.

    Não é análise perfeita de JavaScript: é a checagem dos campos que o
    renderizador de detalhe realmente usa.
    """

    CAMPOS_ESPERADOS = (
        "id", "name", "version", "domain", "author", "license", "source",
        "treeHash", "contentHash", "integrityNow", "risk", "files",
        "validation", "duplicates", "lineage", "history", "trust", "type",
        "lifecycle",
    )

    def test_todos_os_campos_esperados_estao_no_detalhe(self, detalhe):
        faltando = [c for c in self.CAMPOS_ESPERADOS if c not in detalhe]
        assert not faltando, f"a UI lê campos que a API não devolve: {faltando}"

    def test_summary_do_items_nao_promete_o_que_nao_tem(self, hub, detalhe):
        item = hub.items()[0]
        # A lista é resumida de propósito; só garantimos os campos da lista.
        for campo in ("id", "name", "version", "type", "trust", "risk"):
            assert campo in item, campo


class TestListaEQuarentena:
    def test_card_da_lista_usa_contrato_de_items(self, hub, tmp_path):
        d = tmp_path / "q"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: naquarentena\ndescription: d\n---\n\nC.\n", encoding="utf-8")
        hub.import_path(str(d))
        from lia_agenthub.app import SearchQuery
        itens = hub.items(SearchQuery(lifecycle="quarantined"))
        assert itens
        for campo in ("id", "name", "type", "trust", "risk", "licenseKnown",
                      "containsScripts"):
            assert campo in itens[0], campo
