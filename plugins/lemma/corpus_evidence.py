#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Wildcat Labs
"""Verify captured-input custody and bounded corpus evidence joins offline."""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
from pathlib import Path
import re
import sys

import preparation as p

MAX_ROWS = 10_000


def unique(rows, key, category):
    p.require(type(rows) is list and len(rows) <= MAX_ROWS, category)
    result = {}
    for row in rows:
        p.require(type(row) is dict and type(row.get(key)) is str, category)
        p.require(row[key] not in result, category)
        result[row[key]] = row
    return result


def load(pin, root, limit=p.MAX_ARTIFACT):
    return p.decode(p.read_pin(pin, root, limit), limit)


def registry_join(registry, records, root):
    """Recompute subjects and input pins from the registry's exact full records."""
    targets = unique(registry.get("targets"), "id", "registry-rows")
    supplied = {}
    p.require(type(records) is list and len(records) <= MAX_ROWS, "record-count")
    for row in records:
        p.closed(row, "commit path local", "record-fields")
        key = (row["commit"], row["path"])
        p.require(key not in supplied, "record-duplicate")
        supplied[key] = row["local"]
    consumed, inputs, joins = set(), {}, {}
    for target_id, target in targets.items():
        if target.get("status") != "resolved" or target_id.startswith("wildcat"):
            continue
        p.require(type(target.get("full_records")) is dict, "registry-records")
        values = {}
        for kind in ("source_match", "observations"):
            ref = target["full_records"][kind]
            key = (ref["commit"], ref["path"])
            p.require(key in supplied, "record-missing")
            local = supplied[key]
            raw = p.read_pin(local, root, p.MAX_ARTIFACT)
            p.require(local["sha256"] == ref["sha256"] and len(raw) == ref["bytes"], "record-pin")
            values[kind] = p.decode(raw, p.MAX_ARTIFACT)
            consumed.add(key)
        match, observation = values["source_match"], values["observations"]
        sets = unique(match.get("source_sets"), "id", "source-set-identity")
        if target_id == "aave-v3":
            subjects = [{"address": address, "source_set": sid} for sid, record in sets.items()
                        for address in record["reproduction"]["members"]]
            p.require({s["address"].lower() for s in subjects} ==
                      {s["address"].lower() for s in observation["code"]}, "subject-coverage")
        else:
            subjects = [s for s in observation["subjects"] if s["registry_row"] == target_id or
                        (s["registry_row"] == "shared by maple-v2-fixed-term and maple-v2-open-term"
                         and target_id in ("maple-v2-fixed-term", "maple-v2-open-term"))]
        addresses = [s["address"].lower() for s in subjects]
        p.require(len(addresses) == len(set(addresses)) and all(re.fullmatch(r"0x[0-9a-f]{40}", a)
                                                              for a in addresses), "subject-identity")
        subject_pin = target["deployment"]["full_subject_set"]
        subject_digest = p.digest(("\n".join(sorted(addresses)) + "\n").encode())
        p.require(len(addresses) == subject_pin["count"] and subject_digest == subject_pin["sha256"],
                  "subject-pin")
        family = str(Path(target["full_records"]["source_match"]["path"]).parent.name)
        selected, gaps = set(), []
        for subject in subjects:
            sid = subject.get("source_set")
            if sid is None:
                gaps.append(subject)
                continue
            p.require(sid in sets, "subject-source-missing")
            p.require(subject["address"].lower() in
                      {a.lower() for a in sets[sid]["reproduction"]["members"]}, "subject-source-member")
            selected.add(sid)
        for sid in selected:
            record = sets[sid]
            identity = family + "/" + sid
            entry = {"id": identity, "input": record["build_input"],
                     "compiler": record["compiler"], "record_sha256":
                     target["full_records"]["source_match"]["sha256"]}
            p.require(identity not in inputs or inputs[identity] == entry, "input-identity")
            inputs[identity] = entry
        joins[target_id] = {"subjects_sha256": subject_digest, "subjects": len(addresses),
                            "inputs": sorted(family + "/" + sid for sid in selected),
                            "unmatched": gaps, "qualifications": target.get("source_state_gaps", {})}
    p.require(consumed == set(supplied), "record-extra")
    # Every source set in every admitted source-match record must be accounted for.
    for key in consumed:
        document = load(supplied[key], root)
        if "source_sets" in document:
            family = Path(key[1]).parent.name
            p.require({family + "/" + s["id"] for s in document["source_sets"]} <= set(inputs),
                      "source-set-unmapped")
    return targets, inputs, joins


def custody(expected, supplied, root):
    rows = unique(supplied, "id", "input-rows")
    p.require(set(rows) == set(expected), "input-set")
    missing = []
    for identity, entry in expected.items():
        row = rows[identity]
        p.closed(row, "id local", "input-row-fields")
        pin = entry["input"]
        if row["local"] is None:
            missing.append({"id": identity, "sha256": pin["sha256"], "bytes": pin["bytes"]})
            continue
        raw = p.read_pin(row["local"], root)
        p.require(row["local"]["sha256"] == pin["sha256"] and len(raw) == pin["bytes"], "input-pin")
        if pin.get("blob_sha1"):
            import hashlib
            p.require(hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()
                      == pin["blob_sha1"], "input-blob")
    return {"required": len(expected), "verified": len(expected) - len(missing), "missing": missing}


def solidity_module():
    path = Path(__file__).parent / "chunkers/solidity.py"
    spec = importlib.util.spec_from_file_location("lemma_evidence_solidity", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def event_census(document, output, selected):
    """Count declarations from AST owner, source id and spans independently of chunks."""
    rows = []
    for path in selected:
        entry = output["sources"][path]
        source = document["sources"][path]["content"].encode()
        pending = [(n, None) for n in entry["ast"]["nodes"]]
        visits = 0
        while pending:
            node, owner = pending.pop()
            visits += 1
            p.require(visits <= p.MAX_NODES, "census-size")
            if node.get("nodeType") == "ContractDefinition":
                pending.extend((child, node["name"]) for child in node.get("nodes", []))
            elif node.get("nodeType") == "EventDefinition":
                parts = node.get("src", "").split(":")
                p.require(len(parts) == 3 and all(x.isdigit() for x in parts), "census-span")
                start, length, source_id = map(int, parts)
                p.require(source_id == entry["id"] and start + length <= len(source), "census-span")
                rows.append({"path": path, "owner": owner, "name": node["name"], "start": start,
                             "length": length, "declaration_sha256": p.digest(source[start:start+length])})
    return sorted(rows, key=lambda row: (row["path"], row["start"]))


def verify_partition(row, original, expected, root):
    p.closed(row, "id input_id prepared manifest builds census", "partition-fields")
    prepared = p.read_pin(row["prepared"], root)
    manifest = load(row["manifest"], root)
    p.verify_manifest(original, prepared, manifest)
    p.require(manifest["original_sha256"] == expected["input"]["sha256"] and
              manifest["request"]["compiler"]["version"].removesuffix(".Emscripten.clang") ==
              expected["compiler"].removesuffix(".Emscripten.clang"), "partition-input")
    for field in ("runtime", "driver", "artifact"):
        p.read_pin(manifest["request"]["compiler"][field], root, p.MAX_ARTIFACT)
    p.require(type(row["builds"]) is list and len(row["builds"]) == 2, "build-count")
    builds = []
    for build in row["builds"]:
        p.closed(build, "chunks provenance", "build-fields")
        builds.append((p.read_pin(build["chunks"], root, p.MAX_ARTIFACT),
                       p.read_pin(build["provenance"], root)))
    p.require(builds[0] == builds[1], "build-repeat")
    chunks = [p.decode(line) for line in builds[0][0].splitlines()]
    provenance = [p.decode(line) for line in builds[0][1].splitlines()]
    p.require(len(provenance) == 1 and len(chunks) <= p.MAX_NODES, "corpus-shape")
    provenance = provenance[0]
    sol = solidity_module()
    objects = [sol._schema.Chunk(**chunk) for chunk in chunks]
    p.require(not sol._schema.validate(objects) and not sol._schema.validate_provenance(provenance),
              "corpus-schema")
    p.require(provenance["corpus_build_id"] == sol.corpus_build_id(chunks)
              and provenance["chunk_count"] == len(chunks), "corpus-identity")
    p.require(all(c.get("corpus_build_id") == provenance["corpus_build_id"]
                  and c.get("source_ref") == provenance["source_ref"] for c in chunks), "corpus-stamps")
    pins = provenance["inputs"]
    p.require(len(pins) == 1 and pins[0]["sha256"] == p.digest(prepared), "corpus-input")
    present = set(p.decode(prepared)["sources"])
    selected = set(manifest["selected"])
    p.require(set(provenance["selection"]["include"]) == selected and
              set(provenance["selection"]["units_present"]) == present and
              set(provenance["selection"]["units_selected"]) == {c["path"] for c in chunks}
              and {c["path"] for c in chunks} <= selected, "corpus-selection")
    p.require(provenance["source_ref"] == "captured:" + p.digest(original), "corpus-origin")
    compiler = provenance["compiler"]
    p.require(compiler["reported_version"].removesuffix(".Emscripten.clang") ==
              expected["compiler"].removesuffix(".Emscripten.clang"), "corpus-compiler")
    document = p.decode(prepared)
    output = manifest["transcripts"][-1]["output"]
    try:
        sol.validate_event_agreement(output, selected, manifest["request"]["compiler"]["version"])
        derived = sol.chunk_from_output(document, output, sorted(selected),
                                        compiler_version=manifest["request"]["compiler"]["version"])
        derived, _ = sol.dedupe(derived)
        derived.sort(key=lambda chunk: chunk.id)
        sol.compose_embed_text(derived)
    except sol.ChunkError as exc:
        raise p.Refusal("corpus-reconstruction") from exc
    # Rebinding submitted hashes cannot replace reconstruction from source.
    expected_chunks = [chunk.to_dict() for chunk in derived]
    p.require([chunk["id"] for chunk in chunks] == [chunk["id"] for chunk in expected_chunks],
              "corpus-chunk-set")
    for actual, expected_chunk in zip(chunks, expected_chunks):
        p.require({key: value for key, value in actual.items()
                   if key not in ("source_ref", "corpus_build_id")} ==
                  {key: value for key, value in expected_chunk.items()
                   if key not in ("source_ref", "corpus_build_id")}, "corpus-chunk-mismatch")
    census = event_census(document, output, manifest["selected"])
    p.require(load(row["census"], root) == census, "census-mismatch")
    events = [c for c in chunks if c["kind"] == "Event"]
    p.require(len(events) == len(census), "event-count")
    seen = set()
    for event in events:
        detail, path = event["detail"], event["path"]
        span = detail["source_span"]
        matches = [r for r in census if r["path"] == path and r["owner"] == detail["contract"]
                   and r["name"] == detail["name"] and span["start"] <= r["start"]
                   and span["start"] + span["length"] == r["start"] + r["length"]]
        p.require(len(matches) == 1, "event-identity")
        identity = (path, matches[0]["start"])
        p.require(identity not in seen, "event-duplicate")
        seen.add(identity)
        source = document["sources"][path]["content"].encode()
        p.require(event["display_text"].encode() == source[span["start"]:span["start"]+span["length"]],
                  "event-quotation")
    return {"events": len(events), "chunks": len(chunks), "build_id": provenance["corpus_build_id"]}


def _verify_bundle(bundle, root, *, complete=False, full=False):
    p.closed(bundle, "schema registry records inputs rows partitions aggregate", "bundle-fields")
    p.require(bundle["schema"] == "lemma-corpus-evidence/v1", "bundle-schema")
    registry = load(bundle["registry"], root)
    targets, expected, joins = registry_join(registry, bundle["records"], root)
    state = custody(expected, bundle["inputs"], root)
    if complete:
        p.require(not state["missing"], "custody-incomplete")
    rows = unique(bundle["rows"], "id", "coverage-rows")
    resolved = {key for key, row in targets.items() if row["status"] == "resolved"}
    p.require(set(rows) == resolved, "coverage-row-set")
    partitions = unique(bundle["partitions"], "id", "partition-rows")
    input_rows = unique(bundle["inputs"], "id", "input-rows")
    used, results = set(), {}
    for key, row in partitions.items():
        p.require(row.get("input_id") in expected and row["input_id"] not in used, "partition-input-set")
        used.add(row["input_id"])
        pin = input_rows[row["input_id"]]["local"]
        p.require(pin is not None, "partition-custody")
        results[key] = verify_partition(row, p.read_pin(pin, root), expected[row["input_id"]], root)
    assigned = set()
    for key, row in rows.items():
        p.closed(row, "id disposition partitions", "coverage-fields")
        p.require(type(row["partitions"]) is list and len(row["partitions"]) == len(set(row["partitions"])),
                  "coverage-partitions")
        p.require(set(row["partitions"]) <= set(partitions), "coverage-partition-missing")
        if key.startswith("wildcat"):
            p.require(row["disposition"] == "inherited" and not row["partitions"], "coverage-inherited")
        else:
            p.require(row["disposition"] in ("sampled", "complete", "pending"), "coverage-disposition")
            selected = {partitions[x]["input_id"] for x in row["partitions"]}
            p.require(selected <= set(joins[key]["inputs"]), "coverage-source-join")
            if full or row["disposition"] == "complete":
                p.require(selected == set(joins[key]["inputs"]) and row["disposition"] == "complete",
                          "coverage-incomplete")
            assigned.update(row["partitions"])
    p.require(assigned == set(partitions), "partition-unassigned")
    if full:
        p.require(used == set(expected), "partition-set")
    aggregate = {"registry_rows": len(rows), "required_inputs": len(expected),
                 "verified_inputs": state["verified"], "partitions": len(partitions),
                 "events": sum(r["events"] for r in results.values()),
                 "chunks": sum(r["chunks"] for r in results.values())}
    p.require(bundle["aggregate"] == aggregate, "aggregate-mismatch")
    return {"schema": "lemma-corpus-verification/v1", "aggregate": aggregate,
            "custody": state, "partitions": results, "joins": joins,
            "excluded_registry_rows": sorted(set(targets) - resolved),
            "scope": "full" if full else "declared-partitions"}


def verify_bundle(bundle, root, *, complete=False, full=False):
    """Verify a closed evidence bundle, converting malformed joins to refusals."""
    try:
        return _verify_bundle(bundle, root, complete=complete, full=full)
    except (KeyError, IndexError, TypeError, AttributeError, RecursionError) as exc:
        raise p.Refusal("evidence-shape") from exc


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", required=True)
    parser.add_argument("--root", required=True)
    parser.add_argument("--complete", action="store_true")
    parser.add_argument("--full", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = verify_bundle(p.decode(p.read_regular(args.bundle, p.MAX_ARTIFACT), p.MAX_ARTIFACT),
                               args.root, complete=args.complete, full=args.full)
        print(json.dumps({"status": "verified", "aggregate": result["aggregate"],
                          "missing_inputs": len(result["custody"]["missing"])}))
        return 0
    except (p.Refusal, KeyError, TypeError, ValueError, OSError) as exc:
        print(json.dumps({"status": "refused", "category": str(exc) if isinstance(exc, p.Refusal)
                          else "evidence-shape"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
