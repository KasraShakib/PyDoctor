"""Site-packages derivation and bounded inventory tests."""

import tempfile
import unittest
from pathlib import Path

from pydoctor.package_inventory import build_inventory, interpreter_prefix


def make_distribution(site_packages: Path, name: str, version: str) -> None:
    location = site_packages / f"{name}-{version}.dist-info"
    location.mkdir()
    (location / "METADATA").write_text(
        f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n",
        encoding="utf-8",
    )


class InventoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def make_environment(self, version: str | None = None) -> tuple[Path, Path, Path]:
        prefix = self.root / "env"
        scripts = prefix / "Scripts"
        scripts.mkdir(parents=True)
        executable = scripts / "python.exe"
        executable.write_bytes(b"")
        site_packages = prefix / "Lib" / "site-packages"
        site_packages.mkdir(parents=True)
        if version:
            (prefix / "pyvenv.cfg").write_text(f"version = {version}\n", encoding="utf-8")
        return prefix, executable, site_packages

    def test_interpreter_prefix_for_scripts_layout(self) -> None:
        prefix, executable, _ = self.make_environment()
        self.assertEqual(interpreter_prefix(str(executable)), str(prefix))

    def test_inventory_reads_distributions_and_pyvenv_version(self) -> None:
        _, executable, site_packages = self.make_environment("3.12.9")
        make_distribution(site_packages, "requests", "2.31.0")
        make_distribution(site_packages, "click", "8.1.7")

        inventory = build_inventory(str(executable))

        self.assertEqual(inventory.python_version, "3.12.9")
        self.assertEqual(inventory.python_version_source, "pyvenv.cfg")
        self.assertEqual(
            [item.name for item in inventory.distributions],
            ["click", "requests"],
        )
        self.assertTrue(any(root.is_directory for root in inventory.roots))

    def test_missing_site_packages_is_explicit(self) -> None:
        prefix = self.root / "bare"
        scripts = prefix / "Scripts"
        scripts.mkdir(parents=True)
        executable = scripts / "python.exe"
        executable.write_bytes(b"")

        inventory = build_inventory(str(executable))

        self.assertEqual(inventory.distributions, ())
        self.assertTrue(all(root.exists is False for root in inventory.roots))


if __name__ == "__main__":
    unittest.main()
