"""Explain a supplied Python traceback using bounded, evidence-based rules."""

import os
import re

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.discovery_normalization import normalized_path
from pydoctor.error_models import ErrorReport, TracebackFrame
from pydoctor.models import Confidence, SeverityFinding
from pydoctor.package_inventory import build_inventory
from pydoctor.requirements import normalize_name

MAX_TRACEBACK_BYTES = 1024 * 1024

_FRAME_RE = re.compile(r'^\s*File "(?P<path>[^"]+)", line (?P<line>\d+)(?:, in (?P<func>.+))?\s*$')
_SYNTAX_RE = re.compile(r'^\s*File "(?P<path>[^"]+)", line (?P<line>\d+)\s*$')
_EXCEPTION_RE = re.compile(
    r"^(?P<type>[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception|Warning|Exit|Interrupt|KeyboardInterrupt|SystemExit)?)"
    r"(?::\s*(?P<message>.*))?$"
)


def read_traceback(path: str) -> tuple[str | None, list[DiscoveryIssue]]:
    """Read a traceback file or stdin with a bounded size."""
    issues: list[DiscoveryIssue] = []
    try:
        if path == "-":
            import sys

            data = sys.stdin.buffer.read(MAX_TRACEBACK_BYTES + 1)
        else:
            with open(path, "rb") as handle:
                data = handle.read(MAX_TRACEBACK_BYTES + 1)
    except (OSError, ValueError) as exc:
        issues.append(
            DiscoveryIssue(
                "traceback_unreadable",
                "error_explainer",
                f"Traceback could not be read ({type(exc).__name__}).",
                path,
            )
        )
        return None, issues
    if len(data) > MAX_TRACEBACK_BYTES:
        issues.append(
            DiscoveryIssue(
                "traceback_truncated",
                "error_explainer",
                "Traceback exceeded the read limit and was truncated.",
                path,
            )
        )
        data = data[:MAX_TRACEBACK_BYTES]
    return data.decode("utf-8", errors="replace").lstrip("\ufeff"), issues


def parse_traceback(text: str) -> tuple[
    str | None,
    str | None,
    tuple[TracebackFrame, ...],
    tuple[DiscoveryIssue, ...],
]:
    """Extract the final exception and all frames from a traceback string."""
    issues: list[DiscoveryIssue] = []
    frames: list[TracebackFrame] = []
    exception_type = None
    message = None
    for raw in text.splitlines():
        frame = _FRAME_RE.match(raw) or _SYNTAX_RE.match(raw)
        if frame:
            frames.append(
                TracebackFrame(
                    path=frame.group("path"),
                    line=int(frame.group("line")),
                    function=frame.groupdict().get("func"),
                )
            )
            continue
        stripped = raw.strip()
        if not stripped or stripped.startswith(("Traceback", "During handling", "The above")):
            continue
        match = _EXCEPTION_RE.match(stripped)
        if match and (
            match.group("type").endswith(
                ("Error", "Exception", "Warning", "Exit", "Interrupt", "KeyboardInterrupt")
            )
        ):
            exception_type = match.group("type")
            message = match.group("message")
    if exception_type is None and text.strip():
        issues.append(
            DiscoveryIssue(
                "exception_unrecognized",
                "error_explainer",
                "No recognizable exception line was found.",
            )
        )
    return exception_type, message, tuple(frames), tuple(issues)


def _finding(
    code: str,
    severity: str,
    confidence: Confidence,
    summary: str,
    evidence: tuple[str, ...],
    *,
    missing: tuple[str, ...] = (),
    hypotheses: tuple[str, ...] = (),
    next_steps: tuple[str, ...] = (),
) -> SeverityFinding:
    return SeverityFinding(
        code=code,
        severity=severity,
        confidence=confidence,
        summary=summary,
        evidence=evidence,
        missing_information=missing,
        hypotheses=hypotheses,
        next_steps=next_steps,
    )


def _module_name(message: str | None) -> str | None:
    if not message:
        return None
    match = re.search(r"No module named '([^']+)'", message)
    return match.group(1) if match else None


def _import_name(message: str | None) -> tuple[str | None, str | None]:
    if not message:
        return None, None
    match = re.search(r"cannot import name '([^']+)' from '([^']+)'", message)
    return (match.group(1), match.group(2)) if match else (None, None)


def _frames_outside_prefix(frames: tuple[TracebackFrame, ...], prefix: str) -> bool:
    paths = [frame.path for frame in frames if frame.path and os.path.isabs(frame.path)]
    if not paths:
        return False
    prefix_key = normalized_path(prefix).rstrip("\\/") + "\\"
    return not any(normalized_path(path).startswith(prefix_key) for path in paths)


def explain_error(
    text: str,
    source: str = "<memory>",
    intended_interpreter: str | None = None,
    extra_issues: tuple[DiscoveryIssue, ...] = (),
) -> ErrorReport:
    """Classify a traceback and relate it to an optional intended environment."""
    exception_type, message, frames, parsed_issues = parse_traceback(text)
    issues = tuple(extra_issues) + parsed_issues
    evidence = tuple(
        part
        for part in (
            f"Exception: {exception_type}" if exception_type else None,
            f"Message: {message}" if message else None,
            *(f"Frame: {frame.path}:{frame.line} in {frame.function}" for frame in frames[-5:]),
        )
        if part
    )
    findings: list[SeverityFinding] = []

    if exception_type is None:
        findings.append(
            _finding(
                "error.unclassified",
                "WARNING",
                Confidence.UNKNOWN,
                "The supplied text did not contain a recognizable Python exception.",
                evidence or (f"Source: {source}",),
                missing=("A complete traceback is required for a bounded explanation.",),
                next_steps=("Paste the full traceback, including the final exception line.",),
            )
        )
        return ErrorReport(
            source=source,
            exception_type=exception_type,
            message=message,
            frames=frames,
            findings=tuple(findings),
            intended_interpreter=intended_interpreter,
            issues=issues,
        )

    if exception_type in {"ModuleNotFoundError", "ImportError"}:
        module = _module_name(message)
        imported, owner = _import_name(message)
        if module:
            findings.append(
                _finding(
                    "error.module_not_found",
                    "ERROR",
                    Confidence.CONFIRMED,
                    f"The interpreter could not find the module {module!r}.",
                    evidence + (f"Missing module: {module}",),
                    missing=("The interpreter that produced the traceback was not executed.",),
                    hypotheses=(
                        "The package may not be installed in the active environment.",
                        "A different interpreter or virtual environment may be active.",
                        "The import name may differ from the distribution name.",
                    ),
                    next_steps=(
                        "Confirm the interpreter used to run the code.",
                        "Install or select the package in that same environment.",
                        "Check whether the import name differs from the package name.",
                    ),
                )
            )
        elif imported and owner:
            findings.append(
                _finding(
                    "error.import_name_missing",
                    "ERROR",
                    Confidence.LIKELY,
                    f"The module {owner!r} does not expose {imported!r}.",
                    evidence + (f"Missing name: {imported} from {owner}",),
                    hypotheses=(
                        "The installed package version may be older or newer than the code expects.",
                        "The module may be shadowed by a local file with the same name.",
                    ),
                    next_steps=(
                        "Check the installed package version and its public API.",
                        "Look for a local file or directory that shadows the module.",
                    ),
                )
            )
    elif exception_type in {"SyntaxError", "IndentationError", "TabError"}:
        findings.append(
            _finding(
                "error.syntax_error",
                "ERROR",
                Confidence.CONFIRMED,
                "The traceback reports a source-code syntax or indentation problem.",
                evidence,
                hypotheses=("Mixed tabs and spaces or an incomplete edit may be involved.",),
                next_steps=(
                    "Open the reported file and line and correct the syntax.",
                    "This is not an environment or package problem.",
                ),
            )
        )
    elif exception_type == "PermissionError":
        findings.append(
            _finding(
                "error.permission_denied",
                "ERROR",
                Confidence.CONFIRMED,
                "The operation was denied by filesystem or operating-system permissions.",
                evidence,
                next_steps=(
                    "Check the file or directory permissions and ownership.",
                    "Avoid elevating privileges until the required access is understood.",
                ),
            )
        )
    elif exception_type == "FileNotFoundError":
        findings.append(
            _finding(
                "error.file_not_found",
                "ERROR",
                Confidence.CONFIRMED,
                "A required file or directory was not found.",
                evidence,
                next_steps=(
                    "Check the path and the working directory used to run the code.",
                    "Confirm that generated or downloaded files exist.",
                ),
            )
        )
    elif exception_type == "AttributeError":
        findings.append(
            _finding(
                "error.attribute_missing",
                "ERROR",
                Confidence.LIKELY,
                "An object does not expose the requested attribute.",
                evidence,
                hypotheses=(
                    "The installed package version may not match the code's expectations.",
                    "The object may be a different type than assumed.",
                ),
                next_steps=(
                    "Check the package version and the object's actual type.",
                    "Review the API for the installed version.",
                ),
            )
        )
    elif exception_type == "TypeError":
        findings.append(
            _finding(
                "error.type_mismatch",
                "ERROR",
                Confidence.LIKELY,
                "A value or call signature did not match what the code expected.",
                evidence,
                hypotheses=(
                    "A library version may have changed a function signature.",
                    "A value may have an unexpected type.",
                ),
                next_steps=(
                    "Inspect the reported call and the installed library version.",
                    "Check the function signature for that version.",
                ),
            )
        )
    elif exception_type == "MemoryError":
        findings.append(
            _finding(
                "error.memory_exhausted",
                "ERROR",
                Confidence.CONFIRMED,
                "The process ran out of memory.",
                evidence,
                next_steps=("Reduce the data size or increase available memory.",),
            )
        )
    else:
        findings.append(
            _finding(
                "error.classified",
                "WARNING",
                Confidence.LIKELY,
                f"The traceback reports {exception_type}.",
                evidence,
                missing=("No specific environment relationship was established.",),
                next_steps=(
                    "Read the exception message and the last application frame.",
                    "Reproduce with the same interpreter and inputs.",
                ),
            )
        )

    if intended_interpreter:
        inventory = build_inventory(intended_interpreter)
        prefix = inventory.prefix
        if prefix and _frames_outside_prefix(frames, prefix):
            findings.append(
                _finding(
                    "error.frames_outside_intended_environment",
                    "WARNING",
                    Confidence.LIKELY,
                    "Traceback frames do not appear to come from the intended environment.",
                    (
                        f"Intended prefix: {prefix}",
                        *(f"Frame: {frame.path}" for frame in frames[-5:] if frame.path),
                    ),
                    missing=("Frame paths alone do not prove which interpreter ran.",),
                    next_steps=(
                        "Confirm the interpreter and environment used to run the code.",
                        "Select the intended interpreter in the IDE or terminal.",
                    ),
                )
            )
        module = _module_name(message)
        if module and inventory.distributions:
            target = normalize_name(module)
            installed = [
                distribution
                for distribution in inventory.distributions
                if distribution.normalized_name == target
            ]
            if installed:
                findings.append(
                    _finding(
                        "error.module_metadata_present",
                        "INFO",
                        Confidence.LIKELY,
                        f"Distribution metadata for {module!r} exists in the intended environment.",
                        tuple(
                            f"{item.name} {item.version} at {item.location}"
                            for item in installed[:5]
                        ),
                        missing=(
                            "Metadata presence does not prove the module is importable.",
                        ),
                        hypotheses=(
                            "The traceback may come from a different environment.",
                            "The package may be broken or shadowed.",
                        ),
                        next_steps=(
                            "Confirm that the traceback was produced by the intended interpreter.",
                            "Check for local modules that shadow the package.",
                        ),
                    )
                )

    return ErrorReport(
        source=source,
        exception_type=exception_type,
        message=message,
        frames=frames,
        findings=tuple(findings),
        intended_interpreter=intended_interpreter,
        issues=issues,
    )
