"""Observe an explicit interpreter path without opening or executing its contents."""

import ntpath
import os
import re
import stat

from pydoctor.comparison_models import TargetObservation
from pydoctor.discovery_models import DiscoveryIssue
from pydoctor.discovery_normalization import (
    absolute_path,
    normalized_path,
    windows_alias,
)

_RESERVED = re.compile(
    r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$",
    re.IGNORECASE,
)
_FORBIDDEN = re.compile(r'[<>:"|?*\x00-\x1f]')


def _validated_path(path: str) -> str:
    """Require an absolute, unambiguous path; never expand variables or cwd."""
    if not path or not path.strip() or any(ord(c) < 32 for c in path):
        raise ValueError("Target path is empty or contains control characters.")
    if not absolute_path(path):
        raise ValueError("Target path must be absolute; relative paths are not resolved.")

    normalized = normalized_path(path)
    is_windows = os.name == "nt" or bool(ntpath.splitdrive(path)[0]) or "\\" in path
    if is_windows:
        drive, tail = ntpath.splitdrive(normalized)
        if not drive or not tail.startswith("\\"):
            raise ValueError("Target is not an absolute Windows file path.")
        if drive.startswith("\\\\"):
            components = drive[2:].split("\\") + tail.split("\\")
        elif re.fullmatch(r"[a-z]:", drive, re.IGNORECASE):
            components = tail.split("\\")
        else:
            raise ValueError("Device namespace paths are not accepted.")
        for component in components:
            if not component:
                continue
            if (
                _FORBIDDEN.search(component)
                or component.endswith((".", " "))
                or _RESERVED.fullmatch(component)
            ):
                raise ValueError("Target contains an unsupported Windows path component.")
    return normalized


def observe_target(path: str) -> TargetObservation:
    """Collect metadata only; an existing regular file is not verified Python.

    Stat follows ordinary filesystem links. Identity uses the device/inode pair
    underlying Python's same-file comparison and is unavailable when inode is
    zero. This is a point-in-time observation, not a stable file handle.
    """
    try:
        normalized = _validated_path(path)
    except ValueError as exc:
        return TargetObservation(
            path,
            None,
            "INVALID",
            None,
            None,
            False,
            issues=(
                DiscoveryIssue(
                    "invalid_target_path",
                    "comparison",
                    str(exc),
                    path,
                ),
            ),
        )

    alias = windows_alias(normalized)
    issues = []
    if alias:
        issues.append(
            DiscoveryIssue(
                "windowsapps_alias",
                "comparison",
                "WindowsApps path is alias evidence, not a verified interpreter.",
                path,
            )
        )

    identity = None
    try:
        info = os.stat(path)
        exists = True
        is_file = stat.S_ISREG(info.st_mode)
        if is_file:
            status = "REGULAR_FILE"
            issues.append(
                DiscoveryIssue(
                    "interpreter_not_verified",
                    "comparison",
                    "File existence does not verify Python identity, runnability, "
                    "safety, compatibility, or health.",
                    path,
                )
            )
            if info.st_ino and not alias:
                identity = (info.st_dev, info.st_ino)
            elif not alias:
                issues.append(
                    DiscoveryIssue(
                        "target_identity_unavailable",
                        "comparison",
                        "Filesystem did not supply a usable file identity.",
                        path,
                    )
                )
        elif stat.S_ISDIR(info.st_mode):
            status = "DIRECTORY"
            issues.append(
                DiscoveryIssue(
                    "target_not_file",
                    "comparison",
                    "Target is a directory, not a regular executable file.",
                    path,
                )
            )
        else:
            status = "OTHER"
            issues.append(
                DiscoveryIssue(
                    "target_not_file",
                    "comparison",
                    "Target is not a regular file.",
                    path,
                )
            )
    except (FileNotFoundError, NotADirectoryError):
        status, exists, is_file = "MISSING", False, False
        issues.append(
            DiscoveryIssue(
                "target_not_found",
                "comparison",
                "No target file was observed.",
                path,
            )
        )
    except (OSError, ValueError, NotImplementedError) as exc:
        status, exists, is_file = "INACCESSIBLE", None, None
        issues.append(
            DiscoveryIssue(
                "target_inaccessible",
                "comparison",
                f"Target metadata unavailable ({type(exc).__name__}).",
                path,
            )
        )

    return TargetObservation(
        supplied_path=path,
        normalized_path=normalized,
        status=status,
        exists=exists,
        is_file=is_file,
        is_windowsapps_alias=alias,
        file_identity=identity,
        issues=tuple(issues),
    )
