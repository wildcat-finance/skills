#!/usr/bin/env python3
"""Command boundary for the Alexandria lending-data archive."""

import argparse
from pathlib import Path
import sys

from alexandria_lib import (
    AlexandriaError,
    derive,
    emit_statement,
    ingest,
    query_bytes,
    rebuild,
    verify,
)
from alexandria_lib.canonical import canonical_bytes


PLANNED_COMMANDS = (
    ("ingest", "preserve raw objects and write a digest-bound release"),
    ("verify", "verify a release offline"),
    ("statement", "emit an unsigned release-evidence statement"),
    ("derive", "build the narrow Tabularium credit view"),
    ("index", "rebuild the disposable address index"),
    ("query", "query verified releases by account"),
)


def make_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Alexandria's offline lending-data archive and "
            "address-query boundary."
        )
    )
    subcommands = parser.add_subparsers(
        dest="command",
        metavar="{%s}" % ",".join(name for name, _ in PLANNED_COMMANDS),
    )
    ingest_parser = subcommands.add_parser(
        "ingest",
        help=PLANNED_COMMANDS[0][1],
        description=PLANNED_COMMANDS[0][1] + ".",
    )
    ingest_parser.add_argument("--plan", required=True, type=Path)
    ingest_parser.add_argument("--output", required=True, type=Path)
    verify_parser = subcommands.add_parser(
        "verify",
        help=PLANNED_COMMANDS[1][1],
        description=PLANNED_COMMANDS[1][1] + ".",
    )
    verify_parser.add_argument("release", type=Path)
    statement_parser = subcommands.add_parser(
        "statement",
        help=PLANNED_COMMANDS[2][1],
        description=PLANNED_COMMANDS[2][1] + ".",
    )
    statement_parser.add_argument("release", type=Path)
    statement_parser.add_argument("--output", required=True, type=Path)
    derive_parser = subcommands.add_parser(
        "derive",
        help=PLANNED_COMMANDS[3][1],
        description=PLANNED_COMMANDS[3][1] + ".",
    )
    derive_parser.add_argument("release", type=Path)
    derive_parser.add_argument("--output", required=True, type=Path)
    index_parser = subcommands.add_parser(
        "index", help=PLANNED_COMMANDS[4][1], description=PLANNED_COMMANDS[4][1] + "."
    )
    index_parser.add_argument("release", nargs="+", type=Path)
    index_parser.add_argument("--output", required=True, type=Path)
    query_parser = subcommands.add_parser(
        "query", help=PLANNED_COMMANDS[5][1], description=PLANNED_COMMANDS[5][1] + "."
    )
    query_parser.add_argument("--index", required=True, type=Path)
    query_parser.add_argument("--address", required=True, action="append")
    query_parser.add_argument("--venue", action="append", default=[])
    query_parser.add_argument("--chain")
    query_parser.add_argument("--from-time")
    query_parser.add_argument("--to-time")
    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 2
    try:
        if args.command == "ingest":
            print(ingest(args.plan, args.output))
            return 0
        if args.command == "verify":
            print(verify(args.release))
            return 0
        if args.command == "statement":
            sys.stdout.buffer.write(
                canonical_bytes(emit_statement(args.release, args.output))
            )
            return 0
        if args.command == "derive":
            print(derive(args.release, args.output))
            return 0
        if args.command == "index":
            print(rebuild(args.release, args.output))
            return 0
        if args.command == "query":
            sys.stdout.buffer.write(query_bytes(
                args.index, args.address, venues=args.venue, chain=args.chain,
                time_start=args.from_time, time_end=args.to_time,
            ))
            return 0
    except (AlexandriaError, OSError) as exc:
        print(f"alexandria: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
