"""Rebuild the constructed fee specimen without changing its published bytes."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tests"))
import support
from wildcat_fee_public_fixtures import rebuild_fee_example

if __name__ == "__main__":
    raise SystemExit(rebuild_fee_example("wildcat-v1"))
