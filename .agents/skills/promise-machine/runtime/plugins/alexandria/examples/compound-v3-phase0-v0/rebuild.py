#!/usr/bin/env python3
"""Rebuild the bounded Compound III Phase 0 raw release twice offline."""

from pathlib import Path
import socket
import sys
import tempfile
from unittest import mock


EXAMPLE = Path(__file__).resolve().parent
PLUGIN = EXAMPLE.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.compound_phase0 import build, check_phase0  # noqa: E402


def tree(root):
    return {
        path.relative_to(root): path.read_bytes()
        for path in root.rglob("*") if path.is_file()
    }


def main():
    expected = tree(EXAMPLE / "release")
    with tempfile.TemporaryDirectory(prefix="alexandria-compound-phase0-") as directory:
        first = Path(directory) / "first"
        second = Path(directory) / "second"
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            first_id = build(EXAMPLE / "input", first)
            second_id = build(EXAMPLE / "input", second)
            receipt = check_phase0(first)
        if first_id != second_id or tree(first) != tree(second) or tree(first) != expected:
            raise SystemExit("rebuilt Compound Phase 0 release differs from committed bytes")
        print("rebuild matches %s; %d method gates recorded" % (first_id, len(receipt["gates"])))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
