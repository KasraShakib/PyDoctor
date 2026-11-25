"""Immutable evidence records for traceback explanation."""

from dataclasses import asdict, dataclass
from typing import Any

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.models import SeverityFinding


@dataclass(frozen=True)
class TracebackFrame:
    """One parsed traceback frame; no source file is executed or imported."""

    path: str | None
    line: int | None
    function: str | None


@dataclass(frozen=True)
class ErrorReport:
    """Schema 1.5 explanation of a supplied traceback, not a code fix."""

    source: str
    exception_type: str | None
    message: str | None
    frames: tuple[TracebackFrame, ...]
    findings: tuple[SeverityFinding, ...]
    intended_interpreter: str | None = None
    issues: tuple[DiscoveryIssue, ...] = ()
    schema_version: str = "1.5"
    scope: str = "error_explanation"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible report structure."""
        return asdict(self)
