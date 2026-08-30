#!/usr/bin/env python3
"""Run the Hexaemeron suite through a fresh, accounted test manifest.

``wildcat.hexaemeron-assignment.v1`` is the private coordinator/worker
protocol. An assignment is bounded JSON containing the runner digest, suite
root, complete manifest digest and canonical indices. A worker rediscovers
the suite, verifies those identities, and selects the already discovered test
objects at the assigned indices. Worker results use
``wildcat.hexaemeron-worker-result.v1`` and name every started, completed and
fixture-blocked test. A fixture-blocked ID is bound to a real class- or
module-fixture ``SkipTest`` event and is never reported as executed. Only the
coordinator writes the compatible Elenchus report.

Tests that share an active standard class or module fixture form one
indivisible scheduling domain. Tests without those fixtures remain independent
timing units, so fixture correctness does not collapse safe parallel work.

The ``wildcat.hexaemeron-run.v1`` event records its bounded ordered manifest
once. Per-shard ``wildcat.hexaemeron-shard-sequence.v1`` count-and-digest
bindings correlate assigned, started, completed, fixture-blocked and duration
sequences back to canonical manifest indices without repeating every
identifier in output.
Parallel worker text travels only through coordinator-owned bounded pipes;
private result JSON carries accounting, not a second expandable output copy.

Timing data uses ``wildcat.test-timings.v1``. It may change shard balance but
never manifest membership or a test verdict. Missing or corrupt data is a
visible cache miss. Public compatibility remains ``[--jobs POSITIVE_INT]``
plus either one positional report path or ``--elenchus-report PATH``.
"""

import argparse
from collections import Counter
import contextlib
import dis
import functools
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import types
import unittest

try:
    import resource
except ImportError:  # pragma: no cover - the secure reporter already refuses Windows
    resource = None


MANIFEST_SCHEMA = "wildcat.hexaemeron-manifest.v1"
ASSIGNMENT_SCHEMA = "wildcat.hexaemeron-assignment.v1"
WORKER_RESULT_SCHEMA = "wildcat.hexaemeron-worker-result.v1"
RUN_SCHEMA = "wildcat.hexaemeron-run.v1"
TIMING_SCHEMA = "wildcat.test-timings.v1"
SHARD_SEQUENCE_SCHEMA = "wildcat.hexaemeron-shard-sequence.v1"
SCHEDULER_ERROR_EVIDENCE_SCHEMA = (
    "wildcat.hexaemeron-scheduler-error-evidence.v1"
)
RESULT_JSON_OUTPUT = "result-json"
COORDINATOR_PIPE_OUTPUT = "coordinator-pipes"
SUMMARY_PREFIX = "HEXAEMERON-RUN "
TEST_OUTPUT_PREFIX = "HEXAEMERON-TEST-OUTPUT "
MAX_JOBS = 256
MAX_TESTS = 100_000
MAX_IDENTIFIER_BYTES = 4_096
MAX_MANIFEST_BYTES = 327_680
MAX_ASSIGNMENT_BYTES = 1_048_576
MAX_JSON_NUMBER_BYTES = 32
MAX_WORKER_RESULT_FIXED_BYTES = 16_384
# A result repeats bounded identifier-like values in six escaped JSON
# positions: assigned, started, completed, fixture-blocked, duration IDs and
# fixture-skip holders. It then adds one bounded index and one bounded duration
# token per possible manifest item. The fixed reserve covers schemas, counters,
# list framing, and scalar fields.
MAX_WORKER_RESULT_BYTES = (
    6 * MAX_MANIFEST_BYTES
    + MAX_TESTS * (len(str(MAX_TESTS - 1)) + 1)
    + MAX_TESTS * (MAX_JSON_NUMBER_BYTES + 4)
    + MAX_WORKER_RESULT_FIXED_BYTES
)
MAX_RUN_SUMMARY_BYTES = 2_097_152
MAX_CACHE_BYTES = 4_194_304
MAX_OUTPUT_BYTES = 262_144
MAX_TEST_SECONDS = 86_400.0
CACHE_PARTS = ("tmp", "check-runner", "timings-v1.json")
PIPE_DRAIN_GRACE_SECONDS = 0.25
DESCENDANT_TERM_GRACE_SECONDS = 0.5
DESCENDANT_KILL_GRACE_SECONDS = 0.5


class SchedulerError(RuntimeError):
    """A stable discovery, assignment, worker, or accounting refusal."""


class DuplicateKeyError(ValueError):
    """A JSON object repeated a key and is not a unique protocol value."""


class AggregateResult:
    """The counters needed by the unchanged Elenchus unittest schema."""

    def __init__(self, counts=None):
        counts = counts or {}
        for field in (
            "testsRun",
            "failures",
            "errors",
            "skipped",
            "expectedFailures",
            "unexpectedSuccesses",
        ):
            value = counts.get(field, 0)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 0
                or value > sys.maxsize
            ):
                raise SchedulerError(
                    f"aggregate {field} exceeds sequence bound"
                )
        self.testsRun = counts.get("testsRun", 0)
        # Subtests can emit more outcome events than top-level tests.  Ranges
        # preserve the report's existing len()-based interface without
        # allocating one coordinator object per worker event.
        self.failures = range(counts.get("failures", 0))
        self.errors = range(counts.get("errors", 0))
        self.skipped = range(counts.get("skipped", 0))
        self.expectedFailures = range(counts.get("expectedFailures", 0))
        self.unexpectedSuccesses = range(
            counts.get("unexpectedSuccesses", 0)
        )


def positive_jobs(raw):
    """Parse one bounded positive process budget before discovery starts."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        raise argparse.ArgumentTypeError("--jobs requires a positive integer")
    if value < 1 or value > MAX_JOBS:
        raise argparse.ArgumentTypeError(
            f"--jobs must be between 1 and {MAX_JOBS}"
        )
    return value


def argument_parser():
    """Return the public parser plus its paired private worker arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "report",
        nargs="?",
        metavar="PATH",
        help="the source-bound Elenchus report path",
    )
    parser.add_argument(
        "--elenchus-report",
        action="append",
        metavar="PATH",
        help="write an elenchus.unittest.v1 result to a fresh worktree path",
    )
    parser.add_argument(
        "--jobs",
        type=positive_jobs,
        metavar="POSITIVE_INT",
        help="override the automatic quota-aware process budget",
    )
    parser.add_argument(
        "--_worker-assignment",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--_worker-result",
        help=argparse.SUPPRESS,
    )
    return parser


def bind_report_target(raw, parser):
    """Bind one fresh report path to its current worktree identity."""
    if not raw or "\x00" in raw:
        parser.error("--elenchus-report requires a non-empty path")
    supplied = Path(raw)
    if ".." in supplied.parts:
        parser.error("--elenchus-report must stay inside the current worktree")
    try:
        cwd = Path.cwd()
        root = cwd.resolve(strict=True)
        lexical_target = supplied if supplied.is_absolute() else cwd / supplied
        if lexical_target.is_symlink():
            parser.error("--elenchus-report target must not already exist")
        target = (
            supplied if supplied.is_absolute() else root / supplied
        ).resolve(strict=False)
        relative = target.relative_to(root)
    except (OSError, RuntimeError, ValueError):
        parser.error("--elenchus-report must stay inside the current worktree")

    if any(part.casefold() == ".git" for part in relative.parts):
        parser.error("--elenchus-report must not enter Git control paths")

    current = root
    for part in relative.parts[:-1]:
        current /= part
        try:
            current_stat = current.lstat()
        except FileNotFoundError:
            break
        except OSError:
            parser.error("--elenchus-report cannot be inspected")
        if not stat.S_ISDIR(current_stat.st_mode):
            parser.error("--elenchus-report parent is not a directory")
    try:
        existing = target.lstat()
    except FileNotFoundError:
        existing = None
    except (OSError, ValueError):
        parser.error("--elenchus-report cannot be inspected")
    if existing is not None:
        parser.error("--elenchus-report target must not already exist")

    missing = []
    for name in ("O_DIRECTORY", "O_NOFOLLOW"):
        if not hasattr(os, name):
            missing.append(f"os.{name}")
    supports_dir_fd = getattr(os, "supports_dir_fd", ())
    for operation, name in (
        (os.open, "os.open(dir_fd)"),
        (os.mkdir, "os.mkdir(dir_fd)"),
        (os.stat, "os.stat(dir_fd)"),
        (os.unlink, "os.unlink(dir_fd)"),
    ):
        if operation not in supports_dir_fd:
            missing.append(name)
    supports_follow_symlinks = getattr(os, "supports_follow_symlinks", ())
    if os.stat not in supports_follow_symlinks:
        missing.append("os.stat(follow_symlinks)")
    if missing:
        parser.error(
            "--elenchus-report requires secure directory operations: "
            + ", ".join(missing)
        )
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        root_stat = root.stat()
        root_fd = os.open(root, directory_flags)
        try:
            opened_stat = os.fstat(root_fd)
        finally:
            os.close(root_fd)
    except OSError:
        parser.error("--elenchus-report worktree cannot be opened and inspected")
    if (opened_stat.st_dev, opened_stat.st_ino) != (
        root_stat.st_dev,
        root_stat.st_ino,
    ):
        parser.error("--elenchus-report worktree changed during inspection")
    return root, (opened_stat.st_dev, opened_stat.st_ino), relative.parts


def parse_arguments(argv):
    """Parse public compatibility forms or one complete private worker form."""
    parser = argument_parser()
    arguments = parser.parse_args(argv)
    private = bool(
        arguments._worker_assignment is not None
        or arguments._worker_result is not None
    )
    values = list(arguments.elenchus_report or [])
    if arguments.report is not None:
        values.append(arguments.report)
    if private:
        if not arguments._worker_assignment or not arguments._worker_result:
            parser.error("private worker mode requires assignment and result paths")
        if values or arguments.jobs is not None:
            parser.error("private worker mode cannot write a public report or set jobs")
        return arguments, None
    if len(values) > 1:
        parser.error("name one report path, either positionally or with --elenchus-report")
    target = bind_report_target(values[0], parser) if values else None
    return arguments, target


def report_target(argv):
    """Preserve the report-path parser interface used by older callers."""
    return parse_arguments(argv)[1]


def result_payload(result, complete=True):
    """Return Elenchus's complete, unchanged unittest counter schema."""
    return {
        "schema": "elenchus.unittest.v1",
        "complete": bool(complete),
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }


def report_parent(root_fd, parts):
    """Open or create report directories without following a symlink."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current_fd = os.dup(root_fd)
    try:
        for part in parts:
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except FileNotFoundError:
                try:
                    os.mkdir(part, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except OSError:
        os.close(current_fd)
        raise


def report_root(root, identity):
    """Reopen the bound worktree and refuse a replaced directory."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open(root, flags)
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino) != identity:
            raise OSError("report worktree identity changed")
        return descriptor
    except OSError:
        os.close(descriptor)
        raise


def remove_created_report(parent_fd, name, created):
    """Remove a failed write only while the target is still our inode."""
    try:
        current = os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
    except OSError:
        return
    if (current.st_dev, current.st_ino) != (created.st_dev, created.st_ino):
        return
    try:
        os.unlink(name, dir_fd=parent_fd)
    except OSError:
        pass


def write_report(target, payload):
    """Create the declared report through its bound worktree identity."""
    root, identity, parts = target
    if not parts:
        raise OSError("report path has no filename")
    root_fd = report_root(root, identity)
    try:
        parent_fd = report_parent(root_fd, parts[:-1])
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = None
        created = None
        try:
            descriptor = os.open(parts[-1], flags, 0o600, dir_fd=parent_fd)
            created = os.fstat(descriptor)
            if not stat.S_ISREG(created.st_mode):
                raise OSError("report target is not a regular file")
            body = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
            remaining = memoryview(body)
            while remaining:
                written = os.write(descriptor, remaining)
                if written <= 0:
                    raise OSError("report write made no progress")
                remaining = remaining[written:]
            os.close(descriptor)
            descriptor = None
        except OSError:
            if descriptor is not None:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
            if created is not None:
                remove_created_report(parent_fd, parts[-1], created)
            raise
        finally:
            os.close(parent_fd)
    finally:
        os.close(root_fd)


def reject_duplicate_keys(pairs):
    """Reject duplicate protocol keys instead of accepting the final value."""
    value = {}
    for key, item in pairs:
        if key in value:
            raise DuplicateKeyError(f"duplicate JSON key: {key}")
        value[key] = item
    return value


def reject_json_constant(raw):
    """Reject NaN and infinities, which are not JSON numbers."""
    raise ValueError(f"invalid JSON constant: {raw}")


def json_number_bytes(value):
    """Return one strict JSON numeric token's encoded byte length."""
    return len(
        json.dumps(
            value,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("ascii")
    )


def is_bounded_json_number(value):
    """Accept only finite numbers with one bounded strict JSON token."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        return (
            json_number_bytes(value) <= MAX_JSON_NUMBER_BYTES
            and math.isfinite(value)
        )
    except (TypeError, ValueError, OverflowError):
        return False


def strict_json_loads(body):
    """Read strict JSON for every cache and worker filesystem boundary."""
    try:
        return json.loads(
            body,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_json_constant,
        )
    except RecursionError as error:
        raise ValueError("JSON nesting exceeds the decoder limit") from error


def read_bounded_file(path, maximum):
    """Read one regular no-follow file up to a fixed byte boundary."""
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("input is not a regular file")
        if opened.st_size > maximum:
            raise OSError("input exceeds its size limit")
        chunks = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(65_536, maximum + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                raise OSError("input exceeds its size limit")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def read_bounded_at(directory_fd, name, maximum):
    """Read a bounded regular basename through an already bound directory."""
    if not name or name in (".", "..") or "/" in name:
        raise OSError("protocol input name is not a basename")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, dir_fd=directory_fd)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("protocol input is not a regular file")
        if opened.st_size > maximum:
            raise OSError("protocol input exceeds its size limit")
        chunks = []
        total = 0
        while True:
            chunk = os.read(
                descriptor, min(65_536, maximum + 1 - total)
            )
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > maximum:
                raise OSError("protocol input exceeds its size limit")
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def digest_file(path):
    """Hash one bounded runner source file for assignment source binding."""
    return hashlib.sha256(read_bounded_file(path, MAX_ASSIGNMENT_BYTES)).hexdigest()


def suite_iterator(suite):
    """Open one external suite iterator as a stable discovery boundary."""
    try:
        return iter(suite)
    except Exception as error:
        raise SchedulerError(
            f"test suite iteration failed: {type(error).__name__}"
        ) from error


def discovered_test_id(test):
    """Read one external test identity as a stable discovery boundary."""
    try:
        return test.id()
    except Exception as error:
        raise SchedulerError(
            f"test id lookup failed: {type(error).__name__}"
        ) from error


def parse_fixture_skip_holder(holder):
    """Return one recognised fixture kind and scope from a standard holder."""
    if not isinstance(holder, str) or "\x00" in holder:
        raise SchedulerError("unrecognised fixture skip holder")
    for kind, prefix in (
        ("class", "setUpClass ("),
        ("module", "setUpModule ("),
    ):
        if holder.startswith(prefix) and holder.endswith(")"):
            scope = holder[len(prefix):-1]
            if (
                scope
                and len(scope.encode("utf-8")) <= MAX_IDENTIFIER_BYTES
            ):
                return kind, scope
    raise SchedulerError("unrecognised fixture skip holder")


def discovered_fixture_scopes(test):
    """Bind one discovered object to unittest's class and module fixtures."""
    test_class = test.__class__
    module = getattr(test_class, "__module__", None)
    qualified = getattr(test_class, "__qualname__", None)
    if not isinstance(module, str) or not module or "\x00" in module:
        raise SchedulerError("test object has an invalid module fixture scope")
    if not isinstance(qualified, str) or not qualified or "\x00" in qualified:
        raise SchedulerError("test object has an invalid class fixture scope")
    class_scope = f"{module}.{qualified}"
    if (
        len(module.encode("utf-8")) > MAX_IDENTIFIER_BYTES
        or len(class_scope.encode("utf-8")) > MAX_IDENTIFIER_BYTES
    ):
        raise SchedulerError("test fixture scope exceeds its byte limit")
    return {"class": class_scope, "module": module}


def prove_fixture_blocked(
    selected_tests, assigned_ids, started_ids, fixture_skip_holders
):
    """Prove every non-started ID is covered by one actual fixture skip."""
    selected_tests = list(selected_tests)
    if len(selected_tests) != len(assigned_ids):
        raise SchedulerError("fixture accounting object count mismatch")
    if [discovered_test_id(test) for test in selected_tests] != assigned_ids:
        raise SchedulerError("fixture accounting object identity mismatch")
    if (
        not isinstance(fixture_skip_holders, list)
        or any(not isinstance(holder, str) for holder in fixture_skip_holders)
    ):
        raise SchedulerError("invalid fixture skip holders")
    # Reuse the public manifest encoder as the aggregate UTF-8/list bound.
    manifest_bytes(fixture_skip_holders)
    if len(set(fixture_skip_holders)) != len(fixture_skip_holders):
        raise SchedulerError("duplicate fixture skip holder")

    started = set(started_ids)
    blocked_by = {}
    scopes = [discovered_fixture_scopes(test) for test in selected_tests]
    for holder in fixture_skip_holders:
        kind, scope = parse_fixture_skip_holder(holder)
        matching = [
            identifier
            for identifier, fixture_scopes in zip(assigned_ids, scopes)
            if fixture_scopes[kind] == scope
        ]
        if not matching:
            raise SchedulerError("fixture skip holder has no assigned scope")
        for identifier in matching:
            if identifier in started:
                raise SchedulerError("fixture-blocked ID overlaps executed ID")
            if identifier in blocked_by:
                raise SchedulerError("overlapping fixture skip scopes")
            blocked_by[identifier] = holder

    blocked = [
        identifier for identifier in assigned_ids if identifier in blocked_by
    ]
    missing = [
        identifier for identifier in assigned_ids if identifier not in started
    ]
    if blocked != missing:
        raise SchedulerError("unproved missing assignment")
    return blocked


SUITE_EXECUTION_METHODS = (
    "__getattribute__",
    "__call__",
    "run",
    "_handleClassSetUp",
    "_handleModuleFixture",
    "_tearDownPreviousClass",
    "_handleModuleTearDown",
    "_addClassOrModuleLevelException",
    "_createClassOrModuleLevelException",
    "_get_previous_module",
    "_removeTestAtIndex",
)


_MISSING_CLASS_ATTRIBUTE = object()


def raw_class_attribute(test_class, name):
    """Resolve one class attribute without trusting its metaclass lookup."""
    try:
        class_mro = type.__getattribute__(test_class, "__mro__")
    except (AttributeError, TypeError):
        return _MISSING_CLASS_ATTRIBUTE
    for base in class_mro:
        try:
            namespace = type.__getattribute__(base, "__dict__")
        except (AttributeError, TypeError):
            return _MISSING_CLASS_ATTRIBUTE
        if name in namespace:
            return namespace[name]
    return _MISSING_CLASS_ATTRIBUTE


def refuse_custom_suite_execution(suite):
    """Refuse suite wrappers whose execution semantics flattening would lose."""
    try:
        instance_values = object.__getattribute__(suite, "__dict__")
    except (AttributeError, TypeError):
        instance_values = {}
    suite_type = type(suite)
    for name in SUITE_EXECUTION_METHODS:
        if name in instance_values or raw_class_attribute(
            suite_type, name
        ) is not raw_class_attribute(unittest.TestSuite, name):
            raise SchedulerError(
                f"custom test suite execution override: {name}"
            )


def flatten_suite(suite):
    """Yield discovered test objects in unittest's canonical nested order."""
    if not isinstance(suite, unittest.TestSuite):
        yield suite
        return

    refuse_custom_suite_execution(suite)
    root_id = id(suite)
    active = {root_id}
    stack = [(suite_iterator(suite), root_id)]
    visited = 0
    while stack:
        iterator, suite_id = stack[-1]
        try:
            item = next(iterator)
        except StopIteration:
            stack.pop()
            active.remove(suite_id)
            continue
        except Exception as error:
            raise SchedulerError(
                f"test suite iteration failed: {type(error).__name__}"
            ) from error
        visited += 1
        if visited > MAX_TESTS:
            raise SchedulerError("test manifest exceeds its item limit")
        if item is None:
            continue
        if not isinstance(item, unittest.TestSuite):
            yield item
            continue
        item_id = id(item)
        if item_id in active:
            raise SchedulerError("cyclic test suite")
        refuse_custom_suite_execution(item)
        active.add(item_id)
        stack.append((suite_iterator(item), item_id))


def manifest_bytes(identifiers):
    """Encode one ordered manifest beneath its explicit public byte cap."""
    prefix = b'{"ids":['
    suffix = (
        b'],"schema":'
        + json.dumps(
            MANIFEST_SCHEMA,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"}"
    )
    parts = [prefix]
    total = len(prefix) + len(suffix)
    for index, identifier in enumerate(identifiers):
        if not isinstance(identifier, str):
            raise SchedulerError("test id must be a string")
        encoded = json.dumps(
            identifier,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        added = len(encoded) + (1 if index else 0)
        if total + added > MAX_MANIFEST_BYTES:
            raise SchedulerError(
                f"test manifest exceeds {MAX_MANIFEST_BYTES}-byte limit"
            )
        if index:
            parts.append(b",")
        parts.append(encoded)
        total += added
    parts.append(suffix)
    return b"".join(parts)


def manifest_digest(identifiers):
    """Hash the bounded versioned ordered list, not a historical count."""
    return hashlib.sha256(manifest_bytes(identifiers)).hexdigest()


def discover_manifest(suite_root=None, loader=None):
    """Discover and flatten one fresh ordered unique unittest manifest."""
    root = Path(suite_root or Path(__file__).resolve().parent).resolve(strict=True)
    chosen_loader = loader or unittest.defaultTestLoader
    suite = chosen_loader.discover(str(root), pattern="test_*.py")
    tests = []
    identifiers = []
    seen = set()
    for test in flatten_suite(suite):
        if len(tests) >= MAX_TESTS:
            raise SchedulerError("test manifest exceeds its item limit")
        identifier = discovered_test_id(test)
        if not isinstance(identifier, str) or not identifier:
            raise SchedulerError("test id must be a non-empty string")
        if len(identifier.encode("utf-8")) > MAX_IDENTIFIER_BYTES:
            raise SchedulerError("test id exceeds its byte limit")
        if identifier in seen:
            raise SchedulerError(f"duplicate test id: {identifier}")
        seen.add(identifier)
        tests.append(test)
        identifiers.append(identifier)
    if not tests:
        raise SchedulerError("empty test manifest")
    return tests, identifiers, manifest_digest(identifiers)


def module_uses_standard_fixture(module_name):
    """Return whether unittest would resolve a module fixture for this name."""
    module = sys.modules.get(module_name)
    if module is None:
        return True
    if type(module) is not types.ModuleType:
        return True
    try:
        namespace = types.ModuleType.__getattribute__(module, "__dict__")
    except (AttributeError, TypeError):
        return True
    if "__getattr__" in namespace:
        return True
    for name in ("setUpModule", "tearDownModule"):
        try:
            fixture = getattr(module, name, None)
        except Exception:
            return True
        if fixture is not None:
            return True
    return False


def class_uses_standard_fixture(test_class):
    """Return whether a class has non-default fixture work or cleanups."""
    if type(test_class) is not type:
        return True
    for name in ("setUpClass", "tearDownClass"):
        fixture = raw_class_attribute(test_class, name)
        default = raw_class_attribute(unittest.TestCase, name)
        if (
            fixture is _MISSING_CLASS_ATTRIBUTE
            or default is _MISSING_CLASS_ATTRIBUTE
        ):
            return True
        if fixture is not default:
            return True
    cleanups = raw_class_attribute(test_class, "_class_cleanups")
    if cleanups is _MISSING_CLASS_ATTRIBUTE or type(cleanups) is not list:
        return True
    return bool(cleanups)


def code_references_cleanup(code, cleanup_name):
    """Return whether one local code graph names a standard cleanup API."""
    if type(code) is not types.CodeType:
        return True
    cleanup_names = {
        "addModuleCleanup": {"addModuleCleanup", "enterModuleContext"},
        "addClassCleanup": {"addClassCleanup", "enterClassContext"},
    }.get(cleanup_name, {cleanup_name})
    if cleanup_names.intersection(code.co_names):
        return True
    for value in code.co_consts:
        if value in cleanup_names:
            return True
        if type(value) is types.CodeType and code_references_cleanup(
            value, cleanup_name
        ):
            return True
    return False


def value_code_names(value):
    """Return inert names from the built-in callable containers we inspect."""
    functions = []
    if type(value) is types.FunctionType:
        functions.append(value)
    elif type(value) is types.MethodType:
        functions.append(value.__func__)
    elif type(value) in (classmethod, staticmethod):
        functions.append(value.__func__)
    elif type(value) is property:
        functions.extend(
            item
            for item in (value.fget, value.fset, value.fdel)
            if item is not None
        )
    names = set()
    stack = [
        function.__code__
        for function in functions
        if type(function) is types.FunctionType
    ]
    while stack:
        code = stack.pop()
        if type(code) is not types.CodeType:
            continue
        names.update(code.co_names)
        stack.extend(
            item for item in code.co_consts if type(item) is types.CodeType
        )
    return names


def is_standard_cleanup_alias(value, cleanup_name):
    """Recognise inert aliases of unittest's standard cleanup callables."""
    if cleanup_name == "addModuleCleanup":
        return any(
            candidate is not None and value is candidate
            for candidate in (
                unittest.addModuleCleanup,
                getattr(unittest, "enterModuleContext", None),
            )
        )
    if cleanup_name != "addClassCleanup":
        return False
    if type(value) in (classmethod, staticmethod, types.MethodType):
        value = value.__func__
    for name in (cleanup_name, "enterClassContext"):
        target = raw_class_attribute(unittest.TestCase, name)
        if type(target) is classmethod and value is target.__func__:
            return True
    return False


def value_references_cleanup(
    value, cleanup_name, *, follow_helpers=False, seen=None
):
    """Inspect only inert built-in callable containers without invoking them."""
    if is_standard_cleanup_alias(value, cleanup_name):
        return True
    seen = set() if seen is None else seen
    if type(value) in (tuple, list, set, frozenset, dict):
        identifier = id(value)
        if identifier in seen:
            return False
        seen.add(identifier)
        components = (
            [*value.keys(), *value.values()]
            if type(value) is dict
            else list(value)
        )
        return any(
            value_references_cleanup(
                component,
                cleanup_name,
                follow_helpers=True,
                seen=seen,
            )
            for component in components
        )
    if type(value) in (functools.partial, functools.partialmethod):
        identifier = id(value)
        if identifier in seen:
            return False
        seen.add(identifier)
        components = [value.func, *value.args]
        if value.keywords:
            components.extend(value.keywords.values())
        return any(
            value_references_cleanup(
                component,
                cleanup_name,
                follow_helpers=True,
                seen=seen,
            )
            for component in components
        )
    functions = []
    bound_values = []
    if type(value) is types.FunctionType:
        functions.append(value)
    elif type(value) is types.MethodType:
        functions.append(value.__func__)
        bound_values.append(value.__self__)
    elif type(value) in (classmethod, staticmethod):
        functions.append(value.__func__)
    elif type(value) is property:
        functions.extend(
            item
            for item in (value.fget, value.fset, value.fdel)
            if item is not None
        )
    for function in functions:
        if type(function) is not types.FunctionType:
            continue
        identifier = id(function)
        if identifier in seen:
            continue
        seen.add(identifier)
        if code_references_cleanup(function.__code__, cleanup_name):
            return True
        if not follow_helpers:
            continue
        components = list(function.__defaults__ or ())
        if function.__kwdefaults__:
            components.extend(function.__kwdefaults__.values())
        for cell in function.__closure__ or ():
            try:
                components.append(cell.cell_contents)
            except ValueError:
                continue
        if any(
            value_references_cleanup(
                component,
                cleanup_name,
                follow_helpers=True,
                seen=seen,
            )
            for component in components
        ):
            return True
        namespace = function.__globals__
        if type(namespace) is not dict:
            return True
        for name in value_code_names(function):
            helper = namespace.get(name)
            if value_references_cleanup(
                helper,
                cleanup_name,
                follow_helpers=True,
                seen=seen,
            ):
                return True
    for bound in bound_values:
        names = value_code_names(value)
        try:
            state = object.__getattribute__(bound, "__dict__")
        except (AttributeError, TypeError):
            state = None
        if type(state) is dict and any(
            name in state
            and value_references_cleanup(
                state[name],
                cleanup_name,
                follow_helpers=True,
                seen=seen,
            )
            for name in names
        ):
            return True
    if (
        not functions
        and follow_helpers
        and not isinstance(value, type)
        and callable(value)
    ):
        # Inspect a Python callable instance through its raw class binding.
        # An opaque dispatch supplies no inert evidence of a cleanup reference;
        # active fixture registries and inspectable Python callables remain the
        # conservative scheduling boundary.
        identifier = id(value)
        if identifier in seen:
            return False
        seen.add(identifier)
        dispatch = raw_class_attribute(type(value), "__call__")
        if type(dispatch) is types.FunctionType:
            if value_references_cleanup(
                dispatch,
                cleanup_name,
                follow_helpers=True,
                seen=seen,
            ):
                return True
            names = value_code_names(dispatch)
            try:
                state = object.__getattribute__(value, "__dict__")
            except (AttributeError, TypeError):
                state = None
            if type(state) is dict and any(
                name in state
                and value_references_cleanup(
                    state[name],
                    cleanup_name,
                    follow_helpers=True,
                    seen=seen,
                )
                for name in names
            ):
                return True
    return False


def value_testcase_classes(value, *, follow_helpers=False, seen=None):
    """Return inert TestCase class identities referenced by one callable."""
    seen = set() if seen is None else seen
    found = {}

    def collect(component, *, helper=False, module_names=()):
        identifier = id(component)
        if identifier in seen:
            return
        seen.add(identifier)

        if isinstance(component, type):
            try:
                is_testcase = issubclass(component, unittest.TestCase)
            except TypeError:
                is_testcase = False
            if is_testcase:
                found[identifier] = component
            return
        if isinstance(component, unittest.TestCase):
            found[id(type(component))] = type(component)
            return
        if type(component) in (tuple, list, set, frozenset, dict):
            values = (
                [*component.keys(), *component.values()]
                if type(component) is dict
                else list(component)
            )
            for item in values:
                collect(item, helper=True)
            return
        if type(component) in (functools.partial, functools.partialmethod):
            values = [component.func, *component.args]
            if component.keywords:
                values.extend(component.keywords.values())
            for item in values:
                collect(item, helper=True)
            return
        if type(component) is types.ModuleType:
            try:
                namespace = types.ModuleType.__getattribute__(
                    component, "__dict__"
                )
            except (AttributeError, TypeError):
                return
            for name in module_names:
                if name in namespace:
                    collect(namespace[name], helper=True)
            return

        functions = []
        bound_values = []
        if type(component) is types.FunctionType:
            functions.append(component)
        elif type(component) is types.MethodType:
            functions.append(component.__func__)
            bound_values.append(component.__self__)
        elif type(component) in (classmethod, staticmethod):
            functions.append(component.__func__)
        elif type(component) is property:
            functions.extend(
                item
                for item in (component.fget, component.fset, component.fdel)
                if item is not None
            )
        for bound in bound_values:
            collect(bound, helper=True)
        for function in functions:
            if type(function) is not types.FunctionType or not helper:
                continue
            values = list(function.__defaults__ or ())
            if function.__kwdefaults__:
                values.extend(function.__kwdefaults__.values())
            for cell in function.__closure__ or ():
                try:
                    values.append(cell.cell_contents)
                except ValueError:
                    continue
            for item in values:
                collect(item, helper=True)
            namespace = function.__globals__
            if type(namespace) is not dict:
                continue
            names = value_code_names(function)
            for name in names:
                if name in namespace:
                    collect(
                        namespace[name],
                        helper=True,
                        module_names=names,
                    )
        if not functions and helper and callable(component):
            dispatch = raw_class_attribute(type(component), "__call__")
            if type(dispatch) is types.FunctionType:
                collect(dispatch, helper=True)
                names = value_code_names(dispatch)
                try:
                    state = object.__getattribute__(component, "__dict__")
                except (AttributeError, TypeError):
                    state = None
                if type(state) is dict:
                    for name in names:
                        if name in state:
                            collect(state[name], helper=True)

    collect(value, helper=follow_helpers)
    return found


def class_mro_member_values(test_class):
    """Return inert members from every user class that can supply a method."""
    try:
        method_resolution_order = type.__getattribute__(
            test_class, "__mro__"
        )
    except (AttributeError, TypeError):
        return None
    if (
        type(method_resolution_order) is not tuple
        or not method_resolution_order
        or method_resolution_order[0] is not test_class
    ):
        return None
    members = []
    for owner in method_resolution_order:
        if owner is unittest.TestCase or owner is object:
            continue
        try:
            namespace = type.__getattribute__(owner, "__dict__")
        except (AttributeError, TypeError):
            return None
        members.extend(namespace.values())
    return members


def function_cleanup_is_source_local(function):
    """Prove direct class-cleanup lookups use the bound test-class argument."""
    if type(function) is not types.FunctionType:
        return False
    code = function.__code__
    if not code.co_varnames:
        return False
    cleanup_names = {"addClassCleanup", "enterClassContext"}
    if any(
        value in cleanup_names
        or (
            type(value) is types.CodeType
            and code_references_cleanup(value, "addClassCleanup")
        )
        for value in code.co_consts
    ):
        return False
    try:
        instructions = list(dis.get_instructions(code))
    except (TypeError, ValueError):
        return False
    accesses = 0
    for index, instruction in enumerate(instructions):
        if (
            instruction.opname not in ("LOAD_ATTR", "LOAD_METHOD")
            or instruction.argval not in cleanup_names
        ):
            continue
        accesses += 1
        if index == 0:
            return False
        receiver = instructions[index - 1]
        if (
            not receiver.opname.startswith("LOAD_FAST")
            or receiver.argval != code.co_varnames[0]
        ):
            return False
    if not accesses:
        return False

    bound_values = list(function.__defaults__ or ())
    if function.__kwdefaults__:
        bound_values.extend(function.__kwdefaults__.values())
    for cell in function.__closure__ or ():
        try:
            bound_values.append(cell.cell_contents)
        except ValueError:
            continue
    if any(
        value_references_cleanup(
            value,
            "addClassCleanup",
            follow_helpers=True,
        )
        for value in bound_values
    ):
        return False
    namespace = function.__globals__
    if type(namespace) is not dict:
        return False
    for name in value_code_names(function) - cleanup_names:
        if name in namespace and value_references_cleanup(
            namespace[name],
            "addClassCleanup",
            follow_helpers=True,
        ):
            return False
    return True


def member_cleanup_is_source_local(member):
    """Return whether all class-cleanup work is bound directly to this class."""
    functions = []
    wrapper_values = []
    if type(member) is types.FunctionType:
        functions.append(member)
    elif type(member) is classmethod:
        functions.append(member.__func__)
    elif type(member) is property:
        functions.extend(
            value
            for value in (member.fget, member.fset, member.fdel)
            if value is not None
        )
    elif type(member) is functools.partialmethod:
        functions.append(member.func)
        wrapper_values.extend(member.args)
        if member.keywords:
            wrapper_values.extend(member.keywords.values())
    else:
        return False
    if any(
        value_references_cleanup(
            value,
            "addClassCleanup",
            follow_helpers=True,
        )
        for value in wrapper_values
    ):
        return False
    referenced = [
        function
        for function in functions
        if code_references_cleanup(function.__code__, "addClassCleanup")
    ]
    return bool(referenced) and all(
        function_cleanup_is_source_local(function)
        for function in referenced
    )


def class_cleanup_dependencies(test_class):
    """Return cleanup use, named targets and unresolved cross-class ownership."""
    members = class_mro_member_values(test_class)
    if members is None:
        return True, {}, True
    references_cleanup = False
    targets = {}
    unresolved_target = False
    for member in members:
        if not value_references_cleanup(
            member,
            "addClassCleanup",
            follow_helpers=True,
        ):
            continue
        references_cleanup = True
        member_targets = value_testcase_classes(
            member, follow_helpers=True
        )
        targets.update(member_targets)
        if (
            not member_targets
            and not member_cleanup_is_source_local(member)
        ):
            unresolved_target = True
    return references_cleanup, targets, unresolved_target


def module_references_cleanup(module_name, cleanup_name):
    """Conservatively find local code that can register a runtime cleanup."""
    module = sys.modules.get(module_name)
    if module is None or type(module) is not types.ModuleType:
        return True
    try:
        namespace = types.ModuleType.__getattribute__(module, "__dict__")
    except (AttributeError, TypeError):
        return True
    referenced_names = set()
    for value in namespace.values():
        if type(value) is types.FunctionType and value.__module__ == module_name:
            referenced_names.update(value_code_names(value))
            continue
        if type(value) is not type or value.__module__ != module_name:
            continue
        class_members = class_mro_member_values(value)
        if class_members is None:
            return True
        for member in class_members:
            referenced_names.update(value_code_names(member))

    for binding, value in namespace.items():
        if is_standard_cleanup_alias(value, cleanup_name):
            return True
        if type(value) in (functools.partial, functools.partialmethod):
            if binding in referenced_names and value_references_cleanup(
                value,
                cleanup_name,
                follow_helpers=True,
            ):
                return True
            continue
        if type(value) is types.FunctionType:
            if value_references_cleanup(
                value,
                cleanup_name,
                follow_helpers=(
                    value.__module__ == module_name
                    or binding in referenced_names
                ),
            ):
                return True
            continue
        if isinstance(value, types.ModuleType):
            if type(value) is not types.ModuleType:
                if binding in referenced_names:
                    return True
                continue
            try:
                imported_namespace = types.ModuleType.__getattribute__(
                    value, "__dict__"
                )
            except (AttributeError, TypeError):
                return True
            if any(
                name in imported_namespace
                and value_references_cleanup(
                    imported_namespace[name],
                    cleanup_name,
                    follow_helpers=True,
                )
                for name in referenced_names
            ):
                return True
            continue
        if type(value) is not type or value.__module__ != module_name:
            if binding in referenced_names and value_references_cleanup(
                value,
                cleanup_name,
                follow_helpers=True,
            ):
                return True
            continue
        class_members = class_mro_member_values(value)
        if class_members is None:
            return True
        if any(
            value_references_cleanup(
                member,
                cleanup_name,
                follow_helpers=True,
            )
            for member in class_members
        ):
            return True
    return False


def suite_has_pending_module_cleanups():
    """Return whether discovery registered suite-global module cleanup work."""
    try:
        cleanups = getattr(unittest.case, "_module_cleanups", ())
    except Exception:
        return True
    return bool(cleanups)


def fixture_domains(tests):
    """Return minimal domains for only the active standard fixture scopes."""
    if not tests:
        raise SchedulerError("empty test manifest")
    if suite_has_pending_module_cleanups():
        domains = [list(range(len(tests)))]
        validate_assignments(domains, len(tests))
        return domains
    module_fixtures = {}
    class_fixtures = {}
    class_cleanups = {}
    test_classes = {}
    for test in tests:
        test_class = test.__class__
        test_classes[id(test_class)] = test_class
    dependent_classes = set()
    unresolved_class_cleanup = False
    for class_key, test_class in test_classes.items():
        references_cleanup, targets, unresolved = (
            class_cleanup_dependencies(test_class)
        )
        class_cleanups[class_key] = targets
        unresolved_class_cleanup = unresolved_class_cleanup or unresolved
        if references_cleanup:
            dependent_classes.add(class_key)
            dependent_classes.update(
                target_key
                for target_key in targets
                if target_key in test_classes
            )
    if unresolved_class_cleanup:
        domains = [list(range(len(tests)))]
        validate_assignments(domains, len(tests))
        return domains

    preliminary = []
    class_scopes = {}
    for index, test in enumerate(tests):
        fixture_scopes = discovered_fixture_scopes(test)
        module = fixture_scopes["module"]
        if module not in module_fixtures:
            module_fixtures[module] = (
                module_uses_standard_fixture(module)
                or module_references_cleanup(module, "addModuleCleanup")
            )
        if module_fixtures[module]:
            scope = ("module", module)
            preliminary.append(scope)
            class_scopes[id(test.__class__)] = scope
            continue
        test_class = test.__class__
        class_key = id(test_class)
        if class_key not in class_fixtures:
            class_fixtures[class_key] = (
                class_uses_standard_fixture(test_class)
                or class_key in dependent_classes
            )
        if class_fixtures[class_key]:
            scope = ("class", class_key)
            preliminary.append(scope)
            class_scopes[class_key] = scope
        else:
            preliminary.append(("test", index))

    parents = {scope: scope for scope in preliminary}

    def find(scope):
        while parents[scope] != scope:
            parents[scope] = parents[parents[scope]]
            scope = parents[scope]
        return scope

    def union(left, right):
        left = find(left)
        right = find(right)
        if left != right:
            parents[right] = left

    for source_key, targets in class_cleanups.items():
        source_scope = class_scopes.get(source_key)
        if source_scope is None:
            continue
        for target_key in targets:
            target_scope = class_scopes.get(target_key)
            if target_scope is not None:
                union(source_scope, target_scope)

    scopes = [find(scope) for scope in preliminary]
    final_index = {
        scope: index for index, scope in enumerate(scopes)
    }
    domains = []
    start = 0
    while start < len(scopes):
        end = final_index[scopes[start]]
        cursor = start
        while cursor <= end:
            end = max(end, final_index[scopes[cursor]])
            cursor += 1
        domains.append(list(range(start, end + 1)))
        start = end + 1
    validate_assignments(domains, len(tests))
    return domains


def prove_worker_fixture_domains(indices, domains):
    """Refuse a worker assignment that splits any rediscovered fixture scope."""
    assigned = set(indices)
    for domain in domains:
        domain_set = set(domain)
        if assigned & domain_set and not domain_set <= assigned:
            raise SchedulerError("worker fixture domain crosses assignment")
    return True


def positive_capacity(value):
    """Return a usable integer capacity signal or no signal."""
    if isinstance(value, bool):
        return None
    try:
        integer = int(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return integer if integer > 0 else None


def read_small_text(path, maximum=256):
    """Read one tiny CPU-controller value without accepting a large file."""
    return read_bounded_file(path, maximum).decode("ascii").strip()


def quota_capacity(quota, period):
    """Turn a positive CPU quota and period into a conservative whole CPU."""
    try:
        quota_value = int(quota)
        period_value = int(period)
    except (TypeError, ValueError):
        return None
    if quota_value <= 0 or period_value <= 0:
        return None
    return max(1, quota_value // period_value)


def cgroup_v2_member():
    """Resolve the process's one bounded cgroup-v2 membership."""
    try:
        membership = read_small_text("/proc/self/cgroup", maximum=4_096)
    except (OSError, UnicodeError):
        return None
    matches = []
    for line in membership.splitlines():
        parts = line.split(":", 2)
        if len(parts) == 3 and parts[0] == "0" and parts[1] == "":
            matches.append(parts[2])
    if len(matches) != 1:
        return None
    return canonical_cgroup_member(matches[0])


def cgroup_v2_mounts():
    """Return bounded v2 controller roots and filesystem mount points."""
    try:
        mountinfo = read_small_text("/proc/self/mountinfo", maximum=131_072)
    except (OSError, UnicodeError):
        return []
    mounts = []
    for line in mountinfo.splitlines():
        fields = line.split()
        try:
            separator = fields.index("-")
        except ValueError:
            continue
        if separator < 6 or len(fields) <= separator + 1:
            continue
        if fields[separator + 1] != "cgroup2":
            continue
        controller_root = decode_mountinfo_path(fields[3])
        mount_point = decode_mountinfo_path(fields[4])
        if controller_root is None or mount_point is None:
            continue
        pair = (controller_root, mount_point)
        if pair not in mounts:
            mounts.append(pair)
    return mounts


def cgroup_v2_cpu_max_paths():
    """Return v2 CPU quota files from membership through each mount root."""
    member = cgroup_v2_member()
    fallback = (
        PurePosixPath("/"), PurePosixPath("/sys/fs/cgroup")
    )
    mounts = cgroup_v2_mounts() if member is not None else []
    if fallback not in mounts:
        mounts.append(fallback)
    if member is None:
        member = PurePosixPath("/")

    result = []
    for controller_root, mount_point in mounts:
        try:
            relative = member.relative_to(controller_root)
        except ValueError:
            continue
        base = mount_point.joinpath(*relative.parts)
        while True:
            path = str(base / "cpu.max")
            if path not in result:
                result.append(path)
            if base == mount_point:
                break
            if mount_point not in base.parents:
                break
            base = base.parent
    return result


def cgroup_v2_capacity():
    """Take the minimum positive quota along the process's v2 ancestry."""
    capacities = []
    for path in cgroup_v2_cpu_max_paths():
        try:
            values = read_small_text(path).split()
        except (OSError, UnicodeError):
            continue
        if len(values) != 2 or values[0] == "max":
            continue
        value = quota_capacity(values[0], values[1])
        if value is not None:
            capacities.append(value)
    return min(capacities) if capacities else None


def canonical_cgroup_member(raw):
    """Return one canonical absolute controller membership or no value."""
    try:
        member = PurePosixPath(raw)
    except (TypeError, ValueError):
        return None
    if (
        not isinstance(raw, str)
        or not raw.startswith("/")
        or str(member) != raw
        or any(part in ("", ".", "..") for part in member.parts[1:])
    ):
        return None
    return member


def cgroup_v1_cpu_member():
    """Resolve the process's one bounded cgroup-v1 CPU membership."""
    try:
        membership = read_small_text("/proc/self/cgroup", maximum=4_096)
    except (OSError, UnicodeError):
        return None
    matches = []
    for line in membership.splitlines():
        parts = line.split(":", 2)
        if len(parts) != 3 or not parts[0]:
            continue
        controllers = parts[1].split(",") if parts[1] else []
        if "cpu" in controllers:
            matches.append(parts[2])
    if len(matches) != 1:
        return None
    return canonical_cgroup_member(matches[0])


def decode_mountinfo_path(raw):
    """Decode the four path escapes allowed by proc mountinfo."""
    value = raw
    for encoded, decoded in (
        (r"\040", " "),
        (r"\011", "\t"),
        (r"\012", "\n"),
        (r"\134", "\\"),
    ):
        value = value.replace(encoded, decoded)
    if "\\" in value or "\x00" in value:
        return None
    return canonical_cgroup_member(value)


def cgroup_v1_cpu_mounts():
    """Return bounded v1 CPU mount roots and their filesystem mount points."""
    try:
        mountinfo = read_small_text("/proc/self/mountinfo", maximum=131_072)
    except (OSError, UnicodeError):
        return []
    mounts = []
    for line in mountinfo.splitlines():
        fields = line.split()
        try:
            separator = fields.index("-")
        except ValueError:
            continue
        if separator < 6 or len(fields) <= separator + 3:
            continue
        if fields[separator + 1] != "cgroup":
            continue
        controllers = set(fields[separator + 3].split(","))
        if "cpu" not in controllers:
            continue
        controller_root = decode_mountinfo_path(fields[3])
        mount_point = decode_mountinfo_path(fields[4])
        if controller_root is None or mount_point is None:
            continue
        pair = (controller_root, mount_point)
        if pair not in mounts:
            mounts.append(pair)
    return mounts


def cgroup_v1_cpu_quota_paths():
    """Return v1 CPU quota pairs from membership through each mount root."""
    member = cgroup_v1_cpu_member()
    mounts = cgroup_v1_cpu_mounts() if member is not None else []
    if member is not None:
        mounts.extend((PurePosixPath("/"), PurePosixPath(root)) for root in (
            "/sys/fs/cgroup/cpu",
            "/sys/fs/cgroup/cpu,cpuacct",
            "/sys/fs/cgroup/cpuacct,cpu",
        ))
    else:
        mounts.append((PurePosixPath("/"), PurePosixPath("/sys/fs/cgroup/cpu")))
        member = PurePosixPath("/")

    result = []
    for controller_root, mount_point in mounts:
        try:
            relative = member.relative_to(controller_root)
        except ValueError:
            continue
        base = mount_point.joinpath(*relative.parts)
        while True:
            pair = (
                str(base / "cpu.cfs_quota_us"),
                str(base / "cpu.cfs_period_us"),
            )
            if pair not in result:
                result.append(pair)
            if base == mount_point:
                break
            if mount_point not in base.parents:
                break
            base = base.parent
    return result


def cgroup_v1_capacity():
    """Take the minimum positive quota along the process's v1 ancestry."""
    capacities = []
    for quota_path, period_path in cgroup_v1_cpu_quota_paths():
        try:
            quota = read_small_text(quota_path)
            period = read_small_text(period_path)
        except (OSError, UnicodeError):
            continue
        value = quota_capacity(quota, period)
        if value is not None:
            capacities.append(value)
    return min(capacities) if capacities else None


def capacity_signals():
    """Collect positive Python, affinity, cgroup, and fallback CPU signals."""
    signals = {}
    process_count = getattr(os, "process_cpu_count", None)
    if process_count is not None:
        try:
            value = positive_capacity(process_count())
        except OSError:
            value = None
        if value is not None:
            signals["process_cpu_count"] = value
    affinity = getattr(os, "sched_getaffinity", None)
    if affinity is not None:
        try:
            value = positive_capacity(len(affinity(0)))
        except OSError:
            value = None
        if value is not None:
            signals["affinity"] = value
    value = cgroup_v2_capacity()
    if value is not None:
        signals["cgroup_v2"] = value
    value = cgroup_v1_capacity()
    if value is not None:
        signals["cgroup_v1"] = value
    try:
        value = positive_capacity(os.cpu_count())
    except OSError:
        value = None
    if value is not None:
        signals["os_cpu_count"] = value
    return signals


def capacity_plan(requested, item_count, signals=None):
    """Choose conservative automatic capacity or one bounded explicit budget."""
    if requested is not None:
        if isinstance(requested, bool) or not isinstance(requested, int):
            raise ValueError("explicit jobs must be an integer")
        if requested < 1 or requested > MAX_JOBS:
            raise ValueError(f"explicit jobs must be between 1 and {MAX_JOBS}")
    observed = dict(capacity_signals() if signals is None else signals)
    observed = {
        key: value
        for key, raw in sorted(observed.items())
        if (value := positive_capacity(raw)) is not None
    }
    usable = min(observed.values()) if observed else 1
    if requested is None:
        reserve = max(1, (usable + 2) // 3) if usable > 1 else 0
        budget = min(MAX_JOBS, max(1, usable - reserve))
        source = "automatic"
    else:
        reserve = 0
        budget = requested
        source = "explicit"
    effective = min(budget, item_count) if item_count else 0
    return {
        "signals": observed,
        "usable": usable,
        "reserve": reserve,
        "safety_cap": MAX_JOBS,
        "budget": budget,
        "budget_source": source,
        "effective_jobs": effective,
    }


def cache_entries_digest(entries):
    """Hash exact cache entries so malformed history is visible as history."""
    body = json.dumps(
        entries,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def cache_path_for(root):
    """Return the fixed ignored timing path below the invocation root."""
    return Path(root).joinpath(*CACHE_PARTS)


def cache_root_for(path):
    """Recover the lexical invocation root from the one fixed cache path."""
    path = Path(path)
    if tuple(path.parts[-len(CACHE_PARTS) :]) != CACHE_PARTS:
        raise OSError("timing cache path is not the fixed invocation path")
    return path.parents[len(CACHE_PARTS) - 1]


def open_cache_parent(root, create):
    """Open the fixed cache parent without following or re-resolving names."""
    root = Path(root)
    root_stat = root.lstat()
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
        raise OSError("timing cache root is not a real directory")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current_fd = os.open(root, flags)
    try:
        opened_root = os.fstat(current_fd)
        if (opened_root.st_dev, opened_root.st_ino) != (
            root_stat.st_dev,
            root_stat.st_ino,
        ):
            raise OSError("timing cache root changed during inspection")
        for part in CACHE_PARTS[:-1]:
            try:
                next_fd = os.open(part, flags, dir_fd=current_fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, 0o700, dir_fd=current_fd)
                except FileExistsError:
                    pass
                next_fd = os.open(part, flags, dir_fd=current_fd)
            os.close(current_fd)
            current_fd = next_fd
        return current_fd
    except BaseException:
        os.close(current_fd)
        raise


def load_timing_cache(path, identifiers):
    """Load bounded exact-ID timings; every refusal falls back to neutral."""
    info = {
        "schema": TIMING_SCHEMA,
        "status": "missing",
        "digest": None,
        "hits": 0,
        "neutral": len(identifiers),
        "ignored_removed": 0,
        "corrupt_entries": 0,
        "write_status": "not-attempted",
    }
    parent_fd = None
    try:
        parent_fd = open_cache_parent(cache_root_for(path), create=False)
        body = read_bounded_at(
            parent_fd, CACHE_PARTS[-1], MAX_CACHE_BYTES
        )
    except FileNotFoundError:
        return {}, info
    except OSError:
        info["status"] = "unsafe"
        return {}, info
    finally:
        if parent_fd is not None:
            os.close(parent_fd)
    try:
        payload = strict_json_loads(body.decode("utf-8"))
        if not isinstance(payload, dict) or payload.get("schema") != TIMING_SCHEMA:
            info["status"] = "incompatible"
            return {}, info
        entries = payload.get("entries")
        if not isinstance(entries, list) or len(entries) > MAX_TESTS:
            raise ValueError("invalid timing entries")
        if payload.get("entries_digest") != cache_entries_digest(entries):
            raise ValueError("timing digest mismatch")
        timings = {}
        corrupt = 0
        for entry in entries:
            if not isinstance(entry, dict):
                corrupt += 1
                continue
            identifier = entry.get("id")
            seconds = entry.get("seconds")
            if (
                not isinstance(identifier, str)
                or not identifier
                or len(identifier.encode("utf-8")) > MAX_IDENTIFIER_BYTES
                or not is_bounded_json_number(seconds)
                or seconds < 0
                or seconds > MAX_TEST_SECONDS
                or identifier in timings
            ):
                corrupt += 1
                continue
            timings[identifier] = float(seconds)
    except (UnicodeError, ValueError, TypeError, DuplicateKeyError, json.JSONDecodeError):
        info["status"] = "corrupt"
        info["corrupt_entries"] = 1
        return {}, info
    current = set(identifiers)
    selected = {
        identifier: timings[identifier]
        for identifier in identifiers
        if identifier in timings
    }
    info.update({
        "status": "partial" if corrupt else ("hit" if selected else "miss"),
        "digest": payload.get("entries_digest"),
        "hits": len(selected),
        "neutral": len(identifiers) - len(selected),
        "ignored_removed": len(set(timings) - current),
        "corrupt_entries": corrupt,
    })
    return selected, info


def write_timing_cache(root, manifest, durations):
    """Atomically replace bounded current-ID timing advice below a fixed path."""
    entries = []
    for identifier in manifest:
        seconds = durations.get(identifier)
        if (
            not is_bounded_json_number(seconds)
            or seconds < 0
            or seconds > MAX_TEST_SECONDS
        ):
            continue
        entries.append({"id": identifier, "seconds": round(float(seconds), 9)})
    payload = {
        "schema": TIMING_SCHEMA,
        "manifest_digest": manifest_digest(manifest),
        "entries": entries,
        "entries_digest": cache_entries_digest(entries),
    }
    body = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    if len(body) > MAX_CACHE_BYTES:
        raise OSError("timing cache output exceeds its size limit")
    temporary_name = f".{CACHE_PARTS[-1]}.{os.getpid()}.{time.time_ns()}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    parent_fd = open_cache_parent(root, create=True)
    descriptor = None
    temporary_exists = False
    try:
        descriptor = os.open(
            temporary_name, flags, 0o600, dir_fd=parent_fd
        )
        temporary_exists = True
        remaining = memoryview(body)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("timing cache write made no progress")
            remaining = remaining[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        os.replace(
            temporary_name,
            CACHE_PARTS[-1],
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        temporary_exists = False
        os.fsync(parent_fd)
    except OSError:
        if descriptor is not None:
            os.close(descriptor)
        if temporary_exists:
            try:
                os.unlink(temporary_name, dir_fd=parent_fd)
            except OSError:
                pass
        raise
    finally:
        os.close(parent_fd)


def timing_weights(identifiers, timings):
    """Give unknown exact IDs the median known duration or a neutral unit."""
    known = sorted(float(value) for value in timings.values())
    if known:
        midpoint = len(known) // 2
        neutral = (
            known[midpoint]
            if len(known) % 2
            else (known[midpoint - 1] + known[midpoint]) / 2
        )
    else:
        neutral = 1.0
    return [timings.get(identifier, neutral) for identifier in identifiers], neutral


def validate_assignments(assignments, item_count):
    """Prove non-empty shards are the exact disjoint union of ``0..N-1``."""
    flattened = []
    for shard in assignments:
        if not shard:
            raise SchedulerError("empty shard")
        for index in shard:
            if isinstance(index, bool) or not isinstance(index, int):
                raise SchedulerError("non-integer assignment")
            if index < 0 or index >= item_count:
                raise SchedulerError("out-of-range assignment")
            flattened.append(index)
    counts = Counter(flattened)
    duplicates = sorted(index for index, count in counts.items() if count > 1)
    if duplicates:
        raise SchedulerError(f"duplicate assignment: {duplicates}")
    missing = sorted(set(range(item_count)) - set(flattened))
    if missing:
        raise SchedulerError(f"missing assignment: {missing}")
    return True


def partition_indices(identifiers, timings, jobs, domains=None):
    """Balance indivisible domains by duration, then restore manifest order."""
    domains = (
        [[index] for index in range(len(identifiers))]
        if domains is None
        else [list(domain) for domain in domains]
    )
    validate_assignments(domains, len(identifiers))
    if jobs < 1 or jobs > len(domains):
        raise SchedulerError("effective jobs must fit fixture domains")
    weights, neutral = timing_weights(identifiers, timings)
    assignments = [[] for _ in range(jobs)]
    estimates = [0.0] * jobs
    domain_weights = [
        sum(weights[index] for index in domain) for domain in domains
    ]
    ordered = sorted(
        range(len(domains)),
        key=lambda item: (-domain_weights[item], domains[item][0]),
    )
    for domain_index in ordered:
        shard = min(range(jobs), key=lambda item: (estimates[item], item))
        assignments[shard].extend(domains[domain_index])
        estimates[shard] += domain_weights[domain_index]
    for shard in assignments:
        shard.sort()
    validate_assignments(assignments, len(identifiers))
    return assignments, estimates, neutral


class BoundedBytes:
    """Retain a bounded head and tail while counting complete emitted bytes."""

    def __init__(self, maximum=MAX_OUTPUT_BYTES):
        self.maximum = maximum
        self.head_limit = maximum // 2
        self.tail_limit = maximum - self.head_limit
        self.total = 0
        self.data = bytearray()
        self.head = b""
        self.tail = b""
        self.truncated = False
        self.errors = []

    def write(self, body):
        body = bytes(body)
        self.total += len(body)
        if not self.truncated:
            combined = bytes(self.data) + body
            if len(combined) <= self.maximum:
                self.data = bytearray(combined)
            else:
                self.truncated = True
                self.head = combined[: self.head_limit]
                self.tail = combined[-self.tail_limit :]
                self.data.clear()
        else:
            self.tail = (self.tail + body)[-self.tail_limit :]
        return len(body)

    def render(self):
        def decoded(body):
            value = body.decode("utf-8", errors="surrogateescape")
            return "".join(
                "?" if 0xDC80 <= ord(character) <= 0xDCFF else character
                for character in value
            )

        if not self.truncated:
            return decoded(bytes(self.data))
        marker = f"\n... output truncated; {self.total} bytes emitted ...\n".encode()
        return decoded(self.head + marker + self.tail)


class BoundedTextCapture(io.TextIOBase):
    """A text stream backed by bounded UTF-8 head/tail retention."""

    def __init__(self, maximum=MAX_OUTPUT_BYTES):
        super().__init__()
        self.capture = BoundedBytes(maximum)

    @property
    def encoding(self):
        return "utf-8"

    def writable(self):
        return True

    def write(self, value):
        if not isinstance(value, str):
            value = str(value)
        self.capture.write(value.encode("utf-8", errors="replace"))
        return len(value)

    def flush(self):
        return None

    def payload(self):
        return {
            "text": self.capture.render(),
            "bytes": self.capture.total,
            "truncated": self.capture.truncated,
        }


class RecordingResult(unittest.TextTestResult):
    """Record exact starts, completions, and durations around unittest work."""

    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.started_ids = []
        self.completed_ids = []
        self.durations = []
        self._started_at = {}

    def startTest(self, test):
        identifier = test.id()
        self.started_ids.append(identifier)
        self._started_at[id(test)] = time.perf_counter()
        super().startTest(test)

    def stopTest(self, test):
        identifier = test.id()
        started = self._started_at.pop(id(test), time.perf_counter())
        self.completed_ids.append(identifier)
        self.durations.append(
            [identifier, max(0.0, time.perf_counter() - started)]
        )
        super().stopTest(test)


class RecordingSuite(unittest.TestSuite):
    """Record fixture skips only at unittest's suite-owned fixture hook."""

    def __init__(self, tests=()):
        super().__init__(tests)
        self.fixture_skip_holders = []

    def _addClassOrModuleLevelException(
        self, result, exception, error_name, info=None
    ):
        if isinstance(exception, unittest.SkipTest):
            self.fixture_skip_holders.append(error_name)
        super()._addClassOrModuleLevelException(
            result, exception, error_name, info
        )


def run_selected_tests(
    tests,
    indices,
    shard,
    shard_count,
    digest,
    output_transport=RESULT_JSON_OUTPUT,
):
    """Run selected discovered objects and return one complete worker record."""
    if output_transport not in (RESULT_JSON_OUTPUT, COORDINATOR_PIPE_OUTPUT):
        raise SchedulerError("invalid worker output transport")
    capture_in_record = output_transport == RESULT_JSON_OUTPUT
    stdout = BoundedTextCapture() if capture_in_record else None
    stderr = BoundedTextCapture() if capture_in_record else None
    selected_tests = [tests[index] for index in indices]
    selected = RecordingSuite(selected_tests)
    started_at = time.perf_counter()
    with contextlib.ExitStack() as stack:
        if capture_in_record:
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
        result = unittest.TextTestRunner(
            stream=stderr if capture_in_record else sys.stderr,
            verbosity=1,
            resultclass=RecordingResult,
        ).run(selected)
    wall = max(0.0, time.perf_counter() - started_at)
    assigned_ids = [tests[index].id() for index in indices]
    fixture_blocked_ids = prove_fixture_blocked(
        selected_tests,
        assigned_ids,
        result.started_ids,
        selected.fixture_skip_holders,
    )
    if result.completed_ids != result.started_ids:
        raise SchedulerError("worker completion does not match starts")
    if [entry[0] for entry in result.durations] != result.started_ids:
        raise SchedulerError("worker durations do not match starts")
    failures = len(result.failures)
    errors = len(result.errors)
    unexpected_successes = len(result.unexpectedSuccesses)
    record = {
        "schema": WORKER_RESULT_SCHEMA,
        "status": (
            "test-failure"
            if failures + errors + unexpected_successes
            else "passed"
        ),
        "complete": True,
        "output_transport": output_transport,
        "shard": shard,
        "shard_count": shard_count,
        "manifest_digest": digest,
        "manifest_count": len(tests),
        "assigned_indices": list(indices),
        "assigned_ids": assigned_ids,
        "started_ids": result.started_ids,
        "completed_ids": result.completed_ids,
        "fixture_blocked_ids": fixture_blocked_ids,
        "fixture_skip_holders": selected.fixture_skip_holders,
        "exact_accounting": True,
        "testsRun": result.testsRun,
        "failures": failures,
        "errors": errors,
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": unexpected_successes,
        "durations": result.durations,
        "wall_time_seconds": wall,
    }
    if capture_in_record:
        record["output"] = {
            "stdout": stdout.payload(),
            "stderr": stderr.payload(),
        }
    return record


def assignment_payload(
    *, shard, shard_count, indices, identifiers, digest, suite_root, runner_path
):
    """Build one bounded v1 assignment using indices, never dotted selectors."""
    return {
        "schema": ASSIGNMENT_SCHEMA,
        "shard": shard,
        "shard_count": shard_count,
        "suite_root": str(Path(suite_root).resolve(strict=True)),
        "runner_sha256": digest_file(Path(runner_path).resolve(strict=True)),
        "manifest_digest": digest,
        "manifest_count": len(identifiers),
        "indices": list(indices),
    }


def validate_assignment(payload, runner_path):
    """Validate every private field before discovery or object selection."""
    if not isinstance(payload, dict) or payload.get("schema") != ASSIGNMENT_SCHEMA:
        raise SchedulerError("invalid assignment schema")
    for field in ("shard", "shard_count", "manifest_count"):
        value = payload.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            raise SchedulerError(f"invalid assignment {field}")
    if payload["shard_count"] < 1:
        raise SchedulerError("invalid assignment shard_count")
    if payload["shard"] < 0 or payload["shard"] >= payload["shard_count"]:
        raise SchedulerError("invalid assignment shard")
    if payload["manifest_count"] < 1 or payload["manifest_count"] > MAX_TESTS:
        raise SchedulerError("invalid assignment manifest_count")
    digest = payload.get("manifest_digest")
    runner_digest = payload.get("runner_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise SchedulerError("invalid assignment manifest digest")
    if not isinstance(runner_digest, str) or len(runner_digest) != 64:
        raise SchedulerError("invalid assignment runner digest")
    if runner_digest != digest_file(runner_path):
        raise SchedulerError("runner digest mismatch")
    suite_root = payload.get("suite_root")
    if not isinstance(suite_root, str) or "\x00" in suite_root:
        raise SchedulerError("invalid assignment suite root")
    expected_root = Path(runner_path).resolve(strict=True).parent
    try:
        supplied_root = Path(suite_root).resolve(strict=True)
    except (OSError, RuntimeError):
        raise SchedulerError("invalid assignment suite root")
    if supplied_root != expected_root:
        raise SchedulerError("assignment suite root does not own this runner")
    indices = payload.get("indices")
    if not isinstance(indices, list) or not indices:
        raise SchedulerError("empty shard")
    if len(indices) > payload["manifest_count"]:
        raise SchedulerError("assignment index count exceeds manifest")
    if any(
        isinstance(index, bool) or not isinstance(index, int)
        for index in indices
    ):
        raise SchedulerError("non-integer assignment")
    if any(
        index < 0 or index >= payload["manifest_count"] for index in indices
    ):
        raise SchedulerError("out-of-range assignment")
    if len(set(indices)) != len(indices):
        raise SchedulerError("duplicate assignment")
    if indices != sorted(indices):
        raise SchedulerError("assignment indices are not canonical")
    return supplied_root


def protocol_paths(assignment_raw, result_raw):
    """Bind private files to one real directory and fresh result basename."""
    for raw in (assignment_raw, result_raw):
        if not raw or "\x00" in raw:
            raise SchedulerError("invalid private worker path")
    assignment = Path(assignment_raw)
    result = Path(result_raw)
    if not assignment.is_absolute() or not result.is_absolute():
        raise SchedulerError("private worker paths must be absolute")
    directory_fd = None
    try:
        parent = assignment.parent.resolve(strict=True)
        result_parent = result.parent.resolve(strict=True)
        parent_stat = parent.lstat()
        directory_fd = os.open(
            parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
        opened_parent = os.fstat(directory_fd)
        assignment_stat = os.stat(
            assignment.name,
            dir_fd=directory_fd,
            follow_symlinks=False,
        )
    except OSError:
        if directory_fd is not None:
            os.close(directory_fd)
        raise SchedulerError("private worker paths cannot be inspected")
    if parent != result_parent or not stat.S_ISDIR(parent_stat.st_mode):
        os.close(directory_fd)
        raise SchedulerError("private worker paths must share one directory")
    if assignment.parent != parent or result.parent != parent:
        os.close(directory_fd)
        raise SchedulerError("private worker paths must not traverse symlinks")
    if (opened_parent.st_dev, opened_parent.st_ino) != (
        parent_stat.st_dev,
        parent_stat.st_ino,
    ):
        os.close(directory_fd)
        raise SchedulerError("private worker directory changed during inspection")
    if not stat.S_ISREG(assignment_stat.st_mode):
        os.close(directory_fd)
        raise SchedulerError("worker assignment must be a regular file")
    try:
        os.stat(result.name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        pass
    except OSError:
        os.close(directory_fd)
        raise SchedulerError("worker result cannot be inspected")
    else:
        os.close(directory_fd)
        raise SchedulerError("worker result must not already exist")
    return assignment, result, directory_fd


def write_json_exclusive_at(
    directory_fd, name, payload, maximum=MAX_WORKER_RESULT_BYTES
):
    """Create one protocol basename through an already bound directory."""
    if not name or name in (".", "..") or "/" in name:
        raise OSError("protocol output name is not a basename")
    body = (
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    if len(body) > maximum:
        raise OSError("protocol output exceeds its size limit")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
    try:
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise OSError("protocol target is not a regular file")
        remaining = memoryview(body)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("protocol write made no progress")
            remaining = remaining[written:]
    except OSError:
        os.close(descriptor)
        try:
            os.unlink(name, dir_fd=directory_fd)
        except OSError:
            pass
        raise
    else:
        os.close(descriptor)


def worker_failure(message, shard=-1):
    """Return a bounded incomplete worker record for coordinator diagnosis."""
    return {
        "schema": WORKER_RESULT_SCHEMA,
        "status": "scheduler-error",
        "complete": False,
        "shard": shard,
        "scheduler_error": str(message)[:4_096],
    }


def worker_main(arguments):
    """Rediscover, verify, select local objects, run, and write one result."""
    result_path = None
    protocol_fd = None
    shard = -1
    try:
        assignment_path, result_path, protocol_fd = protocol_paths(
            arguments._worker_assignment,
            arguments._worker_result,
        )
        assignment = strict_json_loads(
            read_bounded_at(
                protocol_fd, assignment_path.name, MAX_ASSIGNMENT_BYTES
            ).decode("utf-8")
        )
        if isinstance(assignment, dict):
            shard = assignment.get("shard", -1)
        runner_path = Path(__file__).resolve(strict=True)
        suite_root = validate_assignment(assignment, runner_path)
        tests, identifiers, digest = discover_manifest(suite_root)
        if len(identifiers) != assignment["manifest_count"]:
            raise SchedulerError(
                "manifest count mismatch: "
                f"expected {assignment['manifest_count']}, got {len(identifiers)}"
            )
        if digest != assignment["manifest_digest"]:
            raise SchedulerError(
                "manifest digest mismatch: "
                f"expected {assignment['manifest_digest']}, got {digest}"
            )
        prove_worker_fixture_domains(
            assignment["indices"], fixture_domains(tests)
        )
        record = run_selected_tests(
            tests,
            assignment["indices"],
            assignment["shard"],
            assignment["shard_count"],
            digest,
            output_transport=COORDINATOR_PIPE_OUTPUT,
        )
        write_json_exclusive_at(protocol_fd, result_path.name, record)
        return 1 if (
            record["failures"]
            + record["errors"]
            + record["unexpectedSuccesses"]
        ) else 0
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
        DuplicateKeyError,
        SchedulerError,
        json.JSONDecodeError,
    ) as error:
        record = worker_failure(error, shard)
        if result_path is not None and protocol_fd is not None:
            try:
                write_json_exclusive_at(
                    protocol_fd, result_path.name, record
                )
            except OSError:
                print("run_tests.py: worker result write failed", file=sys.stderr)
        else:
            print(f"run_tests.py: worker refused: {error}", file=sys.stderr)
        return 3
    finally:
        if protocol_fd is not None:
            os.close(protocol_fd)


def validate_worker_envelope(record, expected_shard, shard_count):
    """Bind one result value to its private path slot before any use."""
    if (
        not isinstance(record, dict)
        or record.get("schema") != WORKER_RESULT_SCHEMA
    ):
        raise SchedulerError("invalid worker result schema")
    complete = record.get("complete")
    if not isinstance(complete, bool):
        raise SchedulerError("invalid worker result complete")
    shard = record.get("shard")
    if isinstance(shard, bool) or not isinstance(shard, int):
        raise SchedulerError("invalid worker result shard")
    if shard < 0 or shard >= shard_count:
        raise SchedulerError("unknown worker result shard")
    if shard != expected_shard:
        raise SchedulerError("worker result shard does not match result slot")
    status = record.get("status")
    if complete:
        if status not in ("passed", "test-failure"):
            raise SchedulerError("invalid complete worker result status")
        return True
    scheduler_error = record.get("scheduler_error")
    if (
        status != "scheduler-error"
        or not isinstance(scheduler_error, str)
        or not scheduler_error
        or len(scheduler_error) > 4_096
    ):
        raise SchedulerError("invalid incomplete worker result")
    return False


def validate_worker_output(output):
    """Validate bounded captured output before it may be replayed."""
    if not isinstance(output, dict):
        raise SchedulerError("invalid worker result output")
    for stream_name in ("stdout", "stderr"):
        stream = output.get(stream_name)
        if not isinstance(stream, dict):
            raise SchedulerError(
                f"invalid worker result {stream_name} output"
            )
        text = stream.get("text")
        byte_count = stream.get("bytes")
        truncated = stream.get("truncated")
        if not isinstance(text, str):
            raise SchedulerError(
                f"invalid worker result {stream_name} text"
            )
        if (
            isinstance(byte_count, bool)
            or not isinstance(byte_count, int)
            or byte_count < 0
        ):
            raise SchedulerError(
                f"invalid worker result {stream_name} bytes"
            )
        if not isinstance(truncated, bool):
            raise SchedulerError(
                f"invalid worker result {stream_name} truncation"
            )
        try:
            retained = text.encode("utf-8")
        except UnicodeEncodeError:
            raise SchedulerError(
                f"invalid worker result {stream_name} text encoding"
            )
        if len(retained) > MAX_OUTPUT_BYTES + 128:
            raise SchedulerError(
                f"worker result {stream_name} output exceeds bound"
            )
        marker = (
            f"\n... output truncated; {byte_count} bytes emitted ...\n"
        ).encode("utf-8")
        if truncated:
            metadata_matches = (
                byte_count > MAX_OUTPUT_BYTES
                and len(marker) <= 128
                and len(retained) == MAX_OUTPUT_BYTES + len(marker)
                and retained[
                    MAX_OUTPUT_BYTES // 2 :
                    MAX_OUTPUT_BYTES // 2 + len(marker)
                ] == marker
            )
        else:
            metadata_matches = (
                len(retained) <= MAX_OUTPUT_BYTES
                and byte_count == len(retained)
            )
        if not metadata_matches:
            raise SchedulerError(
                f"worker result {stream_name} byte metadata mismatch"
            )


def validate_worker_record(
    record,
    identifiers,
    digest,
    assignments,
    expected_shard=None,
    expected_output_transport=RESULT_JSON_OUTPUT,
    tests=None,
):
    """Validate one complete slot-bound worker record before use."""
    if expected_shard is None:
        candidate = record.get("shard") if isinstance(record, dict) else -1
        expected_shard = candidate if isinstance(candidate, int) else -1
    if not validate_worker_envelope(
        record, expected_shard, len(assignments)
    ):
        raise SchedulerError(
            "incomplete worker result: " + record["scheduler_error"]
        )
    shard = record["shard"]
    shard_count = record.get("shard_count")
    if (
        isinstance(shard_count, bool)
        or not isinstance(shard_count, int)
        or shard_count != len(assignments)
    ):
        raise SchedulerError("worker shard count mismatch")
    indices = assignments[shard]
    expected_ids = [identifiers[index] for index in indices]
    if record.get("manifest_digest") != digest:
        raise SchedulerError("worker result manifest digest mismatch")
    manifest_count = record.get("manifest_count")
    if (
        isinstance(manifest_count, bool)
        or not isinstance(manifest_count, int)
        or manifest_count != len(identifiers)
    ):
        raise SchedulerError("worker result manifest count mismatch")
    assigned_indices = record.get("assigned_indices")
    if (
        not isinstance(assigned_indices, list)
        or any(
            isinstance(index, bool) or not isinstance(index, int)
            for index in assigned_indices
        )
        or assigned_indices != indices
    ):
        raise SchedulerError("worker result assignment mismatch")
    assigned_ids = record.get("assigned_ids")
    if (
        not isinstance(assigned_ids, list)
        or any(not isinstance(item, str) for item in assigned_ids)
        or assigned_ids != expected_ids
    ):
        raise SchedulerError("worker result assigned ids mismatch")
    for field in ("started_ids", "completed_ids", "fixture_blocked_ids"):
        values = record.get(field)
        if (
            not isinstance(values, list)
            or any(not isinstance(item, str) for item in values)
        ):
            raise SchedulerError(f"invalid worker result {field}")
    fixture_skip_holders = record.get("fixture_skip_holders")
    if (
        not isinstance(fixture_skip_holders, list)
        or any(not isinstance(item, str) for item in fixture_skip_holders)
    ):
        raise SchedulerError("invalid worker result fixture_skip_holders")
    manifest_bytes(fixture_skip_holders)
    if record.get("exact_accounting") is not True:
        raise SchedulerError("worker result lacks exact accounting")
    counter_fields = (
        "testsRun",
        "failures",
        "errors",
        "skipped",
        "expectedFailures",
        "unexpectedSuccesses",
    )
    for field in counter_fields:
        value = record.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < 0
            or value > sys.maxsize
        ):
            raise SchedulerError(f"invalid worker result {field}")
    if record["testsRun"] != len(record["started_ids"]):
        raise SchedulerError("worker testsRun does not match started ids")
    if record["testsRun"] != len(record["completed_ids"]):
        raise SchedulerError("worker testsRun does not match completed ids")
    if len(fixture_skip_holders) > record["skipped"]:
        raise SchedulerError("fixture skip holders exceed skip events")
    expected_status = (
        "test-failure"
        if (
            record["failures"]
            + record["errors"]
            + record["unexpectedSuccesses"]
        )
        else "passed"
    )
    if record["status"] != expected_status:
        raise SchedulerError("worker result status disagrees with counters")
    durations = record.get("durations")
    if not isinstance(durations, list):
        raise SchedulerError("invalid worker result durations")
    for entry in durations:
        if (
            not isinstance(entry, list)
            or len(entry) != 2
            or not isinstance(entry[0], str)
            or not is_bounded_json_number(entry[1])
            or entry[1] < 0
            or entry[1] > MAX_TEST_SECONDS
        ):
            raise SchedulerError("invalid worker result duration entry")
    blocked_ids = record["fixture_blocked_ids"]
    if blocked_ids or fixture_skip_holders:
        if tests is None or len(tests) != len(identifiers):
            raise SchedulerError(
                "fixture accounting requires discovered test objects"
            )
        selected_tests = [tests[index] for index in indices]
        proved_blocked = prove_fixture_blocked(
            selected_tests,
            expected_ids,
            record["started_ids"],
            fixture_skip_holders,
        )
        if blocked_ids != proved_blocked:
            raise SchedulerError("fixture-blocked IDs do not match skip proof")
    else:
        proved_blocked = []
    blocked = set(proved_blocked)
    expected_execution = [
        identifier for identifier in expected_ids if identifier not in blocked
    ]
    if (
        record["started_ids"] != expected_execution
        or record["completed_ids"] != expected_execution
    ):
        raise SchedulerError("worker execution assignment mismatch")
    if [entry[0] for entry in durations] != expected_execution:
        raise SchedulerError("worker duration assignment mismatch")
    wall_time = record.get("wall_time_seconds")
    if (
        not is_bounded_json_number(wall_time)
        or wall_time < 0
    ):
        raise SchedulerError("invalid worker result wall time")
    if expected_output_transport not in (
        RESULT_JSON_OUTPUT,
        COORDINATOR_PIPE_OUTPUT,
    ):
        raise SchedulerError("invalid expected worker output transport")
    if record.get("output_transport") != expected_output_transport:
        raise SchedulerError("worker result output transport mismatch")
    if expected_output_transport == RESULT_JSON_OUTPUT:
        validate_worker_output(record.get("output"))
    elif "output" in record:
        raise SchedulerError("coordinator-pipe result must not contain output")
    return shard


def reconcile_worker_results(
    identifiers,
    digest,
    assignments,
    records,
    expected_output_transport=RESULT_JSON_OUTPUT,
    tests=None,
):
    """Prove one exact executed or fixture-blocked disposition per ID."""
    validate_assignments(assignments, len(identifiers))
    if len(records) != len(assignments) or any(
        record is None for record in records
    ):
        raise SchedulerError(
            f"missing result: expected {len(assignments)}, got "
            f"{sum(record is not None for record in records)}"
        )
    by_shard = {}
    for expected_shard, record in enumerate(records):
        shard = validate_worker_record(
            record,
            identifiers,
            digest,
            assignments,
            expected_shard=expected_shard,
            expected_output_transport=expected_output_transport,
            tests=tests,
        )
        if shard in by_shard:
            raise SchedulerError(f"duplicate worker result: shard {shard}")
        by_shard[shard] = record
    if set(by_shard) != set(range(len(assignments))):
        raise SchedulerError("missing result: worker shard set is incomplete")
    started = [
        item
        for shard in sorted(by_shard)
        for item in by_shard[shard]["started_ids"]
    ]
    completed = [
        item
        for shard in sorted(by_shard)
        for item in by_shard[shard]["completed_ids"]
    ]
    fixture_blocked = [
        item
        for shard in sorted(by_shard)
        for item in by_shard[shard]["fixture_blocked_ids"]
    ]
    known = set(identifiers)
    unknown = sorted(
        (set(started) | set(completed) | set(fixture_blocked)) - known
    )
    if unknown:
        raise SchedulerError(f"unknown result: {unknown}")
    blocked_counts = Counter(fixture_blocked)
    duplicate_blocked = sorted(
        item for item, count in blocked_counts.items() if count > 1
    )
    if duplicate_blocked:
        raise SchedulerError(
            f"duplicate fixture-blocked disposition: {duplicate_blocked}"
        )
    blocked = set(fixture_blocked)
    for label, observed in (("started", started), ("completed", completed)):
        counts = Counter(observed)
        duplicates = sorted(
            item for item, count in counts.items() if count > 1
        )
        if duplicates:
            raise SchedulerError(
                f"duplicate execution in {label}: {duplicates}"
            )
        overlap = sorted(set(observed) & blocked)
        if overlap:
            raise SchedulerError(
                f"fixture-blocked IDs overlap {label}: {overlap}"
            )
        missing = sorted(known - set(observed) - blocked)
        if missing:
            raise SchedulerError(
                f"unexecuted assignment in {label}: {missing}"
            )
    counts = {
        field: sum(by_shard[shard][field] for shard in by_shard)
        for field in (
            "testsRun",
            "failures",
            "errors",
            "skipped",
            "expectedFailures",
            "unexpectedSuccesses",
        )
    }
    for field, value in counts.items():
        if value > sys.maxsize:
            raise SchedulerError(
                f"worker result {field} exceeds aggregate bound"
            )
    if counts["testsRun"] != len(started):
        raise SchedulerError("executed test count does not match starts")
    if set(started) | blocked != known:
        raise SchedulerError("terminal dispositions do not cover manifest")
    durations = {}
    for shard in sorted(by_shard):
        for identifier, seconds in by_shard[shard]["durations"]:
            if identifier not in known:
                raise SchedulerError(f"unknown result duration: {identifier}")
            if identifier in durations:
                raise SchedulerError(
                    f"duplicate execution duration: {identifier}"
                )
            durations[identifier] = float(seconds)
    if set(durations) != set(started):
        missing = sorted(set(started) - set(durations))
        raise SchedulerError(f"unexecuted assignment duration: {missing}")
    for shard in sorted(by_shard):
        expected_ids = [identifiers[index] for index in assignments[shard]]
        record = by_shard[shard]
        shard_blocked = set(record["fixture_blocked_ids"])
        expected_execution = [
            identifier
            for identifier in expected_ids
            if identifier not in shard_blocked
        ]
        if (
            record["started_ids"] != expected_execution
            or record["completed_ids"] != expected_execution
        ):
            raise SchedulerError("worker execution assignment mismatch")
        if [entry[0] for entry in record["durations"]] != expected_execution:
            raise SchedulerError("worker duration assignment mismatch")
    return {
        "counts": counts,
        "started": started,
        "completed": completed,
        "fixture_blocked": fixture_blocked,
        "exact_accounting": True,
        "durations": durations,
        "shards": summarize_validated_workers(assignments, records),
    }


def sequence_binding(domain, values):
    """Bind one ordered sequence into a fixed-size public evidence value."""
    items = list(values)
    body = json.dumps(
        {
            "schema": SHARD_SEQUENCE_SCHEMA,
            "domain": domain,
            "items": items,
        },
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return {
        "schema": SHARD_SEQUENCE_SCHEMA,
        "count": len(items),
        "sha256": hashlib.sha256(body).hexdigest(),
    }


def summarize_validated_workers(assignments, records):
    """Retain bounded evidence from each valid worker on partial runs."""
    shards = []
    for shard, record in enumerate(records):
        if record is None:
            continue
        durations = sequence_binding(
            "test-durations", record["durations"]
        )
        durations["total_seconds"] = sum(
            float(entry[1]) for entry in record["durations"]
        )
        shards.append({
            "shard": shard,
            "assigned_count": len(assignments[shard]),
            "assigned_indices": list(assignments[shard]),
            "assigned_ids": sequence_binding(
                "test-ids", record["assigned_ids"]
            ),
            "started_ids": sequence_binding(
                "test-ids", record["started_ids"]
            ),
            "completed_ids": sequence_binding(
                "test-ids", record["completed_ids"]
            ),
            "fixture_blocked_ids": sequence_binding(
                "test-ids", record["fixture_blocked_ids"]
            ),
            "fixture_skip_holders": sequence_binding(
                "fixture-skip-holders", record["fixture_skip_holders"]
            ),
            "exact_accounting": record["exact_accounting"],
            "durations": durations,
            "wall_time_seconds": record["wall_time_seconds"],
            "status": record["status"],
            "testsRun": record["testsRun"],
            "failures": record["failures"],
            "errors": record["errors"],
            "skipped": record["skipped"],
            "expectedFailures": record["expectedFailures"],
            "unexpectedSuccesses": record["unexpectedSuccesses"],
        })
    return shards


def drain_process_stream(stream, capture):
    """Drain one child pipe concurrently into bounded head/tail memory."""
    try:
        while True:
            chunk = stream.read(65_536)
            if not chunk:
                break
            capture.write(chunk)
    except OSError as error:
        capture.errors.append(f"read failed: {error}"[:4_096])
    finally:
        try:
            stream.close()
        except OSError as error:
            capture.errors.append(f"close failed: {error}"[:4_096])


def pipe_drain_errors(captures):
    """Return every bounded child-pipe error as scheduler evidence."""
    errors = []
    for shard, shard_captures in enumerate(captures):
        if shard_captures is None:
            continue
        for stream_name, capture in zip(
            ("stdout", "stderr"), shard_captures
        ):
            errors.extend(
                f"worker {shard} {stream_name} pipe {error}"
                for error in capture.errors
            )
    return errors


def join_drainers_until(drainers, deadline):
    """Give all pipe readers one shared bounded interval to reach EOF."""
    for shard_threads in drainers:
        for drainer in shard_threads:
            remaining = max(0.0, deadline - time.monotonic())
            drainer.join(remaining)


def retained_drainer_shards(drainers):
    """Name worker shards whose descendants still retain an output pipe."""
    return [
        shard
        for shard, shard_threads in enumerate(drainers)
        if any(drainer.is_alive() for drainer in shard_threads)
    ]


def signal_worker_groups(processes, shards, requested_signal, errors):
    """Request a signal for original worker groups retaining their pipes."""
    for shard in shards:
        process = processes[shard]
        pid = getattr(process, "pid", None)
        if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
            errors.append(
                f"worker {shard} retained output without a process group"
            )
            continue
        try:
            os.killpg(pid, requested_signal)
        except ProcessLookupError:
            errors.append(
                f"worker {shard} process group was unavailable while "
                "output remained open"
            )
        except OSError as error:
            errors.append(
                f"worker {shard} process-group signal failed: {error}"[:4_096]
            )


def observe_worker_exit_without_reaping(process, *, nohang=False):
    """Observe one worker exit while its leader PID still pins the group."""
    pid = getattr(process, "pid", None)
    if isinstance(pid, bool) or not isinstance(pid, int) or pid <= 0:
        raise OSError("worker has no valid process identity")
    options = os.WEXITED | os.WNOWAIT
    if nohang:
        options |= os.WNOHANG
    return os.waitid(os.P_PID, pid, options) is not None


def read_worker_result_at(directory_fd, name):
    """Read one strict worker result through the coordinator's bound root."""
    try:
        return strict_json_loads(
            read_bounded_at(
                directory_fd, name, MAX_WORKER_RESULT_BYTES
            ).decode("utf-8")
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ):
        return None


def replay_worker_outputs(assignments, records, residuals):
    """Replay every buffered shard strictly by canonical shard index."""
    for shard, indices in enumerate(assignments):
        print(
            f"===== hexaemeron shard {shard + 1}/{len(assignments)} "
            f"({len(indices)} tests) ====="
        )
        record = records[shard] if shard < len(records) else None
        if isinstance(record, dict):
            output = record.get("output")
            if isinstance(output, dict):
                for stream_name, destination in (
                    ("stdout", sys.stdout),
                    ("stderr", sys.stderr),
                ):
                    stream = output.get(stream_name)
                    if isinstance(stream, dict):
                        text = stream.get("text", "")
                        if isinstance(text, str) and text:
                            text = frame_test_output(text)
                            print(
                                text,
                                end="" if text.endswith("\n") else "\n",
                                file=destination,
                            )
        residual = residuals[shard] if shard < len(residuals) else {}
        for stream_name, destination in (
            ("stdout", sys.stdout),
            ("stderr", sys.stderr),
        ):
            stream = (
                residual.get(stream_name, {})
                if isinstance(residual, dict)
                else {}
            )
            text = stream.get("text", "") if isinstance(stream, dict) else ""
            if isinstance(text, str) and text:
                text = frame_test_output(text)
                print(
                    text,
                    end="" if text.endswith("\n") else "\n",
                    file=destination,
                )


def frame_test_output(text):
    """Keep test output outside the reserved structured-event namespace."""
    return "".join(
        TEST_OUTPUT_PREFIX + line
        if line.startswith(SUMMARY_PREFIX)
        else line
        for line in text.splitlines(keepends=True)
    )


def child_usage():
    """Return bounded child CPU and peak-RSS observations when available."""
    if resource is None:
        return None
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    return {
        "cpu_seconds": float(usage.ru_utime + usage.ru_stime),
        "peak_rss": int(usage.ru_maxrss),
    }


def usage_delta(before, after):
    """Return child CPU delta and the process-family RSS high-water."""
    if before is None or after is None:
        return {"child_cpu_seconds": None, "peak_child_rss": None}
    return {
        "child_cpu_seconds": max(
            0.0, after["cpu_seconds"] - before["cpu_seconds"]
        ),
        "peak_child_rss": after["peak_rss"],
    }


def directory_contains_identity(directory_fd, root_identity):
    """Return whether a descriptor's physical ancestor chain reaches root."""
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    current_fd = os.dup(directory_fd)
    try:
        while True:
            current = os.fstat(current_fd)
            current_identity = (current.st_dev, current.st_ino)
            if current_identity == root_identity:
                return True
            parent_fd = os.open("..", flags, dir_fd=current_fd)
            try:
                parent = os.fstat(parent_fd)
            except OSError:
                os.close(parent_fd)
                raise
            parent_identity = (parent.st_dev, parent.st_ino)
            if parent_identity == current_identity:
                os.close(parent_fd)
                return False
            os.close(current_fd)
            current_fd = parent_fd
    finally:
        os.close(current_fd)


def run_parallel(
    *,
    run_root,
    runner_path,
    suite_root,
    identifiers,
    digest,
    assignments,
    tests=None,
):
    """Launch fixed-argv private workers, then drain every started process."""
    records = [None] * len(assignments)
    replay_records = [None] * len(assignments)
    residuals = [{} for _ in assignments]
    returncodes = [None] * len(assignments)
    scheduler_errors = []
    processes = []
    captures = [None] * len(assignments)
    drainers = [[] for _ in assignments]
    max_live = 0
    with tempfile.TemporaryDirectory(
        prefix="hexaemeron-workers-"
    ) as temporary:
        protocol_root = Path(temporary).resolve(strict=True)
        invocation_root = Path(run_root).resolve(strict=True)
        os.chmod(protocol_root, 0o700)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        protocol_fd = None
        invocation_fd = None
        try:
            protocol_fd = os.open(protocol_root, flags)
            invocation_fd = os.open(invocation_root, flags)
            invocation = os.fstat(invocation_fd)
            invocation_identity = (invocation.st_dev, invocation.st_ino)
            if directory_contains_identity(protocol_fd, invocation_identity):
                raise SchedulerError(
                    "private worker directory is inside invocation checkout"
                )
        except OSError:
            if protocol_fd is not None:
                os.close(protocol_fd)
            raise SchedulerError(
                "private worker directories cannot be inspected"
            ) from None
        except SchedulerError:
            if protocol_fd is not None:
                os.close(protocol_fd)
            raise
        finally:
            if invocation_fd is not None:
                os.close(invocation_fd)
        assignment_paths = []
        result_paths = []
        for shard, indices in enumerate(assignments):
            assignment_path = protocol_root / f"assignment-{shard}.json"
            result_path = protocol_root / f"result-{shard}.json"
            payload = assignment_payload(
                shard=shard,
                shard_count=len(assignments),
                indices=indices,
                identifiers=identifiers,
                digest=digest,
                suite_root=suite_root,
                runner_path=runner_path,
            )
            write_json_exclusive_at(
                protocol_fd,
                assignment_path.name,
                payload,
                maximum=MAX_ASSIGNMENT_BYTES,
            )
            assignment_paths.append(assignment_path)
            result_paths.append(result_path)

        for shard in range(len(assignments)):
            command = [
                sys.executable,
                str(runner_path),
                "--_worker-assignment",
                str(assignment_paths[shard]),
                "--_worker-result",
                str(result_paths[shard]),
            ]
            try:
                process = subprocess.Popen(
                    command,
                    cwd=run_root,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    start_new_session=True,
                )
            except OSError as error:
                scheduler_errors.append(
                    f"worker {shard} launch failed: {error}"
                )
                process = None
            processes.append(process)
            if process is not None:
                stdout_capture = BoundedBytes()
                stderr_capture = BoundedBytes()
                captures[shard] = (stdout_capture, stderr_capture)
                for stream, capture in (
                    (process.stdout, stdout_capture),
                    (process.stderr, stderr_capture),
                ):
                    drainer = threading.Thread(
                        target=drain_process_stream,
                        args=(stream, capture),
                        daemon=True,
                    )
                    drainer.start()
                    drainers[shard].append(drainer)
            live = 0
            for launched in processes:
                if launched is None:
                    continue
                try:
                    exited = observe_worker_exit_without_reaping(
                        launched, nohang=True
                    )
                except OSError as error:
                    scheduler_errors.append(
                        f"worker exit observation failed: {error}"[:4_096]
                    )
                    exited = False
                live += not exited
            max_live = max(max_live, live)

        group_identity_pinned = [False] * len(processes)
        for shard, process in enumerate(processes):
            if process is not None:
                try:
                    observe_worker_exit_without_reaping(process)
                    group_identity_pinned[shard] = True
                except OSError as error:
                    scheduler_errors.append(
                        f"worker {shard} exit observation failed: {error}"
                    )
                    try:
                        returncodes[shard] = process.wait()
                    except OSError as wait_error:
                        scheduler_errors.append(
                            f"worker {shard} wait failed: {wait_error}"
                        )

        join_drainers_until(
            drainers, time.monotonic() + PIPE_DRAIN_GRACE_SECONDS
        )
        retained = retained_drainer_shards(drainers)
        for shard in retained:
            scheduler_errors.append(
                f"worker {shard} output descriptor remained open after "
                "worker exit; termination requested for the original "
                "worker process group"
            )
        unpinned = [
            shard for shard in retained if not group_identity_pinned[shard]
        ]
        for shard in unpinned:
            scheduler_errors.append(
                f"worker {shard} process-group identity was not retained; "
                "termination was not attempted"
            )
        retained = [
            shard for shard in retained if group_identity_pinned[shard]
        ]
        signal_worker_groups(
            processes, retained, signal.SIGTERM, scheduler_errors
        )
        join_drainers_until(
            drainers, time.monotonic() + DESCENDANT_TERM_GRACE_SECONDS
        )
        retained = retained_drainer_shards(drainers)
        retained = [
            shard for shard in retained if group_identity_pinned[shard]
        ]
        signal_worker_groups(
            processes, retained, signal.SIGKILL, scheduler_errors
        )
        join_drainers_until(
            drainers, time.monotonic() + DESCENDANT_KILL_GRACE_SECONDS
        )
        for shard in retained_drainer_shards(drainers):
            scheduler_errors.append(
                f"worker {shard} output descriptor did not drain after "
                "worker process-group termination requests; a descendant "
                "may have detached"
            )

        for shard, process in enumerate(processes):
            if process is not None and returncodes[shard] is None:
                try:
                    returncodes[shard] = process.wait()
                except OSError as error:
                    scheduler_errors.append(
                        f"worker {shard} wait failed: {error}"
                    )

        scheduler_errors.extend(pipe_drain_errors(captures))

        for shard in range(len(assignments)):
            records[shard] = read_worker_result_at(
                protocol_fd, result_paths[shard].name
            )
            shard_captures = captures[shard]
            if shard_captures is None:
                residuals[shard] = {
                    "stdout": {"text": "", "bytes": 0, "truncated": False},
                    "stderr": {"text": "", "bytes": 0, "truncated": False},
                }
            else:
                residuals[shard] = {
                    name: {
                        "text": capture.render(),
                        "bytes": capture.total,
                        "truncated": capture.truncated,
                    }
                    for name, capture in zip(
                        ("stdout", "stderr"), shard_captures
                    )
                }
            record = records[shard]
            if record is None:
                scheduler_errors.append(f"missing result: worker {shard}")
                continue
            try:
                complete = validate_worker_envelope(
                    record, shard, len(assignments)
                )
                if complete:
                    validate_worker_record(
                        record,
                        identifiers,
                        digest,
                        assignments,
                        expected_shard=shard,
                        expected_output_transport=COORDINATOR_PIPE_OUTPUT,
                        tests=tests,
                    )
            except SchedulerError as error:
                scheduler_errors.append(
                    f"worker {shard} result refused: {error}"
                )
                records[shard] = None
                continue
            if complete:
                replay_records[shard] = record
                expected = (
                    1
                    if (
                        record["failures"]
                        + record["errors"]
                        + record["unexpectedSuccesses"]
                    )
                    else 0
                )
                if returncodes[shard] != expected:
                    scheduler_errors.append(
                        f"worker {shard} exit {returncodes[shard]} "
                        f"disagrees with result {expected}"
                    )
            else:
                scheduler_errors.append(
                    "incomplete worker result: " + record["scheduler_error"]
                )
                if returncodes[shard] != 3:
                    scheduler_errors.append(
                        f"worker {shard} incomplete result has exit "
                        f"{returncodes[shard]}"
                    )
                records[shard] = None
        replay_worker_outputs(assignments, replay_records, residuals)
        os.close(protocol_fd)
    return records, scheduler_errors, {
        "queue_high_water": len(assignments),
        "maximum_observed_live_children": max_live,
    }


def base_summary(runner_path, suite_root, run_root, requested):
    """Create the stable structured summary before work fills its evidence."""
    return {
        "schema": RUN_SCHEMA,
        "status": "scheduler-error",
        "event": {
            "byte_limit": MAX_RUN_SUMMARY_BYTES,
        },
        "source": {
            "runner_sha256": digest_file(runner_path),
            "suite_root": str(suite_root),
            "invocation_root": str(run_root),
        },
        "manifest": {
            "schema": MANIFEST_SCHEMA,
            "digest": None,
            "discovered": 0,
            "unique": 0,
            "ids": [],
            "encoded_bytes": 0,
            "byte_limit": MAX_MANIFEST_BYTES,
        },
        "capacity": {
            "signals": {},
            "usable": None,
            "reserve": None,
            "safety_cap": MAX_JOBS,
            "budget": requested,
            "budget_source": (
                "explicit" if requested is not None else "automatic"
            ),
            "effective_jobs": 0,
        },
        "assignment": {
            "assigned": 0,
            "fixture_domains": 0,
            "fixture_domains_atomic": False,
            "shard_counts": [],
            "shard_estimates_seconds": [],
            "exact_disjoint_union": False,
        },
        "execution": {
            "started": 0,
            "completed": 0,
            "fixture_blocked": 0,
            "executed_once": False,
            "exact_accounting": False,
            "testsRun": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0,
            "expectedFailures": 0,
            "unexpectedSuccesses": 0,
            "wall_time_seconds": 0.0,
            "child_cpu_seconds": None,
            "peak_child_rss": None,
        },
        "cache": {
            "schema": TIMING_SCHEMA,
            "status": "not-read",
            "digest": None,
            "hits": 0,
            "neutral": 0,
            "ignored_removed": 0,
            "corrupt_entries": 0,
            "write_status": "not-attempted",
        },
        "queue": {
            "queue_high_water": 0,
            "maximum_observed_live_children": 0,
        },
        "shards": [],
        "scheduler_errors": [],
    }


def summary_json(summary):
    """Encode one structured run event beneath its fixed output cap."""
    rendered = json.dumps(summary, sort_keys=True, separators=(",", ":"))
    if len(rendered.encode("utf-8")) > MAX_RUN_SUMMARY_BYTES:
        raise SchedulerError(
            f"structured summary exceeds {MAX_RUN_SUMMARY_BYTES}-byte limit"
        )
    return rendered


def scheduler_error_binding(errors, retained):
    """Bind an omitted ordered scheduler-error sequence without repeating it."""
    encoded = json.dumps(
        list(errors), separators=(",", ":")
    ).encode("utf-8")
    return {
        "schema": SCHEDULER_ERROR_EVIDENCE_SCHEMA,
        "count": len(errors),
        "encoded_bytes": len(encoded),
        "retained": retained,
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def render_summary_with_refusal(summary, scheduler_errors):
    """Turn an oversized event into one bounded, explicit refusal event."""
    try:
        return summary_json(summary), False
    except SchedulerError as error:
        message = str(error)
        if message not in scheduler_errors:
            scheduler_errors.append(message)
        all_errors = list(scheduler_errors)
        summary["status"] = "scheduler-error"
        summary["scheduler_errors"] = [message]
        summary["scheduler_error_evidence"] = scheduler_error_binding(
            all_errors, retained=1
        )
        summary["manifest"]["ids"] = []
        summary["manifest"]["ids_omitted"] = "summary-size-refusal"
        summary["shards"] = []
        return summary_json(summary), True


def emit_summary(summary, aggregate, rendered=None):
    """End direct output with human counters and one versioned JSON event."""
    failed = (
        len(aggregate.failures)
        + len(aggregate.errors)
        + len(aggregate.unexpectedSuccesses)
    )
    if failed:
        line = (
            f"{aggregate.testsRun} tests run; "
            f"{len(aggregate.failures)} failure events; "
            f"{len(aggregate.errors)} error events"
        )
        if aggregate.unexpectedSuccesses:
            line += (
                f"; {len(aggregate.unexpectedSuccesses)} "
                "unexpected success events"
            )
        print(line)
    else:
        print(f"{aggregate.testsRun}/{aggregate.testsRun} tests passed")
    print(SUMMARY_PREFIX + (rendered or summary_json(summary)))


def coordinator_main(arguments, target):
    """Discover, schedule, reconcile, report, and preserve public exit codes."""
    started_at = time.perf_counter()
    usage_before = child_usage()
    runner_path = Path(__file__).resolve(strict=True)
    suite_root = runner_path.parent
    run_root = Path.cwd().resolve(strict=True)
    summary = base_summary(
        runner_path, suite_root, run_root, arguments.jobs
    )
    aggregate = AggregateResult()
    complete = False
    scheduler_errors = []
    records = []
    assignments = []
    identifiers = []
    cache_write = None
    try:
        tests, identifiers, digest = discover_manifest(suite_root)
        encoded_manifest = manifest_bytes(identifiers)
        summary["manifest"].update({
            "digest": digest,
            "discovered": len(identifiers),
            "unique": len(set(identifiers)),
            "ids": list(identifiers),
            "encoded_bytes": len(encoded_manifest),
        })
        domains = fixture_domains(tests)
        plan = capacity_plan(arguments.jobs, len(domains))
        summary["capacity"] = plan
        timings, cache_info = load_timing_cache(
            cache_path_for(run_root), identifiers
        )
        summary["cache"] = cache_info
        assignments, estimates, neutral = partition_indices(
            identifiers,
            timings,
            plan["effective_jobs"],
            domains=domains,
        )
        summary["assignment"] = {
            "assigned": sum(len(shard) for shard in assignments),
            "fixture_domains": len(domains),
            "fixture_domains_atomic": True,
            "shard_counts": [len(shard) for shard in assignments],
            "shard_estimates_seconds": [
                round(value, 6) for value in estimates
            ],
            "neutral_seconds": round(neutral, 9),
            "exact_disjoint_union": True,
        }
        output_transport = COORDINATOR_PIPE_OUTPUT
        records, launch_errors, queue = run_parallel(
            run_root=run_root,
            runner_path=runner_path,
            suite_root=suite_root,
            identifiers=identifiers,
            digest=digest,
            assignments=assignments,
            tests=tests,
        )
        scheduler_errors.extend(launch_errors)
        summary["queue"] = queue
        summary["shards"] = summarize_validated_workers(
            assignments, records
        )
        reconciled = reconcile_worker_results(
            identifiers,
            digest,
            assignments,
            records,
            expected_output_transport=output_transport,
            tests=tests,
        )
        aggregate = AggregateResult(reconciled["counts"])
        complete = True
        summary["execution"].update(reconciled["counts"])
        summary["execution"].update({
            "started": len(reconciled["started"]),
            "completed": len(reconciled["completed"]),
            "fixture_blocked": len(reconciled["fixture_blocked"]),
            "executed_once": not reconciled["fixture_blocked"],
            "exact_accounting": reconciled["exact_accounting"],
        })
        if scheduler_errors:
            raise SchedulerError("worker launch or collection errors")
        cache_write = (identifiers, reconciled["durations"])
        failed = (
            len(aggregate.failures)
            + len(aggregate.errors)
            + len(aggregate.unexpectedSuccesses)
        )
        summary["status"] = "test-failure" if failed else "passed"
    except SchedulerError as error:
        scheduler_errors.append(str(error))
        summary["status"] = "scheduler-error"
        if records:
            valid_records = [
                record for record in records if record is not None
            ]
            partial_counts = {
                field: sum(
                    record[field] for record in valid_records
                )
                for field in (
                    "testsRun",
                    "failures",
                    "errors",
                    "skipped",
                    "expectedFailures",
                    "unexpectedSuccesses",
                )
            }
            try:
                aggregate = AggregateResult(partial_counts)
            except SchedulerError as partial_error:
                scheduler_errors.append(str(partial_error))
            else:
                summary["execution"].update(partial_counts)
            summary["execution"].update({
                "started": sum(
                    len(record["started_ids"])
                    for record in valid_records
                ),
                "completed": sum(
                    len(record["completed_ids"])
                    for record in valid_records
                ),
                "fixture_blocked": sum(
                    len(record["fixture_blocked_ids"])
                    for record in valid_records
                ),
                "executed_once": False,
                "exact_accounting": False,
            })
    except (OSError, UnicodeError, ValueError, TypeError) as error:
        scheduler_errors.append(f"scheduler boundary refused: {error}")
        summary["status"] = "scheduler-error"
    summary["scheduler_errors"] = scheduler_errors
    summary["execution"].update(
        usage_delta(usage_before, child_usage())
    )
    summary["execution"]["wall_time_seconds"] = max(
        0.0, time.perf_counter() - started_at
    )
    _, summary_refused = render_summary_with_refusal(
        summary, scheduler_errors
    )
    if summary_refused:
        cache_write = None

    report_failed = False
    if target is not None:
        try:
            write_report(
                target,
                result_payload(
                    aggregate,
                    complete=complete and not scheduler_errors,
                ),
            )
        except OSError:
            print("run_tests.py: report write failed", file=sys.stderr)
            scheduler_errors.append("public report write failed")
            summary["scheduler_errors"] = scheduler_errors
            summary["status"] = "scheduler-error"
            report_failed = True
    if not report_failed and cache_write is not None:
        try:
            write_timing_cache(run_root, *cache_write)
            summary["cache"]["write_status"] = "written"
        except OSError:
            summary["cache"]["write_status"] = "refused"
    rendered_summary, _ = render_summary_with_refusal(
        summary, scheduler_errors
    )
    emit_summary(summary, aggregate, rendered_summary)
    if report_failed:
        return 2
    if scheduler_errors:
        return 3
    return 1 if (
        len(aggregate.failures)
        + len(aggregate.errors)
        + len(aggregate.unexpectedSuccesses)
    ) else 0


def main(argv=None):
    """Run a public coordinator or one complete private worker invocation."""
    arguments, target = parse_arguments(
        sys.argv[1:] if argv is None else argv
    )
    if arguments._worker_assignment is not None:
        return worker_main(arguments)
    return coordinator_main(arguments, target)


if __name__ == "__main__":
    raise SystemExit(main())
