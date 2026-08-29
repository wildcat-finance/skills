#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""
Lemma standard-input builder

Build a solc standard-json input file from a directory of sources.

    python3 baseline/standard_input.py --src baseline/solidity/src --out input.json

Real deployments ship this file already: it is what verified contracts upload
for Etherscan, and it carries the exact compiler settings used for the deployed
bytecode. The baseline corpus has no deployment behind it, so it has to build
one, and this is also the shortest worked example of the format the Solidity
chunker consumes.

The file is derived rather than committed, because it embeds a copy of every
source. A committed copy would sit alongside `src/` with nothing keeping the two
in agreement, and the failure mode is silent: you edit a contract, the chunker
reads the stale copy out of the JSON, and every chunk cites bytes that are no
longer in the file it names.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


def build(src: pathlib.Path, prefix: str = "src") -> dict:
    files = sorted(src.glob("*.sol"))
    if not files:
        sys.exit(f"no .sol files under {src}")
    return {
        "language": "Solidity",
        "sources": {f"{prefix}/{p.name}": {"content": p.read_text()}
                    for p in files},
        "settings": {
            "optimizer": {"enabled": True, "runs": 200},
            "evmVersion": "paris",
            "outputSelection": {"*": {"*": ["abi", "evm.bytecode"],
                                      "": ["ast"]}},
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[2])
    ap.add_argument("--src", required=True, help="directory of .sol sources")
    ap.add_argument("--prefix", default="src",
                    help="source-unit path prefix inside the JSON")
    ap.add_argument("--out", required=True, help="standard-json output path")
    args = ap.parse_args()

    doc = build(pathlib.Path(args.src), args.prefix)
    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n")
    print(f"  {len(doc['sources'])} source(s) -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
