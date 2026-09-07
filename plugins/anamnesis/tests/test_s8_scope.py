"""Step 8: the corpus scope is declared in the release policy, checked both ways
against the admitted sources and the record bounds, and the pilot's committed
artefacts are the ones the tree rebuilds under it."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
WORKTREE = PLUGIN_ROOT.parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
PILOT = PLUGIN_ROOT / "specimens/pilot"
ADMISSION_POLICY = PILOT / "policy.json"
CURATION_POLICY = PILOT / "curation-policy.json"
RELEASE = PILOT / "release"
PROJECTIONS = PILOT / "projections"
LEDGER = PLUGIN_ROOT / "skills/anamnesis/DEMONSTRATION.md"
README = WORKTREE / "README.md"
DEMONSTRATIONS = WORKTREE / "scripts/demonstrations.py"
RESOLVER = PLUGIN_ROOT / "docs/corpus-scope/reports/resolve.py"
REPORTS = PLUGIN_ROOT / "docs/corpus-scope/reports"
REBUILT = "pilot-artefacts-rebuilt"
CANDIDATES = (
    "release-policy-scope",
    "admission-policy-scope",
    "permanent-seed-record",
    "widen-constant",
)

FENCE = re.compile(r"```shoggoth-demonstration\n(?P<body>.*?)\n```", re.S)
CARD = re.compile(
    r'<!-- front-door:demo skill="anamnesis" claim="anamnesis-corpus-demo" '
    r'digest="(?P<digest>[0-9a-f]{64})" -->'
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # A module defining dataclasses must be registered before it executes.
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


anamnesis = load("anamnesis_scope", SCRIPT)


def scratch_directory(prefix: str = "anamnesis-s8-"):
    """Transient space under the ignored top-level tmp/, which git never sees."""
    scratch = WORKTREE / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def committed_manifest():
    return json.loads((RELEASE / "manifest.json").read_text(encoding="utf-8"))


class PilotFixture(unittest.TestCase):
    """The pilot admitted once, its curation policy loaded once, its graph built once."""

    @classmethod
    def setUpClass(cls):
        cls.admission = anamnesis.admit(str(ADMISSION_POLICY), anamnesis.Events())
        cls.sources = cls.admission["sources"]
        cls.count = cls.admission["records"]
        cls.policy = anamnesis.load_curation_policy(str(CURATION_POLICY))
        texts = anamnesis._admitted_texts(str(ADMISSION_POLICY), cls.sources)
        cls.graph = anamnesis.curate(cls.sources, cls.policy, texts)

    def setUp(self):
        self.holder = scratch_directory()
        self.addCleanup(self.holder.cleanup)
        self.scratch = Path(self.holder.name)
        self.scope_policy = copy.deepcopy(self.policy)

    def refusal(self, call):
        with self.assertRaises(anamnesis.Refusal) as caught:
            call()
        return caught.exception

    def write_policy(self, policy):
        path = self.scratch / "curation-policy.json"
        path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
        return str(path)


class ScopeRefusals(PilotFixture):
    def test_an_admitted_source_outside_the_scope_refuses_a074(self):
        dropped = self.scope_policy["scope"]["sources"].pop()
        refusal = self.refusal(
            lambda: anamnesis.check_scope(self.scope_policy, self.sources, self.count))
        self.assertEqual(refusal.code, "A074")
        self.assertEqual(refusal.record, dropped)
        self.assertIn(self.scope_policy["scope"]["id"], refusal.message)

    def test_a_scope_source_that_was_not_admitted_refuses_a075(self):
        self.scope_policy["scope"]["sources"].append("estate-audit-rounds")
        refusal = self.refusal(
            lambda: anamnesis.check_scope(self.scope_policy, self.sources, self.count))
        self.assertEqual(refusal.code, "A075")
        self.assertEqual(refusal.record, "estate-audit-rounds")

    def test_a_record_count_outside_the_declared_bounds_refuses_a073(self):
        bounds = self.scope_policy["scope"]["records"]
        for count in (bounds["minimum"] - 1, bounds["maximum"] + 1):
            with self.subTest(count=count):
                refusal = self.refusal(
                    lambda: anamnesis.check_scope(self.scope_policy, self.sources, count))
                self.assertEqual(refusal.code, "A073")
                self.assertIn(
                    f"{bounds['minimum']} to {bounds['maximum']}", refusal.message,
                    "the refusal names the declared bounds")
        anamnesis.check_scope(self.scope_policy, self.sources, self.count)

    def test_a_malformed_scope_refuses_a076(self):
        good = self.scope_policy["scope"]
        malformed = {
            "not an object": "warden-seed-pilot",
            "unknown key": {**good, "notes": "x"},
            "missing key": {k: v for k, v in good.items() if k != "preserves"},
            "id not kebab-case": {**good, "id": "Warden Seed"},
            "id too long": {**good, "id": "a" * 65},
            "preserves empty": {**good, "preserves": ""},
            "preserves too long": {**good, "preserves": "p" * 301},
            "sources empty": {**good, "sources": []},
            "sources duplicated": {**good, "sources": good["sources"] + good["sources"][:1]},
            "source without id": {**good, "sources": good["sources"] + [""]},
            "records open": {**good, "records": {"minimum": 25}},
            "minimum zero": {**good, "records": {"minimum": 0, "maximum": 50}},
            "minimum above maximum": {**good, "records": {"minimum": 51, "maximum": 50}},
            "bound not an integer": {**good, "records": {"minimum": "25", "maximum": 50}},
            "bound a boolean": {**good, "records": {"minimum": True, "maximum": 50}},
        }
        for label, scope in malformed.items():
            with self.subTest(scope=label):
                policy = copy.deepcopy(self.scope_policy)
                policy["scope"] = scope
                refusal = self.refusal(
                    lambda: anamnesis.load_curation_policy(self.write_policy(policy)))
                self.assertEqual(refusal.code, "A076")

    def test_a_curation_policy_without_a_scope_refuses_a012(self):
        del self.scope_policy["scope"]
        refusal = self.refusal(
            lambda: anamnesis.load_curation_policy(self.write_policy(self.scope_policy)))
        self.assertEqual(refusal.code, "A012")
        self.assertIn("scope", refusal.message)

    def test_a_release_whose_sources_differ_from_its_scope_refuses_a077(self):
        """The release id still recomputes, so only the scope check can catch it."""
        for label, sources in (
            ("scope omits an admitted source", self.policy["scope"]["sources"][:-1]),
            ("scope names an unreleased source",
             self.policy["scope"]["sources"] + ["estate-audit-rounds"]),
        ):
            with self.subTest(release=label):
                policy = copy.deepcopy(self.policy)
                policy["scope"]["sources"] = sources
                out = str(self.scratch / label.replace(" ", "-"))
                anamnesis.build_release(out, policy, self.sources, self.graph)
                refusal = self.refusal(lambda: anamnesis.verify_release(out))
                self.assertEqual(refusal.code, "A077")


class ScopeInTheReleaseId(PilotFixture):
    def test_a_one_byte_change_to_any_scope_field_changes_the_release_id(self):
        base = anamnesis.release_id(self.policy, self.sources, self.graph)
        seen = {base}
        for label, change in (
            ("id", lambda s: s.__setitem__("id", s["id"] + "x")),
            ("preserves", lambda s: s.__setitem__("preserves", s["preserves"] + ".")),
            ("sources", lambda s: s["sources"].__setitem__(0, s["sources"][0] + "x")),
            ("records.minimum", lambda s: s["records"].__setitem__("minimum", s["records"]["minimum"] + 1)),
            ("records.maximum", lambda s: s["records"].__setitem__("maximum", s["records"]["maximum"] + 1)),
        ):
            with self.subTest(field=label):
                policy = copy.deepcopy(self.policy)
                change(policy["scope"])
                changed = anamnesis.release_id(policy, self.sources, self.graph)
                self.assertNotIn(changed, seen)
                seen.add(changed)


class ThePilotUnderItsDeclaredScope(PilotFixture):
    def test_the_pilot_declares_its_scope_under_the_new_policy_version(self):
        self.assertEqual(self.policy["version"], "curation-2026-09-06")
        scope = self.policy["scope"]
        self.assertEqual(scope["id"], "warden-seed-pilot")
        self.assertEqual(scope["records"], {"minimum": 25, "maximum": 50})
        self.assertEqual(set(scope["sources"]), {s["id"] for s in self.sources})
        self.assertTrue(scope["records"]["minimum"] <= self.count <= scope["records"]["maximum"])

    def test_the_pilot_rebuilds_to_the_committed_release_id(self):
        release, components = anamnesis.verify_rebuild(str(PILOT))
        manifest = committed_manifest()
        self.assertEqual(release, manifest["release_id"])
        self.assertEqual(components, 7)
        self.assertEqual(manifest["policy"]["scope"], self.policy["scope"])
        anamnesis.verify_release(str(RELEASE))

    def test_the_committed_projections_equal_fresh_ones(self):
        fresh = {
            "elenchus-severity-high.json": anamnesis.analogues(str(RELEASE), "severity", "high"),
            "synkrisis-cohort.json": anamnesis.observations(
                str(RELEASE), "every public finding in the release"),
        }
        for name, payload in fresh.items():
            with self.subTest(projection=name):
                committed = (PROJECTIONS / name).read_text(encoding="utf-8")
                self.assertEqual(json.loads(committed), payload)
                self.assertEqual(committed, json.dumps(payload, indent=2, sort_keys=True) + "\n")


class TheRebuiltCountSeesArtefactsAndNotGuards(unittest.TestCase):
    """S2-R1-01: this step's own guards quote the pilot's tokens.

    Declaring the scope moved the pilot's curation policy version, and the
    suite below pins it, so the design record's `pilot-artefacts-rebuilt` grep
    counted a test file and reran to 8 against the recorded 7. The study
    enumerates the seven pilot artefacts the criterion counts; a guard that
    pins a value is no more one of them than the study copy under `docs`. The
    regression lives here rather than only in the step 7 suite, because this
    step's runner contract runs this one.
    """

    def recorded(self, candidate: str):
        report = REPORTS / f"{candidate}-{REBUILT}.json"
        return json.loads(report.read_text(encoding="utf-8"))["value"]

    def test_the_resolver_excludes_this_plugin_s_docs_and_tests(self) -> None:
        source = RESOLVER.read_text(encoding="utf-8")
        for excluded in ("plugins/anamnesis/docs", "plugins/anamnesis/tests"):
            with self.subTest(excluded=excluded):
                self.assertIn(f'":(exclude){excluded}"', source)

    def test_every_rebuilt_count_reruns_to_its_recorded_value(self) -> None:
        holder = scratch_directory()
        self.addCleanup(holder.cleanup)
        for candidate in CANDIDATES:
            out = Path(holder.name) / f"{candidate}.json"
            with self.subTest(candidate=candidate):
                completed = subprocess.run(
                    [sys.executable, str(RESOLVER), candidate, REBUILT, "--out", str(out)],
                    cwd=WORKTREE, capture_output=True, text=True,
                )
                self.assertEqual(completed.returncode, 0, completed.stderr)
                self.assertEqual(
                    json.loads(completed.stdout)["value"], self.recorded(candidate))

    def test_a_guard_quoting_a_pilot_token_is_not_counted(self) -> None:
        """The condition that produced the finding, held directly."""
        version = json.loads(CURATION_POLICY.read_text(encoding="utf-8"))["version"]
        listed = subprocess.run(
            ["git", "grep", "-l", "-F", version, "--", "plugins/anamnesis"],
            cwd=WORKTREE, capture_output=True, text=True,
        ).stdout.split()
        self.assertIn("plugins/anamnesis/tests/test_s8_scope.py", listed)
        self.assertEqual(self.recorded("release-policy-scope"), 7)


class TheBoundLeftTheProgram(unittest.TestCase):
    def test_seed_scope_and_the_literal_bound_are_gone(self):
        self.assertFalse(hasattr(anamnesis, "seed_scope"))
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertNotIn("seed_scope", source)
        self.assertNotIn("25 <= record_count <= 50", source)
        self.assertIsNone(
            re.search(r"\b\d+\s*<=\s*record_count\s*<=\s*\d+", source),
            "a record bound belongs in the curation policy, never in the program")


class TheLedgerAndTheCardArePinned(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ledger = LEDGER.read_text(encoding="utf-8")
        cls.record = json.loads(FENCE.search(cls.ledger).group("body"))
        cls.release_id = committed_manifest()["release_id"]

    def test_the_ledger_names_the_current_program_and_admission_policy_digests(self):
        by_id = {source["id"]: source for source in self.record["sources"]}
        self.assertEqual(by_id["program"]["path"], SCRIPT.relative_to(WORKTREE).as_posix())
        self.assertEqual(by_id["input"]["path"], ADMISSION_POLICY.relative_to(WORKTREE).as_posix())
        for source in self.record["sources"]:
            with self.subTest(source=source["id"]):
                digest = hashlib.sha256((WORKTREE / source["path"]).read_bytes()).hexdigest()
                self.assertEqual(source["sha256"], digest)

    def test_the_observation_lines_carry_the_committed_release_id(self):
        observations = self.record["observations"]
        self.assertIn(self.release_id, observations[0])
        self.assertIn(f"cohort:{self.release_id[:16]}", observations[3])
        for line in observations[1:3]:
            self.assertNotIn("cohort:", line)

    def test_the_root_card_digest_equals_the_record_digest(self):
        demonstrations = load("demonstrations_for_scope", DEMONSTRATIONS)
        card = CARD.search(README.read_text(encoding="utf-8"))
        self.assertIsNotNone(card, "the root README carries the anamnesis demo card")
        self.assertEqual(card.group("digest"), demonstrations.record_digest(self.record))


if __name__ == "__main__":
    unittest.main()
