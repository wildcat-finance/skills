#!/usr/bin/env python3
"""The preserved live Ethereum USDC interval, rebuilt offline.

`build` reads the staging tree the live collection checked in -- the shard
journals, the opening-read journal, the checkpoint and the reconciliation
record, exactly as the two providers answered them -- runs `build` and `check`
over those bytes into a new directory, and records the summary. `verify`
re-derives the release identifier, the epoch count, the reconciliation status,
both implementation code digests and the interval's two boundary hashes, and
compares them with `expected.json`.

Nothing here reaches a network. The bytes are already on disk, and a test
asserts no socket is opened on either path. The live reads that produced them
were made once, by the runbook step that preserved this tree.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys


EXAMPLE = Path(__file__).resolve().parent
PLUGIN = EXAMPLE.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from usdc_interval import Builder, check_interval  # noqa: E402


PLAN = EXAMPLE / "plan.json"
REGISTRY = EXAMPLE / "registry.json"
STAGING = EXAMPLE / "staging"
EXPECTED = EXAMPLE / "expected.json"
CREATED_AT = "2026-09-07T00:00:00Z"
SUMMARY_FORMAT = "alexandria-usdc-interval-live-demo/v1"
COMPARED = (
    "end_hash", "epochs", "implementations", "interval", "reconciliation",
    "release_id", "shard_statuses", "start_hash",
)


def _read(path: Path, label: str):
    if not path.is_file() or path.is_symlink():
        raise AlexandriaError(f"the demonstration's {label} is missing at {path}")
    return load_bytes(path.read_bytes(), label)


def boundary_hashes(release: Path) -> dict:
    """The interval's start and end hashes, read back out of the built release.

    They come from the epoch table the release carries, whose first epoch opens
    at the block the collector read first and whose last epoch closes at the
    interval's end, so a rebuild that moved either hash fails the comparison
    rather than being described by it.
    """
    manifest = _read(release / "manifest.json", "release manifest")
    paths = {
        component["name"]: release / component["object_path"]
        for component in manifest["components"]
    }
    if "epoch-table" not in paths:
        raise AlexandriaError("the rebuilt release carries no epoch table")
    epochs = _read(paths["epoch-table"], "release epoch table")["epochs"]
    if not epochs:
        raise AlexandriaError("the rebuilt release's epoch table is empty")
    return {"end_hash": epochs[-1]["end_hash"], "start_hash": epochs[0]["start_hash"]}


class _HistoricalFixtureBuilder(Builder):
    """Reconstruct only this demonstration's immutable block-only receipt."""

    def _epochs(self, phase, end_hash):
        from usdc_interval import epochs_from_opening
        return epochs_from_opening(self.plan, phase, end_hash, legacy=True)

    def _validate_epoch_table(self, epochs, start, end):
        from alexandria_lib.interval import validate_block_epochs
        validate_block_epochs(epochs, start, end)

    def _epoch_receipt(self, phase, epochs, code_bytes, reconciliation, shards):
        import hashlib
        return {"format": "alexandria-interval-receipt/v1", "epochs": epochs,
                "implementation_code": {"component": "implementation-code",
                                        "sha256": hashlib.sha256(code_bytes).hexdigest()},
                "reconciliation": reconciliation["reconciliation"], "shards": shards}


def build(output: Path) -> dict:
    """Rebuild the release from the preserved bytes and check it, offline."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise AlexandriaError("the demonstration output already exists")
    plan = _read(PLAN, "interval plan")
    registry = _read(REGISTRY, "pinned Comet registry")
    if not (STAGING / "checkpoint.json").is_file():
        raise AlexandriaError(
            f"the demonstration's preserved staging tree is missing at {STAGING}"
        )

    output.mkdir(parents=True)
    try:
        release = output / "release"
        release_id = _HistoricalFixtureBuilder(plan, STAGING, registry, created_at=CREATED_AT).build(release)
        checked = check_interval(release)
        summary = {
            "epochs": checked["epochs"],
            "format": SUMMARY_FORMAT,
            "implementations": checked["implementations"],
            "interval": checked["interval"],
            "reconciliation": checked["reconciliation"],
            "release_id": release_id,
            "shard_statuses": checked["shard_statuses"],
            **boundary_hashes(release),
        }
        (output / "summary.json").write_bytes(canonical_bytes(summary))
        return summary
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def verify(built: Path) -> dict:
    """Re-derive every pinned identity from the rebuilt release and compare it."""
    built = built.absolute()
    summary = _read(built / "summary.json", "demonstration summary")
    if summary.get("format") != SUMMARY_FORMAT:
        raise AlexandriaError("the demonstration summary has an unknown format")
    expected = _read(EXPECTED, "pinned expectation")
    checked = check_interval(built / "release")
    derived = {**checked, **boundary_hashes(built / "release")}
    for field in COMPARED:
        if field not in expected:
            raise AlexandriaError(f"the pinned expectation names no {field}")
        if derived.get(field) != expected[field]:
            raise AlexandriaError(
                f"the rebuilt release's {field} does not match the pinned expectation"
            )
        if summary.get(field) != expected[field]:
            raise AlexandriaError(
                f"the recorded summary's {field} does not match the pinned expectation"
            )
    return derived


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = value.add_subparsers(dest="command", metavar="{build,verify}")
    builder = commands.add_parser("build", help="rebuild the release offline into a new directory")
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
        print(f"usdc-interval-live-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
