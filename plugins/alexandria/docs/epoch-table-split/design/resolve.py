#!/usr/bin/env python3
"""Resolve one selection cell of the issue 1888 design record.

Run from the root of the run worktree:

    python3 .hexaemeron/design/resolve.py <criterion> --candidate <id>

Every value comes from pinned inputs:

- the base commit's `plugins/alexandria` tree, extracted with `git archive`;
- the issue 1872 study blob at its pinned commit, checked by SHA-256 before
  any figure is read from it;
- the issue 1872 step heads, for the shared-site count;
- the two preserved Wildcat releases named by `ALEXANDRIA_WILDCAT_V1_RELEASE`
  and `ALEXANDRIA_WILDCAT_V2_RELEASE`, each verified before use: its canonical
  manifest must hash to the pinned id, and every component object must match
  the size and digest that manifest records;
- the base measurements recorded beside this script in `observations.json`.

It prints one closed `protasis-design-report/v1` object. `--out` also writes
that object to a path that must not exist, and `--evidence` writes the
figures the value came from to another fresh path. The script reads no
controller state, writes nothing else and opens no socket; its only child
processes are fixed `git` reads and the base commit's own `check`. Every git
read goes through `run_git`, which reads no system, global or XDG git
configuration or attributes file and no inherited `GIT_*` variable, and
refuses by name when git cannot start, cannot finish or prints output that is
not UTF-8. The repository's own configuration and `.git/info/attributes`
still apply, so the base tree `git archive` extracts is checked against the
base commit's blob ids before anything runs from it.
"""

from __future__ import annotations

import argparse
import ast
import copy
import functools
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

HERE = Path(__file__).resolve().parent
SCHEMA = "protasis-design-report/v1"
BASE = "17ea8d2ab5e52081370b13b92390b64849ed880d"
PLUGIN = "plugins/alexandria"
AAVE_STUDY = {
    "commit": "3abcb107e22118427e08e8e23b826bc555d9f613",
    "path": "plugins/alexandria/docs/aave-v3-interval/study.md",
    "sha256": "42af8412e8242c99a9e2b40e571e193a5edda611043a41fb1e157deae78e4c60",
}
# Each figure is read only after its literal is found in the pinned blob.
AAVE_FIGURES = {
    "blocks": ("9,731,023 blocks", 9_731_023),
    "logs": ("19,644,502 logs", 19_644_502),
    "log_response_bytes": ("14,296,415,154", 14_296_415_154),
    "trace_filtered_bytes": ("48,097,593,584", 48_097_593_584),
    "densest_logs_per_1000_blocks": ("5,718", 5_718),
    "densest_trace_bytes_per_block": ("13,420 bytes per block", 13_420),
    "second_transport_span": ("29,999", 29_999),
}
AAVE_RANGE_RULE = "three quarters of the 64 MiB ceiling"
# The local Reth node's eth_getLogs answer limit, from the issue 1888 brief;
# it is Reth's default --rpc.max-logs-per-response.
RETH_LOG_CAP = 20_000
PR_STEPS = {
    "1885": ("beb9f18ec889ce41d9489b6c71025cbc63b5b13f",
             "0eea1abc2a0193c91b7de48edebcaa9fd19a645c"),
    "1889": ("0eea1abc2a0193c91b7de48edebcaa9fd19a645c",
             "b479c21b72d58edcf1a2e8f1ca9910fc37ab5a6d"),
}
RELEASES = {
    "ALEXANDRIA_WILDCAT_V1_RELEASE":
        "sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69",
    "ALEXANDRIA_WILDCAT_V2_RELEASE":
        "sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3",
}
CANDIDATES = (
    "split-attribution-parts",
    "compact-attribution-rows",
    "raised-epoch-table-ceiling",
    "plan-sized-releases",
)
PROPOSED_CAP = 16_384
PART_FIELD = "log_attribution_parts"
COMPACT_FIELD = "log_attribution_rows"
TRIGGERS = {
    "split-attribution-parts": PART_FIELD,
    "compact-attribution-rows": COMPACT_FIELD,
    "raised-epoch-table-ceiling": None,
    "plan-sized-releases": None,
}
# The raised-epoch-table-ceiling candidate's own ceiling for that one component.
TABLE_CEILING_BYTES = 8 * 1024 ** 3
TABLE_CEILING_NODES = 200_000_000
COMPONENT_CEILING = 64 * 1024 * 1024
LARGE_NODES = 2_000_000
RANGE_BUDGET = 48 * 1024 * 1024
FIXED_AND_OPENING = 7

# Declared edit sites: (path, symbol). A Python symbol is a module constant,
# function, class or Class.method present at the base commit; "*" is a whole
# file that exists at the base commit; "new" is a file that must not.
_CORE = [
    (f"{PLUGIN}/scripts/alexandria_lib/release.py", "MAX_COMPONENTS"),
    (f"{PLUGIN}/scripts/alexandria_lib/release.py", "MAX_CAPTURES"),
    (f"{PLUGIN}/scripts/alexandria_lib/release.py", "ingest"),
    (f"{PLUGIN}/scripts/alexandria_lib/release.py", "verify"),
    (f"{PLUGIN}/scripts/alexandria_lib/index.py", "_load_release"),
    (f"{PLUGIN}/scripts/alexandria_lib/index.py", "_load_manifest"),
    (f"{PLUGIN}/scripts/alexandria_lib/index.py", "_insert_release"),
    (f"{PLUGIN}/scripts/alexandria_lib/derivation.py", "_read_manifest"),
    (f"{PLUGIN}/scripts/alexandria_lib/derivation.py", "derive"),
    (f"{PLUGIN}/scripts/alexandria_lib/derivation.py", "verify_derivation"),
    (f"{PLUGIN}/scripts/alexandria_lib/compound_phase0.py", "load_phase0"),
    (f"{PLUGIN}/scripts/alexandria_lib/statement.py", "_verified_manifest"),
    (f"{PLUGIN}/scripts/alexandria_lib/interval.py", "Staging"),
    (f"{PLUGIN}/scripts/usdc_interval.py", "Builder.build"),
    (f"{PLUGIN}/scripts/usdc_interval.py", "check_interval"),
    (f"{PLUGIN}/schemas/capture-plan-v1.schema.json", "*"),
    (f"{PLUGIN}/schemas/archive-manifest-v1.schema.json", "*"),
    (f"{PLUGIN}/schemas/address-query-v1.schema.json", "*"),
    (f"{PLUGIN}/schemas/interval-checkpoint-v2.schema.json", "*"),
    (f"{PLUGIN}/schemas/README.md", "*"),
    (f"{PLUGIN}/docs/usdc-interval-collector.md", "*"),
    (f"{PLUGIN}/docs/raw-releases.md", "*"),
]
EDIT_SITES = {
    "split-attribution-parts": _CORE + [
        (f"{PLUGIN}/scripts/alexandria_lib/interval.py", "validate_plan"),
        (f"{PLUGIN}/scripts/usdc_interval.py", "journal_components"),
        (f"{PLUGIN}/scripts/usdc_interval.py", "component_gap"),
        (f"{PLUGIN}/scripts/usdc_interval.py", "Builder._epoch_receipt"),
        (f"{PLUGIN}/scripts/usdc_interval.py", "Builder._capture"),
        (f"{PLUGIN}/scripts/usdc_interval.py", "_role"),
        (f"{PLUGIN}/schemas/interval-plan-v2.schema.json", "*"),
        (f"{PLUGIN}/schemas/interval-receipt-v4.schema.json", "new"),
        (f"{PLUGIN}/schemas/interval-log-attributions-v1.schema.json", "new"),
    ],
    "compact-attribution-rows": _CORE + [
        (f"{PLUGIN}/scripts/alexandria_lib/interval.py", "validate_plan"),
        (f"{PLUGIN}/scripts/alexandria_lib/interval.py", "validate_attributions"),
        (f"{PLUGIN}/scripts/usdc_interval.py", "Builder._epoch_receipt"),
        (f"{PLUGIN}/schemas/interval-plan-v2.schema.json", "*"),
        (f"{PLUGIN}/schemas/interval-receipt-v4.schema.json", "new"),
    ],
    "raised-epoch-table-ceiling": _CORE + [
        (f"{PLUGIN}/scripts/alexandria_lib/release.py", "_validate_coverage_against_bytes"),
        (f"{PLUGIN}/scripts/alexandria_lib/canonical.py", "MAX_LARGE_NODES"),
    ],
    "plan-sized-releases": [],
}


class Refusal(Exception):
    pass


# -- small, owned helpers -------------------------------------------------

def canon(value) -> bytes:
    """Alexandria's canonical JSON form: sorted keys, compact, one newline."""
    return (json.dumps(value, ensure_ascii=False, allow_nan=False,
                       separators=(",", ":"), sort_keys=True) + "\n").encode("utf-8")


def nodes(value) -> int:
    """Count nodes the way `alexandria_lib.canonical._check_tree` does: keys are free."""
    total = 0
    stack = [value]
    while stack:
        current = stack.pop()
        total += 1
        if isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, dict):
            stack.extend(current.values())
    return total


# -- git, isolated from the caller ---------------------------------------

GIT_TIMEOUT = 300
# Command-line configuration outranks every file git reads. The attributes
# file is pinned as well, because git reads its default attributes file even
# when no configuration names one.
GIT_OPTIONS = ("-c", "color.ui=never", "-c", f"core.attributesFile={os.devnull}")
# Flags that keep each command's output plain: no colour, no external diff or
# text conversion, every file compared as text, and git's default hunk shape.
PLAIN_OUTPUT = {
    "diff": ("--no-color", "--no-ext-diff", "--no-textconv", "--text",
             "--diff-algorithm=myers", "--indent-heuristic", "--inter-hunk-context=0"),
    "grep": ("--no-color", "--no-textconv", "--text"),
    "show": ("--no-color", "--no-ext-diff", "--no-textconv"),
}
_GIT_HOME: list = []


def git_environment() -> dict:
    """The caller's environment without its GIT_* variables or user git configuration.

    HOME and XDG_CONFIG_HOME name one empty directory for the whole process,
    so git reads no global, XDG or system configuration or attributes file.
    """
    if not _GIT_HOME:
        _GIT_HOME.append(tempfile.TemporaryDirectory(prefix="fiat-1888-git-home-"))
    home = _GIT_HOME[0].name
    environment = {key: value for key, value in os.environ.items()
                   if not key.startswith("GIT_")}
    environment.update(HOME=home, XDG_CONFIG_HOME=home, GIT_CONFIG_NOSYSTEM="1",
                       GIT_CONFIG_GLOBAL=os.devnull, GIT_ATTR_NOSYSTEM="1")
    return environment


def run_git(directory: Path, argv: tuple, accept: tuple = (0,)):
    """Run one git command in directory. Every git call in this script comes here.

    A git that cannot start, does not finish or exits outside accept is a
    Refusal naming git and the cause, never a traceback or a guessed value.
    """
    command = ["git", *GIT_OPTIONS, "-C", str(directory), argv[0],
               *PLAIN_OUTPUT.get(argv[0], ()), *argv[1:]]
    try:
        result = subprocess.run(  # phylax: allow subprocess: fixed git argv, no shell
            command, capture_output=True, timeout=GIT_TIMEOUT, env=git_environment(),
        )
    except subprocess.TimeoutExpired:
        raise Refusal(f"git {argv[0]} did not finish within {GIT_TIMEOUT} seconds") from None
    except OSError as error:
        raise Refusal(f"git {argv[0]} could not start: {type(error).__name__}: "
                      f"{error.strerror or error}") from None
    if result.returncode not in accept:
        raise Refusal("git " + " ".join(argv[:2]) + " failed: "
                      + result.stderr.decode("utf-8", "replace").strip()[:200])
    return result


def git_text(data: bytes, command: str) -> str:
    """Decode git output as strict UTF-8, or refuse by name."""
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise Refusal(f"git {command} printed output that is not UTF-8, "
                      f"at byte {error.start}") from None


@functools.lru_cache(maxsize=None)
def repository_root() -> Path:
    """Ask git for the worktree that holds this script.

    The script runs from `.hexaemeron/design/` and as its committed copy in
    `plugins/alexandria/docs/epoch-table-split/design/`, so no fixed count of
    parent directories reaches the root from both.
    """
    output = run_git(HERE, ("rev-parse", "--show-toplevel")).stdout
    return Path(git_text(output, "rev-parse").rstrip("\n"))


def git(*argv: str) -> bytes:
    """Run one git command at the repository root and return its raw output."""
    return run_git(repository_root(), argv).stdout


def base_file(path: str) -> str:
    return git_text(git("show", f"{BASE}:{path}"), "show")


@functools.lru_cache(maxsize=None)
def release_root(variable: str) -> Path:
    """The preserved release a variable names, verified once against its pinned id.

    The claimed id alone binds nothing, so an incomplete or edited copy would
    otherwise yield a value: the manifest must be canonical JSON that hashes to
    the pinned id, and every component must be a regular file with the size and
    digest the manifest records.
    """
    value = os.environ.get(variable)
    if not value:
        raise Refusal(f"{variable} is not set; it names a preserved release directory")
    root = Path(value)
    manifest_path = root / "manifest.json"
    if root.is_symlink() or not manifest_path.is_file() or manifest_path.is_symlink():
        raise Refusal(f"{variable} names {root}, which holds no regular manifest.json")
    try:
        raw = manifest_path.read_bytes()
        manifest = json.loads(raw)
        claimed = manifest.get("release_id") if isinstance(manifest, dict) else None
        if claimed != RELEASES[variable]:
            raise Refusal(f"{variable} holds release {claimed}, not {RELEASES[variable]}")
        identity = {key: item for key, item in manifest.items() if key != "release_id"}
        if canon(manifest) != raw or "sha256:" + hashlib.sha256(canon(identity)).hexdigest() != claimed:
            raise Refusal(f"{variable} names a manifest.json whose content does not hash to {claimed}")
        components = [(item["name"], item["object_path"], item["bytes"], item["sha256"])
                      for item in manifest["components"]]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise Refusal(f"{variable} names a manifest.json that is not a readable Alexandria "
                      f"release manifest: {type(error).__name__}") from None
    for name, object_path, size, digest in components:
        path = root / object_path
        try:
            data = path.read_bytes() if path.is_file() and not path.is_symlink() else None
        except OSError as error:
            raise Refusal(f"{variable} component {name} cannot be read: {error.strerror}") from None
        if data is None:
            raise Refusal(f"{variable} component {name} is not a regular file at {object_path}")
        if len(data) != size or "sha256:" + hashlib.sha256(data).hexdigest() != digest:
            raise Refusal(f"{variable} component {name} does not match its size and digest")
    return root


def load_release(root: Path):
    manifest = json.loads((root / "manifest.json").read_bytes())
    components = {item["name"]: item for item in manifest["components"]}
    return manifest, components


def component_bytes(root: Path, item: dict) -> bytes:
    data = (root / item["object_path"]).read_bytes()
    if "sha256:" + hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise Refusal(f"component {item['name']} does not match its digest")
    return data


def observations() -> dict:
    return json.loads((HERE / "observations.json").read_bytes())


def aave_figures() -> dict:
    blob = git("show", f"{AAVE_STUDY['commit']}:{AAVE_STUDY['path']}")
    if hashlib.sha256(blob).hexdigest() != AAVE_STUDY["sha256"]:
        raise Refusal("the pinned issue 1872 study blob does not match its SHA-256")
    text = git_text(blob, "show")
    if AAVE_RANGE_RULE not in text:
        raise Refusal("the pinned issue 1872 study no longer states its range rule")
    figures = {}
    for name, (literal, value) in AAVE_FIGURES.items():
        if literal not in text:
            raise Refusal(f"the pinned issue 1872 study does not state {literal!r}")
        figures[name] = value
    return figures


def integer_expression(node, path: str) -> int:
    """Fold an integer constant written as literals joined by +, -, * or **."""
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -integer_expression(node.operand, path)
    if isinstance(node, ast.BinOp):
        left = integer_expression(node.left, path)
        right = integer_expression(node.right, path)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Pow) and 0 <= right <= 64:
            return left ** right
    raise Refusal(f"{path} declares a limit this script cannot fold")


def base_constants() -> dict:
    """The interval and release limits the base commit declares."""
    wanted = {
        f"{PLUGIN}/scripts/alexandria_lib/interval.py": ("MAX_SHARDS", "MAX_SHARD_WIDTH"),
        f"{PLUGIN}/scripts/alexandria_lib/release.py": ("MAX_COMPONENTS", "MAX_CAPTURES",
                                                         "MAX_RAW_COMPONENT_BYTES"),
        f"{PLUGIN}/scripts/alexandria_lib/canonical.py": ("MAX_CONTROL_BYTES", "MAX_NODES",
                                                           "MAX_LARGE_NODES"),
    }
    found = {}
    for path, names in wanted.items():
        tree = ast.parse(base_file(path))
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1:
                target = node.targets[0]
                if isinstance(target, ast.Name) and target.id in names:
                    found[target.id] = integer_expression(node.value, path)
    missing = {name for names in wanted.values() for name in names} - set(found)
    if missing:
        raise Refusal("the base commit no longer declares " + ", ".join(sorted(missing)))
    return found


# -- measurements from the preserved releases -----------------------------

def v2_measurements() -> dict:
    root = release_root("ALEXANDRIA_WILDCAT_V2_RELEASE")
    manifest, components = load_release(root)
    table_bytes = component_bytes(root, components["epoch-table"])
    table = json.loads(table_bytes)
    rows = table["log_attributions"]
    rest = {key: value for key, value in table.items() if key != "log_attributions"}
    rest_bytes = len(canon(rest))
    rest_nodes = nodes(rest)
    row_nodes = {nodes(row) for row in rows}
    if len(row_nodes) != 1:
        raise Refusal("the V2 attribution rows do not share one node count")
    listed = len(json.dumps(rows, ensure_ascii=False, separators=(",", ":"),
                            sort_keys=True).encode("utf-8"))
    compact = [{key: value for key, value in row.items()
                if key not in ("block_hash", "transaction_hash")} for row in rows]
    compact_listed = len(json.dumps(compact, ensure_ascii=False, separators=(",", ":"),
                                    sort_keys=True).encode("utf-8"))
    ratios = {}
    for cls in ("logs", "traces", "boundary-blocks"):
        journal = response = records = 0
        for name, item in components.items():
            if name.split(".")[0] != cls:
                continue
            document = json.loads(component_bytes(root, item))
            journal += item["bytes"]
            for record in document["records"]:
                response += len(record["response"].encode("utf-8"))
                records += 1
        ratios[cls] = {"journal_bytes": journal, "response_bytes": response, "records": records}
    shards = len(json.loads(component_bytes(root, components["interval-plan"]))["shards"])
    return {
        "release_bytes": sum(item["bytes"] for item in manifest["components"])
        + (root / "manifest.json").stat().st_size,
        "rows": len(rows),
        "table_bytes": len(table_bytes),
        "rest_bytes": rest_bytes,
        "rest_nodes": rest_nodes,
        "row_bytes": (listed - 1) / len(rows),
        "row_nodes": row_nodes.pop(),
        "compact_row_bytes": (compact_listed - 1) / len(rows),
        "compact_row_nodes": nodes(compact[0]),
        "logs_journal_per_response": ratios["logs"]["journal_bytes"] / ratios["logs"]["response_bytes"],
        "traces_journal_per_response": ratios["traces"]["journal_bytes"] / ratios["traces"]["response_bytes"],
        "boundary_journal_bytes_per_shard": ratios["boundary-blocks"]["journal_bytes"] / shards,
        "class_bytes": ratios,
        "shards": shards,
    }


def manifest_cost() -> dict:
    """Bytes and nodes per component with its capture, worst of both preserved releases."""
    costs = {}
    for variable in RELEASES:
        root = release_root(variable)
        raw = (root / "manifest.json").read_bytes()
        manifest = json.loads(raw)
        top = {key: value for key, value in manifest.items()
               if key not in ("components", "captures")}
        count = len(manifest["components"])
        costs[variable] = {
            "components": count,
            "bytes_per_component": (len(raw) - len(canon(top))) / count,
            "nodes_per_component": (nodes(manifest["components"])
                                    + nodes(manifest["captures"])) / count,
        }
    return {
        "per_release": costs,
        "bytes_per_component": max(item["bytes_per_component"] for item in costs.values()),
        "nodes_per_component": max(item["nodes_per_component"] for item in costs.values()),
    }


def aligned_part_ratio() -> dict:
    """Worst ratio of one range's attribution rows to that range's logs journal part.

    Both preserved releases split their journals by plan ranges; each range's
    attribution rows are the rows whose block falls in the range's blocks.
    """
    worst = {}
    for variable in RELEASES:
        root = release_root(variable)
        manifest, components = load_release(root)
        plan = json.loads(component_bytes(root, components["interval-plan"]))
        table = json.loads(component_bytes(root, components["epoch-table"]))
        shards = plan["shards"]
        size = plan["shards_per_component"]
        best = (0.0, None)
        for index, first in enumerate(range(0, len(shards), size)):
            last = min(first + size, len(shards)) - 1
            low, high = shards[first]["start"], shards[last]["end"]
            rows = [row for row in table["log_attributions"]
                    if low <= int(row["block_number"]) <= high]
            item = components.get(f"logs.{index}")
            if item is None or not rows:
                continue
            part = len(canon({"first_shard": first, "format": "specimen", "last_shard": last,
                              "part": index, "rows": rows}))
            ratio = part / item["bytes"]
            if ratio > best[0]:
                best = (ratio, f"logs.{index}")
        worst[variable] = {"ratio": best[0], "component": best[1]}
    return worst


def aave_model(candidate: str) -> dict:
    figures = aave_figures()
    limits = base_constants()
    v2 = v2_measurements()
    cost = manifest_cost()
    run = {item["id"]: item for item in observations()["runs"]}["check-v2"]
    checked_bytes = observations()["inputs"]["ALEXANDRIA_WILDCAT_V2_RELEASE"]
    coefficient = run["maximum_resident_set_bytes"] / (
        checked_bytes["component_bytes"] + checked_bytes["manifest_bytes"])

    blocks, logs = figures["blocks"], figures["logs"]
    density = figures["densest_logs_per_1000_blocks"] / 1000
    trace_rate = figures["densest_trace_bytes_per_block"]
    range_blocks = RANGE_BUDGET / trace_rate
    width = min(math.floor(RETH_LOG_CAP / density), math.floor(range_blocks),
                figures["second_transport_span"], limits["MAX_SHARD_WIDTH"])
    per_component = max(1, math.floor(range_blocks / width))
    shards = math.ceil(blocks / width)
    if shards > limits["MAX_SHARDS"]:
        raise Refusal("the Aave interval needs more shards than MAX_SHARDS at this width")
    ranges = math.ceil(shards / per_component)
    journal_range = round(width * per_component * trace_rate * v2["traces_journal_per_response"])
    journals = round(figures["log_response_bytes"] * v2["logs_journal_per_response"]
                     + figures["trace_filtered_bytes"] * v2["traces_journal_per_response"]
                     + shards * v2["boundary_journal_bytes_per_shard"])
    journal_per_log = journals / logs
    attributions = round(logs * v2["row_bytes"])
    model = {
        "figures": figures, "limits": limits, "v2": v2, "manifest_cost": cost,
        "check_coefficient": coefficient, "shard_width": width,
        "shards_per_component": per_component, "shards": shards, "ranges": ranges,
        "journal_range_bytes": journal_range, "journal_bytes": journals,
        "attribution_bytes": attributions,
    }

    def table_capacity(row_bytes, row_nodes):
        by_bytes = math.floor((COMPONENT_CEILING - v2["rest_bytes"]) / row_bytes)
        by_nodes = math.floor((LARGE_NODES - v2["rest_nodes"]) / row_nodes)
        return min(by_bytes, by_nodes), by_bytes, by_nodes

    if candidate == "split-attribution-parts":
        components = FIXED_AND_OPENING + 4 * ranges
        per_release = math.floor((PROPOSED_CAP - FIXED_AND_OPENING) / 4)
        part = round(width * per_component * density * v2["row_bytes"])
        release_bytes = journals + attributions + v2["rest_bytes"]
        model.update(
            components=components,
            releases=1 if components <= PROPOSED_CAP else math.ceil(ranges / per_release),
            largest_component=max(journal_range, part), densest_part_bytes=part,
            largest_release_bytes=release_bytes, cap=PROPOSED_CAP,
        )
    elif candidate == "raised-epoch-table-ceiling":
        components = FIXED_AND_OPENING + 3 * ranges
        table = attributions + v2["rest_bytes"]
        table_nodes = logs * v2["row_nodes"] + v2["rest_nodes"]
        fits = (components <= PROPOSED_CAP and table <= TABLE_CEILING_BYTES
                and table_nodes <= TABLE_CEILING_NODES)
        model.update(
            components=components, releases=1 if fits else math.ceil(table / TABLE_CEILING_BYTES),
            largest_component=max(journal_range, table), table_bytes=table,
            table_nodes=table_nodes, largest_release_bytes=journals + table, cap=PROPOSED_CAP,
        )
    elif candidate == "compact-attribution-rows":
        rows, by_bytes, by_nodes = table_capacity(v2["compact_row_bytes"], v2["compact_row_nodes"])
        table = round(rows * v2["compact_row_bytes"]) + v2["rest_bytes"]
        model.update(
            rows_per_release=rows, rows_by_bytes=by_bytes, rows_by_nodes=by_nodes,
            releases=math.ceil(logs / rows), largest_component=max(journal_range, table),
            largest_release_bytes=round(rows * journal_per_log) + table, cap=PROPOSED_CAP,
        )
    elif candidate == "plan-sized-releases":
        rows, by_bytes, by_nodes = table_capacity(v2["row_bytes"], v2["row_nodes"])
        table = round(rows * v2["row_bytes"]) + v2["rest_bytes"]
        model.update(
            rows_per_release=rows, rows_by_bytes=by_bytes, rows_by_nodes=by_nodes,
            releases=math.ceil(logs / rows), largest_component=max(journal_range, table),
            largest_release_bytes=round(rows * journal_per_log) + table,
            cap=limits["MAX_COMPONENTS"],
        )
    else:
        raise Refusal(f"unknown candidate {candidate}")
    model["check_peak_bytes"] = round(coefficient * model["largest_release_bytes"])
    model["manifest_bytes_at_cap"] = round(model["cap"] * cost["bytes_per_component"])
    return model


# -- the older verifier ---------------------------------------------------

def extract_base(destination: Path) -> Path:
    data = git("archive", "--format=tar", BASE, PLUGIN)
    try:
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(destination, filter="data")
    except tarfile.TarError as error:
        raise Refusal("git archive of the base commit could not be read: "
                      + str(error).replace("\n", " ")[:200]) from None
    verify_extracted_base(destination)
    return destination / PLUGIN / "scripts"


def verify_extracted_base(destination: Path) -> None:
    """Refuse unless the extracted files are exactly the base commit's blobs.

    git archive still applies the clone's own .git/info/attributes, including
    export-ignore, export-subst and end-of-line rules, and no option turns that
    file off, so every file is checked against the blob id git ls-tree reports.
    """
    expected = {}
    listing = git_text(git("ls-tree", "-r", "-z", BASE, PLUGIN), "ls-tree")
    for entry in filter(None, listing.split("\0")):
        header, _, name = entry.partition("\t")
        mode, kind, oid = header.split(" ")
        if kind != "blob" or mode not in ("100644", "100755"):
            raise Refusal(f"the base commit holds {name} as {kind} {mode}, not a file")
        expected[name] = oid
    found = {path.relative_to(destination).as_posix()
             for path in destination.rglob("*") if path.is_file() or path.is_symlink()}
    missing, extra = sorted(set(expected) - found), sorted(found - set(expected))
    if missing or extra:
        raise Refusal(f"git archive of the base commit left out {len(missing)} and added "
                      f"{len(extra)} file(s), first {(missing + extra)[0]}")
    for name, oid in sorted(expected.items()):
        path = destination / name
        data = b"" if path.is_symlink() else path.read_bytes()
        digest = (hashlib.sha256 if len(oid) == 64 else hashlib.sha1)(
            b"blob %d\0" % len(data) + data).hexdigest()
        if path.is_symlink() or digest != oid:
            raise Refusal(f"git archive of the base commit changed {name}")


def run_base_check(scripts: Path, release: Path) -> dict:
    environment = {"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1",
                   "NO_COLOR": "1", "HOME": os.environ.get("HOME", "")}
    result = subprocess.run(  # phylax: allow subprocess: fixed interpreter and base-commit script argv
        [sys.executable, str(scripts / "usdc_interval.py"), "check", str(release)],
        capture_output=True, timeout=900, env=environment, cwd=str(release.parent),
    )
    stderr = result.stderr.decode("utf-8", "replace")
    stdout = result.stdout.decode("utf-8", "replace")
    semantics = None
    if result.returncode == 0:
        semantics = json.loads(stdout).get("receipt_semantics")
    return {
        "exit": result.returncode,
        "stderr": stderr.strip()[:600],
        "traceback": "Traceback" in stderr,
        "receipt_semantics": semantics,
    }


def build_specimen(kind: str, scripts: Path, source: Path, output: Path) -> str:
    """Build one specimen release with the base commit's own ingest (run in a child)."""
    sys.path.insert(0, str(scripts))
    from alexandria_lib import interval as base_interval  # noqa: E402
    from alexandria_lib import release as base_release  # noqa: E402

    manifest, components = load_release(source)
    captures = {item["id"]: item for item in manifest["captures"]}
    raw = {name: component_bytes(source, item) for name, item in components.items()}
    documents = {}

    def document(name):
        if name not in documents:
            documents[name] = json.loads(raw[name])
        return documents[name]

    extra_captures = {}
    extra_components = {}
    if kind in ("parts", "parts-plan-only", "compact"):
        plan = document("interval-plan")
        plan[COMPACT_FIELD if kind == "compact" else PART_FIELD] = (
            "compact" if kind == "compact" else "journal-ranges")
        document("reconciliation")["plan_sha256"] = base_interval.plan_digest(plan)
    if kind == "parts":
        plan = document("interval-plan")
        table = document("epoch-table")
        rows = table.pop("log_attributions")
        listing = []
        template = captures["epoch-table"]
        for index, (first, last) in enumerate(base_interval.plan_partition(plan)):
            low, high = plan["shards"][first]["start"], plan["shards"][last]["end"]
            chosen = [row for row in rows if low <= int(row["block_number"]) <= high]
            name = f"log-attributions.{index}"
            documents[name] = {"first_shard": first,
                               "format": "alexandria-interval-log-attributions/v1",
                               "last_shard": last, "part": index, "rows": chosen}
            listing.append({"component": name, "first_shard": first,
                            "last_shard": last, "rows": len(chosen)})
            capture = copy.deepcopy(template)
            capture.pop("component_sha256", None)
            capture["id"] = capture["component"] = name
            capture["source"]["reference"] = f"derived offline from the collected interval, {name}"
            capture["coverage"] = {
                "collections": [{"name": "log-attributions", "record_count": len(chosen),
                                 "selector": "/rows"}],
                "gaps": [f"component {index} of the log attributions holds the rows of shards "
                         f"{first} to {last}; the other components hold the interval's other rows"],
                "record_count": len(chosen), "status": "partial", "unsupported_collections": [],
            }
            extra_captures[name] = capture
            extra_components[name] = dict(components["epoch-table"], name=name)
        table["format"] = "alexandria-interval-receipt/v4"
        table["log_attribution_parts"] = listing
    if kind in ("compact", "compact-format-only"):
        table = document("epoch-table")
        table["log_attributions"] = [
            {key: value for key, value in row.items()
             if key not in ("block_hash", "transaction_hash")}
            for row in table["log_attributions"]]
        if kind == "compact":
            table["format"] = "alexandria-interval-receipt/v4"
    if kind == "padded":
        table = document("epoch-table")
        rows = table["log_attributions"]
        repeat = math.ceil((COMPONENT_CEILING + 1) / len(canon(rows))) + 1
        table["log_attributions"] = rows * repeat
        base_release.MAX_RAW_COMPONENT_BYTES = 4 * COMPONENT_CEILING
    if kind == "parts":
        base_release.MAX_COMPONENTS = PROPOSED_CAP
        base_release.MAX_CAPTURES = PROPOSED_CAP

    staging = output / "staging"
    staging.mkdir(parents=True)
    names = sorted(set(components) | set(extra_components))
    plan_components, plan_captures = [], []
    for name in names:
        data = canon(documents[name]) if name in documents else raw[name]
        (staging / f"{name}.json").write_bytes(data)
        item = extra_components.get(name, components.get(name))
        plan_components.append({key: item[key] for key in
                                ("access", "media_type", "redistribution", "role")}
                               | {"name": name, "path": f"{name}.json"})
        capture = copy.deepcopy(extra_captures[name] if name in extra_captures else captures[name])
        capture.pop("component_sha256", None)
        plan_captures.append(capture)
    capture_plan = {"captures": plan_captures, "components": plan_components,
                    "format": "alexandria-capture-plan/v1", "release": manifest["release"]}
    (staging / "capture-plan.json").write_bytes(canon(capture_plan))
    return base_release.ingest(staging / "capture-plan.json", output / "release")


SPECIMENS = {
    "split-attribution-parts": ("parts", "parts-plan-only"),
    "compact-attribution-rows": ("compact", "compact-format-only"),
    "raised-epoch-table-ceiling": ("padded",),
    "plan-sized-releases": (),
}


def older_verifier(candidate: str) -> tuple[bool, dict]:
    source = release_root("ALEXANDRIA_WILDCAT_V1_RELEASE")
    evidence = {"base": BASE, "source_release": RELEASES["ALEXANDRIA_WILDCAT_V1_RELEASE"],
                "specimens": {}}
    with tempfile.TemporaryDirectory(prefix="fiat-1888-older-verifier-") as name:
        work = Path(name)
        scripts = extract_base(work / "base")
        if not SPECIMENS[candidate]:
            observed = run_base_check(scripts, source)
            evidence["specimens"]["todays-format"] = observed
            passed = observed["exit"] == 0 and observed["receipt_semantics"] == "v3-subject-positional"
            return passed, evidence
        passed = True
        for kind in SPECIMENS[candidate]:
            out = work / kind
            out.mkdir()
            child = subprocess.run(  # phylax: allow subprocess: this script's own fixed specimen argv
                [sys.executable, str(Path(__file__).resolve()), "_specimen", kind,
                 str(scripts), str(source), str(out)],
                capture_output=True, timeout=900,
                env={"PATH": os.environ.get("PATH", ""), "PYTHONDONTWRITEBYTECODE": "1",
                     "NO_COLOR": "1", "HOME": os.environ.get("HOME", "")},
            )
            if child.returncode != 0:
                raise Refusal(f"specimen {kind} could not be built: "
                              + child.stderr.decode("utf-8", "replace").strip()[-400:])
            specimen_id = child.stdout.decode("utf-8").strip()
            manifest = json.loads((out / "release" / "manifest.json").read_bytes())
            observed = run_base_check(scripts, out / "release")
            observed.update(release_id=specimen_id, components=len(manifest["components"]))
            evidence["specimens"][kind] = observed
            refused = (observed["exit"] == 1 and not observed["traceback"]
                       and observed["stderr"].startswith("usdc-interval: ")
                       and "\n" not in observed["stderr"])
            passed = passed and refused
        return passed, evidence


# -- source-level measurements --------------------------------------------

def symbol_spans(source: str) -> dict:
    tree = ast.parse(source)
    spans = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            spans[node.name] = (node.lineno, node.end_lineno)
            if isinstance(node, ast.ClassDef):
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        spans[f"{node.name}.{child.name}"] = (child.lineno, child.end_lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    spans[target.id] = (node.lineno, node.end_lineno)
    return spans


def base_paths() -> set:
    listing = git("ls-tree", "-r", "--name-only", BASE, PLUGIN)
    return set(git_text(listing, "ls-tree").split("\n"))


def edit_sites(candidate: str) -> tuple[int, dict]:
    present = base_paths()
    checked = []
    for path, symbol in EDIT_SITES[candidate]:
        if symbol == "new":
            if path in present:
                raise Refusal(f"{path} already exists at the base commit")
        elif path not in present:
            raise Refusal(f"{path} is absent at the base commit")
        elif symbol != "*" and symbol not in symbol_spans(base_file(path)):
            raise Refusal(f"{path} declares no {symbol} at the base commit")
        checked.append([path, symbol])
    if len({tuple(item) for item in checked}) != len(checked):
        raise Refusal(f"{candidate} declares an edit site twice")
    return len(checked), {"sites": checked}


def changed_lines(before: str, after: str, path: str) -> list:
    diff = git_text(git("diff", "-U0", before, after, "--", path), "diff")
    ranges = []
    for match in re.finditer(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", diff, re.M):
        start, count = int(match.group(1)), int(match.group(2) or "1")
        ranges.append((start, start + max(count, 1) - 1))
    return ranges


def shared_sites(candidate: str) -> tuple[int, dict]:
    shared = []
    for path, symbol in EDIT_SITES[candidate]:
        for pr, (before, after) in PR_STEPS.items():
            ranges = changed_lines(before, after, path)
            if not ranges:
                continue
            if not path.endswith(".py") or symbol in ("*", "new"):
                shared.append([path, symbol, pr])
                continue
            spans = symbol_spans(git_text(git("show", f"{after}:{path}"), "show"))
            if symbol not in spans:
                continue
            low, high = spans[symbol]
            if any(start <= high and end >= low for start, end in ranges):
                shared.append([path, symbol, pr])
    sites = {(path, symbol) for path, symbol, _pr in shared}
    return len(sites), {"pull_requests": {pr: list(pair) for pr, pair in PR_STEPS.items()},
                        "shared": shared}


def trigger_absent(candidate: str) -> tuple[bool, dict]:
    trigger = TRIGGERS[candidate]
    plans = sorted(path for path in base_paths()
                   if path.startswith(f"{PLUGIN}/examples/") and path.endswith("/plan.json"))
    evidence = {"trigger": trigger, "committed_plans": plans}
    if trigger is None:
        evidence["reason"] = "the candidate declares no trigger and changes no encoder"
        return True, evidence
    carrying = [path for path in plans if trigger in json.loads(base_file(path))]
    # git grep exits 1 when nothing matches, which is the answer this cell wants.
    search = run_git(repository_root(), ("grep", "-c", "-F", trigger, BASE, "--", PLUGIN),
                     accept=(0, 1))
    mentioned = git_text(search.stdout, "grep").strip()
    evidence.update(plans_carrying_trigger=carrying, base_tree_mentions=mentioned)
    return not carrying and not mentioned, evidence


def plan_bound(candidate: str) -> tuple[bool, dict]:
    source = base_file(f"{PLUGIN}/scripts/usdc_interval.py")
    spans = symbol_spans(source)
    lines = source.split("\n")
    low, high = spans["journal_components"]
    body = "\n".join(lines[low - 1:high])
    evidence = {"journal_components_bounds_attributions": "attribution" in body}
    if candidate == "split-attribution-parts":
        ratios = aligned_part_ratio()
        evidence["worst_part_to_logs_journal_ratio"] = ratios
        return all(item["ratio"] < 1 for item in ratios.values()), evidence
    evidence["reason"] = ("one attribution table whose size is the collected log count; "
                          "the base plan-time refusal counts no attribution bytes")
    return False, evidence


CRITERIA = {
    "fitting-plans-keep-todays-path": ("boolean", lambda c: trigger_absent(c)),
    "older-verifier-refuses-by-name": ("boolean", lambda c: older_verifier(c)),
    "component-ceiling-kept": ("bytes", lambda c: (lambda m: (m["largest_component"], m))(aave_model(c))),
    "aave-interval-in-one-release": ("count", lambda c: (lambda m: (m["releases"], m))(aave_model(c))),
    "attribution-bound-fixed-by-the-plan": ("boolean", lambda c: plan_bound(c)),
    "edit-sites": ("count", lambda c: edit_sites(c)),
    "sites-shared-with-1872": ("count", lambda c: shared_sites(c)),
    "manifest-bytes-at-cap": ("bytes", lambda c: (lambda m: (m["manifest_bytes_at_cap"], m))(aave_model(c))),
    "aave-release-check-peak": ("bytes", lambda c: (lambda m: (m["check_peak_bytes"], m))(aave_model(c))),
}


def write_fresh(path: str, data: bytes) -> None:
    target = Path(path)
    if os.path.lexists(target):
        raise Refusal(f"{target} already exists; reports are never replaced")
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "xb") as handle:
        handle.write(data)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["_specimen"]:
        kind, scripts, source, output = argv[1:5]
        print(build_specimen(kind, Path(scripts), Path(source), Path(output)))
        return 0
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("criterion", choices=sorted(CRITERIA))
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--out")
    parser.add_argument("--evidence")
    args = parser.parse_args(argv)
    unit, measure = CRITERIA[args.criterion]
    try:
        value, evidence = measure(args.candidate)
    except Refusal as error:
        print(f"resolve: {error}", file=sys.stderr)
        return 1
    if unit == "boolean":
        value = bool(value)
    else:
        value = int(value)
    report = {
        "candidate": args.candidate,
        "command": f"python3 .hexaemeron/design/resolve.py {args.criterion} --candidate {args.candidate}",
        "criterion": args.criterion,
        "exit": 0,
        "schema": SCHEMA,
        "unit": unit,
        "value": value,
    }
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    sys.stdout.buffer.write(data)
    try:
        if args.out:
            write_fresh(args.out, data)
        if args.evidence:
            write_fresh(args.evidence, (json.dumps(evidence, indent=2, sort_keys=True,
                                                   default=str) + "\n").encode("utf-8"))
    except (Refusal, OSError) as error:
        print(f"resolve: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
