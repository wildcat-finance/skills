#!/usr/bin/env python3
"""Emit bounded evidence for the X-Ray source-reuse fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
from pathlib import Path
import shutil
import sys
import tempfile
import time
from typing import Any, Callable, Mapping


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from lib import xray_reuse as reuse  # noqa: E402


FIXTURE_ROOT = Path(__file__).resolve().parent
PROJECT_FIXTURE = FIXTURE_ROOT / "project"
SCOPE_FIXTURE = FIXTURE_ROOT / "scope.json"
SCHEMA = "hexaemeron.xray.reuse-fixture-proof.v1"
COMMAND = (
    "python3.12 "
    "plugins/hexaemeron/tests/fixtures/xray-reuse/run_demo.py --samples 3"
)


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_fact(variable: str, site: str, delta: str) -> dict[str, str]:
    return {"variable": variable, "site": site, "delta": delta}


def facts(path: str, variant: str = "baseline") -> dict[str, Any]:
    stem = Path(path).stem
    writes = {
        "Base": [write_fact("total", "Base.sol:8", "=next")],
        "Vault": [write_fact("total", "Vault.sol:8", "+amount")],
        "Router": [write_fact("vault", "Router.sol:constructor", "=target")],
    }
    catalog: dict[str, Any] = {
        "access": [f"{stem}.access"],
        "calls": [] if stem == "Base" else [f"{stem}.declared-call"],
        "declarations": [f"{stem}.declaration"],
        "entry_points": [f"{stem}.entry"],
        "fund_flows": [f"{stem}.fund-flow"],
        "guards": [f"{stem}.guard"],
        "imports": [f"{stem}.import"],
        "inheritance": [f"{stem}.inheritance"],
        "invariant_inputs": [f"{stem}.invariant-input"],
        "key_logic": [f"{stem}.key-logic"],
        "roles": [f"{stem}.role"],
        "state_facts": [f"{stem}.state"],
        "transitions": [f"{stem}.transition"],
        "types": [f"{stem}.type"],
        "value_facts": [f"{stem}.value"],
        "writes": writes[stem],
    }
    if variant == "body-v2":
        catalog["key_logic"] = [f"{stem}.key-logic-body-v2"]
    elif variant == "dependency-v2":
        catalog["state_facts"] = [f"{stem}.state-dependency-v2"]
    elif variant == "write-v2":
        catalog["writes"] = [write_fact("total", "Vault.sol:8", "+amount+1")]
    elif variant != "baseline":
        raise ValueError(f"unknown fact variant: {variant}")
    return {key: catalog[key] for key in reuse.FACT_KEYS}


def entry(
    plan: Mapping[str, Any],
    path: str,
    variants: Mapping[str, str],
) -> dict[str, Any]:
    source = next(item for item in plan["sources"] if item["path"] == path)
    return {
        "schema": reuse.ENTRY_SCHEMA,
        "path": path,
        "source_sha256": source["source_sha256"],
        **plan["identity"],
        "dependencies": source["dependencies"],
        "dependency_digests": reuse.dependency_digests_for(path, plan["sources"]),
        "facts": facts(path, variants.get(path, "baseline")),
    }


def write_outputs(candidate: Mapping[str, Any], output_dir: Path) -> None:
    output_dir.mkdir()
    synthesis = candidate["synthesis"]
    compact = json.dumps(synthesis, sort_keys=True, separators=(",", ":"))
    documents = {
        "architecture.json": json.dumps(synthesis, indent=2, sort_keys=True) + "\n",
        "entry-points.md": f"# fixture entry points\n\n```json\n{compact}\n```\n",
        "invariants.md": f"# fixture invariants\n\n```json\n{compact}\n```\n",
        "x-ray.md": f"# fixture x-ray\n\n```json\n{compact}\n```\n",
    }
    for name, body in documents.items():
        (output_dir / name).write_text(body, encoding="utf-8")


def execute(
    project: Path,
    scope: Mapping[str, Any],
    cache: Path,
    run_root: Path,
    label: str,
    variants: Mapping[str, str] | None = None,
    *,
    measure: bool = False,
) -> tuple[dict[str, Any], int | None]:
    variants = variants or {}
    candidate_path = run_root / f"{label}-candidate.json"
    output_dir = run_root / f"{label}-outputs"
    source_read_paths: list[str] = []
    read_source = reuse._read_source

    def observed_read(root: Path, relative: str) -> bytes:
        source_read_paths.append(relative)
        return read_source(root, relative)

    reuse._read_source = observed_read
    started = time.perf_counter_ns() if measure else None
    try:
        plan = reuse.plan(project, scope, cache)
        fresh_extraction_paths = list(plan["dirty"])
        fresh = [entry(plan, path, variants) for path in fresh_extraction_paths]
        candidate = reuse.assemble(
            project,
            scope,
            plan,
            fresh,
            cache_path=cache,
            candidate_path=candidate_path,
        )
    finally:
        reuse._read_source = read_source
    write_outputs(candidate, output_dir)
    manifest = reuse.bind_outputs(candidate_path, output_dir)
    promoted = reuse.promote(candidate_path, output_dir, cache)
    duration = time.perf_counter_ns() - started if started is not None else None
    if promoted["outputs"] != manifest["outputs"]:
        raise RuntimeError("promoted output digests differ from the bound manifest")
    source_paths = [source["path"] for source in plan["sources"]]
    stale_removed = sorted(
        set(plan["removed"]) & set(candidate["synthesis"]["source_inventory"])
    )
    evidence = {
        "plan": {
            key: plan[key]
            for key in (
                "mode",
                "reason",
                "changed",
                "dirty",
                "reusable",
                "removed",
                "reverse_invalidated",
            )
        },
        "source_reads": len(source_read_paths),
        "source_read_paths": source_read_paths,
        "source_digests": {
            source["path"]: source["source_sha256"] for source in plan["sources"]
        },
        "fresh_extractions": len(fresh),
        "fresh_extraction_paths": fresh_extraction_paths,
        "reused_entries": len(plan["reusable"]),
        "source_inventory": candidate["synthesis"]["source_inventory"],
        "stale_removed_rows": stale_removed,
        "fact_union_sha256": reuse.canonical_digest(candidate["synthesis"]),
        "candidate_sha256": manifest["candidate_sha256"],
        "outputs": manifest["outputs"],
        "write_sites": candidate["synthesis"]["write_sites"],
    }
    return evidence, duration


def workspace(root: Path) -> tuple[Path, dict[str, Any], Path]:
    project = root / "project"
    shutil.copytree(PROJECT_FIXTURE, project)
    scope = json.loads(SCOPE_FIXTURE.read_text(encoding="utf-8"))
    return project, scope, root / "cache.json"


def baseline(root: Path) -> tuple[Path, dict[str, Any], Path, dict[str, Any]]:
    project, scope, cache = workspace(root)
    evidence, _duration = execute(project, scope, cache, root, "baseline")
    return project, scope, cache, evidence


def scenario(
    name: str,
    mutate: Callable[[Path, dict[str, Any], Path], Mapping[str, str]],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix=f"xray-reuse-{name}-") as temporary:
        root = Path(temporary)
        project, scope, cache, _initial = baseline(root)
        variants = mutate(project, scope, cache)
        evidence, _duration = execute(
            project,
            scope,
            cache,
            root,
            name,
            variants,
        )
        reference, _reference_duration = execute(
            project,
            scope,
            root / f"{name}-full-cache.json",
            root,
            f"{name}-full-recompute",
            variants,
        )
        return compare_with_full_recompute(evidence, reference)


def compare_with_full_recompute(
    evidence: Mapping[str, Any], reference: Mapping[str, Any]
) -> dict[str, Any]:
    matches = {
        "candidate": evidence["candidate_sha256"] == reference["candidate_sha256"],
        "fact_union": (
            evidence["fact_union_sha256"] == reference["fact_union_sha256"]
        ),
        "outputs": evidence["outputs"] == reference["outputs"],
    }
    if not all(matches.values()):
        failed = ", ".join(key for key, matched in matches.items() if not matched)
        raise RuntimeError(f"reuse result differs from full recomputation: {failed}")
    result = dict(evidence)
    result["full_recompute"] = {
        key: reference[key]
        for key in (
            "plan",
            "source_reads",
            "source_read_paths",
            "fresh_extractions",
            "fresh_extraction_paths",
            "reused_entries",
            "source_inventory",
            "fact_union_sha256",
            "candidate_sha256",
            "outputs",
        )
    }
    result["matches_full_recompute"] = matches
    return result


def independent_full() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="xray-reuse-full-reference-") as temporary:
        root = Path(temporary)
        project, scope, cache = workspace(root)
        evidence, _duration = execute(project, scope, cache, root, "full-reference")
        return evidence


def append_comment(path: Path, text: str) -> None:
    source = path.read_text(encoding="utf-8")
    path.write_text(source + f"\n// {text}\n", encoding="utf-8")


def body_only(
    project: Path, _scope: dict[str, Any], _cache: Path
) -> Mapping[str, str]:
    router = project / "src" / "Router.sol"
    source = router.read_text(encoding="utf-8")
    changed = source.replace("vault.deposit(amount);", "vault.deposit(amount + 1);")
    if changed == source:
        raise RuntimeError("body-only fixture mutation found no route body")
    router.write_text(changed, encoding="utf-8")
    return {"src/Router.sol": "body-v2"}


def dependency_drift(
    project: Path, _scope: dict[str, Any], _cache: Path
) -> Mapping[str, str]:
    append_comment(project / "src" / "Base.sol", "dependency drift")
    return {"src/Base.sol": "dependency-v2"}


def write_site_drift(
    project: Path, _scope: dict[str, Any], _cache: Path
) -> Mapping[str, str]:
    vault = project / "src" / "Vault.sol"
    source = vault.read_text(encoding="utf-8")
    vault.write_text(
        source.replace("total += amount;", "total += amount + 1;"),
        encoding="utf-8",
    )
    return {"src/Vault.sol": "write-v2"}


def source_removal(
    _project: Path, scope: dict[str, Any], _cache: Path
) -> Mapping[str, str]:
    scope["sources"] = [
        source for source in scope["sources"] if source["path"] != "src/Router.sol"
    ]
    return {}


def corrupt_cache(
    _project: Path, _scope: dict[str, Any], cache: Path
) -> Mapping[str, str]:
    cache.write_text("{not-json\n", encoding="utf-8")
    return {}


def measured_pairs(
    samples: int,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    results: list[dict[str, Any]] = []
    first_full: dict[str, Any] | None = None
    first_unchanged: dict[str, Any] | None = None
    for number in range(1, samples + 1):
        with tempfile.TemporaryDirectory(prefix="xray-reuse-timing-") as temporary:
            root = Path(temporary)
            project, scope, cache = workspace(root)
            full, full_ns = execute(
                project, scope, cache, root, f"full-{number}", measure=True
            )
            unchanged, unchanged_ns = execute(
                project, scope, cache, root, f"unchanged-{number}", measure=True
            )
            equivalent = full["outputs"] == unchanged["outputs"]
            if not equivalent:
                raise RuntimeError("unchanged reuse changed a final output digest")
            results.append(
                {
                    "sample": number,
                    "full_wall_time_ns": full_ns,
                    "unchanged_wall_time_ns": unchanged_ns,
                    "outputs_equal": equivalent,
                    "full_outputs": full["outputs"],
                    "unchanged_outputs": unchanged["outputs"],
                }
            )
            if first_full is None:
                first_full = full
                first_unchanged = unchanged
    assert first_full is not None and first_unchanged is not None
    return results, first_full, first_unchanged


def proof(samples: int) -> dict[str, Any]:
    timing_samples, full, unchanged = measured_pairs(samples)
    full_reference = independent_full()
    full = compare_with_full_recompute(full, full_reference)
    unchanged = compare_with_full_recompute(unchanged, full_reference)
    full_times = [sample["full_wall_time_ns"] for sample in timing_samples]
    unchanged_times = [
        sample["unchanged_wall_time_ns"] for sample in timing_samples
    ]
    source_bytes = sum(path.stat().st_size for path in PROJECT_FIXTURE.rglob("*.sol"))
    scenarios = {
        "full": full,
        "unchanged": unchanged,
        "body-only": scenario("body-only", body_only),
        "dependency-drift": scenario("dependency-drift", dependency_drift),
        "write-site-drift": scenario("write-site-drift", write_site_drift),
        "source-removal": scenario("source-removal", source_removal),
        "corrupt-cache": scenario("corrupt-cache", corrupt_cache),
    }
    return {
        "schema": SCHEMA,
        "command": COMMAND,
        "environment": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "python_executable": sys.executable,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "timer": "time.perf_counter_ns",
            "network": False,
            "dependencies": "python-standard-library-only",
            "adapter_sha256": file_sha256(PLUGIN_ROOT / "lib" / "xray_reuse.py"),
            "xray_skill_sha256": file_sha256(
                PLUGIN_ROOT / "skills" / "x-ray" / "SKILL.md"
            ),
            "fixture_source_count": len(list(PROJECT_FIXTURE.rglob("*.sol"))),
            "fixture_source_bytes": source_bytes,
        },
        "limits": {
            "samples_per_mode": samples,
            "max_sources": reuse.MAX_SOURCES,
            "max_source_bytes": reuse.MAX_SOURCE_BYTES,
            "max_total_source_bytes": reuse.MAX_TOTAL_SOURCE_BYTES,
            "max_json_bytes": reuse.MAX_JSON_BYTES,
            "max_output_bytes": reuse.MAX_OUTPUT_BYTES,
            "warmups_discarded": 0,
            "pair_order": "full-then-unchanged",
        },
        "timing": {
            "samples": timing_samples,
            "full_spread_ns": max(full_times) - min(full_times),
            "unchanged_spread_ns": max(unchanged_times) - min(unchanged_times),
        },
        "scenarios": scenarios,
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--samples", type=int, choices=(3,), default=3)
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    print(json.dumps(proof(arguments.samples), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
