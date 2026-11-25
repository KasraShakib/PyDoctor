"""Distribution metadata parsing tests using temporary fixtures."""

import json
import tempfile
import unittest
from pathlib import Path

from pydoctor.package_metadata import read_distribution


def write_metadata(directory: Path, lines: list[str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "METADATA").write_text("\n".join(lines) + "\n", encoding="utf-8")


def codes(distribution) -> set[str]:
    return {issue.code for issue in distribution.issues}


class MetadataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def test_reads_core_fields(self) -> None:
        location = self.root / "demo-1.0.dist-info"
        write_metadata(
            location,
            [
                "Metadata-Version: 2.1",
                "Name: demo",
                "Version: 1.0",
                "Summary: Demo package",
                "Requires-Python: >=3.8",
                "Requires-Dist: requests>=2",
                "Requires-Dist: click",
                "Provides-Extra: test",
            ],
        )
        (location / "INSTALLER").write_text("pip\n", encoding="utf-8")
        (location / "direct_url.json").write_text(
            json.dumps({"url": "https://example.invalid/demo"}), encoding="utf-8"
        )

        distribution = read_distribution(str(location))

        self.assertEqual(distribution.name, "demo")
        self.assertEqual(distribution.normalized_name, "demo")
        self.assertEqual(distribution.version, "1.0")
        self.assertEqual(distribution.summary, "Demo package")
        self.assertEqual(distribution.requires_python, ">=3.8")
        self.assertEqual(distribution.requires_dist, ("requests>=2", "click"))
        self.assertEqual(distribution.provides_extra, ("test",))
        self.assertEqual(distribution.installer, "pip")
        self.assertEqual(distribution.direct_url, "https://example.invalid/demo")
        self.assertEqual(distribution.issues, ())

    def test_missing_name_is_reported(self) -> None:
        location = self.root / "broken-1.0.dist-info"
        write_metadata(location, ["Metadata-Version: 2.1", "Version: 1.0"])
        distribution = read_distribution(str(location))
        self.assertIsNone(distribution.name)
        self.assertIn("metadata_missing_name", codes(distribution))

    def test_missing_metadata_file_is_reported(self) -> None:
        location = self.root / "empty-1.0.dist-info"
        location.mkdir()
        distribution = read_distribution(str(location))
        self.assertIn("metadata_file_missing", codes(distribution))
        self.assertEqual(distribution.metadata_kind, "dist-info")

    def test_egg_info_file_is_supported(self) -> None:
        location = self.root / "legacy.egg-info"
        location.write_text("Name: legacy\nVersion: 0.1\n", encoding="utf-8")
        distribution = read_distribution(str(location))
        self.assertEqual(distribution.name, "legacy")
        self.assertEqual(distribution.version, "0.1")
        self.assertEqual(distribution.metadata_kind, "egg-info")

    def test_utf8_bom_is_tolerated(self) -> None:
        location = self.root / "bom-1.0.dist-info"
        location.mkdir()
        (location / "METADATA").write_bytes(
            b"\xef\xbb\xbfMetadata-Version: 2.1\r\nName: bom\r\nVersion: 1.0\r\n"
        )
        distribution = read_distribution(str(location))
        self.assertEqual(distribution.name, "bom")
        self.assertEqual(distribution.version, "1.0")


if __name__ == "__main__":
    unittest.main()
