"""Contenção de caminho — o Hub nunca escreve fora da área autorizada."""
import os
import zipfile
from pathlib import Path

import pytest

from lia_agenthub.domain.paths import check_relative_path


@pytest.mark.parametrize("mau", [
    "../../etc/passwd",
    "a/../../b",
    "..\\..\\Windows\\System32\\x.dll",
    "/etc/passwd",
    "/",
    "C:\\Windows\\System32\\x.dll",
    "D:/dados",
    "//servidor/compartilhado/x",
    ".git/config",
    ".git./config",
    ".SSH/authorized_keys",
    "aux.md",
    "CON.txt",
    "com1",
    "NUL",
    "arquivo.exe:fluxo",
    "termina_em_ponto.",
    "termina_em_espaco ",
    "nul\x00byte.md",
    "",
    "./",
])
def test_caminhos_perigosos_sao_recusados(mau):
    v = check_relative_path(mau)
    assert not v.ok, f"aceitou caminho perigoso: {mau!r}"
    assert v.message


@pytest.mark.parametrize("bom", [
    "SKILL.md", "scripts/run.py", "a/b/c.md", "docs/LEIAME.txt",
    "assets/imagem-1.png", "scripts/sub/ferramenta.sh",
])
def test_caminhos_normais_sao_aceitos(bom):
    assert check_relative_path(bom).ok


def test_profundidade_excessiva_e_recusada():
    assert not check_relative_path("/".join(["a"] * 40) + "/x.md").ok


def test_nome_longo_demais_e_recusado():
    assert not check_relative_path("x" * 300 + ".md").ok


def test_zip_com_traversal_nao_grava_nada_fora(tmp_path, hub):
    """Um ZIP malicioso não deve criar arquivo algum fora da área autorizada."""
    alvo = tmp_path / "INVADIDO.txt"
    zip_path = tmp_path / "malicioso.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("../../INVADIDO.txt", "conteudo")
        zf.writestr("SKILL.md", "---\nname: x\ndescription: y\n---\n")

    antes = set(p.name for p in tmp_path.iterdir())
    report = hub.import_path(str(zip_path))
    assert not report.ok
    assert not alvo.exists()
    assert set(p.name for p in tmp_path.iterdir()) == antes


def test_zip_com_caminho_absoluto_e_recusado(tmp_path, hub):
    zip_path = tmp_path / "abs.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("/tmp/escapou.txt", "x")
    assert not hub.import_path(str(zip_path)).ok


def test_zip_com_ponto_ponto_no_meio_e_recusado(tmp_path, hub):
    zip_path = tmp_path / "meio.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("a/../../b.txt", "x")
    assert not hub.import_path(str(zip_path)).ok


def test_importacao_nao_altera_o_original(tmp_path, hub, skill_dir):
    antes = {p: p.read_bytes() for p in skill_dir.rglob("*") if p.is_file()}
    report = hub.import_path(str(skill_dir))
    assert report.ok
    depois = {p: p.read_bytes() for p in skill_dir.rglob("*") if p.is_file()}
    assert antes == depois, "o importador alterou o recurso original"


def test_importacao_nao_move_o_original(tmp_path, hub, skill_dir):
    hub.import_path(str(skill_dir))
    assert skill_dir.is_dir() and (skill_dir / "SKILL.md").is_file()


def test_reimportar_o_mesmo_conteudo_nao_sobrescreve(hub, skill_dir):
    """Mesmo conteúdo => mesmo id => o Hub reconhece e não regrava nada."""
    first = hub.import_path(str(skill_dir))
    hub.promote(first.capability_id)
    caminho = hub.locations.library / first.capability_id / "payload" / "SKILL.md"
    original = caminho.read_bytes()

    second = hub.import_path(str(skill_dir))
    assert second.ok
    assert second.already_present
    assert second.capability_id == first.capability_id
    assert caminho.read_bytes() == original, "o conteúdo foi sobrescrito"


def test_promover_capacidade_inexistente_falha_limpo(hub):
    from lia_agenthub.domain.errors import NotFound
    with pytest.raises(NotFound):
        hub.promote("nao-existe-00000000")


def test_staging_nao_grava_fora_da_quarentena(hub, skill_dir, tmp_path):
    """O staging escreve só sob Quarentena/<id>/payload."""
    antes = set(p.name for p in hub.locations.home.iterdir())
    report = hub.import_path(str(skill_dir))
    assert report.ok
    raiz = hub.locations.quarantine / report.capability_id
    escritos = [p for p in raiz.rglob("*") if p.is_file()]
    assert escritos, "nada foi gravado no staging"
    for p in escritos:
        assert str(p.resolve()).startswith(str(hub.locations.quarantine.resolve()))
    assert set(p.name for p in hub.locations.home.iterdir()) == antes


def test_capacidade_sem_confirmacao_nao_e_apagada(hub, imported):
    from lia_agenthub.domain.errors import ConflictError
    with pytest.raises(ConflictError):
        hub.repo.delete(imported["id"], confirmed=False)
    assert hub.repo.exists(imported["id"])


def test_symlink_em_diretorio_e_recusado(tmp_path, hub):
    d = tmp_path / "comlink"
    d.mkdir()
    (d / "SKILL.md").write_text("---\nname: com-link\ndescription: x\n---\n")
    try:
        os.symlink("/etc/passwd", d / "link.txt")
    except (OSError, NotImplementedError):
        pytest.skip("sistema sem suporte a symlink")
    report = hub.import_path(str(d))
    assert not report.ok or any(
        "link" in str(w).lower() or "symlink" in str(w).lower() for w in report.warnings)


def test_destino_de_exportacao_fora_da_area_e_permitido_apenas_por_escolha(hub, imported, tmp_path):
    """Exportar é a única escrita fora da área — e só para onde o humano aponta."""
    destino = tmp_path / "meus-exportados"
    r = hub.export(imported["id"], target="private", destination=str(destino))
    assert r["ok"]
    assert Path(r["path"]).parent == destino
