#!/usr/bin/env python3
"""Bounded tests for the checked impact map and the global check executor.

Every case here drives the real ``scripts/run_checks.py`` module against either
the repository's own committed map or a bounded fixture map.  Nothing in this
file starts a network call, and every subprocess a case starts is a fixed argv
that prints or exits.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "check-runner"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import run_checks  # noqa: E402


def load_fixture(name: str) -> run_checks.CheckMap:
    return run_checks.load_map(FIXTURES, name)


class CheckMapContractTests(unittest.TestCase):
    """The committed map must stay a valid, total, non-overlapping graph."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.check_map = run_checks.load_map(REPO_ROOT)

    def test_repository_map_loads_and_is_current(self) -> None:
        run_checks.refuse_stale_commands(REPO_ROOT, self.check_map)
        self.assertTrue(self.check_map.checks)
        self.assertTrue(self.check_map.scopes)

    def test_every_tracked_path_has_exactly_one_owner(self) -> None:
        listing = subprocess.run(
            ["git", "ls-files"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            shell=False,
            check=True,
        ).stdout.split("\n")
        unowned = [p for p in listing if p and run_checks.owner_of(self.check_map, p) is None]
        self.assertEqual(unowned, [], f"paths without a declared owner: {unowned[:10]}")

    def test_a_written_elenchus_report_does_not_refuse_the_plan(self) -> None:
        """Regression: the step's own runner contract broke its own planner.

        ``run_tests.py --elenchus-report .elenchus/<step>.json`` leaves a
        relevant untracked file behind.  While that path was neither ignored
        nor owned it reached the planner as an unowned changed path, so every
        plan refused with ``unknown-ownership`` once Elenchus had run once.
        """
        report = REPO_ROOT / ".elenchus" / "probe.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        created = not report.exists()
        if created:
            report.write_text("{}\n", encoding="utf-8")
        try:
            observed = run_checks.changed_paths(REPO_ROOT, None)
            self.assertNotIn(
                ".elenchus/probe.json", observed,
                "an Elenchus report must not look like a source change",
            )
        finally:
            if created:
                report.unlink()

    def test_relevant_untracked_paths_also_resolve_to_an_owner(self) -> None:
        """Totality over ``git ls-files`` alone does not cover what the planner reads.

        ``changed_paths`` unions tracked changes with relevant untracked files,
        so an unowned untracked path refuses just as hard as a tracked one.
        """
        untracked = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            cwd=str(REPO_ROOT), capture_output=True, text=True, shell=False, check=True,
        ).stdout.split("\n")
        unowned = [
            p for p in untracked
            if p and not run_checks.is_runner_owned(p)
            and run_checks.owner_of(self.check_map, p) is None
        ]
        self.assertEqual(unowned, [], f"untracked paths with no declared owner: {unowned[:10]}")

    def test_owner_resolution_prefers_the_longest_prefix(self) -> None:
        self.assertEqual(run_checks.owner_of(self.check_map, "scripts/contributors.py"), "root")
        self.assertEqual(
            run_checks.owner_of(self.check_map, "scripts/promise_machine.py"), "promise-machine"
        )

    def test_every_scope_check_and_group_member_resolves(self) -> None:
        for scope in self.check_map.scopes.values():
            for cid in scope.checks:
                self.assertIn(cid, self.check_map.checks)
        for gid, members in self.check_map.groups.items():
            for cid in members:
                self.assertEqual(self.check_map.checks[cid].group, gid)


class MapRefusalTests(unittest.TestCase):
    """A malformed graph refuses by name before anything is selected."""

    def assert_refuses(self, fixture: str, code: str) -> None:
        with self.assertRaises(run_checks.PlanError) as caught:
            load_fixture(fixture)
        self.assertEqual(caught.exception.code, code)

    def test_duplicate_key_refuses(self) -> None:
        self.assert_refuses("map-duplicate-key.json", "duplicate-key")

    def test_dependency_cycle_refuses(self) -> None:
        self.assert_refuses("map-cycle.json", "dependency-cycle")

    def test_ambiguous_ownership_refuses(self) -> None:
        self.assert_refuses("map-ambiguous-owner.json", "ambiguous-ownership")

    def test_traversing_owner_path_refuses(self) -> None:
        self.assert_refuses("map-unsafe-path.json", "unsafe-path")

    def test_git_namespace_script_refuses(self) -> None:
        self.assert_refuses("map-git-namespace.json", "unsafe-path")

    def test_unknown_check_reference_refuses(self) -> None:
        self.assert_refuses("map-unknown-check.json", "map-invalid")

    def test_stale_command_refuses_before_execution(self) -> None:
        check_map = load_fixture("map-stale-command.json")
        with self.assertRaises(run_checks.PlanError) as caught:
            run_checks.refuse_stale_commands(REPO_ROOT, check_map)
        self.assertEqual(caught.exception.code, "stale-command")


class SelectionTests(unittest.TestCase):
    """Requested scope is always widened by the actual diff, then closed."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.check_map = run_checks.load_map(REPO_ROOT)
        cls.cases = json.loads((FIXTURES / "selection-cases.json").read_text())["cases"]

    def select(self, changed, requested=(), full=False):
        return run_checks.build_selection(
            REPO_ROOT, self.check_map, requested, None, full, observed=changed
        )

    def test_named_change_classes_select_their_own_scopes(self) -> None:
        for case in self.cases:
            with self.subTest(case=case["name"]):
                if "expect_refusal" in case:
                    with self.assertRaises(run_checks.PlanError) as caught:
                        self.select(case["changed"])
                    self.assertEqual(caught.exception.code, case["expect_refusal"])
                    continue
                selection = self.select(case["changed"])
                for scope in case["expect_scopes"]:
                    self.assertIn(scope, selection.scopes, f"{case['name']} missed {scope}")
                for scope in case.get("reject_scopes", []):
                    self.assertNotIn(scope, selection.scopes, f"{case['name']} over-selected {scope}")

    def test_requested_scope_is_widened_by_the_actual_diff(self) -> None:
        selection = self.select(["plugins/janus/tests/test_x.py"], requested=["lemma"])
        self.assertIn("lemma", selection.scopes)
        self.assertIn("janus", selection.scopes)
        self.assertIn("requested", selection.scopes["lemma"])
        self.assertTrue(
            any("changed path" in reason for reason in selection.scopes["janus"]),
            "the widening reason must name the changed path",
        )

    def test_every_inclusion_carries_a_reason(self) -> None:
        selection = self.select(["PROMISE_MACHINE.md"])
        for scope, reasons in selection.scopes.items():
            self.assertTrue(reasons, f"{scope} was selected without a reason")

    def test_closure_is_deterministic(self) -> None:
        first = self.select(["PROMISE_MACHINE.md"]).scopes
        second = self.select(["PROMISE_MACHINE.md"]).scopes
        self.assertEqual(sorted(first), sorted(second))

    def test_shared_contract_reaches_only_named_consumers(self) -> None:
        selection = self.select(["PROMISE_MACHINE.md"])
        self.assertIn("hexaemeron", selection.scopes)
        self.assertIn("root", selection.scopes)
        self.assertNotIn("alexandria", selection.scopes)

    def test_full_tolerates_an_unowned_path(self) -> None:
        selection = self.select(["unowned/thing.txt"], full=True)
        self.assertEqual(selection.unowned_paths, ["unowned/thing.txt"])
        self.assertIn("root", selection.scopes)

    def test_unknown_scope_refuses(self) -> None:
        with self.assertRaises(run_checks.PlanError) as caught:
            self.select([], requested=["not-a-scope"])
        self.assertEqual(caught.exception.code, "unknown-scope")


class SchedulerTests(unittest.TestCase):
    """One global budget covers commands, ordered groups and nested shards."""

    def test_live_slots_never_exceed_the_budget(self) -> None:
        scheduler = run_checks.Scheduler(4)
        errors: list[str] = []
        barrier_lock = threading.Lock()
        live = {"count": 0}

        def worker(slots: int) -> None:
            granted = scheduler.acquire(slots)
            with barrier_lock:
                live["count"] += granted
                if live["count"] > scheduler.budget:
                    errors.append(f"live {live['count']} exceeded budget {scheduler.budget}")
            with barrier_lock:
                live["count"] -= granted
            scheduler.release(granted)

        threads = [threading.Thread(target=worker, args=(s,)) for s in (1, 2, 3, 4, 1, 1)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(errors, [])
        self.assertLessEqual(scheduler.high_water, scheduler.budget)

    def test_a_request_over_budget_is_capped_not_deadlocked(self) -> None:
        scheduler = run_checks.Scheduler(2)
        granted = scheduler.acquire(9)
        self.assertEqual(granted, 2)
        scheduler.release(granted)

    def test_nested_runner_receives_an_allocation_not_a_new_budget(self) -> None:
        nested = run_checks.Check(
            id="nested", title="Nested", argv=("python3",), cwd=".", kind="suite",
            script=None, jobs_flag="--jobs", requires_executable=None, group=None,
            order=0, timeout_seconds=60,
        )
        alone = run_checks._allocation_for(nested, budget=8, parallel_checks=1)
        shared = run_checks._allocation_for(nested, budget=8, parallel_checks=4)
        self.assertEqual(alone, 8)
        self.assertLessEqual(shared, 8)
        self.assertGreaterEqual(shared, 1)

    def test_a_plain_check_takes_one_slot(self) -> None:
        plain = run_checks.Check(
            id="plain", title="Plain", argv=("python3",), cwd=".", kind="lint",
            script=None, jobs_flag=None, requires_executable=None, group=None,
            order=0, timeout_seconds=60,
        )
        self.assertEqual(run_checks._allocation_for(plain, budget=8, parallel_checks=1), 1)


class ExecutionTests(unittest.TestCase):
    """Fixed argv, ordered groups and bounded output."""

    def test_ordered_group_runs_in_declared_order(self) -> None:
        check_map = load_fixture("map-ordered-group.json")
        checks = [check_map.checks["build"], check_map.checks["test"]]
        results, scheduler = run_checks.execute(checks, REPO_ROOT, 4)
        self.assertEqual({r["status"] for r in results}, {"passed"})
        self.assertLessEqual(scheduler.high_water, 4)

    def test_ordered_group_stops_after_a_failing_member(self) -> None:
        check_map = load_fixture("map-failing-group.json")
        checks = [check_map.checks["build"], check_map.checks["test"]]
        results, _ = run_checks.execute(checks, REPO_ROOT, 4)
        by_id = {r["check"]: r for r in results}
        self.assertEqual(by_id["build"]["status"], "failed")
        self.assertEqual(by_id["test"]["status"], "not-started")

    def test_argv_is_fixed_and_no_shell_expands_it(self) -> None:
        check = run_checks.Check(
            id="echoing", title="Echoing", argv=("python3", "-c", "print('$HOME and *')"),
            cwd=".", kind="lint", script=None, jobs_flag=None, requires_executable=None,
            group=None, order=0, timeout_seconds=60,
        )
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(2), 1)
        self.assertEqual(record["status"], "passed")
        self.assertIn("$HOME and *", record["output"]["head"])

    def test_missing_executable_is_a_command_failure(self) -> None:
        check = run_checks.Check(
            id="absent", title="Absent", argv=("definitely-not-on-path",), cwd=".",
            kind="suite", script=None, jobs_flag=None,
            requires_executable="definitely-not-on-path", group=None, order=0,
            timeout_seconds=60,
        )
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(2), 1)
        self.assertEqual(record["failure_class"], "command-failure")
        self.assertEqual(record["status"], "unavailable")

    def test_a_failing_suite_is_a_test_failure(self) -> None:
        check = run_checks.Check(
            id="red", title="Red", argv=("python3", "-c", "raise SystemExit(1)"), cwd=".",
            kind="suite", script=None, jobs_flag=None, requires_executable=None,
            group=None, order=0, timeout_seconds=60,
        )
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(2), 1)
        self.assertEqual(record["failure_class"], "test-failure")

    def test_nested_allocation_reaches_the_child_argv(self) -> None:
        check = run_checks.Check(
            id="nested", title="Nested",
            argv=("python3", "-c", "import sys; print(' '.join(sys.argv[1:]))"),
            cwd=".", kind="suite", script=None, jobs_flag="--jobs",
            requires_executable=None, group=None, order=0, timeout_seconds=60,
        )
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(6), 1)
        self.assertEqual(record["nested_allocation"], 6)
        self.assertIn("--jobs 6", record["output"]["head"])


class BoundedOutputTests(unittest.TestCase):
    """Diagnosis survives without unbounded memory use."""

    def test_head_and_tail_are_retained_with_an_exact_count(self) -> None:
        buffer = run_checks.CaptureBuffer()
        payload = b"a" * (run_checks.MAX_CAPTURE_HEAD_BYTES + run_checks.MAX_CAPTURE_TAIL_BYTES + 5_000)
        buffer.feed(payload)
        record = buffer.record()
        self.assertEqual(record["bytes"], len(payload))
        self.assertTrue(record["truncated"])
        self.assertLessEqual(len(record["head"]), run_checks.MAX_CAPTURE_HEAD_BYTES)
        self.assertLessEqual(len(record["tail"]), run_checks.MAX_CAPTURE_TAIL_BYTES)

    def test_short_output_is_not_marked_truncated(self) -> None:
        buffer = run_checks.CaptureBuffer()
        buffer.feed(b"short")
        record = buffer.record()
        self.assertFalse(record["truncated"])
        self.assertEqual(record["head"], "short")


class SubprocessBoundTests(unittest.TestCase):
    """A check is bounded by its own deadline, whatever it prints or retains.

    Regression for the audit finding that ``timeout_seconds`` bounded nothing:
    the deadline was only consulted after a blocking ``read(65_536)`` returned,
    so a quiet check outlived it and a descendant holding the write end blocked
    completion for ever while the record still claimed a pass.
    """

    def test_a_quiet_check_is_stopped_at_its_deadline(self) -> None:
        check = run_checks.Check(
            id="quiet", title="Quiet",
            argv=("python3", "-c", "import time; time.sleep(30)"),
            cwd=".", kind="suite", script=None, jobs_flag=None,
            requires_executable=None, group=None, order=0, timeout_seconds=2,
        )
        started = time.monotonic()
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(2), 1)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 20, f"the deadline did not bound the check: {elapsed:.1f}s")
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["failure_class"], "command-failure")
        self.assertEqual(record["reason"], "timeout")

    def test_a_retained_descriptor_is_a_scheduler_error_not_a_pass(self) -> None:
        program = (
            "import os, time\n"
            "if os.fork() == 0:\n"
            "    time.sleep(30)\n"
            "    os._exit(0)\n"
            "os._exit(0)\n"
        )
        check = run_checks.Check(
            id="detached", title="Detached", argv=("python3", "-c", program),
            cwd=".", kind="suite", script=None, jobs_flag=None,
            requires_executable=None, group=None, order=0, timeout_seconds=2,
        )
        started = time.monotonic()
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(2), 1)
        elapsed = time.monotonic() - started
        self.assertLess(elapsed, 20, f"a retained descriptor blocked completion: {elapsed:.1f}s")
        self.assertNotEqual(record["status"], "passed")
        self.assertEqual(record["failure_class"], "scheduler-error")
        self.assertTrue(record["descriptor_retained"])
        self.assertIn("retained", record["reason"])

    def test_an_ordinary_check_is_not_charged_the_drain_interval(self) -> None:
        check = run_checks.Check(
            id="prompt", title="Prompt", argv=("python3", "-c", "print('done')"),
            cwd=".", kind="lint", script=None, jobs_flag=None,
            requires_executable=None, group=None, order=0, timeout_seconds=60,
        )
        started = time.monotonic()
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(2), 1)
        self.assertEqual(record["status"], "passed")
        self.assertFalse(record["descriptor_retained"])
        self.assertIn("done", record["output"]["head"])
        self.assertLess(time.monotonic() - started, run_checks.DRAIN_SECONDS)


class WorkerAccountingTests(unittest.TestCase):
    """Selection and completion are a disjoint union before any green.

    Regression for the audit finding that a worker fault removed the check from
    ``results`` entirely, so a selected check could vanish while the run still
    aggregated green.
    """

    def _faulting_check(self) -> run_checks.Check:
        # A non-OSError raised inside run_check used to kill the worker thread.
        return run_checks.Check(
            id="faulting", title="Faulting", argv=("python3", "-c", "pass"),
            cwd=".", kind="suite", script=None, jobs_flag=None,
            requires_executable=None, group=None, order=0,
            timeout_seconds="not-a-number",  # type: ignore[arg-type]
        )

    def test_a_faulting_worker_stays_in_the_report_as_a_scheduler_error(self) -> None:
        good = run_checks.Check(
            id="good", title="Good", argv=("python3", "-c", "pass"), cwd=".",
            kind="lint", script=None, jobs_flag=None, requires_executable=None,
            group=None, order=0, timeout_seconds=60,
        )
        results, _ = run_checks.execute([good, self._faulting_check()], REPO_ROOT, 4)
        recorded = {r["check"] for r in results}
        self.assertEqual(recorded, {"good", "faulting"}, "a selected check was dropped")
        by_id = {r["check"]: r for r in results}
        self.assertEqual(by_id["faulting"]["failure_class"], "scheduler-error")
        classes = {r["failure_class"] for r in results if r.get("failure_class")}
        self.assertIn("scheduler-error", classes, "the fault must keep the run out of green")

    def test_every_emitted_failure_class_is_declared(self) -> None:
        results, _ = run_checks.execute([self._faulting_check()], REPO_ROOT, 2)
        for record in results:
            if record.get("failure_class"):
                self.assertIn(record["failure_class"], run_checks.FAILURE_CLASSES)


class MalformedMapFieldTests(unittest.TestCase):
    """A malformed field refuses by name instead of raising out of main().

    Regression for the audit finding that an unvalidated ``jobs_flag`` reached
    ``subprocess.Popen`` and that a non-numeric ``timeout_seconds`` escaped as a
    bare ValueError rather than an ``invalid-plan`` refusal.
    """

    def _map_with(self, tmp: str, body: dict) -> Path:
        payload = {
            "schema": "wildcat.check-map.v1",
            "checks": {"probe": dict({"title": "Probe", "argv": ["python3", "-c", "pass"],
                                      "cwd": ".", "kind": "lint"}, **body)},
            "groups": {},
            "scopes": {"one": {"title": "One", "checks": ["probe"]}},
            "dependencies": {},
            "owners": [{"path": "src", "scope": "one"}],
        }
        root = Path(tmp)
        (root / "map.json").write_text(json.dumps(payload))
        return root

    def test_non_string_and_non_integer_fields_refuse(self) -> None:
        import tempfile

        for body in (
            {"jobs_flag": 7},
            {"jobs_flag": ["--jobs"]},
            {"requires_executable": 7},
            {"timeout_seconds": "soon"},
            {"timeout_seconds": 0},
            {"order": "first"},
        ):
            with self.subTest(body=body):
                with tempfile.TemporaryDirectory() as tmp:
                    root = self._map_with(tmp, body)
                    with self.assertRaises(run_checks.PlanError) as caught:
                        run_checks.load_map(root, "map.json")
                    self.assertEqual(caught.exception.code, "map-invalid")

    def test_a_well_formed_optional_field_still_loads(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._map_with(tmp, {"jobs_flag": "--jobs", "timeout_seconds": 30})
            check_map = run_checks.load_map(root, "map.json")
            self.assertEqual(check_map.checks["probe"].jobs_flag, "--jobs")
            self.assertEqual(check_map.checks["probe"].timeout_seconds, 30)


class ReportTests(unittest.TestCase):
    """Reports are confined, atomic and never left half written."""

    def test_a_symlinked_component_cannot_redirect_the_report(self) -> None:
        """Regression: the lexical check could not see a link out of the tree."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (root / "reports").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.write_report(root, "reports/run.json", {"schema": "x"})
            self.assertEqual(caught.exception.code, "unsafe-path")
            self.assertEqual(list(outside.iterdir()), [], "the report escaped the repository")

    def test_a_symlinked_component_refuses_before_execution(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            root.mkdir()
            (root / "out").symlink_to(Path(tmp), target_is_directory=True)
            with self.assertRaises(run_checks.PlanError):
                run_checks.confine_report_path(root, "out/run.json")

    def test_unsafe_report_targets_refuse(self) -> None:
        for candidate in ("../escape.json", "/etc/passwd", ".git/config", "a/../../b.json"):
            with self.subTest(candidate=candidate):
                with self.assertRaises(run_checks.PlanError):
                    run_checks.write_report(REPO_ROOT, candidate, {"schema": "x"})

    def test_report_write_is_atomic_and_leaves_no_partial(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = run_checks.write_report(root, "out/report.json", {"schema": run_checks.RUN_SCHEMA})
            target = root / written
            self.assertTrue(target.is_file())
            self.assertEqual(json.loads(target.read_text())["schema"], run_checks.RUN_SCHEMA)
            leftovers = [p.name for p in (root / "out").iterdir() if p.name.endswith(".partial")]
            self.assertEqual(leftovers, [])

    def test_report_replacement_keeps_one_file(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            run_checks.write_report(root, "out/report.json", {"schema": "first"})
            run_checks.write_report(root, "out/report.json", {"schema": "second"})
            entries = sorted(p.name for p in (root / "out").iterdir())
            self.assertEqual(entries, ["report.json"])
            self.assertEqual(json.loads((root / "out/report.json").read_text())["schema"], "second")


class SnapshotOwnershipTests(unittest.TestCase):
    """Cleanup removes only a tree this runner can still prove it owns."""

    def test_owned_tree_is_removed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nonce = "a" * 32
            parent = root / run_checks.RUNNER_PARENT / nonce
            parent.mkdir(parents=True)
            (parent / run_checks.SENTINEL_NAME).write_text(nonce + "\n")
            self.assertEqual(run_checks.remove_snapshot(root, nonce), "removed")
            self.assertFalse(parent.exists())

    def test_a_tree_without_a_matching_sentinel_is_preserved(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nonce = "b" * 32
            parent = root / run_checks.RUNNER_PARENT / nonce
            parent.mkdir(parents=True)
            (parent / run_checks.SENTINEL_NAME).write_text("a different nonce\n")
            self.assertEqual(run_checks.remove_snapshot(root, nonce), "not-owned")
            self.assertTrue(parent.exists())

    def test_a_tree_without_any_sentinel_is_preserved(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nonce = "c" * 32
            parent = root / run_checks.RUNNER_PARENT / nonce
            parent.mkdir(parents=True)
            self.assertEqual(run_checks.remove_snapshot(root, nonce), "not-owned")
            self.assertTrue(parent.exists())


class SourceIdentityTests(unittest.TestCase):
    """Source movement is observable, and the identity covers untracked content."""

    def test_identity_is_stable_across_repeated_reads(self) -> None:
        first = run_checks.source_identity(REPO_ROOT)
        second = run_checks.source_identity(REPO_ROOT)
        self.assertEqual(first, second)
        self.assertRegex(first, r"^[0-9a-f]{64}$")

    def test_git_environment_is_scrubbed_for_child_processes(self) -> None:
        env = run_checks._git_env()
        self.assertNotIn("GIT_DIR", env)
        self.assertNotIn("GIT_INDEX_FILE", env)
        self.assertEqual(env["GIT_PAGER"], "cat")


class CapacityTests(unittest.TestCase):
    """The budget is quota aware, capped, and never zero."""

    def test_automatic_budget_is_positive_and_capped(self) -> None:
        capacity = run_checks.read_capacity()
        self.assertGreaterEqual(capacity["effective_budget"], 1)
        self.assertLessEqual(capacity["effective_budget"], run_checks.SAFETY_CAP)
        self.assertEqual(capacity["safety_cap"], run_checks.SAFETY_CAP)
        self.assertEqual(capacity["source"], "automatic")

    def test_explicit_jobs_must_be_positive(self) -> None:
        for candidate in ("0", "-3", "x", ""):
            with self.subTest(candidate=candidate):
                with self.assertRaises(Exception):
                    run_checks.positive_int(candidate)
        self.assertEqual(run_checks.positive_int("7"), 7)


class CommandLineTests(unittest.TestCase):
    """The documented entrypoints behave as the runbook step states."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "scripts/run_checks.py", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            shell=False,
        )

    def test_full_plan_json_exits_zero_and_accounts_for_every_check(self) -> None:
        proc = self.run_cli("--full", "--plan", "--format", "json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], run_checks.PLAN_SCHEMA)
        check_map = run_checks.load_map(REPO_ROOT)
        selected = {c["id"] for c in payload["selected_checks"]}
        self.assertEqual(selected | set(payload["omitted_checks"]), set(check_map.checks))
        self.assertEqual(payload["omitted_checks"], [])

    def test_scoped_plan_json_exits_zero_and_selects_a_subset(self) -> None:
        proc = self.run_cli("--scope", "hexaemeron", "--plan", "--format", "json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        payload = json.loads(proc.stdout)
        selected = {c["id"] for c in payload["selected_checks"]}
        self.assertIn("hexaemeron-suite", selected)
        self.assertIn("hexaemeron", payload["selected_scopes"])
        self.assertTrue(payload["omitted_checks"], "a scoped plan must omit something")

    def test_plan_accounts_for_every_selected_check_exactly_once(self) -> None:
        proc = self.run_cli("--full", "--plan", "--format", "json")
        payload = json.loads(proc.stdout)
        ids = [c["id"] for c in payload["selected_checks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_unknown_scope_refuses_with_invalid_plan(self) -> None:
        proc = self.run_cli("--scope", "no-such-scope", "--plan", "--format", "json")
        self.assertEqual(proc.returncode, 2)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["failure_class"], "invalid-plan")
        self.assertEqual(payload["code"], "unknown-scope")

    def test_invalid_base_refuses_before_execution(self) -> None:
        proc = self.run_cli("--scope", "root", "--base", "no-such-ref", "--plan", "--format", "json")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)["code"], "invalid-base")

    def test_unsafe_report_path_refuses_before_execution(self) -> None:
        proc = self.run_cli("--scope", "schemas", "--report", "../escape.json", "--format", "json")
        self.assertEqual(proc.returncode, 2)
        self.assertEqual(json.loads(proc.stdout)["failure_class"], "invalid-plan")

    def test_human_plan_names_its_reasons(self) -> None:
        proc = self.run_cli("--scope", "lemma", "--plan")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("selected scopes", proc.stdout)
        self.assertIn("requested", proc.stdout)
        self.assertIn("budget", proc.stdout)


class TimingAuthorityTests(unittest.TestCase):
    """Timing history may balance work; it may never decide membership."""

    def test_no_pass_verdict_is_persisted_by_the_plan(self) -> None:
        check_map = run_checks.load_map(REPO_ROOT)
        selection = run_checks.build_selection(
            REPO_ROOT, check_map, ["lemma"], None, False, observed=[]
        )
        checks = run_checks.selected_checks(check_map, selection)
        plan = run_checks.plan_record(check_map, selection, checks, run_checks.read_capacity())
        serialised = json.dumps(plan)
        for forbidden in ("passed", "verdict", "cached_result"):
            self.assertNotIn(forbidden, serialised)

    def test_selection_ignores_any_prior_result(self) -> None:
        check_map = run_checks.load_map(REPO_ROOT)
        first = run_checks.build_selection(
            REPO_ROOT, check_map, ["lemma"], None, False, observed=[]
        )
        second = run_checks.build_selection(
            REPO_ROOT, check_map, ["lemma"], None, False, observed=[]
        )
        self.assertEqual(sorted(first.scopes), sorted(second.scopes))


class TemporaryRepositoryMixin:
    """Build a disposable repository whose fixture commits never invoke a signer."""

    def make_repo(self, tmp: str) -> Path:
        root = Path(tmp) / "repo"
        (root / "src").mkdir(parents=True)
        (root / "tests").mkdir(parents=True)
        (root / "src" / "kept.txt").write_text("kept\n")
        (root / "src" / "doomed.txt").write_text("doomed\n")
        subprocess.run(["git", "init", "--quiet", str(root)], check=True, shell=False)
        for key, value in (
            ("user.email", "fixture@example.invalid"),
            ("user.name", "Fixture"),
            ("commit.gpgsign", "false"),
            ("tag.gpgsign", "false"),
        ):
            subprocess.run(
                ["git", "config", key, value], cwd=str(root), check=True, shell=False
            )
        return root

    def git(self, root: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=str(root), check=True, shell=False,
                       capture_output=True)

    def write_map(self, root: Path, argv: list[str]) -> None:
        payload = {
            "schema": "wildcat.check-map.v1",
            "checks": {
                "probe": {"title": "Probe", "argv": argv, "cwd": ".", "kind": "lint"}
            },
            "groups": {},
            "scopes": {"one": {"title": "One", "checks": ["probe"]}},
            "dependencies": {},
            "owners": [
                {"path": "src", "scope": "one"},
                {"path": "tests", "scope": "one"},
            ],
        }
        (root / "tests" / "check-map-v1.json").write_text(json.dumps(payload, indent=2))

    def run_cli(self, root: Path, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / "scripts" / "run_checks.py"), *args],
            cwd=str(root),
            capture_output=True,
            text=True,
            shell=False,
        )


class DiffCaptureTests(TemporaryRepositoryMixin, unittest.TestCase):
    """Renames, deletions and relevant untracked files all reach the planner."""

    def test_rename_deletion_and_untracked_are_captured(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            self.git(root, "mv", "src/kept.txt", "src/renamed.txt")
            self.git(root, "rm", "--quiet", "src/doomed.txt")
            (root / "src" / "fresh.txt").write_text("fresh\n")

            observed = run_checks.changed_paths(root, None)
            self.assertIn("src/renamed.txt", observed)
            self.assertIn("src/kept.txt", observed)
            self.assertIn("src/doomed.txt", observed)
            self.assertIn("src/fresh.txt", observed)

    def test_ignored_files_are_not_captured(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            (root / ".gitignore").write_text("src/ignored.txt\n")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            (root / "src" / "ignored.txt").write_text("ignored\n")

            self.assertNotIn("src/ignored.txt", run_checks.changed_paths(root, None))

    def test_base_widens_selection_by_committed_history(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            base = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(root), capture_output=True,
                text=True, check=True, shell=False,
            ).stdout.strip()
            (root / "src" / "later.txt").write_text("later\n")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "later")

            self.assertIn("src/later.txt", run_checks.changed_paths(root, base))
            self.assertNotIn("src/later.txt", run_checks.changed_paths(root, None))


class SupersessionTests(TemporaryRepositoryMixin, unittest.TestCase):
    """One movement supersedes and retries; repeated movement is unstable-source."""

    def _mutating_argv(self, root: Path, *, once: bool) -> list[str]:
        marker = root / "src" / "moved.txt"
        flag = root / "src" / ".mutated-once"
        if once:
            program = (
                "import pathlib;"
                f"flag=pathlib.Path({str(flag)!r});"
                f"target=pathlib.Path({str(marker)!r});"
                "flag.exists() or (target.write_text('moved'), flag.write_text('1'))"
            )
        else:
            program = (
                "import pathlib,uuid;"
                f"pathlib.Path({str(marker)!r}).write_text(uuid.uuid4().hex)"
            )
        return ["python3", "-c", program]

    def test_a_single_movement_supersedes_then_completes(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, self._mutating_argv(root, once=True))
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")

            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["outcome"], "green")
            self.assertEqual(len(payload["attempts"]), 1)
            self.assertEqual(payload["attempts"][0]["outcome"], "superseded")

    def test_repeated_movement_ends_as_unstable_source(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, self._mutating_argv(root, once=False))
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")

            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["outcome"], "unstable-source")
            self.assertEqual(payload["failure_classes"], ["unstable-source"])
            self.assertNotIn("test-failure", payload["failure_classes"])

    def test_a_stable_source_reports_no_superseded_attempt(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "print('stable')"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")

            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["outcome"], "green")
            self.assertEqual(payload["attempts"], [])
            self.assertEqual(payload["snapshot_cleanup"], "removed")

    def test_the_snapshot_is_used_instead_of_the_checkout(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(
                root,
                ["python3", "-c", "import os;print('cwd=' + os.getcwd())"],
            )
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")

            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            emitted = payload["checks"][0]["output"]["head"]
            self.assertIn(run_checks.RUNNER_PARENT.replace("/", os.sep), emitted)
            self.assertNotIn(f"cwd={root}\n", emitted)


class AggregationTests(TemporaryRepositoryMixin, unittest.TestCase):
    """Every selected check reaches exactly one terminal disposition."""

    def test_each_selected_check_appears_once_in_the_report(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            payload = {
                "schema": "wildcat.check-map.v1",
                "checks": {
                    f"probe-{n}": {
                        "title": f"Probe {n}",
                        "argv": ["python3", "-c", f"print({n})"],
                        "cwd": ".",
                        "kind": "lint",
                    }
                    for n in range(6)
                },
                "groups": {},
                "scopes": {
                    "one": {"title": "One", "checks": [f"probe-{n}" for n in range(6)]}
                },
                "dependencies": {},
                "owners": [{"path": "src", "scope": "one"}, {"path": "tests", "scope": "one"}],
            }
            (root / "tests" / "check-map-v1.json").write_text(json.dumps(payload, indent=2))
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")

            proc = self.run_cli(root, "--scope", "one", "--jobs", "3", "--format", "json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(proc.stdout)
            seen = [c["check"] for c in report["checks"]]
            self.assertEqual(sorted(seen), sorted(payload["checks"]))
            self.assertEqual(len(seen), len(set(seen)))
            self.assertLessEqual(report["scheduler"]["slot_high_water"], 3)
            self.assertEqual(report["scheduler"]["budget"], 3)

    def test_a_red_check_makes_the_run_red_without_hiding_the_others(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            payload = {
                "schema": "wildcat.check-map.v1",
                "checks": {
                    "green": {"title": "Green", "argv": ["python3", "-c", "pass"], "cwd": ".", "kind": "lint"},
                    "red": {"title": "Red", "argv": ["python3", "-c", "raise SystemExit(2)"], "cwd": ".", "kind": "suite"},
                },
                "groups": {},
                "scopes": {"one": {"title": "One", "checks": ["green", "red"]}},
                "dependencies": {},
                "owners": [{"path": "src", "scope": "one"}, {"path": "tests", "scope": "one"}],
            }
            (root / "tests" / "check-map-v1.json").write_text(json.dumps(payload, indent=2))
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")

            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            report = json.loads(proc.stdout)
            self.assertEqual(report["outcome"], "red")
            self.assertEqual(report["failure_classes"], ["test-failure"])
            statuses = {c["check"]: c["status"] for c in report["checks"]}
            self.assertEqual(statuses["green"], "passed")
            self.assertEqual(statuses["red"], "failed")


if __name__ == "__main__":
    unittest.main()


class DescendantSignalSafetyTests(unittest.TestCase):
    """A process group is only ever signalled through a leader the runner owns.

    Regression for the round 2 finding that the descendant-lifetime guard added
    in round 1 derived a process group from an already-reaped pid.  ``poll`` and
    ``wait`` reap the leader and return its pid to the kernel; ``getpgid`` on a
    recycled pid resolves a stranger's group, and the runner then delivered
    SIGTERM and SIGKILL to it.
    """

    class _Reaped:
        """A Popen whose child has already been reaped: returncode is set."""

        pid = 424242
        returncode = 0

        def wait(self, timeout: float | None = None) -> int:
            return 0

    def _record_signals(self) -> tuple[list, object]:
        sent: list = []
        real_getpgid, real_killpg = os.getpgid, os.killpg

        def spy_getpgid(pid: int) -> int:
            return 999_999  # model a pid the kernel has handed to a stranger

        def spy_killpg(pgid: int, sig: int) -> None:
            sent.append((pgid, int(sig)))

        os.getpgid, os.killpg = spy_getpgid, spy_killpg
        self.addCleanup(lambda: (setattr(os, "getpgid", real_getpgid),
                                 setattr(os, "killpg", real_killpg)))
        return sent, None

    def test_a_reaped_leader_is_never_signalled(self) -> None:
        sent, _ = self._record_signals()
        disposition = run_checks._terminate_group(self._Reaped())  # type: ignore[arg-type]
        self.assertEqual(
            sent, [], "the runner signalled a process group derived from a reaped pid"
        )
        self.assertIn("reaped", disposition)

    def test_a_detached_descendant_leaves_a_reaped_leader_unsignalled(self) -> None:
        """The real path: leader exits, a setsid descendant holds the descriptor.

        ``_capture_output`` reaps the leader, waits out the bounded drain, and
        only then asks for termination -- by which point the pid is stale.
        """
        script = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        (script / "detach.py").write_text(
            "import os, sys, time\n"
            "if os.fork() == 0:\n"
            "    os.setsid()\n"          # leave the leader's group entirely
            "    time.sleep(30)\n"       # keep holding the inherited stdout
            "    os._exit(0)\n"
            "sys.stdout.write('leader done\\n'); sys.stdout.flush()\n"
            "os._exit(0)\n",
            encoding="utf-8",
        )
        check = run_checks.Check(
            id="detached", title="Detached", argv=("python3", "detach.py"), cwd=".",
            kind="command", script=None, jobs_flag=None, requires_executable=None,
            group=None, order=0, timeout_seconds=30,
        )
        sent, _ = self._record_signals()
        record = run_checks.run_check(check, script, run_checks.Scheduler(2), 1)
        self.assertEqual(
            sent, [], "a stale pid's process group was signalled after the leader was reaped"
        )
        # The honest verdict is unchanged: a retained descriptor stays a bounded
        # red with an explicit disposition, never a pass.
        self.assertEqual(record["status"], "failed")
        self.assertEqual(record["failure_class"], "scheduler-error")
        self.assertTrue(record["descriptor_retained"])
        self.assertIn("reaped", record["termination"])


class OrderedGroupDeclarationTests(unittest.TestCase):
    """The declared ``ordered`` list is what execution follows.

    Regression for the round 2 finding that ``execute`` sequenced group members
    by the optional ``order`` integer while ignoring the mandatory ``ordered``
    declaration.  A group that stated its sequence only in ``ordered`` ran in
    check-id order instead, silently inverting the declaration.
    """

    def _map(self, tmp: Path, checks: dict, ordered: list) -> Path:
        body = {
            "schema": "wildcat.check-map.v1",
            "checks": checks,
            "groups": {"chain": {"title": "Chain", "ordered": ordered}},
            "scopes": {"one": {"title": "One", "checks": sorted(checks)}},
            "dependencies": {},
            "owners": [{"path": "one", "scope": "one"}],
        }
        (tmp / "m.json").write_text(json.dumps(body), encoding="utf-8")
        return tmp

    def test_a_group_stating_only_ordered_runs_in_that_order(self) -> None:
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        trace = tmp / "trace.txt"
        # The declared sequence is the reverse of check-id order, and no member
        # restates it with an "order" field.  Each member appends its own name,
        # so the file records the sequence execution actually chose.
        def appender(name: str) -> list[str]:
            return [
                "python3", "-c",
                f"open({str(trace)!r}, 'a').write({name!r} + '\\n')",
            ]

        checks = {
            "zeta-setup": {"argv": appender("zeta-setup"), "group": "chain"},
            "alpha-apply": {"argv": appender("alpha-apply"), "group": "chain"},
        }
        check_map = run_checks.load_map(
            self._map(tmp, checks, ["zeta-setup", "alpha-apply"]), "m.json"
        )
        # Go through the real pipeline: selected_checks sorts by check id, and
        # that ordering is what reached execute() in the shipped run.
        selection = run_checks.build_selection(
            tmp, check_map, ["one"], None, False, observed=[]
        )
        selected = run_checks.selected_checks(check_map, selection)
        self.assertEqual([c.id for c in selected], ["alpha-apply", "zeta-setup"])
        results, _ = run_checks.execute(selected, REPO_ROOT, 2)
        self.assertTrue(all(r["status"] == "passed" for r in results), results)
        self.assertEqual(
            trace.read_text(encoding="utf-8").split(),
            ["zeta-setup", "alpha-apply"],
            "execution ignored the declared ordered list and sequenced by check id",
        )

    def test_an_order_field_contradicting_the_declaration_refuses(self) -> None:
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        checks = {
            "build": {"argv": ["true"], "group": "chain", "order": 9},
            "test": {"argv": ["true"], "group": "chain", "order": 1},
        }
        with self.assertRaises(run_checks.PlanError) as caught:
            run_checks.load_map(self._map(tmp, checks, ["build", "test"]), "m.json")
        self.assertEqual(caught.exception.code, "ordered-conflict")

    def test_a_member_missing_from_the_ordered_list_refuses(self) -> None:
        tmp = Path(self.enterContext(__import__("tempfile").TemporaryDirectory()))
        checks = {
            "build": {"argv": ["true"], "group": "chain"},
            "stray": {"argv": ["true"], "group": "chain"},
        }
        with self.assertRaises(run_checks.PlanError) as caught:
            run_checks.load_map(self._map(tmp, checks, ["build"]), "m.json")
        self.assertEqual(caught.exception.code, "map-invalid")

    def test_the_repository_map_group_still_loads_and_agrees(self) -> None:
        check_map = run_checks.load_map(REPO_ROOT)
        for gid, ordered in check_map.groups.items():
            by_order = sorted(
                (c for c in check_map.checks.values() if c.group == gid),
                key=lambda c: c.order,
            )
            self.assertEqual([c.id for c in by_order], list(ordered))


class GitCaptureRefusalTests(unittest.TestCase):
    """A git capture fault refuses by name and leaks no snapshot.

    Regression for the round 2 finding that a ``PlanError`` from git capture --
    an oversized ``git diff HEAD`` is the reachable case -- escaped ``main`` as
    a traceback with exit code 1, the same code a red run uses, and when it
    arose inside ``make_snapshot`` the owned tree and its sentinel were left on
    disk because the caller only caught ``SnapshotError``.
    """

    def test_git_capture_inside_the_snapshot_becomes_a_snapshot_error(self) -> None:
        root = run_checks.repository_root()
        real_git = run_checks.git

        def oversized(r, *args, **kwargs):
            if args[:2] == ("diff", "HEAD"):
                raise run_checks.PlanError("git-oversized", "too much output")
            return real_git(r, *args, **kwargs)

        run_checks.git = oversized
        self.addCleanup(lambda: setattr(run_checks, "git", real_git))
        nonce = "audit" + os.urandom(6).hex()
        parent = root / run_checks.RUNNER_PARENT / nonce
        try:
            with self.assertRaises(run_checks.SnapshotError) as caught:
                run_checks.make_snapshot(root, nonce)
            self.assertEqual(caught.exception.code, "snapshot-error")
            self.assertEqual(
                run_checks.remove_snapshot(root, nonce),
                "removed",
                "the caller could not clean up the tree it owns",
            )
            self.assertFalse(parent.exists(), "the snapshot tree was leaked")
        finally:
            if parent.exists():
                __import__("shutil").rmtree(parent, ignore_errors=True)

    def test_git_capture_around_the_attempt_loop_refuses_rather_than_raising(self) -> None:
        """The attempt loop sits outside main's covered region.

        Shrinking the byte bound alone would refuse during selection and never
        reach the loop, so fail the capture the loop itself performs: the
        ``source_identity`` call taken before and after execution.
        """
        real_identity = run_checks.source_identity

        def oversized(root: Path) -> str:
            raise run_checks.PlanError("git-oversized", "git diff HEAD produced too much output")

        run_checks.source_identity = oversized
        self.addCleanup(lambda: setattr(run_checks, "source_identity", real_identity))
        code = run_checks.main(["--scope", "hexaemeron", "--format", "json"])
        self.assertEqual(code, 2, "a git capture fault must refuse, not exit as a red run")


class CacheDispositionTests(TemporaryRepositoryMixin, unittest.TestCase):
    """The run record states this runner's cache disposition explicitly.

    The step's ephoros discipline names cache among what the reports bind, and
    the composed run reaches a nested runner that does keep a timing cache, so
    the question is not vacuous and absence is not an answer.
    """

    def test_the_runner_reads_no_cache_at_all(self) -> None:
        source = (REPO_ROOT / "scripts" / "run_checks.py").read_text(encoding="utf-8")
        self.assertNotIn("timings-v1", source)

    def test_a_completed_run_binds_its_cache_disposition(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "print('probe')"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = json.loads(proc.stdout)
            self.assertIn("cache", report, "the run record binds no cache disposition")
            self.assertEqual(report["cache"]["result_cache"], "none")
            self.assertIs(report["cache"]["selection_input"], False)
