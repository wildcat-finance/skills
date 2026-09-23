#!/usr/bin/env python3
"""Check the issue 1355 protected inventory and write its design reports.

`check` validates the committed inventory against the pinned registry row, the
repository copies of the study, runbook and design record, the
profile-invariance evidence, the fixture, release and owner-handoff records,
and the custody rules for `docs/kickoff/1355/`.

`conformance --criterion <id> --candidate <id> --report <path>` writes one
closed `protasis-design-report/v1` for an implemented conformance criterion.
`owner-handoffs` also re-verifies the retained fixture and release under
`.hexaemeron/restricted/` with Lazarus's and Alexandria's own verifiers,
loaded in-process. From those bytes it recomputes every fixture row, component
digest, plan limit, recorded response and release identity. The capture's
request, byte and time counts, its UTC time and its attempt list are the
capture script's own report, and no retained byte recomputes them. A criterion
whose evidence belongs to a later step refuses by name.

Every read is bounded, refuses symlinks and parses JSON into closed schemas.
The checker starts no subprocess and reaches no network. Every refusal names
the record, the field and the digest involved.
"""

from __future__ import annotations

import argparse
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
RUNBOOK_SHA256 = "de2d0ccc1b6576059b37fbe91b0c3c0e7646b33a2fb184d0ca21cbb6817ac0b5"
DESIGN_SHA256 = "3d3f5097938b422f1d77d9c6ffb46448038a51bd2704674a3375145d5a80d650"
REGISTRY_PATH = "docs/kickoff/1359/targets.json"
REGISTRY_SHA256 = "417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea"
REGISTRY_ROW = "wildcat-v2-ethereum-mainnet"
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

# criterion -> the transition it blocks; Step 1 lands profile-invariance, Step 2 owner-handoffs.
CONFORMANCE = {
    "profile-invariance": "step:2",
    "owner-handoffs": "step:3",
    "selector-rejection": "step:4",
    "layout-rejection": "step:4",
    "sealed-coverage": "step:5",
    "evidence-custody": "integration",
}
IMPLEMENTED = {"profile-invariance", "owner-handoffs"}

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

def load_registry(root: Path, inventory: dict[str, Any]) -> dict[str, Any]:
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
    value, raw = read_json(root, REGISTRY_PATH, "registry")
    digest = sha256(raw)
    if digest != REGISTRY_SHA256:
        raise Refusal([finding("registry", "sha256", f"{REGISTRY_PATH} does not match the pinned {REGISTRY_SHA256}", digest)])
    rows = [row for row in value.get("targets", []) if isinstance(row, dict) and row.get("id") == REGISTRY_ROW]
    if len(rows) != 1:
        raise Refusal([finding("registry", "targets", f"expected one {REGISTRY_ROW} row, found {len(rows)}", digest)])
    row = dict(rows[0])
    row["_evidence_digests"] = value.get("evidence_digests") if isinstance(value.get("evidence_digests"), dict) else {}
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
    """The registry is pinned by this checker; its evidence files are pinned by the registry."""
    return REGISTRY_SHA256 if relative == REGISTRY_PATH else registry_digest(row, relative)


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
    complete = 0
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
        if row["status"] != "complete":
            problems.append(finding(sub, "status", f"is {row['status']!r}, not complete", digest))
            ok = False
        complete += int(ok)
    for missing in sorted(set(HANDOFFS) - seen):
        problems.append(finding(f"owner-handoffs.{missing}", "handoff", "has no row", digest))
    return problems, {"record": HANDOFFS_RECORD, "sha256": digest, "rows": len(rows), "complete": complete}


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
    if not type_problems:
        profile_problems, summary = validate_profile_evidence(root, inventory, types)
        problems += profile_problems
        chain_problems, chain = validate_chain_evidence(root, inventory, row)
        problems += chain_problems
    if problems:
        raise Refusal(problems)
    return {
        "status": "ok",
        "inventory": {"path": INVENTORY, "sha256": inventory_sha},
        "addresses": len(inventory["addresses"]),
        "types": len(types),
        "exclusions": len(inventory["exclusions"]),
        "profile_invariance": summary or None,
        "chain_evidence": {key: chain.get(key) for key in ("fixture", "release", "handoffs")},
        "_records": {"inventory": inventory, "fixture": chain.get("_fixture"), "release": chain.get("_release")},
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
    if criterion not in IMPLEMENTED:
        raise Refusal([finding("conformance", "criterion",
                               f"{criterion} is not implemented yet; it blocks {CONFORMANCE[criterion]} and its evidence lands in a later step",
                               DESIGN_SHA256)])
    target = fresh_report_path(root, report, candidate, criterion)
    summary = check(root)
    if criterion == "profile-invariance":
        invariance = summary["profile_invariance"]
        if not invariance or invariance["invariant"] != invariance["comparisons"] or invariance["types"] != TYPE_COUNT:
            raise Refusal([finding("conformance", "value", "not every type is invariant under both profiles",
                                   (invariance or {}).get("sha256"))])
        result = {"evidence": {"path": invariance["record"], "sha256": invariance["sha256"]},
                  "comparisons": invariance["comparisons"], "types": invariance["types"]}
    else:
        result = owner_handoffs_evidence(root, summary, verifiers or sibling_verifiers(root))
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
    """Every handoff row is complete and both retained payloads re-verify to their committed records."""
    chain = summary["chain_evidence"]
    records = summary["_records"]
    handoffs = chain["handoffs"]
    if not handoffs or handoffs["complete"] != len(HANDOFFS) or handoffs["rows"] != len(HANDOFFS):
        raise Refusal([finding("conformance", "value", "not every owner handoff is complete", (handoffs or {}).get("sha256"))])
    problems = validate_fixture_payload(root, records["fixture"], records["inventory"], verifiers["fixture"])
    problems += validate_release_payload(root, records["release"], records["inventory"], verifiers["release"])
    if problems:
        raise Refusal(problems)
    return {"evidence": {"fixture": chain["fixture"], "release": chain["release"], "handoffs": handoffs}}


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = top.add_subparsers(dest="command", required=True)
    commands.add_parser("check", help="validate the inventory, digests, profile evidence and custody")
    conf = commands.add_parser("conformance", help="write one design report for an implemented criterion")
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
