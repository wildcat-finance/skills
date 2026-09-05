"""Local deterministic JSON-RPC server for capture integration tests."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread
from typing import Any, Callable


@dataclass(frozen=True)
class RpcError:
    code: int
    message: str
    data: Any = None


class FakeRpc:
    def __init__(
        self,
        dispatch: Callable[[str, Any, "FakeRpc"], Any],
        *,
        reverse_batches: bool = False,
        raw_response: bytes | None = None,
        redirect_to: str | None = None,
        reverse_fields: bool = False,
        declared_length: str | None = None,
    ) -> None:
        self.dispatch = dispatch
        self.reverse_batches = reverse_batches
        self.raw_response = raw_response
        self.redirect_to = redirect_to
        self.reverse_fields = reverse_fields
        self.declared_length = declared_length
        self.requests: list[dict[str, Any]] = []
        self.headers: list[dict[str, str]] = []
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                if owner.redirect_to is not None:
                    self.send_response(307)
                    self.send_header("Location", owner.redirect_to)
                    self.end_headers()
                    return
                length = int(self.headers.get("Content-Length", "0"))
                payload = json.loads(self.rfile.read(length))
                owner.headers.append(dict(self.headers.items()))
                if owner.raw_response is not None:
                    raw = owner.raw_response
                else:
                    batch = payload if isinstance(payload, list) else [payload]
                    responses = [owner._answer(item) for item in batch]
                    if owner.reverse_batches and len(responses) > 1:
                        responses.reverse()
                    body: Any = responses if isinstance(payload, list) else responses[0]
                    raw = json.dumps(body, separators=(",", ":")).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header(
                    "Content-Length",
                    owner.declared_length
                    if owner.declared_length is not None
                    else str(len(raw)),
                )
                self.end_headers()
                self.wfile.write(raw)

            def log_message(self, format: str, *args: Any) -> None:
                return

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = Thread(target=self.server.serve_forever, daemon=True)

    @property
    def url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/rpc"

    def _answer(self, request: dict[str, Any]) -> dict[str, Any]:
        self.requests.append(request)
        outcome = self.dispatch(request["method"], request.get("params", []), self)
        if self.reverse_fields and not isinstance(outcome, RpcError):
            outcome = _reverse_fields(outcome)
        response = {"jsonrpc": "2.0", "id": request["id"]}
        if isinstance(outcome, RpcError):
            error = {"code": outcome.code, "message": outcome.message}
            if outcome.data is not None:
                error["data"] = outcome.data
            response["error"] = error
        else:
            response["result"] = outcome
        return response

    def __enter__(self) -> "FakeRpc":
        self.thread.start()
        return self

    def __exit__(self, *exc: Any) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def material_dispatch(material: dict[str, Any], *, reject_hash_selectors: bool = False):
    def as_result(record: dict[str, Any]) -> dict[str, Any]:
        return {
            "address": record["address"],
            "accountProof": record["account_proof"],
            "balance": record["balance"],
            "codeHash": record["code_hash"],
            "nonce": record["nonce"],
            "storageHash": record["storage_hash"],
            "storageProof": [
                {"key": item["key"], "value": item["value"], "proof": item["proof"]}
                for item in reversed(record["storage_proof"])
            ],
        }

    # A plan may prove more than one account, so answer for the address that
    # was asked for and fall back to the first record for material that
    # carries only one.
    records = material["proof_records"]
    by_address = {record["address"].lower(): record for record in records}

    def chosen(params: Any) -> dict[str, Any]:
        if isinstance(params, list) and params and isinstance(params[0], str):
            record = by_address.get(params[0].lower())
            if record is not None:
                return record
        return records[0]

    def dispatch(method: str, params: Any, server: FakeRpc) -> Any:
        if method == "eth_chainId":
            return "0x1"
        if method == "eth_getBlockByNumber":
            return material["header"]["rpc_result"]
        if method in {"eth_getProof", "eth_getCode"}:
            selector = params[-1]
            if reject_hash_selectors and isinstance(selector, dict):
                return RpcError(-32602, "block object unsupported")
            record = chosen(params)
            return as_result(record) if method == "eth_getProof" else record["code"]
        return {"method": method, "params": params}

    return dispatch


def receipt_material_dispatch(material: dict[str, Any]):
    """Serve the fixed recorded calls, plus the capture-only state calls."""

    fallback = material_dispatch(material)

    def dispatch(method: str, params: Any, server: FakeRpc) -> Any:
        for record in material["rpc_records"]:
            if record["method"] != method or record["params"] != params:
                continue
            outcome = record["outcome"]
            if "error" in outcome:
                error = outcome["error"]
                return RpcError(error["code"], error["message"])
            return copy.deepcopy(outcome["result"])
        return fallback(method, params, server)

    return dispatch


def _reverse_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _reverse_fields(item)
            for key, item in reversed(tuple(value.items()))
        }
    if isinstance(value, list):
        return [_reverse_fields(item) for item in value]
    return value
