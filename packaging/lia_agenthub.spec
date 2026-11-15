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

a = Analysis(
    [str(ROOT / "src" / "lia_agenthub" / "__main__.py")],
    pathex=[str(ROOT / "src")],
    binaries=[],
    datas=[(str(STATIC), "lia_agenthub/resources/static")],
    hiddenimports=[
        "lia_agenthub.resources",
        "webview",
        "webview.platforms.edgechromium",
        "webview.platforms.winforms",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "unittest", "pydoc", "doctest"],
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
