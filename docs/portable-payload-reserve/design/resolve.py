#!/usr/bin/env python3
"""Design-evidence resolver for Fiat run 1720 (portable payload reserve).

Read-only with respect to the repository and the controller: it imports
scripts/portable_promise_machine.py from --root, builds package bytes in
memory, and writes only closed protasis-design-report/v1 files below
--reports. An existing report with different bytes is refused, never
overwritten. It never touches state.json, the ledger or a receipt.

Modes:
  measure      print the main-branch measurement as JSON (no report written)
  selection    write every selection-stage report for every candidate
  conformance  write one conformance report for one candidate and criterion;
               this needs the `measure` action the runbook's Step 2 builds
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import posixpath
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path, PurePosixPath

REPORT_SCHEMA = "protasis-design-report/v1"
GROWTH_BASE = "0578c19bb812ba34fcfc752dcb81e5df4b1090ae"  # ADR-090 landed here
LOWER_RESERVE = 2 * 1024 * 1024
DELIVERY_ROOM = 794_493  # largest first-parent delivery since GROWTH_BASE
CANDIDATES = (
    "example-payload-class", "second-distribution", "lower-reserve",
    "plugin-budgets",
)
LAZARUS_RETAINED = "plugins/lazarus/examples/aave-v4-spoke-v1-release/"
LINK = re.compile(r"\[[^]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
EXAMPLE = re.compile(r"^plugins/[^/]+/examples/")
EVIDENCE = re.compile(r"^plugins/[^/]+/(examples|docs)/")


def load_generator(root: Path):
    spec = importlib.util.spec_from_file_location(
        "portable_generator_1720", root / "scripts/portable_promise_machine.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(root: Path, *argv: str) -> bytes:
    done = subprocess.run(  # phylax: allow subprocess: fixed local git argv, no shell
        ["git", "-C", str(root), *argv], check=True, capture_output=True)
    return done.stdout


def blob_sizes(root: Path, commit: str) -> dict[str, int]:
    sizes = {}
    for record in git(root, "ls-tree", "-r", "-l", "-z", commit).split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        size = meta.split()[3]
        sizes[path.decode("utf-8")] = int(size) if size != b"-" else 0
    return sizes


def link_targets(path: str, data: bytes, universe: set[str], prefixes: set[str]):
    """Yield (kind, target) for each relative link that resolved in the base."""
    text = data.decode("utf-8", errors="replace")
    for raw in LINK.findall(text):
        link = raw.split("#", 1)[0]
        if not link or "://" in link or link.startswith(("mailto:", "/")):
            continue
        target = posixpath.normpath(posixpath.join(posixpath.dirname(path), link))
        if target in universe:
            yield "file", target
        elif target.rstrip("/") in prefixes:
            yield "dir", target.rstrip("/")


def directory_prefixes(paths) -> set[str]:
    prefixes = set()
    for path in paths:
        parts = path.split("/")
        for end in range(1, len(parts)):
            prefixes.add("/".join(parts[:end]))
    return prefixes


def close_links(kept: set[str], payload: dict[str, bytes]) -> set[str]:
    """Grow `kept` until every Markdown link that resolved before still does.

    Deterministic: file links close to a fixed point first, which is order
    independent; directory links are then settled in sorted order, and the
    two phases repeat until nothing is added.
    """
    universe = set(payload)
    prefixes = directory_prefixes(universe)
    kept = set(kept)
    while True:
        todo = sorted(p for p in kept if p.endswith(".md"))
        while todo:
            path = todo.pop()
            for kind, target in link_targets(path, payload[path], universe, prefixes):
                if kind == "file" and target not in kept:
                    kept.add(target)
                    if target.endswith(".md"):
                        todo.append(target)
        added = False
        for path in sorted(p for p in kept if p.endswith(".md")):
            for kind, target in link_targets(path, payload[path], universe, prefixes):
                if kind != "dir":
                    continue
                inside = sorted(p for p in universe if p.startswith(target + "/"))
                if any(p in kept for p in inside):
                    continue
                documents = [p for p in inside if p.endswith(".md")]
                kept.update(documents or [min(inside, key=lambda p: (len(payload[p]), p))])
                added = True
        if not added:
            return kept


def broken_links(kept: set[str], payload: dict[str, bytes]) -> int:
    universe = set(payload)
    prefixes = directory_prefixes(universe)
    kept = set(kept) | {p for p in universe if p.startswith(".horos/")}
    kept_prefixes = directory_prefixes(kept)
    broken = 0
    for path in sorted(kept):
        if not path.endswith(".md"):
            continue
        for kind, target in link_targets(path, payload[path], universe, prefixes):
            if kind == "file" and target not in kept:
                broken += 1
            if kind == "dir" and target not in kept_prefixes:
                broken += 1
    return broken


def kept_paths(candidate: str, payload: dict[str, bytes], boundary: str) -> set[str]:
    everything = set(payload) - {boundary}
    if candidate in ("lower-reserve", "plugin-budgets"):
        return everything
    if candidate == "example-payload-class":
        start = {
            p for p in everything
            if not EXAMPLE.match(p) or p.endswith(".md") or p.startswith(LAZARUS_RETAINED)
        }
    else:
        start = {p for p in everything if not EVIDENCE.match(p)}
    return close_links(start, payload)


def simulate(gen, root: Path, candidate: str, base: dict) -> dict:
    """Return the capped package's measurement under one candidate rule."""
    payload = base["payload"]
    boundary = gen.PORTABLE_BOUNDARY
    kept = kept_paths(candidate, payload, boundary)
    reduced = {p: payload[p] for p in sorted(kept)}
    if kept == set(payload) - {boundary}:
        reduced[boundary] = payload[boundary]
    else:
        reduced[boundary] = gen._render_portable_boundary(root, reduced)
    manifest = copy.deepcopy(base["manifest"])
    rows = [row for row in manifest["files"] if row["path"] in kept]
    rows.append({
        "bytes": len(reduced[boundary]),
        "generated_by": "plugins/horos/skills/horos/scripts/horos.py",
        "path": boundary, "sha256": hashlib.sha256(reduced[boundary]).hexdigest(),
        "source": None,
    })
    rows.sort(key=lambda row: row["path"])
    runtime_bytes = sum(len(data) for data in reduced.values())
    manifest["files"] = rows
    manifest["file_count"] = len(rows)
    manifest["total_bytes"] = runtime_bytes
    manifest["byte_budget"]["headroom"] = gen.MAX_RUNTIME_BYTES - runtime_bytes
    if kept != set(payload) - {boundary}:
        manifest["omissions"].append({
            "pattern": "plugins/*/examples/**",
            "exceptions": ["**/*.md", LAZARUS_RETAINED + "**"],
            "reason": (
                "demonstration payloads remain in the full source checkout; "
                "their documents, every file a packaged document links and "
                "the one complete Lazarus release stay"
            ),
        })
    manifest_bytes = len((json.dumps(manifest, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    package_bytes = runtime_bytes + manifest_bytes + base["outer_bytes"]
    reserve = LOWER_RESERVE if candidate == "lower-reserve" else gen.MIN_BYTE_HEADROOM
    line = gen.MAX_RUNTIME_BYTES - reserve
    removed = set(payload) - {boundary} - kept
    growth = base["growth"]
    return {
        "candidate": candidate,
        "line": line,
        "reserve_held": gen.MAX_RUNTIME_BYTES - line,
        "package_bytes": package_bytes,
        "package_files": len(reduced) + 1 + base["outer_files"],
        "margin": line - package_bytes,
        "runtime_bytes": runtime_bytes,
        "removed_files": len(removed),
        "removed_bytes": sum(len(payload[p]) for p in removed),
        "growth_reach": sum(growth.get(p, 0) for p in kept),
        "links_broken": broken_links(kept, payload) - base["links_broken"],
        "files_leaving_cli_install": len(removed) if candidate == "example-payload-class" else 0,
        "human_pushed_workflows": 1 if candidate == "second-distribution" else 0,
    }


def baseline(gen, root: Path) -> dict:
    commit = gen.source_commit(root)
    payload, manifest_raw = gen.expected_files(root)
    files, _modes = gen._package_bytes(root, commit)
    prefix = (gen.PACKAGE_ROOT / "runtime").as_posix() + "/"
    outer = {k: v for k, v in files.items() if not k.startswith(prefix)}
    main_sizes = blob_sizes(root, commit)
    old_sizes = blob_sizes(root, GROWTH_BASE)
    growth = {p: main_sizes.get(p, 0) - old_sizes.get(p, 0) for p in payload if p in main_sizes}
    everything = set(payload) - {gen.PORTABLE_BOUNDARY}
    return {
        "commit": commit,
        "payload": payload,
        "manifest": json.loads(manifest_raw),
        "manifest_bytes": len(manifest_raw),
        "outer_bytes": sum(len(v) for v in outer.values()),
        "outer_files": len(outer),
        "package_bytes": sum(len(v) for v in files.values()),
        "package_files": len(files),
        "growth": growth,
        "links_broken": broken_links(everything, payload),
    }


def delivery_growth(root: Path, commit: str, packaged: set[str]) -> list[dict]:
    """Per first-parent commit since GROWTH_BASE, bytes added to packaged paths."""
    log = git(root, "log", "--first-parent", "--format=%H", f"{GROWTH_BASE}..{commit}")
    rows = []
    for name in log.decode("ascii").split():
        after, before = blob_sizes(root, name), blob_sizes(root, name + "^1")
        rows.append({
            "commit": name,
            "bytes": sum(after.get(p, 0) - before.get(p, 0) for p in packaged),
        })
    return sorted(rows, key=lambda row: (-row["bytes"], row["commit"]))


def measure(gen, root: Path, top: int) -> dict:
    base = baseline(gen, root)
    payload = base["payload"]
    deliveries = delivery_growth(root, base["commit"], set(payload) - {gen.PORTABLE_BOUNDARY})
    named = {p.as_posix() for group in (
        gen.ROOT_FILES, gen.OBLIGATION_FIXTURE_FILES, gen.EVALUATION_FIXTURE_FILES,
        gen.SEMANTIC_FIXTURE_FILES, gen.PORTABLE_TEST_FILES) for p in group}
    default = {p: len(d) for p, d in payload.items()
               if p not in named and p != gen.PORTABLE_BOUNDARY}
    line = gen.MAX_RUNTIME_BYTES - gen.MIN_BYTE_HEADROOM
    runtime_bytes = sum(len(d) for d in payload.values())
    return {
        "source_commit": base["commit"],
        "cap": gen.MAX_RUNTIME_BYTES, "reserve": gen.MIN_BYTE_HEADROOM, "line": line,
        "package_bytes": base["package_bytes"], "package_files": base["package_files"],
        "package_margin": line - base["package_bytes"],
        "runtime_bytes": runtime_bytes, "runtime_files": len(payload),
        "runtime_margin": line - runtime_bytes,
        "manifest_bytes": base["manifest_bytes"], "outer_bytes": base["outer_bytes"],
        "omission_classes": len(gen.OMISSIONS),
        "default_included_bytes": sum(default.values()),
        "default_included_files": len(default),
        "growth_since_base": {"base": GROWTH_BASE, "bytes": sum(base["growth"].values())},
        "markdown_links_already_broken": base["links_broken"],
        "first_parent_commits_since_base": len(deliveries),
        "largest_deliveries": deliveries[:5],
        "largest_default_included": [
            {"path": p, "bytes": b}
            for p, b in sorted(default.items(), key=lambda kv: (-kv[1], kv[0]))[:top]],
    }


def write_report(reports: Path, candidate: str, criterion: str, value, unit: str, command: str) -> Path:
    document = {
        "schema": REPORT_SCHEMA, "candidate": candidate, "criterion": criterion,
        "value": value, "unit": unit, "command": command, "exit": 0,
    }
    data = (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")
    reports.mkdir(parents=True, exist_ok=True)
    target = reports / f"{candidate}--{criterion}.json"
    if target.is_symlink():
        raise SystemExit(f"refusing a symlinked report path: {target}")
    if target.exists():
        if target.read_bytes() == data:
            return target
        raise SystemExit(f"refusing to overwrite a different existing report: {target}")
    target.write_bytes(data)
    return target


def selection(gen, root: Path, reports: Path) -> list[dict]:
    base = baseline(gen, root)
    command = "python3 .hexaemeron/design/resolve.py selection --root . --reports .hexaemeron/reports"
    summary = []
    for candidate in CANDIDATES:
        started = time.monotonic_ns()
        result = simulate(gen, root, candidate, base)
        result["wall_ms"] = (time.monotonic_ns() - started) // 1_000_000
        summary.append(result)
        for criterion, value, unit in (
            ("reserve-held", result["reserve_held"], "bytes"),
            ("delivery-room", max(result["margin"], 0), "bytes"),
            ("links-closed", max(result["links_broken"], 0), "count"),
            ("measure-wall-time", result["wall_ms"], "milliseconds"),
            ("margin-after", max(result["margin"], 0), "bytes"),
            ("growth-reach", max(result["growth_reach"], 0), "bytes"),
            ("files-leaving-cli-install", result["files_leaving_cli_install"], "count"),
            ("human-pushed-workflows", result["human_pushed_workflows"], "count"),
        ):
            write_report(reports, candidate, criterion, value, unit, command)
    return summary


def run(argv: list[str], cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(  # phylax: allow subprocess: fixed local python argv, no shell
        argv, cwd=cwd, check=False, capture_output=True, text=True)


def conformance(gen, root: Path, reports: Path, candidate: str, criterion: str) -> Path:
    command = (
        "python3 .hexaemeron/design/resolve.py conformance --root . --reports "
        f".hexaemeron/reports --candidate {candidate} --criterion {criterion}"
    )
    generator = str(root / "scripts/portable_promise_machine.py")
    measured = run([sys.executable, generator, "measure", "--json"], root)
    if measured.returncode != 0:
        raise SystemExit("measure action failed: " + measured.stderr.strip())
    reading = json.loads(measured.stdout)
    with tempfile.TemporaryDirectory(prefix="fiat-1720-conformance.") as raw:
        out = Path(raw).resolve() / "package"
        built = run([sys.executable, generator, "package", "--out", str(out)], root)
        if built.returncode != 0:
            raise SystemExit("package action failed: " + built.stderr.strip())
        walked = [p for p in out.rglob("*") if p.is_file()]
        runtime = out / gen.PACKAGE_ROOT / "runtime"
        manifest = json.loads((runtime / "MANIFEST.json").read_bytes())
        if criterion == "measure-agrees":
            value = (
                reading["package"]["bytes"] == sum(p.stat().st_size for p in walked)
                and reading["package"]["files"] == len(walked)
                and reading["runtime"]["bytes"] == manifest["total_bytes"]
                and reading["runtime"]["files"] == manifest["file_count"]
                and reading["line"] == gen.MAX_RUNTIME_BYTES - gen.MIN_BYTE_HEADROOM
                and reading["package"]["margin"] == reading["line"] - reading["package"]["bytes"]
            )
            return write_report(reports, candidate, criterion, value, "boolean", command)
        if criterion == "room-on-step-tree":
            return write_report(reports, candidate, criterion, max(reading["package"]["margin"], 0), "bytes", command)
        if criterion == "class-leaks":
            payload = {
                p.relative_to(runtime).as_posix(): p.read_bytes()
                for p in runtime.rglob("*") if p.is_file()
            }
            linked = set()
            universe = set(payload)
            prefixes = directory_prefixes(universe)
            for path, data in payload.items():
                if path.endswith(".md"):
                    linked.update(t for k, t in link_targets(path, data, universe, prefixes) if k == "file")
            leaks = [
                p for p in payload
                if EXAMPLE.match(p) and not p.endswith(".md")
                and not p.startswith(LAZARUS_RETAINED) and p not in linked
            ]
            return write_report(reports, candidate, criterion, len(leaks), "count", command)
        if criterion == "installed-gates-pass":
            project = Path(raw).resolve() / "project"
            installed = project / gen.PACKAGE_ROOT
            installed.parent.mkdir(parents=True)
            shutil.copytree(out / gen.PACKAGE_ROOT, installed)
            checks = (
                [sys.executable, str(installed / "scripts/verify_runtime.py")],
                [sys.executable, str(installed / "runtime/plugins/horos/skills/horos/scripts/horos.py"),
                 "check", str(installed / "runtime")],
                [sys.executable, str(installed / "runtime/scripts/promise_machine.py"), "check",
                 "--root", str(installed / "runtime"), "--only", "evaluation", "--json"],
            )
            value = all(run(argv, project).returncode == 0 for argv in checks)
            return write_report(reports, candidate, criterion, value, "boolean", command)
    raise SystemExit(f"unknown conformance criterion: {criterion}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=("measure", "selection", "conformance"))
    parser.add_argument("--root", required=True)
    parser.add_argument("--reports")
    parser.add_argument("--candidate", choices=CANDIDATES)
    parser.add_argument("--criterion")
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    gen = load_generator(root)
    if args.mode == "measure":
        json.dump(measure(gen, root, args.top), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if not args.reports:
        parser.error("--reports is required")
    reports = Path(args.reports).resolve()
    if args.mode == "selection":
        json.dump(selection(gen, root, reports), sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0
    if not args.candidate or not args.criterion:
        parser.error("conformance needs --candidate and --criterion")
    print(conformance(gen, root, reports, args.candidate, args.criterion))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
