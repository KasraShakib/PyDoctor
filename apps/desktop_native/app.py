"""Native WebView2 shell for the PyDoctor React interface.

The shell hosts the built React bundle and exposes the read-only Python engine
through a small JavaScript API. It never executes a target interpreter, imports
its packages, installs anything, or runs a repair step.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def _bootstrap_paths() -> None:
    """Make the engine importable when running from a source checkout."""
    if getattr(sys, "frozen", False):
        return
    here = Path(__file__).resolve()
    engine_src = here.parent.parent.parent / "engine" / "python" / "src"
    if engine_src.is_dir() and str(engine_src) not in sys.path:
        sys.path.insert(0, str(engine_src))


_bootstrap_paths()

import webview  # noqa: E402

from pydoctor import __version__  # noqa: E402
from pydoctor.__main__ import _engine_info  # noqa: E402
from pydoctor.comparison import compare_interpreter  # noqa: E402
from pydoctor.discovery import discover_environments  # noqa: E402
from pydoctor.environment_report import build_environment_report  # noqa: E402
from pydoctor.error_explainer import explain_error  # noqa: E402
from pydoctor.notebooks import inspect_notebooks  # noqa: E402
from pydoctor.package_diagnostics import inspect_packages  # noqa: E402
from pydoctor.repair import build_repair_plan  # noqa: E402


def _ui_index() -> str:
    """Return the absolute path to the built React entry point."""
    override = os.environ.get("PYDOCTOR_UI_INDEX")
    if override:
        return str(Path(override).resolve())
    if getattr(sys, "frozen", False):
        return str(Path(sys._MEIPASS) / "ui" / "index.html")  # type: ignore[attr-defined]
    return str(
        Path(__file__).resolve().parent.parent / "desktop-ui" / "dist" / "index.html"
    )


def _as_dict(report: Any) -> dict[str, Any]:
    return report.to_dict() if hasattr(report, "to_dict") else dict(report)


class Api:
    """JavaScript-facing facade over the read-only diagnostic engine."""

    def engine_info(self) -> dict[str, Any]:
        return _engine_info()

    def discover(self, project: str = "") -> dict[str, Any]:
        return _as_dict(discover_environments(project or None))

    def run_report(
        self,
        mode: str,
        interpreter: str = "",
        project: str = "",
        payload: str = "",
    ) -> dict[str, Any]:
        interpreter = (interpreter or "").strip()
        project = (project or "").strip()

        if mode == "discovery":
            return _as_dict(discover_environments(project or None))
        if mode == "environment":
            if not interpreter:
                raise ValueError("An interpreter path is required.")
            return _as_dict(build_environment_report(interpreter, project or None))
        if mode == "packages":
            if not interpreter:
                raise ValueError("An interpreter path is required.")
            return _as_dict(inspect_packages(interpreter))
        if mode == "compare":
            if not interpreter:
                raise ValueError("An interpreter path is required.")
            return _as_dict(compare_interpreter(interpreter, project or None))
        if mode == "notebooks":
            if not project:
                raise ValueError("A project or notebook directory is required.")
            return _as_dict(inspect_notebooks(project, interpreter or None))
        if mode == "error":
            if not payload.strip():
                raise ValueError("A traceback is required.")
            return _as_dict(
                explain_error(
                    payload,
                    source="desktop",
                    intended_interpreter=interpreter or None,
                )
            )
        if mode == "repair":
            if not payload.strip():
                raise ValueError("Run a diagnostic report before building a repair plan.")
            try:
                report = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError("The source report is not valid JSON.") from exc
            if not isinstance(report, dict):
                raise ValueError("The source report must be a JSON object.")
            return _as_dict(build_repair_plan(report, "desktop"))
        raise ValueError(f"Unknown mode: {mode}")


def _self_check(window: Any, output: str) -> None:
    """Render check used to verify a packaged build without human inspection."""
    time.sleep(3)
    verdict: dict[str, Any] = {}
    try:
        text = window.evaluate_js("document.body.innerText") or ""
        verdict = {
            "chars": len(text),
            "brand": "PyDoctor" in text,
            # Language-independent checks so the verdict holds for English and Persian.
            "mode": bool(
                window.evaluate_js("!!document.querySelector('[data-mode=\"environment\"]')")
            ),
            "bridge": bool(window.evaluate_js("!!document.querySelector('.dot:not(.off)')")),
            "layout": bool(
                window.evaluate_js(
                    "!!(document.querySelector('.hero') && document.querySelector('.command'))"
                )
            ),
            "controls": bool(
                window.evaluate_js(
                    "!!(document.querySelector('.toggle.lang') && "
                    "document.querySelector('.toggle:not(.lang)'))"
                )
            ),
            "api": window.evaluate_js("Object.keys(window.pywebview.api || {}).join(',')"),
            "logo": bool(
                window.evaluate_js(
                    "(function(){var i=document.querySelector('img.logo');"
                    "return !!(i && i.complete && i.naturalWidth > 0);})()"
                )
            ),
        }
        window.evaluate_js(
            "window.__pydScope = null;"
            "window.pywebview.api.run_report('discovery', '', '', '')"
            ".then(function (r) { window.__pydScope = r.scope; })"
            ".catch(function (e) { window.__pydScope = 'ERR:' + e; });"
        )
        time.sleep(2)
        verdict["report_scope"] = window.evaluate_js("window.__pydScope")
    except Exception as exc:  # noqa: BLE001 - report the failure verbatim
        verdict = {"error": f"{type(exc).__name__}: {exc}"}
    finally:
        Path(output).write_text(json.dumps(verdict), encoding="utf-8")
        window.destroy()


def main() -> int:
    index = _ui_index()
    if not Path(index).is_file():
        print(
            f"PyDoctor UI bundle not found at {index}. "
            "Run 'npm run build' in apps/desktop-ui first.",
            file=sys.stderr,
        )
        return 2
    window = webview.create_window(
        f"PyDoctor {__version__}",
        url=Path(index).as_uri(),
        js_api=Api(),
        width=1280,
        height=840,
        min_size=(980, 640),
        text_select=True,
    )
    self_check_output = os.environ.get("PYDOCTOR_SELF_CHECK_OUT")
    if self_check_output:
        webview.start(_self_check, (window, self_check_output))
    else:
        webview.start(debug=bool(os.environ.get("PYDOCTOR_UI_DEBUG")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
