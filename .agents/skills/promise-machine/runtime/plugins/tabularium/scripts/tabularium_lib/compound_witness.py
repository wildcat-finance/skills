"""Offline Compound III execution facts from a verified Alexandria release."""

from __future__ import annotations

import hashlib
import importlib
import os
from pathlib import Path
import stat
import sys

from .core import (
    TabulariumError,
    canonical_json,
    jsonl_bytes,
    loads_json,
    sha256_bytes,
    write_bytes_atomic,
)
from .keccak import mapping_slot


PROXY = "0xc3d688b66703497daa19211eedff47f25384cdc3"
USER_BASIC_MAPPING_SLOT = 5
SLOT_ZERO = "0x" + "0" * 64
SUPPLY_FROM = "0x90323177"
WITHDRAW_FROM = "0x26441318"
FACT_FORMAT = "tabularium-compound-v3-execution-fact/v1"
MANIFEST_FORMAT = "tabularium-compound-v3-witness/v1"
MAX_FACT_BYTES = 1_048_576
MAX_WITNESS_BYTES = 1_048_576


def debt_transfer_conformance(principal_source_before, principal_source_after,
                              principal_destination_before, principal_destination_after):
    """Validate the hostile no-log debt-to-debt shape used by the Phase 1 fixture."""
    values = (
        principal_source_before, principal_source_after,
        principal_destination_before, principal_destination_after,
    )
    if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
        raise TabulariumError("debt-transfer principals must be integers")
    if any(not -(1 << 103) <= value < (1 << 103) for value in values):
        raise TabulariumError("debt-transfer principal is outside signed int104")
    if not (principal_source_before < 0 and principal_destination_before < 0):
        raise TabulariumError("debt-transfer fixture must start with debt on both sides")
    if principal_source_after >= principal_source_before:
        raise TabulariumError("debt-transfer source debt did not increase")
    if principal_destination_after <= principal_destination_before:
        raise TabulariumError("debt-transfer destination debt did not decrease")
    return {
        "destination_principal_delta": principal_destination_after - principal_destination_before,
        "source_principal_delta": principal_source_after - principal_source_before,
    }


def _alexandria_api():
    plugins_root = Path(__file__).resolve().parents[3]
    alexandria_scripts = plugins_root / "alexandria" / "scripts"
    if not alexandria_scripts.is_dir():
        raise TabulariumError("the Alexandria plugin is required to verify a Compound witness")
    sys.path.insert(0, str(alexandria_scripts))
    try:
        phase0 = importlib.import_module("alexandria_lib.compound_phase0")
        from alexandria_lib.errors import AlexandriaError  # pylint: disable=import-outside-toplevel
    except ImportError as error:
        raise TabulariumError("Alexandria Compound verification API is unavailable") from error
    module_file = getattr(phase0, "__file__", None)
    if not isinstance(module_file, str):
        raise TabulariumError("loaded Alexandria verifier has no local module path")
    module_path = Path(module_file).resolve()
    try:
        module_path.relative_to(alexandria_scripts.resolve())
    except ValueError as error:
        raise TabulariumError("loaded Alexandria verifier is outside the sibling plugin") from error
    return phase0.check_phase0, phase0.load_phase0, phase0.load_phase0_responses, AlexandriaError


def _word(value, label):
    if not isinstance(value, str):
        raise TabulariumError("%s is not a hexadecimal word" % label)
    digits = value[2:] if value.startswith("0x") else value
    if not digits or len(digits) > 64:
        raise TabulariumError("%s is not a bounded hexadecimal word" % label)
    try:
        int(digits, 16)
    except ValueError as error:
        raise TabulariumError("%s is not hexadecimal" % label) from error
    return "0x" + digits.lower().rjust(64, "0")


def _address_word(input_data, argument, label):
    start = 10 + argument * 64
    end = start + 64
    if not isinstance(input_data, str) or len(input_data) < end:
        raise TabulariumError("%s calldata is truncated" % label)
    word = input_data[start:end]
    if word[:24] != "0" * 24:
        raise TabulariumError("%s address argument is not ABI-canonical" % label)
    return "0x" + word[-40:].lower()


def _address(value, label):
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise TabulariumError("%s is not an address" % label)
    try:
        int(value[2:], 16)
    except ValueError as error:
        raise TabulariumError("%s is not a hexadecimal address" % label) from error
    return value.lower()


def _hex_data(value, label):
    if not isinstance(value, str) or not value.startswith("0x") or len(value) % 2:
        raise TabulariumError("%s is not hexadecimal data" % label)
    try:
        bytes.fromhex(value[2:])
    except ValueError as error:
        raise TabulariumError("%s is not hexadecimal data" % label) from error
    return value.lower()


def _bounded_file_bytes(path, limit, label):
    path = Path(path)
    required = ("O_CLOEXEC", "O_NOFOLLOW", "O_NONBLOCK")
    if any(not hasattr(os, name) for name in required):
        raise TabulariumError("safe local file reads are unavailable")
    descriptor = None
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW | os.O_NONBLOCK,
        )
    except OSError as error:
        raise TabulariumError("%s is unavailable" % label) from error
    try:
        try:
            before = os.fstat(descriptor)
        except OSError as error:
            raise TabulariumError("%s metadata is unavailable" % label) from error
        if not stat.S_ISREG(before.st_mode):
            raise TabulariumError("%s is not a regular file" % label)
        if before.st_size > limit:
            raise TabulariumError("%s exceeds the byte limit" % label)
        chunks = []
        remaining = limit + 1
        while remaining:
            block = os.read(descriptor, min(65_536, remaining))
            if not block:
                break
            chunks.append(block)
            remaining -= len(block)
        after = os.fstat(descriptor)
        data = b"".join(chunks)
        if (
            len(data) > limit
            or len(data) != before.st_size
            or (before.st_dev, before.st_ino, before.st_size)
            != (after.st_dev, after.st_ino, after.st_size)
        ):
            raise TabulariumError("%s changed while it was read" % label)
        return data
    finally:
        os.close(descriptor)


def decode_principal(word):
    """Decode the signed int104 principal from a packed userBasic word."""
    value = int(_word(word, "userBasic word"), 16) & ((1 << 104) - 1)
    if value & (1 << 103):
        value -= 1 << 104
    return value


def _borrow_index(word):
    return (int(_word(word, "totals slot zero"), 16) >> 64) & ((1 << 64) - 1)


def _walk_calls(frame, path=()):
    yield path, frame
    calls = frame.get("calls", [])
    if not isinstance(calls, list):
        raise TabulariumError("call trace children are not a list")
    for index, child in enumerate(calls):
        if not isinstance(child, dict):
            raise TabulariumError("call trace child is not an object")
        yield from _walk_calls(child, path + (index,))


def _source_digest(manifest, name):
    matches = [item for item in manifest["components"] if item["name"] == name]
    if len(matches) != 1:
        raise TabulariumError("Alexandria component %s is missing or duplicated" % name)
    return matches[0]["sha256"]


def _make_bytes(release_root):
    check_phase0, load_phase0, load_responses, alexandria_error = _alexandria_api()
    try:
        receipt = check_phase0(release_root)
        release_id, manifest, corpus, _registry = load_phase0(Path(release_root))
        responses = load_responses(Path(release_root).absolute(), manifest, corpus)
    except alexandria_error as error:
        raise TabulariumError("Alexandria Compound release failed verification: %s" % error) from error

    transaction_hash = corpus["recent"]["transaction_hash"]
    block_hash = corpus["recent"]["block_hash"]
    call_trace = responses["recent-call-trace"]["result"]
    opcode = responses["recent-opcode-trace"]["result"]
    prestate = responses["recent-prestate-trace"]["result"]
    implementation_word = _word(responses["recent-implementation-slot"]["result"], "implementation slot")
    implementation = "0x" + implementation_word[-40:]

    component_digests = {
        name: _source_digest(manifest, name)
        for name in (
            "registry",
            "response-recent-call-trace",
            "response-recent-opcode-trace",
            "response-recent-prestate-trace",
            "response-recent-implementation-slot",
            "response-recent-implementation-code",
            "upstream-configuration-json",
            "upstream-deploy-ts",
            "upstream-relations-ts",
            "upstream-roots-json",
        )
    }
    recent_receipt = next(
        item for item in receipt["transactions"] if item["label"] == "recent"
    )
    implementation_code_sha256 = recent_receipt["implementation_code_sha256"]
    facts = []
    comet_calls = []
    for call_path, frame in _walk_calls(call_trace):
        if str(frame.get("to", "")).lower() != PROXY or "error" in frame:
            continue
        input_data = _hex_data(frame.get("input"), "Comet call input")
        selector = input_data[:10] if isinstance(input_data, str) else ""
        if selector not in (SUPPLY_FROM, WITHDRAW_FROM):
            raise TabulariumError("successful Comet call uses an unsupported Phase 0 selector")
        comet_calls.append((call_path, frame))
        facts.append({
            "block_hash": block_hash,
            "call_path": list(call_path),
            "call_type": frame.get("type"),
            "caller": _address(frame.get("from"), "Comet caller"),
            "format": FACT_FORMAT,
            "implementation": implementation,
            "implementation_code_sha256": implementation_code_sha256,
            "input": input_data,
            "kind": "call",
            "ordinal": len(comet_calls) - 1,
            "output": _hex_data(frame.get("output", "0x"), "Comet call output"),
            "selector": selector,
            "source": {
                "component": "response-recent-call-trace",
                "json_pointer": "/result" + "".join("/calls/%d" % index for index in call_path),
                "sha256": component_digests["response-recent-call-trace"],
            },
            "success": True,
            "target": PROXY,
            "transaction_hash": transaction_hash,
        })
    if [path for path, _ in comet_calls] != [(0,), (1,)]:
        raise TabulariumError("Phase 0 witness does not contain the expected two ordered Comet calls")
    withdraw = comet_calls[1][1]
    if any(frame.get("type") != "CALL" for _, frame in comet_calls):
        raise TabulariumError("Phase 0 Comet calls are not CALL frames")
    if withdraw["input"][:10] != WITHDRAW_FROM:
        raise TabulariumError("Phase 0 second Comet call is not withdrawFrom")
    account = _address_word(withdraw["input"], 0, "withdrawFrom")
    user_slot = mapping_slot(account, USER_BASIC_MAPPING_SLOT)

    pre_accounts = prestate.get("pre")
    post_accounts = prestate.get("post")
    if not isinstance(pre_accounts, dict) or not isinstance(post_accounts, dict):
        raise TabulariumError("prestate tracer did not return account maps")
    proxy_pre = pre_accounts.get(PROXY, {})
    proxy_post = post_accounts.get(PROXY, {})
    if not isinstance(proxy_pre, dict) or not isinstance(proxy_post, dict):
        raise TabulariumError("prestate tracer did not return proxy account objects")
    pre_storage = proxy_pre.get("storage", {})
    post_storage = proxy_post.get("storage", {})
    if not isinstance(pre_storage, dict) or not isinstance(post_storage, dict):
        raise TabulariumError("prestate tracer did not return proxy storage maps")
    current = {
        SLOT_ZERO: _word(pre_storage.get(SLOT_ZERO, "0x0"), "prestate slot zero"),
        user_slot: _word(pre_storage.get(user_slot, "0x0"), "prestate userBasic"),
    }
    initial = dict(current)
    struct_logs = opcode.get("structLogs")
    if not isinstance(struct_logs, list):
        raise TabulariumError("opcode trace has no structLogs list")
    storage_facts = []
    active_call_path = None
    next_call_index = 0
    for index, item in enumerate(struct_logs):
        depth = item.get("depth")
        if depth is not None and depth <= 2:
            active_call_path = None
        if item.get("op") == "DELEGATECALL" and depth == 2:
            stack = item.get("stack")
            if not isinstance(stack, list) or len(stack) < 2:
                raise TabulariumError("DELEGATECALL stack is incomplete")
            target = "0x" + _word(stack[-2], "DELEGATECALL target")[-40:]
            if target == implementation:
                if next_call_index >= len(comet_calls):
                    raise TabulariumError("opcode trace has an extra Comet delegatecall")
                active_call_path = list(comet_calls[next_call_index][0])
                next_call_index += 1
        if item.get("op") != "SSTORE":
            continue
        stack = item.get("stack")
        if not isinstance(stack, list) or len(stack) < 2:
            raise TabulariumError("SSTORE stack is incomplete")
        slot = _word(stack[-1], "SSTORE slot")
        if slot not in current:
            continue
        if item.get("depth") != 3 or active_call_path is None:
            raise TabulariumError("relevant storage write is not bound to a Comet call")
        if not isinstance(item.get("pc"), int) or isinstance(item.get("pc"), bool) or item["pc"] < 0:
            raise TabulariumError("relevant storage write has an invalid program counter")
        written = _word(stack[-2], "SSTORE value")
        fact = {
            "block_hash": block_hash,
            "call_path": active_call_path,
            "depth": item["depth"],
            "format": FACT_FORMAT,
            "implementation": implementation,
            "implementation_code_sha256": implementation_code_sha256,
            "kind": "storage-write",
            "opcode_index": index,
            "ordinal": len(storage_facts),
            "pc": item["pc"],
            "prior_word": current[slot],
            "slot": slot,
            "source": {
                "component": "response-recent-opcode-trace",
                "json_pointer": "/result/structLogs/%d" % index,
                "sha256": component_digests["response-recent-opcode-trace"],
            },
            "storage_address": PROXY,
            "transaction_hash": transaction_hash,
            "written_word": written,
        }
        storage_facts.append(fact)
        current[slot] = written
    if next_call_index != len(comet_calls):
        raise TabulariumError("opcode trace is missing a Comet delegatecall")
    if not storage_facts or not any(item["slot"] == user_slot for item in storage_facts):
        raise TabulariumError("opcode trace has no ordered userBasic write")
    for slot in (SLOT_ZERO, user_slot):
        expected = _word(post_storage.get(slot, "0x0"), "poststate storage")
        if current[slot] != expected:
            raise TabulariumError("ordered SSTORE replay does not match the poststate diff")
    facts.extend(storage_facts)
    principal_before = decode_principal(initial[user_slot])
    principal_after = decode_principal(current[user_slot])
    if (principal_before, principal_after) != (0, -6349137978):
        raise TabulariumError("Phase 0 signed principal transition does not match the witness")
    facts.append({
        "account": account,
        "base_borrow_index": _borrow_index(current[SLOT_ZERO]),
        "block_hash": block_hash,
        "format": FACT_FORMAT,
        "implementation": implementation,
        "implementation_code_sha256": implementation_code_sha256,
        "kind": "principal-transition",
        "packed_after": current[user_slot],
        "packed_before": initial[user_slot],
        "principal_after": principal_after,
        "principal_before": principal_before,
        "principal_delta": principal_after - principal_before,
        "slot": user_slot,
        "sources": [
            {
                "component": "response-recent-prestate-trace",
                "json_pointer": "/result/pre/%s/storage" % PROXY,
                "sha256": component_digests["response-recent-prestate-trace"],
            },
            {
                "component": "response-recent-prestate-trace",
                "json_pointer": "/result/post/%s/storage/%s" % (PROXY, user_slot),
                "sha256": component_digests["response-recent-prestate-trace"],
            },
            *[
                item["source"] for item in storage_facts if item["slot"] == user_slot
            ],
        ],
        "transaction_hash": transaction_hash,
    })
    facts_bytes = jsonl_bytes(facts)
    witness_manifest = {
        "alexandria_method_receipt": receipt,
        "alexandria_release_id": release_id,
        "component_digests": component_digests,
        "facts_bytes": len(facts_bytes),
        "facts_sha256": sha256_bytes(facts_bytes),
        "format": MANIFEST_FORMAT,
        "registry_commit": corpus["registry_commit"],
        "scope": "one Ethereum USDC transaction; method proof, not market history",
        "row_count": len(facts),
        "transaction_hash": transaction_hash,
    }
    manifest_bytes = canonical_json(witness_manifest) + b"\n"
    return facts_bytes, manifest_bytes, witness_manifest


def build_compound_witness(release_root, facts_path, manifest_path):
    release_root = Path(release_root).resolve(strict=True)
    facts_path = Path(facts_path)
    manifest_path = Path(manifest_path)
    if facts_path.is_symlink() or manifest_path.is_symlink():
        raise TabulariumError("Compound witness outputs must not be symlinks")
    facts_parent = facts_path.parent.resolve(strict=True)
    manifest_parent = manifest_path.parent.resolve(strict=True)
    resolved_facts = facts_parent / facts_path.name
    resolved_manifest = manifest_parent / manifest_path.name
    if resolved_facts == resolved_manifest:
        raise TabulariumError("Compound witness outputs alias each other")
    if release_root == resolved_facts or release_root in resolved_facts.parents or release_root == resolved_manifest or release_root in resolved_manifest.parents:
        raise TabulariumError("Compound witness outputs must stay outside the Alexandria release")
    facts_bytes, manifest_bytes, manifest = _make_bytes(release_root)
    existing = (facts_path.exists(), manifest_path.exists())
    if any(existing):
        if not all(existing):
            raise TabulariumError("Compound witness output pair is incomplete")
        if (
            _bounded_file_bytes(facts_path, MAX_FACT_BYTES, "existing Compound facts") != facts_bytes
            or _bounded_file_bytes(manifest_path, MAX_WITNESS_BYTES, "existing Compound manifest") != manifest_bytes
        ):
            raise TabulariumError("Compound witness outputs already contain different bytes")
        return manifest
    write_bytes_atomic(facts_bytes, facts_path)
    write_bytes_atomic(manifest_bytes, manifest_path)
    return manifest


def verify_compound_witness(release_root, facts_path, manifest_path):
    facts_path = Path(facts_path)
    manifest_path = Path(manifest_path)
    supplied_facts = _bounded_file_bytes(facts_path, MAX_FACT_BYTES, "Compound facts")
    supplied_manifest = _bounded_file_bytes(manifest_path, MAX_WITNESS_BYTES, "Compound manifest")
    parsed = loads_json(supplied_manifest, "Compound witness manifest")
    facts_bytes, manifest_bytes, expected = _make_bytes(Path(release_root).resolve(strict=True))
    if supplied_facts != facts_bytes or supplied_manifest != manifest_bytes or parsed != expected:
        raise TabulariumError("Compound witness bytes do not match the verified Alexandria release")
    if hashlib.sha256(supplied_facts).hexdigest() != expected["facts_sha256"]:
        raise TabulariumError("Compound witness fact digest does not match")
    return expected
