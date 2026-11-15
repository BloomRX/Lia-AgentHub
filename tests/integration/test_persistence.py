"""Persistência — escrita interrompida, recuperação, índice inconsistente."""
import json
import os
from pathlib import Path

import pytest

from lia_agenthub.adapters.atomic import atomic_write_bytes, atomic_write_json, read_json
from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.app import AgentHub


# ---------- escrita atômica ----------
def test_escrita_atomica_nao_deixa_arquivo_parcial(tmp_path):
    alvo = tmp_path / "dados.json"
    atomic_write_json(alvo, {"a": 1})
    assert read_json(alvo) == {"a": 1}
    temporarios = [p for p in tmp_path.iterdir() if p.name.startswith(".tmp")]
    assert temporarios == [], "arquivo temporário ficou para trás"


def test_segunda_escrita_substitui_sem_deixar_resto(tmp_path):
    alvo = tmp_path / "dados.json"
    atomic_write_json(alvo, {"versao": 1})
    atomic_write_json(alvo, {"versao": 2})
    assert read_json(alvo) == {"versao": 2}
    assert len([p for p in tmp_path.iterdir() if p.is_file()]) == 1


def test_json_corrompido_e_tratado_sem_derrubar(tmp_path):
    alvo = tmp_path / "capability.json"
    alvo.write_bytes(b'{"id": "x", truncado')
    assert read_json(alvo) is None


def test_leitura_de_arquivo_inexistente_retorna_none(tmp_path):
    assert read_json(tmp_path / "nao-existe.json") is None


def test_escrita_em_diretorio_inexistente_cria_pai(tmp_path):
    alvo = tmp_path / "a" / "b" / "c.json"
    atomic_write_json(alvo, {"ok": True})
    assert alvo.is_file()


def test_bytes_grandes_sao_escritos_integrais(tmp_path):
    dados = os.urandom(500_000)
    alvo = tmp_path / "grande.bin"
    atomic_write_bytes(alvo, dados)
    assert alvo.read_bytes() == dados


# ---------- recuperação da biblioteca ----------
def test_biblioteca_e_reconstruida_varrendo_o_disco(hub, imported, tmp_path):
    """O índice é derivado: pode ser apagado sem perda de verdade."""
    idx = hub.locations.common / "index.json"
    if idx.exists():
        idx.unlink()
    assert hub.items() and hub.items()[0]["id"] == imported["id"]


def test_capacidade_com_metadado_corrompido_nao_derruba_a_lista(hub, imported):
    outra = hub.import_path.__self__  # noqa: F841  (só para clareza)
    ruim = hub.locations.library / "corrompida-00000000"
    (ruim / ".lia").mkdir(parents=True)
    (ruim / ".lia" / "capability.json").write_text("{lixo", encoding="utf-8")
    itens = hub.items()
    assert any(i["id"] == imported["id"] for i in itens)


def test_capacidade_sem_metadado_e_ignorada(hub, imported):
    orfa = hub.locations.library / "sem-metadado-aaa"
    (orfa / "payload").mkdir(parents=True)
    (orfa / "payload" / "x.md").write_text("x", encoding="utf-8")
    assert all(i["id"] != "sem-metadado-aaa" for i in hub.items())


def test_arquivo_ausente_no_payload_nao_quebra_o_detalhe(hub, imported):
    alvo = hub.locations.library / imported["id"] / "payload" / "SKILL.md"
    alvo.unlink()
    d = hub.detail(imported["id"])
    assert d["id"] == imported["id"]
    assert "SKILL.md" not in d["files"]      # o ausente não é listado
    assert "LICENSE" in d["files"]           # o que sobrou continua listado


def test_metadado_sumido_vira_erro_legivel(hub, imported):
    from lia_agenthub.domain.errors import NotFound
    (hub.locations.library / imported["id"] / ".lia" / "capability.json").unlink()
    with pytest.raises(NotFound) as e:
        hub.detail(imported["id"])
    assert "não encontr" in e.value.message.lower()
    assert e.value.hint


# ---------- índice ----------
def test_indice_consistente_apos_publicacao(hub, imported, tmp_path):
    hub.publish_index()
    saude = hub.index_health()
    assert saude["ok"], saude


def test_indice_apontando_para_pacote_ausente_e_detectado(hub, imported, tmp_path):
    hub.export(imported["id"], target="private")
    hub.publish_index()
    # apagar o pacote deixa o índice apontando para o nada
    for p in hub.locations.exports.glob("*.lia-capability"):
        p.unlink()
    saude = hub.index_health()
    assert not saude["ok"]
    assert saude["missingPackages"]


def test_indice_alterado_a_mao_e_detectado(hub, imported):
    hub.publish_index()
    caminho = hub.locations.common / "index.json"
    idx = json.loads(caminho.read_text())
    idx["capabilities"].append({
        "id": "fantasma-00000000", "name": "fantasma", "version": "1.0",
        "type": "agent-skill", "trust": "first-party", "license": "MIT"})
    caminho.write_text(json.dumps(idx), encoding="utf-8")
    saude = hub.index_health()
    assert not saude["ok"]


def test_indice_que_afirma_assinatura_e_rejeitado(hub, imported):
    hub.publish_index()
    caminho = hub.locations.common / "index.json"
    idx = json.loads(caminho.read_text())
    idx["signed"] = True
    caminho.write_text(json.dumps(idx), encoding="utf-8")
    saude = hub.index_health()
    assert not saude["ok"]
    assert any("signed" in p for p in saude["problems"])


def test_indice_sem_gerar_nao_e_erro(hub):
    saude = hub.index_health()
    assert saude["exists"] is False
    assert saude["ok"] is True


def test_indice_nao_contem_caminho_absoluto(hub, imported):
    hub.publish_index()
    texto = (hub.locations.common / "index.json").read_text()
    assert "C:\\" not in texto
    assert "\\\\" not in texto.replace("\\\\n", "")


def test_indice_e_legivel_sem_o_hub(hub, imported):
    """O leitor de referência não importa nada do Hub."""
    hub.publish_index()
    caminho = hub.locations.common / "index.json"
    dados = json.loads(caminho.read_text())
    assert dados["schemaVersion"] == 1
    assert isinstance(dados["capabilities"], list)
    assert dados["signed"] is False


# ---------- atualização de versão ----------
def test_diff_entre_duas_versoes(hub, tmp_path):
    a = tmp_path / "v1"
    a.mkdir()
    (a / "SKILL.md").write_text("---\nname: evoluindo\ndescription: v1\n---\n\nA\n")
    (a / "extra.md").write_text("some depois", encoding="utf-8")
    ra = hub.import_path(str(a))
    hub.promote(ra.capability_id)

    b = tmp_path / "v2"
    b.mkdir()
    (b / "SKILL.md").write_text("---\nname: evoluindo\ndescription: v2\n---\n\nB\n")
    (b / "novo.md").write_text("aparece", encoding="utf-8")
    rb = hub.import_path(str(b))
    hub.promote(rb.capability_id)

    d = hub.diff_versions(ra.capability_id, rb.capability_id)
    assert "extra.md" in d["onlyInA"]
    assert "novo.md" in d["onlyInB"]
    assert "SKILL.md" in d["changed"]
    assert not d["identical"]


def test_diff_de_identicos(hub, imported):
    assert hub.diff_versions(imported["id"], imported["id"])["identical"]


# ---------- backup e restauração ----------
def test_backup_e_restauracao_por_copia_de_diretorio(hub, imported, tmp_path):
    """A estratégia documentada: copiar a pasta com o Hub fechado."""
    import shutil

    backup = tmp_path / "backup"
    shutil.copytree(hub.locations.home, backup)

    # estrago: apaga a biblioteca
    shutil.rmtree(hub.locations.library)
    assert hub.items() == []

    # restauração
    shutil.copytree(backup / "Biblioteca", hub.locations.library)
    itens = hub.items()
    assert len(itens) == 1 and itens[0]["id"] == imported["id"]
    assert hub.detail(imported["id"])["files"] == ["LICENSE", "SKILL.md"]


def test_restauracao_preserva_hashes(hub, imported, tmp_path):
    import shutil
    antes = hub.detail(imported["id"])["integrityNow"]
    backup = tmp_path / "bk"
    shutil.copytree(hub.locations.home, backup)
    shutil.rmtree(hub.locations.library)
    shutil.copytree(backup / "Biblioteca", hub.locations.library)
    depois = hub.detail(imported["id"])["integrityNow"]
    assert antes == depois


def test_promocao_e_atomica_nao_deixa_meio_estado(hub, skill_dir):
    """Promover move o diretório inteiro: ou existe, ou não existe."""
    report = hub.import_path(str(skill_dir))
    hub.promote(report.capability_id)
    na_biblioteca = hub.locations.library / report.capability_id
    na_quarentena = hub.locations.quarantine / report.capability_id
    assert na_biblioteca.is_dir()
    assert not na_quarentena.exists()
    assert (na_biblioteca / "payload" / "SKILL.md").is_file()
    assert (na_biblioteca / ".lia" / "capability.json").is_file()


def test_historico_registra_as_acoes(hub, imported):
    hub.validate(imported["id"])
    hub.set_trust(imported["id"], "user-provided")
    acoes = [h["action"] for h in hub.history(imported["id"])]
    assert "import" in acoes
    assert "promote" in acoes
    assert "trust" in acoes


def test_descartar_quarentena_remove_do_disco(hub, skill_dir):
    report = hub.import_path(str(skill_dir))
    raiz = hub.locations.quarantine / report.capability_id
    assert raiz.is_dir()
    hub.discard(report.capability_id)
    assert not raiz.exists()


def test_locations_persistem_entre_instancias(locations, skill_dir):
    """Fechar e reabrir o app não perde nada: o disco é a verdade."""
    h1 = AgentHub(locations)
    rep = h1.import_path(str(skill_dir))
    h1.promote(rep.capability_id)
    h1.set_trust(rep.capability_id, "reviewed-external")

    # reabrir = mesmo home, processo novo (aqui: nova instância e novo resolvedor)
    h2 = AgentHub(resolve_locations(locations.home))
    itens = h2.items()
    assert len(itens) == 1
    assert itens[0]["id"] == rep.capability_id
    assert itens[0]["trust"] == "reviewed-external"
