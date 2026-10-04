"""Admit Wildcat raw bytes before interpreting their native logs."""

from collections import defaultdict
import importlib
import os
from pathlib import Path
import re
import stat
import sys

from .compound_witness import _bounded_file_bytes
from .core import TabulariumError, canonical_json, loads_json, sha256_bytes
from .wildcat_view import (
    CONTROLLER, DEPLOY, PINS, _address, _binding_v2, _hex, _journals,
    _path, _position, _shape, _terms,
)


MAX_INPUT_BYTES = 512 * 1024 * 1024
MAX_COMPONENT_BYTES = 64 * 1024 * 1024
MAX_RECORDS = 500_000
CONSTRUCTION_FORMAT = "tabularium-wildcat-construction/v1"
CONSTRUCTION_GAP = "constructed fixture; historical origin, interval epochs and runtime code are not established"
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")


def _api():
    scripts = Path(__file__).resolve().parents[3] / "alexandria" / "scripts"
    if not scripts.is_dir() or scripts.is_symlink():
        raise TabulariumError("Wildcat canonical releases require the sibling Alexandria plugin")
    names = (
        "usdc_interval", "alexandria_lib.release", "alexandria_lib.derivation",
        "alexandria_lib.errors",
    )
    sys.path.insert(0, str(scripts))
    try:
        modules = tuple(importlib.import_module(name) for name in names)
    except ImportError as error:
        raise TabulariumError("Alexandria raw verification API is unavailable") from error
    finally:
        sys.path.remove(str(scripts))
    # A preloaded sibling name must earn the same confinement as a new import.
    for name, module in tuple(sys.modules.items()):
        if name == "usdc_interval" or name == "alexandria_lib" or name.startswith("alexandria_lib."):
            source = getattr(module, "__file__", None)
            if not isinstance(source, str) or not Path(source).resolve().is_relative_to(scripts):
                raise TabulariumError("loaded Alexandria API is outside the sibling plugin")
    return modules


def _exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise TabulariumError(label + " has an unknown or incomplete shape")
    return value


def _physical_inventory(root):
    result, identities, total = {}, set(), 0
    for directory, subdirs, files in os.walk(root, followlinks=False):
        for name in subdirs:
            if (Path(directory) / name).is_symlink():
                raise TabulariumError("raw release contains a directory link")
        for name in files:
            path = Path(directory) / name
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise TabulariumError("raw release contains a linked or non-regular file")
            identity = (info.st_dev, info.st_ino)
            if identity in identities:
                raise TabulariumError("raw release files alias each other")
            identities.add(identity)
            limit = 2 * 1024 * 1024 if path.name == "manifest.json" else MAX_COMPONENT_BYTES
            data = _bounded_file_bytes(path, limit, "raw release file")
            total += len(data)
            if total > MAX_INPUT_BYTES + 2 * 1024 * 1024:
                raise TabulariumError("raw release exceeds the input byte budget")
            result[path.relative_to(root).as_posix()] = {"sha256": sha256_bytes(data), "bytes": len(data)}
    return dict(sorted(result.items()))


def _ref(components, captures, component, pointer, evidence_class="recorded"):
    return {
        "component": component,
        "component_sha256": components[component]["sha256"],
        "capture_id": captures[component]["id"],
        "evidence_class": evidence_class,
        "selector": pointer,
    }


def _uint(word, width, label):
    value = int.from_bytes(word)
    if value >= 1 << width:
        raise TabulariumError(label + " exceeds its concrete ABI integer width")
    return value


def constructor_parameters(venue, value):
    """Decode the complete selected constructor tuple, keeping V1 decimals absent."""
    data = _hex(value)
    if venue == "wildcat-v2":
        if len(data) != 19 * 32:
            raise TabulariumError("V2 constructor parameters are not nineteen words")
        words = [data[i:i + 32] for i in range(0, len(data), 32)]
        for index in (0, 6, 7, 8, 16, 17):
            _address(words[index])
        for index, width in ((1, 8), (9, 128), (10, 16), (11, 16), (12, 16), (13, 32), (14, 16), (15, 32)):
            _uint(words[index], width, "V2 constructor field")
        return {"asset": _address(words[0]), "borrower": _address(words[6]), "decimals": int.from_bytes(words[1])}
    if venue != "wildcat-v1" or len(data) < 32 + 16 * 32 or len(data) > 4096:
        raise TabulariumError("V1 constructor parameters exceed their tuple bounds")
    if int.from_bytes(data[:32]) != 32:
        raise TabulariumError("V1 constructor tuple offset is not canonical")
    body = data[32:]
    words = [body[i * 32:(i + 1) * 32] for i in range(16)]
    for index in (0, 3, 4, 5, 6, 14, 15):
        _address(words[index])
    for index, width in ((7, 128), (8, 16), (9, 16), (10, 16), (11, 32), (12, 16), (13, 32)):
        _uint(words[index], width, "V1 constructor field")
    end = 16 * 32
    for index in (1, 2):
        offset = int.from_bytes(words[index])
        if offset != end or offset + 32 > len(body):
            raise TabulariumError("V1 constructor string offset is not canonical")
        length = int.from_bytes(body[offset:offset + 32])
        end = offset + 32 + ((length + 31) // 32) * 32
        if length > 512 or end > len(body) or any(body[offset + 32 + length:end]):
            raise TabulariumError("V1 constructor string has invalid bounds or padding")
        try:
            body[offset + 32:offset + 32 + length].decode("utf-8")
        except UnicodeDecodeError as error:
            raise TabulariumError("V1 constructor string is not UTF-8") from error
    if end != len(body):
        raise TabulariumError("V1 constructor parameters have trailing bytes")
    return {"asset": _address(words[0]), "borrower": _address(words[3]), "controller": _address(words[4]), "decimals": None}


def _constructor(venue, market, deployment, traces, expected_role, entries):
    event = deployment[0]
    candidates = []
    for trace, reference in traces:
        action, result = trace.get("action", {}), trace.get("result", {})
        if action.get("input") != "0x04032dbb" or action.get("from", "").lower() != market:
            continue
        target = action.get("to", "").lower()
        if entries.get(target, {}).get("role") != expected_role:
            raise TabulariumError("constructor parameters target has the wrong registered role")
        if (trace.get("type") != "call" or action.get("callType") != "staticcall"
                or "error" in trace or trace.get("blockHash") != event["blockHash"]
                or trace.get("transactionHash") != event["transactionHash"]):
            raise TabulariumError("constructor parameters call is not a matching successful staticcall")
        path = trace.get("traceAddress")
        if not isinstance(path, list) or any(type(part) is not int or part < 0 for part in path):
            raise TabulariumError("constructor trace path is malformed")
        ancestors = [parent for parent, _ in traces if len(parent.get("traceAddress", [])) < len(path)
                     and path[:len(parent.get("traceAddress", []))] == parent.get("traceAddress")]
        creates = [parent for parent in ancestors if parent.get("type") == "create"
                   and parent.get("result", {}).get("address", "").lower() == market]
        if len(creates) != 1 or any("error" in parent for parent in ancestors):
            raise TabulariumError("constructor call lacks one successful market creation ancestor")
        parameters = constructor_parameters(venue, result.get("output"))
        if parameters["asset"] != deployment[2]["asset"]:
            raise TabulariumError("constructor asset conflicts with MarketDeployed")
        if venue == "wildcat-v1" and (target != event["address"].lower() or parameters["controller"] != target):
            raise TabulariumError("V1 constructor controller conflicts with deployment")
        candidates.append({"values": parameters, "source": reference, "native": trace,
                           "evidence_class": "recorded-constructor-context"})
    if len(candidates) > 1:
        raise TabulariumError("ambiguous constructor parameters for market")
    return candidates[0] if candidates else None


def _real_context(plan, manifest, read, interval_api):
    from .wildcat_rules import abi_variant_for, VARIANTS

    venue = plan["venue"]
    registry = loads_json(read("registry"), "registry")
    epoch_table = loads_json(read("epoch-table"), "epoch-table")
    components = {item["name"]: item for item in manifest["components"]}
    captures = {item["component"]: item for item in manifest["captures"]}
    entries = {item["address"]: item for item in registry["entries"]}
    contexts = {}
    for index, item in enumerate(registry["entries"]):
        variant = abi_variant_for(venue, item["role"], item["name"], item["source_commit"])
        contexts[item["address"]] = {
            "role": item["role"], "asset": None,
            "abi_variant": variant,
            "concrete_contract": VARIANTS[variant]["contract"] if variant else None,
            "source": [{"class": "checked-registry-context", "reference": _ref(components, captures, "registry", f"/entries/{index}"), "native": item}],
        }
    logs = list(_journals(plan, manifest, read, interval_api, "logs"))
    attributions = epoch_table.get("log_attributions", [])
    if "log_attribution_parts" in epoch_table:
        for item in epoch_table["log_attribution_parts"]:
            part = loads_json(read(item["component"]), "log attribution part")
            attributions.extend(part["rows"])
    owners = {(item["subject"], item["block_hash"], item["transaction_hash"], item["log_index"]): item for item in attributions}
    epochs = {item["subject"]: item["epochs"] for item in epoch_table["epochs"]}
    for log, _ in logs:
        owner = owners.get((log["address"].lower(), log["blockHash"], log["transactionHash"], int(log["logIndex"], 16)))
        if (owner is None or owner["transaction_index"] != int(log["transactionIndex"], 16)
                or int(owner["block_number"]) != int(log["blockNumber"], 16)):
            raise TabulariumError("native log lacks its exact verified positional epoch attribution")
        subject = owner["subject"]
        epoch = epochs[subject][owner["epoch_index"]]
        if epoch["implementation"] != subject:
            raise TabulariumError("Wildcat concrete ABI has an unsupported implementation epoch")
    for index, item in enumerate(epoch_table["epochs"]):
        contexts[item["subject"]]["source"].append({
            "class": "checked-positional-epoch-context",
            "reference": _ref(components, captures, "epoch-table", f"/epochs/{index}"),
            "native": item,
        })
    controllers, deployments = {}, {}
    for event, ref in logs:
        address, topics = event["address"].lower(), event["topics"]
        topic = topics[0].lower() if topics else ""
        role = entries[address]["role"]
        if venue == "wildcat-v1" and role == "factory" and topic == CONTROLLER:
            data = _shape(event, 1, 2)
            controller = _address(data[32:])
            if controller in controllers:
                raise TabulariumError("duplicate controller binding")
            controllers[controller] = {"borrower": _address(data[:32]), "source": ref, "native": event,
                                       "rule": "v1-NewController-and-MarketDeployed"}
        elif role == ("controller" if venue == "wildcat-v1" else "factory") and topic == DEPLOY[venue]:
            market, values = _terms(event, venue)
            if market not in contexts or contexts[market]["role"] != "market":
                continue
            if market in deployments:
                raise TabulariumError("duplicate market deployment context")
            deployments[market] = (event, ref, values)
    transactions = {event["transactionHash"] for event, _, _ in deployments.values()}
    by_tx = defaultdict(list)
    for trace, ref in _journals(plan, manifest, read, interval_api, "traces"):
        if trace.get("transactionHash") in transactions:
            by_tx[trace["transactionHash"]].append((trace, ref))
    for market, deployment in deployments.items():
        event, ref, values = deployment
        binding = controllers.get(event["address"].lower()) if venue == "wildcat-v1" else _binding_v2(event, by_tx[event["transactionHash"]])
        if venue == "wildcat-v1" and binding and _position(binding["native"]) > _position(event):
            raise TabulariumError("controller binding follows market deployment")
        constructor = _constructor(venue, market, deployment, by_tx[event["transactionHash"]],
                                   "controller" if venue == "wildcat-v1" else "factory", entries)
        if binding and constructor and binding["borrower"] != constructor["values"]["borrower"]:
            raise TabulariumError("constructor borrower conflicts with deployment binding")
        context = contexts[market]
        context["asset"] = values["asset"]
        context["source"].append({"class": "inferred-deployment-asset", "reference": ref, "native": event, "values": values})
        if constructor:
            context["source"].append({"class": "recorded-constructor-context", **constructor})
        if binding:
            context["borrower_context"] = {"class": "registry-inferred", **binding}
            context["source"].append({"class": "registry-inferred-debtor", **binding})
    return venue, contexts, logs, {
        "kind": "recorded-interval", "interval": plan["interval"], "subjects": plan["subjects"],
        "raw_captures": manifest["captures"], "wrapper_native_coverage": "not-established",
        "underlying_decimals": "V1 absent; V2 recorded constructor context only",
    }


def _constructed_context(manifest, read):
    from .wildcat_rules import VARIANTS

    components = {item["name"]: item for item in manifest["components"]}
    if set(components) != {"wildcat-construction", "native-logs"}:
        raise TabulariumError("constructed Wildcat release has an unknown component set")
    document = loads_json(read("wildcat-construction"), "construction context")
    _exact(document, ("schema", "venue", "contexts", "limitations"), "construction context")
    venue = document["venue"]
    if document["schema"] != CONSTRUCTION_FORMAT or venue not in PINS or document["limitations"] != [CONSTRUCTION_GAP]:
        raise TabulariumError("constructed Wildcat context has missing source qualifications")
    captures = {item["component"]: item for item in manifest["captures"]}
    if len(manifest["captures"]) != 2 or len(captures) != 2 or set(captures) != set(components):
        raise TabulariumError("constructed Wildcat captures are incomplete")
    for capture in captures.values():
        if (capture["venue"] != venue or capture["chain"] != "eip155:1"
                or capture["evidence_class"] != "recorded-rpc"
                or capture["source"]["kind"] != "constructed-fixture"
                or capture["source"]["locator_class"] != "local-fixture"
                or capture["scope"]["deployment"] != venue + "-constructed-specimen"
                or capture["scope"]["finality"] != "unknown"
                or capture["coverage"]["status"] != "partial"
                or CONSTRUCTION_GAP not in capture["coverage"]["gaps"]):
            raise TabulariumError("constructed Wildcat capture labels conflict")
    if captures["wildcat-construction"]["scope"] != captures["native-logs"]["scope"]:
        raise TabulariumError("constructed capture scopes disagree")
    if not isinstance(document["contexts"], list) or not document["contexts"] or len(document["contexts"]) > 1024:
        raise TabulariumError("constructed context count is invalid")
    contexts = {}
    for index, item in enumerate(document["contexts"]):
        _exact(item, ("address", "role", "asset", "market", "abi_variant", "concrete_contract"), "constructed emitter context")
        address = item["address"]
        if not isinstance(address, str) or not ADDRESS.fullmatch(address) or address in contexts:
            raise TabulariumError("constructed emitter identity is invalid or duplicated")
        for field in ("asset", "market"):
            if item[field] is not None and (not isinstance(item[field], str) or not ADDRESS.fullmatch(item[field])):
                raise TabulariumError("constructed asset or market identity is invalid")
        variant_id = item["abi_variant"]
        if variant_id is not None and not isinstance(variant_id, str):
            raise TabulariumError("constructed concrete ABI identity is invalid")
        variant = VARIANTS.get(variant_id)
        if variant_id is None:
            if item["concrete_contract"] is not None or item["role"] in ("market", "wrapper"):
                raise TabulariumError("constructed primary context lacks its concrete ABI")
        elif (variant is None or variant["contract"] != item["concrete_contract"]
              or {"generation": venue, "role": item["role"]} not in variant["bindings"]):
            raise TabulariumError("constructed concrete ABI is unregistered for its generation and role")
        contexts[address] = {key: value for key, value in item.items() if key != "address"}
        contexts[address]["source"] = [{"class": "declared-constructed-context", "reference": _ref(components, captures, "wildcat-construction", f"/contexts/{index}"), "native": item}]
    for context in contexts.values():
        if context["role"] == "wrapper":
            if venue != "wildcat-v2" or context["market"] not in contexts or contexts[context["market"]]["role"] != "market" or context["asset"] != context["market"]:
                raise TabulariumError("constructed wrapper lacks its declared market-token asset context")
    journal = loads_json(read("native-logs"), "constructed native journal")
    _exact(journal, ("records",), "constructed native journal")
    records = journal["records"]
    if not isinstance(records, list) or len(records) > MAX_RECORDS:
        raise TabulariumError("constructed native journal exceeds the record budget")
    logs = []
    for i, entry in enumerate(records):
        _exact(entry, ("request", "response"), "constructed journal record")
        if not isinstance(entry["request"], str) or not isinstance(entry["response"], str):
            raise TabulariumError("constructed RPC journal bytes must be strings")
        request = loads_json(entry["request"].encode("utf-8"), "constructed RPC request")
        raw = entry["response"].encode("utf-8")
        response = loads_json(raw, "constructed RPC response")
        _exact(request, ("jsonrpc", "id", "method", "params"), "constructed RPC request")
        _exact(response, ("jsonrpc", "id", "result"), "constructed RPC response")
        if request["jsonrpc"] != "2.0" or response["jsonrpc"] != "2.0" or type(request["id"]) is not int or type(response["id"]) is not int or response["id"] != request["id"] or request["method"] != "eth_getLogs" or not isinstance(response["result"], list):
            raise TabulariumError("constructed RPC request and response do not match")
        params = request["params"]
        if not isinstance(params, list) or len(params) != 1:
            raise TabulariumError("constructed log request filter is malformed")
        _exact(params[0], ("address", "fromBlock", "toBlock"), "constructed log filter")
        if params[0]["address"] != sorted(contexts):
            raise TabulariumError("constructed log request does not bind the declared emitter set")
        interval = captures["native-logs"]["scope"]["interval"]
        if interval.get("kind") != "block-range" or params[0]["fromBlock"] != hex(int(interval["start"])) or params[0]["toBlock"] != hex(int(interval["end"])):
            raise TabulariumError("constructed log request conflicts with capture interval")
        for j, record in enumerate(response["result"]):
            if len(logs) >= MAX_RECORDS:
                raise TabulariumError("constructed native journal exceeds the record budget")
            if not isinstance(record, dict) or record.get("address") not in contexts:
                raise TabulariumError("constructed native log is outside the declared emitter set")
            block = record.get("blockNumber")
            if not isinstance(block, str) or not re.fullmatch(r"0x(?:0|[1-9a-f][0-9a-f]*)", block) or not int(interval["start"]) <= int(block, 16) <= int(interval["end"]):
                raise TabulariumError("constructed native log is outside the declared block range")
            logs.append((record, {"component": "native-logs", "component_sha256": components["native-logs"]["sha256"],
                                 "capture_id": captures["native-logs"]["id"], "evidence_class": captures["native-logs"]["evidence_class"],
                                 "journal_selector": f"/records/{i}/response", "response_sha256": "sha256:" + sha256_bytes(raw), "selector": f"/result/{j}"}))
    return venue, contexts, logs, {"kind": "constructed-fixture", "limitations": [CONSTRUCTION_GAP], "raw_captures": manifest["captures"]}


def load_raw(release_root):
    """Return verified native input and rederived context; no descriptor is trusted."""
    root = _path(release_root)
    before = _physical_inventory(root)
    raw = _bounded_file_bytes(root / "manifest.json", 2 * 1024 * 1024, "Alexandria manifest")
    proposed = loads_json(raw, "Alexandria manifest")
    if not isinstance(proposed, dict) or not isinstance(proposed.get("components"), list):
        raise TabulariumError("raw release manifest has no component inventory")
    sizes = [item.get("bytes") if isinstance(item, dict) else None for item in proposed["components"]]
    if any(type(size) is not int or size < 0 or size > MAX_COMPONENT_BYTES for size in sizes) or sum(sizes) > MAX_INPUT_BYTES:
        raise TabulariumError("raw release exceeds component or aggregate byte bounds")
    interval_api, release_api, derivation, errors = _api()
    try:
        release_id, manifest = release_api.verify_release(root)
        read = derivation.component_reader(root, manifest)
        names = {item["name"] for item in manifest["components"]}
        if "interval-plan" in names:
            receipt = interval_api.check_interval(root)
            if receipt["release_id"] != release_id:
                raise TabulariumError("interval verification changed raw release identity")
            plan = loads_json(read("interval-plan"), "interval plan")
            if plan.get("venue") not in PINS:
                raise TabulariumError("raw interval is not a supported Wildcat generation")
            venue, contexts, records, scope = _real_context(plan, manifest, read, interval_api)
        else:
            venue, contexts, records, scope = _constructed_context(manifest, read)
    except errors.AlexandriaError as error:
        raise TabulariumError("Alexandria Wildcat raw verification failed: " + str(error)) from error
    if _physical_inventory(root) != before:
        raise TabulariumError("raw release changed during admission")
    return {"root": root, "release_id": release_id, "manifest": manifest,
            "inventory": before, "venue": venue, "contexts": contexts,
            "records": records, "scope": {"chain": "ethereum-mainnet", **scope}}
