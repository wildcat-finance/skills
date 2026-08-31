"""The shipped tree passes the three structural checkers, in one place.

Ephoros (observability), Phylax (off-chain surface) and Hypomnema (decision
records) each carry a "the shipped tree is clean" invariant: run the checker
over every plugin and assert it finds nothing. Those invariants used to live
inside each checker's own unit suite under plugins/hexaemeron, so a change to
Hexaemeron re-audited all fourteen plugins and inherited any sibling's lint
breakage. They are repo-wide invariants, so they live here, run once over the
whole tree, and the per-checker suites keep only their fixture-scoped behaviour
tests. The checkers are loaded by path exactly as their own suites load them.
"""

from pathlib import Path
import importlib.util
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGINS = ROOT / "plugins"
DOCS = ROOT / "docs"
SKILLS = PLUGINS / "hexaemeron" / "skills"


def _load(name, script):
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ephoros = _load("ephoros_lint", SKILLS / "ephoros" / "scripts" / "ephoros.py")
phylax = _load("phylax_lint", SKILLS / "phylax" / "scripts" / "phylax.py")
hypomnema = _load("hypomnema_lint", SKILLS / "hypomnema" / "scripts" / "hypomnema.py")


class ShippedTreeChecks(unittest.TestCase):
    def test_ephoros_finds_nothing_in_the_shipped_tree(self):
        findings = []
        for path in ephoros.walk([str(PLUGINS)]):
            findings.extend(ephoros.check(path))
        self.assertEqual([], [str(f) for f in findings])

    def test_phylax_finds_nothing_in_the_shipped_tree(self):
        findings = []
        for path in phylax.walk([str(PLUGINS)]):
            findings.extend(phylax.check(path))
        self.assertEqual([], [str(f) for f in findings])

    def test_hypomnema_record_pointers_all_resolve(self):
        # Folds the two former hypomnema whole-tree cases: pointers resolve, and
        # the walk reaches source files, not only Markdown.
        # A preserved specimen carries its origin's links. Repointing one so it
        # resolves here would change the bytes the preserving policy pins, and
        # the record would no longer be what was preserved.
        files = [
            path
            for path in hypomnema.walk([str(PLUGINS), str(DOCS)])
            if "specimens" not in path.parts
        ]
        self.assertTrue(any(p.suffix == ".py" for p in files))
        index = hypomnema.adr_index(files)
        findings = []
        for path in files:
            findings.extend(hypomnema.check(path, index))
        self.assertEqual([], [str(f) for f in findings])

    def test_every_decision_record_in_the_tree_passes(self):
        decisions = DOCS / "decisions"
        paths = hypomnema.walk([str(decisions)])
        self.assertGreaterEqual(len(paths), 6)
        findings = []
        for path in paths:
            findings.extend(hypomnema.check(path))
        self.assertEqual([], [str(f) for f in findings])


if __name__ == "__main__":
    unittest.main()
