"""Inventory guards for the Fiat checkpoint archive contract.

`skills/fiat/references/checkpoint-archive.md` is the contract the archive,
inspect and restore commands are built against. Two of its sets were fixed by
name in the study committed as `docs/fiat-checkpoint-archive-study.md`: the 24
refusal classes of study section 4 and the 35 hostile fixture ids on the risk
register's `hostile-fixture-set` line. A class missing from the reference is a
refusal nobody tests; an id missing is a specimen nobody builds. The first test
holds both sets equal to the tracked study copy, so it runs outside a Fiat run
worktree. The second holds the budgets file to the six limits study section 10
derived, read through the same loader `metron.py check --budgets` uses.

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
BUDGET_ROW = re.compile(
    r"^\| `(?P<name>checkpoint\.archive\.[a-z_]+)` \| (?P<unit>[a-z]+) \|"
    r" (?P<limit>[0-9]+) \| (?P<derivation>.+) \|$"
)
STUDY_BUDGET_HEADING = "10. The budget, or its absence"

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

        classes = reference_refusal_classes(reference)
        self.assertEqual(len(classes), len(set(classes)), "a refusal class row repeats")
        self.assertEqual(24, len(classes), classes)
        self.assertEqual(study_refusal_classes(study), set(classes))

        ids = reference_fixture_ids(reference)
        self.assertEqual(len(ids), len(set(ids)), "a fixture id repeats")
        self.assertEqual(35, len(ids), ids)
        self.assertEqual(study_fixture_ids(study), set(ids))

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
