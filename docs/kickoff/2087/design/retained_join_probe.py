"""Retained-release closure probe for the withdrawal-batch burn join (#2087).

Rebuilds both retained Wildcat raw releases from the staging trees named by
``ALEXANDRIA_WILDCAT_V1_STAGING`` and ``ALEXANDRIA_WILDCAT_V2_STAGING`` through
the public Alexandria example builders, builds each canonical release with the
installed ``wildcat-canonical`` command into a fresh private temporary
directory, and evaluates one candidate pairing rule over every market
transaction. The report carries a boolean, the raw release identifiers and the
canonical digests of the rebuilt inputs; it carries no count. Every temporary
tree is removed before exit.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ZERO = "0x" + "00" * 20
PAYMENT = "WithdrawalBatchPayment(uint256,uint256,uint256)"
TRANSFER = "Transfer(address,address,uint256)"
BATCH = {
    "WithdrawalBatchCreated(uint256)", PAYMENT,
    "WithdrawalBatchExpired(uint256,uint256,uint256,uint256)", "WithdrawalBatchClosed(uint256)",
}
CANDIDATES = ("adjacent-burn", "unique-value-burn", "all-batch-events", "envelope-batch-field")
GENERATIONS = (("wildcat-v1", "ALEXANDRIA_WILDCAT_V1_STAGING", "wildcat-v1-interval-v0"),
               ("wildcat-v2", "ALEXANDRIA_WILDCAT_V2_STAGING", "wildcat-v2-interval-v0"))


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _run(argv):
    completed = subprocess.run(argv, cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if completed.returncode != 0:
        tail = completed.stderr.decode(errors="replace").strip().splitlines()[-1:]
        raise SystemExit("rebuild step failed: " + " ".join(tail))


def rebuild(generation, example, scratch):
    raw = scratch / (generation + "-raw")
    demo = ROOT / "plugins" / "alexandria" / "examples" / example / "demo.py"
    _run([sys.executable, str(demo), "build", "--output", str(raw)])
    canonical = scratch / (generation + "-canonical")
    cli = ROOT / "plugins" / "tabularium" / "scripts" / "tabularium.py"
    _run([sys.executable, str(cli), "wildcat-canonical", "--alexandria-release",
          str(raw / "release"), "--release", "probe-" + generation, "--out", str(canonical)])
    return canonical


def closure(candidate, source):
    """True when every payment joins one burn and every market burn is claimed once."""
    by_tx = {}
    for record in source["mapping_records"]:
        if record["emitter_role"] != "market" or record["signature"] not in BATCH | {TRANSFER}:
            continue
        raw = record["native_record"]
        decoded = record["decoded"] or {}
        kind = None
        if record["signature"] == PAYMENT:
            kind = "payment"
        elif record["signature"] in BATCH:
            kind = "batch"
        elif decoded.get("from", "").lower() == raw["address"].lower() and decoded.get("to", "").lower() == ZERO:
            kind = "burn"
        if kind is None:
            continue
        value = decoded.get("normalizedAmountPaid") if kind == "payment" else decoded.get("value")
        by_tx.setdefault((raw["transactionHash"].lower(), raw["address"].lower()), []).append(
            (int(raw["logIndex"], 16), kind, str(value)))
    for items in by_tx.values():
        items.sort()
        index = {i: (k, v) for i, k, v in items}
        burns = [i for i, k, _ in items if k == "burn"]
        payments = [i for i, k, _ in items if k == "payment"]
        claims = {}
        for i in payments:
            if candidate in ("adjacent-burn", "envelope-batch-field"):
                prev = index.get(i - 1)
                if prev is None or prev[0] != "burn" or prev[1] != index[i][1]:
                    return False
                claims[i - 1] = claims.get(i - 1, 0) + 1
            elif candidate == "unique-value-burn":
                matches = [b for b in burns if index[b][1] == index[i][1]]
                same = [p for p in payments if index[p][1] == index[i][1]]
                if len(matches) != 1 or len(same) != 1:
                    return False
                claims[matches[0]] = claims.get(matches[0], 0) + 1
            elif candidate == "all-batch-events":
                earlier = [b for b in burns if b < i]
                if not earlier:
                    return False
                claims[earlier[-1]] = claims.get(earlier[-1], 0) + 1
        if any(claims.get(b, 0) != 1 for b in burns):
            return False
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=("retained-join-closure",))
    parser.add_argument("--report", required=True)
    args = parser.parse_args()
    if os.path.lexists(args.report):
        parser.exit(2, "report path already exists: " + args.report + "\n")
    for _, variable, _ in GENERATIONS:
        if not os.environ.get(variable):
            parser.exit(2, variable + " is not set\n")
    # Tabularium refuses a release path that crosses a symlink, so the scratch
    # root is the resolved temporary directory, not its symlinked alias.
    scratch = Path(tempfile.mkdtemp(prefix="fiat-2087-retained-probe-",
                                    dir=str(Path(tempfile.gettempdir()).resolve())))
    os.chmod(scratch, 0o700)
    observations = []
    try:
        value = True
        for generation, _, example in GENERATIONS:
            canonical = rebuild(generation, example, scratch)
            source = json.loads((canonical / "source.json").read_bytes())
            value = closure(args.candidate, source) and value
            observations.append({"generation": generation,
                                 "raw_release_id": source["raw_release"]["release_id"],
                                 "canonical_sha256": sha256_file(canonical / "events.jsonl"),
                                 "coverage_sha256": sha256_file(canonical / "coverage.json")})
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    command = "python3 .hexaemeron/design/retained_join_probe.py --candidate %s --criterion %s --report %s" % (
        args.candidate, args.criterion, args.report)
    payload = {"schema": "protasis-design-report/v1", "candidate": args.candidate,
               "criterion": args.criterion, "value": value, "unit": "boolean", "command": command, "exit": 0}
    data = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode()
    Path(args.report).parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(args.report, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(data)
    sidecar = Path(args.report).with_suffix(".observations.json")
    sidecar_data = (json.dumps({"schema": "fiat-2087-retained-join-observations/v1", "candidate": args.candidate,
                                "inputs": observations}, indent=2, sort_keys=True) + "\n").encode()
    fd = os.open(sidecar, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(sidecar_data)
    print(json.dumps({"report": args.report, "value": value, "sha256": hashlib.sha256(data).hexdigest()}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
