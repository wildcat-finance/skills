"""Step 2: the graph keeps what a smaller schema would have dropped."""

from __future__ import annotations

import collections
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import pathlib
import shutil
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
FIXTURES = PLUGIN_ROOT / "tests/fixtures"
PILOT = PLUGIN_ROOT / "specimens/pilot"


def load():
    spec = importlib.util.spec_from_file_location("anamnesis_curation", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anamnesis = load()

BASE_POLICY = {
    "version": "test-v1",
    "mapper": {"name": "warden-audit-round-markdown", "version": "1"},
    "taxonomy": {"name": "warden-severity", "version": "1",
                 "severities": ["high", "medium", "low"]},
    "disclosure": {"derived_text": ["public"]},
}


class EdgeCases(unittest.TestCase):
    """Curate the synthetic record that carries the shapes the pilot lacks."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        shutil.copy(FIXTURES / "edge-cases.md", self.root / "edge-cases.md")
        self.policy_path = self.root / "policy.json"
        shutil.copy(FIXTURES / "edge-cases-policy.json", self.policy_path)
        self.admitted = anamnesis.admit(str(self.policy_path), anamnesis.Events())["sources"]
        self.text = (self.root / "edge-cases.md").read_text(encoding="utf-8")

    def graph(self, **changes):
        policy = json.loads(json.dumps(BASE_POLICY))
        policy.update(changes)
        return anamnesis.curate(self.admitted, policy, {"edge-cases": self.text})

    def by_kind(self, graph, kind):
        return [a for a in graph["assertions"] if a["kind"] == kind]

    def edges(self, graph, kind):
        return [r for r in graph["relations"] if r["kind"] == kind]


class Rounds(EdgeCases):
    def test_a_heading_that_is_not_a_round_owns_no_findings(self):
        rounds = anamnesis.parse_source(self.text, "edge-cases")
        self.assertEqual(len(rounds), 3)
        self.assertNotIn("Leads closed since", [r["label"] for r in rounds])

    def test_a_zero_finding_round_is_kept_and_counted(self):
        graph = self.graph()
        rounds = graph["engagements"][0]["rounds"]
        empty = [r for r in rounds if r["findings"] == 0]
        self.assertEqual(len(empty), 1)
        self.assertEqual(empty[0]["verdict"], "guarded")

    def test_the_round_label_and_date_are_the_source_bytes(self):
        rounds = anamnesis.parse_source(self.text, "edge-cases")
        self.assertEqual(rounds[0]["label"], "Step 1, round 1")
        self.assertEqual(rounds[0]["date"], "2026-08-20")


class LegacyFields(unittest.TestCase):
    """The pilot's real rounds predate the schema and verdict fields."""

    def setUp(self):
        self.policy = json.loads((PILOT / "policy.json").read_text(encoding="utf-8"))
        self.admitted = anamnesis.admit(str(PILOT / "policy.json"), anamnesis.Events())["sources"]
        self.texts = {
            s["id"]: (PILOT / s["path"]).read_text(encoding="utf-8")
            for s in self.policy["sources"]
        }

    def test_a_missing_legacy_field_is_unknown_and_not_none(self):
        graph = anamnesis.curate(self.admitted, BASE_POLICY, self.texts)
        rounds = [r for e in graph["engagements"] for r in e["rounds"]]
        self.assertTrue(rounds)
        self.assertTrue(all(r["native_schema"] is None for r in rounds))
        self.assertEqual(graph["unknowns"]["round.native_schema"], len(rounds))
        self.assertEqual(graph["unknowns"]["round.verdict"], len(rounds))

    def test_an_unrecorded_verdict_does_not_become_a_pass(self):
        graph = anamnesis.curate(self.admitted, BASE_POLICY, self.texts)
        states = {a["state"]["value"] for a in graph["assertions"]
                  if a["kind"] == "verification"}
        self.assertEqual(states, {"unknown"})

    def test_the_pilot_carries_zero_finding_rounds(self):
        graph = anamnesis.curate(self.admitted, BASE_POLICY, self.texts)
        rounds = [r for e in graph["engagements"] for r in e["rounds"]]
        self.assertGreater(sum(1 for r in rounds if r["findings"] == 0), 0)


class Adjudication(EdgeCases):
    def test_a_rejected_finding_keeps_its_own_state(self):
        """Rejection is a fact about the finding, not about a change."""
        graph = self.graph()
        rejected = [a for a in self.by_kind(graph, "finding")
                    if a["state"]["value"] == "rejected"]
        self.assertEqual(len(rejected), 1)
        self.assertIn("not reachable", rejected[0]["state"]["basis"])

    def test_a_rejected_finding_produces_no_remediation(self):
        graph = self.graph()
        rejected = next(a for a in self.by_kind(graph, "finding")
                        if a["state"]["value"] == "rejected")
        addressed = [r for r in self.edges(graph, "addressed-by")
                     if r["from"] == rejected["id"]]
        self.assertEqual(addressed, [])

    def test_an_accepted_risk_finding_keeps_its_own_state(self):
        graph = self.graph()
        accepted = [a for a in self.by_kind(graph, "finding")
                    if a["state"]["value"] == "accepted-risk"]
        self.assertEqual(len(accepted), 1)
        self.assertIn("costs more than the exposure", accepted[0]["state"]["basis"])

    def test_an_open_finding_is_unknown_rather_than_fixed(self):
        graph = self.graph()
        states = [a["state"]["value"] for a in self.by_kind(graph, "finding")]
        self.assertIn("unknown", states)

    def test_a_rejection_and_a_fix_in_one_round_stay_separate(self):
        """Both statuses appear in round 1; neither may absorb the other."""
        graph = self.graph()
        states = {a["native"]["native_id"]: a["state"]["value"]
                  for a in self.by_kind(graph, "finding")}
        self.assertEqual(states["S1-R1-02"], "rejected")
        self.assertEqual(states["S1-R1-03"], "accepted-risk")
        self.assertEqual(states["S1-R1-01"], "unknown")

    def test_applied_never_becomes_verified(self):
        graph = self.graph()
        for assertion in self.by_kind(graph, "remediation"):
            self.assertNotEqual(assertion["state"]["value"], "verified")


class Verification(EdgeCases):
    def test_an_unguarded_verdict_is_carried_as_unguarded(self):
        graph = self.graph()
        values = [a["state"]["value"] for a in self.by_kind(graph, "verification")]
        self.assertIn("unguarded", values)

    def test_an_inconclusive_verdict_is_carried_as_inconclusive(self):
        graph = self.graph()
        values = [a["state"]["value"] for a in self.by_kind(graph, "verification")]
        self.assertIn("inconclusive", values)

    def test_a_guarded_verdict_is_not_inferred_from_a_fix(self):
        graph = self.graph()
        guarded = [a for a in self.by_kind(graph, "verification")
                   if a["state"]["value"] == "guarded"]
        self.assertEqual(len(guarded), 1)
        self.assertEqual(guarded[0]["native"]["declared"], "guarded")


class Clusters(EdgeCases):
    def test_a_duplicate_keeps_its_submission_and_shares_one_finding(self):
        graph = self.graph(duplicates={"edge-cases:S1-R1-05": "edge-cases:S1-R1-01"})
        submissions = {a["id"] for a in self.by_kind(graph, "submission")}
        self.assertIn("sub:edge-cases:S1-R1-05", submissions)
        self.assertIn("sub:edge-cases:S1-R1-01", submissions)
        findings = {a["id"] for a in self.by_kind(graph, "finding")}
        self.assertNotIn("find:edge-cases:S1-R1-05", findings)
        self.assertIn("find:edge-cases:S1-R1-01", findings)

    def test_the_duplicate_edge_records_the_policy_that_joined_them(self):
        graph = self.graph(duplicates={"edge-cases:S1-R1-05": "edge-cases:S1-R1-01"})
        edges = self.edges(graph, "duplicate-of")
        self.assertEqual(len(edges), 1)
        self.assertEqual(edges[0]["policy_version"], "test-v1")
        self.assertEqual(edges[0]["to"], "sub:edge-cases:S1-R1-01")

    def test_without_a_policy_join_the_two_stay_separate_findings(self):
        graph = self.graph()
        findings = {a["id"] for a in self.by_kind(graph, "finding")}
        self.assertIn("find:edge-cases:S1-R1-05", findings)
        self.assertIn("find:edge-cases:S1-R1-01", findings)
        self.assertEqual(self.edges(graph, "duplicate-of"), [])

    def test_a_duplicate_of_a_duplicate_is_refused(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            self.graph(duplicates={"a": "b", "b": "c"})
        self.assertEqual(caught.exception.code, "A116")

    def test_a_duplicate_naming_itself_is_refused(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            self.graph(duplicates={"a": "a"})
        self.assertEqual(caught.exception.code, "A115")


class ManyToMany(EdgeCases):
    def test_one_finding_can_be_addressed_by_several_remediations(self):
        graph = self.graph()
        per_finding = collections.Counter(
            r["from"] for r in self.edges(graph, "addressed-by"))
        self.assertGreater(per_finding["find:edge-cases:S1-R1-01"], 1)

    def test_one_remediation_can_address_several_findings(self):
        graph = self.graph()
        per_remediation = collections.Counter(
            r["to"] for r in self.edges(graph, "addressed-by"))
        self.assertTrue(any(count > 1 for count in per_remediation.values()))

    def test_the_pilot_carries_a_real_one_fix_to_many_cluster(self):
        policy = json.loads((PILOT / "policy.json").read_text(encoding="utf-8"))
        admitted = anamnesis.admit(str(PILOT / "policy.json"), anamnesis.Events())["sources"]
        texts = {s["id"]: (PILOT / s["path"]).read_text(encoding="utf-8")
                 for s in policy["sources"]}
        graph = anamnesis.curate(admitted, BASE_POLICY, texts)
        per_remediation = collections.Counter(
            r["to"] for r in graph["relations"] if r["kind"] == "addressed-by")
        self.assertGreater(sum(1 for c in per_remediation.values() if c > 1), 0)


class Taxonomy(EdgeCases):
    def test_a_severity_outside_the_taxonomy_is_quarantined_not_mapped(self):
        graph = self.graph()
        drift = [q for q in graph["quarantine"] if q["rule"] == "taxonomy-drift"]
        self.assertEqual(len(drift), 1)
        self.assertIn("critical", drift[0]["reason"])
        ids = {a["native"].get("native_id") for a in self.by_kind(graph, "finding")}
        self.assertNotIn("S1-R1-04", ids)

    def test_widening_the_taxonomy_admits_the_same_finding(self):
        graph = self.graph(taxonomy={"name": "warden-severity", "version": "2",
                                     "severities": ["critical", "high", "medium", "low"]})
        self.assertEqual(graph["quarantine"], [])
        ids = {a["native"].get("native_id") for a in self.by_kind(graph, "finding")}
        self.assertIn("S1-R1-04", ids)


class Egress(EdgeCases):
    def test_a_restricted_source_contributes_no_derived_text(self):
        restricted = [dict(s, disclosure="restricted") for s in self.admitted]
        graph = anamnesis.curate(restricted, BASE_POLICY, {"edge-cases": self.text})
        for assertion in graph["assertions"]:
            for field in ("finding", "file", "status"):
                self.assertEqual(assertion["native"].get(field, ""), "")
        for round_entry in graph["engagements"][0]["rounds"]:
            self.assertEqual(round_entry["label"], "")

    def test_a_restricted_source_keeps_its_identifiers(self):
        restricted = [dict(s, disclosure="restricted") for s in self.admitted]
        graph = anamnesis.curate(restricted, BASE_POLICY, {"edge-cases": self.text})
        ids = {a["native"].get("native_id") for a in graph["assertions"]
               if a["kind"] == "submission"}
        self.assertIn("S1-R1-01", ids)

    def test_the_refusal_is_recorded_rather_than_silent(self):
        restricted = [dict(s, disclosure="restricted") for s in self.admitted]
        graph = anamnesis.curate(restricted, BASE_POLICY, {"edge-cases": self.text})
        rules = {q["rule"] for q in graph["quarantine"]}
        self.assertIn("restricted-derived-text", rules)

    def test_admitting_restricted_text_needs_an_explicit_policy(self):
        restricted = [dict(s, disclosure="restricted") for s in self.admitted]
        policy = json.loads(json.dumps(BASE_POLICY))
        policy["disclosure"]["derived_text"] = ["public", "restricted"]
        graph = anamnesis.curate(restricted, policy, {"edge-cases": self.text})
        findings = [a for a in graph["assertions"] if a["kind"] == "finding"]
        self.assertTrue(any(a["native"]["finding"] for a in findings))


class NativePreservation(EdgeCases):
    def test_every_assertion_carries_its_source_and_line(self):
        graph = self.graph()
        for assertion in graph["assertions"]:
            self.assertEqual(assertion["source"], "edge-cases")
            self.assertGreaterEqual(assertion["locator"]["line"], 1)

    def test_the_native_status_survives_normalisation(self):
        graph = self.graph()
        bases = [a["state"]["basis"] for a in self.by_kind(graph, "finding")]
        self.assertIn("rejected: not reachable from any caller", bases)

    def test_every_assertion_names_the_mapper_that_made_it(self):
        graph = self.graph()
        for assertion in graph["assertions"]:
            self.assertEqual(assertion["mapper"]["name"], "warden-audit-round-markdown")
            self.assertEqual(assertion["mapper"]["version"], "1")


class DeterministicIds(EdgeCases):
    def test_curating_twice_produces_identical_graphs(self):
        first = anamnesis.canonical(self.graph())
        second = anamnesis.canonical(self.graph())
        self.assertEqual(first, second)

    def test_ids_are_derived_from_the_source_not_from_order(self):
        graph = self.graph()
        ids = [a["id"] for a in graph["assertions"]]
        self.assertEqual(ids, sorted(set(ids), key=lambda i: (
            next(a["kind"] for a in graph["assertions"] if a["id"] == i), i)))
        self.assertEqual(len(ids), len(set(ids)))

    def test_a_release_id_changes_when_one_input_byte_changes(self):
        graph = self.graph()
        first = anamnesis.release_id(BASE_POLICY, self.admitted, graph)
        moved = [dict(s, sha256="0" * 64) for s in self.admitted]
        self.assertNotEqual(first, anamnesis.release_id(BASE_POLICY, moved, graph))

    def test_a_release_id_changes_when_the_policy_changes(self):
        graph = self.graph()
        first = anamnesis.release_id(BASE_POLICY, self.admitted, graph)
        other = json.loads(json.dumps(BASE_POLICY))
        other["version"] = "test-v2"
        self.assertNotEqual(first, anamnesis.release_id(other, self.admitted, graph))


class ReleaseBoundary(EdgeCases):
    def build(self, out=None):
        graph = self.graph()
        target = str(out or (self.root / "release"))
        return anamnesis.build_release(target, BASE_POLICY, self.admitted, graph), target

    def test_a_release_verifies_from_its_own_bytes(self):
        manifest, out = self.build()
        checked, bodies = anamnesis.verify_release(out)
        self.assertEqual(checked["release_id"], manifest["release_id"])
        self.assertEqual(
            set(bodies), {c["path"] for c in checked["components"]},
            "verification returns the bytes it checked, so nothing reads them twice")

    def test_an_existing_destination_is_refused(self):
        _, out = self.build()
        with self.assertRaises(anamnesis.Refusal) as caught:
            self.build(out)
        self.assertEqual(caught.exception.code, "A100")

    def test_a_tampered_component_fails_verification(self):
        _, out = self.build()
        target = Path(out) / "assertions.json"
        target.chmod(0o600)
        target.write_text(target.read_text(encoding="utf-8") + " ", encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.verify_release(out)
        self.assertIn(caught.exception.code, {"A104", "A105"})

    def edit_manifest(self, out, mutate):
        path = Path(out) / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        mutate(manifest)
        path.chmod(0o600)
        path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def refuses(self, out):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.verify_release(out)
        return caught.exception.code

    def test_a_tampered_count_fails_verification(self):
        """The manifest is not covered by its own digest, so its claims are
        checked against the components instead."""
        _, out = self.build()
        self.edit_manifest(out, lambda m: m["counts"].__setitem__(
            "findings", m["counts"]["findings"] + 1))
        self.assertEqual(self.refuses(out), "A119")

    def test_a_dropped_exclusion_fails_verification(self):
        _, out = self.build()
        self.assertTrue(json.loads(
            (Path(out) / "manifest.json").read_text(encoding="utf-8"))["exclusions"])
        self.edit_manifest(out, lambda m: m.__setitem__("exclusions", []))
        self.assertEqual(self.refuses(out), "A118")

    def test_a_dropped_unknown_fails_verification(self):
        _, out = self.build()
        self.edit_manifest(out, lambda m: m.__setitem__("unknowns", {}))
        self.assertEqual(self.refuses(out), "A123")

    def test_a_forged_policy_fails_verification(self):
        _, out = self.build()
        self.edit_manifest(out, lambda m: m["policy"].__setitem__("version", "forged"))
        self.assertEqual(self.refuses(out), "A117")

    def test_a_forged_release_id_fails_verification(self):
        _, out = self.build()
        self.edit_manifest(out, lambda m: m.__setitem__("release_id", "0" * 64))
        self.assertEqual(self.refuses(out), "A109")

    def test_a_forged_source_digest_fails_verification(self):
        _, out = self.build()
        self.edit_manifest(
            out, lambda m: m["sources"][0].__setitem__("sha256", "0" * 64))
        self.assertEqual(self.refuses(out), "A109")

    def test_an_extra_file_in_the_release_fails_verification(self):
        _, out = self.build()
        (Path(out) / "stray.json").write_text("{}", encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.verify_release(out)
        self.assertEqual(caught.exception.code, "A103")

    def test_a_missing_component_fails_verification(self):
        _, out = self.build()
        os.unlink(Path(out) / "quarantine.json")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.verify_release(out)
        self.assertEqual(caught.exception.code, "A103")

    def test_a_killed_build_leaves_no_release_and_no_staging(self):
        graph = self.graph()
        out = str(self.root / "killed")
        broken = json.loads(json.dumps(BASE_POLICY))
        broken["version"] = object  # not serialisable; fails mid-build
        with self.assertRaises(TypeError):
            anamnesis.build_release(out, broken, self.admitted, graph)
        self.assertFalse(os.path.exists(out))
        leftovers = [p for p in os.listdir(self.root) if "staging" in p]
        self.assertEqual(leftovers, [])

    def test_the_release_names_every_source_digest(self):
        manifest, _ = self.build()
        self.assertEqual(
            {s["sha256"] for s in manifest["sources"]},
            {s["sha256"] for s in self.admitted},
        )

    def test_the_release_reports_its_exclusions(self):
        manifest, _ = self.build()
        self.assertTrue(manifest["exclusions"])
        self.assertIn("taxonomy-drift", {e["rule"] for e in manifest["exclusions"]})


class ByteCap(EdgeCases):
    def test_the_pilot_release_is_within_the_cap(self):
        total = anamnesis.measure_release(str(PILOT / "release"))
        self.assertLessEqual(total, anamnesis.MAX_RELEASE_BYTES)
        self.assertEqual(anamnesis.MAX_RELEASE_BYTES, 50_000_000)

    def test_the_cap_is_the_number_the_design_record_declares(self):
        record = json.loads(
            (PLUGIN_ROOT.parents[1] / ".hexaemeron/design-evidence.json").read_text()
        ) if (PLUGIN_ROOT.parents[1] / ".hexaemeron/design-evidence.json").is_file() else None
        if record is None:
            self.skipTest("the design record is controller state and is not always present")
        threshold = next(
            (
                c["threshold"]
                for c in record["criteria"]
                if c["id"] == "seed-release-byte-cap"
            ),
            None,
        )
        if threshold is None:
            self.skipTest(
                "the design record in this worktree belongs to another Fiat run "
                "and declares no seed-release-byte-cap criterion"
            )
        self.assertEqual(anamnesis.MAX_RELEASE_BYTES, threshold)


class SourceTampering(EdgeCases):
    def test_a_changed_source_byte_is_refused_before_curation(self):
        target = self.root / "edge-cases.md"
        target.write_text(self.text + "\n", encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.admit(str(self.policy_path), anamnesis.Events())
        self.assertIn(caught.exception.code, {"A056", "A057"})

    def test_the_pilot_sources_still_match_their_declared_digests(self):
        policy = json.loads((PILOT / "policy.json").read_text(encoding="utf-8"))
        for source in policy["sources"]:
            payload = (PILOT / source["path"]).read_bytes()
            self.assertEqual(hashlib.sha256(payload).hexdigest(), source["sha256"])
            self.assertEqual(len(payload), source["bytes"])




class AdmissionToCurationBoundary(EdgeCases):
    """S2-R1-02: curation reads the files a second time and must re-check them."""

    def test_a_source_swapped_after_admission_is_refused(self):
        admitted = anamnesis.admit(str(self.policy_path), anamnesis.Events())["sources"]
        # Same length, different bytes: the byte-count check passes and the
        # digest check is the one that has to catch it.
        swapped = self.text.replace("The first finding", "The worst finding")
        self.assertEqual(len(swapped), len(self.text))
        (self.root / "edge-cases.md").write_text(swapped, encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis._admitted_texts(str(self.policy_path), admitted)
        self.assertEqual(caught.exception.code, "A121")

    def test_a_source_truncated_after_admission_is_refused(self):
        admitted = anamnesis.admit(str(self.policy_path), anamnesis.Events())["sources"]
        (self.root / "edge-cases.md").write_text("short", encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis._admitted_texts(str(self.policy_path), admitted)
        self.assertEqual(caught.exception.code, "A120")

    def test_unchanged_sources_pass_the_second_read(self):
        admitted = anamnesis.admit(str(self.policy_path), anamnesis.Events())["sources"]
        texts = anamnesis._admitted_texts(str(self.policy_path), admitted)
        self.assertEqual(texts["edge-cases"], self.text)

    def test_a_source_that_is_not_utf8_is_refused_not_traced(self):
        payload = b"## Step 1, round 1 -- 2026-08-20\n\n\xff\xfe not utf-8\n"
        target = self.root / "edge-cases.md"
        target.write_bytes(payload)
        policy = json.loads(self.policy_path.read_text(encoding="utf-8"))
        policy["sources"][0]["bytes"] = len(payload)
        policy["sources"][0]["sha256"] = hashlib.sha256(payload).hexdigest()
        self.policy_path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
        admitted = anamnesis.admit(str(self.policy_path), anamnesis.Events())["sources"]
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis._admitted_texts(str(self.policy_path), admitted)
        self.assertEqual(caught.exception.code, "A122")


class ComponentBound(EdgeCases):
    """S2-R1-03: a component is bounded by the release cap, not the source one."""

    def test_verification_bounds_a_component_by_the_release_cap(self):
        source = pathlib.Path(SCRIPT).read_text(encoding="utf-8")
        self.assertIn("MAX_RELEASE_BYTES,\n", source)
        self.assertNotIn(
            "os.path.join(out, component[\"path\"]), MAX_SOURCE_BYTES_CEILING", source)

    def test_the_release_cap_is_larger_than_the_source_ceiling(self):
        self.assertGreater(
            anamnesis.MAX_RELEASE_BYTES, anamnesis.MAX_SOURCE_BYTES_CEILING)

class HostileManifest(EdgeCases):
    """S2-R2-01: a release from elsewhere carries an untrusted manifest."""

    def setUp(self):
        super().setUp()
        graph = self.graph()
        self.out = str(self.root / "release")
        anamnesis.build_release(self.out, BASE_POLICY, self.admitted, graph)
        self.manifest_path = Path(self.out) / "manifest.json"
        self.manifest_path.chmod(0o600)

    def write(self, manifest):
        self.manifest_path.write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def load(self):
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def refuses(self):
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.verify_release(self.out)
        return caught.exception.code

    def test_a_manifest_missing_a_required_field_is_refused(self):
        self.write({"schema": "anamnesis-release/v1"})
        self.assertEqual(self.refuses(), "A012")

    def test_a_manifest_with_an_unknown_field_is_refused(self):
        manifest = self.load(); manifest["extra"] = True
        self.write(manifest)
        self.assertEqual(self.refuses(), "A011")

    def test_a_malformed_release_id_is_refused(self):
        manifest = self.load(); manifest["release_id"] = "short"
        self.write(manifest)
        self.assertEqual(self.refuses(), "A130")

    def test_components_that_are_not_a_list_are_refused(self):
        manifest = self.load(); manifest["components"] = {}
        self.write(manifest)
        self.assertEqual(self.refuses(), "A131")

    def test_a_component_named_twice_is_refused(self):
        manifest = self.load()
        manifest["components"].append(dict(manifest["components"][0]))
        self.write(manifest)
        self.assertEqual(self.refuses(), "A133")

    def test_a_malformed_component_digest_is_refused(self):
        manifest = self.load()
        manifest["components"][0]["sha256"] = "nope"
        self.write(manifest)
        self.assertEqual(self.refuses(), "A134")

    def test_a_negative_byte_count_is_refused(self):
        manifest = self.load()
        manifest["components"][0]["bytes"] = -1
        self.write(manifest)
        self.assertEqual(self.refuses(), "A135")

    def test_counts_that_are_not_an_object_are_refused(self):
        manifest = self.load(); manifest["counts"] = []
        self.write(manifest)
        self.assertEqual(self.refuses(), "A136")

    def test_exclusions_that_are_not_a_list_are_refused(self):
        manifest = self.load(); manifest["exclusions"] = {}
        self.write(manifest)
        self.assertEqual(self.refuses(), "A137")

    def test_a_component_path_escaping_the_release_is_refused(self):
        manifest = self.load()
        manifest["components"][0]["path"] = "../escape.json"
        self.write(manifest)
        self.assertIn(self.refuses(), {"A041", "A103"})

    def test_a_duplicated_manifest_key_is_refused(self):
        self.manifest_path.write_text(
            '{"schema": "anamnesis-release/v1", "schema": "anamnesis-release/v1"}',
            encoding="utf-8")
        self.assertEqual(self.refuses(), "A025")

    def test_the_untouched_release_still_verifies(self):
        checked, _ = anamnesis.verify_release(self.out)
        self.assertEqual(len(checked["components"]), 6)


if __name__ == "__main__":
    unittest.main()
