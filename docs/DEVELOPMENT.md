# Development Setup

## Environment Audit

Audit date: 2026-11-09

Operating system: Microsoft Windows 11 Pro, version 10.0.26200, 64-bit.

| Tool | Status | Version | Executable path |
| --- | --- | --- | --- |
| Git | Installed | 2.48.1.windows.1 | `C:\Program Files\Git\cmd\git.exe` |
| Python | Installed | 3.12.9 | `C:\Program Files\Python312\python.exe` |
| Node.js | Missing | — | — |
| npm | Missing | — | — |
| Rust | Missing | — | — |
| Cargo | Missing | — | — |

Additional observations:

- `python3` resolves to a Windows Apps stub at `C:\Users\ACER\AppData\Local\Microsoft\WindowsApps\python3.exe`; use the explicit Python 3.12 path or the `python` command.
- pip 26.3 is available for the installed Python 3.12 interpreter.
- setuptools 84.0.0 and wheel 0.46.3 are installed for Python 3.12.
- pytest and Ruff are not installed yet.
- The C: drive had approximately 38.06 GB free at audit time. This is sufficient for initial development, but dependency and build caches should be monitored.
- The PATH contains a reference to `D:\apps\nodejs`, but that path and drive were not available during the audit.
- The Tauri CLI is not installed.
- The official Tauri Windows prerequisites include Microsoft C++ Build Tools and WebView2. These have not been verified.

No global software was installed, no PATH changes were made, and no system settings were modified during this audit.

## Prerequisites for Desktop Development

Before generating the Tauri desktop application, install or verify:

1. Node.js LTS and npm.
2. Rust stable with the MSVC toolchain selected as the default host.
3. Microsoft C++ Build Tools with the "Desktop development with C++" workload.
4. Microsoft Edge WebView2 Runtime.
5. The Tauri CLI or use the npm-based `create-tauri-app` workflow.

Restart the terminal after installing these tools so executable paths are refreshed. Do not install global tools without explicit project approval.

## Desktop Scaffold

The official Tauri workflow is documented at:

- <https://v2.tauri.app/start/create-project/>
- <https://v2.tauri.app/start/prerequisites/>

When the prerequisites are available, scaffold inside `apps/desktop` using:

```powershell
npm create tauri-app@latest .
```

Select React and TypeScript. Review the generated files and dependency versions before installing dependencies. Keep all generated project files inside `apps/desktop`.

## Python Engine Setup

Python 3.12 or newer is required. The M1 CLI and standard-library tests can run directly from source without installing any packages. From `engine/python/src`:

```powershell
python -m pydoctor --pretty
python -m unittest discover -s ../tests -p "test_*.py" -v
```

These commands use the selected `python` interpreter, not an automatically discovered target environment. Reports contain local paths; inspect them before sharing.

### Optional Development Tools

Only after approval for package installation, run the following from `engine/python`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

This creates an isolated environment and installs the engine and development tools. Installation may download packages; it is not required for M1 verification and is not authorized by the implementation package. The `.venv` directory is ignored by Git.

## Repository Commands

Run engine tests from the repository root:

```powershell
.\scripts\run-tests.ps1
```

Inspect repository state:

```powershell
git status
git diff
```

No remote is configured. Do not publish or push this repository as part of initial setup.

## Known Setup Blockers

- Node.js and npm are unavailable, so the official React/TypeScript Tauri scaffold cannot be generated.
- Rust and Cargo are unavailable, so the Tauri shell cannot be built.
- Tauri Windows build prerequisites have not been verified.
- Optional Python development dependencies were absent at the snapshot audit. They are no longer required for the standard-library tests; pytest and Ruff checks remain blocked until separately approved and installed.
