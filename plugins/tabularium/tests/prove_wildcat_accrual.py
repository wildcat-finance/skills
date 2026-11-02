#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Execute one declared Wildcat accrual and state-update conformance check."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=(
        "abi-named-amounts", "unit-named-amounts", "native-state-only", "envelope-native-state"))
    parser.add_argument("--criterion", required=True, choices=(
        "semantic-conformance", "schema-parity", "retained-conformance"))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    # Elenchus starts this runner with PYTHONSAFEPATH=1, which leaves the
    # script's own directory off sys.path, so put it first before the import.
    here = str(Path(__file__).resolve().parent)
    if sys.path[:1] != [here]:
        sys.path.insert(0, here)
    from wildcat_accrual_reports import execute_proof
    return execute_proof(build_parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
