"""Cohort construction: one declared universe, one policy, fail-closed checks."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests import support


class CohortCase(unittest.TestCase):
    def setUp(self):
        self._scratch = tempfile.TemporaryDirectory()
        self.root = Path(self._scratch.name).resolve()
        self.addCleanup(self._scratch.cleanup)
        self.synkrisis = support.synkrisis()

    def refusal(self, code, callable_, *args, **kwargs):
        with self.assertRaises(self.synkrisis.Refusal) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))
        self.assertTrue(caught.exception.recovery)
        return caught.exception


class ExampleCohortTests(CohortCase):
    def test_example_cohort_recomputes_deterministically(self):
        support.copy_example_into(self.root)
        first = support.run_cohort(self.root, out="out/first.json")
        second = support.run_cohort(self.root, out="out/second.json")
        self.assertEqual(first["cohort_digest"], second["cohort_digest"])
        self.assertEqual(
            (self.root / "out/first.json").read_bytes(),
            (self.root / "out/second.json").read_bytes(),
        )

    def test_example_dispositions_are_complete_and_reasoned(self):
        support.copy_example_into(self.root)
        support.run_cohort(self.root)
        cohort = support.read_json(self.root / "out/cohort.json")
        by_run = {row["run_id"]: row for row in cohort["runs"]}
        self.assertEqual(len(by_run), 5)
        self.assertEqual(by_run["run-delta"]["disposition"], "excluded")
        self.assertEqual(by_run["run-delta"]["policy_field"], "context.selected_skill")
        self.assertEqual(by_run["run-epsilon"]["disposition"], "unknown")
        self.assertEqual(by_run["run-epsilon"]["reason_code"], "binding-unavailable")
        self.assertEqual(
            sorted(cohort["included"]), ["run-alpha", "run-beta", "run-gamma"]
        )

    def test_refused_transition_run_is_retained_in_the_cohort(self):
        records = {
            "run-ok": support.simple_record("run-ok", boundary_at="early"),
            "run-refused": support.simple_record("run-refused", status="refused"),
        }
        support.stage_pair(self.root, records)
        result = support.run_cohort(self.root)
        self.assertEqual(result["included"], 2)

    def test_unknown_run_cannot_satisfy_inclusion(self):
        payload = support.simple_record("run-gap")
        support.stage_pair(
            self.root,
            {"run-gap": payload, "run-ok": support.simple_record("run-ok")},
            bindings={
                "run-gap": {
                    "status": "unavailable",
                    "reason": "observer reported no selected receipt",
                }
            },
        )
        support.run_cohort(self.root)
        cohort = support.read_json(self.root / "out/cohort.json")
        self.assertIn("run-gap", cohort["unknown"])
        self.assertNotIn("run-gap", cohort["included"])
        by_run = {row["run_id"]: row for row in cohort["runs"]}
        self.assertEqual(by_run["run-gap"]["reason_code"], "binding-unavailable")

    def test_committed_expected_cohort_recomputes_byte_identically(self):
        import os

        scratch = f"build/synkrisis-cohort-test-{os.getpid()}"
        out = f"{scratch}/cohort.json"
        self.addCleanup(support.clean_tree, support.REPO_ROOT / scratch)
        support.run_cohort(
            support.REPO_ROOT,
            manifest="plugins/synkrisis/examples/cross-run-v0/manifest.json",
            policy="plugins/synkrisis/examples/cross-run-v0/policy.json",
            out=out,
        )
        expected = (support.EXAMPLE / "expected" / "cohort.json").read_bytes()
        self.assertEqual((support.REPO_ROOT / out).read_bytes(), expected)

    def test_token_accounting_identity_is_recorded_not_assumed(self):
        support.stage_pair(self.root, {"run-a": support.simple_record("run-a")})
        support.run_cohort(self.root)
        cohort = support.read_json(self.root / "out/cohort.json")
        self.assertEqual(cohort["token_accounting"]["mode"], "require-equal")
        self.assertEqual(cohort["token_accounting"]["accounting_ids"], ["demo-host-usage"])


class ManifestRefusalTests(CohortCase):
    def test_unsupported_producer_contract_is_refused(self):
        manifest = support.fixture_manifest(
            [
                support.manifest_row(
                    "run-a", "records/run-a.jsonl", support.simple_record("run-a")
                )
            ]
        )
        manifest["producer_contract"] = "another-producer/v9"
        support.write(self.root, "records/run-a.jsonl", support.simple_record("run-a"))
        support.stage_inputs(self.root, manifest, support.fixture_policy())
        self.refusal("SK008", support.run_cohort, self.root)

    def test_missing_validation_status_is_refused(self):
        payload = support.simple_record("run-a")
        row = support.manifest_row("run-a", "records/run-a.jsonl", payload)
        row["validation"]["status"] = "refused"
        support.write(self.root, "records/run-a.jsonl", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        self.refusal("SK008", support.run_cohort, self.root)

    def test_failed_redaction_status_is_refused(self):
        payload = support.simple_record("run-a")
        row = support.manifest_row("run-a", "records/run-a.jsonl", payload)
        row["redaction"]["status"] = "gap"
        support.write(self.root, "records/run-a.jsonl", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        self.refusal("SK008", support.run_cohort, self.root)

    def test_duplicate_run_id_is_refused(self):
        payload = support.simple_record("run-a")
        rows = [
            support.manifest_row("run-a", "records/run-a.jsonl", payload),
            support.manifest_row("run-a", "records/run-b.jsonl", payload),
        ]
        support.write(self.root, "records/run-a.jsonl", payload)
        support.write(self.root, "records/run-b.jsonl", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest(rows), support.fixture_policy()
        )
        self.refusal("SK004", support.run_cohort, self.root)

    def test_absolute_record_path_is_refused(self):
        payload = support.simple_record("run-a")
        row = support.manifest_row("run-a", "/etc/hosts", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        self.refusal("SK001", support.run_cohort, self.root)

    def test_parent_traversal_record_path_is_refused(self):
        payload = support.simple_record("run-a")
        row = support.manifest_row("run-a", "../outside.jsonl", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        self.refusal("SK001", support.run_cohort, self.root)

    def test_empty_run_universe_is_refused(self):
        support.stage_inputs(
            self.root, support.fixture_manifest([]), support.fixture_policy()
        )
        self.refusal("SK004", support.run_cohort, self.root)

    def test_run_count_over_the_ceiling_is_refused(self):
        payload = support.simple_record("run-a")
        rows = [
            support.manifest_row(f"run-{index:03d}", f"records/{index}.jsonl", payload)
            for index in range(101)
        ]
        support.stage_inputs(
            self.root, support.fixture_manifest(rows), support.fixture_policy()
        )
        self.refusal("SK002", support.run_cohort, self.root)

    def test_per_file_byte_ceiling_is_refused(self):
        oversized = b"\n" * (self.synkrisis.MAX_FILE_BYTES + 1)
        row = support.manifest_row("run-a", "records/run-a.jsonl", oversized)
        support.write(self.root, "records/run-a.jsonl", oversized)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        self.refusal("SK002", support.run_cohort, self.root)

    def test_event_ceiling_is_refused(self):
        payload = support.simple_record("run-a")
        support.stage_pair(self.root, {"run-a": payload})
        original = self.synkrisis.MAX_EVENTS
        self.synkrisis.MAX_EVENTS = 3
        self.addCleanup(setattr, self.synkrisis, "MAX_EVENTS", original)
        self.refusal("SK002", support.run_cohort, self.root)


class RecordRefusalTests(CohortCase):
    def stage_single(self, payload, binding=None):
        row = support.manifest_row("run-a", "records/run-a.jsonl", payload, binding=binding)
        support.write(self.root, "records/run-a.jsonl", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        return row

    def test_replaced_record_bytes_are_refused(self):
        payload = support.simple_record("run-a")
        self.stage_single(payload)
        support.write(
            self.root, "records/run-a.jsonl", support.simple_record("run-a", output_tokens=99)
        )
        self.refusal("SK007", support.run_cohort, self.root)

    def test_truncated_record_is_refused(self):
        payload = support.simple_record("run-a")
        self.stage_single(payload)
        support.write(self.root, "records/run-a.jsonl", payload[: len(payload) // 2])
        self.refusal("SK007", support.run_cohort, self.root)

    def test_bound_prefix_digest_mismatch_is_refused(self):
        payload = support.simple_record("run-a")
        binding = {
            "status": "bound",
            "receipt": "fixture-receipt",
            "bound_bytes": len(payload),
            "bound_events": payload.count(b"\n"),
            "sha256": "0" * 64,
        }
        self.stage_single(payload, binding=binding)
        self.refusal("SK009", support.run_cohort, self.root)

    def test_bound_prefix_event_count_mismatch_is_refused(self):
        payload = support.simple_record("run-a")
        binding = {
            "status": "bound",
            "receipt": "fixture-receipt",
            "bound_bytes": len(payload),
            "bound_events": payload.count(b"\n") + 1,
            "sha256": support.sha256(payload),
        }
        self.stage_single(payload, binding=binding)
        self.refusal("SK009", support.run_cohort, self.root)

    def test_record_with_wrong_run_id_is_refused(self):
        payload = support.simple_record("run-b")
        self.stage_single(payload)
        self.refusal("SK006", support.run_cohort, self.root)

    def test_duplicate_json_key_is_refused(self):
        payload = support.simple_record("run-a")
        first_line, rest = payload.split(b"\n", 1)
        poisoned = first_line[:-1] + b',"type":"run.started"}\n' + rest
        self.stage_single(poisoned)
        self.refusal("SK003", support.run_cohort, self.root)

    def test_record_without_trailing_newline_is_refused(self):
        payload = support.simple_record("run-a")[:-1]
        self.stage_single(
            payload,
            binding={"status": "unavailable", "reason": "fixture without a receipt"},
        )
        self.refusal("SK006", support.run_cohort, self.root)

    def test_event_order_fault_is_refused(self):
        lines = support.simple_record("run-a").split(b"\n")[:-1]
        reordered = b"\n".join([lines[0], lines[2], lines[1], *lines[3:]]) + b"\n"
        self.stage_single(reordered)
        self.refusal("SK006", support.run_cohort, self.root)

    def test_record_without_closing_event_is_refused(self):
        lines = support.simple_record("run-a").split(b"\n")[:-1]
        headless = b"\n".join(lines[:-1]) + b"\n"
        self.stage_single(headless)
        self.refusal("SK006", support.run_cohort, self.root)

    def test_missing_record_file_is_refused(self):
        payload = support.simple_record("run-a")
        row = support.manifest_row("run-a", "records/run-a.jsonl", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        self.refusal("SK001", support.run_cohort, self.root)


class PolicyRefusalTests(CohortCase):
    def test_unclassified_dimension_is_refused(self):
        policy = support.fixture_policy()
        del policy["dimensions"]["context.step"]
        support.stage_pair(
            self.root, {"run-a": support.simple_record("run-a")}, policy=policy
        )
        self.refusal("SK005", support.run_cohort, self.root)

    def test_unknown_dimension_rule_is_refused(self):
        policy = support.fixture_policy()
        policy["dimensions"]["context.step"] = {"rule": "similar"}
        support.stage_pair(
            self.root, {"run-a": support.simple_record("run-a")}, policy=policy
        )
        self.refusal("SK005", support.run_cohort, self.root)

    def test_match_rule_without_expected_value_is_refused(self):
        policy = support.fixture_policy()
        policy["dimensions"]["context.role"] = {"rule": "match"}
        support.stage_pair(
            self.root, {"run-a": support.simple_record("run-a")}, policy=policy
        )
        self.refusal("SK005", support.run_cohort, self.root)

    def test_policy_leaving_no_eligible_run_is_refused(self):
        policy = support.fixture_policy()
        policy["dimensions"]["context.selected_skill"] = {
            "rule": "match",
            "value": "warden",
        }
        support.stage_pair(
            self.root, {"run-a": support.simple_record("run-a")}, policy=policy
        )
        self.refusal("SK010", support.run_cohort, self.root)

    def test_unlike_token_accounting_is_refused(self):
        support.stage_pair(
            self.root,
            {
                "run-a": support.simple_record("run-a"),
                "run-b": support.simple_record("run-b", accounting="other-usage"),
            },
        )
        self.refusal("SK010", support.run_cohort, self.root)

    def test_unlike_accounting_passes_when_policy_ignores_tokens(self):
        support.stage_pair(
            self.root,
            {
                "run-a": support.simple_record("run-a"),
                "run-b": support.simple_record("run-b", accounting="other-usage"),
            },
            policy=support.fixture_policy(token_accounting="ignore"),
        )
        result = support.run_cohort(self.root)
        self.assertEqual(result["included"], 2)


class OutputDisciplineTests(CohortCase):
    def test_no_partial_output_survives_a_refusal(self):
        payload = support.simple_record("run-a")
        row = support.manifest_row("run-a", "records/run-a.jsonl", payload)
        row["validation"]["status"] = "refused"
        support.write(self.root, "records/run-a.jsonl", payload)
        support.stage_inputs(
            self.root, support.fixture_manifest([row]), support.fixture_policy()
        )
        self.refusal("SK008", support.run_cohort, self.root)
        self.assertFalse((self.root / "out/cohort.json").exists())

    def test_existing_output_with_different_bytes_is_refused(self):
        support.stage_pair(self.root, {"run-a": support.simple_record("run-a")})
        support.write(self.root, "out/cohort.json", b"{}\n")
        self.refusal("SK013", support.run_cohort, self.root)

    def test_rerun_over_identical_output_stays_clean(self):
        support.stage_pair(self.root, {"run-a": support.simple_record("run-a")})
        first = support.run_cohort(self.root)
        second = support.run_cohort(self.root)
        self.assertEqual(first["cohort_digest"], second["cohort_digest"])

    def test_refusal_names_recovery_and_reruns_clean(self):
        payload = support.simple_record("run-a")
        row = support.manifest_row("run-a", "records/run-a.jsonl", payload)
        row["validation"]["status"] = "refused"
        support.write(self.root, "records/run-a.jsonl", payload)
        manifest = support.fixture_manifest([row])
        support.stage_inputs(self.root, manifest, support.fixture_policy())
        refusal = self.refusal("SK008", support.run_cohort, self.root)
        self.assertIn("accepted", refusal.recovery)
        row["validation"]["status"] = "accepted"
        (self.root / "manifest.json").unlink()
        support.write(self.root, "manifest.json", support.canonical(manifest))
        result = support.run_cohort(self.root)
        self.assertEqual(result["included"], 1)

    def test_cohort_keeps_the_unknown_run_out_of_every_sample(self):
        """The nearest overclaim: an unknown observer quietly counted as data."""
        support.stage_pair(
            self.root,
            {
                "run-a": support.simple_record("run-a"),
                "run-b": support.simple_record("run-b"),
            },
            bindings={
                "run-b": {"status": "unavailable", "reason": "observer unavailable"}
            },
        )
        support.run_cohort(self.root)
        cohort = support.read_json(self.root / "out/cohort.json")
        self.assertEqual(cohort["included"], ["run-a"])
        self.assertEqual(cohort["unknown"], ["run-b"])


if __name__ == "__main__":
    unittest.main()
