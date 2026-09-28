#!/usr/bin/env python3
"""Validate the #1963 Wildcat V1 map bundle; never execute or fetch its evidence.

scripts/kickoff_xray_1963.py is the registered command interface. This module
holds everything behind it: the fixed V1 pins, the bounded bundle reader, the
closed record schemas, the synthetic specimen, the hostile catalogue and the
private source admission.

Every check compares recorded bytes with pins fixed here, independently of
the bundle's own manifest, so rebinding the manifest cannot hide an omitted
artifact, input, file or action. A declared review stays recorded evidence:
the checker binds it to exact bytes and a distinct name, and cannot verify the
reviewer's identity or judgement, observed execution, capture completeness,
source-to-bytecode identity, runtime emitter fidelity or protocol safety.

Refusals carry one stable code, a bounded path and a detail: read, json,
schema, shape, unsafe-path, limit, unstable, inventory, digest, specification,
source-identity, source-membership, source-context, source-reference,
compiler, derivation, denominator, action-identity, signature,
action-membership, families, disposition, execution, evidence-reference,
report, review-binding, review-independence, review-coverage, review-findings
and duplicate.
"""

from __future__ import annotations

import contextlib
import dataclasses
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import stat
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emitter_declarations import keccak256  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BUNDLE = ROOT / "docs/kickoff/1963"
REPOSITORY = "wildcat-finance/wildcat-protocol"
SKILLS_START = "1f772fc01bb50c90fe0f254fec8ed088fbe6ab13"
CORE_COMMIT = "da74452aa7d1a0f024d99efd22cc6d950a8116b7"
SENTINEL_COMMIT = "6164ddd4c75ef6da2181e5623b99795b9829e31c"
LENS_CLOSEST_COMMIT = "488b30d08c73a93be3e4bf99128c774997411d3a"
SELECTED_CANDIDATE = "shared-input-index"

MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TOTAL_BYTES = 96 * 1024 * 1024
MAX_FILES = 256
MAX_INPUT_BYTES = 8 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_TEXT_BYTES = 8192
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
PATH_PART = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.-]*\Z")
IDENTIFIER = re.compile(r"[A-Za-z_$][A-Za-z0-9_$]*\Z")
SOURCE_REF = re.compile(
    r"(?:(?P<input>[A-Za-z][A-Za-z0-9]*)@)?(?P<path>[^:@\s]+):(?P<start>[1-9][0-9]*)(?:-(?P<end>[1-9][0-9]*))?\Z")

KINDS = ("read", "state-changing", "creation")
SCOPED_KINDS = ("state-changing", "creation")
MUTABILITY = {"read": {"view", "pure"}, "state-changing": {"nonpayable", "payable"},
              "creation": {"nonpayable", "payable"}}
ORIGINS = ("abi", "ast")
CONTEXT_KINDS = ("runtime", "creation-target")
FILE_DISPOSITIONS = ("context", "support", "excluded")
DISPOSITIONS = ("mapped", "conditional", "eventless", "unresolved")
RELATIONS = ("direct", "transitive")
EXECUTION_STATUS = ("passed", "failed", "inconclusive")
REQUIRED_FAMILIES = frozenset({
    "funding", "transfer", "borrowing", "repayment", "fee", "withdrawal-queue", "batch-funding",
    "execution", "sanctions", "escrow-release", "closure", "administration",
})
FAMILIES = REQUIRED_FAMILIES | {"creation", "read"}
REPORT_NAMES = ("x-ray.md", "entry-points.md", "invariants.md", "architecture.json", "architecture.svg")
REPORT_HEADINGS = {
    "x-ray.md": ("overview", "threat", "invariant", "doc", "test", "git", "x-ray verdict"),
    "entry-points.md": ("permissionless", "role", "init", "external"),
    "invariants.md": ("enforced guards", "single-contract", "cross-contract", "economic"),
}
BOUNDARY = (
    "Checks retained bytes, fixed input, source and action pins, dispositions and the declared review binding. "
    "Does not prove observed execution, capture completeness, source-to-bytecode identity, runtime emitter "
    "fidelity, reviewer identity or protocol safety."
)


@dataclasses.dataclass(frozen=True)
class InputPin:
    sha256: str
    partition: str
    source_ref: str
    files: int
    projection: str
    binding_limit: str | None = None


@dataclasses.dataclass(frozen=True)
class ContextPin:
    input: str
    source_path: str
    kind: str


@dataclasses.dataclass(frozen=True)
class Profile:
    """The fixed expectations one bundle is checked against."""

    name: str
    repository: str
    start: str
    anchors: dict
    compiler: dict
    inputs: dict
    contexts: dict
    artifacts: frozenset
    specifications: dict
    denominator: tuple | None
    executions: frozenset
    families: frozenset
    commits: tuple


LENS_LIMIT = (
    "Verified compiler input; no single exact Git commit covers all 46 in-tree files. Closest commit "
    "488b30d08c73a93be3e4bf99128c774997411d3a matches 40. This partition does not satisfy whole-tree "
    "exact-commit acceptance."
)
V1_INPUTS = {
    "WildcatMarketControllerFactory": InputPin(
        "dbeb245c5fc0a44f8ca7d001ddf801ec00176e838eae9487c8d65f2b9bdc8706", "core-da74452a",
        f"https://github.com/{REPOSITORY}/tree/{CORE_COMMIT}", 40,
        "8d1c47865303062363f1705ab01a10d7132d2fbd5bda56b752d503ff2fbd4435"),
    "WildcatArchController": InputPin(
        "cb9136ec6740226c91e8d85268a0bbf7c8a5e81edb57b4bb332cc72a7e2b60db", "core-da74452a",
        f"https://github.com/{REPOSITORY}/tree/{CORE_COMMIT}", 10,
        "21032a14a876ad6431e38340cc534de8272f8162518a49e3629f528ec56d49b5"),
    "WildcatSanctionsSentinel": InputPin(
        "45055f0b576dc6a607e4d8165711b144d1d1776d14939f74b46c4960273d8cb6", "sentinel-6164ddd4",
        f"https://github.com/{REPOSITORY}/tree/{SENTINEL_COMMIT}", 7,
        "9c4d819dca7eed43821dd4d37d796de33bbdf05f9057106d40a7b3ec2dd22ae4"),
    "MarketLensMixed": InputPin(
        "fe06195c86502900d64692619da8e1275ebc7720087e59d81b2c8dd651648377", "lens-verified-mixed",
        "https://sourcify.dev/server/v2/contract/1/0xf1d516954f96c1363f8b0ae48d79c8dde6237847"
        "?fields=stdJsonInput#sha256=fe06195c86502900d64692619da8e1275ebc7720087e59d81b2c8dd651648377", 50,
        "f1804b1536c07449c0eea632e1d7824f94c43bb9b453e102a6dec6e22be38173", LENS_LIMIT),
}
V1_CONTEXTS = {
    "WildcatMarket": ContextPin("WildcatMarketControllerFactory", "src/market/WildcatMarket.sol", "runtime"),
    "WildcatMarketController": ContextPin("WildcatMarketControllerFactory", "src/WildcatMarketController.sol", "runtime"),
    "WildcatMarketControllerFactory": ContextPin(
        "WildcatMarketControllerFactory", "src/WildcatMarketControllerFactory.sol", "runtime"),
    "WildcatArchController": ContextPin("WildcatArchController", "src/WildcatArchController.sol", "runtime"),
    "WildcatSanctionsSentinel": ContextPin("WildcatSanctionsSentinel", "src/WildcatSanctionsSentinel.sol", "runtime"),
    "WildcatSanctionsEscrow": ContextPin("WildcatSanctionsSentinel", "src/WildcatSanctionsEscrow.sol", "creation-target"),
    "MarketLens": ContextPin("MarketLensMixed", "src/lens/MarketLens.sol", "runtime"),
}
V1_COMPILER = {
    "version": "0.8.22+commit.4fc1097e",
    "solcjs_sha256": "92d283c545395b91a656fa1ec94d567a464bca55aebcdbb99debf42b43026845",
    "evm_version": "shanghai",
    "optimizer_runs": 200,
    "via_ir": True,
    "bytecode_hash": "none",
}
V1_ANCHORS = {
    "registry": {"path": "docs/kickoff/1359/targets.json", "row": "wildcat-v1-ethereum-mainnet",
                 "sha256": "2a3ec081f9a74bdcc60a57ee3cab3f11d33ce8be22001bdf4c6f5a8c218ce625"},
    "emitter_table": {"path": "docs/kickoff/1962/emitters.json",
                      "sha256": "7fb47cb94b14a851df12406a454810ff3d22620751b78f96fbd53feffcf37cff"},
}
V1_SELECTION_REPORTS = tuple(
    f"design-reports/{candidate}-{criterion}.json"
    for candidate in ("shared-input-index", "component-copies")
    for criterion in ("context-bindings", "parse-budget", "public-reference-only",
                      "recoverable-input-identities", "reference-bytes")
)
PRODUCTION = Profile(
    name="wildcat-v1",
    repository=REPOSITORY,
    start=SKILLS_START,
    anchors=V1_ANCHORS,
    compiler=V1_COMPILER,
    inputs=V1_INPUTS,
    contexts=V1_CONTEXTS,
    artifacts=frozenset({
        "README.md", "study.md", "runbook.md", "design-evidence.json", *V1_SELECTION_REPORTS,
        "sources.json", "denominator-inputs.json", "actions.json", "linkage.json", "review.json",
        "execution.json", *REPORT_NAMES,
    }),
    specifications={
        "study.md": "724b104caf999eb4fe134f5da54ab9b135936934b5003f5b1551b6fde1ab7839",
        "runbook.md": "84c8502b957c98179569e744fc3b5d26ac582fba247ef53334ceafb006af7e0a",
        "design-evidence.json": "38ec354050ed6239caa8eeb12369378d37af5c2ff33b4c1d78143d693d083e49",
    },
    # Step 2 fixes the independent denominator's count and projection digest
    # from the compiler outputs; until then no production bundle can pass.
    denominator=None,
    executions=frozenset(f"derive-{name}" for name in V1_INPUTS),
    families=REQUIRED_FAMILIES,
    commits=(CORE_COMMIT, SENTINEL_COMMIT),
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


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def text(value: object, where: str) -> str:
    require(isinstance(value, str) and bool(value.strip()) and len(value.encode()) <= MAX_TEXT_BYTES,
            "shape", where, "expected bounded nonempty text")
    return value


def mapping(value: object, where: str, keys: tuple[str, ...]) -> dict:
    """Require an object with exactly the named keys."""
    require(isinstance(value, dict), "shape", where, "expected object")
    require(set(value) == set(keys), "shape", where, "fields differ from the closed schema")
    return value


def sequence(value: object, where: str, nonempty: bool = False) -> list:
    require(isinstance(value, list), "shape", where, "expected array")
    require(not nonempty or bool(value), "shape", where, "expected nonempty array")
    return value


def texts(value: object, where: str, nonempty: bool = False) -> list[str]:
    items = sequence(value, where, nonempty)
    for index, item in enumerate(items):
        text(item, f"{where}[{index}]")
    require(len(items) == len(set(items)), "duplicate", where, "repeated entry")
    return items


def sha256(value: object, where: str) -> str:
    require(isinstance(value, str) and bool(SHA256.fullmatch(value)), "shape", where, "expected SHA-256")
    return value


def count(value: object, where: str) -> int:
    require(type(value) is int and value >= 0, "shape", where, "expected nonnegative integer")
    return value


def relative_path(value: object, where: str) -> str:
    require(isinstance(value, str) and bool(value), "unsafe-path", where, "expected relative path")
    parts = value.split("/")
    require(len(value) <= 512 and len(parts) <= 8 and all(PATH_PART.fullmatch(p) for p in parts),
            "unsafe-path", where, "expected bounded portable relative path")
    require(all(p not in (".", "..") for p in parts), "unsafe-path", where, "dot component")
    return value


def json_value(data: bytes, where: str) -> object:
    """Decode strict JSON: no duplicate keys, no non-finite numbers, bounded depth."""
    def pairs(items: list[tuple[str, object]]) -> dict:
        result = {}
        for key, value in items:
            require(key not in result, "json", where, f"duplicate object key {key[:64]!r}")
            result[key] = value
        return result

    def constant(name: str) -> None:
        raise ValueError(f"non-finite JSON number {name}")

    def finite(raw: str) -> float:
        # An overflowing literal such as 1e999 decodes to inf without reaching parse_constant.
        number = float(raw)
        if not math.isfinite(number):
            raise ValueError("non-finite JSON number")
        return number

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=pairs, parse_constant=constant,
                           parse_float=finite)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise Refusal("json", where, "invalid or excessively nested JSON") from exc
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        require(depth <= MAX_JSON_DEPTH, "json", where, f"JSON depth exceeds {MAX_JSON_DEPTH}")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in item.values())
        elif isinstance(item, list):
            pending.extend((child, depth + 1) for child in item)
    return value


# Canonical ABI signatures ---------------------------------------------------

_ELEMENTARY = re.compile(
    r"(?:u?int(?:8|16|24|32|40|48|56|64|72|80|88|96|104|112|120|128|136|144|152|160|168|176|184|192|200|208|216|224|232|240|248|256)"
    r"|bytes(?:3[0-2]|[12][0-9]|[1-9])?|address|bool|string|function)(?![A-Za-z0-9_$])")
_ARRAY = re.compile(r"\[(?:[1-9][0-9]*)?\]")


def _type_end(value: str, start: int) -> int | None:
    """Return the end of one canonical ABI type at start, or None."""
    if start < len(value) and value[start] == "(":
        index = start + 1
        if index < len(value) and value[index] == ")":
            index += 1
        else:
            while True:
                end = _type_end(value, index)
                if end is None:
                    return None
                if end < len(value) and value[end] == ",":
                    index = end + 1
                    continue
                if end < len(value) and value[end] == ")":
                    index = end + 1
                    break
                return None
    else:
        match = _ELEMENTARY.match(value, start)
        if match is None:
            return None
        index = match.end()
    while True:
        match = _ARRAY.match(value, index)
        if match is None:
            return index
        index = match.end()


def canonical_signature(value: object) -> bool:
    """True for name(type,...) with canonical ABI parameter types only."""
    if not isinstance(value, str) or len(value) > 1024 or "(" not in value:
        return False
    name, _, rest = value.partition("(")
    if not IDENTIFIER.fullmatch(name):
        return False
    return _type_end(value, len(name)) == len(value)


def selector(signature: str) -> str:
    return "0x" + keccak256(signature.encode()).hex()[:8]


def action_id(row: dict) -> str:
    return f"{row['input']}:{row['context']}:{row['kind']}:{row['signature']}"


# Bounded, link-refusing bundle reads ---------------------------------------

class Bundle:
    """Read regular files through held directory descriptors without following links."""

    def __init__(self, root: Path):
        self.root = Path(root).absolute()
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
        handle = None
        try:
            parts = name.split("/")
            for part in parts[:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
                os.close(parent)
                parent = child
            handle = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            before = os.fstat(handle)
            require(stat.S_ISREG(before.st_mode), "unsafe-path", name, "not a regular file")
            require(before.st_size <= MAX_FILE_BYTES, "limit", name, "file exceeds 16 MiB")
            with os.fdopen(handle, "rb", closefd=False) as stream:
                result = stream.read(MAX_FILE_BYTES + 1)
            after = os.fstat(handle)
            named = os.stat(parts[-1], dir_fd=parent, follow_symlinks=False)
            identity = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)  # noqa: E731
            require(identity(before) == identity(after) == identity(named) and len(result) == before.st_size,
                    "unstable", name, "file changed during read")
            require(len(result) <= MAX_FILE_BYTES, "limit", name, "file exceeds 16 MiB")
            return result
        except OSError as exc:
            raise Refusal("read", name, "missing, linked, unsafe or unreadable evidence") from exc
        finally:
            if handle is not None:
                os.close(handle)
            os.close(parent)

    def paths(self) -> set[str]:
        found: set[str] = set()
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
        value = json_value(self.load(name), name)
        require(isinstance(value, dict) and value.get("schema") == schema, "schema", name, "unsupported schema")
        return value

    def finish(self) -> None:
        require(self.paths() == set(self.data), "unstable", "bundle", "file inventory changed")
        for name, previous in self.data.items():
            require(self.read(name) == previous, "unstable", name, "bytes changed during check")
        named = self.root.stat(follow_symlinks=False)
        opened = os.fstat(self.fd)
        require((named.st_dev, named.st_ino) == (opened.st_dev, opened.st_ino),
                "unstable", "bundle", "bundle directory changed")


def records(value: object, where: str, key: str, keys: tuple[str, ...]) -> dict[str, dict]:
    result: dict[str, dict] = {}
    for index, raw in enumerate(sequence(value, where)):
        row = mapping(raw, f"{where}[{index}]", keys)
        name = text(row[key], f"{where}[{index}].{key}")
        require(name not in result, "duplicate", where, f"duplicate {key}: {name}")
        result[name] = row
    return result


# Record checks ---------------------------------------------------------------

def check_manifest(bundle: Bundle, profile: Profile) -> dict[str, dict]:
    manifest = bundle.json("manifest.json", "issue-1963-manifest/v1")
    mapping(manifest, "manifest", ("schema", "repository", "start", "artifacts"))
    require(manifest["repository"] == profile.repository, "source-identity", "manifest.repository", "wrong repository")
    require(manifest["start"] == profile.start, "specification", "manifest.start", "wrong starting commit")
    rows = sequence(manifest["artifacts"], "manifest.artifacts", True)
    for index, row in enumerate(rows):
        mapping(row, f"manifest.artifacts[{index}]", ("path", "sha256", "bytes"))
        relative_path(row["path"], f"manifest.artifacts[{index}].path")
    artifacts = records(rows, "manifest.artifacts", "path", ("path", "sha256", "bytes"))
    missing = sorted(profile.artifacts - artifacts.keys())
    extra = sorted(artifacts.keys() - profile.artifacts)
    require(not missing, "inventory", "manifest.artifacts", "required artifact absent: " + ", ".join(missing[:4]))
    require(not extra, "inventory", "manifest.artifacts", "artifact outside the fixed set: " + ", ".join(extra[:4]))
    physical = bundle.paths()
    require(physical == set(artifacts) | {"manifest.json"}, "inventory", "bundle",
            "physical files differ from the fixed artifact set")
    for name, row in artifacts.items():
        expected = sha256(row["sha256"], name + ".sha256")
        size = count(row["bytes"], name + ".bytes")
        data = bundle.load(name)
        require(len(data) == size and digest(data) == expected, "digest", name, "bytes or SHA-256 differ")
    return artifacts


def check_specifications(bundle: Bundle, profile: Profile) -> None:
    for name, expected in sorted(profile.specifications.items()):
        require(digest(bundle.load(name)) == expected, "specification", name, "receipted specification changed")
    design = bundle.json("design-evidence.json", "protasis-design-evidence/v1")
    for index, result in enumerate(sequence(design.get("results"), "design-evidence.results")):
        require(isinstance(result, dict), "shape", f"design-evidence.results[{index}]", "expected object")
        if result.get("state") != "pass":
            continue
        reference = mapping(result.get("report"), f"design-evidence.results[{index}].report", ("path", "sha256"))
        path = relative_path(reference["path"], f"design-evidence.results[{index}].report.path")
        require(digest(bundle.load(path)) == reference["sha256"], "specification", path,
                "selection report differs from the receipted record")
        report = bundle.json(path, "protasis-design-report/v1")
        require(report.get("candidate") == result.get("candidate") and report.get("criterion") == result.get("criterion")
                and type(report.get("exit")) is int and report["exit"] == 0,
                "specification", path, "selection report binding differs")


def check_sources(bundle: Bundle, profile: Profile) -> dict[str, dict[str, dict]]:
    """Return {input: {path: file row}} after exact identity and membership checks."""
    sources = bundle.json("sources.json", "issue-1963-sources/v1")
    mapping(sources, "sources", ("schema", "repository", "anchors", "compiler", "inputs", "contexts",
                                 "dependencies", "exclusions"))
    require(sources["repository"] == profile.repository, "source-identity", "sources.repository", "wrong repository")
    # Canonical bytes, not ==: Python equates 1 and 1.0 with true and 200.0 with 200.
    require(canonical(sources["anchors"]) == canonical(profile.anchors), "source-identity", "sources.anchors",
            "registry or emitter-table anchor differs")
    require(canonical(sources["compiler"]) == canonical(profile.compiler), "compiler", "sources.compiler",
            "compiler identity differs")
    inputs = records(sources["inputs"], "sources.inputs", "id",
                     ("id", "sha256", "partition", "source_ref", "binding_limit", "files"))
    require(set(inputs) == set(profile.inputs), "source-identity", "sources.inputs", "input set differs")
    files_by_input: dict[str, dict[str, dict]] = {}
    for name, pin in profile.inputs.items():
        row = inputs[name]
        where = f"sources.inputs.{name}"
        require(row["sha256"] == pin.sha256, "source-identity", where + ".sha256", "accepted input digest differs")
        require(row["partition"] == pin.partition and row["source_ref"] == pin.source_ref,
                "source-identity", where, "partition or source reference differs")
        require(row["binding_limit"] == pin.binding_limit, "source-identity", where + ".binding_limit",
                "source-binding exception differs")
        files = records(row["files"], where + ".files", "path",
                        ("path", "sha256", "bytes", "lines", "disposition", "reason"))
        projection = []
        for path in sorted(files):
            item = files[path]
            relative_path(path, f"{where}.files.path")
            require(item["disposition"] in FILE_DISPOSITIONS, "shape", f"{where}.{path}.disposition",
                    "unknown file disposition")
            text(item["reason"], f"{where}.{path}.reason")
            projection.append({"path": path, "sha256": sha256(item["sha256"], f"{where}.{path}.sha256"),
                               "bytes": count(item["bytes"], f"{where}.{path}.bytes"),
                               "lines": count(item["lines"], f"{where}.{path}.lines")})
        require(len(files) == pin.files and digest(canonical(projection)) == pin.projection,
                "source-membership", where + ".files", "source projection differs from the accepted input")
        files_by_input[name] = files
    contexts = records(sources["contexts"], "sources.contexts", "contract", ("contract", "input", "source_path", "kind"))
    require(set(contexts) == set(profile.contexts), "source-context", "sources.contexts", "context set differs")
    for name, pin in profile.contexts.items():
        row = contexts[name]
        require((row["input"], row["source_path"], row["kind"]) == (pin.input, pin.source_path, pin.kind),
                "source-context", f"sources.contexts.{name}", "context binding differs")
    declared = {(pin.input, pin.source_path) for pin in profile.contexts.values()}
    for name, files in files_by_input.items():
        for path, item in files.items():
            require((item["disposition"] == "context") == ((name, path) in declared), "source-context",
                    f"sources.inputs.{name}.{path}", "context disposition disagrees with the bound contexts")
    records(sources["dependencies"], "sources.dependencies", "subject", ("subject", "limit"))
    require(bool(sources["dependencies"]), "shape", "sources.dependencies", "external dependencies unstated")
    for index, row in enumerate(sources["dependencies"]):
        text(row["limit"], f"sources.dependencies[{index}].limit")
    records(sources["exclusions"], "sources.exclusions", "subject", ("subject", "reason"))
    require(bool(sources["exclusions"]), "shape", "sources.exclusions", "exclusions unstated")
    for index, row in enumerate(sources["exclusions"]):
        text(row["reason"], f"sources.exclusions[{index}].reason")
    return files_by_input


def check_reference(ref: object, default_input: str, files: dict[str, dict[str, dict]], where: str) -> None:
    match = SOURCE_REF.fullmatch(ref) if isinstance(ref, str) else None
    require(match is not None, "source-reference", where, "expected [input@]path:line[-line]")
    name = match.group("input") or default_input
    require(name in files, "source-reference", where, "unknown source input")
    path = match.group("path")
    require(path in files[name], "source-reference", where, "path is absent from the bound input")
    start = int(match.group("start"))
    end = int(match.group("end") or start)
    require(start <= end <= files[name][path]["lines"], "source-reference", where,
            "line range lies outside the recorded file")


def references(value: object, default_input: str, files: dict, where: str, nonempty: bool = True) -> None:
    for index, ref in enumerate(texts(value, where, nonempty)):
        check_reference(ref, default_input, files, f"{where}[{index}]")


IDENTITY_KEYS = ("id", "input", "context", "kind", "signature", "selector", "mutability", "declared_in",
                 "source_ref", "origin")


def check_denominator(bundle: Bundle, profile: Profile, files: dict) -> dict[str, dict]:
    value = bundle.json("denominator-inputs.json", "issue-1963-denominator-inputs/v1")
    mapping(value, "denominator", ("schema", "derivations", "identities"))
    derivations = records(value["derivations"], "denominator.derivations", "input",
                          ("input", "original_input_sha256", "prepared_input_sha256", "output_sha256",
                           "compiler", "argv", "exit"))
    require(set(derivations) == set(profile.inputs), "derivation", "denominator.derivations",
            "derivation set differs from the accepted inputs")
    for name, row in derivations.items():
        where = f"denominator.derivations.{name}"
        require(row["original_input_sha256"] == profile.inputs[name].sha256, "derivation", where,
                "original input digest differs")
        sha256(row["prepared_input_sha256"], where + ".prepared_input_sha256")
        sha256(row["output_sha256"], where + ".output_sha256")
        require(row["compiler"] == profile.compiler["version"], "compiler", where, "compiler differs")
        texts(row["argv"], where + ".argv", True)
        require(type(row["exit"]) is int and row["exit"] == 0, "derivation", where, "derivation did not exit 0")
    identities = records(value["identities"], "denominator.identities", "id", IDENTITY_KEYS)
    creations: dict[str, int] = {name: 0 for name in profile.contexts}
    for name, row in identities.items():
        where = f"denominator.{name}"
        require(isinstance(row["context"], str) and row["context"] in profile.contexts, "action-identity", where,
                "unknown context")
        require(row["input"] == profile.contexts[row["context"]].input, "action-identity", where,
                "context is bound to a different input")
        require(row["kind"] in KINDS, "action-identity", where, "unknown kind")
        require(canonical_signature(row["signature"]), "signature", where, "signature is not canonical")
        require(name == action_id(row), "action-identity", where, "id differs from input, context, kind and signature")
        if row["kind"] == "creation":
            require(row["signature"].startswith("constructor(") and row["selector"] is None,
                    "signature", where, "creation identity needs a constructor signature and no selector")
            creations[row["context"]] += 1
        else:
            require(row["selector"] == selector(row["signature"]), "signature", where, "selector differs from signature")
        require(isinstance(row["mutability"], str) and row["mutability"] in MUTABILITY[row["kind"]],
                "action-identity", where, "mutability contradicts kind")
        require(row["origin"] in ORIGINS, "action-identity", where, "unknown origin")
        text(row["declared_in"], where + ".declared_in")
        check_reference(row["source_ref"], row["input"], files, where + ".source_ref")
    missing = sorted(name for name, seen in creations.items() if seen != 1)
    require(not missing, "denominator", "denominator.identities",
            "each context needs exactly one creation path: " + ", ".join(missing[:4]))
    require(profile.denominator is not None, "denominator", "profile",
            "no independent denominator pin is fixed for this profile")
    projection = [{key: identities[name][key] for key in ("id", "selector", "mutability", "declared_in", "origin")}
                  for name in sorted(identities)]
    expected_count, expected_digest = profile.denominator
    require(len(identities) == expected_count and digest(canonical(projection)) == expected_digest,
            "denominator", "denominator.identities", "identities differ from the independent compiler projection")
    return identities


def check_actions(bundle: Bundle, profile: Profile, identities: dict, files: dict) -> dict[str, dict]:
    value = bundle.json("actions.json", "issue-1963-actions/v1")
    mapping(value, "actions", ("schema", "actions"))
    actions = records(value["actions"], "actions.actions", "id",
                      ("id", "input", "context", "kind", "signature", "families", "summary", "source_refs"))
    require(actions.keys() <= identities.keys(), "action-membership", "actions.actions",
            "action outside the independent denominator")
    require(actions.keys() >= identities.keys(), "action-membership", "actions.actions",
            "denominator identity has no action row")
    covered: set[str] = set()
    for name, row in actions.items():
        where = f"actions.{name}"
        identity = identities[name]
        require((row["input"], row["context"], row["kind"]) == (identity["input"], identity["context"], identity["kind"]),
                "action-identity", where, "input, context or kind differs from the denominator")
        require(row["signature"] == identity["signature"], "signature", where, "signature differs from the denominator")
        families = texts(row["families"], where + ".families", True)
        require(set(families) <= FAMILIES, "families", where, "unknown flow family")
        require((row["kind"] == "read") == (families == ["read"]), "families", where,
                "read identities carry only the read family")
        covered.update(families)
        text(row["summary"], where + ".summary")
        references(row["source_refs"], row["input"], files, where + ".source_refs")
    missing = sorted(profile.families - covered)
    require(not missing, "families", "actions.actions", "required flow family uncovered: " + ", ".join(missing[:4]))
    return actions


LINK_KEYS = ("id", "disposition", "guards", "state_effects", "value_flows", "events", "dynamic_callees",
             "attribution", "gaps", "source_refs", "reason")
EVENT_KEYS = ("event", "emitter", "relation", "source_ref", "condition")


def check_linkage(bundle: Bundle, identities: dict, files: dict) -> set[str]:
    value = bundle.json("linkage.json", "issue-1963-linkage/v1")
    mapping(value, "linkage", ("schema", "actions"))
    rows = sequence(value["actions"], "linkage.actions")
    for index, raw in enumerate(rows):
        require(isinstance(raw, dict), "shape", f"linkage.actions[{index}]", "expected object")
        require("disposition" in raw, "disposition", f"linkage.actions[{index}]", "disposition missing")
    links = records(rows, "linkage.actions", "id", LINK_KEYS)
    scoped = {name for name, row in identities.items() if row["kind"] in SCOPED_KINDS}
    require(links.keys() <= scoped, "action-membership", "linkage.actions", "linkage row outside the scoped actions")
    require(links.keys() >= scoped, "action-membership", "linkage.actions", "scoped action has no linkage row")
    for name, row in links.items():
        where = f"linkage.{name}"
        home = identities[name]["input"]
        disposition = row["disposition"]
        require(disposition in DISPOSITIONS, "disposition", where, "unknown disposition")
        for field in ("guards", "state_effects", "value_flows", "attribution", "gaps"):
            texts(row[field], f"{where}.{field}")
        events = sequence(row["events"], where + ".events")
        conditional = 0
        for index, raw in enumerate(events):
            event = mapping(raw, f"{where}.events[{index}]", EVENT_KEYS)
            require(canonical_signature(event["event"]), "signature", f"{where}.events[{index}]",
                    "event signature is not canonical")
            text(event["emitter"], f"{where}.events[{index}].emitter")
            require(event["relation"] in RELATIONS, "shape", f"{where}.events[{index}].relation", "unknown relation")
            check_reference(event["source_ref"], home, files, f"{where}.events[{index}].source_ref")
            if event["condition"] is not None:
                text(event["condition"], f"{where}.events[{index}].condition")
                conditional += 1
        for index, raw in enumerate(sequence(row["dynamic_callees"], where + ".dynamic_callees")):
            callee = mapping(raw, f"{where}.dynamic_callees[{index}]", ("call", "limit"))
            text(callee["call"], f"{where}.dynamic_callees[{index}].call")
            text(callee["limit"], f"{where}.dynamic_callees[{index}].limit")
        references(row["source_refs"], home, files, where + ".source_refs")
        text(row["reason"], where + ".reason")
        if disposition == "mapped":
            require(bool(events) and not conditional, "disposition", where, "mapped needs unconditional events only")
        elif disposition == "conditional":
            require(bool(conditional), "disposition", where, "conditional needs an event with a path condition")
        elif disposition == "eventless":
            require(not events and not row["gaps"], "disposition", where,
                    "eventless carries no event and no unresolved gap")
        else:
            require(bool(row["gaps"]), "disposition", where, "unresolved needs a named gap")
    return scoped


EXECUTION_KEYS = ("id", "purpose", "argv", "exit", "status", "log", "observation")


def artifact_ref(raw: object, where: str, artifacts: dict) -> str:
    row = mapping(raw, where, ("path", "sha256"))
    path = relative_path(row["path"], where + ".path")
    require(path in artifacts, "evidence-reference", where, "path is absent from the manifest")
    require(row["sha256"] == artifacts[path]["sha256"], "evidence-reference", where, "digest differs from the manifest")
    return path


def check_execution(bundle: Bundle, profile: Profile, artifacts: dict) -> None:
    value = bundle.json("execution.json", "issue-1963-execution/v1")
    mapping(value, "execution", ("schema", "records"))
    rows = records(value["records"], "execution.records", "id", EXECUTION_KEYS)
    require(set(rows) == profile.executions, "execution", "execution.records", "execution record set differs")
    for name, row in rows.items():
        where = f"execution.{name}"
        text(row["purpose"], where + ".purpose")
        texts(row["argv"], where + ".argv", True)
        require(type(row["exit"]) is int, "execution", where, "exit is not an integer")
        status = row["status"]
        require(status in EXECUTION_STATUS, "execution", where, "unknown status")
        require((status == "passed") == (row["exit"] == 0) or status == "inconclusive", "execution", where,
                "status contradicts the recorded exit")
        text(row["observation"], where + ".observation")
        if row["log"] is not None:
            artifact_ref(row["log"], where + ".log", artifacts)
        require(status == "passed" or row["log"] is not None, "execution", where, "failed attempt keeps no log")


def check_reports(bundle: Bundle, profile: Profile, scoped: set[str]) -> None:
    for name, required in REPORT_HEADINGS.items():
        body = bundle.load(name).decode("utf-8")
        require(all(commit in body for commit in profile.commits), "report", name, "exact source commit missing")
        titles = "\n".join(line.lower() for line in body.splitlines() if line.startswith("#"))
        require(all(term in titles for term in required), "report", name, "required section missing")
        if name == "x-ray.md":
            require(len(body.splitlines()) < 500, "report", name, "X-Ray exceeds its line budget")
        if name == "entry-points.md":
            absent = sorted(action for action in scoped if action not in body)
            require(not absent, "report", name, "scoped action id missing: " + ", ".join(absent[:2]))
    architecture = json_value(bundle.load("architecture.json"), "architecture.json")
    mapping(architecture, "architecture.json", ("title", "nodes", "edges"))
    text(architecture["title"], "architecture.json.title")
    nodes = records(architecture["nodes"], "architecture.json.nodes", "id", ("id", "label", "kind"))
    for name, node in nodes.items():
        text(node["label"], f"architecture.json.nodes.{name}.label")
        text(node["kind"], f"architecture.json.nodes.{name}.kind")
    require(set(profile.contexts) <= set(nodes), "report", "architecture.json", "context node missing")
    for index, raw in enumerate(sequence(architecture["edges"], "architecture.json.edges", True)):
        edge = mapping(raw, f"architecture.json.edges[{index}]", ("from", "to", "label"))
        require(all(isinstance(edge[end], str) and edge[end] in nodes for end in ("from", "to")),
                "report", "architecture.json", "edge endpoint missing")
        text(edge["label"], f"architecture.json.edges[{index}].label")
    svg = bundle.load("architecture.svg").decode("utf-8")
    require(svg.lstrip().startswith("<svg") and svg.rstrip().endswith("</svg>"), "report", "architecture.svg",
            "SVG root missing")
    require(all(name in svg for name in profile.contexts), "report", "architecture.svg", "context label missing")


REVIEW_KEYS = ("schema", "producer", "reviewer", "status", "method", "linkage", "actions", "reviewed_actions",
               "findings", "resolved_finding_ids", "open_findings", "artifacts", "visual_inspection", "boundary")
REVIEWED_ARTIFACTS = ("sources.json", "denominator-inputs.json", "actions.json", "linkage.json",
                      "execution.json", *REPORT_NAMES)


def check_review(bundle: Bundle, scoped: set[str], artifacts: dict) -> None:
    review = bundle.json("review.json", "issue-1963-review/v1")
    mapping(review, "review", REVIEW_KEYS)
    for field in ("linkage", "actions"):
        bound = mapping(review[field], "review." + field, ("path", "sha256"))
        require(bound["path"] == f"{field}.json", "review-binding", "review." + field, "review names the wrong record")
        require(bound["sha256"] == digest(bundle.load(bound["path"])), "review-binding", "review." + field,
                "review is not bound to the exact record bytes")
    producer = text(review["producer"], "review.producer")
    reviewer = text(review["reviewer"], "review.reviewer")
    require(producer.strip().lower() != reviewer.strip().lower(), "review-independence", "review.reviewer",
            "the linkage producer reviewed their own record")
    require(review["status"] == "complete", "review-coverage", "review.status", "review is not complete")
    text(review["method"], "review.method")
    text(review["boundary"], "review.boundary")
    reviewed = texts(review["reviewed_actions"], "review.reviewed_actions")
    require(set(reviewed) == scoped, "review-coverage", "review.reviewed_actions",
            "reviewed action set differs from the scoped actions")
    findings = records(review["findings"], "review.findings", "id", ("id", "status", "summary", "resolution"))
    for name, row in findings.items():
        require(row["status"] == "resolved", "review-findings", "review.findings." + name, "finding is not resolved")
        text(row["summary"], f"review.findings.{name}.summary")
        text(row["resolution"], f"review.findings.{name}.resolution")
    resolved = texts(review["resolved_finding_ids"], "review.resolved_finding_ids")
    require(set(resolved) == set(findings), "review-findings", "review.resolved_finding_ids",
            "resolved ids must name each retained finding once")
    require(sequence(review["open_findings"], "review.open_findings") == [], "review-findings",
            "review.open_findings", "completed review retains open findings")
    refs = records(review["artifacts"], "review.artifacts", "path", ("path", "sha256"))
    require(set(REVIEWED_ARTIFACTS) <= set(refs), "review-coverage", "review.artifacts", "reviewed artifact missing")
    for path, row in refs.items():
        relative_path(path, "review.artifacts.path")
        require(path in artifacts and row["sha256"] == artifacts[path]["sha256"], "review-binding",
                "review.artifacts." + path, "reviewed bytes differ from the retained artifact")
    visual = mapping(review["visual_inspection"], "review.visual_inspection",
                     ("artifact", "sha256", "status", "reviewer", "observations"))
    require(visual["artifact"] == "architecture.svg" and visual["status"] == "inspected"
            and visual["sha256"] == artifacts["architecture.svg"]["sha256"], "review-binding",
            "review.visual_inspection", "visual inspection missing or stale")
    text(visual["reviewer"], "review.visual_inspection.reviewer")
    text(visual["observations"], "review.visual_inspection.observations")


def check_bundle(root: Path = DEFAULT_BUNDLE, profile: Profile = PRODUCTION) -> dict:
    """Return a bounded result without modifying the bundle or executing evidence."""
    bundle = None
    try:
        bundle = Bundle(root)
        artifacts = check_manifest(bundle, profile)
        check_specifications(bundle, profile)
        files = check_sources(bundle, profile)
        identities = check_denominator(bundle, profile, files)
        actions = check_actions(bundle, profile, identities, files)
        scoped = check_linkage(bundle, identities, files)
        check_execution(bundle, profile, artifacts)
        check_reports(bundle, profile, scoped)
        check_review(bundle, scoped, artifacts)
        bundle.finish()
        kinds = {kind: sum(1 for row in actions.values() if row["kind"] == kind) for kind in KINDS}
        return {"schema": "issue-1963-check/v1", "profile": profile.name, "status": "passed",
                "artifacts": len(artifacts), "actions": kinds, "findings": [], "boundary": BOUNDARY}
    except Refusal as exc:
        return {"schema": "issue-1963-check/v1", "profile": profile.name, "status": "failed",
                "findings": [exc.finding], "boundary": BOUNDARY}
    except (OSError, UnicodeError, RecursionError) as exc:
        return {"schema": "issue-1963-check/v1", "profile": profile.name, "status": "failed",
                "findings": [{"code": "read", "path": "bundle", "detail": f"unreadable evidence: {type(exc).__name__}"}],
                "boundary": BOUNDARY}
    finally:
        if bundle is not None:
            bundle.close()


# Writing ---------------------------------------------------------------------

def encode(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def write_new(path: Path, data: bytes) -> None:
    """Create one new regular file; an existing path or link is refused."""
    handle = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(handle, "wb") as stream:
        stream.write(data)


def physical_files(root: Path) -> list[str]:
    bundle = Bundle(root)
    try:
        return sorted(bundle.paths() - {"manifest.json"})
    finally:
        bundle.close()


def write_manifest(root: Path, profile: Profile) -> bytes:
    """Bind the files physically present; the fixed set is enforced by the check, not here."""
    bundle = Bundle(root)
    try:
        rows = []
        for name in sorted(bundle.paths() - {"manifest.json"}):
            data = bundle.load(name)
            rows.append({"path": name, "sha256": digest(data), "bytes": len(data)})
    finally:
        bundle.close()
    data = encode({"schema": "issue-1963-manifest/v1", "repository": profile.repository,
                   "start": profile.start, "artifacts": rows})
    handle = os.open(Path(root) / "manifest.json", os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644)
    with os.fdopen(handle, "wb") as stream:
        stream.write(data)
    return data


# Synthetic specimen ------------------------------------------------------------

_SYNTHETIC_FILES = {
    "SyntheticCore": (("src/Pool.sol", 120, "context"), ("src/PoolFactory.sol", 80, "context"),
                      ("src/Vault.sol", 40, "context"), ("src/libraries/Math.sol", 60, "support"),
                      ("lib/token/IERC20.sol", 20, "support")),
    "SyntheticLens": (("src/Lens.sol", 50, "context"), ("src/Pool.sol", 118, "excluded")),
}
_SYNTHETIC_CONTEXTS = {
    "Pool": ContextPin("SyntheticCore", "src/Pool.sol", "runtime"),
    "PoolFactory": ContextPin("SyntheticCore", "src/PoolFactory.sol", "runtime"),
    "Vault": ContextPin("SyntheticCore", "src/Vault.sol", "creation-target"),
    "Lens": ContextPin("SyntheticLens", "src/Lens.sol", "runtime"),
}
# (context, kind, signature, mutability, origin, line, families)
_SYNTHETIC_IDENTITIES = (
    ("Pool", "creation", "constructor()", "nonpayable", "ast", 10, ["creation"]),
    ("Pool", "state-changing", "deposit(uint256)", "nonpayable", "abi", 30, ["funding"]),
    ("Pool", "state-changing", "queueWithdrawal(uint256)", "nonpayable", "abi", 60, ["withdrawal-queue"]),
    ("Pool", "state-changing", "transfer(address,uint256)", "nonpayable", "abi", 90, ["transfer"]),
    ("Pool", "read", "balanceOf(address)", "view", "abi", 100, ["read"]),
    ("Pool", "read", "totalSupply()", "view", "abi", 105, ["read"]),
    ("PoolFactory", "creation", "constructor(address)", "nonpayable", "abi", 12, ["creation"]),
    ("PoolFactory", "state-changing", "createPool(address,(uint128,uint16)[])", "nonpayable", "abi", 40,
     ["administration", "creation"]),
    ("PoolFactory", "read", "pools(uint256)", "view", "abi", 70, ["read"]),
    ("Vault", "creation", "constructor(address,address)", "nonpayable", "abi", 8, ["creation"]),
    ("Vault", "state-changing", "release()", "nonpayable", "abi", 25, ["escrow-release"]),
    ("Lens", "creation", "constructor(address)", "nonpayable", "abi", 9, ["creation"]),
    ("Lens", "read", "getPool(address)", "view", "abi", 30, ["read"]),
)
_SYNTHETIC_FAMILIES = frozenset({"funding", "withdrawal-queue", "transfer", "administration", "escrow-release"})


def _synthetic_link(identity: dict) -> dict:
    signature = identity["signature"]
    line = int(identity["source_ref"].rsplit(":", 1)[1])
    base = {"id": identity["id"], "guards": [], "state_effects": [], "value_flows": [], "events": [],
            "dynamic_callees": [], "attribution": [], "gaps": [], "source_refs": [identity["source_ref"]]}
    path = identity["source_ref"].rsplit(":", 1)[0]
    event = lambda name, condition=None: {  # noqa: E731
        "event": name, "emitter": identity["context"], "relation": "direct",
        "source_ref": f"{path}:{line + 2}", "condition": condition}
    if signature == "deposit(uint256)":
        base.update(disposition="mapped", state_effects=["scaledBalance[msg.sender] increases"],
                    value_flows=["asset moves from msg.sender to the pool"],
                    events=[event("Deposit(address,uint256,uint256)"), event("Transfer(address,address,uint256)")],
                    attribution=["msg.sender is the depositor"], reason="both events are emitted on every success")
    elif signature == "queueWithdrawal(uint256)":
        base.update(disposition="conditional", state_effects=["a withdrawal batch is opened or extended"],
                    events=[event("WithdrawalQueued(uint32,address,uint256)"),
                            event("WithdrawalBatchCreated(uint32)", "only when no batch is open")],
                    reason="batch creation depends on whether a batch is open")
    elif signature == "transfer(address,uint256)":
        base.update(disposition="mapped", state_effects=["balances move between accounts"],
                    events=[event("Transfer(address,address,uint256)")], reason="emitted on every success")
    elif signature == "createPool(address,(uint128,uint16)[])":
        base.update(disposition="mapped", guards=["onlyOwner"], state_effects=["a pool is deployed"],
                    events=[event("PoolCreated(address,address)")], reason="emitted on every success")
    elif signature == "release()":
        base.update(disposition="unresolved", value_flows=["the escrowed token moves to the account"],
                    dynamic_callees=[{"call": "IERC20(asset).transfer", "limit": "arbitrary external token"}],
                    gaps=["the external token decides whether a Transfer is emitted"],
                    reason="the only event would come from an external token")
    else:
        base.update(disposition="eventless", state_effects=["immutable configuration is written"],
                    reason="the constructor emits no event")
    return base


def synthetic_bundle(root: Path) -> Profile:
    """Write a complete synthetic specimen under root and return the profile it satisfies.

    The specimen carries no source text. Its source rows are fabricated
    metadata; the check never reads source bytes, only their recorded identity.
    """
    root = Path(root)
    (root / "design-reports").mkdir(parents=True)
    (root / "evidence").mkdir()
    inputs, source_rows = {}, []
    for name, rows in _SYNTHETIC_FILES.items():
        files, projection = [], []
        for path, lines, disposition in rows:
            item = {"path": path, "sha256": digest(f"{name}:{path}".encode()), "bytes": lines * 40, "lines": lines}
            projection.append(item)
            files.append({**item, "disposition": disposition, "reason": f"synthetic {disposition} file"})
        projection.sort(key=lambda row: row["path"])
        input_digest = digest(f"synthetic input {name}".encode())
        pin = InputPin(input_digest, f"synthetic-{name.lower()}", f"https://example.invalid/{name}",
                       len(files), digest(canonical(projection)))
        inputs[name] = pin
        source_rows.append({"id": name, "sha256": pin.sha256, "partition": pin.partition,
                            "source_ref": pin.source_ref, "binding_limit": None,
                            "files": sorted(files, key=lambda row: row["path"])})
    anchors = {"registry": {"path": "synthetic/registry.json", "row": "synthetic", "sha256": digest(b"registry")}}
    compiler = {"version": "0.8.22+commit.4fc1097e", "via_ir": True}
    sources = {"schema": "issue-1963-sources/v1", "repository": "synthetic/protocol", "anchors": anchors,
               "compiler": compiler, "inputs": source_rows,
               "contexts": [{"contract": name, "input": pin.input, "source_path": pin.source_path, "kind": pin.kind}
                            for name, pin in _SYNTHETIC_CONTEXTS.items()],
               "dependencies": [{"subject": "external ERC20 assets", "limit": "their events are outside the map"}],
               "exclusions": [{"subject": "SyntheticLens src/Pool.sol", "reason": "Pool is bound to SyntheticCore"}]}
    identities = []
    for context, kind, signature, mutability, origin, line, _ in _SYNTHETIC_IDENTITIES:
        pin = _SYNTHETIC_CONTEXTS[context]
        row = {"input": pin.input, "context": context, "kind": kind, "signature": signature,
               "selector": None if kind == "creation" else selector(signature), "mutability": mutability,
               "declared_in": context, "source_ref": f"{pin.source_path}:{line}", "origin": origin}
        identities.append({"id": action_id(row), **row})
    identities.sort(key=lambda row: row["id"])
    projection = [{key: row[key] for key in ("id", "selector", "mutability", "declared_in", "origin")}
                  for row in identities]
    denominator = {"schema": "issue-1963-denominator-inputs/v1",
                   "derivations": [{"input": name, "original_input_sha256": pin.sha256,
                                    "prepared_input_sha256": digest(f"prepared {name}".encode()),
                                    "output_sha256": digest(f"output {name}".encode()),
                                    "compiler": compiler["version"], "argv": ["solc", "--standard-json"], "exit": 0}
                                   for name, pin in inputs.items()],
                   "identities": identities}
    families = {action_id({"input": _SYNTHETIC_CONTEXTS[c].input, "context": c, "kind": k, "signature": s}): f
                for c, k, s, _, _, _, f in _SYNTHETIC_IDENTITIES}
    actions = {"schema": "issue-1963-actions/v1",
               "actions": [{"id": row["id"], "input": row["input"], "context": row["context"], "kind": row["kind"],
                            "signature": row["signature"], "families": families[row["id"]],
                            "summary": f"synthetic {row['kind']} action", "source_refs": [row["source_ref"]]}
                           for row in identities]}
    scoped = [row for row in identities if row["kind"] in SCOPED_KINDS]
    linkage = {"schema": "issue-1963-linkage/v1", "actions": [_synthetic_link(row) for row in scoped]}
    executions = {"derive-SyntheticCore": 0, "derive-SyntheticLens": 0, "coverage-default": 1}
    (root / "evidence/coverage-default.log").write_bytes(b"synthetic build failure retained as observed\n")
    execution = {"schema": "issue-1963-execution/v1", "records": [
        {"id": name, "purpose": "synthetic observation", "argv": ["synthetic", name], "exit": code,
         "status": "passed" if code == 0 else "failed",
         "log": None if code == 0 else {"path": "evidence/coverage-default.log",
                                        "sha256": digest((root / "evidence/coverage-default.log").read_bytes())},
         "observation": "synthetic"} for name, code in executions.items()]}
    commit = "0" * 40
    report_ids = "\n".join(f"- `{row['id']}`" for row in scoped)
    reports = {
        "x-ray.md": f"# X-Ray\n\nSource {commit}.\n\n## Overview\n## Threat model\n## Invariants\n## Docs\n"
                    "## Tests\n## Git history\n## X-Ray verdict\n",
        "entry-points.md": f"# Entry points\n\nSource {commit}.\n\n## Permissionless\n## Role-gated\n"
                           f"## Initialization\n## External calls\n\n{report_ids}\n",
        "invariants.md": f"# Invariants\n\nSource {commit}.\n\n## Enforced guards\n## Single-contract\n"
                         "## Cross-contract\n## Economic\n",
        "architecture.json": encode({"title": "synthetic", "edges": [
            {"from": "PoolFactory", "to": "Pool", "label": "deploys"}],
            "nodes": [{"id": name, "label": name, "kind": pin.kind} for name, pin in _SYNTHETIC_CONTEXTS.items()]}),
        "architecture.svg": "<svg xmlns=\"http://www.w3.org/2000/svg\">"
                            + "".join(f"<text>{name}</text>" for name in _SYNTHETIC_CONTEXTS) + "</svg>\n",
    }
    records_out = {"sources.json": encode(sources), "denominator-inputs.json": encode(denominator),
                   "actions.json": encode(actions), "linkage.json": encode(linkage),
                   "execution.json": encode(execution), "README.md": b"# Synthetic specimen\n",
                   "study.md": b"# Synthetic study\n", "runbook.md": b"# Synthetic runbook\n"}
    records_out.update({name: body if isinstance(body, bytes) else body.encode() for name, body in reports.items()})
    report = encode({"schema": "protasis-design-report/v1", "candidate": "synthetic", "criterion": "gate",
                     "command": "synthetic", "exit": 0, "unit": "boolean", "value": True})
    records_out["design-reports/synthetic-gate.json"] = report
    records_out["design-evidence.json"] = encode({"schema": "protasis-design-evidence/v1", "results": [
        {"candidate": "synthetic", "criterion": "gate", "state": "pass",
         "report": {"path": "design-reports/synthetic-gate.json", "sha256": digest(report)}}]})
    for name, data in records_out.items():
        (root / name).write_bytes(data)
    reviewed = {name: {"path": name, "sha256": digest((root / name).read_bytes())} for name in REVIEWED_ARTIFACTS}
    review = {"schema": "issue-1963-review/v1", "producer": "synthetic-producer", "reviewer": "synthetic-reviewer",
              "status": "complete", "method": "read every scoped action against the synthetic source rows",
              "linkage": reviewed["linkage.json"], "actions": reviewed["actions.json"],
              "reviewed_actions": sorted(row["id"] for row in scoped),
              "findings": [{"id": "R-1", "status": "resolved", "summary": "a synthetic finding",
                            "resolution": "fixed before the review was bound"}],
              "resolved_finding_ids": ["R-1"], "open_findings": [],
              "artifacts": [reviewed[name] for name in sorted(reviewed)],
              "visual_inspection": {"artifact": "architecture.svg", "sha256": reviewed["architecture.svg"]["sha256"],
                                    "status": "inspected", "reviewer": "synthetic-reviewer",
                                    "observations": "every context is labelled"},
              "boundary": "synthetic review"}
    (root / "review.json").write_bytes(encode(review))
    specifications = {name: digest((root / name).read_bytes())
                      for name in ("study.md", "runbook.md", "design-evidence.json")}
    profile = Profile(
        name="synthetic", repository="synthetic/protocol", start="1" * 40, anchors=anchors, compiler=compiler,
        inputs=inputs, contexts=_SYNTHETIC_CONTEXTS,
        artifacts=frozenset(records_out) | {"review.json", "evidence/coverage-default.log"},
        specifications=specifications, denominator=(len(identities), digest(canonical(projection))),
        executions=frozenset(executions), families=_SYNTHETIC_FAMILIES, commits=(commit,))
    write_manifest(root, profile)
    return profile


# Hostile specimens -------------------------------------------------------------

def _load(root: Path, name: str) -> dict:
    return json.loads((root / name).read_bytes())


def _save(root: Path, name: str, value: dict) -> None:
    (root / name).write_bytes(encode(value))


def _edit(name: str, change):
    def apply(root: Path, profile: Profile) -> None:
        value = _load(root, name)
        change(value)
        _save(root, name, value)
        write_manifest(root, profile)
    return apply


def _alter_input(value: dict) -> None:
    value["inputs"][0]["sha256"] = digest(b"altered input")


def _drop_source_file(value: dict) -> None:
    value["inputs"][0]["files"].pop()


def _omit_action(value: dict) -> None:
    value["actions"].pop()


def _mismatch_signature(value: dict) -> None:
    row = next(row for row in value["actions"] if row["kind"] == "state-changing")
    row["signature"] = row["signature"].replace("(", "Altered(", 1)


def _drop_disposition(value: dict) -> None:
    del value["actions"][0]["disposition"]


def _stale_reference(value: dict) -> None:
    row = value["actions"][0]
    path = row["source_refs"][0].rsplit(":", 1)[0]
    row["source_refs"][0] = f"{path}:999999"


def _semantic_edit(value: dict) -> None:
    value["actions"][0]["reason"] += " (edited after review)"


def _incomplete_review(value: dict) -> None:
    value["reviewed_actions"].pop()


def _self_review(value: dict) -> None:
    value["reviewer"] = value["producer"]


def _open_finding(value: dict) -> None:
    value["open_findings"].append({"id": "R-open", "summary": "unresolved"})


def _identity_mismatch(value: dict) -> None:
    row = next(row for row in value["identities"] if row["kind"] == "state-changing")
    row["context"] = next(other["context"] for other in value["identities"]
                          if other["input"] == row["input"] and other["context"] != row["context"])


def _non_canonical(value: dict) -> None:
    row = next(row for row in value["identities"] if "uint256" in row["signature"] and row["kind"] != "creation")
    row["signature"] = row["signature"].replace("uint256", "uint", 1)
    row["id"] = action_id(row)
    row["selector"] = selector(row["signature"])


def _event_on_eventless(value: dict) -> None:
    row = next(row for row in value["actions"] if row["disposition"] == "eventless")
    row["events"].append({"event": "Stray(uint256)", "emitter": "unknown", "relation": "direct",
                          "source_ref": row["source_refs"][0], "condition": None})


def _duplicate_key(root: Path, profile: Profile) -> None:
    data = (root / "actions.json").read_bytes()
    (root / "actions.json").write_bytes(data.replace(b"{", b'{"schema": "issue-1963-actions/v1", ', 1))
    write_manifest(root, profile)


def _unsafe_manifest_path(root: Path, profile: Profile) -> None:
    value = _load(root, "manifest.json")
    value["artifacts"][0]["path"] = "../escape.json"
    _save(root, "manifest.json", value)


def _linked_artifact(root: Path, profile: Profile) -> None:
    target = root / "README.md"
    target.unlink()
    target.symlink_to("study.md")


def _oversized_artifact(root: Path, profile: Profile) -> None:
    with (root / "README.md").open("ab") as stream:
        stream.truncate(MAX_FILE_BYTES + 1)
    value = _load(root, "manifest.json")
    for row in value["artifacts"]:
        if row["path"] == "README.md":
            row["bytes"] = MAX_FILE_BYTES + 1
    _save(root, "manifest.json", value)


def _omit_artifact_and_rebind(root: Path, profile: Profile) -> None:
    (root / "architecture.svg").unlink()
    write_manifest(root, profile)


def _drop_review(root: Path, profile: Profile) -> None:
    (root / "review.json").unlink()
    write_manifest(root, profile)


def _omit_identity_everywhere(root: Path, profile: Profile) -> None:
    """Remove one read identity from both the denominator and the action rows: a joint omission."""
    denominator = _load(root, "denominator-inputs.json")
    victim = next(row["id"] for row in denominator["identities"] if row["kind"] == "read")
    denominator["identities"] = [row for row in denominator["identities"] if row["id"] != victim]
    _save(root, "denominator-inputs.json", denominator)
    actions = _load(root, "actions.json")
    actions["actions"] = [row for row in actions["actions"] if row["id"] != victim]
    _save(root, "actions.json", actions)
    write_manifest(root, profile)


# The demonstration set is the named study list; the scaffold set adds the
# input-boundary and joint-omission mechanisms. Each entry: (name, code, apply).
DEMONSTRATION = (
    ("altered-source-identity", "source-identity", _edit("sources.json", _alter_input)),
    ("omitted-action", "action-membership", _edit("actions.json", _omit_action)),
    ("mismatched-signature", "signature", _edit("actions.json", _mismatch_signature)),
    ("missing-disposition", "disposition", _edit("linkage.json", _drop_disposition)),
    ("stale-source-reference", "source-reference", _edit("linkage.json", _stale_reference)),
    ("stale-review-digest", "review-binding", _edit("linkage.json", _semantic_edit)),
    ("incomplete-review", "review-coverage", _edit("review.json", _incomplete_review)),
)
SCAFFOLD = DEMONSTRATION + (
    ("source-membership", "source-membership", _edit("sources.json", _drop_source_file)),
    ("duplicate-key", "json", _duplicate_key),
    ("unsafe-manifest-path", "unsafe-path", _unsafe_manifest_path),
    ("linked-artifact", "unsafe-path", _linked_artifact),
    ("oversized-artifact", "limit", _oversized_artifact),
    ("action-identity", "action-identity", _edit("denominator-inputs.json", _identity_mismatch)),
    ("non-canonical-signature", "signature", _edit("denominator-inputs.json", _non_canonical)),
    ("event-on-eventless", "disposition", _edit("linkage.json", _event_on_eventless)),
    ("self-review", "review-independence", _edit("review.json", _self_review)),
    ("open-finding", "review-findings", _edit("review.json", _open_finding)),
    ("omitted-artifact-rebound", "inventory", _omit_artifact_and_rebind),
    ("joint-omission", "denominator", _omit_identity_everywhere),
    ("incomplete-product", "inventory", _drop_review),
)


def run_specimens(source: Path, profile: Profile, catalogue: tuple) -> list[dict]:
    """Copy source once per hostile specimen, apply it, and record the observed refusal."""
    observed = []
    for name, code, apply in catalogue:
        with tempfile.TemporaryDirectory(prefix="issue-1963-") as scratch:
            target = Path(scratch) / "bundle"
            shutil.copytree(source, target, symlinks=True)
            try:
                apply(target, profile)
                result = check_bundle(target, profile)
                finding = result["findings"][0] if result["findings"] else None
            except (Refusal, OSError, ValueError, KeyError, StopIteration, IndexError) as exc:
                result, finding = {"status": "error"}, {"code": "specimen-error", "path": name,
                                                          "detail": type(exc).__name__}
            actual = finding["code"] if finding else None
            observed.append({"name": name, "expected": code, "observed": actual,
                             "status": "refused-as-expected" if result["status"] == "failed" and actual == code
                             else "unexpected", "finding": finding})
    return observed


def scaffold_matrix() -> dict:
    """Run the complete synthetic specimen and every scaffold hostile specimen."""
    with tempfile.TemporaryDirectory(prefix="issue-1963-") as scratch:
        root = Path(scratch) / "bundle"
        root.mkdir()
        profile = synthetic_bundle(root)
        positive = check_bundle(root, profile)
        specimens = run_specimens(root, profile, SCAFFOLD)
    passed = positive["status"] == "passed" and all(row["status"] == "refused-as-expected" for row in specimens)
    return {"positive": positive, "specimens": specimens, "status": "passed" if passed else "failed"}


# Private source admission ------------------------------------------------------

def source_projection(value: dict, where: str) -> list[dict]:
    sources = value.get("sources")
    require(isinstance(sources, dict) and bool(sources), "source-membership", where, "input has no sources")
    rows = []
    for path in sorted(sources):
        entry = sources[path]
        require(isinstance(entry, dict) and isinstance(entry.get("content"), str), "source-membership",
                f"{where}.{path}", "source content missing")
        data = entry["content"].encode("utf-8")
        lines = entry["content"].count("\n") + (0 if not entry["content"] or entry["content"].endswith("\n") else 1)
        rows.append({"path": path, "sha256": digest(data), "bytes": len(data), "lines": lines})
    return rows


def admit_inputs(directory: Path, profile: Profile = PRODUCTION) -> dict:
    """Check each private accepted input's bytes, sources and settings; report identities only."""
    rows, status = [], "passed"
    for name, pin in sorted(profile.inputs.items()):
        row = {"id": name, "expected_sha256": pin.sha256}
        try:
            reader = Bundle(directory)
            try:
                data = reader.read(f"{name}.json")
            finally:
                reader.close()
            require(len(data) <= MAX_INPUT_BYTES, "limit", name, "input exceeds 8 MiB")
            row["sha256"] = digest(data)
            require(row["sha256"] == pin.sha256, "source-identity", name, "accepted input digest differs")
            value = json_value(data, name)
            require(isinstance(value, dict) and value.get("language") == "Solidity", "compiler", name,
                    "not a Solidity standard JSON input")
            settings = value.get("settings") or {}
            observed = {"evm_version": settings.get("evmVersion"),
                        "optimizer_runs": (settings.get("optimizer") or {}).get("runs"),
                        "via_ir": settings.get("viaIR"),
                        "bytecode_hash": (settings.get("metadata") or {}).get("bytecodeHash")}
            expected = {key: profile.compiler.get(key) for key in observed}
            require(observed == expected and (settings.get("optimizer") or {}).get("enabled") is True,
                    "compiler", name, "compiler settings differ")
            projection = source_projection(value, name)
            row.update(files=len(projection), projection=digest(canonical(projection)))
            require(len(projection) == pin.files and row["projection"] == pin.projection,
                    "source-membership", name, "source projection differs from the pin")
            row["status"] = "admitted"
        except Refusal as exc:
            row.update(status="refused", finding=exc.finding)
            status = "failed"
        rows.append(row)
    return {"schema": "issue-1963-admission/v1", "status": status, "inputs": rows,
            "boundary": "Reports digests and counts only; no source text, compiler input or output is copied."}


# Commands ----------------------------------------------------------------------

@contextlib.contextmanager
def network_disabled():
    """Refuse every socket this process tries to open while the demonstration runs."""
    def refuse(*_args, **_kwargs):
        raise OSError("network use is disabled during the #1963 demonstration")

    saved = (socket.socket, socket.create_connection, socket.getaddrinfo)
    socket.socket, socket.create_connection, socket.getaddrinfo = refuse, refuse, refuse
    try:
        yield
    finally:
        socket.socket, socket.create_connection, socket.getaddrinfo = saved


def demonstrate(root: Path, profile: Profile = PRODUCTION) -> dict:
    started = time.perf_counter()
    with network_disabled():
        positive = check_bundle(root, profile)
        specimens = run_specimens(root, profile, DEMONSTRATION) if positive["status"] == "passed" else []
    passed = positive["status"] == "passed" and len(specimens) == len(DEMONSTRATION) and all(
        row["status"] == "refused-as-expected" for row in specimens)
    return {"schema": "issue-1963-demo/v1", "status": "passed" if passed else "failed", "network": "disabled",
            "positive": positive, "specimens": specimens,
            "counts": {"expected": len(DEMONSTRATION), "refused_as_expected":
                       sum(row["status"] == "refused-as-expected" for row in specimens)},
            "duration_ms": round((time.perf_counter() - started) * 1000),
            "boundary": BOUNDARY}


def design_value(criterion: str, root: Path) -> bool:
    if criterion == "checked-scaffold":
        return scaffold_matrix()["status"] == "passed"
    if criterion == "reviewed-map":
        return check_bundle(root)["status"] == "passed"
    return demonstrate(root)["status"] == "passed"


def run(arguments, parser) -> int:
    command = arguments.command
    root = arguments.bundle or DEFAULT_BUNDLE
    needs = {"design-report": ("candidate", "criterion", "report"), "demo": ("report",),
             "admit": ("inputs", "report"), "derive": ("inputs", "out")}
    absent = [f"--{name}" for name in needs.get(command, ()) if getattr(arguments, name) is None]
    if absent:
        parser.error(f"{command} requires " + " ".join(absent))
    if command == "check":
        result = check_bundle(root)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["status"] == "passed" else 1
    if command == "manifest":
        try:
            missing = sorted(PRODUCTION.artifacts - set(physical_files(root)))
            if missing:
                print(json.dumps({"code": "inventory", "detail": "fixed artifacts absent", "paths": missing}),
                      file=sys.stderr)
                return 1
            write_manifest(root, PRODUCTION)
        except Refusal as exc:
            print(json.dumps(exc.finding, sort_keys=True), file=sys.stderr)
            return 1
        except OSError as exc:
            print(json.dumps({"code": "manifest-write", "detail": type(exc).__name__}), file=sys.stderr)
            return 2
        return 0
    if command == "derive":
        print(json.dumps({"code": "unavailable", "detail": "the compiler-output derivation lands in Step 2"}),
              file=sys.stderr)
        return 2
    try:
        if command == "design-report":
            if arguments.candidate != SELECTED_CANDIDATE:
                print(json.dumps({"code": "candidate", "detail": "only the selected shared-input-index layout is "
                                  "implemented; the other candidate's conformance cells stay pending"}), file=sys.stderr)
                return 2
            value = design_value(arguments.criterion, root)
            argv = ["python3", "scripts/kickoff_xray_1963.py", "design-report", "--candidate", arguments.candidate,
                    "--criterion", arguments.criterion, "--report", arguments.report.as_posix()]
            if arguments.bundle is not None:
                argv += ["--bundle", arguments.bundle.as_posix()]
            result = {"schema": "protasis-design-report/v1", "candidate": arguments.candidate,
                      "criterion": arguments.criterion, "command": shlex.join(argv), "exit": 0,
                      "unit": "boolean", "value": value}
            write_new(arguments.report, encode(result))
            print(json.dumps(result, sort_keys=True))
            return 0
        if command == "demo":
            result = demonstrate(root)
        else:
            result = admit_inputs(arguments.inputs)
        write_new(arguments.report, encode(result))
        print(json.dumps({"status": result["status"], "report": arguments.report.as_posix()}, sort_keys=True))
        return 0 if result["status"] == "passed" else 1
    except FileExistsError:
        print(json.dumps({"code": "report-write", "detail": "report path must be new"}), file=sys.stderr)
        return 2
    except OSError as exc:
        print(json.dumps({"code": "report-write", "detail": type(exc).__name__}), file=sys.stderr)
        return 2
