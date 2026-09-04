"""Contract and causal fixtures for the base-owned ADR assignment gate."""

from __future__ import annotations

import json
import os
from collections.abc import Callable
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import textwrap
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/adr-assignments.yml"
ALLOCATOR = (
    ROOT
    / "plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py"
)
PROOF = ROOT / "docs/adr-merge-assignment/local-proof.md"
CONTEXT = "adr-assignments"
ACTIONS_INTEGRATION_ID = 15368
RULESET_ID = 21830871


def clean_env(**overrides: str) -> dict[str, str]:
    environment = {
        name: value
        for name, value in os.environ.items()
        if not name.startswith("GIT_")
    }
    environment.update(overrides)
    return environment


def run(
    *arguments: str,
    cwd: Path,
    check: bool = True,
    input_bytes: bytes | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(  # phylax: allow subprocess: fixed test-only argv
        list(arguments),
        cwd=cwd,
        input=input_bytes,
        capture_output=True,
        check=False,
        env=clean_env() if env is None else env,
    )
    if check and result.returncode:
        raise AssertionError(
            f"{arguments!r} failed with {result.returncode}: "
            f"{result.stderr.decode('utf-8', 'replace')}"
        )
    return result


def git(cwd: Path, *arguments: str) -> str:
    return run("git", *arguments, cwd=cwd).stdout.decode("ascii").strip()


def write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def record(heading: str) -> str:
    return (
        f"{heading}\n\n"
        "## Status\n\nAccepted, 2026-09-02.\n\n"
        "## Context\n\nA bounded choice is required.\n\n"
        "## Decision\n\nKeep one stable identity.\n\n"
        "## Consequences\n\nReferences remain meaningful.\n\n"
        "## Alternatives considered\n\nEarly numbering was rejected.\n"
    )


def workflow_run_blocks(text: str) -> list[str]:
    """Return dedented literal shell bodies without YAML expressions."""
    lines = text.splitlines(keepends=True)
    blocks: list[str] = []
    index = 0
    while index < len(lines):
        if lines[index] != "        run: |\n":
            index += 1
            continue
        index += 1
        body: list[str] = []
        while index < len(lines):
            line = lines[index]
            if line.strip() and not line.startswith("          "):
                break
            body.append(line)
            index += 1
        blocks.append(textwrap.dedent("".join(body)))
    return blocks


def scratch_directory(prefix: str = "adr-assignment-workflow-"):
    """Keep fixture churn under the repository's ignored scratch anchor."""
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


class AssignmentRepository:
    """A complete local graph ending at ADR-060 with disposable candidates."""

    def __init__(self) -> None:
        self.temporary = scratch_directory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        self.source.mkdir()
        git(self.source, "init", "--quiet", "-b", "main")
        git(self.source, "config", "user.name", "Fixture")
        git(self.source, "config", "user.email", "fixture@example.invalid")
        git(self.source, "config", "commit.gpgsign", "false")
        write(self.source / ".gitignore", ".hexaemeron/\n")
        write(
            self.source / "docs/decisions/ADR-060-existing.md",
            record("# ADR-060: Existing"),
        )
        git(self.source, "add", ".")
        git(self.source, "commit", "--quiet", "-m", "base")
        self.base = git(self.source, "rev-parse", "HEAD")
        self.products: dict[str, str] = {}
        self.reports: dict[str, Path] = {}

    def close(self) -> None:
        self.temporary.cleanup()

    def product(
        self,
        slug: str,
        *,
        start: str | None = None,
        hostile_sentinel: Path | None = None,
    ) -> str:
        branch = f"product-{slug}"
        git(self.source, "checkout", "--quiet", "-B", branch, start or self.base)
        write(
            self.source / f"docs/decisions/drafts/{slug}.md",
            record(f"# Decision: {slug.replace('-', ' ').title()}"),
        )
        if hostile_sentinel is not None:
            write(self.source / ".gitattributes", "* filter=hostile\n")
            write(
                self.source / "candidate-trigger.sh",
                f"#!/bin/sh\ntouch {shlex.quote(str(hostile_sentinel))}\n",
            )
            os.chmod(self.source / "candidate-trigger.sh", 0o755)
        git(self.source, "add", ".")
        git(self.source, "commit", "--quiet", "-m", f"product {slug}")
        product = git(self.source, "rev-parse", "HEAD")
        self.products[slug] = product
        return product

    def plan(self, slug: str, *, base: str | None = None) -> dict[str, object]:
        report = Path(f".hexaemeron/{slug}.json")
        result = run(
            "python3",
            str(ALLOCATOR),
            "plan",
            "--repo",
            str(self.source),
            "--base",
            base or self.base,
            "--base-ref",
            "refs/heads/main",
            "--product",
            self.products[slug],
            "--report",
            report.as_posix(),
            cwd=ROOT,
        )
        self.assert_success(result)
        self.reports[slug] = report
        return json.loads((self.source / report).read_text(encoding="ascii"))

    @staticmethod
    def assert_success(result: subprocess.CompletedProcess[bytes]) -> None:
        if result.returncode:
            raise AssertionError(result.stderr.decode("utf-8", "replace"))

    def assignment(
        self,
        slug: str,
        *,
        message: str | None = None,
        parents: tuple[str, ...] | None = None,
    ) -> str:
        report = json.loads(
            (self.source / self.reports[slug]).read_text(encoding="ascii")
        )
        rows = report["mappings"]
        trailers = [f"ADR-Assignment-Base: {report['base']}"]
        trailers.extend(
            f"ADR-Assignment: {row['identity']}=ADR-{row['number_text']}"
            for row in rows
        )
        body = message or "\n".join(["Assign decision record", "", *trailers])
        git(self.source, "checkout", "--quiet", "--detach", self.products[slug])
        applied = run(
            "python3",
            str(ALLOCATOR),
            "apply",
            "--repo",
            str(self.source),
            "--report",
            self.reports[slug].as_posix(),
            cwd=ROOT,
            check=False,
        )
        self.assert_success(applied)
        git(self.source, "add", "-A")
        tree = git(self.source, "write-tree")
        if tree != report["result_tree"]:
            raise AssertionError("fixture apply did not reproduce the report tree")
        arguments = ["commit-tree", tree]
        for parent in parents or (self.products[slug],):
            arguments.extend(("-p", parent))
        arguments.extend(("-m", body))
        candidate = git(self.source, *arguments)
        git(self.source, "update-ref", f"refs/heads/assignment-{slug}", candidate)
        git(self.source, "reset", "--quiet", "--hard", self.products[slug])
        return candidate

    def unnumbered_sync(self, slug: str) -> tuple[str, str]:
        """Make the unnumbered sibling used by Fiat's two-parent sync form."""
        first_parent = self.products[slug]
        tree = git(self.source, "rev-parse", f"{first_parent}^{{tree}}")
        product = git(
            self.source,
            "commit-tree",
            tree,
            "-p",
            first_parent,
            "-p",
            self.base,
            "-m",
            "unnumbered sync",
        )
        self.products[slug] = product
        return first_parent, product

    def replay(self, slug: str, *, allocator: Path = ALLOCATOR):
        return run(
            "python3",
            str(allocator),
            "replay",
            "--repo",
            str(self.source),
            "--report",
            self.reports[slug].as_posix(),
            cwd=ROOT,
            check=False,
        )

    def remote(self, head: str, *, main: str | None = None) -> Path:
        bare = self.root / "remote.git"
        if bare.exists():
            shutil.rmtree(bare)
        git(self.root, "clone", "--quiet", "--bare", str(self.source), str(bare))
        git(bare, "update-ref", "refs/heads/main", main or self.base)
        git(bare, "update-ref", "refs/pull/1/head", head)
        return bare


def evaluate_workflow(
    remote: Path,
    *,
    base: str,
    head: str,
    preexisting: str | None = None,
    home: Path | None = None,
    mutate: Callable[[str], str] | None = None,
) -> tuple[subprocess.CompletedProcess[bytes], str, str]:
    """Run the evaluate step's literal shell against a disposable remote.

    ``home`` stands in for the runner's own account; ``mutate`` rewrites the
    extracted block so a guard can be removed from a disposable copy and
    shown to be causal.
    """
    text = WORKFLOW.read_text(encoding="utf-8")
    blocks = workflow_run_blocks(text)
    block = next(body for body in blocks if "candidate_repository=" in body)
    block = block.replace(
        "https://github.com/wildcat-finance/skills.git",
        remote.as_uri(),
    ).replace("protocol.file.allow=never", "protocol.file.allow=always")
    if mutate is not None:
        mutated = mutate(block)
        if mutated == block:
            raise AssertionError("mutation fixture changed nothing")
        block = mutated
    with scratch_directory(prefix="adr-assignment-run-") as directory:
        temporary = Path(directory)
        output = temporary / "output"
        summary = temporary / "summary"
        output.touch()
        summary.touch()
        if preexisting is not None:
            target = temporary / f"adr-assignments-{preexisting}"
            target.symlink_to(temporary / "not-created", target_is_directory=True)
        environment = clean_env(
            BASE_SHA=base,
            HEAD_SHA=head,
            PR_NUMBER="1",
            RUNNER_TEMP=str(temporary),
            GITHUB_OUTPUT=str(output),
            GITHUB_STEP_SUMMARY=str(summary),
            PATH=os.environ["PATH"],
            **({} if home is None else {"HOME": str(home)}),
        )
        result = run(
            "bash",
            "-c",
            block,
            cwd=ROOT,
            check=False,
            env=environment,
        )
        return (
            result,
            output.read_text(encoding="utf-8"),
            summary.read_text(encoding="utf-8"),
        )


def object_count(repository: Path, *revisions: str) -> int:
    listed = git(repository, "rev-list", "--objects", *revisions)
    return len(listed.splitlines()) if listed else 0


def hostile_home(root: Path, sentinel: Path) -> Path:
    """A runner account whose global Git configuration routes every hook."""
    home = root / "hostile-home"
    hooks = root / "hostile-hooks"
    hooks.mkdir()
    for name in ("reference-transaction", "post-index-change"):
        hook = hooks / name
        hook.write_text(
            f"#!/bin/sh\ntouch {shlex.quote(str(sentinel))}\n", encoding="utf-8"
        )
        os.chmod(hook, 0o755)
    home.mkdir()
    (home / ".gitconfig").write_text(
        f"[core]\n\thooksPath = {hooks}\n", encoding="utf-8"
    )
    return home


def strip_runner_isolation(block: str) -> str:
    """Remove the three guards that keep the runner's own Git state inert."""
    return (
        block.replace('HOME="$safe_home" \\\n', 'HOME="$HOME" \\\n')
        .replace("GIT_CONFIG_GLOBAL=/dev/null \\\n", "")
        .replace("-c core.hooksPath=/dev/null \\\n", "")
    )


def external_gate_qualified(
    statuses: list[dict[str, object]],
    required_checks: list[dict[str, object]],
    *,
    head: str,
) -> bool:
    """Model the later readback without claiming that Step 4 performs it."""
    matching_status = any(
        row.get("context") == CONTEXT
        and row.get("sha") == head
        and row.get("state") == "success"
        for row in statuses
    )
    matching_requirement = any(
        row == {"context": CONTEXT, "integration_id": ACTIONS_INTEGRATION_ID}
        for row in required_checks
    )
    return matching_status and matching_requirement


class StaleBaseRegressionTests(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.repo = AssignmentRepository()

    def tearDown(self) -> None:
        self.repo.close()

    def test_two_candidates_recompute_after_one_advances_main(self):
        self.repo.product("alpha-choice")
        alpha = self.repo.plan("alpha-choice")
        alpha_head = self.repo.assignment("alpha-choice")
        self.repo.product("beta-choice")
        beta = self.repo.plan("beta-choice")
        self.assertEqual(alpha["mappings"][0]["number"], 61)
        self.assertEqual(beta["mappings"][0]["number"], 61)

        git(self.repo.source, "update-ref", "refs/heads/main", alpha_head)
        stale = self.repo.replay("beta-choice")
        self.assertEqual(stale.returncode, 2)
        self.assertEqual(json.loads(stale.stderr)["code"], "base-moved")

        self.repo.product("beta-choice", start=alpha_head)
        rebuilt = self.repo.plan("beta-choice", base=alpha_head)
        self.assertEqual(rebuilt["mappings"][0]["number"], 62)

    def test_removing_the_base_comparison_revives_the_stale_report(self):
        self.repo.product("beta-choice")
        self.repo.plan("beta-choice")
        self.repo.product("alpha-choice")
        self.repo.plan("alpha-choice")
        alpha_head = self.repo.assignment("alpha-choice")
        git(self.repo.source, "update-ref", "refs/heads/main", alpha_head)
        self.assertEqual(self.repo.replay("beta-choice").returncode, 2)

        source = ALLOCATOR.read_text(encoding="utf-8")
        needle = "    verify_base_ref(repo, base_ref, base)\n"
        self.assertGreaterEqual(source.count(needle), 2)
        mutated = self.repo.root / "decision_assignments_without_base_guard.py"
        mutated.write_text(source.replace(needle, "    pass  # mutation fixture\n"), encoding="utf-8")
        revived = self.repo.replay("beta-choice", allocator=mutated)
        self.assertEqual(
            revived.returncode,
            0,
            revived.stderr.decode("utf-8", "replace"),
        )


class WorkflowContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.blocks = workflow_run_blocks(cls.text)
        cls.shell = "".join(cls.blocks)
        cls.evaluate = next(
            body for body in cls.blocks if "candidate_repository=" in body
        )

    def test_trigger_job_and_context_are_stable(self):
        self.assertIn("name: adr-assignments\n", self.text)
        self.assertRegex(self.text, r"(?m)^  pull_request_target:$")
        self.assertNotRegex(self.text, r"(?m)^  pull_request:$")
        self.assertNotIn("paths:", self.text)
        self.assertRegex(self.text, r"(?m)^  adr-assignments:$")

    def test_permissions_are_least_privilege(self):
        block = self.text.split("permissions:\n", 1)[1].split("\njobs:\n", 1)[0]
        self.assertEqual(block.strip(), "contents: read\n  statuses: write")
        self.assertEqual(block.casefold().count(": write"), 1)
        self.assertNotIn("secrets.", self.text)
        self.assertIn("persist-credentials: false", self.text)

    def test_status_is_pending_then_terminal_on_only_the_exact_head(self):
        endpoint = '"repos/wildcat-finance/skills/statuses/$HEAD_SHA"'
        self.assertEqual(self.shell.count(endpoint), 2)
        self.assertEqual(self.shell.count("-f context=adr-assignments"), 2)
        self.assertIn("-f state=pending", self.shell)
        self.assertIn("state=failure", self.shell)
        self.assertIn("if: ${{ always() }}", self.text)
        self.assertNotIn("continue-on-error", self.text)

    def test_only_the_exact_base_policy_is_checked_out(self):
        self.assertEqual(self.text.count("uses: actions/checkout@v4"), 1)
        self.assertIn("ref: ${{ github.event.pull_request.base.sha }}", self.text)
        self.assertNotIn("github.event.pull_request.head.sha }}\n          path:", self.text)
        for block in self.blocks:
            self.assertNotIn("${{", block)

    def test_candidate_objects_enter_only_a_fresh_bare_repository(self):
        self.assertIn('git init --quiet --bare --template= "$candidate_repository"', self.evaluate)
        self.assertIn("https://github.com/wildcat-finance/skills.git", self.evaluate)
        self.assertIn("refs/pull/${PR_NUMBER}/head", self.evaluate)
        for forbidden in (
            "git checkout",
            "git clone",
            "pip install",
            "npm ",
            "make ",
            "candidate-trigger.sh",
        ):
            self.assertNotIn(forbidden, self.evaluate)

    def test_git_configuration_hooks_aliases_and_transports_are_closed(self):
        for guard in (
            "GIT_CONFIG_NOSYSTEM=1",
            "GIT_CONFIG_GLOBAL=/dev/null",
            "GIT_ATTR_NOSYSTEM=1",
            "GIT_TERMINAL_PROMPT=0",
            "core.hooksPath=/dev/null",
            "protocol.allow=never",
            "protocol.https.allow=always",
            "protocol.file.allow=never",
            "protocol.ext.allow=never",
        ):
            self.assertIn(guard, self.evaluate)

    def test_history_objects_reports_and_output_are_bounded(self):
        for ceiling in (
            'test "$object_count" -le 50000',
            'test "$object_bytes" -le 268435456',
            'test "$commit_count" -le 2048',
            'test "$delta_bytes" -le 262144',
            'test "$message_bytes" -le 65536',
        ):
            self.assertIn(ceiling, self.evaluate)
        self.assertIn("timeout-minutes: 10", self.text)
        self.assertNotIn("cat $", self.evaluate)

    def test_object_ceilings_bound_the_candidate_delta_not_the_base_history(self):
        self.assertIn(
            'rev-list --objects \\\n  "$BASE_SHA..$HEAD_SHA" | cut', self.evaluate
        )
        self.assertNotIn("rev-list --objects --all", self.evaluate)
        self.assertNotIn("du -sk", self.evaluate)

    def test_report_is_planned_replayed_and_bound_to_head_tree_and_trailers(self):
        self.assertIn("decision_assignments.py", self.evaluate)
        self.assertIn('"plan"', self.evaluate)
        self.assertIn('"replay"', self.evaluate)
        self.assertIn('report["result_tree"] != head_tree', self.evaluate)
        self.assertIn("candidate trailers do not match", self.evaluate)
        self.assertIn("final decision paths do not match", self.evaluate)

    def test_base_and_head_refs_are_reread_after_evidence_collection(self):
        self.assertGreaterEqual(self.evaluate.count("refs/heads/main"), 3)
        self.assertGreaterEqual(self.evaluate.count("refs/pull/${PR_NUMBER}/head"), 2)
        self.assertIn("stale-base", self.evaluate)
        self.assertIn("head-moved", self.evaluate)
        self.assertIn("ls-remote", self.evaluate)

    def test_python_runtime_is_pinned_from_the_base(self):
        self.assertIn('python-version-file: ".python-version"', self.text)
        self.assertNotRegex(self.text, r"(?m)^\s+python-version:")


class WorkflowExecutionTests(unittest.TestCase):
    def setUp(self) -> None:
        (ROOT / "tmp").mkdir(exist_ok=True)
        self.repo = AssignmentRepository()

    def tearDown(self) -> None:
        self.repo.close()

    def test_safe_assignment_accepts_while_candidate_script_and_filter_stay_inert(self):
        sentinel = self.repo.root / "candidate-executed"
        self.repo.product("safe-choice", hostile_sentinel=sentinel)
        self.repo.plan("safe-choice")
        candidate = self.repo.assignment("safe-choice")
        remote = self.repo.remote(candidate)
        git(
            remote,
            "config",
            "filter.hostile.clean",
            shlex.join(["sh", "-c", f"touch {shlex.quote(str(sentinel))}; cat"]),
        )
        result, output, summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertFalse(sentinel.exists())
        self.assertIn("mapping_count=1", output)
        self.assertIn("adr/safe-choice=ADR-061", summary)

    def test_runner_global_hooks_stay_inert_and_the_isolation_is_causal(self):
        sentinel = self.repo.root / "hook-executed"
        home = hostile_home(self.repo.root, sentinel)
        self.repo.product("safe-choice")
        self.repo.plan("safe-choice")
        candidate = self.repo.assignment("safe-choice")
        remote = self.repo.remote(candidate)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate, home=home
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn("mapping_count=1", output)
        self.assertFalse(sentinel.exists())

        evaluate_workflow(
            remote,
            base=self.repo.base,
            head=candidate,
            home=home,
            mutate=strip_runner_isolation,
        )
        self.assertTrue(sentinel.exists())

    def test_object_ceiling_admits_a_candidate_whose_base_history_exceeds_it(self):
        self.repo.product("alpha-choice")
        self.repo.plan("alpha-choice")
        candidate = self.repo.assignment("alpha-choice")
        remote = self.repo.remote(candidate)
        delta = object_count(remote, f"{self.repo.base}..{candidate}")
        whole = object_count(remote, "--all")
        self.assertGreater(delta, 1)
        self.assertGreater(whole, delta)

        def lower(ceiling: int) -> Callable[[str], str]:
            return lambda block: block.replace(
                'test "$object_count" -le 50000', f'test "$object_count" -le {ceiling}'
            )

        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate, mutate=lower(delta)
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn("mapping_count=1", output)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate, mutate=lower(delta - 1)
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("reason=object-limit", output)

    def test_active_two_parent_assignment_sync_is_accepted(self):
        self.repo.product("sync-choice")
        first_parent, _unnumbered = self.repo.unnumbered_sync("sync-choice")
        self.repo.plan("sync-choice")
        candidate = self.repo.assignment(
            "sync-choice", parents=(first_parent, self.repo.base)
        )
        remote = self.repo.remote(candidate)
        result, output, summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertIn("mapping_count=1", output)
        self.assertIn("adr/sync-choice=ADR-061", summary)

    def test_stale_base_is_a_fixed_refusal(self):
        self.repo.product("alpha-choice")
        self.repo.plan("alpha-choice")
        first = self.repo.assignment("alpha-choice")
        self.repo.product("beta-choice")
        self.repo.plan("beta-choice")
        second = self.repo.assignment("beta-choice")
        remote = self.repo.remote(second, main=first)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=second
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("reason=stale-base", output)

    def test_moved_head_is_a_fixed_refusal(self):
        self.repo.product("alpha-choice")
        self.repo.plan("alpha-choice")
        expected = self.repo.assignment("alpha-choice")
        moved = git(
            self.repo.source,
            "commit-tree",
            f"{expected}^{{tree}}",
            "-p",
            self.repo.products["alpha-choice"],
            "-m",
            "different head",
        )
        remote = self.repo.remote(moved)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=expected
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("reason=head-moved", output)

    def test_malformed_assignment_trailers_refuse(self):
        self.repo.product("alpha-choice")
        self.repo.plan("alpha-choice")
        candidate = self.repo.assignment(
            "alpha-choice", message="Assign without evidence trailers"
        )
        remote = self.repo.remote(candidate)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("reason=assignment-evidence", output)

    def test_malformed_final_path_is_a_fixed_refusal(self):
        self.repo.product("alpha-choice")
        write(
            self.repo.source / "docs/decisions/ADR-061-Upper.md",
            record("# ADR-061: Upper"),
        )
        git(self.repo.source, "add", ".")
        git(self.repo.source, "commit", "--quiet", "-m", "malformed final")
        candidate = git(self.repo.source, "rev-parse", "HEAD")
        remote = self.repo.remote(candidate)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("reason=path-shape", output)

    def test_non_decision_change_has_no_assignment(self):
        write(self.repo.source / "README.md", "A repository change.\n")
        git(self.repo.source, "add", "README.md")
        git(self.repo.source, "commit", "--quiet", "-m", "non-decision change")
        candidate = git(self.repo.source, "rev-parse", "HEAD")
        remote = self.repo.remote(candidate)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("mapping_count=0", output)

    def test_preexisting_repository_symlink_is_a_fixed_refusal(self):
        write(self.repo.source / "README.md", "A repository change.\n")
        git(self.repo.source, "add", "README.md")
        git(self.repo.source, "commit", "--quiet", "-m", "non-decision change")
        candidate = git(self.repo.source, "rev-parse", "HEAD")
        remote = self.repo.remote(candidate)
        result, output, _summary = evaluate_workflow(
            remote,
            base=self.repo.base,
            head=candidate,
            preexisting="candidate.git",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("reason=workspace-state", output)

    def test_assignment_trailers_must_be_the_terminal_block(self):
        self.repo.product("alpha-choice")
        report = self.repo.plan("alpha-choice")
        trailers = [f"ADR-Assignment-Base: {report['base']}"]
        trailers.extend(
            f"ADR-Assignment: {row['identity']}=ADR-{row['number_text']}"
            for row in report["mappings"]
        )
        candidate = self.repo.assignment(
            "alpha-choice",
            message="Assign decision\n\n"
            + "\n".join(trailers)
            + "\npostscript",
        )
        remote = self.repo.remote(candidate)
        result, output, _summary = evaluate_workflow(
            remote, base=self.repo.base, head=candidate
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("reason=assignment-evidence", output)


class QualificationAndProofTests(unittest.TestCase):
    def test_wrong_integration_id_and_missing_status_do_not_qualify(self):
        head = "1" * 40
        status = [{"context": CONTEXT, "sha": head, "state": "success"}]
        self.assertFalse(external_gate_qualified([], [], head=head))
        self.assertFalse(
            external_gate_qualified(
                status,
                [{"context": CONTEXT, "integration_id": 999}],
                head=head,
            )
        )
        self.assertTrue(
            external_gate_qualified(
                status,
                [{"context": CONTEXT, "integration_id": ACTIONS_INTEGRATION_ID}],
                head=head,
            )
        )

    def test_local_proof_keeps_the_bootstrap_qualification(self):
        text = PROOF.read_text(encoding="utf-8")
        self.assertIn(f"ruleset `{RULESET_ID}`", text)
        self.assertIn("`evaluate`", text)
        self.assertIn("not required", text)
        self.assertIn(f"integration `{ACTIONS_INTEGRATION_ID}`", text)
        self.assertIn(
            "production race freedom is not claimed",
            " ".join(text.casefold().split()),
        )
        # The live ruleset has strict up-to-date checks off; the later
        # operation must turn them on, because no event re-evaluates a head
        # when main moves under it.
        self.assertIn("strict up-to-date checks off", text)
        self.assertIn("turn strict up-to-date checks on", text)
        self.assertNotIn("retain strict", text)
        self.assertIn("adr/assign-adr-numbers-at-merge-not-at-authoring", text)
        self.assertIn("hypomnema/EVOLUTION.md", text)
        self.assertIn("fiat/EVOLUTION.md", text)


if __name__ == "__main__":
    unittest.main()
