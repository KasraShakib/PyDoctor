# Architecture

## Status

PYD is an engine-first project. M1 observes the engine runtime, M2 discovers
Windows candidates, M3 compares an explicitly intended interpreter path against
discovery evidence, and M4 reads installed distribution metadata for an explicit
interpreter path. M7 adds notebook/kernel evidence, M8 explains tracebacks, M9
plans safe repairs, and M10 aggregates evidence into one environment report.

The desktop layer has two front ends that render engine reports: a React 18
interface hosted in the native Windows WebView2 control, and a stdlib Tkinter
fallback. Both are packaged with PyInstaller. The Tauri shell remains the
long-term target and is not built in the current environment.

## Component boundaries

### Python engine

Location: `engine/python`; package: `pydoctor`.

- `models.py`: immutable runtime, finding, confidence, and severity models.
- `environment.py`: current-process observation and activation-hint evaluation.
- `discovery_models.py`: immutable M2 hints, provenance, issues, and candidates.
- `discovery_registry.py`: bounded read-only PEP 514 collection.
- `discovery_sources.py`: launcher, PATH, active hints, and opt-in project sources.
- `discovery_normalization.py`: shared path rules and deterministic M2 merging.
- `discovery.py`: independent source orchestration.
- `comparison_models.py`: immutable schema 1.2 models.
- `interpreter_target.py`: explicit target syntax validation and metadata observation.
- `comparison.py`: candidate relationship analysis and M2 reuse.
- `versions.py`: bounded PEP 440 version and specifier evaluation.
- `requirements.py`: bounded PEP 508 requirement and marker parsing.
- `package_models.py`: immutable schema 1.3 inventory and dependency models.
- `package_metadata.py`: `.dist-info`/`.egg-info` metadata reading.
- `package_inventory.py`: prefix derivation, site-packages discovery, enumeration.
- `dependency_analysis.py`: requirement, marker, and Requires-Python evaluation.
- `package_diagnostics.py`: package report orchestration and findings.
- `notebook_models.py` / `notebooks.py`: kernelspec and notebook metadata evidence.
- `error_models.py` / `error_explainer.py`: traceback parsing and explanation.
- `repair_models.py` / `repair.py`: dry-run plans and guarded execution.
- `environment_models.py` / `environment_report.py`: aggregate report.
- `__main__.py`: argument validation, orchestration, and JSON streams.

Target validation does not discover sources. Comparison does not implement a
second discovery engine. Package diagnostics reuse the M3 target observation and
do not execute the target. Notebook diagnostics do not launch kernels. Error
explanation does not execute traceback code. Repair planning does not execute
steps. CLI code contains no matching, dependency, notebook, or repair rules.

### React interface

Location: `apps/desktop-ui`.

- `index.html`: loads React 18 UMD from `vendor/`.
- `app.js`: interface built with `React.createElement`; no bundler required.
- `styles.css`: hand-authored dark theme.
- `dist/`: generated static bundle consumed by the shell and the executable.

The interface calls only the bridge API. It contains no diagnostic rules.

### Native shell

Location: `apps/desktop_native`.

- `app.py`: `pywebview` window over WebView2 plus the `Api` bridge.
- `tests/test_api.py`: bridge contract and input validation.

`Api` exposes `engine_info`, `discover`, and `run_report`. It calls engine
functions in-process and returns their JSON structures. It never executes a
target interpreter, imports packages, installs anything, or runs a repair.

### Tkinter fallback

Location: `apps/desktop`.

- `pydoctor_ui.py`: Tkinter window, background worker threads, and report tabs.
- `ui_model.py`: pure formatting helpers, tested without starting Tk.
- `tests/test_ui_model.py`: presentation tests.

It uses only the standard library and remains available if WebView2 or the
packaged React bundle is unavailable.

### Packaging

Location: `packaging`.

- `pydoctor-tk.spec`: one-file `PyDoctor.exe`.
- `pydoctor-ui.spec`: one-file `PyDoctor-UI.exe` with the `ui/` bundle,
  `pywebview`, and `pythonnet`.

`scripts/build-ui.py` assembles the React bundle; `scripts/build-exe.cmd` runs
both PyInstaller specs.

### Branding assets

Location: `assets`.

- `icon-ui.ico`: multi-size Windows icon (cyan accent ring) embedded in
  `PyDoctor-UI.exe` and loaded by the React header.
- `icon-tk.ico`: multi-size Windows icon (amber accent ring) embedded in
  `PyDoctor.exe` and set by the Tkinter window.
- `icon.ico`: copy of `icon-ui.ico`, retained as a generic fallback.
- `icon.svg`: vector mark loaded by the React header.
- `icon-256.png`: preview.

`scripts/make-icon.py` is the single source of the geometry and regenerates all
files, producing both accent variants from the same geometry.

## Integration boundary

Explicit local CLI modes return independent versioned reports:

- M1: schema 1.0, `current_interpreter`.
- M2: schema 1.1, `python_discovery`.
- M3: schema 1.2, `intended_interpreter_comparison`.
- M4: schema 1.3, `package_diagnostics`.
- M7: schema 1.4, `notebook_diagnostics`.
- M8: schema 1.5, `error_explanation`.
- M9: schema 1.6, `repair_plan`.
- M10: schema 1.7, `environment_report`.
- M11: schema `meta`, `engine_info`.

The default command remains M1. All other modes are opt-in. The authoritative
report semantics are in `ENGINE_CONTRACT.md`.

## Evidence and identity

M2 merges normalized paths and accessible regular-file device/inode identities.
Provenance preserves original executable paths and conflicting metadata.
Directories and WindowsApps aliases do not provide identity merge keys.

M3 checks all established executable paths retained in candidate provenance.
It never substitutes a prefix, basename, version, or source location for an
executable path. Device/inode identity follows links and junctions where the
filesystem supplies a usable identity.

Observations are point-in-time snapshots, not stable file handles or health
checks. Identity failure is explicit uncertainty.

M4 derives a prefix from the conventional executable layout and reads only
recognized metadata files under conventional site-packages roots. Distribution
metadata is evidence of installation metadata, not of import success, native
extension loading, or runtime health. Missing or unsupported syntax becomes an
explicit UNKNOWN result.

M7 reads kernelspec and notebook JSON without launching a kernel or cell. M8
parses supplied traceback text without executing it. M9 builds plans without
executing them; its guarded executor is separate and allowlisted. M10 reuses
existing reports rather than implementing new collectors.

## Dependency policy

The engine runtime remains standard-library-only. pytest and Ruff are optional
development tools, not prerequisites for unittest or the CLI. The Tkinter UI is
part of the standard library on Windows CPython. The React shell adds
`pywebview` and `pythonnet` as desktop-only dependencies; they are not imported
by the engine or its tests.

## Safety and privacy

No intended or discovered interpreter is executed. No package is imported for
investigation, and no repair or environment mutation is performed. M4 does not
run pip, resolve direct URLs, or download packages. M7 does not launch kernels.
M8 does not execute traceback code. M9 does not execute plans from the CLI.

M2's installed-location launcher listing is the sole collection subprocess.
Installed-location trust is not signature verification. Filesystem metadata
access may block on remote locations; count limits are not filesystem deadlines.

Python startup hooks and bytecode caching of the trusted engine process remain
normal Python behavior. Reports may expose usernames, filesystem paths, source
metadata, and bounded launcher diagnostics. There is no telemetry or network
transfer.
