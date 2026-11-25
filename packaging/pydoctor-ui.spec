# -*- mode: python ; coding: utf-8 -*-
"""One-file Windows build of the React interface hosted in WebView2."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

ROOT = Path(SPECPATH).parent

datas = [(str(ROOT / "apps" / "desktop-ui" / "dist"), "ui")]
datas += collect_data_files("webview")

hiddenimports = [
    "webview.platforms.edgechromium",
    "clr",
    "pythonnet",
    "clr_loader",
]
hiddenimports += collect_submodules("webview")

a = Analysis(
    [str(ROOT / "apps" / "desktop_native" / "app.py")],
    pathex=[str(ROOT / "engine" / "python" / "src")],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "ruff", "tkinter"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PyDoctor-UI",
    icon=str(ROOT / "assets" / "icon-ui.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
