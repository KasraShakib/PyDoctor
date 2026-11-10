# PyDoctor Python Engine

Read-only Python runtime, Windows discovery, and intended-interpreter comparison.

Requires a known trusted Python 3.12+ interpreter. Runtime dependencies: none.

## Source CLI

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
| M1 | 1.0 | current_interpreter |
| M2 | 1.1 | python_discovery |
| M3 | 1.2 | intended_interpreter_comparison |

`--pretty` only changes indentation. Discovery and comparison are mutually
exclusive. `--project` is allowed only with discovery or comparison.

M3 requires an absolute target path. A syntactically invalid target produces a
schema 1.2 uncertainty report without discovery. A valid but missing target
still gets discovery and comparison evidence.

## Meaning and safety

M2 CONFIRMED confirms regular-file observation only. An inert text file named
python.exe may receive this bounded confidence together with
interpreter_not_verified.

M3 MATCHED confirms a normalized-path or file-identity relationship only.
interpreter_verification always remains NOT_VERIFIED.

No intended or discovered interpreter, package manager, activation script, or
user package is executed. The sole discovery subprocess is the documented
installed-location legacy launcher listing.

No packages, project files, environments, PATH, or Registry entries are changed.
No network request, recursive scan, repair, or automatic selection is performed.

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
