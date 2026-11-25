"""Immutable unified environment report models for the desktop layer."""

from dataclasses import asdict, dataclass
from typing import Any

from pydoctor.comparison_models import ComparisonReport, TargetObservation
from pydoctor.discovery_models import DiscoveryIssue, DiscoveryReport
from pydoctor.models import SeverityFinding
from pydoctor.notebook_models import NotebookReport
from pydoctor.package_models import PackageReport


@dataclass(frozen=True)
class EnvironmentSummary:
    """Compact counts and the highest observed severity."""

    comparison_outcome: str
    distributions: int
    missing_dependencies: int
    version_conflicts: int
    notebooks: int
    kernels: int
    severity: str


@dataclass(frozen=True)
class EnvironmentReport:
    """Schema 1.7 aggregate; nested reports retain their own schemas."""

    interpreter: str
    project: str | None
    target: TargetObservation
    summary: EnvironmentSummary
    discovery: DiscoveryReport
    comparison: ComparisonReport
    packages: PackageReport
    notebooks: NotebookReport | None
    findings: tuple[SeverityFinding, ...]
    issues: tuple[DiscoveryIssue, ...] = ()
    schema_version: str = "1.7"
    scope: str = "environment_report"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible report structure."""
        return asdict(self)
