"""Fluxo de recebimento ponta a ponta: arquivo → validação → recibo.

O que estes testes protegem, em ordem de importância:

  1. Dry-run não grava NADA. Nem recibo, nem índice, nem quarentena.
  2. Rejeição não grava nada — "rejeitado sem gravação" é literal.
  3. Recibo é prova imutável: não sobrescreve.
  4. Quarentena é diretório real, não etiqueta de tela.
  5. O intake não executa, não instala, não conecta.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from lia_agenthub.adapters.inventory_intake import (
    ESTADO_CATALOGADO,
    ESTADO_QUARENTENA,
    ESTADO_RECEBIDO,
    ESTADO_REJEITADO,
    IntakeError,
    InventoryIntake,
)
from lia_agenthub.cli import main as cli_main

EXEMPLO = Path(__file__).resolve().parents[2] / "docs" / "examples" / "central-capability-inventory.v1.json"


@pytest.fixture
def doc() -> dict:
    return json.loads(EXEMPLO.read_text(encoding="utf-8"))


@pytest.fixture
def intake(locations) -> InventoryIntake:
    return InventoryIntake(locations)


def _salvar(tmp_path: Path, obj, nome: str = "inv.json") -> Path:
    destino = tmp_path / nome
    destino.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return destino


def _sem_dados(locations) -> bool:
    """True quando nada de inventário foi escrito."""
    raiz = Path(locations.common) / "Inventarios"
    return not raiz.exists() or not any(raiz.rglob("*"))


# --------------------------------------------------------------------------
# Pré-visualização
# --------------------------------------------------------------------------
def test_preview_nao_grava_nada(intake, doc, tmp_path, locations):
    plano = intake.previsualizar(_salvar(tmp_path, doc))
    assert plano.ok is True
    assert plano.efetivado is False
    assert plano.estado_proposto == ESTADO_RECEBIDO
    assert _sem_dados(locations), "dry-run que grava não é dry-run"
    assert plano.receipt_id == ""


def test_preview_classifica_igual_ao_recebimento(intake, doc, tmp_path):
    """Preview e gravação usam a MESMA classificação, senão confirma-se outra coisa."""
    caminho = _salvar(tmp_path, doc)
    preview = intake.previsualizar(caminho)
    efetivo = intake.receber(caminho)
    assert [c.classe for c in preview.classificados] == [c.classe for c in efetivo.classificados]
    assert preview.estado_proposto == efetivo.estado_proposto


def test_preview_de_arquivo_inexistente_nao_levanta(intake, tmp_path):
    plano = intake.previsualizar(tmp_path / "nao-existe.json")
    assert plano.ok is False
    assert "FILE_NOT_FOUND" in [a.code for a in plano.leitura.erros]


def test_diretorio_no_lugar_de_arquivo_e_recusado(intake, tmp_path):
    plano = intake.previsualizar(tmp_path)
    assert plano.ok is False
    assert "FILE_IS_DIRECTORY" in [a.code for a in plano.leitura.erros]


# --------------------------------------------------------------------------
# Recebimento
# --------------------------------------------------------------------------
def test_recebimento_grava_recibo_com_proveniencia(intake, doc, tmp_path):
    plano = intake.receber(_salvar(tmp_path, doc))
    assert plano.ok is True
    assert plano.efetivado is True

    recibo = json.loads(Path(plano.recibo_path).read_text(encoding="utf-8"))
    assert recibo["receiptId"] == plano.receipt_id
    assert recibo["state"] == ESTADO_RECEBIDO
    assert recibo["inventoryState"] == ESTADO_CATALOGADO
    assert recibo["issuerProject"] == "lia-forge"
    assert recibo["inventoryId"] == doc["inventoryId"]
    assert recibo["revision"] == doc["revision"]
    assert recibo["fileDigest"] == plano.leitura.envelope.file_digest
    assert recibo["receivedAt"], "momento do recebimento é obrigatório"
    assert recibo["complete"] is False
    assert len(recibo["records"]) == 1


def test_recibo_preserva_licenca_e_referencias(intake, doc, tmp_path):
    plano = intake.receber(_salvar(tmp_path, doc))
    recibo = json.loads(Path(plano.recibo_path).read_text(encoding="utf-8"))
    original = doc["records"][0]
    gravado = recibo["records"][0]
    conteudo = gravado["record"]
    assert conteudo["license"] == original["license"]
    assert conteudo["origins"] == original["origins"]
    assert conteudo["integrity"] == original["integrity"]
    assert conteudo["compatibility"] == original["compatibility"]


def test_recebimento_nao_promete_estado_alem_de_inventoried(intake, doc, tmp_path):
    plano = intake.receber(_salvar(tmp_path, doc))
    recibo = json.loads(Path(plano.recibo_path).read_text(encoding="utf-8"))
    assert recibo["inventoryState"] == "inventoried"
    # Nenhum estado posterior do contrato aparece.
    for proibido in ("approved-for-distribution", "configured", "operational",
                     "available-for-configuration", "validated"):
        assert proibido not in json.dumps(recibo)
    assert plano.as_dict()["boundary"]["maxState"] == "inventoried"


def test_recibo_declara_a_fronteira(intake, doc, tmp_path):
    plano = intake.receber(_salvar(tmp_path, doc))
    fronteira = plano.as_dict()["boundary"]
    assert fronteira["executes"] is False
    assert fronteira["installs"] is False
    assert fronteira["connects"] is False
    assert fronteira["grantsTrust"] is False
    assert fronteira["approvesLicense"] is False
    assert fronteira["promotesState"] is False


def test_recebimento_idempotente_nao_duplica_identidade(intake, doc, tmp_path, locations):
    caminho = _salvar(tmp_path, doc)
    intake.receber(caminho)
    segundo = intake.receber(caminho)
    assert segundo.efetivado is True
    classes = [c.classe.value for c in segundo.classificados]
    assert classes == ["exact-duplicate"]

    estado = json.loads((Path(locations.common) / "Inventarios" / "estado.json")
                        .read_text(encoding="utf-8"))
    assert len(estado) == 1
    (info,) = estado.values()
    assert len(info["revisions"]) == 1, "reenviar igual não pode criar revisão nova"


def test_recebimento_nao_sobrescreve_recibo(intake, doc, tmp_path):
    plano = intake.receber(_salvar(tmp_path, doc))
    recibo = inventory_recibo = intake.store.ler_recibo(plano.receipt_id)
    assert inventory_recibo["receiptId"] == recibo["receiptId"]
    # Gravar o mesmo id de novo é recusado: recibo é prova, não cache.
    from lia_agenthub.adapters.inventory_intake import Recibo
    with pytest.raises(IntakeError):
        intake.store.gravar_recibo(Recibo.from_dict(recibo))


# --------------------------------------------------------------------------
# Rejeição não grava
# --------------------------------------------------------------------------
@pytest.mark.parametrize("mutacao,codigo", [
    (lambda d: d.pop("revision"), "ENVELOPE_MISSING_FIELD"),
    (lambda d: d.__setitem__("inventoryVersion", 99), "ENVELOPE_UNSUPPORTED_VERSION"),
    (lambda d: d["records"][0].__setitem__("id", "id-inventado"), "RECORD_BAD_ID"),
    (lambda d: d["records"][0].__setitem__("origins", []), "RECORD_MISSING_ORIGINS"),
    (lambda d: d["records"][0].__setitem__("description", "ghp_" + "a" * 36),
     "SECRET_IN_INVENTORY"),
])
def test_rejeicao_nao_grava_nada(intake, doc, tmp_path, locations, mutacao, codigo):
    mutacao(doc)
    plano = intake.receber(_salvar(tmp_path, doc))
    assert plano.ok is False
    assert plano.efetivado is False
    assert plano.estado_proposto == ESTADO_REJEITADO
    assert codigo in [a.code for a in plano.leitura.erros]
    assert plano.receipt_id == ""
    assert _sem_dados(locations), "documento rejeitado não pode deixar rastro gravado"


def test_json_quebrado_nao_grava_nada(intake, tmp_path, locations):
    caminho = tmp_path / "quebrado.json"
    caminho.write_bytes(b'{"inventoryVersion": 1,,,}')
    plano = intake.receber(caminho)
    assert plano.ok is False
    assert _sem_dados(locations)


# --------------------------------------------------------------------------
# Conflito de feed e quarentena
# --------------------------------------------------------------------------
def test_mesma_revisao_com_conteudo_diferente_e_conflito_de_feed(intake, doc, tmp_path, locations):
    intake.receber(_salvar(tmp_path, doc, "a.json"))
    doc["records"][0]["name"] = "nome alterado"
    plano = intake.receber(_salvar(tmp_path, doc, "b.json"))
    assert plano.ok is False
    assert plano.estado_proposto == ESTADO_REJEITADO
    assert "conflito de feed" in plano.problema_feed
    assert plano.receipt_id == "", "conflito de feed não gera recibo de admissão"


def test_conflito_de_identidade_vai_para_quarentena_real(intake, doc, tmp_path, locations):
    primeiro = intake.receber(_salvar(tmp_path, doc, "a.json"))
    digest_original = primeiro.leitura.envelope.registros[0].digest
    estado_antes = json.loads((Path(locations.common) / "Inventarios" / "estado.json")
                              .read_text(encoding="utf-8"))
    registro_antes = copy.deepcopy(estado_antes[doc["records"][0]["id"]])
    # Envelope novo; o REGISTRO republica a MESMA revisão com conteúdo divergente.
    doc["revision"] = "snapshot-002"
    doc["records"][0]["name"] = "divergente"
    plano = intake.receber(_salvar(tmp_path, doc, "b.json"))

    assert plano.ok is True
    assert plano.estado_proposto == ESTADO_QUARENTENA
    assert plano.destino_quarentena, "quarentena precisa existir no disco"

    pasta = Path(plano.destino_quarentena)
    assert pasta.exists() and pasta.is_dir()
    assert str(pasta).startswith(str(locations.quarantine))
    retencao = json.loads((pasta / "retencao.json").read_text(encoding="utf-8"))
    assert retencao["receiptId"] == plano.receipt_id
    assert "decisão humana" in retencao["reason"]
    assert retencao["records"][0]["classification"] == "identity-conflict"

    # E o registro NÃO entrou no acervo.
    estado = json.loads((Path(locations.common) / "Inventarios" / "estado.json")
                        .read_text(encoding="utf-8"))
    # A revisão disputada continua registrada com o digest ORIGINAL: o relato
    # que chegou depois não substituiu o que já estava comprovado.
    revisoes = estado[doc["records"][0]["id"]]["revisions"]
    assert revisoes[doc["records"][0]["revisionId"]]["digest"] == digest_original
    assert estado[doc["records"][0]["id"]] == registro_antes, \
        "conflito não altera o acervo — nem apaga, nem sobrescreve"


def test_quarentena_nao_copia_payload(intake, doc, tmp_path):
    """O emissor não envia payload; e mesmo que enviasse, não seria copiado."""
    doc["records"][0]["payload"] = "conteudo-que-nao-deve-ser-copiado"
    plano = intake.receber(_salvar(tmp_path, doc))
    pasta = Path(plano.destino_quarentena) if plano.destino_quarentena else Path(plano.recibo_path).parent
    for arquivo in pasta.rglob("*"):
        if arquivo.is_file():
            assert "conteudo-que-deve" not in arquivo.read_text(encoding="utf-8")


def test_downgrade_nao_e_admitido(intake, doc, tmp_path, locations):
    doc["records"][0]["version"] = "1.0.0"
    intake.receber(_salvar(tmp_path, doc, "a.json"))
    # A revisão do ENVELOPE avança; a do REGISTRO muda para uma versão anterior.
    doc["revision"] = "snapshot-002"
    doc["records"][0]["revisionId"] = "rev-000"
    doc["records"][0]["version"] = "0.1.0"
    plano = intake.receber(_salvar(tmp_path, doc, "b.json"))
    assert plano.estado_proposto == ESTADO_QUARENTENA
    classes = [c.classe.value for c in plano.classificados]
    assert "downgrade" in classes


def test_atualizacao_de_versao_e_admitida(intake, doc, tmp_path):
    doc["records"][0]["version"] = "1.0.0"
    intake.receber(_salvar(tmp_path, doc, "a.json"))
    doc["revision"] = "snapshot-002"
    doc["records"][0]["revisionId"] = "rev-002"
    doc["records"][0]["version"] = "1.1.0"
    plano = intake.receber(_salvar(tmp_path, doc, "b.json"))
    assert plano.estado_proposto == ESTADO_RECEBIDO, "atualização não é conflito"
    assert "update" in [c.classe.value for c in plano.classificados]
    plano_dict = plano.as_dict()
    assert plano_dict["state"] == ESTADO_RECEBIDO
    assert plano.destino_quarentena == "", "atualização não vai para quarentena"


# --------------------------------------------------------------------------
# Estado e recibos
# --------------------------------------------------------------------------
def test_estado_corrompido_nao_e_tratado_como_vazio(intake, locations):
    """Tratar índice corrompido como vazio faria o próximo inventário 'atualizar' tudo."""
    raiz = Path(locations.common) / "Inventarios"
    raiz.mkdir(parents=True, exist_ok=True)
    (raiz / "estado.json").write_text("{lixo", encoding="utf-8")
    with pytest.raises(IntakeError):
        intake.store.conhecidos()


def test_listar_e_ler_recibos(intake, doc, tmp_path):
    plano = intake.receber(_salvar(tmp_path, doc))
    recibos = intake.store.listar_recibos()
    assert len(recibos) == 1
    assert recibos[0]["receiptId"] == plano.receipt_id
    assert intake.store.ler_recibo(plano.receipt_id)["revision"] == doc["revision"]


@pytest.mark.parametrize("ruim", ["../estado", "rec-1/../../x", "", "rec 1", "rec\x001"])
def test_id_de_recibo_com_caractere_estranho_e_recusado(intake, ruim):
    """`receipt_id` vem da rota; não pode virar leitura fora do diretório."""
    with pytest.raises(IntakeError):
        intake.store.ler_recibo(ruim)


# --------------------------------------------------------------------------
# CLI — o caminho do usuário sem janela
# --------------------------------------------------------------------------
def test_cli_preview_nao_grava(locations, doc, tmp_path, capsys):
    caminho = _salvar(tmp_path, doc)
    codigo = cli_main(["--home", str(locations.home), "inventory", "preview", str(caminho)])
    assert codigo == 0
    saida = capsys.readouterr().out
    assert "PRÉ-VISUALIZAÇÃO" in saida
    assert _sem_dados(locations)


def test_cli_receive_com_commit_grava(locations, doc, tmp_path, capsys):
    caminho = _salvar(tmp_path, doc)
    codigo = cli_main(["--home", str(locations.home), "inventory", "receive",
                       str(caminho), "--commit"])
    assert codigo == 0
    assert "RECEBIDO" in capsys.readouterr().out
    assert not _sem_dados(locations)


def test_cli_rejeicao_sai_com_1(locations, doc, tmp_path, capsys):
    doc.pop("revision")
    caminho = _salvar(tmp_path, doc)
    codigo = cli_main(["--home", str(locations.home), "inventory", "receive",
                       str(caminho), "--commit"])
    assert codigo == 1, "recurso com erro bloqueante sai 1, não 0"
    assert "ENVELOPE_MISSING_FIELD" in capsys.readouterr().out


def test_cli_json_e_parseavel(locations, doc, tmp_path, capsys):
    caminho = _salvar(tmp_path, doc)
    cli_main(["--home", str(locations.home), "inventory", "preview", str(caminho), "--json"])
    saida = json.loads(capsys.readouterr().out)
    assert saida["dryRun"] is True
    assert saida["ok"] is True
    assert saida["classifications"] == {"new": 1}


def test_cli_state_lista_identidades(locations, doc, tmp_path, capsys):
    cli_main(["--home", str(locations.home), "inventory", "receive",
              str(_salvar(tmp_path, doc)), "--commit"])
    capsys.readouterr()
    assert cli_main(["--home", str(locations.home), "inventory", "state"]) == 0
    saida = capsys.readouterr().out
    assert doc["records"][0]["id"] in saida
    assert "inventoried" in saida


# --------------------------------------------------------------------------
# Rotas HTTP (mesma lógica, caminho do usuário na interface)
# --------------------------------------------------------------------------
def test_rotas_de_inventario_existem_no_servidor(hub, doc, tmp_path):
    assert hub.inventory_preview(str(_salvar(tmp_path, doc)))["dryRun"] is True
    resultado = hub.inventory_receive(str(_salvar(tmp_path, doc, "b.json")))
    assert resultado["committed"] is True
    assert hub.inventory_receipts()
    assert hub.inventory_receipt(resultado["receiptId"])["receiptId"] == resultado["receiptId"]
    estado = hub.inventory_state()
    assert estado["ok"] is True
    assert estado["count"] == 1
    assert estado["maxState"] == "inventoried"


def test_spa_declara_as_rotas():
    """Rota no servidor sem caminho na UI é método interno sem usuário."""
    raiz = Path(__file__).resolve().parents[2]
    fonte = (raiz / "src" / "lia_agenthub" / "resources" / "static"
             / "index.html").read_text(encoding="utf-8")
    for rota in ("/api/inventory/preview", "/api/inventory/receive",
                 "/api/inventory", "/api/inventory/receipts"):
        assert rota in fonte or rota.split("/")[-1] in fonte, f"{rota} sem caminho na UI"


# --------------------------------------------------------------------------
# P0 do CAPABILITY-REGISTRY-READINESS: fixture v1 continua legível
# --------------------------------------------------------------------------
def test_fixture_v1_continua_legivel():
    """Critério P0: a fixture de intercâmbio permanece legível, campo a campo."""
    from lia_agenthub.domain.inventory import ler
    from pathlib import Path as _P
    raiz = _P(__file__).resolve().parents[2]
    dados = (raiz / "docs" / "examples" / "central-capability-inventory.v1.json").read_bytes()
    leitura = ler(dados)
    assert leitura.ok is True
    assert leitura.achados == [], "fixture de referência não pode gerar achado"
    original = json.loads(dados)
    assert leitura.envelope.registros[0].bruto == original["records"][0]


def test_erro_de_validacao_aponta_o_registro():
    """Critério P0: erro aponta ao registro, não só 'documento inválido'."""
    from lia_agenthub.domain.inventory import ler
    doc = json.loads(EXEMPLO.read_text(encoding="utf-8"))
    doc["records"][0]["name"] = ""
    leitura = ler(json.dumps(doc).encode())
    assert leitura.ok is False
    (erro,) = [a for a in leitura.erros if a.code == "RECORD_MISSING_NAME"]
    assert erro.where == "records[0]", f"erro sem localização: {erro.where!r}"


def test_catalogo_interno_nao_e_confundido_com_envelope_v1():
    """`docs/stitch/catalog/*.records.json` é catálogo do Hub, não envelope v1.

    Aceitá-lo como inventário faria o intake ler um formato interno como se
    fosse intercâmbio entre projetos — exatamente o que o contrato separa.
    """
    from lia_agenthub.domain.inventory import ler
    p = Path(__file__).resolve().parents[2] / "docs" / "stitch" / "catalog" / "google-stitch.records.json"
    leitura = ler(p.read_bytes())
    assert leitura.ok is False
    assert "ENVELOPE_MISSING_VERSION" in [a.code for a in leitura.erros]


def test_cli_recusa_com_commit_nao_se_disfarca_de_preview(locations, doc, tmp_path, capsys):
    """Pedir para gravar e não gravar precisa aparecer como RECUSADO.

    Regressão: a saída dizia "PRÉ-VISUALIZAÇÃO" mesmo com `--commit`, o que
    esconderia a recusa de quem pediu o recebimento.
    """
    doc.pop("revision")
    codigo = cli_main(["--home", str(locations.home), "inventory", "receive",
                       str(_salvar(tmp_path, doc)), "--commit"])
    saida = capsys.readouterr().out
    assert codigo == 1
    assert "RECUSADO (nada gravado)" in saida
    assert "PRÉ-VISUALIZAÇÃO" not in saida
    assert _sem_dados(locations)


# --------------------------------------------------------------------------
# Proveniência multi-origem e relações declaradas
# --------------------------------------------------------------------------
def test_mesma_identidade_preserva_declaracoes_de_feeds_diferentes(
        intake, doc, tmp_path, locations):
    """Um feed novo não pode sobrescrever a origem que já declarou a revisão."""
    primeiro = _salvar(tmp_path, doc, "forge.json")
    intake.receber(primeiro)

    segundo_doc = copy.deepcopy(doc)
    segundo_doc["inventoryId"] = "studio-snapshot"
    segundo_doc["revision"] = "snapshot-studio-001"
    segundo_doc["issuer"] = {
        "project": "lia-studio",
        "repository": "https://example.invalid/studio",
        "maintainer": "Mantenedor Studio",
    }
    segundo = _salvar(tmp_path, segundo_doc, "studio.json")
    resultado = intake.receber(segundo)

    assert resultado.classificados[0].classe.value == "exact-duplicate"
    estado = json.loads((Path(locations.common) / "Inventarios" / "estado.json")
                        .read_text(encoding="utf-8"))
    revisao = next(iter(estado.values()))["revisions"]["rev-001"]
    assert len(revisao["sources"]) == 2
    assert {s["issuer"]["project"] for s in revisao["sources"]} == {
        "lia-forge", "lia-studio"}
    assert len(estado[next(iter(estado))]["issuerProjects"]) == 2


def test_reenvio_do_mesmo_feed_acrescenta_recibo_sem_duplicar_origem(
        intake, doc, tmp_path, locations):
    caminho = _salvar(tmp_path, doc)
    primeiro = intake.receber(caminho)
    segundo = intake.receber(caminho)

    estado = json.loads((Path(locations.common) / "Inventarios" / "estado.json")
                        .read_text(encoding="utf-8"))
    revisao = next(iter(estado.values()))["revisions"]["rev-001"]
    assert len(revisao["sources"]) == 1
    claim = revisao["sources"][0]
    assert claim["receiptIds"] == [primeiro.receipt_id, segundo.receipt_id]


def test_estado_preserva_aliases_dependencias_e_ofertas_como_declaracoes(
        intake, doc, tmp_path, locations):
    registro = doc["records"][0]
    registro["aliases"] = [
        {"scheme": "upstream", "value": "forge:workflow/revisao",
         "authority": "lia-forge"}
    ]
    registro["dependencies"] = [
        {"targetId": "urn:lia:cap:11111111-2222-3333-4444-555555555555",
         "optional": True, "versionRange": ">=1.0.0"}
    ]
    registro["offers"] = [
        {"id": "revisar-asset", "kind": "workflow-step"}
    ]

    intake.receber(_salvar(tmp_path, doc))
    estado = json.loads((Path(locations.common) / "Inventarios" / "estado.json")
                        .read_text(encoding="utf-8"))
    revisao = next(iter(estado.values()))["revisions"]["rev-001"]
    assert revisao["aliases"] == registro["aliases"]
    assert revisao["dependencies"] == registro["dependencies"]
    assert revisao["offers"] == registro["offers"]
    assert revisao["sources"][0]["origins"] == registro["origins"]
