# Testing

## Current Coverage

M1 includes 21 standard-library tests covering package import/version, runtime collection, base and isolated prefix observations, absent and empty activation hints, matching and different directory identities, relative/missing/inaccessible paths, UNKNOWN guidance, Unicode JSON, runtime non-mutation, CLI output/error streams, argument validation, and a real module invocation.

Tests create and clean up temporary fixture directories; the diagnostic collector itself performs no repairs. Confidence is tested independently from command exit status.

## Offline Python Engine Tests

Requires Python 3.12 or newer. No installation, network access, pytest, or desktop tools are required.

From the repository root in PowerShell:

```powershell
.\scripts\run-tests.ps1
```

The runner selects `engine/python/.venv/Scripts/python.exe` if present, otherwise `python`. It temporarily sets PYTHONPATH to the source directory, restores the prior value and working directory, and forwards the test exit code. PowerShell execution policy is not changed; if the script is blocked, use the direct command below.

Portable alternative, from `engine/python/src`:

```powershell
python -m unittest discover -s ../tests -p "test_*.py" -v
```

Expected result: `Ran 21 tests` and `OK`, with exit code 0. A lower test count or an unexecuted command is not full acceptance. The tests also remain discoverable by pytest when that optional tool is available.

## Manual Runtime Verification

From `engine/python/src`:

```powershell
python -m pydoctor --pretty
```

Expect exactly one JSON report on stdout and no stderr. Verify `runtime.executable`, `runtime.prefix`, and `runtime.base_prefix` against the Python selected in that terminal. Repeat from an already available virtual environment if desired; no environment creation is necessary. Exit 0 means collection completed, not that every environment problem was ruled out. UNKNOWN and LIKELY findings are valid successful reports. See `docs/ENGINE_CONTRACT.md`.

## Optional Linting and pytest

No new tools are installed by this milestone. If the optional development environment already exists, run from `engine/python`:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Otherwise report these checks as blocked by unavailable optional tools; do not claim they passed or install them automatically.

## Desktop Tests

Desktop tooling remains undefined until the official Tauri React + TypeScript scaffold is generated. No desktop test or build is included in M1.

## Verification Rules

- Record the interpreter version and platform used for each run.
- Windows acceptance requires execution on the founder's Windows/Python environment.
- Record passed, failed, blocked, and skipped checks separately.
- Do not infer target-Python compatibility from a run on an older or different runtime.
- Keep engine tests independent from the desktop application.
