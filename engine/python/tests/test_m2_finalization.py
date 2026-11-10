"""M2 finalization coverage; fixture files must never be executed."""

import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydoctor.comparison import compare_interpreter
from pydoctor.discovery_models import CandidateHint, SourceEvidence
from pydoctor.discovery_normalization import absolute_path, merge_candidates
from pydoctor.models import Confidence


def hint(path, source="path"):
    return CandidateHint(path, SourceEvidence(source, path))


class M2FinalizationTests(unittest.TestCase):
    def test_inert_python_exe_is_only_a_confirmed_regular_file(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "python.exe"
            executable.write_text("This is not Python or a PE executable.", encoding="utf-8")
            executable.chmod(0o600)
            with patch("subprocess.run") as run:
                candidate = merge_candidates((hint(str(executable)),)).candidates[0]
            run.assert_not_called()
            self.assertTrue(candidate.exists)
            self.assertTrue(candidate.is_file)
            self.assertEqual(candidate.confidence, Confidence.CONFIRMED)
            self.assertIsNone(candidate.version)
            self.assertIn(
                "interpreter_not_verified",
                {issue.code for issue in candidate.issues},
            )

    def test_alias_identity_does_not_absorb_a_concrete_file(self):
        info = SimpleNamespace(st_mode=stat.S_IFREG, st_ino=42, st_dev=1)
        with patch("pydoctor.discovery_normalization.os.stat", return_value=info):
            report = merge_candidates(
                (
                    hint(r"C:\Python\python.exe"),
                    hint(r"C:\Users\User\Microsoft\WindowsApps\python.exe"),
                )
            )
        self.assertEqual(len(report.candidates), 2)
        alias = next(c for c in report.candidates if "WindowsApps" in c.executable)
        concrete = next(c for c in report.candidates if c is not alias)
        self.assertNotEqual(alias.confidence, Confidence.CONFIRMED)
        self.assertEqual(concrete.confidence, Confidence.CONFIRMED)

    def test_directories_with_equal_mock_identity_are_not_merged(self):
        info = SimpleNamespace(st_mode=stat.S_IFDIR, st_ino=42, st_dev=1)
        with patch("pydoctor.discovery_normalization.os.stat", return_value=info):
            report = merge_candidates(
                (hint(r"C:\First\python.exe"), hint(r"C:\Second\python.exe"))
            )
        self.assertEqual(len(report.candidates), 2)
        self.assertTrue(all(c.is_file is False for c in report.candidates))

    @unittest.skipUnless(os.name == "nt", "Windows path semantics required")
    def test_windows_root_relative_paths_are_not_absolute(self):
        self.assertFalse(absolute_path("/Python/python.exe"))
        self.assertFalse(absolute_path(r"\Python\python.exe"))
        self.assertFalse(absolute_path(r"C:Python\python.exe"))
        self.assertTrue(absolute_path(r"C:\Python\python.exe"))


class OptionalWindowsJunctionTests(unittest.TestCase):
    @unittest.skipUnless(
        os.name == "nt" and bool(os.environ.get("PYD_JUNCTION_ROOT")),
        "Requires an explicitly prepared temporary Windows junction fixture",
    )
    def test_real_junction_merges_and_matches_without_execution(self):
        root = Path(os.environ["PYD_JUNCTION_ROOT"])
        real = root / "real" / "python.exe"
        junction = root / "junction"
        alias = junction / "python.exe"
        self.assertTrue(real.is_file())
        self.assertTrue(alias.is_file())
        self.assertTrue(os.path.isjunction(junction))

        report = merge_candidates(
            (hint(str(real), "path"), hint(str(alias), "project"))
        )
        self.assertEqual(len(report.candidates), 1)
        self.assertEqual(report.candidates[0].sources, ("path", "project"))

        discovered = merge_candidates((hint(str(real), "path"),))
        with (
            patch("pydoctor.comparison.discover_environments", return_value=discovered),
            patch("subprocess.run") as run,
        ):
            comparison = compare_interpreter(str(alias))
        run.assert_not_called()
        self.assertEqual(comparison.outcome, "MATCHED")
        self.assertEqual(comparison.comparisons[0].method, "SAME_FILE_IDENTITY")
        self.assertEqual(comparison.target.interpreter_verification, "NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
