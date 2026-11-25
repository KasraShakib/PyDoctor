# PyDoctor 0.3.0

Portable Windows build of PyDoctor, a read-only diagnostics tool for Python
environments.

## Highlights

- **New interface.** Command-center layout with an aurora background, a
  collapsing hero, a single glass command bar, mode chips, a verdict banner,
  expandable findings, and a List / Raw JSON toggle.
- **Light and dark themes.** Switch from the top bar; the choice is remembered.
- **English and Persian (فارسی).** Full translation with right-to-left layout;
  switch from the top bar and the choice is remembered.
- **Distinct icons per executable.** Cyan accent for `PyDoctor-UI.exe`, amber
  accent for `PyDoctor.exe`, both embedded at 16-256 px.
- M1-M11 diagnostic engine (schemas 1.0-1.7 plus `meta`).
- React 18 interface hosted in the native Windows WebView2 control.
- Stdlib Tkinter interface as a zero-dependency fallback.
- Standalone one-file executables; no installer and no admin rights.
- Read-only by design: no target execution, no imports, no pip, no mutations.

## Modes

| Mode | What it does |
| --- | --- |
| Full report | Interpreter, packages, and optional notebook evidence |
| Packages | Installed distributions and dependency problems |
| Notebooks | Kernelspec and notebook metadata |
| Explain error | Traceback classification with evidence |
| Repair plan | Dry-run steps derived from the last report |
| Discover | Bounded Windows Python discovery |
| Compare | Intended interpreter vs discovery evidence |

## Verification

- 188 engine tests, 5 Tkinter presentation tests, and 8 native bridge tests
  pass; one optional junction test is skipped.
- The WebView2 check confirms layout, both toggles (theme and language), the
  bridge surface, and a real discovery report (`report_scope:
  python_discovery`).
- Every bridge mode was exercised end-to-end, including a fixture with a missing
  dependency that produced a one-step `python -m pip install` repair plan.
- Both executables launched and stayed running.

## Known limitations

- The Tauri shell is not built. It requires Rust/Cargo and the MSVC build tools,
  which were unavailable. The React interface is delivered in WebView2.
- Tailwind CSS was not installable; the interface uses a hand-authored CSS layer.
- Theme and language switching are available in the React interface only; the
  Tkinter fallback stays English and dark.
- Repair execution is intentionally not exposed in the UI.
- The executables are unsigned, so SmartScreen may warn on first launch.
- No auto-update, telemetry, localization beyond English/Persian, or cloud
  service.

## Files

- `PyDoctor-UI.exe`: React interface, one-file build.
- `PyDoctor.exe`: Tkinter interface, one-file build.
- `README.txt`: quick start and safety.
- `SHA256SUMS.txt`: integrity hashes.
