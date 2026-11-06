#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Execute one declared Wildcat withdrawal-batch conformance check."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=(
        "adjacent-burn", "unique-value-burn", "all-batch-events", "envelope-batch-field"))
    parser.add_argument("--criterion", required=True, choices=(
        "semantic-conformance", "schema-parity", "retained-conformance"))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    from wildcat_batch_reports import execute_proof
    return execute_proof(build_parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
