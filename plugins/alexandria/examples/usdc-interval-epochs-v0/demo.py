#!/usr/bin/env python3
"""Positional implementation epochs over `alexandria-interval-receipt/v2`, offline.

`build` collects a synthetic Ethereum USDC interval whose upgrade block carries
a proxy log in an earlier transaction, the `Upgraded(address)` announcement and
a proxy log in a later transaction. It reconciles the interval against a second
fixture provider, builds a v2 release and checks it. It then builds a second v2
release from the unchanged staging bytes of `usdc-interval-live-v0` and records
both summaries. `verify` re-checks both releases, compares their owners and
identifiers with the pinned expectations, and re-runs the probes: two ordinary
logs inside the upgrade transaction, two re-digested releases with a moved
owner or boundary, the synthetic fixture's own first-block answer, and a second
provider that reports a different transaction index for one log.

Nothing here reaches a network. The synthetic chain state comes from the
immutable `usdc-interval-v0` fixture plus the literal upgrade constants below,
and the live bytes are already on disk. Probe directories are temporary and
removed on return.
"""

from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile


EXAMPLE = Path(__file__).resolve().parent
PLUGIN = EXAMPLE.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import UPGRADED_TOPIC  # noqa: E402
from alexandria_lib.paths import read_confined_file  # noqa: E402
from alexandria_lib.release import MAX_RAW_COMPONENT_BYTES, ingest  # noqa: E402
from usdc_interval import Builder, Collector, Reconciler, check_interval  # noqa: E402


SYNTHETIC = EXAMPLE.parent / "usdc-interval-v0"
SOURCE = SYNTHETIC / "fixtures" / "primary.json"
SOURCE_SHA256 = "b796d242e05813b0656c9144ec3f696611522b7a1c78edea1ff40b2ccf9b4b0c"
REGISTRY = PLUGIN / "examples" / "compound-v3-phase0-v0" / "input" / "registry.json"
LIVE = EXAMPLE.parent / "usdc-interval-live-v0"
EXPECTED = EXAMPLE / "expected.json"
LIVE_EXPECTED = EXAMPLE / "live-v2-expected.json"
CREATED_AT = "2026-09-15T00:00:00Z"
LIVE_CREATED_AT = "2026-09-07T00:00:00Z"
SUMMARY_FORMAT = "alexandria-usdc-interval-epochs-demo/v1"
SECOND_PROVIDER = "synthetic second provider"

# The literal upgrade. Block 15,331,626 opens shard 2 of the synthetic plan;
# its first log becomes the announcement, and one ordinary proxy log is placed
# in an earlier and one in a later transaction of the same block.
UPGRADE_BLOCK = 15331626
IMPLEMENTATION_A = "0x42f9505a376761b180e27a01ba0554244ed1de7d"
IMPLEMENTATION_B = "0x8b3e1f2a4c5d6e7f8091a2b3c4d5e6f708192a3b"
IMPLEMENTATION_B_CODE = "0x60806040" + "cd" * 32
ORDINARY_TOPIC = "0x" + "aa" * 32
BEFORE_TRANSACTION = "0x" + "01" * 32
AFTER_TRANSACTION = "0x" + "02" * 32
OWNERSHIP_FIELDS = (
    "block_number", "epoch_index", "kind", "log_index", "transaction_index",
)


def _read(path: Path, label: str):
    if path.is_symlink() or not path.is_file():
        raise AlexandriaError(f"the demonstration's {label} is missing at {path}")
    return load_bytes(path.read_bytes(), label)


def _built(root: Path, relative: str, label: str, max_bytes: int = MAX_CONTROL_BYTES):
    """Read one file of a build directory, which `verify` must treat as hostile.

    The read is confined below the root, refuses links and is capped, so a
    tampered manifest cannot name a file elsewhere on disk or an unbounded one.
    """
    return load_bytes(read_confined_file(root, relative, label, max_bytes=max_bytes), label, max_bytes=max_bytes)


def _fixture_provider():
    """The historical demonstration's provider, loaded by path under its own name."""
    spec = importlib.util.spec_from_file_location(
        "usdc_interval_epochs_fixture_provider", SYNTHETIC / "demo.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.FixtureProvider


def specimen(*, first_block_from_log: bool = True) -> dict:
    """The synthetic chain state: the pinned fixture plus the literal upgrade.

    The fixture answers its first block, 15,331,586, with a hash that its own
    first log in that block does not carry. V1 never compared the two; v2
    refuses the contradiction, which `historical_first_block` records. The
    specimen therefore answers that block with the log's hash.
    """
    if SOURCE.is_symlink() or not SOURCE.is_file():
        raise AlexandriaError(f"the demonstration's synthetic source is missing at {SOURCE}")
    data = SOURCE.read_bytes()
    if hashlib.sha256(data).hexdigest() != SOURCE_SHA256:
        raise AlexandriaError("the synthetic source no longer carries its pinned digest")
    state = load_bytes(data, "synthetic source")
    first = state["logs"]["0"][0]
    start = state["plan"]["interval"]["start"]
    if int(first["blockNumber"], 16) != int(start):
        raise AlexandriaError("the synthetic source's first log is not in the interval's first block")
    if first_block_from_log:
        state["blocks"][start] = first["blockHash"]
    template = state["logs"]["2"][0]
    if int(template["blockNumber"], 16) != UPGRADE_BLOCK:
        raise AlexandriaError("the synthetic source's shard 2 does not open at the upgrade block")
    upgrade = dict(
        template, data="0x", logIndex="0x4", transactionIndex="0x2",
        topics=[UPGRADED_TOPIC, "0x" + "00" * 12 + IMPLEMENTATION_B[2:]],
    )
    before = dict(
        template, data="0x", logIndex="0x3", topics=[ORDINARY_TOPIC],
        transactionHash=BEFORE_TRANSACTION, transactionIndex="0x1",
    )
    after = dict(before, logIndex="0x5", transactionHash=AFTER_TRANSACTION, transactionIndex="0x3")
    state["logs"]["2"][0:1] = [before, upgrade, after]
    state["blocks"][str(UPGRADE_BLOCK)] = template["blockHash"]
    state["slots"][str(UPGRADE_BLOCK)] = upgrade["topics"][1]
    state["code"][IMPLEMENTATION_B] = IMPLEMENTATION_B_CODE
    return state


def _component(release: Path, name: str):
    """One component of a release; callers run `check_interval` on it first."""
    manifest = _built(release, "manifest.json", "release manifest")
    for row in manifest["components"]:
        if row["name"] == name:
            return _built(release, row["object_path"], f"release {name}", MAX_RAW_COMPONENT_BYTES)
    raise AlexandriaError(f"the release carries no {name} component")


def _checked(release: Path) -> dict:
    checked = check_interval(release)
    return {
        key: checked[key]
        for key in (
            "epochs", "implementations", "interval", "receipt_semantics",
            "reconciliation", "release_id", "shard_statuses",
        )
    }


def staging_digest(root: Path) -> str:
    """One digest over every preserved staging file's relative path and bytes."""
    rows = []
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise AlexandriaError(f"the preserved staging tree holds a link at {path}")
        if path.is_file():
            rows.append([path.relative_to(root).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()])
    if not rows:
        raise AlexandriaError(f"the preserved staging tree is empty at {root}")
    return hashlib.sha256(canonical_bytes(rows)).hexdigest()


def synthetic_summary(release: Path) -> dict:
    """Check the synthetic release and name each log's owner by address."""
    checked = _checked(release)
    receipt = _component(release, "epoch-table")
    owners = [epoch["implementation"] for epoch in receipt["epochs"]]
    ownership = [
        {**{field: row[field] for field in OWNERSHIP_FIELDS}, "implementation": owners[row["epoch_index"]]}
        for row in receipt["log_attributions"]
    ]
    return {**checked, "ownership": ownership, "upgrade_block": str(UPGRADE_BLOCK)}


def live_summary(release: Path) -> dict:
    """Check the live v2 release and count its owners; its identifier binds every row."""
    checked = _checked(release)
    receipt = _component(release, "epoch-table")
    counts: dict = {}
    for row in receipt["log_attributions"]:
        per_kind = counts.setdefault(row["kind"], {})
        per_kind[str(row["epoch_index"])] = per_kind.get(str(row["epoch_index"]), 0) + 1
    boundaries = [
        {field: epoch["start_position"][field] for field in ("block_number", "log_index", "transaction_index")}
        for epoch in receipt["epochs"][1:]
    ]
    return {
        **checked,
        "attributions": counts,
        "boundaries": boundaries,
        "historical_release_id": _read(LIVE / "expected.json", "historical expectation")["release_id"],
        "staging_sha256": staging_digest(LIVE / "staging"),
    }


def _collect(state: dict, staging: Path) -> None:
    staging.mkdir(parents=True)
    provider = _fixture_provider()
    collector = Collector(state["plan"], staging, provider(state, state, provider_class="primary"))
    try:
        collector.collect()
    finally:
        # A refused collection returns before the collector closes its journals.
        collector.staging.close()


def _reconciled(state: dict, staging: Path, second: dict | None = None) -> dict:
    """Collect from the primary, then compare with a second provider's answers."""
    _collect(state, staging)
    second = state if second is None else second
    provider = _fixture_provider()
    return Reconciler(
        state["plan"], staging, provider(second, second, provider_class="second"), SECOND_PROVIDER,
    ).reconcile()["reconciliation"]


def unsupported_attribution(state: dict, workspace: Path, name: str, position: int) -> dict:
    """Put one ordinary log inside the upgrade transaction and record the refusal."""
    variant = deepcopy(state)
    logs = variant["logs"]["2"]
    logs[position].update(transactionHash=logs[1]["transactionHash"], transactionIndex=logs[1]["transactionIndex"])
    staging = workspace / name
    try:
        _collect(variant, staging)
    except AlexandriaError as error:
        receipts = (staging / "receipts" / "errors.jsonl").read_text(encoding="utf-8").splitlines()
        return {"codes": sorted({json.loads(line)["code"] for line in receipts}), "refusal": str(error)}
    raise AlexandriaError(f"the {name} specimen was placed rather than refused")


def rebound_refusal(release: Path, workspace: Path, name: str, edit) -> str:
    """Re-ingest an edited epoch table under fresh digests; `check` must refuse it."""
    manifest = _built(release, "manifest.json", "release manifest")
    source = workspace / name / "source"
    source.mkdir(parents=True)
    components = []
    for row in manifest["components"]:
        document = _component(release, row["name"])
        if row["name"] == "epoch-table":
            edit(document)
        filename = row["name"] + ".json"
        (source / filename).write_bytes(canonical_bytes(document))
        components.append(
            {key: row[key] for key in ("access", "media_type", "name", "redistribution", "role")}
            | {"path": filename}
        )
    plan = {
        "captures": [
            {key: value for key, value in capture.items() if key != "component_sha256"}
            for capture in manifest["captures"]
        ],
        "components": components,
        "format": "alexandria-capture-plan/v1",
        "release": manifest["release"],
    }
    (source / "plan.json").write_bytes(canonical_bytes(plan))
    forged = workspace / name / "release"
    ingest(source / "plan.json", forged)
    try:
        check_interval(forged)
    except AlexandriaError as error:
        return str(error)
    raise AlexandriaError(f"the {name} release was accepted")


def _move_owner(receipt: dict) -> None:
    for row in receipt["log_attributions"]:
        if row["transaction_hash"] == BEFORE_TRANSACTION:
            row["epoch_index"] = 1


def _move_boundary(receipt: dict) -> None:
    receipt["epochs"][0]["end_position"]["log_index"] += 1
    receipt["epochs"][1]["start_position"]["log_index"] += 1
    receipt["epochs"][1]["upgrade"]["log_index"] += 1


def index_only_reconciliation(state: dict, workspace: Path) -> dict:
    """A second provider that differs only in one log's transaction index."""
    second = deepcopy(state)
    primary_log = state["logs"]["2"][2]
    second["logs"]["2"][2]["transactionIndex"] = "0x7"
    record = _reconciled(state, workspace / "index-only", second)
    return {
        "disputed": len(record["disputed"]),
        "log_index": primary_log["logIndex"],
        "primary_transaction_index": primary_log["transactionIndex"],
        "second_transaction_index": second["logs"]["2"][2]["transactionIndex"],
        "status": record["status"],
    }


def historical_first_block(workspace: Path, registry) -> str:
    """Build the fixture's own first-block answer as v2 and record the refusal."""
    state = specimen(first_block_from_log=False)
    staging = workspace / "historical-first-block"
    _reconciled(state, staging)
    try:
        Builder(state["plan"], staging, registry, created_at=CREATED_AT).build(workspace / "historical-release")
    except AlexandriaError as error:
        return str(error)
    raise AlexandriaError("the fixture's contradictory first-block hash was accepted")


def probes(state: dict, release: Path, registry) -> dict:
    with tempfile.TemporaryDirectory(prefix="alexandria-epochs-demo-") as directory:
        workspace = Path(directory)
        return {
            "historical_first_block": historical_first_block(workspace, registry),
            "hostile_releases": {
                "moved-boundary": rebound_refusal(release, workspace, "moved-boundary", _move_boundary),
                "moved-owner": rebound_refusal(release, workspace, "moved-owner", _move_owner),
            },
            "index_only_reconciliation": index_only_reconciliation(state, workspace),
            "unsupported_attribution": {
                "ordinary-log-after-announcement": unsupported_attribution(state, workspace, "after", 2),
                "ordinary-log-before-announcement": unsupported_attribution(state, workspace, "before", 0),
            },
        }


class _HistoricalFixtureBuilder(Builder):
    def _reconciliation(self):
        document = super()._reconciliation()
        # This fixture predates journal binding; keep its pinned release bytes.
        document.pop("journal_sha256", None)
        for shard in document["shards"]:
            shard.pop("node_syncing", None)
        return document

    def _journal(self, name, component=None):
        document = super()._journal(name, component)
        for record in document["records"]:
            record.pop("node_syncing", None)
        return document


def build(output: Path) -> dict:
    """Collect, reconcile, build and check both v2 releases, then run the probes."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise AlexandriaError("the demonstration output already exists")
    state = specimen()
    registry = _read(REGISTRY, "pinned Comet registry")
    live_plan = _read(LIVE / "plan.json", "live interval plan")
    live_registry = _read(LIVE / "registry.json", "live registry")
    live_before = staging_digest(LIVE / "staging")

    output.mkdir(parents=True)
    try:
        staging = output / "staging"
        _reconciled(state, staging)
        _HistoricalFixtureBuilder(state["plan"], staging, registry, created_at=CREATED_AT).build(output / "synthetic-release")
        Builder(live_plan, LIVE / "staging", live_registry, created_at=LIVE_CREATED_AT).build(output / "live-release")
        if staging_digest(LIVE / "staging") != live_before:
            raise AlexandriaError("the live v2 build changed the preserved staging bytes")
        summary = {
            "format": SUMMARY_FORMAT,
            "live": live_summary(output / "live-release"),
            "synthetic": synthetic_summary(output / "synthetic-release"),
            **probes(state, output / "synthetic-release", registry),
        }
        (output / "summary.json").write_bytes(canonical_bytes(summary))
        return summary
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def verify(built: Path) -> dict:
    """Re-check both releases and re-run every probe; compare with the pins."""
    built = built.absolute()
    recorded = _built(built, "summary.json", "demonstration summary")
    if not isinstance(recorded, dict) or recorded.get("format") != SUMMARY_FORMAT:
        raise AlexandriaError("the demonstration summary has an unknown format")
    expected = _read(EXPECTED, "pinned expectation")
    live_expected = _read(LIVE_EXPECTED, "pinned live v2 expectation")
    derived = {
        "format": SUMMARY_FORMAT,
        "live": live_summary(built / "live-release"),
        "synthetic": synthetic_summary(built / "synthetic-release"),
        **probes(specimen(), built / "synthetic-release", _read(REGISTRY, "pinned Comet registry")),
    }
    if derived["live"]["release_id"] == derived["live"]["historical_release_id"]:
        raise AlexandriaError("the live v2 release reuses the historical v1 identifier")
    if canonical_bytes(derived["live"]) != canonical_bytes(live_expected):
        raise AlexandriaError("the live v2 release does not match its pinned expectation")
    pinned = {key: value for key, value in derived.items() if key != "live"}
    if canonical_bytes(pinned) != canonical_bytes(expected):
        raise AlexandriaError("the synthetic v2 release or a probe does not match the pinned expectation")
    if canonical_bytes(recorded) != canonical_bytes(derived):
        raise AlexandriaError("the recorded summary does not match the re-derived one")
    return derived


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = value.add_subparsers(dest="command", metavar="{build,verify}")
    builder = commands.add_parser("build", help="build both v2 releases offline into a new directory")
    builder.add_argument("--output", required=True, type=Path)
    verifier = commands.add_parser("verify", help="re-check both releases and every probe")
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
        print(f"usdc-interval-epochs-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
