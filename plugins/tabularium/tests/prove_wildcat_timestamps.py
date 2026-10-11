#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Execute one bounded Wildcat archive timestamp proof case."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True, choices=(
        "scaffold", "capture", "mapping", "demonstration", "integration"))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    from wildcat_timestamp_reports import execute
    return execute(build_parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
