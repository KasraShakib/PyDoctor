"""Dependency status tests against synthetic distribution metadata."""

import unittest

from pydoctor.dependency_analysis import (
    MISSING,
    OPTIONAL_UNKNOWN,
    SATISFIED,
    SKIPPED,
    UNKNOWN,
    VERSION_CONFLICT,
    analyze_dependencies,
    find_duplicates,
)
from pydoctor.package_models import PackageDistribution
from pydoctor.requirements import normalize_name


def distribution(
    name: str,
    version: str,
    requires: tuple[str, ...] = (),
    requires_python: str | None = None,
) -> PackageDistribution:
    return PackageDistribution(
        name=name,
        normalized_name=normalize_name(name),
        version=version,
        metadata_kind="dist-info",
        location=f"C:/fixtures/{name}-{version}.dist-info",
        metadata_path=None,
        requires_dist=requires,
        requires_python=requires_python,
    )


def find(results, package: str, fragment: str):
    return next(
        item
        for item in results
        if item.package == package and fragment in item.requirement
    )


class DependencyStatusTests(unittest.TestCase):
    def test_satisfied_missing_and_conflict(self) -> None:
        results = analyze_dependencies(
            (
                distribution("flask", "2.0.0", ("requests>=2.0", "missing-pkg")),
                distribution("requests", "2.31.0"),
            ),
            "3.12.9",
        )
        self.assertEqual(find(results, "flask", "requests").status, SATISFIED)
        self.assertEqual(find(results, "flask", "missing-pkg").status, MISSING)

        conflicting = analyze_dependencies(
            (
                distribution("flask", "2.0.0", ("requests>=3.0",)),
                distribution("requests", "2.31.0"),
            ),
            "3.12.9",
        )
        self.assertEqual(find(conflicting, "flask", "requests").status, VERSION_CONFLICT)

    def test_marker_handling(self) -> None:
        results = analyze_dependencies(
            (
                distribution(
                    "demo",
                    "1.0",
                    (
                        'pytest; extra == "test"',
                        'old; python_version < "3.0"',
                        'machine; platform_machine == "x86_64"',
                    ),
                ),
            ),
            "3.12.9",
        )
        self.assertEqual(find(results, "demo", "pytest").status, OPTIONAL_UNKNOWN)
        self.assertEqual(find(results, "demo", "old").status, SKIPPED)
        self.assertEqual(find(results, "demo", "machine").status, UNKNOWN)

    def test_requires_python(self) -> None:
        satisfied = analyze_dependencies(
            (distribution("demo", "1.0", requires_python=">=3.8"),), "3.12.9"
        )
        self.assertEqual(satisfied[0].status, SATISFIED)

        conflict = analyze_dependencies(
            (distribution("demo", "1.0", requires_python="<3.10"),), "3.12.9"
        )
        self.assertEqual(conflict[0].status, VERSION_CONFLICT)

        unknown = analyze_dependencies(
            (distribution("demo", "1.0", requires_python=">=3.8"),), None
        )
        self.assertEqual(unknown[0].status, UNKNOWN)

    def test_duplicate_detection(self) -> None:
        duplicates = find_duplicates(
            (distribution("demo", "1.0"), distribution("Demo", "2.0"))
        )
        self.assertEqual(list(duplicates), ["demo"])
        self.assertEqual(len(duplicates["demo"]), 2)


if __name__ == "__main__":
    unittest.main()
