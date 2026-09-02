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

# Every leaf of the record and the type it must carry.  The closed key sets
# above say which fields exist and say nothing about what they hold, so a
# wrong-typed value reached a ``str`` method, a comparison or a hash and raised
# there.  That arrives as an error rather than an assertion failure, and a
# report mixing the two classifies ``inconclusive`` instead of naming the bad
# field.  Typing one field in one helper left the class alive everywhere else.
RECORD_SHAPE = {
    "contract": str,
    "schema": str,
    "issue": str,
    "date": str,
    "step": int,
    "counts": {"*": int},
    "host": {"*": str},
    "evidence_classes": {"*": str},
    "unknowns": [str],
    "non_goals": [str],
    "inputs": [{"path": str, "sha256": str, "bytes": int}],
    "commands": [
        {"command": str, "stage": str, "evidence_class": str, "exit_status": int}
    ],
    "gate_classes": [
        {
            "class": str,
            "issue_obligation": str,
            "evaluator": str,
            "checker_function": str,
            "disposition": str,
            "marker_backed": bool,
            "obligation_ids": [str],
            "specimens": [str],
            "blocked_transitions": [str],
            "recovery_actions": [str],
            "finding_codes": [str],
            "network_findings": [str],
            "tests": [str],
            "negative_cases": {"count": int, "kind": str},
        }
    ],
}


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def typed(value, shape, where: str) -> None:
    """Walk one record value against its declared shape, naming what fails.

    ``"*"`` as a mapping's only key means arbitrary string keys carrying that
    value type.  ``bool`` is excluded from ``int`` deliberately: Python makes
    ``True`` an integer, so a boolean where an exit status or a count belongs
    would otherwise pass an ``isinstance`` check unnoticed.

    Every failure here is an ``AssertionError`` raised from ``setUp``, which
    unittest records as a failure rather than an error.  That is the whole
    point: the module refuses a malformed record by naming the field, instead
    of scattering ``AttributeError`` and ``unhashable type`` across whichever
    consumers happen to touch it first.
    """
    if isinstance(shape, dict):
        if not isinstance(value, dict):
            raise AssertionError(f"{where} is {type(value).__name__}, expected an object")
        if "*" in shape:
            for key, item in value.items():
                if not isinstance(key, str):
                    raise AssertionError(f"{where} has a non-string key {key!r}")
                typed(item, shape["*"], f"{where}.{key}")
            return
        if set(value) != set(shape):
            raise AssertionError(
                f"{where} keys are {sorted(value)}, expected {sorted(shape)}"
            )
        for key, sub in shape.items():
            typed(value[key], sub, f"{where}.{key}")
        return
    if isinstance(shape, list):
        if not isinstance(value, list):
            raise AssertionError(f"{where} is {type(value).__name__}, expected a list")
        for index, item in enumerate(value):
            typed(item, shape[0], f"{where}[{index}]")
        return
    if shape is int and isinstance(value, bool):
        raise AssertionError(f"{where} is a bool, expected an int")
    if not isinstance(value, shape):
        raise AssertionError(
            f"{where} is {type(value).__name__}, expected {shape.__name__}"
        )


def claimed_rows(rows: dict, entry: dict) -> list[dict]:
    """Registry rows for one class's ids, refused by assertion when absent.

    Indexing the registry directly turned an unknown obligation id into a
    ``KeyError`` in two consumers, so a bad record produced one failure and two
    errors.  The partition test still owns the message about what is wrong; this
    only keeps the other readers from erroring before it can say so.
    """
    missing = [o for o in entry["obligation_ids"] if o not in rows]
    if missing:
        raise AssertionError(f"{entry['class']} claims unknown obligation ids: {missing}")
    return [rows[o] for o in entry["obligation_ids"]]


def emittable_finding_codes(path: Path) -> set[str]:
    """Finding codes a script can actually emit, read from its live literals.

    A regex over the whole source counts a code named in a comment or a
    docstring, so the record could claim a code the checker cannot raise and
    this module would still pass it -- the declaration-only defect #884 exists
    to close, in the guard that reports on closing it.  Comments are absent
    from the AST entirely; docstrings are the first statement of a module,
    class or function and are excluded here by position.
    """
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    docstrings = set()
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if not isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            docstrings.add(id(body[0].value))
    codes: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstrings
        ):
            codes.update(FINDING_CODE.findall(node.value))
    return codes


def checker_functions() -> set[str]:
    """Every function the checker defines, read statically from its source."""
    tree = ast.parse(CHECKER.read_text(encoding="utf-8"))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def checker_only_values() -> set[str]:
    """The exact ``--only`` values the checker accepts, from its own literal.

    Read from the source rather than restated here, so the two cannot drift.
    If the checker stops declaring them where this reads them, the helper
    refuses instead of quietly returning an empty set that would accept
    anything.
    """
    source = CHECKER.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        segment = ast.get_source_segment(source, node) or ""
        if "unsupported --only value(s)" not in segment:
            continue
        for sub in ast.walk(node):
            if (
                isinstance(sub, ast.Assign)
                and len(sub.targets) == 1
                and isinstance(sub.targets[0], ast.Name)
                and sub.targets[0].id == "allowed"
                and isinstance(sub.value, ast.Set)
            ):
                return {e.value for e in sub.value.elts if isinstance(e, ast.Constant)}
    raise AssertionError(
        "the checker no longer declares its --only values where this reads them"
    )


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

    def setUp(self) -> None:
        typed(self.record, RECORD_SHAPE, "record")

    def test_every_record_field_carries_its_declared_type(self) -> None:
        """The declared shape is bound to the closed key sets it types.

        Two declarations of the same fields drift, so the shape is checked
        against the key sets rather than maintained beside them: a field added
        to one and not the other fails here.
        """
        self.assertEqual(set(RECORD_SHAPE), RECORD_FIELDS)
        self.assertEqual(set(RECORD_SHAPE["gate_classes"][0]), GATE_CLASS_FIELDS)
        self.assertEqual(set(RECORD_SHAPE["commands"][0]), COMMAND_FIELDS)

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

    def setUp(self) -> None:
        typed(self.record, RECORD_SHAPE, "record")

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
                rows = claimed_rows(self.rows, entry)
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
        """A claimed code has to be a live literal, not a mention in a comment.

        The scan was a regex over the whole checker source, so ``# PM999`` in a
        comment satisfied a record claiming ``PM999`` as a code that gate
        emits.  That is a declaration nothing evaluates, which is the defect
        this whole record exists to demonstrate closed.
        """
        emitted = emittable_finding_codes(CHECKER)
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
        offline = emittable_finding_codes(CHECKER)
        upstream = emittable_finding_codes(VENDORED_VERIFIER)
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
                declared = {row["finding"] for row in claimed_rows(self.rows, entry)}
                self.assertTrue(declared <= set(entry["finding_codes"]))

    def test_every_recorded_pointer_resolves_where_the_record_points(self) -> None:
        """``checker_function`` and ``evaluator`` are pointers, so they resolve.

        Both were held to a prefix and nothing more, and ``checker_function``
        was read at all only for the two classes without a marker, so eight of
        the ten went unread.  Renaming every one of them to a function the
        checker does not define left this module green, as did pointing the
        evaluator at a script that does not exist, at an unsupported ``--only``
        value, or at the real checker with an extra flag that makes it exit 2.

        The evaluator column is not decoration.  The evidence report's ``When a
        gate stops the line`` section sends a reader to it by name, and the
        report join added in the previous round only made both halves agree on
        whatever the record said -- including a command that does not run.
        """
        defined = checker_functions()
        allowed = checker_only_values()
        self.assertTrue(allowed)
        for entry in self.record["gate_classes"]:
            with self.subTest(gate_class=entry["class"]):
                self.assertIn(entry["checker_function"], defined)
                parts = entry["evaluator"].split()
                self.assertEqual(len(parts), 5, parts)
                self.assertEqual(parts[0], "python3")
                self.assertEqual(confined(parts[1]), CHECKER)
                self.assertEqual(parts[2], "check")
                self.assertEqual(parts[3], "--only")
                requested = parts[4].split(",")
                self.assertTrue(all(requested), parts)
                self.assertLessEqual(set(requested), allowed)

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

    def setUp(self) -> None:
        typed(self.record, RECORD_SHAPE, "record")

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
        rows = REPORT_COUNT_ROW.findall(text)
        # Built as a list first: reading the rows straight into a dict let a
        # second row for the same subject overwrite the first, so a wrong row
        # placed above the right one disappeared and a reader quoting the
        # report got a number the record contradicts.
        subjects = [subject for subject, _ in rows]
        self.assertEqual(
            sorted(subjects), sorted(set(subjects)), "a count subject has two rows"
        )
        observed = {subject: int(n) for subject, n in rows}
        self.assertEqual(set(observed), set(REPORT_COUNT_SUBJECTS))
        self.assertEqual(set(REPORT_COUNT_SUBJECTS.values()), set(self.record["counts"]))
        for subject, key in REPORT_COUNT_SUBJECTS.items():
            with self.subTest(subject=subject):
                self.assertEqual(observed[subject], self.record["counts"][key])

    def test_the_report_gate_table_repeats_every_recorded_gate_class(self) -> None:
        """Every cell of the report's gate table is joined to the record.

        The table restates six things the record already carries.  Checking
        only that each class name appeared somewhere in the prose let all six
        drift silently, and joining only the three numeric ones left the three
        that carry the reader's instructions free: the report could name
        ``check --only nonsense`` as the command that reproduces a refusal, or
        a finding code the checker cannot emit, and stay green.  ``When a gate
        stops the line`` sends the reader to the evaluator column by name, so
        that column is a pointer and is resolved like one.
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
                self.assertEqual(cells[0], entry["issue_obligation"])
                evaluator = cells[1].strip("`")
                self.assertTrue(evaluator.startswith("check "), evaluator)
                self.assertTrue(
                    entry["evaluator"].endswith(f" {evaluator}"),
                    f"{evaluator!r} is not the tail of {entry['evaluator']!r}",
                )
                ids = entry["obligation_ids"]
                self.assertEqual(cells[2], str(len(ids)) if ids else "none")
                negative = entry["negative_cases"]
                # Equality, not containment: "35 runtime binding rows" contains
                # "5 runtime binding rows", so a substring check let the report
                # differ from the record by any leading digits.
                self.assertEqual(cells[3], f"{negative['count']} {negative['kind']}")
                self.assertEqual(
                    FINDING_CODE.findall(cells[4]),
                    list(entry["finding_codes"]) + list(entry["network_findings"]),
                )
                self.assertEqual(cells[5], str(len(entry["tests"])))

    def test_the_report_repeats_every_bound_input_digest(self) -> None:
        """A quoted digest is evidence, so it is compared rather than trusted."""
        text = EVIDENCE_REPORT.read_text(encoding="utf-8")
        rows = REPORT_INPUT_ROW.findall(text)
        # Same collapse as the count table: a duplicate row for one path was
        # overwritten rather than caught, and a duplicated record entry would
        # have hidden the same way on the other side of the comparison.
        quoted = [path for path, _, _ in rows]
        self.assertEqual(
            sorted(quoted), sorted(set(quoted)), "a path is quoted more than once"
        )
        named = input_paths(self.record["inputs"])
        self.assertEqual(
            sorted(named), sorted(set(named)), "a path is recorded more than once"
        )
        observed = {path: (digest, int(size)) for path, digest, size in rows}
        recorded = {
            path: (entry["sha256"], entry["bytes"])
            for path, entry in zip(named, self.record["inputs"])
        }
        self.assertEqual(observed, recorded)


if __name__ == "__main__":
    unittest.main()
