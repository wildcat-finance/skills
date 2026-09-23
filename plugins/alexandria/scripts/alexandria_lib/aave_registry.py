"""Pinned Aave V3 Ethereum main-market registry: generation and validation.

The merged `aave-v3` row of `docs/kickoff/1359/targets.json` lists 22 of the
market's 356 subjects and binds the whole set by a digest over its addresses.
The other 334 subjects, every creation block and transaction, and the token
proxies' implementation epochs are carried only by the two full records the
row pins by SHA-256 and byte count under `full_records`. Those records are not
in this repository. `generate` reads them from paths its caller names and
derives the registry document from them; `validate_registry` then checks any
registry document against `AAVE_V3_REGISTRY_SHA256` without either record.

The generator reads each full record through one no-follow open of the path
it is given: the final path component must not be a symbolic link, the file
must be a regular file of at most `MAX_FULL_RECORD_BYTES`, and its SHA-256 and
byte count must equal the row's pin before its bytes are parsed. Directories
above that final component are resolved as the operating system resolves
them. A mismatch names the record, the observed bytes and digest, and the
pinned ones. The generator runs no subprocess and opens no socket.

`targets.json` is shared with every other venue row, so it is pinned by the
canonical bytes of the `aave-v3` row alone, the way `wildcat_registry.ROW_PINS`
pins the two Wildcat rows: an edit to another row leaves this module's checks
unchanged, and a changed `aave-v3` row is refused by name. The row is found by
iterating the file's `targets` list, never by walking the document.

Subject roles are not recorded per address in the full records; they are
derived from the tables that name each subject. The market block names the
AddressesProvider, the Pool and PoolConfigurator proxies and the ACLManager;
`implementation_revisions` names each Pool, PoolConfigurator and token
implementation with its role; each reserve names its aToken, variable debt
token and, where it has one, stable debt token proxy, and its rate strategy
epochs name the strategies; `library_links` names the linked libraries. An
address given two roles, a subject given none and a derived address outside
the record's `code` array each refuse.

`AAVE_V3_REGISTRY_SHA256` is held in this module and nowhere else: no plan
field and no operator document can supply it, and the venue module re-exports
`validate_registry` rather than restating the digest.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys

from .canonical import MAX_LARGE_NODES, canonical_bytes, load_bytes
from .errors import AlexandriaError
from .interval import ADDRESS_RE, HASH_RE, MAX_EPOCHS
from .paths import read_confined_file
from .wildcat_registry import NEWLINE_JOINED_TRAILING, list_digest


REGISTRY_FORMAT = "alexandria-aave-v3-registry/v1"
VENUE = "aave-v3"
ROW_ID = "aave-v3"
CHAIN_ID = 1
TARGETS_PATH = "docs/kickoff/1359/targets.json"
MAX_TARGETS_BYTES = 4 * 1024 * 1024
# `targets.json` is checked through this one row: the SHA-256 of
# `canonical_bytes` of the `aave-v3` row, taken at this run's base,
# d162d0952782f09659370b6a554c9cd4511b8db9.
ROW_PINS = (
    ("aave-v3", "03c07d47cbae0d176b5498e93131a881c781a8f5abd55dcb747d0e14afbc1bc8"),
)
# The row's `full_records` keys, in the order the generator reads them.
FULL_RECORD_NAMES = ("observations", "source_match")
MAX_FULL_RECORD_BYTES = 4 * 1024 * 1024
# The SHA-256 of the generated document's canonical bytes. See the module
# docstring: this is the only place the digest is written.
AAVE_V3_REGISTRY_SHA256 = "f5689f9e2ce977689676e64c474847c8d123aa332608a5f276dd933f62480b86"

# The main market as the row's `deployment.market` records it.
MARKET = {
    "acl_manager": "0xc2aacf6553d20d1e9d78e365aaba8032af9c85b0",
    "addresses_provider": "0x2f39d218133afab8f2b819b1066c7e434ad94e9e",
    "pool": "0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2",
    "pool_configurator": "0x64b761d848206f447fe2dd461b0c635ec39ebb27",
}
EXPECTED_ROLE_COUNTS = {
    "aToken-implementation": 11,
    "aToken-proxy": 67,
    "acl-manager": 1,
    "addresses-provider": 1,
    "interest-rate-strategy": 71,
    "library": 70,
    "pool-configurator-implementation": 7,
    "pool-configurator-proxy": 1,
    "pool-implementation": 11,
    "pool-proxy": 1,
    "stableDebtToken-implementation": 2,
    "stableDebtToken-proxy": 36,
    "variableDebtToken-implementation": 10,
    "variableDebtToken-proxy": 67,
}
SUBJECT_COUNT = sum(EXPECTED_ROLE_COUNTS.values())
# The row's `full_subject_set.sha256`, reproduced by the generator and by
# `_validate_shape` under the form below.
SUBJECT_SET_SHA256 = "289bbdf765e2e66f335f46706269dfbcc63600108d0ef5eb22ba814ecbcf8d64"
# The serialisation the row declares in `full_subject_set.form`, mapped to the
# named form the registry records. A form absent from this table is refused.
DECLARED_FORMS = {
    "sha256 of the lowercase addresses of the full record's code array, sorted, "
    "newline-joined with a trailing newline": NEWLINE_JOINED_TRAILING,
}
# Each proxy role and the role every implementation it names must carry.
PROXY_ROLES = {
    "aToken-proxy": "aToken-implementation",
    "pool-configurator-proxy": "pool-configurator-implementation",
    "pool-proxy": "pool-implementation",
    "stableDebtToken-proxy": "stableDebtToken-implementation",
    "variableDebtToken-proxy": "variableDebtToken-implementation",
}
IMPLEMENTATION_ROLES = frozenset(PROXY_ROLES.values())
PROXY_COUNT = sum(EXPECTED_ROLE_COUNTS[role] for role in PROXY_ROLES)
# The market block's key for each of the four market subjects, and its role.
MARKET_ROLES = (
    ("addresses_provider", "addresses_provider", "addresses-provider"),
    ("pool", "pool_proxy", "pool-proxy"),
    ("pool_configurator", "pool_configurator_proxy", "pool-configurator-proxy"),
    ("acl_manager", "acl_manager", "acl-manager"),
)
# The row's `source.deployed_source_epochs` proxy names, and the full record's
# table for each.
MARKET_EPOCH_TABLES = (
    ("Pool", "pool", "pool_implementation_epochs"),
    ("PoolConfigurator", "pool_configurator", "pool_configurator_implementation_epochs"),
)
RESERVE_TOKENS = (
    ("a_token", "aToken-proxy"),
    ("variable_debt_token", "variableDebtToken-proxy"),
    ("stable_debt_token", "stableDebtToken-proxy"),
)
# The one address the full record lists both as a subject and under
# `periphery_not_subjects`. It stays a subject: it is inside the digest-bound
# set. A different overlap is a reviewed change here, not a silent one.
PERIPHERY_OVERLAP = (
    {
        "address": "0x102633152313c81cd80419b6ecf66d14ad68949a",
        "periphery": "mock_stable_debt",
        "role": "stableDebtToken-proxy",
    },
)
SOURCE_SET_RE = re.compile(r"^set-[0-9]{3}$")
TOP_FIELDS = frozenset({
    "chain_id", "entries", "format", "market", "observed_block", "periphery",
    "reserves", "source", "start_block", "subject_set", "venue",
})
ENTRY_FIELDS = frozenset({
    "address", "code_keccak256", "code_length", "creation_block", "creation_transaction",
    "implementations", "role", "source_set",
})
EPOCH_FIELDS = frozenset({"from_block", "implementation", "to_block", "transaction", "via"})
RESERVE_FIELDS = frozenset({"asset", "a_token", "stable_debt_token", "variable_debt_token"})


def _address(value, label: str) -> str:
    if not isinstance(value, str) or ADDRESS_RE.fullmatch(value) is None:
        raise AlexandriaError(f"{label} is not a lowercase EVM address")
    return value


def _hash(value, label: str) -> str:
    if not isinstance(value, str) or HASH_RE.fullmatch(value) is None:
        raise AlexandriaError(f"{label} is not a 32-byte hash")
    return value


def _block(value, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AlexandriaError(f"{label} is not a block number")
    return value


def _mapping(value, label: str) -> dict:
    if not isinstance(value, dict):
        raise AlexandriaError(f"{label} has an unknown shape")
    return value


def _list(value, label: str) -> list:
    if not isinstance(value, list):
        raise AlexandriaError(f"{label} has an unknown shape")
    return value


def subject_set_digest(addresses) -> str:
    """The SHA-256 of the addresses under the form the row records."""
    return list_digest(list(addresses), NEWLINE_JOINED_TRAILING)


def row_digest(row) -> str:
    """The SHA-256 of one target row's canonical bytes."""
    return hashlib.sha256(canonical_bytes(row)).hexdigest()


def find_row(targets) -> dict:
    """The one `aave-v3` row, found by iterating the document's target list."""
    rows = targets.get("targets") if isinstance(targets, dict) else None
    if not isinstance(rows, list):
        raise AlexandriaError(f"{TARGETS_PATH} carries no target list")
    matches = [row for row in rows if isinstance(row, dict) and row.get("id") == ROW_ID]
    if len(matches) != 1:
        raise AlexandriaError(f"{TARGETS_PATH} carries no single {ROW_ID} row")
    return matches[0]


def check_row_pin(row) -> None:
    """Refuse a row whose canonical bytes are not the pinned ones, naming both digests."""
    for row_id, expected in ROW_PINS:
        actual = row_digest(row)
        if row.get("id") != row_id or actual != expected:
            raise AlexandriaError(
                f"{TARGETS_PATH} row {row_id} does not match its pin: canonical bytes "
                f"hashing to {actual}, where {expected} is pinned"
            )


def read_row(repo_root: Path) -> dict:
    """The pinned `aave-v3` row, read from `targets.json` under `repo_root`."""
    data = read_confined_file(
        Path(repo_root).absolute(), TARGETS_PATH, TARGETS_PATH, max_bytes=MAX_TARGETS_BYTES
    )
    row = find_row(load_bytes(data, TARGETS_PATH, max_bytes=MAX_TARGETS_BYTES))
    check_row_pin(row)
    return row


def full_record_pins(row) -> dict:
    """Each full record's pinned SHA-256 and byte count, by name, from the row."""
    records = _mapping(row.get("full_records"), f"the {ROW_ID} row's full_records")
    pins = {}
    for name in FULL_RECORD_NAMES:
        record = _mapping(records.get(name), f"the {ROW_ID} row's {name} full record")
        sha256, size = record.get("sha256"), record.get("bytes")
        if not isinstance(sha256, str) or re.fullmatch(r"[0-9a-f]{64}", sha256) is None:
            raise AlexandriaError(f"the {ROW_ID} row pins no SHA-256 for its {name} full record")
        if isinstance(size, bool) or not isinstance(size, int) or not 0 < size <= MAX_FULL_RECORD_BYTES:
            raise AlexandriaError(f"the {ROW_ID} row pins no bounded byte count for its {name} full record")
        pins[name] = (sha256, size)
    return pins


def read_full_record(path, name: str, sha256: str, size: int):
    """One full record, parsed only after its bytes equal the row's pin.

    `path` is opened once without following a symbolic link in its final
    component; the descriptor must be a regular file no larger than
    `MAX_FULL_RECORD_BYTES`.
    """
    label = f"full record {name}"
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    if not getattr(os, "O_NOFOLLOW", 0):
        raise AlexandriaError("this platform cannot open a full record without following a link")
    try:
        descriptor = os.open(os.fspath(path), flags)
    except OSError as error:
        if error.errno == errno.ELOOP:
            raise AlexandriaError(f"{label} must not be a symbolic link") from error
        raise AlexandriaError(f"cannot open {label}: {error.strerror}") from error
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode):
            raise AlexandriaError(f"{label} must be a regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as handle:
            data = handle.read(MAX_FULL_RECORD_BYTES + 1)
    except OSError as error:
        raise AlexandriaError(f"cannot read {label}: {error.strerror}") from error
    finally:
        os.close(descriptor)
    if len(data) > MAX_FULL_RECORD_BYTES:
        raise AlexandriaError(f"{label} exceeds the {MAX_FULL_RECORD_BYTES}-byte limit")
    actual = hashlib.sha256(data).hexdigest()
    if actual != sha256 or len(data) != size:
        raise AlexandriaError(
            f"{label} does not match the {ROW_ID} row's pin: {len(data)} bytes hashing to "
            f"{actual}, where {size} bytes hashing to {sha256} are pinned"
        )
    return load_bytes(data, label, max_bytes=MAX_FULL_RECORD_BYTES, max_nodes=MAX_LARGE_NODES)


def _derive_roles(observations) -> dict:
    """Each subject's role, from the tables of the full record that name it."""
    roles = {}

    def assign(value, role, label):
        address = _address(value, label)
        if roles.setdefault(address, role) != role:
            raise AlexandriaError(
                f"subject {address} is given both role {roles[address]} and role {role}"
            )

    market = _mapping(observations.get("market"), "full record observations market")
    for _key, record_key, role in MARKET_ROLES:
        assign(market.get(record_key), role, f"market {record_key}")
    revisions = _mapping(
        observations.get("implementation_revisions"), "full record observations implementation_revisions"
    )
    for address, revision in revisions.items():
        role = revision.get("role") if isinstance(revision, dict) else None
        if role not in IMPLEMENTATION_ROLES:
            raise AlexandriaError(f"implementation {str(address)[:64]} carries no implementation role")
        assign(address, role, "implementation revision address")
    for position, reserve in enumerate(_list(observations.get("reserves"), "full record observations reserves")):
        label = f"reserve {position}"
        reserve = _mapping(reserve, label)
        for key, role in RESERVE_TOKENS:
            if key == "stable_debt_token" and reserve.get(key) is None:
                continue
            assign(reserve.get(key), role, f"{label} {key}")
        for epoch in _list(reserve.get("interest_rate_strategy_epochs"), f"{label} strategy epochs"):
            assign(_mapping(epoch, f"{label} strategy epoch").get("strategy"), "interest-rate-strategy", f"{label} strategy")
    links = _mapping(observations.get("library_links"), "full record observations library_links")
    for parent, libraries in links.items():
        for library in _mapping(libraries, f"library links of {str(parent)[:64]}"):
            assign(library, "library", "linked library")
    return roles


def _epochs(rows, label: str) -> list:
    epochs = []
    for position, row in enumerate(_list(rows, label)):
        row = _mapping(row, f"{label} {position}")
        to_block = row.get("to_block")
        epochs.append({
            "from_block": _block(row.get("from_block"), f"{label} {position} from block"),
            "implementation": _address(row.get("implementation"), f"{label} {position} implementation"),
            "to_block": None if to_block is None else _block(to_block, f"{label} {position} to block"),
            "transaction": _hash(row.get("tx"), f"{label} {position} transaction"),
            "via": str(row.get("via")),
        })
    return epochs


def derive_registry(row, observations, source_match) -> dict:
    """The registry document the pinned row and the two parsed full records yield."""
    check_row_pin(row)
    deployment = _mapping(row.get("deployment"), f"the {ROW_ID} row's deployment")
    if deployment.get("chain_id") != CHAIN_ID or observations.get("chain_id") != CHAIN_ID:
        raise AlexandriaError(f"the {ROW_ID} row or its observations are not Ethereum mainnet")
    start = _mapping(deployment.get("start_block"), f"the {ROW_ID} row's start block")
    observed = _mapping(deployment.get("observed_block"), f"the {ROW_ID} row's observed block")
    observed_number = _block(observed.get("number"), f"the {ROW_ID} row's observed block number")
    market = _mapping(observations.get("market"), "full record observations market")
    for key, record_key, _role in MARKET_ROLES:
        if market.get(record_key) != MARKET[key]:
            raise AlexandriaError(f"full record observations names another {record_key} than the main market's")

    codes = {}
    for position, item in enumerate(_list(observations.get("code"), "full record observations code")):
        item = _mapping(item, f"code entry {position}")
        address = _address(item.get("address"), f"code entry {position} address")
        if address in codes:
            raise AlexandriaError(f"code entry {position} repeats {address}")
        if item.get("block_number") != observed_number:
            raise AlexandriaError(f"code entry {position} was not read at the row's observed block")
        codes[address] = item
    roles = _derive_roles(observations)
    unassigned = sorted(set(codes) - set(roles))
    if unassigned:
        raise AlexandriaError(f"{len(unassigned)} subjects carry no role, the first {unassigned[0]}")
    outside = sorted(set(roles) - set(codes))
    if outside:
        raise AlexandriaError(f"{len(outside)} role-bearing addresses are outside the code array, the first {outside[0]}")

    summary = _mapping(observations.get("summary"), "full record observations summary")
    if summary.get("by_role") != EXPECTED_ROLE_COUNTS:
        raise AlexandriaError("full record observations summary counts other roles than this module pins")
    counts = {}
    for role in roles.values():
        counts[role] = counts.get(role, 0) + 1
    if counts != EXPECTED_ROLE_COUNTS:
        raise AlexandriaError("the derived roles do not match the pinned role counts")

    creation = _mapping(observations.get("creation"), "full record observations creation")
    members = {}
    for position, item in enumerate(_list(source_match.get("source_sets"), "full record source_match source_sets")):
        item = _mapping(item, f"source set {position}")
        set_id = item.get("id")
        if not isinstance(set_id, str) or SOURCE_SET_RE.fullmatch(set_id) is None:
            raise AlexandriaError(f"source set {position} carries no set identifier")
        reproduction = _mapping(item.get("reproduction"), f"source set {set_id} reproduction")
        for member in _list(reproduction.get("members"), f"source set {set_id} members"):
            member = _address(member, f"source set {set_id} member")
            if member not in codes:
                raise AlexandriaError(f"source set {set_id} names {member}, which is not a subject")
            if members.setdefault(member, set_id) != set_id:
                raise AlexandriaError(f"subject {member} is a member of two source sets")
    missing = sorted(set(codes) - set(members))
    if missing:
        raise AlexandriaError(f"{len(missing)} subjects belong to no source set, the first {missing[0]}")

    token_epochs = _mapping(
        observations.get("token_proxy_implementation_epochs"),
        "full record observations token_proxy_implementation_epochs",
    )
    implementations = {}
    for _name, key, table in MARKET_EPOCH_TABLES:
        implementations[MARKET[key]] = _epochs(observations.get(table), table)
    token_proxies = {address for address, role in roles.items() if role in PROXY_ROLES} - set(implementations)
    if set(token_epochs) != token_proxies:
        raise AlexandriaError("the token proxy epoch tables do not name exactly the token proxy subjects")
    for proxy in sorted(token_proxies):
        implementations[proxy] = _epochs(token_epochs[proxy], f"epochs of {proxy}")

    entries = []
    for address in sorted(codes):
        item = codes[address]
        made = _mapping(creation.get(address), f"creation of {address}")
        entries.append({
            "address": address,
            "code_keccak256": _hash(item.get("code_keccak256"), f"code keccak of {address}"),
            "code_length": _block(item.get("code_length"), f"code length of {address}"),
            "creation_block": _block(made.get("block"), f"creation block of {address}"),
            "creation_transaction": _hash(made.get("tx"), f"creation transaction of {address}"),
            "implementations": implementations.get(address),
            "role": roles[address],
            "source_set": members[address],
        })

    periphery = _mapping(observations.get("periphery_not_subjects"), "full record observations periphery")
    overlap, excluded = [], []
    for key in sorted(periphery):
        values = periphery[key] if isinstance(periphery[key], list) else [periphery[key]]
        for value in values:
            address = _address(value, f"periphery {key}")
            if address in roles:
                overlap.append({"address": address, "periphery": key, "role": roles[address]})
            else:
                excluded.append(address)

    reserves = []
    for position, reserve in enumerate(observations["reserves"]):
        reserves.append({
            "asset": _address(reserve.get("asset"), f"reserve {position} asset"),
            "a_token": reserve["a_token"],
            "stable_debt_token": reserve["stable_debt_token"],
            "variable_debt_token": reserve["variable_debt_token"],
        })

    records = []
    for name, (sha256, size) in full_record_pins(row).items():
        records.append({"bytes": size, "name": name, "sha256": sha256})
    registry = {
        "chain_id": CHAIN_ID,
        "entries": entries,
        "format": REGISTRY_FORMAT,
        "market": dict(MARKET),
        "observed_block": {
            "hash": _hash(observed.get("hash"), f"the {ROW_ID} row's observed block hash"),
            "number": observed_number,
        },
        "periphery": {"excluded": sorted(excluded), "overlap": overlap},
        "reserves": sorted(reserves, key=lambda reserve: reserve["asset"]),
        "source": {"full_records": records, "row": ROW_ID, "row_sha256": row_digest(row)},
        "start_block": {
            "hash": _hash(start.get("hash"), f"the {ROW_ID} row's start block hash"),
            "number": _block(start.get("number"), f"the {ROW_ID} row's start block number"),
        },
        "subject_set": {
            "by_role": dict(sorted(counts.items())),
            "canonical_form": NEWLINE_JOINED_TRAILING,
            "count": len(entries),
            "sha256": subject_set_digest(codes),
        },
        "venue": VENUE,
    }
    _validate_shape(registry)
    check_row_agreement(registry, row)
    return registry


def check_row_agreement(registry, row) -> None:
    """Refuse a registry that disagrees with the merged row, naming the field.

    Compared: the market, the start and observed blocks, the subject-set
    count, digest, form and role counts, each of the 22 listed contracts'
    address, role, code length, code keccak, observed block and deployment
    block, the Pool and PoolConfigurator epoch tables and the full-record pins.
    """
    deployment = _mapping(row.get("deployment"), f"the {ROW_ID} row's deployment")
    if _mapping(deployment.get("market"), f"the {ROW_ID} row's market") != registry["market"]:
        raise AlexandriaError(f"the registry names another market than the {ROW_ID} row")
    for key in ("start_block", "observed_block"):
        block = _mapping(deployment.get(key), f"the {ROW_ID} row's {key}")
        if {"hash": block.get("hash"), "number": block.get("number")} != registry[key]:
            raise AlexandriaError(f"the registry's {key} is not the {ROW_ID} row's")
    subject_set = _mapping(deployment.get("full_subject_set"), f"the {ROW_ID} row's full_subject_set")
    recorded = registry["subject_set"]
    if DECLARED_FORMS.get(subject_set.get("form")) != recorded["canonical_form"]:
        raise AlexandriaError(f"the registry's subject-set form is not the one the {ROW_ID} row declares")
    if subject_set.get("count") != recorded["count"]:
        raise AlexandriaError(
            f"the registry declares {recorded['count']} subjects, where the {ROW_ID} row "
            f"records {subject_set.get('count')}"
        )
    if subject_set.get("sha256") != recorded["sha256"]:
        raise AlexandriaError(
            f"the registry's subject set hashes to {recorded['sha256']}, where the {ROW_ID} "
            f"row records {str(subject_set.get('sha256'))[:64]}"
        )
    if subject_set.get("by_role") != recorded["by_role"]:
        raise AlexandriaError(f"the registry's role counts are not the {ROW_ID} row's by_role")
    if [
        {"bytes": size, "name": name, "sha256": sha256}
        for name, (sha256, size) in full_record_pins(row).items()
    ] != registry["source"]["full_records"]:
        raise AlexandriaError(f"the registry's full-record pins are not the {ROW_ID} row's")
    entries = subject_entries(registry)
    for position, contract in enumerate(_list(deployment.get("contracts"), f"the {ROW_ID} row's contracts")):
        contract = _mapping(contract, f"{ROW_ID} contract {position}")
        address = contract.get("address")
        entry = entries.get(address)
        if entry is None:
            raise AlexandriaError(f"{ROW_ID} contract {position} {str(address)[:64]} is not a registry subject")
        match = contract.get("code_match") if isinstance(contract.get("code_match"), dict) else {}
        for field, expected, actual in (
            ("role", contract.get("role"), entry["role"]),
            ("code length", contract.get("code_length"), entry["code_length"]),
            ("code keccak", contract.get("code_keccak256"), entry["code_keccak256"]),
            ("observed block", contract.get("observed_block_number"), registry["observed_block"]["number"]),
            ("deployment block", match.get("deployment_block"), entry["creation_block"]),
        ):
            if expected != actual:
                raise AlexandriaError(
                    f"registry subject {address} {field} {str(actual)[:80]} is not the {ROW_ID} "
                    f"row's {str(expected)[:80]}"
                )
    source = _mapping(row.get("source"), f"the {ROW_ID} row's source")
    listed = _list(source.get("deployed_source_epochs"), f"the {ROW_ID} row's deployed_source_epochs")
    for name, key, _table in MARKET_EPOCH_TABLES:
        expected = sorted(
            (
                item.get("from_block"), item.get("to_block"),
                item.get("implementation"), item.get("transaction"),
            )
            for item in listed if isinstance(item, dict) and item.get("proxy") == name
        )
        actual = sorted(
            (epoch["from_block"], epoch["to_block"], epoch["implementation"], epoch["transaction"])
            for epoch in entries[registry["market"][key]]["implementations"]
        )
        if expected != actual:
            raise AlexandriaError(f"the registry's {name} epochs are not the {ROW_ID} row's")


def _validate_entries(registry) -> dict:
    entries = registry["entries"]
    if not isinstance(entries, list) or len(entries) != SUBJECT_COUNT:
        raise AlexandriaError(f"Aave V3 registry must contain {SUBJECT_COUNT} subjects")
    by_address = {}
    counts = {}
    previous = ""
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != ENTRY_FIELDS:
            raise AlexandriaError("Aave V3 registry entry has an unknown shape")
        address = _address(entry["address"], "Aave V3 registry entry address")
        if address <= previous:
            raise AlexandriaError(f"Aave V3 registry subject {address} is out of order or repeated")
        previous = address
        role = entry["role"]
        if not isinstance(role, str) or role not in EXPECTED_ROLE_COUNTS:
            raise AlexandriaError(f"Aave V3 registry subject {address} carries an unknown role")
        counts[role] = counts.get(role, 0) + 1
        _hash(entry["code_keccak256"], f"Aave V3 subject {address} code keccak")
        _block(entry["code_length"], f"Aave V3 subject {address} code length")
        created = _block(entry["creation_block"], f"Aave V3 subject {address} creation block")
        if created > registry["observed_block"]["number"]:
            raise AlexandriaError(f"Aave V3 subject {address} is created after the observed block")
        _hash(entry["creation_transaction"], f"Aave V3 subject {address} creation transaction")
        if not isinstance(entry["source_set"], str) or SOURCE_SET_RE.fullmatch(entry["source_set"]) is None:
            raise AlexandriaError(f"Aave V3 subject {address} names no source set")
        if (role in PROXY_ROLES) != (entry["implementations"] is not None):
            raise AlexandriaError(f"Aave V3 subject {address} carries implementations against its role")
        by_address[address] = entry
    if counts != EXPECTED_ROLE_COUNTS:
        raise AlexandriaError("Aave V3 registry roles do not match the pinned role counts")
    return by_address


def _validate_implementations(by_address) -> None:
    named = set()
    for address, entry in by_address.items():
        epochs = entry["implementations"]
        if epochs is None:
            continue
        if not isinstance(epochs, list) or not 1 <= len(epochs) <= MAX_EPOCHS:
            raise AlexandriaError(f"Aave V3 proxy {address} records no bounded implementation table")
        expected_from = entry["creation_block"]
        for position, epoch in enumerate(epochs):
            label = f"Aave V3 proxy {address} epoch {position}"
            if not isinstance(epoch, dict) or set(epoch) != EPOCH_FIELDS:
                raise AlexandriaError(f"{label} has an unknown shape")
            implementation = _address(epoch["implementation"], f"{label} implementation")
            target = by_address.get(implementation)
            if target is None or target["role"] != PROXY_ROLES[entry["role"]]:
                raise AlexandriaError(
                    f"{label} names {implementation}, which is not a {PROXY_ROLES[entry['role']]} subject"
                )
            named.add(implementation)
            if _block(epoch["from_block"], f"{label} from block") != expected_from:
                raise AlexandriaError(f"{label} does not open where the previous epoch closes")
            _hash(epoch["transaction"], f"{label} transaction")
            if not isinstance(epoch["via"], str) or not epoch["via"]:
                raise AlexandriaError(f"{label} names no evidence it was read from")
            last = position == len(epochs) - 1
            if last:
                if epoch["to_block"] is not None:
                    raise AlexandriaError(f"{label} is the last epoch and is closed")
            else:
                end = _block(epoch["to_block"], f"{label} to block")
                if end < epoch["from_block"]:
                    raise AlexandriaError(f"{label} closes before it opens")
                expected_from = end + 1
    unnamed = sorted(
        address for address, entry in by_address.items()
        if entry["role"] in IMPLEMENTATION_ROLES and address not in named
    )
    if unnamed:
        raise AlexandriaError(f"Aave V3 implementation subject {unnamed[0]} is named by no proxy epoch")


def _validate_reserves(registry, by_address) -> None:
    reserves = registry["reserves"]
    if not isinstance(reserves, list):
        raise AlexandriaError("Aave V3 registry reserves have an unknown shape")
    seen = {role: set() for _key, role in RESERVE_TOKENS}
    previous = ""
    for reserve in reserves:
        if not isinstance(reserve, dict) or set(reserve) != RESERVE_FIELDS:
            raise AlexandriaError("Aave V3 registry reserve has an unknown shape")
        asset = _address(reserve["asset"], "Aave V3 reserve asset")
        if asset <= previous:
            raise AlexandriaError(f"Aave V3 reserve {asset} is out of order or repeated")
        previous = asset
        if asset in by_address:
            raise AlexandriaError(f"Aave V3 reserve asset {asset} is a subject")
        for key, role in RESERVE_TOKENS:
            token = reserve[key]
            if token is None and key == "stable_debt_token":
                continue
            entry = by_address.get(token) if isinstance(token, str) else None
            if entry is None or entry["role"] != role:
                raise AlexandriaError(f"Aave V3 reserve {asset} {key} is not a {role} subject")
            if token in seen[role]:
                raise AlexandriaError(f"Aave V3 {role} {token} serves two reserves")
            seen[role].add(token)
    for _key, role in RESERVE_TOKENS:
        if len(seen[role]) != EXPECTED_ROLE_COUNTS[role]:
            raise AlexandriaError(f"Aave V3 registry reserves do not name every {role} subject")


def _validate_shape(registry) -> None:
    """What the pinned records must yield, checked on the document alone."""
    if not isinstance(registry, dict):
        raise AlexandriaError("Aave V3 registry has an unknown shape")
    # The format is read first, so another venue's registry is refused as
    # another format rather than as a malformed Aave one.
    if registry.get("format") != REGISTRY_FORMAT:
        raise AlexandriaError("Aave V3 registry format is unknown")
    if set(registry) != TOP_FIELDS:
        raise AlexandriaError("Aave V3 registry has an unknown shape")
    if registry["venue"] != VENUE or registry["chain_id"] != CHAIN_ID:
        raise AlexandriaError("Aave V3 registry names another venue or chain")
    if registry["market"] != MARKET:
        raise AlexandriaError("Aave V3 registry names another market than the main market")
    for key in ("start_block", "observed_block"):
        block = registry[key]
        if not isinstance(block, dict) or set(block) != {"hash", "number"}:
            raise AlexandriaError(f"Aave V3 registry {key} has an unknown shape")
        _hash(block["hash"], f"Aave V3 registry {key} hash")
        _block(block["number"], f"Aave V3 registry {key} number")
    if registry["start_block"]["number"] > registry["observed_block"]["number"]:
        raise AlexandriaError("Aave V3 registry starts after its observed block")
    by_address = _validate_entries(registry)
    for key, _record_key, role in MARKET_ROLES:
        entry = by_address.get(MARKET[key])
        if entry is None or entry["role"] != role:
            raise AlexandriaError(f"Aave V3 registry does not declare the main market's {key} as {role}")
    subject_set = registry["subject_set"]
    if not isinstance(subject_set, dict) or set(subject_set) != {"by_role", "canonical_form", "count", "sha256"}:
        raise AlexandriaError("Aave V3 registry subject set has an unknown shape")
    if subject_set["canonical_form"] != NEWLINE_JOINED_TRAILING:
        raise AlexandriaError("Aave V3 registry subject set names another canonical form")
    if subject_set["count"] != SUBJECT_COUNT or subject_set["by_role"] != EXPECTED_ROLE_COUNTS:
        raise AlexandriaError("Aave V3 registry subject set counts are not the pinned ones")
    actual = subject_set_digest(by_address)
    if subject_set["sha256"] != actual or actual != SUBJECT_SET_SHA256:
        raise AlexandriaError(
            f"Aave V3 registry subjects hash to {actual}, where {SUBJECT_SET_SHA256} is pinned "
            f"and {str(subject_set['sha256'])[:64]} is recorded"
        )
    _validate_implementations(by_address)
    _validate_reserves(registry, by_address)
    periphery = registry["periphery"]
    if not isinstance(periphery, dict) or set(periphery) != {"excluded", "overlap"}:
        raise AlexandriaError("Aave V3 registry periphery has an unknown shape")
    if periphery["overlap"] != list(PERIPHERY_OVERLAP):
        raise AlexandriaError("Aave V3 registry periphery overlap is not the reviewed one")
    excluded = periphery["excluded"]
    if not isinstance(excluded, list) or not excluded or excluded != sorted(set(excluded)):
        raise AlexandriaError("Aave V3 registry excluded periphery is not a sorted address list")
    for address in excluded:
        if _address(address, "Aave V3 excluded periphery") in by_address:
            raise AlexandriaError(f"Aave V3 excluded periphery {address} is a subject")
    source = registry["source"]
    if (
        not isinstance(source, dict)
        or set(source) != {"full_records", "row", "row_sha256"}
        or source["row"] != ROW_ID
        or source["row_sha256"] != dict(ROW_PINS)[ROW_ID]
        or not isinstance(source["full_records"], list)
        or [item.get("name") if isinstance(item, dict) else None for item in source["full_records"]]
        != list(FULL_RECORD_NAMES)
    ):
        raise AlexandriaError("Aave V3 registry source does not name the pinned row and full records")


def validate_registry(registry) -> None:
    """Refuse any document but the one the pinned records generate, naming both digests."""
    _validate_shape(registry)
    actual = hashlib.sha256(canonical_bytes(registry)).hexdigest()
    if actual != AAVE_V3_REGISTRY_SHA256:
        raise AlexandriaError(
            f"Aave V3 registry bytes do not match AAVE_V3_REGISTRY_SHA256: they hash to "
            f"{actual}, where {AAVE_V3_REGISTRY_SHA256} is pinned"
        )


def subject_entries(registry) -> dict:
    """The registry's entries keyed by subject address, in declared order."""
    return {entry["address"]: entry for entry in registry["entries"]}


def generate(repo_root: Path, observations_path, source_match_path) -> tuple:
    """The registry and the pins it checked, from the pinned row and the two full records."""
    row = read_row(repo_root)
    pins = full_record_pins(row)
    paths = {"observations": observations_path, "source_match": source_match_path}
    documents = {name: read_full_record(paths[name], name, *pins[name]) for name in FULL_RECORD_NAMES}
    registry = derive_registry(row, documents["observations"], documents["source_match"])
    return registry, pins


def main(argv=None) -> int:
    """Write the registry's canonical bytes to a new file after they pass the pin."""
    parser = argparse.ArgumentParser(
        prog="alexandria_lib.aave_registry",
        description="Generate the Aave V3 registry from the two full records the aave-v3 row pins.",
    )
    parser.add_argument("--observations", required=True, type=Path)
    parser.add_argument("--source-match", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[4])
    arguments = parser.parse_args(argv)
    try:
        registry, pins = generate(arguments.repo_root, arguments.observations, arguments.source_match)
        validate_registry(registry)
        data = canonical_bytes(registry)
        descriptor = os.open(arguments.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
    except (AlexandriaError, OSError) as error:
        print(f"aave-registry: {error}", file=sys.stderr)
        return 1
    print(json.dumps({
        "full_records": [
            {"bytes": size, "name": name, "sha256": sha256} for name, (sha256, size) in pins.items()
        ],
        "registry_sha256": hashlib.sha256(data).hexdigest(),
        "row_sha256": registry["source"]["row_sha256"],
        "subjects": len(registry["entries"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
