"""Rebuild finite retained inputs; absence never becomes a positive join.

Only owned temporary outputs are removed. Python exceptions, including
KeyboardInterrupt, run cleanup; an uncatchable process kill can leave scratch.
The caller's staging trees remain unchanged. Public observations contain
release identities, digests and bounded outcomes, with no capture inventory.
"""

from __future__ import annotations

import os
from pathlib import Path
import shutil

import wildcat_batch_retained as owner
from wildcat_sanctions_fixtures import ESCROWED, QUEUED
from wildcat_sanctions_reports import EvidenceUnavailable
from tabularium_lib.keccak import keccak256
from tabularium_lib.wildcat_source import load_raw

GENERATIONS = owner.GENERATIONS
TARGETS = (QUEUED, ESCROWED)
TOPICS = frozenset("0x" + keccak256(signature.encode()).hex() for signature in TARGETS)
VERSION = "1.3.0"


def classification(source, coverage, native_records):
    """Require every native target to have one reciprocal supporting relation."""
    native = sum(raw.get("topics", [None])[0] in TOPICS
                 for raw, _ in native_records if raw.get("topics"))
    mappings = {row["source_selector"]: row for row in source["mapping_records"]}
    companions = [row for row in mappings.values() if row["signature"] in TARGETS]
    gaps = coverage["coverage"]["unsupported_events"]
    if any(key.startswith("routing:sanctioned-assets-") or
           any(signature in key for signature in TARGETS) or
           (key.startswith("decode:") and key.rsplit(":", 1)[-1] in TOPICS)
           for key in gaps):
        raise EvidenceUnavailable("retained routing has an unexplained gap")
    if native != len(companions):
        raise EvidenceUnavailable("retained target is not fully mapped")
    claimed = set()
    for companion in companions:
        relations = companion.get("routing_joins")
        if companion["disposition"] != "supporting-routing" or not isinstance(relations, list) or len(relations) != 1:
            raise EvidenceUnavailable("present retained target has no unique eligible primary")
        relation, = relations
        primary = mappings.get(relation["primary_selector"])
        selector = companion["source_selector"]
        if (primary is None or relation["companion_selector"] != selector or
                relation not in primary.get("routing_joins", ()) or
                primary["source_selector"] in claimed or
                selector not in primary["supporting_selectors"] or
                primary["source_selector"] not in companion["supporting_selectors"]):
            raise EvidenceUnavailable("retained routing relation is not reciprocal and unique")
        claimed.add(primary["source_selector"])
    return "joined-present-targets" if native else "checked-absence"


def retained_conformance(generations=GENERATIONS, environ=None, witness=None):
    """Verify all custody before rebuilding, recheck afterwards, always clean up.

    Alternative generation adapters are only for constructed unittest controls.
    The public dispatcher always supplies the two fixed Alexandria owners.
    """
    environ = os.environ if environ is None else environ
    roots = [(spec, spec.custody(environ)) for spec in generations]
    checked = []
    for spec, root in roots:
        if spec.example is not None:
            module = owner.example_module(spec.example)
            manifest = module.verify_preserved()["manifest"]
            module.verify_staging_tree(root, manifest)
            checked.append((module, root, manifest))
    scratch = owner.private_scratch()
    try:
        if witness is not None:
            witness(scratch)
        observations = []
        for spec, root in roots:
            raw = spec.rebuild(root, scratch / (spec.generation + "-raw"))
            admitted = load_raw(raw)
            canonical = scratch / (spec.generation + "-canonical")
            owner.build_wildcat_canonical(raw, canonical, spec.generation + "-sanctions-retained-v0",
                                          adapter_version=VERSION)
            owner.verifier.verify(canonical / "coverage.json")
            source = owner.document(canonical / "source.json")
            coverage = owner.document(canonical / "coverage.json")
            outcome = classification(source, coverage, admitted["records"])
            observations.append({"generation": spec.generation,
                                 "raw_release_id": admitted["release_id"],
                                 "raw_manifest_sha256": owner.sha256_file(raw / "manifest.json"),
                                 "canonical_sha256": owner.sha256_file(canonical / "events.jsonl"),
                                 "coverage_sha256": owner.sha256_file(canonical / "coverage.json"),
                                 "adapter_version": VERSION, "verified": True,
                                 "routing_coverage": outcome})
        for module, root, manifest in checked:
            module.verify_staging_tree(root, manifest)
        return True, {"inputs": observations,
                      "qualification": "finite-input-coverage; constructed positives establish branch exercise"}
    finally:
        shutil.rmtree(scratch)
