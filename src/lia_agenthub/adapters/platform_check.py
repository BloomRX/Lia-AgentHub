"""Detecção de plataforma e WebView2. NUNCA baixa nem instala nada.

WebView2 vem no Windows 11; no Windows 10 "na maioria" das máquinas elegíveis,
mas NÃO em instalações limpas antigas, LTSC, Server ou máquinas gerenciadas.
Por isso: detectar, avisar, e cair para o navegador do sistema.
"""
from __future__ import annotations

import os
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
        "webview2_network": {
            "envVar": ENV_BROWSER_ARGS,
            # `controle_ativo()` verifica se os NOSSOS argumentos estão na
            # variável. Um `bool(os.environ.get(...))` responderia "ativo"
            # para qualquer valor — inclusive um `--remote-debugging-port`
            # deixado por depuração, que é o oposto de controle.
            "active": controle_ativo(),
            "scope": "runtime do navegador (WebView2), não a rede do app",
            "notAFirewall": True,
        },
        "notes": (
            "O Hub não envia dados para fora. Sem conta, sem telemetria, "
            "sem atualização automática. O controle de rede do WebView2 reduz "
            "o tráfego do runtime do navegador; não substitui medição em "
            "Windows nem funciona como firewall."
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


# ---------------------------------------------------------------------------
# Controle de rede do WebView2
# ---------------------------------------------------------------------------
#: Recursos do Chromium que o Hub desliga na janela nativa.
#:
#: O Hub é uma UI local que serve arquivos de `127.0.0.1`. Nenhum destes
#: recursos tem função aqui, e todos geram tráfego de saída que o produto não
#: pediu. A medição em Windows (D-09 do relatório de validação) viu conexões
#: externas de processos `msedgewebview2.exe` com o Hub aberto; estes são os
#: candidatos documentados, desligados por nome.
#:
#: `msWebOOUI`/`msPdfOOUI` = barras de ferramentas do Edge; `OptimizationHints`
#: = download de modelo de otimização; `Translate` = tradução; `AutofillServer
#: Communication` = preenchimento; `InterestFeedContentSuggestions`/`Optimization
#: GuideOnboarding` = sugestões; `SafeBrowsing*` consulta listas remotas a cada
#: navegação; `MetricsReporting`/`UMA` = telemetria do Chromium.
#:
#: DESLIGAR TEM CUSTO: sem Safe Browsing, a janela não consulta listas de
#: reputação — o Hub só carrega a própria UI de `127.0.0.1`, então o risco é
#: baixo, mas é uma decisão que fica registrada aqui.
_ARGUMENTOS_REDE = (
    "--disable-features=" + ",".join((
        "AutofillServerCommunication",
        "CalculateNativeWinOcclusion",
        "InterestFeedContentSuggestions",
        "MetricsReportingEnabled",
        "OptimizationHints",
        "OptimizationGuideOnboarding",
        "msPdfOOUI",
        "msWebOOUI",
        "Translate",
        "SafeBrowsingEnhancedProtection",
    )),
    "--disable-background-networking",
    "--disable-component-update",
    "--disable-domain-reliability",
    "--disable-sync",
    "--no-first-run",
    "--no-default-browser-check",
)

#: Nome da variável que o WebView2 lê ao criar o processo de navegador.
#: Documentado pela Microsoft: os argumentos são ANEXADOS aos que o host
#: passa via `CoreWebView2EnvironmentOptions` — não os substituem.
#: É por isso que este caminho funciona com o pywebview, que fixa os seus.
ENV_BROWSER_ARGS = "WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"


def argumentos_windows_rede() -> str:
    """String única de argumentos, pronta para a variável de ambiente."""
    return " ".join(_ARGUMENTOS_REDE)


def aplicar_controle_de_rede(env: dict | None = None) -> dict:
    """Define `WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS` antes da janela abrir.

    Devolve um resumo do que foi feito, para o log. Nunca sobrescreve um valor
    já presente: se alguém (suporte, depuração) definiu argumentos, misturar
    os dois poderia quebrar a janela de forma difícil de diagnosticar. Nesse
    caso, registra e respeita.

    Retorna `{"applied": bool, "reason": str, "arguments": str}`.
    """
    import os

    alvo = os.environ if env is None else env

    if sys.platform != "win32":
        return {"applied": False,
                "reason": "controle de rede do WebView2 só se aplica no Windows",
                "arguments": ""}

    existente = alvo.get(ENV_BROWSER_ARGS, "").strip()
    if existente:
        return {"applied": False,
                "reason": (f"{ENV_BROWSER_ARGS} já estava definida; "
                           "valor preservado em vez de sobrescrito"),
                "arguments": existente}

    novos = argumentos_windows_rede()
    alvo[ENV_BROWSER_ARGS] = novos
    return {"applied": True,
            "reason": "aplicado antes da criação da janela",
            "arguments": novos}


def controle_ativo(env: dict | None = None) -> bool:
    """Os argumentos de controle do Hub estão presentes no ambiente?

    Distingue três situações que um `bool()` não distingue:
      - variável ausente          -> False (não configurado)
      - variável nossa            -> True  (controle aplicado)
      - variável de outra origem  -> False (controle NÃO aplicado; alguém
                                     definiu outra coisa e o Hub preservou)
    """
    alvo = os.environ if env is None else env
    valor = alvo.get(ENV_BROWSER_ARGS, "")
    # A marca inconfundível é o disable-features com o primeiro recurso da
    # nossa lista; comparar a string inteira quebraria se um cliente anexasse.
    return "AutofillServerCommunication" in valor


def resumo_controle_de_rede(controle: dict) -> str:
    """Texto para o log/Diagnóstico: o que foi desligado e o que fica aberto."""
    if not controle.get("applied"):
        return f"Controle de rede do WebView2 não aplicado: {controle.get('reason', '')}"
    return (
        "Controle de rede do WebView2 aplicado (recursos desligados por nome). "
        "Isto reduz o tráfego do RUNTIME do navegador; NÃO é firewall e não "
        "garante zero egress. A prova de zero egress continua sendo medição "
        "de rede em Windows — ver D-09 do relatório de validação."
    )
