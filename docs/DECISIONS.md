# Technical Decisions

## 2026-11-09: Keep desktop and engine separate

The desktop interface and Python diagnostic engine remain separately testable.
Diagnostic logic belongs in the engine. React/TypeScript and Tauri are planned
desktop technologies, not an implemented integration.

## 2026-11-09: No runtime dependencies

The engine uses the standard library. pytest and Ruff are optional development
tools only. M2 and M3 add no dependencies.

## M1: Current-interpreter evidence and JSON

Use immutable evidence and finding models, schema 1.0, and a read-only default
CLI. Observe the trusted engine process rather than executing arbitrary targets.

The CLI is an initial local boundary, not a completed desktop bridge.

## M1: Activation metadata is a hint

Compare a nonempty absolute VIRTUAL_ENV hint with the observed prefix using
filesystem identity. A mismatch is LIKELY, unavailable evidence is UNKNOWN,
and absence is not an error.

Prefix and runtime facts do not prove environment health. No repair follows.

## M1: Tests without installation

Use standard-library unittest, compatible with optional pytest discovery.
The PowerShell runner restores caller state. Optional development tools are not
required for offline tests.

## M2: Bounded discovery without candidate execution

Use independent sources, immutable provenance, normalized paths, and available
regular-file identity. Preserve missing registrations, incomplete named project
environments, alias caveats, and metadata conflicts.

Only the legacy launcher's installed-location `-0p` listing may execute.
Installed-location trust is not signature verification. No arbitrary PATH
launcher, discovered interpreter, package, or activation script may execute.

M2 uses schema 1.1 and does not alter M1.

## M2 finalization: Preserve bounded CONFIRMED semantics

Do not redefine the public confidence enum or change schema 1.1.

CONFIRMED on an M2 candidate means direct regular-file observation only.
Every observed regular-file hint receives interpreter_not_verified, explaining
that Python identity, runnability, safety, compatibility, and health were not
verified. An inert python.exe test enforces this distinction.

Directories and WindowsApps aliases do not provide identity merge keys.
WindowsApps remains conservatively classified by location.

## M2 finalization: Keep explicit collection limits

Retain PATH limits of 128 directories and 4096 entries per directory. Reaching
a limit reports uncertainty; it is not a complete inventory guarantee.

Do not expand literal percent-delimited variables inside PATH entries.
Unresolved relative-style entries are skipped with an issue. This avoids
introducing recursive expansion or ambient-environment differences in fixtures.

Retain the existing launcher timeout and parsing bounds. Captured output is
buffered before parsing, so the parsing limit is not a hard memory cap.
A separately reviewed process-reader change would be needed for a strict
byte-level capture cap; no such redesign is hidden in M3.

## M3: Compare explicit intent, not interpreter health

Add schema 1.2 with scope intended_interpreter_comparison. Require an explicit
absolute target path and reject relative, device-namespace, alternate-stream,
and ambiguous Windows component forms.

Reuse M2. Separate target observation, candidate comparison, immutable report
models, and CLI orchestration.

Exact normalized paths and nonzero device/inode identities establish bounded
relationships. Missing executable paths, prefixes, basenames, and versions never
establish exact executable matches. Retained observed_executable provenance
prevents identity deduplication from losing an original path relationship.

WindowsApps lexical correspondence is POSSIBLE, never a confirmed interpreter
match. Metadata conflicts survive a successful path match.

## M3: Distinguish outcomes and command success

MATCHED describes a confirmed path/file relationship to a regular non-alias
target. PARTIALLY_MATCHED describes a lexical relationship lacking that support.
NO_MATCH is limited to compared evidence. INSUFFICIENT_EVIDENCE preserves
invalid targets and undecidable relationships.

A report containing uncertainty exits 0. CLI syntax errors exit 2. Invalid
project input retains structured exit 2. Handled collection errors exit 1.

interpreter_verification remains NOT_VERIFIED in every M3 report.

## Acceptance and authorization

Historical tests and the founder's audit do not validate subsequently delivered
code. Run the full suite and Windows acceptance, record skips and limitations,
and obtain founder review. No commit or push is authorized by code delivery.

## M4: Read distribution metadata, never execute or import

Package diagnostics observe an explicit interpreter path with the M3 target
policy, derive a conventional prefix, and read only recognized metadata files
under conventional site-packages roots. The target interpreter is not executed,
packages are not imported, pip is not run, direct URLs are not resolved, and
environments are not modified.

Schema 1.3 adds scope package_diagnostics without changing M1-M3.

## M4: Derive prefix from layout, not from execution

`<prefix>\Scripts\python.exe` and `<prefix>\bin\python` imply the environment
prefix. `pyvenv.cfg` supplies `version`/`version_info` only; `home` is not
followed. Without reliable local version evidence, Requires-Python checks are
UNKNOWN. The engine does not infer a version from a folder name.

## M4: Bounded PEP 440/508 subset with explicit UNKNOWN

The engine remains standard-library-only. Version and requirement parsing covers
the common PEP 440/PEP 508 forms used by installed metadata. Environment markers
are evaluated only with variables that can be established without executing the
target. Unsupported syntax, unknown marker variables, extras, and direct
references produce UNKNOWN rather than a guessed SATISFIED or MISSING result.

SATISFIED means observed metadata satisfies a clause; it is not an import or
health verdict. MISSING and VERSION_CONFLICT are bounded by the observed
inventory.

M4 findings add an INFO/WARNING/ERROR severity through a PackageFinding subtype.
Severity and confidence are independent, and M1-M3 finding schemas are unchanged.

## M4: Bounded inventory collection

At most 16 site-packages roots and 4096 directory entries per root are inspected.
Metadata reads are capped at 2 MiB. Missing or unreadable metadata is an explicit
issue. Distribution names are normalized per PEP 503; duplicate names remain
visible rather than being silently collapsed.

## M5: Interim Tkinter desktop, React/Tauri target retained

The desktop layer is a stdlib Tkinter application because Node.js, Rust/Cargo,
the Tauri CLI, and network access are unavailable. It invokes engine functions
in-process and renders their JSON reports. Presentation logic lives in
`ui_model.py` so it is testable without Tk.

React + TypeScript + Tailwind + Tauri remains the target architecture. The
interim UI does not change engine boundaries or add diagnostic rules.

## M6: Source launcher instead of an unverified package

`scripts/run-desktop.cmd` runs the app from source. No standalone `.exe` is
claimed because PyInstaller is unavailable and cannot be fetched. Packaging must
be built and tested on a prepared toolchain before it is called complete.

## M7: Read notebook metadata, never launch kernels

Kernelspecs are read from conventional Jupyter locations and the intended
environment prefix. `kernel.json` and notebook JSON are parsed with bounded
reads. No kernel is launched and no cell is executed. Kernel presence is
evidence, not launch or health proof.

## M8: Explain supplied tracebacks without executing them

The explainer parses the final exception and frames from supplied text. Rules
classify common exceptions and keep unknown cases explicit. Optional interpreter
context adds metadata and frame-prefix evidence, never a claim about which
interpreter actually ran.

## M9: Planning is separate from execution

The CLI only produces dry-run plans. Execution is a separate API that requires
the exact step id, an absolute Python path, and an allowlisted
`python -m pip install` argv. Execution uses `shell=False`, a timeout, captured
output, and metadata-only verification. The UI does not execute repairs.

## M10: Aggregate existing evidence

The environment report reuses M2, M3, M4, and M7 rather than adding collectors.
Nested reports keep their own schemas, and the summary exposes counts and the
highest severity for the desktop layer.

## M11: Engine metadata and explicit limits

`--info` provides a meta schema for the desktop layer. `--version` is the only
plain-text mode. Collection limits are published in the info report and
`QUALITY.md`. There is no telemetry, auto-update, or network transfer.

## M5 delivery: WebView2 instead of Tauri

Tauri requires Rust, Cargo, and the MSVC build tools. None are installed, the
Rust download servers are unreachable, and no Visual Studio Build Tools are
present. WebView2 is already available on Windows 11, so the React interface is
hosted by `pywebview` in a native WebView2 window. The Tauri shell remains the
documented target and can replace the shell without changing the React bundle or
the engine.

## M5 delivery: no bundler, React from a PyPI wheel

The npm registry and its reachable mirror could not serve package tarballs
reliably, so Vite and Tailwind could not be installed. The official React
18.3.1 UMD builds are taken from the `dash` wheel on PyPI, and the interface is
written with `React.createElement` so no build step is required. `styles.css`
is a hand-authored utility layer equivalent to the intended Tailwind design.

## M6 delivery: PyInstaller one-file executables

PyInstaller is installed from PyPI and builds two one-file executables:
`PyDoctor.exe` (Tkinter) and `PyDoctor-UI.exe` (React + WebView2). The React
build embeds the static bundle as `ui/` and supports
`PYDOCTOR_SELF_CHECK_OUT`, which renders the page, reads the DOM, and writes a
JSON verdict so packaged builds can be verified without human inspection.

## Branding: a stethoscope around a Python snake

The icon is drawn programmatically in `scripts/make-icon.py` so the geometry is
deterministic and reproducible at every size. A white stethoscope U surrounds a
blue Python snake with a yellow head, and the chest piece carries a small
medical cross. The generated `.ico` is embedded in both executables, the
Tkinter window sets it explicitly, and the React header loads the SVG variant.

## Branding: two accent variants

The same geometry ships in two accent colors so the two executables are
distinguishable in the taskbar and Explorer: `icon-ui.ico` uses a cyan ring for
`PyDoctor-UI.exe` and the React header, and `icon-tk.ico` uses an amber ring for
`PyDoctor.exe`. `scripts/make-icon.py` emits both from one drawing routine,
which keeps the mark consistent while still giving each binary a distinct
identity.

## M5 redesign: command center instead of a dashboard

The first React interface used a dashboard layout (sidebar, stat cards, panel
grid). It read as generic and buried the one action that matters: run a
diagnostic. The interface was rebuilt around a command-center model:

- An aurora gradient background with soft animated blobs replaces flat panels.
- A centered hero (eyebrow, gradient headline, subtitle) collapses to a compact
  header once a report exists, so results get the full screen.
- A single glass command bar holds the interpreter input (with a discovered-
  interpreter dropdown), the project input, and the run button.
- Mode selection is a horizontal chip row rather than a sidebar.
- Results lead with a verdict banner (ok / warning / error) and a schema pill,
  then inline metrics, then expandable finding rows with severity-colored left
  borders, a numbered repair timeline, and a List / Raw JSON segmented control.
- Loading uses skeleton shimmer; `Ctrl+Enter` runs the active mode.

No diagnostic behavior changed. The redesign is presentation-only and keeps the
same bridge API, engine contract, and read-only guarantees.

## M5: theme and language are client-side preferences

The light/dark theme and the English/Persian language are stored in
`localStorage` and applied by setting `data-theme`, `lang`, and `dir` on
`<html>`. An inline bootstrap script in `index.html` applies them before React
mounts so there is no flash of the wrong theme. Nothing is sent to the engine,
and the engine's JSON stays language-neutral: only presentation strings are
translated, so reports remain comparable across languages.

Persian uses the same layout with logical CSS properties (`margin-inline-start`,
`border-inline-start`, `inset-inline-end`), so RTL mirroring needs no duplicate
stylesheets. Severity and confidence values (`ERROR`, `CONFIRMED`, ...) are
schema terms and stay in English in both languages.
