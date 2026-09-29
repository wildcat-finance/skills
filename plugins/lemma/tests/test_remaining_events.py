#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Guard healthy event membership from exact retained compiler outputs."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import test_legacy_events


FIXTURES = Path(__file__).resolve().parent / "fixtures" / "issue-1366-remaining"
INPUT = FIXTURES / "membership-input.json"
LEGACY_ADDITIONS = ("0.6.11", "0.8.7", "0.8.13", "0.8.15", "0.8.17", "0.8.18")


def compiler_evidence() -> dict:
    return json.loads((FIXTURES / "compiler-evidence.json").read_text())


def compiler_fixture(version: str) -> tuple[dict, dict]:
    evidence = compiler_evidence()
    matches = [row for row in evidence["records"]
               if row["version"].split("+")[0] == version]
    if len(matches) != 1:
        raise AssertionError(f"expected one compiler fixture: {version}")
    row = matches[0]
    raw = (FIXTURES / row["output_file"]).read_bytes()
    if (hashlib.sha256(raw).hexdigest() != row["output_sha256"]
            or len(raw) != row["output_bytes"]):
        raise AssertionError(f"compiler fixture changed: {version}")
    if hashlib.sha256(INPUT.read_bytes()).hexdigest() != evidence["input_sha256"]:
        raise AssertionError("public compiler input changed")
    return row, json.loads(raw)


def run_cli(output: dict, version: str, destination: Path, **kwargs):
    """Keep the production CLI, pin check, validation and writes active."""
    with (
        mock.patch.object(test_legacy_events, "INPUT", INPUT),
        mock.patch.object(test_legacy_events, "INPUT_SHA256",
                          compiler_evidence()["input_sha256"]),
    ):
        return test_legacy_events.run_cli(output, version, destination, **kwargs)


class RemainingLegacyMembershipGuardTests(unittest.TestCase):
    """Each absent legacy membership field needs its exact admitted build."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="lemma-remaining-events-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def assert_delivery(self, version: str, name: str):
        row, output = compiler_fixture(version)
        owners = [node for node in output["sources"]["EventProbe.sol"]["ast"]["nodes"]
                  if node["nodeType"] == "ContractDefinition"]
        self.assertEqual(len(owners), 4)
        if version in LEGACY_ADDITIONS:
            self.assertTrue(all("usedEvents" not in owner for owner in owners))
        else:
            self.assertTrue(all(isinstance(owner["usedEvents"], list) for owner in owners))
        destination = self.root / name
        status, stdout, stderr = run_cli(output, row["observed_version"], destination)
        self.assertEqual(status, 0, stdout + stderr)
        self.assertTrue((destination / "provenance.jsonl").is_file())
        corpus = destination / "chunks.jsonl"
        self.assertTrue(corpus.is_file())
        chunks = [json.loads(line) for line in corpus.read_text().splitlines()]
        self.assertTrue(any(chunk["kind"] == "Event" for chunk in chunks))

    def test_modern_control_delivers(self):
        self.assert_delivery("0.8.25", "modern")


def legacy_guard(version: str):
    def test(self):
        self.assert_delivery("0.8.25", "modern")
        self.assert_delivery(version, "legacy")
    test.__name__ = "test_solc_" + version.replace(".", "_") + "_delivers"
    return test


for _version in LEGACY_ADDITIONS:
    _test = legacy_guard(_version)
    setattr(RemainingLegacyMembershipGuardTests, _test.__name__, _test)


if __name__ == "__main__":
    unittest.main()
