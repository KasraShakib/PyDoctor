"""Bounded local sources; only the legacy launcher's listing may be executed."""

import ntpath
import os
import re
import stat
import subprocess
from collections.abc import Mapping

from pydoctor.discovery_models import CandidateHint, DiscoveryIssue, SourceEvidence, SourceResult
from pydoctor.discovery_normalization import absolute_path, normalized_path, windows_alias

MAX_PATH_DIRECTORIES = 128
MAX_DIRECTORY_ENTRIES = 4096
MAX_LAUNCHER_LINES = 1024
LAUNCHER_TIMEOUT = 3
PYTHON_NAME = re.compile(r"python(?:3(?:\.\d+){0,2}|\d+\.\d+(?:\.\d+)?)?(?:t)?\.exe", re.I)
LAUNCHER_LINE = re.compile(
    r'^\s*-(?:V:)?(?P<tag>[^\s]+)\s+(?P<default>\*\s*)?'
    r'(?P<path>(?:[A-Za-z]:[\\/]|\\\\).+?\.exe)\s*$', re.I,
)


def parse_launcher_output(output: str, launcher: str) -> SourceResult:
    """Parse legacy and -V tags; spaces in absolute Windows paths are preserved."""
    hints, issues = [], []
    lines = output.splitlines()
    for line in lines[:MAX_LAUNCHER_LINES]:
        if not line.strip():
            continue
        match = LAUNCHER_LINE.fullmatch(line)
        if not match:
            issues.append(DiscoveryIssue("launcher_unexpected_output", "python_launcher",
                                         "Unrecognized listing line: " + line[:300], launcher))
            continue
        path, tag = match["path"], match["tag"]
        # PythonCore tags are version metadata, not directory-name inference.
        version_tag = tag.removeprefix("PythonCore/")
        version_match = re.fullmatch(r"(\d+\.\d+(?:\.\d+)?)(?:-(32|64))?", version_tag)
        metadata = (("tag", tag), ("default", str(bool(match["default"])).lower()),
                    ("launcher", launcher))
        hints.append(CandidateHint(
            path, SourceEvidence("python_launcher", launcher, metadata),
            version=version_match[1] if version_match else None,
            architecture=(version_match[2] + "bit") if version_match and version_match[2] else None,
        ))
    if len(lines) > MAX_LAUNCHER_LINES:
        issues.append(DiscoveryIssue("launcher_output_limit", "python_launcher",
                                     "Listing line limit reached.", launcher))
    if not hints:
        issues.append(DiscoveryIssue("launcher_no_candidates", "python_launcher",
                                     "No interpretable executable entries.", launcher))
    return SourceResult(tuple(hints), tuple(issues))


def resolve_launcher(environ: Mapping[str, str]) -> str | None:
    """Use conventional installed legacy-launcher paths, never cwd or WindowsApps.

    This is a bounded installed-location policy, not a signature verification.
    Environment variables belong to the trusted invoking process. Arbitrary
    PATH py.exe programs are deliberately not executed.
    """
    locations = (("LOCALAPPDATA", ("Programs", "Python", "Launcher", "py.exe")),
                 ("SystemRoot", ("py.exe",)),
                 ("ProgramFiles", ("Python Launcher", "py.exe")),
                 ("ProgramFiles(x86)", ("Python Launcher", "py.exe")))
    for variable, suffix in locations:
        base = environ.get(variable)
        if not base or not absolute_path(base):
            continue
        path = os.path.join(base, *suffix)
        try:
            if not windows_alias(path) and stat.S_ISREG(os.stat(path).st_mode):
                return path
        except (OSError, ValueError):
            continue
    return None


def discover_launcher(environ: Mapping[str, str]) -> SourceResult:
    """Run only the resolved installed launcher's offline -0p listing."""
    launcher = resolve_launcher(environ)
    if launcher is None:
        return SourceResult(issues=(DiscoveryIssue(
            "launcher_missing", "python_launcher", "No legacy launcher at trusted installed locations."),))
    try:
        completed = subprocess.run(
            [launcher, "-0p"], shell=False, capture_output=True, text=True,
            errors="replace", timeout=LAUNCHER_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return SourceResult(issues=(DiscoveryIssue(
            "launcher_timeout", "python_launcher", "Launcher listing timed out.", launcher),))
    except (OSError, ValueError) as exc:
        return SourceResult(issues=(DiscoveryIssue(
            "launcher_execution_failed", "python_launcher", type(exc).__name__, launcher),))
    parsed = parse_launcher_output(completed.stdout, launcher)
    issues = list(parsed.issues)
    if completed.returncode:
        issues.append(DiscoveryIssue("launcher_nonzero_exit", "python_launcher",
                                     f"Launcher exited with status {completed.returncode}.", launcher))
    if completed.stderr.strip():
        issues.append(DiscoveryIssue("launcher_stderr", "python_launcher",
                                     completed.stderr[:1000], launcher))
    return SourceResult(parsed.hints, tuple(issues))


def discover_path(environ: Mapping[str, str]) -> SourceResult:
    """Inspect only direct PATH entries, with directory and entry count limits."""
    hints, issues = [], []
    seen = set()
    for raw in environ.get("PATH", "").split(";"):
        directory = raw.strip().strip('"')
        if not directory:
            continue  # Empty PATH entries must not imply scanning cwd.
        if not absolute_path(directory):
            issues.append(DiscoveryIssue("path_entry_invalid", "path",
                                         "Relative or malformed PATH entry was skipped.", directory))
            continue
        key = normalized_path(directory)
        if key in seen:
            continue
        if len(seen) == MAX_PATH_DIRECTORIES:
            issues.append(DiscoveryIssue("path_directory_limit", "path",
                                         "PATH directory limit reached."))
            break
        seen.add(key)
        names = []
        try:
            with os.scandir(directory) as entries:
                for index, entry in enumerate(entries):
                    if index == MAX_DIRECTORY_ENTRIES:
                        issues.append(DiscoveryIssue("path_entry_limit", "path",
                                                     "Directory entry limit reached.", directory))
                        break
                    if PYTHON_NAME.fullmatch(entry.name):
                        names.append(entry.name)
        except (OSError, ValueError) as exc:
            issues.append(DiscoveryIssue("path_directory_inaccessible", "path",
                                         type(exc).__name__, directory))
        for name in sorted(names, key=lambda s: (s.casefold(), s)):
            hints.append(CandidateHint(os.path.join(directory, name),
                                      SourceEvidence("path", directory)))
    return SourceResult(tuple(hints), tuple(issues))


def discover_active(environ: Mapping[str, str]) -> SourceResult:
    """Preserve activation hints even when their expected executables are missing."""
    hints = []
    for variable, suffix in (("VIRTUAL_ENV", ("Scripts", "python.exe")),
                             ("CONDA_PREFIX", ("python.exe",))):
        prefix = environ.get(variable)
        if not prefix:
            continue
        local = ()
        if not absolute_path(prefix):
            local = (DiscoveryIssue("environment_hint_invalid", "active_environment",
                                    "Environment hint must be absolute.", prefix),)
        hints.append(CandidateHint(
            os.path.join(prefix, *suffix),
            SourceEvidence("active_environment", variable, (("variable", variable),
                                                           ("prefix", prefix))),
            prefix=prefix, issues=local,
        ))
    return SourceResult(tuple(hints))


class DiscoveryInputError(ValueError):
    """Invalid project scope; handled as a structured CLI input error."""


def validate_project(project: str) -> str:
    """Validate an explicitly selected directory without scanning its tree."""
    try:
        if not project or "\x00" in project:
            raise ValueError("Empty or NUL-containing project path.")
        path = os.path.abspath(project)
        if not stat.S_ISDIR(os.stat(path).st_mode):
            raise ValueError("Project path is not a directory.")
        return path
    except (OSError, ValueError) as exc:
        raise DiscoveryInputError(f"Invalid project directory ({type(exc).__name__}).") from exc


def discover_project(project: str) -> SourceResult:
    """Inspect the selected root and three named direct children only.

    Named environment roots may be junctions, but no subtrees are enumerated.
    A selected root is a venv hint only when pyvenv.cfg exists or Scripts/python.exe
    exists. Existing named child directories remain evidence even if incomplete.
    """
    project = validate_project(project)
    hints, issues = [], []
    for name in ("", ".venv", "venv", "env"):
        root = os.path.join(project, name) if name else project
        try:
            info = os.stat(root)
        except FileNotFoundError:
            continue
        except (OSError, ValueError) as exc:
            issues.append(DiscoveryIssue("project_environment_inaccessible", "project",
                                         type(exc).__name__, root))
            if name:
                hints.append(CandidateHint(os.path.join(root, "Scripts", "python.exe"),
                                          SourceEvidence("project", root), prefix=root))
            continue
        if not stat.S_ISDIR(info.st_mode):
            if name:
                issues.append(DiscoveryIssue("project_environment_not_directory", "project",
                                             "Named environment root is not a directory.", root))
            continue
        executable = os.path.join(root, "Scripts", "python.exe")
        if not name:
            found = False
            for marker in (os.path.join(root, "pyvenv.cfg"), executable):
                try:
                    found = stat.S_ISREG(os.stat(marker).st_mode) or found
                except (FileNotFoundError, NotADirectoryError):
                    pass
                except (OSError, ValueError) as exc:
                    issues.append(DiscoveryIssue("project_environment_inaccessible", "project",
                                                 type(exc).__name__, marker))
                    # Preserve the root as an uncertain hint instead of discarding it.
                    found = True
            if not found:
                continue
        hints.append(CandidateHint(executable, SourceEvidence("project", root), prefix=root))
    return SourceResult(tuple(hints), tuple(issues))
