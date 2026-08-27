"""Every document this repository ships passes its own prose lint.

Imprimatur is the organisation's banned lexicon, and each plugin's prose was
brought to a clean score one document at a time. Nothing held them there. A
banned word could return to any shipped file and no test would notice, which is
how `leverage` sat in Kronos's fourth scoring axis long enough for a reader to
find it by eye rather than by suite.

Scope, and why each exclusion is here rather than a matter of taste:

- `audit/` and `docs/**` are records of what was written at the time. Editing a
  logged audit round or a delivered spec to satisfy a later lexicon rewrites
  history to look tidier than it was.
- `EVOLUTION.md` history rows are governed records. The live frontier above
  `## History` stays in scope; prior generation explanations do not.
- The vendored Pashov skills keep their upstream instructional register. Their
  `NOTICE.md` files record the local distribution changes, and Wildcat's house
  lint does not rewrite third-party source for style.
- `LICENSE` and `NOTICE` files are legal text nobody may reword.
- A frozen eval corpus is measurement input. Rewriting it changes what the
  numbers beside it mean.

Everything else is shipped prose and is held clean.
"""

from pathlib import Path
import importlib.util
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
LINT = ROOT / "plugins" / "hexaemeron" / "skills" / "imprimatur" / "scripts" / "imprimatur.py"

VENDORED = ("x-ray", "solidity-auditor", "fizz", "fizz-convert", "fizz-sync")


def imprimatur():
    """The lint as a module.

    Called in process rather than shelled out once per file: 134 subprocess
    launches took the root suite from 0.12s to 7.1s, and a suite that slow gets
    a test deleted rather than a document fixed. `build` is the same entry the
    CLI uses, so the score here is the score the command reports.
    """
    spec = importlib.util.spec_from_file_location("imprimatur_lint", LINT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shipped_markdown():
    """Tracked Markdown this repository ships as its own prose."""
    listed = subprocess.run(
        [
            "git", "-C", str(ROOT), "ls-files", "--cached", "--others",
            "--exclude-standard", "--", "*.md",
        ],
        capture_output=True, text=True, check=True).stdout.split("\n")
    for name in listed:
        if not name:
            continue
        if not (ROOT / name).is_file():
            continue
        parts = Path(name).parts
        if "audit" in parts or "docs" in parts or "evals" in parts:
            continue
        if any(part in VENDORED for part in parts):
            continue
        if Path(name).stem in ("LICENSE", "NOTICE"):
            continue
        yield name


def lint(module, name):
    text = (ROOT / name).read_text(encoding="utf-8")
    if Path(name).name == "EVOLUTION.md":
        text = text.partition("\n## History\n")[0]
    report = module.build(text)
    return report["score"], report["defects"]


class ShippedProseLintTests(unittest.TestCase):
    def test_the_lint_is_where_this_test_expects_it(self):
        # A moved script would otherwise make every case below fail for the
        # wrong reason, or pass by finding nothing to check.
        self.assertTrue(LINT.is_file(), LINT)

    def test_the_scope_is_not_empty(self):
        """A filter that excluded everything would pass in silence."""
        found = list(shipped_markdown())
        self.assertGreater(len(found), 50, found[:10])
        # The documents most likely to drift are in scope.
        for expected in ("README.md",
                         "plugins/hexaemeron/skills/kronos/SKILL.md",
                         "plugins/hexaemeron/skills/fiat/SKILL.md"):
            self.assertIn(expected, found)

    def test_history_and_vendored_text_stay_out_of_scope(self):
        found = set(shipped_markdown())
        for excluded in ("audit/AUDIT.md",
                         "plugins/probitas/audit/AUDIT.md",
                         "docs/protasis-discipline-cores/study.md"):
            self.assertNotIn(excluded, found)
        self.assertFalse([n for n in found if "x-ray" in Path(n).parts])

    def test_evolution_history_stays_out_of_the_live_prose_gate(self):
        module = imprimatur()
        name = "plugins/hexaemeron/skills/fiat/EVOLUTION.md"
        full = module.build((ROOT / name).read_text(encoding="utf-8"))
        self.assertTrue(
            [
                hit for hit in full["hits"]
                if hit["family"] == "causal_subject_has_no"
            ]
        )
        _, defects = lint(module, name)
        self.assertEqual(defects, 0)

    def test_causal_subject_has_no_family_is_active(self):
        module = imprimatur()
        report = module.build(
            "because this repository has no checked Atlas hand-off for them"
        )
        hits = [
            hit for hit in report["hits"]
            if hit["family"] == "causal_subject_has_no"
        ]
        self.assertEqual(report["defects"], 1)
        self.assertEqual(
            [
                (hit["pass"], hit["severity"], hit["signal_only"])
                for hit in hits
            ],
            [("structural", "medium", False)],
        )
        direct = module.build(
            "No checked Atlas hand-off exists for them, so they stay on the manual route."
        )
        self.assertFalse(
            [
                hit for hit in direct["hits"]
                if hit["family"] == "causal_subject_has_no"
            ]
        )

    def test_every_shipped_document_scores_clean(self):
        module = imprimatur()
        dirty = []
        for name in shipped_markdown():
            score, defects = lint(module, name)
            if defects:
                dirty.append(f"{name}: {score}/100, {defects} defect(s)")
        self.assertEqual(
            dirty, [],
            "shipped prose carries lint defects; run the lint on each file "
            "named here and rewrite the sentence rather than swapping a "
            "neighbouring word from the same family:\n  " + "\n  ".join(dirty))


if __name__ == "__main__":
    unittest.main()
