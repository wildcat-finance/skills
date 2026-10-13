#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Run only the declared Step's in-process Wildcat batch tests."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True, type=int, choices=(1, 2, 3, 4))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    from wildcat_batch_reports import execute_report
    return execute_report(build_parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
