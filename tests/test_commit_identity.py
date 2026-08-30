"""Contract tests for the base-owned pull-request identity gate."""

from __future__ import annotations

from contextlib import contextmanager, redirect_stdout
import importlib.util
from io import StringIO
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
POLICY_PATH = SCRIPTS / "check_commit_identity.py"
HEXCTL_PATH = (
    ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
)
WORKFLOW = ROOT / ".github/workflows/identity.yml"
STUDY = ROOT / "docs/pr-identity-gate/study.md"
RUNBOOK = ROOT / "docs/pr-identity-gate/runbook.md"
ADR = ROOT / "docs/decisions/ADR-058-require-base-owned-identity-and-human-review.md"


def load_module(name: str, path: Path):
    scripts = str(SCRIPTS)
    sys.path.insert(0, scripts)
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        sys.path.remove(scripts)


def workflow_run_blocks(text: str) -> list[str]:
    """Return only literal shell bodies, excluding surrounding expressions."""
    lines = text.splitlines(keepends=True)
    blocks = []
    index = 0
    while index < len(lines):
        if lines[index] != "        run: |\n":
            index += 1
            continue
        index += 1
        body = []
        while index < len(lines):
            line = lines[index]
            if line.strip() and not line.startswith("          "):
                break
            body.append(line)
            index += 1
        blocks.append("".join(body))
    return blocks


policy = load_module("commit_identity_under_test", POLICY_PATH)
contributors = load_module("contributors_under_test", SCRIPTS / "contributors.py")
hexctl = load_module("hexctl_identity_policy_under_test", HEXCTL_PATH)


def run(*arguments: str, cwd: Path, input_bytes: bytes | None = None) -> str:
    completed = subprocess.run(
        list(arguments),
        cwd=cwd,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env={**os.environ, "LC_ALL": "C"},
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"{arguments!r} failed with {completed.returncode}: "
            f"{completed.stderr.decode(errors='replace')}"
        )
    return completed.stdout.decode().strip()


def commit(
    source: Path,
    *,
    author_name: str,
    author_email: str,
    committer_name: str,
    committer_email: str,
    message: str,
) -> str:
    environment = {
        **os.environ,
        "GIT_AUTHOR_NAME": author_name,
        "GIT_AUTHOR_EMAIL": author_email,
        "GIT_COMMITTER_NAME": committer_name,
        "GIT_COMMITTER_EMAIL": committer_email,
        "LC_ALL": "C",
    }
    completed = subprocess.run(
        [
            "git",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "--allow-empty",
            "-m",
            message,
        ],
        cwd=source,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=environment,
    )
    if completed.returncode != 0:
        raise AssertionError(completed.stderr.decode(errors="replace"))
    return run("git", "rev-parse", "HEAD", cwd=source)


HUMAN = {
    "author_name": "A Human",
    "author_email": "human@example.com",
    "committer_name": "A Human",
    "committer_email": "human@example.com",
    "message": "human change",
}
SHOGGOTH = {
    "author_name": "Shoggoth",
    "author_email": "shoggoth@wildcat.finance",
    "committer_name": "Laurence Day",
    "committer_email": "laurence@wildcat.finance",
    "message": (
        "governed change\n\n"
        "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>\n"
        "Wildcat-Origin: shoggoth"
    ),
}


@contextmanager
def candidate_repository(changes=(), *, base_change=None, shallow=False):
    temporary_root = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(dir=temporary_root) as directory:
        root = Path(directory)
        source = root / "source"
        bare = root / "candidate.git"
        source.mkdir()
        run("git", "init", "-b", "main", cwd=source)
        base = commit(source, **dict(HUMAN if base_change is None else base_change))
        head = base
        for change in changes:
            head = commit(source, **dict(change))
        clone_arguments = ["git", "clone", "--bare"]
        if shallow:
            clone_arguments.extend(["--depth", "1", source.as_uri()])
        else:
            clone_arguments.append(str(source))
        clone_arguments.append(str(bare))
        run(*clone_arguments, cwd=root)
        yield source, bare, base, head


class AcceptedIdentityTests(unittest.TestCase):
    def test_authorised_shoggoth_author_and_human_publisher_pass(self):
        with candidate_repository([SHOGGOTH]) as (_source, bare, base, head):
            result = policy.evaluate(str(bare), base, head, "laurenceday")
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["commit_count"], 1)
        self.assertEqual(result["shoggoth_author_count"], 1)
        self.assertEqual(result["human_author_count"], 0)

    def test_a_human_contributor_needs_no_shoggoth_trailer(self):
        with candidate_repository([HUMAN]) as (_source, bare, base, head):
            result = policy.evaluate(str(bare), base, head, "radup1337")
        self.assertEqual(result["human_author_count"], 1)
        self.assertEqual(result["shoggoth_author_count"], 0)

    def test_the_base_commit_is_not_reclassified_as_pull_request_work(self):
        base_host = dict(
            HUMAN,
            author_name="Claude",
            author_email="noreply@anthropic.com",
            committer_name="Claude",
            committer_email="noreply@anthropic.com",
        )
        with candidate_repository([HUMAN], base_change=base_host) as (
            _source,
            bare,
            base,
            head,
        ):
            result = policy.evaluate(str(bare), base, head, "radup1337")
        self.assertEqual(result["commit_count"], 1)

    def test_success_output_contains_no_address(self):
        with candidate_repository([SHOGGOTH]) as (_source, bare, base, head):
            output = StringIO()
            with redirect_stdout(output):
                exit_code = policy.main(
                    [
                        "--repository",
                        str(bare),
                        "--base",
                        base,
                        "--head",
                        head,
                        "--pull-request-login",
                        "laurenceday",
                    ]
                )
        self.assertEqual(exit_code, 0)
        self.assertNotIn("@", output.getvalue())
        self.assertIn('"schema":"wildcat-commit-identity-check/v1"', output.getvalue())


class RefusedIdentityTests(unittest.TestCase):
    def refusal(self, change, *, login="laurenceday", patch=None):
        with candidate_repository([change]) as (_source, bare, base, head):
            context = patch if patch is not None else mock.patch.object(
                policy, "COMMIT_COUNT_MAX", policy.COMMIT_COUNT_MAX
            )
            with context, self.assertRaises(policy.Refusal) as stopped:
                policy.evaluate(str(bare), base, head, login)
        return str(stopped.exception)

    def test_known_host_author_name_or_address_refuses(self):
        cases = (
            dict(HUMAN, author_name="Claude"),
            dict(HUMAN, author_email="noreply@anthropic.com"),
            dict(HUMAN, author_name="Codex"),
        )
        for change in cases:
            with self.subTest(change=change):
                self.assertIn("runtime host as author", self.refusal(change))

    def test_known_host_committer_refuses(self):
        change = dict(
            HUMAN,
            committer_name="Codex",
            committer_email="noreply@openai.com",
        )
        self.assertIn("runtime host as committer", self.refusal(change))

    def test_known_host_coauthor_refuses(self):
        change = dict(
            HUMAN,
            message=(
                "change\n\nCo-authored-by: Claude <noreply@anthropic.com>"
            ),
        )
        self.assertIn("runtime host as co-author", self.refusal(change))

    def test_known_host_generated_by_byline_refuses(self):
        change = dict(HUMAN, message="change\n\nGenerated with Claude Code")
        self.assertIn("generated-by byline", self.refusal(change))

    def test_known_host_pull_request_login_refuses(self):
        for login in sorted(
            policy.contributors.HOST_PR_LOGINS
            | policy.contributors.HOST_IDENTITY_NAMES
        ):
            with self.subTest(login=login):
                self.assertIn(
                    "runtime-host account", self.refusal(HUMAN, login=login)
                )

    def test_ambiguous_shoggoth_identity_refuses(self):
        change = dict(SHOGGOTH, author_email="other@example.com")
        self.assertIn("ambiguous Shoggoth author", self.refusal(change))

    def test_shoggoth_author_requires_each_exact_trailer_once(self):
        missing = dict(SHOGGOTH, message="governed change")
        duplicate = dict(
            SHOGGOTH,
            message=SHOGGOTH["message"] + "\nWildcat-Origin: shoggoth",
        )
        self.assertIn("co-author trailer", self.refusal(missing))
        self.assertIn("Wildcat-Origin trailer", self.refusal(duplicate))

    def test_an_offending_middle_commit_cannot_hide_behind_a_clean_head(self):
        host = dict(
            HUMAN,
            author_name="Claude",
            author_email="noreply@anthropic.com",
        )
        with candidate_repository([HUMAN, host, SHOGGOTH]) as (
            _source,
            bare,
            base,
            head,
        ):
            with self.assertRaisesRegex(policy.Refusal, "runtime host as author"):
                policy.evaluate(str(bare), base, head, "laurenceday")

    def test_a_head_that_does_not_contain_the_exact_base_refuses(self):
        with candidate_repository([HUMAN]) as (source, bare, base, head):
            run("git", "checkout", "--orphan", "unrelated", cwd=source)
            unrelated = commit(source, **dict(HUMAN, message="unrelated root"))
            run("git", f"--git-dir={bare}", "fetch", str(source), unrelated, cwd=source)
            with self.assertRaisesRegex(policy.Refusal, "does not contain the exact base"):
                policy.evaluate(str(bare), base, unrelated, "radup1337")
            self.assertNotEqual(head, unrelated)

    def test_a_shallow_candidate_repository_refuses(self):
        with candidate_repository([HUMAN], shallow=True) as (_source, bare, base, head):
            with self.assertRaisesRegex(policy.Refusal, "repository is shallow"):
                policy.evaluate(str(bare), base, head, "radup1337")

    def test_a_non_bare_repository_refuses(self):
        with candidate_repository([HUMAN]) as (source, _bare, base, head):
            with self.assertRaisesRegex(policy.Refusal, "repository is not bare"):
                policy.evaluate(str(source), base, head, "radup1337")

    def test_a_symlinked_repository_path_refuses(self):
        with candidate_repository([HUMAN]) as (source, bare, base, head):
            link = source.parent / "candidate-link"
            link.symlink_to(bare, target_is_directory=True)
            with self.assertRaisesRegex(policy.Refusal, "path contains a symlink"):
                policy.evaluate(str(link), base, head, "radup1337")

    def test_commit_count_object_and_total_byte_ceilings_refuse(self):
        with candidate_repository([HUMAN, HUMAN]) as (_source, bare, base, head):
            with mock.patch.object(policy, "COMMIT_COUNT_MAX", 1):
                with self.assertRaisesRegex(policy.Refusal, "exceeds 1 commits"):
                    policy.evaluate(str(bare), base, head, "radup1337")
        with candidate_repository([HUMAN]) as (_source, bare, base, head):
            with mock.patch.object(policy, "COMMIT_BYTES_MAX", 1):
                with self.assertRaisesRegex(policy.Refusal, "exceeds 1 bytes"):
                    policy.evaluate(str(bare), base, head, "radup1337")
            with mock.patch.object(policy, "COMMIT_TOTAL_BYTES_MAX", 1):
                with self.assertRaisesRegex(policy.Refusal, "objects exceed 1 bytes"):
                    policy.evaluate(str(bare), base, head, "radup1337")

    def test_a_malformed_author_object_refuses(self):
        with candidate_repository([]) as (source, _bare, base, _head):
            tree = run("git", "show", "-s", "--format=%T", base, cwd=source)
            raw = (
                f"tree {tree}\n"
                f"parent {base}\n"
                "author malformed\n"
                "committer A Human <human@example.com> 1 +0000\n\n"
                "malformed identity\n"
            ).encode()
            malformed = run(
                "git", "hash-object", "-t", "commit", "-w", "--stdin", "--literally",
                cwd=source,
                input_bytes=raw,
            )
            run("git", "update-ref", "refs/heads/main", malformed, cwd=source)
            bare = source.parent / "malformed.git"
            run("git", "clone", "--bare", str(source), str(bare), cwd=source.parent)
            with self.assertRaisesRegex(policy.Refusal, "malformed author identity"):
                policy.evaluate(str(bare), base, malformed, "radup1337")


class PolicyParityTests(unittest.TestCase):
    def test_host_sets_are_the_existing_fiat_and_contributor_sets(self):
        for name in (
            "HOST_IDENTITY_NAMES",
            "HOST_IDENTITY_EMAILS",
            "HOST_PR_LOGINS",
        ):
            self.assertEqual(
                getattr(policy.contributors, name), getattr(contributors, name)
            )
            self.assertEqual(
                getattr(policy.contributors, name), getattr(hexctl, name)
            )

    def test_message_and_login_grammars_match_fiat(self):
        self.assertEqual(policy.COAUTHOR_RE.pattern, hexctl.COAUTHOR_RE.pattern)
        self.assertEqual(policy.COAUTHOR_RE.flags, hexctl.COAUTHOR_RE.flags)
        self.assertEqual(policy.HOST_BYLINE_RE.pattern, hexctl.HOST_BYLINE_RE.pattern)
        self.assertEqual(policy.HOST_BYLINE_RE.flags, hexctl.HOST_BYLINE_RE.flags)
        self.assertEqual(policy.GITHUB_LOGIN_RE.pattern, hexctl.GITHUB_LOGIN_RE.pattern)
        self.assertEqual(policy.GITHUB_LOGIN_RE.flags, hexctl.GITHUB_LOGIN_RE.flags)

    def test_provenance_trailers_match_fiat(self):
        self.assertEqual(policy.COAUTHOR_TRAILER, hexctl.COAUTHOR_TRAILER)
        self.assertEqual(policy.ORIGIN_TRAILER, hexctl.ORIGIN_TRAILER)


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.run_blocks = workflow_run_blocks(cls.text)
        cls.run_block = "".join(cls.run_blocks)

    def test_job_and_trigger_are_unconditional_and_stable(self):
        self.assertIn("name: identity\n", self.text)
        self.assertRegex(self.text, r"(?m)^  pull_request_target:$")
        self.assertNotRegex(self.text, r"(?m)^  pull_request:$")
        self.assertNotIn("paths:", self.text)
        self.assertRegex(self.text, r"(?m)^  identity:$")
        self.assertIn("timeout-minutes: 5", self.text)

    def test_only_exact_head_status_publication_is_writable(self):
        permission_block = self.text.split("permissions:\n", 1)[1].split("\njobs:\n", 1)[0]
        self.assertEqual(
            permission_block.strip(),
            "contents: read\n  statuses: write",
        )
        self.assertEqual(permission_block.casefold().count(": write"), 1)
        self.assertNotIn("secrets.", self.text)
        self.assertNotIn("actions/cache", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_exact_head_status_is_pending_then_resolved_fail_closed(self):
        endpoint = '"repos/wildcat-finance/skills/statuses/$HEAD_SHA"'
        self.assertEqual(self.run_block.count(endpoint), 2)
        self.assertEqual(self.run_block.count("-f context=identity"), 2)
        self.assertIn("-f state=pending", self.run_block)
        self.assertIn("state=failure", self.run_block)
        self.assertIn('[ "$EVALUATION_OUTCOME" = "success" ]', self.run_block)
        self.assertIn("if: ${{ always() }}", self.text)
        self.assertIn(
            "EVALUATION_OUTCOME: ${{ steps.evaluate.outcome }}",
            self.text,
        )
        self.assertNotIn("continue-on-error", self.text)

    def test_only_the_exact_base_policy_is_checked_out(self):
        self.assertEqual(self.text.count("uses: actions/checkout@v4"), 1)
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", self.text)
        self.assertNotIn("path:", self.text)
        self.assertNotIn("github.event.pull_request.head.sha }}\n          path:", self.text)

    def test_candidate_is_bare_and_only_base_policy_executes(self):
        self.assertIn('git init --bare "$candidate_repository"', self.run_block)
        self.assertIn("https://github.com/wildcat-finance/skills.git", self.run_block)
        self.assertIn("refs/pull/${PR_NUMBER}/head", self.run_block)
        self.assertIn("python3 scripts/check_commit_identity.py", self.run_block)
        for forbidden in ("git checkout", "pip install", "npm ", "make ", "source "):
            self.assertNotIn(forbidden, self.run_block)

    def test_event_values_do_not_enter_shell_source(self):
        for block in self.run_blocks:
            self.assertNotIn("${{", block)
        for value in ("BASE_SHA", "HEAD_SHA", "PR_LOGIN", "PR_NUMBER"):
            self.assertIn(f"{value}: ${{{{ github.event.pull_request.", self.text)
        self.assertIn('""|*[!0-9]*)', self.run_block)
        self.assertIn('test "$fetched_head" = "$HEAD_SHA"', self.run_block)


class DurableRecordTests(unittest.TestCase):
    def test_study_runbook_and_decision_name_the_bootstrap_boundary(self):
        study = STUDY.read_text(encoding="utf-8")
        runbook = RUNBOOK.read_text(encoding="utf-8")
        decision = ADR.read_text(encoding="utf-8")
        for text in (study, runbook, decision):
            self.assertIn("base", text.casefold())
            self.assertIn("canary", text.casefold())
            self.assertIn("one approving review", text.casefold())
        self.assertIn(
            "Do not add `identity` to a ruleset in this step",
            " ".join(runbook.split()),
        )
        self.assertIn("candidate cannot rewrite the deciding policy", decision)


if __name__ == "__main__":
    unittest.main()
