"""Integração do Google Stitch no Hub — verificada, não afirmada.

Estes testes não testam a internet nem o serviço do Google. Testam que o que o
Hub REGISTRA sobre o Stitch é consistente, verdadeiro e sem segredo — e que as
quatro distinções que o produto promete (catalogado, instalado, configurado,
operacional) não se colapsam num único "ok".
"""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.app import AgentHub
from lia_agenthub.domain.mcp import (
    DescritorInvalido, MCPServer, ler_descritor, varrer_segredos,
)

RAIZ = Path(__file__).resolve().parents[2]
STITCH = RAIZ / "docs/stitch"
CATALOGO = STITCH / "catalog/google-stitch.records.json"
DESCRITOR = STITCH / "mcp/google-stitch.mcp.json"


@pytest.fixture
def hub(tmp_path):
    return AgentHub(resolve_locations(tmp_path / "hub"))


# ==========================================================================
# Descritor MCP — o que o Hub registra e o que ele se recusa a registrar
# ==========================================================================
class TestDescritorMCP:
    def test_endpoint_e_transporte_oficiais(self):
        d = json.loads(DESCRITOR.read_text(encoding="utf-8"))
        srv = MCPServer.from_dict(d)
        assert srv.endpoint == "https://stitch.googleapis.com/mcp"
        # documentação oficial: HTTP (streamable). stdio/sse seriam errados.
        assert srv.transport == "http"
        assert srv.authentication == "api-key"

    def test_descreve_apenas_nome_do_cabecalho(self):
        """`X-Goog-Api-Key` é o NOME. O valor é do host, nunca do Hub."""
        d = json.loads(DESCRITOR.read_text(encoding="utf-8"))
        assert d["headers"] == ["X-Goog-Api-Key"]
        for valor in d["headers"]:
            assert "AIza" not in valor

    def test_descritor_versionado_nao_tem_segredo(self):
        bruto = DESCRITOR.read_text(encoding="utf-8")
        assert varrer_segredos(json.loads(bruto)) == []
        for padrao in ("AIza", "ya29.", "Bearer ", "eyJhbGci"):
            assert padrao not in bruto, padrao

    def test_conectividade_nunca_e_afirmada(self):
        """O Hub não conecta. Um campo que pudesse virar True aqui mentiria."""
        srv = MCPServer.from_dict({"endpoint": "https://x/mcp"})
        assert srv.as_dict()["connectivityVerified"] is False

    @pytest.mark.parametrize("transporte", ["stdio", "sse", "http", "HTTP"])
    def test_transportes_conhecidos_passam(self, transporte):
        srv = MCPServer.from_dict({"endpoint": "https://x/mcp", "transport": transporte})
        assert srv.transport == transporte.lower()

    def test_transporte_desconhecido_e_recusado_nao_adivinhado(self):
        with pytest.raises(DescritorInvalido):
            MCPServer.from_dict({"endpoint": "https://x/mcp", "transport": "carrier-pigeon"})

    def test_sem_endpoint_e_recusado(self):
        with pytest.raises(DescritorInvalido):
            MCPServer.from_dict({"transport": "http"})

    @pytest.mark.parametrize("segredo", [
        "AIza" + "a" * 35,
        "ya29." + "b" * 20,
        "Bearer abcdefghijkl",
        "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ4In0.assinatura",
    ])
    def test_credencial_no_descritor_recusa_o_recurso(self, hub, tmp_path, segredo):
        d = tmp_path / "mcp"
        d.mkdir()
        (d / "mcp.json").write_text(json.dumps(
            {"endpoint": "https://x/mcp", "headers": {"X-Goog-Api-Key": segredo}}),
            encoding="utf-8")
        r = hub.import_path(str(d))
        assert r.ok is False
        assert "credencial" in (r.blocked_reason or "").lower()

    def test_varredura_e_recursiva(self):
        """Segredo escondido em `tools` vaza igual que no topo."""
        achados = varrer_segredos({"tools": [{"auth": {"token": "eyJhbGciOiJ.abc.def"}}]})
        assert achados

    def test_mcp_json_vira_tipo_mcp_server(self, hub, tmp_path):
        d = tmp_path / "m"
        d.mkdir()
        (d / "mcp.json").write_text(json.dumps({
            "endpoint": "https://stitch.googleapis.com/mcp",
            "transport": "http", "authentication": "api-key",
            "headers": ["X-Goog-Api-Key"], "category": "UI/UX Design"}),
            encoding="utf-8")
        r = hub.import_path(str(d))
        assert r.ok
        assert r.resource_type == "mcp-server"
        det = hub.detail(r.capability_id)
        assert det["type"] == "mcp-server"
        assert det["mcp"]["endpoint"] == "https://stitch.googleapis.com/mcp"
        assert det["mcp"]["connectivityVerified"] is False

    def test_endpoint_entra_no_egress_declarado(self, hub, tmp_path):
        """O risco precisa enxergar o destino, não só o descritor."""
        d = tmp_path / "e"
        d.mkdir()
        (d / "mcp.json").write_text(json.dumps({"endpoint": "https://x.example/mcp"}),
                                    encoding="utf-8")
        r = hub.import_path(str(d))
        det = hub.detail(r.capability_id)
        assert det["egress"] == ["https://x.example/mcp"]
        assert "EGRESS" in [f["code"] for f in det["risk"]["factors"]]

    def test_skill_com_descritor_nao_perde_nem_ganha_tipo_em_silencio(self, hub, tmp_path):
        d = tmp_path / "ambos"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: ambos\ndescription: d\n---\n\nCorpo.\n", encoding="utf-8")
        (d / "mcp.json").write_text(json.dumps({"endpoint": "https://x/mcp"}),
                                    encoding="utf-8")
        r = hub.import_path(str(d))
        assert r.ok
        assert r.resource_type == "agent-skill"
        assert "MCP_DESCRIPTOR_IGNORED" in [i["code"] for i in r.issues]


# ==========================================================================
# Catálogo — gerado pelo importador real
# ==========================================================================
class TestCatalogoStitch:
    def _cat(self):
        assert CATALOGO.is_file(), "catálogo ausente"
        return json.loads(CATALOGO.read_text(encoding="utf-8"))

    def test_tem_16_skills_e_1_servidor(self):
        d = self._cat()
        tipos = [r["capability"]["type"] for r in d["records"]]
        assert tipos.count("agent-skill") == 16
        assert tipos.count("mcp-server") == 1
        assert d["failures"] == []

    def test_todo_registro_declara_origem_e_commit(self):
        d = self._cat()
        for r in d["records"]:
            prov = r["provenance"]
            assert prov["upstreamRepo"] == "https://github.com/google-labs-code/stitch-skills"
            assert d["source"]["commit"], "commit upstream não registrado"
            assert prov["upstream"], r["capability"]["name"]

    def test_hash_presente_e_verificavel(self):
        """Hash de 64 hex; não é assinatura e o registro não diz que é."""
        d = self._cat()
        for r in d["records"]:
            h = r["provenance"]["hashes"]["contentHash"]
            assert len(h) == 64 and all(c in "0123456789abcdef" for c in h), r["capability"]["name"]
            assert "signed" not in json.dumps(r).lower().replace("unsigned", "")

    def test_descricao_nunca_e_indicador_yaml(self):
        """O defeito que a importação de material real revelou."""
        d = self._cat()
        for r in d["records"]:
            desc = r["capability"]["description"]
            if r["capability"]["type"] == "mcp-server":
                continue
            assert desc not in (">-", "|", ">", ""), r["capability"]["name"]
            assert len(desc) >= 20, r["capability"]["name"]

    def test_namespace_preservado_quando_declarado(self):
        d = self._cat()
        com_ns = [r for r in d["records"] if r["capability"].get("namespace")]
        assert len(com_ns) == 8, "8 das 16 usam `stitch::` no upstream"
        for r in com_ns:
            assert r["capability"]["namespace"] == "stitch"
            assert "::" not in r["capability"]["name"]

    def test_nenhuma_credencial_no_catalogo(self):
        bruto = CATALOGO.read_text(encoding="utf-8")
        for padrao in ("AIza", "ya29.", "Bearer ", "eyJhbGci"):
            assert padrao not in bruto, padrao

    def test_licenca_registrada_como_declaracao_nao_permissao(self):
        d = self._cat()
        for r in d["records"]:
            assert r["capability"]["license"]["redistributable"] is False
        skills = [r for r in d["records"] if r["capability"]["type"] == "agent-skill"]
        for r in skills:
            ev = r["provenance"]["licenseEvidence"]
            assert ev["spdx"] == "Apache-2.0"
            assert ev["kind"] == "repository-root-LICENSE"
            # a Skill NÃO declara licença própria — e o registro diz isso
            assert "não trazem campo" in ev["note"]

    def test_catalogo_nao_carrega_payload_de_terceiros(self):
        """Só registro. Nenhum SKILL.md de terceiro entra no repositório."""
        d = self._cat()
        for r in d["records"]:
            assert "files" not in r["capability"]
            assert "payload" not in json.dumps(r)


# ==========================================================================
# Documentação — coerência e ausência de instrução inventada
# ==========================================================================
class TestDocumentacaoStitch:
    def test_docs_existem(self):
        for nome in ("MCP-SETUP.md", "CATALOG.md", "CODEX-AND-OTHER-HOSTS.md",
                     "workflow/lia-uiux-workflow.md", "handoff/README.md",
                     "design-brief-hub/README.md"):
            assert (STITCH / nome).is_file(), nome

    def test_mcp_setup_nao_contem_segredo(self):
        texto = (STITCH / "MCP-SETUP.md").read_text(encoding="utf-8")
        for padrao in ("AIza", "ya29."):
            assert padrao not in texto, padrao
        assert "<SUA_CHAVE>" in texto

    def test_nenhum_documento_inventa_comando_cli(self):
        """`codex plugin install` não existe na doc oficial. Não documentamos."""
        for arq in STITCH.rglob("*.md"):
            texto = arq.read_text(encoding="utf-8")
            for linha in texto.splitlines():
                if "codex plugin install" in linha and not linha.lstrip().startswith((">", "  ")):
                    pytest.fail(f"comando não verificado em {arq.name}: {linha.strip()}")

    def test_catalogo_md_concorda_com_json(self):
        """CATALOG.md é renderizado do JSON; divergência é defeito."""
        md = (STITCH / "CATALOG.md").read_text(encoding="utf-8")
        d = json.loads(CATALOGO.read_text(encoding="utf-8"))
        for r in d["records"]:
            assert f"`{r['capability']['name']}`" in md, r["capability"]["name"]
        assert f"{len(d['records'])}" in md

    def test_workflow_cobre_as_sete_etapas(self):
        texto = (STITCH / "workflow/lia-uiux-workflow.md").read_text(encoding="utf-8")
        for etapa in ("Discovery", "Design brief", "Prompt engineering",
                      "Design generation", "Design validation", "Handoff",
                      "Implementation feedback"):
            assert etapa in texto, etapa

    def test_workflow_declara_precedencia_do_produto(self):
        """O mockup nunca manda mais que o contrato."""
        texto = (STITCH / "workflow/lia-uiux-workflow.md").read_text(encoding="utf-8")
        assert "fonte da verdade **funcional e arquitetural**" in texto

    def test_handoff_define_precedencia(self):
        texto = (STITCH / "handoff/README.md").read_text(encoding="utf-8")
        assert "Requisito e contrato do produto" in texto
        assert "o mockup está errado" in texto

    def test_prompts_do_hub_nao_inventam_funcionalidade(self):
        """Toda tela do brief corresponde a rota real do servidor."""
        server = (RAIZ / "src/lia_agenthub/interface/server.py").read_text(encoding="utf-8")
        ia = (STITCH / "design-brief-hub/02-INFORMATION-ARCHITECTURE.md").read_text(encoding="utf-8")
        import re
        citadas = set(re.findall(r"/api/[a-z-]+(?:/<id>)?", ia))
        assert citadas, "o brief não cita rota nenhuma"
        for rota in citadas:
            base = rota.replace("/<id>", "")
            assert base in server, f"o brief cita rota inexistente: {rota}"

    def test_relatorio_de_integracao_existe_e_nao_cita_arquivo_fantasma(self):
        """Docs que apontam para arquivo inexistente mentem em silêncio."""
        rel = RAIZ / "docs/operations/STITCH-INTEGRATION-REPORT.md"
        assert rel.is_file()
        texto = rel.read_text(encoding="utf-8")
        import re
        for caminho in set(re.findall(r"`((?:docs|src|tests)/[A-Za-z0-9/_.-]+\.(?:md|py|json))`", texto)):
            if caminho.endswith("SKILL-CATALOG-IMPORT-REPORT.md"):
                # Existe, mas fora desta branch — o relatório é obrigado a dizer isso.
                assert "não existe nesta branch" in texto, caminho
                continue
            assert (RAIZ / caminho).exists(), f"relatório cita caminho inexistente: {caminho}"

    def test_brief_avisa_que_nao_houve_acesso_ao_mcp(self):
        """Não simular conexão: o brief diz o que aconteceu de fato."""
        texto = (STITCH / "design-brief-hub/README.md").read_text(encoding="utf-8")
        assert "não houve" in texto.lower() and "acesso autenticado" in texto.lower()


class TestThirdPartyNotices:
    """A obrigação de licença não pode ficar desatualizada em silêncio."""

    def _texto(self):
        return (RAIZ / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    def test_registra_o_stitch(self):
        texto = self._texto()
        assert "google-labs-code/stitch-skills" in texto
        assert "Apache-2.0" in texto
        assert "0337446dadde" in texto

    def test_declara_que_nada_foi_incorporado(self):
        texto = self._texto()
        assert "por referência, não por cópia" in texto

    def test_nao_afirma_licenca_do_servico(self):
        """O serviço é regido pelos ToS do Google; não inventamos licença."""
        texto = self._texto()
        assert "Google APIs Terms of Service" in texto

    def test_comando_de_verificacao_antigo_esta_marcado_como_historico(self):
        """O comando da Fase 0.1 devolve 68 arquivos hoje. Marcá-lo é obrigatório."""
        texto = self._texto()
        assert "não é mais um teste válido" in texto

    def test_nao_declara_nenhuma_licenca_para_o_projeto(self):
        """D-16 continua aberta: este arquivo não escolhe licença."""
        texto = self._texto()
        assert "D-16" in texto


# ==========================================================================
# Fronteiras — o Hub não conecta, não executa, não guarda
# ==========================================================================
class TestFronteirasStitch:
    def test_importar_skill_com_script_nao_executa(self, hub, tmp_path):
        d = tmp_path / "com-script"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: com-script\ndescription: d\n---\n\nCorpo.\n", encoding="utf-8")
        marcador = tmp_path / "EXECUTOU"
        (d / "run.sh").write_text(f"#!/bin/sh\ntouch {marcador}\n", encoding="utf-8")
        r = hub.import_path(str(d))
        assert r.ok
        assert r.contains_scripts is True
        assert not marcador.exists()

    def test_exportar_mcp_leva_o_descritor_sem_segredo(self, hub, tmp_path):
        d = tmp_path / "m"
        d.mkdir()
        (d / "mcp.json").write_text(json.dumps({
            "endpoint": "https://stitch.googleapis.com/mcp",
            "transport": "http", "authentication": "api-key",
            "headers": ["X-Goog-Api-Key"]}), encoding="utf-8")
        r = hub.import_path(str(d))
        hub.promote(r.capability_id)
        e = hub.export(r.capability_id, target="private",
                       destination=str(tmp_path / "out"))
        zf = zipfile.ZipFile(e["path"])
        assert "payload/mcp.json" in zf.namelist()
        bruto = zf.read("payload/mcp.json").decode()
        assert "AIza" not in bruto

    def test_hub_nao_faz_chamada_de_rede_na_importacao(self, hub, tmp_path, monkeypatch):
        """Prova ativa: qualquer socket aberto durante a importação falha."""
        import socket

        def proibido(*a, **k):
            raise AssertionError("o Hub tentou abrir conexão de rede")

        monkeypatch.setattr(socket.socket, "connect", proibido)
        monkeypatch.setattr(socket, "create_connection", proibido)
        d = tmp_path / "s"
        d.mkdir()
        (d / "SKILL.md").write_text(
            "---\nname: s\ndescription: d\n---\n\nCorpo.\n", encoding="utf-8")
        (d / "mcp.json").write_text(json.dumps({"endpoint": "https://stitch.googleapis.com/mcp"}),
                                    encoding="utf-8")
        r = hub.import_path(str(d))
        assert r.ok
