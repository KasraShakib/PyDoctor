"""CLI contract tests, including a real module invocation."""

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from pydoctor.__main__ import main
from pydoctor.environment import diagnose_current_environment
from pydoctor.models import Confidence, DiagnosticReport, Finding


class CliTests(unittest.TestCase):
    def test_success_is_exactly_one_json_document(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main([])
        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), "")
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["schema_version"], "1.0")
        self.assertEqual(data["runtime"]["executable"], sys.executable)
        self.assertEqual(stdout.getvalue().count("\n"), 1)

    def test_pretty_output_is_valid_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = main(["--pretty"])
        self.assertEqual(status, 0)
        self.assertIn('\n  "runtime"', stdout.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["scope"], "current_interpreter")

    def test_collection_error_uses_stderr_and_nonzero_exit(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with (
            patch("pydoctor.__main__.diagnose_current_environment", side_effect=OSError("denied")),
            redirect_stdout(stdout),
            redirect_stderr(stderr),
        ):
            status = main([])
        self.assertEqual(status, 1)
        self.assertEqual(stdout.getvalue(), "")
        data = json.loads(stderr.getvalue())
        self.assertEqual(data["error"], {"code": "collection_failed", "message": "denied"})

    def test_unknown_finding_is_not_an_execution_failure(self) -> None:
        report = DiagnosticReport(
            runtime=diagnose_current_environment().runtime,
            findings=(
                Finding(
                    code="test.unknown",
                    confidence=Confidence.UNKNOWN,
                    summary="Test observation could not be verified.",
                    evidence=("Test fixture.",),
                ),
            ),
        )
        stdout = io.StringIO()
        with (
            patch("pydoctor.__main__.diagnose_current_environment", return_value=report),
            redirect_stdout(stdout),
        ):
            status = main([])
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(stdout.getvalue())["findings"][0]["confidence"], "UNKNOWN")

    def test_invalid_arguments_do_not_start_collection(self) -> None:
        stderr = io.StringIO()
        with (
            patch("pydoctor.__main__.diagnose_current_environment") as collect,
            redirect_stderr(stderr),
            self.assertRaises(SystemExit) as result,
        ):
            main(["--repair"])
        self.assertEqual(result.exception.code, 2)
        collect.assert_not_called()

    def test_module_invocation(self) -> None:
        source_root = Path(__file__).resolve().parents[1] / "src"
        result = subprocess.run(
            [sys.executable, "-m", "pydoctor", "--pretty"],
            cwd=source_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        data = json.loads(result.stdout)
        self.assertEqual(data["runtime"]["executable"], sys.executable)
        self.assertEqual(data["schema_version"], "1.0")
