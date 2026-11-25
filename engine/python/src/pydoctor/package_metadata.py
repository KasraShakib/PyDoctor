"""Read distribution metadata without importing packages or running pip."""

import json
import os
from email.parser import Parser
from email.policy import compat32

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.package_models import PackageDistribution
from pydoctor.requirements import normalize_name

MAX_METADATA_BYTES = 2 * 1024 * 1024


def _read_text(path: str, source: str) -> tuple[str | None, list[DiscoveryIssue]]:
    issues: list[DiscoveryIssue] = []
    try:
        with open(path, "rb") as handle:
            data = handle.read(MAX_METADATA_BYTES + 1)
    except (OSError, ValueError) as exc:
        issues.append(
            DiscoveryIssue(
                "metadata_unreadable",
                source,
                f"Metadata could not be read ({type(exc).__name__}).",
                path,
            )
        )
        return None, issues
    if len(data) > MAX_METADATA_BYTES:
        issues.append(
            DiscoveryIssue(
                "metadata_truncated",
                source,
                "Metadata exceeded the read limit and was truncated.",
                path,
            )
        )
        data = data[:MAX_METADATA_BYTES]
    text = data.decode("utf-8", errors="replace")
    if text.startswith("\ufeff"):
        text = text[1:]
    return text, issues


def _read_small_text(path: str) -> str | None:
    try:
        with open(path, "rb") as handle:
            return handle.read(4096).decode("utf-8", errors="replace").strip()
    except (OSError, ValueError):
        return None


def _metadata_kind(location: str) -> str:
    lowered = location.casefold()
    if lowered.endswith(".dist-info"):
        return "dist-info"
    if lowered.endswith(".egg-info"):
        return "egg-info"
    return "unknown"


def _metadata_path(location: str, kind: str) -> str | None:
    if os.path.isdir(location):
        if kind == "dist-info":
            return os.path.join(location, "METADATA")
        if kind == "egg-info":
            return os.path.join(location, "PKG-INFO")
        return None
    if kind == "egg-info" and os.path.isfile(location):
        return location
    return None


def _direct_url(location: str, issues: list[DiscoveryIssue]) -> str | None:
    path = os.path.join(location, "direct_url.json")
    if not os.path.isfile(path):
        return None
    text, read_issues = _read_text(path, "package_metadata")
    issues.extend(read_issues)
    if text is None:
        return None
    try:
        payload = json.loads(text)
    except ValueError:
        issues.append(
            DiscoveryIssue(
                "direct_url_invalid",
                "package_metadata",
                "direct_url.json is not valid JSON.",
                path,
            )
        )
        return None
    if isinstance(payload, dict) and isinstance(payload.get("url"), str):
        return payload["url"]
    return None


def read_distribution(location: str) -> PackageDistribution:
    """Parse one ``.dist-info`` or ``.egg-info`` location conservatively."""
    kind = _metadata_kind(location)
    issues: list[DiscoveryIssue] = []
    path = _metadata_path(location, kind)
    if path is None or not os.path.isfile(path):
        issues.append(
            DiscoveryIssue(
                "metadata_file_missing",
                "package_metadata",
                "Expected metadata file was not found.",
                location,
            )
        )
        return PackageDistribution(
            name=None,
            normalized_name=None,
            version=None,
            metadata_kind=kind,
            location=location,
            metadata_path=path,
            issues=tuple(issues),
        )

    text, read_issues = _read_text(path, "package_metadata")
    issues.extend(read_issues)
    if text is None:
        return PackageDistribution(
            name=None,
            normalized_name=None,
            version=None,
            metadata_kind=kind,
            location=location,
            metadata_path=path,
            issues=tuple(issues),
        )

    message = Parser(policy=compat32).parsestr(text)
    if not message.items():
        issues.append(
            DiscoveryIssue(
                "metadata_unreadable",
                "package_metadata",
                "Metadata contained no recognizable headers.",
                path,
            )
        )

    name = message.get("Name")
    version = message.get("Version")
    if not name:
        issues.append(
            DiscoveryIssue(
                "metadata_missing_name",
                "package_metadata",
                "Distribution metadata has no Name field.",
                path,
            )
        )
    if not version:
        issues.append(
            DiscoveryIssue(
                "metadata_missing_version",
                "package_metadata",
                "Distribution metadata has no Version field.",
                path,
            )
        )

    installer = None
    if kind == "dist-info":
        installer = _read_small_text(os.path.join(location, "INSTALLER"))

    return PackageDistribution(
        name=name,
        normalized_name=normalize_name(name) if name else None,
        version=version,
        metadata_kind=kind,
        location=location,
        metadata_path=path,
        summary=message.get("Summary"),
        requires_dist=tuple(message.get_all("Requires-Dist") or ()),
        requires_python=message.get("Requires-Python"),
        provides_extra=tuple(message.get_all("Provides-Extra") or ()),
        installer=installer,
        direct_url=_direct_url(location, issues) if kind == "dist-info" else None,
        issues=tuple(issues),
    )
