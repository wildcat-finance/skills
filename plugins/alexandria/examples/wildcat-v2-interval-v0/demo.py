#!/usr/bin/env python3
"""The preserved Wildcat V2 mainnet interval, rebuilt from its staging tree.

Unlike the smaller USDC demonstration beside this one, the staging tree this
release was built from is too large to carry in this repository (it holds
124 files totalling over 200MB): 3,463 shards' worth of `logs` and targeted
`trace_transaction` journals, an opening-read journal, a checkpoint and a
reconciliation record, spanning both transports Step 9 collected against.
That tree is preserved outside this repository and verified by digest --
`staging-manifest.json` binds the preserved archive's own byte count and
SHA-256 to the byte count and SHA-256 of every file inside it, and
`rebuild-record.json` is what this collecting host got when it actually
rebuilt the release from that tree, checked beside the manifest.

`build` needs the staging tree unpacked locally and reaches no network itself
-- it only reads the bytes the two transports already returned. It finds the
unpacked tree through the `ALEXANDRIA_WILDCAT_V2_STAGING` environment
variable; without it, it refuses by name rather than silently skipping.
`verify` re-derives the release identifier, the epoch count, every subject's
implementation code digest and the reconciliation status from a directory
`build` produced, and compares them with `expected.json`. `verify-preserved`
needs neither the staging tree nor the network: it checks
`staging-manifest.json` and `rebuild-record.json` against each other and
against `expected.json` alone.
"""

from __future__ import annotations

import argparse
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
STAGING_ENV_VAR = "ALEXANDRIA_WILDCAT_V2_STAGING"
CREATED_AT = "2026-09-21T11:50:00Z"
SUMMARY_FORMAT = "alexandria-wildcat-v2-interval-demo/v1"
MANIFEST_FORMAT = "alexandria-wildcat-v2-staging-manifest/v1"
RECORD_FORMAT = "alexandria-wildcat-v2-rebuild-record/v1"
COMPARED = (
    "epochs", "implementations", "interval", "receipt_semantics",
    "reconciliation", "release_id", "shard_statuses",
)
PRESERVED_COMPARED = ("epochs", "reconciliation", "release_id", "shard_statuses")


def _read(path: Path, label: str):
    if not path.is_file() or path.is_symlink():
        raise AlexandriaError(f"the demonstration's {label} is missing at {path}")
    return load_bytes(path.read_bytes(), label, max_bytes=200_000_000, max_nodes=2_000_000)


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


def build(output: Path) -> dict:
    """Rebuild the release from the preserved staging tree and check it."""
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise AlexandriaError("the demonstration output already exists")
    plan = _read(PLAN, "interval plan")
    registry = _read(REGISTRY, "pinned venue registry")
    staging = staging_root()

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
    manifest = _read(MANIFEST, "staging manifest")
    record = _read(RECORD, "rebuild record")
    expected = _read(EXPECTED, "pinned expectation")
    if manifest.get("format") != MANIFEST_FORMAT:
        raise AlexandriaError("the staging manifest has an unknown format")
    if record.get("format") != RECORD_FORMAT:
        raise AlexandriaError("the rebuild record has an unknown format")

    archive = manifest.get("archive")
    if not isinstance(archive, dict) or "sha256" not in archive or "bytes" not in archive:
        raise AlexandriaError("the staging manifest's archive entry is incomplete")
    files = manifest.get("files")
    if not isinstance(files, list) or not files:
        raise AlexandriaError("the staging manifest names no files")
    total_bytes = 0
    seen_paths = set()
    for entry in files:
        for field in ("path", "bytes", "sha256"):
            if field not in entry:
                raise AlexandriaError(f"a staging manifest file entry is missing {field}")
        if entry["path"] in seen_paths:
            raise AlexandriaError(f"the staging manifest names {entry['path']} more than once")
        seen_paths.add(entry["path"])
        total_bytes += entry["bytes"]
    if total_bytes != manifest.get("staging_bytes_total"):
        raise AlexandriaError(
            "the staging manifest's file sizes do not sum to its declared total"
        )
    if len(files) != manifest.get("staging_files_total"):
        raise AlexandriaError(
            "the staging manifest's file count does not match its declared total"
        )

    if record.get("archive_sha256") != archive["sha256"]:
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
        print(f"wildcat-v2-interval-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
