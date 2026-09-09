"""Step 11: the declared mapper selects the implementation that reads a source.

Before this step the curation policy's `mapper` was decoration. A release built
from the estate specimen under a policy declaring
`{"name": "a-mapper-that-does-not-exist", "version": "9"}` exited 0 at the
parent commit `f0ef9266`, produced 17 findings, wrote that name into all 55
assertions and into the manifest's recorded policy, and released
`8bae874752c55b9f2dde2c12a1ef15eed15052e29de2d459cb3aaf1e21b50dc0` rather than
the estate's shipped `509239765f9fa2db`. The release id hashes the canonical
curation policy, so the false name was hashed into the corpus identity: every
record in that release said which implementation made it, and nothing had
checked.

The fixture below is that exact policy. The guard runs it against the current
tree and requires a refusal before any record exists.

Two things this suite does not establish. It does not establish that the
registry is unwritable after import; runbook step 3 owns `registry-mutability`.
And it does not establish that any second format is readable; step 2 owns the
synopsis mapper.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
WORKTREE = PLUGIN_ROOT.parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
RUNNER = PLUGIN_ROOT / "tests/elenchus.py"
FIXTURE = PLUGIN_ROOT / "tests/fixtures/unknown-mapper-policy.json"

# The receipted bytes of the three documents this step commits. A digest here
# and the comparison against `.hexaemeron/` below say the same thing; only this
# one can still say it once the run worktree is gone.
PINNED_DIGESTS = {
    PLUGIN_ROOT / "docs/resolved-mapper-study.md":
        "52f6a11247782d6c6cdd537fa70f08809e197ecc6645f6a0416bbfe09806db06",
    PLUGIN_ROOT / "docs/resolved-mapper-runbook.md":
        "d666a6e7b864ef944c9db645bdf870d8a57dd621d18e67f8b6cd7413a1be9e19",
    PLUGIN_ROOT / "docs/resolved-mapper/design-evidence.json":
        "36170cc03cbd3ce3fab6b4d0ae2cec31bcc2f2024ba5ad397881a17815e54228",
}

PILOT = PLUGIN_ROOT / "specimens/pilot"
ESTATE = PLUGIN_ROOT / "specimens/estate"

RECORD_HOME = PLUGIN_ROOT / "docs/resolved-mapper"
RECORD = RECORD_HOME / "design-evidence.json"
REPORTS = RECORD_HOME / "reports"
RESOLVER = REPORTS / "resolve.py"
STUDY = PLUGIN_ROOT / "docs/resolved-mapper-study.md"
RUNBOOK = PLUGIN_ROOT / "docs/resolved-mapper-runbook.md"
RUN_STUDY = WORKTREE / ".hexaemeron/study.md"
RUN_RUNBOOK = WORKTREE / ".hexaemeron/runbook.md"

SELECTED = "registry-and-synopsis-mapper"
SELECTION_RULE = "unique-frontier"
CANDIDATES = (
    SELECTED,
    "registry-and-red-team-mapper",
    "registry-only",
    "per-source-mapper",
)
CONCERNS = {"correctness", "time", "space", "compatibility", "recovery"}
CONFORMANCE = "second-corpus-rebuilds-deterministically"
SCHEMA_GATE = "second-format-declares-its-own-schema"
POLICIES_GATE = "shipped-release-policies-changed"
PENDING_REPORT = f"reports/{SELECTED}-{CONFORMANCE}.json"
STEPS = tuple(range(1, 15))

# The registry entry both shipped corpora declare, and the shipped release ids
# that move if a resolved entry is not byte-identical to the declaration.
DECLARED = {"name": "warden-audit-round-markdown", "version": "1"}
PILOT_RELEASE = "41d640fb168049d5061e12c9d7282dafad2266343eeb0be2a078db8797c0bfbf"
ESTATE_RELEASE = "509239765f9fa2db782d3bc70fadea3b05411fc0638402fe5e0a43882f0063e3"

# What the parent commit did with the fixture below, recorded here because the
# guard's whole claim is a change in that behaviour.
PARENT_RELEASE = "8bae874752c55b9f2dde2c12a1ef15eed15052e29de2d459cb3aaf1e21b50dc0"
PARENT_FINDINGS = 17
PARENT_ASSERTIONS = 55

RULE = "A078"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


anamnesis = load("anamnesis_registry", SCRIPT)
runner = load("anamnesis_step_runner", RUNNER)


def scratch_directory(prefix: str = "anamnesis-s11-"):
    """Transient space under the ignored top-level tmp/, which git never sees."""
    scratch = WORKTREE / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


class Fixture(unittest.TestCase):
    def setUp(self) -> None:
        holder = scratch_directory()
        self.addCleanup(holder.cleanup)
        self.scratch = Path(holder.name)

    def copy_specimen(self, shipped: Path) -> Path:
        """A writable copy of a shipped specimen, without its built release."""
        target = self.scratch / shipped.name
        shutil.copytree(shipped, target)
        shutil.rmtree(target / "release")
        shutil.rmtree(target / "projections", ignore_errors=True)
        return target


class TheCommittedDesignRecordIsWhatTheRunSelected(unittest.TestCase):
    """The Protasis scaffolding, held at the home the step 4 ledger row cites.

    A design record that lives only in a run directory is deleted with the run
    worktree. These checks hold the committed copies, so the selection stays
    checkable from the repository alone.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.record = read(RECORD)
        cls.criteria = {entry["id"]: entry for entry in cls.record["criteria"]}
        cls.resolved = [
            cell for cell in cls.record["results"] if cell["state"] != "pending"
        ]
        cls.pending = [
            cell for cell in cls.record["results"] if cell["state"] == "pending"
        ]

    def test_the_record_is_one_closed_v1_object_over_four_candidates(self) -> None:
        self.assertEqual(self.record["schema"], "protasis-design-evidence/v1")
        self.assertEqual(
            sorted(entry["id"] for entry in self.record["candidates"]),
            sorted(CANDIDATES),
        )
        self.assertEqual(len(self.criteria), 9)
        self.assertEqual(
            CONCERNS, {entry["concern"] for entry in self.record["criteria"]})

    def test_the_selection_is_the_synopsis_mapper_under_unique_frontier(self) -> None:
        self.assertEqual(self.record["selection"]["candidate"], SELECTED)
        self.assertEqual(self.record["selection"]["rule"], SELECTION_RULE)
        failed = {
            cell["candidate"]
            for cell in self.resolved
            if cell["state"] == "fail"
        }
        self.assertNotIn(SELECTED, failed)
        self.assertEqual(len(failed), 3)

    def test_each_rejected_candidate_fails_exactly_its_one_gate(self) -> None:
        expected = {
            "registry-and-red-team-mapper": {SCHEMA_GATE},
            "registry-only": {SCHEMA_GATE},
            "per-source-mapper": {POLICIES_GATE},
        }
        for candidate, gates in expected.items():
            with self.subTest(candidate=candidate):
                self.assertEqual(
                    {
                        cell["criterion"]
                        for cell in self.resolved
                        if cell["candidate"] == candidate and cell["state"] == "fail"
                    },
                    gates,
                )
        # The compatibility gate the general mechanism fails, measured: both
        # shipped curation policies change their canonical bytes, and the
        # release id hashes that policy.
        measured = read(REPORTS / f"per-source-mapper-{POLICIES_GATE}.json")
        self.assertEqual(measured["value"], 2)

    def test_every_resolved_cell_names_a_committed_report_that_exited_zero(self) -> None:
        self.assertEqual(len(self.resolved), 32)
        for cell in self.resolved:
            with self.subTest(candidate=cell["candidate"], criterion=cell["criterion"]):
                report = cell["report"]
                body = (RECORD_HOME / report["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(), report["sha256"])
                payload = json.loads(body.decode("utf-8"))
                self.assertEqual(payload["exit"], 0)
                self.assertEqual(payload["candidate"], cell["candidate"])
                self.assertEqual(payload["criterion"], cell["criterion"])
                self.assertIn("reports/resolve.py", payload["command"])
        # The command names the run's copy of the resolver. The committed copy
        # beside these reports is that file, byte for byte, so the reports stay
        # reproducible from the repository after the run worktree is gone.
        self.assertTrue(RESOLVER.exists())
        run_copy = WORKTREE / ".hexaemeron/reports/resolve.py"
        if run_copy.exists():
            self.assertEqual(RESOLVER.read_bytes(), run_copy.read_bytes())

    def test_the_four_pending_cells_block_step_three_and_name_a_resolver(self) -> None:
        self.assertEqual(len(self.pending), 4)
        self.assertEqual(
            sorted(cell["candidate"] for cell in self.pending), sorted(CANDIDATES))
        for cell in self.pending:
            with self.subTest(candidate=cell["candidate"]):
                self.assertEqual(cell["criterion"], CONFORMANCE)
                self.assertEqual(cell["blocks"], "step:3")
                self.assertTrue(cell["resolver"].strip())
                self.assertTrue(cell["report"].startswith("reports/"))
        selected = next(
            cell for cell in self.pending if cell["candidate"] == SELECTED)
        self.assertEqual(selected["report"], PENDING_REPORT)
        # Due by the step:3 transition, which the controller checks at step 2's
        # push, so step 2 wrote the selected candidate's report. The three
        # rejected candidates keep theirs unresolved: each already failed a
        # selection gate, and a candidate nothing was built from owes no
        # conformance evidence.
        self.assertTrue((RECORD_HOME / PENDING_REPORT).exists())
        for cell in self.pending:
            if cell["candidate"] == SELECTED:
                continue
            with self.subTest(candidate=cell["candidate"]):
                self.assertFalse((RECORD_HOME / cell["report"]).exists())

    def test_the_committed_documents_match_their_pinned_digests(self) -> None:
        """The byte-identity claim, checked where there is no controller.

        The comparison below reads `.hexaemeron/`, which exists only inside the
        run's own worktree, so it skipped everywhere else and skipped in CI. A
        claim nothing checks after the worktree is archived is not a claim. The
        digests are the same bytes the controller receipted, recorded here so
        the check survives the run. Step 4 re-syncs the documents after any
        amendment and moves these three values with them.
        """
        for path, digest in PINNED_DIGESTS.items():
            with self.subTest(document=path.name):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), digest)

    def test_the_committed_documents_equal_the_run_artefacts(self) -> None:
        """And where the controller is present, that the pins track it."""
        for committed, artefact in ((STUDY, RUN_STUDY), (RUNBOOK, RUN_RUNBOOK)):
            with self.subTest(document=committed.name):
                if not artefact.exists():
                    self.skipTest(f"{artefact} is not in this checkout")
                self.assertEqual(committed.read_bytes(), artefact.read_bytes())

    def test_the_step_runner_admits_every_step_from_one_to_fourteen(self) -> None:
        self.assertEqual(runner.STEPS, STEPS)
        source = RUNNER.read_text(encoding="utf-8")
        self.assertIn("STEPS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14)", source)


class AnUnresolvedMapperRefusesBeforeAnythingIsWritten(Fixture):
    """The failure in hand, run against its own policy.

    `unresolved-mapper-writes-records` in the study's risk register: the
    refusal must land between reading the declaration and the first assertion,
    so no assertion, quarantine entry or release directory ever exists.
    """

    def refusal(self, events, curation: Path):
        result = anamnesis.admit(str(ESTATE / "policy.json"), events)
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis._admitted_within_scope(events, result, str(curation))
        return caught.exception

    def test_curate_refuses_the_rule_and_returns_no_graph(self) -> None:
        policy = read(FIXTURE)
        events = anamnesis.Events()
        result = anamnesis.admit(str(ESTATE / "policy.json"), events)
        texts = anamnesis._admitted_texts(
            str(ESTATE / "policy.json"), result["sources"])
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.curate(result["sources"], policy, texts)
        self.assertEqual(caught.exception.code, RULE)
        self.assertIn("a-mapper-that-does-not-exist", caught.exception.message)

    def test_ingest_refuses_the_rule_through_its_own_command(self) -> None:
        parser = anamnesis.build_parser()
        stream = self.scratch / "ingest.jsonl"
        arguments = parser.parse_args([
            "ingest",
            "--policy", str(ESTATE / "policy.json"),
            "--curation-policy", str(FIXTURE),
            "--events", str(stream),
        ])
        with self.assertRaises(anamnesis.Refusal) as caught:
            arguments.handler(arguments)
        self.assertEqual(caught.exception.code, RULE)
        # The refusal is durable: ingest names an event stream and the rule
        # reaches it, because ingest resolves inside the recorded span.
        written = [json.loads(line) for line in
                   stream.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(
            [event["rule"] for event in written
             if event["event"] == "anamnesis.source.refused"],
            [RULE],
        )

    def test_release_leaves_no_directory_no_assertion_and_no_quarantine(self) -> None:
        out = self.scratch / "release"
        parser = anamnesis.build_parser()
        arguments = parser.parse_args([
            "release",
            "--policy", str(ESTATE / "policy.json"),
            "--curation-policy", str(FIXTURE),
            "--out", str(out),
        ])
        with self.assertRaises(anamnesis.Refusal) as caught:
            arguments.handler(arguments)
        self.assertEqual(caught.exception.code, RULE)
        self.assertFalse(out.exists())
        self.assertEqual(list(self.scratch.iterdir()), [])
        # At the parent commit this same input released PARENT_RELEASE with
        # PARENT_FINDINGS findings and wrote the false name into every one of
        # PARENT_ASSERTIONS assertions.
        self.assertNotEqual(PARENT_RELEASE, ESTATE_RELEASE)
        self.assertEqual((PARENT_FINDINGS, PARENT_ASSERTIONS), (17, 55))

    def test_the_refusal_emits_one_event_carrying_the_rule_and_correlation(self) -> None:
        events = anamnesis.Events()
        refusal = self.refusal(events, FIXTURE)
        self.assertEqual(refusal.code, RULE)
        refused = [event for event in events.emitted
                   if event["event"] == "anamnesis.source.refused"]
        self.assertEqual(len(refused), 1)
        event = refused[0]
        self.assertEqual(event["rule"], RULE)
        self.assertIn("a-mapper-that-does-not-exist", event["reason"])
        self.assertEqual(event["policy_version"], "estate-2026-09-06")
        self.assertEqual(len(event["correlation_id"]), 16)
        # A policy-level refusal implicates no declared record, and the field
        # says so rather than naming the mapper as one.
        self.assertIsNone(event["record"])

    def test_the_fixture_is_the_estate_policy_with_only_its_mapper_changed(self) -> None:
        shipped = read(ESTATE / "curation-policy.json")
        probe = read(FIXTURE)
        self.assertEqual(probe["mapper"], {
            "name": "a-mapper-that-does-not-exist", "version": "9"})
        self.assertEqual(shipped["mapper"], DECLARED)
        without = dict(probe)
        without.pop("mapper")
        expected = dict(shipped)
        expected.pop("mapper")
        self.assertEqual(without, expected)


class TheAssertionRecordsTheEntryThatRan(Fixture):
    """`declared-not-resolved-in-assertion`: the record names the code.

    An assertion used to copy the policy's declared object. It now carries the
    identity of the registry entry that produced it, which is the same object
    whenever the declaration resolves and no object at all when it does not.
    """

    def test_every_assertion_carries_the_resolved_registry_entry(self) -> None:
        entry = anamnesis.resolve_mapper(DECLARED)
        identity = anamnesis.mapper_identity(entry)
        policy = read(PILOT / "curation-policy.json")
        events = anamnesis.Events()
        result = anamnesis.admit(str(PILOT / "policy.json"), events)
        texts = anamnesis._admitted_texts(
            str(PILOT / "policy.json"), result["sources"])
        graph = anamnesis.curate(result["sources"], policy, texts)
        self.assertTrue(graph["assertions"])
        for assertion in graph["assertions"]:
            self.assertEqual(assertion["mapper"], identity)

    def test_a_declaration_that_resolves_is_recorded_byte_for_byte(self) -> None:
        """The hard gate. Anything else moves both shipped release ids."""
        entry = anamnesis.resolve_mapper(DECLARED)
        self.assertEqual(
            anamnesis.canonical(anamnesis.mapper_identity(entry)),
            anamnesis.canonical(DECLARED),
        )
        self.assertEqual(entry.parse, anamnesis.parse_source)

    def test_assertion_takes_the_resolved_entry_and_not_the_policy_string(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        body = source.split("def _assertion(", 1)[1].split("\ndef ", 1)[0]
        self.assertIn("resolved", body.split("\n", 1)[0])
        self.assertIn("mapper_identity(resolved)", body)
        self.assertNotIn('policy["mapper"]', body)
        curation = source.split("def curate(", 1)[1].split("\ndef ", 1)[0]
        self.assertIn('resolve_mapper(policy["mapper"])', curation)
        self.assertNotIn("parse_source(", curation)

    def test_the_unreferenced_declared_constant_is_gone(self) -> None:
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIsNone(
            re.search(r"\bMAPPER\b", source),
            "the constant nothing referenced is replaced by the registry")
        self.assertFalse(hasattr(anamnesis, "MAPPER"))
        # Step 2 added the second entry beside it. Both are listed, so a third
        # arriving unremarked is a failure here rather than a surprise later.
        self.assertEqual(
            list(anamnesis.MAPPER_REGISTRY),
            [("warden-audit-round-markdown", "1"), ("fiat-audit-synopsis", "1")])


class ResolutionIsExactWithNoFallback(Fixture):
    """`fail-open-mapper` at the registry: a miss is a refusal, never a default."""

    def test_no_near_miss_resolves_to_anything(self) -> None:
        for declared in (
            {"name": "warden-audit-round-markdown", "version": "2"},
            {"name": "warden-audit-round-markdown", "version": "1.0"},
            {"name": "warden-audit-round-markdown", "version": ""},
            {"name": "warden-audit-round-markdown", "version": 1},
            {"name": "warden-audit-round-markdown", "version": None},
            {"name": "warden-audit-round-markdow", "version": "1"},
            {"name": "warden-audit-round-markdown-v2", "version": "1"},
            {"name": "WARDEN-AUDIT-ROUND-MARKDOWN", "version": "1"},
            {"name": "", "version": "1"},
            {"name": None, "version": "1"},
            {"name": ["warden-audit-round-markdown"], "version": "1"},
            {"name": "warden-audit-round-markdown"},
            {"version": "1"},
            {},
        ):
            with self.subTest(declared=json.dumps(declared, sort_keys=True)):
                with self.assertRaises(anamnesis.Refusal) as caught:
                    anamnesis.resolve_mapper(declared)
                self.assertEqual(caught.exception.code, RULE)
        # Nothing outside a mapping resolves either, and none of it raises
        # anything but the rule.
        for declared in (None, "warden-audit-round-markdown", [], 1):
            with self.subTest(declared=repr(declared)):
                with self.assertRaises(anamnesis.Refusal) as caught:
                    anamnesis.resolve_mapper(declared)
                self.assertEqual(caught.exception.code, RULE)

    def test_both_shipped_corpora_rebuild_to_their_own_release_ids(self) -> None:
        """`release-identity-drift`: neither id moves though the record changed."""
        for shipped, expected in (
            (PILOT, PILOT_RELEASE),
            (ESTATE, ESTATE_RELEASE),
        ):
            with self.subTest(specimen=shipped.name):
                specimen = self.copy_specimen(shipped)
                release_id, _ = anamnesis.verify_rebuild(str(specimen))
                self.assertEqual(release_id, expected)
                # Unmoved because the policies are unchanged and a resolved
                # entry records the same object the policy declares. The
                # release id hashes that policy, so either would move it.
                self.assertEqual(
                    read(shipped / "curation-policy.json")["mapper"], DECLARED)


if __name__ == "__main__":
    unittest.main()
