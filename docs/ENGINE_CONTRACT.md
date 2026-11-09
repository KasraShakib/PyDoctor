# Engine Report and CLI Contract (M1)

## Scope and Invocation

Schema version: `1.0`. Scope: `current_interpreter`.

From `engine/python/src`, run `python -m pydoctor` or `python -m pydoctor --pretty`. This works without installation. If already installed, the module can also be invoked outside the source directory. The `python` selected by the caller is the interpreter being observed. There is no target path argument, stdin request, auto-discovery, daemon, or Tauri bridge yet.

The CLI writes exactly one JSON document and a terminating newline to stdout on successful collection. Default output is a single line; `--pretty` changes indentation only. Strings use ASCII JSON escapes to preserve Unicode paths across Windows console encodings. JSON consumers recover the original Unicode strings normally.

## Success Report

Top-level fields:

| Field | Type | Meaning |
| --- | --- | --- |
| schema_version | string | Currently `1.0`; consumers must check support. |
| scope | string | Currently `current_interpreter`, never an implicitly selected target. |
| runtime | object | Observed facts described below. |
| findings | array | Evidence-backed observations, not an overall health verdict. |

Runtime fields:

- `executable`: string, observed `sys.executable`.
- `version`: string, full observed `sys.version`, not a parsed compatibility result.
- `implementation`: string, Python implementation name.
- `prefix`, `base_prefix`: strings, observed `sys.prefix` and `sys.base_prefix`.
- `sys_path`: array of strings, preserving ordering and empty entries from `sys.path`.
- `virtual_env`: string or null, only the VIRTUAL_ENV environment variable. Empty strings are preserved but do not trigger a comparison.

Each finding contains:

- `code`: stable machine-readable identifier from the list below.
- `confidence`: `CONFIRMED`, `LIKELY`, or `UNKNOWN`; this is not severity.
- `summary`: English explanation bounded by the evidence.
- `evidence`: array of strings supporting this specific observation.
- `missing_information`, `hypotheses`, `next_steps`: arrays of strings, possibly empty.
- `commands`: array of argument arrays, possibly empty. These are investigation suggestions only, never shell strings or automatically executed actions. Shell quoting is the caller's responsibility; do not join arguments and execute through a shell.

## Finding Semantics

| Code | Confidence | Bounded meaning |
| --- | --- | --- |
| runtime.observed | CONFIRMED | These executable/version facts belong to the engine process. |
| environment.prefix_base | CONFIRMED | Prefix equals base prefix; this does not rule out Conda or other managers. |
| environment.prefix_isolated | CONFIRMED | Prefix differs from base prefix, the standard venv signal; not a health check. |
| environment.activation_hint_matches | CONFIRMED | Absolute hint and prefix identify the same filesystem object. |
| environment.activation_hint_mismatch | LIKELY | Hint and prefix identify different objects; intended interpreter is not known. |
| environment.activation_hint_unverified | UNKNOWN | Relative, inaccessible, missing, or invalid paths prevent reliable comparison. |

No hint produces no activation finding. Inherited activation metadata is not authoritative. Matching directories do not prove packages are correct. Directory identities are compared using `os.path.samefile`, avoiding false textual mismatches from aliases, casing, or junctions when supported and accessible. Filesystem access failures produce UNKNOWN rather than an invented mismatch. Prefix facts use the runtime's documented prefix relationship; this is not general environment-manager discovery.

UNKNOWN findings include collected evidence, what could not be established, labelled hypotheses, investigation steps, and an interpreter/prefix inspection command. No finding in M1 proposes or performs a repair.

## Exit Codes and Errors

- `0`: collection completed, including reports containing LIKELY or UNKNOWN findings. Not a clean bill of health.
- `1`: handled collection failure (`OSError` or `ValueError`). Stdout is empty; stderr contains one JSON document: `{"schema_version":"1.0","error":{"code":"collection_failed","message":"..."}}`.
- `2`: invalid CLI arguments; argparse writes ordinary usage text to stderr. This is not a JSON collection failure.

Interpreter startup failures, unavailable modules, broken output streams, and unexpected programming errors are not guaranteed to use the JSON error envelope. Future process integration must handle nonzero exits, startup failures, timeouts, and invalid output independently.

## Safety and Privacy

The collector reads process state and optional directory metadata. It does not launch subprocesses, import user packages for investigation, install anything, scan PATH, alter activation, or write repairs. Python itself still follows its normal startup and bytecode-cache behavior; this command is not a sandbox for untrusted interpreters or startup hooks.

Only VIRTUAL_ENV is collected from the environment; the full process environment is not exported. Reports can expose usernames, directories, and project paths through executable, prefixes, and sys.path. No telemetry, automatic persistence, network transfer, or automatic report sharing is implemented.

The CLI/report contract is an initial local boundary. Desktop process supervision, secure target selection, Python bundling, packaging, repairs, and a broader request protocol remain separate milestones.
