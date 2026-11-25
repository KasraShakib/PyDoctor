"""Build safe repair plans and execute only explicitly approved allowlisted steps."""

import os
import subprocess
from collections.abc import Mapping
from typing import Any, Callable

from pydoctor.dependency_analysis import index_distributions
from pydoctor.models import Confidence, SeverityFinding
from pydoctor.package_inventory import build_inventory
from pydoctor.repair_models import RepairExecution, RepairPlan, RepairStep
from pydoctor.requirements import RequirementError, parse_requirement
from pydoctor.versions import evaluate_specifier

_ALLOWED_PIP_ACTIONS = {"install"}


def _step(
    step_id: str,
    title: str,
    rationale: str,
    risk: str,
    argv: tuple[str, ...] | None,
    verification: str,
    evidence: tuple[str, ...] = (),
) -> RepairStep:
    return RepairStep(
        step_id=step_id,
        title=title,
        rationale=rationale,
        risk=risk,
        requires_confirmation=True,
        argv=argv,
        verification=verification,
        evidence=evidence,
    )


def _interpreter(report: Mapping[str, Any]) -> str | None:
    target = report.get("target")
    if isinstance(target, dict):
        supplied = target.get("supplied_path")
        if isinstance(supplied, str):
            return supplied
    intended = report.get("intended_interpreter")
    return intended if isinstance(intended, str) else None


def _pip_install(interpreter: str | None, requirement: str) -> tuple[str, ...] | None:
    if not interpreter or not os.path.isabs(interpreter):
        return None
    return (interpreter, "-m", "pip", "install", requirement)


def build_repair_plan(report: Mapping[str, Any], source: str = "<report>") -> RepairPlan:
    """Derive proposed actions from a PyDoctor report without executing anything."""
    scope = report.get("scope") if isinstance(report.get("scope"), str) else None
    interpreter = _interpreter(report)
    steps: list[RepairStep] = []
    seen: set[tuple[str, tuple[str, ...] | None]] = set()

    def add(step: RepairStep) -> None:
        key = (step.title, step.argv)
        if key not in seen:
            seen.add(key)
            steps.append(step)

    dependencies = report.get("dependencies")
    if isinstance(dependencies, list):
        for item in dependencies:
            if not isinstance(item, dict):
                continue
            if item.get("kind") == "requires_python":
                continue
            status = item.get("status")
            requirement = item.get("requirement")
            if not isinstance(requirement, str):
                continue
            if status == "MISSING":
                argv = _pip_install(interpreter, requirement)
                add(
                    _step(
                        f"install-{len(steps) + 1}",
                        f"Install missing dependency {requirement}",
                        "A declared dependency has no observed matching distribution.",
                        "MEDIUM",
                        argv,
                        "Re-run package diagnostics and confirm the requirement is SATISFIED.",
                        (f"Declared requirement: {requirement}",),
                    )
                )
            elif status == "VERSION_CONFLICT":
                argv = _pip_install(interpreter, requirement)
                add(
                    _step(
                        f"resolve-{len(steps) + 1}",
                        f"Resolve version constraint {requirement}",
                        "Observed installed versions do not satisfy the declared requirement.",
                        "MEDIUM",
                        argv,
                        "Re-run package diagnostics and confirm the conflict is gone.",
                        (f"Declared requirement: {requirement}",),
                    )
                )

    findings = report.get("findings")
    codes = {
        item.get("code")
        for item in findings
        if isinstance(item, dict) and isinstance(item.get("code"), str)
    } if isinstance(findings, list) else set()

    if "packages.requires_python_incompatible" in codes:
        add(
            _step(
                "requires-python",
                "Use an interpreter that satisfies Requires-Python",
                "One or more distributions declare a Python range the target does not satisfy.",
                "LOW",
                None,
                "Re-run package diagnostics with the replacement interpreter.",
            )
        )
    if "packages.duplicate_distribution" in codes:
        add(
            _step(
                "duplicate-distribution",
                "Inspect duplicate distribution locations",
                "The same distribution name is installed more than once.",
                "HIGH",
                None,
                "Confirm which copy is imported before changing anything.",
            )
        )
    if codes & {"notebooks.kernel_missing", "notebooks.kernel_mismatch"}:
        add(
            _step(
                "notebook-kernel",
                "Register or select the intended Jupyter kernel",
                "A notebook references a kernel that was not observed or does not match intent.",
                "LOW",
                None,
                "Re-run notebook diagnostics and confirm the kernel relationship.",
            )
        )
    if "error.module_not_found" in codes:
        module = None
        for item in (findings if isinstance(findings, list) else []):
            if isinstance(item, dict) and item.get("code") == "error.module_not_found":
                for line in item.get("evidence", []):
                    if isinstance(line, str) and line.startswith("Missing module: "):
                        module = line.removeprefix("Missing module: ").strip()
        if module:
            argv = _pip_install(interpreter, module)
            add(
                _step(
                    "install-module",
                    f"Install module {module}",
                    "The traceback reports that a module could not be imported.",
                    "MEDIUM",
                    argv,
                    "Re-run the failing code with the same interpreter.",
                    (f"Missing module: {module}",),
                )
            )
    if "error.frames_outside_intended_environment" in codes:
        add(
            _step(
                "select-interpreter",
                "Run the code with the intended interpreter",
                "Traceback frames do not appear to come from the intended environment.",
                "LOW",
                None,
                "Re-run and confirm the traceback frames use the intended prefix.",
            )
        )

    if steps:
        finding = SeverityFinding(
            code="repair.plan_ready",
            severity="INFO",
            confidence=Confidence.CONFIRMED,
            summary="A dry-run repair plan was generated; no action was executed.",
            evidence=tuple(f"{step.step_id}: {step.title}" for step in steps[:5]),
            next_steps=(
                "Review every step, risk, and exact argv before approving execution.",
                "Execution requires explicit confirmation through the guarded API.",
            ),
        )
    else:
        finding = SeverityFinding(
            code="repair.no_actions",
            severity="INFO",
            confidence=Confidence.LIKELY,
            summary="No safe automated repair action was derived from this report.",
            evidence=(f"Source report scope: {scope}",),
            next_steps=("Review the report findings and apply manual steps if needed.",),
        )
    return RepairPlan(
        source_report=source,
        source_scope=scope,
        steps=tuple(steps),
        findings=(finding,),
    )


def _validate_step(step: RepairStep) -> None:
    if not step.requires_confirmation:
        raise ValueError("Step does not require confirmation.")
    argv = step.argv
    if argv is None:
        raise ValueError("Step has no executable argv.")
    if len(argv) < 5:
        raise ValueError("Step argv is too short.")
    if not os.path.isabs(argv[0]) or not argv[0].casefold().endswith((".exe", "python", "python3")):
        raise ValueError("Step interpreter must be an absolute Python path.")
    if tuple(argv[1:3]) != ("-m", "pip") or argv[3] not in _ALLOWED_PIP_ACTIONS:
        raise ValueError("Only allowlisted 'python -m pip install' steps may execute.")
    if any("\x00" in part for part in argv):
        raise ValueError("Step argv contains a NUL character.")


def _verify_requirement(interpreter: str, requirement: str) -> bool | None:
    try:
        parsed = parse_requirement(requirement)
    except RequirementError:
        return None
    inventory = build_inventory(interpreter)
    installed = index_distributions(inventory.distributions).get(parsed.normalized_name, ())
    if not installed:
        return False
    return any(
        evaluate_specifier(parsed.specifier, item.version) is True for item in installed
    )


def execute_repair_step(
    step: RepairStep,
    *,
    approved_step_id: str,
    runner: Callable[..., Any] | None = None,
    timeout: int = 300,
) -> RepairExecution:
    """Execute one step only after exact step-id approval and allowlist checks."""
    if approved_step_id != step.step_id:
        raise PermissionError("Approval does not match the requested step id.")
    _validate_step(step)
    assert step.argv is not None
    runner = runner or subprocess.run
    try:
        completed = runner(
            list(step.argv),
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
        return RepairExecution(
            step_id=step.step_id,
            executed=False,
            notes=(f"Execution failed: {type(exc).__name__}",),
        )
    verified = None
    if completed.returncode == 0:
        verified = _verify_requirement(step.argv[0], step.argv[4])
    return RepairExecution(
        step_id=step.step_id,
        executed=True,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        verified=verified,
        notes=("Verification re-reads package metadata only.",),
    )
