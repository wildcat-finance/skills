"""Step 3: what each consumer may read, and what it can never be handed."""

from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
PILOT = PLUGIN_ROOT / "specimens/pilot"
RELEASE = PILOT / "release"
FIXTURES = PLUGIN_ROOT / "tests/fixtures"


def load():
    spec = importlib.util.spec_from_file_location("anamnesis_consumers", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anamnesis = load()


class Sandbox(unittest.TestCase):
    """A writable copy of the pilot, so a test may corrupt it."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.specimen = self.root / "pilot"
        shutil.copytree(PILOT, self.specimen)
        for path in self.specimen.rglob("*"):
            if path.is_file():
                path.chmod(0o600)
        self.release = str(self.specimen / "release")


class ElenchusView(unittest.TestCase):
    def view(self, kind="severity", value="high"):
        return anamnesis.analogues(str(RELEASE), kind, value)

    def test_the_projection_carries_no_verdict_field_a_verdict_could_fill(self):
        payload = self.view()
        self.assertIsNone(payload["verdict"])
        self.assertEqual(
            set(payload), anamnesis.ANALOGUE_FIELDS,
            "a new top-level field is where a verdict would arrive next")

    def test_no_analogue_carries_a_verification_state(self):
        forbidden = {"guarded", "unguarded", "passed", "inconclusive", "verified"}
        for analogue in self.view()["analogues"]:
            for remediation in analogue["remediations"]:
                self.assertNotIn(remediation["state"], forbidden)

    def test_the_projection_states_what_it_does_not_establish(self):
        text = self.view()["not_established"]
        self.assertIn("does not establish a cause", text)
        self.assertIn("still earn its own guard", text)

    def test_similarity_cannot_be_promoted_to_cause(self):
        """The view has no field for a cause, so there is nothing to promote."""
        payload = self.view()
        flat = json.dumps(payload)
        for word in ("cause", "caused_by", "root_cause", "because"):
            self.assertNotIn(f'"{word}"', flat)

    def test_a_remediation_carrying_a_verification_state_is_refused(self):
        """If one ever reached a remediation record, the adapter stops it."""
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "release"
            shutil.copytree(RELEASE, out)
            for path in out.rglob("*"):
                if path.is_file():
                    path.chmod(0o600)
            assertions = json.loads((out / "assertions.json").read_text())
            for assertion in assertions:
                if assertion["kind"] == "remediation":
                    assertion["state"]["value"] = "guarded"
                    break
            body = json.dumps(assertions, indent=2, sort_keys=True) + "\n"
            (out / "assertions.json").write_text(body, encoding="utf-8")
            manifest = json.loads((out / "manifest.json").read_text())
            # Keep the release self-consistent so the adapter, not verification,
            # is the thing under test.
            import hashlib
            for component in manifest["components"]:
                if component["path"] == "assertions.json":
                    component["sha256"] = hashlib.sha256(body.encode()).hexdigest()
                    component["bytes"] = len(body.encode())
            (out / "manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
            with self.assertRaises(anamnesis.Refusal) as caught:
                anamnesis.analogues(str(out), "severity", "high")
            # Either verification catches the drift or the adapter refuses the
            # state; both are correct and neither passes the verdict on.
            self.assertIn(caught.exception.code, {"A109", "A119", "A142"})

    def test_an_unknown_query_kind_is_refused(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.analogues(str(RELEASE), "vibes", "x")
        self.assertEqual(caught.exception.code, "A140")

    def test_an_empty_query_value_is_refused(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.analogues(str(RELEASE), "file", "")
        self.assertEqual(caught.exception.code, "A141")

    def test_a_query_that_matches_nothing_returns_an_empty_view(self):
        payload = self.view("native-id", "S99-R99-99")
        self.assertEqual(payload["analogues"], [])
        self.assertIsNone(payload["verdict"])

    def test_the_view_names_the_release_it_read(self):
        manifest = json.loads((RELEASE / "manifest.json").read_text())
        self.assertEqual(self.view()["release_id"], manifest["release_id"])


class SynkrisisView(unittest.TestCase):
    def view(self, rule="every public finding in the release"):
        return anamnesis.observations(str(RELEASE), rule)

    def test_the_projection_declares_its_producer(self):
        payload = self.view()
        self.assertEqual(payload["producer"], "anamnesis-synkrisis-observation/v1")
        self.assertEqual(payload["schema"], payload["producer"])

    def test_a_projection_with_another_producer_is_refused(self):
        payload = self.view()
        payload["producer"] = "promise-machine-run-observation/v1"
        payload["schema"] = "promise-machine-run-observation/v1"
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.check_projection(
                payload, anamnesis.OBSERVATION_SCHEMA, anamnesis.OBSERVATION_FIELDS)
        self.assertEqual(caught.exception.code, "A144")

    def test_a_projection_missing_the_cohort_is_refused(self):
        payload = self.view()
        del payload["cohort"]
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.check_projection(
                payload, anamnesis.OBSERVATION_SCHEMA, anamnesis.OBSERVATION_FIELDS)
        self.assertEqual(caught.exception.code, "A145")
        self.assertIn("cohort", caught.exception.message)

    def test_a_projection_with_an_extra_field_is_refused(self):
        payload = self.view()
        payload["prevalence"] = 0.42
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.check_projection(
                payload, anamnesis.OBSERVATION_SCHEMA, anamnesis.OBSERVATION_FIELDS)
        self.assertEqual(caught.exception.code, "A145")

    def test_an_unstated_cohort_rule_is_refused(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.observations(str(RELEASE), "")
        self.assertEqual(caught.exception.code, "A143")

    def test_every_count_arrives_with_its_denominators(self):
        payload = self.view()
        self.assertLessEqual(
            payload["cohort"]["included"], payload["denominators"]["findings"])
        for name in ("findings", "rounds", "rounds_with_no_findings", "submissions",
                     "remediations", "verifications", "relations"):
            self.assertIn(name, payload["denominators"])

    def test_the_projection_carries_its_exclusions_and_unknowns(self):
        manifest = json.loads((RELEASE / "manifest.json").read_text())
        payload = self.view()
        self.assertEqual(payload["exclusions"], manifest["exclusions"])
        self.assertEqual(payload["unknowns"], manifest["unknowns"])

    def test_the_projection_states_what_it_does_not_establish(self):
        self.assertIn("does not establish how common", self.view()["not_established"])

    def test_the_projection_names_the_policy_that_produced_it(self):
        manifest = json.loads((RELEASE / "manifest.json").read_text())
        payload = self.view()
        self.assertEqual(
            payload["policy"]["curation_version"], manifest["policy"]["version"])
        self.assertTrue(payload["policy"]["cohort_rule"])


class RestrictedMaterial(Sandbox):
    """Restricted data crosses neither adapter."""

    def restricted_release(self):
        policy = json.loads((self.specimen / "policy.json").read_text())
        policy["sources"][0]["rights"]["disclosure"] = "restricted"
        (self.specimen / "policy.json").write_text(
            json.dumps(policy, indent=2), encoding="utf-8")
        shutil.rmtree(self.specimen / "release")
        anamnesis._rebuild_once(str(self.specimen), self.release)
        return policy["sources"][0]["id"]

    def test_a_restricted_source_reaches_no_analogue(self):
        withheld = self.restricted_release()
        for kind, value in (("severity", "high"), ("severity", "medium"),
                            ("severity", "low")):
            payload = anamnesis.analogues(self.release, kind, value)
            for analogue in payload["analogues"]:
                self.assertNotEqual(analogue["source"], withheld)

    def test_a_restricted_source_reaches_no_cohort_member(self):
        withheld = self.restricted_release()
        payload = anamnesis.observations(self.release, "every public finding")
        for member in payload["cohort"]["members"]:
            self.assertNotIn(withheld, member)

    def test_the_withholding_is_counted_rather_than_silent(self):
        self.restricted_release()
        payload = anamnesis.observations(self.release, "every public finding")
        self.assertGreater(
            payload["denominators"]["findings_withheld_by_disclosure"], 0)

    def test_a_public_source_still_reaches_both_adapters(self):
        payload = anamnesis.observations(self.release, "every public finding")
        self.assertGreater(payload["cohort"]["included"], 0)


class DeterministicRebuild(Sandbox):
    def test_two_fresh_builds_agree_byte_for_byte(self):
        release, components = anamnesis.verify_rebuild(str(self.specimen))
        self.assertEqual(len(release), 64)
        self.assertEqual(components, 7)

    def test_the_committed_release_matches_a_fresh_build(self):
        release, _ = anamnesis.verify_rebuild(str(PILOT))
        manifest = json.loads((RELEASE / "manifest.json").read_text())
        self.assertEqual(release, manifest["release_id"])

    def test_one_changed_input_byte_changes_the_bound_digest(self):
        before, _ = anamnesis.verify_rebuild(str(self.specimen))
        source = self.specimen / "sources" / "tabularium-audit-rounds.md"
        payload = source.read_bytes() + b"\n"
        source.write_bytes(payload)
        policy = json.loads((self.specimen / "policy.json").read_text())
        import hashlib
        for entry in policy["sources"]:
            if entry["path"].endswith("tabularium-audit-rounds.md"):
                entry["sha256"] = hashlib.sha256(payload).hexdigest()
                entry["bytes"] = len(payload)
        (self.specimen / "policy.json").write_text(
            json.dumps(policy, indent=2), encoding="utf-8")
        after, _ = anamnesis.verify_rebuild(str(self.specimen))
        self.assertNotEqual(before, after)

    def test_one_changed_policy_byte_changes_the_bound_digest(self):
        before, _ = anamnesis.verify_rebuild(str(self.specimen))
        path = self.specimen / "curation-policy.json"
        policy = json.loads(path.read_text())
        policy["version"] = policy["version"] + "-b"
        path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
        after, _ = anamnesis.verify_rebuild(str(self.specimen))
        self.assertNotEqual(before, after)

    def test_a_partial_build_never_verifies(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "release"
            shutil.copytree(RELEASE, out)
            for path in out.rglob("*"):
                if path.is_file():
                    path.chmod(0o600)
            os.unlink(out / "relations.json")
            with self.assertRaises(anamnesis.Refusal) as caught:
                anamnesis.verify_release(str(out))
            self.assertEqual(caught.exception.code, "A103")

    def test_a_rebuild_into_an_occupied_directory_is_refused(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis._rebuild_once(str(self.specimen), self.release)
        self.assertEqual(caught.exception.code, "A100")


class RiskRegister(unittest.TestCase):
    """Every id the study declares is cited by the audit record."""

    def register_ids(self):
        study = (PLUGIN_ROOT / "docs/study.md").read_text(encoding="utf-8")
        block = study.split("```risk-register", 1)[1].split("```", 1)[0]
        return [line.split("|", 1)[0].strip()
                for line in block.strip().splitlines() if line.strip()]

    def audit_text(self):
        log = (PLUGIN_ROOT.parents[1] /
               "audit/rounds/fiat-anamnesis-source-bound-curation-and-release-of-a.md")
        if not log.is_file():
            self.skipTest("the audit record lives in the run's own tree")
        return log.read_text(encoding="utf-8")

    def test_the_study_declares_the_register_the_runbook_expects(self):
        ids = self.register_ids()
        self.assertEqual(len(ids), 11)
        self.assertEqual(len(set(ids)), 11)

    def test_every_register_id_is_cited_as_reviewed_or_not_applicable(self):
        text = self.audit_text()
        covered = {}
        for match in re.finditer(r"([a-z][a-z-]+)=(reviewed|not-applicable)", text):
            covered.setdefault(match.group(1), set()).add(match.group(2))
        for identifier in self.register_ids():
            with self.subTest(risk=identifier):
                self.assertIn(identifier, covered)
                self.assertTrue(covered[identifier] <= {"reviewed", "not-applicable"})

    def test_no_round_cites_an_id_the_register_does_not_declare(self):
        text = self.audit_text()
        declared = set(self.register_ids())
        for match in re.finditer(r"([a-z][a-z-]+)=(reviewed|not-applicable)", text):
            with self.subTest(cited=match.group(1)):
                self.assertIn(match.group(1), declared)

class ExpectedProjections(unittest.TestCase):
    """The committed projections are what the adapters produce today.

    Pinning them turns a silent change in either adapter into a diff a reviewer
    sees, which is the point of committing an expected output at all.
    """

    def test_the_expected_elenchus_projection_still_matches(self):
        expected = json.loads(
            (PILOT / "projections/elenchus-severity-high.json").read_text())
        actual = anamnesis.analogues(str(RELEASE), "severity", "high")
        self.assertEqual(actual, expected)

    def test_the_expected_synkrisis_projection_still_matches(self):
        expected = json.loads((PILOT / "projections/synkrisis-cohort.json").read_text())
        actual = anamnesis.observations(
            str(RELEASE), "every public finding in the release")
        self.assertEqual(actual, expected)

    def test_the_admitted_event_example_is_a_closed_stream(self):
        lines = (PILOT / "events/admit.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(lines), 3)
        for line in lines:
            event = json.loads(line)
            self.assertEqual(event["event"], "anamnesis.source.admitted")
            self.assertEqual(len(event["correlation_id"]), 16)
            self.assertIn("disclosure", event)

    def test_the_refusal_event_example_names_its_rule_and_record(self):
        lines = (PILOT / "events/refused.jsonl").read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event["event"], "anamnesis.source.refused")
        self.assertEqual(event["rule"], "A057")
        self.assertTrue(event["record"])
        self.assertEqual(len(event["correlation_id"]), 16)


if __name__ == "__main__":
    unittest.main()
