#!/usr/bin/env python3
"""Procrustes: fail-closed deployed-code-size evidence for one size class.

Gate 1 seals a green baseline of per-contract runtime and initcode sizes beside
the sources, storage layouts and method identifiers a later comparison needs.
The sealing, layout and selector machinery is Hermes's; this module owns the
size measurement and the limits it is measured against.
"""

from __future__ import annotations

import argparse
import datetime as dt
import inspect
import json
import os
import re
import sys
import uuid
from pathlib import Path
from typing import Any, Sequence

SCHEMA = "procrustes-run/v1"
SKILL_NAME = "procrustes"

# EIP-170 caps deployed runtime code; EIP-3860 caps the initcode that returns
# it. `forge build --sizes --json` reports both, and a contract can pass one
# and fail the other.
EIP170_RUNTIME_LIMIT = 24576
EIP3860_INITCODE_LIMIT = 49152

HERMES_SCRIPTS = Path(__file__).resolve().parents[2] / "hermes" / "scripts"

# Every name Procrustes takes from Hermes, with the signature it was written
# against. `test_procrustes.py` compares this map to the live module, so a
# Hermes change that moves one of these fails a test here rather than a run in
# somebody's repository.
PINNED_HERMES_SURFACE = {
    "utc_now": "() -> 'str'",
    "write_text": "(path: 'Path', text: 'str') -> 'None'",
    "write_json": "(path: 'Path', value: 'Any') -> 'None'",
    "read_json": "(path: 'Path') -> 'Any'",
    "run_command": (
        "(command: 'Sequence[str]', cwd: 'Path', log_path: 'Path', "
        "env: 'dict[str, str] | None' = None, echo: 'bool' = True) -> 'CommandResult'"
    ),
    "require_success": "(result: 'CommandResult', gate: 'int', description: 'str', exit_code: 'int') -> 'None'",
    "is_within": "(path: 'Path', parent: 'Path') -> 'bool'",
    "git": "(repo: 'Path', arguments: 'Sequence[str]', log_path: 'Path') -> 'CommandResult'",
    "require_git_repository": "(repo: 'Path', log_path: 'Path', gate: 'int' = 1) -> 'str'",
    "canonical_json": "(raw: 'str', description: 'str', gate: 'int', exit_code: 'int') -> 'tuple[Any, str]'",
    "parse_protected_contract": "(raw: 'str') -> 'dict[str, str]'",
    "snapshot_sources": "(repo: 'Path', run_dir: 'Path') -> 'dict[str, str]'",
    "inspect_layout": (
        "(repo: 'Path', run_dir: 'Path', contract: 'dict[str, str]', suffix: 'str', "
        "gate: 'int', exit_code: 'int') -> 'tuple[Path, Any]'"
    ),
    "inspect_methods": (
        "(repo: 'Path', run_dir: 'Path', contract: 'dict[str, str]', suffix: 'str', "
        "gate: 'int', exit_code: 'int') -> 'tuple[Path, Any]'"
    ),
    "forge_test_arguments": "(seed: 'str | None', excluded_paths: 'Sequence[str]') -> 'list[str]'",
    "artifact_hashes": "(run_dir: 'Path', paths: 'Iterable[Path]') -> 'dict[str, str]'",
}


def load_hermes():
    """Import the sibling Hermes harness, failing loudly when it is not there."""
    if str(HERMES_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(HERMES_SCRIPTS))
    try:
        import hermes  # noqa: PLC0415  (located at runtime beside this skill)
    except ImportError as exc:  # pragma: no cover - environment defect
        raise SystemExit(
            f"cannot import the Hermes harness from {HERMES_SCRIPTS}: {exc}"
        ) from exc
    return hermes


hermes = load_hermes()

CommandResult = hermes.CommandResult
GateFailure = hermes.GateFailure
SingleValueAction = hermes.SingleValueAction

utc_now = hermes.utc_now
write_text = hermes.write_text
write_json = hermes.write_json
read_json = hermes.read_json
run_command = hermes.run_command
require_success = hermes.require_success
is_within = hermes.is_within
require_git_repository = hermes.require_git_repository
canonical_json = hermes.canonical_json
parse_protected_contract = hermes.parse_protected_contract
snapshot_sources = hermes.snapshot_sources
inspect_layout = hermes.inspect_layout
inspect_methods = hermes.inspect_methods
forge_test_arguments = hermes.forge_test_arguments
artifact_hashes = hermes.artifact_hashes
git = hermes.git

# Forge keys each size row by contract name, and disambiguates a name that
# several files declare as `Name (path/to/File.sol)`. Both forms are legitimate
# and a real repository with a mock or an interface twin produces the second.
CONTRACT_KEY_RE = re.compile(
    r"^[A-Za-z_][A-Za-z0-9_]*(?: \((?!/)[A-Za-z0-9_./-]+\.sol\))?$"
)


def pinned_surface_drift() -> dict[str, str]:
    """Names whose live signature no longer matches the pinned one."""
    drift: dict[str, str] = {}
    for name, expected in sorted(PINNED_HERMES_SURFACE.items()):
        target = getattr(hermes, name, None)
        if target is None:
            drift[name] = "absent"
            continue
        actual = str(inspect.signature(target))
        if actual != expected:
            drift[name] = actual
    return drift


def default_evidence_dir(repo: Path) -> Path:
    codex_root = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))).expanduser()
    stamp = dt.datetime.now().strftime("%Y%m%dT%H%M%S")
    return codex_root / "procrustes-runs" / f"{repo.name}-{stamp}-{uuid.uuid4().hex[:8]}"


def prepare_evidence_dir(repo: Path, requested: str | None) -> Path:
    run_dir = Path(requested).expanduser().resolve() if requested else default_evidence_dir(repo).resolve()
    if is_within(run_dir, repo):
        raise GateFailure(1, "evidence directory must be outside the target repository", 10)
    if run_dir.exists() and any(run_dir.iterdir()):
        raise GateFailure(1, f"evidence directory is not empty: {run_dir}", 10)
    run_dir.mkdir(parents=True, exist_ok=True)
    return run_dir


def mark_failure(run_dir: Path | None, state: dict[str, Any] | None, failure: GateFailure) -> None:
    """Write the refusal into the evidence directory before the process ends."""
    if run_dir is None:
        return
    result = {
        "schema": SCHEMA,
        "skill": SKILL_NAME,
        "status": "rejected",
        "failed_gate": failure.gate,
        "exit_code": failure.exit_code,
        "reason": str(failure),
        "finished_at": utc_now(),
    }
    write_json(run_dir / "result.json", result)
    if state is not None:
        state["status"] = "rejected"
        state["result"] = result
        write_json(run_dir / "state.json", state)


def require_clean_tree(repo: Path, run_dir: Path, gate: int, exit_code: int) -> None:
    result = git(repo, ["status", "--porcelain"], run_dir / "logs" / f"gate{gate}.git-status.log")
    require_success(result, gate, "git status --porcelain", exit_code)
    if result.stdout.strip():
        raise GateFailure(gate, "target repository has uncommitted changes", exit_code)


def parse_size_report(raw: str, gate: int, exit_code: int) -> dict[str, dict[str, int]]:
    """Read `forge build --sizes --json` into a contract-keyed size map.

    Forge prints one JSON object per contract name, each carrying a runtime and
    an initcode size. Anything else is a refusal rather than a partial parse:
    a size this harness guessed is worse than no size at all.
    """
    value, _ = canonical_json(raw, "forge build --sizes --json", gate, exit_code)
    if not isinstance(value, dict) or not value:
        raise GateFailure(gate, "forge build --sizes --json returned no contract sizes", exit_code)
    sizes: dict[str, dict[str, int]] = {}
    for name, entry in value.items():
        if not isinstance(name, str) or not CONTRACT_KEY_RE.fullmatch(name):
            raise GateFailure(gate, f"unexpected contract name in size report: {name!r}", exit_code)
        if not isinstance(entry, dict):
            raise GateFailure(gate, f"size report entry for {name} is not an object", exit_code)
        runtime = entry.get("runtime_size")
        initcode = entry.get("init_size")
        if not isinstance(runtime, int) or not isinstance(initcode, int):
            raise GateFailure(
                gate,
                f"size report for {name} lacks integer runtime_size and init_size",
                exit_code,
            )
        if runtime < 0 or initcode < 0:
            raise GateFailure(gate, f"negative size reported for {name}", exit_code)
        # Forge reports its own margins. They are recomputed here rather than
        # trusted, and a disagreement means Forge is measuring against a
        # different limit than this harness claims to enforce.
        for field, size, limit in (
            ("runtime_margin", runtime, EIP170_RUNTIME_LIMIT),
            ("init_margin", initcode, EIP3860_INITCODE_LIMIT),
        ):
            reported = entry.get(field)
            if isinstance(reported, int) and reported != limit - size:
                raise GateFailure(
                    gate,
                    f"forge reports {field} {reported} for {name}, which is not "
                    f"{limit} - {size}: the toolchain is measuring against a "
                    f"different code-size limit",
                    exit_code,
                )
        sizes[name] = {
            "runtime_size": runtime,
            "init_size": initcode,
            "runtime_margin": EIP170_RUNTIME_LIMIT - runtime,
            "init_margin": EIP3860_INITCODE_LIMIT - initcode,
        }
    return sizes


def match_size_targets(
    sizes: dict[str, dict[str, int]], targets: Sequence[str], gate: int, exit_code: int
) -> dict[str, list[str]]:
    """Resolve each declared target expression to the contracts it names."""
    matched: dict[str, list[str]] = {}
    for expression in targets:
        try:
            pattern = re.compile(expression)
        except re.error as exc:
            raise GateFailure(gate, f"invalid --size-target expression {expression!r}: {exc}", exit_code) from exc
        names = sorted(name for name in sizes if pattern.search(name))
        if not names:
            raise GateFailure(gate, f"--size-target {expression!r} matched no compiled contract", exit_code)
        matched[expression] = names
    return matched


def over_limit(sizes: dict[str, dict[str, int]]) -> dict[str, dict[str, int]]:
    """Contracts already past either limit, recorded rather than refused.

    A contract over EIP-170 is the reason somebody runs this harness, so the
    baseline states the fact and leaves the judgement to the candidate gates.
    """
    return {
        name: entry
        for name, entry in sorted(sizes.items())
        if entry["runtime_size"] > EIP170_RUNTIME_LIMIT or entry["init_size"] > EIP3860_INITCODE_LIMIT
    }


def baseline_command(args: argparse.Namespace) -> int:
    repo = Path(args.repo).expanduser().resolve()
    run_dir: Path | None = None
    state: dict[str, Any] | None = None
    try:
        if not repo.is_dir():
            raise GateFailure(1, f"target repository is not a directory: {repo}", 10)
        if not (repo / "foundry.toml").is_file():
            raise GateFailure(1, f"no foundry.toml at the target root: {repo}", 10)
        run_dir = prepare_evidence_dir(repo, args.evidence_dir)

        protected = list(args.protected_contract or [])
        if not protected and not args.assert_no_protected_contracts:
            raise GateFailure(
                1,
                "name every frozen layout with --protected-contract, or state "
                "there are none with --assert-no-protected-contracts",
                10,
            )
        if protected and args.assert_no_protected_contracts:
            raise GateFailure(1, "--assert-no-protected-contracts contradicts --protected-contract", 10)

        revision = require_git_repository(repo, run_dir / "logs" / "gate1.git-revision.log")
        require_clean_tree(repo, run_dir, 1, 10)

        version = run_command(
            ["forge", "--version"], repo, run_dir / "logs" / "gate1.forge-version.log", echo=False
        )
        require_success(version, 1, "forge --version", 10)
        config = run_command(
            ["forge", "config", "--json"], repo, run_dir / "logs" / "gate1.forge-config.log", echo=False
        )
        require_success(config, 1, "forge config --json", 10)
        _, canonical_config = canonical_json(config.stdout, "forge config --json", 1, 10)
        write_text(run_dir / "foundry-config.json", canonical_config)

        report = run_command(
            ["forge", "build", "--sizes", "--json"],
            repo,
            run_dir / "logs" / "gate1.forge-sizes.log",
            echo=False,
        )
        require_success(report, 1, "forge build --sizes --json", 10)
        sizes = parse_size_report(report.stdout, 1, 10)
        matched = match_size_targets(sizes, args.size_target, 1, 10)
        write_json(
            run_dir / "sizes.json",
            {
                "schema": SCHEMA,
                "limits": {
                    "eip170_runtime": EIP170_RUNTIME_LIMIT,
                    "eip3860_initcode": EIP3860_INITCODE_LIMIT,
                },
                "sizes": sizes,
                "targets": matched,
                "over_limit": over_limit(sizes),
            },
        )

        manifest = snapshot_sources(repo, run_dir)

        layouts: dict[str, str] = {}
        methods: dict[str, str] = {}
        for contract in protected:
            layout_path, _ = inspect_layout(repo, run_dir, contract, "baseline", 1, 10)
            method_path, _ = inspect_methods(repo, run_dir, contract, "baseline", 1, 10)
            layouts[contract["label"]] = str(layout_path.relative_to(run_dir))
            methods[contract["label"]] = str(method_path.relative_to(run_dir))

        test_arguments = forge_test_arguments(args.fuzz_seed, args.no_match_path or [])
        tests = run_command(
            ["forge", "test", *test_arguments], repo, run_dir / "logs" / "gate1.forge-test.log"
        )
        require_success(tests, 1, "forge test", 10)

        state = {
            "schema": SCHEMA,
            "skill": SKILL_NAME,
            "status": "sealed",
            "gate": 1,
            "repo": str(repo),
            "revision": revision,
            "forge_version": version.stdout.strip(),
            "fuzz_seed": args.fuzz_seed,
            "excluded_paths": list(args.no_match_path or []),
            "protected_contracts": protected,
            "size_targets": list(args.size_target),
            "matched_targets": matched,
            "storage_layouts": layouts,
            "method_identifiers": methods,
            "source_count": len(manifest),
            "sealed_at": utc_now(),
        }
        state["artifacts"] = artifact_hashes(
            run_dir,
            [
                run_dir / "sizes.json",
                run_dir / "foundry-config.json",
                run_dir / "baseline-source-manifest.json",
            ],
        )
        write_json(run_dir / "state.json", state)
        write_json(
            run_dir / "result.json",
            {
                "schema": SCHEMA,
                "skill": SKILL_NAME,
                "status": "sealed",
                "gate": 1,
                "revision": revision,
                "size_targets": list(args.size_target),
                "over_limit": sorted(over_limit(sizes)),
                "finished_at": utc_now(),
            },
        )
        print(f"sealed baseline at {run_dir}")
        for expression, names in matched.items():
            for name in names:
                entry = sizes[name]
                print(
                    f"  {name}: runtime {entry['runtime_size']} "
                    f"(margin {entry['runtime_margin']}), initcode {entry['init_size']} "
                    f"(margin {entry['init_margin']})  [{expression}]"
                )
        return 0
    except GateFailure as failure:
        mark_failure(run_dir, state, failure)
        print(f"gate {failure.gate} refused: {failure}", file=sys.stderr)
        return failure.exit_code


def status_command(args: argparse.Namespace) -> int:
    run_dir = Path(args.run_dir).expanduser().resolve()
    result = run_dir / "result.json"
    if not result.is_file():
        print(f"no result.json in {run_dir}", file=sys.stderr)
        return 10
    print(json.dumps(read_json(result), indent=2, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="procrustes",
        description="Fail-closed deployed-code-size evidence against EIP-170 and EIP-3860.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    baseline = subparsers.add_parser("baseline", help="Run Gate 1 and seal size baseline evidence")
    baseline.add_argument("--repo", required=True, action=SingleValueAction, help="Foundry repository root")
    baseline.add_argument(
        "--evidence-dir", action=SingleValueAction, help="Empty evidence directory outside the repository"
    )
    baseline.add_argument(
        "--size-target",
        action="append",
        required=True,
        metavar="REGEX",
        help="Contract-name expression that must carry a measured reduction; repeatable",
    )
    baseline.add_argument(
        "--protected-contract",
        action="append",
        type=parse_protected_contract,
        metavar="LABEL=PATH:CONTRACT",
        help="Frozen storage layout and selector set; repeatable",
    )
    baseline.add_argument(
        "--assert-no-protected-contracts",
        action="store_true",
        help="State explicitly that no frozen layout is in scope",
    )
    baseline.add_argument(
        "--no-match-path", action="append", metavar="GLOB", help="Forge test exclusion; repeatable"
    )
    baseline.add_argument(
        "--fuzz-seed", action=SingleValueAction, help="Pinned Foundry fuzz seed for the behaviour suite"
    )
    baseline.set_defaults(handler=baseline_command)

    status = subparsers.add_parser("status", help="Print the run's result JSON")
    status.add_argument("--run-dir", required=True, action=SingleValueAction)
    status.set_defaults(handler=status_command)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    drift = pinned_surface_drift()
    if drift:
        print(
            "the Hermes harness moved under Procrustes: "
            + ", ".join(f"{name} is now {signature}" for name, signature in drift.items()),
            file=sys.stderr,
        )
        return 70
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
