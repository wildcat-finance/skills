"""Inventory guards for the Fiat checkpoint archive contract.

`skills/fiat/references/checkpoint-archive.md` is the contract the archive,
inspect and restore commands are built against. Every value in it comes from
the study committed as `docs/fiat-checkpoint-archive-study.md`, so a value that
drifts in one document and not the other is a specification an implementer
reads and a specification the study fixed, disagreeing.

The first test holds the reference to that study, item for item: the 24 refusal
classes of study section 4 and the 35 hostile fixture ids on the risk
register's `hostile-fixture-set` line, then the six schema names, the nine
entry paths, the thirteen closed manifest fields, the seven ceiling values, the
zip metadata rule including the entry mode, the bundle determinism command, the
six secret patterns, the `## Restore transaction` heading, the sidecar
two-space rule and the `acceptance/current` rule, against study sections 1, 3
and 4. A class missing from the reference is a refusal nobody tests; an id
missing is a specimen nobody builds; a drifted ceiling or pattern is the limit
an implementer builds to. Mutating any one of those values, or deleting it,
fails this test. Both documents are read from the tracked copies, so the test
runs outside a Fiat run worktree.

The second test holds the budgets file to the six limits study section 10
derived, read through the same loader `metron.py check --budgets` uses, and
holds the reference's and the study's prose tables equal to it.

Every slice below is taken through `anchored` or `fenced_block`, which name the
missing anchor in an assertion rather than raising `IndexError` on a reworded
study.

No test or class name here contains `hostile` or `restore_from_archive`: the
design record's conformance resolvers select later steps' tests with
`-k hostile` and `-k restore_from_archive`, and a match here would change
their counts.
"""

from __future__ import annotations

import importlib.util
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
ROOT = PLUGIN.parents[1]
FIAT = PLUGIN / "skills" / "fiat"
REFERENCE = FIAT / "references" / "checkpoint-archive.md"
BUDGETS = FIAT / "scripts" / "checkpoint-archive-budgets.json"
METRON = PLUGIN / "skills" / "metron" / "scripts" / "metron.py"
STUDY = ROOT / "docs" / "fiat-checkpoint-archive-study.md"

TABLE_CLASS = re.compile(r"^\| `([a-z0-9]+(?:-[a-z0-9]+)+)` \|")
LIST_ID = re.compile(r"^- `([a-z0-9]+(?:-[a-z0-9]+)+)`$")
KEBAB_SPAN = re.compile(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`")
MANIFEST_ROW = re.compile(r"^\| `(?P<field>[a-z_]+)` \| (?P<closed>.+) \| (?P<joined>.+) \|$")
SCHEMA_NAME = re.compile(r"(?<![-\w])fiat-checkpoint-[a-z-]+/v[0-9]+")
BUDGET_ROW = re.compile(
    r"^\| `(?P<name>checkpoint\.archive\.[a-z_]+)` \| (?P<unit>[a-z]+) \|"
    r" (?P<limit>[0-9]+) \| (?P<derivation>.+) \|$"
)
STUDY_BUDGET_HEADING = "10. The budget, or its absence"
CEILING_NUMBER = re.compile(r"(?<![\w,.\-])([0-9][0-9,]*)")
CODE_SPAN = re.compile(r"`([^`]+)`")
BUNDLE_COMMAND = "`git -c pack.threads=1 bundle create`"
UNTHREADED_BUNDLE_COMMAND = "`git bundle create`"

# The six schema names of study sections 1 and 4. `fiat-controller-checkpoint`
# schemas belong to the capsule this archive carries and are not this
# reference's to fix, so the pattern above starts at `fiat-checkpoint-`.
EXPECTED_SCHEMAS = frozenset(
    {
        "fiat-checkpoint-archive/v1",
        "fiat-checkpoint-archive-export/v1",
        "fiat-checkpoint-archive-restore/v1",
        "fiat-checkpoint-inspect/v1",
        "fiat-checkpoint-restore-transcript/v1",
        "fiat-checkpoint-signature-proof/v1",
    }
)

# The nine entry paths, in the fixed order both documents state them.
EXPECTED_ENTRY_PATHS = (
    "checkpoint.json",
    "README.txt",
    "git/repository.bundle",
    "controller-capsule/MANIFEST.json",
    "controller-capsule/controller/...",
    "identity/checkpoint-identity.json",
    "proof/signatures.json",
    "proof/pubkey.asc",
    "acceptance/prior/<n>.json",
)

# The thirteen fields `checkpoint.json` is closed to, in order.
EXPECTED_MANIFEST_FIELDS = (
    "schema",
    "archive",
    "boundary",
    "run",
    "refs",
    "bundle",
    "controller_capsule",
    "identity",
    "signer",
    "proof",
    "acceptance",
    "controller",
    "limits",
)

# The seven ceiling values, in the order both documents state them: entries,
# expanded total, the bundle, every other entry, an entry name, an entry name
# component, and prior acceptance receipts.
EXPECTED_CEILINGS = (4200, 1300, 1, 64, 1024, 255, 64)
EXPECTED_CEILING_PHRASES = (
    "4,200 entries",
    "1,300 MiB",
    "1 GiB",
    "64 MiB",
    "1,024 UTF-8 bytes",
    "64 prior",
)
EXPECTED_ENTRY_MODE = "0100644"
EXPECTED_CONTAINER_CLAUSES = (
    "stored",
    f"Unix mode `{EXPECTED_ENTRY_MODE}`",
    "DOS time 1980-01-01 00:00:00",
    "`create_system` 3",
    "no directory entries",
    "no ZIP64 records",
    "no comment",
    "no extra fields",
    "sorted by UTF-8 bytes",
)
EXPECTED_SECRET_SPANS = (
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "ghp_[A-Za-z0-9]{36}",
    "github_pat_[A-Za-z0-9_]{22,}",
    "AKIA[0-9A-Z]{16}",
    "xox[baprs]-",
)
EXPECTED_PEM_PROSE = "PEM private-key block"

# The sidecar's two spaces are what `shasum -a 256 -c` reads, so the one-space
# form is rejected by name in both documents.
SIDECAR_SPAN = r"`<64 lowercase hex>  checkpoint.zip\n`"
SIDECAR_ONE_SPACE = r"`<64 lowercase hex> checkpoint.zip\n`"

RESTORE_HEADING = "Restore transaction"
ACCEPTANCE_OUTSIDE = "`current` is the literal `outside`"
ACCEPTANCE_NEVER_WRITTEN = "No `acceptance/current` entry is ever written."
ACCEPTANCE_REFUSAL_ROW = "| `acceptance-self-reference` |"
ACCEPTANCE_REFUSAL_CONDITION = "an `acceptance/current` entry is present"
STUDY_ACCEPTANCE_REFUSES = "acceptance/current refuses"

EXPECTED_BUDGETS = {
    "checkpoint.archive.export_wall_ms": ("ms", 15000),
    "checkpoint.archive.inspect_wall_ms": ("ms", 10000),
    "checkpoint.archive.restore_wall_ms": ("ms", 20000),
    "checkpoint.archive.bytes": ("bytes", 201581002),
    "checkpoint.archive.expanded_bytes": ("bytes", 209715200),
    "checkpoint.archive.export_peak_rss_bytes": ("bytes", 1073741824),
}


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required Step 1 file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def section(text: str, heading: str) -> str:
    """The body under one `## heading`, up to the next `## ` heading."""
    marker = f"\n## {heading}\n"
    if marker not in text:
        raise AssertionError(f"no `## {heading}` section")
    return text.split(marker, 1)[1].split("\n## ", 1)[0]


def reference_refusal_classes(reference: str) -> list[str]:
    """The first cell of every data row in the refusal-class table, in order."""
    found = []
    for line in section(reference, "Refusal classes").splitlines():
        match = TABLE_CLASS.match(line)
        if match:
            found.append(match.group(1))
    return found


def reference_fixture_ids(reference: str) -> list[str]:
    """Every one-id list item under the fixture heading, in order."""
    found = []
    for line in section(reference, "Hostile fixtures").splitlines():
        match = LIST_ID.match(line)
        if match:
            found.append(match.group(1))
    return found


def study_refusal_classes(study: str) -> set[str]:
    """The kebab-case spans of study section 4's `Refusal classes` bullet.

    The bullet's only other span, `status: unavailable`, carries a colon and a
    space, so a kebab-only pattern leaves it out.
    """
    details = study.split("### Details the runbook binds", 1)[1].split("\n## ", 1)[0]
    bullet = details.split("- Refusal classes,", 1)[1].split("\n- ", 1)[0]
    return set(KEBAB_SPAN.findall(bullet))


def budget_rows(text: str, heading: str) -> list[str]:
    """The data rows of one budget table under `## heading`, exactly as written."""
    return [
        line
        for line in section(text, heading).splitlines()
        if BUDGET_ROW.match(line)
    ]


def flat(text: str) -> str:
    """One line, single-spaced, so a rewrapped paragraph reads the same."""
    return " ".join(text.split())


def anchored(text: str, start: str, end: str, what: str) -> str:
    """The slice between two literal anchors, or a named assertion failure.

    A prose anchor that has moved is a specification change somebody must
    look at, so it fails by name here rather than as an `IndexError` from a
    bare `split`.
    """
    if start not in text:
        raise AssertionError(f"{what}: the opening anchor {start!r} is absent")
    tail = text.split(start, 1)[1]
    if end not in tail:
        raise AssertionError(f"{what}: no {end!r} closes {start!r}")
    return tail.split(end, 1)[0]


def fenced_block(text: str, anchor: str, what: str) -> str:
    """The body of the first ```text fence after a literal anchor."""
    if anchor not in text:
        raise AssertionError(f"{what}: the anchor {anchor!r} is absent")
    tail = text.split(anchor, 1)[1]
    opener = "```text\n"
    if opener not in tail:
        raise AssertionError(f"{what}: no ```text fence follows {anchor!r}")
    body = tail.split(opener, 1)[1]
    if "\n```" not in body:
        raise AssertionError(f"{what}: the fence after {anchor!r} does not close")
    return body.split("\n```", 1)[0]


def first_column(block: str) -> list[str]:
    """The first whitespace-separated field of every non-blank line."""
    return [line.split()[0] for line in block.splitlines() if line.strip()]


def ceiling_numbers(text: str) -> list[int]:
    """Every free-standing quantity in a ceilings block, in written order.

    The lookbehind keeps `C0`, `C1` and the `8` of `UTF-8` out, since those
    are a control-character class and an encoding name rather than limits.
    """
    return [int(found.replace(",", "")) for found in CEILING_NUMBER.findall(text)]


def secret_spans(text: str) -> list[str]:
    return CODE_SPAN.findall(flat(text))


def study_fixture_ids(study: str) -> set[str]:
    """The whitespace-separated ids after `one test per id:` in the register."""
    for line in study.splitlines():
        if line.startswith("hostile-fixture-set |"):
            return set(line.split("one test per id:", 1)[1].split())
    raise AssertionError("the study's risk register has no hostile-fixture-set line")


def load_metron():
    spec = importlib.util.spec_from_file_location("metron_budget_loader", METRON)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckpointArchiveScaffoldTests(unittest.TestCase):
    def test_archive_reference_names_every_refusal_class_and_fixture_id(self):
        reference = read(REFERENCE)
        study = read(STUDY)
        problem = section(study, "1. Problem statement")
        constraints = section(study, "3. Constraints and non-goals")
        options = section(study, "4. Design options")

        # The 24 refusal classes (study section 4) and the 35 hostile fixture
        # ids (study section 5), as sets, so a drop is a failure.
        classes = reference_refusal_classes(reference)
        self.assertEqual(len(classes), len(set(classes)), "a refusal class row repeats")
        self.assertEqual(24, len(classes), classes)
        self.assertEqual(study_refusal_classes(study), set(classes))

        ids = reference_fixture_ids(reference)
        self.assertEqual(len(ids), len(set(ids)), "a fixture id repeats")
        self.assertEqual(35, len(ids), ids)
        self.assertEqual(study_fixture_ids(study), set(ids))

        # The six schema names. The reference's set is closed, so a renamed or
        # reversioned schema shows as both a missing and an unexpected member.
        self.assertEqual(EXPECTED_SCHEMAS, set(SCHEMA_NAME.findall(reference)))
        for schema in sorted(EXPECTED_SCHEMAS):
            with self.subTest(schema=schema):
                self.assertIn(schema, study)

        # The nine entry paths. Both documents carry the layout as one fenced
        # block, and the blocks are equal, so a dropped or renamed line fails
        # in the column comparison and again in the block comparison.
        reference_layout_block = fenced_block(
            reference, "Nine entry paths, fixed:", "reference layout fence"
        )
        study_layout_block = fenced_block(
            problem, "Layout, fixed:", "study section 1 layout fence"
        )
        self.assertEqual(list(EXPECTED_ENTRY_PATHS), first_column(reference_layout_block))
        self.assertEqual(list(EXPECTED_ENTRY_PATHS), first_column(study_layout_block))
        self.assertEqual(study_layout_block, reference_layout_block)

        # The thirteen closed manifest fields (study section 1). The reference
        # states them as table rows and the study as one sentence, so the rows
        # are compared in order and the study is required to name each field in
        # the same order.
        manifest_rows = [
            match
            for match in (
                MANIFEST_ROW.match(line)
                for line in section(reference, "Content manifest").splitlines()
            )
            if match
        ]
        self.assertEqual(
            list(EXPECTED_MANIFEST_FIELDS),
            [match.group("field") for match in manifest_rows],
        )
        study_manifest = anchored(
            problem,
            "`checkpoint.json` is closed to:",
            "\n\n",
            "study section 1 closed manifest fields",
        )
        seen = -1
        for field in EXPECTED_MANIFEST_FIELDS:
            with self.subTest(manifest_field=field):
                at = study_manifest.find(f"`{field}`")
                self.assertNotEqual(-1, at, f"the study does not name `{field}`")
                self.assertGreater(at, seen, f"`{field}` is out of order in the study")
                seen = at

        # The seven ceiling values (study section 1). The two documents wrap and
        # punctuate the list differently, so the values are compared as ordered
        # quantities and the unit-bearing phrases are required in both.
        reference_ceilings = section(reference, "Ceilings")
        study_ceilings = anchored(
            problem,
            "Ceilings (safety, not performance):",
            "\n\n",
            "study section 1 ceilings",
        )
        self.assertEqual(list(EXPECTED_CEILINGS), ceiling_numbers(reference_ceilings))
        self.assertEqual(list(EXPECTED_CEILINGS), ceiling_numbers(study_ceilings))
        for name, block in (("reference", reference_ceilings), ("study", study_ceilings)):
            flattened = flat(block)
            for phrase in EXPECTED_CEILING_PHRASES:
                with self.subTest(document=name, ceiling=phrase):
                    self.assertIn(phrase, flattened)
            with self.subTest(document=name, ceiling="255 per component"):
                self.assertRegex(flattened, r"255 (?:bytes )?per component")

        # The zip metadata rule, entry mode included (study section 1).
        reference_container = flat(section(reference, "Container"))
        study_container = flat(
            anchored(
                problem,
                "The zip is a pure container",
                "Layout, fixed:",
                "study section 1 container rule",
            )
        )
        for name, block in (
            ("reference", reference_container),
            ("study", study_container),
        ):
            for clause in EXPECTED_CONTAINER_CLAUSES:
                with self.subTest(document=name, clause=clause):
                    self.assertIn(clause, block)

        # The `entry-mode` refusal row names the mode the container rule fixes,
        # so the reference cannot state one mode and refuse against another.
        entry_mode_rows = [
            line
            for line in section(reference, "Refusal classes").splitlines()
            if line.startswith("| `entry-mode` |")
        ]
        self.assertEqual(1, len(entry_mode_rows), entry_mode_rows)
        self.assertIn(f"`{EXPECTED_ENTRY_MODE}`", entry_mode_rows[0])

        # The bundle determinism command (study section 3, constraint 12).
        reference_layout = flat(section(reference, "Layout"))
        study_bundle = flat(
            anchored(
                constraints,
                "Determinism rule for the bundle:",
                "\n",
                "study section 3 bundle determinism rule",
            )
        )
        self.assertIn(BUNDLE_COMMAND, reference_layout)
        self.assertIn(BUNDLE_COMMAND, study_bundle)
        self.assertNotIn(UNTHREADED_BUNDLE_COMMAND, reference_layout)

        # The six secret patterns (study section 4). Five are code spans that
        # are identical in both documents; the PEM block is prose in both.
        reference_secret_items = [
            line
            for line in section(reference, "Secret patterns").splitlines()
            if line.startswith("- ")
        ]
        self.assertEqual(6, len(reference_secret_items), reference_secret_items)
        study_secrets = anchored(
            anchored(options, "- Secret scan at export", "\n- ", "study section 4 secret scan"),
            "controller file:",
            ". A hit",
            "study section 4 secret pattern list",
        )
        self.assertEqual(
            list(EXPECTED_SECRET_SPANS), secret_spans("\n".join(reference_secret_items))
        )
        self.assertEqual(list(EXPECTED_SECRET_SPANS), secret_spans(study_secrets))
        self.assertIn(EXPECTED_PEM_PROSE, flat("\n".join(reference_secret_items)))
        self.assertIn(EXPECTED_PEM_PROSE, flat(study_secrets))

        # The `## Restore transaction` heading, which is where the reference
        # states the transaction the Exit requires it to state.
        self.assertIn(f"\n## {RESTORE_HEADING}\n", reference)
        self.assertTrue(
            section(reference, RESTORE_HEADING).strip(),
            "the reference's `## Restore transaction` section is empty",
        )

        # The sidecar's two spaces, unflattened so the spacing is the evidence.
        for name, document in (("reference", reference), ("study", study)):
            with self.subTest(document=name, rule="sidecar two spaces"):
                self.assertIn(SIDECAR_SPAN, document)
                self.assertNotIn(SIDECAR_ONE_SPACE, document)

        # The `acceptance/current` rule, stated three ways in the reference and
        # two in the study, so an inverted sentence fails rather than passing on
        # a substring of itself.
        self.assertIn(ACCEPTANCE_NEVER_WRITTEN, reference)
        acceptance_rows = [
            line
            for line in section(reference, "Refusal classes").splitlines()
            if line.startswith(ACCEPTANCE_REFUSAL_ROW)
        ]
        self.assertEqual(1, len(acceptance_rows), acceptance_rows)
        self.assertIn(ACCEPTANCE_REFUSAL_CONDITION, acceptance_rows[0])
        self.assertIn(ACCEPTANCE_OUTSIDE, section(reference, "Content manifest"))
        self.assertIn(ACCEPTANCE_OUTSIDE, study_manifest)
        self.assertIn(STUDY_ACCEPTANCE_REFUSES, study)

    def test_archive_budgets_declare_the_six_measured_limits(self):
        budgets = load_metron().load_budgets(str(BUDGETS))
        self.assertEqual(6, len(budgets))
        declared = {entry["name"]: entry for entry in budgets}
        self.assertEqual(sorted(EXPECTED_BUDGETS), sorted(declared))
        for name, (unit, limit) in EXPECTED_BUDGETS.items():
            with self.subTest(budget=name):
                entry = declared[name]
                self.assertEqual(unit, entry["unit"])
                self.assertEqual(limit, entry["limit"])
                self.assertEqual(0.25, entry["variance"])
                self.assertEqual("lower_is_better", entry["direction"])

        reference = read(REFERENCE)
        budgets_section = section(reference, "Budgets")
        for name in EXPECTED_BUDGETS:
            self.assertIn(f"`{name}`", budgets_section)
        self.assertIn("checkpoint-archive-budgets.json", budgets_section)

        # Both prose tables restate every declared limit, and the reference is
        # the contract the later steps are built against. Holding the three
        # statements equal is what keeps a drifted number from becoming the
        # ceiling an implementer reads while every other gate stays green.
        reference_rows = budget_rows(reference, "Budgets")
        self.assertEqual(6, len(reference_rows), reference_rows)
        self.assertEqual(budget_rows(read(STUDY), STUDY_BUDGET_HEADING), reference_rows)
        for row in reference_rows:
            fields = BUDGET_ROW.match(row)
            with self.subTest(budget=fields.group("name")):
                self.assertIn(fields.group("name"), declared, row)
                entry = declared[fields.group("name")]
                self.assertEqual(entry["unit"], fields.group("unit"))
                self.assertEqual(entry["limit"], int(fields.group("limit")))


if __name__ == "__main__":
    unittest.main()
