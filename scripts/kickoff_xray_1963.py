#!/usr/bin/env python3
"""Check, demonstrate and report the Wildcat V1 map bundle for #1963.

    python3 scripts/kickoff_xray_1963.py check [--bundle DIR]
    python3 scripts/kickoff_xray_1963.py design-report --candidate ID --criterion ID --report NEW.json [--bundle DIR]
    python3 scripts/kickoff_xray_1963.py demo --bundle DIR --report NEW.json
    python3 scripts/kickoff_xray_1963.py admit --inputs DIR --report NEW.json
    python3 scripts/kickoff_xray_1963.py derive --inputs DIR --out NEW.json
    python3 scripts/kickoff_xray_1963.py manifest [--bundle DIR]

This parser is a registered runbook interface, bound by digest at Step 1's
push. Keep it declarative: every behaviour lives in
scripts/kickoff_xray_1963_bundle.py.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kickoff_xray_1963_bundle as bundle  # noqa: E402


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("check", "design-report", "demo", "admit", "derive", "manifest"))
    parser.add_argument("--bundle", type=Path, help="bundle directory; defaults to docs/kickoff/1963")
    parser.add_argument("--candidate", choices=("shared-input-index", "component-copies"))
    parser.add_argument("--criterion", choices=("checked-scaffold", "reviewed-map", "offline-demonstration"))
    parser.add_argument("--report", type=Path, help="new report path; an existing path is refused")
    parser.add_argument("--inputs", type=Path, help="directory holding the accepted private inputs")
    parser.add_argument("--out", type=Path, help="new output path; an existing path is refused")
    return parser


def main(argv=None):
    parser = build_parser()
    arguments = parser.parse_args(argv)
    return bundle.run(arguments, parser)


if __name__ == "__main__":
    raise SystemExit(main())
