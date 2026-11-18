# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller — Lia Agent Hub.

Empacota um executável de arquivo único com a UI embarcada.

Decisões:
  - `console=False`: o usuário não vê um terminal preto ao abrir.
  - A UI estática entra sob `lia_agenthub/resources/static`, exatamente onde
    `paths_resolver` procura quando `sys.frozen` é verdadeiro.
  - `hiddenimports` cobrem backends do pywebview importados dinamicamente.
  - `upx=False`: compressão UPX dispara falso positivo de antivírus.
"""
from pathlib import Path

SPEC_DIR = Path(SPECPATH)
ROOT = SPEC_DIR.parent
STATIC = ROOT / "src" / "lia_agenthub" / "resources" / "static"

if not STATIC.is_dir():
    raise SystemExit(f"UI nao encontrada em {STATIC} - rode a partir da raiz do repo.")

# IMPORTANTE: a entrada é `launcher.py`, NÃO `lia_agenthub/__main__.py`.
# O PyInstaller executa o script de entrada como `__main__`, sem contexto de
# pacote; o `__main__.py` do pacote usa import relativo e quebraria com
# "attempted relative import with no known parent package".
a = Analysis(
    [str(ROOT / "packaging" / "launcher.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[(str(STATIC), "lia_agenthub/resources/static")],
    hiddenimports=[
        "lia_agenthub.resources",
        # `cli` é importado dentro de `_despachar_cli`. O import é estático, o
        # PyInstaller o seguiria — mas declará-lo custa nada e evita que uma
        # futura troca por import dinâmico quebre a CLI só no .exe.
        "lia_agenthub.cli",
        "webview",
        "webview.platforms.edgechromium",
        "webview.platforms.winforms",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # Exclusões: reduzem tamanho e evitam que o PyInstaller arraste stacks
    # gráficas que o Hub nunca usa. No Windows o pywebview tenta `qt` e depois
    # `winforms`; `qt` só existe se QtPy+PyQt estiverem instalados, o que NÃO é
    # o caso do venv de build deste projeto. Excluir é seguro e evita um .exe
    # de centenas de MB.
    excludes=[
        "tkinter", "unittest", "pydoc", "doctest",
        # backends de UI que não usamos
        "PyQt5", "PyQt6", "PySide2", "PySide6", "qtpy", "QtPy",
        "gi", "cefpython3", "android",
        # plataformas de outros sistemas
        "webview.platforms.cocoa", "webview.platforms.gtk",
        "webview.platforms.cef", "webview.platforms.qt",
        "webview.platforms.android", "webview.platforms.mshtml",
        # ferramentas de desenvolvimento que não rodam no bundle
        "pytest", "setuptools", "pip",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="LiaAgentHub",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
