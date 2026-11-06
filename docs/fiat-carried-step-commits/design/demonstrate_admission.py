#!/usr/bin/env python3
"""Show what the tree's own controller answers for a downward carry.

usage: demonstrate_admission.py --hexctl PATH

Builds a disposable three-step stack in a temporary Git repository, merges the
step 3 branch into the waiting step 2 branch, then calls the loaded controller's
`refuse_rewritten_stack` for a run whose current step is 1. The remote tip read
is pointed at the disposable repository's own refs; the native ancestry query
runs unchanged against real objects. The script prints `admitted` when the
guard returns without refusing and `refused: <text>` when it refuses. Exit 0
either way: the observation, not a verdict, is the output. It reads no
controller state and writes nothing.
"""

from __future__ import annotations

import argparse
import importlib.util
import io
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path
from unittest import mock

GIT_TIMEOUT = 30
BRANCHES = ("run-step-1", "run-step-2", "run-step-3")


def load_controller(path: Path):
    if path.is_symlink() or not path.is_file():
        raise SystemExit("--hexctl must name a regular file")
    specification = importlib.util.spec_from_file_location("hexctl_admission_demo", path)
    if specification is None or specification.loader is None:
        raise SystemExit("controller cannot be loaded")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


class Repo:
    def __init__(self, root: Path) -> None:
        executable = shutil.which("git", path=os.defpath)
        if executable is None:
            raise SystemExit("native git is not on the default path")
        self.executable = executable
        self.root = root
        self.serial = 0

    def git(self, *argv: str) -> str:
        self.serial += 1
        stamp = f"{1000000000 + self.serial} +0000"
        done = subprocess.run(
            [self.executable, "--no-replace-objects", *argv],
            cwd=self.root,
            env={
                "PATH": os.defpath,
                "LANG": "C",
                "LC_ALL": "C",
                "HOME": str(self.root),
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_AUTHOR_NAME": "Fixture",
                "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
                "GIT_COMMITTER_NAME": "Fixture",
                "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
                "GIT_AUTHOR_DATE": stamp,
                "GIT_COMMITTER_DATE": stamp,
            },
            capture_output=True,
            timeout=GIT_TIMEOUT,
            check=False,
        )
        if done.returncode != 0:
            raise SystemExit(f"fixture git {' '.join(argv)} failed with status {done.returncode}")
        return done.stdout.decode("ascii", "replace").strip()

    def commit(self, name: str) -> str:
        (self.root / f"{name}.txt").write_text(f"{name}\n", encoding="utf-8")
        self.git("add", f"{name}.txt")
        self.git("commit", "-q", "-m", name)
        return self.git("rev-parse", "HEAD")


def build(repo: Repo) -> dict:
    repo.git("init", "-q", "-b", "main")
    repo.git("config", "commit.gpgsign", "false")
    repo.commit("base")
    repo.git("checkout", "-q", "-b", "run")
    steps = []
    below = "run"
    for number, branch in enumerate(BRANCHES, start=1):
        repo.git("checkout", "-q", "-b", branch, below)
        commits = [repo.commit(f"s{number}a"), repo.commit(f"s{number}b")]
        steps.append({
            "n": number,
            "title": branch,
            "receipts": {"push": {
                "head_commit": commits[-1],
                "verified_commits": commits,
            }},
        })
        below = branch
    repo.git("checkout", "-q", BRANCHES[1])
    repo.git("merge", "-q", "--no-ff", "-m", "carry", BRANCHES[2])
    return {"integrate": {"merged": []}, "steps": steps}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--hexctl", required=True)
    args = parser.parse_args(argv)
    module = load_controller(Path(args.hexctl))
    with tempfile.TemporaryDirectory() as raw:
        repo = Repo(Path(raw))
        state = build(repo)
        tips = {branch: repo.git("rev-parse", f"refs/heads/{branch}") for branch in BRANCHES}
        recorded = state["steps"][1]["receipts"]["push"]["head_commit"]
        print(f"step 2 recorded head {recorded}")
        print(f"step 2 observed tip  {tips[BRANCHES[1]]}")
        print(f"step 3 recorded head {state['steps'][2]['receipts']['push']['head_commit']}")
        captured = io.StringIO()
        with mock.patch.object(
            module, "step_branch_name", side_effect=lambda _state, step: step["title"]
        ), mock.patch.object(
            module, "remote_branch_tip",
            side_effect=lambda _dir, branch, *rest, **kw: tips[branch],
        ), redirect_stderr(captured):
            try:
                module.refuse_rewritten_stack(raw, state, 1)
            except SystemExit:
                print(f"refused: {captured.getvalue().strip()}")
                return 0
    print("admitted: refuse_rewritten_stack returned for a waiting branch that gained step 3's receipted commits")
    return 0


if __name__ == "__main__":
    sys.exit(main())
