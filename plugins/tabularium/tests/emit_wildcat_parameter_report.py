#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Run the declared Step's in-process Wildcat parameter tests."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

# Explicit sibling resolution also works with Python safe-path and isolation.
sys.path.insert(0, str(Path(__file__).resolve().parent))


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True, type=int, choices=(1, 2, 3))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    from wildcat_parameter_reports import execute_report
    return execute_report(parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
