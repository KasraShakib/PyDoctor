"""CLI contract tests for M7-M11 modes."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from pyd_fixtures import add_distribution, add_kernelspec, make_venv, write_notebook
from pydoctor.__main__ import main


class ExtendedCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.executable = make_venv(self.root)
        self.prefix = self.executable.parent.parent
        add_distribution(self.prefix, "demo", "1.0", requires=("missing-dep>=1",))

    def run_cli(self, argv):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(argv)
        return status, stdout.getvalue(), stderr.getvalue()

    def test_info(self) -> None:
        status, stdout, stderr = self.run_cli(["--info"])
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        data = json.loads(stdout)
        self.assertEqual(data["schema_version"], "meta")
        self.assertEqual(data["scope"], "engine_info")
        self.assertEqual(data["version"], "0.2.0")
        self.assertIn("environment_report", data["modes"])

    def test_version_exits_zero(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as raised:
                main(["--version"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("0.2.0", stdout.getvalue())

    def test_notebook_mode(self) -> None:
        project = self.root / "project"
        project.mkdir()
        add_kernelspec(self.prefix, "pyd-test-kernel", self.executable)
        write_notebook(project / "a.ipynb", kernel="pyd-test-kernel")
        status, stdout, stderr = self.run_cli(
            ["--inspect-notebooks", str(project), "--interpreter", str(self.executable)]
        )
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        data = json.loads(stdout)
        self.assertEqual(data["schema_version"], "1.4")
        self.assertEqual(data["scope"], "notebook_diagnostics")

    def test_error_mode(self) -> None:
        path = self.root / "trace.txt"
        path.write_text(
            "Traceback (most recent call last):\n"
            '  File "C:\\project\\app.py", line 1, in <module>\n'
            "ModuleNotFoundError: No module named 'requests'\n",
            encoding="utf-8",
        )
        status, stdout, stderr = self.run_cli(["--explain-error", str(path)])
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        data = json.loads(stdout)
        self.assertEqual(data["schema_version"], "1.5")
        self.assertEqual(data["exception_type"], "ModuleNotFoundError")

    def test_repair_plan_mode(self) -> None:
        report = {
            "scope": "package_diagnostics",
            "target": {"supplied_path": str(self.executable)},
            "dependencies": [
                {"kind": "requirement", "status": "MISSING", "requirement": "missing-dep>=1"}
            ],
            "findings": [],
        }
        path = self.root / "report.json"
        path.write_text(json.dumps(report), encoding="utf-8")
        status, stdout, stderr = self.run_cli(["--repair-plan", str(path)])
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        data = json.loads(stdout)
        self.assertEqual(data["schema_version"], "1.6")
        self.assertTrue(data["dry_run"])
        self.assertEqual(len(data["steps"]), 1)

    def test_environment_report_mode(self) -> None:
        status, stdout, stderr = self.run_cli(
            ["--environment-report", str(self.executable)]
        )
        self.assertEqual(status, 0)
        self.assertEqual(stderr, "")
        data = json.loads(stdout)
        self.assertEqual(data["schema_version"], "1.7")
        self.assertEqual(data["scope"], "environment_report")
        self.assertEqual(data["summary"]["distributions"], 1)

    def test_invalid_repair_report_exits_two(self) -> None:
        path = self.root / "bad.json"
        path.write_text("not json", encoding="utf-8")
        status, stdout, stderr = self.run_cli(["--repair-plan", str(path)])
        self.assertEqual(status, 2)
        self.assertEqual(stdout, "")
        self.assertEqual(json.loads(stderr)["error"]["code"], "invalid_report_file")

    def test_interpreter_requires_context_mode(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(["--inspect-packages", str(self.executable), "--interpreter", str(self.executable)])
        self.assertEqual(raised.exception.code, 2)

    def test_project_rejected_for_notebook_mode(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(["--inspect-notebooks", str(self.root), "--project", str(self.root)])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
