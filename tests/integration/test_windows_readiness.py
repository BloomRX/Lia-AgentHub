"""Preparação para Windows — o que é verificável fora do Windows.

Estes testes travam comportamentos que QUEBRAM especificamente no Windows e
que passariam despercebidos em Linux/macOS. Cada um aponta o motivo.
"""
import os
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from lia_agenthub.adapters import atomic
from lia_agenthub.adapters.paths_resolver import resolve_locations
from lia_agenthub.app import AgentHub
from lia_agenthub.interface.server import _LocalServer, create_server


# ---------------- escrita atômica ----------------
def test_escrita_atomica_sobrevive_a_bloqueio_temporario(tmp_path):
    """No Windows, antivírus segura o destino por instantes: PermissionError.

    O comportamento esperado é: repetir até conseguir. Em POSIX não há retry.
    """
    alvo = tmp_path / "x.json"
    atomic.atomic_write_json(alvo, {"v": 1})

    real = os.replace
    estado = {"n": 0}

    def alterna(src, dst):
        estado["n"] += 1
        if estado["n"] <= 2:
            raise PermissionError(13, "ocupado", str(dst))
        return real(src, dst)

    with patch.object(atomic, "_REPLACE_ATTEMPTS", 5), \
         patch.object(atomic, "_REPLACE_DELAY", 0.001), \
         patch("os.replace", alterna):
        atomic.atomic_write_json(alvo, {"v": 2})

    assert alvo.read_text(encoding="utf-8").strip().startswith("{")
    assert '"v": 2' in alvo.read_text(encoding="utf-8")


def test_escrita_atomica_propaga_falha_permanente(tmp_path):
    """Se for sempre bloqueado, o erro sobe — não mascara."""
    alvo = tmp_path / "y.json"
    atomic.atomic_write_json(alvo, {"v": 1})
    anterior = alvo.read_text(encoding="utf-8")

    def sempre_falha(src, dst):
        raise PermissionError(13, "ocupado", str(dst))

    with patch.object(atomic, "_REPLACE_ATTEMPTS", 3), \
         patch.object(atomic, "_REPLACE_DELAY", 0.001), \
         patch("os.replace", sempre_falha):
        with pytest.raises(PermissionError):
            atomic.atomic_write_json(alvo, {"v": 2})

    assert alvo.read_text(encoding="utf-8") == anterior, "o antigo deve sobreviver"
    assert not [p for p in tmp_path.iterdir() if ".part" in p.name], "sem órfão"


def test_retry_so_existe_no_windows():
    """Em POSIX, repetir não faz sentido e só atrasaria o erro."""
    esperado = 5 if sys.platform == "win32" else 1
    assert atomic._REPLACE_ATTEMPTS == esperado


# ---------------- servidor local ----------------
def test_servidor_nao_permite_segundo_bind_na_mesma_porta():
    """Exclusividade: outra instância não pode responder no lugar do Hub."""
    hub = AgentHub(resolve_locations(Path(tempfile.mkdtemp()) / "h"))
    a, _ = create_server(hub)
    porta = a.server_address[1]
    try:
        with pytest.raises(OSError):
            create_server(hub, port=porta)
    finally:
        a.server_close()


def test_servidor_usa_exclusive_addr_no_windows(monkeypatch):
    """Verifica a CHAMADA correta de setsockopt, sem precisar de Windows."""
    chamadas = []

    class SockFalso:
        def setsockopt(self, nivel, opcao, valor):
            chamadas.append((nivel, opcao, valor))

    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setattr(socket, "SO_EXCLUSIVEADDRUSE", 0xDEAD, raising=False)

    # objeto mínimo que se comporta como o servidor no que o método usa
    class Falso:
        socket = SockFalso()
        server_bind = _LocalServer.server_bind.__get__(object(), object)

    with patch("socketserver.TCPServer.server_bind", lambda self: None):
        _LocalServer.server_bind(Falso())

    assert any(op == 0xDEAD for _, op, _ in chamadas), (
        f"SO_EXCLUSIVEADDRUSE não foi aplicado: {chamadas}")


def test_servidor_escuta_apenas_em_loopback():
    """O Hub é local: jamais 0.0.0.0."""
    hub = AgentHub(resolve_locations(Path(tempfile.mkdtemp()) / "h"))
    httpd, _ = create_server(hub)
    try:
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()


def test_encerramento_libera_a_porta():
    hub = AgentHub(resolve_locations(Path(tempfile.mkdtemp()) / "h"))
    httpd, _ = create_server(hub)
    porta = httpd.server_address[1]
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    httpd.shutdown()
    httpd.server_close()
    t.join(timeout=3)

    assert not t.is_alive()
    with socket.socket() as s:
        s.settimeout(1)
        assert s.connect_ex(("127.0.0.1", porta)) != 0, "porta ainda escutando"


# ---------------- caminhos no Windows ----------------
def test_caminho_longo_e_recusado_antes_de_falhar_no_windows():
    from lia_agenthub.domain.paths import MAX_PATH_LEN, check_relative_path
    longo = "/".join(["a" * 40] * 6) + "/x.md"
    assert len(longo) > MAX_PATH_LEN
    assert not check_relative_path(longo).ok


def test_nome_com_unicode_e_preservado(hub, tmp_path):
    d = tmp_path / "ação-e-coração"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: acao-e-coracao\ndescription: Ação e coração\n---\n\nCorpo.\n",
        encoding="utf-8")
    r = hub.import_path(str(d))
    assert r.ok
    assert hub.promote(r.capability_id)


def test_arquivo_gravado_e_lido_como_utf8(hub, tmp_path):
    """cp1252 no Windows corromperia acentos se o encoding não fosse explícito."""
    d = tmp_path / "acentos"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: acentos\ndescription: Coração, ação, informações\n---\n\nCorpo.\n",
        encoding="utf-8")
    r = hub.import_path(str(d))
    conteudo = hub.repo.payload_files(r.capability_id)["SKILL.md"].decode("utf-8")
    assert "Coração" in conteudo


# ---------------- independência do diretório de trabalho ----------------
def test_ui_resolve_sem_depender_do_cwd(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    locs = resolve_locations()
    assert (locs.resources / "static" / "index.html").is_file()


def test_dados_do_usuario_ficam_fora_dos_arquivos_da_aplicacao(tmp_path):
    """A biblioteca nunca deve cair dentro de site-packages ou do _MEIPASS."""
    locs = resolve_locations(tmp_path / "home")
    app_src = Path(__file__).resolve().parents[2] / "src"
    assert not str(locs.library.resolve()).startswith(str(app_src.resolve()))
    assert not str(locs.quarantine.resolve()).startswith(str(app_src.resolve()))
