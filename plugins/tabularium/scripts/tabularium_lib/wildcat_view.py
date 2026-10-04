"""Rebuild bounded Wildcat facts from verified Alexandria interval releases."""

from collections import Counter, defaultdict
import importlib
from pathlib import Path
import re
import sys

from .compound_witness import _bounded_file_bytes
from .core import TabulariumError, canonical_json, loads_json, sha256_bytes, write_bytes_atomic
from .keccak import keccak256


FORMAT = "tabularium-wildcat-view/v1"
MAX_INPUT_BYTES = 512 * 1024 * 1024
MAX_VIEW_BYTES = 128 * 1024 * 1024
MAX_RECORDS = 500_000
PINS = {
    "wildcat-v1": "da74452aa7d1a0f024d99efd22cc6d950a8116b7",
    "wildcat-v2": "a70f297fbd1b1ab597e0e9a3458a2d13a34b4657",
}
OBSERVED = "directly-observed"
DERIVED = "derived-from-recorded-evidence"


def _topic(signature):
    return "0x" + keccak256(signature.encode()).hex()


BORROW = _topic("Borrow(uint256)")
REPAY = _topic("DebtRepaid(address,uint256)")
CLOSE = _topic("MarketClosed(uint256)")
CONTROLLER = _topic("NewController(address,address)")
DEPLOY = {
    "wildcat-v1": _topic("MarketDeployed(address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256)"),
    "wildcat-v2": _topic("MarketDeployed(address,address,string,string,address,uint256,uint256,uint256,uint256,uint256,uint256,uint256)"),
}
_INPUTS = "(address,string,string,uint128,uint16,uint16,uint32,uint16,uint32,uint256)"
DEPLOY_CALLS = {
    _topic(f"deployMarket({_INPUTS},bytes,bytes32,address,uint256)")[:10]: 32,
    _topic(f"deployMarketAndHooks(address,bytes,{_INPUTS},bytes,bytes32,address,uint256)")[:10]: 64,
}

# Each old consumer field has a disposition; missing state is never a zero.
UNSUPPORTED = {
    "record_context": {
        "observed_at": "The selected log journals do not supply block timestamps for every event.",
    },
    "market_terms": {
        "token_symbol": "MarketDeployed.symbol names the market token, not the underlying asset.",
        "token_decimals": "No selected, verified asset metadata read supplies decimals.",
        "current_annual_interest_bips": "Deployment terms do not establish the current interest rate.",
        "current_reserve_ratio_bips": "Deployment terms do not establish the current reserve ratio.",
    },
    "market_standing": {
        field: "A finite log interval does not establish current standing or lifetime totals."
        for field in ("is_closed", "is_delinquent_now", "incurring_penalties_now",
                      "total_borrowed", "total_repaid", "penalty_interest_accrued")
    },
    "delinquency_entered": {
        field: "StateUpdated alone does not supply the required liquidity and asset state."
        for field in ("liquidity_required", "assets_held")
    },
    "delinquency_cured": {
        field: "No complete state replay establishes the episode or its duration."
        for field in ("liquidity_required", "assets_held", "seconds_delinquent", "past_grace_period")
    },
    "withdrawal_batch_expired_unpaid": {
        field: "An expiry log alone does not establish the batch's later unpaid status or normalized request amount."
        for field in ("expiry", "requested", "paid")
    },
}


def _api():
    scripts = Path(__file__).resolve().parents[3] / "alexandria" / "scripts"
    sys.path.insert(0, str(scripts))
    try:
        modules = [importlib.import_module(name) for name in (
            "usdc_interval", "alexandria_lib.derivation", "alexandria_lib.canonical",
            "alexandria_lib.errors",
        )]
    except ImportError as error:
        raise TabulariumError("Wildcat views require the sibling Alexandria plugin") from error
    finally:
        sys.path.remove(str(scripts))
    for module in modules:
        if not getattr(module, "__file__", None) or not Path(module.__file__).resolve().is_relative_to(scripts):
            raise TabulariumError("loaded Alexandria API is outside the sibling plugin")
    return modules


def _path(path):
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise TabulariumError("Wildcat input and output paths must not contain symlinks")
    return path.resolve()


def _hex(value, size=None):
    if not isinstance(value, str) or not re.fullmatch(r"0x(?:[0-9a-fA-F]{2})*", value):
        raise TabulariumError("Wildcat ABI value is not hexadecimal bytes")
    data = bytes.fromhex(value[2:])
    if size is not None and len(data) != size:
        raise TabulariumError("Wildcat ABI value has the wrong byte length")
    return data


def _address(word):
    if len(word) != 32 or any(word[:12]):
        raise TabulariumError("Wildcat ABI address has nonzero padding or the wrong length")
    return "0x" + word[12:].hex()


def _shape(event, topics, words):
    if len(event["topics"]) != topics:
        raise TabulariumError("Wildcat event has the wrong topic count")
    return _hex(event["data"], 32 * words)


def _terms(event, venue):
    count = 9 if venue == "wildcat-v1" else 10
    if len(event["topics"]) != (2 if venue == "wildcat-v1" else 3):
        raise TabulariumError("MarketDeployed has the wrong topic count")
    data = _hex(event["data"])
    if len(data) < count * 32 or len(data) > 4096:
        raise TabulariumError("MarketDeployed data is truncated or exceeds the ABI budget")
    words = [data[i * 32:(i + 1) * 32] for i in range(count)]
    strings = []
    end = count * 32
    for word in words[:2]:
        offset = int.from_bytes(word)
        if offset != end or offset + 32 > len(data):
            raise TabulariumError("MarketDeployed string offset is not canonical")
        length = int.from_bytes(data[offset:offset + 32])
        end = offset + 32 + ((length + 31) // 32) * 32
        if length > 512 or end > len(data) or any(data[offset + 32 + length:end]):
            raise TabulariumError("MarketDeployed string is unbounded or has nonzero padding")
        try:
            strings.append(data[offset + 32:offset + 32 + length].decode("utf-8"))
        except UnicodeDecodeError as error:
            raise TabulariumError("MarketDeployed string is not UTF-8") from error
    if end != len(data):
        raise TabulariumError("MarketDeployed has trailing ABI bytes")
    values = {
        "market_name": strings[0], "market_symbol": strings[1],
        "asset": _address(words[2]), "terms_at": "deployment",
    }
    for name, word in zip(("max_total_supply", "annual_interest_bips", "delinquency_fee_bips",
                           "withdrawal_batch_duration", "reserve_ratio_bips", "grace_period_seconds"), words[3:9]):
        values[name] = str(int.from_bytes(word))
    if venue == "wildcat-v2":
        values["hooks"] = "0x" + words[9].hex()
    return _address(_hex(event["topics"][-1], 32)), values


def _position(event):
    return tuple(int(event[name], 16) for name in ("blockNumber", "transactionIndex", "logIndex"))


def _journals(plan, manifest, read, api, kind):
    classes = api.declared_classes(plan)
    components = {item["name"]: item for item in manifest["components"]}
    captures = {item["component"]: item for item in manifest["captures"]}
    count = 0
    for name, part in api.journal_components(plan, classes).items():
        if part["class"] != kind:
            continue
        document = loads_json(read(name), name)
        for i, entry in enumerate(document["records"]):
            raw = entry["response"].encode()
            response = loads_json(raw, name + " response")
            # An RPC error remains a capture gap; it is never an empty result.
            if "result" not in response:
                continue
            response_digest = "sha256:" + sha256_bytes(raw)
            for j, record in enumerate(response["result"]):
                count += 1
                if count > MAX_RECORDS:
                    raise TabulariumError("Wildcat journal exceeds the record budget")
                yield record, {
                    "component": name, "component_sha256": components[name]["sha256"],
                    "capture_id": captures[name]["id"],
                    "evidence_class": captures[name]["evidence_class"],
                    "journal_selector": f"/records/{i}/response",
                    "response_sha256": response_digest,
                    "selector": f"/result/{j}",
                }


def _binding_v2(event, traces):
    market = _address(_hex(event["topics"][-1], 32))
    candidates = []
    for trace, ref in traces:
        action, result = trace.get("action", {}), trace.get("result", {})
        expected = DEPLOY_CALLS.get(action.get("input", "")[:10])
        if (trace.get("type") != "call" or action.get("callType") != "call"
                or action.get("to", "").lower() != event["address"].lower()
                or "error" in trace or not expected
                or trace.get("blockHash") != event["blockHash"]):
            continue
        path = trace["traceAddress"]
        if any("error" in parent and path[:len(parent["traceAddress"])] == parent["traceAddress"]
               for parent, _ in traces):
            continue
        output = _hex(result.get("output"), expected)
        if _address(output[:32]) != market:
            continue
        borrower = "0x" + _hex(action.get("from"), 20).hex()
        candidates.append({"borrower": borrower, "source": ref, "native": trace,
                           "rule": "v2-factory-return-and-MarketDeployed"})
    if len(candidates) > 1:
        raise TabulariumError("ambiguous Wildcat deployment call; borrower cannot be selected")
    return candidates[0] if candidates else None


def make_wildcat_view(release_root):
    """Verify the whole raw release, then derive only source-bound historical facts."""
    root = _path(release_root)
    before = _bounded_file_bytes(root / "manifest.json", 2 * 1024 * 1024, "Alexandria manifest")
    manifest = loads_json(before, "Alexandria manifest")
    try:
        sizes = [item["bytes"] for item in manifest["components"]]
        if any(type(size) is not int or size < 0 for size in sizes) or sum(sizes) > MAX_INPUT_BYTES:
            raise TabulariumError("Wildcat release exceeds the input byte budget")
    except (KeyError, TypeError) as error:
        raise TabulariumError("Wildcat release manifest has no valid component sizes") from error
    api, derivation, canonical, errors = _api()
    try:
        receipt = api.check_interval(root)
        if before != _bounded_file_bytes(root / "manifest.json", 2 * 1024 * 1024, "Alexandria manifest"):
            raise TabulariumError("Alexandria manifest changed during verification")
        read = derivation.component_reader(root, manifest)
        plan = canonical.load_bytes(read("interval-plan"), "interval-plan")
        registry = canonical.load_bytes(read("registry"), "registry")
        venue = plan["venue"]
        if venue not in PINS or (venue == "wildcat-v1" and registry["source"].get("commit") != PINS[venue]):
            raise TabulariumError("Wildcat source commit or venue is unsupported")
        subjects = set(plan["subjects"])
        entries = {item["address"]: item for item in registry["entries"]}
        markets = {address for address in subjects if entries[address]["role"] == "market"}
        controllers, deployments, events = {}, {}, []
        seen = set()
        ignored = Counter()
        for event, ref in _journals(plan, manifest, read, api, "logs"):
            identity = (event["blockHash"].lower(), event["transactionHash"].lower(), int(event["logIndex"], 16))
            if identity in seen:
                raise TabulariumError("duplicate Wildcat log identity")
            seen.add(identity)
            address = event["address"].lower()
            entry = entries[address]
            topic = event["topics"][0].lower() if event["topics"] else ""
            if entry["role"] in ("market", "factory", "controller") and entry["source_commit"] != PINS[venue]:
                raise TabulariumError("Wildcat subject source commit is unsupported")
            if venue == "wildcat-v1" and entry["role"] == "factory" and topic == CONTROLLER:
                data = _shape(event, 1, 2)
                controller = _address(data[32:])
                if controller in controllers:
                    raise TabulariumError("duplicate Wildcat controller binding")
                controllers[controller] = {"borrower": _address(data[:32]), "source": ref,
                                           "native": event, "rule": "v1-NewController-and-MarketDeployed"}
            elif topic == DEPLOY[venue] and entry["role"] == ("controller" if venue == "wildcat-v1" else "factory"):
                market, values = _terms(event, venue)
                if market not in markets:
                    ignored["deployment-outside-selected-markets"] += 1
                    continue
                if market in deployments:
                    raise TabulariumError("duplicate Wildcat market deployment")
                deployments[market] = (event, ref, values)
                events.append(("market_terms", market, values, event, ref))
            elif address in markets and topic in (BORROW, REPAY, CLOSE):
                data = _shape(event, 2 if topic == REPAY else 1, 1)
                claim = {BORROW: "borrow", REPAY: "repayment", CLOSE: "market_closed"}[topic]
                values = {"timestamp" if topic == CLOSE else "amount": str(int.from_bytes(data))}
                if topic == REPAY:
                    values["payer"] = _address(_hex(event["topics"][1], 32))
                events.append((claim, address, values, event, ref))
            else:
                ignored["unmapped-native-log"] += 1
        by_tx = defaultdict(list)
        deployment_txs = {item[0]["transactionHash"] for item in deployments.values()}
        if venue == "wildcat-v2":
            for trace, ref in _journals(plan, manifest, read, api, "traces"):
                if trace.get("transactionHash") in deployment_txs:
                    by_tx[trace["transactionHash"]].append((trace, ref))
        bindings = {}
        for market, (event, ref, _values) in sorted(deployments.items()):
            binding = (controllers.get(event["address"].lower()) if venue == "wildcat-v1"
                       else _binding_v2(event, by_tx[event["transactionHash"]]))
            if binding:
                if venue == "wildcat-v1" and _position(binding["native"]) > _position(event):
                    raise TabulariumError("Wildcat controller binding follows its market deployment")
                bindings[market] = {**binding, "deployment_source": ref, "class": DERIVED}
        rows = []
        for claim, market, values, event, ref in sorted(events, key=lambda item: _position(item[3])):
            values = {"market": market, **values}
            classes = {name: OBSERVED for name in values}
            if claim != "market_terms":
                classes["market"] = DERIVED
            if claim == "market_terms":
                classes["terms_at"] = DERIVED
            rows.append({
                "claim": claim, "market": market,
                "borrower": bindings.get(market, {}).get("borrower"),
                "borrower_class": DERIVED if market in bindings else "unsupported",
                "values": values, "field_classes": classes,
                "source": ref, "native": event,
            })
        return {
            "format": FORMAT, "venue": venue, "release_id": receipt["release_id"],
            "source_commit": PINS[venue], "interval": plan["interval"],
            "registry_sha256": next(item["sha256"] for item in manifest["components"] if item["name"] == "registry"),
            "raw_capture_coverage": {item["id"]: item["coverage"] for item in manifest["captures"]},
            "mapping_coverage": "partial", "unsupported_fields": UNSUPPORTED,
            "selected_markets": sorted(markets),
            "unattributed_markets": sorted(markets - bindings.keys()),
            "ignored_logs": dict(sorted(ignored.items())),
            "bindings": bindings, "records": rows,
        }
    except errors.AlexandriaError as error:
        raise TabulariumError(f"Alexandria Wildcat release failed verification: {error}") from error


def _view_bytes(release_root):
    view = make_wildcat_view(release_root)
    data = canonical_json(view) + b"\n"
    if len(data) > MAX_VIEW_BYTES:
        raise TabulariumError("Wildcat view exceeds the output byte budget")
    return data, {"release_id": view["release_id"], "records": len(view["records"]),
                  "sha256": "sha256:" + sha256_bytes(data)}


def build_wildcat_view(release_root, output):
    """Write a reproducible view outside the preserved release; refuse replacement."""
    root, target = _path(release_root), _path(output)
    if target.is_relative_to(root):
        raise TabulariumError("Wildcat view output must be outside the preserved release")
    data, report = _view_bytes(root)
    if target.exists():
        if _bounded_file_bytes(target, MAX_VIEW_BYTES, "Wildcat view") != data:
            raise TabulariumError("Wildcat view output already contains different bytes")
    else:
        write_bytes_atomic(data, target)
    return report


def verify_wildcat_view(release_root, output):
    """Rebuild from the verified raw release and compare every output byte."""
    data, report = _view_bytes(release_root)
    if _bounded_file_bytes(_path(output), MAX_VIEW_BYTES, "Wildcat view") != data:
        raise TabulariumError("Wildcat view differs from its rebuilt source")
    return report
