"""Interface local — navegação, estados vazios, erros, acessibilidade.

Testa o SERVIDOR e os ATIVOS estáticos. Não abre navegador: aqui não há
WebView2. O que exige renderização real está marcado e não é afirmado.
"""
import json
import re
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from lia_agenthub.interface.server import create_server


@pytest.fixture
def server(hub):
    httpd, token = create_server(hub)
    import threading
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    yield base, token
    httpd.shutdown()
    httpd.server_close()


def call(base, token, path, *, method="GET", body=None, headers=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    if token is not None:
        req.add_header("X-Lia-Token", token)
    if data:
        req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


# ---------------- acessibilidade estática dos ativos ----------------
def test_pagina_declara_idioma():
    html = (Path("src/lia_agenthub/resources/static/index.html")).read_text(encoding="utf-8")
    assert 'lang="pt-BR"' in html


def test_pagina_tem_titulo_e_charset():
    html = Path("src/lia_agenthub/resources/static/index.html").read_text(encoding="utf-8")
    assert "<title>" in html
    assert 'charset="utf-8"' in html


def test_link_de_pular_para_conteudo_existe():
    html = Path("src/lia_agenthub/resources/static/index.html").read_text(encoding="utf-8")
    assert 'class="skip"' in html
    assert 'href="#main"' in html


def test_todo_input_tem_rotulo():
    html = Path("src/lia_agenthub/resources/static/index.html").read_text(encoding="utf-8")
    for element_id in ("search", "ftype", "ftrust", "ftag", "ipath", "vpath"):
        tem_label = re.search(rf'<label[^>]*\bfor="{element_id}"', html)
        tem_aria = re.search(rf'<input[^>]*\bid="{element_id}"[^>]*aria-label', html)
        assert tem_label or tem_aria, f"campo sem rótulo: {element_id}"


def test_areas_principais_sao_landmarks():
    html = Path("src/lia_agenthub/resources/static/index.html").read_text(encoding="utf-8")
    assert html.count("<main") == 1
    assert "<nav" in html
    assert "<header" in html
    assert "<footer" in html


def test_regiao_anunciada_para_leitor_de_tela():
    html = Path("src/lia_agenthub/resources/static/index.html").read_text(encoding="utf-8")
    assert 'aria-live' in html
    assert 'role="status"' in html


def test_css_respeita_movimento_reduzido():
    css = Path("src/lia_agenthub/resources/static/app.css").read_text(encoding="utf-8")
    assert "prefers-reduced-motion" in css


def test_css_tem_foco_visivel():
    css = Path("src/lia_agenthub/resources/static/app.css").read_text(encoding="utf-8")
    assert "focus-visible" in css


def test_js_nao_usa_eval_nem_html_cru():
    js = Path("src/lia_agenthub/resources/static/app.js").read_text(encoding="utf-8")
    assert "eval(" not in js
    assert "innerHTML" not in js
    assert "document.write" not in js


# ---------------- servidor ----------------
def test_raiz_serve_a_interface(server):
    base, token = server
    code, body = call(base, None, "/")
    assert code == 200
    assert b"Lia Agent Hub" in body


def test_token_de_sessao_e_injetado_na_pagina(server):
    base, token = server
    _, body = call(base, None, "/")
    assert token.encode() in body


def test_sem_token_a_api_recusa(server):
    base, _ = server
    assert call(base, None, "/api/items")[0] == 403


def test_token_errado_recusa(server):
    base, _ = server
    assert call(base, "errado", "/api/items")[0] == 403


def test_origem_externa_e_recusada(server):
    base, token = server
    code, _ = call(base, token, "/api/items", headers={"Origin": "https://evil.example"})
    assert code == 403


def test_origem_local_e_aceita(server):
    base, token = server
    code, _ = call(base, token, "/api/items",
                   headers={"Origin": f"http://127.0.0.1:{base.rsplit(':', 1)[1]}"})
    assert code == 200


def test_host_estranho_e_recusado(server):
    base, token = server
    assert call(base, token, "/api/items", headers={"Host": "evil.example"})[0] == 403


def test_cabecalhos_de_seguranca_presentes(server):
    base, _ = server
    req = urllib.request.Request(base + "/")
    with urllib.request.urlopen(req) as r:
        h = r.headers
    assert "Content-Security-Policy" in h
    assert "frame-ancestors 'none'" in h["Content-Security-Policy"]
    assert h["X-Frame-Options"] == "DENY"
    assert h["X-Content-Type-Options"] == "nosniff"


def test_traversal_em_estatico_e_bloqueado(server):
    base, _ = server
    assert call(base, None, "/static/../../__main__.py")[0] in (400, 404)


def test_rota_desconhecida_da_404(server):
    base, token = server
    assert call(base, token, "/api/nao-existe")[0] == 404


def test_json_invalido_da_400_com_dica(server):
    base, token = server
    req = urllib.request.Request(base + "/api/import", data=b"{lixo", method="POST")
    req.add_header("X-Lia-Token", token)
    req.add_header("Content-Type", "application/json")
    try:
        urllib.request.urlopen(req)
        pytest.fail("deveria ter recusado")
    except urllib.error.HTTPError as e:
        assert e.code == 400
        corpo = json.loads(e.read())
        assert corpo["error"]


# ---------------- estados vazios e dados ----------------
def test_biblioteca_vazia_responde_lista_vazia(server):
    base, token = server
    code, body = call(base, token, "/api/items")
    assert code == 200
    assert json.loads(body)["items"] == []


def test_quarentena_vazia_responde_lista_vazia(server):
    base, token = server
    assert json.loads(call(base, token, "/api/quarantine")[1])["items"] == []


def test_diagnostico_traz_caminhos(server):
    base, token = server
    d = json.loads(call(base, token, "/api/diagnostics")[1])
    for chave in ("library", "quarantine", "exports", "common", "logs"):
        assert d["paths"][chave]


def test_diagnostico_nao_expoe_segredo(server):
    base, token = server
    corpo = call(base, token, "/api/diagnostics")[1].decode()
    assert token not in corpo
    assert "password" not in corpo.lower()


def test_importacao_pela_api(server, skill_dir):
    base, token = server
    code, body = call(base, token, "/api/import", method="POST",
                      body={"path": str(skill_dir)})
    assert code == 200
    r = json.loads(body)
    assert r["ok"]
    assert r["capabilityId"]


def test_detalhe_pela_api(server, skill_dir):
    base, token = server
    r = json.loads(call(base, token, "/api/import", method="POST",
                        body={"path": str(skill_dir)})[1])
    code, body = call(base, token, f"/api/items/{r['capabilityId']}")
    assert code == 200
    d = json.loads(body)
    assert d["name"]
    assert d["risk"]["disclaimer"]


def test_erro_de_importacao_volta_legivel(server):
    base, token = server
    r = json.loads(call(base, token, "/api/import", method="POST",
                        body={"path": "/nao/existe/mesmo"})[1])
    assert r["ok"] is False
    assert r["blockedReason"]
    assert r["hint"]


def test_capacidade_inexistente_da_400(server):
    base, token = server
    code, _ = call(base, token, "/api/items/nao-existe-000")
    assert code == 400


def test_fluxo_completo_pela_api(server, skill_dir):
    base, token = server
    r = json.loads(call(base, token, "/api/import", method="POST",
                        body={"path": str(skill_dir)})[1])
    cid = r["capabilityId"]
    assert json.loads(call(base, token, "/api/promote", method="POST",
                           body={"id": cid})[1])["lifecycle"] == "active"
    assert json.loads(call(base, token, "/api/validate", method="POST",
                           body={"id": cid})[1])["summary"]["error"] == 0
    assert json.loads(call(base, token, "/api/publish-index", method="POST",
                           body={})[1])["count"] == 1
    exportado = json.loads(call(base, token, "/api/export", method="POST",
                                body={"id": cid, "target": "private"})[1])
    assert exportado["ok"]
    verificado = json.loads(call(base, token, "/api/verify-package", method="POST",
                                 body={"path": exportado["path"]})[1])
    assert verificado["ok"]
