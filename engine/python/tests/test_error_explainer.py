"""Traceback parsing and explanation tests."""

import tempfile
import unittest
from pathlib import Path

from pyd_fixtures import add_distribution, make_venv
from pydoctor.error_explainer import explain_error, parse_traceback, read_traceback

MODULE_TRACEBACK = (
    "Traceback (most recent call last):\n"
    '  File "C:\\project\\app.py", line 3, in <module>\n'
    "    import requests\n"
    "ModuleNotFoundError: No module named 'requests'\n"
)


class ErrorExplainerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def codes(self, report) -> set[str]:
        return {finding.code for finding in report.findings}

    def test_module_not_found(self) -> None:
        report = explain_error(MODULE_TRACEBACK, "fixture")
        self.assertEqual(report.exception_type, "ModuleNotFoundError")
        self.assertEqual(report.frames[0].line, 3)
        self.assertIn("error.module_not_found", self.codes(report))

    def test_import_name_missing(self) -> None:
        text = (
            "Traceback (most recent call last):\n"
            '  File "C:\\project\\app.py", line 1, in <module>\n'
            "    from bar import foo\n"
            "ImportError: cannot import name 'foo' from 'bar'\n"
        )
        report = explain_error(text, "fixture")
        self.assertIn("error.import_name_missing", self.codes(report))

    def test_syntax_error(self) -> None:
        text = '  File "C:\\project\\app.py", line 1\n    def broken(\nSyntaxError: invalid syntax\n'
        report = explain_error(text, "fixture")
        self.assertIn("error.syntax_error", self.codes(report))

    def test_unclassified_text(self) -> None:
        report = explain_error("hello world", "fixture")
        self.assertIn("error.unclassified", self.codes(report))

    def test_environment_context(self) -> None:
        executable = make_venv(self.root)
        add_distribution(executable.parent.parent, "requests", "2.31.0")

        report = explain_error(
            MODULE_TRACEBACK, "fixture", intended_interpreter=str(executable)
        )

        self.assertIn("error.module_metadata_present", self.codes(report))
        self.assertIn("error.frames_outside_intended_environment", self.codes(report))

    def test_read_traceback_file(self) -> None:
        path = self.root / "trace.txt"
        path.write_text(MODULE_TRACEBACK, encoding="utf-8")
        text, issues = read_traceback(str(path))
        self.assertIn("ModuleNotFoundError", text or "")
        self.assertEqual(issues, [])

    def test_parse_traceback_frames(self) -> None:
        exception, message, frames, issues = parse_traceback(MODULE_TRACEBACK)
        self.assertEqual(exception, "ModuleNotFoundError")
        self.assertIn("requests", message or "")
        self.assertEqual(len(frames), 1)
        self.assertEqual(issues, ())


if __name__ == "__main__":
    unittest.main()
