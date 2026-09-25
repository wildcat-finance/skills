#!/usr/bin/env python3
"""The preserved Aave V3 Ethereum segments, rebuilt from their staging trees.

The interval is twelve segment releases, one per plan in `segments.json`. Each
segment's staging tree is held outside this repository and bound by digest:
`segments/<index>/staging-manifest.json` binds that tree's archive by byte
count and SHA-256, and every file inside it the same way.
`segments/<index>/rebuild-record.json` records what the collecting host got
when it rebuilt the release from a fresh extraction of that archive, and
`segments/<index>/expected.json` pins what a correct rebuild produces. A
segment with no committed directory has not been preserved yet.

`build` finds the unpacked trees through `ALEXANDRIA_AAVE_V3_STAGING`, which
names a directory holding one `segment-<index>` tree per segment. Without the
variable it refuses by name. Before any rebuild it compares every file under
each tree with that segment's manifest. The rebuild itself runs with Python
socket construction denied. `verify` re-derives each pinned identity from a
directory `build` produced. `verify-preserved` needs neither the staging trees
nor the network: it checks the committed metadata against the segment table and
the pinned plan digests, and reports how many segments have a rebuild record.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import shutil
import socket
import sys
from unittest.mock import patch


EXAMPLE = Path(__file__).resolve().parent
PLUGIN = EXAMPLE.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import MAX_JOURNAL_BYTES  # noqa: E402
from alexandria_lib.paths import read_confined_file  # noqa: E402
from alexandria_lib.release import MAX_MANIFEST_NODES, MAX_RAW_COMPONENT_BYTES  # noqa: E402
from alexandria_lib.venues import aave_v3  # noqa: E402
from usdc_interval import Builder, check_interval  # noqa: E402


TABLE = EXAMPLE / "segments.json"
REGISTRY = EXAMPLE / "registry.json"
SEGMENTS = EXAMPLE / "segments"
STAGING_ENV_VAR = "ALEXANDRIA_AAVE_V3_STAGING"
SUMMARY_FORMAT = "alexandria-aave-v3-interval-demo/v1"
MANIFEST_FORMAT = "alexandria-aave-v3-staging-manifest/v1"
RECORD_FORMAT = "alexandria-aave-v3-rebuild-record/v1"
EXPECTED_FORMAT = "alexandria-aave-v3-segment-expectation/v1"
PRESERVED_FORMAT = "alexandria-aave-v3-preserved-check/v1"
# What `check_interval` returns, compared field by field with expected.json.
CHECKED = (
    "epochs", "implementations", "interval", "receipt_semantics",
    "reconciliation", "release_id", "shard_statuses",
)
# What the rebuild record carries from that result, as V2's does.
PRESERVED_COMPARED = ("epochs", "reconciliation", "release_id", "shard_statuses")
# The collected classes, one part per shard range and one record per shard.
SHARD_CLASSES = ("boundary-blocks", "logs", "traces")
# Split at the same ranges, but counted in attributions rather than shards.
RANGE_CLASSES = SHARD_CLASSES + ("log-attributions",)
CONSTRUCTED_MARKER = "declared constructed rather than collected from a chain"


def require(condition, message):
    if not condition:
        raise AlexandriaError(message)


def valid_digest(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        character in "0123456789abcdef" for character in value
    )


def _read(path: Path, label: str):
    """One committed JSON file, under `load_bytes`'s control-document bounds.

    The largest committed file here is a staging manifest, about 330,000 bytes
    and 13,000 nodes for 2,550 files, inside both default limits.
    """
    if not path.is_file() or path.is_symlink():
        raise AlexandriaError(f"the demonstration's {label} is missing at {path}")
    value = load_bytes(path.read_bytes(), label)
    if not isinstance(value, dict):
        raise AlexandriaError(f"the demonstration's {label} is not an object")
    return value


@contextmanager
def offline():
    """Deny Python socket construction for this in-process rebuild.

    This is an observed Python boundary, not operating-system isolation. The
    rebuild path launches no child process and opens no provider.
    """
    with patch.object(socket, "socket", side_effect=AlexandriaError("socket construction refused")), \
         patch.object(socket, "create_connection", side_effect=AlexandriaError("connection refused")):
        yield


def table() -> dict:
    """The pinned segment table, refused unless each row names its pinned plan."""
    value = _read(TABLE, "segment table")
    require(value.get("format") == "alexandria-aave-v3-segment-table/v1",
            "the segment table has an unknown format")
    rows = value.get("segments")
    require(isinstance(rows, list) and len(rows) == len(aave_v3.SEGMENT_PLAN_SHA256),
            "the segment table does not hold one row per pinned segment plan")
    for position, row in enumerate(rows):
        require(isinstance(row, dict) and row.get("index") == position,
                f"segment table row {position} is out of order")
        require(row.get("plan_sha256") == aave_v3.SEGMENT_PLAN_SHA256[position],
                f"segment {position}'s table digest differs from SEGMENT_PLAN_SHA256")
    return value


def plan(row: dict) -> dict:
    """One segment plan, refused unless its bytes hash to the pinned digest."""
    path = EXAMPLE / row["plan"]
    require(path.parent == EXAMPLE / "plans" and path.is_file() and not path.is_symlink(),
            f"segment {row['index']}'s plan is missing")
    data = path.read_bytes()
    require(hashlib.sha256(data).hexdigest() == row["plan_sha256"],
            f"segment {row['index']}'s plan bytes differ from the pinned digest")
    return load_bytes(data, f"segment {row['index']} plan")


def committed_indexes(rows) -> list:
    """The segments with a committed directory; anything else there refuses."""
    if not SEGMENTS.is_dir():
        return []
    known = {str(row["index"]): row["index"] for row in rows}
    found = []
    for path in sorted(SEGMENTS.iterdir()):
        if path.name.startswith(".") or path.name == "__pycache__":
            continue
        require(path.name in known and path.is_dir() and not path.is_symlink(),
                f"segments/{path.name} is not a segment the table names")
        found.append(known[path.name])
    return sorted(found)


def segment_files(index: int) -> dict:
    root = SEGMENTS / str(index)
    return {
        "manifest": _read(root / "staging-manifest.json", f"segment {index} staging manifest"),
        "record": _read(root / "rebuild-record.json", f"segment {index} rebuild record"),
        "expected": _read(root / "expected.json", f"segment {index} pinned expectation"),
    }


def checked_manifest(manifest: dict, index: int) -> dict:
    """A staging manifest, refused unless its own figures agree with each other."""
    label = f"segment {index}'s staging manifest"
    require(manifest.get("format") == MANIFEST_FORMAT, f"{label} has an unknown format")
    require(manifest.get("segment") == index, f"{label} names another segment")
    archive = manifest.get("archive")
    require(isinstance(archive, dict) and archive.get("format") == "tar+zstd"
            and valid_digest(archive.get("sha256"))
            and type(archive.get("bytes")) is int and archive["bytes"] > 0,
            f"{label}'s archive digest or byte count is malformed")
    files = manifest.get("files")
    require(isinstance(files, list) and files, f"{label} names no files")
    total, seen = 0, set()
    for entry in files:
        require(isinstance(entry, dict) and set(entry) == {"bytes", "path", "sha256"},
                f"a {label} file entry is malformed")
        path = entry["path"]
        require(isinstance(path, str) and path and not path.startswith("/")
                and not any(part in ("", ".", "..") for part in path.split("/"))
                and "\\" not in path and not any(ord(character) < 32 for character in path),
                f"a {label} file entry names an unsafe path")
        require(type(entry["bytes"]) is int and entry["bytes"] >= 0,
                f"{label}'s byte count for {path} is not a count")
        require(valid_digest(entry["sha256"]), f"{label}'s SHA-256 for {path} is malformed")
        require(path not in seen, f"{label} names {path} more than once")
        seen.add(path)
        total += entry["bytes"]
    require(total == manifest.get("staging_bytes_total"),
            f"{label}'s file sizes do not sum to its declared total")
    require(len(files) == manifest.get("staging_files_total"),
            f"{label}'s file count does not match its declared total")
    return manifest


def staging_root() -> Path:
    """The directory of unpacked trees, named by one environment variable."""
    value = os.environ.get(STAGING_ENV_VAR)
    if not value:
        raise AlexandriaError(
            f"{STAGING_ENV_VAR} is not set -- point it at the directory holding each "
            "unpacked preserved segment-<index> staging tree (see this example's README) "
            "before running build"
        )
    return Path(value)


def segment_staging(root: Path, index: int) -> Path:
    staging = root / f"segment-{index}"
    require((staging / "checkpoint.json").is_file(),
            f"{STAGING_ENV_VAR} names {root}, whose segment-{index} holds no checkpoint.json "
            "-- it does not look like that segment's preserved staging tree")
    return staging


def verify_staging_tree(root: Path, manifest: dict) -> dict:
    """Compare every file under one unpacked tree with its manifest, before any rebuild.

    Each refusal names a path: a file the manifest does not list, a listed file
    the tree lacks, a listed file whose byte count or SHA-256 differs, and a
    symlink or special file anywhere under the tree.
    """
    expected = {entry["path"]: entry for entry in manifest["files"]}
    present = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise AlexandriaError(f"the staging tree holds a symlink at {relative}")
        if path.is_file():
            present[relative] = path
        elif not path.is_dir():
            raise AlexandriaError(f"the staging tree holds a special file at {relative}")
    unlisted = sorted(set(present) - set(expected))
    require(not unlisted, f"the staging tree holds {len(unlisted)} file(s) the manifest "
            f"does not list, first {unlisted[0] if unlisted else ''}")
    missing = sorted(set(expected) - set(present))
    require(not missing, f"the staging tree lacks {len(missing)} file(s) the manifest "
            f"lists, first {missing[0] if missing else ''}")
    total = 0
    for relative in sorted(expected):
        size = present[relative].stat().st_size
        require(size == expected[relative]["bytes"],
                f"the staging tree's {relative} differs from the manifest")
        with present[relative].open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        require(digest == expected[relative]["sha256"],
                f"the staging tree's {relative} differs from the manifest")
        total += size
    return {"bytes": total, "files": len(expected)}


def evidence_classes(release: Path, release_id: str) -> dict:
    """Count each evidence class's parts, records and statuses from the manifest.

    Read only after `check_interval` verified the release, and refused unless
    this read hashes to that verified identifier under the rule `check` uses:
    the canonical bytes of the manifest without its `release_id` field.
    """
    data = read_confined_file(release, "manifest.json", "release manifest",
                              max_bytes=MAX_RAW_COMPONENT_BYTES)
    manifest = load_bytes(data, "release manifest", max_bytes=MAX_RAW_COMPONENT_BYTES,
                          max_nodes=MAX_MANIFEST_NODES)
    identity = {key: value for key, value in manifest.items() if key != "release_id"}
    digest = hashlib.sha256(canonical_bytes(identity, max_nodes=MAX_MANIFEST_NODES)).hexdigest()
    require(manifest.get("release_id") == release_id and "sha256:" + digest == release_id,
            "the release manifest differs from the verified identifier")
    classes = {}
    constructed = False
    for capture in manifest["captures"]:
        stem, _, part = capture["id"].rpartition(".")
        name = stem if stem and part.isdigit() else capture["id"]
        row = classes.setdefault(name, {"evidence_class": capture["evidence_class"],
                                        "parts": 0, "record_count": 0, "statuses": {}})
        require(row["evidence_class"] == capture["evidence_class"],
                f"the parts of {name} name different evidence classes")
        coverage = capture["coverage"]
        row["parts"] += 1
        row["record_count"] += coverage["record_count"]
        row["statuses"][coverage["status"]] = row["statuses"].get(coverage["status"], 0) + 1
        constructed = constructed or any(CONSTRUCTED_MARKER in gap for gap in coverage["gaps"])
    sizes = [row["bytes"] for row in manifest["components"]]
    return {
        "classes": classes,
        "components": {"count": len(sizes), "bytes": sum(sizes), "largest_bytes": max(sizes)},
        "constructed_staging_gap": constructed,
        "created_at": manifest["release"]["created_at"],
    }


def rebuild(plan_value: dict, staging: Path, registry: dict, created_at: str, output: Path) -> dict:
    """Build one segment release offline and derive everything `verify` compares."""
    with offline():
        release_id = Builder(plan_value, staging, registry, created_at=created_at).build(output)
        return derive(output, release_id)


def derive(release: Path, release_id: str | None = None) -> dict:
    """Check one release and add its evidence-class and component counts."""
    with offline():
        checked = check_interval(release)
    require(release_id is None or checked["release_id"] == release_id,
            "the checked release differs from the one just built")
    return {**{field: checked[field] for field in CHECKED},
            **evidence_classes(release, checked["release_id"])}


def compare(derived: dict, expected: dict, label: str) -> None:
    for field in CHECKED + ("classes", "components", "constructed_staging_gap", "created_at"):
        require(field in expected, f"segment {expected.get('segment')}'s expectation names no {field}")
        require(derived.get(field) == expected[field],
                f"the {label}'s {field} does not match the pinned expectation")


def build(output: Path) -> dict:
    """Rebuild every committed segment from its unpacked tree, then check each."""
    output = output.absolute()
    require(not output.exists() and not output.is_symlink(), "the demonstration output already exists")
    rows = table()["segments"]
    registry = _read(REGISTRY, "pinned venue registry")
    indexes = committed_indexes(rows)
    require(indexes, "no segment has committed preserved metadata to rebuild against")
    root = staging_root()
    inputs = {}
    for index in indexes:
        files = segment_files(index)
        staging = segment_staging(root, index)
        verify_staging_tree(staging, checked_manifest(files["manifest"], index))
        inputs[index] = (staging, files["expected"])
    output.mkdir(parents=True)
    try:
        summary = {"format": SUMMARY_FORMAT, "segments": {}}
        for index in indexes:
            staging, expected = inputs[index]
            target = output / f"segment-{index}"
            target.mkdir()
            derived = rebuild(plan(rows[index]), staging, registry, expected["created_at"],
                              target / "release")
            (target / "summary.json").write_bytes(canonical_bytes(derived))
            summary["segments"][str(index)] = {"release_id": derived["release_id"]}
        (output / "summary.json").write_bytes(canonical_bytes(summary))
        return summary
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def verify(built: Path) -> dict:
    """Re-derive every pinned identity from each rebuilt segment and compare it."""
    built = built.absolute()
    summary = _read(built / "summary.json", "demonstration summary")
    require(summary.get("format") == SUMMARY_FORMAT, "the demonstration summary has an unknown format")
    rows = table()["segments"]
    indexes = committed_indexes(rows)
    require(sorted(summary.get("segments", {})) == sorted(str(index) for index in indexes),
            "the build does not hold exactly the committed segments")
    result = {"format": SUMMARY_FORMAT, "segments": {}}
    for index in indexes:
        expected = segment_files(index)["expected"]
        target = built / f"segment-{index}"
        derived = derive(target / "release")
        compare(derived, expected, f"rebuilt segment {index}")
        recorded = _read(target / "summary.json", f"segment {index} summary")
        compare(recorded, expected, f"recorded segment {index} summary")
        result["segments"][str(index)] = {"release_id": derived["release_id"]}
    return result


def check_segment(row: dict, files: dict) -> dict:
    """One committed segment's manifest, record and expectation against the table."""
    index = row["index"]
    manifest = checked_manifest(files["manifest"], index)
    record, expected = files["record"], files["expected"]
    require(record.get("format") == RECORD_FORMAT, f"segment {index}'s rebuild record has an unknown format")
    require(expected.get("format") == EXPECTED_FORMAT, f"segment {index}'s expectation has an unknown format")
    for label, value in (("rebuild record", record), ("expectation", expected)):
        require(value.get("segment") == index, f"segment {index}'s {label} names another segment")
        require(value.get("plan_sha256") == row["plan_sha256"],
                f"segment {index}'s {label} binds a plan other than the pinned one")
    require(record.get("archive_sha256") == manifest["archive"]["sha256"],
            f"segment {index}'s rebuild record binds a different archive than its staging manifest")
    require(expected["interval"] == {"end": str(row["end"]), "start": str(row["start"])},
            f"segment {index}'s expected interval differs from the segment table")
    require(sum(expected["shard_statuses"].values()) == row["shards"],
            f"segment {index}'s shard statuses do not count every planned shard")
    for name in RANGE_CLASSES:
        counted = expected["classes"].get(name)
        require(counted is not None and counted["parts"] == row["ranges"]
                and sum(counted["statuses"].values()) == row["ranges"]
                and (name not in SHARD_CLASSES or counted["record_count"] == row["shards"]),
                f"segment {index}'s {name} class does not count every planned shard")
    require(expected["constructed_staging_gap"] is False,
            f"segment {index}'s release declares constructed staging")
    require(expected["components"]["largest_bytes"] <= MAX_RAW_COMPONENT_BYTES,
            f"segment {index} holds a component over the ceiling")
    journals = [entry["bytes"] for entry in manifest["files"] if entry["path"].startswith("journals/")]
    require(journals and max(journals) <= MAX_JOURNAL_BYTES, f"segment {index} holds a journal over the ceiling")
    checked = record.get("checked")
    require(isinstance(checked, dict), f"segment {index}'s rebuild record carries no checked result")
    for field in PRESERVED_COMPARED:
        require(checked.get(field) == expected.get(field),
                f"segment {index}'s rebuild record's {field} does not match the pinned expectation")
    measured = record.get("measurements")
    require(isinstance(measured, dict) and measured.get("planned", {}).get("release_bytes") == row["release_bytes"],
            f"segment {index}'s rebuild record does not carry its planned bytes")
    for stage in ("collect", "reconcile"):
        elapsed = measured.get(stage, {}).get("elapsed_seconds")
        require(type(elapsed) is int and elapsed > 0,
                f"segment {index}'s rebuild record carries no {stage} elapsed time")
    rebuild_commands = {command.get("label"): command for command in record.get("commands", [])}
    for label in ("build", "check", "verify"):
        command = rebuild_commands.get(label)
        require(command is not None and command.get("exit") == 0
                and command.get("socket_refusals") == 0 and command.get("socket_policy"),
                f"segment {index}'s rebuild record has no clean socket-denied {label}")
    return {"archive_sha256": manifest["archive"]["sha256"], "epochs": checked["epochs"],
            "reconciliation": checked["reconciliation"], "release_id": checked["release_id"],
            "shards": row["shards"]}


def verify_preserved() -> dict:
    """Check every committed segment's metadata against the pins, rebuilding nothing.

    Reads only files in this directory and reaches no network. A segment with
    no committed directory is counted as not yet preserved, never as passing.
    """
    rows = table()["segments"]
    indexes = committed_indexes(rows)
    segments = {str(index): check_segment(rows[index], segment_files(index)) for index in indexes}
    return {
        "format": PRESERVED_FORMAT,
        "rebuild_performed": False,
        "scope": "committed-metadata-only",
        "segments": segments,
        "segments_in_table": len(rows),
        "segments_with_rebuild_record": len(segments),
        "segments_without_rebuild_record": [row["index"] for row in rows if row["index"] not in indexes],
    }


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = value.add_subparsers(dest="command", metavar="{build,verify,verify-preserved}")
    builder = commands.add_parser("build", help="rebuild every committed segment from its unpacked tree")
    builder.add_argument("--output", required=True, type=Path)
    verifier = commands.add_parser("verify", help="re-derive and compare every pinned identity")
    verifier.add_argument("built", type=Path)
    commands.add_parser("verify-preserved",
                        help="check the committed metadata against the pins, no staging tree needed")
    return value


def main(argv=None) -> int:
    value = parser()
    args = value.parse_args(argv)
    if args.command is None:
        value.print_help(sys.stderr)
        return 2
    try:
        if args.command == "build":
            result = build(args.output)
        elif args.command == "verify":
            result = verify(args.built)
        else:
            result = verify_preserved()
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"aave-v3-interval-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
