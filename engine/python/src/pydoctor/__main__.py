"""Local JSON command-line entry point; no shell or subprocess is started."""

import argparse
import json
import sys
from collections.abc import Sequence

from pydoctor.environment import diagnose_current_environment


def main(argv: Sequence[str] | None = None) -> int:
    """Write one report to stdout, or a structured collection error to stderr."""
    parser = argparse.ArgumentParser(
        description="Report the current Python interpreter and environment evidence (read-only)."
    )
    parser.add_argument("--pretty", action="store_true", help="Indent the JSON report.")
    args = parser.parse_args(argv)
    try:
        report = diagnose_current_environment()
    except (OSError, ValueError) as exc:
        json.dump(
            {
                "schema_version": "1.0",
                "error": {"code": "collection_failed", "message": str(exc)},
            },
            sys.stderr,
            ensure_ascii=True,
        )
        sys.stderr.write("\n")
        return 1
    # ASCII escaping keeps JSON portable across Windows console encodings.
    json.dump(report.to_dict(), sys.stdout, ensure_ascii=True, indent=2 if args.pretty else None)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
