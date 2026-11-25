"""Immutable evidence records for read-only package and dependency diagnostics."""

from dataclasses import asdict, dataclass
from typing import Any

from pydoctor.comparison_models import TargetObservation
from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.models import Confidence, SeverityFinding


@dataclass(frozen=True)
class PackageDistribution:
    """Metadata observed for one installed distribution, never an import result."""

    name: str | None
    normalized_name: str | None
    version: str | None
    metadata_kind: str
    location: str
    metadata_path: str | None
    summary: str | None = None
    requires_dist: tuple[str, ...] = ()
    requires_python: str | None = None
    provides_extra: tuple[str, ...] = ()
    installer: str | None = None
    direct_url: str | None = None
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class DependencyStatus:
    """One requirement or Requires-Python clause and its bounded evaluation."""

    kind: str
    requirement: str
    package: str | None
    normalized_name: str | None
    status: str
    confidence: Confidence
    explanation: str
    installed_version: str | None = None
    specifier: str | None = None
    marker: str | None = None
    evidence: tuple[str, ...] = ()
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class SitePackagesRoot:
    """One observed site-packages candidate and its bounded contents summary."""

    path: str
    exists: bool | None
    is_directory: bool | None
    distribution_count: int
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class PackageReport:
    """Schema 1.3 report; metadata evidence is not an import or health check."""

    target: TargetObservation
    interpreter_prefix: str | None
    python_version: str | None
    python_version_source: str | None
    site_packages: tuple[SitePackagesRoot, ...]
    distributions: tuple[PackageDistribution, ...]
    dependencies: tuple[DependencyStatus, ...]
    findings: tuple[SeverityFinding, ...]
    issues: tuple[DiscoveryIssue, ...] = ()
    schema_version: str = "1.3"
    scope: str = "package_diagnostics"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible report structure."""
        return asdict(self)
