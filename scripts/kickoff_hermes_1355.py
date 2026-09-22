#!/usr/bin/env python3
"""Validate the public and restricted preparation evidence for kickoff #1355."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "docs/kickoff/1355/evidence/prepared-harnesses.json"
DEFAULT_RESTRICTED = ROOT / ".hexaemeron/restricted/step-1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
SUMMARY_PATTERNS = (
    re.compile(
        r"Test result: ok\. (?P<passed>[0-9]+) passed; "
        r"(?P<failed>[0-9]+) failed; (?P<skipped>[0-9]+) skipped;"
    ),
    re.compile(
        r"Ran [0-9]+ test suites?[^\n]*: (?P<passed>[0-9]+) tests passed, "
        r"(?P<failed>[0-9]+) failed, (?P<skipped>[0-9]+) skipped"
    ),
)
PARENT_RED_PATTERN = re.compile(
    r"Encountered a total of (?P<failed>[0-9]+) failing tests, "
    r"(?P<passed>[0-9]+) tests succeeded"
)
MAX_JSON = 2 * 1024 * 1024
MAX_LOG = 32 * 1024 * 1024
SIGNER = "3BCD9EFDA6670A3F65AF679EB83B60AE16F5DD1A"
CURRENT_RUNNER = {
    "version": "forge 1.7.1 (4072e48705af9d93e3c0f6e29e93b5e9a40caed8)",
    "binary_sha256": "e729589084ca2f1479354353d1ec3d4789451b577f4cdee4e7dc57cae64a38fa",
}
HISTORICAL_RUNNER = {
    "version": "forge 0.3.0 (5a8bd89 2024-12-19T17:17:08.560665000Z)",
    "binary_sha256": "5c65573eb556e06d3a60f9b61223988c18e6c8fe43e97a1a3d1eeaf9761bc423",
}


def profile(solc: str, evm: str, via_ir: bool, runs: int, bytecode_hash: str) -> dict[str, Any]:
    return {
        "kind": "historical-test",
        "solc": solc,
        "evm_version": evm,
        "via_ir": via_ir,
        "optimizer": runs > 0,
        "optimizer_runs": runs,
        "bytecode_hash": bytecode_hash,
    }


GROUPS: dict[str, dict[str, Any]] = {
    "v2-a70f297f": {
        "repository": "wildcat-finance/v2-protocol",
        "source_commit": "a70f297fbd1b1ab597e0e9a3458a2d13a34b4657",
        "source_access": "public",
        "profile": profile("0.8.25", "cancun", True, 50000, "none"),
        "changed": ["test/market/WildcatMarket.t.sol"],
    },
    "v2-5838b2f3": {
        "repository": "wildcat-finance/v2-protocol",
        "source_commit": "5838b2f3f5c0bb3489cd2ff16bb31ddd5194c7fa",
        "source_access": "public",
        "profile": profile("0.8.25", "cancun", True, 50000, "none"),
        "changed": [
            "test/access/FixedTermHooks.t.sol",
            "test/helpers/BaseERC20Test.sol",
            "test/market/WildcatMarket.t.sol",
        ],
    },
    "v2-e1f77540": {
        "repository": "wildcat-finance/v2-protocol",
        "source_commit": "e1f77540fef65736374de6c847743d8ca2233fb4",
        "source_access": "public",
        "profile": profile("0.8.25", "cancun", True, 200, "none"),
        "changed": [
            "test/helpers/BaseERC20Test.sol",
            "test/market/WildcatMarket.t.sol",
        ],
    },
    "v2-c7be4039": {
        "repository": "wildcat-finance/v2-protocol",
        "source_commit": "c7be4039f8f383a9dda4e45f63331c17d63f9ed9",
        "source_access": "public",
        "profile": profile("0.8.25", "cancun", False, 200, "none"),
        "changed": ["test/market/WildcatMarket.t.sol"],
    },
    "v1-da74452a": {
        "repository": "wildcat-finance/wildcat-protocol",
        "source_commit": "da74452aa7d1a0f024d99efd22cc6d950a8116b7",
        "source_access": "public",
        "profile": profile("0.8.22", "shanghai", False, 0, "ipfs"),
        "changed": ["test/EscrowTest.sol", "test/helpers/BaseERC20Test.sol"],
    },
    "v1-6164ddd4": {
        "repository": "wildcat-finance/wildcat-protocol",
        "source_commit": "6164ddd4c75ef6da2181e5623b99795b9829e31c",
        "source_access": "public",
        "profile": profile("0.8.22", "shanghai", False, 0, "ipfs"),
        "changed": ["test/EscrowTest.sol", "test/helpers/BaseERC20Test.sol"],
    },
    "fee-ac73bda3": {
        "repository": "wildcat-finance/fee-recipient-contract",
        "source_commit": "ac73bda3642c9a7c8de64e39856b31af53f06068",
        "source_access": "restricted",
        "profile": profile("0.8.25", "cancun", True, 200, "none"),
        "changed": [],
    },
    "collateral-46dba596": {
        "repository": "wildcat-finance/collateral-contract",
        "source_commit": "46dba596fa111f868200358f551796e8f73b5fd7",
        "source_access": "public",
        "profile": profile("0.8.28", "cancun", True, 50000, "none"),
        "changed": [],
    },
    "provider-5d7f8c88": {
        "repository": "wildcat-finance/chainalysis-ofac-role-provider",
        "source_commit": "5d7f8c889a8d29935838a3906172feb8d9861807",
        "source_access": "restricted",
        "profile": profile("0.8.25", "cancun", True, 200, "none"),
        "changed": [],
    },
}

GROUP_KEYS = {
    "id",
    "repository",
    "source_access",
    "source_commit",
    "prepared_commit",
    "signature",
    "compiler_profile",
    "admitted_test_paths",
    "parity",
    "tests",
    "restricted_evidence_sha256",
}
PARITY_KEYS = {
    "changed_paths",
    "production_diff_count",
    "configuration_diff_count",
    "dependency_diff_count",
    "submodule_diff_count",
}
TEST_KEYS = {
    "command",
    "seed",
    "passed",
    "failed",
    "skipped",
    "duration_seconds",
    "log_sha256",
    "runner",
}


class EvidenceError(ValueError):
    pass


def strict_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise EvidenceError(f"duplicate-key:{key}")
        result[key] = value
    return result


def read_json(path: Path, limit: int = MAX_JSON) -> tuple[dict[str, Any], bytes]:
    if path.is_symlink() or not path.is_file():
        raise EvidenceError(f"unsafe-json-path:{path}")
    raw = path.read_bytes()
    if len(raw) > limit:
        raise EvidenceError(f"json-too-large:{path}")
    try:
        value = json.loads(raw, object_pairs_hook=strict_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise EvidenceError(f"invalid-json:{path}:{exc}") from exc
    if not isinstance(value, dict):
        raise EvidenceError(f"json-root-not-object:{path}")
    return value, raw


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    if set(value) != expected:
        raise EvidenceError(
            f"{label}-keys:missing={sorted(expected - set(value))}:"
            f"extra={sorted(set(value) - expected)}"
        )


def safe_leaf(base: Path, relative: str, *, directory: bool = False) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise EvidenceError(f"unsafe-relative-path:{relative!r}")
    item = Path(relative)
    if item.is_absolute() or ".." in item.parts:
        raise EvidenceError(f"path-escape:{relative}")
    resolved_base = base.resolve()
    candidate = base.joinpath(item)
    resolved = candidate.resolve()
    if not resolved.is_relative_to(resolved_base):
        raise EvidenceError(f"path-escape:{relative}")
    if candidate.is_symlink():
        raise EvidenceError(f"symlink-refused:{relative}")
    if directory and not candidate.is_dir():
        raise EvidenceError(f"missing-directory:{relative}")
    if not directory and not candidate.is_file():
        raise EvidenceError(f"missing-file:{relative}")
    return candidate


def find_forbidden_payload(value: Any, trail: str = "$") -> None:
    forbidden_keys = {"source", "source_bytes", "source_text", "private_key", "credential"}
    if isinstance(value, dict):
        for key, child in value.items():
            if key in forbidden_keys:
                raise EvidenceError(f"private-payload-key:{trail}.{key}")
            find_forbidden_payload(child, f"{trail}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            find_forbidden_payload(child, f"{trail}[{index}]")
    elif isinstance(value, str):
        if value.startswith("/") or "/.hexaemeron/" in value:
            raise EvidenceError(f"private-or-absolute-path:{trail}")


def validate_group(row: dict[str, Any], expected_id: str) -> None:
    exact_keys(row, GROUP_KEYS, f"group:{expected_id}")
    expected = GROUPS[expected_id]
    if row["id"] != expected_id:
        raise EvidenceError(f"group-order-or-id:{expected_id}")
    for field in ("repository", "source_access", "source_commit"):
        if row[field] != expected[field]:
            raise EvidenceError(f"{expected_id}:{field}")
    if not isinstance(row["prepared_commit"], str) or not HEX40.fullmatch(row["prepared_commit"]):
        raise EvidenceError(f"{expected_id}:prepared-commit")
    signature = row["signature"]
    if signature != {"status": "verified", "fingerprint": SIGNER}:
        raise EvidenceError(f"{expected_id}:signature")
    if row["compiler_profile"] != expected["profile"]:
        raise EvidenceError(f"{expected_id}:compiler-profile")
    if row["admitted_test_paths"] != expected["changed"]:
        raise EvidenceError(f"{expected_id}:admitted-test-paths")
    parity = row["parity"]
    if not isinstance(parity, dict):
        raise EvidenceError(f"{expected_id}:parity-type")
    exact_keys(parity, PARITY_KEYS, f"{expected_id}:parity")
    if parity["changed_paths"] != expected["changed"]:
        raise EvidenceError(f"{expected_id}:changed-paths")
    for field in PARITY_KEYS - {"changed_paths"}:
        if parity[field] != 0 or isinstance(parity[field], bool):
            raise EvidenceError(f"{expected_id}:{field}")
    tests = row["tests"]
    if not isinstance(tests, dict):
        raise EvidenceError(f"{expected_id}:tests-type")
    exact_keys(tests, TEST_KEYS, f"{expected_id}:tests")
    if not isinstance(tests["command"], list) or not tests["command"]:
        raise EvidenceError(f"{expected_id}:test-command")
    if tests["command"][-2:] != ["--fuzz-seed", "0x5EED"]:
        raise EvidenceError(f"{expected_id}:fixed-seed-command")
    if tests["seed"] != "0x5EED":
        raise EvidenceError(f"{expected_id}:fuzz-seed")
    expected_runner = HISTORICAL_RUNNER if expected_id == "v2-c7be4039" else CURRENT_RUNNER
    if tests["runner"] != expected_runner:
        raise EvidenceError(f"{expected_id}:runner")
    for field in ("passed", "failed", "skipped"):
        if not isinstance(tests[field], int) or isinstance(tests[field], bool):
            raise EvidenceError(f"{expected_id}:{field}-type")
    if tests["passed"] <= 0 or tests["failed"] != 0 or tests["skipped"] != 0:
        raise EvidenceError(f"{expected_id}:suite-not-green")
    if not isinstance(tests["duration_seconds"], (int, float)) or tests["duration_seconds"] < 0:
        raise EvidenceError(f"{expected_id}:duration")
    for field in ("log_sha256",):
        if not isinstance(tests[field], str) or not HEX64.fullmatch(tests[field]):
            raise EvidenceError(f"{expected_id}:{field}")
    if not isinstance(row["restricted_evidence_sha256"], str) or not HEX64.fullmatch(
        row["restricted_evidence_sha256"]
    ):
        raise EvidenceError(f"{expected_id}:restricted-evidence-digest")


def validate_public_data(data: dict[str, Any]) -> None:
    exact_keys(
        data,
        {"schema", "candidate", "criterion", "access_boundary", "groups"},
        "manifest",
    )
    if data["schema"] != "hermes-prepared-harnesses-public/v1":
        raise EvidenceError("manifest-schema")
    if data["candidate"] != "prepared-source-group" or data["criterion"] != "prepared-state":
        raise EvidenceError("manifest-subject")
    if data["access_boundary"] != {
        "public": "identities-counts-and-digests",
        "restricted": "source-worktrees-complete-logs-and-private-source",
    }:
        raise EvidenceError("access-boundary")
    groups = data["groups"]
    if not isinstance(groups, list) or len(groups) != len(GROUPS):
        raise EvidenceError("group-count")
    for row, expected_id in zip(groups, GROUPS, strict=True):
        if not isinstance(row, dict):
            raise EvidenceError(f"group-not-object:{expected_id}")
        validate_group(row, expected_id)
    find_forbidden_payload(data)


def run_git(worktree: Path, *argv: str) -> str:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "LC_ALL": "C",
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    }
    if "GNUPGHOME" in os.environ:
        env["GNUPGHOME"] = os.environ["GNUPGHOME"]
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=", *argv],
        cwd=worktree,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
        check=False,
    )
    if result.returncode:
        raise EvidenceError(f"git-failed:{argv[0]}:{result.stderr.strip()[:300]}")
    return result.stdout.strip()


def parse_log(path: Path) -> tuple[int, int, int]:
    if path.stat().st_size > MAX_LOG:
        raise EvidenceError(f"log-too-large:{path.name}")
    text = path.read_text(encoding="utf-8", errors="strict")
    matches = [
        match
        for pattern in SUMMARY_PATTERNS
        for match in pattern.finditer(text)
    ]
    if not matches:
        raise EvidenceError(f"missing-test-summary:{path.name}")
    final = max(matches, key=lambda match: match.start())
    return tuple(int(final.group(name)) for name in ("passed", "failed", "skipped"))


def parse_parent_red_log(path: Path) -> tuple[int, int]:
    if path.stat().st_size > MAX_LOG:
        raise EvidenceError(f"log-too-large:{path.name}")
    text = path.read_text(encoding="utf-8", errors="strict")
    matches = list(PARENT_RED_PATTERN.finditer(text))
    if not matches:
        raise EvidenceError(f"missing-parent-red-summary:{path.name}")
    final = matches[-1]
    return int(final.group("passed")), int(final.group("failed"))


def validate_profile_data(data: dict[str, Any], expected_id: str) -> None:
    expected = GROUPS[expected_id]["profile"]
    actual = {
        "solc": data.get("solc"),
        "evm_version": data.get("evm_version"),
        "via_ir": data.get("via_ir"),
        "optimizer": data.get("optimizer"),
        "optimizer_runs": data.get("optimizer_runs"),
        "bytecode_hash": data.get("bytecode_hash"),
    }
    wanted = {key: expected[key] for key in actual}
    if actual != wanted:
        raise EvidenceError(f"{expected_id}:executed-compiler-profile")


def validate_restricted(
    manifest: dict[str, Any], restricted_root: Path, restricted_data: dict[str, Any]
) -> None:
    exact_keys(restricted_data, {"schema", "groups", "regressions"}, "restricted-index")
    if restricted_data["schema"] != "hermes-prepared-state/v1":
        raise EvidenceError("restricted-schema")
    rows = restricted_data["groups"]
    if not isinstance(rows, list) or len(rows) != len(GROUPS):
        raise EvidenceError("restricted-group-count")
    public_rows = {row["id"]: row for row in manifest["groups"]}
    for row, expected_id in zip(rows, GROUPS, strict=True):
        exact_keys(
            row,
            {
                "id",
                "worktree",
                "test_log",
                "test_log_sha256",
                "profile_report",
                "profile_report_sha256",
                "runner_binary",
                "passed",
                "failed",
                "skipped",
                "duration_seconds",
            },
            f"restricted:{expected_id}",
        )
        if row["id"] != expected_id:
            raise EvidenceError(f"restricted-order:{expected_id}")
        worktree = safe_leaf(restricted_root, row["worktree"], directory=True)
        test_log = safe_leaf(restricted_root, row["test_log"])
        raw_log = test_log.read_bytes()
        if sha256(raw_log) != row["test_log_sha256"]:
            raise EvidenceError(f"{expected_id}:log-digest")
        profile_path = safe_leaf(restricted_root, row["profile_report"])
        profile_data, profile_raw = read_json(profile_path)
        if sha256(profile_raw) != row["profile_report_sha256"]:
            raise EvidenceError(f"{expected_id}:profile-report-digest")
        validate_profile_data(profile_data, expected_id)
        runner_binary = row["runner_binary"]
        if not isinstance(runner_binary, str):
            raise EvidenceError(f"{expected_id}:missing-runner-binary")
        binary_path = safe_leaf(restricted_root, runner_binary)
        expected_runner = (
            HISTORICAL_RUNNER if expected_id == "v2-c7be4039" else CURRENT_RUNNER
        )
        if sha256(binary_path.read_bytes()) != expected_runner["binary_sha256"]:
            raise EvidenceError(f"{expected_id}:runner-binary-digest")
        counts = parse_log(test_log)
        if counts != (row["passed"], row["failed"], row["skipped"]):
            raise EvidenceError(f"{expected_id}:log-counts")
        public = public_rows[expected_id]
        if counts != (
            public["tests"]["passed"],
            public["tests"]["failed"],
            public["tests"]["skipped"],
        ):
            raise EvidenceError(f"{expected_id}:public-counts")
        if row["duration_seconds"] != public["tests"]["duration_seconds"]:
            raise EvidenceError(f"{expected_id}:duration-drift")
        if row["test_log_sha256"] != public["tests"]["log_sha256"]:
            raise EvidenceError(f"{expected_id}:public-log-digest")
        expected = GROUPS[expected_id]
        head = run_git(worktree, "rev-parse", "HEAD")
        parent = run_git(worktree, "rev-parse", "HEAD^")
        if head != public["prepared_commit"] or parent != expected["source_commit"]:
            raise EvidenceError(f"{expected_id}:wrong-parent-or-head")
        run_git(worktree, "verify-commit", head)
        fingerprint = run_git(worktree, "log", "-1", "--format=%GF")
        if fingerprint != SIGNER:
            raise EvidenceError(f"{expected_id}:wrong-signer")
        changed = run_git(worktree, "diff", "--name-only", parent, head).splitlines()
        if changed != expected["changed"]:
            raise EvidenceError(f"{expected_id}:tree-parity")
        if run_git(worktree, "status", "--porcelain=v1"):
            raise EvidenceError(f"{expected_id}:dirty-worktree")
        row_raw = json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
        if sha256(row_raw) != public["restricted_evidence_sha256"]:
            raise EvidenceError(f"{expected_id}:restricted-row-digest")
    regressions = restricted_data["regressions"]
    if not isinstance(regressions, list) or [row.get("id") for row in regressions] != [
        "v1-escrow-oracle",
        "v1-legacy-failure-convention",
        "v2-timestamp-oracle",
        "v2-legacy-failure-convention",
        "v2-fixed-term-boundary",
        "v2-vendored-wrapper-suite",
    ]:
        raise EvidenceError("regression-inventory")
    for row in regressions:
        exact_keys(
            row,
            {"id", "parent_report", "parent_report_sha256", "prepared_report", "prepared_report_sha256"},
            f"regression:{row.get('id')}",
        )
        for path_field, digest_field in (
            ("parent_report", "parent_report_sha256"),
            ("prepared_report", "prepared_report_sha256"),
        ):
            path = safe_leaf(restricted_root, row[path_field])
            if sha256(path.read_bytes()) != row[digest_field]:
                raise EvidenceError(f"regression-digest:{row['id']}:{path_field}")
        parent_report = safe_leaf(restricted_root, row["parent_report"])
        prepared_report = safe_leaf(restricted_root, row["prepared_report"])
        _, parent_failures = parse_parent_red_log(parent_report)
        if parent_failures <= 0:
            raise EvidenceError(f"regression-parent-not-red:{row['id']}")
        prepared_passed, prepared_failed, prepared_skipped = parse_log(prepared_report)
        if prepared_passed <= 0 or prepared_failed != 0 or prepared_skipped != 0:
            raise EvidenceError(f"regression-prepared-not-green:{row['id']}")


def write_report(path: Path, report: dict[str, Any]) -> None:
    root = ROOT.resolve()
    parent = path.parent.resolve()
    if not parent.is_relative_to(root) or path.exists() and path.is_symlink():
        raise EvidenceError(f"unsafe-report-path:{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps(report, indent=2, sort_keys=True).encode() + b"\n"
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    finally:
        if os.path.exists(temporary_name):
            os.unlink(temporary_name)


def validate(manifest_path: Path) -> tuple[dict[str, Any], bytes]:
    manifest, raw = read_json(manifest_path)
    validate_public_data(manifest)
    return manifest, raw


def command_validate(args: argparse.Namespace) -> int:
    manifest, _ = validate(args.manifest)
    print(f"prepared-harnesses: valid groups={len(manifest['groups'])}")
    return 0


def command_conformance(args: argparse.Namespace) -> int:
    if args.candidate != "prepared-source-group" or args.criterion != "prepared-state":
        raise EvidenceError("unsupported-conformance-subject")
    manifest, manifest_raw = validate(args.manifest)
    restricted_path = safe_leaf(args.restricted_root, "evidence/prepared-state.json")
    restricted, restricted_raw = read_json(restricted_path)
    validate_restricted(manifest, args.restricted_root, restricted)
    report = {
        "schema": "protasis-conformance-report/v1",
        "candidate": args.candidate,
        "criterion": args.criterion,
        "status": "pass",
        "manifest": {
            "path": str(args.manifest.relative_to(ROOT)),
            "sha256": sha256(manifest_raw),
        },
        "restricted_evidence_sha256": sha256(restricted_raw),
        "group_count": len(GROUPS),
        "checks": [
            "exact-group-and-profile-set",
            "signed-child-commits",
            "fixed-seed-green-suites",
            "admitted-test-only-diffs",
            "clean-production-configuration-dependency-and-submodule-parity",
            "retained-parent-red-and-prepared-green-regressions",
            "public-private-payload-boundary",
        ],
        "failures": [],
    }
    write_report(args.report, report)
    print(f"prepared-state: pass groups={len(GROUPS)} report={args.report}")
    return 0


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(description=__doc__)
    commands = top.add_subparsers(dest="command", required=True)
    validate_parser = commands.add_parser("validate")
    validate_parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    validate_parser.set_defaults(handler=command_validate)
    conformance = commands.add_parser("conformance")
    conformance.add_argument("--candidate", required=True)
    conformance.add_argument("--criterion", required=True)
    conformance.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    conformance.add_argument("--restricted-root", type=Path, default=DEFAULT_RESTRICTED)
    conformance.add_argument("--report", type=Path, required=True)
    conformance.set_defaults(handler=command_conformance)
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.handler(args)
    except (EvidenceError, OSError, subprocess.SubprocessError) as exc:
        print(f"prepared-state refused: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
