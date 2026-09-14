"""Step 9: the estate corpus is a second release under its own declared scope.

The pilot proved the path over one corpus. This one proves the scope is a
property of a policy rather than of the program: a different corpus, a
different taxonomy and a different set of bounds rebuild to their own release
id under the same code, and neither corpus can be built under the other's
scope. It also holds the estate sources to what may leave them: their
originals are named by date, section and digest, and never by location.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
WORKTREE = PLUGIN_ROOT.parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
ESTATE = PLUGIN_ROOT / "specimens/estate"
PILOT = PLUGIN_ROOT / "specimens/pilot"
RELEASE = ESTATE / "release"
SOURCES = ESTATE / "sources"

FINDINGS = 17
ROUNDS = 4
SCOPE_ID = "capture-estate-findings"
DIGEST = re.compile(r"\b[0-9a-f]{64}\b")
# What must never appear in a preserved source: a repository slug, a URL, an
# absolute or home-relative path. The originals are held by the maintainer and
# the corpus cites them by date, section and digest alone.
FORBIDDEN = (
    re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]*secret[A-Za-z0-9_.-]*", re.I),
    re.compile(r"[a-z][a-z0-9+.-]*://"),
    re.compile(r"(?<![\w.])~?/(?:Users|home|var|opt|tmp)/"),
)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


anamnesis = load("anamnesis_estate", SCRIPT)


def scratch_directory(prefix: str = "anamnesis-s9-"):
    """Transient space under the ignored top-level tmp/, which git never sees."""
    scratch = WORKTREE / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class EstateFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = read(ESTATE / "policy.json")
        self.curation = read(ESTATE / "curation-policy.json")
        self.manifest = read(RELEASE / "manifest.json")
        holder = scratch_directory()
        self.addCleanup(holder.cleanup)
        self.scratch = Path(holder.name)

    def specimen(self, name: str = "estate") -> Path:
        """A writable copy of the estate specimen, without its built release."""
        import shutil

        target = self.scratch / name
        shutil.copytree(ESTATE, target)
        shutil.rmtree(target / "release")
        shutil.rmtree(target / "projections", ignore_errors=True)
        return target


class TheEstateReleaseIsItsOwn(EstateFixture):
    def test_two_fresh_builds_agree_and_equal_the_committed_release(self) -> None:
        release_id, components = anamnesis.verify_rebuild(str(self.specimen()))
        self.assertEqual(release_id, self.manifest["release_id"])
        self.assertEqual(components, len(self.manifest["components"]) + 1)

    def test_the_committed_release_verifies_with_its_own_counts(self) -> None:
        manifest, _ = anamnesis.verify_release(str(RELEASE))
        counts = manifest["counts"]
        self.assertEqual(counts["findings"], FINDINGS)
        self.assertEqual(counts["submissions"], FINDINGS)
        self.assertEqual(counts["rounds"], ROUNDS)
        self.assertEqual(counts["engagements"], 2)
        # Neither source records a fix, so the corpus records none. `applied`
        # is as far as a status reaches and no status here reaches it.
        self.assertEqual(counts["remediations"], 0)
        self.assertEqual(counts["verifications"], ROUNDS)

    def test_the_estate_release_id_differs_from_the_pilot_s(self) -> None:
        pilot = read(PILOT / "release/manifest.json")["release_id"]
        self.assertNotEqual(self.manifest["release_id"], pilot)

    def test_the_release_declares_the_estate_scope_and_its_sources(self) -> None:
        scope = self.manifest["policy"]["scope"]
        self.assertEqual(scope["id"], SCOPE_ID)
        self.assertEqual(scope["records"], {"minimum": 10, "maximum": 40})
        self.assertEqual(
            sorted(scope["sources"]),
            sorted(source["id"] for source in self.manifest["sources"]),
        )

    def test_the_committed_projections_equal_fresh_ones(self) -> None:
        for name, fresh in (
            ("elenchus-severity-high.json",
             anamnesis.analogues(str(RELEASE), "severity", "high")),
            ("synkrisis-cohort.json",
             anamnesis.observations(str(RELEASE), "every public finding in the release")),
        ):
            with self.subTest(projection=name):
                self.assertEqual(read(ESTATE / "projections" / name), fresh)


class NeitherCorpusBuildsUnderTheOther_sScope(EstateFixture):
    def refusal(self, policy: Path, curation: Path, out: str):
        events = anamnesis.Events()
        result = anamnesis.admit(str(policy), events)
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis._admitted_within_scope(events, result, str(curation))
        return caught.exception

    def test_the_estate_sources_are_outside_the_pilot_scope(self) -> None:
        refusal = self.refusal(
            ESTATE / "policy.json", PILOT / "curation-policy.json", "a")
        self.assertEqual(refusal.code, "A074")

    def test_the_pilot_sources_are_outside_the_estate_scope(self) -> None:
        refusal = self.refusal(
            PILOT / "policy.json", ESTATE / "curation-policy.json", "b")
        self.assertEqual(refusal.code, "A074")

    def test_a_scope_source_the_estate_does_not_admit_refuses_a075(self) -> None:
        specimen = self.specimen()
        curation = read(specimen / "curation-policy.json")
        curation["scope"]["sources"].append("a-source-nobody-admitted")
        (specimen / "curation-policy.json").write_text(
            json.dumps(curation, indent=2) + "\n", encoding="utf-8")
        events = anamnesis.Events()
        result = anamnesis.admit(str(specimen / "policy.json"), events)
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis._admitted_within_scope(
                events, result, str(specimen / "curation-policy.json"))
        self.assertEqual(caught.exception.code, "A075")

    def test_seventeen_records_are_outside_the_pilot_bounds(self) -> None:
        """The estate is admissible under its own bounds and not under the pilot's."""
        pilot = read(PILOT / "curation-policy.json")["scope"]["records"]
        self.assertFalse(pilot["minimum"] <= FINDINGS <= pilot["maximum"])
        estate = self.curation["scope"]["records"]
        self.assertTrue(estate["minimum"] <= FINDINGS <= estate["maximum"])


class TheSourcesCarryTheirRightsAndNotTheirLocation(EstateFixture):
    def test_every_source_records_a_written_permission_and_public_disclosure(self) -> None:
        for source in self.policy["sources"]:
            with self.subTest(source=source["id"]):
                rights = source["rights"]
                self.assertEqual(rights["basis"], "permission")
                self.assertEqual(rights["disclosure"], "public")
                self.assertEqual(rights["holder"], "Wildcat Labs")
                self.assertTrue(rights["statement"].strip())

    def test_every_provenance_names_a_date_and_a_digest(self) -> None:
        for source in self.policy["sources"]:
            with self.subTest(source=source["id"]):
                provenance = source["provenance"]
                self.assertRegex(provenance["retrieved"], r"^\d{4}-\d{2}-\d{2}$")
                self.assertTrue(DIGEST.search(provenance["origin"]))
                self.assertTrue(provenance["origin_path"].strip())
                self.assertNotIn("origin_commit", provenance)

    def test_no_estate_byte_names_a_location(self) -> None:
        subjects = [ESTATE / "policy.json", ESTATE / "curation-policy.json"]
        subjects += sorted(SOURCES.glob("*.md"))
        for path in subjects:
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN:
                with self.subTest(path=path.name, pattern=pattern.pattern):
                    self.assertIsNone(pattern.search(text))


class TheCommittedStreamAndTheDemoDocumentAreCurrent(EstateFixture):
    """S3-R1-01 and S3-R1-02: two artefacts this specimen ships that nothing held.

    A committed event stream and a document naming one corpus both go stale in
    silence. The projections already had a guard for exactly this reason; these
    are the two the estate added.
    """

    def test_the_committed_event_stream_is_what_a_fresh_admission_writes(self) -> None:
        stream = self.scratch / "admit.jsonl"
        anamnesis.admit(str(ESTATE / "policy.json"), anamnesis.Events(str(stream)))
        fresh = [json.loads(line) for line in stream.read_text(encoding="utf-8").splitlines()]
        committed = [
            json.loads(line)
            for line in (ESTATE / "events/admit.jsonl").read_text(encoding="utf-8").splitlines()
        ]
        self.assertEqual(committed, fresh)
        self.assertEqual(len(committed), len(self.policy["sources"]))
        for event in committed:
            self.assertEqual(event["event"], "anamnesis.source.admitted")
            self.assertEqual(event["disclosure"], "public")
            self.assertEqual(len(event["correlation_id"]), 16)

    def test_the_demo_document_names_both_committed_specimens(self) -> None:
        text = (PLUGIN_ROOT / "docs/demo.md").read_text(encoding="utf-8")
        for specimen in ("specimens/pilot", "specimens/estate"):
            with self.subTest(specimen=specimen):
                self.assertIn(specimen, text)
        self.assertIn(SCOPE_ID, text)


class TheEstateTaxonomyAdmitsAnUnratedRecord(EstateFixture):
    def test_unrated_is_declared_and_nothing_is_quarantined(self) -> None:
        self.assertIn("unrated", self.curation["taxonomy"]["severities"])
        self.assertEqual(self.manifest["exclusions"], [])

    def test_a_taxonomy_without_unrated_quarantines_those_records(self) -> None:
        specimen = self.specimen("narrow")
        curation = read(specimen / "curation-policy.json")
        curation["taxonomy"]["severities"] = ["high", "medium"]
        (specimen / "curation-policy.json").write_text(
            json.dumps(curation, indent=2) + "\n", encoding="utf-8")
        manifest = anamnesis._rebuild_once(str(specimen), str(self.scratch / "narrow-out"))
        self.assertTrue(manifest["exclusions"])
        for exclusion in manifest["exclusions"]:
            self.assertEqual(exclusion["rule"], "taxonomy-drift")
        self.assertLess(manifest["counts"]["findings"], FINDINGS)


if __name__ == "__main__":
    unittest.main()
