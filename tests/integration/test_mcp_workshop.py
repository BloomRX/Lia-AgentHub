"""Fase 2 — MCP Workshop: catalogar sem conectar.

O produto promete registrar um servidor MCP e entregar a configuração para o
usuário colar. Ele NÃO promete conectar, instalar nem saber se funciona.

A distinção que estes testes protegem (doutrina de quatro estados):
    catalogado no Hub  ≠  configurado no host  ≠  autenticado  ≠  operacional
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from lia_agenthub.domain.mcp import (
    PLACEHOLDER_CREDENCIAL, DescritorInvalido, MCPServer, config_para_host,
)
from lia_agenthub.domain.errors import LiaError

STITCH = Path(__file__).resolve().parents[2] / "docs/stitch/mcp/google-stitch.mcp.json"
INVENTORY_STDIO_ID = "urn:lia:cap:12345678-1234-4abc-8def-123456789abc"


@pytest.fixture
def hub(tmp_path):
    from lia_agenthub.adapters.paths_resolver import resolve_locations
    from lia_agenthub.app import AgentHub
    return AgentHub(resolve_locations(tmp_path / "hub"))


def _mcp(hub, tmp_path, descritor: dict, nome="srv") -> str:
    d = tmp_path / nome
    d.mkdir(parents=True)
    (d / "mcp.json").write_text(json.dumps(descritor), encoding="utf-8")
    r = hub.import_path(str(d))
    assert r.ok, r.blocked_reason
    return r.capability_id


def _inventory_stdio(tmp_path: Path, details: dict | None = None) -> Path:
    """MCP apenas inventariado: referência, nunca payload ou launcher."""
    doc = {
        "inventoryVersion": 1,
        "inventoryId": "forge-mcp-template-test",
        "revision": "snapshot-1",
        "generatedAt": "2026-11-20T00:00:00Z",
        "complete": False,
        "issuer": {
            "project": "lia-forge",
            "repository": "https://example.invalid/forge",
            "maintainer": "Forge test",
        },
        "records": [{
            "id": INVENTORY_STDIO_ID,
            "revisionId": "stdio-1",
            "kind": "mcp-server",
            "name": "forge-mcp",
            "version": None,
            "description": "Servidor MCP declarado apenas para revisão de host.",
            "origins": [{
                "project": "lia-forge",
                "repository": "https://example.invalid/forge",
                "path": "scripts/forge-mcp.mjs",
                "branch": None,
                "commit": None,
                "author": None,
                "maintainer": "Forge test",
                "evidenceIds": [],
            }],
            "license": {"declared": None,
                        "redistribution": {"status": "pending", "authorizationIds": []}},
            "integrity": [],
            "dependencies": [],
            "offers": [],
            "compatibility": [],
            "details": details if details is not None else {"declaredTransport": "stdio"},
        }],
        "evidence": [],
    }
    path = tmp_path / "forge-mcp.inventory.json"
    path.write_text(json.dumps(doc), encoding="utf-8")
    return path


class TestConfiguracaoParaHost:
    def test_bloco_generico_usa_url(self):
        s = MCPServer.from_dict({"endpoint": "https://x.example/mcp",
                                 "provider": "Exemplo"})
        bloco = config_para_host(s, "mcp-json", nome="exemplo")
        entrada = bloco["bloco"]["mcpServers"]["exemplo"]
        assert entrada["url"] == "https://x.example/mcp"
        assert entrada["type"] == "http"

    def test_antigravity_usa_serverurl(self):
        """Diferença real entre clientes, verificada na doc do Stitch."""
        s = MCPServer.from_dict({"endpoint": "https://x/mcp"})
        bloco = config_para_host(s, "antigravity", nome="x")
        entrada = bloco["bloco"]["mcpServers"]["x"]
        assert "serverUrl" in entrada
        assert "url" not in entrada

    def test_cabecalho_vira_placeholder_nunca_valor(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp",
                                 "headers": ["X-Goog-Api-Key"]})
        bloco = config_para_host(s)
        cab = bloco["bloco"]["mcpServers"]["servidor-mcp"]["headers"]
        assert cab["X-Goog-Api-Key"] == PLACEHOLDER_CREDENCIAL

    def test_pendencia_avisa_que_falta_chave(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp",
                                 "headers": ["X-Goog-Api-Key"]})
        pendencias = " ".join(config_para_host(s)["pendencias"])
        assert "X-Goog-Api-Key" in pendencias
        assert "não neste aplicativo" in pendencias

    def test_sem_cabecalho_nao_inventa_pendencia(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp"})
        assert config_para_host(s)["pendencias"] == []

    def test_requisitos_de_conta_viram_pendencia(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp",
                                 "accountRequirements": ["conta Google"]})
        assert any("conta Google" in p for p in config_para_host(s)["pendencias"])

    def test_avisa_que_nao_verificou(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp"})
        avisos = " ".join(config_para_host(s)["avisos"])
        assert "NÃO verificou" in avisos
        assert "connectivityVerified" in avisos

    def test_formato_desconhecido_falha_em_vez_de_adivinhar(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp"})
        with pytest.raises(DescritorInvalido):
            config_para_host(s, "cliente-inventado")

    def test_stdio_recusado_com_explicacao(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp", "transport": "stdio"})
        with pytest.raises(DescritorInvalido) as e:
            config_para_host(s)
        assert "comando" in str(e.value)

    def test_config_nunca_marca_executado(self):
        s = MCPServer.from_dict({"endpoint": "https://x/mcp"})
        assert config_para_host(s)["executadoPeloHub"] is False


class TestConfigNoHub:
    def test_inventory_stdio_generates_passive_template_without_import(
            self, hub, tmp_path, monkeypatch):
        """O catálogo pode descrever a revisão, mas não vira payload nem host."""
        import socket
        monkeypatch.setattr(socket.socket, "connect",
                            lambda *a, **k: (_ for _ in ()).throw(
                                AssertionError("tentou conectar")))
        recebido = hub.inventory_receive(str(_inventory_stdio(tmp_path)))
        assert recebido["ok"] is True

        config = hub.mcp_config(INVENTORY_STDIO_ID, "claude-code")
        entry = config["bloco"]["mcpServers"]["forge-mcp"]
        assert entry == {"type": "stdio", "command": "<CAMINHO_DO_EXECUTAVEL>", "args": []}
        recurso = config["recurso"]
        assert recurso["id"] == INVENTORY_STDIO_ID
        assert recurso["source"] == "inventory-reference"
        assert recurso["inventoryRevision"] == "stdio-1"
        assert recurso["inventoryState"] == "inventoried"
        assert recurso["configuredInHost"] is False
        assert recurso["connectivityVerified"] is False
        assert len(recurso["inventoryDigest"]) == 64
        assert config["executadoPeloHub"] is False
        assert hub.items() == [], "inventário não pode importar payload implicitamente"
        record = hub.inventory_state()["records"][0]
        assert record["declaredDetails"]["stdio-1"] == {"declaredTransport": "stdio"}

    def test_inventory_stdio_rejects_launch_material(self, hub, tmp_path):
        hub.inventory_receive(str(_inventory_stdio(tmp_path, {
            "declaredTransport": "stdio", "command": "nao-use-isto",
        })))
        with pytest.raises(LiaError, match="conexão/lançamento"):
            hub.mcp_config(INVENTORY_STDIO_ID, "claude-code")

    def test_stdio_template_is_passive_and_does_not_declare_egress(self, hub, tmp_path):
        cid = _mcp(hub, tmp_path, {"transport": "stdio", "provider": "Forge"})
        config = hub.mcp_config(cid, "claude-code")
        entry = next(iter(config["bloco"]["mcpServers"].values()))
        assert entry == {"type": "stdio", "command": "<CAMINHO_DO_EXECUTAVEL>", "args": []}
        assert config["recurso"]["endpoint"] == ""
        assert config["recurso"]["connectivityVerified"] is False
        assert config["executadoPeloHub"] is False
        assert hub.repo._load_any(cid).capability.egress == []

    @pytest.mark.parametrize("field,value", [
        ("command", "launcher"), ("args", ["--example"]), ("env", {"EXAMPLE": "fixture"}),
    ])
    def test_stdio_descriptor_rejects_host_launch_fields(self, field, value):
        with pytest.raises(DescritorInvalido, match="somente no host"):
            MCPServer.from_dict({"transport": "stdio", field: value})

    def test_stich_gera_bloco_utilizavel(self, hub, tmp_path):
        cid = _mcp(hub, tmp_path, json.loads(STITCH.read_text(encoding="utf-8")))
        r = hub.mcp_config(cid)
        assert r["bloco"]["mcpServers"]
        entrada = next(iter(r["bloco"]["mcpServers"].values()))
        assert entrada["url"] == "https://stitch.googleapis.com/mcp"
        assert r["recurso"]["connectivityVerified"] is False

    def test_json_da_config_nao_tem_chave(self, hub, tmp_path):
        cid = _mcp(hub, tmp_path, json.loads(STITCH.read_text(encoding="utf-8")))
        bruto = json.dumps(hub.mcp_config(cid), ensure_ascii=False)
        for padrao in ("AIza", "ya29.", "eyJhbGci"):
            assert padrao not in bruto, padrao

    def test_recurso_que_nao_e_mcp_e_recusado(self, hub, tmp_path):
        d = tmp_path / "s"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: s\ndescription: d\n---\n\nC.\n", encoding="utf-8")
        r = hub.import_path(str(d))
        with pytest.raises(LiaError) as e:
            hub.mcp_config(r.capability_id)
        assert "não é um servidor MCP" in str(e.value)

    def test_id_inexistente_nao_estoura_500(self, hub):
        """`Exception` genérica aceitaria até um TypeError — o teste passaria
        com o código quebrado. Exige o erro de domínio do Hub."""
        from lia_agenthub.domain.errors import LiaError as _LiaError
        with pytest.raises((_LiaError, FileNotFoundError)):
            hub.mcp_config("nao-existe")


class TestRotaHTTP:
    def test_rota_existe_e_devolve_bloco(self, hub, tmp_path):
        cid = _mcp(hub, tmp_path, json.loads(STITCH.read_text(encoding="utf-8")))
        r = hub.mcp_config(cid)
        assert r["format"] == "mcp-json"

    def test_formato_na_url(self, hub, tmp_path):
        cid = _mcp(hub, tmp_path, {"endpoint": "https://x/mcp"})
        assert hub.mcp_config(cid, "antigravity")["format"] == "antigravity"


class TestExportacaoLevaDescritor:
    """O pacote precisa carregar o descritor — senão o receptor não sabe o quê
    configurar. E precisa carregar SEM segredo."""

    def test_pacote_leva_mcp_json(self, hub, tmp_path):
        cid = _mcp(hub, tmp_path, json.loads(STITCH.read_text(encoding="utf-8")))
        hub.promote(cid)
        r = hub.export(cid, target="private", destination=str(tmp_path / "out"))
        zf = zipfile.ZipFile(r["path"])
        assert "payload/mcp.json" in zf.namelist()
        dados = json.loads(zf.read("payload/mcp.json"))
        assert dados["endpoint"] == "https://stitch.googleapis.com/mcp"

    def test_manifesto_declara_o_endpoint_como_egress(self, hub, tmp_path):
        cid = _mcp(hub, tmp_path, {"endpoint": "https://x.example/mcp"})
        hub.promote(cid)
        r = hub.export(cid, target="private", destination=str(tmp_path / "out"))
        zf = zipfile.ZipFile(r["path"])
        manifesto = json.loads(zf.read("manifest.json"))
        assert "https://x.example/mcp" in json.dumps(manifesto)


class TestNaoConecta:
    def test_importar_mcp_nao_abre_socket(self, hub, tmp_path, monkeypatch):
        import socket
        monkeypatch.setattr(socket.socket, "connect",
                            lambda *a, **k: (_ for _ in ()).throw(
                                AssertionError("tentou conectar")))
        monkeypatch.setattr(socket, "create_connection",
                            lambda *a, **k: (_ for _ in ()).throw(
                                AssertionError("tentou conectar")))
        cid = _mcp(hub, tmp_path, json.loads(STITCH.read_text(encoding="utf-8")))
        assert cid

    def test_gerar_config_nao_abre_socket(self, hub, tmp_path, monkeypatch):
        import socket
        monkeypatch.setattr(socket.socket, "connect",
                            lambda *a, **k: (_ for _ in ()).throw(
                                AssertionError("tentou conectar")))
        cid = _mcp(hub, tmp_path, {"endpoint": "https://x/mcp"})
        hub.mcp_config(cid)
