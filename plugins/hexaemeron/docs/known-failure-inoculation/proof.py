#!/usr/bin/env python3
"""Drive the checked-in Fiat controller through the inoculation contract.

The proof builds one disposable signed Git repository, runs three
controller lanes inside it, records what the controller did, writes the
bounded sibling `proof.md` transcript, and then checks that transcript
against the run it just completed. It ends by mutating the transcript once
per bound field class and requiring the same checker to refuse each one.

Nothing here reads a network, a credential store, or a repository outside
the one it created. The signer it generates lives inside the disposable
tree, is never printed, and dies with it. The only path written outside the
temporary tree is the transcript beside this file.

Exit 0 means the run completed, the transcript matched it, and every
mutation was refused. Exit 1 means the demonstration or the check failed.
Exit 2 means the invocation or the environment was unusable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
REPOSITORY_ROOT = HERE.parents[3]
TRANSCRIPT = HERE / "proof.md"

CONTROLLER = "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
SYNOPSIS = "plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py"
INVENTORY_LOADER = "plugins/hexaemeron/skills/protasis/scripts/known_failure_inventory.py"
DESIGN_CHECKER = "plugins/hexaemeron/skills/protasis/scripts/design_evidence.py"
GUARD_RUNNER = "plugins/hexaemeron/skills/elenchus/scripts/elenchus.py"
BOUND_SOURCES = (
    CONTROLLER,
    SYNOPSIS,
    INVENTORY_LOADER,
    DESIGN_CHECKER,
    GUARD_RUNNER,
)

AUDIT_FILTER = "sapheneia:sapheneia"
CO_AUTHOR = "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>"
ORIGIN_TRAILER = "Wildcat-Origin: shoggoth"
SIGNER_IDENTITY = "shoggoth@wildcat.finance"
SIGNER_NAME = "Shoggoth"

RECORD_FENCE = "proof-record"
RECORD_FENCE_LINES = 32
OUTPUT_BYTES_MAX = 1 << 20
COMMAND_TIMEOUT = 900

FULL_OID = re.compile(r"\b[0-9a-f]{40}\b")
DIGEST = re.compile(r"\b[0-9a-f]{64}\b")

MUTATION_CLASSES = ("command", "exit", "count", "commit", "path", "digest")

LANE_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5}
STATED_LANES = re.compile(
    r"through (" + "|".join(LANE_WORDS) + r") lanes inside it"
)


class ProofError(Exception):
    """A demonstration step the controller did not answer as recorded."""


# ------------------------------------------------------------------ recording


class Record:
    """Everything the transcript binds, kept as ordered plain data.

    Run-local identifiers -- commit ids, controller run ids, state and
    ledger digests, manifest digests -- are replaced by stable tokens, so
    the transcript is the same bytes on every run against the same tree.
    The token table keeps the actual value behind each token, and the
    checker resolves through it. A token collision is therefore a real
    binding: two different actual values can never share one token, and one
    actual value always reaches the same token.
    """

    def __init__(self) -> None:
        self.sources: list[dict] = []
        self.lanes: list[dict] = []
        self.phases: list[dict] = []
        self.refusals: list[dict] = []
        self.tokens: dict[str, str] = {}
        self.by_value: dict[tuple[str, str], str] = {}
        self.relations: dict[str, str] = {}

    def token(self, kind: str, value: str, hint: str) -> str:
        """Return the stable token for one run-local value."""
        existing = self.by_value.get((kind, value))
        if existing is not None:
            return existing
        name = f"@{hint}"
        if name in self.tokens:
            raise ProofError(f"token {name} already binds another value")
        self.tokens[name] = value
        self.by_value[(kind, value)] = name
        self.relations.setdefault(name, kind)
        return name

    def source(self, path: str, raw: bytes) -> None:
        self.sources.append(
            {
                "path": path,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        )

    def lane(self, identifier: str, topic: str, run_branch: str,
             step_branch: str) -> None:
        self.lanes.append(
            {
                "id": identifier,
                "topic": topic,
                "run_branch": run_branch,
                "step_branch": step_branch,
            }
        )

    def phase(self, lane: str, phase: str, question: str, command: str,
              exit_code: int, result: str, counts: str, evidence: str) -> None:
        self.phases.append(
            {
                "lane": lane,
                "ordinal": str(len(self.phases) + 1),
                "phase": phase,
                "question": question,
                "command": command,
                "exit": str(exit_code),
                "result": result,
                "counts": counts or "-",
                "evidence": evidence or "-",
            }
        )

    def refusal(self, lane: str, case: str, family: str, command: str,
                exit_code: int, message: str, before: tuple[str, str],
                after: tuple[str, str], counters: str) -> None:
        self.refusals.append(
            {
                "lane": lane,
                "case": case,
                "class": family,
                "command": command,
                "exit": str(exit_code),
                "message": message,
                "state": f"{before[0]}/{after[0]}",
                "ledger": f"{before[1]}/{after[1]}",
                "counters": counters or "-",
            }
        )


# -------------------------------------------------------------- process calls


def controlled_environment(home: Path) -> dict[str, str]:
    """A closed environment for every child this proof starts."""
    return {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(home),
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
    }


def run_bounded(argv: list[str], cwd: Path, environment: dict[str, str]):
    """Run one exact argument list with no shell and bounded output."""
    completed = subprocess.run(
        argv,
        cwd=str(cwd),
        env=environment,
        capture_output=True,
        timeout=COMMAND_TIMEOUT,
        check=False,
    )
    if (len(completed.stdout) + len(completed.stderr)) > OUTPUT_BYTES_MAX:
        raise ProofError(f"{argv[0]} produced more output than the proof reads")
    return completed


class Lane:
    """One disposable controller run inside the disposable repository."""

    def __init__(self, proof: "Proof", identifier: str, topic: str,
                 run_branch: str) -> None:
        self.proof = proof
        self.id = identifier
        self.topic = topic
        self.run_branch = run_branch
        self.worktree = proof.repository / "tmp/fiat" / run_branch.replace("/", "-")
        self.state_root = self.worktree / ".hexaemeron"

    # ------------------------------------------------------------- primitives

    def git(self, *arguments: str) -> str:
        completed = run_bounded(
            ["git", *arguments], self.worktree, self.proof.environment
        )
        if completed.returncode != 0:
            raise ProofError(
                f"git {' '.join(arguments)} exited {completed.returncode}"
            )
        return completed.stdout.decode("utf-8", "replace").strip()

    def controller(self, *arguments: str, expect: int = 0):
        completed = run_bounded(
            [sys.executable, str(self.proof.controller_path), *arguments],
            self.worktree,
            self.proof.environment,
        )
        if expect is not None and completed.returncode != expect:
            raise ProofError(
                f"hexctl {' '.join(arguments)} exited "
                f"{completed.returncode}, expected {expect}: "
                + completed.stderr.decode("utf-8", "replace").strip()
            )
        return completed

    def command_text(self, arguments: tuple[str, ...]) -> str:
        return "hexctl " + " ".join(arguments)

    def refusal_text(self, completed) -> str:
        """The controller's own refusal line, with run-local ids replaced."""
        stderr = completed.stderr.decode("utf-8", "replace").strip()
        line = ""
        for candidate in stderr.splitlines():
            if candidate.startswith("hexctl: error: "):
                line = candidate[len("hexctl: error: "):]
                break
        if not line:
            raise ProofError("a refusal carried no controller error line")
        line = FULL_OID.sub("<object-id>", line)
        line = DIGEST.sub("<digest>", line)
        return line

    def boundary(self) -> tuple[str, str]:
        """Token pair for the current state and ledger digests."""
        state = hashlib.sha256(
            (self.state_root / "state.json").read_bytes()
        ).hexdigest()
        ledger = hashlib.sha256(
            (self.state_root / "ledger.jsonl").read_bytes()
        ).hexdigest()
        record = self.proof.record
        return (
            record.token("state-digest", state,
                         f"{self.id}-state-{len(record.tokens)}"),
            record.token("ledger-digest", ledger,
                         f"{self.id}-ledger-{len(record.tokens)}"),
        )

    def commit_all(self, subject: str) -> str:
        self.git("add", "-A")
        self.git(
            "commit", "-q", "-m",
            f"{subject}\n\n{CO_AUTHOR}\n{ORIGIN_TRAILER}",
        )
        return self.git("rev-parse", "HEAD")

    # --------------------------------------------------------------- fixtures

    def write(self, relative: str, text: str) -> None:
        target = self.worktree / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def design_evidence(self) -> None:
        """One closed design-evidence record with its ten reports."""
        candidates = [
            {
                "id": "receipted-inoculation",
                "summary": "Receipt source-bound guarded evidence before "
                           "implementation opens.",
            },
            {
                "id": "late-audit",
                "summary": "Check the guard order only once implementation "
                           "has finished.",
            },
        ]
        criteria = [
            ("pre-edit-refusal", "correctness", "gate", "boolean",
             "equals", True),
            ("round-trips", "time", "metric", "count", "minimise", None),
            ("record-kinds", "space", "metric", "count", "minimise", None),
            ("role-compatibility", "compatibility", "gate", "boolean",
             "equals", True),
            ("resume-parity", "recovery", "gate", "boolean", "equals", True),
        ]
        criteria_records = [
            {
                "id": identifier,
                "concern": concern,
                "kind": kind,
                "stage": "selection",
                "owner": "fiat",
                "unit": unit,
                "comparator": comparator,
                "threshold": threshold,
                "blocks": "design-lock",
            }
            for identifier, concern, kind, unit, comparator, threshold
            in criteria
        ]
        outcomes = {
            ("receipted-inoculation", "pre-edit-refusal"): (True, "pass"),
            ("receipted-inoculation", "round-trips"): (1, "pass"),
            ("receipted-inoculation", "record-kinds"): (3, "pass"),
            ("receipted-inoculation", "role-compatibility"): (True, "pass"),
            ("receipted-inoculation", "resume-parity"): (True, "pass"),
            ("late-audit", "pre-edit-refusal"): (False, "fail"),
            ("late-audit", "round-trips"): (2, "pass"),
            ("late-audit", "record-kinds"): (4, "pass"),
            ("late-audit", "role-compatibility"): (True, "pass"),
            ("late-audit", "resume-parity"): (False, "fail"),
        }
        reports = self.state_root / "design-reports"
        reports.mkdir(parents=True, exist_ok=True)
        results = []
        for candidate in candidates:
            for criterion in criteria_records:
                value, state = outcomes[(candidate["id"], criterion["id"])]
                payload = {
                    "schema": "protasis-design-report/v1",
                    "candidate": candidate["id"],
                    "criterion": criterion["id"],
                    "value": value,
                    "unit": criterion["unit"],
                    "command": "python3 tests/suite.py",
                    "exit": 0,
                }
                raw = json.dumps(
                    payload, sort_keys=True, separators=(",", ":")
                ).encode("utf-8")
                name = f"{candidate['id']}-{criterion['id']}.json"
                (reports / name).write_bytes(raw)
                results.append(
                    {
                        "candidate": candidate["id"],
                        "criterion": criterion["id"],
                        "state": state,
                        "report": {
                            "path": f"design-reports/{name}",
                            "sha256": hashlib.sha256(raw).hexdigest(),
                        },
                    }
                )
        record = {
            "schema": "protasis-design-evidence/v1",
            "candidates": candidates,
            "criteria": criteria_records,
            "results": results,
            "selection": {
                "candidate": "receipted-inoculation",
                "rule": "unique-frontier",
                "policy_ref": None,
            },
        }
        (self.state_root / "design-evidence.json").write_text(
            json.dumps(record, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    def design_lock(self) -> str:
        state = json.loads((self.state_root / "state.json").read_text())
        design = state["receipts"]["study"]["design_evidence"]
        return (
            "```design-lock\n"
            f"schema | {design['schema']}\n"
            f"sha256 | {design['sha256']}\n"
            f"candidate | {design['selected']}\n"
            "```\n"
        )

    def capture(self) -> dict:
        state = json.loads((self.state_root / "state.json").read_text())
        return state["receipts"]["runbook"]["known_failure_inventory"]


# ----------------------------------------------------------------- the runner


GUARD_SOURCE = '''#!/usr/bin/env python3
"""One disposable guard: the product answer must be one."""

import argparse
import json
import os
import sys
import unittest

sys.path.insert(0, ".")


class ProductTests(unittest.TestCase):
    def test_answer_is_one(self):
        import product

        self.assertEqual(1, product.answer())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--report", required=True)
    options = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ProductTests)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    payload = {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "expectedFailures": len(result.expectedFailures),
        "unexpectedSuccesses": len(result.unexpectedSuccesses),
    }
    parent = os.path.dirname(options.report)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(options.report, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, sort_keys=True) + "\\n")
    if result.wasSuccessful() and result.testsRun:
        return 0
    return 1


raise SystemExit(main())
'''

FIXED_RUNNER = '''#!/usr/bin/env python3
"""One disposable guard that emits a fixed report."""

import argparse
import json
import os

PAYLOAD = {payload}
EXIT = {exit_code}

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--case", required=True)
parser.add_argument("--report", required=True)
options = parser.parse_args()
parent = os.path.dirname(options.report)
if parent:
    os.makedirs(parent, exist_ok=True)
with open(options.report, "w", encoding="utf-8") as handle:
    handle.write(json.dumps(PAYLOAD, sort_keys=True) + "\\n")
raise SystemExit(EXIT)
'''

SILENT_RUNNER = '''#!/usr/bin/env python3
"""One disposable guard that writes no report at all."""

raise SystemExit(3)
'''


def report_payload(**overrides) -> dict:
    payload = {
        "schema": "elenchus.unittest.v1",
        "complete": True,
        "testsRun": 1,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
        "expectedFailures": 0,
        "unexpectedSuccesses": 0,
    }
    payload.update(overrides)
    return payload


def counter_text(payload: dict) -> str:
    """The five admission counters one unittest report determines.

    The arithmetic is Elenchus's own, not a restatement of it: executed
    drops skipped and expected failures, errors absorb unexpected
    successes, and skipped absorbs expected failures.
    """
    executed = (
        payload["testsRun"] - payload["skipped"] - payload["expectedFailures"]
    )
    return (
        f"complete={str(payload['complete']).lower()};"
        f"executed={executed};"
        f"assertion_failures={payload['failures']};"
        f"errors={payload['errors'] + payload['unexpectedSuccesses']};"
        f"skipped={payload['skipped'] + payload['expectedFailures']}"
    )


VARIANTS = (
    ("passed", "non-guard-verdict", "passed", report_payload(), 0),
    ("zero-executed", "non-guard-verdict", "inconclusive",
     report_payload(testsRun=0), 1),
    ("infrastructure-error", "non-guard-verdict", "inconclusive",
     report_payload(errors=1), 1),
    ("skipped-case", "non-guard-verdict", "inconclusive",
     report_payload(skipped=1), 1),
    ("expected-failure", "non-guard-verdict", "inconclusive",
     report_payload(expectedFailures=1), 1),
    ("unexpected-success", "non-guard-verdict", "inconclusive",
     report_payload(unexpectedSuccesses=1), 1),
    ("incomplete-report", "runner-fault", "not-reached",
     report_payload(complete=False, failures=1), 1),
)


# ----------------------------------------------------------------- the proof


class Proof:
    """One disposable repository, three controller lanes, one transcript."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.repository = root / "repository"
        self.home = root / "home"
        self.environment = controlled_environment(self.home)
        self.controller_path = REPOSITORY_ROOT / CONTROLLER
        self.synopsis_path = REPOSITORY_ROOT / SYNOPSIS
        self.record = Record()
        self.source_view = {}

    # ------------------------------------------------------------ preparation

    def bind_sources(self) -> None:
        for relative in BOUND_SOURCES:
            path = REPOSITORY_ROOT / relative
            if not path.is_file() or path.is_symlink():
                raise ProofError(f"{relative} is not a tracked regular file")
            self.record.source(relative, path.read_bytes())

    def repository_git(self, *arguments: str) -> str:
        completed = run_bounded(
            ["git", *arguments], self.repository, self.environment
        )
        if completed.returncode != 0:
            raise ProofError(
                f"git {' '.join(arguments)} exited {completed.returncode}"
            )
        return completed.stdout.decode("utf-8", "replace").strip()

    def build_repository(self) -> None:
        """A signed repository whose every commit verifies locally."""
        self.home.mkdir()
        signer = self.root / "signer"
        generated = run_bounded(
            [
                "ssh-keygen", "-q", "-t", "ed25519", "-N", "",
                "-C", "fiat-proof@invalid", "-f", str(signer),
            ],
            self.root,
            self.environment,
        )
        if generated.returncode != 0:
            raise ProofError("the disposable signer could not be generated")
        public = signer.with_suffix(".pub")
        allowed = self.root / "allowed-signers"
        allowed.write_text(
            f"{SIGNER_IDENTITY} {public.read_text(encoding='utf-8').strip()}\n",
            encoding="utf-8",
        )

        self.repository.mkdir()
        self.repository_git("init", "-q", "-b", "main")
        for name, value in (
            ("user.name", SIGNER_NAME),
            ("user.email", SIGNER_IDENTITY),
            ("gpg.format", "ssh"),
            ("user.signingkey", str(public)),
            ("gpg.ssh.allowedSignersFile", str(allowed)),
            ("commit.gpgsign", "true"),
        ):
            self.repository_git("config", "--local", name, value)

        (self.repository / ".gitignore").write_text(
            ".elenchus/\ntmp/\n", encoding="utf-8"
        )
        (self.repository / "product.py").write_text(
            "def answer():\n    return 0\n", encoding="utf-8"
        )
        (self.repository / "audit/rounds").mkdir(parents=True)
        (self.repository / "evidence").mkdir()
        source_relative = "evidence/fixture-source.md"
        source_text = "One disposable audit source for the proof.\n"
        (self.repository / source_relative).write_text(
            source_text, encoding="utf-8"
        )
        source_sha256 = hashlib.sha256(source_text.encode()).hexdigest()
        view_relative = "evidence/fixture-source.synopsis.md"
        view_text = (
            "Synopsis schema=fiat-audit-synopsis/v1 | "
            f"source={source_relative} | source_sha256={source_sha256} | "
            "h2_count=0\n"
        )
        (self.repository / view_relative).write_text(
            view_text, encoding="utf-8"
        )
        self.source_view = {
            "id": "fixture-audit",
            "path": view_relative,
            "source_sha256": source_sha256,
            "view_sha256": hashlib.sha256(view_text.encode()).hexdigest(),
        }

        tests = self.repository / "tests"
        tests.mkdir()
        (tests / "check-map-v1.json").write_text(
            json.dumps(
                {
                    "schema": "wildcat.check-map.v1",
                    "checks": {
                        "root-suite": {
                            "argv": ["python3", "tests/suite.py"],
                            "cwd": ".",
                        },
                        "hexaemeron-suite": {
                            "argv": ["python3", "tests/suite.py"],
                            "cwd": ".",
                        },
                    },
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (tests / "suite.py").write_text(
            '"""The disposable repository suite."""\n\nraise SystemExit(0)\n',
            encoding="utf-8",
        )
        self.repository_git("add", "-A")
        self.repository_git(
            "commit", "-q", "-m",
            f"base\n\n{CO_AUTHOR}\n{ORIGIN_TRAILER}",
        )

    def start_lane(self, identifier: str, topic: str,
                   run_branch: str) -> Lane:
        started = run_bounded(
            [
                sys.executable, str(self.controller_path), "init",
                "--topic", topic, "--run-branch", run_branch,
            ],
            self.repository,
            self.environment,
        )
        if started.returncode != 0:
            raise ProofError(
                "init refused the disposable repository: "
                + started.stderr.decode("utf-8", "replace").strip()
            )
        lane = Lane(self, identifier, topic, run_branch)
        if not (lane.state_root / "state.json").is_file():
            raise ProofError(f"lane {identifier} has no controller state")
        return lane

    # ---------------------------------------------------------- guarded lane

    def guarded_lane(self) -> None:
        lane = self.start_lane(
            "guarded", "proof guarded lane", "fiat/proof-guarded"
        )
        lane.design_evidence()
        runner_relative = "tests/test_product_guard.py"
        finding_id = "kf-proof-01"
        report_file = f".elenchus/{finding_id}.json"
        green_report = f".elenchus/{finding_id}-green.json"
        inventory = {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": [dict(self.source_view)],
            "findings": [
                {
                    "id": finding_id,
                    "source_ref": "fixture-audit:1",
                    "failure": "the product answers zero where one is owed",
                    "guard_paths": [runner_relative],
                    "test_command": (
                        f"python3 {runner_relative} --case {finding_id} "
                        "--report {report}"
                    ),
                    "report_format": "unittest-json-v1",
                    "report_file": report_file,
                    "expected_guard_verdict": "guarded",
                    "green_command": (
                        f"python3 {runner_relative} --case {finding_id} "
                        f"--report {green_report}"
                    ),
                    "consuming_step": 1,
                }
            ],
            "no_known_findings": None,
        }
        lane.write(
            ".hexaemeron/study.md",
            "# Study: the disposable guarded lane\n\n"
            "**Assumption.** One disposable repository stands in for a "
            "delivery whose product answer is wrong.\n\n"
            "```risk-register\n"
            "guard-order | implementation opening before the guard | the "
            "inoculate phase refuses it\n"
            "```\n\n"
            "```known-failure-inventory\n"
            + json.dumps(inventory, indent=2)
            + "\n```\n",
        )
        arguments = ("done", "study", "--artifact", ".hexaemeron/study.md")
        completed = lane.controller(*arguments)
        self.record.phase(
            lane.id, "study", "was the study receipted with its design lock",
            lane.command_text(arguments), completed.returncode,
            "receipted", "source_views=1;findings=1",
            "design_candidate=receipted-inoculation",
        )

        lane.write(
            ".hexaemeron/runbook.md",
            lane.design_lock()
            + "# Runbook: the disposable guarded lane\n\n"
            "## Step 1: Guard the answer, then fix it\n\n"
            "**Goal.** Guard the known failure, then change the product.\n\n"
            "**Entry.** The capture is receipted.\n\n"
            "**Exit.** Run `python3 tests/suite.py`.\n\n"
            "**Files.** `product.py`.\n\n"
            "**Tests.** Run `python3 tests/suite.py`.\n\n"
            "**Disciplines.** none, disposable fixture.\n\n"
            f"Known-failure assignment: `{finding_id}` -> Step 1\n",
        )
        lane.write(
            ".hexaemeron/steps.json",
            json.dumps(["Guard the answer, then fix it"]) + "\n",
        )
        arguments = (
            "done", "runbook", "--artifact", ".hexaemeron/runbook.md",
            "--steps-file", ".hexaemeron/steps.json",
        )
        completed = lane.controller(*arguments)
        self.record.phase(
            lane.id, "runbook",
            "does the receipted runbook open the step in inoculate",
            lane.command_text(arguments), completed.returncode,
            "step 1 -> inoculate", "steps=1", "-",
        )

        arguments = ("next",)
        completed = lane.controller(*arguments)
        directive = json.loads(completed.stdout.decode("utf-8"))
        if directive["do"] != "inoculate":
            raise ProofError("the directive after runbook was not inoculate")
        step_branch = directive["branch"]
        parent = directive["step_parent"]
        parent_token = self.record.token("commit", parent, "step-parent")
        self.record.lane(lane.id, lane.topic, lane.run_branch, step_branch)
        self.record.phase(
            lane.id, "inoculate",
            "what does the controller direct before any product edit",
            lane.command_text(arguments), completed.returncode,
            f"do={directive['do']}",
            f"assigned={directive['assigned_count']};"
            f"remaining={len(directive['remaining_ids'])}",
            f"step_parent={parent_token};agent={directive['agent']};"
            f"then=hexctl done inoculate",
        )

        before = lane.boundary()
        arguments = ("done", "implement")
        completed = lane.controller(*arguments, expect=2)
        after = lane.boundary()
        self.record.refusal(
            lane.id, "implement-before-inoculate", "early-product",
            lane.command_text(arguments), completed.returncode,
            lane.refusal_text(completed), before, after, "-",
        )

        lane.git("checkout", "-q", "-b", step_branch)

        def reset_to_parent() -> None:
            lane.git("reset", "-q", "--hard", parent)
            lane.git("clean", "-qfd")

        for case, family, verdict, payload, exit_code in VARIANTS:
            reset_to_parent()
            lane.write(
                runner_relative,
                FIXED_RUNNER.format(payload=payload, exit_code=exit_code),
            )
            head = lane.commit_all(f"guard variant {case}")
            arguments = (
                "retain-guard", "--finding-id", finding_id,
                "--guard-commit", head,
            )
            before = lane.boundary()
            completed = lane.controller(*arguments, expect=2)
            after = lane.boundary()
            self.record.refusal(
                lane.id, case, family,
                "hexctl retain-guard --finding-id " + finding_id
                + " --guard-commit <object-id>",
                completed.returncode, lane.refusal_text(completed),
                before, after,
                counter_text(payload) + f";verdict={verdict}",
            )

        reset_to_parent()
        lane.write(runner_relative, SILENT_RUNNER)
        head = lane.commit_all("guard variant absent-report")
        arguments = (
            "retain-guard", "--finding-id", finding_id,
            "--guard-commit", head,
        )
        before = lane.boundary()
        completed = lane.controller(*arguments, expect=2)
        after = lane.boundary()
        self.record.refusal(
            lane.id, "absent-report", "runner-fault",
            "hexctl retain-guard --finding-id " + finding_id
            + " --guard-commit <object-id>",
            completed.returncode, lane.refusal_text(completed),
            before, after,
            "complete=absent;executed=absent;verdict=not-reached",
        )

        reset_to_parent()
        lane.write(runner_relative, GUARD_SOURCE)
        lane.write("product.py", "def answer():\n    return 1\n")
        head = lane.commit_all("guard the answer and change the product")
        arguments = (
            "retain-guard", "--finding-id", finding_id,
            "--guard-commit", head,
        )
        before = lane.boundary()
        completed = lane.controller(*arguments, expect=2)
        after = lane.boundary()
        self.record.refusal(
            lane.id, "undeclared-product-path", "early-product",
            "hexctl retain-guard --finding-id " + finding_id
            + " --guard-commit <object-id>",
            completed.returncode, lane.refusal_text(completed),
            before, after, "changed_paths=2;declared_guard_paths=1",
        )

        reset_to_parent()
        lane.write(runner_relative, GUARD_SOURCE)
        guard_commit = lane.commit_all("guard the answer")
        guard_token = self.record.token("commit", guard_commit, "guard-commit")
        guard_parent = lane.git(
            "show", "-s", "--no-show-signature", "--format=%P", guard_commit
        )
        if guard_parent != parent:
            raise ProofError("the guard commit does not sit on the step parent")
        self.record.relations[guard_token] = f"commit sole-parent={parent_token}"

        arguments = (
            "retain-guard", "--finding-id", finding_id,
            "--guard-commit", guard_commit,
        )
        completed = lane.controller(*arguments)
        retention = json.loads(completed.stdout.decode("utf-8"))
        manifest_token = self.record.token(
            "manifest-digest", retention["manifest"]["sha256"],
            "guard-manifest",
        )
        retained = lane.state_root / "steps/1/inoculation/reports" / (
            f"{finding_id}.report"
        )
        retained_bytes = retained.read_bytes()
        report_sha256 = hashlib.sha256(retained_bytes).hexdigest()
        if retention["retained_report"]["sha256"] != report_sha256:
            raise ProofError("the retained report digest does not match")
        self.record.phase(
            lane.id, "inoculate",
            "which exact report bytes and Git objects does the guard bind",
            "hexctl retain-guard --finding-id " + finding_id
            + " --guard-commit <object-id>",
            completed.returncode, f"disposition={retention['disposition']}",
            f"report_bytes={len(retained_bytes)};"
            + counter_text(report_payload(failures=1))
            + ";verdict=guarded",
            f"guard_commit={guard_token};step_parent={parent_token};"
            f"report_sha256={report_sha256};manifest={manifest_token};"
            f"retained_report={retention['retained_report']['path']}",
        )

        completed = lane.controller(*arguments)
        resumed = json.loads(completed.stdout.decode("utf-8"))
        if resumed["disposition"] != "already-retained":
            raise ProofError("a second retention did not resume the first")
        if resumed["manifest"]["sha256"] != retention["manifest"]["sha256"]:
            raise ProofError("the resumed manifest digest moved")
        self.record.phase(
            lane.id, "inoculate",
            "does a repeated retention resume the published evidence",
            "hexctl retain-guard --finding-id " + finding_id
            + " --guard-commit <object-id>",
            completed.returncode, f"disposition={resumed['disposition']}",
            "published_pairs=1",
            f"manifest={manifest_token}",
        )

        before = lane.boundary()
        arguments = ("halt", "--reason", "prove the resume boundary")
        lane.controller(*arguments)
        halted = json.loads(
            lane.controller("next").stdout.decode("utf-8")
        )
        if halted["do"] != "halted":
            raise ProofError("a halted run did not report itself halted")
        arguments = ("resume", "--note", "resumed for the proof")
        completed = lane.controller(*arguments)
        directive = json.loads(
            lane.controller("next").stdout.decode("utf-8")
        )
        if directive["do"] != "inoculate":
            raise ProofError("the resumed directive changed phase")
        if directive["completed_ids"] != [finding_id]:
            raise ProofError("the resumed directive lost its completed id")
        self.record.phase(
            lane.id, "inoculate",
            "does a halt and resume preserve the assigned and completed ids",
            lane.command_text(arguments), completed.returncode,
            f"do={directive['do']}",
            f"completed={len(directive['completed_ids'])};"
            f"remaining={len(directive['remaining_ids'])}",
            f"step_parent={parent_token}",
        )

        arguments = ("done", "inoculate")
        completed = lane.controller(*arguments)
        state = json.loads((lane.state_root / "state.json").read_text())
        receipt = state["steps"][0]["receipts"]["inoculate"]
        if receipt["guard_manifests"][0]["sha256"] != retention[
            "manifest"
        ]["sha256"]:
            raise ProofError("the inoculation receipt bound another manifest")
        self.record.phase(
            lane.id, "inoculate",
            "what does the inoculation receipt bind before implementation",
            lane.command_text(arguments), completed.returncode,
            "phase -> implement",
            f"assigned={len(receipt['assigned_ids'])};"
            f"guard_manifests={len(receipt['guard_manifests'])}",
            f"step_parent={parent_token};manifest={manifest_token};"
            "no_known_findings=null",
        )

        lane.write("product.py", "def answer():\n    return 1\n")
        final_commit = lane.commit_all("answer one")
        final_token = self.record.token("commit", final_commit, "final-commit")
        self.record.relations[final_token] = (
            f"commit descends-from={guard_token}"
        )
        arguments = (
            "done", "implement", "--branch", step_branch,
            "--commit", final_commit, "--tests", "python3 tests/suite.py",
        )
        completed = lane.controller(*arguments)
        state = json.loads((lane.state_root / "state.json").read_text())
        implement = state["steps"][0]["receipts"]["implement"]
        green = implement["final_green"]
        suites = "+".join(sorted(row["check"] for row in green["suites"]))
        green_report = (
            lane.state_root / "steps/1/final-green/reports" / (
                f"{finding_id}.report"
            )
        ).read_bytes()
        self.record.phase(
            lane.id, "implement",
            "is the guard green on the fixed tree and both suites clean",
            "hexctl done implement --branch <step-branch> --commit "
            "<object-id> --tests python3 tests/suite.py",
            completed.returncode, "phase -> audit",
            f"verified_commits={len(implement['verified_commits'])};"
            f"green_manifests={len(green['manifests'])};"
            f"suite_rows={len(green['suites'])};"
            f"green_report_bytes={len(green_report)};"
            + counter_text(report_payload()),
            f"final_commit={final_token};suites={suites};"
            f"green_report_sha256={hashlib.sha256(green_report).hexdigest()}",
        )

        arguments = (
            "record", "security_suite",
            "waived:the disposable repository carries no Solidity",
        )
        lane.controller(*arguments)
        state = json.loads((lane.state_root / "state.json").read_text())
        log_relative = state["config"]["audit"]["log_path"]
        lane.write(
            log_relative,
            "## Step 1, round 1 -- 2026-09-11T00:00:00Z\n\n"
            "Audit schema: fiat-audit-round/v2\n\n"
            "Covered: guard-order=reviewed\n\n"
            "Not checked: none\n\n"
            "Elenchus verdict: null\n\n"
            "| id | severity | file | finding | status |\n"
            "| --- | --- | --- | --- | --- |\n"
            "| -- | -- | -- | none | -- |\n\n"
            "Leads not pursued: none\n",
        )
        rendered = run_bounded(
            [
                sys.executable, str(self.synopsis_path), "--write",
                str(lane.worktree),
            ],
            lane.worktree,
            self.environment,
        )
        if rendered.returncode != 0:
            raise ProofError("the audit synopsis could not be rendered")
        arguments = (
            "audit-round", "--findings", "0", "--audit-filter", AUDIT_FILTER,
            "--phylax-exit", "0", "--ephoros-exit", "0",
            "--hypomnema-exit", "0",
        )
        completed = lane.controller(*arguments)
        state = json.loads((lane.state_root / "state.json").read_text())
        rounds = state["steps"][0]["audit"]["rounds"]
        self.record.phase(
            lane.id, "audit",
            "does the audit round record its own log boundary and lints",
            lane.command_text(arguments), completed.returncode,
            "round 1 recorded",
            f"rounds={len(rounds)};findings={rounds[0]['findings']};"
            f"phylax=0;ephoros=0;hypomnema=0",
            f"log={log_relative};audit_filter={AUDIT_FILTER}",
        )

        arguments = ("verify",)
        completed = lane.controller(*arguments)
        entries = len(
            [
                line
                for line in (
                    lane.state_root / "ledger.jsonl"
                ).read_text().splitlines()
                if line
            ]
        )
        final = lane.boundary()
        self.record.phase(
            lane.id, "verify",
            "does the finished lane verify its own chain and state",
            lane.command_text(arguments), completed.returncode,
            "chain intact, state consistent",
            f"ledger_entries={entries}",
            f"state={final[0]};ledger={final[1]}",
        )

    # -------------------------------------------------------- unguarded lane

    def unguarded_lane(self) -> None:
        """The fourth verdict: guard blobs carrying no test file at all.

        Elenchus answers `unguarded` rather than a classification, and that
        answer reaches Fiat as a result missing the report members a verdict
        carries, so the controller refuses it with the same text a runner
        fault earns. The lane exists to record that: the refusal is real, and
        it does not tell the two apart. Its step can never complete, because
        the declared guard path can never be admitted, so the lane stops at
        the refusal it was built for.
        """
        lane = self.start_lane(
            "unguarded", "proof unguarded lane", "fiat/proof-unguarded"
        )
        lane.design_evidence()
        runner_relative = "support/guard_runner.py"
        finding_id = "kf-proof-02"
        inventory = {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": [dict(self.source_view)],
            "findings": [
                {
                    "id": finding_id,
                    "source_ref": "fixture-audit:1",
                    "failure": "the declared guard carries no test file",
                    "guard_paths": [runner_relative],
                    "test_command": (
                        f"python3 {runner_relative} --case {finding_id} "
                        "--report {report}"
                    ),
                    "report_format": "unittest-json-v1",
                    "report_file": f".elenchus/{finding_id}.json",
                    "expected_guard_verdict": "guarded",
                    "green_command": (
                        f"python3 {runner_relative} --case {finding_id} "
                        f"--report .elenchus/{finding_id}-green.json"
                    ),
                    "consuming_step": 1,
                }
            ],
            "no_known_findings": None,
        }
        lane.write(
            ".hexaemeron/study.md",
            "# Study: the disposable unguarded lane\n\n"
            "**Assumption.** A declared guard path that is not a test file "
            "still passes the inventory contract.\n\n"
            "```risk-register\n"
            "verdict-confusion | a fourth verdict read as a guard | the "
            "retention refusal\n"
            "```\n\n"
            "```known-failure-inventory\n"
            + json.dumps(inventory, indent=2)
            + "\n```\n",
        )
        arguments = ("done", "study", "--artifact", ".hexaemeron/study.md")
        completed = lane.controller(*arguments)
        self.record.phase(
            lane.id, "study",
            "was a study whose declared guard is not a test receipted",
            lane.command_text(arguments), completed.returncode,
            "receipted", "source_views=1;findings=1", "-",
        )
        lane.write(
            ".hexaemeron/runbook.md",
            lane.design_lock()
            + "# Runbook: the disposable unguarded lane\n\n"
            "## Step 1: Declare a guard that is not a test\n\n"
            "**Goal.** Reach the retention boundary with no test blob.\n\n"
            "**Entry.** The capture is receipted.\n\n"
            "**Exit.** Run `python3 tests/suite.py`.\n\n"
            "**Files.** `product.py`.\n\n"
            "**Tests.** Run `python3 tests/suite.py`.\n\n"
            "**Disciplines.** none, disposable fixture.\n\n"
            f"Known-failure assignment: `{finding_id}` -> Step 1\n",
        )
        lane.write(
            ".hexaemeron/steps.json",
            json.dumps(["Declare a guard that is not a test"]) + "\n",
        )
        arguments = (
            "done", "runbook", "--artifact", ".hexaemeron/runbook.md",
            "--steps-file", ".hexaemeron/steps.json",
        )
        completed = lane.controller(*arguments)
        directive = json.loads(
            lane.controller("next").stdout.decode("utf-8")
        )
        step_branch = directive["branch"]
        self.record.lane(lane.id, lane.topic, lane.run_branch, step_branch)
        self.record.phase(
            lane.id, "runbook",
            "does the step still open in inoculate with that guard declared",
            lane.command_text(arguments), completed.returncode,
            f"do={directive['do']}",
            f"assigned={directive['assigned_count']}", "-",
        )
        lane.git("checkout", "-q", "-b", step_branch)
        lane.write(
            runner_relative,
            FIXED_RUNNER.format(
                payload=report_payload(failures=1), exit_code=1
            ),
        )
        head = lane.commit_all("declare a guard that is not a test")
        arguments = (
            "retain-guard", "--finding-id", finding_id,
            "--guard-commit", head,
        )
        before = lane.boundary()
        completed = lane.controller(*arguments, expect=2)
        after = lane.boundary()
        self.record.refusal(
            lane.id, "no-test-blob", "non-guard-verdict",
            "hexctl retain-guard --finding-id " + finding_id
            + " --guard-commit <object-id>",
            completed.returncode, lane.refusal_text(completed),
            before, after,
            "complete=not-reached;executed=not-reached;verdict=unguarded",
        )

        arguments = ("verify",)
        completed = lane.controller(*arguments)
        entries = len(
            [
                line
                for line in (
                    lane.state_root / "ledger.jsonl"
                ).read_text().splitlines()
                if line
            ]
        )
        final = lane.boundary()
        self.record.phase(
            lane.id, "verify",
            "does the refused lane still verify its own chain and state",
            lane.command_text(arguments), completed.returncode,
            "chain intact, state consistent",
            f"ledger_entries={entries}",
            f"state={final[0]};ledger={final[1]}",
        )

    # --------------------------------------------------------- no-known lane

    def no_known_lane(self) -> None:
        lane = self.start_lane(
            "no-known", "proof no known lane", "fiat/proof-no-known"
        )
        lane.design_evidence()
        checked_view = {
            "id": self.source_view["id"],
            "source_sha256": self.source_view["source_sha256"],
            "view_sha256": self.source_view["view_sha256"],
        }
        inventory = {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": [dict(self.source_view)],
            "findings": [],
            "no_known_findings": {
                "source_views": [checked_view],
                "consuming_step": 1,
                "surveyor_assertion": "no-known-findings",
            },
        }
        lane.write(
            ".hexaemeron/study.md",
            "# Study: the disposable no-known lane\n\n"
            "**Assumption.** The lane carries no assigned known failure, so "
            "its claim has to be written rather than assumed.\n\n"
            "```risk-register\n"
            "claim-absence | an empty array read as evidence | an explicit "
            "recorded claim\n"
            "```\n\n"
            "```known-failure-inventory\n"
            + json.dumps(inventory, indent=2)
            + "\n```\n",
        )
        arguments = ("done", "study", "--artifact", ".hexaemeron/study.md")
        completed = lane.controller(*arguments)
        self.record.phase(
            lane.id, "study",
            "was a study with no assigned finding receipted",
            lane.command_text(arguments), completed.returncode,
            "receipted", "source_views=1;findings=0", "-",
        )
        lane.write(
            ".hexaemeron/runbook.md",
            lane.design_lock()
            + "# Runbook: the disposable no-known lane\n\n"
            "## Step 1: Release with no assigned finding\n\n"
            "**Goal.** Record an explicit no-known-findings claim.\n\n"
            "**Entry.** The capture is receipted.\n\n"
            "**Exit.** Run `python3 tests/suite.py`.\n\n"
            "**Files.** `product.py`.\n\n"
            "**Tests.** Run `python3 tests/suite.py`.\n\n"
            "**Disciplines.** none, disposable fixture.\n",
        )
        lane.write(
            ".hexaemeron/steps.json",
            json.dumps(["Release with no assigned finding"]) + "\n",
        )
        arguments = (
            "done", "runbook", "--artifact", ".hexaemeron/runbook.md",
            "--steps-file", ".hexaemeron/steps.json",
        )
        completed = lane.controller(*arguments)
        directive = json.loads(
            lane.controller("next").stdout.decode("utf-8")
        )
        step_branch = directive["branch"]
        self.record.lane(lane.id, lane.topic, lane.run_branch, step_branch)
        self.record.phase(
            lane.id, "runbook",
            "does a zero-assignment step still open in inoculate",
            lane.command_text(arguments), completed.returncode,
            f"do={directive['do']}",
            f"assigned={directive['assigned_count']}", "-",
        )
        lane.git("checkout", "-q", "-b", step_branch)

        before = lane.boundary()
        arguments = ("done", "inoculate")
        completed = lane.controller(*arguments, expect=2)
        after = lane.boundary()
        self.record.refusal(
            lane.id, "absent-no-known-claim", "absent-claim",
            lane.command_text(arguments), completed.returncode,
            lane.refusal_text(completed), before, after, "claims=0",
        )

        capture = lane.capture()
        claim = {
            "schema": "fiat-no-known-findings/v1",
            "assertion": "no-known-findings-for-step",
            "consuming_step": 1,
            "study_sha256": capture["study_sha256"],
            "inventory_sha256": capture["inventory_sha256"],
            "source_views": [
                {
                    "id": view["id"],
                    "source_sha256": view["source_sha256"],
                    "view_sha256": view["view_sha256"],
                }
                for view in capture["source_views"]
            ],
        }
        lane.write(
            ".hexaemeron/steps/1/inoculation/no-known-findings.json",
            json.dumps(claim, indent=2, sort_keys=True) + "\n",
        )
        arguments = ("done", "inoculate")
        completed = lane.controller(*arguments)
        state = json.loads((lane.state_root / "state.json").read_text())
        receipt = state["steps"][0]["receipts"]["inoculate"]
        recorded = receipt["no_known_findings"]
        if recorded is None:
            raise ProofError("the no-known receipt carries no claim")
        study_token = self.record.token(
            "study-digest", capture["study_sha256"], "no-known-study"
        )
        inventory_token = self.record.token(
            "inventory-digest", capture["inventory_sha256"],
            "no-known-inventory",
        )
        self.record.phase(
            lane.id, "inoculate",
            "what does the explicit no-known-findings receipt bind",
            lane.command_text(arguments), completed.returncode,
            "phase -> implement",
            f"assigned={len(receipt['assigned_ids'])};"
            f"source_views={len(recorded['source_views'])};"
            f"consuming_step={recorded['consuming_step']}",
            f"assertion={recorded['assertion']};study={study_token};"
            f"inventory={inventory_token}",
        )

        arguments = ("verify",)
        completed = lane.controller(*arguments)
        entries = len(
            [
                line
                for line in (
                    lane.state_root / "ledger.jsonl"
                ).read_text().splitlines()
                if line
            ]
        )
        final = lane.boundary()
        self.record.phase(
            lane.id, "verify",
            "does the no-known lane verify its own chain and state",
            lane.command_text(arguments), completed.returncode,
            "chain intact, state consistent",
            f"ledger_entries={entries}",
            f"state={final[0]};ledger={final[1]}",
        )


# ------------------------------------------------------------- the transcript


PROSE = """# Proof: the inoculation contract, driven end to end

`proof.py` beside this file builds one disposable signed Git repository,
runs the checked-in Fiat controller through three lanes inside it, writes
these bytes, and then checks them against the run it just finished. Every
number, command, exit status, path and digest below came out of that run.
The question, case, class and result labels are `proof.py`'s own, and so is
every `verdict=` value; the refusal matrix below says what that column
rests on.

## What this run of the contract used

The delivery that built this contract ran on the pinned plugin-cache
controller, which predates the gates the contract adds. Its runbook receipt
carries no known-failure capture, so every reader in that run took the
legacy branch, and its guard and final-green evidence came from running
Elenchus and the green commands by hand. That is the manual bootstrap
procedure, and it is the only procedure that delivery used.

So the claim here is narrow and it is the only one these bytes support: the
controller checked into this tree enforces the contract on the disposable
repository `proof.py` just drove. It does not claim that the controller
which produced this run's receipts enforced anything.

## What the lanes establish

The guarded lane carries one assigned known failure. It shows the receipted
runbook opening its step in `inoculate` rather than `implement`, the
controller refusing implementation before a valid inoculation receipt, every
non-guard verdict and both runner faults refused at retention, one admitted
guard binding exact report bytes and exact Git objects, a repeated retention
resuming the published pair rather than sampling a second run, a halt and
resume preserving the assigned and completed ids, the inoculation receipt,
the fixed-tree green run with both declared suites, one audit round, and a
final verification.

The no-known lane carries no assigned finding. It shows the same step
opening in `inoculate`, the controller refusing the phase while the explicit
claim is absent, and the receipt binding that claim's study, inventory and
source-view digests once it exists. An empty array is not what closed it.

The unguarded lane declares a guard path that is not a test file, which the
inventory contract permits and the guard runner cannot classify. Its step can
never finish, so the lane stops at the refusal it exists for.

## What the refusal matrix covers

Six report shapes reach the classifier and come back as something other than
`guarded`: a passing guard, a run that executed nothing, a run carrying an
infrastructure error, and three whose single case was skipped, expected to
fail, or unexpectedly succeeded. Three shapes never reach it at all: a report
the runner declared incomplete, which the parser rejects first; no report
written; and guard blobs holding no test file, which answer `unguarded`
instead of a classification.

The controller refuses all nine. The last three share one refusal text,
because a result missing a verdict's own members is what Fiat sees in each
case, so that text cannot tell an unguarded commit from a broken runner. The
verdict column below is therefore inferred from the bound counters under
Elenchus's published classification, not read out of the refusal, and the
rows that never reached classification say so instead of naming a verdict.

## What this does not establish

These bytes say nothing about the controller in the plugin cache, about any
repository other than the one the proof created and destroyed, or about
timing. The proof measures correctness only and makes no latency or
throughput claim. The disposable guard, product, suite and audit source are
fixtures, not the real ones. A lane stops at its own verification: nothing
here pushes, opens a pull request, merges, or completes a step.

## The bound record

The block below is what the checker reads. Each line is one record: fields
are separated by ` | `, the first field names the kind, and a value written
`@name` is a token whose actual run-local value is resolved through the
`bind` records. Changing any command, exit status, count, commit token, path
or digest in it makes the check refuse.
"""


def render(record: Record) -> bytes:
    """Render the transcript from the record, deterministically."""
    lines: list[str] = []
    for row in record.sources:
        lines.append(
            f"source | {row['path']} | {row['bytes']} | {row['sha256']}"
        )
    for row in record.lanes:
        lines.append(
            f"lane | {row['id']} | {row['topic']} | {row['run_branch']} | "
            f"{row['step_branch']}"
        )
    for row in record.phases:
        lines.append(
            f"phase | {row['lane']} | {row['ordinal']} | {row['phase']} | "
            f"{row['question']} | {row['command']} | {row['exit']} | "
            f"{row['result']} | {row['counts']} | {row['evidence']}"
        )
    for row in record.refusals:
        lines.append(
            f"refuse | {row['lane']} | {row['case']} | {row['class']} | "
            f"{row['command']} | {row['exit']} | {row['message']} | "
            f"{row['state']} | {row['ledger']} | {row['counters']}"
        )
    for name in sorted(record.tokens):
        lines.append(f"bind | {name} | {record.relations[name]}")

    body = [PROSE]
    for start in range(0, len(lines), RECORD_FENCE_LINES):
        chunk = lines[start:start + RECORD_FENCE_LINES]
        body.append(
            f"\n```{RECORD_FENCE}\n" + "\n".join(chunk) + "\n```\n"
        )
    return "".join(body).encode("utf-8")


def extract(text: str) -> list[str]:
    """Every record line, in order, out of the fenced record blocks."""
    lines: list[str] = []
    inside = False
    for line in text.splitlines():
        if not inside:
            if line.strip() == f"```{RECORD_FENCE}":
                inside = True
            continue
        if line.strip() == "```":
            inside = False
            continue
        lines.append(line)
    if inside:
        raise ProofError("a record block in the transcript is not closed")
    return lines


def check(record: Record, text: str) -> list[str]:
    """Every way the transcript disagrees with the run it describes."""
    refusals: list[str] = []
    parsed: dict[str, list[list[str]]] = {
        "source": [], "lane": [], "phase": [], "refuse": [], "bind": [],
    }
    for line in extract(text):
        fields = line.split(" | ")
        kind = fields[0]
        if kind not in parsed:
            refusals.append(f"unknown record kind {kind!r}")
            continue
        parsed[kind].append(fields[1:])

    expected_sources = [
        [row["path"], str(row["bytes"]), row["sha256"]]
        for row in record.sources
    ]
    if parsed["source"] != expected_sources:
        refusals.append("the bound source table does not match this tree")
    for fields in parsed["source"]:
        if len(fields) != 3:
            refusals.append("a source record has the wrong field count")
            continue
        path = REPOSITORY_ROOT / fields[0]
        try:
            raw = path.read_bytes()
        except OSError:
            refusals.append(f"bound source {fields[0]} cannot be read")
            continue
        if str(len(raw)) != fields[1]:
            refusals.append(f"bound source {fields[0]} has other byte length")
        if hashlib.sha256(raw).hexdigest() != fields[2]:
            refusals.append(f"bound source {fields[0]} has another digest")

    expected_lanes = [
        [row["id"], row["topic"], row["run_branch"], row["step_branch"]]
        for row in record.lanes
    ]
    if parsed["lane"] != expected_lanes:
        refusals.append("the lane table does not match the run")

    expected_phases = [
        [
            row["lane"], row["ordinal"], row["phase"], row["question"],
            row["command"], row["exit"], row["result"], row["counts"],
            row["evidence"],
        ]
        for row in record.phases
    ]
    if parsed["phase"] != expected_phases:
        for index, expected in enumerate(expected_phases):
            if index >= len(parsed["phase"]):
                refusals.append(f"phase record {index + 1} is missing")
                continue
            if parsed["phase"][index] != expected:
                refusals.append(
                    f"phase record {index + 1} disagrees with the run"
                )
        if len(parsed["phase"]) > len(expected_phases):
            refusals.append("the transcript carries an unrecorded phase")

    expected_refusals = [
        [
            row["lane"], row["case"], row["class"], row["command"],
            row["exit"], row["message"], row["state"], row["ledger"],
            row["counters"],
        ]
        for row in record.refusals
    ]
    if parsed["refuse"] != expected_refusals:
        for index, expected in enumerate(expected_refusals):
            if index >= len(parsed["refuse"]):
                refusals.append(f"refusal record {index + 1} is missing")
                continue
            if parsed["refuse"][index] != expected:
                refusals.append(
                    f"refusal record {index + 1} disagrees with the run"
                )
        if len(parsed["refuse"]) > len(expected_refusals):
            refusals.append("the transcript carries an unrecorded refusal")

    expected_binds = [
        [name, record.relations[name]] for name in sorted(record.tokens)
    ]
    if parsed["bind"] != expected_binds:
        refusals.append("the token bind table does not match the run")

    declared = {fields[0] for fields in parsed["bind"] if fields}
    used = set()
    for kind in ("phase", "refuse"):
        for fields in parsed[kind]:
            for field in fields:
                used.update(re.findall(r"@[a-z0-9-]+", field))
    unknown = sorted(used - declared)
    if unknown:
        refusals.append("tokens used with no bind record: " + ", ".join(unknown))
    unused = sorted(declared - used)
    if unused:
        refusals.append("tokens bound but never used: " + ", ".join(unused))

    for fields in parsed["bind"]:
        if len(fields) != 2:
            refusals.append("a bind record has the wrong field count")
            continue
        name, relation = fields
        value = record.tokens.get(name)
        if value is None:
            refusals.append(f"token {name} names no run-local value")
            continue
        parts = relation.split()
        if not parts:
            refusals.append(f"token {name} declares no kind")
            continue
        for clause in parts[1:]:
            if "=" not in clause:
                refusals.append(f"token {name} has a malformed relation")
                continue
            left, right = clause.split("=", 1)
            other = record.tokens.get(right)
            if other is None:
                refusals.append(
                    f"token {name} relates to unbound {right}"
                )
                continue
            if left == "sole-parent" and other == value:
                refusals.append(
                    f"token {name} cannot be its own parent {right}"
                )
            if left == "descends-from" and other == value:
                refusals.append(
                    f"token {name} cannot descend from itself"
                )

    stated = STATED_LANES.search(text)
    if stated is None:
        refusals.append(
            "the transcript states no lane count the run can answer"
        )
    elif LANE_WORDS[stated.group(1)] != len(record.lanes):
        refusals.append(
            f"the transcript says {stated.group(1)} lanes and the run "
            f"drove {len(record.lanes)}"
        )

    for fields in parsed["refuse"]:
        if len(fields) != 9:
            refusals.append("a refusal record has the wrong field count")
            continue
        for column, label in ((6, "state"), (7, "ledger")):
            before, _, after = fields[column].partition("/")
            if not after:
                refusals.append(f"a refusal has no {label} boundary pair")
                continue
            if before != after:
                refusals.append(
                    f"a refusal moved the {label} digest from {before} "
                    f"to {after}"
                )
            if record.tokens.get(before) is None:
                refusals.append(f"a refusal names unbound {label} {before}")
    return refusals


def mutate(text: str, family: str) -> str:
    """Change exactly one bound field of one record, by class."""
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        fields = line.rstrip("\n").split(" | ")
        if family == "command" and fields[0] == "phase":
            fields[5] = fields[5] + " --tests other"
        elif family == "exit" and fields[0] == "refuse":
            fields[5] = "0"
        elif family == "count" and fields[0] == "phase" and fields[8] != "-":
            fields[8] = re.sub(r"=(\d+)", lambda m: f"={int(m.group(1)) + 1}",
                               fields[8], count=1)
        elif family == "commit" and fields[0] == "bind" and (
            "sole-parent=" in line
        ):
            fields[2] = fields[2].replace("sole-parent=@step-parent",
                                          "sole-parent=@guard-commit")
        elif family == "path" and fields[0] == "source":
            fields[1] = fields[1].replace("/scripts/", "/scripts/other/")
        elif family == "digest" and fields[0] == "source":
            digest = fields[3]
            fields[3] = ("0" if digest[0] != "0" else "1") + digest[1:]
        else:
            continue
        lines[index] = " | ".join(fields) + "\n"
        return "".join(lines)
    raise ProofError(f"the transcript carries no {family} field to change")


def atomic_write(target: Path, payload: bytes) -> None:
    """Replace the transcript in one step, or leave the old bytes alone."""
    descriptor, temporary = tempfile.mkstemp(
        prefix=".proof-", suffix=".md", dir=str(target.parent)
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except OSError:
        Path(temporary).unlink(missing_ok=True)
        raise


# -------------------------------------------------------------------- driver


def arguments(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--transcript",
        default=str(TRANSCRIPT),
        help="where to write the checked transcript",
    )
    parser.add_argument(
        "--keep-temporary",
        action="store_true",
        help="leave the disposable repository behind for inspection",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    options = arguments(sys.argv[1:] if argv is None else argv)
    if shutil.which("git") is None or shutil.which("ssh-keygen") is None:
        print("proof.py: git and ssh-keygen are required", file=sys.stderr)
        return 2
    transcript = Path(options.transcript).resolve()
    if not transcript.parent.is_dir():
        print("proof.py: the transcript directory does not exist",
              file=sys.stderr)
        return 2

    root = Path(tempfile.mkdtemp(prefix="fiat-inoculation-proof-"))
    try:
        proof = Proof(root)
        proof.bind_sources()
        proof.build_repository()
        proof.guarded_lane()
        proof.no_known_lane()
        proof.unguarded_lane()
        payload = render(proof.record)
        atomic_write(transcript, payload)
        written = transcript.read_bytes()
        if written != payload:
            print("proof.py: the transcript on disk is not what was rendered",
                  file=sys.stderr)
            return 1
        text = written.decode("utf-8")
        complaints = check(proof.record, text)
        if complaints:
            for complaint in complaints:
                print(f"proof.py: {complaint}", file=sys.stderr)
            return 1
        for family in MUTATION_CLASSES:
            if not check(proof.record, mutate(text, family)):
                print(f"proof.py: a changed {family} was not refused",
                      file=sys.stderr)
                return 1
            print(f"replay refuses a changed {family}")
    except ProofError as error:
        print(f"proof.py: {error}", file=sys.stderr)
        return 1
    except subprocess.TimeoutExpired:
        print("proof.py: a child command did not finish in time",
              file=sys.stderr)
        return 1
    finally:
        if options.keep_temporary:
            print(f"disposable repository kept at {root}")
        else:
            shutil.rmtree(root, ignore_errors=True)

    print(
        f"proof: {len(proof.record.lanes)} lanes, "
        f"{len(proof.record.phases)} phases, "
        f"{len(proof.record.refusals)} refusals, "
        f"{len(proof.record.tokens)} bound tokens; "
        f"transcript checked at {transcript}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
