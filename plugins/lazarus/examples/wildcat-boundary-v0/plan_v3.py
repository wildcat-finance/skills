#!/usr/bin/env python3
"""Generate one Lazarus plan-v3 for a Wildcat estate at its capture boundary.

Inputs are the accepted value map under ``docs/kickoff/1384/`` and one probe
summary written by ``probe.py`` for the same generation, which supplies the
chain-derived inputs the map does not carry: each market's unpaid-batch queue
indices, each underlying token's balance layout and proxy pointers, and the
receipt witness target. The generator reaches no network, reads only the value
map and files inside its own directory, writes only to the caller-named
``--out`` path, which must not exist yet and must not be a symlink, and prints
the plan's size, digest and counts.

The request inventory is carried byte for byte: the first rows of ``requests``
are exactly the rows ``capture_requests.py`` expands, checked against the
digest in ``request-spec.json`` before anything is appended. A market whose
derived word count differs from what the probe read at the boundary refuses
the whole plan.

This copy is the maintained one. The study-time copy differed in two ways: it
accepted a probe summary from any path, and its elapsed limit defaulted to
7,200 s for both generations, so the study passed ``--max-elapsed-seconds
3600`` for V1 by hand. Here the default is per generation, so the commands in
the study's problem statement reproduce the committed digests unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from wildcat_slots import POINTER_SLOTS, balance_slot, market_words  # noqa: E402

KICKOFF = Path("docs/kickoff/1384")
ANCHOR_SOURCES = ("local-archive", "public-archive")
LIMITS = {
    "max_component_bytes": 134_217_728,
    "max_total_bytes": 536_870_912,
}
# The study's plan limits: twice the projected V1 capture of 25.9 s leaves
# 3,600 s generous, and the projected 598 s V2 capture sits under 7,200 s.
ELAPSED_LIMITS = {"v1": 3600, "v2": 7200}
HASH_SOURCE = (
    "Finalized boundary reported by the accepted Wildcat {generation} interval "
    "capture (release {release_id}; docs/kickoff/1384/values.md at Skills revision "
    "{revision}). Re-read by number from a local archive node and from the capture "
    "route on 2026-09-27; both returned this hash. Provider coordinates are not "
    "fixture components, and this note does not establish canonical-chain membership."
)


def load_inventory(generation: str) -> list[dict]:
    sys.path.insert(0, str(KICKOFF.resolve()))
    import capture_requests  # noqa: E402

    encoded = capture_requests.encoded_requests(generation)
    spec = json.loads((KICKOFF / "request-spec.json").read_text())["expanded_requests"][generation]
    digest = hashlib.sha256(encoded).hexdigest()
    if digest != spec["sha256"] or len(encoded) != spec["bytes"]:
        raise SystemExit("request inventory bytes disagree with request-spec.json")
    rows = [json.loads(line) for line in encoded.decode().splitlines()]
    if len(rows) != spec["count"]:
        raise SystemExit("request inventory count disagrees with request-spec.json")
    return rows


def build(generation: str, probe: dict, *, state_words_only: bool, max_elapsed: int) -> dict:
    scope = json.loads((KICKOFF / "scope.json").read_text())
    population = json.loads((KICKOFF / "population.json").read_text())[generation]
    anchor = scope["anchors"][generation]
    if probe["generation"] != generation or probe["block_number"] != anchor["number"]:
        raise SystemExit("probe summary is for another generation or block")
    block_hash = anchor["hash"].lower()
    if probe["block_hash"] != block_hash:
        raise SystemExit("probe summary names another block hash")
    subjects = scope["subjects"][generation]
    markets = [s["address"].lower() for s in subjects if s["role"] == "market"]

    requests = load_inventory(generation)
    witness = probe["receipt_witness"]
    requests.append({
        "name": "block-receipts", "method": "eth_getBlockReceipts",
        "params": [block_hash], "required": True, "evidence": "recorded-rpc",
    })
    requests.append({
        "name": "target-receipt", "method": "eth_getTransactionReceipt",
        "params": [witness["target_transaction_hash"]], "required": True,
        "evidence": "recorded-rpc",
    })
    requests.append({
        "name": "market-logs", "method": "eth_getLogs",
        "params": [{"address": markets, "blockHash": block_hash}], "required": True,
        "evidence": "recorded-rpc",
    })

    proof_targets = []
    counts = {"state": 0, "fifo_head": 0, "fifo_data": 0, "accounts": 0,
              "batches": 0, "statuses": 0, "balances": 0, "pointers": 0,
              "implementations": 0}
    for subject in subjects:
        address = subject["address"].lower()
        slots: set[str] = set()
        if subject["role"] == "market":
            words = market_words(generation, population[address], probe["fifo"][address])
            expected = probe["market_slots"][address]
            for group, values in words.items():
                if expected.get(group, 0) != len(values):
                    raise SystemExit(f"{address} {group}: generator derives {len(values)} words, probe read {expected.get(group, 0)}")
                if state_words_only and group not in ("state", "fifo_head"):
                    continue
                counts[group] += len(values)
                slots.update(values)
        proof_targets.append({"address": address, "slots": sorted(slots)})

    if not state_words_only:
        tokens = probe["tokens"]
        for token in sorted(tokens):
            record = tokens[token]
            layout = record["balance_slot"]
            if layout is None:
                raise SystemExit(f"token {token} has no recognised balance layout")
            holders = [m for m in markets if probe["assets_per_market"].get(m) == token]
            slots = {"0x" + balance_slot(m, layout).hex() for m in holders}
            counts["balances"] += len(slots)
            for pointer in record["pointers"].values():
                slots.add(pointer["slot"])
                counts["pointers"] += 1
            proof_targets.append({"address": token, "slots": sorted(slots)})
        # Two proxies may share one implementation; a target address is unique.
        listed = {target["address"] for target in proof_targets}
        for token in sorted(tokens):
            for pointer in tokens[token]["pointers"].values():
                implementation = pointer["address"].lower()
                if implementation in listed:
                    continue
                listed.add(implementation)
                proof_targets.append({"address": implementation, "slots": []})
                counts["implementations"] += 1
    for slot in POINTER_SLOTS.values():
        assert len(slot) == 66

    plan = {
        "schema_version": 3,
        "chain": {"chain_id": "0x1", "network": "ethereum-mainnet"},
        "block": {
            "number": hex(anchor["number"]),
            "hash": block_hash,
            "hash_source": HASH_SOURCE.format(
                generation=generation.upper(), release_id=anchor["release_id"],
                revision=scope["source_revision"],
            ),
        },
        "requests": requests,
        "proof_targets": proof_targets,
        "limits": {
            "max_requests": min(100_000, 2 * (len(requests) + 2 * len(proof_targets)) + 64),
            **LIMITS,
            "max_elapsed_seconds": max_elapsed,
        },
        "anchor_sources": [{"source_id": s} for s in sorted(ANCHOR_SOURCES)],
        "receipt_witness": {
            "block_receipts_request": "block-receipts",
            "target_receipt_lookup_request": "target-receipt",
            "target_transaction_index": hex(int(witness["target_transaction_index"])),
            "filtered_logs_request": "market-logs",
        },
    }
    plan["_counts"] = counts  # removed before writing; reported on stdout
    return plan


def refuse(message: str) -> int:
    print(f"refusing: {message}", file=sys.stderr)
    return 2


def checked_probe(supplied: Path) -> Path | None:
    """The probe summary must be a regular file that resolves inside this directory."""
    try:
        resolved = supplied.resolve(strict=True)
    except (OSError, RuntimeError):
        return None
    if not resolved.is_file() or not resolved.is_relative_to(HERE):
        return None
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generation", choices=("v1", "v2"), required=True)
    parser.add_argument("--probe", type=Path, required=True,
                        help="probe.py summary for this generation, inside this directory")
    parser.add_argument("--state-words-only", action="store_true",
                        help="prove only the market state and queue-head words")
    parser.add_argument("--max-elapsed-seconds", type=int, default=None,
                        help="plan limit; defaults to 3600 for v1 and 7200 for v2")
    parser.add_argument("--out", type=Path, required=True,
                        help="a fresh path in an existing directory; never a symlink")
    args = parser.parse_args()
    if not (KICKOFF / "request-spec.json").is_file():
        return refuse(f"{KICKOFF}/request-spec.json is not here; run from the repository root")
    probe_path = checked_probe(args.probe)
    if probe_path is None:
        return refuse("--probe must be a regular file inside the generator's own directory")
    if args.out.is_symlink():
        return refuse(f"{args.out} is a symlink")
    if os.path.lexists(args.out):
        return refuse(f"{args.out} already exists")
    if not args.out.parent.is_dir():
        return refuse(f"{args.out.parent} is not a directory")
    max_elapsed = args.max_elapsed_seconds
    if max_elapsed is None:
        max_elapsed = ELAPSED_LIMITS[args.generation]
    probe = json.loads(probe_path.read_text())
    plan = build(args.generation, probe, state_words_only=args.state_words_only,
                 max_elapsed=max_elapsed)
    counts = plan.pop("_counts")
    encoded = json.dumps(plan, indent=1, sort_keys=True).encode() + b"\n"
    with open(args.out, "xb") as handle:
        handle.write(encoded)
    print(json.dumps({
        "generation": args.generation,
        "state_words_only": args.state_words_only,
        "bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "requests": len(plan["requests"]),
        "proof_targets": len(plan["proof_targets"]),
        "slots": sum(len(t["slots"]) for t in plan["proof_targets"]),
        "words": counts,
        "max_slots_per_target": max(len(t["slots"]) for t in plan["proof_targets"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
