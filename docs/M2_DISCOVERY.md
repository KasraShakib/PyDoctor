# M2 Discovery: Finalization and Acceptance

## Implemented behavior

M2 discovers evidence from the current interpreter, PEP 514 Registry, the
installed legacy launcher's `-0p` listing, direct PATH entries, VIRTUAL_ENV,
CONDA_PREFIX, and explicitly selected project environment roots.

It emits schema 1.1 with scope python_discovery. M1 remains schema 1.0.
M3 reuses this discovery engine rather than adding another collector.

No discovered interpreter or user package is executed.

## Confidence

CONFIRMED means a regular file was observed, not that the file is Python,
runnable, safe, compatible, or healthy.

The interpreter_not_verified issue is emitted for observed regular files.
An inert text fixture named python.exe demonstrates the distinction.

LIKELY retains an absolute executable hint without a confirmed ordinary file.
UNKNOWN covers missing or invalid executable evidence. WindowsApps aliases
are not CONFIRMED. Candidate metadata can remain unverified or conflicting.

## Normalization and identity

Windows paths use case-insensitive separator/dot/extended-prefix normalization.
Native host paths exist only to support portability and fixtures.

Regular-file device/inode identities can merge hardlinks and paths through
junctions. Zero inode, denied access, missing paths, and unsupported identity
remain uncertainty. Directories and WindowsApps aliases do not supply identity
merge keys.

Original observed executable paths survive in provenance, so M3 can compare
paths that are not the merged candidate's canonical path.

## Intentional limits

- PATH: 128 distinct directories, 4096 directory entries each, no recursion.
- Directory-entry limits can omit candidates; the issue records incompleteness.
- Literal `%VAR%` strings inside PATH are not expanded. An unresolved entry
  without an absolute path is skipped as path_entry_invalid.
- Empty PATH entries never imply cwd.
- WindowsApps is a conservative location-based alias classification.
- Named empty project environments remain hints; they do not prove a venv exists.
- The legacy launcher is resolved only from documented installed locations.
- Launcher trust is based on the trusted invoking environment and location,
  not Authenticode verification.
- The three-second launcher timeout bounds process waiting, not output bytes.
- Output is captured before the 1024-line parser limit; no hard capture-memory
  bound is claimed.
- Filesystem metadata calls may block on remote or unavailable paths.
- Non-Windows discovery reports the current interpreter and unsupported_platform,
  not emulated Windows discovery.

These limits are not hidden health or completeness guarantees.

## Acceptance history

The previous implementation-host run recorded 82 passing tests on Linux,
Python 3.11.16. This was not Windows/Python 3.12+ acceptance.

The founder's November 10, 2026 audit reports successful Windows suite,
PowerShell runner, M1/M2 CLI, and project fixture checks for the previous M2
implementation. Real junction acceptance remained unverified.

Neither historical result validates the finalization changes delivered with M3.

## Finalization acceptance gate

1. All original M1/M2 tests pass after applying the finalization.
2. Inert python.exe confidence test passes without execution.
3. Alias and directory identity isolation tests pass.
4. Documentation matches current commands, schemas, evidence, and limitations.
5. Windows M1/M2 and project CLI checks pass.
6. The optional real junction test passes, or its exact blocked limitation is
   explicitly accepted by the founder.
7. No dependency installation, repair, arbitrary interpreter execution, commit,
   or push occurs.
8. Actual results are reviewed before marking M2 accepted.

See TESTING.md for commands. M2 must not be marked accepted merely because
source was delivered or mocks passed.
