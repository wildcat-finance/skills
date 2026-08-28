#!/usr/bin/env python3
"""Build and verify the checked-in Alexandria credit-history demonstration."""

from __future__ import annotations

import argparse
from collections import Counter
from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import importlib.util
import io
from pathlib import Path
import shutil
import sys
import tempfile


EXAMPLE_ROOT = Path(__file__).resolve().parent
PLUGIN_ROOT = EXAMPLE_ROOT.parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))

from alexandria_lib import derive, ingest, query_bytes, rebuild, verify  # noqa: E402
from alexandria_lib.canonical import (  # noqa: E402
    MAX_CONTROL_BYTES,
    canonical_bytes,
    load_bytes,
)
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.paths import read_confined_file  # noqa: E402
from alexandria_lib.release import MAX_RAW_COMPONENT_BYTES, sha256, validate_plan  # noqa: E402


PLAN = EXAMPLE_ROOT / "demo-plan.json"
EXPECTED_QUERY = EXAMPLE_ROOT / "expected-query.json"
EXPECTED_PROBITAS = EXAMPLE_ROOT / "expected-probitas.json"
PROBITAS_SCRIPT = REPO_ROOT / "plugins" / "probitas" / "scripts" / "probitas.py"


def build_demo(output: Path, *, check_expected=True, source_paths=None):
    """Build the entire offline path into a new directory."""
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        raise AlexandriaError("demo output must not already exist")
    output.mkdir(parents=True)
    try:
        plan = load_bytes(PLAN.read_bytes(), "demo plan")
        capture_plan = _materialize_inputs(output, plan, source_paths or {})
        plan_path = output / "inputs" / "capture-plan.json"
        plan_path.write_bytes(canonical_bytes(capture_plan))

        raw_release = output / "raw-release"
        derived_release = output / "derived-release"
        database = output / "alexandria.sqlite"
        raw_id = ingest(plan_path, raw_release)
        if verify(raw_release) != raw_id:
            raise AlexandriaError("demo raw release identity changed after ingest")
        derived_id = derive(raw_release, derived_release)
        if verify(derived_release) != derived_id:
            raise AlexandriaError("demo derived release identity changed after derivation")
        logical_digest = rebuild([derived_release], database)

        addresses = plan["query"]["addresses"]
        query_data = query_bytes(database, addresses)
        (output / "query.json").write_bytes(query_data)
        evidence, dossier, gate_lines = _run_probitas(
            database, plan["query"]["entity"], addresses, plan["query"]["run_id"]
        )
        (output / "evidence.json").write_bytes(evidence)
        (output / "dossier.md").write_bytes(dossier)

        summary = _summary(
            output, raw_id, derived_id, logical_digest, query_data,
            evidence, dossier, gate_lines,
        )
        (output / "summary.json").write_bytes(canonical_bytes(summary))
        if check_expected:
            _check_expected(query_data, evidence, dossier, gate_lines)
        return summary
    except Exception:
        shutil.rmtree(output)
        raise


def verify_demo(output: Path, *, check_expected=True):
    """Recheck an existing demo without changing it or reaching the network."""
    output = Path(output).absolute()
    plan = load_bytes(PLAN.read_bytes(), "demo plan")
    _verify_materialized_sources(output, plan)
    raw_id = verify(output / "raw-release")
    derived_id = verify(output / "derived-release")
    query_data = query_bytes(output / "alexandria.sqlite", plan["query"]["addresses"])
    if query_data != (output / "query.json").read_bytes():
        raise AlexandriaError("demo query output does not rebuild byte-for-byte")
    evidence, dossier, gate_lines = _run_probitas(
        output / "alexandria.sqlite", plan["query"]["entity"],
        plan["query"]["addresses"], plan["query"]["run_id"],
    )
    if evidence != (output / "evidence.json").read_bytes():
        raise AlexandriaError("demo Probitas evidence does not rebuild byte-for-byte")
    if dossier != (output / "dossier.md").read_bytes():
        raise AlexandriaError("demo Probitas dossier does not rebuild byte-for-byte")
    if check_expected:
        _check_expected(query_data, evidence, dossier, gate_lines)
    summary = load_bytes((output / "summary.json").read_bytes(), "demo summary")
    if summary["raw_release_id"] != raw_id or summary["derived_release_id"] != derived_id:
        raise AlexandriaError("demo summary release identities do not match")
    logical_digest = load_bytes(query_data, "demo query")["index"]["logical_digest"]
    rebuilt = _summary(
        output, raw_id, derived_id, logical_digest,
        query_data, evidence, dossier, gate_lines,
    )
    if summary != rebuilt:
        raise AlexandriaError("demo summary does not rebuild")
    return summary


def _materialize_inputs(output, plan, source_paths):
    if plan.get("format") != "alexandria-demo-plan/v1":
        raise AlexandriaError("demo plan format is unknown")
    capture_plan = _capture_plan(plan)
    validate_plan(capture_plan)
    inputs = output / "inputs"
    inputs.mkdir()
    for declared in plan["components"]:
        item = deepcopy(declared)
        repository_path = item["repository_path"]
        expected = item["source_sha256"]
        override = source_paths.get(item["name"])
        data = (
            Path(override).absolute().read_bytes()
            if override is not None
            else read_confined_file(
                REPO_ROOT, repository_path, f"demo source {item['name']}",
                max_bytes=MAX_RAW_COMPONENT_BYTES,
            )
        )
        if sha256(data) != expected:
            raise AlexandriaError(f"demo source {item['name']} digest does not match its pin")
        destination = inputs / item["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
    return capture_plan


def _capture_plan(plan):
    components = []
    for declared in plan["components"]:
        item = deepcopy(declared)
        item.pop("repository_path")
        item.pop("source_sha256")
        components.append(item)
    return {
        "captures": deepcopy(plan["captures"]),
        "components": components,
        "format": "alexandria-capture-plan/v1",
        "release": deepcopy(plan["release"]),
    }


def _verify_materialized_sources(output, plan):
    validate_plan(_capture_plan(plan))
    inputs = output / "inputs"
    for item in plan["components"]:
        data = read_confined_file(
            inputs, item["path"], f"demo source {item['name']}",
            max_bytes=MAX_RAW_COMPONENT_BYTES,
        )
        if sha256(data) != item["source_sha256"]:
            raise AlexandriaError(f"demo source {item['name']} no longer matches its pin")
    plan_bytes = read_confined_file(
        inputs, "capture-plan.json", "materialized capture plan",
        max_bytes=MAX_CONTROL_BYTES,
    )
    if plan_bytes != canonical_bytes(_capture_plan(plan)):
        raise AlexandriaError("materialized capture plan does not match demo-plan.json")


def _run_probitas(database, entity, addresses, run_id):
    module = _load_probitas()
    collect = [
        "collect", "--entity", entity, "--alexandria-index", str(database),
        "--run-id", run_id, "--out", "-",
    ]
    for address in addresses:
        collect.extend(("--address", address))
    evidence_text, collect_error, code = _invoke(module, collect)
    if code != 0:
        raise AlexandriaError(f"demo Probitas collect failed: {collect_error.strip()}")

    with tempfile.TemporaryDirectory(prefix="alexandria-demo-probitas-") as temporary:
        temporary_evidence = Path(temporary) / "evidence.json"
        temporary_dossier = Path(temporary) / "dossier.md"
        temporary_evidence.write_text(evidence_text, encoding="utf-8")
        dossier_text, render_error, code = _invoke(
            module, ["render", str(temporary_evidence), "--out", "-"]
        )
        if code != 0:
            raise AlexandriaError(f"demo Probitas render failed: {render_error.strip()}")
        temporary_dossier.write_text(dossier_text, encoding="utf-8")
        gate_text, verify_error, code = _invoke(
            module, ["verify", str(temporary_dossier), str(temporary_evidence)]
        )
        if code != 0:
            raise AlexandriaError(
                f"demo Probitas verification failed: {gate_text.strip()} {verify_error.strip()}"
            )
    return evidence_text.encode(), dossier_text.encode(), gate_text.strip().splitlines()


def _load_probitas():
    name = "alexandria_demo_probitas"
    specification = importlib.util.spec_from_file_location(name, PROBITAS_SCRIPT)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _invoke(module, arguments):
    stdout = io.StringIO()
    stderr = io.StringIO()
    with redirect_stdout(stdout), redirect_stderr(stderr):
        code = module.main(arguments)
    return stdout.getvalue(), stderr.getvalue(), code


def _summary(output, raw_id, derived_id, logical_digest, query_data,
             evidence, dossier, gate_lines):
    query_value = load_bytes(query_data, "demo query")
    evidence_value = load_bytes(evidence, "demo Probitas evidence")
    events = Counter(item["row"]["venue"] for item in query_value["events"])
    observations = Counter(item["row"]["venue"] for item in query_value["observations"])
    coverage = {item["venue"]: item["status"] for item in query_value["coverage"]}
    return {
        "artifacts": {
            "dossier_sha256": sha256(dossier),
            "evidence_sha256": sha256(evidence),
            "query_sha256": sha256(query_data),
        },
        "derived_release_id": derived_id,
        "format": "alexandria-credit-history-demo/v1",
        "index_logical_digest": logical_digest,
        "probitas": {
            "coverage": dict(sorted(Counter(
                item["status"] for item in evidence_value["coverage"]
            ).items())),
            "gate_lines": gate_lines,
            "records": len(evidence_value["records"]),
        },
        "query": {
            "coverage": dict(sorted(coverage.items())),
            "events": dict(sorted(events.items())),
            "observations": dict(sorted(observations.items())),
        },
        "raw_release_id": raw_id,
        "release_truth": _truth_digests(output),
    }


def _truth_digests(output):
    result = {}
    for directory in ("raw-release", "derived-release"):
        root = output / directory
        result[directory] = {
            str(path.relative_to(root)): sha256(path.read_bytes())
            for path in sorted(root.rglob("*")) if path.is_file()
        }
    return result


def _check_expected(query_data, evidence, dossier, gate_lines):
    actual_query = _query_receipt(load_bytes(query_data, "demo query"), query_data)
    expected_query = load_bytes(EXPECTED_QUERY.read_bytes(), "expected query")
    if actual_query != expected_query:
        raise AlexandriaError("demo query does not match expected-query.json")
    actual_probitas = _probitas_receipt(
        load_bytes(evidence, "demo evidence"), evidence, dossier, gate_lines
    )
    expected_probitas = load_bytes(EXPECTED_PROBITAS.read_bytes(), "expected Probitas output")
    if actual_probitas != expected_probitas:
        raise AlexandriaError("demo output does not match expected-probitas.json")


def _query_receipt(value, data):
    return {
        "coverage": [
            {
                "chain": item["chain"], "empty_allowed": item["empty_allowed"],
                "records": item["records"], "status": item["status"], "venue": item["venue"],
            }
            for item in value["coverage"]
        ],
        "event_ids": [item["row_id"] for item in value["events"]],
        "format": "alexandria-demo-query-receipt/v1",
        "observation_ids": [item["row_id"] for item in value["observations"]],
        "query_sha256": sha256(data),
        "request": value["request"],
    }


def _probitas_receipt(value, evidence, dossier, gate_lines):
    return {
        "coverage": dict(sorted(Counter(item["status"] for item in value["coverage"]).items())),
        "dossier_sha256": sha256(dossier),
        "evidence_sha256": sha256(evidence),
        "format": "alexandria-demo-probitas-receipt/v1",
        "gate_lines": gate_lines,
        "record_sources": dict(sorted(Counter(item["source_kind"] for item in value["records"]).items())),
        "record_venues": dict(sorted(Counter(item["venue"] for item in value["records"]).items())),
        "records": len(value["records"]),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build and check the offline demonstration")
    build.add_argument("--output", required=True, type=Path)
    verify_parser = commands.add_parser("verify", help="verify an existing demonstration")
    verify_parser.add_argument("output", type=Path)
    args = parser.parse_args(argv)
    try:
        summary = build_demo(args.output) if args.command == "build" else verify_demo(args.output)
        print(summary["derived_release_id"])
        return 0
    except (AlexandriaError, OSError, ValueError) as error:
        print(f"alexandria-demo: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
