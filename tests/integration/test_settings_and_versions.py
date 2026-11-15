"""Configurações e versionamento — C1 (config) e C6 (histórico de versões)."""
import json
from pathlib import Path

import pytest


# ---------------- configurações ----------------
def test_padroes_de_configuracao(hub):
    s = hub.settings()
    assert s["default_export_target"] == "private"
    assert s["confirm_discard"] is True
    assert s["prefer_browser"] is False


def test_salvar_e_reler_configuracao(hub, locations):
    hub.save_settings({"prefer_browser": True, "default_export_target": "shared"})
    s = hub.settings()
    assert s["prefer_browser"] is True
    assert s["default_export_target"] == "shared"

    from lia_agenthub.adapters.paths_resolver import resolve_locations
    from lia_agenthub.app import AgentHub
    outra = AgentHub(resolve_locations(locations.home))
    assert outra.settings()["prefer_browser"] is True


def test_valor_invalido_volta_ao_padrao(hub):
    hub.save_settings({"default_export_target": "qualquer-coisa"})
    assert hub.settings()["default_export_target"] == "private"


def test_configuracao_nao_aceita_campo_desconhecido(hub):
    hub.save_settings({"chave_inventada": "x", "prefer_browser": True})
    assert "chave_inventada" not in hub.settings()
    assert hub.settings()["prefer_browser"] is True


def test_resetar_configuracao(hub):
    hub.save_settings({"prefer_browser": True})
    hub.reset_settings()
    assert hub.settings()["prefer_browser"] is False


def test_arquivo_de_configuracao_nao_guarda_segredo(hub):
    hub.save_settings({"prefer_browser": True})
    texto = (hub.locations.config / "settings.json").read_text()
    baixo = texto.lower()
    for proibido in ("password", "senha", "token", "secret", "api_key"):
        assert proibido not in baixo


def test_configuracao_corrompida_nao_derruba_o_app(hub):
    caminho = hub.locations.config / "settings.json"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("{lixo", encoding="utf-8")
    assert hub.settings()["default_export_target"] == "private"


# ---------------- versionamento ----------------
def _skill(pasta: Path, nome: str, versao: str, descricao: str, corpo: str = "Corpo."):
    pasta.mkdir(parents=True, exist_ok=True)
    (pasta / "SKILL.md").write_text(
        f"---\nname: {nome}\ndescription: {descricao}\nversion: {versao}\n---\n\n{corpo}\n",
        encoding="utf-8")
    return pasta


def test_versao_vem_do_frontmatter(hub, tmp_path):
    r = hub.import_path(str(_skill(tmp_path / "v", "com-versao", "3.2.1", "d")))
    assert r.ok
    item = hub.promote(r.capability_id)
    assert item["version"] == "3.2.1"


def test_sem_versao_declarada_usa_padrao(hub, tmp_path):
    d = tmp_path / "sem"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: sem-ver\ndescription: d\n---\n\nCorpo.\n",
                                encoding="utf-8")
    r = hub.import_path(str(d))
    assert hub.promote(r.capability_id)["version"] == "0.1.0"


def test_atualizar_preserva_a_versao_anterior(hub, tmp_path):
    v1 = hub.import_path(str(_skill(tmp_path / "v1", "evolutiva", "1.0.0", "primeira")))
    hub.promote(v1.capability_id)

    v2dir = _skill(tmp_path / "v2", "evolutiva", "2.0.0", "segunda", corpo="Novo corpo.")
    u = hub.update_capability(v1.capability_id, str(v2dir))
    assert u["ok"]
    assert u["item"]["version"] == "2.0.0"

    # a anterior continua no disco
    antiga = hub.repo._load_any(v1.capability_id).capability
    assert antiga.lifecycle.value == "superseded"
    assert (hub.locations.library / v1.capability_id / "payload" / "SKILL.md").is_file()


def test_linhagem_lista_as_duas_versoes(hub, tmp_path):
    v1 = hub.import_path(str(_skill(tmp_path / "a", "linha", "1.0.0", "a")))
    hub.promote(v1.capability_id)
    u = hub.update_capability(v1.capability_id,
                              str(_skill(tmp_path / "b", "linha", "2.0.0", "b")))
    cadeia = hub.lineage(u["id"])
    versoes = {x["version"] for x in cadeia}
    assert {"1.0.0", "2.0.0"} <= versoes
    assert cadeia[0]["version"] == "2.0.0"


def test_versao_superada_sai_da_estante_principal(hub, tmp_path):
    v1 = hub.import_path(str(_skill(tmp_path / "c", "estante", "1.0.0", "a")))
    hub.promote(v1.capability_id)
    hub.update_capability(v1.capability_id,
                          str(_skill(tmp_path / "d", "estante", "2.0.0", "b")))
    versoes = [i["version"] for i in hub.items()]
    assert versoes == ["2.0.0"]


def test_versao_superada_continua_consultavel(hub, tmp_path):
    v1 = hub.import_path(str(_skill(tmp_path / "e", "consulta", "1.0.0", "a")))
    hub.promote(v1.capability_id)
    hub.update_capability(v1.capability_id,
                          str(_skill(tmp_path / "f", "consulta", "2.0.0", "b")))
    d = hub.detail(v1.capability_id)
    assert d["lifecycle"] == "superseded"
    assert d["files"]


def test_atualizar_com_conteudo_identico_nao_faz_nada(hub, tmp_path):
    d = _skill(tmp_path / "g", "igual", "1.0.0", "a")
    v1 = hub.import_path(str(d))
    hub.promote(v1.capability_id)
    u = hub.update_capability(v1.capability_id, str(d))
    assert not u["ok"]
    assert "idêntico" in u["reason"]
    assert len(hub.items()) == 1


def test_atualizar_com_entrada_invalida_falha_limpo(hub, imported, tmp_path):
    u = hub.update_capability(imported["id"], str(tmp_path / "nao-existe"))
    assert not u["ok"]
    assert u["reason"]
    assert hub.detail(imported["id"])["lifecycle"] == "active"


def test_atualizar_republica_o_indice(hub, tmp_path):
    v1 = hub.import_path(str(_skill(tmp_path / "h", "indexada", "1.0.0", "a")))
    hub.promote(v1.capability_id)
    hub.update_capability(v1.capability_id,
                          str(_skill(tmp_path / "i", "indexada", "2.0.0", "b")))
    idx = hub.read_index()
    assert idx is not None
    versoes = [c["version"] for c in idx["capabilities"]]
    assert "2.0.0" in versoes
    assert "1.0.0" not in versoes


def test_diferenca_entre_versoes_mostra_o_que_mudou(hub, tmp_path):
    v1 = hub.import_path(str(_skill(tmp_path / "j", "diffavel", "1.0.0", "a", "Antigo.")))
    hub.promote(v1.capability_id)
    v2dir = _skill(tmp_path / "k", "diffavel", "2.0.0", "b", "Novo e diferente.")
    (v2dir / "extra.md").write_text("arquivo novo", encoding="utf-8")
    u = hub.update_capability(v1.capability_id, str(v2dir))
    d = hub.diff_versions(v1.capability_id, u["id"])
    assert "SKILL.md" in d["changed"]
    assert "extra.md" in d["onlyInB"]
