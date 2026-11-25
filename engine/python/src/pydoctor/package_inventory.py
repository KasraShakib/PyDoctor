"""Derive site-packages locations and enumerate distribution metadata read-only."""

import os
import re
import stat
from dataclasses import dataclass

from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.discovery_normalization import normalized_path
from pydoctor.package_metadata import read_distribution
from pydoctor.package_models import PackageDistribution, SitePackagesRoot

MAX_SITE_PACKAGES_ROOTS = 16
MAX_DISTRIBUTIONS = 4096
MAX_PYVENV_BYTES = 64 * 1024
_PYTHON_VERSION_RE = re.compile(r"^\d+\.\d+(?:\.\d+)?")


@dataclass(frozen=True)
class Inventory:
    """Bounded metadata inventory for one interpreter prefix."""

    prefix: str | None
    python_version: str | None
    python_version_source: str | None
    roots: tuple[SitePackagesRoot, ...]
    distributions: tuple[PackageDistribution, ...]
    issues: tuple[DiscoveryIssue, ...]


def interpreter_prefix(executable: str) -> str:
    """Derive the environment prefix from ``<prefix>\\Scripts\\python.exe``.

    No interpreter is executed. This is the conventional venv layout only; an
    unusual layout simply yields site-packages candidates that are not found.
    """
    directory = os.path.dirname(os.path.abspath(executable))
    if os.path.basename(directory).casefold() in {"scripts", "bin"}:
        return os.path.dirname(directory)
    return directory


def read_pyvenv_cfg(prefix: str) -> dict[str, str]:
    """Read ``pyvenv.cfg`` key/value pairs without following ``home``."""
    path = os.path.join(prefix, "pyvenv.cfg")
    try:
        with open(path, "rb") as handle:
            text = handle.read(MAX_PYVENV_BYTES).decode("utf-8", errors="replace")
    except (OSError, ValueError):
        return {}
    values: dict[str, str] = {}
    for line in text.splitlines():
        key, separator, value = line.partition("=")
        if separator:
            values[key.strip().lower()] = value.strip()
    return values


def _python_version_from_cfg(config: dict[str, str]) -> str | None:
    for key in ("version", "version_info"):
        value = config.get(key)
        if not value:
            continue
        match = _PYTHON_VERSION_RE.match(value)
        if match:
            return match.group(0)
    return None


def _python_version_from_layout(prefix: str) -> str | None:
    lib = os.path.join(prefix, "lib")
    try:
        with os.scandir(lib) as entries:
            for entry in sorted(entries, key=lambda item: item.name.casefold()):
                match = re.fullmatch(r"python(\d+\.\d+)", entry.name)
                if match and entry.is_dir():
                    return match.group(1)
    except (OSError, ValueError):
        return None
    return None


def site_packages_candidates(prefix: str) -> tuple[str, ...]:
    """Return bounded conventional site-packages locations for a prefix."""
    candidates = [os.path.join(prefix, "Lib", "site-packages")]
    lib = os.path.join(prefix, "lib")
    try:
        with os.scandir(lib) as entries:
            for entry in sorted(entries, key=lambda item: item.name.casefold()):
                if re.fullmatch(r"python3(?:\.\d+)?", entry.name) and entry.is_dir():
                    candidates.append(os.path.join(lib, entry.name, "site-packages"))
    except (OSError, ValueError):
        pass
    unique: list[str] = []
    seen: set[str] = set()
    for candidate in candidates:
        key = normalized_path(candidate)
        if key not in seen:
            seen.add(key)
            unique.append(candidate)
    return tuple(unique[:MAX_SITE_PACKAGES_ROOTS])


def _enumerate_distributions(
    root: str,
    seen_locations: set[str],
    issues: list[DiscoveryIssue],
) -> tuple[tuple[PackageDistribution, ...], int]:
    found: list[PackageDistribution] = []
    try:
        with os.scandir(root) as entries:
            for index, entry in enumerate(entries):
                if index >= MAX_DISTRIBUTIONS:
                    issues.append(
                        DiscoveryIssue(
                            "package_entry_limit",
                            "package_inventory",
                            "Distribution enumeration limit reached.",
                            root,
                        )
                    )
                    break
                if not entry.name.casefold().endswith((".dist-info", ".egg-info")):
                    continue
                key = normalized_path(entry.path)
                if key in seen_locations:
                    continue
                seen_locations.add(key)
                found.append(read_distribution(entry.path))
    except (OSError, ValueError) as exc:
        issues.append(
            DiscoveryIssue(
                "site_packages_inaccessible",
                "package_inventory",
                type(exc).__name__,
                root,
            )
        )
    return tuple(found), len(found)


def discover_site_packages(prefix: str) -> tuple[
    tuple[SitePackagesRoot, ...],
    tuple[PackageDistribution, ...],
    tuple[DiscoveryIssue, ...],
]:
    """Observe candidate roots and read only recognized metadata directories."""
    roots: list[SitePackagesRoot] = []
    distributions: list[PackageDistribution] = []
    issues: list[DiscoveryIssue] = []
    seen_locations: set[str] = set()
    for candidate in site_packages_candidates(prefix):
        local: list[DiscoveryIssue] = []
        exists: bool | None = None
        is_directory: bool | None = None
        count = 0
        try:
            info = os.stat(candidate)
            exists = True
            is_directory = stat.S_ISDIR(info.st_mode)
            if is_directory:
                found, count = _enumerate_distributions(candidate, seen_locations, local)
                distributions.extend(found)
            else:
                local.append(
                    DiscoveryIssue(
                        "site_packages_not_directory",
                        "package_inventory",
                        "Site-packages candidate is not a directory.",
                        candidate,
                    )
                )
        except (FileNotFoundError, NotADirectoryError):
            exists, is_directory = False, False
        except (OSError, ValueError) as exc:
            local.append(
                DiscoveryIssue(
                    "site_packages_inaccessible",
                    "package_inventory",
                    type(exc).__name__,
                    candidate,
                )
            )
        roots.append(SitePackagesRoot(candidate, exists, is_directory, count, tuple(local)))
        issues.extend(local)
    return tuple(roots), tuple(distributions), tuple(issues)


def build_inventory(executable: str) -> Inventory:
    """Build a bounded, read-only inventory for the supplied interpreter path."""
    prefix = interpreter_prefix(executable)
    config = read_pyvenv_cfg(prefix)
    python_version = _python_version_from_cfg(config)
    source = "pyvenv.cfg" if python_version else None
    if python_version is None:
        python_version = _python_version_from_layout(prefix)
        source = "site-packages layout" if python_version else None
    roots, distributions, issues = discover_site_packages(prefix)
    ordered = tuple(
        sorted(
            distributions,
            key=lambda item: (
                item.normalized_name or "",
                item.name or "",
                normalized_path(item.location),
            ),
        )
    )
    return Inventory(
        prefix=prefix,
        python_version=python_version,
        python_version_source=source,
        roots=roots,
        distributions=ordered,
        issues=issues,
    )
