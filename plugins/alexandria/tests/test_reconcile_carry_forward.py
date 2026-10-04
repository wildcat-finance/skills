"""`reconcile --carry-forward`: compare again only the shards `recollect` changed.

Every case runs the constructed Aave fixture under a one-shard-per-component
plan, as `test_interval_recollect` does. The primary loses the trace frames of
one transaction in shard 1, reconciliation disputes them, and `recollect`
replaces that shard's traces and sets the bound record aside. Carry-forward
then compares shard 1 again and keeps the other three shards' comparisons.
No socket is opened.
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

from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
import usdc_interval  # noqa: E402
from usdc_interval import Builder, Reconciler, check_interval  # noqa: E402

from tests import test_aave_v3_collector as aave  # noqa: E402
from tests import test_interval_recollect as recollect  # noqa: E402

SHARD = recollect.SHARD
# The transaction shard 3's logs name, lost the same way in the two-shard cases.
OTHER = "0xc71737b3"


def second_calls(transport):
    """The shard indices a second transport was asked about, opening reads apart."""
    shards = set()
    for _method, label in transport.calls:
        if label.startswith("shard "):
            shards.add(int(label.split()[1]))
    return shards


class CarryForwardCase(recollect.RecollectCase):
    def reconciler(self, staging, transport=None, provider_class=aave.SECOND_PROVIDER):
        self.second = transport or aave.AaveTransport(self.state)
        return Reconciler(
            self.plan, staging, self.second, provider_class, registry=self.registry,
        )

    def carried(self, staging, **kwargs):
        return self.reconciler(staging, **kwargs).carry_forward()

    def repaired(self):
        """A disputed tree whose shard 1 traces were re-collected."""
        staging = self.disputed()
        self.stale = (Path(staging) / "reconciliation" / "reconciliation.json").read_bytes()
        self.recollect(staging)
        return staging

    def prior_path(self, staging):
        return Path(staging) / "reconciliation" / "prior.json"

    def edit_prior(self, staging, edit):
        path = self.prior_path(staging)
        document = json.loads(path.read_bytes())
        edit(document)
        path.write_bytes(canonical_bytes(document))

    def full(self, staging, name="full"):
        """A full reconcile over a copy of the same staging tree."""
        copy = self.root / name
        shutil.copytree(staging, copy)
        return self.reconciled(copy)


class CarryForwardComparisonTests(CarryForwardCase):
    def test_recollect_moves_the_bound_record_to_prior(self):
        staging = self.repaired()
        directory = Path(staging) / "reconciliation"
        self.assertEqual(self.prior_path(staging).read_bytes(), self.stale)
        self.assertFalse((directory / "reconciliation.json").exists())
        self.assertFalse((directory / "checkpoint.json").exists())
        with self.assertRaisesRegex(AlexandriaError, "has not been reconciled"):
            Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(self.root / "out")

    def test_compares_again_exactly_the_changed_shard(self):
        # The Elenchus guard: an unchanged shard asked again, or the changed
        # shard not asked, fails here.
        staging = self.repaired()
        self.carried(staging)
        self.assertEqual(second_calls(self.second), {SHARD})
        labels = [label for _method, label in self.second.calls]
        self.assertIn(f"shard {SHARD} boundary-blocks second provider", labels)
        self.assertTrue(any(label.startswith(f"shard {SHARD} traces 0x") for label in labels))
        self.assertFalse(any(label.startswith("opening read") for label in labels))

    def test_the_changed_shard_takes_its_new_comparison(self):
        # The Elenchus guard's other half: keeping the changed shard's earlier
        # status or dispute fails here.
        staging = self.repaired()
        stale = json.loads(self.stale)
        self.assertEqual(stale["shards"][SHARD]["status"], "partial")
        document = self.carried(staging)
        self.assertEqual(document["shards"][SHARD]["status"], "complete")
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        self.assertEqual(document["reconciliation"]["disputed"], [])

    def test_every_other_shard_keeps_its_status_and_counts(self):
        staging = self.repaired()
        stale = json.loads(self.stale)
        document = self.carried(staging)
        for index, entry in enumerate(document["shards"]):
            if index != SHARD:
                self.assertEqual(entry, stale["shards"][index])

    def test_the_record_names_carried_and_compared_shards_and_binds_every_journal(self):
        staging = self.repaired()
        prior = self.prior_path(staging).read_bytes()
        document = self.carried(staging)
        self.assertEqual(document["carry_forward"], {
            "carried_forward_shards": [0, 2, 3],
            "prior_sha256": hashlib.sha256(prior).hexdigest(),
            "recompared_shards": [SHARD],
        })
        current = {
            name: entry["sha256"]
            for name, entry in usdc_interval._staged_journal_bindings(
                usdc_interval.Staging(staging, self.plan)
            ).items()
        }
        self.assertEqual(document["journal_sha256"], current)
        written = json.loads((Path(staging) / "reconciliation" / "reconciliation.json").read_bytes())
        self.assertEqual(written, document)

    def test_totals_equal_a_full_reconcile_over_the_same_staging(self):
        staging = self.repaired()
        full = self.full(staging)
        document = self.carried(staging)
        carried = {key: value for key, value in document.items() if key != "carry_forward"}
        self.assertEqual(carried, full)

    def test_a_carried_disputed_shard_keeps_exact_totals(self):
        staging = self.scratch("two-staging")
        usdc_interval.Collector(
            self.plan, staging, recollect.LosingTraces(self.state, lost=(recollect.LOST, OTHER)),
            registry=self.registry,
        ).collect()
        before = self.reconciled(staging)
        self.assertEqual(
            {(item["kind"], item["shard"]) for item in before["reconciliation"]["disputed"]},
            {("trace-identity", SHARD), ("trace-identity", 3)},
        )
        self.recollect(staging)
        full = self.full(staging)
        document = self.carried(staging)
        self.assertEqual(document["carry_forward"]["recompared_shards"], [SHARD])
        self.assertEqual(second_calls(self.second), {SHARD})
        self.assertEqual(document["shards"][3]["status"], "partial")
        self.assertEqual(document["reconciliation"]["status"], "disputed")
        self.assertEqual({key: value for key, value in document.items() if key != "carry_forward"}, full)

    def test_a_build_accepts_the_result_and_check_verifies_it(self):
        staging = self.repaired()
        self.carried(staging)
        output = self.root / "carried-release"
        release_id = Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(output)
        result = check_interval(output)
        self.assertEqual(result["release_id"], release_id)
        self.assertEqual(result["reconciliation"], "agreed")
        self.assertEqual(result["reconciliation_binding"]["status"], "verified")
        self.assertEqual(result["reconciliation_carry_forward"], {
            "carried_forward_shards": 3, "recompared_shards": [SHARD],
        })

    def test_a_release_without_carry_forward_reports_no_carry_forward(self):
        staging = self.repaired()
        self.reconciled(staging)
        output = self.root / "full-release"
        Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(output)
        self.assertNotIn("reconciliation_carry_forward", check_interval(output))

    def test_check_refuses_a_compared_shard_the_release_never_recollected(self):
        staging = self.repaired()
        self.carried(staging)
        output = self.root / "carried-release"
        Builder(self.plan, staging, self.registry, created_at=aave.CREATED_AT).build(output)
        manifest = json.loads((output / "manifest.json").read_bytes())
        documents = {
            item["name"]: json.loads((output / item["object_path"]).read_bytes())
            for item in manifest["components"]
        }
        reconciliation = documents["reconciliation"]
        reconciliation["carry_forward"] = {
            "carried_forward_shards": [0, 1, 2],
            "prior_sha256": reconciliation["carry_forward"]["prior_sha256"],
            "recompared_shards": [3],
        }
        self.assertEqual(usdc_interval._carried_shards(reconciliation, 4), ([0, 1, 2], [3]))
        original = usdc_interval._reconciliation_bindings

        def swapped(document, names, label):
            if label == "reconciliation component":
                document.clear()
                document.update(reconciliation)
            return original(document, names, label)

        with mock.patch.object(usdc_interval, "_reconciliation_bindings", swapped):
            with self.assertRaisesRegex(AlexandriaError, "compared shard 3 again, but the release records"):
                self.check_without_verify(output)

    def test_the_cli_flag_compares_only_the_replaced_shard(self):
        staging = self.repaired()
        plan_path, registry_path = self.files(self.plan)
        second = aave.AaveTransport(self.state)
        code, stdout, stderr = self.cli(
            "reconcile", "--plan", plan_path, "--staging", staging, "--registry", registry_path,
            "--provider-class", aave.SECOND_PROVIDER, "--carry-forward", transport=second,
        )
        self.assertEqual(code, 0, stderr)
        self.assertEqual(json.loads(stdout)["carry_forward"]["recompared_shards"], [SHARD])
        self.assertEqual(second_calls(second), {SHARD})

    def test_plain_reconcile_ignores_the_prior_record(self):
        staging = self.repaired()
        document = self.reconciler(staging).reconcile()
        self.assertNotIn("carry_forward", document)
        self.assertEqual(second_calls(self.second), {0, 1, 2, 3})


class CarryForwardRefusalTests(CarryForwardCase):
    def assertRefused(self, staging, message, **kwargs):
        with self.assertRaisesRegex(AlexandriaError, message):
            self.carried(staging, **kwargs)
        self.assertFalse((Path(staging) / "reconciliation" / "reconciliation.json").exists())

    def test_refuses_without_an_earlier_bound_reconciliation(self):
        staging = self.repaired()
        self.prior_path(staging).unlink()
        self.assertRefused(staging, "needs an earlier bound reconciliation")

    def test_refuses_an_earlier_record_without_a_journal_binding(self):
        staging = self.repaired()
        self.edit_prior(staging, lambda document: document.pop("journal_sha256"))
        self.assertRefused(staging, "has no journal digest binding")

    def test_refuses_an_earlier_record_for_another_plan(self):
        staging = self.repaired()
        self.edit_prior(staging, lambda document: document.update(plan_sha256="0" * 64))
        self.assertRefused(staging, "belongs to a different plan")

    def test_refuses_an_earlier_record_for_another_provider_class(self):
        staging = self.repaired()
        self.assertRefused(staging, "compared provider class", provider_class="another class")

    def test_refuses_an_earlier_record_over_another_boundary(self):
        staging = self.repaired()

        def edit(document):
            document["shards"][-1]["end_hash"] = "0x" + "ab" * 32

        self.edit_prior(staging, edit)
        self.assertRefused(staging, "staging boundary differs")

    def test_refuses_a_journal_changed_outside_a_recorded_recollection(self):
        staging = self.repaired()
        self.edit_prior(staging, lambda document: document["journal_sha256"].update({"logs.2": "0" * 64}))
        self.assertRefused(staging, "journal logs.2 changed outside a recorded recollection")

    def test_refuses_a_replacement_the_recollection_records_do_not_explain(self):
        staging = self.repaired()
        path = Path(staging) / "receipts" / recollect.RECOLLECTION_RECORDS
        row = json.loads(path.read_bytes())
        row["old_sha256"] = "0" * 64
        path.write_bytes(canonical_bytes(row))
        self.assertRefused(staging, f"journal traces.{SHARD} changed outside a recorded recollection")

    def test_refuses_an_unreconciled_earlier_record(self):
        staging = self.repaired()

        def edit(document):
            document["reconciliation"].update(status="unreconciled", disputed=[])

        self.edit_prior(staging, edit)
        self.assertRefused(staging, "is unreconciled")

    def test_refuses_an_earlier_record_whose_disputes_reached_the_limit(self):
        staging = self.repaired()
        with mock.patch.object(usdc_interval, "MAX_DISPUTES", 1):
            self.assertRefused(staging, "reached the 1-entry limit")

    def test_refuses_a_carried_dispute_it_cannot_attribute(self):
        # The second provider loses shard 1's frames, so the disputed
        # identities are ones the primary staged; the record cannot say
        # which provider held them, and carrying shard 1 would guess.
        staging = self.collected("clean", aave.AaveTransport(self.state))
        Reconciler(
            self.plan, staging, recollect.LosingTraces(self.state), aave.SECOND_PROVIDER,
            registry=self.registry,
        ).reconcile()
        self.recollect(staging, shards=(3,))
        self.assertRefused(staging, f"does not say which provider held shard {SHARD} trace-identity")

    def test_refuses_totals_the_shard_table_does_not_explain(self):
        staging = self.repaired()
        self.edit_prior(staging, lambda document: document["reconciliation"].update(compared=1, matched=1))
        self.assertRefused(staging, "totals disagree")

    def test_a_failed_second_read_writes_nothing_and_keeps_the_prior(self):
        staging = self.repaired()
        prior = self.prior_path(staging).read_bytes()
        second = aave.AaveTransport(
            self.state, faults={f"shard {SHARD} boundary-blocks second provider": b"not json"},
        )
        self.assertRefused(staging, f"could not compare shard {SHARD} again", transport=second)
        self.assertEqual(self.prior_path(staging).read_bytes(), prior)


if __name__ == "__main__":
    unittest.main()
