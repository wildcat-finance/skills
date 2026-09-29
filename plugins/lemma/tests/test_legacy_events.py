#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Exercise pinned compiler event membership through the production CLI.

The public input and exact compiler standard-JSON outputs are retained beside
these tests. Only the compiler process boundary is replaced. The modern
control must deliver before either legacy omission is tested.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from test_events import solidity


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures" / "issue-1983"
INPUT = FIXTURES / "membership-input.json"
INPUT_SHA256 = "f772b7ffc5cb8dae7f63600f829002acd363962f5488e98b97c3442da3b46af0"
VERSIONS = {
    "0.8.10": "0.8.10+commit.fc410830.Emscripten.clang",
    "0.8.19": "0.8.19+commit.7dd6d404.Emscripten.clang",
    "0.8.22": "0.8.22+commit.4fc1097e.Emscripten.clang",
}
OUTPUT_SHA256 = {
    "0.8.10": "ada9edfa17b32cb34c88fa02ad60ae030413cc140170d8a797f743d55974b3ce",
    "0.8.19": "8a2a45e17037add5a22fa7d14975ad32f9b0d93ed80a9c2a928ac2df9f289b31",
    "0.8.22": "0fffc888942fa8595d4cbfd8c2501c34a1ce3872546490870aac0479d53333ce",
}


def compiler_output(version: str) -> dict:
    """Read one retained output only after checking its exact bytes."""
    raw = (FIXTURES / f"compiler-{version}.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != OUTPUT_SHA256[version]:
        raise AssertionError(f"compiler fixture changed: {version}")
    return json.loads(raw)


def run_cli(output: dict, version: str, destination: Path) -> tuple[int, str, str]:
    """Replace only solc execution; keep version, validation and writes real."""
    raw = INPUT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA256:
        raise AssertionError("public compiler input changed")
    document = json.loads(raw)
    destination.mkdir()
    argv = [
        "solidity.py", "--input", str(INPUT), "--solc", "fixture-solc",
        "--expect-solc", version, "--include", "EventProbe.sol",
        "--source-ref", "fixture:issue-1983/membership-input.json",
        "--out", str(destination / "chunks.jsonl"),
    ]

    def compiler(command, **kwargs):
        if command == ["fixture-solc", "--version"]:
            return subprocess.CompletedProcess(command, 0, f"Version: {version}\n", "")
        if command == ["fixture-solc", "--standard-json"]:
            if json.loads(kwargs["input"]) != document:
                raise AssertionError("production compiler input changed the fixture")
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        raise AssertionError(f"unexpected process invocation: {command!r}")

    stdout, stderr = io.StringIO(), io.StringIO()
    with (
        mock.patch.object(sys, "argv", argv),
        mock.patch.object(solidity.subprocess, "run", side_effect=compiler) as calls,
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        status = solidity.main()
    if calls.call_count != 2:
        raise AssertionError("membership validation changed the compiler call count")
    return status, stdout.getvalue(), stderr.getvalue()


class LegacyMembershipGuardTests(unittest.TestCase):
    """Healthy legacy outputs must pass without usedEvents owner metadata."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lemma-legacy-event-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def assert_delivery(self, version: str, name: str):
        output = compiler_output(version)
        owners = [
            node for node in output["sources"]["EventProbe.sol"]["ast"]["nodes"]
            if node["nodeType"] == "ContractDefinition"
        ]
        self.assertTrue(owners)
        if version != "0.8.22":
            self.assertTrue(all("usedEvents" not in node for node in owners))
        else:
            self.assertTrue(all(isinstance(node["usedEvents"], list) for node in owners))
        destination = self.root / name
        status, stdout, stderr = run_cli(output, VERSIONS[version], destination)
        self.assertEqual(status, 0, stdout + stderr)
        corpus = destination / "chunks.jsonl"
        self.assertTrue(corpus.is_file(), stdout + stderr)
        self.assertTrue((destination / "provenance.jsonl").is_file(), stdout + stderr)
        chunks = [json.loads(line) for line in corpus.read_text().splitlines()]
        self.assertTrue(any(chunk["kind"] == "Event" for chunk in chunks))

    def test_modern_compiler_control_delivers(self):
        self.assert_delivery("0.8.22", "modern")

    def test_solc_0810_without_used_events_delivers(self):
        self.assert_delivery("0.8.22", "modern")
        self.assert_delivery("0.8.10", "legacy")

    def test_solc_0819_without_used_events_delivers(self):
        self.assert_delivery("0.8.22", "modern")
        self.assert_delivery("0.8.19", "legacy")


if __name__ == "__main__":
    unittest.main()
