"""Collecting a bounded interval: bounds, refusals, resume and reorg rewind."""

from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
import urllib.request


PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import (  # noqa: E402
    DISPUTE_KINDS,
    EVIDENCE_CLASSES,
    IMPLEMENTATION_SLOT,
    JOURNAL_CLASSES,
    OPENING_CLASS,
    Staging,
    plan_digest,
    validate_checkpoint,
)
import usdc_interval  # noqa: E402
from usdc_interval import (  # noqa: E402
    CODE_COMPONENT,
    Builder,
    Collector,
    HttpsTransport,
    Reconciler,
    TransportError,
    check_interval,
    opening_identifier,
    request_identifier,
)


FIXTURE = PLUGIN / "tests" / "fixtures" / "usdc-interval-transport.json"
ENDPOINT = "https://fixture.invalid/rpc-with-a-secret-token"


def fixture():
    if not FIXTURE.is_file():
        raise AssertionError(
            f"the interval transport fixture is missing at {FIXTURE}; this suite proves "
            "the collector end to end and must fail rather than skip without it"
        )
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FixtureTransport:
    """Answers from preserved chain state, never from a socket."""

    def __init__(self, state, *, reorg_from=None, faults=None, finalized_number=None):
        self.state = state
        self.reorg_from = reorg_from
        self.faults = dict(faults or {})
        self.calls = []
        # Where the provider's `finalized` and `safe` tags stand. None means
        # the plan's own boundary; a live tag moves past it every epoch.
        self.finalized_number = finalized_number

    def _hash(self, number):
        """A finalized boundary does not reorg, so the fixture never moves it."""
        final = int(self.state["plan"]["finality"]["block_number"])
        if self.reorg_from is not None and self.reorg_from <= number < final:
            return "0x" + f"{number:064x}"
        known = self.state["blocks"].get(str(number))
        if known is not None:
            return known
        return "0x" + hashlib.sha256(f"usdc-interval-block:{number}".encode()).hexdigest()

    def transactions(self, number):
        """A deterministic, ordered transaction list for one block."""
        return [
            "0x" + hashlib.sha256(f"usdc-interval-blocktx:{number}:{position}".encode()).hexdigest()
            for position in range(2)
        ]

    def _shard_for(self, end):
        for shard in self.state["plan"]["shards"]:
            if shard["end"] == end:
                return shard
        return None

    def request(self, payload, label):
        envelope = json.loads(payload)
        self.calls.append((envelope["method"], label))
        fault = self.faults.get(label)
        if fault is not None:
            return fault if isinstance(fault, bytes) else fault(envelope)
        method = envelope["method"]
        identifier = envelope["id"]
        if method == "eth_getBlockByNumber":
            tag = envelope["params"][0]
            if tag in ("finalized", "safe"):
                number = self.finalized_number
                if number is None:
                    number = int(self.state["plan"]["finality"]["block_number"])
            else:
                number = int(tag, 16)
            result = {
                "hash": self._hash(number),
                "number": hex(number),
                "transactions": self.transactions(number),
            }
        elif method == "eth_getLogs":
            shard = self._shard_for(int(envelope["params"][0]["toBlock"], 16))
            result = self.logs(shard)
        elif method == "trace_filter":
            shard = self._shard_for(int(envelope["params"][0]["toBlock"], 16))
            result = self.state["traces"][str(shard["index"])]
        elif method == "eth_getStorageAt":
            proxy, slot, tag = envelope["params"]
            if proxy != self.state["plan"]["proxy"] or slot != IMPLEMENTATION_SLOT:
                raise AssertionError(f"unexpected storage read {envelope['params']}")
            result = self.slot_word(int(tag, 16))
        elif method == "eth_getCode":
            address, tag = envelope["params"]
            result = self.code(address, int(tag, 16))
        else:
            raise AssertionError(f"the fixture answers no {method}")
        return canonical_bytes({"id": identifier, "jsonrpc": "2.0", "result": result})

    def logs(self, shard):
        """One shard's logs; under a reorg each log names the block hash the new chain has."""
        records = deepcopy(self.state["logs"][str(shard["index"])])
        if self.reorg_from is not None:
            for record in records:
                record["blockHash"] = self._hash(int(record["blockNumber"], 16))
        return records

    def slot_word(self, number):
        return self.state["slots"][str(number)]

    def code(self, address, _number):
        return self.state["code"][address]


def journals(root):
    return {
        name: (Path(root) / "journals" / f"{name}.jsonl").read_bytes()
        for name in JOURNAL_CLASSES
        if (Path(root) / "journals" / f"{name}.jsonl").is_file()
    }


def opening_entries(root):
    path = Path(root) / "journals" / f"{OPENING_CLASS}.jsonl"
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_bytes().splitlines() if line]


def checkpoint(root):
    return json.loads((Path(root) / "checkpoint.json").read_text())


class _Killed(Exception):
    pass


class KillingTransport(FixtureTransport):
    """Stops the collection at a chosen request, the way a killed process would."""

    def __init__(self, state, *, kill_at, **kwargs):
        super().__init__(state, **kwargs)
        self.kill_at = kill_at

    def request(self, payload, label):
        if label == self.kill_at:
            raise _Killed(label)
        return super().request(payload, label)


class CollectorTestCase(unittest.TestCase):
    def setUp(self):
        self.state = fixture()
        self.plan = self.state["plan"]
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def collect(self, root=None, transport=None, plan=None):
        collector = Collector(plan or self.plan, root or self.root, transport or FixtureTransport(self.state))
        return collector, collector.collect()

    def scratch(self, name):
        """A named directory under this case's own temporary root."""
        root = self.root / name
        root.mkdir()
        return root

    def receipts(self, root=None):
        path = (root or self.root) / "receipts" / "errors.jsonl"
        if not path.is_file():
            return []
        return [json.loads(line) for line in path.read_bytes().splitlines() if line]


class CollectionTests(CollectorTestCase):
    def test_a_clean_collection_walks_every_shard(self):
        _collector, summary = self.collect()
        self.assertEqual(summary["shards"], 5)
        self.assertEqual(summary["collected_shards"], 5)
        self.assertEqual(summary["resumed_from"], 0)
        self.assertEqual(summary["record_counts"], {"boundary-blocks": 5, "logs": 15, "traces": 10})
        self.assertEqual(sorted(journals(self.root)), sorted(JOURNAL_CLASSES))

    def test_the_checkpoint_names_the_last_accepted_boundary(self):
        self.collect()
        checkpoint = json.loads((self.root / "checkpoint.json").read_text())
        last = self.plan["shards"][-1]
        self.assertEqual(checkpoint["next_shard"], 5)
        self.assertEqual(checkpoint["last_accepted"]["block_number"], str(last["end"]))
        self.assertEqual(
            checkpoint["last_accepted"]["block_hash"], self.state["blocks"][str(last["end"])]
        )
        self.assertEqual(len(checkpoint["history"]), 5)

    def test_request_ids_are_derived_from_the_plan(self):
        self.assertEqual(request_identifier(0, "boundary-blocks"), 1)
        self.assertEqual(request_identifier(1, "boundary-blocks"), 4)
        self.assertNotEqual(request_identifier(0, "logs"), request_identifier(1, "logs"))

    def test_a_finality_boundary_that_disagrees_with_the_plan_refuses(self):
        plan = deepcopy(self.plan)
        plan["finality"]["block_hash"] = "0x" + "ee" * 32
        with self.assertRaisesRegex(AlexandriaError, "does not match the plan"):
            self.collect(plan=plan)

    def test_each_finality_policy_binds_its_own_boundary(self):
        for policy in ("finalized", "safe"):
            with self.subTest(policy=policy):
                root = self.scratch(policy)
                plan = deepcopy(self.plan)
                plan["finality"]["policy"] = policy
                collector = Collector(plan, root, FixtureTransport(self.state))
                collector.collect()
                self.assertEqual(collector.plan["finality"]["policy"], policy)
        root = self.scratch("confirmations")
        plan = deepcopy(self.plan)
        plan["finality"] = {
            "block_hash": plan["finality"]["block_hash"],
            "block_number": plan["finality"]["block_number"],
            "confirmations": 64,
            "policy": "confirmations",
        }
        collector = Collector(plan, root, FixtureTransport(self.state))
        collector.collect()

    def test_an_unrecognised_finality_policy_refuses_before_any_shard(self):
        plan = deepcopy(self.plan)
        plan["finality"]["policy"] = "probably-final"
        with self.assertRaisesRegex(AlexandriaError, "finality policy"):
            self.collect(plan=plan)

    def test_collection_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.collect()


class ResponseRefusalTests(CollectorTestCase):
    def refuse(self, fault, pattern):
        label = "shard 0 logs"
        transport = FixtureTransport(self.state, faults={label: fault})
        with self.assertRaisesRegex(AlexandriaError, pattern):
            self.collect(transport=transport)
        receipts = self.receipts()
        self.assertTrue(receipts)
        return receipts[-1]

    def test_an_oversized_response_refuses_and_leaves_a_receipt(self):
        """The ceiling is lowered to 1 KiB, which the real responses fit inside."""
        with mock.patch.object(usdc_interval, "MAX_RAW_COMPONENT_BYTES", 1024):
            receipt = self.refuse(
                canonical_bytes({"id": 2, "jsonrpc": "2.0", "result": ["x" * 4000]}),
                "component byte ceiling",
            )
        self.assertEqual(receipt["code"], "oversized-response")

    def test_a_malformed_response_refuses_and_leaves_a_receipt(self):
        receipt = self.refuse(b"{not json\n", "not valid JSON")
        self.assertEqual(receipt["code"], "malformed-response")

    def test_a_json_rpc_error_refuses_and_leaves_a_receipt(self):
        receipt = self.refuse(
            canonical_bytes({"error": {"code": -32000, "message": "busy"}, "id": 2, "jsonrpc": "2.0"}),
            "JSON-RPC error",
        )
        self.assertEqual(receipt["code"], "json-rpc-error")
        self.assertEqual(receipt["status"], -32000)

    def test_a_response_marked_truncated_refuses_and_leaves_a_receipt(self):
        receipt = self.refuse(
            canonical_bytes({"id": 2, "jsonrpc": "2.0", "result": [], "truncated": True}),
            "marked truncated",
        )
        self.assertEqual(receipt["code"], "truncated-response")

    def test_a_page_at_the_provider_limit_refuses_and_leaves_a_receipt(self):
        plan = deepcopy(self.plan)
        plan["provider"]["page_limit"] = 3
        label = "shard 0 logs"
        transport = FixtureTransport(self.state, faults={
            label: canonical_bytes({"id": 2, "jsonrpc": "2.0", "result": [1, 2, 3]}),
        })
        with self.assertRaisesRegex(AlexandriaError, "provider's limit"):
            self.collect(transport=transport, plan=plan)
        receipt = self.receipts()[-1]
        self.assertEqual(receipt["code"], "page-limit")

    def test_an_envelope_for_another_request_refuses(self):
        receipt = self.refuse(
            canonical_bytes({"id": 999, "jsonrpc": "2.0", "result": []}),
            "envelope does not match",
        )
        self.assertEqual(receipt["code"], "envelope-mismatch")

    def test_a_transport_failure_refuses_and_leaves_a_receipt(self):
        def fail(_envelope):
            raise TransportError("shard 0 logs transport failed")

        receipt = self.refuse(fail, "transport failed")
        self.assertEqual(receipt["code"], "transport")

    def test_no_receipt_carries_the_endpoint_or_a_header(self):
        """A transport that puts its endpoint in its own message must not reach the file."""
        leaked = "https://user:hunter2@rpc.example.invalid/v1/SECRET-KEY"

        def leak(_envelope):
            raise TransportError(f"POST {leaked} failed: connection reset")

        transport = FixtureTransport(self.state, faults={"shard 0 logs": leak})
        with self.assertRaisesRegex(AlexandriaError, "connection reset"):
            self.collect(transport=transport)
        body = (self.root / "receipts" / "errors.jsonl").read_text()
        for secret in ("https://", "rpc.example.invalid", "SECRET-KEY", "hunter2",
                       "Content-Type", "Authorization", "User-Agent",
                       usdc_interval.USER_AGENT):
            self.assertNotIn(secret, body)
        self.assertEqual(self.receipts()[-1]["code"], "transport")

    def test_a_receipt_carries_no_field_the_provider_wrote(self):
        self.test_a_json_rpc_error_refuses_and_leaves_a_receipt()
        self.assertEqual(
            set(self.receipts()[-1]),
            {"class", "code", "provider_class", "shard", "status", "unresolved"},
        )

    def test_a_symlinked_receipts_directory_refuses(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        root = self.scratch("hostile")
        (root / "receipts").symlink_to(Path(elsewhere.name))
        with self.assertRaisesRegex(AlexandriaError, "not a directory"):
            Collector(self.plan, root, FixtureTransport(self.state))
        self.assertFalse((Path(elsewhere.name) / "errors.jsonl").exists())

    def test_a_symlinked_receipt_file_refuses(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        root = self.scratch("hostile-file")
        (root / "receipts").mkdir()
        (root / "receipts" / "errors.jsonl").symlink_to(Path(elsewhere.name) / "captured")
        collector = Collector(self.plan, root, FixtureTransport(self.state))
        with self.assertRaisesRegex(AlexandriaError, "cannot open the error receipt file"):
            collector.record_error(0, "logs", "probe")
        self.assertFalse((Path(elsewhere.name) / "captured").exists())

    def test_a_failed_finality_bind_leaves_a_receipt(self):
        def fail(_envelope):
            raise TransportError("finality boundary transport failed")

        transport = FixtureTransport(self.state, faults={"finality boundary under finalized": fail})
        with self.assertRaisesRegex(AlexandriaError, "transport failed"):
            self.collect(transport=transport)
        receipt = self.receipts()[-1]
        self.assertEqual((receipt["code"], receipt["class"], receipt["shard"]), ("transport", "boundary", -1))
        self.assertIsNone(receipt["unresolved"])

    def test_a_failed_boundary_re_read_leaves_a_receipt(self):
        root = self.scratch("interrupted")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at="shard 3 logs")).collect()

        def fail(_envelope):
            raise TransportError("boundary re-read transport failed")

        transport = FixtureTransport(
            self.state, faults={"shard 2 boundary re-read": fail}
        )
        with self.assertRaisesRegex(AlexandriaError, "transport failed"):
            Collector(self.plan, root, transport).collect()
        receipt = self.receipts(root)[-1]
        self.assertEqual((receipt["code"], receipt["class"]), ("transport", "boundary"))

    def test_a_retry_does_not_erase_the_earlier_receipt(self):
        self.test_a_json_rpc_error_refuses_and_leaves_a_receipt()
        first = len(self.receipts())
        self.test_a_json_rpc_error_refuses_and_leaves_a_receipt()
        self.assertEqual(len(self.receipts()), first + 1)


class ResumeTests(CollectorTestCase):
    def clean_journals(self):
        root = self.scratch("clean")
        Collector(self.plan, root, FixtureTransport(self.state)).collect()
        return journals(root)

    def test_a_kill_on_a_committed_boundary_resumes_byte_identically(self):
        expected = self.clean_journals()
        root = self.scratch("resumed")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at="shard 2 boundary-blocks")).collect()
        self.assertNotEqual(journals(root), expected)
        summary = Collector(self.plan, root, FixtureTransport(self.state)).collect()
        self.assertEqual(summary["resumed_from"], 2)
        self.assertEqual(journals(root), expected)

    def test_a_kill_mid_shard_resumes_byte_identically(self):
        expected = self.clean_journals()
        root = self.scratch("resumed")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at="shard 3 traces")).collect()
        summary = Collector(self.plan, root, FixtureTransport(self.state)).collect()
        self.assertEqual(summary["resumed_from"], 3)
        self.assertEqual(journals(root), expected)

    def test_a_kill_before_the_first_commit_starts_over(self):
        expected = self.clean_journals()
        root = self.scratch("resumed")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at="shard 0 traces")).collect()
        summary = Collector(self.plan, root, FixtureTransport(self.state)).collect()
        self.assertEqual(summary["resumed_from"], 0)
        self.assertEqual(journals(root), expected)

    def test_a_completed_collection_rerun_collects_nothing_further(self):
        root = self.scratch("rerun")
        Collector(self.plan, root, FixtureTransport(self.state)).collect()
        before = journals(root)
        summary = Collector(self.plan, root, FixtureTransport(self.state)).collect()
        self.assertEqual(summary["collected_shards"], 0)
        self.assertEqual(journals(root), before)


class ReorgRewindTests(CollectorTestCase):
    """The conformance evidence for `resume-rewinds-on-reorg`."""

    def interrupted(self, kill_at="shard 4 boundary-blocks"):
        root = self.scratch("interrupted")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at=kill_at)).collect()
        return root

    def test_an_unchanged_boundary_resumes_without_rewinding(self):
        root = self.interrupted()
        before = json.loads((root / "checkpoint.json").read_text())
        summary = Collector(self.plan, root, FixtureTransport(self.state)).collect()
        self.assertEqual(summary["resumed_from"], before["next_shard"])

    def test_a_changed_boundary_rewinds_to_the_last_matching_checkpoint(self):
        root = self.interrupted()
        reorged = self.plan["shards"][2]["end"]
        summary = Collector(
            self.plan, root, FixtureTransport(self.state, reorg_from=reorged)
        ).collect()
        self.assertEqual(summary["resumed_from"], 2)
        checkpoint = json.loads((root / "checkpoint.json").read_text())
        self.assertEqual(checkpoint["next_shard"], 5)

    def test_a_rewind_re_collects_the_dropped_shards(self):
        root = self.interrupted()
        reorged = self.plan["shards"][2]["end"]
        before = journals(root)
        Collector(self.plan, root, FixtureTransport(self.state, reorg_from=reorged)).collect()
        after = journals(root)
        self.assertNotEqual(after, before)
        for name in EVIDENCE_CLASSES:
            self.assertEqual(len(after[name].splitlines()), 5)

    def test_a_rewind_leaves_the_journals_where_the_new_chain_would(self):
        """A rewound run holds the chain it ended on, not the one it started from."""
        reorged = self.plan["shards"][3]["end"]
        clean = self.scratch("clean")
        Collector(
            self.plan, clean, FixtureTransport(self.state, reorg_from=reorged)
        ).collect()
        expected = journals(clean)
        root = self.interrupted()
        before = journals(root)
        Collector(
            self.plan, root, FixtureTransport(self.state, reorg_from=reorged)
        ).collect()
        self.assertEqual(journals(root), expected)
        self.assertNotEqual(journals(root), before)

    def test_a_reorg_below_every_remembered_boundary_starts_over(self):
        root = self.interrupted()
        summary = Collector(
            self.plan, root, FixtureTransport(self.state, reorg_from=0)
        ).collect()
        self.assertEqual(summary["resumed_from"], 0)

    def test_a_reorg_deeper_than_the_history_refuses(self):
        """A trail that no longer reaches shard zero cannot answer for it."""
        with mock.patch("alexandria_lib.interval.MAX_HISTORY", 2):
            root = self.interrupted()
            history = json.loads((root / "checkpoint.json").read_text())["history"]
            self.assertEqual([entry["shard"] for entry in history], [2, 3])
            reorged = self.plan["shards"][0]["end"]
            with self.assertRaisesRegex(AlexandriaError, "deeper than the checkpoint"):
                Collector(
                    self.plan, root, FixtureTransport(self.state, reorg_from=reorged)
                ).collect()

    def test_the_rewind_opens_no_socket(self):
        root = self.interrupted()
        reorged = self.plan["shards"][2]["end"]
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            Collector(self.plan, root, FixtureTransport(self.state, reorg_from=reorged)).collect()



SECOND_FIXTURE = PLUGIN / "tests" / "fixtures" / "usdc-interval-second-provider.json"


def second_fixture():
    if not SECOND_FIXTURE.is_file():
        raise AssertionError(
            f"the second-provider fixture is missing at {SECOND_FIXTURE}; the reconciler "
            "cannot be shown without it and this suite must fail rather than skip"
        )
    return json.loads(SECOND_FIXTURE.read_text(encoding="utf-8"))


class SecondProviderTransport(FixtureTransport):
    """The same chain, with the disagreements the second-provider fixture declares."""

    def __init__(self, state, disagreements, **kwargs):
        super().__init__(state, **kwargs)
        self.disagreements = disagreements

    def _shard_index(self, number):
        shard = self._shard_for(number)
        return None if shard is None else str(shard["index"])

    def _hash(self, number):
        if number == int(self.state["plan"]["interval"]["start"]):
            override = self.disagreements.get("first_block_hash_override")
            if override:
                return override
        index = self._shard_index(number)
        override = self.disagreements.get("boundary_hash_overrides", {}).get(index)
        return override if override else super()._hash(number)

    def transactions(self, number):
        index = self._shard_index(number)
        order = self.disagreements.get("transaction_orders", {}).get(index)
        return list(order) if order else super().transactions(number)

    def slot_word(self, number):
        override = self.disagreements.get("slot_word_overrides", {}).get(str(number))
        return override if override else super().slot_word(number)

    def code(self, address, number):
        override = self.disagreements.get("code_overrides", {}).get(address)
        return override if override else super().code(address, number)

    def request(self, payload, label):
        data = super().request(payload, label)
        envelope = json.loads(data)
        method = json.loads(payload)["method"]
        if method == "eth_getLogs":
            shard = self._shard_for(int(json.loads(payload)["params"][0]["toBlock"], 16))
            extra = self.disagreements.get("extra_logs", {}).get(str(shard["index"]))
            if extra:
                extras = deepcopy(extra)
                for record in extras:
                    record["blockHash"] = self._hash(int(record["blockNumber"], 16))
                envelope["result"] = sorted(list(envelope["result"]) + extras,
                    key=lambda record: tuple(int(record[key], 16) for key in ("blockNumber", "transactionIndex", "logIndex")))
                return canonical_bytes(envelope)
        return data


class ReconciliationTests(CollectorTestCase):
    """The conformance evidence for `reconciliation-refuses-mismatch`."""

    def setUp(self):
        super().setUp()
        self.disagreements = second_fixture()

    def collected(self, name="collected"):
        root = self.scratch(name)
        Collector(self.plan, root, FixtureTransport(self.state)).collect()
        return root

    def reconcile(self, root, transport, provider_class="second archive endpoint, class only"):
        return Reconciler(self.plan, root, transport, provider_class).reconcile()

    def test_two_agreeing_providers_record_an_agreement(self):
        root = self.collected()
        document = self.reconcile(root, FixtureTransport(self.state))
        record = document["reconciliation"]
        self.assertEqual(record["status"], "agreed")
        self.assertEqual(record["disputed"], [])
        self.assertEqual(record["matched"], record["compared"])
        self.assertGreater(record["compared"], 0)
        self.assertEqual({shard["status"] for shard in document["shards"]}, {"complete"})

    def test_a_disputed_log_identity_makes_only_its_own_shard_partial(self):
        root = self.collected()
        document = self.reconcile(
            root,
            SecondProviderTransport(self.state, {"extra_logs": self.disagreements["extra_logs"]}),
        )
        record = document["reconciliation"]
        self.assertEqual(record["status"], "disputed")
        self.assertEqual([entry["kind"] for entry in record["disputed"]], ["log-identity"])
        self.assertEqual(record["disputed"][0]["shard"], 1)
        statuses = {shard["index"]: shard["status"] for shard in document["shards"]}
        self.assertEqual(statuses[1], "partial")
        self.assertEqual({index: status for index, status in statuses.items() if index != 1},
                         {0: "complete", 2: "complete", 3: "complete", 4: "complete"})

    def test_a_disagreeing_boundary_hash_makes_its_shard_failed(self):
        root = self.collected()
        document = self.reconcile(
            root,
            SecondProviderTransport(
                self.state,
                {"boundary_hash_overrides": self.disagreements["boundary_hash_overrides"]},
            ),
        )
        record = document["reconciliation"]
        self.assertEqual(record["status"], "disputed")
        self.assertIn("boundary-hash", [entry["kind"] for entry in record["disputed"]])
        statuses = {shard["index"]: shard["status"] for shard in document["shards"]}
        self.assertEqual(statuses[2], "failed")

    def test_a_disagreeing_transaction_order_is_recorded(self):
        root = self.collected()
        document = self.reconcile(
            root,
            SecondProviderTransport(
                self.state,
                {"transaction_orders": self.disagreements["transaction_orders"]},
            ),
        )
        kinds = {entry["kind"] for entry in document["reconciliation"]["disputed"]}
        self.assertIn("transaction-order", kinds)
        statuses = {shard["index"]: shard["status"] for shard in document["shards"]}
        self.assertEqual(statuses[3], "partial")

    def test_neither_provider_wins_by_answering_first(self):
        """The disputed shard keeps both sets of bytes and takes neither as truth."""
        root = self.collected()
        document = self.reconcile(
            root,
            SecondProviderTransport(
                self.state,
                {"boundary_hash_overrides": self.disagreements["boundary_hash_overrides"]},
            ),
        )
        kept = (root / "reconciliation" / "disputed.jsonl").read_bytes()
        entries = [json.loads(line) for line in kept.splitlines() if line]
        self.assertTrue(entries)
        self.assertEqual({entry["shard"] for entry in entries}, {2})
        staged = {
            entry["shard"]: entry["response"]
            for entry in Staging(root, self.plan).entries("boundary-blocks")
        }
        self.assertIn("0x" + "9" * 64, entries[0]["response"])
        self.assertNotIn("0x" + "9" * 64, staged[2])
        self.assertEqual(
            [shard["status"] for shard in document["shards"] if shard["index"] == 2], ["failed"]
        )

    def test_a_second_provider_that_raises_leaves_the_interval_unreconciled(self):
        def fail(_envelope):
            raise TransportError("second provider transport failed")

        for label in ("shard 0 boundary-blocks second provider", "shard 0 logs second provider"):
            with self.subTest(label=label):
                root = self.collected(f"unreconciled-{label.split()[1]}-{label.split()[2]}")
                document = self.reconcile(
                    root, SecondProviderTransport(self.state, {}, faults={label: fail})
                )
                record = document["reconciliation"]
                self.assertEqual(record["status"], "unreconciled")
                self.assertEqual((record["compared"], record["matched"]), (0, 0))

    def test_a_second_provider_returning_an_error_leaves_the_interval_unreconciled(self):
        root = self.collected()
        transport = SecondProviderTransport(self.state, {}, faults={
            "shard 0 logs second provider": canonical_bytes(
                {"error": {"code": -32000}, "id": 2, "jsonrpc": "2.0"}
            ),
        })
        self.assertEqual(self.reconcile(root, transport)["reconciliation"]["status"], "unreconciled")

    def test_an_incompletely_collected_interval_refuses(self):
        root = self.scratch("partial")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at="shard 3 logs")).collect()
        with self.assertRaisesRegex(AlexandriaError, "not completely collected"):
            self.reconcile(root, FixtureTransport(self.state))

    def test_a_provider_class_carrying_an_endpoint_refuses(self):
        root = self.collected()
        with self.assertRaisesRegex(AlexandriaError, "must not carry an endpoint"):
            self.reconcile(root, FixtureTransport(self.state), "https://second.invalid/rpc")

    def test_a_symlinked_reconciliation_directory_refuses(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        root = self.collected("symlinked")
        (root / "reconciliation").symlink_to(Path(elsewhere.name))
        with self.assertRaisesRegex(AlexandriaError, "not a directory"):
            self.reconcile(root, FixtureTransport(self.state))

    def test_the_record_matches_the_receipt_schema(self):
        root = self.collected()
        document = self.reconcile(
            root,
            SecondProviderTransport(self.state, {"extra_logs": self.disagreements["extra_logs"]}),
        )
        schema = json.loads(
            (PLUGIN / "schemas" / "interval-receipt-v1.schema.json").read_text()
        )
        self.assertEqual(
            set(document["reconciliation"]),
            set(schema["$defs"]["reconciliation"]["required"]),
        )
        dispute = schema["$defs"]["reconciliation"]["properties"]["disputed"]["items"]
        self.assertEqual(set(document["reconciliation"]["disputed"][0]), set(dispute["required"]))

    def test_reconciling_an_incomplete_tree_changes_nothing(self):
        """Refusing must not truncate the journals it refused to read."""
        root = self.scratch("untouched")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at="shard 3 traces")).collect()
        before = journals(root)
        with self.assertRaisesRegex(AlexandriaError, "not completely collected"):
            self.reconcile(root, FixtureTransport(self.state))
        self.assertEqual(journals(root), before)

    def test_a_successful_reconciliation_changes_no_journal(self):
        root = self.collected("read-only")
        before = journals(root)
        self.reconcile(root, FixtureTransport(self.state))
        self.assertEqual(journals(root), before)

    def test_a_staged_record_above_the_control_limit_is_still_readable(self):
        """The reader's ceiling is the one the writer enforced, not the smaller one.

        The record here is deliberately just over the 8 MiB control limit and
        far under the 64 MiB component limit the collector accepts, which is
        the exact band a reader using the smaller default cannot read back.
        """
        from alexandria_lib.canonical import MAX_CONTROL_BYTES
        from alexandria_lib.release import MAX_RAW_COMPONENT_BYTES

        self.assertGreater(MAX_RAW_COMPONENT_BYTES, MAX_CONTROL_BYTES)
        root = self.scratch("wide")
        staging = Staging(root, self.plan)
        staging.resume()
        wide = canonical_bytes({"id": 2, "jsonrpc": "2.0", "result": "0x" + "a" * MAX_CONTROL_BYTES})
        self.assertGreater(len(wide), MAX_CONTROL_BYTES)
        self.assertLess(len(wide), MAX_RAW_COMPONENT_BYTES)
        staging.record(0, "logs", b"{}", wide)
        end = self.plan["shards"][0]["end"]
        staging.commit(0, end, self.state["blocks"][str(end)])
        try:
            entries = list(staging.entries("logs"))
        except AlexandriaError as error:
            staging.close()
            self.fail(
                "a staged record inside the component ceiling could not be read "
                f"back: {error}"
            )
        staging.close()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["response"].encode(), wide)

    def test_an_unreconciled_interval_keeps_the_counts_it_reached(self):
        def fail(_envelope):
            raise TransportError("second provider transport failed")

        root = self.collected("partial-counts")
        document = self.reconcile(
            root,
            SecondProviderTransport(self.state, {}, faults={"shard 3 logs second provider": fail}),
        )
        record = document["reconciliation"]
        self.assertEqual(record["status"], "unreconciled")
        self.assertGreater(record["compared"], 0)
        self.assertLessEqual(record["matched"], record["compared"])

    def test_a_second_provider_envelope_without_its_version_refuses(self):
        root = self.collected("versionless")
        transport = SecondProviderTransport(self.state, {}, faults={
            "shard 0 logs second provider": canonical_bytes({"id": 2, "result": []}),
        })
        self.assertEqual(
            self.reconcile(root, transport)["reconciliation"]["status"], "unreconciled"
        )

    def test_reconciliation_opens_no_socket(self):
        root = self.collected()
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.reconcile(root, FixtureTransport(self.state))



REGISTRY = PLUGIN / "examples" / "compound-v3-phase0-v0" / "input" / "registry.json"
CREATED_AT = "2026-08-31T06:00:00Z"


def registry():
    if not REGISTRY.is_file():
        raise AssertionError(
            f"the pinned Comet registry is missing at {REGISTRY}; the release cannot "
            "declare its uncollected markets without it"
        )
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def component_path(output, name):
    """Where one named component's bytes live inside a built release."""
    manifest = json.loads((Path(output) / "manifest.json").read_text())
    return Path(output) / next(
        component["object_path"] for component in manifest["components"]
        if component["name"] == name
    )


def component_document(output, name):
    return json.loads(component_path(output, name).read_text())


class ReleaseTestCase(CollectorTestCase):
    """Collect, reconcile and build over the fixture, for the release-level cases."""

    def setUp(self):
        super().setUp()
        self.registry = registry()

    def pipeline(self, name="release", second=None, reconcile=True, plan=None):
        plan = plan or self.plan
        staging = self.scratch(f"{name}-staging")
        Collector(plan, staging, FixtureTransport(self.state)).collect()
        if reconcile:
            Reconciler(
                plan, staging, second or FixtureTransport(self.state),
                "second archive endpoint, class only",
            ).reconcile()
        return staging, self.root / name

    def build(self, staging, output, registry_document=None, builder=Builder, plan=None):
        return builder(
            plan or self.plan, staging, registry_document or self.registry, created_at=CREATED_AT,
        ).build(output)



class IntervalCheckTests(ReleaseTestCase):
    """The conformance evidence for `release-verifies-offline`."""

    def test_a_release_over_a_clean_interval_verifies_offline(self):
        staging, output = self.pipeline()
        release_id = self.build(staging, output)
        summary = check_interval(output)
        self.assertEqual(summary["release_id"], release_id)
        self.assertEqual(summary["interval"], dict(self.plan["interval"]))
        self.assertEqual(summary["shard_statuses"], {"complete": 5})
        self.assertEqual(summary["reconciliation"], "agreed")
        self.assertEqual(summary["epochs"], 2)
        self.assertEqual(set(summary["implementations"]), {IMPLEMENTATION_A, IMPLEMENTATION_B})

    def test_a_second_build_over_the_same_tree_yields_the_same_identity(self):
        staging, output = self.pipeline()
        first = self.build(staging, output)
        second = self.build(staging, self.root / "release-again")
        self.assertEqual(first, second)

    def test_the_release_declares_one_component_per_class_and_its_receipts(self):
        staging, output = self.pipeline()
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(
            {component["name"] for component in manifest["components"]},
            {"boundary-blocks", "epoch-evidence", "epoch-table", "error-receipts",
             "implementation-code", "interval-plan", "logs", "reconciliation",
             "registry", "traces"},
        )
        self.assertEqual(len(manifest["components"]), 10)

    def test_every_coverage_count_is_derived_from_the_component_bytes(self):
        staging, output = self.pipeline()
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        captures = {capture["id"]: capture for capture in manifest["captures"]}
        self.assertEqual(captures["logs"]["coverage"]["record_count"], 5)
        self.assertEqual(captures["registry"]["coverage"]["record_count"], 28)
        for capture in captures.values():
            self.assertEqual(capture["venue"], "compound-v3")
            self.assertEqual(capture["chain"], "eip155:1")
            self.assertEqual(capture["scope"]["interval"]["kind"], "block-range")

    def test_an_inflated_coverage_count_is_refused_by_ingest(self):
        """A count asserted rather than derived must not survive `ingest`."""

        class Inflating(Builder):
            def _capture(self, component, document, reconciliation, boundaries):
                capture = super()._capture(component, document, reconciliation, boundaries)
                if component == "logs":
                    capture["coverage"]["collections"][0]["record_count"] += 1
                    capture["coverage"]["record_count"] += 1
                return capture

        staging, output = self.pipeline()
        with self.assertRaisesRegex(AlexandriaError, "declares .* records but found"):
            self.build(staging, output, builder=Inflating)

    def test_the_uncollected_registry_entries_are_declared_as_a_gap(self):
        staging, output = self.pipeline()
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        gaps = {
            capture["id"]: capture["coverage"]["gaps"] for capture in manifest["captures"]
        }
        self.assertTrue(any("27 of the 28 registry entries" in gap for gap in gaps["registry"]))
        for name in JOURNAL_CLASSES:
            self.assertTrue(any("no credit event" in gap for gap in gaps[name]))
            # The first block is read now, so no scope names it as unread.
            self.assertFalse(any("first block" in gap for gap in gaps[name]))

    def test_no_coverage_reports_complete_while_naming_a_gap(self):
        staging, output = self.pipeline()
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        for capture in manifest["captures"]:
            with self.subTest(capture=capture["id"]):
                if capture["coverage"]["gaps"] or capture["coverage"]["unsupported_collections"]:
                    self.assertEqual(capture["coverage"]["status"], "partial")

    def test_a_disputed_shard_is_named_in_every_evidence_coverage(self):
        staging, output = self.pipeline(
            "disputed",
            second=SecondProviderTransport(
                self.state, {"boundary_hash_overrides": second_fixture()["boundary_hash_overrides"]}
            ),
        )
        self.build(staging, output)
        summary = check_interval(output)
        self.assertEqual(summary["shard_statuses"], {"complete": 4, "failed": 1})
        manifest = json.loads((output / "manifest.json").read_text())
        for capture in manifest["captures"]:
            if capture["id"] in EVIDENCE_CLASSES:
                self.assertTrue(
                    any("shard 2," in gap for gap in capture["coverage"]["gaps"]),
                    capture["id"],
                )

    def test_building_without_a_reconciliation_refuses(self):
        staging, output = self.pipeline("unreconciled", reconcile=False)
        with self.assertRaisesRegex(AlexandriaError, "has not been reconciled"):
            self.build(staging, output)

    def test_building_over_an_incomplete_interval_refuses(self):
        staging = self.scratch("incomplete")
        with self.assertRaises(_Killed):
            Collector(self.plan, staging, KillingTransport(self.state, kill_at="shard 3 logs")).collect()
        with self.assertRaisesRegex(AlexandriaError, "not completely collected"):
            self.build(staging, self.root / "no-release")

    def test_an_epoch_table_that_does_not_tile_the_interval_refuses(self):
        class Shortening(Builder):
            def _epochs(self, phase, end_hash):
                epochs = super()._epochs(phase, end_hash)
                epochs[-1]["end_block"] = str(int(epochs[-1]["end_block"]) - 1)
                return epochs

        staging, output = self.pipeline("short-epochs")
        with self.assertRaisesRegex(AlexandriaError, "block envelope"):
            self.build(staging, output, builder=Shortening)

    def test_an_epoch_from_another_market_refuses_at_check(self):
        class Mislabelling(Builder):
            def _epochs(self, phase, end_hash):
                epochs = super()._epochs(phase, end_hash)
                epochs[0]["proxy"] = "0x" + "ab" * 20
                return epochs

        staging, output = self.pipeline("other-market")
        self.build(staging, output, builder=Mislabelling)
        with self.assertRaisesRegex(AlexandriaError, "does not belong to the plan's market"):
            check_interval(output)

    def test_a_tampered_component_refuses_at_check(self):
        staging, output = self.pipeline("tampered")
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        target = next(
            output / component["object_path"]
            for component in manifest["components"]
            if component["name"] == "logs"
        )
        target.write_bytes(target.read_bytes().replace(b'"logs"', b'"logz"', 1))
        with self.assertRaises(AlexandriaError):
            check_interval(output)

    def test_a_receipt_disagreeing_with_the_reconciliation_refuses_at_check(self):
        staging, output = self.pipeline("disagree")
        with mock.patch("usdc_interval._receipt_shards", autospec=True) as shards:
            def flip(table, *_arguments):
                rows = deepcopy(table)
                rows[0]["status"] = "partial"
                return rows

            shards.side_effect = flip
            self.build(staging, output)
        with self.assertRaisesRegex(AlexandriaError, "disagree about a shard"):
            check_interval(output)

    def test_a_receipt_whose_counts_the_journals_do_not_carry_refuses(self):
        """A self-consistent release must still not be able to inflate a count."""

        class Inflating(Builder):
            def build(self, output):
                original = usdc_interval._receipt_shards

                def inflate(*arguments):
                    rows = original(*arguments)
                    for row in rows:
                        row["record_counts"]["logs"] *= 100
                    return rows

                usdc_interval._receipt_shards = inflate
                try:
                    return super().build(output)
                finally:
                    usdc_interval._receipt_shards = original

        staging, output = self.pipeline("inflated-receipt")
        self.build(staging, output, builder=Inflating)
        with self.assertRaisesRegex(AlexandriaError, "record counts the journals do not carry"):
            check_interval(output)

    def test_the_receipt_counts_come_from_the_journals(self):
        staging, output = self.pipeline("counted")
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        receipt = json.loads(
            (output / next(
                component["object_path"] for component in manifest["components"]
                if component["name"] == "epoch-table"
            )).read_text()
        )
        for shard in receipt["shards"]:
            self.assertEqual(
                shard["record_counts"], {"boundary-blocks": 1, "logs": 3, "traces": 2}
            )

    def omission_naming(self, output, omitted):
        manifest = json.loads((output / "manifest.json").read_text())
        return {
            capture["id"]
            for capture in manifest["captures"]
            if any(
                f"the {omitted} evidence class was not declared" in gap
                for gap in capture["coverage"]["gaps"]
            )
        }

    def test_a_plan_omitting_traces_names_the_gap_on_every_evidence_component_and_no_other(self):
        plan = deepcopy(self.plan)
        plan["evidence_classes"] = ["boundary-blocks", "logs"]
        staging, output = self.pipeline("no-traces", plan=plan)
        self.build(staging, output, plan=plan)
        self.assertEqual(
            self.omission_naming(output, "traces"), {"boundary-blocks", "logs", OPENING_CLASS}
        )
        self.assertEqual(self.omission_naming(output, "logs"), set())
        gap = next(
            gap for gap in json.loads((output / "manifest.json").read_text())["captures"][0]["coverage"]["gaps"]
            if "traces evidence class" in gap
        )
        self.assertIn("no internal call to the proxy was preserved", gap)
        self.assertEqual(check_interval(output)["epochs"], 2)

    def test_a_plan_omitting_logs_names_the_undetectable_upgrade(self):
        """Without logs the epoch table has one epoch by construction, and every scope says why."""
        plan = deepcopy(self.plan)
        plan["evidence_classes"] = ["boundary-blocks"]
        staging, output = self.pipeline("no-logs", plan=plan)
        self.build(staging, output, plan=plan)
        self.assertEqual(self.omission_naming(output, "logs"), {"boundary-blocks", OPENING_CLASS})
        self.assertEqual(self.omission_naming(output, "traces"), {"boundary-blocks", OPENING_CLASS})
        manifest = json.loads((output / "manifest.json").read_text())
        gaps = next(c for c in manifest["captures"] if c["id"] == "boundary-blocks")["coverage"]["gaps"]
        self.assertTrue(any("Upgraded(address) inside the interval is undetectable" in gap for gap in gaps))
        self.assertEqual(check_interval(output)["epochs"], 1)

    def test_a_full_plan_names_no_omitted_class(self):
        staging, output = self.pipeline("all-classes")
        self.build(staging, output)
        for name in EVIDENCE_CLASSES:
            self.assertEqual(self.omission_naming(output, name), set(), name)

    def test_an_epoch_and_a_shard_naming_one_block_must_agree(self):
        """Two sources describing the interval's last block cannot disagree."""

        class Clashing(Builder):
            def _epochs(self, phase, end_hash):
                epochs = super()._epochs(phase, end_hash)
                epochs[-1]["end_hash"] = "0x" + "77" * 32
                return epochs

        staging, output = self.pipeline("hash-clash")
        self.build(staging, output, builder=Clashing)
        with self.assertRaisesRegex(AlexandriaError, "name different block hashes"):
            check_interval(output)

    def test_an_epoch_agreeing_with_its_shard_passes(self):
        staging, output = self.pipeline("hash-agree")
        self.build(staging, output)
        self.assertEqual(check_interval(output)["shard_statuses"], {"complete": 5})

    def test_the_check_opens_no_socket_and_changes_no_file(self):
        staging, output = self.pipeline("read-only")
        self.build(staging, output)
        before = {
            path.relative_to(output): path.read_bytes()
            for path in sorted(output.rglob("*")) if path.is_file()
        }
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            check_interval(output)
        after = {
            path.relative_to(output): path.read_bytes()
            for path in sorted(output.rglob("*")) if path.is_file()
        }
        self.assertEqual(after, before)


class BoundsTests(CollectorTestCase):
    def test_the_byte_ceiling_stops_the_collection(self):
        with mock.patch.object(usdc_interval, "MAX_COLLECT_BYTES", 256):
            with self.assertRaisesRegex(AlexandriaError, "total byte ceiling"):
                self.collect()

    def test_the_elapsed_ceiling_stops_the_collection(self):
        with mock.patch.object(usdc_interval, "MAX_COLLECT_SECONDS", -1):
            with self.assertRaisesRegex(AlexandriaError, "elapsed-time ceiling"):
                self.collect()

    def test_the_https_transport_refuses_a_non_https_endpoint(self):
        for endpoint in ("http://example.invalid/rpc", "", "https://example.invalid/ rpc"):
            with self.subTest(endpoint=endpoint):
                with self.assertRaisesRegex(AlexandriaError, "HTTPS endpoint"):
                    HttpsTransport(endpoint, 25)

    def test_the_https_transport_reads_its_endpoint_only_from_the_environment(self):
        transport = HttpsTransport.from_environment(25, {"ALEXANDRIA_COMPOUND_RPC_URL": ENDPOINT})
        self.assertNotIn(ENDPOINT, repr(transport.__class__))
        with self.assertRaisesRegex(AlexandriaError, "HTTPS endpoint"):
            HttpsTransport.from_environment(25, {})

    def test_the_https_transport_refuses_a_redirect(self):
        handler = usdc_interval._NoRedirect()
        with self.assertRaisesRegex(TransportError, "redirected"):
            handler.redirect_request(None, None, 302, "Found", {}, "https://elsewhere.invalid")


class FinalityRebindTests(CollectorTestCase):
    """The conformance evidence for `finality-rebinds-after-tag-advance`.

    The `finalized` tag moves every epoch. A plan pins the boundary block it
    was written against, so the bind reads that block by number and compares
    its hash, then requires the tag to stand at or above it. The
    `finality-tag-drift` guard: against a collector that compares the tag's
    hash with the plan's, every case in this class that advances the tag fails.
    """

    def boundary(self):
        return int(self.plan["finality"]["block_number"])

    def finality_reads(self, transport):
        return [label for method, label in transport.calls if label.startswith("finality")]

    def test_a_finalized_tag_past_the_plan_boundary_still_binds(self):
        transport = FixtureTransport(self.state, finalized_number=self.boundary() + 4_096)
        collector, summary = self.collect(transport=transport)
        self.assertEqual(summary["collected_shards"], 5)
        self.assertEqual(self.receipts(), [])
        self.assertEqual(
            self.finality_reads(transport),
            [f"finality boundary block {self.boundary()}", "finality boundary under finalized"],
        )
        self.assertEqual(collector.plan["finality"]["block_number"], str(self.boundary()))

    def test_a_resume_after_the_tag_advanced_continues_from_the_checkpoint(self):
        with self.assertRaises(_Killed):
            Collector(
                self.plan, self.root,
                KillingTransport(self.state, kill_at="shard 3 logs"),
            ).collect()
        transport = FixtureTransport(self.state, finalized_number=self.boundary() + 65_536)
        _collector, summary = self.collect(transport=transport)
        self.assertEqual(summary["resumed_from"], 3)
        self.assertEqual(summary["collected_shards"], 2)
        self.assertEqual(self.receipts(), [])

    def test_the_safe_policy_rebinds_the_same_way(self):
        plan = deepcopy(self.plan)
        plan["finality"]["policy"] = "safe"
        transport = FixtureTransport(self.state, finalized_number=self.boundary() + 1)
        _collector, summary = self.collect(transport=transport, plan=plan)
        self.assertEqual(summary["collected_shards"], 5)
        self.assertIn("finality boundary under safe", self.finality_reads(transport))

    def test_a_boundary_block_with_another_hash_refuses_with_a_receipt(self):
        boundary = self.boundary()

        def moved(envelope):
            return canonical_bytes({
                "id": envelope["id"], "jsonrpc": "2.0",
                "result": {"hash": "0x" + "ee" * 32, "number": hex(boundary), "transactions": []},
            })

        transport = FixtureTransport(
            self.state, faults={f"finality boundary block {boundary}": moved},
        )
        with self.assertRaisesRegex(AlexandriaError, f"block {boundary} does not match the plan"):
            self.collect(transport=transport)
        receipt = self.receipts()[-1]
        self.assertEqual(
            (receipt["code"], receipt["class"], receipt["shard"], receipt["status"]),
            ("boundary-hash-mismatch", "boundary", -1, boundary),
        )
        self.assertIsNone(receipt["unresolved"])
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(journals(self.root), {})

    def test_a_finalized_number_below_the_boundary_refuses_with_a_receipt(self):
        boundary = self.boundary()
        transport = FixtureTransport(self.state, finalized_number=boundary - 1)
        with self.assertRaisesRegex(AlexandriaError, f"block {boundary - 1}, below the plan"):
            self.collect(transport=transport)
        receipt = self.receipts()[-1]
        self.assertEqual(
            (receipt["code"], receipt["class"], receipt["shard"], receipt["status"]),
            ("boundary-not-yet-final", "boundary", -1, boundary - 1),
        )
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(journals(self.root), {})

    def test_a_tag_at_the_boundary_with_another_hash_refuses_with_a_receipt(self):
        """A tag standing exactly on the boundary has to name the plan's hash."""
        boundary = self.boundary()

        def other_hash(envelope):
            return canonical_bytes({
                "id": envelope["id"], "jsonrpc": "2.0",
                "result": {"hash": "0x" + "11" * 32, "number": hex(boundary), "transactions": []},
            })

        transport = FixtureTransport(
            self.state, faults={"finality boundary under finalized": other_hash}
        )
        with self.assertRaisesRegex(AlexandriaError, "under a hash other than the plan's boundary hash"):
            self.collect(transport=transport)
        receipt = self.receipts()[-1]
        self.assertEqual((receipt["code"], receipt["class"], receipt["status"]),
                         ("tag-hash-mismatch", "boundary", boundary))
        self.assertEqual(self.finality_reads(transport), [
            f"finality boundary block {boundary}", "finality boundary under finalized",
        ])

    def test_a_confirmations_policy_reads_the_boundary_by_number_only(self):
        plan = deepcopy(self.plan)
        plan["finality"] = {
            "block_hash": plan["finality"]["block_hash"],
            "block_number": plan["finality"]["block_number"],
            "confirmations": 64,
            "policy": "confirmations",
        }
        transport = FixtureTransport(self.state, finalized_number=0)
        self.collect(transport=transport, plan=plan)
        self.assertEqual(self.finality_reads(transport), [f"finality boundary block {self.boundary()}"])

    def test_a_refusal_is_one_sanitised_line_and_no_traceback(self):
        boundary = self.boundary()
        transport = FixtureTransport(self.state, finalized_number=boundary - 1)
        plan_path = self.root / "plan.json"
        plan_path.write_bytes(canonical_bytes(self.plan))
        staging = self.root / "staging"
        stderr = io.StringIO()
        with mock.patch.object(
            HttpsTransport, "from_environment", classmethod(lambda cls, timeout, environ=None: transport),
        ), mock.patch.object(sys, "stderr", stderr):
            exit_code = usdc_interval.main(
                ["collect", "--plan", str(plan_path), "--staging", str(staging)]
            )
        self.assertEqual(exit_code, 1)
        lines = stderr.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith("usdc-interval: "), lines[0])
        self.assertIn(f"boundary block {boundary}", lines[0])
        self.assertNotIn("Traceback", stderr.getvalue())
        self.assertEqual(self.receipts(staging)[-1]["code"], "boundary-not-yet-final")

    def test_the_rebind_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.test_a_finalized_tag_past_the_plan_boundary_still_binds()


class DeclaredClassTests(CollectorTestCase):
    """A plan declares which classes it collects; an omitted one is never asked for."""

    def declared(self, classes):
        plan = deepcopy(self.plan)
        plan["evidence_classes"] = list(classes)
        return plan

    def test_collect_journals_only_the_declared_classes_and_asks_for_no_other(self):
        transport = FixtureTransport(self.state)
        _collector, summary = self.collect(
            transport=transport, plan=self.declared(["boundary-blocks", "logs"])
        )
        self.assertEqual(summary["record_counts"], {"boundary-blocks": 5, "logs": 15})
        self.assertEqual(sorted(journals(self.root)), ["boundary-blocks", OPENING_CLASS, "logs"])
        self.assertFalse((self.root / "journals" / "traces.jsonl").exists())
        self.assertNotIn("trace_filter", {method for method, _label in transport.calls})
        offsets = checkpoint(self.root)["offsets"]
        self.assertEqual(set(offsets), {"boundary-blocks", "logs", OPENING_CLASS})

    def test_the_plan_order_is_the_request_order(self):
        transport = FixtureTransport(self.state)
        self.collect(transport=transport, plan=self.declared(["logs", "boundary-blocks"]))
        shard_zero = [label for _method, label in transport.calls if label.startswith("shard 0 ")]
        self.assertEqual(shard_zero, ["shard 0 logs", "shard 0 boundary-blocks"])
        # Request ids come from the fixed class table, not the plan's order, so
        # two plans naming the same classes ask for byte-identical requests.
        self.assertEqual(
            (request_identifier(0, "boundary-blocks"), request_identifier(0, "logs")), (1, 2)
        )

    def test_a_plan_omitting_boundary_blocks_refuses_by_name(self):
        with self.assertRaisesRegex(AlexandriaError, "must declare the boundary-blocks"):
            Collector(self.declared(["logs"]), self.root, FixtureTransport(self.state))

    def test_a_two_class_tree_reconciles_builds_and_checks_offline(self):
        plan = self.declared(["boundary-blocks", "logs"])
        staging = self.scratch("staging")
        Collector(plan, staging, FixtureTransport(self.state)).collect()
        document = Reconciler(
            plan, staging, FixtureTransport(self.state), "second archive endpoint, class only",
        ).reconcile()
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        self.assertEqual(
            document["shards"][0]["record_counts"], {"boundary-blocks": 1, "logs": 3}
        )
        release_id = Builder(
            plan, staging, registry(), created_at=CREATED_AT,
        ).build(self.root / "release")
        summary = check_interval(self.root / "release")
        self.assertEqual(summary["release_id"], release_id)
        manifest = json.loads((self.root / "release" / "manifest.json").read_text())
        self.assertNotIn("traces", {component["name"] for component in manifest["components"]})
        self.assertEqual(len(manifest["components"]), 9)

    def test_declared_classes_open_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.test_collect_journals_only_the_declared_classes_and_asks_for_no_other()


class RequestHeaderTests(unittest.TestCase):
    """The transport sends two constant headers, neither read from the environment."""

    DECOYS = {
        "USER_AGENT": "decoy-agent/9.9",
        "HTTP_USER_AGENT": "decoy-agent/9.9",
        "ALEXANDRIA_USER_AGENT": "decoy-agent/9.9",
        "ALEXANDRIA_COMPOUND_RPC_URL": ENDPOINT,
    }

    class _Response:
        status = 200

        def __init__(self, body):
            self._body = body

        def read(self, limit):
            return self._body[:limit]

        def __enter__(self):
            return self

        def __exit__(self, *_exception):
            return False

    def sent(self, payload):
        captured = []

        def capture(_opener, request, timeout=None):
            captured.append((request, timeout))
            return self._Response(b'{"id": 0, "jsonrpc": "2.0", "result": null}')

        with mock.patch.dict(os.environ, self.DECOYS), mock.patch.object(
            urllib.request.OpenerDirector, "open", capture,
        ), mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            transport = HttpsTransport.from_environment(25)
            body = transport.request(payload, "shard 0 logs")
        self.assertEqual(len(captured), 1)
        return captured[0][0], captured[0][1], body

    def test_the_headers_are_exactly_content_type_and_the_constant_user_agent(self):
        manifest = json.loads(
            (PLUGIN / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        request, timeout, _body = self.sent(b'{"id": 0}')
        self.assertEqual(
            dict(request.header_items()),
            {
                "Content-type": "application/json",
                "User-agent": f"alexandria-usdc-interval/{manifest['version']}",
            },
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.data, b'{"id": 0}')
        self.assertEqual(timeout, 25)
        self.assertEqual(usdc_interval.PACKAGE_VERSION, manifest["version"])

    def test_no_header_value_comes_from_the_environment(self):
        request, _timeout, _body = self.sent(b"{}")
        for _name, value in request.header_items():
            self.assertNotIn("decoy", value)
            self.assertNotIn("fixture.invalid", value)
        self.assertEqual(usdc_interval.USER_AGENT, "alexandria-usdc-interval/" + usdc_interval.PACKAGE_VERSION)

    def test_the_version_is_read_from_the_manifest_at_import_and_refused_when_absent(self):
        with tempfile.TemporaryDirectory() as name:
            missing = Path(name) / "plugin.json"
            with self.assertRaisesRegex(AlexandriaError, "plugin manifest"):
                usdc_interval.package_version(missing)
            missing.write_text('{"name": "alexandria", "version": "not-a-version"}')
            with self.assertRaisesRegex(AlexandriaError, "no package version"):
                usdc_interval.package_version(missing)
            missing.write_text('{"name": "alexandria", "version": "7.8.9"}')
            self.assertEqual(usdc_interval.package_version(missing), "7.8.9")


START = 15331586
UPGRADE = 15331626
IMPLEMENTATION_A = "0x42f9505a376761b180e27a01ba0554244ed1de7d"
IMPLEMENTATION_B = "0x8b3e1f2a4c5d6e7f8091a2b3c4d5e6f708192a3b"
OFFLINE_BUDGET_SECONDS = 5.0


def opening_labels():
    """The seven opening reads the fixture's one-upgrade interval names, in plan order."""
    return [
        f"opening read 0 first-block-header block {START}",
        f"opening read 1 implementation-slot block {START}",
        f"opening read 2 implementation-slot block {UPGRADE}",
        f"opening read 3 epoch-boundary-header block {UPGRADE}",
        f"opening read 4 epoch-boundary-header block {UPGRADE - 1}",
        f"opening read 5 implementation-code block {START}",
        f"opening read 6 implementation-code block {UPGRADE}",
    ]


class OpeningPhaseTests(CollectorTestCase):
    """After the last shard, `collect` reads what binds the start and the epochs."""

    def test_a_clean_collection_journals_exactly_the_plan_order_reads(self):
        transport = FixtureTransport(self.state)
        _collector, summary = self.collect(transport=transport)
        self.assertEqual(summary["opening_reads"], {"issued": 7, "resumed_from": 0, "total": 7})
        entries = opening_entries(self.root)
        self.assertEqual([entry["class"] for entry in entries], [OPENING_CLASS] * 7)
        self.assertEqual({entry["shard"] for entry in entries}, {5})
        requests = [json.loads(entry["request"]) for entry in entries]
        self.assertEqual([request["id"] for request in requests], list(range(16, 23)))
        self.assertEqual(
            [(request["method"], request["params"]) for request in requests],
            [
                ("eth_getBlockByNumber", [hex(START), False]),
                ("eth_getStorageAt", [self.plan["proxy"], IMPLEMENTATION_SLOT, hex(START)]),
                ("eth_getStorageAt", [self.plan["proxy"], IMPLEMENTATION_SLOT, hex(UPGRADE)]),
                ("eth_getBlockByNumber", [hex(UPGRADE), False]),
                ("eth_getBlockByNumber", [hex(UPGRADE - 1), False]),
                ("eth_getCode", [IMPLEMENTATION_A, hex(START)]),
                ("eth_getCode", [IMPLEMENTATION_B, hex(UPGRADE)]),
            ],
        )
        labels = [label for _method, label in transport.calls if label.startswith("opening")]
        self.assertEqual(labels, opening_labels())
        shard_labels = [label for _method, label in transport.calls if label.startswith("shard")]
        self.assertEqual(shard_labels[-1], "shard 4 traces")
        self.assertLess(transport.calls.index(("eth_getLogs", "shard 4 logs")),
                        transport.calls.index(("eth_getBlockByNumber", labels[0])))

    def test_opening_ids_follow_every_shard_id(self):
        self.assertEqual(opening_identifier(5, 0), request_identifier(4, "traces") + 1)
        self.assertEqual(opening_identifier(5, 6), 22)

    def test_the_checkpoint_commits_the_opening_reads_under_the_existing_fields(self):
        self.collect()
        state = checkpoint(self.root)
        self.assertEqual(state["next_shard"], 5)
        self.assertEqual(state["last_accepted"]["block_number"], str(self.plan["shards"][-1]["end"]))
        journal = (self.root / "journals" / f"{OPENING_CLASS}.jsonl").stat().st_size
        self.assertEqual(state["offsets"][OPENING_CLASS], journal)
        self.assertEqual(state["records"], 15 + 7)
        self.assertEqual(state["history"][-1]["offsets"], state["offsets"])
        for entry in state["history"][:-1]:
            self.assertEqual(entry["offsets"][OPENING_CLASS], 0)

    def test_the_opening_reads_are_bound_to_the_staged_upgrade_log(self):
        """The one-upgrade interval names two implementations from its own slot reads."""
        self.collect()
        results = [json.loads(entry["response"])["result"] for entry in opening_entries(self.root)]
        self.assertEqual(results[0]["hash"], self.state["blocks"][str(START)])
        self.assertEqual(results[1], self.state["slots"][str(START)])
        self.assertEqual(results[2], self.state["slots"][str(UPGRADE)])
        self.assertEqual(results[5], self.state["code"][IMPLEMENTATION_A])
        self.assertEqual(results[6], self.state["code"][IMPLEMENTATION_B])

    def test_a_plan_without_logs_reads_one_epoch(self):
        plan = deepcopy(self.plan)
        plan["evidence_classes"] = ["boundary-blocks"]
        _collector, summary = self.collect(plan=plan)
        self.assertEqual(summary["opening_reads"]["total"], 3)

    def test_the_opening_phase_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.test_a_clean_collection_journals_exactly_the_plan_order_reads()


class OpeningPhaseResumeTests(CollectorTestCase):
    """The conformance evidence for `opening-reads-resumable`.

    The `opening-phase-resume` guard: against a collector whose resume after
    the last shard has no opening phase, or re-issues a committed read, every
    case here fails.
    """

    def clean_journals(self):
        root = self.scratch("clean")
        Collector(self.plan, root, FixtureTransport(self.state)).collect()
        return journals(root)

    def killed_at(self, label, name="resumed"):
        root = self.scratch(name)
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at=label)).collect()
        return root

    def resumed(self, root):
        transport = FixtureTransport(self.state)
        summary = Collector(self.plan, root, transport).collect()
        issued = [label for _method, label in transport.calls if label.startswith("opening")]
        return summary, issued

    def test_a_kill_before_the_first_opening_read_resumes_into_the_opening_phase(self):
        expected = self.clean_journals()
        root = self.killed_at(opening_labels()[0])
        state = checkpoint(root)
        self.assertEqual((state["next_shard"], state["offsets"][OPENING_CLASS]), (5, 0))
        self.assertEqual(opening_entries(root), [])
        summary, issued = self.resumed(root)
        self.assertEqual(summary["resumed_from"], 5)
        self.assertEqual(summary["collected_shards"], 0)
        self.assertEqual(summary["opening_reads"], {"issued": 7, "resumed_from": 0, "total": 7})
        self.assertEqual(issued, opening_labels())
        self.assertEqual(journals(root), expected)

    def test_a_kill_between_two_opening_reads_re_issues_only_the_reads_past_the_checkpoint(self):
        expected = self.clean_journals()
        root = self.killed_at(opening_labels()[3])
        state = checkpoint(root)
        self.assertEqual(state["next_shard"], 5)
        self.assertEqual(len(opening_entries(root)), 3)
        self.assertEqual(
            state["offsets"][OPENING_CLASS],
            (root / "journals" / f"{OPENING_CLASS}.jsonl").stat().st_size,
        )
        summary, issued = self.resumed(root)
        self.assertEqual(summary["opening_reads"], {"issued": 4, "resumed_from": 3, "total": 4 + 3})
        self.assertEqual(issued, opening_labels()[3:])
        self.assertEqual(journals(root), expected)

    def test_a_kill_after_the_last_opening_read_resumes_with_nothing_to_issue(self):
        expected = self.clean_journals()
        root = self.scratch("complete")
        Collector(self.plan, root, FixtureTransport(self.state)).collect()
        summary, issued = self.resumed(root)
        self.assertEqual(summary["opening_reads"], {"issued": 0, "resumed_from": 7, "total": 7})
        self.assertEqual(issued, [])
        self.assertEqual(journals(root), expected)

    def test_a_kill_on_a_code_read_resumes_from_the_committed_slot_words(self):
        expected = self.clean_journals()
        root = self.killed_at(opening_labels()[6])
        summary, issued = self.resumed(root)
        self.assertEqual(summary["opening_reads"]["issued"], 1)
        self.assertEqual(issued, opening_labels()[6:])
        self.assertEqual(journals(root), expected)

    def test_a_reorg_under_the_last_shard_rewinds_past_the_opening_reads(self):
        """A rewound shard drops every opening read, which the new chain re-answers."""
        reorged = self.plan["shards"][3]["end"]
        clean = self.scratch("clean-reorg")
        Collector(self.plan, clean, FixtureTransport(self.state, reorg_from=reorged)).collect()
        root = self.killed_at(opening_labels()[4], "reorged")
        self.assertEqual(len(opening_entries(root)), 4)
        transport = FixtureTransport(self.state, reorg_from=reorged)
        summary = Collector(self.plan, root, transport).collect()
        self.assertEqual(summary["resumed_from"], 3)
        self.assertEqual(summary["opening_reads"], {"issued": 7, "resumed_from": 0, "total": 7})
        self.assertEqual(journals(root), journals(clean))

    def test_a_committed_read_the_plan_does_not_name_refuses_with_a_receipt(self):
        root = self.killed_at(opening_labels()[3], "foreign")
        path = root / "journals" / f"{OPENING_CLASS}.jsonl"
        lines = path.read_bytes().splitlines(keepends=True)
        lines[1] = lines[1].replace(hex(START).encode(), hex(START + 1).encode(), 1)
        path.write_bytes(b"".join(lines))
        state = checkpoint(root)
        self.assertEqual(state["offsets"][OPENING_CLASS], path.stat().st_size)
        with self.assertRaisesRegex(AlexandriaError, "committed opening read 1 is not the read"):
            Collector(self.plan, root, FixtureTransport(self.state)).collect()
        receipt = self.receipts(root)[-1]
        self.assertEqual((receipt["code"], receipt["class"], receipt["shard"]),
                         ("opening-journal-mismatch", OPENING_CLASS, 5))

    def test_a_clean_and_an_interrupted_collection_stay_inside_the_offline_budget(self):
        """The study's 5,000 ms offline budget, re-measured with the opening phase inside it."""
        started = time.perf_counter()
        self.clean_journals()
        root = self.killed_at(opening_labels()[2], "timed")
        Collector(self.plan, root, FixtureTransport(self.state)).collect()
        elapsed = time.perf_counter() - started
        self.assertLess(elapsed, OFFLINE_BUDGET_SECONDS, f"took {elapsed * 1000:.0f} ms")

    def test_the_resume_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.test_a_kill_between_two_opening_reads_re_issues_only_the_reads_past_the_checkpoint()


class OpeningRefusalTests(CollectorTestCase):
    """Each opening read is shape-checked and cross-checked before it is believed."""

    def refuse(self, label, fault, pattern):
        def answer(envelope):
            return canonical_bytes({"id": envelope["id"], "jsonrpc": "2.0", "result": fault})

        transport = FixtureTransport(self.state, faults={label: answer})
        with self.assertRaisesRegex(AlexandriaError, pattern):
            self.collect(transport=transport)
        receipt = self.receipts()[-1]
        self.assertEqual((receipt["class"], receipt["shard"]), (OPENING_CLASS, 5))
        self.assertEqual(set(receipt), {"class", "code", "provider_class", "shard", "status", "unresolved"})
        return receipt

    def test_a_slot_word_that_is_not_a_left_padded_address_refuses(self):
        receipt = self.refuse(
            opening_labels()[1], "0x" + "ff" * 12 + IMPLEMENTATION_A[2:], "not a left-padded address",
        )
        self.assertEqual(receipt["code"], "slot-not-an-address")
        self.assertEqual(receipt["unresolved"], {"end": START, "start": START})
        self.assertEqual(receipt["status"], START)
        self.assertEqual(len(opening_entries(self.root)), 1)

    def test_a_slot_word_that_is_not_a_word_refuses_the_same_way(self):
        receipt = self.refuse(opening_labels()[2], "0x1234", "not a 32-byte word")
        self.assertEqual(receipt["code"], "slot-not-an-address")
        self.assertEqual(receipt["unresolved"], {"end": UPGRADE, "start": UPGRADE})

    def test_a_zero_address_slot_refuses(self):
        receipt = self.refuse(opening_labels()[1], "0x" + "0" * 64, "is the zero address")
        self.assertEqual(receipt["code"], "slot-zero-address")

    def test_an_empty_or_non_hex_code_read_refuses(self):
        cases = (("0x", "empty runtime code"), ("0xzz", "not hexadecimal"), ("", "not hexadecimal"), (None, "not hexadecimal"))
        for index, (value, pattern) in enumerate(cases):
            with self.subTest(value=value):
                root = self.scratch(f"code-{index}")
                collector = Collector(self.plan, root, FixtureTransport(self.state, faults={
                    opening_labels()[5]: lambda envelope, value=value: canonical_bytes(
                        {"id": envelope["id"], "jsonrpc": "2.0", "result": value}
                    ),
                }))
                with self.assertRaisesRegex(AlexandriaError, pattern):
                    collector.collect()
                receipt = self.receipts(root)[-1]
                self.assertEqual((receipt["code"], receipt["unresolved"]), ("code-not-hex", {"end": START, "start": START}))
                self.assertEqual(len(opening_entries(root)), 5)

    def test_an_upgrade_log_announcing_another_implementation_refuses(self):
        receipt = self.refuse(
            opening_labels()[2], "0x" + "0" * 24 + IMPLEMENTATION_A[2:], "announces .* while the implementation slot",
        )
        self.assertEqual(receipt["code"], "upgrade-log-mismatch")
        self.assertEqual(receipt["unresolved"], {"end": UPGRADE, "start": UPGRADE})

    def test_an_upgrade_log_naming_another_block_hash_refuses(self):
        receipt = self.refuse(
            opening_labels()[3],
            {"hash": "0x" + "ee" * 32, "number": hex(UPGRADE), "transactions": []},
            "names a different block hash",
        )
        self.assertEqual(receipt["code"], "upgrade-log-mismatch")
        self.assertEqual(len(opening_entries(self.root)), 3)

    def test_a_header_without_its_own_number_refuses(self):
        receipt = self.refuse(
            opening_labels()[0],
            {"hash": self.state["blocks"][str(START)], "number": hex(START + 1), "transactions": []},
            "carries another block number",
        )
        self.assertEqual(receipt["code"], "malformed-header")

    def test_an_oversized_code_read_refuses_under_the_byte_ceiling(self):
        with mock.patch.object(usdc_interval, "MAX_RAW_COMPONENT_BYTES", 4096):
            receipt = self.refuse(opening_labels()[5], "0x" + "ab" * 4096, "component byte ceiling")
        self.assertEqual(receipt["code"], "oversized-response")

    def test_no_opening_receipt_carries_the_endpoint(self):
        leaked = "https://user:hunter2@rpc.example.invalid/v1/SECRET-KEY"

        def leak(_envelope):
            raise TransportError(f"POST {leaked} failed: connection reset")

        transport = FixtureTransport(self.state, faults={opening_labels()[0]: leak})
        with self.assertRaisesRegex(AlexandriaError, "connection reset"):
            self.collect(transport=transport)
        body = (self.root / "receipts" / "errors.jsonl").read_text()
        for secret in ("https://", "rpc.example.invalid", "SECRET-KEY", "hunter2", usdc_interval.USER_AGENT):
            self.assertNotIn(secret, body)
        self.assertEqual(self.receipts()[-1]["code"], "transport")

    def test_the_refusals_open_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.test_a_zero_address_slot_refuses()


class OpeningReconciliationTests(CollectorTestCase):
    """`reconcile` compares the opening reads as well as the shards."""

    SHARD_COMPARISONS = 5 * (1 + 1 + 3)
    OPENING_COMPARISONS = 1 + 2 + 2

    def setUp(self):
        super().setUp()
        self.disagreements = second_fixture()

    def collected(self, name="collected"):
        root = self.scratch(name)
        Collector(self.plan, root, FixtureTransport(self.state)).collect()
        return root

    def reconcile(self, root, transport):
        return Reconciler(self.plan, root, transport, "second archive endpoint, class only").reconcile()

    def disputed_entries(self, root):
        kept = (root / "reconciliation" / "disputed.jsonl").read_bytes()
        return [json.loads(line) for line in kept.splitlines() if line]

    def test_two_agreeing_providers_count_the_opening_reads(self):
        root = self.collected()
        transport = FixtureTransport(self.state)
        record = self.reconcile(root, transport)["reconciliation"]
        self.assertEqual(record["status"], "agreed")
        self.assertEqual(record["compared"], self.SHARD_COMPARISONS + self.OPENING_COMPARISONS)
        self.assertEqual(record["matched"], record["compared"])
        asked = [label for _method, label in transport.calls if label.startswith("opening")]
        self.assertEqual(asked, [
            f"{label} second provider" for index, label in enumerate(opening_labels()) if index not in (3, 4)
        ])

    def test_a_second_provider_disagreeing_on_one_slot_word_records_the_kind_and_keeps_both(self):
        root = self.collected()
        document = self.reconcile(
            root,
            SecondProviderTransport(self.state, {"slot_word_overrides": self.disagreements["slot_word_overrides"]}),
        )
        record = document["reconciliation"]
        self.assertEqual(record["status"], "disputed")
        self.assertEqual(record["disputed"], [{
            "identity": f"implementation slot at block {UPGRADE}",
            "kind": "slot-word",
            "shard": 5,
        }])
        self.assertEqual(record["compared"], self.SHARD_COMPARISONS + self.OPENING_COMPARISONS)
        self.assertEqual(record["matched"], record["compared"] - 1)
        self.assertEqual({shard["status"] for shard in document["shards"]}, {"complete"})
        kept = self.disputed_entries(root)
        self.assertEqual([(entry["class"], entry["shard"]) for entry in kept], [(OPENING_CLASS, 5)])
        other = self.disagreements["slot_word_overrides"][str(UPGRADE)]
        self.assertIn(other, kept[0]["response"])
        staged = opening_entries(root)[2]["response"]
        self.assertIn(self.state["slots"][str(UPGRADE)], staged)
        self.assertNotIn(other, staged)

    def test_a_second_provider_disagreeing_on_the_first_block_records_its_hash(self):
        root = self.collected()
        record = self.reconcile(
            root,
            SecondProviderTransport(self.state, {"first_block_hash_override": self.disagreements["first_block_hash_override"]}),
        )["reconciliation"]
        self.assertEqual([entry["kind"] for entry in record["disputed"]], ["first-block-hash"])
        self.assertEqual(record["disputed"][0]["identity"], f"block {START}")

    def test_a_second_provider_first_block_header_under_another_number_is_disputed(self):
        """The right hash under another block number is not the first block's header."""
        root = self.collected()

        def misnumbered(envelope):
            return canonical_bytes({
                "id": envelope["id"], "jsonrpc": "2.0",
                "result": {"hash": self.state["blocks"][str(START)], "number": hex(START + 1), "transactions": []},
            })

        label = f"{opening_labels()[0]} second provider"
        record = self.reconcile(
            root, SecondProviderTransport(self.state, {}, faults={label: misnumbered})
        )["reconciliation"]
        self.assertEqual([entry["kind"] for entry in record["disputed"]], ["first-block-hash"])
        self.assertEqual(record["status"], "disputed")

    def test_a_second_provider_disagreeing_on_a_code_read_records_its_digest(self):
        root = self.collected()
        record = self.reconcile(
            root,
            SecondProviderTransport(self.state, {"code_overrides": self.disagreements["code_overrides"]}),
        )["reconciliation"]
        self.assertEqual([entry["kind"] for entry in record["disputed"]], ["code-digest"])
        self.assertEqual(record["disputed"][0]["identity"], f"code of {IMPLEMENTATION_B} at block {UPGRADE}")

    def test_a_second_provider_failing_on_an_opening_read_leaves_the_interval_unreconciled(self):
        def fail(_envelope):
            raise TransportError("second provider transport failed")

        root = self.collected()
        label = f"{opening_labels()[5]} second provider"
        record = self.reconcile(
            root, SecondProviderTransport(self.state, {}, faults={label: fail})
        )["reconciliation"]
        self.assertEqual(record["status"], "unreconciled")
        self.assertEqual(record["compared"], self.SHARD_COMPARISONS + 3)

    def test_an_interval_killed_in_the_opening_phase_refuses_to_reconcile(self):
        root = self.scratch("half-open")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at=opening_labels()[4])).collect()
        before = journals(root)
        with self.assertRaisesRegex(AlexandriaError, "opening reads are not completely collected"):
            self.reconcile(root, FixtureTransport(self.state))
        self.assertEqual(journals(root), before)

    def test_an_opening_read_the_checkpoint_has_not_committed_refuses_to_reconcile(self):
        """A record past the committed offset is one the collector would re-issue on resume."""
        clean = self.collected("clean")
        lines = (clean / "journals" / f"{OPENING_CLASS}.jsonl").read_bytes().splitlines(keepends=True)
        root = self.scratch("uncommitted")
        with self.assertRaises(_Killed):
            Collector(self.plan, root, KillingTransport(self.state, kill_at=opening_labels()[6])).collect()
        path = root / "journals" / f"{OPENING_CLASS}.jsonl"
        committed = checkpoint(root)["offsets"][OPENING_CLASS]
        self.assertEqual(committed, path.stat().st_size)
        path.write_bytes(b"".join(lines))
        self.assertEqual(len(opening_entries(root)), 7)
        self.assertGreater(path.stat().st_size, committed)
        before = journals(root)
        with self.assertRaisesRegex(
            AlexandriaError,
            r"epoch-evidence journal holds bytes the checkpoint has not committed "
            rf"\({path.stat().st_size} bytes on disk, {committed} committed\)",
        ):
            self.reconcile(root, FixtureTransport(self.state))
        self.assertEqual(journals(root), before)
        self.assertFalse((root / "reconciliation" / "reconciliation.json").exists())

    def test_a_journal_shorter_than_its_committed_offset_refuses_by_name(self):
        root = self.collected("cut")
        path = root / "journals" / f"{OPENING_CLASS}.jsonl"
        committed = checkpoint(root)["offsets"][OPENING_CLASS]
        path.write_bytes(path.read_bytes()[:-1])
        with self.assertRaisesRegex(
            AlexandriaError,
            rf"epoch-evidence journal is shorter than its committed offset \({committed - 1} bytes on disk, {committed} committed\)",
        ):
            self.reconcile(root, FixtureTransport(self.state))

    def test_the_receipt_schema_names_every_dispute_kind(self):
        schema = json.loads((PLUGIN / "schemas" / "interval-receipt-v1.schema.json").read_text())
        kinds = schema["$defs"]["reconciliation"]["properties"]["disputed"]["items"]["properties"]["kind"]["enum"]
        self.assertEqual(set(kinds), set(DISPUTE_KINDS))
        self.assertTrue({"first-block-hash", "slot-word", "code-digest"} <= set(kinds))

    def test_the_opening_reconciliation_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.test_two_agreeing_providers_count_the_opening_reads()


class ScopeBindingTests(ReleaseTestCase):
    """The conformance evidence for `scope-binds-both-hashes`.

    The `start-hash-source` guard: against a builder that copies the start
    hash from the epoch table or an operator, or a check that believes the
    scope's own word, the cases here that compare the scope with the journal's
    first-block read fail.
    """

    def scopes(self, output):
        manifest = json.loads((output / "manifest.json").read_text())
        return {capture["id"]: capture["scope"] for capture in manifest["captures"]}

    def first_block_read(self, staging):
        return json.loads(opening_entries(staging)[0]["response"])["result"]["hash"]

    def test_a_reconciled_tree_builds_ten_components(self):
        staging, output = self.pipeline("ten")
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(len(manifest["components"]), 10)
        self.assertEqual(len(manifest["captures"]), 10)

    def test_every_evidence_scope_is_finalized_with_both_hashes(self):
        staging, output = self.pipeline("bound")
        self.build(staging, output)
        scopes = self.scopes(output)
        first = self.first_block_read(staging)
        last = self.state["blocks"][str(self.plan["shards"][-1]["end"])]
        for name in JOURNAL_CLASSES:
            with self.subTest(component=name):
                self.assertEqual(scopes[name]["finality"], "finalized")
                self.assertEqual(scopes[name]["interval"]["start_hash"], first)
                self.assertEqual(scopes[name]["interval"]["end_hash"], last)
        for name in ("epoch-table", "error-receipts", CODE_COMPONENT, "interval-plan", "reconciliation", "registry"):
            with self.subTest(component=name):
                self.assertEqual(scopes[name]["finality"], "provider-reported")
                self.assertNotIn("start_hash", scopes[name]["interval"])
                self.assertNotIn("end_hash", scopes[name]["interval"])

    def test_the_start_hash_is_the_journals_first_block_read_and_not_the_shard_hash(self):
        staging, output = self.pipeline("source")
        self.build(staging, output)
        first = self.first_block_read(staging)
        self.assertEqual(first, self.state["blocks"][str(START)])
        self.assertNotEqual(first, self.state["blocks"][str(self.plan["shards"][0]["end"])])
        for name in JOURNAL_CLASSES:
            self.assertEqual(self.scopes(output)[name]["interval"]["start_hash"], first)

    def test_a_safe_plan_emits_safe_scopes(self):
        plan = deepcopy(self.plan)
        plan["finality"]["policy"] = "safe"
        staging, output = self.pipeline("safe", plan=plan)
        self.build(staging, output, plan=plan)
        for name in JOURNAL_CLASSES:
            scope = self.scopes(output)[name]
            self.assertEqual(scope["finality"], "safe")
            self.assertIn("start_hash", scope["interval"])
        check_interval(output)

    def test_a_confirmations_plan_stays_provider_reported_with_both_hashes(self):
        plan = deepcopy(self.plan)
        plan["finality"] = dict(plan["finality"], policy="confirmations", confirmations=64)
        staging, output = self.pipeline("confirmations", plan=plan)
        self.build(staging, output, plan=plan)
        for name in JOURNAL_CLASSES:
            scope = self.scopes(output)[name]
            self.assertEqual(scope["finality"], "provider-reported")
            self.assertEqual(scope["interval"]["start_hash"], self.first_block_read(staging))
        check_interval(output)

    def test_a_tree_with_no_epoch_evidence_journal_refuses_to_build(self):
        staging = self.scratch("no-journal")
        with self.assertRaises(_Killed):
            Collector(self.plan, staging, KillingTransport(self.state, kill_at=opening_labels()[0])).collect()
        self.assertFalse((staging / "journals" / f"{OPENING_CLASS}.jsonl").exists())
        with self.assertRaisesRegex(AlexandriaError, "no committed epoch-evidence journal"):
            self.build(staging, self.root / "no-journal-release")

    def test_a_tree_killed_in_the_opening_phase_refuses_to_build(self):
        staging = self.scratch("half-open")
        with self.assertRaises(_Killed):
            Collector(self.plan, staging, KillingTransport(self.state, kill_at=opening_labels()[4])).collect()
        with self.assertRaisesRegex(AlexandriaError, "opening reads are not completely collected"):
            self.build(staging, self.root / "half-open-release")

    def test_a_journal_the_checkpoint_has_not_committed_refuses_to_build(self):
        staging, output = self.pipeline("uncommitted")
        path = staging / "journals" / f"{OPENING_CLASS}.jsonl"
        path.write_bytes(path.read_bytes() + b"\n")
        with self.assertRaisesRegex(AlexandriaError, "bytes the checkpoint has not committed .* nothing to build"):
            self.build(staging, output)

    def test_a_scope_with_one_hash_is_refused_by_ingest_and_by_check(self):
        class HalfBound(Builder):
            def _capture(self, component, document, reconciliation, boundaries):
                capture = super()._capture(component, document, reconciliation, boundaries)
                capture["scope"]["interval"].pop("end_hash", None)
                return capture

        staging, output = self.pipeline("half")
        with self.assertRaisesRegex(AlexandriaError, "boundary hashes must be supplied together"):
            self.build(staging, output, builder=HalfBound)
        # `check` names it on its own, independent of Alexandria's verifier.
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        for capture in manifest["captures"]:
            if capture["id"] == "logs":
                del capture["scope"]["interval"]["end_hash"]
        (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
        with mock.patch.object(usdc_interval, "verify", return_value=manifest["release_id"]):
            with self.assertRaisesRegex(AlexandriaError, "the logs scope carries one boundary hash and not the other"):
                check_interval(output)

    def test_check_refuses_a_start_hash_the_first_block_read_does_not_carry(self):
        staging, output = self.pipeline("copied")
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        for capture in manifest["captures"]:
            if capture["id"] == "traces":
                capture["scope"]["interval"]["start_hash"] = self.state["blocks"][str(self.plan["shards"][0]["end"])]
        (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
        with mock.patch.object(usdc_interval, "verify", return_value=manifest["release_id"]):
            with self.assertRaisesRegex(AlexandriaError, "traces scope's start hash is not the hash the collector's first-block read carries"):
                check_interval(output)

    def test_check_refuses_a_scope_finality_the_plan_does_not_bind(self):
        staging, output = self.pipeline("class")
        self.build(staging, output)
        manifest = json.loads((output / "manifest.json").read_text())
        for capture in manifest["captures"]:
            if capture["id"] == OPENING_CLASS:
                capture["scope"]["finality"] = "provider-reported"
        (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
        with mock.patch.object(usdc_interval, "verify", return_value=manifest["release_id"]):
            with self.assertRaisesRegex(AlexandriaError, "carries finality provider-reported while the plan's policy binds finalized"):
                check_interval(output)

    def test_two_builds_over_one_tree_yield_one_identifier(self):
        staging, output = self.pipeline("twice")
        self.assertEqual(self.build(staging, output), self.build(staging, self.root / "twice-again"))

    def test_the_scope_binding_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            self.test_every_evidence_scope_is_finalized_with_both_hashes()


class CodeHashRecheckTests(ReleaseTestCase):
    """The conformance evidence for `code-hash-rechecked-from-component`.

    The `code-digest-rebind` guard: against a check that accepts a declared
    digest without re-hashing the component's bytes, every tampering case
    here that leaves the manifest's own digests alone passes for the wrong
    reason and fails this class.
    """

    def released(self, name="code"):
        staging, output = self.pipeline(name)
        self.build(staging, output)
        return output

    def rewrite(self, output, name, edit):
        """Edit one component's document in place, leaving the manifest as it was."""
        path = component_path(output, name)
        document = json.loads(path.read_text())
        edit(document)
        path.write_bytes(canonical_bytes(document))
        return document

    def rebind_component_digest(self, output):
        """Point the receipt at the component's current bytes, so only the epoch digests are wrong."""
        digest = hashlib.sha256(component_path(output, CODE_COMPONENT).read_bytes()).hexdigest()
        self.rewrite(output, "epoch-table", lambda receipt: receipt["implementation_code"].__setitem__("sha256", digest))

    def check_without_verify(self, output):
        release_id = json.loads((output / "manifest.json").read_text())["release_id"]
        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
            return check_interval(output)

    def test_the_epoch_table_names_the_component_and_each_epoch_names_its_digest(self):
        output = self.released()
        receipt = component_document(output, "epoch-table")
        component = component_document(output, CODE_COMPONENT)
        self.assertEqual(receipt["implementation_code"]["component"], CODE_COMPONENT)
        self.assertEqual(
            receipt["implementation_code"]["sha256"],
            hashlib.sha256(component_path(output, CODE_COMPONENT).read_bytes()).hexdigest(),
        )
        bodies = {record["address"]: record["code"] for record in component["records"]}
        self.assertEqual(set(bodies), {IMPLEMENTATION_A, IMPLEMENTATION_B})
        for epoch in receipt["epochs"]:
            self.assertEqual(
                epoch["implementation_code_sha256"],
                hashlib.sha256(bytes.fromhex(bodies[epoch["implementation"]][2:])).hexdigest(),
            )
        summary = self.check_without_verify(output)
        self.assertEqual(summary["implementations"], {
            epoch["implementation"]: epoch["implementation_code_sha256"] for epoch in receipt["epochs"]
        })

    def test_one_flipped_byte_in_the_component_is_refused_by_name(self):
        output = self.released("flipped")
        path = component_path(output, CODE_COMPONENT)
        data = path.read_bytes()
        position = data.index(b"0x60806040") + 12
        flipped = data[:position] + (b"0" if data[position:position + 1] != b"0" else b"1") + data[position + 1:]
        path.write_bytes(flipped)
        with self.assertRaisesRegex(AlexandriaError, "component implementation-code digest does not match"):
            check_interval(output)
        with self.assertRaisesRegex(AlexandriaError, "names implementation-code digest .* but the component's bytes hash to"):
            self.check_without_verify(output)
        self.rebind_component_digest(output)
        with self.assertRaisesRegex(AlexandriaError, "names implementation code digest .* which the preserved bytes do not carry"):
            self.check_without_verify(output)

    def test_one_changed_hex_digit_in_an_epoch_digest_is_refused_by_name(self):
        output = self.released("digit")

        def change(receipt):
            digest = receipt["epochs"][1]["implementation_code_sha256"]
            receipt["epochs"][1]["implementation_code_sha256"] = ("0" if digest[0] != "0" else "1") + digest[1:]

        self.rewrite(output, "epoch-table", change)
        with self.assertRaisesRegex(AlexandriaError, "component epoch-table digest does not match"):
            check_interval(output)
        with self.assertRaisesRegex(
            AlexandriaError, f"the epoch at block {UPGRADE} names implementation code digest .* for {IMPLEMENTATION_B}, which the preserved bytes do not carry",
        ):
            self.check_without_verify(output)

    def test_an_implementation_missing_from_the_component_is_refused_by_name(self):
        output = self.released("missing")
        self.rewrite(
            output, CODE_COMPONENT,
            lambda component: component["records"].__delitem__(
                next(i for i, r in enumerate(component["records"]) if r["address"] == IMPLEMENTATION_B)
            ),
        )
        self.rebind_component_digest(output)
        with self.assertRaisesRegex(AlexandriaError, f"implementation {IMPLEMENTATION_B}, .* is missing from the implementation-code component"):
            self.check_without_verify(output)

    def test_a_stray_implementation_in_the_component_is_refused(self):
        output = self.released("stray")
        self.rewrite(
            output, CODE_COMPONENT,
            lambda component: component["records"].append({"address": "0x" + "ab" * 20, "code": "0x6080"}),
        )
        self.rebind_component_digest(output)
        with self.assertRaisesRegex(AlexandriaError, "which no epoch names"):
            self.check_without_verify(output)

    def test_a_release_carrying_a_journal_the_plan_did_not_declare_is_refused(self):
        class Smuggling(Builder):
            """Adds a `traces` journal component the plan never declared."""

            def _reconciliation(self):
                # After the checkpoint is read and before the journals are
                # written: the release gains an empty `traces` journal.
                self.staging.classes = tuple(self.staging.classes) + ("traces",)
                return super()._reconciliation()

        plan = deepcopy(self.plan)
        plan["evidence_classes"] = ["boundary-blocks", "logs"]
        staging, output = self.pipeline("undeclared", plan=plan)
        self.build(staging, output, builder=Smuggling, plan=plan)
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertIn("traces", {component["name"] for component in manifest["components"]})
        with self.assertRaisesRegex(AlexandriaError, "carries a traces component the plan does not declare"):
            check_interval(output)

    def test_a_journal_whose_class_disagrees_with_its_component_is_refused(self):
        class Relabelling(Builder):
            def _journal(self, name):
                journal = super()._journal(name)
                if name == "traces":
                    journal["class"] = "logs"
                return journal

        staging, output = self.pipeline("relabelled")
        self.build(staging, output, builder=Relabelling)
        with self.assertRaisesRegex(AlexandriaError, "traces component carries a logs journal, so the plan and the journals disagree"):
            check_interval(output)

    def test_a_release_lacking_a_declared_journal_is_refused(self):
        output = self.released("lacking")
        manifest = json.loads((output / "manifest.json").read_text())
        manifest["components"] = [c for c in manifest["components"] if c["name"] != "traces"]
        manifest["captures"] = [c for c in manifest["captures"] if c["id"] != "traces"]
        (output / "manifest.json").write_text(json.dumps(manifest, sort_keys=True))
        with self.assertRaisesRegex(AlexandriaError, "lacks its traces component"):
            self.check_without_verify(output)

    def test_a_journal_record_whose_request_or_response_is_not_text_is_refused_by_name(self):
        """A release is somebody else's bytes: a number where text belongs refuses by name."""
        for component, field in ((OPENING_CLASS, "request"), ("logs", "response")):
            with self.subTest(component=component, field=field):
                output = self.released(f"not-text-{component}-{field}")
                self.rewrite(
                    output, component,
                    lambda document: document["records"][0].__setitem__(field, 5),
                )
                raised = None
                try:
                    self.check_without_verify(output)
                except Exception as error:  # noqa: BLE001 - the type is the claim
                    raised = error
                # A parent that reads the field without checking it raises an
                # AttributeError here, which is why the type is asserted rather
                # than matched: the claim is a named refusal, not any failure.
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(
                    str(raised),
                    f"a {component} journal record carries a {field} that is not text",
                )

    def test_a_journal_record_whose_shard_index_is_not_a_whole_number_is_refused_by_name(self):
        """The shard index is a set element and a dictionary key, so its type is checked too."""
        for value, label in ((["x"], "list"), ({"a": 1}, "object"), (True, "boolean")):
            with self.subTest(label=label):
                output = self.released(f"not-a-shard-{label}")
                self.rewrite(
                    output, "logs",
                    lambda document: document["records"][0].__setitem__("shard", value),
                )
                raised = None
                try:
                    self.check_without_verify(output)
                except Exception as error:  # noqa: BLE001 - the type is the claim
                    raised = error
                # A parent that checks only the key set raises a TypeError on
                # the unhashable values and accepts the boolean as shard one,
                # so the type is asserted rather than matched.
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(
                    str(raised),
                    "a logs journal record carries a shard index that is not a whole number",
                )

    def test_a_reconciliation_component_of_an_unknown_shape_is_refused_by_name(self):
        """The last record shape the check reads is shape-checked like the others."""
        cases = (
            ("null-record", lambda document: document.__setitem__("reconciliation", None),
             "records no reconciliation"),
            ("no-plan-digest", lambda document: document.pop("plan_sha256"),
             "reconciliation component has an unknown shape"),
            ("no-record", lambda document: document.pop("reconciliation"),
             "reconciliation component has an unknown shape"),
            ("wrong-format", lambda document: document.__setitem__("format", "other/v1"),
             "reconciliation component has an unknown shape"),
        )
        for label, edit, expected in cases:
            with self.subTest(label=label):
                output = self.released(f"reconciliation-shape-{label}")
                self.rewrite(output, "reconciliation", edit)
                raised = None
                try:
                    self.check_without_verify(output)
                except Exception as error:  # noqa: BLE001 - the type is the claim
                    raised = error
                # A parent that reads the component's fields without checking
                # them raises a KeyError on an absent field and a TypeError on
                # a null record where the status is read at the return, and
                # accepts a wrong format, so the type is asserted rather than
                # matched: the claim is a named refusal, not any failure.
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(str(raised), expected)

    def test_a_receipt_declaring_another_comparison_than_the_record_is_refused(self):
        """The receipt's copy of the comparison is not believed on its own word."""
        output = self.released("fabricated-comparison")
        self.rewrite(
            output, "reconciliation",
            lambda document: document["reconciliation"].__setitem__("status", "unreconciled"),
        )
        raised = None
        try:
            self.check_without_verify(output)
        except Exception as error:  # noqa: BLE001 - the type is the claim
            raised = error
        # A parent compares only the record's own copy, so it accepts the
        # receipt's `agreed` beside a record that says otherwise.
        self.assertIsInstance(raised, AlexandriaError)
        self.assertRegex(str(raised), "declare different comparisons")

    def test_an_epoch_table_the_opening_reads_do_not_derive_is_refused(self):
        output = self.released("undeclared-epoch")

        def move_boundary(receipt):
            receipt["epochs"][0]["end_block"] = str(UPGRADE)
            receipt["epochs"][1]["start_block"] = str(UPGRADE + 1)
            receipt["epochs"][1]["upgrade"]["block_number"] = str(UPGRADE + 1)

        self.rewrite(output, "epoch-table", move_boundary)
        with self.assertRaisesRegex(AlexandriaError, "does not match the epochs the preserved opening reads derive|does not open its epoch|block envelope"):
            self.check_without_verify(output)

    def test_check_prints_the_epoch_count_and_the_rehashed_digests(self):
        output = self.released("printed")
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / "usdc_interval.py"), "check", str(output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        printed = json.loads(result.stdout)
        self.assertEqual(printed["epochs"], 2)
        self.assertEqual(set(printed["implementations"]), {IMPLEMENTATION_A, IMPLEMENTATION_B})
        for digest in printed["implementations"].values():
            self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_the_build_command_takes_no_epoch_table(self):
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / "usdc_interval.py"), "build", "--help"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("--epochs", result.stdout)
        self.assertIn("--registry", result.stdout)

    def test_the_recheck_opens_no_socket_and_changes_no_file(self):
        output = self.released("offline")
        before = {p.relative_to(output): p.read_bytes() for p in sorted(output.rglob("*")) if p.is_file()}
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            check_interval(output)
        after = {p.relative_to(output): p.read_bytes() for p in sorted(output.rglob("*")) if p.is_file()}
        self.assertEqual(after, before)


class DeclaredValueRecheckTests(ReleaseTestCase):
    """Every quantity the release declares is compared with the bytes it describes.

    Against a check that reads a declared value without recomputing it, each
    case here passes for the wrong reason: the shard table's boundary hash
    stood beside the preserved read that produced it and was never compared
    with it, the reconciliation record carried its own uncompared copy of the
    shard table's hashes and counts, an evidence scope declared a block range
    nothing held against the plan's, and a shard's record count named one
    read where the journal carried two.
    """

    def released(self, name="declared"):
        staging, output = self.pipeline(name)
        self.build(staging, output)
        return output

    def rewrite(self, output, name, edit):
        """Edit one component's document in place, leaving the manifest as it was."""
        path = component_path(output, name)
        document = json.loads(path.read_text())
        edit(document)
        path.write_bytes(canonical_bytes(document))
        return document

    def rewrite_manifest(self, output, edit):
        path = output / "manifest.json"
        manifest = json.loads(path.read_text())
        edit(manifest)
        path.write_bytes(canonical_bytes(manifest))
        return manifest

    def check_without_verify(self, output):
        release_id = json.loads((output / "manifest.json").read_text())["release_id"]
        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
            return check_interval(output)

    def refusal(self, output):
        try:
            self.check_without_verify(output)
        except Exception as error:  # noqa: BLE001 - the type is the claim
            return error
        return None

    def boundary_record(self, document, shard):
        return next(
            record for record in document["records"] if record["shard"] == shard
        )

    def set_boundary_result(self, output, shard, edit):
        def rewrite(document):
            record = self.boundary_record(document, shard)
            envelope = json.loads(record["response"])
            edit(envelope["result"])
            record["response"] = json.dumps(
                envelope, separators=(",", ":"), sort_keys=True
            )

        self.rewrite(output, "boundary-blocks", rewrite)

    def test_a_shard_boundary_hash_is_compared_with_its_preserved_read(self):
        """The declared hash and the read that produced it cannot move apart."""
        fabricated = "0x" + "de" * 32
        cases = (
            (
                "declared-hash",
                lambda output: (
                    self.rewrite(
                        output, "epoch-table",
                        lambda receipt: receipt["shards"][0].__setitem__("end_hash", fabricated),
                    ),
                    self.rewrite(
                        output, "reconciliation",
                        lambda record: record["shards"][0].__setitem__("end_hash", fabricated),
                    ),
                ),
                "shard 0 declares boundary hash .* which its preserved boundary read does not carry",
            ),
            (
                "preserved-hash",
                lambda output: self.set_boundary_result(
                    output, 0, lambda result: result.__setitem__("hash", fabricated)
                ),
                "shard 0 declares boundary hash .* which its preserved boundary read does not carry",
            ),
            (
                "preserved-number",
                lambda output: self.set_boundary_result(
                    output, 0, lambda result: result.__setitem__("number", "0xdeadbe")
                ),
                "preserves block 0xdeadbe, not the shard's last block",
            ),
            (
                "no-number",
                lambda output: self.set_boundary_result(
                    output, 0, lambda result: result.pop("number")
                ),
                "block number is not a hexadecimal quantity",
            ),
            (
                "no-header",
                lambda output: self.set_boundary_result(
                    output, 0, lambda result: result.pop("hash")
                ),
                "the boundary-blocks record for shard 0 preserves no block header",
            ),
        )
        for label, edit, expected in cases:
            with self.subTest(label=label):
                output = self.released(f"boundary-{label}")
                edit(output)
                # A parent compares the last shard's hash only with the epoch
                # table, which its own derivation takes from that same
                # declared value, so every case here is accepted there.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(str(raised), expected)

    def test_the_last_shards_boundary_hash_is_compared_with_its_preserved_read(self):
        """The interval's own end hash is bound to a read, not to itself."""
        output = self.released("boundary-last")
        receipt = component_document(output, "epoch-table")
        last = receipt["shards"][-1]
        fabricated = "0x" + "ab" * 32
        self.set_boundary_result(
            output, last["index"], lambda result: result.__setitem__("hash", fabricated)
        )
        raised = self.refusal(output)
        self.assertIsInstance(raised, AlexandriaError)
        self.assertRegex(
            str(raised),
            f"shard {last['index']} declares boundary hash .* which its preserved "
            "boundary read does not carry",
        )

    def test_a_reconciliation_shard_table_differing_from_the_receipts_is_refused(self):
        """The two copies of one shard table must agree entry for entry."""
        cases = (
            ("end-hash", lambda entry: entry.__setitem__("end_hash", "0x" + "cd" * 32)),
            ("record-counts", lambda entry: entry["record_counts"].__setitem__("logs", 9999)),
        )
        for label, edit in cases:
            with self.subTest(label=label):
                output = self.released(f"reconciliation-table-{label}")
                # A parent compares only the two tables' statuses, so a
                # fabricated hash or count in this copy is accepted there and
                # read by nothing else.
                self.rewrite(
                    output, "reconciliation", lambda record: edit(record["shards"][0])
                )
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(str(raised), "disagree about a shard")

    def test_an_evidence_scope_declaring_another_block_range_is_refused(self):
        """The range beside the two checked hashes is checked as well."""
        for name in JOURNAL_CLASSES:
            with self.subTest(component=name):
                output = self.released(f"scope-range-{name}")

                def edit(manifest, component=name):
                    for capture in manifest["captures"]:
                        if capture["id"] == component:
                            interval = capture["scope"]["interval"]
                            interval["start"] = str(int(interval["start"]) + 1)

                self.rewrite_manifest(output, edit)
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(str(raised), f"the {name} scope declares blocks .* not the plan's")

    def test_a_capture_that_names_no_component_of_the_release_is_refused(self):
        """The coverage and the scope are read under the component's own name."""
        output = self.released("capture-id")

        def edit(manifest):
            for capture in manifest["captures"]:
                if capture["id"] == "traces":
                    capture["id"] = "x"

        self.rewrite_manifest(output, edit)
        # A parent indexes the capture map straight, so this raises a KeyError
        # where the coverage gaps are read rather than refusing by name.
        raised = self.refusal(output)
        self.assertIsInstance(raised, AlexandriaError)
        self.assertRegex(str(raised), "carries no capture for its traces component")

    def test_a_shard_carrying_one_class_twice_declares_both_reads(self):
        """A record count names what the journal holds, not its last record alone."""
        output = self.released("duplicate-read")
        journal = component_document(output, "logs")
        original = next(record for record in journal["records"] if record["shard"] == 0)

        def duplicate(document):
            record = next(item for item in document["records"] if item["shard"] == 0)
            document["records"].insert(1, deepcopy(record))

        self.rewrite(output, "logs", duplicate)
        # A parent assigns each record's size to its shard rather than adding
        # it, so the second read leaves the declared count untouched and the
        # release carries evidence its own receipt does not count.
        raised = self.refusal(output)
        self.assertIsInstance(raised, AlexandriaError)
        self.assertRegex(str(raised), "shard 0 declares record counts the journals do not carry")
        self.assertEqual(original["shard"], 0)

    def test_a_second_boundary_read_for_one_shard_is_refused(self):
        """One shard has one boundary read, so a second cannot supplant it."""
        fabricated = "0x" + "ab" * 32
        for label, index in (("first", 0), ("last", -1)):
            with self.subTest(shard=label):
                output = self.released(f"boundary-twice-{label}")
                receipt = component_document(output, "epoch-table")
                shard = receipt["shards"][index]

                def duplicate(document, target=shard["index"]):
                    record = self.boundary_record(document, target)
                    copied = deepcopy(record)
                    envelope = json.loads(copied["response"])
                    envelope["result"]["hash"] = fabricated
                    copied["response"] = json.dumps(
                        envelope, separators=(",", ":"), sort_keys=True
                    )
                    document["records"].append(copied)

                def declare(table, target=shard["index"]):
                    entry = next(item for item in table if item["index"] == target)
                    entry["end_hash"] = fabricated
                    entry["record_counts"]["boundary-blocks"] = 2

                def rebind(receipt, target=shard["end"]):
                    declare(receipt["shards"])
                    for epoch in receipt["epochs"]:
                        if int(epoch["end_block"]) == target:
                            epoch["end_hash"] = fabricated

                self.rewrite(output, "boundary-blocks", duplicate)
                self.rewrite(output, "epoch-table", rebind)
                self.rewrite(output, "reconciliation", lambda record: declare(record["shards"]))
                # A parent keeps the last record it reads for the shard, so the
                # fabricated read stands beside the genuine one and the
                # comparison with the preserved bytes is made against it.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(
                    str(raised),
                    f"the boundary-blocks journal holds shard {shard['index']} twice",
                )

    def test_a_shard_record_that_is_not_the_planned_read_is_refused(self):
        """The request a record preserves must be the read its shard names."""
        cases = (
            (
                "logs-range",
                "logs",
                lambda request: request["params"][0].update(
                    {"fromBlock": "0x1", "toBlock": "0x2"}
                ),
            ),
            (
                "logs-address",
                "logs",
                lambda request: request["params"][0].__setitem__(
                    "address", "0x" + "11" * 20
                ),
            ),
            (
                "boundary-method",
                "boundary-blocks",
                lambda request: request.update({"method": "eth_chainId", "params": []}),
            ),
        )
        for label, name, edit in cases:
            with self.subTest(case=label):
                output = self.released(f"planned-read-{label}")

                def rewrite(document, edit=edit):
                    record = next(
                        item for item in document["records"] if item["shard"] == 0
                    )
                    request = json.loads(record["request"])
                    edit(request)
                    record["request"] = json.dumps(
                        request, separators=(",", ":"), sort_keys=True
                    )

                self.rewrite(output, name, rewrite)
                # A parent reads the response and never the request, so a read
                # of another range, another address or another method stands
                # for the shard it is filed under.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(
                    str(raised),
                    f"the {name} record filed under shard 0 is not the read the plan names there",
                )

    def test_an_entry_outside_its_shards_blocks_is_refused(self):
        """A read bounded by the shard cannot return an entry from outside it."""
        for name, block in (("logs", "0x1"), ("traces", 1)):
            with self.subTest(component=name):
                output = self.released(f"entry-outside-{name}")

                def rewrite(document, block=block):
                    record = next(
                        item for item in document["records"] if item["shard"] == 0
                    )
                    envelope = json.loads(record["response"])
                    envelope["result"][0]["blockNumber"] = block
                    record["response"] = json.dumps(
                        envelope, separators=(",", ":"), sort_keys=True
                    )

                self.rewrite(output, name, rewrite)
                # A parent counts the entries and reads no entry's block, so an
                # entry from any block at all is carried as the shard's
                # evidence.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(str(raised), "names block 1, outside the shard's blocks")

    def test_a_response_that_is_not_the_answer_to_its_request_is_refused(self):
        """The collector refuses these envelopes; the release is held to the same rule."""
        cases = (
            (
                "json-rpc-error",
                "logs",
                lambda envelope: (
                    envelope.pop("result"),
                    envelope.__setitem__("error", {"code": -32000, "message": "boom"}),
                ),
                "the logs response for shard 0 is not the answer its preserved request names",
            ),
            (
                "another-read",
                "logs",
                lambda envelope: envelope.__setitem__("id", 999),
                "the logs response for shard 0 is not the answer its preserved request names",
            ),
            (
                "no-result",
                "traces",
                lambda envelope: envelope.pop("result"),
                "the traces response for shard 0 is not the answer its preserved request names",
            ),
            (
                "result-not-a-list",
                "logs",
                lambda envelope: envelope.__setitem__("result", {"note": "one read"}),
                "the logs result for shard 0 is not a list of entries",
            ),
        )
        for label, name, edit, expected in cases:
            with self.subTest(case=label):
                output = self.released(f"envelope-{label}")

                def rewrite(document, edit=edit):
                    record = next(
                        item for item in document["records"] if item["shard"] == 0
                    )
                    envelope = json.loads(record["response"])
                    edit(envelope)
                    record["response"] = json.dumps(
                        envelope, separators=(",", ":"), sort_keys=True
                    )

                self.rewrite(output, name, rewrite)
                # A parent reads `result` off the envelope and nothing else, so
                # a preserved error, another read's answer, or a result of any
                # shape at all counts as one read of this shard.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(str(raised), expected)

    def test_a_preserved_read_the_collector_would_have_stopped_for_is_refused(self):
        """A marked or page-filled answer is not a complete read of its shard."""
        output = self.released("truncated-envelope")

        def mark(document):
            record = next(item for item in document["records"] if item["shard"] == 0)
            envelope = json.loads(record["response"])
            envelope["truncated"] = True
            record["response"] = json.dumps(
                envelope, separators=(",", ":"), sort_keys=True
            )

        self.rewrite(output, "logs", mark)
        raised = self.refusal(output)
        self.assertIsInstance(raised, AlexandriaError)
        self.assertRegex(str(raised), "the logs response for shard 0 is marked truncated")

        output = self.released("page-limit")
        journal = component_document(output, "logs")
        record = next(item for item in journal["records"] if item["shard"] == 0)
        entries = len(json.loads(record["response"])["result"])
        self.rewrite(
            output, "interval-plan",
            lambda plan: plan["provider"].__setitem__("page_limit", entries),
        )
        self.rewrite(
            output, "reconciliation",
            lambda reconciliation: reconciliation.__setitem__(
                "plan_sha256", plan_digest(component_document(output, "interval-plan"))
            ),
        )
        # A parent reads neither the marker nor the page limit from the
        # release, so a read the collector would have refused stands as a
        # complete shard.
        raised = self.refusal(output)
        self.assertIsInstance(raised, AlexandriaError)
        self.assertRegex(
            str(raised),
            "the logs result for shard 0 stands at the provider's page limit",
        )

    def test_a_preserved_opening_read_is_held_to_the_same_envelope_rule(self):
        """The opening journal binds the start hash and the epochs, so it is read no weaker."""
        cases = (
            (
                "json-rpc-error",
                lambda envelope: envelope.__setitem__(
                    "error", {"code": -32000, "message": "boom"}
                ),
                "the epoch-evidence response for opening read 0 is not the answer its "
                "preserved request names",
            ),
            (
                "another-read",
                lambda envelope: envelope.__setitem__("id", 999),
                "the epoch-evidence response for opening read 0 is not the answer its "
                "preserved request names",
            ),
            (
                "no-version",
                lambda envelope: envelope.pop("jsonrpc"),
                "the epoch-evidence response for opening read 0 is not the answer its "
                "preserved request names",
            ),
            (
                "truncated",
                lambda envelope: envelope.__setitem__("truncated", True),
                "the epoch-evidence response for opening read 0 is marked truncated",
            ),
        )
        for label, edit, expected in cases:
            with self.subTest(case=label):
                output = self.released(f"opening-envelope-{label}")

                def rewrite(document, edit=edit):
                    record = document["records"][0]
                    envelope = json.loads(record["response"])
                    edit(envelope)
                    record["response"] = json.dumps(
                        envelope, separators=(",", ":"), sort_keys=True
                    )

                self.rewrite(output, "epoch-evidence", rewrite)
                # A parent applied the envelope rule inside the shard
                # journals' own loop, so the opening journal -- read by
                # `_replay_release_opening` instead -- took `result` off the
                # envelope and nothing else, and an answer the collector
                # would have refused derived the epoch table.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(str(raised), expected)

    def test_an_entry_naming_another_address_than_its_read_is_refused(self):
        """A bounded read names one address, so an entry naming another is not its answer."""
        foreign = "0x" + "de" * 20
        cases = (
            ("logs", lambda entry: entry.__setitem__("address", foreign)),
            ("traces", lambda entry: entry["action"].__setitem__("to", foreign)),
            ("traces-no-recipient", lambda entry: entry.pop("action")),
        )
        for label, edit in cases:
            name = label.split("-")[0]
            with self.subTest(component=label):
                output = self.released(f"entry-address-{label}")

                def rewrite(document, edit=edit):
                    record = next(
                        item for item in document["records"] if item["shard"] == 0
                    )
                    envelope = json.loads(record["response"])
                    edit(envelope["result"][0])
                    record["response"] = json.dumps(
                        envelope, separators=(",", ":"), sort_keys=True
                    )

                self.rewrite(output, name, rewrite)
                # A parent binds each entry's block and reads no other field,
                # so another contract's entry is carried as this market's
                # evidence.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(
                    str(raised),
                    f"a {name} entry for shard 0 names (address {foreign}, not the|no address)",
                )

    def test_a_second_read_of_any_class_for_one_shard_is_refused(self):
        """One read per shard and class is what the collector writes, for every class."""
        for name in ("logs", "traces"):
            with self.subTest(component=name):
                output = self.released(f"second-read-{name}")

                def duplicate(document):
                    record = next(
                        item for item in document["records"] if item["shard"] == 0
                    )
                    document["records"].append(deepcopy(record))

                def declare(table, component=name):
                    entry = next(item for item in table if item["index"] == 0)
                    entry["record_counts"][component] *= 2

                self.rewrite(output, name, duplicate)
                self.rewrite(output, "epoch-table", lambda receipt: declare(receipt["shards"]))
                self.rewrite(
                    output, "reconciliation", lambda record: declare(record["shards"])
                )
                # A parent refuses a second read for the boundary class alone,
                # so a second read of this class stands beside the genuine one
                # and the receipt declares their sum as reads that were made.
                raised = self.refusal(output)
                self.assertIsInstance(raised, AlexandriaError)
                self.assertRegex(
                    str(raised),
                    f"the {name} journal holds shard 0 twice, so two reads claim that "
                    f"shard's {name} evidence",
                )


class CheckpointOpeningOffsetTests(CollectorTestCase):
    """A checkpoint below the plan's last shard cannot have committed an opening read."""

    def test_an_opening_offset_under_an_uncollected_shard_refuses(self):
        with self.assertRaises(_Killed):
            Collector(self.plan, self.root, KillingTransport(self.state, kill_at="shard 3 logs")).collect()
        state = checkpoint(self.root)
        self.assertEqual(state["next_shard"], 3)
        state["offsets"][OPENING_CLASS] = 1
        state["history"][-1]["offsets"][OPENING_CLASS] = 1
        with self.assertRaisesRegex(AlexandriaError, "commits opening reads while a shard is still uncollected"):
            validate_checkpoint(state, plan_digest(self.plan), len(self.plan["shards"]), JOURNAL_CLASSES)
        (self.root / "checkpoint.json").write_bytes(canonical_bytes(state))
        with self.assertRaisesRegex(AlexandriaError, "commits opening reads while a shard is still uncollected"):
            Staging(self.root, self.plan).committed()

    def test_a_history_entry_committing_opening_reads_under_an_earlier_shard_refuses(self):
        self.collect()
        state = checkpoint(self.root)
        state["history"][0]["offsets"][OPENING_CLASS] = 1
        with self.assertRaisesRegex(AlexandriaError, "under a shard that is not the plan's last"):
            validate_checkpoint(state, plan_digest(self.plan), len(self.plan["shards"]), JOURNAL_CLASSES)

    def test_a_completed_checkpoint_is_accepted(self):
        self.collect()
        validate_checkpoint(checkpoint(self.root), plan_digest(self.plan), len(self.plan["shards"]), JOURNAL_CLASSES)


if __name__ == "__main__":
    unittest.main()
