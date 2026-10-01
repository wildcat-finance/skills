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
import copy
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


def run_cli(output: dict, version: str, destination: Path, *,
            later_outputs: tuple[dict, ...] = (), existing: bool = False,
            source_ref: str = "fixture:issue-1983/membership-input.json") -> tuple[int, str, str]:
    """Replace only solc execution; keep version, validation and writes real."""
    raw = INPUT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != INPUT_SHA256:
        raise AssertionError("public compiler input changed")
    document = json.loads(raw)
    if not existing:
        destination.mkdir()
    outputs = iter((output, *later_outputs))
    argv = [
        "solidity.py", "--input", str(INPUT), "--solc", "fixture-solc",
        "--expect-solc", version, "--include", "EventProbe.sol",
        "--source-ref", source_ref,
        "--out", str(destination / "chunks.jsonl"),
    ]

    for _ in later_outputs:
        argv.extend(["--input", str(INPUT)])

    def compiler(command, **kwargs):
        if command == ["fixture-solc", "--version"]:
            return subprocess.CompletedProcess(command, 0, f"Version: {version}\n", "")
        if command == ["fixture-solc", "--standard-json"]:
            if json.loads(kwargs["input"]) != document:
                raise AssertionError("production compiler input changed the fixture")
            return subprocess.CompletedProcess(command, 0, json.dumps(next(outputs)), "")
        raise AssertionError(f"unexpected process invocation: {command!r}")

    stdout, stderr = io.StringIO(), io.StringIO()
    with (
        mock.patch.object(sys, "argv", argv),
        mock.patch.object(solidity.subprocess, "run", side_effect=compiler) as calls,
        contextlib.redirect_stdout(stdout),
        contextlib.redirect_stderr(stderr),
    ):
        status = solidity.main()
    if calls.call_count != 2 + len(later_outputs):
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


class LegacyMembershipTests(unittest.TestCase):
    """Keep compiler identity, AST membership and ABI descriptors independent."""

    def setUp(self):
        self.output = compiler_output("0.8.10")
        self.path = "EventProbe.sol"
        self.nodes = self.output["sources"][self.path]["ast"]["nodes"]
        self.owners = {node["name"]: node for node in self.nodes
                       if node["nodeType"] == "ContractDefinition"}
        self.owner = self.owners["Derived"]
        self.abi = self.output["contracts"][self.path]["Derived"]["abi"]

    def validate(self, version=VERSIONS["0.8.10"], *, output=None):
        solidity.validate_event_agreement(
            self.output if output is None else output, {self.path}, version)

    def refuse(self, reason):
        return self.assertRaisesRegex(solidity.ChunkError, "event ABI agreement: .*" + reason)

    @staticmethod
    def clone(node):
        result = copy.deepcopy(node)
        pending = [result]
        while pending:
            value = pending.pop()
            if isinstance(value, list):
                pending.extend(value)
            elif isinstance(value, dict):
                if "nodeType" in value and "id" in value:
                    value["id"] += 10000
                pending.extend(value.values())
        return result

    def test_only_exact_compiler_identities_admit_missing_membership(self):
        for version in VERSIONS.values():
            if version.startswith("0.8.22"):
                continue
            for form in (version, version.removesuffix(".Emscripten.clang")):
                with self.subTest(version=form):
                    self.validate(form)
        for version in (None, "", [], {}, True, "0.8.10", "0.8.19+commit.7dd6",
                        "0.8.10+commit.fc410830.g++", "0.8.10+commit.fc410830.evil",
                        "0.8.10+commit.fc410830\n", "0.8.11+commit.fc410830",
                        "0.8.19+commit.00000000", "0.8.22+commit.4fc1097e"):
            with self.subTest(version=version), self.refuse("usedEvents"):
                self.validate(version)
        with self.refuse("usedEvents"):
            solidity.validate_event_agreement(self.output, {self.path})

    def test_present_malformed_membership_never_falls_back(self):
        for value in (None, {}, "", [True], [-1], [1, 1], [999999]):
            with self.subTest(value=value):
                self.owner["usedEvents"] = value
                with self.refuse("usedEvents"):
                    self.validate()
        self.owner["usedEvents"] = []
        with self.refuse("descriptors differ"):
            self.validate()

    def test_modern_membership_stays_strict(self):
        output = compiler_output("0.8.22")
        self.validate(VERSIONS["0.8.22"], output=output)
        owner = next(node for node in output["sources"][self.path]["ast"]["nodes"]
                     if node.get("name") == "Derived")
        del owner["usedEvents"]
        with self.refuse("usedEvents"):
            self.validate(VERSIONS["0.8.22"], output=output)

    def test_inherited_events_resolve_from_excluded_sources(self):
        dependencies = [self.owners["Base"], self.owners["IBase"]]
        for node in dependencies:
            self.nodes.remove(node)
            del self.output["contracts"][self.path][node["name"]]
        self.output["sources"]["excluded.sol"] = {
            "id": 1, "ast": {"id": 100000, "nodeType": "SourceUnit", "nodes": dependencies}}
        self.validate()
        del self.output["sources"]["excluded.sol"]["ast"]
        with self.refuse("legacy base"):
            self.validate()

    def test_legacy_abi_excludes_emitted_library_event(self):
        self.validate()
        library_row = self.output["contracts"][self.path]["Lib"]["abi"][0]
        self.assertEqual(library_row["name"], "FromLibrary")
        self.assertNotIn("FromLibrary", [row.get("name") for row in self.abi])
        self.abi.append(copy.deepcopy(library_row))
        with self.refuse("descriptors differ"):
            self.validate()

    def test_inherited_overload_and_anonymous_descriptors_are_checked(self):
        self.validate()
        self.assertEqual(len([row for row in self.abi if row.get("name") == "Ping"]), 2)
        inherited = next(row for row in self.abi if row.get("name") == "Seen")
        self.assertIs(inherited["anonymous"], True)
        inherited["anonymous"] = False
        with self.refuse("Derived.*anonymous"):
            self.validate()

    def test_first_external_signature_keeps_first_complete_descriptor(self):
        inherited = next(node for node in self.owners["IBase"]["nodes"]
                         if node["nodeType"] == "EventDefinition")
        override = self.clone(inherited)
        override["anonymous"] = True
        override["parameters"]["parameters"][0].update(name="replacement", indexed=False)
        self.owner["nodes"].insert(0, override)
        row = next(row for row in self.abi if row.get("name") == "Ping"
                   and row["inputs"][0]["type"] == "address")
        original = copy.deepcopy(row)
        row["anonymous"] = True
        row["inputs"][0].update(name="replacement", indexed=False)
        self.validate()
        row.update(original)
        with self.refuse("descriptors differ"):
            self.validate()

    def test_missing_extra_and_duplicate_abi_events_refuse(self):
        for mode in ("missing", "extra", "duplicate"):
            with self.subTest(mode=mode):
                self.setUp()
                row = next(row for row in self.abi if row.get("name") == "Changed")
                if mode == "missing":
                    self.abi.remove(row)
                else:
                    self.abi.append({**row, "name": "Other"} if mode == "extra" else copy.deepcopy(row))
                with self.refuse("descriptors differ"):
                    self.validate()

    def test_missing_malformed_or_reordered_base_membership_refuses(self):
        own_id = self.owner["id"]
        base_id = self.owners["Base"]["id"]
        for value in (None, {}, [], [True], [-1], [own_id, own_id], [base_id, own_id]):
            with self.subTest(value=value):
                self.owner["linearizedBaseContracts"] = value
                with self.refuse("legacy base"):
                    self.validate()
        del self.owner["linearizedBaseContracts"]
        with self.refuse("legacy base"):
            self.validate()

    def test_unresolved_or_wrong_base_kind_refuses(self):
        for ref in (999999, self.owners["IBase"]["nodes"][0]["id"], self.owners["Lib"]["id"]):
            with self.subTest(ref=ref):
                self.owner["linearizedBaseContracts"] = [self.owner["id"], ref]
                with self.refuse("legacy base"):
                    self.validate()
        self.setUp()
        self.owners["Base"]["contractKind"] = "wrong"
        with self.refuse("owner kind|legacy base"):
            self.validate()

    def test_missing_owner_and_event_ids_refuse(self):
        for target in (self.owner, self.owner["nodes"][0]):
            saved = target.pop("id")
            with self.refuse("legacy base|legacy event id"):
                self.validate()
            target["id"] = saved

    def test_missing_malformed_or_unknown_declarations_refuse(self):
        for value in (None, {}, [None], [{}], [{"nodeType": "Bogus"}]):
            with self.subTest(value=value):
                self.owner["nodes"] = value
                with self.refuse("legacy declaration"):
                    self.validate()
        del self.owner["nodes"]
        with self.refuse("legacy declaration"):
            self.validate()

    def test_base_and_declaration_list_limits_are_inclusive(self):
        self.validate()
        # Seven ABI rows dominate the common per-list limit in this fixture.
        # Test legacy lists in isolation so the bound is reached by that list.
        nodes = {node["id"]: node for node in self.owners.values()}
        types = solidity._EventTypes(nodes)
        owner = {"id": 1, "nodeType": "ContractDefinition", "contractKind": "contract",
                 "linearizedBaseContracts": [1], "nodes": []}
        nodes[1] = owner
        with mock.patch.object(solidity, "EVENT_ITEM_LIMIT", 1):
            membership = solidity._LegacyEventMembership(nodes, types)
            self.assertEqual(membership.descriptors(owner, "bound"), [])
            owner["linearizedBaseContracts"].append(self.owner["id"])
            with self.refuse("legacy base"):
                membership.descriptors(owner, "bound")
            owner["linearizedBaseContracts"] = [1]
            owner["nodes"] = [{"nodeType": "UsingForDirective"}]
            self.assertEqual(membership.descriptors(owner, "bound"), [])
            owner["nodes"].append({"nodeType": "UsingForDirective"})
            with self.refuse("legacy declarations"):
                membership.descriptors(owner, "bound")

    def test_aggregate_visit_limit_includes_repeated_bases_and_declarations(self):
        expected_visits = sum(
            1 + len(next(node for node in self.owners.values() if node["id"] == ref)["nodes"])
            for owner in self.owners.values() for ref in owner["linearizedBaseContracts"])
        self.assertGreater(expected_visits, sum(1 + len(node["nodes"]) for node in self.owners.values()))
        with mock.patch.object(solidity, "EVENT_LEGACY_VISIT_LIMIT", expected_visits):
            self.validate()
        with mock.patch.object(solidity, "EVENT_LEGACY_VISIT_LIMIT", expected_visits - 1):
            with self.refuse("legacy membership traversal limit exceeded"):
                self.validate()
        self.assertEqual(solidity.EVENT_LEGACY_VISIT_LIMIT, 1_000_000)

    def test_indexed_disagreement_refuses_without_creating_outputs(self):
        row = next(row for row in self.abi if row.get("name") == "Changed")
        row["inputs"][1]["indexed"] = False
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "refused"
            status, stdout, stderr = run_cli(self.output, VERSIONS["0.8.10"], destination)
            self.assertEqual(status, 1, stdout + stderr)
            self.assertIn("Derived: event descriptors differ (Changed: inputs[1].indexed)", stderr)
            self.assertEqual(list(destination.iterdir()), [])

    def test_late_unit_disagreement_preserves_existing_outputs(self):
        healthy = compiler_output("0.8.10")
        row = next(row for row in self.abi if row.get("name") == "Changed")
        row["inputs"][0]["name"] = "different"
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary)
            for name in ("chunks.jsonl", "provenance.jsonl"):
                (destination / name).write_bytes(b"preserve existing bytes\n")
            before = {path.name: path.read_bytes() for path in destination.iterdir()}
            status, stdout, stderr = run_cli(
                healthy, VERSIONS["0.8.10"], destination,
                later_outputs=(self.output,), existing=True)
            self.assertEqual(status, 1, stdout + stderr)
            self.assertIn("name/order", stderr)
            self.assertEqual({path.name: path.read_bytes() for path in destination.iterdir()}, before)

    def test_validation_does_not_fabricate_compiler_membership(self):
        before = copy.deepcopy(self.output)
        self.validate()
        self.assertEqual(self.output, before)


class TupleSignatureTests(unittest.TestCase):
    """Synthetic AST mutations isolate tuple names from canonical wire types."""

    def setUp(self):
        def user(ref):
            return {"nodeType": "UserDefinedTypeName", "referencedDeclaration": ref}

        def member(name, kind):
            return {"nodeType": "VariableDeclaration", "name": name, "typeName": kind}

        def array(base, dimension):
            suffix = "dyn" if dimension == "" else dimension
            return {"nodeType": "ArrayTypeName", "baseType": base,
                    "length": None if dimension == "" else {"nodeType": "Literal"},
                    "typeDescriptions": {"typeIdentifier": f"t_array$_x_${suffix}_storage_ptr",
                                         "typeString": f"struct Outer[{dimension}]"}}

        def event(number, ref, name):
            return {"id": number, "nodeType": "EventDefinition", "name": "Nested",
                    "anonymous": False, "parameters": {"nodeType": "ParameterList", "parameters": [
                        {**member(name, array(array(user(ref), ""), "2")), "indexed": False}]}}

        self.first = event(2, 200, "first")
        self.second = event(11, 201, "second")
        owners = [
            {"id": 1, "nodeType": "ContractDefinition", "name": "Derived", "contractKind": "contract",
             "linearizedBaseContracts": [1, 10], "nodes": [self.first]},
            {"id": 10, "nodeType": "ContractDefinition", "name": "Base", "contractKind": "contract",
             "linearizedBaseContracts": [10], "nodes": [self.second]},
        ]
        structs = []
        for outer, inner, name in ((200, 300, "first"), (201, 301, "second")):
            structs.extend([
                {"id": outer, "nodeType": "StructDefinition", "members": [member(name, user(inner))]},
                {"id": inner, "nodeType": "StructDefinition", "members": [member(name,
                    {"nodeType": "ElementaryTypeName", "name": "uint"})]},
            ])
        self.row = {"type": "event", "name": "Nested", "anonymous": False, "inputs": [
            {"name": "first", "indexed": False, "type": "tuple[][2]", "components": [
                {"name": "first", "type": "tuple", "components": [{"name": "first", "type": "uint256"}]}]}]}
        self.output = {
            "sources": {
                "selected.sol": {"id": 0, "ast": {"id": 400, "nodeType": "SourceUnit", "nodes": owners[:1]}},
                "excluded.sol": {"id": 1, "ast": {"id": 401, "nodeType": "SourceUnit", "nodes": owners[1:] + structs}},
            },
            "contracts": {"selected.sol": {"Derived": {"abi": [self.row]}}},
        }

    def validate(self):
        solidity.validate_event_agreement(self.output, {"selected.sol"}, VERSIONS["0.8.19"])

    def test_recursive_tuple_names_do_not_create_an_overload(self):
        self.validate()
        self.row["inputs"][0]["components"][0]["components"][0]["name"] = "second"
        with self.assertRaisesRegex(solidity.ChunkError, "components.*name/order"):
            self.validate()

    def test_array_dimensions_remain_part_of_the_external_signature(self):
        array = self.second["parameters"]["parameters"][0]["typeName"]
        array["typeDescriptions"] = {"typeIdentifier": "t_array$_x_$3_storage_ptr",
                                     "typeString": "struct Outer[][3]"}
        with self.assertRaisesRegex(solidity.ChunkError, "AST-only: Nested"):
            self.validate()

    def test_nested_tuple_types_remain_part_of_the_external_signature(self):
        struct = next(node for node in self.output["sources"]["excluded.sol"]["ast"]["nodes"]
                      if node.get("id") == 301)
        struct["members"][0]["typeName"]["name"] = "address"
        with self.assertRaisesRegex(solidity.ChunkError, "AST-only: Nested"):
            self.validate()


if __name__ == "__main__":
    unittest.main()
