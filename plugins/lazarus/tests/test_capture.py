"""A fake archive RPC exercises the complete finite capture boundary."""

import copy
from contextlib import ExitStack
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import traceback
import unittest
from unittest import mock

from lazarus_lib import __version__
from lazarus_lib.canonical import dump, dumps, load, loads
from lazarus_lib.capture import (
    CaptureError,
    _atomic_no_replace,
    _validate_capture_plan,
    capture_failure_terminal_result,
    capture_fixture,
)
from lazarus_lib.errors import FormatError, IntegrityError, PathError, ResourceLimitError
from lazarus_lib.records import read_anchor_records, read_rpc_records
from lazarus_lib.rpc import JsonRpcClient
from lazarus_lib.scrub import (
    assert_no_secret_bytes,
    assert_no_secrets as scan_fixture_secrets,
    provider_secret_union,
)
from lazarus_lib.verifier import verify_fixture

from . import support
from .fake_rpc import FakeRpc, RpcError, material_dispatch, receipt_material_dispatch


class CaptureTests(unittest.TestCase):
    def material(self):
        material = support.synthetic_fixture_material()
        material["plan"]["limits"]["max_elapsed_seconds"] = 10
        return material

    def write_plan(self, root: Path, plan):
        path = root / "capture-plan.json"
        dump(path, plan)
        return path

    def anchored_material(self, source_ids=("archive-a", "archive-b")):
        material = support.anchored_fixture_material(source_ids)
        material["plan"]["limits"]["max_elapsed_seconds"] = 10
        return material

    def assert_no_capture_artifacts(self, root: Path, output: Path):
        self.assertFalse(output.exists())
        self.assertEqual(list(root.glob(f".{output.name}.lazarus-*")), [])

    def test_plan_v3_requires_its_anchor_mapping_before_network(self):
        def forbidden_client(*args, **kwargs):
            raise AssertionError("plan-v3 mapping refusal must precede client creation")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            candidate = support.sample_plan_v3()
            candidate["limits"]["max_elapsed_seconds"] = 10
            plan = self.write_plan(root, candidate)
            output = root / "fixture"
            with self.assertRaisesRegex(FormatError, "missing archive-a"):
                capture_fixture(
                    plan,
                    "https://primary.example",
                    output,
                    client_factory=forbidden_client,
                )
            self.assert_no_capture_artifacts(root, output)

    def test_cli_captures_and_verifies_one_deterministic_fixture(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material), reverse_batches=True
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "capture",
                    "--plan",
                    str(plan),
                    "--rpc-url",
                    server.url + "?apiKey=query-secret",
                    "--out",
                    str(output),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            report = verify_fixture(output)
            self.assertEqual(report["manifest"]["tool_version"], __version__)
            self.assertIn(report["fixture_digest"], result.stdout)
            self.assertNotIn("query-secret", b"".join(
                path.read_bytes() for path in output.rglob("*") if path.is_file()
            ).decode("utf-8"))
            self.assertEqual(
                [request["params"] for request in server.requests if request["method"] == "eth_getBlockByNumber"],
                [[material["header"]["number"], False]] * 2,
            )

    def test_repeated_capture_has_identical_bytes_and_digest(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            first = root / "first"
            second = root / "second"
            one = capture_fixture(plan, server.url, first)
            two = capture_fixture(plan, server.url, second)
            self.assertEqual(one["fixture_digest"], two["fixture_digest"])
            self.assertEqual(
                {path.relative_to(first): path.read_bytes() for path in first.rglob("*") if path.is_file()},
                {path.relative_to(second): path.read_bytes() for path in second.rglob("*") if path.is_file()},
            )

    def test_anchor_mappings_must_exactly_cover_the_plan_before_network(self):
        cases = (
            ([], {}, "missing archive-a, archive-b"),
            (["archive-a=ANCHOR_A"], {"ANCHOR_A": "https://a.example"}, "missing archive-b"),
            (
                ["archive-a=ANCHOR_A", "archive-b=ANCHOR_B", "extra=EXTRA"],
                {
                    "ANCHOR_A": "https://a.example",
                    "ANCHOR_B": "https://b.example",
                    "EXTRA": "https://extra.example",
                },
                "extra extra",
            ),
            (
                ["archive-a=ANCHOR_A", "archive-a=ANCHOR_B", "archive-b=ANCHOR_B"],
                {"ANCHOR_A": "https://a.example", "ANCHOR_B": "https://b.example"},
                "duplicate archive-a",
            ),
            (["archive-a"], {}, "mapping"),
            (["archive-a="], {}, "mapping"),
            (
                [f"source-{index:02d}=ANCHOR_{index}" for index in range(33)],
                {},
                "count exceeds 32",
            ),
        )

        def forbidden_client(*args, **kwargs):
            raise AssertionError("mapping refusal must precede client creation")

        for mappings, environment, message in cases:
            with self.subTest(mappings=mappings), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "fixture"
                plan = self.write_plan(root, self.anchored_material()["plan"])
                with self.assertRaisesRegex(FormatError, message):
                    capture_fixture(
                        plan,
                        "https://primary.example",
                        output,
                        anchor_rpc_env=mappings,
                        environment=environment,
                        client_factory=forbidden_client,
                    )
                self.assert_no_capture_artifacts(root, output)

    def test_anchor_environment_reads_are_explicit_non_empty_and_bounded(self):
        class TrackingEnvironment(dict):
            def __init__(self, values):
                super().__init__(values)
                self.reads = []

            def __getitem__(self, key):
                self.reads.append(key)
                return super().__getitem__(key)

        cases = (
            ({"ANCHOR_A": "https://a.example"}, "archive-b"),
            ({"ANCHOR_A": "https://a.example", "ANCHOR_B": ""}, "archive-b"),
            ({"ANCHOR_A": "https://a.example", "ANCHOR_B": "   "}, "archive-b"),
        )

        def forbidden_client(*args, **kwargs):
            raise AssertionError("environment refusal must precede client creation")

        for values, source_id in cases:
            environment = TrackingEnvironment({**values, "UNDECLARED_SECRET": "do-not-read"})
            with self.subTest(values=values), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "fixture"
                plan = self.write_plan(root, self.anchored_material()["plan"])
                with self.assertRaisesRegex(FormatError, f"{source_id}.*mapping"):
                    capture_fixture(
                        plan,
                        "https://primary.example",
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A", "archive-b=ANCHOR_B"),
                        environment=environment,
                        client_factory=forbidden_client,
                    )
                self.assertEqual(environment.reads, ["ANCHOR_A", "ANCHOR_B"])
                self.assert_no_capture_artifacts(root, output)

    def test_direct_capture_records_sorted_anchors_with_one_fixed_utc_clock(self):
        material = self.anchored_material()
        observed = datetime(2026, 8, 25, 8, 30, 45, 123456, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(material_dispatch(material)))
            archive_a = stack.enter_context(FakeRpc(material_dispatch(material)))
            archive_b = stack.enter_context(FakeRpc(material_dispatch(material)))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            environment = {
                "ANCHOR_A": archive_a.url + "?token=anchor-a-secret",
                "ANCHOR_B": archive_b.url + "?token=anchor-b-secret",
                "UNDECLARED_SECRET": "do-not-read",
            }
            report = capture_fixture(
                plan,
                primary.url,
                output,
                anchor_rpc_env=("archive-b=ANCHOR_B", "archive-a=ANCHOR_A"),
                environment=environment,
                wall_clock=lambda: observed,
            )
            records = read_anchor_records(output / "anchors.jsonl")
            self.assertEqual([item["source_id"] for item in records], ["archive-a", "archive-b"])
            self.assertEqual({item["observed_at"] for item in records}, {"2026-08-25T08:30:45.123456Z"})
            self.assertEqual(report["chain_anchors"], {
                "records": 2,
                "canonical_chain_claim": False,
                "provider_independence_claim": False,
            })
            for server in (archive_a, archive_b):
                self.assertEqual(
                    [(item["method"], item["params"]) for item in server.requests],
                    [
                        ("eth_chainId", []),
                        ("eth_getBlockByNumber", [material["header"]["number"], False]),
                    ],
                )
            fixture_bytes = b"".join(
                path.read_bytes() for path in output.rglob("*") if path.is_file()
            )
            for secret in ("anchor-a-secret", "anchor-b-secret", archive_a.url, archive_b.url):
                self.assertNotIn(secret.encode(), fixture_bytes)

    def test_cli_reads_anchor_urls_from_environment_not_argv_or_output(self):
        material = self.anchored_material()
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(material_dispatch(material)))
            archive_a = stack.enter_context(FakeRpc(material_dispatch(material)))
            archive_b = stack.enter_context(FakeRpc(material_dispatch(material)))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            command = [
                sys.executable,
                str(support.SCRIPTS / "lazarus.py"),
                "capture",
                "--plan",
                str(plan),
                "--rpc-url",
                primary.url,
                "--anchor-rpc-env",
                "archive-b=LAZARUS_TEST_ANCHOR_B",
                "--anchor-rpc-env",
                "archive-a=LAZARUS_TEST_ANCHOR_A",
                "--out",
                str(output),
            ]
            anchor_values = {
                "LAZARUS_TEST_ANCHOR_A": archive_a.url + "?token=anchor-a-secret",
                "LAZARUS_TEST_ANCHOR_B": archive_b.url + "?token=anchor-b-secret",
            }
            for value in anchor_values.values():
                self.assertNotIn(value, command)
            result = subprocess.run(
                command,
                env={**os.environ, **anchor_values},
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("anchor-sources-declared: 2", result.stdout)
            self.assertIn("chain-anchor-records: 2", result.stdout)
            for secret in (*anchor_values.values(), "anchor-a-secret", "anchor-b-secret"):
                self.assertNotIn(secret, result.stdout + result.stderr)

    def test_anchor_provider_disagreements_fail_at_bounded_stages(self):
        mutations = {
            "chain": ("eth_chainId", "0x2"),
            "height": ("number", "0x1"),
            "hash": ("hash", support.hash32("ff")),
            "schema": ("hash", None),
        }
        for stage, (field, value) in mutations.items():
            material = self.anchored_material(("archive-a",))
            base = material_dispatch(material)

            def dispatch(method, params, server, *, field=field, value=value):
                if field == "eth_chainId" and method == "eth_chainId":
                    return value
                result = base(method, params, server)
                if method == "eth_getBlockByNumber":
                    result = copy.deepcopy(result)
                    result[field] = value
                return result

            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory)
                primary = stack.enter_context(FakeRpc(material_dispatch(material)))
                anchor = stack.enter_context(FakeRpc(dispatch))
                plan = self.write_plan(root, material["plan"])
                output = root / "fixture"
                error = CaptureError if stage == "schema" else IntegrityError
                with self.assertRaisesRegex(error, f"archive-a.*{stage}"):
                    capture_fixture(
                        plan,
                        primary.url,
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment={"ANCHOR_A": anchor.url},
                    )
                self.assert_no_capture_artifacts(root, output)

    def test_anchor_transport_redirect_and_raw_error_are_secret_free(self):
        material = self.anchored_material(("archive-a",))
        failures = (
            lambda destination: FakeRpc(material_dispatch(material), redirect_to=destination),
            lambda destination: FakeRpc(
                lambda method, params, server: RpcError(
                    -32042,
                    "provider said anchor-transport-secret",
                    {"url": destination},
                )
            ),
        )
        for factory in failures:
            with self.subTest(factory=factory), tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
                root = Path(directory)
                primary = stack.enter_context(FakeRpc(material_dispatch(material)))
                anchor = stack.enter_context(factory("https://redirect-secret.example"))
                plan = self.write_plan(root, material["plan"])
                output = root / "fixture"
                with self.assertRaisesRegex(CaptureError, "archive-a.*transport") as raised:
                    capture_fixture(
                        plan,
                        primary.url,
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment={"ANCHOR_A": anchor.url + "?token=anchor-url-secret"},
                    )
                diagnostic = str(raised.exception)
                for secret in ("anchor-transport-secret", "redirect-secret", "anchor-url-secret", anchor.url):
                    self.assertNotIn(secret, diagnostic)
                self.assert_no_capture_artifacts(root, output)

    def test_partial_anchor_success_and_shared_request_limit_leave_nothing(self):
        material = self.anchored_material()
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(material_dispatch(material)))
            archive_a = stack.enter_context(FakeRpc(material_dispatch(material)))
            base = material_dispatch(material)

            def disagree(method, params, server):
                result = base(method, params, server)
                if method == "eth_getBlockByNumber":
                    result = copy.deepcopy(result)
                    result["hash"] = support.hash32("ff")
                return result

            archive_b = stack.enter_context(FakeRpc(disagree))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(IntegrityError, "archive-b.*hash"):
                capture_fixture(
                    plan,
                    primary.url,
                    output,
                    anchor_rpc_env=("archive-a=ANCHOR_A", "archive-b=ANCHOR_B"),
                    environment={"ANCHOR_A": archive_a.url, "ANCHOR_B": archive_b.url},
                )
            self.assertEqual(len(archive_a.requests), 2)
            self.assert_no_capture_artifacts(root, output)

    def test_anchor_clients_share_response_byte_and_elapsed_time_limits(self):
        class ControlledClock:
            def __init__(self):
                self.value = 0.0

            def __call__(self):
                return self.value

        for budget in ("bytes", "time"):
            material = self.anchored_material(("archive-a",))
            material["plan"]["limits"]["max_component_bytes"] = 1_000_000
            material["plan"]["limits"]["max_total_bytes"] = 1_000_000
            clock = ControlledClock()
            seen_limits = []

            class ExhaustingAnchorClient:
                def __init__(self, limits):
                    self.limits = limits

                def call(self, method, params):
                    if budget == "time":
                        clock.value = 10.0
                        self.limits.before_request()
                    else:
                        self.limits.before_request()
                        self.limits.after_response(999_999)
                    raise AssertionError("the shared limit must refuse first")

            with self.subTest(budget=budget), tempfile.TemporaryDirectory() as directory, FakeRpc(
                material_dispatch(material)
            ) as primary:
                root = Path(directory)
                plan = self.write_plan(root, material["plan"])
                output = root / "fixture"

                def client_factory(url, limits, headers=None):
                    seen_limits.append(limits)
                    if url == "https://anchor-budget.example":
                        return ExhaustingAnchorClient(limits)
                    return JsonRpcClient(url, limits, headers=headers)

                with self.assertRaisesRegex(ResourceLimitError, "archive-a.*limit"):
                    capture_fixture(
                        plan,
                        primary.url,
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment={"ANCHOR_A": "https://anchor-budget.example"},
                        clock=clock,
                        client_factory=client_factory,
                    )
                self.assertEqual(len(seen_limits), 2)
                self.assertIs(seen_limits[0], seen_limits[1])
                self.assert_no_capture_artifacts(root, output)

    def test_elapsed_budget_starts_before_provider_secret_mapping(self):
        class ControlledClock:
            value = 0.0

            def __call__(self):
                return self.value

        clock = ControlledClock()
        material = self.anchored_material(("archive-a",))
        material["plan"]["limits"]["max_elapsed_seconds"] = 1
        original_mapping = provider_secret_union

        def delayed_mapping(*args, **kwargs):
            secrets = original_mapping(*args, **kwargs)
            clock.value = 2.0
            return secrets

        def forbidden_client(*args, **kwargs):
            raise AssertionError("mapping must consume the shared elapsed budget")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture.provider_secret_union",
                side_effect=delayed_mapping,
            ):
                with self.assertRaisesRegex(ResourceLimitError, "seconds"):
                    capture_fixture(
                        plan,
                        "https://primary.invalid",
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment={"ANCHOR_A": "https://anchor.invalid"},
                        clock=clock,
                        client_factory=forbidden_client,
                    )
            self.assert_no_capture_artifacts(root, output)

        material = self.anchored_material()
        material["plan"]["limits"]["max_requests"] = 9
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(material_dispatch(material)))
            archive_a = stack.enter_context(FakeRpc(material_dispatch(material)))
            archive_b = stack.enter_context(FakeRpc(material_dispatch(material)))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(ResourceLimitError, "archive-b.*limit"):
                capture_fixture(
                    plan,
                    primary.url,
                    output,
                    anchor_rpc_env=("archive-a=ANCHOR_A", "archive-b=ANCHOR_B"),
                    environment={"ANCHOR_A": archive_a.url, "ANCHOR_B": archive_b.url},
                )
            self.assert_no_capture_artifacts(root, output)

    def test_provider_mapping_receives_the_shared_elapsed_callback(self):
        material = self.anchored_material(("archive-a",))
        observed_callbacks = []

        def bounded_mapping(*args, **kwargs):
            observed_callbacks.append(kwargs.get("check_time"))
            raise ResourceLimitError("bounded mapping refusal")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture.provider_secret_union",
                side_effect=bounded_mapping,
            ):
                with self.assertRaisesRegex(ResourceLimitError, "provider mapping"):
                    capture_fixture(
                        plan,
                        "https://primary.invalid",
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment={"ANCHOR_A": "https://anchor.invalid"},
                    )
            self.assertEqual(len(observed_callbacks), 1)
            self.assertTrue(callable(observed_callbacks[0]))
            self.assert_no_capture_artifacts(root, output)

    def test_anchor_schema_clock_fails_before_finalisation(self):
        material = self.anchored_material(("archive-a",))
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(material_dispatch(material)))
            anchor = stack.enter_context(FakeRpc(material_dispatch(material)))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(CaptureError, "archive-a.*schema"):
                capture_fixture(
                    plan,
                    primary.url,
                    output,
                    anchor_rpc_env=("archive-a=ANCHOR_A",),
                    environment={"ANCHOR_A": anchor.url},
                    wall_clock=lambda: datetime(2026, 8, 25),
                )
            self.assert_no_capture_artifacts(root, output)

    def test_failed_final_verification_is_sanitised_and_atomic(self):
        material = self.anchored_material(("archive-a",))
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(material_dispatch(material)))
            anchor = stack.enter_context(FakeRpc(material_dispatch(material)))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture.verify_fixture",
                side_effect=IntegrityError("provider-final-secret"),
            ), self.assertRaisesRegex(CaptureError, "final verification") as raised:
                capture_fixture(
                    plan,
                    primary.url,
                    output,
                    anchor_rpc_env=("archive-a=ANCHOR_A",),
                    environment={"ANCHOR_A": anchor.url},
                )
            self.assertNotIn("provider-final-secret", str(raised.exception))
            self.assertIsNone(raised.exception.__cause__)
            self.assertIsNone(raised.exception.__context__)
            surfaces = (
                repr(raised.exception.args),
                repr(raised.exception),
                "".join(traceback.format_exception(raised.exception)),
            )
            self.assertTrue(
                all("provider-final-secret" not in surface for surface in surfaces)
            )
            self.assert_no_capture_artifacts(root, output)

    def test_unexpected_capture_failure_retains_no_nested_exception_material(self):
        marker = "provider-unexpected-exception-secret"
        material = self.anchored_material(("archive-a",))

        class UnusedClient:
            def __init__(self, *args, **kwargs):
                pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture._capture_into",
                side_effect=RuntimeError(marker),
            ):
                with self.assertRaisesRegex(
                    CaptureError, "before fixture finalisation"
                ) as raised:
                    capture_fixture(
                        plan,
                        "https://primary.invalid",
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment={"ANCHOR_A": "https://anchor.invalid"},
                        client_factory=UnusedClient,
                    )
            self.assertIsNone(raised.exception.__cause__)
            self.assertIsNone(raised.exception.__context__)
            surfaces = (
                repr(raised.exception.args),
                repr(raised.exception),
                "".join(traceback.format_exception(raised.exception)),
            )
            self.assertTrue(all(marker not in surface for surface in surfaces))
            self.assert_no_capture_artifacts(root, output)

    def test_expected_capture_failure_redacts_every_exception_surface(self):
        marker = "provider-expected-exception-secret"
        material = self.anchored_material(("archive-a",))

        class UnusedClient:
            def __init__(self, *args, **kwargs):
                pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture._capture_into",
                side_effect=IntegrityError(marker),
            ):
                with self.assertRaises(IntegrityError) as raised:
                    capture_fixture(
                        plan,
                        f"https://primary.invalid/{marker}",
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_A",),
                        environment={"ANCHOR_A": "https://anchor.invalid"},
                        client_factory=UnusedClient,
                    )
            self.assertIsNone(raised.exception.__cause__)
            self.assertIsNone(raised.exception.__context__)
            surfaces = (
                repr(raised.exception.args),
                repr(raised.exception),
                "".join(traceback.format_exception(raised.exception)),
            )
            self.assertTrue(all(marker not in surface for surface in surfaces))
            self.assert_no_capture_artifacts(root, output)

    def test_union_secret_scan_fails_before_finalisation(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            material = self.anchored_material(("archive-a",))
            anchor = stack.enter_context(FakeRpc(material_dispatch(material)))
            anchor_secret = anchor.url + "?token=anchor-final-secret"
            base = material_dispatch(material)

            def primary_dispatch(method, params, server):
                if method == "eth_chainId" and params == [] and len(server.requests) > 1:
                    return anchor_secret
                return base(method, params, server)

            primary = stack.enter_context(FakeRpc(primary_dispatch))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(IntegrityError, "secret"):
                capture_fixture(
                    plan,
                    primary.url,
                    output,
                    anchor_rpc_env=("archive-a=ANCHOR_A",),
                    environment={"ANCHOR_A": anchor_secret},
                )
            self.assert_no_capture_artifacts(root, output)

    def test_runtime_bearer_and_cookie_headers_never_enter_fixture(self):
        material = self.material()
        headers = {
            "Authorization": "Bearer bearer-secret",
            "Cookie": "session=cookie-secret",
        }
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            capture_fixture(plan, server.url, output, headers=headers)
            fixture_bytes = b"".join(
                path.read_bytes() for path in output.rglob("*") if path.is_file()
            )
            self.assertNotIn(b"bearer-secret", fixture_bytes)
            self.assertNotIn(b"cookie-secret", fixture_bytes)
            self.assertEqual(server.headers[0]["Authorization"], headers["Authorization"])
            self.assertEqual(server.headers[0]["Cookie"], headers["Cookie"])

    def test_expected_hash_and_header_equivocation_fail_without_output(self):
        material = self.material()
        bad_plan = copy.deepcopy(material["plan"])
        bad_plan["block"]["hash"] = support.hash32("ff")
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, bad_plan)
            output = root / "fixture"
            with self.assertRaises(IntegrityError):
                capture_fixture(plan, server.url, output)
            self.assertFalse(output.exists())

        calls = {"headers": 0}
        base = material_dispatch(material)

        def equivocate(method, params, server):
            result = base(method, params, server)
            if method == "eth_getBlockByNumber":
                calls["headers"] += 1
                if calls["headers"] == 2:
                    result = copy.deepcopy(result)
                    result["gasUsed"] = "0x1"
            return result

        with tempfile.TemporaryDirectory() as directory, FakeRpc(equivocate) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaises(IntegrityError):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_moving_tags_are_rejected_before_network_access(self):
        material = self.material()
        material["plan"]["requests"][0]["params"] = [{"block": "latest"}]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(FormatError, "moving block tag"):
                capture_fixture(plan, "http://127.0.0.1:1/?token=secret", root / "fixture")
            self.assertFalse((root / "fixture").exists())

        material = support.synthetic_fixture_material()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(FormatError, "max_elapsed_seconds"):
                capture_fixture(plan, "http://127.0.0.1:1", root / "fixture")

    def test_hash_selector_rejection_uses_bracketed_number_fallback(self):
        material = self.material()
        material["plan"]["requests"] = []
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material, reject_hash_selectors=True)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            capture_fixture(plan, server.url, root / "fixture")
            state_requests = [
                item for item in server.requests if item["method"] in {"eth_getProof", "eth_getCode"}
            ]
            self.assertEqual(len(state_requests), 4)
            self.assertTrue(isinstance(state_requests[0]["params"][-1], dict))
            self.assertEqual(state_requests[1]["params"][-1], material["header"]["number"])
            self.assertEqual(
                len([item for item in server.requests if item["method"] == "eth_getBlockByNumber"]),
                2,
            )

    def test_optional_failure_is_sanitised_but_required_failure_aborts(self):
        material = self.material()
        material["plan"]["requests"] = [
            {
                "name": "optional",
                "method": "eth_getTransactionReceipt",
                "params": [],
                "required": False,
                "evidence": "recorded-rpc",
            }
        ]
        base = material_dispatch(material)

        def dispatch(method, params, server):
            if method == "eth_getTransactionReceipt":
                return RpcError(-32042, "provider said bearer-secret", {"url": "query-secret"})
            return base(method, params, server)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(dispatch) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            capture_fixture(plan, server.url, output)
            record = read_rpc_records(output / "rpc.jsonl")[0]
            self.assertEqual(
                record["outcome"]["error"],
                {"code": -32042, "message": "provider request failed"},
            )
            self.assertNotIn("secret", (output / "rpc.jsonl").read_text())

        material["plan"]["requests"][0]["required"] = True
        with tempfile.TemporaryDirectory() as directory, FakeRpc(dispatch) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(CaptureError, "required"):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_proof_or_code_rejection_happens_before_finalisation(self):
        material = self.material()
        base = material_dispatch(material)

        def dispatch(method, params, server):
            if method == "eth_getCode":
                return "0x6001"
            return base(method, params, server)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(dispatch) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(IntegrityError, "captured code"):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

        def bad_proof(method, params, server):
            result = base(method, params, server)
            if method == "eth_getProof":
                result = copy.deepcopy(result)
                node = result["accountProof"][0]
                result["accountProof"][0] = node[:-1] + ("0" if node[-1] != "0" else "1")
            return result

        with tempfile.TemporaryDirectory() as directory, FakeRpc(bad_proof) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(IntegrityError, "root"):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_response_byte_and_elapsed_time_limits_leave_no_output(self):
        material = self.material()
        material["plan"]["limits"]["max_component_bytes"] = 64
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaises(ResourceLimitError):
                capture_fixture(plan, server.url, root / "fixture")
            self.assertFalse((root / "fixture").exists())

    def test_oversized_plan_fails_before_client_or_network_creation(self):
        material = self.material()
        material["plan"]["limits"]["max_component_bytes"] = 1

        def forbidden_client(*args, **kwargs):
            raise AssertionError("client must not be created")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(ResourceLimitError, "capture plan"):
                capture_fixture(
                    plan,
                    "http://127.0.0.1:1",
                    root / "fixture",
                    client_factory=forbidden_client,
                )

    def test_elapsed_time_limit_leaves_no_output(self):
        material = self.material()

        class AdvancingClock:
            def __init__(self):
                self.value = 0.0

            def __call__(self):
                self.value += 0.34
                return self.value

        material["plan"]["limits"]["max_elapsed_seconds"] = 1
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            with self.assertRaisesRegex(ResourceLimitError, "seconds"):
                capture_fixture(
                    plan,
                    server.url,
                    root / "fixture",
                    clock=AdvancingClock(),
                )
            self.assertFalse((root / "fixture").exists())

    def test_out_of_order_planned_responses_keep_their_exact_results(self):
        material = self.material()
        material["plan"]["requests"] = [
            {"name": "transaction", "method": "eth_getTransactionByHash", "params": [1], "required": True, "evidence": "recorded-rpc"},
            {"name": "receipt", "method": "eth_getTransactionReceipt", "params": [2], "required": True, "evidence": "recorded-rpc"},
        ]
        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material), reverse_batches=True
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            capture_fixture(plan, server.url, output)
            records = {item["name"]: item for item in read_rpc_records(output / "rpc.jsonl")}
            self.assertEqual(records["transaction"]["outcome"]["result"]["params"], [1])
            self.assertEqual(records["receipt"]["outcome"]["result"]["params"], [2])

    def test_unknown_and_state_changing_methods_are_rejected_before_network(self):
        for method in ("eth_alpha", "evm_mine", "anvil_setBalance", "debug_setHead"):
            with self.subTest(method=method):
                material = self.material()
                material["plan"]["requests"][0]["method"] = method
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    plan = self.write_plan(root, material["plan"])
                    with self.assertRaisesRegex(FormatError, "read-only"):
                        capture_fixture(plan, "http://127.0.0.1:1", root / "fixture")

    def test_interrupted_finalisation_leaves_no_fixture_or_staging_directory(self):
        material = self.anchored_material(("archive-a",))

        def interrupt(source, destination):
            raise OSError("simulated interruption")

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            server = stack.enter_context(FakeRpc(material_dispatch(material)))
            anchor = stack.enter_context(FakeRpc(material_dispatch(material)))
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(CaptureError, "finalisation"):
                capture_fixture(
                    plan,
                    server.url,
                    output,
                    anchor_rpc_env=("archive-a=ANCHOR_A",),
                    environment={"ANCHOR_A": anchor.url},
                    finalizer=interrupt,
                )
            self.assertFalse(output.exists())
            self.assertEqual(list(root.glob(".fixture.lazarus-*")), [])

    def test_existing_output_is_never_overwritten(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            output.mkdir()
            with self.assertRaisesRegex(PathError, "already exists"):
                capture_fixture(plan, "http://127.0.0.1:1", output)

    def test_output_created_during_capture_is_not_replaced(self):
        material = self.material()

        def race(source, destination):
            Path(destination).mkdir()
            _atomic_no_replace(source, destination)

        with tempfile.TemporaryDirectory() as directory, FakeRpc(
            material_dispatch(material)
        ) as server:
            root = Path(directory)
            plan = self.write_plan(root, material["plan"])
            output = root / "fixture"
            with self.assertRaisesRegex(PathError, "appeared"):
                capture_fixture(
                    plan,
                    server.url,
                    output,
                    finalizer=race,
                )
            self.assertTrue(output.is_dir())
            self.assertEqual(list(output.iterdir()), [])
            self.assertEqual(list(root.glob(".fixture.lazarus-*")), [])


class ReceiptCaptureTests(unittest.TestCase):
    def material(self):
        material = support.receipt_fixture_material()
        material["plan"]["limits"].update(
            {
                "max_requests": 16,
                "max_component_bytes": 1_048_576,
                "max_total_bytes": 4_194_304,
                "max_elapsed_seconds": 10,
            }
        )
        return material

    def observed_at(self, material):
        return datetime.fromisoformat(
            material["anchor_records"][0]["observed_at"].replace("Z", "+00:00")
        )

    def rpc_without_fixture_port(self, dispatch, forbidden_bytes, **options):
        """Bind a loopback port whose spelling is absent from fixed output."""
        rejected = []
        selected = None
        try:
            for _ in range(128):
                candidate = FakeRpc(dispatch, **options)
                port = str(candidate.server.server_address[1]).encode("ascii")
                if port not in forbidden_bytes:
                    selected = candidate
                    break
                rejected.append(candidate)
        finally:
            for candidate in rejected:
                candidate.server.server_close()
        if selected is None:
            self.fail("could not allocate a fixture-neutral loopback port")
        return selected

    def capture_material(
        self,
        material,
        root,
        output,
        *,
        dispatch=None,
        reverse_fields=False,
        clock=None,
    ):
        source_id = material["plan"]["anchor_sources"][0]["source_id"]
        plan_path = root / "receipt-plan.json"
        dump(plan_path, material["plan"])
        forbidden_port_bytes = b"".join(
            path.read_bytes()
            for path in sorted(support.RECEIPT_PROOF_FIXTURE.iterdir())
            if path.is_file()
        )
        with ExitStack() as stack:
            primary = stack.enter_context(
                self.rpc_without_fixture_port(
                    dispatch or receipt_material_dispatch(material),
                    forbidden_port_bytes,
                    reverse_fields=reverse_fields,
                )
            )
            anchor = stack.enter_context(
                self.rpc_without_fixture_port(
                    receipt_material_dispatch(material),
                    forbidden_port_bytes,
                    reverse_fields=reverse_fields,
                )
            )
            options = {}
            if clock is not None:
                options["clock"] = clock
            report = capture_fixture(
                plan_path,
                primary.url,
                output,
                anchor_rpc_env=(f"{source_id}=ANCHOR_RPC",),
                environment={"ANCHOR_RPC": anchor.url},
                wall_clock=lambda: self.observed_at(material),
                **options,
            )
            return report, tuple(primary.requests), tuple(anchor.requests)

    def assert_no_capture_artifacts(self, root, output):
        self.assertFalse(output.exists())
        self.assertEqual(list(root.glob(f".{output.name}.lazarus-*")), [])

    def test_short_query_credential_is_refused_before_receipt_capture(self):
        material = self.material()
        base = receipt_material_dispatch(material)

        def primary_dispatch(method, params, server):
            result = base(method, params, server)
            if method == "eth_getBlockByNumber" and isinstance(result, dict):
                result = copy.deepcopy(result)
                result["providerNote"] = "abc"
            return result

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(primary_dispatch))
            anchor = stack.enter_context(FakeRpc(base))
            plan = root / "receipt-plan.json"
            dump(plan, material["plan"])
            output = root / "fixture"
            source_id = material["plan"]["anchor_sources"][0]["source_id"]
            with self.assertRaisesRegex(ResourceLimitError, "provider mapping"):
                capture_fixture(
                    plan,
                    primary.url + "?token=abc",
                    output,
                    anchor_rpc_env=(f"{source_id}=ANCHOR_RPC",),
                    environment={"ANCHOR_RPC": anchor.url},
                    wall_clock=lambda: self.observed_at(material),
                )
            self.assertEqual(primary.requests, [])
            self.assertEqual(anchor.requests, [])
            self.assert_no_capture_artifacts(root, output)

    def test_short_digest_component_is_refused_before_receipt_capture(self):
        material = self.material()
        base = receipt_material_dispatch(material)

        def primary_dispatch(method, params, server):
            result = base(method, params, server)
            if method == "eth_getBlockByNumber" and isinstance(result, dict):
                result = copy.deepcopy(result)
                result["providerNote"] = "abc"
            return result

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            primary = stack.enter_context(FakeRpc(primary_dispatch))
            anchor = stack.enter_context(FakeRpc(base))
            plan = root / "receipt-plan.json"
            dump(plan, material["plan"])
            output = root / "fixture"
            source_id = material["plan"]["anchor_sources"][0]["source_id"]
            observed_error = None
            try:
                capture_fixture(
                    plan,
                    primary.url,
                    output,
                    headers={
                        "Authorization": (
                            'Digest nonce="abc", realm="longrealm"'
                        )
                    },
                    anchor_rpc_env=(f"{source_id}=ANCHOR_RPC",),
                    environment={"ANCHOR_RPC": anchor.url},
                    wall_clock=lambda: self.observed_at(material),
                )
            except Exception as error:
                observed_error = error
            self.assertIsInstance(observed_error, ResourceLimitError)
            self.assertRegex(str(observed_error), "provider mapping")
            self.assertEqual(primary.requests, [])
            self.assertEqual(anchor.requests, [])
            self.assert_no_capture_artifacts(root, output)

    def test_plan_v3_recaptures_the_fixed_consensus_witness(self):
        material = support.receipt_capture_material()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "fixture"
            report, primary_requests, _ = self.capture_material(
                material,
                root,
                output,
            )
            self.assertEqual(
                report["fixture_digest"],
                "a88218e27b979a67941bd66f04eec9e0d1208178697c0c3f59a245f22dba0eec",
            )
            expected_files = sorted(
                path.name
                for path in support.RECEIPT_PROOF_FIXTURE.iterdir()
                if path.is_file()
            )
            self.assertEqual(sorted(path.name for path in output.iterdir()), expected_files)
            for name in expected_files:
                self.assertEqual(
                    (output / name).read_bytes(),
                    (support.RECEIPT_PROOF_FIXTURE / name).read_bytes(),
                    name,
                )
            block_calls = [
                request
                for request in primary_requests
                if request["method"] == "eth_getBlockReceipts"
            ]
            self.assertEqual(
                [request["params"] for request in block_calls],
                [[material["plan"]["block"]["hash"]]],
            )
            self.assertFalse(
                any(
                    request["method"].lower().startswith(("debug_", "trace_"))
                    for request in primary_requests
                )
            )
            proof_calls = [
                request
                for request in primary_requests
                if request["method"] == "eth_getProof"
            ]
            self.assertTrue(proof_calls)
            self.assertTrue(
                all(isinstance(request["params"][-1], dict) for request in proof_calls)
            )

    def test_only_plan_v3_can_make_exactly_one_block_receipts_call(self):
        extra = self.material()["plan"]
        extra["requests"].append(
            {
                "name": "second-block-receipts",
                "method": "eth_getBlockReceipts",
                "params": [extra["block"]["number"]],
                "required": True,
                "evidence": "recorded-rpc",
            }
        )
        with self.assertRaisesRegex(FormatError, "exactly one"):
            _validate_capture_plan(extra)

        legacy = support.anchored_fixture_material(("archive-a",))["plan"]
        legacy["limits"]["max_elapsed_seconds"] = 10
        legacy["requests"].append(
            {
                "name": "legacy-block-receipts",
                "method": "eth_getBlockReceipts",
                "params": [legacy["block"]["hash"]],
                "required": True,
                "evidence": "recorded-rpc",
            }
        )
        with self.assertRaisesRegex(FormatError, "requires plan-v3"):
            _validate_capture_plan(legacy)

    def test_cli_emits_one_safe_terminal_result_and_offline_output(self):
        material = support.receipt_capture_material()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        with ExitStack() as stack:
            root = Path(temporary.name)
            output = root / "fixture"
            primary = stack.enter_context(FakeRpc(receipt_material_dispatch(material)))
            anchor = stack.enter_context(FakeRpc(receipt_material_dispatch(material)))
            primary_marker = "primary-step3-marker"
            anchor_marker = "anchor-step3-marker"
            environment = dict(os.environ)
            environment["STEP3_ANCHOR_RPC"] = f"{anchor.url}?token={anchor_marker}"
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "capture",
                    "--plan",
                    str(support.RECEIPT_CAPTURE_FIXTURE / "plan.json"),
                    "--rpc-url",
                    f"{primary.url}?token={primary_marker}",
                    "--anchor-rpc-env",
                    "publicnode=STEP3_ANCHOR_RPC",
                    "--out",
                    str(output),
                ],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stderr, "")
            self.assertEqual(len(result.stdout.splitlines()), 1)
            event = loads(result.stdout)
            for secret in (
                primary_marker,
                anchor_marker,
                primary.url,
                anchor.url,
            ):
                self.assertNotIn(secret, result.stdout + result.stderr)
        with mock.patch("socket.socket", side_effect=AssertionError("network forbidden")):
            report = verify_fixture(output)
        self.assertEqual(event["schema"], "lazarus-capture-terminal/v1")
        self.assertEqual(event["event"], "lazarus.capture.completed")
        self.assertEqual(event["stage"], "fixture-finalised")
        self.assertEqual(event["fixture_digest"], report["fixture_digest"])
        self.assertEqual(
            event["correlation_id"],
            "lazarus-capture:" + hashlib.sha256(dumps(material["plan"])).hexdigest(),
        )
        self.assertEqual(event["block"]["hash"], material["plan"]["block"]["hash"])
        self.assertEqual(
            event["recorded_target_selector"]["value"],
            material["plan"]["requests"][2]["params"][0],
        )
        self.assertEqual(
            event["recorded_target_selector"]["evidence"], "recorded_rpc"
        )
        self.assertEqual(event["recorded_target_selector"]["transaction_index"], "0xbf")
        self.assertEqual(event["counts"]["recorded_rpc"], 5)
        self.assertEqual(event["counts"]["anchor_records"], 1)
        self.assertEqual(event["counts"]["receipts"], 224)
        self.assertEqual(event["counts"]["selected_logs"], 5)
        self.assertEqual(event["counts"]["receipt_trie_proved"], 2)
        self.assertEqual(event["counts"]["header_transactions"], 224)
        self.assertEqual(event["counts"]["returned_receipts"], 224)
        self.assertEqual(event["counts"]["encoded_receipts"], 224)
        self.assertEqual(event["versions"]["plan"], 3)
        self.assertEqual(event["versions"]["manifest"], 2)
        self.assertEqual(event["versions"]["receipt_witness"], 1)
        self.assertEqual(
            event["roots"]["expected_receipts_root"],
            event["roots"]["computed_receipts_root"],
        )
        proved = event["relation_scope"]["receipt_trie_proved"]
        self.assertEqual(
            proved,
            [
                "consensus_receipt_payload_at_trie_index",
                "consensus_log_projection",
            ],
        )
        self.assertFalse(any("transaction_hash" in claim for claim in proved))
        self.assertEqual(
            event["relation_scope"]["transaction_hash_attribution"], "recorded_rpc"
        )
        terminal_keys = set()

        def collect_keys(value):
            if isinstance(value, dict):
                terminal_keys.update(value)
                for item in value.values():
                    collect_keys(item)
            elif isinstance(value, list):
                for item in value:
                    collect_keys(item)

        collect_keys(event)
        self.assertTrue(
            {"url", "params", "outcome", "result", "log_data"}.isdisjoint(
                terminal_keys
            )
        )

    def test_cli_emits_one_safe_mapping_failure_result(self):
        environment = dict(os.environ)
        environment.pop("LAZARUS_STEP3_MISSING_ANCHOR", None)
        plan = load(support.RECEIPT_CAPTURE_FIXTURE / "plan.json")
        marker = hashlib.sha256(dumps(plan)).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "fixture"
            result = subprocess.run(
                [
                    sys.executable,
                    str(support.SCRIPTS / "lazarus.py"),
                    "capture",
                    "--plan",
                    str(support.RECEIPT_CAPTURE_FIXTURE / "plan.json"),
                    "--rpc-url",
                    f"https://primary.invalid/?token={marker}",
                    "--anchor-rpc-env",
                    "publicnode=LAZARUS_STEP3_MISSING_ANCHOR",
                    "--out",
                    str(output),
                ],
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertEqual(len(result.stderr.splitlines()), 1)
        self.assertTrue(result.stderr.startswith("{"), result.stderr)
        event = loads(result.stderr)
        self.assertEqual(event["schema"], "lazarus-capture-terminal/v1")
        self.assertEqual(event["event"], "lazarus.capture.failed")
        self.assertEqual(event["stage"], "anchor-mapping")
        self.assertEqual(event["failure"], "format")
        self.assertEqual(event["counts"]["rpc_requests"], 0)
        self.assertEqual(event["counts"]["receipt_trie_proved"], 0)
        self.assertEqual(
            event["recorded_target_selector"]["evidence"], "recorded_rpc"
        )
        self.assertIsNone(event["correlation_id"])
        self.assertNotIn(marker, result.stderr)

    def test_failure_terminal_redacts_a_provider_secret_identity_collision(self):
        material = self.material()
        source_id = material["plan"]["anchor_sources"][0]["source_id"]
        identity_secret = material["plan"]["block"]["hash"]
        correlation_secret = hashlib.sha256(dumps(material["plan"])).hexdigest()
        fallback = receipt_material_dispatch(material)

        def dispatch(method, params, server):
            if method == "eth_getBlockReceipts":
                return None
            return fallback(method, params, server)

        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            root = Path(directory)
            plan_path = root / "receipt-plan.json"
            dump(plan_path, material["plan"])
            output = root / "fixture"
            primary = stack.enter_context(FakeRpc(dispatch))
            anchor = stack.enter_context(
                FakeRpc(receipt_material_dispatch(material))
            )
            terminal_context = {}
            primary_url = f"{primary.url}/{identity_secret}/{correlation_secret}"
            secrets = provider_secret_union(
                ((primary_url, None), (anchor.url, None))
            )
            with self.assertRaisesRegex(IntegrityError, "not an array") as raised:
                capture_fixture(
                    plan_path,
                    primary_url,
                    output,
                    anchor_rpc_env=(f"{source_id}=ANCHOR_RPC",),
                    environment={"ANCHOR_RPC": anchor.url},
                    wall_clock=lambda: self.observed_at(material),
                    terminal_context=terminal_context,
                )
            event = capture_failure_terminal_result(
                terminal_context, raised.exception
            )
            self.assertIsNotNone(event)
            try:
                assert_no_secret_bytes(
                    dumps(event), secrets, label="capture failure terminal result"
                )
            except IntegrityError as error:
                secret_scan_error = error
            else:
                secret_scan_error = None
            self.assertIsNone(secret_scan_error)
            self.assertIsNone(event["block"]["hash"])
            self.assertIsNone(event["correlation_id"])
            self.assert_no_capture_artifacts(root, output)

    def test_provider_object_order_does_not_change_any_fixture_byte(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = root / "first"
            second = root / "second"
            first_report, _, _ = self.capture_material(material, root, first)
            second_report, _, _ = self.capture_material(
                material, root, second, reverse_fields=True
            )
            self.assertEqual(first_report["fixture_digest"], second_report["fixture_digest"])
            self.assertEqual(
                sorted(path.name for path in first.iterdir()),
                sorted(path.name for path in second.iterdir()),
            )
            for path in first.iterdir():
                self.assertEqual(path.read_bytes(), (second / path.name).read_bytes())

    def test_coherent_recorded_hash_rewrite_changes_only_recorded_identity(self):
        original = self.material()
        rewritten = copy.deepcopy(original)
        replacement = support.hash32("99")
        support.rewrite_recorded_target_hash(rewritten, replacement)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original_output = root / "original"
            rewritten_output = root / "rewritten"
            original_report, _, _ = self.capture_material(
                original, root, original_output
            )
            rewritten_report, _, _ = self.capture_material(
                rewritten, root, rewritten_output
            )
            self.assertNotEqual(
                original_report["fixture_digest"], rewritten_report["fixture_digest"]
            )
            self.assertEqual(
                (original_output / "receipt-witness.json").read_bytes(),
                (rewritten_output / "receipt-witness.json").read_bytes(),
            )
            self.assertEqual(
                original_report["receipt_trie_proved"]["computed_root"],
                rewritten_report["receipt_trie_proved"]["computed_root"],
            )
            terminal = rewritten_report["terminal_result"]
            self.assertEqual(terminal["recorded_target_selector"]["value"], replacement)
            self.assertEqual(
                terminal["relation_scope"]["transaction_hash_attribution"],
                "recorded_rpc",
            )

    def test_one_source_hash_rewrite_refuses_without_proof_or_stage(self):
        material = self.material()
        relation = material["plan"]["receipt_witness"]
        index = int(relation["target_transaction_index"], 16)
        records = {record["name"]: record for record in material["rpc_records"]}
        records[relation["block_receipts_request"]]["outcome"]["result"][index][
            "transactionHash"
        ] = support.hash32("99")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "fixture"
            with self.assertRaisesRegex(IntegrityError, "transaction hash disagreement"):
                self.capture_material(material, root, output)
            self.assert_no_capture_artifacts(root, output)

    def test_malformed_incomplete_and_failed_receipt_responses_leave_nothing(self):
        cases = {}
        base_material = self.material()
        relation = base_material["plan"]["receipt_witness"]
        block_name = relation["block_receipts_request"]
        records = {record["name"]: record for record in base_material["rpc_records"]}
        original = records[block_name]["outcome"]["result"]
        cases["null"] = None
        cases["rpc-error"] = RpcError(
            -32000, "provider-body-secret", {"url": "provider-url-secret"}
        )
        cases["missing"] = copy.deepcopy(original[:-1])
        cases["extra"] = copy.deepcopy(original + [original[-1]])
        duplicate = copy.deepcopy(original)
        duplicate[1] = copy.deepcopy(duplicate[0])
        cases["duplicate"] = duplicate
        cases["reordered"] = list(reversed(copy.deepcopy(original)))
        non_object = copy.deepcopy(original)
        non_object[0] = None
        cases["non-object"] = non_object

        for label, result in cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                material = self.material()
                fallback = receipt_material_dispatch(material)

                def dispatch(method, params, server, *, result=result):
                    if method == "eth_getBlockReceipts":
                        return copy.deepcopy(result)
                    return fallback(method, params, server)

                root = Path(directory)
                output = root / "fixture"
                with self.assertRaises((CaptureError, IntegrityError, FormatError)) as raised:
                    self.capture_material(
                        material, root, output, dispatch=dispatch
                    )
                diagnostic = str(raised.exception)
                self.assertNotIn("provider-body-secret", diagnostic)
                self.assertNotIn("provider-url-secret", diagnostic)
                self.assert_no_capture_artifacts(root, output)

    def test_receipt_collection_field_log_and_topic_caps_leave_nothing(self):
        patches = (
            ("MAX_RECEIPTS", 1, "receipt count"),
            ("MAX_RECEIPT_FIELDS", 1, "field count"),
            ("MAX_LOGS", 0, "log count"),
            ("MAX_RECEIPT_LOG_FIELDS", 1, "field count"),
            ("MAX_TOPICS", 0, "topic count"),
        )
        for name, maximum, message in patches:
            with self.subTest(cap=name), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "fixture"
                with mock.patch(f"lazarus_lib.capture.{name}", maximum):
                    with self.assertRaisesRegex(ResourceLimitError, message):
                        self.capture_material(self.material(), root, output)
                self.assert_no_capture_artifacts(root, output)

    def test_plan_v3_request_response_total_and_time_budgets_leave_nothing(self):
        class AdvancingClock:
            def __init__(self):
                self.value = -1

            def __call__(self):
                self.value += 1
                return self.value

        cases = []
        request_limited = self.material()
        request_limited["plan"]["limits"]["max_requests"] = len(
            request_limited["plan"]["requests"]
        )
        cases.append(("request", request_limited, None))
        component_limited = self.material()
        plan_size = len(dumps(component_limited["plan"])) + 1
        component_limited["plan"]["limits"]["max_component_bytes"] = plan_size
        cases.append(("component", component_limited, None))
        total_limited = self.material()
        total_limited["plan"]["limits"]["max_total_bytes"] = (
            len(dumps(total_limited["plan"])) + 1
        )
        cases.append(("total", total_limited, None))
        time_limited = self.material()
        time_limited["plan"]["limits"]["max_elapsed_seconds"] = 1
        cases.append(("time", time_limited, AdvancingClock()))

        for label, material, clock in cases:
            with self.subTest(limit=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                output = root / "fixture"
                with self.assertRaises(ResourceLimitError):
                    self.capture_material(
                        material, root, output, clock=clock
                    )
                self.assert_no_capture_artifacts(root, output)

    def test_elapsed_budget_is_rechecked_after_secret_scan(self):
        class ControlledClock:
            value = 0

            def __call__(self):
                return self.value

        clock = ControlledClock()
        material = self.material()
        material["plan"]["limits"]["max_elapsed_seconds"] = 1

        def slow_scan(*args, **kwargs):
            scan_fixture_secrets(*args, **kwargs)
            clock.value = 2

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture.assert_no_secrets", side_effect=slow_scan
            ):
                with self.assertRaisesRegex(ResourceLimitError, "seconds"):
                    self.capture_material(
                        material,
                        root,
                        output,
                        clock=clock,
                    )
            self.assert_no_capture_artifacts(root, output)

    def test_terminal_secret_scan_receives_the_shared_elapsed_callback(self):
        material = self.material()
        observed_callbacks = []

        def terminal_scan(data, secrets, *, label, check_time=None):
            observed_callbacks.append(check_time)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture.assert_no_secret_bytes",
                side_effect=terminal_scan,
            ):
                self.capture_material(material, root, output)
            self.assertEqual(len(observed_callbacks), 1)
            self.assertTrue(callable(observed_callbacks[0]))

    def test_plan_v3_preserves_an_existing_destination_before_network(self):
        material = self.material()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "receipt-plan.json"
            dump(plan_path, material["plan"])
            output = root / "fixture"
            output.mkdir()
            marker = output / "marker"
            marker.write_text("preserve\n", encoding="utf-8")

            def forbidden_client(*args, **kwargs):
                raise AssertionError("existing output refusal must precede network setup")

            with self.assertRaisesRegex(PathError, "already exists"):
                capture_fixture(
                    plan_path,
                    "https://primary.invalid",
                    output,
                    anchor_rpc_env=("archive-a=ANCHOR_RPC",),
                    environment={"ANCHOR_RPC": "https://anchor.invalid"},
                    client_factory=forbidden_client,
                )
            self.assertEqual(marker.read_text(encoding="utf-8"), "preserve\n")
            self.assertEqual(list(root.glob(".fixture.lazarus-*")), [])

    def test_plan_v3_interruption_after_staging_removes_the_stage(self):
        material = self.material()

        class UnusedClient:
            def __init__(self, *args, **kwargs):
                pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "receipt-plan.json"
            dump(plan_path, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture._capture_into",
                side_effect=KeyboardInterrupt("simulated interruption"),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    capture_fixture(
                        plan_path,
                        "https://primary.invalid",
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_RPC",),
                        environment={"ANCHOR_RPC": "https://anchor.invalid"},
                        client_factory=UnusedClient,
                    )
            self.assert_no_capture_artifacts(root, output)

    def test_plan_v3_stage_creation_failure_creates_no_artifact(self):
        material = self.material()

        class UnusedClient:
            def __init__(self, *args, **kwargs):
                pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            plan_path = root / "receipt-plan.json"
            dump(plan_path, material["plan"])
            output = root / "fixture"
            with mock.patch(
                "lazarus_lib.capture.tempfile.mkdtemp",
                side_effect=OSError("simulated staging interruption"),
            ):
                with self.assertRaisesRegex(CaptureError, "staging"):
                    capture_fixture(
                        plan_path,
                        "https://primary.invalid",
                        output,
                        anchor_rpc_env=("archive-a=ANCHOR_RPC",),
                        environment={"ANCHOR_RPC": "https://anchor.invalid"},
                        client_factory=UnusedClient,
                    )
            self.assert_no_capture_artifacts(root, output)


if __name__ == "__main__":
    unittest.main()
