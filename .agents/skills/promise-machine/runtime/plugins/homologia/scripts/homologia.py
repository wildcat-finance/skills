#!/usr/bin/env python3
"""Homologia: does an off-chain mirror answer what the chain answers?

The scaffold ships the command surface and nothing behind it. Every verb below
is declared so the contract and the runbook can be read against a real
interface, and each one refuses rather than pretending to have compared
anything. Behaviour arrives in the runbook's later steps: input checking, then
mirror execution, then the verdict and its verification.
"""

from __future__ import annotations

import argparse
import sys

VERBS = {
    "check": "Validate a manifest, its vector sets and their expected-answer provenance.",
    "run-mirror": "Run one declared mirror over checked vectors and record its answers.",
    "compare": "Compare recorded answers against expected answers and write the verdict.",
    "render": "Render a verdict as a report, adding nothing the verdict does not carry.",
    "verify": "Recompute the verdict, its specimens and the report from the declared inputs.",
}

NOT_BUILT = 3


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="homologia",
        description=(
            "Compare one pinned on-chain computation with one pinned off-chain "
            "mirror over declared vectors. A verdict states agreement, never "
            "correctness."
        ),
    )
    parser.add_argument(
        "--version", action="version", version="homologia 0.1.0 (scaffold)"
    )
    subparsers = parser.add_subparsers(dest="verb")
    for verb, help_text in VERBS.items():
        subparsers.add_parser(verb, help=help_text)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.verb is None:
        parser.print_help()
        return 0
    # Refuse rather than answer. A verb that returned zero here would look like
    # a comparison that found nothing to report.
    print(
        f"homologia {args.verb} is not built yet: this is the scaffold "
        f"(homologia-v0.1.0). See plugins/homologia/docs/homologia-runbook.md.",
        file=sys.stderr,
    )
    return NOT_BUILT


if __name__ == "__main__":
    raise SystemExit(main())
