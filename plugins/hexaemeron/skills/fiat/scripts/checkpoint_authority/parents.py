"""Join a signed parent link to exact native producer bytes and accepted history."""
from __future__ import annotations

from .canonical import Refusal, canonical, decode, digest
from .native import NativeResult
from .native_records import identity_result, ledger


def native_projection(result, producer, validation):
    """Consume a caller-owned current NativeResult and its exact producer ledger.

    Signature policy authenticates the validator separately. This does not run
    native commands or turn an arbitrary result dictionary into execution proof.
    """
    if not isinstance(result, NativeResult) or type(producer) is not bytes:
        raise Refusal("native-evidence-required", "parents")
    value = result.record
    if (value.get("schema") != "checkpoint-authority-native-result/v1"
        or value.get("complete") is not True or value.get("operation_ran") is not True
        or digest(result.payload) != validation["output_sha256"]):
        raise Refusal("native-evidence-binding", "parents")
    request = value["request"]
    for field in ("candidate_id", "attempt_id", "lease_id", "carrier_length"):
        if request.get(field) != validation[field]:
            raise Refusal("native-evidence-binding", "parents")
    if any(request.get(field) != expected for field, expected in validation["identities"].items()):
        raise Refusal("native-evidence-binding", "parents")
    if any(value.get(field) != expected for field, expected in validation["native"].items()):
        raise Refusal("native-evidence-binding", "parents")
    stages = value.get("native_results")
    if type(stages) is not list or len(stages) != 4:
        raise Refusal("native-evidence-binding", "parents")
    for actual, expected in zip(stages, validation["native_results"]):
        if any(actual.get(field) != expected[field] for field in expected):
            raise Refusal("native-evidence-binding", "parents")
    coverage = value.get("coverage", {})
    verified = coverage.get("verified", [])
    if (coverage.get("complete") is not True or type(verified) is not list
        or coverage.get("required") != validation["coverage"]["required"]
        or any(type(row) is not dict or type(row.get("fingerprint")) is not str for row in verified)
        or [{field: row.get(field) for field in ("commit", "enrollment", "evidence_class")}
            for row in verified] != validation["coverage"]["verified"]):
        raise Refusal("native-coverage-binding", "parents")
    ident = identity_result(value["identity"])["identity"]
    evidence, run = ident["evidence"], ident["run"]
    rows = ledger(producer)
    if (len(rows) != evidence["ledger_entries"] or rows[-1]["hash"] != evidence["ledger_tail"]
        or digest(producer) != evidence["ledger_sha256"]
        or value["identity"]["snapshot_id"] != validation["identities"]["snapshot_id"]):
        raise Refusal("native-producer-binding", "parents")
    # Only prefix byte commitments survive this call; no producer bodies are retained.
    import hashlib
    hasher = hashlib.sha256()
    prefixes = []
    for line in producer.splitlines(keepends=True):
        hasher.update(line)
        prefixes.append(hasher.hexdigest())
    return {"anchor": digest(canonical(run)), "initial_base": run["initial_base_sha"],
            "run_id": run["run_id"], "prefixes": tuple(prefixes),
            "producer": evidence["ledger_sha256"], "count": len(rows),
            "signers": tuple((row["enrollment"], row["fingerprint"]) for row in verified)}


def check_parent(link, registration, native, decisions, acceptance, registration_id):
    """Require a root or the unique longest accepted producer prefix, with all ancestors."""
    if (link["registration"]["sha256"] != registration_id
        or link["initial_base"] != registration["initial_base"]
        or acceptance["initial_base"] != registration["initial_base"]
        or native["initial_base"] != registration["initial_base"]
        or native["anchor"] != registration["native_anchor_sha256"]
        or native["run_id"] != acceptance["scope"]["run_id"]
        or link["native"] != registration["source"]
        or acceptance["native"] != registration["source"]
        or link["producer_prefix_sha256"] != native["producer"]):
        raise Refusal("parent-run-base", "parents")
    matching = [item for item in decisions.values() if item.get("state") == "authorize"
        and item["registration"] == registration_id and item["publication"] == "complete"
        and item["producer_count"] < native["count"]
        and native["prefixes"][item["producer_count"]-1] == item["producer"]]
    parent = None
    if matching:
        longest = max(item["producer_count"] for item in matching)
        choices = [item for item in matching if item["producer_count"] == longest]
        if len(choices) != 1:
            raise Refusal("parent-ambiguous", "parents")
        parent = choices[0]
        prior = [*parent["prior"], {"type": "acceptance", "sha256": parent["receipt"]}]
        if len(prior) > 64 or link["parents"] != prior[-1:] or link["prior_receipts"] != prior:
            raise Refusal("parent-inventory", "parents")
        if acceptance["parent_acceptance_ids"] != [parent["acceptance_id"]]:
            raise Refusal("parent-identity", "parents")
        transition = acceptance["transition"]
        if (transition["kind"] != "continuation" or transition["producer_prefix_sha256"] != native["producer"]
            or transition["parent"]["sha256"] != acceptance["parent_link"]):
            raise Refusal("parent-transition", "parents")
        if parent["poisoned"]:
            raise Refusal("poisoned-parent", "parents")
    else:
        prior = []
        if (not registration["root_authorized"] or registration["initial_parent"] is not None
            or link["parents"] or link["prior_receipts"] or acceptance["parent_acceptance_ids"]
            or acceptance["transition"] != {"kind": "registered-root", "registration": link["registration"]}):
            raise Refusal("root-permission", "parents")
    return prior, None if parent is None else parent["acceptance_id"]
