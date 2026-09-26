#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Exercise event agreement through the production entrypoint without solc.

The public synthetic input was compiled with solc 0.8.25+commit.b61c2a91.
compiler-0.8.25.json preserves its exact standard-JSON stdout. The soljson
compiler SHA-256 is
f8c9554471ff2db3843167dffb7a503293b5dc728c8305b044ef9fd37d626ca7.
Only the process boundary is replaced; parsing, chunking and delivery remain
production code. A divergent ABI bit leaves the source and AST unchanged.
"""

from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures" / "issue-1366"
INPUT = FIXTURES / "event-input.json"
COMPILER_OUTPUT = FIXTURES / "compiler-0.8.25.json"
VERSION = "0.8.25+commit.b61c2a91"
INPUT_SHA256 = "dd37444e69f83a0a8ce96612110b7ff830d8400e67b3997ef3139639d1d6f272"
OUTPUT_SHA256 = "b7d9be3f8bce17861bfeb3b0bb7fd2184339f640b584d3d13a7bbfb15ec8ec3e"

SPEC = importlib.util.spec_from_file_location(
    "lemma_event_solidity", HERE.parent / "chunkers" / "solidity.py"
)
assert SPEC is not None and SPEC.loader is not None
solidity = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = solidity
SPEC.loader.exec_module(solidity)


def run_cli(output: dict, destination: Path) -> tuple[int, str, str]:
    """Feed preserved compiler output to the real CLI in this process."""
    document = json.loads(INPUT.read_bytes())
    destination.mkdir()
    argv = [
        "solidity.py", "--input", str(INPUT), "--solc", "fixture-solc",
        "--expect-solc", VERSION, "--include", "src/**",
        "--source-ref", "fixture:issue-1366/event-input.json",
        "--out", str(destination / "chunks.jsonl"),
    ]

    def compiler(command, **kwargs):
        if command == ["fixture-solc", "--version"]:
            return subprocess.CompletedProcess(command, 0, f"Version: {VERSION}\n", "")
        if command == ["fixture-solc", "--standard-json"]:
            if json.loads(kwargs["input"]) != document:
                raise AssertionError("production compiler input changed the fixture")
            return subprocess.CompletedProcess(command, 0, json.dumps(output), "")
        raise AssertionError(f"unexpected process invocation: {command!r}")

    stdout, stderr = io.StringIO(), io.StringIO()
    with (
        mock.patch.object(sys, "argv", argv),
        mock.patch.object(solidity.subprocess, "run", side_effect=compiler),
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        status = solidity.main()
    return status, stdout.getvalue(), stderr.getvalue()


class IndexedBitGuardTests(unittest.TestCase):
    """A healthy delivery must precede the single-bit refusal assertion."""

    def setUp(self):
        self.assertEqual(hashlib.sha256(INPUT.read_bytes()).hexdigest(), INPUT_SHA256)
        self.assertEqual(
            hashlib.sha256(COMPILER_OUTPUT.read_bytes()).hexdigest(), OUTPUT_SHA256
        )
        self.output = json.loads(COMPILER_OUTPUT.read_bytes())
        self.temporary = tempfile.TemporaryDirectory(prefix="lemma-event-guard-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def assert_healthy_delivery(self, destination: Path):
        status, stdout, stderr = run_cli(self.output, destination)
        self.assertEqual(status, 0, stdout + stderr)
        corpus = destination / "chunks.jsonl"
        provenance = destination / "provenance.jsonl"
        self.assertTrue(corpus.is_file(), stdout + stderr)
        self.assertTrue(provenance.is_file(), stdout + stderr)
        chunks = [json.loads(line) for line in corpus.read_text().splitlines()]
        self.assertTrue(any(chunk["kind"] == "Event" for chunk in chunks))

    def test_healthy_compiler_output_delivers(self):
        self.assert_healthy_delivery(self.root / "healthy")

    def test_indexed_bit_refuses_delivery(self):
        self.assert_healthy_delivery(self.root / "healthy")
        divergent = copy.deepcopy(self.output)
        event = next(
            row for row in divergent["contracts"]["src/EventProbe.sol"]["EventProbe"]["abi"]
            if row["type"] == "event" and row["name"] == "Changed"
        )
        self.assertIs(event["inputs"][0]["indexed"], True)
        event["inputs"][0]["indexed"] = False
        self.assertEqual(divergent["sources"], self.output["sources"])
        destination = self.root / "divergent"
        status, stdout, stderr = run_cli(divergent, destination)
        self.assertNotEqual(
            status, 0,
            "production CLI accepted divergent event ABI indexed metadata\n" + stdout + stderr,
        )
        self.assertIn("event", stderr.lower())
        self.assertIn("EventProbe", stderr)
        self.assertIn("Changed", stderr)
        self.assertFalse((destination / "chunks.jsonl").exists())
        self.assertFalse((destination / "provenance.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
