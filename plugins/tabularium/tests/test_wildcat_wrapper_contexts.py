"""Wildcat V2 wrapper contexts from an Alexandria `wrapper-subjects` component (skills#2116).

A verified release whose plan declared wrapper instances yields one `wrapper`
context per declared wrapper, with its market as both market and asset, so
the wrapper's native `Deposit`, `Withdraw` and `Transfer` logs map to rows
whose market-token assets name that market. An undeclared wrapper gets no
context. A release without the component maps as before. Every release here
is constructed; no record was observed on a chain.
"""

from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = REPO_ROOT / "plugins" / "tabularium" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

if __package__:
    from . import wildcat_wrapper_fixture as fixture
    from .wildcat_v3_registry_fixture import build_registry_release
else:
    import wildcat_wrapper_fixture as fixture
    from wildcat_v3_registry_fixture import build_registry_release

from tabularium_lib import wildcat_rows  # noqa: E402
from tabularium_lib.core import TabulariumError  # noqa: E402
from tabularium_lib.wildcat_source import WRAPPER_FORMAT, _wrapper_contexts  # noqa: E402


TOPIC = "0x317d343bad96f4924450e809267dcfa70e37270e3bb036b5d6d04e3befd47a64"
FACTORY_COMMIT = "c7be4039f8f383a9dda4e45f63331c17d63f9ed9"
EXPECTED = REPO_ROOT / "plugins" / "tabularium" / "examples" / "wildcat-v2-v0" / "expected.json"


def _document(root, name):
    return json.loads((root / name).read_bytes())


def _rows(root):
    return [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]


class WrapperReleaseTests(unittest.TestCase):
    """One declared wrapper with three native logs, and one undeclared wrapper."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="tabularium-wrapper-contexts-")
        cls.root = Path(cls.temporary.name).resolve() / "release"
        fixture.build_wrapper_release(cls.root, "wildcat-v2-constructed-wrapper-v0")
        cls.source = _document(cls.root, "source.json")
        cls.rows = _rows(cls.root)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_each_declared_wrapper_log_maps_to_a_row_whose_asset_is_its_market(self):
        rows = {row["action"].split(".", 1)[1]: row for row in self.rows}
        expected = {
            "wrapper-deposit": [("market-token-assets", "100", fixture.MARKET),
                                ("wrapper-shares", "80", fixture.WRAPPER)],
            "wrapper-withdrawal": [("market-token-assets", "60", fixture.MARKET),
                                   ("wrapper-shares", "45", fixture.WRAPPER)],
            "wrapper-transfer": [("wrapper-shares", "5", fixture.WRAPPER)],
        }
        self.assertEqual(set(rows), {"borrow", "debt-repaid", *expected})
        for action, amounts in expected.items():
            with self.subTest(action=action):
                row = rows[action]
                self.assertEqual(row["instrument"]["id"], fixture.WRAPPER)
                self.assertEqual([(a["kind"], a["base_units"], a["asset"]) for a in row["amounts"]], amounts)
                self.assertEqual(row["instrument"]["type"], "wildcat-v2-wrapper")

    def test_the_declared_wrapper_context_binds_its_market_as_market_and_asset(self):
        context = self.source["contexts"][fixture.WRAPPER]
        self.assertEqual(context["role"], "wrapper")
        self.assertEqual(context["market"], fixture.MARKET)
        self.assertEqual(context["asset"], fixture.MARKET)
        self.assertEqual(context["concrete_contract"], "Wildcat4626Wrapper")
        self.assertEqual([item["class"] for item in context["source"]],
                         ["checked-wrapper-subject-context", "checked-positional-epoch-context"])
        subject = context["source"][0]
        self.assertEqual(subject["reference"]["component"], "wrapper-subjects")
        self.assertEqual(subject["reference"]["selector"], "/wrappers/0")
        self.assertEqual(subject["native"]["wrapper"], fixture.WRAPPER)
        self.assertEqual(subject["native"]["market"], fixture.MARKET)
        self.assertTrue(subject["native"]["declared"])
        self.assertNotIn("borrower_context", context)
        market = self.source["contexts"][fixture.MARKET]
        self.assertEqual(market["role"], "market")
        self.assertNotEqual(market["asset"], fixture.MARKET)

    def test_an_undeclared_wrapper_gets_no_context_and_is_named_in_scope(self):
        self.assertNotIn(fixture.UNDECLARED_WRAPPER, self.source["contexts"])
        scope = self.source["scope"]
        self.assertEqual(scope["kind"], "recorded-interval")
        self.assertEqual(scope["wrapper_native_coverage"], "declared-wrapper-subjects")
        self.assertEqual(scope["wrapper_subjects"],
                         {"declared": [fixture.WRAPPER], "undeclared": [fixture.UNDECLARED_WRAPPER]})
        self.assertNotIn(fixture.WRAPPER, scope["subjects"])
        self.assertIn(fixture.WRAPPER_FACTORY, scope["subjects"])
        self.assertEqual(_document(self.root, "capture.json")["scope"], scope)

    def test_the_factorys_wrapper_deployed_logs_stay_unsupported(self):
        dispositions = Counter(item["disposition"] for item in self.source["dispositions"])
        self.assertEqual(dispositions, {"primary": 5, "unsupported-canonical-meaning": 3})
        by_role = Counter((item["emitter_role"], item["disposition"]) for item in self.source["mapping_records"])
        self.assertEqual(by_role[("wrapper", "primary")], 3)
        self.assertEqual(by_role[("wrapper-factory", "unsupported-canonical-meaning")], 2)
        self.assertEqual(by_role[("factory", "unsupported-canonical-meaning")], 1)
        wrapper_selectors = {row["provenance"]["source_selector"] for row in self.rows
                             if row["instrument"]["id"] == fixture.WRAPPER}
        self.assertEqual(len(wrapper_selectors), 3)
        self.assertTrue(wrapper_selectors <= {item["source_selector"] for item in self.source["mapping_records"]
                                              if item["disposition"] == "primary"})


class ReleaseWithoutTheComponentTests(unittest.TestCase):
    """A plan that declares no wrapper reaches none of the wrapper code."""

    def test_a_release_without_the_component_maps_as_before(self):
        with tempfile.TemporaryDirectory(prefix="tabularium-wrapper-legacy-") as temporary:
            root = Path(temporary).resolve() / "release"
            fixture.build_wrapper_release(root, "wildcat-v2-constructed-undeclared-v0", declare=False)
            source = _document(root, "source.json")
            manifest = _document(root / "source" / "raw-release", "manifest.json")
            self.assertNotIn("wrapper-subjects", {item["name"] for item in manifest["components"]})
            scope = source["scope"]
            self.assertEqual(scope["wrapper_native_coverage"], "not-established")
            self.assertNotIn("wrapper_subjects", scope)
            self.assertNotIn(fixture.WRAPPER, source["contexts"])
            self.assertNotIn(fixture.UNDECLARED_WRAPPER, source["contexts"])
            self.assertEqual({row["action"] for row in _rows(root)},
                             {"wildcat-v2.borrow", "wildcat-v2.debt-repaid"})
            classes = {item["class"] for context in source["contexts"].values() for item in context["source"]}
            self.assertNotIn("checked-wrapper-subject-context", classes)

    def test_the_public_registry_context_specimen_still_rebuilds_to_its_pinned_bytes(self):
        expected = json.loads(EXPECTED.read_bytes())["registry-context/release"]
        with tempfile.TemporaryDirectory(prefix="tabularium-wrapper-pinned-") as temporary:
            root = Path(temporary).resolve() / "release"
            build_registry_release(root, "wildcat-v2", "wildcat-v2-constructed-registry-context-v0")
            for name, pinned in expected["files"].items():
                with self.subTest(file=name):
                    raw = (root / name).read_bytes()
                    self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()),
                                     (pinned["bytes"], pinned["sha256"]))


class WrapperContextRefusalTests(unittest.TestCase):
    """`_wrapper_contexts` refuses what no context can be built from."""

    def fresh(self):
        self.contexts = {fixture.MARKET: {"role": "market", "asset": None, "source": []}}
        self.entries = {fixture.WRAPPER_FACTORY: {"role": "wrapper-factory", "source_commit": FACTORY_COMMIT}}
        self.components = {"wrapper-subjects": {"sha256": "sha256:" + "0" * 64}}
        self.captures = {"wrapper-subjects": {"id": "capture-0"}}

    def setUp(self):
        self.fresh()

    @staticmethod
    def row(wrapper=fixture.WRAPPER, market=fixture.MARKET, declared=True):
        return {"wrapper": wrapper, "market": market, "declared": declared,
                "deployment": {"block_number": "1", "log_index": 0,
                               "transaction_hash": "0x" + "11" * 32, "transaction_index": 0}}

    def document(self, *rows):
        return {"format": WRAPPER_FORMAT, "factory": fixture.WRAPPER_FACTORY, "topic": TOPIC,
                "window": {"start": "1", "end": "2"}, "wrappers": list(rows) or [self.row()]}

    def build(self, document, venue="wildcat-v2"):
        return _wrapper_contexts(venue, document, self.contexts, self.entries, self.components, self.captures)

    def test_a_declared_row_builds_one_context_the_row_mapper_admits(self):
        result = self.build(self.document(self.row(), self.row(fixture.UNDECLARED_WRAPPER, declared=False)))
        self.assertEqual(result, {"declared": [fixture.WRAPPER], "undeclared": [fixture.UNDECLARED_WRAPPER]})
        context = self.contexts[fixture.WRAPPER]
        self.assertEqual((context["role"], context["asset"], context["market"]),
                         ("wrapper", fixture.MARKET, fixture.MARKET))
        self.assertEqual(context["concrete_contract"], "Wildcat4626Wrapper")
        self.assertEqual(context["source"][0]["class"], "checked-wrapper-subject-context")
        self.assertEqual(context["source"][0]["reference"]["selector"], "/wrappers/0")
        self.assertEqual(wildcat_rows._context("wildcat-v2", fixture.WRAPPER, context),
                         [wildcat_rows.context_selector(context["source"][0])])
        self.assertNotIn(fixture.UNDECLARED_WRAPPER, self.contexts)

    def test_refusals_name_their_cause_and_add_no_context(self):
        cases = (
            ("admitted only for wildcat-v2", self.document(), "wildcat-v1"),
            ("unsupported format",
             dict(self.document(), format="alexandria-wildcat-v2-wrapper-subjects/v2"), "wildcat-v2"),
            ("factory the registry does not list", dict(self.document(), factory="0x" + "ef" * 20), "wildcat-v2"),
            ("no registry market context", self.document(self.row(market=fixture.WRAPPER_FACTORY)), "wildcat-v2"),
            ("already an emitter context", self.document(self.row(wrapper=fixture.MARKET)), "wildcat-v2"),
            ("repeat a wrapper", self.document(self.row(), self.row(declared=False)), "wildcat-v2"),
            ("declaration is not boolean", self.document(self.row(declared="yes")), "wildcat-v2"),
            ("identity is invalid", self.document(self.row(wrapper="0xAB" + "ab" * 19)), "wildcat-v2"),
            ("count is invalid", dict(self.document(), wrappers=[]), "wildcat-v2"),
            ("unknown or incomplete shape", dict(self.document(), extra=1), "wildcat-v2"),
        )
        for message, document, venue in cases:
            with self.subTest(message=message):
                self.fresh()
                with self.assertRaisesRegex(TabulariumError, message):
                    self.build(document, venue)
                self.assertEqual(set(self.contexts) - {fixture.MARKET, fixture.WRAPPER}, set())
        self.fresh()
        self.entries[fixture.WRAPPER_FACTORY]["source_commit"] = "0" * 40
        with self.assertRaisesRegex(TabulariumError, "no concrete ABI at the factory's source commit"):
            self.build(self.document())
        self.assertNotIn(fixture.WRAPPER, self.contexts)


if __name__ == "__main__":
    unittest.main()
