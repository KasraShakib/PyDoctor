# Architecture

## Status

The desktop architecture remains provisional. Milestone M1 implements a read-only Python runtime report and a versioned JSON CLI; the desktop shell and repair execution remain unimplemented.

## Component Boundaries

### Desktop Application

Location: `apps/desktop`

Planned stack:

- React for the user interface
- TypeScript for application code
- Tauri for the Windows desktop shell and native integration

Responsibilities:

- Present diagnostic findings and remediation guidance
- Manage user interaction and application state
- Invoke the Python engine through a defined boundary
- Avoid embedding diagnostic logic in UI components

### Python Diagnostic Engine

Location: `engine/python`

Package: `pydoctor`

Responsibilities:

- Inspect Python environments and dependencies
- Evaluate diagnostic rules
- Return structured findings and suggested actions
- Run and test independently from the desktop application

## Integration Boundary

The desktop application and Python engine remain separately testable. M1 defines a versioned JSON report and local CLI in `docs/ENGINE_CONTRACT.md`; this is a first executable boundary, not a completed Tauri integration. The eventual Rust bridge may consume this CLI, but target selection, process supervision, packaging, and request transport are not implemented or finalized.

### Current Engine Modules

- `models.py`: immutable runtime evidence, findings, confidence levels, and report serialization.
- `environment.py`: current-process observation and conservative prefix/activation evaluation.
- `__main__.py`: argument handling and JSON output only; no diagnostic rules in the CLI.

There are no package imports under investigation, subprocesses, network calls, repairs, or environment scans during collection. Directory identity checks can read filesystem metadata for the activation hint. A caller needing the environment of another interpreter must not substitute the engine interpreter's report for it. Normal Python startup behavior, including site hooks and bytecode caching, is outside this collector's control.

## Dependency Policy

- Keep runtime dependencies minimal.
- Do not add a dependency without a concrete need.
- Use versions supported by the installed toolchain.
- Keep frontend and engine dependency sets independent.

## Security and Safety

- Diagnostics should be read-only by default.
- Any environment-changing operation must require explicit user confirmation.
- Never store credentials or secrets in the repository.
- Avoid privileged system modifications unless a future design explicitly requires and documents them.
