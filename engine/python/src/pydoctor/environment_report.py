"""Aggregate existing milestone evidence into one environment report."""

from pydoctor.comparison import compare_evidence
from pydoctor.discovery import discover_environments
from pydoctor.environment_models import EnvironmentReport, EnvironmentSummary
from pydoctor.interpreter_target import observe_target
from pydoctor.models import Confidence, SeverityFinding
from pydoctor.notebooks import inspect_notebooks
from pydoctor.package_diagnostics import inspect_packages

_SEVERITY_ORDER = {"INFO": 0, "WARNING": 1, "ERROR": 2}


def _highest_severity(findings: tuple[SeverityFinding, ...]) -> str:
    if not findings:
        return "INFO"
    return max((finding.severity for finding in findings), key=lambda value: _SEVERITY_ORDER.get(value, 0))


def build_environment_report(interpreter: str, project: str | None = None) -> EnvironmentReport:
    """Combine M2, M3, M4, and optional M7 evidence without new collection rules."""
    target = observe_target(interpreter)
    discovery = discover_environments(project)
    comparison = compare_evidence(target, discovery)
    packages = inspect_packages(interpreter)
    notebooks = inspect_notebooks(project, interpreter) if project else None

    missing = sum(1 for item in packages.dependencies if item.status == "MISSING")
    conflicts = sum(1 for item in packages.dependencies if item.status == "VERSION_CONFLICT")
    findings: list[SeverityFinding] = [
        SeverityFinding(
            code="environment.target",
            severity="INFO" if target.status == "REGULAR_FILE" else "ERROR",
            confidence=Confidence.CONFIRMED if target.status == "REGULAR_FILE" else Confidence.UNKNOWN,
            summary="The report describes the explicitly supplied interpreter path.",
            evidence=(
                f"Target: {interpreter}",
                f"Target status: {target.status}",
            ),
            next_steps=("Path observation does not verify interpreter health.",),
        ),
        SeverityFinding(
            code="environment.discovery",
            severity="INFO",
            confidence=Confidence.CONFIRMED,
            summary="Windows discovery evidence was collected for context.",
            evidence=(
                f"Candidates: {len(discovery.candidates)}",
                f"Discovery issues: {len(discovery.issues)}",
            ),
            next_steps=("Discovery may be incomplete; review its issues.",),
        ),
        SeverityFinding(
            code="environment.comparison",
            severity="ERROR"
            if comparison.outcome == "NO_MATCH"
            else "WARNING"
            if comparison.outcome in {"PARTIALLY_MATCHED", "INSUFFICIENT_EVIDENCE"}
            else "INFO",
            confidence=Confidence.CONFIRMED,
            summary=f"Intended-interpreter comparison outcome: {comparison.outcome}.",
            evidence=(
                f"Outcome: {comparison.outcome}",
                f"Compared candidates: {len(comparison.comparisons)}",
            ),
            next_steps=("Match confidence is a path relationship, not interpreter health.",),
        ),
        SeverityFinding(
            code="environment.packages",
            severity="ERROR" if conflicts else "WARNING" if missing else "INFO",
            confidence=Confidence.CONFIRMED,
            summary="Package metadata was evaluated for the supplied interpreter.",
            evidence=(
                f"Distributions: {len(packages.distributions)}",
                f"Missing dependencies: {missing}",
                f"Version conflicts: {conflicts}",
            ),
            next_steps=("Metadata presence does not prove import success.",),
        ),
    ]
    if notebooks is not None:
        findings.append(
            SeverityFinding(
                code="environment.notebooks",
                severity=_highest_severity(notebooks.findings),
                confidence=Confidence.CONFIRMED,
                summary="Notebook and kernelspec metadata was evaluated for the project.",
                evidence=(
                    f"Notebooks: {len(notebooks.notebooks)}",
                    f"Kernels: {len(notebooks.kernels)}",
                ),
                next_steps=("Notebook metadata can be stale; kernel launch was not tested.",),
            )
        )
    findings_tuple = tuple(findings)
    summary = EnvironmentSummary(
        comparison_outcome=comparison.outcome,
        distributions=len(packages.distributions),
        missing_dependencies=missing,
        version_conflicts=conflicts,
        notebooks=len(notebooks.notebooks) if notebooks else 0,
        kernels=len(notebooks.kernels) if notebooks else 0,
        severity=_highest_severity(findings_tuple),
    )
    issues = (
        tuple(discovery.issues)
        + tuple(comparison.discovery_issues)
        + tuple(packages.issues)
        + (tuple(notebooks.issues) if notebooks else ())
    )
    return EnvironmentReport(
        interpreter=interpreter,
        project=project,
        target=target,
        summary=summary,
        discovery=discovery,
        comparison=comparison,
        packages=packages,
        notebooks=notebooks,
        findings=findings_tuple,
        issues=issues,
    )
