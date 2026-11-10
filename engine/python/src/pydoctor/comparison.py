"""Compare intended-interpreter evidence without executing any target."""

import os
import stat

from pydoctor.comparison_models import (
    CandidateComparison,
    ComparisonReport,
    TargetObservation,
)
from pydoctor.discovery import discover_environments
from pydoctor.discovery_models import DiscoveryIssue, DiscoveryReport, PythonCandidate
from pydoctor.discovery_normalization import (
    absolute_path,
    normalized_path,
    windows_alias,
)
from pydoctor.interpreter_target import observe_target
from pydoctor.models import Confidence, Finding

EXACT = "EXACT_NORMALIZED_PATH"
IDENTITY = "SAME_FILE_IDENTITY"
POSSIBLE = "POSSIBLE"
NO_MATCH = "NO_MATCH"
INSUFFICIENT = "INSUFFICIENT_EVIDENCE"


def _issue_key(issue: DiscoveryIssue) -> tuple[str, str, str, str]:
    return issue.source, issue.code, issue.location or "", issue.message


def _candidate_paths(candidate: PythonCandidate) -> tuple[str, ...]:
    """Recover paths retained by M2 identity deduplication.

    A candidate with no canonical executable remains incomplete. Prefixes,
    filenames, versions, and arbitrary source locations are never match keys.
    """
    if candidate.executable is None:
        return ()
    paths = {candidate.executable}
    for evidence in candidate.evidence:
        observed = dict(evidence.metadata).get("observed_executable")
        if observed:
            paths.add(observed)
    return tuple(sorted(paths, key=lambda p: (normalized_path(p), p)))


def _compare_candidate(
    target: TargetObservation,
    candidate: PythonCandidate,
) -> CandidateComparison:
    paths = _candidate_paths(candidate)
    valid_paths = tuple(p for p in paths if absolute_path(p))
    local = list(candidate.issues)

    def result(method: str, confidence: Confidence) -> CandidateComparison:
        return CandidateComparison(
            candidate_executable=candidate.executable,
            compared_paths=paths,
            method=method,
            confidence=confidence,
            sources=tuple(sorted(set(candidate.sources))),
            evidence=tuple(
                sorted(
                    set(candidate.evidence),
                    key=lambda e: (e.source, e.location, e.metadata),
                )
            ),
            issues=tuple(sorted(set(local), key=_issue_key)),
        )

    if target.normalized_path is None or not valid_paths:
        return result(INSUFFICIENT, Confidence.UNKNOWN)

    alias = target.is_windowsapps_alias or any(windows_alias(p) for p in valid_paths)
    exact = any(normalized_path(p) == target.normalized_path for p in valid_paths)
    if exact:
        if alias:
            return result(POSSIBLE, Confidence.LIKELY)
        confidence = (
            Confidence.CONFIRMED
            if target.status == "REGULAR_FILE"
            else Confidence.LIKELY
        )
        return result(EXACT, confidence)

    if alias:
        local.append(
            DiscoveryIssue(
                "alias_identity_not_checked",
                "comparison",
                "Filesystem identity is not used to confirm WindowsApps aliases.",
                candidate.executable,
            )
        )
        return result(INSUFFICIENT, Confidence.UNKNOWN)

    if target.status != "REGULAR_FILE" or target.file_identity is None:
        return result(INSUFFICIENT, Confidence.UNKNOWN)

    undecidable = False
    for path in valid_paths:
        try:
            info = os.stat(path)
            if not stat.S_ISREG(info.st_mode):
                continue
            if not info.st_ino:
                undecidable = True
                local.append(
                    DiscoveryIssue(
                        "identity_unavailable",
                        "comparison",
                        "Candidate filesystem did not supply a usable file identity.",
                        path,
                    )
                )
                continue
            if (info.st_dev, info.st_ino) == target.file_identity:
                return result(IDENTITY, Confidence.CONFIRMED)
        except (FileNotFoundError, NotADirectoryError):
            local.append(
                DiscoveryIssue(
                    "candidate_not_found",
                    "comparison",
                    "Candidate path was not present during comparison.",
                    path,
                )
            )
        except (OSError, ValueError, NotImplementedError) as exc:
            undecidable = True
            local.append(
                DiscoveryIssue(
                    "identity_unavailable",
                    "comparison",
                    f"Candidate identity unavailable ({type(exc).__name__}).",
                    path,
                )
            )

    if undecidable:
        return result(INSUFFICIENT, Confidence.UNKNOWN)
    return result(NO_MATCH, Confidence.LIKELY)


def _outcome(
    target: TargetObservation,
    comparisons: tuple[CandidateComparison, ...],
) -> str:
    if target.status in {"INVALID", "DIRECTORY", "OTHER"}:
        return INSUFFICIENT
    if any(
        item.method in {EXACT, IDENTITY}
        and item.confidence == Confidence.CONFIRMED
        for item in comparisons
    ):
        return "MATCHED"
    if any(item.method in {EXACT, POSSIBLE} for item in comparisons):
        return "PARTIALLY_MATCHED"
    if (
        target.status == "REGULAR_FILE"
        and not target.is_windowsapps_alias
        and comparisons
        and all(item.method == NO_MATCH for item in comparisons)
    ):
        return NO_MATCH
    return INSUFFICIENT


def compare_evidence(
    target: TargetObservation,
    discovery: DiscoveryReport,
) -> ComparisonReport:
    """Analyze an observed target against an existing M2 report.

    This function may read candidate file metadata but does not collect sources,
    execute processes, or mutate the target or discovery report.
    """
    comparisons = tuple(
        sorted(
            (_compare_candidate(target, candidate) for candidate in discovery.candidates),
            key=lambda item: (
                normalized_path(item.candidate_executable or ""),
                item.sources,
                repr(item.evidence),
                item.method,
            ),
        )
    )
    outcome = _outcome(target, comparisons)
    summaries = {
        "MATCHED": (
            "Discovered evidence supports the target path or file identity; "
            "interpreter identity and health were not verified."
        ),
        "PARTIALLY_MATCHED": (
            "A path relationship was found, but a regular non-alias target "
            "relationship could not be confirmed."
        ),
        NO_MATCH: (
            "No relationship was found among the compared candidates; "
            "this is not proof that discovery is complete."
        ),
        INSUFFICIENT: (
            "Available target or candidate evidence is insufficient "
            "for a conclusive comparison."
        ),
    }
    confidence = {
        "MATCHED": Confidence.CONFIRMED,
        "PARTIALLY_MATCHED": Confidence.LIKELY,
        NO_MATCH: Confidence.LIKELY,
        INSUFFICIENT: Confidence.UNKNOWN,
    }[outcome]

    missing = [
        "Python identity, runnability, safety, compatibility, and health were not tested."
    ]
    if discovery.issues:
        missing.append("Discovery reported source limitations; its inventory may be incomplete.")
    if any(item.method == INSUFFICIENT for item in comparisons):
        missing.append("At least one candidate could not be conclusively compared.")
    if any(
        issue.code == "metadata_conflict"
        for item in comparisons
        for issue in item.issues
    ):
        missing.append("Source metadata conflicts remain unresolved.")

    finding = Finding(
        code="comparison." + outcome.casefold(),
        confidence=confidence,
        summary=summaries[outcome],
        evidence=(
            f"Target file status: {target.status}.",
            f"Compared discovery candidates: {len(comparisons)}.",
            "Match confidence describes a path relationship, not interpreter health.",
        ),
        missing_information=tuple(missing),
        next_steps=(
            "Review target, candidate provenance, and issues before choosing an interpreter.",
            "Check that the selected IDE or project interpreter path is the intended path.",
            "Investigate stale registrations or access restrictions manually; no repair was run.",
        ),
    )
    return ComparisonReport(
        target=target,
        outcome=outcome,
        comparisons=comparisons,
        discovery_issues=tuple(sorted(set(discovery.issues), key=_issue_key)),
        findings=(finding,),
    )


def compare_interpreter(path: str, project: str | None = None) -> ComparisonReport:
    """Observe the explicit target and reuse the existing M2 discovery engine.

    Invalid target syntax produces an evidence report without starting discovery.
    Missing or inaccessible but syntactically valid targets still get discovery.
    An invalid project for a valid target retains M2's structured input error.
    """
    target = observe_target(path)
    if target.status == "INVALID":
        discovery = DiscoveryReport(
            (),
            (
                DiscoveryIssue(
                    "discovery_not_run",
                    "comparison",
                    "Discovery was not run because target path syntax is invalid.",
                ),
            ),
        )
    else:
        discovery = discover_environments(project)
    return compare_evidence(target, discovery)
