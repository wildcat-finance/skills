#!/usr/bin/env python3
"""pandects -- executable laws for credit contracts.

Three subcommands:

    laws   list the catalogue, with each law's applicability
    check  refuse a law missing any of the six parts that make it one
    run    search with an engine, and write down how it was searched
    render write the catalogue out as the document readers are pointed at

Exit codes: 0 success, 1 a check failed, 2 usage or validation error.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pandects_lib import catalogue as catalogue_module  # noqa: E402
from pandects_lib import checker  # noqa: E402
from pandects_lib import render as render_module  # noqa: E402
from pandects_lib import run as run_module  # noqa: E402

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CATALOGUE = os.path.join(PLUGIN_ROOT, "catalogue", "pandects.json")

CHECK_FAILED = 1
USAGE_ERROR = 2


def load(path):
    try:
        return catalogue_module.load(path)
    except catalogue_module.CatalogueError as error:
        print("%s" % error, file=sys.stderr)
        return None


def cmd_laws(args):
    found = load(args.catalogue)
    if found is None:
        return USAGE_ERROR

    if args.json:
        print(json.dumps(found.raw, indent=2))
        return 0

    if not found.laws:
        print("catalogue %s: no laws yet" % found.version)
        print("families declared: %s" % ", ".join(sorted(found.families)))
        return 0

    width = max(len(law.id) for law in found.laws)
    for law in found.laws:
        print("%s  %s" % (law.id.ljust(width), law.get("statement")))
        applicability = law.get("applicability") or {}
        print("%s  applies to: %s" % (" " * width, applicability.get("accounting_model")))
    return 0


def cmd_check(args):
    found = load(args.catalogue)
    if found is None:
        return USAGE_ERROR

    try:
        findings = checker.check(PLUGIN_ROOT, found)
    except checker.ExerciseMapError as error:
        print("%s" % error, file=sys.stderr)
        return USAGE_ERROR
    if args.json:
        print(
            json.dumps(
                {
                    "laws": len(found.laws),
                    "findings": [
                        {"law": f.law, "part": f.part, "detail": f.detail}
                        for f in findings
                    ],
                    "ok": not findings,
                },
                indent=2,
            )
        )
        return CHECK_FAILED if findings else 0

    for finding in findings:
        print(finding.line())
    if findings:
        print("%d law(s) checked, %d finding(s)" % (len(found.laws), len(findings)))
        return CHECK_FAILED
    print("%d law(s) checked, every part present" % len(found.laws))
    return 0


def cmd_run(args):
    found = load(args.catalogue)
    if found is None:
        return USAGE_ERROR

    try:
        record = run_module.search_record(
            PLUGIN_ROOT, found, match=args.match, seed=args.seed
        )
    except run_module.RunError as error:
        print("%s" % error, file=sys.stderr)
        return USAGE_ERROR

    body = json.dumps(record, indent=2)
    if args.out:
        try:
            with open(args.out, "w") as handle:
                handle.write(body + "\n")
        except OSError as error:
            print("cannot write %s: %s" % (args.out, error), file=sys.stderr)
            return USAGE_ERROR
    else:
        print(body)

    if not record["commands"]:
        print("no engine ran; the record names none", file=sys.stderr)
        return CHECK_FAILED
    failed = [
        c for c in record["commands"] if c["detail"].get("outcome") == "failed"
    ]
    if failed:
        print(
            "%d of %d campaign(s) reported a violation"
            % (len(failed), len(record["commands"])),
            file=sys.stderr,
        )
        return CHECK_FAILED
    return 0


def cmd_render(args):
    found = load(args.catalogue)
    if found is None:
        return USAGE_ERROR

    body = render_module.render(found)
    if not args.out:
        print(body, end="")
        return 0
    try:
        with open(args.out, "w") as handle:
            handle.write(body)
    except OSError as error:
        print("cannot write %s: %s" % (args.out, error), file=sys.stderr)
        return USAGE_ERROR
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="pandects", description="Executable laws for credit contracts."
    )
    subcommands = parser.add_subparsers(dest="command")

    listing = subcommands.add_parser("laws", help="list the catalogue")
    listing.add_argument("--catalogue", default=CATALOGUE)
    listing.add_argument("--json", action="store_true")
    listing.set_defaults(handler=cmd_laws)

    verify = subcommands.add_parser(
        "check", help="refuse a law missing any of its six parts"
    )
    verify.add_argument("--catalogue", default=CATALOGUE)
    verify.add_argument("--json", action="store_true")
    verify.set_defaults(handler=cmd_check)

    search = subcommands.add_parser(
        "run", help="run a campaign and write the search record"
    )
    search.add_argument("--catalogue", default=CATALOGUE)
    search.add_argument("--match", help="restrict the campaign to one contract")
    search.add_argument(
        "--seed", help="the seed the engine was given, when it takes one"
    )
    search.add_argument("--out", help="write the record here rather than to stdout")
    search.set_defaults(handler=cmd_run)

    document = subcommands.add_parser(
        "render", help="write the catalogue out as a document"
    )
    document.add_argument("--catalogue", default=CATALOGUE)
    document.add_argument(
        "--out",
        default=os.path.join(PLUGIN_ROOT, "docs", "catalogue.md"),
        help="where to write it; the shipped document by default",
    )
    document.set_defaults(handler=cmd_render)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "handler", None):
        parser.print_help()
        return USAGE_ERROR
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())
