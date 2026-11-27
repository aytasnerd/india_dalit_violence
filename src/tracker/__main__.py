"""Command line entry point: python -m tracker collect"""

from __future__ import annotations

import argparse
import logging
import sys

from . import collect


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tracker", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collect", help="fetch all sources and save new relevant articles")
    c.add_argument(
        "--dalit-times-pages",
        type=int,
        default=3,
        help="max Dalit Times pages to read (default 3; use ~40 to backfill)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    result = collect.run(dalit_times_pages=args.dalit_times_pages)
    # Fail loudly (so GitHub emails you) only if every source failed.
    return 1 if not result.ok else 0


if __name__ == "__main__":
    sys.exit(main())
