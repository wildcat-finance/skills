#!/usr/bin/env python3
"""Build and verify both preserved Wildcat estates and current Compound offline.

External staging remains bound by the two estate manifests. The full path
checks coverage, source identities, subject isolation and component limits.
verify-preserved checks only committed metadata and never claims a rebuild.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, redirect_stderr
from copy import deepcopy
import importlib.util
import io
from pathlib import Path
import shutil
import socket
import sys
import tempfile
from unittest.mock import patch

EXAMPLE = Path(__file__).resolve().parent
PLUGIN = EXAMPLE.parents[1]
REPO = PLUGIN.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))
from alexandria_lib.canonical import MAX_LARGE_NODES, MAX_NODES, canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import MAX_JOURNAL_BYTES, proxy_log_positions  # noqa: E402
from alexandria_lib.paths import read_confined_file  # noqa: E402
from alexandria_lib.release import MAX_RAW_COMPONENT_BYTES, verify as verify_release  # noqa: E402
from alexandria_lib.wildcat_registry import generate_v1_registry, validate_shared_subjects  # noqa: E402
from usdc_interval import Builder, check_interval, main as interval_main  # noqa: E402

FORMAT = "alexandria-wildcat-estates-demo/v1"
EXPECTED = EXAMPLE / "expected.json"
COMPOUND = EXAMPLE.parent / "usdc-interval-live-v0"
COMPOUND_CREATED_AT = "2026-09-07T00:00:00Z"
FIELDS = ("coverage", "source", "scope")


def require(condition, message):
    if not condition:
        raise AlexandriaError(message)


def read(root, relative, *, max_nodes=MAX_NODES):
    """Bound and confine an untrusted build-tree read before decoding it."""
    return load_bytes(read_confined_file(root, relative, relative,
                      max_bytes=MAX_RAW_COMPONENT_BYTES), relative,
                      max_bytes=MAX_RAW_COMPONENT_BYTES, max_nodes=max_nodes)


def estate(version):
    """Load only one of the two repository-owned demonstration programs."""
    require(version in (1, 2), "unknown estate version")
    path = EXAMPLE.parent / f"wildcat-v{version}-interval-v0" / "demo.py"
    spec = importlib.util.spec_from_file_location(f"estates_v{version}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextmanager
def offline():
    """Deny Python socket construction for this in-process demonstration.

    This guard is an observed Python boundary, not operating-system isolation.
    A process never launches a child or a provider from this path.
    """
    with patch.object(socket, "socket", side_effect=AlexandriaError("socket construction refused")), \
         patch.object(socket, "create_connection", side_effect=AlexandriaError("connection refused")):
        yield


def component(release, manifest, name):
    for row in manifest["components"]:
        if row["name"] == name:
            return read(release, row["object_path"], max_nodes=MAX_LARGE_NODES)
    raise AlexandriaError(f"release lacks {name}")


def shape(capture):
    # Capture-plan component becomes component_sha256 after ingest.
    return {"capture": sorted(capture), **{key: sorted(capture[key]) for key in FIELDS}}


def refusal(plan, registry, staging, workspace, label, expected):
    """Run the actual CLI handler; retain its exit and bounded refusal text."""
    plan_path = workspace / (label + "-plan.json")
    registry_path = workspace / (label + "-registry.json")
    plan_path.write_bytes(canonical_bytes(plan))
    registry_path.write_bytes(canonical_bytes(registry))
    output = workspace / (label + "-release")
    stderr = io.StringIO()
    with redirect_stderr(stderr):
        code = interval_main(["build", "--plan", str(plan_path), "--registry", str(registry_path),
                              "--staging", str(staging), "--created-at", COMPOUND_CREATED_AT,
                              "--output", str(output)])
    detail = stderr.getvalue().strip()
    require(code == 1 and expected in detail and not output.exists(),
            f"{label} did not refuse by name before output")
    return {"exit": code, "refusal": detail}


def probes(modules, workspace):
    """Unknown venues, wrong formats, wrong pins and foreign emitters must refuse."""
    plans = [read(module.EXAMPLE, "plan.json") for module in modules]
    registries = [read(module.EXAMPLE, "registry.json") for module in modules]
    unknown = dict(plans[0], venue="unregistered-estate")
    results = {"unregistered-venue": refusal(unknown, registries[0], modules[0].staging_root(),
               workspace, "unknown", "unregistered venue")}
    for index, module in enumerate(modules):
        venue = plans[index]["venue"]
        results[venue + "-wrong-format"] = refusal(plans[index], registries[1-index],
            module.staging_root(), workspace, venue + "-format", "registry format")
        changed = deepcopy(registries[index])
        changed["source"]["equivalence_note"] = "changed pin"
        results[venue + "-wrong-pin"] = refusal(plans[index], changed, module.staging_root(),
            workspace, venue + "-pin", "registry")
        foreign = sorted(set(plans[1-index]["subjects"]) - set(plans[index]["subjects"]))[0]
        try:
            proxy_log_positions([{"address": foreign}], plans[index]["subjects"],
                                plans[index]["interval"], upgrade_topic=None)
        except AlexandriaError as error:
            require("not emitted by a declared subject" in str(error), "wrong emitter refusal")
            results[venue + "-foreign-subject"] = str(error)
        else:
            raise AlexandriaError("foreign subject attributed")
    return results


def observations(built, modules):
    """Recompute assertions from verified releases, never from the saved summary."""
    releases = {"compound-v3": built / "compound-release",
                **{f"wildcat-v{i}": built / f"wildcat-v{i}" / "release" for i in (1, 2)}}
    checked = {}
    manifests = {}
    for venue, release in releases.items():
        verify_release(release)
        checked[venue] = check_interval(release)
        manifests[venue] = read(release, "manifest.json")
        require({row["venue"] for row in manifests[venue]["captures"]} == {venue},
                "capture venue differs from owning release")
    reference = shape(manifests["compound-v3"]["captures"][0])
    for manifest in manifests.values():
        require(all(shape(row) == reference for row in manifest["captures"]), "coverage field mismatch")
    recorded = read(REPO, "docs/kickoff/1374/capture.json")["pattern_release"]["coverage"]
    require(len(recorded) == 9, "Compound pattern must retain nine coverage rows")
    require(all(set(row) == {"component", "status", "record_count", "gaps",
                            "unsupported_collections", "evidence_class", "finality"}
                for row in recorded), "recorded Compound coverage fields changed")
    for row in recorded:
        capture = next(item for item in manifests["compound-v3"]["captures"] if item["id"] == row["component"])
        require(set(capture["coverage"]) == {"collections", "status", "record_count", "gaps", "unsupported_collections"},
                "Compound nested coverage differs from recorded fields")
        require("evidence_class" in capture and "finality" in capture["scope"], "Compound pattern mapping differs")
    registries = [component(releases[f"wildcat-v{i}"], manifests[f"wildcat-v{i}"], "registry") for i in (1, 2)]
    validate_shared_subjects(*registries)
    subject_sets = [{row["address"] for row in registry["entries"]} for registry in registries]
    require([len(value) for value in subject_sets] == [16, 137], "estate subject cardinality differs")
    shared = sorted(subject_sets[0] & subject_sets[1])
    counts = {}
    for index, venue in enumerate(("wildcat-v1", "wildcat-v2")):
        receipt = component(releases[venue], manifests[venue], "epoch-table")
        require(all(row["subject"] in subject_sets[index] for row in receipt["log_attributions"]),
                "attribution names undeclared subject")
        counts[venue] = {address: sum(row["subject"] == address for row in receipt["log_attributions"])
                         for address in shared}
    v1 = registries[0]
    sourced = generate_v1_registry(REPO)
    require(v1 == sourced, "V1 registry differs from pinned source records")
    require(all(row["source_commit"] for row in v1["entries"]), "V1 source identity missing")
    missing = sorted(row["address"] for row in v1["entries"] if row["deployment_block"] is None)
    gaps = next(row["coverage"]["gaps"] for row in manifests["wildcat-v1"]["captures"] if row["id"] == "registry")
    require(len(missing) == 12 and all(any(address in gap and "deployment block" in gap for gap in gaps)
                for address in missing), "V1 deployment gaps missing")
    budgets = {}
    for index, venue in enumerate(("wildcat-v1", "wildcat-v2")):
        module = modules[index]
        staging = module.staging_root()
        binding = module.verify_staging_tree(staging, module._checked_manifest())
        journals = list((staging / "journals").glob("*.jsonl"))
        require(journals, "staging journals missing")
        largest_journal = max(path.stat().st_size for path in journals)
        largest_component = max(row["bytes"] for row in manifests[venue]["components"])
        require(largest_journal <= MAX_JOURNAL_BYTES and largest_component <= MAX_RAW_COMPONENT_BYTES,
                "component or journal exceeds ceiling")
        budgets[venue] = {**binding, "largest_journal_bytes": largest_journal,
                          "largest_component_bytes": largest_component}
    return {"format": FORMAT, "checked": checked, "coverage_fields": reference,
            "compound_pattern_rows": len(recorded), "shared_subjects": shared,
            "shared_log_counts": counts, "v1_source_identities": len(v1["entries"]),
            "v1_missing_deployment_blocks": len(missing),
            "v1_equivalent_commits": v1["source"]["equivalent_commits"], "budgets": budgets}


def build(output):
    """Rebuild all three releases, execute refusals, and save the observed proof."""
    output = output.absolute()
    require(not output.exists() and not output.is_symlink(), "demonstration output already exists")
    modules = [estate(1), estate(2)]
    # Check both external inputs before creating output; missing input is no result.
    for module in modules:
        module.verify_staging_tree(module.staging_root(), module._checked_manifest())
    output.mkdir(parents=True)
    try:
        with offline():
            for index, module in enumerate(modules, 1):
                module.build(output / f"wildcat-v{index}")
                module.verify(output / f"wildcat-v{index}")
            Builder(read(COMPOUND, "plan.json"), COMPOUND / "staging", read(COMPOUND, "registry.json"),
                    created_at=COMPOUND_CREATED_AT).build(output / "compound-release")
            summary = observations(output, modules)
            with tempfile.TemporaryDirectory(prefix="wildcat-estates-probes-") as temporary:
                summary["refusals"] = probes(modules, Path(temporary))
        (output / "summary.json").write_bytes(canonical_bytes(summary))
        return summary
    except BaseException:
        shutil.rmtree(output, ignore_errors=True)
        raise


def verify(built):
    """Recheck releases, both input trees and probes, then compare exact expectations."""
    modules = [estate(1), estate(2)]
    with offline():
        for index, module in enumerate(modules, 1):
            module.verify(built / f"wildcat-v{index}")
        derived = observations(built, modules)
        with tempfile.TemporaryDirectory(prefix="wildcat-estates-probes-") as temporary:
            derived["refusals"] = probes(modules, Path(temporary))
    require(derived == read(built, "summary.json"), "summary differs from recomputed proof")
    require(derived == read(EXAMPLE, "expected.json"), "proof differs from pinned expectation")
    return derived


def verify_preserved():
    """Check both committed metadata sets; no archive read or rebuild occurs."""
    result = {"scope": "committed-metadata-only", "rebuild_performed": False, "estates": {}}
    expected = read(EXAMPLE, "expected.json")
    for index in (1, 2):
        module = estate(index)
        preserved = module.verify_preserved()
        venue = f"wildcat-v{index}"
        checked = preserved["record"]["checked"]
        require(all(checked[field] == expected["checked"][venue][field] for field in module.PRESERVED_COMPARED),
                "preserved metadata differs from whole proof")
        result["estates"][venue] = {"release_id": checked["release_id"], "epochs": checked["epochs"],
                                   "archive_sha256": preserved["manifest"]["archive"]["sha256"]}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("build").add_argument("--output", type=Path, required=True)
    commands.add_parser("verify").add_argument("built", type=Path)
    commands.add_parser("verify-preserved")
    args = parser.parse_args(argv)
    try:
        result = build(args.output) if args.command == "build" else (
            verify(args.built) if args.command == "verify" else verify_preserved())
        sys.stdout.buffer.write(canonical_bytes(result))
        return 0
    except (AlexandriaError, OSError) as error:
        print(f"wildcat-estates-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
