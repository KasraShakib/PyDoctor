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
```

Default invocation observes the Python running PYD, not the comparison target.
M3 never executes the target. Target paths must be absolute and are not expanded
from environment variables or resolved against cwd.

Discovery and comparison support explicit project context. No recursive project
scan or automatic environment activation is performed.

## Tests

From the project root:

```powershell
.\scripts\run-tests.ps1
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

The historical Node.js, Rust, Cargo, Tauri CLI, C++ Build Tools, and WebView2
readiness limitations do not block engine tests. No desktop scaffold or
toolchain installation is part of M1–M3.

## Applying a text delivery

Validate paths under the project root, inspect existing files, and back up
replaced files before applying complete replacements. Do not overwrite an
unexpected CREATE target or silently merge divergent code.

Run the specified tests and report actual results. Do not independently change
the delivered code, install tools, commit, or push.
