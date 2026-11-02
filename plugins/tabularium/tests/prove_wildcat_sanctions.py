#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Execute one declared Wildcat sanctions conformance criterion."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=(
        "unique-key", "first-match", "adjacent-only"))
    parser.add_argument("--criterion", required=True, choices=(
        "semantic-conformance", "release-compatibility", "retained-coverage"))
    parser.add_argument("--report", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    source = Path(__file__).resolve().parent
    helper = source / "wildcat_sanctions_reports.py"
    if helper.is_symlink() or not helper.is_file():
        parser().exit(2, "report unavailable: helper source unavailable\n")
    sys.path.insert(0, str(source))
    import wildcat_sanctions_reports as reports
    if Path(reports.__file__).resolve() != source / "wildcat_sanctions_reports.py":
        parser().exit(2, "conformance unavailable: helper source differs\n")
    return reports.execute_proof(parser(), argv)


if __name__ == "__main__":
    raise SystemExit(main())
