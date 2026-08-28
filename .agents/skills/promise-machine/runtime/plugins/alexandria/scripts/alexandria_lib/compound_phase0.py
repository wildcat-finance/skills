"""Capture and offline checking for the bounded Compound III Phase 0 corpus."""

from __future__ import annotations

import os
from pathlib import Path
import hashlib
import re
import shutil
import tempfile
import time
import urllib.error
import urllib.request

from .canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes, load_raw_json
from .compound_registry import (
    COMET_COMMIT,
    deployment_source_bytes,
    registry_bytes,
    validate_registry,
)
from .errors import AlexandriaError
from .paths import read_confined_file
from .release import MAX_RAW_COMPONENT_BYTES, ingest, verify


CORPUS_FORMAT = "alexandria-compound-v3-corpus/v1"
CORPUS_SHA256 = "fdafb894bc212bc23133ddf80a8ad11384332e2ac6fba871c251a8a082fe0880"
PROXY = "0xc3d688b66703497daa19211eedff47f25384cdc3"
USER_BASIC_SLOT = 5
MAX_REQUESTS = 48
MAX_PHASE0_JSON_NODES = 1_000_000
MAX_CAPTURE_SECONDS = 300
MAX_CAPTURE_BYTES = 128 * 1024 * 1024
WORD_RE = re.compile(r"^0x[0-9a-f]{64}$")
OLD_WITNESS = {
    "block_hash": "0xf56dbfce61b5f2ae9b0a7b25a4a2f8cb7c47f716db7abc4f64a0c8dcf914d1e8",
    "block_number": "0xeb2c89",
    "transaction_hash": "0x10a4ec0d64fc459c9945098601a8115c9268fd9a4742cae509ec15adaf1f9f03",
}
RECENT_WITNESS = {
    "block_hash": "0xb50117200075e10d2e1c489595c9c3ccb9b0585d7851fc2d26ea8c0b717f10ca",
    "block_number": "0x1892b65",
    "finalized_hash": "0x6c0c64f7fee455de134925db00f2f5c9b01710fa47d4d0dae7aaa86eaa35c8e2",
    "finalized_number": "0x1894b65",
    "transaction_hash": "0x8c02ef7830078c22e8221b91a77c757e95f7e373adcccf132fb128136f224ad3",
}
EXPECTED_METHODS = {
    "client-version": "web3_clientVersion",
    "chain-id": "eth_chainId",
    "finalized-block": "eth_getBlockByNumber",
    "trace-filter-probe-window": "trace_filter",
    "rpc-modules-unsupported": "rpc_modules",
}
for _label in ("old", "recent"):
    EXPECTED_METHODS.update({
        f"{_label}-block": "eth_getBlockByNumber",
        f"{_label}-transaction": "eth_getTransactionByHash",
        f"{_label}-receipt": "eth_getTransactionReceipt",
        f"{_label}-trace-filter": "trace_filter",
        f"{_label}-flat-trace": "trace_transaction",
        f"{_label}-call-trace": "debug_traceTransaction",
        f"{_label}-prestate-trace": "debug_traceTransaction",
        f"{_label}-opcode-trace": "debug_traceTransaction",
        f"{_label}-proxy-code": "eth_getCode",
        f"{_label}-slot-zero": "eth_getStorageAt",
        f"{_label}-base-token": "eth_call",
        f"{_label}-implementation-slot": "eth_getStorageAt",
        f"{_label}-implementation-code": "eth_getCode",
    })
EXPECTED_METHODS["recent-user-basic-slot"] = "eth_getStorageAt"


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise AlexandriaError("Compound RPC endpoint redirected")


def _load(path: Path, label: str):
    data = read_confined_file(path.parent, path.name, label, max_bytes=MAX_CONTROL_BYTES)
    return load_bytes(data, label)


def _request_bytes(identifier: int, method: str, params) -> bytes:
    return canonical_bytes({"id": identifier, "jsonrpc": "2.0", "method": method, "params": params})


def _coverage_gap():
    return {
        "collections": [],
        "gaps": ["bounded method-proof corpus; no market interval completeness is claimed"],
        "record_count": 0,
        "status": "partial",
        "unsupported_collections": ["full-market-history"],
    }


def _component(name: str, path: str, role: str, media_type="application/json"):
    return {
        "access": "public",
        "media_type": media_type,
        "name": name,
        "path": path,
        "redistribution": "permitted",
        "role": role,
    }


def _capture_declaration(name: str, observed_at: str):
    return {
        "chain": "eip155:1",
        "component": name,
        "coverage": _coverage_gap(),
        "evidence_class": "recorded-rpc",
        "id": name,
        "scope": {
            "deployment": "ethereum-usdc-comet",
            "finality": "provider-reported",
            "interval": {"kind": "snapshot", "observed_at": observed_at},
            "kind": "full-dataset",
        },
        "source": {
            "kind": "json-rpc",
            "locator_class": "provider-endpoint",
            "reference": "public Hinterlight Ethereum endpoint; URL and transport headers omitted",
        },
        "venue": "compound-v3",
    }


def validate_corpus(corpus) -> None:
    required = {"format", "observed_at", "registry_commit", "proxy", "old", "recent", "requests"}
    if not isinstance(corpus, dict) or set(corpus) != required:
        raise AlexandriaError("Compound corpus has an unknown shape")
    if corpus["format"] != CORPUS_FORMAT or corpus["registry_commit"] != COMET_COMMIT:
        raise AlexandriaError("Compound corpus pin does not match")
    if not isinstance(corpus["proxy"], str) or corpus["proxy"].lower() != PROXY:
        raise AlexandriaError("Compound corpus proxy does not match Ethereum USDC Comet")
    if corpus["old"] != OLD_WITNESS or corpus["recent"] != RECENT_WITNESS:
        raise AlexandriaError("Compound corpus transaction set does not match Phase 0")
    if corpus["observed_at"] != "2026-08-17T12:57:59Z":
        raise AlexandriaError("Compound corpus observation time does not match Phase 0")
    requests = corpus["requests"]
    if not isinstance(requests, list) or not requests or len(requests) > MAX_REQUESTS:
        raise AlexandriaError("Compound corpus request count is invalid")
    names = []
    for index, item in enumerate(requests, 1):
        if not isinstance(item, dict) or set(item) not in (
            {"name", "method", "params"},
            {"name", "method", "params", "expected_error_code"},
        ):
            raise AlexandriaError("Compound corpus request has an unknown shape")
        name = item["name"]
        if not isinstance(name, str) or not name or not all(c.islower() or c.isdigit() or c == "-" for c in name):
            raise AlexandriaError("Compound corpus request name is invalid")
        if not isinstance(item["method"], str) or not isinstance(item["params"], list):
            raise AlexandriaError("Compound corpus request method or params are invalid")
        if "expected_error_code" in item and not isinstance(item["expected_error_code"], int):
            raise AlexandriaError("Compound expected error code must be an integer")
        names.append(name)
        if index != len(names):
            raise AlexandriaError("Compound request ordering is invalid")
    if len(names) != len(set(names)):
        raise AlexandriaError("Compound corpus request names must be unique")
    if names != list(EXPECTED_METHODS):
        raise AlexandriaError("Compound corpus request set or ordering does not match Phase 0")
    for item in requests:
        if item["method"] != EXPECTED_METHODS[item["name"]]:
            raise AlexandriaError(f"Compound request {item['name']} uses the wrong method")
    unsupported = next(item for item in requests if item["name"] == "rpc-modules-unsupported")
    if unsupported.get("expected_error_code") != -32601:
        raise AlexandriaError("Compound rpc_modules refusal code does not match")
    if hashlib.sha256(canonical_bytes(corpus)).hexdigest() != CORPUS_SHA256:
        raise AlexandriaError("Compound corpus bytes do not match Phase 0")


def capture(
    registry_path: Path,
    corpus_path: Path,
    comet_repository: Path,
    output: Path,
    endpoint_env="ALEXANDRIA_COMPOUND_RPC_URL",
) -> None:
    """Capture the fixed corpus into a source directory; never persist the endpoint."""
    registry = _load(registry_path.absolute(), "Compound registry")
    validate_registry(registry)
    registry_data = canonical_bytes(registry)
    if registry_data != registry_bytes(comet_repository):
        raise AlexandriaError("Compound registry bytes do not match the pinned repository")
    corpus = _load(corpus_path.absolute(), "Compound corpus")
    validate_corpus(corpus)
    endpoint = os.environ.get(endpoint_env, "")
    if not endpoint.startswith("https://") or any(character.isspace() for character in endpoint):
        raise AlexandriaError(f"{endpoint_env} must name an HTTPS endpoint")
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise AlexandriaError("capture output already exists")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        (temporary / "requests").mkdir()
        (temporary / "responses").mkdir()
        (temporary / "upstream").mkdir()
        (temporary / "registry.json").write_bytes(registry_data)
        corpus_data = canonical_bytes(corpus)
        (temporary / "corpus.json").write_bytes(corpus_data)
        total_bytes = len(registry_data) + len(corpus_data)
        opener = urllib.request.build_opener(_NoRedirect)
        started = time.monotonic()
        components = [
            _component("corpus", "corpus.json", "capture-contract"),
            _component("registry", "registry.json", "deployment-registry"),
        ]
        captures = [
            _capture_declaration("corpus", corpus["observed_at"]),
            _capture_declaration("registry", corpus["observed_at"]),
        ]
        for filename, data in deployment_source_bytes(comet_repository).items():
            total_bytes += len(data)
            if total_bytes > MAX_CAPTURE_BYTES:
                raise AlexandriaError("Compound capture exceeded the total byte limit")
            relative = f"upstream/{filename}"
            (temporary / relative).write_bytes(data)
            name = "upstream-" + filename.replace(".", "-")
            components.append(_component(name, relative, "pinned-deployment-source", "text/plain"))
            captures.append(_capture_declaration(name, corpus["observed_at"]))
        for identifier, declaration in enumerate(corpus["requests"], 1):
            if time.monotonic() - started > MAX_CAPTURE_SECONDS:
                raise AlexandriaError("Compound capture exceeded the elapsed-time limit")
            name = declaration["name"]
            request_data = _request_bytes(identifier, declaration["method"], declaration["params"])
            total_bytes += len(request_data)
            if total_bytes > MAX_CAPTURE_BYTES:
                raise AlexandriaError("Compound capture exceeded the total byte limit")
            request_path = temporary / "requests" / f"{name}.json"
            request_path.write_bytes(request_data)
            request = urllib.request.Request(
                endpoint,
                data=request_data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with opener.open(request, timeout=25) as response:
                    if response.status != 200:
                        raise AlexandriaError(f"Compound RPC {name} returned HTTP {response.status}")
                    response_data = response.read(MAX_RAW_COMPONENT_BYTES + 1)
            except urllib.error.URLError as error:
                raise AlexandriaError(f"Compound RPC {name} transport failed") from error
            if len(response_data) > MAX_RAW_COMPONENT_BYTES:
                raise AlexandriaError(f"Compound RPC {name} exceeded the component byte limit")
            total_bytes += len(response_data)
            if total_bytes > MAX_CAPTURE_BYTES:
                raise AlexandriaError("Compound capture exceeded the total byte limit")
            if time.monotonic() - started > MAX_CAPTURE_SECONDS:
                raise AlexandriaError("Compound capture exceeded the elapsed-time limit")
            load_raw_json(
                response_data,
                f"Compound RPC {name}",
                max_bytes=MAX_RAW_COMPONENT_BYTES,
                max_nodes=MAX_PHASE0_JSON_NODES,
            )
            response_path = temporary / "responses" / f"{name}.json"
            response_path.write_bytes(response_data)
            for prefix, relative, role in (
                ("request", f"requests/{name}.json", "json-rpc-request"),
                ("response", f"responses/{name}.json", "json-rpc-response"),
            ):
                component_name = f"{prefix}-{name}"
                components.append(_component(component_name, relative, role))
                captures.append(_capture_declaration(component_name, corpus["observed_at"]))
        plan = {
            "captures": captures,
            "components": components,
            "format": "alexandria-capture-plan/v1",
            "release": {"created_at": corpus["observed_at"], "name": "compound-v3-phase0-v0"},
        }
        plan_data = canonical_bytes(plan)
        if total_bytes + len(plan_data) > MAX_CAPTURE_BYTES:
            raise AlexandriaError("Compound capture exceeded the total byte limit")
        (temporary / "capture-plan.json").write_bytes(plan_data)
        os.replace(temporary, output)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise


def build(input_root: Path, output: Path) -> str:
    """Ingest and semantically check before installing the release directory."""
    output = output.absolute()
    if output.is_symlink():
        raise AlexandriaError("Compound release output must not be a symlink")
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=f".{output.name}.phase0-", dir=output.parent))
    candidate = temporary_root / "release"
    try:
        release_id = ingest(input_root.absolute() / "capture-plan.json", candidate)
        check_phase0(candidate)
        if output.exists():
            if check_phase0(output)["release_id"] != release_id:
                raise AlexandriaError("Compound release output already contains different bytes")
            return release_id
        os.replace(candidate, output)
        return release_id
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)


def component_bytes(release_root: Path, manifest, name: str) -> bytes:
    matches = [item for item in manifest["components"] if item["name"] == name]
    if len(matches) != 1:
        raise AlexandriaError(f"Compound release component {name} is missing or duplicated")
    component = matches[0]
    return read_confined_file(
        release_root,
        component["object_path"],
        f"Compound release component {name}",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
    )


def load_phase0(release_root: Path):
    release_root = release_root.absolute()
    release_id = verify(release_root)
    manifest = load_bytes(
        read_confined_file(release_root, "manifest.json", "manifest", max_bytes=MAX_CONTROL_BYTES),
        "manifest",
    )
    corpus = load_bytes(component_bytes(release_root, manifest, "corpus"), "Compound corpus")
    registry = load_bytes(component_bytes(release_root, manifest, "registry"), "Compound registry")
    validate_corpus(corpus)
    validate_registry(registry)
    selected = next(
        item for item in registry["entries"]
        if item["network"] == "mainnet" and item["market"] == "usdc"
    )
    if selected["proxy"] != PROXY:
        raise AlexandriaError("Compound registry Ethereum USDC proxy does not match the corpus")
    metadata_by_name = {Path(item["path"]).name: item for item in selected["files"]}
    for filename in ("roots.json", "configuration.json", "deploy.ts", "relations.ts"):
        name = "upstream-" + filename.replace(".", "-")
        data = component_bytes(release_root, manifest, name)
        metadata = metadata_by_name[filename]
        if len(data) != metadata["bytes"] or hashlib.sha256(data).hexdigest() != metadata["sha256"]:
            raise AlexandriaError(f"Compound upstream {filename} does not match the registry")
    return release_id, manifest, corpus, registry


def _response(release_root: Path, manifest, declaration, identifier: int):
    name = declaration["name"]
    request = load_bytes(component_bytes(release_root, manifest, f"request-{name}"), f"request {name}")
    expected = load_bytes(_request_bytes(identifier, declaration["method"], declaration["params"]), f"expected request {name}")
    if request != expected:
        raise AlexandriaError(f"Compound request {name} does not match the corpus")
    response = load_raw_json(
        component_bytes(release_root, manifest, f"response-{name}"),
        f"response {name}",
        max_bytes=MAX_RAW_COMPONENT_BYTES,
        max_nodes=MAX_PHASE0_JSON_NODES,
        preserve_integers=True,
    )
    if not isinstance(response, dict) or response.get("jsonrpc") != "2.0" or response.get("id") != identifier:
        raise AlexandriaError(f"Compound response {name} envelope does not match")
    expected_error = declaration.get("expected_error_code")
    if expected_error is not None:
        if (
            "result" in response
            or not isinstance(response.get("error"), dict)
            or response["error"].get("code") != expected_error
        ):
            raise AlexandriaError(f"Compound response {name} did not return the expected error")
        return response
    if "error" in response or "result" not in response:
        raise AlexandriaError(f"Compound response {name} was not successful")
    return response


def _walk_calls(frame, path=()):
    if not isinstance(frame, dict):
        raise AlexandriaError("Compound call trace frame is not an object")
    yield path, frame
    children = frame.get("calls", [])
    if not isinstance(children, list):
        raise AlexandriaError("Compound call trace children are not a list")
    for index, child in enumerate(children):
        yield from _walk_calls(child, path + (index,))


def load_phase0_responses(release_root: Path, manifest, corpus) -> dict:
    return {
        declaration["name"]: _response(release_root, manifest, declaration, identifier)
        for identifier, declaration in enumerate(corpus["requests"], 1)
    }


def _hex_number(value, label):
    if not isinstance(value, str) or not value.startswith("0x"):
        raise AlexandriaError(f"{label} is not a hexadecimal quantity")
    try:
        return int(value, 16)
    except ValueError as error:
        raise AlexandriaError(f"{label} is not a hexadecimal quantity") from error


def _object(value, label):
    if not isinstance(value, dict):
        raise AlexandriaError(f"{label} is not an object")
    return value


def _runtime_code_digest(value, label):
    if not isinstance(value, str) or not value.startswith("0x") or len(value) <= 2 or len(value) % 2:
        raise AlexandriaError(f"{label} is not EVM runtime bytecode")
    try:
        return hashlib.sha256(bytes.fromhex(value[2:])).hexdigest()
    except ValueError as error:
        raise AlexandriaError(f"{label} is not hexadecimal EVM runtime bytecode") from error


def check_phase0(release_root: Path) -> dict:
    """Verify the Alexandria release and its fixed RPC relationships offline."""
    release_root = release_root.absolute()
    release_id, manifest, corpus, registry = load_phase0(release_root)
    responses = load_phase0_responses(release_root, manifest, corpus)
    ethereum_usdc = next(
        item for item in registry["entries"]
        if item["network"] == "mainnet" and item["market"] == "usdc"
    )
    if not str(responses["client-version"]["result"]).startswith("reth/"):
        raise AlexandriaError("Compound client identity is not the measured Reth variant")
    if responses["chain-id"]["result"] != "0x1":
        raise AlexandriaError("Compound chain id is not Ethereum mainnet")
    finalized = _object(responses["finalized-block"]["result"], "Compound finalized header")
    if finalized.get("number") != corpus["recent"]["finalized_number"] or finalized.get("hash") != corpus["recent"]["finalized_hash"]:
        raise AlexandriaError("Compound finalized header does not match the corpus boundary")

    receipt = {
        "client": responses["client-version"]["result"],
        "format": "alexandria-compound-v3-method-receipt/v1",
        "gates": {
            "archive_state": "passed",
            "nested_calls": "passed",
            "ordered_storage": "passed",
            "provider_reported_finality": "passed",
            "rpc_modules": "unsupported",
        },
        "registry_commit": COMET_COMMIT,
        "release_id": release_id,
        "transactions": [],
    }
    for label in ("old", "recent"):
        expected = corpus[label]
        block = _object(responses[f"{label}-block"]["result"], f"Compound {label} block")
        transaction = _object(responses[f"{label}-transaction"]["result"], f"Compound {label} transaction")
        transaction_receipt = _object(responses[f"{label}-receipt"]["result"], f"Compound {label} receipt")
        if block.get("number") != expected["block_number"] or block.get("hash") != expected["block_hash"]:
            raise AlexandriaError(f"Compound {label} block does not match the corpus")
        if (
            transaction.get("hash") != expected["transaction_hash"]
            or transaction.get("blockHash") != expected["block_hash"]
            or transaction.get("blockNumber") != expected["block_number"]
        ):
            raise AlexandriaError(f"Compound {label} transaction does not match its block")
        if (
            transaction_receipt.get("transactionHash") != expected["transaction_hash"]
            or transaction_receipt.get("blockHash") != expected["block_hash"]
            or transaction_receipt.get("blockNumber") != expected["block_number"]
            or transaction_receipt.get("status") != "0x1"
        ):
            raise AlexandriaError(f"Compound {label} receipt is not a successful matching receipt")
        flat = responses[f"{label}-trace-filter"]["result"]
        if not isinstance(flat, list) or any(not isinstance(item, dict) for item in flat):
            raise AlexandriaError(f"Compound {label} trace filter is not a frame list")
        proxy_frames = [
            item for item in flat
            if isinstance(item.get("action"), dict)
            and str(item["action"].get("to", "")).lower() == PROXY
            and item.get("transactionHash") == expected["transaction_hash"]
            and "error" not in item
        ]
        if not proxy_frames or not any(isinstance(item.get("traceAddress"), list) and item["traceAddress"] for item in proxy_frames):
            raise AlexandriaError(f"Compound {label} trace filter did not retain a nested proxy call")
        call_root = responses[f"{label}-call-trace"]["result"]
        calls = [
            (path, frame) for path, frame in _walk_calls(call_root)
            if str(frame.get("to", "")).lower() == PROXY and "error" not in frame
        ]
        if not calls or not any(path for path, _ in calls):
            raise AlexandriaError(f"Compound {label} call trace did not retain a nested successful proxy call")
        selectors = [str(frame.get("input", ""))[:10] for _, frame in calls]
        expected_selectors = ["0x90323177"] if label == "old" else ["0x90323177", "0x26441318"]
        if selectors != expected_selectors:
            raise AlexandriaError(f"Compound {label} call trace selectors do not match Phase 0")
        opcode = responses[f"{label}-opcode-trace"]["result"]
        if not isinstance(opcode, dict):
            raise AlexandriaError(f"Compound {label} opcode trace is not an object")
        struct_logs = opcode.get("structLogs") if isinstance(opcode, dict) else None
        if (
            opcode.get("failed") is not False
            or not isinstance(struct_logs, list)
            or any(not isinstance(item, dict) for item in struct_logs)
        ):
            raise AlexandriaError(f"Compound {label} opcode trace is incomplete")
        sstores = [index for index, item in enumerate(struct_logs) if item.get("op") == "SSTORE"]
        if not sstores or sstores != sorted(sstores):
            raise AlexandriaError(f"Compound {label} opcode trace has no ordered storage writes")
        prestate = responses[f"{label}-prestate-trace"]["result"]
        if (
            not isinstance(prestate, dict)
            or not isinstance(prestate.get("pre"), dict)
            or not isinstance(prestate.get("post"), dict)
        ):
            raise AlexandriaError(f"Compound {label} prestate diff is incomplete")
        implementation_slot = responses[f"{label}-implementation-slot"]["result"]
        if not isinstance(implementation_slot, str) or WORD_RE.fullmatch(implementation_slot) is None:
            raise AlexandriaError(f"Compound {label} implementation slot is not a word")
        implementation = "0x" + implementation_slot[-40:].lower()
        implementation_code = responses[f"{label}-implementation-code"]["result"]
        if implementation == "0x" + "0" * 40 or not isinstance(implementation_code, str) or len(implementation_code) <= 2:
            raise AlexandriaError(f"Compound {label} implementation binding is empty")
        proxy_code = responses[f"{label}-proxy-code"]["result"]
        if not isinstance(proxy_code, str) or len(proxy_code) <= 2:
            raise AlexandriaError(f"Compound {label} proxy code binding is empty")
        _runtime_code_digest(proxy_code, f"Compound {label} proxy code")
        base_token = responses[f"{label}-base-token"]["result"]
        if not isinstance(base_token, str) or "0x" + base_token[-40:].lower() != ethereum_usdc["base_token"]:
            raise AlexandriaError(f"Compound {label} base token does not match the registry")
        receipt["transactions"].append({
            "block_hash": expected["block_hash"],
            "block_number": str(_hex_number(expected["block_number"], f"{label} block")),
            "call_count": len(calls),
            "implementation": implementation,
            "implementation_code_sha256": _runtime_code_digest(
                implementation_code, f"Compound {label} implementation code"
            ),
            "label": label,
            "sstore_count": len(sstores),
            "transaction_hash": expected["transaction_hash"],
        })
    return receipt
