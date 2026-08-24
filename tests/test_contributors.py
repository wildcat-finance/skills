"""Hold the contributor generator's host-identity set equal to Fiat's.

ADR-016 names one mechanical set of runtime host identities and Fiat's
controller owns it. scripts/contributors.py keeps a copy so it stays a
standalone root script with no cross-plugin import. A copy that nothing checks
stops agreeing, so these tests read the frozensets straight out of hexctl.py's
syntax tree and compare them. Either side edited alone fails here.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import unittest
import urllib.request

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts import contributors  # noqa: E402

HEXCTL = REPOSITORY_ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
SET_NAMES = ("HOST_IDENTITY_NAMES", "HOST_IDENTITY_EMAILS", "HOST_PR_LOGINS")


class HostSetParity(unittest.TestCase):
    """The generator's copy of the host set matches Fiat's declaration."""

    @classmethod
    def setUpClass(cls):
        cls.declared = contributors.frozensets_from_source(HEXCTL)

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

    # Every document this work ships, not only the two the guard was written for.
    # Rounds 3 and 4 of step 1 found the same dead-link defect twice, and a guard
    # scoped to the files that had already failed would not have caught it in the
    # records added later.
    SPEC = (
        "docs/contributors/study.md",
        "docs/contributors/runbook.md",
        "docs/decisions/ADR-018-rank-contributors-by-resolved-identity.md",
        "docs/promise-machine/contributors-v1.md",
        "CONTRIBUTORS.md",
    )

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
            document = REPOSITORY_ROOT / relative
            # Assert presence rather than dereferencing it: a missing file must
            # fail this test, not error out of it, or Elenchus cannot tell a
            # proved guard from a broken harness.
            self.assertTrue(document.is_file(), f"{relative} is absent")
            text = document.read_text(encoding="utf-8")
            for number, line in enumerate(text.splitlines(), start=1):
                if "`.hexaemeron/" in line or "](.hexaemeron/" in line:
                    offenders.append(f"{relative}:{number}")
        self.assertEqual(
            offenders,
            [],
            "published spec cites the untracked run-state directory at: " + "; ".join(offenders),
        )


class RecordedDecisions(unittest.TestCase):
    """The claims and records this work is obliged to leave behind."""

    ADR = REPOSITORY_ROOT / "docs/decisions/ADR-018-rank-contributors-by-resolved-identity.md"
    PROMISE_DOC = REPOSITORY_ROOT / "docs/promise-machine/contributors-v1.md"
    GUIDE = REPOSITORY_ROOT / "docs/how-to-help-shoggoth.md"
    README = REPOSITORY_ROOT / "README.md"

    def test_the_readme_claim_names_the_file_it_promises(self):
        text = self.README.read_text(encoding="utf-8")
        head = text.split(contributors.THANKS_START)[0]
        self.assertIn(
            "CONTRIBUTORS.md",
            head,
            "the recognition sentence must name the list, not just imply one exists",
        )
        self.assertIn("weekly", head)

    def test_the_readme_claim_names_the_condition_it_cannot_control(self):
        head = self.README.read_text(encoding="utf-8").split(contributors.THANKS_START)[0]
        self.assertIn("outside this repository's control", head)
        self.assertIn("linked to no account", head)

    def test_the_adr_records_the_decision_and_the_option_it_rejected(self):
        self.assertTrue(self.ADR.is_file(), f"{self.ADR.name} is absent")
        text = self.ADR.read_text(encoding="utf-8")
        self.assertIn("Wildcat-Origin", text, "the rejected option must be named")
        self.assertIn("empty file", text, "the evidence against it must be stated")
        self.assertIn("ADR-016", text)
        self.assertIn("#466", text)
        for heading in ("## Status", "## Context", "## Decision", "## Alternatives", "## Consequences"):
            self.assertIn(heading, text, f"{heading} missing from the record")

    def test_the_promise_contract_states_a_boundary_and_refusals(self):
        self.assertTrue(self.PROMISE_DOC.is_file(), f"{self.PROMISE_DOC.name} is absent")
        text = self.PROMISE_DOC.read_text(encoding="utf-8")
        for heading in ("## Boundary", "## Refuses", "## Recovery", "## Evidence classes"):
            self.assertIn(heading, text)

    def test_the_promise_is_declared_in_the_authored_source(self):
        text = (REPOSITORY_ROOT / "PROMISE_MACHINE.md").read_text(encoding="utf-8")
        self.assertIn("promise-machine-contributor-ranking", text)
        block = text.split("promise-machine-contributor-ranking", 1)[1]
        for field in ("- Promise:", "- Evidence:", "- Boundary:", "- Refuses:", "- Recovery:"):
            self.assertIn(field, block.split("## ", 1)[0])

    def test_the_guide_says_what_the_list_does_not_establish(self):
        text = self.GUIDE.read_text(encoding="utf-8")
        self.assertIn("CONTRIBUTORS.md", text)
        self.assertIn("ADR-018-rank-contributors-by-resolved-identity", text)
        self.assertIn("not a ranking of people", text)


if __name__ == "__main__":
    unittest.main()


def fixture(name):
    return json.loads((REPOSITORY_ROOT / "tests/fixtures/contributors" / name).read_text("utf-8"))


def fake_reader(contributors_rows=None, merged=None, authors=None, issues=None, fail=None):
    """A reader over recorded data, so every test below runs with no network."""
    rows = fixture("contributors.json") if contributors_rows is None else contributors_rows
    merged = {} if merged is None else merged
    authors = {} if authors is None else authors
    issues = [] if issues is None else issues

    def read(path):
        if fail is not None:
            raise contributors.Stop(fail)
        if "/contributors" in path:
            return rows
        if "type:pr" in path:
            login = path.split("author:")[1].split("&")[0]
            return {"total_count": merged.get(login, 0)}
        if "/search/commits" in path:
            login = path.split("author:")[1].split("&")[0]
            recorded = authors.get(login)
            if recorded is None:
                recorded = fixture(f"authors-{login}.json")
            return {"items": [{"commit": {"author": pair}} for pair in recorded]}
        if "type:issue" in path:
            return {"items": [{"user": {"login": login}} for login in issues]}
        raise AssertionError(f"unexpected api path: {path}")

    return read


class Ranking(unittest.TestCase):
    """The ranking is computed from recorded responses, offline."""

    MERGED = {"kethcode": 15, "radup1337": 1}

    def compute(self, **kwargs):
        return contributors.compute(fake_reader(**kwargs), repo="wildcat-finance/skills")

    def test_ranks_only_the_human_contributors(self):
        payload = self.compute(merged=self.MERGED)
        self.assertEqual(
            [(c["rank"], c["login"]) for c in payload["contributors"]],
            [(1, "kethcode"), (2, "radup1337")],
        )

    def test_names_a_reason_for_every_exclusion(self):
        payload = self.compute(merged=self.MERGED)
        reasons = {e["login"]: e["reason"] for e in payload["excluded"]}
        self.assertEqual(
            sorted(reasons), ["claude", "claude[bot]", "laurenceday", "shoggoth-wildcat"]
        )
        self.assertIn("runtime host", reasons["claude"])
        self.assertIn("runtime host", reasons["claude[bot]"])
        self.assertIn("owner", reasons["laurenceday"])
        self.assertIn("Shoggoth", reasons["shoggoth-wildcat"])
        for login, reason in reasons.items():
            self.assertTrue(reason.strip(), f"{login} excluded with an empty reason")

    def test_shoggoth_is_never_ranked(self):
        """The request was explicit: excluding shoggoth itself."""
        payload = self.compute(merged=self.MERGED)
        self.assertNotIn(
            "shoggoth-wildcat", [c["login"] for c in payload["contributors"]]
        )

    def test_one_human_split_across_two_emails_ranks_once(self):
        """kethcode is Kethic and Dave Coleman; git log splits them, the API does not."""
        recorded = fixture("authors-kethcode.json")
        self.assertEqual(len({pair["email"] for pair in recorded}), 2)
        self.assertEqual(len({pair["name"] for pair in recorded}), 2)
        payload = self.compute(merged=self.MERGED)
        appearances = [c for c in payload["contributors"] if c["login"] == "kethcode"]
        self.assertEqual(len(appearances), 1)
        self.assertEqual(appearances[0]["commits"], 29)

    def test_equal_counts_order_deterministically(self):
        rows = [
            {"login": "zoe", "type": "User", "contributions": 5},
            {"login": "adam", "type": "User", "contributions": 5},
            {"login": "mia", "type": "User", "contributions": 5},
        ]
        authors = {name: [{"name": name, "email": f"{name}@example.com"}] for name in ("zoe", "adam", "mia")}
        first = contributors.compute(
            fake_reader(contributors_rows=rows, merged={"zoe": 2, "adam": 2, "mia": 9}, authors=authors),
            repo="x/y",
        )
        second = contributors.compute(
            fake_reader(contributors_rows=list(reversed(rows)), merged={"zoe": 2, "adam": 2, "mia": 9}, authors=authors),
            repo="x/y",
        )
        order = [c["login"] for c in first["contributors"]]
        self.assertEqual(order, ["mia", "adam", "zoe"], "merged PRs break the commit tie, then login")
        self.assertEqual(order, [c["login"] for c in second["contributors"]], "input order must not matter")

    def test_no_api_field_other_than_login_reaches_the_payload(self):
        rows = [
            {
                "login": "someone",
                "type": "User",
                "contributions": 3,
                "avatar_url": "https://example.com/a.png",
                "html_url": "https://example.com/someone",
                "node_id": "MDQ6VXNlcjE=",
            }
        ]
        payload = contributors.compute(
            fake_reader(
                contributors_rows=rows,
                merged={"someone": 0},
                authors={"someone": [{"name": "A Person", "email": "a@example.com"}]},
            ),
            repo="x/y",
        )
        blob = json.dumps(payload)
        for leaked in ("avatar_url", "html_url", "node_id", "example.com", "MDQ6"):
            self.assertNotIn(leaked, blob, f"{leaked} reached the payload")

    def test_classification_lines_name_every_identity(self):
        payload = self.compute(merged=self.MERGED)
        lines = contributors.classification_lines(payload)
        for login in ("kethcode", "radup1337", "claude", "claude[bot]", "laurenceday", "shoggoth-wildcat"):
            self.assertTrue(
                any(login in line for line in lines), f"{login} appears in no classification line"
            )

    def test_singular_merged_pull_request_reads_as_english(self):
        payload = self.compute(merged=self.MERGED)
        line = next(l for l in contributors.classification_lines(payload) if "radup1337" in l)
        self.assertIn("1 merged pull request", line)
        self.assertNotIn("1 merged pull requests", line)


class FailClosed(unittest.TestCase):
    """Each of the five stops in the study's item 11, one test each."""

    def test_stops_on_unknown_identity(self):
        rows = [{"login": "future-agent[bot]", "type": "Bot", "contributions": 4}]
        with self.assertRaises(contributors.Stop) as caught:
            contributors.compute(fake_reader(contributors_rows=rows), repo="x/y")
        self.assertIn("future-agent[bot]", str(caught.exception))
        self.assertIn("unknown identity", str(caught.exception))

    def test_stops_on_an_unknown_account_type(self):
        rows = [{"login": "mystery", "type": "Organization", "contributions": 4}]
        with self.assertRaises(contributors.Stop) as caught:
            contributors.compute(fake_reader(contributors_rows=rows), repo="x/y")
        self.assertIn("Organization", str(caught.exception))

    def test_stops_on_bad_login_grammar(self):
        rows = [{"login": "[injected](http://evil.example)", "type": "User", "contributions": 4}]
        with self.assertRaises(contributors.Stop) as caught:
            contributors.compute(fake_reader(contributors_rows=rows), repo="x/y")
        self.assertIn("not a valid GitHub login", str(caught.exception))

    def test_stops_on_api_failure(self):
        with self.assertRaises(contributors.Stop) as caught:
            contributors.compute(fake_reader(fail="api read failed for /x: timed out"), repo="x/y")
        self.assertIn("api read failed", str(caught.exception))

    def test_stops_on_host_set_drift(self):
        with tempfile.TemporaryDirectory() as work:
            drifted = Path(work) / "hexctl.py"
            drifted.write_text(
                HEXCTL.read_text(encoding="utf-8") + '\n\nHOST_FUTURE = frozenset({"nobody"})\n',
                encoding="utf-8",
            )
            with self.assertRaises(contributors.Stop) as caught:
                contributors.verify_host_set_parity(drifted)
        self.assertIn("host set drift", str(caught.exception))
        self.assertIn("HOST_FUTURE", str(caught.exception))

    def test_stops_on_a_changed_member_of_a_known_set(self):
        with tempfile.TemporaryDirectory() as work:
            drifted = Path(work) / "hexctl.py"
            text = HEXCTL.read_text(encoding="utf-8").replace('"devin",', '"devin",\n        "newhost",', 1)
            drifted.write_text(text, encoding="utf-8")
            with self.assertRaises(contributors.Stop) as caught:
                contributors.verify_host_set_parity(drifted)
        self.assertIn("HOST_IDENTITY_NAMES", str(caught.exception))
        self.assertIn("newhost", str(caught.exception))

    def test_stops_on_owner_in_output(self):
        """An owner that slipped past classification must not reach the ranking."""
        rows = [{"login": "laurenceday", "type": "User", "contributions": 900}]
        authors = {"laurenceday": [{"name": "Dr Laurence E. Day", "email": "l@example.com"}]}
        with self.assertRaises(contributors.Stop) as caught:
            contributors.compute(
                fake_reader(contributors_rows=rows, merged={"laurenceday": 1}, authors=authors),
                repo="x/y",
                excluded=frozenset(),
            )
        self.assertIn("laurenceday", str(caught.exception))
        self.assertIn("reached the ranked list", str(caught.exception))

    def test_stops_when_every_sampled_commit_is_a_runtime_host(self):
        rows = [{"login": "suspicious", "type": "User", "contributions": 7}]
        authors = {"suspicious": [{"name": "Claude", "email": "noreply@anthropic.com"}]}
        with self.assertRaises(contributors.Stop) as caught:
            contributors.compute(
                fake_reader(contributors_rows=rows, merged={"suspicious": 0}, authors=authors),
                repo="x/y",
            )
        self.assertIn("runtime host identity", str(caught.exception))

    def test_the_real_reader_refuses_a_non_absolute_path(self):
        """Exercises the network reader itself, not an injected substitute."""
        read = contributors.http_reader()
        with self.assertRaises(contributors.Stop) as caught:
            read("repos/x/y/contributors")
        self.assertIn("must be absolute", str(caught.exception))

    def test_the_real_reader_stops_on_an_unroutable_host(self):
        """A genuine transport failure, with no fixture standing in for it."""
        original = contributors.API_ROOT
        contributors.API_ROOT = "http://127.0.0.1:1"
        try:
            read = contributors.http_reader()
            with self.assertRaises(contributors.Stop) as caught:
                read("/repos/x/y/contributors")
        finally:
            contributors.API_ROOT = original
        self.assertIn("api read failed", str(caught.exception))


class RequiresSymbol:
    """Assert a symbol exists before using it, so a guard fails instead of erroring.

    Dereferencing a missing attribute raises AttributeError, which unittest
    records as an error rather than a failure. Elenchus will not call a round
    guarded once errors appear, because it cannot tell a proved guard from a
    broken harness. A guard that errors on the unfixed tree proves nothing it
    could not have proved by failing. This mixin is shared rather than copied per
    class: the same omission was made twice in this run already.
    """

    def require(self, name, why):
        value = getattr(contributors, name, None)
        self.assertIsNotNone(value, f"contributors.{name} is absent; {why}")
        return value

    def assert_stops(self, call, contains):
        """Require a Stop, and fail rather than error on any other exception.

        `assertRaises(Stop)` errors when the code raises the wrong type, and the
        wrong type is often the defect itself: a bare FileNotFoundError where a
        named Stop belongs. Elenchus reads an error as a broken harness, so a
        guard written that way cannot prove the fix it guards.
        """
        try:
            call()
        except contributors.Stop as stop:
            self.assertIn(contains, str(stop))
        except BaseException as other:  # noqa: BLE001 - the point is to catch everything
            self.fail(
                f"expected a Stop naming {contains!r}, got "
                f"{type(other).__name__}: {other}"
            )
        else:
            self.fail(f"expected a Stop naming {contains!r}; nothing was raised")


class NetworkBoundary(RequiresSymbol, unittest.TestCase):
    """Guards on the one boundary that reaches off the machine."""

    def redirect_handler(self):
        return self.require(
            "RefuseOffHostRedirect", "the off-host redirect guard is gone"
        )()

    def test_refuses_an_off_host_redirect_before_reissuing_the_request(self):
        """The token must not travel to the redirect target."""
        handler = self.redirect_handler()
        request = urllib.request.Request(
            contributors.API_ROOT + "/repos/x/y/contributors",
            headers={"Authorization": "Bearer secret-value"},
        )
        with self.assertRaises(contributors.Stop) as caught:
            handler.redirect_request(
                request, None, 302, "Found", {}, "https://evil.example/steal"
            )
        message = str(caught.exception)
        self.assertIn("redirected off", message)
        self.assertIn("evil.example", message)
        self.assertNotIn("secret-value", message, "the guard must not echo the token")

    def test_allows_a_redirect_that_stays_on_the_api_host(self):
        handler = self.redirect_handler()
        request = urllib.request.Request(contributors.API_ROOT + "/repos/x/y/contributors")
        result = handler.redirect_request(
            request, None, 301, "Moved", {}, contributors.API_ROOT + "/repositories/1/contributors"
        )
        self.assertIsNotNone(result)

    def test_urllib_would_otherwise_carry_the_authorization_header(self):
        """Pin the reason the guard exists, so nobody deletes it as belt and braces."""
        import inspect

        source = inspect.getsource(urllib.request.HTTPRedirectHandler.redirect_request)
        self.assertIn("content-length", source)
        self.assertNotIn("authorization", source.lower())

    def test_stops_on_a_repository_carrying_query_syntax(self):
        for bad in ("x/y&per_page=1", "x", "x/y/z", "x/y#frag", "x /y", "", "x/y+type:pr"):
            with self.assertRaises(contributors.Stop) as caught:
                contributors.compute(fake_reader(), repo=bad)
            self.assertIn("owner/name", str(caught.exception), bad)


class Coverage(RequiresSymbol, unittest.TestCase):
    """No silent cap. A truncated read must not read as full coverage."""

    def rows(self, count, offset=0):
        return [
            {"login": f"user{i + offset:04d}", "type": "User", "contributions": 1}
            for i in range(count)
        ]

    def pager(self):
        return self.require("read_all_pages", "the pagination guard is gone")

    def rate_limit_message(self):
        return self.require(
            "rate_limit_aware_message",
            "a rate-limited run would report a bare read failure again",
        )

    def test_reads_every_page_rather_than_the_first(self):
        pages = {1: self.rows(100), 2: self.rows(5, offset=100)}
        calls = []

        def read(path):
            page = int(path.split("&page=")[1])
            calls.append(page)
            return pages[page]

        collected = self.pager()(
            read, "/x?per_page={per_page}&page={page}", "test endpoint"
        )
        self.assertEqual(calls, [1, 2])
        self.assertEqual(len(collected), 105)

    def test_stops_rather_than_truncating_when_pages_never_end(self):
        def read(path):
            return self.rows(100)

        pager = self.pager()
        with self.assertRaises(contributors.Stop) as caught:
            pager(read, "/x?per_page={per_page}&page={page}", "test endpoint")
        self.assertIn("truncated", str(caught.exception))

    def test_stops_when_closed_issue_coverage_is_partial(self):
        def read(path):
            if "/contributors" in path:
                return []
            if "type:issue" in path:
                return {"total_count": 340, "items": [{"user": {"login": "someone"}}]}
            raise AssertionError(path)

        with self.assertRaises(contributors.Stop) as caught:
            contributors.compute(read, repo="x/y")
        self.assertIn("read 1 of 340", str(caught.exception))

    def test_reports_the_corroboration_evidence_it_gathered(self):
        payload = contributors.compute(
            fake_reader(merged={"kethcode": 15, "radup1337": 1}), repo="wildcat-finance/skills"
        )
        for entry in payload["contributors"]:
            self.assertIn("human_authored_sampled", entry)
            self.assertIn("commits_sampled", entry)
            self.assertGreater(entry["commits_sampled"], 0)
            self.assertGreater(entry["human_authored_sampled"], 0)

    def test_names_rate_limiting_and_the_token_when_unauthenticated(self):
        import urllib.error

        error = urllib.error.HTTPError(
            "https://api.github.com/search/issues", 403, "rate limit exceeded",
            {"X-RateLimit-Remaining": "0", "X-RateLimit-Reset": "1787529907"}, None,
        )
        message = self.rate_limit_message()("/search/issues", error, authenticated=False)
        self.assertIn("rate limit reached", message)
        self.assertIn("10 search requests", message)
        self.assertIn("GITHUB_TOKEN", message)

    def test_names_rate_limiting_differently_when_authenticated(self):
        import urllib.error

        error = urllib.error.HTTPError(
            "https://api.github.com/search/issues", 429, "too many requests",
            {"Retry-After": "42"}, None,
        )
        message = self.rate_limit_message()("/search/issues", error, authenticated=True)
        self.assertIn("retry after 42s", message)
        self.assertIn("30 search requests", message)
        self.assertNotIn("GITHUB_TOKEN", message)

    def test_reports_an_http_status_that_is_not_rate_limiting(self):
        import urllib.error

        error = urllib.error.HTTPError(
            "https://api.github.com/repos/x/y/contributors", 404, "Not Found", {}, None,
        )
        message = self.rate_limit_message()("/repos/x/y/contributors", error, True)
        self.assertIn("HTTP 404", message)
        self.assertIn("Not Found", message)
        self.assertNotIn("rate limit", message)

    def test_http_error_is_a_url_error_so_the_order_of_handlers_matters(self):
        """Pin the reason HTTPError is caught first; reordering silently loses the status."""
        import urllib.error

        self.assertTrue(issubclass(urllib.error.HTTPError, urllib.error.URLError))


class Rendering(RequiresSymbol, unittest.TestCase):
    """Both artefacts come from one computation, so they cannot disagree."""

    PAYLOAD = {
        "schema": "wildcat-contributors/v1",
        "repository": "wildcat-finance/skills",
        "contributors": [
            {"rank": 1, "login": "kethcode", "commits": 29, "merged_prs": 15,
             "human_authored_sampled": 20, "commits_sampled": 20},
            {"rank": 2, "login": "radup1337", "commits": 11, "merged_prs": 1,
             "human_authored_sampled": 11, "commits_sampled": 11},
        ],
        "excluded": [{"login": "laurenceday", "reason": "repository owner, excluded by decision"}],
        "issue_activity_without_ranked_commits": [],
    }
    README = "# Project\n\nSome prose.\n\n## Licence\n\nApache-2.0.\n"

    def root(self, readme=None):
        work = Path(tempfile.mkdtemp())
        self.addCleanup(lambda: __import__("shutil").rmtree(work, ignore_errors=True))
        (work / "README.md").write_text(self.README if readme is None else readme, encoding="utf-8")
        return work

    def test_readme_block_carries_handles_and_no_aggregate(self):
        """A login may contain digits, so `radup1337` is a handle and not a count.

        The check removes every handle first, then requires nothing numeric to
        survive. Banning digits outright would fail on a legitimate login, which
        is why the runbook's literal wording could not be implemented as written.
        """
        block = contributors.render_thanks(self.PAYLOAD)
        stripped = re.sub(r"@[A-Za-z0-9-]+", "", block)
        self.assertFalse(
            re.search(r"\d", stripped),
            f"numeric content survived handle removal: {stripped!r}",
        )
        # `#` is not in this list: `## Thanks` is a heading, not a rank column.
        for word in ("commits", "Commits", "Merged PRs", "rank", "| ---"):
            self.assertNotIn(word, block, f"{word!r} is aggregate data and must not be here")
        self.assertIn("@kethcode", block)
        self.assertIn("@radup1337", block)

    def test_readme_block_reads_as_a_sentence_for_one_two_and_none(self):
        one = dict(self.PAYLOAD, contributors=[self.PAYLOAD["contributors"][0]])
        self.assertIn("Thanks to @kethcode.", contributors.render_thanks(one))
        self.assertIn(
            "Thanks to @kethcode and @radup1337.", contributors.render_thanks(self.PAYLOAD)
        )
        empty = dict(self.PAYLOAD, contributors=[])
        self.assertIn("No external contributors", contributors.render_thanks(empty))

    def test_everything_outside_the_markers_is_returned_byte_for_byte(self):
        spliced = contributors.splice_thanks(
            self.README, contributors.render_thanks(self.PAYLOAD)
        )
        again = contributors.splice_thanks(
            spliced, contributors.render_thanks(dict(self.PAYLOAD, contributors=[]))
        )
        start = again.find(contributors.THANKS_START)
        end = again.find(contributors.THANKS_END) + len(contributors.THANKS_END)
        outside = again[:start] + again[end:]
        original_start = spliced.find(contributors.THANKS_START)
        original_end = spliced.find(contributors.THANKS_END) + len(contributors.THANKS_END)
        self.assertEqual(outside, spliced[:original_start] + spliced[original_end:])
        self.assertIn("Some prose.", again)
        self.assertIn("Apache-2.0.", again)

    def test_stops_on_one_marker_without_the_other(self):
        for broken in (
            self.README + "\n<!-- contributors:start -->\n",
            self.README + "\n<!-- contributors:end -->\n",
        ):
            with self.assertRaises(contributors.Stop) as caught:
                contributors.splice_thanks(broken, "block")
            self.assertIn("marker", str(caught.exception))

    def test_stops_on_markers_in_the_wrong_order(self):
        broken = self.README + "\n<!-- contributors:end -->\n<!-- contributors:start -->\n"
        with self.assertRaises(contributors.Stop) as caught:
            contributors.splice_thanks(broken, "block")
        self.assertIn("wrong order", str(caught.exception))

    def test_a_rerun_that_changed_nothing_produces_no_diff(self):
        root = self.root()
        contributors.write_artefacts(root, self.PAYLOAD)
        first = {
            name: (root / name).read_bytes()
            for name in (contributors.CONTRIBUTORS_PATH, contributors.README_PATH)
        }
        contributors.write_artefacts(root, self.PAYLOAD)
        for name, before in first.items():
            self.assertEqual(before, (root / name).read_bytes(), f"{name} changed on a no-op rerun")
        self.assertEqual(contributors.check_artefacts(root, self.PAYLOAD), [])

    def test_check_names_the_file_that_is_out_of_date(self):
        root = self.root()
        contributors.write_artefacts(root, self.PAYLOAD)
        (root / contributors.CONTRIBUTORS_PATH).write_text("tampered\n", encoding="utf-8")
        stale = contributors.check_artefacts(root, self.PAYLOAD)
        self.assertEqual(len(stale), 1)
        self.assertIn(contributors.CONTRIBUTORS_PATH, stale[0])

    def test_check_reports_an_absent_artefact_rather_than_crashing(self):
        root = self.root()
        stale = contributors.check_artefacts(root, self.PAYLOAD)
        self.assertTrue(any("is absent" in item for item in stale))

    def test_no_excluded_login_reaches_either_artefact(self):
        root = self.root()
        contributors.write_artefacts(root, self.PAYLOAD)
        for name in (contributors.CONTRIBUTORS_PATH, contributors.README_PATH):
            text = (root / name).read_text(encoding="utf-8")
            for login in sorted(contributors.EXCLUDED_MAINTAINERS | contributors.AGENT_LOGINS):
                self.assertNotIn(login, text, f"{login} reached {name}")

    def test_an_interrupted_write_leaves_the_original_intact(self):
        """atomic_write replaces or does nothing. It never truncates in place."""
        root = self.root()
        target = root / contributors.CONTRIBUTORS_PATH
        target.write_text("original content\n", encoding="utf-8")
        real_replace = os.replace

        def fail_replace(*args, **kwargs):
            raise OSError("interrupted")

        os.replace = fail_replace
        try:
            with self.assertRaises(OSError):
                contributors.atomic_write(target, "new content that must not land\n")
        finally:
            os.replace = real_replace
        self.assertEqual(target.read_text(encoding="utf-8"), "original content\n")
        leftovers = [p.name for p in root.iterdir() if p.name.startswith(".CONTRIBUTORS")]
        self.assertEqual(leftovers, [], f"temporary files left behind: {leftovers}")

    def test_a_failure_on_the_second_artefact_leaves_the_first_whole(self):
        root = self.root()
        real_write = contributors.atomic_write
        written = []

        def one_then_fail(path, text):
            if written:
                raise OSError("interrupted between artefacts")
            written.append(Path(path).name)
            real_write(path, text)

        contributors.atomic_write = one_then_fail
        try:
            with self.assertRaises(OSError):
                contributors.write_artefacts(root, self.PAYLOAD)
        finally:
            contributors.atomic_write = real_write
        first = root / written[0]
        self.assertTrue(first.is_file())
        self.assertEqual(
            first.read_text(encoding="utf-8"),
            contributors.rendered(root, self.PAYLOAD)[written[0]],
            "the artefact that was written is not whole",
        )
        stale = contributors.check_artefacts(root, self.PAYLOAD)
        self.assertTrue(stale, "--check must report the artefact that never landed")

    def test_replacing_a_tracked_file_does_not_narrow_its_mode(self):
        """git records only the executable bit, so a mode change leaves no diff."""
        root = self.root()
        readme = root / contributors.README_PATH
        os.chmod(readme, 0o644)
        contributors.write_artefacts(root, self.PAYLOAD)
        self.assertEqual(
            stat.S_IMODE(readme.stat().st_mode), 0o644, "README.md mode was changed by the write"
        )

    def test_a_new_artefact_is_created_world_readable(self):
        root = self.root()
        contributors.write_artefacts(root, self.PAYLOAD)
        mode = stat.S_IMODE((root / contributors.CONTRIBUTORS_PATH).stat().st_mode)
        self.assertEqual(mode, self.require("DEFAULT_FILE_MODE", "new artefacts get an ad-hoc mode"))
        self.assertTrue(mode & stat.S_IROTH, "a generated file nobody else can read is a defect")

    def test_an_unusual_existing_mode_is_preserved_rather_than_normalised(self):
        root = self.root()
        target = root / contributors.CONTRIBUTORS_PATH
        target.write_text("placeholder\n", encoding="utf-8")
        os.chmod(target, 0o640)
        contributors.atomic_write(target, "replaced\n")
        self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o640)

    def test_check_reports_an_absent_readme_as_a_stop(self):
        root = self.root()
        (root / contributors.README_PATH).unlink()
        self.assert_stops(
            lambda: contributors.check_artefacts(root, self.PAYLOAD),
            contributors.README_PATH,
        )

    def test_stops_on_a_readme_that_is_not_utf8(self):
        root = self.root()
        (root / contributors.README_PATH).write_bytes(b"\xff\xfe not text \x00")
        self.assert_stops(
            lambda: contributors.check_artefacts(root, self.PAYLOAD), "UTF-8"
        )

    def test_an_abandoned_temporary_is_swept_and_never_looks_like_a_change(self):
        """A hard-killed run leaves litter that a broad `git add` could commit."""
        root = self.root()
        sweep = self.require("sweep_orphans", "abandoned temporaries accumulate in the repository")
        orphan = root / f".{contributors.CONTRIBUTORS_PATH}.abandoned"
        orphan.write_text("half written\n", encoding="utf-8")
        bystander = root / "unrelated.md"
        bystander.write_text("keep me\n", encoding="utf-8")
        removed = sweep(root, [contributors.CONTRIBUTORS_PATH, contributors.README_PATH])
        self.assertEqual(removed, [orphan.name])
        self.assertFalse(orphan.exists())
        self.assertTrue(bystander.exists(), "the sweep must not touch anything else")

    def test_the_sweep_leaves_the_artefacts_themselves_alone(self):
        root = self.root()
        contributors.write_artefacts(root, self.PAYLOAD)
        before = (root / contributors.CONTRIBUTORS_PATH).read_bytes()
        self.require("sweep_orphans", "the sweep is gone")(
            root, [contributors.CONTRIBUTORS_PATH, contributors.README_PATH]
        )
        self.assertEqual(before, (root / contributors.CONTRIBUTORS_PATH).read_bytes())

    def test_the_temporary_pattern_is_gitignored(self):
        ignored = (REPOSITORY_ROOT / ".gitignore").read_text(encoding="utf-8")
        for pattern in (".CONTRIBUTORS.md.*", ".README.md.*"):
            self.assertIn(pattern, ignored, f"{pattern} must never be committed")


class WorkflowShape(unittest.TestCase):
    """The unattended trigger's shape, checked without PyYAML.

    PyYAML is not available to the root suite and every other root script is
    stdlib-only, so a full parse is out. What is checked is the handful of keys
    whose absence would be a real defect, read by indentation rather than by
    regex over the whole file.
    """

    WORKFLOW = REPOSITORY_ROOT / ".github/workflows/contributors.yml"

    @classmethod
    def setUpClass(cls):
        cls.text = cls.WORKFLOW.read_text(encoding="utf-8")
        cls.lines = cls.text.splitlines()

    def block(self, key):
        """Return the indented lines under a top-level mapping key."""
        collected, inside, indent = [], False, None
        for line in self.lines:
            if not inside:
                if line.startswith(f"{key}:"):
                    inside = True
                continue
            if line.strip() == "" or line.lstrip().startswith("#"):
                continue
            current = len(line) - len(line.lstrip())
            if indent is None:
                indent = current
            if current < indent:
                break
            collected.append(line.strip())
        return collected

    def test_the_workflow_exists(self):
        self.assertTrue(self.WORKFLOW.is_file(), f"{self.WORKFLOW} is absent")

    def test_permissions_are_exactly_the_two_writes_it_needs(self):
        self.assertEqual(
            sorted(self.block("permissions")),
            ["contents: write", "pull-requests: write"],
            "the workflow must hold no scope beyond what it uses",
        )

    def test_it_runs_weekly_and_on_demand(self):
        trigger = self.block("on")
        dispatch = [line for line in trigger if line.startswith("workflow_dispatch")]
        self.assertTrue(dispatch, "workflow_dispatch is missing, so it cannot be run on demand")
        crons = [line for line in trigger if line.startswith("- cron:")]
        self.assertEqual(len(crons), 1, f"expected exactly one schedule, got {crons}")
        fields = crons[0].split('"')[1].split()
        self.assertEqual(len(fields), 5, f"malformed cron: {crons[0]}")
        self.assertNotEqual(
            fields[4], "*", "a day-of-week of * is daily or hourly, not the weekly cadence asked for"
        )
        self.assertNotEqual(fields[2], "*/1", "not weekly")

    def test_it_is_guarded_to_the_canonical_repository(self):
        self.assertIn(
            "if: github.repository == 'wildcat-finance/skills'",
            self.text,
            "without the guard a fork's schedule opens pull requests",
        )

    def test_concurrency_is_grouped_so_two_runs_cannot_race(self):
        block = self.block("concurrency")
        self.assertTrue(any(line.startswith("group:") for line in block), block)

    def test_it_checks_before_it_writes(self):
        check_at = self.text.find("contributors.py --check")
        write_at = self.text.find("contributors.py --write")
        self.assertNotEqual(check_at, -1, "--check is never run, so it cannot skip a no-op")
        self.assertNotEqual(write_at, -1)
        self.assertLess(check_at, write_at, "--write must be gated behind --check")

    def test_a_non_staleness_exit_is_not_treated_as_a_change(self):
        """Exit 2 is a stop, not `the list needs updating`."""
        self.assertIn('if [ "$status" -ne 1 ]', self.text)

    def executable(self):
        """The workflow's lines with comments dropped.

        The comments deliberately name `git commit` to explain why it is not
        used, so a whole-file search for it would fail on the explanation rather
        than on a real call.
        """
        return "\n".join(
            line for line in self.lines if not line.lstrip().startswith("#")
        )

    def test_it_publishes_through_the_contents_api_not_a_git_commit(self):
        """Every branch here requires signed commits; an Actions git commit is not signed."""
        self.assertIn("contents/$path", self.text)
        body = self.executable()
        self.assertNotIn("git commit", body)
        self.assertNotIn("git push", body)

    def test_the_comments_still_explain_why_git_commit_is_avoided(self):
        """If the reason is deleted, the next person reinstates the broken approach."""
        comments = "\n".join(line for line in self.lines if line.lstrip().startswith("#"))
        self.assertIn("signed commits", comments)

    def test_it_refuses_to_open_a_second_pull_request_for_one_ranking(self):
        self.assertIn("--state open --json number --jq 'length'", self.text)

    def test_it_writes_a_summary_on_every_run_including_a_no_op(self):
        self.assertIn("GITHUB_STEP_SUMMARY", self.text)
        self.assertIn("if: always()", self.text)
        self.assertIn("A run that changes nothing is a success", self.text)

    def test_a_failed_run_is_not_reported_as_no_change(self):
        """The inverse of the signal requirement: a failure must not read as a clean no-op."""
        body = self.executable()
        status_at = body.find("job.status")
        changed_at = body.find("steps.decide.outputs.changed }}\" != \"true\"")
        self.assertNotEqual(status_at, -1, "the summary never checks whether the job failed")
        self.assertNotEqual(changed_at, -1)
        self.assertLess(
            status_at,
            changed_at,
            "job.status must be checked before the changed flag; otherwise an empty "
            "flag from a failed step reads as 'nothing changed'",
        )
        self.assertIn("This run failed", self.text)

    def test_the_generated_commit_names_what_generated_it(self):
        self.assertIn("Generated by .github/workflows/contributors.yml", self.text)
        self.assertIn("scripts/contributors.py --check", self.text)

    def test_the_generated_commit_claims_no_human_or_agent_authorship(self):
        """A cron job is not Shoggoth doing governed work, and must not say it is."""
        body = self.executable()
        self.assertNotIn("Co-authored-by", body)
        self.assertNotIn("Wildcat-Origin", body)

    def test_the_unattended_job_bounds_its_own_runtime(self):
        """A scheduled writer with no timeout can hold a runner for six hours."""
        timeouts = [line.strip() for line in self.lines if line.strip().startswith("timeout-minutes:")]
        self.assertEqual(len(timeouts), 1, f"expected exactly one timeout, got {timeouts}")
        minutes = int(timeouts[0].split(":", 1)[1])
        self.assertGreater(minutes, 0)
        self.assertLessEqual(minutes, 30, "a generous timeout is not a bound")

    TOP_LEVEL_KEYS = ("name:", "on:", "permissions:", "concurrency:", "jobs:")

    def test_no_line_sits_at_column_one_except_a_top_level_key(self):
        """The defect class that made this file unparseable once.

        A `run: |` block scalar ends at the first line indented less than the
        block. A shell continuation written at column 1 therefore terminates the
        block and YAML reads the remainder as new keys, so the workflow never
        runs and GitHub reports a syntax error instead. Every string and
        indentation test in this class passed while the file was invalid, which
        is why validity needs its own check rather than being assumed.
        """
        offenders = []
        for number, line in enumerate(self.lines, start=1):
            if not line or line[0] in " \t" or line.startswith("#"):
                continue
            if not line.startswith(self.TOP_LEVEL_KEYS):
                offenders.append(f"{number}: {line[:60]}")
        self.assertEqual(
            offenders,
            [],
            "lines at column one that are not top-level keys; these end a block "
            "scalar and make the workflow unparseable: " + "; ".join(offenders),
        )

    def test_a_multi_line_commit_message_is_built_without_unindented_lines(self):
        self.assertIn("message=$(printf", self.text)

    def test_it_holds_no_secret_beyond_the_job_token(self):
        self.assertNotIn("secrets.", self.text, "this workflow needs no repository secret")


class RankingDigest(RequiresSymbol, unittest.TestCase):
    """The unattended run reports a digest, so a no-op is legible."""

    def test_the_digest_covers_the_ranking_and_nothing_else(self):
        digest = self.require("ranking_digest", "the unattended summary has nothing to report")
        one = [{"login": "a", "commits": 2, "merged_prs": 1}]
        self.assertEqual(digest(one), digest([dict(one[0], human_authored_sampled=5)]))

    def test_the_digest_changes_when_the_ranking_changes(self):
        digest = self.require("ranking_digest", "the unattended summary has nothing to report")
        a = [{"login": "a", "commits": 2, "merged_prs": 1}]
        for changed in (
            [{"login": "b", "commits": 2, "merged_prs": 1}],
            [{"login": "a", "commits": 3, "merged_prs": 1}],
            [{"login": "a", "commits": 2, "merged_prs": 2}],
            list(a) + [{"login": "b", "commits": 1, "merged_prs": 0}],
        ):
            self.assertNotEqual(digest(a), digest(changed), changed)

    def test_order_matters_because_the_published_order_matters(self):
        digest = self.require("ranking_digest", "the unattended summary has nothing to report")
        a = [{"login": "a", "commits": 2, "merged_prs": 1},
             {"login": "b", "commits": 1, "merged_prs": 0}]
        self.assertNotEqual(digest(a), digest(list(reversed(a))))
