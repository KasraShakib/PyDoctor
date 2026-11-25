# PyDoctor

**Your Python environment, understood.**

PyDoctor is a portable Windows desktop app that diagnoses Python environments.
It finds every Python installation on the machine, checks whether the
interpreter you *think* you are using is the one you are *actually* using,
inventories installed packages, detects missing and conflicting dependencies,
explains tracebacks, inspects Jupyter kernels, and produces dry-run repair
plans — without ever executing, importing, or modifying anything.

**[Download the latest portable build →](../../releases/latest)**

---

## Why

Most Python environment problems are not syntax errors. They are:

- the wrong interpreter silently running your code,
- packages installed into a different environment than the project,
- a missing or conflicting dependency,
- a Jupyter kernel pointing at an old interpreter,
- a broken `PATH` or a launcher that resolves to something unexpected.

PyDoctor answers those questions with **evidence**, not guesses. Every finding
carries a severity, a confidence level (`CONFIRMED`, `LIKELY`, `UNKNOWN`), the
evidence behind it, and a suggested next step.

## What it does

| Mode | What you get |
| --- | --- |
| **Full report** | Interpreter, package inventory, dependency problems, and notebook evidence in one report |
| **Packages** | Installed distributions, missing dependencies, version conflicts, `Requires-Python` mismatches |
| **Notebooks** | Jupyter kernelspecs, notebook metadata, kernel/interpreter mismatches |
| **Explain error** | Traceback classification with the likely root cause and environment context |
| **Repair plan** | Ordered, dry-run steps derived from the last report (nothing is executed) |
| **Discover** | Every Python installation found via registry (PEP 514), the `py` launcher, `PATH`, and active environment hints |
| **Compare** | Whether a specific `python.exe` matches the evidence gathered during discovery |

## Features

- **Read-only by design.** No target execution, no imports, no `pip`, no PATH or
  registry changes, no file mutations.
- **Evidence-based findings.** Severity, confidence, evidence, explanation, and
  next steps for every result.
- **Light and dark themes**, remembered between launches.
- **English and Persian (فارسی)** interface with full right-to-left layout.
- **Portable.** Single-folder build, no installer, no admin rights, no network
  access, no telemetry.
- **Two front ends.** A modern React interface in the native Windows WebView2
  control, plus a zero-dependency Tkinter fallback.

## Download and run

1. Download `PyDoctor-<version>-win64.zip` from
   [Releases](../../releases/latest).
2. Extract it anywhere — it is portable.
3. Run `PyDoctor-UI.exe` (recommended) or `PyDoctor.exe` (Tkinter fallback).

`PyDoctor-UI.exe` needs the Microsoft Edge WebView2 runtime, which ships with
Windows 11 and is present on most updated Windows 10 systems. `PyDoctor.exe`
needs nothing beyond Windows.

The executables are unsigned, so Windows SmartScreen may warn on first launch.

## Safety model

PyDoctor never, without explicit user approval:

- installs or removes packages,
- changes package versions,
- creates, deletes, or rebuilds virtual environments,
- modifies `PATH` or the registry,
- deletes project files,
- activates or deactivates an environment.

Repair plans are **dry-run only**: they describe the exact commands and the
verification step, and nothing is executed.

## Architecture

```
┌──────────────────────────────┐
│  React UI (apps/desktop-ui)  │  no bundler, no npm, no network
└───────────────┬──────────────┘
                │ JSON over the pywebview bridge
┌───────────────▼──────────────┐
│  Native shell (pywebview)    │  WebView2 window, exposes the Api class
└───────────────┬──────────────┘
                │ in-process calls
┌───────────────▼──────────────┐
│  Python engine (pydoctor)    │  read-only diagnostics, JSON reports
└──────────────────────────────┘
```

- `engine/python/src/pydoctor/` — the diagnostic engine (schemas `1.0`–`1.7`
  plus `meta`).
- `apps/desktop-ui/` — the React interface (React 18 UMD, hand-authored CSS).
- `apps/desktop_native/` — the WebView2 host and bridge API.
- `apps/desktop/` — the stdlib Tkinter fallback.
- `packaging/` — PyInstaller specs for both executables.

The Tauri shell remains the long-term target; the React bundle and the engine
are shell-independent, so it can be swapped in without changing either.

## Use the engine from the command line

The engine is a normal Python package and works without the desktop app:

```powershell
python -m pydoctor --pretty
python -m pydoctor --discover --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --pretty
python -m pydoctor --inspect-packages "C:\Path\To\python.exe" --pretty
python -m pydoctor --info --pretty
```

Every mode writes a structured JSON report to stdout. See
`docs/ENGINE_CONTRACT.md` for the schemas.

## Build from source

Requirements: Windows 10/11, Python 3.11+ (developed on 3.12), and
`pyinstaller` + `pywebview` for the packaged executables.

```powershell
cmd /c scripts\run-desktop-ui.cmd    # run the React app from source
cmd /c scripts\run-desktop.cmd       # run the Tkinter fallback
cmd /c scripts\build-ui.cmd          # assemble the UI bundle
cmd /c scripts\build-exe.cmd         # build dist\PyDoctor.exe and dist\PyDoctor-UI.exe
cmd /c scripts\build-release.cmd     # assemble the portable folder and zip
```

Regenerate the icons with:

```powershell
python scripts\make-icon.py
```

## Tests

```powershell
cmd /c scripts\run-tests.cmd
```

This runs the engine suite, the Tkinter presentation tests, and the native
bridge tests. `scripts/verify-ui.py` additionally opens the real WebView2
window and checks layout, theme switching, language switching, and the bridge.

## Documentation

- `docs/ARCHITECTURE.md` — components and data flow.
- `docs/ENGINE_CONTRACT.md` — JSON schemas per mode.
- `docs/DECISIONS.md` — technical decisions and their rationale.
- `docs/ROADMAP.md` — milestones.
- `docs/QUALITY.md` — collection limits and known constraints.
- `docs/TESTING.md` — how to verify a build.

## Status

Milestones M1–M11 of the diagnostic engine and the desktop MVP (M5, M6) are
implemented. Notebook diagnostics, the error explainer, and repair planning are
available; automatic repair execution is intentionally not exposed.

## Notes

- Reports contain local paths. Review them before sharing.
- No telemetry, no auto-update, no cloud service, no account.
