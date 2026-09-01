"""The reconciliation refuses to decide, and says so when nothing decided."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from dokimasia_lib import reconcile  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "disposition_build", PLUGIN / "tests" / "fixtures" / "dispositions" / "build.py"
)
build = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(build)


class ReconcileCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.made = build.build_all(Path(self.tmp.name))
        self.inventory = reconcile.read_json(self.made["inventory.json"])
        self.workbook = reconcile.read_json(self.made["workbook.json"])

    def run_with(self, name: str) -> dict:
        return reconcile.reconcile(
            self.inventory, self.workbook, reconcile.read_json(self.made[name])
        )

    def refusal_from(self, name: str) -> str:
        with self.assertRaises(reconcile.ReconcileError) as caught:
            self.run_with(name)
        return str(caught.exception)


class ClosedSet(ReconcileCase):
    def test_a_covered_item_records_the_oracle_it_was_held_to(self):
        made = self.run_with("closed.json")
        covered = [d for d in made["dispositions"] if d["disposition"] == "covered"]
        self.assertTrue(covered)
        for entry in covered:
            self.assertTrue(entry["oracle"], f"{entry['item']} is covered by nothing")

    def test_a_manual_item_carries_a_reason(self):
        made = self.run_with("closed.json")
        manual = [d for d in made["dispositions"] if d["disposition"] == "manual"]
        self.assertTrue(manual)
        for entry in manual:
            self.assertTrue(entry["reason"].strip())

    def test_an_excluded_item_carries_a_reason(self):
        made = self.run_with("closed.json")
        excluded = [d for d in made["dispositions"] if d["disposition"] == "excluded"]
        self.assertTrue(excluded)
        for entry in excluded:
            self.assertTrue(entry["reason"].strip())

    def test_the_gap_list_names_every_manual_and_excluded_item(self):
        made = self.run_with("closed.json")
        expected = {
            d["item"] for d in made["dispositions"]
            if d["disposition"] in reconcile.NEEDS_REASON
        }
        self.assertEqual({g["item"] for g in made["gaps"]}, expected)
        self.assertTrue(all(g["reason"].strip() for g in made["gaps"]))

    def test_an_inventory_item_no_oracle_cites_is_named(self):
        """The most important question the record answers, both directions."""
        made = self.run_with("closed.json")
        cited = made["unmatched"]["items_no_oracle_cites"]
        by_item = {d["item"]: d for d in made["dispositions"]}
        for key in cited:
            self.assertNotEqual(
                by_item[key]["disposition"], "covered",
                f"{key} is covered, so an oracle cites it",
            )
        covered_items = [
            d["item"] for d in made["dispositions"]
            if d["disposition"] == "covered" and d["item"].startswith(
                ("route:", "api:", "action:", "guard:")
            )
        ]
        for key in covered_items:
            self.assertNotIn(key, cited)

    def test_a_workbook_case_no_item_cites_is_named(self):
        made = self.run_with("closed.json")
        cited_oracles = {
            f"case:{d['oracle']}" for d in made["dispositions"] if d["oracle"]
        }
        for key in made["unmatched"]["cases_no_item_cites"]:
            self.assertNotIn(key, cited_oracles)

    def test_both_sides_are_scoped(self):
        made = self.run_with("closed.json")
        self.assertEqual(
            made["counts"]["scoped"],
            made["counts"]["inventory_items"] + made["counts"]["workbook_cases"],
        )


class ClosureRatio(ReconcileCase):
    """The numerator and denominator are proved separately, not through the value."""

    def test_the_denominator_is_the_scoped_count(self):
        made = self.run_with("closed.json")
        scoped = reconcile.scoped_set(self.inventory, self.workbook)
        self.assertEqual(made["closure_ratio"]["denominator"], len(scoped))
        self.assertEqual(made["counts"]["scoped"], len(scoped))

    def test_the_numerator_is_the_count_of_items_carrying_a_disposition(self):
        made = self.run_with("closed.json")
        self.assertEqual(
            made["closure_ratio"]["numerator"], len(made["dispositions"])
        )
        self.assertEqual(made["counts"]["disposed"], len(made["dispositions"]))

    def test_one_is_reached_only_when_nothing_is_unanswered(self):
        closed = self.run_with("closed.json")
        self.assertTrue(closed["closure_ratio"]["closed"])
        self.assertEqual(closed["closure_ratio"]["value"], 1.0)
        self.assertEqual(closed["undisposed"], [])

    def test_an_unanswered_item_holds_the_ratio_below_one(self):
        """This must not refuse. An open ratio is a true answer."""
        made = self.run_with("no-disposition.json")
        self.assertFalse(made["closure_ratio"]["closed"])
        self.assertLess(made["closure_ratio"]["value"], 1.0)
        self.assertEqual(len(made["undisposed"]), 1)
        self.assertEqual(
            made["closure_ratio"]["numerator"] + len(made["undisposed"]),
            made["closure_ratio"]["denominator"],
        )


class Refusals(ReconcileCase):
    def test_two_dispositions_on_one_item_refuse(self):
        self.assertIn("two dispositions", self.refusal_from("two-dispositions.json"))

    def test_an_oracle_the_workbook_does_not_hold_refuses(self):
        self.assertIn(
            "the workbook does not hold", self.refusal_from("absent-oracle.json")
        )

    def test_an_unreviewed_oracle_refuses(self):
        message = self.refusal_from("unreviewed-oracle.json")
        self.assertIn("nothing is held to it", message)
        self.assertIn(reconcile.UNREVIEWED_STATUS, message)

    def test_covered_without_an_oracle_refuses(self):
        self.assertIn(
            "names no oracle", self.refusal_from("covered-without-oracle.json")
        )

    def test_a_manual_item_without_a_reason_refuses(self):
        self.assertIn("carries no reason", self.refusal_from("missing-reason.json"))

    def test_a_moved_inventory_digest_refuses_as_stale(self):
        message = self.refusal_from("stale-inventory.json")
        self.assertIn("stale", message)
        self.assertIn("inventory_sha256", message)

    def test_a_moved_workbook_digest_refuses_as_stale(self):
        message = self.refusal_from("stale-workbook.json")
        self.assertIn("stale", message)
        self.assertIn("workbook_sha256", message)

    def test_a_disposition_naming_an_unscoped_item_refuses(self):
        self.assertIn("not a scoped item", self.refusal_from("unknown-item.json"))

    def test_an_oracle_carrying_no_status_field_refuses(self):
        """The check must not pass by absence.

        Comparing only against the unreviewed value lets every oracle through
        in a workbook that has no status column at all, which is the control
        failing open in exactly the direction that widens coverage.
        """
        import copy
        from dokimasia_lib import workbook as workbook_lib

        stripped = copy.deepcopy(self.workbook)
        for case in stripped["cases"]:
            case["fields"].pop(reconcile.STATUS_FIELD, None)
        stripped["workbook_sha256"] = workbook_lib.workbook_digest(stripped["cases"])
        declared = reconcile.read_json(self.made["closed.json"])
        declared["workbook_sha256"] = stripped["workbook_sha256"]
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(self.inventory, stripped, declared)
        self.assertIn("carries no Status field", str(caught.exception))

    def test_an_oracle_whose_status_is_blank_refuses(self):
        import copy
        from dokimasia_lib import workbook as workbook_lib

        blanked = copy.deepcopy(self.workbook)
        for case in blanked["cases"]:
            case["fields"][reconcile.STATUS_FIELD] = "  "
        blanked["workbook_sha256"] = workbook_lib.workbook_digest(blanked["cases"])
        declared = reconcile.read_json(self.made["closed.json"])
        declared["workbook_sha256"] = blanked["workbook_sha256"]
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(self.inventory, blanked, declared)
        self.assertIn("is blank", str(caught.exception))

    def test_a_reason_over_the_cap_refuses_whatever_the_disposition(self):
        # The cap is declared over reasons, so a covered entry is bound by it
        # even though covered is not required to carry one.
        self.assertIn("over the", self.refusal_from("oversize-reason.json"))

    def test_a_manual_item_naming_an_oracle_refuses(self):
        """A row cannot read as both decided by a person and held to a case."""
        self.assertIn(
            "also names an oracle", self.refusal_from("manual-with-oracle.json")
        )

    def test_a_case_cannot_be_covered_by_itself_or_by_another_case(self):
        """A case is an oracle, not something held to one.

        Left open, a row could name itself and close the ratio on its own
        evidence, which is the record certifying a circle.
        """
        self.assertIn(
            "cannot be covered", self.refusal_from("case-covered-by-itself.json")
        )
        declared = reconcile.read_json(self.made["closed.json"])
        cases = [c["id"] for c in self.workbook["cases"]]
        for entry in declared["dispositions"]:
            if entry["item"] == f"case:{cases[0]}":
                entry.clear()
                entry.update({
                    "item": f"case:{cases[0]}",
                    "disposition": "covered",
                    "oracle": cases[2],
                })
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(self.inventory, self.workbook, declared)
        self.assertIn("cannot be covered", str(caught.exception))

    def test_a_state_outside_the_vocabulary_refuses(self):
        self.assertIn("is not one of", self.refusal_from("bad-vocabulary.json"))

    def test_a_set_declaring_the_wrong_schema_refuses(self):
        declared = reconcile.read_json(self.made["closed.json"])
        declared["schema"] = "something-else/v1"
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(self.inventory, self.workbook, declared)
        self.assertIn("declares schema", str(caught.exception))


class NoPathMarksAnythingCovered(ReconcileCase):
    """The control this step exists for: an agent cannot widen coverage."""

    def test_no_disposition_appears_that_the_set_did_not_declare(self):
        made = self.run_with("closed.json")
        declared = reconcile.read_json(self.made["closed.json"])["dispositions"]
        self.assertEqual(
            sorted(d["item"] for d in made["dispositions"]),
            sorted(d["item"] for d in declared),
        )
        by_item = {d["item"]: d["disposition"] for d in declared}
        for entry in made["dispositions"]:
            self.assertEqual(entry["disposition"], by_item[entry["item"]])

    def test_an_empty_set_covers_nothing_rather_than_inferring_a_match(self):
        """Every case here shares an identifier shape with the inventory.

        A reconciler that inferred coverage from a match would return a
        non-zero covered count. This one returns none, because nothing was
        declared.
        """
        declared = reconcile.read_json(self.made["closed.json"])
        declared["dispositions"] = []
        made = reconcile.reconcile(self.inventory, self.workbook, declared)
        self.assertEqual(made["counts"]["by_disposition"]["covered"], 0)
        self.assertEqual(made["closure_ratio"]["numerator"], 0)
        self.assertFalse(made["closure_ratio"]["closed"])

    def test_the_module_exposes_no_verb_that_assigns_a_disposition(self):
        writers = [
            name for name in dir(reconcile)
            if any(word in name for word in ("assign", "propose", "infer", "mark"))
        ]
        self.assertEqual(writers, [], f"a disposition-writing path exists: {writers}")


class RecordShape(ReconcileCase):
    def test_the_record_validates_against_the_committed_schema(self):
        made = self.run_with("closed.json")
        schema = json.loads(
            (PLUGIN / "schemas" / "coverage-v1.json").read_text(encoding="utf-8")
        )
        self.assertEqual(sorted(made), sorted(schema["required"]))
        for key in made:
            self.assertIn(key, schema["properties"], f"{key} is not in the schema")

    def test_the_digest_is_stable_and_ignores_the_subject_labels(self):
        first = self.run_with("closed.json")
        second = self.run_with("closed.json")
        self.assertEqual(
            reconcile.coverage_digest(first), reconcile.coverage_digest(second)
        )
        moved = dict(second)
        moved["subject"] = {"inventory_sha256": "1" * 64, "workbook_sha256": "2" * 64}
        self.assertEqual(
            reconcile.coverage_digest(first), reconcile.coverage_digest(moved)
        )

    def test_every_enforced_bound_appears_in_the_caps_block(self):
        """A bound enforced but unpublished cannot be audited from the record."""
        made = self.run_with("closed.json")
        self.assertEqual(
            made["caps"],
            {
                "dispositions": reconcile.MAX_DISPOSITIONS,
                "reason_bytes": reconcile.MAX_REASON_BYTES,
                "input_bytes": reconcile.MAX_FILE_BYTES,
            },
        )

    def test_the_record_is_the_same_however_the_dispositions_are_ordered(self):
        first = self.run_with("closed.json")
        declared = reconcile.read_json(self.made["closed.json"])
        declared["dispositions"] = list(reversed(declared["dispositions"]))
        second = reconcile.reconcile(self.inventory, self.workbook, declared)
        self.assertEqual(
            reconcile.coverage_digest(first), reconcile.coverage_digest(second)
        )

    def test_the_counts_add_up_three_ways(self):
        made = self.run_with("no-disposition.json")
        counts = made["counts"]
        self.assertEqual(
            sum(counts["by_disposition"].values()), counts["disposed"]
        )
        self.assertEqual(
            counts["inventory_items"] + counts["workbook_cases"], counts["scoped"]
        )
        self.assertEqual(
            counts["disposed"] + counts["undisposed"], counts["scoped"]
        )

    def test_the_vocabulary_is_recorded_so_a_reader_knows_which_one_applied(self):
        made = self.run_with("closed.json")
        self.assertEqual(made["vocabulary"], list(reconcile.DISPOSITIONS))


class BoundedReads(ReconcileCase):
    def test_a_file_over_the_byte_cap_refuses(self):
        target = Path(self.tmp.name) / "big.json"
        target.write_text(json.dumps({"padding": "x" * 4096}))
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.read_json(target, max_bytes=64)
        self.assertIn("over the", str(caught.exception))

    def test_a_symlink_refuses(self):
        target = Path(self.tmp.name) / "link.json"
        target.symlink_to(self.made["closed.json"])
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.read_json(target)
        self.assertIn("symlink", str(caught.exception))

    def test_a_payload_that_is_not_one_object_refuses(self):
        target = Path(self.tmp.name) / "list.json"
        target.write_text("[1, 2, 3]")
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.read_json(target)
        self.assertIn("not one JSON object", str(caught.exception))


class MalformedRecords(ReconcileCase):
    """A mistyped record is an ordinary mistake and must refuse by name.

    Every other refusal in this plugin is named. Reaching a `KeyError` would
    make this the one place a caller got a stack trace instead.
    """

    def test_an_inventory_item_missing_a_field_refuses_by_name(self):
        broken = {"inventory_sha256": self.inventory["inventory_sha256"],
                  "items": [{"kind": "route"}]}
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(
                broken, self.workbook, reconcile.read_json(self.made["closed.json"])
            )
        self.assertIn("missing 'source'", str(caught.exception))

    def test_a_workbook_case_missing_a_field_refuses_by_name(self):
        broken = {"workbook_sha256": self.workbook["workbook_sha256"],
                  "cases": [{"id": "ADM-01"}]}
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(
                self.inventory, broken, reconcile.read_json(self.made["closed.json"])
            )
        self.assertIn("missing", str(caught.exception))

    def test_a_record_with_no_collection_refuses_by_name(self):
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(
                {"inventory_sha256": self.inventory["inventory_sha256"]},
                self.workbook,
                reconcile.read_json(self.made["closed.json"]),
            )
        self.assertIn("holds no items list", str(caught.exception))

    def test_a_disposition_list_that_is_not_a_list_refuses_by_name(self):
        declared = reconcile.read_json(self.made["closed.json"])
        declared["dispositions"] = "nope"
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(self.inventory, self.workbook, declared)
        self.assertIn("holds no dispositions list", str(caught.exception))

    def test_a_disposition_entry_that_is_not_an_object_refuses_by_name(self):
        declared = reconcile.read_json(self.made["closed.json"])
        declared["dispositions"] = ["a string"]
        with self.assertRaises(reconcile.ReconcileError) as caught:
            reconcile.reconcile(self.inventory, self.workbook, declared)
        self.assertIn("is not an object", str(caught.exception))

    def test_the_command_refuses_rather_than_tracing_back(self):
        import json as json_module
        import subprocess

        root = Path(self.tmp.name)
        (root / "broken.json").write_text(json_module.dumps({
            "inventory_sha256": "a" * 64, "items": [{"kind": "route"}],
        }))
        result = subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / "dokimasia.py"), "reconcile",
             "--inventory", str(root / "broken.json"),
             "--workbook", str(self.made["workbook.json"]),
             "--dispositions", str(self.made["closed.json"])],
            capture_output=True, text=True, timeout=60,
        )
        self.assertNotIn("Traceback", result.stderr)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("refused", result.stderr)


class ContractCheck(unittest.TestCase):
    def test_the_bundled_check_passes(self):
        self.assertEqual(reconcile.check(), [])


if __name__ == "__main__":
    unittest.main()
