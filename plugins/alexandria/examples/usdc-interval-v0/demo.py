#!/usr/bin/env python3
"""The resumable Ethereum USDC interval collector, end to end and offline.

`build` runs the whole path against the two checked-in fixture providers: it
collects the interval, is killed once mid-shard and resumed, reconciles against
the second provider, builds the Alexandria release and verifies it. `verify`
re-derives the release identifier and compares it with the one this example
pins.

Nothing here reaches a network. The fixture providers answer from preserved
synthetic chain state, and a test asserts no socket is opened on either path.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys


EXAMPLE = Path(__file__).resolve().parent
PLUGIN = EXAMPLE.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import discover_epochs  # noqa: E402
from usdc_interval import Builder, Collector, Reconciler, check_interval  # noqa: E402


FIXTURES = EXAMPLE / "fixtures"
EXPECTED = EXAMPLE / "expected.json"
REGISTRY = PLUGIN / "examples" / "compound-v3-phase0-v0" / "input" / "registry.json"
CREATED_AT = "2026-08-31T07:00:00Z"
KILL_AT = "shard 2 logs"
SUMMARY_FORMAT = "alexandria-usdc-interval-demo/v1"


class Interrupted(Exception):
    """The collection stopped where a killed process would have stopped."""


class FixtureProvider:
    """Answers from preserved synthetic chain state, never from a socket."""

    def __init__(self, state, *, provider_class, stop_at=None) -> None:
        self.state = state
        self.provider_class = provider_class
        self.stop_at = stop_at

    def _shard_for(self, end):
        for shard in self.state["plan"]["shards"]:
            if shard["end"] == end:
                return shard
        raise AlexandriaError(f"the fixture holds no shard ending at block {end}")

    def request(self, payload: bytes, label: str) -> bytes:
        if self.stop_at is not None and label.startswith(self.stop_at):
            raise Interrupted(label)
        envelope = json.loads(payload)
        method = envelope["method"]
        if method == "eth_getBlockByNumber":
            tag = envelope["params"][0]
            number = (
                int(self.state["plan"]["finality"]["block_number"])
                if tag in ("finalized", "safe")
                else int(tag, 16)
            )
            result = {
                "hash": self.state["blocks"][str(number)],
                "number": hex(number),
                "transactions": [],
            }
        elif method == "eth_getLogs":
            shard = self._shard_for(int(envelope["params"][0]["toBlock"], 16))
            result = self.state["logs"][str(shard["index"])]
        else:
            shard = self._shard_for(int(envelope["params"][0]["toBlock"], 16))
            result = self.state["traces"][str(shard["index"])]
        return canonical_bytes({"id": envelope["id"], "jsonrpc": "2.0", "result": result})


def _read(path: Path, label: str):
    if not path.is_file():
        raise AlexandriaError(f"the demonstration's {label} is missing at {path}")
    return load_bytes(path.read_bytes(), label)


def build(output: Path) -> dict:
    """Collect, interrupt, resume, reconcile, build and verify, in one path."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise AlexandriaError("the demonstration output already exists")
    primary_state = _read(FIXTURES / "primary.json", "primary fixture")
    secondary = _read(FIXTURES / "secondary.json", "secondary fixture")
    epoch_source = _read(FIXTURES / "epochs.json", "epoch fixture")
    registry = _read(REGISTRY, "pinned Comet registry")
    plan = primary_state["plan"]

    output.mkdir(parents=True)
    try:
        staging = output / "staging"
        staging.mkdir()

        interrupted = 0
        try:
            Collector(
                plan, staging,
                FixtureProvider(primary_state, provider_class="primary", stop_at=KILL_AT),
            ).collect()
        except Interrupted:
            interrupted = 1
        if not interrupted:
            raise AlexandriaError("the demonstration's interruption did not fire")

        resumed = Collector(
            plan, staging, FixtureProvider(primary_state, provider_class="primary")
        ).collect()

        reconciliation = Reconciler(
            plan, staging,
            FixtureProvider(primary_state, provider_class="second"),
            secondary["provider_class"],
        ).reconcile()

        epochs = discover_epochs(
            chain=plan["chain"],
            deployment=plan["deployment"],
            proxy=plan["proxy"],
            interval=plan["interval"],
            upgrade_logs=epoch_source["upgrade_logs"],
            slot_reads=epoch_source["slot_reads"],
            code_reads=epoch_source["code_reads"],
            block_hashes=epoch_source["block_hashes"],
        )

        release_id = Builder(
            plan, staging, epochs, registry, created_at=CREATED_AT
        ).build(output / "release")
        checked = check_interval(output / "release")

        summary = {
            "epochs": checked["epochs"],
            "format": SUMMARY_FORMAT,
            "interval": checked["interval"],
            "interrupted_at": KILL_AT,
            "reconciliation": reconciliation["reconciliation"]["status"],
            "release_id": release_id,
            "resumed_from_shard": resumed["resumed_from"],
            "shard_statuses": checked["shard_statuses"],
        }
        (output / "summary.json").write_bytes(canonical_bytes(summary))
        return summary
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def verify(built: Path) -> dict:
    """Re-derive the release identifier and compare it with the pinned one."""
    built = built.absolute()
    summary = _read(built / "summary.json", "demonstration summary")
    if summary.get("format") != SUMMARY_FORMAT:
        raise AlexandriaError("the demonstration summary has an unknown format")
    expected = _read(EXPECTED, "pinned expectation")
    checked = check_interval(built / "release")
    for field in ("epochs", "interval", "reconciliation", "release_id", "shard_statuses"):
        if checked[field] != expected[field]:
            raise AlexandriaError(
                f"the rebuilt release's {field} does not match the pinned expectation"
            )
        if summary[field] != expected[field]:
            raise AlexandriaError(
                f"the recorded summary's {field} does not match the pinned expectation"
            )
    if summary["resumed_from_shard"] != expected["resumed_from_shard"]:
        raise AlexandriaError("the recorded resume point does not match the pinned expectation")
    return checked


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = value.add_subparsers(dest="command", metavar="{build,verify}")
    builder = commands.add_parser("build", help="run the offline path into a new directory")
    builder.add_argument("--output", required=True, type=Path)
    verifier = commands.add_parser("verify", help="re-derive and compare the pinned identities")
    verifier.add_argument("built", type=Path)
    return value


def main(argv=None) -> int:
    value = parser()
    args = value.parse_args(argv)
    if args.command is None:
        value.print_help(sys.stderr)
        return 2
    try:
        if args.command == "build":
            sys.stdout.buffer.write(canonical_bytes(build(args.output)))
        else:
            sys.stdout.buffer.write(canonical_bytes(verify(args.built)))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"usdc-interval-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
