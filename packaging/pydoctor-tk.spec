# -*- mode: python ; coding: utf-8 -*-
"""One-file Windows build of the stdlib Tkinter interface."""

from pathlib import Path

ROOT = Path(SPECPATH).parent

a = Analysis(
    [str(ROOT / "apps" / "desktop" / "pydoctor_ui.py")],
    pathex=[
        str(ROOT / "engine" / "python" / "src"),
        str(ROOT / "apps" / "desktop"),
    ],
    binaries=[],
    datas=[(str(ROOT / "assets" / "icon-tk.ico"), "assets")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "ruff", "pywebview", "pythonnet"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PyDoctor",
    icon=str(ROOT / "assets" / "icon-tk.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
)
