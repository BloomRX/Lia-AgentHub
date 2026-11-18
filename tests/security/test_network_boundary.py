"""Fronteira de rede — o que o Hub PODE e NÃO PODE garantir.

O relatório de validação Windows mediu conexões externas de processos
`msedgewebview2.exe` com o Hub aberto (D-09). Isso motivou uma distinção que
o produto precisa manter honestamente:

    rede do APLICATIVO      -> o Hub não abre nenhuma. Provado aqui.
    rede do RUNTIME WebView2 -> é do navegador. Reduzida por argumentos,
                                NÃO provada zero. Documentada como aberta.

Estes testes provam a primeira e verificam que a segunda não é declarada
como resolvida. Não é permitido "resolver" D-09 afrouxando o critério.
"""
from __future__ import annotations

import json
import socket
import sys
from pathlib import Path

import pytest

from lia_agenthub.adapters import platform_check as pc
from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.app import AgentHub

RAIZ = Path(__file__).resolve().parents[2]


@pytest.fixture
def hub(tmp_path):
    return AgentHub(resolve_locations(tmp_path / "hub"))


def _skill(base: Path, nome="fronteira") -> Path:
    d = base / nome
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {nome}\ndescription: teste de fronteira\n---\n\nCorpo.\n",
        encoding="utf-8")
    return d


class TestAppNaoFazRede:
    """Prova ativa: qualquer socket aberto durante operação normal falha."""

    @pytest.fixture
    def sem_rede(self, monkeypatch):
        def proibido(*a, **k):
            raise AssertionError("o Hub tentou abrir conexão de rede")
        monkeypatch.setattr(socket.socket, "connect", proibido)
        monkeypatch.setattr(socket.socket, "connect_ex", proibido)
        monkeypatch.setattr(socket, "create_connection", proibido)
        monkeypatch.setattr(socket, "getaddrinfo", proibido)
        return proibido

    def test_importacao_completa_sem_rede(self, hub, tmp_path, sem_rede):
        d = _skill(tmp_path)
        r = hub.import_path(str(d))
        assert r.ok

    def test_promocao_e_validacao_sem_rede(self, hub, tmp_path, sem_rede):
        d = _skill(tmp_path)
        r = hub.import_path(str(d))
        hub.promote(r.capability_id)
        hub.validate(r.capability_id)

    def test_exportacao_sem_rede(self, hub, tmp_path, sem_rede):
        d = _skill(tmp_path)
        r = hub.import_path(str(d))
        hub.promote(r.capability_id)
        saida = hub.export(r.capability_id, target="private",
                           destination=str(tmp_path / "out"))
        assert saida["ok"]

    def test_publicacao_de_indice_sem_rede(self, hub, tmp_path, sem_rede):
        d = _skill(tmp_path)
        r = hub.import_path(str(d))
        hub.promote(r.capability_id)
        assert hub.publish_index()["ok"]

    def test_diagnostico_sem_rede(self, hub, sem_rede):
        info = hub.diagnostics()
        assert info["environment"]["frozen"] in (True, False)

    def test_importacao_de_zip_sem_rede(self, hub, tmp_path, sem_rede):
        import zipfile
        pacote = tmp_path / "p.zip"
        with zipfile.ZipFile(pacote, "w") as z:
            z.writestr("SKILL.md",
                       "---\nname: zipeado\ndescription: via zip\n---\n\nCorpo.\n")
        assert hub.import_path(str(pacote)).ok


class TestControleDeRedeWebView2:
    def test_argumentos_incluem_desligamento_de_recursos(self):
        args = pc.argumentos_windows_rede()
        for recurso in ("--disable-background-networking",
                        "--disable-component-update",
                        "--disable-domain-reliability",
                        "--disable-sync",
                        "--no-first-run"):
            assert recurso in args, recurso
        assert "--disable-features=" in args

    def test_argumentos_nao_contem_nada_que_quebre_a_ui_local(self):
        """`--disable-web-security`, `--allow-file-access` etc. seriam errados
        aqui: enfraqueceriam a janela em nome de "menos rede"."""
        args = pc.argumentos_windows_rede()
        for perigoso in ("--disable-web-security", "--allow-file-access-from-files",
                         "--disable-features=A11y", "--no-sandbox"):
            assert perigoso not in args, perigoso

    def test_aplica_apenas_no_windows(self, monkeypatch):
        monkeypatch.setattr(pc.sys, "platform", "linux")
        env = {}
        r = pc.aplicar_controle_de_rede(env)
        assert r["applied"] is False
        assert env == {}

    def test_aplica_no_windows(self, monkeypatch):
        monkeypatch.setattr(pc.sys, "platform", "win32")
        env = {}
        r = pc.aplicar_controle_de_rede(env)
        assert r["applied"] is True
        assert env[pc.ENV_BROWSER_ARGS] == pc.argumentos_windows_rede()

    def test_nao_sobrescreve_valor_existente(self, monkeypatch):
        """Sobrescrever argumento de suporte/depuração quebra a janela de um
        jeito difícil de diagnosticar. Preservar e registrar é mais seguro."""
        monkeypatch.setattr(pc.sys, "platform", "win32")
        env = {pc.ENV_BROWSER_ARGS: "--remote-debugging-port=9222"}
        r = pc.aplicar_controle_de_rede(env)
        assert r["applied"] is False
        assert env[pc.ENV_BROWSER_ARGS] == "--remote-debugging-port=9222"
        assert "preservado" in r["reason"]

    def test_resumo_nao_promete_zero_egress(self):
        """A frase que impede a regressão de critério."""
        texto = pc.resumo_controle_de_rede({"applied": True, "reason": "", "arguments": "x"})
        assert "NÃO é firewall" in texto
        assert "zero egress" in texto
        assert "medição" in texto


class TestDiagnosticoNaoMenteSobreRede:
    def test_relata_controle_ativo_ou_inativo(self, hub):
        dados = hub.diagnostics()["environment"]["webview2_network"]
        assert dados["envVar"] == pc.ENV_BROWSER_ARGS
        assert isinstance(dados["active"], bool)
        # Ausência de controle NÃO é sucesso: o campo precisa existir sempre.
        assert "notAFirewall" in dados

    def test_escopo_separa_app_de_runtime(self, hub):
        dados = hub.diagnostics()["environment"]["webview2_network"]
        assert "runtime do navegador" in dados["scope"]
        assert "não a rede do app" in dados["scope"]

    def test_notas_dizem_que_nao_e_prova(self, hub):
        notas = hub.diagnostics()["environment"]["notes"]
        assert "não substitui medição" in notas

    def test_diagnostico_nao_atribui_egress_ao_app(self, hub):
        """O app não pode se declarar fonte de tráfego que ele não faz."""
        notas = hub.diagnostics()["environment"]["notes"]
        assert "O Hub não envia dados para fora" in notas


class TestD09ContinuaAberto:
    """Guarda de honestidade: o defeito não pode ser fechado no documento."""

    def test_relatorio_windows_mantem_d09_documentado(self):
        rel = (RAIZ / "docs/operations/WINDOWS-VALIDATION-REPORT.md")
        texto = rel.read_text(encoding="utf-8")
        assert "D-09" in texto
        # Se alguém "resolver" mudando o critério, este teste cai.
        assert "Nenhuma VM Windows limpa" in texto or "BLOQUEADO" in texto

    def test_plano_nao_foi_relaxado(self):
        plano = (RAIZ / "docs/operations/WINDOWS-VALIDATION-AND-BUILD-PLAN.md").read_text(encoding="utf-8")
        assert "nenhuma conexão de saída" in plano.lower()
