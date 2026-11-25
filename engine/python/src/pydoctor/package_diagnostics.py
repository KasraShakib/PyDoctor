"""Read-only package inventory and dependency diagnostics orchestration."""

from pydoctor.comparison_models import TargetObservation
from pydoctor.dependency_analysis import (
    MISSING,
    UNKNOWN,
    VERSION_CONFLICT,
    analyze_dependencies,
    find_duplicates,
)
from pydoctor.interpreter_target import observe_target
from pydoctor.models import Confidence, SeverityFinding
from pydoctor.package_inventory import build_inventory
from pydoctor.package_models import (
    DependencyStatus,
    PackageDistribution,
    PackageReport,
    SitePackagesRoot,
)

_EXAMPLE_LIMIT = 5


def _examples(values: list[str], limit: int = _EXAMPLE_LIMIT) -> tuple[str, ...]:
    unique = sorted(set(values))
    shown = unique[:limit]
    if len(unique) > limit:
        shown.append(f"... and {len(unique) - limit} more")
    return tuple(shown)


def _metadata_incomplete(distribution: PackageDistribution) -> bool:
    codes = {issue.code for issue in distribution.issues}
    return bool(
        codes
        & {
            "metadata_file_missing",
            "metadata_unreadable",
            "metadata_missing_name",
            "metadata_missing_version",
        }
    )


def _target_finding(target: TargetObservation) -> SeverityFinding:
    return SeverityFinding(
        code="packages.target_unavailable",
        severity="ERROR",
        confidence=Confidence.UNKNOWN,
        summary="Package inventory requires an observed regular interpreter file.",
        evidence=(
            f"Target status: {target.status}.",
            f"Supplied path: {target.supplied_path!r}.",
        ),
        missing_information=(
            "A regular interpreter file is required to derive a site-packages location.",
        ),
        hypotheses=(
            "The path may be missing, a directory, or inaccessible.",
            "The path may point to a launcher rather than an installation.",
        ),
        next_steps=(
            "Select the interpreter file itself, not its directory or a shell alias.",
            "Re-run discovery or comparison to inspect the supplied path.",
        ),
    )


def _inventory_finding(
    roots: tuple[SitePackagesRoot, ...],
    distributions: tuple[PackageDistribution, ...],
) -> SeverityFinding:
    existing = [root for root in roots if root.is_directory]
    summary = (
        "Distribution metadata was read from observed site-packages locations."
        if existing
        else "No conventional site-packages location was observed; no distributions were read."
    )
    return SeverityFinding(
        code="packages.inventory_observed",
        severity="INFO",
        confidence=Confidence.CONFIRMED,
        summary=summary,
        evidence=(
            f"Observed distributions: {len(distributions)}.",
            f"Existing site-packages directories: {len(existing)}.",
            *(f"site-packages: {root.path}" for root in existing[:_EXAMPLE_LIMIT]),
        ),
        next_steps=(
            "Distribution metadata does not prove that a package imports successfully.",
            "Package contents, native extensions, and runtime behavior were not verified.",
        ),
    )


def _no_site_packages_finding(roots: tuple[SitePackagesRoot, ...]) -> SeverityFinding:
    return SeverityFinding(
        code="packages.no_site_packages",
        severity="WARNING",
        confidence=Confidence.UNKNOWN,
        summary="No conventional site-packages directory was observed for this interpreter.",
        evidence=tuple(f"Checked: {root.path}" for root in roots),
        missing_information=(
            "The interpreter may use an unusual layout or an embedded distribution.",
        ),
        hypotheses=(
            "The prefix may have been derived from a launcher or shim.",
            "The environment may not have been created yet.",
        ),
        next_steps=(
            "Confirm the interpreter path belongs to a full Python installation.",
            "Check the environment with the interpreter's own tooling if appropriate.",
        ),
    )


def _duplicate_finding(
    duplicates: dict[str, tuple[PackageDistribution, ...]],
) -> SeverityFinding:
    return SeverityFinding(
        code="packages.duplicate_distribution",
        severity="WARNING",
        confidence=Confidence.LIKELY,
        summary="The same distribution name is installed more than once.",
        evidence=_examples(
            [
                f"{name}: " + ", ".join(f"{item.version} at {item.location}" for item in items)
                for name, items in duplicates.items()
            ]
        ),
        missing_information=(
            "Which copy is imported first depends on sys.path ordering, which was not observed.",
        ),
        hypotheses=(
            "Stale metadata may remain after an upgrade.",
            "Multiple site-packages roots may be present.",
        ),
        next_steps=(
            "Inspect the reported locations before removing or reinstalling anything.",
            "Do not delete distribution metadata based on this finding alone.",
        ),
    )


def _dependency_finding(
    code: str,
    severity: str,
    confidence: Confidence,
    summary: str,
    statuses: list[DependencyStatus],
    next_steps: tuple[str, ...],
) -> SeverityFinding:
    return SeverityFinding(
        code=code,
        severity=severity,
        confidence=confidence,
        summary=summary,
        evidence=_examples(
            [
                f"{item.package or 'unknown'} requires {item.requirement}"
                + (f" (installed: {item.installed_version})" if item.installed_version else "")
                for item in statuses
            ]
        ),
        missing_information=(
            "Declared metadata is not proof of import success or runtime compatibility.",
        ),
        next_steps=next_steps,
    )


def inspect_packages(interpreter_path: str) -> PackageReport:
    """Observe an interpreter path and evaluate installed distribution metadata.

    The target interpreter is never executed, its packages are never imported,
    and no package manager or environment mutation is performed.
    """
    target = observe_target(interpreter_path)
    if target.status != "REGULAR_FILE":
        return PackageReport(
            target=target,
            interpreter_prefix=None,
            python_version=None,
            python_version_source=None,
            site_packages=(),
            distributions=(),
            dependencies=(),
            findings=(_target_finding(target),),
        )

    inventory = build_inventory(interpreter_path)
    distributions = inventory.distributions
    dependencies = analyze_dependencies(distributions, inventory.python_version)
    duplicates = find_duplicates(distributions)

    findings: list[SeverityFinding] = [
        _inventory_finding(inventory.roots, distributions),
    ]
    if not any(root.is_directory for root in inventory.roots):
        findings.append(_no_site_packages_finding(inventory.roots))
    elif not distributions:
        findings.append(
            SeverityFinding(
                code="packages.no_distributions",
                severity="WARNING",
                confidence=Confidence.LIKELY,
                summary="Site-packages exists but no distribution metadata was observed.",
                evidence=tuple(
                    f"Directory: {root.path} (entries: {root.distribution_count})"
                    for root in inventory.roots
                    if root.is_directory
                ),
                missing_information=(
                    "Packages may be installed without distribution metadata or elsewhere.",
                ),
                next_steps=(
                    "Confirm that packages were installed into this environment.",
                    "Check for an unusual site-packages layout.",
                ),
            )
        )

    if duplicates:
        findings.append(_duplicate_finding(duplicates))

    missing = [item for item in dependencies if item.status == MISSING]
    if missing:
        findings.append(
            _dependency_finding(
                "packages.missing_dependency",
                "WARNING",
                Confidence.LIKELY,
                "Some declared dependencies have no observed matching distribution.",
                missing,
                (
                    "Confirm the dependency is installed in the same environment.",
                    "Check whether the requirement is optional or environment-specific.",
                    "Do not install or remove packages based on this finding alone.",
                ),
            )
        )

    conflicts = [item for item in dependencies if item.status == VERSION_CONFLICT]
    if conflicts:
        findings.append(
            _dependency_finding(
                "packages.version_conflict",
                "ERROR",
                Confidence.CONFIRMED,
                "Observed installed versions do not satisfy declared requirements.",
                conflicts,
                (
                    "Review the declared requirement and the observed installed version.",
                    "Resolve version constraints deliberately; no change was made.",
                ),
            )
        )

    incompatible = [
        item
        for item in dependencies
        if item.kind == "requires_python" and item.status == VERSION_CONFLICT
    ]
    if incompatible:
        findings.append(
            _dependency_finding(
                "packages.requires_python_incompatible",
                "ERROR",
                Confidence.CONFIRMED,
                "Some distributions declare a Python version range the target does not satisfy.",
                incompatible,
                (
                    "Check whether the target interpreter version is the intended one.",
                    "Review each package's supported Python range before changing anything.",
                ),
            )
        )

    incomplete = [item for item in distributions if _metadata_incomplete(item)]
    if incomplete:
        findings.append(
            SeverityFinding(
                code="packages.metadata_incomplete",
                severity="WARNING",
                confidence=Confidence.LIKELY,
                summary="Some distribution metadata is missing or unreadable.",
                evidence=_examples([item.location for item in incomplete]),
                missing_information=(
                    "Name, version, and requirements may be unavailable for these entries.",
                ),
                next_steps=(
                    "Inspect the reported metadata locations manually.",
                    "Avoid deleting metadata directories until their origin is understood.",
                ),
            )
        )

    unknown = [
        item
        for item in dependencies
        if item.status == UNKNOWN
    ]
    if unknown:
        findings.append(
            SeverityFinding(
                code="packages.dependency_analysis_incomplete",
                severity="WARNING",
                confidence=Confidence.UNKNOWN,
                summary="Some requirements could not be conclusively evaluated.",
                evidence=_examples(
                    [f"{item.package or 'unknown'}: {item.requirement}" for item in unknown]
                ),
                missing_information=(
                    "Environment markers, direct references, extras, or unsupported "
                    "syntax prevented a definitive result.",
                ),
                next_steps=(
                    "Treat these requirements as unknown rather than satisfied or missing.",
                    "Inspect the owning package metadata if the result matters.",
                ),
            )
        )

    if inventory.python_version is None:
        findings.append(
            SeverityFinding(
                code="packages.python_version_unverified",
                severity="INFO",
                confidence=Confidence.UNKNOWN,
                summary="The target interpreter version was not established from local metadata.",
                evidence=tuple(f"Checked prefix: {inventory.prefix}"),
                missing_information=(
                    "Requires-Python checks need the target version, which was not executed.",
                ),
                hypotheses=(
                    "The environment may be a base installation without pyvenv.cfg.",
                    "The layout may not expose a python3.X directory.",
                ),
                next_steps=(
                    "Use discovery evidence or the interpreter's own version output if needed.",
                    "Do not assume compatibility when the version is unknown.",
                ),
            )
        )

    return PackageReport(
        target=target,
        interpreter_prefix=inventory.prefix,
        python_version=inventory.python_version,
        python_version_source=inventory.python_version_source,
        site_packages=inventory.roots,
        distributions=distributions,
        dependencies=dependencies,
        findings=tuple(findings),
        issues=tuple(inventory.issues),
    )
