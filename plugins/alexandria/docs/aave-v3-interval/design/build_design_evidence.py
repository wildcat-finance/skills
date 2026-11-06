"""Evaluate four Aave V3 interval-capture constructions; conformance stays pending.

Every selection value is computed from a declared model of each candidate or
from the bounded preflight sample beside this file, never typed in.  The two
byte figures come from `preflight-sample.json`: twelve 1,000-block log windows
over the 356-address filter and 72 traced transactions from the local archive
node on 2026-09-23.  Traces are costed at the sample's filtered bytes per
transaction; logs at each window's own response bytes.

This script writes the design record and its selection reports once.  It reads
no controller state and writes none.  Do not rerun it after the study is
receipted: it would rewrite a receipted report.
"""

from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
COMMAND = "python3 .hexaemeron/design/build_design_evidence.py"
SELECTED = "segmented-proxy-set-venue"

# The existing release format admits at most 128 components of 64 MiB each.
FORMAT_CEILING = 128 * 64 * 1024 * 1024
# `shards_per_component` splits all three shard classes at the same shard
# ranges, so a segment has one range count for boundary blocks, logs and
# traces alike.  Forty ranges per class is what the preserved Wildcat V2
# release used (3,463 shards at 87 per component); three classes of forty
# leave eight of the 128 components for the opening evidence, registry,
# implementation code and the rest.  Each range of the densest class is
# planned to at most 48 MiB, three quarters of the 64 MiB component ceiling.
RANGES_PER_CLASS = 40
RANGE_TARGET = 48 * 1024 * 1024

CANDIDATES = (
    "segmented-proxy-set-venue",
    "single-interval-venue",
    "log-discovered-subjects",
    "global-transaction-order-rule",
)

SUMMARIES = {
    "segmented-proxy-set-venue": (
        "A reviewed aave-v3 venue with a pinned 356-subject registry, per-subject "
        "EIP-1967 or immutable epochs with a venue-scoped upgrade-transaction order "
        "rule, and the interval frozen as contiguous segment plans that each fit one release."
    ),
    "single-interval-venue": (
        "The same venue and registry, but one plan and one release over the whole "
        "interval from 16291071 to 26022093."
    ),
    "log-discovered-subjects": (
        "Pin only the 22 contracts the merged row lists and discover token proxies, "
        "strategies and implementations from provider and configurator logs during collection."
    ),
    "global-transaction-order-rule": (
        "Admit ordinary proxy logs inside an upgrade transaction by position for every "
        "venue by removing the shared refusal, instead of scoping the rule to aave-v3."
    ),
}

SHARED_EDITS = [
    "alexandria_lib/venues/__init__.py, the aave-v3 _MODULES row",
    "alexandria_lib/interval.py, an opt-in upgrade-transaction order parameter on proxy_log_positions",
    "usdc_interval.py, passing the venue's upgrade-transaction rule to attribution in build and check",
]

SPECS = {
    "segmented-proxy-set-venue": {
        "entry_points": ["collect", "reconcile", "build", "check"],
        "subject_set": "registry-before-collection",
        "subject_pin": "reviewed-code",
        "order_rule_scope": "venue",
        "releases": "segments",
        "shared_edit_sites": SHARED_EDITS,
    },
    "single-interval-venue": {
        "entry_points": ["collect", "reconcile", "build", "check"],
        "subject_set": "registry-before-collection",
        "subject_pin": "reviewed-code",
        "order_rule_scope": "venue",
        "releases": "one",
        "shared_edit_sites": SHARED_EDITS,
    },
    "log-discovered-subjects": {
        "entry_points": ["collect", "reconcile", "build", "check"],
        "subject_set": "discovered-during-collection",
        "subject_pin": "provider-responses",
        "order_rule_scope": "venue",
        "releases": "segments",
        "shared_edit_sites": SHARED_EDITS + [
            "usdc_interval.py Collector.collect, a discovery pass that widens the subject set between shards",
            "alexandria_lib/interval.py validate_plan, a subject set that grows after the plan digest is bound",
        ],
    },
    "global-transaction-order-rule": {
        "entry_points": ["collect", "reconcile", "build", "check"],
        "subject_set": "registry-before-collection",
        "subject_pin": "reviewed-code",
        "order_rule_scope": "every-venue",
        "releases": "segments",
        "shared_edit_sites": [
            "alexandria_lib/venues/__init__.py, the aave-v3 _MODULES row",
            "alexandria_lib/interval.py, the removed ordinary-log refusal in proxy_log_positions",
            "examples/usdc-interval-epochs-v0, the refusal probe and expected.json",
            "tests/test_epoch_positions_demo.py, the upgrade-transaction refusal assertion",
        ],
    },
}

EXISTING_ENTRY_POINTS = ["collect", "reconcile", "build", "check"]


def sample_rates():
    """Bytes per block from the recorded preflight sample.

    Returns the mean total rate, the densest window's total rate, the densest
    single-class rate among logs and traces, and the interval length.
    """
    sample = json.loads((ROOT / "design" / "preflight-sample.json").read_text())
    traces = sample["trace_sample"]
    per_transaction = traces["filtered_frame_bytes"] / traces["transactions"]
    windows = sample["log_windows"]["windows"]
    blocks = total = 0
    densest = densest_class = 0.0
    for window in windows:
        width = window["to_block"] - window["from_block"] + 1
        logs = window["response_bytes"]
        trace_bytes = window["distinct_transactions"] * per_transaction
        blocks += width
        total += logs + trace_bytes
        densest = max(densest, (logs + trace_bytes) / width)
        densest_class = max(densest_class, logs / width, trace_bytes / width)
    return total / blocks, densest, densest_class, sample["interval_blocks"]


def largest_release_bytes(candidate: str) -> int:
    mean, densest, densest_class, interval_blocks = sample_rates()
    if SPECS[candidate]["releases"] == "one":
        return int(mean * interval_blocks)
    # Uniform-width segments at the densest sampled rate, a conservative bound:
    # the densest class fills forty ranges of 48 MiB and no more.
    width = int(RANGES_PER_CLASS * RANGE_TARGET // densest_class)
    return int(width * densest)


def values_for(candidate: str) -> dict:
    spec = SPECS[candidate]
    return {
        "existing-build-check-path": spec["entry_points"] == EXISTING_ENTRY_POINTS,
        "subject-set-frozen-before-collection": spec["subject_set"] == "registry-before-collection",
        "largest-release-within-ceiling": largest_release_bytes(candidate),
        "upgrade-order-rule-venue-scoped": spec["order_rule_scope"] == "venue",
        "subject-pin-in-reviewed-code": spec["subject_pin"] == "reviewed-code",
        "shared-module-edit-sites": len(spec["shared_edit_sites"]),
        "largest-release-estimate": largest_release_bytes(candidate),
    }


def gate(name, concern, owner, unit="boolean", comparator="equals", threshold=True):
    return {"blocks": "design-lock", "comparator": comparator, "concern": concern,
            "id": name, "kind": "gate", "owner": owner, "stage": "selection",
            "threshold": threshold, "unit": unit}


def metric(name, concern, unit):
    return {"blocks": "design-lock", "comparator": "minimise", "concern": concern,
            "id": name, "kind": "metric", "owner": "metron", "stage": "selection",
            "threshold": None, "unit": unit}


def conformance(name, concern, owner, blocks):
    return {"blocks": blocks, "comparator": "equals", "concern": concern, "id": name,
            "kind": "gate", "owner": owner, "stage": "conformance", "threshold": True,
            "unit": "boolean"}


CRITERIA = [
    gate("existing-build-check-path", "compatibility", "protasis"),
    gate("subject-set-frozen-before-collection", "correctness", "protasis"),
    gate("largest-release-within-ceiling", "space", "metron", unit="bytes",
         comparator="at-most", threshold=FORMAT_CEILING),
    gate("upgrade-order-rule-venue-scoped", "compatibility", "protasis"),
    gate("subject-pin-in-reviewed-code", "recovery", "phylax"),
    metric("shared-module-edit-sites", "time", "count"),
    metric("largest-release-estimate", "space", "bytes"),
    conformance("registry-reproduces-recorded-subject-set", "correctness", "protasis", "step:3"),
    conformance("registry-pin-change-refuses", "recovery", "phylax", "step:3"),
    conformance("per-subject-proxy-epochs-derived", "correctness", "protasis", "step:4"),
    conformance("unsupported-upgrade-shapes-refuse", "recovery", "elenchus", "step:4"),
    conformance("other-venues-keep-upgrade-transaction-refusal", "compatibility", "protasis", "step:4"),
    conformance("wrong-chain-or-market-refuses", "recovery", "phylax", "step:5"),
    conformance("collection-refusal-battery", "recovery", "elenchus", "step:5"),
    conformance("transaction-index-only-disagreement-declared", "correctness", "protasis", "step:5"),
    conformance("credential-absent-from-artefacts", "recovery", "phylax", "step:5"),
    conformance("segment-plans-tile-the-interval", "correctness", "protasis", "step:7"),
    conformance("segment-budget-within-ceilings", "space", "metron", "step:7"),
    conformance("preflight-measurement-recorded", "time", "metron", "step:7"),
    conformance("production-segments-preserved-and-rebuilt", "correctness", "protasis", "step:8"),
    conformance("existing-release-identities-retained", "compatibility", "protasis", "integration"),
    conformance("aave-fixture-rebuilds-offline-without-sockets", "correctness", "protasis", "integration"),
]


def encode(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def main() -> None:
    record = {
        "candidates": [{"id": n, "summary": SUMMARIES[n]} for n in CANDIDATES],
        "criteria": CRITERIA,
        "results": [],
        "schema": "protasis-design-evidence/v1",
        "selection": {"candidate": SELECTED, "policy_ref": None, "rule": "unique-frontier"},
    }
    observations = {}
    for candidate in CANDIDATES:
        values = values_for(candidate)
        observations[candidate] = {"spec": SPECS[candidate], "values": values}
        for item in CRITERIA:
            name = item["id"]
            if item["stage"] == "conformance":
                record["results"].append({
                    "blocks": item["blocks"],
                    "candidate": candidate,
                    "criterion": name,
                    "report": f"reports/conformance/{candidate}-{name}.json",
                    "resolver": (
                        "python3 .hexaemeron/design/conformance.py "
                        f"{name} --candidate {candidate}"
                    ),
                    "state": "pending",
                })
                continue
            value = values[name]
            payload = encode({
                "candidate": candidate, "command": COMMAND, "criterion": name, "exit": 0,
                "schema": "protasis-design-report/v1", "unit": item["unit"], "value": value,
            })
            relative = f"reports/selection/{candidate}-{name}.json"
            path = ROOT / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            if item["kind"] == "metric":
                state = "pass"
            elif item["comparator"] == "at-most":
                state = "pass" if value <= item["threshold"] else "fail"
            else:
                state = "pass" if value == item["threshold"] else "fail"
            record["results"].append({
                "candidate": candidate, "criterion": name,
                "report": {"path": relative, "sha256": hashlib.sha256(payload).hexdigest()},
                "state": state,
            })
    (ROOT / "design" / "model-observations.json").write_bytes(encode(observations))
    (ROOT / "design-evidence.json").write_bytes(encode(record))
    print(json.dumps({n: d["values"] for n, d in observations.items()}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
