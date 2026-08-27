#!/usr/bin/env python3
"""Bounded tests for the checked impact map and the global check executor.

Every case here drives the real ``scripts/run_checks.py`` module against either
the repository's own committed map or a bounded fixture map.  Nothing in this
file starts a network call, and every subprocess a case starts is a fixed argv
that prints or exits.
"""

from __future__ import annotations

import json
import errno
import os
import signal
import stat
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

    def test_full_refuses_an_unowned_path(self) -> None:
        """Selecting every check never waives the map's ownership contract."""
        with self.assertRaises(run_checks.PlanError) as caught:
            self.select(["unowned/thing.txt"], full=True)
        self.assertEqual(caught.exception.code, "unknown-ownership")

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
        self.assertEqual(record["nested_allocation"], 5)
        self.assertIn("--jobs 5", record["output"]["head"])


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

    def test_a_timeout_records_its_actual_termination_disposition(self) -> None:
        check = run_checks.Check(
            id="timed", title="Timed",
            argv=("python3", "-c", "import time; time.sleep(30)"),
            cwd=".", kind="lint", script=None, jobs_flag=None,
            requires_executable=None, group=None, order=0, timeout_seconds=1,
        )
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(1), 1)
        self.assertEqual(record["reason"], "timeout")
        self.assertEqual(
            record["termination"],
            "leader-exited-after-group-sigterm; process-group-exit-unproved",
        )

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

    def test_unknown_fields_refuse_at_every_schema_level(self) -> None:
        import copy
        import tempfile

        payload = {
            "schema": run_checks.MAP_SCHEMA,
            "checks": {
                "first": {
                    "title": "First",
                    "argv": ["python3", "-c", "pass"],
                    "cwd": ".",
                    "kind": "suite",
                    "group": "chain",
                },
                "second": {
                    "title": "Second",
                    "argv": ["python3", "-c", "pass"],
                    "cwd": ".",
                    "kind": "lint",
                    "group": "chain",
                },
            },
            "groups": {"chain": {"title": "Chain", "ordered": ["first", "second"]}},
            "scopes": {"one": {"title": "One", "checks": ["first", "second"]}},
            "dependencies": {},
            "owners": [{"path": "src", "scope": "one"}],
        }
        mutations = {
            "top level": lambda body: body.update(dependecies={}),
            "check": lambda body: body["checks"]["first"].update(jobs_falg="--jobs"),
            "group": lambda body: body["groups"]["chain"].update(ordred=["first", "second"]),
            "scope": lambda body: body["scopes"]["one"].update(cheks=["first", "second"]),
            "owner": lambda body: body["owners"][0].update(scpoe="one"),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, mutate in mutations.items():
                with self.subTest(level=name):
                    candidate = copy.deepcopy(payload)
                    mutate(candidate)
                    (root / "map.json").write_text(json.dumps(candidate), encoding="utf-8")
                    with self.assertRaises(run_checks.PlanError) as caught:
                        run_checks.load_map(root, "map.json")
                    self.assertEqual(caught.exception.code, "map-invalid")

    def test_kind_is_a_closed_enum(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._map_with(tmp, {"kind": "sutie"})
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.load_map(root, "map.json")
            self.assertEqual(caught.exception.code, "map-invalid")


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

    def test_persisted_report_matches_the_emitted_record(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = TemporaryRepositoryMixin().make_repo(tmp)
            TemporaryRepositoryMixin().write_map(
                root, ["python3", "-c", "print('report')"]
            )
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            TemporaryRepositoryMixin().git(root, "add", "-A")
            TemporaryRepositoryMixin().git(root, "commit", "--quiet", "-m", "base")
            proc = TemporaryRepositoryMixin().run_cli(
                root, "--scope", "one", "--format", "json", "--report", "out/report.json"
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            emitted = json.loads(proc.stdout)
            persisted = json.loads((root / "out" / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(persisted, emitted)

    def test_nothing_selected_still_writes_the_requested_report(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            helper = TemporaryRepositoryMixin()
            root = helper.make_repo(tmp)
            helper.write_map(root, ["python3", "-c", "pass"])
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            helper.git(root, "add", "-A")
            helper.git(root, "commit", "--quiet", "-m", "base")
            proc = helper.run_cli(
                root, "--format", "json", "--report", "out/nothing-selected.json"
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            emitted = json.loads(proc.stdout)
            self.assertEqual(emitted["outcome"], "nothing-selected")
            target = root / "out" / "nothing-selected.json"
            self.assertTrue(target.is_file())
            self.assertEqual(json.loads(target.read_text(encoding="utf-8")), emitted)


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


class _PathAuthorityCases:
    """Creation, execution and cleanup stay descriptor-bound to owned paths.

    Round 8 findings S2-R8-17, S2-R8-18 and S2-R8-20: a declared cwd must
    bind to the exact validated snapshot directory, the runner parent must be
    proved component by component at creation, and cleanup must remove only
    the identical tree this runner created.
    """

    def _probe_check(self, cwd: str) -> "run_checks.Check":
        return run_checks.Check(
            id="probe",
            title="Probe",
            argv=("python3", "-c", "import os, sys; sys.stdout.write(os.getcwd())"),
            cwd=cwd,
            kind="command",
            script=None,
            jobs_flag=None,
            requires_executable=None,
            group=None,
            order=0,
            timeout_seconds=60,
        )

    def test_a_symlinked_declared_cwd_refuses_instead_of_escaping(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            outside = Path(tmp) / "outside"
            outside.mkdir()
            snapshot = Path(tmp) / "snapshot"
            snapshot.mkdir()
            (snapshot / "sub").symlink_to(outside)
            record = run_checks.run_check(
                self._probe_check("sub"), snapshot, run_checks.Scheduler(2), 1
            )
            self.assertEqual(record.get("status"), "failed")
            self.assertEqual(record.get("failure_class"), "scheduler-error")
            self.assertIn("cwd", record.get("reason", ""))

    def test_a_declared_cwd_executes_in_the_validated_directory(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "snapshot"
            (snapshot / "sub").mkdir(parents=True)
            record = run_checks.run_check(
                self._probe_check("sub"), snapshot, run_checks.Scheduler(2), 1
            )
            self.assertEqual(record.get("status"), "passed", record)
            observed = record["output"]["head"]
            self.assertEqual(
                Path(observed).resolve(), (snapshot / "sub").resolve()
            )

    def test_a_symlinked_runner_parent_refuses_snapshot_creation(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            outside = Path(tmp) / "outside"
            outside.mkdir()
            (root / "tmp").symlink_to(outside)
            nonce = "redirect" + os.urandom(5).hex()
            with self.assertRaises(run_checks.SnapshotError) as caught:
                run_checks.make_snapshot(root, nonce)
            self.assertEqual(caught.exception.code, "snapshot-error")
            self.assertEqual(
                list(outside.iterdir()), [],
                "snapshot creation escaped through a symlinked runner parent",
            )

    def test_a_substituted_snapshot_tree_is_not_removed(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            nonce = "swap" + os.urandom(5).hex()
            run_checks.make_snapshot(root, nonce)
            parent = root / run_checks.RUNNER_PARENT / nonce
            stolen = root / run_checks.RUNNER_PARENT / "stolen"
            os.rename(parent, stolen)
            substitute = parent
            substitute.mkdir()
            (substitute / run_checks.SENTINEL_NAME).write_text(
                nonce + "\n", encoding="utf-8"
            )
            victim = substitute / "victim.txt"
            victim.write_text("precious\n", encoding="utf-8")
            try:
                self.assertEqual(
                    run_checks.remove_snapshot(root, nonce),
                    "not-owned",
                    "cleanup removed a substituted tree carrying a copied sentinel",
                )
                self.assertTrue(victim.exists(), "the substitute tree was removed")
            finally:
                import shutil as _shutil

                _shutil.rmtree(stolen, ignore_errors=True)
                _shutil.rmtree(substitute, ignore_errors=True)

    def test_cleanup_still_removes_the_identical_created_tree(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            nonce = "keep" + os.urandom(5).hex()
            run_checks.make_snapshot(root, nonce)
            self.assertEqual(run_checks.remove_snapshot(root, nonce), "removed")
            self.assertFalse((root / run_checks.RUNNER_PARENT / nonce).exists())


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

    def test_automatic_capacity_takes_the_minimum_then_reserves_headroom(self) -> None:
        self.assertTrue(
            hasattr(run_checks, "capacity_plan"),
            "automatic capacity must expose the bounded planning seam",
        )
        capacity = run_checks.capacity_plan(
            None,
            item_count=12,
            signals={"affinity": 8, "cgroup_v2": 3, "os_cpu_count": 16},
        )
        self.assertEqual(capacity["usable"], 3)
        self.assertEqual(capacity["reserve"], 1)
        self.assertEqual(capacity["effective_budget"], 2)
        self.assertEqual(capacity["source"], "automatic")

    def test_cgroup_v2_capacity_follows_membership_and_ancestor_limits(self) -> None:
        self.assertTrue(
            hasattr(run_checks, "_read_small_text"),
            "cgroup discovery must use a bounded text reader",
        )
        reads = {
            "/proc/self/cgroup": "0::/tenant/job\n",
            "/proc/self/mountinfo": (
                "29 23 0:26 /tenant /cg rw,nosuid,nodev - cgroup2 cgroup rw\n"
            ),
            "/cg/job/cpu.max": "300000 100000\n",
            "/cg/cpu.max": "100000 100000\n",
        }
        real_read = run_checks._read_small_text

        def read(path, maximum=256):
            try:
                return reads[str(path)].strip()
            except KeyError as exc:
                raise OSError(str(path)) from exc

        run_checks._read_small_text = read
        self.addCleanup(lambda: setattr(run_checks, "_read_small_text", real_read))
        self.assertEqual(run_checks._cgroup_v2_capacity(), 1)

    def test_cgroup_v1_capacity_follows_the_cpu_controller_membership(self) -> None:
        self.assertTrue(
            hasattr(run_checks, "_read_small_text"),
            "cgroup discovery must use a bounded text reader",
        )
        reads = {
            "/proc/self/cgroup": "5:cpu,cpuacct:/tenant/job\n",
            "/proc/self/mountinfo": (
                "30 23 0:27 /tenant /cg1 rw - cgroup cgroup rw,cpu,cpuacct\n"
            ),
            "/cg1/job/cpu.cfs_quota_us": "400000\n",
            "/cg1/job/cpu.cfs_period_us": "100000\n",
            "/cg1/cpu.cfs_quota_us": "200000\n",
            "/cg1/cpu.cfs_period_us": "100000\n",
        }
        real_read = run_checks._read_small_text

        def read(path, maximum=256):
            try:
                return reads[str(path)].strip()
            except KeyError as exc:
                raise OSError(str(path)) from exc

        run_checks._read_small_text = read
        self.addCleanup(lambda: setattr(run_checks, "_read_small_text", real_read))
        self.assertEqual(run_checks._cgroup_v1_capacity(), 2)


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
        authority_changed = {
            "scripts/run_checks.py", "tests/check-map-v1.json"
        }.intersection(payload["changed_paths"])
        if authority_changed:
            self.assertEqual(
                payload["omitted_checks"], [],
                "a runner/map change must force complete self-audit",
            )
        else:
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

    def test_a_mutable_base_name_is_pinned_to_one_commit(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            base_commit = subprocess.run(
                ["git", "rev-parse", "HEAD"], cwd=str(root), capture_output=True,
                text=True, check=True, shell=False,
            ).stdout.strip()
            self.git(root, "branch", "comparison-base", base_commit)
            (root / "src" / "later.txt").write_text("later\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "later")

            check_map = run_checks.load_map(root)
            first = run_checks.build_selection(
                root, check_map, [], "comparison-base", False
            )
            self.assertEqual(first.base, base_commit)
            self.assertIn("src/later.txt", first.changed_paths)

            self.git(root, "branch", "-f", "comparison-base", "HEAD")
            retry = run_checks.build_selection(
                root, check_map, [], first.base, False
            )
            self.assertEqual(retry.base, base_commit)
            self.assertIn(
                "src/later.txt", retry.changed_paths,
                "a retry re-resolved the mutable name instead of retaining the pinned base",
            )


class SnapshotFidelityTests(TemporaryRepositoryMixin, unittest.TestCase):
    """The immutable attempt includes every supported untracked object."""

    def _committed_repo(self, tmp: str) -> Path:
        root = self.make_repo(tmp)
        self.write_map(root, ["python3", "-c", "pass"])
        self.git(root, "add", "-A")
        self.git(root, "commit", "--quiet", "-m", "base")
        return root

    def test_a_safe_untracked_symlink_is_recreated_in_the_snapshot(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            (root / "src" / "link.txt").symlink_to("kept.txt")
            nonce = "symlink" + os.urandom(5).hex()
            try:
                snapshot = run_checks.make_snapshot(root, nonce)
                copied = snapshot / "src" / "link.txt"
                self.assertTrue(copied.is_symlink())
                self.assertEqual(os.readlink(copied), "kept.txt")
            finally:
                run_checks.remove_snapshot(root, nonce)

    def test_source_identity_binds_an_untracked_symlink_target(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            link = root / "src" / "link.txt"
            link.symlink_to("kept.txt")
            before = run_checks.source_identity(root)
            link.unlink()
            link.symlink_to("doomed.txt")
            after = run_checks.source_identity(root)
            self.assertNotEqual(before, after)

    def test_an_untracked_symlink_outside_the_repository_refuses(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            (root / "src" / "link.txt").symlink_to("../../outside")
            nonce = "escape" + os.urandom(5).hex()
            try:
                with self.assertRaises(run_checks.SnapshotError) as caught:
                    run_checks.make_snapshot(root, nonce)
                self.assertEqual(caught.exception.code, "snapshot-error")
            finally:
                run_checks.remove_snapshot(root, nonce)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is not available")
    def test_an_untracked_special_file_refuses_the_snapshot(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            os.mkfifo(root / "src" / "pipe")
            nonce = "special" + os.urandom(5).hex()
            try:
                with self.assertRaises(run_checks.SnapshotError) as caught:
                    run_checks.make_snapshot(root, nonce)
                self.assertEqual(caught.exception.code, "snapshot-error")
            finally:
                run_checks.remove_snapshot(root, nonce)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is not available")
    def test_an_ignored_special_file_is_outside_the_snapshot(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            (root / ".gitignore").write_text("src/ignored-pipe\n", encoding="utf-8")
            self.git(root, "add", ".gitignore")
            self.git(root, "commit", "--quiet", "-m", "ignore fixture")
            os.mkfifo(root / "src" / "ignored-pipe")
            nonce = "ignored" + os.urandom(5).hex()
            try:
                snapshot = run_checks.make_snapshot(root, nonce)
                self.assertFalse((snapshot / "src" / "ignored-pipe").exists())
            finally:
                run_checks.remove_snapshot(root, nonce)


class SourceAuthorityTests(TemporaryRepositoryMixin, unittest.TestCase):
    """The bytes the snapshot executes are the bytes the identity binds.

    Round 8 findings S2-R8-09 through S2-R8-14: content capture must never
    pass through a Git clean filter, textconv or external-diff helper, must
    survive non-UTF-8 tracked bytes exactly, must carry the staged index into
    the snapshot, and must refuse a snapshot whose source moved between the
    bound identity and construction.
    """

    def _committed_repo(self, tmp: str) -> Path:
        root = self.make_repo(tmp)
        self.write_map(root, ["python3", "-c", "pass"])
        self.git(root, "add", "-A")
        self.git(root, "commit", "--quiet", "-m", "base")
        return root

    def test_a_clean_filter_cannot_hide_changed_tracked_bytes(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            masked = root / "src" / "masked.txt"
            masked.write_text("original\n", encoding="utf-8")
            (root / ".gitattributes").write_text(
                "src/masked.txt filter=hider\n", encoding="utf-8"
            )
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            original_copy = Path(tmp) / "original.bin"
            original_copy.write_text("original\n", encoding="utf-8")
            # The clean filter swallows the real worktree bytes and answers
            # with the committed bytes, so every content question routed
            # through Git conversion reports the file unchanged.
            self.git(
                root, "config", "filter.hider.clean",
                f"cat >/dev/null; cat '{original_copy}'",
            )
            before = run_checks.source_identity(root)
            masked.write_text("tampered\n", encoding="utf-8")
            after = run_checks.source_identity(root)
            self.assertNotEqual(
                before, after,
                "a clean filter hid changed tracked bytes from the identity",
            )
            nonce = "hider" + os.urandom(5).hex()
            try:
                snapshot = run_checks.make_snapshot(root, nonce)
                self.assertEqual(
                    (snapshot / "src" / "masked.txt").read_bytes(),
                    b"tampered\n",
                    "the snapshot executed bytes a clean filter substituted",
                )
            finally:
                run_checks.remove_snapshot(root, nonce)

    def test_diff_helpers_never_execute_during_capture(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            sentinel = Path(tmp) / "helper-ran"
            helper = Path(tmp) / "external-diff.sh"
            helper.write_text(
                f"#!/bin/sh\n: > '{sentinel}'\nexit 0\n", encoding="utf-8"
            )
            helper.chmod(0o755)
            self.git(root, "config", "diff.external", str(helper))
            (root / "src" / "kept.txt").write_text("changed\n", encoding="utf-8")
            run_checks.source_identity(root)
            nonce = "helper" + os.urandom(5).hex()
            try:
                run_checks.make_snapshot(root, nonce)
            except run_checks.SnapshotError:
                pass
            finally:
                run_checks.remove_snapshot(root, nonce)
            self.assertFalse(
                sentinel.exists(),
                "a configured diff helper executed during source capture",
            )

    def test_non_utf8_tracked_bytes_reach_the_snapshot_exactly(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            blob = root / "src" / "blob.bin"
            blob.write_bytes(b"\x00\xff\xfe-old")
            self.git(root, "add", "src/blob.bin")
            self.git(root, "commit", "--quiet", "-m", "binary fixture")
            tampered = b"\x00\xff\xfe-new\x80"
            blob.write_bytes(tampered)
            nonce = "binary" + os.urandom(5).hex()
            try:
                snapshot = run_checks.make_snapshot(root, nonce)
                self.assertEqual(
                    (snapshot / "src" / "blob.bin").read_bytes(),
                    tampered,
                    "changed tracked binary bytes did not reach the snapshot",
                )
            finally:
                run_checks.remove_snapshot(root, nonce)

    def test_staged_index_state_is_reconstructed_in_the_snapshot(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            staged = root / "src" / "staged.txt"
            staged.write_text("staged\n", encoding="utf-8")
            self.git(root, "add", "src/staged.txt")
            staged.write_text("worktree\n", encoding="utf-8")

            def index_listing(repo: Path) -> bytes:
                return subprocess.run(
                    ["git", "ls-files", "-z", "--stage"],
                    cwd=str(repo), capture_output=True, shell=False, check=True,
                ).stdout

            nonce = "staged" + os.urandom(5).hex()
            try:
                snapshot = run_checks.make_snapshot(root, nonce)
                self.assertEqual(
                    index_listing(snapshot), index_listing(root),
                    "the snapshot index diverged from the bound source index",
                )
                self.assertEqual(
                    (snapshot / "src" / "staged.txt").read_bytes(), b"worktree\n"
                )
            finally:
                run_checks.remove_snapshot(root, nonce)

    def test_snapshot_refuses_when_source_moved_since_the_bound_identity(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            expected = run_checks.source_identity(root)
            (root / "src" / "kept.txt").write_text("moved\n", encoding="utf-8")
            nonce = "moved" + os.urandom(5).hex()
            try:
                with self.assertRaises(run_checks.SnapshotError) as caught:
                    run_checks.make_snapshot(
                        root, nonce, expected_identity=expected
                    )
                self.assertEqual(caught.exception.code, "unstable-source")
            finally:
                run_checks.remove_snapshot(root, nonce)

    def test_oversized_tracked_capture_refuses_by_name(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            real_bound = getattr(run_checks, "MAX_TRACKED_BYTES", None)
            self.assertIsNotNone(
                real_bound, "tracked content capture must declare a byte bound"
            )
            run_checks.MAX_TRACKED_BYTES = 4
            self.addCleanup(
                lambda: setattr(run_checks, "MAX_TRACKED_BYTES", real_bound)
            )
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.source_identity(root)
            self.assertEqual(caught.exception.code, "snapshot-error")


class PathAuthorityTests(TemporaryRepositoryMixin, _PathAuthorityCases, unittest.TestCase):
    """Bind the descriptor-authority cases to the repository fixture mixin."""


class HereditaryContainmentTests(unittest.TestCase):
    """No check reports green while its descendants keep working.

    Round 8 findings S2-R8-01, S2-R8-02 and S2-R8-03: a descendant that
    starts a new session, a same-group descendant that closes its output, and
    nested independent-session workers under an outer timeout must all be
    reached by the drain, and the otherwise-green path must carry a drain
    proof rather than an assumption.
    """

    ESCAPEE = (
        "import os, sys, time\n"
        "time.sleep(600)\n"
    )

    def _leader(self, *, new_session: bool, close_output: bool, linger: float) -> str:
        escapee = (
            "import os, sys, time\n"
            + ("os.close(1)\nos.close(2)\n" if close_output else "")
            + "time.sleep(600)\n"
        )
        return (
            "import os, subprocess, sys, time\n"
            f"escapee = {escapee!r}\n"
            "child = subprocess.Popen(\n"
            "    [sys.executable, '-c', escapee],\n"
            f"    start_new_session={new_session!r},\n"
            "    stdin=subprocess.DEVNULL,\n"
            + (
                "    stdout=subprocess.DEVNULL,\n    stderr=subprocess.DEVNULL,\n"
                if new_session
                else ""
            )
            + ")\n"
            "with open(sys.argv[1], 'w') as fh:\n"
            "    fh.write(str(child.pid))\n"
            f"time.sleep({linger!r})\n"
        )

    def _run_probe(self, tmp: str, *, new_session: bool, close_output: bool,
                   linger: float, timeout_seconds: int) -> tuple[dict, int]:
        snapshot = Path(tmp) / "snapshot"
        snapshot.mkdir()
        pid_file = Path(tmp) / "escapee.pid"
        check = run_checks.Check(
            id="probe",
            title="Probe",
            argv=(
                sys.executable, "-c",
                self._leader(
                    new_session=new_session,
                    close_output=close_output,
                    linger=linger,
                ),
                str(pid_file),
            ),
            cwd=".",
            kind="command",
            script=None,
            jobs_flag=None,
            requires_executable=None,
            group=None,
            order=0,
            timeout_seconds=timeout_seconds,
        )
        record = run_checks.run_check(check, snapshot, run_checks.Scheduler(2), 1)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not pid_file.exists():
            time.sleep(0.05)
        self.assertTrue(pid_file.exists(), "the leader never reported its child")
        pid = int(pid_file.read_text())
        self.addCleanup(self._reap, pid)
        return record, pid

    def _reap(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass

    def _assert_dead(self, pid: int, why: str) -> None:
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return
            except OSError:
                return
            time.sleep(0.05)
        self.fail(why)

    def test_a_new_session_descendant_cannot_outlive_a_green_leader(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            record, pid = self._run_probe(
                tmp, new_session=True, close_output=False,
                linger=0.0, timeout_seconds=60,
            )
            self.assertEqual(
                record.get("status"), "failed",
                "the runner reported green while a detached descendant worked on",
            )
            self.assertEqual(record.get("failure_class"), "scheduler-error")
            self._assert_dead(
                pid, "a new-session descendant survived the hereditary drain"
            )

    def test_a_quiet_group_survivor_is_found_on_the_green_path(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            record, pid = self._run_probe(
                tmp, new_session=False, close_output=True,
                linger=0.0, timeout_seconds=60,
            )
            self.assertEqual(
                record.get("status"), "failed",
                "no group-drain proof ran on the otherwise-green path",
            )
            self._assert_dead(
                pid, "a same-group survivor outlived the reaped leader"
            )

    def test_nested_session_workers_are_reached_by_an_outer_timeout(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            record, pid = self._run_probe(
                tmp, new_session=True, close_output=False,
                linger=600.0, timeout_seconds=3,
            )
            self.assertEqual(record.get("status"), "failed")
            self._assert_dead(
                pid,
                "an independent-session worker survived the outer timeout drain",
            )

    def test_a_clean_check_still_passes_with_a_drain_proof(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            snapshot = Path(tmp) / "snapshot"
            snapshot.mkdir()
            check = run_checks.Check(
                id="probe",
                title="Probe",
                argv=(sys.executable, "-c", "print('ok')"),
                cwd=".",
                kind="command",
                script=None,
                jobs_flag=None,
                requires_executable=None,
                group=None,
                order=0,
                timeout_seconds=60,
            )
            record = run_checks.run_check(
                check, snapshot, run_checks.Scheduler(2), 1
            )
            self.assertEqual(record.get("status"), "passed", record)
            containment = record.get("containment")
            self.assertIsInstance(
                containment, dict,
                "a green record must carry its drain proof, not an assumption",
            )
            self.assertEqual(containment.get("proof"), "drained")


class SnapshotIsolationTests(TemporaryRepositoryMixin, unittest.TestCase):
    """A run is green only if the observed source never changed under it.

    Round 8 finding S2-R8-19: parallel checks share one writable snapshot, so
    one selected check can alter source another selected check observes.  The
    run must re-verify the snapshot's bound source set after execution and
    refuse green when it moved.
    """

    def test_a_check_that_mutates_shared_source_cannot_aggregate_green(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(
                root,
                [
                    "python3", "-c",
                    "open('src/kept.txt', 'w').write('poisoned by a check')",
                ],
            )
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            emitted = json.loads(proc.stdout)
            self.assertNotEqual(
                emitted["outcome"], "green",
                "a check rewrote shared snapshot source and the run stayed green",
            )
            self.assertIn("snapshot-error", emitted.get("failure_classes", []))
            verification = emitted.get("snapshot_sources")
            self.assertIsInstance(verification, dict)
            self.assertEqual(verification.get("status"), "mutated")
            self.assertIn("src/kept.txt", verification.get("mutated", []))

    def test_an_untouched_snapshot_verifies_intact(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "print('clean')"])
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            emitted = json.loads(proc.stdout)
            self.assertEqual(emitted["outcome"], "green")
            verification = emitted.get("snapshot_sources")
            self.assertIsInstance(
                verification, dict,
                "a green run must carry its source verification, not imply it",
            )
            self.assertEqual(verification.get("status"), "intact")

    def test_new_files_a_check_creates_do_not_refute_the_run(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(
                root,
                [
                    "python3", "-c",
                    "open('artifact.out', 'w').write('a build product')",
                ],
            )
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            proc = self.run_cli(root, "--scope", "one", "--format", "json")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            emitted = json.loads(proc.stdout)
            self.assertEqual(
                emitted["outcome"], "green",
                "a new build artifact is not a mutation of observed source",
            )


class ReportEntryIdentityTests(unittest.TestCase):
    """The persisted report entry is the exact bytes this runner wrote.

    Round 8 finding S2-R8-23: the temporary name is discoverable and
    replaceable by the same credential between close and replace, so the
    final directory entry must be proved to be the written file itself.
    """

    def test_a_substituted_final_entry_refuses_instead_of_standing(self) -> None:
        import tempfile
        from unittest import mock

        real_replace = os.replace

        def hijack(src, dst, *, src_dir_fd=None, dst_dir_fd=None):
            real_replace(src, dst, src_dir_fd=src_dir_fd, dst_dir_fd=dst_dir_fd)
            if dst_dir_fd is None or str(dst).endswith(".partial"):
                return
            attacker = f".attacker.{os.urandom(4).hex()}"
            fd = os.open(
                attacker, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644,
                dir_fd=dst_dir_fd,
            )
            try:
                os.write(fd, b'{"forged": true}\n')
            finally:
                os.close(fd)
            real_replace(attacker, dst, src_dir_fd=dst_dir_fd, dst_dir_fd=dst_dir_fd)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(run_checks.os, "replace", side_effect=hijack):
                with self.assertRaises(run_checks.PlanError) as caught:
                    run_checks.write_report(
                        root, "out/report.json", {"schema": run_checks.RUN_SCHEMA}
                    )
            self.assertEqual(caught.exception.code, "report-substituted")

    def test_an_unmolested_report_still_writes_and_verifies(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            written = run_checks.write_report(
                root, "out/report.json", {"schema": run_checks.RUN_SCHEMA}
            )
            self.assertEqual(
                json.loads((root / written).read_text())["schema"],
                run_checks.RUN_SCHEMA,
            )


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
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")

            proc = self.run_cli(
                root,
                "--scope",
                "one",
                "--format",
                "json",
                "--report",
                "out/report.json",
            )
            self.assertEqual(proc.returncode, 3, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["outcome"], "unstable-source")
            self.assertEqual(payload["failure_classes"], ["unstable-source"])
            self.assertNotIn("test-failure", payload["failure_classes"])
            self.assertEqual(
                json.loads((root / "out" / "report.json").read_text(encoding="utf-8")),
                payload,
            )

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
        # Signal 0 delivers nothing: it is the round-8 drain proof's existence
        # probe and is allowed against the group id captured at spawn.  What
        # stays forbidden is delivering a signal through a group handle once
        # the leader has been reaped.
        delivered = [entry for entry in sent if entry[1] != 0]
        self.assertEqual(
            delivered, [],
            "a stale pid's process group was signalled after the leader was reaped",
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
            if args[:2] == ("rev-parse", "HEAD"):
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

    def test_failed_detached_checkout_refuses_the_snapshot(self) -> None:
        """A clone at the wrong revision must never be accepted as immutable."""
        real_run = run_checks.subprocess.run

        def fail_checkout(argv, *args, **kwargs):
            if list(argv[:4]) == ["git", "checkout", "--quiet", "--detach"]:
                return subprocess.CompletedProcess(argv, 1, b"", b"checkout refused")
            return real_run(argv, *args, **kwargs)

        run_checks.subprocess.run = fail_checkout
        self.addCleanup(lambda: setattr(run_checks.subprocess, "run", real_run))
        root = run_checks.repository_root()
        nonce = "checkout" + os.urandom(5).hex()
        try:
            with self.assertRaises(run_checks.SnapshotError) as caught:
                run_checks.make_snapshot(root, nonce)
            self.assertEqual(caught.exception.code, "snapshot-error")
            self.assertIn("checkout", caught.exception.message)
        finally:
            run_checks.remove_snapshot(root, nonce)


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


class RoundFiveReducedGuards(TemporaryRepositoryMixin, unittest.TestCase):
    """Two causal guards retained after the larger candidate clusters were dropped."""

    def _committed_repo(self, tmp: str) -> Path:
        root = self.make_repo(tmp)
        self.write_map(root, ["python3", "-c", "pass"])
        self.git(root, "add", "-A")
        self.git(root, "commit", "--quiet", "-m", "base")
        return root

    def test_untracked_regular_mode_is_part_of_source_identity(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            target = root / "untracked-tool"
            target.write_bytes(b"#!/bin/sh\nexit 0\n")
            target.chmod(0o644)
            before = run_checks.source_identity(root)
            target.chmod(0o755)
            self.assertNotEqual(
                run_checks.source_identity(root),
                before,
                "source identity omitted the executable mode replayed into the snapshot",
            )

    def test_untracked_special_mode_bits_are_normalized_to_replayed_permissions(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            target = root / "untracked-tool"
            target.write_bytes(b"#!/bin/sh\nexit 0\n")
            target.chmod(0o4755)
            if target.stat().st_mode & 0o7000 != 0o4000:
                self.skipTest("fixture filesystem does not retain set-id mode bits")
            before = run_checks.source_identity(root)
            nonce = "mode" + os.urandom(5).hex()
            try:
                snapshot = run_checks.make_snapshot(root, nonce)
                copied = snapshot / "untracked-tool"
                self.assertEqual(copied.stat().st_mode & 0o7777, 0o755)
                self.assertEqual(run_checks.source_identity(snapshot), before)
            finally:
                run_checks.remove_snapshot(root, nonce)

    def test_untracked_symlink_mode_is_outside_replayed_identity(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self._committed_repo(tmp)
            link = root / "untracked-link"
            link.symlink_to("src/kept.txt")
            lchmod = getattr(os, "lchmod", None)
            if lchmod is None:
                self.skipTest("fixture platform cannot change symlink permissions")
            lchmod(link, 0o700)
            source_mode = link.lstat().st_mode & 0o777
            before = run_checks.source_identity(root)
            nonce = "linkmode" + os.urandom(5).hex()
            try:
                snapshot = run_checks.make_snapshot(root, nonce)
                copied = snapshot / "untracked-link"
                replayed_mode = copied.lstat().st_mode & 0o777
                if replayed_mode == source_mode:
                    self.skipTest("fixture filesystem replayed the same symlink mode")
                self.assertEqual(run_checks.source_identity(snapshot), before)
            finally:
                run_checks.remove_snapshot(root, nonce)

    def test_capture_eio_is_not_treated_as_eof(self) -> None:
        proc = subprocess.Popen(
            [sys.executable, "-c", "print('evidence')"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        real_read = os.read

        def eio(fd: int, size: int) -> bytes:
            raise OSError(errno.EIO, "injected capture fault")

        os.read = eio
        try:
            try:
                run_checks._capture_output(
                    proc, run_checks.CaptureBuffer(), time.monotonic() + 10
                )
            except OSError as exc:
                self.assertEqual(exc.errno, errno.EIO)
            else:
                self.fail("capture EIO was accepted as ordinary EOF")
        finally:
            os.read = real_read
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)
            if proc.stdout is not None:
                proc.stdout.close()

    def test_capture_eio_is_reported_as_a_scheduler_error(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            check = run_checks.Check(
                id="capture",
                title="Capture",
                argv=(sys.executable, "-c", "print('evidence')"),
                cwd=".",
                kind="lint",
                script=None,
                jobs_flag=None,
                requires_executable=None,
                group=None,
                order=0,
                timeout_seconds=10,
            )
            real_capture = run_checks._capture_output

            def eio(*args, **kwargs):
                raise OSError(errno.EIO, "injected capture fault")

            run_checks._capture_output = eio
            try:
                record = run_checks.run_check(
                    check, Path(tmp), run_checks.Scheduler(2), 1
                )
            finally:
                run_checks._capture_output = real_capture
            self.assertEqual(record.get("status"), "failed")
            self.assertEqual(record.get("failure_class"), "scheduler-error")
            self.assertIn("capture", record.get("reason", ""))


class RoundSixBoundedGuards(TemporaryRepositoryMixin, unittest.TestCase):
    """Small fail-closed guards that do not depend on the open containment design."""

    def test_cleanup_disposition_cannot_leave_an_otherwise_green_run_green(self) -> None:
        import contextlib
        import io
        import tempfile

        for disposition in ("retained", "not-owned"):
            with self.subTest(disposition=disposition), tempfile.TemporaryDirectory() as tmp:
                root = self.make_repo(tmp)
                self.write_map(root, ["python3", "-c", "pass"])
                self.git(root, "add", "-A")
                self.git(root, "commit", "--quiet", "-m", "base")
                real_remove = run_checks.remove_snapshot

                def failed_cleanup(repo: Path, nonce: str) -> str:
                    real_remove(repo, nonce)
                    return disposition

                previous = Path.cwd()
                run_checks.remove_snapshot = failed_cleanup
                stream = io.StringIO()
                try:
                    os.chdir(root)
                    with contextlib.redirect_stdout(stream):
                        code = run_checks.main(["--scope", "one", "--format", "json"])
                finally:
                    os.chdir(previous)
                    run_checks.remove_snapshot = real_remove
                report = json.loads(stream.getvalue())
                self.assertEqual(code, 1)
                self.assertEqual(report["outcome"], "red")
                self.assertEqual(report["snapshot_cleanup"], disposition)
                self.assertIn("snapshot-error", report["failure_classes"])

    def test_stdout_eof_does_not_shorten_the_declared_check_timeout(self) -> None:
        check = run_checks.Check(
            id="early-eof",
            title="Early EOF",
            argv=(
                sys.executable,
                "-c",
                "import os,time;os.close(1);os.close(2);time.sleep(0.25)",
            ),
            cwd=".",
            kind="lint",
            script=None,
            jobs_flag=None,
            requires_executable=None,
            group=None,
            order=0,
            timeout_seconds=2,
        )
        real_drain = run_checks.DRAIN_SECONDS
        run_checks.DRAIN_SECONDS = 0.03
        try:
            record = run_checks.run_check(
                check, Path.cwd(), run_checks.Scheduler(1), 1
            )
        finally:
            run_checks.DRAIN_SECONDS = real_drain
        self.assertEqual(record.get("status"), "passed", record)
        self.assertGreaterEqual(record.get("duration_seconds", 0), 0.2)

    def test_unhashable_group_value_refuses_as_a_named_map_error(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "schema": run_checks.MAP_SCHEMA,
                "checks": {
                    "probe": {
                        "argv": ["python3", "-c", "pass"],
                        "group": {"not": "a string"},
                    }
                },
                "groups": {},
                "scopes": {"one": {"checks": ["probe"]}},
                "dependencies": {},
                "owners": [{"path": "src", "scope": "one"}],
            }
            (root / "map.json").write_text(json.dumps(payload), encoding="utf-8")
            try:
                run_checks.load_map(root, "map.json")
            except BaseException as exc:
                self.assertIsInstance(exc, run_checks.PlanError)
                self.assertEqual(exc.code, "map-invalid")
            else:
                self.fail("an unhashable group value was accepted")

    def test_unhashable_references_refuse_as_named_map_errors(self) -> None:
        import copy
        import tempfile

        base = {
            "schema": run_checks.MAP_SCHEMA,
            "checks": {"probe": {"argv": ["python3", "-c", "pass"]}},
            "groups": {},
            "scopes": {"one": {"checks": ["probe"]}},
            "dependencies": {},
            "owners": [{"path": "src", "scope": "one"}],
        }
        mutations = {
            "group member": lambda body: body.update(
                groups={"ordered": {"ordered": [{"not": "a check id"}]}}
            ),
            "scope check": lambda body: body.update(
                scopes={"one": {"checks": [{"not": "a check id"}]}}
            ),
            "dependency consumer": lambda body: body.update(
                dependencies={"one": [{"not": "a scope id"}]}
            ),
            "owner path": lambda body: body.update(
                owners=[{"path": {"not": "a path"}, "scope": "one"}]
            ),
            "owner scope": lambda body: body.update(
                owners=[{"path": "src", "scope": {"not": "a scope id"}}]
            ),
        }
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, mutate in mutations.items():
                with self.subTest(field=name):
                    payload = copy.deepcopy(base)
                    mutate(payload)
                    (root / "map.json").write_text(json.dumps(payload), encoding="utf-8")
                    try:
                        run_checks.load_map(root, "map.json")
                    except BaseException as exc:
                        self.assertIsInstance(exc, run_checks.PlanError)
                        self.assertEqual(exc.code, "map-invalid")
                    else:
                        self.fail(f"unhashable {name} was accepted")

    def test_every_check_must_be_reachable_from_at_least_one_scope(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "schema": run_checks.MAP_SCHEMA,
                "checks": {
                    "selected": {"argv": ["python3", "-c", "pass"]},
                    "orphan": {"argv": ["python3", "-c", "raise SystemExit(1)"]},
                },
                "groups": {},
                "scopes": {"one": {"checks": ["selected"]}},
                "dependencies": {},
                "owners": [{"path": "src", "scope": "one"}],
            }
            (root / "map.json").write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.load_map(root, "map.json")
            self.assertEqual(caught.exception.code, "map-invalid")

    def test_a_scope_cannot_select_only_part_of_an_ordered_group(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "schema": run_checks.MAP_SCHEMA,
                "checks": {
                    "first": {"argv": ["python3", "-c", "pass"], "group": "ordered"},
                    "second": {"argv": ["python3", "-c", "pass"], "group": "ordered"},
                },
                "groups": {"ordered": {"ordered": ["first", "second"]}},
                "scopes": {
                    "partial": {"checks": ["second"]},
                    "complete": {"checks": ["first", "second"]},
                },
                "dependencies": {},
                "owners": [{"path": "src", "scope": "partial"}],
            }
            (root / "map.json").write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.load_map(root, "map.json")
            self.assertEqual(caught.exception.code, "map-invalid")


class RoundEightBoundedGuards(TemporaryRepositoryMixin, unittest.TestCase):
    """Parent-red guards for independently bounded round-eight fixes."""

    def test_runner_and_map_authority_changes_select_every_declared_check(self) -> None:
        check_map = run_checks.load_map(REPO_ROOT)
        expected = set(check_map.checks)
        for authority_path in ("scripts/run_checks.py", "tests/check-map-v1.json"):
            with self.subTest(path=authority_path):
                selection = run_checks.build_selection(
                    REPO_ROOT,
                    check_map,
                    [],
                    None,
                    False,
                    observed=[authority_path],
                )
                selected = {check.id for check in run_checks.selected_checks(check_map, selection)}
                self.assertEqual(
                    selected,
                    expected,
                    "changing execution authority did not select every governed check",
                )

    def test_an_ignored_custom_map_cannot_escape_source_identity(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            ignored_map = root / "ignored" / "check-map.json"
            ignored_map.parent.mkdir()
            ignored_map.write_bytes((root / "tests" / "check-map-v1.json").read_bytes())

            proc = self.run_cli(
                root,
                "--scope",
                "one",
                "--plan",
                "--format",
                "json",
                "--map",
                "ignored/check-map.json",
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["code"], "map-untracked")

    def test_map_tracking_probe_treats_the_name_as_a_literal_path(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            (root / ".gitignore").write_text("ignored/\n", encoding="utf-8")
            ignored = root / "ignored"
            ignored.mkdir()
            body = (root / "tests" / "check-map-v1.json").read_bytes()
            (ignored / "tracked.json").write_bytes(body)
            self.git(root, "add", "-A")
            self.git(root, "add", "-f", "ignored/tracked.json")
            self.git(root, "commit", "--quiet", "-m", "base")
            (ignored / "*.json").write_bytes(body)

            proc = self.run_cli(
                root,
                "--scope",
                "one",
                "--plan",
                "--format",
                "json",
                "--map",
                "ignored/*.json",
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["code"], "map-untracked")

    def test_map_tracking_probe_requires_an_exact_index_entry(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            body = (root / "tests" / "check-map-v1.json").read_bytes()
            authority = root / "authority"
            authority.mkdir()
            decoy = authority / "child.json"
            decoy.write_bytes(body)
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            decoy.unlink()
            authority.rmdir()
            authority.write_bytes(body)

            check_map = run_checks.load_map(root, "authority")
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.require_tracked_map(root, check_map)
            self.assertEqual(caught.exception.code, "map-untracked")

    def test_a_retry_reloads_the_map_instead_of_reusing_stale_authority(self) -> None:
        import argparse
        from unittest import mock

        check_map = run_checks.load_map(REPO_ROOT)
        selection = run_checks.build_selection(
            REPO_ROOT, check_map, ["root"], None, False, observed=[]
        )
        checks = run_checks.selected_checks(check_map, selection)
        capacity = run_checks.capacity_plan(1, run_checks._runnable_slot_cap(checks))
        plan = run_checks.plan_record(check_map, selection, checks, capacity)
        args = argparse.Namespace(
            scope=["root"], base=None, full=False, report=None, format="json",
            jobs=1, map=run_checks.DEFAULT_MAP_PATH,
        )
        identities = iter(("first", "moved", "second", "second", "second"))
        reloads: list[str] = []
        executions: list[list[str]] = []

        def reload_map(root: Path, map_path: str = run_checks.DEFAULT_MAP_PATH):
            reloads.append(map_path)
            return check_map

        def execute_once(selected, snapshot, budget):
            executions.append([check.id for check in selected])
            return [], run_checks.Scheduler(budget)

        with (
            mock.patch.object(run_checks, "source_identity", side_effect=lambda root: next(identities)),
            mock.patch.object(
                run_checks,
                "make_snapshot",
                side_effect=lambda root, nonce, expected_identity=None: root,
            ),
            mock.patch.object(
                run_checks,
                "execute",
                side_effect=execute_once,
            ),
            mock.patch.object(run_checks, "remove_snapshot", return_value="removed"),
            mock.patch.object(run_checks, "load_map", side_effect=reload_map),
            mock.patch.object(run_checks, "changed_paths", return_value=[]),
            mock.patch.object(run_checks, "emit"),
        ):
            run_checks._run_attempts(
                args, REPO_ROOT, check_map, selection, checks, capacity, plan, []
            )
        self.assertEqual(
            reloads,
            [run_checks.DEFAULT_MAP_PATH, run_checks.DEFAULT_MAP_PATH],
            "each attempt must reload its authority inside the identity bracket",
        )
        self.assertEqual(len(executions), 1, "stale authority executed before retry")

    def test_an_outside_map_path_is_refused_before_it_is_read(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            root = base / "repo"
            root.mkdir()
            outside = base / "outside.json"
            outside.write_text(
                json.dumps(
                    {
                        "schema": run_checks.MAP_SCHEMA,
                        "checks": {"probe": {"argv": ["python3", "-c", "pass"]}},
                        "groups": {},
                        "scopes": {"one": {"checks": ["probe"]}},
                        "dependencies": {},
                        "owners": [{"path": "src", "scope": "one"}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.load_map(root, "../outside.json")
            self.assertEqual(caught.exception.code, "unsafe-path")

    def test_map_read_identity_includes_ctime(self) -> None:
        import tempfile
        from types import SimpleNamespace
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "schema": run_checks.MAP_SCHEMA,
                "checks": {"probe": {"argv": ["python3", "-c", "pass"]}},
                "groups": {},
                "scopes": {"one": {"checks": ["probe"]}},
                "dependencies": {},
                "owners": [{"path": "src", "scope": "one"}],
            }
            (root / "map.json").write_text(json.dumps(payload), encoding="utf-8")
            real_fstat = os.fstat
            regular_reads = {"count": 0}

            def changed_ctime(fd: int):
                info = real_fstat(fd)
                if not stat.S_ISREG(info.st_mode):
                    return info
                regular_reads["count"] += 1
                return SimpleNamespace(
                    st_mode=info.st_mode,
                    st_dev=info.st_dev,
                    st_ino=info.st_ino,
                    st_size=info.st_size,
                    st_mtime_ns=info.st_mtime_ns,
                    st_ctime_ns=info.st_ctime_ns + (regular_reads["count"] - 1),
                )

            with (
                mock.patch.object(os, "fstat", side_effect=changed_ctime),
                self.assertRaises(run_checks.PlanError) as caught,
            ):
                run_checks.load_map(root, "map.json")
            self.assertEqual(caught.exception.code, "map-unreadable")

    def test_a_command_only_check_still_validates_its_cwd(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            payload = {
                "schema": run_checks.MAP_SCHEMA,
                "checks": {
                    "probe": {
                        "argv": ["python3", "-c", "pass"],
                        "cwd": "missing",
                        "kind": "command",
                    }
                },
                "groups": {},
                "scopes": {"one": {"checks": ["probe"]}},
                "dependencies": {},
                "owners": [{"path": "src", "scope": "one"}],
            }
            (root / "map.json").write_text(json.dumps(payload), encoding="utf-8")
            check_map = run_checks.load_map(root, "map.json")
            with self.assertRaises(run_checks.PlanError) as caught:
                run_checks.refuse_stale_commands(root, check_map)
            self.assertEqual(caught.exception.code, "stale-command")

    def test_nested_allocation_reserves_one_slot_for_its_coordinator(self) -> None:
        check = run_checks.Check(
            id="nested",
            title="Nested",
            argv=(sys.executable, "-c", "import sys; print(sys.argv[-1])"),
            cwd=".",
            kind="suite",
            script=None,
            jobs_flag="--jobs",
            requires_executable=None,
            group=None,
            order=0,
            timeout_seconds=10,
        )
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(6), 1)
        self.assertEqual(record["status"], "passed", record)
        self.assertEqual(record["slots"], 6)
        self.assertEqual(record["nested_allocation"], 5)
        self.assertIn("5", record["output"]["head"].splitlines())

    def test_budget_one_refuses_a_nested_coordinator_before_launch(self) -> None:
        check = run_checks.Check(
            id="nested",
            title="Nested",
            argv=(sys.executable, "-c", "raise SystemExit(99)"),
            cwd=".",
            kind="suite",
            script=None,
            jobs_flag="--jobs",
            requires_executable=None,
            group=None,
            order=0,
            timeout_seconds=10,
        )
        record = run_checks.run_check(check, REPO_ROOT, run_checks.Scheduler(1), 1)
        self.assertEqual(record.get("failure_class"), "scheduler-error", record)
        self.assertIn("two process slots", record.get("reason", ""))
        self.assertNotIn("exit_code", record, "the nested coordinator was launched")

    def test_a_later_thread_start_fault_waits_for_started_work_and_accounts_all(self) -> None:
        from unittest import mock

        checks = [
            run_checks.Check(
                id=f"probe-{index}", title=f"Probe {index}", argv=("true",), cwd=".",
                kind="lint", script=None, jobs_flag=None, requires_executable=None,
                group=None, order=0, timeout_seconds=10,
            )
            for index in range(2)
        ]
        real_start = threading.Thread.start
        starts = {"count": 0}

        def fail_second(thread: threading.Thread) -> None:
            starts["count"] += 1
            if starts["count"] == 2:
                raise RuntimeError("thread launch refused")
            real_start(thread)

        def bounded_work(check, snapshot, scheduler, parallel_checks):
            time.sleep(0.12)
            return {"check": check.id, "title": check.title, "status": "passed"}

        started = time.monotonic()
        with (
            mock.patch.object(run_checks, "run_check", side_effect=bounded_work),
            mock.patch.object(threading.Thread, "start", new=fail_second),
        ):
            results, _ = run_checks.execute(checks, REPO_ROOT, 2)
        self.assertGreaterEqual(time.monotonic() - started, 0.1)
        self.assertEqual({record["check"] for record in results}, {"probe-0", "probe-1"})
        self.assertTrue(any(record.get("failure_class") == "scheduler-error" for record in results))

    def test_start_cancellation_drains_started_work_then_propagates(self) -> None:
        from unittest import mock

        checks = [
            run_checks.Check(
                id=f"probe-{index}", title=f"Probe {index}", argv=("true",), cwd=".",
                kind="lint", script=None, jobs_flag=None, requires_executable=None,
                group=None, order=0, timeout_seconds=10,
            )
            for index in range(2)
        ]
        real_start = threading.Thread.start
        starts = {"count": 0}

        def cancel_second(thread: threading.Thread) -> None:
            starts["count"] += 1
            if starts["count"] == 2:
                raise KeyboardInterrupt("cancel launch")
            real_start(thread)

        def bounded_work(check, snapshot, scheduler, parallel_checks):
            time.sleep(0.12)
            return {"check": check.id, "title": check.title, "status": "passed"}

        started = time.monotonic()
        with (
            mock.patch.object(run_checks, "run_check", side_effect=bounded_work),
            mock.patch.object(threading.Thread, "start", new=cancel_second),
            self.assertRaises(KeyboardInterrupt),
        ):
            run_checks.execute(checks, REPO_ROOT, 2)
        self.assertGreaterEqual(time.monotonic() - started, 0.1)

    def test_post_launch_start_fault_remains_scheduler_evidence(self) -> None:
        from unittest import mock

        check = run_checks.Check(
            id="probe", title="Probe", argv=("true",), cwd=".", kind="lint",
            script=None, jobs_flag=None, requires_executable=None, group=None,
            order=0, timeout_seconds=10,
        )
        real_start = threading.Thread.start

        def start_then_fault(thread: threading.Thread) -> None:
            real_start(thread)
            raise RuntimeError("ambiguous start result")

        def bounded_work(check, snapshot, scheduler, parallel_checks):
            time.sleep(0.05)
            return {"check": check.id, "title": check.title, "status": "passed"}

        with (
            mock.patch.object(run_checks, "run_check", side_effect=bounded_work),
            mock.patch.object(threading.Thread, "start", new=start_then_fault),
        ):
            results, _ = run_checks.execute([check], REPO_ROOT, 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].get("failure_class"), "scheduler-error")
        self.assertIn("ambiguous start result", results[0].get("reason", ""))

    def test_join_fault_does_not_escape_before_worker_completion(self) -> None:
        from unittest import mock

        check = run_checks.Check(
            id="probe", title="Probe", argv=("true",), cwd=".", kind="lint",
            script=None, jobs_flag=None, requires_executable=None, group=None,
            order=0, timeout_seconds=10,
        )

        def bounded_work(check, snapshot, scheduler, parallel_checks):
            time.sleep(0.05)
            return {"check": check.id, "title": check.title, "status": "passed"}

        with (
            mock.patch.object(run_checks, "run_check", side_effect=bounded_work),
            mock.patch.object(threading.Thread, "join", side_effect=RuntimeError("join fault")),
        ):
            results, _ = run_checks.execute([check], REPO_ROOT, 1)
        self.assertEqual(results, [{"check": "probe", "title": "Probe", "status": "passed"}])

    def test_duplicate_terminal_records_are_not_accepted_as_exact_once(self) -> None:
        from unittest import mock

        checks = [
            run_checks.Check(
                id=f"probe-{index}", title=f"Probe {index}", argv=("true",), cwd=".",
                kind="lint", script=None, jobs_flag=None, requires_executable=None,
                group=None, order=0, timeout_seconds=10,
            )
            for index in range(2)
        ]

        def duplicate(check, snapshot, scheduler, parallel_checks):
            return {"check": "probe-0", "title": check.title, "status": "passed"}

        with mock.patch.object(run_checks, "run_check", side_effect=duplicate):
            results, _ = run_checks.execute(checks, REPO_ROOT, 2)
        self.assertEqual([record["check"] for record in results], ["probe-0", "probe-1"])
        self.assertTrue(
            all(record.get("failure_class") == "scheduler-error" for record in results),
            results,
        )
        self.assertIn("duplicate", results[0].get("reason", ""))

    def test_foreign_terminal_record_cannot_join_the_selected_union(self) -> None:
        from unittest import mock

        check = run_checks.Check(
            id="probe", title="Probe", argv=("true",), cwd=".", kind="lint",
            script=None, jobs_flag=None, requires_executable=None, group=None,
            order=0, timeout_seconds=10,
        )
        with mock.patch.object(
            run_checks,
            "run_check",
            return_value={"check": "foreign", "title": "Foreign", "status": "passed"},
        ):
            results, _ = run_checks.execute([check], REPO_ROOT, 1)
        self.assertEqual([record["check"] for record in results], ["probe"])
        self.assertEqual(results[0].get("failure_class"), "scheduler-error")
        self.assertIn("foreign", results[0].get("reason", ""))

    def test_report_target_must_be_ignored_and_cannot_overwrite_source(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            target = root / "src" / "kept.txt"
            before = target.read_bytes()
            proc = self.run_cli(
                root, "--scope", "one", "--format", "json", "--report", "src/kept.txt"
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(target.read_bytes(), before)
            self.assertEqual(json.loads(proc.stdout)["outcome"], "refused")

            unowned = root / "report.json"
            proc = self.run_cli(
                root, "--scope", "one", "--format", "json", "--report", "report.json"
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertFalse(unowned.exists())
            self.assertEqual(json.loads(proc.stdout)["outcome"], "refused")

    def test_report_ownership_git_probe_error_refuses(self) -> None:
        from types import SimpleNamespace
        from unittest import mock

        with (
            mock.patch.object(
                run_checks.subprocess,
                "run",
                side_effect=(
                    SimpleNamespace(returncode=128, stdout=b"", stderr=b"index corrupt"),
                    SimpleNamespace(returncode=0, stdout=b"", stderr=b""),
                ),
            ),
            self.assertRaises(run_checks.PlanError) as caught,
        ):
            run_checks.require_ignored_report_path(REPO_ROOT, ".elenchus/probe.json")
        self.assertEqual(caught.exception.code, "git-failed")

        with (
            mock.patch.object(
                run_checks.subprocess,
                "run",
                side_effect=(
                    SimpleNamespace(returncode=1, stdout=b"", stderr=b""),
                    SimpleNamespace(returncode=128, stdout=b"", stderr=b"ignore corrupt"),
                ),
            ),
            self.assertRaises(run_checks.PlanError) as caught,
        ):
            run_checks.require_ignored_report_path(REPO_ROOT, ".elenchus/probe.json")
        self.assertEqual(caught.exception.code, "git-failed")

    def test_initial_incomplete_report_survives_an_unhandled_cancellation(self) -> None:
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            with (
                mock.patch.object(run_checks, "repository_root", return_value=root),
                mock.patch.object(
                    run_checks, "_run_attempts", side_effect=KeyboardInterrupt("cancelled")
                ),
                self.assertRaises(KeyboardInterrupt),
            ):
                run_checks.main(
                    ["--scope", "one", "--format", "json", "--report", "out/report.json"]
                )
            payload = json.loads((root / "out" / "report.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["outcome"], "incomplete")

    def test_refusal_replaces_a_prior_green_report(self) -> None:
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            root = self.make_repo(tmp)
            self.write_map(root, ["python3", "-c", "pass"])
            (root / ".gitignore").write_text("out/\n", encoding="utf-8")
            self.git(root, "add", "-A")
            self.git(root, "commit", "--quiet", "-m", "base")
            target = root / "out" / "report.json"
            target.parent.mkdir()
            target.write_text(
                json.dumps({"schema": run_checks.RUN_SCHEMA, "outcome": "green"}),
                encoding="utf-8",
            )
            proc = self.run_cli(
                root, "--scope", "missing", "--format", "json", "--report", "out/report.json"
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            self.assertEqual(json.loads(target.read_text(encoding="utf-8"))["outcome"], "refused")

    def test_report_write_uses_the_opened_parent_after_path_rebinding(self) -> None:
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "repo"
            outside = Path(tmp) / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "out").mkdir()
            real_open = run_checks._open_confined_directory
            swapped = {"done": False}

            def open_then_swap(repo: Path, parts, *, create: bool) -> int:
                fd = real_open(repo, parts, create=create)
                if tuple(parts) == ("out",) and not swapped["done"]:
                    (root / "out").rename(root / "held")
                    (root / "out").symlink_to(outside, target_is_directory=True)
                    swapped["done"] = True
                return fd

            with mock.patch.object(
                run_checks, "_open_confined_directory", side_effect=open_then_swap
            ):
                run_checks.write_report(root, "out/report.json", {"schema": "bound"})
            self.assertTrue((root / "held" / "report.json").is_file())
            self.assertEqual(list(outside.iterdir()), [])

    def test_failed_report_replacement_removes_its_partial(self) -> None:
        import tempfile
        from unittest import mock

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with (
                mock.patch.object(os, "replace", side_effect=OSError("replace refused")),
                self.assertRaises(OSError),
            ):
                run_checks.write_report(root, "out/report.json", {"schema": "x"})
            leftovers = list((root / "out").glob("*.partial")) + list(
                (root / "out").glob(".*.partial")
            )
            self.assertEqual(leftovers, [])
