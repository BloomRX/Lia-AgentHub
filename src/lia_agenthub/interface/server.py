"""Servidor local — 127.0.0.1 apenas, token de sessão, Origin validado.

Quatro controles obrigatórios (PLATFORM §5.5.6), nenhum automático:
  1. bind exclusivo em 127.0.0.1
  2. token de sessão exigido em toda requisição de API
  3. Origin/Host validados — sem CORS permissivo
  4. porta efêmera, URL real injetada na janela

Isto é interface local, NÃO é API de integração. O contrato de integração
do MVP é arquivo em disco (index.json), não HTTP.
"""
from __future__ import annotations

import json
import logging
import socket
import socketserver
import sys
import mimetypes
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from ..app import AgentHub, SearchQuery
from ..domain.errors import LiaError

log = logging.getLogger("lia_agenthub.http")

ALLOWED_HOSTS = {"127.0.0.1", "localhost"}


class Handler(BaseHTTPRequestHandler):
    server_version = "LiaAgentHub/0.1"
    sys_version = ""

    hub: AgentHub = None          # injetado
    token: str = ""               # injetado
    resources: Path = None        # injetado

    # ---- utilidades ------------------------------------------------------
    def _host_ok(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ALLOWED_HOSTS

    def _origin_ok(self) -> bool:
        origin = self.headers.get("Origin")
        if origin is None:
            return True  # requisição same-origin de navegador não envia Origin
        parsed = urlparse(origin)
        return parsed.hostname in ALLOWED_HOSTS

    def _token_ok(self) -> bool:
        supplied = self.headers.get("X-Lia-Token") or ""
        return secrets.compare_digest(supplied, self.token)

    def _send(self, code: int, body: bytes, ctype: str = "application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        # CSP: nada de script remoto, nada de eval. A UI é local e estática.
        self.send_header("Content-Security-Policy",
                         "default-src 'self'; script-src 'self'; style-src 'self' "
                         "'unsafe-inline'; img-src 'self' data:; connect-src 'self'; "
                         "frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
        self.send_header("X-Frame-Options", "DENY")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code: int = 200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def _error(self, message: str, hint: str = "", code: int = 400):
        self._json({"error": message, "hint": hint}, code)

    def log_message(self, fmt, *args):
        log.debug("%s - %s", self.address_string(), fmt % args)

    # ---- roteamento ------------------------------------------------------
    def do_GET(self):
        if not self._host_ok() or not self._origin_ok():
            self._error("Origem não autorizada.", "O Hub só atende a máquina local.", 403)
            return

        url = urlparse(self.path)
        path = url.path

        if path == "/":
            return self._serve_static("static/index.html")
        if path.startswith("/static/"):
            return self._serve_static("static/" + path[len("/static/"):])

        if not path.startswith("/api/"):
            self._error("Não encontrado.", "", 404)
            return
        if not self._token_ok():
            self._error("Token de sessão inválido.", "Recarregue a página.", 403)
            return

        try:
            self._route_get(path, parse_qs(url.query))
        except LiaError as e:
            self._json({**e.as_dict()}, 400)
        except Exception:
            log.exception("erro em GET %s", path)
            self._error("Falha interna.", "Veja o log em Diagnóstico.", 500)

    def do_POST(self):
        if not self._host_ok() or not self._origin_ok():
            self._error("Origem não autorizada.", "", 403)
            return
        if not self._token_ok():
            self._error("Token de sessão inválido.", "Recarregue a página.", 403)
            return
        if not self.path.startswith("/api/"):
            self._error("Não encontrado.", "", 404)
            return

        length = int(self.headers.get("Content-Length") or 0)
        if length > 2 * 1024 * 1024:
            self._error("Requisição grande demais.", "", 413)
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8")) if raw.strip() else {}
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._error("JSON inválido no corpo da requisição.", "", 400)
            return

        try:
            self._route_post(urlparse(self.path).path, payload)
        except LiaError as e:
            self._json({**e.as_dict()}, 400)
        except Exception:
            log.exception("erro em POST %s", self.path)
            self._error("Falha interna.", "Veja o log em Diagnóstico.", 500)

    # ---- estáticos -------------------------------------------------------
    def _serve_static(self, rel: str):
        rel = rel.replace("\\", "/")
        if ".." in rel.split("/") or rel.startswith("/"):
            self._error("Caminho inválido.", "", 400)
            return
        target = (self.resources / rel).resolve()
        if not str(target).startswith(str(self.resources.resolve())):
            self._error("Caminho inválido.", "", 400)
            return
        if not target.is_file():
            self._error("Arquivo não encontrado.", "", 404)
            return
        ctype, _ = mimetypes.guess_type(str(target))
        ctype = ctype or "application/octet-stream"
        if target.suffix == ".js":
            ctype = "text/javascript; charset=utf-8"
        if target.suffix in (".html", ".css"):
            ctype += "; charset=utf-8"
        html = target.read_bytes()
        if target.suffix == ".html":
            html = html.replace(b"__LIA_TOKEN__", self.token.encode())
        self._send(200, html, ctype)

    # ---- API -------------------------------------------------------------
    def _route_get(self, path: str, qs: dict):
        hub = self.hub
        if path == "/api/items":
            # Parâmetro ausente usa o padrão do SearchQuery ("só ativas").
            # Antes, ausência virava "" e anulava o padrão, devolvendo vazio.
            #
            # Semântica do filtro de ciclo de vida:
            #   ausente           -> "active"  (só o que o usuário usa)
            #   "all"             -> None      (todos os estados DENTRO da
            #                                   biblioteca: ativas + versões
            #                                   substituídas)
            #   "active"/"quarantined"/... -> filtro exato
            #
            # `all` é convertido para None e não comparado por igualdade:
            # antes, "all" não casava com nenhum `cap.lifecycle.value` e a rota
            # devolvia lista vazia EM SILÊNCIO. Filtro que não filtra nada e
            # parece ter funcionado é pior que um erro explícito.
            #
            # Atenção: a quarentena é um armazém SEPARADO (outro diretório).
            # "all" NÃO a inclui — para isso existe `/api/quarantine`.
            bruto = qs.get("lifecycle")
            if bruto is None:
                ciclo = "active"
            else:
                valor = bruto[0].strip().lower()
                ciclo = None if valor in ("", "all", "todas", "todos") else valor
            query = SearchQuery(
                text=(qs.get("q") or [""])[0],
                type=(qs.get("type") or [""])[0],
                domain=(qs.get("domain") or [""])[0],
                tag=(qs.get("tag") or [""])[0],
                trust=(qs.get("trust") or [""])[0],
                lifecycle=ciclo,
            )
            return self._json({"items": hub.items(query)})
        if path.startswith("/api/items/"):
            return self._json(hub.detail(path.rsplit("/", 1)[-1]))
        if path == "/api/quarantine":
            return self._json({"items": hub.items(SearchQuery(lifecycle="quarantined"))})
        if path == "/api/diagnostics":
            return self._json(hub.diagnostics())
        if path == "/api/index":
            idx = hub.read_index()
            return self._json({"index": idx, "health": hub.index_health()})
        if path == "/api/settings":
            return self._json(self.hub.settings())
        if path == "/api/lineage":
            cap = (qs.get("id") or [""])[0]
            if not cap:
                self._error("Informe `id`.", "", 400)
                return
            return self._json({"lineage": hub.lineage(cap)})
        if path == "/api/mcp-config":
            cap = (qs.get("id") or [""])[0]
            formato = (qs.get("format") or ["mcp-json"])[0]
            if not cap:
                self._error("Informe `id`.", "", 400)
                return
            return self._json(hub.mcp_config(cap, formato))
        if path == "/api/history":
            cap = (qs.get("id") or [""])[0]
            return self._json({"history": hub.history(cap) if cap else []})
        self._error("Rota desconhecida.", "", 404)

    def _route_post(self, path: str, payload: dict):
        hub = self.hub
        if path == "/api/import":
            report = hub.import_path(payload.get("path", ""),
                                     dry_run=bool(payload.get("dryRun")))
            return self._json(report.as_dict())
        if path == "/api/promote":
            return self._json(hub.promote(payload["id"]))
        if path == "/api/discard":
            hub.discard(payload["id"])
            return self._json({"ok": True})
        if path == "/api/validate":
            return self._json(hub.validate(payload["id"]))
        if path == "/api/trust":
            return self._json(hub.set_trust(payload["id"], payload["trust"],
                                            decided_by=payload.get("decidedBy", "humano")))
        if path == "/api/license":
            return self._json(hub.set_license(
                payload["id"], code=payload.get("code", ""),
                redistributable=bool(payload.get("redistributable")),
                basis=payload.get("basis", "")))
        if path == "/api/export":
            return self._json(hub.export(payload["id"], payload.get("target", "private"),
                                         payload.get("destination")))
        if path == "/api/export-many":
            return self._json(hub.export_many(
                payload.get("ids", []), payload.get("target", "private"),
                payload.get("destination")))
        if path == "/api/settings":
            return self._json(self.hub.save_settings(payload))
        if path == "/api/settings-reset":
            return self._json(self.hub.reset_settings())
        if path == "/api/update":
            return self._json(self.hub.update_capability(
                payload["id"], payload["path"]))
        if path == "/api/verify-package":
            return self._json(hub.verify_package(payload["path"]))
        if path == "/api/publish-index":
            return self._json(hub.publish_index())
        if path == "/api/diff":
            return self._json(hub.diff_versions(payload["a"], payload["b"]))
        self._error("Rota desconhecida.", "", 404)


class _LocalServer(ThreadingHTTPServer):
    """Servidor que só aceita uma instância por porta, inclusive no Windows.

    `allow_reuse_address = 1` (o padrão de HTTPServer) é a escolha certa no
    POSIX e a ERRADA no Windows: lá, SO_REUSEADDR permite que OUTRO processo
    faça bind na mesma porta e responda no lugar do Hub. Como a interface
    carrega o token de sessão, isso seria um sequestro local.

    No Windows usamos SO_EXCLUSIVEADDRUSE, que torna a porta exclusiva do
    processo. Fora do Windows, SO_REUSEADDR só evita o TIME_WAIT, o que é
    desejável.
    """

    daemon_threads = True
    allow_reuse_address = False
    allow_reuse_port = False

    def server_bind(self):
        # Desativamos as opções herdadas de reuso para que TCPServer não
        # combine SO_REUSEADDR com SO_EXCLUSIVEADDRUSE no Windows.
        if sys.platform == "win32" and hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        socketserver.TCPServer.server_bind(self)


def create_server(hub: AgentHub, *, port: int = 0) -> tuple[ThreadingHTTPServer, str]:
    """Cria o servidor. Retorna (servidor, token). Porta 0 = efêmera."""
    token = secrets.token_urlsafe(32)
    handler = type("BoundHandler", (Handler,), {
        "hub": hub, "token": token, "resources": hub.locations.resources,
    })
    httpd = _LocalServer(("127.0.0.1", port), handler)  # bind só local
    return httpd, token


def serve_in_thread(hub: AgentHub, port: int = 0):
    httpd, token = create_server(hub, port=port)
    t = threading.Thread(target=httpd.serve_forever, daemon=True)
    t.start()
    host, real_port = httpd.server_address[0], httpd.server_address[1]
    return httpd, token, f"http://{host}:{real_port}/", t


CRASH_HTML = """<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8">
<title>Lia Agent Hub — encerrou com erro</title><style>
body{{background:#0e1117;color:#e6edf3;font:15px/1.6 system-ui,sans-serif;padding:2.5rem;max-width:760px;margin:0 auto}}
h1{{font-size:1.3rem;color:#ff9d97}}code,pre{{background:#1d2430;border-radius:8px;padding:.8rem;overflow:auto;font-size:.82rem}}
pre{{border-left:3px solid #f85149}}li{{margin-bottom:.4rem}}a{{color:#6ea8fe}}</style></head><body>
<h1>O Lia Agent Hub encerrou com um erro</h1>
<p>Nada do seu acervo foi alterado — os arquivos continuam onde estavam.
A biblioteca pode ser recarregada quando você abrir de novo.</p>
<h2 style="font-size:1rem">O que aconteceu</h2>
<pre>{err}</pre>
<h2 style="font-size:1rem">O que fazer</h2>
<ol><li>Feche esta janela e abra o Hub de novo.</li>
<li>Se repetir, abra a pasta de logs abaixo e envie o arquivo mais recente a quem te deu suporte.</li>
<li>Nenhum relatório é enviado automaticamente. Nada sai da sua máquina.</li></ol>
<p><strong>Logs:</strong> <code>{logs}</code></p>
<h2 style="font-size:1rem">Detalhes técnicos</h2>
<pre>{tb}</pre>
</body></html>"""


def show_crash_window(exc: BaseException, log: logging.Logger) -> None:
    """Mostra uma página legível sobre a falha. Não tenta se recuperar sozinho."""
    import html as _html
    import traceback as _tb
    import tempfile

    from ..adapters.paths_resolver import resolve_locations

    locs = resolve_locations()
    tb = _html.escape("".join(_tb.format_exception(type(exc), exc, exc.__traceback__)))
    page = CRASH_HTML.format(
        err=_html.escape(f"{type(exc).__name__}: {exc}")[:2000],
        tb=tb[-6000:],
        logs=_html.escape(str(locs.logs)),
    )
    out = Path(tempfile.gettempdir()) / "lia-agenthub-erro.html"
    out.write_text(page, encoding="utf-8")
    import webbrowser as _wb
    _wb.open(out.as_uri())
    log.critical("tela de erro gravada em %s", out)
