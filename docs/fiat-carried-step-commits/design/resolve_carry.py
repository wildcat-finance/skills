#!/usr/bin/env python3
"""Measure one design candidate against one selection criterion.

Issue wildcat-finance/skills#1480: a later Fiat step's receipted commits can be
merged into a lower step branch and the integrate phase admits the movement.
Each candidate below is a reference decision procedure for the pre-merge check
that `hexctl next` would run. It is evaluated over a disposable Git repository
that holds a three-step stack and one named specimen movement, so every value
in a report is measured from real Git objects rather than asserted.

The procedures model the candidate constructions named in the study. They are
not the product controller, and a passing cell here establishes only that the
construction answers the specimen as the criterion requires.

usage: resolve_carry.py --candidate ID --criterion ID --out PATH

`--out` is required, must not exist, must end in `.json`, and may not name a
controller file. Nothing else is written. No network is used and no shell is
spawned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCHEMA = "protasis-design-report/v1"
CONTROLLER_FILES = frozenset({"state.json", "ledger.jsonl", "lock"})
GIT_OUTPUT_MAX = 2 * 1024 * 1024
GIT_PATHS_MAX = 500
GIT_TIMEOUT = 30
STEP_BRANCHES = ("run-step-1", "run-step-2", "run-step-3")
RUN_BRANCH = "run"
MISSING_OBJECT = "f" * 40

CANDIDATES = (
    "gained-range-ownership",
    "owned-commit-ancestry",
    "pull-request-merge-state",
    "merge-time-only",
)

CRITERIA = {
    "refuses-whole-carry": ("boolean", ("whole-carry-current", "whole-carry-waiting"), "carried"),
    "refuses-partial-carry": ("boolean", ("partial-carry",), "carried"),
    "admits-honest-extension": ("boolean", ("honest-extension", "healthy"), "admit"),
    "admits-adopted-early-merge": ("boolean", ("adopted-early-merge",), "admit"),
    "no-new-github-reads": ("boolean", ("whole-carry-current",), None),
    # The time metric is measured on the healthy stack: that is the path every
    # `next` in a healthy integrate pays, whereas a carry ends at the first hit.
    "added-native-processes-per-next": ("count", ("healthy",), None),
    "max-child-output-bytes": ("bytes", ("whole-carry-current", "healthy"), None),
    "unknown-refuses-as-unknown": ("boolean", ("unknown-object",), "unknown"),
}


class Git:
    """Bounded native Git over one disposable repository, counting processes."""

    def __init__(self, root: Path) -> None:
        executable = shutil.which("git", path=os.defpath)
        if executable is None:
            raise SystemExit("native git is not on the default path")
        self.executable = executable
        self.root = root
        self.processes = 0
        self.max_output = 0
        self.serial = 0

    def environment(self) -> dict[str, str]:
        self.serial += 1
        stamp = f"{1000000000 + self.serial} +0000"
        return {
            "PATH": os.defpath,
            "LANG": "C",
            "LC_ALL": "C",
            "HOME": str(self.root),
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_AUTHOR_NAME": "Fixture",
            "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
            "GIT_COMMITTER_NAME": "Fixture",
            "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
            "GIT_AUTHOR_DATE": stamp,
            "GIT_COMMITTER_DATE": stamp,
        }

    def run(self, *argv: str, count: bool = False) -> tuple[int | None, str]:
        """Run one fixed argv; return (status, stdout) with status None on failure."""
        if count:
            self.processes += 1
        try:
            done = subprocess.run(
                [self.executable, "--no-replace-objects", *argv],
                cwd=self.root,
                env=self.environment(),
                capture_output=True,
                timeout=GIT_TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None, ""
        if len(done.stdout) > GIT_OUTPUT_MAX:
            return None, ""
        if count:
            self.max_output = max(self.max_output, len(done.stdout))
        return done.returncode, done.stdout.decode("ascii", "replace")

    def must(self, *argv: str) -> str:
        status, out = self.run(*argv)
        if status != 0:
            raise SystemExit(f"fixture git {' '.join(argv)} failed with status {status}")
        return out.strip()

    def commit(self, name: str) -> str:
        (self.root / f"{name}.txt").write_text(f"{name}\n", encoding="utf-8")
        self.must("add", f"{name}.txt")
        self.must("commit", "-q", "-m", name)
        return self.must("rev-parse", "HEAD")


def build_stack(git: Git) -> dict:
    """A run branch and three chained step branches with two commits each."""
    git.must("init", "-q", "-b", "main")
    git.must("config", "commit.gpgsign", "false")
    git.commit("base")
    git.must("checkout", "-q", "-b", RUN_BRANCH)
    steps = []
    below = RUN_BRANCH
    for number, branch in enumerate(STEP_BRANCHES, start=1):
        git.must("checkout", "-q", "-b", branch, below)
        commits = [git.commit(f"s{number}a"), git.commit(f"s{number}b")]
        steps.append({
            "n": number,
            "branch": branch,
            "pr_base": below,
            "receipts": {"push": {
                "head_commit": commits[-1],
                "verified_commits": list(commits),
                "early_merge": None,
            }},
            "pull_request": {"merged": False, "base": below},
        })
        below = branch
    return {"steps": steps, "merged": [], "current": 1, "tips": {}}


def apply_specimen(git: Git, state: dict, specimen: str) -> None:
    steps = state["steps"]
    if specimen == "healthy":
        return
    if specimen == "whole-carry-current":
        git.must("checkout", "-q", STEP_BRANCHES[0])
        git.must("merge", "-q", "--no-ff", "-m", "carry", STEP_BRANCHES[2])
    elif specimen == "whole-carry-waiting":
        git.must("checkout", "-q", STEP_BRANCHES[1])
        git.must("merge", "-q", "--no-ff", "-m", "carry", STEP_BRANCHES[2])
    elif specimen == "partial-carry":
        first = steps[2]["receipts"]["push"]["verified_commits"][0]
        git.must("checkout", "-q", STEP_BRANCHES[0])
        git.must("merge", "-q", "--no-ff", "-m", "partial", first)
    elif specimen == "honest-extension":
        git.must("checkout", "-q", STEP_BRANCHES[1])
        git.commit("fix")
    elif specimen == "adopted-early-merge":
        git.must("checkout", "-q", STEP_BRANCHES[1])
        git.must("merge", "-q", "--no-ff", "-m", "early", STEP_BRANCHES[2])
        merge = git.must("rev-parse", "HEAD")
        steps[2]["receipts"]["push"]["early_merge"] = {
            "merge_commit": merge,
            "reachable_from": STEP_BRANCHES[1],
        }
        steps[2]["pull_request"] = {"merged": True, "base": STEP_BRANCHES[1]}
    elif specimen == "unknown-object":
        state["tips"][STEP_BRANCHES[1]] = MISSING_OBJECT
    else:
        raise SystemExit(f"unknown specimen {specimen}")


def read_tip(git: Git, state: dict, branch: str) -> str:
    """The remote tip read, modelled as one native ref read on this repository."""
    if branch in state["tips"]:
        git.processes += 1
        return state["tips"][branch]
    status, out = git.run("rev-parse", "--verify", f"refs/heads/{branch}", count=True)
    if status != 0:
        raise SystemExit(f"fixture branch {branch} cannot be read")
    return out.strip()


def unmerged(state: dict) -> list[dict]:
    return [step for step in state["steps"] if step["n"] not in state["merged"]]


def ownership(state: dict, exclude: dict) -> set[str]:
    owned: set[str] = set()
    for step in state["steps"]:
        if step is exclude:
            continue
        push = step["receipts"]["push"]
        if push.get("early_merge"):
            continue
        commits = push.get("verified_commits")
        if isinstance(commits, list) and commits:
            owned.update(commits)
        elif isinstance(push.get("head_commit"), str):
            owned.add(push["head_commit"])
    return owned


def existing_waiting_guard(git: Git, state: dict, step: dict, recorded: str, tip: str):
    """The neighbouring guard that is already on main; not counted as added."""
    git.processes -= 1
    status, _ = git.run("merge-base", "--is-ancestor", recorded, tip, count=True)
    if status not in (0, 1):
        return "unknown"
    if status == 1:
        return "rewritten"
    return None


def candidate_gained_range_ownership(git: Git, state: dict) -> tuple[str, int]:
    baseline = git.processes
    for step in unmerged(state):
        recorded = step["receipts"]["push"]["head_commit"]
        tip = read_tip(git, state, step["branch"])
        if step["n"] != state["current"]:
            # The waiting tip read and its ancestry query already run on main.
            git.processes -= 1
            if tip == recorded:
                continue
            verdict = existing_waiting_guard(git, state, step, recorded, tip)
            if verdict is not None:
                return verdict, 0
        elif tip == recorded:
            continue
        status, out = git.run(
            "rev-list", f"--max-count={GIT_PATHS_MAX + 1}", f"{recorded}..{tip}", count=True
        )
        if status != 0:
            return "unknown", 0
        gained = {line.strip() for line in out.splitlines() if line.strip()}
        if len(gained) > GIT_PATHS_MAX:
            return "unknown", 0
        if gained & ownership(state, step):
            return "carried", 0
    return "admit", 0


def candidate_owned_commit_ancestry(git: Git, state: dict) -> tuple[str, int]:
    steps = unmerged(state)
    for lower in steps:
        tip = read_tip(git, state, lower["branch"])
        if lower["n"] != state["current"]:
            git.processes -= 1
        for higher in steps:
            if higher["n"] <= lower["n"]:
                continue
            push = higher["receipts"]["push"]
            if push.get("early_merge"):
                continue
            for commit in push["verified_commits"]:
                status, _ = git.run("merge-base", "--is-ancestor", commit, tip, count=True)
                if status not in (0, 1):
                    return "unknown", 0
                if status == 0:
                    return "carried", 0
    return "admit", 0


def candidate_pull_request_merge_state(git: Git, state: dict) -> tuple[str, int]:
    reads = 0
    for step in unmerged(state):
        reads += 1
        record = step["pull_request"]
        adopted = step["receipts"]["push"].get("early_merge")
        if record["merged"] and record["base"] != RUN_BRANCH and not adopted:
            return "carried", reads
    return "admit", reads


def candidate_merge_time_only(git: Git, state: dict) -> tuple[str, int]:
    return "admit", 0


PROCEDURES = {
    "gained-range-ownership": candidate_gained_range_ownership,
    "owned-commit-ancestry": candidate_owned_commit_ancestry,
    "pull-request-merge-state": candidate_pull_request_merge_state,
    "merge-time-only": candidate_merge_time_only,
}


def evaluate(candidate: str, specimen: str) -> dict:
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        git = Git(root)
        state = build_stack(git)
        apply_specimen(git, state, specimen)
        git.processes = 0
        git.max_output = 0
        verdict, github_reads = PROCEDURES[candidate](git, state)
        return {
            "verdict": verdict,
            "processes": git.processes,
            "github_reads": github_reads,
            "max_output": git.max_output,
        }


def measure(candidate: str, criterion: str):
    unit, specimens, expected = CRITERIA[criterion]
    observations = [evaluate(candidate, specimen) for specimen in specimens]
    if criterion == "no-new-github-reads":
        return unit, all(item["github_reads"] == 0 for item in observations)
    if criterion == "added-native-processes-per-next":
        return unit, max(item["processes"] for item in observations)
    if criterion == "max-child-output-bytes":
        return unit, max(item["max_output"] for item in observations)
    return unit, all(item["verdict"] == expected for item in observations)


def checked_out(path_text: str) -> Path:
    path = Path(path_text)
    if path.suffix != ".json" or path.name in CONTROLLER_FILES:
        raise SystemExit("--out must name a new .json report, not a controller file")
    if path.exists() or path.is_symlink():
        raise SystemExit("--out must not already exist")
    if not path.parent.is_dir():
        raise SystemExit("--out parent directory does not exist")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=sorted(CRITERIA))
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    out = checked_out(args.out)
    unit, value = measure(args.candidate, args.criterion)
    report = {
        "schema": SCHEMA,
        "candidate": args.candidate,
        "criterion": args.criterion,
        "value": value,
        "unit": unit,
        "command": (
            f"python3 {sys.argv[0]} --candidate {args.candidate} "
            f"--criterion {args.criterion} --out {args.out}"
        ),
        "exit": 0,
    }
    data = (json.dumps(report, sort_keys=True) + "\n").encode("ascii")
    with open(out, "xb") as handle:
        handle.write(data)
    print(f"{out} {hashlib.sha256(data).hexdigest()} value={value!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
