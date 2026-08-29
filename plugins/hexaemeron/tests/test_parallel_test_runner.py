"""Guards for the fresh-manifest Hexaemeron test scheduler."""

import importlib.util
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest import mock
from pathlib import Path


RUNNER = Path(__file__).with_name("run_tests.py")
SUMMARY_PREFIX = "HEXAEMERON-RUN "

spec = importlib.util.spec_from_file_location("parallel_test_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


def require_runner_features(case, *names):
    """Turn a missing parent interface into an assertion guard, not an error."""
    missing = [name for name in names if not hasattr(runner, name)]
    case.assertEqual([], missing, f"runner is missing Step 2 interfaces: {missing}")


class RunnerFixture:
    def __init__(self, files):
        self.temporary = tempfile.TemporaryDirectory(prefix="parallel-runner-")
        self.root = Path(self.temporary.name).resolve()
        shutil.copy2(RUNNER, self.root / "run_tests.py")
        for name, source in files.items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(textwrap.dedent(source), encoding="utf-8")

    def close(self):
        self.temporary.cleanup()

    def run(self, *arguments, environment=None):
        return subprocess.run(
            [sys.executable, str(self.root / "run_tests.py"), *arguments],
            cwd=self.root,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def summary(self, result):
        lines = [
            line[len(SUMMARY_PREFIX):]
            for line in result.stdout.splitlines()
            if line.startswith(SUMMARY_PREFIX)
        ]
        self_test = self
        self_test.assert_summary_count(lines)
        return json.loads(lines[0])

    @staticmethod
    def assert_summary_count(lines):
        if len(lines) != 1:
            raise AssertionError(f"expected one structured summary, got {lines!r}")


class RunnerCase(unittest.TestCase):
    def fixture(self, files):
        made = RunnerFixture(files)
        self.addCleanup(made.close)
        return made

    def summary(self, fixture, result):
        return fixture.summary(result)


class EmptyPipe:
    """A finished binary pipe for coordinator boundary tests."""

    def read(self, _size):
        return b""

    def close(self):
        return None


class BrokenReadPipe:
    """A binary child pipe whose coordinator read fails locally."""

    def read(self, _size):
        raise OSError("synthetic pipe read failure")

    def close(self):
        return None


class FinishedProcess:
    """A process stub whose output streams have already drained."""

    def __init__(self, returncode=0, pid=91_001, events=None):
        self.returncode = returncode
        self.pid = pid
        self.events = events
        self.stdout = EmptyPipe()
        self.stderr = EmptyPipe()

    def poll(self):
        return self.returncode

    def wait(self):
        if self.events is not None:
            self.events.append("reap")
        return self.returncode


class ParentRedGuard(RunnerCase):
    def test_positive_jobs_runs_a_complete_fresh_manifest(self):
        fixture = self.fixture({
            "test_fixture.py": """
                import unittest

                class Example(unittest.TestCase):
                    def test_a(self): self.assertTrue(True)
                    def test_b(self): self.assertTrue(True)
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("wildcat.hexaemeron-run.v1", summary["schema"])
        self.assertEqual("passed", summary["status"])
        self.assertEqual(2, summary["manifest"]["discovered"])
        self.assertEqual(2, summary["assignment"]["assigned"])
        self.assertEqual(2, summary["execution"]["completed"])
        self.assertTrue(summary["execution"]["executed_once"])

    def test_report_target_refuses_git_control_namespace(self):
        require_runner_features(self, "argument_parser", "bind_report_target")
        with tempfile.TemporaryDirectory(prefix="report-git-control-") as raw:
            root = Path(raw)
            (root / ".git").mkdir()
            parser = runner.argument_parser()
            with (
                mock.patch.object(runner.Path, "cwd", return_value=root),
                self.assertRaises(SystemExit),
            ):
                runner.bind_report_target(
                    ".git/refs/heads/corrupt",
                    parser,
                )


class ManifestAndWorkerProtocol(RunnerCase):
    def test_test_id_failure_is_a_structured_scheduler_refusal(self):
        fixture = self.fixture({
            "test_broken_id.py": """
                import unittest

                class BrokenId(unittest.TestCase):
                    def id(self):
                        raise RuntimeError('synthetic id failure')

                    def test_value(self):
                        pass

                def load_tests(loader, standard, pattern):
                    return unittest.TestSuite([BrokenId('test_value')])
            """,
        })

        result = fixture.run("--jobs", "1")

        self.assertEqual(3, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn(
            "test id lookup failed: RuntimeError",
            " ".join(summary["scheduler_errors"]),
        )
        self.assertNotIn("Traceback", result.stderr)

    def test_suite_iterator_failures_are_structured_scheduler_refusals(self):
        for exception in ("RuntimeError", "RecursionError"):
            with self.subTest(exception=exception):
                fixture = self.fixture({
                    "test_broken_iterator.py": f"""
                        import unittest

                        class BrokenIteratorSuite(unittest.TestSuite):
                            def __iter__(self):
                                raise {exception}('synthetic iterator failure')

                        def load_tests(loader, standard, pattern):
                            return BrokenIteratorSuite()
                    """,
                })

                result = fixture.run("--jobs", "1")

                self.assertEqual(3, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual("scheduler-error", summary["status"])
                self.assertIn(
                    f"test suite iteration failed: {exception}",
                    " ".join(summary["scheduler_errors"]),
                )
                self.assertNotIn("Traceback", result.stderr)

    def test_custom_suite_run_behavior_cannot_disappear(self):
        fixture = self.fixture({
            "test_custom_suite.py": """
                import unittest

                class Passing(unittest.TestCase):
                    def test_ok(self):
                        pass

                class FailingWrapper(unittest.TestSuite):
                    def run(self, result, debug=False):
                        raise AssertionError(
                            'custom suite run must not disappear'
                        )

                def load_tests(loader, standard, pattern):
                    return FailingWrapper([Passing('test_ok')])
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(3, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn(
            "custom test suite execution override: run",
            " ".join(summary["scheduler_errors"]),
        )
        self.assertEqual(0, summary["execution"]["started"])
        self.assertNotIn("Traceback", result.stderr)

    def test_custom_suite_metaclass_cannot_hide_execution_override(self):
        fixture = self.fixture({
            "test_hidden_suite.py": """
                import unittest

                class LyingMeta(type):
                    def __getattribute__(cls, name):
                        if name == "run":
                            return unittest.TestSuite.run
                        return super().__getattribute__(name)

                class Passing(unittest.TestCase):
                    def test_ok(self):
                        pass

                class HiddenWrapper(
                    unittest.TestSuite, metaclass=LyingMeta
                ):
                    def run(self, result, debug=False):
                        raise AssertionError(
                            "metaclass-hidden suite run must not disappear"
                        )

                def load_tests(loader, standard, pattern):
                    return HiddenWrapper([Passing("test_ok")])
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(3, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn(
            "custom test suite execution override: run",
            " ".join(summary["scheduler_errors"]),
        )
        self.assertEqual(0, summary["execution"]["started"])
        self.assertNotIn("Traceback", result.stderr)

    def test_custom_suite_fixture_transition_hooks_cannot_disappear(self):
        cases = {
            "module-transition": (
                "_get_previous_module",
                """
                    import unittest

                    class Passing(unittest.TestCase):
                        def test_ok(self):
                            pass

                    class AlteredWrapper(unittest.TestSuite):
                        def _get_previous_module(self, result):
                            raise AssertionError(
                                "custom module transition must not disappear"
                            )

                    def load_tests(loader, standard, pattern):
                        return AlteredWrapper([Passing("test_ok")])
                """,
            ),
            "fixture-exception": (
                "_createClassOrModuleLevelException",
                """
                    import unittest

                    class Blocked(unittest.TestCase):
                        @classmethod
                        def setUpClass(cls):
                            raise unittest.SkipTest("fixture transition")

                        def test_ok(self):
                            pass

                    class AlteredWrapper(unittest.TestSuite):
                        def _createClassOrModuleLevelException(
                            self, result, exception, method_name, parent,
                            info=None,
                        ):
                            raise AssertionError(
                                "custom fixture exception must not disappear"
                            )

                    def load_tests(loader, standard, pattern):
                        return AlteredWrapper([Blocked("test_ok")])
                """,
            ),
        }
        for label, (method, source) in cases.items():
            with self.subTest(case=label):
                fixture = self.fixture({"test_custom_hook.py": source})
                result = fixture.run("--jobs", "2")

                self.assertEqual(3, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual("scheduler-error", summary["status"])
                self.assertIn(
                    f"custom test suite execution override: {method}",
                    " ".join(summary["scheduler_errors"]),
                )
                self.assertEqual(0, summary["execution"]["started"])
                self.assertNotIn("Traceback", result.stderr)

    def test_deep_and_cyclic_suites_have_stable_manifest_boundaries(self):
        case = unittest.FunctionTestCase(lambda: None)
        nested = case
        for _ in range(2_000):
            nested = unittest.TestSuite([nested])

        self.assertEqual([case], list(runner.flatten_suite(nested)))

        cyclic = unittest.TestSuite()
        cyclic.addTest(cyclic)
        with self.assertRaisesRegex(runner.SchedulerError, "cyclic test suite"):
            list(runner.flatten_suite(cyclic))

    def test_manifest_item_limit_stops_discovery_incrementally(self):
        class FakeCase:
            def __init__(self, index):
                self.index = index

            def id(self):
                return f"suite.test_{self.index}"

        class CountingSuite(unittest.TestSuite):
            def __iter__(self):
                for index in range(5):
                    if index > 3:
                        raise AssertionError(
                            "discovery read past the manifest item limit"
                        )
                    yield FakeCase(index)

        loader = mock.Mock()
        loader.discover.return_value = CountingSuite()
        with (
            mock.patch.object(runner, "MAX_TESTS", 3),
            self.assertRaisesRegex(
                runner.SchedulerError, "manifest exceeds its item limit"
            ),
        ):
            runner.discover_manifest(RUNNER.parent, loader)

    def test_sparse_suite_iteration_consumes_the_item_limit(self):
        class SparseSuite(unittest.TestSuite):
            def __iter__(self):
                for index in range(5):
                    if index > 3:
                        raise AssertionError(
                            "discovery read past the traversal item limit"
                        )
                    yield None

        loader = mock.Mock()
        loader.discover.return_value = SparseSuite()
        with (
            mock.patch.object(runner, "MAX_TESTS", 3),
            self.assertRaisesRegex(
                runner.SchedulerError, "manifest exceeds its item limit"
            ),
        ):
            runner.discover_manifest(RUNNER.parent, loader)

    def test_dynamic_locals_ids_execute_from_worker_local_objects(self):
        fixture = self.fixture({
            "test_dynamic.py": """
                import unittest

                def load_tests(loader, standard, pattern):
                    class Generated(unittest.TestCase):
                        pass
                    for number in range(3):
                        def generated(self, number=number):
                            self.assertGreaterEqual(number, 0)
                        setattr(Generated, f'test_generated_{number}', generated)
                    return loader.loadTestsFromTestCase(Generated)
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(3, summary["manifest"]["discovered"])
        self.assertEqual(3, summary["execution"]["started"])
        self.assertEqual(3, summary["execution"]["completed"])
        self.assertTrue(summary["execution"]["executed_once"])

    def test_add_remove_and_rename_are_fresh_later_manifests(self):
        fixture = self.fixture({
            "test_drift.py": """
                import unittest
                class Drift(unittest.TestCase):
                    def test_one(self): pass
                    def test_two(self): pass
            """,
        })
        first = fixture.run("--jobs", "2")
        first_summary = self.summary(fixture, first)

        (fixture.root / "test_drift.py").write_text(textwrap.dedent("""
            import unittest
            class Drift(unittest.TestCase):
                def test_one_renamed(self): pass
                def test_three(self): pass
                def test_four(self): pass
        """), encoding="utf-8")
        second = fixture.run("--jobs", "2")
        second_summary = self.summary(fixture, second)

        (fixture.root / "test_drift.py").write_text(textwrap.dedent("""
            import unittest
            class Drift(unittest.TestCase):
                def test_four(self): pass
        """), encoding="utf-8")
        third = fixture.run("--jobs", "2")
        third_summary = self.summary(fixture, third)

        self.assertEqual([0, 0, 0], [first.returncode, second.returncode, third.returncode])
        self.assertEqual([2, 3, 1], [
            first_summary["manifest"]["discovered"],
            second_summary["manifest"]["discovered"],
            third_summary["manifest"]["discovered"],
        ])
        self.assertEqual(3, len({
            first_summary["manifest"]["digest"],
            second_summary["manifest"]["digest"],
            third_summary["manifest"]["digest"],
        }))
        for summary in (first_summary, second_summary, third_summary):
            self.assertTrue(summary["execution"]["executed_once"])

    def test_duplicate_discovered_id_is_a_scheduler_error(self):
        fixture = self.fixture({
            "test_duplicate.py": """
                import unittest

                def load_tests(loader, standard, pattern):
                    def generated(): pass
                    case = unittest.FunctionTestCase(generated)
                    return unittest.TestSuite([case, unittest.FunctionTestCase(generated)])
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(3, result.returncode)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn("duplicate test id", " ".join(summary["scheduler_errors"]))

    def test_worker_refuses_a_stale_manifest(self):
        require_runner_features(
            self, "discover_manifest", "assignment_payload"
        )
        fixture = self.fixture({
            "test_stale.py": """
                import unittest
                class Stale(unittest.TestCase):
                    def test_before(self): pass
            """,
        })
        tests, identifiers, digest = runner.discover_manifest(fixture.root)
        self.assertEqual(1, len(tests))
        protocol = fixture.root / ".worker-protocol"
        protocol.mkdir(mode=0o700)
        assignment = protocol / "assignment-0.json"
        result_path = protocol / "result-0.json"
        payload = runner.assignment_payload(
            shard=0,
            shard_count=1,
            indices=[0],
            identifiers=identifiers,
            digest=digest,
            suite_root=fixture.root,
            runner_path=fixture.root / "run_tests.py",
        )
        assignment.write_text(json.dumps(payload), encoding="utf-8")
        (fixture.root / "test_stale.py").write_text(textwrap.dedent("""
            import unittest
            class Stale(unittest.TestCase):
                def test_after(self): pass
        """), encoding="utf-8")

        completed = fixture.run(
            "--_worker-assignment", str(assignment),
            "--_worker-result", str(result_path),
        )

        self.assertEqual(3, completed.returncode)
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertFalse(payload["complete"])
        self.assertEqual("scheduler-error", payload["status"])
        self.assertIn("manifest digest mismatch", payload["scheduler_error"])


class AssignmentAccounting(RunnerCase):
    def setUp(self):
        self.identifiers = ["suite.test_a", "suite.test_b"]
        self.digest = (
            runner.manifest_digest(self.identifiers)
            if hasattr(runner, "manifest_digest")
            else None
        )
        self.assignments = [[0], [1]]

    def record(
        self,
        shard,
        started=None,
        completed=None,
        assigned=None,
        shard_count=None,
        durations=None,
    ):
        indices = self.assignments[shard] if assigned is None else assigned
        ids = [self.identifiers[index] for index in indices]
        started = ids if started is None else started
        completed = ids if completed is None else completed
        durations = (
            [[identifier, 0.01] for identifier in completed]
            if durations is None
            else durations
        )
        return {
            "schema": "wildcat.hexaemeron-worker-result.v1",
            "status": "passed",
            "complete": True,
            "output_transport": "result-json",
            "shard": shard,
            "shard_count": (
                len(self.assignments) if shard_count is None else shard_count
            ),
            "manifest_digest": self.digest,
            "manifest_count": len(self.identifiers),
            "assigned_indices": indices,
            "assigned_ids": ids,
            "started_ids": started,
            "completed_ids": completed,
            "fixture_blocked_ids": [],
            "fixture_skip_holders": [],
            "exact_accounting": True,
            "testsRun": len(started),
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
            "durations": durations,
            "wall_time_seconds": 0.01,
            "output": {
                "stdout": {"text": "", "bytes": 0, "truncated": False},
                "stderr": {"text": "", "bytes": 0, "truncated": False},
            },
        }

    def private_result(self, record):
        require_runner_features(
            self,
            "manifest_digest",
            "run_parallel",
        )
        identifiers = [self.identifiers[0]]
        digest = runner.manifest_digest(identifiers)
        assignments = [[0]]
        with tempfile.TemporaryDirectory(prefix="worker-boundary-") as root:
            replay = mock.Mock()
            with (
                mock.patch.object(
                    runner.subprocess,
                    "Popen",
                    return_value=FinishedProcess(),
                ),
                mock.patch.object(
                    runner, "read_worker_result_at", return_value=record
                ),
                mock.patch.object(
                    runner, "replay_worker_outputs", replay
                ),
                mock.patch.object(
                    runner,
                    "observe_worker_exit_without_reaping",
                    return_value=True,
                    create=True,
                ),
            ):
                outcome = runner.run_parallel(
                    run_root=Path(root).resolve(),
                    runner_path=RUNNER.resolve(),
                    suite_root=RUNNER.parent.resolve(),
                    identifiers=identifiers,
                    digest=digest,
                    assignments=assignments,
                )
        return outcome, replay

    def test_worker_protocol_directory_is_outside_invocation_checkout(self):
        require_runner_features(self, "run_parallel")
        real_temporary_directory = tempfile.TemporaryDirectory
        protocol_roots = []

        def tracked_temporary_directory(*args, **kwargs):
            context = real_temporary_directory(*args, **kwargs)
            protocol_roots.append(Path(context.name).resolve())
            return context

        with real_temporary_directory(prefix="worker-checkout-") as root_raw:
            root = Path(root_raw).resolve()
            with (
                mock.patch.object(
                    runner.tempfile,
                    "TemporaryDirectory",
                    side_effect=tracked_temporary_directory,
                ),
                mock.patch.object(
                    runner.subprocess,
                    "Popen",
                    return_value=FinishedProcess(),
                ),
                mock.patch.object(
                    runner, "read_worker_result_at", return_value=None
                ),
                mock.patch.object(
                    runner, "replay_worker_outputs", return_value=None
                ),
                mock.patch.object(
                    runner,
                    "observe_worker_exit_without_reaping",
                    return_value=True,
                    create=True,
                ),
            ):
                runner.run_parallel(
                    run_root=root,
                    runner_path=RUNNER.resolve(),
                    suite_root=RUNNER.parent.resolve(),
                    identifiers=[self.identifiers[0]],
                    digest=runner.manifest_digest([self.identifiers[0]]),
                    assignments=[[0]],
                )

        self.assertEqual(1, len(protocol_roots))
        self.assertNotEqual(root, protocol_roots[0])
        self.assertNotIn(root, protocol_roots[0].parents)

    def test_worker_protocol_containment_uses_directory_identity(self):
        require_runner_features(
            self, "directory_contains_identity", "run_parallel"
        )
        identities = {
            101: mock.Mock(st_dev=4, st_ino=30),
            102: mock.Mock(st_dev=4, st_ino=20),
            103: mock.Mock(st_dev=4, st_ino=10),
        }
        closed = []
        with (
            mock.patch.object(runner.os, "dup", return_value=101),
            mock.patch.object(runner.os, "open", side_effect=[102, 103]),
            mock.patch.object(
                runner.os,
                "fstat",
                side_effect=lambda descriptor: identities[descriptor],
            ),
            mock.patch.object(
                runner.os, "close", side_effect=closed.append
            ),
        ):
            contained = runner.directory_contains_identity(90, (4, 10))

        self.assertTrue(contained)
        self.assertEqual([101, 102, 103], closed)

        probe = mock.Mock(return_value=True)
        with tempfile.TemporaryDirectory(
            prefix="worker-identity-root-"
        ) as root:
            with mock.patch.object(
                runner, "directory_contains_identity", probe
            ):
                with self.assertRaisesRegex(
                    runner.SchedulerError,
                    "private worker directory is inside invocation checkout",
                ):
                    runner.run_parallel(
                        run_root=Path(root).resolve(),
                        runner_path=RUNNER.resolve(),
                        suite_root=RUNNER.parent.resolve(),
                        identifiers=[self.identifiers[0]],
                        digest=runner.manifest_digest(
                            [self.identifiers[0]]
                        ),
                        assignments=[[0]],
                    )
        self.assertEqual(1, probe.call_count)

    def test_ambient_temp_root_cannot_put_worker_protocol_in_checkout(self):
        fixture = self.fixture({
            "test_protocol_root.py": """
                import unittest

                class ProtocolRoot(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass
            """,
        })
        hostile_temp = fixture.root / "hostile-temp"
        hostile_temp.mkdir()
        environment = os.environ.copy()
        environment.update({
            "TMPDIR": str(hostile_temp),
            "TMP": str(hostile_temp),
            "TEMP": str(hostile_temp),
        })

        result = fixture.run("--jobs", "2", environment=environment)

        self.assertEqual(3, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn(
            "private worker directory is inside invocation checkout",
            " ".join(summary["scheduler_errors"]),
        )
        self.assertEqual([], list(hostile_temp.iterdir()))

    def test_process_group_identity_is_retained_until_cleanup_signals_finish(self):
        events = []
        process = FinishedProcess(events=events)

        def observe(_process, *, nohang=False):
            events.append("observe-nonblocking" if nohang else "observe-exit")
            return True

        def signal_groups(_processes, _shards, _signal, _errors):
            events.append("signal")

        with tempfile.TemporaryDirectory(prefix="worker-identity-") as root:
            with (
                mock.patch.object(
                    runner.subprocess, "Popen", return_value=process
                ),
                mock.patch.object(
                    runner,
                    "observe_worker_exit_without_reaping",
                    side_effect=observe,
                    create=True,
                ),
                mock.patch.object(
                    runner,
                    "retained_drainer_shards",
                    side_effect=([0], [0], []),
                ),
                mock.patch.object(
                    runner, "join_drainers_until", return_value=None
                ),
                mock.patch.object(
                    runner, "signal_worker_groups", side_effect=signal_groups
                ),
                mock.patch.object(
                    runner, "read_worker_result_at", return_value=None
                ),
                mock.patch.object(
                    runner, "replay_worker_outputs", return_value=None
                ),
            ):
                runner.run_parallel(
                    run_root=Path(root).resolve(),
                    runner_path=RUNNER.resolve(),
                    suite_root=RUNNER.parent.resolve(),
                    identifiers=["suite.test_a"],
                    digest=runner.manifest_digest(["suite.test_a"]),
                    assignments=[[0]],
                )

        self.assertIn("observe-exit", events)
        self.assertIn("signal", events)
        self.assertIn("reap", events)
        self.assertLess(events.index("signal"), events.index("reap"))

    def test_assignments_must_be_an_exact_disjoint_union(self):
        require_runner_features(
            self, "SchedulerError", "validate_assignments"
        )
        for assignments, message in (
            ([[0], [0, 1]], "duplicate assignment"),
            ([[0]], "missing assignment"),
            ([[0], [2]], "out-of-range assignment"),
            ([[0], []], "empty shard"),
        ):
            with self.subTest(assignments=assignments), self.assertRaisesRegex(
                runner.SchedulerError, message
            ):
                runner.validate_assignments(assignments, 2)

    def test_missing_duplicate_unexecuted_and_unknown_results_refuse_green(self):
        require_runner_features(
            self,
            "SchedulerError",
            "manifest_digest",
            "reconcile_worker_results",
        )
        cases = [
            ("missing", "missing result", [self.record(0)]),
            ("duplicate", "worker execution assignment mismatch", [
                self.record(0),
                self.record(1, started=[self.identifiers[0]], completed=[self.identifiers[0]]),
            ]),
            ("unexecuted", "worker execution assignment mismatch", [
                self.record(0),
                self.record(1, started=[], completed=[]),
            ]),
            ("unknown", "worker execution assignment mismatch", [
                self.record(0),
                self.record(1, started=["suite.unknown"], completed=["suite.unknown"]),
            ]),
            ("swapped", "worker execution assignment mismatch", [
                self.record(
                    0,
                    started=[self.identifiers[1]],
                    completed=[self.identifiers[1]],
                ),
                self.record(
                    1,
                    started=[self.identifiers[0]],
                    completed=[self.identifiers[0]],
                ),
            ]),
            ("shard-count", "worker shard count mismatch", [
                self.record(0),
                self.record(1, shard_count=3),
            ]),
            ("duration", "worker duration assignment mismatch", [
                self.record(
                    0,
                    durations=[[self.identifiers[1], 0.01]],
                ),
                self.record(
                    1,
                    durations=[[self.identifiers[0], 0.01]],
                ),
            ]),
        ]
        for label, message, records in cases:
            with self.subTest(case=label), self.assertRaisesRegex(
                runner.SchedulerError, message
            ):
                runner.reconcile_worker_results(
                    self.identifiers,
                    self.digest,
                    self.assignments,
                    records,
                )

    def test_result_file_slot_is_bound_before_reconciliation(self):
        require_runner_features(
            self,
            "SchedulerError",
            "manifest_digest",
            "reconcile_worker_results",
        )
        with self.assertRaisesRegex(
            runner.SchedulerError, "shard does not match result slot"
        ):
            runner.reconcile_worker_results(
                self.identifiers,
                self.digest,
                self.assignments,
                [self.record(1), self.record(0)],
            )

    def test_non_object_result_is_a_scheduler_error_not_an_exception(self):
        try:
            (records, errors, _queue), replay = self.private_result([])
        except Exception as error:  # pragma: no cover - parent-red guard
            self.fail(f"worker result escaped scheduler boundary: {error}")

        self.assertEqual([None], records)
        self.assertIn("invalid worker result schema", " ".join(errors))
        replay.assert_called_once()
        self.assertEqual([None], replay.call_args.args[1])

    def test_invalid_record_cannot_replay_forged_output(self):
        record = self.record(0, shard_count=1)
        record["manifest_count"] = 1
        record["manifest_digest"] = "0" * 64
        record["output"]["stdout"]["text"] = "FORGED-BEFORE-VALIDATION\n"
        record["output"]["stdout"]["bytes"] = 25

        (records, errors, _queue), replay = self.private_result(record)

        self.assertEqual([None], records)
        self.assertIn("manifest digest mismatch", " ".join(errors))
        replay.assert_called_once()
        self.assertEqual([None], replay.call_args.args[1])

    def test_replayed_text_is_bound_to_its_byte_metadata(self):
        record = self.record(0)
        record["output"]["stdout"]["text"] = "abc"
        record["output"]["stdout"]["bytes"] = 0

        with self.assertRaisesRegex(
            runner.SchedulerError, "byte metadata mismatch"
        ):
            runner.validate_worker_record(
                record,
                self.identifiers,
                self.digest,
                self.assignments,
            )

    def test_truncated_output_requires_the_full_bounded_head_and_tail(self):
        record = self.record(0)
        byte_count = runner.MAX_OUTPUT_BYTES + 1
        marker = (
            f"\n... output truncated; {byte_count} bytes emitted ...\n"
        )
        record["output"]["stdout"] = {
            "text": marker,
            "bytes": byte_count,
            "truncated": True,
        }

        with self.assertRaisesRegex(
            runner.SchedulerError, "byte metadata mismatch"
        ):
            runner.validate_worker_record(
                record,
                self.identifiers,
                self.digest,
                self.assignments,
            )

    def test_bounded_text_capture_has_one_exact_utf8_truncation_shape(self):
        require_runner_features(self, "BoundedTextCapture", "MAX_OUTPUT_BYTES")
        cases = (
            ("exact", "a" * runner.MAX_OUTPUT_BYTES, False),
            ("one-over", "a" * (runner.MAX_OUTPUT_BYTES + 1), True),
            (
                "unaligned-unicode",
                "ab" + "😀" * 70_000,
                True,
            ),
        )
        empty = {"text": "", "bytes": 0, "truncated": False}
        for label, emitted, truncated in cases:
            with self.subTest(case=label):
                capture = runner.BoundedTextCapture()
                capture.write(emitted)
                payload = capture.payload()
                runner.validate_worker_output({
                    "stdout": payload,
                    "stderr": empty,
                })
                self.assertEqual(truncated, payload["truncated"])
                if truncated:
                    marker = (
                        f"\n... output truncated; {payload['bytes']} "
                        "bytes emitted ...\n"
                    ).encode("utf-8")
                    retained = payload["text"].encode("utf-8")
                    self.assertEqual(
                        runner.MAX_OUTPUT_BYTES + len(marker), len(retained)
                    )
                    self.assertEqual(
                        runner.MAX_OUTPUT_BYTES // 2, retained.index(marker)
                    )

    def test_single_worker_uses_the_private_worker_transport(self):
        identifier = "suite.test_a"
        identifiers = [identifier]
        digest = runner.manifest_digest(identifiers)
        assignments = [[0]]
        record = self.record(0, shard_count=1)
        record.update({
            "manifest_digest": digest,
            "manifest_count": 1,
            "assigned_indices": [0],
            "assigned_ids": identifiers,
            "started_ids": identifiers,
            "completed_ids": identifiers,
            "testsRun": 1,
            "durations": [[identifier, 0.01]],
            "output_transport": runner.COORDINATOR_PIPE_OUTPUT,
        })
        record.pop("output")
        capacity = {
            "signals": {"os_cpu_count": 1},
            "usable": 1,
            "reserve": 0,
            "budget": 1,
            "budget_source": "explicit",
            "effective_jobs": 1,
        }
        cache = {
            "schema": "wildcat.test-timings.v1",
            "status": "missing",
            "digest": None,
            "hits": 0,
            "neutral": 1,
            "ignored_removed": 0,
            "corrupt_entries": 0,
            "write_status": "not-attempted",
        }
        parallel = mock.Mock(return_value=(
            [record],
            [],
            {
                "queue_high_water": 1,
                "maximum_observed_live_children": 1,
            },
        ))
        in_process = mock.Mock()
        emitted = mock.Mock()
        with (
            mock.patch.object(
                runner,
                "discover_manifest",
                return_value=([object()], identifiers, digest),
            ),
            mock.patch.object(runner, "capacity_plan", return_value=capacity),
            mock.patch.object(
                runner, "load_timing_cache", return_value=({}, cache)
            ),
            mock.patch.object(
                runner,
                "partition_indices",
                return_value=(assignments, [1.0], 1.0),
            ),
            mock.patch.object(runner, "run_parallel", parallel),
            mock.patch.object(runner, "run_selected_tests", in_process),
            mock.patch.object(runner, "write_timing_cache"),
            mock.patch.object(runner, "child_usage", return_value=None),
            mock.patch.object(runner, "emit_summary", emitted),
        ):
            exit_code = runner.coordinator_main(mock.Mock(jobs=1), None)

        self.assertEqual(0, exit_code)
        parallel.assert_called_once()
        in_process.assert_not_called()
        summary = emitted.call_args.args[0]
        self.assertEqual("passed", summary["status"])
        self.assertEqual(1, summary["queue"]["maximum_observed_live_children"])

    def test_parallel_worker_output_uses_only_coordinator_owned_pipes(self):
        fixture = self.fixture({
            "test_pipe.py": """
                import sys
                import unittest

                class Pipe(unittest.TestCase):
                    def test_output(self):
                        print('PIPE-STDOUT')
                        print('PIPE-STDERR', file=sys.stderr)
            """,
        })
        tests, identifiers, digest = runner.discover_manifest(fixture.root)
        self.assertEqual(1, len(tests))
        protocol = fixture.root / ".worker-protocol"
        protocol.mkdir(mode=0o700)
        assignment = protocol / "assignment-0.json"
        result_path = protocol / "result-0.json"
        payload = runner.assignment_payload(
            shard=0,
            shard_count=1,
            indices=[0],
            identifiers=identifiers,
            digest=digest,
            suite_root=fixture.root,
            runner_path=fixture.root / "run_tests.py",
        )
        assignment.write_text(json.dumps(payload), encoding="utf-8")

        completed = fixture.run(
            "--_worker-assignment", str(assignment),
            "--_worker-result", str(result_path),
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        record = json.loads(result_path.read_text(encoding="utf-8"))
        self.assertEqual("coordinator-pipes", record.get("output_transport"))
        self.assertNotIn("output", record)
        self.assertIn("PIPE-STDOUT", completed.stdout)
        self.assertIn("PIPE-STDERR", completed.stderr)

    def test_near_cap_unicode_worker_record_fits_its_private_file(self):
        identifiers = []
        encoded_size = len(runner.manifest_bytes(identifiers))
        for index in range(runner.MAX_TESTS):
            identifier = f"😀{index}"
            encoded = json.dumps(
                identifier,
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
            added = len(encoded) + (1 if identifiers else 0)
            if encoded_size + added > runner.MAX_MANIFEST_BYTES:
                break
            identifiers.append(identifier)
            encoded_size += added
        self.assertGreater(encoded_size, runner.MAX_MANIFEST_BYTES - 128)
        digest = runner.manifest_digest(identifiers)
        indices = list(range(len(identifiers)))
        duration = 0.00012345678901234567
        record = {
            "schema": runner.WORKER_RESULT_SCHEMA,
            "status": "passed",
            "complete": True,
            "output_transport": "coordinator-pipes",
            "shard": 0,
            "shard_count": 1,
            "manifest_digest": digest,
            "manifest_count": len(identifiers),
            "assigned_indices": indices,
            "assigned_ids": identifiers,
            "started_ids": identifiers,
            "completed_ids": identifiers,
            "fixture_blocked_ids": [],
            "fixture_skip_holders": [],
            "exact_accounting": True,
            "testsRun": len(identifiers),
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
            "durations": [
                [identifier, duration] for identifier in identifiers
            ],
            "wall_time_seconds": duration,
        }
        with tempfile.TemporaryDirectory(prefix="worker-cap-") as root:
            descriptor = runner.os.open(
                root,
                runner.os.O_RDONLY
                | runner.os.O_DIRECTORY
                | runner.os.O_NOFOLLOW,
            )
            try:
                try:
                    runner.write_json_exclusive_at(
                        descriptor,
                        "result.json",
                        record,
                        maximum=runner.MAX_WORKER_RESULT_BYTES,
                    )
                except OSError as error:
                    self.fail(f"valid bounded worker record was refused: {error}")
            finally:
                runner.os.close(descriptor)
            written = (Path(root) / "result.json").read_bytes()
        self.assertGreater(len(written), 2 * 1024 * 1024)
        self.assertLessEqual(len(written), runner.MAX_WORKER_RESULT_BYTES)
        self.assertEqual(record, json.loads(written))

    def test_worker_result_limit_is_derived_from_every_bounded_field(self):
        require_runner_features(
            self,
            "MAX_JSON_NUMBER_BYTES",
            "MAX_WORKER_RESULT_FIXED_BYTES",
        )
        expected = (
            6 * runner.MAX_MANIFEST_BYTES
            + runner.MAX_TESTS * (len(str(runner.MAX_TESTS - 1)) + 1)
            + runner.MAX_TESTS * (runner.MAX_JSON_NUMBER_BYTES + 4)
            + runner.MAX_WORKER_RESULT_FIXED_BYTES
        )

        self.assertEqual(expected, runner.MAX_WORKER_RESULT_BYTES)
        for number in (0.0, 5e-324, 0.00012345678901234567, 86400.0):
            with self.subTest(number=number):
                self.assertLessEqual(
                    runner.json_number_bytes(number),
                    runner.MAX_JSON_NUMBER_BYTES,
                )

    def test_large_parseable_numbers_use_stable_scheduler_refusals(self):
        huge = 10 ** 309
        cases = (
            (
                "duration",
                lambda record: record.__setitem__(
                    "durations", [[self.identifiers[0], huge]]
                ),
                "invalid worker result duration entry",
            ),
            (
                "wall-time",
                lambda record: record.__setitem__(
                    "wall_time_seconds", huge
                ),
                "invalid worker result wall time",
            ),
        )
        for label, mutate, expected in cases:
            record = self.record(0)
            mutate(record)
            with self.subTest(field=label):
                try:
                    runner.validate_worker_record(
                        record,
                        self.identifiers,
                        self.digest,
                        self.assignments,
                    )
                except runner.SchedulerError as error:
                    self.assertIn(expected, str(error))
                except (TypeError, ValueError, OverflowError) as error:
                    self.fail(f"numeric refusal escaped scheduler boundary: {error}")
                else:
                    self.fail("oversized numeric token was accepted")

    def test_cross_shard_outcome_counts_refuse_before_aggregate_overflow(self):
        per_shard = sys.maxsize // len(self.assignments) + 1
        records = [self.record(0), self.record(1)]
        for record in records:
            record["status"] = "test-failure"
            record["failures"] = per_shard

        try:
            reconciled = runner.reconcile_worker_results(
                self.identifiers,
                self.digest,
                self.assignments,
                records,
            )
            runner.result_payload(
                runner.AggregateResult(reconciled["counts"])
            )
        except runner.SchedulerError as error:
            self.assertRegex(str(error), "failures.*aggregate bound")
        except OverflowError as error:
            self.fail(f"aggregate sequence overflow escaped: {error}")
        else:
            self.fail("aggregate sequence overflow was accepted")

    def test_public_coordinator_contains_cross_shard_aggregate_refusal(self):
        per_shard = sys.maxsize // len(self.assignments) + 1
        records = [self.record(0), self.record(1)]
        for record in records:
            record["status"] = "test-failure"
            record["output_transport"] = "coordinator-pipes"
            record["failures"] = per_shard
            record.pop("output")
        capacity = {
            "signals": {"os_cpu_count": 2},
            "usable": 2,
            "reserve": 0,
            "budget": 2,
            "budget_source": "explicit",
            "effective_jobs": 2,
        }
        cache = {
            "schema": "wildcat.test-timings.v1",
            "status": "missing",
            "digest": None,
            "hits": 0,
            "neutral": 2,
            "ignored_removed": 0,
            "corrupt_entries": 0,
            "write_status": "not-attempted",
        }
        emitted = mock.Mock()
        with (
            mock.patch.object(
                runner,
                "discover_manifest",
                return_value=([object(), object()], self.identifiers, self.digest),
            ),
            mock.patch.object(runner, "capacity_plan", return_value=capacity),
            mock.patch.object(
                runner, "load_timing_cache", return_value=({}, cache)
            ),
            mock.patch.object(
                runner,
                "partition_indices",
                return_value=(self.assignments, [1.0, 1.0], 1.0),
            ),
            mock.patch.object(
                runner,
                "run_parallel",
                return_value=(
                    records,
                    [],
                    {
                        "queue_high_water": 2,
                        "maximum_observed_live_children": 2,
                    },
                ),
            ),
            mock.patch.object(runner, "child_usage", return_value=None),
            mock.patch.object(runner, "emit_summary", emitted),
        ):
            exit_code = runner.coordinator_main(mock.Mock(jobs=2), None)

        self.assertEqual(3, exit_code)
        summary, aggregate = emitted.call_args.args[:2]
        self.assertEqual("scheduler-error", summary["status"])
        self.assertEqual(0, len(aggregate.failures))
        self.assertEqual(
            [per_shard, per_shard],
            [shard["failures"] for shard in summary["shards"]],
        )
        self.assertRegex(
            " ".join(summary["scheduler_errors"]),
            "worker result failures exceeds aggregate bound.*"
            "aggregate failures exceeds sequence bound",
        )

    def test_uneven_outcome_counts_at_the_sequence_limit_remain_valid(self):
        records = [self.record(0), self.record(1)]
        records[0]["status"] = "test-failure"
        records[0]["failures"] = sys.maxsize

        reconciled = runner.reconcile_worker_results(
            self.identifiers,
            self.digest,
            self.assignments,
            records,
        )
        payload = runner.result_payload(
            runner.AggregateResult(reconciled["counts"])
        )

        self.assertEqual(sys.maxsize, payload["failures"])

    def test_execution_sequences_correlate_before_result_use(self):
        record = self.record(
            0,
            started=[self.identifiers[1]],
            completed=[self.identifiers[1]],
            durations=[[self.identifiers[1], 0.01]],
        )

        with self.assertRaisesRegex(
            runner.SchedulerError, "execution assignment mismatch"
        ):
            runner.validate_worker_record(
                record,
                self.identifiers,
                self.digest,
                self.assignments,
            )

    def test_manifest_and_summary_have_explicit_byte_limits(self):
        require_runner_features(
            self,
            "MAX_IDENTIFIER_BYTES",
            "MAX_MANIFEST_BYTES",
            "MAX_RUN_SUMMARY_BYTES",
            "manifest_digest",
            "summary_json",
        )
        class HostileIdentifiers:
            def __iter__(self):
                for index in range(runner.MAX_TESTS):
                    if index > 1_000:
                        raise AssertionError(
                            "manifest encoder read past its byte bound"
                        )
                    yield (
                        f"suite.test_{index:03d}."
                        + "x" * (runner.MAX_IDENTIFIER_BYTES - 20)
                    )

        with self.assertRaisesRegex(
            runner.SchedulerError, "manifest exceeds .*byte limit"
        ):
            runner.manifest_digest(HostileIdentifiers())
        with self.assertRaisesRegex(
            runner.SchedulerError, "structured summary exceeds .*byte limit"
        ):
            runner.summary_json({
                "payload": "x" * runner.MAX_RUN_SUMMARY_BYTES
            })

    def test_oversized_scheduler_errors_have_a_bounded_refusal_event(self):
        summary = runner.base_summary(RUNNER, RUNNER.parent, RUNNER.parent, 2)
        scheduler_errors = ["x" * 4_096 for _ in range(runner.MAX_JOBS)]
        scheduler_errors.append("; ".join(scheduler_errors))
        summary["scheduler_errors"] = scheduler_errors

        rendered, refused = runner.render_summary_with_refusal(
            summary, scheduler_errors
        )

        self.assertTrue(refused)
        self.assertLessEqual(
            len(rendered.encode("utf-8")), runner.MAX_RUN_SUMMARY_BYTES
        )
        payload = json.loads(rendered)
        self.assertEqual("scheduler-error", payload["status"])
        self.assertEqual(1, len(payload["scheduler_errors"]))
        self.assertEqual(
            len(scheduler_errors),
            payload["scheduler_error_evidence"]["count"],
        )
        self.assertEqual(
            64, len(payload["scheduler_error_evidence"]["sha256"])
        )

    def test_failure_event_summary_never_reports_negative_passes(self):
        aggregate = runner.AggregateResult({"testsRun": 1, "failures": 2})

        with mock.patch("builtins.print") as printed:
            runner.emit_summary({}, aggregate, "{}")

        self.assertEqual(
            "1 tests run; 2 failure events; 0 error events",
            printed.call_args_list[0].args[0],
        )

    def test_scheduler_error_summary_keeps_validated_worker_evidence(self):
        record = self.record(0)
        capacity = {
            "signals": {"os_cpu_count": 2},
            "usable": 2,
            "reserve": 0,
            "budget": 2,
            "budget_source": "explicit",
            "effective_jobs": 2,
        }
        cache = {
            "schema": "wildcat.test-timings.v1",
            "status": "missing",
            "digest": None,
            "hits": 0,
            "neutral": 2,
            "ignored_removed": 0,
            "corrupt_entries": 0,
            "write_status": "not-attempted",
        }
        emitted = mock.Mock()
        with (
            mock.patch.object(
                runner,
                "discover_manifest",
                return_value=([object(), object()], self.identifiers, self.digest),
            ),
            mock.patch.object(runner, "capacity_plan", return_value=capacity),
            mock.patch.object(
                runner, "load_timing_cache", return_value=({}, cache)
            ),
            mock.patch.object(
                runner,
                "partition_indices",
                return_value=(self.assignments, [1.0, 1.0], 1.0),
            ),
            mock.patch.object(
                runner,
                "run_parallel",
                return_value=(
                    [record, None],
                    ["missing result: worker 1"],
                    {
                        "queue_high_water": 2,
                        "maximum_observed_live_children": 2,
                    },
                ),
            ),
            mock.patch.object(runner, "child_usage", return_value=None),
            mock.patch.object(runner, "emit_summary", emitted),
        ):
            exit_code = runner.coordinator_main(mock.Mock(jobs=2), None)

        self.assertEqual(3, exit_code)
        summary = emitted.call_args.args[0]
        self.assertIn("shards", summary)
        self.assertEqual([0], [item["shard"] for item in summary["shards"]])
        completed_evidence = (
            runner.sequence_binding("test-ids", record["completed_ids"])
            if hasattr(runner, "sequence_binding")
            else record["completed_ids"]
        )
        self.assertEqual(
            completed_evidence, summary["shards"][0]["completed_ids"]
        )
        self.assertEqual(1, summary["execution"]["testsRun"])
        self.assertEqual(1, summary["execution"]["started"])
        self.assertEqual(1, summary["execution"]["completed"])
        self.assertFalse(summary["execution"]["executed_once"])
        self.assertEqual(1, summary["shards"][0]["testsRun"])
        self.assertEqual(0, summary["shards"][0]["failures"])
        self.assertEqual(0, summary["shards"][0]["errors"])
        self.assertIn("missing result", " ".join(summary["scheduler_errors"]))

    def test_structured_summary_preserves_each_shards_execution_evidence(self):
        require_runner_features(
            self,
            "MAX_RUN_SUMMARY_BYTES",
            "sequence_binding",
            "summary_json",
        )
        fixture = self.fixture({
            "test_summary_a.py": """
                import unittest

                class SummaryA(unittest.TestCase):
                    def test_a(self): pass
            """,
            "test_summary_b.py": """
                import unittest

                class SummaryB(unittest.TestCase):
                    def test_b(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertIn("shards", summary)
        self.assertEqual(2, len(summary["shards"]))
        self.assertEqual(
            runner.MAX_RUN_SUMMARY_BYTES,
            summary["event"]["byte_limit"],
        )
        self.assertIn("ids", summary["manifest"])
        self.assertEqual(2, len(summary["manifest"]["ids"]))
        self.assertLessEqual(
            summary["manifest"]["encoded_bytes"],
            summary["manifest"]["byte_limit"],
        )
        rendered = runner.summary_json(summary)
        self.assertLessEqual(
            len(rendered.encode("utf-8")), runner.MAX_RUN_SUMMARY_BYTES
        )
        for identifier in summary["manifest"]["ids"]:
            self.assertEqual(1, rendered.count(identifier))
        for expected, shard in enumerate(summary["shards"]):
            with self.subTest(shard=expected):
                self.assertEqual(expected, shard["shard"])
                self.assertEqual(
                    shard["assigned_ids"]["sha256"],
                    shard["started_ids"]["sha256"],
                )
                self.assertEqual(
                    shard["assigned_ids"]["sha256"],
                    shard["completed_ids"]["sha256"],
                )
                self.assertEqual(
                    shard["assigned_count"], shard["assigned_ids"]["count"]
                )
                self.assertEqual(
                    shard["assigned_count"],
                    len(shard["assigned_indices"]),
                )
                assigned_ids = [
                    summary["manifest"]["ids"][index]
                    for index in shard["assigned_indices"]
                ]
                self.assertEqual(
                    runner.sequence_binding("test-ids", assigned_ids),
                    shard["assigned_ids"],
                )
                self.assertEqual(
                    shard["assigned_count"], shard["durations"]["count"]
                )
                self.assertGreaterEqual(shard["wall_time_seconds"], 0)


class CapacityAndCache(RunnerCase):
    def test_automatic_capacity_uses_the_smallest_signal_and_headroom(self):
        require_runner_features(self, "capacity_plan")
        plan = runner.capacity_plan(
            requested=None,
            item_count=20,
            signals={"process_cpu_count": 9, "affinity": 10, "os_cpu_count": 16},
        )

        self.assertEqual(9, plan["usable"])
        self.assertEqual(3, plan["reserve"])
        self.assertEqual(6, plan["budget"])
        self.assertEqual(6, plan["effective_jobs"])
        self.assertEqual("automatic", plan["budget_source"])

    def test_automatic_capacity_respects_safety_cap_after_headroom(self):
        require_runner_features(self, "MAX_JOBS", "capacity_plan")
        plan = runner.capacity_plan(
            requested=None,
            item_count=runner.MAX_JOBS * 4,
            signals={
                "process_cpu_count": runner.MAX_JOBS * 4,
                "os_cpu_count": runner.MAX_JOBS * 4,
            },
        )

        self.assertEqual(runner.MAX_JOBS, plan.get("safety_cap"))
        self.assertEqual(runner.MAX_JOBS, plan["budget"])
        self.assertEqual(runner.MAX_JOBS, plan["effective_jobs"])

    def test_capacity_arithmetic_never_rounds_through_float(self):
        require_runner_features(self, "capacity_plan", "quota_capacity")
        period = 10 ** 200
        quota = 2 * period - 1

        self.assertEqual(
            1,
            runner.quota_capacity(str(quota), str(period)),
        )
        usable = period + 1
        plan = runner.capacity_plan(
            requested=None,
            item_count=1,
            signals={"synthetic": usable},
        )
        self.assertEqual((usable + 2) // 3, plan["reserve"])

    def test_explicit_override_is_positive_bounded_and_capped_by_work(self):
        require_runner_features(self, "MAX_JOBS", "capacity_plan")
        plan = runner.capacity_plan(
            requested=7,
            item_count=2,
            signals={"os_cpu_count": 4},
        )
        self.assertEqual("explicit", plan["budget_source"])
        self.assertEqual(7, plan["budget"])
        self.assertEqual(2, plan["effective_jobs"])

        for value in (0, -1, runner.MAX_JOBS + 1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runner.capacity_plan(value, 2, {"os_cpu_count": 4})

    def test_capacity_signals_include_python_affinity_and_both_quota_forms(self):
        require_runner_features(self, "capacity_signals")

        def controller(path, maximum=256):
            values = {
                "/proc/self/cgroup": "0::/\n",
                "/proc/self/mountinfo": (
                    "31 23 0:28 / /sys/fs/cgroup rw - "
                    "cgroup2 cgroup rw\n"
                ),
                "/sys/fs/cgroup/cpu.max": "750000 100000",
                "/sys/fs/cgroup/cpu/cpu.cfs_quota_us": "900000",
                "/sys/fs/cgroup/cpu/cpu.cfs_period_us": "100000",
            }
            return values[path]

        with (
            mock.patch.object(
                runner.os, "process_cpu_count", return_value=12, create=True
            ),
            mock.patch.object(
                runner.os, "sched_getaffinity", return_value=set(range(10)),
                create=True,
            ),
            mock.patch.object(runner.os, "cpu_count", return_value=16),
            mock.patch.object(runner, "read_small_text", side_effect=controller),
        ):
            signals = runner.capacity_signals()

        self.assertEqual({
            "process_cpu_count": 12,
            "affinity": 10,
            "cgroup_v2": 7,
            "cgroup_v1": 9,
            "os_cpu_count": 16,
        }, signals)

    def test_nested_cgroup_v2_membership_limits_automatic_capacity(self):
        require_runner_features(
            self, "capacity_plan", "capacity_signals"
        )

        def controller(path, maximum=256):
            values = {
                "/proc/self/cgroup": "0::/tenant/job\n",
                "/sys/fs/cgroup/tenant/job/cpu.max": "200000 100000",
                "/sys/fs/cgroup/tenant/cpu.max": "max 100000",
                "/sys/fs/cgroup/cpu.max": "max 100000",
            }
            if path not in values:
                raise OSError("synthetic controller is unavailable")
            return values[path]

        with (
            mock.patch.object(
                runner.os, "process_cpu_count", return_value=32, create=True
            ),
            mock.patch.object(
                runner.os, "sched_getaffinity", return_value=set(range(32)),
                create=True,
            ),
            mock.patch.object(runner.os, "cpu_count", return_value=32),
            mock.patch.object(
                runner, "read_small_text", side_effect=controller
            ),
        ):
            signals = runner.capacity_signals()
            plan = runner.capacity_plan(None, 100, signals)

        self.assertEqual(2, signals.get("cgroup_v2"))
        self.assertEqual(2, plan["usable"])
        self.assertEqual(1, plan["budget"])
        self.assertEqual(1, plan["effective_jobs"])

    def test_cgroup_v2_mount_root_limits_automatic_capacity(self):
        require_runner_features(
            self, "capacity_plan", "capacity_signals"
        )

        def controller(path, maximum=256):
            values = {
                "/proc/self/cgroup": "0::/tenant/job\n",
                "/proc/self/mountinfo": (
                    "31 23 0:28 /tenant /sys/fs/cgroup rw - "
                    "cgroup2 cgroup rw\n"
                ),
                "/sys/fs/cgroup/job/cpu.max": "100000 100000",
                "/sys/fs/cgroup/cpu.max": "max 100000",
            }
            if path not in values:
                raise OSError("synthetic controller is unavailable")
            return values[path]

        with (
            mock.patch.object(
                runner.os, "process_cpu_count", return_value=32, create=True
            ),
            mock.patch.object(
                runner.os,
                "sched_getaffinity",
                return_value=set(range(32)),
                create=True,
            ),
            mock.patch.object(runner.os, "cpu_count", return_value=32),
            mock.patch.object(
                runner, "read_small_text", side_effect=controller
            ),
        ):
            signals = runner.capacity_signals()
            plan = runner.capacity_plan(None, 100, signals)

        self.assertEqual(1, signals.get("cgroup_v2"))
        self.assertEqual(1, plan["usable"])
        self.assertEqual(1, plan["budget"])
        self.assertEqual(1, plan["effective_jobs"])

    def test_nested_cgroup_v1_membership_limits_automatic_capacity(self):
        require_runner_features(
            self, "capacity_plan", "capacity_signals"
        )

        def controller(path, maximum=256):
            values = {
                "/proc/self/cgroup": "2:cpu,cpuacct:/tenant/job\n",
                "/sys/fs/cgroup/cpu,cpuacct/tenant/job/cpu.cfs_quota_us": (
                    "100000"
                ),
                "/sys/fs/cgroup/cpu,cpuacct/tenant/job/cpu.cfs_period_us": (
                    "100000"
                ),
                "/sys/fs/cgroup/cpu,cpuacct/tenant/cpu.cfs_quota_us": "-1",
                "/sys/fs/cgroup/cpu,cpuacct/tenant/cpu.cfs_period_us": (
                    "100000"
                ),
                "/sys/fs/cgroup/cpu/cpu.cfs_quota_us": "-1",
                "/sys/fs/cgroup/cpu/cpu.cfs_period_us": "100000",
            }
            if path not in values:
                raise OSError("synthetic controller is unavailable")
            return values[path]

        with (
            mock.patch.object(
                runner.os, "process_cpu_count", return_value=32, create=True
            ),
            mock.patch.object(
                runner.os, "sched_getaffinity", return_value=set(range(32)),
                create=True,
            ),
            mock.patch.object(runner.os, "cpu_count", return_value=32),
            mock.patch.object(
                runner, "read_small_text", side_effect=controller
            ),
        ):
            signals = runner.capacity_signals()
            plan = runner.capacity_plan(None, 100, signals)

        self.assertEqual(1, signals.get("cgroup_v1"))
        self.assertEqual(1, plan["usable"])
        self.assertEqual(1, plan["budget"])
        self.assertEqual(1, plan["effective_jobs"])

    def test_missing_capacity_signals_fall_back_to_one(self):
        require_runner_features(self, "capacity_plan", "capacity_signals")
        with (
            mock.patch.object(
                runner.os, "process_cpu_count", return_value=None, create=True
            ),
            mock.patch.object(
                runner.os, "sched_getaffinity", side_effect=OSError,
                create=True,
            ),
            mock.patch.object(runner.os, "cpu_count", return_value=None),
            mock.patch.object(runner, "read_small_text", side_effect=OSError),
        ):
            signals = runner.capacity_signals()
            plan = runner.capacity_plan(None, 5, signals)

        self.assertEqual({}, signals)
        self.assertEqual(1, plan["usable"])
        self.assertEqual(1, plan["effective_jobs"])

    def test_invalid_override_is_rejected_before_discovery(self):
        fixture = self.fixture({
            "test_never.py": "raise AssertionError('discovery must not run')\n",
        })

        for value in ("0", "-1", "not-a-number"):
            with self.subTest(value=value):
                result = fixture.run("--jobs", value)
                self.assertEqual(2, result.returncode)
                self.assertNotIn("discovery must not run", result.stderr)

    def test_manifest_smaller_than_budget_creates_no_empty_shards(self):
        fixture = self.fixture({
            "test_small_a.py": """
                import unittest
                class SmallA(unittest.TestCase):
                    def test_one(self): pass
            """,
            "test_small_b.py": """
                import unittest
                class SmallB(unittest.TestCase):
                    def test_two(self): pass
            """,
        })

        result = fixture.run("--jobs", "8")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(2, summary["capacity"]["effective_jobs"])
        self.assertEqual([1, 1], summary["assignment"]["shard_counts"])

    def test_corrupt_timing_cache_is_visible_but_cannot_block_execution(self):
        fixture = self.fixture({
            "test_cache.py": """
                import unittest
                class Cache(unittest.TestCase):
                    def test_pass(self): pass
            """,
        })
        cache = fixture.root / "tmp" / "check-runner" / "timings-v1.json"
        cache.parent.mkdir(parents=True)
        cache.write_text("{not json", encoding="utf-8")

        result = fixture.run("--jobs", "1")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("corrupt", summary["cache"]["status"])
        self.assertEqual(0, summary["cache"]["hits"])
        self.assertEqual(1, summary["cache"]["neutral"])
        rewritten = json.loads(cache.read_text(encoding="utf-8"))
        self.assertEqual("wildcat.test-timings.v1", rewritten["schema"])

    def test_timing_cache_read_refuses_a_linked_parent_outside_the_run_root(self):
        identifiers = ["suite.test_a"]
        entries = [{"id": identifiers[0], "seconds": 9.0}]
        payload = {
            "schema": runner.TIMING_SCHEMA,
            "manifest_digest": runner.manifest_digest(identifiers),
            "entries": entries,
            "entries_digest": runner.cache_entries_digest(entries),
        }
        with (
            tempfile.TemporaryDirectory(prefix="cache-root-") as root_raw,
            tempfile.TemporaryDirectory(prefix="cache-outside-") as outside_raw,
        ):
            root = Path(root_raw)
            outside = Path(outside_raw)
            (outside / "check-runner").mkdir()
            external = outside / "check-runner" / "timings-v1.json"
            external.write_text(json.dumps(payload), encoding="utf-8")
            before = external.read_bytes()
            (root / "tmp").symlink_to(outside, target_is_directory=True)

            timings, info = runner.load_timing_cache(
                runner.cache_path_for(root), identifiers
            )
            with self.assertRaises(OSError):
                runner.write_timing_cache(
                    root, identifiers, {identifiers[0]: 1.0}
                )

            self.assertEqual({}, timings)
            self.assertEqual("unsafe", info["status"])
            self.assertEqual(before, external.read_bytes())

    def test_large_parseable_cache_number_is_a_visible_neutral_entry(self):
        identifiers = ["suite.test_a"]
        huge = 10 ** 309
        entries = [{"id": identifiers[0], "seconds": huge}]
        payload = {
            "schema": runner.TIMING_SCHEMA,
            "manifest_digest": runner.manifest_digest(identifiers),
            "entries": entries,
            "entries_digest": runner.cache_entries_digest(entries),
        }
        with tempfile.TemporaryDirectory(prefix="cache-number-") as root_raw:
            root = Path(root_raw)
            cache = runner.cache_path_for(root)
            cache.parent.mkdir(parents=True)
            cache.write_text(json.dumps(payload), encoding="utf-8")

            try:
                timings, info = runner.load_timing_cache(cache, identifiers)
                runner.write_timing_cache(
                    root, identifiers, {identifiers[0]: huge}
                )
            except OverflowError as error:
                self.fail(f"cache numeric refusal escaped its boundary: {error}")

            rewritten = json.loads(cache.read_text(encoding="utf-8"))

        self.assertEqual({}, timings)
        self.assertEqual("partial", info["status"])
        self.assertEqual(1, info["corrupt_entries"])
        self.assertEqual(1, info["neutral"])
        self.assertEqual([], rewritten["entries"])

    def test_timing_cache_atomic_replace_stays_on_its_bound_directory(self):
        identifiers = ["suite.test_a"]
        with (
            tempfile.TemporaryDirectory(prefix="cache-root-") as root_raw,
            tempfile.TemporaryDirectory(prefix="cache-outside-") as outside_raw,
        ):
            root = Path(root_raw)
            outside = Path(outside_raw)
            parent = root / "tmp" / "check-runner"
            parent.mkdir(parents=True)
            moved = root / "bound-cache-parent"
            external = outside / "timings-v1.json"
            external.write_text("EXTERNAL-SENTINEL", encoding="utf-8")
            original_replace = runner.os.replace

            def substitute_parent(source, target, *args, **kwargs):
                parent.rename(moved)
                parent.symlink_to(outside, target_is_directory=True)
                if not kwargs:
                    (outside / Path(source).name).write_text(
                        "ATTACKER-TEMP", encoding="utf-8"
                    )
                return original_replace(source, target, *args, **kwargs)

            with mock.patch.object(
                runner.os, "replace", side_effect=substitute_parent
            ):
                runner.write_timing_cache(
                    root, identifiers, {identifiers[0]: 1.0}
                )

            self.assertEqual(
                "EXTERNAL-SENTINEL", external.read_text(encoding="utf-8")
            )
            self.assertTrue((moved / "timings-v1.json").is_file())

    def test_deep_json_is_a_stable_corrupt_cache_not_a_recursion_escape(self):
        identifiers = ["suite.test_a"]
        with tempfile.TemporaryDirectory(prefix="cache-json-") as root_raw:
            root = Path(root_raw)
            cache = runner.cache_path_for(root)
            cache.parent.mkdir(parents=True)
            cache.write_text("{}", encoding="utf-8")
            with mock.patch.object(
                runner.json,
                "loads",
                side_effect=RecursionError("hostile JSON nesting"),
            ):
                try:
                    timings, info = runner.load_timing_cache(cache, identifiers)
                except RecursionError as error:
                    self.fail(f"JSON recursion escaped its boundary: {error}")

        self.assertEqual({}, timings)
        self.assertEqual("corrupt", info["status"])

    def test_existing_json_number_refusals_remain_stable(self):
        for body in ('{"seconds": NaN}', '{"seconds": ' + "9" * 10_000 + '}'):
            with self.subTest(body=body[:24]), self.assertRaises(ValueError):
                runner.strict_json_loads(body)


class FixtureSkipAccounting(RunnerCase):
    def test_module_fixture_domain_is_not_split_across_workers(self):
        require_runner_features(self, "fixture_domains")
        fixture = self.fixture({
            "test_shared_fixture.py": """
                from pathlib import Path
                import unittest

                def setUpModule():
                    with Path(__file__).with_name("setup-count").open("ab") as handle:
                        handle.write(b"x")

                class Shared(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["assignment"]["fixture_domains"])
        self.assertTrue(summary["assignment"]["fixture_domains_atomic"])
        self.assertEqual([2], summary["assignment"]["shard_counts"])
        self.assertEqual(
            b"x", (fixture.root / "setup-count").read_bytes()
        )

    def test_import_registered_module_cleanup_keeps_one_suite_domain(self):
        require_runner_features(
            self, "fixture_domains", "suite_has_pending_module_cleanups"
        )
        fixture = self.fixture({
            "test_module_cleanup.py": """
                from pathlib import Path
                import unittest

                def record_cleanup():
                    with Path(__file__).with_name("cleanup-count").open("ab") as handle:
                        handle.write(b"x")

                unittest.addModuleCleanup(record_cleanup)

                class Cleaned(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["assignment"]["fixture_domains"])
        self.assertEqual([2], summary["assignment"]["shard_counts"])
        self.assertEqual(
            b"x", (fixture.root / "cleanup-count").read_bytes()
        )

    def test_class_fixture_domain_is_not_split_across_workers(self):
        require_runner_features(self, "fixture_domains")
        fixture = self.fixture({
            "test_shared_class.py": """
                from pathlib import Path
                import unittest

                class Shared(unittest.TestCase):
                    @classmethod
                    def setUpClass(cls):
                        with Path(__file__).with_name("class-setup-count").open("ab") as handle:
                            handle.write(b"x")

                    def test_a(self): pass
                    def test_b(self): pass

                class Independent(unittest.TestCase):
                    def test_c(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(2, summary["capacity"]["effective_jobs"])
        self.assertEqual(2, summary["assignment"]["fixture_domains"])
        self.assertEqual([2, 1], summary["assignment"]["shard_counts"])
        self.assertEqual(
            b"x", (fixture.root / "class-setup-count").read_bytes()
        )

    def test_unfixtured_tests_retain_fine_grained_distribution(self):
        require_runner_features(self, "fixture_domains")
        fixture = self.fixture({
            "test_independent.py": """
                import unittest

                class Independent(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(2, summary["capacity"]["effective_jobs"])
        self.assertEqual(2, summary["assignment"]["fixture_domains"])
        self.assertEqual([1, 1], summary["assignment"]["shard_counts"])

    def test_runtime_registered_standard_cleanups_cannot_split_domains(self):
        require_runner_features(self, "fixture_domains")
        cases = {
            "class": {
                "source": """
                    import unittest

                    class RuntimeCleaned(unittest.TestCase):
                        def test_a(self):
                            self.addClassCleanup(lambda: None)

                        def test_b(self):
                            pass
                """,
                "count": 2,
            },
            "module": {
                "source": """
                    import unittest

                    def register_cleanup():
                        unittest.addModuleCleanup(lambda: None)

                    class First(unittest.TestCase):
                        def test_a(self):
                            register_cleanup()

                    class Second(unittest.TestCase):
                        def test_b(self):
                            pass
                """,
                "count": 2,
            },
        }
        for label, case in cases.items():
            with self.subTest(scope=label):
                fixture = self.fixture({
                    f"test_runtime_{label}_cleanup.py": case["source"]
                })
                result = fixture.run("--jobs", "2")

                self.assertEqual(0, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual(1, summary["capacity"]["effective_jobs"])
                self.assertEqual(
                    1, summary["assignment"]["fixture_domains"]
                )
                self.assertEqual(
                    [case["count"]],
                    summary["assignment"]["shard_counts"],
                )

    def test_cross_class_cleanup_registration_cannot_split_domain(self):
        fixture = self.fixture({
            "test_cross_class_cleanup.py": """
                from pathlib import Path
                import unittest

                class ARegistrar(unittest.TestCase):
                    def test_a_registers_cleanup_on_target(self):
                        BTarget.addClassCleanup(
                            lambda: Path(__file__).with_name(
                                "cross-class-cleanup-ran"
                            ).write_text("yes", encoding="ascii")
                        )

                class BTarget(unittest.TestCase):
                    def test_b_target(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["assignment"]["fixture_domains"])
        self.assertEqual([2], summary["assignment"]["shard_counts"])
        self.assertEqual(
            "yes",
            (fixture.root / "cross-class-cleanup-ran").read_text(
                encoding="ascii"
            ),
        )

    def test_inherited_cleanup_registrars_cannot_split_domains(self):
        cases = {
            "class": {
                "files": {
                    "test_inherited_class_cleanup.py": """
                        from pathlib import Path
                        import unittest

                        class BTarget(unittest.TestCase):
                            def test_b_target(self): pass

                        class RegistrarMixin:
                            def test_a_registers_inherited_cleanup(self):
                                BTarget.addClassCleanup(
                                    lambda: Path(__file__).with_name(
                                        "inherited-class-cleanup-ran"
                                    ).write_text("yes", encoding="ascii")
                                )

                        class ASource(RegistrarMixin, unittest.TestCase):
                            pass
                    """,
                },
                "marker": "inherited-class-cleanup-ran",
                "expected": "yes",
            },
            "module": {
                "files": {
                    "cleanup_mixin.py": """
                        from pathlib import Path
                        import unittest

                        class RegistrarMixin:
                            def test_a_registers_inherited_cleanup(self):
                                target = Path(__file__).with_name(
                                    "inherited-module-target-ran"
                                )
                                outcome = Path(__file__).with_name(
                                    "inherited-module-cleanup-order"
                                )
                                unittest.addModuleCleanup(
                                    lambda: outcome.write_text(
                                        "after" if target.exists() else "before",
                                        encoding="ascii",
                                    )
                                )
                    """,
                    "test_inherited_module_cleanup.py": """
                        from pathlib import Path
                        import time
                        import unittest
                        from cleanup_mixin import RegistrarMixin

                        class ASource(RegistrarMixin, unittest.TestCase):
                            pass

                        class BTarget(unittest.TestCase):
                            def test_b_target(self):
                                time.sleep(0.25)
                                Path(__file__).with_name(
                                    "inherited-module-target-ran"
                                ).write_text("yes", encoding="ascii")
                    """,
                },
                "marker": "inherited-module-cleanup-order",
                "expected": "after",
            },
        }
        for label, case in cases.items():
            with self.subTest(scope=label):
                fixture = self.fixture(case["files"])
                result = fixture.run("--jobs", "2")

                self.assertEqual(0, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual(1, summary["capacity"]["effective_jobs"])
                self.assertEqual(1, summary["assignment"]["fixture_domains"])
                self.assertEqual([2], summary["assignment"]["shard_counts"])
                self.assertEqual(
                    case["expected"],
                    (fixture.root / case["marker"]).read_text(
                        encoding="ascii"
                    ),
                )

    def test_dynamic_cross_class_cleanup_target_cannot_split_domain(self):
        fixture = self.fixture({
            "test_dynamic_target_cleanup.py": """
                from pathlib import Path
                import unittest

                class ARegistrar(unittest.TestCase):
                    def test_a_registers_dynamic_target_cleanup(self):
                        globals()["BTarget"].addClassCleanup(
                            lambda: Path(__file__).with_name(
                                "dynamic-target-cleanup-ran"
                            ).write_text("yes", encoding="ascii")
                        )

                class BTarget(unittest.TestCase):
                    def test_b_target(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["assignment"]["fixture_domains"])
        self.assertEqual([2], summary["assignment"]["shard_counts"])
        self.assertEqual(
            "yes",
            (fixture.root / "dynamic-target-cleanup-ran").read_text(
                encoding="ascii"
            ),
        )

    def test_imported_module_cleanup_alias_cannot_split_domain(self):
        fixture = self.fixture({
            "test_cleanup_alias.py": """
                from unittest import TestCase, addModuleCleanup as register_cleanup

                def schedule_cleanup():
                    register_cleanup(lambda: None)

                class First(TestCase):
                    def test_a(self):
                        schedule_cleanup()

                class Second(TestCase):
                    def test_b(self):
                        pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["assignment"]["fixture_domains"])
        self.assertEqual([2], summary["assignment"]["shard_counts"])

    def test_callable_wrapped_cleanup_registration_cannot_split_domains(self):
        cases = {
            "module-partial": {
                "source": """
                    import functools
                    import unittest

                    register = functools.partial(
                        unittest.addModuleCleanup,
                        lambda: None,
                    )

                    class First(unittest.TestCase):
                        def test_a(self):
                            register()

                    class Second(unittest.TestCase):
                        def test_b(self): pass
                """,
                "domains": 1,
                "shards": [2],
            },
            "class-partialmethod": {
                "source": """
                    import functools
                    import unittest

                    class First(unittest.TestCase):
                        register = functools.partialmethod(
                            lambda self: self.addClassCleanup(lambda: None)
                        )

                        def test_a(self):
                            self.register()

                        def test_b(self): pass

                    class Second(unittest.TestCase):
                        def test_c(self): pass
                """,
                "domains": 2,
                "shards": [2, 1],
            },
        }
        for label, case in cases.items():
            with self.subTest(wrapper=label):
                fixture = self.fixture({
                    f"test_{label.replace('-', '_')}.py": case["source"]
                })
                result = fixture.run("--jobs", "2")

                self.assertEqual(0, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual(
                    case["domains"],
                    summary["assignment"]["fixture_domains"],
                )
                self.assertEqual(
                    case["shards"],
                    summary["assignment"]["shard_counts"],
                )

    def test_referenced_callable_cleanup_registration_cannot_split_domain(self):
        helper = """
            import unittest

            class Registrar:
                def __call__(self):
                    unittest.addModuleCleanup(lambda: None)

            register = Registrar()
        """
        cases = {
            "direct": """
                import unittest
                from cleanup_callable import register

                class First(unittest.TestCase):
                    def test_a(self):
                        register()

                class Second(unittest.TestCase):
                    def test_b(self): pass
            """,
            "module": """
                import cleanup_callable
                import unittest

                class First(unittest.TestCase):
                    def test_a(self):
                        cleanup_callable.register()

                class Second(unittest.TestCase):
                    def test_b(self): pass
            """,
        }
        for label, source in cases.items():
            with self.subTest(import_shape=label):
                fixture = self.fixture({
                    "cleanup_callable.py": helper,
                    "test_callable_cleanup.py": source,
                })
                result = fixture.run("--jobs", "2")

                self.assertEqual(0, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual(
                    1, summary["capacity"]["effective_jobs"]
                )
                self.assertEqual(
                    1, summary["assignment"]["fixture_domains"]
                )
                self.assertEqual(
                    [2], summary["assignment"]["shard_counts"]
                )

    def test_referenced_opaque_callable_does_not_create_fixture_domain(self):
        fixture = self.fixture({
            "opaque_callable.py": "calculate = len\n",
            "test_opaque_callable.py": """
                import unittest
                from opaque_callable import calculate

                class First(unittest.TestCase):
                    def test_a(self):
                        self.assertEqual(0, calculate([]))

                class Second(unittest.TestCase):
                    def test_b(self): pass
            """,
        })
        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(2, summary["capacity"]["effective_jobs"])
        self.assertEqual(2, summary["assignment"]["fixture_domains"])
        self.assertEqual([1, 1], summary["assignment"]["shard_counts"])

    def test_transitive_imported_cleanup_helpers_cannot_split_domain(self):
        helper = """
            import unittest

            def register_cleanup():
                unittest.addModuleCleanup(lambda: None)
        """
        cases = {
            "direct": """
                import unittest
                from cleanup_helper import register_cleanup

                class First(unittest.TestCase):
                    def test_a(self):
                        register_cleanup()

                class Second(unittest.TestCase):
                    def test_b(self):
                        pass
            """,
            "module": """
                import cleanup_helper
                import unittest

                class First(unittest.TestCase):
                    def test_a(self):
                        cleanup_helper.register_cleanup()

                class Second(unittest.TestCase):
                    def test_b(self):
                        pass
            """,
        }
        for label, source in cases.items():
            with self.subTest(import_shape=label):
                fixture = self.fixture({
                    "cleanup_helper.py": helper,
                    "test_transitive_cleanup.py": source,
                })

                result = fixture.run("--jobs", "2")

                self.assertEqual(0, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual(
                    1, summary["capacity"]["effective_jobs"]
                )
                self.assertEqual(
                    1, summary["assignment"]["fixture_domains"]
                )
                self.assertEqual(
                    [2], summary["assignment"]["shard_counts"]
                )

    def test_nested_cleanup_helpers_and_context_registration_cannot_split_domains(self):
        cases = {
            "nested-import": {
                "files": {
                    "cleanup_helper.py": """
                        import unittest

                        def inner_cleanup():
                            unittest.addModuleCleanup(lambda: None)

                        def register_cleanup():
                            inner_cleanup()
                    """,
                    "test_nested_cleanup.py": """
                        import unittest
                        from cleanup_helper import register_cleanup

                        class First(unittest.TestCase):
                            def test_a(self):
                                register_cleanup()

                        class Second(unittest.TestCase):
                            def test_b(self): pass
                    """,
                },
            },
            "class-context": {
                "files": {
                    "test_class_context.py": """
                        from contextlib import nullcontext
                        import unittest

                        class Shared(unittest.TestCase):
                            def test_a(self):
                                self.enterClassContext(nullcontext())

                            def test_b(self): pass
                    """,
                },
            },
        }
        for label, case in cases.items():
            with self.subTest(registration=label):
                fixture = self.fixture(case["files"])
                result = fixture.run("--jobs", "2")

                self.assertEqual(0, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual(1, summary["capacity"]["effective_jobs"])
                self.assertEqual(
                    1, summary["assignment"]["fixture_domains"]
                )
                self.assertEqual(
                    [2], summary["assignment"]["shard_counts"]
                )

    def test_callable_bound_cleanup_state_cannot_split_domain(self):
        cases = {
            "closure": """
                import unittest

                def make_register():
                    cleanup = unittest.addModuleCleanup
                    def register():
                        cleanup(lambda: None)
                    return register

                register = make_register()
            """,
            "default": """
                import unittest

                def register(cleanup=unittest.addModuleCleanup):
                    cleanup(lambda: None)
            """,
            "bound-method": """
                import unittest

                class Registrar:
                    def register(self):
                        unittest.addModuleCleanup(lambda: None)

                register = Registrar().register
            """,
            "callable-state": """
                import unittest

                class Registrar:
                    def __init__(self):
                        self.cleanup = unittest.addModuleCleanup

                    def __call__(self):
                        self.cleanup(lambda: None)

                register = Registrar()
            """,
        }
        test_source = """
            import unittest
            from cleanup_helper import register

            class First(unittest.TestCase):
                def test_a(self):
                    register()

            class Second(unittest.TestCase):
                def test_b(self): pass
        """
        for label, helper in cases.items():
            with self.subTest(binding=label):
                fixture = self.fixture({
                    "cleanup_helper.py": helper,
                    "test_bound_cleanup.py": test_source,
                })
                result = fixture.run("--jobs", "2")

                self.assertEqual(0, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual(
                    1, summary["capacity"]["effective_jobs"]
                )
                self.assertEqual(
                    1, summary["assignment"]["fixture_domains"]
                )
                self.assertEqual(
                    [2], summary["assignment"]["shard_counts"]
                )

    def test_worker_rediscovery_cannot_widen_fixture_domain_across_assignments(self):
        fixture = self.fixture({
            "test_worker_fixture_drift.py": """
                from pathlib import Path
                import os
                import unittest

                marker = Path(__file__).with_name("coordinator-imported")
                if marker.exists():
                    def setUpModule():
                        with Path(__file__).with_name("setup-count").open("ab") as handle:
                            handle.write(b"x")
                else:
                    marker.write_text(str(os.getpid()), encoding="ascii")

                class Shared(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(3, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn(
            "worker fixture domain crosses assignment",
            " ".join(summary["scheduler_errors"]),
        )
        self.assertFalse((fixture.root / "setup-count").exists())

    def test_dynamic_module_fixture_lookup_cannot_split_domain(self):
        fixture = self.fixture({
            "test_dynamic_module_fixture.py": """
                from pathlib import Path
                import unittest

                fixture_lookups = 0

                def module_setup():
                    with Path(__file__).with_name("setup-count").open("ab") as handle:
                        handle.write(b"x")

                def __getattr__(name):
                    global fixture_lookups
                    if name == "setUpModule":
                        fixture_lookups += 1
                        if fixture_lookups == 1:
                            return None
                        return module_setup
                    raise AttributeError(name)

                class Shared(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["assignment"]["fixture_domains"])
        self.assertEqual([2], summary["assignment"]["shard_counts"])
        self.assertFalse((fixture.root / "setup-count").exists())

    def test_stateful_class_fixture_descriptor_cannot_split_domain(self):
        fixture = self.fixture({
            "test_dynamic_class_fixture.py": """
                from pathlib import Path
                import unittest

                class FixtureDescriptor:
                    def __init__(self):
                        self.lookups = 0

                    def __get__(self, instance, owner):
                        self.lookups += 1
                        if self.lookups == 1:
                            return None

                        def setup():
                            with Path(__file__).with_name(
                                "class-setup-count"
                            ).open("ab") as handle:
                                handle.write(b"x")

                        return setup

                class Shared(unittest.TestCase):
                    setUpClass = FixtureDescriptor()

                    def test_a(self): pass
                    def test_b(self): pass
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(0, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["assignment"]["fixture_domains"])
        self.assertEqual([2], summary["assignment"]["shard_counts"])
        self.assertFalse((fixture.root / "class-setup-count").exists())

    def test_test_object_cannot_forge_fixture_blocked_disposition(self):
        fixture = self.fixture({
            "test_forged_fixture_skip.py": """
                import unittest

                class Forged(unittest.TestCase):
                    def run(self, result=None):
                        holder = unittest.suite._ErrorHolder(
                            f"setUpClass ({__name__}.Forged)"
                        )
                        result.addSkip(holder, "forged fixture skip")
                        return result

                    def test_body_must_not_disappear(self):
                        raise AssertionError("the test body must execute")
            """,
        })

        result = fixture.run("--jobs", "1")

        self.assertEqual(3, result.returncode, result.stderr)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn(
            "unproved missing assignment",
            " ".join(summary["scheduler_errors"]),
        )

    def test_class_fixture_skip_is_accounted_without_execution(self):
        fixture = self.fixture({
            "test_class_skip.py": """
                import unittest

                class Blocked(unittest.TestCase):
                    @classmethod
                    def setUpClass(cls):
                        raise unittest.SkipTest('optional class fixture')

                    def test_a(self): pass
                    def test_b(self): pass

                class Runs(unittest.TestCase):
                    def test_c(self): pass
            """,
        })
        report = fixture.root / "class-skip.json"

        result = fixture.run(
            "--jobs", "2", "--elenchus-report", str(report)
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 0,
            "errors": 0,
            "skipped": 1,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }, json.loads(report.read_text(encoding="utf-8")))
        summary = self.summary(fixture, result)
        self.assertEqual("passed", summary["status"])
        self.assertEqual(3, summary["assignment"]["assigned"])
        self.assertEqual(1, summary["execution"]["started"])
        self.assertEqual(1, summary["execution"]["completed"])
        self.assertEqual(2, summary["execution"]["fixture_blocked"])
        self.assertFalse(summary["execution"]["executed_once"])
        self.assertTrue(summary["execution"]["exact_accounting"])
        self.assertEqual(
            2,
            sum(
                shard["fixture_blocked_ids"]["count"]
                for shard in summary["shards"]
            ),
        )
        self.assertEqual(
            1,
            sum(
                shard["fixture_skip_holders"]["count"]
                for shard in summary["shards"]
            ),
        )

    def test_module_fixture_skip_is_accounted_without_execution(self):
        fixture = self.fixture({
            "test_module_skip.py": """
                import unittest

                def setUpModule():
                    raise unittest.SkipTest('optional module fixture')

                class First(unittest.TestCase):
                    def test_a(self): pass
                    def test_b(self): pass

                class Second(unittest.TestCase):
                    def test_c(self): pass
            """,
        })
        report = fixture.root / "module-skip.json"

        result = fixture.run(
            "--jobs", "2", "--elenchus-report", str(report)
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 1,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }, json.loads(report.read_text(encoding="utf-8")))
        summary = self.summary(fixture, result)
        self.assertEqual("passed", summary["status"])
        self.assertEqual(0, summary["execution"]["started"])
        self.assertEqual(0, summary["execution"]["completed"])
        self.assertEqual(3, summary["execution"]["fixture_blocked"])
        self.assertFalse(summary["execution"]["executed_once"])
        self.assertTrue(summary["execution"]["exact_accounting"])

    def test_fixture_errors_and_unrecognised_holders_remain_scheduler_errors(self):
        cases = {
            "ordinary-error": """
                import unittest

                class Broken(unittest.TestCase):
                    @classmethod
                    def setUpClass(cls):
                        raise RuntimeError('ordinary fixture error')

                    def test_a(self): pass
            """,
            "unrecognised-holder": """
                import unittest

                class Broken(unittest.TestCase):
                    @classmethod
                    def tearDownClass(cls):
                        raise unittest.SkipTest('not a setup disposition')

                    def test_a(self): pass
            """,
        }
        expected = {
            "ordinary-error": "unproved missing assignment",
            "unrecognised-holder": "unrecognised fixture skip holder",
        }
        for label, source in cases.items():
            with self.subTest(case=label):
                fixture = self.fixture({f"test_{label.replace('-', '_')}.py": source})
                result = fixture.run("--jobs", "1")
                self.assertEqual(3, result.returncode, result.stderr)
                summary = self.summary(fixture, result)
                self.assertEqual("scheduler-error", summary["status"])
                self.assertIn(
                    expected[label], " ".join(summary["scheduler_errors"])
                )

    def test_fixture_blocked_record_refuses_overlap_duplicate_and_unproved_missing(self):
        class Blocked(unittest.TestCase):
            @classmethod
            def setUpClass(cls):
                raise unittest.SkipTest("optional fixture")

            def test_a(self): pass
            def test_b(self): pass

        tests = [Blocked("test_a"), Blocked("test_b")]
        identifiers = [test.id() for test in tests]
        digest = runner.manifest_digest(identifiers)
        assignments = [[0, 1]]
        valid = runner.run_selected_tests(
            tests, assignments[0], 0, 1, digest
        )
        runner.validate_worker_record(
            valid,
            identifiers,
            digest,
            assignments,
            tests=tests,
        )

        def copied():
            return json.loads(json.dumps(valid))

        cases = []
        duplicate = copied()
        duplicate["fixture_blocked_ids"].append(identifiers[0])
        cases.append(("duplicate", duplicate, "do not match skip proof"))

        overlap = copied()
        overlap["started_ids"] = [identifiers[0]]
        overlap["completed_ids"] = [identifiers[0]]
        overlap["durations"] = [[identifiers[0], 0.0]]
        overlap["testsRun"] = 1
        cases.append(("overlap", overlap, "overlaps executed ID"))

        duplicate_holder = copied()
        duplicate_holder["fixture_skip_holders"] *= 2
        duplicate_holder["skipped"] = 2
        cases.append(
            ("duplicate-holder", duplicate_holder, "duplicate fixture skip holder")
        )

        unrecognised = copied()
        unrecognised["fixture_skip_holders"] = ["tearDownClass (foreign.Scope)"]
        cases.append(
            ("unrecognised-holder", unrecognised, "unrecognised fixture skip holder")
        )

        unproved = copied()
        unproved["fixture_skip_holders"] = []
        cases.append(("unproved", unproved, "unproved missing assignment"))

        foreign = copied()
        foreign["fixture_blocked_ids"] = ["foreign.test_id"]
        cases.append(("foreign", foreign, "do not match skip proof"))

        for label, record, message in cases:
            with self.subTest(case=label), self.assertRaisesRegex(
                runner.SchedulerError, message
            ):
                runner.validate_worker_record(
                    record,
                    identifiers,
                    digest,
                    assignments,
                    tests=tests,
                )


class FailureDrainAndStableOutput(RunnerCase):
    def test_unexpected_success_is_non_green(self):
        fixture = self.fixture({
            "test_unexpected_success.py": """
                import unittest

                class UnexpectedSuccess(unittest.TestCase):
                    @unittest.expectedFailure
                    def test_expected_to_fail(self):
                        pass
            """,
        })
        report = fixture.root / "unexpected-success.json"

        result = fixture.run(
            "--jobs", "1", "--elenchus-report", str(report)
        )

        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 1,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 1,
        }, json.loads(report.read_text(encoding="utf-8")))
        summary = self.summary(fixture, result)
        self.assertEqual("test-failure", summary["status"])
        self.assertEqual(1, summary["execution"]["unexpectedSuccesses"])
        self.assertEqual([], summary["scheduler_errors"])
        self.assertIn("1 unexpected success events", result.stdout)

    def test_descendant_cannot_hold_worker_output_descriptor_open(self):
        fixture = self.fixture({
            "test_descendant.py": """
                import subprocess
                import sys
                import unittest

                class Descendant(unittest.TestCase):
                    def test_inherited_output_descriptor(self):
                        subprocess.Popen([
                            sys.executable,
                            "-c",
                            "import time; time.sleep(4)",
                        ])
            """,
        })

        started = time.monotonic()
        result = fixture.run("--jobs", "1")
        elapsed = time.monotonic() - started

        self.assertEqual(3, result.returncode, result.stderr)
        self.assertLess(elapsed, 3.0)
        summary = self.summary(fixture, result)
        self.assertEqual("scheduler-error", summary["status"])
        self.assertIn(
            "output descriptor remained open after worker exit",
            " ".join(summary["scheduler_errors"]),
        )

    def test_detached_descendant_is_red_bounded_and_not_claimed_terminated(self):
        fixture = self.fixture({
            "test_detached_descendant.py": """
                import os
                import subprocess
                import sys
                import unittest

                class DetachedDescendant(unittest.TestCase):
                    def test_inherited_output_descriptor(self):
                        child = subprocess.Popen(
                            [
                                sys.executable,
                                "-c",
                                "import time; time.sleep(30)",
                            ],
                            start_new_session=True,
                        )
                        with open(
                            "detached-child.pid", "w", encoding="ascii"
                        ) as stream:
                            stream.write(str(child.pid))
            """,
        })

        started = time.monotonic()
        result = fixture.run("--jobs", "1")
        elapsed = time.monotonic() - started
        child_pid = int(
            (fixture.root / "detached-child.pid").read_text(encoding="ascii")
        )
        try:
            os.kill(child_pid, 0)
            self.assertEqual(3, result.returncode, result.stderr)
            self.assertLess(elapsed, 3.0)
            summary = self.summary(fixture, result)
            errors = " ".join(summary["scheduler_errors"])
            self.assertEqual("scheduler-error", summary["status"])
            self.assertIn("a descendant may have detached", errors)
            self.assertNotIn("descendant process group terminated", errors)
        finally:
            try:
                os.killpg(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_test_output_cannot_forge_the_structured_run_summary(self):
        fixture = self.fixture({
            "test_reserved_output.py": """
                import sys
                import unittest

                class ReservedOutput(unittest.TestCase):
                    def test_reserved_prefix(self):
                        print('HEXAEMERON-RUN {"schema":"forged-stdout"}')
                        print(
                            'HEXAEMERON-RUN {"schema":"forged-stderr"}',
                            file=sys.stderr,
                        )
            """,
        })

        result = fixture.run("--jobs", "1")

        self.assertEqual(0, result.returncode, result.stderr)
        structured_lines = [
            line
            for line in result.stdout.splitlines()
            if line.startswith(SUMMARY_PREFIX)
        ]
        self.assertEqual(1, len(structured_lines), result.stdout)
        self.assertEqual(
            "wildcat.hexaemeron-run.v1",
            json.loads(structured_lines[0][len(SUMMARY_PREFIX):])["schema"],
        )
        self.assertIn(
            'HEXAEMERON-TEST-OUTPUT HEXAEMERON-RUN '
            '{"schema":"forged-stdout"}',
            result.stdout,
        )
        self.assertIn(
            'HEXAEMERON-TEST-OUTPUT HEXAEMERON-RUN '
            '{"schema":"forged-stderr"}',
            result.stderr,
        )
        self.assertFalse(any(
            line.startswith(SUMMARY_PREFIX)
            for line in result.stderr.splitlines()
        ))

    def test_single_worker_child_fd_output_is_bounded_and_replayed(self):
        fixture = self.fixture({
            "test_raw_output.py": """
                import subprocess
                import sys
                import unittest

                class RawOutput(unittest.TestCase):
                    def test_raw_fd(self):
                        subprocess.run(
                            [
                                sys.executable,
                                '-c',
                                "import os; os.write(1, b'@' * 300_000)",
                            ],
                            check=True,
                        )
            """,
        })

        result = fixture.run("--jobs", "1")

        self.assertEqual(0, result.returncode, result.stderr)
        header = "===== hexaemeron shard 1/1 (1 tests) ====="
        marker = "\n... output truncated; 300000 bytes emitted ...\n"
        self.assertIn(header, result.stdout)
        self.assertIn(marker, result.stdout)
        self.assertLess(result.stdout.index(header), result.stdout.index("@"))
        self.assertEqual(runner.MAX_OUTPUT_BYTES, result.stdout.count("@"))
        summary = self.summary(fixture, result)
        self.assertEqual(1, summary["capacity"]["effective_jobs"])
        self.assertEqual(1, summary["queue"]["queue_high_water"])
        self.assertEqual(1, summary["queue"]["maximum_observed_live_children"])

    def test_multiple_failing_subtests_remain_test_failure_evidence(self):
        fixture = self.fixture({
            "test_subtests.py": """
                import unittest

                class Subtests(unittest.TestCase):
                    def test_a_multiple_failures(self):
                        for number in range(2):
                            with self.subTest(number=number):
                                self.fail(f'failure {number}')

                    def test_b_passes(self):
                        pass
            """,
        })
        report = fixture.root / "subtests.json"

        result = fixture.run(
            "--jobs", "2", "--elenchus-report", str(report)
        )

        self.assertEqual(1, result.returncode, result.stderr)
        self.assertEqual({
            "schema": "elenchus.unittest.v1",
            "complete": True,
            "testsRun": 2,
            "failures": 2,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
        }, json.loads(report.read_text(encoding="utf-8")))
        summary = self.summary(fixture, result)
        self.assertEqual("test-failure", summary["status"])
        self.assertEqual([], summary["scheduler_errors"])

    def test_pipe_read_failure_is_scheduler_evidence(self):
        capture = runner.BoundedBytes()

        runner.drain_process_stream(BrokenReadPipe(), capture)

        self.assertEqual(
            [
                "worker 0 stdout pipe read failed: "
                "synthetic pipe read failure"
            ],
            (
                runner.pipe_drain_errors([(capture, runner.BoundedBytes())])
                if hasattr(runner, "pipe_drain_errors")
                else []
            ),
        )

    def test_all_started_shards_drain_after_failures(self):
        fixture = self.fixture({
            "test_failures_a.py": """
                import unittest

                class FastFailure(unittest.TestCase):
                    def test_a_fails_fast(self):
                        self.fail('first failure')
            """,
            "test_failures_b.py": """
                from pathlib import Path
                import time
                import unittest

                class LateFailure(unittest.TestCase):
                    def test_b_finishes_late(self):
                        time.sleep(0.15)
                        Path('late-shard-finished').write_text('done', encoding='utf-8')
                        self.fail('second failure')
            """,
        })
        report = fixture.root / "result.json"

        result = fixture.run("--jobs", "2", "--elenchus-report", str(report))

        self.assertEqual(1, result.returncode)
        self.assertEqual("done", (fixture.root / "late-shard-finished").read_text())
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(2, payload["testsRun"])
        self.assertEqual(2, payload["failures"])
        summary = self.summary(fixture, result)
        self.assertEqual(2, summary["execution"]["completed"])

    def test_output_is_replayed_in_shard_order_not_completion_order(self):
        fixture = self.fixture({
            "test_output_a.py": """
                import time
                import unittest

                class SlowOutput(unittest.TestCase):
                    def test_a_slow(self):
                        time.sleep(0.15)
                        print('OUTPUT-FROM-CANONICAL-FIRST')
                        self.fail('first')
            """,
            "test_output_b.py": """
                import unittest

                class FastOutput(unittest.TestCase):
                    def test_b_fast(self):
                        print('OUTPUT-FROM-CANONICAL-SECOND')
                        self.fail('second')
            """,
        })

        result = fixture.run("--jobs", "2")

        self.assertEqual(1, result.returncode)
        combined = result.stdout + result.stderr
        self.assertLess(
            combined.index("OUTPUT-FROM-CANONICAL-FIRST"),
            combined.index("OUTPUT-FROM-CANONICAL-SECOND"),
        )
        self.assertLess(combined.index("shard 1/2"), combined.index("shard 2/2"))


class CopiedRunnerCompatibility(RunnerCase):
    def test_copied_runner_keeps_positional_and_flag_reports_with_parallel_tests(self):
        source = """
            import unittest

            def load_tests(loader, standard, pattern):
                class Generated(unittest.TestCase):
                    pass
                for number in range(2):
                    def generated(self, number=number): pass
                    setattr(Generated, f'test_generated_{number}', generated)
                return loader.loadTestsFromTestCase(Generated)
        """
        for mode in ("positional", "flag"):
            with self.subTest(mode=mode):
                fixture = self.fixture({"test_copy.py": source})
                report = fixture.root / f"{mode}.json"
                arguments = (
                    ("--jobs", "2", str(report))
                    if mode == "positional"
                    else ("--jobs", "2", "--elenchus-report", str(report))
                )
                result = fixture.run(*arguments)
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual({
                    "schema": "elenchus.unittest.v1",
                    "complete": True,
                    "testsRun": 2,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                    "expectedFailures": 0,
                    "unexpectedSuccesses": 0,
                }, json.loads(report.read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
