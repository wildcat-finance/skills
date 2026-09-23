#!/usr/bin/env python3
"""Check the issue 1355 protected inventory and write its design reports.

`check` validates the committed inventory against the pinned registry row, the
repository copies of the study, runbook and design record, the
profile-invariance evidence and the custody rules for `docs/kickoff/1355/`.

`conformance --criterion <id> --candidate <id> --report <path>` writes one
closed `protasis-design-report/v1` for an implemented conformance criterion.
A criterion whose evidence belongs to a later step refuses by name.

The checker reads committed JSON and Markdown only. Every read is bounded,
refuses symlinks, parses JSON into closed schemas and starts no subprocess.
Every refusal names the record, the field and the digest involved.
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

# criterion -> the transition it blocks; only profile-invariance lands in Step 1.
CONFORMANCE = {
    "profile-invariance": "step:2",
    "owner-handoffs": "step:3",
    "selector-rejection": "step:4",
    "layout-rejection": "step:4",
    "sealed-coverage": "step:5",
    "evidence-custody": "integration",
}
IMPLEMENTED = {"profile-invariance"}

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
    if not type_problems:
        profile_problems, summary = validate_profile_evidence(root, inventory, types)
        problems += profile_problems
    if problems:
        raise Refusal(problems)
    return {
        "status": "ok",
        "inventory": {"path": INVENTORY, "sha256": inventory_sha},
        "addresses": len(inventory["addresses"]),
        "types": len(types),
        "exclusions": len(inventory["exclusions"]),
        "profile_invariance": summary or None,
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


def conformance(root: Path, criterion: str, candidate: str, report: str) -> dict[str, Any]:
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
    invariance = summary["profile_invariance"]
    if not invariance or invariance["invariant"] != invariance["comparisons"] or invariance["types"] != TYPE_COUNT:
        raise Refusal([finding("conformance", "value", "not every type is invariant under both profiles",
                               (invariance or {}).get("sha256"))])
    value = {"schema": REPORT_SCHEMA, "candidate": candidate, "criterion": criterion, "value": True,
             "unit": "boolean", "command": command, "exit": 0}
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o644)
    try:
        os.write(fd, data)
    finally:
        os.close(fd)
    return {"status": "written", "report": report, "sha256": sha256(data), "value": True,
            "evidence": {"path": invariance["record"], "sha256": invariance["sha256"]},
            "comparisons": invariance["comparisons"], "types": invariance["types"]}


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
