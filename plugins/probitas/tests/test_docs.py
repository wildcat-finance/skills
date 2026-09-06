"""The shipped prose has to agree with the code it describes.

A README that miscounts its own coverage gaps is a poor advertisement for a
tool whose whole claim is that it counts coverage honestly. These checks turn
the numbers in the documents into assertions, so the next person to add a venue
finds out here rather than from a reader.
"""

import argparse
import json
import os
import re
import unittest

from . import support

from probitas_lib import registry  # noqa: E402

DOCS = os.path.join(support.PLUGIN_ROOT, "docs")
REFERENCES = os.path.join(
    support.PLUGIN_ROOT, "skills", "probitas", "references"
)
README = os.path.join(support.PLUGIN_ROOT, "README.md")
RUNTIME_CONTRACT = os.path.join(support.PLUGIN_ROOT, "AGENTS.md")

WORDS = {
    2: "two",
    3: "three",
    4: "four",
    5: "five",
    6: "six",
    7: "seven",
    8: "eight",
    9: "nine",
    10: "ten",
    11: "eleven",
    12: "twelve",
    13: "thirteen",
    14: "fourteen",
    15: "fifteen",
}

# README fixture counts describe the corpus exercised through the shipped
# aggregate collector.  Focused adapter specimens can live beside it before an
# adapter is registered, so classify by a file consumed by a shipped adapter
# rather than by every top-level directory.
AGGREGATE_FIXTURE_ANCHORS = frozenset(
    {
        "wildcat.json",
        "morpho.json",
        "euler-v1.json",
        "euler-events.json",
        "euler-liquidations.json",
        "euler-vaults.json",
    }
)

# Step 4 publishes the Midnight adapter in the package version and the
# marketplace prose, so it crosses this release boundary and joins the counts
# the public documents are allowed to claim.
PUBLISHED_ADAPTER_IDS = frozenset(
    {"wildcat", "morpho-blue", "euler-v1", "euler", "morpho-midnight"}
)


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def counts():
    venues = registry.all_venues()
    gaps = [v for v in venues if v.id not in PUBLISHED_ADAPTER_IDS]
    # Keyless is not the same as buildable. Maple answers without a key and
    # publishes no schema, so it needs something nobody here can supply.
    adapter_only = [v for v in gaps if v.auth == "none" and v.id != "maple"]
    return len(venues), len(PUBLISHED_ADAPTER_IDS), len(gaps), len(adapter_only)


class TestTheDocumentsCountCorrectly(unittest.TestCase):
    def setUp(self):
        self.total, self.built, self.gaps, self.adapter_only = counts()

    def test_the_readme_states_the_registry_size(self):
        self.assertIn(
            WORDS[self.total].capitalize(), read(README),
            f"the README does not say there are {self.total} venues",
        )

    def test_the_readme_states_the_number_of_gaps(self):
        self.assertIn(
            f"other {WORDS[self.gaps]}", read(README),
            f"the README does not say {self.gaps} venues have no adapter",
        )

    def test_the_readme_states_how_many_need_only_an_adapter(self):
        self.assertIn(
            f"{WORDS[self.adapter_only].capitalize()} of the {WORDS[self.gaps]} gaps",
            read(README),
            f"the README miscounts the {self.adapter_only} venues that need "
            "only an adapter",
        )

    def test_the_venues_reference_agrees_with_the_readme(self):
        text = read(os.path.join(REFERENCES, "venues.md"))
        self.assertIn(WORDS[self.total].capitalize(), text)
        self.assertIn(f"{WORDS[self.adapter_only].capitalize()} of the {WORDS[self.gaps]}", text)

    def test_the_contributor_guide_agrees_too(self):
        text = read(os.path.join(DOCS, "adding-a-venue.md"))
        self.assertIn(f"{WORDS[self.built]} of the {WORDS[self.total]}", text)
        self.assertIn(f"other {WORDS[self.gaps]}", text)

    def test_the_three_reader_surfaces_state_the_midnight_limits(self):
        """The limits are the point of shipping a fail-closed venue.

        A reader who learns Midnight ships and not what its coverage excludes
        has been told the useful half. Each claim below is a boundary the
        adapter actually enforces, so prose that drops one is overclaiming.
        """
        surfaces = {
            "README.md": read(README),
            "SKILL.md": read(os.path.join(os.path.dirname(REFERENCES), "SKILL.md")),
            "venues.md": read(os.path.join(REFERENCES, "venues.md")),
        }
        claims = {
            "Base-scoped": ("Base chain id 8453",),
            "API-scoped, not archive-complete": ("API-scoped",),
            "unpublished lower bound": ("lower bound is unpublished", "unpublished\nhistory lower bound", "unpublished history lower bound"),
            "no partial answer": ("no records and a\nnamed gap", "no records and a named gap", "no records and a named gap instead"),
            "secondary close refused": ("secondary-market borrow exit is refused",),
            "late settlement is not repayment": ("never as voluntary repayment",),
        }
        for name, text in surfaces.items():
            flat = " ".join(text.split())
            for claim, variants in claims.items():
                with self.subTest(surface=name, claim=claim):
                    self.assertTrue(
                        any(" ".join(v.split()) in flat for v in variants),
                        f"{name} does not state the {claim} limit",
                    )

    def test_every_venue_in_the_registry_is_named_somewhere_a_reader_looks(self):
        text = read(README) + read(os.path.join(REFERENCES, "venues.md"))
        for venue in registry.all_venues():
            with self.subTest(venue=venue.id):
                self.assertIn(venue.name, text)

    def test_the_publication_pass_left_no_adapter_unpublished(self):
        """Both directions, so neither set can drift from the other.

        Midnight was the one adapter this boundary held back while Step 3
        shipped its runtime. Step 4 published it, so the sets now agree: a
        registered adapter the documents do not count, or a counted adapter
        with no runtime, is a defect either way.
        """
        runtime = {venue.id for venue in registry.implemented()}
        self.assertEqual(runtime - PUBLISHED_ADAPTER_IDS, set())
        self.assertEqual(PUBLISHED_ADAPTER_IDS - runtime, set())


class TestTheQuickstartIsTheOneThatWasRun(unittest.TestCase):
    """The README's commands have to produce the committed example dossier."""

    def fixture_in(self, path):
        found = re.findall(r"--fixtures (?:tests/)?fixtures/([a-z-]+)", read(path))
        return set(found)

    def test_the_readme_uses_the_demo_fixture(self):
        self.assertEqual(
            self.fixture_in(README),
            {"demo"},
            "the README quickstart does not build the committed example dossier",
        )

    def test_the_contributor_guide_uses_it_too(self):
        self.assertEqual(self.fixture_in(os.path.join(DOCS, "adding-a-venue.md")), {"demo"})

    def test_the_demo_fixture_carries_all_shipped_venues(self):
        directory = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures", "demo")
        present = set(os.listdir(directory))
        self.assertEqual(
            present,
            {
                "wildcat.json",
                "morpho.json",
                "euler-v1.json",
                "euler-events.json",
                "euler-liquidations.json",
                "euler-vaults.json",
                "morpho-midnight.json",
            },
        )

    def test_every_aggregate_fixture_carries_a_midnight_response(self):
        directory = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")
        aggregate = [
            name
            for name in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, name))
            and AGGREGATE_FIXTURE_ANCHORS.intersection(
                os.listdir(os.path.join(directory, name))
            )
        ]
        self.assertEqual(len(aggregate), 11)
        for name in aggregate:
            with self.subTest(name=name):
                fixture = os.path.join(directory, name, "morpho-midnight.json")
                self.assertTrue(os.path.isfile(fixture))
                with open(fixture, encoding="utf-8") as handle:
                    source = json.load(handle)["source"]
                self.assertEqual(source["date"], "2026-08-28")
                self.assertEqual(source["origin"], "https://api.morpho.org")


class TestTheReadmeDescribesTheToolThatExists(unittest.TestCase):
    """The two things that went stale last time: the CLI and the fixtures."""

    def test_every_subcommand_is_named(self):
        import probitas

        parser = probitas.build_parser()
        actions = [
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        ]
        commands = set(actions[0].choices)
        text = read(README)
        for command in sorted(commands):
            with self.subTest(command=command):
                self.assertIn(f"probitas.py {command}", text)

    def test_every_collect_flag_is_documented(self):
        import probitas

        parser = probitas.build_parser()
        sub = [
            a for a in parser._actions if isinstance(a, argparse._SubParsersAction)
        ][0]
        flags = {
            option
            for action in sub.choices["collect"]._actions
            for option in action.option_strings
            if option.startswith("--") and option != "--help"
        }
        text = read(README)
        for flag in sorted(flags):
            with self.subTest(flag=flag):
                self.assertIn(f"`{flag}`", text)

    def test_the_fixture_count_is_right(self):
        directory = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")
        shipped = [
            name
            for name in os.listdir(directory)
            if os.path.isdir(os.path.join(directory, name))
            and AGGREGATE_FIXTURE_ANCHORS.intersection(
                os.listdir(os.path.join(directory, name))
            )
        ]
        self.assertIn(
            f"{WORDS[len(shipped)].capitalize()} of them",
            read(README),
            f"the README does not say there are {len(shipped)} fixtures",
        )

    def test_the_working_directory_is_stated(self):
        """The quickstart is relative to the plugin, the tests to the root."""
        text = read(README)
        self.assertIn("From this directory, `plugins/probitas`", text)
        self.assertIn("From the repository root", text)

    def test_the_runtime_contract_routes_and_bounds_the_diff_command(self):
        text = " ".join(read(RUNTIME_CONTRACT).split())
        for statement in (
            "compare two Probitas evidence files for the same subject",
            "`diff` reaches no network",
            "atomically",
            "must not alias either input",
        ):
            with self.subTest(statement=statement):
                self.assertIn(statement, text)


class TestTheDescriptionAgreesWithItself(unittest.TestCase):
    """One line describes this plugin in six places. They have to match."""

    def manifests(self):
        import json

        root = os.path.dirname(os.path.dirname(support.PLUGIN_ROOT))
        paths = {
            "claude plugin": os.path.join(
                support.PLUGIN_ROOT, ".claude-plugin", "plugin.json"
            ),
            "codex plugin": os.path.join(
                support.PLUGIN_ROOT, ".codex-plugin", "plugin.json"
            ),
            "claude marketplace": os.path.join(
                root, ".claude-plugin", "marketplace.json"
            ),
        }
        out = {}
        for label, path in paths.items():
            with open(path, encoding="utf-8") as handle:
                out[label] = json.load(handle)
        return out

    def test_the_short_description_is_the_same_everywhere(self):
        loaded = self.manifests()
        codex = loaded["codex plugin"]["interface"]["shortDescription"]
        entry = next(
            p for p in loaded["claude marketplace"]["plugins"] if p["name"] == "probitas"
        )
        yaml = read(
            os.path.join(support.PLUGIN_ROOT, "skills", "probitas", "agents", "openai.yaml")
        )
        self.assertEqual(entry["description"], codex)
        self.assertIn(codex.rstrip("."), yaml)

    def test_both_plugin_manifests_describe_it_identically(self):
        loaded = self.manifests()
        self.assertEqual(
            loaded["claude plugin"]["description"],
            loaded["codex plugin"]["description"],
        )

    def test_nothing_still_calls_it_undercollateralised_only(self):
        """The motive is undercollateralised lending; the coverage is wider.

        Conflating the two is what made the old description too narrow, and it
        read as though the tool only worked on Wildcat-shaped borrowers.
        """
        narrow = "dossier for undercollateralised lending"
        loaded = self.manifests()
        self.assertNotIn(narrow, loaded["claude plugin"]["description"])
        self.assertNotIn(narrow, loaded["codex plugin"]["description"])
        self.assertNotIn(
            "counterparty who wants an undercollateralised market", read(README)
        )


class TestNoInternalInfrastructureLeaked(unittest.TestCase):
    """This tree is bound for a public repository."""

    def test_no_wildcat_endpoint_or_credential_appears_anywhere(self):
        # Assembled at runtime so the literals never appear in any file,
        # including this one. Exempting the test from its own scan would be
        # the sort of hole this check exists to close.
        forbidden = (
            "hinter" + "light",
            "PROBITAS_RPC_" + "TOKEN=",
            "api_" + "key=",
            "Bear" + "er ",
        )
        for root, _, files in os.walk(support.PLUGIN_ROOT):
            if "__pycache__" in root:
                continue
            for name in files:
                path = os.path.join(root, name)
                try:
                    with open(path, encoding="utf-8") as handle:
                        text = handle.read()
                except (UnicodeDecodeError, OSError):
                    continue
                for token in forbidden:
                    with self.subTest(path=path, token=token):
                        self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
