#!/usr/bin/env python3
"""Run one named checkpoint authority conformance gate; unsupported work refuses."""

import sys
from pathlib import Path

SCRIPTS = Path(__file__).absolute().parents[1] / "skills" / "fiat" / "scripts"
sys.path.insert(0, str(SCRIPTS))

from checkpoint_authority.conformance import main


if __name__ == "__main__":
    raise SystemExit(main())
