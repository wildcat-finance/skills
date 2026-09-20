"""Focused tests for historical success-criteria receipt custody."""

import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "plugins/hexaemeron/skills/fiat/scripts/criteria_receipts.py"
SPEC = importlib.util.spec_from_file_location("criteria_receipts_tests", SOURCE)
RECEIPTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RECEIPTS)


COMMAND = "python3 plugins/hexaemeron/tests/run_tests.py --jobs 12 --elenchus-report .hexaemeron/reports/step-4-exit.json"


def join(*, changed=False):
    rows = []
    for identifier, claim in (("done", "finished"), ("pending", "still due")):
        command = COMMAND + (" --changed" if changed and identifier == "done" else "")
        rows.append({
            "id": identifier,
            "claim": claim,
            "step": 4,
            "command": command,
            "descriptor_sha256": ("1" if identifier == "done" else "2") * 64,
            "exit": {
                "step": 4,
                "command": command,
                "command_sha256": __import__("hashlib").sha256(command.encode()).hexdigest(),
            },
        })
    return {
        "schema": RECEIPTS.JOIN_SCHEMA,
        "declaration_sha256": "3" * 64,
        "runbook_sha256": "b" * 64,
        "criteria": rows,
    }


def admission():
    return {"join": join(), "study_sha256": "a" * 64, "runbook_sha256": "b" * 64}


def attempt(identifier="done", runbook="b" * 64):
    return {
        "attempt_id": "attempt-" + identifier,
        "study_sha256": "a" * 64,
        "runbook_sha256": runbook,
        "criterion_ids": [identifier],
        "settled": True,
        "status": "settled",
    }


class CriteriaReceiptTests(unittest.TestCase):
    def test_initial_history_round_trips_canonically(self):
        receipt = RECEIPTS.new(admission())
        encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"))
        restored = json.loads(encoded)
        self.assertEqual(RECEIPTS.history(restored)[0]["join"], join())

    def test_completion_refuses_missing_descriptor(self):
        receipt = RECEIPTS.new(admission())
        with self.assertRaisesRegex(RECEIPTS.Refusal, "unmet-criteria:pending"):
            RECEIPTS.require_complete(receipt, [attempt()])

    def test_completed_descriptor_cannot_be_removed(self):
        receipt = RECEIPTS.new(admission())
        candidate = join()
        candidate["criteria"] = [candidate["criteria"][1]]
        with self.assertRaisesRegex(RECEIPTS.Refusal, "completed-descriptor-removed"):
            RECEIPTS.amend(receipt, candidate, study_sha256="a" * 64,
                            runbook_sha256="c" * 64, amendment_sha256="4" * 64,
                            attempts=[attempt()])

    def test_completed_descriptor_cannot_change_or_reassign(self):
        receipt = RECEIPTS.new(admission())
        candidate = join(changed=True)
        with self.assertRaisesRegex(RECEIPTS.Refusal, "completed-descriptor-changed"):
            RECEIPTS.amend(receipt, candidate, study_sha256="a" * 64,
                            runbook_sha256="c" * 64, amendment_sha256="4" * 64,
                            attempts=[attempt()])
        reassigned = join()
        reassigned["criteria"][0]["id"] = "moved"
        with self.assertRaisesRegex(RECEIPTS.Refusal, "completed-descriptor-removed"):
            RECEIPTS.amend(receipt, reassigned, study_sha256="a" * 64,
                            runbook_sha256="c" * 64, amendment_sha256="5" * 64,
                            attempts=[attempt()])

    def test_completed_descriptor_ignores_moved_exit_metadata(self):
        receipt = RECEIPTS.new(admission())
        candidate = join()
        candidate["criteria"][0]["exit"]["offset"] = 999
        candidate["criteria"][0]["exit"]["source"] = {
            "path": "/different/runbook",
            "offset": 999,
        }
        amended = RECEIPTS.amend(
            receipt, candidate, study_sha256="a" * 64,
            runbook_sha256="c" * 64, amendment_sha256="6" * 64,
            attempts=[attempt()],
        )
        self.assertEqual(len(amended["versions"]), 2)

    def test_unbuilt_descriptor_can_change_but_needs_new_result(self):
        receipt = RECEIPTS.new(admission())
        candidate = join()
        candidate["criteria"][1]["claim"] = "new claim"
        candidate["criteria"][1]["descriptor_sha256"] = "9" * 64
        amended = RECEIPTS.amend(receipt, candidate, study_sha256="a" * 64,
                                  runbook_sha256="c" * 64, amendment_sha256="4" * 64,
                                  attempts=[attempt()])
        with self.assertRaisesRegex(RECEIPTS.Refusal, "unmet-criteria:pending"):
            RECEIPTS.require_complete(amended, [attempt()])
        self.assertEqual(len(amended["versions"]), 2)

    def test_duplicate_amendment_digest_is_rejected(self):
        receipt = RECEIPTS.new(admission())
        candidate = join()
        amended = RECEIPTS.amend(receipt, candidate, study_sha256="a" * 64,
                                  runbook_sha256="c" * 64, amendment_sha256="4" * 64,
                                  attempts=[attempt()])
        with self.assertRaisesRegex(RECEIPTS.Refusal, "duplicate-amendment-digest"):
            RECEIPTS.amend(amended, candidate, study_sha256="a" * 64,
                            runbook_sha256="d" * 64, amendment_sha256="4" * 64,
                            attempts=[attempt()])

    def test_replay_selects_historical_source_without_launching(self):
        receipt = RECEIPTS.new(admission())
        calls = []
        result = RECEIPTS.replay(
            receipt, [attempt()],
            lambda value, historical_join, **_: calls.append(
                (value["attempt_id"], historical_join["runbook_sha256"])
            ),
        )
        self.assertEqual(result[0]["join_sha256"], RECEIPTS.join_digest(join()))
        self.assertEqual(calls, [("attempt-done", "b" * 64)])

    def test_wrong_source_is_rejected_before_validator(self):
        receipt = RECEIPTS.new(admission())
        calls = []
        with self.assertRaisesRegex(RECEIPTS.Refusal, "attempt-source-version"):
            RECEIPTS.replay(
                receipt, [attempt(runbook="e" * 64)],
                lambda *_args, **_kwargs: calls.append(True),
            )
        self.assertEqual(calls, [])

    def test_terminal_receipt_is_read_only_and_bound(self):
        receipt = RECEIPTS.new(admission())
        attempts = [attempt(), attempt("pending")]
        calls = []
        terminal = RECEIPTS.terminal(
            receipt, attempts, run_id="run-1",
            validator=lambda value, _join, **_: calls.append(value["attempt_id"]),
        )
        self.assertFalse(terminal["operation_ran"])
        self.assertEqual(calls, ["attempt-done", "attempt-pending"])
        RECEIPTS.validate_terminal(
            terminal, receipt, attempts,
            validator=lambda *_args, **_kwargs: None,
        )

    def test_terminal_materialises_iterable_for_count_and_replay(self):
        receipt = RECEIPTS.new(admission())
        values = iter([attempt(), attempt("pending")])
        terminal = RECEIPTS.terminal(
            receipt, values,
            validator=lambda *_args, **_kwargs: None,
        )
        self.assertEqual(terminal["attempt_count"], 2)

    def test_legacy_receipt_has_no_backfill_path(self):
        with self.assertRaisesRegex(RECEIPTS.Refusal, "receipt-schema"):
            RECEIPTS.history({"schema": "legacy"})


if __name__ == "__main__":
    unittest.main()
