# PyDoctor Product Specification

## Purpose

Help Windows users understand Python interpreter and environment choices through
explainable evidence, without silently selecting or modifying an environment.

## Product principles

- Evidence before assumptions.
- CONFIRMED, LIKELY, and UNKNOWN describe a bounded observation, not severity.
- Preserve source provenance, conflicts, and missing information.
- Never claim that a file is valid Python or healthy without relevant verification.
- Do not execute unknown interpreters for inspection.
- Keep collection read-only, bounded, and standard-library-only.
- Keep the engine independently testable before adding a desktop interface.

## Current engine capabilities

### M1: Current interpreter

Observe the trusted process running PYD: executable, version, implementation,
prefixes, sys.path, and the VIRTUAL_ENV hint. Emit schema 1.0 with scope
`current_interpreter`.

This does not inspect another interpreter or diagnose packages.

### M2: Windows discovery

Collect current-runtime evidence, PEP 514 registrations, the installed legacy
launcher's listing, direct PATH entries, active-environment hints, and optional
project-local environment roots.

Emit schema 1.1 with scope `python_discovery`.

Registrations, aliases, incomplete directories, and regular files remain
evidence rather than a guaranteed inventory of runnable Python installations.

### M3: Intended interpreter comparison

Accept an explicit absolute interpreter path, observe its file metadata, reuse
M2, and explain its relationship to candidate executable paths and file identities.

Emit schema 1.2 with scope `intended_interpreter_comparison`.

Outcomes are MATCHED, PARTIALLY_MATCHED, NO_MATCH, and INSUFFICIENT_EVIDENCE.
None is an interpreter-health result or an automatic selection decision.

### M4: Package inventory and dependency diagnostics

Accept an explicit interpreter path, derive its conventional environment prefix,
and read installed `.dist-info`/`.egg-info` metadata without executing the target
or importing packages.

Emit schema 1.3 with scope `package_diagnostics`.

Report observed distributions, duplicate names, missing dependencies, version
conflicts, Requires-Python results, and inconclusive clauses. SATISFIED is a
metadata result, not an import or health verdict. Unsupported markers, extras,
direct references, and unparseable syntax remain UNKNOWN. Findings carry an
INFO/WARNING/ERROR severity separate from evidence confidence.

### M5: Desktop interface

A React 18 interface hosted in the native Windows WebView2 control presents
interpreter, package, notebook, error, repair-plan, discovery, and comparison
reports. It offers summary, details, and raw JSON views plus explicit loading,
empty, and error states. A stdlib Tkinter application is retained as a fallback.

The Tauri shell remains the target. It is not built because Rust/Cargo and the
MSVC build tools are unavailable. Tailwind could not be installed either; the
interface uses a hand-authored CSS layer.

### M6: Windows packaging

PyInstaller builds two one-file executables: `PyDoctor.exe` (Tkinter) and
`PyDoctor-UI.exe` (React + WebView2). The React build embeds the static bundle
and supports a packaged render self-check. A Tauri bundle still requires a
prepared Rust/MSVC toolchain.

### M7: Notebook diagnostics

Read conventional Jupyter kernelspecs and notebook metadata without launching a
kernel or executing cells. Emit schema 1.4 with scope `notebook_diagnostics`.

Report missing kernels, missing kernel interpreters, intended-kernel matches and
mismatches, language-version mismatches, invalid notebooks, and empty targets.

### M8: Error explainer

Accept a traceback file or stdin and classify the final exception with bounded
explanations. Emit schema 1.5 with scope `error_explanation`.

Optional interpreter context adds module-metadata and frame-prefix evidence.
No traceback code is executed.

### M9: Safe repair system

Build dry-run plans from package, notebook, and error findings. Emit schema 1.6
with scope `repair_plan`.

Each step includes an exact argv, risk, confirmation requirement, verification,
and evidence. The CLI never executes a step. A separate guarded executor
requires the exact step id and an allowlisted `python -m pip install` argv.

### M10: Environment management

Aggregate M2, M3, M4, and optional M7 evidence into a unified report. Emit
schema 1.7 with scope `environment_report`.

The summary exposes comparison outcome, distribution and problem counts,
notebook and kernel counts, and the highest severity.

### M11: Product quality

Expose engine metadata through `--info` and a version through `--version`.
Publish collection limits, error envelopes, accessibility notes, and performance
constraints in `QUALITY.md`. There is no telemetry or automatic update.

## User interaction boundary

The interaction is a local JSON CLI and a desktop interface. The user selects
the trusted Python running PYD and, for target-specific modes, supplies the
intended interpreter path separately.

Project context is optional and explicit. No cwd-based target inference or
recursive repository scan is performed.

## Future problem areas

The Tauri shell, automatic repair execution, localization, auto-update, and
product analytics remain future work.

## Acceptance

Source delivery alone is not acceptance. Automated tests, Windows-specific
checks, documented limitations, and founder review are required as described in
`TESTING.md` and `ROADMAP.md`.
