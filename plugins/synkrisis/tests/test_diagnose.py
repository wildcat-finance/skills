"""Diagnosis: deterministic rule evaluation that never strengthens evidence."""

from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from tests import support


class DiagnoseCase(unittest.TestCase):
    def setUp(self):
        self._scratch = tempfile.TemporaryDirectory()
        self.root = Path(self._scratch.name).resolve()
        self.addCleanup(self._scratch.cleanup)
        self.synkrisis = support.synkrisis()

    def refusal(self, code, callable_, *args, **kwargs):
        with self.assertRaises(self.synkrisis.Refusal) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))
        return caught.exception

    def rules(self, mutate=None):
        document = support.read_json(support.RULES)
        if mutate is not None:
            mutate(document)
        return document

    def stage_and_cohort(self, records=None, policy=None, rules=None, bindings=None):
        if records is None:
            support.copy_example_into(self.root)
            if rules is not None:
                support.write(self.root, "rules.json", support.canonical(rules))
        else:
            support.stage_pair(
                self.root, records, policy=policy, rules=rules, bindings=bindings
            )
        support.run_cohort(self.root)


class ExampleDiagnosisTests(DiagnoseCase):
    def test_example_findings_recompute_exactly(self):
        support.copy_example_into(self.root)
        support.run_cohort(self.root)
        support.run_diagnose(self.root)
        produced = support.read_json(self.root / "out/findings.json")
        expected = support.read_json(
            support.EXAMPLE / "expected" / "findings.json"
        )
        expected_ids = {item["rule_id"] for item in expected["findings"]}
        produced_ids = {item["rule_id"] for item in produced["findings"]}
        self.assertEqual(produced_ids, expected_ids)
        self.assertEqual(
            {item["fingerprint"] for item in produced["findings"]},
            {item["fingerprint"] for item in expected["findings"]},
        )

    def test_both_shipped_rules_match_the_example(self):
        self.stage_and_cohort()
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        self.assertEqual(
            [item["rule_id"] for item in findings["findings"]],
            ["late-boundary-consultation/v1", "unchanged-retry-before-handoff/v1"],
        )
        self.assertEqual(findings["refused_rules"], [])

    def test_fingerprints_survive_harmless_manifest_reordering(self):
        manifest, policy = support.stage_example(self.root)
        manifest["runs"] = list(reversed(manifest["runs"]))
        support.stage_inputs(self.root, manifest, policy)
        support.run_cohort(self.root)
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        expected = support.read_json(support.EXAMPLE / "expected" / "findings.json")
        self.assertEqual(
            {item["fingerprint"] for item in findings["findings"]},
            {item["fingerprint"] for item in expected["findings"]},
        )

    def test_findings_carry_exact_event_references(self):
        self.stage_and_cohort()
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        retry = next(
            item
            for item in findings["findings"]
            if item["rule_id"] == "unchanged-retry-before-handoff/v1"
        )
        self.assertEqual(
            retry["matched_runs"],
            [{"run_id": "run-gamma", "events": ["evt-4", "evt-7", "evt-10"]}],
        )

    def test_unknown_runs_stay_visible_in_every_finding(self):
        self.stage_and_cohort()
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        for item in findings["findings"]:
            self.assertIn("run-epsilon", item["unknown_runs"])

    def test_handoffs_name_the_owning_siblings(self):
        self.stage_and_cohort()
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        targets = {item["rule_id"]: item["handoff"]["to"] for item in findings["findings"]}
        self.assertEqual(
            targets,
            {
                "late-boundary-consultation/v1": "horos",
                "unchanged-retry-before-handoff/v1": "elenchus",
            },
        )

    def test_conflicting_pair_is_recorded_as_counterevidence(self):
        records = {
            "run-early": support.simple_record(
                "run-early", boundary_at="early", output_tokens=25
            ),
            "run-late-high": support.simple_record(
                "run-late-high", boundary_at="late", output_tokens=40
            ),
            "run-late-low": support.simple_record(
                "run-late-low", boundary_at="late", output_tokens=5
            ),
        }

        def relax(document):
            document["rules"][0]["parameters"]["pair_fraction"] = {
                "numerator": 1,
                "denominator": 2,
            }

        self.stage_and_cohort(records=records, rules=self.rules(relax))
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        late = next(
            item
            for item in findings["findings"]
            if item["rule_id"] == "late-boundary-consultation/v1"
        )
        self.assertEqual(
            late["counterevidence"],
            [
                {
                    "note": "pair where the later consultation did not record more output tokens",
                    "late_run": "run-late-low",
                    "early_run": "run-early",
                }
            ],
        )

    def test_relation_below_pair_fraction_is_refused_not_softened(self):
        records = {
            "run-early": support.simple_record(
                "run-early", boundary_at="early", output_tokens=50
            ),
            "run-late-low": support.simple_record(
                "run-late-low", boundary_at="late", output_tokens=5
            ),
        }
        self.stage_and_cohort(records=records)
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        refused = {row["rule_id"]: row["reason_code"] for row in findings["refused_rules"]}
        self.assertEqual(
            refused["late-boundary-consultation/v1"], "relation-not-met"
        )

    def test_rule_below_minimum_samples_is_refused(self):
        records = {
            "run-early": support.simple_record("run-early", boundary_at="early"),
            "run-early-2": support.simple_record("run-early-2", boundary_at="early"),
        }
        self.stage_and_cohort(records=records)
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        refused = {row["rule_id"]: row["reason_code"] for row in findings["refused_rules"]}
        self.assertEqual(
            refused["late-boundary-consultation/v1"], "below-minimum-samples"
        )

    def test_token_rule_is_refused_when_accounting_is_not_comparable(self):
        records = {
            "run-early": support.simple_record("run-early", boundary_at="early"),
            "run-late": support.simple_record(
                "run-late", boundary_at="late", accounting="other-usage"
            ),
        }
        self.stage_and_cohort(
            records=records,
            policy=support.fixture_policy(token_accounting="ignore"),
        )
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        refused = {row["rule_id"]: row["reason_code"] for row in findings["refused_rules"]}
        self.assertEqual(
            refused["late-boundary-consultation/v1"],
            "token-accounting-not-comparable",
        )

    def test_missing_required_dimension_refuses_the_rule(self):
        policy = support.fixture_policy()
        policy["dimensions"]["context.selected_skill"] = {"rule": "differ"}
        records = {
            "run-early": support.simple_record("run-early", boundary_at="early"),
            "run-late": support.simple_record("run-late", boundary_at="late"),
        }
        self.stage_and_cohort(records=records, policy=policy)
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        refused = {row["rule_id"]: row["reason_code"] for row in findings["refused_rules"]}
        self.assertEqual(
            refused["late-boundary-consultation/v1"], "missing-required-dimension"
        )


class RuleCatalogueRefusalTests(DiagnoseCase):
    def stage_with_rules(self, mutate):
        self.stage_and_cohort(rules=self.rules(mutate))

    def test_unknown_rule_field_is_refused(self):
        def mutate(document):
            document["rules"][0]["action"] = "file-an-issue"

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_unknown_rule_kind_is_refused(self):
        def mutate(document):
            document["rules"][0]["kind"] = "model-authored-review"

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_unsupported_catalogue_schema_is_refused(self):
        def mutate(document):
            document["schema"] = "synkrisis-rules/v2"

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_evidence_class_strengthening_is_refused(self):
        def mutate(document):
            document["rules"][0]["evidence_class"] = "checked"

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_causal_language_in_a_rule_is_refused(self):
        def mutate(document):
            document["rules"][0]["observed_relation_template"] = (
                "Late consultation caused the extra tokens."
            )

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_model_quality_language_in_a_rule_is_refused(self):
        def mutate(document):
            document["rules"][1]["title"] = "The smarter run retried less"

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_template_attribute_access_is_refused(self):
        def mutate(document):
            document["rules"][0]["observed_relation_template"] = (
                "{ordered.__class__} pairs held the relation"
            )

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_handoff_outside_the_named_owner_set_is_refused(self):
        def mutate(document):
            document["rules"][0]["handoff"]["to"] = "github"

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_zero_minimum_sample_count_is_refused(self):
        def mutate(document):
            document["rules"][0]["minimum_samples"] = {"late": 0}

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_improper_pair_fraction_is_refused(self):
        def mutate(document):
            document["rules"][0]["parameters"]["pair_fraction"] = {
                "numerator": 3,
                "denominator": 2,
            }

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)

    def test_duplicate_rule_id_is_refused(self):
        def mutate(document):
            document["rules"].append(copy.deepcopy(document["rules"][0]))

        self.stage_with_rules(mutate)
        self.refusal("SK011", support.run_diagnose, self.root)


class CohortBindingTests(DiagnoseCase):
    def test_tampered_cohort_digest_is_refused(self):
        self.stage_and_cohort()
        cohort = support.read_json(self.root / "out/cohort.json")
        cohort["cohort_digest"] = "0" * 64
        (self.root / "out/cohort.json").unlink()
        support.write(self.root, "out/cohort.json", support.canonical(cohort))
        self.refusal("SK012", support.run_diagnose, self.root)

    def test_dropped_cohort_run_is_refused(self):
        self.stage_and_cohort()
        cohort = support.read_json(self.root / "out/cohort.json")
        cohort["runs"] = cohort["runs"][1:]
        (self.root / "out/cohort.json").unlink()
        support.write(self.root, "out/cohort.json", support.canonical(cohort))
        self.refusal("SK012", support.run_diagnose, self.root)

    def test_record_changed_after_cohort_is_refused(self):
        self.stage_and_cohort()
        target = self.root / "records" / "run-alpha.jsonl"
        payload = target.read_bytes()
        target.write_bytes(payload.replace(b"demo-alpha", b"demo-alphb"))
        self.refusal("SK012", support.run_diagnose, self.root)

    def test_findings_never_strengthen_evidence_class(self):
        self.stage_and_cohort()
        support.run_diagnose(self.root)
        findings = support.read_json(self.root / "out/findings.json")
        self.assertTrue(findings["findings"])
        for item in findings["findings"]:
            self.assertEqual(item["evidence_class"], "inferred")

    def test_diagnose_recovers_after_rule_repair(self):
        broken = self.rules(
            lambda document: document["rules"][0].update({"evidence_class": "checked"})
        )
        self.stage_and_cohort(rules=broken)
        self.refusal("SK011", support.run_diagnose, self.root)
        (self.root / "rules.json").unlink()
        support.write(self.root, "rules.json", support.canonical(self.rules()))
        result = support.run_diagnose(self.root)
        self.assertEqual(result["findings"], 2)


if __name__ == "__main__":
    unittest.main()
