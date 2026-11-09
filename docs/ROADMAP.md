# Roadmap

## Phase 0: Initial Setup

Status: repository foundation complete; desktop toolchain readiness still blocked

- [x] Create the PYD project structure
- [x] Document product scope and architecture boundaries
- [x] Configure the Python engine package
- [x] Record the development environment audit
- [x] Initialize local Git without publishing
- [ ] Prepare the desktop scaffold when Node.js and Rust are available

## Phase 1: Diagnostic Engine Foundation

M1 implementation: current-interpreter evidence and offline JSON CLI. Windows acceptance must be established by the local test report, not inferred from source delivery.

- [x] Define a structured diagnostic result model with confidence levels
- [x] Observe the current interpreter, prefixes, sys.path, and activation hint
- [x] Add isolated standard-library tests and a real CLI invocation test
- [x] Document the initial JSON report and local CLI contract
- [ ] Compare an explicitly intended interpreter with observed evidence
- [ ] Discover other interpreters safely; define target-process trust and timeouts first
- [ ] Add package inventory and evidence-based dependency/import diagnostics
- [ ] Establish the actual desktop-to-engine process integration

M1 does not infer that an environment is healthy, install packages, or perform repairs.

## Phase 2: Desktop Shell

- Generate and configure the official Tauri React + TypeScript app
- Build the initial diagnostic workflow
- Connect the UI to the Python engine safely
- Add error states and clear remediation guidance

## Phase 3: Windows Packaging and Hardening

- Validate Windows build prerequisites
- Add installer and release configuration when appropriate
- Add accessibility, logging, and update policies
- Run end-to-end verification on supported Windows versions

Roadmap items are directional. Next recommended slice: explicit intended-interpreter comparison, without automatic launches or repairs. The desktop scaffold remains dependent on approved toolchain setup.
