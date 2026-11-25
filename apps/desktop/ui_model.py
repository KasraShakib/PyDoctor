"""Pure formatting helpers for the PyDoctor desktop UI.

Keeping presentation logic here makes it testable without starting Tk.
"""

import json
from collections.abc import Mapping
from typing import Any


def pretty(report: Mapping[str, Any]) -> str:
    """Serialize a report for the raw JSON tab."""
    return json.dumps(report, indent=2, ensure_ascii=False)


def _findings(findings: Any) -> list[str]:
    lines = ["Findings"]
    items = findings if isinstance(findings, list) else []
    if not items:
        lines.append("  (none)")
    for item in items:
        if not isinstance(item, dict):
            continue
        lines.append(
            f"  [{item.get('severity', 'INFO')}] {item.get('code', '?')} "
            f"({item.get('confidence', '?')})"
        )
        if item.get("summary"):
            lines.append(f"    {item['summary']}")
        for evidence in (item.get("evidence") or [])[:5]:
            lines.append(f"    - {evidence}")
        for step in (item.get("next_steps") or [])[:3]:
            lines.append(f"    next: {step}")
    return lines


def describe_engine_info(report: Mapping[str, Any]) -> str:
    modes = report.get("modes") if isinstance(report.get("modes"), dict) else {}
    lines = [
        "PyDoctor engine",
        f"  Version: {report.get('version')}",
        f"  Engine Python: {report.get('engine_python')}",
        f"  Modes: {len(modes)}",
    ]
    for name, meta in modes.items():
        if isinstance(meta, dict):
            lines.append(f"    {name}: {meta.get('flag') or '(default)'} -> {meta.get('schema')}")
    return "\n".join(lines)


def describe_environment_report(report: Mapping[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    lines = [
        "Environment summary",
        f"  Interpreter: {report.get('interpreter')}",
        f"  Project: {report.get('project') or '(none)'}",
        f"  Comparison: {summary.get('comparison_outcome')}",
        f"  Distributions: {summary.get('distributions')}",
        f"  Missing dependencies: {summary.get('missing_dependencies')}",
        f"  Version conflicts: {summary.get('version_conflicts')}",
        f"  Notebooks: {summary.get('notebooks')}",
        f"  Kernels: {summary.get('kernels')}",
        f"  Severity: {summary.get('severity')}",
        "",
    ]
    return "\n".join(lines + _findings(report.get("findings")))


def describe_package_report(report: Mapping[str, Any]) -> str:
    distributions = report.get("distributions") if isinstance(report.get("distributions"), list) else []
    dependencies = report.get("dependencies") if isinstance(report.get("dependencies"), list) else []
    missing = sum(1 for item in dependencies if isinstance(item, dict) and item.get("status") == "MISSING")
    conflicts = sum(
        1 for item in dependencies if isinstance(item, dict) and item.get("status") == "VERSION_CONFLICT"
    )
    lines = [
        "Package summary",
        f"  Interpreter prefix: {report.get('interpreter_prefix')}",
        f"  Python version: {report.get('python_version') or '(unknown)'}",
        f"  Distributions: {len(distributions)}",
        f"  Dependencies evaluated: {len(dependencies)}",
        f"  Missing: {missing}",
        f"  Version conflicts: {conflicts}",
        "",
    ]
    names = [item.get("name") for item in distributions if isinstance(item, dict) and item.get("name")]
    if names:
        lines.append("Installed distributions")
        lines.extend(f"  {name}" for name in names[:40])
        if len(names) > 40:
            lines.append(f"  ... and {len(names) - 40} more")
        lines.append("")
    return "\n".join(lines + _findings(report.get("findings")))


def describe_notebook_report(report: Mapping[str, Any]) -> str:
    notebooks = report.get("notebooks") if isinstance(report.get("notebooks"), list) else []
    kernels = report.get("kernels") if isinstance(report.get("kernels"), list) else []
    lines = [
        "Notebook summary",
        f"  Target: {report.get('target')}",
        f"  Target kind: {report.get('target_kind')}",
        f"  Notebooks: {len(notebooks)}",
        f"  Kernels: {len(kernels)}",
        "",
    ]
    if kernels:
        lines.append("Kernels")
        for kernel in kernels[:20]:
            if isinstance(kernel, dict):
                lines.append(f"  {kernel.get('name')}: {kernel.get('interpreter') or '(no path)'}")
        lines.append("")
    return "\n".join(lines + _findings(report.get("findings")))


def describe_error_report(report: Mapping[str, Any]) -> str:
    frames = report.get("frames") if isinstance(report.get("frames"), list) else []
    lines = [
        "Error summary",
        f"  Source: {report.get('source')}",
        f"  Exception: {report.get('exception_type') or '(unclassified)'}",
        f"  Message: {report.get('message') or '(none)'}",
        f"  Frames: {len(frames)}",
        "",
    ]
    return "\n".join(lines + _findings(report.get("findings")))


def describe_repair_plan(report: Mapping[str, Any]) -> str:
    steps = report.get("steps") if isinstance(report.get("steps"), list) else []
    lines = [
        "Repair plan (dry run)",
        f"  Source: {report.get('source_report')}",
        f"  Steps: {len(steps)}",
        "",
    ]
    for step in steps:
        if not isinstance(step, dict):
            continue
        lines.append(f"  [{step.get('risk', '?')}] {step.get('title')}")
        if step.get("argv"):
            lines.append(f"    argv: {step['argv']}")
        lines.append(f"    verify: {step.get('verification')}")
    lines.append("")
    return "\n".join(lines + _findings(report.get("findings")))


def describe(report: Mapping[str, Any]) -> str:
    """Return the human-readable summary for any PyDoctor report."""
    scope = report.get("scope")
    if scope == "environment_report":
        return describe_environment_report(report)
    if scope == "package_diagnostics":
        return describe_package_report(report)
    if scope == "notebook_diagnostics":
        return describe_notebook_report(report)
    if scope == "error_explanation":
        return describe_error_report(report)
    if scope == "repair_plan":
        return describe_repair_plan(report)
    if scope == "engine_info":
        return describe_engine_info(report)
    return pretty(report)


def details(report: Mapping[str, Any]) -> str:
    """Return the detailed JSON view used by the Details tab."""
    return pretty(report)
