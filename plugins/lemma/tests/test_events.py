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
        for wire_type in ("uint7", "uint257", "uint08", "bytes0", "bytes33", "uint", "address[0]", "address[01]"):
            with self.subTest(wire_type=wire_type):
                self.row["inputs"][0]["type"] = wire_type
                with self.refusal("unsupported event parameter type"):
                    self.validate()
        self.row["inputs"][0]["type"] = "address"
        self.event["parameters"]["parameters"][0]["typeName"]["nodeType"] = "ArrayTypeName"
        with self.refusal("array dimension evidence"):
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
                with self.refusal("missing, malformed or duplicate source id"):
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


class EventConformanceTests(unittest.TestCase):
    """Preserved compiler evidence and isolated mutations through production code."""

    def setUp(self):
        self.output = json.loads((FIXTURES / "wire-compiler-0.8.25.json").read_bytes())
        self.document = json.loads((FIXTURES / "wire-input.json").read_bytes())
        self.path = "src/WireProbe.sol"
        self.owner = next(node for node in self.output["sources"][self.path]["ast"]["nodes"]
                          if node.get("name") == "WireProbe")
        self.abi = self.output["contracts"][self.path]["WireProbe"]["abi"]
        self.event = next(node for node in self.owner["nodes"]
                          if node.get("name") == "Complex")
        self.row = next(row for row in self.abi if row.get("name") == "Complex")

    def validate(self, output=None, selected=None):
        solidity.validate_event_agreement(
            self.output if output is None else output,
            {self.path} if selected is None else selected,
        )

    def healthy(self):
        try:
            self.validate()
        except solidity.ChunkError as exc:
            self.fail(f"preserved compiler evidence was refused: {exc}")

    def refuse(self, reason):
        return self.assertRaisesRegex(solidity.ChunkError, "event ABI agreement: .*" + reason)

    def declaration(self, name):
        return next(node for node in self.output["sources"]["lib/Types.sol"]["ast"]["nodes"]
                    if node.get("name") == name)

    def cli(self, destination, outputs, *, existing=False):
        """Exercise the real entrypoint; only compiler subprocesses are replaced."""
        if not existing:
            destination.mkdir()
        compiler_outputs = iter(outputs)
        argv = ["solidity.py", "--solc", "fixture-solc", "--expect-solc", VERSION,
                "--include", "src/**", "--source-ref", "fixture:issue-1366/wire-input.json",
                "--out", str(destination / "chunks.jsonl")]
        for _ in outputs:
            argv.extend(["--input", str(FIXTURES / "wire-input.json")])

        def compiler(command, **kwargs):
            if command == ["fixture-solc", "--version"]:
                return subprocess.CompletedProcess(command, 0, f"Version: {VERSION}\n", "")
            self.assertEqual(command, ["fixture-solc", "--standard-json"])
            self.assertEqual(json.loads(kwargs["input"]), self.document)
            return subprocess.CompletedProcess(command, 0, json.dumps(next(compiler_outputs)), "")

        stdout, stderr = io.StringIO(), io.StringIO()
        with (mock.patch.object(sys, "argv", argv),
              mock.patch.object(solidity.subprocess, "run", side_effect=compiler) as calls,
              contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr)):
            status = solidity.main()
        self.assertEqual(calls.call_count, 1 + len(outputs))
        return status, stdout.getvalue() + stderr.getvalue()

    def test_membership_multisets_and_overloads(self):
        self.healthy()
        same = [row for row in self.abi if row.get("name") == "Same"]
        self.assertEqual(len(same), 2)
        self.assertEqual(same[0], same[1])
        changed = [row for row in self.abi if row.get("name") == "Changed"]
        self.assertEqual(len(changed), 2)
        for mode in ("missing", "extra", "duplicate", "same-count-replacement"):
            with self.subTest(mode=mode):
                self.setUp()
                if mode == "missing": self.abi.pop(0)
                elif mode == "extra": self.abi.append({**self.row, "name": "Unknown"})
                elif mode == "duplicate": self.abi.append(copy.deepcopy(self.row))
                else:
                    self.abi.remove(next(row for row in self.abi if row.get("name") == "Same"))
                    self.abi.append(copy.deepcopy(self.row))
                with self.refuse("descriptors differ"):
                    self.validate()

    def test_inherited_and_qualified_events(self):
        self.healthy()
        self.assertTrue({"Inherited", "Remote", "Same"}.issubset({row.get("name") for row in self.abi}))
        declared = {node["id"] for node in self.owner["nodes"] if node["nodeType"] == "EventDefinition"}
        self.assertEqual(len(set(self.owner["usedEvents"]) - declared), 4)
        self.validate(selected=set(self.output["sources"]))
        self.declaration("Base")["nodes"][0]["anonymous"] = True
        with self.refuse("anonymous"):
            self.validate()

    def test_event_only_owner_kinds(self):
        self.healthy()
        for name in ("AbstractEvents", "InterfaceEvents", "LibraryEvents", "EmptyEvents"):
            with self.subTest(owner=name):
                self.setUp()
                abi = self.output["contracts"][self.path][name]["abi"]
                if abi: abi[0]["anonymous"] = not abi[0]["anonymous"]
                else: abi.append(copy.deepcopy(self.row))
                with self.refuse(name + ".*descriptors differ"):
                    self.validate()

    def test_primitive_and_compound_wire_types(self):
        self.healthy()
        self.assertEqual([row["type"] for row in self.row["inputs"]],
                         ["tuple", "uint128", "address", "uint8", "function", "bytes32[3][]"])
        # Constant SIZE is an identifier; the compiler has evaluated its dimension.
        array = self.event["parameters"]["parameters"][-1]["typeName"]["baseType"]
        self.assertEqual(array["length"]["nodeType"], "Identifier")
        for index, wire in enumerate(("uint256", "uint256", "bytes20", "uint16", "bytes24", "bytes32[4][]")):
            with self.subTest(parameter=index):
                self.setUp()
                internal = self.row["inputs"][index]["internalType"]
                self.row["inputs"][index]["type"] = wire
                if index == 0: self.row["inputs"][index].pop("components")
                self.assertEqual(self.row["inputs"][index]["internalType"], internal)
                with self.refuse("descriptors differ"):
                    self.validate()

    def test_abi_order_types_and_flags(self):
        self.healthy()
        mutations = [
            lambda: self.row["inputs"].reverse(),
            lambda: self.row["inputs"][0]["components"].reverse(),
            lambda: self.row["inputs"][0]["components"][0]["components"][0].update(type="uint64"),
            lambda: self.row["inputs"][0]["components"][0]["components"][0].update(name="renamed"),
            lambda: self.row.update(anonymous=True),
        ]
        for index in range(len(self.row["inputs"])):
            mutations.append(lambda index=index: self.row["inputs"][index].update(indexed=True))
        for mutation in mutations:
            self.setUp()
            mutation()
            with self.refuse("descriptors differ"):
                self.validate()
        for row_index, row in enumerate(self.abi):
            if row["type"] != "event":
                continue
            for input_index in range(len(row["inputs"])):
                self.setUp()
                target = self.abi[row_index]["inputs"][input_index]
                target["indexed"] = not target["indexed"]
                with self.refuse("indexed"):
                    self.validate()
        self.setUp()
        self.row["inputs"][1]["indexed"] = True
        with self.refuse(r"inputs\[1\].indexed"):
            self.validate()
        self.setUp()
        self.row["inputs"][0]["components"][0]["components"][0]["name"] = "other"
        with self.refuse(r"components\[0\].*name"):
            self.validate()

    def test_excluded_dependency_evidence(self):
        self.healthy()
        # The selection excludes Types.sol but still needs its declarations.
        del self.output["sources"]["lib/Types.sol"]["ast"]
        with self.refuse("unresolved usedEvents"):
            self.validate()
        self.setUp()
        self.event["parameters"]["parameters"][0]["typeName"]["referencedDeclaration"] = 99999
        with self.refuse("unresolved event type declaration"):
            self.validate()

    def test_missing_and_malformed_evidence(self):
        self.healthy()
        mutations = [
            (lambda: self.owner.pop("usedEvents"), "usedEvents"),
            (lambda: self.owner["usedEvents"].append(99999), "unresolved usedEvents"),
            (lambda: self.row.update(anonymous=0), "non-boolean"),
            (lambda: self.row["inputs"][0].update(indexed="false"), "non-boolean"),
            (lambda: self.row["inputs"][0].pop("components"), "tuple components"),
            (lambda: self.row["inputs"][0]["components"][0].pop("name"), "parameter name"),
            (lambda: self.declaration("Outer").pop("members"), "struct members"),
            (lambda: self.declaration("Price").pop("underlyingType"), "underlying type"),
            (lambda: self.declaration("Choice").update(members=[]), "enum members"),
            (lambda: self.declaration("Choice").update(members=[{}] * 257), "enum members"),
            (lambda: self.declaration("Outer")["members"][0].update(nodeType="Identifier"), "struct member"),
            (lambda: self.declaration("Outer")["members"][0]["typeName"].update(nodeType="Mapping"), "AST type shape"),
            (lambda: self.event["parameters"]["parameters"][0]["typeName"].update(referencedDeclaration=True), "unresolved event type"),
            (lambda: self.row["inputs"][5].update(type="bytes32[0][]"), "unsupported event parameter type"),
            (lambda: self.row["inputs"][5].update(type="bytes32[03][]"), "unsupported event parameter type"),
            (lambda: self.row["inputs"][5].update(type="bytes32" + "[]" * 65), "type depth"),
            (lambda: self.row["inputs"][5].update(type="bytes32" + "[]" * 4096), "type text"),
            (lambda: self.event["parameters"]["parameters"][4]["typeName"].update(visibility="internal"), "external function"),
            (lambda: self.event["parameters"]["parameters"][5]["typeName"]["baseType"].pop("typeDescriptions"), "array dimension evidence"),
            (lambda: self.event["parameters"]["parameters"][5]["typeName"]["baseType"]["length"].update(nodeType="Mapping"), "array dimension evidence"),
            (lambda: self.event["parameters"]["parameters"][5]["typeName"]["baseType"].pop("length"), "array dimension evidence"),
            (lambda: self.event["parameters"]["parameters"][5]["typeName"]["baseType"]["typeDescriptions"].update(typeString="bytes32[4]"), "array dimension evidence"),
        ]
        for mutate, reason in mutations:
            with self.subTest(reason=reason):
                self.setUp()
                mutate()
                with self.refuse(reason): self.validate()

    def test_cyclic_and_excessive_type_expansion(self):
        self.healthy()
        self.declaration("Outer")["members"][0]["typeName"]["referencedDeclaration"] = self.declaration("Outer")["id"]
        with self.refuse("cyclic event type"):
            self.validate()
        self.setUp()
        for bound, value, reason in (("EVENT_TYPE_DEPTH_LIMIT", 2, "type depth"),
                                     ("EVENT_TYPE_NODE_LIMIT", 2, "type expansion")):
            with self.subTest(bound=bound), mock.patch.object(solidity, bound, value):
                with self.refuse(reason): self.validate()
        self.setUp()
        self.row["inputs"][0]["components"][0]["components"] = [self.row["inputs"][0]]
        with self.refuse("type depth"):
            self.validate()

    def test_repeated_struct_references_consume_expansion_budget(self):
        self.healthy()
        nodes = {0: {"nodeType": "StructDefinition", "members": [
            {"nodeType": "VariableDeclaration", "name": "leaf", "typeName":
             {"nodeType": "ElementaryTypeName", "name": "uint256"}}]}}
        for reference in range(1, 15):
            nodes[reference] = {"nodeType": "StructDefinition", "members": [
                {"nodeType": "VariableDeclaration", "name": name, "typeName":
                 {"nodeType": "UserDefinedTypeName", "referencedDeclaration": reference - 1}}
                for name in ("left", "right")]}
        with mock.patch.object(solidity, "EVENT_TYPE_NODE_LIMIT", 1024):
            with self.refuse("type expansion"):
                solidity._EventTypes(nodes).ast(
                    {"nodeType": "UserDefinedTypeName", "referencedDeclaration": 14}, "synthetic repeated struct")

    def test_selected_diagnostics_ignore_source_insertion_order(self):
        self.healthy()
        for name in ("AbstractEvents", "InterfaceEvents"):
            self.output["contracts"][self.path][name]["abi"][0]["anonymous"] = True
        messages = []
        for sources in (self.output["sources"], dict(reversed(list(self.output["sources"].items())))):
            output = {**self.output, "sources": sources}
            with self.refuse("AbstractEvents.*anonymous") as caught:
                self.validate(output, set(sources))
            messages.append(str(caught.exception))
        self.assertEqual(messages[0], messages[1])

    def test_late_unit_failure_writes_nothing(self):
        with tempfile.TemporaryDirectory(prefix="lemma-event-late-") as temporary:
            root = Path(temporary)
            status, diagnostics = self.cli(root / "healthy", [self.output, self.output])
            self.assertEqual(status, 0, diagnostics)
            self.assertTrue((root / "healthy" / "provenance.jsonl").is_file())
            divergent = copy.deepcopy(self.output)
            divergent["contracts"][self.path]["WireProbe"]["abi"][0]["anonymous"] = True
            status, diagnostics = self.cli(root / "failed", [self.output, divergent])
            self.assertNotEqual(status, 0, diagnostics)
            self.assertIn("event descriptors differ", diagnostics)
            self.assertIn("corpus and provenance unchanged", diagnostics)
            self.assertIn("WireProbe", diagnostics)
            self.assertEqual(list((root / "failed").iterdir()), [])

    def test_refusal_preserves_existing_outputs(self):
        with tempfile.TemporaryDirectory(prefix="lemma-event-existing-") as temporary:
            root = Path(temporary)
            status, diagnostics = self.cli(root / "healthy", [self.output])
            self.assertEqual(status, 0, diagnostics)
            destination = root / "existing"
            destination.mkdir()
            before = {"chunks.jsonl": b"retained corpus\n", "provenance.jsonl": b"retained origin\n"}
            for name, data in before.items(): (destination / name).write_bytes(data)
            self.row["inputs"][0]["indexed"] = True
            status, diagnostics = self.cli(destination, [self.output], existing=True)
            self.assertNotEqual(status, 0, diagnostics)
            self.assertIn("event descriptors differ", diagnostics)
            self.assertEqual({p.name: p.read_bytes() for p in destination.iterdir()}, before)

    def test_external_function_signature_rejects_unsupported_type_shapes(self):
        """S2-R1-01: wire opacity does not admit arbitrary AST type tags."""
        self.healthy()
        for field in ("parameterTypes", "returnParameterTypes"):
            for shape in ("Mapping", "Identifier", "Bogus", ""):
                with self.subTest(field=field, shape=shape):
                    self.setUp()
                    signature = self.event["parameters"]["parameters"][4]["typeName"]
                    signature[field]["parameters"][0]["typeName"] = {"nodeType": shape}
                    with self.refuse("unsupported event external function signature type"):
                        self.validate()

    def test_external_function_signature_recursion_is_wire_opaque(self):
        for version in ("0.8.22", "0.8.25", "0.8.28"):
            with self.subTest(compiler=version):
                output = json.loads((FIXTURES / f"recursive-function-compiler-{version}.json").read_bytes())
                try:
                    solidity.validate_event_agreement(output, {"src/RecursiveFunction.sol"})
                except solidity.ChunkError as exc:
                    self.fail(f"valid external function wire type was refused: {exc}")

    def test_pinned_compiler_shapes(self):
        self.assertEqual(hashlib.sha256((FIXTURES / "wire-input.json").read_bytes()).hexdigest(),
                         "2fb800020bb7c72fc6681267270e9b87f6a213721e249ab4c161372dc37643ec")
        for version in ("0.8.22", "0.8.25", "0.8.28"):
            with self.subTest(compiler=version):
                data = (FIXTURES / f"wire-compiler-{version}.json").read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(),
                                 "e3ee4327198da8f811c3e36f2e8788e9870a62ce3dc04791ea266d0d6480eda7")
                self.output = json.loads(data)
                self.healthy()
        evidence = json.loads((FIXTURES / "compiler-evidence.json").read_bytes())
        self.assertEqual(len(evidence["compilations"]), 3)
        for item in evidence["inputs"]:
            self.assertEqual(hashlib.sha256((FIXTURES / item["path"]).read_bytes()).hexdigest(), item["sha256"])
        for compiler in evidence["compilations"]:
            self.assertIn("+commit.", compiler["version"])
            for item in compiler["outputs"]:
                self.assertEqual(hashlib.sha256((FIXTURES / item["path"]).read_bytes()).hexdigest(), item["sha256"])


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
