"""Assemble the portable Windows release folder and zip.

Expects ``dist/PyDoctor-UI.exe`` and ``dist/PyDoctor.exe`` to exist. Templates
live in ``release/``; generated output is ``release/PyDoctor-<version>-win64``.
"""

from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "0.3.0"
DIST = ROOT / "dist"
RELEASE = ROOT / "release"
PACKAGE = RELEASE / f"PyDoctor-{VERSION}-win64"
ARCHIVE = RELEASE / f"PyDoctor-{VERSION}-win64.zip"
EXECUTABLES = ("PyDoctor-UI.exe", "PyDoctor.exe")
TEMPLATES = ("README.txt", "RELEASE_NOTES.md", "sample-traceback.txt")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    missing = [name for name in EXECUTABLES if not (DIST / name).is_file()]
    if missing:
        print(f"Missing build output: {', '.join(missing)}. Run build-exe.cmd first.")
        return 1

    if PACKAGE.exists():
        shutil.rmtree(PACKAGE)
    PACKAGE.mkdir(parents=True)

    for name in EXECUTABLES:
        shutil.copy2(DIST / name, PACKAGE / name)
    for name in TEMPLATES:
        shutil.copy2(RELEASE / name, PACKAGE / name)

    sums = [f"{_sha256(PACKAGE / name)}  {name}" for name in EXECUTABLES]
    (PACKAGE / "SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="ascii")

    if ARCHIVE.exists():
        ARCHIVE.unlink()
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(PACKAGE.rglob("*")):
            if item.is_file():
                archive.write(item, item.relative_to(RELEASE))

    print(f"Package: {PACKAGE}")
    print(f"Archive: {ARCHIVE} ({ARCHIVE.stat().st_size} bytes)")
    print(f"Archive SHA256: {_sha256(ARCHIVE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
