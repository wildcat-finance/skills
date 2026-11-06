#!/usr/bin/env python3
"""Resolve one selection cell of the issue 1892 design record.

Run from the root of the run worktree, whose Alexandria, Ariadne, Lazarus and
Probitas trees must still equal the base commit:

    python3 .hexaemeron/design/resolve.py <criterion> --candidate <id>

Each candidate is prototyped here, in memory, from the base commit's own
`statement_for` projection and canonical encoder, so a value measures the
candidate's design rather than a promise about code nobody has written yet.
Ariadne runs from the base tree too: in process for the two correctness gates,
and as one `ariadne.py verify` child process per emitted file for the time
metric, which is what a stranger checking the statement pays.

Two synthetic releases stand in for a release at #1888's cap. Both hold 16,384
components and 16,384 captures and share one tiny object, as
`tests/test_release_limits.py` builds them. `light` keeps that module's one
short gap per capture; `heavy` carries seven 941-character gaps per capture so
each component costs at least the 7,402 statement bytes the densest measured
Aave V3 segment costs. Both are written as real releases and pass the base
`verify` before any candidate sees them.

The pinned cell also reads the two preserved Wildcat releases named by
`ALEXANDRIA_WILDCAT_V1_RELEASE` and `ALEXANDRIA_WILDCAT_V2_RELEASE`, builds four
demonstrations into a temporary directory, and ingests the statement test
fixture. Each release must verify to the identifier pinned below, and its
statement must hash to the digest the base `alexandria.py statement` wrote.

The script prints one closed `protasis-design-report/v1` object. `--out`
writes the same bytes to a path that must not exist, and `--evidence` writes
the figures behind the value to another fresh path. It reads no controller
state, writes nothing else outside an operating-system temporary directory it
removes, and opens no socket.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
from unittest import mock

SCHEMA = "protasis-design-report/v1"
BASE = "150943da240837040478a76c3611d150fa04f2b6"
TREES = ("plugins/alexandria", "plugins/ariadne", "plugins/lazarus", "plugins/probitas")
ROOT = Path.cwd()
ALEXANDRIA = ROOT / "plugins/alexandria"
ARIADNE_SCRIPT = ROOT / "plugins/ariadne/scripts/ariadne.py"

CANDIDATES = (
    "statement-parts",
    "per-component-statements",
    "raised-limit-matched-reader",
    "compact-projection",
)
UNITS = {
    "cap-release-verifies": "boolean",
    "default-reader-verifies": "boolean",
    "pinned-statements-stay-single": "boolean",
    "set-verify-milliseconds": "milliseconds",
    "statement-set-bytes": "bytes",
}

STATEMENT_LIMIT = 8 * 1024 * 1024            # Ariadne's default input bound
KEY_BUDGET = 262_144                         # Ariadne's aggregate key-scan budget
PART_LIMIT = 6 * 1024 * 1024 - 64 * 1024     # 6,225,920: leaves DSSE headroom
RAISED_LIMIT = 128 * 1024 * 1024             # MAX_MANIFEST_BYTES
RAISED_BUDGET = RAISED_LIMIT // 16           # 8,388,608 key characters
COMPONENTS = 16_384
HEAVY_GAPS = 7
HEAVY_GAP_CHARACTERS = 941
SYNTHETIC_AT = "2026-09-24T00:00:00Z"
PART_TYPE = "https://ariadne.wildcat.finance/alexandria-release-part/v1"
INDEX_TYPE = "https://ariadne.wildcat.finance/alexandria-release-parts/v1"
COMPACT_TYPE = "https://ariadne.wildcat.finance/alexandria-release/v2"

# Label -> (release identifier, SHA-256 of the statement the base
# `alexandria.py statement` wrote for it on 2026-09-30).
PINNED = {
    "fixture": ("sha256:e86550e59baba75258093ed4b67c144d1dd520c68f0411d23ba59af050f3fed6",
                "041c699bdefc8be359c88d738a8c5b45002e044b6226534d52bace7c09796c43"),
    "credit-history-raw": ("sha256:6117658c59c96e9ca32594ffe09e994d478dc7d9f2d3799c64bb25050c7fe0e2",
                           "d4846fd64852e5a8e34615679a252a7729976d1278b3be1ec177e1bc2da92fd2"),
    "credit-history-derived": ("sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec",
                               "3b12aa332fcf45cff14fb9a7d1c5f379852d3858c6cf56dcea57c26fc78523e6"),
    "usdc-interval-v0": ("sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa",
                         "c92e6cbb3b953acc3ad11e456cf5ca4715b5b2e8dbc98872a15e0c7c455716cf"),
    "usdc-interval-live-v0": ("sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32",
                              "64df112deab0c91fe3da1aef1196a3a9226adee0cebc977468b3a609b4bc921f"),
    "usdc-interval-epochs-synthetic": ("sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036",
                                       "656e225fbd67321230f58ff943a9dea3fc6ac265af8dc88beacbae2ba8b81bdd"),
    "usdc-interval-epochs-live": ("sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a",
                                  "76334510a1434645e0f249f4015c0c5d0065c17d0eea5f9814a7c9d12cc53527"),
    "compound-v3-phase0": ("sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab",
                           "4ebe969c40dbe77eacbe8848e530454596ecbb8ba9a07b3e6c49b11b41ca7a93"),
    "proof-backed-state": ("sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f",
                           "faaff30f38025379781f35a7289af80cb0e15c9c0ff9c3efd0b9c09f1c77efa5"),
    "wildcat-v1": ("sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69",
                   "679277a2a3367d16a4cb462a12c805c6580291bbaaf7c3a6aa5b4d4e177c00ca"),
    "wildcat-v2": ("sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3",
                   "c891c9d510da6cf02136b082766792d520823beb98b79781c4f8cbcbaec7feae"),
}
DEMOS = {
    "credit-history-v0": {"raw-release": "credit-history-raw",
                          "derived-release": "credit-history-derived"},
    "usdc-interval-v0": {"release": "usdc-interval-v0"},
    "usdc-interval-live-v0": {"release": "usdc-interval-live-v0"},
    "usdc-interval-epochs-v0": {"synthetic-release": "usdc-interval-epochs-synthetic",
                                "live-release": "usdc-interval-epochs-live"},
}
WILDCAT = {"wildcat-v1": "ALEXANDRIA_WILDCAT_V1_RELEASE",
           "wildcat-v2": "ALEXANDRIA_WILDCAT_V2_RELEASE"}


class Refusal(Exception):
    pass


def child_environment() -> dict:
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1"}


def git(*args: str) -> str:
    environment = dict(child_environment(), GIT_CONFIG_NOSYSTEM="1",
                       GIT_CONFIG_GLOBAL=os.devnull)
    result = subprocess.run(  # phylax: allow subprocess: fixed git argv, no shell
        ["git", *args], cwd=ROOT, capture_output=True, env=environment, timeout=120,
    )
    if result.returncode != 0:
        raise Refusal("git " + " ".join(args[:2]) + " failed: "
                      + result.stderr.decode("utf-8", "replace").strip()[:200])
    return result.stdout.decode("utf-8")


def require_base_trees() -> None:
    changed = git("diff", "--name-only", BASE, "--", *TREES).strip()
    untracked = git("ls-files", "--others", "--exclude-standard", "--", *TREES).strip()
    if changed or untracked:
        raise Refusal("the worktree's measured trees differ from " + BASE
                      + "; measure a snapshot of the base instead")


def load_modules() -> dict:
    sys.path.insert(0, str(ALEXANDRIA / "scripts"))
    sys.path.insert(0, str(ARIADNE_SCRIPT.parent))
    from alexandria_lib import release, statement  # noqa: E402
    from alexandria_lib.canonical import canonical_bytes  # noqa: E402
    import ariadne  # noqa: E402
    from ariadne_lib import core_predicate, envelope  # noqa: E402
    return {"release": release, "statement": statement, "encode": canonical_bytes,
            "ariadne": ariadne, "core": core_predicate, "envelope": envelope}


def encode(m, value) -> bytes:
    return m["encode"](value, max_nodes=10 ** 9)


def size(m, value) -> int:
    """Bytes one value adds inside a canonical document: its encoding without the newline."""
    return len(encode(m, value)) - 1


def key_characters(value) -> int:
    """Characters in every object key below `value`, as Ariadne's gates 4 and 7 count them."""
    total = 0
    stack = [value]
    while stack:
        current = stack.pop()
        if isinstance(current, dict):
            total += sum(len(key) for key in current)
            stack.extend(current.values())
        elif isinstance(current, list):
            stack.extend(current)
    return total


def statement_keys(statement) -> int:
    """Ariadne scans the predicate and each subject's digest object, not subject names."""
    subjects = sum(key_characters(subject["digest"]) for subject in statement["subject"])
    return key_characters(statement["predicate"]) + subjects


# ---------------------------------------------------------------- fixtures

def synthetic_manifest(m, gaps):
    release = m["release"]
    data = b"{}\n"
    digest = release.sha256(data)
    path = f"objects/sha256/{digest[7:9]}/{digest[7:]}"
    names = [f"c{index:05d}" for index in range(COMPONENTS)]
    unsigned = {
        "captures": [
            {
                "chain": "eip155:1", "component": names[index], "component_sha256": digest,
                "coverage": {"collections": [], "gaps": list(gaps), "record_count": 0,
                             "status": "partial", "unsupported_collections": []},
                "evidence_class": "archive-log", "id": f"x{index:05d}",
                "scope": {"deployment": "d", "finality": "unknown",
                          "interval": {"kind": "snapshot", "observed_at": SYNTHETIC_AT},
                          "kind": "full-dataset"},
                "source": {"kind": "local", "locator_class": "local-fixture",
                           "reference": "synthetic"},
                "venue": "v",
            }
            for index in range(COMPONENTS)
        ],
        "components": [
            {"access": "public", "bytes": len(data), "media_type": "application/json",
             "name": name, "object_path": path, "redistribution": "permitted",
             "role": "raw", "sha256": digest}
            for name in names
        ],
        "format": release.MANIFEST_FORMAT,
        "release": {"created_at": SYNTHETIC_AT, "name": "limits"},
    }
    identity = release.sha256(m["encode"](unsigned, max_nodes=release.MAX_MANIFEST_NODES))
    return dict(unsigned, release_id=identity), path, data


def write_release(m, root: Path, gaps):
    manifest, path, data = synthetic_manifest(m, gaps)
    root.mkdir()
    (root / path).parent.mkdir(parents=True)
    (root / path).write_bytes(data)
    (root / "manifest.json").write_bytes(
        m["encode"](manifest, max_nodes=m["release"].MAX_MANIFEST_NODES))
    if m["release"].verify(root) != manifest["release_id"]:
        raise Refusal("a synthetic release did not verify to its own identifier")
    return manifest


def fixtures(m, scratch: Path) -> dict:
    heavy_gaps = [f"g{k}" + "x" * (HEAVY_GAP_CHARACTERS - 2) for k in range(HEAVY_GAPS)]
    return {
        "light": write_release(m, scratch / "light", ["synthetic"]),
        "heavy": write_release(m, scratch / "heavy", heavy_gaps),
    }


# ---------------------------------------------------------------- candidates

def grouped_captures(predicate) -> dict:
    by_component: dict = {}
    for capture in predicate["captures"]:
        by_component.setdefault(capture["component"], []).append(capture)
    return by_component


def split_statement(m, single, groups):
    """Part statements over `groups` of component indices, then one index binding them."""
    release_subject = single["subject"][0]
    predicate = single["predicate"]
    by_component = grouped_captures(predicate)
    order = {capture["id"]: position for position, capture in enumerate(predicate["captures"])}
    parts = []
    for number, group in enumerate(groups):
        components = [predicate["components"][index] for index in group]
        captures = sorted((capture for component in components
                           for capture in by_component.get(component["name"], [])),
                          key=lambda capture: order[capture["id"]])
        part = {
            "_type": single["_type"],
            "subject": [release_subject] + [single["subject"][index + 1] for index in group],
            "predicateType": PART_TYPE,
            "predicate": {
                "release": predicate["release"],
                "part": {"index": number, "first_component": group[0],
                         "components": len(group), "captures": len(captures)},
                "components": components,
                "captures": captures,
                "claims": predicate["claims"],
                "commands": [],
            },
        }
        parts.append((f"part-{number:05d}.json", part))
    encoded = [(name, encode(m, part)) for name, part in parts]
    index = {
        "_type": single["_type"],
        "subject": [release_subject] + [
            {"name": f"part/{name}", "digest": {"sha256": hashlib.sha256(body).hexdigest()}}
            for name, body in encoded
        ],
        "predicateType": INDEX_TYPE,
        "predicate": {
            "release": predicate["release"],
            "parts": {"count": len(encoded), "components": len(predicate["components"]),
                      "captures": len(predicate["captures"])},
            "claims": predicate["claims"],
            "commands": [],
        },
    }
    return [("index.json", encode(m, index))] + encoded


def pack(m, single):
    """Greedy groups in manifest order; every part stays within PART_LIMIT and KEY_BUDGET.

    The running size is an upper bound on the exact encoding: the frame's four
    part numbers use five digits, the widest a 16,384-component release needs,
    and every added value is charged a separating comma.
    """
    predicate = single["predicate"]
    by_component = grouped_captures(predicate)
    frame = {
        "_type": single["_type"], "subject": [single["subject"][0]], "predicateType": PART_TYPE,
        "predicate": {"release": predicate["release"],
                      "part": {"index": 99_999, "first_component": 99_999,
                               "components": 99_999, "captures": 99_999},
                      "components": [], "captures": [], "claims": predicate["claims"],
                      "commands": []},
    }
    frame_bytes, frame_keys = len(encode(m, frame)), statement_keys(frame)
    groups, group, used, keys = [], [], frame_bytes, frame_keys
    for index, component in enumerate(predicate["components"]):
        subject = single["subject"][index + 1]
        captures = by_component.get(component["name"], [])
        cost = sum(size(m, value) + 1 for value in (subject, component, *captures))
        cost_keys = (key_characters(subject["digest"]) + key_characters(component)
                     + sum(key_characters(capture) for capture in captures))
        if frame_bytes + cost > PART_LIMIT or frame_keys + cost_keys > KEY_BUDGET:
            return None
        if group and (used + cost > PART_LIMIT or keys + cost_keys > KEY_BUDGET):
            groups.append(group)
            group, used, keys = [], frame_bytes, frame_keys
        group.append(index)
        used += cost
        keys += cost_keys
    if group:
        groups.append(group)
    return groups


def compact_statement(m, single) -> bytes:
    predicate = single["predicate"]
    compact = dict(single, predicateType=COMPACT_TYPE, predicate={
        "release": predicate["release"],
        "components": [[c["name"], c["object_path"], c["media_type"], c["bytes"],
                        c["digest"]["sha256"]] for c in predicate["components"]],
        "captures": [[c["id"], c["component"], c["component_digest"]["sha256"], c["venue"],
                      c["chain"], c["evidence_class"], c["scope"], c["coverage"]]
                     for c in predicate["captures"]],
        "claims": predicate["claims"],
        "commands": [],
    })
    return encode(m, compact)


def within_default_bounds(data: bytes, limit: int) -> bool:
    return len(data) <= limit and statement_keys(json.loads(data)) <= KEY_BUDGET


def emit(m, candidate, manifest, *, unbounded=False):
    """The candidate's statement form as (name, bytes) pairs, or None when it refuses.

    `unbounded` returns what the candidate's encoding produces even past its own
    limit, so a comparative metric can still be measured for it.
    """
    single = m["statement"].statement_for(manifest)
    body = encode(m, single)
    if candidate in ("statement-parts", "per-component-statements"):
        if within_default_bounds(body, STATEMENT_LIMIT):
            return [("statement.json", body)]
        if candidate == "per-component-statements":
            groups = [[index] for index in range(len(single["predicate"]["components"]))]
        else:
            groups = pack(m, single)
            if groups is None:
                return None
        files = split_statement(m, single, groups)
        if not unbounded and not all(within_default_bounds(data, PART_LIMIT) for _, data in files):
            return None
        return files
    if candidate == "raised-limit-matched-reader":
        return [("statement.json", body)] if unbounded or len(body) <= RAISED_LIMIT else None
    if len(body) <= STATEMENT_LIMIT:
        return [("statement.json", body)]
    compact = compact_statement(m, single)
    return [("statement.json", compact)] if unbounded or len(compact) <= STATEMENT_LIMIT else None


# ---------------------------------------------------------------- readers

def reader_arguments(candidate):
    """The flags and key budget the candidate's own reader runs with."""
    if candidate == "raised-limit-matched-reader":
        return ["--max-bytes", str(RAISED_LIMIT)], RAISED_BUDGET
    return [], None


def verify_in_process(m, path: Path, arguments, budget) -> int:
    stream = io.StringIO()
    with contextlib.ExitStack() as stack:
        stack.enter_context(contextlib.redirect_stdout(stream))
        stack.enter_context(contextlib.redirect_stderr(stream))
        if budget is not None:
            stack.enter_context(mock.patch.object(
                m["core"], "MAX_STRUCTURED_KEY_CHARACTERS_TOTAL", budget))
        return m["ariadne"].main(["verify", str(path), *arguments])


def complete(m, manifest, files) -> bool:
    """Each component and capture appears once, in order, with its own part; the index binds each part."""
    expected = m["statement"].statement_for(manifest)
    if len(files) == 1:
        return files[0][1] == encode(m, expected)
    index = json.loads(files[0][1])
    parts = [json.loads(data) for _, data in files[1:]]
    if [s["digest"]["sha256"] for s in index["subject"][1:]] != [
            hashlib.sha256(data).hexdigest() for _, data in files[1:]]:
        return False
    for part in parts:
        names = {component["name"] for component in part["predicate"]["components"]}
        if any(capture["component"] not in names for capture in part["predicate"]["captures"]):
            return False
    order = {capture["id"]: position
             for position, capture in enumerate(expected["predicate"]["captures"])}
    components = [c for part in parts for c in part["predicate"]["components"]]
    captures = sorted((c for part in parts for c in part["predicate"]["captures"]),
                      key=lambda capture: order.get(capture["id"], -1))
    subjects = [s for part in parts for s in part["subject"][1:]]
    return (components == expected["predicate"]["components"]
            and captures == expected["predicate"]["captures"]
            and subjects == expected["subject"][1:]
            and all(part["subject"][0] == expected["subject"][0] for part in parts)
            and index["subject"][0] == expected["subject"][0]
            and index["predicate"]["parts"]["count"] == len(parts))


def write_files(directory: Path, files):
    directory.mkdir()
    paths = []
    for name, data in files:
        path = directory / name
        path.write_bytes(data)
        paths.append(path)
    return paths


# ---------------------------------------------------------------- criteria

def cap_release_verifies(m, candidate, scratch, evidence):
    arguments, budget = reader_arguments(candidate)
    passed = True
    for label, manifest in fixtures(m, scratch).items():
        files = emit(m, candidate, manifest)
        if files is None:
            evidence[label] = {"emitted": False}
            passed = False
            continue
        paths = write_files(scratch / f"{label}-form", files)
        exits = [verify_in_process(m, path, arguments, budget) for path in paths]
        whole = complete(m, manifest, files)
        evidence[label] = {"emitted": True, "files": len(files),
                           "nonzero_exits": sum(1 for code in exits if code),
                           "complete": whole, "largest_file": max(len(d) for _, d in files),
                           "total_bytes": sum(len(d) for _, d in files)}
        passed = passed and whole and not any(exits)
    return passed


def default_reader_verifies(m, candidate, scratch, evidence):
    passed = True
    for label, manifest in fixtures(m, scratch).items():
        files = emit(m, candidate, manifest)
        if files is None:
            evidence[label] = {"emitted": False}
            passed = False
            continue
        bare = write_files(scratch / f"{label}-bare", files)
        wrapped = write_files(scratch / f"{label}-dsse", [
            (name, m["envelope"].Envelope(data).to_json().encode("utf-8")) for name, data in files])
        bare_exits = [verify_in_process(m, path, [], None) for path in bare]
        wrapped_exits = [verify_in_process(m, path, [], None) for path in wrapped]
        evidence[label] = {
            "files": len(files), "bare_nonzero": sum(1 for code in bare_exits if code),
            "dsse_nonzero": sum(1 for code in wrapped_exits if code),
            "largest_bare": max(path.stat().st_size for path in bare),
            "largest_dsse": max(path.stat().st_size for path in wrapped),
            "largest_keys": max(statement_keys(json.loads(d)) for _, d in files),
        }
        passed = passed and not any(bare_exits) and not any(wrapped_exits)
    return passed


def pinned_releases(m, scratch: Path) -> dict:
    releases = {}
    for demo, outputs in DEMOS.items():
        output = scratch / demo
        result = subprocess.run(  # phylax: allow subprocess: fixed interpreter and repository demo argv
            [sys.executable, str(ALEXANDRIA / "examples" / demo / "demo.py"), "build",
             "--output", str(output)], cwd=ROOT, capture_output=True, env=child_environment(),
            timeout=900,
        )
        if result.returncode != 0:
            raise Refusal(f"{demo} did not build at the base")
        for directory, label in outputs.items():
            releases[label] = output / directory
    inputs = scratch / "fixture-inputs"
    shutil.copytree(ALEXANDRIA / "tests" / "fixtures", inputs)
    m["release"].ingest(inputs / "capture-plan.json", scratch / "fixture-release")
    releases["fixture"] = scratch / "fixture-release"
    releases["compound-v3-phase0"] = ALEXANDRIA / "examples/compound-v3-phase0-v0/release"
    releases["proof-backed-state"] = ALEXANDRIA / "examples/proof-backed-state-v0/release"
    for label, variable in WILDCAT.items():
        if not os.environ.get(variable):
            raise Refusal(f"{variable} is not set; it names the preserved release")
        releases[label] = Path(os.environ[variable])
    return releases


def pinned_statements_stay_single(m, candidate, scratch, evidence):
    passed = True
    for label, root in sorted(pinned_releases(m, scratch).items()):
        release_id, statement_digest = PINNED[label]
        if m["release"].verify(root) != release_id:
            raise Refusal(f"{label} does not verify to its pinned identifier")
        manifest = json.loads((root / "manifest.json").read_bytes())
        files = emit(m, candidate, manifest)
        single = m["statement"].statement_for(manifest)
        observed = (hashlib.sha256(files[0][1]).hexdigest()
                    if files is not None and len(files) == 1 else None)
        evidence[label] = {"components": len(manifest["components"]),
                           "statement_bytes": len(encode(m, single)),
                           "key_characters": statement_keys(single),
                           "matches": observed == statement_digest}
        passed = passed and observed == statement_digest
    return passed


def statement_set_bytes(m, candidate, scratch, evidence):
    manifest = fixtures(m, scratch)["heavy"]
    files = emit(m, candidate, manifest, unbounded=True)
    total = sum(len(data) for _, data in files)
    evidence.update(files=len(files), bytes_per_component=total / COMPONENTS,
                    single_statement_bytes=len(encode(m, m["statement"].statement_for(manifest))))
    return total


def set_verify_milliseconds(m, candidate, scratch, evidence):
    manifest = fixtures(m, scratch)["heavy"]
    files = emit(m, candidate, manifest, unbounded=True)
    paths = write_files(scratch / "timed", files)
    arguments, budget = reader_arguments(candidate)
    if candidate == "compact-projection":
        # Read it at all; its gates still run under the default key budget.
        arguments = ["--max-bytes", str(RAISED_LIMIT)]
    prefix = [sys.executable, str(ARIADNE_SCRIPT)]
    if budget is not None:
        prefix = [sys.executable, "-c",
                  "import sys; sys.path.insert(0, sys.argv[1]); "
                  "from ariadne_lib import core_predicate; "
                  f"core_predicate.MAX_STRUCTURED_KEY_CHARACTERS_TOTAL = {budget}; "
                  "import ariadne; sys.exit(ariadne.main(sys.argv[2:]))",
                  str(ARIADNE_SCRIPT.parent)]
    exits = []
    started = time.perf_counter_ns()
    for path in paths:
        result = subprocess.run(  # phylax: allow subprocess: fixed interpreter and Ariadne argv
            [*prefix, "verify", str(path), *arguments], cwd=ROOT, capture_output=True,
            env=child_environment(), timeout=3600,
        )
        exits.append(result.returncode)
    elapsed = (time.perf_counter_ns() - started) // 1_000_000
    evidence.update(files=len(paths), nonzero_exits=sum(1 for code in exits if code))
    return int(elapsed)


CRITERIA = {
    "cap-release-verifies": cap_release_verifies,
    "default-reader-verifies": default_reader_verifies,
    "pinned-statements-stay-single": pinned_statements_stay_single,
    "set-verify-milliseconds": set_verify_milliseconds,
    "statement-set-bytes": statement_set_bytes,
}


def fresh_write(path: str, data: bytes) -> None:
    with open(path, "xb") as handle:
        handle.write(data)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("criterion", choices=sorted(CRITERIA))
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--out", help="write the report to this new path")
    parser.add_argument("--evidence", help="write the supporting figures to this new path")
    args = parser.parse_args(argv)
    for option in (args.out, args.evidence):
        if option and os.path.lexists(option):
            parser.error(f"{option} already exists; a report is never replaced")
    try:
        require_base_trees()
        m = load_modules()
        evidence: dict = {}
        with tempfile.TemporaryDirectory(prefix="fiat-1892-resolve-") as name:
            value = CRITERIA[args.criterion](m, args.candidate, Path(name), evidence)
    except Refusal as refusal:
        print(f"resolve.py: {refusal}", file=sys.stderr)
        return 1
    report = {
        "candidate": args.candidate,
        "command": f"python3 .hexaemeron/design/resolve.py {args.criterion} --candidate {args.candidate}",
        "criterion": args.criterion, "exit": 0, "schema": SCHEMA,
        "unit": UNITS[args.criterion], "value": value,
    }
    data = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")
    sys.stdout.write(data.decode("utf-8"))
    if args.out:
        fresh_write(args.out, data)
    if args.evidence:
        fresh_write(args.evidence,
                    (json.dumps(evidence, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
