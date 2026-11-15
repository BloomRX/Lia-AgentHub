"""Configurações persistentes do usuário.

Arquivo JSON pequeno, escrito atomicamente. Nada sensível: o Hub não guarda
token, senha, chave nem credencial — por desenho, não por esquecimento.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .atomic import atomic_write_json, read_json

SETTINGS_FILE = "settings.json"


@dataclass
class Settings:
    """Preferências que mudam o comportamento da interface."""

    #: Abrir no navegador em vez de tentar janela nativa.
    prefer_browser: bool = False
    #: Confirmar antes de descartar da quarentena (padrão: sim).
    confirm_discard: bool = True
    #: Destino padrão da exportação: private | shared | public.
    default_export_target: str = "private"
    #: Exibir caracteres invisíveis escapados na interface (U+XXXX).
    escape_invisible: bool = True
    #: Pasta onde o Hub escreve. Vazio = padrão (%USERPROFILE%\Lia\AgentHub).
    #: Só leitura aqui: mudar exigiria reiniciar e mover dados, então o
    #: caminho é informativo no MVP.
    home_override_note: str = ""
    #: Já viu o aviso de primeira execução.
    seen_welcome: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


ALLOWED_TARGETS = ("private", "shared", "public")


class SettingsStore:
    def __init__(self, config_dir: Path):
        self.dir = Path(config_dir)
        self.path = self.dir / SETTINGS_FILE

    def load(self) -> Settings:
        data = read_json(self.path) or {}
        validos = {f.name for f in fields(Settings)}
        limpo = {k: v for k, v in data.items() if k in validos}
        try:
            s = Settings(**limpo)
        except TypeError:
            return Settings()
        return self._coerce(s)

    @staticmethod
    def _coerce(s: Settings) -> Settings:
        """Nunca confiar no arquivo: valores fora do contrato voltam ao padrão."""
        s.prefer_browser = bool(s.prefer_browser)
        s.confirm_discard = bool(s.confirm_discard)
        s.escape_invisible = bool(s.escape_invisible)
        s.seen_welcome = bool(s.seen_welcome)
        if s.default_export_target not in ALLOWED_TARGETS:
            s.default_export_target = "private"
        return s

    def save(self, settings: Settings) -> None:
        self.dir.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self.path, self._coerce(settings).as_dict())

    def update(self, changes: dict) -> Settings:
        s = self.load()
        validos = {f.name for f in fields(Settings)}
        for k, v in changes.items():
            if k in validos and k != "home_override_note":
                setattr(s, k, v)
        self.save(s)
        return s

    def reset(self) -> Settings:
        s = Settings()
        self.save(s)
        return s
