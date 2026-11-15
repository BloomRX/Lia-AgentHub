"""Detecção de plataforma e WebView2. NUNCA baixa nem instala nada.

WebView2 vem no Windows 11; no Windows 10 "na maioria" das máquinas elegíveis,
mas NÃO em instalações limpas antigas, LTSC, Server ou máquinas gerenciadas.
Por isso: detectar, avisar, e cair para o navegador do sistema.
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass

# Chaves do registro onde o runtime Evergreen se registra (por-máquina e por-usuário).
WV2_REGISTRY_KEYS = (
    r"SOFTWARE\WOW6432Node\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
    r"SOFTWARE\Microsoft\EdgeUpdate\Clients\{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}",
)

MIN_WINDOWS = (10, 0, 0)


@dataclass(frozen=True)
class WebView2Status:
    available: bool
    version: str = ""
    reason: str = ""
    how_to_fix: str = ""

    def as_dict(self) -> dict:
        return {"available": self.available, "version": self.version,
                "reason": self.reason, "howToFix": self.how_to_fix}


def _read_registry_pv(key: str) -> str:
    """Lê o valor `pv` por winreg. Retorna "" se não existir/sem acesso."""
    try:
        import winreg  # type: ignore[import-not-found]
    except ImportError:
        return ""
    for raiz in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
        try:
            with winreg.OpenKey(raiz, key) as k:
                valor, _ = winreg.QueryValueEx(k, "pv")
                if valor and valor != "0.0.0.0":
                    return str(valor)
        except OSError:
            continue
    return ""


def detect_webview2() -> WebView2Status:
    """Detecta o runtime WebView2 sem instalar nada."""
    if sys.platform != "win32":
        return WebView2Status(
            False, reason="WebView2 só existe no Windows.",
            how_to_fix="No Linux/macOS o Hub abre no navegador padrão. "
                       "Para janela nativa, instale o pywebview com GTK/Qt.")

    versao = platform.version()
    try:
        if tuple(int(x) for x in versao.split(".")[:3]) < MIN_WINDOWS:
            return WebView2Status(
                False, reason=f"Windows {versao} é anterior ao mínimo (10.0.0).",
                how_to_fix="Atualize o Windows. O Hub funciona no navegador.")
    except ValueError:
        pass

    for chave in WV2_REGISTRY_KEYS:
        pv = _read_registry_pv(chave)
        if pv:
            return WebView2Status(True, version=pv)

    # Fallback: pastas de instalação conhecidas do Edge/EdgeWebView.
    for raiz in (r"C:\Program Files (x86)\Microsoft\EdgeWebView\Application",
                 r"C:\Program Files\Microsoft\EdgeWebView\Application"):
        try:
            from pathlib import Path
            base = Path(raiz)
            if base.is_dir():
                versoes = sorted((d.name for d in base.iterdir() if d.is_dir()),
                                 reverse=True)
                if versoes:
                    return WebView2Status(True, version=versoes[0])
        except OSError:
            continue

    return WebView2Status(
        False,
        reason="O runtime WebView2 não foi encontrado nesta máquina.",
        how_to_fix=(
            "O Hub vai abrir no seu navegador padrão — funciona igual. "
            "Para a janela nativa, instale o 'Evergreen WebView2 Runtime' "
            "da Microsoft (procure por 'WebView2 Runtime download'). "
            "O Hub NÃO baixa nem instala isso por você."))


def system_info() -> dict:
    """Resumo honesto do ambiente. Sem telemetria: nada sai da máquina."""
    from .paths_resolver import is_frozen
    wv2 = detect_webview2()
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "python": sys.version.split()[0],
        "frozen": is_frozen(),
        "webview2": wv2.as_dict(),
        "browser_fallback": True,
        "notes": (
            "O Hub não envia dados para fora. Sem conta, sem telemetria, "
            "sem atualização automática."
        ),
    }


def has_browser() -> bool:
    """Há um navegador utilizável para o fallback?"""
    import webbrowser
    try:
        return webbrowser.get() is not None
    except webbrowser.Error:
        for nome in ("xdg-open", "open", "start"):
            if shutil.which(nome):
                return True
        return False


def explain_launch(use_browser: bool) -> str:
    """Mensagem única e clara sobre COMO a janela vai abrir."""
    if use_browser:
        return ("Abrindo no seu navegador padrão. A interface é a mesma; "
                "o Hub roda localmente na sua máquina.")
    wv2 = detect_webview2()
    if wv2.available:
        return f"Janela integrada (WebView2 {wv2.version})."
    return wv2.how_to_fix
