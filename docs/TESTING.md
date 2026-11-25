# Testing

## Policy

Use a known trusted Python 3.12+ interpreter. Do not install dependencies.

Record Python version, platform, command, exit code, failures, skips, and blocked
checks. Source delivery is not test execution. Do not infer Windows acceptance
from mocks or another operating system.

## Coverage

The original 21 M1 tests and the existing combined 82-test M1/M2 suite remain.

New tests cover:

- Inert text named python.exe and file-only confidence.
- Alias/directory identity isolation.
- Target syntax, relative paths, existence, directories, and permission errors.
- Exact Windows path relationships and regular-file identity.
- Missing or unsupported identity, zero inode, and hardlinks.
- Incomplete candidates, provenance paths, multiple sources, and conflicts.
- Partial/no-match/insufficient outcomes.
- Schema 1.2, immutability, deterministic output, and CLI argument validation.
- M1/M2 compatibility and launcher missing/timeout issue propagation.
- Optional real Windows junction behavior.
- PEP 440 ordering, specifier ranges, wildcards, and compatible releases.
- PEP 508 requirement parsing and bounded marker evaluation.
- `.dist-info`/`.egg-info` metadata parsing, missing fields, and unreadable files.
- Prefix derivation, site-packages discovery, and bounded enumeration.
- Satisfied, missing, conflicting, marker-gated, and Requires-Python results.
- Schema 1.3 package report and CLI argument validation.
- Kernelspec discovery, notebook metadata, missing kernels, and invalid notebooks.
- Traceback parsing, exception classification, and environment context.
- Repair plan derivation, approval checks, allowlist rejection, and fake-runner execution.
- Unified environment report aggregation.
- Engine metadata, version output, and extended CLI error envelopes.
- Desktop presentation helpers without starting Tk.

Fixture files are inert. No test executes a fixture interpreter. Existing real
CLI tests execute only the trusted Python running the test suite.

## Automated tests

From the project root in PowerShell:

```powershell
.\scripts\run-tests.ps1
```

If script execution is disabled, run `cmd /c scripts\run-tests.cmd` from the
project root. It performs the same PYTHONPATH setup and unittest discovery, then
runs the desktop presentation tests under `apps/desktop/tests`.

Also run the explicit unittest command with a temporary PYTHONPATH:

```powershell
$oldPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path (Get-Location) "engine\python\src")
    python -m unittest discover -s engine/python/tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "unittest failed: $LASTEXITCODE" }
}
finally {
    if ($null -eq $oldPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $oldPythonPath
    }
}
```

Expected: exit 0, no failures or errors. Capability-dependent hardlink and
junction skips must be reported. Do not invent a passed test count; record the
actual count printed by unittest.

pytest and Ruff are optional existing tools. Do not install them. If unavailable,
record them as not run or blocked.

## Real Windows CLI acceptance

From `engine/python/src`:

```powershell
python -m pydoctor --pretty
python -m pydoctor --discover --pretty
python -m pydoctor --inspect-packages "C:\Path\To\python.exe" --pretty
python -m pydoctor --environment-report "C:\Path\To\python.exe" --pretty
python -m pydoctor --inspect-notebooks "C:\Path\To\Project" --pretty
python -m pydoctor --explain-error "C:\Path\To\traceback.txt" --pretty
python -m pydoctor --repair-plan "C:\Path\To\report.json" --pretty
python -m pydoctor --info --pretty
python -m pydoctor --version
```

Expected: exit 0, one JSON document on stdout, empty stderr.

- M1: schema 1.0, scope current_interpreter.
- M2: schema 1.1, scope python_discovery.
- M4: schema 1.3, scope package_diagnostics.
- M7: schema 1.4, scope notebook_diagnostics.
- M8: schema 1.5, scope error_explanation.
- M9: schema 1.6, scope repair_plan.
- M10: schema 1.7, scope environment_report.
- M11: schema meta, scope engine_info.
- M2 issues may indicate legitimate partial discovery.

For M4, use the trusted engine interpreter path. Expected: exit 0, schema 1.3,
scope package_diagnostics, at least one observed site-packages root on a normal
installation, and findings that do not claim import or runtime health.
`python_version` may be null for a base installation without `pyvenv.cfg`; that
is reported as `packages.python_version_unverified`, not guessed.

Use the trusted engine interpreter path as M3's target:

```powershell
$knownPython = python -c "import sys; print(sys.executable)"
python -m pydoctor --compare-interpreter "$knownPython" --pretty
```

Expected: exit 0, schema 1.2, scope intended_interpreter_comparison,
target REGULAR_FILE, outcome MATCHED, and interpreter_verification NOT_VERIFIED.

The setup command executes only the already selected trusted Python, not a
discovered or arbitrary target.

Create temporary project fixtures and run:

```powershell
$fixture = Join-Path ([IO.Path]::GetTempPath()) ("pyd-accept-" + [guid]::NewGuid())
try {
    New-Item -ItemType Directory -Path "$fixture\.venv\Scripts" -Force | Out-Null
    Set-Content -LiteralPath "$fixture\.venv\Scripts\python.exe" `
        -Value "Inert fixture, not Python." -Encoding ASCII

    python -m pydoctor --discover --project "$fixture" --pretty
    if ($LASTEXITCODE -ne 0) { throw "Project discovery failed" }

    python -m pydoctor --compare-interpreter "$fixture\.venv\Scripts\python.exe" `
        --project "$fixture" --pretty
    if ($LASTEXITCODE -ne 0) { throw "Project comparison failed" }

    python -m pydoctor --compare-interpreter "$fixture\missing\python.exe" `
        --project "$fixture" --pretty
    if ($LASTEXITCODE -ne 0) { throw "Missing-target report failed" }
}
finally {
    if (Test-Path -LiteralPath $fixture) {
        Remove-Item -LiteralPath $fixture -Recurse -Force
    }
}
```

Expected:

- Project discovery includes project evidence for the inert .venv file.
- Project comparison is MATCHED by exact path, not a health verdict.
- Inert file version is not inferred from its contents or directory name.
- Missing target status is MISSING; it must not produce MATCHED.
- Every comparison target says interpreter_verification NOT_VERIFIED.

## Optional real junction acceptance

Run from the project root on Windows/Python 3.12+.

This fixture creates an ordinary temporary junction, not a symbolic link and
not a system setting. If the filesystem or local policy rejects creation,
record the junction acceptance as blocked. Do not elevate automatically.

```powershell
$fixture = Join-Path ([IO.Path]::GetTempPath()) ("pyd-junction-" + [guid]::NewGuid())
$oldPythonPath = $env:PYTHONPATH
$oldJunctionRoot = $env:PYD_JUNCTION_ROOT
try {
    New-Item -ItemType Directory -Path "$fixture\real" -Force | Out-Null
    Set-Content -LiteralPath "$fixture\real\python.exe" `
        -Value "Inert junction fixture." -Encoding ASCII
    New-Item -ItemType Junction -Path "$fixture\junction" `
        -Target "$fixture\real" -ErrorAction Stop | Out-Null

    $env:PYTHONPATH = (Join-Path (Get-Location) "engine\python\src")
    $env:PYD_JUNCTION_ROOT = $fixture
    python -m unittest discover -s engine/python/tests `
        -p "test_m2_finalization.py" -v
    if ($LASTEXITCODE -ne 0) { throw "Junction acceptance failed" }
}
finally {
    if (Test-Path -LiteralPath "$fixture\junction") {
        [IO.Directory]::Delete("$fixture\junction")
    }
    if (Test-Path -LiteralPath $fixture) {
        Remove-Item -LiteralPath $fixture -Recurse -Force
    }
    if ($null -eq $oldPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $oldPythonPath
    }
    if ($null -eq $oldJunctionRoot) {
        Remove-Item Env:PYD_JUNCTION_ROOT -ErrorAction SilentlyContinue
    }
    else {
        $env:PYD_JUNCTION_ROOT = $oldJunctionRoot
    }
}
```

The junction is explicitly removed before recursive cleanup. No fixture file is
executed. Without PYD_JUNCTION_ROOT, this optional integration test is skipped.

## Acceptance record

The earlier Linux run recorded 82 passing tests on Python 3.11.16. The founder's
November 10 audit reports successful Windows checks for the previous M2 version.

Neither result validates the new finalization or M3 code. Their results must be
recorded by the implementation agent after applying this delivery.

M4 delivery was verified locally on Windows with Python 3.12.9: 158 unittest
tests passed with one optional junction test skipped. The M4 CLI was run against
`C:\Program Files\Python312\python.exe` and returned schema 1.3 with 129 observed
distributions and no missing or conflicting dependency findings for that
environment. `python_version` was null because the base installation has no
`pyvenv.cfg`; the report recorded `packages.python_version_unverified`.

M5-M11 delivery was verified locally on Windows with Python 3.12.9: 188 engine
tests, 5 Tkinter presentation tests, and 8 native bridge tests passed, with one
optional junction test skipped. CLI smoke checks covered `--info`, `--version`,
`--environment-report`, `--inspect-packages`, `--repair-plan`,
`--explain-error`, and `--inspect-notebooks`. No repair was executed.

M5/M6 packaging was verified on the same machine:

- The React interface rendered in WebView2 with the bridge exposed
  (`discover,engine_info,run_report`).
- `dist/PyDoctor.exe` launched and stayed running.
- `dist/PyDoctor-UI.exe` launched and its packaged self-check returned
  `{"chars": 582, "brand": true, "mode": true, "bridge": true, ...}`.
- The Tauri shell was not built because Rust/Cargo and MSVC are unavailable.

## Packaged UI self-check

The React executable can verify its own rendering:

```powershell
$env:PYDOCTOR_SELF_CHECK_OUT="$env:TEMP\pyd.json"
.\dist\PyDoctor-UI.exe
Get-Content "$env:TEMP\pyd.json"
```

The verdict includes rendered character count, brand/mode/bridge presence, and
the bridge API method names. A missing or false field is a packaging failure.

M2/M3 acceptance requires source/document review, successful automatic tests,
Windows CLI checks, explicit safety semantics, and an actual junction result or
an acknowledged remaining junction limitation.
