# PyDoctor (PYD)

PyDoctor is a planned professional Windows desktop application for diagnosing Python environment issues. Its intended focus includes dependency conflicts, import failures, and common Python and Jupyter problems.

The repository includes its first read-only diagnostic slice: a versioned JSON report of the current Python interpreter, runtime prefixes, import search paths, and optional shell activation evidence. The desktop application is not scaffolded yet.

## Proposed Direction

- React and TypeScript for the desktop interface
- Tauri for the Windows desktop shell
- A separate Python diagnostic engine
- Independently testable desktop and engine components

The technology direction is provisional. Dependencies and versions should be added only when needed and when supported by the installed toolchain.

## Repository Layout

```text
PYD/
├── apps/desktop/          # Reserved for the React + TypeScript + Tauri app
├── engine/python/         # Python diagnostic engine package and tests
├── scripts/               # Project automation scripts
└── docs/                  # Product, architecture, testing, and development notes
```

## Current Status

- Project structure and initial documentation created.
- Initial Python runtime diagnostics and an offline JSON CLI implemented.
- Standard-library tests run without installing the engine, pytest, or Ruff.
- Python engine package retains optional pytest and Ruff development settings.
- Local Git repository initialized; no remote configured.
- Desktop application scaffold not generated because Node.js, npm, Rust, and Cargo are not installed.
- No Python or JavaScript dependencies installed yet.

## Environment Summary

| Tool | Status | Version | Path |
| --- | --- | --- | --- |
| Git | Installed | 2.48.1.windows.1 | `C:\Program Files\Git\cmd\git.exe` |
| Python | Installed | 3.12.9 | `C:\Program Files\Python312\python.exe` |
| Node.js | Missing | — | — |
| npm | Missing | — | — |
| Rust | Missing | — | — |
| Cargo | Missing | — | — |

The C: drive had approximately 38.06 GB free at audit time. See `docs/DEVELOPMENT.md` for the full audit and setup prerequisites.

## Development Entry Points

- Environment and setup notes: `docs/DEVELOPMENT.md`
- Product scope: `docs/PRODUCT_SPEC.md`
- Component boundaries: `docs/ARCHITECTURE.md`
- Test approach: `docs/TESTING.md`
- Engineering rules: `AGENTS.md`

Run the engine tests from the repository root with Python 3.12 or newer; no dependency installation is required:

```powershell
.\scripts\run-tests.ps1
```

For a diagnostic report, change to `engine/python/src` and run:

```powershell
python -m pydoctor --pretty
```

This reports only the interpreter executing the command. It does not scan other installations, check packages, or repair anything. Paths in the report can contain personal information; review them before sharing. See `docs/ENGINE_CONTRACT.md` for the JSON contract.
