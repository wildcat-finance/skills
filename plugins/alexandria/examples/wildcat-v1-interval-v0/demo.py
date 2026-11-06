#!/usr/bin/env python3
"""Rebuild the preserved Wildcat V1 interval from an externally held staging tree.

The manifest binds 107 files totalling 18,665,266 bytes and their archive.
Build checks every staged file before reading it as capture input. Verify
recomputes the release; verify-preserved checks only the committed metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import os
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
EXPECTED = EXAMPLE / "expected.json"
MANIFEST = EXAMPLE / "staging-manifest.json"
RECORD = EXAMPLE / "rebuild-record.json"
STAGING_ENV_VAR = "ALEXANDRIA_WILDCAT_V1_STAGING"
CREATED_AT = "2026-09-21T20:41:36Z"
SUMMARY_FORMAT = "alexandria-wildcat-v1-interval-demo/v1"
MANIFEST_FORMAT = "alexandria-wildcat-v1-staging-manifest/v1"
RECORD_FORMAT = "alexandria-wildcat-v1-rebuild-record/v1"
COMPARED = (
    "epochs", "implementations", "interval", "receipt_semantics",
    "reconciliation", "release_id", "shard_statuses",
)
PRESERVED_COMPARED = ("epochs", "reconciliation", "release_id", "shard_statuses")


def _read(path: Path, label: str):
    """One committed JSON file, under `load_bytes`'s own control-document bounds.

    These committed documents stay within MAX_CONTROL_BYTES and MAX_NODES.
    """
    if not path.is_file() or path.is_symlink():
        raise AlexandriaError(f"the demonstration's {label} is missing at {path}")
    value = load_bytes(path.read_bytes(), label)
    if not isinstance(value, dict):
        raise AlexandriaError(f"the demonstration's {label} is not an object")
    return value


def staging_root() -> Path:
    """The unpacked staging tree's location, named by one environment variable.

    Refuses by name when the variable is unset or the path it names does not
    hold a checkpoint -- never falls back to a bundled copy, because none is
    bundled here.
    """
    value = os.environ.get(STAGING_ENV_VAR)
    if not value:
        raise AlexandriaError(
            f"{STAGING_ENV_VAR} is not set -- point it at the unpacked "
            "preserved staging tree (see this example's README) before "
            "running build"
        )
    root = Path(value)
    if not (root / "checkpoint.json").is_file():
        raise AlexandriaError(
            f"{STAGING_ENV_VAR} names {root}, which holds no checkpoint.json "
            "-- it does not look like the preserved staging tree"
        )
    return root


def _checked_manifest() -> dict:
    """The staging manifest, refused unless its own figures agree with each other."""
    manifest = _read(MANIFEST, "staging manifest")
    if manifest.get("format") != MANIFEST_FORMAT:
        raise AlexandriaError("the staging manifest has an unknown format")
    archive = manifest.get("archive")
    if not isinstance(archive, dict) or "sha256" not in archive or "bytes" not in archive:
        raise AlexandriaError("the staging manifest's archive entry is incomplete")
    def valid_digest(value):
        return isinstance(value, str) and len(value) == 64 and all(
            character in "0123456789abcdef" for character in value
        )

    if (
        not valid_digest(archive["sha256"])
        or type(archive["bytes"]) is not int or archive["bytes"] < 0
    ):
        raise AlexandriaError("the staging manifest's archive digest or byte count is malformed")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise AlexandriaError("the staging manifest names no files")
    total_bytes = 0
    seen_paths = set()
    for entry in files:
        for field in ("path", "bytes", "sha256"):
            if not isinstance(entry, dict) or field not in entry:
                raise AlexandriaError(f"a staging manifest file entry is missing {field}")
        path = entry["path"]
        if (
            not isinstance(path, str) or not path or path.startswith("/")
            or any(part in ("", ".", "..") for part in path.split("/")) or "\\" in path
            or any(ord(character) < 32 for character in path)
        ):
            raise AlexandriaError("a staging manifest file entry names an unsafe path")
        if not isinstance(entry["bytes"], int) or isinstance(entry["bytes"], bool) or entry["bytes"] < 0:
            raise AlexandriaError(f"the staging manifest's byte count for {path} is not a count")
        if not valid_digest(entry["sha256"]):
            raise AlexandriaError(f"the staging manifest's SHA-256 for {path} is malformed")
        if path in seen_paths:
            raise AlexandriaError(f"the staging manifest names {path} more than once")
        seen_paths.add(path)
        total_bytes += entry["bytes"]
    if total_bytes != manifest.get("staging_bytes_total"):
        raise AlexandriaError(
            "the staging manifest's file sizes do not sum to its declared total"
        )
    if len(files) != manifest.get("staging_files_total"):
        raise AlexandriaError(
            "the staging manifest's file count does not match its declared total"
        )
    return manifest


def verify_staging_tree(root: Path, manifest: dict) -> dict:
    """Compare every file under the unpacked tree with the manifest, before any rebuild.

    Three refusals, each by path and each before a byte of staging is read as
    input: a file the manifest does not list, a listed file the tree lacks, and
    a listed file whose byte count or SHA-256 differs. A symlink anywhere under
    the tree refuses too, because the manifest binds regular files alone.
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
    if unlisted:
        raise AlexandriaError(
            f"the staging tree holds {len(unlisted)} file(s) the manifest does not list, "
            f"first {unlisted[0]}"
        )
    missing = sorted(set(expected) - set(present))
    if missing:
        raise AlexandriaError(
            f"the staging tree lacks {len(missing)} file(s) the manifest lists, first {missing[0]}"
        )
    total = 0
    for relative in sorted(expected):
        entry = expected[relative]
        size = present[relative].stat().st_size
        if size != entry["bytes"]:
            raise AlexandriaError(f"the staging tree's {relative} differs from the manifest")
        with present[relative].open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        total += size
        if digest != entry["sha256"]:
            raise AlexandriaError(f"the staging tree's {relative} differs from the manifest")
    return {"bytes": total, "files": len(expected)}


def build(output: Path) -> dict:
    """Rebuild the release from the preserved staging tree and check it."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise AlexandriaError("the demonstration output already exists")
    plan = _read(PLAN, "interval plan")
    registry = _read(REGISTRY, "pinned venue registry")
    staging = staging_root()
    verify_staging_tree(staging, _checked_manifest())

    output.mkdir(parents=True)
    try:
        release = output / "release"
        release_id = Builder(plan, staging, registry, created_at=CREATED_AT).build(release)
        checked = check_interval(release)
        summary = {
            "epochs": checked["epochs"],
            "format": SUMMARY_FORMAT,
            "implementations": checked["implementations"],
            "interval": checked["interval"],
            "receipt_semantics": checked["receipt_semantics"],
            "reconciliation": checked["reconciliation"],
            "release_id": release_id,
            "shard_statuses": checked["shard_statuses"],
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
    for field in COMPARED:
        if field not in expected:
            raise AlexandriaError(f"the pinned expectation names no {field}")
        if checked.get(field) != expected[field]:
            raise AlexandriaError(
                f"the rebuilt release's {field} does not match the pinned expectation"
            )
        if summary.get(field) != expected[field]:
            raise AlexandriaError(
                f"the recorded summary's {field} does not match the pinned expectation"
            )
    return checked


def verify_preserved() -> dict:
    """Confirm the preserved-archive manifest and rebuild record agree with the pin.

    Needs no staging tree and reaches no network: it reads three small JSON
    files already in this directory. A missing, malformed or disagreeing
    manifest or rebuild record fails here by name, rather than only
    surfacing once someone has unpacked the externally preserved archive.
    """
    manifest = _checked_manifest()
    record = _read(RECORD, "rebuild record")
    expected = _read(EXPECTED, "pinned expectation")
    if record.get("format") != RECORD_FORMAT:
        raise AlexandriaError("the rebuild record has an unknown format")

    if record.get("archive_sha256") != manifest["archive"]["sha256"]:
        raise AlexandriaError(
            "the rebuild record binds a different archive than the staging manifest"
        )
    checked = record.get("checked")
    if not isinstance(checked, dict):
        raise AlexandriaError("the rebuild record carries no checked result")
    for field in PRESERVED_COMPARED:
        if field not in expected:
            raise AlexandriaError(f"the pinned expectation names no {field}")
        if checked.get(field) != expected[field]:
            raise AlexandriaError(
                f"the rebuild record's {field} does not match the pinned expectation"
            )
    return {"manifest": manifest, "record": record}


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = value.add_subparsers(
        dest="command", metavar="{build,verify,verify-preserved}"
    )
    builder = commands.add_parser(
        "build", help="rebuild the release from the preserved staging tree"
    )
    builder.add_argument("--output", required=True, type=Path)
    verifier = commands.add_parser("verify", help="re-derive and compare the pinned identities")
    verifier.add_argument("built", type=Path)
    commands.add_parser(
        "verify-preserved",
        help="check the staging manifest and rebuild record against the pin, no staging tree needed",
    )
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
        elif args.command == "verify-preserved":
            sys.stdout.buffer.write(canonical_bytes(verify_preserved()))
        else:
            sys.stdout.buffer.write(canonical_bytes(verify(args.built)))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"wildcat-v1-interval-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
