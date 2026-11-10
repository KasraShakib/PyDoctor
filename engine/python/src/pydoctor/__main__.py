"""Local JSON CLI for runtime observation, discovery, or explicit comparison."""

import argparse
import json
import sys
from collections.abc import Sequence

from pydoctor.comparison import compare_interpreter
from pydoctor.discovery import discover_environments
from pydoctor.discovery_sources import DiscoveryInputError
from pydoctor.environment import diagnose_current_environment


def main(argv: Sequence[str] | None = None) -> int:
    """Write one report, or a structured handled error, without target execution."""
    parser = argparse.ArgumentParser(
        description="Report read-only Python runtime and environment evidence."
    )
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON report.")
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--discover",
        action="store_true",
        help="Discover Windows Python candidates.",
    )
    modes.add_argument(
        "--compare-interpreter",
        metavar="ABSOLUTE_PATH",
        help="Compare an explicit interpreter path with discovery evidence.",
    )
    parser.add_argument(
        "--project",
        help="Explicit project directory; requires discovery or comparison mode.",
    )
    args = parser.parse_args(argv)
    comparing = args.compare_interpreter is not None
    if args.project is not None and not (args.discover or comparing):
        parser.error("--project requires --discover or --compare-interpreter")

    schema = "1.2" if comparing else "1.1" if args.discover else "1.0"
    try:
        if comparing:
            report = compare_interpreter(args.compare_interpreter, args.project)
        elif args.discover:
            report = discover_environments(args.project)
        else:
            report = diagnose_current_environment()
    except DiscoveryInputError as exc:
        json.dump(
            {
                "schema_version": schema,
                "error": {
                    "code": "invalid_project_directory",
                    "message": str(exc),
                },
            },
            sys.stderr,
            ensure_ascii=True,
        )
        sys.stderr.write("\n")
        return 2
    except (OSError, ValueError) as exc:
        json.dump(
            {
                "schema_version": schema,
                "error": {"code": "collection_failed", "message": str(exc)},
            },
            sys.stderr,
            ensure_ascii=True,
        )
        sys.stderr.write("\n")
        return 1

    json.dump(
        report.to_dict(),
        sys.stdout,
        ensure_ascii=True,
        indent=2 if args.pretty else None,
    )
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
