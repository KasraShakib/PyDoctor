"""Normalize discovery evidence without executing candidate interpreters."""

import ntpath
import os
import stat
from collections import defaultdict

from pydoctor.discovery_models import (
    CandidateHint,
    DiscoveryIssue,
    DiscoveryReport,
    PythonCandidate,
    SourceEvidence,
)
from pydoctor.models import Confidence


def normalized_path(path: str) -> str:
    """Apply Windows rules to Windows paths and native rules to host fixtures."""
    if os.name == "nt" or ntpath.splitdrive(path)[0] or "\\" in path:
        if path[:8].casefold() == "\\\\?\\unc\\":
            path = "\\\\" + path[8:]
        elif path.startswith("\\\\?\\"):
            path = path[4:]
        return ntpath.normcase(ntpath.normpath(path))
    return os.path.normcase(os.path.normpath(path))


def absolute_path(path: str) -> bool:
    """Reject empty, NUL-containing, and drive-relative Windows paths."""
    if not path or "\x00" in path:
        return False
    if os.name == "nt" or ntpath.splitdrive(path)[0] or "\\" in path:
        drive, tail = ntpath.splitdrive(path)
        return bool(drive) and (
            tail.startswith(("\\", "/")) or drive.startswith("\\\\")
        )
    return os.path.isabs(path)


def windows_alias(path: str) -> bool:
    """Treat WindowsApps locations conservatively as alias evidence."""
    parts = ntpath.normpath(path).replace("/", "\\").casefold().split("\\")
    return "windowsapps" in parts


def _issue_key(issue: DiscoveryIssue) -> tuple[str, str, str, str]:
    return issue.source, issue.code, issue.location or "", issue.message


def merge_candidates(
    hints: tuple[CandidateHint, ...],
    issues: tuple[DiscoveryIssue, ...] = (),
) -> DiscoveryReport:
    """Merge lexical paths and observable regular-file identities.

    Filesystem observations are snapshots, not health checks. Identity follows
    symlinks and junctions, but directories and WindowsApps aliases do not supply
    identity merge keys. Missing paths retain lexical evidence.
    """
    ordered = sorted(
        hints,
        key=lambda h: (
            normalized_path(h.executable or ""),
            h.evidence.source,
            h.evidence.location,
            repr(h),
        ),
    )
    parents = list(range(len(ordered)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    keys: dict[tuple, int] = {}
    observations = []
    for index, hint in enumerate(ordered):
        path = hint.executable
        local = list(hint.issues)
        exists = is_file = None
        path_keys = []
        if path is None:
            local.append(
                DiscoveryIssue(
                    "executable_missing",
                    hint.evidence.source,
                    "No executable path was established.",
                    hint.evidence.location,
                )
            )
        elif not absolute_path(path):
            local.append(
                DiscoveryIssue(
                    "invalid_executable_path",
                    hint.evidence.source,
                    "Executable must be an absolute path without NULs.",
                    path,
                )
            )
        else:
            alias = windows_alias(path)
            path_keys.append(("path", normalized_path(path)))
            try:
                info = os.stat(path)
                exists, is_file = True, stat.S_ISREG(info.st_mode)
                if is_file:
                    local.append(
                        DiscoveryIssue(
                            "interpreter_not_verified",
                            "normalization",
                            "A regular file was observed; Python identity, "
                            "runnability, safety, and health were not verified.",
                            path,
                        )
                    )
                    if not alias:
                        if info.st_ino:
                            path_keys.append(
                                ("identity", info.st_dev, info.st_ino)
                            )
                        else:
                            local.append(
                                DiscoveryIssue(
                                    "identity_unavailable",
                                    "normalization",
                                    "Filesystem did not supply a file identity.",
                                    path,
                                )
                            )
                else:
                    local.append(
                        DiscoveryIssue(
                            "executable_not_file",
                            "normalization",
                            "Executable location is not a regular file.",
                            path,
                        )
                    )
            except (FileNotFoundError, NotADirectoryError):
                exists, is_file = False, False
                local.append(
                    DiscoveryIssue(
                        "executable_not_found",
                        "normalization",
                        "Executable is missing; identity could not be checked.",
                        path,
                    )
                )
            except (OSError, ValueError, NotImplementedError) as exc:
                local.append(
                    DiscoveryIssue(
                        "path_inaccessible",
                        "normalization",
                        f"Filesystem identity unavailable ({type(exc).__name__}).",
                        path,
                    )
                )
            if alias:
                local.append(
                    DiscoveryIssue(
                        "windowsapps_alias",
                        "normalization",
                        "WindowsApps execution alias is not installation proof.",
                        path,
                    )
                )

        for key in path_keys:
            if key in keys:
                parents[root(index)] = root(keys[key])
            else:
                keys[key] = index
        observations.append((exists, is_file, local))

    groups: dict[int, list[int]] = defaultdict(list)
    for index in range(len(ordered)):
        groups[root(index)].append(index)

    candidates = []
    for indices in groups.values():
        group = [ordered[i] for i in indices]
        local = [item for i in indices for item in observations[i][2]]
        values = {}
        for field in ("prefix", "version", "implementation", "architecture"):
            raw = sorted(
                {getattr(h, field) for h in group if getattr(h, field) is not None}
            )
            distinct = {
                normalized_path(v) if field == "prefix" else v for v in raw
            }
            values[field] = raw[0] if len(distinct) == 1 else None
            if len(distinct) > 1:
                local.append(
                    DiscoveryIssue(
                        "metadata_conflict",
                        "normalization",
                        f"Conflicting {field}: {raw!r}.",
                        group[0].executable,
                    )
                )

        statuses = {observations[i][:2] for i in indices}
        if len(statuses) == 1:
            exists, is_file = next(iter(statuses))
        else:
            exists = is_file = None
            local.append(
                DiscoveryIssue(
                    "path_status_conflict",
                    "normalization",
                    "Aliases gave inconsistent filesystem observations.",
                    group[0].executable,
                )
            )

        alias = any(windows_alias(h.executable or "") for h in group)
        if is_file is True and not alias:
            confidence = Confidence.CONFIRMED
        elif (
            any(h.executable and absolute_path(h.executable) for h in group)
            and exists is not False
        ):
            confidence = Confidence.LIKELY
        else:
            confidence = Confidence.UNKNOWN

        evidence_records = set()
        for hint in group:
            metadata = dict(hint.evidence.metadata)
            for field in (
                "executable",
                "prefix",
                "version",
                "implementation",
                "architecture",
            ):
                value = getattr(hint, field)
                if value is not None:
                    metadata["observed_" + field] = value
            evidence_records.add(
                SourceEvidence(
                    hint.evidence.source,
                    hint.evidence.location,
                    tuple(sorted(metadata.items())),
                )
            )
        evidence = tuple(
            sorted(
                evidence_records,
                key=lambda e: (e.source, e.location, e.metadata),
            )
        )
        candidates.append(
            PythonCandidate(
                executable=group[0].executable,
                **values,
                sources=tuple(sorted({e.source for e in evidence})),
                evidence=evidence,
                exists=exists,
                is_file=is_file,
                confidence=confidence,
                issues=tuple(sorted(set(local), key=_issue_key)),
            )
        )

    candidates.sort(
        key=lambda c: (normalized_path(c.executable or ""), repr(c.evidence))
    )
    return DiscoveryReport(
        tuple(candidates),
        tuple(sorted(set(issues), key=_issue_key)),
    )
