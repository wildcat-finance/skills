"""A drafted set covers everything, decides nothing, and survives editing.

The point of the verb is that a reviewer corrects a draft instead of authoring
261 entries. These check the three things that makes safe: it cannot draft
`covered`, it cannot confirm anything, and regenerating it does not throw away
what a person already decided.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
SCRIPT = PLUGIN / "scripts" / "dokimasia.py"
sys.path.insert(0, str(PLUGIN / "scripts"))

from dokimasia_lib import propose  # noqa: E402
from dokimasia_lib import reconcile  # noqa: E402
from dokimasia_lib import schema  # noqa: E402

sys.path.insert(0, str(PLUGIN / "tests" / "fixtures" / "dispositions"))
import build  # noqa: E402


class ProposeCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.made = build.build_all(Path(self.tmp.name))
        self.inventory = reconcile.read_json(self.made["inventory.json"])
        self.workbook = reconcile.read_json(self.made["workbook.json"])

    def draft(self, existing=None):
        return propose.propose(self.inventory, self.workbook, existing)


class Completeness(ProposeCase):
    def test_every_scoped_item_gets_exactly_one_entry(self):
        record, counts = self.draft()
        scoped = reconcile.scoped_set(self.inventory, self.workbook)
        items = [entry["item"] for entry in record["dispositions"]]
        self.assertEqual(sorted(items), sorted(entry["id"] for entry in scoped))
        self.assertEqual(len(items), len(set(items)))
        self.assertEqual(counts["scoped"], len(scoped))

    def test_every_entry_carries_a_reason_inside_the_cap(self):
        record, _ = self.draft()
        for entry in record["dispositions"]:
            with self.subTest(item=entry["item"]):
                self.assertTrue(entry["reason"].strip())
                self.assertLessEqual(
                    len(entry["reason"].encode("utf-8")), propose.MAX_REASON_BYTES
                )

    def test_a_reason_quotes_the_record_and_asserts_no_outcome(self):
        record, _ = self.draft()
        for entry in record["dispositions"]:
            with self.subTest(item=entry["item"]):
                self.assertTrue(entry["reason"].startswith("drafted from"))
        forbidden = ("passed", "failed", "works", "tested", "Not Run")
        joined = " ".join(e["reason"] for e in record["dispositions"])
        for word in forbidden:
            self.assertNotIn(word, joined)

    def test_the_drafted_set_binds_the_two_digests_it_was_built_from(self):
        record, _ = self.draft()
        self.assertEqual(
            record["inventory_sha256"], self.inventory["inventory_sha256"]
        )
        self.assertEqual(record["workbook_sha256"], self.workbook["workbook_sha256"])

    def test_the_drafted_set_validates_against_its_committed_schema(self):
        record, _ = self.draft()
        self.assertEqual(schema.check(record), [])


class NothingIsDecided(ProposeCase):
    def test_no_entry_arrives_confirmed(self):
        record, _ = self.draft()
        self.assertTrue(all(e["confirmed"] is False for e in record["dispositions"]))

    def test_no_entry_is_covered_and_none_names_an_oracle(self):
        record, _ = self.draft()
        states = {entry["disposition"] for entry in record["dispositions"]}
        self.assertEqual(states, set(states) & set(propose.DRAFTABLE))
        self.assertNotIn("covered", states)
        self.assertTrue(all(e["oracle"] == "" for e in record["dispositions"]))

    def test_the_module_holds_no_covered_branch_at_all(self):
        """The absence is a property of the code, so assert it of the code."""
        source = (PLUGIN / "scripts" / "dokimasia_lib" / "propose.py").read_text(
            encoding="utf-8"
        )
        executable = re.sub(r'""".*?"""', "", source, flags=re.S)
        executable = re.sub(r"#.*", "", executable)
        self.assertNotIn("covered", executable)
        self.assertEqual(propose.DRAFTABLE, ("manual", "excluded"))

    def test_a_drafted_set_closes_the_ratio_at_zero(self):
        record, _ = self.draft()
        made = reconcile.reconcile(self.inventory, self.workbook, record)
        self.assertEqual(made["closure_ratio"]["numerator"], 0)
        self.assertFalse(made["closure_ratio"]["closed"])
        self.assertEqual(made["counts"]["unconfirmed"], made["counts"]["scoped"])

    def test_a_case_is_drafted_manual_and_an_item_excluded(self):
        record, _ = self.draft()
        by_item = {e["item"]: e for e in record["dispositions"]}
        for item, entry in by_item.items():
            with self.subTest(item=item):
                expected = "manual" if item.startswith("case:") else "excluded"
                self.assertEqual(entry["disposition"], expected)


class Regeneration(ProposeCase):
    def _edited(self):
        record, _ = self.draft()
        edited = json.loads(json.dumps(record))
        edited["dispositions"][0]["confirmed"] = True
        edited["dispositions"][1]["reason"] = "a person wrote this instead"
        return record, edited

    def test_a_confirmed_entry_survives_byte_for_byte(self):
        _, edited = self._edited()
        before = json.dumps(edited["dispositions"][0], sort_keys=True)
        again, counts = self.draft(edited)
        after = next(
            e for e in again["dispositions"]
            if e["item"] == edited["dispositions"][0]["item"]
        )
        self.assertEqual(json.dumps(after, sort_keys=True), before)

    def test_an_edited_draft_survives_byte_for_byte(self):
        _, edited = self._edited()
        before = json.dumps(edited["dispositions"][1], sort_keys=True)
        again, _ = self.draft(edited)
        after = next(
            e for e in again["dispositions"]
            if e["item"] == edited["dispositions"][1]["item"]
        )
        self.assertEqual(json.dumps(after, sort_keys=True), before)

    def test_untouched_drafts_are_replaced_and_counted(self):
        record, edited = self._edited()
        again, counts = self.draft(edited)
        self.assertEqual(counts["preserved"], 2)
        self.assertEqual(counts["replaced"], counts["scoped"] - 2)
        self.assertEqual(counts["added"], 0)
        self.assertEqual(counts["dropped"], 0)

    def test_an_entry_with_no_recorded_digest_is_treated_as_written_by_hand(self):
        """Unknown provenance reads as a person, which is the safe direction."""
        record, _ = self.draft()
        edited = json.loads(json.dumps(record))
        edited["dispositions"][0].pop("proposed_sha256")
        edited["dispositions"][0]["reason"] = "hand written, no digest"
        again, counts = self.draft(edited)
        after = next(
            e for e in again["dispositions"]
            if e["item"] == edited["dispositions"][0]["item"]
        )
        self.assertEqual(after["reason"], "hand written, no digest")
        self.assertEqual(counts["preserved"], 1)

    def test_an_entry_whose_item_left_the_scoped_set_is_reported(self):
        record, _ = self.draft()
        edited = json.loads(json.dumps(record))
        gone = dict(edited["dispositions"][0])
        gone["item"] = "route:src/app/removed/page.tsx"
        gone["confirmed"] = True
        edited["dispositions"].append(gone)
        again, counts = self.draft(edited)
        self.assertEqual(counts["dropped"], 1)
        self.assertEqual(counts["dropped_items"], ["route:src/app/removed/page.tsx"])
        self.assertNotIn(
            "route:src/app/removed/page.tsx",
            [e["item"] for e in again["dispositions"]],
        )

    def test_an_existing_set_answering_twice_refuses(self):
        record, _ = self.draft()
        edited = json.loads(json.dumps(record))
        edited["dispositions"].append(dict(edited["dispositions"][0]))
        with self.assertRaises(propose.ProposeError) as caught:
            self.draft(edited)
        self.assertIn("twice", str(caught.exception))

    def test_an_existing_set_with_the_wrong_schema_refuses(self):
        record, _ = self.draft()
        edited = json.loads(json.dumps(record))
        edited["schema"] = "dokimasia-imaginary/v1"
        with self.assertRaises(propose.ProposeError) as caught:
            self.draft(edited)
        self.assertIn("declares schema", str(caught.exception))

    def test_two_drafts_of_the_same_records_agree(self):
        first, _ = self.draft()
        second, _ = self.draft()
        self.assertEqual(
            json.dumps(first, sort_keys=True), json.dumps(second, sort_keys=True)
        )


class WriteBoundary(ProposeCase):
    def run_verb(self, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "propose",
             "--inventory", str(self.made["inventory.json"]),
             "--workbook", str(self.made["workbook.json"]), *extra],
            capture_output=True, text=True, cwd=str(ROOT), timeout=60,
        )

    def test_a_label_carrying_a_separator_refuses_and_writes_nothing(self):
        result = self.run_verb("--label", "../../../../tmp/pwned")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not one safe path segment", result.stderr)
        self.assertFalse(Path("/tmp/pwned.dispositions.json").exists())

    def test_a_label_carrying_a_parent_reference_refuses(self):
        result = self.run_verb("--label", "..")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not one safe path segment", result.stderr)

    def test_the_write_is_staged_and_renamed(self):
        """A killed run leaves the previous file, never half of the new one."""
        source = (PLUGIN / "scripts" / "dokimasia_lib" / "propose.py").read_text(
            encoding="utf-8"
        )
        self.assertIn("os.replace(staging, path)", source)

    def test_writing_through_a_symlink_refuses(self):
        with tempfile.TemporaryDirectory() as raw:
            real = Path(raw) / "real.json"
            real.write_text("{}")
            link = Path(raw) / "link.json"
            link.symlink_to(real)
            record, _ = self.draft()
            with self.assertRaises(propose.ProposeError) as caught:
                propose.write_set(record, link)
            self.assertIn("symlink", str(caught.exception))

    def test_the_verb_without_a_label_writes_nothing_and_prints_the_set(self):
        result = self.run_verb()
        self.assertEqual(result.returncode, 0, result.stderr)
        made = json.loads(result.stdout)
        self.assertEqual(made["schema"], propose.SCHEMA)


class ContractCheck(unittest.TestCase):
    def test_the_declared_contract_holds(self):
        self.assertEqual(propose.check(), [])


if __name__ == "__main__":
    unittest.main()
