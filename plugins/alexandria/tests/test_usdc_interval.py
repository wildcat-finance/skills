"""Collecting a bounded interval: bounds, refusals, resume and reorg rewind."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import EVIDENCE_CLASSES, Staging  # noqa: E402
import usdc_interval  # noqa: E402
from usdc_interval import (  # noqa: E402
    Collector,
    HttpsTransport,
    Reconciler,
    TransportError,
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

    def __init__(self, state, *, reorg_from=None, faults=None):
        self.state = state
        self.reorg_from = reorg_from
        self.faults = dict(faults or {})
        self.calls = []

    def _hash(self, number):
        """A finalized boundary does not reorg, so the fixture never moves it."""
        final = int(self.state["plan"]["finality"]["block_number"])
        if self.reorg_from is not None and self.reorg_from <= number < final:
            return "0x" + f"{number:064x}"
        return self.state["blocks"][str(number)]

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
            result = self.state["logs"][str(shard["index"])]
        else:
            shard = self._shard_for(int(envelope["params"][0]["toBlock"], 16))
            result = self.state["traces"][str(shard["index"])]
        return canonical_bytes({"id": identifier, "jsonrpc": "2.0", "result": result})


def journals(root):
    return {
        name: (Path(root) / "journals" / f"{name}.jsonl").read_bytes()
        for name in EVIDENCE_CLASSES
        if (Path(root) / "journals" / f"{name}.jsonl").is_file()
    }


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
        self.assertEqual(sorted(journals(self.root)), sorted(EVIDENCE_CLASSES))

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
                       "Content-Type", "Authorization"):
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
        index = self._shard_index(number)
        override = self.disagreements.get("boundary_hash_overrides", {}).get(index)
        return override if override else super()._hash(number)

    def transactions(self, number):
        index = self._shard_index(number)
        order = self.disagreements.get("transaction_orders", {}).get(index)
        return list(order) if order else super().transactions(number)

    def request(self, payload, label):
        data = super().request(payload, label)
        envelope = json.loads(data)
        method = json.loads(payload)["method"]
        if method == "eth_getLogs":
            shard = self._shard_for(int(json.loads(payload)["params"][0]["toBlock"], 16))
            extra = self.disagreements.get("extra_logs", {}).get(str(shard["index"]))
            if extra:
                envelope["result"] = list(envelope["result"]) + list(extra)
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


if __name__ == "__main__":
    unittest.main()
