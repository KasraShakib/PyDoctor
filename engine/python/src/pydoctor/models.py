"""Versioned, JSON-serializable results for read-only runtime diagnostics."""

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Confidence(str, Enum):
    """Strength of the evidence supporting a finding, not its severity."""

    CONFIRMED = "CONFIRMED"
    LIKELY = "LIKELY"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class RuntimeEvidence:
    """Facts observed inside the interpreter running the engine."""

    executable: str
    version: str
    implementation: str
    prefix: str
    base_prefix: str
    sys_path: tuple[str, ...]
    virtual_env: str | None


@dataclass(frozen=True)
class Finding:
    """An evidence-backed observation with bounded investigation guidance."""

    code: str
    confidence: Confidence
    summary: str
    evidence: tuple[str, ...]
    missing_information: tuple[str, ...] = ()
    hypotheses: tuple[str, ...] = ()
    next_steps: tuple[str, ...] = ()
    commands: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True)
class DiagnosticReport:
    """Version 1.0 contract for a single current-interpreter observation."""

    runtime: RuntimeEvidence
    findings: tuple[Finding, ...]
    schema_version: str = "1.0"
    scope: str = "current_interpreter"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent structure accepted by the JSON encoder."""
        return asdict(self)
