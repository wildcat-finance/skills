#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Resolve issue 1366 gates from current private bytes, never stored verdicts."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import preparation as p
import corpus_evidence as evidence

REGISTRY_SHA256 = "fef8a08e9cbb421ed7a45fa8d56ebec15fcb6b8fecd0e2a2c5571d7b2136103d"
EXAMPLES = {
    "aave067": "aave-v3-ethereum-main-source-map-2026-09-23/set-067",
    "aave068": "aave-v3-ethereum-main-source-map-2026-09-23/set-068",
    "aave101": "aave-v3-ethereum-main-source-map-2026-09-23/set-101",
    "euler001": "euler-ethereum-source-map-2026-09-28/set-001",
    "maple036": "maple-ethereum-source-map-2026-09-28/set-036",
    "maple037": "maple-ethereum-source-map-2026-09-28/set-037",
    "maple038": "maple-ethereum-source-map-2026-09-28/set-038",
    "maple039": "maple-ethereum-source-map-2026-09-28/set-039",
    "maple139": "maple-ethereum-source-map-2026-09-28/set-139",
}


def evaluate(case, candidate):
    """Recompute one declared gate; unavailable custody remains a failed gate."""
    p.require(case in ("production-conformance", "complete-input-custody", "venue-conformance"),
              "conformance-case")
    if candidate != "prepared-events":
        return False
    config = p.decode(p.read_regular(Path.cwd() / ".hexaemeron/evidence/lemma-1366-conformance.json"))
    p.closed(config, "schema root bundle", "conformance-config")
    p.require(config["schema"] == "lemma-1366-conformance/v1", "conformance-schema")
    bundle = evidence.load(config["bundle"], config["root"])
    p.require(bundle["registry"]["sha256"] == REGISTRY_SHA256, "conformance-registry")
    registry = evidence.load(bundle["registry"], config["root"])
    targets, inputs, _ = evidence.registry_join(registry, bundle["records"], config["root"])
    p.require(len(inputs) == 816 and sum(r["status"] == "resolved" for r in targets.values()) == 12,
              "conformance-denominator")
    if case == "complete-input-custody":
        state = evidence.custody(inputs, bundle["inputs"], config["root"])
        if state["missing"]:
            print("custody-incomplete: " + str(state["verified"]) + "/" + str(state["required"]), file=sys.stderr)
        return not state["missing"]
    if case == "production-conformance":
        p.require({row["id"]: row["input_id"] for row in bundle["partitions"]} == EXAMPLES,
                  "conformance-example-set")
        evidence.verify_bundle(bundle, config["root"])
        return True
    try:
        evidence.verify_bundle(bundle, config["root"], complete=True, full=True)
    except p.Refusal as exc:
        print(str(exc), file=sys.stderr)
        return False
    return True
