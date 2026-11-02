#!/usr/bin/env python3
"""Rebuild the constructed wildcat-v2 accrual specimen and compare every file."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
from wildcat_accrual_public_fixtures import rebuild_example


if __name__ == "__main__":
    raise SystemExit(rebuild_example("wildcat-v2"))
