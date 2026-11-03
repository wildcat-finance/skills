"""The Wildcat boundary value decoder on constructed fixtures.

Each fixture holds one market's storage words under the V1 or V2 layout and its
underlying token's balance word, proved under EIP-1186 against a constructed
header, with the recorded getter for every key. Every decoded value equals its
recorded getter, or carries the differing view the relation report names. A
proof that fails, a word the fixture does not prove, a set bit outside the
declared fields and an unnamed disagreement each refuse. The committed relation
reports, statements and releases are not touched.
"""

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from eth_hash.auto import keccak
from trie import HexaryTrie

from . import support
from .support import PLUGIN_ROOT, REPO_ROOT
from lazarus_lib.canonical import dump
from lazarus_lib.header import compute_header_hash
from lazarus_lib.hexvalue import encode_hex
from lazarus_lib.manifest import build_manifest, write_manifest
from lazarus_lib.records import make_rpc_record, write_proof_records, write_rpc_records
from lazarus_lib.rlp import encode

EXAMPLE = PLUGIN_ROOT / "examples" / "wildcat-boundary-v0"
spec = importlib.util.spec_from_file_location("wildcat_boundary_values", EXAMPLE / "values.py")
values = importlib.util.module_from_spec(spec)
spec.loader.exec_module(values)
slots = sys.modules["wildcat_slots"]

MARKET = "0x" + "aa" * 20
TOKEN = "0x" + "bb" * 20
ACCOUNTS = ["0x" + "c1" * 20, "0x" + "c2" * 20]
EXPIRY = 1_742_310_239
STATE = {
    "isClosed": 0, "maxTotalSupply": 10**24, "accruedProtocolFees": 12_345,
    "normalizedUnclaimedWithdrawals": 6_789, "scaledTotalSupply": 9 * 10**20,
    "scaledPendingWithdrawals": 4 * 10**18, "pendingWithdrawalExpiry": EXPIRY,
    "isDelinquent": 1, "timeDelinquent": 3_600, "protocolFeeBips": 1_000,
    "annualInterestBips": 1_200, "reserveRatioBips": 1_500,
    "scaleFactor": 1_050_000_000_000_000_000_000_000_000,
    "lastInterestAccruedTimestamp": 1_742_000_000,
}
SCALED = [7 * 10**18, 0]
BATCH = (4 * 10**18, 10**18, 2 * 10**18)
STATUS = (3 * 10**18, 5 * 10**17)
BALANCE = 123_456_789_000


def pack(fields, named):
    return sum(named[name] << (8 * offset) for name, offset, _ in fields)


def word_hex(value):
    return "0x" + format(value, "064x")


def abi(*items):
    return "0x" + "".join(format(item, "064x") for item in items)


class Construction:
    """One market's words, proofs and recorded getters, written as a fixture."""

    def __init__(self, generation):
        self.generation = generation
        layout = slots.LAYOUTS[generation]
        state = {k: v for k, v in STATE.items()
                 if generation == "v2" or k != "protocolFeeBips"}
        words = {}
        for slot_number, fields in values.state_fields(generation):
            words[slots.slot_hex(slot_number)] = pack(fields, state)
        for account, scaled in zip(ACCOUNTS, SCALED):
            approval = {"approval": 3} if generation == "v1" else {}
            words[slots.slot_hex(slots.mapping_slot(account, layout["accounts"]))] = pack(
                values.ACCOUNT_WORD[generation], {"scaledBalance": scaled, **approval})
        base = slots.mapping_slot(EXPIRY, layout["batches"])
        words[slots.slot_hex(base)] = BATCH[0] | BATCH[1] << 104
        words[slots.slot_hex(int.from_bytes(base, "big") + 1)] = BATCH[2]
        inner = slots.mapping_slot(EXPIRY, layout["statuses"])
        words[slots.slot_hex(slots.mapping_slot(ACCOUNTS[0], inner))] = STATUS[0] | STATUS[1] << 104
        words[slots.slot_hex(layout["fifo_head"])] = 0 | 1 << 128
        words[slots.slot_hex(slots.mapping_slot(0, layout["fifo_data"]))] = EXPIRY
        self.market_words = words
        balance_layout = {"order": "solidity", "base": 0}
        self.token_words = {"0x" + slots.balance_slot(MARKET, balance_layout).hex(): BALANCE}
        order = [n for _, fields in values.state_fields(generation) for n, _, _ in fields]
        self.getters = {
            "previousState()": abi(*(state[n] for n in order)),
            "totalAssets()": abi(BALANCE),
            "getUnpaidBatchExpiries()": abi(32, 1, EXPIRY),
        }
        self.keyed = [
            ("scaledBalanceOf(address)", (ACCOUNTS[0],), abi(SCALED[0])),
            ("scaledBalanceOf(address)", (ACCOUNTS[1],), abi(SCALED[1])),
            ("getWithdrawalBatch(uint32)", (EXPIRY,), abi(*BATCH)),
            ("getAccountWithdrawalStatus(address,uint32)", (ACCOUNTS[0], EXPIRY), abi(*STATUS)),
        ]
        self.population = {MARKET: {
            "accounts": list(ACCOUNTS), "batch_expiries": [EXPIRY],
            "account_batches": [{"account": ACCOUNTS[0], "expiry": EXPIRY}],
        }}
        self.probe = {
            "fifo": {MARKET: {"start_index": 0, "next_index": 1, "entries": 1}},
            "assets_per_market": {MARKET: TOKEN},
            "tokens": {TOKEN: {"balance_slot": balance_layout, "pointers": {}}},
        }
        proved = sorted(set(values.BATCH_ROWS) | set(values.STATUS_ROWS) | {
            "native.scaledBalance", "native.unpaidExpiries", "credit.totalAssets",
            "native.supply"} | {f"state.{n}" for n in order})
        self.relations = {"rows": [{"id": row, "class": "proved"} for row in proved]}

    def calls(self):
        out = [(sig, (), result) for sig, result in self.getters.items()] + self.keyed
        return [(sig, values.SELECTORS[sig] + "".join(slots.pad(a).hex() for a in args), r)
                for sig, args, r in out]

    def write(self, root: Path, *, corrupt_proof=False):
        root.mkdir()
        tries = {}
        accounts = {}
        for address, words in ((MARKET, self.market_words), (TOKEN, self.token_words)):
            storage = HexaryTrie({})
            for slot, value in words.items():
                if value:
                    storage[keccak(bytes.fromhex(slot[2:]))] = encode(
                        value.to_bytes(32, "big").lstrip(b"\0"))
            tries[address] = storage
            accounts[address] = encode([b"\x01", b"", storage.root_hash, keccak(b"\x60\x00")])
        state = HexaryTrie({})
        for address, leaf in accounts.items():
            state[keccak(bytes.fromhex(address[2:]))] = leaf

        def proof_hex(trie, key):
            return [encode_hex(encode(node)) for node in trie.get_proof(key)]

        header = support.genesis_header()
        header["state_root"] = header["rpc_result"]["stateRoot"] = encode_hex(state.root_hash)
        header["hash"] = header["rpc_result"]["hash"] = support.hash32("00")
        block_hash = encode_hex(compute_header_hash(header))
        header["hash"] = header["rpc_result"]["hash"] = block_hash
        proofs = []
        for address, words in ((MARKET, self.market_words), (TOKEN, self.token_words)):
            storage_proof = []
            for slot, value in sorted(words.items()):
                stated = value + 1 if corrupt_proof and address == MARKET and not storage_proof else value
                storage_proof.append({
                    "key": slot, "value": hex(stated),
                    "proof": proof_hex(tries[address], keccak(bytes.fromhex(slot[2:]))),
                })
            proofs.append({
                "schema_version": 1, "evidence": "proof-backed", "block_hash": block_hash,
                "address": address, "balance": "0x0", "nonce": "0x1",
                "code_hash": encode_hex(keccak(b"\x60\x00")),
                "storage_hash": encode_hex(tries[address].root_hash), "code": "0x6000",
                "account_proof": proof_hex(state, keccak(bytes.fromhex(address[2:]))),
                "storage_proof": storage_proof,
            })
        plan = support.sample_plan()
        plan["block"] = {"number": header["number"], "hash": block_hash,
                         "hash_source": "constructed offline test vector"}
        plan["proof_targets"] = [
            {"address": MARKET, "slots": sorted(self.market_words)},
            {"address": TOKEN, "slots": sorted(self.token_words)},
        ]
        records = []
        for index, (signature, data, result) in enumerate(self.calls()):
            params = [{"to": MARKET, "data": data}, block_hash]
            name = f"call-{index}"
            plan["requests"].append({"name": name, "method": "eth_call", "params": params,
                                     "required": True, "evidence": "recorded-rpc"})
            records.append(make_rpc_record("eth_call", params, required=True,
                                           evidence="recorded-rpc", result=result, name=name))
        records.append(make_rpc_record("eth_chainId", [], required=True,
                                       evidence="recorded-rpc", result="0x1", name="chain-id"))
        plan["limits"]["max_requests"] = 64
        dump(root / "plan.json", plan)
        dump(root / "header.json", header)
        write_rpc_records(root / "rpc.jsonl", records)
        write_proof_records(root / "proofs.jsonl", proofs)
        included = sum(1 for words in (self.market_words, self.token_words)
                       for value in words.values())
        manifest = build_manifest(
            root, ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl"),
            chain_id="0x1", block_number=header["number"], block_hash=block_hash,
            evidence_counts={"proof_backed": len(proofs) + included, "header_bound": 1,
                             "recorded_rpc": len(records)},
        )
        write_manifest(root, manifest)
        return root

    def decode(self, root):
        return values.decode_estate(self.generation, root, self.relations, [MARKET],
                                    self.population, self.probe)


class DecodedValueTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.scratch = Path(directory.name)

    def build(self, generation, name="fixture", **kwargs):
        construction = Construction(generation)
        return construction, construction.write(self.scratch / name, **kwargs)

    def test_every_value_equals_its_recorded_getter(self):
        for generation in ("v1", "v2"):
            with self.subTest(generation=generation):
                construction, root = self.build(generation, generation)
                report = construction.decode(root)
                self.assertEqual({v["recorded"] for v in report["values"]}, {"equal"})
                by_row = {(v["row"], v.get("account"), v.get("expiry")): v for v in report["values"]}
                self.assertEqual(by_row[("native.scaledBalance", ACCOUNTS[0], None)]["value"],
                                 str(SCALED[0]))
                self.assertEqual(by_row[("native.batch.scaledAmountBurned", None, EXPIRY)]["value"],
                                 str(BATCH[1]))
                self.assertEqual(
                    by_row[("native.account.normalizedAmountWithdrawn", ACCOUNTS[0], EXPIRY)]["value"],
                    str(STATUS[1]))
                self.assertEqual(by_row[("state.scaleFactor", None, None)]["value"],
                                 str(STATE["scaleFactor"]))
                self.assertEqual(by_row[("native.unpaidExpiries", None, None)]["value"], [str(EXPIRY)])
                self.assertEqual(by_row[("credit.totalAssets", None, None)]["value"], str(BALANCE))
                self.assertEqual(report["derived"][0]["row"], "native.supply")
                manifest = json.loads((root / "manifest.json").read_text())
                self.assertEqual(report["fixture_digest"], manifest["fixture_digest"])
                state_rows = 14 if generation == "v2" else 13
                self.assertEqual(len(report["values"]), state_rows + 2 + 3 + 2 + 1 + 1)

    def test_v1_account_word_packs_approval_below_the_balance(self):
        construction, root = self.build("v1")
        value = next(v for v in construction.decode(root)["values"]
                     if v["row"] == "native.scaledBalance" and v["account"] == ACCOUNTS[0])
        self.assertEqual(value["field"], {"offset": 1, "bytes": 13})
        self.assertNotIn("approval", {v["row"] for v in construction.decode(root)["values"]})

    def test_a_named_differing_view_is_kept_and_an_unnamed_one_refuses(self):
        construction = Construction("v2")
        simulated = (BATCH[0], BATCH[0], BATCH[2] + 9)
        construction.keyed[2] = ("getWithdrawalBatch(uint32)", (EXPIRY,), abi(*simulated))
        root = construction.write(self.scratch / "differs")
        with self.assertRaisesRegex(values.Refusal, "recorded getter returns"):
            construction.decode(root)
        for row in construction.relations["rows"]:
            if row["id"] in values.BATCH_ROWS:
                row["differing_recorded_view"] = [
                    {"market": MARKET, "expiry": EXPIRY, "differs": True}]
        recorded = {v["row"]: v["recorded"] for v in construction.decode(root)["values"]
                    if v["row"] in values.BATCH_ROWS}
        self.assertEqual(recorded["native.batch.scaledAmountBurned"], "differing-view-named")
        self.assertEqual(recorded["native.batch.scaledTotalAmount"], "equal")

    def test_a_failed_proof_refuses(self):
        construction, root = self.build("v2", corrupt_proof=True)
        with self.assertRaisesRegex(values.Refusal, "Lazarus refused"):
            construction.decode(root)

    def test_a_word_the_fixture_does_not_prove_refuses(self):
        construction = Construction("v2")
        root = construction.write(self.scratch / "missing")
        construction.population[MARKET]["accounts"].append("0x" + "c3" * 20)
        with self.assertRaisesRegex(values.Refusal, "proves no such word"):
            construction.decode(root)

    def test_a_field_wider_than_declared_refuses(self):
        for generation, kind in (("v2", "status"), ("v1", "boolean"), ("v2", "queue")):
            with self.subTest(kind=kind):
                construction = Construction(generation)
                layout = slots.LAYOUTS[generation]
                if kind == "status":
                    inner = slots.mapping_slot(EXPIRY, layout["statuses"])
                    slot = slots.slot_hex(slots.mapping_slot(ACCOUNTS[0], inner))
                    construction.market_words[slot] |= 1 << 240
                elif kind == "boolean":
                    construction.market_words[slots.slot_hex(layout["state"][2])] |= 2 << 240
                else:
                    slot = slots.slot_hex(slots.mapping_slot(0, layout["fifo_data"]))
                    construction.market_words[slot] |= 1 << 32
                root = construction.write(self.scratch / f"wide-{kind}")
                with self.assertRaisesRegex(values.Refusal, "declared fields|not a boolean"):
                    construction.decode(root)

    def test_a_component_changed_after_verify_refuses(self):
        construction, root = self.build("v2")
        original = values.read_confined_bytes

        def changed(fixture, name, **kwargs):
            data = original(fixture, name, **kwargs)
            return data + b" " if name == "proofs.jsonl" else data

        values.read_confined_bytes = changed
        try:
            with self.assertRaisesRegex(values.Refusal, "changed after Lazarus verified it"):
                construction.decode(root)
        finally:
            values.read_confined_bytes = original


class CommittedRecordTests(unittest.TestCase):
    def test_getter_selectors_are_the_value_maps(self):
        recorded = json.loads((REPO_ROOT / "docs/kickoff/1384/selectors.json").read_text())
        self.assertEqual(values.SELECTORS, {k: recorded[k] for k in values.SELECTORS})

    def test_cli_refuses_a_fixture_without_the_estate_and_an_existing_output(self):
        construction = Construction("v2")
        with tempfile.TemporaryDirectory() as directory:
            root = construction.write(Path(directory) / "fixture")
            out = Path(directory) / "values.json"
            command = [sys.executable, str(EXAMPLE / "values.py"), "--generation", "v2",
                       "--fixture", str(root), "--out", str(out)]
            refused = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
            self.assertEqual(refused.returncode, 2)
            self.assertFalse(out.exists())
            out.write_text("{}")
            again = subprocess.run(command, cwd=REPO_ROOT, capture_output=True, text=True)
            self.assertEqual(again.returncode, 2)
            self.assertIn("already exists", again.stderr)


if __name__ == "__main__":
    unittest.main()
