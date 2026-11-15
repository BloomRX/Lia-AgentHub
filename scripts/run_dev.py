#!/usr/bin/env python3
"""Sobe o Hub em modo desenvolvimento, escutando em 0.0.0.0 para pré-visualização.

Em produção o bind é 127.0.0.1 (ver interface/server.py). Este script é
ferramenta de desenvolvimento: sem token, sem Origin, aceita qualquer Host.
NUNCA use isto como o app do usuário final.
"""
from __future__ import annotations

import json
import sys
from http.server import ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from lia_agenthub.app import AgentHub                       # noqa: E402
from lia_agenthub.adapters.paths_resolver import resolve_locations  # noqa: E402
from lia_agenthub.interface import server as srv           # noqa: E402


class DevHandler(srv.Handler):
    """Relaxa SÓ as checagens de host/origem e o token, para o proxy de preview."""

    def _host_ok(self) -> bool:
        return True

    def _origin_ok(self) -> bool:
        return True

    def _token_ok(self) -> bool:
        return True


def main() -> int:
    home = ROOT / ".devhome"
    hub = AgentHub(resolve_locations(home))
    handler = type("BoundDev", (DevHandler,), {
        "hub": hub, "token": "dev", "resources": hub.locations.resources,
    })
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    httpd.daemon_threads = True
    print(f"Lia Agent Hub (dev) em http://0.0.0.0:{port}/ — home: {home}", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
