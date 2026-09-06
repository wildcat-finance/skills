"""Prove deterministic instruction reconciliation with model evidence disabled.

The corpus digest uses the digest-neutral structural projection. Source spans
still refuse until their review digest is explicitly replaced, while edits
outside a reviewed span rederive every affected offset from the bound bytes.
Two source locations may bind the same directive node, so offsets are keyed by
node and recorded span rather than node alone.

The committed measurement and parity files are frozen historical records.
They remain digest-bound but are neither rewritten nor used as transition
gates. Every proof runs against a throwaway tree copy, and no case starts a
model, tokenizer, adapter, subprocess-backed generator, or network socket.
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

    def assertPlantedSpanRefuses(self, plant, message):
        """`plant` one drift into `source-spans.json`, then re-derive against it.

        The copy is left self-consistent by every digest the manifest binds --
        the planted record's own artefact digest is rebound before the
        constructor reads it -- so the refusal comes from the re-derivation and
        not from the tree already disagreeing with itself. That rebinding is
        what makes the plant reachable at all: it sits in the one place the
        constructor's whole-file check cannot see.
        """
        with tempfile.TemporaryDirectory() as scratch:
            tree = self.work.copy_tree(Path(scratch))
            relative = self.work.fixture["artifacts"]["source_spans"]["path"]
            record = self.checker.load_canonical_record(
                self.checker.read_confined(tree, relative)
            )
            plant(record)
            written = self.checker.canonical_record_bytes(record)
            self.checker.write_confined_atomic(tree, relative, written)

            manifest = self.checker.load_canonical_record(
                self.checker.read_confined(tree, self.prover.MANIFEST)
            )
            entry = next(
                item for item in manifest["fixtures"]
                if item["id"] == self.prover.SUBJECT
            )
            entry["artifacts"]["source_spans"]["sha256"] = self.prover.digest(written)
            self.checker.write_confined_atomic(
                tree,
                self.prover.MANIFEST,
                self.checker.canonical_record_bytes(manifest),
            )

            drifted = self.prover.Reconciliation(tree, checker=self.checker)
            with self.assertRaises(self.prover.ProverError) as raised:
                drifted.rederive_offsets(
                    drifted.edited_source(self.prover.BEFORE_SPAN_PLACEMENT)
                )
            self.assertIn(message, str(raised.exception))

    def test_out_of_span_edit_leaves_the_corpus_digest_where_it_was(self):
        """An out-of-span edit is structural and leaves frozen evidence alone."""
        self.assertFalse(
            self.work.span_moved(self.after_span),
            "the out-of-span edit moved the reviewed span",
        )
        self.assertEqual(
            self.work.span,
            self.after_span[self.work.start : self.work.end],
        )

        before = self.work.corpus_digest(self.work.manifest)
        outcome = self.work.reconcile(self.after_span)
        self.assertEqual(
            before,
            outcome["corpus_sha256"],
            "the out-of-span edit moved the corpus digest",
        )
        self.assertNotIn(
            {"code": CORPUS_REFUSAL, "node_path": MEASUREMENT_NODE},
            outcome["refusals"],
            "the corpus digest still refuses at the measurement record",
        )
        self.assertTrue(outcome["accepted"], outcome["refusals"])
        self.assertEqual(self.work.manifest["model_evidence_status"], "disabled")

    def test_out_of_span_edit_no_longer_stales_the_parity_record(self):
        """Disabled historical records are neither rewritten nor transition gates."""
        frozen = {
            path: self.work._live_bytes(path)
            for path in (self.prover.MEASUREMENT, self.prover.PARITY)
        }
        before = self.work.corpus_digest(self.work.manifest)
        for path, historical_bytes in frozen.items():
            historical = self.checker.load_canonical_record(
                historical_bytes, allow_integers=True
            )
            self.assertNotEqual(
                before,
                historical["corpus_sha256"],
                f"{path} still claims the current structural corpus",
            )
        outcome = self.work.reconcile(self.after_span)
        after = outcome["corpus_sha256"]
        self.assertEqual(before, after, "the edit moved the corpus digest")
        self.assertTrue(outcome["accepted"], outcome["refusals"])
        for path, expected in frozen.items():
            self.assertEqual(expected, self.work._live_bytes(path))

    def test_in_span_edit_requires_an_explicit_source_span_rebind(self):
        """The structural span refuses until its review boundary is replaced."""
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

        rebound = self.work.reconcile(in_span, rebind_span=True)
        self.assertTrue(rebound["accepted"], rebound["refusals"])

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

    def test_a_before_span_edit_has_its_offsets_re_derived_rather_than_shifted(self):
        """#1098's third acceptance check, on the placement that moves offsets.

        An edit before a reviewed span start moves every recorded binding
        offset: the manifest's `source.start` and `source.end`, every
        `source-spans.json` span's pair, and every `model.json` binding's pair.
        An edit after the span moves none, which is why the two placements are
        separate claims and why nothing before step 4 covered this one.

        What the offsets pass writes back is re-derived and not shifted. The
        reviewed span's bytes are the anchor, their digest is what an
        out-of-span edit leaves alone, and the new offsets are read off from
        where those bytes were found in the edited source. Adding the byte
        delta to each recorded number would land on the same integers here
        while proving nothing about where the span went.

        What separates the two is bounded by the fixture, and saying which
        assertions do the work matters. A prepend moves every span by one
        uniform delta, so the re-derived integers and the shifted integers are
        equal here, and no assertion on them can tell the two apart. The
        refusals can: bytes that occur twice identify no offset and refuse
        rather than resolving to their first occurrence; bytes that are gone
        return `None` instead of a number; and a recorded span that is not the
        bytes it claims refuses instead of being carried into the copy. Those
        are asserted for the anchor and, in the ambiguous-node case below, for
        the node loop, which is the only thing separating that loop from
        arithmetic. The uniform delta is asserted as a consequence of the
        located offsets, not as their source.

        An absent re-derivation is asserted rather than raised, so a tree
        without it fails on the claim this case makes instead of erroring on a
        missing attribute and reading as inconclusive.
        """
        self.assertTrue(
            hasattr(self.work, "rederive_offsets"),
            "the prover re-derives no offsets, so a before-span edit cannot reconcile",
        )
        before_span = self.work.edited_source(self.prover.BEFORE_SPAN_PLACEMENT)

        # The placement really is the one that moves offsets: the reviewed
        # bytes survived the edit, and they are no longer where they were.
        self.assertIn(self.work.span, before_span)
        self.assertTrue(
            self.work.span_moved(before_span),
            "the before-span edit left the reviewed bytes at their recorded offsets",
        )

        offsets = self.work.rederive_offsets(before_span)
        self.assertIsNotNone(offsets, "the anchor was not found in the edited source")
        self.assertEqual(len(self.prover.OUT_OF_SPAN_EDIT), offsets["delta"])
        self.assertEqual(
            [self.work.start, self.work.end], offsets["governed"]["recorded"]
        )

        # Located, then digest-checked at the position found. This is the
        # assertion a shift cannot satisfy by construction: it says the bytes
        # at the new offsets are the reviewed bytes, not that the number
        # changed by the right amount.
        span_start, span_end = offsets["governed"]["rederived"]
        self.assertEqual(
            self.work.fixture["source"]["span_sha256"],
            self.prover.digest(before_span[span_start:span_end]),
        )
        self.assertNotEqual(self.work.start, span_start)

        spans = self.work._live_record(
            self.work.fixture["artifacts"]["source_spans"]["path"]
        )
        self.assertEqual(len(spans["spans"]), len(offsets["nodes"]))
        located_by_binding = {
            (item["node"], tuple(item["recorded"])): item
            for item in offsets["nodes"]
        }
        self.assertEqual(len(offsets["nodes"]), len(located_by_binding))
        for entry in spans["spans"]:
            node = entry["node"]
            recorded = (int(entry["start"]), int(entry["end"]))
            with self.subTest(node=node, recorded=recorded):
                located = located_by_binding[(node, recorded)]
                start, end = located["rederived"]
                self.assertEqual(
                    entry["sha256"], self.prover.digest(before_span[start:end])
                )
                self.assertEqual(
                    [int(entry["start"]), int(entry["end"])], located["recorded"]
                )
                # Every offset moved, so no assertion above is passing on a
                # span the edit happened to leave alone.
                self.assertNotEqual(located["recorded"], located["rederived"])
                self.assertEqual(int(entry["start"]) + offsets["delta"], start)

        # Bytes that do not identify one position refuse. A shift has no
        # opinion here, which is the difference this case exists to state.
        with self.assertRaises(self.prover.ProverError) as raised:
            self.work.rederive_offsets(self.work.source + self.work.span)
        self.assertIn("more than once", str(raised.exception))

        # Bytes that are gone are an in-span edit, and there is nothing to
        # re-derive. A shift would return numbers for this too.
        self.assertIsNone(self.work.rederive_offsets(self.work.in_span_source()))

        # A recorded span that is not the bytes it says it is refuses, so the
        # re-derivation is anchored on digests it checked rather than on
        # offsets it trusted. `check` catches this too, but only after the
        # rewrite; a shift would carry the disagreement into the copy and let
        # the refusal arrive attributed to the edit. Planted in a throwaway
        # copy, in the one field the constructor's whole-file check cannot see.
        def wrong_digest(record):
            record["spans"][0]["sha256"] = self.prover.digest(b"")

        self.assertPlantedSpanRefuses(wrong_digest, "off its own digest")

        # The same refusal, one level down. The two assertions above are the
        # anchor's; this one is the node loop's, and it is the only thing
        # separating that loop from arithmetic. A prepend moves every node by
        # one uniform delta, so no assertion on the integers can tell a located
        # node from a node moved by `delta`; bytes that occur twice inside the
        # reviewed span can, because locating refuses where adding does not.
        span = self.work.span
        width = 8
        repeated = next(
            index
            for index in range(len(span) - width)
            if span.count(span[index : index + width]) > 1
        )
        node_start = self.work.start + repeated
        node_end = node_start + width

        def ambiguous_node(record):
            entry = record["spans"][-1]
            entry["start"] = str(node_start)
            entry["end"] = str(node_end)
            entry["sha256"] = self.prover.digest(self.work.source[node_start:node_end])

        self.assertPlantedSpanRefuses(ambiguous_node, "more than once")

        # The re-derived offsets reach all three records that carry them, and
        # `check` accepts the reviewed span at its new position.
        with tempfile.TemporaryDirectory() as scratch:
            tree = self.work.copy_tree(Path(scratch))
            self.work.apply_passes(tree, before_span)

            manifest = self.checker.load_canonical_record(
                self.checker.read_confined(tree, self.prover.MANIFEST)
            )
            written = next(
                entry for entry in manifest["fixtures"]
                if entry["id"] == self.prover.SUBJECT
            )
            self.assertEqual(str(span_start), written["source"]["start"])
            self.assertEqual(str(span_end), written["source"]["end"])
            self.assertEqual(
                self.work.fixture["source"]["span_sha256"],
                written["source"]["span_sha256"],
                "an out-of-span edit rebound the reviewed span digest",
            )

            written_spans = self.checker.load_canonical_record(
                self.checker.read_confined(
                    tree, self.work.fixture["artifacts"]["source_spans"]["path"]
                )
            )
            written_model = self.checker.load_canonical_json(
                self.checker.read_confined(
                    tree, self.work.fixture["artifacts"]["model"]["path"]
                )
            )
            expected = [
                [str(item["rederived"][0]), str(item["rederived"][1])]
                for item in offsets["nodes"]
            ]
            for label, entries in (
                ("source-spans", written_spans["spans"]),
                ("model", written_model["bindings"]),
            ):
                with self.subTest(record=label):
                    self.assertEqual(
                        expected, [[item["start"], item["end"]] for item in entries]
                    )

        # And the pass is load-bearing: omitted, the same edit leaves the
        # recorded offsets pointing at bytes the edit displaced.
        omitted = self.work.reconcile(before_span, skip=(self.prover.OFFSET_PASS,))
        self.assertRefused(
            omitted,
            "WAI-E-DIGEST.SOURCE_SPAN",
            f"$.fixtures.{self.prover.SUBJECT}.source.span_sha256",
        )

    def test_the_manifests_own_offsets_are_read_as_recorded_decimals(self):
        """The anchor pair, held to the rule every other recorded offset obeys.

        `recorded_offset` exists because `int()` accepts `"+1"`, `" 1"`,
        `"1_0"` and a Unicode digit, and raises `ValueError` rather than a
        `ProverError` on the rest, so a record that had drifted would reach the
        reader as a crash instead of a refusal naming the field. The manifest's
        `source.start` and `source.end` are the anchor the whole re-derivation
        hangs off, and reading them any other way would exempt the one pair
        that matters most from the rule.

        Planted in a throwaway copy, on a value the constructor's other checks
        pass over: `int("018445")` is `18445`, so the reviewed span is still
        found at its recorded digest and nothing else in the tree disagrees.
        """
        with tempfile.TemporaryDirectory() as scratch:
            tree = self.work.copy_tree(Path(scratch))
            manifest = self.checker.load_canonical_record(
                self.checker.read_confined(tree, self.prover.MANIFEST)
            )
            entry = next(
                item for item in manifest["fixtures"]
                if item["id"] == self.prover.SUBJECT
            )
            entry["source"]["start"] = "0" + entry["source"]["start"]
            self.checker.write_confined_atomic(
                tree,
                self.prover.MANIFEST,
                self.checker.canonical_record_bytes(manifest),
            )

            with self.assertRaises(self.prover.ProverError) as raised:
                self.prover.Reconciliation(tree, checker=self.checker)
            self.assertIn("padded decimal", str(raised.exception))

    def test_a_before_span_edit_reconciles_without_model_evidence(self):
        """Offset-only movement is accepted without consulting disabled records."""
        before_span = self.work.edited_source(self.prover.BEFORE_SPAN_PLACEMENT)
        unmoved = self.work.corpus_digest(self.work.manifest)

        # The contrast, in one line: the sibling placement changes nothing.
        after = self.work.reconcile(self.after_span)
        self.assertTrue(after["accepted"], after["refusals"])
        self.assertEqual(unmoved, after["corpus_sha256"])

        outcome = self.work.reconcile(before_span)
        self.assertTrue(outcome["accepted"], outcome["refusals"])
        self.assertNotEqual(
            unmoved,
            outcome["corpus_sha256"],
            "the recorded offsets moved and the corpus digest did not",
        )
        self.assertNotIn(
            "WAI-E-DIGEST.SOURCE_SPAN",
            {refusal["code"] for refusal in outcome["refusals"]},
        )

        # The cause, isolated: the offsets alone, with every digest, path, count
        # and risk class left where it was.
        shifted = json.loads(json.dumps(self.work.manifest))
        fixture = next(
            entry for entry in shifted["fixtures"]
            if entry["id"] == self.prover.SUBJECT
        )
        delta = len(self.prover.OUT_OF_SPAN_EDIT)
        fixture["source"]["start"] = str(self.work.start + delta)
        fixture["source"]["end"] = str(self.work.end + delta)
        self.assertNotEqual(unmoved, self.work.corpus_digest(shifted))

        # And the projection is not what fails to cover them: an offset is not
        # a digest the manifest binds a path by, so there is nothing here for
        # `digest_neutral_projection` to substitute.
        bound = set(self.checker._bound_digest_values(self.work.manifest))
        for offset in (self.work.start, self.work.end):
            self.assertNotIn(str(offset), bound)

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

        `selftest` checks the tool's own machinery rather than the repository's
        behaviour. `offline` and `span-shift` are the two criteria the design
        record schedules at `integration`, and both are met at step 4, so all
        three subcommands are asserted to exit zero and to write a closed
        report at the paths the record's own resolver commands name.
        """
        with tempfile.TemporaryDirectory() as scratch:
            reports = {}
            for command, expected_exit in (
                ("selftest", 0),
                # Step 1 expected 1 from `offline`: an out-of-span edit could
                # not be reconciled offline, which is the fault skills#1098
                # reports. Step 3 removed the corpus and measured-bytes
                # bindings that caused it. Step 1 and step 3 expected 1 from
                # `span-shift` because the before-span placement was uncovered;
                # step 4 covers it, so the gate is met and this expects 0.
                ("offline", 0),
                ("span-shift", 0),
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

        # The two criteria the design record schedules at `integration`, both
        # met at step 4, reported as what they are.
        self.assertEqual(
            "offline-reconciliation-green", reports["offline"]["criterion"]
        )
        self.assertEqual("boolean", reports["offline"]["unit"])
        # Step 1 asserted false: an out-of-span edit could not then be
        # reconciled without a model, which is the fault skills#1098 reports.
        # The step 3 widening removed the corpus and measured-bytes bindings
        # that caused it, so this criterion is met and the design record's
        # `offline-reconciliation-green` gate has its evidence.
        self.assertTrue(reports["offline"]["value"])
        self.assertEqual("span-shift-regression", reports["span-shift"]["criterion"])
        self.assertEqual("count", reports["span-shift"]["unit"])
        # The value, not just its shape: a report nothing checks the value of
        # is not evidence. Both placements are covered at step 4, which is the
        # threshold the design record sets, and this assertion is what says the
        # count came from covering the second rather than from counting the
        # first twice.
        self.assertEqual(len(self.prover.SPAN_PLACEMENTS), 2)
        self.assertEqual(2, reports["span-shift"]["value"])

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

    def test_the_projection_covers_every_path_the_prover_binds(self):
        """Inverted from step 2's `..._covers_only_the_source_quarter_...`.

        Step 2's assumption was that `digest_neutral_projection` neutralised the
        source digest and none of the five artefact digests. That was the whole
        of S2-R1-01, and the case stated it against step 1's own enumeration
        rather than a list rewritten here, so the two halves could not drift
        into disagreeing about what "bound" means.

        `bound_digests` is still the authoritative list: the prover's
        constructor self-consistency check and its `--report` guard both read
        it, and it holds six digests per fixture -- the whole-file source digest
        and five artefact digests, eighteen in all. Three of those five per
        fixture (`model`, `source_spans`, `compact`) embed the source digest,
        which is why `manifest-artifacts` is a mechanical pass in its own right.
        `mutations` and `questions` embed none.

        Step 3 widened the projection to the whole of that list, so the
        agreement this case now asserts is the one the design needs:
        `_corpus_sha256` digests a subject carrying `fixtures`, so it carries
        all six per fixture, and a projection covering only the source quarter
        would have left the corpus digest moving on an out-of-span edit -- the
        refusal skills#1098 reports. The widening is safe because an in-span
        edit still moves `span_sha256`, which the projection never substitutes.

        Kept pointed at `bound_digests` rather than at a list of eighteen
        written out here, so a path the manifest starts binding is covered by
        the projection in the same commit that makes the prover protect it.
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
        marker = self.checker.CORPUS_BOUND_DIGEST_PLACEHOLDER.encode("ascii")

        for kind, digests in (("source", sources), ("artifact", artifacts)):
            for digest in sorted(digests):
                with self.subTest(kind=kind, digest=digest):
                    self.assertNotIn(digest.encode("ascii"), projected)
        # Length is preserved and every one of the eighteen became the marker,
        # so this counts the whole enumeration rather than the source quarter
        # step 2 could account for.
        self.assertEqual(len(bound), projected.count(marker))
        self.assertEqual(len(probe), len(projected))

    def test_the_disabled_measurement_record_is_frozen_not_current(self):
        """Historical measurement bytes stay bound while current structure diverges."""
        manifest = self.work.manifest
        self.assertEqual(manifest["model_evidence_status"], "disabled")
        evidence_path = manifest["evidence"]["measurement_record"]["path"]
        evidence_bytes = self.work._live_bytes(evidence_path)
        self.assertEqual(
            manifest["evidence"]["measurement_record"]["sha256"],
            self.prover.digest(evidence_bytes),
        )
        recorded = self.work._live_record(self.prover.MEASUREMENT, allow_integers=True)
        documents = {item["fixture_id"]: item for item in recorded["documents"]}

        for entry in manifest["fixtures"]:
            for artifact_name in ("model", "compact", "source_spans"):
                with self.subTest(fixture=entry["id"], artifact=artifact_name):
                    raw = self.work._live_bytes(
                        entry["artifacts"][artifact_name]["path"]
                    )
                    self.assertEqual(
                        entry["artifacts"][artifact_name]["sha256"],
                        self.prover.digest(raw),
                    )

        subject = next(
            entry
            for entry in manifest["fixtures"]
            if entry["id"] == self.prover.SUBJECT
        )
        historical = documents[self.prover.SUBJECT]
        current_model = self.work._live_bytes(subject["artifacts"]["model"]["path"])
        current_compact = self.work._live_bytes(subject["artifacts"]["compact"]["path"])
        self.assertNotEqual(
            historical["canonical_model"]["sha256"],
            self.prover.digest(
                self.checker.digest_neutral_projection(manifest, current_model)
            ),
        )
        self.assertNotEqual(
            historical["compact"]["sha256"],
            self.prover.digest(
                self.checker.digest_neutral_projection(manifest, current_compact)
            ),
        )
        self.assertNotEqual(
            subject["source"]["span_sha256"],
            historical["source"]["sha256"],
        )

    def test_no_reviewed_span_carries_a_bound_digest(self):
        """Why measuring the reviewed spans raw costs nothing.

        The measurement counts each span as it is on disk, so if a span quoted
        one of the digests the manifest binds, an out-of-span edit would move
        bytes inside a measured stream and the record would go stale for a
        reason the projection was meant to remove.

        No span does today, and this observes it rather than assuming it. If a
        reviewed span ever starts quoting a bound digest, this fails and the
        choice between projecting the span and losing the `span_sha256`
        equality has to be made deliberately, rather than discovered as a
        mysterious `WAI-E-MEASURE.RECORD` after a measure run nobody can repeat.
        """
        manifest = self.work.manifest
        bound = self.checker._bound_digest_values(manifest)
        self.assertEqual(len(self.prover.bound_digests(manifest)), len(bound))
        for entry in manifest["fixtures"]:
            with self.subTest(fixture=entry["id"]):
                source = self.work._live_bytes(entry["source"]["path"])
                span = source[int(entry["source"]["start"]) : int(entry["source"]["end"])]
                self.assertEqual(span, self.checker.digest_neutral_projection(manifest, span))
                for digest in bound:
                    self.assertNotIn(digest.encode("ascii"), span)


if __name__ == "__main__":
    unittest.main()


class LiveReconcileTests(unittest.TestCase):
    """`reconcile`, the one subcommand that writes the tree it is pointed at.

    The three proofs above establish that an out-of-span edit *can* be
    reconciled without a model. None of them reconciles anything a contributor
    keeps: every one works inside a throwaway copy and throws it away. This
    class covers the command that performs the reconciliation, which is the
    second command of the study's demo path and the thing skills#1098's first
    acceptance check needs in order to be met rather than demonstrated.

    Every case here still runs against a copy. The command writes the root it
    is given, so the copy is what it is given.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.prover = load("prove_agent_instruction_reconciliation", PROVER)
        cls.checker = load("agent_instruction", CHECKER)
        cls.work = cls.prover.Reconciliation(ROOT, checker=cls.checker)

    def live_copy(self, scratch: Path, edited: bytes) -> Path:
        """A copy carrying the edit, plus the register `copy_tree` leaves out.

        `Reconciliation.copy_tree` copies what `check` reads, and `check` never
        reads the coverage register. `reconcile` does, because rebinding it is
        the sixth pass, so it has to be there for the command to be exercised
        at all.
        """
        tree = self.work.copy_tree(scratch)
        register = self.prover.COVERAGE
        (tree / register).parent.mkdir(parents=True, exist_ok=True)
        (tree / register).write_bytes((ROOT / register).read_bytes())
        self.checker.write_confined_atomic(tree, self.work.source_path, edited)
        return tree

    def test_reconcile_brings_an_appended_out_of_span_edit_back_to_accepted(self):
        """The demo path's second and third commands, in one case.

        An appended edit moves the whole-file digest and no recorded offset.
        The six passes are applied to the tree itself, and `check` then accepts
        it. Without the command the same tree refuses at
        `WAI-E-DIGEST.SOURCE`, which is what
        `test_reconcile_is_what_makes_the_difference` holds separately.
        """
        with tempfile.TemporaryDirectory() as scratch:
            tree = self.live_copy(
                Path(scratch),
                self.work.edited_source(self.prover.AFTER_SPAN_PLACEMENT),
            )
            # Before, so the case cannot pass because the edit was harmless.
            exit_code, records = self.work.check(tree)
            self.assertEqual(2, exit_code)
            self.assertEqual(
                {
                    "code": "WAI-E-DIGEST.SOURCE",
                    "node_path": f"$.fixtures.{self.prover.SUBJECT}.source.sha256",
                },
                {
                    "code": self.work.refusals(records)[0].get("code"),
                    "node_path": self.work.refusals(records)[0].get("node_path"),
                },
            )

            live = self.prover.LiveReconciliation(tree, checker=self.checker)
            result = live.apply()

            self.assertEqual(
                [
                    "manifest-source",
                    "model",
                    "source-spans",
                    "compact",
                    "manifest-artifacts",
                    self.prover.UNOBSERVED_PASS,
                ],
                result["applied"],
            )
            exit_code, _ = self.work.check(tree)
            self.assertEqual(0, exit_code)

    def test_reconcile_refuses_an_edit_inside_the_reviewed_span(self):
        """Changed reviewed bytes require restoration or separate new authority.

        Disabled historical evidence is not a recovery gate, so the refusal
        cannot direct the caller to a generator that is itself disabled.
        """
        with tempfile.TemporaryDirectory() as scratch:
            tree = self.live_copy(Path(scratch), self.work.in_span_source())
            live = self.prover.LiveReconciliation(tree, checker=self.checker)
            with self.assertRaises(self.prover.ProverError) as raised:
                live.apply()
            message = str(raised.exception)
            self.assertIn("reviewed-span digest", message)
            self.assertIn("Restore the exact reviewed bytes", message)
            self.assertIn("separate authority", message)
            self.assertNotIn("agent_instruction.py measure", message)
            self.assertIn("1192", message)

            # And it refused before writing: the tree is exactly as unreconciled
            # as it was, which is the difference between a refusal and a
            # half-applied reconciliation.
            manifest = self.checker.load_canonical_record(
                self.checker.read_confined(tree, self.prover.MANIFEST)
            )
            entry = next(
                item for item in manifest["fixtures"]
                if item["id"] == self.prover.SUBJECT
            )
            self.assertEqual(self.work.old_digest, entry["source"]["sha256"])

    def test_reconcile_rebinds_the_coverage_register(self):
        """The sixth pass, which `agent_instruction.py check` cannot see.

        `check` is green without it and `tests/test_agent_instruction.py` is
        not, which is why the demo path ends in the suite rather than in the
        checker. Asserted against the register's own bytes rather than against
        the command's report, so a report that claimed the pass without doing
        it fails here.
        """
        with tempfile.TemporaryDirectory() as scratch:
            tree = self.live_copy(
                Path(scratch),
                self.work.edited_source(self.prover.AFTER_SPAN_PLACEMENT),
            )
            before = json.loads((tree / self.prover.COVERAGE).read_text())["agent_instruction"]
            live = self.prover.LiveReconciliation(tree, checker=self.checker)
            result = live.apply()
            after = json.loads((tree / self.prover.COVERAGE).read_text())["agent_instruction"]

            self.assertIn(self.prover.MANIFEST, result["coverage_rebound"])
            self.assertNotEqual(before["manifest"]["sha256"], after["manifest"]["sha256"])
            self.assertEqual(
                self.prover.digest(self.checker.read_confined(tree, self.prover.MANIFEST)),
                after["manifest"]["sha256"],
            )
            for entry in after["fixtures"]:
                self.assertEqual(
                    self.prover.digest(self.checker.read_confined(tree, entry["path"])),
                    entry["sha256"],
                    entry["path"],
                )

    def test_reconcile_opens_no_socket_and_runs_no_model(self):
        """Asserted, not observed.

        Two guards, because one covers what this process does and the other
        covers what it starts. Any `AF_INET` or `AF_INET6` socket constructed
        during the reconciliation fails the case, and every subprocess the
        command spawns is recorded and checked: the only checker verb it may
        reach for is `format`, so `measure` and `parity` cannot be smuggled in
        behind a passing reconciliation.
        """
        import socket as socket_module

        spawned: list[list[str]] = []
        opened: list[int] = []
        read_paths: list[str] = []
        real_socket_init = socket_module.socket.__init__
        real_run = self.prover.subprocess.run
        real_read_confined = self.checker.read_confined

        def guarded_init(instance, family=socket_module.AF_INET, *args, **kwargs):
            if family in (socket_module.AF_INET, socket_module.AF_INET6):
                opened.append(int(family))
            return real_socket_init(instance, family, *args, **kwargs)

        def recording_run(arguments, *args, **kwargs):
            spawned.append([str(item) for item in arguments])
            return real_run(arguments, *args, **kwargs)

        def recording_read_confined(root, relative, *args, **kwargs):
            read_paths.append(str(relative))
            return real_read_confined(root, relative, *args, **kwargs)

        with tempfile.TemporaryDirectory() as scratch:
            tree = self.live_copy(
                Path(scratch),
                self.work.edited_source(self.prover.AFTER_SPAN_PLACEMENT),
            )
            socket_module.socket.__init__ = guarded_init
            self.prover.subprocess.run = recording_run
            self.checker.read_confined = recording_read_confined
            try:
                self.prover.LiveReconciliation(tree, checker=self.checker).apply()
            finally:
                socket_module.socket.__init__ = real_socket_init
                self.prover.subprocess.run = real_run
                self.checker.read_confined = real_read_confined

        self.assertEqual([], opened, "the reconciliation opened an internet socket")
        self.assertNotIn(self.prover.MEASUREMENT, read_paths)
        self.assertNotIn(self.prover.PARITY, read_paths)
        self.assertTrue(spawned, "the reconciliation spawned nothing, so nothing was checked")
        for arguments in spawned:
            self.assertNotIn("measure", arguments)
            self.assertNotIn("parity", arguments)
            self.assertIn("format", arguments)

    def test_an_interrupted_reconciliation_refuses_and_names_its_recovery(self):
        """The six passes are not one transaction, and the refusal says so.

        Each write is atomic on its own, so no artefact is left half-written.
        The sequence is not, so a run killed between two passes leaves an
        artefact rewritten and the manifest still recording the old digest.
        Re-running stops on that artefact, which is indistinguishable from drift
        the tool refuses on purpose. Recorded as a round finding rather than
        removed: what the refusal has to do is name both causes and the one
        command that recovers, which is what this pins.
        """
        with tempfile.TemporaryDirectory() as scratch:
            tree = self.live_copy(
                Path(scratch),
                self.work.edited_source(self.prover.AFTER_SPAN_PLACEMENT),
            )
            # A kill after the model pass and before the manifest pass.
            live = self.prover.LiveReconciliation(tree, checker=self.checker)
            relative = live.fixture["artifacts"]["model"]["path"]
            raw = self.checker.read_confined(tree, relative)
            self.checker.write_confined_atomic(
                tree,
                relative,
                raw.replace(live.old_digest.encode("ascii"), live.new_digest.encode("ascii")),
            )

            with self.assertRaises(self.prover.ProverError) as raised:
                self.prover.LiveReconciliation(tree, checker=self.checker)
            message = str(raised.exception)
            self.assertIn("interrupted", message)
            self.assertIn("git checkout --", message)
            self.assertIn(self.prover.FIXTURE_ROOT, message)
            self.assertIn(self.prover.COVERAGE, message)
