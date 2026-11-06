#!/usr/bin/env python3
"""Run the real pinned native sequence on the shipped public two-step fixture."""
import argparse
import json
from pathlib import Path
import sys

from checkpoint_authority_native_fixture import FIXTURES, approval, fixture, pin, request
from checkpoint_authority.native import verify_native


def run(source, scratch, *, attempt="native-positive", first_step=1):
    result = verify_native(FIXTURES / "checkpoint.zip", job_root=Path(scratch),
        pin=pin(source), request=request(attempt), approval=approval(first_step=first_step))
    expected = fixture()
    value = result.record
    assert value["complete"] is True
    assert value["coverage"]["required"] == sorted(expected["required"])
    assert value["coverage"]["native_expected"] == sorted(expected["native_expected"])
    assert value["coverage"]["historical_required"] == sorted(expected["historical_required"])
    assert len(value["coverage"]["verified"]) == 4
    assert [row["stage"] for row in value["native_results"]] == ["inspect", "restore", "verify", "identity"]
    assert all(row["exit"] == 0 for row in value["native_results"])
    return value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--scratch", required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.source, args.scratch), sort_keys=True, separators=(",", ":")))
