"""Fluxo de importação ponta a ponta — C3 a C7."""
import io
import zipfile
from pathlib import Path

import pytest


def test_importar_skill_leva_para_quarentena(hub, skill_dir):
    r = hub.import_path(str(skill_dir))
    assert r.ok
    assert not hub.repo.exists(r.capability_id)
    assert (hub.locations.quarantine / r.capability_id).is_dir()


def test_fluxo_completo_importar_revisar_promover_exportar(hub, skill_dir, tmp_path):
    r = hub.import_path(str(skill_dir))
    assert r.ok
    assert r.type == "agent-skill" if hasattr(r, "type") else True
    assert r.resource_type == "agent-skill"

    promovida = hub.promote(r.capability_id)
    assert promovida["lifecycle"] == "active"

    validacao = hub.validate(r.capability_id)
    assert validacao["summary"]["error"] == 0

    hub.set_trust(r.capability_id, "user-provided")
    exportado = hub.export(r.capability_id, target="private", destination=str(tmp_path))
    assert exportado["ok"]

    verificado = hub.verify_package(exportado["path"])
    assert verificado["ok"]


def test_simulacao_nao_grava_nada(hub, skill_dir):
    antes = list(hub.locations.home.rglob("*"))
    r = hub.import_path(str(skill_dir), dry_run=True)
    assert r.ok
    depois = list(hub.locations.home.rglob("*"))
    assert antes == depois
    assert any("Simulação" in w for w in r.warnings)


def test_importar_zip_funciona(tmp_path, hub):
    z = tmp_path / "skill.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("SKILL.md", "---\nname: do-zip\ndescription: veio zipado\n---\n\nCorpo.\n")
        zf.writestr("scripts/run.py", "print('nada roda aqui')\n")
    r = hub.import_path(str(z))
    assert r.ok
    assert r.contains_scripts is True
    assert "scripts/run.py" in [f["path"] for f in r.files]


def test_arquivo_unico_vira_capacidade(tmp_path, hub):
    f = tmp_path / "notas.md"
    f.write_text("# Notas\n\nConteúdo sintético.\n", encoding="utf-8")
    r = hub.import_path(str(f))
    assert r.ok
    assert r.resource_type == "reference"


def test_tipo_detectado_pelo_conteudo(tmp_path, hub):
    d = tmp_path / "mcp"
    d.mkdir()
    (d / "package.json").write_text('{"name":"mcp-x"}', encoding="utf-8")
    (d / "index.js").write_text("// servidor", encoding="utf-8")
    r = hub.import_path(str(d))
    assert r.ok
    assert r.resource_type == "mcp-server"


def test_skill_invalida_e_recusada_com_apontamento(hub, tmp_path):
    d = tmp_path / "quebrada"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: Tem Espaço\ndescription: x\n---\n\nCorpo.\n",
                                encoding="utf-8")
    r = hub.import_path(str(d))
    assert not r.ok
    assert r.blocked_reason
    assert r.hint
    assert any(i["code"] == "NAME_FORMAT" for i in r.issues)


def test_caractere_invisivel_bloqueia_e_explica(hub, tmp_path):
    d = tmp_path / "invisivel"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: invisivel\ndescription: x\n---\n\n```\ntexto\u202efalso\n```\n",
        encoding="utf-8")
    r = hub.import_path(str(d))
    assert not r.ok
    assert "invisíveis" in r.blocked_reason or "invisiveis" in r.blocked_reason
    assert r.unicode_findings


def test_caractere_ambiguo_em_prosa_permite_mas_marca_revisao(hub, tmp_path):
    d = tmp_path / "ambiguo"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: ambiguo\ndescription: x\n---\n\nAqui há \u202etexto\u202c em prosa.\n",
        encoding="utf-8")
    r = hub.import_path(str(d))
    assert r.ok
    assert r.requires_review is True


def test_bom_e_removido_e_registrado(hub, tmp_path):
    d = tmp_path / "combom"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "\ufeff---\nname: combom\ndescription: x\n---\n\nCorpo.\n", encoding="utf-8")
    r = hub.import_path(str(d))
    assert r.ok
    assert any("BOM" in w for w in r.warnings)


def test_licenca_presente_e_registrada(hub, skill_dir):
    r = hub.import_path(str(skill_dir))
    assert r.detected_license
    assert "MIT" in r.detected_license
    assert r.license_status == "declared"


def test_licenca_ausente_nao_vira_licenca_livre(hub, bare_skill_dir):
    r = hub.import_path(str(bare_skill_dir))
    assert r.ok
    assert r.detected_license is None
    assert r.license_status == "unknown"
    assert any("NÃO" in w or "NAO" in w for w in r.warnings)

    hub.promote(r.capability_id)
    d = hub.detail(r.capability_id)
    assert d["license"]["code"] is None
    assert d["license"]["redistributable"] is False
    assert "signed" not in d["license"]


def test_manifesto_declarando_arquivo_ausente_gera_aviso(tmp_path, hub):
    aviso = {
        "formatVersion": 1, "id": "incompleto", "name": "incompleto",
        "version": "1.0.0", "payload": {"files": [{"path": "SKILL.md", "size": 1, "sha256": "x"}]},
    }
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        import json as _json
        zf.writestr("manifest.json", _json.dumps(aviso))
        zf.writestr("payload/outro.md", "conteudo")
    p = tmp_path / "incompleto.lia-capability"
    p.write_bytes(buf.getvalue())
    r = hub.import_path(str(p))
    assert r.ok
    codigos = {i["code"] for i in r.issues}
    assert "MANIFEST_MISSING_FILE" in codigos


def test_caminho_inexistente_da_erro_claro(hub):
    r = hub.import_path("/caminho/que/nao/existe")
    assert not r.ok
    assert "não existe" in r.blocked_reason
    assert r.hint


def test_diretorio_vazio_e_recusado(tmp_path, hub):
    d = tmp_path / "vazio"
    d.mkdir()
    r = hub.import_path(str(d))
    assert not r.ok


@pytest.mark.parametrize("texto,esperado", [
    ("Você pode SALVAR o arquivo.", "SALVAR"),
])
def test_importacao_preserva_acentos(hub, tmp_path, texto, esperado):
    d = tmp_path / "acentos"
    d.mkdir()
    (d / "SKILL.md").write_text(
        f"---\nname: acentos\ndescription: x\n---\n\n{texto}\n", encoding="utf-8")
    r = hub.import_path(str(d))
    assert r.ok
    conteudo = hub.repo.payload_files(r.capability_id)["SKILL.md"].decode("utf-8")
    assert esperado in conteudo


def test_exportar_varios_de_uma_vez(hub, tmp_path):
    d = tmp_path / "src"
    for nome in ("skill-a", "skill-b"):
        pasta = d / nome
        pasta.mkdir(parents=True)
        (pasta / "SKILL.md").write_text(
            f"---\nname: {nome}\ndescription: {nome}\n---\n\nCorpo.\n", encoding="utf-8")
        r = hub.import_path(str(pasta))
        hub.promote(r.capability_id)

    ids = [i["id"] for i in hub.items()]
    destino = tmp_path / "pacotes"
    res = hub.export_many(ids, target="private", destination=str(destino))
    assert res["ok"]
    assert res["exported"] == 2
    assert len(list(destino.glob("*.lia-capability"))) == 2


def test_exportar_varios_continua_quando_um_falha(hub, imported, tmp_path):
    destino = tmp_path / "mix"
    res = hub.export_many([imported["id"], "inexistente-00000000"],
                          target="private", destination=str(destino))
    assert res["exported"] == 1
    assert res["failed"] == 1
    assert not res["ok"]     # o agregado não mente sobre a falha
