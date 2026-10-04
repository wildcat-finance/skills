"""Synthetic V1/V2 releases exercise the real offline verification boundary."""

from copy import deepcopy
from contextlib import redirect_stderr
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
PLUGINS = PLUGIN.parent
sys.path.insert(0, str(PLUGIN / "scripts"))
sys.path.insert(0, str(PLUGINS / "alexandria" / "scripts"))

from tabularium_lib import wildcat_view as view  # noqa: E402
from tabularium_lib.core import TabulariumError, sha256_bytes  # noqa: E402
from alexandria_lib import wildcat_registry  # noqa: E402
from usdc_interval import Builder, Collector, Reconciler  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "wildcat_fixture_transport", PLUGINS / "alexandria/tests/test_usdc_interval.py"
)
_transport = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_transport)

BORROWER = "0x" + "11" * 20
PAYER = "0x" + "22" * 20
ASSET = "0x" + "33" * 20


def word(value):
    return int(value, 16).to_bytes(32, "big") if isinstance(value, str) else value.to_bytes(32, "big")


def encoded_terms(generation):
    head = 9 if generation == "wildcat-v1" else 10
    tails = []
    for text in (b"Synthetic market", b"sUSD"):
        tails.append(word(len(text)) + text.ljust(32, b"\0"))
    words = [word(head * 32), word(head * 32 + len(tails[0])), word(ASSET),
             word(10**24), word(1200), word(300), word(86400), word(2000), word(7200)]
    if generation == "wildcat-v2":
        words.append(word(0))
    return "0x" + b"".join(words + tails).hex()


def release_fixture(root, generation, *, edit=None):
    """Construct provider responses; no private archive bytes enter the fixture."""
    root = root.resolve()
    state = json.loads((PLUGINS / "alexandria/tests/fixtures/wildcat-interval-transport.json").read_bytes())[generation]
    if generation == "wildcat-v1":
        # The source fixture predates the factory. Move this synthetic interval
        # after it so a factory log has an epoch owner.
        start = 18743513
        state["blocks"] = {}
        state["plan"]["interval"] = {"start": str(start), "end": str(start + 39)}
        for index, shard in enumerate(state["plan"]["shards"]):
            shard["start"], shard["end"] = start + index * 20, start + index * 20 + 19
        state["plan"]["finality"]["block_number"] = str(start + 39)
        state["plan"]["finality"]["block_hash"] = "0x" + hashlib.sha256(f"usdc-interval-block:{start + 39}".encode()).hexdigest()
    registry_bytes = (wildcat_registry.registry_v1_bytes if generation == "wildcat-v1"
                      else wildcat_registry.registry_bytes)
    registry = json.loads(registry_bytes(PLUGINS.parent))
    entries = registry["entries"]
    subjects = set(state["plan"]["subjects"])
    market = next(e["address"] for e in entries if e["role"] == "market" and e["address"] in subjects)
    factory = next(e["address"] for e in entries if e["role"] == "factory" and e["address"] in subjects)
    controller = (next(e["address"] for e in entries if e["role"] == "controller" and e["address"] in subjects)
                  if generation == "wildcat-v1" else factory)
    transport = _transport.FixtureTransport(state)
    block = state["plan"]["shards"][0]["start"] + 1
    tx = transport.transactions(block)[0]

    def log(emitter, topic, data, index, topics=()):
        return {"address": emitter, "topics": [topic, *topics], "data": data,
                "blockNumber": hex(block), "blockHash": transport._hash(block),
                "transactionHash": tx, "transactionIndex": "0x0", "logIndex": hex(index),
                "removed": False}

    logs = []
    if generation == "wildcat-v1":
        logs.append(log(factory, view.CONTROLLER, "0x" + (word(BORROWER) + word(controller)).hex(), 0))
    topics = (["0x" + word(factory).hex()] if generation == "wildcat-v2" else []) + ["0x" + word(market).hex()]
    logs.extend([
        log(controller, view.DEPLOY[generation], encoded_terms(generation), 1, topics),
        log(market, view.BORROW, "0x" + word(123456789).hex(), 2),
        log(market, view.REPAY, "0x" + word(98765432).hex(), 3, ["0x" + word(PAYER).hex()]),
        log(market, view.CLOSE, "0x" + word(1800000000).hex(), 4),
    ])
    state["logs"] = {key: (logs if key == "0" else []) for key in state["logs"]}
    state["traces"] = {key: [] for key in state["traces"]}
    if generation == "wildcat-v2":
        selector = next(key for key, length in view.DEPLOY_CALLS.items() if length == 32)
        state["traces"]["0"] = [{
            "action": {"callType": "call", "from": BORROWER, "to": factory,
                       "input": selector + "00" * 320, "gas": "0x100000", "value": "0x0"},
            "result": {"output": "0x" + word(market).hex(), "gasUsed": "0x100"},
            "type": "call", "blockNumber": block, "blockHash": transport._hash(block),
            "transactionHash": tx, "transactionPosition": 0, "traceAddress": [0], "subtraces": 0,
        }]
    if edit:
        edit(state, registry)
    staging = root / "staging"
    staging.mkdir(parents=True)
    with redirect_stderr(io.StringIO()):
        Collector(state["plan"], staging, _transport.FixtureTransport(state), registry=registry).collect()
        Reconciler(state["plan"], staging, _transport.FixtureTransport(state),
                   "synthetic second provider", registry=registry).reconcile()
    output = root / "release"
    Builder(state["plan"], staging, registry, created_at="2026-09-24T00:00:00Z").build(output)
    return output


class WildcatViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name)
        cls.releases = {generation: release_fixture(cls.root / generation, generation)
                        for generation in ("wildcat-v1", "wildcat-v2")}

    def test_v2_registry_has_per_subject_source_commits(self):
        result = view.make_wildcat_view(self.releases["wildcat-v2"])
        self.assertEqual(result["source_commit"], view.PINS["wildcat-v2"])
        self.assertEqual(len(result["records"]), 4)

    def test_both_generations_map_native_values_and_keep_payer_separate(self):
        for generation, release in self.releases.items():
            with self.subTest(generation=generation), mock.patch.object(socket, "socket", side_effect=AssertionError("network")):
                result = view.make_wildcat_view(release)
            rows = {row["claim"]: row for row in result["records"]}
            self.assertEqual(set(rows), {"market_terms", "borrow", "repayment", "market_closed"})
            self.assertEqual(rows["borrow"]["values"]["amount"], "123456789")
            self.assertEqual(rows["repayment"]["values"]["amount"], "98765432")
            self.assertEqual(rows["repayment"]["values"]["payer"], PAYER)
            self.assertEqual(rows["repayment"]["borrower"], BORROWER)
            terms = rows["market_terms"]["values"]
            self.assertEqual(terms["annual_interest_bips"], "1200")
            self.assertEqual(terms["terms_at"], "deployment")
            self.assertNotIn("token_symbol", terms)
            self.assertNotIn("token_decimals", terms)
            self.assertEqual(rows["borrow"]["borrower_class"], view.DERIVED)
            self.assertEqual(rows["borrow"]["field_classes"]["amount"], view.OBSERVED)
            self.assertEqual(result["mapping_coverage"], "partial")

    def test_every_record_resolves_to_exact_preserved_bytes(self):
        for release in self.releases.values():
            result = view.make_wildcat_view(release)
            manifest = json.loads((release / "manifest.json").read_bytes())
            components = {c["name"]: c for c in manifest["components"]}
            for row in result["records"]:
                source = row["source"]
                component = components[source["component"]]
                self.assertEqual(component["sha256"], source["component_sha256"])
                journal = json.loads((release / component["object_path"]).read_bytes())
                index = int(source["journal_selector"].split("/")[2])
                raw = journal["records"][index]["response"]
                self.assertEqual("sha256:" + sha256_bytes(raw.encode()), source["response_sha256"])
                log = json.loads(raw)["result"][int(source["selector"].split("/")[2])]
                self.assertEqual(log, row["native"])

    def test_missing_binding_is_unsupported_not_a_payer_attribution(self):
        def edit(state, _registry):
            state["traces"] = {key: [] for key in state["traces"]}
        with tempfile.TemporaryDirectory() as directory:
            result = view.make_wildcat_view(release_fixture(Path(directory).resolve(), "wildcat-v2", edit=edit))
        self.assertEqual(len(result["records"]), 4)
        self.assertTrue(all(row["borrower"] is None for row in result["records"]))
        self.assertTrue(result["unattributed_markets"])

    def test_unavailable_state_never_becomes_zero_or_no_delinquency(self):
        result = view.make_wildcat_view(self.releases["wildcat-v1"])
        for name in ("market_standing", "delinquency_entered", "delinquency_cured", "withdrawal_batch_expired_unpaid"):
            self.assertIn(name, result["unsupported_fields"])
            self.assertNotIn(name, {row["claim"] for row in result["records"]})

    def test_view_is_deterministic_and_changed_output_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory).resolve() / "view.json"
            release = self.releases["wildcat-v1"]
            first = view.build_wildcat_view(release, target)
            self.assertEqual(first, view.build_wildcat_view(release, target))
            self.assertEqual(first, view.verify_wildcat_view(release, target))
            target.write_text("{}\n")
            with self.assertRaisesRegex(TabulariumError, "differs"):
                view.verify_wildcat_view(release, target)
            with self.assertRaisesRegex(TabulariumError, "different bytes"):
                view.build_wildcat_view(release, target)
            target.unlink()
            self.assertEqual(first, view.build_wildcat_view(release, target))

    def test_changed_source_and_output_inside_source_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve() / "release"
            shutil.copytree(self.releases["wildcat-v1"], root)
            manifest = json.loads((root / "manifest.json").read_bytes())
            component = next(c for c in manifest["components"] if c["name"] == "logs")
            (root / component["object_path"]).write_bytes(b"{}")
            with self.assertRaises(TabulariumError):
                view.make_wildcat_view(root)
            with self.assertRaisesRegex(TabulariumError, "outside"):
                view.build_wildcat_view(root, root / "view.json")

    def test_symlink_input_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            link = Path(directory).resolve() / "linked"
            link.symlink_to(self.releases["wildcat-v1"])
            with self.assertRaisesRegex(TabulariumError, "symlink"):
                view.make_wildcat_view(link)

    def test_noncanonical_event_data_is_refused(self):
        def edit(state, _registry):
            state["logs"]["0"][-2]["data"] += "00"
        with tempfile.TemporaryDirectory() as directory:
            release = release_fixture(Path(directory).resolve(), "wildcat-v1", edit=edit)
            with self.assertRaisesRegex(TabulariumError, "byte length"):
                view.make_wildcat_view(release)

    def test_invalid_dynamic_offsets_are_refused(self):
        log = {"topics": [view.DEPLOY["wildcat-v1"], "0x" + word(ASSET).hex()],
               "data": "0x" + word(0).hex() + encoded_terms("wildcat-v1")[66:]}
        with self.assertRaisesRegex(TabulariumError, "offset"):
            view._terms(log, "wildcat-v1")

    def test_record_budget_is_enforced(self):
        with mock.patch.object(view, "MAX_RECORDS", 1):
            with self.assertRaisesRegex(TabulariumError, "record budget"):
                view.make_wildcat_view(self.releases["wildcat-v1"])

    def test_failed_deployment_call_does_not_bind_a_borrower(self):
        def edit(state, _registry):
            trace = state["traces"]["0"][0]
            trace["error"] = "Reverted"
            trace.pop("result")
        with tempfile.TemporaryDirectory() as directory:
            result = view.make_wildcat_view(release_fixture(Path(directory).resolve(), "wildcat-v2", edit=edit))
        self.assertFalse(result["bindings"])

    def test_runtime_module_from_another_checkout_is_refused(self):
        import usdc_interval
        with mock.patch.object(usdc_interval, "__file__", "/elsewhere/usdc_interval.py"):
            with self.assertRaisesRegex(TabulariumError, "outside the sibling"):
                view.make_wildcat_view(self.releases["wildcat-v1"])

    def test_ambiguous_factory_calls_refuse_borrower_selection(self):
        def edit(state, _registry):
            duplicate = deepcopy(state["traces"]["0"][0])
            duplicate["traceAddress"] = [1]
            duplicate["action"]["from"] = PAYER
            state["traces"]["0"].append(duplicate)
        with tempfile.TemporaryDirectory() as directory:
            release = release_fixture(Path(directory).resolve(), "wildcat-v2", edit=edit)
            with self.assertRaisesRegex(TabulariumError, "ambiguous"):
                view.make_wildcat_view(release)


if __name__ == "__main__":
    unittest.main()
