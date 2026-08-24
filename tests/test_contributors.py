"""Hold the contributor generator's host-identity set equal to Fiat's.

ADR-016 names one mechanical set of runtime host identities and Fiat's
controller owns it. scripts/contributors.py keeps a copy so it stays a
standalone root script with no cross-plugin import. A copy that nothing checks
stops agreeing, so these tests read the frozensets straight out of hexctl.py's
syntax tree and compare them. Either side edited alone fails here.
"""

from __future__ import annotations

import json
from pathlib import Path
import re
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
