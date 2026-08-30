#!/usr/bin/env python3
"""Scaffold for the wildcat-agent-instruction/v1 codec.

The version-1 contract is docs/agent-instruction-language-v1.md. Step 1 freezes
the public surface and deliberately opens no decoder or file-input path.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence


SCHEMA_ID = "wildcat-agent-instruction/v1"
MAGIC = "WAI1"
CONTRACT_PATH = "docs/agent-instruction-language-v1.md"
SCHEMA_PATH = "schemas/agent-instruction-v1.schema.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate and encode Wildcat agent instruction models.",
        epilog=f"Contract: {CONTRACT_PATH}; schema: {SCHEMA_PATH}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {SCHEMA_ID} compact-magic={MAGIC}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    del arguments
    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
