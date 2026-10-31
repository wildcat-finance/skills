"""Capture reads its primary endpoint and bearer from named environment variables.

These cases live apart from ``test_capture.py`` because a Promise Machine
composition relation binds that file's bytes by digest as producer and
consumer evidence, so appending cases there would move a pinned record.
"""

from collections.abc import Mapping
from contextlib import ExitStack
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
import unittest
from unittest import mock

from lazarus_lib.canonical import dump
from lazarus_lib.capture import capture_fixture
from lazarus_lib.errors import FormatError, IntegrityError, ResourceLimitError
from lazarus_lib.verifier import verify_fixture

from . import support
from .fake_rpc import FakeRpc, material_dispatch


class TrackingEnvironment(dict):
    def __init__(self, values):
        super().__init__(values)
        self.reads = []

    def __getitem__(self, key):
        self.reads.append(key)
        return super().__getitem__(key)


def forbidden_client(*args, **kwargs):
    raise AssertionError("a mapping refusal must precede client creation")


class UnusedClient:
    def __init__(self, *args, **kwargs):
        pass


class UnreadableHeaderValues(Mapping):
    """Names one header and raises, with a provider value, when it is read."""

    def __init__(self, message):
        self.message = message

    def __iter__(self):
        return iter(["X-Custom"])

    def __len__(self):
        return 1

    def __getitem__(self, key):
        raise RuntimeError(self.message)


class UnreadableHeaderNames(UnreadableHeaderValues):
    """Raises, with a provider value, as soon as its names are read."""

    def __iter__(self):
        raise RuntimeError(self.message)


class EnvironmentCaptureTests(unittest.TestCase):
    def material(self):
        material = support.synthetic_fixture_material()
        material["plan"]["limits"]["max_elapsed_seconds"] = 10
        return material

    def write_plan(self, root: Path, plan):
        path = root / "capture-plan.json"
        dump(path, plan)
        return path

    def assert_no_capture_artifacts(self, root: Path, output: Path):
        self.assertFalse(output.exists())
        self.assertEqual(list(root.glob(f".{output.name}.lazarus-*")), [])

    def capture_refusal(self, error_type, *args, **kwargs):
        """Return capture's refusal and its traceback, formatted while it is live.

        assertRaises strips the traceback from the exception it keeps, so the
        traceback is formatted here, inside the handler, before that happens.
        """
        try:
            capture_fixture(*args, **kwargs)
        except error_type as caught:
            return caught, "".join(traceback.format_exception(caught))
        self.fail(f"capture did not refuse with {error_type.__name__}")

    def assert_absent_from_every_surface(self, exception, live_traceback, value):
        surfaces = (
            str(exception),
            repr(exception.args),
            repr(exception),
            live_traceback,
        )
        for surface in surfaces:
            self.assertNotIn(value, surface)

    def test_cli_reads_primary_url_and_bearer_from_environment_not_argv_or_output(self):
        material = self.material()
        token_value = "environment-bearer-value"
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(material_dispatch(material)))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            values = {
                "LAZARUS_TEST_PRIMARY_RPC": primary.url + "?token=primary-url-secret",
                "LAZARUS_TEST_PRIMARY_BEARER": token_value,
            }
            command = [
                sys.executable,
                str(support.SCRIPTS / "lazarus.py"),
                "capture",
                "--plan",
                str(plan),
                "--rpc-url-env",
                "LAZARUS_TEST_PRIMARY_RPC",
                "--bearer-env",
                "LAZARUS_TEST_PRIMARY_BEARER",
                "--out",
                str(output),
            ]
            hidden = (*values.values(), "primary-url-secret")
            for value in hidden:
                self.assertTrue(all(value not in argument for argument in command))
            result = subprocess.run(
                command,
                env={**os.environ, **values},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(primary.headers)
            for received in primary.headers:
                self.assertEqual(received["Authorization"], f"Bearer {token_value}")
            fixture_bytes = b"".join(
                path.read_bytes() for path in output.rglob("*") if path.is_file()
            )
            for value in hidden:
                self.assertNotIn(value, result.stdout + result.stderr)
                self.assertNotIn(value.encode(), fixture_bytes)
            verify_fixture(output)

    def test_cli_requires_exactly_one_primary_url_source(self):
        material = self.material()
        primary_value = "https://primary.invalid/?token=cli-environment-value"
        cases = {
            "neither": [],
            "both": [
                "--rpc-url",
                "https://argv.invalid",
                "--rpc-url-env",
                "LAZARUS_TEST_PRIMARY_RPC",
            ],
        }
        for case, primary_options in cases.items():
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                plan = self.write_plan(root, material["plan"])
                output = root / "fixture"
                command = [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "capture",
                    "--plan",
                    str(plan),
                    *primary_options,
                    "--out",
                    str(output),
                ]
                result = subprocess.run(
                    command,
                    env={**os.environ, "LAZARUS_TEST_PRIMARY_RPC": primary_value},
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("--rpc-url", result.stderr)
                if case == "both":
                    self.assertIn("not allowed with argument", result.stderr)
                    self.assertNotIn("unrecognized arguments", result.stderr)
                else:
                    required = [
                        line for line in result.stderr.splitlines()
                        if "one of the arguments" in line
                    ]
                    self.assertEqual(len(required), 1, result.stderr)
                    self.assertIn("--rpc-url ", required[0])
                    self.assertIn("--rpc-url-env", required[0])
                self.assertNotIn(primary_value, result.stdout + result.stderr)
                self.assertNotIn("cli-environment-value", result.stdout + result.stderr)
                self.assert_no_capture_artifacts(root, output)

    def test_primary_environment_reads_are_explicit_non_empty_and_bounded(self):
        primary_value = "https://primary.invalid/?token=tracked-primary-value"
        token_value = "tracked-bearer-value"
        primary_reads = ["PRIMARY_RPC"]
        both_reads = ["PRIMARY_RPC", "BEARER"]
        cases = (
            ("absent primary", {}, "PRIMARY_RPC", "BEARER", primary_reads,
             "primary provider failed at mapping: environment variable PRIMARY_RPC is absent"),
            ("empty primary", {"PRIMARY_RPC": ""}, "PRIMARY_RPC", "BEARER", primary_reads,
             "primary provider failed at mapping: environment variable PRIMARY_RPC is empty"),
            ("blank primary", {"PRIMARY_RPC": "   "}, "PRIMARY_RPC", "BEARER", primary_reads,
             "primary provider failed at mapping: environment variable PRIMARY_RPC is empty"),
            ("absent bearer", {"PRIMARY_RPC": primary_value}, "PRIMARY_RPC", "BEARER",
             both_reads, "bearer failed at mapping: environment variable BEARER is absent"),
            ("blank bearer", {"PRIMARY_RPC": primary_value, "BEARER": " \t "},
             "PRIMARY_RPC", "BEARER", both_reads,
             "bearer failed at mapping: environment variable BEARER is empty"),
            ("two-word bearer", {"PRIMARY_RPC": primary_value, "BEARER": "two words-value"},
             "PRIMARY_RPC", "BEARER", both_reads,
             "bearer failed at mapping: environment variable BEARER is not a single header token"),
            ("crlf bearer",
             {"PRIMARY_RPC": primary_value, "BEARER": token_value + "\r\nX-Injected: yes"},
             "PRIMARY_RPC", "BEARER", both_reads,
             "bearer failed at mapping: environment variable BEARER is not a single header token"),
            ("padded bearer", {"PRIMARY_RPC": primary_value, "BEARER": token_value + " "},
             "PRIMARY_RPC", "BEARER", both_reads,
             "bearer failed at mapping: environment variable BEARER is not a single header token"),
            ("invalid primary name", {"PRIMARY_RPC": primary_value, "BEARER": token_value},
             "PRIMARY-RPC", "BEARER", [],
             "primary provider failed at mapping: invalid environment variable name"),
            ("invalid bearer name", {"PRIMARY_RPC": primary_value, "BEARER": token_value},
             "PRIMARY_RPC", "1BEARER", [],
             "bearer failed at mapping: invalid environment variable name"),
        )
        for case, values, primary_name, token_name, reads, message in cases:
            environment = TrackingEnvironment({**values, "UNDECLARED_SECRET": "do-not-read"})
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "fixture"
                plan = self.write_plan(root, self.material()["plan"])
                exception, live = self.capture_refusal(
                    FormatError,
                    plan,
                    None,
                    output,
                    rpc_url_env=primary_name,
                    bearer_env=token_name,
                    environment=environment,
                    client_factory=forbidden_client,
                )
                self.assertEqual(str(exception), message)
                if not reads:
                    self.assertNotIn(primary_name, str(exception))
                    self.assertNotIn(token_name, str(exception))
                for value in (*values.values(), "do-not-read"):
                    if value.strip():
                        self.assert_absent_from_every_surface(exception, live, value)
                self.assertEqual(environment.reads, reads)
                self.assert_no_capture_artifacts(root, output)

    def test_primary_mapping_refuses_both_or_neither_url_source_and_a_duplicate_authorization(self):
        exactly_one = (
            "primary provider failed at mapping: "
            "name exactly one of a URL or an environment variable"
        )
        duplicate = "bearer failed at mapping: a runtime Authorization header is already present"
        cases = (
            ("neither", None, {"rpc_url_env": None}, exactly_one),
            ("both", "https://primary.invalid", {"rpc_url_env": "PRIMARY_RPC"}, exactly_one),
            ("empty url beside a variable", "", {"rpc_url_env": "PRIMARY_RPC"}, exactly_one),
            ("bytes url", b"https://primary.invalid", {},
             "primary provider failed at mapping: URL must be text"),
            ("lower-case authorization", "https://primary.invalid",
             {"bearer_env": "BEARER", "headers": {"authorization": "Bearer runtime-value"}},
             duplicate),
            ("upper-case authorization", "https://primary.invalid",
             {"bearer_env": "BEARER", "headers": {"AUTHORIZATION": "Bearer runtime-value"}},
             duplicate),
        )
        for case, rpc_url, options, message in cases:
            environment = TrackingEnvironment({
                "PRIMARY_RPC": "https://environment.invalid",
                "BEARER": "environment-bearer-value",
            })
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "fixture"
                plan = self.write_plan(root, self.material()["plan"])
                with self.assertRaises(FormatError) as raised:
                    capture_fixture(
                        plan,
                        rpc_url,
                        output,
                        environment=environment,
                        client_factory=forbidden_client,
                        **options,
                    )
                self.assertEqual(str(raised.exception), message)
                self.assertNotIn("runtime-value", str(raised.exception))
                self.assertEqual(environment.reads, [])
                self.assert_no_capture_artifacts(root, output)

    def test_primary_shape_precedes_anchor_reads_and_primary_reads_follow_them(self):
        material = support.anchored_fixture_material(("archive-a",))
        material["plan"]["limits"]["max_elapsed_seconds"] = 10
        cases = (
            ("bearer name", {"bearer_env": "BAD-NAME"}, [],
             "bearer failed at mapping: invalid environment variable name"),
            ("primary value", {"bearer_env": "BEARER"}, ["ANCHOR_A", "PRIMARY_RPC"],
             "primary provider failed at mapping: environment variable PRIMARY_RPC is absent"),
        )
        for case, options, reads, message in cases:
            environment = TrackingEnvironment({
                "ANCHOR_A": "https://anchor.invalid/?token=anchor-ordering-value",
                "BEARER": "ordering-bearer-value",
            })
            with self.subTest(case=case), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "fixture"
                plan = self.write_plan(root, material["plan"])
                with self.assertRaises(FormatError) as raised:
                    capture_fixture(
                        plan,
                        None,
                        output,
                        rpc_url_env="PRIMARY_RPC",
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment=environment,
                        client_factory=forbidden_client,
                        **options,
                    )
                self.assertEqual(str(raised.exception), message)
                self.assertEqual(environment.reads, reads)
                self.assert_no_capture_artifacts(root, output)

    def test_environment_bearer_joins_the_secret_scan_and_every_error_surface(self):
        material = self.material()
        token_value = "echoed-environment-bearer-value"
        base = material_dispatch(material)

        def echo_bearer(method, params, server):
            if method == "eth_chainId" and params == [] and len(server.requests) > 1:
                return server.headers[-1]["Authorization"].split(" ", 1)[1]
            return base(method, params, server)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(echo_bearer) as primary:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            exception, live = self.capture_refusal(
                IntegrityError,
                plan,
                primary.url,
                output,
                bearer_env="BEARER",
                environment={"BEARER": token_value},
            )
            self.assertRegex(str(exception), "secret")
            self.assert_absent_from_every_surface(exception, live, token_value)
            self.assertEqual(primary.headers[0]["Authorization"], f"Bearer {token_value}")
            self.assert_no_capture_artifacts(root, output)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture._capture_into",
                side_effect=IntegrityError(token_value),
            ):
                exception, live = self.capture_refusal(
                    IntegrityError,
                    plan,
                    "https://primary.invalid",
                    output,
                    bearer_env="BEARER",
                    environment={"BEARER": token_value},
                    client_factory=UnusedClient,
                )
            self.assertIsNone(exception.__cause__)
            self.assertIsNone(exception.__context__)
            self.assert_absent_from_every_surface(exception, live, token_value)
            self.assert_no_capture_artifacts(root, output)

    def test_environment_primary_url_joins_the_secret_scan(self):
        material = self.material()
        base = material_dispatch(material)
        holder = {}

        def echo_primary(method, params, server):
            if method == "eth_chainId" and params == [] and len(server.requests) > 1:
                return holder["url"]
            return base(method, params, server)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(echo_primary) as primary:
            holder["url"] = primary.url + "?token=primary-scan-secret"
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            exception, live = self.capture_refusal(
                IntegrityError,
                plan,
                None,
                output,
                rpc_url_env="PRIMARY_RPC",
                environment={"PRIMARY_RPC": holder["url"]},
            )
            self.assertRegex(str(exception), "secret")
            for value in (holder["url"], "primary-scan-secret"):
                self.assert_absent_from_every_surface(exception, live, value)
            self.assertGreater(len(primary.requests), 1)
            self.assert_no_capture_artifacts(root, output)

    def test_short_bearer_components_are_refused_by_the_classifier(self):
        token_value = "abcd.ef.ghijkl"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, self.material()["plan"])
            output = root / "fixture"
            exception, live = self.capture_refusal(
                ResourceLimitError,
                plan,
                "https://primary.invalid",
                output,
                bearer_env="BEARER",
                environment={"BEARER": token_value},
                client_factory=forbidden_client,
            )
            self.assertRegex(str(exception), "resource limits")
            self.assert_absent_from_every_surface(exception, live, token_value)
            self.assert_no_capture_artifacts(root, output)

    def test_header_mapping_failure_does_not_expose_provider_values(self):
        token_value = "mapping-raised-provider-value"
        for headers in (
            UnreadableHeaderValues(token_value),
            UnreadableHeaderNames(token_value),
        ):
            with self.subTest(headers=type(headers).__name__), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                plan = self.write_plan(root, self.material()["plan"])
                output = root / "fixture"
                exception, live = self.capture_refusal(
                    FormatError,
                    plan,
                    "https://primary.invalid",
                    output,
                    headers=headers,
                    bearer_env="BEARER",
                    environment={"BEARER": token_value},
                    client_factory=forbidden_client,
                )
                self.assertEqual(
                    str(exception),
                    "bearer failed at mapping: runtime headers could not be read",
                )
                self.assertIsNone(exception.__cause__)
                self.assertIsNone(exception.__context__)
                self.assert_absent_from_every_surface(exception, live, token_value)
                self.assert_no_capture_artifacts(root, output)

    def test_primary_and_bearer_variables_must_differ(self):
        environment = TrackingEnvironment({
            "SHARED_RPC": "https://primary.invalid/?token=shared-variable-value",
        })
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, self.material()["plan"])
            output = root / "fixture"
            exception, live = self.capture_refusal(
                FormatError,
                plan,
                None,
                output,
                rpc_url_env="SHARED_RPC",
                bearer_env="SHARED_RPC",
                environment=environment,
                client_factory=forbidden_client,
            )
            self.assertEqual(
                str(exception),
                "primary provider failed at mapping: the primary and bearer variables must differ",
            )
            self.assert_absent_from_every_surface(exception, live, "shared-variable-value")
            self.assertEqual(environment.reads, [])
            self.assert_no_capture_artifacts(root, output)


if __name__ == "__main__":
    unittest.main()
