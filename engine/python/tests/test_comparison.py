"""M3 behavior tests using inert files and mocked discovery."""

import json
import os
import stat
import tempfile
import unittest
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from pydoctor.comparison import compare_evidence, compare_interpreter
from pydoctor.discovery_models import (
    CandidateHint,
    DiscoveryIssue,
    DiscoveryReport,
    SourceEvidence,
)
from pydoctor.discovery_normalization import merge_candidates
from pydoctor.interpreter_target import observe_target


def hint(path, source="path", **kwargs):
    return CandidateHint(path, SourceEvidence(source, str(path)), **kwargs)


class ComparisonTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def file(self, relative="python.exe"):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Inert non-Python fixture; never execute.", encoding="utf-8")
        path.chmod(0o600)
        return path

    def discovery(self, *hints):
        return merge_candidates(tuple(hints))

    def test_exact_path_is_matched_but_health_is_not_verified(self):
        path = self.file()
        result = compare_evidence(
            observe_target(str(path)),
            self.discovery(hint(str(path))),
        )
        self.assertEqual(result.outcome, "MATCHED")
        self.assertEqual(result.comparisons[0].method, "EXACT_NORMALIZED_PATH")
        self.assertEqual(result.target.status, "REGULAR_FILE")
        self.assertEqual(result.target.interpreter_verification, "NOT_VERIFIED")
        self.assertIn(
            "interpreter_not_verified",
            {issue.code for issue in result.target.issues},
        )
        self.assertTrue(result.findings[0].missing_information)
        self.assertEqual(result.findings[0].commands, ())

    def test_windows_case_and_slashes_match_lexically(self):
        first = r"C:\Project\.venv\Scripts\python.exe"
        second = "c:/PROJECT/.venv/Scripts/PYTHON.EXE"
        with patch(
            "pydoctor.discovery_normalization.os.stat",
            side_effect=FileNotFoundError,
        ):
            discovery = self.discovery(hint(first))
            target = observe_target(second)
        result = compare_evidence(target, discovery)
        self.assertEqual(result.comparisons[0].method, "EXACT_NORMALIZED_PATH")
        self.assertEqual(result.outcome, "PARTIALLY_MATCHED")
        self.assertEqual(
            result.target.normalized_path,
            r"c:\project\.venv\scripts\python.exe",
        )

    def test_real_hardlink_identity_where_supported(self):
        first = self.file()
        second = self.root / "linked.exe"
        try:
            os.link(first, second)
        except OSError as exc:
            self.skipTest(f"Hardlinks unavailable: {exc}")
        discovery = self.discovery(hint(str(first)))
        result = compare_evidence(observe_target(str(second)), discovery)
        self.assertEqual(result.outcome, "MATCHED")
        self.assertEqual(result.comparisons[0].method, "SAME_FILE_IDENTITY")

    def test_deduplicated_original_path_is_still_an_exact_match(self):
        first = self.file()
        second = self.root / "linked.exe"
        try:
            os.link(first, second)
        except OSError as exc:
            self.skipTest(f"Hardlinks unavailable: {exc}")
        discovery = self.discovery(
            hint(str(first), "registry"),
            hint(str(second), "project"),
        )
        self.assertEqual(len(discovery.candidates), 1)
        result = compare_evidence(observe_target(str(second)), discovery)
        self.assertEqual(result.comparisons[0].method, "EXACT_NORMALIZED_PATH")
        self.assertEqual(result.comparisons[0].sources, ("project", "registry"))

    def test_distinct_regular_files_are_not_matched_by_basename(self):
        first = self.file("first/python.exe")
        second = self.file("second/python.exe")
        result = compare_evidence(
            observe_target(str(first)),
            self.discovery(hint(str(second), version="3.12")),
        )
        self.assertEqual(result.outcome, "NO_MATCH")
        self.assertEqual(result.comparisons[0].method, "NO_MATCH")

    def test_permission_failure_is_insufficient_not_a_false_mismatch(self):
        first = self.file("first/python.exe")
        second = self.file("second/python.exe")
        target = observe_target(str(first))
        discovery = self.discovery(hint(str(second)))
        with patch("pydoctor.comparison.os.stat", side_effect=PermissionError):
            result = compare_evidence(target, discovery)
        self.assertEqual(result.outcome, "INSUFFICIENT_EVIDENCE")
        self.assertIn(
            "identity_unavailable",
            {issue.code for issue in result.comparisons[0].issues},
        )

    def test_unsupported_identity_check_is_insufficient(self):
        first = self.file("first/python.exe")
        second = self.file("second/python.exe")
        target = observe_target(str(first))
        discovery = self.discovery(hint(str(second)))
        with patch("pydoctor.comparison.os.stat", side_effect=NotImplementedError):
            result = compare_evidence(target, discovery)
        self.assertEqual(result.comparisons[0].method, "INSUFFICIENT_EVIDENCE")

    def test_zero_inode_cannot_create_a_same_file_match(self):
        first = self.file("first/python.exe")
        second = self.file("second/python.exe")
        target = observe_target(str(first))
        discovery = self.discovery(hint(str(second)))
        info = SimpleNamespace(st_mode=stat.S_IFREG, st_ino=0, st_dev=1)
        with patch("pydoctor.comparison.os.stat", return_value=info):
            result = compare_evidence(target, discovery)
        self.assertEqual(result.outcome, "INSUFFICIENT_EVIDENCE")

    def test_target_without_identity_can_still_match_exact_path(self):
        path = self.file()
        target = replace(observe_target(str(path)), file_identity=None)
        result = compare_evidence(target, self.discovery(hint(str(path))))
        self.assertEqual(result.outcome, "MATCHED")
        self.assertEqual(result.comparisons[0].method, "EXACT_NORMALIZED_PATH")

    def test_empty_target_is_invalid_and_does_not_start_discovery(self):
        with patch("pydoctor.comparison.discover_environments") as discover:
            result = compare_interpreter("")
        discover.assert_not_called()
        self.assertEqual(result.target.status, "INVALID")
        self.assertEqual(result.outcome, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result.discovery_issues[0].code, "discovery_not_run")

    def test_invalid_paths(self):
        paths = (
            "\x00",
            " ",
            r"C:python.exe",
            r"\Python\python.exe",
            r"C:\Python\bad?.exe",
            r"C:\Python\python.exe:stream",
            r"C:\Python\NUL",
            r"\\.\C:\Python\python.exe",
        )
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(observe_target(path).status, "INVALID")

    def test_relative_target_is_not_resolved_against_cwd(self):
        target = observe_target("project/python.exe")
        self.assertEqual(target.status, "INVALID")
        self.assertIsNone(target.normalized_path)

    def test_nonexistent_target_without_correspondence_is_insufficient(self):
        path = self.root / "missing.exe"
        result = compare_evidence(observe_target(str(path)), DiscoveryReport(()))
        self.assertEqual(result.target.status, "MISSING")
        self.assertFalse(result.target.exists)
        self.assertEqual(result.outcome, "INSUFFICIENT_EVIDENCE")

    def test_missing_target_with_registration_is_partial(self):
        path = str(self.root / "missing.exe")
        result = compare_evidence(
            observe_target(path),
            self.discovery(hint(path, "registry")),
        )
        self.assertEqual(result.outcome, "PARTIALLY_MATCHED")
        self.assertEqual(result.comparisons[0].method, "EXACT_NORMALIZED_PATH")

    def test_directory_target_is_not_an_interpreter_match(self):
        result = compare_evidence(
            observe_target(str(self.root)),
            self.discovery(hint(str(self.root))),
        )
        self.assertEqual(result.target.status, "DIRECTORY")
        self.assertEqual(result.outcome, "INSUFFICIENT_EVIDENCE")

    def test_target_permission_failure_keeps_unknown_status(self):
        with patch("pydoctor.interpreter_target.os.stat", side_effect=PermissionError):
            target = observe_target(str(self.root / "python.exe"))
        self.assertEqual(target.status, "INACCESSIBLE")
        self.assertIsNone(target.exists)

    def test_target_stat_not_implemented_is_handled(self):
        with patch(
            "pydoctor.interpreter_target.os.stat",
            side_effect=NotImplementedError,
        ):
            target = observe_target(str(self.root / "python.exe"))
        self.assertEqual(target.status, "INACCESSIBLE")

    def test_exact_inaccessible_target_is_only_partial(self):
        path = str(self.root / "python.exe")
        with patch("pydoctor.interpreter_target.os.stat", side_effect=PermissionError):
            target = observe_target(path)
            discovery = self.discovery(hint(path))
        result = compare_evidence(target, discovery)
        self.assertEqual(result.outcome, "PARTIALLY_MATCHED")

    def test_windowsapps_alias_is_never_confirmed_as_an_interpreter_match(self):
        path = self.file("Microsoft/WindowsApps/python.exe")
        result = compare_evidence(
            observe_target(str(path)),
            self.discovery(hint(str(path))),
        )
        self.assertTrue(result.target.is_windowsapps_alias)
        self.assertIsNone(result.target.file_identity)
        self.assertEqual(result.outcome, "PARTIALLY_MATCHED")
        self.assertEqual(result.comparisons[0].method, "POSSIBLE")
        self.assertEqual(result.comparisons[0].confidence, "LIKELY")

    def test_candidate_without_executable_cannot_match_by_prefix(self):
        path = self.file()
        discovery = self.discovery(
            hint(None, "registry", prefix=str(path.parent), version="3.12")
        )
        result = compare_evidence(observe_target(str(path)), discovery)
        self.assertEqual(result.outcome, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(result.comparisons[0].compared_paths, ())
        self.assertEqual(result.comparisons[0].method, "INSUFFICIENT_EVIDENCE")

    def test_metadata_conflict_is_preserved_without_erasing_path_match(self):
        path = self.file()
        discovery = self.discovery(
            hint(str(path), "registry", version="3.11"),
            hint(str(path), "path", version="3.12"),
        )
        result = compare_evidence(observe_target(str(path)), discovery)
        self.assertEqual(result.outcome, "MATCHED")
        comparison = result.comparisons[0]
        self.assertEqual(comparison.sources, ("path", "registry"))
        self.assertIn("metadata_conflict", {issue.code for issue in comparison.issues})
        self.assertEqual(
            {dict(e.metadata)["observed_version"] for e in comparison.evidence},
            {"3.11", "3.12"},
        )
        self.assertTrue(
            any("conflicts" in text for text in result.findings[0].missing_information)
        )

    def test_empty_discovery_is_insufficient_even_when_target_exists(self):
        result = compare_evidence(
            observe_target(str(self.file())),
            DiscoveryReport(()),
        )
        self.assertEqual(result.outcome, "INSUFFICIENT_EVIDENCE")

    def test_discovery_issues_survive_a_successful_path_match(self):
        path = self.file()
        discovered = self.discovery(hint(str(path)))
        issue = DiscoveryIssue("launcher_missing", "python_launcher", "Fixture.")
        result = compare_evidence(
            observe_target(str(path)),
            replace(discovered, issues=(issue,)),
        )
        self.assertEqual(result.outcome, "MATCHED")
        self.assertEqual(result.discovery_issues, (issue,))
        self.assertTrue(
            any("incomplete" in text for text in result.findings[0].missing_information)
        )

    def test_json_and_report_models_are_immutable(self):
        path = self.file()
        result = compare_evidence(
            observe_target(str(path)),
            self.discovery(hint(str(path))),
        )
        data = json.loads(json.dumps(result.to_dict()))
        self.assertEqual(data["schema_version"], "1.2")
        self.assertEqual(data["scope"], "intended_interpreter_comparison")
        self.assertEqual(data["target"]["interpreter_verification"], "NOT_VERIFIED")
        with self.assertRaises(FrozenInstanceError):
            result.outcome = "NO_MATCH"
        independent = result.to_dict()
        independent["target"]["status"] = "INVALID"
        self.assertEqual(result.target.status, "REGULAR_FILE")

    def test_ordering_is_deterministic(self):
        target_path = self.file("target/python.exe")
        first = self.file("a/python.exe")
        second = self.file("z/python.exe")
        discovered = self.discovery(hint(str(second)), hint(str(first)))
        target = observe_target(str(target_path))
        one = compare_evidence(target, discovered)
        two = compare_evidence(
            target,
            replace(discovered, candidates=tuple(reversed(discovered.candidates))),
        )
        self.assertEqual(one.to_dict(), two.to_dict())

    def test_orchestration_reuses_discovery_and_passes_project(self):
        path = self.file()
        discovered = self.discovery(hint(str(path), "project"))
        with (
            patch(
                "pydoctor.comparison.discover_environments",
                return_value=discovered,
            ) as discover,
            patch("subprocess.run") as run,
        ):
            result = compare_interpreter(str(path), str(self.root))
        discover.assert_called_once_with(str(self.root))
        run.assert_not_called()
        self.assertEqual(result.outcome, "MATCHED")

    def test_no_match_does_not_claim_global_discovery_completeness(self):
        first = self.file("target/python.exe")
        second = self.file("other/python.exe")
        result = compare_evidence(
            observe_target(str(first)),
            self.discovery(hint(str(second))),
        )
        self.assertEqual(result.outcome, "NO_MATCH")
        self.assertIn("not proof", result.findings[0].summary)


if __name__ == "__main__":
    unittest.main()
