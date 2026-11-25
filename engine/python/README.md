# PyDoctor Python Engine

Read-only Python runtime, Windows discovery, intended-interpreter comparison,
package/dependency diagnostics, notebook and traceback analysis, dry-run repair
planning, and a unified environment report.

Requires a known trusted Python 3.12+ interpreter. Runtime dependencies: none.

## Source CLI

From `engine/python/src`:

```powershell
python -m pydoctor --pretty
python -m pydoctor --discover --pretty
python -m pydoctor --discover --project "C:\Path\To\Project" --pretty
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

| Mode | Schema | Scope |
| --- | --- | --- |
| M1 | 1.0 | current_interpreter |
| M2 | 1.1 | python_discovery |
| M3 | 1.2 | intended_interpreter_comparison |
| M4 | 1.3 | package_diagnostics |
| M7 | 1.4 | notebook_diagnostics |
| M8 | 1.5 | error_explanation |
| M9 | 1.6 | repair_plan |
| M10 | 1.7 | environment_report |
| M11 | meta | engine_info |

`--pretty` only changes indentation. All inspection modes are mutually
exclusive. `--project` is allowed only with discovery, comparison, or the
environment report. `--interpreter` supplies intended-interpreter context for
notebook and error diagnosis.

M3 requires an absolute target path. A syntactically invalid target produces a
schema 1.2 uncertainty report without discovery. A valid but missing target
still gets discovery and comparison evidence.

## Meaning and safety

M2 CONFIRMED confirms regular-file observation only. An inert text file named
python.exe may receive this bounded confidence together with
interpreter_not_verified.

M3 MATCHED confirms a normalized-path or file-identity relationship only.
interpreter_verification always remains NOT_VERIFIED.

M4 SATISFIED confirms that observed distribution metadata satisfies a declared
clause. It does not confirm import success or runtime health. Unsupported
markers, direct references, and unparseable syntax remain UNKNOWN.

M7 kernel evidence does not prove that a kernel launches or that a notebook
executes. M8 explanations are bounded by the supplied traceback and optional
metadata. M9 plans are dry-run; building a plan executes nothing.

No intended or discovered interpreter, package manager, activation script,
kernel, or user package is executed or imported. The sole discovery subprocess
is the documented installed-location legacy launcher listing.

No packages are installed or removed, and no project files, environments, PATH,
or Registry entries are changed. No network request, recursive scan, repair, or
automatic selection is performed. M9 execution is a separate library API, not a
CLI mode, and requires an exact step id plus an allowlisted
`python -m pip install` argv.

Handled failures emit a JSON error envelope on stderr and exit non-zero; see
`docs/QUALITY.md` for the codes and bounded collection limits.

## Tests

From the repository root:

```powershell
.\scripts\run-tests.ps1
```

Or set PYTHONPATH to `engine/python/src` and run:

```powershell
python -m unittest discover -s engine/python/tests -p "test_*.py" -v
```

No pytest or Ruff installation is necessary. See `docs/TESTING.md` for acceptance,
including the optional real junction fixture.

The definitive report and exit-code semantics are in `docs/ENGINE_CONTRACT.md`.
