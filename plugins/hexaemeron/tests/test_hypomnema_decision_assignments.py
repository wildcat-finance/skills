"""Stable decision identities and merge-time number assignment are fail-closed.

The fixtures deliberately end at ADR-060 while leaving 026, 027, and 059
unused.  A hole-filling allocator therefore fails these guards even when it
looks locally collision-free.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
ASSIGN = ROOT / "plugins/hexaemeron/skills/hypomnema/scripts/decision_assignments.py"
HYPO = ROOT / "plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py"
FIXTURES = ROOT / "plugins/hexaemeron/tests/fixtures/hypomnema/decision-assignments"
BASE_FIXTURES = FIXTURES / "base"
DRAFT_FIXTURES = FIXTURES / "drafts"
PORTABLE_EVOLUTION = (
    ROOT
    / ".agents/skills/promise-machine/runtime/plugins/hexaemeron/skills/hypomnema/EVOLUTION.md"
)

ASSIGNMENT_SPEC = importlib.util.spec_from_file_location(
    "hypomnema_decision_assignments", ASSIGN
)
assignments = importlib.util.module_from_spec(ASSIGNMENT_SPEC)
sys.modules[ASSIGNMENT_SPEC.name] = assignments
ASSIGNMENT_SPEC.loader.exec_module(assignments)

GIT_ENV_NAMES = tuple(
    name for name in os.environ if name.startswith("GIT_")
)


def clean_env(**overrides: str) -> dict[str, str]:
    env = dict(os.environ)
    for name in GIT_ENV_NAMES:
        env.pop(name, None)
    env.update(overrides)
    return env


def run_git(repo: Path, *args: str, input_bytes: bytes | None = None) -> str:
    result = subprocess.run(  # phylax: allow subprocess: fixed test-only Git argv
        ["git", "-C", str(repo), *args],
        input=input_bytes,
        capture_output=True,
        env=clean_env(),
        check=False,
    )
    if result.returncode:
        raise AssertionError(
            f"git {' '.join(args)} failed: {result.stderr.decode('utf-8', 'replace')}"
        )
    return result.stdout.decode("ascii").strip()


def complete_record(heading: str) -> bytes:
    return (
        f"{heading}\n\n"
        "## Status\n\nAccepted, 2026-08-31.\n\n"
        "## Context\n\nA bounded choice is required.\n\n"
        "## Decision\n\nKeep one stable identity.\n\n"
        "## Consequences\n\nReferences remain meaningful.\n\n"
        "## Alternatives considered\n\nRenaming the identity was rejected.\n"
    ).encode("utf-8")


class Repository:
    def __init__(self, drafts: tuple[str, ...] = ("zeta-choice", "alpha-choice")):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name)
        run_git(self.path, "init", "-q")
        run_git(self.path, "config", "user.name", "Fixture")
        run_git(self.path, "config", "user.email", "fixture@example.invalid")
        run_git(self.path, "config", "commit.gpgsign", "false")
        run_git(self.path, "config", "core.autocrlf", "false")
        (self.path / ".gitignore").write_text(".hexaemeron/\n", encoding="utf-8")
        decisions = self.path / "docs/decisions"
        decisions.mkdir(parents=True)
        for source in sorted(BASE_FIXTURES.iterdir()):
            shutil.copyfile(source, decisions / source.name)
        run_git(self.path, "add", ".")
        run_git(self.path, "commit", "-q", "-m", "base")
        self.base = run_git(self.path, "rev-parse", "HEAD")
        self.base_ref = "refs/heads/integration-base"
        run_git(self.path, "update-ref", self.base_ref, self.base)

        draft_dir = decisions / "drafts"
        draft_dir.mkdir()
        for slug in drafts:
            source = DRAFT_FIXTURES / f"{slug}.md"
            target = draft_dir / f"{slug}.md"
            if source.is_file():
                shutil.copyfile(source, target)
            else:
                target.write_bytes(complete_record(f"# Decision: Choose {slug}"))
        if "alpha-choice" in drafts:
            os.chmod(draft_dir / "alpha-choice.md", 0o755)
        run_git(self.path, "add", ".")
        run_git(self.path, "commit", "-q", "--allow-empty", "-m", "product")
        self.product = run_git(self.path, "rev-parse", "HEAD")
        self.report = Path(".hexaemeron/decision-assignment.json")

    def close(self) -> None:
        self.temporary.cleanup()

    def commit_path(self, relative: str, content: bytes) -> None:
        target = self.path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        run_git(self.path, "add", "--", relative)
        run_git(self.path, "commit", "-q", "-m", "add specimen")
        self.product = run_git(self.path, "rev-parse", "HEAD")


def run_assignment(
    repo: Repository | Path,
    command: str,
    *,
    base: str | None = None,
    base_ref: str = "refs/heads/integration-base",
    product: str | None = None,
    report: str | None = None,
    hostile_env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[bytes]:
    path = repo.path if isinstance(repo, Repository) else repo
    argv = [sys.executable, str(ASSIGN), command, "--repo", str(path)]
    if base is not None:
        argv.extend(("--base", base))
        argv.extend(("--base-ref", base_ref))
    if product is not None:
        argv.extend(("--product", product))
    argv.extend(("--report", report or ".hexaemeron/decision-assignment.json"))
    env = clean_env()
    if hostile_env:
        env.update(hostile_env)
    return subprocess.run(  # phylax: allow subprocess: fixed script argv in tests
        argv, capture_output=True, env=env, check=False
    )


def payload(result: subprocess.CompletedProcess[bytes]) -> dict[str, object]:
    stream = result.stdout if result.returncode == 0 else result.stderr
    return json.loads(stream.decode("utf-8"))


class DecisionAssignments(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repository()

    def tearDown(self) -> None:
        self.repo.close()

    def plan(self) -> dict[str, object]:
        result = run_assignment(
            self.repo, "plan", base=self.repo.base, product=self.repo.product
        )
        self.assertEqual(
            result.returncode, 0, result.stderr.decode("utf-8", "replace")
        )
        return json.loads((self.repo.path / self.repo.report).read_text(encoding="utf-8"))

    def assert_refused(
        self, result: subprocess.CompletedProcess[bytes], code: str
    ) -> None:
        self.assertEqual(result.returncode, 2, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(payload(result).get("code"), code)

    def test_holes_are_ignored_and_multiple_drafts_sort_by_ascii_bytes(self):
        report = self.plan()
        self.assertEqual(report["schema"], "fiat-decision-assignments/v1")
        mappings = report["mappings"]
        self.assertEqual(
            [(row["slug"], row["number"]) for row in mappings],
            [("alpha-choice", 61), ("zeta-choice", 62)],
        )
        self.assertEqual(report["base"], self.repo.base)
        self.assertEqual(report["product"], self.repo.product)
        self.assertRegex(report["result_tree"], r"\A[0-9a-f]{40,64}\Z")
        self.assertEqual(
            report["limits"],
            {
                "max_adr_number": 999,
                "max_blob_bytes": 1048576,
                "max_drafts": 32,
                "max_git_input_bytes": 2097152,
                "max_git_output_bytes": 16777216,
                "max_git_seconds": 20,
                "max_heading_bytes": 4096,
                "max_path_bytes": 1024,
                "max_report_bytes": 262144,
                "max_report_depth": 16,
                "max_slug_bytes": 96,
                "max_tree_entries": 20000,
            },
        )

    def test_a_safe_legacy_numbered_suffix_remains_valid(self):
        report = self.plan()
        self.assertEqual(report["mappings"][0]["number"], 61)

    def test_apply_changes_only_the_path_and_exact_first_heading(self):
        report = self.plan()
        source = self.repo.path / "docs/decisions/drafts/alpha-choice.md"
        before = source.read_bytes()
        result = run_assignment(self.repo, "apply")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        target = self.repo.path / "docs/decisions/ADR-061-alpha-choice.md"
        self.assertFalse(source.exists())
        self.assertEqual(
            target.read_bytes(),
            b"# ADR-061: Choose alpha\n" + before.split(b"\n", 1)[1],
        )
        self.assertEqual(target.stat().st_mode & 0o111, 0o111)
        self.assertEqual(payload(result)["result_tree"], report["result_tree"])

    def test_plan_and_replay_emit_the_same_canonical_report(self):
        report = self.plan()
        raw = (self.repo.path / self.repo.report).read_bytes()
        expected = (
            json.dumps(report, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("ascii")
        self.assertEqual(raw, expected)
        result = run_assignment(self.repo, "replay")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
        self.assertEqual(payload(result)["result_tree"], report["result_tree"])

    def test_duplicate_draft_and_final_identity_is_refused(self):
        self.repo.commit_path(
            "docs/decisions/ADR-061-alpha-choice.md",
            complete_record("# ADR-061: Choose alpha"),
        )
        result = run_assignment(
            self.repo, "plan", base=self.repo.base, product=self.repo.product
        )
        self.assert_refused(result, "identity-duplicate")

    def test_hostile_slugs_are_refused(self):
        for slug in (
            "Uppercase",
            "caf\N{LATIN SMALL LETTER E WITH ACUTE}",
            "bad.name",
            "bad\nname",
            "a" * 97,
        ):
            with self.subTest(slug=repr(slug)):
                repo = Repository(drafts=())
                try:
                    repo.commit_path(
                        f"docs/decisions/drafts/{slug}.md",
                        complete_record("# Decision: Hostile"),
                    )
                    result = run_assignment(
                        repo, "plan", base=repo.base, product=repo.product
                    )
                    self.assert_refused(result, "slug-invalid")
                finally:
                    repo.close()

    def test_more_than_32_drafts_is_refused(self):
        repo = Repository(drafts=())
        try:
            for number in range(33):
                target = repo.path / f"docs/decisions/drafts/choice-{number:02d}.md"
                target.write_bytes(complete_record(f"# Decision: Choice {number:02d}"))
            run_git(repo.path, "add", ".")
            run_git(repo.path, "commit", "-q", "-m", "too many drafts")
            repo.product = run_git(repo.path, "rev-parse", "HEAD")
            result = run_assignment(repo, "plan", base=repo.base, product=repo.product)
            self.assert_refused(result, "draft-limit")
        finally:
            repo.close()

    def test_oversized_draft_is_refused(self):
        repo = Repository(drafts=())
        try:
            repo.commit_path(
                "docs/decisions/drafts/large-choice.md",
                b"# Decision: Large\n" + (b"x" * (1024 * 1024)),
            )
            result = run_assignment(repo, "plan", base=repo.base, product=repo.product)
            self.assert_refused(result, "blob-limit")
        finally:
            repo.close()

    def test_wrong_object_type_is_refused(self):
        blob = run_git(
            self.repo.path,
            "hash-object",
            "-w",
            "--stdin",
            input_bytes=b"not a commit",
        )
        result = run_assignment(
            self.repo, "plan", base=blob, product=self.repo.product
        )
        self.assert_refused(result, "object-type")

    def test_shallow_repository_is_refused_before_object_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            shallow = Path(directory) / "shallow"
            result = subprocess.run(  # phylax: allow subprocess: bounded local fixture
                [
                    "git", "clone", "-q", "--depth", "1",
                    self.repo.path.as_uri(), str(shallow),
                ],
                capture_output=True,
                env=clean_env(),
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))
            outcome = run_assignment(
                shallow,
                "plan",
                base=self.repo.base,
                product=self.repo.product,
            )
            self.assert_refused(outcome, "repository-shallow")

    def test_missing_blob_makes_the_product_commit_incomplete(self):
        self.repo.commit_path("other.bin", b"tracked but removed from the object store\n")
        row = run_git(self.repo.path, "ls-tree", self.repo.product, "--", "other.bin")
        blob = row.split()[2]
        loose = self.repo.path / ".git/objects" / blob[:2] / blob[2:]
        loose.unlink()
        result = run_assignment(
            self.repo, "plan", base=self.repo.base, product=self.repo.product
        )
        self.assert_refused(result, "object-incomplete")

    def test_a_moved_integration_base_ref_invalidates_replay(self):
        self.plan()
        run_git(self.repo.path, "update-ref", self.repo.base_ref, self.repo.product)
        result = run_assignment(self.repo, "replay")
        self.assert_refused(result, "base-moved")

    def test_replacement_objects_are_disabled(self):
        run_git(self.repo.path, "replace", self.repo.base, self.repo.product)
        report = self.plan()
        self.assertEqual(report["mappings"][0]["number"], 61)

    def test_grafts_cannot_make_an_unrelated_product_look_descended(self):
        tree = run_git(self.repo.path, "rev-parse", f"{self.repo.product}^{{tree}}")
        unrelated = run_git(self.repo.path, "commit-tree", tree, "-m", "unrelated")
        run_git(self.repo.path, "config", "advice.graftFileDeprecated", "false")
        (self.repo.path / ".git/info/grafts").write_text(
            f"{unrelated} {self.repo.base}\n", encoding="ascii"
        )
        result = run_assignment(
            self.repo, "plan", base=self.repo.base, product=unrelated
        )
        self.assert_refused(result, "repository-graft")

    def test_repointing_environment_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            result = run_assignment(
                self.repo,
                "plan",
                base=self.repo.base,
                product=self.repo.product,
                hostile_env={
                    "GIT_DIR": str(Path(directory) / "missing.git"),
                    "GIT_WORK_TREE": directory,
                    "GIT_OBJECT_DIRECTORY": str(Path(directory) / "objects"),
                },
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))

    def test_apply_refuses_a_configured_content_filter_without_executing_it(self):
        self.plan()
        sentinel = self.repo.path / "filter-ran"
        run_git(
            self.repo.path,
            "config",
            "filter.hostile.clean",
            f"touch {sentinel}",
        )
        (self.repo.path / ".git/info/attributes").write_text(
            "* filter=hostile\n", encoding="utf-8"
        )
        result = run_assignment(self.repo, "apply")
        self.assert_refused(result, "repository-filter")
        self.assertFalse(sentinel.exists())

    def test_apply_refuses_an_included_content_filter_without_executing_it(self):
        self.plan()
        sentinel = self.repo.path / "included-filter-ran"
        (self.repo.path / ".git/hostile-filter.config").write_text(
            "[filter \"hostile\"]\n"
            f"\tclean = touch {sentinel}\n",
            encoding="utf-8",
        )
        run_git(self.repo.path, "config", "include.path", "hostile-filter.config")
        (self.repo.path / ".git/info/attributes").write_text(
            "* filter=hostile\n", encoding="utf-8"
        )
        result = run_assignment(self.repo, "apply")
        self.assert_refused(result, "repository-filter")
        self.assertFalse(sentinel.exists())

    def test_apply_refuses_a_worktree_filter_without_executing_it(self):
        self.plan()
        sentinel = self.repo.path / "worktree-filter-ran"
        run_git(self.repo.path, "config", "extensions.worktreeConfig", "true")
        run_git(
            self.repo.path,
            "config",
            "--worktree",
            "filter.hostile.clean",
            f"touch {sentinel}",
        )
        (self.repo.path / ".git/info/attributes").write_text(
            "* filter=hostile\n", encoding="utf-8"
        )
        result = run_assignment(self.repo, "apply")
        self.assert_refused(result, "repository-filter")
        self.assertFalse(sentinel.exists())

    def test_git_input_and_output_are_drained_concurrently(self):
        oid = run_git(
            self.repo.path,
            "hash-object",
            "-w",
            "--stdin",
            input_bytes=b"bounded pipe fixture",
        )
        script = "\n".join((
            "import importlib.util",
            "from pathlib import Path",
            "import sys",
            f"spec = importlib.util.spec_from_file_location('assignment_pipe', {str(ASSIGN)!r})",
            "module = importlib.util.module_from_spec(spec)",
            "sys.modules[spec.name] = module",
            "spec.loader.exec_module(module)",
            f"repo = module.repository({str(self.repo.path)!r})",
            f"oid = {oid!r}",
            "request = (oid + '\\n').encode('ascii') * 10000",
            "status, output = module.bounded_git(",
            "    repo.root,",
            "    ['cat-file', '--batch-check=%(objectname) %(objecttype)'],",
            "    input_bytes=request,",
            ")",
            "expected = (oid + ' blob\\n').encode('ascii') * 10000",
            "raise SystemExit(0 if status == 0 and output == expected else 1)",
        ))
        try:
            result = subprocess.run(  # phylax: allow subprocess: bounded pipe child
                [sys.executable, "-c", script],
                capture_output=True,
                env=clean_env(),
                timeout=5,
                check=False,
            )
        except subprocess.TimeoutExpired:
            self.fail("bounded Git deadlocked while stdin and stdout pipes filled")
        self.assertEqual(result.returncode, 0, result.stderr.decode("utf-8", "replace"))

    def test_report_and_blob_drift_are_refused(self):
        for field in ("result_tree", "output_blob"):
            with self.subTest(field=field):
                report = self.plan()
                if field == "result_tree":
                    report[field] = "0" * len(report[field])
                else:
                    report["mappings"][0][field] = "0" * len(
                        report["mappings"][0][field]
                    )
                raw = json.dumps(
                    report, ensure_ascii=True, sort_keys=True, separators=(",", ":")
                ) + "\n"
                (self.repo.path / self.repo.report).write_text(raw, encoding="ascii")
                result = run_assignment(self.repo, "replay")
                self.assert_refused(result, "report-mismatch")

    def test_an_excessive_json_integer_is_a_bounded_refusal(self):
        self.plan()
        path = self.repo.path / self.repo.report
        raw = path.read_bytes().replace(b'"number":61', b'"number":' + b"9" * 5000)
        path.write_bytes(raw)
        result = run_assignment(self.repo, "replay")
        self.assert_refused(result, "report-json")

    def test_refusal_rolls_back_every_mapping(self):
        self.plan()
        first = self.repo.path / "docs/decisions/drafts/alpha-choice.md"
        second = self.repo.path / "docs/decisions/drafts/zeta-choice.md"
        first_before = first.read_bytes()
        second.write_bytes(second.read_bytes() + b"drift\n")
        second_before = second.read_bytes()
        result = run_assignment(self.repo, "apply")
        self.assert_refused(result, "worktree-dirty")
        self.assertEqual(first.read_bytes(), first_before)
        self.assertEqual(second.read_bytes(), second_before)
        self.assertFalse((self.repo.path / "docs/decisions/ADR-061-alpha-choice.md").exists())
        self.assertFalse((self.repo.path / "docs/decisions/ADR-062-zeta-choice.md").exists())

    def test_an_io_failure_after_the_first_install_restores_every_draft(self):
        report = self.plan()
        sources = [self.repo.path / row["draft_path"] for row in report["mappings"]]
        before = [source.read_bytes() for source in sources]
        repo = assignments.repository(str(self.repo.path))
        checked = assignments.checked_replay(repo, self.repo.path / self.repo.report)
        replace = os.replace
        calls = 0

        def fail_once(source, target):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise OSError("fixture failure")
            return replace(source, target)

        with mock.patch.object(assignments.os, "replace", side_effect=fail_once):
            with self.assertRaises(assignments.AssignmentError) as caught:
                assignments.apply_report(repo, checked)
        self.assertEqual(caught.exception.code, "apply-io")
        self.assertEqual([source.read_bytes() for source in sources], before)
        for row in report["mappings"]:
            self.assertFalse((self.repo.path / row["final_path"]).exists())

    def test_backup_cleanup_failure_restores_every_draft(self):
        report = self.plan()
        sources = [self.repo.path / row["draft_path"] for row in report["mappings"]]
        targets = [self.repo.path / row["final_path"] for row in report["mappings"]]
        before = [source.read_bytes() for source in sources]
        repo = assignments.repository(str(self.repo.path))
        checked = assignments.checked_replay(repo, self.repo.path / self.repo.report)
        path_type = type(self.repo.path)
        unlink = path_type.unlink
        backup_unlinks = 0

        def fail_second_backup(path, *args, **kwargs):
            nonlocal backup_unlinks
            if path.name.startswith(".hypomnema-backup-"):
                backup_unlinks += 1
                if backup_unlinks == 2:
                    raise OSError("backup cleanup fixture failure")
            return unlink(path, *args, **kwargs)

        with mock.patch.object(
            path_type, "unlink", autospec=True, side_effect=fail_second_backup
        ):
            with self.assertRaises(assignments.AssignmentError) as caught:
                assignments.apply_report(repo, checked)
        self.assertEqual(caught.exception.code, "apply-io")
        self.assertTrue(all(source.exists() for source in sources))
        self.assertEqual([source.read_bytes() for source in sources], before)
        self.assertFalse([target for target in targets if target.exists()])
        self.assertFalse(list((self.repo.path / "docs/decisions").rglob(".hypomnema-*")))

    def test_an_interrupted_install_restores_every_draft(self):
        report = self.plan()
        sources = [self.repo.path / row["draft_path"] for row in report["mappings"]]
        targets = [self.repo.path / row["final_path"] for row in report["mappings"]]
        before = [source.read_bytes() for source in sources]
        repo = assignments.repository(str(self.repo.path))
        checked = assignments.checked_replay(repo, self.repo.path / self.repo.report)
        replace = os.replace
        calls = 0

        def interrupt_fourth_replace(source, target):
            nonlocal calls
            calls += 1
            if calls == 4:
                raise KeyboardInterrupt
            return replace(source, target)

        with mock.patch.object(
            assignments.os, "replace", side_effect=interrupt_fourth_replace
        ):
            with self.assertRaises(KeyboardInterrupt):
                assignments.apply_report(repo, checked)
        self.assertTrue(all(source.exists() for source in sources))
        self.assertEqual([source.read_bytes() for source in sources], before)
        self.assertFalse([target for target in targets if target.exists()])
        self.assertFalse(list((self.repo.path / "docs/decisions").rglob(".hypomnema-*")))

    def test_a_non_exact_first_heading_is_refused(self):
        repo = Repository(drafts=())
        try:
            repo.commit_path(
                "docs/decisions/drafts/late-heading.md",
                b"intro\n# Decision: Too late\n",
            )
            result = run_assignment(repo, "plan", base=repo.base, product=repo.product)
            self.assert_refused(result, "heading-invalid")
        finally:
            repo.close()

    def test_a_product_outside_the_base_ancestry_is_refused(self):
        tree = run_git(self.repo.path, "rev-parse", f"{self.repo.product}^{{tree}}")
        unrelated = run_git(self.repo.path, "commit-tree", tree, "-m", "unrelated")
        result = run_assignment(
            self.repo, "plan", base=self.repo.base, product=unrelated
        )
        self.assert_refused(result, "object-ancestry")

    def test_a_draft_already_in_the_base_is_refused(self):
        self.repo.base = self.repo.product
        run_git(self.repo.path, "update-ref", self.repo.base_ref, self.repo.base)
        self.repo.commit_path(
            "docs/decisions/drafts/later-choice.md",
            complete_record("# Decision: Later choice"),
        )
        result = run_assignment(
            self.repo, "plan", base=self.repo.base, product=self.repo.product
        )
        self.assert_refused(result, "base-draft")

    def test_report_path_traversal_is_refused_without_writing(self):
        outside = self.repo.path.parent / "escape.json"
        result = run_assignment(
            self.repo,
            "plan",
            base=self.repo.base,
            product=self.repo.product,
            report="../escape.json",
        )
        self.assert_refused(result, "report-path")
        self.assertFalse(outside.exists())
        self.assertFalse((self.repo.path / ".hexaemeron").exists())

    def test_a_failed_plan_creates_no_report_directory(self):
        blob = run_git(
            self.repo.path, "hash-object", "-w", "--stdin", input_bytes=b"wrong type"
        )
        result = run_assignment(
            self.repo, "plan", base=blob, product=self.repo.product
        )
        self.assert_refused(result, "object-type")
        self.assertFalse((self.repo.path / ".hexaemeron").exists())


class StableIdentityLint(unittest.TestCase):
    def run_lint(
        self,
        *,
        drafts: tuple[str, ...] = ("alpha-choice",),
        finals: tuple[str, ...] = (),
        markdown: str = "",
        source: str = "",
    ) -> tuple[int, list[dict[str, object]]]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft_dir = root / "docs/decisions/drafts"
            draft_dir.mkdir(parents=True)
            for slug in drafts:
                (draft_dir / f"{slug}.md").write_bytes(
                    complete_record(f"# Decision: Choose {slug}")
                )
            for value in finals:
                number, slug = value.split(":", 1)
                target = root / f"docs/decisions/ADR-{number}-{slug}.md"
                target.write_bytes(complete_record(f"# ADR-{number}: Choose {slug}"))
            if markdown:
                (root / "note.md").write_text(markdown, encoding="utf-8")
            if source:
                (root / "source.py").write_text(source, encoding="utf-8")
            result = subprocess.run(  # phylax: allow subprocess: fixed lint argv
                [sys.executable, str(HYPO), "--format", "json", str(root)],
                capture_output=True,
                env=clean_env(),
                check=False,
            )
            findings = json.loads(result.stdout.decode("utf-8"))
            return result.returncode, findings

    def test_valid_markdown_reference_resolves_to_a_draft(self):
        status, findings = self.run_lint(markdown="Governed by adr/alpha-choice.\n")
        self.assertEqual((status, findings), (0, []))

    def test_only_the_exact_stable_identity_placeholder_is_exempt(self):
        status, findings = self.run_lint(
            markdown="Grammar adr/<slug>=ADR-NNN; typo adr/<slug>-typo.\n"
        )
        self.assertEqual(status, 1)
        self.assertEqual([finding["code"] for finding in findings], ["H008"])

    def test_the_portable_evolution_links_resolve_through_the_canonical_copy(self):
        result = subprocess.run(  # phylax: allow subprocess: fixed lint argv
            [sys.executable, str(HYPO), str(PORTABLE_EVOLUTION)],
            capture_output=True,
            env=clean_env(),
            check=False,
        )
        self.assertEqual(
            result.returncode,
            0,
            result.stdout.decode("utf-8", "replace")
            + result.stderr.decode("utf-8", "replace"),
        )

    def test_dangling_markdown_reference_is_reported(self):
        status, findings = self.run_lint(markdown="Governed by adr/missing-choice.\n")
        self.assertEqual(status, 1)
        self.assertIn("H009", [finding["code"] for finding in findings])

    def test_dangling_source_comment_reference_is_reported(self):
        status, findings = self.run_lint(source="# governed by adr/missing-choice\n")
        self.assertEqual(status, 1)
        self.assertIn("H009", [finding["code"] for finding in findings])

    def test_duplicate_draft_and_final_identity_is_reported(self):
        status, findings = self.run_lint(
            drafts=("alpha-choice",), finals=("061:alpha-choice",)
        )
        self.assertEqual(status, 1)
        self.assertIn("H008", [finding["code"] for finding in findings])

    def test_hostile_draft_identity_is_reported(self):
        for slug in (
            "Uppercase",
            "caf\N{LATIN SMALL LETTER E WITH ACUTE}",
            "bad\nname",
            "a" * 97,
        ):
            with self.subTest(slug=repr(slug)):
                status, findings = self.run_lint(drafts=(slug,))
                self.assertEqual(status, 1)
                self.assertIn("H008", [finding["code"] for finding in findings])

    def test_traversal_reference_is_reported(self):
        status, findings = self.run_lint(markdown="Governed by adr/../outside.\n")
        self.assertEqual(status, 1)
        self.assertIn("H008", [finding["code"] for finding in findings])


if __name__ == "__main__":
    unittest.main()
