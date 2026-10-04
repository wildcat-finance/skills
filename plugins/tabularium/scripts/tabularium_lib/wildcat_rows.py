"""Preserve Wildcat native parties, units and qualified log dispositions."""

from collections import Counter, defaultdict
from copy import deepcopy
import re

from .core import MAX_SAFE_INTEGER, TabulariumError, canonical_json, sha256_bytes
from .wildcat_abi import VARIANTS, decode_log, hex_bytes
from .wildcat_rules import ADAPTER_VERSION, BY_SIGNATURE, CHAIN, ROUTING_SIGNATURE, SOURCE_API


MAX_RECORDS = 500_000
_ADDRESS = re.compile(r"0x[0-9a-f]{40}\Z")
_HASH = re.compile(r"0x[0-9a-fA-F]{64}\Z")
_QUANTITY = re.compile(r"0x(?:0|[1-9a-fA-F][0-9a-fA-F]*)\Z")
_REF_KEYS = frozenset(("component", "component_sha256", "capture_id", "evidence_class",
                       "journal_selector", "response_sha256", "selector"))
_NATIVE_CLASSES = frozenset(("recorded-rpc", "recorded", "recorded:constructed-fixture"))
_CONTEXT_CLASSES = frozenset(("checked-registry-context", "checked-positional-epoch-context",
                              "inferred-deployment-asset", "recorded-constructor-context",
                              "registry-inferred-debtor", "declared-constructed-context"))


def selector(reference):
    """Bind one opaque row selector to its complete nested journal reference."""
    if not isinstance(reference, dict) or set(reference) != _REF_KEYS:
        raise TabulariumError("Wildcat native reference has an unsupported field set")
    if not all(isinstance(v, str) and v and len(v) <= 1024 for v in reference.values()):
        raise TabulariumError("Wildcat native reference has an invalid string field")
    if reference["evidence_class"] not in _NATIVE_CLASSES:
        raise TabulariumError("Wildcat native reference has an unaccepted evidence class")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", reference["component_sha256"]):
        raise TabulariumError("Wildcat native component digest is malformed")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", reference["response_sha256"]):
        raise TabulariumError("Wildcat native response digest is malformed")
    if not re.fullmatch(r"/records/(?:0|[1-9][0-9]*)/response", reference["journal_selector"]):
        raise TabulariumError("Wildcat native journal selector is malformed")
    if not re.fullmatch(r"/result/(?:0|[1-9][0-9]*)", reference["selector"]):
        raise TabulariumError("Wildcat native response selector is malformed")
    if len(canonical_json(reference)) > 4096:
        raise TabulariumError("Wildcat native reference exceeds its byte budget")
    return "wildcat-journal:" + sha256_bytes(canonical_json(reference))


def context_selector(record):
    """Bind separately classified context without strengthening its evidence."""
    if not isinstance(record, dict):
        raise TabulariumError("Wildcat supporting context is not an object")
    evidence_class = record.get("class", record.get("evidence_class"))
    if not isinstance(evidence_class, str) or evidence_class not in _CONTEXT_CLASSES:
        raise TabulariumError("Wildcat supporting context lacks an evidence class")
    encoded = canonical_json(record)
    if len(encoded) > 65536:
        raise TabulariumError("Wildcat supporting context exceeds its byte budget")
    return "wildcat-context:" + sha256_bytes(encoded)


def _address(value, where):
    if not isinstance(value, str) or not _ADDRESS.fullmatch(value):
        raise TabulariumError("Wildcat %s is not a lowercase address" % where)
    return value


def _quantity(value, where):
    if not isinstance(value, str) or not _QUANTITY.fullmatch(value) or len(value) > 16:
        raise TabulariumError("Wildcat %s is not a bounded JSON-RPC quantity" % where)
    result = int(value, 16)
    if result > MAX_SAFE_INTEGER:
        raise TabulariumError("Wildcat %s exceeds the safe integer range" % where)
    return result


def _transaction(raw):
    if not isinstance(raw, dict) or raw.get("removed") is not False:
        raise TabulariumError("Wildcat native log is not an unremoved object")
    values = {}
    for key, name in (("blockNumber", "block_number"), ("transactionIndex", "transaction_index"),
                      ("logIndex", "log_index")):
        values[name] = _quantity(raw.get(key), key)
    for key, name in (("transactionHash", "hash"), ("blockHash", "block_hash")):
        value = raw.get(key)
        if not isinstance(value, str) or not _HASH.fullmatch(value):
            raise TabulariumError("Wildcat native log has an invalid %s" % key)
        values[name] = value.lower()
    values["timestamp"] = None
    return values


def _context(venue, emitter, context):
    if not isinstance(context, dict) or not isinstance(context.get("role"), str) or not context["role"]:
        raise TabulariumError("Wildcat emitter context has no role")
    source = context.get("source")
    if not isinstance(source, list) or len(source) > 1024:
        raise TabulariumError("Wildcat emitter context has no bounded source inventory")
    supports = [context_selector(item) for item in source]
    if len(supports) != len(set(supports)):
        raise TabulariumError("Wildcat emitter context repeats supporting records")
    asset = context.get("asset")
    if asset is not None:
        _address(asset, "asset context")
    variant_id = context.get("abi_variant")
    if variant_id is not None:
        variant = VARIANTS.get(variant_id)
        if variant is None or {"generation": venue, "role": context["role"]} not in variant["bindings"]:
            raise TabulariumError("Wildcat concrete ABI does not bind its generation and emitter role")
        if context.get("concrete_contract") != variant["contract"]:
            raise TabulariumError("Wildcat concrete contract does not match its ABI variant")
    if context["role"] == "wrapper":
        if venue != "wildcat-v2" or context.get("market") != asset or asset == emitter:
            raise TabulariumError("Wildcat wrapper context does not bind a distinct wrapped market")
        if asset is None:
            raise TabulariumError("Wildcat wrapper context lacks its wrapped market")
    return supports


def _party(role, address):
    return {"role": role, "address": address}


def _amount(kind, value, asset):
    return {"kind": kind, "base_units": value, "asset": asset}


def _context_summary(context):
    result = {key: deepcopy(context.get(key)) for key in
              ("role", "asset", "market", "abi_variant", "concrete_contract")}
    borrower = context.get("borrower_context")
    if borrower is not None:
        if not isinstance(borrower, dict):
            raise TabulariumError("Wildcat inferred debtor context is not an object")
        result["borrower_context"] = {key: deepcopy(borrower[key]) for key in
                                      ("borrower", "class", "rule") if key in borrower}
    return result


def _primary(venue, emitter, context, definition, values, raw, reference, supports):
    specification = BY_SIGNATURE[(venue, context["role"], definition["signature"])]
    action = specification["action"].split(".", 1)[1]
    asset = context.get("asset")
    limitations = []
    gaps = []
    if action == "deposit":
        parties = [_party("depositor", values["account"]), _party("minted-token-account", values["account"])]
        amounts = [_amount("assets", values["assetAmount"], asset), _amount("scaled-claims", values["scaledAmount"], None)]
    elif action == "withdrawal-queued":
        parties = [_party("withdrawing-account", values["account"])]
        amounts = [_amount("normalized-claims", values["normalizedAmount"], emitter), _amount("scaled-claims", values["scaledAmount"], None)]
        limitations.append("The queued claims do not establish assets paid.")
    elif action == "withdrawal-executed":
        parties = [_party("beneficiary", values["account"])]
        amounts = [_amount("assets", values["normalizedAmount"], asset)]
        gaps.extend(("attribution:withdrawal-executed:executor", "attribution:withdrawal-executed:recipient"))
        limitations.append("The indexed account is the claim beneficiary; no executor is emitted.")
    elif action in ("transfer", "wrapper-transfer"):
        parties = [_party("from", values["from"]), _party("to", values["to"])]
        kind = "market-token-claims" if action == "transfer" else "wrapper-shares"
        amounts = [_amount(kind, values.get("value", values.get("amount")), emitter)]
        limitations.append("Native token endpoints do not establish underlying cash flow or fresh capital.")
    elif action == "borrow":
        parties = [_party("pool", emitter)]
        amounts = [_amount("assets", values["assetAmount"], asset)]
        gaps.append("attribution:borrow:borrower")
        limitations.append("The amount-only event emits no borrower actor.")
    elif action == "debt-repaid":
        parties = [_party("payer", values["from"]), _party("pool", emitter)]
        amounts = [_amount("assets", values["assetAmount"], asset)]
        gaps.append("attribution:debt-repaid:debtor")
        limitations.append("The emitted payer is separate from any inferred debtor context.")
    elif action == "market-closed":
        parties = [_party("pool", emitter)]
        amounts = []
        gaps.append("attribution:market-closed:closing-actor")
        limitations.append("The timestamp is native state; closure does not establish settlement or full repayment.")
        if venue == "wildcat-v1":
            limitations.append("Closure does not establish processing of expired withdrawal batches.")
    elif action == "wrapper-deposit":
        parties = [_party("caller", values["by"]), _party("owner", values["owner"])]
        amounts = [_amount("market-token-assets", values["assets"], asset), _amount("wrapper-shares", values["shares"], emitter)]
        limitations.append("The wrapper exchanges market tokens and wrapper shares; no underlying cash flow is inferred.")
    elif action == "wrapper-withdrawal":
        parties = [_party("caller", values["by"]), _party("receiver", values["to"]), _party("owner", values["owner"])]
        amounts = [_amount("market-token-assets", values["assets"], asset), _amount("wrapper-shares", values["shares"], emitter)]
        limitations.append("The wrapper returns market tokens rather than executing a pool withdrawal.")
    else:
        raise TabulariumError("Wildcat primary mapping is unimplemented")
    if any(a["kind"] in ("assets", "market-token-assets") and a["asset"] is None for a in amounts):
        gaps.append("attribution:%s:asset" % action)
        limitations.append("The source does not establish an asset context; missing metadata remains null.")
    transaction = _transaction(raw)
    source_selector = selector(reference)
    event = {
        "schema_version": 3,
        "id": "tabularium:%s:%s:%s:%d:%s" % (CHAIN, venue, transaction["hash"], transaction["log_index"], specification["rule"]),
        "event_family": specification["family"], "action": specification["action"], "venue": venue,
        "chain": CHAIN, "transaction": transaction, "parties": parties,
        "instrument": {"type": specification["instrument_type"], "id": emitter}, "amounts": amounts,
        "provenance": {
            "source_kind": "ethereum-log", "source_contract": emitter,
            "source_entity": definition["signature"], "source_id": transaction["hash"] + ":" + str(transaction["log_index"]),
            "source_selector": source_selector, "supporting_selectors": list(supports),
            "mapping_rule": specification["rule"], "adapter": venue, "adapter_version": ADAPTER_VERSION,
            "protocol_generation": venue, "source_api": SOURCE_API,
        },
        "native_record": deepcopy(raw),
    }
    return event, gaps, limitations


def map_records(venue, contexts, records):
    """Partition preserved logs and map only their admitted native meanings."""
    if venue not in ("wildcat-v1", "wildcat-v2"):
        raise TabulariumError("Wildcat mapping generation is unsupported")
    if not isinstance(contexts, dict) or len(contexts) > MAX_RECORDS:
        raise TabulariumError("Wildcat context inventory is not bounded")
    context_supports = {}
    for emitter, context in contexts.items():
        _address(emitter, "emitter context")
        context_supports[emitter] = _context(venue, emitter, context)
    if not isinstance(records, (list, tuple)) or len(records) > MAX_RECORDS:
        raise TabulariumError("Wildcat native log inventory exceeds its record budget")
    seen_selectors, seen_logs = set(), set()
    blocks, transactions, block_numbers, transaction_positions = {}, {}, {}, {}
    block_log_positions = set()
    decoded = []
    for entry in records:
        if not isinstance(entry, (list, tuple)) or len(entry) != 2:
            raise TabulariumError("Wildcat native record does not carry one source reference")
        raw, reference = entry
        tx = _transaction(raw)
        emitter = _address(raw.get("address"), "native emitter")
        source_selector = selector(reference)
        identity = (tx["hash"], tx["log_index"])
        if source_selector in seen_selectors or identity in seen_logs:
            raise TabulariumError("Wildcat source repeats a native log identity or selector")
        seen_selectors.add(source_selector)
        seen_logs.add(identity)
        block_number = tx["block_number"]
        if block_number in blocks and blocks[block_number] != tx["block_hash"]:
            raise TabulariumError("Wildcat source gives one block conflicting hashes")
        blocks[block_number] = tx["block_hash"]
        if tx["block_hash"] in block_numbers and block_numbers[tx["block_hash"]] != block_number:
            raise TabulariumError("Wildcat source gives one block hash conflicting numbers")
        block_numbers[tx["block_hash"]] = block_number
        position = (tx["block_hash"], tx["transaction_index"])
        if position in transaction_positions and transaction_positions[position] != tx["hash"]:
            raise TabulariumError("Wildcat source gives one transaction position conflicting hashes")
        transaction_positions[position] = tx["hash"]
        block_log_position = (tx["block_hash"], tx["log_index"])
        if block_log_position in block_log_positions:
            raise TabulariumError("Wildcat source repeats a block-wide log index")
        block_log_positions.add(block_log_position)
        metadata = (block_number, tx["block_hash"], tx["transaction_index"])
        if tx["hash"] in transactions and transactions[tx["hash"]] != metadata:
            raise TabulariumError("Wildcat source gives one transaction conflicting metadata")
        transactions[tx["hash"]] = metadata
        context = contexts.get(emitter, {"role": "unregistered", "source": [], "abi_variant": None})
        variant_id = context.get("abi_variant")
        if variant_id is not None:
            result = decode_log(variant_id, raw)
        else:
            topics = raw.get("topics")
            if not isinstance(topics, list) or not 1 <= len(topics) <= 4:
                raise TabulariumError("Wildcat unknown log topics are malformed")
            for topic in topics:
                hex_bytes(topic, 32)
            hex_bytes(raw.get("data"))
            result = None
        definition, values = result if result else (None, None)
        decoded.append({"raw": raw, "reference": reference, "selector": source_selector,
                        "emitter": emitter, "context": context, "definition": definition,
                        "values": values, "transaction": tx})
    decoded.sort(key=lambda item: (item["transaction"]["block_number"], item["transaction"]["transaction_index"],
                                   item["transaction"]["log_index"], item["selector"]))
    routes, executions = defaultdict(list), defaultdict(list)
    for item in decoded:
        if item["definition"] is None or item["context"]["role"] != "market":
            continue
        sig = item["definition"]["signature"]
        values = item["values"]
        if sig in (ROUTING_SIGNATURE, "WithdrawalExecuted(uint256,address,uint256)"):
            amount = values["amount"] if sig == ROUTING_SIGNATURE else values["normalizedAmount"]
            key = (item["emitter"], item["transaction"]["hash"], values["account"], values["expiry"], amount)
            (routes if sig == ROUTING_SIGNATURE else executions)[key].append(item)
            item["routing_key"] = key
    events, dispositions, mappings = [], [], []
    included, unsupported = Counter(), Counter()
    for item in decoded:
        raw, reference, source_selector = item["raw"], item["reference"], item["selector"]
        context, definition, values = item["context"], item["definition"], item["values"]
        role, emitter = context["role"], item["emitter"]
        supports = context_supports.get(emitter, [])
        gaps, limitations, join = [], [], None
        if definition is None:
            disposition = "unsupported-decode"
            gaps.append("decode:%s:%s" % (role, raw["topics"][0].lower()))
            limitations.append("No accepted concrete ABI decodes this emitter role and topic.")
        elif (venue, role, definition["signature"]) in BY_SIGNATURE:
            disposition = "primary"
            event, gaps, limitations = _primary(venue, emitter, context, definition, values, raw, reference, supports)
            if "routing_key" in item and definition["signature"] != ROUTING_SIGNATURE:
                key = item["routing_key"]
                companions = routes[key]
                if len(companions) == 1 and len(executions[key]) == 1:
                    companion = companions[0]
                    event["parties"].append(_party("escrow-recipient", companion["values"]["escrow"]))
                    event["provenance"]["supporting_selectors"].append(companion["selector"])
                    gaps.remove("attribution:withdrawal-executed:recipient")
                    join = {"evidence_class": "join-inference", "rule": "same-market-transaction-account-expiry-amount",
                            "primary_selector": source_selector, "companion_selector": companion["selector"],
                            "conditions": {"market": emitter, "transaction_hash": item["transaction"]["hash"],
                                           "account": values["account"], "expiry": values["expiry"],
                                           "amount": values["normalizedAmount"]}}
                elif companions:
                    limitations.append("Routing companions are ambiguous; no escrow recipient is inferred.")
                else:
                    limitations.append("No unique routing companion establishes the ultimate cash recipient.")
            events.append(event)
            included[event["action"].split(".", 1)[1]] += 1
        elif role == "market" and definition["signature"] == ROUTING_SIGNATURE:
            disposition = "supporting-routing"
            limitations.append("The routing companion is not a second cash withdrawal.")
        else:
            disposition = "unsupported-canonical-meaning"
            gaps.append("canonical:%s:%s" % (role, definition["signature"]))
            limitations.append("The concrete ABI is decoded; no canonical meaning is admitted for this event.")
        unsupported.update(gaps)
        dispositions.append({"source_selector": source_selector, "emitter_role": role,
                             "topic0": raw["topics"][0].lower(), "disposition": disposition,
                             "gaps": gaps})
        mappings.append({"source_selector": source_selector, "reference": deepcopy(reference),
                         "evidence_class": "directly-observed", "emitter_role": role,
                         "abi_variant": context.get("abi_variant"),
                         "concrete_contract": context.get("concrete_contract"),
                         "signature": definition["signature"] if definition else None,
                         "definition": deepcopy(definition), "decoded": deepcopy(values),
                         "context": _context_summary(context),
                         "supporting_selectors": list(supports) + ([join["companion_selector"]] if join else []),
                         "join": join, "limitations": limitations, "disposition": disposition,
                         "native_record": deepcopy(raw)})
    return {"events": tuple(events), "dispositions": tuple(dispositions), "mapping_records": tuple(mappings),
            "included_counts": dict(sorted(included.items())), "unsupported_counts": dict(sorted(unsupported.items()))}
