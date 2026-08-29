"""The shipped documents, held against the code they describe.

A tool whose whole claim is that a document should not drift from what produced
it is a poor advertisement for itself if its own README does. These checks turn
the drift into a test failure rather than something a reader finds first.
"""

import os
import re
import unittest

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import core_predicate, gates, registry  # noqa: E402
from ariadne_lib.predicates import dataset  # noqa: E402
from ariadne_lib.predicates import grounded_agent  # noqa: E402
from ariadne_lib.predicates import solidity_release as release  # noqa: E402
from ariadne_lib.predicates import state_fixture  # noqa: E402

PLUGIN = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SKILL = os.path.join(PLUGIN, "skills", "ariadne", "SKILL.md")
README = os.path.join(PLUGIN, "README.md")
CONTRACT = os.path.join(PLUGIN, "AGENTS.md")
CONFORMANCE = os.path.join(PLUGIN, "docs", "conformance.md")
PREDICATE_DOC = os.path.join(PLUGIN, "docs", "solidity-release.md")
DATASET_DOC = os.path.join(PLUGIN, "docs", "dataset.md")
STATE_FIXTURE_DOC = os.path.join(PLUGIN, "docs", "state-fixture.md")
GROUNDED_AGENT_DOC = os.path.join(PLUGIN, "docs", "grounded-agent.md")
CAPTURE_GROUNDED_AGENT_DOC = os.path.join(
    PLUGIN, "docs", "capturing-a-grounded-agent.md"
)

STAGED_COMMAND_DOCS = {
    "capture-grounded-agent": CAPTURE_GROUNDED_AGENT_DOC,
}
"""A command whose bounded guide lands before Step 4 updates marketplace prose.

Every other command remains mandatory in both top-level surfaces. The final
grounded-agent step removes this staged entry when those surfaces stop saying
the capture is unimplemented.
"""

DOCUMENTED = (
    (release, PREDICATE_DOC),
    (dataset, DATASET_DOC),
    (state_fixture, STATE_FIXTURE_DOC),
    (state_fixture.V2, STATE_FIXTURE_DOC),
    (grounded_agent, GROUNDED_AGENT_DOC),
)
"""Each shipped predicate and the document that describes its fields."""
EXAMPLES = os.path.join(PLUGIN, "examples")

POLICY_CITATION = re.compile(r"(?m)^Policy: \[[^\]]+\]\([^)]+\)$")
"""The one link a ledger has to point outside the plugin.

`tests/test_evolution_contract.py` at the repository root requires every
governed ledger to cite `plugins/hexaemeron/skills/VERSIONING.md` by a relative
path that resolves to that file. The versioning contract is shared by twelve
plugins and is not copied into each, so that citation cannot both satisfy the
repository contract and stay inside this plugin. The exemption is this one line;
every other link in the ledger is held to the rule below.
"""


def read(path):
    with open(path, "rb") as handle:
        return handle.read().decode("utf-8")


def subcommands():
    """Every subcommand the parser actually offers."""
    parser = ariadne.build_parser()
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        return sorted(action.choices)
    raise AssertionError("the parser offers no subcommands")


class SubcommandTests(unittest.TestCase):
    def test_every_subcommand_is_named_in_the_skill_and_the_readme(self):
        found = subcommands()
        self.assertTrue(found)
        for name, guide in STAGED_COMMAND_DOCS.items():
            self.assertIn(name, found)
            self.assertIn("ariadne.py %s" % name, read(guide))
        for path in (SKILL, README):
            text = read(path)
            for name in found:
                if name in STAGED_COMMAND_DOCS:
                    continue
                self.assertIn(
                    "ariadne.py %s" % name,
                    text,
                    "%s does not show the %s subcommand" % (path, name),
                )

    def test_the_module_docstring_lists_the_same_subcommands(self):
        listed = re.findall(r"(?m)^    (\w[\w-]*)\s{2,}", ariadne.__doc__)
        self.assertEqual(sorted(listed), subcommands())


class GateTests(unittest.TestCase):
    def test_the_skill_table_carries_every_gate(self):
        text = read(SKILL)
        numbers = sorted(
            [number for number, _ in gates.CORE_GATES] + list(gates.PREDICATE_GATES)
        )
        for number in numbers:
            self.assertRegex(
                text,
                r"(?m)^\| %d [A-Z]" % number,
                "the gate table has no row for gate %d" % number,
            )

    def test_the_skill_names_the_core_and_predicate_split_correctly(self):
        text = read(SKILL)
        for number, _ in gates.CORE_GATES:
            row = re.search(r"(?m)^\| %d [^|]+\| (\w+) \|" % number, text)
            self.assertIsNotNone(row, number)
            self.assertEqual(row.group(1), "core", "gate %d" % number)
        for number in gates.PREDICATE_GATES:
            row = re.search(r"(?m)^\| %d [^|]+\| (\w+) \|" % number, text)
            self.assertIsNotNone(row, number)
            self.assertEqual(row.group(1), "predicate", "gate %d" % number)


class VocabularyTests(unittest.TestCase):
    def test_the_skill_names_every_disposition(self):
        text = read(SKILL)
        for disposition in core_predicate.DISPOSITIONS:
            self.assertIn("`%s`" % disposition, text)

    def test_the_skill_names_both_determinism_classes(self):
        text = read(SKILL)
        for entry in core_predicate.DETERMINISM:
            self.assertIn("`%s`" % entry, text)


class PredicateTests(unittest.TestCase):
    def test_every_registered_type_is_one_the_documents_quote(self):
        registered = [type_uri for type_uri, _ in registry.DEFAULT.entries()]
        self.assertEqual(registered, sorted(module.TYPE for module, _ in DOCUMENTED))
        skill = read(SKILL)
        for module, doc in DOCUMENTED:
            with self.subTest(predicate=module.TYPE):
                self.assertIn(module.TYPE, skill)
                self.assertIn(module.TYPE, read(doc))

    def test_each_predicate_document_names_every_field(self):
        for module, doc in DOCUMENTED:
            text = read(doc)
            for field in module.PREDICATE_FIELDS:
                with self.subTest(predicate=module.TYPE, field=field):
                    self.assertIn(
                        "`%s`" % field, text, "%s omits %s" % (doc, field)
                    )

    def test_the_grounded_agent_guide_preserves_its_two_digest_domains(self):
        text = read(GROUNDED_AGENT_DOC)
        self.assertIn("semantic `release_digest`", text)
        self.assertIn("exact `release.json` bytes", text)
        self.assertIn("must not be equal", text)

    def test_the_grounded_agent_guide_names_the_non_conclusion_boundary(self):
        text = read(GROUNDED_AGENT_DOC)
        for field in ("score", "grade", "verdict", "threshold", "result count"):
            self.assertIn("`%s`" % field, text)


class PrintedCommandTests(unittest.TestCase):
    """A file path printed in a document is a claim that the file is there.

    Three of the faults found while auditing this predicate were in prose rather
    than in code, and a stale path is the cheapest of them to leave behind: a
    reader runs the command, gets an error about a missing file, and learns
    nothing about the tool.
    """

    def test_every_fixture_path_a_document_prints_exists(self):
        pattern = re.compile(r"(tests/fixtures/[\w./-]+\.json)")
        found = 0
        for name in sorted(os.listdir(os.path.join(PLUGIN, "docs"))):
            if not name.endswith(".md"):
                continue
            text = read(os.path.join(PLUGIN, "docs", name))
            for relative in pattern.findall(text):
                found += 1
                with self.subTest(document=name, path=relative):
                    self.assertTrue(
                        os.path.isfile(os.path.join(PLUGIN, relative)),
                        "docs/%s prints %s and it is not there" % (name, relative),
                    )
        self.assertTrue(found)


class FixtureTests(unittest.TestCase):
    def test_the_conformance_document_names_every_fixture(self):
        text = read(CONFORMANCE)
        directory = os.path.join(PLUGIN, "tests", "fixtures", "conformance")
        for name in sorted(os.listdir(directory)):
            if name.endswith(".json"):
                self.assertIn(
                    name, text, "docs/conformance.md does not list %s" % name
                )

    def test_the_grounded_agent_inventory_has_one_row_per_fixture(self):
        text = read(CONFORMANCE)
        directory = os.path.join(PLUGIN, "tests", "fixtures", "conformance")
        expected = sorted(
            name
            for name in os.listdir(directory)
            if "grounded-agent" in name and name.endswith(".json")
        )
        rows = sorted(
            re.findall(
                r"(?m)^\| `((?:pass|fail)-[^`]*grounded-agent[^`]*\.json)` \|",
                text,
            )
        )
        self.assertEqual(rows, expected)

    def test_the_examples_document_names_every_example(self):
        text = read(os.path.join(EXAMPLES, "README.md"))
        for directory in (EXAMPLES, os.path.join(EXAMPLES, "tampered")):
            for name in sorted(os.listdir(directory)):
                if name.endswith(".json"):
                    self.assertIn(
                        name, text, "examples/README.md does not list %s" % name
                    )


class ContractTests(unittest.TestCase):
    def test_the_runtime_contract_points_at_the_skill_that_exists(self):
        for relative in re.findall(r"`(skills/[^`]+/SKILL\.md)`", read(CONTRACT)):
            self.assertTrue(os.path.isfile(os.path.join(PLUGIN, relative)), relative)

    def test_no_shipped_document_links_outside_the_plugin(self):
        """The directory is published on its own, so a link that leaves it
        breaks wherever it lands."""
        for directory, _, names in os.walk(PLUGIN):
            if "__pycache__" in directory:
                continue
            for name in names:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(directory, name)
                text = read(path)
                if name == "EVOLUTION.md":
                    text = POLICY_CITATION.sub("", text)
                for link in re.findall(r"\]\((\.[^)]+)\)", text):
                    target = os.path.normpath(os.path.join(directory, link))
                    with self.subTest(document=os.path.relpath(path, PLUGIN)):
                        self.assertTrue(
                            os.path.commonpath([PLUGIN, target]) == PLUGIN,
                            "%s links to %s, outside the plugin" % (path, link),
                        )
                        self.assertTrue(
                            os.path.exists(target), "%s links to a missing %s"
                            % (path, link),
                        )


if __name__ == "__main__":
    unittest.main()
