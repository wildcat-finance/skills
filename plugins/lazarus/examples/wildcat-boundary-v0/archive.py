#!/usr/bin/env python3
"""Build the deterministic handoff archives and their digest inventory.

    python3 plugins/lazarus/examples/wildcat-boundary-v0/archive.py \
      --v1-lazarus-release <dir> --v1-alexandria-release <dir> \
      --v2-lazarus-release <dir> --v2-alexandria-release <dir> \
      --out-dir <fresh directory> --record <fresh path> [--expect archives.json]

One uncompressed ustar archive per estate for the Lazarus release tree and one
per estate for the Alexandria release. Members are regular files only, sorted
by the UTF-8 bytes of their archive path under a top-level directory named
after the archive, with mtime 0, uid and gid 0, empty owner names and mode
0644. No compressor is involved, so rebuilding from the same trees gives the
same bytes on any host, and the inventory records every member's path, byte
count and SHA-256 beside each archive's own. ``--expect`` compares the freshly
built inventory with a committed one and exits 1 on any difference.

Each Lazarus release tree is bound to the committed capture record beside this
script by fixture digest before it is archived; a tree carrying another digest
refuses. Nothing here verifies a fixture or a release: run ``demo.py
verify-releases`` for that. The build reaches no network, writes only under
``--out-dir`` and to ``--record``, and refuses either path when it exists or
sits inside an input tree.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import sys
import tarfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATIONS = ("v1", "v2")
RECORD_SCHEMA = "wildcat-boundary-archives/v1"
CAPTURE_RECORD_SCHEMA = "wildcat-boundary-capture-record/v1"
KINDS = ("lazarus-release", "alexandria-release")
MEMBER_MODE = 0o644
FORMAT = {
    "container": "tar",
    "header": "ustar",
    "compression": "none",
    "top_level_directory": "the archive name without .tar",
    "member_order": "ascending UTF-8 bytes of the member path",
    "member_types": "regular files only; a symlink or other entry refuses the build",
    "directory_entries": False,
    "mtime": 0,
    "uid": 0,
    "gid": 0,
    "uname": "",
    "gname": "",
    "mode": "0644",
}
ESTABLISHES = (
    "Each archive's SHA-256 and byte count, and every member's path, byte count "
    "and SHA-256, as built from the release trees this run held; a rebuild from "
    "the same trees under the same format reproduces the same bytes."
)
DOES_NOT_ESTABLISH = (
    "that any copy of an archive exists outside the machine that built it, that "
    "a fixture or release verifies (demo.py verify-releases does that), or "
    "canonical-chain membership and provider independence, which no record here "
    "claims"
)


class Refusal(Exception):
    """A precondition failed before anything was written."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def real_directory(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise Refusal(f"{label} is a symlink")
    if not path.is_dir():
        raise Refusal(f"{label} is not a directory")
    return path


def fresh_path(path: Path, label: str, inputs) -> Path:
    if path.is_symlink():
        raise Refusal(f"{label} is a symlink")
    if path.exists():
        raise Refusal(f"{label} already exists")
    parent = path.absolute().parent
    if not parent.is_dir():
        raise Refusal(f"{label} has no parent directory")
    resolved = parent.resolve()
    for tree in inputs:
        root = tree.resolve()
        if resolved == root or root in resolved.parents:
            raise Refusal(f"{label} sits inside an input tree")
    return path


def regular_files(tree: Path):
    """Every regular file below ``tree`` as (archive-relative path, absolute path)."""
    found = []
    for root, directories, files in os.walk(tree, followlinks=False):
        root_path = Path(root)
        for name in directories:
            if (root_path / name).is_symlink():
                raise Refusal(f"{tree.name}: {name} is a symlink")
        for name in files:
            path = root_path / name
            if path.is_symlink() or not path.is_file():
                raise Refusal(f"{tree.name}: {path.relative_to(tree).as_posix()} is not a regular file")
            found.append((path.relative_to(tree).as_posix(), path))
    if not found:
        raise Refusal(f"{tree.name}: holds no regular file")
    return found


def load_json(path: Path, label: str):
    def refuse(token):
        raise ValueError(f"non-finite number {token}")

    try:
        return json.loads(path.read_bytes().decode("utf-8"), parse_constant=refuse)
    except (OSError, UnicodeDecodeError, ValueError) as exc:
        raise Refusal(f"{label} is not readable finite JSON: {exc}") from exc


def build_archive(entries, name: str, destination: Path) -> dict:
    """Encode the listed regular files as one ustar archive; nothing else is read."""
    prefix = name.removesuffix(".tar")
    members = []
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w", format=tarfile.USTAR_FORMAT, encoding="utf-8") as archive:
        entries = sorted(entries, key=lambda item: f"{prefix}/{item[0]}".encode("utf-8"))
        for relative, path in entries:
            data = path.read_bytes()
            info = tarfile.TarInfo(name=f"{prefix}/{relative}")
            info.size = len(data)
            info.mtime = 0
            info.mode = MEMBER_MODE
            info.uid = info.gid = 0
            info.uname = info.gname = ""
            info.type = tarfile.REGTYPE
            archive.addfile(info, io.BytesIO(data))
            members.append({"path": info.name, "bytes": len(data), "sha256": sha256_bytes(data)})
    encoded = buffer.getvalue()
    with open(destination, "xb") as handle:
        handle.write(encoded)
    return {"name": name, "bytes": len(encoded), "sha256": sha256_bytes(encoded), "member_count": len(members), "members": members}


def lazarus_entry(generation: str, tree: Path, record: dict) -> dict:
    """Read and bind a Lazarus release tree; the archive is written later."""
    document = load_json(tree / "release.json", f"{generation} release.json")
    digest = document["fixture"]["fixture_digest"]
    if digest != record["fixture"]["fixture_digest"]:
        raise Refusal(f"{generation} Lazarus release tree carries a fixture digest the committed capture record does not")
    statement = (tree / "statement.json").read_bytes()
    if sha256_bytes(statement) != document["statement"]["sha256"]:
        raise Refusal(f"{generation} Lazarus release tree's statement is not the one its document names")
    return {
        "name": f"wildcat-boundary-{generation}-lazarus-release.tar",
        "entries": regular_files(tree),
        "identity": {
            "generation": generation, "contents": "lazarus-release", "fixture_digest": digest,
            "release_digest": document["release_digest"], "statement_sha256": document["statement"]["sha256"],
        },
    }


def alexandria_entry(generation: str, tree: Path, record: dict) -> dict:
    """Read and bind an Alexandria release; the archive is written later."""
    manifest_bytes = (tree / "manifest.json").read_bytes()
    manifest = load_json(tree / "manifest.json", f"{generation} Alexandria manifest")
    captures = [c for c in manifest["captures"] if c["evidence_class"] == "proof-backed-state"]
    if len(captures) != 1 or captures[0]["source"]["reference"] != record["fixture"]["fixture_digest"]:
        raise Refusal(f"{generation} Alexandria release does not hold one proof-backed-state capture of the recorded fixture")
    return {
        "name": f"wildcat-boundary-{generation}-alexandria-release.tar",
        "entries": regular_files(tree),
        "identity": {
            "generation": generation, "contents": "alexandria-release",
            "fixture_digest": record["fixture"]["fixture_digest"],
            "release_id": manifest["release_id"], "manifest_sha256": sha256_bytes(manifest_bytes),
        },
    }


def capture_record(generation: str) -> dict:
    record = load_json(HERE / f"capture-{generation}.json", f"capture-{generation}.json")
    if record.get("schema") != CAPTURE_RECORD_SCHEMA or record.get("generation") != generation:
        raise Refusal(f"capture-{generation}.json is not the {generation} capture record")
    return record


def build(args) -> int:
    inputs = {}
    for generation in GENERATIONS:
        inputs[(generation, "lazarus-release")] = real_directory(Path(getattr(args, f"{generation}_lazarus_release")), f"{generation} Lazarus release tree")
        inputs[(generation, "alexandria-release")] = real_directory(Path(getattr(args, f"{generation}_alexandria_release")), f"{generation} Alexandria release")
    out_dir = fresh_path(Path(args.out_dir), "output directory", inputs.values())
    record_path = fresh_path(Path(args.record), "record path", inputs.values())
    expected = load_json(Path(args.expect), "expected record") if args.expect else None
    records = {generation: capture_record(generation) for generation in GENERATIONS}
    # Every tree is read, walked and bound before anything is written, so a
    # refusal leaves no output directory behind.
    planned = []
    for generation in GENERATIONS:
        planned.append(lazarus_entry(generation, inputs[(generation, "lazarus-release")], records[generation]))
        planned.append(alexandria_entry(generation, inputs[(generation, "alexandria-release")], records[generation]))
    out_dir.mkdir(mode=0o700)
    archives = []
    for item in planned:
        archive = build_archive(item["entries"], item["name"], out_dir / item["name"])
        archive.update(item["identity"])
        archives.append(archive)
    body = {
        "schema": RECORD_SCHEMA,
        "format": FORMAT,
        "establishes": ESTABLISHES,
        "does_not_establish": DOES_NOT_ESTABLISH,
        "archives": archives,
    }
    with open(record_path, "xb") as handle:
        handle.write(json.dumps(body, indent=1, sort_keys=True).encode("utf-8") + b"\n")
    for archive in archives:
        print(f"archive name={archive['name']} bytes={archive['bytes']} sha256={archive['sha256']} members={archive['member_count']}")
    if expected is not None:
        if expected.get("archives") != archives or expected.get("format") != FORMAT:
            differing = [
                built["name"] for built, known in zip(archives, expected.get("archives", []))
                if built != known
            ] or ["archive count or format"]
            print(f"archive: rebuilt inventory differs from the expected record: {', '.join(differing)}", file=sys.stderr)
            return 1
        print(f"archive: rebuilt inventory equals the expected record for {len(archives)} archives")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    for generation in GENERATIONS:
        parser.add_argument(f"--{generation}-lazarus-release", required=True, help=f"the {generation} Lazarus release tree")
        parser.add_argument(f"--{generation}-alexandria-release", required=True, help=f"the {generation} Alexandria release")
    parser.add_argument("--out-dir", required=True, help="a directory that does not exist yet")
    parser.add_argument("--record", required=True, help="a path that does not exist yet for the inventory")
    parser.add_argument("--expect", help="a committed inventory the rebuilt one must equal")
    args = parser.parse_args(argv)
    try:
        return build(args)
    except Refusal as exc:
        print(f"archive: refusing: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
