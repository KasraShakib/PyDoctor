# Roadmap

## Foundation

- Repository and Python engine foundation exist.
- Desktop scaffolding and toolchain readiness are separate work.
- No desktop implementation is claimed.

## M1: Current interpreter inspection

Status: accepted and committed.

Baseline: `9ceeacf414c6799b5d093aa7320a2d5f06a7af66`.

- Immutable runtime and finding models.
- Current-process executable, version, prefixes, and sys.path.
- Conservative activation-hint comparison.
- Schema 1.0 and default JSON CLI.
- Original 21 unittest tests retained.

## M2: Python environment discovery

Status: implemented; Windows audit passed for the pre-finalization implementation.
Finalization acceptance remains pending execution of the delivered changes.

The founder's November 10, 2026 audit reports 82 passing tests, a successful
PowerShell runner, M1/M2 CLI checks, and a project discovery fixture.

Finalization gate:

- Documentation aligned with actual behavior.
- Inert `python.exe` test passes.
- File-only CONFIRMED semantics and unverified interpreter issue are visible.
- WindowsApps and directory identity safeguards pass.
- Existing M1 and M2 tests remain green.
- Real junction acceptance passes, or its precise blocked limitation is recorded.
- PATH, launcher trust, and output-buffer limitations are acknowledged.
- Founder reviews the actual results before authorizing a baseline commit.

Do not mark this gate accepted merely because source has been supplied.

## M3: Intended Interpreter Comparison

Status: implementation delivered; application, execution, and acceptance pending.

Acceptance gate:

- Strict absolute target validation.
- Exact normalized and safe file-identity relationships.
- Explicit possible, no-match, and insufficient-evidence cases.
- Alias, missing-file, permission, incomplete-candidate, and conflict coverage.
- Immutable schema 1.2 report and dedicated CLI.
- M2 reuse, project integration, deterministic serialization.
- No target execution or environment modification.
- Full test suite and Windows CLI acceptance pass.
- Founder reviews actual results.

Only after these gates pass may M2/M3 be recorded as accepted. No commit or
push is authorized by the delivery.

## Next milestone

Design a separate, explicitly approved package-inventory milestone. It must
define trust and collection boundaries before implementation and must not
silently execute unknown targets.

Dependency diagnostics, notebook diagnosis, repair, desktop UI, integration,
and distribution packaging remain deferred. Their exact order requires review.
