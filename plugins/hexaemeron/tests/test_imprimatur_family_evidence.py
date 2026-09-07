"""Guard the structural-family-evidence-v1 fixture and its checker."""

from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "imprimatur"
SCRIPT = SKILL_ROOT / "scripts" / "check_family_evidence.py"
FIXTURE = SKILL_ROOT / "evals" / "structural-family-evidence-v1"
SCHEMAS = FIXTURE / "schemas"
ISSUE = FIXTURE / "issue-1298.md"
README = FIXTURE / "README.md"

SOURCE_ISSUE = "https://github.com/wildcat-finance/skills/issues/1298"
GROUPS = (
    "Missing conditions and causal wrappers",
    "Hidden actors, authority, and intent",
    "Verb, capability, and purpose shells",
    "Stacked hedges, emphasis, and redundant markers",
    "Existential, reference, and scope constructions needing more evidence",
)
COPIED_FIELDS = {
    "Form": "form",
    "Reader cost": "reader_cost",
    "Direct rewrite": "direct_rewrite",
    "Boundary": "boundary",
    "Disposition": "disposition",
}

FAMILY_ROW = {
    "family_id": "causal_fact_clause_wrapper",
    "group": "Missing conditions and causal wrappers",
    "evidence_tier": "boundary",
    "form": "\"Publication failed due to the fact that the digest changed\".",
    "reader_cost": "A causal connector wraps an already finite cause in a fact noun.",
    "direct_rewrite": "\"Publication failed because the digest changed.\"",
    "boundary": "Cover a closed list of causal connectors followed by \"the fact that\".",
    "disposition": "Strong candidate for evidence.",
    "overlaps": [],
    "discovery_phrases": ["due to the fact that"],
    "minimum_positive": 0,
    "minimum_negative": 0,
    "source_issue": SOURCE_ISSUE,
}

SPECIMEN_TEXT = "Publication failed due to the fact that the digest changed."
SPECIMEN_ROW = {
    "specimen_id": "causal_fact_clause_wrapper-pos-01",
    "family_id": "causal_fact_clause_wrapper",
    "tier": "structural",
    "family": "causal_fact_clause_wrapper",
    "polarity": "positive",
    "decision": "actionable",
    "text": SPECIMEN_TEXT,
    "text_sha256": hashlib.sha256(SPECIMEN_TEXT.encode("utf-8")).hexdigest(),
    "start_byte": 18,
    "end_byte": 38,
    "reason": "A causal connector wraps a finite cause in a fact noun.",
    "rewrite": "Publication failed because the digest changed.",
    "repository": "wildcat-finance/skills",
    "source_url": "https://github.com/wildcat-finance/skills/blob/" + "0" * 40 + "/README.md",
    "source_commit": "0" * 40,
    "source_path": "README.md",
    "source_start_line": 1,
    "source_end_line": 1,
    "source_object": "markdown_paragraph",
    "source_group_id": "wildcat-finance/skills:README.md",
    "origin": "human",
    "annotated_before_lint": True,
    "selection_seed": "imprimatur-structural-family-evidence-v1",
    "selection_rank_within_group": 1,
}


def jsonl(rows) -> str:
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def issue_families() -> list[dict]:
    """Parse the checked-in issue body into one record per family heading."""
    group = None
    rows: list[dict] = []
    current = None
    for line in ISSUE.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            group = heading if heading in GROUPS else None
            continue
        if line.startswith("### ") and group is not None:
            current = {"family_id": line[4:].strip(), "group": group}
            rows.append(current)
            continue
        if current is None:
            continue
        for label, key in COPIED_FIELDS.items():
            prefix = f"{label}: "
            if line.startswith(prefix):
                current[key] = line[len(prefix):].strip()
    return rows


class FamilyEvidenceCheckerTest(unittest.TestCase):
    """Every refusal the fixture's checker owes its reader."""

    maxDiff = None

    def run_checker(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def build_fixture(self, families=None, specimens=None, root=None) -> Path:
        """Write a throwaway fixture; the shipped one is never mutated."""
        if root is None:
            root = Path(tempfile.mkdtemp(prefix="family-evidence-"))
            self.addCleanup(self.remove_tree, root)
        (root / "schemas").mkdir(parents=True, exist_ok=True)
        for name in ("family.schema.json", "specimen.schema.json"):
            (root / "schemas" / name).write_bytes((SCHEMAS / name).read_bytes())
        rows = [FAMILY_ROW] if families is None else families
        (root / "families.jsonl").write_text(jsonl(rows), encoding="utf-8")
        (root / "specimens.jsonl").write_text(jsonl(specimens or []), encoding="utf-8")
        return root

    def remove_tree(self, root: Path) -> None:
        for path, directories, files in os.walk(root, topdown=False):
            for name in files:
                Path(path, name).unlink()
            for name in directories:
                target = Path(path, name)
                target.unlink() if target.is_symlink() else target.rmdir()
        root.rmdir()

    def assert_refused(self, root: Path, needle: str, code: int = 1, *args: str) -> None:
        result = self.run_checker("--fixture", str(root), *args)
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertIn(needle, result.stderr)

    def test_clean_fixture_exits_zero(self):
        root = self.build_fixture(specimens=[SPECIMEN_ROW])
        result = self.run_checker("--fixture", str(root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_refuses_symlink(self):
        root = self.build_fixture()
        target = root / "families.jsonl"
        target.unlink()
        target.symlink_to(root / "specimens.jsonl")
        self.assert_refused(root, "symlink refused", code=2)

    def test_refuses_oversized_file(self):
        root = self.build_fixture()
        padded = dict(FAMILY_ROW, reader_cost="x" * 1_100_000)
        (root / "families.jsonl").write_text(jsonl([padded]), encoding="utf-8")
        self.assert_refused(root, "file over 1048576 bytes", code=2)

    def test_refuses_unreadable_json_line(self):
        root = self.build_fixture()
        (root / "families.jsonl").write_text('{"family_id": "broken"\n', encoding="utf-8")
        self.assert_refused(root, "unreadable JSON at families.jsonl:1", code=2)

    def test_refuses_path_outside_the_fixture(self):
        root = self.build_fixture()
        (root / "schemas").rename(root.parent / "escaped-schemas")
        self.addCleanup(self.remove_tree, root.parent / "escaped-schemas")
        (root / "schemas").symlink_to(root.parent / "escaped-schemas")
        self.assert_refused(root, "symlink refused", code=2)

    def test_refuses_row_failing_its_schema(self):
        broken = dict(FAMILY_ROW)
        del broken["reader_cost"]
        root = self.build_fixture(families=[broken])
        self.assert_refused(root, "schema missing keys")

    def test_refuses_duplicate_family_id(self):
        root = self.build_fixture(families=[FAMILY_ROW, dict(FAMILY_ROW)])
        self.assert_refused(root, "duplicate family_id causal_fact_clause_wrapper")

    def test_refuses_unknown_evidence_tier(self):
        root = self.build_fixture(families=[dict(FAMILY_ROW, evidence_tier="promising")])
        self.assert_refused(root, "unknown evidence_tier 'promising'")

    def test_refuses_specimen_naming_unknown_family(self):
        row = dict(SPECIMEN_ROW, family_id="no_such_family", family="no_such_family")
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "names unknown family no_such_family")

    def test_refuses_span_outside_its_text(self):
        row = dict(SPECIMEN_ROW, start_byte=0, end_byte=len(SPECIMEN_TEXT) + 40)
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "lies outside the")

    def test_refuses_span_splitting_a_codepoint(self):
        text = "Publication failed because the digest changed — twice."
        row = dict(
            SPECIMEN_ROW,
            text=text,
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            start_byte=0,
            end_byte=text.encode("utf-8").index(b"\xe2\x80\x94") + 1,
        )
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "splits a UTF-8 codepoint")

    def test_refuses_mismatched_text_sha256(self):
        row = dict(SPECIMEN_ROW, text_sha256="0" * 64)
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "text_sha256 does not match the text")

    def test_refuses_annotation_after_lint(self):
        row = dict(SPECIMEN_ROW, annotated_before_lint=False)
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "annotated_before_lint is not true")

    def test_refuses_two_positives_sharing_a_source_group(self):
        second = dict(SPECIMEN_ROW, specimen_id="causal_fact_clause_wrapper-pos-02")
        root = self.build_fixture(specimens=[SPECIMEN_ROW, second])
        self.assert_refused(root, "share source_group_id")

    def test_refuses_a_family_below_its_tier_minimum(self):
        root = self.build_fixture(
            families=[dict(FAMILY_ROW, evidence_tier="high-value", minimum_positive=2, minimum_negative=2)]
        )
        self.assert_refused(root, "below the 2 and 2 its tier requires")

    def test_allow_below_minimum_reports_the_shortfall_instead(self):
        root = self.build_fixture(
            families=[dict(FAMILY_ROW, evidence_tier="high-value", minimum_positive=2, minimum_negative=2)]
        )
        report = root.parent / "report.json"
        self.addCleanup(lambda: report.exists() and report.unlink())
        result = self.run_checker(
            "--fixture", str(root), "--allow-below-minimum", "--report", str(report)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["families"], 1)
        self.assertEqual(payload["specimens"], 0)
        self.assertEqual(payload["rejections_path"], "selection-rejections.jsonl")
        self.assertEqual([entry["family_id"] for entry in payload["below_minimum"]], ["causal_fact_clause_wrapper"])

    def test_refuses_a_bad_invocation(self):
        result = self.run_checker("--fixture", str(FIXTURE), "--tier", "promising")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unknown tier: promising", result.stderr)

    def test_shipped_fixture_reports_forty_two_families(self):
        with tempfile.TemporaryDirectory(prefix="family-evidence-report-") as directory:
            report = Path(directory) / "report.json"
            result = self.run_checker(
                "--fixture", str(FIXTURE), "--allow-below-minimum", "--report", str(report)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["families"], 42)
        self.assertEqual(len(payload["below_minimum"]), 13)


class FamilyCatalogueWordingTest(unittest.TestCase):
    """The catalogue must quote the issue rather than paraphrase it."""

    maxDiff = None

    def setUp(self):
        self.rows = [
            json.loads(line)
            for line in (FIXTURE / "families.jsonl").read_text(encoding="utf-8").splitlines()
        ]

    def test_families_match_the_issue_headings_and_lines(self):
        parsed = issue_families()
        self.assertEqual(len(parsed), 42)
        self.assertEqual([row["family_id"] for row in self.rows], [row["family_id"] for row in parsed])
        for shipped, source in zip(self.rows, parsed):
            self.assertEqual(shipped["group"], source["group"], shipped["family_id"])
            for key in COPIED_FIELDS.values():
                self.assertEqual(shipped[key], source[key], f"{shipped['family_id']}/{key}")

    def test_tier_minimums_follow_the_evidence_tier(self):
        minimums = {
            "high-value": (2, 2),
            "signal": (2, 1),
            "boundary": (0, 0),
            "existing-family": (0, 0),
            "future": (0, 0),
        }
        for row in self.rows:
            expected = minimums[row["evidence_tier"]]
            self.assertEqual((row["minimum_positive"], row["minimum_negative"]), expected, row["family_id"])
        tiers = [row["evidence_tier"] for row in self.rows]
        self.assertEqual(tiers.count("high-value"), 5)
        self.assertEqual(tiers.count("signal"), 8)

    def test_readme_frozen_digests_match_the_current_files(self):
        table = re.findall(
            r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$",
            README.read_text(encoding="utf-8"),
            flags=re.M,
        )
        self.assertEqual(len(table), 5)
        for relative, expected in table:
            blob = (SKILL_ROOT / relative).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), expected, relative)


if __name__ == "__main__":
    unittest.main()
