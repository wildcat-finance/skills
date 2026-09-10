"""Step 7: the committed corpus-scope design record says what this run decided,
its reports are the bytes it was scored from, and the committed study and
runbook are the receipted artefacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
RECORD_DIR = PLUGIN_ROOT / "docs/corpus-scope"
RECORD = RECORD_DIR / "design-evidence.json"
REPORTS = RECORD_DIR / "reports"
RESOLVER = REPORTS / "resolve.py"
STUDY = PLUGIN_ROOT / "docs/corpus-scope-study.md"
RUNBOOK = PLUGIN_ROOT / "docs/corpus-scope-runbook.md"
WORKTREE = PLUGIN_ROOT.parents[1]
CONTROLLER = WORKTREE / ".hexaemeron"
REBUILT = "pilot-artefacts-rebuilt"

CONCERNS = {"correctness", "time", "space", "compatibility", "recovery"}
CANDIDATES = {
    "release-policy-scope",
    "admission-policy-scope",
    "permanent-seed-record",
    "widen-constant",
}
CRITERIA = {
    "release-id-declared-function",
    "scope-recorded-in-release",
    "estate-findings-admissible-without-widening",
    "foreign-ledgers-touched",
    "pilot-artefacts-rebuilt",
    "policy-bytes-added",
    "acceptance-check-ms",
    "scope-recovery-by-policy-edit",
}
REJECTED_BY = {
    "release-id-declared-function",
    "scope-recorded-in-release",
    "estate-findings-admissible-without-widening",
    "scope-recovery-by-policy-edit",
}
FAILED = {
    "release-policy-scope": set(),
    "admission-policy-scope": {"scope-recorded-in-release"},
    "permanent-seed-record": REJECTED_BY,
    "widen-constant": REJECTED_BY,
}


class CommittedDesignRecord(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(RECORD.read_text(encoding="utf-8"))

    def test_record_declares_the_protasis_schema_and_four_candidates(self) -> None:
        self.assertEqual(self.record["schema"], "protasis-design-evidence/v1")
        self.assertEqual({c["id"] for c in self.record["candidates"]}, CANDIDATES)

    def test_eight_criteria_cover_every_concern(self) -> None:
        criteria = self.record["criteria"]
        self.assertEqual({c["id"] for c in criteria}, CRITERIA)
        self.assertEqual({c["concern"] for c in criteria}, CONCERNS)
        self.assertTrue(all(c["blocks"] == "design-lock" for c in criteria))

    def test_selection_is_release_policy_scope_on_a_unique_frontier(self) -> None:
        selection = self.record["selection"]
        self.assertEqual(selection["candidate"], "release-policy-scope")
        self.assertEqual(selection["rule"], "unique-frontier")
        failed = {candidate: set() for candidate in CANDIDATES}
        for result in self.record["results"]:
            if result["state"] == "fail":
                failed[result["candidate"]].add(result["criterion"])
        self.assertEqual(failed, FAILED)

    def test_every_cell_names_a_report_whose_bytes_match_its_digest(self) -> None:
        results = self.record["results"]
        self.assertEqual(len(results), 32)
        self.assertEqual(
            {(r["candidate"], r["criterion"]) for r in results},
            {(c, k) for c in CANDIDATES for k in CRITERIA},
        )
        for result in results:
            report = result["report"]
            path = RECORD_DIR / report["path"]
            with self.subTest(report=report["path"]):
                self.assertTrue(path.is_file(), f"missing report {report['path']}")
                body = path.read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(), report["sha256"])
                document = json.loads(body)
                self.assertEqual(document["schema"], "protasis-design-report/v1")
                self.assertEqual(document["exit"], 0)
                self.assertEqual(document["candidate"], result["candidate"])
                self.assertEqual(document["criterion"], result["criterion"])
                self.assertEqual(
                    document["command"],
                    "python3 .hexaemeron/reports/resolve.py "
                    f"{result['candidate']} {result['criterion']}",
                )

    def test_the_resolver_is_committed_beside_the_reports(self) -> None:
        # The previous run's reports named a resolver nobody committed, so the
        # values could not be rerun from the repository. This one ships it.
        self.assertTrue(RESOLVER.is_file())
        source = RESOLVER.read_text(encoding="utf-8")
        for name in CANDIDATES | CRITERIA:
            with self.subTest(name=name):
                self.assertIn(f'"{name}"', source)


def scratch_directory(prefix: str = "anamnesis-s7-"):
    """Transient space under the ignored top-level tmp/, which git never sees."""
    scratch = WORKTREE / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


class ResolverReproducesTheCommittedCounts(unittest.TestCase):
    """S1-R1-01 and S1-R1-02: the committed resolver reruns to the recorded
    values from the repository root and writes into no controller state."""

    def setUp(self) -> None:
        holder = scratch_directory()
        self.addCleanup(holder.cleanup)
        self.scratch = Path(holder.name)

    def committed_value(self, candidate: str):
        report = REPORTS / f"{candidate}-{REBUILT}.json"
        return json.loads(report.read_text(encoding="utf-8"))["value"]

    def run_resolver(self, *arguments: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(RESOLVER), *arguments],
            cwd=WORKTREE, capture_output=True, text=True,
        )

    def test_the_rebuilt_counts_rerun_to_their_recorded_values(self) -> None:
        for candidate in sorted(CANDIDATES):
            out = self.scratch / f"{candidate}.json"
            with self.subTest(candidate=candidate):
                completed = self.run_resolver(candidate, REBUILT, "--out", str(out))
                self.assertEqual(completed.returncode, 0, completed.stderr)
                printed = json.loads(completed.stdout)
                written = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(printed["value"], self.committed_value(candidate))
                self.assertEqual(written, printed)
                self.assertEqual(written["schema"], "protasis-design-report/v1")

    def test_a_rerun_without_out_writes_no_report(self) -> None:
        target = CONTROLLER / "reports" / f"release-policy-scope-{REBUILT}.json"
        before = target.read_bytes() if target.is_file() else None
        completed = self.run_resolver("release-policy-scope", REBUILT)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        after = target.read_bytes() if target.is_file() else None
        self.assertEqual(after, before)
        self.assertEqual(json.loads(completed.stdout)["value"], self.committed_value("release-policy-scope"))

    def test_an_existing_out_path_is_refused_rather_than_replaced(self) -> None:
        out = self.scratch / "taken.json"
        out.write_text("{}\n", encoding="utf-8")
        completed = self.run_resolver("widen-constant", REBUILT, "--out", str(out))
        self.assertEqual(completed.returncode, 2)
        self.assertEqual(out.read_text(encoding="utf-8"), "{}\n")


class CommittedCopiesAreTheReceiptedArtefacts(unittest.TestCase):
    """Byte identity with the controller's pinned artefacts, checked where the
    controller state is this run's own and skipped everywhere else."""

    def test_committed_copies_equal_the_receipted_artefacts(self) -> None:
        pinned = CONTROLLER / "design-evidence.json"
        if not pinned.is_file():
            self.skipTest("the design record is controller state and is not always present")
        selection = json.loads(pinned.read_text(encoding="utf-8")).get("selection", {})
        if selection.get("candidate") != "release-policy-scope":
            self.skipTest("the controller state in this worktree belongs to another run")
        for committed, receipted in (
            (RECORD, pinned),
            (STUDY, CONTROLLER / "study.md"),
            (RUNBOOK, CONTROLLER / "runbook.md"),
        ):
            with self.subTest(path=committed.name):
                self.assertEqual(committed.read_bytes(), receipted.read_bytes())


if __name__ == "__main__":
    unittest.main()
