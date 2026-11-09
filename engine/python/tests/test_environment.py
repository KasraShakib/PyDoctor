"""Deterministic evidence and confidence tests without third-party packages."""

import json
import os
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from pydoctor.environment import collect_runtime, diagnose_current_environment, diagnose_runtime
from pydoctor.models import Confidence, RuntimeEvidence


class RuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name) / "base"
        self.environment = Path(self.directory.name) / "environment"
        self.base.mkdir()
        self.environment.mkdir()
        self.runtime = RuntimeEvidence(
            executable=str(self.base / "python.exe"),
            version="3.12.9 (test fixture)",
            implementation="CPython",
            prefix=str(self.base),
            base_prefix=str(self.base),
            sys_path=("", str(self.base / "Lib")),
            virtual_env=None,
        )

    def test_collects_actual_runtime_facts(self) -> None:
        with patch.dict(os.environ, {"VIRTUAL_ENV": str(self.environment)}):
            runtime = collect_runtime()
        self.assertEqual(runtime.executable, sys.executable)
        self.assertEqual(runtime.version, sys.version)
        self.assertEqual(runtime.prefix, sys.prefix)
        self.assertEqual(runtime.base_prefix, sys.base_prefix)
        self.assertEqual(runtime.sys_path, tuple(sys.path))
        self.assertEqual(runtime.virtual_env, str(self.environment))
        self.assertTrue(runtime.implementation)

    def test_absent_marker_is_not_an_activation_failure(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            runtime = collect_runtime()
        self.assertIsNone(runtime.virtual_env)
        self.assertEqual(len(diagnose_runtime(runtime).findings), 2)

    def test_base_prefix_observation_is_confirmed(self) -> None:
        finding = diagnose_runtime(self.runtime).findings[1]
        self.assertEqual(finding.code, "environment.prefix_base")
        self.assertIs(finding.confidence, Confidence.CONFIRMED)
        self.assertTrue(finding.evidence)
        self.assertIn("Conda", " ".join(finding.next_steps))

    def test_prefix_separation_does_not_require_activation(self) -> None:
        runtime = replace(self.runtime, prefix=str(self.environment))
        finding = diagnose_runtime(runtime).findings[1]
        self.assertEqual(finding.code, "environment.prefix_isolated")
        self.assertIs(finding.confidence, Confidence.CONFIRMED)

    def test_matching_marker_reports_directory_agreement_only(self) -> None:
        runtime = replace(self.runtime, virtual_env=str(self.base))
        finding = diagnose_runtime(runtime).findings[-1]
        self.assertEqual(finding.code, "environment.activation_hint_matches")
        self.assertIs(finding.confidence, Confidence.CONFIRMED)
        self.assertIn("does not establish", finding.next_steps[0])

    def test_directory_alias_is_not_a_mismatch(self) -> None:
        runtime = replace(self.runtime, virtual_env=str(self.base) + os.sep + ".")
        finding = diagnose_runtime(runtime).findings[-1]
        self.assertEqual(finding.code, "environment.activation_hint_matches")

    def test_different_existing_directories_are_only_likely(self) -> None:
        runtime = replace(self.runtime, virtual_env=str(self.environment))
        finding = diagnose_runtime(runtime).findings[-1]
        self.assertEqual(finding.code, "environment.activation_hint_mismatch")
        self.assertIs(finding.confidence, Confidence.LIKELY)
        self.assertTrue(finding.missing_information)
        self.assertTrue(finding.hypotheses)
        self.assertTrue(finding.next_steps)
        self.assertEqual(finding.commands[0][0], runtime.executable)

    def test_removed_marker_is_unknown_not_confirmed_mismatch(self) -> None:
        runtime = replace(self.runtime, virtual_env=str(self.base / "removed"))
        finding = diagnose_runtime(runtime).findings[-1]
        self.assertEqual(finding.code, "environment.activation_hint_unverified")
        self.assertIs(finding.confidence, Confidence.UNKNOWN)
        self.assertTrue(finding.evidence)
        self.assertTrue(finding.missing_information)
        self.assertTrue(finding.hypotheses)
        self.assertTrue(finding.next_steps)
        self.assertTrue(finding.commands)

    def test_relative_marker_is_unknown_without_filesystem_comparison(self) -> None:
        runtime = replace(self.runtime, virtual_env="relative-environment")
        with patch("pydoctor.environment.os.path.samefile") as samefile:
            finding = diagnose_runtime(runtime).findings[-1]
        samefile.assert_not_called()
        self.assertIs(finding.confidence, Confidence.UNKNOWN)

    def test_permission_error_is_unknown(self) -> None:
        runtime = replace(self.runtime, virtual_env=str(self.environment))
        with patch("pydoctor.environment.os.path.samefile", side_effect=PermissionError):
            finding = diagnose_runtime(runtime).findings[-1]
        self.assertIs(finding.confidence, Confidence.UNKNOWN)
        self.assertIn("PermissionError", finding.missing_information[0])

    def test_invalid_path_is_unknown(self) -> None:
        runtime = replace(self.runtime, virtual_env=str(self.environment))
        with patch("pydoctor.environment.os.path.samefile", side_effect=ValueError):
            finding = diagnose_runtime(runtime).findings[-1]
        self.assertIs(finding.confidence, Confidence.UNKNOWN)

    def test_empty_marker_is_not_an_error(self) -> None:
        report = diagnose_runtime(replace(self.runtime, virtual_env=""))
        self.assertEqual(len(report.findings), 2)
        self.assertEqual(report.runtime.virtual_env, "")

    def test_report_contract_serializes_unicode_and_confidence(self) -> None:
        runtime = replace(self.runtime, executable="C:/Users/کاربر/python.exe")
        report = diagnose_runtime(runtime)
        data = json.loads(json.dumps(report.to_dict(), ensure_ascii=True))
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["scope"], "current_interpreter")
        self.assertEqual(data["runtime"]["executable"], runtime.executable)
        self.assertEqual(data["runtime"]["sys_path"], list(runtime.sys_path))
        self.assertEqual(data["findings"][0]["confidence"], "CONFIRMED")

    def test_diagnosis_does_not_modify_runtime_or_environment(self) -> None:
        before_environment = dict(os.environ)
        before_path = list(sys.path)
        before_prefixes = (sys.prefix, sys.base_prefix)
        report = diagnose_current_environment()
        self.assertEqual(dict(os.environ), before_environment)
        self.assertEqual(sys.path, before_path)
        self.assertEqual((sys.prefix, sys.base_prefix), before_prefixes)
        self.assertEqual(report.runtime.executable, sys.executable)
