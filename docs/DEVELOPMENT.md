# Development Setup

## Historical environment audit

Audit date: 2026-11-09.

Windows 11 Pro 10.0.26200, 64-bit.

| Tool | Recorded status | Recorded version |
| --- | --- | --- |
| Git | Installed | 2.48.1.windows.1 |
| Python | Installed | 3.12.9 |
| Node.js / npm | Missing | - |
| Rust / Cargo | Missing | - |
| pytest / Ruff | Missing | - |

Recorded Python: `C:\Program Files\Python312\python.exe`.

The recorded `python3` command resolved to a WindowsApps stub. Use a known
trusted interpreter rather than assuming an alias is a working Python runtime.

The audit recorded pip 26.3, setuptools 84.0.0, wheel 0.46.3, approximately
38.06 GB free on C:, an unavailable `D:\apps\nodejs` PATH reference, and no
verified Tauri Windows prerequisites.

These are historical observations, not current toolchain verification. No
global software, PATH, or system settings were changed by that audit.

## Python engine

Python 3.12+ is required. No package installation is needed for source execution.

From `engine/python/src`:

```powershell
python -m pydoctor --pretty
python -m pydoctor --discover --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --project "C:\Path\To\Project" --pretty
python -m pydoctor --inspect-packages "C:\Path\To\python.exe" --pretty
python -m pydoctor --inspect-notebooks "C:\Path\To\Project" --interpreter "C:\Path\To\python.exe" --pretty
python -m pydoctor --explain-error "C:\Path\To\traceback.txt" --pretty
python -m pydoctor --repair-plan "C:\Path\To\report.json" --pretty
python -m pydoctor --environment-report "C:\Path\To\python.exe" --project "C:\Path\To\Project" --pretty
python -m pydoctor --info --pretty
python -m pydoctor --version
```

Default invocation observes the Python running PYD, not the comparison target.
M3 never executes the target. Target paths must be absolute and are not expanded
from environment variables or resolved against cwd.

Discovery and comparison support explicit project context. No recursive project
scan or automatic environment activation is performed. Package, notebook, error,
repair-plan, and environment modes are read-only; see `QUALITY.md` for limits
and error envelopes.

## Desktop interface

The primary desktop interface is React 18 hosted in WebView2. It needs no
Node.js, Rust, or network access at runtime.

From the project root:

```powershell
cmd /c scripts\build-ui.cmd
.\scripts\run-desktop-ui.cmd
```

The Tkinter fallback needs only the standard library:

```powershell
.\scripts\run-desktop.cmd
```

Both launchers set `PYTHONPATH` for you. The React shell requires `pywebview` and
`pythonnet`; the engine and its tests do not.

## Build executables

```powershell
cmd /c scripts\build-ui.cmd
cmd /c scripts\build-exe.cmd
```

Outputs are `dist/PyDoctor.exe` and `dist/PyDoctor-UI.exe`. PyInstaller is
required. Verify the packaged React app with `PYDOCTOR_SELF_CHECK_OUT` as
described in `TESTING.md`.

For the portable release folder and zip:

```powershell
cmd /c scripts\build-release.cmd
```

Output is `release/PyDoctor-0.2.0-win64/` and
`release/PyDoctor-0.2.0-win64.zip`. These generated artifacts are gitignored;
attach the zip to a GitHub release instead of committing it.

## Regenerate the icon

```powershell
python scripts\make-icon.py
```

This rewrites `assets/icon.ico`, `assets/icon-256.png`, and `assets/icon.svg`.
Rebuild the executables afterwards to embed the new icon.

## Tests

From the project root:

```powershell
.\scripts\run-tests.ps1
```

If PowerShell script execution is disabled by policy, use the batch runner:

```powershell
cmd /c scripts\run-tests.cmd
```

For explicit unittest commands, CLI acceptance, temporary fixtures, and optional
junction verification, follow `TESTING.md`.

Reports expose local paths. Inspect them before sharing.

## Optional development environment

Only with separate package-installation approval, an isolated development
environment may be created from `engine/python`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

This is not required or authorized by the M2/M3 delivery. It can download
packages and must not be performed automatically.

If optional tools already exist:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Otherwise report them unavailable. Do not install dependencies to make a
verification report look complete.

## Desktop status

The React interface and both standalone executables are built and verified. The
Tauri shell is not built: Rust/Cargo, the Tauri CLI, and the MSVC build tools are
unavailable, and the Rust and npm registries are unreachable. Tailwind could not
be installed, so the React interface uses a hand-authored CSS layer. These
limitations do not block the engine, the React UI, the Tkinter fallback, or the
PyInstaller builds.

## Applying a text delivery

Validate paths under the project root, inspect existing files, and back up
replaced files before applying complete replacements. Do not overwrite an
unexpected CREATE target or silently merge divergent code.

Run the specified tests and report actual results. Do not independently change
the delivered code, install tools, commit, or push.
