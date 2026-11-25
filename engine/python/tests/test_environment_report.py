"""Unified environment report aggregation tests."""

import tempfile
import unittest
from pathlib import Path

from pyd_fixtures import add_distribution, add_kernelspec, make_venv, write_notebook
from pydoctor.environment_report import build_environment_report


class EnvironmentReportTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.executable = make_venv(self.root)
        self.prefix = self.executable.parent.parent

    def test_aggregates_packages_and_notebooks(self) -> None:
        add_distribution(
            self.prefix,
            "demo",
            "1.0",
            requires=("missing-dep>=1",),
            requires_python=">=3.8",
        )
        project = self.root / "project"
        project.mkdir()
        add_kernelspec(self.prefix, "pyd-test-kernel", self.executable)
        write_notebook(project / "a.ipynb", kernel="pyd-test-kernel")

        report = build_environment_report(str(self.executable), str(project))

        self.assertEqual(report.schema_version, "1.7")
        self.assertEqual(report.summary.distributions, 1)
        self.assertEqual(report.summary.missing_dependencies, 1)
        self.assertEqual(report.summary.notebooks, 1)
        self.assertIsNotNone(report.notebooks)
        codes = {finding.code for finding in report.findings}
        self.assertIn("environment.target", codes)
        self.assertIn("environment.packages", codes)
        self.assertIn("environment.notebooks", codes)

    def test_without_project_has_no_notebook_section(self) -> None:
        report = build_environment_report(str(self.executable))
        self.assertIsNone(report.notebooks)
        self.assertEqual(report.summary.notebooks, 0)


if __name__ == "__main__":
    unittest.main()
