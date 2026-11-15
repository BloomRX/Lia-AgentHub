"""Resolução de caminhos — o ÚNICO módulo que monta caminho (regra do kit).

Detecta modo fonte vs. empacotado. Nenhum outro módulo usa sys._MEIPASS
ou monta %USERPROFILE% na mão. `--diagnostico` imprime o que está aqui.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

from .. import APP_ID

APP_FOLDER = "Lia"


@dataclass(frozen=True)
class Locations:
    """Todos os caminhos do app, resolvidos uma vez."""

    home: Path          # %USERPROFILE%\Lia\AgentHub
    library: Path       # ...\Biblioteca
    quarantine: Path    # ...\Quarentena
    exports: Path       # ...\Exportados
    collections: Path   # ...\Colecoes
    common: Path        # %USERPROFILE%\Lia\Comum\Capacidades
    config: Path        # %APPDATA%\Lia\AgentHub\config
    cache: Path         # %LOCALAPPDATA%\Lia\AgentHub
    logs: Path          # %LOCALAPPDATA%\Lia\AgentHub\logs
    resources: Path     # recursos do app (HTML/CSS), fonte ou _MEIPASS

    def ensure(self) -> None:
        for p in (self.home, self.library, self.quarantine, self.exports,
                  self.collections, self.common, self.config, self.logs):
            p.mkdir(parents=True, exist_ok=True)

    def as_dict(self) -> dict[str, str]:
        return {k: str(v) for k, v in self.__dict__.items()}


def is_frozen() -> bool:
    """True quando rodando do .exe do PyInstaller."""
    return bool(getattr(sys, "frozen", False))


def resolve_locations(override_root: Path | None = None) -> Locations:
    """Resolve todos os caminhos. `override_root` existe para testes e para
    `--home`, nunca para o usuário final escolher no meio do uso."""
    if override_root is not None:
        home = Path(override_root)
    elif os.environ.get("LIA_AGENTHUB_HOME"):
        home = Path(os.environ["LIA_AGENTHUB_HOME"])
    else:
        home = Path.home() / APP_FOLDER / APP_ID

    common = home.parent / "Comum" / "Capacidades"

    if is_frozen():
        resources = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "lia_agenthub" / "resources"
        config = Path(os.environ.get("APPDATA", home)) / APP_FOLDER / APP_ID / "config"
        cache = Path(os.environ.get("LOCALAPPDATA", home)) / APP_FOLDER / APP_ID
    else:
        resources = Path(__file__).resolve().parent.parent / "resources"
        config = home / "config"
        cache = home / "cache"

    return Locations(
        home=home,
        library=home / "Biblioteca",
        quarantine=home / "Quarentena",
        exports=home / "Exportados",
        collections=home / "Colecoes",
        common=common,
        config=config,
        cache=cache,
        logs=cache / "logs",
        resources=resources,
    )
