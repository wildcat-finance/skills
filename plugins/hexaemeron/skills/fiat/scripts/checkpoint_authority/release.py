"""Digest-bound release inventory and the consumer lock that pins it externally.

The manifest lists every release component by exact bytes and never hashes
itself; the immutable source commit and the manifest digest live in the
consumer's `protocol.lock.json`. Authority and native toolchain pins stay
separate, and a mutable reference or a component from another release refuses.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys

from . import native_io as io
from .canonical import MAX_ENTRIES, MAX_RECORD_BYTES, MAX_TOTAL_BYTES, Refusal, canonical, decode, digest
from .native_records import PROFILE
from .schema import COMMIT, HASH, PROFILE as SIGNATURE_PROFILE, PROTOCOL, RECORD_TYPES, enum, obj, string, validate

SCHEMA = "checkpoint-authority-release/v1"
LOCK_SCHEMA = "checkpoint-authority-protocol-lock/v1"
STAGE = "release"
CORPUS = "plugins/hexaemeron/skills/fiat/checkpoint-authority/"
SCRIPTS = "plugins/hexaemeron/skills/fiat/scripts/"
DOCS = "docs/checkpoint-authority/"
MANIFEST = CORPUS + "release-manifest.json"
LOCK_EXAMPLE = DOCS + "protocol.lock.json"
MODULES = ("__init__", "canonical", "conformance", "coverage", "demo", "eligibility", "native",
           "native_conformance", "native_io", "native_records", "network", "parents", "records", "release",
           "release_conformance", "replay", "replay_conformance", "schema", "signatures", "trust",
           "verifier", "wire")
CORPUS_MANIFESTS = (CORPUS + "fixtures/manifest.json", CORPUS + "fixtures/replay-manifest.json",
                    CORPUS + "native-manifest.json", CORPUS + "fixtures/interoperability-manifest.json")
COMPONENTS = {
    "schemas": tuple(CORPUS + "schemas/" + kind + ".schema.json" for kind in RECORD_TYPES),
    "verifier": (*(SCRIPTS + "checkpoint_authority/" + name + ".py" for name in MODULES),
                 SCRIPTS + "checkpoint_authority.py"),
    "fixtures": CORPUS_MANIFESTS,
    "capabilities": (CORPUS + "native-capabilities.json",),
    "native": (CORPUS + "native-profile.json",),
    "tools": (CORPUS + "tool-profile.json",),
    "documentation": (SCRIPTS.replace("scripts/", "references/") + "checkpoint-authority.md",
                      DOCS + "release.md", CORPUS + "schemas/README.md", CORPUS + "fixtures/README.md"),
}
ENUMERATED = (CORPUS, SCRIPTS + "checkpoint_authority/", SCRIPTS + "checkpoint_authority.py")
FILE_MAX = io.FILE_MAX
MANIFEST_MAX = 1048576
LOCK_MAX = 16384
ASSET_PLATFORM = re.compile(r"[a-z]+-[a-z0-9]+\Z")
COMMIT_FORM = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
RESOURCE_LIMITS = {
    "component_file_bytes": FILE_MAX, "release_manifest_bytes": MANIFEST_MAX,
    "consumer_lock_bytes": LOCK_MAX, "control_record_bytes": MAX_RECORD_BYTES,
    "history_entries": MAX_ENTRIES, "history_bytes": MAX_TOTAL_BYTES,
    "declared_peak_rss_ceiling_bytes": 536870912,
}
"""Declared supported ceilings for a released verification; none is a measured result."""
ROW = obj(path=string(maximum=512), sha256=HASH,
          bytes={"type": "integer", "minimum": 0, "maximum": FILE_MAX})
REFERENCE = obj(path=string(maximum=512), sha256=HASH)
ASSET = obj(sha256=HASH, bytes={"type": "integer", "minimum": 1, "maximum": 2**31})
VERSION = string(r"^[0-9]+\.[0-9]+\.[0-9]+$", 32)
AUTHORITY = obj(source_commit=string(maximum=128), release_manifest_sha256=HASH,
                artifact_sha256=HASH, schema_set_sha256=HASH, verifier_sha256=HASH,
                fixture_corpus_sha256=HASH)
NATIVE = obj(source_commit=string(maximum=128), executable_sha256=HASH,
             profile=string(maximum=128))
LOCK_SECTIONS = ("schema", "protocol", "authority", "native", "tools")
PLACEHOLDER_COMMIT = "0" * 40
"""The example lock's own authority commit; a consumer replaces it with the merged commit."""


def _path(path):
    """Manifest paths name canonical relative leaves below the caller's release root."""
    if (path.startswith("/") or "\\" in path
            or any(part in ("", ".", "..") for part in path.split("/"))
            or any(ord(char) < 32 or ord(char) == 127 for char in path)):
        raise Refusal("component-path", STAGE)
    return path


def _hash(root, path):
    path = _path(path)
    try:
        return io.hash_file(root / path, FILE_MAX)
    except Refusal as error:
        if error.code == "native-file-limit-or-kind":
            raise Refusal("component-unsafe", STAGE) from None
        raise Refusal("component-missing", STAGE) from None
    except OSError:
        raise Refusal("component-missing", STAGE) from None


def _read_json(root, path, maximum):
    try:
        return decode(io.read(root / path, maximum), limit=maximum)
    except (Refusal, OSError):
        raise Refusal("component-missing", STAGE) from None


def _rows(root, paths):
    rows = []
    for path in paths:
        sha256, size = _hash(root, path)
        rows.append({"path": path, "sha256": sha256, "bytes": size})
    return rows


def _corpus_rows(root):
    """Follow each corpus manifest's own `files` rows; they bind fixtures transitively."""
    covered = {}
    for path in CORPUS_MANIFESTS:
        value = _read_json(root, path, MANIFEST_MAX)
        rows = value.get("files") if type(value) is dict else None
        if type(rows) is not list or not 1 <= len(rows) <= 256:
            raise Refusal("corpus-manifest-shape", STAGE)
        for row in rows:
            if type(row) is not dict or set(row) != {"path", "sha256"}:
                raise Refusal("corpus-manifest-shape", STAGE)
            validate(row["path"], string(maximum=512))
            validate(row["sha256"], HASH)
            _path(row["path"])
            if covered.setdefault(row["path"], row["sha256"]) != row["sha256"]:
                raise Refusal("corpus-manifest-conflict", STAGE)
    return covered


def _assets(value):
    """Platform-keyed cosign assets; `validate` cannot express a bounded key grammar."""
    if type(value) is not dict or not 1 <= len(value) <= 16:
        raise Refusal("component-shape", STAGE)
    for name, asset in value.items():
        if ASSET_PLATFORM.fullmatch(name) is None:
            raise Refusal("component-shape", STAGE)
        validate(asset, ASSET)
    return value


def _lock_fields(value):
    """The lock's closed shape; the platform-keyed asset map is checked separately."""
    if type(value) is not dict or set(value) != set(LOCK_SECTIONS):
        raise Refusal("lock-fields", STAGE)
    validate(value["schema"], enum(LOCK_SCHEMA))
    validate(value["protocol"], enum(PROTOCOL))
    validate(value["authority"], AUTHORITY)
    validate(value["native"], NATIVE)
    tools = value["tools"]
    if (type(tools) is not dict or set(tools) != {"cosign", "python"}
            or type(tools["cosign"]) is not dict or set(tools["cosign"]) != {"version", "assets"}):
        raise Refusal("lock-fields", STAGE)
    validate(tools["cosign"]["version"], VERSION)
    validate(tools["python"], VERSION)
    _assets(tools["cosign"]["assets"])


def build(root):
    """Compute the manifest from the tree; the same tree yields the same bytes."""
    root = Path(root)
    components = {}
    for name, paths in COMPONENTS.items():
        rows = _rows(root, paths)
        components[name] = {"sha256": digest(canonical(rows, limit=MANIFEST_MAX)), "files": rows}
    corpus_rows = [{"path": path, "sha256": sha256}
                   for path, sha256 in sorted(_corpus_rows(root).items())]
    profile = _read_json(root, CORPUS + "native-profile.json", MANIFEST_MAX)
    tools = _read_json(root, CORPUS + "tool-profile.json", MANIFEST_MAX)
    if (type(profile) is not dict or type(tools) is not dict
            or profile.get("schema") != "checkpoint-authority-native-source/v1"
            or tools.get("schema") != "checkpoint-authority-tool-profile/v1"
            or tools.get("signature_profile") != SIGNATURE_PROFILE
            or type(tools.get("cosign")) is not dict
            or set(tools["cosign"]) != {"version", "assets"}):
        raise Refusal("component-shape", STAGE)
    validate(profile.get("source_commit"), COMMIT)
    validate(profile.get("executable_sha256"), HASH)
    validate(tools["cosign"]["version"], VERSION)
    native = {"source_commit": profile["source_commit"], "executable_sha256": profile["executable_sha256"],
              "profile": PROFILE, "profile_sha256": components["native"]["files"][0]["sha256"]}
    toolchain = {"cosign": {"version": tools["cosign"]["version"],
                            "assets": _assets(tools["cosign"]["assets"])},
                 "python": python_pin(root)}
    validate(toolchain["python"], VERSION)
    pins = {"schema_set_sha256": components["schemas"]["sha256"],
            "verifier_sha256": components["verifier"]["sha256"],
            "fixture_corpus_sha256": digest(canonical(
                {"direct": components["fixtures"]["sha256"], "transitive": corpus_rows}, limit=MANIFEST_MAX))}
    pins["artifact_sha256"] = digest(canonical(
        {"components": {name: value["sha256"] for name, value in components.items()},
         "native": native, "tools": toolchain, "pins": pins}, limit=MANIFEST_MAX))
    from .verifier import LIMITS
    return {"schema": SCHEMA, "protocol": PROTOCOL, "signature_profile": SIGNATURE_PROFILE,
            "record_types": list(RECORD_TYPES), "components": components,
            "transitive_files": corpus_rows, "native": native, "tools": toolchain, "pins": pins,
            "limits": LIMITS, "resource_limits": RESOURCE_LIMITS,
            "external_pins": ["source_commit", "release_manifest_sha256"],
            "note": "The source commit and this file's digest are pinned by the consumer lock, "
                    "never by this file."}


def python_pin(root):
    """The repository interpreter pin; the ambient interpreter is a fallback, not authority."""
    try:
        return io.read(Path(root) / ".python-version", 64).decode().strip()
    except (Refusal, OSError, UnicodeError):
        return sys.version.split()[0]


def encode(manifest):
    return (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode()


def committed(root):
    """The manifest bytes present in the tree, bounded and read without following links."""
    try:
        data = io.read(Path(root) / MANIFEST, MANIFEST_MAX)
    except (Refusal, OSError):
        raise Refusal("manifest-missing", STAGE) from None
    value = decode(data, limit=MANIFEST_MAX)
    if type(value) is not dict or value.get("schema") != SCHEMA:
        raise Refusal("manifest-shape", STAGE)
    return data, value


def _enumerate(root):
    found = []
    for prefix in ENUMERATED:
        target = Path(root) / prefix
        if target.is_file():
            found.append(prefix)
            continue
        for directory, names, files in os.walk(target):
            names[:] = sorted(name for name in names if name != "__pycache__" and not name.startswith("."))
            for name in sorted(files):
                if name.startswith("."):
                    continue
                found.append((Path(directory) / name).relative_to(root).as_posix())
    return found


def check(root):
    """Refuse altered, missing, extra or stale components before returning the rebuilt manifest."""
    root = Path(root)
    data, value = committed(root)
    listed = {}
    components = value.get("components")
    if type(components) is not dict or set(components) != set(COMPONENTS):
        raise Refusal("manifest-shape", STAGE)
    for name, paths in COMPONENTS.items():
        rows = components[name].get("files") if type(components[name]) is dict else None
        if type(rows) is not list or [row.get("path") for row in rows if type(row) is dict] != list(paths):
            raise Refusal("manifest-shape", STAGE)
        for row in rows:
            validate(row, ROW)
            listed[row["path"]] = row["sha256"]
    rows = value.get("transitive_files")
    if type(rows) is not list or not 1 <= len(rows) <= 256 * len(CORPUS_MANIFESTS):
        raise Refusal("manifest-shape", STAGE)
    for row in rows:
        try:
            validate(row, REFERENCE)
        except Refusal:
            raise Refusal("manifest-shape", STAGE) from None
        _path(row["path"])
    paths = [row["path"] for row in rows]
    if paths != sorted(set(paths)):
        raise Refusal("manifest-shape", STAGE)
    for row in rows:
        if row["path"] in listed and listed[row["path"]] != row["sha256"]:
            raise Refusal("manifest-shape", STAGE)
        listed.setdefault(row["path"], row["sha256"])
    for path, expected in listed.items():
        if _hash(root, path)[0] != expected:
            raise Refusal("component-drift", STAGE)
    for path in _enumerate(root):
        if path != MANIFEST and path not in listed:
            raise Refusal("component-extra", STAGE)
    rebuilt = build(root)
    if encode(rebuilt) != data:
        raise Refusal("manifest-stale", STAGE)
    return rebuilt


def lock_example(manifest_bytes, manifest):
    """A consumer lock over one manifest; the authority commit is the consumer's to fill in."""
    return {"schema": LOCK_SCHEMA, "protocol": PROTOCOL,
            "authority": {"source_commit": PLACEHOLDER_COMMIT,
                          "release_manifest_sha256": digest(manifest_bytes),
                          **{key: manifest["pins"][key] for key in
                             ("artifact_sha256", "schema_set_sha256", "verifier_sha256",
                              "fixture_corpus_sha256")}},
            "native": {key: manifest["native"][key] for key in
                       ("source_commit", "executable_sha256", "profile")},
            "tools": {"cosign": {"version": manifest["tools"]["cosign"]["version"],
                                 "assets": manifest["tools"]["cosign"]["assets"]},
                      "python": manifest["tools"]["python"]}}


def lock_check(lock_bytes, root, *, source_commit=None):
    """Hold a consumer lock to the tree: recompute every digest, refuse mutable or mixed pins.

    `source_commit` is the caller's own answer for the checked-out commit; the
    lock is compared against it and this function never runs Git.
    """
    if type(lock_bytes) is not bytes or len(lock_bytes) > LOCK_MAX:
        raise Refusal("lock-limit", STAGE)
    lock = decode(lock_bytes, limit=LOCK_MAX)
    try:
        _lock_fields(lock)
    except Refusal:
        raise Refusal("lock-fields", STAGE) from None
    for value in (lock["authority"]["source_commit"], lock["native"]["source_commit"]):
        if COMMIT_FORM.fullmatch(value) is None:
            raise Refusal("mutable-source-reference", STAGE)
    if source_commit is not None:
        if type(source_commit) is not str or COMMIT_FORM.fullmatch(source_commit) is None:
            raise Refusal("mutable-source-reference", STAGE)
        if source_commit != lock["authority"]["source_commit"]:
            raise Refusal("source-commit-mismatch", STAGE)
    data, _ = committed(root)
    if digest(data) != lock["authority"]["release_manifest_sha256"]:
        raise Refusal("release-manifest-mismatch", STAGE)
    manifest = check(root)
    for key in ("artifact_sha256", "schema_set_sha256", "verifier_sha256", "fixture_corpus_sha256"):
        if lock["authority"][key] != manifest["pins"][key]:
            raise Refusal("mixed-components", STAGE)
    if lock["native"] != {key: manifest["native"][key] for key in
                          ("source_commit", "executable_sha256", "profile")}:
        raise Refusal("unsupported-native-pin", STAGE)
    if lock["tools"]["cosign"] != manifest["tools"]["cosign"]:
        raise Refusal("unsupported-tool-pin", STAGE)
    if lock["tools"]["python"] != manifest["tools"]["python"]:
        raise Refusal("unsupported-python-pin", STAGE)
    return {"schema": "checkpoint-authority-lock-check/v1", "event": "checkpoint_authority_lock_verified",
            "stage": STAGE, "code": "lock-agrees", "complete": True,
            "source_commit_asserted": source_commit is not None,
            "source_commit": lock["authority"]["source_commit"],
            "release_manifest_sha256": lock["authority"]["release_manifest_sha256"],
            "pins": manifest["pins"], "native": manifest["native"],
            "tools": {"cosign": manifest["tools"]["cosign"]["version"],
                      "python": manifest["tools"]["python"]}}
