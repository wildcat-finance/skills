#!/usr/bin/env python3
"""probitas -- a sourced counterparty dossier for undercollateralised lending.

Five subcommands:

    venues    list every venue in the registry and whether it can be checked
    collect   run the adapters over the declared addresses, write evidence.json
    render    turn an evidence file into the dossier a lender reads
    verify    check a dossier and its evidence against the five gates
    diff      compare two gate-checkable evidence files for the same subject

Exit codes: 0 success, 1 a gate was breached, 2 usage or validation error.
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from probitas_lib import registry, sanitise  # noqa: E402
from probitas_lib.adapters import (  # noqa: E402
    ADAPTER_ROUTES,
    run_adapter,
    unchecked_coverage,
)
from probitas_lib.adapters import (  # noqa: E402
    euler,
    euler_v1,
    morpho,
    morpho_midnight,
    wildcat,
)
from probitas_lib.evidence import (  # noqa: E402
    Coverage,
    Evidence,
    EvidenceError,
    Gap,
    Record,
)
from probitas_lib import delta, gates, render, statement  # noqa: E402

ADAPTERS = {
    "euler": euler.adapter,
    "euler-v1": euler_v1.adapter,
    "morpho-blue": morpho.adapter,
    "morpho-midnight": morpho_midnight.adapter,
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


def routes_for(args):
    """Which routes this invocation asked for, in the order they run.

    An archive index on its own suppresses the adapter route, exactly as it
    always has. That is deliberate rather than tidy: making an index additive
    by default would start sending requests from every command that already
    passes one, and a tool whose whole claim is provenance should not widen
    what it reaches to save a flag.
    """
    routes = []
    if args.alexandria_index is None or args.fixtures is not None or args.live:
        routes.append("fixtures" if args.fixtures else "live")
    if args.alexandria_index:
        routes.append("archive")
    return tuple(routes)


def cmd_collect(args):
    try:
        entity = sanitise.entity_name(args.entity)
        declared = [(sanitise.address(a), "declared") for a in args.address]
        inferred = [(sanitise.address(a), "inferred") for a in args.inferred or []]
    except ValueError as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2

    evidence = Evidence(entity=entity, addresses=declared + inferred, run_id=args.run_id)
    routes = routes_for(args)

    if any(route in ADAPTER_ROUTES for route in routes):
        config = {"fixtures": args.fixtures, "timeout": args.timeout}
        for venue in registry.all_venues():
            adapter = ADAPTERS.get(venue.id)
            if adapter is None:
                continue
            records, coverage = run_adapter(
                venue.id, adapter, evidence.addresses, config
            )
            for record in records:
                evidence.add_record(record)
            evidence.add_coverage(coverage)

    if args.alexandria_index:
        _collect_alexandria(args.alexandria_index, evidence)

    # Every route has now put down a row for each venue it answered for, and
    # only for those. What is left over is the venue nobody reached, and it
    # gets one row saying so rather than one per route saying the same thing.
    answered = {coverage.venue for coverage in evidence.coverage}
    for venue in registry.all_venues():
        if venue.id not in answered:
            evidence.add_coverage(unchecked_coverage(venue, routes))

    _record_gaps(evidence)
    return _write_evidence(args, evidence, routes)


def _record_gaps(evidence):
    """Name what could not be established, once per venue.

    A venue some route answered for is not a hole, even when another route
    had nothing to say about it, so a run that reached Wildcat live does not
    also report Wildcat as unchecked because the archive never held it. An
    `error` row still counts: a route that failed leaves a gap whether or not
    something else answered.
    """
    observed = {
        coverage.venue
        for coverage in evidence.coverage
        if coverage.status in ("checked", "empty")
    }
    for coverage in evidence.coverage:
        unreached = (
            coverage.status in ("unimplemented", "unconfigured")
            and coverage.venue not in observed
        )
        if coverage.status != "error" and not unreached:
            continue
        subject = f"{coverage.venue} borrowing history"
        if any(gap.subject == subject for gap in evidence.gaps):
            continue
        evidence.add_gap(
            Gap(
                subject=subject,
                reason=coverage.note or f"venue not checked ({coverage.status})",
            )
        )


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
    known = {venue.id for venue in registry.all_venues()}
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

    # Only the venues the archive actually holds. A venue this index never
    # harvested is not this route's to describe: another route may have
    # answered for it, and the shared pass below owns the ones nobody reached.
    for venue_id in sorted(by_venue):
        if venue_id not in known:
            continue
        evidence.add_coverage(Coverage(source="archive", **by_venue[venue_id]))

    for item in translated["gaps"]:
        evidence.add_gap(Gap(**item))


def _write_evidence(args, evidence, routes):
    payload = evidence.to_json()
    if args.out == "-":
        sys.stdout.write(payload)
    else:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(payload)
        # Counted over venues rather than rows. A union run holds more rows
        # than venues, and "5 of 17 venue(s) checked" would understate the
        # coverage by counting the same venue's two answers as two venues.
        venues = {c.venue for c in evidence.coverage}
        checked = {
            c.venue for c in evidence.coverage if c.status in ("checked", "empty")
        }
        print(
            f"probitas: wrote {args.out} -- {len(evidence.records)} record(s), "
            f"{len(checked)} of {len(venues)} venue(s) checked "
            f"over {len(evidence.coverage)} row(s); "
            f"routes: {_routes_line(args, routes)}",
            file=sys.stderr,
        )
    return 0


def _routes_line(args, routes):
    """Name each route the run asked for and what backed it."""
    backing = {
        "live": "the network",
        "fixtures": args.fixtures,
        "archive": args.alexandria_index,
    }
    return ", ".join(f"{route} ({backing[route]})" for route in routes)


def cmd_render(args):
    try:
        payload = render.load(args.evidence)
        # render refuses malformed evidence too, so it belongs to the same
        # bounded diagnostic as load rather than an uncaught traceback.
        document = render.render(payload)
    except (OSError, ValueError) as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2

    if args.out == "-":
        sys.stdout.write(document)
    else:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(document)
        print(f"probitas: wrote {args.out}", file=sys.stderr)
    return 0


def cmd_verify(args):
    try:
        if args.statement_out == "-":
            raise ValueError("statement output must name a file, not stdout")
        if args.statement_out is not None:
            output = os.path.realpath(os.path.abspath(args.statement_out))
            inputs = {
                os.path.realpath(os.path.abspath(args.dossier)),
                os.path.realpath(os.path.abspath(args.evidence)),
            }
            if output in inputs:
                raise ValueError("statement output must not be the dossier or evidence")

        with open(args.evidence, "rb") as handle:
            evidence_bytes = handle.read()
        payload = render.load_bytes(evidence_bytes, args.evidence)
        with open(args.dossier, "rb") as handle:
            dossier_bytes = handle.read()
        document = dossier_bytes.decode("utf-8")
        results = gates.check(document, payload)
    except (OSError, ValueError) as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2

    for gate in results:
        print(gate.line())
    breached = [g for g in results if not g.passed]
    if breached:
        print(
            f"probitas: {len(breached)} gate(s) breached; this dossier does not ship",
            file=sys.stderr,
        )
        if args.statement_out is not None:
            print(
                f"probitas: no statement was written to {args.statement_out}",
                file=sys.stderr,
            )
        return 1
    if args.statement_out is not None:
        try:
            statement.emit_statement(
                dossier_bytes,
                evidence_bytes,
                results,
                args.statement_out,
            )
        except (OSError, ValueError) as error:
            print(f"probitas: {error}", file=sys.stderr)
            return 2
        print(f"probitas: wrote statement {args.statement_out}", file=sys.stderr)
    return 0


def cmd_diff(args):
    """Write a source-preserving report over operator-designated evidence sides."""
    try:
        if delta.output_aliases_input(args.out, args.prior, args.current):
            raise delta.DeltaError(
                "change-report output must not replace either evidence input"
            )
        prior_bytes = delta.read_evidence(args.prior, "prior")
        current_bytes = delta.read_evidence(args.current, "current")
        comparison = delta.compare(
            prior_bytes,
            current_bytes,
            prior_name="prior",
            current_name="current",
        )
        body = delta.to_json(comparison) if args.json else delta.render_markdown(comparison)
        if args.out == "-":
            sys.stdout.write(body)
        else:
            delta.write_output(args.out, body)
    except delta.DeltaGateError as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 1
    except (OSError, ValueError) as error:
        print(f"probitas: {error}", file=sys.stderr)
        return 2
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
    # --fixtures and --live both name the adapter route's backing, so they
    # contradict each other. --alexandria-index names a second route and
    # combines with either; on its own it still suppresses the adapter route,
    # so no invocation that works today starts reaching the network.
    backing = collect.add_mutually_exclusive_group()
    backing.add_argument(
        "--fixtures",
        metavar="DIR",
        help="read venue responses from this directory instead of the network",
    )
    backing.add_argument(
        "--live",
        action="store_true",
        help="run the adapters against the network; needed beside "
        "--alexandria-index, and the default when no index is given",
    )
    collect.add_argument(
        "--alexandria-index",
        metavar="SQLITE",
        help="also read verified archive-backed evidence from this index",
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
    verify.add_argument(
        "--statement-out",
        metavar="PATH",
        help="write an unsigned Ariadne-readable statement after all gates pass",
    )
    verify.set_defaults(func=cmd_verify)

    diff = sub.add_parser(
        "diff",
        help="compare prior and current evidence for the same subject",
    )
    diff.add_argument("prior", help="operator-designated prior evidence file")
    diff.add_argument("current", help="operator-designated current evidence file")
    diff.add_argument(
        "--json",
        action="store_true",
        help="write the canonical JSON comparison instead of Markdown",
    )
    diff.add_argument(
        "--out",
        default="borrower-change-report.md",
        help="output path, or - for stdout",
    )
    diff.set_defaults(func=cmd_diff)

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
