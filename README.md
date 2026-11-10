# PYD / PyDoctor

PYD is an engine-first Windows Python environment diagnosis project.

The engine currently supports:

- M1: observation of the Python process running the engine.
- M2: bounded, read-only discovery of Windows Python environment candidates.
- M3: comparison of an explicitly intended interpreter path with M2 evidence.

No desktop application, package inventory, dependency diagnosis, notebook
diagnosis, automatic interpreter selection, repair, or distribution packaging
is implemented.

## Run from source

Use a known, trusted Python 3.12+ interpreter.

From `engine/python/src`:

```powershell
python -m pydoctor --pretty
python -m pydoctor --discover --pretty
python -m pydoctor --discover --project "C:\Path\To\Project" --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --project "C:\Path\To\Project" --pretty
```

| Mode | Schema | Scope |
| --- | --- | --- |
| Default M1 | 1.0 | current_interpreter |
| M2 discovery | 1.1 | python_discovery |
| M3 comparison | 1.2 | intended_interpreter_comparison |

`--discover` and `--compare-interpreter` are mutually exclusive.
`--project` requires one of these modes.

M3 requires an absolute target path. Relative paths and invalid target syntax
produce an uncertainty report, not an implicit cwd-based selection.

## What the evidence means

A regular file named `python.exe` may be inert text or an invalid executable.

M2 candidate `CONFIRMED` means only that a regular file was observed. The
`interpreter_not_verified` issue explicitly records the missing verification.

M3 `MATCHED` means a path or file-identity relationship was established. It
does not mean the file is Python, runnable, safe, compatible, or healthy.
The target field `interpreter_verification` remains `NOT_VERIFIED`.

WindowsApps paths are treated conservatively as alias evidence.

## Safety

The engine does not execute intended or discovered Python interpreters, import
their packages, activate environments, change PATH or Registry, install packages,
repair environments, recursively scan disks, or make network requests.

The sole discovery subprocess is the legacy Python Launcher's `-0p` listing,
resolved from documented conventional installed locations. This policy trusts
the invoking environment and installed locations; it is not signature validation.

Normal startup behavior of the trusted Python running PYD is outside the
collector's control. Reports contain local paths; review them before sharing.

## Test

From the project root:

```powershell
.\scripts\run-tests.ps1
```

Alternatively, set `PYTHONPATH` to `engine/python/src` and run:

```powershell
python -m unittest discover -s engine/python/tests -p "test_*.py" -v
```

No dependency installation is required. See `docs/TESTING.md` for the exact
acceptance procedure and optional real Windows junction coverage.

## Status and documentation

M1 is accepted at baseline commit
`9ceeacf414c6799b5d093aa7320a2d5f06a7af66`.

The founder's November 10, 2026 audit reports successful Windows M2 tests and
CLI checks. The finalization changes and M3 delivery still require execution
and review before acceptance. No new commit is authorized.

- `docs/ENGINE_CONTRACT.md`: report, matching, error, and safety semantics.
- `docs/ARCHITECTURE.md`: module boundaries.
- `docs/M2_DISCOVERY.md`: discovery acceptance and intentional limitations.
- `docs/TESTING.md`: automated and real Windows acceptance.
- `docs/ROADMAP.md`: milestone gates and deferred work.
