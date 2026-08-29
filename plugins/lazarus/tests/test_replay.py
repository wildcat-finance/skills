"""Verified replay matches exact canonical requests and stable misses."""

from pathlib import Path
import tempfile
import unittest

from lazarus_lib.records import make_rpc_record, read_rpc_records, request_key
from lazarus_lib.replay import (
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    MISS_ERROR,
    ReplayStore,
)

from . import support
from .test_verifier import write_fixture


def custom_material(method="eth_call", params=None, result=None):
    material = support.synthetic_fixture_material()
    params = (
        [{"data": "0x00", "to": support.address()}, "0x0"]
        if params is None
        else params
    )
    result = (
        {"array": ["0x0", "0x00", 0, None], "quantity": "0x0"}
        if result is None
        else result
    )
    request = {
        "name": "custom-read",
        "method": method,
        "params": params,
        "required": True,
        "evidence": "recorded-rpc",
    }
    material["plan"]["requests"] = [request]
    material["rpc_records"] = [
        make_rpc_record(
            method,
            params,
            required=True,
            evidence="recorded-rpc",
            result=result,
            name=request["name"],
        )
    ]
    return material


class ReplayTests(unittest.TestCase):
    def store(self, root: Path, material=None):
        write_fixture(root, material or custom_material())
        return ReplayStore.from_fixture(root)

    def test_request_object_and_param_object_key_order_do_not_matter(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(Path(directory))
            request = {
                "params": [
                    {"to": support.address(), "data": "0x00"},
                    "0x0",
                ],
                "method": "eth_call",
                "id": "caller",
                "jsonrpc": "2.0",
            }
            response = store.dispatch(request)
            self.assertEqual(response["id"], "caller")
            self.assertEqual(
                response["result"],
                {"array": ["0x0", "0x00", 0, None], "quantity": "0x0"},
            )

    def test_receipt_proof_fixture_replays_recorded_block_receipts_exactly(self):
        root = support.FIXTURES / "receipt-proof-v1"
        plan = support.load_json("tests/fixtures/receipt-proof-v1/plan.json")
        request = next(
            item
            for item in plan["requests"]
            if item["method"] == "eth_getBlockReceipts"
        )
        record = next(
            item
            for item in read_rpc_records(root / "rpc.jsonl")
            if item["method"] == "eth_getBlockReceipts"
        )
        response = ReplayStore.from_fixture(root).dispatch(
            {
                "jsonrpc": "2.0",
                "id": 383,
                "method": request["method"],
                "params": request["params"],
            }
        )
        self.assertEqual(
            response,
            {"jsonrpc": "2.0", "id": 383, **record["outcome"]},
        )
        self.assertEqual(len(response["result"]), 224)

    def test_exact_values_and_omitted_params_are_not_coerced(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(Path(directory))
            changed = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": [{"data": "0x0", "to": support.address()}, "0x0"],
            }
            self.assertEqual(store.dispatch(changed)["error"]["code"], MISS_ERROR)
            omitted = {"jsonrpc": "2.0", "id": 2, "method": "eth_call"}
            self.assertEqual(
                store.dispatch(omitted)["error"]["code"], INVALID_REQUEST
            )

    def test_integer_string_and_null_caller_ids_are_copied_exactly(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(Path(directory))
            base = custom_material()["plan"]["requests"][0]
            for identifier in (7, "seven", None):
                request = {
                    "jsonrpc": "2.0",
                    "id": identifier,
                    "method": base["method"],
                    "params": base["params"],
                }
                with self.subTest(identifier=identifier):
                    self.assertEqual(store.dispatch(request)["id"], identifier)

    def test_notifications_never_receive_success_or_error_responses(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(Path(directory))
            params = custom_material()["plan"]["requests"][0]["params"]
            for method in ("eth_call", "eth_getStorageAt", "eth_sendTransaction"):
                with self.subTest(method=method):
                    self.assertIsNone(
                        store.dispatch(
                            {"jsonrpc": "2.0", "method": method, "params": params}
                        )
                    )

    def test_miss_payload_is_stable_and_is_a_capture_plan_fragment(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(Path(directory))
            method = "eth_getStorageAt"
            params = [support.address(), support.slot("01"), "0x0"]
            response = store.dispatch(
                {"jsonrpc": "2.0", "id": 4, "method": method, "params": params}
            )
            key = request_key(method, params)
            self.assertEqual(
                response,
                {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "error": {
                        "code": -32070,
                        "message": "request is outside this Lazarus fixture",
                        "data": {
                            "method": method,
                            "params": params,
                            "capture_plan_fragment": {
                                "evidence": "recorded-rpc",
                                "method": method,
                                "name": f"replay-miss-{key[:12]}",
                                "params": params,
                                "required": True,
                            },
                        },
                    },
                },
            )

    def test_unsupported_and_write_methods_are_rejected_even_if_captured(self):
        with tempfile.TemporaryDirectory() as directory:
            store = self.store(Path(directory))
            unsupported = store.dispatch(
                {"jsonrpc": "2.0", "id": 1, "method": "unknown_read", "params": []}
            )
            self.assertEqual(unsupported["error"]["code"], METHOD_NOT_FOUND)
            moving_head = store.dispatch(
                {"jsonrpc": "2.0", "id": 2, "method": "eth_blockNumber", "params": []}
            )
            self.assertEqual(moving_head["error"]["code"], METHOD_NOT_FOUND)

        for method, params in (
            ("eth_sendRawTransaction", ["0xdead"]),
            ("eth_signTypedData_v4", [support.address(), {}]),
            ("debug_setHead", ["0x1"]),
            ("evm_mine", []),
        ):
            with (
                self.subTest(method=method),
                tempfile.TemporaryDirectory() as directory,
            ):
                material = custom_material(
                    method=method,
                    params=params,
                    result=support.hash32(),
                )
                store = self.store(Path(directory), material)
                response = store.dispatch(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": method,
                        "params": params,
                    }
                )
                self.assertEqual(response["error"]["code"], METHOD_NOT_FOUND)

    def test_results_and_the_outcome_index_are_immutable(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            store = self.store(root)
            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "eth_call",
                "params": custom_material()["plan"]["requests"][0]["params"],
            }
            first = store.dispatch(request)
            first["result"]["array"][0] = "changed"
            second = store.dispatch(request)
            self.assertEqual(second["result"]["array"][0], "0x0")
            with self.assertRaises(TypeError):
                store.outcomes[request_key(request["method"], request["params"])] = b"{}"


if __name__ == "__main__":
    unittest.main()
