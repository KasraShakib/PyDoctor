# Roadmap

## M1: Current interpreter inspection

Status: accepted and committed.

Baseline: `9ceeacf414c6799b5d093aa7320a2d5f06a7af66`.

- Immutable runtime and finding models.
- Current-process executable, version, prefixes, and sys.path.
- Conservative activation-hint comparison.
- Schema 1.0 and default JSON CLI.

## M2: Python environment discovery

Status: implemented and committed in `33c84e7`.

- PEP 514 registry, launcher listing, PATH, active hints, and project roots.
- Bounded, read-only collection with explicit uncertainty.
- Schema 1.1.

## M3: Intended interpreter comparison

Status: implemented and committed in `33c84e7`.

- Strict absolute target validation.
- Exact normalized path and file-identity relationships.
- Explicit possible, no-match, and insufficient-evidence outcomes.
- Schema 1.2.

## M4: Package inventory and dependency diagnostics

Status: implemented and locally verified.

- Explicit interpreter target observed without execution.
- Conventional prefix and site-packages derivation.
- Bounded `.dist-info`/`.egg-info` metadata reading.
- PEP 503 name normalization and duplicate detection.
- Bounded PEP 508 requirement and PEP 440 specifier evaluation.
- Missing, conflicting, marker-gated, and Requires-Python results.
- Schema 1.3 with severity, confidence, evidence, and findings.

## M5: Desktop interface

Status: React interface delivered in WebView2; Tauri shell not built.

- React 18 interface in `apps/desktop-ui`.
- Native WebView2 shell in `apps/desktop_native` via `pywebview`.
- Interpreter and project selection.
- Full report, package, notebook, error, repair-plan, discovery, and compare
  actions.
- Summary, details, and raw JSON tabs.
- Loading, empty, and error states.
- `scripts/run-desktop-ui.cmd` launcher.
- Stdlib Tkinter interface retained as a fallback.

The Tauri shell remains the long-term target. It requires Rust/Cargo, the MSVC
build tools, the Tauri CLI, and network access, none of which are available
here. Tailwind could not be installed either; `styles.css` is a hand-authored
equivalent.

## M6: Windows packaging

Status: implemented with PyInstaller.

- `dist/PyDoctor.exe`: one-file Tkinter build.
- `dist/PyDoctor-UI.exe`: one-file React + WebView2 build.
- `scripts/build-ui.cmd` assembles the static bundle.
- `scripts/build-exe.cmd` builds both executables.
- `PYDOCTOR_SELF_CHECK_OUT` verifies the packaged React UI renders and exposes
  the bridge.
- A Tauri bundle still requires a prepared Rust/MSVC toolchain.

## M7: Notebook diagnostics

Status: implemented.

- Conventional Jupyter kernelspec discovery.
- Notebook metadata parsing without cell execution.
- Kernel missing, interpreter missing, intended-kernel match/mismatch,
  language-version mismatch, invalid notebook, and empty-target findings.
- Schema 1.4.

## M8: Error explainer

Status: implemented.

- Traceback file or stdin input.
- Final exception and frame extraction.
- Common exception classification with bounded explanations.
- Optional interpreter context for module metadata and frame-prefix evidence.
- Schema 1.5.

## M9: Safe repair system

Status: planning implemented; execution guarded and not exposed by the CLI.

- Dry-run plans derived from package, notebook, and error findings.
- Exact argv, risk, confirmation flag, verification, and evidence per step.
- Guarded executor requiring exact step id and an allowlisted
  `python -m pip install` argv.
- Metadata-only post-execution verification.
- Schema 1.6.

## M10: Advanced environment management

Status: implemented as an aggregate report.

- Combines M2, M3, M4, and optional M7 evidence.
- Compact summary counts and highest severity.
- Nested reports retain their own schemas.
- Schema 1.7.

## M11: Product quality

Status: implemented for engine metadata and quality documentation.

- `--info` schema `meta` with version, modes, and limits.
- `--version`.
- Consistent JSON error envelopes and exit codes.
- Bounded collection limits documented in `QUALITY.md`.
- Accessibility and keyboard notes for the interim UI.
- No telemetry or network transfer.

## Deferred

- React/Tauri desktop implementation and bundle.
- Standalone Windows executable.
- Automatic repair execution from the UI.
- Localization, auto-update, and analytics.
