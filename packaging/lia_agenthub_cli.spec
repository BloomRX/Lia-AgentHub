# -*- mode: python ; coding: utf-8 -*-
"""Standalone console distribution for the Hub CLI."""
from pathlib import Path

root = Path(SPECPATH).parent
analysis = Analysis(
    [str(root / "packaging" / "cli_launcher.py")],
    pathex=[str(root / "src")],
    excludes=["webview", "tkinter", "pytest", "setuptools", "pip"],
)
pyz = PYZ(analysis.pure)
exe = EXE(
    pyz,
    analysis.scripts,
    analysis.binaries,
    analysis.datas,
    [],
    name="LiaAgentHubCli",
    console=True,
    upx=False,
)
