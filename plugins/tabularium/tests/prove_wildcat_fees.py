#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Execute one declared Wildcat fee conformance check."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Pin sibling imports under Python's safe-path and isolated modes.
sys.path.insert(0, str(Path(__file__).resolve().parent))


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=(
        "versioned-native", "in-place-native", "repayment-reuse"))
    parser.add_argument("--criterion", required=True, choices=(
        "semantic-conformance", "schema-parity", "legacy-conformance", "retained-conformance"))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    from wildcat_fee_reports import execute_proof
    return execute_proof(parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
