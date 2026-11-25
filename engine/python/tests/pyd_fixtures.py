"""Shared temporary fixtures for M4-M10 tests; no fixture is executed."""

import json
from pathlib import Path


def make_venv(root: Path, version: str = "3.12.9") -> Path:
    prefix = root / "env"
    scripts = prefix / "Scripts"
    scripts.mkdir(parents=True)
    executable = scripts / "python.exe"
    executable.write_bytes(b"")
    (prefix / "pyvenv.cfg").write_text(f"version = {version}\n", encoding="utf-8")
    (prefix / "Lib" / "site-packages").mkdir(parents=True)
    return executable


def add_distribution(
    prefix: Path,
    name: str,
    version: str,
    requires: tuple[str, ...] = (),
    requires_python: str | None = None,
) -> Path:
    location = prefix / "Lib" / "site-packages" / f"{name}-{version}.dist-info"
    location.mkdir(parents=True)
    lines = ["Metadata-Version: 2.1", f"Name: {name}", f"Version: {version}"]
    if requires_python:
        lines.append(f"Requires-Python: {requires_python}")
    lines.extend(f"Requires-Dist: {item}" for item in requires)
    (location / "METADATA").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return location


def add_kernelspec(prefix: Path, name: str, interpreter: Path, display: str = "Python") -> Path:
    location = prefix / "share" / "jupyter" / "kernels" / name
    location.mkdir(parents=True)
    (location / "kernel.json").write_text(
        json.dumps(
            {
                "argv": [str(interpreter), "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": display,
                "language": "python",
            }
        ),
        encoding="utf-8",
    )
    return location


def write_notebook(
    path: Path,
    kernel: str = "python3",
    version: str = "3.12.9",
) -> Path:
    path.write_text(
        json.dumps(
            {
                "nbformat": 4,
                "nbformat_minor": 5,
                "metadata": {
                    "kernelspec": {
                        "name": kernel,
                        "display_name": "Python 3",
                        "language": "python",
                    },
                    "language_info": {"name": "python", "version": version},
                },
                "cells": [],
            }
        ),
        encoding="utf-8",
    )
    return path
