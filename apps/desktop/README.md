# Tkinter Desktop (Fallback)

This directory holds the zero-dependency Tkinter interface. It invokes the
Python engine and renders its JSON reports; all diagnostic logic stays in
`engine/python`.

The primary React interface now lives in `apps/desktop-ui` and is hosted by
`apps/desktop_native` in WebView2. This Tkinter app is retained as a fallback
that needs only the Python standard library.

## Status

A working stdlib Tkinter interface is implemented and runs without Node.js,
Rust, or network access:

- `pydoctor_ui.py`: the application (interpreter picker, project picker, mode
  selector, background execution, Summary / Details / Raw JSON tabs).
- `ui_model.py`: pure formatting helpers, unit tested without starting Tk.
- `tests/test_ui_model.py`: presentation tests.

The React interface is delivered in `apps/desktop-ui`; the Tauri shell remains
the long-term target and is not built because Rust/Cargo and MSVC are
unavailable. Do not claim a Tauri build from source scaffolding alone.

## Run

From the project root:

```powershell
.\scripts\run-desktop.cmd
```

Or directly:

```powershell
python apps\desktop\pydoctor_ui.py
```

The launcher puts `engine/python/src` and `apps/desktop` on `PYTHONPATH`, so no
installation is required.

## What the interface does

- Lists discovered interpreters and lets the user pick one, or browse for a
  `python.exe`.
- Optionally accepts a project directory.
- Runs one of: full environment report, package report, notebook report, error
  explanation, or repair plan.
- Shows a human-readable summary, detailed findings with severity, confidence,
  evidence, and next steps, plus the raw JSON.
- Reports loading, empty, and error states explicitly.

`F5` runs a full report and `Ctrl+O` opens the interpreter picker.

## Boundaries

- The desktop never re-implements diagnostic rules and never executes repairs.
- Reports are produced by `python -m pydoctor` and parsed in-process.
- A Tauri build, when the toolchain exists, must keep the engine separate and
  must not embed Python logic into the frontend.

## Future Tauri scaffold

When the prerequisites are installed, the official Tauri 2 `create-tauri-app`
utility is the documented path:

```powershell
npm create tauri-app@latest .
```

Select the React template, TypeScript flavor, and npm package manager, then
review the generated configuration and versions rather than assuming them.
