"""Hold the committed issue 1892 design records to the record the run locked.

`docs/statement-parts/` carries byte copies of the controller's study,
runbook, design record and design folder. Git ignores their `.hexaemeron/`
originals, so these tests read only committed bytes: the digest the runbook's
design-lock fence names, the selection reports the record binds, and the
conformance harness's refusal of every candidate the record rejected.
`ProofRecordTests` holds the Step 4 proof to the commit its runs used, to the
study's section 3 digests and to the heavy fixture the tree builds.
"""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import tempfile
import unittest


DOCS = Path(__file__).resolve().parents[1] / "docs" / "statement-parts"
RECORD = DOCS / "design-evidence.json"
RUNBOOK = DOCS / "runbook.md"
STUDY = DOCS / "study.md"
PROOF = DOCS / "proof.md"
CONFORMANCE = DOCS / "design" / "conformance.py"
SELECTION = PurePosixPath("design/reports/selection")
DESIGN_LOCK = (
    ("schema", "protasis-design-evidence/v1"),
    ("sha256", "071dcdb20c28a46fdd18933b4dcf31975d787b7c5581f2f092e5ecf00b3c2459"),
    ("candidate", "statement-parts"),
)
SELECTED = "statement-parts"
REJECTED = ("per-component-statements", "raised-limit-matched-reader", "compact-projection")
# The Step 4 commit the proof's runs used, and its parent, the Step 3 head.
PROOF_COMMIT = "e3d38ff92e118835b77b147d6896780aa0068944"
PROOF_PARENT = "c9eb708e260093fb2043c938e2dfa40a4e4ed092"
DIGEST = re.compile(r"sha256:[0-9a-f]{64}|[0-9a-f]{64}")


def design_lock_rows():
    """Return the rows of the runbook's one design-lock fence, in order."""
    lines = RUNBOOK.read_text(encoding="utf-8").splitlines()
    openings = [index for index, line in enumerate(lines) if line == "```design-lock"]
    if len(openings) != 1:
        raise AssertionError(f"the runbook carries {len(openings)} design-lock fences, not one")
    rows = []
    for line in lines[openings[0] + 1:]:
        if line == "```":
            return tuple(rows)
        key, separator, value = line.partition(" | ")
        if not separator:
            raise AssertionError(f"design-lock row {line!r} is not `key | value`")
        rows.append((key, value))
    raise AssertionError("the runbook's design-lock fence is not closed")


def locked_record():
    return json.loads(RECORD.read_bytes())


def tree_below(root):
    """Every path under root, relative and in POSIX form."""
    return sorted(
        (Path(parent) / name).relative_to(root).as_posix()
        for parent, directories, files in os.walk(root)
        for name in directories + files
    )


class DesignRecordCopyTests(unittest.TestCase):
    def test_the_record_copy_is_the_locked_design_record(self):
        self.assertEqual(design_lock_rows(), DESIGN_LOCK)
        data = RECORD.read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), dict(DESIGN_LOCK)["sha256"])
        record = json.loads(data)
        self.assertEqual(record["schema"], dict(DESIGN_LOCK)["schema"])
        self.assertEqual(record["selection"]["candidate"], SELECTED)

    def test_every_selection_report_the_record_binds_is_committed(self):
        resolved = [row for row in locked_record()["results"] if row["state"] != "pending"]
        self.assertEqual(len(resolved), 20)
        bound = set()
        for row in resolved:
            with self.subTest(candidate=row["candidate"], criterion=row["criterion"]):
                self.assertIn(row["state"], ("pass", "fail"))
                relative = PurePosixPath(row["report"]["path"])
                self.assertEqual(relative.parent, SELECTION)
                self.assertEqual(relative.name, f"{row['candidate']}-{row['criterion']}.json")
                path = DOCS.joinpath(*relative.parts)
                self.assertFalse(path.is_symlink(), str(relative))
                self.assertTrue(path.is_file(), str(relative))
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), row["report"]["sha256"]
                )
                bound.add(relative.name)
        committed = {entry.name for entry in DOCS.joinpath(*SELECTION.parts).iterdir()}
        self.assertEqual(committed, bound)

    def test_the_conformance_harness_refuses_every_other_candidate(self):
        record = locked_record()
        others = tuple(
            item["id"] for item in record["candidates"]
            if item["id"] != record["selection"]["candidate"]
        )
        self.assertEqual(others, REJECTED)
        criteria = [item["id"] for item in record["criteria"] if item["stage"] == "conformance"]
        self.assertEqual(len(criteria), 4)
        # No staging variable reaches the child, so a harness that skipped the
        # candidate check could not rebuild a demonstration from here.
        environment = {
            "PATH": os.environ.get("PATH", os.defpath),
            "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        for candidate in REJECTED:
            for criterion in criteria:
                with self.subTest(candidate=candidate, criterion=criterion):
                    with tempfile.TemporaryDirectory() as directory:
                        root = Path(directory)
                        # The harness also exits 2 from a directory without
                        # plugins/alexandria; creating it leaves the candidate
                        # check as the only refusal that exits 2.
                        (root / "plugins" / "alexandria").mkdir(parents=True)
                        result = subprocess.run(
                            [sys.executable, str(CONFORMANCE), criterion,
                             "--candidate", candidate],
                            capture_output=True, text=True, check=False,
                            cwd=root, env=environment, timeout=120,
                        )
                        after = tree_below(root)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertIn(
                        f"only the selected candidate {SELECTED} carries conformance cases; "
                        f"refusing {candidate}",
                        result.stderr,
                    )
                    self.assertNotIn("Traceback", result.stderr)
                    self.assertEqual(result.stdout, "")
                    self.assertEqual(after, ["plugins", "plugins/alexandria"])


def section(text, start, end):
    """The text from the line `start` opens up to the line `end` opens."""
    opening = text.index(start)
    return text[opening:text.index(end, opening + len(start))]


def table_rows(text):
    """Each Markdown table body row as a tuple of stripped cells."""
    rows = []
    for line in text.splitlines():
        if line.startswith("| ") and not line.startswith("| ---"):
            rows.append(tuple(cell.strip() for cell in line.strip().strip("|").split("|")))
    return rows[1:] if rows else rows


def number(cell):
    return int(cell.split()[0].replace(",", ""))


def study_pins():
    """(identifier, statement bytes, statement SHA-256) for each section 3 row."""
    table = section(STUDY.read_text(encoding="utf-8"), "**Byte identity.**", "**External dependencies.**")
    rows = []
    for cells in table_rows(table):
        rows.append((cells[1].strip("`"), number(cells[3]), cells[4].strip("`")))
    return rows


class ProofRecordTests(unittest.TestCase):
    """The Step 4 proof records only what its commit's tree and the study hold."""

    @classmethod
    def setUpClass(cls):
        cls.raw = PROOF.read_text(encoding="utf-8")

    def test_the_proof_names_the_commit_its_runs_used(self):
        opening = section(self.raw, "# Statement parts", "## Heavy fixture")
        for token in (
            f"Step 4\ncommit `{PROOF_COMMIT}`",
            f"`{PROOF_PARENT}`",
            "`tests/test_version_propagation.py`",
            "`ProofRecordTests`",
            "`plugins/alexandria/tests/test_statement_parts_records.py`",
        ):
            self.assertIn(token, opening)
        whole = " ".join(self.raw.split())
        self.assertNotIn("Step 4 tree", whole)
        self.assertEqual(
            set(re.findall(r"\b[0-9a-f]{40}\b", self.raw)), {PROOF_COMMIT, PROOF_PARENT}
        )

    def test_every_pinned_statement_digest_is_the_studys_section_3_table(self):
        pins = study_pins()
        self.assertEqual(len(pins), 11)
        table = section(self.raw, "## Pinned statements", "All eleven statements")
        recorded = []
        for cells in table_rows(table):
            self.assertEqual(cells[4], "match")
            recorded.append((cells[1].strip("`"), number(cells[2]), cells[3].strip("`")))
        self.assertEqual(recorded, pins)

    def test_every_digest_the_proof_records_is_pinned_or_the_heavy_release(self):
        pinned = {value for identity, _, statement in study_pins() for value in (identity, statement)}
        heavy = section(self.raw, "## Heavy fixture", "## Ariadne")
        (release,) = re.findall(r"`(sha256:[0-9a-f]{64})`", heavy)
        self.assertEqual(set(DIGEST.findall(self.raw)) - pinned, {release})

    def test_the_heavy_figures_are_the_ones_the_tree_projects(self):
        # This module puts Alexandria's and Ariadne's scripts on the path.
        from tests.test_statement_parts import heavy_manifest
        from alexandria_lib import statement as statement_module
        from alexandria_lib.canonical import canonical_bytes
        from ariadne_lib import envelope as ariadne_envelope

        manifest = heavy_manifest()
        heavy = section(self.raw, "## Heavy fixture", "## Ariadne")
        self.assertIn(f"`{manifest['release_id']}`", heavy)
        single = canonical_bytes(
            statement_module.statement_for(manifest), max_nodes=statement_module.MAX_STATEMENT_BYTES
        )
        self.assertIn(f"encode to {len(single):,} bytes", heavy)
        projection = statement_module.project_statement(manifest)
        files = [(statement_module.INDEX_NAME, projection.index)] + [
            (f"{statement_module.PART_DIRECTORY}/{name}", body) for name, body in projection.parts
        ]
        expected = []
        for name, body in files:
            part = json.loads(body)["predicate"].get("part")
            expected.append((
                f"`{name}`", f"{len(body):,}",
                f"{statement_module.key_characters(json.loads(body)):,}",
                "index" if part is None else str(part["components"]), "0",
                f"{len(ariadne_envelope.Envelope(body).to_json().encode('utf-8')):,}", "0",
            ))
        ariadne = section(self.raw, "## Ariadne", "## Emission cost")
        self.assertEqual(table_rows(ariadne), expected)
        figures = dict(
            line[2:].rstrip(".").split(": ", 1)
            for line in heavy.splitlines() if line.startswith("- ")
        )
        sizes = [len(body) for _, body in projection.parts]
        self.assertEqual(figures["Parts"], str(len(projection.parts)))
        self.assertEqual(figures["Largest part"], f"{max(sizes):,} bytes")
        self.assertEqual(
            figures["Index"],
            f"{len(projection.index):,} bytes, "
            f"{statement_module.key_characters(json.loads(projection.index)):,} key characters",
        )


class LimitsTextTests(unittest.TestCase):
    """The guide's single-statement DSSE band is the one Ariadne's reader computes."""

    def test_the_band_names_the_largest_statement_an_unsigned_envelope_carries(self):
        # This module puts Alexandria's and Ariadne's scripts on the path.
        from tests.test_statement_parts import heavy_manifest  # noqa: F401
        from alexandria_lib import statement as statement_module
        from ariadne_lib import envelope as ariadne_envelope

        def envelope_bytes(size):
            return len(ariadne_envelope.Envelope(b"x" * size).to_json().encode("utf-8"))

        low, high = statement_module.MAX_PART_BYTES, statement_module.MAX_STATEMENT_BYTES
        self.assertLessEqual(envelope_bytes(low), statement_module.MAX_STATEMENT_BYTES)
        while low < high:
            middle = (low + high + 1) // 2
            if envelope_bytes(middle) <= statement_module.MAX_STATEMENT_BYTES:
                low = middle
            else:
                high = middle - 1
        guide = (DOCS.parent / "release-statements.md").read_text(encoding="utf-8")
        limits = " ".join(section(guide, "### Limits", "## Evidence boundary").split())
        self.assertIn(f"{low:,} bytes", limits)
        self.assertIn("may exceed Ariadne's default 8,388,608-byte read", limits)


if __name__ == "__main__":
    unittest.main()
