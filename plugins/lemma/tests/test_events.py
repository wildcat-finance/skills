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

from emit_issue_1366_report import write_report


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
        mock.patch.object(solidity.subprocess, "run", side_effect=compiler) as process_calls,
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        status = solidity.main()
    if process_calls.call_count != 2:
        raise AssertionError("event validation changed the one-version, one-compilation boundary")
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


class EventAgreementTests(unittest.TestCase):
    """Mutate real compiler evidence to isolate each event relation."""

    def setUp(self):
        self.output = json.loads(COMPILER_OUTPUT.read_bytes())
        self.path = "src/EventProbe.sol"
        self.source = self.output["sources"][self.path]
        self.owner = next(node for node in self.source["ast"]["nodes"]
                          if node["nodeType"] == "ContractDefinition")
        self.event = next(node for node in self.owner["nodes"]
                          if node["nodeType"] == "EventDefinition")
        self.abi = self.output["contracts"][self.path]["EventProbe"]["abi"]
        self.row = next(row for row in self.abi if row["type"] == "event")

    def validate(self, output=None, selected=None):
        solidity.validate_event_agreement(
            self.output if output is None else output,
            {self.path} if selected is None else selected,
        )

    def refusal(self, reason):
        return self.assertRaisesRegex(solidity.ChunkError, "event ABI agreement: .*" + reason)

    @staticmethod
    def renumbered(node, offset=1000):
        node = copy.deepcopy(node)
        pending = [node]
        while pending:
            value = pending.pop()
            if isinstance(value, list):
                pending.extend(value)
            elif isinstance(value, dict):
                if "nodeType" in value and "id" in value:
                    value["id"] += offset
                pending.extend(value.values())
        return node

    def clone_event(self, offset=1000):
        return self.renumbered(self.event, offset)

    def test_real_compiler_evidence_agrees(self):
        self.validate()

    def test_missing_extra_and_duplicate_abi_rows_refuse(self):
        for rows in ([], [self.row, self.row], [{**self.row, "name": "Other"}]):
            with self.subTest(rows=len(rows)):
                output = copy.deepcopy(self.output)
                output["contracts"][self.path]["EventProbe"]["abi"] = rows
                with self.refusal("descriptors differ"):
                    self.validate(output)

    def test_identical_descriptors_keep_multiplicity(self):
        second = self.clone_event()
        self.owner["nodes"].append(second)
        self.owner["usedEvents"].append(second["id"])
        self.abi.append(copy.deepcopy(self.row))
        self.validate()
        self.abi.remove(self.row)
        with self.refusal("Changed x1"):
            self.validate()

    def test_overloads_use_ordered_wire_types(self):
        second = self.clone_event()
        second["parameters"]["parameters"][0]["typeName"]["name"] = "uint8"
        self.owner["nodes"].append(second)
        self.owner["usedEvents"].append(second["id"])
        row = copy.deepcopy(self.row)
        row["inputs"][0]["type"] = "uint8"
        self.abi.append(row)
        self.validate()
        row["inputs"].reverse()
        with self.refusal("descriptors differ"):
            self.validate()

    def test_inherited_and_qualified_events_resolve_outside_owner(self):
        for kind in ("contract", "interface", "library"):
            with self.subTest(kind=kind):
                output = copy.deepcopy(self.output)
                owner = next(node for node in output["sources"][self.path]["ast"]["nodes"]
                             if node["nodeType"] == "ContractDefinition")
                event = next(node for node in owner["nodes"] if node["nodeType"] == "EventDefinition")
                owner["nodes"].remove(event)
                dependency = {"id": 1001, "nodeType": "ContractDefinition", "name": "Dependency",
                              "contractKind": kind, "abstract": kind == "interface",
                              "nodes": [event], "usedEvents": [event["id"]]}
                output["sources"]["lib/Dependency.sol"] = {
                    "id": 1, "ast": {"id": 1002, "nodeType": "SourceUnit", "nodes": [dependency]}}
                output["contracts"]["lib/Dependency.sol"] = {"Dependency": {"abi": [self.row]}}
                owner["linearizedBaseContracts"] = [owner["id"], 1001] if kind == "contract" else [owner["id"]]
                self.validate(output)
                self.validate(output, {self.path, "lib/Dependency.sol"})
                del output["sources"]["lib/Dependency.sol"]["ast"]
                with self.refusal("unresolved usedEvents"):
                    self.validate(output)

    def test_event_only_owner_kinds_are_checked(self):
        self.owner["nodes"] = [self.event]
        self.abi[:] = [self.row]
        for kind, abstract in (("contract", False), ("contract", True), ("interface", True), ("library", False)):
            with self.subTest(kind=kind, abstract=abstract):
                self.owner["contractKind"], self.owner["abstract"] = kind, abstract
                self.validate()
                self.row["inputs"][0]["indexed"] = False
                with self.refusal("descriptors differ"):
                    self.validate()
                self.row["inputs"][0]["indexed"] = True

    def test_empty_inventory_is_checked(self):
        self.owner["nodes"].remove(self.event)
        self.owner["usedEvents"] = []
        self.abi.remove(self.row)
        self.validate()
        self.abi.append(self.row)
        with self.refusal("descriptors differ"):
            self.validate()

    def test_flags_require_explicit_booleans(self):
        for target, key in ((self.event, "anonymous"), (self.row, "anonymous"),
                            (self.event["parameters"]["parameters"][0], "indexed"),
                            (self.row["inputs"][0], "indexed")):
            saved = target[key]
            for value in (None, 0, 1, "false"):
                with self.subTest(key=key, value=value):
                    target[key] = value
                    with self.refusal("non-boolean"):
                        self.validate()
            del target[key]
            with self.refusal("non-boolean"):
                self.validate()
            target[key] = saved

    def test_anonymous_and_each_indexed_bit_are_compared(self):
        for target, key in [(self.row, "anonymous")] + [(row, "indexed") for row in self.row["inputs"]]:
            target[key] = not target[key]
            with self.refusal("descriptors differ"):
                self.validate()
            target[key] = not target[key]

    def test_primitive_types_are_independent_of_internal_type(self):
        parameter = self.event["parameters"]["parameters"][0]
        for ast_type, wire_type in (("uint", "uint256"), ("int", "int256"), ("byte", "bytes1"),
                                    ("address", "address"), ("bool", "bool"), ("bytes", "bytes"),
                                    ("string", "string"), ("uint8", "uint8"), ("int248", "int248"),
                                    ("bytes32", "bytes32")):
            with self.subTest(wire_type=wire_type):
                parameter["typeName"]["name"] = ast_type
                self.row["inputs"][0]["type"] = wire_type
                self.validate()
        self.row["inputs"][0]["type"] = "address"
        with self.refusal("descriptors differ"):
            self.validate()

    def test_unsupported_primitive_and_compound_shapes_refuse(self):
        for wire_type in ("uint7", "uint257", "uint08", "bytes0", "bytes33", "uint", "tuple", "address[]"):
            with self.subTest(wire_type=wire_type):
                self.row["inputs"][0]["type"] = wire_type
                with self.refusal("unsupported event parameter type"):
                    self.validate()
        self.row["inputs"][0]["type"] = "address"
        self.event["parameters"]["parameters"][0]["typeName"]["nodeType"] = "ArrayTypeName"
        with self.refusal("unsupported event AST type shape 'ArrayTypeName'"):
            self.validate()

    def test_missing_and_invalid_membership_refuse(self):
        original = self.owner.pop("usedEvents")
        with self.refusal("usedEvents membership"):
            self.validate()
        for refs in (None, {}, [True], [-1], [999999], original * 2, [self.owner["id"]]):
            with self.subTest(refs=refs):
                self.owner["usedEvents"] = refs
                with self.refusal("usedEvents"):
                    self.validate()

    def test_missing_selected_ast_and_abi_refuse(self):
        ast = self.source.pop("ast")
        with self.refusal("source AST"):
            self.validate()
        self.source["ast"] = ast
        del self.output["contracts"][self.path]["EventProbe"]["abi"]
        with self.refusal("ABI"):
            self.validate()

    def test_abi_owner_without_ast_refuses(self):
        self.source["ast"]["nodes"].remove(self.owner)
        with self.refusal("ABI owner has no selected AST"):
            self.validate()

    def test_duplicate_ast_ids_refuse(self):
        self.owner["nodes"].append(copy.deepcopy(self.event))
        with self.refusal("duplicate AST node id"):
            self.validate()

    def test_ast_traversal_and_event_inventory_are_bounded(self):
        with mock.patch.object(solidity, "EVENT_AST_CONTAINER_LIMIT", 1), self.refusal("traversal limit"):
            self.validate()
        with mock.patch.object(solidity, "EVENT_ITEM_LIMIT", 0), self.refusal("oversized usedEvents"):
            self.validate()

    def test_names_are_bounded_and_free_of_control_characters(self):
        """S1-R1-01: DEL and C1 controls passed a C0-only check."""
        self.event["name"] = self.row["name"] = "E" * 256
        self.validate()
        self.event["name"] = self.row["name"] = "E" * 257
        with self.refusal("unsupported event name"):
            self.validate()
        for char in ("\x00", "\x1f", "\x7f", "\x80", "\x9f"):
            with self.subTest(event_name=repr(char)):
                self.event["name"] = self.row["name"] = f"Chan{char}ged"
                with self.refusal("unsupported event name"):
                    self.validate()
        self.event["name"] = self.row["name"] = "Changed"
        for target in (self.event["parameters"]["parameters"][0], self.row["inputs"][0]):
            with self.subTest(parameter_side="AST" if "nodeType" in target else "ABI"):
                target["name"] = "who\x7f"
                try:
                    with self.refusal("unsupported parameter name"):
                        self.validate()
                finally:
                    target["name"] = "who"
        self.owner["name"] = "EventProbe\x85"
        with self.refusal("unsupported owner name"):
            self.validate()

    def test_selected_input_source_absent_from_output_refuses(self):
        """S1-R1-02: a selected source the compiler omitted is refused, not skipped."""
        document = json.loads(INPUT.read_bytes())
        document["sources"]["src/Missing.sol"] = {"content": "// absent from compiler output\n"}
        with mock.patch.object(solidity, "compile_ast", return_value=(document, self.output)):
            chunks = solidity.chunk(str(INPUT), "unused-solc", [self.path])
            self.assertTrue(any(chunk.kind == "Event" for chunk in chunks))
            with self.refusal("src/Missing.sol: missing selected source evidence"):
                solidity.chunk(str(INPUT), "unused-solc", ["src/**"])

    def test_malformed_source_evidence_refuses(self):
        """S1-R1-02: source map, source id and declaration shapes fail closed."""
        output = copy.deepcopy(self.output)
        output["sources"] = []
        with self.refusal("compiler output: missing source evidence"):
            self.validate(output)
        for value in (None, "0", True, -1):
            with self.subTest(source_id=value):
                output = copy.deepcopy(self.output)
                output["sources"][self.path]["id"] = value
                with self.refusal("missing, malformed or duplicate source id"):
                    self.validate(output)
        for extra in ([], {"id": self.source["id"]}):
            with self.subTest(extra_source=extra):
                output = copy.deepcopy(self.output)
                output["sources"]["lib/Extra.sol"] = extra
                with self.refusal("lib/Extra.sol: missing, malformed or duplicate source id"):
                    self.validate(output)
        self.source["ast"]["nodes"].append(1)
        with self.refusal("malformed source declaration"):
            self.validate()

    def test_owner_identity_and_kind_refuse(self):
        """S1-R1-02: duplicate owner names and unknown owner kinds fail closed."""
        output = copy.deepcopy(self.output)
        owner = next(node for node in output["sources"][self.path]["ast"]["nodes"]
                     if node["nodeType"] == "ContractDefinition")
        output["sources"][self.path]["ast"]["nodes"].append(self.renumbered(owner))
        with self.refusal("duplicate event owner name"):
            self.validate(output)
        for kind in (None, "free", 1):
            with self.subTest(kind=kind):
                self.owner["contractKind"] = kind
                with self.refusal("unsupported event owner kind"):
                    self.validate()

    def test_malformed_abi_rows_refuse(self):
        """S1-R1-02: an ABI row without a string type fails closed."""
        for row in (1, {}, {"type": 1}):
            with self.subTest(row=row):
                output = copy.deepcopy(self.output)
                output["contracts"][self.path]["EventProbe"]["abi"].append(row)
                with self.refusal("malformed ABI row"):
                    self.validate(output)

    def test_abi_and_parameter_lists_are_bounded(self):
        """S1-R1-02: ABI rows and each side's parameters stop at the limit."""
        limit = len(self.abi)
        self.assertEqual(len(self.row["inputs"]), limit)
        with mock.patch.object(solidity, "EVENT_ITEM_LIMIT", limit):
            self.validate()
            output = copy.deepcopy(self.output)
            output["contracts"][self.path]["EventProbe"]["abi"].append(copy.deepcopy(self.abi[-1]))
            with self.refusal("missing, malformed or oversized ABI"):
                self.validate(output)
            output = copy.deepcopy(self.output)
            row = next(row for row in output["contracts"][self.path]["EventProbe"]["abi"]
                       if row["type"] == "event")
            row["inputs"].append(copy.deepcopy(row["inputs"][-1]))
            with self.refusal("oversized event parameters"):
                self.validate(output)
            parameters = self.event["parameters"]["parameters"]
            parameters.append(self.renumbered(parameters[-1]))
            with self.refusal("oversized event parameters"):
                self.validate()

    def test_malformed_parameter_shapes_refuse(self):
        """S1-R1-02: parameter lists, declarations and ABI fields fail closed."""
        cases = (
            (lambda: self.event["parameters"].update(nodeType="Block"), "missing event parameter list"),
            (lambda: self.event.update(parameters=None), "missing event parameter list"),
            (lambda: self.event["parameters"].update(parameters=None), "oversized event parameters"),
            (lambda: self.row.pop("inputs"), "oversized event parameters"),
            (lambda: self.event["parameters"]["parameters"].append(1), "malformed event parameter"),
            (lambda: self.row["inputs"].append(1), "malformed event parameter"),
            (lambda: self.event["parameters"]["parameters"][0].update(nodeType="Identifier"),
             "unsupported event parameter declaration"),
            (lambda: self.event["parameters"]["parameters"][0].update(typeName=None),
             "unsupported event AST type shape 'None'"),
            (lambda: self.row["inputs"][0].update(components=[]), "unsupported event ABI tuple components"),
            (lambda: self.row["inputs"][0].pop("type"), "missing event parameter type"),
        )
        for index, (mutate, reason) in enumerate(cases):
            with self.subTest(case=index, reason=reason):
                self.setUp()
                mutate()
                with self.refusal(reason):
                    self.validate()


class ReportPathTests(unittest.TestCase):
    """Root aliases are allowed; symlinks below that root are refused."""

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="lemma-report-path-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.worktree = self.root / "worktree"
        self.worktree.mkdir()
        self.alias = self.root / "alias"
        self.alias.symlink_to(self.worktree, target_is_directory=True)

    def test_absolute_root_alias_accepts_report(self):
        with contextlib.chdir(self.worktree):
            write_report(str(self.alias / ".elenchus" / "report.json"), {"observed": True})
        self.assertEqual(
            json.loads((self.worktree / ".elenchus" / "report.json").read_text()),
            {"observed": True},
        )

    def test_descendant_symlink_is_refused(self):
        outside = self.root / "outside"
        outside.mkdir()
        (self.worktree / "linked").symlink_to(outside, target_is_directory=True)
        with contextlib.chdir(self.worktree), self.assertRaises(OSError):
            write_report(str(self.alias / "linked" / "report.json"), {})
        self.assertFalse((outside / "report.json").exists())

    def test_outside_absolute_path_is_refused(self):
        with contextlib.chdir(self.worktree), self.assertRaises(ValueError):
            write_report(str(self.root / "outside.json"), {})
        self.assertFalse((self.root / "outside.json").exists())

    def test_parent_traversal_is_refused(self):
        with contextlib.chdir(self.worktree), self.assertRaises(ValueError):
            write_report("../outside.json", {})
        self.assertFalse((self.root / "outside.json").exists())

    def test_existing_report_is_preserved(self):
        report = self.worktree / "report.json"
        report.write_bytes(b"existing report")
        with contextlib.chdir(self.worktree), self.assertRaises(FileExistsError):
            write_report(str(self.alias / "report.json"), {})
        self.assertEqual(report.read_bytes(), b"existing report")


if __name__ == "__main__":
    unittest.main()
