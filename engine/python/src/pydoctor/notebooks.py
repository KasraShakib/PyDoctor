"""Read-only Jupyter kernel and notebook metadata diagnostics."""

import json
import os
import stat
import sys
from collections.abc import Mapping

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.discovery_normalization import normalized_path
from pydoctor.interpreter_target import observe_target
from pydoctor.models import Confidence, SeverityFinding
from pydoctor.notebook_models import KernelSpec, NotebookObservation, NotebookReport
from pydoctor.package_inventory import build_inventory, interpreter_prefix

MAX_KERNELS = 256
MAX_NOTEBOOKS = 256
MAX_KERNEL_BYTES = 256 * 1024
MAX_NOTEBOOK_BYTES = 8 * 1024 * 1024


def _read_json(path: str, limit: int) -> tuple[object | None, list[DiscoveryIssue]]:
    issues: list[DiscoveryIssue] = []
    try:
        with open(path, "rb") as handle:
            data = handle.read(limit + 1)
    except (OSError, ValueError) as exc:
        issues.append(
            DiscoveryIssue(
                "json_unreadable",
                "notebooks",
                f"File could not be read ({type(exc).__name__}).",
                path,
            )
        )
        return None, issues
    if len(data) > limit:
        issues.append(
            DiscoveryIssue(
                "json_truncated",
                "notebooks",
                "File exceeded the read limit and was truncated.",
                path,
            )
        )
        data = data[:limit]
    try:
        return json.loads(data.decode("utf-8", errors="replace").lstrip("\ufeff")), issues
    except ValueError:
        issues.append(
            DiscoveryIssue("json_invalid", "notebooks", "File is not valid JSON.", path)
        )
        return None, issues


def kernelspec_directories(
    environ: Mapping[str, str] | None = None,
    extra_prefixes: tuple[str, ...] = (),
) -> tuple[str, ...]:
    """Return bounded conventional Jupyter kernelspec roots."""
    environment = dict(os.environ if environ is None else environ)
    roots: list[str] = []
    for variable in ("APPDATA", "PROGRAMDATA"):
        base = environment.get(variable)
        if base:
            roots.append(os.path.join(base, "jupyter", "kernels"))
    roots.append(os.path.join(sys.prefix, "share", "jupyter", "kernels"))
    for prefix in extra_prefixes:
        roots.append(os.path.join(prefix, "share", "jupyter", "kernels"))
    unique: list[str] = []
    seen: set[str] = set()
    for root in roots:
        key = normalized_path(root)
        if key not in seen:
            seen.add(key)
            unique.append(root)
    return tuple(unique)


def _interpreter_from_argv(argv: tuple[str, ...]) -> str | None:
    if not argv:
        return None
    candidate = argv[0]
    if not os.path.isabs(candidate):
        return None
    if not candidate.casefold().endswith((".exe", "python", "python3")):
        return None
    return candidate


def _read_kernelspec(directory: str) -> KernelSpec | None:
    path = os.path.join(directory, "kernel.json")
    if not os.path.isfile(path):
        return None
    payload, issues = _read_json(path, MAX_KERNEL_BYTES)
    if not isinstance(payload, dict):
        return KernelSpec(
            name=os.path.basename(directory),
            display_name=None,
            language=None,
            argv=(),
            resource_dir=directory,
            interpreter=None,
            interpreter_exists=None,
            issues=tuple(issues),
        )
    argv_value = payload.get("argv")
    argv = tuple(item for item in argv_value if isinstance(item, str)) if isinstance(argv_value, list) else ()
    if not argv:
        issues.append(
            DiscoveryIssue(
                "kernelspec_argv_missing",
                "notebooks",
                "kernel.json has no usable argv list.",
                path,
            )
        )
    interpreter = _interpreter_from_argv(argv)
    exists = None
    if interpreter is not None:
        try:
            exists = stat.S_ISREG(os.stat(interpreter).st_mode)
        except (OSError, ValueError):
            exists = False
        if not exists:
            issues.append(
                DiscoveryIssue(
                    "kernel_interpreter_missing",
                    "notebooks",
                    "Kernelspec interpreter path is missing or not a regular file.",
                    interpreter,
                )
            )
    return KernelSpec(
        name=os.path.basename(directory),
        display_name=payload.get("display_name") if isinstance(payload.get("display_name"), str) else None,
        language=payload.get("language") if isinstance(payload.get("language"), str) else None,
        argv=argv,
        resource_dir=directory,
        interpreter=interpreter,
        interpreter_exists=exists,
        issues=tuple(issues),
    )


def discover_kernels(
    environ: Mapping[str, str] | None = None,
    extra_prefixes: tuple[str, ...] = (),
) -> tuple[tuple[KernelSpec, ...], tuple[DiscoveryIssue, ...]]:
    """Read conventional kernelspec directories with bounded enumeration."""
    kernels: list[KernelSpec] = []
    issues: list[DiscoveryIssue] = []
    seen: set[str] = set()
    for root in kernelspec_directories(environ, extra_prefixes):
        try:
            with os.scandir(root) as entries:
                for index, entry in enumerate(
                    sorted(entries, key=lambda item: item.name.casefold())
                ):
                    if index >= MAX_KERNELS:
                        issues.append(
                            DiscoveryIssue(
                                "kernel_limit",
                                "notebooks",
                                "Kernelspec enumeration limit reached.",
                                root,
                            )
                        )
                        break
                    if not entry.is_dir():
                        continue
                    spec = _read_kernelspec(entry.path)
                    if spec is None:
                        continue
                    key = normalized_path(spec.resource_dir)
                    if key in seen:
                        continue
                    seen.add(key)
                    kernels.append(spec)
                    issues.extend(spec.issues)
        except (OSError, ValueError):
            continue
    kernels.sort(key=lambda item: (item.name.casefold(), item.resource_dir))
    return tuple(kernels), tuple(issues)


def parse_notebook(path: str) -> NotebookObservation:
    """Read notebook metadata only; no cell is executed."""
    payload, issues = _read_json(path, MAX_NOTEBOOK_BYTES)
    if not isinstance(payload, dict):
        return NotebookObservation(path=path, valid=False, issues=tuple(issues))
    metadata = payload.get("metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    kernelspec = metadata.get("kernelspec")
    kernelspec = kernelspec if isinstance(kernelspec, dict) else {}
    language_info = metadata.get("language_info")
    language_info = language_info if isinstance(language_info, dict) else {}
    return NotebookObservation(
        path=path,
        valid=True,
        kernel_name=kernelspec.get("name") if isinstance(kernelspec.get("name"), str) else None,
        kernel_display_name=(
            kernelspec.get("display_name")
            if isinstance(kernelspec.get("display_name"), str)
            else None
        ),
        language=(
            language_info.get("name") if isinstance(language_info.get("name"), str) else None
        ),
        language_version=(
            language_info.get("version")
            if isinstance(language_info.get("version"), str)
            else None
        ),
        nbformat=str(payload.get("nbformat")) if payload.get("nbformat") is not None else None,
        issues=tuple(issues),
    )


def collect_notebooks(target: str) -> tuple[str, tuple[NotebookObservation, ...], tuple[DiscoveryIssue, ...]]:
    """Inspect one notebook file or the direct children of a project directory."""
    issues: list[DiscoveryIssue] = []
    try:
        info = os.stat(target)
    except (OSError, ValueError) as exc:
        return "missing", (), (
            DiscoveryIssue("notebook_target_missing", "notebooks", type(exc).__name__, target),
        )
    if stat.S_ISREG(info.st_mode):
        if not target.casefold().endswith(".ipynb"):
            return "other", (), (
                DiscoveryIssue(
                    "notebook_target_not_notebook",
                    "notebooks",
                    "Target file is not a .ipynb notebook.",
                    target,
                ),
            )
        return "notebook", (parse_notebook(target),), ()
    if not stat.S_ISDIR(info.st_mode):
        return "other", (), (
            DiscoveryIssue("notebook_target_not_file", "notebooks", "Target is not a file or directory.", target),
        )
    notebooks: list[NotebookObservation] = []
    try:
        with os.scandir(target) as entries:
            for index, entry in enumerate(sorted(entries, key=lambda item: item.name.casefold())):
                if index >= MAX_NOTEBOOKS:
                    issues.append(
                        DiscoveryIssue(
                            "notebook_limit",
                            "notebooks",
                            "Notebook enumeration limit reached.",
                            target,
                        )
                    )
                    break
                if entry.is_file() and entry.name.casefold().endswith(".ipynb"):
                    notebooks.append(parse_notebook(entry.path))
    except (OSError, ValueError) as exc:
        issues.append(
            DiscoveryIssue("notebook_directory_inaccessible", "notebooks", type(exc).__name__, target)
        )
    return "project", tuple(notebooks), tuple(issues)


def _same_interpreter(left: str, right: str) -> bool:
    try:
        if normalized_path(left) == normalized_path(right):
            return True
        return os.path.samefile(left, right)
    except (OSError, ValueError):
        return False


def inspect_notebooks(
    target: str,
    intended_interpreter: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> NotebookReport:
    """Explain kernel and notebook metadata without launching kernels or cells."""
    extra_prefixes: tuple[str, ...] = ()
    intended_version: str | None = None
    if intended_interpreter:
        extra_prefixes = (interpreter_prefix(intended_interpreter),)
        intended_version = build_inventory(intended_interpreter).python_version
    kernels, kernel_issues = discover_kernels(environ, extra_prefixes)
    target_kind, notebooks, notebook_issues = collect_notebooks(target)
    issues = list(kernel_issues) + list(notebook_issues)
    by_name = {kernel.name: kernel for kernel in kernels}
    findings: list[SeverityFinding] = []

    if kernels:
        findings.append(
            SeverityFinding(
                code="notebooks.kernels_observed",
                severity="INFO",
                confidence=Confidence.CONFIRMED,
                summary="Jupyter kernelspecs were read from conventional locations.",
                evidence=tuple(
                    f"{kernel.name}: {kernel.resource_dir}" for kernel in kernels[:5]
                ),
                next_steps=(
                    "Kernelspec presence does not prove that a kernel launches.",
                ),
            )
        )
    else:
        findings.append(
            SeverityFinding(
                code="notebooks.no_kernels",
                severity="WARNING",
                confidence=Confidence.UNKNOWN,
                summary="No Jupyter kernelspecs were observed in conventional locations.",
                evidence=tuple(
                    f"Checked: {root}" for root in kernelspec_directories(environ, extra_prefixes)
                ),
                missing_information=("Jupyter may not be installed or may use another location.",),
                next_steps=("Confirm that Jupyter is installed in the environment you use.",),
            )
        )

    missing_kernels = [
        notebook
        for notebook in notebooks
        if notebook.valid and notebook.kernel_name and notebook.kernel_name not in by_name
    ]
    if missing_kernels:
        findings.append(
            SeverityFinding(
                code="notebooks.kernel_missing",
                severity="WARNING",
                confidence=Confidence.LIKELY,
                summary="Some notebooks reference a kernelspec that was not observed.",
                evidence=tuple(
                    f"{notebook.path}: kernel {notebook.kernel_name!r}"
                    for notebook in missing_kernels[:5]
                ),
                missing_information=("The kernel may exist in an unsearched location.",),
                next_steps=(
                    "Select an available kernel in the notebook interface.",
                    "Inspect the kernelspec name stored in notebook metadata.",
                ),
            )
        )

    missing_interpreters = [kernel for kernel in kernels if kernel.interpreter_exists is False]
    if missing_interpreters:
        findings.append(
            SeverityFinding(
                code="notebooks.kernel_interpreter_missing",
                severity="WARNING",
                confidence=Confidence.LIKELY,
                summary="Some kernelspecs point to a missing interpreter file.",
                evidence=tuple(
                    f"{kernel.name}: {kernel.interpreter}" for kernel in missing_interpreters[:5]
                ),
                next_steps=(
                    "Re-register the kernel from the intended environment.",
                    "Do not delete the kernelspec until its origin is understood.",
                ),
            )
        )

    if intended_interpreter:
        intended = observe_target(intended_interpreter)
        matched = [
            kernel
            for kernel in kernels
            if kernel.interpreter and _same_interpreter(kernel.interpreter, intended_interpreter)
        ]
        if matched:
            findings.append(
                SeverityFinding(
                    code="notebooks.kernel_matches_intended",
                    severity="INFO",
                    confidence=Confidence.CONFIRMED,
                    summary="At least one kernelspec points to the intended interpreter path.",
                    evidence=tuple(f"{kernel.name}: {kernel.interpreter}" for kernel in matched[:5]),
                    next_steps=("Path agreement does not prove kernel launch or package health.",),
                )
            )
        elif intended.status == "REGULAR_FILE" and kernels:
            findings.append(
                SeverityFinding(
                    code="notebooks.kernel_mismatch",
                    severity="WARNING",
                    confidence=Confidence.LIKELY,
                    summary="No observed kernelspec points to the intended interpreter path.",
                    evidence=(
                        f"Intended interpreter: {intended_interpreter}",
                        f"Observed kernels: {len(kernels)}",
                    ),
                    missing_information=(
                        "A kernel may use an interpreter path not present in the kernelspec argv.",
                    ),
                    next_steps=(
                        "Register a kernel from the intended environment if needed.",
                        "Select the intended kernel in the notebook interface.",
                    ),
                )
            )

    if intended_version:
        mismatched = [
            notebook
            for notebook in notebooks
            if notebook.language_version
            and notebook.language_version.split(".")[:2]
            != intended_version.split(".")[:2]
        ]
        if mismatched:
            findings.append(
                SeverityFinding(
                    code="notebooks.language_version_mismatch",
                    severity="WARNING",
                    confidence=Confidence.LIKELY,
                    summary="Notebook language metadata differs from the intended interpreter version.",
                    evidence=tuple(
                        f"{notebook.path}: {notebook.language_version} vs {intended_version}"
                        for notebook in mismatched[:5]
                    ),
                    missing_information=(
                        "Notebook metadata can be stale and does not prove the kernel version.",
                    ),
                    next_steps=("Re-run the notebook with the intended kernel to refresh metadata.",),
                )
            )

    invalid = [notebook for notebook in notebooks if not notebook.valid]
    if invalid:
        findings.append(
            SeverityFinding(
                code="notebooks.invalid_notebook",
                severity="WARNING",
                confidence=Confidence.LIKELY,
                summary="Some notebook files could not be parsed as JSON.",
                evidence=tuple(notebook.path for notebook in invalid[:5]),
                next_steps=("Inspect or restore the reported notebook files.",),
            )
        )

    if target_kind in {"notebook", "project"} and not notebooks:
        findings.append(
            SeverityFinding(
                code="notebooks.no_notebooks",
                severity="INFO",
                confidence=Confidence.UNKNOWN,
                summary="No notebooks were observed at the selected target.",
                evidence=(f"Target: {target}",),
                next_steps=("Select a notebook file or a project directory containing notebooks.",),
            )
        )

    return NotebookReport(
        target=target,
        target_kind=target_kind,
        kernels=kernels,
        notebooks=notebooks,
        findings=tuple(findings),
        issues=tuple(issues),
    )
