#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Guard healthy event membership from exact retained compiler outputs."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
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
        return test_legacy_events.run_cli(
            output, version, destination,
            source_ref="fixture:issue-1366-remaining/membership-input.json", **kwargs)


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


class RemainingCompilerConformanceTests(unittest.TestCase):
    """Exercise descriptors and output preservation across every retained build."""

    def versions(self):
        rows = compiler_evidence()["records"]
        self.assertEqual(len(rows), 20)
        self.assertEqual(len({row["version"] for row in rows}), 20)
        return [row["version"].split("+")[0] for row in rows]

    def validate(self, output, identity):
        test_legacy_events.solidity.validate_event_agreement(
            output, {"EventProbe.sol"}, identity)

    def test_all_twenty_outputs_and_both_identity_forms(self):
        for version in self.versions():
            row, output = compiler_fixture(version)
            for identity in (row["version"], row["observed_version"]):
                with self.subTest(version=identity):
                    self.validate(output, identity)

    def test_all_twenty_compilers_deliver_event_quotations(self):
        with tempfile.TemporaryDirectory(prefix="lemma-all-compilers-") as temporary:
            for version in self.versions():
                row, output = compiler_fixture(version)
                with self.subTest(version=version):
                    destination = Path(temporary) / version
                    status, stdout, stderr = run_cli(output, row["observed_version"], destination)
                    self.assertEqual(status, 0, stdout + stderr)
                    chunks = [json.loads(line) for line in
                              (destination / "chunks.jsonl").read_text().splitlines()]
                    self.assertTrue((destination / "provenance.jsonl").is_file())
                    self.assertTrue(any(chunk["kind"] == "Event" for chunk in chunks))

    def test_fixture_semantics_cover_inheritance_overloads_and_wire_shapes(self):
        for version in self.versions():
            row, output = compiler_fixture(version)
            with self.subTest(version=version):
                contracts = output["contracts"]["EventProbe.sol"]
                self.assertEqual(set(contracts), {"IBase", "Base", "Lib", "Derived"})
                events = [event for event in contracts["Derived"]["abi"]
                          if event["type"] == "event"]
                ping = [event for event in events if event["name"] == "Ping"]
                self.assertEqual(len(ping), 2)
                self.assertEqual({event["inputs"][0]["type"] for event in ping},
                                 {"address", "uint256"})
                seen = next(event for event in events if event["name"] == "Seen")
                self.assertIs(seen["anonymous"], True)
                complex_event = next(event for event in events if event["name"] == "Complex")
                self.assertEqual([entry["type"] for entry in complex_event["inputs"]],
                                 ["tuple", "tuple[]", "bytes32"])
                nested = complex_event["inputs"][0]["components"]
                self.assertEqual([entry["type"] for entry in nested],
                                 ["tuple", "uint8", "address"])
                self.assertEqual(nested[0]["components"][1]["type"], "uint256[2]")
                opaque = next(event for event in events if event["name"] == "Opaque")
                self.assertEqual(opaque["inputs"][0]["type"], "function")
                self.validate(output, row["observed_version"])

    def test_unknown_or_malformed_legacy_identity_refuses(self):
        for version in LEGACY_ADDITIONS:
            row, output = compiler_fixture(version)
            bad = (None, "", [], {}, True, version, row["version"] + ".evil",
                   row["version"] + "\n", version + "+commit.00000000",
                   row["version"].replace("+commit.", "+commit.X"))
            for identity in bad:
                with self.subTest(version=version, identity=identity):
                    with self.assertRaisesRegex(test_legacy_events.solidity.ChunkError,
                                                "usedEvents"):
                        self.validate(output, identity)

    def test_present_malformed_membership_refuses_every_compiler(self):
        for version in self.versions():
            row, original = compiler_fixture(version)
            for malformed in (None, {}, "", [True], [-1], [1, 1], [999999]):
                with self.subTest(version=version, malformed=malformed):
                    output = copy.deepcopy(original)
                    owner = next(node for node in output["sources"]["EventProbe.sol"]["ast"]["nodes"]
                                 if node.get("name") == "Derived")
                    owner["usedEvents"] = malformed
                    with self.assertRaisesRegex(test_legacy_events.solidity.ChunkError,
                                                "usedEvents"):
                        self.validate(output, row["observed_version"])

    def test_modern_membership_never_uses_legacy_fallback(self):
        for version in self.versions():
            row, output = compiler_fixture(version)
            owner = next(node for node in output["sources"]["EventProbe.sol"]["ast"]["nodes"]
                         if node.get("name") == "Derived")
            if "usedEvents" not in owner:
                continue
            del owner["usedEvents"]
            with self.subTest(version=version):
                with self.assertRaisesRegex(test_legacy_events.solidity.ChunkError, "usedEvents"):
                    self.validate(output, row["observed_version"])

    def test_independent_descriptor_corruption_refuses_every_compiler(self):
        for version in self.versions():
            row, original = compiler_fixture(version)
            for mutation in ("indexed", "type", "anonymous", "order", "missing", "extra"):
                with self.subTest(version=version, mutation=mutation):
                    output = copy.deepcopy(original)
                    abi = output["contracts"]["EventProbe.sol"]["Derived"]["abi"]
                    event = next(item for item in abi if item.get("name") == "Changed")
                    if mutation == "indexed":
                        event["inputs"][0]["indexed"] = not event["inputs"][0]["indexed"]
                    elif mutation == "type":
                        event["inputs"][0]["type"] = "bytes32"
                    elif mutation == "anonymous":
                        event["anonymous"] = not event["anonymous"]
                    elif mutation == "order":
                        event["inputs"].reverse()
                    elif mutation == "missing":
                        abi.remove(event)
                    else:
                        abi.append(copy.deepcopy(event))
                    with self.assertRaisesRegex(test_legacy_events.solidity.ChunkError,
                                                "event ABI agreement"):
                        self.validate(output, row["observed_version"])

    def test_later_corruption_preserves_absent_and_existing_outputs(self):
        with tempfile.TemporaryDirectory(prefix="lemma-preserve-events-") as temporary:
            for version in self.versions():
                row, output = compiler_fixture(version)
                corrupt = copy.deepcopy(output)
                abi = corrupt["contracts"]["EventProbe.sol"]["Derived"]["abi"]
                event = next(item for item in abi if item.get("name") == "Changed")
                event["inputs"][0]["indexed"] = not event["inputs"][0]["indexed"]
                for existing in (False, True):
                    with self.subTest(version=version, existing=existing):
                        destination = Path(temporary) / f"{version}-{existing}"
                        expected = {}
                        if existing:
                            destination.mkdir()
                            for name in ("chunks.jsonl", "provenance.jsonl"):
                                expected[name] = ("prior " + name).encode()
                                (destination / name).write_bytes(expected[name])
                        status, stdout, stderr = run_cli(
                            output, row["observed_version"], destination,
                            later_outputs=(corrupt,), existing=existing)
                        self.assertNotEqual(status, 0)
                        self.assertIn("event ABI agreement", stdout + stderr)
                        for name in ("chunks.jsonl", "provenance.jsonl"):
                            if existing:
                                self.assertEqual((destination / name).read_bytes(), expected[name])
                            else:
                                self.assertFalse((destination / name).exists())


class DistinctEventOwnersGuardTests(unittest.TestCase):
    """Separate source declarations retain their exact event quotations."""

    def setUp(self):
        self.document = json.loads(
            (FIXTURES / "whitespace-events-input.json").read_bytes())
        self.solidity = test_legacy_events.solidity
        self.source = self.document["sources"]["Pool.sol"]["content"].encode()
        self.smap = self.solidity.SourceMap(self.document["sources"], {"Pool.sol": 0})
        self.chunks = []
        self.spans = []
        cursor = 0
        for name, kind in (("Pool", "contract"), ("PoolLib", "library")):
            start = self.source.index(b"event Updated(", cursor)
            end = self.source.index(b";", start) + 1
            cursor = end
            node = {
                "nodeType": "EventDefinition", "name": "Updated",
                "src": f"{start}:{end - start}:0", "anonymous": False,
                "parameters": {"parameters": [
                    {"typeDescriptions": {"typeString": "address"}, "indexed": True},
                    {"typeDescriptions": {"typeString": "uint256"}, "indexed": False},
                ]},
            }
            owner = {"name": name, "contractKind": kind}
            chunk = self.solidity.make_chunk(node, owner, self.smap, [])
            self.assertIsNotNone(chunk)
            self.chunks.append(chunk)
            self.spans.append((start, end))

    def test_each_event_is_valid_alone(self):
        for chunk in self.chunks:
            with self.subTest(owner=chunk.detail["contract"]):
                self.assertEqual(self.solidity._schema.validate([chunk]), [])

    def test_distinct_owners_keep_whitespace_different_quotations(self):
        first, second = self.chunks
        self.assertNotEqual(first.display_text, second.display_text)
        self.assertEqual(" ".join(first.model_text.split()),
                         " ".join(second.model_text.split()))
        self.assertEqual([chunk.detail["contract"] for chunk in self.chunks],
                         ["Pool", "PoolLib"])
        self.assertEqual([chunk.detail["declared_in_kind"] for chunk in self.chunks],
                         ["contract", "library"])
        before = [chunk.to_dict() for chunk in self.chunks]
        for chunk, (start, end) in zip(self.chunks, self.spans):
            self.assertEqual(chunk.display_text.encode(), self.source[start:end])
            self.assertEqual(chunk.model_text, chunk.display_text)
            self.assertFalse(chunk.synthesised)
            self.assertEqual(chunk.path, "Pool.sol")
        self.assertEqual(self.solidity._schema.validate(self.chunks), [])
        self.assertEqual([chunk.to_dict() for chunk in self.chunks], before)

    def test_repeated_identity_still_refuses(self):
        original = self.chunks[0]
        problems = self.solidity._schema.validate([original, copy.deepcopy(original)])
        self.assertTrue(any("duplicate id" in problem for problem in problems), problems)

    def test_same_owner_duplicate_content_still_refuses(self):
        original = self.chunks[0]
        duplicate = copy.deepcopy(original)
        duplicate.id += "-duplicate"
        problems = self.solidity._schema.validate([original, duplicate])
        self.assertTrue(problems)


class RemainingReporterInterfaceTests(unittest.TestCase):
    def test_fiat_binds_every_reporter_case_without_importing_it(self):
        import emit_issue_1366_remaining_report as reporter

        root = Path(__file__).resolve().parents[3]
        path = root / "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py"
        spec = importlib.util.spec_from_file_location("remaining_gate_commands", path)
        gates = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(gates)
        digest = hashlib.sha256((root / reporter.REPORTER).read_bytes()).hexdigest()
        parser, receipt = gates.interface(
            root, reporter.REPORTER,
            {reporter.REPORTER: ("build_parser", digest)})
        self.assertEqual(receipt["sha256"], digest)
        runtime = reporter.build_parser()
        for case in (*reporter.TEST_CASES, *reporter.DESIGN_CASES):
            candidates = reporter.CANDIDATES if case in reporter.DESIGN_CASES else (None,)
            for candidate in candidates:
                with self.subTest(case=case, candidate=candidate):
                    argv = ["--case", case, "--report", "report.json"]
                    if candidate is not None:
                        argv += ["--candidate", candidate]
                    self.assertEqual(vars(parser.parse_args(argv)),
                                     vars(runtime.parse_args(argv)))
        with self.assertRaises(gates.Refusal):
            parser.parse_args(["--case", "unknown", "--report", "report.json"])


if __name__ == "__main__":
    unittest.main()
