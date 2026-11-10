"""Deterministic merging, orchestration and CLI contract coverage."""

import io
import json
import os
import stat
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydoctor.__main__ import main
from pydoctor.discovery import discover_environments
from pydoctor.discovery_models import CandidateHint, SourceEvidence, SourceResult
from pydoctor.discovery_normalization import absolute_path, merge_candidates, normalized_path


def hint(path, source="path", **kwargs):
    return CandidateHint(path, SourceEvidence(source, str(path)), **kwargs)


class NormalizationTests(unittest.TestCase):
    def test_windows_paths_case_separators_dot_components(self):
        paths = (r"C:\Python\python.exe", "c:/python/./python.exe",
                 r"C:\Python\child\..\PYTHON.EXE", r"\\?\C:\Python\python.exe")
        self.assertEqual(len({normalized_path(p) for p in paths}), 1)
        with patch("pydoctor.discovery_normalization.os.stat", side_effect=FileNotFoundError):
            report = merge_candidates(tuple(hint(p) for p in paths))
        self.assertEqual(len(report.candidates), 1)
        self.assertEqual(len(report.candidates[0].evidence), 4)

    def test_unc_and_extended_unc(self):
        self.assertEqual(normalized_path(r"\\server\Share\python.exe"),
                         normalized_path(r"\\?\UNC\SERVER\share\python.exe"))
        self.assertTrue(absolute_path(r"\\server\share\python.exe"))
        for path in ("", "relative", r"C:python.exe", r"\python.exe", "a\x00b"):
            self.assertFalse(absolute_path(path))

    def test_duplicate_provenance_and_metadata_conflicts(self):
        with patch("pydoctor.discovery_normalization.os.stat", side_effect=FileNotFoundError):
            report = merge_candidates((hint(r"C:\Python\python.exe", version="3.12"),
                                       hint(r"c:\python\python.exe", "registry", version="3.11")))
        candidate = report.candidates[0]
        self.assertEqual(candidate.sources, ("path", "registry"))
        self.assertIsNone(candidate.version)
        self.assertIn("metadata_conflict", {i.code for i in candidate.issues})
        self.assertEqual({dict(e.metadata)["observed_version"] for e in candidate.evidence},
                         {"3.11", "3.12"})
        self.assertEqual(json.loads(json.dumps(report.to_dict()))["schema_version"], "1.1")

    def test_unknown_executables_are_not_merged_by_prefix(self):
        result = merge_candidates((hint(None, "registry", prefix=r"C:\Python"),
                                   hint(None, "project", prefix=r"C:\Python")))
        self.assertEqual(len(result.candidates), 2)
        self.assertTrue(all(c.confidence == "UNKNOWN" for c in result.candidates))

    def test_permission_denied_is_unknown_not_missing(self):
        with patch("pydoctor.discovery_normalization.os.stat", side_effect=PermissionError):
            candidate = merge_candidates((hint(r"C:\Python\python.exe"),)).candidates[0]
        self.assertIsNone(candidate.exists)
        self.assertIn("path_inaccessible", {i.code for i in candidate.issues})
        self.assertNotEqual(candidate.confidence, "CONFIRMED")

    def test_existing_directory_is_not_executable_file(self):
        with tempfile.TemporaryDirectory() as directory:
            candidate = merge_candidates((hint(directory),)).candidates[0]
        self.assertTrue(candidate.exists)
        self.assertFalse(candidate.is_file)
        self.assertNotEqual(candidate.confidence, "CONFIRMED")

    def test_file_identity_merges_aliases_and_preserves_paths(self):
        info = SimpleNamespace(st_mode=stat.S_IFREG, st_ino=42, st_dev=1)
        with patch("pydoctor.discovery_normalization.os.stat", return_value=info):
            candidate = merge_candidates((hint(r"C:\real\python.exe"),
                                          hint(r"D:\junction\python.exe", "project"))).candidates[0]
        self.assertEqual(candidate.sources, ("path", "project"))
        self.assertEqual(len(candidate.evidence), 2)
        self.assertEqual(candidate.confidence, "CONFIRMED")

    def test_actual_hardlink_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "python.exe", Path(directory) / "alias.exe"
            first.touch()
            try:
                os.link(first, second)
            except OSError as exc:
                self.skipTest(f"Hardlinks unavailable: {exc}")
            self.assertEqual(len(merge_candidates((hint(str(first)), hint(str(second)))).candidates), 1)

    def test_zero_inode_does_not_merge_unrelated_files(self):
        info = SimpleNamespace(st_mode=stat.S_IFREG, st_ino=0, st_dev=1)
        with patch("pydoctor.discovery_normalization.os.stat", return_value=info):
            report = merge_candidates((hint(r"C:\one.exe"), hint(r"C:\two.exe")))
        self.assertEqual(len(report.candidates), 2)

    def test_stable_order_regardless_of_source_order(self):
        hints = (hint(r"C:\z.exe"), hint(r"C:\a.exe", "registry"), hint(None))
        with patch("pydoctor.discovery_normalization.os.stat", side_effect=FileNotFoundError):
            self.assertEqual(merge_candidates(hints), merge_candidates(tuple(reversed(hints))))


class DiscoveryTests(unittest.TestCase):
    def test_non_windows_is_explicit_and_never_invokes_launcher(self):
        with patch("pydoctor.discovery.discover_launcher") as launcher:
            report = discover_environments(environ={}, platform_name="linux")
        launcher.assert_not_called()
        self.assertIn("unsupported_platform", {i.code for i in report.issues})
        self.assertIn("current_interpreter", report.candidates[0].sources)

    def test_sources_merge_and_failure_does_not_block_other_sources(self):
        source = SourceResult((hint(r"C:\Python\python.exe", "registry"),))
        with (patch("pydoctor.discovery.discover_registry", return_value=source),
              patch("pydoctor.discovery.discover_launcher", side_effect=PermissionError),
              patch("pydoctor.discovery.discover_path", return_value=SourceResult()),
              patch("pydoctor.discovery.discover_active", return_value=SourceResult()),
              patch("pydoctor.discovery.discover_project") as project):
            report = discover_environments(environ={}, platform_name="win32")
        project.assert_not_called()
        self.assertIn("source_failed", {i.code for i in report.issues})
        self.assertTrue(any("registry" in c.sources for c in report.candidates))
        self.assertTrue(any("current_interpreter" in c.sources for c in report.candidates))

    def test_only_explicit_project_is_inspected(self):
        with tempfile.TemporaryDirectory() as directory:
            with (patch("pydoctor.discovery.discover_registry", return_value=SourceResult()),
                  patch("pydoctor.discovery.discover_launcher", return_value=SourceResult()),
                  patch("pydoctor.discovery.discover_path", return_value=SourceResult()),
                  patch("pydoctor.discovery.discover_active", return_value=SourceResult()),
                  patch("pydoctor.discovery.discover_project", return_value=SourceResult()) as project):
                discover_environments(directory, environ={}, platform_name="win32")
            project.assert_called_once_with(os.path.abspath(directory))

    def test_cli_m1_and_discovery_are_separate_json_contracts(self):
        for args, schema in (([], "1.0"), (["--discover"], "1.1"),
                             (["--discover", "--pretty"], "1.1")):
            stdout, stderr = io.StringIO(), io.StringIO()
            with (redirect_stdout(stdout), redirect_stderr(stderr),
                  patch("pydoctor.__main__.discover_environments",
                        return_value=merge_candidates(()))):
                status = main(args)
            self.assertEqual(status, 0)
            self.assertEqual(stderr.getvalue(), "")
            report = json.loads(stdout.getvalue())
            self.assertEqual(report["schema_version"], schema)
            self.assertEqual("candidates" in report, bool(args))

    def test_cli_invalid_project_is_structured_stderr(self):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["--discover", "--project", "\x00"])
        self.assertEqual(status, 2)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(json.loads(stderr.getvalue())["error"]["code"], "invalid_project_directory")

    def test_cli_project_requires_discovery(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            main(["--project", "."])
        self.assertEqual(error.exception.code, 2)
