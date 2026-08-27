#!/usr/bin/env python3
"""Build and verify deterministic Tabularium credit-event releases."""

import argparse
import sys

from tabularium_lib.builder import build
from tabularium_lib.core import TabulariumError
from tabularium_lib.verifier import verify
from tabularium_lib.compound_witness import (
    build_compound_witness,
    verify_compound_witness,
)


def make_parser():
    parser = argparse.ArgumentParser(
        description="Build deterministic Tabularium credit-event JSONL."
    )
    subcommands = parser.add_subparsers(
        dest="command",
        metavar="{build,verify,compound-witness,verify-compound-witness}",
    )
    build_parser = subcommands.add_parser(
        "build", help="build canonical venue-qualified credit-event JSONL"
    )
    build_parser.add_argument(
        "--adapter",
        choices=("goldfinch", "euler-v1", "euler-v2"),
        default="goldfinch",
        help="source adapter (default: goldfinch)",
    )
    build_parser.add_argument("--source", required=True, help="preserved source JSON")
    build_parser.add_argument(
        "--capture-manifest", required=True, help="preserved capture manifest JSON"
    )
    build_parser.add_argument("--out", required=True, help="canonical JSONL output")
    build_parser.add_argument(
        "--manifest", required=True, help="coverage manifest output"
    )
    build_parser.add_argument("--release", required=True, help="release identifier")
    verify_parser = subcommands.add_parser(
        "verify",
        help="verify a release offline from its coverage manifest",
        description="Verify a release fully offline from its coverage manifest.",
    )
    verify_parser.add_argument("manifest", help="coverage manifest to verify")
    compound = subcommands.add_parser(
        "compound-witness",
        help="build non-canonical Compound Phase 0 execution facts",
    )
    compound.add_argument("--alexandria-release", required=True)
    compound.add_argument("--out", required=True)
    compound.add_argument("--manifest", required=True)
    compound_verify = subcommands.add_parser(
        "verify-compound-witness",
        help="verify Compound Phase 0 execution facts offline",
    )
    compound_verify.add_argument("--alexandria-release", required=True)
    compound_verify.add_argument("--facts", required=True)
    compound_verify.add_argument("--manifest", required=True)
    return parser


def main(argv=None):
    parser = make_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help(sys.stderr)
        return 2
    if args.command == "verify":
        try:
            report = verify(args.manifest)
        except (OSError, TabulariumError) as error:
            print("tabularium: verification failed: %s" % error, file=sys.stderr)
            return 1
        print(
            "verified %s offline: %d event(s), sha256 %s"
            % (report.release, report.rows, report.sha256)
        )
        return 0
    if args.command in ("compound-witness", "verify-compound-witness"):
        try:
            if args.command == "compound-witness":
                report = build_compound_witness(
                    args.alexandria_release, args.out, args.manifest
                )
            else:
                report = verify_compound_witness(
                    args.alexandria_release, args.facts, args.manifest
                )
        except (OSError, TabulariumError) as error:
            print("tabularium: Compound witness failed: %s" % error, file=sys.stderr)
            return 1
        print(
            "verified Compound witness offline: %d fact(s), sha256 %s"
            % (report["row_count"], report["facts_sha256"])
        )
        return 0
    try:
        report = build(
            args.source,
            args.capture_manifest,
            args.out,
            args.manifest,
            args.release,
            args.adapter,
        )
    except (OSError, TabulariumError) as error:
        print("tabularium: %s" % error, file=sys.stderr)
        return 2
    print(
        "built %d event(s): %s; sha256 %s"
        % (
            report.rows,
            ", ".join("%s=%d" % item for item in sorted(report.families.items())),
            report.sha256,
        ),
        file=sys.stderr,
    )
    print(
        "not mapped as events: %s"
        % ", ".join(
            "%s=%d" % item for item in sorted(report.unmapped_counts.items())
        ),
        file=sys.stderr,
    )
    print("coverage manifest sha256 %s" % report.manifest_sha256, file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
