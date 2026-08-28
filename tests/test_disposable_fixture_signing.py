"""A disposable git fixture must not sign its commits.

A test that creates a repository and commits into it inherits whatever signing
configuration the contributor has. On a GPG contributor that stalls the suite on
a pinentry prompt; on an SSH contributor it quietly signs fixture history with a
real identity. Fixture history is not signing evidence either way, so a fixture
declares ``git config --local commit.gpgsign false`` immediately after the
repository comes into existence, whichever verb created it.

This is the guard for that rule. It is the only test here that fails when the
cause is signing rather than the change under test, and it answers four
questions for whoever is reading a red suite.

- *Did this fail because of my change, or because of my signing setup?* This
  module failing, and nothing else, means signing.
- *Was the signer actually reached?* Every failure message carries the sentinel
  path and what the sentinel recorded, not merely whether it was empty.
- *Is this green for the right reason?* ``NegativeControl`` is the answer. It
  fails saying the hostile configuration failed to be hostile, which points at
  the harness rather than at the fix, and needs a different repair.
- *Did a fixture commit get signed with my key?* The positive case reads ``%G?``
  and requires exactly ``N``, and reads the commit object and requires no
  signature header. A commit that succeeds but is signed still breaks the rule.
  The object read is the half that discriminates: ``%G?`` is a verification
  verdict, and under the hostile configuration git has no verifier, so it
  answers ``N`` for a signed commit as readily as for an unsigned one.

Nothing here skips. A guard that skips when it cannot build its hostile
configuration reports as a pass and reads as evidence, so a missing git or an
unwritable configuration fails and names the precondition that was missing.
"""

from collections import namedtuple
from pathlib import Path
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
HARNESS = ROOT / "tests" / "hostile_signing_harness.py"

GIT = shutil.which("git")

# Bounded so a reintroduced pinentry stall fails this guard instead of hanging
# it. Git against a two-file repository needs a fraction of a second; a single
# representative test from another suite is given room to be slow.
GIT_TIMEOUT_SECONDS = 60
SUITE_TIMEOUT_SECONDS = 300


def load_harness():
    """Load the harness by path, so the guard proves the module a shell runs."""
    spec = importlib.util.spec_from_file_location("hostile_signing_harness", HARNESS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


harness = load_harness()


CoveredSuite = namedtuple("CoveredSuite", ("label", "top_level", "test"))

# The suites the rule has been applied to, and for each one a representative
# test that commits fixture history. Running it under the hostile configuration
# is what fails when a construction site in that suite forgets the rule.
# ``top_level`` is the unittest top-level directory, relative to the repository
# root, that ``test`` is resolved from.
COVERED_SUITES = ()

# The two ways a configuration value arrives carrying `git -c` precedence,
# which outranks the repository-local declaration. A caller sets the
# GIT_CONFIG_COUNT triple by hand; git converts its own `-c` into
# GIT_CONFIG_PARAMETERS and hands that to every process it spawns, so a suite
# run from inside `git -c ... bisect run` inherits it without anyone typing it.
COMMAND_LINE_CHANNELS = {
    "GIT_CONFIG_PARAMETERS": {"GIT_CONFIG_PARAMETERS": "'commit.gpgsign=true'"},
    "GIT_CONFIG_COUNT": {
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "commit.gpgsign",
        "GIT_CONFIG_VALUE_0": "true",
    },
}


class HostileCase(unittest.TestCase):
    """Each case builds its own hostile configuration in its own directory."""

    def setUp(self):
        if GIT is None:
            self.fail(
                "this guard fails rather than skips: git is not available, so "
                "the hostile signing configuration cannot be exercised and a "
                "skip here would report as a pass"
            )
        self.workspace = Path(self.enterContext(tempfile.TemporaryDirectory())).resolve()

    def hostile(self, arm, name=None):
        """Write one arm into a fresh directory belonging to this case.

        ``name`` names that directory when one case builds the same arm more
        than once, so two subtests cannot land in each other's sentinel.
        """
        directory = self.workspace / (name or arm)
        directory.mkdir()
        try:
            return harness.write_arm(directory, arm)
        except (OSError, ValueError) as error:
            self.fail(
                "this guard fails rather than skips: the hostile "
                f"{arm} configuration could not be written ({error})"
            )

    def recorded(self, files):
        """What the hostile signer recorded, for a failure message to carry."""
        return files.sentinel.read_text(encoding="utf-8")

    def git(self, root, environment, *arguments):
        """One bounded git call against a disposable repository. Fixed argv, no shell."""
        return subprocess.run(
            [GIT, "-C", str(root), *arguments],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
            env=environment,
        )

    def git_or_fail(self, root, environment, *arguments):
        """The same call, where anything but success is a missing precondition."""
        result = self.git(root, environment, *arguments)
        if result.returncode != 0:
            self.fail(
                "this guard fails rather than skips: `git "
                f"{' '.join(arguments)}` could not build the disposable "
                f"repository ({result.stderr.strip()})"
            )
        return result

    def signature_headers(self, root, environment):
        """The commit object's signature headers, read without any verifier.

        ``%G?`` is a verification verdict rather than a presence check. The
        hostile configuration names no ``gpg.ssh.allowedSignersFile``, so git
        cannot verify an ssh signature under it and reports ``N`` -- the same
        letter a genuinely unsigned commit gets. Measured on an ssh-signing
        host: a commit signed with the contributor's real key reads ``G``
        under their own configuration and ``N`` under either hostile arm. The
        object itself needs no verifier and no key material, so it answers
        "was this signed" the same way whatever configuration is in force.
        """
        raw = self.git_or_fail(root, environment, "cat-file", "commit", "HEAD")
        headers = raw.stdout.split("\n\n", 1)[0].splitlines()
        return [line.split(" ", 1)[0] for line in headers if line.startswith("gpgsig")]

    def fixture(self, files, declare, base=None):
        """Build a disposable repository under the hostile arm and commit once.

        ``declare`` chooses whether the repository states the rule the way a
        fixture is meant to. ``base`` is the environment the child inherits
        before the harness strips it, which is how a caller stands in for a
        suite launched from inside another git process. Returns the repository
        root and the commit's completed process, so a caller can read the code
        git actually exited on.
        """
        root = files.config.parent / ("declared" if declare else "undeclared")
        root.mkdir()
        environment = harness.child_environment(files.config, base=base)
        self.git_or_fail(root, environment, "init", "-q")
        if declare:
            self.git_or_fail(
                root, environment, "config", "--local", "commit.gpgsign", "false"
            )
        (root / "fixture.txt").write_text("fixture history\n", encoding="utf-8")
        self.git_or_fail(root, environment, "add", "fixture.txt")
        return root, self.git(root, environment, "commit", "-qm", "fixture history")


class HostileHarness(HostileCase):
    """The harness writes what it claims to write, and writes it nowhere else."""

    def test_the_openpgp_arm_points_gpg_program_at_the_recording_signer(self):
        files = self.hostile(harness.OPENPGP)
        text = files.config.read_text(encoding="utf-8")
        self.assertIn("gpgsign = true", text)
        self.assertIn("format = openpgp", text)
        self.assertIn(f'program = "{files.signer}"', text)
        self.assertTrue(os.access(files.signer, os.X_OK), f"{files.signer} is not executable")
        self.assertEqual(self.recorded(files), "")

    def test_the_ssh_arm_points_gpg_ssh_program_at_the_recording_signer(self):
        files = self.hostile(harness.SSH)
        text = files.config.read_text(encoding="utf-8")
        self.assertIn("gpgsign = true", text)
        self.assertIn("format = ssh", text)
        self.assertIn('[gpg "ssh"]', text)
        self.assertIn(f'program = "{files.signer}"', text)
        self.assertTrue(os.access(files.signer, os.X_OK), f"{files.signer} is not executable")
        self.assertEqual(self.recorded(files), "")

    def test_the_unsigned_control_arm_commits_without_reaching_the_signer(self):
        files = self.hostile(harness.UNSIGNED)
        _, result = self.fixture(files, declare=False)
        self.assertEqual(
            result.returncode,
            0,
            "the unsigned control arm asks for no signature, so a fixture commit "
            f"must succeed under it. git said: {result.stderr.strip()}",
        )
        self.assertEqual(
            self.recorded(files),
            "",
            "the sentinel records signing attempts, not commits, but the "
            f"unsigned control arm reached the signer at {files.signer}. "
            f"Sentinel {files.sentinel} holds: {self.recorded(files)!r}",
        )

    def test_the_harness_leaves_the_running_process_environment_alone(self):
        before = dict(os.environ)
        files = self.hostile(harness.OPENPGP)
        environment = harness.child_environment(files.config)
        self.assertEqual(
            dict(os.environ),
            before,
            "the harness changed this process's environment, so a failure part "
            "way through a test could leave the contributor's git pointed at a "
            "temporary file",
        )
        self.assertEqual(environment["GIT_CONFIG_GLOBAL"], str(files.config))
        self.assertEqual(environment["GIT_CONFIG_SYSTEM"], os.devnull)
        # Asserted against a base that actually carries them. Reading them off
        # `os.environ`, which holds neither, would pass without the drop.
        inherited = dict(os.environ)
        inherited.update(COMMAND_LINE_CHANNELS["GIT_CONFIG_PARAMETERS"])
        inherited.update(COMMAND_LINE_CHANNELS["GIT_CONFIG_COUNT"])
        stripped = harness.child_environment(files.config, base=inherited)
        for name in ("GIT_CONFIG_COUNT", "GIT_CONFIG_PARAMETERS"):
            self.assertNotIn(
                name,
                stripped,
                f"{name} carries `git -c` precedence and survived into the "
                "child environment, so an outer git process can re-enable "
                "signing over a fixture that declared the rule correctly",
            )

    def test_the_emit_entry_point_writes_the_arm_the_negative_control_proves(self):
        directory = self.workspace / "emitted"
        directory.mkdir()
        result = subprocess.run(
            [sys.executable, str(HARNESS), "--emit", str(directory)],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        signer = directory / harness.SIGNER_NAME
        sentinel = directory / harness.SENTINEL_NAME
        self.assertTrue(os.access(signer, os.X_OK), f"{signer} is not executable")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "")
        self.assertEqual(
            (directory / harness.CONFIG_NAME).read_text(encoding="utf-8"),
            harness.config_text(harness.EMITTED_ARM, signer),
            "the emitted configuration is not the arm this module proves "
            "hostile, so a later step would run its suites under something no "
            "test here has exercised",
        )


class NegativeControl(HostileCase):
    """Without the rule, a fixture commit reaches the hostile signer and fails.

    This is the assertion that makes every other assertion in this module mean
    something. If it passes, the hostile configuration is not hostile, and the
    positive case below is green for no reason at all.
    """

    def test_the_hostile_signer_is_reached_without_the_local_declaration(self):
        for arm in (harness.OPENPGP, harness.SSH):
            with self.subTest(arm=arm):
                files = self.hostile(arm)
                _, result = self.fixture(files, declare=False)
                recorded = self.recorded(files)
                self.assertNotEqual(
                    result.returncode,
                    0,
                    f"the hostile {arm} configuration failed to be hostile: a "
                    "fixture commit that declares nothing still succeeded, so "
                    "the rest of this module proves nothing. Repair the harness, "
                    f"not the fixtures. Sentinel {files.sentinel} holds: "
                    f"{recorded!r}",
                )
                self.assertNotEqual(
                    recorded,
                    "",
                    f"the hostile {arm} configuration failed to be hostile: the "
                    f"signing program at {files.signer} was never reached, so "
                    "the commit failed for some other reason and this guard is "
                    f"measuring the wrong thing. git said: {result.stderr.strip()}",
                )


class InheritedPrecedence(HostileCase):
    """An inherited `git -c` channel cannot defeat the declaration under test.

    Both channels outrank repository-local config, so either one carrying
    ``commit.gpgsign=true`` would drive a correctly declared fixture into the
    signer, and the failure would read as a broken fix rather than as a
    contaminated environment. The harness strips them from the child; this is
    the end-to-end proof that stripping them is enough.
    """

    def test_an_inherited_command_line_channel_cannot_re_enable_signing(self):
        for label, inherited in COMMAND_LINE_CHANNELS.items():
            with self.subTest(channel=label):
                files = self.hostile(harness.OPENPGP, name=f"inherited-{label}")
                base = dict(os.environ)
                base.update(inherited)
                _, result = self.fixture(files, declare=True, base=base)
                recorded = self.recorded(files)
                self.assertEqual(
                    result.returncode,
                    0,
                    f"an inherited {label} re-enabled signing over a fixture "
                    "that declared `git config --local commit.gpgsign false`, "
                    "so the harness is not stripping it from the child. git "
                    f"said: {result.stderr.strip()}. Sentinel {files.sentinel} "
                    f"holds: {recorded!r}",
                )
                self.assertEqual(
                    recorded,
                    "",
                    f"an inherited {label} reached the signer at "
                    f"{files.signer} from a fixture that declared the rule. "
                    f"Sentinel {files.sentinel} holds: {recorded!r}",
                )


class LocalDeclaration(HostileCase):
    """With the rule, the same construction commits, unsigned, untouched by the signer."""

    def test_the_local_declaration_defeats_the_hostile_signer(self):
        for arm in (harness.OPENPGP, harness.SSH):
            with self.subTest(arm=arm):
                files = self.hostile(arm)
                root, result = self.fixture(files, declare=True)
                recorded = self.recorded(files)
                self.assertEqual(
                    result.returncode,
                    0,
                    "a fixture that declares `git config --local commit.gpgsign "
                    f"false` still could not commit under inherited {arm} "
                    f"signing. git said: {result.stderr.strip()}. Sentinel "
                    f"{files.sentinel} holds: {recorded!r}",
                )
                self.assertEqual(
                    recorded,
                    "",
                    "`commit.gpgsign false` was declared and the signer at "
                    f"{files.signer} was reached anyway. Sentinel "
                    f"{files.sentinel} holds: {recorded!r}",
                )
                status = self.git(
                    root,
                    harness.child_environment(files.config),
                    "log",
                    "-1",
                    "--format=%G?",
                )
                self.assertEqual(
                    status.stdout.strip(),
                    "N",
                    "the fixture commit carries a signature. A commit that "
                    "succeeds but is signed still breaks the rule, because it "
                    "signs fixture history with the contributor's real identity",
                )
                # `%G?` above cannot carry this on its own: it reports `N` for
                # a signed commit it has no verifier for, which under the
                # hostile configuration is every signed commit. The object is
                # read too, and it is the half that discriminates.
                self.assertEqual(
                    self.signature_headers(
                        root, harness.child_environment(files.config)
                    ),
                    [],
                    "the fixture commit object carries a signature header. A "
                    "commit that succeeds but is signed still breaks the rule, "
                    "because it signs fixture history with the contributor's "
                    "real identity",
                )


class SignedFixture(HostileCase):
    """A signed fixture commit is caught, and `%G?` alone is not what catches it.

    Under the hostile configuration git has no ``gpg.ssh.allowedSignersFile``,
    so it cannot verify an ssh signature and reports ``N`` -- the same letter a
    genuinely unsigned commit gets. A positive case that read only ``%G?``
    would pass on fixture history signed with the contributor's real identity,
    which is the outcome this whole delivery exists to prevent on an
    ssh-signing host. This builds a genuinely signed commit from a throwaway
    key that never leaves the test's own temporary directory, and shows both
    halves: ``%G?`` says ``N``, and the commit object says otherwise.
    """

    def throwaway_key(self):
        """An ed25519 key belonging to this test, so no real identity signs."""
        keygen = shutil.which("ssh-keygen")
        if keygen is None:
            self.fail(
                "this guard fails rather than skips: ssh-keygen is not "
                "available, so a genuinely signed fixture commit cannot be "
                "built and the positive case's signature assertion would go "
                "unproven"
            )
        key = self.workspace / "throwaway-key"
        result = subprocess.run(
            [keygen, "-q", "-t", "ed25519", "-N", "", "-C", "throwaway",
             "-f", str(key)],
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
        if result.returncode != 0:
            self.fail(
                "this guard fails rather than skips: a throwaway signing key "
                f"could not be generated ({result.stderr.strip()})"
            )
        return key

    def test_a_signed_fixture_commit_reads_as_unsigned_under_the_hostile_config(self):
        key = self.throwaway_key()
        files = self.hostile(harness.UNSIGNED, name="signed-fixture")
        root = files.config.parent / "signed"
        root.mkdir()
        signing = self.workspace / "signing.gitconfig"
        signing.write_text(
            harness.IDENTITY
            + f"\tsigningkey = {key}\n"
            "[commit]\n\tgpgsign = true\n"
            "[gpg]\n\tformat = ssh\n",
            encoding="utf-8",
        )
        environment = harness.child_environment(signing)
        self.git_or_fail(root, environment, "init", "-q")
        (root / "fixture.txt").write_text("signed history\n", encoding="utf-8")
        self.git_or_fail(root, environment, "add", "fixture.txt")
        commit = self.git(root, environment, "commit", "-qm", "signed history")
        self.assertEqual(
            commit.returncode,
            0,
            "a throwaway ssh key could not sign a fixture commit, so this "
            f"test cannot say what a signed one looks like. git said: "
            f"{commit.stderr.strip()}",
        )

        hostile = harness.child_environment(files.config)
        status = self.git(root, hostile, "log", "-1", "--format=%G?")
        self.assertEqual(
            status.stdout.strip(),
            "N",
            "`%G?` reported something other than `N` for a signed commit it "
            "cannot verify. That is a better answer than the one measured "
            "here, and the positive case's `%G?` assertion is stronger than "
            "this test assumes -- but the object read below is what the "
            "positive case relies on, so update this test rather than it",
        )
        self.assertNotEqual(
            self.signature_headers(root, hostile),
            [],
            "a commit signed with a throwaway ssh key shows no signature "
            "header, so the check the positive case relies on cannot tell a "
            "signed fixture from an unsigned one and the rule is unguarded",
        )


class CoveredSuites(HostileCase):
    """Every suite the rule has been applied to still runs under inherited signing."""

    def test_each_covered_suite_runs_clean_under_the_hostile_configuration(self):
        files = self.hostile(harness.EMITTED_ARM)
        environment = harness.child_environment(files.config)
        for suite in COVERED_SUITES:
            with self.subTest(suite=suite.label):
                result = subprocess.run(
                    [sys.executable, "-m", "unittest", suite.test],
                    cwd=str(ROOT / suite.top_level),
                    capture_output=True,
                    text=True,
                    timeout=SUITE_TIMEOUT_SECONDS,
                    env=environment,
                )
                recorded = self.recorded(files)
                self.assertEqual(
                    result.returncode,
                    0,
                    f"{suite.label} does not survive inherited signing: "
                    f"{suite.test} exited {result.returncode}. A construction "
                    "site in that suite is missing `git config --local "
                    f"commit.gpgsign false`. Sentinel {files.sentinel} holds: "
                    f"{recorded!r}. It said: {result.stderr.strip()}",
                )
                self.assertEqual(
                    recorded,
                    "",
                    f"{suite.label} reached the signer at {files.signer} while "
                    f"running {suite.test}. Sentinel {files.sentinel} holds: "
                    f"{recorded!r}",
                )


if __name__ == "__main__":
    unittest.main()
