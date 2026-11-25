"""Evaluate declared requirements against observed distribution metadata."""

from collections import defaultdict

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.models import Confidence
from pydoctor.package_models import DependencyStatus, PackageDistribution
from pydoctor.requirements import (
    MarkerNotEvaluated,
    RequirementError,
    evaluate_marker,
    marker_context,
    marker_references_extra,
    parse_requirement,
)
from pydoctor.versions import evaluate_specifier

SATISFIED = "SATISFIED"
MISSING = "MISSING"
VERSION_CONFLICT = "VERSION_CONFLICT"
UNKNOWN = "UNKNOWN"
SKIPPED = "SKIPPED"
OPTIONAL_UNKNOWN = "OPTIONAL_UNKNOWN"


def index_distributions(
    distributions: tuple[PackageDistribution, ...],
) -> dict[str, tuple[PackageDistribution, ...]]:
    """Group distributions by normalized name for case-insensitive lookup."""
    groups: dict[str, list[PackageDistribution]] = defaultdict(list)
    for distribution in distributions:
        if distribution.normalized_name:
            groups[distribution.normalized_name].append(distribution)
    return {name: tuple(items) for name, items in groups.items()}


def find_duplicates(
    distributions: tuple[PackageDistribution, ...],
) -> dict[str, tuple[PackageDistribution, ...]]:
    """Return normalized names installed more than once."""
    return {
        name: items
        for name, items in index_distributions(distributions).items()
        if len(items) > 1
    }


def _status(
    distribution: PackageDistribution,
    requirement: str,
    status: str,
    confidence: Confidence,
    explanation: str,
    *,
    normalized_name: str | None = None,
    installed_version: str | None = None,
    specifier: str | None = None,
    marker: str | None = None,
    evidence: tuple[str, ...] = (),
    issues: tuple[DiscoveryIssue, ...] = (),
) -> DependencyStatus:
    return DependencyStatus(
        kind="requirement",
        requirement=requirement,
        package=distribution.name,
        normalized_name=normalized_name,
        status=status,
        confidence=confidence,
        explanation=explanation,
        installed_version=installed_version,
        specifier=specifier,
        marker=marker,
        evidence=evidence,
        issues=issues,
    )


def _evaluate_requirement(
    distribution: PackageDistribution,
    raw: str,
    index: dict[str, tuple[PackageDistribution, ...]],
    context: dict[str, str],
) -> DependencyStatus:
    try:
        requirement = parse_requirement(raw)
    except RequirementError as exc:
        return _status(
            distribution,
            raw,
            UNKNOWN,
            Confidence.UNKNOWN,
            "The requirement string could not be parsed with the supported subset.",
            issues=(
                DiscoveryIssue(
                    "requirement_unparsed",
                    "dependency_analysis",
                    str(exc),
                    distribution.location,
                ),
            ),
        )

    if requirement.marker:
        if marker_references_extra(requirement.marker):
            return _status(
                distribution,
                raw,
                OPTIONAL_UNKNOWN,
                Confidence.UNKNOWN,
                "The requirement applies only to an optional extra; extras were not selected.",
                normalized_name=requirement.normalized_name,
                specifier=requirement.specifier,
                marker=requirement.marker,
            )
        try:
            applicable = evaluate_marker(requirement.marker, context)
        except MarkerNotEvaluated as exc:
            return _status(
                distribution,
                raw,
                UNKNOWN,
                Confidence.UNKNOWN,
                "The environment marker could not be evaluated for this target.",
                normalized_name=requirement.normalized_name,
                specifier=requirement.specifier,
                marker=requirement.marker,
                issues=(
                    DiscoveryIssue(
                        "environment_marker_not_evaluated",
                        "dependency_analysis",
                        str(exc),
                        distribution.location,
                    ),
                ),
            )
        if not applicable:
            return _status(
                distribution,
                raw,
                SKIPPED,
                Confidence.CONFIRMED,
                "The environment marker evaluates to false for this target.",
                normalized_name=requirement.normalized_name,
                specifier=requirement.specifier,
                marker=requirement.marker,
            )

    if requirement.url:
        return _status(
            distribution,
            raw,
            UNKNOWN,
            Confidence.UNKNOWN,
            "A direct-reference requirement was not resolved or downloaded.",
            normalized_name=requirement.normalized_name,
            marker=requirement.marker,
            evidence=(f"Direct reference: {requirement.url}",),
        )

    installed = index.get(requirement.normalized_name, ())
    if not installed:
        return _status(
            distribution,
            raw,
            MISSING,
            Confidence.LIKELY,
            "No observed distribution satisfies this dependency name; inventory may be incomplete.",
            normalized_name=requirement.normalized_name,
            specifier=requirement.specifier,
            marker=requirement.marker,
            evidence=(f"Looked up normalized name: {requirement.normalized_name}",),
        )

    versions = tuple(item.version for item in installed)
    evaluations = [evaluate_specifier(requirement.specifier, version) for version in versions]
    if any(result is True for result in evaluations):
        confidence = Confidence.CONFIRMED if len(installed) == 1 else Confidence.LIKELY
        explanation = (
            "An observed distribution satisfies the requirement; import success was not verified."
            if len(installed) == 1
            else "At least one of several installed copies satisfies the requirement."
        )
        return _status(
            distribution,
            raw,
            SATISFIED,
            confidence,
            explanation,
            normalized_name=requirement.normalized_name,
            installed_version=versions[0],
            specifier=requirement.specifier,
            marker=requirement.marker,
            evidence=tuple(
                f"Observed {item.name} {item.version} at {item.location}" for item in installed
            ),
        )
    if any(result is None for result in evaluations):
        return _status(
            distribution,
            raw,
            UNKNOWN,
            Confidence.UNKNOWN,
            "Installed or required versions could not be compared reliably.",
            normalized_name=requirement.normalized_name,
            installed_version=versions[0],
            specifier=requirement.specifier,
            marker=requirement.marker,
            issues=(
                DiscoveryIssue(
                    "version_unparsed",
                    "dependency_analysis",
                    "A version or specifier uses unsupported syntax.",
                    distribution.location,
                ),
            ),
        )
    return _status(
        distribution,
        raw,
        VERSION_CONFLICT,
        Confidence.CONFIRMED,
        "Observed installed versions do not satisfy the declared requirement.",
        normalized_name=requirement.normalized_name,
        installed_version=versions[0],
        specifier=requirement.specifier,
        marker=requirement.marker,
        evidence=tuple(
            f"Observed {item.name} {item.version} at {item.location}" for item in installed
        ),
    )


def _requires_python_status(
    distribution: PackageDistribution,
    python_version: str | None,
) -> DependencyStatus | None:
    specifier = distribution.requires_python
    if not specifier:
        return None
    if python_version is None:
        return DependencyStatus(
            kind="requires_python",
            requirement=f"Requires-Python: {specifier}",
            package=distribution.name,
            normalized_name="python",
            status=UNKNOWN,
            confidence=Confidence.UNKNOWN,
            explanation="The target interpreter version was not established.",
            specifier=specifier,
            issues=(
                DiscoveryIssue(
                    "python_version_unknown",
                    "dependency_analysis",
                    "Requires-Python could not be checked without a target version.",
                    distribution.location,
                ),
            ),
        )
    result = evaluate_specifier(specifier, python_version)
    if result is None:
        return DependencyStatus(
            kind="requires_python",
            requirement=f"Requires-Python: {specifier}",
            package=distribution.name,
            normalized_name="python",
            status=UNKNOWN,
            confidence=Confidence.UNKNOWN,
            explanation="The Requires-Python specifier could not be parsed.",
            installed_version=python_version,
            specifier=specifier,
            issues=(
                DiscoveryIssue(
                    "requires_python_unparsed",
                    "dependency_analysis",
                    "Unsupported Requires-Python syntax.",
                    distribution.location,
                ),
            ),
        )
    return DependencyStatus(
        kind="requires_python",
        requirement=f"Requires-Python: {specifier}",
        package=distribution.name,
        normalized_name="python",
        status=SATISFIED if result else VERSION_CONFLICT,
        confidence=Confidence.CONFIRMED,
        explanation=(
            "The observed interpreter version satisfies Requires-Python."
            if result
            else "The observed interpreter version does not satisfy Requires-Python."
        ),
        installed_version=python_version,
        specifier=specifier,
        evidence=(f"Target Python version: {python_version}",),
    )


def analyze_dependencies(
    distributions: tuple[PackageDistribution, ...],
    python_version: str | None,
) -> tuple[DependencyStatus, ...]:
    """Evaluate every declared requirement and Requires-Python clause."""
    index = index_distributions(distributions)
    context = marker_context(python_version)
    results: list[DependencyStatus] = []
    for distribution in distributions:
        for raw in distribution.requires_dist:
            results.append(_evaluate_requirement(distribution, raw, index, context))
        requires_python = _requires_python_status(distribution, python_version)
        if requires_python is not None:
            results.append(requires_python)
    return tuple(
        sorted(
            results,
            key=lambda item: (
                (item.package or "").casefold(),
                item.kind,
                item.requirement.casefold(),
                item.status,
            ),
        )
    )
