"""Local discovery source tests; no actual launcher or target process is run."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from pydoctor.discovery_normalization import merge_candidates
from pydoctor.discovery_sources import (
    DiscoveryInputError, discover_active, discover_launcher, discover_path,
    discover_project, parse_launcher_output, resolve_launcher,
)


def codes(result):
    return {issue.code for issue in result.issues}


class LauncherTests(unittest.TestCase):
    def test_modern_listing_spaces_and_default_marker(self):
        result = parse_launcher_output(
            "-V:3.12 * C:\\Program Files\\Python312\\python.exe\n"
            " -V:3.11-32 C:\\Other Python\\python.exe\n", r"C:\Windows\py.exe")
        self.assertEqual(len(result.hints), 2)
        self.assertEqual(result.hints[0].executable, r"C:\Program Files\Python312\python.exe")
        self.assertEqual(dict(result.hints[0].evidence.metadata)["default"], "true")
        self.assertEqual(result.hints[1].architecture, "32bit")
        self.assertFalse(result.issues)

    def test_legacy_and_company_tags(self):
        result = parse_launcher_output(
            " -3.9-64 * C:\\Python39\\python.exe\n"
            "-V:Vendor/custom \\\\server\\share\\python.exe\n"
            "-V:PythonCore/3.12 C:\\Python312\\python.exe", "launcher")
        self.assertEqual(len(result.hints), 3)
        self.assertEqual(result.hints[0].version, "3.9")
        self.assertIsNone(result.hints[1].version)
        self.assertEqual(result.hints[2].version, "3.12")

    def test_unexpected_and_unsafe_listing_lines(self):
        result = parse_launcher_output(
            "header\n-V:3.12 relative.exe\n-V:3.12 C:\\python.exe --do-stuff\n", "launcher")
        self.assertEqual(result.hints, ())
        self.assertIn("launcher_unexpected_output", codes(result))
        self.assertIn("launcher_no_candidates", codes(result))

    def test_listing_line_bound(self):
        with patch("pydoctor.discovery_sources.MAX_LAUNCHER_LINES", 1):
            result = parse_launcher_output("header\nheader", "launcher")
        self.assertIn("launcher_output_limit", codes(result))

    def test_missing_launcher_does_not_invoke_process(self):
        with patch("pydoctor.discovery_sources.subprocess.run") as run:
            result = discover_launcher({})
        run.assert_not_called()
        self.assertIn("launcher_missing", codes(result))

    def test_installed_launcher_resolution_ignores_path_and_cwd(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            executable = root / "Programs" / "Python" / "Launcher" / "py.exe"
            executable.parent.mkdir(parents=True)
            executable.touch()
            self.assertEqual(resolve_launcher({"LOCALAPPDATA": directory}), str(executable))
            self.assertIsNone(resolve_launcher({"PATH": str(executable.parent)}))
            self.assertIsNone(resolve_launcher({"LOCALAPPDATA": "relative"}))

    def test_listing_is_only_permitted_process(self):
        completed = subprocess.CompletedProcess([], 0, "-V:3.12 * C:\\Python\\python.exe", "")
        with (patch("pydoctor.discovery_sources.resolve_launcher", return_value=r"C:\Windows\py.exe"),
              patch("pydoctor.discovery_sources.subprocess.run", return_value=completed) as run):
            result = discover_launcher({})
        args, kwargs = run.call_args
        self.assertEqual(args[0], [r"C:\Windows\py.exe", "-0p"])
        self.assertIs(kwargs["shell"], False)
        self.assertTrue(kwargs["capture_output"])
        self.assertLessEqual(kwargs["timeout"], 5)
        self.assertEqual(len(result.hints), 1)
        run.assert_called_once()

    def test_launcher_timeout(self):
        with (patch("pydoctor.discovery_sources.resolve_launcher", return_value=r"C:\Windows\py.exe"),
              patch("pydoctor.discovery_sources.subprocess.run",
                    side_effect=subprocess.TimeoutExpired("py", 3))):
            result = discover_launcher({})
        self.assertIn("launcher_timeout", codes(result))

    def test_nonzero_exit_keeps_evidence_and_stderr(self):
        completed = subprocess.CompletedProcess([], 9, "-3.12 C:\\Python\\python.exe", "problem")
        with (patch("pydoctor.discovery_sources.resolve_launcher", return_value=r"C:\Windows\py.exe"),
              patch("pydoctor.discovery_sources.subprocess.run", return_value=completed)):
            result = discover_launcher({})
        self.assertIn("launcher_nonzero_exit", codes(result))
        self.assertIn("launcher_stderr", codes(result))
        self.assertEqual(len(result.hints), 1)

    def test_launcher_permission_error(self):
        with (patch("pydoctor.discovery_sources.resolve_launcher", return_value=r"C:\Windows\py.exe"),
              patch("pydoctor.discovery_sources.subprocess.run", side_effect=PermissionError)):
            self.assertIn("launcher_execution_failed", codes(discover_launcher({})))


class LocalSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def executable(self, relative):
        executable = self.root / relative
        executable.parent.mkdir(parents=True, exist_ok=True)
        executable.write_text("not an executable; must never be run", encoding="utf-8")
        return executable

    def test_path_executable_names_nonrecursive_no_version_guesses(self):
        for name in ("python.exe", "python3.exe", "python3.12.exe", "python3.13t.exe",
                     "pythonw.exe", "notpython.exe", "py.exe", "child/python.exe"):
            self.executable(name)
        result = discover_path({"PATH": str(self.root)})
        self.assertEqual({Path(h.executable).name for h in result.hints},
                         {"python.exe", "python3.exe", "python3.12.exe", "python3.13t.exe"})
        self.assertTrue(all(h.version is None for h in result.hints))

    def test_path_windowsapps_alias_distinct_from_concrete_file(self):
        alias = self.executable("Microsoft/WindowsApps/python.exe")
        result = discover_path({"PATH": str(alias.parent)})
        candidate = merge_candidates(result.hints).candidates[0]
        self.assertTrue(candidate.is_file)
        self.assertEqual(candidate.confidence, "LIKELY")
        self.assertIn("windowsapps_alias", {i.code for i in candidate.issues})

    def test_inaccessible_path_directory(self):
        with patch("pydoctor.discovery_sources.os.scandir", side_effect=PermissionError):
            result = discover_path({"PATH": str(self.root)})
        self.assertIn("path_directory_inaccessible", codes(result))

    def test_path_empty_relative_and_duplicates(self):
        self.executable("python.exe")
        result = discover_path({"PATH": f';relative;"{self.root}";{self.root};;'})
        self.assertEqual(len(result.hints), 1)
        self.assertIn("path_entry_invalid", codes(result))

    def test_path_directory_limit(self):
        with patch("pydoctor.discovery_sources.MAX_PATH_DIRECTORIES", 1):
            result = discover_path({"PATH": f"{self.root};{self.root / 'second'}"})
        self.assertIn("path_directory_limit", codes(result))

    def test_path_entry_limit(self):
        entry = Mock(name="entry")
        entry.name = "python.exe"
        context = Mock()
        context.__enter__ = Mock(return_value=iter([entry, entry]))
        context.__exit__ = Mock(return_value=False)
        with (patch("pydoctor.discovery_sources.MAX_DIRECTORY_ENTRIES", 1),
              patch("pydoctor.discovery_sources.os.scandir", return_value=context)):
            result = discover_path({"PATH": str(self.root)})
        self.assertIn("path_entry_limit", codes(result))

    def test_active_virtual_env(self):
        executable = self.executable("active/Scripts/python.exe")
        result = discover_active({"VIRTUAL_ENV": str(executable.parents[1])})
        candidate = merge_candidates(result.hints).candidates[0]
        self.assertEqual(candidate.executable, str(executable))
        self.assertTrue(candidate.is_file)
        self.assertIsNone(candidate.version)

    def test_active_conda_prefix(self):
        executable = self.executable("conda/python.exe")
        result = discover_active({"CONDA_PREFIX": str(executable.parent)})
        self.assertEqual(result.hints[0].executable, str(executable))
        self.assertEqual(dict(result.hints[0].evidence.metadata)["variable"], "CONDA_PREFIX")

    def test_stale_active_environment_hints(self):
        result = discover_active({"VIRTUAL_ENV": str(self.root / "gone"),
                                  "CONDA_PREFIX": str(self.root / "also-gone")})
        report = merge_candidates(result.hints)
        self.assertEqual(len(report.candidates), 2)
        self.assertTrue(all(c.exists is False for c in report.candidates))
        self.assertTrue(all(c.confidence == "UNKNOWN" for c in report.candidates))

    def test_relative_active_hint_is_unknown(self):
        result = discover_active({"VIRTUAL_ENV": "relative"})
        candidate = merge_candidates(result.hints).candidates[0]
        self.assertIsNone(candidate.exists)
        self.assertIn("environment_hint_invalid", {i.code for i in candidate.issues})

    def test_project_known_children_only(self):
        for name in (".venv", "venv", "env", "unrelated", "child/.venv"):
            self.executable(name + "/Scripts/python.exe")
        result = discover_project(str(self.root))
        self.assertEqual({Path(h.prefix).name for h in result.hints}, {".venv", "venv", "env"})

    def test_project_itself_is_venv_root(self):
        executable = self.executable("Scripts/python.exe")
        self.executable("pyvenv.cfg")
        result = discover_project(str(self.root))
        self.assertEqual(len(result.hints), 1)
        self.assertEqual(result.hints[0].executable, str(executable))

    def test_project_missing_environment_executable_preserved(self):
        (self.root / ".venv").mkdir()
        result = discover_project(str(self.root))
        candidate = merge_candidates(result.hints).candidates[0]
        self.assertFalse(candidate.exists)
        self.assertIn("executable_not_found", {i.code for i in candidate.issues})

    def test_project_root_config_with_missing_executable(self):
        self.executable("pyvenv.cfg")
        result = discover_project(str(self.root))
        self.assertEqual(len(result.hints), 1)
        self.assertFalse(merge_candidates(result.hints).candidates[0].exists)

    def test_invalid_project_directory(self):
        file = self.executable("file")
        for path in ("", "\x00", str(self.root / "absent"), str(file)):
            with self.subTest(path=path), self.assertRaises(DiscoveryInputError):
                discover_project(path)

    def test_permission_denied_project(self):
        with (patch("pydoctor.discovery_sources.os.stat", side_effect=PermissionError),
              self.assertRaises(DiscoveryInputError)):
            discover_project(str(self.root))

    def test_permission_denied_environment_root_keeps_hint(self):
        real_stat = os.stat

        def stat_fixture(path, *args, **kwargs):
            if Path(path) == self.root / ".venv":
                raise PermissionError("denied")
            return real_stat(path, *args, **kwargs)

        with patch("pydoctor.discovery_sources.os.stat", side_effect=stat_fixture):
            result = discover_project(str(self.root))
        self.assertEqual(len(result.hints), 1)
        self.assertIn("project_environment_inaccessible", codes(result))

    def test_named_environment_is_file(self):
        self.executable("venv")
        self.assertIn("project_environment_not_directory", codes(discover_project(str(self.root))))
