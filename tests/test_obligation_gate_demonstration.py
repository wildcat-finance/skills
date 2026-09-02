#!/usr/bin/env python3
"""The Step 7 demonstration record must recompute from the tree it describes.

Issue #884 is about obligations that stay green while nothing evaluates the
promised fact.  A demonstration record that merely asserts counts, specimens
and gate coverage in prose would reproduce that defect one level up: the
numbers would drift the moment an obligation, relation, history row or
evaluation case moved, and no gate would notice.

So every recomputable claim in
``docs/promise-machine/obligation-gates/demonstration-run.json`` is checked
here against its live source: the authored law's markers, the obligation
registry, the checker's own reported counts, the declared history and
upstream-provenance case sets, the committed evaluation run, the check map,
and the named test methods in the contract suite.  Recorded observations that
no local input can recompute -- the command exit statuses of one run on one
host -- are held to their declared shape and are never read here as proof.

The one structural claim worth stating separately: the ten issue-listed gate
classes partition the eighteen registry rows exactly.  A new obligation marker
that nobody assigns to a gate class fails this module rather than landing
unevaluated.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "scripts" / "promise_machine.py"
VENDORED_VERIFIER = ROOT / "scripts" / "verify_vendored_provenance.py"
LAW = ROOT / "PROMISE_MACHINE.md"
REGISTRY = ROOT / "tests" / "promise_machine_obligations.json"
CONTRACT_TEST = ROOT / "tests" / "test_promise_machine_contract.py"
HISTORY_CASES = ROOT / "tests" / "fixtures" / "promise-machine" / "history" / "cases.json"
PROVENANCE_CASES = (
    ROOT / "tests" / "fixtures" / "promise-machine" / "upstream-provenance" / "cases.json"
)
DEMONSTRATION = (
    ROOT / "docs" / "promise-machine" / "obligation-gates" / "demonstration-run.json"
)
EVALUATION_RUN = (
    ROOT / "docs" / "promise-machine" / "obligation-gates" / "evaluation-run.json"
)
EVIDENCE_REPORT = (
    ROOT / "docs" / "promise-machine" / "obligation-gates" / "demonstration-evidence.md"
)

MARKER = re.compile(r"^<!-- promise-machine-obligation: id=([a-z0-9-]+) -->$", re.MULTILINE)
FINDING_CODE = re.compile(r"\b(?:PM|PV)\d{3}\b")

RECORD_FIELDS = {
    "contract",
    "counts",
    "date",
    "evidence_classes",
    "gate_classes",
    "host",
    "inputs",
    "issue",
    "non_goals",
    "commands",
    "schema",
    "step",
    "unknowns",
}
GATE_CLASS_FIELDS = {
    "blocked_transitions",
    "checker_function",
    "class",
    "disposition",
    "evaluator",
    "finding_codes",
    "issue_obligation",
    "marker_backed",
    "negative_cases",
    "network_findings",
    "obligation_ids",
    "recovery_actions",
    "specimens",
    "tests",
}
COMMAND_FIELDS = {"command", "evidence_class", "exit_status", "stage"}
ISSUE_GATE_CLASSES = (
    "result-binding",
    "level-3-separation",
    "exception-resolution",
    "composition",
    "field-semantics",
    "upstream-provenance",
    "refusal-shape",
    "unknown-evidence",
    "id-history",
    "no-side-effect",
)

# Where each ``negative_cases.kind`` gets its count.  The classification is
# closed: a kind in none of these three groups fails rather than passing as an
# unchecked declaration.
NEGATIVE_CASE_COUNT_SOURCES = {
    "runtime binding rows": "runtime_rows",
    "composition relations": "composition_relations",
    "declared provenance cases": "provenance_rows",
    "declared history cases": "history_cases",
}
NEGATIVE_CASE_SPECIMEN_KINDS = frozenset(
    {
        "law obligation specimens",
        "exception specimen",
        "finding specimen",
        "consequence specimen",
        "import specimen",
    }
)
# The one count no local input recomputes, bound to the one class entitled to
# it.  Level-3 separation is exercised by four consequence specimens that no
# registry row, declared inventory or checker count enumerates, so it stays
# declared evidence and is held only to the specimens its own rows name.  The
# binding is the point: an unbound declared kind is a door any class can walk
# through to escape recomputation entirely.
NEGATIVE_CASE_DECLARED_KINDS = {"consequence specimens": "level-3-separation"}

# Every ``counts`` key appears once in the evidence report's own table, so the
# half a reader quotes cannot drift away from the half the digests bind.
REPORT_COUNT_SUBJECTS = {
    "Obligation markers in `PROMISE_MACHINE.md`": "obligation_markers",
    "Obligation registry rows": "registry_rows",
    "Distinct negative specimen files": "negative_specimens",
    "Runtime binding rows": "runtime_rows",
    "Composition relations": "composition_relations",
    "Promise-id history rows": "history_rows",
    "Active history ids": "active_history_ids",
    "Declared history cases": "history_cases",
    "Declared upstream-provenance cases": "provenance_rows",
    "Evaluation cases": "evaluation_cases",
    "Evaluation outcomes": "evaluation_outcomes",
    "Issue-listed gate classes": "gate_classes",
    "Declared promises": "promises",
    "Coverage rows": "coverage_rows",
    "Selected repository scopes": "repository_scopes",
    "Selected repository checks": "repository_checks",
}
REPORT_COUNT_ROW = re.compile(r"^\| ([^|]+?) \| (\d+) \|$", re.MULTILINE)
REPORT_INPUT_ROW = re.compile(
    r"^- `([^`]+)`, SHA-256 `([0-9a-f]{64})`, (\d+) bytes$", re.MULTILINE
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def input_paths(inputs) -> list[str]:
    """Every ``inputs[].path``, refused before it is hashed rather than after.

    Two consumers put these values in a set and in a mapping key, where a
    list-valued path raises ``TypeError: unhashable type`` before any
    assertion runs.  The record deserves the same stable refusal there as it
    gets from ``confined``.
    """
    values = []
    for entry in inputs:
        value = entry["path"]
        if not isinstance(value, str):
            raise AssertionError(f"path is not a string: {value!r}")
        values.append(value)
    return values


def confined(relative: str) -> Path:
    """Resolve a record-supplied path under the repository root, or refuse it.

    ``ROOT / "/etc/passwd"`` is ``/etc/passwd``: pathlib discards the left side
    of the join the moment the right side is absolute.  Every path the record
    names is repository-relative by contract, and a digest mismatch afterwards
    would not undo a read that had already left the checkout, so the contract
    is checked here rather than assumed.

    The type check comes first because a refusal has to stay a refusal.  A
    list, integer, dict or bytes value reaching ``str`` methods raises
    ``AttributeError`` or ``TypeError``, which arrives as an error rather than
    an assertion failure, and a report mixing the two classifies
    ``inconclusive`` instead of naming the bad record.
    """
    if not isinstance(relative, str):
        raise AssertionError(f"path is not a string: {relative!r}")
    if not relative or relative.strip() != relative:
        raise AssertionError(f"path is empty or padded: {relative!r}")
    if relative.startswith("/") or "\\" in relative or "\x00" in relative:
        raise AssertionError(f"path is not repository-relative: {relative!r}")
    candidate = ROOT / relative
    if candidate.is_symlink():
        raise AssertionError(f"path is a symlink: {relative!r}")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(ROOT.resolve()):
        raise AssertionError(f"path escapes the repository root: {relative!r}")
    if not resolved.is_file():
        raise AssertionError(f"path is not a regular file: {relative!r}")
    return resolved


def checker_counts() -> dict:
    completed = subprocess.run(
        [sys.executable, str(CHECKER), "check", "--json"],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        shell=False,
        check=False,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stdout + completed.stderr)
    return json.loads(completed.stdout)["counts"]


def contract_test_methods() -> set[str]:
    source = CONTRACT_TEST.read_text(encoding="utf-8")
    tree = ast.parse(source)
    names = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for member in node.body:
            if isinstance(member, ast.FunctionDef) and member.name.startswith("test"):
                names.add(f"{node.name}.{member.name}")
    return names


class DemonstrationRecordTests(unittest.TestCase):
    """Every recomputable field of the record is rebuilt from its source."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.record = load_json(DEMONSTRATION)
        cls.registry = load_json(REGISTRY)
        cls.counts = checker_counts()

    def test_record_declares_the_fixed_contract_and_closed_shape(self) -> None:
        self.assertEqual(self.record["contract"], "promise-machine/v1")
        self.assertEqual(
            self.record["schema"], "promise-machine-obligation-demonstration/v1"
        )
        self.assertEqual(self.record["issue"], "wildcat-finance/skills#884")
        self.assertEqual(self.record["step"], 7)
        self.assertEqual(set(self.record), RECORD_FIELDS)

    def test_marker_registry_and_specimen_counts_recompute(self) -> None:
        markers = MARKER.findall(LAW.read_text(encoding="utf-8"))
        rows = self.registry["obligations"]
        counts = self.record["counts"]
        self.assertEqual(counts["obligation_markers"], len(markers))
        self.assertEqual(counts["registry_rows"], len(rows))
        self.assertEqual(len(markers), len(set(markers)))
        self.assertEqual(sorted(markers), sorted(row["id"] for row in rows))
        self.assertEqual(
            counts["negative_specimens"], len({row["specimen"] for row in rows})
        )

    def test_checker_reported_counts_recompute(self) -> None:
        counts = self.record["counts"]
        for field, reported in (
            ("runtime_rows", "runtime_bindings"),
            ("composition_relations", "composition_relations"),
            ("history_rows", "history_entries"),
            ("active_history_ids", "active_history_ids"),
            ("evaluation_cases", "evaluation_cases"),
            ("evaluation_outcomes", "evaluation_outcomes"),
            ("promises", "promises"),
            ("coverage_rows", "coverage_rows"),
        ):
            with self.subTest(field=field):
                self.assertEqual(counts[field], self.counts[reported])

    def test_declared_case_set_counts_recompute(self) -> None:
        counts = self.record["counts"]
        self.assertEqual(counts["provenance_rows"], len(load_json(PROVENANCE_CASES)["cases"]))
        self.assertEqual(counts["history_cases"], len(load_json(HISTORY_CASES)["cases"]))

    def test_recorded_evaluation_counts_match_the_committed_run(self) -> None:
        run = load_json(EVALUATION_RUN)
        counts = self.record["counts"]
        self.assertEqual(counts["evaluation_cases"], run["counts"]["cases"])
        self.assertEqual(counts["evaluation_outcomes"], run["counts"]["outcomes"])
        self.assertEqual(run["counts"]["failed"], 0)
        self.assertEqual(run["domain_evidence"], "not-supplied")

    def test_selected_repository_check_counts_recompute(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import run_checks
        finally:
            sys.path.pop(0)
        check_map = run_checks.load_map(ROOT)
        selection = run_checks.build_selection(ROOT, check_map, (), None, True, observed=[])
        counts = self.record["counts"]
        self.assertEqual(counts["repository_scopes"], len(selection.scopes))
        self.assertEqual(
            counts["repository_checks"],
            len(run_checks.selected_checks(check_map, selection)),
        )

    def test_every_named_input_digest_recomputes(self) -> None:
        self.assertTrue(self.record["inputs"])
        for entry in self.record["inputs"]:
            with self.subTest(path=entry["path"]):
                self.assertEqual(set(entry), {"bytes", "path", "sha256"})
                raw = confined(entry["path"]).read_bytes()
                self.assertEqual(entry["bytes"], len(raw))
                self.assertEqual(entry["sha256"], hashlib.sha256(raw).hexdigest())

    def test_the_law_and_registry_are_named_inputs(self) -> None:
        named = set(input_paths(self.record["inputs"]))
        for required in (
            "PROMISE_MACHINE.md",
            "tests/promise_machine_obligations.json",
            "tests/promise_machine_id_history.json",
            "tests/fixtures/promise-machine/composition/cases.json",
            "docs/promise-machine/obligation-gates/evaluation-run.json",
        ):
            with self.subTest(path=required):
                self.assertIn(required, named)


class GateClassCoverageTests(unittest.TestCase):
    """The ten issue-listed classes cover the registry with nothing left over."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.record = load_json(DEMONSTRATION)
        cls.registry = load_json(REGISTRY)
        cls.rows = {row["id"]: row for row in cls.registry["obligations"]}
        cls.methods = contract_test_methods()

    def test_the_ten_issue_classes_appear_once_in_their_recorded_order(self) -> None:
        observed = tuple(entry["class"] for entry in self.record["gate_classes"])
        self.assertEqual(observed, ISSUE_GATE_CLASSES)
        self.assertEqual(self.record["counts"]["gate_classes"], len(ISSUE_GATE_CLASSES))

    def test_each_gate_class_declares_its_closed_shape(self) -> None:
        for entry in self.record["gate_classes"]:
            with self.subTest(gate_class=entry["class"]):
                self.assertEqual(set(entry), GATE_CLASS_FIELDS)
                self.assertEqual(set(entry["negative_cases"]), {"count", "kind"})
                self.assertGreater(entry["negative_cases"]["count"], 0)
                self.assertTrue(entry["evaluator"].startswith("python3 "))
                self.assertEqual(entry["disposition"], "refused-with-declared-finding")
                self.assertTrue(entry["finding_codes"])
                self.assertTrue(entry["tests"])

    def test_the_gate_classes_partition_every_registry_row(self) -> None:
        claimed: list[str] = []
        for entry in self.record["gate_classes"]:
            claimed.extend(entry["obligation_ids"])
        self.assertEqual(len(claimed), len(set(claimed)), "an obligation is claimed twice")
        self.assertEqual(sorted(claimed), sorted(self.rows))

    def test_marker_backing_matches_the_declared_obligation_ids(self) -> None:
        for entry in self.record["gate_classes"]:
            with self.subTest(gate_class=entry["class"]):
                self.assertEqual(entry["marker_backed"], bool(entry["obligation_ids"]))

    def test_each_claimed_row_supplies_its_specimen_transition_and_recovery(self) -> None:
        for entry in self.record["gate_classes"]:
            with self.subTest(gate_class=entry["class"]):
                rows = [self.rows[o] for o in entry["obligation_ids"]]
                self.assertEqual(
                    entry["specimens"], sorted({row["specimen"] for row in rows})
                )
                self.assertEqual(
                    entry["blocked_transitions"],
                    sorted({row["blocked_transition"] for row in rows}),
                )
                self.assertEqual(
                    entry["recovery_actions"], sorted({row["recovery"] for row in rows})
                )
                for specimen in entry["specimens"]:
                    confined(specimen)

    def test_every_negative_case_count_is_joined_to_its_source(self) -> None:
        """A per-class exercise count must recompute, not merely be positive.

        ``negative_cases.count`` is this record's claim about how much each
        gate class actually exercises, and four of the ten name inventories
        ``counts`` already recomputes from the live tree.  Asserting only that
        they were positive left every one of them free: the composition class
        could claim ninety-nine relations, or the result-binding class one
        runtime row, and this module stayed green.  That is the
        declaration-only defect #884 exists to close, reproduced one level up
        in the record that reports on closing it.
        """
        counts = self.record["counts"]
        for entry in self.record["gate_classes"]:
            kind = entry["negative_cases"]["kind"]
            count = entry["negative_cases"]["count"]
            with self.subTest(gate_class=entry["class"], kind=kind):
                if kind in NEGATIVE_CASE_COUNT_SOURCES:
                    self.assertEqual(count, counts[NEGATIVE_CASE_COUNT_SOURCES[kind]])
                elif kind in NEGATIVE_CASE_SPECIMEN_KINDS:
                    self.assertEqual(count, len(entry["specimens"]))
                else:
                    self.assertIn(
                        kind,
                        NEGATIVE_CASE_DECLARED_KINDS,
                        "an unclassified negative-case kind recomputes from nothing",
                    )
                    self.assertEqual(
                        NEGATIVE_CASE_DECLARED_KINDS[kind],
                        entry["class"],
                        "only the class entitled to this kind may declare it",
                    )
                    self.assertGreaterEqual(count, len(entry["specimens"]))

    def test_every_recorded_finding_code_can_be_emitted_by_the_checker(self) -> None:
        emitted = set(FINDING_CODE.findall(CHECKER.read_text(encoding="utf-8")))
        for entry in self.record["gate_classes"]:
            for code in entry["finding_codes"]:
                with self.subTest(gate_class=entry["class"], code=code):
                    self.assertIn(code, emitted)

    def test_network_findings_belong_to_the_separate_upstream_verifier(self) -> None:
        """The offline core checker must not be credited with a fetched result.

        PV003 and PV004 are raised by scripts/verify_vendored_provenance.py,
        which reaches upstream. The demonstration never runs it, so a class
        that names those codes has to say they come from elsewhere rather than
        letting them read as core-checker coverage.

        The set is pinned from the other direction too: every declared
        upstream-provenance case whose finding the offline checker cannot emit
        must be named as a network finding, so a new fetched case cannot enter
        the inventory and read as covered.
        """
        offline = set(FINDING_CODE.findall(CHECKER.read_text(encoding="utf-8")))
        upstream = set(FINDING_CODE.findall(VENDORED_VERIFIER.read_text(encoding="utf-8")))
        named = set()
        for entry in self.record["gate_classes"]:
            for code in entry["network_findings"]:
                with self.subTest(gate_class=entry["class"], code=code):
                    self.assertIn(code, upstream)
                    self.assertNotIn(code, offline)
                    self.assertNotIn(code, entry["finding_codes"])
                named.add(code)
        declared = {case["expected_finding"] for case in load_json(PROVENANCE_CASES)["cases"]}
        self.assertEqual(named, declared - offline)
        self.assertTrue(named <= upstream)

    def test_a_marker_backed_class_declares_the_finding_its_rows_carry(self) -> None:
        for entry in self.record["gate_classes"]:
            if not entry["marker_backed"]:
                continue
            with self.subTest(gate_class=entry["class"]):
                declared = {self.rows[o]["finding"] for o in entry["obligation_ids"]}
                self.assertTrue(declared <= set(entry["finding_codes"]))

    def test_every_named_test_selector_exists_in_the_contract_suite(self) -> None:
        for entry in self.record["gate_classes"]:
            for selector in entry["tests"]:
                with self.subTest(gate_class=entry["class"], selector=selector):
                    self.assertIn(selector, self.methods)

    def test_a_class_without_a_marker_still_names_its_evaluator_and_cases(self) -> None:
        unmarked = [e for e in self.record["gate_classes"] if not e["marker_backed"]]
        self.assertEqual(
            sorted(e["class"] for e in unmarked), ["id-history", "upstream-provenance"]
        )
        for entry in unmarked:
            with self.subTest(gate_class=entry["class"]):
                self.assertEqual(entry["specimens"], [])
                self.assertEqual(entry["blocked_transitions"], [])
                self.assertEqual(entry["recovery_actions"], [])
                self.assertTrue(entry["checker_function"].startswith("check_"))


class RecordedObservationTests(unittest.TestCase):
    """Observations no local input can recompute stay shaped and labelled."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.record = load_json(DEMONSTRATION)

    def test_every_command_is_a_labelled_recorded_observation(self) -> None:
        commands = self.record["commands"]
        self.assertTrue(commands)
        for entry in commands:
            with self.subTest(stage=entry.get("stage")):
                self.assertEqual(set(entry), COMMAND_FIELDS)
                self.assertTrue(entry["command"].strip())
                self.assertTrue(entry["stage"].strip())
                self.assertEqual(entry["evidence_class"], "recorded")
                self.assertIsInstance(entry["exit_status"], int)
        stages = [entry["stage"] for entry in commands]
        self.assertEqual(len(stages), len(set(stages)), "a stage label is reused")

    def test_the_exit_clause_commands_are_all_present(self) -> None:
        commands = {entry["command"] for entry in self.record["commands"]}
        for required in (
            'test -z "$(git status --porcelain)"',
            "python3 scripts/promise_machine.py check",
            "python3 scripts/promise_machine.py coverage --check",
            "python3 scripts/promise_machine.py sync --check",
            "python3 scripts/portable_promise_machine.py check",
            "python3 plugins/horos/skills/horos/scripts/horos.py scan . --write",
            "python3 scripts/run_checks.py --full --jobs 12 --report .reports/issue-884-full.json",
            "python3 plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py --check .",
            "python3 tests/run_tests.py --elenchus-report .elenchus/promise-obligations-step-7.json",
        ):
            with self.subTest(command=required):
                self.assertIn(required, commands)

    def test_evidence_classes_unknowns_and_non_goals_are_stated(self) -> None:
        for field in ("unknowns", "non_goals"):
            with self.subTest(field=field):
                values = self.record[field]
                self.assertTrue(values)
                for value in values:
                    self.assertIsInstance(value, str)
                    self.assertTrue(value.strip())
        classes = self.record["evidence_classes"]
        self.assertEqual(sorted(classes), ["checked", "declared", "recorded"])
        for name, description in classes.items():
            with self.subTest(evidence_class=name):
                self.assertIsInstance(description, str)
                self.assertTrue(description.strip())

    def test_the_host_observation_is_named_rather_than_generalised(self) -> None:
        host = self.record["host"]
        self.assertEqual(set(host), {"machine", "platform", "python"})
        self.assertEqual(host["python"], (ROOT / ".python-version").read_text().strip())

    def test_the_evidence_report_ships_beside_the_record(self) -> None:
        self.assertTrue(EVIDENCE_REPORT.is_file())
        text = EVIDENCE_REPORT.read_text(encoding="utf-8")
        self.assertIn("demonstration-run.json", text)
        for entry in self.record["gate_classes"]:
            with self.subTest(gate_class=entry["class"]):
                self.assertIn(entry["class"], text)

    def test_the_report_count_table_repeats_every_recorded_count(self) -> None:
        """The human half of the record must not drift away from the bound half.

        ``demonstration-evidence.md`` opens by saying every count in the run
        record recomputes in this module.  Nothing joined the report's own
        tables to that record, so it could say thirty-six runtime binding rows
        against the record's thirty-five and stay green -- and the report is
        the half a reader quotes.  The subject map is total in both
        directions, so a new count with no row, and a row naming no count,
        both fail.
        """
        text = EVIDENCE_REPORT.read_text(encoding="utf-8")
        observed = {subject: int(n) for subject, n in REPORT_COUNT_ROW.findall(text)}
        self.assertEqual(set(observed), set(REPORT_COUNT_SUBJECTS))
        self.assertEqual(set(REPORT_COUNT_SUBJECTS.values()), set(self.record["counts"]))
        for subject, key in REPORT_COUNT_SUBJECTS.items():
            with self.subTest(subject=subject):
                self.assertEqual(observed[subject], self.record["counts"][key])

    def test_the_report_gate_table_repeats_every_recorded_gate_class(self) -> None:
        """Rows, negative cases and test counts are joined cell by cell.

        The report's gate table restates three numbers the record already
        carries.  Checking only that each class name appeared somewhere in the
        prose let all three drift silently.
        """
        text = EVIDENCE_REPORT.read_text(encoding="utf-8")
        for entry in self.record["gate_classes"]:
            with self.subTest(gate_class=entry["class"]):
                pattern = re.compile(
                    r"^\| `" + re.escape(entry["class"]) + r"` \|(.+)\|$", re.MULTILINE
                )
                match = pattern.search(text)
                self.assertIsNotNone(match, "the class has no row in the report")
                cells = [cell.strip() for cell in match.group(1).split("|")]
                self.assertEqual(len(cells), 6, cells)
                ids = entry["obligation_ids"]
                self.assertEqual(cells[2], str(len(ids)) if ids else "none")
                negative = entry["negative_cases"]
                # Equality, not containment: "35 runtime binding rows" contains
                # "5 runtime binding rows", so a substring check let the report
                # differ from the record by any leading digits.
                self.assertEqual(cells[3], f"{negative['count']} {negative['kind']}")
                self.assertEqual(cells[5], str(len(entry["tests"])))

    def test_the_report_repeats_every_bound_input_digest(self) -> None:
        """A quoted digest is evidence, so it is compared rather than trusted."""
        text = EVIDENCE_REPORT.read_text(encoding="utf-8")
        observed = {
            path: (digest, int(size))
            for path, digest, size in REPORT_INPUT_ROW.findall(text)
        }
        recorded = {
            path: (entry["sha256"], entry["bytes"])
            for path, entry in zip(
                input_paths(self.record["inputs"]), self.record["inputs"]
            )
        }
        self.assertEqual(observed, recorded)


if __name__ == "__main__":
    unittest.main()
