"""Immutable reports for intended-interpreter evidence comparison."""

from dataclasses import asdict, dataclass
from typing import Any

from pydoctor.discovery_models import DiscoveryIssue, SourceEvidence
from pydoctor.models import Confidence, Finding


@dataclass(frozen=True)
class TargetObservation:
    """Observable target metadata, never an interpreter-health verdict."""

    supplied_path: str
    normalized_path: str | None
    status: str
    exists: bool | None
    is_file: bool | None
    is_windowsapps_alias: bool
    file_identity: tuple[int, int] | None = None
    issues: tuple[DiscoveryIssue, ...] = ()
    interpreter_verification: str = "NOT_VERIFIED"


@dataclass(frozen=True)
class CandidateComparison:
    """One M2 candidate's relationship to the explicit target."""

    candidate_executable: str | None
    compared_paths: tuple[str, ...]
    method: str
    confidence: Confidence
    sources: tuple[str, ...]
    evidence: tuple[SourceEvidence, ...]
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class ComparisonReport:
    """Schema 1.2; discovery provenance is included without a second inventory."""

    target: TargetObservation
    outcome: str
    comparisons: tuple[CandidateComparison, ...]
    discovery_issues: tuple[DiscoveryIssue, ...]
    findings: tuple[Finding, ...]
    schema_version: str = "1.2"
    scope: str = "intended_interpreter_comparison"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible report structure."""
        return asdict(self)
