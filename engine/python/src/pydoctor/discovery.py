"""Read-only Windows Python environment discovery orchestration."""

import os
import struct
import sys
from collections.abc import Mapping

from pydoctor.discovery_models import (
    CandidateHint,
    DiscoveryIssue,
    DiscoveryReport,
    SourceEvidence,
    SourceResult,
)
from pydoctor.discovery_normalization import merge_candidates
from pydoctor.discovery_registry import discover_registry
from pydoctor.discovery_sources import (
    discover_active,
    discover_launcher,
    discover_path,
    discover_project,
    validate_project,
)
from pydoctor.environment import collect_runtime


def discover_current() -> SourceResult:
    """Include the engine interpreter as observed evidence, without a new process."""
    runtime = collect_runtime()
    return SourceResult((CandidateHint(
        runtime.executable, SourceEvidence("current_interpreter", "sys.executable", (
            ("runtime_version", runtime.version), ("base_prefix", runtime.base_prefix),
        )), prefix=runtime.prefix,
        version=".".join(str(part) for part in sys.version_info[:3]),
        implementation=runtime.implementation, architecture=f"{struct.calcsize('P') * 8}bit",
    ),))


def discover_environments(project: str | None = None, *,
                          environ: Mapping[str, str] | None = None,
                          platform_name: str | None = None) -> DiscoveryReport:
    """Collect independent sources and merge evidence, never probing candidates.

    Non-Windows calls report the engine only and an unsupported-platform issue.
    Source failures do not suppress other sources. Unexpected programming errors
    are not silently converted into a successful discovery report.
    """
    if project is not None:
        project = validate_project(project)
    environment = dict(os.environ if environ is None else environ)
    platform_name = sys.platform if platform_name is None else platform_name
    sources = [("current_interpreter", discover_current)]
    issues = []
    if platform_name != "win32":
        issues.append(DiscoveryIssue("unsupported_platform", "discovery",
                                     "Windows discovery is unavailable on this platform."))
    else:
        sources.extend((
            ("registry", discover_registry),
            ("python_launcher", lambda: discover_launcher(environment)),
            ("path", lambda: discover_path(environment)),
            ("active_environment", lambda: discover_active(environment)),
        ))
        if project is not None:
            sources.append(("project", lambda: discover_project(project)))
    hints = []
    for source, collector in sources:
        try:
            result = collector()
        except (OSError, ValueError) as exc:
            issues.append(DiscoveryIssue("source_failed", source, type(exc).__name__))
            continue
        hints.extend(result.hints)
        issues.extend(result.issues)
    return merge_candidates(tuple(hints), tuple(issues))
