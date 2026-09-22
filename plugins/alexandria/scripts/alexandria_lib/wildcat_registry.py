"""Pinned Wildcat V2 deployment-registry generation from merged repository records.

The registry is generated from two merged JSON records of this repository and
from nothing else: `docs/kickoff/1359/targets.json`, whose
`wildcat-v2-ethereum-mainnet` row lists the estate's 137 contracts, and
`docs/kickoff/1359/evidence/ethereum-mainnet-1590.json`, which carries the
core contracts' creation blocks and the arch controller's registered-market
list. Each record is pinned here by SHA-256 and byte count and a changed one
is refused before it is parsed. The generator runs no subprocess and reaches
no network.

The generated document is validated against `WILDCAT_V2_REGISTRY_SHA256`. That
constant is held in this module and nowhere else: no plan field and no
operator document can supply it, and the venue module re-exports
`validate_registry` rather than restating the digest.

The row records three address-list digests and the serialisation they were
taken over (`sha256_method`). The generator maps that declared method to a
named canonical form, reproduces each digest under it, refuses one that does
not reproduce, and records the form beside each digest. The form is recorded
rather than assumed because the two Wildcat rows do not share one.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from .canonical import canonical_bytes
from .errors import AlexandriaError
from .interval import ADDRESS_RE, HASH_RE, CODE_DIGEST_RE
from .paths import read_confined_file


REGISTRY_FORMAT = "alexandria-wildcat-v2-registry/v1"
VENUE = "wildcat-v2"
ROW_ID = "wildcat-v2-ethereum-mainnet"
CHAIN_ID = 1
TARGETS_PATH = "docs/kickoff/1359/targets.json"
ESTATE_PATH = "docs/kickoff/1359/evidence/ethereum-mainnet-1590.json"
# Each record the generator reads: its repository path, the SHA-256 of its
# bytes and its byte count, recomputed with `shasum -a 256 <path>` and
# `wc -c <path>` at the base this module was written on.
SOURCE_RECORDS = (
    (TARGETS_PATH, "417f727d018ecbfa86efb23ea8c9cdfc53d429cf3f4a6285543ae24e89fc40ea", 340997),
    (ESTATE_PATH, "b7ce1e66f343a480ac64f8b6259e108638dc1fe473607b77f728980846d6ca70", 429262),
)
MAX_SOURCE_BYTES = 4 * 1024 * 1024
# The SHA-256 of the generated document's canonical bytes. See the module
# docstring: this is the only place the digest is written.
WILDCAT_V2_REGISTRY_SHA256 = "1d206f36284ce51d0d23bf843899eef27316a36e5013c3df5d81da92e72ee29f"

EXPECTED_ROLE_COUNTS = {
    "collateral-factory": 1,
    "collateral-init-code-storage": 1,
    "collateral-lens": 1,
    "factory": 1,
    "fee-recipient": 1,
    "hooks-instance": 42,
    "hooks-template": 3,
    "lens": 2,
    "market": 80,
    "market-init-code-storage": 1,
    "registry": 1,
    "role-provider": 1,
    "sanctions-sentinel": 1,
    "wrapper-factory": 1,
}
SUBJECT_COUNT = sum(EXPECTED_ROLE_COUNTS.values())
# The one subject whose merged records carry a code length and digest but no
# creation block. A generated set that differs from this one is refused, so a
# second subject losing its block, or this one gaining one, is a reviewed
# change here rather than a silent change of epoch starts.
NO_CREATION_BLOCK = ("0xbbb998043a20a26828617769f37dc3980be25ebc",)

COMPACT_SORTED_JSON = "compact-sorted-json"
# The serialisation a row declares in `sha256_method`, mapped to the named
# form the registry records. A method absent from this table is refused.
DECLARED_METHODS = {
    "sha256 over json.dumps(sorted(lowercase addresses), separators=(',',':'))": COMPACT_SORTED_JSON,
}


def _compact_sorted_json(addresses) -> bytes:
    return json.dumps(sorted(addresses), separators=(",", ":")).encode("utf-8")


CANONICAL_FORMS = {COMPACT_SORTED_JSON: _compact_sorted_json}
LIST_DIGEST_NAMES = ("v2_markets_sha256", "hooks_instances_sha256", "registered_markets_sha256")
BLOCK_SOURCES = ("contract-record", "creation-epochs", "code-match")


def list_digest(addresses, form: str) -> str:
    """The SHA-256 of one address list under one named canonical form."""
    # A supplied registry names its form; a list or an object there is not a
    # name, and a membership test on one raises instead of refusing.
    if not isinstance(form, str) or form not in CANONICAL_FORMS:
        raise AlexandriaError(f"address-list canonical form {str(form)[:64]!r} is not recognised")
    return hashlib.sha256(CANONICAL_FORMS[form](addresses)).hexdigest()


def _address(value, label: str) -> str:
    if not isinstance(value, str) or ADDRESS_RE.fullmatch(value.lower()) is None:
        raise AlexandriaError(f"{label} is not an EVM address")
    return value.lower()


def _block(value, label: str):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AlexandriaError(f"{label} is not a block number")
    return value


def read_source(repo_root: Path, path: str, sha256: str, size: int):
    """One pinned record, refused by name when its bytes are not the pinned ones."""
    data = read_confined_file(Path(repo_root).absolute(), path, path, max_bytes=MAX_SOURCE_BYTES)
    actual = hashlib.sha256(data).hexdigest()
    if actual != sha256 or len(data) != size:
        raise AlexandriaError(
            f"source record {path} does not match its pin: {len(data)} bytes hashing to "
            f"{actual}, where {size} bytes hashing to {sha256} are pinned"
        )
    try:
        return json.loads(data)
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise AlexandriaError(f"source record {path} is not JSON") from error


def _deployment_block(contract, creation_epochs, label: str):
    """The subject's creation block and which record carries it, or a null pair.

    Three places record one: the contract entry itself (instances and
    markets), the estate record's `creation_epochs` (core contracts) and the
    entry's `code_match` (the pair shared with V1). Two that disagree refuse.
    """
    found = []
    if "deployment_block" in contract:
        found.append(("contract-record", contract["deployment_block"]))
    epoch = creation_epochs.get(contract["address"])
    if epoch is not None:
        if not isinstance(epoch, dict):
            raise AlexandriaError(f"{label} creation epoch has an unknown shape")
        found.append(("creation-epochs", epoch.get("block_number")))
    match = contract.get("code_match")
    if isinstance(match, dict) and "deployment_block" in match:
        found.append(("code-match", match["deployment_block"]))
    if not found:
        return None, None
    blocks = {_block(value, f"{label} deployment block") for _source, value in found}
    if len(blocks) != 1:
        raise AlexandriaError(f"{label} records disagree about its deployment block")
    return blocks.pop(), found[0][0]


def generate_v2_registry(repo_root: Path) -> dict:
    """Generate the Wildcat V2 registry from the two pinned merged records."""
    records = {}
    sources = []
    for path, sha256, size in SOURCE_RECORDS:
        records[path] = read_source(repo_root, path, sha256, size)
        sources.append({"bytes": size, "path": path, "sha256": sha256})
    targets, estate = records[TARGETS_PATH], records[ESTATE_PATH]
    # The registry record pins the estate record too; the two pins are one
    # fact written twice, so they are compared rather than trusted apart.
    declared = targets.get("evidence_digests") if isinstance(targets, dict) else None
    if not isinstance(declared, dict) or declared.get(ESTATE_PATH) != dict(
        (path, sha256) for path, sha256, _size in SOURCE_RECORDS
    )[ESTATE_PATH]:
        raise AlexandriaError(
            f"{TARGETS_PATH} pins another digest for {ESTATE_PATH} than this generator does"
        )
    rows = targets.get("targets")
    if not isinstance(rows, list):
        raise AlexandriaError(f"{TARGETS_PATH} carries no target list")
    # Iterate the target list directly; the file is large and deeply nested.
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == ROW_ID]
    if len(matches) != 1:
        raise AlexandriaError(f"{TARGETS_PATH} carries no single {ROW_ID} row")
    deployment = matches[0].get("deployment")
    if not isinstance(deployment, dict) or deployment.get("chain_id") != CHAIN_ID:
        raise AlexandriaError(f"the {ROW_ID} row is not an Ethereum mainnet deployment")
    contracts = deployment.get("contracts")
    instances = deployment.get("instances")
    start = deployment.get("start_block")
    if not isinstance(contracts, list) or not isinstance(instances, dict) or not isinstance(start, dict):
        raise AlexandriaError(f"the {ROW_ID} row has an unknown shape")
    creation_epochs = estate.get("creation_epochs") if isinstance(estate, dict) else None
    controller = estate.get("arch_controller") if isinstance(estate, dict) else None
    if not isinstance(creation_epochs, dict) or not isinstance(controller, dict):
        raise AlexandriaError(f"{ESTATE_PATH} has an unknown shape")

    entries = []
    seen = set()
    for position, contract in enumerate(contracts):
        label = f"{ROW_ID} contract {position}"
        if not isinstance(contract, dict):
            raise AlexandriaError(f"{label} is not an object")
        address = _address(contract.get("address"), f"{label} address")
        if address != contract["address"]:
            raise AlexandriaError(f"{label} address is not lowercase")
        if address in seen:
            raise AlexandriaError(f"{label} repeats {address}")
        seen.add(address)
        role = contract.get("role")
        if role not in EXPECTED_ROLE_COUNTS:
            raise AlexandriaError(f"{label} carries the unknown role {str(role)[:64]!r}")
        match = contract.get("code_match")
        commit = match.get("source_commit") if isinstance(match, dict) else None
        if not isinstance(commit, str) or not commit:
            raise AlexandriaError(f"{label} names no source commit")
        digest = contract.get("code_keccak256")
        if not isinstance(digest, str) or HASH_RE.fullmatch(digest) is None:
            raise AlexandriaError(f"{label} carries no runtime code keccak256")
        block, block_source = _deployment_block(contract, creation_epochs, label)
        entries.append({
            "address": address,
            "code_keccak256": digest,
            "code_length": _block(contract.get("code_length"), f"{label} code length"),
            "deployment_block": block,
            "deployment_block_source": block_source,
            "name": str(contract.get("name")),
            "observed_block_number": _block(
                contract.get("observed_block_number"), f"{label} observed block"
            ),
            "role": role,
            "source_commit": commit,
            "source_repository_private": "source_repository_visibility" in contract,
        })

    markets = [entry["address"] for entry in entries if entry["role"] == "market"]
    hooks = [entry["address"] for entry in entries if entry["role"] == "hooks-instance"]
    registered = controller.get("getRegisteredMarkets")
    derived_v1 = controller.get("v1_markets_derived")
    if not isinstance(registered, list) or not isinstance(derived_v1, list):
        raise AlexandriaError(f"{ESTATE_PATH} carries no registered-market list")
    registered = [_address(value, "registered market") for value in registered]
    derived_v1 = [_address(value, "derived V1 market") for value in derived_v1]
    if len(set(registered)) != len(registered) or set(markets) | set(derived_v1) != set(registered):
        raise AlexandriaError(
            "the registered markets are not exactly the row's V2 markets and the derived V1 markets"
        )
    form = DECLARED_METHODS.get(instances.get("sha256_method"))
    if form is None:
        raise AlexandriaError(
            f"the {ROW_ID} row declares an address-list digest method this generator does not name"
        )
    lists = {
        "v2_markets_sha256": (markets, "entries of role market"),
        "hooks_instances_sha256": (hooks, "entries of role hooks-instance"),
        "registered_markets_sha256": (registered, "registered_markets"),
    }
    digests = []
    for name in LIST_DIGEST_NAMES:
        addresses, members = lists[name]
        actual = list_digest(addresses, form)
        if actual != instances.get(name):
            raise AlexandriaError(
                f"the {ROW_ID} row records {name} {str(instances.get(name))[:64]}, which its "
                f"{len(addresses)} addresses do not reproduce under {form}; they hash to {actual}"
            )
        digests.append({
            "canonical_form": form,
            "count": len(addresses),
            "members": members,
            "name": name,
            "sha256": actual,
        })
    if controller.get("registered_markets_sha256") != instances.get("registered_markets_sha256"):
        raise AlexandriaError("the two records disagree about the registered-market digest")

    registry = {
        "chain_id": CHAIN_ID,
        "entries": entries,
        "format": REGISTRY_FORMAT,
        "list_digests": digests,
        "registered_markets": registered,
        "source": {"records": sources, "row": ROW_ID},
        "start_block": _block(start.get("number"), f"{ROW_ID} start block"),
        "venue": VENUE,
    }
    _validate_shape(registry)
    return registry


def registry_bytes(repo_root: Path) -> bytes:
    """The generated registry's canonical bytes, after they pass the pinned digest."""
    registry = generate_v2_registry(repo_root)
    validate_registry(registry)
    return canonical_bytes(registry)


def _validate_shape(registry) -> None:
    """What the pinned records must yield, checked on the document alone."""
    if not isinstance(registry, dict):
        raise AlexandriaError("Wildcat V2 registry has an unknown shape")
    # The format is read first, so another venue's registry is refused as
    # another format rather than as a malformed Wildcat one.
    if registry.get("format") != REGISTRY_FORMAT:
        raise AlexandriaError("Wildcat V2 registry format is unknown")
    if set(registry) != {
        "chain_id", "entries", "format", "list_digests", "registered_markets",
        "source", "start_block", "venue",
    }:
        raise AlexandriaError("Wildcat V2 registry has an unknown shape")
    if registry["venue"] != VENUE or registry["chain_id"] != CHAIN_ID:
        raise AlexandriaError("Wildcat V2 registry names another venue or chain")
    entries = registry["entries"]
    if not isinstance(entries, list) or len(entries) != SUBJECT_COUNT:
        raise AlexandriaError(f"Wildcat V2 registry must contain {SUBJECT_COUNT} subjects")
    counts = {}
    addresses = []
    unblocked = []
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {
            "address", "code_keccak256", "code_length", "deployment_block",
            "deployment_block_source", "name", "observed_block_number", "role",
            "source_commit", "source_repository_private",
        }:
            raise AlexandriaError("Wildcat V2 registry entry has an unknown shape")
        address = entry["address"]
        if not isinstance(address, str) or ADDRESS_RE.fullmatch(address) is None:
            raise AlexandriaError("Wildcat V2 registry entry is not keyed by a lowercase address")
        addresses.append(address)
        if not isinstance(entry["role"], str):
            raise AlexandriaError("Wildcat V2 registry entry role is not a name")
        counts[entry["role"]] = counts.get(entry["role"], 0) + 1
        block, source = entry["deployment_block"], entry["deployment_block_source"]
        if block is None:
            if source is not None:
                raise AlexandriaError(f"Wildcat V2 subject {address} names a source for no block")
            unblocked.append(address)
        else:
            _block(block, f"Wildcat V2 subject {address} deployment block")
            if source not in BLOCK_SOURCES:
                raise AlexandriaError(
                    f"Wildcat V2 subject {address} names no record for its deployment block"
                )
    if len(set(addresses)) != len(addresses):
        raise AlexandriaError("Wildcat V2 registry declares a subject twice")
    if counts != EXPECTED_ROLE_COUNTS:
        raise AlexandriaError("Wildcat V2 registry roles do not match the pinned estate")
    if tuple(sorted(unblocked)) != NO_CREATION_BLOCK:
        raise AlexandriaError(
            "Wildcat V2 registry subjects without a creation block are not the reviewed set"
        )
    _block(registry["start_block"], "Wildcat V2 registry start block")
    registered = registry["registered_markets"]
    if not isinstance(registered, list) or any(
        not isinstance(value, str) or ADDRESS_RE.fullmatch(value) is None for value in registered
    ):
        raise AlexandriaError("Wildcat V2 registry registered markets are not lowercase addresses")
    digests = registry["list_digests"]
    if not isinstance(digests, list) or [
        item.get("name") if isinstance(item, dict) else None for item in digests
    ] != list(LIST_DIGEST_NAMES):
        raise AlexandriaError("Wildcat V2 registry list digests are not the three the row records")
    members = {
        "v2_markets_sha256": [a for a, e in zip(addresses, entries) if e["role"] == "market"],
        "hooks_instances_sha256": [
            a for a, e in zip(addresses, entries) if e["role"] == "hooks-instance"
        ],
        "registered_markets_sha256": registered,
    }
    for item in digests:
        if set(item) != {"canonical_form", "count", "members", "name", "sha256"}:
            raise AlexandriaError("Wildcat V2 registry list digest has an unknown shape")
        if (
            not isinstance(item["sha256"], str)
            or CODE_DIGEST_RE.fullmatch(item["sha256"]) is None
            or item["count"] != len(members[item["name"]])
            or list_digest(members[item["name"]], item["canonical_form"]) != item["sha256"]
        ):
            raise AlexandriaError(
                f"Wildcat V2 registry {item['name']} does not reproduce under its recorded form"
            )
    source = registry["source"]
    if (
        not isinstance(source, dict)
        or set(source) != {"records", "row"}
        or source["row"] != ROW_ID
        or source["records"] != [
            {"bytes": size, "path": path, "sha256": sha256}
            for path, sha256, size in SOURCE_RECORDS
        ]
    ):
        raise AlexandriaError("Wildcat V2 registry source records do not match the pin")


def validate_registry(registry) -> None:
    """Refuse any document but the one the pinned records generate."""
    _validate_shape(registry)
    if hashlib.sha256(canonical_bytes(registry)).hexdigest() != WILDCAT_V2_REGISTRY_SHA256:
        raise AlexandriaError("Wildcat V2 registry bytes do not match the pinned registry")


def subject_entries(registry) -> dict:
    """The registry's entries keyed by subject address, in declared order."""
    return {entry["address"]: entry for entry in registry["entries"]}
