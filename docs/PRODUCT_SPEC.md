# PyDoctor Product Specification

## Purpose

Help Windows users understand Python interpreter and environment choices through
explainable evidence, without silently selecting or modifying an environment.

## Product principles

- Evidence before assumptions.
- CONFIRMED, LIKELY, and UNKNOWN describe a bounded observation, not severity.
- Preserve source provenance, conflicts, and missing information.
- Never claim that a file is valid Python or healthy without relevant verification.
- Do not execute unknown interpreters for inspection.
- Keep collection read-only, bounded, and standard-library-only.
- Keep the engine independently testable before adding a desktop interface.

## Current engine capabilities

### M1: Current interpreter

Observe the trusted process running PYD: executable, version, implementation,
prefixes, sys.path, and the VIRTUAL_ENV hint. Emit schema 1.0 with scope
`current_interpreter`.

This does not inspect another interpreter or diagnose packages.

### M2: Windows discovery

Collect current-runtime evidence, PEP 514 registrations, the installed legacy
launcher's listing, direct PATH entries, active-environment hints, and optional
project-local environment roots.

Emit schema 1.1 with scope `python_discovery`.

Registrations, aliases, incomplete directories, and regular files remain
evidence rather than a guaranteed inventory of runnable Python installations.

### M3: Intended interpreter comparison

Accept an explicit absolute interpreter path, observe its file metadata, reuse
M2, and explain its relationship to candidate executable paths and file identities.

Emit schema 1.2 with scope `intended_interpreter_comparison`.

Outcomes are MATCHED, PARTIALLY_MATCHED, NO_MATCH, and INSUFFICIENT_EVIDENCE.
None is an interpreter-health result or an automatic selection decision.

## User interaction boundary

The current interaction is a local JSON CLI. The user selects the trusted Python
running PYD and, for M3, supplies the intended target path separately.

Project context is optional and explicit. No cwd-based target inference or
recursive repository scan is performed.

## Future problem areas

Package inventory, dependency/import diagnosis, notebook errors, controlled
repair recommendations, and a polished Windows desktop application are future
milestones. They are not implemented by M1–M3.

## Acceptance

Source delivery alone is not acceptance. Automated tests, Windows-specific
checks, documented limitations, and founder review are required as described in
`TESTING.md` and `ROADMAP.md`.
