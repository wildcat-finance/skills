"""The Step 9 targeted-tracing and concurrency redesign.

Covers what `test_usdc_interval.py` and `test_wildcat_venue.py` do not: the
log-to-transaction-hash derivation, the per-transaction trace filter
(including a frame it must drop, and a real offline equivalence proof against
shard 0's genuine mainnet capture), the synthesized combined `traces`
record's shape and the exactly-once `Staging.record` call every other class
already relies on, concurrent shard fetch with strictly ordered commits
(including a resume after an interruption with shards fetched out of arrival
order), and reconciliation's own independent second-transport trace
derivation and comparison. The Compound single-proxy path is exercised only
to prove concurrency works there too -- it never reaches targeted tracing,
which stays gated on a declared subject set.
"""

from copy import deepcopy
import concurrent.futures
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import threading
import time
import unittest
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.errors import AlexandriaError  # noqa: E402
import usdc_interval  # noqa: E402
from usdc_interval import Collector, Reconciler  # noqa: E402

from tests import test_usdc_interval as existing  # noqa: E402
from tests import test_wildcat_venue as wildcat  # noqa: E402


class SubjectTransactionHashesTests(unittest.TestCase):
    """`subject_transaction_hashes`: the shard's own `logs` result, no new call."""

    def test_derives_distinct_hashes_ordered_by_block_and_transaction_index(self):
        logs = [
            {"transactionHash": "0x" + "bb" * 32, "blockNumber": "0x2", "transactionIndex": "0x0"},
            {"transactionHash": "0x" + "aa" * 32, "blockNumber": "0x1", "transactionIndex": "0x5"},
            # A second log of the same transaction: deduplicated, not a second hash.
            {"transactionHash": "0x" + "bb" * 32, "blockNumber": "0x2", "transactionIndex": "0x0"},
            {"transactionHash": "0x" + "cc" * 32, "blockNumber": "0x2", "transactionIndex": "0x3"},
        ]
        hashes = usdc_interval.subject_transaction_hashes(logs)
        self.assertEqual(hashes, ["0x" + "aa" * 32, "0x" + "bb" * 32, "0x" + "cc" * 32])

    def test_an_empty_shard_derives_no_hashes(self):
        self.assertEqual(usdc_interval.subject_transaction_hashes([]), [])

    def test_refuses_a_non_list_result(self):
        with self.assertRaisesRegex(AlexandriaError, "not a list"):
            usdc_interval.subject_transaction_hashes(None)

    def test_refuses_a_log_with_no_transaction_hash(self):
        with self.assertRaisesRegex(AlexandriaError, "no transaction hash"):
            usdc_interval.subject_transaction_hashes(
                [{"blockNumber": "0x1", "transactionIndex": "0x0"}]
            )


class MatchesSubjectsTests(unittest.TestCase):
    """`_matches_subjects` mirrors `trace_filter`'s own `toAddress` matching, per trace type."""

    SUBJECTS = frozenset({"0x" + "11" * 20, "0x" + "22" * 20})

    def test_a_call_matches_on_its_to_address(self):
        frame = {"type": "call", "action": {"to": "0x" + "11" * 20, "from": "0x" + "99" * 20}}
        self.assertTrue(usdc_interval._matches_subjects(frame, self.SUBJECTS))

    def test_a_call_to_an_unrelated_address_is_dropped(self):
        frame = {"type": "call", "action": {"to": "0x" + "99" * 20, "from": "0x" + "11" * 20}}
        self.assertFalse(usdc_interval._matches_subjects(frame, self.SUBJECTS))

    def test_a_create_matches_on_its_result_address(self):
        frame = {
            "type": "create", "action": {"from": "0x" + "99" * 20},
            "result": {"address": "0x" + "22" * 20},
        }
        self.assertTrue(usdc_interval._matches_subjects(frame, self.SUBJECTS))

    def test_a_reverted_create_has_no_result_and_matches_nothing(self):
        frame = {"type": "create", "action": {"from": "0x" + "99" * 20}, "error": "Reverted"}
        self.assertFalse(usdc_interval._matches_subjects(frame, self.SUBJECTS))

    def test_a_suicide_matches_on_its_refund_address(self):
        frame = {
            "type": "suicide",
            "action": {"address": "0x" + "99" * 20, "refundAddress": "0x" + "11" * 20},
        }
        self.assertTrue(usdc_interval._matches_subjects(frame, self.SUBJECTS))

    def test_a_reward_matches_on_its_author(self):
        frame = {"type": "reward", "action": {"author": "0x" + "22" * 20}}
        self.assertTrue(usdc_interval._matches_subjects(frame, self.SUBJECTS))

    def test_a_non_object_frame_matches_nothing(self):
        self.assertFalse(usdc_interval._matches_subjects("not a frame", self.SUBJECTS))


class _TraceTransactionTransport:
    """Answers `trace_transaction` from a fixed `{tx_hash: [frames]}` table; nothing else."""

    def __init__(self, table):
        self.table = table
        self.calls = []

    def request(self, payload, label):
        envelope = json.loads(payload)
        self.calls.append((envelope["method"], envelope["params"], label))
        if envelope["method"] != "trace_transaction":
            raise AssertionError(f"unexpected method {envelope['method']}")
        result = self.table[envelope["params"][0]]
        return usdc_interval.canonical_bytes(
            {"id": envelope["id"], "jsonrpc": "2.0", "result": result}
        )


class TargetedTraceConcurrencyTests(unittest.TestCase):
    """Concurrent reads retain the serial bytes and a bounded request window."""

    def setUp(self):
        self.state = wildcat.fixture(wildcat.wildcat_v2.VENUE)
        self.plan = self.state["plan"]
        self.registry = wildcat.registry()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.hashes = ["0x" + f"{index:064x}" for index in range(1, 7)]
        self.logs = [
            {"transactionHash": value, "blockNumber": "0x1", "transactionIndex": hex(index)}
            for index, value in enumerate(self.hashes)
        ]
        subject = self.plan["subjects"][0]
        self.table = {
            value: [{"transactionHash": value, "traceAddress": [], "type": "call",
                     "action": {"to": subject, "value": hex(index)},
                     "result": {"output": "0x1234"}}]
            for index, value in enumerate(self.hashes)
        }

    def make_owner(self, kind, transport, concurrency):
        if kind == "collect":
            return Collector(self.plan, self.root, transport, registry=self.registry,
                             trace_concurrency=concurrency)
        return Reconciler(self.plan, self.root, transport, "fixture-second",
                          registry=self.registry, trace_concurrency=concurrency)

    def fetch(self, owner):
        if isinstance(owner, Collector):
            _payload, data, frames = owner._targeted_traces(0, self.logs)
            return frames, data
        return owner._second_traces(0, self.hashes)

    def test_out_of_order_completion_preserves_serial_bytes_for_both_paths(self):
        for kind in ("collect", "reconcile"):
            with self.subTest(kind=kind):
                serial_transport = _TraceTransactionTransport(self.table)
                expected = self.fetch(self.make_owner(kind, serial_transport, 1))
                first, second = self.hashes[:2]
                table = self.table

                class Controlled(_TraceTransactionTransport):
                    def __init__(self):
                        super().__init__(table)
                        self.second_done = threading.Event()
                        self.lock = threading.Lock()
                        self.active = self.peak = 0
                        self.finished = []

                    def request(self, payload, label):
                        tx_hash = json.loads(payload)["params"][0]
                        with self.lock:
                            self.active += 1
                            self.peak = max(self.peak, self.active)
                        try:
                            if tx_hash == first and not self.second_done.wait(5):
                                raise AssertionError("second request never overlapped the first")
                            answer = super().request(payload, label)
                            self.finished.append(tx_hash)
                            if tx_hash == second:
                                self.second_done.set()
                            return answer
                        finally:
                            with self.lock:
                                self.active -= 1

                transport = Controlled()
                actual = self.fetch(self.make_owner(kind, transport, 2))
                self.assertEqual(actual, expected)
                self.assertEqual(transport.peak, 2)
                self.assertEqual(transport.finished[0], second)
                self.assertCountEqual([params[0] for _, params, _ in transport.calls], self.hashes)
                self.assertEqual([params[0] for _, params, _ in serial_transport.calls], self.hashes)

    def test_a_slow_first_call_does_not_idle_the_rest_of_the_window(self):
        for kind in ("collect", "reconcile"):
            with self.subTest(kind=kind):
                expected = self.fetch(self.make_owner(kind, _TraceTransactionTransport(self.table), 1))
                first, rest = self.hashes[0], self.hashes[1:]
                table = self.table

                class SlowFirst(_TraceTransactionTransport):
                    def __init__(self):
                        super().__init__(table)
                        self.rest_done = threading.Event()
                        self.lock = threading.Lock()
                        self.active = self.peak = 0
                        self.finished = []

                    def request(self, payload, label):
                        tx_hash = json.loads(payload)["params"][0]
                        with self.lock:
                            self.active += 1
                            self.peak = max(self.peak, self.active)
                        try:
                            # A batch loop asks for no third hash while the
                            # first is outstanding, so this wait times out.
                            if tx_hash == first and not self.rest_done.wait(5):
                                raise AssertionError("the window did not refill while the first call was slow")
                            answer = super().request(payload, label)
                            with self.lock:
                                self.finished.append(tx_hash)
                                if len(self.finished) == len(rest):
                                    self.rest_done.set()
                            return answer
                        finally:
                            with self.lock:
                                self.active -= 1

                transport = SlowFirst()
                actual = self.fetch(self.make_owner(kind, transport, 2))
                self.assertEqual(actual, expected)
                self.assertEqual(transport.finished, rest + [first])
                self.assertEqual(transport.peak, 2)

    def test_failure_stops_refilling_and_never_stages_a_partial_trace_result(self):
        for kind in ("collect", "reconcile"):
            with self.subTest(kind=kind):
                first, second = self.hashes[:2]
                table = self.table
                failed = threading.Event()
                requested = []

                class Failing(_TraceTransactionTransport):
                    def request(self, payload, label):
                        tx_hash = json.loads(payload)["params"][0]
                        requested.append(tx_hash)
                        if tx_hash == second:
                            failed.set()
                            raise usdc_interval.TransportError("fixture transport failed")
                        if tx_hash == first and not failed.wait(5):
                            raise AssertionError("failure request never overlapped")
                        return super().request(payload, label)

                owner = self.make_owner(kind, Failing(table), 2)
                with mock.patch.object(owner.staging, "record") as record:
                    with self.assertRaisesRegex(usdc_interval.TransportError, "fixture transport failed"):
                        self.fetch(owner)
                record.assert_not_called()
                self.assertCountEqual(requested, [first, second])

    def test_invalid_trace_concurrency_refuses(self):
        for kind in ("collect", "reconcile"):
            for invalid in (0, -1, 17, True, 1.5, "4"):
                with self.subTest(kind=kind, concurrency=invalid):
                    with self.assertRaisesRegex(AlexandriaError, "trace concurrency"):
                        self.make_owner(kind, _TraceTransactionTransport(self.table), invalid)

    def test_one_collectors_trace_cap_is_shared_across_shard_fetches(self):
        table = self.table

        class Paired(_TraceTransactionTransport):
            def __init__(self):
                super().__init__(table)
                self.barrier = threading.Barrier(2)
                self.lock = threading.Lock()
                self.active = self.peak = 0

            def request(self, payload, label):
                with self.lock:
                    self.active += 1
                    self.peak = max(self.peak, self.active)
                try:
                    self.barrier.wait(timeout=5)
                    return super().request(payload, label)
                finally:
                    with self.lock:
                        self.active -= 1

        transport = Paired()
        owner = self.make_owner("collect", transport, 2)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(owner._targeted_traces, shard, self.logs) for shard in (0, 1)]
            results = [future.result() for future in futures]
        self.assertEqual(transport.peak, 2)
        self.assertEqual(len(transport.calls), 2 * len(self.hashes))
        self.assertEqual(results[0][2], results[1][2])

    def test_cli_default_and_serial_fallback_are_available_to_both_commands(self):
        for command in ("collect", "reconcile"):
            arguments = [command, "--plan", "plan.json", "--staging", "staging"]
            if command == "reconcile":
                arguments += ["--provider-class", "fixture-second"]
            with self.subTest(command=command):
                self.assertEqual(usdc_interval.parser().parse_args(arguments).trace_concurrency, 4)
                self.assertEqual(usdc_interval.parser().parse_args(
                    arguments + ["--trace-concurrency", "1"]
                ).trace_concurrency, 1)


class OverallRpcConcurrencyTests(unittest.TestCase):
    def setUp(self):
        self.state = wildcat.fixture(wildcat.wildcat_v2.VENUE)
        self.plan, self.registry = self.state["plan"], wildcat.registry()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def transport(self):
        state = self.state

        class Observed(wildcat.WildcatTransport):
            def __init__(self):
                super().__init__(state)
                self.lock = threading.Lock()
                self.active = self.peak = self.opening_peak = 0
                self.logs_started = threading.Event()

            def request(self, payload, label):
                with self.lock:
                    self.active += 1
                    self.peak = max(self.peak, self.active)
                    if label.startswith("opening read"):
                        self.opening_peak = max(self.opening_peak, self.active)
                try:
                    time.sleep(0.003)
                    return super().request(payload, label)
                finally:
                    with self.lock:
                        self.active -= 1

        return Observed()

    def test_collection_preserves_bytes_and_coordinator_writes_under_one_rpc_cap(self):
        coordinator = threading.get_ident()
        trees = []
        for limit in (1, 4):
            root = self.root / str(limit)
            root.mkdir()
            transport = self.transport()
            collector = Collector(self.plan, root, transport, registry=self.registry,
                                  concurrency=limit, trace_concurrency=8, rpc_concurrency=limit)
            writers = []
            commit, record = collector.staging.commit, collector.staging.record
            def committed(*args):
                writers.append(threading.get_ident())
                return commit(*args)
            def recorded(*args):
                writers.append(threading.get_ident())
                return record(*args)
            collector.staging.commit, collector.staging.record = committed, recorded
            collector.collect()
            self.assertEqual(set(writers), {coordinator})
            self.assertLessEqual(transport.peak, limit)
            if limit > 1:
                self.assertGreater(transport.peak, 1)
                self.assertGreater(transport.opening_peak, 1)
            trees.append({str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()})
        self.assertEqual(trees[0], trees[1])

    def test_reconciliation_preserves_results_checkpoint_order_and_global_limit(self):
        collected = self.root / "collected"
        collected.mkdir()
        Collector(self.plan, collected, wildcat.WildcatTransport(self.state), registry=self.registry).collect()
        results = []
        coordinator = threading.get_ident()
        for limit in (1, 4):
            root = self.root / str(limit)
            shutil.copytree(collected, root)
            transport = self.transport()
            reconciler = Reconciler(self.plan, root, transport, "second", registry=self.registry,
                                    concurrency=limit, trace_concurrency=8, rpc_concurrency=limit)
            checkpoints = []
            save = reconciler._save_reconcile_checkpoint
            def saved(*args):
                checkpoints.append((threading.get_ident(), args[4]))
                return save(*args)
            reconciler._save_reconcile_checkpoint = saved
            document = reconciler.reconcile()
            results.append((document, reconciler._checkpoint_path().read_bytes()))
            self.assertEqual(checkpoints, [(coordinator, n) for n in range(1, len(self.plan["shards"]) + 1)])
            self.assertLessEqual(transport.peak, limit)
            if limit > 1:
                self.assertGreater(transport.peak, 1)
                self.assertGreater(transport.opening_peak, 1)
        self.assertEqual(results[0], results[1])

    def test_reconciliation_starts_the_next_shard_while_the_lowest_is_outstanding(self):
        collected = self.root / "collected"
        collected.mkdir()
        Collector(self.plan, collected, wildcat.WildcatTransport(self.state), registry=self.registry).collect()
        serial = self.root / "serial"
        shutil.copytree(collected, serial)
        expected = Reconciler(self.plan, serial, wildcat.WildcatTransport(self.state), "second",
                              registry=self.registry, concurrency=1).reconcile()
        state = self.state

        class SlowShardZero(wildcat.WildcatTransport):
            def __init__(self):
                super().__init__(state)
                self.lock = threading.Lock()
                self.held = False
                self.shard_two_started = threading.Event()

            def request(self, payload, label):
                if label.startswith("shard 2 "):
                    self.shard_two_started.set()
                with self.lock:
                    hold = label.startswith("shard 0 ") and not self.held
                    self.held = self.held or hold
                # Neither a batch loop nor a window that refills only when the
                # lowest result is taken starts shard 2 while shard 0 is slow.
                if hold and not self.shard_two_started.wait(5):
                    raise AssertionError("reconcile did not start shard 2 while shard 0 was slow")
                return super().request(payload, label)

        root = self.root / "windowed"
        shutil.copytree(collected, root)
        transport = SlowShardZero()
        actual = Reconciler(self.plan, root, transport, "second", registry=self.registry,
                            concurrency=2).reconcile()
        self.assertTrue(transport.held)
        self.assertEqual(actual, expected)

    def test_read_window_holds_at_most_twice_its_limit_behind_a_slow_first_read(self):
        lock = threading.Lock()
        started, active, peak = [], [0], [0]
        release, four_started = threading.Event(), threading.Event()
        seen = []

        def read(item):
            with lock:
                started.append(item)
                active[0] += 1
                peak[0] = max(peak[0], active[0])
                if len(started) == 4:
                    four_started.set()
            try:
                if item == 0 and not release.wait(5):
                    raise AssertionError("the first read was never released")
                return item * 10
            finally:
                with lock:
                    active[0] -= 1

        def observe():
            if four_started.wait(5):
                time.sleep(0.2)
            with lock:
                seen.extend(started)
            release.set()

        observer = threading.Thread(target=observe)
        observer.start()
        results = [(item, outcome.result()) for item, outcome in usdc_interval._read_batches(range(10), read, 2)]
        observer.join()
        self.assertEqual(sorted(seen), [0, 1, 2, 3])
        self.assertEqual(results, [(item, item * 10) for item in range(10)])
        self.assertEqual(peak[0], 2)

    def test_prefetched_failure_writes_only_on_coordinator_and_resumes_prefix(self):
        root = self.root / "failure"
        root.mkdir()
        Collector(self.plan, root, wildcat.WildcatTransport(self.state), registry=self.registry).collect()
        reconciler = Reconciler(self.plan, root, _FailOnceAtShard(self.state, fail_shard=1),
                                "second", registry=self.registry, concurrency=4, rpc_concurrency=4)
        writers = []
        record = reconciler._record_error
        def recorded(*args):
            writers.append(threading.get_ident())
            return record(*args)
        reconciler._record_error = recorded
        self.assertEqual(reconciler.reconcile()["reconciliation"]["status"], "unreconciled")
        self.assertEqual(writers, [threading.get_ident()])
        self.assertEqual(json.loads(reconciler._checkpoint_path().read_bytes())["next_shard"], 1)
        resumed = Reconciler(self.plan, root, wildcat.WildcatTransport(self.state), "second",
                             registry=self.registry, concurrency=4, rpc_concurrency=4).reconcile()
        self.assertEqual(resumed["reconciliation"]["status"], "agreed")
        self.assertEqual(resumed["reconciliation"]["compared"], resumed["reconciliation"]["matched"])

    def test_rpc_bounds_refuse_before_requests(self):
        for value in (0, 9, True, 2.5):
            with self.subTest(value=value):
                with self.assertRaisesRegex(AlexandriaError, "RPC concurrency"):
                    Collector(self.plan, self.root, self.transport(), registry=self.registry, rpc_concurrency=value)
                with self.assertRaisesRegex(AlexandriaError, "RPC concurrency"):
                    Reconciler(self.plan, self.root, self.transport(), "second", registry=self.registry, rpc_concurrency=value)

    def test_collection_worker_refusal_defers_error_file_to_coordinator(self):
        root = self.root / "collector-failure"
        root.mkdir()
        collector = Collector(self.plan, root, _FailOnceAtShard(self.state, fail_shard=1),
                              registry=self.registry, concurrency=4, rpc_concurrency=4)
        writers = []
        original = usdc_interval.os.open
        def observed(path, *args, **kwargs):
            if Path(path).name == "errors.jsonl":
                writers.append(threading.get_ident())
            return original(path, *args, **kwargs)
        with mock.patch.object(usdc_interval.os, "open", side_effect=observed):
            with self.assertRaises(usdc_interval.TransportError):
                collector.collect()
        self.assertEqual(writers, [threading.get_ident()])
        self.assertEqual(json.loads((root / "checkpoint.json").read_bytes())["next_shard"], 1)
        self.assertEqual(collector.staging._handles, {})

    def test_deferred_error_receipt_failure_closes_journals_and_preserves_prefix(self):
        root = self.root / "receipt-failure"
        root.mkdir()
        collector = Collector(self.plan, root, _FailOnceAtShard(self.state, fail_shard=1),
                              registry=self.registry, concurrency=4, rpc_concurrency=4)
        self.addCleanup(collector.staging.close)
        handles = []
        record = collector.staging.record
        def recorded(*args):
            result = record(*args)
            handles.extend(collector.staging._handles.values())
            return result
        collector.staging.record = recorded
        original = usdc_interval.os.open
        def refuse_receipt(path, *args, **kwargs):
            if Path(path).name == "errors.jsonl":
                raise PermissionError("injected receipt write refusal")
            return original(path, *args, **kwargs)
        with mock.patch.object(usdc_interval.os, "open", side_effect=refuse_receipt):
            with self.assertRaisesRegex(AlexandriaError, "cannot open the error receipt file"):
                collector.collect()
        self.assertEqual(json.loads((root / "checkpoint.json").read_bytes())["next_shard"], 1)
        self.assertTrue(handles)
        self.assertTrue(all(handle.closed for handle in handles))
        self.assertEqual(collector.staging._handles, {})

    def test_timed_out_http_worker_keeps_its_global_slot_until_it_finishes(self):
        release = threading.Event()
        entered = threading.Event()
        finished = threading.Event()
        slots = threading.BoundedSemaphore(1)
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.read.return_value = b"{}"
        opener = mock.Mock()
        def open_request(*args, **kwargs):
            entered.set()
            try:
                release.wait(5)
                return response
            finally:
                finished.set()
        opener.open.side_effect = open_request
        workers = usdc_interval._RequestWorkers(2)
        try:
            with mock.patch.object(usdc_interval, "MAX_REQUEST_SECONDS", 0.02):
                with self.assertRaises(usdc_interval.TransportError):
                    usdc_interval._bounded_request(opener, mock.Mock(), 1, "first", workers=workers, slots=slots)
                self.assertTrue(entered.is_set())
                self.assertFalse(slots.acquire(blocking=False))
                with self.assertRaises(usdc_interval.TransportError):
                    usdc_interval._bounded_request(opener, mock.Mock(), 1, "second", workers=workers, slots=slots)
                self.assertEqual(opener.open.call_count, 1)
        finally:
            release.set()
            self.assertTrue(finished.wait(5))


class TargetedTracesSynthesisTests(unittest.TestCase):
    """`Collector._targeted_traces`: one combined record, built from real per-tx calls.

    Uses the Wildcat V2 fixture's plan and registry only to get a valid
    multi-subject `Collector` to call the method on; the transport and the
    shard's `logs` result are this test's own, so the per-transaction
    filtering is exercised directly rather than through the fixture's
    already-filtered `traces` state.
    """

    def setUp(self):
        self.state = wildcat.fixture(wildcat.wildcat_v2.VENUE)
        self.plan = self.state["plan"]
        self.registry = wildcat.registry()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def collector(self, transport):
        return Collector(self.plan, self.root, transport, registry=self.registry)

    def test_synthesizes_one_combined_record_and_drops_a_non_matching_frame(self):
        subjects = list(self.plan["subjects"])
        matching_to = subjects[0]
        other_address = "0x" + "77" * 20
        self.assertNotIn(other_address, {address.lower() for address in subjects})
        tx_a = "0x" + "aa" * 32
        tx_b = "0x" + "bb" * 32
        table = {
            tx_a: [
                {
                    "type": "call", "traceAddress": [0], "transactionHash": tx_a,
                    "action": {"to": matching_to, "from": "0x" + "01" * 20},
                },
                {
                    "type": "call", "traceAddress": [0, 0], "transactionHash": tx_a,
                    "action": {"to": other_address, "from": "0x" + "01" * 20},
                },
            ],
            tx_b: [
                {
                    "type": "call", "traceAddress": [0], "transactionHash": tx_b,
                    "action": {"to": matching_to, "from": "0x" + "02" * 20},
                },
            ],
        }
        transport = _TraceTransactionTransport(table)
        logs_result = [
            {"transactionHash": tx_a, "blockNumber": "0x1", "transactionIndex": "0x0"},
            {"transactionHash": tx_b, "blockNumber": "0x2", "transactionIndex": "0x0"},
        ]
        collector = self.collector(transport)
        payload, response, combined = collector._targeted_traces(0, logs_result)

        # Each hash is requested exactly once; results retain derivation order.
        self.assertCountEqual([params[0] for _method, params, _label in transport.calls], [tx_a, tx_b])
        self.assertTrue(all(method == "trace_transaction" for method, _p, _l in transport.calls))

        # The non-matching frame (to `other_address`) was dropped.
        self.assertEqual(len(combined), 2)
        self.assertTrue(all(frame["action"]["to"] == matching_to for frame in combined))
        self.assertEqual(combined, [table[tx_a][0], table[tx_b][0]])

        # The request honestly names what was actually done -- trace_transaction
        # over the hashes actually derived, never a trace_filter call that never happened.
        request = json.loads(payload)
        self.assertEqual(request["method"], "trace_transaction")
        self.assertEqual(request["params"], [tx_a, tx_b])

        # The response is a self-consistent JSON-RPC envelope naming the combined result.
        envelope = json.loads(response)
        self.assertEqual(envelope["jsonrpc"], "2.0")
        self.assertEqual(envelope["id"], request["id"])
        self.assertEqual(envelope["result"], combined)

    def test_an_empty_shard_still_produces_one_valid_empty_record(self):
        collector = self.collector(_TraceTransactionTransport({}))
        payload, response, combined = collector._targeted_traces(0, [])
        self.assertEqual(combined, [])
        self.assertEqual(json.loads(payload)["params"], [])
        self.assertEqual(json.loads(response)["result"], [])

    def test_refuses_when_logs_was_not_read_first_this_shard(self):
        collector = self.collector(_TraceTransactionTransport({}))
        with self.assertRaisesRegex(AlexandriaError, "logs result"):
            collector._targeted_traces(0, None)

    def test_targeted_traces_itself_never_touches_staging(self):
        """The method that gathers a shard's traces must not be the one that records them."""
        tx_a = "0x" + "aa" * 32
        subjects = list(self.plan["subjects"])
        table = {
            tx_a: [{
                "type": "call", "traceAddress": [0], "transactionHash": tx_a,
                "action": {"to": subjects[0], "from": "0x" + "01" * 20},
            }],
        }
        collector = self.collector(_TraceTransactionTransport(table))
        record_calls = []
        collector.staging.record = lambda *a, **k: record_calls.append((a, k))
        collector._targeted_traces(0, [{"transactionHash": tx_a, "blockNumber": "0x1", "transactionIndex": "0x0"}])
        self.assertEqual(record_calls, [])


class ExactlyOnceTracesRecordTests(unittest.TestCase):
    """`Staging.record(shard, "traces", ...)` fires once per shard.

    `Reconciler._staged()` keys its dict by `(shard, class)` and silently
    keeps only the last entry for a repeated key, so a second `record("traces")`
    call for the same shard would drop evidence with no error anywhere. This
    drives a real `collect()` end to end and inspects every call the
    collector actually made to `Staging.record`.
    """

    def test_a_full_collection_records_traces_exactly_once_per_shard(self):
        state = wildcat.fixture(wildcat.wildcat_v2.VENUE)
        plan = state["plan"]
        reg = wildcat.registry()
        with tempfile.TemporaryDirectory() as root:
            transport = wildcat.WildcatTransport(state)
            collector = Collector(plan, root, transport, registry=reg)
            record_calls = []
            original_record = collector.staging.record

            def spy(shard, name, request, response):
                record_calls.append((shard, name))
                return original_record(shard, name, request, response)

            collector.staging.record = spy
            collector.collect()

        traces_shards = [shard for shard, name in record_calls if name == "traces"]
        self.assertEqual(
            len(traces_shards), len(set(traces_shards)),
            "Staging.record('traces') fired more than once for some shard",
        )
        self.assertEqual(sorted(traces_shards), list(range(len(plan["shards"]))))


class _DelayedTransport(existing.FixtureTransport):
    """Delays any request whose label starts with a given prefix; everything else is instant."""

    def __init__(self, state, *, delays=None, **kwargs):
        super().__init__(state, **kwargs)
        self.delays = delays or {}

    def request(self, payload, label):
        for prefix, seconds in self.delays.items():
            if label.startswith(prefix):
                time.sleep(seconds)
        return super().request(payload, label)


class ConcurrentCollectionTests(existing.CollectorTestCase):
    """`Collector(..., concurrency=N)`: fetches may overlap, commits never do.

    Uses the plain Compound single-proxy fixture (5 shards): concurrency is a
    property of `_collect_shards`/`_fetch_shard`, independent of whether a
    shard's `traces` class goes through the targeted-trace path or the
    untouched blanket `trace_filter` path.
    """

    def test_concurrency_one_is_the_default_and_matches_the_original_sequential_run(self):
        implicit_root = self.scratch("implicit")
        explicit_root = self.scratch("explicit")
        Collector(self.plan, implicit_root, existing.FixtureTransport(self.state)).collect()
        Collector(
            self.plan, explicit_root, existing.FixtureTransport(self.state), concurrency=1,
        ).collect()
        self.assertEqual(
            existing.journal_files(implicit_root), existing.journal_files(explicit_root)
        )

    def test_an_out_of_bounds_concurrency_refuses(self):
        for bad in (0, -1, 9, "4", 4.0, True):
            with self.subTest(concurrency=bad):
                with self.assertRaisesRegex(AlexandriaError, "concurrency"):
                    Collector(self.plan, self.root, existing.FixtureTransport(self.state), concurrency=bad)

    def test_commits_land_ascending_even_when_an_early_shard_fetches_slowest(self):
        root = self.scratch("concurrent")
        # Shard 0's own requests are slowest, so a correct pool fetches 1-4
        # before 0 finishes -- yet 0 must still be the first one committed.
        transport = _DelayedTransport(self.state, delays={"shard 0": 0.25})
        collector = Collector(self.plan, root, transport, concurrency=4)

        fetch_order = []
        real_fetch = collector._fetch_shard

        def spy_fetch(index):
            result = real_fetch(index)
            fetch_order.append(index)
            return result

        collector._fetch_shard = spy_fetch

        commit_order = []
        real_commit = collector.staging.commit

        def spy_commit(shard, block_number, block_hash):
            commit_order.append(shard)
            return real_commit(shard, block_number, block_hash)

        collector.staging.commit = spy_commit

        collector.collect()

        # The opening phase commits again under the last shard's index once per
        # opening read (see `Staging.commit`'s own docstring), so `commit_order`
        # is `[0, 1, 2, 3, 4, 4, 4, ...]`, not a single pass over every index.
        # It must never go backwards, and the first time each shard index
        # appears must be in ascending order.
        self.assertEqual(commit_order, sorted(commit_order))
        first_seen = list(dict.fromkeys(commit_order))
        self.assertEqual(first_seen, list(range(len(self.plan["shards"]))))
        # Real concurrency happened: the delayed shard did not finish fetching first.
        self.assertNotEqual(fetch_order[0], 0)
        self.assertNotEqual(fetch_order, sorted(fetch_order))

        expected = self.scratch("sequential")
        Collector(self.plan, expected, existing.FixtureTransport(self.state)).collect()
        self.assertEqual(existing.journal_files(root), existing.journal_files(expected))

    def test_a_kill_mid_flight_leaves_a_contiguous_prefix_and_resumes_byte_identically(self):
        root = self.scratch("interrupted")
        transport = existing.KillingTransport(self.state, kill_at="shard 3 logs")
        collector = Collector(self.plan, root, transport, concurrency=4)

        with self.assertRaises(existing._Killed):
            collector.collect()

        state = existing.checkpoint(root)
        # A contiguous committed prefix: shards 0-2 landed, in order, and
        # nothing beyond the killed shard did, whatever order fetches arrived in.
        self.assertEqual(state["next_shard"], 3)

        summary = Collector(
            self.plan, root, existing.FixtureTransport(self.state), concurrency=4,
        ).collect()
        self.assertEqual(summary["resumed_from"], 3)

        expected = self.scratch("sequential")
        Collector(self.plan, expected, existing.FixtureTransport(self.state)).collect()
        self.assertEqual(existing.journal_files(root), existing.journal_files(expected))

    def test_a_slow_lowest_shard_does_not_idle_the_rest_of_the_window(self):
        root = self.scratch("windowed")
        state = self.state

        class SlowShardZero(existing.FixtureTransport):
            def __init__(self):
                super().__init__(state)
                self.lock = threading.Lock()
                self.held = False
                self.shard_two_started = threading.Event()

            def request(self, payload, label):
                if label.startswith("shard 2 "):
                    self.shard_two_started.set()
                with self.lock:
                    hold = label.startswith("shard 0 ") and not self.held
                    self.held = self.held or hold
                # A window capped by fetched and in-flight shards together
                # never starts shard 2 at concurrency 2 while shard 0 is slow.
                if hold and not self.shard_two_started.wait(5):
                    raise AssertionError("collect did not start shard 2 while shard 0 was slow")
                return super().request(payload, label)

        transport = SlowShardZero()
        Collector(self.plan, root, transport, concurrency=2).collect()
        self.assertTrue(transport.held)
        expected = self.scratch("sequential")
        Collector(self.plan, expected, existing.FixtureTransport(self.state)).collect()
        self.assertEqual(existing.journal_files(root), existing.journal_files(expected))

    def test_the_window_holds_at_most_twice_its_concurrency_behind_a_slow_lowest_shard(self):
        root = self.scratch("bounded")
        lock = threading.Lock()
        started, seen = [], []
        release, four_started = threading.Event(), threading.Event()
        collector = Collector(self.plan, root, existing.FixtureTransport(self.state), concurrency=2)
        real_fetch = collector._fetch_shard

        def spy_fetch(index):
            with lock:
                started.append(index)
                if len(started) == 4:
                    four_started.set()
            if index == 0 and not release.wait(10):
                raise AssertionError("shard 0 was never released")
            return real_fetch(index)

        def observe():
            if four_started.wait(5):
                time.sleep(0.2)
            with lock:
                seen.extend(started)
            release.set()

        collector._fetch_shard = spy_fetch
        observer = threading.Thread(target=observe)
        observer.start()
        collector.collect()
        observer.join()
        self.assertEqual(sorted(seen), [0, 1, 2, 3])
        self.assertEqual(sorted(started), list(range(len(self.plan["shards"]))))

    def test_a_failed_fetch_stops_refill_and_commits_every_shard_below_it(self):
        root = self.scratch("failed")
        transport = existing.KillingTransport(self.state, kill_at="shard 1 logs")
        collector = Collector(self.plan, root, transport, concurrency=2)
        started = []
        real_fetch = collector._fetch_shard

        def spy_fetch(index):
            started.append(index)
            if index == 0:
                time.sleep(0.25)
            return real_fetch(index)

        collector._fetch_shard = spy_fetch
        with self.assertRaises(existing._Killed):
            collector.collect()
        self.assertEqual(existing.checkpoint(root)["next_shard"], 1)
        # Shard 1 fails while shard 0 is still fetching, so nothing past the
        # two shards already running is started.
        self.assertEqual(sorted(started), [0, 1])

    def test_a_higher_concurrency_still_matches_sequential_output(self):
        for concurrency in (2, 4, 8):
            with self.subTest(concurrency=concurrency):
                root = self.scratch(f"pooled-{concurrency}")
                Collector(
                    self.plan, root, existing.FixtureTransport(self.state), concurrency=concurrency,
                ).collect()
                expected = self.scratch(f"sequential-{concurrency}")
                Collector(self.plan, expected, existing.FixtureTransport(self.state)).collect()
                self.assertEqual(existing.journal_files(root), existing.journal_files(expected))


class _BeforeFirstShard(Exception):
    pass


class ByteCeilingDrainTests(existing.CollectorTestCase):
    """Past the byte ceiling no new shard starts, and every started shard commits."""

    def _ceiling_crossed_by_the_first_shard_read(self):
        collector = Collector(self.plan, self.scratch("probe"), existing.FixtureTransport(self.state))
        spent = []

        def stop(*_args):
            spent.append(collector._bytes)
            raise _BeforeFirstShard()

        collector._collect_sequential = stop
        with self.assertRaises(_BeforeFirstShard):
            collector.collect()
        return spent[0] + 1

    def _assert_resumes_to_the_sequential_journals(self, root, concurrency):
        Collector(self.plan, root, existing.FixtureTransport(self.state), concurrency=concurrency).collect()
        expected = self.scratch(f"sequential-{concurrency}")
        Collector(self.plan, expected, existing.FixtureTransport(self.state)).collect()
        self.assertEqual(existing.journal_files(root), existing.journal_files(expected))

    def test_a_pooled_run_past_its_byte_ceiling_commits_every_shard_it_started(self):
        ceiling = self._ceiling_crossed_by_the_first_shard_read()
        root = self.scratch("pooled")
        collector = Collector(self.plan, root, existing.FixtureTransport(self.state), concurrency=2)
        started = []
        real_fetch = collector._fetch_shard

        def spy_fetch(index):
            started.append(index)
            return real_fetch(index)

        collector._fetch_shard = spy_fetch
        with mock.patch.object(usdc_interval, "MAX_COLLECT_BYTES", ceiling):
            with self.assertRaisesRegex(AlexandriaError, "^collection exceeded its total byte ceiling$"):
                collector.collect()
        committed = existing.checkpoint(root)["next_shard"]
        self.assertTrue(started)
        self.assertEqual(sorted(started), list(range(committed)))
        self.assertLess(committed, len(self.plan["shards"]))
        self._assert_resumes_to_the_sequential_journals(root, 2)

    def test_a_sequential_run_past_its_byte_ceiling_finishes_the_shard_it_started(self):
        ceiling = self._ceiling_crossed_by_the_first_shard_read()
        root = self.scratch("sequential")
        with mock.patch.object(usdc_interval, "MAX_COLLECT_BYTES", ceiling):
            with self.assertRaisesRegex(AlexandriaError, "^collection exceeded its total byte ceiling$"):
                Collector(self.plan, root, existing.FixtureTransport(self.state)).collect()
        self.assertEqual(existing.checkpoint(root)["next_shard"], 1)
        self._assert_resumes_to_the_sequential_journals(root, 1)

    def test_finishing_started_shards_stops_at_the_hard_ceiling(self):
        ceiling = self._ceiling_crossed_by_the_first_shard_read()
        root = self.scratch("hard")
        with mock.patch.object(usdc_interval, "MAX_COLLECT_BYTES", ceiling), \
                mock.patch.object(usdc_interval, "MAX_COLLECT_DRAIN_BYTES", ceiling):
            with self.assertRaisesRegex(AlexandriaError, "hard byte ceiling while finishing started shards"):
                Collector(self.plan, root, existing.FixtureTransport(self.state), concurrency=2).collect()
        self.assertFalse((root / "checkpoint.json").exists())
        self._assert_resumes_to_the_sequential_journals(root, 2)


class ReconciliationTracesComparisonTests(unittest.TestCase):
    """Reconciliation's own, independent second-transport targeted-trace derivation."""

    def setUp(self):
        self.state = wildcat.fixture(wildcat.wildcat_v2.VENUE)
        self.plan = self.state["plan"]
        self.registry = wildcat.registry()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def collect(self):
        transport = wildcat.WildcatTransport(self.state)
        Collector(self.plan, self.root, transport, registry=self.registry).collect()

    def test_a_second_provider_that_agrees_counts_the_trace_comparisons(self):
        self.collect()
        second = wildcat.WildcatTransport(self.state)
        document = Reconciler(
            self.plan, self.root, second, "agreeing provider", registry=self.registry,
        ).reconcile()
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        self.assertEqual(document["reconciliation"]["disputed"], [])

    def test_a_second_provider_that_returns_a_different_frame_is_a_trace_identity_dispute(self):
        self.collect()

        class DisagreeingTransport(wildcat.WildcatTransport):
            def trace_transaction(self, tx_hash):
                frames = super().trace_transaction(tx_hash)
                if not frames:
                    return frames
                frames = deepcopy(frames)
                frames[0]["traceAddress"] = list(frames[0].get("traceAddress", [])) + [99]
                return frames

        second = DisagreeingTransport(self.state)
        document = Reconciler(
            self.plan, self.root, second, "disagreeing provider", registry=self.registry,
        ).reconcile()
        kinds = {entry["kind"] for entry in document["reconciliation"]["disputed"]}
        self.assertIn("trace-identity", kinds)
        self.assertEqual(document["reconciliation"]["status"], "disputed")

    def test_a_second_provider_whose_trace_transaction_fails_leaves_the_interval_unreconciled(self):
        self.collect()

        class FailingTransport(wildcat.WildcatTransport):
            def trace_transaction(self, tx_hash):
                raise usdc_interval.TransportError("second-provider trace_transaction refused")

        second = FailingTransport(self.state)
        document = Reconciler(
            self.plan, self.root, second, "failing provider", registry=self.registry,
        ).reconcile()
        self.assertEqual(document["reconciliation"]["status"], "unreconciled")

    def test_changed_trace_content_with_the_same_identity_is_disputed(self):
        self.collect()

        class ChangedValueTransport(wildcat.WildcatTransport):
            def trace_transaction(self, tx_hash):
                frames = deepcopy(super().trace_transaction(tx_hash))
                if frames:
                    frames[0]["action"]["value"] = "0xfeed"
                return frames

        document = Reconciler(
            self.plan, self.root, ChangedValueTransport(self.state),
            "changed value provider", registry=self.registry,
        ).reconcile()
        self.assertEqual(document["reconciliation"]["status"], "disputed")
        self.assertIn("trace-identity", {
            entry["kind"] for entry in document["reconciliation"]["disputed"]
        })

    def test_trace_comparison_includes_each_preserved_field(self):
        frame = {
            "transactionHash": "0x" + "aa" * 32, "traceAddress": [0],
            "type": "call", "action": {"to": "0x" + "11" * 20, "value": "0x1"},
            "result": {"output": "0x", "gasUsed": "0x1"},
            "blockHash": "0x" + "bb" * 32, "blockNumber": 100,
            "transactionPosition": 0, "subtraces": 0,
        }
        for field, value in (
            ("action", dict(frame["action"], value="0x2")),
            ("result", {"output": "0xab", "gasUsed": "0x1"}),
            ("error", "Reverted"), ("blockHash", "0x" + "cc" * 32),
            ("blockNumber", 101), ("transactionPosition", 1), ("subtraces", 1),
        ):
            with self.subTest(field=field):
                self.assertNotEqual(
                    usdc_interval.trace_identity(frame),
                    usdc_interval.trace_identity(dict(frame, **{field: value})),
                )

    def test_the_single_proxy_path_never_reaches_a_traces_comparison(self):
        """The Compound path is untouched: reconcile() never asks it for trace_transaction."""
        compound_state = existing.fixture()
        compound_plan = compound_state["plan"]
        root = tempfile.TemporaryDirectory()
        self.addCleanup(root.cleanup)
        Collector(
            compound_plan, root.name, existing.FixtureTransport(compound_state),
        ).collect()
        second = existing.RecordingTransport(compound_state)
        Reconciler(compound_plan, root.name, second, "second provider").reconcile()
        self.assertNotIn(
            "trace_transaction", {method for method, _label in second.calls}
        )


class TargetedTraceCoverageTests(wildcat.WildcatCase):
    def test_release_names_transactions_the_log_filter_does_not_reach(self):
        output, _release_id = self.released()
        self.assertIn(
            usdc_interval.TARGETED_TRACE_GAP, self.captures(output)["traces"]["coverage"]["gaps"]
        )
        self.assertEqual(usdc_interval.check_interval(output)["epochs"], 137)

    def test_check_refuses_a_release_that_drops_the_targeted_gap(self):
        output, _release_id = self.released()
        path = output / "manifest.json"
        manifest = json.loads(path.read_text())
        next(row for row in manifest["captures"] if row["id"] == "traces")["coverage"]["gaps"].remove(
            usdc_interval.TARGETED_TRACE_GAP
        )
        path.write_bytes(usdc_interval.canonical_bytes(manifest))
        with self.assertRaisesRegex(AlexandriaError, "targeted trace gap"):
            self.check_without_verify(output)


class RealMainnetEquivalenceTests(unittest.TestCase):
    """Shard 0's real, already-committed ground truth: an offline equivalence proof.

    `fixtures/step9-shard0-ground-truth.json` holds real mainnet data captured
    2026-09-21 from the same local trace-enabled Reth archive node the actual
    (interrupted, one-shard) collection used: the shard's genuine `eth_getLogs`
    result, its genuine blanket `trace_filter` result (9 frames across 2
    transactions), the 137-address subject list, and the real, UNFILTERED
    `trace_transaction` answer the node gave for each of those two
    transactions (17 and 3 raw frames respectively -- so the filter has real
    work to do). This is the differential proof the Step 9 spec required
    before anything else was built, re-run here as a permanent, offline,
    no-socket regression test rather than a one-off manual check.
    """

    FIXTURE = Path(__file__).resolve().parent / "fixtures" / "step9-shard0-ground-truth.json"

    @classmethod
    def setUpClass(cls):
        if not cls.FIXTURE.is_file():
            raise AssertionError(
                f"the shard 0 ground-truth fixture is missing at {cls.FIXTURE}; this is real "
                "captured mainnet data checked into the repo, so its absence is a fixture bug, "
                "not something to skip past"
            )
        with open(cls.FIXTURE) as f:
            cls.data = json.load(f)

    def test_targeted_derivation_reproduces_the_real_blanket_trace_filter_result(self):
        subjects = frozenset(address.lower() for address in self.data["subjects"])
        hashes = usdc_interval.subject_transaction_hashes(self.data["logs_result"])
        self.assertEqual(
            hashes,
            [
                "0xdaf2e91a7d080510f36bf595d62bfcf891e5b52a84770e06943a56956e328e77",
                "0x1d876fd551c0c721e2e5268d13a67ab92c69103a169550cfcb45427a3401477f",
            ],
        )
        raw_by_hash = self.data["raw_trace_transaction_by_hash"]
        # The real node returned more frames per transaction than the old
        # blanket trace_filter call kept: the filter has real work to do here,
        # this is not a vacuous pass-through.
        self.assertEqual(len(raw_by_hash[hashes[0]]), 17)
        self.assertEqual(len(raw_by_hash[hashes[1]]), 3)

        combined = []
        for tx_hash in hashes:
            frames = raw_by_hash[tx_hash]
            combined.extend(
                frame for frame in frames if usdc_interval._matches_subjects(frame, subjects)
            )

        self.assertEqual(len(combined), 9)
        self.assertEqual(
            usdc_interval.canonical_bytes(combined),
            usdc_interval.canonical_bytes(self.data["ground_truth_traces"]),
        )

    def test_every_dropped_frame_genuinely_did_not_match_a_subject(self):
        """Cross-check, frame by frame: kept iff `_matches_subjects` says so, never by luck."""
        subjects = frozenset(address.lower() for address in self.data["subjects"])
        raw_by_hash = self.data["raw_trace_transaction_by_hash"]
        kept_identities = {
            usdc_interval.trace_identity(frame) for frame in self.data["ground_truth_traces"]
        }
        checked = 0
        for frames in raw_by_hash.values():
            for frame in frames:
                matches = usdc_interval._matches_subjects(frame, subjects)
                was_kept = usdc_interval.trace_identity(frame) in kept_identities
                self.assertEqual(matches, was_kept, frame)
                checked += 1
        self.assertEqual(checked, 20)  # 17 + 3 raw frames across both transactions


class _FailOnceAtShard(wildcat.WildcatTransport):
    """The Wildcat fixture transport, refusing the first request to a chosen shard once.

    Matches by label prefix (e.g. "shard 2 "), not a raw call count, so
    shards before it always finish in full -- the same style the real
    interrupted-and-resumed proof used against the live hosted endpoint.
    """

    def __init__(self, state, *, fail_shard, **kwargs):
        super().__init__(state, **kwargs)
        self.fail_shard = fail_shard
        self.triggered = False

    def request(self, payload, label):
        if not self.triggered and label.startswith(f"shard {self.fail_shard} "):
            self.triggered = True
            raise usdc_interval.TransportError(f"{label} injected failure for a test")
        return super().request(payload, label)


class ReconcileCheckpointTests(unittest.TestCase):
    """reconcile()'s own progress checkpoint, error receipts and heartbeat.

    A transport failure partway through used to cost every comparison made
    so far, with the real cause never recorded anywhere. This proves the
    fix offline, deterministically, on top of the real interrupted-and-
    resumed proof already run against the live hosted endpoint.
    """

    def setUp(self):
        self.state = wildcat.fixture(wildcat.wildcat_v2.VENUE)
        self.plan = self.state["plan"]
        self.registry = wildcat.registry()
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.collected = self.root / "collected"
        self.collected.mkdir()
        Collector(
            self.plan, self.collected, wildcat.WildcatTransport(self.state), registry=self.registry,
        ).collect()

    def _copy(self, name):
        dest = self.root / name
        shutil.copytree(self.collected, dest)
        return dest

    def test_a_transport_failure_checkpoints_progress_and_records_the_real_cause(self):
        staging = self._copy("checkpoint")
        second = _FailOnceAtShard(self.state, fail_shard=2)
        document = Reconciler(
            self.plan, staging, second, "second provider", registry=self.registry,
        ).reconcile()
        self.assertEqual(document["reconciliation"]["status"], "unreconciled")

        checkpoint = json.loads((staging / "reconciliation" / "checkpoint.json").read_text())
        self.assertEqual(checkpoint["next_shard"], 2)
        self.assertEqual(checkpoint["plan_sha256"], usdc_interval.plan_digest(self.plan))
        self.assertEqual(checkpoint["provider_class"], "second provider")
        self.assertEqual(checkpoint["format"], usdc_interval.RECONCILE_CHECKPOINT_FORMAT)
        committed = json.loads((staging / "checkpoint.json").read_text())
        self.assertEqual(
            checkpoint["staging_last_accepted"], committed["last_accepted"]["block_hash"]
        )

        errors = [
            json.loads(line)
            for line in (staging / "reconciliation" / "errors.jsonl").read_text().splitlines()
            if line
        ]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["exception"], "TransportError")
        self.assertEqual(errors[0]["shard"], 2)
        self.assertIn("shard 2", errors[0]["message"])
        # Bounded, and never carries a scheme or a host -- see _close_transport_error.
        self.assertLessEqual(len(errors[0]["message"]), 200)
        self.assertNotIn("://", errors[0]["message"])

    def test_resuming_after_a_checkpointed_failure_matches_an_uninterrupted_run(self):
        baseline_staging = self._copy("baseline")
        baseline = Reconciler(
            self.plan, baseline_staging, wildcat.WildcatTransport(self.state), "second provider",
            registry=self.registry,
        ).reconcile()

        resumed_staging = self._copy("resumed")
        Reconciler(
            self.plan, resumed_staging, _FailOnceAtShard(self.state, fail_shard=2),
            "second provider", registry=self.registry,
        ).reconcile()

        calls = []

        class Counting(wildcat.WildcatTransport):
            def request(self, payload, label):
                calls.append(label)
                return super().request(payload, label)

        resumed = Reconciler(
            self.plan, resumed_staging, Counting(self.state), "second provider",
            registry=self.registry,
        ).reconcile()

        self.assertFalse(
            any(label.startswith("shard 0 ") or label.startswith("shard 1 ") for label in calls),
            "resume re-asked an already-checkpointed shard",
        )
        self.assertTrue(any(label.startswith("shard 2 ") for label in calls))
        self.assertEqual(resumed["reconciliation"], baseline["reconciliation"])
        self.assertEqual(resumed["shards"], baseline["shards"])

    def test_a_checkpoint_for_a_different_second_provider_is_not_trusted(self):
        staging = self._copy("provider-mismatch")
        Reconciler(
            self.plan, staging, _FailOnceAtShard(self.state, fail_shard=2),
            "provider A", registry=self.registry,
        ).reconcile()
        # Under a different provider_class, the checkpoint above proves
        # nothing about THIS comparison: it must start over at shard 0, not
        # skip ahead on the strength of a different second opinion's work.
        calls = []

        class Counting(wildcat.WildcatTransport):
            def request(self, payload, label):
                calls.append(label)
                return super().request(payload, label)

        document = Reconciler(
            self.plan, staging, Counting(self.state), "provider B", registry=self.registry,
        ).reconcile()
        self.assertTrue(any(label.startswith("shard 0 ") for label in calls))
        self.assertEqual(document["reconciliation"]["status"], "agreed")

    def _stale_checkpoint(self, name, mutate):
        """A checkpoint written at shard 2, then rewritten by `mutate` to look like another run's."""
        staging = self._copy(name)
        Reconciler(
            self.plan, staging, _FailOnceAtShard(self.state, fail_shard=2),
            "second provider", registry=self.registry,
        ).reconcile()
        path = staging / "reconciliation" / "checkpoint.json"
        stale = json.loads(path.read_text())
        self.assertEqual(stale["next_shard"], 2)
        mutate(stale)
        path.write_text(json.dumps(stale))
        return staging, path

    def _reconcile_counting(self, staging):
        calls = []

        class Counting(wildcat.WildcatTransport):
            def request(self, payload, label):
                calls.append(label)
                return super().request(payload, label)

        document = Reconciler(
            self.plan, staging, Counting(self.state), "second provider", registry=self.registry,
        ).reconcile()
        return document, calls

    def test_a_checkpoint_for_another_committed_boundary_is_not_trusted(self):
        """A tree rewound and collected again since the checkpoint was written is another tree.

        Its shards 0 and 1 were compared over bytes that may no longer be in
        the tree, so the checkpoint starts nothing and shard 0 is asked again;
        the checkpoint the run then writes names the tree's own boundary.
        """
        def other_boundary(stale):
            stale["staging_last_accepted"] = "0x" + "ab" * 32

        staging, path = self._stale_checkpoint("boundary-mismatch", other_boundary)
        document, calls = self._reconcile_counting(staging)
        self.assertTrue(any(label.startswith("shard 0 ") for label in calls))
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        rewritten = json.loads(path.read_text())
        committed = json.loads((staging / "checkpoint.json").read_text())
        self.assertEqual(
            rewritten["staging_last_accepted"], committed["last_accepted"]["block_hash"]
        )

    def test_a_checkpoint_in_the_earlier_format_is_not_trusted(self):
        """A v1 checkpoint carries no boundary, so it is treated as absent, never as a shape error."""
        def earlier_format(stale):
            stale["format"] = "alexandria-interval-reconcile-checkpoint/v1"
            del stale["staging_last_accepted"]

        staging, _path = self._stale_checkpoint("format-v1", earlier_format)
        document, calls = self._reconcile_counting(staging)
        self.assertTrue(any(label.startswith("shard 0 ") for label in calls))
        self.assertEqual(document["reconciliation"]["status"], "agreed")

    def test_changed_journal_bytes_at_the_same_boundary_restart_comparison(self):
        staging, _path = self._stale_checkpoint("changed-journal", lambda row: None)
        path = staging / "journals" / "traces.jsonl"
        before = path.read_bytes()
        after = before.replace(b'0x90323177', b'0x90323178', 1)
        self.assertNotEqual(before, after)
        self.assertEqual(len(before), len(after))
        path.write_bytes(after)
        _document, calls = self._reconcile_counting(staging)
        self.assertTrue(any(label.startswith("shard 0 ") for label in calls))

    def test_heartbeat_prints_one_flushed_line_per_shard_and_opening_read(self):
        staging = self._copy("heartbeat")
        stderr = io.StringIO()
        with mock.patch.object(sys, "stderr", stderr):
            Reconciler(
                self.plan, staging, wildcat.WildcatTransport(self.state), "second provider",
                registry=self.registry,
            ).reconcile()
        lines = stderr.getvalue().splitlines()
        shard_lines = [line for line in lines if line.startswith("[reconcile] shard ")]
        opening_lines = [line for line in lines if line.startswith("[reconcile] opening read ")]
        self.assertEqual(len(shard_lines), len(self.plan["shards"]))
        self.assertGreater(len(opening_lines), 0)
        self.assertIn("elapsed", shard_lines[0])
        self.assertIn(f"shard 1/{len(self.plan['shards'])} done", shard_lines[0])


if __name__ == "__main__":
    unittest.main()
