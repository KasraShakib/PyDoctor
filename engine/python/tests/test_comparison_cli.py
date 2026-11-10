"""CLI and source integration tests without real launcher execution."""

import io
import json
import subprocess
import tempfile
import unittest
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from pydoctor.__main__ import main
from pydoctor.comparison import compare_interpreter
from pydoctor.discovery import discover_environments
from pydoctor.discovery_models import (
    CandidateHint,
    DiscoveryReport,
    SourceEvidence,
    SourceResult,
)
from pydoctor.discovery_normalization import merge_candidates
from pydoctor.discovery_sources import DiscoveryInputError


class ComparisonCliTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.target = self.root / "python.exe"
        self.target.write_text("Not an interpreter.", encoding="utf-8")
        self.discovered = merge_candidates(
            (
                CandidateHint(
                    str(self.target),
                    SourceEvidence("project", str(self.root)),
                ),
            )
        )

    def invoke(self, arguments):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(arguments)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_comparison_cli_schema_and_pretty_json(self):
        with patch(
            "pydoctor.comparison.discover_environments",
            return_value=self.discovered,
        ):
            status, stdout, stderr = self.invoke(
                ["--compare-interpreter", str(self.target), "--pretty"]
            )
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        self.assertIn('\n  "target"', stdout)
        report = json.loads(stdout)
        self.assertEqual(report["schema_version"], "1.2")
        self.assertEqual(report["scope"], "intended_interpreter_comparison")
        self.assertEqual(report["outcome"], "MATCHED")
        self.assertEqual(report["target"]["interpreter_verification"], "NOT_VERIFIED")

    def test_default_m1_does_not_start_discovery_or_comparison(self):
        with (
            patch("pydoctor.__main__.discover_environments") as discover,
            patch("pydoctor.__main__.compare_interpreter") as compare,
        ):
            status, stdout, stderr = self.invoke(["--pretty"])
        discover.assert_not_called()
        compare.assert_not_called()
        self.assertEqual((status, stderr), (0, ""))
        report = json.loads(stdout)
        self.assertEqual(report["schema_version"], "1.0")
        self.assertEqual(report["scope"], "current_interpreter")
        self.assertNotIn("target", report)

    def test_m2_contract_is_still_schema_1_1(self):
        with (
            patch(
                "pydoctor.__main__.discover_environments",
                return_value=self.discovered,
            ),
            patch("pydoctor.__main__.compare_interpreter") as compare,
        ):
            status, stdout, stderr = self.invoke(["--discover", "--pretty"])
        compare.assert_not_called()
        self.assertEqual((status, stderr), (0, ""))
        report = json.loads(stdout)
        self.assertEqual(report["schema_version"], "1.1")
        self.assertEqual(report["scope"], "python_discovery")
        self.assertNotIn("target", report)

    def test_modes_are_mutually_exclusive_before_collection(self):
        with (
            patch("pydoctor.__main__.compare_interpreter") as compare,
            patch("pydoctor.__main__.discover_environments") as discover,
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as result,
        ):
            main(["--discover", "--compare-interpreter", str(self.target)])
        self.assertEqual(result.exception.code, 2)
        compare.assert_not_called()
        discover.assert_not_called()

    def test_project_without_a_mode_is_an_argument_error(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
            main(["--project", str(self.root)])
        self.assertEqual(result.exception.code, 2)

    def test_compare_requires_a_value(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as result:
            main(["--compare-interpreter"])
        self.assertEqual(result.exception.code, 2)

    def test_invalid_target_is_a_successful_uncertainty_report(self):
        with patch("pydoctor.comparison.discover_environments") as discover:
            status, stdout, stderr = self.invoke(["--compare-interpreter", ""])
        discover.assert_not_called()
        self.assertEqual((status, stderr), (0, ""))
        report = json.loads(stdout)
        self.assertEqual(report["target"]["status"], "INVALID")
        self.assertEqual(report["outcome"], "INSUFFICIENT_EVIDENCE")

    def test_missing_target_with_project_returns_a_report(self):
        missing = str(self.root / "missing.exe")
        with patch(
            "pydoctor.comparison.discover_environments",
            return_value=DiscoveryReport(()),
        ) as discover:
            status, stdout, stderr = self.invoke(
                ["--compare-interpreter", missing, "--project", str(self.root)]
            )
        discover.assert_called_once_with(str(self.root))
        self.assertEqual((status, stderr), (0, ""))
        self.assertEqual(json.loads(stdout)["target"]["status"], "MISSING")

    def test_invalid_project_preserves_structured_input_error(self):
        with patch(
            "pydoctor.comparison.discover_environments",
            side_effect=DiscoveryInputError("Fixture invalid project."),
        ):
            status, stdout, stderr = self.invoke(
                ["--compare-interpreter", str(self.target), "--project", "\x00"]
            )
        self.assertEqual(status, 2)
        self.assertEqual(stdout, "")
        report = json.loads(stderr)
        self.assertEqual(report["schema_version"], "1.2")
        self.assertEqual(report["error"]["code"], "invalid_project_directory")

    def test_handled_comparison_failure_is_schema_1_2_stderr(self):
        with patch(
            "pydoctor.__main__.compare_interpreter",
            side_effect=OSError("Fixture denied."),
        ):
            status, stdout, stderr = self.invoke(
                ["--compare-interpreter", str(self.target)]
            )
        self.assertEqual(status, 1)
        self.assertEqual(stdout, "")
        report = json.loads(stderr)
        self.assertEqual(report["schema_version"], "1.2")
        self.assertEqual(report["error"]["code"], "collection_failed")

    def launcher_integration(self, timeout):
        real_discovery = discover_environments

        def collect(project):
            return real_discovery(project, environ={}, platform_name="win32")

        current = SourceResult(
            (
                CandidateHint(
                    str(self.target),
                    SourceEvidence("current_interpreter", "fixture"),
                ),
            )
        )
        with ExitStack() as stack:
            stack.enter_context(
                patch("pydoctor.comparison.discover_environments", side_effect=collect)
            )
            stack.enter_context(
                patch("pydoctor.discovery.discover_current", return_value=current)
            )
            for name in ("discover_registry", "discover_path", "discover_active"):
                stack.enter_context(
                    patch(f"pydoctor.discovery.{name}", return_value=SourceResult())
                )
            if timeout:
                stack.enter_context(
                    patch(
                        "pydoctor.discovery_sources.resolve_launcher",
                        return_value=r"C:\Windows\py.exe",
                    )
                )
                run = stack.enter_context(
                    patch(
                        "pydoctor.discovery_sources.subprocess.run",
                        side_effect=subprocess.TimeoutExpired("py", 3),
                    )
                )
            else:
                stack.enter_context(
                    patch(
                        "pydoctor.discovery_sources.resolve_launcher",
                        return_value=None,
                    )
                )
                run = stack.enter_context(
                    patch("pydoctor.discovery_sources.subprocess.run")
                )
            result = compare_interpreter(str(self.target))
            if timeout:
                run.assert_called_once()
                self.assertEqual(run.call_args.args[0], [r"C:\Windows\py.exe", "-0p"])
                self.assertFalse(run.call_args.kwargs["shell"])
            else:
                run.assert_not_called()
        return result

    def test_missing_launcher_does_not_block_comparison(self):
        result = self.launcher_integration(timeout=False)
        self.assertEqual(result.outcome, "MATCHED")
        self.assertIn(
            "launcher_missing",
            {issue.code for issue in result.discovery_issues},
        )

    def test_launcher_timeout_does_not_block_comparison(self):
        result = self.launcher_integration(timeout=True)
        self.assertEqual(result.outcome, "MATCHED")
        self.assertIn(
            "launcher_timeout",
            {issue.code for issue in result.discovery_issues},
        )


if __name__ == "__main__":
    unittest.main()
