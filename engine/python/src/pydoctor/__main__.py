"""Local JSON CLI for read-only PyDoctor evidence reports."""

import argparse
import json
import sys
from collections.abc import Sequence
from typing import Any

from pydoctor import __version__
from pydoctor.comparison import compare_interpreter
from pydoctor.discovery import discover_environments
from pydoctor.discovery_sources import DiscoveryInputError
from pydoctor.environment import diagnose_current_environment
from pydoctor.environment_report import build_environment_report
from pydoctor.error_explainer import explain_error, read_traceback
from pydoctor.notebooks import inspect_notebooks
from pydoctor.package_diagnostics import inspect_packages
from pydoctor.repair import build_repair_plan

MAX_REPORT_BYTES = 32 * 1024 * 1024


def _engine_info() -> dict[str, Any]:
    """Return machine-readable engine metadata for the desktop layer."""
    return {
        "schema_version": "meta",
        "scope": "engine_info",
        "name": "pydoctor-engine",
        "version": __version__,
        "engine_python": sys.version.split()[0],
        "modes": {
            "current_interpreter": {"flag": None, "schema": "1.0"},
            "python_discovery": {"flag": "--discover", "schema": "1.1"},
            "intended_interpreter_comparison": {
                "flag": "--compare-interpreter",
                "schema": "1.2",
            },
            "package_diagnostics": {"flag": "--inspect-packages", "schema": "1.3"},
            "notebook_diagnostics": {"flag": "--inspect-notebooks", "schema": "1.4"},
            "error_explanation": {"flag": "--explain-error", "schema": "1.5"},
            "repair_plan": {"flag": "--repair-plan", "schema": "1.6"},
            "environment_report": {"flag": "--environment-report", "schema": "1.7"},
        },
        "limits": {
            "path_directories": 128,
            "directory_entries": 4096,
            "distributions": 4096,
            "metadata_bytes": 2 * 1024 * 1024,
            "kernels": 256,
            "notebooks": 256,
            "traceback_bytes": 1024 * 1024,
            "report_bytes": MAX_REPORT_BYTES,
        },
    }


def _write_error(schema: str, code: str, message: str, status: int) -> int:
    json.dump(
        {"schema_version": schema, "error": {"code": code, "message": message}},
        sys.stderr,
        ensure_ascii=True,
    )
    sys.stderr.write("\n")
    return status


def _read_report(path: str) -> dict[str, Any]:
    with open(path, "rb") as handle:
        data = handle.read(MAX_REPORT_BYTES + 1)
    if len(data) > MAX_REPORT_BYTES:
        raise ValueError("Report exceeded the read limit.")
    if data.startswith((b"\xff\xfe", b"\xfe\xff")):
        text = data.decode("utf-16", errors="replace")
    else:
        text = data.decode("utf-8", errors="replace")
    payload = json.loads(text.lstrip("\ufeff"))
    if not isinstance(payload, dict):
        raise ValueError("Report must be a JSON object.")
    return payload


def main(argv: Sequence[str] | None = None) -> int:
    """Write one report, or a structured handled error, without target execution."""
    parser = argparse.ArgumentParser(
        description="Report read-only Python environment evidence."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pydoctor-engine {__version__}",
        help="Print the engine version and exit.",
    )
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON report.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--discover", action="store_true", help="Discover Windows Python candidates.")
    modes.add_argument(
        "--compare-interpreter",
        metavar="ABSOLUTE_PATH",
        help="Compare an explicit interpreter path with discovery evidence.",
    )
    modes.add_argument(
        "--inspect-packages",
        metavar="ABSOLUTE_PATH",
        help="Read installed distribution metadata for an explicit interpreter path.",
    )
    modes.add_argument(
        "--inspect-notebooks",
        metavar="TARGET",
        help="Inspect a notebook file or project directory for kernel evidence.",
    )
    modes.add_argument(
        "--explain-error",
        metavar="FILE",
        help="Explain a traceback file, or '-' for stdin.",
    )
    modes.add_argument(
        "--repair-plan",
        metavar="REPORT_FILE",
        help="Build a dry-run repair plan from a PyDoctor JSON report.",
    )
    modes.add_argument(
        "--environment-report",
        metavar="ABSOLUTE_PATH",
        help="Aggregate interpreter, package, and notebook evidence.",
    )
    modes.add_argument("--info", action="store_true", help="Print engine metadata as JSON.")
    parser.add_argument(
        "--project",
        help="Explicit project directory; requires discovery, comparison, or environment report.",
    )
    parser.add_argument(
        "--interpreter",
        metavar="ABSOLUTE_PATH",
        help="Intended interpreter context for notebook or error diagnosis.",
    )
    args = parser.parse_args(argv)

    comparing = args.compare_interpreter is not None
    notebooks = args.inspect_notebooks is not None
    error = args.explain_error is not None
    repair = args.repair_plan is not None
    environment = args.environment_report is not None
    packages = args.inspect_packages is not None

    if args.project is not None and not (args.discover or comparing or environment):
        parser.error(
            "--project requires --discover, --compare-interpreter, or --environment-report"
        )
    if args.interpreter is not None and not (notebooks or error):
        parser.error("--interpreter requires --inspect-notebooks or --explain-error")

    if args.info:
        schema = "meta"
    elif notebooks:
        schema = "1.4"
    elif error:
        schema = "1.5"
    elif repair:
        schema = "1.6"
    elif environment:
        schema = "1.7"
    elif packages:
        schema = "1.3"
    elif comparing:
        schema = "1.2"
    elif args.discover:
        schema = "1.1"
    else:
        schema = "1.0"

    try:
        if args.info:
            report: Any = _engine_info()
        elif notebooks:
            report = inspect_notebooks(args.inspect_notebooks, args.interpreter)
        elif error:
            text, issues = read_traceback(args.explain_error)
            if text is None:
                message = issues[0].message if issues else "Traceback could not be read."
                return _write_error(schema, "collection_failed", message, 1)
            report = explain_error(
                text,
                source=args.explain_error,
                intended_interpreter=args.interpreter,
                extra_issues=issues,
            )
        elif repair:
            try:
                payload = _read_report(args.repair_plan)
            except (OSError, ValueError) as exc:
                return _write_error(
                    schema,
                    "invalid_report_file",
                    f"Report could not be read ({type(exc).__name__}).",
                    2,
                )
            report = build_repair_plan(payload, args.repair_plan)
        elif environment:
            report = build_environment_report(args.environment_report, args.project)
        elif packages:
            report = inspect_packages(args.inspect_packages)
        elif comparing:
            report = compare_interpreter(args.compare_interpreter, args.project)
        elif args.discover:
            report = discover_environments(args.project)
        else:
            report = diagnose_current_environment()
    except DiscoveryInputError as exc:
        return _write_error(schema, "invalid_project_directory", str(exc), 2)
    except (OSError, ValueError) as exc:
        return _write_error(schema, "collection_failed", str(exc), 1)

    payload = report.to_dict() if hasattr(report, "to_dict") else report
    json.dump(
        payload,
        sys.stdout,
        ensure_ascii=True,
        indent=2 if args.pretty else None,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
