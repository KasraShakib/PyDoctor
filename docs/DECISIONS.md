# Technical Decisions

This document records significant decisions and their rationale. Add new entries rather than silently rewriting history.

## 2026-11-09: Keep Desktop and Engine as Separate Components

Decision: The React/TypeScript desktop interface and Python diagnostic engine will be separate, independently testable components.

Rationale: Diagnostic logic is the core product capability. Separating it allows direct Python tests, clearer ownership, and a UI that can evolve without coupling to diagnostic implementation details.

## 2026-11-09: Use a Minimal Monorepo Layout

Decision: Use `apps/desktop` for the desktop application and `engine/python` for the engine.

Rationale: The layout makes component boundaries explicit without adding workspace tooling or unnecessary configuration.

## 2026-11-09: Do Not Generate the Tauri Scaffold Yet

Decision: Do not create a manually invented Tauri/React application skeleton while Node.js, npm, Rust, and Cargo are unavailable.

Rationale: The official Tauri template should supply compatible configuration and dependency versions. Manually selecting versions without the installed toolchain would violate the project's dependency policy. The official scaffold command is documented in `apps/desktop/README.md`.

## 2026-11-09: No Runtime Dependencies in the Initial Python Package

Decision: The initial Python engine package has no runtime dependencies. pytest and Ruff are optional development tools only.

Rationale: The setup phase should remain small and avoid locking the product into dependencies before diagnostic requirements exist.

## M1: Start with Current-Interpreter Evidence and JSON Output

Decision: Add immutable evidence and finding models, schema version `1.0`, and a read-only `python -m pydoctor` CLI. The engine observes only its own interpreter. JSON output is an initial independently testable boundary; the Rust/Tauri process integration is deferred.

Rationale: Python is available while the desktop toolchain is not. A useful engine slice can be validated offline without inventing desktop configuration or executing arbitrary target interpreters. JSON remains inspectable and has standard-library support.

## M1: Treat Activation Metadata as a Hint

Decision: Report executable and prefix observations as CONFIRMED facts, not proof of environment health. Compare a nonempty, absolute VIRTUAL_ENV hint with sys.prefix using filesystem identity. Different accessible paths produce only a LIKELY activation mismatch; unavailable or relative paths produce UNKNOWN with investigation guidance. An absent hint is not an error.

Rationale: Activation variables can be stale, absent, or intentionally bypassed. Aliases and Windows junctions must not create textual-path false positives. Equal prefixes do not rule out Conda or other managers. No repair follows automatically.

## M1: Make Foundation Tests Available without Installation

Decision: Use standard-library unittest tests, also discoverable by pytest. Update the existing PowerShell runner to use unittest and restore PYTHONPATH after execution. Retain optional pytest and Ruff configuration without adding dependencies.

Rationale: The installed Python can exercise the first milestone immediately and offline. Optional lint tools remain useful when explicitly approved and available.
