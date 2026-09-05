"""Hold the commit gate to what the run behind it promised.

Two things are held here. The record that says where the gate lives, because
the record is the part a reader reaches for once the scripts are ordinary and
nobody remembers the alternatives. And the gate itself: what it refuses, what
it says when it refuses, and that the tracked scripts a fresh clone gets are
the ones a checkout actually runs.

The record ships unnumbered. The arithmetic against this base gives ADR-074 and
run #856 is open on the same base claiming the same number;
`tests/test_decision_records.py` compares against `origin/main`, so it sees the
collision only once the other number has landed. That check is left exactly as
it is, and it globs `ADR-*.md`, so it never sees a draft. These cases hold the
draft's shape in its place, and one of them refuses an `ADR-074-*.md` file so
the run cannot drift back into the collision it is avoiding.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DECISIONS = REPOSITORY_ROOT / "docs" / "decisions"
RECORD = DECISIONS / "draft-activate-the-commit-gate-from-a-tracked-hooks-directory.md"

REQUIRED_SECTIONS = ("Status", "Context", "Decision", "Alternatives", "Consequences")
NUMBERED_HEADING = re.compile(r"\A#\s*ADR-\d+\b")
SECTION_HEADING = re.compile(r"\A##\s+(?P<name>\S.*?)\s*\Z")

# Each rejected option from the study's design section, and the word the record
# has to reach for beside it. Naming an option without saying what it cost is
# the failure mode the issue's first acceptance condition is aimed at.
REJECTED = ("installed-hooks", "ci-only", "null option")


def record_text() -> str:
    return RECORD.read_text(encoding="utf-8")


def sections(text: str) -> dict[str, str]:
    """The record's `## ` sections, each mapped to its own body."""
    found: dict[str, list[str]] = {}
    current: str | None = None
    for line in text.splitlines():
        heading = SECTION_HEADING.match(line)
        if heading:
            current = heading.group("name")
            found.setdefault(current, [])
            continue
        if current is not None:
            found[current].append(line)
    return {name: "\n".join(body) for name, body in found.items()}


def bullets(body: str) -> list[str]:
    """Top-level `- ` bullets, each carrying its indented continuation lines."""
    found: list[list[str]] = []
    for line in body.splitlines():
        if line.startswith("- "):
            found.append([line])
        elif found and line.strip() and line.startswith(" "):
            found[-1].append(line)
    return [" ".join(part.strip() for part in block) for block in found]


class DecisionRecordTests(unittest.TestCase):
    def test_the_record_is_at_the_path_the_runbook_names(self):
        self.assertTrue(
            RECORD.is_file(),
            f"the decision record for the commit gate is not at {RECORD}",
        )

    def test_the_first_heading_is_a_title_rather_than_a_number(self):
        """A numbered heading here would claim a number nothing has assigned.

        The filename carries no `ADR-` prefix, so the heading must not carry a
        number either; the two disagreeing is exactly what
        `tests/test_decision_records.py` catches on the records it does see.
        """
        first = record_text().lstrip().splitlines()[0]
        self.assertTrue(first.startswith("# "), f"first heading is not an H1: {first!r}")
        self.assertIsNone(
            NUMBERED_HEADING.match(first),
            f"the draft claims a number nothing has assigned yet: {first!r}",
        )

    def test_the_record_carries_every_required_section(self):
        present = sections(record_text())
        missing = [name for name in REQUIRED_SECTIONS if name not in present]
        self.assertEqual(missing, [], f"sections missing from {RECORD.name}: {missing}")

    def test_the_alternatives_say_what_each_rejected_option_loses(self):
        body = sections(record_text()).get("Alternatives", "")
        self.assertTrue(body.strip(), "the Alternatives section is empty")
        silent = []
        for option in REJECTED:
            named = [b for b in bullets(body) if option in b]
            if not named:
                silent.append(f"{option}: not named")
            elif not any("loses" in b for b in named):
                silent.append(f"{option}: named without saying what it loses")
        self.assertEqual(silent, [], "; ".join(silent))

    def test_the_consequences_call_the_green_record_a_convenience(self):
        body = sections(record_text()).get("Consequences", "")
        self.assertIn(
            "convenience rather than proof", body,
            "the consequences must state that the green record is a convenience "
            "rather than proof that the suite ran; a reader who takes it as "
            "proof is trusting a record its own subject can write",
        )

    def test_no_record_claims_the_number_this_draft_is_avoiding(self):
        claimed = sorted(p.name for p in DECISIONS.glob("ADR-074-*.md"))
        self.assertEqual(
            claimed, [],
            "this run ships its record unnumbered because run #856 is open on "
            f"the same base and claims ADR-074; found {claimed}",
        )


# --- the gate itself ------------------------------------------------------

GITHOOKS = REPOSITORY_ROOT / ".githooks"
HOOK = GITHOOKS / "pre-commit"
GREENLIGHT = GITHOOKS / "greenlight"
HOOKS_README = GITHOOKS / "README.md"
RECORD_NAME = "LAST_GREEN"

# The documented escape hatch, as one literal string. Renaming it in the gate
# without renaming it here is the drift this constant exists to catch.
BYPASS_TOKEN = "FIAT_SKIP_PRECOMMIT"

# The one activation, as argv. The value stays relative: an absolute path would
# point every linked worktree at one worktree's copy of the gate.
ACTIVATION = ("config", "core.hooksPath", ".githooks")

REFUSAL_PREFIX = "pre-commit: refused,"

# Fixture commits carry their own identity and no signature, so the gate is
# what is under test rather than the machine's git configuration.
GIT_BASE = (
    "git",
    "-c", "commit.gpgsign=false",
    "-c", "user.name=commit gate fixture",
    "-c", "user.email=fixture@example.invalid",
)

# Anything git exports into a hook, or a caller exports at us, that could
# repoint a fixture's git commands at the repository this suite runs inside.
INHERITED_GIT_VARIABLES = (
    "GIT_DIR",
    "GIT_INDEX_FILE",
    "GIT_WORK_TREE",
    "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES",
    "GIT_COMMON_DIR",
    "GIT_NAMESPACE",
    "GIT_PREFIX",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_CONFIG_PARAMETERS",
    "GIT_CONFIG_COUNT",
    # The file selectors reach the same end one indirection out, so a fixture
    # that inherited one would be measuring the caller's configuration rather
    # than the case's.
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_SYSTEM",
)

PASSING_SUITE = """import unittest


class FixtureTests(unittest.TestCase):
    def test_the_fixture_suite_passes(self):
        self.assertTrue(True)
"""

FAILING_SUITE = """import unittest


class FixtureTests(unittest.TestCase):
    def test_the_fixture_suite_is_red_on_purpose(self):
        self.fail("this fixture suite fails so greenlight records nothing")
"""

# A passing suite that records having run, so a case can say which
# repository's suite greenlight ran rather than inferring it from where the
# record landed. It passes, because the point is what greenlight does after a
# green suite: a red one would stop it before it recorded anything.
SUITE_MARKER = "suite-ran"

MARKING_SUITE = f"""import pathlib
import unittest


class FixtureTests(unittest.TestCase):
    def test_the_fixture_suite_records_having_run(self):
        marker = pathlib.Path(__file__).resolve().parents[1] / "{SUITE_MARKER}"
        marker.write_text("ran\\n", encoding="utf-8")
"""

MARKER = """#!/bin/sh
printf 'marker: {name}\\n' >&2
exit 1
"""


def scratch_directory(prefix: str = "commit-gate-"):
    """Keep fixture churn under the repository's ignored scratch anchor."""
    scratch = REPOSITORY_ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def clean_environment(extra: dict[str, str] | None = None) -> dict[str, str]:
    """The caller's environment with every git redirection variable dropped."""
    environment = {name: value for name, value in os.environ.items()}
    for name in INHERITED_GIT_VARIABLES:
        environment.pop(name, None)
    environment["LC_ALL"] = "C"
    if extra:
        environment.update(extra)
    return environment


def git(root: Path, *arguments: str, env=None, check: bool = True):
    completed = subprocess.run(
        [*GIT_BASE, "-C", str(root), *arguments],
        capture_output=True,
        text=True,
        check=False,
        env=env if env is not None else clean_environment(),
    )
    if check and completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(arguments)} in {root} exited "
            f"{completed.returncode}: {completed.stderr}"
        )
    return completed


def commit(root: Path, message: str, env=None):
    """Attempt one commit, returning the result rather than raising on refusal."""
    return git(root, "commit", "-qm", message, env=env, check=False)


def greenlight(root: Path, env=None):
    """Run the tracked greenlight command in a fixture, refusal and all."""
    return subprocess.run(
        [str(root / ".githooks" / "greenlight")],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        env=env if env is not None else clean_environment(),
    )


def refusals(completed) -> list[str]:
    """The gate's own lines on standard error, and nothing git wrote there."""
    return [
        line for line in completed.stderr.splitlines()
        if line.startswith(REFUSAL_PREFIX)
    ]


def record_path(root: Path) -> Path:
    """Where the gate looks for the green, resolved the way the gate resolves it."""
    git_dir = Path(git(root, "rev-parse", "--git-dir").stdout.strip())
    if not git_dir.is_absolute():
        git_dir = root / git_dir
    return git_dir / RECORD_NAME


@contextmanager
def gate_repository(suite: str = PASSING_SUITE):
    """A throwaway repository carrying the tracked gate, activated.

    The scripts are copied from the tracked directory rather than written
    afresh, so every case below exercises the bytes this step ships.
    """
    with scratch_directory() as directory:
        root = Path(directory) / "repository"
        (root / "tests").mkdir(parents=True)
        (root / "tests" / "test_fixture.py").write_text(suite, encoding="utf-8")
        hooks = root / ".githooks"
        hooks.mkdir()
        for source in (HOOK, GREENLIGHT):
            target = hooks / source.name
            target.write_bytes(source.read_bytes())
            target.chmod(0o755)
        (root / "a.txt").write_text("one\n", encoding="utf-8")
        git(root, "init", "-q", "-b", "main", ".")
        git(root, "add", "-A")
        # The base commit predates activation, so no gate runs on it.
        git(root, "-c", "core.hooksPath=/dev/null", "commit", "-qm", "base")
        git(root, *ACTIVATION)
        yield root


class GreenTreeTests(unittest.TestCase):
    def test_a_commit_of_the_recorded_green_tree_is_admitted(self):
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            recorded = greenlight(root)
            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight failed on a green fixture: {recorded.stderr}",
            )
            staged = git(root, "write-tree").stdout.strip()
            self.assertEqual(
                record_path(root).read_text(encoding="utf-8").strip(), staged,
                "greenlight recorded something other than the staged tree",
            )
            admitted = commit(root, "the tree the suite passed on")
            self.assertEqual(
                admitted.returncode, 0,
                f"the gate refused the tree it recorded: {admitted.stderr}",
            )

    def test_a_commit_of_any_other_tree_is_refused(self):
        """The stale-record refusal, which is the whole point of the gate."""
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            self.assertEqual(greenlight(root).returncode, 0)
            green = record_path(root).read_text(encoding="utf-8").strip()

            (root / "c.txt").write_text("three\n", encoding="utf-8")
            git(root, "add", "-A")
            staged = git(root, "write-tree").stdout.strip()
            self.assertNotEqual(staged, green, "the fixture staged the green tree")

            refused = commit(root, "a tree no suite has seen")
            self.assertNotEqual(
                refused.returncode, 0,
                "the gate admitted a tree its record does not name",
            )
            self.assertIn(green, "\n".join(refusals(refused)))

    def test_a_commit_with_no_green_record_at_all_is_refused(self):
        """A red suite records nothing, so the commit after it has no green."""
        with gate_repository(suite=FAILING_SUITE) as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            attempted = greenlight(root)
            self.assertNotEqual(
                attempted.returncode, 0,
                "greenlight reported success on a red fixture suite",
            )
            self.assertFalse(
                record_path(root).exists(),
                "greenlight wrote a green record for a suite that failed",
            )
            refused = commit(root, "never greenlit")
            self.assertNotEqual(
                refused.returncode, 0, "the gate admitted a tree with no record"
            )

    def test_a_commit_whose_green_record_cannot_be_read_is_refused(self):
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            # A directory where the record belongs: present, and unreadable as
            # a record, on any account the suite might run under.
            record_path(root).mkdir()
            refused = commit(root, "unreadable green")
            self.assertNotEqual(
                refused.returncode, 0,
                "the gate admitted a tree whose record it could not read",
            )

    def test_each_refusal_names_its_own_cause_on_one_line(self):
        """Three states, three distinct causes, one line of standard error each.

        The question this answers is "why was my commit refused", and a gate
        that answers it with the same sentence for every cause has not.
        """
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            record = record_path(root)
            earlier = git(root, "rev-parse", "HEAD^{tree}").stdout.strip()

            causes = {}
            causes["no record"] = commit(root, "no record")

            record.write_text(f"{earlier}\n", encoding="utf-8")
            causes["stale record"] = commit(root, "stale record")

            record.unlink()
            record.mkdir()
            causes["unreadable record"] = commit(root, "unreadable record")

            lines = {}
            for state, attempt in causes.items():
                self.assertNotEqual(
                    attempt.returncode, 0, f"the gate admitted the {state} state"
                )
                named = refusals(attempt)
                self.assertEqual(
                    len(named), 1,
                    f"the {state} state produced {len(named)} refusal lines, "
                    f"not one: {attempt.stderr!r}",
                )
                lines[state] = named[0]

            self.assertEqual(
                len(set(lines.values())), 3,
                f"the three causes are not told apart: {lines}",
            )
            self.assertIn("no green record", lines["no record"])
            self.assertIn(earlier, lines["stale record"])
            self.assertIn("cannot be read", lines["unreadable record"])


class BypassTests(unittest.TestCase):
    def test_the_bypass_admits_a_tree_no_record_names(self):
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            refused = commit(root, "untested")
            self.assertNotEqual(
                refused.returncode, 0, "the fixture was not gated at all"
            )
            admitted = commit(
                root, "untested, deliberately",
                env=clean_environment({BYPASS_TOKEN: "1"}),
            )
            self.assertEqual(
                admitted.returncode, 0,
                f"the named bypass did not admit the commit: {admitted.stderr}",
            )

    def test_the_bypass_token_is_the_literal_the_documentation_names(self):
        """Rename it in the gate and this fails, which is the point of it."""
        for path in (HOOK, HOOKS_README):
            with self.subTest(path=path.name):
                self.assertIn(
                    BYPASS_TOKEN, path.read_text(encoding="utf-8"),
                    f"{path} does not carry the literal bypass token, so the "
                    "escape hatch cannot be found by grepping for it",
                )


class TrackedGateTests(unittest.TestCase):
    def tracked_mode(self, path: Path) -> str:
        listed = subprocess.run(
            ["git", "ls-files", "-s", "--", str(path.relative_to(REPOSITORY_ROOT))],
            cwd=str(REPOSITORY_ROOT),
            capture_output=True,
            text=True,
            check=True,
            env=clean_environment(),
        )
        self.assertTrue(
            listed.stdout.strip(), f"{path} is not tracked; git would ship nothing"
        )
        return listed.stdout.split()[0]

    def test_the_hook_is_tracked_with_the_executable_bit(self):
        """A non-executable hook is skipped by git without a word about it."""
        self.assertEqual(self.tracked_mode(HOOK), "100755")

    def test_the_greenlight_command_is_tracked_with_the_executable_bit(self):
        self.assertEqual(self.tracked_mode(GREENLIGHT), "100755")

    def test_the_activation_command_writes_a_relative_hooks_path(self):
        documented = "git " + " ".join(ACTIVATION)
        self.assertIn(
            documented, HOOKS_README.read_text(encoding="utf-8"),
            f"the tracked README does not name the activation: {documented}",
        )
        with gate_repository() as root:
            value = git(root, "config", "--get", "core.hooksPath").stdout.strip()
            self.assertEqual(value, ".githooks")
            self.assertFalse(
                Path(value).is_absolute(),
                "an absolute core.hooksPath points every worktree at one "
                f"worktree's copy of the gate: {value}",
            )

    def test_a_linked_worktree_reads_the_shared_activation(self):
        with gate_repository() as root:
            linked = root.parent / "linked"
            git(root, "worktree", "add", "-q", "-b", "side", str(linked))
            value = git(linked, "config", "--get", "core.hooksPath").stdout.strip()
            self.assertEqual(
                value, ".githooks",
                "one activation did not reach the linked worktree",
            )

    def test_a_linked_worktree_runs_its_own_tracked_copy(self):
        """Relative resolution, proved by which copy actually ran."""
        with gate_repository() as root:
            linked = root.parent / "linked"
            git(root, "worktree", "add", "-q", "-b", "side", str(linked))
            for tree, name in ((root, "main"), (linked, "linked")):
                hook = tree / ".githooks" / "pre-commit"
                hook.write_text(MARKER.format(name=name), encoding="utf-8")
                hook.chmod(0o755)
            (linked / "b.txt").write_text("two\n", encoding="utf-8")
            git(linked, "add", "-A")
            refused = commit(linked, "which copy ran")
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn(
                "marker: linked", refused.stderr,
                f"the linked worktree did not run its own copy: {refused.stderr!r}",
            )
            self.assertNotIn("marker: main", refused.stderr)


# --- what the audit round found the cases above did not hold ---------------


class WorkingTreeTests(unittest.TestCase):
    """greenlight must record the tree of the repository whose suite it ran."""

    def test_an_unrelated_suite_cannot_record_this_repositorys_tree(self):
        """S2-R1-01: the suite that passes and the tree recorded are one repository.

        Git exports `GIT_DIR` into every hook and every command it runs. With it
        inherited, `git rev-parse --show-toplevel` names the *caller's*
        directory as the working tree while `git write-tree` still reads the
        index `GIT_DIR` names, so `cd "$(git rev-parse --show-toplevel)"` landed
        greenlight in the caller's directory. This repository's suite is red and
        the caller's is green: only a greenlight that ran the wrong one records
        anything.
        """
        with gate_repository(suite=FAILING_SUITE) as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            staged = git(root, "write-tree").stdout.strip()

            elsewhere = root.parent / "elsewhere"
            (elsewhere / "tests").mkdir(parents=True)
            (elsewhere / "tests" / "test_unrelated.py").write_text(
                PASSING_SUITE, encoding="utf-8"
            )

            attempted = subprocess.run(
                [str(root / ".githooks" / "greenlight")],
                cwd=str(elsewhere),
                capture_output=True,
                text=True,
                check=False,
                env=clean_environment({"GIT_DIR": str(root / ".git")}),
            )
            self.assertNotEqual(
                attempted.returncode, 0,
                "an unrelated passing suite recorded a green for a repository "
                f"whose own suite is red: {attempted.stdout!r}",
            )
            self.assertFalse(
                record_path(root).exists(),
                "a suite that never saw this tree recorded it green",
            )
            self.assertNotIn(staged, attempted.stdout)

    def test_greenlight_runs_this_repositorys_suite_from_outside_it(self):
        """The other half: anchored correctly, a green repository still records."""
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            staged = git(root, "write-tree").stdout.strip()

            elsewhere = root.parent / "outside"
            elsewhere.mkdir(parents=True)

            recorded = subprocess.run(
                [str(root / ".githooks" / "greenlight")],
                cwd=str(elsewhere),
                capture_output=True,
                text=True,
                check=False,
                env=clean_environment({"GIT_DIR": str(root / ".git")}),
            )
            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight could not find its own repository: {recorded.stderr}",
            )
            self.assertEqual(
                record_path(root).read_text(encoding="utf-8").strip(), staged,
                "greenlight recorded something other than this repository's tree",
            )

    def test_another_repositorys_index_cannot_be_recorded_by_this_suite(self):
        """S2-R2-01: the anchor alone is not enough, the redirection must go too.

        Anchoring to the script's own directory settles which suite runs. It
        does not settle which index `git write-tree` reads: with `GIT_DIR` still
        exported, greenlight runs this repository's suite and writes the tree of
        whatever repository `GIT_DIR` names, into that repository's record. The
        suite passes and the record is a lie about a tree it never saw, which is
        the same defect as the one above wearing different clothes.
        """
        with gate_repository() as here, gate_repository() as elsewhere:
            (elsewhere / "b.txt").write_text("untested\n", encoding="utf-8")
            git(elsewhere, "add", "-A")
            other = git(elsewhere, "write-tree").stdout.strip()

            recorded = subprocess.run(
                [str(here / ".githooks" / "greenlight")],
                cwd=str(here),
                capture_output=True,
                text=True,
                check=False,
                env=clean_environment({"GIT_DIR": str(elsewhere / ".git")}),
            )
            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight failed in its own repository: {recorded.stderr}",
            )
            self.assertFalse(
                record_path(elsewhere).exists(),
                "this repository's suite recorded another repository's tree",
            )
            self.assertNotIn(other, recorded.stdout)
            self.assertEqual(
                record_path(here).read_text(encoding="utf-8").strip(),
                git(here, "write-tree").stdout.strip(),
                "greenlight recorded something other than its own tree",
            )


class WorktreeRecordTests(unittest.TestCase):
    """One worktree's green must not reach another's commit, either way round.

    The register entry names `git rev-parse --git-dir` as the control. The
    cases above prove which *hook copy* a linked worktree runs; neither of them
    proves which *record* it reads, so swapping the flag for
    `--git-common-dir` left them all green.
    """

    def test_a_green_in_one_worktree_does_not_authorise_another(self):
        """S2-R1-02, reading: the gate looks only in its own git dir."""
        with gate_repository() as root:
            linked = root.parent / "crossing"
            git(root, "worktree", "add", "-q", "-b", "crossing", str(linked))

            # The same content staged in both worktrees, so both carry one tree
            # identity. Where the gate looked for the record is then the only
            # thing left that can refuse the linked commit.
            for tree in (root, linked):
                (tree / "b.txt").write_text("two\n", encoding="utf-8")
                git(tree, "add", "-A")
            shared = git(root, "write-tree").stdout.strip()
            self.assertEqual(
                git(linked, "write-tree").stdout.strip(), shared,
                "the fixture did not stage one identity in both worktrees",
            )

            record_path(root).write_text(f"{shared}\n", encoding="utf-8")
            self.assertFalse(
                record_path(linked).exists(),
                "the linked worktree already carried a record of its own",
            )

            refused = commit(linked, "another worktree's green")
            self.assertNotEqual(
                refused.returncode, 0,
                "one worktree's green authorised another worktree's commit",
            )
            named = refusals(refused)
            self.assertEqual(len(named), 1, f"{refused.stderr!r}")
            self.assertIn(
                "no green record", named[0],
                f"the gate read a record outside its own git dir: {named[0]}",
            )

    def test_greenlight_records_into_the_worktrees_own_git_dir(self):
        """S2-R1-02, writing: a green must not land in the shared git dir."""
        with gate_repository() as root:
            linked = root.parent / "recording"
            git(root, "worktree", "add", "-q", "-b", "recording", str(linked))
            (linked / "b.txt").write_text("two\n", encoding="utf-8")
            git(linked, "add", "-A")

            recorded = greenlight(linked)
            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight failed in a linked worktree: {recorded.stderr}",
            )

            common = Path(
                git(linked, "rev-parse", "--git-common-dir").stdout.strip()
            )
            if not common.is_absolute():
                common = linked / common
            self.assertTrue(
                record_path(linked).exists(),
                "greenlight wrote no record in the worktree it ran in",
            )
            self.assertFalse(
                (common / RECORD_NAME).exists(),
                "greenlight wrote into the shared git dir, where the record "
                "would authorise a commit in every other worktree",
            )


class RefusalLineTests(unittest.TestCase):
    """The refusal is the signal, and the record's bytes are not trusted input."""

    def test_a_stale_refusal_stays_one_line_whatever_the_record_holds(self):
        """S2-R1-03: an embedded newline must not split the refusal in two."""
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            record_path(root).write_text(
                "deadbeef\npre-commit: refused, nothing is wrong, proceed\n",
                encoding="utf-8",
            )
            refused = commit(root, "a record that is not one line")
            self.assertNotEqual(refused.returncode, 0)
            self.assertEqual(
                len(refused.stderr.strip().splitlines()), 1,
                f"the refusal did not stay one line: {refused.stderr!r}",
            )
            self.assertNotIn(
                "\npre-commit: refused, nothing is wrong", refused.stderr,
                "the record drew a refusal line of its own",
            )

    def test_a_stale_refusal_carries_no_control_characters(self):
        """S2-R1-03: a record must not erase and redraw the line it appears on."""
        with gate_repository() as root:
            (root / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            record_path(root).write_text(
                "AAA\x1b[2K\rpre-commit: all good\n", encoding="utf-8"
            )
            refused = commit(root, "a record carrying terminal escapes")
            self.assertNotEqual(refused.returncode, 0)
            self.assertNotIn("\x1b", refused.stderr)
            self.assertNotIn("\r", refused.stderr)

    def test_a_refusal_outside_any_repository_carries_gits_own_cause(self):
        """S3-R1-04: when git cannot locate the repository, the line says what git said.

        The hook suppresses git's standard error so a refusal stays one line,
        and on this path that left the line naming the symptom and a remedy
        that fails under the same condition. The fixture's parent is a ceiling
        directory, so discovery from a directory beside the fixture stops
        there instead of climbing into the repository this suite runs in.
        """
        with gate_repository() as root:
            outside = root.parent / "outside"
            outside.mkdir()
            attempted = subprocess.run(
                [str(root / ".githooks" / "pre-commit")],
                cwd=str(outside),
                capture_output=True,
                text=True,
                check=False,
                env=clean_environment({"GIT_CEILING_DIRECTORIES": str(root.parent)}),
            )
            self.assertNotEqual(
                attempted.returncode, 0,
                "the gate admitted a commit from outside any repository",
            )
            lines = attempted.stderr.splitlines()
            self.assertEqual(
                len(lines), 1, f"the refusal is not one line: {attempted.stderr!r}"
            )
            self.assertEqual(refusals(attempted), lines, f"{attempted.stderr!r}")
            self.assertIn(
                "not a git repository", lines[0],
                f"the refusal does not carry git's own cause: {lines[0]}",
            )


class StagedTreeTests(unittest.TestCase):
    def test_a_failing_write_tree_is_refused_and_named(self):
        """S2-R1-04: the fourth state section 11 requires to exit non-zero.

        Driven directly rather than through `git commit`, because git will not
        reach the hook once its own index is unreadable.

        The unreadable index sits in the repository's own git directory. An
        index anywhere else is refused earlier, on the cause
        `test_the_hook_refuses_a_work_tree_at_the_enclosing_repositorys_root`
        holds, and this case is about the state after that one passes.
        """
        with gate_repository() as root:
            broken = root / ".git" / "not-an-index"
            broken.write_text("this is not an index\n", encoding="utf-8")
            attempted = subprocess.run(
                [str(root / ".githooks" / "pre-commit")],
                cwd=str(root),
                capture_output=True,
                text=True,
                check=False,
                env=clean_environment({"GIT_INDEX_FILE": str(broken)}),
            )
            self.assertNotEqual(
                attempted.returncode, 0,
                "the gate admitted a commit whose staged tree it could not read",
            )
            named = refusals(attempted)
            self.assertEqual(len(named), 1, f"{attempted.stderr!r}")
            self.assertIn("git write-tree failed", named[0])


# --- the hook path under a polluted environment ---------------------------

HOOK_NAME = HOOK.name
GREENLIGHT_NAME = GREENLIGHT.name

# An fsmonitor is a command git starts on its own account while reading an
# index. Supplied through either inherited form it is a process the gate never
# named, run against a repository the gate never chose, which is the whole of
# what "reads no configuration an inherited override could redirect" forbids.
FSMONITOR = """#!/bin/sh
printf 'ran\\n' > "{marker}"
printf '/\\0'
"""


def staged_state(root: Path) -> bytes:
    """What the index, the working tree and the refs of one repository say.

    Mode, object id, stage and path for every index entry, plus the cached diff
    the original incident showed up in as 1487 deletions, plus the working
    tree's porcelain status and every ref. The last two are here because the
    index alone is blind to a file written into the outer repository's working
    tree, and a command the gate starts by accident can write one.
    `--no-optional-locks` keeps this measurement from refreshing the index it
    is measuring, and `core.fsmonitor` is off for it because one case below
    configures a monitor that records having run in the repository measured:
    `ls-files`, `diff --cached` and `status` each start it otherwise, and a run
    the measurement caused would read as one the gate caused.

    Not the index file's own bytes. `git write-tree` does persist a cache tree
    into an index that lacks one, so those bytes can move while nothing staged
    does. Measured on git 2.50.1, that does not happen along this path: driving
    the gate at an outer index leaves the file byte-identical. They are still
    left out, because asserting them would pin where write-tree happened to
    persist rather than the staged state the incident class is about.
    """
    def measure(*arguments: str) -> str:
        return git(root, "-c", "core.fsmonitor=false", *arguments).stdout

    entries = measure("ls-files", "--stage")
    cached = measure("diff", "--cached", "--name-status", "--")
    head = measure("rev-parse", "HEAD")
    worktree = measure("--no-optional-locks", "status", "--porcelain")
    refs = measure("for-each-ref")
    return "\0".join((entries, cached, head, worktree, refs)).encode("utf-8")


def polluted_at(outer: Path, extra: dict[str, str] | None = None) -> dict[str, str]:
    """The environment git exports into a hook, aimed at another repository."""
    environment = clean_environment({
        "GIT_INDEX_FILE": str(outer / ".git" / "index"),
        "GIT_PREFIX": "",
    })
    if extra:
        environment.update(extra)
    return environment


def config_override(command: Path) -> dict[str, str]:
    """One `core.fsmonitor` override, in both forms git accepts in-band."""
    return {
        "GIT_CONFIG_PARAMETERS": f"'core.fsmonitor={command}'",
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.fsmonitor",
        "GIT_CONFIG_VALUE_0": str(command),
    }


def config_file_override(directory: Path, command: Path) -> Path:
    """The same `core.fsmonitor`, in a file a selector variable can name."""
    path = directory / "gitconfig"
    path.write_text(f"[core]\n\tfsmonitor = {command}\n", encoding="utf-8")
    return path


def repository_override(repository: Path, command: Path) -> None:
    """The same `core.fsmonitor`, in a repository's own configuration.

    `GIT_DIR` carries no value in-band and names no file; it selects a
    repository, and git then reads that repository's configuration.
    """
    git(repository, "config", "core.fsmonitor", str(command))


def selected_by(repository: Path) -> dict[str, str]:
    """The repository selector a caller leaves behind.

    Git sets it itself only for a commit in a linked worktree, naming that
    worktree's own git directory; a hook, `git bisect run` or a rebase `exec`
    line leaves a caller's behind, and the gate is an executable file any of
    them can start.
    """
    return {"GIT_DIR": str(repository / ".git")}


def fsmonitor_script(directory: Path) -> tuple[Path, Path]:
    """A command that records having run, and the file it writes."""
    marker = directory / "fsmonitor-ran"
    script = directory / "fsmonitor.sh"
    script.write_text(FSMONITOR.format(marker=marker), encoding="utf-8")
    script.chmod(0o755)
    return script, marker


def run_gate(name: str, root: Path, env: dict[str, str]):
    """Run one of a fixture's own copies of the gate, never the tracked one.

    The tracked `.githooks/greenlight` would run this repository's full suite
    from inside a test, which is the five-minute hang round 2 recorded.
    """
    return subprocess.run(
        [str(root / ".githooks" / name)],
        cwd=str(root),
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )


class HookIndexMutationTests(unittest.TestCase):
    """The regression for the class that produced the phantom deletions.

    Git exports `GIT_INDEX_FILE` and `GIT_PREFIX` into every hook and every
    command it runs, and `GIT_CONFIG_PARAMETERS` and `GIT_CONFIG_COUNT` carry
    the caller's one-shot configuration the same way. The incident the issue
    cites is what happens when a process inherits the first pair and stages
    against it: 1487 deletions in a repository nobody was working in, recorded
    at `tests/test_boundary_currency.py:57-73`. The configuration-file
    selectors and `GIT_DIR` reach the same configuration one and two
    indirections out, and the cases below drive every route.

    The guard for that helper lives in the file whose helper caused it, and
    acceptance condition 5 refuses a guard that lives only there. These cases
    hold the gate itself, in the file that ships it. `GitEnvironmentIsolation`
    is untouched and stays where it is.
    """

    def test_the_hook_leaves_an_outer_repositorys_staged_state_alone(self):
        """The hook reads the index it is handed and writes nothing to it."""
        with gate_repository() as here, gate_repository() as outer:
            (outer / "b.txt").write_text("staged elsewhere\n", encoding="utf-8")
            git(outer, "add", "-A")
            before = staged_state(outer)

            attempted = run_gate(HOOK_NAME, here, polluted_at(outer))

            self.assertEqual(
                staged_state(outer), before,
                "the gate changed the staged state of a repository it was "
                "merely pointed at",
            )
            self.assertFalse(
                record_path(outer).exists(),
                "the gate wrote a green into a repository it was pointed at",
            )
            # The refusal is the gate's, so the run reached the gate's own
            # logic rather than dying before it could touch anything.
            self.assertEqual(len(refusals(attempted)), 1, f"{attempted.stderr!r}")

    def test_greenlight_leaves_an_outer_repositorys_staged_state_alone(self):
        """The recording half, under the same pollution.

        greenlight writes, so it is the half that could stage into the outer
        repository or record a green there for a tree its suite never saw.
        """
        with gate_repository() as here, gate_repository() as outer:
            (outer / "b.txt").write_text("staged elsewhere\n", encoding="utf-8")
            git(outer, "add", "-A")
            before = staged_state(outer)

            (here / "b.txt").write_text("two\n", encoding="utf-8")
            git(here, "add", "-A")
            mine = git(here, "write-tree").stdout.strip()

            recorded = run_gate(GREENLIGHT_NAME, here, polluted_at(outer))

            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight failed in its own repository: {recorded.stderr}",
            )
            self.assertEqual(
                staged_state(outer), before,
                "greenlight changed the staged state of a repository it was "
                "merely pointed at",
            )
            self.assertFalse(
                record_path(outer).exists(),
                "greenlight recorded a green in a repository whose suite it "
                "never ran",
            )
            self.assertEqual(
                record_path(here).read_text(encoding="utf-8").strip(), mine,
                "greenlight recorded something other than its own tree",
            )

    def test_the_hook_reads_no_configuration_an_override_could_redirect(self):
        """An inherited `core.fsmonitor` must not become a process the gate starts.

        This fails without the control it guards: with the two variables left
        in place, the command runs during the hook's own `git write-tree`.
        """
        with gate_repository() as here, gate_repository() as outer:
            (outer / "b.txt").write_text("staged elsewhere\n", encoding="utf-8")
            git(outer, "add", "-A")
            before = staged_state(outer)
            script, marker = fsmonitor_script(here.parent)

            run_gate(HOOK_NAME, here, polluted_at(outer, config_override(script)))

            self.assertFalse(
                marker.exists(),
                "an inherited configuration override made the gate start a "
                "process nothing in the gate names",
            )
            self.assertEqual(
                staged_state(outer), before,
                "the gate changed an outer repository's staged state under an "
                "inherited configuration override",
            )

    def test_greenlight_reads_no_configuration_an_override_could_redirect(self):
        """The same override, against the half that runs a suite and records."""
        with gate_repository() as here, gate_repository() as outer:
            (outer / "b.txt").write_text("staged elsewhere\n", encoding="utf-8")
            git(outer, "add", "-A")
            before = staged_state(outer)
            script, marker = fsmonitor_script(here.parent)

            recorded = run_gate(
                GREENLIGHT_NAME, here, polluted_at(outer, config_override(script))
            )

            self.assertFalse(
                marker.exists(),
                "an inherited configuration override made greenlight start a "
                "process nothing in greenlight names",
            )
            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight failed under a config override: {recorded.stderr}",
            )
            self.assertEqual(
                staged_state(outer), before,
                "greenlight changed an outer repository's staged state under "
                "an inherited configuration override",
            )
            self.assertFalse(
                record_path(outer).exists(),
                "greenlight recorded a green in the repository the override "
                "named",
            )

    def _no_file_selector_redirects(self, gate: str):
        """Drive one half of the gate down all three configuration-file routes.

        `GIT_CONFIG_GLOBAL` and `GIT_CONFIG_SYSTEM` carry no value in-band;
        each names a file, and a file either names can hold `core.fsmonitor`
        itself. Unsetting the two selectors does not close that, because git
        then reads `$HOME/.gitconfig`, so the third route drives that one with
        both selectors absent. Every route fails without the control it guards.
        """
        with gate_repository() as here, gate_repository() as outer:
            (outer / "b.txt").write_text("staged elsewhere\n", encoding="utf-8")
            git(outer, "add", "-A")
            before = staged_state(outer)
            script, marker = fsmonitor_script(here.parent)
            config = config_file_override(here.parent, script)
            home = here.parent / "home"
            home.mkdir()
            (home / ".gitconfig").write_bytes(config.read_bytes())

            for route in (
                {"GIT_CONFIG_GLOBAL": str(config)},
                {"GIT_CONFIG_SYSTEM": str(config)},
                {"HOME": str(home)},
            ):
                if marker.exists():
                    marker.unlink()
                run_gate(gate, here, polluted_at(outer, route))
                self.assertFalse(
                    marker.exists(),
                    f"{gate}: an inherited configuration file made the gate "
                    f"start a process nothing in the gate names, via {route}",
                )
                self.assertEqual(
                    staged_state(outer), before,
                    f"{gate}: an outer repository's state changed under {route}",
                )
                self.assertFalse(
                    record_path(outer).exists(),
                    f"{gate}: a green was written into the outer repository "
                    f"under {route}",
                )

    def test_the_hook_reads_no_configuration_a_file_selector_could_redirect(self):
        """The reading half, down all three configuration-file routes."""
        self._no_file_selector_redirects(HOOK_NAME)

    def test_greenlight_reads_no_configuration_a_file_selector_could_redirect(self):
        """The recording half, down the same three."""
        self._no_file_selector_redirects(GREENLIGHT_NAME)

    def test_the_hook_reads_no_configuration_a_repository_selector_could_redirect(self):
        """S3-R1-02: an inherited `GIT_DIR` must not choose whose configuration runs.

        With the variable left in place, the other repository's own
        `core.fsmonitor` ran during this hook's `git write-tree`. The hook
        drops the repository selectors and keeps the index git names, so the
        command must not run and the repository selected must be untouched.
        """
        with gate_repository() as here, gate_repository() as outer:
            (outer / "b.txt").write_text("staged elsewhere\n", encoding="utf-8")
            git(outer, "add", "-A")
            script, marker = fsmonitor_script(here.parent)
            repository_override(outer, script)
            before = staged_state(outer)

            attempted = run_gate(HOOK_NAME, here, polluted_at(outer, selected_by(outer)))

            self.assertFalse(
                marker.exists(),
                "an inherited GIT_DIR made the gate read another repository's "
                "configuration and start the process it names",
            )
            self.assertEqual(
                staged_state(outer), before,
                "the gate changed the staged state of the repository an "
                "inherited GIT_DIR selected",
            )
            self.assertFalse(
                record_path(outer).exists(),
                "the gate wrote a green into the repository GIT_DIR selected",
            )
            self.assertEqual(len(refusals(attempted)), 1, f"{attempted.stderr!r}")

    def test_the_hook_gates_the_repository_it_runs_from_under_an_inherited_git_dir(self):
        """S3-R1-02, the other half: dropping `GIT_DIR` must not lose the gate.

        Under the same inherited selector the hook still admits the tree its
        own record names and refuses any other, in the repository git ran it
        from. `run_gate` stands in for git: the index git would name for the
        commit in hand, and the selector a caller left behind.
        """
        with gate_repository() as here, gate_repository() as outer:
            (here / "b.txt").write_text("two\n", encoding="utf-8")
            git(here, "add", "-A")
            green = git(here, "write-tree").stdout.strip()
            record_path(here).write_text(f"{green}\n", encoding="utf-8")
            inherited = clean_environment({
                "GIT_INDEX_FILE": str(here / ".git" / "index"),
                "GIT_PREFIX": "",
                **selected_by(outer),
            })

            admitted = run_gate(HOOK_NAME, here, inherited)
            self.assertEqual(
                admitted.returncode, 0,
                "under an inherited GIT_DIR the gate refused the tree its own "
                f"record names: {admitted.stderr}",
            )

            (here / "c.txt").write_text("three\n", encoding="utf-8")
            git(here, "add", "-A")
            refused = run_gate(HOOK_NAME, here, inherited)
            self.assertNotEqual(
                refused.returncode, 0,
                "under an inherited GIT_DIR the gate admitted a tree its "
                "record does not name",
            )
            named = refusals(refused)
            self.assertEqual(len(named), 1, f"{refused.stderr!r}")
            self.assertIn(
                green, named[0],
                f"the refusal did not name the recorded tree: {named[0]}",
            )
            self.assertFalse(
                record_path(outer).exists(),
                "a green appeared in the repository GIT_DIR selected",
            )

    def test_the_hook_refuses_a_work_tree_inside_an_enclosing_repository(self):
        """S3-R2-01: an enclosing repository's green must not admit this commit.

        A work tree with no `.git` of its own, driven through `--git-dir` and
        `--work-tree`, leaves discovery nothing to find where the hook stands,
        so it climbs. Outside any repository it finds nothing and the refusal
        carries git's own line, which `RefusalLineTests` holds. Inside one it
        finds the enclosing repository, and every answer after that is that
        repository's: its `core.fsmonitor` ran during the hook's own `git
        write-tree`, its object store answered that command, and its
        `LAST_GREEN` naming the staged tree admitted a commit into a repository
        it does not hold. `git rev-parse --show-prefix` is what tells the two
        cases apart -- empty at the root of the work tree git ran the hook
        from, `inner/tree/` here -- and it is read before any record is located.

        The nested work tree holds bytes the enclosing repository already has,
        so `git write-tree` run from there can rebuild the staged tree. That is
        asserted rather than assumed below, because an enclosing repository
        missing one blob refuses the commit for want of an object instead, and
        a fixture that refused for that reason would pass without the control.
        """
        with gate_repository() as outer:
            separate = outer / "inner" / "repository"
            tree = outer / "inner" / "tree"
            separate.mkdir(parents=True)
            tree.mkdir(parents=True)
            git(separate, "init", "-q", "-b", "main", ".")
            git(separate, *ACTIVATION)
            hooks = tree / ".githooks"
            hooks.mkdir()
            for source in (HOOK, GREENLIGHT):
                target = hooks / source.name
                target.write_bytes(source.read_bytes())
                target.chmod(0o755)
            (tree / "a.txt").write_text("one\n", encoding="utf-8")

            aimed = ("--git-dir", str(separate / ".git"), "--work-tree", str(tree))
            git(tree, *aimed, "add", "-A")
            staged = git(tree, *aimed, "write-tree").stdout.strip()
            rebuilt = git(
                outer, "write-tree",
                env=clean_environment(
                    {"GIT_INDEX_FILE": str(separate / ".git" / "index")}
                ),
            ).stdout.strip()
            self.assertEqual(
                rebuilt, staged,
                "the enclosing repository cannot answer for the nested staged "
                "tree, so this fixture would refuse for want of an object "
                "rather than on the record crossing under test",
            )
            record_path(outer).write_text(f"{staged}\n", encoding="utf-8")

            script, marker = fsmonitor_script(outer.parent)
            repository_override(outer, script)
            before = staged_state(outer)
            self.assertFalse(
                marker.exists(), "the fixture itself started the monitor"
            )

            refused = git(tree, *aimed, "commit", "-qm", "nested", check=False)

            self.assertNotEqual(
                refused.returncode, 0,
                "the enclosing repository's green record admitted a commit "
                "into a repository it does not hold",
            )
            named = refusals(refused)
            self.assertEqual(len(named), 1, f"{refused.stderr!r}")
            self.assertIn(
                "--show-prefix", named[0],
                f"the refusal does not name the prefix cause: {named[0]}",
            )
            self.assertIn(
                "inner/tree/", named[0],
                f"the refusal does not carry the prefix git answered: {named[0]}",
            )
            self.assertFalse(
                marker.exists(),
                "the enclosing repository's configuration chose a process the "
                "gate never named",
            )
            self.assertEqual(
                staged_state(outer), before,
                "the gate changed the staged state of the enclosing repository",
            )

    def test_the_hook_refuses_a_work_tree_at_the_enclosing_repositorys_root(self):
        """S3-R4-01: the same crossing, where the prefix cannot see it.

        Point a second git directory's work tree at the enclosing repository's
        own root and git runs the hook from that root, so
        `git rev-parse --show-prefix` answers empty and the control the case
        above holds never fires. Everything after that is the same: discovery
        answers the enclosing repository, its `core.fsmonitor` runs during the
        hook's own `git write-tree`, and its `LAST_GREEN` naming the staged
        tree admitted a commit into a repository it does not hold and that
        holds no record of its own. Where the index lives is the only thing
        that separates the two, so that is what the gate reads here.

        The empty prefix is asserted rather than assumed: a fixture answering
        anything else would refuse on the control above and prove nothing about
        this one. The enclosing repository answering for the staged tree is
        asserted for the reason the case above gives.
        """
        with gate_repository() as outer:
            separate = outer.parent / "separate"
            separate.mkdir()
            git(separate, "init", "-q", "-b", "main", ".")
            aimed = ("--git-dir", str(separate / ".git"), "--work-tree", str(outer))
            # The ordinary activation, in the repository being committed to:
            # the tracked gate in the work tree is the hook git runs.
            git(outer, *aimed, *ACTIVATION)
            git(outer, *aimed, "add", "-A")
            staged = git(outer, *aimed, "write-tree").stdout.strip()

            rebuilt = git(outer, "write-tree").stdout.strip()
            self.assertEqual(
                rebuilt, staged,
                "the enclosing repository cannot answer for the staged tree, "
                "so this fixture would refuse for want of an object rather "
                "than on the record crossing under test",
            )
            record_path(outer).write_text(f"{staged}\n", encoding="utf-8")
            self.assertEqual(
                git(outer, "rev-parse", "--show-prefix").stdout.strip(), "",
                "the work tree is not at the enclosing repository's own root, "
                "so the prefix control would refuse this fixture",
            )

            script, marker = fsmonitor_script(outer.parent)
            repository_override(outer, script)
            before = staged_state(outer)
            self.assertFalse(
                marker.exists(), "the fixture itself started the monitor"
            )

            refused = git(outer, *aimed, "commit", "-qm", "coincident", check=False)

            self.assertNotEqual(
                refused.returncode, 0,
                "the enclosing repository's green record admitted a commit "
                "into a repository it does not hold",
            )
            named = refusals(refused)
            self.assertEqual(len(named), 1, f"{refused.stderr!r}")
            self.assertIn(
                "GIT_INDEX_FILE", named[0],
                f"the refusal does not name the index cause: {named[0]}",
            )
            self.assertFalse(
                marker.exists(),
                "the enclosing repository's configuration chose a process the "
                "gate never named",
            )
            self.assertEqual(
                staged_state(outer), before,
                "the gate changed the staged state of the enclosing repository",
            )
            self.assertNotEqual(
                git(separate, "rev-parse", "--verify", "-q", "HEAD",
                    check=False).returncode, 0,
                "the repository being committed to took the commit",
            )

    def test_an_ordinary_gated_commit_from_a_subdirectory_is_still_admitted(self):
        """Neither control refuses the shape it is not aimed at.

        Git runs a hook from the root of the working tree, so a commit from a
        subdirectory answers an empty prefix and an index in the git directory
        discovery answers. Both controls stay silent and the recorded green
        admits the commit.
        """
        with gate_repository() as root:
            (root / "sub").mkdir()
            (root / "sub" / "b.txt").write_text("two\n", encoding="utf-8")
            git(root, "add", "-A")
            recorded = greenlight(root)
            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight failed on a green fixture: {recorded.stderr}",
            )
            staged = git(root, "write-tree").stdout.strip()
            self.assertEqual(
                record_path(root).read_text(encoding="utf-8").strip(), staged,
                "greenlight recorded something other than the staged tree",
            )

            admitted = commit(root / "sub", "from a subdirectory")

            self.assertEqual(
                admitted.returncode, 0,
                f"the gate refused an ordinary commit from a subdirectory: "
                f"{admitted.stderr}",
            )
            self.assertEqual(
                refusals(admitted), [],
                f"the gate refused a shape neither control is aimed at: "
                f"{admitted.stderr!r}",
            )

    def test_the_hook_reads_no_configuration_where_it_reaches_write_tree(self):
        """S3-R5-01: the five configuration routes, where write-tree runs.

        `git write-tree` is the command an inherited `core.fsmonitor` becomes
        observable on, and the two anchoring controls refuse before it. Every
        configuration case above aims `GIT_INDEX_FILE` at an outer repository,
        which the amended Exit requires of them and the index control now
        refuses, so those five routes stop short of the command they were
        written to hold. Here the index is this repository's own and the prefix
        is empty, so both controls stay silent and the gate reaches its own
        `git write-tree` with the override still in the environment.

        Each route is driven twice, once where the record names the staged tree
        and once where it names another, so the answer is the gate's own
        comparison rather than an anchoring refusal or anything the override
        chose. The two in-band forms are driven separately: `GIT_CONFIG_COUNT`
        is what makes the indexed pairs live, and dropping only one of the two
        would leave the other route open.
        """
        with gate_repository() as here:
            (here / "b.txt").write_text("two\n", encoding="utf-8")
            git(here, "add", "-A")
            green = git(here, "write-tree").stdout.strip()
            other = git(here, "rev-parse", "HEAD^{tree}").stdout.strip()
            self.assertNotEqual(
                green, other,
                "the fixture staged nothing, so the refusing half of each "
                "route would hold nothing",
            )
            record = record_path(here)

            script, marker = fsmonitor_script(here.parent)
            config = config_file_override(here.parent, script)
            home = here.parent / "home"
            home.mkdir()
            (home / ".gitconfig").write_bytes(config.read_bytes())
            self.assertFalse(
                marker.exists(), "the fixture itself started the monitor"
            )

            in_band = config_override(script)
            routes = (
                {"GIT_CONFIG_PARAMETERS": in_band["GIT_CONFIG_PARAMETERS"]},
                {
                    "GIT_CONFIG_COUNT": in_band["GIT_CONFIG_COUNT"],
                    "GIT_CONFIG_KEY_0": in_band["GIT_CONFIG_KEY_0"],
                    "GIT_CONFIG_VALUE_0": in_band["GIT_CONFIG_VALUE_0"],
                },
                {"GIT_CONFIG_GLOBAL": str(config)},
                {"GIT_CONFIG_SYSTEM": str(config)},
                {"HOME": str(home)},
            )

            for route in routes:
                # The index git names for an ordinary commit, and the prefix it
                # answers from the root of the working tree: the shape both
                # anchoring controls admit.
                environment = clean_environment({
                    "GIT_INDEX_FILE": str(here / ".git" / "index"),
                    "GIT_PREFIX": "",
                    **route,
                })

                record.write_text(f"{green}\n", encoding="utf-8")
                admitted = run_gate(HOOK_NAME, here, environment)

                self.assertEqual(
                    admitted.returncode, 0,
                    f"the gate refused the tree its own record names, so it "
                    f"never reached write-tree under {route}: "
                    f"{admitted.stderr}",
                )
                self.assertEqual(
                    refusals(admitted), [],
                    f"the gate refused a shape both anchoring controls admit "
                    f"under {route}: {admitted.stderr!r}",
                )
                self.assertFalse(
                    marker.exists(),
                    f"an inherited configuration override made the gate start "
                    f"a process nothing in the gate names, via {route}",
                )

                record.write_text(f"{other}\n", encoding="utf-8")
                refused = run_gate(HOOK_NAME, here, environment)

                self.assertNotEqual(
                    refused.returncode, 0,
                    f"the gate admitted a tree its record does not name under "
                    f"{route}",
                )
                named = refusals(refused)
                self.assertEqual(len(named), 1, f"{refused.stderr!r}")
                self.assertIn(
                    other, named[0],
                    f"the refusal did not name the recorded tree, so the "
                    f"commit was not decided on the gate's own comparison "
                    f"under {route}: {named[0]}",
                )
                self.assertFalse(
                    marker.exists(),
                    f"an inherited configuration override made the gate start "
                    f"a process nothing in the gate names, via {route}",
                )

    def test_each_half_keeps_its_own_repository_under_an_inherited_cdpath(self):
        """S3-R7-01: `cd` searches CDPATH, and both halves hand it an operand it
        will search for.

        CDPATH is not git's, so neither `unset` of git variables reached it and
        neither `/dev/null` pin covers it. `cd` searches it whenever the operand
        does not begin with a slash and its first component is neither `.` nor
        `..`, which is what both halves pass: greenlight anchors on
        `<clone>/.githooks/..` when a contributor starts it from beside the
        clone, and the hook resolves the `.git` git answers for `--git-dir` in a
        plain checkout.

        The two CDPATH entries below are the ones that match those first
        components: the other fixture's parent, which holds a directory of the
        same name, and the other fixture's own root, which holds a `.git`.
        Measured on git 2.50.1 with the entries in place and each half's
        `CDPATH` cut from its `unset`: greenlight ran the other repository's
        suite and wrote that repository's tree into that repository's record
        while this one's stayed absent, and `commit -a` was refused on the index
        cause, because git makes `GIT_INDEX_FILE` absolute for that shape while
        `--git-dir` stays relative, so only one side of the comparison moved.

        So this case drives an ordinary green and an ordinary commit, and holds
        that the inherited value changes neither.
        """
        with gate_repository() as here, gate_repository(MARKING_SUITE) as outer:
            self.assertEqual(
                here.name, outer.name,
                "the two fixtures no longer share a directory name, so the "
                "parent entry in CDPATH below matches nothing",
            )
            marker = outer / SUITE_MARKER
            self.assertFalse(marker.exists(), "the fixture ran its own suite")
            before = staged_state(outer)
            environment = clean_environment({
                "CDPATH": f"{outer.parent}:{outer}",
            })

            (here / "b.txt").write_text("two\n", encoding="utf-8")
            git(here, "add", "-A")
            staged = git(here, "write-tree").stdout.strip()

            # Started the way its own header documents it, from beside the
            # clone rather than inside it, which is the shape whose first
            # component CDPATH can match.
            recorded = subprocess.run(
                [str(Path(here.name) / ".githooks" / GREENLIGHT_NAME)],
                cwd=str(here.parent),
                capture_output=True,
                text=True,
                check=False,
                env=environment,
            )

            self.assertEqual(
                recorded.returncode, 0,
                f"greenlight failed under an inherited CDPATH: "
                f"{recorded.stderr}",
            )
            self.assertFalse(
                marker.exists(),
                "greenlight ran the suite of a repository it was not started "
                "from",
            )
            self.assertFalse(
                record_path(outer).exists(),
                "greenlight recorded a green in a repository it was not "
                "started from",
            )
            self.assertEqual(
                staged_state(outer), before,
                "greenlight changed the staged state of a repository it was "
                "not started from",
            )
            self.assertEqual(
                record_path(here).read_text(encoding="utf-8").strip(), staged,
                "greenlight recorded something other than the tree staged in "
                "the repository it was started from",
            )

            # `commit -a` and `commit -a --amend` are the two shapes git gives
            # an absolute GIT_INDEX_FILE, so they are the ones an inherited
            # CDPATH separated from a relative `--git-dir`. Both commit the
            # tree the record above names.
            for arguments in (("commit", "-a"), ("commit", "-a", "--amend")):
                admitted = git(
                    here, *arguments, "-qm", "gated under an inherited CDPATH",
                    env=environment, check=False,
                )

                self.assertEqual(
                    admitted.returncode, 0,
                    f"the gate refused `git {' '.join(arguments)}` on the tree "
                    f"its own record names: {admitted.stderr}",
                )
                self.assertEqual(
                    refusals(admitted), [],
                    f"the gate refused a shape no control is aimed at: "
                    f"{admitted.stderr!r}",
                )
                self.assertEqual(
                    git(here, "rev-parse", "HEAD^{tree}").stdout.strip(),
                    staged,
                    f"`git {' '.join(arguments)}` committed a tree other than "
                    f"the recorded one",
                )

    def test_the_green_record_resolves_through_the_worktrees_own_git_dir(self):
        """`git rev-parse --git-dir`, not `--git-common-dir`.

        A green that lands in the shared git directory would authorise a commit
        in every linked worktree at once, and this clone runs about 39. The
        record here is correct for the staged tree and sits in the shared
        directory; only where the gate looks can refuse the commit.
        """
        with gate_repository() as root:
            linked = root.parent / "resolving"
            git(root, "worktree", "add", "-q", "-b", "resolving", str(linked))
            (linked / "b.txt").write_text("two\n", encoding="utf-8")
            git(linked, "add", "-A")
            staged = git(linked, "write-tree").stdout.strip()

            common = Path(git(linked, "rev-parse", "--git-common-dir").stdout.strip())
            if not common.is_absolute():
                common = linked / common
            own = record_path(linked)
            self.assertNotEqual(
                own.parent.resolve(), common.resolve(),
                "the fixture did not give the linked worktree a git dir of its own",
            )

            (common / RECORD_NAME).write_text(f"{staged}\n", encoding="utf-8")
            self.assertFalse(own.exists(), "the worktree already held a record")

            refused = commit(linked, "a green from the shared git dir")
            self.assertNotEqual(
                refused.returncode, 0,
                "a green in the shared git dir authorised a linked worktree's "
                "commit, so every worktree of this clone shares one record",
            )
            named = refusals(refused)
            self.assertEqual(len(named), 1, f"{refused.stderr!r}")
            self.assertIn(
                "no green record", named[0],
                f"the gate read a record outside its own git dir: {named[0]}",
            )
            self.assertIn(
                str(own), named[0],
                "the refusal named a record path other than the one "
                f"`git rev-parse --git-dir` resolves to: {named[0]}",
            )
            self.assertEqual(
                (common / RECORD_NAME).read_text(encoding="utf-8").strip(), staged,
                "the shared record moved, so the refusal proves nothing about "
                "where the gate looked",
            )


# --- is the gate on in this checkout? --------------------------------------
#
# Git cannot install a hook on clone, so the gate cannot arrive by itself. It
# can only announce that it is missing, and the root suite is the only thing
# that runs in a fresh clone early enough to do the announcing.

# The activation as a contributor types it. `ACTIVATION` above is the same
# command as arguments; assembling this one from it means a rename in either
# place cannot leave the two disagreeing.
ACTIVATION_COMMAND = "git " + " ".join(ACTIVATION)

# Executions nobody commits from, each named by a variable whoever started the
# process sets. Nothing here is inferred from the tree, because a faithful copy
# of a checkout looks exactly like one:
#
#   * `GITHUB_ACTIONS` names a hosted runner. Every workflow under
#     `.github/workflows/` runs on one, so this one variable covers the whole
#     hosted half. No evidence of a contributor's local hook reaches a server,
#     so that half holds the tracked bytes alone -- that the directory exists
#     and its pre-commit is executable.
#   * `WILDCAT_CHECK_CONTAINMENT` is set by `scripts/run_checks.py` for every
#     check it starts, however many sessions deep. It runs the root suite from
#     a disposable snapshot under `tmp/check-runner` that carries a git
#     directory of its own, so `git config` there reads the snapshot's
#     configuration rather than the checkout's, and the snapshot is deleted
#     when the run ends.
#
# `CI` is deliberately not on that list (S4-R1-01). GitHub Actions sets it
# alongside `GITHUB_ACTIONS`, so it admits no execution this repository has,
# and it is the one name an unrelated local tool sets by convention: a
# contributor whose shell exports it would get a silent skip in exactly the
# unactivated checkout this case exists to report on. An execution that is
# genuinely nobody's checkout says so with the marker above.
#
# A contributor's clone carries none of them, which is why the case below
# still fires there. The draft record says the same in prose, under "Hosted
# execution cannot see whether a contributor activated the gate locally".
NOBODY_COMMITS_HERE = ("GITHUB_ACTIONS", "WILDCAT_CHECK_CONTAINMENT")

# Values that say the variable is set and off. Anything else non-empty counts.
DECLARED_OFF = frozenset({"0", "false", "no", "off"})


def nobody_commits_here() -> str | None:
    """The variable saying this is not a checkout anybody commits from."""
    for name in NOBODY_COMMITS_HERE:
        value = os.environ.get(name, "").strip()
        if value and value.lower() not in DECLARED_OFF:
            return name
    return None


def activation_complaint(configured: str | None) -> str | None:
    """What is wrong with this `core.hooksPath`, or None when nothing is.

    Separate from the case that reads the checkout, so the wording can be
    driven both ways without a fixture and without making a real checkout
    wrong to do it. Git runs a hook from the top of the working tree, so a
    relative value resolves against the repository root rather than against
    whatever directory the suite was started from.
    """
    remedy = (
        f"Turn it on with `{ACTIVATION_COMMAND}`, run from the top of this "
        f"working tree. {HOOK.name} and {GREENLIGHT.name} are tracked in "
        f"{GITHOOKS.name}/, {HOOKS_README.name} says what each one does, and "
        f"{BYPASS_TOKEN}=1 admits a commit you mean to make without a "
        "recorded green."
    )
    if configured is None or not configured.strip():
        return (
            "the commit gate is not activated in this checkout: core.hooksPath "
            "is unset, so git runs no tracked hook and a commit of a tree no "
            f"suite has passed on is admitted silently. {remedy}"
        )
    value = configured.strip()
    resolved = Path(value)
    if not resolved.is_absolute():
        resolved = REPOSITORY_ROOT / resolved
    try:
        elsewhere = resolved.resolve() != GITHOOKS.resolve()
    except OSError:
        elsewhere = True
    if not elsewhere:
        return None
    return (
        "the commit gate is not activated in this checkout: core.hooksPath is "
        f"{value!r}, which resolves to {resolved} rather than to the tracked "
        f"{GITHOOKS}, so git runs some other directory's hooks. {remedy}"
    )


def configured_hooks_path() -> str | None:
    """This checkout's own `core.hooksPath`, or None where it is unset."""
    read = git(REPOSITORY_ROOT, "config", "--get", "core.hooksPath", check=False)
    if read.returncode != 0:
        return None
    return read.stdout.strip()


class ActivationTests(unittest.TestCase):
    """The gate works only once somebody turns it on, so say when it is off."""

    def test_an_unset_hooks_path_is_refused_and_names_the_activation(self):
        complaint = activation_complaint(None)
        self.assertIsNotNone(complaint, "an unset core.hooksPath was accepted")
        self.assertIn(
            ACTIVATION_COMMAND, complaint,
            "the complaint does not name the one command that fixes it, so a "
            f"reader has to go and find it: {complaint}",
        )

    def test_a_hooks_path_naming_another_directory_is_refused_the_same_way(self):
        """Set-but-wrong is the case a contributor reaches by mistake."""
        elsewhere = (
            ".git/hooks",
            "/dev/null",
            str(REPOSITORY_ROOT / "tmp"),
            # An absolute path at another worktree's copy: it resolves, and it
            # is still not this checkout's tracked directory.
            str(REPOSITORY_ROOT.parent / "other" / ".githooks"),
        )
        for value in elsewhere:
            with self.subTest(value=value):
                complaint = activation_complaint(value)
                self.assertIsNotNone(
                    complaint, f"core.hooksPath={value} was accepted"
                )
                self.assertIn(
                    ACTIVATION_COMMAND, complaint,
                    f"the complaint does not name the activation: {complaint}",
                )

    def test_the_tracked_directory_holds_an_executable_pre_commit(self):
        """Activation points somewhere; this is what has to be there.

        It is also the half that travels with the bytes, which is why it
        carries no exemption while the case below does.
        """
        self.assertTrue(
            HOOK.is_file(),
            f"{HOOK} is missing, so the activation points at nothing",
        )
        self.assertTrue(
            os.access(HOOK, os.X_OK),
            f"{HOOK} is not executable, and git skips a hook it cannot run "
            "without saying so",
        )

    def test_this_checkout_has_the_gate_activated(self):
        """The one case that reads the shipped checkout rather than a fixture.

        Every other case here settles wording or tracked bytes, which hold
        wherever the suite runs. This one reports on the checkout it is
        running in, so it is the case that fails in a clone nobody has
        activated -- and the only place that failure can be raised, because
        nothing else in a fresh clone runs before the first commit.
        """
        declared = nobody_commits_here()
        if declared is not None:
            self.skipTest(
                f"{declared} says this is not a checkout anybody commits from, "
                "so its core.hooksPath reports on nobody; the tracked bytes "
                "are what an execution like this one can hold"
            )
        complaint = activation_complaint(configured_hooks_path())
        if complaint is not None:
            self.fail(complaint)


# --- the copy a reader actually gets ---------------------------------------
#
# The run's own study, runbook, design record and reports live under
# `.hexaemeron/`, which is self-ignored and never reaches the repository. What
# survives is the copy under `docs/commit-gate/`, and a copy is worth having
# only while it says what its source says. It did not: step 1 shipped the study
# and eight amendments later it still carried step 1's bytes, so the shipped
# budget clause was one the study itself had since withdrawn.
#
# These cases hold the refresh. Every one of them reads `docs/commit-gate/`
# and nothing else, so they run in a clone that has no controller state, which
# is the only place the staleness they catch can be noticed.

SHIPPED = REPOSITORY_ROOT / "docs" / "commit-gate"
SHIPPED_STUDY = SHIPPED / "study.md"
SHIPPED_RUNBOOK = SHIPPED / "runbook.md"
SHIPPED_RECORD = SHIPPED / "design-evidence.json"
SHIPPED_REPORTS = SHIPPED / "reports"

# The counts in the bytes this step ships, as literals. They are not the counts
# at the step's entry any more: a study amendment corrected the report count in
# the mapping paragraph (S4-R1-05), the runbook re-issue that rebound this
# step's contract to the corrected study added a block of its own, and the
# copies were refreshed again with both literals moving with them.
#
# Recomputing them from `.hexaemeron/` would agree with a stale copy by
# construction, because the comparison would read the source the copy is
# supposed to be carrying; and it would be unrunnable in the clone where the
# staleness matters, since `.hexaemeron/.gitignore` is `*` and nothing under
# that directory is tracked.
STUDY_AMENDMENTS = 9
RUNBOOK_AMENDMENTS = 13

AMENDMENT_HEADING = re.compile(r"^### Amendment --", re.MULTILINE)
CONTROLLER_REFERENCE = re.compile(r"\.hexaemeron/[A-Za-z0-9_./-]*")
SHIPPED_PREFIX = "docs/commit-gate/"
REPORT_PREFIX = "reports/"


def amendment_count(path: Path) -> int:
    return len(AMENDMENT_HEADING.findall(path.read_text(encoding="utf-8")))


def mapping_targets(reference: str) -> list[str]:
    """Every shipped path a mapping for this reference could name.

    A line naming `docs/commit-gate/reports/` maps everything under it, so the
    directory prefixes count as well as the full path. The prefixes stop at
    segment boundaries, which is why `design/` is not satisfied by a line
    naming `design-evidence.json`. A bare `.hexaemeron/` is mapped by the
    shipped directory itself and by nothing narrower.
    """
    tail = reference[len(".hexaemeron/"):]
    if not tail:
        return [""]
    targets = [tail]
    parts = [part for part in tail.split("/") if part]
    for stop in range(len(parts) - 1, 0, -1):
        targets.append("/".join(parts[:stop]) + "/")
    return targets


def says_it_is_not_shipped(text: str, reference: str) -> bool:
    """Does the file say, at the reference itself, that it did not travel?

    One reference in the study is the evaluator that wrote the reports, and it
    is genuinely absent from the repository rather than moved into it. Saying
    so is the honest mapping for that case, and it has to be said where the
    reader meets the path rather than somewhere else in the file.
    """
    return re.search(re.escape(reference) + r"`?\s+is not shipped", text) is not None


class ShippedCopyTests(unittest.TestCase):
    """The shipped artefacts, held against what the run recorded in them."""

    def test_the_shipped_study_carries_every_amendment(self):
        found = amendment_count(SHIPPED_STUDY)
        self.assertEqual(
            found, STUDY_AMENDMENTS,
            f"{SHIPPED_STUDY} carries {found} amendments where this step "
            f"shipped {STUDY_AMENDMENTS}. Either the copy is behind its "
            "source, or it was refreshed without moving the literal here; "
            "both leave a reader holding a document the run has corrected.",
        )

    def test_the_shipped_runbook_carries_every_amendment(self):
        found = amendment_count(SHIPPED_RUNBOOK)
        self.assertEqual(
            found, RUNBOOK_AMENDMENTS,
            f"{SHIPPED_RUNBOOK} carries {found} amendments where this step "
            f"shipped {RUNBOOK_AMENDMENTS}; the copy is behind its source, or "
            "the literal here was not moved with it.",
        )

    def test_every_controller_path_in_the_study_is_mapped_into_the_tree(self):
        """`.hexaemeron/` resolves to nothing for a reader holding the clone.

        The study is append-only once receipted, so the references cannot be
        rewritten where they stand. What it carries instead is a mapping, and
        the mapping only helps while it covers every path the study sends a
        reader to.
        """
        text = SHIPPED_STUDY.read_text(encoding="utf-8")
        references = sorted(set(CONTROLLER_REFERENCE.findall(text)))
        self.assertTrue(
            references,
            f"{SHIPPED_STUDY} names no `.hexaemeron/` path at all, so this "
            "case would pass on any file; the study it copies names five",
        )
        unmapped = []
        for reference in references:
            mapped = any(
                SHIPPED_PREFIX + target in text
                for target in mapping_targets(reference)
            )
            if mapped or says_it_is_not_shipped(text, reference):
                continue
            unmapped.append(reference)
        self.assertEqual(
            unmapped, [],
            "the shipped study sends a reader to a directory the repository "
            "does not carry, and nothing in the same file says where those "
            f"artefacts went or that they did not travel: {unmapped}",
        )

    def test_every_report_the_shipped_record_cites_resolves_beside_it(self):
        """The record is only evidence while the reports it names are here.

        A row that has been resolved names its report and that report's
        digest. Both are checked. A row the controller has not resolved names a
        path and no digest, so there are no bytes to compare against; it is
        checked for still being pending, and, where it belongs to the selected
        candidate, for naming a report that is actually here. The day it is
        resolved the digest comparison starts holding it too.
        """
        record = json.loads(SHIPPED_RECORD.read_text(encoding="utf-8"))
        rows = record["results"]
        selected = record["selection"]["candidate"]
        cited = [row for row in rows if isinstance(row.get("report"), dict)]
        self.assertTrue(
            cited,
            f"{SHIPPED_RECORD} cites no report with a digest, so this case "
            "would pass on an empty record",
        )
        wrong = []
        for row in cited:
            report = row["report"]
            path = report["path"]
            named = f"{row['candidate']}/{row['criterion']}"
            if not path.startswith(REPORT_PREFIX) or ".." in path.split("/"):
                wrong.append(f"{named}: {path} is not under {REPORT_PREFIX}")
                continue
            target = SHIPPED / path
            if not target.is_file():
                wrong.append(f"{named}: {path} is missing")
                continue
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            if digest != report["sha256"]:
                wrong.append(
                    f"{named}: {path} is {digest}, record names "
                    f"{report['sha256']}"
                )
        self.assertEqual(
            wrong, [],
            "the shipped design record cites evidence the shipped tree does "
            f"not carry at the bytes the record names: {wrong}",
        )

        undigested = [row for row in rows if not isinstance(row.get("report"), dict)]
        premature = [
            f"{row['candidate']}/{row['criterion']}: {row.get('state')}"
            for row in undigested
            if row.get("state") != "pending"
            or not isinstance(row.get("report"), str)
        ]
        self.assertEqual(
            premature, [],
            "a row the record treats as settled carries no report digest, so "
            f"the case above skipped evidence it should be holding: {premature}",
        )

        # A pending row still cites a path, and for the candidate the run
        # selected that citation is one this step is expected to satisfy: its
        # criterion blocks this step, and the report is written here before the
        # controller resolves the cell. Checking only the digested rows left
        # the one artefact the refresh adds outside every assertion in this
        # case, so the case passed on the tree that was missing it (S4-R1-02).
        # The other candidates' rows name reports that were never produced,
        # because only the selected design is built, so they stay unchecked.
        absent = sorted(
            f"{row['candidate']}/{row['criterion']}: {row['report']}"
            for row in undigested
            if row["candidate"] == selected
            and (
                not row["report"].startswith(REPORT_PREFIX)
                or ".." in row["report"].split("/")
                or not (SHIPPED / row["report"]).is_file()
            )
        )
        self.assertEqual(
            absent, [],
            "the shipped record sends a reader to evidence for the selected "
            f"design that the shipped tree does not carry: {absent}",
        )

        named = {row["report"]["path"] for row in cited}
        named.update(row["report"] for row in undigested)
        orphans = sorted(
            f"{REPORT_PREFIX}{path.name}"
            for path in SHIPPED_REPORTS.iterdir()
            if f"{REPORT_PREFIX}{path.name}" not in named
        )
        self.assertEqual(
            orphans, [],
            f"{SHIPPED_REPORTS} carries evidence the record does not cite, "
            f"which is what a copy refreshed from a stale source looks like: "
            f"{orphans}",
        )

        # A row can go missing by moving rather than by being deleted, and only
        # the second was caught. Deleting the selected candidate's undigested
        # row orphans the report it named, which the check above reports;
        # re-attributing that same row to another candidate leaves everything
        # above green, because the selected candidate then has no undigested
        # row and the pending check passes over an empty set, while the report
        # stays cited by the row that moved and so is no orphan (S4-R3-01).
        #
        # What holds it is the column rather than the row. The record declares
        # the criteria it judges candidates on, and the shipped copy exists to
        # carry the evidence for the one candidate the run selected, so that
        # candidate's column is one row per declared criterion and no more.
        # This survives the controller resolving a pending cell, which turns a
        # row's report from a path into a path and a digest and moves no row.
        # It is not the whole matrix, which is Protasis's to judge; it is the
        # one column this copy is evidence about.
        declared = [criterion["id"] for criterion in record["criteria"]]
        self.assertTrue(
            declared,
            f"{SHIPPED_RECORD} declares no criteria, so this case would pass "
            "on a record that judges the selected design against nothing",
        )
        held = [row["criterion"] for row in rows if row["candidate"] == selected]
        gaps = sorted(
            f"{criterion}: {held.count(criterion)} rows"
            for criterion in set(declared)
            if held.count(criterion) != 1
        )
        self.assertEqual(
            gaps, [],
            f"the shipped record does not carry exactly one row per declared "
            f"criterion for {selected}, the design the run selected, so a row "
            f"this copy is evidence about has been dropped or moved: {gaps}",
        )


if __name__ == "__main__":
    unittest.main()
