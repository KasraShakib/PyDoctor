# Native WebView2 Shell

`app.py` hosts the built React interface in the Windows WebView2 control using
`pywebview`, and exposes the read-only Python engine through a small JavaScript
API.

## Why WebView2 instead of Tauri

Tauri requires Rust, Cargo, and the MSVC build tools. None are installed and the
Rust download servers are unreachable here. WebView2 is already present on
Windows 11, so this shell delivers the React desktop experience without a Rust
toolchain. The Tauri shell remains the documented long-term target.

## Run from source

```powershell
.\scripts\run-desktop-ui.cmd
```

Requires `apps/desktop-ui/dist` to exist; run `scripts\build-ui.cmd` first.

## Bridge API

`Api` exposes three methods to JavaScript:

- `engine_info()`: engine metadata.
- `discover(project)`: schema 1.1 discovery.
- `run_report(mode, interpreter, project, payload)`: the selected report.

All calls are read-only. The shell never executes a target interpreter, imports
its packages, installs anything, or runs a repair step.

## Packaged self-check

The packaged executable can verify its own rendering without a human:

```powershell
$env:PYDOCTOR_SELF_CHECK_OUT="$env:TEMP\pyd.json"
.\dist\PyDoctor-UI.exe
Get-Content "$env:TEMP\pyd.json"
```

The verdict reports rendered character count, brand/mode/bridge presence, and
the exposed API method names.

## Packaging

`packaging/pydoctor-ui.spec` bundles the engine, `pywebview`, `pythonnet`, and
`apps/desktop-ui/dist` as `ui/`. Build with:

```powershell
cmd /c scripts\build-exe.cmd
```

## Tests

`apps/desktop_native/tests/test_api.py` covers the bridge contract and input
validation. Run the full suite with `cmd /c scripts\run-tests.cmd`.
