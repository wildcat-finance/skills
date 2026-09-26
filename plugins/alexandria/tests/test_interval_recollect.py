"""`recollect`: replace one shard's traces in a complete one-shard-per-component tree.

Every case runs the constructed Aave fixture under a plan that declares one
shard per component and journal-range attribution parts, as the production
segment plans do. The primary transport loses the trace frames of one
transaction in shard 1, the way a node in pipeline catch-up answered for
segment 6; the second transport answers correctly, so reconciliation disputes
those trace identities, and `recollect` repairs them through the collector's
own request path. No socket is opened.
"""

import hashlib
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib import interval  # noqa: E402
from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import (  # noqa: E402
    RECOLLECTION_RECORDS,
    REPLACEMENT_INTENT,
    Staging,
)
import usdc_interval  # noqa: E402
from usdc_interval import Builder, Collector, Reconciler, check_interval  # noqa: E402

from tests import test_aave_v3_collector as aave  # noqa: E402
from tests import test_usdc_interval as existing  # noqa: E402

# The one transaction shard 1's logs name; the primary answers no frame for it.
LOST = "0x5ba9d856"
SHARD = 1
# 2026-09-26T18:30:00Z, the time every recollection here is recorded at.
NOW = 1790447400


class LosingTraces(aave.AaveTransport):
    """A primary that answers no trace frame for the transactions in `lost`."""

    def __init__(self, state, *, lost=(LOST,), **kwargs):
        super().__init__(state, **kwargs)
        self.lost = tuple(lost)

    def trace_transaction(self, tx_hash):
        if tx_hash.startswith(self.lost):
            return []
        return super().trace_transaction(tx_hash)


class KillingOpening(aave.AaveTransport):
    """Stops the collection at its first opening read, after every shard committed."""

    def request(self, payload, label):
        if label.startswith("opening read 0 "):
            raise existing._Killed(label)
        return super().request(payload, label)


def split_state(state, per_component=1):
    state = dict(state)
    state["plan"] = dict(
        state["plan"], shards_per_component=per_component, log_attribution_parts="journal-ranges",
    )
    return state


def journal_bytes(staging):
    return {
        path.name: path.read_bytes()
        for path in sorted((Path(staging) / "journals").iterdir())
        if not path.name.startswith(".")
    }


def checkpoint(staging):
    return json.loads((Path(staging) / "checkpoint.json").read_bytes())


class RecollectCase(aave.AaveCase):
    def setUp(self):
        super().setUp()
        self.state = split_state(self.state)
        self.plan = self.state["plan"]

    def collected(self, name="tree", primary=None):
        staging = self.scratch(f"{name}-staging")
        Collector(self.plan, staging, primary or LosingTraces(self.state), registry=self.registry).collect()
        return staging

    def reconciled(self, staging):
        return Reconciler(
            self.plan, staging, aave.AaveTransport(self.state), aave.SECOND_PROVIDER,
            registry=self.registry,
        ).reconcile()

    def recollect(self, staging, shards=(SHARD,), transport=None):
        collector = Collector(
            self.plan, staging, transport or aave.AaveTransport(self.state), registry=self.registry,
        )
        return collector.recollect(list(shards), now=NOW)

    def disputed(self):
        staging = self.collected()
        document = self.reconciled(staging)
        self.assertEqual(document["reconciliation"]["status"], "disputed")
        self.assertEqual(
            {(item["kind"], item["shard"]) for item in document["reconciliation"]["disputed"]},
            {("trace-identity", SHARD)},
        )
        return staging


class RecollectReplacementTests(RecollectCase):
    def test_replaces_only_the_named_shards_traces_component(self):
        staging = self.disputed()
        before = journal_bytes(staging)
        summary = self.recollect(staging)
        after = journal_bytes(staging)
        changed = {name for name in before if before[name] != after[name]}
        self.assertEqual(changed, {f"traces.{SHARD}.jsonl"})
        self.assertEqual(set(before), set(after))
        (record,) = summary["recollected"]
        self.assertEqual(record["shard"], SHARD)
        self.assertEqual(record["old_sha256"], hashlib.sha256(before[f"traces.{SHARD}.jsonl"]).hexdigest())
        self.assertEqual(record["new_sha256"], hashlib.sha256(after[f"traces.{SHARD}.jsonl"]).hexdigest())
        # The replaced journal is what a clean collection would have staged.
        clean = self.collected("clean", aave.AaveTransport(self.state))
        self.assertEqual(after, journal_bytes(clean))
        self.assertEqual(self.reconciled(staging)["reconciliation"]["status"], "agreed")

    def test_moves_only_that_journals_offsets_in_the_checkpoint_and_history(self):
        staging = self.disputed()
        before = checkpoint(staging)
        self.recollect(staging)
        after = checkpoint(staging)
        name = f"traces.{SHARD}"
        size = (Path(staging) / "journals" / f"{name}.jsonl").stat().st_size
        self.assertNotEqual(before["offsets"][name], size)
        self.assertEqual(after["offsets"][name], size)
        self.assertEqual(after["records"], before["records"])
        expected = json.loads(json.dumps(before))
        expected["offsets"][name] = size
        for entry in expected["history"]:
            if entry["shard"] >= SHARD:
                entry["offsets"][name] = size
            else:
                self.assertEqual(entry["offsets"][name], 0)
        self.assertEqual(after, expected)
        # The tree resumes as it stands: nothing is truncated or re-collected.
        state = Staging(staging, self.plan).resume()
        self.assertEqual(state["next_shard"], len(self.plan["shards"]))
        self.assertEqual(journal_bytes(staging)[f"{name}.jsonl"].count(b"\n"), 1)

    def test_several_shards_are_replaced_in_one_invocation_through_the_cli(self):
        staging = self.scratch("cli-staging")
        Collector(
            self.plan, staging, LosingTraces(self.state, lost=(LOST, "0xc71737b3")),
            registry=self.registry,
        ).collect()
        plan_path, registry_path = self.files(self.plan)
        code, stdout, stderr = self.cli(
            "recollect", "--plan", plan_path, "--staging", staging, "--registry", registry_path,
            "--shard", "3", "--shard", str(SHARD), transport=aave.AaveTransport(self.state),
        )
        self.assertEqual(code, 0, stderr)
        summary = json.loads(stdout)
        self.assertEqual([record["shard"] for record in summary["recollected"]], [SHARD, 3])
        self.assertEqual(self.reconciled(staging)["reconciliation"]["status"], "agreed")

    def test_the_request_bytes_are_the_collectors_own(self):
        staging = self.disputed()
        transport = aave.AaveTransport(self.state)
        self.recollect(staging, transport=transport)
        labels = [label for _method, label in transport.calls]
        self.assertIn(f"shard {SHARD} boundary-blocks", labels)
        self.assertIn(f"shard {SHARD} logs", labels)
        self.assertTrue(any(label.startswith(f"shard {SHARD} traces 0x") for label in labels))
        self.assertFalse(any(label.startswith(("shard 0 ", "shard 2 ", "shard 3 ")) for label in labels))
        self.assertEqual(labels[0], f"shard {SHARD} sync-state")
        entry = json.loads(journal_bytes(staging)[f"traces.{SHARD}.jsonl"])
        clean = self.collected("clean", aave.AaveTransport(self.state))
        self.assertEqual(entry, json.loads(journal_bytes(clean)[f"traces.{SHARD}.jsonl"]))


class RecollectRefusalTests(RecollectCase):
    def assertUnchanged(self, staging, before):
        self.assertEqual(journal_bytes(staging), before)
        self.assertFalse((Path(staging) / "receipts" / RECOLLECTION_RECORDS).exists())
        self.assertFalse((Path(staging) / REPLACEMENT_INTENT).exists())

    def test_refuses_a_plan_with_more_than_one_shard_per_component(self):
        self.state = split_state(self.state, per_component=2)
        self.plan = self.state["plan"]
        staging = self.collected()
        before = journal_bytes(staging)
        with self.assertRaisesRegex(AlexandriaError, "must declare shards_per_component 1, not 2"):
            self.recollect(staging)
        self.assertUnchanged(staging, before)

    def test_refuses_a_collection_that_has_not_committed_every_shard(self):
        staging = self.scratch("partial-staging")
        with self.assertRaises(existing._Killed):
            Collector(
                self.plan, staging, aave.existing_killing(self.state, "shard 3 logs"),
                registry=self.registry,
            ).collect()
        before = journal_bytes(staging)
        with self.assertRaisesRegex(AlexandriaError, "not completely collected, so there is nothing to recollect"):
            self.recollect(staging)
        self.assertUnchanged(staging, before)

    def test_refuses_a_collection_whose_opening_reads_are_not_committed(self):
        staging = self.scratch("opening-staging")
        with self.assertRaises(existing._Killed):
            Collector(self.plan, staging, KillingOpening(self.state), registry=self.registry).collect()
        self.assertEqual(checkpoint(staging)["next_shard"], len(self.plan["shards"]))
        before = journal_bytes(staging)
        with self.assertRaisesRegex(AlexandriaError, "not completely collected, so there is nothing to recollect"):
            self.recollect(staging)
        self.assertUnchanged(staging, before)

    def test_refuses_an_index_outside_the_plan(self):
        staging = self.disputed()
        before = journal_bytes(staging)
        for index in (len(self.plan["shards"]), -1):
            with self.subTest(index=index):
                transport = aave.AaveTransport(self.state)
                with self.assertRaisesRegex(AlexandriaError, f"shard {index} is outside the plan's 4 shards"):
                    self.recollect(staging, shards=(SHARD, index), transport=transport)
                self.assertEqual(transport.calls, [])
        self.assertUnchanged(staging, before)

    def test_refuses_a_shard_whose_boundary_block_re_read_differs(self):
        staging = self.disputed()
        before = journal_bytes(staging)

        def moved(envelope):
            number = int(envelope["params"][0], 16)
            return canonical_bytes({"id": envelope["id"], "jsonrpc": "2.0", "result": {
                "hash": "0x" + "ab" * 32, "number": hex(number), "transactions": [],
            }})

        transport = aave.AaveTransport(self.state, faults={f"shard {SHARD} boundary-blocks": moved})
        with self.assertRaisesRegex(AlexandriaError, f"shard {SHARD} boundary-blocks re-read is not byte-identical"):
            self.recollect(staging, transport=transport)
        self.assertUnchanged(staging, before)
        self.assertTrue((Path(staging) / "reconciliation" / "reconciliation.json").is_file())

    def test_refuses_a_shard_whose_logs_re_read_differs(self):
        staging = self.disputed()
        before = journal_bytes(staging)
        transport = aave.SecondLogs(
            self.state, shard=str(SHARD), edit=lambda records: records[0].update(logIndex="0x7f"),
        )
        with self.assertRaisesRegex(AlexandriaError, f"shard {SHARD} logs re-read is not byte-identical"):
            self.recollect(staging, transport=transport)
        self.assertUnchanged(staging, before)

    def test_refuses_a_syncing_node_by_name_before_replacing_anything(self):
        staging = self.disputed()
        before = journal_bytes(staging)
        for value, code in (({"currentBlock": "0x1", "highestBlock": "0x2"}, "node-syncing"),
                            (True, "invalid-sync-state")):
            with self.subTest(value=value):
                transport = aave.AaveTransport(self.state, faults={
                    f"shard {SHARD} sync-state": lambda request, value=value: canonical_bytes({
                        "id": request["id"], "jsonrpc": "2.0", "result": value,
                    }),
                })
                with self.assertRaisesRegex(AlexandriaError, f"{code}: shard {SHARD} requires eth_syncing"):
                    self.recollect(staging, transport=transport)
                self.assertEqual(
                    [label for _method, label in transport.calls if label.startswith(f"shard {SHARD} ")],
                    [f"shard {SHARD} sync-state"],
                )
                self.assertUnchanged(staging, before)
                self.assertEqual(checkpoint(staging)["next_shard"], len(self.plan["shards"]))
                self.assertTrue((Path(staging) / "reconciliation" / "reconciliation.json").is_file())

    def test_stops_by_name_before_a_shard_once_the_byte_budget_is_spent(self):
        probe = self.disputed()
        collector = Collector(self.plan, probe, aave.AaveTransport(self.state), registry=self.registry)
        collector.recollect([SHARD], now=NOW)
        spent = collector._bytes
        staging = self.collected("budget")
        before = journal_bytes(staging)
        with mock.patch.object(usdc_interval, "MAX_COLLECT_BYTES", spent):
            with self.assertRaisesRegex(AlexandriaError, "budget before shard 3; that shard was not replaced"):
                self.recollect(staging, shards=(SHARD, 3))
        after = journal_bytes(staging)
        self.assertEqual({name for name in before if before[name] != after[name]}, {f"traces.{SHARD}.jsonl"})


class StaleReconciliationTests(RecollectCase):
    def test_a_reconciliation_made_before_the_replacement_is_not_reused(self):
        staging = self.disputed()
        directory = Path(staging) / "reconciliation"
        self.assertTrue((directory / "reconciliation.json").is_file())
        self.assertTrue((directory / "checkpoint.json").is_file())
        self.recollect(staging)
        # Both are discarded by name, so the build refuses rather than carry
        # a verdict over bytes the tree no longer holds.
        self.assertFalse((directory / "reconciliation.json").exists())
        self.assertFalse((directory / "checkpoint.json").exists())
        with self.assertRaisesRegex(AlexandriaError, "has not been reconciled"):
            Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(self.root / "out")
        # The next reconcile starts at shard 0 and compares every shard again.
        second = aave.AaveTransport(self.state)
        document = Reconciler(
            self.plan, staging, second, aave.SECOND_PROVIDER, registry=self.registry,
        ).reconcile()
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        labels = [label for _method, label in second.calls]
        self.assertIn("shard 0 boundary-blocks second provider", labels)

    def test_a_reconcile_after_the_replacement_binds_the_new_traces_digest(self):
        staging = self.disputed()
        name = f"traces.{SHARD}"
        journal = Path(staging) / "journals" / f"{name}.jsonl"
        stale = json.loads((Path(staging) / "reconciliation" / "reconciliation.json").read_bytes())
        self.assertEqual(stale["journal_sha256"][name], hashlib.sha256(journal.read_bytes()).hexdigest())
        (record,) = self.recollect(staging)["recollected"]
        self.assertEqual(record["old_sha256"], stale["journal_sha256"][name])
        document = self.reconciled(staging)
        new = hashlib.sha256(journal.read_bytes()).hexdigest()
        self.assertEqual(record["new_sha256"], new)
        self.assertEqual(document["journal_sha256"][name], new)
        # Every other journal keeps the digest the stale record bound.
        self.assertEqual(
            {key: value for key, value in document["journal_sha256"].items() if key != name},
            {key: value for key, value in stale["journal_sha256"].items() if key != name},
        )
        output = self.root / "bound"
        Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(output)
        self.assertEqual(check_interval(output)["reconciliation_binding"]["status"], "verified")

    def test_a_stale_record_put_back_after_the_replacement_is_refused(self):
        staging = self.disputed()
        path = Path(staging) / "reconciliation" / "reconciliation.json"
        stale = path.read_bytes()
        self.recollect(staging)
        path.write_bytes(stale)
        with self.assertRaisesRegex(
            AlexandriaError, f"the reconciliation digest differs for journal traces.{SHARD}",
        ):
            Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(self.root / "out")


class RecollectionRecordTests(RecollectCase):
    def released(self):
        staging = self.disputed()
        self.recollect(staging)
        self.reconciled(staging)
        output = self.root / "release"
        release_id = Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(output)
        return staging, output, release_id

    def receipts_component(self, output):
        manifest = json.loads((output / "manifest.json").read_bytes())
        (item,) = [item for item in manifest["components"] if item["name"] == "error-receipts"]
        return json.loads((output / item["object_path"]).read_bytes())

    def test_the_built_release_names_each_recollected_shard(self):
        staging, output, release_id = self.released()
        document = self.receipts_component(output)
        self.assertEqual(document["format"], "alexandria-interval-errors/v2")
        (record,) = document["recollections"]
        journal = (Path(staging) / "journals" / f"traces.{SHARD}.jsonl").read_bytes()
        self.assertEqual(record, {
            "class": "traces",
            "new_sha256": hashlib.sha256(journal).hexdigest(),
            "node_syncing": False,
            "old_sha256": record["old_sha256"],
            "provider_class": self.plan["provider"]["class"],
            "recollected_at": "2026-09-26T18:30:00Z",
            "shard": SHARD,
        })
        self.assertNotEqual(record["old_sha256"], record["new_sha256"])
        self.assertEqual(check_interval(output)["release_id"], release_id)

    def test_a_tree_never_recollected_keeps_the_v1_receipts_document(self):
        staging = self.collected("clean", aave.AaveTransport(self.state))
        self.reconciled(staging)
        output = self.root / "clean-release"
        Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(output)
        self.assertEqual(set(self.receipts_component(output)), {"format", "records"})
        self.assertEqual(self.receipts_component(output)["format"], "alexandria-interval-errors/v1")

    def test_check_refuses_a_record_naming_bytes_the_release_does_not_carry(self):
        _staging, output, _release_id = self.released()
        manifest = json.loads((output / "manifest.json").read_bytes())
        documents = {
            item["name"]: json.loads((output / item["object_path"]).read_bytes())
            for item in manifest["components"]
        }
        parts = usdc_interval.journal_components(self.plan, usdc_interval.declared_classes(self.plan))
        receipts = documents["error-receipts"]
        usdc_interval._check_recollections(self.plan, receipts, documents, parts)
        for field, value, message in (
            ("new_sha256", "0" * 64, f"recollection of shard {SHARD} traces names bytes"),
            ("shard", 4, "names a shard outside its plan"),
            ("provider_class", "https://host.invalid", "not a bounded class name"),
            ("node_syncing", None, "node_syncing must be false"),
            ("node_syncing", True, "node_syncing must be false"),
            ("node_syncing", {"currentBlock": "0x1"}, "node_syncing must be false"),
        ):
            with self.subTest(field=field):
                edited = json.loads(json.dumps(receipts))
                edited["recollections"][0][field] = value
                with self.assertRaisesRegex(AlexandriaError, message):
                    usdc_interval._check_recollections(self.plan, edited, documents, parts)
        edited = json.loads(json.dumps(receipts))
        del edited["recollections"][0]["node_syncing"]
        with self.assertRaisesRegex(AlexandriaError, "recollection record has an unknown shape"):
            usdc_interval._check_recollections(self.plan, edited, documents, parts)
        with self.assertRaisesRegex(AlexandriaError, "error-receipts component has an unknown shape"):
            usdc_interval._check_recollections(
                self.plan, dict(receipts, format="alexandria-interval-errors/v1"), documents, parts,
            )

    def test_the_staging_record_carries_the_sync_answer_and_the_boundary_keeps_its_own(self):
        staging = self.disputed()
        boundary = journal_bytes(staging)[f"boundary-blocks.{SHARD}.jsonl"]
        self.recollect(staging)
        (line,) = (Path(staging) / "receipts" / RECOLLECTION_RECORDS).read_bytes().splitlines()
        self.assertIs(json.loads(line)["node_syncing"], False)
        self.assertEqual(journal_bytes(staging)[f"boundary-blocks.{SHARD}.jsonl"], boundary)
        self.assertIs(json.loads(boundary)["node_syncing"], False)

    def test_a_boundary_staged_before_sync_recording_still_compares_by_response(self):
        original = Staging.record

        def legacy(staging, *args, **kwargs):
            kwargs.pop("node_syncing", None)
            return original(staging, *args, **kwargs)

        with mock.patch.object(Staging, "record", legacy):
            staging = self.disputed()
        boundary = journal_bytes(staging)[f"boundary-blocks.{SHARD}.jsonl"]
        self.assertNotIn("node_syncing", json.loads(boundary))
        (record,) = self.recollect(staging)["recollected"]
        self.assertIs(record["node_syncing"], False)
        self.assertEqual(journal_bytes(staging)[f"boundary-blocks.{SHARD}.jsonl"], boundary)

    def test_no_endpoint_or_bearer_reaches_the_record(self):
        staging, _output, _release_id = self.released()
        data = (Path(staging) / "receipts" / RECOLLECTION_RECORDS).read_bytes()
        for fragment in (aave.ENDPOINT, aave.TOKEN_VALUE, "://", "Bearer"):
            self.assertNotIn(fragment.encode(), data)


class KillBetweenWritesTests(RecollectCase):
    """A kill at each step of the replacement leaves a tree `resume` accepts."""

    def killed(self, where):
        staging = self.disputed()
        old = journal_bytes(staging)
        real_write = interval._atomic_write
        real_append = interval._append_record_once

        def write(path, data):
            if Path(path).name == where:
                raise existing._Killed(where)
            return real_write(path, data)

        def append(*arguments):
            if where == RECOLLECTION_RECORDS:
                raise existing._Killed(where)
            return real_append(*arguments)

        with mock.patch.object(interval, "_atomic_write", write), \
                mock.patch.object(interval, "_append_record_once", append):
            with self.assertRaises(existing._Killed):
                self.recollect(staging)
        return staging, old

    def assertResumesWhole(self, staging, *, replaced):
        name = f"traces.{SHARD}.jsonl"
        clean = journal_bytes(self.collected("clean", aave.AaveTransport(self.state)))
        state = Staging(staging, self.plan).resume()
        self.assertEqual(state["next_shard"], len(self.plan["shards"]))
        self.assertFalse((Path(staging) / REPLACEMENT_INTENT).exists())
        self.assertFalse((Path(staging) / "journals" / f".{name}.recollect").exists())
        after = journal_bytes(staging)
        records = Path(staging) / "receipts" / RECOLLECTION_RECORDS
        if replaced:
            self.assertEqual(after, clean)
            self.assertEqual(len(records.read_bytes().splitlines()), 1)
        else:
            self.assertNotEqual(after[name], clean[name])
            self.assertFalse(records.exists())
        usdc_interval.require_committed_journals(
            Staging(staging, self.plan), Staging(staging, self.plan).committed(), "check",
        )
        # A second resume changes nothing, and collect continues from the end.
        Staging(staging, self.plan).resume()
        self.assertEqual(journal_bytes(staging), after)
        summary = Collector(
            self.plan, staging, aave.AaveTransport(self.state), registry=self.registry,
        ).collect()
        self.assertEqual(summary["collected_shards"], 0)
        status = self.reconciled(staging)["reconciliation"]["status"]
        self.assertEqual(status, "agreed" if replaced else "disputed")

    def test_a_kill_between_the_journal_write_and_the_checkpoint_write_resumes(self):
        staging, _old = self.killed("checkpoint.json")
        # Until it is finished, no reader trusts the tree.
        with self.assertRaisesRegex(AlexandriaError, "shard component replacement is unfinished"):
            Staging(staging, self.plan).committed()
        self.assertResumesWhole(staging, replaced=True)

    def test_a_kill_before_the_intent_is_written_leaves_the_old_tree(self):
        staging, old = self.killed(REPLACEMENT_INTENT)
        self.assertEqual(journal_bytes(staging), old)
        self.assertResumesWhole(staging, replaced=False)

    def test_a_kill_before_the_record_is_appended_resumes(self):
        staging, _old = self.killed(RECOLLECTION_RECORDS)
        self.assertResumesWhole(staging, replaced=True)

    def test_recollect_itself_finishes_an_interrupted_replacement(self):
        staging, _old = self.killed("checkpoint.json")
        summary = self.recollect(staging, shards=(3,))
        self.assertEqual([record["shard"] for record in summary["recollected"]], [3])
        lines = (Path(staging) / "receipts" / RECOLLECTION_RECORDS).read_bytes().splitlines()
        self.assertEqual([json.loads(line)["shard"] for line in lines], [SHARD, 3])


if __name__ == "__main__":
    unittest.main()
