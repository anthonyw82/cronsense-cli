from __future__ import annotations

import argparse
import json
import sys

from .describe import describe
from .parser import CronValidationError, parse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronsense",
        description="Validate a cron expression and print a human-readable explanation.",
    )
    parser.add_argument(
        "expression",
        nargs="?",
        help="cron expression, e.g. '*/15 * * * *' (reads from stdin if omitted)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit machine-readable JSON instead of plain text",
    )
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    raw = args.expression if args.expression is not None else sys.stdin.read()
    stripped = raw.strip()

    try:
        cron = parse(raw)
    except CronValidationError as exc:
        if args.json:
            print(json.dumps({"valid": False, "input": stripped, "error": str(exc)}))
        else:
            print(f"invalid: {exc}", file=sys.stderr)
        return 1

    if args.json:
        payload = {
            "valid": True,
            "input": stripped,
            "normalized": str(cron),
            "fields": {
                "minute": str(cron.minute),
                "hour": str(cron.hour),
                "day_of_month": str(cron.day_of_month),
                "month": str(cron.month),
                "day_of_week": str(cron.day_of_week),
            },
            "command": cron.command,
            "description": describe(cron),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(describe(cron))
        if cron.command:
            print(f"runs: {cron.command}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
