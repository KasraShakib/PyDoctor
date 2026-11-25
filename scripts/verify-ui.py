"""Headless-ish smoke check for the React interface inside WebView2.

Opens the real window, waits for React to render, inspects the rendered layout,
exercises the theme and language toggles, calls the bridge, prints a JSON
verdict, and closes the window.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "apps" / "desktop_native"))
sys.path.insert(0, str(ROOT / "engine" / "python" / "src"))

import webview  # noqa: E402

from app import Api, _ui_index  # noqa: E402


def check(window: webview.Window) -> None:
    time.sleep(3)
    verdict: dict[str, object] = {}
    try:
        text = window.evaluate_js("document.body.innerText") or ""
        verdict["chars"] = len(text)
        verdict["brand"] = "PyDoctor" in text
        verdict["mode"] = bool(
            window.evaluate_js("!!document.querySelector('[data-mode=\"environment\"]')")
        )
        verdict["layout"] = bool(
            window.evaluate_js(
                "!!(document.querySelector('.hero') && document.querySelector('.command'))"
            )
        )
        verdict["controls"] = bool(
            window.evaluate_js(
                "!!(document.querySelector('.toggle.lang') && "
                "document.querySelector('.toggle:not(.lang)'))"
            )
        )
        verdict["api"] = window.evaluate_js(
            "Object.keys(window.pywebview.api || {}).join(',')"
        )

        # Theme toggle: flip once and confirm the attribute and background change.
        window.evaluate_js("document.querySelector('.toggle:not(.lang)').click()")
        time.sleep(0.4)
        verdict["theme_after_toggle"] = window.evaluate_js(
            "document.documentElement.dataset.theme"
        )
        verdict["background"] = window.evaluate_js(
            "getComputedStyle(document.body).backgroundColor"
        )

        # Language toggle: flip once and confirm RTL plus Persian text.
        window.evaluate_js("document.querySelector('.toggle.lang').click()")
        time.sleep(0.6)
        verdict["dir"] = window.evaluate_js("document.documentElement.dir")
        verdict["persian"] = bool(
            window.evaluate_js(
                "(document.body.innerText || '').indexOf('\\u06af\\u0632\\u0627\\u0631\\u0634') !== -1"
            )
        )

        # Restore English and confirm the direction flips back.
        window.evaluate_js("document.querySelector('.toggle.lang').click()")
        time.sleep(0.4)
        verdict["dir_restored"] = window.evaluate_js("document.documentElement.dir")

        # Restore the original theme so the check leaves no lasting preference.
        window.evaluate_js("document.querySelector('.toggle:not(.lang)').click()")
        time.sleep(0.3)
        verdict["theme_restored"] = window.evaluate_js(
            "document.documentElement.dataset.theme"
        )

        # Exercise the bridge end to end.
        window.evaluate_js(
            "window.__pydScope = null;"
            "window.pywebview.api.run_report('discovery', '', '', '')"
            ".then(function (r) { window.__pydScope = r.scope; })"
            ".catch(function (e) { window.__pydScope = 'ERR:' + e; });"
        )
        time.sleep(1.5)
        verdict["report_scope"] = window.evaluate_js("window.__pydScope")
    except Exception as exc:  # noqa: BLE001 - report the failure verbatim
        verdict["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        print(json.dumps(verdict))
        window.destroy()


def main() -> int:
    window = webview.create_window(
        "PyDoctor UI check",
        url=Path(_ui_index()).as_uri(),
        js_api=Api(),
        width=900,
        height=640,
    )
    webview.start(check, (window,))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
