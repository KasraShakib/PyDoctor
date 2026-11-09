# PyDoctor Product Specification

## Working Name

PYD (PyDoctor)

## Product Purpose

PyDoctor is intended to help Windows users diagnose Python environment problems without requiring deep expertise in Python packaging or runtime configuration. It should explain what is wrong and suggest actionable next steps.

## Initial Problem Areas

- Dependency conflicts and inconsistent package versions
- Import errors and missing modules
- Python interpreter and virtual environment confusion
- Common Python and Jupyter configuration problems

## Target Users

- Python developers who need faster environment troubleshooting
- Data scientists and Jupyter users
- Technical support and developer-tooling teams
- Less experienced users who need clear explanations

## Product Principles

- Diagnose first; do not modify environments without explicit user action.
- Present findings in plain language and preserve technical detail for advanced users.
- Keep diagnostics repeatable and testable outside the desktop UI.
- Avoid unnecessary dependencies and privileged system changes.

## Initial Scope

The original setup phase covered project structure, configuration, documentation, and environment readiness. M1 now adds read-only current-interpreter diagnostics: runtime identity, prefix observations, and conservative evaluation of the VIRTUAL_ENV shell hint. Package checks, repair execution, target-interpreter discovery, and the desktop interface are not implemented.

## Explicit Non-Goals for the Setup Phase

- Installing Python or JavaScript packages
- Generating a Tauri application without the required toolchain
- Implementing diagnostic rules
- Creating installers or publishing releases
- Adding cloud services, telemetry, or credentials

## Success Criteria for the Initial Setup

- The repository is initialized inside `C:\Users\ACER\Source\Repo\PYD`.
- The desktop and Python engine boundaries are documented.
- The Python engine package has basic configuration and a smoke test.
- The development environment and missing prerequisites are recorded.
- Existing files are preserved and no files outside PYD are modified.
