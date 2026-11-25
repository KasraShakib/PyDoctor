"""PEP 508 requirement parsing and bounded marker evaluation tests."""

import unittest

from pydoctor.requirements import (
    MarkerNotEvaluated,
    RequirementError,
    evaluate_marker,
    marker_context,
    marker_references_extra,
    normalize_name,
    parse_requirement,
)


class RequirementParsingTests(unittest.TestCase):
    def test_name_extras_specifier_and_marker(self) -> None:
        requirement = parse_requirement(
            "requests[security] >= 2.8, != 2.9 ; python_version < '3.8'"
        )
        self.assertEqual(requirement.name, "requests")
        self.assertEqual(requirement.normalized_name, "requests")
        self.assertEqual(requirement.extras, ("security",))
        self.assertEqual(requirement.specifier, ">= 2.8, != 2.9")
        self.assertEqual(requirement.marker, "python_version < '3.8'")

    def test_parenthesized_specifier(self) -> None:
        requirement = parse_requirement("demo (>=1.0,<2.0)")
        self.assertEqual(requirement.specifier, ">=1.0,<2.0")

    def test_direct_reference(self) -> None:
        requirement = parse_requirement(
            'demo @ https://example.invalid/demo.whl ; python_version >= "3.8"'
        )
        self.assertEqual(requirement.url, "https://example.invalid/demo.whl")
        self.assertEqual(requirement.marker, 'python_version >= "3.8"')

    def test_normalized_name(self) -> None:
        self.assertEqual(normalize_name("Foo_Bar.baz"), "foo-bar-baz")

    def test_invalid_requirements_raise(self) -> None:
        for text in ("", "   ", "!!!"):
            with self.assertRaises(RequirementError):
                parse_requirement(text)


class MarkerTests(unittest.TestCase):
    def test_version_and_platform_comparisons(self) -> None:
        context = {"python_version": "3.12", "sys_platform": "win32"}
        self.assertTrue(evaluate_marker('python_version >= "3.8"', context))
        self.assertFalse(evaluate_marker('python_version < "3.8"', context))
        self.assertTrue(
            evaluate_marker(
                'sys_platform == "win32" and python_version >= "3.8"', context
            )
        )
        self.assertTrue(
            evaluate_marker(
                '(sys_platform == "win32" or sys_platform == "linux")', context
            )
        )

    def test_unknown_variables_are_not_guessed(self) -> None:
        for marker in ('extra == "dev"', 'platform_machine == "x86_64"'):
            with self.assertRaises(MarkerNotEvaluated):
                evaluate_marker(marker, {})

    def test_extra_detection_and_context(self) -> None:
        self.assertTrue(marker_references_extra('extra == "dev"'))
        self.assertFalse(marker_references_extra('python_version >= "3.8"'))
        context = marker_context("3.12.9")
        self.assertEqual(context["python_version"], "3.12")
        self.assertEqual(context["python_full_version"], "3.12.9")


if __name__ == "__main__":
    unittest.main()
