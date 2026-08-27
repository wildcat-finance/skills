#!/usr/bin/env python3
"""probitas -- a sourced counterparty dossier for undercollateralised lending.

Four subcommands:

    venues    list every venue in the registry and whether it can be checked
    collect   run the adapters over the declared addresses, write evidence.json
    render    turn an evidence file into the dossier a lender reads
    verify    check a dossier and its evidence against the five gates

Exit codes: 0 success, 1 a gate was breached, 2 usage or validation error.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from probitas_lib import registry, sanitise  # noqa: E402
from probitas_lib.adapters import run_adapter, unchecked_coverage  # noqa: E402
from probitas_lib.adapters import euler, euler_v1, morpho, wildcat  # noqa: E402
from probitas_lib.evidence import (  # noqa: E402
    Coverage,
    Evidence,
    EvidenceError,
    Gap,
    Record,
)
from probitas_lib import gates, render  # noqa: E402

ADAPTERS = {
    "euler": euler.adapter,
    "euler-v1": euler_v1.adapter,
    "morpho-blue": morpho.adapter,
    "wildcat": wildcat.adapter,
}
"""Venue id to callable. Everything else in the registry is a stated gap."""


def cmd_venues(args):
    venues = registry.all_venues()
    if args.json:
        print(json.dumps([v.to_dict() for v in venues], indent=2))
        return 0

    width = max(len(v.id) for v in venues)
    for venue in venues:
        state = "implemented" if venue.implemented else "not implemented"
        auth = "" if venue.auth == "none" else f"  auth: {venue.auth}"
        print(f"{venue.id.ljust(width)}  {state}{auth}")
        print(f"{' ' * width}  {venue.note}")
    return 0


def cmd_collect(args):
    try:
        entity = sanitise.entity_name(args.entity)
        declared = [(sanitise.address(a), "declared") for a in args.address]
        inferred = [(sanitise.address(a), "inferred") for a in args.inferred or []]
    except ValueError as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2

    evidence = Evidence(entity=entity, addresses=declared + inferred, run_id=args.run_id)
    if args.alexandria_index:
        _collect_alexandria(args.alexandria_index, evidence)
        return _write_evidence(args, evidence)

    config = {"fixtures": args.fixtures, "timeout": args.timeout}

    for venue in registry.all_venues():
        adapter = ADAPTERS.get(venue.id)
        if adapter is None:
            evidence.add_coverage(unchecked_coverage(venue))
            continue
        records, coverage = run_adapter(venue.id, adapter, evidence.addresses, config)
        for record in records:
            evidence.add_record(record)
        evidence.add_coverage(coverage)

    for coverage in evidence.coverage:
        if coverage.status in ("unimplemented", "unconfigured", "error"):
            evidence.add_gap(
                Gap(
                    subject=f"{coverage.venue} borrowing history",
                    reason=coverage.note or f"venue not checked ({coverage.status})",
                )
            )

    return _write_evidence(args, evidence)


def _collect_alexandria(index_path, evidence):
    alexandria_scripts = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "alexandria", "scripts")
    )
    if alexandria_scripts not in sys.path:
        sys.path.insert(0, alexandria_scripts)
    try:
        from alexandria_lib.errors import AlexandriaError  # noqa: E402
        from alexandria_lib.probitas import translate  # noqa: E402
    except ImportError as error:
        raise EvidenceError(
            "Alexandria support is not installed beside Probitas"
        ) from error

    try:
        translated = translate(index_path, evidence.addresses)
    except (AlexandriaError, OSError) as error:
        raise EvidenceError(f"Alexandria index: {error}") from error

    by_venue = {item["venue"]: item for item in translated["coverage"]}
    for item in translated["records"]:
        address = item["address"]
        values = dict(item["values"])
        for key in [name for name in values if name.startswith("token_symbol")]:
            values[key] = sanitise.clean(values[key], max_length=32)
        evidence.add_record(Record(
            venue=item["venue"], address=address,
            provenance=evidence.addresses[address], claim=item["claim"],
            values=values, source=item["source"],
            observed_at=item["observed_at"], block=item["block"],
        ))

    for venue in registry.all_venues():
        item = by_venue.get(venue.id)
        if item is not None:
            evidence.add_coverage(Coverage(**item))
            continue
        status = "unconfigured" if venue.implemented else "unimplemented"
        evidence.add_coverage(Coverage(
            venue=venue.id, status=status, endpoint="Alexandria index",
            note="venue was not harvested into the selected Alexandria index",
        ))

    for item in translated["gaps"]:
        evidence.add_gap(Gap(**item))
    for coverage in evidence.coverage:
        if coverage.status in ("unimplemented", "unconfigured", "error"):
            subject = f"{coverage.venue} borrowing history"
            if not any(gap.subject == subject for gap in evidence.gaps):
                evidence.add_gap(Gap(
                    subject=subject,
                    reason=coverage.note or f"venue not checked ({coverage.status})",
                ))


def _write_evidence(args, evidence):
    payload = evidence.to_json()
    if args.out == "-":
        sys.stdout.write(payload)
    else:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload)
        checked = sum(1 for c in evidence.coverage if c.status in ("checked", "empty"))
        print(
            f"probitas: wrote {args.out} -- {len(evidence.records)} record(s), "
            f"{checked} of {len(evidence.coverage)} venue(s) checked",
            file=sys.stderr,
        )
    return 0


def cmd_render(args):
    try:
        payload = render.load(args.evidence)
    except (OSError, ValueError) as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2

    document = render.render(payload)
    if args.out == "-":
        sys.stdout.write(document)
    else:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(document)
        print(f"probitas: wrote {args.out}", file=sys.stderr)
    return 0


def cmd_verify(args):
    try:
        payload = render.load(args.evidence)
        with open(args.dossier, encoding="utf-8") as handle:
            document = handle.read()
    except (OSError, ValueError) as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2

    results = gates.check(document, payload)
    for gate in results:
        print(gate.line())
    breached = [g for g in results if not g.passed]
    if breached:
        print(
            f"probitas: {len(breached)} gate(s) breached; this dossier does not ship",
            file=sys.stderr,
        )
        return 1
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        prog="probitas",
        description=__doc__.split("\n\n")[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    venues = sub.add_parser("venues", help="list the venue registry")
    venues.add_argument("--json", action="store_true")
    venues.set_defaults(func=cmd_venues)

    collect = sub.add_parser("collect", help="gather evidence for a counterparty")
    collect.add_argument("--entity", required=True, help="counterparty name")
    collect.add_argument(
        "--address",
        action="append",
        required=True,
        metavar="0x...",
        help="an address the counterparty declared; repeatable",
    )
    collect.add_argument(
        "--inferred",
        action="append",
        metavar="0x...",
        help="an address suspected but not declared or provably linked; "
        "kept in its own section and never mixed with the declared ones",
    )
    sources = collect.add_mutually_exclusive_group()
    sources.add_argument(
        "--fixtures",
        metavar="DIR",
        help="read venue responses from this directory instead of the network",
    )
    sources.add_argument(
        "--alexandria-index",
        metavar="SQLITE",
        help="read verified archive-backed evidence instead of live or fixture adapters",
    )
    collect.add_argument("--run-id", default=None)
    collect.add_argument(
        "--timeout", type=int, default=30, help="per-request seconds"
    )
    collect.add_argument("--out", default="evidence.json", help="- for stdout")
    collect.set_defaults(func=cmd_collect)

    render_parser = sub.add_parser("render", help="turn evidence into a dossier")
    render_parser.add_argument("evidence")
    render_parser.add_argument("--out", default="dossier.md", help="- for stdout")
    render_parser.set_defaults(func=cmd_render)

    verify = sub.add_parser("verify", help="check a dossier against the five gates")
    verify.add_argument("dossier")
    verify.add_argument("evidence")
    verify.set_defaults(func=cmd_verify)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except EvidenceError as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
