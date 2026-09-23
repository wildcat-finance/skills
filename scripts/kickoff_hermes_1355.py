#!/usr/bin/env python3
"""Check the issue 1355 protected inventory and write its design reports.

`check` validates the committed inventory against the registry's
`wildcat-v2-ethereum-mainnet` row, which is bound with three of the registry's
evidence digests by `REGISTRY_PROJECTION_SHA256` rather than by the whole
file's digest, and against the
repository copies of the study, runbook and design record, the
profile-invariance evidence, the fixture, release and owner-handoff records,
the five sealed anchor baselines, the zero-loss exclusion evidence, the eleven
equivalence records, the selector and layout rejection records, the Step 5
reproduction record, and the custody rules for `docs/kickoff/1355/`. The two private-repository anchors are
checked from their public maps, counts and digests.

`conformance --criterion <id> --candidate <id> --report <path>` writes one
closed `protasis-design-report/v1` for one of the design record's conformance
criteria.
`owner-handoffs` also re-verifies the retained fixture and release under
`.hexaemeron/restricted/` with Lazarus's and Alexandria's own verifiers,
loaded in-process. From those bytes it recomputes every fixture row, component
digest, plan limit, recorded response and release identity, and it checks that
the preserved registry is the capture-time revision `REGISTRY_SHA256` and
projects to `REGISTRY_PROJECTION_SHA256`. The capture's
request, byte and time counts, its UTC time and its attempt list are the
capture script's own report, and no retained byte recomputes them.
`selector-rejection` and `layout-rejection` write `true` only when the checked
record names an attempt that passed Gates 1 to 4 and exited 50 at Gate 5 with
a reason naming its intended contract; otherwise they refuse and list every
attempt's gate and exit. `sealed-coverage` writes `true` only when every type
and address is covered by a sealed anchor, natively or through a byte-equal
equivalence record, and each retained private Hermes run under
`.hexaemeron/restricted/hermes/` re-verifies against its public record.
`evidence-custody` writes `true` only when every reproduction verdict
recomputes as `reproduced` from its recorded fields, each retained private
reproduction's state is not the sealed run's and projects to the sealed
record's, every retained payload a committed record names by digest is
present and matches, every `.hexaemeron/restricted` path named under the docs
tree resolves to one of them, and no docs file carries retained private bytes,
a private test name or path, or a sealed target source file. It compares whole
files, whole JSON strings and whole test identifiers, not other encodings.
`validate_baseline`, `validate_restricted_baseline`, `verify_restricted_payload`,
`validate_exclusion_evidence`, `validate_equivalence`, `validate_rejection`,
`method_check_problems`, `validate_reproduction`, `verify_reproduction_payload`
and `evidence_custody_evidence` state which fields they recompute and which are
recorded only.

Every read is bounded, refuses symlinks and parses JSON into closed schemas.
The checker starts no subprocess and reaches no network; it compiles Hermes's
own `hermes.py` in-process, from bytes checked against the pinned digest, for
`canonical_storage_layout`. Every refusal names
the record and the field, and the digest where one is involved; a missing
file or an unbacked reference has none.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS = "docs/kickoff/1355"
INVENTORY = f"{DOCS}/inventory.json"
PROFILE_EVIDENCE = f"{DOCS}/evidence/profile-invariance.json"
DESIGN_EVIDENCE = f"{DOCS}/design-evidence.json"
REPORT_DIRECTORY = ".hexaemeron/design-reports"
HERMES = "plugins/hermes/skills/hermes/scripts/hermes.py"

MAX_JSON = 4 * 1024 * 1024
MAX_FILE = 8 * 1024 * 1024
MAX_TREE_FILES = 2000
MAX_DEPTH = 8

INVENTORY_SCHEMA = "kickoff-hermes-1355-inventory/v1"
PROFILE_SCHEMA = "kickoff-hermes-1355-profile-invariance/v1"
REPORT_SCHEMA = "protasis-design-report/v1"
DESIGN_SCHEMA = "protasis-design-evidence/v1"
SELECTED = "anchor-and-inspect"

# Receipted bytes this step copies and pins (study section 3, runbook design-lock).
STUDY_SHA256 = "1ba10293ea33adba9faec45ee58aeae43c80a3d09c9ba4d98ca8eddbf05703d0"
# Re-pinned at Step 3 to the runbook as amended on 2026-09-23.
RUNBOOK_SHA256 = "9c3cd58abd263586e88157bc4ecb56bce01e9890433ca3d87166502aa132d86f"
DESIGN_SHA256 = "3d3f5097938b422f1d77d9c6ffb46448038a51bd2704674a3375145d5a80d650"
REGISTRY_PATH = "docs/kickoff/1359/targets.json"
# The capture-time revision of the registry: the whole file's SHA-256 and byte
# count when the inventory, fixture and release were made. The fixture, release
# and handoff records name it, and the retained Alexandria release preserves
# those exact bytes. The file is shared with every other venue row and changes
# for their reasons, so the current file is not compared with this digest.
REGISTRY_SHA256 = "417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea"
REGISTRY_BYTES = 340997
REGISTRY_ROW = "wildcat-v2-ethereum-mainnet"
# The current registry is bound by the SHA-256 of `registry_projection`: the
# exactly-one `wildcat-v2-ethereum-mainnet` row and the `evidence_digests`
# entries for the three evidence files this checker reads (`REGISTRY_EVIDENCE`),
# in `canonical_bytes`. It was taken from the 417f727d revision; any change to
# that row or to one of those entries is refused, and an edit elsewhere in the
# file is accepted.
REGISTRY_PROJECTION_SHA256 = "de0287b92d21bcf5000a4efaf33803ad37a45ac6a926d8b9388ecb7170f2faaa"
CHAIN_ID = 1
BLOCK_NUMBER = 26006289
BLOCK_HASH = "0x3d069f254a10d98ad19eff0f397cf28db3613fd98bff1df48c798920552f4ec5"
ADDRESS_COUNT = 137
TYPE_COUNT = 17
EXCLUSION_COUNT = 8
HERMES_SHA256 = "36e80da4405645486e4f34caf6fa59ed795d864c685e04a9b37a959bc43c1805"
FORGE = {"version": "1.7.1", "commit": "4072e48705af9d93e3c0f6e29e93b5e9a40caed8"}

# Registry role, template or lens source -> inventory type. The inventory must
# agree with this derivation for every registry contract.
ROLE_TYPES = {
    "registry": "arch-controller",
    "sanctions-sentinel": "sanctions-sentinel",
    "factory": "hooks-factory",
    "market-init-code-storage": "wildcat-market",
    "market": "wildcat-market",
    "wrapper-factory": "wrapper-factory",
    "fee-recipient": "fee-recipient",
    "collateral-factory": "collateral-factory",
    "collateral-init-code-storage": "collateral-multi-party",
    "collateral-lens": "collateral-lens",
    "role-provider": "open-access-role-provider",
}
TEMPLATE_TYPES = {
    "0x4c62b4844c8371f321541e8d564a4b3896cecec7": "open-term-hooks",
    "0x7e49caba6fb53cdc70cd98829731a2b8d76dfc36": "fixed-term-hooks-365",
    "0x731c775385d0efb2cac61074ba2d885d343a09cd": "fixed-term-hooks-730",
}
LENS_TYPES = {
    "a70f297fbd1b1ab597e0e9a3458a2d13a34b4657": "market-lens-core",
    "e1f77540fef65736374de6c847743d8ca2233fb4": "market-lens-app",
}

V2 = "https://github.com/wildcat-finance/v2-protocol"
V1 = "https://github.com/wildcat-finance/wildcat-protocol"
PIN_V1 = {"FOUNDRY_SOLC": "0.8.22"}
PIN_825 = {"FOUNDRY_EVM_VERSION": "cancun", "FOUNDRY_SOLC": "0.8.25"}
# Study section 3: tree -> (repository, commit, access, Gate 1 pins, anchor, zero-loss exclusions).
STUDY_TREES = {
    "v2-a70f": (V2, "a70f297fbd1b1ab597e0e9a3458a2d13a34b4657", "public", {}, False, []),
    "v2-5838": (V2, "5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa", "public", {}, False, []),
    "v2-e1f7": (V2, "e1f77540fef65736374de6c847743d8ca2233fb4", "public", {}, False, []),
    "v2-c7be": (V2, "c7be4039f8f383a9dda4e45f63331c17d63f9ed9", "public", {}, True,
                ["test/vault/Wildcat4626WrapperStandard.t.sol"]),
    "v1-da74": (V1, "da74452aa7d1a0f024d99efd22cc6d950a8116b7", "public", PIN_V1, False, []),
    "v1-6164": (V1, "6164ddd4c75ef6da2181e5623b99795b9829e31c", "public", PIN_V1, False, []),
    "v1-488b": (V1, "488b30d08c73a93be3e4bf99128c774997411d3a", "public", PIN_V1, True,
                ["test/market/WildcatMarketToken.t.sol"]),
    "fee-ac73": ("https://github.com/wildcat-finance/fee-recipient-contract",
                 "ac73bda3642c9a7c8de64e39856b31af53f06068", "restricted", PIN_825, True, []),
    "rp-5d7f": ("https://github.com/wildcat-finance/chainalysis-ofac-role-provider",
                "5d7f8c889a8d29935838a3906172feb8d9861807", "restricted", PIN_825, True, []),
    "col-46db": ("https://github.com/wildcat-finance/collateral-contract",
                 "46dba596fa111f868200358f551796e8f73b5fd7", "public",
                 {"FOUNDRY_EVM_VERSION": "cancun", "FOUNDRY_SOLC": "0.8.28"}, True, []),
}
# An unenumerated type is created by an enumerated one from the same compilation.
CREATED_BY = {"wrapper": "wrapper-factory", "sanctions-escrow": "sanctions-sentinel"}
SOURCIFY_PATH = "docs/kickoff/1359/evidence/sourcify-summary.json"
# The registry evidence that records the role provider's Sourcify source digest.
SOURCE_MATCH_PATH = "docs/kickoff/1359/evidence/source-match-1590.json"

# criterion -> the transition it blocks; Step 1 lands profile-invariance, Step 2 owner-handoffs,
# Step 3 the two Gate 5 rejections, Step 4 sealed-coverage, Step 5 evidence-custody.
CONFORMANCE = {
    "profile-invariance": "step:2",
    "owner-handoffs": "step:3",
    "selector-rejection": "step:4",
    "layout-rejection": "step:4",
    "sealed-coverage": "step:5",
    "evidence-custody": "integration",
}

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")
KECCAK = re.compile(r"^0x[0-9a-f]{64}$")
SLUG = re.compile(r"^[a-z0-9][a-z0-9.-]{0,63}$")
IDENTIFIER = re.compile(r"^src/[A-Za-z0-9_./-]+\.sol:[A-Za-z_][A-Za-z0-9_]*$")
SELECTOR = re.compile(r"^[0-9a-f]{8}$")
FOUNDRY_ENV = re.compile(r"^FOUNDRY_[A-Z_]+$")
ALLOWED_SUFFIXES = {".md", ".json"}
FORBIDDEN_PARTS = {"baseline-sources", "restricted", "lib", "src", "test", "script"}


class Refusal(Exception):
    """One or more named findings."""

    def __init__(self, findings: list[str]):
        super().__init__("; ".join(findings))
        self.findings = findings


def finding(record: str, field: str, detail: str, digest: str | None = None) -> str:
    text = f"record={record} field={field} {detail}"
    if digest is not None:
        text += f" digest={digest}"
    return text


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def canonical_bytes(value: Any) -> bytes:
    """Sorted keys, no whitespace, UTF-8: the form `REGISTRY_PROJECTION_SHA256` is taken over."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def canonical_text(value: Any) -> str:
    """Hermes's comparison form for layout and method-map files."""
    return json.dumps(value, indent=2, sort_keys=True, separators=(",", ": ")) + "\n"


# --- bounded, no-follow reads -------------------------------------------------

def safe_relative(relative: str, record: str) -> PurePosixPath:
    if not isinstance(relative, str) or not relative or "\x00" in relative or "\\" in relative:
        raise Refusal([finding(record, "path", f"unsafe path {relative!r}")])
    path = PurePosixPath(relative)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise Refusal([finding(record, "path", f"path escapes the repository: {relative!r}")])
    return path


def read_bytes(root: Path, relative: str, record: str, limit: int = MAX_FILE) -> bytes:
    path = safe_relative(relative, record)
    current = root
    for part in path.parts[:-1]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            raise Refusal([finding(record, "path", f"missing directory {current.relative_to(root)}")]) from None
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise Refusal([finding(record, "path", f"{current.relative_to(root)} is a symlink or not a directory")])
    target = current / path.parts[-1]
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(target, flags)
    except FileNotFoundError:
        raise Refusal([finding(record, "path", f"missing file {relative}")]) from None
    except OSError as exc:
        raise Refusal([finding(record, "path", f"{relative} cannot be opened without following a link: {exc.strerror}")]) from None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise Refusal([finding(record, "path", f"{relative} is not a regular file")])
        if info.st_size > limit:
            raise Refusal([finding(record, "size", f"{relative} is {info.st_size} bytes, over the {limit}-byte bound")])
        chunks = []
        remaining = limit + 1
        while remaining > 0:
            chunk = os.read(fd, min(remaining, 1 << 20))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
    finally:
        os.close(fd)
    if len(raw) > limit:
        raise Refusal([finding(record, "size", f"{relative} grew over the {limit}-byte bound")])
    return raw


def strict_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key {key!r}")
        result[key] = value
    return result


def reject_constant(value: str) -> Any:
    raise ValueError(f"non-finite number {value}")


def parse_json(raw: bytes, record: str) -> Any:
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=strict_pairs, parse_constant=reject_constant)
    except (UnicodeDecodeError, ValueError, RecursionError) as exc:
        raise Refusal([finding(record, "json", f"invalid JSON: {exc}", sha256(raw))]) from None


def read_json(root: Path, relative: str, record: str, limit: int = MAX_JSON) -> tuple[Any, bytes]:
    raw = read_bytes(root, relative, record, limit)
    return parse_json(raw, record), raw


# --- closed-schema helpers ----------------------------------------------------

def exact_keys(value: Any, keys: set[str], record: str, optional: set[str] = frozenset()) -> list[str]:
    if not isinstance(value, dict):
        return [finding(record, "$", f"expected an object, found {type(value).__name__}")]
    problems = []
    missing = sorted(keys - set(value))
    extra = sorted(set(value) - keys - set(optional))
    if missing:
        problems.append(finding(record, ",".join(missing), "missing"))
    if extra:
        problems.append(finding(record, ",".join(extra), "not in the closed schema"))
    return problems


def is_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def text(value: Any, limit: int = 2000) -> bool:
    return isinstance(value, str) and 0 < len(value) <= limit and "\x00" not in value


# --- registry -----------------------------------------------------------------

def registry_projection(value: Any) -> tuple[dict[str, Any] | None, str | None]:
    """The part of the registry this estate consumes, and the SHA-256 of its `canonical_bytes`.

    The projection is the one `REGISTRY_ROW` row and the `evidence_digests`
    entries of `REGISTRY_EVIDENCE`, an absent entry kept as null. A document
    with no target list or not exactly one such row has no projection.
    """
    rows = value.get("targets") if isinstance(value, dict) else None
    if not isinstance(rows, list):
        return None, None
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == REGISTRY_ROW]
    if len(matches) != 1:
        return None, None
    digests = value.get("evidence_digests") if isinstance(value.get("evidence_digests"), dict) else {}
    projection = {"row": matches[0], "evidence_digests": {path: digests.get(path) for path in REGISTRY_EVIDENCE}}
    return projection, sha256(canonical_bytes(projection))


def load_registry(root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
    """The current registry's `REGISTRY_ROW` row, accepted only through its pinned projection.

    `inventory.registry.sha256` must name the capture-time revision
    `REGISTRY_SHA256`; the current file itself is bound by
    `REGISTRY_PROJECTION_SHA256`, not by its whole-file digest.
    """
    registry = inventory.get("registry")
    problems = exact_keys(registry, {"path", "sha256", "row", "chain_id", "block_number", "block_hash", "contract_count"},
                          "inventory.registry")
    if problems:
        raise Refusal(problems)
    expected = {"path": REGISTRY_PATH, "sha256": REGISTRY_SHA256, "row": REGISTRY_ROW, "chain_id": CHAIN_ID,
                "block_number": BLOCK_NUMBER, "block_hash": BLOCK_HASH, "contract_count": ADDRESS_COUNT}
    for key, value in expected.items():
        if registry[key] != value:
            problems.append(finding("inventory.registry", key, f"is {registry[key]!r}, expected {value!r}"))
    if problems:
        raise Refusal(problems)
    value, _ = read_json(root, REGISTRY_PATH, "registry")
    projection, digest = registry_projection(value)
    if digest != REGISTRY_PROJECTION_SHA256:
        raise Refusal([finding("registry", "projection", f"{REGISTRY_PATH} row {REGISTRY_ROW} or its evidence digests "
                               f"do not match the pinned projection {REGISTRY_PROJECTION_SHA256}", digest)])
    row = dict(projection["row"])
    row["_evidence_digests"] = dict(projection["evidence_digests"])
    observed = row.get("deployment", {}).get("observed_block", {})
    if (row.get("deployment", {}).get("chain_id"), observed.get("number"), observed.get("hash")) != (CHAIN_ID, BLOCK_NUMBER, BLOCK_HASH):
        raise Refusal([finding("registry", "deployment.observed_block", "chain, block or hash differs from the study", digest)])
    return row


def derived_type(contract: dict[str, Any]) -> str | None:
    role = contract.get("role")
    if role == "hooks-template":
        return TEMPLATE_TYPES.get(contract.get("address"))
    if role == "hooks-instance":
        return TEMPLATE_TYPES.get(contract.get("template"))
    if role == "lens":
        return LENS_TYPES.get((contract.get("code_match") or {}).get("source_commit"))
    return ROLE_TYPES.get(role)


def private_digests(row: dict[str, Any]) -> set[str]:
    """SHA-256s of every private-repository build input the registry records."""
    digests = set()
    for component in row.get("source", {}).get("components", []):
        if "private" in str(component.get("visibility", "")):
            for item in component.get("build_inputs", []):
                if isinstance(item, dict) and isinstance(item.get("sha256"), str) and HEX64.match(item["sha256"]):
                    digests.add(item["sha256"])
    return digests


# --- inventory ----------------------------------------------------------------

TREE_KEYS = {"repository", "commit", "access", "gate1_environment", "anchor", "zero_loss_exclusions"}
PROFILE_KEYS = {"solc", "evm_version", "optimizer", "optimizer_runs", "via_ir"}
TYPE_KEYS = {"id", "identifier", "deployed_state", "anchor", "anchor_identifier", "coverage",
             "deployed_profile", "enumerated"}
TYPE_OPTIONAL = {"not_enumerated_reason", "registry_source_override"}
ADDRESS_KEYS = {"address", "role", "name", "type", "code_keccak256"}
EXCLUSION_KEYS = {"item", "owner", "reason"}


def validate_trees(trees: Any) -> list[str]:
    if not isinstance(trees, dict) or not trees:
        return [finding("inventory.trees", "$", "expected a non-empty object")]
    problems = []
    if set(trees) != set(STUDY_TREES):
        problems.append(finding("inventory.trees", "$", f"must name exactly the study's trees {sorted(STUDY_TREES)}"))
    for tree_id, tree in trees.items():
        record = f"inventory.trees.{tree_id}"
        if not SLUG.match(tree_id):
            problems.append(finding(record, "id", "is not a slug"))
        found = exact_keys(tree, TREE_KEYS, record)
        if found:
            problems += found
            continue
        if not (text(tree["repository"]) and tree["repository"].startswith("https://github.com/wildcat-finance/")):
            problems.append(finding(record, "repository", "is not a wildcat-finance GitHub URL"))
        if not (isinstance(tree["commit"], str) and HEX40.match(tree["commit"])):
            problems.append(finding(record, "commit", "is not a full commit id"))
        if tree["access"] not in ("public", "restricted"):
            problems.append(finding(record, "access", "must be public or restricted"))
        env = tree["gate1_environment"]
        if not isinstance(env, dict) or any(not FOUNDRY_ENV.match(k) or not text(v, 64) for k, v in env.items()):
            problems.append(finding(record, "gate1_environment", "must map FOUNDRY_ names to short strings"))
        if not isinstance(tree["anchor"], bool):
            problems.append(finding(record, "anchor", "must be a boolean"))
        exclusions = tree["zero_loss_exclusions"]
        if not isinstance(exclusions, list) or any(not (text(e, 200) and e.startswith("test/") and e.endswith(".sol")) for e in exclusions):
            problems.append(finding(record, "zero_loss_exclusions", "must list test/*.sol paths"))
        elif exclusions and tree["anchor"] is not True:
            problems.append(finding(record, "zero_loss_exclusions", "only an anchor may exclude a test file"))
        study = STUDY_TREES.get(tree_id)
        if study is not None:
            actual = (tree["repository"], tree["commit"], tree["access"], tree["gate1_environment"], tree["anchor"],
                      tree["zero_loss_exclusions"])
            for field, want, have in zip(("repository", "commit", "access", "gate1_environment", "anchor",
                                          "zero_loss_exclusions"), study, actual):
                if want != have:
                    problems.append(finding(record, field, f"is {have!r}, study section 3 records {want!r}"))
    return problems


def validate_profiles(profiles: Any) -> list[str]:
    if not isinstance(profiles, dict) or not profiles:
        return [finding("inventory.profiles", "$", "expected a non-empty object")]
    problems = []
    for profile_id, profile in profiles.items():
        record = f"inventory.profiles.{profile_id}"
        found = exact_keys(profile, PROFILE_KEYS | {"source"}, record)
        if found:
            problems += found
            continue
        if profile_id == "default" or not SLUG.match(profile_id):
            problems.append(finding(record, "id", "must be a slug other than default"))
        if not (text(profile["solc"], 16) and re.match(r"^0\.8\.[0-9]+$", profile["solc"])):
            problems.append(finding(record, "solc", "must be a 0.8.x version"))
        if profile["evm_version"] not in ("shanghai", "cancun", "paris", "london"):
            problems.append(finding(record, "evm_version", "is not a known EVM version"))
        if profile["optimizer"] is not True or not is_int(profile["optimizer_runs"]) or profile["optimizer_runs"] <= 0:
            problems.append(finding(record, "optimizer", "a deployed profile names an enabled optimizer and positive runs"))
        if not isinstance(profile["via_ir"], bool):
            problems.append(finding(record, "via_ir", "must be a boolean"))
        if not text(profile["source"]):
            problems.append(finding(record, "source", "must cite where the deployed settings were recorded"))
    return problems


def validate_types(types: Any, trees: dict[str, Any], profiles: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    if not isinstance(types, list):
        return [finding("inventory.types", "$", "expected a list")], {}
    problems = []
    by_id: dict[str, Any] = {}
    for index, item in enumerate(types):
        record = f"inventory.types[{index}]"
        found = exact_keys(item, TYPE_KEYS, record, TYPE_OPTIONAL)
        if found:
            problems += found
            continue
        type_id = item["id"]
        if any(not isinstance(item[f], str) for f in ("id", "identifier", "deployed_state", "anchor",
                                                     "anchor_identifier", "coverage", "deployed_profile")):
            problems.append(finding(record, "$", "id, identifiers, trees, coverage and profile must be strings"))
            continue
        record = f"inventory.types.{type_id}"
        if not SLUG.match(type_id):
            problems.append(finding(record, "id", "is not a slug"))
            continue
        if type_id in by_id:
            problems.append(finding(record, "id", "is duplicated"))
            continue
        by_id[type_id] = item
        for field in ("identifier", "anchor_identifier"):
            if not (isinstance(item[field], str) and IDENTIFIER.match(item[field])):
                problems.append(finding(record, field, "is not a src/<path>.sol:<Contract> identifier"))
        deployed = trees.get(item["deployed_state"])
        anchor = trees.get(item["anchor"])
        if deployed is None:
            problems.append(finding(record, "deployed_state", f"names no inventory tree: {item['deployed_state']!r}"))
        if anchor is None:
            problems.append(finding(record, "anchor", f"names no inventory tree: {item['anchor']!r}"))
        elif anchor.get("anchor") is not True:
            problems.append(finding(record, "anchor", f"{item['anchor']} is not an anchor tree"))
        if item["deployed_profile"] not in profiles:
            problems.append(finding(record, "deployed_profile", f"names no inventory profile: {item['deployed_profile']!r}"))
        native = item["deployed_state"] == item["anchor"] and item["identifier"] == item["anchor_identifier"]
        expected = "native" if native else "equivalent"
        if item["coverage"] not in ("native", "equivalent"):
            problems.append(finding(record, "coverage", f"must be native or equivalent, found {item['coverage']!r}"))
        elif item["coverage"] != expected:
            problems.append(finding(record, "coverage", f"is {item['coverage']}, but the deployed state and anchor make it {expected}"))
        if not isinstance(item["enumerated"], bool):
            problems.append(finding(record, "enumerated", "must be a boolean"))
        elif item["enumerated"] is False and not text(item.get("not_enumerated_reason")):
            problems.append(finding(record, "not_enumerated_reason", "an unenumerated type must say why"))
        elif item["enumerated"] is True and "not_enumerated_reason" in item:
            problems.append(finding(record, "not_enumerated_reason", "only an unenumerated type carries a reason"))
        override = item.get("registry_source_override")
        if override is not None:
            found = exact_keys(override, {"commit", "reason", "sourcify_source_sha256"},
                               f"{record}.registry_source_override")
            if found:
                problems += found
            elif not (isinstance(override["commit"], str) and HEX40.match(override["commit"]) and text(override["reason"])
                      and isinstance(override["sourcify_source_sha256"], str)
                      and HEX64.match(override["sourcify_source_sha256"])):
                problems.append(finding(record, "registry_source_override",
                                        "needs a full commit, a reason and the Sourcify source SHA-256"))
    if len(by_id) != TYPE_COUNT:
        problems.append(finding("inventory.types", "$", f"has {len(by_id)} types, the study names {TYPE_COUNT}"))
    return problems, by_id


def validate_addresses(addresses: Any, row: dict[str, Any], types: dict[str, Any],
                       trees: dict[str, Any]) -> list[str]:
    if not isinstance(addresses, list):
        return [finding("inventory.addresses", "$", "expected a list")]
    registry = {}
    for contract in row.get("deployment", {}).get("contracts", []):
        registry[str(contract.get("address", "")).lower()] = contract
    problems = []
    seen: dict[str, int] = {}
    counts: dict[str, int] = {}
    for index, entry in enumerate(addresses):
        record = f"inventory.addresses[{index}]"
        found = exact_keys(entry, ADDRESS_KEYS, record)
        if found:
            problems += found
            continue
        address = entry["address"]
        if any(not isinstance(entry[f], str) for f in ADDRESS_KEYS):
            problems.append(finding(record, "$", "every address field must be a string"))
            continue
        record = f"inventory.addresses.{address}"
        if not ADDRESS.match(address):
            problems.append(finding(record, "address", "is not a lowercase 20-byte hex address"))
            continue
        if address in seen:
            problems.append(finding(record, "address", f"is duplicated (entries {seen[address]} and {index})"))
            continue
        seen[address] = index
        contract = registry.get(address)
        if contract is None:
            problems.append(finding(record, "address", f"is not a {REGISTRY_ROW} registry contract", REGISTRY_SHA256))
            continue
        for field, source in (("role", "role"), ("name", "name"), ("code_keccak256", "code_keccak256")):
            if entry[field] != contract.get(source):
                problems.append(finding(record, field, f"is {entry[field]!r}, the registry records {contract.get(source)!r}", REGISTRY_SHA256))
        expected = derived_type(contract)
        if entry["type"] not in types:
            problems.append(finding(record, "type", f"names no inventory type: {entry['type']!r}"))
            continue
        if expected is None:
            problems.append(finding(record, "type", f"registry role {contract.get('role')!r} has no protected type", REGISTRY_SHA256))
            continue
        if entry["type"] != expected:
            problems.append(finding(record, "type", f"is {entry['type']}, the registry role and source make it {expected}", REGISTRY_SHA256))
            continue
        item = types[expected]
        registry_commit = (contract.get("code_match") or {}).get("source_commit")
        deployed_commit = trees.get(item["deployed_state"], {}).get("commit")
        override = (item.get("registry_source_override") or {}).get("commit")
        if registry_commit not in (deployed_commit, override):
            problems.append(finding(record, "type", f"registry source commit {registry_commit} is neither {expected}'s deployed state nor its recorded override", REGISTRY_SHA256))
        counts[expected] = counts.get(expected, 0) + 1
    missing = sorted(set(registry) - set(seen))
    for address in missing:
        problems.append(finding(f"inventory.addresses.{address}", "address", "registry contract is missing from the inventory", REGISTRY_SHA256))
    if len(seen) != ADDRESS_COUNT:
        problems.append(finding("inventory.addresses", "$", f"maps {len(seen)} addresses, the registry records {ADDRESS_COUNT}"))
    for type_id, item in types.items():
        if item.get("enumerated") is True and counts.get(type_id, 0) == 0:
            problems.append(finding(f"inventory.types.{type_id}", "enumerated", "no registry address maps to an enumerated type"))
        if item.get("enumerated") is False and counts.get(type_id, 0):
            problems.append(finding(f"inventory.types.{type_id}", "enumerated", "an unenumerated type has registry addresses"))
    return problems


def registry_profile(compiler: Any) -> dict[str, Any] | None:
    if not isinstance(compiler, dict):
        return None
    return {"solc": str(compiler.get("solc", "")).split("+")[0], "evm_version": compiler.get("evm_version"),
            "optimizer": True, "optimizer_runs": compiler.get("optimizer_runs"), "via_ir": compiler.get("via_ir")}


def validate_profile_sources(root: Path, registry_raw_row: dict[str, Any], types: dict[str, Any],
                             trees: dict[str, Any], profiles: dict[str, Any], addresses: list[Any]) -> list[str]:
    """Each type's deployed profile must agree with every machine-readable record of its deployed settings."""
    problems = []
    digests = registry_raw_row.get("_evidence_digests", {})
    sourcify: dict[str, Any] = {}
    value, raw = read_json(root, SOURCIFY_PATH, "sourcify-summary")
    if sha256(raw) != digests.get(SOURCIFY_PATH):
        return [finding("sourcify-summary", "sha256", "does not match the registry's evidence digest", sha256(raw))]
    for key, entry in (value.get("records") or {}).items():
        if isinstance(entry, dict) and entry.get("match"):
            sourcify[key.split(":")[-1].lower()] = {
                "solc": str(entry.get("compiler_version", "")).split("+")[0], "evm_version": entry.get("evm_version"),
                "optimizer": True, "optimizer_runs": entry.get("optimizer_runs"), "via_ir": entry.get("via_ir")}
    source = registry_raw_row.get("source", {})
    row_commits = {source.get("commit"), (source.get("third_template_source") or {}).get("commit")}
    components = {c.get("commit"): c.get("compiler") for c in source.get("components", []) if isinstance(c, dict)}
    by_type: dict[str, list[str]] = {}
    for entry in addresses:
        if isinstance(entry, dict) and isinstance(entry.get("type"), str):
            by_type.setdefault(entry["type"], []).append(entry.get("address"))
    for type_id, item in types.items():
        record = f"inventory.types.{type_id}"
        profile = profiles.get(item["deployed_profile"])
        if profile is None:
            continue
        declared = {k: profile[k] for k in PROFILE_KEYS}
        if type_id in CREATED_BY:
            creator = types.get(CREATED_BY[type_id], {})
            if (creator.get("deployed_profile"), creator.get("deployed_state")) != (item["deployed_profile"], item["deployed_state"]):
                problems.append(finding(record, "deployed_profile", f"must equal its creator {CREATED_BY[type_id]}'s profile and deployed state"))
            continue
        witnesses = []
        for address in by_type.get(type_id, []):
            if address in sourcify:
                witnesses.append(("sourcify " + address, sourcify[address]))
        commit = trees.get(item["deployed_state"], {}).get("commit")
        override = (item.get("registry_source_override") or {}).get("commit")
        if commit in row_commits:
            witnesses.append(("registry source.compiler", registry_profile(source.get("compiler"))))
        for candidate in (commit, override):
            if candidate in components:
                witnesses.append((f"registry component {candidate[:8]}", registry_profile(components[candidate])))
        if not witnesses:
            problems.append(finding(record, "deployed_profile", "no registry or Sourcify record confirms the deployed settings", REGISTRY_SHA256))
        for name, witness in witnesses:
            if witness != declared:
                problems.append(finding(record, "deployed_profile", f"{item['deployed_profile']} disagrees with {name}: {witness}", REGISTRY_SHA256))
    return problems


def validate_overrides(root: Path, row: dict[str, Any], types: dict[str, Any], addresses: list[Any]) -> list[str]:
    """Bind each registry source override to the registry's own source-match evidence.

    An override replaces the registry's source commit with a public deployed
    state. The replacement stands only when the registry evidence records a
    Sourcify match at an inventory address of that type, the registry-named
    blob differs from the Sourcify source, and the override states the Sourcify
    source digest exactly.
    """
    overrides = {type_id: item["registry_source_override"] for type_id, item in types.items()
                 if isinstance(item.get("registry_source_override"), dict)}
    if not overrides:
        return []
    digests = row.get("_evidence_digests", {})
    try:
        value, raw = read_json(root, SOURCE_MATCH_PATH, "source-match")
    except Refusal as refusal:
        return refusal.findings
    digest = sha256(raw)
    if digest != digests.get(SOURCE_MATCH_PATH):
        return [finding("source-match", "sha256", f"{SOURCE_MATCH_PATH} does not match the registry's evidence digest", digest)]
    entries = [entry for entry in value.values() if isinstance(entry, dict)] if isinstance(value, dict) else []
    by_type: dict[str, set[str]] = {}
    for entry in addresses:
        if isinstance(entry, dict) and isinstance(entry.get("type"), str):
            by_type.setdefault(entry["type"], set()).add(entry.get("address"))
    problems = []
    for type_id, override in sorted(overrides.items()):
        record = f"inventory.types.{type_id}.registry_source_override"
        claimed = override.get("sourcify_source_sha256")
        matches = [entry for entry in entries
                   if entry.get("commit") == override.get("commit")
                   and str(entry.get("address", "")).lower() in by_type.get(type_id, set())
                   and isinstance(entry.get("sourcify"), dict) and entry["sourcify"].get("match") == "match"]
        if len(matches) != 1:
            problems.append(finding(record, "commit", f"{SOURCE_MATCH_PATH} records {len(matches)} Sourcify matches "
                                    f"for this type at the overridden commit, expected 1", digest))
            continue
        recorded = matches[0]["sourcify"].get("source_sha256")
        if claimed != recorded:
            problems.append(finding(record, "sourcify_source_sha256",
                                    f"is {claimed!r}, the registry's Sourcify evidence records {recorded!r}", digest))
        elif matches[0].get("blob_sha256") == recorded:
            problems.append(finding(record, "sourcify_source_sha256",
                                    "the registry-named blob already equals the Sourcify source; no override is needed", digest))
    return problems


def validate_exclusions(exclusions: Any, row: dict[str, Any]) -> list[str]:
    if not isinstance(exclusions, list):
        return [finding("inventory.exclusions", "$", "expected a list")]
    problems = []
    for index, item in enumerate(exclusions):
        record = f"inventory.exclusions[{index}]"
        found = exact_keys(item, EXCLUSION_KEYS, record)
        if found:
            problems += found
            continue
        for field in EXCLUSION_KEYS:
            if not text(item[field]):
                problems.append(finding(record, field, "must name the item, its owner and the reason"))
    if len(exclusions) != EXCLUSION_COUNT:
        problems.append(finding("inventory.exclusions", "$", f"keeps {len(exclusions)} exclusions, the study keeps {EXCLUSION_COUNT}"))
    if exclusions != row.get("protected_set_exclusions"):
        problems.append(finding("inventory.exclusions", "$", "differs from the registry's protected_set_exclusions", REGISTRY_SHA256))
    return problems


def validate_documents(root: Path, documents: Any) -> list[str]:
    expected = {
        "study": (f"{DOCS}/study.md", STUDY_SHA256),
        "runbook": (f"{DOCS}/runbook.md", RUNBOOK_SHA256),
        "design_evidence": (DESIGN_EVIDENCE, DESIGN_SHA256),
    }
    problems = exact_keys(documents, set(expected), "inventory.documents")
    if problems:
        return problems
    for key, (path, digest) in expected.items():
        record = f"inventory.documents.{key}"
        entry = documents[key]
        found = exact_keys(entry, {"path", "sha256"}, record)
        if found:
            problems += found
            continue
        if entry["path"] != path or entry["sha256"] != digest:
            problems.append(finding(record, "sha256", f"must pin {path} at the receipted bytes", entry.get("sha256")))
            continue
        try:
            actual = sha256(read_bytes(root, path, record))
        except Refusal as refusal:
            problems += refusal.findings
            continue
        if actual != digest:
            problems.append(finding(record, "sha256", f"{path} does not match the receipted {digest}", actual))
    if problems:
        return problems
    runbook = read_bytes(root, f"{DOCS}/runbook.md", "inventory.documents.runbook").decode("utf-8")
    lock = re.search(r"```design-lock\n(.*?)```", runbook, re.S)
    if not lock or f"sha256 | {DESIGN_SHA256}" not in lock.group(1) or f"candidate | {SELECTED}" not in lock.group(1):
        problems.append(finding("inventory.documents.runbook", "design-lock", "does not bind the design record and selected candidate", RUNBOOK_SHA256))
    return problems


def load_design(root: Path) -> dict[str, Any]:
    value, raw = read_json(root, DESIGN_EVIDENCE, "design-evidence")
    if sha256(raw) != DESIGN_SHA256:
        raise Refusal([finding("design-evidence", "sha256", "does not match the design-lock", sha256(raw))])
    if value.get("schema") != DESIGN_SCHEMA or value.get("selection", {}).get("candidate") != SELECTED:
        raise Refusal([finding("design-evidence", "selection", f"must select {SELECTED}", DESIGN_SHA256)])
    return value


def validate_design_reports(root: Path, design: dict[str, Any]) -> list[str]:
    problems = []
    listed = set()
    for result in design.get("results", []):
        report = result.get("report")
        record = f"design-evidence.{result.get('candidate')}/{result.get('criterion')}"
        if result.get("state") == "pending":
            continue
        if not isinstance(report, dict) or not isinstance(report.get("path"), str):
            problems.append(finding(record, "report", "a resolved cell must name its report", DESIGN_SHA256))
            continue
        relative = f"{DOCS}/{report['path']}"
        listed.add(relative)
        try:
            raw = read_bytes(root, relative, record, MAX_JSON)
        except Refusal as refusal:
            problems += refusal.findings
            continue
        if sha256(raw) != report.get("sha256"):
            problems.append(finding(record, "report.sha256", f"{relative} does not match the design record's {report.get('sha256')}", sha256(raw)))
            continue
        value = parse_json(raw, record)
        if not isinstance(value, dict) or value.get("schema") != REPORT_SCHEMA or value.get("exit") != 0 \
                or value.get("candidate") != result.get("candidate") or value.get("criterion") != result.get("criterion"):
            problems.append(finding(record, "report", "is not the zero-exit report for this cell", sha256(raw)))
    directory = f"{DOCS}/design-reports"
    present = {f"{directory}/{name}" for name in list_directory(root, directory, "design-reports")}
    for extra in sorted(present - listed):
        problems.append(finding("design-reports", "path", f"{extra} is not a resolved cell of the design record", DESIGN_SHA256))
    return problems


def list_directory(root: Path, relative: str, record: str) -> list[str]:
    path = root / safe_relative(relative, record)
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        raise Refusal([finding(record, "path", f"missing directory {relative}")]) from None
    if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
        raise Refusal([finding(record, "path", f"{relative} is a symlink or not a directory")])
    names = sorted(os.listdir(path))
    if len(names) > MAX_TREE_FILES:
        raise Refusal([finding(record, "path", f"{relative} holds more than {MAX_TREE_FILES} entries")])
    return names


# --- custody --------------------------------------------------------------------

def json_strings(value: Any) -> list[str]:
    """Every key and string value in a parsed JSON document, without recursion."""
    found: list[str] = []
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, str):
            found.append(item)
        elif isinstance(item, dict):
            found.extend(item.keys())
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return found


# A pragma followed by a version constraint is source wherever it sits: a
# Markdown file can carry an escaped standard-JSON input on one line, where
# no line starts with the pragma.
PRAGMA_WITH_VERSION = re.compile(rb"pragma[ \t]+solidity[ \t]*[\^~>=<]*[ \t]*[0-9]")


def solidity_text(value: str) -> bool:
    return bool(re.search(r"^\s*pragma solidity\b", value, re.M) or "SPDX-License-Identifier" in value)


def validate_custody(root: Path, private: set[str]) -> list[str]:
    """No symlink, target source, private source or Hermes source copy under the docs tree."""
    problems: list[str] = []
    count = 0
    stack = [(PurePosixPath(DOCS), 0)]
    while stack:
        relative, depth = stack.pop()
        path = root / relative
        try:
            names = sorted(os.listdir(path))
        except OSError as exc:
            problems.append(finding("custody", "path", f"{relative} cannot be listed: {exc.strerror}"))
            continue
        for name in names:
            child = relative / name
            count += 1
            if count > MAX_TREE_FILES:
                return problems + [finding("custody", "path", f"{DOCS} holds more than {MAX_TREE_FILES} entries")]
            mode = (root / child).lstat().st_mode
            if stat.S_ISLNK(mode):
                problems.append(finding("custody", "path", f"{child} is a symlink"))
                continue
            if name.lower() in FORBIDDEN_PARTS:
                problems.append(finding("custody", "path", f"{child} is a target or Hermes source directory name"))
                continue
            if stat.S_ISDIR(mode):
                if depth + 1 >= MAX_DEPTH:
                    problems.append(finding("custody", "path", f"{child} is deeper than {MAX_DEPTH} levels"))
                else:
                    stack.append((child, depth + 1))
                continue
            if not stat.S_ISREG(mode):
                problems.append(finding("custody", "path", f"{child} is not a regular file"))
                continue
            suffix = PurePosixPath(name).suffix.lower()
            if suffix not in ALLOWED_SUFFIXES:
                problems.append(finding("custody", "path", f"{child} has suffix {suffix or '(none)'}; only {sorted(ALLOWED_SUFFIXES)} may ship here"))
                continue
            try:
                raw = read_bytes(root, str(child), "custody")
            except Refusal as refusal:
                problems += refusal.findings
                continue
            digest = sha256(raw)
            if digest in private:
                problems.append(finding("custody", "path", f"{child} is a private-repository source file", digest))
            elif re.search(rb"^\s*pragma solidity\b", raw, re.M) or PRAGMA_WITH_VERSION.search(raw) or (
                    suffix != ".md" and re.search(rb"SPDX-License-Identifier", raw)):
                problems.append(finding("custody", "path", f"{child} carries Solidity source text", digest))
            elif suffix == ".json":
                # A standard-JSON input carries each source as one escaped
                # string, so a line-anchored scan of the raw bytes misses it.
                try:
                    embedded = any(solidity_text(item) for item in json_strings(parse_json(raw, "custody")))
                except Refusal as refusal:
                    problems += [item + f" path={child}" for item in refusal.findings]
                    continue
                if embedded:
                    problems.append(finding("custody", "path", f"{child} carries Solidity source text in a JSON string", digest))
    return problems


# --- profile invariance ---------------------------------------------------------

def deployed_environment(profile: dict[str, Any]) -> dict[str, str]:
    return {
        "FOUNDRY_SOLC": profile["solc"],
        "FOUNDRY_EVM_VERSION": profile["evm_version"],
        "FOUNDRY_OPTIMIZER": "true",
        "FOUNDRY_OPTIMIZER_RUNS": str(profile["optimizer_runs"]),
        "FOUNDRY_VIA_IR": "true" if profile["via_ir"] else "false",
    }


def settings_of(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or set(value) != PROFILE_KEYS:
        return None
    if not (text(value["solc"], 16) and text(value["evm_version"], 16) and isinstance(value["optimizer"], bool)
            and is_int(value["optimizer_runs"]) and isinstance(value["via_ir"], bool)):
        return None
    return value


def validate_blobs(blobs: Any) -> tuple[list[str], dict[str, Any]]:
    if not isinstance(blobs, dict) or not blobs:
        return [finding("profile-invariance.blobs", "$", "expected a non-empty object")], {}
    problems = []
    for digest, value in blobs.items():
        record = f"profile-invariance.blobs.{digest}"
        actual = sha256(canonical_text(value).encode("utf-8"))
        if not HEX64.match(digest) or actual != digest:
            problems.append(finding(record, "sha256", "the canonical content does not hash to its key", actual))
    return problems, blobs


def check_layout(value: Any) -> bool:
    return isinstance(value, dict) and set(value) == {"storage", "types"} and isinstance(value["storage"], list) \
        and (value["types"] is None or isinstance(value["types"], dict))


def check_methods(value: Any) -> bool:
    return isinstance(value, dict) and all(isinstance(k, str) and "(" in k and isinstance(v, str) and SELECTOR.match(v)
                                           for k, v in value.items())


def validate_profile_evidence(root: Path, inventory: dict[str, Any], types: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Return findings and a summary.

    An empty finding list means every type's storage layout and method map are
    byte-equal under the Gate 1 and deployed profiles.
    """
    record_name = "profile-invariance"
    try:
        evidence, raw = read_json(root, PROFILE_EVIDENCE, record_name)
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    top = {"schema", "issue", "forge", "canonicaliser", "capture", "profiles", "builds", "records", "blobs"}
    problems = exact_keys(evidence, top, record_name)
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    if evidence["schema"] != PROFILE_SCHEMA or evidence["issue"] != 1355:
        problems.append(finding(record_name, "schema", f"must be {PROFILE_SCHEMA} for issue 1355", digest))
    if evidence["forge"] != FORGE:
        problems.append(finding(record_name, "forge", f"is {evidence['forge']!r}, the study pins {FORGE!r}", digest))
    canon = evidence["canonicaliser"]
    if canon != {"path": HERMES, "function": "canonical_storage_layout", "sha256": HERMES_SHA256}:
        problems.append(finding(record_name, "canonicaliser", "must name Hermes's canonical_storage_layout at the pinned hermes.py", digest))
    else:
        try:
            actual = sha256(read_bytes(root, HERMES, record_name))
            if actual != HERMES_SHA256:
                problems.append(finding(record_name, "canonicaliser.sha256", f"{HERMES} no longer matches {HERMES_SHA256}", actual))
        except Refusal as refusal:
            problems += refusal.findings
    capture = evidence["capture"]
    found = exact_keys(capture, {"script", "sha256", "inspect_argv", "config_argv", "isolation"}, f"{record_name}.capture")
    if found:
        problems += found
    elif not (text(capture["script"]) and isinstance(capture["sha256"], str) and HEX64.match(capture["sha256"])
              and isinstance(capture["inspect_argv"], list) and capture["inspect_argv"][:2] == ["forge", "inspect"] and capture["config_argv"] == ["forge", "config", "--json"]
              and text(capture["isolation"])):
        problems.append(finding(record_name, "capture", "must name the capture script digest, forge argv and isolation", digest))
    expected_profiles = {pid: {k: v for k, v in p.items() if k != "source"} for pid, p in inventory["profiles"].items()}
    if evidence["profiles"] != expected_profiles:
        problems.append(finding(record_name, "profiles", "differ from the inventory's deployed profiles", digest))
    blob_problems, blobs = validate_blobs(evidence["blobs"])
    problems += [p + f" record-digest={digest}" for p in blob_problems]

    trees = inventory["trees"]
    builds: dict[str, dict[str, Any]] = {}
    if not isinstance(evidence["builds"], list):
        problems.append(finding(f"{record_name}.builds", "$", "expected a list", digest))
    else:
        for index, build in enumerate(evidence["builds"]):
            record = f"{record_name}.builds[{index}]"
            found = exact_keys(build, {"id", "tree", "commit", "profile", "environment", "resolved_config"}, record)
            if found:
                problems += found
                continue
            if any(not isinstance(build[f], str) for f in ("id", "tree", "commit", "profile")):
                problems.append(finding(record, "$", "id, tree, commit and profile must be strings", digest))
                continue
            record = f"{record_name}.builds.{build['id']}"
            if build["id"] != f"{build['tree']}/{build['profile']}" or build["id"] in builds:
                problems.append(finding(record, "id", "must be <tree>/<profile> and unique", digest))
                continue
            tree = trees.get(build["tree"])
            if tree is None or build["commit"] != tree["commit"]:
                problems.append(finding(record, "commit", "does not match the inventory tree", digest))
                continue
            if build["profile"] == "default":
                expected_env = tree["gate1_environment"]
            elif build["profile"] in inventory["profiles"]:
                expected_env = deployed_environment(inventory["profiles"][build["profile"]])
            else:
                problems.append(finding(record, "profile", f"names no inventory profile: {build['profile']!r}", digest))
                continue
            if build["environment"] != expected_env:
                problems.append(finding(record, "environment", f"is {build['environment']!r}, expected {expected_env!r}", digest))
            resolved = settings_of(build["resolved_config"])
            if resolved is None:
                problems.append(finding(record, "resolved_config", "must carry solc, evm_version, optimizer, optimizer_runs and via_ir", digest))
            elif build["profile"] != "default" and resolved != expected_profiles[build["profile"]]:
                problems.append(finding(record, "resolved_config", "forge did not resolve the deployed profile", digest))
            elif build["profile"] == "default":
                pins = tree["gate1_environment"]
                if "FOUNDRY_SOLC" in pins and resolved["solc"] != pins["FOUNDRY_SOLC"] \
                        or "FOUNDRY_EVM_VERSION" in pins and resolved["evm_version"] != pins["FOUNDRY_EVM_VERSION"]:
                    problems.append(finding(record, "resolved_config", "forge did not resolve the Gate 1 compiler pins", digest))
            builds[build["id"]] = build

    expected_places: dict[tuple[str, str], tuple[str, str, str]] = {}
    for type_id, item in types.items():
        expected_places[(type_id, "deployed")] = (item["deployed_state"], item["identifier"], item["deployed_profile"])
        if (item["anchor"], item["anchor_identifier"]) != (item["deployed_state"], item["identifier"]):
            expected_places[(type_id, "anchor")] = (item["anchor"], item["anchor_identifier"], item["deployed_profile"])
    seen: set[tuple[str, str]] = set()
    invariant: dict[str, bool] = {}
    if not isinstance(evidence["records"], list):
        problems.append(finding(f"{record_name}.records", "$", "expected a list", digest))
        return problems, {}
    for index, entry in enumerate(evidence["records"]):
        record = f"{record_name}.records[{index}]"
        found = exact_keys(entry, {"type", "state", "tree", "identifier", "default", "deployed"}, record)
        if found:
            problems += found
            continue
        if any(not isinstance(entry[f], str) for f in ("type", "state", "tree", "identifier")):
            problems.append(finding(record, "$", "type, state, tree and identifier must be strings", digest))
            continue
        key = (entry["type"], entry["state"])
        record = f"{record_name}.records.{entry['type']}/{entry['state']}"
        if key not in expected_places:
            problems.append(finding(record, "type", "is not an inventory type at its deployed state or anchor", digest))
            continue
        if key in seen:
            problems.append(finding(record, "type", "is duplicated", digest))
            continue
        seen.add(key)
        tree_id, identifier, profile_id = expected_places[key]
        if (entry["tree"], entry["identifier"]) != (tree_id, identifier):
            problems.append(finding(record, "identifier", f"must be {tree_id} {identifier}", digest))
            continue
        maps = {}
        ok = True
        for side, build_profile in (("default", "default"), ("deployed", profile_id)):
            half = entry[side]
            sub = f"{record}.{side}"
            found = exact_keys(half, {"build", "compiled_settings", "storage_layout_sha256", "method_identifiers_sha256"}, sub)
            if found:
                problems += found
                ok = False
                continue
            build_id = f"{tree_id}/{build_profile}"
            if half["build"] != build_id or build_id not in builds:
                problems.append(finding(sub, "build", f"must name the recorded build {build_id}", digest))
                ok = False
                continue
            compiled = settings_of(half["compiled_settings"])
            want = settings_of(builds[build_id]["resolved_config"])
            if compiled is None or compiled != want:
                problems.append(finding(sub, "compiled_settings", "the artefact's compiler settings differ from the build's resolved profile", digest))
                ok = False
            for field, check in (("storage_layout_sha256", check_layout), ("method_identifiers_sha256", check_methods)):
                reference = half[field]
                if not isinstance(reference, str) or reference not in blobs:
                    problems.append(finding(sub, field, "names no recorded map", reference if isinstance(reference, str) else None))
                    ok = False
                elif not check(blobs[reference]):
                    problems.append(finding(sub, field, "the recorded map is not a canonical layout or method map", reference))
                    ok = False
            maps[side] = half
        if ok and len(maps) == 2:
            for field in ("storage_layout_sha256", "method_identifiers_sha256"):
                if maps["default"][field] != maps["deployed"][field]:
                    problems.append(finding(record, field, f"default profile {maps['default'][field]} differs from deployed profile {profile_id} {maps['deployed'][field]}", digest))
                    ok = False
        invariant[f"{entry['type']}/{entry['state']}"] = ok
    for key in sorted(set(expected_places) - seen):
        problems.append(finding(f"{record_name}.records.{key[0]}/{key[1]}", "type", "no profile comparison is recorded", digest))
    summary = {
        "record": PROFILE_EVIDENCE,
        "sha256": digest,
        "types": len(types),
        "comparisons": len(invariant),
        "invariant": sum(1 for value in invariant.values() if value),
    }
    return problems, summary


# --- chain evidence: fixture, release and owner handoffs --------------------------

FIXTURE_RECORD = f"{DOCS}/evidence/fixture.json"
RELEASE_RECORD = f"{DOCS}/evidence/release.json"
HANDOFFS_RECORD = f"{DOCS}/evidence/owner-handoffs.json"
FIXTURE_SCHEMA = "kickoff-hermes-1355-fixture/v1"
RELEASE_SCHEMA = "kickoff-hermes-1355-release/v1"
HANDOFFS_SCHEMA = "kickoff-hermes-1355-owner-handoffs/v1"
OBSERVATIONS_PATH = "docs/kickoff/1359/evidence/ethereum-mainnet-1590.json"
SCOPE_PATH = "docs/kickoff/1359/evidence/scope-approval.json"
# The registry `evidence_digests` entries this checker reads; `registry_projection` binds them.
REGISTRY_EVIDENCE = (SOURCIFY_PATH, SOURCE_MATCH_PATH, OBSERVATIONS_PATH)
# The complete payloads stay outside Git (runbook: ignored restricted directory).
RESTRICTED = ".hexaemeron/restricted"
FIXTURE_PAYLOAD = f"{RESTRICTED}/fixture-26006289"
PROOFS_SOURCE = f"{FIXTURE_PAYLOAD}/proofs.jsonl"
RELEASE_PAYLOAD = f"{RESTRICTED}/alexandria-release"
RELEASE_PLAN = f"{RESTRICTED}/alexandria-input/capture-plan.json"
CAPTURE_SCRIPT = f"{RESTRICTED}/tools/capture_1355.py"
MAX_PAYLOAD = 32 * 1024 * 1024
FIXTURE_COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")
LIMIT_KEYS = {"max_requests", "max_component_bytes", "max_total_bytes", "max_elapsed_seconds"}
# Open Lazarus findings that concern receipts; this fixture carries no receipt.
NOT_APPLICABLE = {"fiat-383 S1-R1-01", "fiat-383 S2-R1-03"}
RELEASE_INPUTS = {"registry": REGISTRY_PATH, "source-match": SOURCE_MATCH_PATH, "chain-observations": OBSERVATIONS_PATH}
RELEASE_COMPONENTS = {
    "registry": "deployment-registry", "source-match": "source-match", "chain-observations": "chain-observations",
    "fixture-manifest": "lazarus-manifest", "fixture-header-json": "lazarus-fixture-file",
    "fixture-plan-json": "lazarus-fixture-file", "fixture-proofs-jsonl": "lazarus-fixture-file",
    "fixture-rpc-jsonl": "lazarus-fixture-file",
}
FIXTURE_FILE_COMPONENTS = {"fixture-header-json": "header.json", "fixture-plan-json": "plan.json",
                           "fixture-proofs-jsonl": "proofs.jsonl", "fixture-rpc-jsonl": "rpc.jsonl"}
HANDOFFS = {
    "scope": SCOPE_PATH, "registry": REGISTRY_PATH, "source-matching": SOURCE_MATCH_PATH,
    "chain-observations": OBSERVATIONS_PATH, "fixture": FIXTURE_RECORD, "release": RELEASE_RECORD,
    "inventory": INVENTORY,
}
# A row whose named reviewer has not reviewed says so in its status. Only the
# inventory may be handed on that way: its target-maintainer review is carried
# to the run pull request, and every other handoff must be complete.
REVIEW_OUTSTANDING = "target-maintainer-review-outstanding"
REVIEW_OUTSTANDING_ALLOWED = {"inventory"}
RECORDED = "recorded"
PROVED = "proof-backed"
MISS_ERROR = -32070
RELEASE_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
STAMP = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$")


def field_of(value: Any, key: str) -> Any:
    return value.get(key) if isinstance(value, dict) else None


def positive_int(value: Any) -> bool:
    return is_int(value) and value > 0


def file_digest(root: Path, relative: str, record: str, limit: int = MAX_FILE) -> tuple[str, int]:
    """Recompute a file's SHA-256 and length; a stated digest is never trusted on its own."""
    raw = read_bytes(root, relative, record, limit)
    return sha256(raw), len(raw)


def registry_digest(row: dict[str, Any], relative: str) -> str | None:
    return (row.get("_evidence_digests") or {}).get(relative)


def pinned_digest(row: dict[str, Any], relative: str) -> str | None:
    """An evidence file is pinned by the registry's projected digest; the registry is not handled here."""
    return registry_digest(row, relative)


def load_observations(root: Path, row: dict[str, Any]) -> tuple[list[str], dict[str, dict[str, Any]]]:
    try:
        value, raw = read_json(root, OBSERVATIONS_PATH, "chain-observations")
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    if digest != registry_digest(row, OBSERVATIONS_PATH):
        return [finding("chain-observations", "sha256", "does not match the registry's evidence digest", digest)], {}
    table = {}
    for entry in value.get("code", []) if isinstance(value, dict) else []:
        if isinstance(entry, dict) and isinstance(entry.get("address"), str):
            table[entry["address"].lower()] = entry
    return [], table


FIXTURE_KEYS = {"schema", "issue", "owner", "lazarus", "chain_id", "block_number", "block_hash", "block_hash_source",
                "plan", "capture", "payload", "verification", "replay", "not_applicable_findings", "addresses", "totals"}
ROW_KEYS = {"address", "type", "recorded_registry", "recorded_observation", "proved"}
REGISTRY_VALUE_KEYS = {"code_keccak256", "evidence", "source"}
OBSERVATION_VALUE_KEYS = {"code_keccak256", "code_length", "evidence", "source"}
PROVED_VALUE_KEYS = {"code_hash", "code_sha256", "code_bytes", "proof_record_sha256", "evidence", "source"}


def validate_fixture_rows(rows: Any, inventory: dict[str, Any], observations: dict[str, dict[str, Any]],
                          digest: str) -> tuple[list[str], dict[str, int]]:
    """Recorded and proved code identities stay in separate, labelled fields."""
    inventoried = {a["address"]: a for a in inventory["addresses"] if isinstance(a, dict) and isinstance(a.get("address"), str)}
    problems: list[str] = []
    counts = {"addresses": 0, "proved": 0, "recorded_registry_equal_to_proved": 0,
              "recorded_observation_equal_to_proved": 0}
    if not isinstance(rows, list):
        return [finding("fixture.addresses", "$", "expected a list", digest)], counts
    seen: set[str] = set()
    for index, row in enumerate(rows):
        record = f"fixture.addresses[{index}]"
        found = exact_keys(row, ROW_KEYS, record)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        address = row["address"]
        if not (isinstance(address, str) and ADDRESS.match(address)):
            problems.append(finding(record, "address", "is not a lowercase 20-byte hex address", digest))
            continue
        record = f"fixture.addresses.{address}"
        if address in seen:
            problems.append(finding(record, "address", "is duplicated", digest))
            continue
        seen.add(address)
        entry = inventoried.get(address)
        if entry is None:
            problems.append(finding(record, "address", "is not an inventory address", digest))
            continue
        if row["type"] != entry["type"]:
            problems.append(finding(record, "type", f"is {row['type']!r}, the inventory records {entry['type']!r}", digest))
        ok = True
        registry_value, observed, proved = row["recorded_registry"], row["recorded_observation"], row["proved"]
        for field, value, keys, source in (("recorded_registry", registry_value, REGISTRY_VALUE_KEYS, REGISTRY_PATH),
                                           ("recorded_observation", observed, OBSERVATION_VALUE_KEYS, OBSERVATIONS_PATH)):
            found = exact_keys(value, keys, f"{record}.{field}")
            if found:
                problems += [p + f" digest={digest}" for p in found]
                ok = False
                continue
            if value["evidence"] != RECORDED or value["source"] != source:
                problems.append(finding(f"{record}.{field}", "evidence",
                                        f"a recorded value is presented as proved: evidence {value['evidence']!r} from "
                                        f"{value['source']!r}; only {PROOFS_SOURCE} is proof-backed and this field must be "
                                        f"{RECORDED!r} from {source}", digest))
                ok = False
        found = exact_keys(proved, PROVED_VALUE_KEYS, f"{record}.proved")
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        if proved["evidence"] != PROVED or proved["source"] != PROOFS_SOURCE:
            problems.append(finding(f"{record}.proved", "source",
                                    f"a value from {proved['source']!r} labelled {proved['evidence']!r} is presented as "
                                    f"proved; a proved value is {PROVED!r} from {PROOFS_SOURCE}", digest))
            ok = False
        if not (isinstance(proved["code_hash"], str) and KECCAK.match(proved["code_hash"])
                and isinstance(proved["code_sha256"], str) and HEX64.match(proved["code_sha256"])
                and isinstance(proved["proof_record_sha256"], str) and HEX64.match(proved["proof_record_sha256"])
                and positive_int(proved["code_bytes"])):
            problems.append(finding(f"{record}.proved", "code_hash", "needs a code hash, code SHA-256, positive length and proof record SHA-256", digest))
            continue
        if ok:
            if registry_value["code_keccak256"] != entry["code_keccak256"]:
                problems.append(finding(f"{record}.recorded_registry", "code_keccak256",
                                        f"is {registry_value['code_keccak256']!r}, the inventory records {entry['code_keccak256']!r}", digest))
            obs = observations.get(address)
            if obs is None or (observed["code_keccak256"], observed["code_length"]) != (obs.get("code_keccak256"), obs.get("code_length")):
                problems.append(finding(f"{record}.recorded_observation", "code_keccak256",
                                        f"differs from {OBSERVATIONS_PATH}", digest))
            if observed["code_length"] != proved["code_bytes"]:
                problems.append(finding(f"{record}.proved", "code_bytes",
                                        f"proved length {proved['code_bytes']} differs from the recorded length {observed['code_length']}", digest))
        counts["addresses"] += 1
        if ok:
            counts["proved"] += 1
        if entry["code_keccak256"] != proved["code_hash"]:
            problems.append(finding(record, "code_hash", f"inventory code hash {entry['code_keccak256']} differs from "
                                    f"the fixture's proved code hash {proved['code_hash']}", digest))
        else:
            counts["recorded_registry_equal_to_proved"] += int(field_of(registry_value, "code_keccak256") == proved["code_hash"])
            counts["recorded_observation_equal_to_proved"] += int(field_of(observed, "code_keccak256") == proved["code_hash"])
    for address in sorted(set(inventoried) - seen):
        problems.append(finding(f"fixture.addresses.{address}", "address",
                                f"inventory code hash {inventoried[address].get('code_keccak256')} is absent from the fixture", digest))
    return problems, counts


def validate_fixture_record(root: Path, inventory: dict[str, Any], row: dict[str, Any]) -> tuple[list[str], dict[str, Any] | None]:
    name = "fixture"
    try:
        record, raw = read_json(root, FIXTURE_RECORD, name)
    except Refusal as refusal:
        return refusal.findings, None
    digest = sha256(raw)
    problems = exact_keys(record, FIXTURE_KEYS, name)
    if problems:
        return [p + f" digest={digest}" for p in problems], None

    def bad(field: str, detail: str) -> None:
        problems.append(finding(name, field, detail, digest))

    if record["schema"] != FIXTURE_SCHEMA or record["issue"] != 1355 or record["owner"] != "lazarus":
        bad("schema", f"must be {FIXTURE_SCHEMA} for issue 1355, owned by lazarus")
    for field, want in (("chain_id", CHAIN_ID), ("block_number", BLOCK_NUMBER), ("block_hash", BLOCK_HASH)):
        if record[field] != want:
            bad(field, f"is {record[field]!r}, the study fixes {want!r}")
    if record["block_hash_source"] != {"path": REGISTRY_PATH, "sha256": REGISTRY_SHA256, "row": REGISTRY_ROW}:
        bad("block_hash_source", f"must name the pinned registry row {REGISTRY_ROW} at {REGISTRY_SHA256}")
    if exact_keys(record["lazarus"], {"command", "manifest_tool_version"}, "fixture.lazarus") \
            or record["lazarus"]["command"] != "plugins/lazarus/scripts/lazarus.py" \
            or not text(record["lazarus"]["manifest_tool_version"], 32):
        bad("lazarus", "must name plugins/lazarus/scripts/lazarus.py and the manifest tool version")
    plan = record["plan"]
    plan_keys = {"sha256", "limits", "proof_targets", "storage_slots", "requests", "request_method", "request_evidence"}
    limits: dict[str, Any] = {}
    if exact_keys(plan, plan_keys, "fixture.plan") or exact_keys(plan["limits"], LIMIT_KEYS, "fixture.plan.limits"):
        bad("plan", f"must carry {sorted(plan_keys)} and the four declared limits {sorted(LIMIT_KEYS)}")
    else:
        limits = plan["limits"]
        if not all(positive_int(limits[k]) for k in LIMIT_KEYS):
            bad("plan.limits", "every request, byte and time limit must be a positive integer declared before capture")
        if not (isinstance(plan["sha256"], str) and HEX64.match(plan["sha256"])):
            bad("plan.sha256", "is not a SHA-256")
        if (plan["proof_targets"], plan["storage_slots"], plan["requests"], plan["request_method"], plan["request_evidence"]) \
                != (ADDRESS_COUNT, 0, ADDRESS_COUNT, "eth_getCode", "recorded-rpc"):
            bad("plan", f"must target all {ADDRESS_COUNT} addresses with account proofs and one recorded eth_getCode each")
    capture = record["capture"]
    capture_keys = {"entry", "credential", "observed_at", "requests", "response_bytes", "elapsed_seconds", "script_sha256", "attempts"}
    if exact_keys(capture, capture_keys, "fixture.capture"):
        bad("capture", f"must carry {sorted(capture_keys)}")
    else:
        if not (text(capture["entry"]) and text(capture["credential"]) and isinstance(capture["observed_at"], str)
                and STAMP.match(capture["observed_at"]) and isinstance(capture["script_sha256"], str)
                and HEX64.match(capture["script_sha256"]) and isinstance(capture["attempts"], list)
                and capture["attempts"] and all(text(a) for a in capture["attempts"])):
            bad("capture", "must name the entry point, credential handling, UTC time, script digest and every attempt")
        if not (positive_int(capture["requests"]) and positive_int(capture["response_bytes"])
                and isinstance(capture["elapsed_seconds"], (int, float)) and not isinstance(capture["elapsed_seconds"], bool)):
            bad("capture", "request count, byte count and elapsed time must be recorded as numbers")
        elif limits and all(positive_int(limits[k]) for k in LIMIT_KEYS):
            if capture["requests"] > limits["max_requests"] or capture["response_bytes"] > limits["max_total_bytes"] \
                    or capture["elapsed_seconds"] > limits["max_elapsed_seconds"]:
                bad("capture", "the recorded capture exceeds a declared limit")
    payload = record["payload"]
    components: list[Any] = []
    if exact_keys(payload, {"retained_at", "fixture_digest", "manifest_sha256", "components"}, "fixture.payload"):
        bad("payload", "must name the retained fixture, its digest, manifest SHA-256 and components")
    else:
        components = payload["components"] if isinstance(payload["components"], list) else []
        if payload["retained_at"] != FIXTURE_PAYLOAD:
            bad("payload.retained_at", f"must be {FIXTURE_PAYLOAD}")
        if not all(isinstance(payload[k], str) and HEX64.match(payload[k]) for k in ("fixture_digest", "manifest_sha256")):
            bad("payload", "fixture_digest and manifest_sha256 must be SHA-256 values")
        if [c.get("path") if isinstance(c, dict) else None for c in components] != list(FIXTURE_COMPONENTS) or any(
                exact_keys(c, {"path", "bytes", "sha256"}, "fixture.payload.components") or not is_int(c["bytes"])
                or not (isinstance(c["sha256"], str) and HEX64.match(c["sha256"])) for c in components):
            bad("payload.components", f"must list {list(FIXTURE_COMPONENTS)} with bytes and SHA-256")
    verification = record["verification"]
    verification_keys = {"command", "exit", "fixture_digest", "state_root", "evidence_counts", "accounts_included",
                         "accounts_absent", "canonical_chain_claim"}
    if exact_keys(verification, verification_keys, "fixture.verification"):
        bad("verification", f"must carry {sorted(verification_keys)}")
    else:
        if verification["exit"] != 0 or verification["command"] != f"python3 plugins/lazarus/scripts/lazarus.py verify {FIXTURE_PAYLOAD}":
            bad("verification.exit", f"the fixture is not verified: lazarus.py verify exit {verification['exit']!r}")
        if verification["fixture_digest"] != payload.get("fixture_digest"):
            bad("verification.fixture_digest", "differs from the retained fixture digest")
        want = {"proof_backed": ADDRESS_COUNT, "header_bound": 1, "recorded_rpc": ADDRESS_COUNT}
        if verification["evidence_counts"] != want or verification["accounts_included"] != ADDRESS_COUNT \
                or verification["accounts_absent"] != 0:
            bad("verification.evidence_counts", f"must be {want} with {ADDRESS_COUNT} included accounts")
        if verification["canonical_chain_claim"] is not False:
            bad("verification.canonical_chain_claim", "a self-consistent header is not a canonical-chain proof")
        if not (isinstance(verification["state_root"], str) and KECCAK.match(verification["state_root"])):
            bad("verification.state_root", "is not a 32-byte hash")
    replay = record["replay"]
    if exact_keys(replay, {"command", "requests", "served", "code_equal_to_proof_record", "miss_probe_error_code"}, "fixture.replay") \
            or not text(replay["command"]) or FIXTURE_PAYLOAD not in replay["command"] \
            or (replay["requests"], replay["served"], replay["code_equal_to_proof_record"], replay["miss_probe_error_code"]) \
            != (ADDRESS_COUNT, ADDRESS_COUNT, ADDRESS_COUNT, MISS_ERROR):
        bad("replay", f"offline replay must serve all {ADDRESS_COUNT} code reads equal to the proof records and miss with {MISS_ERROR}")
    notes = record["not_applicable_findings"]
    if not isinstance(notes, list) or any(exact_keys(n, {"id", "reason"}, "fixture.not_applicable_findings") or not text(n["reason"])
                                         for n in notes) or {n["id"] for n in notes} != NOT_APPLICABLE:
        bad("not_applicable_findings", f"must carry {sorted(NOT_APPLICABLE)} each with its reason")
    observation_problems, observations = load_observations(root, row)
    problems += observation_problems
    row_problems, counts = validate_fixture_rows(record["addresses"], inventory, observations, digest)
    problems += row_problems
    if record["totals"] != counts:
        bad("totals", f"are {record['totals']!r}, the rows give {counts!r}")
    summary = {"record": FIXTURE_RECORD, "sha256": digest, "fixture_digest": payload.get("fixture_digest"),
               "block_hash": record["block_hash"], **counts}
    return problems, {"record": record, "summary": summary}


RELEASE_KEYS = {"schema", "issue", "owner", "release_id", "name", "created_at", "payload", "verification", "inputs",
                "fixture", "components", "captures", "totals"}
CAPTURE_KEYS = {"id", "component", "evidence_class", "coverage_status", "record_count", "subjects", "source_reference"}


def validate_release_record(root: Path, row: dict[str, Any], fixture: dict[str, Any] | None) -> tuple[list[str], dict[str, Any] | None]:
    name = "release"
    try:
        record, raw = read_json(root, RELEASE_RECORD, name)
    except Refusal as refusal:
        return refusal.findings, None
    digest = sha256(raw)
    problems = exact_keys(record, RELEASE_KEYS, name)
    if problems:
        return [p + f" digest={digest}" for p in problems], None

    def bad(field: str, detail: str) -> None:
        problems.append(finding(name, field, detail, digest))

    if record["schema"] != RELEASE_SCHEMA or record["issue"] != 1355 or record["owner"] != "alexandria":
        bad("schema", f"must be {RELEASE_SCHEMA} for issue 1355, owned by alexandria")
    if not (isinstance(record["release_id"], str) and RELEASE_ID.match(record["release_id"])):
        bad("release_id", "is not a sha256: release identity")
    if not (text(record["name"], 128) and isinstance(record["created_at"], str) and STAMP.match(record["created_at"])):
        bad("name", "needs a release name and UTC creation time")
    expected_payload = {"retained_at": RELEASE_PAYLOAD, "plan_retained_at": RELEASE_PLAN}
    payload = record["payload"]
    if exact_keys(payload, {"retained_at", "manifest_sha256", "plan_retained_at", "plan_sha256"}, "release.payload") \
            or any(payload[k] != v for k, v in expected_payload.items()) \
            or not all(isinstance(payload[k], str) and HEX64.match(payload[k]) for k in ("manifest_sha256", "plan_sha256")):
        bad("payload", f"must name {RELEASE_PAYLOAD} and {RELEASE_PLAN} with their SHA-256 values")
    verification = record["verification"]
    if exact_keys(verification, {"command", "exit", "release_id"}, "release.verification") \
            or verification["exit"] != 0 \
            or verification["command"] != f"python3 plugins/alexandria/scripts/alexandria.py verify {RELEASE_PAYLOAD}":
        bad("verification.exit", f"the release is not verified: alexandria.py verify exit {verification.get('exit')!r}"
            if isinstance(verification, dict) else "the release is not verified")
    elif verification["release_id"] != record["release_id"]:
        bad("verification.release_id", "differs from the release identity")
    inputs: dict[str, str] = {}
    listed = record["inputs"] if isinstance(record["inputs"], list) else []
    for index, item in enumerate(listed):
        sub = f"release.inputs[{index}]"
        found = exact_keys(item, {"role", "path", "sha256", "bytes"}, sub)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        if RELEASE_INPUTS.get(item["role"]) != item["path"] or item["role"] in inputs:
            problems.append(finding(sub, "role", f"must be one of {sorted(RELEASE_INPUTS)} at its fixed path, once", digest))
            continue
        if item["path"] == REGISTRY_PATH:
            # The release preserved the capture-time revision. The current file is
            # bound by its projection in `load_registry`, and `owner-handoffs`
            # checks the preserved bytes' projection against the same pin.
            if (item["sha256"], item["bytes"]) != (REGISTRY_SHA256, REGISTRY_BYTES):
                problems.append(finding(sub, "sha256", f"states {item['sha256']!r} and {item['bytes']!r} bytes for {item['path']}; "
                                        f"the capture-time revision is {REGISTRY_BYTES} bytes hashing to {REGISTRY_SHA256}", digest))
            inputs[item["role"]] = REGISTRY_SHA256
            continue
        try:
            actual, size = file_digest(root, item["path"], sub)
        except Refusal as refusal:
            problems += refusal.findings
            continue
        if (item["sha256"], item["bytes"]) != (actual, size):
            problems.append(finding(sub, "sha256", f"states {item['sha256']!r} for {item['path']}; its bytes hash to {actual}", actual))
        elif actual != pinned_digest(row, item["path"]):
            problems.append(finding(sub, "sha256", f"{item['path']} does not match its pinned digest", actual))
        inputs[item["role"]] = actual
    if set(inputs) != set(RELEASE_INPUTS):
        bad("inputs", f"must preserve {sorted(RELEASE_INPUTS)} by digest")
    fixture_record = (fixture or {}).get("record") or {}
    fixture_payload = fixture_record.get("payload") if isinstance(fixture_record.get("payload"), dict) else {}
    expected_fixture = {"fixture_digest": fixture_payload.get("fixture_digest"), "manifest_sha256": fixture_payload.get("manifest_sha256")}
    if record["fixture"] != expected_fixture:
        bad("fixture", f"must bind the fixture record's digest and manifest SHA-256 {expected_fixture!r}")
    fixture_files = {c.get("path"): c.get("sha256") for c in fixture_payload.get("components", []) if isinstance(c, dict)}
    components = record["components"] if isinstance(record["components"], list) else []
    names = []
    total_bytes = 0
    for index, item in enumerate(components):
        sub = f"release.components[{index}]"
        found = exact_keys(item, {"name", "role", "sha256", "bytes", "access", "redistribution"}, sub)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        names.append(item["name"])
        total_bytes += item["bytes"] if is_int(item["bytes"]) else 0
        if RELEASE_COMPONENTS.get(item["name"]) != item["role"]:
            problems.append(finding(sub, "role", f"{item['name']!r} with role {item['role']!r} is not a declared component", digest))
            continue
        if item["access"] != "public" or item["redistribution"] not in ("permitted", "unknown"):
            problems.append(finding(sub, "access", "every component must be public with a stated redistribution class", digest))
        if item["name"] in RELEASE_INPUTS:
            want = inputs.get(item["name"])
        elif item["name"] == "fixture-manifest":
            want = fixture_payload.get("manifest_sha256")
        else:
            want = fixture_files.get(FIXTURE_FILE_COMPONENTS[item["name"]])
        if item["sha256"] != want:
            problems.append(finding(sub, "sha256", f"{item['name']} is {item['sha256']!r}, its source record gives {want!r}", digest))
    if sorted(names) != sorted(RELEASE_COMPONENTS):
        bad("components", f"must be exactly {sorted(RELEASE_COMPONENTS)}")
    captures = record["captures"] if isinstance(record["captures"], list) else []
    by_id = {}
    for index, item in enumerate(captures):
        found = exact_keys(item, CAPTURE_KEYS, f"release.captures[{index}]")
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        by_id[item["id"]] = item
    state = by_id.get("state-proof")
    if set(by_id) != {"state-proof", "chain-observations"} or state is None \
            or (state["component"], state["evidence_class"], state["coverage_status"], state["record_count"],
                state["subjects"], state["source_reference"]) != ("fixture-manifest", "proof-backed-state", "complete",
                                                                  len(FIXTURE_COMPONENTS), ADDRESS_COUNT,
                                                                  fixture_payload.get("fixture_digest")):
        bad("captures", f"the state-proof capture must be proof-backed-state over the fixture's {ADDRESS_COUNT} subjects")
    observed = by_id.get("chain-observations")
    if observed is not None and (observed["component"], observed["evidence_class"]) != ("chain-observations", "recorded-rpc"):
        bad("captures", "the chain-observations capture must stay recorded-rpc evidence")
    totals = {"components": len(components), "captures": len(captures), "bytes": total_bytes}
    if record["totals"] != totals:
        bad("totals", f"are {record['totals']!r}, the components give {totals!r}")
    summary = {"record": RELEASE_RECORD, "sha256": digest, "release_id": record["release_id"], **totals}
    return problems, {"record": record, "summary": summary}


def validate_handoffs(root: Path) -> tuple[list[str], dict[str, Any] | None]:
    name = "owner-handoffs"
    try:
        record, raw = read_json(root, HANDOFFS_RECORD, name)
    except Refusal as refusal:
        return refusal.findings, None
    digest = sha256(raw)
    problems = exact_keys(record, {"schema", "issue", "rows"}, name)
    if problems:
        return [p + f" digest={digest}" for p in problems], None
    if record["schema"] != HANDOFFS_SCHEMA or record["issue"] != 1355:
        problems.append(finding(name, "schema", f"must be {HANDOFFS_SCHEMA} for issue 1355", digest))
    rows = record["rows"] if isinstance(record["rows"], list) else []
    seen: set[str] = set()
    complete = outstanding = handed_off = 0
    for index, row in enumerate(rows):
        sub = f"owner-handoffs.rows[{index}]"
        found = exact_keys(row, {"handoff", "producer", "reviewer", "artefact", "status", "note"}, sub)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        handoff = row["handoff"]
        if handoff not in HANDOFFS or handoff in seen:
            problems.append(finding(sub, "handoff", f"{handoff!r} is not one of {sorted(HANDOFFS)} or is repeated", digest))
            continue
        seen.add(handoff)
        sub = f"owner-handoffs.{handoff}"
        ok = True
        for field in ("producer", "reviewer", "note"):
            if not text(row[field], 500):
                problems.append(finding(sub, field, "the handoff row is incomplete: it must name its producer, reviewer and note", digest))
                ok = False
        artefact = row["artefact"]
        if exact_keys(artefact, {"path", "sha256"}, f"{sub}.artefact") or artefact["path"] != HANDOFFS[handoff]:
            problems.append(finding(sub, "artefact", f"the handoff row is incomplete: it must name {HANDOFFS[handoff]} and its SHA-256", digest))
            ok = False
        elif handoff == "registry":
            # Handed on and reviewed at the capture-time revision; `load_registry`
            # binds the current file to that revision's projection.
            if artefact["sha256"] != REGISTRY_SHA256:
                problems.append(finding(sub, "artefact.sha256", f"states {artefact['sha256']!r}; the registry was handed on "
                                        f"at its capture-time revision {REGISTRY_SHA256}", digest))
                ok = False
        else:
            try:
                actual, _ = file_digest(root, artefact["path"], sub)
            except Refusal as refusal:
                problems += refusal.findings
                ok = False
            else:
                if artefact["sha256"] != actual:
                    problems.append(finding(sub, "artefact.sha256", f"states {artefact['sha256']!r}; {artefact['path']} hashes to {actual}", actual))
                    ok = False
        status = row["status"]
        if status == REVIEW_OUTSTANDING and handoff not in REVIEW_OUTSTANDING_ALLOWED:
            problems.append(finding(sub, "status", f"is {status!r}; only {sorted(REVIEW_OUTSTANDING_ALLOWED)} may be "
                                    "handed on with its target-maintainer review outstanding", digest))
            ok = False
        elif status not in ("complete", REVIEW_OUTSTANDING):
            problems.append(finding(sub, "status", f"is {status!r}, not complete or {REVIEW_OUTSTANDING}", digest))
            ok = False
        handed_off += int(ok)
        complete += int(ok and status == "complete")
        outstanding += int(ok and status == REVIEW_OUTSTANDING)
    for missing in sorted(set(HANDOFFS) - seen):
        problems.append(finding(f"owner-handoffs.{missing}", "handoff", "has no row", digest))
    return problems, {"record": HANDOFFS_RECORD, "sha256": digest, "rows": len(rows), "handed_off": handed_off,
                      "complete": complete, "review_outstanding": outstanding}


def validate_chain_evidence(root: Path, inventory: dict[str, Any], row: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    problems, fixture = validate_fixture_record(root, inventory, row)
    release_problems, release = validate_release_record(root, row, fixture)
    handoff_problems, handoffs = validate_handoffs(root)
    return problems + release_problems + handoff_problems, {
        "fixture": (fixture or {}).get("summary"), "release": (release or {}).get("summary"), "handoffs": handoffs,
        "_fixture": (fixture or {}).get("record"), "_release": (release or {}).get("record")}


# --- retained payloads (owner-handoffs conformance only) ---------------------------

def sibling_verifiers(root: Path) -> dict[str, Any]:
    """Lazarus's and Alexandria's own verifiers, loaded in-process from this tree."""

    def load(plugin: str) -> None:
        scripts = str(root / "plugins" / plugin / "scripts")
        if scripts not in sys.path:
            sys.path.insert(0, scripts)

    def fixture(path: Path) -> dict[str, Any]:
        load("lazarus")
        from lazarus_lib.verifier import verify_fixture  # pylint: disable=import-outside-toplevel
        return verify_fixture(path)

    def release(path: Path) -> str:
        load("alexandria")
        from alexandria_lib.release import verify  # pylint: disable=import-outside-toplevel
        return verify(path)

    return {"fixture": fixture, "release": release}


def jsonl_lines(raw: bytes) -> list[bytes]:
    lines = raw.split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return lines


def validate_fixture_payload(root: Path, record: dict[str, Any], inventory: dict[str, Any], verify_fixture: Any) -> list[str]:
    """Recompute the committed fixture record from the retained fixture bytes."""
    name = "fixture-payload"
    problems: list[str] = []
    payload = record["payload"]
    try:
        manifest_raw = read_bytes(root, f"{FIXTURE_PAYLOAD}/manifest.json", name, MAX_JSON)
    except Refusal as refusal:
        return refusal.findings
    manifest_digest = sha256(manifest_raw)
    if manifest_digest != payload["manifest_sha256"]:
        problems.append(finding(name, "manifest.sha256", f"differs from the record's {payload['manifest_sha256']}", manifest_digest))
    try:
        report = verify_fixture(root / FIXTURE_PAYLOAD)
    except Exception as exc:  # the sibling's own refusal, reported rather than trusted
        problems.append(finding(name, "verification", f"Lazarus verify refused the retained fixture: {type(exc).__name__}: {exc}", manifest_digest))
        return problems
    verification = record["verification"]
    observed = {"fixture_digest": report.get("fixture_digest"), "block_hash": report.get("block_hash"),
                "block_number": report.get("block_number"), "state_root": report.get("state_root"),
                "evidence_counts": report.get("evidence_counts"),
                "accounts_included": (report.get("proof_backed") or {}).get("accounts_included"),
                "accounts_absent": (report.get("proof_backed") or {}).get("accounts_absent")}
    expected = {"fixture_digest": payload["fixture_digest"], "block_hash": BLOCK_HASH, "block_number": hex(BLOCK_NUMBER),
                "state_root": verification["state_root"], "evidence_counts": verification["evidence_counts"],
                "accounts_included": verification["accounts_included"], "accounts_absent": verification["accounts_absent"]}
    for field, want in expected.items():
        if observed[field] != want:
            problems.append(finding(name, field, f"Lazarus verify reports {observed[field]!r}, the record states {want!r}", manifest_digest))
    manifest = parse_json(manifest_raw, name)
    if manifest.get("tool_version") != record["lazarus"]["manifest_tool_version"]:
        problems.append(finding(name, "tool_version", "differs from the record's Lazarus manifest tool version", manifest_digest))
    listed = [{"path": c.get("path"), "bytes": c.get("bytes"), "sha256": c.get("sha256")} for c in manifest.get("components", [])]
    if listed != payload["components"]:
        problems.append(finding(name, "components", "the retained manifest's components differ from the record", manifest_digest))
    files: dict[str, bytes] = {}
    for component in payload["components"]:
        try:
            raw = read_bytes(root, f"{FIXTURE_PAYLOAD}/{component['path']}", name, MAX_PAYLOAD)
        except Refusal as refusal:
            problems += refusal.findings
            continue
        files[component["path"]] = raw
        if (sha256(raw), len(raw)) != (component["sha256"], component["bytes"]):
            problems.append(finding(name, component["path"], "bytes differ from the recorded length or SHA-256", sha256(raw)))
    inventoried = {a["address"] for a in inventory["addresses"]}
    plan_raw = files.get("plan.json", b"")
    if sha256(plan_raw) != record["plan"]["sha256"]:
        problems.append(finding(name, "plan.sha256", "the retained plan differs from the record", sha256(plan_raw)))
    elif plan_raw:
        plan = parse_json(plan_raw, name)
        if plan.get("limits") != record["plan"]["limits"]:
            problems.append(finding(name, "plan.limits", "the limits the capture ran under differ from the record", sha256(plan_raw)))
        targets = plan.get("proof_targets", [])
        requests = plan.get("requests", [])
        if {t.get("address") for t in targets} != inventoried or any(t.get("slots") for t in targets) \
                or {tuple(r.get("params", [])) for r in requests} != {(a, hex(BLOCK_NUMBER)) for a in inventoried} \
                or any((r.get("method"), r.get("evidence")) != ("eth_getCode", "recorded-rpc") for r in requests):
            problems.append(finding(name, "plan", "the plan does not target exactly the inventory addresses", sha256(plan_raw)))
    rows = {r["address"]: r for r in record["addresses"] if isinstance(r, dict)}
    proved_code: dict[str, bytes] = {}
    for line in jsonl_lines(files.get("proofs.jsonl", b"")):
        entry = parse_json(line, name)
        address = str(entry.get("address", "")).lower()
        row = rows.get(address)
        if row is None:
            problems.append(finding(name, "proofs", f"{address} has a proof record but no fixture row", sha256(line)))
            continue
        proved = row["proved"]
        try:
            code = bytes.fromhex(str(entry.get("code", ""))[2:])
        except ValueError:
            problems.append(finding(name, "proofs", f"{address} carries malformed code", sha256(line)))
            continue
        proved_code[address] = code
        actual = {"code_hash": entry.get("code_hash"), "code_sha256": sha256(code), "code_bytes": len(code),
                  "proof_record_sha256": sha256(line)}
        for field, value in actual.items():
            if proved[field] != value:
                problems.append(finding(f"{name}.{address}", field, f"the proof record gives {value!r}, the fixture row states {proved[field]!r}", sha256(line)))
        if entry.get("evidence") != PROVED or entry.get("block_hash") != BLOCK_HASH:
            problems.append(finding(f"{name}.{address}", "evidence", "the proof record is not proof-backed at the fixed block", sha256(line)))
    if set(proved_code) != inventoried:
        problems.append(finding(name, "proofs", f"proves {len(proved_code)} inventory addresses, not {len(inventoried)}"))
    served = 0
    for line in jsonl_lines(files.get("rpc.jsonl", b"")):
        entry = parse_json(line, name)
        params = entry.get("params") or [None]
        address = str(params[0]).lower()
        result = (entry.get("outcome") or {}).get("result")
        try:
            recorded_code = bytes.fromhex(str(result)[2:])
        except ValueError:
            recorded_code = None
        if entry.get("method") == "eth_getCode" and recorded_code is not None and recorded_code == proved_code.get(address):
            served += 1
        else:
            problems.append(finding(f"{name}.{address}", "rpc", "the recorded eth_getCode result differs from the proved code", sha256(line)))
    if served != ADDRESS_COUNT:
        problems.append(finding(name, "rpc", f"{served} recorded code reads equal the proved code, not {ADDRESS_COUNT}"))
    try:
        script, _ = file_digest(root, CAPTURE_SCRIPT, name)
    except Refusal as refusal:
        problems += refusal.findings
    else:
        if script != record["capture"]["script_sha256"]:
            problems.append(finding(name, "capture.script_sha256", f"{CAPTURE_SCRIPT} differs from the record", script))
    return problems


def preserved_registry_problems(root: Path, manifest: dict[str, Any], manifest_digest: str) -> list[str]:
    """The retained release's registry bytes are the capture-time revision and project to the current pin.

    The object is read from the manifest's `object_path` under the retained
    release, its whole-file SHA-256 and byte count must be `REGISTRY_SHA256` and
    `REGISTRY_BYTES`, and its `registry_projection` must hash to
    `REGISTRY_PROJECTION_SHA256`.
    """
    name = "release-payload.registry"
    entries = [c for c in manifest.get("components", []) if isinstance(c, dict) and c.get("name") == "registry"]
    if len(entries) != 1 or not isinstance(entries[0].get("object_path"), str):
        return [finding(name, "object_path", "the retained manifest names no single registry object", manifest_digest)]
    try:
        raw = read_bytes(root, f"{RELEASE_PAYLOAD}/{entries[0]['object_path']}", name, MAX_PAYLOAD)
    except Refusal as refusal:
        return refusal.findings
    digest = sha256(raw)
    if (digest, len(raw)) != (REGISTRY_SHA256, REGISTRY_BYTES):
        return [finding(name, "sha256", f"the preserved registry is {len(raw)} bytes, not the capture-time "
                        f"{REGISTRY_BYTES} bytes hashing to {REGISTRY_SHA256}", digest)]
    _, projected = registry_projection(parse_json(raw, name))
    if projected != REGISTRY_PROJECTION_SHA256:
        return [finding(name, "projection", f"the preserved registry projects to {projected}, not {REGISTRY_PROJECTION_SHA256}", digest)]
    return []


def validate_release_payload(root: Path, record: dict[str, Any], inventory: dict[str, Any], verify_release: Any) -> list[str]:
    """Recompute the committed release record from the retained release bytes."""
    name = "release-payload"
    problems: list[str] = []
    try:
        manifest_raw = read_bytes(root, f"{RELEASE_PAYLOAD}/manifest.json", name, MAX_JSON)
    except Refusal as refusal:
        return refusal.findings
    manifest_digest = sha256(manifest_raw)
    if manifest_digest != record["payload"]["manifest_sha256"]:
        problems.append(finding(name, "manifest.sha256", f"differs from the record's {record['payload']['manifest_sha256']}", manifest_digest))
    try:
        released = verify_release(root / RELEASE_PAYLOAD)
    except Exception as exc:  # the sibling's own refusal, reported rather than trusted
        problems.append(finding(name, "verification", f"Alexandria verify refused the retained release: {type(exc).__name__}: {exc}", manifest_digest))
        return problems
    if released != record["release_id"]:
        problems.append(finding(name, "release_id", f"Alexandria verify reports {released!r}, the record states {record['release_id']!r}", manifest_digest))
    manifest = parse_json(manifest_raw, name)
    if (manifest.get("release_id"), manifest.get("release")) != (record["release_id"], {"created_at": record["created_at"], "name": record["name"]}):
        problems.append(finding(name, "release", "the retained manifest's identity, name or time differs from the record", manifest_digest))
    listed = [{"name": c.get("name"), "role": c.get("role"), "sha256": str(c.get("sha256", "")).removeprefix("sha256:"),
               "bytes": c.get("bytes"), "access": c.get("access"), "redistribution": c.get("redistribution")}
              for c in manifest.get("components", [])]
    if sorted(listed, key=lambda c: str(c["name"])) != sorted(record["components"], key=lambda c: str(c["name"])):
        problems.append(finding(name, "components", "the retained manifest's components differ from the record", manifest_digest))
    problems += preserved_registry_problems(root, manifest, manifest_digest)
    captures = []
    for capture in manifest.get("captures", []):
        scope = capture.get("scope") or {}
        captures.append({"id": capture.get("id"), "component": capture.get("component"),
                         "evidence_class": capture.get("evidence_class"),
                         "coverage_status": (capture.get("coverage") or {}).get("status"),
                         "record_count": (capture.get("coverage") or {}).get("record_count"),
                         "subjects": len(scope.get("subjects") or []),
                         "source_reference": (capture.get("source") or {}).get("reference")})
        if capture.get("id") == "state-proof":
            subjects = {s.split(":")[-1] for s in scope.get("subjects") or []}
            if subjects != {a["address"] for a in inventory["addresses"]}:
                problems.append(finding(name, "captures.state-proof", "subjects differ from the inventory addresses", manifest_digest))
    if sorted(captures, key=lambda c: str(c["id"])) != sorted(record["captures"], key=lambda c: str(c["id"])):
        problems.append(finding(name, "captures", "the retained manifest's captures differ from the record", manifest_digest))
    try:
        plan_digest, _ = file_digest(root, RELEASE_PLAN, name)
    except Refusal as refusal:
        problems += refusal.findings
    else:
        if plan_digest != record["payload"]["plan_sha256"]:
            problems.append(finding(name, "plan_sha256", f"{RELEASE_PLAN} differs from the record", plan_digest))
    return problems


# --- Hermes evidence: the sealed V2 anchor and the two Gate 5 rejections ------------

# The anchors this step seals: v2 for the selector rejection, V1 for the layout rejection.
BASELINE_TREES = ("v2-c7be", "v1-488b", "col-46db", "fee-ac73", "rp-5d7f")
# Tree -> the directory under baselines/ that holds its Gate 1.
BASELINE_NAMES = {"v2-c7be": "v2-c7be", "v1-488b": "v1-488b", "col-46db": "collateral-46db",
                  "fee-ac73": "fee-ac73", "rp-5d7f": "role-provider-5d7f"}
# The two private repositories. Their public records carry maps, counts and digests only.
RESTRICTED_TREES = ("fee-ac73", "rp-5d7f")
BASELINE_DIRS = {tree: f"{DOCS}/baselines/{BASELINE_NAMES[tree]}" for tree in BASELINE_TREES}
BASELINE_RECORDS = {tree: f"{BASELINE_DIRS[tree]}/record.json" for tree in BASELINE_TREES}
BASELINE_SCHEMA = "kickoff-hermes-1355-baseline/v1"
RESTRICTED_BASELINE_SCHEMA = "kickoff-hermes-1355-restricted-baseline/v1"
# A restricted anchor's complete Hermes run directory, named by the SHA-256 of its state.json.
RESTRICTED_RUNS = ".hexaemeron/restricted/hermes"
# What a restricted anchor's public directory never carries.
WITHHELD = ["baseline-sources/", "logs/", "baseline-source-manifest.json", "baseline.forge-config.json",
            "baseline.forge-version.txt", "baseline.gas-rule-corpus.json", "baseline.gas-snapshot",
            "baseline.git-status.bin", "result.json", "state.json"]
EXCLUSIONS_RECORD = f"{DOCS}/baselines/exclusions.json"
EXCLUSIONS_SCHEMA = "kickoff-hermes-1355-exclusions/v1"
EQUIVALENCE_DIR = f"{DOCS}/equivalence"
EQUIVALENCE_RECORD = f"{EQUIVALENCE_DIR}/record.json"
EQUIVALENCE_SCHEMA = "kickoff-hermes-1355-equivalence/v1"
EQUIVALENCE_FILES = ("method-identifiers.json", "storage-layout.json", "storage-layout.raw.json")
REJECTION_SCHEMA = "kickoff-hermes-1355-rejection/v1"
REJECTION_RECORDS = {kind: f"{DOCS}/rejections/{kind}/record.json" for kind in ("selector", "layout")}
HERMES_RUN_SCHEMA = "hermes/v1"
CORPUS = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
CORPUS_SHA256 = "5d1773f9a5f51e957bd769deb3b030b670fa10499e33fce4a8df3a2e221bd5ac"
FUZZ_SEED = "0x5EED"
# Study section 3: the compiler foundry.toml resolves at each Hermes tree, and the anchor's pass count.
TREE_COMPILER = {"v2-c7be": {"solc": "0.8.25", "evm_version": "cancun", "via_ir": False},
                 "v1-488b": {"solc": "0.8.22", "evm_version": "shanghai", "via_ir": False},
                 "col-46db": {"solc": "0.8.28", "evm_version": "cancun", "via_ir": False},
                 "fee-ac73": {"solc": "0.8.25", "evm_version": "cancun", "via_ir": False},
                 "rp-5d7f": {"solc": "0.8.25", "evm_version": "cancun", "via_ir": False}}
ANCHOR_PASSES = {"v2-c7be": 795, "v1-488b": 348, "col-46db": 48, "fee-ac73": 19, "rp-5d7f": 5}
BASE_ENVIRONMENT = {"HOME": "<operator home>", "LANG": "en_US.UTF-8", "NO_COLOR": "1",
                    "PATH": "<operator home>/.foundry/bin:/usr/bin:/bin:/usr/sbin:/sbin"}
INTERPRETER = "Python 3.14.6"
GATE5_PREFIX = {"selector": "public method identifiers changed", "layout": "protected storage layout changed"}
GATE5_FAMILY = {"selector": "method-identifiers", "layout": "storage-layout"}
BASELINE_TEXT = ("baseline.forge-version.txt", "baseline.git-status.bin", "baseline.gas-snapshot")
# Per-rule hunk checks. Each hunk of a candidate must change a line matching the rule's
# pattern; `deletions_only` and `line` narrow it further. This is a token check on the
# diff; whether each hunk implements the rule stays Hermes's single-class attestation.
RULE_HUNKS = {
    "MEM-16": {"class": "calldata-memory", "pattern": r"getMarketsForHooksInstance|address hooksInstance",
               "deletions_only": True, "line": None},
    "STO-18": {"class": "storage-packing", "pattern": r"ShortString|Fallback|\b_name\b|\b_symbol\b",
               "deletions_only": False, "line": None},
    "STO-04": {"class": "storage-packing", "pattern": r"[Tt]mpEscrow|TmpAccount|TmpAsset",
               "deletions_only": False, "line": None},
    "STO-01": {"class": "storage-packing", "pattern": r"\bfullLiquidationIndex\b|\btotalShares\b",
               "deletions_only": False, "line": r"^\s*(///.*|uint\d+ public [A-Za-z_]\w*;)?\s*$"},
}
TEST_PATH = re.compile(r"(^|/)(test|tests)/|\.t\.sol$")
ATTEMPT_KEYS = {"id", "study_order", "note", "tree", "repository", "commit", "intended_contract", "rule",
                "optimisation_class", "patch", "patch_sha256", "candidate_solidity_diff", "invocation",
                "baseline_exit", "verify_exit", "gate_reached", "reason", "output", "restoration", "run_files"}
METHOD_CHECK_KEYS = {"contract", "reason", "argv", "environment", "before", "after", "equal"}


def load_hermes(root: Path) -> Any:
    """Hermes's own module, loaded only while its bytes match the pinned digest."""

    def pinned() -> None:
        raw = read_bytes(root, HERMES, "hermes")
        if sha256(raw) != HERMES_SHA256:
            raise Refusal([finding("hermes", "sha256", f"{HERMES} does not match the pinned {HERMES_SHA256}", sha256(raw))])

    import importlib.util  # pylint: disable=import-outside-toplevel
    pinned()
    name = "kickoff_hermes_1355_hermes"
    spec = importlib.util.spec_from_file_location(name, root / HERMES)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses resolve the defining module by name
    try:
        spec.loader.exec_module(module)
    finally:
        sys.modules.pop(name, None)
    pinned()  # a file swapped while it loaded is refused rather than trusted
    return module.__dict__


def canonical_layout_text(hermes: dict[str, Any], raw: bytes, record: str) -> str:
    value = parse_json(raw, record)
    try:
        return canonical_text(hermes["canonical_storage_layout"](value, 5, 50))
    except Exception as exc:  # Hermes's own GateFailure, reported rather than trusted
        raise Refusal([finding(record, "layout", f"Hermes cannot canonicalise it: {exc}", sha256(raw))]) from None


def expected_protected(inventory: dict[str, Any], tree: str) -> list[dict[str, str]]:
    """Every protected identifier anchored at `tree`, labelled by contract name, in inventory order."""
    seen: list[str] = []
    for item in inventory["types"]:
        if item.get("anchor") == tree and item.get("anchor_identifier") not in seen:
            seen.append(item["anchor_identifier"])
    return [{"identifier": identifier, "label": identifier.rsplit(":", 1)[1]} for identifier in seen]


def environment_for(inventory: dict[str, Any], tree: str) -> dict[str, str]:
    return {**BASE_ENVIRONMENT, **inventory["trees"][tree]["gate1_environment"]}


def baseline_argv(protected: list[dict[str, str]], exclusions: list[str]) -> list[str]:
    argv = ["python3", HERMES, "baseline", "--repo", "<fresh checkout>", "--evidence-dir", "<empty run directory>",
            "--fuzz-seed", FUZZ_SEED]
    for path in exclusions:
        argv += ["--no-match-path", path]
    for contract in protected:
        argv += ["--protected-contract", f"{contract['label']}={contract['identifier']}"]
    return argv


def gate1_commands(exclusions: list[str]) -> list[str]:
    arguments = []
    for path in exclusions:
        arguments += ["--no-match-path", path]
    arguments += ["--fuzz-seed", FUZZ_SEED]
    return [" ".join(["forge", "snapshot", *arguments]), " ".join(["forge", "test", *arguments])]


def committed_files(root: Path, directory: str, declared: Any, record: str) -> tuple[list[str], dict[str, bytes]]:
    """Recompute each declared file's digest and refuse an undeclared file beside them."""
    problems: list[str] = []
    contents: dict[str, bytes] = {}
    if not isinstance(declared, dict) or not declared:
        return [finding(record, "run_files", "expected a non-empty object of path to sha256")], {}
    for relative, digest in sorted(declared.items()):
        try:
            raw = read_bytes(root, f"{directory}/{relative}", record)
        except Refusal as refusal:
            problems += refusal.findings
            continue
        actual = sha256(raw)
        if actual != digest:
            problems.append(finding(record, f"run_files.{relative}", f"recorded {digest} but the committed file hashes differently", actual))
            continue
        contents[relative] = raw
    present: list[str] = []
    stack = [""]
    while stack:
        prefix = stack.pop()
        base = f"{directory}/{prefix}".rstrip("/")
        try:
            names = list_directory(root, base, record)
        except Refusal as refusal:
            return problems + refusal.findings, contents
        for name in names:
            child = f"{prefix}{name}"
            if stat.S_ISDIR((root / base / name).lstat().st_mode):
                stack.append(child + "/")
            else:
                present.append(child)
    for extra in sorted(set(present) - set(declared)):
        problems.append(finding(record, "run_files", f"{directory}/{extra} is committed but not declared"))
    return problems, contents


def json_of(contents: dict[str, bytes], relative: str, record: str) -> Any:
    if relative not in contents:
        raise Refusal([finding(record, f"run_files.{relative}", "is not committed")])
    return parse_json(contents[relative], f"{record}:{relative}")


def validate_baseline(root: Path, inventory: dict[str, Any], hermes: dict[str, Any], tree_id: str) -> tuple[list[str], dict[str, Any]]:
    """One sealed public anchor Gate 1 (`v2-c7be`, `v1-488b` or `col-46db`).

    Recomputed from committed bytes: every file digest under `run/`, every entry of
    Hermes's `artifact_hashes` (the three text artefacts from `artefact_text`, the
    corpus copy from the repository corpus, the rest from the committed files),
    `forge_version_sha256`, `forge_config_sha256`, the source manifest, and each
    canonical layout from its raw inspector output through Hermes's own
    canonicaliser. Checked against the inventory and study: commit, protected set,
    exclusions, seed, compiler, environment, argv, status and Gate 1 commands.
    Recorded only: the pass count and the submodule list.
    """
    record_name = f"baseline.{tree_id}"
    try:
        value, raw = read_json(root, BASELINE_RECORDS[tree_id], record_name)
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    keys = {"schema", "issue", "tree", "repository", "commit", "checkout", "hermes", "corpus", "invocation",
            "tests", "artefact_text", "run_files", "not_committed"}
    problems = exact_keys(value, keys, record_name)
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    tree = inventory["trees"].get(tree_id, {})
    exclusions = tree.get("zero_loss_exclusions", [])
    protected = expected_protected(inventory, tree_id)
    expected = {"schema": BASELINE_SCHEMA, "issue": 1355, "tree": tree_id, "repository": tree.get("repository"),
                "commit": tree.get("commit"), "hermes": {"path": HERMES, "sha256": HERMES_SHA256},
                "corpus": {"path": CORPUS, "sha256": CORPUS_SHA256}, "not_committed": ["baseline-sources/", "logs/"]}
    for key, want in expected.items():
        if value[key] != want:
            problems.append(finding(record_name, key, f"is {value[key]!r}, expected {want!r}", digest))
    invocation = {"argv": baseline_argv(protected, exclusions), "environment": environment_for(inventory, tree_id),
                  "inherited_environment": False, "interpreter": INTERPRETER, "exit": 0}
    if value["invocation"] != invocation:
        problems.append(finding(record_name, "invocation",
                                "argv, environment or exit differ from the inventory's protected set, exclusions and pins", digest))
    tests = value["tests"]
    if not (isinstance(tests, dict) and tests.get("passed") == ANCHOR_PASSES[tree_id] and tests.get("failed") == 0
            and isinstance(tests.get("summary"), str) and f"{tests.get('passed')} tests passed, 0 failed" in tests["summary"]):
        problems.append(finding(record_name, "tests", f"must record {ANCHOR_PASSES[tree_id]} passed and 0 failed", digest))
    texts = value["artefact_text"]
    if not isinstance(texts, dict) or set(texts) != set(BASELINE_TEXT) or not all(isinstance(t, str) for t in texts.values()):
        problems.append(finding(record_name, "artefact_text", f"must carry exactly {list(BASELINE_TEXT)} as text", digest))
        texts = {}
    try:
        corpus_raw = read_bytes(root, CORPUS, record_name)
    except Refusal as refusal:
        return problems + refusal.findings, {}
    if sha256(corpus_raw) != CORPUS_SHA256:
        problems.append(finding(record_name, "corpus", f"{CORPUS} no longer matches {CORPUS_SHA256}", sha256(corpus_raw)))
    found, contents = committed_files(root, f"{BASELINE_DIRS[tree_id]}/run", value["run_files"], record_name)
    problems += found
    try:
        state = json_of(contents, "state.json", record_name)
        result = json_of(contents, "result.json", record_name)
        manifest = json_of(contents, "baseline-source-manifest.json", record_name)
    except Refusal as refusal:
        return problems + refusal.findings, {}
    record_state = f"{record_name}.state"
    if not isinstance(state, dict) or not isinstance(state.get("baseline"), dict):
        return problems + [finding(record_state, "$", "is not a Hermes run state", digest)], {}
    if state.get("schema") != HERMES_RUN_SCHEMA or state.get("status") != "baseline_ready":
        problems.append(finding(record_state, "status", f"is {state.get('status')!r}; the anchor must be baseline_ready", digest))
    if result != {"schema": HERMES_RUN_SCHEMA, "skill": "hermes", "status": "baseline_ready", "exit_code": 0,
                  "run_dir": state.get("run_dir")}:
        problems.append(finding(f"{record_name}.result", "status", "result.json does not report baseline_ready with exit 0", digest))
    if state.get("protected_contracts") != protected:
        missing = sorted({c["identifier"] for c in protected} - {c.get("identifier") for c in state.get("protected_contracts") or []
                                                                  if isinstance(c, dict)})
        problems.append(finding(record_state, "protected_contracts",
                                f"must be every protected type anchored at {tree_id}; missing {missing}", digest))
    if state.get("layout_contracts") != [{**c, "protected": True} for c in protected] or state.get("asserted_no_protected_contracts") is not False:
        problems.append(finding(record_state, "layout_contracts", "must be the protected set, all protected, with no assertion of none", digest))
    if state.get("execution") != {"fuzz_seed": FUZZ_SEED, "no_match_paths": exclusions}:
        problems.append(finding(record_state, "execution", f"must pin seed {FUZZ_SEED} and exclude only {exclusions}", digest))
    gates = state.get("gates")
    if not (isinstance(gates, list) and len(gates) == 1 and isinstance(gates[0], dict) and gates[0].get("id") == 1
            and gates[0].get("status") == "passed" and gates[0].get("commands") == gate1_commands(exclusions)):
        problems.append(finding(record_state, "gates", "Gate 1 must be the only gate, passed, with the pinned forge commands", digest))
    baseline = state["baseline"]
    if baseline.get("git_head") != tree.get("commit"):
        problems.append(finding(record_state, "baseline.git_head", f"is {baseline.get('git_head')!r}, expected {tree.get('commit')}", digest))
    if baseline.get("corpus_sha256") != CORPUS_SHA256:
        problems.append(finding(record_state, "baseline.corpus_sha256", f"must be {CORPUS_SHA256}", digest))
    if baseline.get("forge_config") != TREE_COMPILER[tree_id]:
        problems.append(finding(record_state, "baseline.forge_config", f"must resolve {TREE_COMPILER[tree_id]}", digest))
    if baseline.get("source_manifest") != manifest:
        problems.append(finding(record_state, "baseline.source_manifest", "differs from the committed baseline-source-manifest.json", digest))
    if texts and baseline.get("forge_version_sha256") != sha256(texts["baseline.forge-version.txt"].encode("utf-8")):
        problems.append(finding(record_state, "baseline.forge_version_sha256", "does not hash the recorded forge version text", digest))
    if "baseline.forge-config.json" in contents and baseline.get("forge_config_sha256") != sha256(contents["baseline.forge-config.json"]):
        problems.append(finding(record_state, "baseline.forge_config_sha256", "does not hash the committed forge config", digest))
    recomputed: dict[str, str] = {}
    for name, text_value in texts.items():
        recomputed[name] = sha256(text_value.encode("utf-8"))
    corpus_copy = json.dumps(parse_json(corpus_raw, CORPUS), indent=2, ensure_ascii=False) + "\n"
    recomputed["baseline.gas-rule-corpus.json"] = sha256(corpus_copy.encode("utf-8"))
    for relative, raw_file in contents.items():
        recomputed[relative] = sha256(raw_file)
    hashes = baseline.get("artifact_hashes")
    if not isinstance(hashes, dict):
        return problems + [finding(record_state, "baseline.artifact_hashes", "missing", digest)], {}
    for relative, want in sorted(hashes.items()):
        if recomputed.get(relative) != want:
            problems.append(finding(record_state, f"baseline.artifact_hashes.{relative}",
                                    "does not recompute from the committed record", recomputed.get(relative)))
    problems += map_problems(hermes, protected, contents, record_name)
    summary = {"record": BASELINE_RECORDS[tree_id], "sha256": digest, "status": state.get("status"),
               "state_sha256": sha256(contents["state.json"]), "protected": len(protected),
               "tests_passed": tests.get("passed") if isinstance(tests, dict) else None, "access": "public", "_state": state,
               "_sealed": {**sealed_maps(protected, contents, hashes), "compiler": baseline.get("forge_config")}}
    return problems, summary


def diff_lines(text_value: str) -> tuple[list[str], list[str], list[list[str]], list[str]]:
    """Removed lines, added lines, changed lines per hunk and the files a unified diff names."""
    removed: list[str] = []
    added: list[str] = []
    hunks: list[list[str]] = []
    files: list[str] = []
    for line in text_value.splitlines():
        if line.startswith("+++ "):
            path = line[4:].split("\t")[0]
            for prefix in ("b/", "candidate/"):
                if path.startswith(prefix):
                    path = path[len(prefix):]
            if path not in files:
                files.append(path)
        elif line.startswith(("--- ", "diff --git", "index ")):
            continue
        elif line.startswith("@@"):
            hunks.append([])
        elif line.startswith("-"):
            removed.append(line[1:])
            if hunks:
                hunks[-1].append(line)
        elif line.startswith("+"):
            added.append(line[1:])
            if hunks:
                hunks[-1].append(line)
    return removed, added, hunks, files


def class_problems(attempt: dict[str, Any], record: str) -> list[str]:
    rule = RULE_HUNKS.get(attempt["rule"])
    if rule is None:
        return [finding(record, "rule", f"no hunk check is declared for {attempt['rule']!r}")]
    problems = []
    if attempt["optimisation_class"] != rule["class"]:
        problems.append(finding(record, "optimisation_class", f"{attempt['rule']} is a {rule['class']} rule"))
    removed, added, hunks, files = diff_lines(attempt["patch"])
    if not hunks:
        problems.append(finding(record, "patch", "has no hunk"))
    tests = [path for path in files if TEST_PATH.search(path)]
    if tests:
        problems.append(finding(record, "patch", f"changes test sources {tests}"))
    if any(not (path.startswith("src/") and path.endswith(".sol")) for path in files):
        problems.append(finding(record, "patch", f"changes a path outside src/*.sol: {files}"))
    if rule["deletions_only"] and added:
        problems.append(finding(record, "patch", f"{attempt['rule']} removes the overload only; {len(added)} line(s) are added"))
    for index, hunk in enumerate(hunks):
        if not any(re.search(rule["pattern"], line[1:]) for line in hunk):
            problems.append(finding(record, f"patch.hunk[{index}]", f"changes nothing the {attempt['rule']} candidate names; the classes are mixed"))
        if rule["line"] and any(not re.match(rule["line"], line[1:]) for line in hunk):
            problems.append(finding(record, f"patch.hunk[{index}]", "changes a line that is not a storage declaration or its comment"))
    if re.search(r"\bunchecked\b|\bassembly\b", "\n".join(added)):
        problems.append(finding(record, "patch", "adds unchecked or assembly code outside its class"))
    hermes_diff = attempt["candidate_solidity_diff"]
    if isinstance(hermes_diff, str):
        h_removed, h_added, _, h_files = diff_lines(hermes_diff)
        if sorted(h_removed) != sorted(removed) or sorted(h_added) != sorted(added) or sorted(h_files) != sorted(files):
            problems.append(finding(record, "candidate_solidity_diff", "Hermes's recorded diff and the patch change different lines"))
    elif attempt["gate_reached"] != 2:
        problems.append(finding(record, "candidate_solidity_diff", "is missing although Gate 2 read the candidate"))
    return problems


def flag_value(argv: list[Any], flag: str) -> Any:
    """The operand after the first `flag` in `argv`, or None when the flag or its operand is absent."""
    if flag not in argv:
        return None
    index = argv.index(flag)
    return argv[index + 1] if index + 1 < len(argv) else None


def validate_attempt(root: Path, directory: str, attempt: Any, kind: str, inventory: dict[str, Any],
                     anchors: dict[str, dict[str, Any]], hermes: dict[str, Any], digest: str) -> tuple[list[str], dict[str, Any]]:
    record = f"rejection.{kind}.attempt"
    optional = {"hermes_method_identifiers_diff", "hermes_storage_layout_diff", "method_identifier_check"}
    problems = exact_keys(attempt, ATTEMPT_KEYS, record, optional)
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    record = f"rejection.{kind}.{attempt['id']}"
    if not (isinstance(attempt["id"], str) and SLUG.match(attempt["id"])):
        return [finding(record, "id", "must be a slug", digest)], {}
    tree_id = attempt["tree"]
    tree = inventory["trees"].get(tree_id)
    if tree is None or tree_id not in TREE_COMPILER:
        return [finding(record, "tree", f"{tree_id!r} is not a Hermes tree of the inventory", digest)], {}
    protected = expected_protected(inventory, tree_id)
    exclusions = tree["zero_loss_exclusions"]
    if (attempt["repository"], attempt["commit"]) != (tree["repository"], tree["commit"]):
        problems.append(finding(record, "commit", f"must be {tree['repository']} at {tree['commit']}", digest))
    intended = attempt["intended_contract"]
    if intended not in {c["identifier"] for c in protected}:
        problems.append(finding(record, "intended_contract", f"{intended!r} is not a protected contract anchored at {tree_id}", digest))
    for field in ("patch", "rule", "optimisation_class"):
        if not text(attempt[field], 200_000):
            return problems + [finding(record, field, "must be text", digest)], {}
    if attempt["patch_sha256"] != sha256(attempt["patch"].encode("utf-8")):
        problems.append(finding(record, "patch_sha256", "does not hash the recorded patch", sha256(attempt["patch"].encode("utf-8"))))
    problems += [p + f" digest={digest}" for p in class_problems(attempt, record)]
    invocation = attempt["invocation"]
    if not isinstance(invocation, dict) or invocation.get("baseline_argv") != baseline_argv(protected, exclusions) \
            or invocation.get("environment") != environment_for(inventory, tree_id) \
            or invocation.get("inherited_environment") is not False or invocation.get("interpreter") != INTERPRETER:
        problems.append(finding(record, "invocation", "baseline argv or environment differ from the tree's protected set and pins", digest))
    verify = invocation.get("verify_argv") if isinstance(invocation, dict) else None
    if not (isinstance(verify, list) and verify[:5] == ["python3", HERMES, "verify", "--run-dir", "<attempt run directory>"]
            and flag_value(verify, "--rule") == attempt["rule"]
            and flag_value(verify, "--optimisation-class") == attempt["optimisation_class"]
            and "--attest-single-class" in verify and "--allow-unprotected-layout-change" not in verify):
        problems.append(finding(record, "invocation.verify_argv", "must name the record's rule and class, attest one class and declare no layout change", digest))
    restoration = attempt["restoration"]
    if not (isinstance(restoration, dict) and restoration.get("status_after") == "" and restoration.get("head_after") == tree["commit"]):
        problems.append(finding(record, "restoration", f"the copy must show a clean status at {tree['commit']} afterwards", digest))
    found, contents = committed_files(root, f"{directory}/attempts/{attempt['id']}/run", attempt["run_files"], record)
    problems += found
    try:
        state = json_of(contents, "state.json", record)
        result = json_of(contents, "result.json", record)
    except Refusal as refusal:
        return problems + refusal.findings, {}
    if not isinstance(state, dict) or not isinstance(result, dict) or not isinstance(state.get("baseline"), dict):
        return problems + [finding(record, "state.json", "is not a Hermes run state", digest)], {}
    gate = result.get("failed_gate")
    exit_code = result.get("exit_code")
    if (attempt["gate_reached"], attempt["verify_exit"], attempt["reason"]) != (gate, exit_code, result.get("reason")):
        problems.append(finding(record, "gate_reached", "gate, exit and reason differ from Hermes's result.json", digest))
    output = attempt["output"]
    stderr = output.get("verify_stderr_last_line") if isinstance(output, dict) else None
    if stderr != f"Hermes rejected at Gate {gate}: {result.get('reason')}":
        problems.append(finding(record, "output.verify_stderr_last_line", "does not carry Hermes's rejection line", digest))
    if attempt["baseline_exit"] != 0 or state.get("schema") != HERMES_RUN_SCHEMA or state.get("status") != "rejected" \
            or result.get("status") != "rejected" or state.get("result") != result:
        problems.append(finding(record, "state.json", "the attempt's own Gate 1 must have exited 0 and verify must have rejected", digest))
    baseline = state["baseline"]
    sealed_hashes = baseline.get("artifact_hashes")
    if not isinstance(sealed_hashes, dict):
        return problems + [finding(record, "state.baseline.artifact_hashes", "missing", digest)], {}
    for relative, raw_file in sorted(contents.items()):
        if relative in sealed_hashes and sealed_hashes[relative] != sha256(raw_file):
            problems.append(finding(record, relative, "is not the map the attempt's Gate 1 sealed", sha256(raw_file)))
    allowed = {"run"} | ({"supplementary"} if "method_identifier_check" in attempt else set())
    try:
        beside = list_directory(root, f"{directory}/attempts/{attempt['id']}", record)
    except Refusal as refusal:
        return problems + refusal.findings, {}
    for extra in sorted(set(beside) - allowed):
        problems.append(finding(record, "run_files", f"{directory}/attempts/{attempt['id']}/{extra} is committed but not declared", digest))
    if baseline.get("git_head") != tree["commit"] or baseline.get("corpus_sha256") != CORPUS_SHA256 \
            or baseline.get("forge_config") != TREE_COMPILER[tree_id]:
        problems.append(finding(record, "state.baseline", "commit, corpus or compiler differ from the tree's pins", digest))
    if state.get("protected_contracts") != protected or state.get("execution") != {"fuzz_seed": FUZZ_SEED, "no_match_paths": exclusions}:
        problems.append(finding(record, "state.protected_contracts", "the attempt's Gate 1 must seal the tree's protected set, seed and exclusions", digest))
    if tree_id in anchors:
        anchor = anchors[tree_id]["baseline"]
        maps = {k: v for k, v in anchor.get("artifact_hashes", {}).items() if k.startswith(("storage-layout/", "method-identifiers/"))}
        mine = {k: v for k, v in baseline.get("artifact_hashes", {}).items() if k.startswith(("storage-layout/", "method-identifiers/"))}
        if maps != mine or any(anchor.get(k) != baseline.get(k) for k in ("forge_version_sha256", "forge_config_sha256", "source_manifest")):
            problems.append(finding(record, "state.baseline", "the copy's Gate 1 maps, toolchain or sources differ from the sealed anchor", digest))
    passed = [g.get("id") for g in state.get("gates", []) if isinstance(g, dict) and g.get("status") == "passed"]
    candidate = state.get("candidate") if isinstance(state.get("candidate"), dict) else {}
    candidate_rule = candidate.get("rule") if isinstance(candidate.get("rule"), dict) else {}
    if gate is not None and gate > 2:
        _, _, _, files = diff_lines(attempt["patch"])
        if candidate_rule.get("id") != attempt["rule"] or candidate.get("optimisation_class") != attempt["optimisation_class"] \
                or sorted(candidate.get("changed_files", [])) != sorted(files) or candidate.get("single_class_attested") is not True:
            problems.append(finding(record, "state.candidate", "Hermes's Gate 2 record names another rule, class or file set", digest))
    reached_gate5 = passed == [1, 2, 3, 4] and gate == 5 and exit_code == 50 and attempt["verify_exit"] == 50
    names_intended = result.get("reason") == f"{GATE5_PREFIX[kind]}: {intended}"
    if reached_gate5:
        family = GATE5_FAMILY[kind]
        label = intended.rsplit(":", 1)[1]
        before = f"{family}/{label}.before.json"
        after = f"{family}/{label}.after.json"
        if before not in contents or after not in contents:
            problems.append(finding(record, "run_files", f"a Gate 5 rejection must commit {before} and {after}", digest))
        else:
            if sealed_hashes.get(before) != sha256(contents[before]):
                problems.append(finding(record, before, "is not the map the attempt's Gate 1 sealed", sha256(contents[before])))
            recorded = attempt.get(f"hermes_{family.replace('-', '_')}_diff")
            recomputed = "".join(difflib.unified_diff(contents[before].decode("utf-8").splitlines(keepends=True),
                                                      contents[after].decode("utf-8").splitlines(keepends=True),
                                                      fromfile=f"{label}.before.json", tofile=f"{label}.after.json"))
            if not recomputed or recorded != recomputed:
                problems.append(finding(record, f"hermes_{family.replace('-', '_')}_diff",
                                        "does not recompute from the committed before and after maps", sha256(contents[after])))
    if "method_identifier_check" in attempt:
        problems += method_check_problems(root, f"{directory}/attempts/{attempt['id']}", attempt["method_identifier_check"],
                                          baseline, protected, record, digest)
    sealed = tree_id in anchors
    status = "rejected-at-gate-5" if reached_gate5 and names_intended and sealed else f"stopped-at-gate-{gate}"
    return problems, {"id": attempt["id"], "tree": tree_id, "status": status, "gate": gate, "exit": exit_code,
                      "reason": result.get("reason"), "names_intended": names_intended, "sealed_anchor": sealed}


def method_check_problems(root: Path, directory: str, check: Any, baseline: dict[str, Any],
                          protected: list[dict[str, str]], record: str, digest: str) -> list[str]:
    """A method-map comparison run beside Hermes after its Gate 5 stopped at the layout.

    Recomputed: the committed after map's digest; the committed before map's
    bytes, at `run/method-identifiers/<label>.before.json`, against the attempt's
    own Gate 1 `artifact_hashes`; and equality of the two maps. The after map must
    sit at `supplementary/<label>.methods.after.json`. The argv and environment
    are recorded only.
    """
    sub = f"{record}.method_identifier_check"
    problems = exact_keys(check, METHOD_CHECK_KEYS, sub)
    if problems:
        return [p + f" digest={digest}" for p in problems]
    labels = {c["identifier"]: c["label"] for c in protected}
    label = labels.get(check["contract"])
    if label is None:
        return [finding(sub, "contract", f"{check['contract']!r} is not a protected contract of the tree", digest)]
    before_key = f"method-identifiers/{label}.before.json"
    hashes = baseline.get("artifact_hashes") if isinstance(baseline.get("artifact_hashes"), dict) else {}
    sealed = hashes.get(before_key)
    if not (isinstance(check["before"], dict) and check["before"].get("path") == f"run/{before_key}"
            and sealed is not None and check["before"].get("sha256") == sealed):
        problems.append(finding(sub, "before", f"must name run/{before_key}, the map the attempt's Gate 1 sealed", digest))
    after = check["after"]
    after_path = f"supplementary/{label}.methods.after.json"
    if not (isinstance(after, dict) and after.get("path") == after_path and isinstance(after.get("sha256"), str)):
        return problems + [finding(sub, "after", f"must name {after_path} and its sha256", digest)]
    try:
        raw_after = read_bytes(root, f"{directory}/{after['path']}", sub)
        raw_before = read_bytes(root, f"{directory}/run/{before_key}", sub)
    except Refusal as refusal:
        return problems + refusal.findings
    if sha256(raw_before) != sealed:
        problems.append(finding(sub, "before", f"the committed run/{before_key} is not the map the attempt's Gate 1 sealed", sha256(raw_before)))
    if sha256(raw_after) != after["sha256"]:
        problems.append(finding(sub, "after.sha256", "does not hash the committed after map", sha256(raw_after)))
    if not check_methods(parse_json(raw_after, sub)):
        problems.append(finding(sub, "after", "is not a method map", sha256(raw_after)))
    if check["equal"] is not (raw_before == raw_after):
        problems.append(finding(sub, "equal", f"records {check['equal']!r} but the committed maps say {raw_before == raw_after}", digest))
    argv = check["argv"]
    if not (isinstance(argv, list) and argv[:2] == ["forge", "inspect"] and check["contract"] in argv and "methodIdentifiers" in argv):
        problems.append(finding(sub, "argv", "must be the forge inspect methodIdentifiers command for the contract", digest))
    return problems


def validate_rejection(root: Path, kind: str, inventory: dict[str, Any], anchors: dict[str, dict[str, Any]],
                       hermes: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Every recorded attempt of one Gate 5 demonstration.

    Recomputed: every committed run file digest, each committed map against the
    attempt's own Gate 1 `artifact_hashes`, the patch digest, the patch's
    files, hunks and test-path check against Hermes's own diff, each hunk's rule
    token check, the Gate 5 map diff from the committed before and after maps,
    and, for an attempt on an anchor this step seals, the copy's Gate 1 maps,
    toolchain and sources against that sealed anchor. Checked against Hermes's
    committed state and result: the gates passed, the gate reached, the verify
    exit and the reason. A selected attempt must run on a sealed anchor, and a
    malformed attempt refuses by name rather than raising.
    Recorded only: the baseline exit, the output lines, the stdout digest, the
    Gate 3 snapshot moves and the restoration status, which no committed or
    retained byte backs.
    """
    relative = REJECTION_RECORDS[kind]
    record_name = f"rejection.{kind}"
    try:
        value, raw = read_json(root, relative, record_name)
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    keys = {"schema", "issue", "kind", "attempts", "selected", "blocker"}
    problems = exact_keys(value, keys, record_name, {"study_order"} if kind == "layout" else set())
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    if (value["schema"], value["issue"], value["kind"]) != (REJECTION_SCHEMA, 1355, kind):
        problems.append(finding(record_name, "schema", f"must be {REJECTION_SCHEMA} for issue 1355 and kind {kind}", digest))
    if not isinstance(value["attempts"], list) or not value["attempts"]:
        return problems + [finding(record_name, "attempts", "must record at least one attempt", digest)], {}
    results = []
    ids: set[str] = set()
    for index, attempt in enumerate(value["attempts"]):
        try:
            found, outcome = validate_attempt(root, str(PurePosixPath(relative).parent), attempt, kind, inventory,
                                              anchors, hermes, digest)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
            found, outcome = [finding(record_name, f"attempts[{index}]",
                                      f"is malformed: {type(exc).__name__}: {exc}", digest)], {}
        problems += found
        if outcome:
            if outcome["id"] in ids:
                problems.append(finding(record_name, "attempts", f"{outcome['id']} is recorded twice", digest))
            ids.add(outcome["id"])
            results.append(outcome)
    reached = [r["id"] for r in results if r["status"] == "rejected-at-gate-5"]
    selected = value["selected"]
    if selected is None:
        if reached:
            problems.append(finding(record_name, "selected", f"is null although {reached[0]} reached Gate 5", digest))
        if not text(value["blocker"]):
            problems.append(finding(record_name, "blocker", "a record with no selected attempt must state its blocker", digest))
    elif selected not in reached:
        problems.append(finding(record_name, "selected", f"{selected!r} did not exit 50 at Gate 5 naming its intended contract "
                                "on a sealed anchor", digest))
    elif value["blocker"] is not None:
        problems.append(finding(record_name, "blocker", "must be null once an attempt reached Gate 5", digest))
    if kind == "layout":
        order = [str(a.get("study_order")) for a in value["attempts"] if isinstance(a, dict)]
        if order != sorted(order) or value.get("study_order") != LAYOUT_ORDER:
            problems.append(finding(record_name, "study_order", "attempts must follow the study's candidate order", digest))
    summary = {"record": relative, "sha256": digest, "attempts": results, "selected": selected,
               "blocker": value["blocker"]}
    return problems, summary


LAYOUT_ORDER = [
    {"item": "1", "candidate": "STO-18 on Wildcat4626Wrapper's constructor-only _name and _symbol with a retained fallback"},
    {"item": "2", "candidate": "any co-accessed field pair in a protected type"},
]


MAP_PREFIXES = ("storage-layout/", "method-identifiers/")


def map_names(protected: list[dict[str, str]]) -> list[str]:
    names = []
    for contract in protected:
        label = contract["label"]
        names += [f"storage-layout/{label}.before.json", f"storage-layout/{label}.before.raw.json",
                  f"method-identifiers/{label}.before.json"]
    return sorted(names)


def sealed_maps(protected: list[dict[str, str]], contents: dict[str, bytes], hashes: dict[str, Any]) -> dict[str, Any]:
    """The parts of a sealed Gate 1 an equivalence record compares with."""
    return {"protected": [c["identifier"] for c in protected],
            "maps": {k: v for k, v in contents.items() if k.startswith(MAP_PREFIXES)},
            "hashes": {k: v for k, v in hashes.items() if isinstance(k, str) and k.startswith(MAP_PREFIXES)}}


def map_problems(hermes: dict[str, Any], protected: list[dict[str, str]], contents: dict[str, bytes],
                 record_name: str) -> list[str]:
    """Each protected contract's committed maps exist, and the layout is Hermes's canonical form of its raw output."""
    problems = []
    for contract in protected:
        label = contract["label"]
        for relative in (f"storage-layout/{label}.before.json", f"storage-layout/{label}.before.raw.json",
                         f"method-identifiers/{label}.before.json"):
            if relative not in contents:
                problems.append(finding(record_name, f"run_files.{relative}", f"the protected contract {contract['identifier']} has no committed map"))
        before = f"storage-layout/{label}.before.json"
        raw_layout = f"storage-layout/{label}.before.raw.json"
        if before in contents and raw_layout in contents:
            try:
                if canonical_layout_text(hermes, contents[raw_layout], f"{record_name}:{raw_layout}").encode("utf-8") != contents[before]:
                    problems.append(finding(record_name, before, "is not Hermes's canonical form of the raw inspector output", sha256(contents[before])))
            except Refusal as refusal:
                problems += refusal.findings
        methods = f"method-identifiers/{label}.before.json"
        if methods in contents:
            try:
                if not check_methods(parse_json(contents[methods], methods)):
                    problems.append(finding(record_name, methods, "is not a method map", sha256(contents[methods])))
            except Refusal as refusal:
                problems += refusal.findings
    return problems


def state_projection(state: Any) -> dict[str, Any]:
    """The fields of a Hermes Gate 1 state that a restricted anchor's public record carries."""
    state = state if isinstance(state, dict) else {}
    baseline = state.get("baseline") if isinstance(state.get("baseline"), dict) else {}
    hashes = baseline.get("artifact_hashes") if isinstance(baseline.get("artifact_hashes"), dict) else {}
    gates = state.get("gates") if isinstance(state.get("gates"), list) else []
    return {
        "schema": state.get("schema"),
        "status": state.get("status"),
        "git_head": baseline.get("git_head"),
        "corpus_sha256": baseline.get("corpus_sha256"),
        "forge_config": baseline.get("forge_config"),
        "execution": state.get("execution"),
        "protected_contracts": state.get("protected_contracts"),
        "layout_contracts": state.get("layout_contracts"),
        "asserted_no_protected_contracts": state.get("asserted_no_protected_contracts"),
        "gates": [{"id": g.get("id"), "status": g.get("status"), "commands": g.get("commands")}
                  for g in gates if isinstance(g, dict)],
        "map_hashes": {k: v for k, v in sorted(hashes.items()) if isinstance(k, str) and k.startswith(MAP_PREFIXES)},
    }


PROJECTION_KEYS = set(state_projection({}))


def validate_restricted_baseline(root: Path, inventory: dict[str, Any], hermes: dict[str, Any],
                                 tree_id: str) -> tuple[list[str], dict[str, Any]]:
    """The public record of one private-repository anchor Gate 1 (`fee-ac73` or `rp-5d7f`).

    The public directory holds only each protected contract's canonical layout,
    raw layout and method map. Recomputed from committed bytes: every map digest,
    each canonical layout from its raw output through Hermes's own canonicaliser,
    and each `state.map_hashes` entry against the committed map. Checked against
    the inventory and study: commit, protected set, seed, exclusions, compiler,
    environment, argv, Gate 1 commands, status and pass count. Recorded only
    until the retained run is re-verified by `sealed-coverage`: the rest of the
    `state` projection and the `state.json` and `result.json` digests. A withheld
    Hermes file in the public directory is refused by name.
    """
    record_name = f"baseline.{tree_id}"
    try:
        value, raw = read_json(root, BASELINE_RECORDS[tree_id], record_name)
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    keys = {"schema", "issue", "tree", "repository", "commit", "access", "hermes", "corpus", "invocation",
            "tests", "state", "restricted", "run_files", "withheld"}
    problems = exact_keys(value, keys, record_name)
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    tree = inventory["trees"].get(tree_id, {})
    exclusions = tree.get("zero_loss_exclusions", [])
    protected = expected_protected(inventory, tree_id)
    expected = {"schema": RESTRICTED_BASELINE_SCHEMA, "issue": 1355, "tree": tree_id, "repository": tree.get("repository"),
                "commit": tree.get("commit"), "access": "restricted", "hermes": {"path": HERMES, "sha256": HERMES_SHA256},
                "corpus": {"path": CORPUS, "sha256": CORPUS_SHA256}, "withheld": WITHHELD}
    for key, want in expected.items():
        if value[key] != want:
            problems.append(finding(record_name, key, f"is {value[key]!r}, expected {want!r}", digest))
    if tree.get("access") != "restricted":
        problems.append(finding(record_name, "access", f"inventory tree {tree_id} is not restricted", digest))
    invocation = {"argv": baseline_argv(protected, exclusions), "environment": environment_for(inventory, tree_id),
                  "inherited_environment": False, "interpreter": INTERPRETER, "exit": 0}
    if value["invocation"] != invocation:
        problems.append(finding(record_name, "invocation",
                                "argv, environment or exit differ from the inventory's protected set, exclusions and pins", digest))
    tests = value["tests"]
    if not (isinstance(tests, dict) and set(tests) == {"passed", "failed", "skipped"}
            and tests["passed"] == ANCHOR_PASSES[tree_id] and tests["failed"] == 0 and is_int(tests["skipped"])):
        problems.append(finding(record_name, "tests", f"must record {ANCHOR_PASSES[tree_id]} passed and 0 failed as counts", digest))
    state = value["state"]
    record_state = f"{record_name}.state"
    found = exact_keys(state, PROJECTION_KEYS, record_state)
    if found:
        return problems + [p + f" digest={digest}" for p in found], {}
    want_state = {
        "schema": HERMES_RUN_SCHEMA, "status": "baseline_ready", "git_head": tree.get("commit"),
        "corpus_sha256": CORPUS_SHA256, "forge_config": TREE_COMPILER.get(tree_id),
        "execution": {"fuzz_seed": FUZZ_SEED, "no_match_paths": exclusions}, "protected_contracts": protected,
        "layout_contracts": [{**c, "protected": True} for c in protected], "asserted_no_protected_contracts": False,
        "gates": [{"id": 1, "status": "passed", "commands": gate1_commands(exclusions)}],
    }
    for key, want in want_state.items():
        if state[key] != want:
            problems.append(finding(record_state, key, f"is {state[key]!r}, expected {want!r}", digest))
    restricted = value["restricted"]
    found = exact_keys(restricted, {"path", "state_sha256", "result_sha256"}, f"{record_name}.restricted")
    if found:
        problems += [p + f" digest={digest}" for p in found]
    elif not (isinstance(restricted["state_sha256"], str) and HEX64.match(restricted["state_sha256"])
              and isinstance(restricted["result_sha256"], str) and HEX64.match(restricted["result_sha256"])
              and restricted["path"] == f"{RESTRICTED_RUNS}/{restricted['state_sha256']}"):
        problems.append(finding(f"{record_name}.restricted", "path",
                                f"must be {RESTRICTED_RUNS}/<state_sha256> with both digests", digest))
    declared = value["run_files"]
    wanted = map_names(protected)
    if isinstance(declared, dict):
        for relative in sorted(set(declared) - set(wanted)):
            withheld = any(relative == item or relative.startswith(item) or PurePosixPath(relative).name == item
                           for item in WITHHELD)
            detail = "is a withheld Hermes file of a private repository" if withheld else "is not a protected contract's map"
            problems.append(finding(record_name, f"run_files.{relative}", f"{detail}; the public tree carries maps, counts and digests only", digest))
        declared = {k: v for k, v in declared.items() if k in wanted}
    directory = f"{BASELINE_DIRS[tree_id]}/run"
    found, contents = committed_files(root, directory, declared, record_name)
    for item in found:
        name = item.split(f"{directory}/", 1)[-1].split(" ", 1)[0]
        if "is committed but not declared" in item and any(
                name == w or name.startswith(w) or PurePosixPath(name).name == w for w in WITHHELD):
            problems.append(finding(record_name, "run_files", f"{directory}/{name} is a withheld Hermes file of a private repository", digest))
        else:
            problems.append(item)
    for relative in wanted:
        if relative not in (value["run_files"] if isinstance(value["run_files"], dict) else {}):
            problems.append(finding(record_name, f"run_files.{relative}", "a protected contract's map is not declared", digest))
    hashes = state["map_hashes"]
    canonical_names = [name for name in wanted if not name.endswith(".raw.json")]
    if not isinstance(hashes, dict) or sorted(hashes) != canonical_names:
        problems.append(finding(record_state, "map_hashes", f"must name exactly {canonical_names}", digest))
        hashes = {}
    for relative, want in sorted(hashes.items()):
        if relative in contents and sha256(contents[relative]) != want:
            problems.append(finding(record_state, f"map_hashes.{relative}", "does not hash the committed map", sha256(contents[relative])))
    problems += map_problems(hermes, protected, contents, record_name)
    summary = {"record": BASELINE_RECORDS[tree_id], "sha256": digest, "status": state["status"],
               "state_sha256": restricted.get("state_sha256") if isinstance(restricted, dict) else None,
               "protected": len(protected), "tests_passed": tests.get("passed") if isinstance(tests, dict) else None,
               "access": "restricted", "_sealed": {**sealed_maps(protected, contents, hashes), "compiler": state["forge_config"]},
               "_record": value}
    return problems, summary


def verify_restricted_payload(root: Path, tree_id: str, record: dict[str, Any], maps: dict[str, bytes]) -> list[str]:
    """Re-verify a restricted anchor's retained Hermes run against its public record.

    Recomputed from the retained bytes: the `state.json` and `result.json`
    digests; the state projection the public record carries; every entry of
    Hermes's `artifact_hashes`; each committed map against the retained file;
    the source manifest against every retained `baseline-sources/` copy; the
    forge config and version digests; the compiler the config resolves; and the
    pass count in the Gate 1 test log.
    """
    record_name = f"restricted.{tree_id}"
    restricted = record["restricted"]
    base = restricted["path"]
    try:
        state_raw = read_bytes(root, f"{base}/state.json", record_name)
        result_raw = read_bytes(root, f"{base}/result.json", record_name)
    except Refusal as refusal:
        return [item + " (the retained run is not present)" for item in refusal.findings]
    problems = []
    if sha256(state_raw) != restricted["state_sha256"]:
        return [finding(record_name, "state_sha256", f"{base}/state.json does not match the public record", sha256(state_raw))]
    if sha256(result_raw) != restricted["result_sha256"]:
        problems.append(finding(record_name, "result_sha256", f"{base}/result.json does not match the public record", sha256(result_raw)))
    state = parse_json(state_raw, record_name)
    result = parse_json(result_raw, record_name)
    if state_projection(state) != record["state"]:
        problems.append(finding(record_name, "state", "the retained state.json differs from the public record's projection", sha256(state_raw)))
    if not isinstance(state, dict) or result != {"schema": HERMES_RUN_SCHEMA, "skill": "hermes", "status": "baseline_ready",
                                                  "exit_code": 0, "run_dir": state.get("run_dir")}:
        problems.append(finding(record_name, "result", "result.json does not report baseline_ready with exit 0", sha256(result_raw)))
        return problems
    baseline = state.get("baseline") if isinstance(state.get("baseline"), dict) else {}
    hashes = baseline.get("artifact_hashes")
    if not isinstance(hashes, dict) or not hashes:
        return problems + [finding(record_name, "artifact_hashes", "missing", sha256(state_raw))]
    retained: dict[str, bytes] = {}
    for relative, want in sorted(hashes.items()):
        try:
            retained[relative] = read_bytes(root, f"{base}/{relative}", record_name)
        except Refusal as refusal:
            problems += refusal.findings
            continue
        if sha256(retained[relative]) != want:
            problems.append(finding(record_name, f"artifact_hashes.{relative}", "does not recompute from the retained file", sha256(retained[relative])))
    for relative, committed in sorted(maps.items()):
        try:
            if read_bytes(root, f"{base}/{relative}", record_name) != committed:
                problems.append(finding(record_name, relative, "the committed map differs from the retained file", sha256(committed)))
        except Refusal as refusal:
            problems += refusal.findings
    manifest = baseline.get("source_manifest")
    if not isinstance(manifest, dict) or not manifest or len(manifest) > MAX_TREE_FILES:
        problems.append(finding(record_name, "source_manifest", "missing or over the file bound", sha256(state_raw)))
    else:
        if "baseline-source-manifest.json" in retained and parse_json(retained["baseline-source-manifest.json"], record_name) != manifest:
            problems.append(finding(record_name, "source_manifest", "differs from the retained baseline-source-manifest.json", sha256(state_raw)))
        for relative, want in sorted(manifest.items()):
            try:
                copy = read_bytes(root, f"{base}/baseline-sources/{relative}", record_name)
            except Refusal as refusal:
                problems += refusal.findings
                continue
            if sha256(copy) != want:
                problems.append(finding(record_name, f"source_manifest.{relative}", "does not hash the retained source copy", sha256(copy)))
    config = retained.get("baseline.forge-config.json")
    if config is None or sha256(config) != baseline.get("forge_config_sha256"):
        problems.append(finding(record_name, "forge_config_sha256", "does not hash the retained forge config", sha256(config or b"")))
    else:
        document = parse_json(config, record_name)
        resolved = {"solc": document.get("solc"), "evm_version": document.get("evm_version"), "via_ir": bool(document.get("via_ir"))} \
            if isinstance(document, dict) else None
        if resolved != TREE_COMPILER[tree_id] or baseline.get("forge_config") != resolved:
            problems.append(finding(record_name, "forge_config", f"the retained config resolves {resolved}, the study pins {TREE_COMPILER[tree_id]}", sha256(config)))
    version = retained.get("baseline.forge-version.txt")
    if version is None or sha256(version) != baseline.get("forge_version_sha256") or FORGE["commit"].encode() not in version:
        problems.append(finding(record_name, "forge_version_sha256", f"the retained forge version is not Forge {FORGE['version']} at {FORGE['commit']}", sha256(version or b"")))
    try:
        log = read_bytes(root, f"{base}/logs/gate1.forge-test.log", record_name).decode("utf-8", errors="replace")
    except Refusal as refusal:
        return problems + refusal.findings
    counts = re.findall(r"^Ran \d+ test suites? .*?(\d+) tests passed, (\d+) failed, (\d+) skipped", log, re.M)
    tests = record["tests"]
    if not counts or tuple(int(n) for n in counts[-1]) != (tests["passed"], tests["failed"], tests["skipped"]):
        problems.append(finding(record_name, "tests", f"the retained Gate 1 test log does not report {tests['passed']} passed", sha256(log.encode())))
    return problems


EXCLUSION_ROW_KEYS = {"tree", "commit", "file", "environment", "inherited_environment", "excluded", "unexcluded", "status_after"}
EXCLUSION_RUN_KEYS = {"argv", "exit", "passed", "failed", "skipped", "summary"}


def validate_exclusion_evidence(root: Path, inventory: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """Each anchor exclusion runs zero passing tests, and excluding it drops none.

    Checked: one row per anchor exclusion, at the tree's commit, pins and seed;
    the excluded file's own run passed zero tests; the unexcluded suite passed
    exactly the anchor's sealed count; each summary line states its counts.
    Recorded only: the counts and exit codes, which come from Forge runs on
    disposable copies that no committed or retained byte backs.
    """
    record_name = "exclusions"
    try:
        value, raw = read_json(root, EXCLUSIONS_RECORD, record_name)
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    problems = exact_keys(value, {"schema", "issue", "forge", "rows"}, record_name)
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    if (value["schema"], value["issue"], value["forge"]) != (EXCLUSIONS_SCHEMA, 1355, FORGE):
        problems.append(finding(record_name, "schema", f"must be {EXCLUSIONS_SCHEMA} for issue 1355 under Forge {FORGE}", digest))
    wanted = {(tree, path) for tree in BASELINE_TREES for path in inventory["trees"][tree]["zero_loss_exclusions"]}
    seen: set[tuple[str, str]] = set()
    rows = value["rows"] if isinstance(value["rows"], list) else []
    if not isinstance(value["rows"], list):
        problems.append(finding(record_name, "rows", "expected a list", digest))
    for index, row in enumerate(rows):
        record = f"{record_name}.rows[{index}]"
        found = exact_keys(row, EXCLUSION_ROW_KEYS, record)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        key = (row["tree"], row["file"])
        record = f"{record_name}.{row['tree']}:{row['file']}"
        if key not in wanted or key in seen:
            problems.append(finding(record, "file", "is not an anchor's zero-loss exclusion, or is recorded twice", digest))
            continue
        seen.add(key)
        tree = inventory["trees"][row["tree"]]
        if row["commit"] != tree["commit"] or row["environment"] != environment_for(inventory, row["tree"]) \
                or row["inherited_environment"] is not False or row["status_after"] != "":
            problems.append(finding(record, "environment", "commit, pins, environment or restoration differ from the tree", digest))
        for side, argv in (("excluded", ["forge", "test", "--match-path", row["file"], "--fuzz-seed", FUZZ_SEED]),
                           ("unexcluded", ["forge", "test", "--fuzz-seed", FUZZ_SEED])):
            run = row[side]
            found = exact_keys(run, EXCLUSION_RUN_KEYS, f"{record}.{side}")
            if found:
                problems += [p + f" digest={digest}" for p in found]
                continue
            if run["argv"] != argv or not all(is_int(run[k]) for k in ("exit", "passed", "failed", "skipped")) \
                    or not isinstance(run["summary"], str) \
                    or f"{run['passed']} tests passed, {run['failed']} failed, {run['skipped']} skipped" not in run["summary"]:
                problems.append(finding(f"{record}.{side}", "argv", f"must be {argv} with counts its summary states", digest))
                continue
            if side == "excluded" and run["passed"] != 0:
                problems.append(finding(f"{record}.excluded", "passed",
                                        f"the excluded file runs {run['passed']} passing tests; only a zero-loss file may be excluded", digest))
            if side == "unexcluded" and run["passed"] != ANCHOR_PASSES[row["tree"]]:
                problems.append(finding(f"{record}.unexcluded", "passed",
                                        f"the unexcluded suite passes {run['passed']} but the sealed Gate 1 passes "
                                        f"{ANCHOR_PASSES[row['tree']]}; the exclusion drops passing tests", digest))
    for tree, path in sorted(wanted - seen):
        problems.append(finding(f"{record_name}.{tree}:{path}", "file", "the exclusion has no zero-loss evidence", digest))
    return problems, {"record": EXCLUSIONS_RECORD, "sha256": digest, "rows": len(seen)}


EQUIVALENCE_KEYS = {"schema", "issue", "canonicaliser", "forge", "captures", "types"}
EQUIVALENCE_CAPTURE_KEYS = {"tree", "repository", "commit", "checkout", "environment", "inherited_environment", "interpreter",
                "forge_version", "forge_config_sha256", "compiler", "status_after", "head_after"}
EQUIVALENT_KEYS = {"type", "deployed_state", "identifier", "anchor", "anchor_identifier", "argv", "files", "anchor_maps"}


def validate_equivalence(root: Path, inventory: dict[str, Any], hermes: dict[str, Any],
                         sealed: dict[str, dict[str, Any]]) -> tuple[list[str], dict[str, Any]]:
    """Each equivalence type's maps at its deployed state are byte-equal to its sealed anchor's.

    Recomputed from committed bytes: every file digest; each canonical layout
    from its raw output through Hermes's own canonicaliser; the byte comparison
    of layout and method map with the anchor's committed Gate 1 files; the
    anchor files' digests against the anchor's sealed hashes; and each map's
    digest against the profile-invariance record at the same deployed state.
    Checked against the inventory: the deployed commit, identifier, anchor,
    pins, and a compiler equal to the anchor's. Recorded only: the capture's
    forge version text, forge config digest, restoration status and submodule
    list, which no committed or retained byte backs. A type whose anchor is
    not sealed is refused by name.
    """
    record_name = "equivalence"
    try:
        value, raw = read_json(root, EQUIVALENCE_RECORD, record_name)
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    problems = exact_keys(value, EQUIVALENCE_KEYS, record_name)
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    if (value["schema"], value["issue"]) != (EQUIVALENCE_SCHEMA, 1355):
        problems.append(finding(record_name, "schema", f"must be {EQUIVALENCE_SCHEMA} for issue 1355", digest))
    if value["canonicaliser"] != {"path": HERMES, "function": "canonical_storage_layout", "sha256": HERMES_SHA256}:
        problems.append(finding(record_name, "canonicaliser", "must name Hermes's canonical_storage_layout at the pinned hermes.py", digest))
    if value["forge"] != FORGE:
        problems.append(finding(record_name, "forge", f"is {value['forge']!r}, the study pins {FORGE!r}", digest))
    trees = inventory["trees"]
    expected = {item["id"]: item for item in inventory["types"] if item.get("coverage") == "equivalent"}
    wanted_trees = {item["deployed_state"] for item in expected.values()}
    captures: dict[str, dict[str, Any]] = {}
    for index, capture in enumerate(value["captures"] if isinstance(value["captures"], list) else []):
        record = f"{record_name}.captures[{index}]"
        found = exact_keys(capture, EQUIVALENCE_CAPTURE_KEYS, record)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        tree_id = capture["tree"]
        record = f"{record_name}.captures.{tree_id}"
        tree = trees.get(tree_id) if isinstance(tree_id, str) else None
        if tree is None or tree_id not in wanted_trees or tree_id in captures:
            problems.append(finding(record, "tree", "is not a deployed state of an equivalence type, or is captured twice", digest))
            continue
        if (capture["repository"], capture["commit"], capture["head_after"]) != (tree["repository"], tree["commit"], tree["commit"]):
            problems.append(finding(record, "commit", f"must be {tree['repository']} at {tree['commit']}", digest))
        if capture["environment"] != environment_for(inventory, tree_id) or capture["inherited_environment"] is not False \
                or capture["interpreter"] != INTERPRETER:
            problems.append(finding(record, "environment", f"is {capture['environment']!r}; the tree's Gate 1 pins give "
                                    f"{environment_for(inventory, tree_id)!r} with no inherited environment", digest))
        if not (isinstance(capture["forge_version"], str) and FORGE["commit"] in capture["forge_version"]
                and f"forge Version: {FORGE['version']}" in capture["forge_version"]):
            problems.append(finding(record, "forge_version", f"is not Forge {FORGE['version']} at {FORGE['commit']}", digest))
        if not (isinstance(capture["forge_config_sha256"], str) and HEX64.match(capture["forge_config_sha256"])):
            problems.append(finding(record, "forge_config_sha256", "must be a SHA-256", digest))
        compiler = capture["compiler"]
        if not (isinstance(compiler, dict) and set(compiler) == {"solc", "evm_version", "via_ir"}):
            problems.append(finding(record, "compiler", "must name solc, evm_version and via_ir", digest))
        if capture["status_after"] != "":
            problems.append(finding(record, "status_after", "the disposable copy was not left clean", digest))
        captures[tree_id] = capture
    for tree_id in sorted(wanted_trees - set(captures)):
        problems.append(finding(f"{record_name}.captures.{tree_id}", "tree", "no capture is recorded for this deployed state", digest))
    profile: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        evidence, _ = read_json(root, PROFILE_EVIDENCE, record_name)
        for entry in evidence.get("records", []) if isinstance(evidence, dict) else []:
            if isinstance(entry, dict) and entry.get("state") == "deployed" and isinstance(entry.get("default"), dict):
                profile[(entry.get("type"), "deployed")] = entry["default"]
    except Refusal as refusal:
        problems += refusal.findings
    results = []
    seen: set[str] = set()
    for index, entry in enumerate(value["types"] if isinstance(value["types"], list) else []):
        record = f"{record_name}.types[{index}]"
        found = exact_keys(entry, EQUIVALENT_KEYS, record)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        type_id = entry["type"]
        record = f"{record_name}.{type_id}"
        item = expected.get(type_id) if isinstance(type_id, str) else None
        if item is None or type_id in seen:
            problems.append(finding(record, "type", "is not an equivalence type of the inventory, or is recorded twice", digest))
            continue
        seen.add(type_id)
        fields = ("deployed_state", "identifier", "anchor", "anchor_identifier")
        if any(entry[f] != item[f] for f in fields):
            problems.append(finding(record, "anchor", "deployed state, identifier or anchor differ from the inventory", digest))
            continue
        anchor = item["anchor"]
        argv = {"storage_layout": ["forge", "inspect", item["identifier"], "storageLayout", "--json", "--force"],
                "method_identifiers": ["forge", "inspect", item["identifier"], "methodIdentifiers", "--json", "--force"]}
        if entry["argv"] != argv:
            problems.append(finding(record, "argv", "must be Hermes's own forge inspect argv for the identifier", digest))
        files = entry["files"]
        if not isinstance(files, dict) or sorted(files) != list(EQUIVALENCE_FILES):
            problems.append(finding(record, "files", f"must name exactly {list(EQUIVALENCE_FILES)}", digest))
            continue
        contents: dict[str, bytes] = {}
        for name in EQUIVALENCE_FILES:
            relative = f"{EQUIVALENCE_DIR}/{type_id}/{name}"
            try:
                contents[name] = read_bytes(root, relative, record)
            except Refusal as refusal:
                problems += refusal.findings
                continue
            if sha256(contents[name]) != files[name]:
                problems.append(finding(record, f"files.{name}", f"recorded {files[name]} but {relative} hashes differently", sha256(contents[name])))
        if len(contents) != len(EQUIVALENCE_FILES):
            continue
        ok = True
        try:
            if canonical_layout_text(hermes, contents["storage-layout.raw.json"], f"{record}:storage-layout.raw.json").encode("utf-8") \
                    != contents["storage-layout.json"]:
                problems.append(finding(record, "storage-layout.json", "is not Hermes's canonical form of the raw inspector output",
                                        sha256(contents["storage-layout.json"])))
                ok = False
            if not check_methods(parse_json(contents["method-identifiers.json"], f"{record}:method-identifiers.json")):
                problems.append(finding(record, "method-identifiers.json", "is not a method map", sha256(contents["method-identifiers.json"])))
                ok = False
        except Refusal as refusal:
            problems += refusal.findings
            ok = False
        capture = captures.get(item["deployed_state"])
        if anchor not in sealed:
            problems.append(finding(record, "anchor", f"{anchor} is not a sealed anchor; no equivalence can rest on it", digest))
            results.append({"type": type_id, "anchor": anchor, "equal": False})
            continue
        anchor_state = sealed[anchor]
        if capture is not None and capture["compiler"] != anchor_state["compiler"]:
            problems.append(finding(record, "compiler", f"the capture at {item['deployed_state']} resolved {capture['compiler']!r}, "
                                    f"the sealed {anchor} Gate 1 resolved {anchor_state['compiler']!r}", digest))
            ok = False
        label = item["anchor_identifier"].rsplit(":", 1)[1]
        anchor_maps = entry["anchor_maps"]
        if not isinstance(anchor_maps, dict) or set(anchor_maps) != {"storage_layout", "method_identifiers"}:
            problems.append(finding(record, "anchor_maps", "must name the anchor's storage_layout and method_identifiers files", digest))
            continue
        for key, mine, relative in (("storage_layout", "storage-layout.json", f"storage-layout/{label}.before.json"),
                                    ("method_identifiers", "method-identifiers.json", f"method-identifiers/{label}.before.json")):
            claimed = anchor_maps[key]
            path = f"{BASELINE_DIRS[anchor]}/run/{relative}"
            theirs = anchor_state["maps"].get(relative)
            sealed_hash = anchor_state["hashes"].get(relative)
            if not (isinstance(claimed, dict) and set(claimed) == {"path", "sha256"} and claimed["path"] == path):
                problems.append(finding(record, f"anchor_maps.{key}", f"must name {path} and its SHA-256", digest))
                ok = False
                continue
            if theirs is None or sealed_hash is None or sha256(theirs) != sealed_hash:
                problems.append(finding(record, f"anchor_maps.{key}", f"{anchor} sealed no map at {relative}", sealed_hash))
                ok = False
                continue
            if claimed["sha256"] != sealed_hash:
                problems.append(finding(record, f"anchor_maps.{key}.sha256", f"is {claimed['sha256']}, the sealed {anchor} map is {sealed_hash}", digest))
                ok = False
            if contents[mine] != theirs:
                problems.append(finding(record, mine, f"differs from the sealed {anchor} map {relative} ({sealed_hash})",
                                        sha256(contents[mine])))
                ok = False
            profiled = profile.get((type_id, "deployed"), {}).get(f"{key}_sha256")
            if profiled != sha256(contents[mine]):
                problems.append(finding(record, mine, f"differs from the profile-invariance map at {item['deployed_state']} ({profiled})",
                                        sha256(contents[mine])))
                ok = False
        results.append({"type": type_id, "deployed_state": item["deployed_state"], "anchor": anchor, "equal": ok,
                        "storage_layout_sha256": sha256(contents["storage-layout.json"]),
                        "method_identifiers_sha256": sha256(contents["method-identifiers.json"])})
    for type_id in sorted(set(expected) - seen):
        problems.append(finding(f"{record_name}.{type_id}", "type", "no equivalence record for this type", digest))
    try:
        present = set(list_directory(root, EQUIVALENCE_DIR, record_name))
        for extra in sorted(present - {"record.json"} - seen):
            problems.append(finding(record_name, "path", f"{EQUIVALENCE_DIR}/{extra} is not a recorded equivalence type", digest))
        for type_id in sorted(seen & present):
            for extra in sorted(set(list_directory(root, f"{EQUIVALENCE_DIR}/{type_id}", record_name)) - set(EQUIVALENCE_FILES)):
                problems.append(finding(record_name, "path", f"{EQUIVALENCE_DIR}/{type_id}/{extra} is not a recorded map", digest))
    except Refusal as refusal:
        problems += refusal.findings
    return problems, {"record": EQUIVALENCE_RECORD, "sha256": digest, "types": len(results),
                      "equal": sum(1 for r in results if r["equal"]), "results": results}


def coverage_of(inventory: dict[str, Any], sealed: dict[str, dict[str, Any]], equivalence: dict[str, Any]) -> dict[str, Any]:
    """Which types and addresses a sealed anchor covers, natively or by a byte-equal equivalence record."""
    equal = {r["type"] for r in equivalence.get("results", []) if r.get("equal")}
    covered: dict[str, str] = {}
    for item in inventory["types"]:
        anchor = sealed.get(item.get("anchor"))
        if item.get("coverage") == "native" and anchor is not None and item.get("anchor_identifier") in anchor["protected"]:
            covered[item["id"]] = "native"
        elif item.get("coverage") == "equivalent" and item["id"] in equal:
            covered[item["id"]] = "equivalent"
    addresses = [a for a in inventory["addresses"] if isinstance(a, dict)]
    uncovered = sorted(item["id"] for item in inventory["types"] if item["id"] not in covered)
    return {"types": len(inventory["types"]), "covered_types": len(covered),
            "native": sum(1 for v in covered.values() if v == "native"),
            "equivalent": sum(1 for v in covered.values() if v == "equivalent"),
            "addresses": len(addresses), "covered_addresses": sum(1 for a in addresses if a.get("type") in covered),
            "sealed_anchors": sorted(sealed), "uncovered": uncovered}


def validate_baseline_directory(root: Path) -> list[str]:
    expected = {BASELINE_NAMES[tree] for tree in BASELINE_TREES} | {PurePosixPath(EXCLUSIONS_RECORD).name}
    try:
        present = set(list_directory(root, f"{DOCS}/baselines", "baselines"))
    except Refusal as refusal:
        return refusal.findings
    problems = [finding("baselines", "path", f"{DOCS}/baselines/{extra} is not an anchor baseline or the exclusion record")
                for extra in sorted(present - expected)]
    # Each anchor directory holds its record and its run directory, nothing beside them.
    for tree in BASELINE_TREES:
        directory = BASELINE_DIRS[tree]
        try:
            names = set(list_directory(root, directory, f"baseline.{tree}"))
        except Refusal as refusal:
            problems += refusal.findings
            continue
        for extra in sorted(names - {"record.json", "run"}):
            if tree in RESTRICTED_TREES:
                withheld = any(extra == item.rstrip("/") for item in WITHHELD)
                detail = "is a withheld Hermes file of a private repository" if withheld else "is not the record or its run directory"
                problems.append(finding(f"baseline.{tree}", "path",
                                        f"{directory}/{extra} {detail}; the public tree carries maps, counts and digests only"))
            else:
                problems.append(finding(f"baseline.{tree}", "path", f"{directory}/{extra} is not the record or its run directory"))
    return problems


def guarded(record: str, check_one: Any, *args: Any) -> tuple[list[str], dict[str, Any]]:
    """Run one record's validator; a malformed record refuses by name rather than raising."""
    try:
        return check_one(*args)
    except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
        return [finding(record, "$", f"is malformed: {type(exc).__name__}: {exc}")], {}


def validate_hermes_evidence(root: Path, inventory: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    try:
        hermes = load_hermes(root)
    except Refusal as refusal:
        return refusal.findings, {}
    problems: list[str] = validate_baseline_directory(root)
    baselines: dict[str, Any] = {}
    anchors: dict[str, dict[str, Any]] = {}
    sealed: dict[str, dict[str, Any]] = {}
    restricted: dict[str, Any] = {}
    for tree in BASELINE_TREES:
        check_one = validate_restricted_baseline if tree in RESTRICTED_TREES else validate_baseline
        found, summary = guarded(f"baseline.{tree}", check_one, root, inventory, hermes, tree)
        problems += found
        state = summary.pop("_state", None) if summary else None
        maps = summary.pop("_sealed", None) if summary else None
        record = summary.pop("_record", None) if summary else None
        if summary and not found:
            if state is not None:
                anchors[tree] = state
            sealed[tree] = maps
            if record is not None:
                restricted[tree] = {"record": record, "maps": maps["maps"]}
        baselines[tree] = summary or None
    found, exclusions = guarded("exclusions", validate_exclusion_evidence, root, inventory)
    problems += found
    found, equivalence = guarded("equivalence", validate_equivalence, root, inventory, hermes, sealed)
    problems += found
    rejections = {}
    for kind in REJECTION_RECORDS:
        found, summary = validate_rejection(root, kind, inventory, anchors, hermes)
        problems += found
        rejections[kind] = summary
    found, reproduction = guarded("reproduction", validate_reproduction, root, inventory, sealed, rejections)
    problems += found
    coverage = coverage_of(inventory, sealed, equivalence)
    return problems, {"baselines": baselines, "exclusions": exclusions or None, "equivalence": equivalence or None,
                      "coverage": coverage, "rejections": rejections, "reproduction": reproduction or None,
                      "_restricted": restricted}


def sealed_coverage_evidence(root: Path, summary: dict[str, Any]) -> dict[str, Any]:
    """Every type and address is covered by a sealed anchor, and each retained private run re-verifies."""
    hermes_summary = summary["hermes"]
    coverage = hermes_summary["coverage"]
    equivalence = hermes_summary["equivalence"]
    if coverage["covered_types"] != TYPE_COUNT or coverage["covered_addresses"] != ADDRESS_COUNT \
            or sorted(coverage["sealed_anchors"]) != sorted(BASELINE_TREES):
        raise Refusal([finding("conformance", "value",
                               f"sealed-coverage: {coverage['covered_types']} of {TYPE_COUNT} types and "
                               f"{coverage['covered_addresses']} of {ADDRESS_COUNT} addresses covered; "
                               f"uncovered {coverage['uncovered']}", (equivalence or {}).get("sha256"))])
    restricted = summary["_records"]["restricted"]
    problems = []
    for tree in RESTRICTED_TREES:
        entry = restricted.get(tree)
        if entry is None:
            problems.append(finding(f"restricted.{tree}", "record", "the public record did not validate"))
            continue
        found, _ = guarded(f"restricted.{tree}", lambda *a: (verify_restricted_payload(*a), {}),
                           root, tree, entry["record"], entry["maps"])
        problems += found
    if problems:
        raise Refusal(problems)
    baselines = hermes_summary["baselines"]
    return {"evidence": {"baselines": {tree: {"path": baselines[tree]["record"], "sha256": baselines[tree]["sha256"],
                                              "state_sha256": baselines[tree]["state_sha256"]} for tree in BASELINE_TREES},
                         "equivalence": {"path": equivalence["record"], "sha256": equivalence["sha256"]},
                         "exclusions": {"path": hermes_summary["exclusions"]["record"], "sha256": hermes_summary["exclusions"]["sha256"]},
                         "restricted": {tree: restricted[tree]["record"]["restricted"]["path"] for tree in RESTRICTED_TREES}},
            "types": coverage["covered_types"], "addresses": coverage["covered_addresses"],
            "native": coverage["native"], "equivalent": coverage["equivalent"]}


def rejection_evidence(kind: str, summary: dict[str, Any]) -> dict[str, Any]:
    """The design report for one Gate 5 demonstration; refuses by name when none reached Gate 5."""
    rejection = summary["hermes"]["rejections"][kind]
    if not rejection or rejection.get("selected") is None:
        attempts = ", ".join(f"{a['id']} {a['status']} exit {a['exit']}" for a in (rejection or {}).get("attempts", []))
        raise Refusal([finding("conformance", "value",
                               f"{kind}-rejection: no recorded attempt exited 50 at Gate 5 naming its intended contract "
                               f"({attempts or 'no attempts'}); blocker: {(rejection or {}).get('blocker')}",
                               (rejection or {}).get("sha256"))])
    chosen = [a for a in rejection["attempts"] if a["id"] == rejection["selected"]][0]
    baseline = summary["hermes"]["baselines"][chosen["tree"]]
    return {"evidence": {"path": rejection["record"], "sha256": rejection["sha256"],
                         "baseline": {"path": baseline["record"], "sha256": baseline["sha256"]}},
            "gate": chosen["gate"], "exit": chosen["exit"], "reason": chosen["reason"]}


# --- reproduction and evidence custody ------------------------------------------

REPRODUCTION_RECORD = f"{DOCS}/evidence/reproduction.json"
REPRODUCTION_SCHEMA = "kickoff-hermes-1355-reproduction/v1"
# A private anchor's reproduced Hermes run directory, named by the SHA-256 of its state.json.
RESTRICTED_REPRODUCTIONS = ".hexaemeron/restricted/reproduction"
REPRODUCTION_KEYS = {"schema", "issue", "hermes", "forge", "interpreter", "workspace", "anchors", "rejections", "observations"}
REPRODUCED_ANCHOR_KEYS = {"tree", "access", "invocation_sha256", "exit", "status", "tests", "maps", "verdict"}
REPRODUCED_REJECTION_KEYS = {"kind", "attempt", "tree", "patch_sha256", "invocation_sha256", "baseline_exit", "verify_exit",
                             "gates_passed", "gate_reached", "reason", "stderr_last_line", "gate1_maps", "after_maps",
                             "restoration", "verdict"}
REPRODUCED = "reproduced"
DIFFERS = "differs"


def invocation_digest(invocation: Any) -> str:
    """The digest a reproduction names for the sealed invocation it re-ran."""
    return sha256(canonical_text(invocation).encode("utf-8"))


def validate_reproduction(root: Path, inventory: dict[str, Any], sealed: dict[str, dict[str, Any]],
                          rejections: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    """The Step 5 re-run of every sealed anchor and both selected Gate 5 candidates.

    Checked against the committed sealed records: each anchor entry names the
    digest of its baseline record's invocation and records exit 0 at
    baseline_ready, the sealed pass count and every sealed map digest, raw
    layouts included. Each rejection entry names the selected attempt's patch
    and invocation digests and records Gates 1 to 4 passed, exit 50 at Gate 5
    with the sealed reason, Gate 1 maps equal to the anchor's, the committed
    after map, and a clean copy at the pinned commit. Each verdict is
    recomputed from those fields rather than read. Recorded only: that the runs
    happened and every reproduced digest and count, because the public copies
    and runs were deleted; `evidence-custody` re-verifies the two private
    reproductions retained under `.hexaemeron/restricted/reproduction/`.
    """
    record_name = "reproduction"
    try:
        value, raw = read_json(root, REPRODUCTION_RECORD, record_name)
    except Refusal as refusal:
        return refusal.findings, {}
    digest = sha256(raw)
    problems = exact_keys(value, REPRODUCTION_KEYS, record_name)
    if problems:
        return [p + f" digest={digest}" for p in problems], {}
    expected = {"schema": REPRODUCTION_SCHEMA, "issue": 1355, "hermes": {"path": HERMES, "sha256": HERMES_SHA256},
                "forge": FORGE, "interpreter": INTERPRETER}
    for key, want in expected.items():
        if value[key] != want:
            problems.append(finding(record_name, key, f"is {value[key]!r}, expected {want!r}", digest))
    anchors = value["anchors"] if isinstance(value["anchors"], list) else []
    if [a.get("tree") if isinstance(a, dict) else None for a in anchors] != list(BASELINE_TREES):
        problems.append(finding(record_name, "anchors", f"must reproduce exactly {list(BASELINE_TREES)} in that order", digest))
    results: dict[str, str] = {}
    retained: dict[str, dict[str, Any]] = {}
    for item in anchors:
        tree = item.get("tree") if isinstance(item, dict) else None
        if tree not in BASELINE_TREES:
            continue
        record = f"{record_name}.{tree}"
        restricted = tree in RESTRICTED_TREES
        found = exact_keys(item, REPRODUCED_ANCHOR_KEYS | ({"retained"} if restricted else set()), record)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        try:
            baseline, _ = read_json(root, BASELINE_RECORDS[tree], record)
        except Refusal as refusal:
            problems += refusal.findings
            continue
        protected = expected_protected(inventory, tree)
        want_maps = {name: baseline["run_files"].get(name) for name in map_names(protected)}
        differences = []
        if item["access"] != ("restricted" if restricted else "public"):
            differences.append("access")
        if item["invocation_sha256"] != invocation_digest(baseline["invocation"]):
            differences.append("invocation_sha256")
        if (item["exit"], item["status"]) != (0, "baseline_ready"):
            differences.append("exit")
        tests = item["tests"]
        if not (isinstance(tests, dict) and set(tests) == {"passed", "failed", "skipped"}
                and (tests["passed"], tests["failed"]) == (ANCHOR_PASSES[tree], 0) and is_int(tests["skipped"])):
            differences.append("tests")
        maps = item["maps"]
        if not isinstance(maps, dict) or sorted(maps) != sorted(want_maps):
            differences.append("maps")
        else:
            for name in sorted(want_maps):
                if maps[name] != want_maps[name] or (tree in sealed and name in sealed[tree]["hashes"]
                                                     and sealed[tree]["hashes"][name] != maps[name]):
                    problems.append(finding(record, f"maps.{name}", f"differs from the sealed record's {want_maps[name]}", maps[name]))
                    differences.append("maps")
        if restricted:
            kept = item["retained"]
            if not (isinstance(kept, dict) and set(kept) == {"path", "state_sha256", "result_sha256"}
                    and isinstance(kept["state_sha256"], str) and HEX64.match(kept["state_sha256"])
                    and isinstance(kept["result_sha256"], str) and HEX64.match(kept["result_sha256"])
                    and kept["path"] == f"{RESTRICTED_REPRODUCTIONS}/{kept['state_sha256']}"):
                problems.append(finding(record, "retained", f"must be {RESTRICTED_REPRODUCTIONS}/<state_sha256> with both digests", digest))
            else:
                retained[tree] = {"retained": kept, "maps": want_maps, "tests": tests, "record": baseline}
        verdict = DIFFERS if differences else REPRODUCED
        for field in sorted(set(differences) - {"maps"}):
            problems.append(finding(record, field, "does not reproduce the sealed record", digest))
        if item["verdict"] != verdict:
            problems.append(finding(record, "verdict", f"records {item['verdict']!r} but the fields recompute {verdict!r}", digest))
        results[tree] = verdict
    rows = value["rejections"] if isinstance(value["rejections"], list) else []
    if [r.get("kind") if isinstance(r, dict) else None for r in rows] != list(REJECTION_RECORDS):
        problems.append(finding(record_name, "rejections", f"must reproduce exactly {list(REJECTION_RECORDS)} in that order", digest))
    rejected: dict[str, str] = {}
    for row in rows:
        kind = row.get("kind") if isinstance(row, dict) else None
        if kind not in REJECTION_RECORDS:
            continue
        record = f"{record_name}.{kind}"
        found = exact_keys(row, REPRODUCED_REJECTION_KEYS, record)
        if found:
            problems += [p + f" digest={digest}" for p in found]
            continue
        summary = rejections.get(kind) or {}
        try:
            sealed_record, _ = read_json(root, REJECTION_RECORDS[kind], record)
        except Refusal as refusal:
            problems += refusal.findings
            continue
        chosen = [a for a in sealed_record.get("attempts", []) if isinstance(a, dict) and a.get("id") == summary.get("selected")]
        if not chosen or row["attempt"] != chosen[0]["id"]:
            problems.append(finding(record, "attempt", f"must be the selected attempt {summary.get('selected')!r}", digest))
            continue
        attempt = chosen[0]
        tree = attempt["tree"]
        commit = inventory["trees"][tree]["commit"]
        anchor_maps = sealed.get(tree, {}).get("hashes", {})
        after = {k: v for k, v in attempt["run_files"].items() if k.endswith(".after.json")}
        checks = {
            "tree": row["tree"] == tree,
            "patch_sha256": row["patch_sha256"] == attempt["patch_sha256"] == sha256(attempt["patch"].encode("utf-8")),
            "invocation_sha256": row["invocation_sha256"] == invocation_digest(attempt["invocation"]),
            "baseline_exit": row["baseline_exit"] == 0,
            "verify_exit": row["verify_exit"] == 50,
            "gates_passed": row["gates_passed"] == [1, 2, 3, 4],
            "gate_reached": row["gate_reached"] == 5,
            "reason": row["reason"] == attempt["reason"] == f"{GATE5_PREFIX[kind]}: {attempt['intended_contract']}",
            "stderr_last_line": row["stderr_last_line"] == f"Hermes rejected at Gate 5: {attempt['reason']}",
            "gate1_maps": bool(anchor_maps) and row["gate1_maps"] == anchor_maps,
            "after_maps": bool(after) and row["after_maps"] == after,
            "restoration": isinstance(row["restoration"], dict) and row["restoration"].get("status_after") == ""
                           and row["restoration"].get("head_after") == commit,
        }
        for field, holds in checks.items():
            if not holds:
                problems.append(finding(record, field, f"does not reproduce the sealed {attempt['id']} rejection "
                                        f"(exit 50 at Gate 5: {attempt['reason']})", digest))
        verdict = REPRODUCED if all(checks.values()) else DIFFERS
        if row["verdict"] != verdict:
            problems.append(finding(record, "verdict", f"records {row['verdict']!r} but the fields recompute {verdict!r}", digest))
        rejected[kind] = verdict
    observations = value["observations"]
    if not (isinstance(observations, dict) and set(observations) == {"positive", "negative"}
            and all(isinstance(v, list) and v and all(text(s) for s in v) for v in observations.values())):
        problems.append(finding(record_name, "observations", "must list positive and negative observations as text", digest))
    if not text(value["workspace"]):
        problems.append(finding(record_name, "workspace", "must name the disposable workspace", digest))
    return problems, {"record": REPRODUCTION_RECORD, "sha256": digest, "anchors": results, "rejections": rejected,
                      "_retained": retained}


def verify_reproduction_payload(root: Path, tree_id: str, entry: dict[str, Any]) -> tuple[list[str], list[str]]:
    """A retained private reproduction: its state and result, its maps and its test count, from the retained bytes.

    The retained `state.json` must not be the sealed run's byte for byte, its
    state projection (commit, compiler, seed, exclusions, protected set, Gate 1
    commands and map digests) must equal the one the sealed public record
    carries, and `result.json` must be Hermes's exact `baseline_ready` result
    for that state's run directory. Recorded only: that the run was executed
    afresh. A copy of the sealed run with an edited run directory or creation
    time, re-hashed into the reproduction record, is not told apart.
    """
    record_name = f"reproduction.{tree_id}.retained"
    kept = entry["retained"]
    base = kept["path"]
    sealed = entry["record"]
    try:
        state_raw = read_bytes(root, f"{base}/state.json", record_name)
        result_raw = read_bytes(root, f"{base}/result.json", record_name)
    except Refusal as refusal:
        return [item + " (the retained reproduction is not present)" for item in refusal.findings], []
    if sha256(state_raw) != kept["state_sha256"]:
        return [finding(record_name, "state_sha256", f"{base}/state.json does not match the reproduction record", sha256(state_raw))], []
    problems = []
    if sha256(result_raw) != kept["result_sha256"]:
        problems.append(finding(record_name, "result_sha256", f"{base}/result.json does not match the reproduction record", sha256(result_raw)))
    if kept["state_sha256"] == sealed["restricted"]["state_sha256"]:
        problems.append(finding(record_name, "state_sha256", "is the sealed run's state.json byte for byte", kept["state_sha256"]))
    state = parse_json(state_raw, record_name)
    result = parse_json(result_raw, record_name)
    if state_projection(state) != sealed["state"]:
        problems.append(finding(record_name, "state", "the retained reproduction's state differs from the sealed record's projection",
                                sha256(state_raw)))
    if not isinstance(state, dict) or state.get("status") != "baseline_ready" \
            or result != {"schema": HERMES_RUN_SCHEMA, "skill": "hermes", "status": "baseline_ready",
                          "exit_code": 0, "run_dir": state.get("run_dir")}:
        return problems + [finding(record_name, "status", "the retained reproduction is not baseline_ready with exit 0", sha256(state_raw))], []
    hashes = state.get("baseline", {}).get("artifact_hashes") if isinstance(state.get("baseline"), dict) else None
    if not isinstance(hashes, dict) or not hashes:
        return problems + [finding(record_name, "artifact_hashes", "missing", sha256(state_raw))], []
    for relative, want in sorted(hashes.items()):
        try:
            actual = sha256(read_bytes(root, f"{base}/{relative}", record_name))
        except Refusal as refusal:
            problems += refusal.findings
            continue
        if actual != want:
            problems.append(finding(record_name, f"artifact_hashes.{relative}", "does not recompute from the retained file", actual))
    for relative, want in sorted(entry["maps"].items()):
        try:
            actual = sha256(read_bytes(root, f"{base}/{relative}", record_name))
        except Refusal as refusal:
            problems += refusal.findings
            continue
        if actual != want:
            problems.append(finding(record_name, relative, "the retained reproduced map differs from the sealed record", actual))
    try:
        log = read_bytes(root, f"{base}/logs/gate1.forge-test.log", record_name).decode("utf-8", errors="replace")
    except Refusal as refusal:
        return problems + refusal.findings, [base]
    counts = re.findall(r"^Ran \d+ test suites? .*?(\d+) tests passed, (\d+) failed, (\d+) skipped", log, re.M)
    tests = entry["tests"]
    if not counts or tuple(int(n) for n in counts[-1]) != (tests["passed"], tests["failed"], tests["skipped"]):
        problems.append(finding(record_name, "tests", f"the retained test log does not report {tests['passed']} passed", sha256(log.encode())))
    return problems, [base]


RESTRICTED_REFERENCE = re.compile(rb"\.hexaemeron/restricted(?:/[A-Za-z0-9_.-]+)*/?")
SNAPSHOT_TEST = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*):([A-Za-z_][A-Za-z0-9_]*)\(", re.M)
LOG_SUITE = re.compile(r"^Ran \d+ tests? for ([A-Za-z0-9_./-]+):([A-Za-z_][A-Za-z0-9_]*)", re.M)


def test_identifiers(snapshot: str, log: str = "") -> set[str]:
    """Every test identifier a gas snapshot or Forge test log names: suite, function, pair and test file path."""
    found: set[str] = set()
    for suite, function in SNAPSHOT_TEST.findall(snapshot):
        found |= {f"{suite}:{function}", suite, function}
    for path, suite in LOG_SUITE.findall(log):
        found |= {path, suite}
    return found


def names_identifier(text_value: str, identifier: str) -> bool:
    """Whether the text names the identifier as a whole token, not inside a longer name."""
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(identifier)}(?![A-Za-z0-9_])", text_value) is not None


def restricted_file(root: Path, relative: str, want: Any, record: str, problems: list[str]) -> bool:
    """One retained payload file named by digest: present, regular, and matching."""
    try:
        raw = read_bytes(root, relative, record, MAX_PAYLOAD)
    except Refusal as refusal:
        problems.extend(f"{item} payload={relative} (the named restricted payload is not present)" for item in refusal.findings)
        return False
    if sha256(raw) != want:
        problems.append(finding(record, "sha256", f"{relative} does not match the digest the committed record names", sha256(raw)))
        return False
    return True


def retained_tree(root: Path, base: str, record: str) -> dict[str, bytes]:
    """Every regular file under one retained private run directory, read with the same bounds."""
    files: dict[str, bytes] = {}
    stack = [""]
    while stack:
        prefix = stack.pop()
        directory = f"{base}/{prefix}".rstrip("/")
        for name in list_directory(root, directory, record):
            child = f"{prefix}{name}"
            mode = (root / directory / name).lstat().st_mode
            if stat.S_ISDIR(mode):
                stack.append(child + "/")
            elif stat.S_ISREG(mode):
                files[child] = read_bytes(root, f"{base}/{child}", record)
            if len(files) > MAX_TREE_FILES:
                raise Refusal([finding(record, "path", f"{base} holds more than {MAX_TREE_FILES} files")])
    return files


def docs_files(root: Path) -> dict[str, bytes]:
    """Every file under the docs tree; `check` has already refused links, depth and suffixes there."""
    files: dict[str, bytes] = {}
    stack = [DOCS]
    while stack:
        directory = stack.pop()
        for name in list_directory(root, directory, "custody"):
            child = f"{directory}/{name}"
            if stat.S_ISDIR((root / child).lstat().st_mode):
                stack.append(child)
            else:
                files[child] = read_bytes(root, child, "custody")
    return files


def evidence_custody_evidence(root: Path, summary: dict[str, Any]) -> dict[str, Any]:
    """Custody of the delivered evidence set, recomputed from committed and retained bytes.

    Recomputed: `check` passes, including its scan for symlinks, suffixes,
    Solidity text and private build inputs; every retained payload a committed
    record names by digest is present and matches (the fixture components and
    manifest, the capture script, the release manifest and plan, both sealed
    private Hermes runs through `verify_restricted_payload`, and both private
    reproductions); every `.hexaemeron/restricted` path any docs file mentions
    resolves to one of those verified payloads; no docs file, and no JSON
    string in one, has the bytes of a retained private file other than the
    public maps each private record declares; no docs file names, as a whole
    token, a private test suite, function or file path from a retained gas
    snapshot or Forge test log that no public anchor's snapshot also names;
    each retained private reproduction's `state.json` is not the sealed run's
    byte for byte and projects to the sealed record's state (a re-hashed copy
    of the sealed run is not told apart); no docs file has the digest
    of a target source file named by any sealed source manifest; and every
    reproduction verdict is `reproduced`.
    """
    records = summary["_records"]
    hermes_summary = summary["hermes"]
    reproduction = hermes_summary["reproduction"]
    problems: list[str] = []
    if not reproduction or any(v != REPRODUCED for v in reproduction["anchors"].values()) \
            or sorted(reproduction["anchors"]) != sorted(BASELINE_TREES) \
            or sorted(reproduction["rejections"]) != sorted(REJECTION_RECORDS) \
            or any(v != REPRODUCED for v in reproduction["rejections"].values()):
        raise Refusal([finding("conformance", "value", "evidence-custody: not every anchor and rejection reproduced",
                               (reproduction or {}).get("sha256"))])
    verified: list[str] = []
    fixture = records["fixture"]
    payload = fixture["payload"]
    base = payload["retained_at"]
    good = restricted_file(root, f"{base}/manifest.json", payload["manifest_sha256"], "custody.fixture", problems)
    for component in payload["components"]:
        good = restricted_file(root, f"{base}/{component['path']}", component["sha256"], "custody.fixture", problems) and good
    if good:
        verified.append(base)
    if restricted_file(root, CAPTURE_SCRIPT, fixture["capture"]["script_sha256"], "custody.fixture.capture", problems):
        verified.append(CAPTURE_SCRIPT)
    release = records["release"]["payload"]
    if restricted_file(root, f"{release['retained_at']}/manifest.json", release["manifest_sha256"], "custody.release", problems):
        verified.append(release["retained_at"])
    if restricted_file(root, release["plan_retained_at"], release["plan_sha256"], "custody.release.plan", problems):
        verified.append(release["plan_retained_at"])
    private_runs: list[str] = []
    public_maps: set[str] = set()
    for tree in RESTRICTED_TREES:
        entry = records["restricted"].get(tree)
        if entry is None:
            problems.append(finding(f"custody.{tree}", "record", "the public record did not validate"))
            continue
        public_maps |= {sha256(raw) for raw in entry["maps"].values()}
        found, _ = guarded(f"restricted.{tree}", lambda *a: (verify_restricted_payload(*a), {}),
                           root, tree, entry["record"], entry["maps"])
        problems += [item if "(the retained run is not present)" not in item
                     else item.replace("(the retained run is not present)", "(the named restricted payload is not present)")
                     for item in found]
        if not found:
            verified.append(entry["record"]["restricted"]["path"])
            private_runs.append(entry["record"]["restricted"]["path"])
    for tree, entry in sorted(records["reproduced"].items()):
        found, bases = verify_reproduction_payload(root, tree, entry)
        problems += [item.replace("(the retained reproduction is not present)", "(the named restricted payload is not present)")
                     for item in found]
        if not found:
            verified += bases
            private_runs += bases
    private_bytes: set[str] = set()
    private_tests: set[str] = set()
    manifests: set[str] = set()
    for base in private_runs:
        try:
            files = retained_tree(root, base, "custody.private")
        except Refusal as refusal:
            problems += refusal.findings
            continue
        private_bytes |= {sha256(raw) for raw in files.values()}
        snapshot = files.get("baseline.gas-snapshot", b"").decode("utf-8", errors="replace")
        log = files.get("logs/gate1.forge-test.log", b"").decode("utf-8", errors="replace")
        private_tests |= test_identifiers(snapshot, log)
        manifest = files.get("baseline-source-manifest.json")
        if manifest is not None:
            value = parse_json(manifest, "custody.private")
            manifests |= {v for v in value.values() if isinstance(v, str)} if isinstance(value, dict) else set()
    # Bytes every Hermes run shares, such as the Forge version text or the corpus
    # copy, are public already: they are the public anchors' sealed artefacts.
    public_known = set(public_maps) | {sha256(b"")}
    public_tests: set[str] = set()
    for tree in BASELINE_TREES:
        if tree in RESTRICTED_TREES:
            continue
        run = f"{BASELINE_DIRS[tree]}/run"
        baseline, _ = read_json(root, BASELINE_RECORDS[tree], "custody")
        public_known |= {v for v in baseline["run_files"].values() if isinstance(v, str)}
        public_known |= {sha256(t.encode("utf-8")) for t in baseline["artefact_text"].values() if isinstance(t, str)}
        public_tests |= test_identifiers(baseline["artefact_text"].get("baseline.gas-snapshot") or "")
        state = parse_json(read_bytes(root, f"{run}/state.json", "custody"), "custody")
        public_known |= {v for v in state["baseline"]["artifact_hashes"].values() if isinstance(v, str)}
        manifest = parse_json(read_bytes(root, f"{run}/baseline-source-manifest.json", "custody"), "custody")
        manifests |= {v for v in manifest.values() if isinstance(v, str)} if isinstance(manifest, dict) else set()
    private_bytes -= public_known
    # A test name a public anchor's snapshot also carries is public already.
    private_tests -= public_tests
    references: set[str] = set()
    files = docs_files(root)
    for relative, raw in sorted(files.items()):
        digest = sha256(raw)
        if digest in private_bytes:
            problems.append(finding("custody", "path", f"{relative} has the bytes of a retained private file", digest))
        if digest in manifests:
            problems.append(finding("custody", "path", f"{relative} has the digest of a sealed target source file", digest))
        text_value = raw.decode("utf-8", errors="replace")
        leaked = sorted(test for test in private_tests if names_identifier(text_value, test))
        if leaked:
            problems.append(finding("custody", "path", f"{relative} carries private test output {leaked[:3]}", digest))
        if relative.endswith(".json"):
            strings = json_strings(parse_json(raw, "custody"))
            if any(sha256(item.encode("utf-8")) in private_bytes for item in strings):
                problems.append(finding("custody", "path", f"{relative} embeds a retained private file in a JSON string", digest))
        # Prose ends a path with a full stop, so trailing dots and slashes are not part of it.
        references |= {match.decode("utf-8").rstrip("./") for match in RESTRICTED_REFERENCE.findall(raw)}
    for reference in sorted(references):
        if not any(reference == path or path.startswith(reference + "/") or reference.startswith(path + "/")
                   for path in verified):
            problems.append(finding("custody", "reference", f"{reference} is named under {DOCS} but no verified payload backs it"))
    if problems:
        raise Refusal(problems)
    return {"evidence": {"reproduction": {"path": reproduction["record"], "sha256": reproduction["sha256"]}},
            "payloads": len(verified), "private_runs": len(private_runs), "docs_files": len(files),
            "references": len(references), "private_tests": len(private_tests), "source_digests": len(manifests)}


# --- top level -------------------------------------------------------------------

def check(root: Path = ROOT) -> dict[str, Any]:
    inventory, raw = read_json(root, INVENTORY, "inventory")
    inventory_sha = sha256(raw)
    top = {"schema", "issue", "selected_design", "registry", "documents", "trees", "profiles", "types", "addresses", "exclusions"}
    problems = exact_keys(inventory, top, "inventory")
    if problems:
        raise Refusal([p + f" digest={inventory_sha}" for p in problems])
    if inventory["schema"] != INVENTORY_SCHEMA or inventory["issue"] != 1355 or inventory["selected_design"] != SELECTED:
        raise Refusal([finding("inventory", "schema", f"must be {INVENTORY_SCHEMA} for issue 1355 and {SELECTED}", inventory_sha)])
    row = load_registry(root, inventory)
    problems += validate_documents(root, inventory["documents"])
    problems += validate_trees(inventory["trees"])
    problems += validate_profiles(inventory["profiles"])
    if problems:
        raise Refusal(problems)
    type_problems, types = validate_types(inventory["types"], inventory["trees"], inventory["profiles"])
    problems += type_problems
    problems += validate_addresses(inventory["addresses"], row, types, inventory["trees"])
    problems += validate_exclusions(inventory["exclusions"], row)
    if not type_problems:
        problems += validate_profile_sources(root, row, types, inventory["trees"], inventory["profiles"],
                                             inventory["addresses"])
        problems += validate_overrides(root, row, types, inventory["addresses"])
    design = load_design(root)
    problems += validate_design_reports(root, design)
    problems += validate_custody(root, private_digests(row))
    summary: dict[str, Any] = {}
    chain: dict[str, Any] = {}
    hermes_evidence: dict[str, Any] = {}
    if not type_problems:
        profile_problems, summary = validate_profile_evidence(root, inventory, types)
        problems += profile_problems
        chain_problems, chain = validate_chain_evidence(root, inventory, row)
        problems += chain_problems
        hermes_problems, hermes_evidence = validate_hermes_evidence(root, inventory)
        problems += hermes_problems
    if problems:
        raise Refusal(problems)
    restricted = hermes_evidence.pop("_restricted", {}) if hermes_evidence else {}
    reproduced = (hermes_evidence.get("reproduction") or {}).pop("_retained", {}) if hermes_evidence else {}
    return {
        "status": "ok",
        "inventory": {"path": INVENTORY, "sha256": inventory_sha},
        "addresses": len(inventory["addresses"]),
        "types": len(types),
        "exclusions": len(inventory["exclusions"]),
        "profile_invariance": summary or None,
        "chain_evidence": {key: chain.get(key) for key in ("fixture", "release", "handoffs")},
        "hermes": hermes_evidence or None,
        "_records": {"inventory": inventory, "fixture": chain.get("_fixture"), "release": chain.get("_release"),
                     "restricted": restricted, "reproduced": reproduced},
    }


def resolver_command(candidate: str, criterion: str) -> str:
    return (f"python3 scripts/kickoff_hermes_1355.py conformance --criterion {criterion} "
            f"--candidate {candidate} --report {REPORT_DIRECTORY}/{candidate}-{criterion}.json")


def fresh_report_path(root: Path, supplied: str, candidate: str, criterion: str) -> Path:
    expected = f"{REPORT_DIRECTORY}/{candidate}-{criterion}.json"
    if supplied != expected:
        raise Refusal([finding("conformance", "report", f"must be {expected}, the path the design record names")])
    current = root
    for part in PurePosixPath(expected).parts[:-1]:
        current = current / part
        try:
            mode = current.lstat().st_mode
        except FileNotFoundError:
            current.mkdir(mode=0o755)
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISDIR(mode):
            raise Refusal([finding("conformance", "report", f"{current.relative_to(root)} is a symlink or not a directory")])
    target = root / expected
    if target.exists() or target.is_symlink():
        raise Refusal([finding("conformance", "report", f"{expected} already exists; a retry uses a fresh path")])
    return target


def conformance(root: Path, criterion: str, candidate: str, report: str,
                verifiers: dict[str, Any] | None = None) -> dict[str, Any]:
    if criterion not in CONFORMANCE:
        raise Refusal([finding("conformance", "criterion", f"{criterion!r} is not a conformance criterion of the design record")])
    design = load_design(root)
    candidates = {item.get("id") for item in design.get("candidates", [])}
    if candidate not in candidates:
        raise Refusal([finding("conformance", "candidate", f"{candidate!r} is not a candidate of the design record", DESIGN_SHA256)])
    if candidate != SELECTED:
        raise Refusal([finding("conformance", "candidate", f"{candidate} was not selected; only {SELECTED} is built", DESIGN_SHA256)])
    cells = [r for r in design.get("results", []) if r.get("candidate") == candidate and r.get("criterion") == criterion]
    command = resolver_command(candidate, criterion)
    if len(cells) != 1 or cells[0].get("resolver") != command or cells[0].get("blocks") != CONFORMANCE[criterion]:
        raise Refusal([finding("conformance", "resolver", f"the design record does not name {command!r}", DESIGN_SHA256)])
    target = fresh_report_path(root, report, candidate, criterion)
    summary = check(root)
    if criterion == "profile-invariance":
        invariance = summary["profile_invariance"]
        if not invariance or invariance["invariant"] != invariance["comparisons"] or invariance["types"] != TYPE_COUNT:
            raise Refusal([finding("conformance", "value", "not every type is invariant under both profiles",
                                   (invariance or {}).get("sha256"))])
        result = {"evidence": {"path": invariance["record"], "sha256": invariance["sha256"]},
                  "comparisons": invariance["comparisons"], "types": invariance["types"]}
    elif criterion == "owner-handoffs":
        result = owner_handoffs_evidence(root, summary, verifiers or sibling_verifiers(root))
    elif criterion == "sealed-coverage":
        result = sealed_coverage_evidence(root, summary)
    elif criterion == "evidence-custody":
        result = evidence_custody_evidence(root, summary)
    else:
        result = rejection_evidence(criterion.removesuffix("-rejection"), summary)
    value = {"schema": REPORT_SCHEMA, "candidate": candidate, "criterion": criterion, "value": True,
             "unit": "boolean", "command": command, "exit": 0}
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return {"status": "written", "report": report, "sha256": sha256(data), "value": True, **result}


def owner_handoffs_evidence(root: Path, summary: dict[str, Any], verifiers: dict[str, Any]) -> dict[str, Any]:
    """Every handoff is handed on and both retained payloads re-verify to their committed records.

    A handed-on row is complete, or it is the inventory with its target-maintainer
    review recorded as outstanding; the report's boolean does not say that review
    happened, and the committed row keeps the status that says it has not.
    """
    chain = summary["chain_evidence"]
    records = summary["_records"]
    handoffs = chain["handoffs"]
    if not handoffs or handoffs["handed_off"] != len(HANDOFFS) or handoffs["rows"] != len(HANDOFFS):
        raise Refusal([finding("conformance", "value", "not every owner handoff is handed on", (handoffs or {}).get("sha256"))])
    problems = validate_fixture_payload(root, records["fixture"], records["inventory"], verifiers["fixture"])
    problems += validate_release_payload(root, records["release"], records["inventory"], verifiers["release"])
    if problems:
        raise Refusal(problems)
    return {"evidence": {"fixture": chain["fixture"], "release": chain["release"], "handoffs": handoffs}}


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = top.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="validate the inventory, digests, profile evidence and custody")
    conf = commands.add_parser("conformance", help="write one design report for a conformance criterion")
    conf.add_argument("--criterion", required=True)
    conf.add_argument("--candidate", required=True)
    conf.add_argument("--report", required=True)
    return top


def main(argv: list[str] | None = None, root: Path = ROOT) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "check":
            result = check(root)
            result.pop("_records")
        else:
            result = conformance(root, args.criterion, args.candidate, args.report)
    except Refusal as refusal:
        for item in refusal.findings:
            print(f"refused: {item}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
