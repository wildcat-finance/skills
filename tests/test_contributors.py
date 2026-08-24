"""Hold the contributor generator's host-identity set equal to Fiat's.

ADR-016 names one mechanical set of runtime host identities and Fiat's
controller owns it. scripts/contributors.py keeps a copy so it stays a
standalone root script with no cross-plugin import. A copy that nothing checks
stops agreeing, so these tests read the frozensets straight out of hexctl.py's
syntax tree and compare them. Either side edited alone fails here.
"""

from __future__ import annotations

import ast
from pathlib import Path
import re
import sys
import tempfile
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import contributors  # noqa: E402

HEXCTL = REPOSITORY_ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
SET_NAMES = ("HOST_IDENTITY_NAMES", "HOST_IDENTITY_EMAILS", "HOST_PR_LOGINS")


def frozensets_from_source(path: Path, prefix: str = "HOST_") -> dict[str, frozenset]:
    """Read every `HOST_* = frozenset({...})` module-level literal without importing.

    Discovery is by prefix, not by the known names. A parity test that compares
    only the sets it already knows cannot notice a new one: if hexctl.py grows a
    fourth host set, the generator would miss a whole class of runtime identity
    and every test here would still pass. Reading by prefix turns that into a
    failure naming the set nobody accounted for.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: dict[str, frozenset] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.startswith(prefix):
            continue
        call = node.value
        if (
            not isinstance(call, ast.Call)
            or not isinstance(call.func, ast.Name)
            or call.func.id != "frozenset"
        ):
            # A HOST_* name that is not a frozenset is not a classification set.
            # hexctl.py has HOST_BYLINE_RE, a compiled pattern. Skipping it here
            # is deliberate; a genuinely missing set is caught by comparing the
            # discovered names against SET_NAMES, not by asserting shape here.
            continue
        if len(call.args) != 1:
            raise AssertionError(
                f"{target.id} in {path.name} is frozenset() with "
                f"{len(call.args)} arguments, which this test cannot read"
            )
        try:
            members = ast.literal_eval(call.args[0])
        except (ValueError, TypeError) as error:
            raise AssertionError(
                f"{target.id} in {path.name} is a frozenset of something other than "
                f"a literal, so this test cannot compare it: {error}"
            ) from error
        found[target.id] = frozenset(members)
    return found


class HostSetParity(unittest.TestCase):
    """The generator's copy of the host set matches Fiat's declaration."""

    @classmethod
    def setUpClass(cls):
        cls.declared = frozensets_from_source(HEXCTL)

    def test_hexctl_declares_exactly_the_sets_the_generator_accounts_for(self):
        """A host set in hexctl.py that the generator does not know about fails here."""
        self.assertEqual(
            sorted(self.declared),
            sorted(SET_NAMES),
            "hexctl.py's HOST_* frozensets and scripts/contributors.py have diverged; "
            "a set present there and absent here is a class of runtime identity the "
            "contributor ranking would silently treat as a person",
        )
        for name in SET_NAMES:
            self.assertTrue(self.declared[name], f"{name} is empty in hexctl.py")

    def test_host_identity_names_match(self):
        self.assertEqual(
            contributors.HOST_IDENTITY_NAMES,
            self.declared["HOST_IDENTITY_NAMES"],
        )

    def test_host_identity_emails_match(self):
        self.assertEqual(
            contributors.HOST_IDENTITY_EMAILS,
            self.declared["HOST_IDENTITY_EMAILS"],
        )

    def test_host_pr_logins_match(self):
        self.assertEqual(
            contributors.HOST_PR_LOGINS,
            self.declared["HOST_PR_LOGINS"],
        )

    def test_is_host_identity_agrees_on_every_declared_entry(self):
        """Equal sets are not enough; the predicate over them must also agree."""
        for name in sorted(self.declared["HOST_IDENTITY_NAMES"]):
            self.assertTrue(
                contributors.is_host_identity(name, "person@example.com"),
                f"{name!r} is a declared host name but was not recognised",
            )
            self.assertTrue(
                contributors.is_host_identity(name.upper(), "person@example.com"),
                f"{name!r} must be recognised case-insensitively",
            )
        for email in sorted(self.declared["HOST_IDENTITY_EMAILS"]):
            self.assertTrue(
                contributors.is_host_identity("A Person", email),
                f"{email!r} is a declared host email but was not recognised",
            )

    def test_a_human_author_is_not_a_host_identity(self):
        self.assertFalse(contributors.is_host_identity("Dave Coleman", "dave@example.com"))
        self.assertFalse(contributors.is_host_identity("Radu P", "radu@example.com"))
        self.assertFalse(contributors.is_host_identity("", ""))


class LoginGrammar(unittest.TestCase):
    """Only a login that cannot carry Markdown reaches an artefact."""

    def test_accepts_real_login_shapes(self):
        for login in ("kethcode", "radup1337", "a", "a-b", "A1", "x" * 39):
            self.assertTrue(contributors.valid_login(login), login)

    def test_rejects_markdown_and_out_of_range(self):
        for login in (
            "",
            "x" * 40,
            "-leading",
            "trailing-",
            "has space",
            "[link](http://example.com)",
            "back`tick",
            "under_score",
            "claude[bot]",
            "app/claude",
            "semi;colon",
            "new\nline",
        ):
            self.assertFalse(contributors.valid_login(login), login)

    def test_host_logins_are_recognised(self):
        for login in sorted(contributors.HOST_PR_LOGINS):
            self.assertTrue(contributors.is_host_login(login), login)
        self.assertTrue(contributors.is_host_login("CLAUDE[BOT]"))
        self.assertFalse(contributors.is_host_login("kethcode"))


class GuardOrder(unittest.TestCase):
    """Host exclusion has to happen before login-grammar validation.

    Some host logins are deliberately not valid GitHub logins. If the ranking
    pipeline validated grammar first, a known runtime identity would trip the
    bad-grammar stop and fail the whole run instead of being dropped quietly,
    which is the difference between a working weekly refresh and a red job.
    """

    def test_a_host_login_that_fails_grammar_is_still_recognised_as_a_host(self):
        offenders = [
            login
            for login in sorted(contributors.HOST_PR_LOGINS)
            if not contributors.valid_login(login)
        ]
        self.assertTrue(
            offenders,
            "the ordering hazard this test guards has gone; if no host login can "
            "fail the grammar check any more, delete this test deliberately",
        )
        for login in offenders:
            self.assertTrue(
                contributors.is_host_login(login),
                f"{login!r} fails the grammar check, so host exclusion must catch it first",
            )

    def test_claude_bot_is_the_concrete_case(self):
        self.assertFalse(contributors.valid_login("claude[bot]"))
        self.assertTrue(contributors.is_host_login("claude[bot]"))


class EmitterContract(unittest.TestCase):
    """The Elenchus report emitter stays wired to the surface it claims.

    The emitter is not executed here. It loads this very module, so running it
    from inside this module would recurse. What is checked is the wiring that
    silently breaks: the reused helpers still import, the declared surface still
    exists, and the report still carries the schema Elenchus reads.
    """

    def setUp(self):
        from tests import emit_contributors_report

        self.emitter = emit_contributors_report

    def test_the_reused_write_path_still_imports(self):
        for name in ("report_target", "result_payload", "write_report"):
            self.assertTrue(
                callable(getattr(self.emitter, name, None)),
                f"{name} no longer imports from emit_run_observation_report",
            )

    def test_every_declared_required_file_exists(self):
        for relative in self.emitter.REQUIRED_SURFACE:
            self.assertTrue(
                (REPOSITORY_ROOT / relative).is_file(),
                f"{relative.as_posix()} is declared required but is absent",
            )

    def test_declared_modules_are_importable_test_modules(self):
        self.assertEqual(self.emitter.MODULES, ("tests.test_contributors",))
        unittest.defaultTestLoader.loadTestsFromNames(list(self.emitter.MODULES))

    def test_missing_surface_produces_a_failing_suite(self):
        with tempfile.TemporaryDirectory() as empty:
            suite = self.emitter.missing_surface_suite(Path(empty))
        self.assertIsNotNone(suite, "an empty root must not look like a present surface")
        result = unittest.TestResult()
        suite.run(result)
        self.assertEqual(len(result.failures) + len(result.errors), 1)

    def test_present_surface_produces_no_substitute_suite(self):
        self.assertIsNone(self.emitter.missing_surface_suite(REPOSITORY_ROOT))

    def test_report_payload_carries_the_elenchus_schema(self):
        result = unittest.TestResult()
        payload = self.emitter.result_payload(result)
        self.assertEqual(payload["schema"], "elenchus.unittest.v1")
        self.assertTrue(payload["complete"])
        for key in ("testsRun", "failures", "errors", "skipped"):
            self.assertIn(key, payload)


class CommittedSpecLinks(unittest.TestCase):
    """Every relative link in the published spec resolves.

    The spec is authored inside the run's .hexaemeron directory, where
    `../ephoros/SKILL.md` means the sibling skill. Copied to docs/contributors/
    that same text points at docs/ephoros/, which does not exist. Copying a
    document changes what its relative links mean, and nothing else in this
    repository checks a link in a shipped document.
    """

    SPEC = ("docs/contributors/study.md", "docs/contributors/runbook.md")

    def test_every_relative_link_resolves(self):
        dead = []
        for relative in self.SPEC:
            doc = REPOSITORY_ROOT / relative
            self.assertTrue(doc.is_file(), f"{relative} is absent")
            for match in re.finditer(r"\]\(([^)]+)\)", doc.read_text(encoding="utf-8")):
                href = match.group(1)
                if href.startswith(("http://", "https://", "#", "mailto:")):
                    continue
                target = (doc.parent / href.split("#", 1)[0]).resolve()
                if not target.exists():
                    dead.append(f"{relative}: {href}")
        self.assertEqual(dead, [], "dead relative links in the published spec: " + "; ".join(dead))


    def test_no_published_file_cites_the_run_state_directory(self):
        """.hexaemeron is fully gitignored, so a clone never has it.

        A published document that sends a reader to `.hexaemeron/study.md` is
        citing a path that exists only on the machine that ran the delivery.
        """
        offenders = []
        for relative in self.SPEC:
            text = (REPOSITORY_ROOT / relative).read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), start=1):
                if ".hexaemeron" in line:
                    offenders.append(f"{relative}:{number}")
        self.assertEqual(
            offenders,
            [],
            "published spec cites the untracked run-state directory at: " + "; ".join(offenders),
        )


if __name__ == "__main__":
    unittest.main()
