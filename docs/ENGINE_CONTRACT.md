# Engine Report and CLI Contract

## Shared CLI behavior

Run from `engine/python/src`, or use an already installed package with a known
trusted Python 3.12+ interpreter.

```powershell
python -m pydoctor --pretty
python -m pydoctor --discover --pretty
python -m pydoctor --compare-interpreter "C:\Path\To\python.exe" --pretty
```

Successful collection writes exactly one JSON document and a terminating newline
to stdout, with empty stderr. `--pretty` changes indentation only. Strings use
ASCII JSON escapes for Windows console portability.

`--discover` and `--compare-interpreter` are mutually exclusive.
`--project` requires discovery or comparison mode.

| Mode | schema_version | scope |
| --- | --- | --- |
| Default M1 | 1.0 | current_interpreter |
| M2 discovery | 1.1 | python_discovery |
| M3 comparison | 1.2 | intended_interpreter_comparison |

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

Desktop process supervision, packaging, package inventory, notebook diagnosis,
repair, and a broader request protocol remain future work.
```

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
