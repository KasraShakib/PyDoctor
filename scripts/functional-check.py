"""Exercise every desktop bridge mode against real inputs.

Prints a JSON verdict so a release can be checked without opening the UI.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "desktop_native"))
sys.path.insert(0, str(ROOT / "engine" / "python" / "src"))

from app import Api  # noqa: E402


def _notebook() -> str:
    return json.dumps(
        {
            "cells": [],
            "metadata": {
                "kernelspec": {
                    "name": "python3",
                    "display_name": "Python 3",
                    "language": "python",
                }
            },
            "nbformat": 4,
            "nbformat_minor": 5,
        }
    )


def main() -> int:
    api = Api()
    python = sys.executable
    results: dict[str, object] = {}

    results["engine_info"] = api.engine_info()["scope"]
    results["discovery"] = api.discover("")["scope"]
    results["environment"] = api.run_report("environment", python, "")["scope"]
    results["packages"] = api.run_report("packages", python, "")["scope"]
    results["compare"] = api.run_report("compare", python, "")["scope"]

    traceback = (
        "Traceback (most recent call last):\n"
        '  File "C:\\project\\app.py", line 1, in <module>\n'
        "ModuleNotFoundError: No module named 'requests'\n"
    )
    error = api.run_report("error", "", "", traceback)
    results["error"] = [error["scope"], error.get("exception_type")]

    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / "project"
        project.mkdir()
        (project / "demo.ipynb").write_text(_notebook(), encoding="utf-8")
        notebooks = api.run_report("notebooks", python, str(project))
        results["notebooks"] = [
            notebooks["scope"],
            len(notebooks["notebooks"]),
            len(notebooks["kernels"]),
        ]

        venv = Path(tmp) / "venv"
        subprocess.run(
            [python, "-m", "venv", "--without-pip", str(venv)],
            check=True,
            capture_output=True,
        )
        dist_info = venv / "Lib" / "site-packages" / "demo-1.0.dist-info"
        dist_info.mkdir(parents=True)
        (dist_info / "METADATA").write_text(
            "Metadata-Version: 2.1\n"
            "Name: demo\n"
            "Version: 1.0\n"
            "Requires-Dist: missing-dep>=1.0\n",
            encoding="utf-8",
        )
        target = venv / "Scripts" / "python.exe"
        package_report = api.run_report("packages", str(target), "")
        missing = [
            item
            for item in package_report["dependencies"]
            if item.get("status") == "MISSING"
        ]
        results["fixture_missing"] = len(missing)
        plan = api.run_report("repair", "", "", json.dumps(package_report))
        results["repair"] = [
            plan["scope"],
            len(plan["steps"]),
            plan["steps"][0]["argv"] if plan["steps"] else None,
        ]

    print(json.dumps(results, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
