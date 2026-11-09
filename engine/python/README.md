# PyDoctor Python Engine

This independent package implements read-only diagnostics for the interpreter running it. Distribution: `pydoctor-engine`; import package: `pydoctor` in `src/pydoctor`. Requires Python 3.12 or newer and has no runtime dependencies.

## Run without Installing

From `engine/python/src`:

```powershell
python -m pydoctor --pretty
python -m unittest discover -s ../tests -p "test_*.py" -v
```

The CLI reports the selected executable, Python version and implementation, prefixes, sys.path, and the VIRTUAL_ENV hint when present. It compares directory identity conservatively and does not infer overall environment health. It does not discover other installations, import packages under investigation, run pip, contact a network, or repair environments.

Use the interpreter belonging to the environment you want to observe; running the engine in its development venv reports that venv, not a separate IDE or notebook environment. Do not copy code into an untrusted environment as an implicit diagnostic launch strategy.

## Python API

`pydoctor.environment.diagnose_current_environment()` returns a `DiagnosticReport`. Its `to_dict()` result is JSON-serializable. Collection and evaluation also have separate entry points, `collect_runtime()` and `diagnose_runtime(runtime)`, for focused tests.

The report and CLI contract are documented in `docs/ENGINE_CONTRACT.md` relative to the repository root. Review local paths before sharing a report.

## Optional Development Setup

Only with approval for possible package downloads, from `engine/python`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Optional checks from the same directory:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m ruff check .
```

Neither installation nor these optional tools are required for M1 tests. Do not add runtime dependencies without a current diagnostic requirement.
