from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tests import test_usdc_interval as existing
from tests.test_log_attribution_parts import reissue
from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.errors import AlexandriaError
from alexandria_lib import interval
import usdc_interval
from usdc_interval import Builder, Reconciler, check_interval


class _StartupRead(Exception):
    """Carries the journal reads `reconcile` made before its first comparison."""


class ReconciliationBindingTests(existing.ReleaseTestCase):
    def record(self, staging):
        return staging / "reconciliation" / "reconciliation.json"

    def test_same_length_edit_after_reconcile_refuses_build_by_journal_name(self):
        for split in (False, True):
            with self.subTest(split=split):
                plan = deepcopy(self.plan)
                if split:
                    plan["shards_per_component"] = 2
                staging, output = self.pipeline(f"edited-{split}", plan=plan)
                name = "logs.0" if split else "logs"
                path = staging / "journals" / f"{name}.jsonl"
                before = path.read_bytes()
                after = before.replace(b"abab", b"abac", 1)
                self.assertNotEqual(before, after)
                self.assertEqual(len(before), len(after))
                path.write_bytes(after)
                with self.assertRaisesRegex(AlexandriaError, rf"reconcil.*{name}"):
                    self.build(staging, output, plan=plan)
                self.assertFalse(output.exists())
                self.assertEqual(path.read_bytes(), after)

    def test_reissued_release_with_same_length_log_edit_refuses_check(self):
        for split in (False, True):
            with self.subTest(split=split):
                plan = deepcopy(self.plan)
                if split:
                    plan["shards_per_component"] = 2
                staging, output = self.pipeline(f"reissued-{split}", plan=plan)
                self.build(staging, output, plan=plan)
                changed = self.root / f"changed-{split}"
                name = "logs.0" if split else "logs"

                def edit(documents):
                    record = documents[name]["records"][0]
                    before = record["response"]
                    record["response"] = before.replace("abab", "abac", 1)
                    self.assertNotEqual(before, record["response"])
                    self.assertEqual(len(before), len(record["response"]))

                reissue(output, changed, edit=edit)
                with self.assertRaisesRegex(AlexandriaError, rf"reconcil.*{name}"):
                    check_interval(changed)

    def test_binding_covers_every_physical_journal_and_survives_resume(self):
        plan = deepcopy(self.plan)
        plan["shards_per_component"] = 2
        staging, output = self.pipeline(plan=plan)
        before = self.record(staging).read_bytes()
        record = json.loads(before)
        self.assertEqual(record["journal_sha256"], {
            path.stem: hashlib.sha256(path.read_bytes()).hexdigest()
            for path in (staging / "journals").glob("*.jsonl")
        })
        Reconciler(plan, staging, existing.FixtureTransport(self.state),
                   "second archive endpoint, class only").reconcile()
        self.assertEqual(self.record(staging).read_bytes(), before)
        self.build(staging, output, plan=plan)
        self.assertEqual(check_interval(output)["reconciliation_binding"], {
            "status": "verified", "gaps": [],
        })

    def test_same_length_whitespace_edit_refuses_every_journal_by_name(self):
        staging, output = self.pipeline()
        for path in sorted((staging / "journals").glob("*.jsonl")):
            with self.subTest(journal=path.stem):
                before = path.read_bytes()
                self.assertTrue(before.endswith(b"\n"))
                path.write_bytes(before[:-1] + b" ")
                with self.assertRaisesRegex(AlexandriaError, rf"reconcil.*{path.stem}"):
                    self.build(staging, output)
                path.write_bytes(before)
        self.assertFalse(output.exists())

    def test_legacy_record_rebuilds_unchanged_and_reports_absent_binding(self):
        staging, output = self.pipeline()
        existing.historical_reconciliation(staging)
        before = self.record(staging).read_bytes()
        release_id = self.build(staging, output)
        checked = check_interval(output)
        self.assertEqual(checked["reconciliation"], "agreed")
        self.assertEqual(checked["reconciliation_binding"], {
            "status": "absent",
            "gaps": ["the reconciliation record has no journal digest binding"],
        })
        self.assertEqual(self.record(staging).read_bytes(), before)
        self.assertEqual(self.build(staging, self.root / "again"), release_id)
        self.assertNotIn("journal_sha256", existing.component_document(output, "reconciliation"))

    def test_malformed_binding_refuses_build_and_check(self):
        staging, output = self.pipeline()
        self.build(staging, output)
        original = json.loads(self.record(staging).read_bytes())
        bindings = original["journal_sha256"]
        cases = [None, [], {}, dict(bindings, logs="A" * 64),
                 dict(bindings, logs=1), dict(bindings, extra="0" * 64)]
        for index, value in enumerate(cases):
            with self.subTest(binding=value):
                document = dict(original, journal_sha256=value)
                self.record(staging).write_bytes(canonical_bytes(document))
                with self.assertRaisesRegex(AlexandriaError, "reconciliation"):
                    self.build(staging, self.root / f"bad-build-{index}")
                changed = self.root / f"bad-release-{index}"
                reissue(output, changed, edit=lambda documents: documents.update(reconciliation=document))
                with self.assertRaisesRegex(AlexandriaError, "reconciliation"):
                    check_interval(changed)

    def test_changed_journal_during_reconcile_refuses_before_record(self):
        staging, _output = self.pipeline(reconcile=False)
        path = staging / "journals" / "logs.jsonl"
        reconciler = Reconciler(self.plan, staging, existing.FixtureTransport(self.state),
                                "second archive endpoint, class only")
        original = reconciler._read_journals

        def change_after_read():
            result = original()
            path.write_bytes(path.read_bytes().replace(b"abab", b"abac", 1))
            return result

        with mock.patch.object(reconciler, "_read_journals", side_effect=change_after_read):
            with self.assertRaisesRegex(AlexandriaError, "reconcil.*logs"):
                reconciler.reconcile()
        self.assertFalse(self.record(staging).exists())

    def test_reconcile_reads_each_journal_once_before_comparing(self):
        for split in (False, True):
            with self.subTest(split=split):
                plan = deepcopy(self.plan)
                if split:
                    plan["shards_per_component"] = 2
                staging, _output = self.pipeline(f"once-{split}", plan=plan, reconcile=False)
                reconciler = Reconciler(plan, staging, existing.FixtureTransport(self.state),
                                        "second archive endpoint, class only")
                reads = []
                original_confined = usdc_interval.read_confined_file
                original_regular = interval.read_regular

                def confined(root, value, label, **kwargs):
                    reads.append(value)
                    return original_confined(root, value, label, **kwargs)

                def regular(path, label, maximum):
                    if path.parent.name == "journals":
                        reads.append(path.name)
                    return original_regular(path, label, maximum)


                def second(*args, **kwargs):
                    # Stop at the first comparison: everything before it is start-up.
                    raise _StartupRead(sorted(reads))

                with mock.patch.object(usdc_interval, "read_confined_file", confined), \
                        mock.patch.object(interval, "read_regular", regular), \
                        mock.patch.object(reconciler, "_second_raw", second):
                    with self.assertRaises(_StartupRead) as caught:
                        reconciler.reconcile()
                names = sorted(f"{name}.jsonl" for name in reconciler.staging.journal_names)
                self.assertEqual(caught.exception.args[0], names)

    def test_journal_changed_after_builder_binding_check_still_refuses(self):
        class ChangingBuilder(Builder):
            def _reconciliation(self):
                record = super()._reconciliation()
                path = self.staging.journals / "logs.jsonl"
                path.write_bytes(path.read_bytes().replace(b"abab", b"abac", 1))
                return record

        staging, output = self.pipeline()
        with self.assertRaisesRegex(AlexandriaError, "reconcil.*logs"):
            self.build(staging, output, builder=ChangingBuilder)
        self.assertFalse(output.exists())

    def test_unreconciled_provider_response_keeps_binding_without_claiming_agreement(self):
        second = existing.FixtureTransport(self.state, faults={
            "shard 0 logs second provider": canonical_bytes(
                {"error": {"code": -32000}, "id": 2, "jsonrpc": "2.0"}
            ),
        })
        staging, output = self.pipeline(second=second)
        self.build(staging, output)
        checked = check_interval(output)
        self.assertEqual(checked["reconciliation"], "unreconciled")
        self.assertEqual(checked["reconciliation_binding"]["status"], "verified")
