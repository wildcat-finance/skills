#!/usr/bin/env python3
"""Run only the declared Step's in-process Wildcat V2 wrapper tests."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--step", required=True, type=int, choices=(1, 2, 3, 4))
    parser.add_argument("--report", required=True)
    parser.add_argument("--retained", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    from wrapper_reports import execute_report
    return execute_report(build_parser(), argv)


if __name__ == "__main__":
    # Elenchus starts every runner with PYTHONSAFEPATH=1, which leaves this
    # script's directory off sys.path, so the sibling import in main needs it.
    here = str(Path(__file__).resolve().parent)
    if here not in sys.path:
        sys.path.insert(0, here)
    raise SystemExit(main())
