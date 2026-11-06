"""Admit saved CLI observations against an independent candidate inventory pin.

Admission checks preserved bytes and recorded executions. It neither executes a
CLI nor authenticates the recorder, provider, host or historical chain state.
"""

from __future__ import annotations

from collections import Counter
from contextvars import ContextVar
from copy import deepcopy
from datetime import datetime
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import unicodedata

if __package__:
    from .wildcat_v3_reports import EvidenceUnavailable
else:
    from wildcat_v3_reports import EvidenceUnavailable


REPO = Path(__file__).resolve().parents[3]
LOCATOR = ".hexaemeron/reports/step-4-execution-custody.json"
SUMMARY = "docs/kickoff/1378/reproduction-summary.json"
FILE_CAP = 256 * 1024 * 1024
JSON_CAP = 16 * 1024 * 1024
STREAM_CAP = 1024 * 1024
ITEM_CAP = 12000
MUTATIONS = ("party", "amount-shape", "selector", "mapping-class", "raw-source")
INPUTS = {
    "public-v1": ("wildcat-v1", "78531eabca0d8b9cbfd92ab382575645db5f9505d9ff51362bcf25edec8faa68"),
    "public-v2": ("wildcat-v2", "bfb2d4fe388fb4f803edda4613c305b1f36514ed6611b193095309ceed61c263"),
    "retained-v1": ("wildcat-v1", "eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69"),
    "retained-v2": ("wildcat-v2", "2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3"),
}
CLI = "plugins/tabularium/scripts/tabularium.py"
HEX = re.compile(r"[0-9a-f]{64}\Z")
GIT = re.compile(r"[0-9a-f]{40}\Z")
SNAPSHOT = ContextVar("wildcat_saved_custody_snapshot", default=None)
ALIASES = ContextVar("wildcat_saved_custody_aliases", default=None)


def require(condition, field):
    if not condition:
        raise EvidenceUnavailable("saved reproduction custody differs: " + field)


def closed(value, fields, field):
    require(type(value) is dict and set(value) == set(fields), field + ".shape")
    return value


def integer(value, field, maximum=2**63 - 1):
    require(type(value) is int and 0 <= value <= maximum, field)
    return value


def digest(value, field):
    require(type(value) is str and HEX.fullmatch(value) is not None, field)
    return value


def text(value, field, maximum=4096):
    require(type(value) is str and 0 < len(value.encode("utf-8")) <= maximum,
            field)
    require(unicodedata.normalize("NFC", value) == value and
            not any(ord(char) < 32 or ord(char) == 127 for char in value), field)
    return value


def relative(value, field):
    text(value, field)
    path = PurePosixPath(value)
    require(not path.is_absolute() and str(path) == value and
            not any(part in (".", "..") for part in path.parts) and
            "\\" not in value and len(path.parts) <= 32, field)
    return value


def absolute(value, field):
    text(value, field)
    path = PurePosixPath(value)
    require(path.is_absolute() and str(path) == value and
            not any(part in (".", "..") for part in path.parts) and
            "\\" not in value and len(path.parts) <= 64, field)
    return value


def _identity(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


class StableFile:
    """Hold each no-follow path component through one bounded file read."""

    def __init__(self, path):
        self.path = absolute(str(path), "file.path")
        self.parents = []
        self.descriptor = None

    def __enter__(self):
        try:
            descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            self.parents.append((descriptor, None, None, os.fstat(descriptor)))
            parts = PurePosixPath(self.path).parts[1:]
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                dir_fd=descriptor)
                self.parents.append((child, descriptor, part, os.fstat(child)))
                descriptor = child
            self.descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                                      dir_fd=descriptor)
            self.before = os.fstat(self.descriptor)
            require(stat.S_ISREG(self.before.st_mode) and self.before.st_nlink == 1,
                    "file.regular-unaliased")
            snapshot = SNAPSHOT.get()
            if snapshot is not None:
                identity = _identity(self.before)
                require(self.path not in snapshot or snapshot[self.path] == identity,
                        "file.observation-identity")
                snapshot[self.path] = identity
                aliases = ALIASES.get()
                key = (self.before.st_dev, self.before.st_ino)
                require(key not in aliases or aliases[key] == self.path, "file.path-alias")
                aliases[key] = self.path
            return self
        except Exception:
            self.close()
            raise

    def check(self):
        require(_identity(os.fstat(self.descriptor)) == _identity(self.before),
                "file.read-identity")
        parent = self.parents[-1][0]
        named = os.stat(PurePosixPath(self.path).name, dir_fd=parent, follow_symlinks=False)
        require(_identity(named) == _identity(self.before), "file.named-identity")
        for descriptor, parent, name, before in self.parents:
            require((os.fstat(descriptor).st_dev, os.fstat(descriptor).st_ino) ==
                    (before.st_dev, before.st_ino), "file.parent-identity")
            if parent is not None:
                named = os.stat(name, dir_fd=parent, follow_symlinks=False)
                require((named.st_dev, named.st_ino, named.st_mode) ==
                        (before.st_dev, before.st_ino, before.st_mode),
                        "file.parent-named-identity")

    def close(self):
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None
        for descriptor, *_ in reversed(self.parents):
            os.close(descriptor)
        self.parents = []

    def __exit__(self, *unused):
        self.close()


def read_file(path, cap=FILE_CAP, collect=True):
    with StableFile(path) as source:
        require(source.before.st_size <= cap, "file.byte-cap")
        chunks = [] if collect else None
        result = hashlib.sha256()
        size = 0
        while True:
            data = os.read(source.descriptor, 1024 * 1024)
            if not data:
                break
            size += len(data)
            require(size <= cap, "file.byte-cap")
            result.update(data)
            if collect:
                chunks.append(data)
        source.check()
        require(size == source.before.st_size, "file.size")
        claim = {"bytes": size, "sha256": result.hexdigest()}
        return (b"".join(chunks) if collect else None), claim


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "JSON.duplicate-key")
        value[key] = item
    return value


def parse_json(data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs,
                          parse_constant=lambda value: require(False, "JSON.nonfinite"))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise EvidenceUnavailable("saved reproduction JSON unavailable") from exc


def read_json(path, cap=JSON_CAP):
    data, claim = read_file(path, cap)
    return parse_json(data), claim


def byte_claim(value, field):
    closed(value, ("bytes", "sha256"), field)
    integer(value["bytes"], field + ".bytes", FILE_CAP)
    digest(value["sha256"], field + ".sha256")
    return value


def file_inventory(root):
    """Hash all regular files and reject additional empty or linked paths."""
    root = Path(absolute(str(root), "inventory.root"))
    files = []
    directories = set()

    def walk(directory, prefix=""):
        descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            before = os.fstat(descriptor)
            names = sorted(os.listdir(descriptor))
            require(bool(names), "inventory.empty-directory")
            for name in names:
                path = relative(prefix + name, "inventory.path")
                info = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    directories.add(path)
                    walk(root / path, path + "/")
                else:
                    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                            "inventory.regular-unaliased")
                    _, claim = read_file(root / path, collect=False)
                    files.append({"path": path, **claim})
                    require(_identity(os.stat(name, dir_fd=descriptor, follow_symlinks=False)) ==
                            _identity(info), "inventory.path-identity")
                require(len(files) <= ITEM_CAP, "inventory.file-cap")
            require(_identity(os.fstat(descriptor)) == _identity(before) and
                    sorted(os.listdir(descriptor)) == names, "inventory.directory-identity")
        finally:
            os.close(descriptor)

    walk(root)
    require(bool(files), "inventory.empty")
    return {"schema": "wildcat-v3-file-inventory/v1", "root": str(root),
            "files": sorted(files, key=lambda item: item["path"]),
            "bytes": sum(item["bytes"] for item in files)}


def inventory_shape(value):
    closed(value, ("schema", "root", "files", "bytes"), "file-inventory")
    require(value["schema"] == "wildcat-v3-file-inventory/v1", "file-inventory.schema")
    absolute(value["root"], "file-inventory.root")
    integer(value["bytes"], "file-inventory.bytes")
    require(type(value["files"]) is list and 0 < len(value["files"]) <= ITEM_CAP,
            "file-inventory.files")
    result = {}
    for item in value["files"]:
        closed(item, ("path", "bytes", "sha256"), "file-inventory.file")
        path = relative(item["path"], "file-inventory.file.path")
        require(path not in result, "file-inventory.duplicate-path")
        result[path] = byte_claim({key: item[key] for key in ("bytes", "sha256")}, path)
    require(list(result) == sorted(result) and value["bytes"] ==
            sum(item["bytes"] for item in result.values()), "file-inventory.total")
    return result


class Custody:
    def __init__(self, root):
        self.root = Path(absolute(str(root), "custody.root"))
        self.references = {}

    def ref(self, value, cap=JSON_CAP, json_value=True):
        closed(value, ("path", "bytes", "sha256"), "reference")
        path = relative(value["path"], "reference.path")
        claim = byte_claim({key: value[key] for key in ("bytes", "sha256")}, "reference")
        require(path not in self.references, "reference.alias")
        data, actual = read_file(self.root / path, cap)
        require(actual == claim, "reference.digest")
        self.references[path] = claim
        return parse_json(data) if json_value else data

    def inventory(self, reference, root, physical=True):
        value = self.ref(reference)
        require(value["root"] == str(root), "file-inventory.root-binding")
        claims = inventory_shape(value)
        if physical:
            require(file_inventory(root) == value, "file-inventory.current-bytes")
        return value, claims


def _pins(values, base=None):
    require(type(values) is list and 0 < len(values) <= ITEM_CAP, "pins")
    result = {}
    for value in values:
        closed(value, ("path", "bytes", "sha256"), "pin")
        path = (relative(value["path"], "pin.path") if base else
                absolute(value["path"], "pin.path"))
        full = str(base / path) if base else path
        require(full not in result, "pin.duplicate-path")
        claim = byte_claim({key: value[key] for key in ("bytes", "sha256")}, "pin")
        _, actual = read_file(full, collect=False)
        require(actual == claim, "pin.current-bytes")
        result[full] = claim
    return result


def _code_closure(code, repo):
    required = {"plugins/tabularium/scripts/tabularium.py",
                "plugins/alexandria/.claude-plugin/plugin.json"}
    for owner in ("plugins/tabularium/scripts", "plugins/alexandria/scripts"):
        required.update(path.relative_to(repo).as_posix() for path in (repo / owner).rglob("*.py")
                        if "__pycache__" not in path.parts)
    required.update("plugins/tabularium/tests/" + name for name in (
        "execute_wildcat_v3_reproduction.py", "wildcat_v3_offline_cli.py", "wildcat_v3_execution.py",
        "wildcat_v3_custody.py", "test_wildcat_v3_reproduction.py", "emit_wildcat_v3_report.py",
        "prove_wildcat_v3.py", "wildcat_v3_proofs.py", "wildcat_v3_reports.py",
        "support.py", "__init__.py"))
    require(set(code) == {str(repo / path) for path in required}, "code.complete-resource-set")


def _summary(value):
    closed(value, ("rows", "canonical_sha256", "raw_bytes", "release_bytes", "native_logs",
                   "mapping_records", "disposition_counts", "action_counts", "evidence_class_counts",
                   "context_counts"), "input.summary")
    for key in ("rows", "raw_bytes", "release_bytes", "native_logs", "mapping_records"):
        integer(value[key], "input.summary." + key)
    for key in ("disposition_counts", "action_counts", "evidence_class_counts", "context_counts"):
        require(type(value[key]) is dict and len(value[key]) <= 256, "input.summary." + key)
        for name, count in value[key].items():
            text(name, "input.summary.count-key", 256)
            integer(count, "input.summary.count-value")
    digest(value["canonical_sha256"], "input.summary.canonical_sha256")
    return value


def _counts(value, field):
    require(type(value) is dict and len(value) <= 256, field)
    for name, count in value.items():
        text(name, field + ".key", 256)
        integer(count, field + ".count")
    return value


def _datetime(value):
    text(value, "observation.utc")
    require(value.endswith("Z") or value.endswith("+00:00"), "observation.utc")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceUnavailable("saved observation UTC unavailable") from exc
    require(result.utcoffset().total_seconds() == 0, "observation.utc")
    return result


def admit(repo=REPO):
    """Check all saved operations; absent evidence never starts a subprocess."""
    snapshot = {}
    token = SNAPSHOT.set(snapshot)
    aliases_token = ALIASES.set({})
    try:
        result = _admit(Path(repo))
        for path in sorted(snapshot):
            with StableFile(path) as current:
                current.check()
        return result
    except EvidenceUnavailable:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError, OverflowError) as exc:
        raise EvidenceUnavailable("saved reproduction custody unavailable: " +
                                  type(exc).__name__) from exc
    finally:
        SNAPSHOT.reset(token)
        ALIASES.reset(aliases_token)


def _admit(repo):
    locator, _ = read_json(repo / LOCATOR)
    closed(locator, ("schema", "root", "inventory"), "locator")
    require(locator["schema"] == "wildcat-v3-custody-locator/v1", "locator.schema")
    custody = Custody(locator["root"])
    require(not custody.root.is_relative_to(repo) and
            not repo.is_relative_to(custody.root), "locator.external-root")
    closed(locator["inventory"], ("path", "bytes", "sha256"), "locator.inventory")
    require(locator["inventory"]["path"] == "inventory.json", "locator.inventory.path")
    anchor, _ = read_json(repo / SUMMARY)
    closed(anchor, ("schema", "inventory", "inputs", "operations", "mutation_refusals",
                    "network_attempts", "limits"), "public-summary")
    require(anchor["schema"] == "wildcat-v3-reproduction-summary/v1", "public-summary.schema")
    byte_claim(anchor["inventory"], "public-summary.inventory")
    require(anchor["inventory"] == {key: locator["inventory"][key]
                                     for key in ("bytes", "sha256")},
            "public-summary.independent-anchor")
    for key, count in (("operations", 52), ("mutation_refusals", 20), ("network_attempts", 0)):
        integer(anchor[key], "public-summary." + key)
        require(anchor[key] == count, "public-summary." + key)
    require(type(anchor["limits"]) is list and 1 <= len(anchor["limits"]) <= 32,
            "public-summary.limits")
    for limit in anchor["limits"]:
        text(limit, "public-summary.limit")
    require(type(anchor["inputs"]) is list and len(anchor["inputs"]) == 4, "public-summary.inputs")
    summary_fields = ("rows", "canonical_sha256", "raw_bytes", "release_bytes", "native_logs", "mapping_records",
                      "disposition_counts", "action_counts", "evidence_class_counts", "context_counts")
    for item in anchor["inputs"]:
        closed(item, ("label", "raw_release_id", "adapter", *summary_fields), "public-summary.input")
        _summary({key: item[key] for key in summary_fields})
    inventory = custody.ref(locator["inventory"])
    closed(inventory, ("schema", "source", "code_pins", "runtime", "guard", "executor",
                       "inputs", "operations", "mutations", "guard_diagnostics"), "custody")
    require(inventory["schema"] == "wildcat-v3-execution-custody/v1", "custody.schema")
    source = closed(inventory["source"], ("root", "head", "tree", "fingerprint"), "source")
    absolute(source["root"], "source.root")
    require(Path(source["root"]).samefile(repo), "source.root-binding")
    for key in ("head", "tree"):
        require(type(source[key]) is str and GIT.fullmatch(source[key]), "source." + key)
    info = repo.stat()
    require(source["fingerprint"] == "issue/" + str(info.st_dev) + "-" + str(info.st_ino),
            "source.fingerprint")
    code = _pins(inventory["code_pins"], repo)
    _code_closure(code, repo)
    for key, filename in (("guard", "wildcat_v3_offline_cli.py"),
                          ("executor", "execute_wildcat_v3_reproduction.py")):
        value = inventory[key]
        closed(value, ("path", "bytes", "sha256"), key)
        path = relative(value["path"], key + ".path")
        require(path == "plugins/tabularium/tests/" + filename, key + ".owner-path")
        require(code.get(str(repo / path)) == {name: value[name] for name in ("bytes", "sha256")},
                key + ".code-pin")
    runtime = closed(inventory["runtime"], ("executable", "version", "pins"), "runtime")
    absolute(runtime["executable"], "runtime.executable")
    require(runtime["version"] == ".".join(map(str, sys.version_info[:3])), "runtime.version")
    require(Path(runtime["executable"]).samefile(sys.executable), "runtime.current-interpreter")
    runtime_pins = _pins(runtime["pins"])
    require(runtime["executable"] in runtime_pins, "runtime.executable-pin")
    distribution = Path(runtime["executable"]).parent.parent
    runtime_paths = set()
    for path in distribution.rglob("*"):
        if ("site-packages" in path.parts or "__pycache__" in path.parts or path.suffix == ".pyc"):
            continue
        info = path.lstat()
        if stat.S_ISREG(info.st_mode):
            require(info.st_nlink == 1, "runtime.resource-alias")
            runtime_paths.add(str(path))
    require(set(runtime_pins) == runtime_paths, "runtime.complete-resource-set")
    pins = {**code, **runtime_pins}
    require(len(pins) == len(code) + len(runtime_pins), "pins.overlap")
    inputs = inventory["inputs"]
    require(type(inputs) is list and len(inputs) == 4, "inputs.count")
    by_label = {}
    input_roots = set()
    public_inputs = []
    for value in inputs:
        closed(value, ("label", "raw_release_id", "adapter", "original_root", "original_inventory",
                       "built_root", "moved_root", "built_inventory", "moved_inventory", "summary"), "input")
        label = value["label"]
        require(type(label) is str and label in INPUTS and label not in by_label, "input.label")
        require((value["adapter"], value["raw_release_id"]) == INPUTS[label], "input.identity")
        original = Path(absolute(value["original_root"], "input.original_root"))
        built = custody.root / relative(value["built_root"], "input.built_root")
        moved = custody.root / relative(value["moved_root"], "input.moved_root")
        require(len({str(original), str(built), str(moved)}) == 3 and
                not built.is_relative_to(moved) and not moved.is_relative_to(built), "input.disjoint-roots")
        require(str(built) not in input_roots and str(moved) not in input_roots, "input.root-alias")
        input_roots.update((str(built), str(moved)))
        original_value, raw_claims = custody.inventory(value["original_inventory"], original)
        built_value, built_claims = custody.inventory(value["built_inventory"], built)
        moved_value, moved_claims = custody.inventory(value["moved_inventory"], moved)
        require(built_claims == moved_claims, "input.moved-bytes")
        copied = {path.removeprefix("source/raw-release/"): claim for path, claim in built_claims.items()
                  if path.startswith("source/raw-release/")}
        require(copied == raw_claims, "input.complete-raw-copy")
        require(set(built_claims) == {"source/raw-release/" + path for path in raw_claims} |
                {"source.json", "capture.json", "events.jsonl", "coverage.json"}, "input.closed-release")
        summary = _summary(value["summary"])
        coverage, _ = read_json(moved / "coverage.json")
        capture, _ = read_json(moved / "capture.json")
        require(capture["request"]["raw_release_id"] == "sha256:" + value["raw_release_id"],
                "input.raw-release-binding")
        require(coverage["versions"]["adapter"]["name"] == value["adapter"] and
                type(coverage["schema_version"]) is int and coverage["schema_version"] == 3,
                "input.generation")
        included = _counts(coverage["coverage"]["included_events"], "coverage.included-events")
        unsupported = _counts(coverage["coverage"]["unsupported_events"], "coverage.unsupported-events")
        counts = source_counts(moved / "source.json")
        actions, families = Counter(), Counter()
        for row in jsonl(moved / "events.jsonl"):
            actions[row["action"]] += 1
            families[row["event_family"]] += 1
        require(summary == {"rows": sum(actions.values()),
                            "canonical_sha256": moved_claims["events.jsonl"]["sha256"],
                            "raw_bytes": original_value["bytes"], "release_bytes": moved_value["bytes"],
                            "action_counts": dict(sorted(actions.items())), **counts} and
                type(coverage["canonical"]["rows"]) is int and coverage["canonical"]["rows"] == summary["rows"] and
                sum(included.values()) == summary["rows"],
                "input.recomputed-summary")
        by_label[label] = {**value, "built": built, "moved": moved,
                           "claims": moved_claims, "release": coverage["release"],
                           "families": dict(families), "unsupported": unsupported}
        public_inputs.append({"label": label, "raw_release_id": value["raw_release_id"],
                              "adapter": value["adapter"], **summary})
    require(anchor["inputs"] == public_inputs, "public-summary.inputs")
    operations = inventory["operations"]
    require(type(operations) is list and len(operations) == 52, "operations.count")
    observed = {}
    caches = set()
    for operation in operations:
        record = _operation(custody, operation, repo, inventory, pins, caches)
        require(operation["id"] not in observed, "operation.duplicate-id")
        require(operation["label"] in by_label, "operation.input")
        observed[operation["id"]] = record
    mutations = inventory["mutations"]
    require(type(mutations) is list and len(mutations) == 20, "mutations.count")
    mutation_keys = set()
    used = set()
    roots = set(input_roots)
    for mutation in mutations:
        _mutation(custody, mutation, by_label, observed, mutation_keys, used, roots)
    for label, value in by_label.items():
        selected = {kind: [op for op in observed.values()
                           if op["label"] == label and op["kind"] == kind]
                    for kind in ("build", "verify", "moved-verify")}
        for kind, records in selected.items():
            require(len(records) == 1, "operation.input-positive-denominator")
            record = records[0]
            used.add(record["id"])
            expected = ([str(repo / CLI), "wildcat-canonical", "--alexandria-release", value["original_root"],
                         "--release", value["release"], "--out", str(value["built"])] if kind == "build" else
                        [str(repo / CLI), "verify", str((value["built"] if kind == "verify" else value["moved"]) / "coverage.json")])
            require(record["cli_argv"] == expected, "operation.literal-cli")
            _positive(record, value, kind)
    require(used == set(observed) and len(mutation_keys) == 20, "operation.full-matrix")
    diagnostics = inventory["guard_diagnostics"]
    require(type(diagnostics) is list and len(diagnostics) == 4, "guard.diagnostics")
    diagnostic_ids = set()
    for operation in diagnostics:
        record = _operation(custody, operation, repo, inventory, pins, caches, diagnostic=True)
        require(record["id"] not in observed and record["id"] not in diagnostic_ids,
                "diagnostic.duplicate-id")
        diagnostic_ids.add(record["id"])
    require(diagnostic_ids == {"guard-compatibility", "guard-socket", "guard-dns", "guard-connect"}, "diagnostic.matrix")
    return {"inventory": anchor["inventory"], "inputs": public_inputs, "operations": 52,
            "mutation_refusals": 20, "network_attempts": 0}


def _operation(custody, value, repo, inventory, pins, caches, diagnostic=False):
    closed(value, ("id", "label", "kind", "receipt", "stdout", "stderr"), "operation")
    text(value["id"], "operation.id", 128)
    text(value["label"], "operation.label", 128)
    kinds = {"build", "verify", "moved-verify", "pristine-control", "mutation-verify"}
    require(value["kind"] == "diagnostic" if diagnostic else value["kind"] in kinds,
            "operation.kind")
    receipt = custody.ref(value["receipt"])
    closed(receipt, ("schema", "id", "label", "kind", "process_argv", "cli_argv", "started_at_utc",
                     "finished_at_utc", "duration_seconds", "exit", "timed_out", "stdout_truncated",
                     "stderr_truncated", "exception", "network_attempts", "guard_report", "loaded_modules"), "receipt")
    require(receipt["schema"] == "wildcat-v3-cli-observation/v1" and
            all(receipt[key] == value[key] for key in ("id", "label", "kind")), "receipt.identity")
    for key in ("timed_out", "stdout_truncated", "stderr_truncated"):
        require(receipt[key] is False, "receipt." + key)
    require(receipt["exception"] is None, "receipt.exception")
    started, finished = _datetime(receipt["started_at_utc"]), _datetime(receipt["finished_at_utc"])
    duration = receipt["duration_seconds"]
    require(type(duration) in (int, float) and math.isfinite(duration) and duration >= 0 and
            finished >= started and abs((finished - started).total_seconds() - duration) <= 2,
            "receipt.duration")
    integer(receipt["exit"], "receipt.exit", 255)
    integer(receipt["network_attempts"], "receipt.network_attempts", 100)
    for key in ("cli_argv", "process_argv"):
        require(type(receipt[key]) is list and 1 <= len(receipt[key]) <= 64, "receipt." + key)
        for argument in receipt[key]:
            text(argument, "receipt.argument")
    argv = receipt["process_argv"]
    require(len(argv) >= 14 and argv[:5] == [inventory["runtime"]["executable"], "-I", "-S", "-B", "-X"],
            "receipt.process-argv")
    prefix = "pycache_prefix="
    require(argv[5].startswith(prefix), "receipt.pycache-prefix")
    cache = Path(absolute(argv[5][len(prefix):], "receipt.pycache-prefix"))
    require(cache.is_relative_to(custody.root) and str(cache) not in caches and not cache.exists(),
            "receipt.fresh-cache")
    caches.add(str(cache))
    require(argv[6:9] == [str(repo / inventory["guard"]["path"]), "--repo", str(repo)] and
            argv[9] == "--guard-report" and argv[11] == "--modules-report" and argv[13] == "--" and
            argv[14:] == receipt["cli_argv"], "receipt.guard-argv")
    require(argv[10] == str(custody.root / receipt["guard_report"]["path"]) and
            argv[12] == str(custody.root / receipt["loaded_modules"]["path"]), "receipt.report-argv")
    guard = custody.ref(receipt["guard_report"])
    closed(guard, ("schema", "attempts", "exception", "cli_exit"), "guard-report")
    require(guard["schema"] == "wildcat-v3-network-observation/v1", "guard-report.schema")
    integer(guard["attempts"], "guard-report.attempts", 100)
    integer(guard["cli_exit"], "guard-report.cli_exit", 255)
    require(guard["attempts"] == receipt["network_attempts"] and
            guard["cli_exit"] == receipt["exit"], "guard-report.receipt-binding")
    if diagnostic:
        denied = value["id"] != "guard-compatibility"
        require(receipt["cli_argv"] == ["diagnostic", value["id"].removeprefix("guard-")] and
                value["label"] == "guard", "diagnostic.literal-cli")
        require((receipt["exit"], guard["attempts"], guard["exception"]) ==
                ((1, 1, "NetworkDenied") if denied else (0, 0, None)), "diagnostic.actual-denial")
    else:
        require(guard["attempts"] == 0 and guard["exception"] is None, "operation.offline-observation")
        require(receipt["exit"] == (1 if value["kind"] == "mutation-verify" else 0), "operation.actual-exit")
    modules = custody.ref(receipt["loaded_modules"])
    closed(modules, ("schema", "modules"), "loaded-modules")
    require(modules["schema"] == "wildcat-v3-loaded-modules/v1" and
            type(modules["modules"]) is list and 0 < len(modules["modules"]) <= ITEM_CAP,
            "loaded-modules.schema")
    names = set()
    for module in modules["modules"]:
        closed(module, ("name", "path", "bytes", "sha256"), "loaded-module")
        name = text(module["name"], "loaded-module.name", 256)
        require(name not in names, "loaded-module.duplicate-name")
        names.add(name)
        absolute(module["path"], "loaded-module.path")
        require(pins.get(module["path"]) == {key: module[key] for key in ("bytes", "sha256")},
                "loaded-module.pin-origin")
    stdout = custody.ref(value["stdout"], STREAM_CAP, json_value=False)
    stderr = custody.ref(value["stderr"], STREAM_CAP, json_value=False)
    if diagnostic:
        require(stdout == b"" and stderr == b"", "diagnostic.empty-streams")
    return {**receipt, "stdout_bytes": stdout, "stderr_bytes": stderr}


def _positive(record, value, kind):
    require(record["stderr_bytes"] == b"", "positive.stderr")
    stdout = parse_json(record["stdout_bytes"])
    if kind == "build":
        closed(stdout, ("event", "release", "rows", "families", "unsupported_counts", "canonical_sha256", "coverage_sha256"), "build.stdout")
        _counts(stdout["families"], "build.families")
        _counts(stdout["unsupported_counts"], "build.unsupported-counts")
        require(stdout["event"] == "wildcat-canonical-built" and
                stdout["coverage_sha256"] == value["claims"]["coverage.json"]["sha256"] and
                stdout["families"] == value["families"] and
                stdout["unsupported_counts"] == value["unsupported"], "build.stdout")
    else:
        closed(stdout, ("event", "release", "adapter", "rows", "schema_version", "canonical_sha256"), "verify.stdout")
        require(stdout["event"] == "wildcat-canonical-verified" and stdout["adapter"] == value["adapter"] and
                type(stdout["schema_version"]) is int and stdout["schema_version"] == 3, "verify.stdout")
    require(stdout["release"] == value["release"] and stdout["rows"] == value["summary"]["rows"] and
            type(stdout["rows"]) is int and stdout["canonical_sha256"] == value["summary"]["canonical_sha256"],
            "positive.recomputed-summary")


def source_counts(path):
    if __package__:
        from .wildcat_v3_execution import source_counts as counts
    else:
        from wildcat_v3_execution import source_counts as counts
    with StableFile(path) as source:
        with os.fdopen(os.dup(source.descriptor), "rb") as stream:
            result = counts(stream)
        source.check()
        return result


def jsonl(path):
    with StableFile(path) as source:
        require(source.before.st_size <= FILE_CAP, "JSONL.byte-cap")
        stream = os.fdopen(os.dup(source.descriptor), "rb")
        try:
            for line in iter(lambda: stream.readline(JSON_CAP + 1), b""):
                require(len(line) <= JSON_CAP and line.endswith(b"\n"), "JSONL.line-cap")
                value = parse_json(line)
                require(type(value) is dict, "JSONL.object")
                yield value
            source.check()
        finally:
            stream.close()


def _mutation(custody, value, inputs, observed, keys, used, roots):
    closed(value, ("label", "kind", "root", "control_id", "verify_id", "pristine_inventory",
                   "mutated_inventory", "changes", "expected_reason"), "mutation")
    label, kind = value["label"], value["kind"]
    require(type(label) is str and label in inputs and kind in MUTATIONS and
            (label, kind) not in keys, "mutation.unique-matrix")
    keys.add((label, kind))
    source = inputs[label]
    root = custody.root / relative(value["root"], "mutation.root")
    require(str(root) not in roots and root not in (source["built"], source["moved"]), "mutation.fresh-root")
    roots.add(str(root))
    _, before = custody.inventory(value["pristine_inventory"], root, physical=False)
    _, after = custody.inventory(value["mutated_inventory"], root)
    require(before == source["claims"] and set(before) == set(after), "mutation.pristine-copy")
    changed = sorted(path for path in before if before[path] != after[path])
    require(type(value["changes"]) is list and len(value["changes"]) == len(changed) and bool(changed), "mutation.changes")
    actual = []
    for change in value["changes"]:
        closed(change, ("path", "before", "after"), "mutation.change")
        path = relative(change["path"], "mutation.change.path")
        byte_claim(change["before"], "mutation.change.before")
        byte_claim(change["after"], "mutation.change.after")
        require(path in changed and change["before"] == before[path] and change["after"] == after[path], "mutation.change.identity")
        actual.append(path)
    require(actual == changed, "mutation.changed-paths")
    if kind in ("party", "amount-shape", "selector"):
        require(changed == ["coverage.json", "events.jsonl"], "mutation.canonical-paths")
        reason = "Wildcat events.jsonl differs from its offline semantic rebuild"
    elif kind == "mapping-class":
        require(changed == ["capture.json", "coverage.json", "source.json"], "mutation.source-paths")
        reason = "Wildcat source.json differs from its offline semantic rebuild"
    else:
        require(len(changed) == 1 and changed[0].startswith("source/raw-release/objects/"), "mutation.raw-path")
        manifest, _ = read_json(root / "source/raw-release/manifest.json")
        components = [component for component in manifest["components"]
                      if "source/raw-release/" + component["object_path"] == changed[0]]
        require(len(components) == 1 and after[changed[0]]["bytes"] == before[changed[0]]["bytes"] + 1,
                "mutation.raw-component")
        reason = "Alexandria Wildcat raw verification failed: component " + components[0]["name"] + " byte count does not match"
    require(value["expected_reason"] == reason, "mutation.production-reason")
    _mutation_semantics(source["moved"], root, kind, changed, before, after)
    for key, expected_kind in (("control_id", "pristine-control"), ("verify_id", "mutation-verify")):
        identifier = text(value[key], "mutation.operation-id", 128)
        require(identifier in observed and identifier not in used, "mutation.operation-binding")
        used.add(identifier)
        operation = observed[identifier]
        require(operation["label"] == label and operation["kind"] == expected_kind and
                operation["cli_argv"] == [str(REPO / CLI), "verify", str(root / "coverage.json")], "mutation.literal-cli")
        if key == "control_id":
            _positive(operation, source, "verify")
        else:
            require(operation["stdout_bytes"] == b"" and operation["stderr_bytes"] ==
                    ("tabularium: verification failed: " + reason + "\n").encode(), "mutation.specific-semantic-refusal")


def _first_deposit(path):
    with StableFile(path) as source:
        with os.fdopen(os.dup(source.descriptor), "rb") as stream:
            offset = 0
            for line in iter(lambda: stream.readline(JSON_CAP + 1), b""):
                require(len(line) <= JSON_CAP and line.endswith(b"\n"), "mutation.JSONL-line")
                row = parse_json(line)
                finish = offset + len(line)
                if row["action"] in ("wildcat-v1.deposit", "wildcat-v2.deposit"):
                    source.check()
                    return row, offset, finish
                offset = finish
        raise EvidenceUnavailable("saved mutation has no deposit specimen")


def _first_mapping(path):
    if __package__:
        from .wildcat_v3_execution import stream_array
    else:
        from wildcat_v3_execution import stream_array
    with StableFile(path) as source:
        with os.fdopen(os.dup(source.descriptor), "rb") as stream:
            row, start, finish = next(stream_array(stream, "mapping_records"))
        source.check()
        return row, start, finish


def _same_outside(before, after, first, last):
    """Check every byte outside the one changed bounded record."""
    require(first[0] == last[0], "mutation.changed-record-position")
    with StableFile(before) as original, StableFile(after) as changed:
        remaining = first[0]
        while remaining:
            size = min(remaining, 1024 * 1024)
            left, right = os.read(original.descriptor, size), os.read(changed.descriptor, size)
            require(len(left) == size and left == right, "mutation.unmodified-prefix")
            remaining -= size
        os.lseek(original.descriptor, first[1], os.SEEK_SET)
        os.lseek(changed.descriptor, last[1], os.SEEK_SET)
        while True:
            left, right = os.read(original.descriptor, 1024 * 1024), os.read(changed.descriptor, 1024 * 1024)
            require(left == right, "mutation.unmodified-suffix")
            if not left:
                break
        original.check()
        changed.check()


def _mutation_semantics(pristine, mutant, kind, changed, before, after):
    original_coverage, _ = read_json(pristine / "coverage.json")
    mutant_coverage, _ = read_json(mutant / "coverage.json")
    expected_coverage = deepcopy(original_coverage)
    if kind in ("party", "amount-shape", "selector"):
        old, start, finish = _first_deposit(pristine / "events.jsonl")
        new, new_start, new_finish = _first_deposit(mutant / "events.jsonl")
        expected = deepcopy(old)
        if kind == "party":
            party = next(item for item in expected["parties"] if item["role"] == "depositor")
            party["address"] = "0x" + ("e" if party["address"] == "0x" + "f" * 40 else "f") * 40
        elif kind == "amount-shape":
            amounts = expected["amounts"]
            expected["amounts"] = [item for item in amounts if item["kind"] != "scaled-claims"]
            require(len(expected["amounts"]) == len(amounts) - 1, "mutation.one-scaled-claim")
        else:
            selector = expected["provenance"]["source_selector"]
            expected["provenance"]["source_selector"] = "wildcat-journal:" + ("1" if selector.endswith("0" * 64) else "0") * 64
        require(new == expected, "mutation.exact-deposit-change")
        _same_outside(pristine / "events.jsonl", mutant / "events.jsonl",
                      (start, finish), (new_start, new_finish))
        expected_coverage["canonical"].update(after["events.jsonl"])
    elif kind == "mapping-class":
        old, start, finish = _first_mapping(pristine / "source.json")
        new, new_start, new_finish = _first_mapping(mutant / "source.json")
        expected = deepcopy(old)
        expected["evidence_class"] = "inferred" if old["evidence_class"] != "inferred" else "directly-observed"
        require(new == expected, "mutation.exact-mapping-class")
        _same_outside(pristine / "source.json", mutant / "source.json",
                      (start, finish), (new_start, new_finish))
        old_capture, _ = read_json(pristine / "capture.json")
        new_capture, _ = read_json(mutant / "capture.json")
        old_capture["source"].update(after["source.json"])
        require(old_capture == new_capture, "mutation.capture-rebinding")
        expected_coverage["source"].update(after["source.json"])
        expected_coverage["capture_manifest"].update(after["capture.json"])
    else:
        path = changed[0]
        with StableFile(pristine / path) as original, StableFile(mutant / path) as changed_file:
            while block := os.read(original.descriptor, 1024 * 1024):
                require(block == os.read(changed_file.descriptor, len(block)), "mutation.raw-preserved-prefix")
            require(os.read(changed_file.descriptor, 2) == b" ", "mutation.one-raw-space")
            original.check()
            changed_file.check()
    require(expected_coverage == mutant_coverage, "mutation.coverage-only-rebinding")
