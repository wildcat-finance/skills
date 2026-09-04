"""The fixture every hexctl test runs on: a real repository, a fake delivery tool.

This is the harness `test_hexctl.py` was built around, moved out from under it.
The bounded-read limit that file is held to is per file, and it had reached 144
bytes of headroom -- about two lines -- while carrying a 32 KB fixture holding
no tests of its own. Nothing here is cited as coverage evidence, so moving it
re-points no selector.

`HexctlCase` is imported by `test_hexctl`, which re-exports it, and through that
module by `test_fiat_skill`, `test_hexctl_frontier_receipt`, and the case
builders that take a namespace. Import it from either; they are the same object.
"""

import argparse
import glob
import json
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import ExitStack, redirect_stderr
from io import BytesIO, StringIO, TextIOWrapper
from pathlib import Path
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
HEXCTL = os.path.join(HERE, "..", "skills", "fiat", "scripts", "hexctl.py")
AUDIT_SYNOPSIS = os.path.join(
    HERE, "..", "skills", "fiat", "scripts", "audit_synopsis.py"
)
PROTASIS = os.path.join(HERE, "..", "skills", "protasis", "scripts", "protasis.py")
COMPLETE_STUDY = os.path.join(HERE, "fixtures", "protasis", "complete-study.md")

SUITE = '["hexaemeron:x-ray", "hexaemeron:solidity-auditor"]'
"""A security_suite receipt shaped like the one preflight records.

These tests used the string "suite", which is neither a waiver nor a list of ids. The
round classifier reads it as a receipt it cannot make sense of, and demands the lint
results, which is the right answer for a receipt like that and the wrong fixture for a
test about a Solidity round.
"""

LINTS_CLEAN = ("--phylax-exit", "0", "--ephoros-exit", "0", "--hypomnema-exit", "0")
"""What a non-Solidity round records when all three lints came back clean."""

AUDIT_FILTER = ("--audit-filter", "sapheneia:sapheneia")
"""The exact checked operator declaration every new audit round owes."""


def make_origin_checkout(path):
    """A real repository on `main` at `path`.

    `init` creates a worktree, so every fixture it runs against has to be a real
    repository. The fake git covers signatures, refs and pull requests; it cannot
    stand in for repository structure.
    """
    for argv in (
        ["init", "-q", "-b", "main"],
        ["config", "--local", "commit.gpgsign", "false"],
        ["config", "user.email", "fixture@example.invalid"],
        ["config", "user.name", "Fixture"],
        ["commit", "-q", "--allow-empty", "-m", "base"],
    ):
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *argv],
            cwd=path,
            check=True,
            capture_output=True,
        )


def run_target(base_dir):
    """Where a run started in `base_dir` keeps its state.

    `init` prints the run worktree and tells the caller to pass it as `--dir`.
    The tests follow the same breadcrumb rather than reaching past it, so they
    exercise the arrangement an operator actually gets.
    """
    crumb = os.path.join(base_dir, ".hexaemeron", "worktree")
    try:
        with open(crumb, encoding="utf-8") as handle:
            recorded = handle.read().strip()
    except OSError:
        return base_dir
    if recorded and os.path.exists(os.path.join(recorded, ".hexaemeron", "state.json")):
        return recorded
    return base_dir


class OriginCheckoutMixin:
    """A `target` that follows the run into its worktree."""

    @property
    def target(self):
        return run_target(self.dir)


def hexctl_module():
    """The controller imported as a module.

    Every other test here drives the CLI, which is the surface the skill uses. The
    round classifier has no CLI of its own -- it decides what `audit-round` demands --
    so it is exercised directly rather than through a command that would only report
    it indirectly.
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("hexctl_under_test", HEXCTL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def audit_synopsis_module():
    """The sibling renderer imported under the controller test runner."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "audit_synopsis_under_test", AUDIT_SYNOPSIS
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def protasis_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("protasis_under_test", PROTASIS)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class HexctlCase(OriginCheckoutMixin, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.processes = []
        self.env = os.environ.copy()
        self.fake_refs = {}
        self.fake_prs = {}
        self.fake_parents = {}
        self.install_fake_delivery_tools()
        make_origin_checkout(self.dir)


    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        self.tmp.cleanup()

    def run_ctl(
        self, *args, expect=0, audit_filter=True, prose_inventory=True
    ):
        if (
            args
            and args[0] == "audit-round"
            and audit_filter
            and "--audit-filter" not in args
        ):
            args = (*args, *AUDIT_FILTER)
        if (
            args[:1] == ("audit-round",)
            and prose_inventory
            and "--no-prose-writes" in Path(HEXCTL).read_text(encoding="utf-8")
            and "--findings" in args
            and args[args.index("--findings") + 1] == "0"
            and "--prose-writable" not in args
            and "--no-prose-writes" not in args
        ):
            args = (*args, "--no-prose-writes")
        pending_refs = dict(self.fake_refs)
        pending_prs = json.loads(json.dumps(self.fake_prs))
        pending_parents = json.loads(json.dumps(self.fake_parents))
        pending_tree = json.loads(
            self.env.get("FAKE_GIT_TREE_BY_COMMIT", "{}")
        )
        pending_diffs = json.loads(
            self.env.get("FAKE_GIT_DIFF_PATHS", "{}")
        )
        pending_audit_baseline = None
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        state = None
        if os.path.exists(state_path):
            try:
                with open(state_path, encoding="utf-8") as handle:
                    state = json.load(handle)
            except (OSError, ValueError):
                state = None
        if (
            args[:2] == ("done", "runbook")
            and state is not None
            and getattr(self, "auto_design_lock", True)
        ):
            design = (
                state.get("receipts", {})
                .get("study", {})
                .get("design_evidence")
            )
            if isinstance(design, dict):
                artifact = args[args.index("--artifact") + 1]
                path = artifact if os.path.isabs(artifact) else os.path.join(self.target, artifact)
                with open(path, encoding="utf-8") as handle:
                    source = handle.read()
                if "```design-lock" not in source:
                    with open(path, "w", encoding="utf-8") as handle:
                        handle.write(self.design_lock_block(state) + "\n" + source)
        if (
            args[:1] == ("audit-round",)
            and expect == 0
            and getattr(self, "auto_audit_records", True)
        ):
            self.append_valid_audit_record(args, state)
        if args[:2] == ("done", "implement") and expect == 0:
            branch = args[args.index("--branch") + 1]
            head = args[args.index("--commit") + 1]
            pending_refs[branch] = self.fake_sha(head)
            if state is not None:
                relative = state["config"]["audit"]["log_path"]
                log = Path(self.target, *relative.split("/"))
                pending_audit_baseline = log.read_bytes() if log.exists() else b""
        if args[:2] == ("done", "prose") and state is not None:
            step = state["steps"][state["current_step"] - 1]
            branch = step["receipts"]["implement"]["branch"]
            override = getattr(self, "next_prose_head", None)
            if override is not None:
                del self.next_prose_head
                prose_head = self.fake_sha(override)
            else:
                prose_head = self.fake_sha(f"head{step['n']}")
            pending_refs[branch] = prose_head
            final_round = step["audit"]["rounds"][-1]
            log_path = final_round["log"]
            synopsis_path = (
                os.path.join(os.path.dirname(log_path), "AUDIT_SYNOPSIS.md")
                if os.path.basename(log_path) == "AUDIT.md"
                else os.path.splitext(log_path)[0] + ".synopsis.md"
            )
            pending_tree.setdefault(prose_head, {}).update({
                log_path: Path(self.target, *log_path.split("/")).read_bytes().hex(),
                synopsis_path: Path(
                    self.target, *synopsis_path.split("/")
                ).read_bytes().hex(),
            })
            declaration = final_round.get("prose_writable", {})
            declared_paths = [
                row["path"] for row in declaration.get("paths", [])
            ]
            tree_absent = set(
                getattr(self, "next_prose_tree_absent_paths", [])
            )
            if hasattr(self, "next_prose_tree_absent_paths"):
                del self.next_prose_tree_absent_paths
            for relative in declared_paths:
                candidate = Path(self.target, *relative.split("/"))
                pending_tree[prose_head][relative] = (
                    candidate.read_bytes().hex()
                    if relative not in tree_absent
                    and candidate.is_file()
                    and not candidate.is_symlink()
                    else None
                )
            source_commit = declaration.get("source_commit")
            if source_commit:
                extra = list(getattr(self, "next_prose_changed_paths", []))
                if hasattr(self, "next_prose_changed_paths"):
                    del self.next_prose_changed_paths
                pending_diffs[f"{source_commit}..{prose_head}"] = (
                    [] if source_commit == prose_head else sorted(set(
                        [log_path, synopsis_path, *declared_paths, *extra]
                    ))
                )
        if args[:2] == ("done", "push") and expect == 0 and state is not None:
            step = state["steps"][state["current_step"] - 1]
            branch = step["receipts"]["implement"]["branch"]
            head = args[args.index("--head-commit") + 1]
            base = args[args.index("--pr-base") + 1] if "--pr-base" in args else state["base"]
            url = args[args.index("--pr-url") + 1]
            pending_refs[branch] = self.fake_sha(head)
            merge = args[args.index("--merge-commit") + 1] if "--merge-commit" in args else None
            pending_prs[url] = self.fake_pr(
                url, branch, base, self.fake_sha(head), merge
            )
        if args[:2] == ("done", "merge-step") and expect == 0 and state is not None:
            number = int(args[args.index("--step") + 1])
            url = state["steps"][number - 1]["receipts"]["push"]["pr_url"]
            merge = args[args.index("--merge-commit") + 1]
            pending_prs[url]["state"] = "closed"
            pending_prs[url]["merged"] = True
            pending_prs[url]["merge_commit_sha"] = merge
            pending_refs[state["run_branch"]] = merge
            if number < len(state["steps"]):
                next_push = state["steps"][number]["receipts"].get("push", {})
                next_url = next_push.get("pr_url")
                if next_url in pending_prs:
                    pending_prs[next_url]["base"]["ref"] = state["run_branch"]
        if args[:2] == ("done", "integrate") and expect == 0 and state is not None:
            url = args[args.index("--pr-url") + 1]
            merge = args[args.index("--merge-commit") + 1]
            head = pending_refs.get(state["run_branch"], self.fake_sha(state["run_branch"]))
            body = "Delivery evidence."
            match = re.fullmatch(
                r"https://github\.com/([^/]+/[^/]+)/issues/([1-9][0-9]*)/?",
                state["receipts"].get("task_issue") or "",
            )
            if match is not None:
                body += f"\n\nCloses {match.group(1)}#{match.group(2)}"
            body += "\n\n<!-- wildcat-origin: shoggoth -->"
            pending_prs[url] = self.fake_pr(
                url, state["run_branch"], self.integration_base(state), head, merge,
                body=body,
            )
        env = dict(self.env)
        env["FAKE_GIT_REFS"] = json.dumps(pending_refs)
        env["FAKE_GIT_PARENTS"] = json.dumps(pending_parents)
        env["FAKE_GH_PRS"] = json.dumps(pending_prs)
        env["FAKE_GIT_TREE_BY_COMMIT"] = json.dumps(pending_tree)
        env["FAKE_GIT_DIFF_PATHS"] = json.dumps(pending_diffs)
        audit_baseline = getattr(self, "fake_audit_baseline", None)
        if (
            args[:1] == ("audit-round",)
            and audit_baseline is not None
            and "FAKE_GIT_BASELINE_HEX" not in env
        ):
            env["FAKE_GIT_BASELINE_HEX"] = audit_baseline.hex()
        proc = subprocess.run(
            [sys.executable, HEXCTL, *args],
            cwd=self.target,
            capture_output=True,
            text=True,
            env=env,
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"hexctl {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        if proc.returncode == 0:
            self.fake_refs = pending_refs
            self.fake_prs = pending_prs
            self.fake_parents = pending_parents
            self.env["FAKE_GIT_TREE_BY_COMMIT"] = json.dumps(pending_tree)
            self.env["FAKE_GIT_DIFF_PATHS"] = json.dumps(pending_diffs)
            if pending_audit_baseline is not None:
                self.fake_audit_baseline = pending_audit_baseline
        return proc

    def append_valid_audit_record(self, args, state):
        """Stand in for Warden when a controller test is not about log syntax."""
        if state is None:
            raise AssertionError("cannot write an audit record without controller state")
        findings = int(args[args.index("--findings") + 1])
        verdict = (
            args[args.index("--elenchus-verdict") + 1]
            if "--elenchus-verdict" in args
            else "null"
        )
        study_path = state["receipts"]["study"]["artifact"]
        if not os.path.isabs(study_path):
            study_path = os.path.join(self.target, study_path)
        with open(study_path, encoding="utf-8") as handle:
            study = handle.read()
        block = re.search(
            r"(?ms)^```risk-register\s*$\n(?P<body>.*?)^```\s*$",
            study,
        )
        if block is None:
            raise AssertionError("fixture study has no risk register")
        risk_ids = [
            line.split("|", 1)[0].strip()
            for line in block.group("body").splitlines()
            if line.strip()
        ]
        covered = "; ".join(f"{risk_id}=reviewed" for risk_id in risk_ids)
        round_number = len(
            state["steps"][state["current_step"] - 1]["audit"]["rounds"]
        ) + 1
        table_rows = (
            ["| -- | -- | -- | none | -- |"]
            if findings == 0
            else [
                f"| F-{index:02d} | low | fixture.py | finding {index} | open |"
                for index in range(1, findings + 1)
            ]
        )
        record = "\n".join(
            [
                f"## Step {state['current_step']}, round {round_number} "
                "-- 2026-08-23T02:17:46Z",
                "",
                "Audit schema: fiat-audit-round/v2",
                "",
                f"Covered: {covered}",
                "",
                "Not checked: none",
                "",
                f"Elenchus verdict: {verdict}",
                "",
                "| id | severity | file | finding | status |",
                "| --- | --- | --- | --- | --- |",
                *table_rows,
                "",
                "Leads not pursued: none",
                "",
            ]
        )
        log_path = state["config"]["audit"]["log_path"]
        path = log_path if os.path.isabs(log_path) else os.path.join(self.target, log_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        needs_gap = os.path.exists(path) and os.path.getsize(path) > 0
        with open(path, "a", encoding="utf-8") as handle:
            if needs_gap:
                handle.write("\n")
            handle.write(record)
        synopsis_result = subprocess.run(
            [sys.executable, AUDIT_SYNOPSIS, "--write", self.target],
            cwd=self.target,
            capture_output=True,
            text=True,
        )
        if synopsis_result.returncode:
            raise AssertionError(
                f"audit synopsis fixture failed\nstdout: {synopsis_result.stdout}"
                f"stderr: {synopsis_result.stderr}"
            )
        # Warden owns and commits the append in a real run. Keep the fixture's
        # worktree equally clean so retirement tests exercise controller state,
        # not an untracked stand-in log.
        synopsis_path = os.path.splitext(log_path)[0] + ".synopsis.md"
        self.git("add", "--", log_path, synopsis_path)
        self.git("commit", "-q", "-m", "fixture audit record")

    @staticmethod
    def fake_sha(ref):
        return ref if re.fullmatch(r"[0-9a-f]{40}", ref) else hashlib.sha1(ref.encode()).hexdigest()

    @staticmethod
    def fake_pr(url, head, base, head_sha, merge_sha=None, *, body=None):
        """One pull request as the REST endpoint spells it.

        REST fills `merge_commit_sha` on an open pull request too, with the
        test merge GitHub computes for it, so the fixture carries one either
        way and `merged` is what says whether it is a real merge.
        """
        return {
            "html_url": url,
            "state": "closed" if merge_sha else "open",
            "merged": bool(merge_sha),
            "user": {"login": "shoggoth-wildcat"},
            "body": body or "Delivery evidence.\n\n<!-- wildcat-origin: shoggoth -->",
            "head": {"ref": head, "sha": head_sha},
            "base": {"ref": base},
            "merge_commit_sha": merge_sha if merge_sha else "f" * 40,
        }

    def install_fake_delivery_tools(self):
        fake_bin = os.path.join(self.dir, "delivery-tools")
        os.makedirs(fake_bin)
        real_git = shutil.which("git")
        git_script = os.path.join(fake_bin, "git")
        with open(git_script, "w", encoding="utf-8") as handle:
            handle.write(f"""#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
import time

raw_args = sys.argv[1:]
args = raw_args
candidate = raw_args[1:] if raw_args[:1] == ["--no-replace-objects"] else raw_args
while len(candidate) >= 2 and candidate[0] == "-c":
    candidate = candidate[2:]
candidate_ref = (
    candidate[-1].removesuffix("^{{commit}}")
    if candidate[:3] == ["rev-parse", "--verify", "--end-of-options"]
    else None
)
candidate_refs = json.loads(os.environ.get("FAKE_GIT_REFS", "{{}}"))
candidate_is_fake_rev_parse = candidate_ref is not None and (
    re.fullmatch(r"[0-9a-f]{{40}}", candidate_ref)
    or candidate_ref in candidate_refs
    or candidate_ref in candidate_refs.values()
)
if candidate_is_fake_rev_parse or (candidate and candidate[0] in (
    "verify-commit",
    "show",
    "diff",
    "merge-base",
    "rev-list",
    "ls-tree",
    "cat-file",
    "ls-remote",
)):
    args = candidate
mode = os.environ.get("FAKE_GIT_MODE", "valid")
if args and args[0] == "rev-parse" and "--show-toplevel" not in args:
    if mode == "missing-commit":
        raise SystemExit(2)
    ref = args[-1].removesuffix("^{{commit}}")
    refs = json.loads(os.environ.get("FAKE_GIT_REFS", "{{}}"))
    print(refs.get(ref, ref if re.fullmatch(r"[0-9a-f]{{40}}", ref) else hashlib.sha1(ref.encode()).hexdigest()))
elif args[:3] == ["remote", "get-url", "origin"]:
    if mode == "slow-remote":
        time.sleep(0.6)
    print(os.environ.get("FAKE_GIT_ORIGIN", "https://github.com/wildcat-finance/example.git"))
elif args and args[0] == "ls-remote":
    if os.environ.get("FAKE_GIT_LS_REMOTE_LOG"):
        with open(os.environ["FAKE_GIT_LS_REMOTE_LOG"], "a", encoding="utf-8") as log:
            log.write(json.dumps({{"args": args, "cwd": os.getcwd()}}) + "\\n")
    ref = args[-1]
    branch = ref.removeprefix("refs/heads/")
    refs = json.loads(os.environ.get("FAKE_GIT_REFS", "{{}}"))
    tip = refs.get(branch, hashlib.sha1(branch.encode()).hexdigest())
    if mode == "remote-absent":
        pass
    elif mode == "remote-malformed":
        print(f"not-a-sha\\t{{ref}}")
    elif mode == "remote-duplicate":
        print(f"{{tip}}\\t{{ref}}")
        print(f"{{tip}}\\t{{ref}}")
    else:
        print(f"{{tip}}\\t{{ref}}")
elif args and args[0] == "merge-base":
    if "--is-ancestor" in args:
        if mode == "ancestry-error":
            raise SystemExit(128)
        if mode == "not-ancestor":
            detached = os.environ.get("FAKE_GIT_NOT_ANCESTOR", "d" * 40).split(",")
            if args[-2] in detached:
                raise SystemExit(1)
        raise SystemExit(0)
    print(os.environ.get("FAKE_GIT_MERGE_BASE", "4" * 40))
elif args and args[0] == "ls-tree":
    if mode == "baseline-unavailable":
        raise SystemExit(128)
    separator = args.index("--") if "--" in args else len(args) - 1
    commit = args[separator - 1]
    requested = [
        item.removeprefix(":(literal)") for item in args[separator + 1:]
    ]
    tree_by_commit = json.loads(
        os.environ.get("FAKE_GIT_TREE_BY_COMMIT", "{{}}")
    )
    mapped = tree_by_commit.get(commit, {{}})
    mapped_request = any(path in mapped for path in requested)
    if mapped_request:
        for path_text in requested:
            payload_hex = mapped.get(path_text)
            if payload_hex is None:
                continue
            baseline = bytes.fromhex(payload_hex)
            object_id = hashlib.sha1(
                b"blob " + str(len(baseline)).encode() + b"\\0" + baseline
            ).hexdigest()
            entry_mode = (
                "100755" if mode == "prose-final-executable" else
                "120000" if mode == "prose-final-symlink" else
                "100644"
            )
            sys.stdout.buffer.write(
                f"{{entry_mode}} blob {{object_id}}\\t{{path_text}}\\0".encode()
            )
    elif len(requested) == 1 and requested[0] == ".fiat/conformance-overlay-contract.json":
        path_text = requested[0]
        by_commit = json.loads(
            os.environ.get("FAKE_GIT_CONFORMANCE_BY_COMMIT", "{{}}")
        )
        payload_hex = (
            by_commit[commit]
            if commit in by_commit
            else os.environ.get("FAKE_GIT_CONFORMANCE_HEX")
        )
    else:
        path_text = requested[-1]
        payload_hex = os.environ.get("FAKE_GIT_BASELINE_HEX")
    if not mapped_request and payload_hex is not None:
        baseline = bytes.fromhex(payload_hex)
        object_id = hashlib.sha1(
            b"blob " + str(len(baseline)).encode() + b"\\0" + baseline
        ).hexdigest()
        path = path_text.encode()
        if mode == "baseline-ambiguous":
            sys.stdout.buffer.write(b"ambiguous\\0")
        elif mode == "baseline-unsafe":
            sys.stdout.buffer.write(
                f"120000 blob {{object_id}}\\t".encode() + path + b"\\0"
            )
        else:
            sys.stdout.buffer.write(
                f"100644 blob {{object_id}}\\t".encode() + path + b"\\0"
            )
elif args and args[:2] == ["cat-file", "-s"]:
    wanted = args[-1]
    payloads = [
        bytes.fromhex(value)
        for value in [
            os.environ.get("FAKE_GIT_BASELINE_HEX"),
            os.environ.get("FAKE_GIT_CONFORMANCE_HEX"),
            *json.loads(
                os.environ.get("FAKE_GIT_CONFORMANCE_BY_COMMIT", "{{}}")
            ).values(),
            *[
                value
                for tree in json.loads(
                    os.environ.get("FAKE_GIT_TREE_BY_COMMIT", "{{}}")
                ).values()
                for value in tree.values()
            ],
        ]
        if value is not None
    ]
    baseline = next((
        value for value in payloads
        if hashlib.sha1(b"blob " + str(len(value)).encode() + b"\\0" + value).hexdigest() == wanted
    ), b"")
    if mode == "baseline-oversized":
        print(2 * 1024 * 1024 + 1)
    elif mode == "baseline-malformed-size":
        print("not-a-size")
    elif mode == "baseline-short-read":
        print(len(baseline) + 1)
    else:
        print(len(baseline))
elif args and args[:2] == ["cat-file", "blob"]:
    wanted = args[-1]
    payloads = [
        bytes.fromhex(value)
        for value in [
            os.environ.get("FAKE_GIT_BASELINE_HEX"),
            os.environ.get("FAKE_GIT_CONFORMANCE_HEX"),
            *json.loads(
                os.environ.get("FAKE_GIT_CONFORMANCE_BY_COMMIT", "{{}}")
            ).values(),
            *[
                value
                for tree in json.loads(
                    os.environ.get("FAKE_GIT_TREE_BY_COMMIT", "{{}}")
                ).values()
                for value in tree.values()
            ],
        ]
        if value is not None
    ]
    baseline = next((
        value for value in payloads
        if hashlib.sha1(b"blob " + str(len(value)).encode() + b"\\0" + value).hexdigest() == wanted
    ), b"")
    sys.stdout.buffer.write(baseline)
elif (
    args
    and args[0] == "diff"
    and "--name-only" in args
    and any(".." in value for value in args)
):
    pair = next(value for value in args if ".." in value)
    paths = json.loads(os.environ.get("FAKE_GIT_DIFF_PATHS", "{{}}")).get(pair, [])
    if paths:
        sys.stdout.write("\\0".join(paths) + "\\0")
elif args and args[0] == "rev-list":
    pair = next(value for value in args if ".." in value)
    base, head = pair.split("..", 1)
    if mode == "malformed-range":
        print("not-a-sha")
    elif mode == "intermediate":
        print(hashlib.sha1(b"middle").hexdigest())
        print(head)
    elif base != head:
        print(base if mode == "range-confusion" else head)
elif args and args[0] == "verify-commit":
    if os.environ.get("FAKE_GIT_LOG"):
        with open(os.environ["FAKE_GIT_LOG"], "a", encoding="utf-8") as log:
            log.write(args[-1] + "\\n")
    if mode == "timeout":
        time.sleep(2)
    if mode == "overflow":
        sys.stdout.write("signature" * 300000)
    if mode in ("nonzero", "unsigned"):
        sys.stderr.write("ghp_FAKE_SECRET raw signature material")
        raise SystemExit(7)
    print("FAKE SIGNATURE MATERIAL")
elif args and args[0] == "show":
    if "--format=%P" in args:
        parents = json.loads(os.environ.get("FAKE_GIT_PARENTS", "{{}}"))
        print(" ".join(parents.get(args[-1], [])))
    elif "--format=%an%x00%ae" in args:
        if mode == "host-author":
            sys.stdout.write("Claude\\0noreply@anthropic.com\\n")
        else:
            sys.stdout.write("Shoggoth\\0shoggoth@wildcat.finance\\n")
    elif "--format=%cn%x00%ce" in args:
        if mode == "host-committer":
            sys.stdout.write("Claude\\0noreply@anthropic.com\\n")
        elif mode == "publisher-committer":
            sys.stdout.write("Laurence Day\\0laurence@wildcat.finance\\n")
        else:
            sys.stdout.write("Shoggoth\\0shoggoth@wildcat.finance\\n")
    elif mode == "missing-trailer":
        print("subject\\n\\nWildcat-Origin: shoggoth")
    elif mode == "duplicate-trailer":
        print("subject\\n\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nWildcat-Origin: shoggoth")
    elif mode == "host-coauthor":
        print("subject\\n\\nCo-authored-by: Claude <noreply@anthropic.com>\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nWildcat-Origin: shoggoth")
    elif mode == "host-byline":
        print("subject\\n\\nGenerated by Claude Code\\n\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nWildcat-Origin: shoggoth")
    else:
        print("subject\\n\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nWildcat-Origin: shoggoth")
else:
    os.execv({real_git!r}, [{real_git!r}, *args])
""")
        os.chmod(git_script, 0o755)

        gh_script = os.path.join(fake_bin, "gh")
        with open(gh_script, "w", encoding="utf-8") as handle:
            handle.write("""#!/usr/bin/env python3
import json
import os
import re
import sys
import time

args = sys.argv[1:]
mode = os.environ.get("FAKE_GH_MODE", "valid")
# The filing contract every fixture issue satisfies unless a case replaces it.
# Written here rather than in each test so a case that is not about the contract
# does not have to restate it.
DEFAULT_ISSUE_BODY = (
    "A fixture issue.\\n"
    "\\n"
    "Fiat-Required: 1\\n"
    "\\n"
    "```carryover\\n"
    "none | none | this fixture carries nothing forward\\n"
    "```\\n"
)
if os.environ.get("FAKE_GH_LOG"):
    with open(os.environ["FAKE_GH_LOG"], "a", encoding="utf-8") as log:
        log.write(json.dumps(args) + "\\n")
if mode == "timeout":
    time.sleep(2)
if mode == "overflow":
    sys.stdout.write("x" * 2200000)
    raise SystemExit(0)
if mode == "nonzero":
    sys.stderr.write("ghp_FAKE_SECRET rate limit response")
    raise SystemExit(9)
if mode == "invalid-json":
    print("not json")
    raise SystemExit(0)
path = args[-1]
if re.fullmatch(r"repos/[^/]+/[^/]+", path):
    repository = "elsewhere/example" if mode == "repo-mismatch" else "wildcat-finance/example"
    print(json.dumps({"full_name": repository}))
    raise SystemExit(0)
issue = re.fullmatch(r"repos/(?P<repo>[^/]+/[^/]+)/issues/(?P<number>[0-9]+)", path)
if issue:
    url = "https://github.com/%s/issues/%s" % (issue.group("repo"), issue.group("number"))
    bodies = json.loads(os.environ.get("FAKE_GH_ISSUES", "{}"))
    if mode == "issue-missing":
        raise SystemExit(4)
    if url in bodies:
        body = bodies[url]
    else:
        body = os.environ.get("FAKE_GH_ISSUE_BODY", DEFAULT_ISSUE_BODY)
    if mode == "issue-body-not-text":
        body = 17
    print(json.dumps({"number": int(issue.group("number")), "body": body}))
    raise SystemExit(0)
pull = re.fullmatch(r"repos/(?P<repo>[^/]+/[^/]+)/pulls/(?P<number>[0-9]+)", path)
if pull:
    url = "https://github.com/%s/pull/%s" % (pull.group("repo"), pull.group("number"))
    payload = json.loads(os.environ.get("FAKE_GH_PRS", "{}")).get(url)
    if payload is None:
        raise SystemExit(4)
    if mode == "pr-mismatch":
        payload["base"]["ref"] = "wrong-base"
    if mode == "pr-head-mismatch":
        payload["head"]["sha"] = "9" * 40
    if mode == "host-pr-author":
        payload["user"] = {"login": "app/claude"}
    if mode == "publisher-committer":
        payload["user"] = {"login": "laurenceday"}
    if mode == "host-pr-byline":
        payload["body"] += "\\n\\nGenerated by [Claude Code](https://claude.ai/code)"
    print(json.dumps(payload))
    raise SystemExit(0)
sha = args[-1].rsplit("/", 1)[-1]
account = {"login": "shoggoth-wildcat"}
identity = {"name": "Shoggoth", "email": "shoggoth@wildcat.finance"}
committer_account = {"login": "shoggoth-wildcat"}
committer_identity = {"name": "Shoggoth", "email": "shoggoth@wildcat.finance"}
message = "subject\\n\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\nWildcat-Origin: shoggoth"
if mode == "publisher-committer":
    committer_account = {"login": "laurenceday"}
    committer_identity = {"name": "Laurence Day", "email": "laurence@wildcat.finance"}
elif mode == "external-author":
    account = {"login": "kethcode"}
    identity = {"name": "Kethcode", "email": "Kethcode@Example.Invalid"}
elif mode == "unlinked-author":
    account = None
    identity = {"name": "Kethcode", "email": "kethcode@example.invalid"}
elif mode == "attribution-null-account-object":
    account = {"login": None}
elif mode == "attribution-host-account":
    account = {"login": "claude[bot]"}
elif mode == "attribution-account-not-object":
    account = "kethcode"
elif mode == "attribution-bad-login":
    account = {"login": "not a login"}
elif mode == "attribution-host-author":
    identity = {"name": "Claude", "email": "noreply@anthropic.com"}
elif mode == "attribution-host-committer-account":
    committer_account = {"login": "claude[bot]"}
elif mode == "attribution-host-committer":
    committer_identity = {"name": "Claude", "email": "noreply@anthropic.com"}
elif mode == "attribution-missing-committer":
    committer_identity = None
elif mode == "attribution-bad-committer-login":
    committer_account = {"login": "not a login"}
elif mode == "attribution-missing-identity":
    identity = None
elif mode == "attribution-blank-name":
    identity = {"name": "   ", "email": "kethcode@example.invalid"}
elif mode == "attribution-long-name":
    identity = {"name": "n" * (256 + 1), "email": "kethcode@example.invalid"}
elif mode == "attribution-spaced-email":
    identity = {"name": "Kethcode", "email": "keth code@example.invalid"}
elif mode == "attribution-long-email":
    identity = {"name": "Kethcode", "email": "k" * 310 + "@example.invalid"}
elif mode == "attribution-missing-message":
    message = None
elif mode == "attribution-host-coauthor":
    message = "subject\\n\\nCo-authored-by: Claude <noreply@anthropic.com>"
elif mode == "attribution-many-coauthors":
    message = "subject\\n\\n" + "\\n".join(
        "Co-authored-by: Person%d <person%d@example.invalid>" % (i, i)
        for i in range(40)
    )
elif mode == "attribution-merge-coauthor":
    account = {"login": "maintainer"}
    identity = {"name": "Maintainer", "email": "maintainer@example.invalid"}
    message = (
        "Merge pull request #1\\n\\n"
        "Co-authored-by: Kethcode <kethcode@example.invalid>"
    )
elif mode == "attribution-merge-stranger":
    account = {"login": "maintainer"}
    identity = {"name": "Maintainer", "email": "maintainer@example.invalid"}
    message = "Merge pull request #1"
elif mode == "attribution-second-coauthor":
    message = (
        "subject\\n\\nCo-authored-by: Shoggoth <shoggoth@wildcat.finance>\\n"
        "Co-authored-by: Kethcode <kethcode@example.invalid>\\n"
        "Wildcat-Origin: shoggoth"
    )
payload = {
    "sha": None if mode == "missing-sha" else sha,
    "author": account,
    "committer": committer_account,
    "commit": {
        "author": identity,
        "committer": committer_identity,
        "message": message,
        "verification": {
            "verified": mode != "verified-false",
            "reason": os.environ.get("FAKE_GH_REASON", "expired_key") if mode == "invalid-reason" else "valid",
            "signature": "RAW FAKE SIGNATURE",
        },
    },
}
print(json.dumps(payload))
""")
        os.chmod(gh_script, 0o755)
        self.env["PATH"] = fake_bin + os.pathsep + self.env.get("PATH", "")

    def next_json(self):
        return json.loads(self.run_ctl("next").stdout)

    def write(self, name, content="stub\n"):
        path = os.path.join(self.target, name)
        os.makedirs(os.path.dirname(path) or self.target, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return name

    CARRYOVER_NONE_ROW = "none | none | this run leaves nothing unfinished\n"

    def carryover_block(self, rows=None):
        """One triage block in the shape `done integrate` requires."""
        return "```carryover\n" + (rows or self.CARRYOVER_NONE_ROW) + "```\n"

    def write_run_pr(self, carried=None, rows=None):
        """The run-level pull request body the integrate receipt reads.

        `rows` gives the triage rows; `carried` replaces the whole section body,
        which is how a case exercises a section that answers nothing.
        """
        body = "Run body.\n"
        section = self.carryover_block(rows) if carried is None else carried
        if section is not None:
            body += "\n## Carried forward\n\n" + section
        return self.write(os.path.join(".hexaemeron", "run-pr.md"), body)

    def init(self, topic="test topic", task_issue=None, base=None):
        args = ["init", "--topic", topic]
        if task_issue is not None:
            args += ["--task-issue", task_issue]
        if base is not None:
            args += ["--base", base]
        self.run_ctl(*args)
        self.write_design_evidence()

    def write_design_evidence(self, target=None):
        """Write the smallest fully resolved evidence matrix used by fixtures."""
        target = target or self.target
        report_dir = os.path.join(target, ".hexaemeron", "design-reports")
        os.makedirs(report_dir, exist_ok=True)
        candidates = (
            ("bounded", "Process one bounded unit at a time."),
            ("buffered", "Hold the complete input before processing."),
        )
        criteria = (
            ("works", "correctness", "gate", "boolean", "equals", True),
            ("warm-time", "time", "metric", "milliseconds", "minimise", None),
            ("peak-space", "space", "metric", "bytes", "minimise", None),
            ("plugin-safe", "compatibility", "gate", "boolean", "equals", True),
            ("restart-safe", "recovery", "gate", "boolean", "equals", True),
        )
        criterion_records = []
        for identifier, concern, kind, unit, comparator, threshold in criteria:
            criterion_records.append({
                "id": identifier,
                "concern": concern,
                "kind": kind,
                "stage": "selection",
                "owner": "fixture",
                "unit": unit,
                "comparator": comparator,
                "threshold": threshold,
                "blocks": "design-lock",
            })
        results = []
        for candidate, _ in candidates:
            for identifier, _, kind, unit, _, _ in criteria:
                value = True
                if kind == "metric":
                    value = 10 if candidate == "bounded" else 20
                payload = {
                    "schema": "protasis-design-report/v1",
                    "candidate": candidate,
                    "criterion": identifier,
                    "value": value,
                    "unit": unit,
                    "command": f"fixture measure {candidate} {identifier}",
                    "exit": 0,
                }
                data = (json.dumps(payload, sort_keys=True) + "\n").encode()
                name = f"{candidate}-{identifier}.json"
                with open(os.path.join(report_dir, name), "wb") as handle:
                    handle.write(data)
                results.append({
                    "candidate": candidate,
                    "criterion": identifier,
                    "state": "pass",
                    "report": {
                        "path": f"design-reports/{name}",
                        "sha256": hashlib.sha256(data).hexdigest(),
                    },
                })
        record = {
            "schema": "protasis-design-evidence/v1",
            "candidates": [
                {"id": identifier, "summary": summary}
                for identifier, summary in candidates
            ],
            "criteria": criterion_records,
            "results": results,
            "selection": {
                "candidate": "bounded",
                "rule": "unique-frontier",
                "policy_ref": None,
            },
        }
        path = os.path.join(target, ".hexaemeron", "design-evidence.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")
        return path

    def design_lock_block(self, state=None):
        state = state or self.state()
        design = state["receipts"]["study"]["design_evidence"]
        return (
            "```design-lock\n"
            f"schema | {design['schema']}\n"
            f"sha256 | {design['sha256']}\n"
            f"candidate | {design['selected']}\n"
            "```\n"
        )

    @staticmethod
    def integration_base(state):
        starting_base = state["base"]
        if re.fullmatch(r"[0-9a-f]{40}(?:[0-9a-f]{24})?", starting_base):
            return state["config"]["git"]["base"]
        return starting_base

    def state(self):
        payload = json.loads(self.run_ctl("status", "--json").stdout)
        payload.pop("observation_run_id", None)
        payload.pop("version_resolution_status", None)
        return payload

    def record_legacy_config(self, path, value):
        """Create a ledger-valid state that an older controller could have stored."""
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        node = state["config"]
        parts = path.split(".")
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value
        hexctl_module().commit(
            self.target,
            state,
            "fixture:legacy-config",
            {"path": path, "value": value},
        )

    def make_prose_receipt_legacy(self, step_no=1):
        """Convert one fixture step to the pre-binding prose receipt shape."""
        state = self.state()
        step = state["steps"][step_no - 1]
        receipt = step["receipts"]["prose"]
        legacy = {
            "files": receipt["files"],
            "skills": receipt["skills"],
        }
        step["receipts"]["prose"] = legacy
        step["receipts"].get("audit", {}).pop("prose_writable", None)
        if step["audit"]["rounds"]:
            step["audit"]["rounds"][-1].pop("prose_writable", None)
        hexctl_module().commit(
            self.target,
            state,
            "fixture:legacy-prose",
            {"step": step_no, **legacy},
        )

    def run_branch(self):
        return self.state()["run_branch"]

    def step_branch(self, n, state=None):
        state = state or self.state()
        title = state["steps"][n - 1]["title"]
        tail = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:32].strip("-")
        return f"{state['run_branch']}-step-{n}-{tail or 'untitled'}"

    def step_base(self, n, state=None):
        state = state or self.state()
        if n == 1:
            return state["run_branch"]
        return self.step_branch(n - 1, state)

    def strip_run_branch(self):
        """Make the state look like a run started before stacked branches."""
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state.pop("run_branch", None)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)

    def merge_stack(self):
        for step in self.state()["steps"]:
            self.run_ctl("done", "merge-step", "--step", str(step["n"]),
                         "--merge-commit", format(step["n"], "x") * 40)

    def integrate_run(self, closed_issue_url=None):
        self.merge_stack()
        self.write_run_pr()
        args = ["done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                "--merge-commit", "f" * 40]
        if closed_issue_url:
            args += ["--closed-issue-url", closed_issue_url]
        self.run_ctl(*args)

    def spawn_lock_holder(self, ready, release, command="cmd_record"):
        program = """
import importlib.util
from pathlib import Path
import sys
import time

spec = importlib.util.spec_from_file_location("hexctl_under_test", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.held_lock(sys.argv[2], sys.argv[3]):
    Path(sys.argv[4]).write_text("ready\\n", encoding="utf-8")
    while not Path(sys.argv[5]).exists():
        time.sleep(0.01)
"""
        process = subprocess.Popen(
            [
                sys.executable,
                "-c",
                program,
                HEXCTL,
                self.target,
                command,
                ready,
                release,
            ],
            cwd=self.target,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.processes.append(process)
        return process

    def wait_for_file(self, path, process, timeout=5):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if os.path.exists(path):
                return
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.fail(
                    f"lock holder exited {process.returncode} before ready\n"
                    f"stdout: {stdout}\nstderr: {stderr}"
                )
            time.sleep(0.01)
        self.fail("lock holder did not become ready")

    def start_lock_holder(self, name="holder", command="cmd_record"):
        ready = os.path.join(self.dir, f"{name}.ready")
        release = os.path.join(self.dir, f"{name}.release")
        process = self.spawn_lock_holder(ready, release, command)
        self.wait_for_file(ready, process)
        return process, ready, release

    def release_lock_holder(self, process, release):
        with open(release, "w", encoding="utf-8") as handle:
            handle.write("release\n")
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0, (stdout, stderr))

    def to_steps(self, titles=("Scaffold", "Core"), task_issue=None, base=None):
        self.init(task_issue=task_issue, base=base)
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "packet-state-drift | packet | compare state hash\n"
            "```\n",
        )
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n" + "\n".join(
                f"## Step {number}: {title}\n\n**Goal.** Ship {title}.\n"
                for number, title in enumerate(titles, 1)
            ),
        )
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)
        # The fixture checkout and the run branch already exist (`init` cut the
        # branch); only the step branches are this helper's to make.
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
        for step in state["steps"]:
            self.git("branch", self.step_branch(step["n"], state))

    def to_amendable_steps(self, titles=("Core", "Finish")):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read()
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n" + "\n".join(
                f"## Step {number}: {title}\n\n**Goal.** {title}.\n"
                for number, title in enumerate(titles, 1)
            ),
        )
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        return original

    def to_runbook_amendable_steps(self, titles=("Core", "Finish")):
        """A source-bound run whose baseline also passes Protasis runbook mode."""
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            study_text = handle.read()
        study = self.write("study.md", study_text)
        self.run_ctl("done", "study", "--artifact", study)
        blocks = []
        for number, title in enumerate(titles, 1):
            blocks.append(
                f"## Step {number}: {title}\n\n"
                f"**Goal.** Ship {title}.\n"
                f"**Entry.** Step {number} is ready.\n"
                "**Exit.** Run `fiat-v1.0.0`.\n"
                f"**Files.** `step-{number}.md`.\n"
                "**Tests.** Run `python3 -m unittest`.\n"
                "**Disciplines.** none, fixture only.\n"
            )
        runbook_text = "# Runbook\n\n" + "\n".join(blocks)
        runbook = self.write("runbook.md", runbook_text)
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        with open(os.path.join(self.target, runbook), encoding="utf-8") as handle:
            return study_text, handle.read()

    @staticmethod
    def amendment(
        verdicts=(
            "Step 1: entry holds; exit holds. "
            "Step 2: entry holds; exit holds."
        ),
        *,
        date="2026-08-22",
        what="The fixture assumption was corrected.",
        why="The receipted baseline disproved it.",
        touched="Steps 1 and 2.",
    ):
        return (
            f"\n### Amendment -- {date}\n\n"
            f"**What changed.** {what}\n"
            f"**Why.** {why}\n"
            f"**Steps touched.** {touched}\n"
            f"**Still holding.** {verdicts}\n"
        )

    @staticmethod
    def runbook_amendment(
        verdicts=(
            "Step 1: entry holds; exit holds. "
            "Step 2: entry holds; exit holds."
        ),
        *,
        date="2026-08-24",
        what="Complete replacement Exit: Run `fiat-v2.0.0`.",
        why="The target version changed.",
        touched="Steps 1 and 2.",
    ):
        return (
            f"\n### Amendment -- {date}\n\n"
            f"**What changed.** {what}\n"
            f"**Why.** {why}\n"
            f"**Steps touched.** {touched}\n"
            f"**Still holding.** {verdicts}\n"
        )

    def git(self, *args, expect=0):
        proc = subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=self.target,
            capture_output=True,
            text=True,
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"git {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def to_audit(self, task_issue=None):
        self.to_steps(task_issue=task_issue)
        self.run_ctl("done", "implement", "--branch", self.step_branch(1),
                     "--commit", "abc123")

    def finish_step(self, step_no=1):
        self.run_ctl("done", "implement", "--branch", self.step_branch(step_no),
                     "--commit", f"abc{step_no}")
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit")
        self.run_ctl("done", "prose", "--files", "3",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        # `done push` records the pushed sha, which must equal the fake
        # remote's tip, fake_sha(head).  A 40-hex head makes fake_sha the
        # identity, the receipt-equals-tip state of a genuine run; a
        # placeholder like "head2" fired the rewritten-stack refusal.
        self.run_ctl(
            "done", "push",
            "--pr-url", f"https://github.com/wildcat-finance/example/pull/{step_no}",
            "--head-commit", self.fake_sha(f"head{step_no}"),
            "--pr-base", self.step_base(step_no),
        )
