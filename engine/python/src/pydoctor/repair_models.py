"""Immutable repair plans; planning is separate from execution."""

from dataclasses import asdict, dataclass
from typing import Any

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.models import SeverityFinding


@dataclass(frozen=True)
class RepairStep:
    """One proposed action with an exact argv and a verification description."""

    step_id: str
    title: str
    rationale: str
    risk: str
    requires_confirmation: bool
    argv: tuple[str, ...] | None
    verification: str
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepairExecution:
    """Result of an explicitly approved, allowlisted step."""

    step_id: str
    executed: bool
    returncode: int | None = None
    stdout: str | None = None
    stderr: str | None = None
    verified: bool | None = None
    notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class RepairPlan:
    """Schema 1.6 dry-run plan; no command is executed while building it."""

    source_report: str
    source_scope: str | None
    steps: tuple[RepairStep, ...]
    findings: tuple[SeverityFinding, ...]
    issues: tuple[DiscoveryIssue, ...] = ()
    dry_run: bool = True
    schema_version: str = "1.6"
    scope: str = "repair_plan"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible report structure."""
        return asdict(self)
