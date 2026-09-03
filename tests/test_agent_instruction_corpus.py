"""What a bound instruction-document edit costs today, pinned before it changes.

Three instruction documents are bound into `tests/fixtures/agent-instruction-v1`
by whole-file SHA-256. `_corpus_sha256` digests a subject that carries
`fixtures`, and `fixtures` carries each bound source's whole-file digest, so
editing any of those three documents moves the corpus digest and invalidates
both committed evidence records. Only `agent_instruction.py measure` and
`parity` can reissue them honestly, and they run through a loopback adapter
pinned to one macOS install.

That is the fault skills#1098 reports. This module records what the fault
actually is, in the checker's own refusal codes, so the change that follows can
be read as a difference rather than taken on trust. Every case here refuses
today. Three of them are expected to keep refusing afterwards, and the runbook
says which.

Every proof runs against a throwaway copy of the tree, through
`scripts/prove_agent_instruction_reconciliation.py`. The live bound documents
are never written: the study's "Never" list rules out editing one to make the
fixture agree with itself, and `test_proofs_run_against_a_copy_and_leave_the_live_tree_untouched`
is what holds that. No case here starts a model or opens a socket.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PROVER = ROOT / "scripts/prove_agent_instruction_reconciliation.py"
CHECKER = ROOT / "scripts/agent_instruction.py"

CORPUS_REFUSAL = "WAI-E-DIGEST.CORPUS"
MEASUREMENT_NODE = "$.evidence.measurement_record"
PARITY_NODE = "$.evidence.parity_record"

# The refusal each omitted mechanical pass produces, observed at
# bacb34c0d49a83dea0c4463a61b2cf1525fec60b. Recorded per pass rather than as a
# count: a pass that started refusing under a sibling's code would still show
# up as needed in a count, and would no longer be identifiable from its refusal.
PASS_SIGNATURES = {
    "manifest-source": (
        "WAI-E-DIGEST.SOURCE",
        "$.fixtures.fiat-study-runbook-phase.source.sha256",
    ),
    "model": (
        "WAI-E-MANIFEST.SOURCE",
        "$.fixtures.fiat-study-runbook-phase.model.sources",
    ),
    "source-spans": (
        "WAI-E-MANIFEST.SOURCE",
        "$.source_spans.source.sha256",
    ),
    "compact": (
        "WAI-E-CANONICAL.ROUNDTRIP",
        "$.fixtures.fiat-study-runbook-phase",
    ),
    "manifest-artifacts": (
        "WAI-E-DIGEST.ARTIFACT",
        "$.fixtures.fiat-study-runbook-phase.artifacts.compact",
    ),
}

REPORT_KEYS = {"candidate", "command", "criterion", "exit", "schema", "unit", "value"}


def load(name: str, script: Path):
    spec = importlib.util.spec_from_file_location(name, script)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentInstructionCorpusTests(unittest.TestCase):
    """One prover, shared: each reconciliation copies the tree and runs `check`."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.prover = load("prove_agent_instruction_reconciliation", PROVER)
        cls.checker = load("agent_instruction", CHECKER)
        cls.work = cls.prover.Reconciliation(ROOT, checker=cls.checker)
        cls.after_span = cls.work.edited_source(cls.prover.AFTER_SPAN_PLACEMENT)

    def assertRefused(self, outcome, code, node_path):
        """The checker refused, and the first refusal is the one named."""
        self.assertFalse(outcome["accepted"], outcome["refusals"])
        self.assertEqual(2, outcome["exit"])
        self.assertEqual(
            {"code": code, "node_path": node_path},
            outcome["refusals"][0],
        )

    def test_out_of_span_edit_refuses_the_corpus_digest_at_the_measurement_record(self):
        """The whole fault, in one case: an edit that changed no reviewed byte.

        The edit is appended after the reviewed span, so the span digest and
        every recorded binding offset are untouched, and all five mechanical
        passes are applied. Nothing is left for a contributor to do by hand,
        and the tree still refuses, because the corpus subject carries the
        whole-file digest the edit moved.
        """
        self.assertFalse(
            self.work.span_moved(self.after_span),
            "the out-of-span edit moved the reviewed span",
        )
        self.assertEqual(
            self.work.span,
            self.after_span[self.work.start : self.work.end],
        )

        outcome = self.work.reconcile(self.after_span)
        self.assertRefused(outcome, CORPUS_REFUSAL, MEASUREMENT_NODE)

        # The measured bytes did not change; only the digest embedded in them
        # did. That is what makes the reissue a formality the machine cannot
        # perform, rather than a measurement that is genuinely out of date.
        recorded = self.work._live_record(
            self.prover.MEASUREMENT, allow_integers=True
        )
        document = next(
            item for item in recorded["documents"]
            if item["fixture_id"] == self.prover.SUBJECT
        )
        self.assertEqual(
            self.work.end - self.work.start,
            document["source"]["bytes"],
            "the recorded source bytes are the reviewed span's bytes",
        )

    def test_out_of_span_edit_also_stales_the_parity_record(self):
        """Both records, not just the one the refusal names.

        `check` compares the measurement record first and refuses there, so the
        parity record's staleness is invisible from one run. It is a second
        record, reissued by a second model family, and the runbook's correction
        to the study turns on it. Proved twice: the recorded digest is shown to
        have matched before the edit and not after, and the refusal waiting at
        the parity node is then reached by moving the measurement record's
        recorded digest onto the recomputed one.
        """
        recorded = self.work.recorded_corpus_digests()
        before = self.work.corpus_digest(self.work.manifest)
        self.assertEqual(before, recorded["measurement_record"])
        self.assertEqual(before, recorded["parity_record"])

        outcome = self.work.reconcile(self.after_span)
        after = outcome["corpus_sha256"]
        self.assertNotEqual(before, after, "the edit did not move the corpus digest")
        self.assertNotEqual(after, recorded["parity_record"])

        # Moving only the measurement record's recorded corpus digest: no count
        # and no date is touched, and no model is consulted. It exists to reach
        # the second refusal, not to reissue anything.
        reached = self.work.reconcile(self.after_span, rebind_measurement_corpus=True)
        self.assertRefused(reached, CORPUS_REFUSAL, PARITY_NODE)

    def test_in_span_edit_refuses_with_every_mechanical_pass_applied(self):
        """The edit that must keep refusing, at both depths it is caught.

        An edit inside the reviewed span changes the bytes the recorded counts
        are counts of. The reviewed span digest catches it first, before any
        evidence record is consulted. Rebinding that digest too, which is what
        a re-review would mean, does not get past it either: the measurement
        record binds the span digest as well. The design landing at step 3 must
        leave both of these refusing.
        """
        in_span = self.work.in_span_source()
        self.assertTrue(self.work.span_moved(in_span))
        self.assertEqual(
            len(self.work.source), len(in_span),
            "the in-span edit changed the file length, so offsets moved too",
        )

        caught_at_the_span = self.work.reconcile(in_span)
        self.assertRefused(
            caught_at_the_span,
            "WAI-E-DIGEST.SOURCE_SPAN",
            f"$.fixtures.{self.prover.SUBJECT}.source.span_sha256",
        )

        caught_at_the_record = self.work.reconcile(in_span, rebind_span=True)
        self.assertRefused(caught_at_the_record, CORPUS_REFUSAL, MEASUREMENT_NODE)

    def test_every_mechanical_pass_is_load_bearing(self):
        """The passes are five, and omitting any one is visible in the refusal.

        This is what makes the corpus refusal above a finding rather than a
        missed step: it is only reached when nothing mechanical is left. Each
        omission refuses under its own pairing of code and node path, so a
        contributor reading a refusal can tell which pass they skipped. The
        codes alone do not separate them: `model` and `source-spans` both
        refuse `WAI-E-MANIFEST.SOURCE` and differ only in node path, which is
        why the assertion below compares the pair rather than the code.

        The sixth pass a live reconciliation owes is the coverage register,
        which `check` never reads and a fixture copy therefore cannot observe.
        It is asserted here as a binding rather than as a behaviour, so it is
        not forgotten by anyone reading this list as complete.
        """
        self.assertEqual(
            sorted(PASS_SIGNATURES),
            sorted(self.prover.MECHANICAL_PASSES),
        )

        observed = {}
        for name in self.prover.MECHANICAL_PASSES:
            outcome = self.work.reconcile(self.after_span, skip=(name,))
            self.assertFalse(
                outcome["accepted"],
                f"omitting the {name} pass left the tree accepted",
            )
            first = outcome["refusals"][0]
            observed[name] = (first["code"], first["node_path"])

        self.assertEqual(PASS_SIGNATURES, observed)
        self.assertEqual(
            len(set(observed.values())), len(observed),
            "two passes share a refusal signature, so one is not identifiable",
        )

        bound = self.work.coverage_bound_artifacts()
        for artifact in ("compact.wai", "model.json", "source-spans.json"):
            self.assertIn(
                f"tests/fixtures/agent-instruction-v1/{self.prover.SUBJECT}/{artifact}",
                bound,
                "the coverage register no longer binds an artefact the passes rewrite",
            )
        self.assertIn("tests/fixtures/agent-instruction-v1/manifest.json", bound)

    def test_proofs_run_against_a_copy_and_leave_the_live_tree_untouched(self):
        """The boundary that lets any of this be a test at all.

        The study's "Never" list rules out editing a bound document to make the
        fixture agree with itself, and every case in this module edits one. They
        stay tests rather than becoming that edit only because the write lands
        in a copy. Checked three ways: the bound sources are byte-identical
        across a full reconciliation, the copy is a fresh directory outside the
        repository, and the confinement the writes go through refuses a path
        that would escape it.
        """
        before = self.work.live_digests()
        self.assertIn("plugins/hexaemeron/skills/fiat/SKILL.md", before)
        self.assertIn("plugins/horos/skills/horos/SKILL.md", before)
        self.assertIn("PROMISE_MACHINE.md", before)

        self.work.reconcile(self.after_span)
        self.assertEqual(before, self.work.live_digests())

        with tempfile.TemporaryDirectory() as scratch:
            tree = self.work.copy_tree(Path(scratch))
            self.assertTrue(tree.is_dir())
            self.assertNotIn(ROOT, tree.parents)

            # Same edit, written into the copy: the copy moves and the live
            # tree does not.
            self.work.apply_passes(tree, self.after_span)
            self.assertEqual(
                self.prover.digest(self.after_span),
                self.prover.digest((tree / self.work.source_path).read_bytes()),
            )
            self.assertNotEqual(
                self.prover.digest(self.after_span),
                before[self.work.source_path],
            )

            for escape in ("../escape", "/etc/passwd", "tests/../../escape"):
                with self.assertRaises(self.checker.CodecError):
                    self.checker.write_confined_atomic(tree, escape, b"x\n")

        self.assertEqual(before, self.work.live_digests())

    def test_prover_selftest_exits_zero_and_writes_a_closed_report(self):
        """The prover, as a contributor runs it, not as this module imports it.

        `selftest` is the one subcommand that must be green before the design
        lands: it checks the tool's own machinery rather than the repository's
        behaviour. `offline` and `span-shift` report the state of a criterion
        that is still unmet at this step, so they are asserted to write a
        closed report rather than to exit zero.
        """
        with tempfile.TemporaryDirectory() as scratch:
            reports = {}
            for command, expected_exit in (
                ("selftest", 0),
                ("offline", 1),
                ("span-shift", 1),
            ):
                target = Path(scratch) / f"{command}.json"
                completed = subprocess.run(
                    [
                        sys.executable, str(PROVER), command,
                        "--root", str(ROOT),
                        "--candidate", "digest-neutral-corpus",
                        "--report", str(target),
                    ],
                    capture_output=True, text=True, timeout=600, check=False,
                )
                self.assertEqual(
                    expected_exit, completed.returncode,
                    f"{command}: {completed.stderr}",
                )
                raw = target.read_bytes()
                self.assertTrue(raw.endswith(b"\n"))
                record = json.loads(raw)
                self.assertEqual(REPORT_KEYS, set(record))
                self.assertEqual("protasis-design-report/v1", record["schema"])
                self.assertEqual("digest-neutral-corpus", record["candidate"])
                self.assertEqual(expected_exit, record["exit"])
                reports[command] = record

        self.assertEqual("prover-selftest", reports["selftest"]["criterion"])
        self.assertEqual("count", reports["selftest"]["unit"])
        self.assertGreater(reports["selftest"]["value"], 0)

        # The two criteria the design record schedules at `integration`, still
        # unmet, reported as what they are.
        self.assertEqual(
            "offline-reconciliation-green", reports["offline"]["criterion"]
        )
        self.assertEqual("boolean", reports["offline"]["unit"])
        self.assertFalse(reports["offline"]["value"])
        self.assertEqual("span-shift-regression", reports["span-shift"]["criterion"])
        self.assertEqual("count", reports["span-shift"]["unit"])
        # The value, not just its shape: a report nothing checks the value of
        # is not evidence. One placement is covered today, `after-span`, and
        # the runbook schedules `before-span` at step 4. When that lands this
        # assertion is what says so.
        self.assertEqual(1, reports["span-shift"]["value"])

    def test_a_report_path_the_manifest_binds_is_refused(self):
        """The one write outside the copy, aimed at a bound document.

        `--report PROMISE_MACHINE.md --root .` would replace a bound document
        with a JSON report, which the study's "Never" list rules out. The bound
        set is derived from the manifest, so it tracks what the manifest binds
        rather than a list that can drift from it.

        The refusal is exercised against a throwaway copy rather than the live
        tree: a regression in the guard then damages a copy under `TMPDIR` and
        never a bound document. The live tree is used only to read the bound
        set, which writes nothing.

        An absent guard is asserted rather than raised, so a tree without the
        control fails this case on the claim it makes instead of erroring on a
        missing attribute.
        """
        self.assertTrue(
            hasattr(self.prover, "bound_targets"),
            "the prover derives no bound set, so `--report` cannot refuse one",
        )
        bound = self.prover.bound_targets(ROOT, self.work.manifest)
        for document in (
            "plugins/hexaemeron/skills/fiat/SKILL.md",
            "plugins/horos/skills/horos/SKILL.md",
            "PROMISE_MACHINE.md",
        ):
            self.assertIn((ROOT / document).resolve(), bound)
        self.assertIn(
            (ROOT / "tests/fixtures/agent-instruction-v1/manifest.json").resolve(),
            bound,
        )

        with tempfile.TemporaryDirectory() as scratch:
            tree = self.work.copy_tree(Path(scratch))
            copied = self.prover.bound_targets(tree, self.work.manifest)

            hostile = (
                "PROMISE_MACHINE.md",
                "plugins/hexaemeron/skills/fiat/SKILL.md",
                "tests/fixtures/agent-instruction-v1/manifest.json",
                f"tests/fixtures/agent-instruction-v1/{self.prover.SUBJECT}/compact.wai",
                str(tree / "PROMISE_MACHINE.md"),
            )
            for target in hostile:
                resolved = Path(target)
                if not resolved.is_absolute():
                    resolved = tree / target
                before = resolved.read_bytes()
                with self.assertRaises(self.prover.ProverError):
                    self.prover.write_report(self.checker, tree, target, b"{}\n", copied)
                self.assertEqual(
                    before, resolved.read_bytes(),
                    f"the refused report write changed {target}",
                )

            # A path the manifest does not bind still writes, so the guard is a
            # boundary rather than a blanket refusal.
            allowed = Path(scratch) / "report.json"
            self.prover.write_report(self.checker, tree, str(allowed), b"{}\n", copied)
            self.assertEqual(b"{}\n", allowed.read_bytes())

    def test_construction_refuses_a_tree_already_off_a_bound_digest(self):
        """The constructor's self-consistency claim, over every bound path.

        `Reconciliation` promises a proof never runs against a tree that was
        already inconsistent. That promise is only worth the paths it covers:
        the manifest binds a source and five artefacts for each of three
        fixtures, and drift in any of them would otherwise surface later as a
        `check` refusal attributed to the edit rather than to the drift.

        Exercised by planting drift in a throwaway copy, in an artefact no
        mechanical pass rewrites, so the failure can only come from the
        constructor's own check. The live tree is read but never written.
        """
        self.assertTrue(
            hasattr(self.prover, "bound_digests"),
            "the prover enumerates no bound digests, so construction checks a subset",
        )
        bound = dict(self.prover.bound_digests(self.work.manifest))
        self.assertEqual(18, len(bound), "three sources and fifteen artefacts")
        for previously_unchecked in (
            f"tests/fixtures/agent-instruction-v1/{self.prover.SUBJECT}/questions.json",
            f"tests/fixtures/agent-instruction-v1/{self.prover.SUBJECT}/mutations.json",
            "tests/fixtures/agent-instruction-v1/horos-boundary-check/model.json",
            "tests/fixtures/agent-instruction-v1/promise-machine-router-selection/compact.wai",
            "PROMISE_MACHINE.md",
        ):
            self.assertIn(previously_unchecked, bound)

        with tempfile.TemporaryDirectory() as scratch:
            tree = self.work.copy_tree(Path(scratch))
            # The unedited copy constructs, so the refusal below is the drift
            # and not the copy.
            self.prover.Reconciliation(tree, checker=self.checker)

            drifted = (
                tree
                / f"tests/fixtures/agent-instruction-v1/{self.prover.SUBJECT}/questions.json"
            )
            drifted.write_bytes(drifted.read_bytes() + b"\n")
            with self.assertRaises(self.prover.ProverError) as raised:
                self.prover.Reconciliation(tree, checker=self.checker)
            self.assertIn("questions.json", str(raised.exception))
            self.assertIn("off its manifest digest", str(raised.exception))

    def test_a_candidate_outside_the_design_record_is_refused(self):
        """A design report may not name a candidate no design record contains.

        `--candidate` is closed over the ids the run's design record declares,
        the way `.hexaemeron/scripts/design_probe.py` closes the same flag, so
        the refusal is a usage error before any proof runs and before any
        report is written. The fallback set is asserted to agree with the
        record, so the flag stays closed where the record is absent.

        An absent guard is asserted rather than raised, for the reason the
        sibling case above gives.
        """
        self.assertTrue(
            hasattr(self.prover, "candidate_choices"),
            "the prover reads no candidate set, so `--candidate` is not closed",
        )
        self.assertEqual(
            sorted(self.prover.candidate_choices(ROOT)),
            sorted(self.prover.FALLBACK_CANDIDATES),
        )
        self.assertIn("digest-neutral-corpus", self.prover.candidate_choices(ROOT))

        with tempfile.TemporaryDirectory() as scratch:
            target = Path(scratch) / "report.json"
            completed = subprocess.run(
                [
                    sys.executable, str(PROVER), "selftest",
                    "--root", str(ROOT),
                    "--candidate", "not-a-candidate",
                    "--report", str(target),
                ],
                capture_output=True, text=True, timeout=600, check=False,
            )
            self.assertNotEqual(0, completed.returncode)
            self.assertIn("not-a-candidate", completed.stderr)
            self.assertFalse(
                target.exists(),
                "a refused candidate still wrote a design report",
            )

    def test_the_projection_covers_only_the_source_quarter_of_the_bound_set(self):
        """Where step 1's enumeration and step 2's projection disagree.

        `bound_digests` is the prover's one enumeration of everything the
        manifest binds, and the constructor's self-consistency check and the
        `--report` guard both read it, so it is the authoritative list. It
        holds six digests per fixture: the whole-file source digest and five
        artefact digests. Three of those five -- `model`, `source_spans` and
        `compact` -- embed the source digest, which is why `manifest-artifacts`
        is a mechanical pass in its own right: they move whenever the source
        digest inside them moves. `mutations` and `questions` embed none, so
        they are the control and stay put either way.

        `digest_neutral_projection` neutralises the source digest and none of
        the five. That is the whole of S2-R1-01, stated against step 1's list
        rather than a list rewritten here, so the two halves cannot drift into
        disagreeing about what "bound" means.

        The consequence is step 3's: `_corpus_sha256` digests a subject
        carrying `fixtures`, so it carries all four. Switching that subject
        onto the projection without widening it to the artefact digests leaves
        the corpus digest moving on an out-of-span edit, which is the refusal
        skills#1098 reports. Widening it is proved safe -- an in-span edit
        still moves `span_sha256`, which the projection never substitutes -- so
        step 3 inverts this case rather than working around it.
        """
        manifest = self.work.manifest
        bound = self.prover.bound_digests(manifest)
        sources = {entry["source"]["sha256"] for entry in manifest["fixtures"]}
        artifacts = {
            artifact["sha256"]
            for entry in manifest["fixtures"]
            for artifact in entry["artifacts"].values()
        }
        self.assertEqual(len(manifest["fixtures"]) * 6, len(bound))
        self.assertEqual(sources | artifacts, {expected for _, expected in bound})
        embedding = {
            entry["artifacts"][name]["sha256"]
            for entry in manifest["fixtures"]
            for name in ("model", "source_spans", "compact")
        }
        self.assertEqual(len(manifest["fixtures"]) * 3, len(embedding))

        # One buffer carrying every bound digest, so the projection is asked
        # about the whole enumeration at once rather than a chosen slice.
        probe = b"\n".join(expected.encode("ascii") for _, expected in bound)
        projected = self.checker.digest_neutral_projection(manifest, probe)
        marker = self.checker.CORPUS_SOURCE_DIGEST_PLACEHOLDER.encode("ascii")

        for digest in sorted(sources):
            with self.subTest(kind="source", digest=digest):
                self.assertNotIn(digest.encode("ascii"), projected)
        for digest in sorted(artifacts):
            with self.subTest(kind="artifact", digest=digest):
                self.assertIn(
                    digest.encode("ascii"),
                    projected,
                    "the projection now reaches the artefact digests: step 3's "
                    "widening has landed and this case is the one to invert",
                )
        self.assertEqual(len(sources), projected.count(marker))


if __name__ == "__main__":
    unittest.main()
