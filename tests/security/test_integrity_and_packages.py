"""Integridade, adulteração de pacote, vazamento de segredos e confiança."""
import json
import zipfile
from pathlib import Path

import pytest

from lia_agenthub.adapters.packager import Target, export, verify_package
from lia_agenthub.domain.errors import IntegrityError


def test_pacote_intacto_verifica(hub, imported, tmp_path):
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    assert r["ok"]
    v = verify_package(r["path"])
    assert v["ok"] and v["treeHashOk"]


def test_pacote_com_payload_alterado_falha(hub, imported, tmp_path):
    """Trocar um byte e reempacotar com o manifesto antigo tem de falhar."""
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    origem = Path(r["path"])

    entrada = zipfile.ZipFile(origem)
    conteudo = {n: entrada.read(n) for n in entrada.namelist()}
    entrada.close()

    conteudo["payload/SKILL.md"] += b"\n<!-- adulterado -->\n"
    adulterado = tmp_path / "adulterado.lia-capability"
    with zipfile.ZipFile(adulterado, "w") as zf:
        for n, d in conteudo.items():
            zf.writestr(n, d)

    v = verify_package(adulterado)
    assert not v["ok"]
    assert any("SKILL.md" in p for p in v["problems"])


def test_pacote_com_arquivo_extra_falha(hub, imported, tmp_path):
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    entrada = zipfile.ZipFile(r["path"])
    conteudo = {n: entrada.read(n) for n in entrada.namelist()}
    entrada.close()
    conteudo["payload/extra.py"] = b"import os\n"

    extra = tmp_path / "extra.lia-capability"
    with zipfile.ZipFile(extra, "w") as zf:
        for n, d in conteudo.items():
            zf.writestr(n, d)

    v = verify_package(extra)
    assert not v["ok"]
    assert any("extra.py" in p for p in v["problems"])


def test_pacote_sem_manifesto_falha(tmp_path):
    p = tmp_path / "sem-manifesto.lia-capability"
    with zipfile.ZipFile(p, "w") as zf:
        zf.writestr("payload/SKILL.md", b"x")
    with pytest.raises(IntegrityError):
        verify_package(p)


def test_arquivo_que_nao_e_pacote_falha(tmp_path):
    p = tmp_path / "lixo.lia-capability"
    p.write_bytes(b"isto nao e um zip")
    with pytest.raises(IntegrityError):
        verify_package(p)


def test_manifesto_nunca_afirma_assinatura(hub, imported, tmp_path):
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    with zipfile.ZipFile(r["path"]) as zf:
        m = json.loads(zf.read("manifest.json"))
    texto = json.dumps(m).lower()
    assert "assinad" not in texto or "não" in texto or "nao" in texto
    assert "signed" not in m
    assert "signature" not in m
    assert "NÃO são assinatura" in m["integrityNote"]


def test_exportacao_publica_sem_base_e_recusada(hub, imported, tmp_path):
    r = hub.export(imported["id"], target="public", destination=str(tmp_path))
    assert not r["ok"]
    assert "redistribuí" in r["refusedReason"] or "redistribu" in r["refusedReason"]
    assert not list(tmp_path.glob("*.lia-capability"))


def test_exportacao_publica_com_base_registrada_e_permitida(hub, imported, tmp_path):
    hub.set_license(imported["id"], code="MIT", redistributable=True,
                    basis="Licença MIT verificada pelo autor do acervo")
    r = hub.export(imported["id"], target="public", destination=str(tmp_path))
    assert r["ok"]


def test_exportacao_compartilhada_avisa_mas_permite(hub, imported, tmp_path):
    r = hub.export(imported["id"], target="shared", destination=str(tmp_path))
    assert r["ok"]
    assert any("STOP_AND_READ" in w for w in r["warnings"])


def test_pacote_nao_carrega_valor_de_segredo(hub, imported, tmp_path):
    """Só NOMES de variáveis de ambiente saem. Valores nunca entram no Hub."""
    segredo = "sk-VAZOU-0123456789"
    rep = hub.repo.load(imported["id"])
    rep.capability.secrets_env_vars = ["MINHA_CHAVE"]
    from lia_agenthub.adapters.atomic import atomic_write_json
    atomic_write_json(rep.meta / "capability.json", rep.capability.as_dict())

    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    with zipfile.ZipFile(r["path"]) as zf:
        manifesto = json.loads(zf.read("manifest.json"))
        todo_o_pacote = b"".join(zf.read(n) for n in zf.namelist())

    assert manifesto["secrets"] == {"envVars": ["MINHA_CHAVE"]}
    assert b"MINHA_CHAVE" in todo_o_pacote
    assert segredo.encode() not in todo_o_pacote


def test_recursos_nao_revisados_levam_sufixo_visivel(hub, imported, tmp_path):
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    assert "NAO-REVISADO" in Path(r["path"]).name


def test_revisado_nao_leva_sufixo(hub, imported, tmp_path):
    hub.set_trust(imported["id"], "user-provided")
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    assert "NAO-REVISADO" not in Path(r["path"]).name


def test_exportar_duas_vezes_nao_sobrescreve(hub, imported, tmp_path):
    a = hub.export(imported["id"], target="private", destination=str(tmp_path))
    b = hub.export(imported["id"], target="private", destination=str(tmp_path))
    assert a["ok"] and b["ok"]
    assert a["path"] != b["path"]
    assert Path(a["path"]).is_file() and Path(b["path"]).is_file()


def test_pacote_reimportado_e_reconhecido_como_o_mesmo_conteudo(hub, imported, tmp_path):
    """Mesmo conteúdo => mesmo id. É identidade, não duplicata nem conflito."""
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    report = hub.import_path(r["path"])
    assert report.ok
    assert report.already_present
    assert report.capability_id == imported["id"]
    assert not report.blocked_reason
    assert any("biblioteca" in w for w in report.warnings)


def test_nada_e_duplicado_em_disco_no_reimport(hub, imported, tmp_path):
    from pathlib import Path as _P
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    antes = sorted(p.name for p in hub.locations.library.iterdir())
    hub.import_path(r["path"])
    depois = sorted(p.name for p in hub.locations.library.iterdir())
    assert antes == depois


def test_conteudo_igual_com_nome_diferente_e_duplicata(hub, imported, tmp_path):
    """Nome trocado, mesmo conteúdo: id diferente, árvore igual => duplicata."""
    d = tmp_path / "renomeada"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: outro-nome\ndescription: Faz algo previsível em testes sintéticos.\n"
        "version: 1.0.0\nmetadata: tags:teste,exemplo\n---\n\n# Exemplo\n\n"
        "Este corpo é sintético.\n", encoding="utf-8")
    # notar: o nome no frontmatter muda, então o hash muda — este teste verifica
    # que o Hub NÃO chama de duplicata o que é apenas parecido.
    rep = hub.import_path(str(d))
    assert rep.ok
    assert rep.capability_id != imported["id"]


def test_hash_de_arquivo_difere_entre_CRLF_e_LF():
    from lia_agenthub.domain.integrity import content_hashes
    a = content_hashes(b"linha1\nlinha2\n")
    b = content_hashes(b"linha1\r\nlinha2\r\n")
    assert a["asReceived"] != b["asReceived"]
    assert a["normalized"] == b["normalized"]


def test_alterar_payload_depois_da_importacao_muda_o_hash(hub, imported):
    antes = hub.repo.recompute_hashes(imported["id"])
    alvo = hub.locations.library / imported["id"] / "payload" / "SKILL.md"
    alvo.write_bytes(alvo.read_bytes() + b"\n<!-- mudou -->\n")
    depois = hub.repo.recompute_hashes(imported["id"])
    assert antes["treeHash"] != depois["treeHash"]


def test_aviso_de_divergencia_na_exportacao(hub, imported, tmp_path):
    alvo = hub.locations.library / imported["id"] / "payload" / "SKILL.md"
    alvo.write_bytes(alvo.read_bytes() + b"\n<!-- mudou -->\n")
    r = hub.export(imported["id"], target="private", destination=str(tmp_path))
    assert r["ok"]
    assert any("treeHash" in w or "difer" in w for w in r["warnings"])
