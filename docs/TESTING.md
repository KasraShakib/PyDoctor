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

Fixture files are inert. No test executes a fixture interpreter. Existing real
CLI tests execute only the trusted Python running the test suite.

## Automated tests

From the project root in PowerShell:

```powershell
.\scripts\run-tests.ps1
```

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
```

Expected: exit 0, one JSON document on stdout, empty stderr.

- M1: schema 1.0, scope current_interpreter.
- M2: schema 1.1, scope python_discovery.
- M2 issues may indicate legitimate partial discovery.

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

M2/M3 acceptance requires source/document review, successful automatic tests,
Windows CLI checks, explicit safety semantics, and an actual junction result or
an acknowledged remaining junction limitation.
