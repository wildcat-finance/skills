"""Hold the decision records to one number each, and to their own numbering.

Two concurrent deliveries can each add a record, pick the same next number, give
their files different names, and merge without a conflict. Git sees no collision
because the filenames differ. The repository then carries two records with the
same number and nothing says so.

That is not hypothetical here. ADR-012 was accepted twice on 2026-08-22 and the
duplicate survived until 2026-08-24, when the licence record moved to 020. ADR-018
nearly went the same way: one delivery held it while another landed it, and only a
manual check caught the collision before both reached the default branch. There is
no exception list below, because the state it would have described is fixed.
"""

from __future__ import annotations

from pathlib import Path
import os
import re
import subprocess
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DECISIONS = REPOSITORY_ROOT / "docs/decisions"
FILENAME_RE = re.compile(r"\AADR-(\d+)-[a-z0-9.-]+\.md\Z")

def records():
    return sorted(p for p in DECISIONS.glob("ADR-*.md") if p.is_file())


def numbers_on(ref):
    """ADR numbers on a git ref, or None when the ref is not available.

    None is not "clean". The caller reports that the comparison could not run,
    because a check that silently skips is worse than no check: it reads as a
    pass.
    """
    result = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
        ["git", "-C", str(REPOSITORY_ROOT), "ls-tree", "-r", "--name-only", ref,
         "--", "docs/decisions"],
        capture_output=True, text=True, env=_git_env(),
    )
    if result.returncode != 0:
        return None
    found = {}
    for line in result.stdout.splitlines():
        name = line.rsplit("/", 1)[-1]
        match = FILENAME_RE.match(name)
        if match:
            found.setdefault(match.group(1), set()).add(name)
    return found


def _git_env():
    env = dict(os.environ)
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE",
                 "GIT_PREFIX", "GIT_INTERNAL_SUPER_PREFIX"):
        env.pop(name, None)
    return env


class DecisionRecordNumbering(unittest.TestCase):
    def test_the_directory_holds_records(self):
        self.assertTrue(records(), f"no decision records found under {DECISIONS}")

    def test_every_filename_follows_the_convention(self):
        bad = [p.name for p in records() if not FILENAME_RE.match(p.name)]
        self.assertEqual(bad, [], f"filenames outside ADR-NNN-kebab-case.md: {bad}")

    def test_no_two_records_share_a_number(self):
        seen: dict[str, list[str]] = {}
        for path in records():
            match = FILENAME_RE.match(path.name)
            if match:
                seen.setdefault(match.group(1), []).append(path.name)

        collisions = {n: sorted(f) for n, f in seen.items() if len(f) > 1}
        self.assertEqual(
            collisions, {},
            "two decision records share a number. There is deliberately no "
            "exception list: git merges differently-named files without a conflict, "
            "so nothing else catches this, and an allowlist would grow every time "
            "somebody found the check inconvenient. Renumber to the next free "
            "number and move every reference with it.",
        )

    def test_each_heading_states_the_number_its_filename_claims(self):
        """A renamed record keeps its old heading unless somebody looks.

        Renumbering by `git mv` alone leaves the H1 announcing the old number,
        so the file and the document disagree about which decision this is.
        """
        wrong = []
        for path in records():
            match = FILENAME_RE.match(path.name)
            if not match:
                continue
            first = path.read_text(encoding="utf-8").lstrip().splitlines()[0]
            heading = re.match(r"#\s*ADR-(\d+)\b", first)
            if heading is None:
                wrong.append(f"{path.name}: first heading is not `# ADR-NNN`: {first!r}")
            elif heading.group(1) != match.group(1):
                wrong.append(
                    f"{path.name}: heading says ADR-{heading.group(1)}"
                )
        self.assertEqual(wrong, [], "; ".join(wrong))


    def test_no_number_collides_with_one_already_on_the_default_branch(self):
        """The case a uniqueness check on this tree alone cannot catch.

        Two branches each add a record and each pick the same next number. Their
        filenames differ, so git merges both with no conflict and the duplicate
        only becomes visible once both have landed. Comparing against the default
        branch catches it while the second branch is still a pull request.

        This needs the default branch fetched. Where it is not, the test says so
        rather than passing quietly.
        """
        for ref in ("origin/main", "refs/remotes/origin/main", "main"):
            theirs = numbers_on(ref)
            if theirs is not None:
                break
        else:
            self.skipTest(
                "no local ref for the default branch, so this comparison could not "
                "run; fetch origin/main in CI (actions/checkout fetch-depth: 0) to "
                "make this check effective"
            )

        ours = {}
        for path in records():
            match = FILENAME_RE.match(path.name)
            if match:
                ours.setdefault(match.group(1), set()).add(path.name)

        collisions = []
        for number, names in sorted(ours.items()):
            if number not in theirs:
                continue
            added = names - theirs[number]
            if added:
                if len(names | theirs[number]) > 1:
                    collisions.append(
                        f"ADR-{number}: this branch adds {sorted(added)} while the "
                        f"default branch already has {sorted(theirs[number])}"
                    )
        self.assertEqual(
            collisions, [],
            "a decision record on this branch reuses a number that is already taken "
            "on the default branch. Renumber to the next free number and move every "
            "reference with it: " + "; ".join(collisions),
        )


if __name__ == "__main__":
    unittest.main()
