#!/usr/bin/env python3
"""Build docs/kickoff/1963/sources.json from the accepted inputs and public Git objects.

    python3 docs/kickoff/1963/evidence/producers/build_sources.py \\
        --corpus CORPUS --protocol CLONE --out NEW.json

CORPUS is the private accepted corpus (its inputs/wildcat-v1-ethereum-mainnet
directory). CLONE is wildcat-finance/wildcat-protocol with commits da74452a,
6164ddd4 and 488b30d0 and the lib/solady and lib/openzeppelin-contracts
submodules at the gitlinks da74452a records. Only digests, sizes and line
counts leave the corpus; no source text does. Each file's public binding is
checked here byte for byte, and the script stops on any mismatch it does not
already expect.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "scripts"))
import kickoff_xray_1963_bundle as v1  # noqa: E402

ROLES = (
    ("src/market/", "abstract market base inherited by WildcatMarket"),
    ("src/spherex/", "SphereX protection code inherited or called by this input's contexts"),
    ("src/interfaces/", "interface compiled for types, events and calls; not deployed on its own"),
    ("src/libraries/", "library code compiled into the contexts that use it"),
    ("src/lens/", "lens data library compiled into MarketLens"),
    ("src/ReentrancyGuard.sol", "reentrancy guard inherited by WildcatMarket"),
    ("lib/", "vendored library"),
)
DEPENDENCIES = (
    ("underlying ERC20 assets", "each market's asset is an arbitrary ERC20 chosen at deployment; its transfers, "
     "metadata answers and Transfer events are outside this map"),
    ("Chainalysis sanctions list", "the sentinel asks this external oracle at execution time; its answers decide "
     "the sanctioned branches and are not recorded here"),
    ("SphereX engine", "set at runtime by the SphereX operator; when nonzero it runs before and after guarded "
     "functions, may revert them and emits its own events outside this map"),
    ("controllers and markets named by callers at runtime", "lens queries, resetReserveRatio and escrow creation "
     "take addresses from the caller; the map covers only the V1 code those addresses are expected to run"),
)
EXCLUSIONS = (
    ("Wildcat V2 and unreleased v2.5 sources", "separate subjects; docs/kickoff/1363 maps V2 and stays unchanged"),
    ("test/, script/ and scripts/ trees of wildcat-protocol", "not compiled into any accepted input"),
    ("deployed addresses and bytecode identity", "the accepted registry at docs/kickoff/1359/targets.json owns the "
     "16 V1 entries; this map counts source contexts only"),
    ("IWildcatArchController event declarations no contract emits", "the deployed arch controller does not inherit "
     "the interface; docs/kickoff/1962 records the ten unused declarations and four disagreements"),
    ("init-code storage contracts", "the factory deploys two storage contracts that hold creation code; they have "
     "no callable surface of their own"),
)


def git_blob(protocol: Path, commit: str, path: str) -> bytes | None:
    if path.startswith("lib/"):
        target = protocol / path
        return target.read_bytes() if target.is_file() else None
    process = subprocess.run(["git", "-C", str(protocol), "show", f"{commit}:{path}"], capture_output=True, check=False)
    return process.stdout if process.returncode == 0 else None


def role(path: str) -> str:
    for prefix, text in ROLES:
        if path.startswith(prefix):
            return text
    raise SystemExit(f"no role for {path}")


def build(corpus: Path, protocol: Path) -> dict:
    contexts_by_input: dict[str, dict[str, str]] = {}
    for name, pin in v1.V1_CONTEXTS.items():
        contexts_by_input.setdefault(pin.input, {})[pin.source_path] = name
    context_home = {pin.source_path: (name, pin.input) for name, pin in v1.V1_CONTEXTS.items()}
    inputs = []
    for input_id, pin in sorted(v1.V1_INPUTS.items()):
        raw = v1.corpus_read(corpus, f"{v1.ACCEPTED_INPUTS}/{input_id}.json")
        assert v1.digest(raw) == pin.sha256, input_id
        value = json.loads(raw)
        commit = pin.commits[0]
        rows, differing = [], []
        for item in v1.source_projection(value, input_id):
            path = item["path"]
            content = value["sources"][path]["content"].encode()
            public = git_blob(protocol, commit, path)
            if public == content:
                binding = (f"byte-identical to the public submodule blob at the gitlink {v1.CORE_COMMIT[:8]} records"
                           if path.startswith("lib/") else f"byte-identical to {commit[:8]}:{path}")
            else:
                differing.append(path)
                binding = f"differs from {commit[:8]}; part of the accepted mixed-source exception"
            own = contexts_by_input.get(input_id, {}).get(path)
            if own:
                disposition, reason = "context", f"declares the {own} context bound to this input; {binding}"
            elif path in context_home:
                other, home = context_home[path]
                disposition = "support"
                reason = f"imported by this input's contexts; its {other} context binds to the {home} input; {binding}"
            else:
                disposition, reason = "support", f"{role(path)}; {binding}"
            rows.append({**item, "disposition": disposition, "reason": reason})
        if tuple(differing) != pin.differing:
            raise SystemExit(f"{input_id}: differing files {differing} do not match the pin {list(pin.differing)}")
        inputs.append({"id": input_id, "sha256": pin.sha256, "partition": pin.partition, "source_ref": pin.source_ref,
                       "binding_limit": pin.binding_limit, "commits": list(pin.commits),
                       "differing_files": list(pin.differing), "files": rows})
    return {"schema": "issue-1963-sources/v1", "repository": v1.REPOSITORY, "anchors": v1.V1_ANCHORS,
            "compiler": v1.V1_COMPILER, "inputs": inputs,
            "contexts": [{"contract": name, "input": pin.input, "source_path": pin.source_path, "kind": pin.kind}
                         for name, pin in sorted(v1.V1_CONTEXTS.items())],
            "dependencies": [{"subject": subject, "limit": limit} for subject, limit in DEPENDENCIES],
            "exclusions": [{"subject": subject, "reason": reason} for subject, reason in EXCLUSIONS]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--corpus", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    arguments = parser.parse_args()
    record = build(arguments.corpus.absolute(), arguments.protocol.absolute())
    v1.write_new(arguments.out, v1.encode(record))
    print(json.dumps({"inputs": {row["id"]: len(row["files"]) for row in record["inputs"]},
                      "out": os.fspath(arguments.out)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
