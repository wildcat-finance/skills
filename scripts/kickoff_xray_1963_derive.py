"""Derive the #1963 V1 callable denominator from the accepted private inputs.

Imported by kickoff_xray_1963_bundle for the `derive` command. It recompiles
each accepted input for ABI and AST only, changing `outputSelection` and
nothing else, then projects every callable and creation identity of the seven
contexts and each context's ABI event catalogue. The projection carries
signatures, selectors, declaring contracts and source locations; it never
carries source text or compiler output.

The caller supplies `read`, a bounded no-follow reader rooted at the accepted
corpus. The compiler wrapper and solc-js file are digest-checked before Node
runs them, and Node runs with an argument list, a timeout and a minimal
environment.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from emitter_declarations import keccak256  # noqa: E402

INPUT_DIRECTORY = "inputs/wildcat-v1-ethereum-mainnet"
WRAPPER = "compilers/solc-0.8.22"
WRAPPER_SHA256 = "e0eb336122b44bb1d27b94c9204b7dd2d87a520818d6ac77f29b6487cb52dc13"
SOLJSON = "compilers/soljson-v0.8.22+commit.4fc1097e.js"
OUTPUT_SELECTION = {"*": {"": ["ast"], "*": ["abi"]}}
MAX_OUTPUT_BYTES = 64 * 1024 * 1024
COMPILE_SECONDS = 300
IDENTITY_KEYS = ("id", "input", "context", "kind", "signature", "selector", "mutability", "declared_in",
                 "source_ref", "origin")


class DeriveError(Exception):
    """One named derivation failure; nothing is written."""

    def __init__(self, code: str, where: str, detail: str):
        self.finding = {"code": code, "path": where, "detail": detail}
        super().__init__(f"{code}: {where}: {detail}")


def _require(condition: bool, code: str, where: str, detail: str) -> None:
    if not condition:
        raise DeriveError(code, where, detail)


def abi_type(parameter: dict) -> str:
    kind = parameter["type"]
    if kind.startswith("tuple"):
        return "(" + ",".join(abi_type(child) for child in parameter["components"]) + ")" + kind[len("tuple"):]
    return kind


def _contracts(node: object, found: list) -> list:
    if isinstance(node, dict):
        if node.get("nodeType") == "ContractDefinition":
            found.append(node)
        for value in node.values():
            _contracts(value, found)
    elif isinstance(node, list):
        for value in node:
            _contracts(value, found)
    return found


def prepare(raw: bytes) -> bytes:
    """Change outputSelection only; keep every other field and its key order."""
    value = json.loads(raw)
    value["settings"]["outputSelection"] = OUTPUT_SELECTION
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False).encode()


def compile_input(root, prepared: bytes, read, solcjs_sha256: str) -> tuple[list[str], bytes]:
    _require(hashlib.sha256(read(WRAPPER)).hexdigest() == WRAPPER_SHA256, "compiler", WRAPPER,
             "compiler wrapper digest differs")
    _require(hashlib.sha256(read(SOLJSON)).hexdigest() == solcjs_sha256, "compiler", SOLJSON,
             "solc-js digest differs")
    argv = ["node", WRAPPER, "--standard-json"]
    try:
        process = subprocess.run(argv, input=prepared, capture_output=True, cwd=root, timeout=COMPILE_SECONDS,
                                 check=False, env={"PATH": os.environ.get("PATH", ""), "LC_ALL": "C"})
    except subprocess.TimeoutExpired as exc:
        raise DeriveError("compiler", WRAPPER, f"compiler exceeded {COMPILE_SECONDS} s") from exc
    _require(process.returncode == 0, "compiler", WRAPPER, f"compiler exited {process.returncode}")
    _require(len(process.stdout) <= MAX_OUTPUT_BYTES, "limit", WRAPPER, "compiler output exceeds 64 MiB")
    return argv, process.stdout


def project(context: str, source_path: str, input_id: str, sources: dict, output: dict) -> tuple[list[dict], list[str]]:
    """Return one context's identities and its sorted ABI event signatures."""
    errors = [row for row in output.get("errors", []) if row.get("severity") == "error"]
    _require(not errors, "compiler", input_id, f"{len(errors)} compiler error(s)")
    by_index = {entry["id"]: path for path, entry in output["sources"].items()}
    contracts = {}
    for path, entry in output["sources"].items():
        for node in _contracts(entry["ast"], []):
            contracts[node["id"]] = (path, node)
    targets = [node for path, node in contracts.values() if path == source_path and node["name"] == context]
    _require(len(targets) == 1, "derivation", f"{input_id}:{context}", "context contract not found once")
    bases = [contracts[identifier] for identifier in targets[0]["linearizedBaseContracts"]]

    def locate(match) -> tuple[str, str]:
        # The linearization runs most-derived first, so the first implemented match is the one that executes.
        for _, contract in bases:
            for node in contract["nodes"]:
                if match(node):
                    start, _, index = node["src"].split(":")
                    path = by_index[int(index)]
                    line = sources[path]["content"].encode()[:int(start)].count(b"\n") + 1
                    return contract["name"], f"{path}:{line}"
        raise DeriveError("derivation", f"{input_id}:{context}", "declaration not found in the linearization")

    rows, events, constructor = [], [], False
    for entry in output["contracts"][source_path][context]["abi"]:
        kind = entry["type"]
        if kind == "function":
            signature = entry["name"] + "(" + ",".join(abi_type(p) for p in entry["inputs"]) + ")"
            chosen = "0x" + keccak256(signature.encode()).hex()[:8]
            declared, ref = locate(lambda n: n.get("functionSelector") == chosen[2:] and (
                n.get("nodeType") == "VariableDeclaration" or n.get("implemented") is True))
            rows.append({"kind": "read" if entry["stateMutability"] in ("view", "pure") else "state-changing",
                         "signature": signature, "selector": chosen, "mutability": entry["stateMutability"],
                         "declared_in": declared, "source_ref": ref, "origin": "abi"})
        elif kind == "constructor":
            constructor = True
            signature = "constructor(" + ",".join(abi_type(p) for p in entry["inputs"]) + ")"
            declared, ref = locate(lambda n: n.get("nodeType") == "FunctionDefinition" and n.get("kind") == "constructor")
            rows.append({"kind": "creation", "signature": signature, "selector": None,
                         "mutability": entry["stateMutability"], "declared_in": declared, "source_ref": ref,
                         "origin": "abi"})
        elif kind == "event":
            _require(not entry.get("anonymous"), "derivation", f"{input_id}:{context}", "anonymous event")
            events.append(entry["name"] + "(" + ",".join(abi_type(p) for p in entry["inputs"]) + ")")
        elif kind != "error":
            raise DeriveError("derivation", f"{input_id}:{context}", f"unsupported ABI entry {kind}")
    if not constructor:
        # An inherited constructor with no parameters leaves no ABI row; the AST still names it.
        declared, ref = locate(lambda n: n.get("nodeType") == "FunctionDefinition" and n.get("kind") == "constructor")
        rows.append({"kind": "creation", "signature": "constructor()", "selector": None, "mutability": "nonpayable",
                     "declared_in": declared, "source_ref": ref, "origin": "ast"})
    for row in rows:
        row.update(input=input_id, context=context)
        row["id"] = f"{input_id}:{context}:{row['kind']}:{row['signature']}"
    return rows, sorted(set(events))


def derive(root, pins: dict, contexts: dict, compiler: dict, read) -> dict:
    """Return the complete denominator-inputs record for every pinned input."""
    derivations, rows, catalogue = [], [], {}
    for input_id, pin in sorted(pins.items()):
        raw = read(f"{INPUT_DIRECTORY}/{input_id}.json")
        _require(hashlib.sha256(raw).hexdigest() == pin.sha256, "source-identity", input_id,
                 "accepted input digest differs")
        prepared = prepare(raw)
        argv, stdout = compile_input(root, prepared, read, compiler["solcjs_sha256"])
        output = json.loads(stdout)
        sources = json.loads(raw)["sources"]
        for context, bound in sorted(contexts.items()):
            if bound.input == input_id:
                found, events = project(context, bound.source_path, input_id, sources, output)
                rows.extend(found)
                catalogue[context] = events
        derivations.append({"input": input_id, "original_input_sha256": pin.sha256,
                            "prepared_input_sha256": hashlib.sha256(prepared).hexdigest(),
                            "output_sha256": hashlib.sha256(stdout).hexdigest(),
                            "compiler": compiler["version"], "argv": argv, "exit": 0})
    return {"schema": "issue-1963-denominator-inputs/v1", "derivations": derivations,
            "identities": [{key: row[key] for key in IDENTITY_KEYS} for row in sorted(rows, key=lambda r: r["id"])],
            "events": {context: catalogue[context] for context in sorted(catalogue)}}
