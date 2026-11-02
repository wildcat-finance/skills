"""Verify retained native-state mappings without publishing retained observations.

The custody and raw-release builders belong to Alexandria. This resolver reuses
those existing checks, builds an explicit 1.2.0 canonical release and verifies
it before evaluating the required and final-group event dispositions. Public
observations contain only release identities, digests and pass booleans. An
optional private inventory callback receives qualified presence/absence rows;
its caller keeps those rows outside the public bundle.
"""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "scripts"))

from tabularium_lib.core import canonical_json, sha256_bytes
from tabularium_lib.wildcat_parameters import NATIVE_RULES, UNSUPPORTED_REASONS
from tabularium_lib.wildcat_release import build_wildcat_canonical
from wildcat_batch_retained import (DIGEST_FILES, RetainedGeneration as BaseGeneration,
                                    document, example_module, private_scratch,
                                    sha256_file, verified)
from wildcat_parameter_fixtures import INVENTORY
from wildcat_v3_reports import EvidenceUnavailable

class RetainedGeneration(BaseGeneration):
    """Refuse links in the complete staging path, including ancestors."""

    def custody(self, environ):
        root = super().custody(environ)
        current = Path(root.anchor)
        for part in root.parts[1:]:
            current /= part
            try:
                status = os.lstat(current)
            except OSError:
                raise EvidenceUnavailable(self.variable + " names an unreadable path") from None
            if stat.S_ISLNK(status.st_mode):
                raise EvidenceUnavailable(self.variable + " names a linked ancestor")
        return root


GENERATIONS = (
    RetainedGeneration("wildcat-v1", "ALEXANDRIA_WILDCAT_V1_STAGING", "wildcat-v1-interval-v0"),
    RetainedGeneration("wildcat-v2", "ALEXANDRIA_WILDCAT_V2_STAGING", "wildcat-v2-interval-v0"),
)
VERSION = "1.2.0"
RELEASE_SUFFIX = "-parameter-retained-conformance"
REQUIRED = {(row["generation"], row["role"], row["signature"], row["variant"])
            for row in INVENTORY["required"]}
FINAL = {(row["generation"], row["role"], row["signature"], row["variant"])
         for row in INVENTORY["last_group"]}
RULES = {(rule["venue"], rule["role"], rule["signature"]): rule
         for rule in NATIVE_RULES.values()}


def key(generation, record):
    return generation, record["emitter_role"], record["signature"], record["abi_variant"]


def inventory_for(generation, source):
    """Private observed/absent concrete declarations, qualified to these inputs."""
    observed = {key(generation, record) for record in source["mapping_records"]}
    rows = []
    for item in sorted(REQUIRED | FINAL):
        if item[0] == generation:
            rows.append({"generation": generation, "role": item[1], "signature": item[2],
                         "abi_variant": item[3], "present": item in observed,
                         "required": item in REQUIRED})
    return {"schema": "wildcat-parameter-private-inventory/v1", "generation": generation,
            "raw_release_id": source["raw_release"]["release_id"],
            "qualification": "absence from these retained inputs only", "declarations": rows}


def require_target(generation, source):
    """An empty required set cannot establish present-event conformance."""
    if not any(key(generation, record) in REQUIRED for record in source["mapping_records"]):
        raise EvidenceUnavailable(generation + " maps no required parameter target")


def release_conforms(generation, source, events):
    """Check every present required declaration and every present final-group row."""
    by_selector = {row["provenance"]["source_selector"]: row for row in events}
    if len(by_selector) != len(events):
        return False
    for record in source["mapping_records"]:
        identity = key(generation, record)
        if identity in REQUIRED:
            rule = RULES[identity[:3]]
            row = by_selector.get(record["source_selector"])
            if (record["disposition"] != "primary" or row is None or
                    row["action"] != rule["action"] or row["amounts"] != [] or
                    row["provenance"]["adapter_version"] != VERSION or
                    row["provenance"]["mapping_rule"] != rule["rule"] or
                    tuple(field["name"] for field in record["definition"]["abi"]["inputs"]) != rule["fields"] or
                    set(record["decoded"]) != set(rule["fields"])):
                return False
        elif identity in FINAL:
            reason = record["signature"] + ": " + UNSUPPORTED_REASONS[record["signature"]]
            if (record["disposition"] != "unsupported-canonical-meaning" or
                    record["limitations"] != [reason] or record["source_selector"] in by_selector):
                return False
    return True


def retained_conformance(generations=GENERATIONS, environ=None, witness=None, private_inventory=None):
    """Build and verify both retained generations; always remove private outputs.

    Missing custody refuses before scratch creation. The callback, if supplied,
    receives a private inventory after verification and before its temporary
    release is removed. Exceptions, including interrupted builds, still clean up.
    """
    environ = os.environ if environ is None else environ
    if not generations:
        raise EvidenceUnavailable("retained generations are absent")
    roots = [(spec, spec.custody(environ)) for spec in generations]
    scratch = private_scratch()
    inputs = []
    try:
        if witness is not None:
            witness(scratch)
        for spec, root in roots:
            raw = spec.rebuild(root, scratch / (spec.generation + "-raw"))
            canonical = scratch / (spec.generation + "-canonical")
            build_wildcat_canonical(raw, canonical, spec.generation + RELEASE_SUFFIX, VERSION)
            source = document(canonical / "source.json")
            require_target(spec.generation, source)
            # Verification rederives decoded values, emitted parties and all
            # coverage bytes. The predicate adds the criterion's scope check.
            accepted = verified(canonical)
            with (canonical / "events.jsonl").open("rb") as handle:
                events = [json.loads(line) for line in handle]
            accepted = accepted and release_conforms(spec.generation, source, events)
            private = inventory_for(spec.generation, source)
            if private_inventory is not None:
                private_inventory(private)
            inputs.append({"generation": spec.generation,
                           "raw_release_id": source["raw_release"]["release_id"],
                           **{field: sha256_file(canonical / name) for field, name in DIGEST_FILES},
                           "inventory_sha256": sha256_bytes(canonical_json(private)), "passed": accepted})
    finally:
        shutil.rmtree(scratch)
    return all(item["passed"] for item in inputs), {"inputs": inputs}


def retained_resolver(generations=GENERATIONS, witness=None):
    def resolve():
        return retained_conformance(generations, witness=witness)
    return resolve
