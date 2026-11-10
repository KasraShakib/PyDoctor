"""Immutable evidence records for read-only Python discovery (not health checks)."""

from dataclasses import asdict, dataclass
from typing import Any

from pydoctor.models import Confidence


@dataclass(frozen=True)
class DiscoveryIssue:
    """Stable source-scoped uncertainty, optionally identifying a location."""

    code: str
    source: str
    message: str
    location: str | None = None


@dataclass(frozen=True)
class SourceEvidence:
    """A single observation; conflicting metadata is retained across observations."""

    source: str
    location: str
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class CandidateHint:
    """Unverified source input, including registrations with no executable path."""

    executable: str | None
    evidence: SourceEvidence
    prefix: str | None = None
    version: str | None = None
    implementation: str | None = None
    architecture: str | None = None
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class SourceResult:
    """Independent results from one discovery source."""

    hints: tuple[CandidateHint, ...] = ()
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class PythonCandidate:
    """Merged evidence about a possible executable, never a runnable verdict."""

    executable: str | None
    prefix: str | None
    version: str | None
    implementation: str | None
    architecture: str | None
    sources: tuple[str, ...]
    evidence: tuple[SourceEvidence, ...]
    exists: bool | None
    is_file: bool | None
    confidence: Confidence
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class DiscoveryReport:
    """Independent schema 1.1 report; does not change the M1 schema."""

    candidates: tuple[PythonCandidate, ...]
    issues: tuple[DiscoveryIssue, ...] = ()
    schema_version: str = "1.1"
    scope: str = "python_discovery"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible structure."""
        return asdict(self)
