#!/usr/bin/env python3
"""Lazarus deterministic fixture commands."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from lazarus_lib.canonical import dumps, load
from lazarus_lib.errors import LazarusError
from lazarus_lib.manifest import build_manifest, verify_manifest, write_manifest
from lazarus_lib.records import (
    read_anchor_records,
    read_proof_records,
    read_receipt_witness,
    read_rpc_records,
)
from lazarus_lib.schemas import validate_builtin_schemas, validate_document
from lazarus_lib.verifier import verify_fixture


DEFAULT_REPLAY_PORT = 8545


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="lazarus",
        description="Build and verify deterministic historical Ethereum fixtures.",
    )
    commands = root.add_subparsers(dest="command", required=True)

    validate = commands.add_parser("validate", help="validate a versioned format")
    validate.add_argument(
        "kind",
        choices=(
            "schemas",
            "plan",
            "header",
            "rpc-records",
            "proof-records",
            "anchor-records",
            "receipt-witness",
            "manifest",
            "release",
        ),
    )
    validate.add_argument("path", nargs="?", type=Path)

    build = commands.add_parser("build-manifest", help="digest fixture components")
    build.add_argument("fixture", type=Path)
    build.add_argument("--component", action="append", required=True)
    build.add_argument("--chain-id", required=True)
    build.add_argument("--block-number", required=True)
    build.add_argument("--block-hash", required=True)

    verify = commands.add_parser(
        "verify",
        help="verify fixture digests, header identity, state proofs and code",
    )
    verify.add_argument("fixture", type=Path)

    capture = commands.add_parser(
        "capture",
        help="capture one finite, fixed-block fixture from JSON-RPC",
    )
    capture.add_argument("--plan", required=True, type=Path)
    capture.add_argument("--rpc-url", required=True)
    capture.add_argument(
        "--anchor-rpc-env",
        action="append",
        default=[],
        metavar="SOURCE_ID=ENV_VAR",
        help="map one declared anchor source to a runtime RPC URL environment variable",
    )
    capture.add_argument("--out", required=True, type=Path)

    replay = commands.add_parser(
        "replay",
        help="serve a verified fixture over loopback exact-request JSON-RPC",
    )
    replay.add_argument("fixture", type=Path)
    replay.add_argument("--port", type=int, default=DEFAULT_REPLAY_PORT)

    verify_release_command = commands.add_parser(
        "verify-release",
        help="re-verify a release: its fixture, its statement and its document",
    )
    verify_release_command.add_argument("release", type=Path)

    release = commands.add_parser(
        "release",
        help="write a fixture, a statement about it, and the document binding them",
    )
    release.add_argument("fixture", type=Path)
    release.add_argument(
        "--statement",
        required=True,
        type=Path,
        help="a statement about this fixture, written by something else",
    )
    release.add_argument(
        "--out",
        required=True,
        type=Path,
        help="a directory that does not exist yet and is not inside the fixture",
    )
    return root


def _validate(kind: str, path: Path | None) -> None:
    if kind == "schemas":
        if path is not None:
            raise LazarusError("validate schemas takes no path")
        validate_builtin_schemas()
        return
    if path is None:
        raise LazarusError(f"validate {kind} requires a path")
    if kind == "rpc-records":
        read_rpc_records(path)
    elif kind == "proof-records":
        read_proof_records(path)
    elif kind == "anchor-records":
        read_anchor_records(path)
    elif kind == "receipt-witness":
        read_receipt_witness(path)
    else:
        validate_document(kind, load(path))


def run(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    if args.command == "validate":
        _validate(args.kind, args.path)
        print(f"valid {args.kind}")
        return 0
    if args.command == "build-manifest":
        manifest = build_manifest(
            args.fixture,
            args.component,
            chain_id=args.chain_id,
            block_number=args.block_number,
            block_hash=args.block_hash,
        )
        write_manifest(args.fixture, manifest)
        verified = verify_manifest(args.fixture)
        print(verified["fixture_digest"])
        return 0
    if args.command == "capture":
        from lazarus_lib.capture import (
            capture_failure_terminal_result,
            capture_fixture,
        )

        terminal_context = {}
        try:
            report = capture_fixture(
                args.plan,
                args.rpc_url,
                args.out,
                anchor_rpc_env=args.anchor_rpc_env,
                terminal_context=terminal_context,
            )
        except LazarusError as exc:
            failure = capture_failure_terminal_result(terminal_context, exc)
            if failure is None:
                raise
            print(dumps(failure).decode("utf-8"), file=sys.stderr)
            return 1
        if "terminal_result" in report:
            print(dumps(report["terminal_result"]).decode("utf-8"))
            return 0
        print(f"fixture: {report['fixture_digest']}")
        print(f"block: {report['block_hash']}")
        print(f"anchor-sources-declared: {len(args.anchor_rpc_env)}")
        print(f"chain-anchor-records: {report['chain_anchors']['records']}")
        return 0
    if args.command == "verify-release":
        from lazarus_lib.release import verify_release

        report = verify_release(args.release)
        print(f"release: {report['release_digest']}")
        print(f"fixture: {report['fixture_digest']}")
        print(f"block: {report['block_hash']}")
        print(f"statement: {report['predicate_type']}")
        print(f"proof-backed: {report['evidence_counts']['proof_backed']}")
        print(f"header-bound: {report['evidence_counts']['header_bound']}")
        print(f"recorded-rpc: {report['evidence_counts']['recorded_rpc']}")
        print("checks: " + ", ".join(report["checks"]))
        return 0
    if args.command == "release":
        from lazarus_lib.release import write_release

        document = write_release(args.fixture, args.statement, args.out)
        print(f"release: {document['release_digest']}")
        print(f"fixture: {document['fixture']['fixture_digest']}")
        print(f"statement: {document['statement']['predicate_type']}")
        counts = document["verified"]["evidence_counts"]
        print(f"proof-backed: {counts['proof_backed']}")
        print(f"header-bound: {counts['header_bound']}")
        print(f"recorded-rpc: {counts['recorded_rpc']}")
        print("checks: " + ", ".join(document["binding"]["checks"]))
        return 0
    if args.command == "replay":
        from lazarus_lib.server import serve_fixture

        try:
            serve_fixture(args.fixture, port=args.port)
        except KeyboardInterrupt:
            return 0
        return 0
    report = verify_fixture(args.fixture)
    print(f"fixture: {report['fixture_digest']}")
    print(f"block: {report['block_hash']}")
    print(f"proof-backed: {report['evidence_counts']['proof_backed']}")
    print(f"header-bound: {report['evidence_counts']['header_bound']}")
    print(f"recorded-rpc: {report['evidence_counts']['recorded_rpc']}")
    if "receipt_trie_proved" in report["evidence_counts"]:
        receipt = report["receipt_trie_proved"]
        print(f"receipt-trie-proved: {receipt['relations']}")
        print(f"receipts-root: {receipt['computed_root']}")
        print(f"receipt-count: {receipt['receipt_count']}")
        print(f"target-transaction-index: {receipt['target_transaction_index']}")
        print(f"filtered-log-count: {receipt['filtered_log_count']}")
    print(f"chain-anchor-records: {report['chain_anchors']['records']}")
    return 0


def main() -> int:
    try:
        return run()
    except LazarusError as exc:
        print(f"lazarus: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
