#!/usr/bin/env python3
"""Resolve one selection cell of the issue 1891 design record.

Run from the root of the run worktree:

    python3 .hexaemeron/design/resolve.py <criterion> --candidate <id> [--out <path>]

Every value comes from pinned inputs:

- the base commit's `alexandria_lib/canonical.py` and `errors.py`, read with
  `git show` and imported from a temporary directory, so the parser measured
  is the base parser whatever the worktree holds later;
- issue 1888's committed design files at the base commit (its study, its
  resolver's Aave figures, its observations and its Aave check-peak report),
  each checked by SHA-256 before a figure is read from it;
- the base commit's release and interval limits, read from source by `ast`;
- the issue 1872 merge base and Step 7 head, for the shared-site count;
- the preserved Wildcat V2 release named by `ALEXANDRIA_WILDCAT_V2_RELEASE`,
  verified before use: its canonical manifest must hash to the pinned id and
  every component object must carry the size and SHA-256 the manifest records;
- the base measurements recorded beside this script in `observations.json`.

It prints one closed `protasis-design-report/v1` object; `--out` also writes
it to a path that must not exist, and `--evidence` writes the figures behind
the value to another fresh path. It reads no controller state, writes nothing
else, opens no socket, and its only child processes are `git ls-tree` and
`git show` reads with the caller's GIT_* variables and user configuration
removed.
"""

from __future__ import annotations

import argparse
import array
import ast
import gc
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tracemalloc

HERE = Path(__file__).resolve().parent
SCHEMA = "protasis-design-report/v1"
BASE = "150943da240837040478a76c3611d150fa04f2b6"
MERGE_BASE_1872 = "d162d0952782f09659370b6a554c9cd4511b8db9"
STEP7_1872 = "5d5ec5e142d83140a0967fe13ad3498df3df2015"
PLUGIN = "plugins/alexandria"
SCRIPTS = f"{PLUGIN}/scripts"
SPLIT = f"{PLUGIN}/docs/epoch-table-split"
PINNED_1888 = {
    "study": (f"{SPLIT}/study.md",
              "7deb74791f9a8b996f4a01f873b997ac01665e0fb81f56d8be567d1b78e172c4"),
    "resolver": (f"{SPLIT}/design/resolve.py",
                 "7fe418e64dadf1150ef1a871ab222af135287ea9fb2a32ff5e20eaf101640577"),
    "observations": (f"{SPLIT}/design/observations.json",
                     "c392e20f81029223bd249014ce808e1620979b455e2ffe40d90cacae1b626f90"),
    "aave_peak": (f"{SPLIT}/design/reports/selection/"
                  "split-attribution-parts-aave-release-check-peak.json",
                  "03e630e12a45aa845496df333ce061831980493ce70431ee56a016b6b17b7176"),
}
# Literals the issue 1888 study must carry before its figures are used.
STUDY_LITERALS = ("19,644,502", "11,139 in all", "about 80.6 GB")
V2_RELEASE_ID = "sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3"
V2_ENV = "ALEXANDRIA_WILDCAT_V2_RELEASE"
LARGE_NODES = 2_000_000
# The one piece of per-log state range-streamed-logs carries between
# components: an 8-byte key per preserved transaction, at most one per log.
TRANSACTION_KEY_BYTES = array.array("Q").itemsize

CANDIDATES = (
    "plan-sized-releases",
    "stream-bytes-hold-logs",
    "compact-log-index",
    "range-streamed-logs",
)
UNITS = {
    "aave-interval-checks-on-host": "bytes",
    "format-limit-release-checks-on-host": "bytes",
    "one-component-at-a-time": "bytes",
    "extra-journal-bytes-read": "bytes",
    "edit-sites": "count",
    "sites-shared-with-1872": "count",
}
CRITERIA = tuple(UNITS)

U = f"{SCRIPTS}/usdc_interval.py"
I = f"{SCRIPTS}/alexandria_lib/interval.py"
W1 = f"{SCRIPTS}/alexandria_lib/venues/wildcat_v1.py"
W2 = f"{SCRIPTS}/alexandria_lib/venues/wildcat_v2.py"
C3 = f"{SCRIPTS}/alexandria_lib/venues/compound_v3.py"
VENUES = f"{SCRIPTS}/alexandria_lib/venues/__init__.py"
COLLECTOR_DOC = f"{PLUGIN}/docs/usdc-interval-collector.md"
# Declared edit sites: (path, symbol). A symbol is a function, class or
# Class.method present at the base commit; "*" is a whole file that exists at
# the base commit; "new" is a file that must not exist there.
_STREAM = [
    (U, "Builder.build"), (U, "Builder._journal"), (U, "_check_interval"),
    (U, "_replay_release_opening"), (U, "_check_attribution_parts"), (U, "_component"),
    (COLLECTOR_DOC, "*"),
]
_OPENING_LOGS = [
    (U, "Builder._epoch_receipt"), (U, "replay_opening"), (U, "staged_log_records"),
    (U, "OpeningPhase.__init__"), (U, "epochs_from_opening"), (U, "_gaps"),
    (I, "proxy_log_positions"), (I, "attribute_logs"), (I, "discover_epochs"),
    (W1, "ImmutableCodeOpening.__init__"), (W1, "ImmutableCodeOpening.epochs"),
    (W1, "evidence_gaps"), (W2, "ImmutableCodeOpening.__init__"),
    (W2, "ImmutableCodeOpening.epochs"), (W2, "market_deploy_report"), (VENUES, "*"),
]
EDIT_SITES = {
    "plan-sized-releases": [],
    "stream-bytes-hold-logs": _STREAM,
    "compact-log-index": _STREAM + _OPENING_LOGS + [
        (f"{SCRIPTS}/alexandria_lib/log_index.py", "new"),
    ],
    "range-streamed-logs": _STREAM + _OPENING_LOGS + [
        (I, "_attribute_into"), (U, "attribution_part_rows"), (C3, "evidence_gaps"),
        (f"{SCRIPTS}/alexandria_lib/log_walk.py", "new"),
    ],
}


class Refusal(Exception):
    pass


def git_environment() -> dict:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.pop("XDG_CONFIG_HOME", None)
    environment.update({
        "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_ATTR_NOSYSTEM": "1", "LC_ALL": "C",
    })
    return environment


_ROOT = None


def repository_root() -> Path:
    """The worktree holding this script; every git read runs from its root."""
    global _ROOT
    if _ROOT is None:
        _ROOT = HERE
        _ROOT = Path(git("rev-parse", "--show-toplevel").decode("utf-8").strip())
    return _ROOT


def git(*argv: str) -> bytes:
    cwd = HERE if _ROOT is None else _ROOT
    try:
        completed = subprocess.run(
            ["git", "-c", "color.ui=false", "-c", "core.autocrlf=false", *argv],
            cwd=cwd, env=git_environment(), capture_output=True, timeout=120, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(f"git {argv[0]} could not run: {error}") from error
    if completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()[:400]
        raise Refusal(f"git {' '.join(argv)[:200]} failed: {detail}")
    return completed.stdout


def show(commit: str, path: str):
    """One file's bytes at a commit, or None when the commit has no such file."""
    repository_root()
    if not git("ls-tree", "--name-only", commit, "--", path).strip():
        return None
    return git("show", "--no-textconv", f"{commit}:{path}")


def pinned(key: str) -> bytes:
    path, digest = PINNED_1888[key]
    data = show(BASE, path)
    if data is None or hashlib.sha256(data).hexdigest() != digest:
        raise Refusal(f"{path} at the base commit does not match its pinned SHA-256")
    return data


def base_parser():
    """The base commit's `load_bytes`, imported from a temporary package."""
    directory = Path(tempfile.mkdtemp(prefix="fiat-1891-base-"))
    try:
        package = directory / "alexandria_lib"
        package.mkdir()
        (package / "__init__.py").write_text("", encoding="utf-8")
        for name in ("canonical.py", "errors.py"):
            data = show(BASE, f"{SCRIPTS}/alexandria_lib/{name}")
            if data is None:
                raise Refusal(f"alexandria_lib/{name} is absent at the base commit")
            (package / name).write_bytes(data)
        sys.path.insert(0, str(directory))
        try:
            canonical = importlib.import_module("alexandria_lib.canonical")
        finally:
            sys.path.remove(str(directory))
    finally:
        shutil.rmtree(directory, ignore_errors=True)
    return canonical.load_bytes


def _fold(node, path):
    if isinstance(node, ast.Constant) and type(node.value) is int:
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Add, ast.Sub, ast.Pow)):
        left, right = _fold(node.left, path), _fold(node.right, path)
        return {ast.Mult: lambda: left * right, ast.Add: lambda: left + right,
                ast.Sub: lambda: left - right, ast.Pow: lambda: left ** right}[type(node.op)]()
    raise Refusal(f"a limit in {path} is not an integer expression")


def base_constants() -> dict:
    wanted = {
        f"{SCRIPTS}/alexandria_lib/release.py":
            ("MAX_COMPONENTS", "MAX_RAW_COMPONENT_BYTES", "MAX_MANIFEST_BYTES"),
        f"{SCRIPTS}/alexandria_lib/interval.py": ("MAX_SHARDS", "MAX_PAGE_LIMIT"),
    }
    values = {}
    for path, names in wanted.items():
        tree = ast.parse(show(BASE, path).decode("utf-8"))
        for node in tree.body:
            if (isinstance(node, ast.Assign) and len(node.targets) == 1
                    and isinstance(node.targets[0], ast.Name) and node.targets[0].id in names):
                values[node.targets[0].id] = _fold(node.value, path)
    missing = [name for names in wanted.values() for name in names if name not in values]
    if missing:
        raise Refusal(f"the base commit declares no {', '.join(missing)}")
    return values


def aave_figures() -> dict:
    """Issue 1888's whole-interval Aave V3 release, from its pinned design files."""
    study = pinned("study").decode("utf-8")
    for literal in STUDY_LITERALS:
        if literal not in study:
            raise Refusal(f"the issue 1888 study does not carry {literal!r}")
    figures = None
    for node in ast.parse(pinned("resolver").decode("utf-8")).body:
        if (isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "AAVE_FIGURES"):
            figures = ast.literal_eval(node.value)
    if figures is None:
        raise Refusal("the issue 1888 resolver carries no AAVE_FIGURES")
    record = json.loads(pinned("observations"))
    run = next(item for item in record["runs"] if item["id"] == "check-v2")
    inputs = record["inputs"]["ALEXANDRIA_WILDCAT_V2_RELEASE"]
    coefficient = run["maximum_resident_set_bytes"] / (
        inputs["component_bytes"] + inputs["manifest_bytes"])
    report = json.loads(pinned("aave_peak"))
    return {
        "logs": figures["logs"][1],
        "log_response_bytes": figures["log_response_bytes"][1],
        # 1888's check-peak projection is its coefficient times this release's bytes.
        "release_bytes": round(report["value"] / coefficient),
        "issue_1888_check_coefficient": coefficient,
        "issue_1888_check_peak": report["value"],
    }


def base_check_factor() -> dict:
    record = json.loads((HERE / "observations.json").read_text(encoding="utf-8"))
    peaks = sorted(run["maximum_resident_set_bytes"] for run in record["runs"]
                   if run["id"].startswith("check-v2-"))
    if len(peaks) != 3:
        raise Refusal("observations.json does not hold three base V2 check runs")
    inputs = record["inputs"]["ALEXANDRIA_WILDCAT_V2_RELEASE"]
    release = inputs["component_bytes"] + inputs["manifest_bytes"]
    return {"median_peak": peaks[1], "release_bytes": release, "factor": peaks[1] / release}


def v2_release() -> Path:
    value = os.environ.get(V2_ENV)
    if not value:
        raise Refusal(f"{V2_ENV} is not set")
    root = Path(value)
    try:
        manifest_bytes = (root / "manifest.json").read_bytes()
        manifest = json.loads(manifest_bytes)
    except (OSError, ValueError) as error:
        raise Refusal(f"{V2_ENV} holds no readable manifest: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("release_id") != V2_RELEASE_ID:
        raise Refusal(f"{V2_ENV} does not hold release {V2_RELEASE_ID}")
    identity = {key: value for key, value in manifest.items() if key != "release_id"}
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8") + b"\n"
    if "sha256:" + hashlib.sha256(canonical).hexdigest() != V2_RELEASE_ID:
        raise Refusal(f"{V2_ENV}'s manifest does not hash to its pinned identity")
    for item in manifest["components"]:
        path = root / item["object_path"]
        if path.is_symlink() or not path.is_file():
            raise Refusal(f"{V2_ENV} component {item['name']} is not a regular file")
        data = path.read_bytes()
        if len(data) != item["bytes"] or "sha256:" + hashlib.sha256(data).hexdigest() != item["sha256"]:
            raise Refusal(f"{V2_ENV} component {item['name']} does not match its manifest")
    return root


def _traced(action):
    gc.collect()
    tracemalloc.start()
    try:
        result = action()
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return result, current, peak


_V2 = None


def v2_measurements() -> dict:
    """Per-unit memory costs on the preserved V2 release, under the base parser."""
    global _V2
    if _V2 is not None:
        return _V2
    load_bytes = base_parser()
    root = v2_release()
    manifest = json.loads((root / "manifest.json").read_bytes())
    by_name = {item["name"]: item for item in manifest["components"]}

    def data(name):
        return (root / by_name[name]["object_path"]).read_bytes()

    def parse(raw, label):
        return load_bytes(raw, label, max_bytes=None, max_nodes=LARGE_NODES)

    logs_names = sorted((name for name in by_name if name.startswith("logs.")),
                        key=lambda name: int(name.split(".")[1]))
    journal = 0
    responses = []
    for name in logs_names:
        raw = data(name)
        journal += len(raw)
        responses.extend(record["response"].encode("utf-8") for record in parse(raw, name)["records"])
    response_bytes = sum(len(item) for item in responses)

    def parse_logs():
        logs = []
        for response in responses:
            logs.extend(parse(response, "logs response")["result"])
        return logs

    logs, parsed, _ = _traced(parse_logs)
    count = len(logs)

    def compact_index():
        blocks, transactions, subjects, index = {}, {}, {}, []
        for log in logs:
            block = int(log["blockNumber"], 16)
            tx = int(log["transactionIndex"], 16)
            block_hash = blocks.setdefault(block, bytes.fromhex(log["blockHash"][2:]))
            tx_hash = transactions.setdefault((block, tx), bytes.fromhex(log["transactionHash"][2:]))
            subject = subjects.setdefault(log["address"], len(subjects))
            topic = sys.intern(log["topics"][0]) if log["topics"] else None
            index.append((block, tx, int(log["logIndex"], 16), subject, block_hash, tx_hash, topic))
        return index, blocks, transactions, subjects

    index, compact, _ = _traced(compact_index)
    distinct_transactions = len(index[2])
    del index, logs

    table = data("epoch-table")
    document = parse(table, "epoch-table")
    rows = len(document["log_attributions"])
    document["log_attributions"] = []
    remainder = json.dumps(document, sort_keys=True, separators=(",", ":"),
                           ensure_ascii=False).encode("utf-8") + b"\n"
    del document
    # A row's cost is the traced size of the parsed table less that of the
    # same table with its row list emptied.
    whole, with_rows, _ = _traced(lambda: parse(table, "epoch-table"))
    del whole
    empty, without_rows, _ = _traced(lambda: parse(remainder, "epoch-table remainder"))
    del empty
    row_total = with_rows - without_rows
    rest = len(remainder)

    # One component's working set: its bytes, its parsed document and one
    # record's parsed response at a time, as a multiple of its bytes. Measured
    # on the largest component of each journal class and on the epoch table.
    largest = {}
    for name, item in by_name.items():
        kind = name.split(".")[0]
        if kind in ("logs", "traces", "boundary-blocks", "epoch-evidence", "epoch-table"):
            if kind not in largest or item["bytes"] > by_name[largest[kind]]["bytes"]:
                largest[kind] = name
    ratios = {}
    for _kind, name in sorted(largest.items()):
        def one_component(name=name):
            raw = data(name)
            document = parse(raw, name)
            for record in document.get("records", []):
                parse(record["response"].encode("utf-8"), "response")
            return len(raw)

        size, _, peak = _traced(one_component)
        ratios[name] = round(peak / size, 2)
    _V2 = {
        "logs": count,
        "distinct_transactions": distinct_transactions,
        "parsed_log_bytes": round(parsed / count),
        "compact_index_bytes_per_log": round(compact / count),
        "rows": rows,
        "row_bytes": round(row_total / rows),
        "row_json_bytes": round((len(table) - rest) / rows, 2),
        "logs_journal_bytes": journal,
        "logs_response_bytes": response_bytes,
        "logs_journal_per_response": round(journal / response_bytes, 4),
        "working_set_ratios": ratios,
        "working_set_ratio": max(ratios.values()),
    }
    return _V2


def working_set(v2: dict, limits: dict) -> dict:
    """What a streaming candidate holds besides its per-log state.

    Eight component ceilings at the worst measured working-set ratio: the
    manifest, counted twice for its 128 MiB limit; the four control components
    kept resident (plan, registry, reconciliation, epoch table); and one
    range's logs component and attribution part. Plus that part's rows as
    derived, at the most rows one part can hold.
    """
    ceiling = limits["MAX_RAW_COMPONENT_BYTES"]
    rows = math.floor(ceiling / v2["row_json_bytes"])
    return {"bytes": round(8 * ceiling * v2["working_set_ratio"] + rows * v2["row_bytes"]),
            "part_rows_at_ceiling": rows}


def per_log_state(candidate: str, v2: dict) -> float:
    if candidate == "stream-bytes-hold-logs":
        # Today's two parsed copies, the traces-request map and the opening
        # replay, and one derived row per log.
        return 2 * v2["parsed_log_bytes"] + v2["row_bytes"]
    if candidate == "compact-log-index":
        return v2["compact_index_bytes_per_log"]
    if candidate == "range-streamed-logs":
        return TRANSACTION_KEY_BYTES
    raise Refusal(f"{candidate} has no per-log model")


def check_peak(candidate: str, release_bytes: int, logs: int, evidence: dict) -> int:
    if candidate == "plan-sized-releases":
        factor = base_check_factor()
        evidence["base_check_factor"] = factor
        return round(factor["factor"] * release_bytes)
    v2 = v2_measurements()
    ws = working_set(v2, base_constants())
    state = per_log_state(candidate, v2)
    evidence.update({"v2": v2, "working_set": ws, "per_log_state": state})
    return round(ws["bytes"] + logs * state)


def symbol_source(source: str, symbol: str):
    nodes = ast.parse(source).body
    found = None
    for part in symbol.split("."):
        found = next((node for node in nodes
                      if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name == part), None)
        if found is None:
            return None
        nodes = found.body
    return ast.get_source_segment(source, found)


def site_text(commit: str, path: str, symbol: str):
    data = show(commit, path)
    if data is None or symbol in ("*", "new"):
        return data
    return symbol_source(data.decode("utf-8"), symbol)


def edit_sites(candidate: str, evidence: dict) -> int:
    checked = []
    for path, symbol in EDIT_SITES[candidate]:
        present = site_text(BASE, path, symbol)
        if symbol == "new" and present is not None:
            raise Refusal(f"{path} already exists at the base commit")
        if symbol != "new" and present is None:
            raise Refusal(f"{path} {symbol} is absent at the base commit")
        checked.append(f"{path}:{symbol}")
    evidence["sites"] = checked
    return len(checked)


# A base symbol that issue 1872's commits carry under its earlier name: #1960
# moved check_interval's body into _check_interval after 1872's merge base.
EARLIER_NAMES = {"_check_interval": "check_interval"}


def shared_sites(candidate: str, evidence: dict) -> int:
    shared, renamed = [], {}
    for path, symbol in EDIT_SITES[candidate]:
        if symbol == "new":
            continue
        name = symbol
        if (symbol in EARLIER_NAMES and site_text(MERGE_BASE_1872, path, symbol) is None
                and site_text(STEP7_1872, path, symbol) is None):
            name = renamed[symbol] = EARLIER_NAMES[symbol]
        if site_text(MERGE_BASE_1872, path, name) != site_text(STEP7_1872, path, name):
            shared.append(f"{path}:{symbol}")
    evidence.update({"shared": shared, "read_under_earlier_name": renamed})
    return len(shared)


# Criteria whose value reads the V2 measurements. They are taken first, before
# any other work in the process, so every cell measures from the same state:
# tracemalloc's figures move by a fraction of a byte per log with the
# allocator state an earlier call leaves, and the values are rounded to whole
# bytes (ratios to hundredths) for the same reason.
MEASURED = {
    "aave-interval-checks-on-host", "format-limit-release-checks-on-host",
    "one-component-at-a-time", "extra-journal-bytes-read",
}


def resolve(criterion: str, candidate: str):
    evidence: dict = {}
    if criterion in MEASURED:
        v2_measurements()
    if criterion == "aave-interval-checks-on-host":
        aave = aave_figures()
        evidence["aave"] = aave
        return check_peak(candidate, aave["release_bytes"], aave["logs"], evidence), evidence
    if criterion == "format-limit-release-checks-on-host":
        limits = base_constants()
        release = (limits["MAX_COMPONENTS"] * limits["MAX_RAW_COMPONENT_BYTES"]
                   + limits["MAX_MANIFEST_BYTES"])
        # One logs read per shard, each a page below the provider limit.
        logs = limits["MAX_SHARDS"] * (limits["MAX_PAGE_LIMIT"] - 1)
        evidence.update({"limits": limits, "release_bytes": release, "logs": logs})
        return check_peak(candidate, release, logs, evidence), evidence
    if criterion == "one-component-at-a-time":
        v2 = v2_measurements()
        evidence["v2"] = v2
        if candidate == "plan-sized-releases":
            # Today's model keeps the whole release, so its state per log is
            # the measured check peak divided by the release's logs.
            factor = base_check_factor()
            evidence["base_check_factor"] = factor
            return math.ceil(factor["median_peak"] / v2["logs"]), evidence
        return math.ceil(per_log_state(candidate, v2)), evidence
    if criterion == "extra-journal-bytes-read":
        # Bytes read beyond today's reads, for issue 1888's whole-interval Aave
        # release. A candidate that does not keep every attribution row reads
        # each part a second time in check: once for its shape, before the
        # journals, and once to compare its rows while its logs range is read.
        # range-streamed-logs' build also reads every staged logs journal
        # twice: once for the opening logs, once to derive each range's rows.
        aave = aave_figures()
        v2 = v2_measurements()
        parts = round(aave["logs"] * v2["row_json_bytes"])
        logs = round(aave["log_response_bytes"] * v2["logs_journal_per_response"])
        extra = {"plan-sized-releases": 0, "stream-bytes-hold-logs": 0,
                 "compact-log-index": parts, "range-streamed-logs": parts + logs}[candidate]
        evidence.update({"aave": aave, "part_bytes": parts, "logs_journal_bytes": logs,
                         "row_json_bytes": v2["row_json_bytes"],
                         "logs_journal_per_response": v2["logs_journal_per_response"]})
        return extra, evidence
    if criterion == "edit-sites":
        return edit_sites(candidate, evidence), evidence
    if criterion == "sites-shared-with-1872":
        return shared_sites(candidate, evidence), evidence
    raise Refusal(f"unknown criterion {criterion}")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("criterion", choices=CRITERIA)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--out")
    parser.add_argument("--evidence")
    args = parser.parse_args(argv)
    if args.out and args.evidence and os.path.abspath(args.out) == os.path.abspath(args.evidence):
        print("resolve: --out and --evidence name the same path", file=sys.stderr)
        return 1
    for target in (args.out, args.evidence):
        if target and os.path.lexists(target):
            print(f"resolve: {target} already exists", file=sys.stderr)
            return 1
    try:
        value, evidence = resolve(args.criterion, args.candidate)
    except Refusal as refusal:
        print(f"resolve: {refusal}", file=sys.stderr)
        return 1
    report = {
        "candidate": args.candidate,
        "command": f"python3 .hexaemeron/design/resolve.py {args.criterion} --candidate {args.candidate}",
        "criterion": args.criterion,
        "exit": 0,
        "schema": SCHEMA,
        "unit": UNITS[args.criterion],
        "value": value,
    }
    text = json.dumps(report, indent=2, sort_keys=True) + "\n"
    try:
        if args.out:
            with open(args.out, "x", encoding="utf-8") as handle:
                handle.write(text)
        if args.evidence:
            with open(args.evidence, "x", encoding="utf-8") as handle:
                handle.write(json.dumps(evidence, indent=1, sort_keys=True, default=str) + "\n")
    except OSError as error:
        print(f"resolve: {error}", file=sys.stderr)
        return 1
    sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
