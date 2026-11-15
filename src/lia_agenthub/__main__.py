"""Ponto de entrada — abre a janela do Hub.

Ordem de preferência de janela:
  1. pywebview (WebView2 no Windows) — janela nativa
  2. navegador padrão do sistema — sempre funciona, nunca baixa nada

Nunca instala WebView2 silenciosamente. Se faltar, avisa e usa o navegador.
"""
from __future__ import annotations

import argparse
import logging
import logging.handlers
import os
import socket
import sys
import traceback
import webbrowser
from pathlib import Path

from . import APP_NAME, __version__
from .adapters.paths_resolver import resolve_locations
from .app import AgentHub


def _setup_logging(logs_dir: Path, verbose: bool = False) -> logging.Logger:
    logs_dir.mkdir(parents=True, exist_ok=True)
    log = logging.getLogger("lia_agenthub")
    log.setLevel(logging.DEBUG if verbose else logging.INFO)
    if log.handlers:
        return log

    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")

    fh = logging.handlers.RotatingFileHandler(
        logs_dir / "agenthub.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    fh.setFormatter(fmt)
    log.addHandler(fh)

    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    log.addHandler(sh)
    return log


def _log_paths(logs_dir: Path) -> str:
    return (f"Logs em: {logs_dir}\n"
            f"Arquivo: agenthub.log (rotaciona em 1 MB, mantém 3)")


def _install_crash_handler(log: logging.Logger) -> None:
    def hook(exc_type, exc, tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc, tb)
            return
        log.critical("falha não tratada:\n%s",
                     "".join(traceback.format_exception(exc_type, exc, tb)))
        try:
            from .interface.server import show_crash_window
            show_crash_window(exc, log)
        except Exception:
            pass
    sys.excepthook = hook


def _pick_port(preferred: int) -> int:
    """Porta efêmera por padrão; se a preferida estiver ocupada, usa 0."""
    if preferred:
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", preferred))
                return preferred
            except OSError:
                return 0
    return 0


def _open_view(url: str, hub: AgentHub, log: logging.Logger) -> bool:
    """Tenta pywebview; se não houver, abre o navegador. Retorna True se bloqueou."""
    try:
        import webview  # type: ignore
    except ImportError:
        log.info("pywebview não disponível — abrindo no navegador padrão.")
        webbrowser.open(url)
        return False

    try:
        window = webview.create_window(
            APP_NAME, url, width=1180, height=780, min_size=(900, 600),
            text_select=True)
        # guarda para os testes e para o encerramento seguro
        hub._window = window  # type: ignore[attr-defined]
        webview.start()
        return True
    except Exception as e:  # WebView2 ausente, GTK ausente, etc.
        log.warning("pywebview falhou (%s) — usando o navegador padrão.", e)
        print(f"\n[Aviso] Não foi possível abrir a janela integrada: {e}\n"
              f"O Hub vai abrir no seu navegador padrão. Nada foi baixado.\n",
              file=sys.stderr)
        webbrowser.open(url)
        return False


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="lia-agenthub",
        description=f"{APP_NAME} — acervo local de capacidades. Nada é executado.")
    ap.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    ap.add_argument("--home", type=Path, default=None,
                    help="Raiz de dados alternativa (padrão: %%USERPROFILE%%\\Lia\\AgentHub)")
    ap.add_argument("--port", type=int, default=0, help="Porta local (0 = automática)")
    ap.add_argument("--browser", action="store_true", help="Abrir no navegador padrão")
    ap.add_argument("--no-window", action="store_true",
                    help="Só subir o servidor e imprimir a URL (para testes)")
    ap.add_argument("--diagnostico", action="store_true", help="Imprimir caminhos e sair")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args(argv)

    locs = resolve_locations(args.home)
    log = _setup_logging(locs.logs, args.verbose)
    log.info("%s %s iniciando (frozen=%s)", APP_NAME, __version__,
             getattr(sys, "frozen", False))

    if args.diagnostico:
        for k, v in locs.as_dict().items():
            print(f"{k:12} {v}")
        print(f"{'python':12} {sys.version.split()[0]}")
        print(f"{'log':12} {locs.logs / 'agenthub.log'}")
        return 0

    _install_crash_handler(log)

    try:
        hub = AgentHub(locs)
    except Exception as e:
        log.exception("falha ao inicializar")
        print(f"\n{APP_NAME} não pôde iniciar.\n\n{e}\n\n{_log_paths(locs.logs)}\n",
              file=sys.stderr)
        return 1

    from .interface.server import serve_in_thread

    port = _pick_port(args.port)
    httpd, token, url, thread = serve_in_thread(hub, port=port)
    log.info("servidor local em %s (token de sessão exigido)", url)

    if args.no_window:
        print(url)
        print(f"TOKEN={token}")
        try:
            thread.join()
        except KeyboardInterrupt:
            pass
        return 0

    try:
        if args.browser:
            webbrowser.open(url)
            thread.join()
        else:
            blocked = _open_view(url, hub, log)
            if not blocked:
                print(f"\n{APP_NAME} está em {url}\nFeche esta janela para encerrar.\n")
                thread.join()
    except KeyboardInterrupt:
        log.info("encerrado por Ctrl+C")
    finally:
        log.info("encerrando servidor local")
        httpd.shutdown()
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
