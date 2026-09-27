#!/usr/bin/env python3
"""Give every row of the Wildcat value map one evidence class for one estate.

For each of the 61 rows in ``docs/kickoff/1384/values.json`` the report names
exactly one class: ``proved`` when every number behind the row is a storage
word or code the fixture proves under EIP-1186, ``header-bound`` when it is a
field of the header, ``recorded`` when only an exact recorded response backs
it, and ``unsupported`` when the map marks it so or the row is not in the
estate. A proved row lists the word groups that back it, each with its target
and slot counts, its first entry and a digest over the whole group, so a
reader can recompute it from the regenerated plan. A row's recorded views are
listed the same way, by request family, with the count of those calls whose
recorded outcome is an error. The one V1 batch pair whose getter simulates an
expired pending batch carries its differing recorded view on the three batch
rows and on ``native.availableWithdrawal``, whose getter takes the batch from
the same simulation.

The generator reads the value map, the probe summary and the committed
capture record, checks the plan it is given against the digest ``plans.json``
records, reaches no network, and writes only to a fresh ``--out``. Every word
it names is checked to be a slot the plan proves, and the words it derives
must account for every slot in the plan.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parents[1] / "scripts"
for entry in (HERE, SCRIPTS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
from lazarus_lib.records import request_key  # noqa: E402
from wildcat_slots import balance_slot, market_words  # noqa: E402

KICKOFF = Path("docs/kickoff/1384")
SCHEMA = "wildcat-boundary-relations/v1"
CLASSES = ("proved", "header-bound", "recorded", "unsupported")
DIGEST_RULE = (
    "sha256 over the group's entries, 'address:slot' for words, 'address' for "
    "code and the request name for calls, sorted, joined by newlines, with a "
    "trailing newline"
)
STATE, HEADER, CODE, BALANCE = "state", "header", "code", "balances"
ACCOUNTS, BATCHES, STATUSES, FIFO_HEAD, FIFO_DATA = (
    "accounts", "batches", "statuses", "fifo_head", "fifo_data",
)
# A currentState() derivation reads the four state words, accrues to the
# header timestamp, and takes its rates from immutables in the market's code.
DERIVED = (STATE, HEADER, CODE)
# getAvailableWithdrawalAmount runs the same _calculateCurrentState() and, when
# the expiry asked for is the expired pending batch, takes that batch from the
# simulation, which pays it from the market's asset balance; only then does it
# read the status word and the batch words.
AVAILABLE_ROW = "native.availableWithdrawal"
PROOF_INPUTS = {
    "credit.asset": (CODE,),
    "credit.totalAssets": (BALANCE,),
    "credit.totalLenderClaims": DERIVED,
    "credit.accruedFees": DERIVED,
    "credit.observedAt": (HEADER,),
    "native.supply": DERIVED,
    "native.scaledSupply": DERIVED,
    "native.liabilities": DERIVED,
    "native.requiredLiquidity": DERIVED,
    "native.arithmeticBorrowable": DERIVED + (BALANCE,),
    "native.collectableFees": DERIVED + (BALANCE,),
    "native.depositCapacity": DERIVED,
    "native.assetDecimals": (CODE,),
    "native.delinquencyFee": (CODE,),
    "native.gracePeriod": (CODE,),
    "native.batchDuration": (CODE,),
    "native.unpaidExpiries": (FIFO_HEAD, FIFO_DATA),
    "native.scaledBalance": (ACCOUNTS,),
    "native.balance": (ACCOUNTS,) + DERIVED,
    "native.batch.scaledTotalAmount": (BATCHES,),
    "native.batch.scaledAmountBurned": (BATCHES,),
    "native.batch.normalizedAmountPaid": (BATCHES,),
    "native.account.scaledAmount": (STATUSES,),
    "native.account.normalizedAmountWithdrawn": (STATUSES,),
    AVAILABLE_ROW: (STATUSES, BATCHES) + DERIVED + (BALANCE,),
    "native.outstandingDebt": DERIVED + (BALANCE,),
    "config.protocolFeeBips": (CODE,),
    "config.borrower": (CODE,),
    "config.feeRecipient": (CODE,),
    "config.sentinel": (CODE,),
    "config.controller": (CODE,),
    "config.factory": (CODE,),
    "config.hooks": (CODE,),
}
BATCH_FIELDS = {
    "native.batch.scaledTotalAmount": 0,
    "native.batch.scaledAmountBurned": 1,
    "native.batch.normalizedAmountPaid": 2,
}
SIMULATION_CAUSE = (
    "getWithdrawalBatch simulates the expired pending batch as paid; the stored "
    "words hold the pre-payment amounts"
)
AVAILABLE_SIMULATION_CAUSE = (
    "getAvailableWithdrawalAmount takes the expired pending batch from the same "
    "simulation, so for these accounts it derives from the simulated "
    "normalizedAmountPaid and scaledTotalAmount and not from the stored batch words"
)
AVAILABLE_BATCH_FIELDS = {"scaledTotalAmount": 0, "normalizedAmountPaid": 2}


def refuse(message: str) -> int:
    print(f"refusing: {message}", file=sys.stderr)
    return 2


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def group_digest(entries) -> str:
    return sha256_bytes(("\n".join(sorted(entries)) + "\n").encode("utf-8"))


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def derive_words(generation: str, plan: dict, probe: dict, population: dict, markets: list[str]) -> dict:
    """Every proved word by group, each checked against the plan's targets."""
    targets = {t["address"].lower(): set(t["slots"]) for t in plan["proof_targets"]}
    groups: dict[str, set[str]] = {
        g: set() for g in (STATE, FIFO_HEAD, FIFO_DATA, ACCOUNTS, BATCHES, STATUSES,
                           BALANCE, "pointers", "implementations")
    }
    for market in markets:
        words = market_words(generation, population[market], probe["fifo"][market])
        for group, slots in words.items():
            for slot in slots:
                if slot not in targets.get(market, ()):
                    raise SystemExit(f"{market} {group}: derived word is not a plan target")
                groups[group].add(f"{market}:{slot}")
    for token in sorted(probe["tokens"]):
        record = probe["tokens"][token]
        holders = [m for m in markets if probe["assets_per_market"].get(m) == token]
        for holder in holders:
            slot = "0x" + balance_slot(holder, record["balance_slot"]).hex()
            if slot not in targets.get(token, ()):
                raise SystemExit(f"{token}: balance word is not a plan target")
            groups[BALANCE].add(f"{token}:{slot}")
        for pointer in record["pointers"].values():
            if pointer["slot"] not in targets.get(token, ()):
                raise SystemExit(f"{token}: pointer word is not a plan target")
            groups["pointers"].add(f"{token}:{pointer['slot']}")
            implementation = pointer["address"].lower()
            if implementation not in targets:
                raise SystemExit(f"{implementation}: implementation is not a plan target")
            groups["implementations"].add(implementation)
    derived = sum(len(v) for g, v in groups.items() if g != "implementations")
    planned = sum(len(v) for v in targets.values())
    if derived != planned:
        raise SystemExit(f"derived {derived} words but the plan proves {planned} slots")
    groups[CODE] = set(markets)
    for market in markets:
        if market not in targets:
            raise SystemExit(f"{market}: market code is not a plan target")
    return groups


def word_item(group: str, entries: set[str]) -> dict:
    ordered = sorted(entries)
    first = ordered[0].split(":", 1)
    item = {
        "kind": "proof-target",
        "words": group,
        "targets": len({e.split(":", 1)[0] for e in ordered}),
        "slots": 0 if group in (CODE, "implementations") else len(ordered),
        "first": {"address": first[0]},
        "sha256": group_digest(ordered),
    }
    if len(first) == 2:
        item["first"]["slot"] = first[1]
    return item


def index_requests(plan: dict, selectors: dict, failures: set[str]) -> dict:
    """Request names by family, with the count whose recorded outcome errs."""
    by_selector = {v.lower(): k for k, v in selectors.items()}
    families: dict[str, dict] = {}
    for request in plan["requests"]:
        method = request["method"]
        if method == "eth_call":
            data = request["params"][0]["data"].lower()
            signature = by_selector.get(data[:10])
            if signature is None:
                continue
            key = signature
        else:
            key = method
        family = families.setdefault(key, {"method": method, "names": [], "errors": 0})
        family["names"].append(request["name"])
        if request_key(method, request["params"]) in failures:
            family["errors"] += 1
    return families


def request_item(signature: str, families: dict, selectors: dict) -> dict:
    family = families.get(signature)
    if family is None:
        raise SystemExit(f"{signature}: no request in the plan backs this view")
    names = sorted(family["names"])
    item = {
        "kind": "request",
        "method": family["method"],
        "requests": len(names),
        "recorded_errors": family["errors"],
        "first": names[0],
        "sha256": group_digest(names),
    }
    if family["method"] == "eth_call":
        item["signature"] = signature
        item["selector"] = selectors[signature]
    return item


def simulated_available_view(mismatch: dict, population: dict) -> dict:
    """The simulated pair as getAvailableWithdrawalAmount reads it.

    The accounts are those holding a withdrawal status at that expiry in the
    value map's population; ``stored`` and ``view`` are the two batch fields
    the derivation reads, so ``differs`` says whether a number recomputed from
    the stored words can equal the recorded view for them.
    """
    market = mismatch["market"].lower()
    expiry = int(mismatch["expiry"])
    accounts = sorted(
        pair["account"].lower()
        for pair in population[market]["account_batches"]
        if int(pair["expiry"]) == expiry
    )
    stored = {name: mismatch["stored"][index] for name, index in AVAILABLE_BATCH_FIELDS.items()}
    view = {name: mismatch["view"][index] for name, index in AVAILABLE_BATCH_FIELDS.items()}
    return {
        "market": market, "expiry": expiry, "accounts": accounts,
        "stored": stored, "view": view, "differs": stored != view,
        "cause": AVAILABLE_SIMULATION_CAUSE,
    }


def classify(row: dict, generation: str) -> tuple[str, str | None]:
    if generation not in row["generations"]:
        return "unsupported", "not-in-generation"
    if row["status"].startswith("unsupported"):
        return "unsupported", row["status"]
    if row["id"] == "credit.observedAt":
        return "header-bound", None
    return "proved", None


def build(generation: str, plan: dict, capture_record: dict) -> dict:
    values = read_json(KICKOFF / "values.json")
    scope = read_json(KICKOFF / "scope.json")
    population = read_json(KICKOFF / "population.json")[generation]
    selectors = read_json(KICKOFF / "selectors.json")
    probe = read_json(HERE / f"probe-{generation}.json")
    anchor = scope["anchors"][generation]
    if int(plan["block"]["number"], 16) != anchor["number"] or plan["block"]["hash"] != anchor["hash"].lower():
        raise SystemExit("plan block disagrees with the value map anchor")
    if probe["generation"] != generation or probe["block_hash"] != plan["block"]["hash"]:
        raise SystemExit("probe summary is for another generation or block")
    markets = [s["address"].lower() for s in scope["subjects"][generation] if s["role"] == "market"]
    groups = derive_words(generation, plan, probe, population, markets)
    failures = set(capture_record["verify"]["manifest"]["optional_failures"])
    families = index_requests(plan, selectors, failures)
    header_component = next(
        c for c in capture_record["fixture"]["components"] if c["path"] == "header.json"
    )
    mismatches = probe["agreement"]["batches_mismatch"]

    rows = []
    counts = {name: 0 for name in CLASSES}
    for row in values["rows"]:
        identity = row["id"]
        klass, reason = classify(row, generation)
        counts[klass] += 1
        entry = {"id": identity, "class": klass, "proof": [], "recorded": []}
        if klass == "unsupported":
            entry["reason"] = reason
            rows.append(entry)
            continue
        inputs = (STATE,) if identity.startswith("state.") else PROOF_INPUTS[identity]
        for group in inputs:
            if group == HEADER:
                entry["proof"].append({
                    "kind": "header", "field": "timestamp", "component": "header.json",
                    "sha256": header_component["sha256"],
                })
                continue
            if not groups[group]:
                continue
            entry["proof"].append(word_item(group, groups[group]))
            if group == BALANCE:
                for extra in ("pointers", "implementations"):
                    if groups[extra]:
                        entry["proof"].append(word_item(extra, groups[extra]))
        for signature in row["source"]["requests"]:
            entry["recorded"].append(request_item(signature, families, selectors))
        if identity in BATCH_FIELDS:
            field = BATCH_FIELDS[identity]
            entry["differing_recorded_view"] = [
                {
                    "market": m["market"], "expiry": m["expiry"],
                    "stored": m["stored"][field], "view": m["view"][field],
                    "differs": m["stored"][field] != m["view"][field],
                    "cause": SIMULATION_CAUSE,
                }
                for m in mismatches
            ]
        if identity == AVAILABLE_ROW:
            entry["differing_recorded_view"] = [
                simulated_available_view(m, population) for m in mismatches
            ]
        if not entry["proof"]:
            raise SystemExit(f"{identity}: a {klass} row has no backing entry")
        rows.append(entry)
    if len(rows) != 61:
        raise SystemExit(f"value map has {len(rows)} rows, not 61")
    return {
        "schema": SCHEMA,
        "generation": generation,
        "block": {"number": anchor["number"], "hash": plan["block"]["hash"]},
        "plan_sha256": capture_record["plan"]["sha256"],
        "capture_record": {
            "path": f"capture-{generation}.json",
            "sha256": capture_record["_sha256"],
            "fixture_digest": capture_record["fixture"]["fixture_digest"],
        },
        "digest_rule": DIGEST_RULE,
        "markets": len(markets),
        "words": {g: len(v) for g, v in groups.items() if g != CODE},
        "differing_recorded_views": len(mismatches),
        "classes": counts,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--generation", choices=("v1", "v2"), required=True)
    parser.add_argument("--plan", type=Path, required=True,
                        help="a plan regenerated to the digest plans.json records")
    parser.add_argument("--capture-record", type=Path, default=None,
                        help="the committed capture record; defaults to capture-<generation>.json here")
    parser.add_argument("--out", type=Path, required=True,
                        help="a fresh path in an existing directory; never a symlink")
    args = parser.parse_args()
    if not (KICKOFF / "values.json").is_file():
        return refuse(f"{KICKOFF}/values.json is not here; run from the repository root")
    if args.out.is_symlink():
        return refuse(f"{args.out} is a symlink")
    if os.path.lexists(args.out):
        return refuse(f"{args.out} already exists")
    if not args.out.parent.is_dir():
        return refuse(f"{args.out.parent} is not a directory")
    expected = read_json(HERE / "plans.json")["plans"][args.generation]
    if args.plan.is_symlink() or not args.plan.is_file():
        return refuse(f"{args.plan} is not a regular file")
    plan_bytes = args.plan.read_bytes()
    if len(plan_bytes) != expected["bytes"] or sha256_bytes(plan_bytes) != expected["sha256"]:
        return refuse(f"{args.plan} is not the {args.generation} plan that plans.json records")
    record_path = args.capture_record or HERE / f"capture-{args.generation}.json"
    if record_path.is_symlink() or not record_path.is_file():
        return refuse(f"{record_path} is not a regular file")
    record_bytes = record_path.read_bytes()
    capture_record = json.loads(record_bytes)
    if capture_record.get("generation") != args.generation or capture_record.get("plan", {}).get("sha256") != expected["sha256"]:
        return refuse("the capture record is for another generation or plan")
    capture_record["_sha256"] = sha256_bytes(record_bytes)
    report = build(args.generation, json.loads(plan_bytes), capture_record)
    encoded = json.dumps(report, indent=1, sort_keys=True).encode("utf-8") + b"\n"
    with open(args.out, "xb") as handle:
        handle.write(encoded)
    print(json.dumps({
        "generation": args.generation,
        "rows": len(report["rows"]),
        "classes": report["classes"],
        "bytes": len(encoded),
        "sha256": sha256_bytes(encoded),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
