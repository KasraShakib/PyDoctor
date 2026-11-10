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
