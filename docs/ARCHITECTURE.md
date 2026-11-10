# Architecture

## Status

PYD is an engine-first project. M1 observes the engine runtime, M2 discovers
Windows candidates, and M3 compares an explicitly intended interpreter path
against discovery evidence.

The desktop architecture is provisional. React/TypeScript and Tauri remain
future implementation choices, not an existing process integration.

## Component boundaries

### Python engine

Location: `engine/python`; package: `pydoctor`.

- `models.py`: immutable M1 runtime, finding, confidence, and report models.
- `environment.py`: current-process observation and activation-hint evaluation.
- `discovery_models.py`: immutable M2 hints, provenance, issues, and candidates.
- `discovery_registry.py`: bounded read-only PEP 514 collection.
- `discovery_sources.py`: launcher, PATH, active hints, and opt-in project sources.
- `discovery_normalization.py`: shared path rules and deterministic M2 merging.
- `discovery.py`: independent source orchestration.
- `comparison_models.py`: immutable schema 1.2 models.
- `interpreter_target.py`: explicit target syntax validation and metadata observation.
- `comparison.py`: candidate relationship analysis and M2 reuse.
- `__main__.py`: argument validation, orchestration, and JSON streams.

Target validation does not discover sources. Comparison does not implement a
second discovery engine. CLI code contains no matching rules.

### Desktop application

Reserved location: `apps/desktop`.

A future desktop layer may present reports and invoke the engine through a
supervised boundary. No UI scaffold, Rust bridge, request transport, bundling,
process supervision, or executable distribution is supplied by M1–M3.

## Integration boundary

Three explicit local CLI modes return independent versioned reports:

- M1: schema 1.0, `current_interpreter`.
- M2: schema 1.1, `python_discovery`.
- M3: schema 1.2, `intended_interpreter_comparison`.

The default command remains M1. Discovery and comparison are opt-in.
The authoritative report semantics are in `ENGINE_CONTRACT.md`.

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

## Dependency policy

Runtime dependencies remain standard-library-only. pytest and Ruff are optional
development tools, not prerequisites for unittest or the CLI. No dependency
installation is authorized by this milestone.

## Safety and privacy

No intended or discovered interpreter is executed. No package is imported for
investigation, and no repair or environment mutation is performed.

M2's installed-location launcher listing is the sole collection subprocess.
Installed-location trust is not signature verification. Filesystem metadata
access may block on remote locations; count limits are not filesystem deadlines.

Python startup hooks and bytecode caching of the trusted engine process remain
normal Python behavior. Reports may expose usernames, filesystem paths, source
metadata, and bounded launcher diagnostics. There is no telemetry or network
transfer.
