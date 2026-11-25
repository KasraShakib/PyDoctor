# Quality, Limits, and Privacy

This document records the quality constraints that apply across the PyDoctor
engine and the interim desktop interface. It complements `ENGINE_CONTRACT.md`
(report semantics) and `TESTING.md` (verification procedure).

## Evidence quality

Every finding carries a confidence value and a severity value. They are
independent:

- Confidence (`CONFIRMED`, `LIKELY`, `UNKNOWN`) describes how strongly the
  collected evidence supports the specific claim.
- Severity (`INFO`, `WARNING`, `ERROR`) describes the practical impact if the
  claim is true.

Rules that must not regress:

- A finding must never claim more than its evidence supports. Observing a file
  named `python.exe` is not proof that it runs.
- Matching a path or file identity is not proof of interpreter health.
- Satisfied package metadata is not proof that a package imports.
- A discovered kernelspec is not proof that a kernel launches.
- When evidence is insufficient, the engine emits `UNKNOWN` with a
  `missing_information` entry instead of guessing.

## Bounded collection

All collection is bounded so that a hostile, corrupt, or unusually large input
cannot exhaust memory or stall the CLI. The limits are published by
`python -m pydoctor --info` and mirrored here:

| Limit | Value | Applies to |
| --- | --- | --- |
| `path_directories` | 128 | PATH entries inspected |
| `directory_entries` | 4096 | Entries read per directory |
| `distributions` | 4096 | Installed distributions inspected |
| `metadata_bytes` | 2 MiB | A single metadata file |
| `kernels` | 256 | Kernelspecs inspected |
| `notebooks` | 256 | Notebook files inspected |
| `traceback_bytes` | 1 MiB | Supplied traceback text |
| `report_bytes` | 32 MiB | Input report read by `--repair-plan` |

Exceeding a limit produces a bounded, explicit finding rather than a crash or a
silent truncation that could be mistaken for complete evidence.

## Error handling

Handled failures never emit a partial success report. They write a single JSON
error envelope to stderr and exit non-zero:

```json
{"schema_version": "1.3", "error": {"code": "collection_failed", "message": "..."}}
```

- `collection_failed` (exit 1): the input could not be read or parsed.
- `invalid_project_directory` (exit 2): `--project` was not a usable directory.
- `invalid_report_file` (exit 2): `--repair-plan` input was missing, oversized,
  non-JSON, or not a JSON object.
- Argument errors (exit 2): raised by the argument parser for invalid flag
  combinations.

Reports are written to stdout only on success. Diagnostics never write to
stdout, so a caller can parse stdout unconditionally.

## Safety invariants

- The engine never executes an intended or discovered interpreter, imports its
  packages, runs pip, activates an environment, or launches a kernel.
- The engine never modifies PATH, the Registry, environments, or project files.
- `--repair-plan` is dry-run only. The guarded executor is a library API, is not
  exposed by the CLI, and requires the exact step id, an absolute Python path,
  and an allowlisted `python -m pip install` argv with `shell=False`.
- The sole subprocess is the legacy Python Launcher `-0p` listing.

## Desktop quality

Both desktop front ends render engine reports without re-implementing diagnostic
logic.

### React interface (WebView2)

- The interface calls only the bridge API; every number comes from the engine.
- Loading, empty, and error states are explicit. A failed run shows the error
  text instead of a blank pane.
- Severity and confidence are always printed as text badges, not color alone.
- Long paths and evidence are truncated with a tooltip in the summary and shown
  in full in the raw JSON tab.
- The packaged executable supports `PYDOCTOR_SELF_CHECK_OUT`, which renders the
  page, reads the DOM, and writes a JSON verdict. This makes packaging failures
  detectable without human inspection.
- The React bundle is local; no CDN or network request is used at runtime.

### Tkinter fallback

- Long-running reports execute on a background thread; results are delivered
  through a thread-safe queue polled with `root.after`, so the UI thread never
  blocks and Tk is never touched from a worker thread.
- Keyboard access: `F5` runs a full report, `Ctrl+O` opens the interpreter
  picker. Tabs are reachable with the standard notebook key bindings.
- Text panes use a fixed-width font for JSON and wrap long lines so paths and
  evidence remain readable at the default 1040x720 window size.
- No color-only signaling: severity and confidence are always printed as text.

## Privacy

- No telemetry, analytics, crash upload, or network request is made by the
  engine or the desktop interface.
- Reports contain absolute local paths and installed package names. They are
  written only to stdout or to a file the user chooses; review them before
  sharing.
- No account, payment, or cloud service is required or contacted.

## Known limitations

- The Tauri shell is not built (missing Rust/Cargo and MSVC). The React
  interface itself is delivered in WebView2, and both standalone executables are
  built.
- Tailwind CSS is not installed; `apps/desktop-ui/styles.css` is a hand-authored
  equivalent.
- Repair execution is intentionally not exposed in the UI.
- Localization, auto-update, and accessibility auditing beyond the notes above
  are deferred to post-MVP work.
