"""Notebook and kernelspec diagnostics tests using temporary fixtures."""

import tempfile
import unittest
from pathlib import Path

from pyd_fixtures import add_kernelspec, make_venv, write_notebook
from pydoctor.notebooks import inspect_notebooks, parse_notebook


class NotebookTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.executable = make_venv(self.root)
        self.prefix = self.executable.parent.parent

    def codes(self, report) -> set[str]:
        return {finding.code for finding in report.findings}

    def test_kernel_matches_intended_and_notebook_metadata(self) -> None:
        add_kernelspec(self.prefix, "pyd-test-kernel", self.executable)
        project = self.root / "project"
        project.mkdir()
        write_notebook(project / "a.ipynb", kernel="pyd-test-kernel", version="3.12.9")

        report = inspect_notebooks(str(project), str(self.executable), environ={})

        self.assertEqual(report.schema_version, "1.4")
        self.assertEqual(report.target_kind, "project")
        self.assertEqual(len(report.notebooks), 1)
        self.assertIn("notebooks.kernels_observed", self.codes(report))
        self.assertIn("notebooks.kernel_matches_intended", self.codes(report))
        self.assertNotIn("notebooks.kernel_missing", self.codes(report))

    def test_missing_kernel_and_version_mismatch(self) -> None:
        add_kernelspec(self.prefix, "pyd-test-kernel", self.executable)
        project = self.root / "project"
        project.mkdir()
        write_notebook(project / "a.ipynb", kernel="absent-kernel", version="3.9.1")

        report = inspect_notebooks(str(project), str(self.executable), environ={})

        self.assertIn("notebooks.kernel_missing", self.codes(report))
        self.assertIn("notebooks.language_version_mismatch", self.codes(report))

    def test_kernel_interpreter_missing(self) -> None:
        add_kernelspec(self.prefix, "broken-kernel", self.root / "missing" / "python.exe")

        report = inspect_notebooks(str(self.root / "absent"), str(self.executable), environ={})

        self.assertIn("notebooks.kernel_interpreter_missing", self.codes(report))
        self.assertEqual(report.target_kind, "missing")

    def test_invalid_notebook(self) -> None:
        project = self.root / "project"
        project.mkdir()
        (project / "bad.ipynb").write_text("{not json", encoding="utf-8")

        report = inspect_notebooks(str(project), None, environ={})

        self.assertIn("notebooks.invalid_notebook", self.codes(report))

    def test_parse_notebook_metadata(self) -> None:
        path = write_notebook(self.root / "one.ipynb", kernel="python3", version="3.11.4")
        observation = parse_notebook(str(path))
        self.assertTrue(observation.valid)
        self.assertEqual(observation.kernel_name, "python3")
        self.assertEqual(observation.language_version, "3.11.4")


if __name__ == "__main__":
    unittest.main()
