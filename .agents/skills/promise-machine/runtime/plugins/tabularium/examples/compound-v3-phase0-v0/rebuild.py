#!/usr/bin/env python3
"""Rebuild and verify the Compound III Phase 0 execution witness offline."""

from pathlib import Path
import socket
import sys
import tempfile
from unittest import mock


EXAMPLE = Path(__file__).resolve().parent
PLUGIN = EXAMPLE.parents[1]
REPO = PLUGIN.parents[1]
COMMAND_ROOT = PLUGIN / "scripts"
sys.path.insert(0, str(COMMAND_ROOT))

from tabularium_lib.compound_witness import (  # noqa: E402
    build_compound_witness,
    verify_compound_witness,
)

ALEXANDRIA = REPO / "plugins" / "alexandria" / "examples" / "compound-v3-phase0-v0" / "release"


def main():
    with tempfile.TemporaryDirectory(prefix="tabularium-compound-phase0-") as directory:
        root = Path(directory)
        outputs = []
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            for name in ("first", "second"):
                facts = root / (name + "-facts.jsonl")
                manifest = root / (name + "-witness.json")
                build_compound_witness(ALEXANDRIA, facts, manifest)
                verify_compound_witness(ALEXANDRIA, facts, manifest)
                outputs.append((facts.read_bytes(), manifest.read_bytes()))
        expected = ((EXAMPLE / "facts.jsonl").read_bytes(), (EXAMPLE / "witness.json").read_bytes())
        if outputs[0] != outputs[1] or outputs[0] != expected:
            raise SystemExit("rebuilt Compound Phase 0 witness differs from committed bytes")
        print("rebuild matches Compound Phase 0 witness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
