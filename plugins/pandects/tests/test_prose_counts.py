"""The hand-written corpus-size sentences must match the catalogue.

Two browsing documents state the corpus size in prose and neither derives it:
the pandects landing README and the repository root README. The rendered
catalogue derives its counts and the adapters are held to theirs by the rest of
this suite; these sentences are hand-written and a frontier run that adds a law
has to remember them. Anchored in pandects's own suite so the check runs when
the catalogue changes rather than on every unrelated gated change (it lived in
tests/test_marketplace_prose.py until the test-scoping de-duplication).
"""

from pathlib import Path
import json
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


class PandectsProseCountTests(unittest.TestCase):
    def test_pandects_prose_counts_the_laws_the_catalogue_holds(self):
        words = [
            "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven",
            "Eight", "Nine", "Ten", "Eleven", "Twelve",
        ]
        catalogue = json.loads(
            (PLUGIN_ROOT / "catalogue" / "pandects.json").read_text(encoding="utf-8")
        )
        laws = catalogue["laws"]
        total = words[len(laws)].lower()
        exact = words[len([law for law in laws if law["bounds"] == "exact"])]
        families = words[len({law["family"] for law in laws})].lower()

        landing = (PLUGIN_ROOT / "README.md").read_text(encoding="utf-8")
        for claim in (
            "%s laws in %s families." % (words[len(laws)], families),
            "%s of the %s laws are exact." % (exact, total),
            "`laws` prints %s laws with their applicability." % total,
        ):
            with self.subTest(document="plugins/pandects/README.md", claim=claim):
                self.assertIn(claim, landing)



if __name__ == "__main__":
    unittest.main()
