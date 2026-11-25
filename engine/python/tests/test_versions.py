"""PEP 440 subset tests for version ordering and specifier evaluation."""

import unittest

from pydoctor.versions import SpecifierSet, evaluate_specifier, parse_version


class VersionOrderingTests(unittest.TestCase):
    def test_release_and_prerelease_order(self) -> None:
        ordered = [
            "1.0.dev1",
            "1.0a1",
            "1.0b1",
            "1.0rc1",
            "1.0",
            "1.0.post1",
            "1.1",
            "2.0",
        ]
        parsed = [parse_version(item) for item in ordered]
        self.assertEqual(parsed, sorted(parsed))

    def test_epoch_and_local_labels(self) -> None:
        self.assertGreater(parse_version("1!1.0"), parse_version("2.0"))
        self.assertLess(parse_version("1.0"), parse_version("1.0+local"))
        self.assertEqual(parse_version("1.0.0"), parse_version("1.0"))

    def test_unsupported_version_raises(self) -> None:
        with self.assertRaises(ValueError):
            parse_version("not-a-version")


class SpecifierTests(unittest.TestCase):
    def test_range_conjunction(self) -> None:
        specifier = SpecifierSet.parse(">=1.0,<2")
        self.assertTrue(specifier.contains("1.5"))
        self.assertFalse(specifier.contains("2.0"))

    def test_compatible_release(self) -> None:
        self.assertTrue(SpecifierSet.parse("~=1.4.5").contains("1.4.9"))
        self.assertFalse(SpecifierSet.parse("~=1.4.5").contains("1.5.0"))

    def test_wildcards_and_arbitrary_equality(self) -> None:
        self.assertTrue(SpecifierSet.parse("==1.4.*").contains("1.4.9"))
        self.assertFalse(SpecifierSet.parse("==1.4.*").contains("1.5.0"))
        self.assertTrue(SpecifierSet.parse("!=1.4.*").contains("1.5.0"))
        self.assertTrue(SpecifierSet.parse("===1.0").contains("1.0"))

    def test_prerelease_and_postrelease_exclusion(self) -> None:
        self.assertFalse(SpecifierSet.parse("<2.0").contains("2.0rc1"))
        self.assertFalse(SpecifierSet.parse(">1.0").contains("1.0.post1"))

    def test_unparseable_input_is_unknown(self) -> None:
        self.assertIsNone(evaluate_specifier("garbage", "1.0"))
        self.assertIsNone(evaluate_specifier(">=1", None))
        self.assertTrue(evaluate_specifier(None, "1.0"))


if __name__ == "__main__":
    unittest.main()
