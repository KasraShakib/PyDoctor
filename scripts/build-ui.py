"""Assemble the static React bundle for the desktop shell.

The interface is a no-bundler React app: React 18 UMD plus plain JavaScript and
CSS. This script copies the source files into ``apps/desktop-ui/dist`` so the
PyInstaller build and the WebView2 shell have a stable output directory.
"""

from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UI = ROOT / "apps" / "desktop-ui"
DIST = UI / "dist"
FILES = ("index.html", "app.js", "styles.css")


def main() -> int:
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(UI / name, DIST / name)
    shutil.copytree(UI / "vendor", DIST / "vendor")
    assets = DIST / "assets"
    assets.mkdir()
    shutil.copy2(ROOT / "assets" / "icon.svg", assets / "icon.svg")
    print(f"UI bundle written to {DIST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
