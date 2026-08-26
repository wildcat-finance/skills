"""A fake archive RPC exercises the complete finite capture boundary."""

import copy
from contextlib import ExitStack
from datetime import datetime, timezone
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from lazarus_lib.canonical import dump
from lazarus_lib.capture import CaptureError, _atomic_no_replace, capture_fixture
from lazarus_lib.errors import FormatError, IntegrityError, PathError, ResourceLimitError
from lazarus_lib.records import read_anchor_records, read_rpc_records
from lazarus_lib.rpc import JsonRpcClient
from lazarus_lib.verifier import verify_fixture

from . import support
from .fake_rpc import FakeRpc, RpcError, material_dispatch


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


if __name__ == "__main__":
    unittest.main()
