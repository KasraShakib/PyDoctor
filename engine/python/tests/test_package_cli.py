"""CLI contract tests for schema 1.3 package diagnostics."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from pydoctor.__main__ import main


class PackageCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        prefix = self.root / "env"
        scripts = prefix / "Scripts"
        scripts.mkdir(parents=True)
        self.executable = scripts / "python.exe"
        self.executable.write_bytes(b"")
        (prefix / "pyvenv.cfg").write_text("version = 3.12.9\n", encoding="utf-8")
        site_packages = prefix / "Lib" / "site-packages"
        site_packages.mkdir(parents=True)
        location = site_packages / "demo-1.0.dist-info"
        location.mkdir()
        (location / "METADATA").write_text(
            "Metadata-Version: 2.1\nName: demo\nVersion: 1.0\n"
            "Requires-Dist: requests>=2\n",
            encoding="utf-8",
        )

    def test_success_report(self) -> None:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            status = main(["--inspect-packages", str(self.executable)])
        self.assertEqual(status, 0)
        self.assertEqual(stderr.getvalue(), "")
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["schema_version"], "1.3")
        self.assertEqual(data["scope"], "package_diagnostics")
        self.assertEqual(data["python_version"], "3.12.9")
        self.assertEqual([item["name"] for item in data["distributions"]], ["demo"])
        codes = {finding["code"] for finding in data["findings"]}
        self.assertIn("packages.inventory_observed", codes)
        self.assertIn("packages.missing_dependency", codes)
        self.assertTrue(all("severity" in finding for finding in data["findings"]))
        missing = next(
            finding
            for finding in data["findings"]
            if finding["code"] == "packages.missing_dependency"
        )
        self.assertEqual(missing["severity"], "WARNING")
        self.assertEqual(missing["confidence"], "LIKELY")

    def test_missing_target_is_an_evidence_report(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = main(["--inspect-packages", str(self.root / "missing" / "python.exe")])
        self.assertEqual(status, 0)
        data = json.loads(stdout.getvalue())
        self.assertEqual(data["target"]["status"], "MISSING")
        self.assertEqual(data["findings"][0]["code"], "packages.target_unavailable")

    def test_pretty_output_is_valid_json(self) -> None:
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            status = main(["--inspect-packages", str(self.executable), "--pretty"])
        self.assertEqual(status, 0)
        self.assertIn('\n  "target"', stdout.getvalue())
        self.assertEqual(json.loads(stdout.getvalue())["schema_version"], "1.3")

    def test_project_is_rejected_for_package_mode(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(["--inspect-packages", str(self.executable), "--project", str(self.root)])
        self.assertEqual(raised.exception.code, 2)

    def test_modes_are_mutually_exclusive(self) -> None:
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as raised:
                main(["--inspect-packages", str(self.executable), "--discover"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
