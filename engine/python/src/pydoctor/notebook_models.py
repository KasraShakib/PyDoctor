"""Immutable evidence records for read-only notebook and kernel diagnostics."""

from dataclasses import asdict, dataclass
from typing import Any

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.models import SeverityFinding


@dataclass(frozen=True)
class KernelSpec:
    """One observed Jupyter kernelspec, never a guarantee that it launches."""

    name: str
    display_name: str | None
    language: str | None
    argv: tuple[str, ...]
    resource_dir: str
    interpreter: str | None
    interpreter_exists: bool | None
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class NotebookObservation:
    """Metadata read from one notebook file without executing any cell."""

    path: str
    valid: bool
    kernel_name: str | None = None
    kernel_display_name: str | None = None
    language: str | None = None
    language_version: str | None = None
    nbformat: str | None = None
    issues: tuple[DiscoveryIssue, ...] = ()


@dataclass(frozen=True)
class NotebookReport:
    """Schema 1.4 notebook evidence, not a kernel launch or health result."""

    target: str
    target_kind: str
    kernels: tuple[KernelSpec, ...]
    notebooks: tuple[NotebookObservation, ...]
    findings: tuple[SeverityFinding, ...]
    issues: tuple[DiscoveryIssue, ...] = ()
    schema_version: str = "1.4"
    scope: str = "notebook_diagnostics"

    def to_dict(self) -> dict[str, Any]:
        """Return an independent JSON-compatible report structure."""
        return asdict(self)
