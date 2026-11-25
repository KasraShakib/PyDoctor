"""Presentation helper tests; Tk is not started."""

import json
import unittest

import ui_model


class UiModelTests(unittest.TestCase):
    def test_environment_summary(self) -> None:
        report = {
            "scope": "environment_report",
            "interpreter": r"C:\env\Scripts\python.exe",
            "project": None,
            "summary": {
                "comparison_outcome": "MATCHED",
                "distributions": 3,
                "missing_dependencies": 1,
                "version_conflicts": 0,
                "notebooks": 2,
                "kernels": 1,
                "severity": "WARNING",
            },
            "findings": [
                {
                    "code": "environment.packages",
                    "severity": "WARNING",
                    "confidence": "CONFIRMED",
                    "summary": "Package metadata was evaluated.",
                    "evidence": ["Distributions: 3"],
                    "next_steps": ["Review findings."],
                }
            ],
        }
        text = ui_model.describe(report)
        self.assertIn("Environment summary", text)
        self.assertIn("MATCHED", text)
        self.assertIn("[WARNING] environment.packages", text)
        self.assertIn("Distributions: 3", text)

    def test_package_summary_counts(self) -> None:
        report = {
            "scope": "package_diagnostics",
            "interpreter_prefix": r"C:\env",
            "python_version": "3.12.9",
            "distributions": [{"name": "requests"}, {"name": "click"}],
            "dependencies": [
                {"status": "MISSING"},
                {"status": "VERSION_CONFLICT"},
                {"status": "SATISFIED"},
            ],
            "findings": [],
        }
        text = ui_model.describe(report)
        self.assertIn("Distributions: 2", text)
        self.assertIn("Missing: 1", text)
        self.assertIn("Version conflicts: 1", text)
        self.assertIn("requests", text)

    def test_repair_plan(self) -> None:
        report = {
            "scope": "repair_plan",
            "source_report": "report.json",
            "steps": [
                {
                    "risk": "MEDIUM",
                    "title": "Install missing dependency demo",
                    "argv": ["python", "-m", "pip", "install", "demo"],
                    "verification": "Re-run diagnostics.",
                }
            ],
            "findings": [],
        }
        text = ui_model.describe(report)
        self.assertIn("Repair plan (dry run)", text)
        self.assertIn("[MEDIUM] Install missing dependency demo", text)

    def test_pretty_round_trips_json(self) -> None:
        self.assertEqual(json.loads(ui_model.pretty({"a": 1})), {"a": 1})

    def test_unknown_scope_falls_back_to_json(self) -> None:
        self.assertIn('"scope": "other"', ui_model.describe({"scope": "other"}))


if __name__ == "__main__":
    unittest.main()
