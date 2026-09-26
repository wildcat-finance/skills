#!/usr/bin/env python3
"""Check the retained #1363 pair; never execute or fetch its evidence.

The fixed source and action pins detect joint omissions in derived views.
Declared review remains recorded evidence; this checker cannot verify the
reviewer's identity, source judgements, deployment state or protocol safety.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat
import sys


REPOSITORY = "wildcat-finance/v2-protocol"
ROLES = {
    "deployed": "f5a26146987926f4811b72a795d662813dedfe85",
    "candidate": "bea503c2736d47de7fd34130c64f10783dc35b39",
}
ACTION_PINS = {
    "deployed": (141, "e2c04e35b400348f1138478f8c1c545e88fc56b9f7041e4fdbcbb2d48e49e6aa"),
    "candidate": (269, "33ebdbe7c39fb7b1339d69acdfa021105e310f5fa070526607244baacf96efe2"),
}
SOURCE_PINS = {
    "deployed": (62, "b04f41a9a928435aae4dac831333a609948d0ea8101013891afdbe3898cdb48a"),
    "candidate": (108, "f43c6f8340728fe35629d6534d59d1832b1efcff039959c5b4d9e57ba8af5960"),
}
SPECIFICATION_PINS = {
    "study.md": "a2843ed9cf1dd9a44d8015d530d4caa225b0df72711df5c6fda0df15a580422c",
    "runbook.md": "9b6748b1db86d1e10cc976f07b777c2b5036b3bd2e5d1a17d779e27aca76d409",
    "design-evidence.json": "130202d63cf6fbd1c9cfa1a1ca3b5161e4976b722e897660e65b0d6dfdf397cf",
}
REPORT_NAMES = ("x-ray.md", "entry-points.md", "invariants.md", "architecture.json", "architecture.svg")
REPORT_PATHS = {f"{role}/{name}" for role in ROLES for name in REPORT_NAMES}
INVENTORY_PATHS = {f"evidence/{role}-action-denominator.json" for role in ROLES}
REVIEWED_PATHS = REPORT_PATHS | INVENTORY_PATHS | {
    "sources.json", "linkage.json", "comparison.json", "comparison.md",
    "entry-points.diff", "evidence/execution.json",
}
REQUIRED_PATHS = REVIEWED_PATHS | {
    "study.md", "runbook.md", "README.md", "design-evidence.json", "evidence/review.json",
}
DEFAULT_BUNDLE = Path(__file__).resolve().parents[1] / "docs/kickoff/1363"
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 96 * 1024 * 1024
MAX_FILES = 256
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PATH_PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")
BOUNDARY = (
    "Checks retained bytes, fixed source and action inventories, and declared review. "
    "Does not prove source semantics, reviewer identity, deployment or safety."
)


class Refusal(Exception):
    """One named failed field; input bytes remain untouched."""

    def __init__(self, code: str, path: str, detail: str):
        self.finding = {"code": code, "path": path, "detail": detail}
        super().__init__(f"{code}: {path}: {detail}")


def require(condition: bool, code: str, path: str, detail: str) -> None:
    if not condition:
        raise Refusal(code, path, detail)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def text(value: object, path: str) -> str:
    require(isinstance(value, str) and bool(value.strip()), "shape", path, "expected nonempty text")
    return value


def mapping(value: object, path: str, required: tuple[str, ...] = ()) -> dict:
    require(isinstance(value, dict), "shape", path, "expected object")
    require(set(required) <= value.keys(), "shape", path, "required field missing")
    return value


def sequence(value: object, path: str, nonempty: bool = False) -> list:
    require(isinstance(value, list), "shape", path, "expected array")
    require(not nonempty or bool(value), "shape", path, "expected nonempty array")
    return value


def relative_path(value: object, where: str) -> str:
    name = text(value, where)
    parts = name.split("/")
    require(len(name) <= 512 and len(parts) <= 8 and all(PATH_PART.fullmatch(p) for p in parts),
            "unsafe-path", where, "expected bounded portable relative path")
    require(all(p not in (".", "..") for p in parts), "unsafe-path", where, "dot component")
    return name


def sha256(value: object, where: str) -> str:
    require(isinstance(value, str) and bool(SHA256.fullmatch(value)), "shape", where, "expected SHA-256")
    return value


def integer(value: object, where: str) -> int:
    require(type(value) is int and value >= 0, "shape", where, "expected nonnegative integer")
    return value


def json_object(data: bytes, path: str) -> dict:
    def invalid_constant(_: str) -> None:
        raise ValueError("nonfinite JSON number")

    def pairs(items: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in items:
            require(key not in result, "json", path, "duplicate object key")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Refusal("json", path, "invalid or excessively nested JSON") from exc
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        require(depth <= 64, "json", path, "JSON depth exceeds 64")
        if isinstance(item, dict):
            pending.extend((v, depth + 1) for v in item.values())
        elif isinstance(item, list):
            pending.extend((v, depth + 1) for v in item)
    return mapping(value, path)


class Bundle:
    """Read regular files through held directory descriptors without following links."""

    def __init__(self, root: Path):
        self.root = root.absolute()
        require(not self.root.is_symlink(), "unsafe-path", "bundle", "bundle is a symlink")
        try:
            self.fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as exc:
            raise Refusal("read", "bundle", "cannot open bundle directory") from exc
        self.data: dict[str, bytes] = {}
        self.total = 0

    def close(self) -> None:
        os.close(self.fd)

    def read(self, name: str) -> bytes:
        relative_path(name, name)
        parent = os.dup(self.fd)
        file_fd = None
        try:
            parts = name.split("/")
            for part in parts[:-1]:
                next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = next_fd
            file_fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            before = os.fstat(file_fd)
            require(stat.S_ISREG(before.st_mode), "unsafe-path", name, "not a regular file")
            require(before.st_size <= MAX_FILE_BYTES, "limit", name, "file exceeds 16 MiB")
            with os.fdopen(file_fd, "rb", closefd=False) as stream:
                result = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(file_fd)
            identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
            named = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            require(identity(before) == identity(after) == identity(named) and len(result) == before.st_size,
                    "unstable", name, "file changed during read")
            require(len(result) <= MAX_FILE_BYTES, "limit", name, "file exceeds 16 MiB")
            return result
        except OSError as exc:
            raise Refusal("read", name, "missing, linked, unsafe or unreadable evidence") from exc
        finally:
            if file_fd is not None:
                os.close(file_fd)
            os.close(parent)

    def paths(self) -> set[str]:
        found = set()
        directories = 0

        def walk(fd: int, prefix: str = "") -> None:
            nonlocal directories
            with os.scandir(fd) as entries:
                for entry in entries:
                    name = prefix + entry.name
                    relative_path(name, name)
                    info = entry.stat(follow_symlinks=False)
                    if stat.S_ISDIR(info.st_mode):
                        directories += 1
                        require(directories <= MAX_FILES, "limit", name, "too many directories")
                        child = os.open(entry.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
                        try:
                            walk(child, name + "/")
                        finally:
                            os.close(child)
                    else:
                        require(stat.S_ISREG(info.st_mode), "unsafe-path", name, "linked or special evidence")
                        found.add(name)
                        require(len(found) <= MAX_FILES, "limit", name, "too many files")

        try:
            walk(self.fd)
        except OSError as exc:
            raise Refusal("read", "bundle", "cannot enumerate stable regular evidence") from exc
        return found

    def load(self, name: str) -> bytes:
        if name not in self.data:
            result = self.read(name)
            self.total += len(result)
            require(self.total <= MAX_TOTAL_BYTES, "limit", name, "bundle exceeds 96 MiB")
            self.data[name] = result
        return self.data[name]

    def json(self, name: str, schema: str) -> dict:
        value = json_object(self.load(name), name)
        require(value.get("schema") == schema, "schema", name, "unsupported schema")
        return value

    def finish(self) -> None:
        require(self.paths() == set(self.data), "unstable", "bundle", "file inventory changed")
        for name, previous in self.data.items():
            require(self.read(name) == previous, "unstable", name, "bytes changed during check")
        named = self.root.stat(follow_symlinks=False)
        opened = os.fstat(self.fd)
        require((named.st_dev, named.st_ino) == (opened.st_dev, opened.st_ino),
                "unstable", "bundle", "bundle directory changed")


def records(value: object, where: str, key: str = "id") -> dict[str, dict]:
    result = {}
    for index, raw in enumerate(sequence(value, where)):
        row = mapping(raw, f"{where}[{index}]", (key,))
        name = text(row[key], f"{where}[{index}].{key}")
        require(name not in result, "duplicate", where, f"duplicate {key}: {name}")
        result[name] = row
    return result


def roles(value: object, where: str) -> None:
    require(value == ROLES, "source-role", where, "source roles do not match accepted pair")


def source_refs(value: object, where: str, required: bool = True) -> None:
    for ref in sequence(value, where, required):
        text(ref, where)


def check_manifest(bundle: Bundle) -> dict[str, dict]:
    manifest = bundle.json("manifest.json", "issue-1363-manifest/v1")
    require(manifest.get("repository") == REPOSITORY, "source-role", "manifest.repository", "wrong repository")
    roles(manifest.get("roles"), "manifest.roles")
    artifacts = records(manifest.get("artifacts"), "manifest.artifacts", "path")
    require(REQUIRED_PATHS <= artifacts.keys(), "inventory", "manifest.artifacts", "required artifact missing")
    require("manifest.json" not in artifacts, "inventory", "manifest.artifacts", "manifest cannot hash itself")
    for name in artifacts:
        relative_path(name, "manifest.artifacts.path")
    require(bundle.paths() == set(artifacts) | {"manifest.json"}, "inventory", "manifest.artifacts", "declared and physical files differ")
    for name, record in artifacts.items():
        relative_path(name, "manifest.artifacts.path")
        expected = sha256(record.get("sha256"), name + ".sha256")
        size = integer(record.get("bytes"), name + ".bytes")
        data = bundle.load(name)
        require(len(data) == size and digest(data) == expected, "digest", name, "bytes or SHA-256 differ")
    return artifacts


def check_sources(bundle: Bundle) -> dict[str, dict]:
    sources = bundle.json("sources.json", "issue-1363-sources/v1")
    require(sources.get("repository") == REPOSITORY, "source-role", "sources.repository", "wrong repository")
    snapshots = mapping(sources.get("snapshots"), "sources.snapshots")
    require(set(snapshots) == set(ROLES), "source-role", "sources.snapshots", "missing or extra role")
    inventories = {}
    for role, commit in ROLES.items():
        row = mapping(snapshots[role], f"sources.{role}", ("commit", "files", "action_inventory"))
        require(row["commit"] == commit, "source-role", f"sources.{role}.commit", "wrong commit")
        files = records(row["files"], f"sources.{role}.files", "path")
        projection = []
        for name in sorted(files):
            relative_path(name, f"sources.{role}.files.path")
            require(name.startswith("src/") and name.endswith(".sol"), "source-inventory", name, "outside logical Solidity source")
            record = files[name]
            text(record.get("disposition"), name + ".disposition")
            projection.append({"path": name, "sha256": sha256(record.get("sha256"), name),
                               "bytes": integer(record.get("bytes"), name)})
        encoded = json.dumps(projection, sort_keys=True, separators=(",", ":")).encode()
        count, expected = SOURCE_PINS[role]
        require(len(files) == count and digest(encoded) == expected,
                "source-inventory", f"sources.{role}", "source projection differs from pinned Git blobs")
        path = f"evidence/{role}-action-denominator.json"
        require(row["action_inventory"] == path, "action-inventory", f"sources.{role}.action_inventory", "wrong inventory path")
        count, expected = ACTION_PINS[role]
        require(digest(bundle.load(path)) == expected, "action-inventory", path, "independent inventory pin differs")
        inventory = bundle.json(path, "issue-1363-action-denominator/v1")
        require(inventory.get("role") == role and inventory.get("commit") == commit and inventory.get("repository") == REPOSITORY,
                "source-role", path, "inventory source identity differs")
        actions = records(inventory.get("actions"), path + ".actions")
        require(len(actions) == count, "action-inventory", path, "wrong action count")
        inventories[role] = {"actions": actions, "initialization": inventory["initialization"]}
    return inventories


def check_specifications(bundle: Bundle, artifacts: dict) -> None:
    for name, expected in SPECIFICATION_PINS.items():
        require(digest(bundle.load(name)) == expected, "specification", name, "receipted specification changed")
    design = bundle.json("design-evidence.json", "protasis-design-evidence/v1")
    for result in design["results"]:
        if result["state"] == "pass":
            path = artifact_ref(result["report"], "design-evidence.results.report", artifacts)
            report = bundle.json(path, "protasis-design-report/v1")
            require(report.get("candidate") == result["candidate"] and report.get("criterion") == result["criterion"]
                    and type(report.get("exit")) is int and report["exit"] == 0,
                    "specification", path, "selection report binding differs")


def check_linkage(bundle: Bundle, inventories: dict) -> None:
    linkage = bundle.json("linkage.json", "issue-1363-linkage/v1")
    snapshots = mapping(linkage.get("snapshots"), "linkage.snapshots")
    require(set(snapshots) == set(ROLES), "source-role", "linkage.snapshots", "missing or extra role")
    for role, commit in ROLES.items():
        row = mapping(snapshots[role], f"linkage.{role}", ("commit", "actions", "initialization"))
        require(row["commit"] == commit, "source-role", f"linkage.{role}.commit", "wrong commit")
        actions = records(row["actions"], f"linkage.{role}.actions")
        require(actions.keys() == inventories[role]["actions"].keys(),
                "action-membership", f"linkage.{role}.actions", "does not equal independent action inventory")
        for name, action in actions.items():
            where = f"linkage.{role}.{name}"
            disposition = action.get("disposition")
            require(disposition in ("events", "eventless", "unresolved"), "linkage", where, "missing or unknown disposition")
            events = sequence(action.get("events"), where + ".events")
            require(disposition != "events" or bool(events), "linkage", where, "events disposition has no event")
            require(disposition != "eventless" or not events, "linkage", where, "eventless action declares events")
            for field in ("reason", "access", "value_flow"):
                text(action.get(field), where + "." + field)
            for field in ("source_refs", "effects", "call_path"):
                source_refs(action.get(field), where + "." + field)
        expected_init = {r["contract"] + ":" + r["signature"] for r in inventories[role]["initialization"]}
        actual_init = set()
        for initial in sequence(row["initialization"], f"linkage.{role}.initialization"):
            item = mapping(initial, f"linkage.{role}.initialization", ("contract", "signature", "source_refs"))
            key = text(item["contract"], "initialization.contract") + ":" + text(item["signature"], "initialization.signature")
            require(key not in actual_init, "duplicate", f"linkage.{role}.initialization", "duplicate constructor")
            actual_init.add(key)
            source_refs(item["source_refs"], f"linkage.{role}.initialization.source_refs")
        require(actual_init == expected_init, "action-membership", f"linkage.{role}.initialization", "constructor inventory differs")


def check_comparison(bundle: Bundle, inventories: dict) -> None:
    comparison = bundle.json("comparison.json", "issue-1363-comparison/v1")
    roles(comparison.get("roles"), "comparison.roles")
    actions = records(comparison.get("actions"), "comparison.actions")
    old, new = (set(inventories[role]["actions"]) for role in ROLES)
    require(set(actions) == old | new, "comparison-membership", "comparison.actions", "union of action sets differs")
    for name, action in actions.items():
        allowed = {"added"} if name not in old else {"removed"} if name not in new else {"changed", "unchanged"}
        require(action.get("status") in allowed, "comparison", name, "status contradicts action membership")
        text(action.get("reason"), name + ".reason")
        refs = mapping(action.get("source_refs"), name + ".source_refs", tuple(ROLES))
        for role, inventory in inventories.items():
            present = name in inventory["actions"]
            source_refs(refs[role], name + ".source_refs." + role, present)
            require(present or not refs[role], "comparison", name, "absent side carries source refs")
    old_text = bundle.load("deployed/entry-points.md").decode("utf-8")
    new_text = bundle.load("candidate/entry-points.md").decode("utf-8")
    expected = "".join(difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True),
                                        fromfile="deployed/entry-points.md", tofile="candidate/entry-points.md")).encode()
    require(bundle.load("entry-points.diff") == expected, "literal-diff", "entry-points.diff", "does not reproduce from both report bytes")


def artifact_ref(raw: object, where: str, artifacts: dict) -> str:
    record = mapping(raw, where, ("path", "sha256"))
    path = relative_path(record["path"], where + ".path")
    require(path in artifacts, "evidence-reference", where, "path is absent from manifest")
    require(sha256(record["sha256"], where + ".sha256") == artifacts[path]["sha256"],
            "evidence-reference", where, "digest differs from manifest")
    return path


def check_execution(bundle: Bundle, artifacts: dict) -> None:
    execution = bundle.json("evidence/execution.json", "issue-1363-execution/v1")
    expected = {(role, variant) for role in ROLES for variant in ("default", "ir-minimum")}
    found = set()
    for index, record in enumerate(sequence(execution.get("coverage"), "execution.coverage")):
        where = f"execution.coverage[{index}]"
        row = mapping(record, where)
        role = row.get("role")
        require(isinstance(role, str) and role in ROLES and row.get("commit") == ROLES[role],
                "source-role", where, "coverage role or commit differs")
        argv = row.get("argv")
        require(argv in (["forge", "coverage"], ["forge", "coverage", "--ir-minimum"]),
                "execution", where, "unexpected coverage invocation")
        key = (role, "default" if len(argv) == 2 else "ir-minimum")
        require(key not in found, "duplicate", where, "duplicate coverage invocation")
        found.add(key)
        require(type(row.get("exit")) is int and row["exit"] != 0 and row.get("status") == "failed",
                "execution", where, "retained coverage failure was changed")
        text(row.get("tool_version"), where + ".tool_version")
        text(row.get("gap"), where + ".gap")
        path = artifact_ref(row.get("log"), where + ".log", artifacts)
        require(bool(bundle.load(path)), "execution", where, "empty coverage log")
    require(found == expected, "execution", "execution.coverage", "incomplete coverage attempts")


def check_reports(bundle: Bundle, inventories: dict) -> None:
    headings = {
        "x-ray.md": ("overview", "threat", "invariant", "doc", "test", "git", "x-ray verdict"),
        "entry-points.md": ("permissionless", "role", "init", "external"),
        "invariants.md": ("enforced guards", "single-contract", "cross-contract", "economic"),
    }
    for role, commit in ROLES.items():
        for name, required in headings.items():
            path = f"{role}/{name}"
            body = bundle.load(path).decode("utf-8")
            require(commit in body, "report", path, "exact source commit missing")
            titles = "\n".join(line.lower() for line in body.splitlines() if line.startswith("#"))
            require(all(term in titles for term in required), "report", path, "required section missing")
            if name == "x-ray.md":
                require(len(body.splitlines()) < 500, "report", path, "X-Ray exceeds line budget")
            if name == "entry-points.md":
                require(all(action in body for action in inventories[role]["actions"]),
                        "report", path, "action ID missing from entry-point view")
        architecture = json_object(bundle.load(f"{role}/architecture.json"), f"{role}/architecture.json")
        text(architecture.get("title"), f"{role}/architecture.json.title")
        nodes = records(architecture.get("nodes"), f"{role}/architecture.json.nodes")
        require(bool(nodes), "report", f"{role}/architecture.json", "no architecture nodes")
        for edge in sequence(architecture.get("edges"), f"{role}/architecture.json.edges", True):
            item = mapping(edge, "architecture.edge", ("from", "to", "label"))
            start = text(item["from"], "architecture.edge.from")
            end = text(item["to"], "architecture.edge.to")
            require(start in nodes and end in nodes, "report", f"{role}/architecture.json", "edge endpoint missing")
            text(item["label"], "architecture.edge.label")
        svg = bundle.load(f"{role}/architecture.svg")
        require(b"<svg" in svg and b"</svg>" in svg, "report", f"{role}/architecture.svg", "SVG root missing")


def check_review(bundle: Bundle, inventories: dict, artifacts: dict) -> None:
    review = bundle.json("evidence/review.json", "issue-1363-review/v1")
    producer = text(review.get("producer"), "review.producer")
    reviewer = text(review.get("reviewer"), "review.reviewer")
    require(producer != reviewer and review.get("status") == "complete", "review", "review", "independent completed review absent")
    roles(review.get("roles"), "review.roles")
    text(review.get("boundary"), "review.boundary")
    reviewed = mapping(review.get("reviewed_actions"), "review.reviewed_actions", tuple(ROLES))
    for role in ROLES:
        ids = sequence(reviewed[role], "review.reviewed_actions." + role)
        require(all(isinstance(x, str) for x in ids) and len(ids) == len(set(ids))
                and set(ids) == set(inventories[role]["actions"]),
                "review", "review.reviewed_actions." + role, "reviewed action set differs")
    refs = records(review.get("artifacts"), "review.artifacts", "path")
    require(REVIEWED_PATHS <= refs.keys(), "review", "review.artifacts", "required reviewed artifact missing")
    for path, row in refs.items():
        artifact_ref(row, "review.artifacts." + path, artifacts)
    visual = mapping(review.get("visual_inspections"), "review.visual_inspections", tuple(ROLES))
    for role in ROLES:
        row = mapping(visual[role], "review.visual_inspections." + role)
        path = f"{role}/architecture.svg"
        require(row.get("status") == "inspected" and row.get("artifact") == path
                and row.get("sha256") == artifacts[path]["sha256"],
                "review", "review.visual_inspections." + role, "visual inspection missing or stale")
        text(row.get("reviewer"), "review.visual_inspections.reviewer")
        text(row.get("observations"), "review.visual_inspections.observations")


def check_bundle(root: Path = DEFAULT_BUNDLE) -> dict:
    """Return a bounded result without modifying the bundle or executing evidence."""
    bundle = None
    try:
        bundle = Bundle(root)
        artifacts = check_manifest(bundle)
        check_specifications(bundle, artifacts)
        inventories = check_sources(bundle)
        check_linkage(bundle, inventories)
        check_comparison(bundle, inventories)
        check_execution(bundle, artifacts)
        check_reports(bundle, inventories)
        check_review(bundle, inventories, artifacts)
        bundle.finish()
        return {"schema": "issue-1363-check/v1", "status": "passed", "artifacts": len(artifacts),
                "actions": {role: len(row["actions"]) for role, row in inventories.items()},
                "findings": [], "boundary": BOUNDARY}
    except Refusal as exc:
        return {"schema": "issue-1363-check/v1", "status": "failed", "findings": [exc.finding], "boundary": BOUNDARY}
    except (OSError, UnicodeError, RecursionError) as exc:
        return {"schema": "issue-1363-check/v1", "status": "failed", "findings": [
            {"code": "read", "path": "bundle", "detail": f"unreadable evidence: {type(exc).__name__}"}], "boundary": BOUNDARY}
    finally:
        if bundle is not None:
            bundle.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "conformance"):
        command = sub.add_parser(name)
        command.add_argument("--bundle", type=Path, default=DEFAULT_BUNDLE)
        if name == "conformance":
            command.add_argument("--candidate", choices=("source-bound-reports",), required=True)
            command.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(argv)
    result = check_bundle(args.bundle)
    print(json.dumps(result, sort_keys=True))
    success = result["status"] == "passed"
    if args.command == "conformance":
        command_args = ["python3", "scripts/kickoff_xray_1363.py", "conformance", "--candidate", args.candidate,
                        "--report", str(args.report)]
        if args.bundle != DEFAULT_BUNDLE:
            command_args.extend(["--bundle", str(args.bundle)])
        report = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
                  "criterion": "complete-pair", "command": shlex.join(command_args), "exit": 0 if success else 1,
                  "unit": "boolean", "value": success}
        try:
            # A caller-selected report is created once; evidence and existing reports remain untouched.
            fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                stream.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
        except OSError:
            print(json.dumps({"code": "report-write", "path": str(args.report), "detail": "report path must be new and writable"}), file=sys.stderr)
            return 1
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
