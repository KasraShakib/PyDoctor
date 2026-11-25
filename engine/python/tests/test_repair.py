"""Repair planning and guarded execution tests; no real pip is run."""

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from pyd_fixtures import make_venv
from pydoctor.repair import build_repair_plan, execute_repair_step
from pydoctor.repair_models import RepairStep


def step(argv: tuple[str, ...], step_id: str = "s1") -> RepairStep:
    return RepairStep(
        step_id=step_id,
        title="Test step",
        rationale="Test rationale",
        risk="MEDIUM",
        requires_confirmation=True,
        argv=argv,
        verification="Re-run diagnostics.",
    )


class RepairPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.executable = make_venv(self.root)

    def test_missing_dependency_becomes_pip_install(self) -> None:
        report = {
            "scope": "package_diagnostics",
            "target": {"supplied_path": str(self.executable)},
            "dependencies": [
                {"kind": "requirement", "status": "MISSING", "requirement": "missing-dep>=1.0"}
            ],
            "findings": [],
        }
        plan = build_repair_plan(report, "report.json")
        self.assertTrue(plan.dry_run)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(
            plan.steps[0].argv,
            (str(self.executable), "-m", "pip", "install", "missing-dep>=1.0"),
        )
        self.assertEqual(plan.steps[0].risk, "MEDIUM")
        self.assertTrue(plan.steps[0].requires_confirmation)

    def test_requires_python_does_not_become_pip_install(self) -> None:
        report = {
            "scope": "package_diagnostics",
            "target": {"supplied_path": str(self.executable)},
            "dependencies": [
                {
                    "kind": "requires_python",
                    "status": "VERSION_CONFLICT",
                    "requirement": "Requires-Python: <3.10",
                }
            ],
            "findings": [],
        }
        plan = build_repair_plan(report, "report.json")
        self.assertEqual(plan.steps, ())
        self.assertEqual(plan.findings[0].code, "repair.no_actions")

    def test_approval_must_match_step_id(self) -> None:
        with self.assertRaises(PermissionError):
            execute_repair_step(
                step((str(self.executable), "-m", "pip", "install", "demo")),
                approved_step_id="other",
            )

    def test_non_allowlisted_command_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            execute_repair_step(
                step((str(self.executable), "-m", "pip", "uninstall", "demo")),
                approved_step_id="s1",
            )

    def test_execution_uses_fake_runner_and_verifies(self) -> None:
        calls = []

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(returncode=0, stdout="ok", stderr="")

        result = execute_repair_step(
            step((str(self.executable), "-m", "pip", "install", "demo")),
            approved_step_id="s1",
            runner=runner,
        )

        self.assertTrue(result.executed)
        self.assertEqual(result.returncode, 0)
        self.assertFalse(result.verified)
        self.assertFalse(calls[0][1]["shell"])

    def test_runner_failure_is_reported(self) -> None:
        def runner(argv, **kwargs):
            raise OSError("blocked")

        result = execute_repair_step(
            step((str(self.executable), "-m", "pip", "install", "demo")),
            approved_step_id="s1",
            runner=runner,
        )
        self.assertFalse(result.executed)


if __name__ == "__main__":
    unittest.main()
