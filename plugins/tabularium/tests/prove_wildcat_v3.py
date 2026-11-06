#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Execute one declared Wildcat canonical-v3 conformance check."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=(
        "view-projection", "topic-only", "role-qualified"))
    parser.add_argument("--criterion", required=True, choices=(
        "semantic-conformance", "schema-parity", "release-reproduction"))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    from wildcat_v3_proofs import execute
    return execute(build_parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
