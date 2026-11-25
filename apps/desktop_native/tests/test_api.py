"""Tests for the JavaScript-facing bridge in the native desktop shell."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps" / "desktop_native"))
sys.path.insert(0, str(ROOT / "engine" / "python" / "src"))

from app import Api  # noqa: E402


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.api = Api()

    def test_engine_info(self) -> None:
        info = self.api.engine_info()
        self.assertEqual(info["scope"], "engine_info")
        self.assertIn("modes", info)

    def test_discover(self) -> None:
        report = self.api.discover("")
        self.assertEqual(report["scope"], "python_discovery")
        self.assertIn("candidates", report)

    def test_package_report_for_engine_python(self) -> None:
        report = self.api.run_report("packages", sys.executable)
        self.assertEqual(report["scope"], "package_diagnostics")
        self.assertIn("distributions", report)

    def test_missing_interpreter_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.api.run_report("packages", "", "", "")

    def test_notebooks_requires_project(self) -> None:
        with self.assertRaises(ValueError):
            self.api.run_report("notebooks", "C:\\python.exe", "", "")

    def test_error_requires_traceback(self) -> None:
        with self.assertRaises(ValueError):
            self.api.run_report("error", "", "", "   ")

    def test_invalid_repair_payload(self) -> None:
        with self.assertRaises(ValueError):
            self.api.run_report("repair", "", "", "not json")

    def test_unknown_mode(self) -> None:
        with self.assertRaises(ValueError):
            self.api.run_report("nope", "", "", "")


if __name__ == "__main__":
    unittest.main()
