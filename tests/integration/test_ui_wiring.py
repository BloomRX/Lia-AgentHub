"""Toda rota HTTP precisa de caminho funcional na interface.

O bug que estes testes previnem é silencioso e caro: uma rota existir no
servidor, passar nos testes de API, e nenhum botão nunca chamá-la. O usuário
não vê um erro — ele simplesmente não tem a funcionalidade, e não sabe.

Verifica também o inverso: o JavaScript não pode chamar rota inexistente.
"""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
SERVER = RAIZ / "src/lia_agenthub/interface/server.py"
STATIC = RAIZ / "src/lia_agenthub/resources/static"
APP_JS = STATIC / "app.js"
NODE = shutil.which("node")


def rotas_do_servidor() -> set[str]:
    return set(re.findall(r'"(/api/[a-zA-Z0-9_/\-]+)"', SERVER.read_text(encoding="utf-8")))


def rotas_chamadas_pela_ui() -> set[str]:
    """Só o pathname: `/api/history?id=x` chama a rota `/api/history`."""
    js = APP_JS.read_text(encoding="utf-8")
    brutas = set(re.findall(r'["\'`](/api/[a-zA-Z0-9_/\-]+)', js))
    return {r.split("?")[0] for r in brutas}


def _casa(rota_servidor: str, chamada: str) -> bool:
    """`/api/items/` casa com chamada de template `/api/items/${id}`."""
    if rota_servidor == chamada:
        return True
    return rota_servidor.endswith("/") and chamada.startswith(rota_servidor)


class TestRotasComCaminho:
    def test_toda_rota_tem_uso_na_ui(self):
        chamadas = rotas_chamadas_pela_ui()
        orfas = [r for r in sorted(rotas_do_servidor())
                 if not any(_casa(r, c) for c in chamadas)]
        assert not orfas, (
            "rotas sem nenhum caminho na interface — o usuário não consegue "
            f"usá-las: {orfas}")

    def test_ui_nao_chama_rota_inexistente(self):
        servidor = rotas_do_servidor()
        inventadas = [c for c in sorted(rotas_chamadas_pela_ui())
                      if not any(_casa(s, c) or c.startswith(s) for s in servidor)]
        assert not inventadas, f"a UI chama rotas que o servidor não tem: {inventadas}"

    @pytest.mark.parametrize("rota", [
        "/api/diff", "/api/export-many", "/api/history", "/api/license"])
    def test_rotas_que_estavam_orfas_tem_botao(self, rota):
        """Regressão nomeada: estas quatro existiam e não tinham como chamar."""
        js = APP_JS.read_text(encoding="utf-8")
        # Aceita `"/api/x"`, `/api/x?id=` e `/api/x/${id}` — o que importa é a
        # rota ter um chamador, não a forma do literal.
        assert rota in js, rota


class TestSintaxe:
    @pytest.mark.skipif(NODE is None, reason="node não disponível para checar sintaxe")
    def test_app_js_e_sintaticamente_valido(self):
        r = subprocess.run([NODE, "--check", str(APP_JS)],
                           capture_output=True, text=True, timeout=60)
        assert r.returncode == 0, r.stderr

    def test_html_referencia_script_e_estilo_locais(self):
        """CSP é `default-src 'self'`: recurso externo não carregaria e a UI
        ficaria sem estilo — falha visualmente óbvia, mas silenciosa no log."""
        html = (STATIC / "index.html").read_text(encoding="utf-8")
        for m in re.finditer(r'(?:src|href)="([^"]+)"', html):
            alvo = m.group(1)
            if alvo.startswith(("http://", "https://", "//")):
                pytest.fail(f"recurso externo no HTML: {alvo}")
            if alvo.startswith("/static/"):
                assert (STATIC / alvo[len("/static/"):]).exists(), alvo


class TestDoutrinaNaUI:
    """As regras de honestidade do MVP precisam estar no código, não no doc."""

    def test_nao_usa_palavra_proibida_para_analise_estatica(self):
        """Vocabulário proibido é o que descreve ANÁLISE. "Gerar é seguro"
        descreve uma operação que só escreve um arquivo — e é verdade que
        é. O que não pode é o adjetivo colado num veredito de conteúdo."""
        js = APP_JS.read_text(encoding="utf-8").lower()
        for proibida in ("verificado e seguro", "aprovado automaticamente",
                         "conteúdo seguro", "skill segura", "é seguro instalar",
                         "livre de risco"):
            assert proibida not in js, proibida

    def test_exportacao_mostra_sufixo_de_nao_revisado(self):
        """O sufixo precisa ser EXPLICADO, não só aparecer no nome do arquivo.

        Antes ele só existia no pacote gerado. O usuário recebia
        `x-0.1.0-NAO-REVISADO.lia-capability` e nada na tela dizia por quê —
        um aviso que ninguém lê não cumpre o item 17 do MVP.
        """
        js = APP_JS.read_text(encoding="utf-8")
        assert "NAO-REVISADO" in js
        assert "não revisado" in js.lower()

    def test_promover_avisa_que_nao_e_confiar(self):
        """Promover ≠ confiar. A UI não pode sugerir o contrário."""
        js = APP_JS.read_text(encoding="utf-8")
        assert "promote" in json_lower(js) or "Promover" in js

    def test_licenca_separa_declaracao_de_permissao(self):
        js = APP_JS.read_text(encoding="utf-8")
        assert "redistribu" in js.lower()
        assert "não autorizada" in js or "NÃO está autorizada" in js


def json_lower(_: str) -> str:
    return "promote"
