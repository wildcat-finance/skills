"""Capture and coverage contracts for Euler event-schema v2 releases."""

from datetime import datetime, timezone
import re

from .adapters import aave_v4, euler_v1, euler_v2
from .core import TabulariumError, safe_integer, sha256_bytes


MANIFEST_SCHEMA_VERSION = 2
EVENT_SCHEMA_VERSION = 2
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ADAPTERS = {
    aave_v4.ADAPTER: aave_v4,
    euler_v1.ADAPTER: euler_v1,
    euler_v2.ADAPTER: euler_v2,
}
EVIDENCE_CLASSES = {
    aave_v4.ADAPTER: "hosted-indexer-reported-block-window",
    euler_v1.ADAPTER: "hosted-rpc-reported-log-scope",
    euler_v2.ADAPTER: "hosted-indexer-reported-query-scope",
}
KNOWN_GAPS = {
    aave_v4.ADAPTER: (
        "the hosted indexer reported the block window; this release does not independently prove the chain boundary",
        "the block window is not complete Aave v4 history, and its bounds were chosen for this release",
        "activity rows report no block hash, transaction index or underlying token address, so every amount leg names a null asset",
        "a REPAY reports no drawn amount, so its asset leg reads the total repaid and no drawn value is reconstructed",
        "SET_COLLATERAL, SUPPLY and WITHDRAW rows are preserved and counted but not mapped as credit events",
        "the release is unsigned; offline verification proves internal consistency, not publisher identity or authenticity",
    ),
    euler_v1.ADAPTER: (
        "the public RPC reported the block and logs; this release does not independently prove the chain boundary",
        "the one-block borrower scope is not the borrower's complete Euler v1 history",
        "the source response does not include block timestamps or token metadata",
        "the release is unsigned; offline verification proves internal consistency, not publisher identity or authenticity",
    ),
    euler_v2.ADAPTER: (
        "the hosted indexer reported its covered range; this release does not independently prove the chain boundary",
        "the exact owner and timestamp query is not complete account or venue history",
        "activity rows do not report block hashes, transaction indexes or underlying token addresses for every amount leg",
        "Euler V2 is the protocol generation and Euler V3 is the source API version",
        "the release is unsigned; offline verification proves internal consistency, not publisher identity or authenticity",
    ),
}


def _object(value, where):
    if not isinstance(value, dict):
        raise TabulariumError("%s is not an object" % where)
    return value


def _exact(value, keys, where):
    value = _object(value, where)
    extra = sorted(set(value) - set(keys))
    missing = sorted(set(keys) - set(value))
    if extra:
        raise TabulariumError("%s has extra field(s): %s" % (where, ", ".join(extra)))
    if missing:
        raise TabulariumError("%s is missing field(s): %s" % (where, ", ".join(missing)))
    return value


def _text(value, where):
    if not isinstance(value, str) or not value:
        raise TabulariumError("%s is not a non-empty string" % where)
    return value


def _utc_timestamp(value, where):
    value = _text(value, where)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise TabulariumError("%s is not an ISO-8601 timestamp" % where) from error
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise TabulariumError("%s is not a UTC timestamp" % where)
    return value


def _digest(value, where):
    value = _text(value, where)
    if not HEX64.fullmatch(value):
        raise TabulariumError("%s is not a lowercase SHA-256 digest" % where)
    return value


def adapter_module(name):
    try:
        return ADAPTERS[name]
    except KeyError as error:
        raise TabulariumError("unsupported release adapter %r" % name) from error


def validate_capture(capture, source, source_bytes, expected_adapter=None):
    capture = _exact(
        capture,
        (
            "schema_version", "release", "adapter", "protocol_generation",
            "source_api", "captured_at", "endpoint", "request", "scope", "source",
        ),
        "capture manifest",
    )
    if safe_integer(capture["schema_version"], "capture manifest.schema_version") != 2:
        raise TabulariumError("unsupported capture manifest schema version")
    _text(capture["release"], "capture manifest.release")
    adapter = _exact(capture["adapter"], ("name", "version"), "capture manifest.adapter")
    module = adapter_module(_text(adapter["name"], "capture manifest.adapter.name"))
    if expected_adapter is not None and adapter["name"] != expected_adapter:
        raise TabulariumError("capture adapter does not match requested adapter")
    if adapter["version"] != module.ADAPTER_VERSION:
        raise TabulariumError("unsupported capture adapter version")
    if capture["protocol_generation"] != module.PROTOCOL_GENERATION:
        raise TabulariumError("capture protocol generation does not match its adapter")
    if capture["source_api"] != module.SOURCE_API:
        raise TabulariumError("capture source API does not match its adapter")
    captured_at = _utc_timestamp(capture["captured_at"], "capture manifest.captured_at")
    _text(capture["endpoint"], "capture manifest.endpoint")
    _object(capture["request"], "capture manifest.request")
    scope = _object(capture["scope"], "capture manifest.scope")
    source_claim = _exact(capture["source"], ("sha256", "bytes"), "capture manifest.source")
    if _digest(source_claim["sha256"], "capture manifest.source.sha256") != sha256_bytes(source_bytes):
        raise TabulariumError("capture manifest source digest does not match source bytes")
    if safe_integer(source_claim["bytes"], "capture manifest.source.bytes") != len(source_bytes):
        raise TabulariumError("capture manifest source byte count does not match source bytes")
    if scope.get("chain") != module.CHAIN:
        raise TabulariumError("capture scope is not Ethereum mainnet")
    if module is euler_v1:
        expected_scope = ("chain", "borrower", "from_block", "to_block", "proxy", "event_topics")
        _exact(scope, expected_scope, "capture manifest.scope")
        if str(scope["borrower"]).lower() != scope["borrower"] or not re.fullmatch(r"0x[0-9a-f]{40}", scope["borrower"]):
            raise TabulariumError("capture borrower is not a lowercase address")
        first = safe_integer(scope["from_block"], "capture manifest.scope.from_block")
        last = safe_integer(scope["to_block"], "capture manifest.scope.to_block")
        if first > last:
            raise TabulariumError("capture block scope is reversed")
        if scope["proxy"] != euler_v1.PROXY:
            raise TabulariumError("capture proxy is not the canonical Euler v1 proxy")
        if scope["event_topics"] != [euler_v1.BORROW_TOPIC, euler_v1.REPAY_TOPIC, euler_v1.LIQUIDATION_TOPIC]:
            raise TabulariumError("capture event topics are incomplete or unsupported")
        if capture["endpoint"] != "https://mainnet.gateway.tenderly.co":
            raise TabulariumError("capture endpoint is not the declared Euler v1 RPC")
        expected_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getLogs",
            "params": [{
                "address": euler_v1.PROXY,
                "fromBlock": hex(first),
                "toBlock": hex(last),
                "topics": [
                    list(scope["event_topics"]),
                    None,
                    "0x" + "0" * 24 + scope["borrower"][2:],
                ],
            }],
        }
        if capture["request"] != expected_request:
            raise TabulariumError("capture request does not match the Euler v1 scope")
    elif module is aave_v4:
        _exact(
            scope,
            ("chain", "from_block", "to_block", "activity_types"),
            "capture manifest.scope",
        )
        first = safe_integer(scope["from_block"], "capture manifest.scope.from_block")
        last = safe_integer(scope["to_block"], "capture manifest.scope.to_block")
        if first > last:
            raise TabulariumError("capture block scope is reversed")
        if scope["activity_types"] != sorted(aave_v4.EXPECTED_TYPES):
            raise TabulariumError("capture activity types are incomplete or unsupported")
        if capture["endpoint"] != "https://gateway.thegraph.com":
            raise TabulariumError("capture endpoint is not The Graph gateway")
        expected_request = {
            "method": "POST",
            "path": "/api/subgraphs/id/%s"
            % _text(
                _object(source["_meta"], "Aave v4 snapshot._meta").get("subgraph_id"),
                "Aave v4 snapshot._meta.subgraph_id",
            ),
            "query": {
                "entity": "userActivities",
                "orderBy": "id",
                "first": "1000",
                "where": "block_gte:%d,block_lte:%d" % (first, last),
            },
        }
        if capture["request"] != expected_request:
            raise TabulariumError("capture request does not match the Aave v4 scope")
        window = _object(
            _object(source["_meta"], "Aave v4 snapshot._meta").get("window"),
            "Aave v4 snapshot._meta.window",
        )
        if (
            safe_integer(window.get("first_block"), "window.first_block") != first
            or safe_integer(window.get("last_block"), "window.last_block") != last
        ):
            raise TabulariumError("snapshot window does not match the capture scope")
    else:
        _exact(scope, ("chain", "owner", "from_timestamp", "to_timestamp", "event_types"), "capture manifest.scope")
        if str(scope["owner"]).lower() != scope["owner"] or not re.fullmatch(r"0x[0-9a-f]{40}", scope["owner"]):
            raise TabulariumError("capture owner is not a lowercase address")
        first = safe_integer(scope["from_timestamp"], "capture manifest.scope.from_timestamp")
        last = safe_integer(scope["to_timestamp"], "capture manifest.scope.to_timestamp")
        if first > last:
            raise TabulariumError("capture timestamp scope is reversed")
        if scope["event_types"] != sorted(euler_v2.MAPPINGS):
            raise TabulariumError("capture event types are incomplete or unsupported")
        if capture["endpoint"] != "https://v3.euler.finance":
            raise TabulariumError("capture endpoint is not the Euler V3 API")
        expected_request = {
            "method": "GET",
            "path": "/v3/activity/accounts/%s/events" % scope["owner"],
            "query": {
                "chainId": "1",
                "eventType": ",".join(scope["event_types"]),
                "from": str(first),
                "limit": "100",
                "to": str(last),
            },
        }
        if capture["request"] != expected_request:
            raise TabulariumError("capture request does not match the Euler V3 scope")
        source_meta = _object(source.get("meta"), "Euler V3 response.meta")
        if _utc_timestamp(source_meta.get("timestamp"), "Euler V3 response.meta.timestamp") != captured_at:
            raise TabulariumError("capture timestamp does not match the Euler V3 response")
    mapped = module.map_source(source, capture)
    return module, mapped


def make_manifest(release, adapter_name, source_path, source_bytes, capture_path,
                  capture_bytes, canonical_path, canonical_bytes, capture, mapped):
    module = adapter_module(adapter_name)
    return {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "release": _text(release, "release"),
        "source": {
            "path": source_path,
            "sha256": sha256_bytes(source_bytes),
            "bytes": len(source_bytes),
            "evidence_class": EVIDENCE_CLASSES[adapter_name],
            "protocol_generation": module.PROTOCOL_GENERATION,
            "source_api": module.SOURCE_API,
            "chain": module.CHAIN,
            "scope": capture["scope"],
        },
        "capture_manifest": {
            "path": capture_path,
            "sha256": sha256_bytes(capture_bytes),
            "bytes": len(capture_bytes),
        },
        "canonical": {
            "path": canonical_path,
            "sha256": sha256_bytes(canonical_bytes),
            "bytes": len(canonical_bytes),
            "rows": len(mapped.events),
        },
        "coverage": {
            "included_events": mapped.mapped_counts,
            "unsupported_events": mapped.unmapped_counts,
        },
        "versions": {
            "event_schema": EVENT_SCHEMA_VERSION,
            "adapter": {"name": adapter_name, "version": module.ADAPTER_VERSION},
            "mapping_rules": sorted({event["provenance"]["mapping_rule"] for event in mapped.events}),
        },
        "known_gaps": list(KNOWN_GAPS[adapter_name]),
    }


def _artifact(value, where):
    value = _exact(value, ("path", "sha256", "bytes"), where)
    _text(value["path"], "%s.path" % where)
    _digest(value["sha256"], "%s.sha256" % where)
    safe_integer(value["bytes"], "%s.bytes" % where)
    return value


def validate_manifest(manifest):
    manifest = _exact(
        manifest,
        (
            "schema_version", "release", "source", "capture_manifest", "canonical",
            "coverage", "versions", "known_gaps",
        ),
        "coverage manifest",
    )
    if safe_integer(manifest["schema_version"], "coverage manifest.schema_version") != 2:
        raise TabulariumError("unsupported coverage manifest schema version")
    _text(manifest["release"], "coverage manifest.release")
    source = _exact(
        manifest["source"],
        ("path", "sha256", "bytes", "evidence_class", "protocol_generation", "source_api", "chain", "scope"),
        "coverage manifest.source",
    )
    _text(source["path"], "coverage manifest.source.path")
    _digest(source["sha256"], "coverage manifest.source.sha256")
    safe_integer(source["bytes"], "coverage manifest.source.bytes")
    _object(source["scope"], "coverage manifest.source.scope")
    _artifact(manifest["capture_manifest"], "coverage manifest.capture_manifest")
    canonical = _exact(manifest["canonical"], ("path", "sha256", "bytes", "rows"), "coverage manifest.canonical")
    _text(canonical["path"], "coverage manifest.canonical.path")
    _digest(canonical["sha256"], "coverage manifest.canonical.sha256")
    safe_integer(canonical["bytes"], "coverage manifest.canonical.bytes")
    safe_integer(canonical["rows"], "coverage manifest.canonical.rows")
    coverage = _exact(manifest["coverage"], ("included_events", "unsupported_events"), "coverage manifest.coverage")
    for name in ("included_events", "unsupported_events"):
        counts = _object(coverage[name], "coverage manifest.coverage.%s" % name)
        for key, value in counts.items():
            _text(key, "coverage event name")
            safe_integer(value, "coverage count")
    versions = _exact(manifest["versions"], ("event_schema", "adapter", "mapping_rules"), "coverage manifest.versions")
    if safe_integer(versions["event_schema"], "coverage manifest.versions.event_schema") != 2:
        raise TabulariumError("unsupported event schema version")
    adapter = _exact(versions["adapter"], ("name", "version"), "coverage manifest.versions.adapter")
    module = adapter_module(adapter["name"])
    if adapter["version"] != module.ADAPTER_VERSION:
        raise TabulariumError("unsupported adapter version")
    if source["evidence_class"] != EVIDENCE_CLASSES[adapter["name"]]:
        raise TabulariumError("unsupported source evidence class")
    if source["protocol_generation"] != module.PROTOCOL_GENERATION or source["source_api"] != module.SOURCE_API or source["chain"] != module.CHAIN:
        raise TabulariumError("source version fields do not match the adapter")
    rules = versions["mapping_rules"]
    if not isinstance(rules, list) or rules != sorted(set(rules)) or not all(isinstance(rule, str) and rule for rule in rules):
        raise TabulariumError("mapping-rule versions are not a sorted unique list")
    allowed_rules = {mapping[2] for mapping in module.MAPPINGS.values()}
    if not set(rules) <= allowed_rules:
        raise TabulariumError("unsupported mapping-rule versions")
    if manifest["known_gaps"] != list(KNOWN_GAPS[adapter["name"]]):
        raise TabulariumError("known semantic gaps are incomplete or unsupported")
    return manifest
