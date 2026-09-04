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


class StagedTreeTests(unittest.TestCase):
    def test_a_failing_write_tree_is_refused_and_named(self):
        """S2-R1-04: the fourth state section 11 requires to exit non-zero.

        Driven directly rather than through `git commit`, because git will not
        reach the hook once its own index is unreadable.
        """
        with gate_repository() as root:
            broken = root.parent / "not-an-index"
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
    is measuring.

    Not the index file's own bytes. `git write-tree` does persist a cache tree
    into an index that lacks one, so those bytes can move while nothing staged
    does. Measured on git 2.50.1, that does not happen along this path: driving
    the gate at an outer index leaves the file byte-identical. They are still
    left out, because asserting them would pin where write-tree happened to
    persist rather than the staged state the incident class is about.
    """
    entries = git(root, "ls-files", "--stage").stdout
    cached = git(root, "diff", "--cached", "--name-status", "--").stdout
    head = git(root, "rev-parse", "HEAD").stdout
    worktree = git(root, "--no-optional-locks", "status", "--porcelain").stdout
    refs = git(root, "for-each-ref").stdout
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
    at `tests/test_boundary_currency.py:57-73`.

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


if __name__ == "__main__":
    unittest.main()
