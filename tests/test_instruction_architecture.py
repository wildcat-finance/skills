"""Step 1 guards for the framework-74 research boundary."""

from __future__ import annotations

import copy
from functools import lru_cache
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/instruction-architecture/benchmark.py"
FIXTURES = ROOT / "tests/fixtures/instruction-architecture"
MANIFEST = FIXTURES / "corpus-manifest.json"
PROFILES = FIXTURES / "invocation-profiles.json"
GRAPH = FIXTURES / "loader-graph.json"
PARTITION = FIXTURES / "byte-partition.json"
COHORTS = FIXTURES / "cohorts.json"
SEAL = FIXTURES / "holdout-seal.json"
INVENTORY = FIXTURES / "artifact-inventory.json"
SCHEMA = ROOT / "research/instruction-architecture/schemas/source-bound-v1.schema.json"
PROFILE_SCHEMA = ROOT / "research/instruction-architecture/schemas/invocation-profile-v1.schema.json"
STUDY = ROOT / "docs/instruction-architecture/study.md"
RUNBOOK = ROOT / "docs/instruction-architecture/runbook.md"
RECEIPTED_STUDY_SHA256 = (
    "8e7236de8321431f295647f9fdf0a4cd782fa4def89b260a98fd13402fea545a"
)
AMENDED_RUNBOOK_SHA256 = (
    "4d2f1af3ff6a42a5ba7d90068be842942907351c62a29ec57dae2fcf3ecd0d1d"
)
EXPECTED_KRONOS_RANKING_LEDGERS = {
    "plugins/alexandria/skills/alexandria/EVOLUTION.md",
    "plugins/anamnesis/skills/anamnesis/EVOLUTION.md",
    "plugins/ariadne/skills/ariadne/EVOLUTION.md",
    "plugins/berean/skills/berean/EVOLUTION.md",
    "plugins/brevitas/skills/brevitas/EVOLUTION.md",
    "plugins/hermes/skills/hermes/EVOLUTION.md",
    "plugins/hexaemeron/skills/elenchus/EVOLUTION.md",
    "plugins/hexaemeron/skills/ephoros/EVOLUTION.md",
    "plugins/hexaemeron/skills/fiat/EVOLUTION.md",
    "plugins/hexaemeron/skills/hypomnema/EVOLUTION.md",
    "plugins/hexaemeron/skills/imprimatur/EVOLUTION.md",
    "plugins/hexaemeron/skills/metron/EVOLUTION.md",
    "plugins/hexaemeron/skills/phylax/EVOLUTION.md",
    "plugins/hexaemeron/skills/protasis/EVOLUTION.md",
    "plugins/hexaemeron/skills/vulgate/EVOLUTION.md",
    "plugins/homologia/skills/homologia/EVOLUTION.md",
    "plugins/horos/skills/horos/EVOLUTION.md",
    "plugins/janus/skills/janus/EVOLUTION.md",
    "plugins/lazarus/skills/lazarus/EVOLUTION.md",
    "plugins/lemma/skills/lemma/EVOLUTION.md",
    "plugins/pandects/skills/pandects/EVOLUTION.md",
    "plugins/probitas/skills/probitas/EVOLUTION.md",
    "plugins/sapheneia/skills/sapheneia/EVOLUTION.md",
    "plugins/synkrisis/skills/synkrisis/EVOLUTION.md",
    "plugins/tabularium/skills/tabularium/EVOLUTION.md",
}

EXPECTED_STRUCTURED_REFERENCES = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": (177_562, "5d1773f9a5f51e957bd769deb3b030b670fa10499e33fce4a8df3a2e221bd5ac"),
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": (3_779, "d2ecc41b3da60df47d5a7ce86f338dbadf7beb18080957dee21881dae4503d1d"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": (3_716, "e554ab6f9661d88095f285c6651983c980bd672b854287f74daa288b1dabc34c"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": (7_842, "a6ad7adbc6c8e06512032cf460c92749a49a6c139b4f2aee101de8bdc95df844"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": (3_843, "908e20c6319b587e95fa21de5949a10c0088ed698d546b0a1048686211826240"),
    "plugins/homologia/references/manifest-v1.schema.json": (3_554, "b60b46a65def47e11347fe408709c137b17accdd6fe2b39872c102c7c7db7413"),
    "plugins/homologia/references/vectors-v1.schema.json": (3_494, "1031838d2405c949a2ad7fcb9c693119499f1f8183286fe2019e02fa6680b056"),
    "plugins/synkrisis/references/cohort-v1.schema.json": (3_204, "5e71420816444af4582e0380b9d6e7ff845e4b3686126233c24a9d1ab5335b0d"),
    "plugins/synkrisis/references/findings-v1.schema.json": (4_152, "52cf6589e57a93fa82eef75520be44f10636d2469eafe2dae9c91e1d457627c8"),
    "plugins/synkrisis/references/policy-v1.schema.json": (1_982, "04d440bdbd96fcff165d4b0badc029a79634bf17b1a7ac380baee85630c873bb"),
    "plugins/synkrisis/references/rule-v1.schema.json": (3_087, "c8b45c1b6e2b9de010d7ce17109a6f7d49a4797d5a79b07186eabdfa1ed44698"),
    "plugins/synkrisis/references/rules-v1.json": (2_361, "e754bb72235103290ec4ea58b2c71b851782573c3e27eb16a08fe762c3f3a4af"),
}

EXPECTED_OPERATION_REFERENCES = {
    "docs/fiat-run-observation-binding-v1.md",
    "plugins/alexandria/docs/runbook.md",
    "plugins/alexandria/docs/study.md",
    "plugins/alexandria/docs/usdc-interval-collector.md",
    "plugins/anamnesis/docs/demo.md",
    "plugins/ariadne/docs/capturing-a-dataset.md",
    "plugins/ariadne/docs/capturing-a-grounded-agent.md",
    "plugins/ariadne/docs/capturing-a-release.md",
    "plugins/ariadne/docs/capturing-a-state-fixture.md",
    "plugins/ariadne/docs/conformance.md",
    "plugins/ariadne/docs/dataset.md",
    "plugins/ariadne/docs/grounded-agent.md",
    "plugins/ariadne/docs/solidity-release.md",
    "plugins/ariadne/docs/state-fixture.md",
    "plugins/lazarus/docs/chain-anchors.md",
    "plugins/lazarus/docs/preservation-release.md",
    "plugins/lazarus/docs/runbook.md",
    "plugins/lazarus/docs/study.md",
    "plugins/lemma/INVARIANTS.md",
    "plugins/pandects/docs/applicability.md",
    "plugins/pandects/docs/writing-a-law.md",
    "plugins/pandects/integrations/wildcat/APPLICABILITY.md",
    "plugins/probitas/docs/adding-a-venue.md",
    "plugins/tabularium/docs/adding-an-adapter.md",
    "plugins/tabularium/docs/release-policy.md",
}

EXPECTED_ARIADNE_OPERATIONS = {
    "operation:ariadne:capture-dataset": {
        "plugins/ariadne/docs/capturing-a-dataset.md",
        "plugins/ariadne/docs/dataset.md",
    },
    "operation:ariadne:capture-grounded-agent": {
        "plugins/ariadne/docs/capturing-a-grounded-agent.md",
        "plugins/ariadne/docs/grounded-agent.md",
    },
    "operation:ariadne:capture-release": {
        "plugins/ariadne/docs/capturing-a-release.md",
        "plugins/ariadne/docs/solidity-release.md",
    },
    "operation:ariadne:capture-state-fixture": {
        "plugins/ariadne/docs/capturing-a-state-fixture.md",
        "plugins/ariadne/docs/state-fixture.md",
    },
    "operation:ariadne:conformance": {"plugins/ariadne/docs/conformance.md"},
}


def load_module():
    spec = importlib.util.spec_from_file_location("instruction_architecture", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AI = load_module()


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_source_cache() -> None:
    for name in (
        "_source_mode",
        "_inventory_source_snapshot",
        "_source_object",
        "_frozen_tree_paths",
    ):
        cached = getattr(AI, name, None)
        if cached is not None:
            cached.cache_clear()
    oracle_source_mode.cache_clear()
    oracle_inventory_snapshot.cache_clear()
    oracle_inventory_sources.cache_clear()
    oracle_tree_paths.cache_clear()
    ORACLE_SOURCE_CACHE.clear()


def scratch_directory(prefix: str = "instruction-architecture-"):
    """Keep confined-path fixtures under the repository's ignored scratch root."""
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


ORACLE_SOURCE_REF = "a2b634d8e039af988bf30c8316defccf70071d8d"
ORACLE_MAX_JSON_BYTES = 8 * 1024 * 1024
ORACLE_MAX_SOURCE_BYTES = 2 * 1024 * 1024
ORACLE_MAX_FROZEN_TREE_PATHS = 10_000
ORACLE_BASELINE_INVENTORY_SHA256 = (
    "7e8566c5e9148ca151323636f51d7d69d7ff0215fb937619eefd4b621fc5bcb9"
)
ORACLE_SKILL_PATHS = {
    "alexandria": "plugins/alexandria/skills/alexandria/SKILL.md",
    "anamnesis": "plugins/anamnesis/skills/anamnesis/SKILL.md",
    "ariadne": "plugins/ariadne/skills/ariadne/SKILL.md",
    "berean": "plugins/berean/skills/berean/SKILL.md",
    "brevitas": "plugins/brevitas/skills/brevitas/SKILL.md",
    "elenchus": "plugins/hexaemeron/skills/elenchus/SKILL.md",
    "ephoros": "plugins/hexaemeron/skills/ephoros/SKILL.md",
    "fiat": "plugins/hexaemeron/skills/fiat/SKILL.md",
    "fizz": "plugins/hexaemeron/skills/fizz/SKILL.md",
    "fizz-convert": "plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md",
    "fizz-sync": "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md",
    "hermes": "plugins/hermes/skills/hermes/SKILL.md",
    "homologia": "plugins/homologia/skills/homologia/SKILL.md",
    "horos": "plugins/horos/skills/horos/SKILL.md",
    "hypomnema": "plugins/hexaemeron/skills/hypomnema/SKILL.md",
    "imprimatur": "plugins/hexaemeron/skills/imprimatur/SKILL.md",
    "janus": "plugins/janus/skills/janus/SKILL.md",
    "kronos": "plugins/hexaemeron/skills/kronos/SKILL.md",
    "lazarus": "plugins/lazarus/skills/lazarus/SKILL.md",
    "lemma": "plugins/lemma/skills/lemma/SKILL.md",
    "metron": "plugins/hexaemeron/skills/metron/SKILL.md",
    "pandects": "plugins/pandects/skills/pandects/SKILL.md",
    "phylax": "plugins/hexaemeron/skills/phylax/SKILL.md",
    "probitas": "plugins/probitas/skills/probitas/SKILL.md",
    "protasis": "plugins/hexaemeron/skills/protasis/SKILL.md",
    "sapheneia": "plugins/sapheneia/skills/sapheneia/SKILL.md",
    "solidity-auditor": "plugins/hexaemeron/skills/solidity-auditor/SKILL.md",
    "synkrisis": "plugins/synkrisis/skills/synkrisis/SKILL.md",
    "tabularium": "plugins/tabularium/skills/tabularium/SKILL.md",
    "vulgate": "plugins/hexaemeron/skills/vulgate/SKILL.md",
    "x-ray": "plugins/hexaemeron/skills/x-ray/SKILL.md",
}
ORACLE_FIXED_INPUTS = {
    ".python-version": "agent-or-prompt",
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": "mandatory-executable",
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": "mandatory-executable",
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": "mandatory-executable",
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": "mandatory-executable",
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": "mandatory-executable",
    "plugins/hexaemeron/skills/solidity-auditor/VERSION": "agent-or-prompt",
    "plugins/hexaemeron/skills/x-ray/VERSION": "agent-or-prompt",
    "plugins/synkrisis/references/rules-v1.json": "mandatory-executable",
}
ORACLE_EVIDENCE_PROJECTION_SHA256 = (
    "a095623b489914a089d7d3c0233d8fdc7ba5a24a3d8dfaf63de7f3e656b98975"
)
ORACLE_PROFILE_EVIDENCE_COUNTS = {
    "document_reference": 963,
    "fixed_input": 53,
    "frontier_ledger": 625,
    "frontier_policy": 25,
    "operation_reference": 22,
    "overlay_contract": 149,
    "related_skill": 2_013,
    "selected_skill": 519,
    "structured_reference": 427,
    "worker_prompt": 288,
}
ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS = {
    "fixed_input": 3,
    "markdown_reference": 3,
    "operation_reference": 3,
    "structured_reference": 12,
}
ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": 1,
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": 1,
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": 1,
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": 1,
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": 1,
    "plugins/synkrisis/references/rules-v1.json": 1,
}
ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": 4,
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": 4,
    "plugins/synkrisis/references/rules-v1.json": 3,
}
ORACLE_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_LITERAL_PATHSPECS": "1",
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "LANG": "C",
    "LC_ALL": "C",
}
ORACLE_SOURCE_CACHE: dict[str, bytes] = {}


def oracle_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def oracle_open_parent(path: Path) -> tuple[int, str]:
    """Open one repository parent without following mutable path components."""
    if (
        not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_NONBLOCK")
    ):
        raise AssertionError("independent no-follow reads are unavailable")
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise AssertionError("independent input leaves repository") from exc
    if not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise AssertionError("independent input path is unsafe")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        descriptor = os.open(ROOT, flags)
    except OSError as exc:
        raise AssertionError(
            "independent input root is unavailable or unsafe"
        ) from exc
    try:
        for part in relative.parent.parts:
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except OSError as exc:
                raise AssertionError(
                    "independent input parent is unavailable or unsafe"
                ) from exc
            metadata = os.fstat(child)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(child)
                raise AssertionError(
                    "independent input parent is unavailable or unsafe"
                )
            os.close(descriptor)
            descriptor = child
        return descriptor, relative.name
    except BaseException:
        os.close(descriptor)
        raise


def oracle_read_regular(path: Path, limit: int) -> bytes:
    """Read one bounded regular file and bind its name to the observed inode."""
    parent, name = oracle_open_parent(path)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        descriptor = os.open(name, flags, dir_fd=parent)
    except OSError as exc:
        os.close(parent)
        raise AssertionError("independent input is unavailable or unsafe") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise AssertionError(
                "independent input is not a single-link regular file"
            )
        if before.st_size > limit:
            raise AssertionError("independent input exceeds byte limit")
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(descriptor, min(65_536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise AssertionError("independent input exceeds byte limit")
        after = os.fstat(descriptor)
        if oracle_identity(before) != oracle_identity(after):
            raise AssertionError("independent input changed during read")
    finally:
        os.close(descriptor)
        os.close(parent)

    current_parent, current_name = oracle_open_parent(path)
    try:
        try:
            current = os.open(current_name, flags, dir_fd=current_parent)
        except OSError as exc:
            raise AssertionError("independent input changed during read") from exc
        try:
            if oracle_identity(os.fstat(current)) != oracle_identity(after):
                raise AssertionError("independent input changed during read")
        finally:
            os.close(current)
    finally:
        os.close(current_parent)
    return b"".join(chunks)


def oracle_git(
    *arguments: str, input_data: bytes | None = None
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            "/usr/bin/git",
            "--no-lazy-fetch",
            "--no-optional-locks",
            "-C",
            str(ROOT),
            *arguments,
        ],
        stdin=subprocess.DEVNULL if input_data is None else None,
        input=input_data,
        capture_output=True,
        check=False,
        timeout=20,
        env=ORACLE_GIT_ENV,
    )


@lru_cache(maxsize=1)
def oracle_source_mode() -> str:
    expression = f"{ORACLE_SOURCE_REF}^{{commit}}"
    probe = oracle_git(
        "cat-file",
        "--batch-check=%(objectname) %(objecttype)",
        input_data=f"{expression}\n".encode("ascii"),
    )
    if probe.returncode != 0:
        raise AssertionError("independent oracle source probe failed")
    if probe.stdout == f"{ORACLE_SOURCE_REF} commit\n".encode("ascii"):
        return "git"
    if probe.stdout != f"{expression} missing\n".encode("ascii"):
        raise AssertionError("independent oracle source probe was ambiguous")
    shallow = oracle_git("rev-parse", "--is-shallow-repository")
    if shallow.returncode != 0 or shallow.stdout != b"true\n":
        raise AssertionError("independent oracle could not resolve the frozen source")
    return "inventory"


@lru_cache(maxsize=1)
def oracle_inventory_snapshot() -> tuple[dict[str, bytes], tuple[str, ...]]:
    """Bind shallow source bytes and tree paths in one independent snapshot."""
    inventory_raw = oracle_read_regular(INVENTORY, ORACLE_MAX_JSON_BYTES)
    if (
        hashlib.sha256(inventory_raw).hexdigest()
        != ORACLE_BASELINE_INVENTORY_SHA256
    ):
        raise AssertionError("independent inventory differs from its source anchor")
    inventory = json.loads(inventory_raw)
    if canonical(inventory) != inventory_raw:
        raise AssertionError("independent inventory snapshot is not canonical")
    if (
        inventory.get("schema")
        != "wildcat-instruction-architecture-artifact-inventory/v1"
        or inventory.get("source_ref") != ORACLE_SOURCE_REF
    ):
        raise AssertionError("independent inventory snapshot identity mismatch")

    bound: dict[str, dict] = {}
    for name, path in (
        ("corpus-manifest.json", MANIFEST),
        ("invocation-profiles.json", PROFILES),
        ("loader-graph.json", GRAPH),
    ):
        raw = oracle_read_regular(path, ORACLE_MAX_JSON_BYTES)
        identity = inventory.get("artifacts", {}).get(name)
        if (
            not isinstance(identity, dict)
            or identity.get("bytes") != len(raw)
            or identity.get("sha256") != hashlib.sha256(raw).hexdigest()
        ):
            raise AssertionError(f"independent inventory binding mismatch: {name}")
        value = json.loads(raw)
        if canonical(value) != raw:
            raise AssertionError(f"independent inventory record is not canonical: {name}")
        bound[name] = value

    manifest = bound["corpus-manifest.json"]
    source = manifest.get("source")
    if (
        not isinstance(source, dict)
        or set(source) != {"ref", "repository_paths", "tree_sha256"}
        or source.get("ref") != ORACLE_SOURCE_REF
    ):
        raise AssertionError("independent manifest source ref mismatch")
    repository_paths = source.get("repository_paths")
    if (
        not isinstance(repository_paths, list)
        or not repository_paths
        or len(repository_paths) > ORACLE_MAX_FROZEN_TREE_PATHS
        or any(not isinstance(path, str) for path in repository_paths)
        or repository_paths != sorted(set(repository_paths))
        or any(
            PurePosixPath(path).is_absolute()
            or str(PurePosixPath(path)) != path
            or "\\" in path
            or any(part in {"", ".", ".."} for part in PurePosixPath(path).parts)
            for path in repository_paths
        )
    ):
        raise AssertionError("independent manifest repository paths are malformed")
    digests: dict[str, tuple[int | None, str]] = {}
    spans: list[tuple[str, int, int, str]] = []
    for document in manifest.get("documents", []):
        path = document.get("path")
        size = document.get("bytes")
        digest = document.get("sha256")
        if (
            not isinstance(path, str)
            or type(size) is not int
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or path in digests
        ):
            raise AssertionError("independent manifest source identity is malformed")
        digests[path] = (size, digest)

    def collect(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                collect(item)
            return
        if not isinstance(value, dict):
            return
        if {
            "path",
            "source_sha256",
            "span_sha256",
            "start",
            "end",
        } <= set(value):
            path = value["path"]
            digest = value["source_sha256"]
            span_digest = value["span_sha256"]
            start = value["start"]
            end = value["end"]
            if (
                not isinstance(path, str)
                or not isinstance(digest, str)
                or not isinstance(span_digest, str)
                or type(start) is not int
                or type(end) is not int
                or start < 0
                or end <= start
            ):
                raise AssertionError("independent source evidence is malformed")
            existing = digests.get(path)
            if existing is not None and existing[1] != digest:
                raise AssertionError("independent source evidence conflicts")
            digests[path] = (existing[0] if existing is not None else None, digest)
            spans.append((path, start, end, span_digest))
        for item in value.values():
            collect(item)

    for value in bound.values():
        collect(value)
    if not set(digests) <= set(repository_paths):
        raise AssertionError("independent manifest omits a source evidence path")
    sources: dict[str, bytes] = {}
    for path, (size, digest) in sorted(digests.items()):
        source_path = ROOT / path
        data = oracle_read_regular(source_path, ORACLE_MAX_SOURCE_BYTES)
        if (
            (size is not None and len(data) != size)
            or hashlib.sha256(data).hexdigest() != digest
        ):
            raise AssertionError(f"independent snapshot source drift: {path}")
        sources[path] = data
    for path, start, end, digest in spans:
        data = sources[path]
        if end > len(data) or hashlib.sha256(data[start:end]).hexdigest() != digest:
            raise AssertionError(f"independent snapshot span drift: {path}")
    return sources, tuple(repository_paths)


@lru_cache(maxsize=1)
def oracle_inventory_sources() -> dict[str, bytes]:
    """Return source bytes from the independently bound shallow snapshot."""
    return oracle_inventory_snapshot()[0]


@lru_cache(maxsize=1)
def oracle_tree_paths() -> tuple[str, ...]:
    """Enumerate the frozen tree without using the production path reader."""
    if oracle_source_mode() == "git":
        process = oracle_git(
            "ls-tree", "-r", "-z", "--name-only", ORACLE_SOURCE_REF
        )
        if process.returncode != 0:
            raise AssertionError("independent oracle could not enumerate source paths")
        try:
            paths = tuple(
                item.decode("utf-8", errors="strict")
                for item in process.stdout.split(b"\0")
                if item
            )
        except UnicodeDecodeError as exc:
            raise AssertionError("independent source path is not UTF-8") from exc
    else:
        _, paths = oracle_inventory_snapshot()
    if not paths or list(paths) != sorted(set(paths)):
        raise AssertionError("independent source path inventory is not canonical")
    return paths


def oracle_source(path: str) -> bytes:
    """Read the frozen blob without importing the production source reader."""
    if path in ORACLE_SOURCE_CACHE:
        expected = ORACLE_SOURCE_CACHE[path]
    elif oracle_source_mode() == "git":
        process = oracle_git("cat-file", "blob", f"{ORACLE_SOURCE_REF}:{path}")
        if process.returncode != 0:
            raise AssertionError(f"independent oracle could not read {path}")
        expected = process.stdout
    else:
        expected = oracle_inventory_sources().get(path)
        if expected is None:
            raise AssertionError(f"independent oracle has no snapshot source: {path}")
    live = oracle_read_regular(ROOT / path, ORACLE_MAX_SOURCE_BYTES)
    if live != expected:
        raise AssertionError(f"independent oracle observed source drift: {path}")
    ORACLE_SOURCE_CACHE[path] = expected
    return expected


def oracle_evidence(obligation: str, path: str, needle: str) -> dict:
    """Build one test-owned frozen span without production evidence helpers."""
    data = oracle_source(path)
    encoded = needle.encode("utf-8")
    start = data.find(encoded)
    if start < 0:
        raise AssertionError(f"independent semantic anchor is absent: {path}")
    return {
        "obligation": obligation,
        "path": path,
        "start": start,
        "end": start + len(encoded),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "span_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def oracle_span(path: str, needle: str) -> dict:
    """Build test-owned evidence without an obligation projection field."""
    evidence = oracle_evidence("", path, needle)
    del evidence["obligation"]
    return evidence


def oracle_manifest_source_anchor(path: str) -> tuple[str, str, str]:
    """Resolve all manifest source relations without production metadata."""
    anchors = {
        ".python-version": (
            "fixed_input",
            "AGENTS.md",
            "Every `python3` command below means the exact interpreter recorded in\n"
            "[`.python-version`](.python-version).",
        ),
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["hermes"],
            "Every candidate names a rule from "
            "[references/gas-rule-corpus.json](references/gas-rule-corpus.json)",
        ),
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["hermes"],
            "A corpus that fails its own schema",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "`gated.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "`hard.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "`structural.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/agent-replies.md": (
            "markdown_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "references/agent-replies.md",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md": (
            "markdown_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "references/lexicon-rationale.md",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/rewriting.md": (
            "markdown_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "references/rewriting.md",
        ),
        "plugins/hexaemeron/skills/solidity-auditor/VERSION": (
            "fixed_input",
            ORACLE_SKILL_PATHS["solidity-auditor"],
            "Read the local `VERSION` file from the same directory as this skill",
        ),
        "plugins/hexaemeron/skills/x-ray/VERSION": (
            "fixed_input",
            ORACLE_SKILL_PATHS["x-ray"],
            "Read the local `VERSION` file from `$SKILL_DIR/VERSION`",
        ),
        "plugins/homologia/references/manifest-v1.schema.json": (
            "structured_reference",
            "plugins/homologia/docs/checked-inputs/runbook.md",
            "plugins/homologia/references/manifest-v1.schema.json",
        ),
        "plugins/homologia/references/vectors-v1.schema.json": (
            "structured_reference",
            "plugins/homologia/docs/checked-inputs/runbook.md",
            "plugins/homologia/references/vectors-v1.schema.json",
        ),
        "plugins/pandects/docs/applicability.md": (
            "operation_reference",
            ORACLE_SKILL_PATHS["pandects"],
            "`docs/applicability.md` states the rules once",
        ),
        "plugins/pandects/docs/writing-a-law.md": (
            "operation_reference",
            ORACLE_SKILL_PATHS["pandects"],
            "`docs/writing-a-law.md`",
        ),
        "plugins/pandects/integrations/wildcat/APPLICABILITY.md": (
            "operation_reference",
            ORACLE_SKILL_PATHS["pandects"],
            "`integrations/wildcat/APPLICABILITY.md` carries all of them",
        ),
        "plugins/synkrisis/references/rules-v1.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["synkrisis"],
            "python3 plugins/synkrisis/scripts/synkrisis.py diagnose \\\n"
            "  --cohort build/synkrisis/cohort.json \\\n"
            "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
            "  --out build/synkrisis/findings.json",
        ),
    }
    for name in (
        "cohort-v1.schema.json",
        "findings-v1.schema.json",
        "policy-v1.schema.json",
        "rule-v1.schema.json",
    ):
        candidate = f"plugins/synkrisis/references/{name}"
        anchors[candidate] = (
            "structured_reference",
            candidate,
            f'"$id": "https://github.com/wildcat-finance/skills/{candidate}"',
        )
    try:
        return anchors[path]
    except KeyError as error:
        raise AssertionError(
            f"independent manifest source relation is unowned: {path}"
        ) from error


def oracle_runtime_anchor(target: str, context: str) -> tuple[str, str]:
    """Resolve every executable input through a test-owned runtime grammar."""
    if target == "plugins/hermes/skills/hermes/references/gas-rule-corpus.json":
        return (
            "plugins/hermes/skills/hermes/scripts/hermes.py",
            "raw = corpus_path.read_bytes()",
        )
    if target == "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json":
        return (
            "plugins/hermes/skills/hermes/scripts/hermes.py",
            'schema = json.loads(schema_path.read_text(encoding="utf-8"))',
        )
    if target in {
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
    }:
        return (
            "plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py",
            'return rd("hard.json"), rd("gated.json"), rd("structural.json")',
        )
    if target != "plugins/synkrisis/references/rules-v1.json":
        raise AssertionError(
            f"independent runtime target is unowned: {target}"
        )
    needles = {
        "manifest": (
            "def load_rules(root: Path, raw_path: str, budget: InputBudget):\n"
            '    target = confined_relative(raw_path, root, label="rules")\n'
            "    shown = shown_path(raw_path)\n"
            "    payload = bounded_read(target, shown, MAX_FILE_BYTES)"
        ),
        "diagnose": (
            "def command_diagnose(root: Path, arguments):\n"
            "    budget = InputBudget()\n"
            "    cohort = load_cohort(root, arguments.cohort, budget)\n"
            "    rules_document, _ = load_rules(root, arguments.rules, budget)"
        ),
        "verify": (
            '            "rebuild the cohort with the cohort command from the original inputs",\n'
            "        )\n"
            "    rules_document, _ = load_rules(root, arguments.rules, budget)"
        ),
    }
    try:
        return "plugins/synkrisis/scripts/synkrisis.py", needles[context]
    except KeyError as error:
        raise AssertionError(
            f"independent Synkrisis runtime context is unowned: {context}"
        ) from error


def oracle_validate_manifest_semantic_anchors(manifest: dict) -> None:
    """Close every manifest source/runtime row under test-owned anchors."""
    source_counts = {
        name: 0 for name in ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS
    }
    runtime_counts = {
        target: 0 for target in ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS
    }
    documents = manifest.get("documents")
    if not isinstance(documents, list):
        raise AssertionError("independent manifest document ledger is not an array")
    for item in documents:
        evidence = item.get("source_evidence")
        if evidence is not None:
            evidence_class, source, needle = oracle_manifest_source_anchor(
                item["path"]
            )
            if (
                item.get("document_class") != evidence_class
                or evidence != oracle_span(source, needle)
            ):
                raise AssertionError(
                    f"independent manifest source anchor mismatch: {item['path']}"
                )
            source_counts[evidence_class] += 1
        runtime = item.get("runtime_evidence")
        if runtime is not None:
            runtime_path, runtime_needle = oracle_runtime_anchor(
                item["path"], "manifest"
            )
            if runtime != oracle_span(runtime_path, runtime_needle):
                raise AssertionError(
                    f"independent manifest runtime anchor mismatch: {item['path']}"
                )
            runtime_counts[item["path"]] += 1
    if source_counts != ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS or sum(
        source_counts.values()
    ) != sum(item.get("source_evidence") is not None for item in documents):
        raise AssertionError("independent manifest source coverage mismatch")
    if runtime_counts != ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS or sum(
        runtime_counts.values()
    ) != sum(item.get("runtime_evidence") is not None for item in documents):
        raise AssertionError("independent manifest runtime coverage mismatch")


def oracle_validate_runtime_edges(record: dict, graph: dict) -> None:
    """Close every host/scenario runtime row under test-owned anchors."""
    profiles = {
        row["id"]: row for row in record.get("profiles", [])
    }
    roots = {
        row["id"]: row for row in graph.get("scenario_roots", [])
    }
    runtime_counts = {
        target: 0 for target in ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS
    }
    validated_scenario_relations: dict[
        tuple[str, str, str, str], list[dict]
    ] = {}
    scenario_rows = 0
    scenario_edges = graph.get("scenario_edges", [])
    if not isinstance(scenario_edges, list):
        raise AssertionError("independent scenario edge ledger is not an array")
    for edge in scenario_edges:
        runtime = edge.get("runtime_evidence")
        mandatory = edge.get("load_type") == "mandatory-executable"
        if (runtime is not None) != mandatory:
            raise AssertionError(
                f"independent scenario runtime presence mismatch: {edge.get('id')}"
            )
        if runtime is None:
            continue
        target = edge.get("target")
        context = "scenario"
        if target == "plugins/synkrisis/references/rules-v1.json":
            operations = set()
            for identifier in edge.get("active_scenarios", []):
                root = roots.get(identifier)
                if root is None or root.get("profile_id") not in profiles:
                    raise AssertionError(
                        "independent Synkrisis runtime scope escapes route roots"
                    )
                state = profiles[root["profile_id"]].get("branch_state")
                if not isinstance(state, list) or not state:
                    raise AssertionError(
                        "independent Synkrisis runtime profile has no branch state"
                    )
                operations.add(state[-1])
            if len(operations) != 1 or not operations <= {"diagnose", "verify"}:
                raise AssertionError(
                    "independent Synkrisis runtime scope mixes operations"
                )
            context = next(iter(operations))
        runtime_path, runtime_needle = oracle_runtime_anchor(target, context)
        if runtime != oracle_span(runtime_path, runtime_needle):
            raise AssertionError(
                f"independent scenario runtime anchor mismatch: {edge.get('id')}"
            )
        relation = (
            edge.get("source"),
            target,
            edge.get("kind"),
            edge.get("load_type"),
        )
        validated_scenario_relations.setdefault(relation, []).append(runtime)
        runtime_counts[target] += 1
        scenario_rows += 1

    host_rows = 0
    host_edges = graph.get("edges", [])
    if not isinstance(host_edges, list):
        raise AssertionError("independent host edge ledger is not an array")
    for edge in host_edges:
        runtime = edge.get("runtime_evidence")
        mandatory = edge.get("load_type") == "mandatory-executable"
        if (runtime is not None) != mandatory:
            raise AssertionError(
                f"independent host runtime presence mismatch: {edge.get('id')}"
            )
        if runtime is None:
            continue
        relation = (
            edge.get("source"),
            edge.get("target"),
            edge.get("kind"),
            edge.get("load_type"),
        )
        if runtime not in validated_scenario_relations.get(relation, []):
            raise AssertionError(
                f"independent host runtime anchor mismatch: {edge.get('id')}"
            )
        runtime_counts[edge["target"]] += 1
        host_rows += 1
    if (
        scenario_rows != 12
        or host_rows != 11
        or runtime_counts != ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS
    ):
        raise AssertionError("independent graph runtime coverage mismatch")


def cross_target_runtime_specimens(
    rows: list[dict], target_field: str
) -> dict[str, tuple[int, str, dict]]:
    """Choose one valid runtime span from a different implementation per target."""
    specimens: dict[str, tuple[int, str, dict]] = {}
    for index, row in enumerate(rows):
        runtime = row.get("runtime_evidence")
        target = row.get(target_field)
        if runtime is None or target in specimens:
            continue
        for donor in rows:
            donor_runtime = donor.get("runtime_evidence")
            donor_target = donor.get(target_field)
            if (
                donor_runtime is not None
                and donor_target != target
                and donor_runtime["path"] != runtime["path"]
                and donor_runtime != runtime
            ):
                specimens[target] = (
                    index,
                    donor_target,
                    copy.deepcopy(donor_runtime),
                )
                break
    if set(specimens) != set(ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS):
        raise AssertionError("runtime rebind specimens do not cover every target")
    return specimens


def oracle_semantic_anchor(profile: dict, obligation: str) -> tuple[str, str]:
    """Name exact skill/frontier relations from the frozen source grammar."""
    selected_skill = profile["selected_skill"]
    selected = ORACLE_SKILL_PATHS[selected_skill]
    skill_by_path = {path: skill for skill, path in ORACLE_SKILL_PATHS.items()}
    if obligation == selected:
        return selected, f"name: {selected_skill}"

    if obligation.endswith("/EVOLUTION.md"):
        selected_evolution = str(Path(selected).with_name("EVOLUTION.md")).replace(
            os.sep, "/"
        )
        if obligation == selected_evolution:
            return selected, "[EVOLUTION.md](EVOLUTION.md)"
        if selected_skill != "kronos":
            raise AssertionError("independent frontier relation escaped Kronos")
        return (
            selected,
            "Walk the whole scope and find every `EVOLUTION.md` beneath it, descending\n"
            "   into each plugin's own skills directory.",
        )

    if not obligation.endswith("/SKILL.md") or obligation not in skill_by_path:
        raise AssertionError("independent semantic anchor received a non-skill path")
    target_skill = skill_by_path[obligation]

    if selected_skill == "kronos":
        dispatch = profile["branch_state"][-1]
        if not dispatch.startswith("dispatch-"):
            raise AssertionError("independent Kronos relation escaped dispatch")
        if target_skill not in {"fiat", dispatch.removeprefix("dispatch-")}:
            raise AssertionError("independent Kronos dispatch target mismatch")
        return (
            selected,
            "Read the selected skill's canonical instructions, its ledger, and Fiat's\n"
            "   `SKILL.md`.",
        )

    if selected_skill == "fiat":
        direct = {
            name: f"[{name}](../{name}/SKILL.md)"
            for name in (
                "protasis",
                "phylax",
                "ephoros",
                "metron",
                "elenchus",
                "hypomnema",
            )
        }
        if target_skill in direct:
            return selected, direct[target_skill]
        if target_skill == "brevitas":
            return (
                "plugins/hexaemeron/agents/scribe.md",
                "Where an artefact is engineering review, audit, gas, protocol-property, or\n"
                "specification commentary, apply Brevitas after the vocabulary and register\n"
                "passes without deleting evidence.",
            )
        if target_skill == "hermes":
            return (
                "plugins/hexaemeron/agents/mason.md",
                "Hermes owns Solidity gas. Do not silently import a sibling's job into the step.",
            )
        if target_skill == "fizz-sync":
            return (
                ORACLE_SKILL_PATHS["elenchus"],
                "When the fix touched contracts, run `fizz-sync` first.",
            )
        if target_skill == "fizz":
            return (
                "plugins/hexaemeron/agents/warden.md",
                "`fizz`\nis in the suite, follow `<plugin-root>/skills/fizz/SKILL.md`",
            )
        if target_skill in {"x-ray", "solidity-auditor"}:
            return (
                "plugins/hexaemeron/skills/fiat/references/audit-loop.md",
                "`x-ray` pass first, then `solidity-auditor`. Both are vendored under\n"
                "   `$PLUGIN_ROOT/skills/<name>/` (as defined in the entry skill) -- read\n"
                "   each SKILL.md and follow\n"
                "   it.",
            )
        if target_skill == "imprimatur":
            if profile["phase"] == "prose directive":
                return (
                    "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                    '`python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" <file>`',
                )
            if profile["id"] == "fiat:integrate-task-issue":
                return (
                    selected,
                    "under the repository's Sapheneia,\n"
                    "Imprimatur, Vulgate, Imprimatur publication order.",
                )
            return selected, "Run the `imprimatur` lint on each artefact before receipting it"
        if target_skill == "vulgate":
            return (
                "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                "$PLUGIN_ROOT/skills/vulgate/SKILL.md",
            )
        if target_skill == "sapheneia":
            if profile["phase"] in {"Solidity audit round", "non-Solidity audit round"}:
                return (
                    "plugins/hexaemeron/skills/fiat/references/audit-loop.md",
                    "apply Sapheneia's bounded audit-record operation",
                )
            if profile["phase"] == "prose directive":
                return (
                    "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                    "Sapheneia -> Imprimatur -> Vulgate -> Imprimatur",
                )
            return (
                selected,
                "under the repository's Sapheneia,\n"
                "Imprimatur, Vulgate, Imprimatur publication order.",
            )
        raise AssertionError(f"independent Fiat skill relation is unowned: {target_skill}")

    if selected_skill == "fizz" and target_skill == "x-ray":
        return (
            selected,
            "Resolve `{SKILL_PATH}/../x-ray/SKILL.md`, read it completely, and execute "
            "its instructions against `{PROJECT_ROOT}`.",
        )
    if selected_skill == "elenchus" and target_skill == "fizz-sync":
        return selected, "When the fix touched contracts, run `fizz-sync` first."
    if selected_skill == "ephoros" and target_skill == "phylax":
        return selected, "`phylax` sets this rule and this skill inherits it"
    if selected_skill == "protasis" and target_skill in {
        "ephoros",
        "phylax",
        "metron",
        "elenchus",
        "hypomnema",
    }:
        return selected, f"[{target_skill}](../{target_skill}/SKILL.md)"
    raise AssertionError(
        f"independent skill relation is unowned: {selected_skill} -> {target_skill}"
    )


def oracle_document_anchor(selected_skill: str, obligation: str) -> tuple[str, str]:
    """Resolve document relations from a test-owned, closed source grammar."""
    fiat = ORACLE_SKILL_PATHS["fiat"]
    fizz = ORACLE_SKILL_PATHS["fizz"]
    solidity = ORACLE_SKILL_PATHS["solidity-auditor"]
    xray = ORACLE_SKILL_PATHS["x-ray"]
    name = Path(obligation).name
    if (
        selected_skill == "kronos"
        and obligation
        == "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"
    ):
        return (
            ORACLE_SKILL_PATHS["kronos"],
            "`../fiat/references/plugin-currency.md` names the host\n"
            "   mechanism.",
        )
    if obligation.startswith("plugins/hexaemeron/skills/fiat/references/"):
        source = fiat
        if name == "xray-reuse.md":
            source = "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
        elif name == "controller-checkpoint.md":
            source = "plugins/hexaemeron/skills/fiat/references/push-discipline.md"
        return source, name
    if obligation == "plugins/hermes/skills/hermes/references/optimisation-catalogue.md":
        return ORACLE_SKILL_PATHS["hermes"], "references/optimisation-catalogue.md"
    if obligation == "plugins/hexaemeron/skills/metron/references/budget-check.md":
        return ORACLE_SKILL_PATHS["metron"], "references/budget-check.md"
    if obligation == "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md":
        return ORACLE_SKILL_PATHS["phylax"], name
    if obligation.startswith("plugins/hexaemeron/skills/fizz/references/"):
        if name == "property-generation.md" and selected_skill == "fiat":
            return (
                "plugins/hexaemeron/skills/fizz/agents/implementers/"
                "specific-property-implementer.md",
                name,
            )
        return fizz, name
    if obligation.startswith("plugins/hexaemeron/skills/solidity-auditor/references/"):
        if name == "shared-rules.md":
            if selected_skill == "solidity-auditor":
                return solidity, "references/hacking-agents/shared-rules.md"
            return (
                "plugins/hexaemeron/skills/solidity-auditor/references/"
                "senior-auditor-sop.md",
                name,
            )
        if name == "senior-auditor-sop.md" and selected_skill != "solidity-auditor":
            return (
                "plugins/hexaemeron/skills/solidity-auditor/references/"
                "hacking-agents/shared-rules.md",
                name,
            )
        return solidity, name
    if obligation == "plugins/hexaemeron/skills/x-ray/references/templates.md":
        if selected_skill == "x-ray":
            return xray, "references/templates.md"
        return "plugins/hexaemeron/skills/x-ray/references/threats.md", name
    if obligation == "plugins/hexaemeron/skills/x-ray/references/threats.md":
        return xray, "references/threats.md"
    if obligation in {
        "plugins/probitas/skills/probitas/references/gates.md",
        "plugins/probitas/skills/probitas/references/venues.md",
    }:
        return ORACLE_SKILL_PATHS["probitas"], f"references/{name}"
    raise AssertionError(f"independent document relation is unowned: {obligation}")


def oracle_python_pin_anchor(profile: dict) -> tuple[str, str]:
    """Resolve the pin through a test-owned exact operation allowlist."""
    anchors = {
        "anamnesis:demo-or-rebuild": (
            ORACLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "anamnesis:ordinary": (
            ORACLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "berean:ordinary": (
            ORACLE_SKILL_PATHS["berean"],
            "Run everything from `$PLUGIN_ROOT` with the exact interpreter in the suite\n"
            "[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version)",
        ),
        "brevitas:ordinary": (
            "plugins/brevitas/AGENTS.md",
            "- Run the checker with the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version)",
        ),
        "hermes:gas-operation": (
            "plugins/hermes/AGENTS.md",
            "Run the harness with\n  the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "lemma:changed-or-unexpected": (
            "plugins/lemma/AGENTS.md",
            "- Use the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "lemma:ordinary": (
            "plugins/lemma/AGENTS.md",
            "- Use the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "probitas:add-venue": (
            "plugins/probitas/docs/adding-a-venue.md",
            "Run this with the exact interpreter in the suite\n"
            "[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "synkrisis:cohort-or-render": (
            ORACLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:diagnose": (
            ORACLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:verify": (
            ORACLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
    }
    try:
        return anchors[profile["id"]]
    except (KeyError, TypeError) as error:
        raise AssertionError(
            f"independent Python pin relation is unowned: {profile.get('id')}"
        ) from error


def oracle_full_semantic_anchor(
    profile: dict, obligation: str
) -> tuple[str, str, str]:
    """Classify every obligation and derive one test-owned semantic anchor."""
    selected_skill = profile["selected_skill"]
    selected = ORACLE_SKILL_PATHS[selected_skill]
    if obligation == selected:
        source, needle = oracle_semantic_anchor(profile, obligation)
        return "selected_skill", source, needle
    if obligation.endswith("/EVOLUTION.md"):
        source, needle = oracle_semantic_anchor(profile, obligation)
        return "frontier_ledger", source, needle
    if obligation.endswith("/SKILL.md"):
        source, needle = oracle_semantic_anchor(profile, obligation)
        return "related_skill", source, needle

    if obligation in EXPECTED_OPERATION_REFERENCES:
        source = selected
        if obligation == "plugins/probitas/docs/adding-a-venue.md":
            source = "plugins/probitas/skills/probitas/references/venues.md"
        return (
            "operation_reference",
            source,
            posixpath.relpath(obligation, posixpath.dirname(source)),
        )

    fiat_workers = {
        "plugins/hexaemeron/agents/mason.md",
        "plugins/hexaemeron/agents/scribe.md",
        "plugins/hexaemeron/agents/surveyor.md",
        "plugins/hexaemeron/agents/warden.md",
    }
    if obligation in fiat_workers:
        return "worker_prompt", ORACLE_SKILL_PATHS["fiat"], f"`{Path(obligation).stem}`"
    if obligation.startswith("plugins/hexaemeron/skills/fizz/agents/"):
        return (
            "worker_prompt",
            ORACLE_SKILL_PATHS["fizz"],
            posixpath.relpath(
                obligation, posixpath.dirname(ORACLE_SKILL_PATHS["fizz"])
            ),
        )
    if obligation == "plugins/hexaemeron/PROMISES.md":
        return (
            "overlay_contract",
            "plugins/hexaemeron/AGENTS.md",
            "[PROMISES.md](PROMISES.md)",
        )
    if obligation == "plugins/hexaemeron/skills/VERSIONING.md":
        return (
            "frontier_policy",
            "plugins/hexaemeron/AGENTS.md",
            "`skills/VERSIONING.md`",
        )

    if obligation == ".python-version":
        source, needle = oracle_python_pin_anchor(profile)
        return "fixed_input", source, needle

    if obligation in ORACLE_FIXED_INPUTS:
        if obligation == "plugins/hexaemeron/skills/x-ray/VERSION":
            return (
                "fixed_input",
                ORACLE_SKILL_PATHS["x-ray"],
                "Read the local `VERSION` file from `$SKILL_DIR/VERSION`",
            )
        if obligation == "plugins/hexaemeron/skills/solidity-auditor/VERSION":
            return (
                "fixed_input",
                ORACLE_SKILL_PATHS["solidity-auditor"],
                "Read the local `VERSION` file from the same directory as this skill",
            )
        if obligation == "plugins/hermes/skills/hermes/references/gas-rule-corpus.json":
            return (
                "structured_reference",
                ORACLE_SKILL_PATHS["hermes"],
                "Every candidate names a rule from "
                "[references/gas-rule-corpus.json](references/gas-rule-corpus.json)",
            )
        if obligation == "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json":
            return (
                "structured_reference",
                ORACLE_SKILL_PATHS["hermes"],
                "A corpus that fails its own schema",
            )
        if obligation.startswith("plugins/hexaemeron/skills/imprimatur/lexicon/"):
            return (
                "structured_reference",
                ORACLE_SKILL_PATHS["imprimatur"],
                f"`{Path(obligation).name}`",
            )
        if obligation == "plugins/synkrisis/references/rules-v1.json":
            needles = {
                "diagnose": (
                    "python3 plugins/synkrisis/scripts/synkrisis.py diagnose \\\n"
                    "  --cohort build/synkrisis/cohort.json \\\n"
                    "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
                    "  --out build/synkrisis/findings.json"
                ),
                "verify": (
                    "python3 plugins/synkrisis/scripts/synkrisis.py verify \\\n"
                    "  --manifest plugins/synkrisis/examples/cross-run-v0/manifest.json \\\n"
                    "  --policy plugins/synkrisis/examples/cross-run-v0/policy.json \\\n"
                    "  --cohort build/synkrisis/cohort.json \\\n"
                    "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
                    "  --findings build/synkrisis/findings.json"
                ),
            }
            operation = profile["branch_state"][-1]
            if operation not in needles:
                raise AssertionError("independent Synkrisis operation drift")
            return "structured_reference", ORACLE_SKILL_PATHS["synkrisis"], needles[operation]
        raise AssertionError(f"independent fixed relation is unowned: {obligation}")

    source, needle = oracle_document_anchor(selected_skill, obligation)
    return "document_reference", source, needle


def oracle_validate_semantic_anchors(profile: dict) -> dict[str, int]:
    """Require all obligations to carry independently derived semantic anchors."""
    evidence_by_obligation = {
        row["obligation"]: row for row in profile["source_evidence"]
    }
    counts = {name: 0 for name in ORACLE_PROFILE_EVIDENCE_COUNTS}
    for obligation in profile["required_documents"]:
        evidence_class, path, needle = oracle_full_semantic_anchor(profile, obligation)
        if evidence_class not in counts:
            raise AssertionError(
                f"independent semantic class is unowned: {evidence_class}"
            )
        expected = oracle_evidence(obligation, path, needle)
        if evidence_by_obligation.get(obligation) != expected:
            raise AssertionError(
                f"independent semantic anchor mismatch: {profile['id']}: {obligation}"
            )
        counts[evidence_class] += 1
    if sum(counts.values()) != len(profile["required_documents"]):
        raise AssertionError(f"independent semantic coverage gap: {profile['id']}")
    return counts


def oracle_add_profile(
    profiles: list[dict],
    skill: str,
    local_id: str,
    phase: str,
    documents: tuple[str, ...] = (),
    workers: tuple[str, ...] = (),
) -> None:
    required = sorted({ORACLE_SKILL_PATHS[skill], *documents})
    worker_prompts = sorted(set(workers))
    profiles.append(
        {
            "id": f"{skill}:{local_id}",
            "selected_skill": skill,
            "phase": phase,
            "applicability": f"bounded-operation:{skill}:{phase}",
            "branch_state": local_id.split("__"),
            "exclusive_group": f"{skill}:{phase}",
            "required_documents": required,
            "worker_prompts": worker_prompts,
            "fixed_inputs": [
                {"path": path, "load_semantics": ORACLE_FIXED_INPUTS[path]}
                for path in required
                if path in ORACLE_FIXED_INPUTS
            ],
        }
    )


def oracle_profiles() -> list[dict]:
    """Reconstruct the frozen bounded-operation grammar without production code."""
    rows: list[dict] = []
    evolution = {
        name: str(Path(path).with_name("EVOLUTION.md")).replace(os.sep, "/")
        for name, path in ORACLE_SKILL_PATHS.items()
        if name
        not in {"fizz", "fizz-convert", "fizz-sync", "solidity-auditor", "x-ray"}
    }
    versioning = "plugins/hexaemeron/skills/VERSIONING.md"
    promises = "plugins/hexaemeron/PROMISES.md"
    python_pin = (".python-version",)
    xray_version = "plugins/hexaemeron/skills/x-ray/VERSION"
    sol_aud_version = "plugins/hexaemeron/skills/solidity-auditor/VERSION"

    def add(
        skill: str,
        local_id: str,
        phase: str,
        documents: tuple[str, ...] = (),
        workers: tuple[str, ...] = (),
    ) -> None:
        oracle_add_profile(rows, skill, local_id, phase, documents, workers)

    def frontier(skill: str) -> None:
        add(skill, "frontier-gate", "gate-only frontier admission", (evolution[skill], versioning))

    add("alexandria", "ordinary", "capture/query/release")
    add(
        "alexandria",
        "ethereum-usdc-interval",
        "Ethereum USDC interval capture",
        (
            "plugins/alexandria/docs/usdc-interval-collector.md",
            "plugins/alexandria/docs/study.md",
            "plugins/alexandria/docs/runbook.md",
        ),
    )
    frontier("alexandria")
    add("anamnesis", "ordinary", "capture/verify/release", python_pin)
    add(
        "anamnesis",
        "demo-or-rebuild",
        "demo or verify-rebuild",
        python_pin + ("plugins/anamnesis/docs/demo.md",),
    )
    frontier("anamnesis")
    add("ariadne", "ordinary", "inspect/verify/replay")
    for local_id, phase, documents in (
        ("capture-release", "capture release", ("plugins/ariadne/docs/capturing-a-release.md", "plugins/ariadne/docs/solidity-release.md")),
        ("capture-dataset", "capture dataset", ("plugins/ariadne/docs/capturing-a-dataset.md", "plugins/ariadne/docs/dataset.md")),
        ("capture-state-fixture", "capture state fixture", ("plugins/ariadne/docs/capturing-a-state-fixture.md", "plugins/ariadne/docs/state-fixture.md")),
        ("capture-grounded-agent", "capture grounded agent", ("plugins/ariadne/docs/capturing-a-grounded-agent.md", "plugins/ariadne/docs/grounded-agent.md")),
        ("conformance", "conformance", ("plugins/ariadne/docs/conformance.md",)),
    ):
        add("ariadne", local_id, phase, documents)
    frontier("ariadne")
    for skill in ("berean", "brevitas", "homologia", "horos", "hypomnema", "janus", "sapheneia", "vulgate"):
        documents = python_pin if skill in {"berean", "brevitas"} else ()
        add(skill, "ordinary", "ordinary operation", documents)
        frontier(skill)

    hermes_runtime = (
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json",
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json",
        "plugins/hermes/skills/hermes/references/optimisation-catalogue.md",
    )
    add("hermes", "gas-operation", "gas analysis", python_pin + hermes_runtime)
    frontier("hermes")
    add("elenchus", "ordinary", "ordinary failure analysis")
    add("elenchus", "contract-fix", "contract failure", (ORACLE_SKILL_PATHS["fizz-sync"], promises))
    frontier("elenchus")
    add("ephoros", "ordinary", "telemetry operation", (ORACLE_SKILL_PATHS["phylax"],))
    frontier("ephoros")

    fizz_common = tuple(
        f"plugins/hexaemeron/skills/fizz/references/{name}.md"
        for name in ("template-map", "selection-policy", "setup-playbook", "handler-patterns")
    )
    fizz_report = ("plugins/hexaemeron/skills/fizz/agents/report-writer.md",)
    fizz_workers = (
        "plugins/hexaemeron/skills/fizz/agents/implementers/global-property-implementer.md",
        "plugins/hexaemeron/skills/fizz/agents/implementers/specific-property-implementer.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/adversarial-profit-maximizer.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/conservation-auditor.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/protocol-type-specialist.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/roundtrip-rounding-analyst.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/state-transition-mapper.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/synthesizer.md",
        "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md",
        fizz_report[0],
    )
    fizz_invariant = (
        "plugins/hexaemeron/skills/fizz/references/property-generation.md",
        *tuple(path for path in fizz_workers if path not in {fizz_report[0], "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md"}),
    )
    xray_full = (
        ORACLE_SKILL_PATHS["x-ray"],
        xray_version,
        promises,
        "plugins/hexaemeron/skills/x-ray/references/threats.md",
        "plugins/hexaemeron/skills/x-ray/references/templates.md",
    )
    for xray_state, invariant_state in itertools.product(("existing", "acquire", "fallback"), ("off", "on")):
        documents = fizz_common + fizz_report + (promises,)
        workers = fizz_report
        if xray_state in {"acquire", "fallback"}:
            documents += xray_full
        if xray_state == "fallback":
            analyzer = "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md"
            documents += (analyzer,)
            workers += (analyzer,)
        if invariant_state == "on":
            documents += fizz_invariant
            workers += tuple(path for path in fizz_invariant if "/agents/" in path)
        add("fizz", f"xray-{xray_state}__invariants-{invariant_state}", "fuzz-suite generation", documents, workers)
    add("fizz-convert", "convert", "property conversion", (promises,))
    add("fizz-sync", "sync", "harness reconciliation", (promises,))

    lexicons = (
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
    )
    add("imprimatur", "lint", "production lint", lexicons)
    frontier("imprimatur")
    add("metron", "ordinary", "measurement")
    add("metron", "budget-check", "budget check", ("plugins/hexaemeron/skills/metron/references/budget-check.md",))
    frontier("metron")
    add("phylax", "ordinary", "off-chain review")
    add("phylax", "model-proxy", "model proxy review", ("plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",))
    frontier("phylax")
    disciplines = tuple(ORACLE_SKILL_PATHS[name] for name in ("ephoros", "phylax", "metron", "elenchus", "hypomnema"))
    add("protasis", "runbook", "runbook validation")
    add("protasis", "study", "study validation", disciplines)
    frontier("protasis")

    sol_general = tuple(
        f"plugins/hexaemeron/skills/solidity-auditor/references/{name}.md"
        for name in ("report-formatting", "judging", "senior-auditor-sop")
    )
    sol_agents = tuple(
        path
        for path in oracle_tree_paths()
        if path.startswith(
            "plugins/hexaemeron/skills/solidity-auditor/"
            "references/hacking-agents/"
        )
        and path.endswith("-agent.md")
    )
    sol_shared = ("plugins/hexaemeron/skills/solidity-auditor/references/hacking-agents/shared-rules.md",)
    add("solidity-auditor", "audit", "Solidity audit", (sol_aud_version, promises) + sol_general + sol_shared + sol_agents, sol_agents)
    add("x-ray", "audit", "pre-audit analysis", xray_full[1:])

    add("lazarus", "ordinary", "capture/verify/replay")
    add("lazarus", "anchored-capture", "anchored capture", ("plugins/lazarus/docs/chain-anchors.md",))
    add("lazarus", "preservation-release", "preservation release", ("plugins/lazarus/docs/preservation-release.md",))
    add("lazarus", "maintenance", "maintenance", ("plugins/lazarus/docs/study.md", "plugins/lazarus/docs/runbook.md"))
    frontier("lazarus")
    add("lemma", "ordinary", "generate/verify", python_pin)
    add(
        "lemma",
        "changed-or-unexpected",
        "change/judge/unexpected-output",
        python_pin + ("plugins/lemma/INVARIANTS.md",),
    )
    frontier("lemma")
    add("pandects", "ordinary", "law operation")
    frontier("pandects")
    probitas = ("plugins/probitas/skills/probitas/references/gates.md", "plugins/probitas/skills/probitas/references/venues.md")
    add("probitas", "dossier", "dossier operation", probitas)
    add(
        "probitas",
        "add-venue",
        "add venue",
        python_pin + probitas + ("plugins/probitas/docs/adding-a-venue.md",),
    )
    frontier("probitas")
    rules = ("plugins/synkrisis/references/rules-v1.json",)
    add("synkrisis", "cohort-or-render", "cohort or render", python_pin)
    add("synkrisis", "diagnose", "diagnose", python_pin + rules)
    add("synkrisis", "verify", "verify", python_pin + rules)
    frontier("synkrisis")
    add("tabularium", "ordinary", "capture/verify")
    add("tabularium", "add-adapter", "add adapter", ("plugins/tabularium/docs/adding-an-adapter.md",))
    add("tabularium", "mapping-or-release", "correct mapping or release-policy", ("plugins/tabularium/docs/release-policy.md",))
    frontier("tabularium")

    full_ledgers = tuple(sorted(path for name, path in evolution.items() if name != "kronos"))
    kronos_currency = (
        "plugins/hexaemeron/skills/fiat/references/plugin-currency.md",
    )
    open_full = (
        "alexandria", "anamnesis", "berean", "brevitas", "hermes", "ephoros",
        "fiat", "hypomnema", "imprimatur", "metron", "vulgate", "homologia",
        "horos", "janus", "lazarus", "lemma", "pandects", "probitas",
        "sapheneia", "synkrisis", "tabularium",
    )
    phase_scope = ("protasis", "phylax", "ephoros", "metron", "elenchus", "hypomnema")

    def kronos(scope: str, targets: tuple[str, ...], ledgers: tuple[str, ...]) -> None:
        common = (evolution["kronos"],) + ledgers
        add("kronos", f"{scope}__rank-only", f"{scope} rank-only pass", common)
        for target in targets:
            add(
                "kronos",
                f"{scope}__dispatch-{target}",
                f"{scope} rank plus one target dispatch",
                common
                + kronos_currency
                + (ORACLE_SKILL_PATHS["fiat"], ORACLE_SKILL_PATHS[target]),
            )

    kronos("full", open_full, full_ledgers)
    kronos(
        "phase",
        ("ephoros", "metron", "hypomnema"),
        tuple(evolution[name] for name in phase_scope),
    )

    phylax_states = {
        "none": (),
        "phylax": (ORACLE_SKILL_PATHS["phylax"],),
        "phylax-proxy": (ORACLE_SKILL_PATHS["phylax"], "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md"),
        "ephoros-phylax": (ORACLE_SKILL_PATHS["ephoros"], ORACLE_SKILL_PATHS["phylax"]),
        "ephoros-phylax-proxy": (ORACLE_SKILL_PATHS["ephoros"], ORACLE_SKILL_PATHS["phylax"], "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md"),
    }
    metron_states = {
        "none": (),
        "metron": (ORACLE_SKILL_PATHS["metron"],),
        "metron-budget": (ORACLE_SKILL_PATHS["metron"], "plugins/hexaemeron/skills/metron/references/budget-check.md"),
    }
    elenchus_states = {
        "none": (),
        "elenchus": (ORACLE_SKILL_PATHS["elenchus"],),
        "elenchus-contract": (ORACLE_SKILL_PATHS["elenchus"], ORACLE_SKILL_PATHS["fizz-sync"], promises),
    }
    hypomnema_states = {"none": (), "hypomnema": (ORACLE_SKILL_PATHS["hypomnema"],)}
    hermes_states = {"none": (), "hermes": (ORACLE_SKILL_PATHS["hermes"],) + hermes_runtime}
    for worker, phylax, metron, elenchus, hypomnema, hermes in itertools.product(
        ("inline", "mason"), phylax_states, metron_states, elenchus_states, hypomnema_states, hermes_states
    ):
        documents = (
            (ORACLE_SKILL_PATHS["protasis"],)
            + phylax_states[phylax]
            + metron_states[metron]
            + elenchus_states[elenchus]
            + hypomnema_states[hypomnema]
            + hermes_states[hermes]
        )
        workers: tuple[str, ...] = ()
        if worker == "mason":
            workers = ("plugins/hexaemeron/agents/mason.md",)
            documents += workers
        add(
            "fiat",
            f"implement__{worker}__{phylax}__{metron}__{elenchus}__{hypomnema}__{hermes}",
            "implement directive",
            documents,
            workers,
        )

    audit_loop = "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
    sapheneia = ORACLE_SKILL_PATHS["sapheneia"]
    for worker, phylax, fix in itertools.product(
        ("inline", "warden"), ("phylax", "phylax-proxy"), ("none", "elenchus")
    ):
        documents = (
            audit_loop,
            sapheneia,
            ORACLE_SKILL_PATHS["phylax"],
            ORACLE_SKILL_PATHS["ephoros"],
            ORACLE_SKILL_PATHS["hypomnema"],
        )
        if phylax == "phylax-proxy":
            documents += ("plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",)
        if fix == "elenchus":
            documents += (ORACLE_SKILL_PATHS["elenchus"],)
        workers = ()
        if worker == "warden":
            workers = ("plugins/hexaemeron/agents/warden.md",)
            documents += workers
        add("fiat", f"audit-nonsol__{worker}__{phylax}__fix-{fix}", "non-Solidity audit round", documents, workers)

    sol_full = (ORACLE_SKILL_PATHS["solidity-auditor"], sol_aud_version, promises) + sol_general + sol_shared + sol_agents
    fizz_audit = {
        "absent": (),
        "later-campaign": (ORACLE_SKILL_PATHS["fizz"], promises),
        "full-generation": (ORACLE_SKILL_PATHS["fizz"], promises) + fizz_common + fizz_report + fizz_invariant,
    }
    for worker, fizz_state, fix in itertools.product(
        ("inline", "warden"), fizz_audit, ("none", "elenchus", "elenchus-contract")
    ):
        documents = (audit_loop, "plugins/hexaemeron/skills/fiat/references/xray-reuse.md", sapheneia) + xray_full + sol_full + fizz_audit[fizz_state]
        if fix == "elenchus":
            documents += (ORACLE_SKILL_PATHS["elenchus"],)
        elif fix == "elenchus-contract":
            documents += (ORACLE_SKILL_PATHS["elenchus"], ORACLE_SKILL_PATHS["fizz-sync"], promises)
        workers = sol_agents
        if fizz_state == "full-generation":
            workers += fizz_report + tuple(path for path in fizz_invariant if "/agents/" in path)
        if worker == "warden":
            workers += ("plugins/hexaemeron/agents/warden.md",)
            documents += ("plugins/hexaemeron/agents/warden.md",)
        add("fiat", f"audit-solidity__{worker}__fizz-{fizz_state}__fix-{fix}", "Solidity audit round", documents, workers)

    prose_base = (
        "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
        ORACLE_SKILL_PATHS["hypomnema"],
        ORACLE_SKILL_PATHS["imprimatur"],
        *lexicons,
        ORACLE_SKILL_PATHS["vulgate"],
    )
    for worker, brevitas, task_issue, last_step in itertools.product(
        ("inline", "scribe"), (False, True), (False, True), (False, True)
    ):
        documents = prose_base
        workers = ()
        if worker == "scribe":
            workers = ("plugins/hexaemeron/agents/scribe.md",)
            documents += workers
        if brevitas:
            documents += (ORACLE_SKILL_PATHS["brevitas"],)
        if task_issue:
            documents += (sapheneia,)
        if last_step:
            documents += ("plugins/hexaemeron/skills/fiat/references/push-discipline.md",)
        add("fiat", f"prose__{worker}__brevitas-{int(brevitas)}__issue-{int(task_issue)}__last-{int(last_step)}", "prose directive", documents, workers)

    for worker in ("inline", "surveyor"):
        documents = (ORACLE_SKILL_PATHS["protasis"],) + disciplines + (ORACLE_SKILL_PATHS["imprimatur"],) + lexicons
        workers = ()
        if worker == "surveyor":
            workers = ("plugins/hexaemeron/agents/surveyor.md",)
            documents += workers
        add("fiat", f"study__{worker}", "study directive", documents, workers)

    fiat_other = {
        "controller-basic": (),
        "frontier-gate": (evolution["fiat"], versioning),
        "marketplace-day1": ("plugins/hexaemeron/skills/fiat/references/wildcat-marketplace.md",),
        "marketplace-post-spec": ("plugins/hexaemeron/skills/fiat/references/wildcat-marketplace.md", "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"),
        "currency-remediation": ("plugins/hexaemeron/skills/fiat/references/plugin-currency.md",),
        "checkpoint-transfer": ("plugins/hexaemeron/skills/fiat/references/push-discipline.md", "plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md"),
        "observation-receipt": ("docs/fiat-run-observation-binding-v1.md",),
        "runbook": (ORACLE_SKILL_PATHS["protasis"], ORACLE_SKILL_PATHS["imprimatur"], *lexicons),
        "close-audit": (audit_loop,),
        "delivery": ("plugins/hexaemeron/skills/fiat/references/push-discipline.md",),
        "integrate-task-issue": ("plugins/hexaemeron/skills/fiat/references/push-discipline.md", sapheneia, ORACLE_SKILL_PATHS["imprimatur"], *lexicons, ORACLE_SKILL_PATHS["vulgate"]),
    }
    for local_id, documents in fiat_other.items():
        add("fiat", local_id, "bounded controller operation", documents)

    return sorted(rows, key=lambda row: row["id"])


def oracle_validate_profiles_and_routes(record: dict, graph: dict) -> None:
    """Check profiles, frozen spans, and 5N reachability without production helpers."""
    expected = oracle_profiles()
    observed = record.get("profiles")
    if not isinstance(observed, list):
        raise TypeError("oracle profile ledger is not an array")
    stripped = [
        {key: value for key, value in row.items() if key != "source_evidence"}
        for row in observed
    ]
    if stripped != expected:
        raise AssertionError("independent profile grammar mismatch")

    expected_counts = {
        skill: sum(row["selected_skill"] == skill for row in expected)
        for skill in sorted(ORACLE_SKILL_PATHS)
    }
    count = len(expected)
    expected_totals = {
        "normalized_profiles": count,
        "repository_roots": count * 2,
        "agent_skills_roots": count * 2,
        "standalone_roots": count,
        "scenario_roots": count * 5,
    }
    if record.get("counts") != expected_counts or record.get("totals") != expected_totals:
        raise AssertionError("independent profile denominator mismatch")

    semantic_counts = {name: 0 for name in ORACLE_PROFILE_EVIDENCE_COUNTS}
    for row in observed:
        row_counts = oracle_validate_semantic_anchors(row)
        for name, count_for_row in row_counts.items():
            semantic_counts[name] += count_for_row
    if semantic_counts != ORACLE_PROFILE_EVIDENCE_COUNTS or sum(
        semantic_counts.values()
    ) != sum(len(row["required_documents"]) for row in observed):
        raise AssertionError("independent semantic evidence denominator mismatch")

    evidence_projection = [
        {"id": row["id"], "source_evidence": row["source_evidence"]}
        for row in observed
    ]
    if hashlib.sha256(canonical(evidence_projection)).hexdigest() != ORACLE_EVIDENCE_PROJECTION_SHA256:
        raise AssertionError("independent obligation evidence projection mismatch")
    for row in observed:
        evidence_rows = row["source_evidence"]
        if [item.get("obligation") for item in evidence_rows] != row["required_documents"]:
            raise AssertionError(f"independent obligation coverage mismatch: {row['id']}")
        for evidence in evidence_rows:
            if set(evidence) != {
                "obligation", "path", "start", "end", "source_sha256", "span_sha256"
            }:
                raise AssertionError("independent evidence field mismatch")
            data = oracle_source(evidence["path"])
            start = evidence["start"]
            end = evidence["end"]
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start < 0
                or end <= start
                or end > len(data)
                or hashlib.sha256(data).hexdigest() != evidence["source_sha256"]
                or hashlib.sha256(data[start:end]).hexdigest() != evidence["span_sha256"]
            ):
                raise AssertionError(f"independent frozen span mismatch: {row['id']}")

    expected_roots: dict[str, dict] = {}
    profiles = {row["id"]: row for row in observed}
    for row in observed:
        skill = row["selected_skill"]
        plugin = ORACLE_SKILL_PATHS[skill].split("/")[1]
        for route, credentials in (
            ("repository", ("absent", "github-contributor")),
            ("agent-skills", ("absent", "github-contributor")),
            ("standalone", ("absent",)),
        ):
            base = (
                f"standalone:{plugin}:skill:{skill}"
                if route == "standalone"
                else f"{route}:skill:{skill}"
            )
            node = {
                "repository": "AGENTS.md",
                "agent-skills": ".agents/skills/promise-machine/SKILL.md",
                "standalone": f"plugins/{plugin}/AGENTS.md",
            }[route]
            for credential in credentials:
                identifier = f"{base}:profile:{row['id']}:credential:{credential}"
                conditions = [f"profile:{row['id']}"]
                if credential == "github-contributor":
                    conditions.append("credential:github-contributor")
                expected_roots[identifier] = {
                    "node": node,
                    "base_scenario": base,
                    "route": route,
                    "selected_skill": skill,
                    "profile_id": row["id"],
                    "credential": credential,
                    "conditions": sorted(conditions),
                }
    roots = {row["id"]: row for row in graph.get("scenario_roots", [])}
    if set(roots) != set(expected_roots):
        raise AssertionError("independent 5N route identity mismatch")
    for identifier, expected_root in expected_roots.items():
        root = roots[identifier]
        for field, value in expected_root.items():
            if root.get(field) != value:
                raise AssertionError(f"independent route binding mismatch: {identifier}")

    adjacency: dict[str, dict[str, set[str]]] = {
        identifier: {} for identifier in roots
    }
    for edge in graph.get("scenario_edges", []):
        for identifier in edge.get("active_scenarios", []):
            if identifier not in adjacency:
                raise AssertionError("independent edge scope escapes 5N roots")
            adjacency[identifier].setdefault(edge["source"], set()).add(edge["target"])
    for identifier, root in roots.items():
        profile = profiles[root["profile_id"]]
        skill = profile["selected_skill"]
        plugin = ORACLE_SKILL_PATHS[skill].split("/")[1]
        selected = ORACLE_SKILL_PATHS[skill]
        expected_documents = set(profile["required_documents"])
        expected_documents.update(
            {f"plugins/{plugin}/AGENTS.md", f"plugins/{plugin}/PROMISE_MACHINE.md", selected}
        )
        if root["route"] == "repository":
            expected_documents.update(
                {"AGENTS.md", "SHOGGOTH.md", "PROMISE_MACHINE.md", ".agents/skills/promise-machine/SKILL.md"}
            )
        elif root["route"] == "agent-skills":
            expected_documents.update(
                {
                    "AGENTS.md", "SHOGGOTH.md", "PROMISE_MACHINE.md",
                    ".agents/skills/promise-machine/SKILL.md",
                    ".agents/skills/promise-machine/PORTABLE.md",
                }
            )
        if root["credential"] == "github-contributor":
            expected_documents.add("CONTRIBUTORS.md")
        pending = [root["node"]]
        reached: set[str] = set()
        while pending:
            node = pending.pop()
            if node in reached:
                continue
            reached.add(node)
            pending.extend(adjacency[identifier].get(node, ()))
        if reached != expected_documents:
            raise AssertionError(f"independent route union mismatch: {identifier}")
    oracle_validate_runtime_edges(record, graph)


def command(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


class CorpusManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)

    def test_exact_inventory_and_denominators(self):
        self.assertEqual(self.manifest["counts"], AI.EXPECTED_COUNTS)
        self.assertEqual(self.manifest["totals"], AI.EXPECTED_TOTALS)
        paths = [item["path"] for item in self.manifest["documents"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))

    def test_shallow_checkout_rebuilds_from_inventory_bound_sources(self):
        if not hasattr(AI, "_source_mode"):
            self.skipTest("the parent has no inventory-bound source mode")
        clear_source_cache()
        try:
            with mock.patch.object(AI, "_source_mode", return_value="inventory"):
                rebuilt = AI.build_manifest(AI.build_invocation_profiles())
            self.assertEqual(rebuilt, self.manifest)
        finally:
            clear_source_cache()

    def test_shallow_checkout_refuses_source_drift(self):
        if not hasattr(AI, "_inventory_source_snapshot"):
            self.skipTest("the parent has no inventory-bound source snapshot")
        clear_source_cache()
        original_read = AI._read_regular

        def changed_source(path: Path, limit: int) -> bytes:
            data = original_read(path, limit)
            if path == ROOT / "AGENTS.md":
                return data + b"\n"
            return data

        try:
            with (
                mock.patch.object(AI, "_source_mode", return_value="inventory"),
                mock.patch.object(AI, "_read_regular", side_effect=changed_source),
                self.assertRaisesRegex(AI.Refusal, "inventory snapshot source drift"),
            ):
                AI._source_blob("AGENTS.md")
        finally:
            clear_source_cache()

    def test_shallow_checkout_does_not_hide_source_probe_failure(self):
        if not hasattr(AI, "_source_mode"):
            self.skipTest("the parent has no inventory-bound source mode")

        def failed_probe(arguments, limit=AI.MAX_GIT_OUTPUT, **kwargs):
            if arguments[0] == "cat-file":
                raise AI.Refusal("bounded Git read timed out")
            if arguments == ["rev-parse", "--is-shallow-repository"]:
                return b"true\n"
            raise AssertionError(f"unexpected Git probe: {arguments}")

        clear_source_cache()
        try:
            with (
                mock.patch.object(AI, "_git", side_effect=failed_probe),
                self.assertRaisesRegex(AI.Refusal, "bounded Git read timed out"),
            ):
                AI._source_mode()
        finally:
            clear_source_cache()

    def test_independent_shallow_oracle_does_not_hide_source_probe_failure(self):
        def failed_probe(*arguments, **kwargs):
            if arguments[0] == "cat-file":
                return subprocess.CompletedProcess(arguments, 128, b"", b"failed")
            if arguments == ("rev-parse", "--is-shallow-repository"):
                return subprocess.CompletedProcess(arguments, 0, b"true\n", b"")
            raise AssertionError(f"unexpected Git probe: {arguments}")

        clear_source_cache()
        try:
            with (
                mock.patch.object(
                    sys.modules[__name__], "oracle_git", side_effect=failed_probe
                ),
                self.assertRaisesRegex(
                    AssertionError, "independent oracle source probe failed"
                ),
            ):
                oracle_source_mode()
        finally:
            clear_source_cache()

    def test_manifest_source_topology_runtime_contract_is_closed(self):
        mutations = {
            "missing": lambda source: source.pop("repository_paths"),
            "extra": lambda source: source.__setitem__("extra", True),
            "duplicate": lambda source: source["repository_paths"].append(
                source["repository_paths"][0]
            ),
            "over-cap": lambda source: source.__setitem__(
                "repository_paths",
                [f"synthetic/{index:05d}" for index in range(10_001)],
            ),
        }
        for label, mutate in mutations.items():
            changed = copy.deepcopy(self.manifest)
            mutate(changed["source"])
            with self.subTest(label=label):
                with self.assertRaisesRegex(
                    AI.Refusal, "manifest source.*(field set|malformed)"
                ):
                    AI._validate_manifest_shape(changed)

        changed = copy.deepcopy(self.manifest)
        changed["source"]["repository_paths"] = changed["source"][
            "repository_paths"
        ][:-1]
        with self.assertRaisesRegex(AI.Refusal, "manifest source topology drift"):
            AI._validate_manifest_shape(changed)

    def test_manifest_validator_refuses_derivation_drift_without_command_rebuild(self):
        mutations = {
            "document-bytes": lambda value: value["documents"][0].__setitem__(
                "bytes", 1
            ),
            "document-sha256": lambda value: value["documents"][0].__setitem__(
                "sha256", "0" * 64
            ),
            "class-count": lambda value: value["counts"].__setitem__(
                "skill_contract", 0
            ),
            "physical-total": lambda value: value["totals"].__setitem__(
                "physical_bytes", 1
            ),
            "missing-ordinary-document": lambda value: value["documents"].pop(
                next(
                    index
                    for index, item in enumerate(value["documents"])
                    if item["source_evidence"] is None
                    and item["runtime_evidence"] is None
                )
            ),
            "host-reachability": lambda value: value["documents"][0].__setitem__(
                "loader_roots", ["repository"]
            ),
            "scenario-reachability": lambda value: value["documents"][0].__setitem__(
                "scenario_reachability",
                [
                    value["documents"][0]["scenario_reachability"][0].replace(
                        "agent-skills:", "repository:", 1
                    )
                ],
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.manifest)
                mutate(changed)
                with self.assertRaisesRegex(
                    AI.Refusal, "manifest differs from its source-bound derivation"
                ):
                    AI._validate_manifest_shape(changed)

    def test_independent_oracle_tree_paths_share_the_anchored_snapshot(self):
        clear_source_cache()
        changed = copy.deepcopy(self.manifest)
        unbound = "zz-unbound-topology.md"
        changed["source"]["repository_paths"] = sorted(
            [*changed["source"]["repository_paths"], unbound]
        )
        try:
            with mock.patch.object(
                sys.modules[__name__], "oracle_source_mode", return_value="inventory"
            ):
                oracle_inventory_snapshot()
                with mock.patch.object(
                    sys.modules[__name__], "load", return_value=changed
                ):
                    paths = oracle_tree_paths()
            self.assertNotIn(unbound, paths)
        finally:
            clear_source_cache()

    def test_independent_inventory_refuses_oversized_input_before_digest(self):
        with scratch_directory("oversized-oracle-inventory-") as temporary:
            oversized = Path(temporary) / "artifact-inventory.json"
            oversized.write_bytes(b" " * (8 * 1024 * 1024 + 1))
            clear_source_cache()
            try:
                with (
                    mock.patch.object(
                        sys.modules[__name__], "INVENTORY", oversized
                    ),
                    self.assertRaisesRegex(
                        AssertionError, "independent input exceeds byte limit"
                    ),
                ):
                    oracle_inventory_snapshot()
            finally:
                clear_source_cache()

    def test_independent_inventory_refuses_symlink_substitution(self):
        with scratch_directory("symlinked-oracle-inventory-") as temporary:
            symlink = Path(temporary) / "artifact-inventory.json"
            symlink.symlink_to(INVENTORY)
            clear_source_cache()
            try:
                with (
                    mock.patch.object(sys.modules[__name__], "INVENTORY", symlink),
                    self.assertRaisesRegex(
                        AssertionError, "independent input is unavailable or unsafe"
                    ),
                ):
                    oracle_inventory_snapshot()
            finally:
                clear_source_cache()

    def test_depth_one_checkout_replays_the_frozen_source(self):
        with scratch_directory("depth-one-checkout-") as temporary:
            checkout = Path(temporary) / "checkout"
            head = subprocess.run(
                ["/usr/bin/git", "-C", str(ROOT), "rev-parse", "HEAD"],
                capture_output=True,
                check=True,
                text=True,
                timeout=20,
            ).stdout.strip()
            subprocess.run(
                ["/usr/bin/git", "init", "--quiet", str(checkout)],
                capture_output=True,
                check=True,
                timeout=20,
            )
            subprocess.run(
                [
                    "/usr/bin/git",
                    "-C",
                    str(checkout),
                    "fetch",
                    "--quiet",
                    "--depth",
                    "1",
                    "--no-tags",
                    ROOT.as_uri(),
                    head,
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            subprocess.run(
                [
                    "/usr/bin/git",
                    "-C",
                    str(checkout),
                    "checkout",
                    "--quiet",
                    "--detach",
                    "FETCH_HEAD",
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            self.assertEqual(
                subprocess.run(
                    [
                        "/usr/bin/git",
                        "-C",
                        str(checkout),
                        "rev-parse",
                        "--is-shallow-repository",
                    ],
                    capture_output=True,
                    check=True,
                    timeout=20,
                ).stdout,
                b"true\n",
            )
            verify = subprocess.run(
                [
                    sys.executable,
                    str(checkout / "research/instruction-architecture/benchmark.py"),
                    "verify-loader",
                    "--profiles",
                    str(checkout / "tests/fixtures/instruction-architecture/invocation-profiles.json"),
                    "--manifest",
                    str(checkout / "tests/fixtures/instruction-architecture/corpus-manifest.json"),
                    "--graph",
                    str(checkout / "tests/fixtures/instruction-architecture/loader-graph.json"),
                ],
                cwd=checkout,
                capture_output=True,
                text=True,
                check=False,
                timeout=90,
            )
            shallow_suite = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "tests.test_instruction_architecture.CorpusManifestTests.test_build_baseline_reproduces_all_committed_outputs",
                    "tests.test_instruction_architecture.CorpusManifestTests.test_independent_markdown_fixed_point_detects_an_unclassified_directive",
                    "tests.test_instruction_architecture.InvocationProfileTests.test_independent_source_owned_profile_and_route_oracle",
                    "tests.test_instruction_architecture.LoaderGraphTests.test_independent_runtime_semantic_evidence_coverage_is_closed",
                    "-v",
                ],
                cwd=checkout,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            self.assertEqual(
                (verify.returncode, shallow_suite.returncode),
                (0, 0),
                f"verify-loader:\n{verify.stderr}\nshallow suite:\n{shallow_suite.stderr}",
            )

    def test_source_directed_admission_is_exact_and_anchored(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        admissions = AI._additional_metadata()
        self.assertEqual(len(admissions), 70)
        self.assertEqual(
            {
                item["path"]
                for item in self.manifest["documents"]
                if item["admission_kind"] != "issue-census"
            },
            set(admissions)
            | set(AI._structured_metadata())
            | set(AI._fixed_agent_metadata()),
        )
        self.assertEqual(sum(documents[path]["bytes"] for path in admissions), 526_326)
        self.assertEqual(
            {
                class_name: sum(
                    1
                    for metadata in admissions.values()
                    if metadata["document_class"] == class_name
                )
                for class_name in sorted(
                    {metadata["document_class"] for metadata in admissions.values()}
                )
            },
            {
                "frontier_ledger": 26,
                "frontier_policy": 1,
                "identity_contract": 1,
                "identity_roster": 1,
                "operation_reference": 25,
                "overlay_contract": 1,
                "router_install_contract": 1,
                "worker_prompt": 14,
            },
        )
        for path, metadata in admissions.items():
            with self.subTest(path=path):
                self.assertEqual(
                    documents[path]["document_class"], metadata["document_class"]
                )
                evidence = AI._evidence(
                    metadata["source_path"], metadata["source_needle"]
                )
                self.assertGreater(evidence["end"], evidence["start"])

    def test_structured_reference_inventory_and_evidence_are_exact(self):
        documents = {
            item["path"]: item
            for item in self.manifest["documents"]
            if item["document_class"] == "structured_reference"
        }
        self.assertEqual(
            {
                path: (item["bytes"], item["sha256"])
                for path, item in documents.items()
            },
            EXPECTED_STRUCTURED_REFERENCES,
        )
        metadata = AI._structured_metadata()
        self.assertEqual(set(documents), set(metadata))
        self.assertEqual(sum(item["bytes"] for item in documents.values()), 218_576)
        for path, item in documents.items():
            with self.subTest(path=path):
                row = metadata[path]
                self.assertEqual(item["canonical_owner"], row["canonical_owner"])
                self.assertEqual(item["load_semantics"], row["load_semantics"])
                self.assertEqual(
                    item["source_evidence"],
                    AI._evidence(row["source_path"], row["source_needle"]),
                )
                if row["runtime_path"] is None:
                    self.assertIsNone(item["runtime_evidence"])
                    self.assertEqual(item["loader_roots"], [])
                    self.assertEqual(item["scenario_reachability"], [])
                else:
                    self.assertEqual(
                        item["runtime_evidence"],
                        AI._evidence(row["runtime_path"], row["runtime_needle"]),
                    )
                    self.assertTrue(item["loader_roots"])
                    self.assertTrue(item["scenario_reachability"])

    def manifest_source_rebinding_specimens(self):
        rows = [
            (index, item)
            for index, item in enumerate(self.manifest["documents"])
            if item["source_evidence"] is not None
        ]
        specimens = {}
        for index, item in rows:
            evidence_class = item["document_class"]
            if evidence_class in specimens:
                continue
            for _, donor in rows:
                if (
                    donor["document_class"] != evidence_class
                    and donor["path"] != item["path"]
                    and donor["source_evidence"]["path"]
                    != item["source_evidence"]["path"]
                    and donor["source_evidence"] != item["source_evidence"]
                ):
                    specimens[evidence_class] = (
                        index,
                        donor["path"],
                        copy.deepcopy(donor["source_evidence"]),
                    )
                    break
        self.assertEqual(
            set(specimens), set(ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS)
        )
        return specimens

    def test_independent_manifest_semantic_evidence_coverage_is_closed(self):
        oracle_validate_manifest_semantic_anchors(self.manifest)
        self.assertEqual(
            sum(
                item["source_evidence"] is not None
                for item in self.manifest["documents"]
            ),
            sum(ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS.values()),
        )
        self.assertEqual(
            sum(
                item["runtime_evidence"] is not None
                for item in self.manifest["documents"]
            ),
            sum(ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS.values()),
        )

    def test_manifest_validator_does_not_trust_structured_source_metadata(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["source_path"] = metadata[donor]["source_path"]
        metadata[target]["source_needle"] = metadata[donor]["source_needle"]
        changed = copy.deepcopy(self.manifest)
        by_path = {item["path"]: item for item in changed["documents"]}
        by_path[target]["source_evidence"] = copy.deepcopy(
            by_path[donor]["source_evidence"]
        )
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "manifest semantic source anchor drift"
            ):
                AI._validate_manifest_shape(changed)

    def test_manifest_validator_refuses_all_synchronised_runtime_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.manifest["documents"], "path"
        )
        original_metadata = AI._structured_metadata()
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                metadata = copy.deepcopy(original_metadata)
                metadata[target]["runtime_path"] = original_metadata[donor_target][
                    "runtime_path"
                ]
                metadata[target]["runtime_needle"] = original_metadata[donor_target][
                    "runtime_needle"
                ]
                changed = copy.deepcopy(self.manifest)
                changed["documents"][index]["runtime_evidence"] = donor_runtime
                with mock.patch.object(
                    AI, "_structured_metadata", return_value=metadata
                ):
                    with self.assertRaisesRegex(
                        AI.Refusal, "manifest semantic runtime anchor drift"
                    ):
                        AI._validate_manifest_shape(changed)

    def test_independent_manifest_oracle_refuses_cross_class_source_rebindings(self):
        for evidence_class, (index, donor_path, donor_evidence) in (
            self.manifest_source_rebinding_specimens().items()
        ):
            with self.subTest(evidence_class=evidence_class, donor=donor_path):
                changed = copy.deepcopy(self.manifest)
                changed["documents"][index]["source_evidence"] = donor_evidence
                with self.assertRaisesRegex(
                    AssertionError, "independent manifest source anchor mismatch"
                ):
                    oracle_validate_manifest_semantic_anchors(changed)

    def test_independent_manifest_oracle_refuses_all_runtime_target_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.manifest["documents"], "path"
        )
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.manifest)
                changed["documents"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AssertionError, "independent manifest runtime anchor mismatch"
                ):
                    oracle_validate_manifest_semantic_anchors(changed)

    def test_fixed_agent_inputs_are_exact_and_never_executable(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            ".python-version": (
                7,
                "3a55324cbeddc91df012407d051dad08c88624c95a82fbdb856728729fbd14ab",
            ),
            "plugins/hexaemeron/skills/x-ray/VERSION": (
                2,
                "53c234e5e8472b6ac51c1ae1cab3fe06fad053beb8ebfd8977b010655bfdd3c3",
            ),
            "plugins/hexaemeron/skills/solidity-auditor/VERSION": (
                2,
                "1121cfccd5913f0a63fec40a6ffd44ea64f9dc135c66634ba001d10bcf4302a2",
            ),
        }
        self.assertEqual(set(AI._fixed_agent_metadata()), set(expected))
        for path, (size, digest) in expected.items():
            with self.subTest(path=path):
                item = documents[path]
                metadata = AI._fixed_agent_metadata()[path]
                self.assertEqual((item["bytes"], item["sha256"]), (size, digest))
                self.assertEqual(item["document_class"], "fixed_input")
                self.assertEqual(item["load_semantics"], "agent-or-prompt")
                self.assertIsNone(item["runtime_evidence"])
                self.assertEqual(
                    item["source_evidence"],
                    AI._evidence(metadata["source_path"], metadata["source_needle"]),
                )
                self.assertTrue(item["loader_roots"])
                self.assertTrue(item["scenario_reachability"])

    def test_operation_reference_closure_and_anamnesis_anchor_are_independent(self):
        operations = {
            item["path"]
            for item in self.manifest["documents"]
            if item["document_class"] == "operation_reference"
        }
        self.assertEqual(operations, EXPECTED_OPERATION_REFERENCES)
        demo = next(
            item
            for item in self.manifest["documents"]
            if item["path"] == "plugins/anamnesis/docs/demo.md"
        )
        self.assertEqual(demo["bytes"], 2_605)
        self.assertEqual(
            demo["sha256"],
            "b523e14fc000502dfc4aafc8732a77091803ab25b7e9ab990ff234f9702673cb",
        )
        self.assertEqual(
            demo["canonical_owner"],
            "plugins/anamnesis/skills/anamnesis/SKILL.md",
        )
        evidence = AI._evidence(
            "plugins/anamnesis/skills/anamnesis/SKILL.md", "../../docs/demo.md"
        )
        self.assertEqual((evidence["start"], evidence["end"]), (7_636, 7_654))
        self.assertEqual(
            evidence["span_sha256"],
            "9dfc4f04bae4c35cad57e454454283642f1676e2bb1e75178e1d83da81b793bc",
        )

    def test_independent_markdown_fixed_point_detects_an_unclassified_directive(self):
        derived = AI._derive_operative_markdown_targets(self.manifest["documents"])
        manifest_paths = {item["path"] for item in self.manifest["documents"]}
        self.assertEqual(derived["occurrences"], 298)
        self.assertEqual(len(derived["targets"]), 112)
        self.assertEqual(len(derived["excluded"]), 127)
        self.assertIn("plugins/anamnesis/docs/demo.md", derived["targets"])
        self.assertFalse(set(derived["targets"]) - manifest_paths)

        without_demo = [
            item
            for item in self.manifest["documents"]
            if item["path"] != "plugins/anamnesis/docs/demo.md"
        ]
        second_pass = AI._derive_operative_markdown_targets(without_demo)
        self.assertIn(
            "plugins/anamnesis/docs/demo.md",
            set(second_pass["targets"]) - {item["path"] for item in without_demo},
        )

        source = "plugins/anamnesis/skills/anamnesis/SKILL.md"
        synthetic = {
            "plugins/anamnesis/docs/new-operation.md",
            "plugins/anamnesis/docs/new-runbook.md",
        }
        repurposed = "plugins/pandects/docs/catalogue.md"
        changed_source = AI._source_blob(source) + (
            b"\nRead [the new operation](../../docs/new-operation.md) before acting.\n"
            b"Read [the new runbook](../../docs/new-runbook.md) before acting.\n"
            b"Read [the catalogue](../../../pandects/docs/catalogue.md) before acting.\n"
        )
        changed = AI._derive_operative_markdown_targets(
            self.manifest["documents"],
            source_overrides={source: changed_source},
            tree_paths={*AI._frozen_tree_paths(), *synthetic},
        )
        self.assertLessEqual(
            synthetic | {repurposed}, set(changed["targets"]) - manifest_paths
        )
        self.assertFalse(
            any(
                item["target"] in synthetic | {repurposed}
                for item in changed["excluded"]
            )
        )

    def test_independent_fixed_point_deriver_is_required(self):
        self.assertTrue(
            callable(getattr(AI, "_derive_operative_markdown_targets", None))
        )

    def test_extension_agnostic_fixed_point_and_runtime_anchor_mutations(self):
        derived = AI._derive_corpus_fixed_point(self.manifest["documents"])
        self.assertEqual(
            set(derived["structured_targets"]), set(EXPECTED_STRUCTURED_REFERENCES)
        )
        mandatory = {
            path
            for path, row in AI._structured_metadata().items()
            if row["load_semantics"] == "mandatory-executable"
        }
        self.assertEqual(set(derived["mandatory_executable_targets"]), mandatory)

        synthetic = "plugins/hermes/skills/hermes/references/new-rules.data"
        decoys = {
            "plugins/hermes/skills/hermes/scripts/generated-rules.json",
            "plugins/hexaemeron/skills/fizz/templates/output.json",
            "plugins/hermes/tests/fixtures/rules.json",
            "plugins/synkrisis/examples/specimens/rules.json",
            "project-inputs/rules.json",
        }
        with_synthetic = AI._derive_corpus_fixed_point(
            self.manifest["documents"],
            tree_paths={*AI._frozen_tree_paths(), synthetic, *decoys},
        )
        self.assertIn(synthetic, with_synthetic["structured_targets"])
        self.assertFalse(decoys & set(with_synthetic["structured_targets"]))

        for path in sorted(mandatory):
            row = AI._structured_metadata()[path]
            runtime_path = row["runtime_path"]
            self.assertIsNotNone(runtime_path)
            runtime = AI._source_blob(runtime_path)
            needle = row["runtime_needle"].encode()
            self.assertIn(needle, runtime)
            changed = AI._derive_corpus_fixed_point(
                self.manifest["documents"],
                source_overrides={runtime_path: runtime.replace(needle, b"", 1)},
            )
            self.assertNotIn(path, changed["mandatory_executable_targets"])
            source_path = row["source_path"]
            source = AI._source_blob(source_path)
            source_needle = row["source_needle"].encode()
            self.assertIn(source_needle, source)
            changed = AI._derive_corpus_fixed_point(
                self.manifest["documents"],
                source_overrides={
                    source_path: source.replace(source_needle, b"", 1)
                },
            )
            self.assertNotIn(path, changed["mandatory_executable_targets"])

    def test_every_structured_input_omission_and_move_refuses(self):
        tree = set(AI._frozen_tree_paths())
        for path in sorted(EXPECTED_STRUCTURED_REFERENCES):
            changed = tuple(sorted(tree - {path}))
            with self.subTest(path=path):
                with mock.patch.object(AI, "_frozen_tree_paths", return_value=changed):
                    with self.assertRaisesRegex(
                        AI.Refusal, "structured reference missing|topology drift"
                    ):
                        AI._corpus_paths()
        lexicon = "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json"
        moved = "plugins/hexaemeron/skills/imprimatur/templates/hard.json"
        with mock.patch.object(
            AI,
            "_frozen_tree_paths",
            return_value=tuple(sorted((tree - {lexicon}) | {moved})),
        ):
            with self.assertRaisesRegex(AI.Refusal, "structured reference missing"):
                AI._corpus_paths()

    def test_reference_suffix_does_not_control_non_markdown_admission(self):
        original = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        renamed = original.removesuffix(".json") + ".bin"
        tree = (set(AI._frozen_tree_paths()) - {original}) | {renamed}
        changed = AI._derive_corpus_fixed_point(
            self.manifest["documents"], tree_paths=tree
        )
        self.assertNotIn(original, changed["structured_targets"])
        self.assertIn(renamed, changed["structured_targets"])

    def test_same_repository_url_requires_exact_repository_ref_and_path(self):
        self.assertEqual(
            AI._same_repository_markdown_url(AI.CONTRIBUTORS_CANONICAL_URL),
            "CONTRIBUTORS.md",
        )
        for changed in (
            AI.CONTRIBUTORS_CANONICAL_URL.replace("wildcat-finance", "attacker"),
            AI.CONTRIBUTORS_CANONICAL_URL.replace("/main/", "/other/"),
            AI.CONTRIBUTORS_CANONICAL_URL.replace(
                "CONTRIBUTORS.md", "contributors.md"
            ),
            f"{AI.CONTRIBUTORS_CANONICAL_URL}?raw=1",
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(AI._same_repository_markdown_url(changed))

    def test_exact_duplicate_group_is_only_promise_machine(self):
        groups: dict[str, list[dict]] = {}
        for item in self.manifest["documents"]:
            if item["exact_duplicate_group"] is not None:
                groups.setdefault(item["exact_duplicate_group"], []).append(item)
        self.assertEqual(len(groups), 1)
        members = next(iter(groups.values()))
        self.assertEqual(len(members), 18)
        self.assertEqual(
            {item["logical_document"] for item in members}, {"promise-machine/v1"}
        )
        self.assertTrue(
            all(
                item["canonical_content_path"] == "PROMISE_MACHINE.md"
                for item in members
            )
        )

    def test_manifest_rebuild_is_exact(self):
        self.assertEqual(self.manifest, AI.build_manifest(load(PROFILES)))
        first = command(
            "verify-corpus", "--profiles", str(PROFILES), "--manifest", str(MANIFEST)
        )
        second = command(
            "verify-corpus", "--profiles", str(PROFILES), "--manifest", str(MANIFEST)
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_artifact_inventory_binds_every_baseline_record(self):
        inventory = load(INVENTORY)
        expected = {
            "corpus-manifest.json",
            "invocation-profiles.json",
            "loader-graph.json",
            "byte-partition.json",
            "cohorts.json",
            "holdout-seal.json",
        }
        self.assertEqual(set(inventory["artifacts"]), expected)
        for name, record in inventory["artifacts"].items():
            path = FIXTURES / name
            self.assertEqual(
                record, {"bytes": path.stat().st_size, "sha256": sha256(path)}
            )
        reconciliation = ROOT / "docs/instruction-architecture/corpus-reconciliation.md"
        self.assertEqual(
            inventory["reconciliation"],
            {
                "bytes": reconciliation.stat().st_size,
                "sha256": sha256(reconciliation),
            },
        )

    def test_committed_reader_refuses_coherently_resealed_generation(self):
        original_read = AI._read_regular
        graph = load(GRAPH)
        graph["unbound_reseal"] = True
        graph_raw = canonical(graph)
        inventory = load(INVENTORY)
        inventory["artifacts"]["loader-graph.json"] = {
            "bytes": len(graph_raw),
            "sha256": hashlib.sha256(graph_raw).hexdigest(),
        }
        inventory_raw = canonical(inventory)

        def resealed_generation(path: Path, limit: int) -> bytes:
            if path == INVENTORY:
                return inventory_raw
            if path == GRAPH:
                return graph_raw
            return original_read(path, limit)

        with mock.patch.object(
            AI, "_read_regular", side_effect=resealed_generation
        ):
            with self.assertRaisesRegex(
                AI.Refusal, "artifact inventory differs from its frozen source anchor"
            ):
                AI._load_committed_baseline(
                    {"invocation-profiles.json": PROFILES}
                )

    def test_independent_oracle_refuses_coherently_resealed_generation(self):
        original_read = oracle_read_regular
        graph = load(GRAPH)
        graph["unbound_reseal"] = True
        graph_raw = canonical(graph)
        inventory = load(INVENTORY)
        inventory["artifacts"]["loader-graph.json"] = {
            "bytes": len(graph_raw),
            "sha256": hashlib.sha256(graph_raw).hexdigest(),
        }
        inventory_raw = canonical(inventory)

        def resealed_generation(path: Path, limit: int) -> bytes:
            if path == INVENTORY:
                return inventory_raw
            if path == GRAPH:
                return graph_raw
            return original_read(path, limit)

        clear_source_cache()
        try:
            with (
                mock.patch.object(
                    sys.modules[__name__],
                    "oracle_read_regular",
                    side_effect=resealed_generation,
                ),
                self.assertRaisesRegex(
                    AssertionError,
                    "independent inventory differs from its source anchor",
                ),
            ):
                oracle_inventory_sources()
        finally:
            clear_source_cache()

    def test_committed_reader_refuses_changed_unrequested_payload(self):
        original_read = AI._read_regular

        def changed_graph(path: Path, limit: int) -> bytes:
            raw = original_read(path, limit)
            return raw + b" " if path == GRAPH else raw

        with mock.patch.object(AI, "_read_regular", side_effect=changed_graph):
            with self.assertRaisesRegex(
                AI.Refusal, "artifact inventory identity mismatch: loader-graph.json"
            ):
                AI._load_committed_baseline(
                    {"invocation-profiles.json": PROFILES}
                )

    def test_committed_reader_refuses_inventory_swap_during_snapshot(self):
        original_read = AI._read_regular
        inventory_reads = 0

        def changed_inventory(path: Path, limit: int) -> bytes:
            nonlocal inventory_reads
            raw = original_read(path, limit)
            if path == INVENTORY:
                inventory_reads += 1
                if inventory_reads == 2:
                    return raw + b" "
            return raw

        with mock.patch.object(AI, "_read_regular", side_effect=changed_inventory):
            with self.assertRaisesRegex(
                AI.Refusal, "artifact inventory changed during generation read"
            ):
                AI._load_committed_baseline(
                    {"invocation-profiles.json": PROFILES}
                )

    def test_build_baseline_reproduces_all_committed_outputs(self):
        with scratch_directory("instruction-architecture-rebuild-") as inside:
            output = Path(inside) / "records"
            reconciliation = Path(inside) / "corpus-reconciliation.md"
            AI.build_baseline(
                mock.Mock(output=output, reconciliation=reconciliation)
            )
            for name in (*AI.BASELINE_RECORD_NAMES, "artifact-inventory.json"):
                self.assertEqual((output / name).read_bytes(), (FIXTURES / name).read_bytes())
            self.assertEqual(
                reconciliation.read_bytes(),
                (ROOT / "docs/instruction-architecture/corpus-reconciliation.md").read_bytes(),
            )

    def test_build_baseline_commits_all_eight_outputs_as_one_generation(self):
        profiles: dict = {}
        manifest = {
            "source": {"ref": AI.SOURCE_REF, "tree_sha256": "a" * 64},
            "totals": {},
        }
        graph = {"edges": []}
        partition: dict = {}
        cohorts = {"holdout": {"logical_skills": []}}
        seal: dict = {}
        new_records = dict(
            zip(
                AI.BASELINE_RECORD_NAMES,
                map(canonical, (manifest, profiles, graph, partition, cohorts, seal)),
            )
        )
        new_reconciliation = b"new reconciliation\n"

        def seed_old_generation(output: Path, reconciliation: Path) -> None:
            output.mkdir(parents=True)
            artifacts = {}
            for name in AI.BASELINE_RECORD_NAMES:
                raw = canonical({"generation": "old", "name": name})
                (output / name).write_bytes(raw)
                artifacts[name] = {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            old_reconciliation = b"old reconciliation\n"
            reconciliation.write_bytes(old_reconciliation)
            inventory = {
                "schema": f"{AI.SCHEMA_PREFIX}-artifact-inventory/v1",
                "source_ref": AI.SOURCE_REF,
                "source_tree_sha256": "a" * 64,
                "artifacts": artifacts,
                "reconciliation": {
                    "bytes": len(old_reconciliation),
                    "sha256": hashlib.sha256(old_reconciliation).hexdigest(),
                },
            }
            (output / "artifact-inventory.json").write_bytes(canonical(inventory))

        def independently_committed(
            output: Path, reconciliation: Path
        ) -> tuple[bool, str | None]:
            try:
                inventory = load(output / "artifact-inventory.json")
                if set(inventory) != {
                    "schema",
                    "source_ref",
                    "source_tree_sha256",
                    "artifacts",
                    "reconciliation",
                }:
                    return False, None
                if set(inventory["artifacts"]) != set(AI.BASELINE_RECORD_NAMES):
                    return False, None
                generations = set()
                for name, record in inventory["artifacts"].items():
                    raw = (output / name).read_bytes()
                    if record != {
                        "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }:
                        return False, None
                    value = json.loads(raw)
                    generations.add(value.get("generation", "new"))
                reconciliation_record = inventory["reconciliation"]
                raw = reconciliation.read_bytes()
                if {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                } != {
                    "bytes": reconciliation_record["bytes"],
                    "sha256": reconciliation_record["sha256"],
                }:
                    return False, None
                generations.add("old" if raw.startswith(b"old ") else "new")
                if len(generations) != 1:
                    return False, None
                return True, next(iter(generations))
            except (KeyError, OSError, TypeError, ValueError):
                return False, None

        derivations = (
            mock.patch.object(AI, "build_invocation_profiles", return_value=profiles),
            mock.patch.object(AI, "_validate_invocation_profiles"),
            mock.patch.object(AI, "build_manifest", return_value=manifest),
            mock.patch.object(AI, "build_loader_graph", return_value=graph),
            mock.patch.object(AI, "build_partition", return_value=partition),
            mock.patch.object(AI, "build_cohorts", return_value=cohorts),
            mock.patch.object(AI, "build_holdout_seal", return_value=seal),
            mock.patch.object(
                AI, "_reconciliation_markdown", return_value=new_reconciliation
            ),
        )
        with scratch_directory("instruction-architecture-transaction-") as inside:
            root = Path(inside)
            with (
                derivations[0],
                derivations[1],
                derivations[2],
                derivations[3],
                derivations[4],
                derivations[5],
                derivations[6],
                derivations[7],
            ):
                for boundary in range(1, 9):
                    output = root / f"records-{boundary}"
                    reconciliation = root / f"reconciliation-{boundary}.md"
                    seed_old_generation(output, reconciliation)
                    original_write = AI._atomic_write
                    calls = 0

                    def inject(path: Path, data: bytes) -> None:
                        nonlocal calls
                        calls += 1
                        if calls == boundary:
                            raise RuntimeError(f"injected refusal before write {boundary}")
                        original_write(path, data)

                    with mock.patch.object(AI, "_atomic_write", side_effect=inject):
                        with self.assertRaisesRegex(
                            RuntimeError, f"injected refusal before write {boundary}"
                        ):
                            AI.build_baseline(
                                mock.Mock(
                                    output=output,
                                    reconciliation=reconciliation,
                                )
                            )
                    accepted, generation = independently_committed(
                        output, reconciliation
                    )
                    self.assertFalse(
                        accepted and generation not in {"old", "new"},
                        f"mixed generation accepted after write boundary {boundary}",
                    )
                    self.assertEqual(
                        (accepted, generation),
                        (True, "old") if boundary == 1 else (False, None),
                    )

                output = root / "records-complete"
                reconciliation = root / "reconciliation-complete.md"
                seed_old_generation(output, reconciliation)
                writes = []
                original_write = AI._atomic_write

                def observe(path: Path, data: bytes) -> None:
                    writes.append(path.name)
                    original_write(path, data)

                with mock.patch.object(AI, "_atomic_write", side_effect=observe):
                    AI.build_baseline(
                        mock.Mock(output=output, reconciliation=reconciliation)
                    )
                self.assertEqual(len(writes), 8)
                self.assertEqual(writes[-1], "artifact-inventory.json")
                self.assertEqual(
                    {name: (output / name).read_bytes() for name in AI.BASELINE_RECORD_NAMES},
                    new_records,
                )
                self.assertEqual(reconciliation.read_bytes(), new_reconciliation)
                self.assertEqual(
                    independently_committed(output, reconciliation),
                    (True, "new"),
                )
                AI._load_committed_baseline(
                    {"invocation-profiles.json": output / "invocation-profiles.json"},
                    reconciliation,
                )

    def test_moved_runtime_and_fixtures_are_excluded(self):
        paths = [item["path"] for item in self.manifest["documents"]]
        self.assertFalse(
            any(path.startswith("distribution/skills-runtime/") for path in paths)
        )
        self.assertFalse(
            any("/fixtures/" in path or path.startswith("tests/") for path in paths)
        )

    def test_external_runtime_ownership_is_explicit(self):
        external = {
            item["path"]
            for item in self.manifest["documents"]
            if item["external_runtime_owner"] == "upstream-pashov"
        }
        self.assertTrue(any(path.endswith("/fizz/SKILL.md") for path in external))
        self.assertTrue(any(path.endswith("/x-ray/SKILL.md") for path in external))
        self.assertTrue(
            any(path.endswith("/solidity-auditor/SKILL.md") for path in external)
        )

    def test_changed_manifest_refuses(self):
        changed = copy.deepcopy(self.manifest)
        changed["totals"]["physical_bytes"] += 1
        self.assertNotEqual(changed, AI.build_manifest(load(PROFILES)))

    def test_live_source_drift_refuses(self):
        clear_source_cache()
        with (
            mock.patch.object(AI, "_source_object", return_value=b"the Git blob"),
            mock.patch.object(AI, "_read_regular", return_value=b"not the Git blob"),
        ):
            with self.assertRaisesRegex(AI.Refusal, "source drift"):
                AI._source_blob("AGENTS.md")
        clear_source_cache()

    def test_cached_git_object_never_skips_live_source_drift_check(self):
        clear_source_cache()
        self.addCleanup(clear_source_cache)
        with (
            mock.patch.object(AI, "_source_mode", return_value="git"),
            mock.patch.object(AI, "_git", return_value=b"pinned"),
            mock.patch.object(
                AI, "_read_regular", side_effect=[b"pinned", b"drifted"]
            ) as live_read,
        ):
            self.assertEqual(AI._source_blob("AGENTS.md"), b"pinned")
            with self.assertRaisesRegex(AI.Refusal, "source drift"):
                AI._source_blob("AGENTS.md")
            self.assertEqual(live_read.call_count, 2)

    def test_independent_oracle_cache_never_skips_live_source_drift_check(self):
        clear_source_cache()
        self.addCleanup(clear_source_cache)
        with (
            mock.patch.object(
                sys.modules[__name__], "oracle_source_mode", return_value="git"
            ),
            mock.patch.object(
                sys.modules[__name__],
                "oracle_git",
                return_value=mock.Mock(returncode=0, stdout=b"pinned"),
            ),
            mock.patch.object(
                sys.modules[__name__],
                "oracle_read_regular",
                side_effect=[b"pinned", b"drifted"],
            ) as live_read,
        ):
            self.assertEqual(oracle_source("AGENTS.md"), b"pinned")
            with self.assertRaisesRegex(
                AssertionError, "independent oracle observed source drift"
            ):
                oracle_source("AGENTS.md")
            self.assertEqual(live_read.call_count, 2)

    def test_git_output_limit_stops_producer_before_completion(self):
        with scratch_directory() as inside:
            root = Path(inside)
            binary = root / "bin"
            binary.mkdir()
            marker = root / "producer-finished"
            fake_git = binary / "git"
            producer = (
                "import os\n"
                "from pathlib import Path\n"
                "import time\n"
                "for _ in range(8):\n"
                "    os.write(1, b'x' * 512)\n"
                "    time.sleep(0.1)\n"
                f"Path({str(marker)!r}).write_text('done')\n"
            )
            fake_git.write_text(
                f"#!{sys.executable}\n"
                "import subprocess\n"
                "import sys\n"
                f"subprocess.Popen([sys.executable, '-c', {producer!r}])\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            environment = {
                "PATH": f"{binary}{os.pathsep}{os.environ.get('PATH', '')}"
            }
            with (
                mock.patch.object(
                    AI,
                    "_git_executable",
                    return_value=str(fake_git.resolve()),
                    create=True,
                ),
                mock.patch.dict(AI.os.environ, environment, clear=False),
            ):
                with self.assertRaisesRegex(AI.Refusal, "output exceeded"):
                    AI._git(["ignored"], limit=1_024)
            time.sleep(1)
            self.assertFalse(marker.exists())

    def test_git_child_is_absolute_closed_and_network_inert(self):
        with scratch_directory() as inside:
            fake_git = Path(inside) / "git"
            fake_git.write_text(
                f"#!{sys.executable}\n"
                "import json\n"
                "import os\n"
                "import sys\n"
                "print(json.dumps({'argv': sys.argv, 'env': dict(os.environ)}, sort_keys=True))\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            spawned: dict[str, str] = {}
            real_popen = AI.subprocess.Popen

            def capture_environment(*arguments, **keywords):
                spawned.update(keywords["env"])
                return real_popen(*arguments, **keywords)

            with (
                mock.patch.object(
                    AI,
                    "_git_executable",
                    return_value=str(fake_git.resolve()),
                    create=True,
                ),
                mock.patch.object(
                    AI.subprocess, "Popen", side_effect=capture_environment
                ),
                mock.patch.dict(
                    AI.os.environ,
                    {
                        "INSTRUCTION_ARCHITECTURE_SECRET": "do-not-copy",
                        "PATH": f"{inside}{os.pathsep}{os.environ.get('PATH', '')}",
                    },
                    clear=False,
                ),
            ):
                observed = json.loads(AI._git(["version"]))
        self.assertEqual(observed["argv"][0], str(fake_git.resolve()))
        self.assertIn("--no-lazy-fetch", observed["argv"])
        expected_environment = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
        self.assertEqual(spawned, expected_environment)
        self.assertEqual(
            {key: observed["env"].get(key) for key in expected_environment},
            expected_environment,
        )
        self.assertNotIn("INSTRUCTION_ARCHITECTURE_SECRET", observed["env"])
        self.assertNotIn("HOME", observed["env"])
        self.assertNotIn("PATH", observed["env"])

    def test_git_executable_ignores_ambient_path(self):
        with scratch_directory() as inside:
            fake_git = Path(inside) / "git"
            fake_git.write_text("not executable by the workbench\n", encoding="utf-8")
            fake_git.chmod(0o755)
            with mock.patch.dict(AI.os.environ, {"PATH": str(inside)}, clear=False):
                resolver = getattr(AI, "_git_executable", lambda: "git")
                executable = Path(resolver())
        self.assertTrue(executable.is_absolute())
        self.assertNotEqual(executable, fake_git)

    def test_nonzero_git_exit_never_signals_a_reaped_process_group(self):
        with mock.patch.object(AI.os, "killpg") as killpg:
            with self.assertRaisesRegex(AI.Refusal, "refused the source"):
                AI._git(["definitely-not-a-git-command"])
        killpg.assert_not_called()

    def test_git_replace_ref_cannot_pivot_the_source_object(self):
        with scratch_directory("instruction-architecture-git-") as inside:
            repository = Path(inside) / "repository"
            repository.mkdir()

            def git(*arguments: str) -> str:
                result = subprocess.run(
                    ["git", "-C", str(repository), *arguments],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "commit.gpgsign", "false")
            source = repository / "source.md"
            source.write_text("original\n", encoding="utf-8")
            git("add", "source.md")
            git("commit", "--quiet", "-m", "original")
            original = git("rev-parse", "HEAD")
            source.write_text("replacement\n", encoding="utf-8")
            git("commit", "--quiet", "-am", "replacement")
            replacement = git("rev-parse", "HEAD")
            git("replace", original, replacement)
            self.assertEqual(
                git("cat-file", "blob", f"{original}:source.md"), "replacement"
            )
            with mock.patch.object(AI, "ROOT", repository):
                self.assertEqual(
                    AI._git(["cat-file", "blob", f"{original}:source.md"]),
                    b"original\n",
                )

    def test_regular_read_refuses_parent_symlink_escape(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            outside_record = Path(outside) / "record.json"
            outside_record.write_text("{}\n", encoding="utf-8")
            escape = Path(inside) / "escape"
            escape.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(
                AI.Refusal, "outside repository|unavailable or unsafe"
            ):
                AI._read_regular(escape / "record.json", AI.MAX_JSON_BYTES)

    def test_regular_read_refuses_fifo_without_blocking(self):
        with scratch_directory("fifo-input-") as temporary:
            fifo = Path(temporary) / "record.json"
            os.mkfifo(fifo)
            probe = "\n".join(
                (
                    "from pathlib import Path",
                    "import sys",
                    "from tests.test_instruction_architecture import AI",
                    "try:",
                    "    AI._read_regular(Path(sys.argv[1]), AI.MAX_JSON_BYTES)",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO input was accepted')",
                )
            )
            process = subprocess.Popen(
                [sys.executable, "-c", probe, str(fifo)],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                self.fail("regular-file input open blocked on a FIFO")
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(
                stdout.strip(), "input is not a single-link regular file"
            )

    def _assert_fifo_output_probe(
        self, probe: str, target: Path, expected: str, blocked: str
    ) -> None:
        process = subprocess.Popen(
            [sys.executable, "-c", probe, str(target)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            self.fail(blocked)
        self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(stdout.strip(), expected)

    def test_atomic_write_refuses_fifo_stage_replacement_without_blocking(self):
        with scratch_directory("fifo-output-stage-") as temporary:
            target = Path(temporary) / "record.json"
            probe = "\n".join(
                (
                    "import os",
                    "from pathlib import Path",
                    "import sys",
                    "from unittest import mock",
                    "from tests.test_instruction_architecture import AI",
                    "target = Path(sys.argv[1])",
                    "real_open = os.open",
                    "real_unlink = os.unlink",
                    "real_mkfifo = os.mkfifo",
                    "swapped = False",
                    "def racing_open(path, flags, *args, **kwargs):",
                    "    global swapped",
                    "    if (not swapped and isinstance(path, str)",
                    "            and path.startswith('.record.json.')",
                    "            and not flags & os.O_WRONLY):",
                    "        swapped = True",
                    "        real_unlink(path, dir_fd=kwargs['dir_fd'])",
                    "        real_mkfifo(path, dir_fd=kwargs['dir_fd'])",
                    "    return real_open(path, flags, *args, **kwargs)",
                    "try:",
                    "    with mock.patch.object(AI.os, 'open', side_effect=racing_open):",
                    "        AI._atomic_write(target, b'{}\\n')",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO stage replacement was accepted')",
                )
            )
            self._assert_fifo_output_probe(
                probe,
                target,
                "output stage changed before publication",
                "output stage verification blocked on a FIFO replacement",
            )

    def test_atomic_write_refuses_fifo_published_replacement_without_blocking(self):
        with scratch_directory("fifo-published-output-") as temporary:
            target = Path(temporary) / "record.json"
            probe = "\n".join(
                (
                    "import os",
                    "from pathlib import Path",
                    "import sys",
                    "from unittest import mock",
                    "from tests.test_instruction_architecture import AI",
                    "target = Path(sys.argv[1])",
                    "real_replace = os.replace",
                    "real_unlink = os.unlink",
                    "real_mkfifo = os.mkfifo",
                    "def racing_replace(source, destination, *args, **kwargs):",
                    "    real_replace(source, destination, *args, **kwargs)",
                    "    real_unlink(destination, dir_fd=kwargs['dst_dir_fd'])",
                    "    real_mkfifo(destination, dir_fd=kwargs['dst_dir_fd'])",
                    "try:",
                    "    with mock.patch.object(AI.os, 'replace', side_effect=racing_replace):",
                    "        AI._atomic_write(target, b'{}\\n')",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO published replacement was accepted')",
                )
            )
            self._assert_fifo_output_probe(
                probe,
                target,
                "input is not a single-link regular file",
                "published output verification blocked on a FIFO replacement",
            )

    def test_fresh_named_identity_refuses_fifo_without_blocking(self):
        with scratch_directory("fifo-output-identity-") as temporary:
            target = Path(temporary) / "record.json"
            probe = "\n".join(
                (
                    "import os",
                    "from pathlib import Path",
                    "import sys",
                    "from tests.test_instruction_architecture import AI",
                    "target = Path(sys.argv[1])",
                    "target.write_bytes(b'{}\\n')",
                    "expected = target.stat()",
                    "relative = AI._repository_relative(target, 'output')",
                    "parent, _ = AI._open_parent(relative, create=False, label='output')",
                    "try:",
                    "    parent_identity = AI._directory_identity(os.fstat(parent))",
                    "finally:",
                    "    os.close(parent)",
                    "target.unlink()",
                    "os.mkfifo(target)",
                    "try:",
                    "    AI._fresh_named_identity(relative, parent_identity, expected)",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO identity replacement was accepted')",
                )
            )
            self._assert_fifo_output_probe(
                probe,
                target,
                "output changed during publication",
                "final output identity check blocked on a FIFO replacement",
            )

    def test_atomic_write_refuses_hardlinked_stage_before_publication(self):
        with scratch_directory("hardlinked-output-stage-") as temporary:
            target = Path(temporary) / "record.json"
            original_open = os.open
            original_fsync = os.fsync
            stage: tuple[str, int] | None = None
            linked = False

            def observe_open(path, flags, *arguments, **keywords):
                nonlocal stage
                descriptor = original_open(path, flags, *arguments, **keywords)
                if (
                    stage is None
                    and isinstance(path, str)
                    and path.startswith(".record.json.")
                    and flags & os.O_WRONLY
                ):
                    stage = (path, keywords["dir_fd"])
                return descriptor

            def racing_fsync(descriptor):
                nonlocal linked
                result = original_fsync(descriptor)
                if not linked and stage is not None:
                    linked = True
                    os.link(
                        stage[0],
                        ".retained-stage-link",
                        src_dir_fd=stage[1],
                        dst_dir_fd=stage[1],
                    )
                return result

            with (
                mock.patch.object(AI.os, "open", side_effect=observe_open),
                mock.patch.object(AI.os, "fsync", side_effect=racing_fsync),
                self.assertRaisesRegex(
                    AI.Refusal, "output stage is not a single-link regular file"
                ),
            ):
                AI._atomic_write(target, b"{}\n")
            self.assertFalse(target.exists())

    def test_atomic_write_refuses_same_bytes_stage_replacement(self):
        with scratch_directory("same-bytes-stage-replacement-") as temporary:
            target = Path(temporary) / "record.json"
            original_replace = os.replace

            def racing_replace(source, destination, *arguments, **keywords):
                os.unlink(source, dir_fd=keywords["src_dir_fd"])
                descriptor = os.open(
                    source,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=keywords["src_dir_fd"],
                )
                try:
                    os.write(descriptor, b"{}\n")
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                return original_replace(
                    source, destination, *arguments, **keywords
                )

            with (
                mock.patch.object(AI.os, "replace", side_effect=racing_replace),
                self.assertRaisesRegex(
                    AI.Refusal, "published output does not match the verified stage"
                ),
            ):
                AI._atomic_write(target, b"{}\n")

    def test_atomic_write_refuses_same_bytes_published_replacement(self):
        with scratch_directory("same-bytes-published-replacement-") as temporary:
            target = Path(temporary) / "record.json"
            original_replace = os.replace

            def racing_replace(source, destination, *arguments, **keywords):
                result = original_replace(
                    source, destination, *arguments, **keywords
                )
                os.unlink(destination, dir_fd=keywords["dst_dir_fd"])
                descriptor = os.open(
                    destination,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=keywords["dst_dir_fd"],
                )
                try:
                    os.write(descriptor, b"{}\n")
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                return result

            with (
                mock.patch.object(AI.os, "replace", side_effect=racing_replace),
                self.assertRaisesRegex(
                    AI.Refusal, "published output does not match the verified stage"
                ),
            ):
                AI._atomic_write(target, b"{}\n")

    def test_regular_read_refuses_concurrent_parent_swap(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            holder = Path(inside)
            outside = Path(outside)
            safe = holder / "safe"
            safe.mkdir()
            target = safe / "record.json"
            target.write_text("inside\n", encoding="utf-8")
            (outside / "record.json").write_text("outside\n", encoding="utf-8")
            original_open = os.open
            swapped = False

            def racing_open(path, flags, *arguments, **keywords):
                nonlocal swapped
                if not swapped and path == "record.json" and "dir_fd" in keywords:
                    swapped = True
                    safe.rename(holder / "safe-old")
                    safe.symlink_to(outside, target_is_directory=True)
                return original_open(path, flags, *arguments, **keywords)

            with mock.patch.object(AI.os, "open", side_effect=racing_open):
                with self.assertRaisesRegex(AI.Refusal, "parent|changed"):
                    AI._read_regular(target, AI.MAX_JSON_BYTES)

    def test_atomic_write_refuses_concurrent_parent_swap_without_escape(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            holder = Path(inside)
            outside = Path(outside)
            safe = holder / "safe"
            safe.mkdir()
            target = safe / "record.json"
            original_replace = os.replace
            swapped = False

            def racing_replace(source, destination, *arguments, **keywords):
                nonlocal swapped
                if not swapped:
                    swapped = True
                    safe.rename(holder / "safe-old")
                    safe.symlink_to(outside, target_is_directory=True)
                    if "src_dir_fd" not in keywords:
                        staged = holder / "safe-old" / Path(source).name
                        staged.rename(outside / Path(source).name)
                return original_replace(source, destination, *arguments, **keywords)

            with mock.patch.object(AI.os, "replace", side_effect=racing_replace):
                with self.assertRaisesRegex(
                    AI.Refusal, "parent|outside repository"
                ):
                    AI._atomic_write(target, b"bounded\n")
            self.assertFalse((outside / "record.json").exists())

    def test_json_depth_and_token_caps_refuse_before_decode(self):
        depth_ceiling = AI.MAX_JSON_DEPTH
        token_ceiling = AI.MAX_JSON_TOKENS
        with scratch_directory() as inside:
            deep = Path(inside) / "deep.json"
            deep.write_bytes(
                b"[" * (depth_ceiling + 1) + b"0" + b"]" * (depth_ceiling + 1)
            )
            with self.assertRaisesRegex(AI.Refusal, "JSON depth limit"):
                AI._load_record(deep)

            wide = Path(inside) / "wide.json"
            wide.write_bytes(
                b'{"items":[' + b"0," * (token_ceiling + 1) + b"0]}\n"
            )
            with self.assertRaisesRegex(AI.Refusal, "JSON token limit"):
                AI._load_record(wide)

    def test_oversized_json_integer_refuses_without_parser_exception(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(b'{"value":' + b"1" * 5_000 + b"}\n")
            try:
                AI._load_record(record)
            except Exception as exc:
                self.assertIsInstance(exc, AI.Refusal)
                self.assertRegex(str(exc), "number length limit|strict UTF-8 JSON")
            else:
                self.fail("oversized JSON integer was accepted")

    def test_integer_bound_does_not_depend_on_the_host_python_limit(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(b'{"value":' + b"1" * 5_000 + b"}\n")
            prior_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(0)
                with self.assertRaisesRegex(AI.Refusal, "number length limit"):
                    AI._load_record(record)
            finally:
                sys.set_int_max_str_digits(prior_limit)

    def test_integer_bound_remains_usable_at_the_lowest_host_limit(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(
                b'{"value":' + b"1" * AI.MAX_JSON_NUMBER_CHARS + b"}\n"
            )
            prior_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(sys.int_info.str_digits_check_threshold)
                value, _ = AI._load_record(record)
            finally:
                sys.set_int_max_str_digits(prior_limit)
            self.assertEqual(len(str(value["value"])), AI.MAX_JSON_NUMBER_CHARS)

    def test_non_scalar_json_refuses_without_encoder_exception(self):
        with scratch_directory() as inside:
            record = Path(inside) / "surrogate.json"
            record.write_bytes(b'{"value":"\\ud800"}\n')
            duplicate = Path(inside) / "duplicate-surrogate.json"
            duplicate.write_bytes(b'{"\\ud800":1,"\\ud800":2}\n')
            for specimen in (record, duplicate):
                with self.subTest(specimen=specimen.name):
                    try:
                        AI._load_record(specimen)
                    except AI.Refusal as exc:
                        self.assertTrue(str(exc).isascii())
                    except Exception as exc:
                        self.fail(f"unbounded parser exception: {type(exc).__name__}")
                    else:
                        self.fail("non-scalar JSON was accepted")

    def test_build_baseline_refuses_unowned_output_paths_before_derivation(self):
        manifest = {"source": {"tree_sha256": "0" * 64}, "totals": {}}
        graph = {"roots": [], "edges": []}
        cohorts = {"holdout": {"logical_skills": []}}
        for output, reconciliation in (
            (ROOT, None),
            (FIXTURES, ROOT / "AGENTS.md"),
            (FIXTURES, ROOT / ".git/config"),
        ):
            with self.subTest(output=output, reconciliation=reconciliation):
                arguments = mock.Mock(output=output, reconciliation=reconciliation)
                with (
                    mock.patch.object(AI, "build_manifest", return_value=manifest) as derive,
                    mock.patch.object(AI, "build_loader_graph", return_value=graph),
                    mock.patch.object(AI, "build_partition", return_value={}),
                    mock.patch.object(AI, "build_cohorts", return_value=cohorts),
                    mock.patch.object(AI, "build_holdout_seal", return_value={}),
                    mock.patch.object(AI, "_reconciliation_markdown", return_value=b""),
                    mock.patch.object(AI, "_atomic_write") as write,
                ):
                    try:
                        AI.build_baseline(arguments)
                    except AI.Refusal:
                        refused = True
                    else:
                        refused = False
                self.assertTrue(refused, "unowned output path was accepted")
                derive.assert_not_called()
                write.assert_not_called()

    def test_build_baseline_refuses_output_aliases_before_derivation(self):
        with scratch_directory("instruction-architecture-alias-") as inside:
            output = Path(inside) / "records"
            for reconciliation in (
                output,
                output / "corpus-manifest.json",
                output / "artifact-inventory.json",
                output / "corpus-manifest.json" / "nested.md",
            ):
                with self.subTest(reconciliation=reconciliation):
                    arguments = mock.Mock(
                        output=output,
                        reconciliation=reconciliation,
                    )
                    with mock.patch.object(AI, "build_manifest") as derive:
                        with self.assertRaisesRegex(AI.Refusal, "overlaps"):
                            AI.build_baseline(arguments)
                    derive.assert_not_called()

    def test_output_refuses_parent_symlink_escape_without_writing(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            escape = Path(inside) / "escape"
            escape.symlink_to(outside, target_is_directory=True)
            target = escape / "record.json"
            with self.assertRaisesRegex(
                AI.Refusal, "not a real directory|parent is unavailable or unsafe"
            ):
                AI._safe_output(target)
            self.assertFalse((Path(outside) / "record.json").exists())

    def test_schema_closes_every_object_definition(self):
        schema = load(SCHEMA)
        self.assertEqual(
            {item["$ref"] for item in schema["oneOf"]},
            {
                "#/$defs/artifactInventory",
                "#/$defs/cohorts",
                "#/$defs/holdoutSeal",
                "#/$defs/loaderGraph",
                "#/$defs/manifest",
                "#/$defs/partition",
            },
        )
        object_definitions = [
            value for value in schema["$defs"].values() if value.get("type") == "object"
        ]
        self.assertGreaterEqual(len(object_definitions), 15)
        self.assertTrue(
            all(
                value.get("additionalProperties") is False
                for value in object_definitions
            )
        )

    def test_runtime_and_schema_share_the_canonical_path_language(self):
        schema = load(SCHEMA)["$defs"]["path"]
        pattern = re.compile(schema["pattern"])

        def schema_accepts(value: str) -> bool:
            return (
                schema["minLength"] <= len(value) <= schema["maxLength"]
                and pattern.search(value) is not None
            )

        accepted = ("a", "a b", "a/b", "a" * 1_024)
        refused = (
            "",
            ".",
            "..",
            "a/.",
            "a/..",
            "a//b",
            "a/",
            "/a",
            "a\\b",
            "a\x00b",
            "a\x1fb",
            "a\n",
            "a\r",
            "a\x7fb",
            "é",
            "a" * 1_025,
        )
        for specimen in accepted:
            with self.subTest(accepted=repr(specimen[:32])):
                self.assertEqual(AI._safe_relative(specimen).as_posix(), specimen)
                self.assertTrue(schema_accepts(specimen))
        for specimen in refused:
            with self.subTest(refused=repr(specimen[:32])):
                with self.assertRaises(AI.Refusal):
                    AI._safe_relative(specimen)
                self.assertFalse(schema_accepts(specimen))

    def test_runtime_refuses_a_noncanonical_path_before_normalisation(self):
        with self.assertRaises(AI.Refusal):
            AI._safe_relative("a//b")

    def test_study_copy_changes_only_relative_link_depth(self):
        shipped = STUDY.read_bytes()
        self.assertEqual(shipped.count(b"](../../plugins/"), 10)
        receipted = shipped.replace(b"](../../plugins/", b"](../plugins/")
        self.assertEqual(hashlib.sha256(receipted).hexdigest(), RECEIPTED_STUDY_SHA256)
        self.assertEqual(sha256(RUNBOOK), AMENDED_RUNBOOK_SHA256)


class FollowOnAudit2ParentGuardTests(unittest.TestCase):
    """Guards that stay assertion-red on the exact follow-on-2 parent."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.graph = load(GRAPH)

    def test_source_owned_profile_product_replaces_singleton_witnesses(self):
        self.assertEqual(len(self.graph["scenario_roots"]), 2_595)
        self.assertTrue(
            self.graph["constraints"].get("invocation_profiles_are_source_owned")
        )
        self.assertTrue(
            self.graph["constraints"].get("profile_route_product_is_exact")
        )

    def test_local_version_files_are_fixed_read_only_agent_inputs(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            "plugins/hexaemeron/skills/solidity-auditor/VERSION",
            "plugins/hexaemeron/skills/x-ray/VERSION",
        }
        self.assertLessEqual(expected, set(documents))
        for path in expected:
            self.assertEqual(documents[path]["load_semantics"], "agent-or-prompt")
            incoming = [
                edge
                for edge in self.graph["scenario_edges"]
                if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(all(edge["kind"] == "fixed-agent-input" for edge in incoming))

    def test_human_reference_docs_have_no_production_reachability(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            "plugins/hexaemeron/skills/imprimatur/references/agent-replies.md",
            "plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md",
            "plugins/hexaemeron/skills/imprimatur/references/rewriting.md",
            "plugins/pandects/docs/applicability.md",
            "plugins/pandects/docs/writing-a-law.md",
            "plugins/pandects/integrations/wildcat/APPLICABILITY.md",
        }
        for path in expected:
            self.assertEqual(documents[path]["load_semantics"], "reference-only")
            self.assertEqual(documents[path]["loader_roots"], [])
            self.assertEqual(documents[path]["scenario_reachability"], [])


class FollowOnAudit6ParentGuardTests(unittest.TestCase):
    """Guards that stay assertion-red on exact parent 46572571528e."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)

    def test_profile_validator_rejects_a_valid_non_skill_span_rebinding(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            row for row in changed["profiles"] if row["id"] == "fiat:close-audit"
        )
        selected = next(
            row
            for row in profile["source_evidence"]
            if row["obligation"] == ORACLE_SKILL_PATHS["fiat"]
        )
        audit_loop = next(
            row
            for row in profile["source_evidence"]
            if row["obligation"]
            == "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
        )
        for key in ("path", "start", "end", "source_sha256", "span_sha256"):
            audit_loop[key] = selected[key]
        digest = hashlib.sha256(canonical(changed["profiles"])).hexdigest()
        changed["projection_sha256"] = digest
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
                AI._validate_invocation_profiles(changed)

    def test_manifest_validator_rejects_synchronised_source_metadata_drift(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["source_path"] = metadata[donor]["source_path"]
        metadata[target]["source_needle"] = metadata[donor]["source_needle"]
        changed = copy.deepcopy(self.manifest)
        by_path = {item["path"]: item for item in changed["documents"]}
        by_path[target]["source_evidence"] = copy.deepcopy(
            by_path[donor]["source_evidence"]
        )
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "manifest semantic source anchor drift"
            ):
                AI._validate_manifest_shape(changed)

    def test_graph_builder_rejects_synchronised_runtime_metadata_drift(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["runtime_path"] = metadata[donor]["runtime_path"]
        metadata[target]["runtime_needle"] = metadata[donor]["runtime_needle"]
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "scenario runtime semantic anchor drift"
            ):
                changed_manifest = AI.build_manifest(self.profiles)
                AI.build_loader_graph(changed_manifest, self.profiles)


class InvocationProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)

    def reseal(self, changed: dict) -> str:
        digest = hashlib.sha256(canonical(changed["profiles"])).hexdigest()
        changed["projection_sha256"] = digest
        return digest

    def validate_synchronized_production_projection(self, changed: dict) -> None:
        digest = self.reseal(changed)
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            AI._validate_invocation_profiles(changed)

    def test_profile_ledger_is_exact_and_source_owned(self):
        self.assertEqual(self.profiles, AI.build_invocation_profiles())
        AI._validate_invocation_profiles(self.profiles)
        self.assertEqual(
            self.profiles["projection_sha256"],
            "b09aeb1ba087dff0c34c3fad63a9096c4862aad71b14fe6c6a12a14819c94c07",
        )
        self.assertEqual(self.profiles["counts"], AI.EXPECTED_PROFILE_COUNTS)

    def test_independent_source_owned_profile_and_route_oracle(self):
        oracle_validate_profiles_and_routes(self.profiles, self.graph)

    def semantic_cross_class_rebinding_specimens(self):
        specimens = {}
        for profile_index, profile in enumerate(self.profiles["profiles"]):
            for evidence_index, evidence in enumerate(profile["source_evidence"]):
                evidence_class, _, _ = oracle_full_semantic_anchor(
                    profile, evidence["obligation"]
                )
                if evidence_class in specimens:
                    continue
                identity = {
                    key: evidence[key]
                    for key in ("path", "start", "end", "source_sha256", "span_sha256")
                }
                for donor_index, donor in enumerate(profile["source_evidence"]):
                    donor_class, _, _ = oracle_full_semantic_anchor(
                        profile, donor["obligation"]
                    )
                    donor_identity = {
                        key: donor[key]
                        for key in (
                            "path",
                            "start",
                            "end",
                            "source_sha256",
                            "span_sha256",
                        )
                    }
                    if (
                        donor_index != evidence_index
                        and donor_class != evidence_class
                        and donor["path"] != evidence["path"]
                        and donor_identity != identity
                    ):
                        specimens[evidence_class] = (
                            profile_index,
                            evidence_index,
                            donor_identity,
                        )
                        break
        self.assertEqual(set(specimens), set(ORACLE_PROFILE_EVIDENCE_COUNTS))
        return specimens

    def test_validator_refuses_valid_cross_class_cross_target_rebinding(self):
        for evidence_class, (
            profile_index,
            evidence_index,
            donor_identity,
        ) in self.semantic_cross_class_rebinding_specimens().items():
            with self.subTest(evidence_class=evidence_class):
                changed = copy.deepcopy(self.profiles)
                evidence = changed["profiles"][profile_index]["source_evidence"][
                    evidence_index
                ]
                evidence.update(donor_identity)
                digest = hashlib.sha256(canonical(changed["profiles"])).hexdigest()
                changed["projection_sha256"] = digest
                with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
                    with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
                        AI._validate_invocation_profiles(changed)

    def test_independent_oracle_refuses_cross_class_cross_target_rebinding(self):
        for evidence_class, (
            profile_index,
            evidence_index,
            donor_identity,
        ) in self.semantic_cross_class_rebinding_specimens().items():
            with self.subTest(evidence_class=evidence_class):
                profile = copy.deepcopy(self.profiles["profiles"][profile_index])
                profile["source_evidence"][evidence_index].update(donor_identity)
                with self.assertRaisesRegex(
                    AssertionError, "independent semantic anchor mismatch"
                ):
                    oracle_validate_semantic_anchors(profile)

    def test_independent_semantic_anchor_coverage_is_closed(self):
        observed = {name: 0 for name in ORACLE_PROFILE_EVIDENCE_COUNTS}
        required = 0
        evidence = 0
        for profile in self.profiles["profiles"]:
            counts = oracle_validate_semantic_anchors(profile)
            for name, count_for_profile in counts.items():
                observed[name] += count_for_profile
            required += len(profile["required_documents"])
            evidence += len(profile["source_evidence"])
        self.assertEqual(observed, ORACLE_PROFILE_EVIDENCE_COUNTS)
        self.assertEqual(required, 5_084)
        self.assertEqual(evidence, required)

    def test_every_required_document_has_one_named_source_witness(self):
        evidence_rows = 0
        required_documents = 0
        for profile in self.profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                obligations = [
                    evidence.get("obligation")
                    for evidence in profile["source_evidence"]
                ]
                self.assertEqual(obligations, profile["required_documents"])
                self.assertEqual(len(obligations), len(set(obligations)))
                evidence_rows += len(obligations)
                required_documents += len(profile["required_documents"])
        self.assertEqual(evidence_rows, 5_084)
        self.assertEqual(required_documents, 5_084)

    def test_every_skill_and_frontier_witness_is_semantically_attributable(self):
        checked = 0
        for profile in self.profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                oracle_validate_semantic_anchors(profile)
                checked += sum(
                    path.endswith(("/SKILL.md", "/EVOLUTION.md"))
                    for path in profile["required_documents"]
                )
        self.assertEqual(checked, 3_157)

    def test_profile_route_denominators_are_exact(self):
        self.assertEqual(
            self.profiles["totals"],
            {
                "normalized_profiles": 519,
                "repository_roots": 1_038,
                "agent_skills_roots": 1_038,
                "standalone_roots": 519,
                "scenario_roots": 2_595,
            },
        )
        self.assertEqual(len(self.graph["scenario_roots"]), 2_595)

    def test_fiat_phase_product_is_not_a_curated_edge_count(self):
        phases: dict[str, int] = {}
        for profile in self.profiles["profiles"]:
            if profile["selected_skill"] == "fiat":
                phases[profile["phase"]] = phases.get(profile["phase"], 0) + 1
        self.assertEqual(
            phases,
            {
                "implement directive": 360,
                "Solidity audit round": 18,
                "non-Solidity audit round": 8,
                "prose directive": 16,
                "study directive": 2,
                "bounded controller operation": 11,
            },
        )

    def test_kronos_dispatch_profiles_load_the_repin_boundary(self):
        currency = (
            "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"
        )
        source = ORACLE_SKILL_PATHS["kronos"]
        needle = (
            "`../fiat/references/plugin-currency.md` names the host\n"
            "   mechanism."
        )
        self.assertIn("and the Kronos re-pin boundary.", oracle_source(currency).decode())
        self.assertIn(needle, oracle_source(source).decode())

        kronos = [
            row
            for row in self.profiles["profiles"]
            if row["selected_skill"] == "kronos"
        ]
        dispatch = [row for row in kronos if "dispatch-" in row["id"]]
        rank_only = [row for row in kronos if "rank-only" in row["id"]]
        self.assertEqual((len(dispatch), len(rank_only)), (24, 2))
        expected_evidence = oracle_evidence(currency, source, needle)
        for profile in dispatch:
            with self.subTest(profile=profile["id"]):
                self.assertIn(currency, profile["required_documents"])
                evidence = {
                    row["obligation"]: row for row in profile["source_evidence"]
                }
                self.assertEqual(evidence[currency], expected_evidence)
        self.assertTrue(
            all(currency not in profile["required_documents"] for profile in rank_only)
        )

        currency_reach = {
            root
            for edge in self.graph["scenario_edges"]
            if edge["target"] == currency
            for root in edge["active_scenarios"]
        }
        dispatch_ids = {row["id"] for row in dispatch}
        rank_only_ids = {row["id"] for row in rank_only}
        dispatch_roots = {
            row["id"]
            for row in self.graph["scenario_roots"]
            if row["profile_id"] in dispatch_ids
        }
        rank_only_roots = {
            row["id"]
            for row in self.graph["scenario_roots"]
            if row["profile_id"] in rank_only_ids
        }
        self.assertEqual(len(dispatch_roots), 120)
        self.assertLessEqual(dispatch_roots, currency_reach)
        self.assertTrue(rank_only_roots.isdisjoint(currency_reach))

    def test_every_profile_document_union_and_worker_set_is_closed(self):
        for profile in self.profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                documents = profile["required_documents"]
                workers = profile["worker_prompts"]
                self.assertEqual(documents, sorted(set(documents)))
                self.assertEqual(workers, sorted(set(workers)))
                self.assertLessEqual(set(workers), set(documents))
                self.assertIn(
                    AI.SELECTABLE_SKILL_PATHS[profile["selected_skill"]], documents
                )

    def test_profile_schema_is_closed_at_every_object(self):
        schema = load(PROFILE_SCHEMA)
        self.assertFalse(schema["additionalProperties"])
        objects = [
            value
            for value in schema["$defs"].values()
            if value.get("type") == "object"
        ]
        self.assertGreaterEqual(len(objects), 5)
        self.assertTrue(all(value.get("additionalProperties") is False for value in objects))

    def test_verify_profiles_is_read_only_and_repeatable(self):
        first = command("verify-profiles", "--profiles", str(PROFILES))
        second = command("verify-profiles", "--profiles", str(PROFILES))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_projection_mutation_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["projection_sha256"] = "0" * 64
        with self.assertRaisesRegex(AI.Refusal, "projection digest"):
            AI._validate_invocation_profiles(changed)

    def test_one_profile_omission_refuses_even_when_totals_are_forged(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"].pop()
        with self.assertRaisesRegex(AI.Refusal, "denominator"):
            self.validate_synchronized_production_projection(changed)

    def test_duplicate_profile_id_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"][1]["id"] = changed["profiles"][0]["id"]
        with self.assertRaisesRegex(AI.Refusal, "id product"):
            self.validate_synchronized_production_projection(changed)

    def test_worker_outside_required_union_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(item for item in changed["profiles"] if item["worker_prompts"])
        profile["required_documents"].remove(profile["worker_prompts"][0])
        with self.assertRaisesRegex(AI.Refusal, "document or worker union"):
            self.validate_synchronized_production_projection(changed)

    def test_reference_only_document_in_profile_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = changed["profiles"][0]
        profile["required_documents"].append(sorted(AI.REFERENCE_ONLY_MARKDOWN)[0])
        profile["required_documents"].sort()
        with self.assertRaisesRegex(AI.Refusal, "human reference"):
            self.validate_synchronized_production_projection(changed)

    def test_fixed_input_execution_fiction_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item
            for item in changed["profiles"]
            if any(row["path"].endswith("/VERSION") for row in item["fixed_inputs"])
        )
        version = next(
            row for row in profile["fixed_inputs"] if row["path"].endswith("/VERSION")
        )
        version["load_semantics"] = "mandatory-executable"
        with self.assertRaisesRegex(AI.Refusal, "fixed input semantics"):
            self.validate_synchronized_production_projection(changed)

    def test_source_span_drift_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"][0]["source_evidence"][0]["span_sha256"] = "0" * 64
        with self.assertRaisesRegex(AI.Refusal, "source span"):
            self.validate_synchronized_production_projection(changed)

    def test_synchronized_obligation_fiction_refuses_both_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"] if item["id"] == "alexandria:ordinary"
        )
        invented = ORACLE_SKILL_PATHS["phylax"]
        profile["required_documents"].append(invented)
        profile["required_documents"].sort()
        evidence = copy.deepcopy(profile["source_evidence"][0])
        evidence["obligation"] = invented
        profile["source_evidence"].append(evidence)
        profile["source_evidence"].sort(key=lambda row: row["obligation"])

        with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "independent profile grammar"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_bare_basename_refuses_both_semantic_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"]
            if item["selected_skill"] == "fiat"
            and ORACLE_SKILL_PATHS["phylax"] in item["required_documents"]
        )
        obligation = ORACLE_SKILL_PATHS["phylax"]
        index = profile["required_documents"].index(obligation)
        profile["source_evidence"][index] = oracle_evidence(
            obligation, "plugins/hexaemeron/PROMISES.md", "SKILL.md"
        )

        with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "semantic anchor"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_first_occurrence_refuses_both_semantic_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"]
            if item["selected_skill"] == "fiat"
            and ORACLE_SKILL_PATHS["phylax"] in item["required_documents"]
        )
        obligation = ORACLE_SKILL_PATHS["phylax"]
        index = profile["required_documents"].index(obligation)
        profile["source_evidence"][index] = oracle_evidence(
            obligation, ORACLE_SKILL_PATHS["fiat"], "SKILL.md"
        )

        with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "semantic anchor"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_valid_span_rebinding_refuses_both_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"]
            if item["selected_skill"] == "fiat"
            and ORACLE_SKILL_PATHS["phylax"] in item["required_documents"]
            and ORACLE_SKILL_PATHS["ephoros"] in item["required_documents"]
        )
        obligation = ORACLE_SKILL_PATHS["phylax"]
        replacement = copy.deepcopy(
            next(
                row for row in profile["source_evidence"]
                if row["obligation"] == ORACLE_SKILL_PATHS["ephoros"]
            )
        )
        replacement["obligation"] = obligation
        index = profile["required_documents"].index(obligation)
        profile["source_evidence"][index] = replacement

        with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "semantic anchor"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_profile_and_routes_refuse_independent_oracle(self):
        changed_profiles = copy.deepcopy(self.profiles)
        changed_graph = copy.deepcopy(self.graph)
        old_profile_id = "alexandria:ordinary"
        new_profile_id = "alexandria:invented"
        profile = next(
            item
            for item in changed_profiles["profiles"]
            if item["id"] == old_profile_id
        )
        profile["id"] = new_profile_id

        root_ids: dict[str, str] = {}
        for root in changed_graph["scenario_roots"]:
            if root["profile_id"] != old_profile_id:
                continue
            old_root_id = root["id"]
            new_root_id = old_root_id.replace(
                f":profile:{old_profile_id}:",
                f":profile:{new_profile_id}:",
            )
            root_ids[old_root_id] = new_root_id
            root["id"] = new_root_id
            root["profile_id"] = new_profile_id
            root["conditions"] = [
                f"profile:{new_profile_id}"
                if condition == f"profile:{old_profile_id}"
                else condition
                for condition in root["conditions"]
            ]
        changed_graph["scenario_roots"].sort(key=lambda row: row["id"])
        self.assertEqual(len(root_ids), 5)
        for edge in changed_graph["scenario_edges"]:
            edge["active_scenarios"] = sorted(
                root_ids.get(identifier, identifier)
                for identifier in edge["active_scenarios"]
            )

        digest = self.reseal(changed_profiles)
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            AI._validate_invocation_profiles(changed_profiles)
            AI._validate_complete_scenarios(changed_graph, changed_profiles)
        with self.assertRaisesRegex(AssertionError, "independent profile grammar"):
            oracle_validate_profiles_and_routes(changed_profiles, changed_graph)

    def test_missing_bundle_edge_refuses_against_profile_union(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["kind"] == "worker-dispatch"
        )
        removed = edge["active_scenarios"].pop()
        edge["eligible_base_scenarios"] = sorted(
            {
                root["base_scenario"]
                for root in changed["scenario_roots"]
                if root["id"] in edge["active_scenarios"]
            }
        )
        with self.assertRaisesRegex(AI.Refusal, "scenario document union"):
            AI._validate_complete_scenarios(changed, self.profiles)
        self.assertTrue(removed)

    def test_synchronized_route_omission_refuses_5n_oracle(self):
        changed = copy.deepcopy(self.graph)
        profile_id = self.profiles["profiles"][0]["id"]
        removed = {
            root["id"]
            for root in changed["scenario_roots"]
            if root["profile_id"] == profile_id
        }
        changed["scenario_roots"] = [
            root for root in changed["scenario_roots"] if root["id"] not in removed
        ]
        for edge in changed["scenario_edges"]:
            edge["active_scenarios"] = [
                item for item in edge["active_scenarios"] if item not in removed
            ]
            if edge["active_scenarios"]:
                edge["eligible_base_scenarios"] = sorted(
                    {
                        root["base_scenario"]
                        for root in changed["scenario_roots"]
                        if root["id"] in edge["active_scenarios"]
                    }
                )
        changed["scenario_edges"] = [
            edge for edge in changed["scenario_edges"] if edge["active_scenarios"]
        ]
        with self.assertRaisesRegex(AI.Refusal, "denominator|5N"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_bogus_profile_binding_refuses(self):
        changed = copy.deepcopy(self.graph)
        changed["scenario_roots"][0]["profile_id"] = "fiat:invented"
        with self.assertRaisesRegex(AI.Refusal, "5N|unknown profile"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_credential_roster_leak_refuses(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["target"] == "CONTRIBUTORS.md"
        )
        absent = next(
            root["id"]
            for root in changed["scenario_roots"]
            if root["route"] == "repository"
            and root["credential"] == "absent"
            and root["base_scenario"] in edge["eligible_base_scenarios"]
        )
        edge["active_scenarios"].append(absent)
        edge["active_scenarios"].sort()
        with self.assertRaisesRegex(AI.Refusal, "scenario document union"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_reference_only_reachability_refuses(self):
        changed = copy.deepcopy(self.graph)
        target = changed["reference_only"][0]["path"]
        edge = copy.deepcopy(changed["scenario_edges"][0])
        edge["id"] = "scenario-edge-99999"
        edge["target"] = target
        changed["scenario_edges"].append(edge)
        with self.assertRaisesRegex(AI.Refusal, "scenario document union|reference-only"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_fixed_input_edge_kind_mutation_refuses(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["kind"] == "fixed-agent-input"
        )
        edge["kind"] = "mandatory-executable"
        with self.assertRaisesRegex(AI.Refusal, "fixed agent input"):
            AI._validate_complete_scenarios(changed, self.profiles)


class BytePartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.partition = load(PARTITION)
        cls.sources = {item["path"]: item for item in cls.manifest["documents"]}

    def test_every_range_is_ordered_gapless_and_digest_bound(self):
        self.assertEqual(len(self.partition["files"]), 191)
        for file_record in self.partition["files"]:
            source = AI._source_blob(file_record["path"])
            cursor = 0
            for item in file_record["ranges"]:
                self.assertEqual(item["start"], cursor)
                self.assertGreater(item["end"], item["start"])
                self.assertEqual(
                    item["span_sha256"],
                    hashlib.sha256(source[item["start"] : item["end"]]).hexdigest(),
                )
                cursor = item["end"]
            self.assertEqual(cursor, len(source))
            self.assertEqual(
                file_record["source_sha256"],
                self.sources[file_record["path"]]["sha256"],
            )

    def test_partition_totals_reconcile(self):
        self.assertEqual(sum(self.partition["totals"].values()), 2_290_450)
        self.assertEqual(self.partition["unsupported_operative_bytes"], 0)
        self.assertEqual(self.partition["totals"]["generated_duplicate"], 471_444)
        self.assertEqual(
            self.partition["totals"],
            {
                "exact_literal_or_evidence": 345_771,
                "generated_duplicate": 471_444,
                "governed_operative_semantics": 1_473_235,
                "human_only_explanation_or_rationale": 0,
                "unsupported_or_unknown": 0,
            },
        )

    def test_only_generated_promise_copies_use_duplicate_class(self):
        generated = {
            item["path"]
            for item in self.partition["files"]
            if {row["classification"] for row in item["ranges"]}
            == {"generated_duplicate"}
        }
        self.assertEqual(len(generated), 17)
        self.assertNotIn("PROMISE_MACHINE.md", generated)
        self.assertTrue(all(path.endswith("/PROMISE_MACHINE.md") for path in generated))

    def test_structured_references_are_whole_file_exact_evidence(self):
        by_path = {item["path"]: item for item in self.partition["files"]}
        for path, (size, digest) in EXPECTED_STRUCTURED_REFERENCES.items():
            with self.subTest(path=path):
                self.assertEqual(
                    by_path[path]["ranges"],
                    [{
                        "start": 0,
                        "end": size,
                        "classification": "exact_literal_or_evidence",
                        "span_sha256": digest,
                    }],
                )

    def test_nested_fences_remain_exact_literal_evidence(self):
        specimens = {
            "plugins/hexaemeron/skills/fiat/references/push-discipline.md": b"plugin-ci-workflow | filed",
            "plugins/hexaemeron/skills/solidity-auditor/references/report-formatting.md": b"- vulnerable line(s)",
        }
        by_path = {item["path"]: item for item in self.partition["files"]}
        for path, needle in specimens.items():
            source = AI._source_blob(path)
            position = source.index(needle)
            containing = next(
                item
                for item in by_path[path]["ranges"]
                if item["start"] <= position < item["end"]
            )
            self.assertEqual(
                containing["classification"], "exact_literal_or_evidence", path
            )

    def test_space_indented_fence_pairs_remain_exact_literal_evidence(self):
        """Independently retain fenced literals nested under list containers."""
        by_path = {item["path"]: item for item in self.partition["files"]}
        observed: list[tuple[str, int, int]] = []
        marker = re.compile(rb"^( {4,})(`{3,}|~{3,})([^\r\n]*)")
        for path, file_record in by_path.items():
            if not path.endswith(".md"):
                continue
            source = oracle_source(path)
            lines = source.splitlines(keepends=True)
            offsets = list(
                itertools.accumulate((len(line) for line in lines), initial=0)
            )
            for index, line in enumerate(lines):
                opening = marker.match(line)
                if opening is None or not opening.group(3).strip(b" \t"):
                    continue
                indent = opening.group(1)
                fence = opening.group(2)
                closing = re.compile(
                    rb"^"
                    + re.escape(indent)
                    + re.escape(fence[:1])
                    + rb"{"
                    + str(len(fence)).encode("ascii")
                    + rb",}[ \t]*(?:\r?\n)?$"
                )
                close_index = next(
                    (
                        candidate
                        for candidate in range(index + 1, len(lines))
                        if closing.match(lines[candidate])
                    ),
                    None,
                )
                if close_index is None:
                    continue
                start = offsets[index]
                end = offsets[close_index + 1]
                observed.append((path, start, end))
                for position in (start, end - 1):
                    containing = next(
                        item
                        for item in file_record["ranges"]
                        if item["start"] <= position < item["end"]
                    )
                    self.assertEqual(
                        containing["classification"],
                        "exact_literal_or_evidence",
                        f"{path}:{index + 1}-{close_index + 1}",
                    )
        self.assertEqual(
            observed,
            [
                (
                    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/"
                    "protocol-type-specialist.md",
                    2368,
                    2975,
                ),
                (
                    "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md",
                    11063,
                    11227,
                ),
            ],
        )

    def test_nested_list_fence_parser_keeps_literal_and_resumes_prose(self):
        source = (
            b"1. outer\n"
            b"   - example:\n"
            b"     ```solidity\n"
            b"     uint256 value = 1;\n"
            b"     ```\n"
            b"   - after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("nested-list.md", generated=False)
        literal = source.index(b"uint256")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_nested_fence_retains_deepest_applicable_list_baseline(self):
        """A root-valid opener must still close relative to its list item."""
        for opening_indent, closing_indent in itertools.product((2, 3), (4, 5)):
            ranges = None
            source = (
                b"- item\n"
                + b" " * opening_indent
                + b"```text\n"
                + b"  body\n"
                + b" " * closing_indent
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(
                opening_indent=opening_indent,
                closing_indent=closing_indent,
            ), mock.patch.object(AI, "_source_blob", return_value=source):
                try:
                    ranges = AI._partition_ranges("nested-list.md", generated=False)
                except AI.Refusal as exc:
                    self.fail(f"valid list-contained fence was refused: {exc}")
            if ranges is None:
                continue
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_fence_container_falls_back_to_root_after_list_exit(self):
        source = (
            b"- item\n"
            b"\n"
            b"```text\n"
            b"root literal\n"
            b"```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("root-fallback.md", generated=False)
        literal = source.index(b"root literal")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_list_marker_tab_padding_uses_absolute_tab_stops(self):
        """Marker padding tabs advance from the marker's ending column."""
        for marker in (b"-\titem", b"- \titem", b"10.\titem"):
            source = (
                marker
                + b"\n"
                + b"    ```text\n"
                + b"    body\n"
                + b"      ```\n"
                + b"after\n"
            )
            with self.subTest(marker=marker), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges("tab-list.md", generated=False)
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_same_line_nested_markers_retain_the_deepest_baseline(self):
        source = (
            b"- - item\n"
            b"    ```text\n"
            b"    body\n"
            b"      ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("same-line-nested.md", generated=False)
        literal = source.index(b"body")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_same_line_nested_marker_plus_four_does_not_open_a_fence(self):
        source = (
            b"- - item\n"
            b"        ```text\n"
            b"        body\n"
            b"        ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("same-line-too-deep.md", generated=False)
        for needle in (b"```text", b"body"):
            position = source.index(needle)
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= position < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_arbitrary_indentation_does_not_create_a_fence(self):
        specimens = {
            "plain-indented-code": (
                b"prose\n"
                b"    ```solidity\n"
                b"    uint256 value = 1;\n"
                b"    ```\n"
                b"after\n"
            ),
            "past-container-allowance": (
                b"- item\n"
                b"      ```solidity\n"
                b"      uint256 value = 1;\n"
                b"      ```\n"
                b"after\n"
            ),
        }
        for name, source in specimens.items():
            with self.subTest(name=name), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges(f"{name}.md", generated=False)
            literal = source.index(b"uint256")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_shorter_or_mismatched_fence_inside_long_fence_is_literal(self):
        specimens = {
            "shorter-backtick": b"````text\n```\nstill literal\n````\nafter\n",
            "shorter-backtick-info": b"````text\n```python\nstill literal\n````\nafter\n",
            "mismatched-tilde": b"````text\n~~~\nstill literal\n````\nafter\n",
            "mismatched-tilde-info": b"````text\n~~~text\nstill literal\n````\nafter\n",
        }
        for name, source in specimens.items():
            with self.subTest(name=name):
                with mock.patch.object(AI, "_source_blob", return_value=source):
                    try:
                        ranges = AI._partition_ranges(f"{name}.md", generated=False)
                    except AI.Refusal as exc:
                        self.fail(f"valid outer fence was refused: {exc}")
                literal = source.index(b"still literal")
                prose = source.index(b"after")
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= literal < item["end"]
                    ),
                    "exact_literal_or_evidence",
                )
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= prose < item["end"]
                    ),
                    "governed_operative_semantics",
                )

    def test_partition_rebuild_and_command_are_exact(self):
        self.assertEqual(self.partition, AI.build_partition(self.manifest))
        first = command(
            "verify-partition",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--partition",
            str(PARTITION),
        )
        second = command(
            "verify-partition",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--partition",
            str(PARTITION),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_overlap_mutation_refuses(self):
        changed = copy.deepcopy(self.partition)
        changed["files"][0]["ranges"][0]["start"] = 1
        with self.assertRaisesRegex(AI.Refusal, "overlap, gap, or are unordered"):
            AI._validate_partition_closure(changed, self.manifest)

    def test_partition_validator_refuses_derivation_drift_without_command_rebuild(self):
        mutations = {
            "source-sha256": lambda value: value["files"][0].__setitem__(
                "source_sha256", "0" * 64
            ),
            "class-total": lambda value: value["totals"].__setitem__(
                "governed_operative_semantics", 0
            ),
            "missing-file": lambda value: value["files"].pop(),
            "duplicate-file": lambda value: value["files"].append(
                copy.deepcopy(value["files"][0])
            ),
            "coherent-reclassification": lambda value: value["files"][0][
                "ranges"
            ][0].__setitem__(
                "classification", "human_only_explanation_or_rationale"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.partition)
                mutate(changed)
                with self.assertRaisesRegex(
                    AI.Refusal, "partition differs from its source-bound derivation"
                ):
                    try:
                        AI._validate_partition_closure(changed, self.manifest)
                    except TypeError:
                        # Exact parent accepted these mutations through the
                        # one-argument boundary. Keep that parent-red path
                        # executable while exercising the repaired join.
                        AI._validate_partition_closure(changed)


class LoaderGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)
        cls.profile_by_id = {
            item["id"]: item for item in cls.profiles["profiles"]
        }
        cls.root_by_id = {
            item["id"]: item for item in cls.graph["scenario_roots"]
        }
        cls.host_reach = AI._reachability_by_root(
            cls.graph["roots"], cls.graph["edges"], "active_roots"
        )
        cls.scenario_reach = AI._reachability_by_root(
            cls.graph["scenario_roots"],
            cls.graph["scenario_edges"],
            "active_scenarios",
        )

    def test_exact_graph_counts_are_derived_outputs(self):
        self.assertEqual(
            (
                len(self.graph["roots"]),
                len(self.graph["edges"]),
                len(self.graph["scenario_roots"]),
                len(self.graph["scenario_edges"]),
                len(self.graph["reference_only"]),
            ),
            (19, 332, 2_595, 337, 12),
        )

    def test_independent_oracle_accepts_inventory_bound_shallow_sources(self):
        clear_source_cache()
        try:
            with mock.patch.object(
                sys.modules[__name__], "oracle_source_mode", return_value="inventory"
            ):
                oracle_validate_runtime_edges(self.profiles, self.graph)
        finally:
            clear_source_cache()

    def test_profile_constraints_are_explicit(self):
        constraints = self.graph["constraints"]
        self.assertTrue(constraints["invocation_profiles_are_source_owned"])
        self.assertTrue(constraints["profile_route_product_is_exact"])
        self.assertTrue(constraints["fixed_agent_inputs_are_not_executed"])

    def test_graph_binds_the_profile_fixture_digest(self):
        self.assertEqual(
            self.graph["invocation_profiles_sha256"],
            hashlib.sha256(PROFILES.read_bytes()).hexdigest(),
        )

    def test_every_graph_evidence_span_binds_frozen_bytes(self):
        relations = [
            *self.graph["roots"],
            *self.graph["edges"],
            *self.graph["scenario_roots"],
            *self.graph["scenario_edges"],
            *self.graph["excluded_links"],
        ]
        for relation in relations:
            AI._validate_source_evidence(relation["evidence"], "test evidence")
        for relation in self.graph["reference_only"]:
            AI._validate_source_evidence(
                relation["source_evidence"], "test reference evidence"
            )

    def test_runtime_evidence_exists_only_for_executable_edges(self):
        for edge in [*self.graph["edges"], *self.graph["scenario_edges"]]:
            with self.subTest(edge=edge["id"]):
                self.assertEqual(
                    edge["runtime_evidence"] is not None,
                    edge["load_type"] == "mandatory-executable",
                )

    def test_independent_runtime_semantic_evidence_coverage_is_closed(self):
        oracle_validate_runtime_edges(self.profiles, self.graph)
        self.assertEqual(
            sum(
                edge["runtime_evidence"] is not None
                for edge in self.graph["scenario_edges"]
            ),
            12,
        )
        self.assertEqual(
            sum(
                edge["runtime_evidence"] is not None
                for edge in self.graph["edges"]
            ),
            11,
        )
        self.assertEqual(
            sum(ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS.values()), 23
        )

    def test_graph_validator_does_not_trust_generator_runtime_metadata(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["runtime_path"] = metadata[donor]["runtime_path"]
        metadata[target]["runtime_needle"] = metadata[donor]["runtime_needle"]
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "scenario runtime semantic anchor drift"
            ):
                AI.build_loader_graph(self.manifest, self.profiles)

    def test_graph_validator_refuses_all_scenario_runtime_target_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.graph["scenario_edges"], "target"
        )
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["scenario_edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AI.Refusal, "scenario runtime semantic anchor drift"
                ):
                    AI._validate_complete_scenarios(changed, self.profiles)

    def test_graph_validator_refuses_all_host_runtime_target_rebindings(self):
        specimens = cross_target_runtime_specimens(self.graph["edges"], "target")
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AI.Refusal, "host runtime semantic anchor drift"
                ):
                    AI._validate_complete_scenarios(changed, self.profiles)

    def test_independent_oracle_refuses_all_scenario_runtime_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.graph["scenario_edges"], "target"
        )
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["scenario_edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AssertionError, "independent scenario runtime anchor mismatch"
                ):
                    oracle_validate_runtime_edges(self.profiles, changed)

    def test_independent_oracle_refuses_all_host_runtime_rebindings(self):
        specimens = cross_target_runtime_specimens(self.graph["edges"], "target")
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AssertionError, "independent host runtime anchor mismatch"
                ):
                    oracle_validate_runtime_edges(self.profiles, changed)

    def test_host_root_identities_are_exact(self):
        self.assertEqual(
            {item["id"] for item in self.graph["roots"]},
            {"repository", "agent-skills"}
            | {f"standalone:{name}" for name in {
                AI._plugin(path) for path in AI.SELECTABLE_SKILL_PATHS.values()
            }},
        )

    def test_host_edge_scopes_are_closed(self):
        known = {item["id"] for item in self.graph["roots"]}
        for edge in self.graph["edges"]:
            self.assertEqual(edge["active_roots"], sorted(set(edge["active_roots"])))
            self.assertTrue(set(edge["active_roots"]) <= known)
            self.assertNotIn("*", edge["active_roots"])

    def test_manifest_host_reachability_is_graph_derived(self):
        for document in self.manifest["documents"]:
            self.assertEqual(
                set(document["loader_roots"]),
                self.host_reach.get(document["path"], set()),
            )

    def test_manifest_scenario_reachability_is_graph_derived(self):
        for document in self.manifest["documents"]:
            self.assertEqual(
                set(document["scenario_reachability"]),
                self.scenario_reach.get(document["path"], set()),
            )

    def test_scenario_denominator_is_exactly_5n(self):
        self.assertEqual(
            len(self.graph["scenario_roots"]),
            5 * self.profiles["totals"]["normalized_profiles"],
        )

    def test_scenario_route_totals_are_2n_2n_n(self):
        counts = {
            route: sum(root["route"] == route for root in self.graph["scenario_roots"])
            for route in ("repository", "agent-skills", "standalone")
        }
        self.assertEqual(
            counts,
            {"repository": 1_038, "agent-skills": 1_038, "standalone": 519},
        )

    def test_each_profile_has_five_scenario_roots(self):
        counts = {identifier: 0 for identifier in self.profile_by_id}
        for root in self.graph["scenario_roots"]:
            counts[root["profile_id"]] += 1
        self.assertEqual(set(counts.values()), {5})

    def test_route_credential_matrix_is_exact(self):
        for profile_id in self.profile_by_id:
            rows = [
                (root["route"], root["credential"])
                for root in self.graph["scenario_roots"]
                if root["profile_id"] == profile_id
            ]
            self.assertEqual(
                set(rows),
                {
                    ("repository", "absent"),
                    ("repository", "github-contributor"),
                    ("agent-skills", "absent"),
                    ("agent-skills", "github-contributor"),
                    ("standalone", "absent"),
                },
            )

    def test_route_skill_base_product_has_93_members(self):
        self.assertEqual(
            len({root["base_scenario"] for root in self.graph["scenario_roots"]}),
            93,
        )

    def test_root_conditions_bind_profile_and_optional_credential(self):
        for root in self.graph["scenario_roots"]:
            expected = [f"profile:{root['profile_id']}"]
            if root["credential"] == "github-contributor":
                expected.append("credential:github-contributor")
            self.assertEqual(root["conditions"], sorted(expected))
            self.assertEqual(root["mode"], "conditional")

    def test_each_scenario_starts_at_its_real_host_entry(self):
        for root in self.graph["scenario_roots"]:
            plugin = AI._plugin(AI.SELECTABLE_SKILL_PATHS[root["selected_skill"]])
            expected = {
                "repository": "AGENTS.md",
                "agent-skills": ".agents/skills/promise-machine/SKILL.md",
                "standalone": f"plugins/{plugin}/AGENTS.md",
            }[root["route"]]
            self.assertEqual(root["node"], expected)

    def test_each_reached_union_exactly_matches_its_profile_and_route(self):
        for identifier, root in self.root_by_id.items():
            expected = AI._scenario_expected_documents(
                root["route"],
                root["credential"],
                self.profile_by_id[root["profile_id"]],
            )
            observed = {
                path for path, scope in self.scenario_reach.items() if identifier in scope
            }
            self.assertEqual(observed, expected)

    def test_scenario_edge_scopes_are_sorted_closed_and_nonempty(self):
        known = set(self.root_by_id)
        for edge in self.graph["scenario_edges"]:
            scope = edge["active_scenarios"]
            self.assertTrue(scope)
            self.assertEqual(scope, sorted(set(scope)))
            self.assertNotIn("*", scope)
            self.assertTrue(set(scope) <= known)

    def test_edge_base_scopes_are_derived_from_active_roots(self):
        for edge in self.graph["scenario_edges"]:
            self.assertEqual(
                edge["eligible_base_scenarios"],
                sorted(
                    {
                        self.root_by_id[identifier]["base_scenario"]
                        for identifier in edge["active_scenarios"]
                    }
                ),
            )

    def test_every_scenario_edge_has_a_realisable_witness(self):
        for edge in self.graph["scenario_edges"]:
            for identifier in edge["active_scenarios"]:
                self.assertIn(identifier, self.scenario_reach[edge["source"]])
                self.assertIn(identifier, self.scenario_reach[edge["target"]])

    def test_profile_scopes_replace_edge_minimised_conditions(self):
        self.assertTrue(
            all(edge["condition"] is None for edge in self.graph["scenario_edges"])
        )
        self.assertTrue(
            all(root["conditions"][0].startswith(("credential:", "profile:")) for root in self.graph["scenario_roots"])
        )

    def test_reference_only_ledger_is_exact(self):
        expected = {
            path
            for path, row in AI._structured_metadata().items()
            if row["load_semantics"] == "reference-only"
        } | set(AI.REFERENCE_ONLY_MARKDOWN)
        self.assertEqual({row["path"] for row in self.graph["reference_only"]}, expected)

    def test_reference_only_documents_have_zero_reachability(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        for row in self.graph["reference_only"]:
            document = documents[row["path"]]
            self.assertEqual(document["loader_roots"], [])
            self.assertEqual(document["scenario_reachability"], [])

    def test_fixed_agent_inputs_have_nonexecuting_edges(self):
        for path in AI._fixed_agent_metadata():
            incoming = [
                edge for edge in self.graph["scenario_edges"] if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(
                all(
                    edge["kind"] == "fixed-agent-input"
                    and edge["load_type"] == "agent-or-prompt"
                    and edge["runtime_evidence"] is None
                    for edge in incoming
                )
            )

    def test_fixed_input_scopes_equal_profile_declarations(self):
        for path in AI._fixed_agent_metadata():
            expected = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if path in self.profile_by_id[root["profile_id"]]["required_documents"]
            }
            self.assertEqual(self.scenario_reach[path], expected)

    def test_mandatory_inputs_keep_executable_semantics(self):
        for path, metadata in AI._structured_metadata().items():
            if metadata["load_semantics"] != "mandatory-executable":
                continue
            incoming = [
                edge for edge in self.graph["scenario_edges"] if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(
                all(
                    edge["kind"] == "mandatory-executable"
                    and edge["runtime_evidence"] is not None
                    for edge in incoming
                )
            )

    def test_mandatory_input_scopes_equal_profile_declarations(self):
        for path, metadata in AI._structured_metadata().items():
            if metadata["load_semantics"] != "mandatory-executable":
                continue
            expected = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if path in self.profile_by_id[root["profile_id"]]["required_documents"]
            }
            self.assertEqual(self.scenario_reach[path], expected)

    def test_synkrisis_rule_runtime_has_two_exclusive_operation_spans(self):
        path = "plugins/synkrisis/references/rules-v1.json"
        spans = {
            edge["runtime_evidence"]["span_sha256"]
            for edge in self.graph["scenario_edges"]
            if edge["target"] == path
        }
        expected = {
            AI._evidence(
                AI._structured_metadata()[path]["runtime_path"], needle
            )["span_sha256"]
            for needle in AI.SYNKRISIS_RULE_RUNTIME_NEEDLES.values()
        }
        self.assertEqual(spans, expected)

    def test_every_declared_worker_is_reached_in_all_five_routes(self):
        for profile in self.profiles["profiles"]:
            roots = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if root["profile_id"] == profile["id"]
            }
            for worker in profile["worker_prompts"]:
                self.assertLessEqual(roots, self.scenario_reach[worker])

    def test_kronos_is_bounded_to_one_rank_or_one_dispatch_iteration(self):
        profiles = [
            row for row in self.profiles["profiles"] if row["selected_skill"] == "kronos"
        ]
        self.assertEqual(len(profiles), 26)
        self.assertEqual(sum("rank-only" in row["id"] for row in profiles), 2)
        self.assertTrue(
            all("rank-only" in row["id"] or "dispatch-" in row["id"] for row in profiles)
        )

    def test_graph_rebuild_is_exact(self):
        self.assertEqual(
            self.graph,
            AI.build_loader_graph(self.manifest, self.profiles),
        )

    def test_graph_validator_refuses_derivation_drift_without_command_rebuild(self):
        mutations = {
            "host-scope": lambda value: value["edges"][0].__setitem__(
                "active_roots", []
            ),
            "constraint": lambda value: value["constraints"].__setitem__(
                "profile_route_product_is_exact", False
            ),
            "excluded-link": lambda value: value["excluded_links"].pop(),
            "manifest-identity": lambda value: value.__setitem__(
                "manifest_sha256", "0" * 64
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.graph)
                mutate(changed)
                with self.assertRaisesRegex(
                    AI.Refusal, "loader graph differs from its source-bound derivation"
                ):
                    validator = getattr(AI, "_validate_loader_graph", None)
                    if validator is None:
                        # Exact parent exposed only the scenario-fragment
                        # validator, which accepted these whole-graph drifts.
                        AI._validate_complete_scenarios(changed, self.profiles)
                    else:
                        validator(changed, self.manifest, self.profiles)

    def test_verify_loader_is_read_only_and_repeatable(self):
        arguments = (
            "verify-loader",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--graph",
            str(GRAPH),
        )
        first = command(*arguments)
        second = command(*arguments)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


class FollowOnAudit18ParentGuardTests(unittest.TestCase):
    """Guards that stay assertion-red on exact parent fa48ff7a5881."""

    PIN = ".python-version"
    PIN_SHA256 = "3a55324cbeddc91df012407d051dad08c88624c95a82fbdb856728729fbd14ab"
    EXPECTED_PROFILES = {
        "anamnesis:demo-or-rebuild",
        "anamnesis:ordinary",
        "berean:ordinary",
        "brevitas:ordinary",
        "hermes:gas-operation",
        "lemma:changed-or-unexpected",
        "lemma:ordinary",
        "probitas:add-venue",
        "synkrisis:cohort-or-render",
        "synkrisis:diagnose",
        "synkrisis:verify",
    }

    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)

    @staticmethod
    def reseal_profiles(record: dict) -> str:
        digest = hashlib.sha256(canonical(record["profiles"])).hexdigest()
        record["projection_sha256"] = digest
        return digest

    @classmethod
    def independent_profile_scope(cls, profiles: list[dict]) -> None:
        expected = {
            row["id"]
            for row in oracle_profiles()
            if cls.PIN in row["required_documents"]
        }
        observed = {
            row.get("id")
            for row in profiles
            if isinstance(row, dict)
            and isinstance(row.get("required_documents"), list)
            and cls.PIN in row["required_documents"]
        }
        if expected != cls.EXPECTED_PROFILES or observed != expected:
            raise AssertionError("independent Python pin profile scope mismatch")

    @classmethod
    def independent_manifest_pin(cls, manifest: dict) -> None:
        documents = manifest.get("documents")
        if not isinstance(documents, list):
            raise AssertionError("independent Python pin manifest is malformed")
        matches = [row for row in documents if row.get("path") == cls.PIN]
        if len(matches) != 1:
            raise AssertionError("independent Python pin manifest identity mismatch")
        pin = matches[0]
        expected_evidence = oracle_span(
            "AGENTS.md",
            "Every `python3` command below means the exact interpreter recorded in\n"
            "[`.python-version`](.python-version).",
        )
        expected = {
            "admission_kind": "fixed-agent-input",
            "authority_tier": "fixed_input",
            "bytes": 7,
            "canonical_content_path": cls.PIN,
            "canonical_owner": "AGENTS.md",
            "document_class": "fixed_input",
            "external_runtime_owner": None,
            "load_semantics": "agent-or-prompt",
            "logical_document": "suite-runtime",
            "path": cls.PIN,
            "runtime_evidence": None,
            "sha256": cls.PIN_SHA256,
            "source_evidence": expected_evidence,
        }
        if any(pin.get(field) != value for field, value in expected.items()):
            raise AssertionError("independent Python pin manifest identity mismatch")
        if len(pin.get("scenario_reachability", [])) != 55:
            raise AssertionError("independent Python pin manifest route scope mismatch")

    @classmethod
    def independent_route_scope(cls, graph: dict) -> None:
        expected: set[str] = set()
        for profile_id in cls.EXPECTED_PROFILES:
            skill = profile_id.split(":", 1)[0]
            plugin = ORACLE_SKILL_PATHS[skill].split("/")[1]
            for route, credentials in (
                ("repository", ("absent", "github-contributor")),
                ("agent-skills", ("absent", "github-contributor")),
                ("standalone", ("absent",)),
            ):
                base = (
                    f"standalone:{plugin}:skill:{skill}"
                    if route == "standalone"
                    else f"{route}:skill:{skill}"
                )
                for credential in credentials:
                    expected.add(
                        f"{base}:profile:{profile_id}:credential:{credential}"
                    )
        roots = {
            row.get("id")
            for row in graph.get("scenario_roots", [])
            if row.get("profile_id") in cls.EXPECTED_PROFILES
        }
        incoming = [
            edge
            for edge in graph.get("scenario_edges", [])
            if edge.get("target") == cls.PIN
        ]
        active = {
            identifier
            for edge in incoming
            for identifier in edge.get("active_scenarios", [])
        }
        if roots != expected or active != expected or len(expected) != 55:
            raise AssertionError("independent Python pin route scope mismatch")
        if not incoming or any(
            edge.get("kind") != "fixed-agent-input"
            or edge.get("load_type") != "agent-or-prompt"
            or edge.get("runtime_evidence") is not None
            for edge in incoming
        ):
            raise AssertionError("independent Python pin execution semantics mismatch")

    def test_suite_runtime_pin_is_an_exact_nonexecuting_fixed_input(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        pin = documents[self.PIN]
        self.assertEqual(pin["document_class"], "fixed_input")
        self.assertEqual(pin["admission_kind"], "fixed-agent-input")
        self.assertEqual(pin["load_semantics"], "agent-or-prompt")
        self.assertEqual((pin["bytes"], pin["sha256"]), (7, self.PIN_SHA256))
        self.assertIsNone(pin["runtime_evidence"])
        self.independent_manifest_pin(self.manifest)

    def test_suite_runtime_pin_scope_is_exact_across_all_five_routes(self):
        profiles = {
            row["id"]
            for row in self.profiles["profiles"]
            if self.PIN in row["required_documents"]
        }
        self.assertEqual(profiles, self.EXPECTED_PROFILES)
        roots = {
            row["id"]
            for row in self.graph["scenario_roots"]
            if row["profile_id"] in profiles
        }
        self.assertEqual(len(roots), 55)
        incoming = [
            edge for edge in self.graph["scenario_edges"] if edge["target"] == self.PIN
        ]
        self.assertTrue(incoming)
        self.assertEqual(
            {root for edge in incoming for root in edge["active_scenarios"]}, roots
        )
        self.assertTrue(
            all(
                edge["kind"] == "fixed-agent-input"
                and edge["load_type"] == "agent-or-prompt"
                and edge["runtime_evidence"] is None
                for edge in incoming
            )
        )
        self.independent_profile_scope(self.profiles["profiles"])
        self.independent_route_scope(self.graph)

    def test_every_allowed_profile_refuses_pin_omission(self):
        for profile_id in sorted(self.EXPECTED_PROFILES):
            with self.subTest(profile_id=profile_id):
                changed = copy.deepcopy(self.profiles)
                profile = next(
                    row for row in changed["profiles"] if row["id"] == profile_id
                )
                profile["required_documents"].remove(self.PIN)
                profile["fixed_inputs"] = [
                    row for row in profile["fixed_inputs"] if row["path"] != self.PIN
                ]
                profile["source_evidence"] = [
                    row
                    for row in profile["source_evidence"]
                    if row["obligation"] != self.PIN
                ]
                digest = self.reseal_profiles(changed)
                with mock.patch.object(
                    AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest
                ):
                    with self.assertRaisesRegex(
                        AI.Refusal, "Python pin scope drift"
                    ):
                        AI._validate_invocation_profiles(changed)
                with self.assertRaisesRegex(
                    AssertionError, "independent Python pin profile scope mismatch"
                ):
                    self.independent_profile_scope(changed["profiles"])

    def test_every_allowed_profile_refuses_pin_demotion(self):
        for profile_id in sorted(self.EXPECTED_PROFILES):
            with self.subTest(profile_id=profile_id):
                changed = copy.deepcopy(self.profiles)
                profile = next(
                    row for row in changed["profiles"] if row["id"] == profile_id
                )
                fixed = next(
                    row for row in profile["fixed_inputs"] if row["path"] == self.PIN
                )
                fixed["load_semantics"] = "reference-only"
                digest = self.reseal_profiles(changed)
                with mock.patch.object(
                    AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest
                ):
                    with self.assertRaisesRegex(
                        AI.Refusal, "fixed input semantics drift"
                    ):
                        AI._validate_invocation_profiles(changed)
                expected = next(
                    row for row in oracle_profiles() if row["id"] == profile_id
                )
                observed = {
                    key: value
                    for key, value in profile.items()
                    if key != "source_evidence"
                }
                self.assertNotEqual(observed, expected)

    def test_every_excluded_profile_has_no_pin_semantic_anchor(self):
        excluded = [
            row
            for row in self.profiles["profiles"]
            if row["id"] not in self.EXPECTED_PROFILES
        ]
        self.assertEqual(len(excluded), 508)
        for profile in excluded:
            with self.subTest(profile_id=profile["id"]):
                with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
                    AI._python_pin_profile_anchor(
                        profile["selected_skill"], tuple(profile["branch_state"])
                    )
                with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
                    AI._validation_python_pin_anchor(profile)
                with self.assertRaisesRegex(AssertionError, "relation is unowned"):
                    oracle_python_pin_anchor(profile)

    def test_synchronised_excluded_profile_pin_addition_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            row
            for row in changed["profiles"]
            if row["id"] == "anamnesis:frontier-gate"
        )
        donor = next(
            row
            for row in changed["profiles"]
            if row["id"] == "anamnesis:ordinary"
        )
        profile["required_documents"].append(self.PIN)
        profile["required_documents"].sort()
        profile["fixed_inputs"].append(
            {"path": self.PIN, "load_semantics": "agent-or-prompt"}
        )
        profile["fixed_inputs"].sort(key=lambda row: row["path"])
        evidence = copy.deepcopy(
            next(
                row
                for row in donor["source_evidence"]
                if row["obligation"] == self.PIN
            )
        )
        profile["source_evidence"].append(evidence)
        profile["source_evidence"].sort(key=lambda row: row["obligation"])
        digest = self.reseal_profiles(changed)
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
                AI._validate_invocation_profiles(changed)
        with self.assertRaisesRegex(
            AssertionError, "independent Python pin profile scope mismatch"
        ):
            self.independent_profile_scope(changed["profiles"])

    def test_pin_manifest_bytes_digest_execution_and_source_weakening_refuse(self):
        executable = next(
            row["runtime_evidence"]
            for row in self.manifest["documents"]
            if row["runtime_evidence"] is not None
        )

        def pin_in(manifest: dict) -> dict:
            return next(
                row for row in manifest["documents"] if row["path"] == self.PIN
            )

        mutations = {
            "bytes": lambda pin: pin.__setitem__("bytes", 6),
            "digest": lambda pin: pin.__setitem__("sha256", "0" * 64),
            "executable": lambda pin: pin.update(
                {
                    "load_semantics": "mandatory-executable",
                    "runtime_evidence": copy.deepcopy(executable),
                }
            ),
            "weak-source-span": lambda pin: pin.__setitem__(
                "source_evidence", oracle_span("AGENTS.md", ".python-version")
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.manifest)
                mutate(pin_in(changed))
                with self.assertRaises(AI.Refusal):
                    AI._validate_manifest_shape(changed, self.profiles)
                with self.assertRaisesRegex(
                    AssertionError, "independent Python pin manifest identity mismatch"
                ):
                    self.independent_manifest_pin(changed)
                if label == "weak-source-span":
                    with self.assertRaisesRegex(
                        AssertionError, "independent manifest source anchor mismatch"
                    ):
                        oracle_validate_manifest_semantic_anchors(changed)

    def test_pin_graph_refuses_executable_fiction(self):
        changed = copy.deepcopy(self.graph)
        pin_edge = next(
            edge
            for edge in changed["scenario_edges"]
            if edge["target"] == self.PIN
        )
        runtime = next(
            edge["runtime_evidence"]
            for edge in changed["scenario_edges"]
            if edge["runtime_evidence"] is not None
        )
        pin_edge["load_type"] = "mandatory-executable"
        pin_edge["runtime_evidence"] = copy.deepcopy(runtime)
        with self.assertRaises(AI.Refusal):
            AI._validate_complete_scenarios(changed, self.profiles)
        with self.assertRaisesRegex(
            AssertionError, "independent Python pin execution semantics mismatch"
        ):
            self.independent_route_scope(changed)

    def test_each_pin_route_variant_refuses_deletion(self):
        roots = [
            row
            for row in self.graph["scenario_roots"]
            if row["profile_id"] == "anamnesis:ordinary"
        ]
        self.assertEqual(
            {(row["route"], row["credential"]) for row in roots},
            {
                ("repository", "absent"),
                ("repository", "github-contributor"),
                ("agent-skills", "absent"),
                ("agent-skills", "github-contributor"),
                ("standalone", "absent"),
            },
        )
        for removed in roots:
            with self.subTest(
                route=removed["route"], credential=removed["credential"]
            ):
                changed = copy.deepcopy(self.graph)
                identifier = removed["id"]
                changed["scenario_roots"] = [
                    row
                    for row in changed["scenario_roots"]
                    if row["id"] != identifier
                ]
                for edge in changed["scenario_edges"]:
                    if identifier in edge["active_scenarios"]:
                        edge["active_scenarios"].remove(identifier)
                with self.assertRaisesRegex(
                    AI.Refusal, "scenario root denominator or identity drift"
                ):
                    AI._validate_complete_scenarios(changed, self.profiles)
                with self.assertRaisesRegex(
                    AssertionError, "independent Python pin route scope mismatch"
                ):
                    self.independent_route_scope(changed)


class HoldoutSealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)
        cls.cohorts = load(COHORTS)
        cls.seal = load(SEAL)

    def test_cohorts_are_disjoint_and_meet_byte_gates(self):
        development = set(self.cohorts["development"]["paths"])
        holdout = set(self.cohorts["holdout"]["paths"])
        self.assertFalse(development & holdout)
        self.assertGreaterEqual(
            float(self.cohorts["development"]["unique_byte_ratio"]), 0.50
        )
        self.assertGreaterEqual(
            float(self.cohorts["holdout"]["unique_byte_ratio"]), 0.20
        )
        self.assertGreaterEqual(len(self.cohorts["development"]["logical_skills"]), 12)
        self.assertEqual(
            self.cohorts["holdout"]["logical_skills"],
            ["alexandria", "fizz", "phylax", "probitas", "sapheneia"],
        )
        self.assertEqual(len(self.cohorts["holdout"]["paths"]), 31)
        self.assertEqual(self.cohorts["holdout"]["unique_bytes"], 363_804)
        self.assertEqual(self.cohorts["holdout"]["unique_byte_ratio"], "0.200002")
        self.assertEqual(self.cohorts["development"]["unique_bytes"], 1_455_202)
        self.assertEqual(
            self.cohorts["development"]["unique_byte_ratio"], "0.799998"
        )
        self.assertEqual(self.cohorts["selection"]["seed"], AI.SELECTION_SEED)

    def test_development_covers_roots_tiers_constructs_and_deciles(self):
        development = set(self.cohorts["development"]["paths"])
        self.assertIn("AGENTS.md", development)
        self.assertIn("PROMISE_MACHINE.md", development)
        self.assertIn(".agents/skills/promise-machine/SKILL.md", development)
        self.assertEqual(self.cohorts["development"]["size_deciles"], list(range(10)))
        self.assertEqual(
            set(self.cohorts["development"]["constructs"]),
            {
                "authority",
                "cross-document",
                "exact-literal",
                "exception",
                "failure",
                "negation",
                "order",
                "recovery",
                "refusal",
                "scope",
                "unknown",
            },
        )
        self.assertEqual(
            set(self.cohorts["development"]["authority_tiers"]),
            {
                item["authority_tier"]
                for item in self.manifest["documents"]
                if item["path"] == item["canonical_content_path"]
            },
        )
        self.assertEqual(
            set(self.cohorts["development"]["document_classes"]),
            set(AI.EXPECTED_COUNTS),
        )

    def test_sealed_envelope_has_required_classes_without_answers(self):
        envelope = self.seal["closed_future_case_envelope"]
        self.assertEqual(len(envelope["slots"]), 16)
        self.assertEqual(
            {slot["semantic_class"] for slot in envelope["slots"]},
            {"authority", "failure", "recovery", "exact-literal", "cross-document"},
        )
        forbidden = set(envelope["forbidden_until_open"])
        self.assertEqual(
            forbidden, {"prompt", "expected_answer", "scorer_key", "model_output"}
        )
        self.assertTrue(all(not forbidden & set(slot) for slot in envelope["slots"]))
        self.assertIs(self.seal["opened"], False)

    def test_commitments_recompute(self):
        membership = self.seal["membership"]
        envelope = self.seal["closed_future_case_envelope"]
        self.assertEqual(
            self.seal["membership_sha256"],
            hashlib.sha256(canonical(membership)).hexdigest(),
        )
        self.assertEqual(
            self.seal["case_envelope_sha256"],
            hashlib.sha256(canonical(envelope)).hexdigest(),
        )
        body = dict(self.seal)
        commitment = body.pop("commitment_sha256")
        self.assertEqual(commitment, hashlib.sha256(canonical(body)).hexdigest())

    def test_seal_binds_exact_profile_and_graph_identities(self):
        expected = {
            "invocation_profiles_sha256": hashlib.sha256(
                canonical(self.profiles)
            ).hexdigest(),
            "loader_graph_sha256": hashlib.sha256(canonical(self.graph)).hexdigest(),
        }
        for field, digest in expected.items():
            with self.subTest(field=field):
                self.assertEqual(self.seal.get(field), digest)

    def test_resealed_profile_or_graph_identity_mismatch_refuses(self):
        for field in ("invocation_profiles_sha256", "loader_graph_sha256"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.seal)
                changed[field] = "0" * 64
                body = dict(changed)
                body.pop("commitment_sha256")
                changed["commitment_sha256"] = hashlib.sha256(
                    canonical(body)
                ).hexdigest()
                with self.assertRaisesRegex(AI.Refusal, "input identity"):
                    AI._validate_holdout_seal(
                        changed,
                        self.manifest,
                        self.cohorts,
                        self.profiles,
                        self.graph,
                    )

    def reseal(self, changed):
        body = dict(changed)
        body.pop("commitment_sha256", None)
        changed["commitment_sha256"] = hashlib.sha256(
            canonical(body)
        ).hexdigest()

    def validate_changed_seal(self, changed):
        AI._validate_holdout_seal(
            changed,
            self.manifest,
            self.cohorts,
            self.profiles,
            self.graph,
        )

    def test_coherently_resealed_membership_drift_refuses(self):
        changed = copy.deepcopy(self.seal)
        changed["membership"]["paths"] = changed["membership"]["paths"][1:]
        changed["membership_sha256"] = hashlib.sha256(
            canonical(changed["membership"])
        ).hexdigest()
        self.reseal(changed)
        with self.assertRaisesRegex(AI.Refusal, "membership drift"):
            self.validate_changed_seal(changed)

    def test_coherently_resealed_upstream_cohort_drift_refuses(self):
        cohorts = copy.deepcopy(self.cohorts)
        cohorts["holdout"]["logical_skills"] = cohorts["holdout"][
            "logical_skills"
        ][1:]
        cohorts["holdout"]["paths"] = cohorts["holdout"]["paths"][1:]
        replacement_skill = cohorts["holdout"]["logical_skills"][0]
        for slot in cohorts["holdout"]["case_slots"]:
            slot["logical_skill"] = replacement_skill

        changed = copy.deepcopy(self.seal)
        changed["cohorts_sha256"] = hashlib.sha256(canonical(cohorts)).hexdigest()
        changed["membership"] = {
            "logical_skills": cohorts["holdout"]["logical_skills"],
            "paths": cohorts["holdout"]["paths"],
        }
        changed["membership_sha256"] = hashlib.sha256(
            canonical(changed["membership"])
        ).hexdigest()
        changed["closed_future_case_envelope"] = {
            "slots": cohorts["holdout"]["case_slots"],
            "forbidden_until_open": [
                "prompt",
                "expected_answer",
                "scorer_key",
                "model_output",
            ],
        }
        changed["case_envelope_sha256"] = hashlib.sha256(
            canonical(changed["closed_future_case_envelope"])
        ).hexdigest()
        self.reseal(changed)

        with self.assertRaisesRegex(
            AI.Refusal, "cohorts differ from their source-bound derivation"
        ):
            AI._validate_holdout_seal(
                changed,
                self.manifest,
                cohorts,
                self.profiles,
                self.graph,
            )

    def test_stale_membership_digest_refuses_after_outer_reseal(self):
        changed = copy.deepcopy(self.seal)
        changed["membership_sha256"] = "0" * 64
        self.reseal(changed)
        with self.assertRaisesRegex(AI.Refusal, "membership digest drift"):
            self.validate_changed_seal(changed)

    def test_coherently_resealed_case_envelope_drift_refuses(self):
        for mutation in ("slot", "forbidden"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.seal)
                envelope = changed["closed_future_case_envelope"]
                if mutation == "slot":
                    envelope["slots"][0]["logical_skill"] = "sapheneia"
                else:
                    envelope["forbidden_until_open"].remove("expected_answer")
                changed["case_envelope_sha256"] = hashlib.sha256(
                    canonical(envelope)
                ).hexdigest()
                self.reseal(changed)
                with self.assertRaisesRegex(AI.Refusal, "case envelope drift"):
                    self.validate_changed_seal(changed)

    def test_stale_case_envelope_digest_refuses_after_outer_reseal(self):
        changed = copy.deepcopy(self.seal)
        changed["case_envelope_sha256"] = "0" * 64
        self.reseal(changed)
        with self.assertRaisesRegex(AI.Refusal, "case envelope digest drift"):
            self.validate_changed_seal(changed)

    def test_resealed_source_identity_drift_refuses(self):
        for field, value in (
            ("schema", "wildcat-instruction-architecture-holdout-seal/v2"),
            ("source_ref", "0" * 40),
            ("selection_seed", "attacker-seed"),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.seal)
                changed[field] = value
                self.reseal(changed)
                with self.assertRaisesRegex(AI.Refusal, "source identity drift"):
                    self.validate_changed_seal(changed)

    def test_resealed_outer_field_set_drift_refuses(self):
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.seal)
                if mutation == "missing":
                    changed.pop("membership_sha256")
                else:
                    changed["unbound_extension"] = "accepted by the exact parent"
                self.reseal(changed)
                with self.assertRaisesRegex(AI.Refusal, "non-closed field set"):
                    self.validate_changed_seal(changed)

    def test_non_object_seal_refuses(self):
        with self.assertRaisesRegex(AI.Refusal, "must be an object"):
            self.validate_changed_seal([])

    def test_seed_replay_and_command_are_exact(self):
        rebuilt = AI.build_cohorts(self.manifest)
        self.assertEqual(rebuilt, self.cohorts)
        self.assertEqual(
            AI.build_holdout_seal(
                self.manifest, rebuilt, self.profiles, self.graph
            ),
            self.seal,
        )
        first = command(
            "verify-seal",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--cohorts",
            str(COHORTS),
            "--seal",
            str(SEAL),
        )
        second = command(
            "verify-seal",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--cohorts",
            str(COHORTS),
            "--seal",
            str(SEAL),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


if __name__ == "__main__":
    unittest.main()
