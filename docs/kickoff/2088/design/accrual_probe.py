#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Selection probe for Wildcat accrual and state-update canonical meaning (issue #2088).

An executable bounded model of four candidate row shapes, not product
conformance. The specimen logs are constructed in the pinned V1 and V2 market
emission order with the repository's own fixture helpers; none comes from a
retained capture. Each call writes one protasis-design-report/v1 object to the
caller-named --report path, which must not already exist.
"""

import argparse
import hashlib
import json
import os
import re
import shlex
import sys
from copy import deepcopy
from pathlib import Path


def _root():
    here = Path(__file__).resolve().parent
    for candidate in (here, *here.parents):
        if (candidate / "plugins" / "tabularium" / "scripts" / "tabularium_lib").is_dir():
            return candidate
    raise SystemExit("the repository root is not above " + str(here))


ROOT = _root()
sys.path.insert(0, str(ROOT / "plugins" / "tabularium" / "tests"))
sys.path.insert(0, str(ROOT / "plugins" / "tabularium" / "scripts"))

CANDIDATES = ("abi-named-amounts", "unit-named-amounts", "native-state-only", "envelope-native-state")
CRITERIA = {
    "numeric-fields-carried": ("boolean", "numeric_fields_carried"),
    "kinds-distinct": ("boolean", "kinds_distinct"),
    "schema-envelope-unchanged": ("boolean", "envelope_unchanged"),
    "existing-rows-unchanged": ("boolean", "existing_rows_unchanged"),
    "changed-event-fails-closed": ("boolean", "fails_closed"),
    "field-reads": ("count", "field_reads"),
    "new-row-bytes": ("bytes", "new_row_bytes"),
}
ACCRUAL = "InterestAndFeesAccrued(uint256,uint256,uint256,uint256,uint256,uint256)"
STATE = "StateUpdated(uint256,bool)"
FIELDS = {ACCRUAL: ("fromTimestamp", "toTimestamp", "scaleFactor", "baseInterestRay",
                    "delinquencyFeeRay", "protocolFees"),
          STATE: ("scaleFactor", "isDelinquent")}
NUMERIC = {ACCRUAL: ("scaleFactor", "baseInterestRay", "delinquencyFeeRay", "protocolFees"),
           STATE: ("scaleFactor",)}
NATIVE_STATE = {ACCRUAL: ("fromTimestamp", "toTimestamp"), STATE: ("isDelinquent",)}
UNDERLYING = ("protocolFees",)
EXISTING_KINDS = frozenset(("assets", "scaled-claims", "normalized-claims", "market-token-claims",
                            "burned-scaled-claims", "reserved-assets", "market-token-assets",
                            "wrapper-shares"))
RAY = 10 ** 27
EXPIRY = 1_700_000_000


class Refusal(Exception):
    """A candidate refused a definition whose declared fields moved."""


def kebab(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "-", name).lower()


def specimen(venue, asset=True):
    """One source-ordered state write: accrual to an expiry, accrual to now, a deposit, the write."""
    from wildcat_v3_fixtures import ACCOUNT, ZERO, constructed_inputs, log, record

    contexts, _ = constructed_inputs(venue)
    if not asset:
        contexts = deepcopy(contexts)
        for context in contexts.values():
            if context["role"] == "market":
                context["asset"] = None
    raws = [
        log(ACCRUAL, (), (EXPIRY - 3600, EXPIRY, RAY + 5 * 10 ** 22, 4 * 10 ** 22, 10 ** 22, 7), index=0),
        log(ACCRUAL, (), (EXPIRY, EXPIRY + 60, RAY + 6 * 10 ** 22, 10 ** 21, 0, 0), index=1),
        log("Transfer(address,address,uint256)", (ZERO, ACCOUNT), (100,), index=2),
        log("Deposit(address,uint256,uint256)", (ACCOUNT,), (100, 94), index=3),
        log(STATE, (), (RAY + 6 * 10 ** 22, 1), index=4),
        log(STATE, (), (RAY + 6 * 10 ** 22, 0), index=5),
    ]
    return contexts, [record(raw) for raw in raws]


def decoded_records(venue, asset=True):
    from tabularium_lib.wildcat_rows import map_records

    contexts, records = specimen(venue, asset)
    result = map_records(venue, contexts, records)
    rows = [m for m in result["mapping_records"] if m["signature"] in (ACCRUAL, STATE)]
    asset_value = next(c["asset"] for c in contexts.values() if c["role"] == "market")
    return rows, asset_value


def build(candidate, mapping, asset):
    """Return (fragment, gaps, reads) for one decoded record under one candidate."""
    signature = mapping["signature"]
    names = tuple(item["name"] for item in mapping["definition"]["abi"]["inputs"])
    if names != FIELDS[signature]:
        raise Refusal("declared fields moved for " + signature)
    values = mapping["decoded"]
    action = "interest-and-fees-accrued" if signature == ACCRUAL else "state-updated"
    gaps = ["attribution:%s:actor" % action]
    reads = 0
    amounts = []
    fragment = {"schema_version": 3}
    if candidate in ("abi-named-amounts", "envelope-native-state", "unit-named-amounts"):
        for field in NUMERIC[signature]:
            reads += 1
            if candidate == "unit-named-amounts":
                kind = "assets" if field in UNDERLYING else "ray"
            else:
                kind = kebab(field)
            amounts.append({"kind": kind, "base_units": values[field],
                            "asset": asset if field in UNDERLYING else None})
    fragment["amounts"] = amounts
    if candidate == "envelope-native-state":
        fragment["schema_version"] = 4
        fragment["native_state"] = {}
        for field in NATIVE_STATE[signature]:
            reads += 1
            fragment["native_state"][field] = values[field]
    if any(a["asset"] is None and a["kind"] in ("assets", "protocol-fees") for a in amounts):
        gaps.append("attribution:%s:asset" % action)
    return fragment, gaps, reads


def all_built(candidate, asset=True):
    built = []
    for venue in ("wildcat-v1", "wildcat-v2"):
        rows, asset_value = decoded_records(venue, asset)
        for mapping in rows:
            built.append((mapping, build(candidate, mapping, asset_value)))
    return built


def numeric_fields_carried(candidate):
    for mapping, (fragment, _, _) in all_built(candidate):
        signature = mapping["signature"]
        kinds = [a["kind"] for a in fragment["amounts"]]
        if len(kinds) != len(NUMERIC[signature]):
            return False
        for field in NUMERIC[signature]:
            matches = [a for a in fragment["amounts"] if a["kind"] == kebab(field)]
            if len(matches) != 1 or matches[0]["base_units"] != mapping["decoded"][field]:
                return False
        if any(kebab(field) in kinds for field in NATIVE_STATE[signature]):
            return False
    return True


def kinds_distinct(candidate):
    for _, (fragment, _, _) in all_built(candidate):
        kinds = [a["kind"] for a in fragment["amounts"]]
        if len(set(kinds)) != len(kinds) or set(kinds) & EXISTING_KINDS:
            return False
    return True


def envelope_unchanged(candidate):
    return all(fragment["schema_version"] == 3 and set(fragment) == {"schema_version", "amounts"}
               for _, (fragment, _, _) in all_built(candidate))


def existing_rows_unchanged(candidate):
    """Rows of the twenty-five released rules stay byte-identical under the candidate."""
    from tabularium_lib.core import canonical_json
    from tabularium_lib.wildcat_rows import map_records
    from wildcat_v3_fixtures import batch_inputs, constructed_inputs

    for venue in ("wildcat-v1", "wildcat-v2"):
        before = list(map_records(venue, *constructed_inputs(venue, routing=True))["events"])
        before += list(map_records(venue, *batch_inputs(venue))["events"])
        after = []
        for row in before:
            row = json.loads(canonical_json(row))
            if candidate == "envelope-native-state":
                row["schema_version"] = 4
                row["native_state"] = None
            after.append(row)
        if [canonical_json(r) for r in before] != [canonical_json(r) for r in after]:
            return False
    return True


def fails_closed(candidate):
    """A moved declaration refuses, a malformed log refuses and an unknown asset stays a gap."""
    from tabularium_lib.core import TabulariumError
    from tabularium_lib.wildcat_rows import map_records
    from wildcat_v3_fixtures import log, record

    rows, asset_value = decoded_records("wildcat-v2")
    moved = deepcopy(next(m for m in rows if m["signature"] == ACCRUAL))
    inputs = moved["definition"]["abi"]["inputs"]
    inputs[3]["name"], inputs[4]["name"] = inputs[4]["name"], inputs[3]["name"]
    try:
        build(candidate, moved, asset_value)
        return False
    except Refusal:
        pass
    for venue in ("wildcat-v1", "wildcat-v2"):
        contexts, _ = specimen(venue)
        bad_bool = log(STATE, (), (RAY, 2), index=0)
        short = log(ACCRUAL, (), (1, 2, RAY, 0, 0), index=0)
        for raw in (bad_bool, short):
            try:
                map_records(venue, contexts, [record(raw)])
                return False
            except TabulariumError:
                pass
    for _, (fragment, gaps, _) in all_built(candidate, asset=False):
        fees = [a for a in fragment["amounts"] if a["kind"] in ("assets", "protocol-fees")]
        if fees and (fees[0]["asset"] is not None or not any(g.endswith(":asset") for g in gaps)):
            return False
    return True


def field_reads(candidate):
    return sum(reads for _, (_, _, reads) in all_built(candidate))


def new_row_bytes(candidate):
    from tabularium_lib.core import canonical_json

    return sum(len(canonical_json(fragment)) for _, (fragment, _, _) in all_built(candidate))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if os.path.lexists(args.report):
        parser.exit(2, "report path already exists: " + args.report + "\n")
    unit, function = CRITERIA[args.criterion]
    value = globals()[function](args.candidate)
    command = shlex.join(["python3", ".hexaemeron/design/accrual_probe.py", "--candidate", args.candidate,
                          "--criterion", args.criterion, "--report", args.report])
    payload = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
               "criterion": args.criterion, "value": value, "unit": unit, "command": command, "exit": 0}
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    print(json.dumps({"report": args.report, "value": value, "sha256": hashlib.sha256(data).hexdigest()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
