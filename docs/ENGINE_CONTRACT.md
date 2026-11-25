# Engine Report and CLI Contract

## Shared CLI behavior

Run from `engine/python/src`, or use an already installed package with a known
trusted Python 3.12+ interpreter.

```powershell
python -m pydoctor --pretty
python -m pydoctor --discover --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --pretty
python -m pydoctor --inspect-packages "C:\Path\To\python.exe" --pretty
python -m pydoctor --inspect-notebooks "C:\Path\To\Project" --pretty
python -m pydoctor --explain-error "C:\Path\To\traceback.txt" --pretty
python -m pydoctor --repair-plan "C:\Path\To\report.json" --pretty
python -m pydoctor --environment-report "C:\Path\To\python.exe" --pretty
python -m pydoctor --info --pretty
```

Successful collection writes exactly one JSON document and a terminating newline
to stdout, with empty stderr. `--pretty` changes indentation only. Strings use
ASCII JSON escapes for Windows console portability.

All diagnostic modes are mutually exclusive. `--project` applies to discovery,
comparison, and environment reports. `--interpreter` supplies intended
interpreter context for notebook and error diagnosis.

| Mode | schema_version | scope |
| --- | --- | --- |
| Default M1 | 1.0 | current_interpreter |
| M2 discovery | 1.1 | python_discovery |
| M3 comparison | 1.2 | intended_interpreter_comparison |
| M4 packages | 1.3 | package_diagnostics |
| M7 notebooks | 1.4 | notebook_diagnostics |
| M8 errors | 1.5 | error_explanation |
| M9 repair plan | 1.6 | repair_plan |
| M10 environment | 1.7 | environment_report |
| M11 metadata | meta | engine_info |

No mode automatically selects or executes an intended interpreter.

## M1: Current interpreter

From `engine/python/src`:

```powershell
python -m pydoctor
python -m pydoctor --pretty
```

The selected Python running PYD is the observed interpreter. M1 does not
implicitly perform discovery or target comparison.

### Report

Top-level fields:

- schema_version: 1.0.
- scope: current_interpreter.
- runtime: observed current-process facts.
- findings: evidence-backed observations, not an overall health verdict.

Runtime fields:

- executable: observed sys.executable.
- version: full sys.version, not a parsed compatibility result.
- implementation: observed implementation name.
- prefix and base_prefix: observed sys.prefix and sys.base_prefix.
- sys_path: strings preserving ordering and empty entries.
- virtual_env: VIRTUAL_ENV string or null; an empty string is preserved.

Each finding contains:

- code: stable machine-readable identifier.
- confidence: CONFIRMED, LIKELY, or UNKNOWN, not severity.
- summary: an English explanation bounded by evidence.
- evidence: supporting strings.
- missing_information, hypotheses, next_steps: arrays of strings.
- commands: arrays of argument arrays, possibly empty.

Commands are suggestions only, never automatically executed shell strings.
Callers must not blindly join and execute them.

### Findings

| Code | Confidence | Bounded meaning |
| --- | --- | --- |
| runtime.observed | CONFIRMED | Runtime facts belong to the engine process. |
| environment.prefix_base | CONFIRMED | Prefix equals base prefix; this does not rule out Conda. |
| environment.prefix_isolated | CONFIRMED | Prefix differs from base prefix; not a health result. |
| environment.activation_hint_matches | CONFIRMED | Absolute hint and prefix identify the same filesystem object. |
| environment.activation_hint_mismatch | LIKELY | Hint and prefix identify different objects; intent is unknown. |
| environment.activation_hint_unverified | UNKNOWN | Relative, missing, invalid, or inaccessible evidence prevents comparison. |

No hint produces no activation finding. Inherited activation metadata is not
authoritative. Directory identity uses os.path.samefile where accessible,
avoiding false textual mismatches from aliases, casing, or junctions.

UNKNOWN findings retain evidence, missing information, hypotheses, and
investigation guidance. No M1 finding performs a repair.

### M1 errors and safety

Exit 0 means collection completed, not environment health.

Handled OSError or ValueError returns exit 1, empty stdout, and one stderr JSON
document with schema_version 1.0 and error code collection_failed.

Invalid CLI syntax returns exit 2 and argparse usage text.

M1 reads process state and optional directory metadata. It does not launch
subprocesses, import target packages, scan PATH, install anything, or alter
activation. Only VIRTUAL_ENV is collected as M1 environment evidence.

## M2: Explicit Windows discovery

```powershell
python -m pydoctor --discover --pretty
python -m pydoctor --discover --project "C:\Path\To\Project" --pretty
```

M2 uses schema 1.1 and scope python_discovery, with candidates and issues arrays.

### Candidate fields

Each candidate contains nullable executable, prefix, version, implementation,
architecture, exists, and is_file. Sources, evidence, confidence, and issues are
always present.

Evidence records contain source, location, and metadata key/value pairs.
observed_* metadata preserves original source executable paths and values,
including conflicts. No version is inferred from folder names.

Issues contain code, source, message, and nullable location. Consumers must
tolerate additional issue codes.

Metadata is source-reported except for the observed current runtime.
A missing executable remains a candidate, not an invented path.

### Sources and bounds

- PEP 514: HKCU Software\Python and both HKLM registry views. Enumerate company
  and tag keys, skip PyLauncher, and retain hive/view/company/tag provenance.
  Prefer InstallPath\ExecutablePath. Only PythonCore can fall back to
  `<InstallPath>\python.exe`, never over a malformed explicit value.
  Limit 256 subkeys per key and 1024 registrations total. Report denied access,
  malformed values, and limits; absent roots are normal.
- Launcher: resolve legacy py.exe only at conventional locations under
  LOCALAPPDATA, SystemRoot, ProgramFiles, or ProgramFiles(x86), in that order.
  Do not search cwd, PATH, or WindowsApps for a launcher to execute.
  The sole subprocess is `[resolved_launcher, "-0p"]`, shell=False, with a
  three-second timeout. Parse at most 1024 lines. Preserve unexpected output,
  bounded stderr, nonzero status, missing launcher, and timeout issues.
  Installed-location trust is not signature validation.
- PATH: semicolon-delimited direct directories only. Skip empty, relative,
  and duplicate entries. Inspect at most 128 directories and 4096 entries per
  directory. Match supported console Python names, not py.exe or pythonw.exe.
  No recursion or candidate execution. Literal percent-variable strings are
  not expanded; unresolved non-absolute entries produce path_entry_invalid.
- Active hints: VIRTUAL_ENV implies Scripts\python.exe; CONDA_PREFIX implies
  python.exe. Missing or invalid hints remain evidence, not activation proof.
- Current interpreter: collect runtime path, version, implementation, prefix,
  base_prefix, and pointer width without a new process.
- Project: inspect only the selected root for pyvenv.cfg or Scripts/python.exe
  and direct .venv, venv, and env children. Named incomplete environments remain
  hints. No ancestors, arbitrary descendants, config contents, or packages are read.

### Deduplication and confidence

Use normalized Windows absolute paths and available regular-file device/inode
identities. Follow links and junctions where metadata supports identity.

Directories and WindowsApps aliases do not supply identity merge keys.
Null executables are not merged by prefix. Missing/inaccessible paths retain
lexical evidence. All source evidence survives.

Conflicting metadata becomes null with metadata_conflict. Inconsistent
filesystem observations remain explicit. Output ordering is deterministic for
the same observations; there are no timestamps or random identifiers.

CONFIRMED means only that a regular file was observed. It does not establish
Python identity, runnability, compatibility, safety, or health. The
interpreter_not_verified issue makes that restriction explicit.

WindowsApps aliases are not CONFIRMED. LIKELY means an absolute executable hint
exists without a confirmed ordinary file. UNKNOWN covers missing/invalid
executable evidence. File confidence does not validate source metadata.

### Platform and errors

Non-Windows discovery returns current-runtime evidence and unsupported_platform;
it does not emulate Windows.

Invalid/inaccessible project input returns exit 2, empty stdout, and stderr JSON
with schema 1.1 and error code invalid_project_directory.

Other handled collection errors return exit 1 / collection_failed.
Partial discovery exits 0 and retains issues. This is not completeness or health.

## M3: Intended Interpreter Comparison

```powershell
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --project "C:\Path\To\Project" --pretty
```

Schema 1.2; scope intended_interpreter_comparison.

### Target policy

The target must be an explicit absolute path.

No cwd resolution, environment-variable expansion, tilde expansion, automatic
selection, or surrounding-quote stripping is performed by the engine.
Shell quotes are handled by the shell before argument parsing.

Windows target paths normalize case, separators, dot components, and supported
extended prefixes. Drive-relative and current-drive-root-relative paths are
invalid. Device namespaces, alternate streams, reserved device components,
control characters, wildcard characters, and trailing-dot/space components are
rejected conservatively.

Native absolute host paths support non-Windows fixtures. Non-Windows M2 source
discovery remains unsupported; lexical Windows path tests do not validate actual
Windows filesystem behavior.

Syntactically invalid targets produce an uncertainty report without discovery.
For valid syntax, M3 observes target metadata and calls the existing M2 engine,
including optional project context.

### Top-level fields

- schema_version: 1.2.
- scope: intended_interpreter_comparison.
- target: immutable target observation.
- outcome: overall comparison outcome.
- comparisons: one relationship record per discovered candidate.
- discovery_issues: M2 source-wide issues, preserved.
- findings: existing finding convention with evidence and next steps.

The full M2 candidate inventory is not duplicated. Relationship records retain
the candidate executable, provenance, and issues needed to explain comparison.

### Target fields

- supplied_path: exact supplied argument.
- normalized_path: normalized path or null for invalid syntax.
- status: INVALID, MISSING, DIRECTORY, REGULAR_FILE, OTHER, or INACCESSIBLE.
- exists and is_file: observed booleans or null when unknown.
- is_windowsapps_alias: conservative location classification.
- file_identity: device/inode pair or null.
- issues: structured validation and observation issues.
- interpreter_verification: always NOT_VERIFIED.

REGULAR_FILE does not establish that a file is Python or executable.
Stat follows links; a broken link may be reported as missing.

### Candidate relationship fields

- candidate_executable: M2 canonical executable or null.
- compared_paths: canonical and retained observed_executable paths.
- method: relationship method below.
- confidence: confidence in this relationship only.
- sources and evidence: retained M2 provenance.
- issues: candidate and comparison uncertainty.

A candidate with a null executable has no executable match keys. Prefixes,
directory names, basenames, versions, and arbitrary evidence locations never
establish an executable match.

### Match methods

| Method | Meaning |
| --- | --- |
| EXACT_NORMALIZED_PATH | Target equals an established candidate path after normalization. |
| SAME_FILE_IDENTITY | Accessible non-alias regular files have the same nonzero device/inode identity. |
| POSSIBLE | Lexical correspondence involves WindowsApps alias evidence. |
| NO_MATCH | Available comparisons found no normalized or file-identity relationship. |
| INSUFFICIENT_EVIDENCE | Missing paths or unavailable evidence prevent a conclusive relationship. |

Exact matching is a lexical relationship. It can remain visible for a missing
target, but is not a confirmed regular-file relationship in that case.

Identity uses os.stat device/inode values, equivalent to the basis of same-file
comparison. Zero inode, permission errors, unsupported metadata, and other
access failures do not establish equality. A distinct missing candidate path
provides no present file to identify with the target.

No WindowsApps identity is used to confirm an interpreter relationship.

### Overall outcomes

| Outcome | Precise meaning |
| --- | --- |
| MATCHED | At least one exact or identity relationship is confirmed for a regular, non-alias target. |
| PARTIALLY_MATCHED | A lexical relationship exists but lacks confirmation of a regular non-alias target relationship, including alias correspondence. |
| NO_MATCH | Target is a regular non-alias file, at least one candidate was compared, and every candidate relationship is NO_MATCH. |
| INSUFFICIENT_EVIDENCE | Target is invalid/non-file, discovery is empty, or unresolved evidence prevents the preceding outcomes. |

An invalid, directory, or other non-regular target always produces
INSUFFICIENT_EVIDENCE overall, even if a lexical path record exists.

A successful path relationship can coexist with metadata conflicts, missing
sources, or unrelated incomplete candidates. These remain visible as issues and
missing information. MATCHED does not resolve runtime versions or metadata.

NO_MATCH is bounded by discovery and time. It is not proof that the intended
interpreter is absent from the system.

### M3 errors

- Completed evidence report: exit 0, including invalid target syntax, missing
  target, partial match, no match, and insufficient evidence.
- Invalid project for a syntactically valid target: exit 2, empty stdout,
  schema 1.2 stderr JSON with invalid_project_directory.
- Handled collection failure: exit 1, empty stdout, schema 1.2 stderr JSON
  with collection_failed.
- Argument syntax or incompatible modes: exit 2 with argparse usage text.

For an invalid target syntax, discovery and project inspection are not attempted.

## Shared safety, limitations, and privacy

M2/M3 do not execute intended/discovered interpreters, import their packages,
run pip, activate environments, change environment variables, modify PATH or
Registry, install/remove packages, repair, persist reports, recursively scan,
or make network requests.

Launcher listing is the only collection subprocess. Its output is captured in
memory before parsing; the line limit is not a hard byte-memory cap.
Installed-location trust assumes a trusted caller environment.

Filesystem calls can block on network locations; source count limits are not
filesystem timeouts. Observations can race with filesystem changes. Identity
does not prove file contents, safety, compatibility, or future identity.

Python's normal startup hooks and bytecode caching are outside the collector's
control. Use a trusted engine interpreter.

Reports can reveal usernames, paths, sys.path, source metadata, and bounded
launcher diagnostics. There is no telemetry or automatic sharing.

Startup failure, unavailable modules, broken output streams, and unexpected
programming errors are not guaranteed to use the JSON error envelope.

Desktop process supervision, packaging, notebook diagnosis, repair, and a
broader request protocol remain future work.

## M4: Package inventory and dependency diagnostics

```powershell
python -m pydoctor --inspect-packages "C:\Path\To\python.exe" --pretty
```

Schema 1.3; scope `package_diagnostics`.

### Target and prefix policy

The target must be an explicit interpreter path. The engine observes it with the
same target validation as M3 and never executes it.

The environment prefix is derived from the conventional layout
`<prefix>\Scripts\python.exe` or `<prefix>\bin\python`. Site-packages candidates
are `<prefix>\Lib\site-packages` and `<prefix>\lib\python3.X\site-packages`.
`pyvenv.cfg` is read for `version`/`version_info` only; its `home` value is not
followed. No interpreter is run to obtain `sys.prefix` or `sys.version`.

### Inventory

`.dist-info` and `.egg-info` entries are enumerated with a 4096-entry limit per
root and at most 16 candidate roots. `METADATA`/`PKG-INFO` is parsed with the
standard library email parser, capped at 2 MiB. `INSTALLER` and
`direct_url.json` are read when present.

Distribution names are normalized per PEP 503. A missing Name or Version is an
explicit issue, not an inferred value. Metadata presence does not prove that a
package imports, that native extensions load, or that the distribution is
healthy.

### Top-level fields

- schema_version: 1.3.
- scope: package_diagnostics.
- target: M3 target observation for the supplied interpreter path.
- interpreter_prefix, python_version, python_version_source.
- site_packages: observed candidate roots with existence and distribution counts.
- distributions: parsed metadata records with nested issues.
- dependencies: requirement and Requires-Python results with nested issues.
- findings: M4 findings with severity.
- issues: inventory-level collection issues; distribution and dependency issues
  remain attached to their records.

### Dependency evaluation

`Requires-Dist` strings are parsed with a bounded PEP 508 subset. Version
specifiers use a bounded PEP 440 subset. Results are:

| Status | Meaning |
| --- | --- |
| SATISFIED | An observed distribution name and version satisfy the clause. |
| MISSING | No observed distribution has the normalized name; inventory may be incomplete. |
| VERSION_CONFLICT | Observed versions were parsed and none satisfy the clause. |
| SKIPPED | A supported environment marker evaluates to false. |
| OPTIONAL_UNKNOWN | The marker depends on an unselected extra. |
| UNKNOWN | Parsing, marker evaluation, direct references, or version comparison was inconclusive. |

`Requires-Python` is checked only when the target version is known from
`pyvenv.cfg` or a `python3.X` layout. Otherwise it is UNKNOWN with
`python_version_unknown`.

Environment markers are evaluated only with variables the engine can establish
without executing the target: `python_version`, `python_full_version`,
`sys_platform`, `os_name`, and `platform_system`. Unknown variables such as
`extra`, `platform_machine`, or `implementation_name` produce UNKNOWN, never a
guessed result.

### Findings and safety

Findings cover inventory observation, missing site-packages, duplicate
distributions, missing dependencies, version conflicts, Requires-Python
incompatibility, incomplete metadata, inconclusive analysis, and an unverified
target version. Each M4 finding carries a `severity` of `INFO`, `WARNING`, or
`ERROR` in addition to the shared CONFIRMED/LIKELY/UNKNOWN confidence. Severity
expresses impact; confidence expresses evidence strength. They are independent.

M4 does not execute the target interpreter, import packages, run pip, resolve
direct URLs, download anything, install or remove packages, modify environments,
or scan recursively. Only metadata files under the derived site-packages roots
are read.

## M7: Notebook and kernel diagnostics

```powershell
python -m pydoctor --inspect-notebooks "C:\Path\To\Project" --pretty
python -m pydoctor --inspect-notebooks "C:\Path\To\Project" --interpreter "C:\Path\To\python.exe" --pretty
```

Schema 1.4; scope `notebook_diagnostics`.

The target is a `.ipynb` file or a project directory. A directory contributes
only its direct `.ipynb` children; no recursive scan is performed.

Kernelspecs are read from `%APPDATA%\jupyter\kernels`,
`%PROGRAMDATA%\jupyter\kernels`, `<sys.prefix>\share\jupyter\kernels`, and,
when `--interpreter` is supplied, `<intended prefix>\share\jupyter\kernels`.
Each `kernel.json` is parsed for `argv`, `display_name`, and `language`. The
first argv element is treated as an interpreter only when it is an absolute
path to a Python-like executable.

Notebook metadata is read for `kernelspec.name`, `kernelspec.display_name`,
`language_info.name`, `language_info.version`, and `nbformat`. No cell is
executed and no kernel is launched.

Findings cover observed kernels, missing kernels, missing kernel interpreters,
kernel/intended-interpreter matches and mismatches, notebook language-version
mismatches, invalid notebooks, and empty targets. `--interpreter` also enables
a version comparison from local `pyvenv.cfg`/layout evidence.

## M8: Traceback explanation

```powershell
python -m pydoctor --explain-error "C:\Path\To\traceback.txt" --pretty
python -m pydoctor --explain-error - --interpreter "C:\Path\To\python.exe" --pretty
```

Schema 1.5; scope `error_explanation`. `-` reads stdin.

The final exception line and all `File "...", line N` frames are parsed. The
explanation is bounded by the supplied text. Recognized classes include
`ModuleNotFoundError`, `ImportError`, syntax/indentation errors, permission and
file-not-found errors, attribute and type mismatches, memory errors, and a
generic classified fallback.

With `--interpreter`, M4 inventory evidence can add
`error.module_metadata_present` when distribution metadata for the missing
module exists, and `error.frames_outside_intended_environment` when frame paths
fall outside the intended prefix. Neither finding proves which interpreter ran.

No traceback code is executed.

## M9: Safe repair planning

```powershell
python -m pydoctor --repair-plan "C:\Path\To\report.json" --pretty
```

Schema 1.6; scope `repair_plan`. The CLI only builds a dry-run plan.

Steps are derived from observed `MISSING` and `VERSION_CONFLICT` dependency
records, Requires-Python incompatibility, duplicate distributions, notebook
kernel problems, and missing-module errors. Each step has an id, title,
rationale, risk, `requires_confirmation`, optional exact `argv`, verification
description, and evidence. `dry_run` is always true in a plan.

The CLI never executes a step. The engine exposes
`execute_repair_step(step, approved_step_id=...)`, which requires the exact step
id, an absolute Python path, and an allowlisted `python -m pip install` argv.
Execution uses `shell=False`, a timeout, captured output, and metadata-only
verification. No repair execution is performed by tests or by the desktop UI.

## M10: Unified environment report

```powershell
python -m pydoctor --environment-report "C:\Path\To\python.exe" --pretty
python -m pydoctor --environment-report "C:\Path\To\python.exe" --project "C:\Path\To\Project" --pretty
```

Schema 1.7; scope `environment_report`.

The report aggregates existing evidence without new collection rules: M3 target
observation and comparison, M2 discovery, M4 packages, and optional M7
notebooks. `summary` contains the comparison outcome, distribution count,
missing-dependency and version-conflict counts, notebook and kernel counts, and
the highest finding severity. Nested reports retain their own schemas.

## M11: Engine metadata and quality

```powershell
python -m pydoctor --info --pretty
python -m pydoctor --version
```

`--info` emits schema `meta`, scope `engine_info`, with the engine version,
engine Python version, mode/schema map, and collection limits. `--version`
prints `pydoctor-engine <version>` and exits 0.

Handled errors use a JSON envelope on stderr with the active schema and an error
code. Invalid report input for `--repair-plan` exits 2 with
`invalid_report_file`. Other handled collection failures exit 1 with
`collection_failed`. Invalid project input exits 2 with
`invalid_project_directory`.

# بخش سوم — تست و پذیرش

## الف. ترتیب اعمال و اجرای خودکار

ایجنت باید ابتدا همهٔ فایل‌ها را اعمال کند و سپس تست‌ها را اجرا کند؛ اجرای تست در میانهٔ اعمال فایل‌ها ملاک نتیجه نیست.

از ریشهٔ پروژه:

```powershell
Set-Location "C:\Users\ACER\Source\Repo\PYD"

python --version
.\scripts\run-tests.ps1
```

انتظار:

- Python `3.12+`.
- خروج موفق runner موجود.
- تمام تست‌های قدیمی M1/M2 حفظ شده باشند.
- هیچ failure یا error.
- skipهای وابسته به hardlink یا junction دقیق گزارش شوند.
- تعداد واقعی تست‌ها از خروجی ثبت شود؛ **عدد ۸۲ دیگر تعداد مورد انتظار کل مجموعه نیست**.

سپس فرمان صریح مورد درخواست:

```powershell
$oldPythonPath = $env:PYTHONPATH
try {
    $env:PYTHONPATH = (Join-Path (Get-Location) "engine\python\src")
    python -m unittest discover -s engine/python/tests -p "test_*.py" -v
    if ($LASTEXITCODE -ne 0) { throw "unittest failed: $LASTEXITCODE" }
}
finally {
    if ($null -eq $oldPythonPath) {
        Remove-Item Env:PYTHONPATH -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $oldPythonPath
    }
}
```

این تغییر موقت `PYTHONPATH` صرفاً تنظیم محیط **runner تست** است، نه رفتاری از موتور M2/M3. مقدار قبلی بازیابی می‌شود.

**Ruff و pytest نصب نشوند.** در صورت نبودن، unavailable ثبت شوند. این بسته نتیجهٔ اجرای آن‌ها را ادعا نمی‌کند.

## ب. پذیرش CLI روی Windows واقعی

از مسیر:

```powershell
Set-Location "C:\Users\ACER\Source\Repo\PYD\engine\python\src"
```

### M1

```powershell
python -m pydoctor --pretty
```

انتظار:

- exit `0`.
- stderr خالی.
- یک JSON روی stdout.
- `schema_version == "1.0"`.
- `scope == "current_interpreter"`.
- ساختار `runtime` و `findings` قبلی.
- نبود `target` و نبود اجرای discovery.

### M2

```powershell
python -m pydoctor --discover --pretty
```

انتظار:

- exit `0`.
- schema `1.1`.
- scope `python_discovery`.
- `candidates` و `issues`.
- provenance مربوط به current interpreter.
- نبود ادعای سلامت برای فایل‌های کشف‌شده.
- وجود `interpreter_not_verified` برای فایل عادی مشاهده‌شده.
- issueهای کشف ناقص لزوماً شکست فرمان نیستند.

### M3 با Python شناخته‌شده

```powershell
$knownPython = python -c "import sys; print(sys.executable)"
python -m pydoctor --compare-interpreter "$knownPython" --pretty
