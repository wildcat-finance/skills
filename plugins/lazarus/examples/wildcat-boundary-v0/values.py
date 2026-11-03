#!/usr/bin/env python3
"""Decode every proved Wildcat boundary storage word into its value-map rows.

For one estate the generator verifies a fixture with Lazarus, then reads the
storage words it proves for the rows the relation report classes ``proved``
and decodes each field under the pinned market layout in ``wildcat_slots.py``.
Every value is keyed by market, and by account and batch expiry where the row
has them, in exact native units as a decimal string, and names the word and
byte range it came from. A word that packs several fields gives each field
under its own row; a field no row maps, such as V1's account approval, is
checked for width and not published.

Each value is held to the recorded getter for the same key. It must be equal
unless the relation report names that pair as a differing recorded view. The
recorded response stays recorded evidence; only the storage word is proved.
A proved row that no single storage field answers, because ``currentState()``
derives it or the market's code holds it, is listed under ``derived`` with the
proof entries the relation report already names.

It refuses a fixture Lazarus does not verify, component bytes other than the
ones verify checked, a derived word the fixture does not prove, a word with a
set bit outside its declared fields or a boolean above one, and a value that
disagrees with its recorded getter without a named differing view. It reaches
no network and writes only to a fresh ``--out``. No fixture byte is in this
repository, so the report is produced in custody beside the fixture.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "scripts"
for entry in (HERE, SCRIPTS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
from lazarus_lib.canonical import MAX_JSONL_BYTES  # noqa: E402
from lazarus_lib.errors import LazarusError  # noqa: E402
from lazarus_lib.paths import read_confined_bytes  # noqa: E402
from lazarus_lib.records import loads_proof_records, loads_rpc_records  # noqa: E402
from lazarus_lib.verifier import verify_fixture  # noqa: E402
from wildcat_slots import (  # noqa: E402
    LAYOUTS, STATE_WORD_0, STATE_WORD_1, STATE_WORD_2, balance_slot, mapping_slot, pad,
    slot_hex,
)

KICKOFF = Path("docs/kickoff/1384")
SCHEMA = "wildcat-boundary-values/v1"
BOOLEANS = {"isClosed", "isDelinquent"}
BATCH_WORD_0 = (("scaledTotalAmount", 0, 13), ("scaledAmountBurned", 13, 13))
BATCH_WORD_1 = (("normalizedAmountPaid", 0, 16),)
STATUS_WORD = (("scaledAmount", 0, 13), ("normalizedAmountWithdrawn", 13, 16))
FIFO_HEAD = (("startIndex", 0, 16), ("nextIndex", 16, 16))
FIFO_ENTRY = (("expiry", 0, 4),)
BALANCE_WORD = (("balance", 0, 32),)
ACCOUNT_WORD = {
    "v1": (("approval", 0, 1), ("scaledBalance", 1, 13)),
    "v2": (("scaledBalance", 0, 13),),
}
BATCH_ROWS = {
    "native.batch.scaledTotalAmount": (0, "scaledTotalAmount"),
    "native.batch.scaledAmountBurned": (0, "scaledAmountBurned"),
    "native.batch.normalizedAmountPaid": (1, "normalizedAmountPaid"),
}
STATUS_ROWS = {
    "native.account.scaledAmount": "scaledAmount",
    "native.account.normalizedAmountWithdrawn": "normalizedAmountWithdrawn",
}
SELECTORS = {
    "previousState()": "0x0c1e3fea",
    "scaledBalanceOf(address)": "0x1da24f3e",
    "getWithdrawalBatch(uint32)": "0xdbcd50b4",
    "getAccountWithdrawalStatus(address,uint32)": "0x02372c4f",
    "getUnpaidBatchExpiries()": "0x878eb921",
    "totalAssets()": "0x01e1d114",
}
DERIVED_REASON = (
    "no single storage field holds this value: currentState() derives it, or "
    "the market's code holds it; the relation report lists the proved entries "
    "it derives from"
)


class Refusal(Exception):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def state_fields(generation: str):
    """The four state words' declared fields, with their storage slots."""
    word_3 = LAYOUTS[generation]["state_word_3"]
    return list(zip(LAYOUTS[generation]["state"],
                    (STATE_WORD_0, STATE_WORD_1, STATE_WORD_2, word_3)))


def unpack_checked(word: int, fields, where: str) -> dict[str, int]:
    """Decode declared fields, refusing a bit outside them or a non-boolean."""
    covered = 0
    values = {}
    for name, offset, size in fields:
        mask = ((1 << (8 * size)) - 1) << (8 * offset)
        covered |= mask
        values[name] = (word & mask) >> (8 * offset)
        if name in BOOLEANS and values[name] > 1:
            raise Refusal(f"{where}: {name} is {values[name]}, not a boolean")
    if word & ~covered:
        raise Refusal(f"{where}: bits outside the declared fields are set")
    return values


def abi_words(result: str) -> list[int]:
    body = result[2:]
    if not result.startswith("0x") or len(body) % 64:
        raise Refusal("recorded getter result is not whole ABI words")
    return [int(body[i:i + 64], 16) for i in range(0, len(body), 64)]


class Estate:
    """One verified fixture's proved words and recorded calls."""

    def __init__(self, fixture: Path):
        try:
            report = verify_fixture(fixture)
            claims = {item["path"]: item for item in report["manifest"]["components"]}
            components = {
                name: read_confined_bytes(fixture, name, max_bytes=MAX_JSONL_BYTES)
                for name in ("proofs.jsonl", "rpc.jsonl")
            }
        except LazarusError as exc:
            raise Refusal(f"Lazarus refused the fixture: {exc}") from None
        for name, data in components.items():
            if sha256_bytes(data) != claims[name]["sha256"]:
                raise Refusal(f"{name} changed after Lazarus verified it")
        self.report = report
        self.words: dict[tuple[str, str], int] = {}
        for record in loads_proof_records(components["proofs.jsonl"]):
            address = record["address"].lower()
            for item in record["storage_proof"]:
                slot = slot_hex(int(item["key"], 16))
                self.words[(address, slot)] = int(item["value"], 16)
        self.calls: dict[tuple[str, str], str] = {}
        for record in loads_rpc_records(components["rpc.jsonl"]):
            if record["method"] == "eth_call" and "result" in record["outcome"]:
                call = record["params"][0]
                self.calls[(call["to"].lower(), call["data"].lower())] = record["outcome"]["result"]

    def word(self, address: str, slot: str) -> int:
        try:
            return self.words[(address, slot)]
        except KeyError:
            raise Refusal(f"{address}:{slot}: the fixture proves no such word") from None

    def call(self, market: str, signature: str, *arguments) -> list[int] | None:
        data = SELECTORS[signature] + "".join(pad(a).hex() for a in arguments)
        result = self.calls.get((market, data))
        return None if result is None else abi_words(result)


def differing_views(relations: dict) -> set[tuple[str, str, str, str]]:
    """Row, market, expiry and account of each pair the report names."""
    named = set()
    for row in relations["rows"]:
        for view in row.get("differing_recorded_view", ()):
            if view.get("differs"):
                accounts = view.get("accounts") or [""]
                for account in accounts:
                    named.add((row["id"], view["market"].lower(), str(view["expiry"]), account))
    return named


def decode_estate(generation: str, fixture: Path, relations: dict, markets: list[str],
                  population: dict, probe: dict) -> dict:
    estate = Estate(fixture)
    proved = {row["id"] for row in relations["rows"] if row["class"] == "proved"}
    named = differing_views(relations)
    layout = LAYOUTS[generation]
    values: list[dict] = []
    decoded_rows: set[str] = set()

    def publish(row, value, key, words, view, field=None):
        if row not in proved:
            return
        recorded = "absent"
        if view is not None:
            if view == value:
                recorded = "equal"
            elif (row, key["market"], str(key.get("expiry", "")), "") in named:
                recorded = "differing-view-named"
            else:
                raise Refusal(f"{row} {key}: decoded {value} but the recorded getter returns {view}")
        entry = {"row": row, **key, "value": value_text(value), "words": words,
                 "recorded": recorded}
        if field is not None:
            entry["field"] = {"offset": field[0], "bytes": field[1]}
        values.append(entry)
        decoded_rows.add(row)

    for market in markets:
        members = population[market]
        key = {"market": market}
        state_values = {}
        offsets = {}
        state_words = []
        for slot_number, fields in state_fields(generation):
            slot = slot_hex(slot_number)
            state_words.append({"address": market, "slot": slot})
            state_values.update(unpack_checked(estate.word(market, slot), fields,
                                               f"{market}:{slot}"))
            offsets.update({name: (slot, offset, size) for name, offset, size in fields})
        view = estate.call(market, "previousState()")
        order = [name for _, fields in state_fields(generation) for name, _, _ in fields]
        for position, name in enumerate(order):
            slot, offset, size = offsets[name]
            publish(f"state.{name}", state_values[name], key,
                    [{"address": market, "slot": slot}],
                    None if view is None else view[position], (offset, size))

        for account in members["accounts"]:
            slot = slot_hex(mapping_slot(account, layout["accounts"]))
            fields = unpack_checked(estate.word(market, slot), ACCOUNT_WORD[generation],
                                    f"{market}:{slot}")
            view = estate.call(market, "scaledBalanceOf(address)", account)
            offset = layout["account_scaled_offset"]
            publish("native.scaledBalance", fields["scaledBalance"],
                    {"market": market, "account": account.lower()},
                    [{"address": market, "slot": slot}],
                    None if view is None else view[0], (offset, 13))

        for expiry in members["batch_expiries"]:
            base = mapping_slot(expiry, layout["batches"])
            slots = (slot_hex(base), slot_hex(int.from_bytes(base, "big") + 1))
            batch = [unpack_checked(estate.word(market, slots[0]), BATCH_WORD_0,
                                    f"{market}:{slots[0]}"),
                     unpack_checked(estate.word(market, slots[1]), BATCH_WORD_1,
                                    f"{market}:{slots[1]}")]
            view = estate.call(market, "getWithdrawalBatch(uint32)", expiry)
            for position, (row, (index, name)) in enumerate(BATCH_ROWS.items()):
                field = next(f for f in (BATCH_WORD_0, BATCH_WORD_1)[index] if f[0] == name)
                publish(row, batch[index][name], {"market": market, "expiry": int(expiry)},
                        [{"address": market, "slot": slots[index]}],
                        None if view is None else view[position], field[1:])

        for pair in members["account_batches"]:
            inner = mapping_slot(pair["expiry"], layout["statuses"])
            slot = slot_hex(mapping_slot(pair["account"], inner))
            status = unpack_checked(estate.word(market, slot), STATUS_WORD, f"{market}:{slot}")
            view = estate.call(market, "getAccountWithdrawalStatus(address,uint32)",
                               pair["account"], pair["expiry"])
            for position, (row, name) in enumerate(STATUS_ROWS.items()):
                field = next(f for f in STATUS_WORD if f[0] == name)
                publish(row, status[name],
                        {"market": market, "account": pair["account"].lower(),
                         "expiry": int(pair["expiry"])},
                        [{"address": market, "slot": slot}],
                        None if view is None else view[position], field[1:])

        head_slot = slot_hex(layout["fifo_head"])
        head = unpack_checked(estate.word(market, head_slot), FIFO_HEAD, f"{market}:{head_slot}")
        recorded = probe["fifo"][market]
        if (head["startIndex"], head["nextIndex"]) != (int(recorded["start_index"]),
                                                        int(recorded["next_index"])):
            raise Refusal(f"{market}: the proved queue head is not the one the plan derived")
        words = [{"address": market, "slot": head_slot}]
        expiries = []
        for index in range(head["startIndex"], head["nextIndex"]):
            slot = slot_hex(mapping_slot(index, layout["fifo_data"]))
            words.append({"address": market, "slot": slot})
            expiries.append(unpack_checked(estate.word(market, slot), FIFO_ENTRY,
                                           f"{market}:{slot}")["expiry"])
        view = estate.call(market, "getUnpaidBatchExpiries()")
        if view is not None:
            if len(view) < 2 or view[0] != 32 or len(view) != 2 + view[1]:
                raise Refusal(f"{market}: getUnpaidBatchExpiries() is not one uint32 array")
            view = view[2:]
        publish("native.unpaidExpiries", expiries, key, words, view)

        asset = probe["assets_per_market"].get(market)
        if asset is not None:
            token = asset.lower()
            slot = "0x" + balance_slot(market, probe["tokens"][asset]["balance_slot"]).hex()
            balance = unpack_checked(estate.word(token, slot), BALANCE_WORD, f"{token}:{slot}")
            view = estate.call(market, "totalAssets()")
            publish("credit.totalAssets", balance["balance"], key,
                    [{"address": token, "slot": slot}],
                    None if view is None else view[0], (0, 32))

    derived = [{"row": row, "reason": DERIVED_REASON}
               for row in sorted(proved - decoded_rows)]
    return {
        "schema": SCHEMA,
        "generation": generation,
        "block": {"number": estate.report["block_number"], "hash": estate.report["block_hash"]},
        "fixture_digest": estate.report["fixture_digest"],
        "evidence": (
            "every value is a field of a storage word the fixture proves under EIP-1186; "
            "recorded says how the recorded getter for the same key compares and is never proof"
        ),
        "rows": sorted(decoded_rows),
        "derived": derived,
        "values": values,
    }


def value_text(value):
    return [str(item) for item in value] if isinstance(value, list) else str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--generation", choices=("v1", "v2"), required=True)
    parser.add_argument("--fixture", type=Path, required=True,
                        help="the estate's fixture directory, as its release tree holds it")
    parser.add_argument("--out", type=Path, required=True,
                        help="a fresh path in an existing directory; never a symlink")
    args = parser.parse_args()

    def refuse(message):
        print(f"refusing: {message}", file=sys.stderr)
        return 2

    if not (KICKOFF / "values.json").is_file():
        return refuse(f"{KICKOFF}/values.json is not here; run from the repository root")
    if args.out.is_symlink() or os.path.lexists(args.out):
        return refuse(f"{args.out} already exists or is a symlink")
    if not args.out.parent.is_dir():
        return refuse(f"{args.out.parent} is not a directory")
    if args.fixture.is_symlink() or not args.fixture.is_dir():
        return refuse(f"{args.fixture} is not a directory")
    relations = read_json(HERE / f"relations-{args.generation}.json")
    scope = read_json(KICKOFF / "scope.json")
    markets = [s["address"].lower() for s in scope["subjects"][args.generation]
               if s["role"] == "market"]
    population = read_json(KICKOFF / "population.json")[args.generation]
    probe = read_json(HERE / f"probe-{args.generation}.json")
    try:
        report = decode_estate(args.generation, args.fixture, relations, markets,
                               population, probe)
    except Refusal as exc:
        return refuse(str(exc))
    if report["fixture_digest"] != relations["capture_record"]["fixture_digest"]:
        return refuse("the fixture is not the one the relation report was built beside")
    encoded = json.dumps(report, indent=1, sort_keys=True).encode("utf-8") + b"\n"
    with open(args.out, "xb") as handle:
        handle.write(encoded)
    print(json.dumps({
        "generation": args.generation,
        "values": len(report["values"]),
        "rows": len(report["rows"]),
        "derived": len(report["derived"]),
        "bytes": len(encoded),
        "sha256": sha256_bytes(encoded),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
