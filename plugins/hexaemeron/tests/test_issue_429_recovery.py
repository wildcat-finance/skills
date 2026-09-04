#!/usr/bin/env python3
"""Permanent composition guards for the issue 429 recovery."""

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[3]
PROOF_MODE = "--proof" in sys.argv
PROOF = (
    ROOT
    / "plugins"
    / "hexaemeron"
    / "docs"
    / "audit-record-schema-timestamp-synopsis-recovery"
    / "proof.md"
)
CONTROLLER = ROOT / "plugins" / "hexaemeron" / "skills" / "fiat" / "scripts" / "hexctl.py"
GENERATOR = CONTROLLER.with_name("audit_synopsis.py")
PRODUCT_HEAD = "f11fe174161f46bf79080422169ad943214e1b4f"
PINNED_BASE = "c4650f02a979e859ce36374779eac9cd70744288"
COMPOSITION = "0fb3bcfba14a36c623f380105504d41d1eb66c86"
STEP_ONE_PRE_PROSE_HEAD = "ab9e70d142fdad70b089268615e107f1733f7900"
STEP_ONE_HEAD = "dda57e8a3258b5c26891fe0b6a39396ce13b9490"
TRAILER_FIXTURE_PARENT = "a79e663a136c446a6653ddbb14648782fef99173"
TRAILER_FIXTURE = "43babf204a0a21435f49a6681d355b692232b1f5"
PRODUCT_FIAT_VERSION = "5.25.1"
PRODUCT_HEXAEMERON_VERSION = "1.6.1"
INTEGRATED_FIAT_VERSION = "5.26.1"
INTEGRATED_HEXAEMERON_VERSION = "1.6.1"
PRODUCT_CONTROLLER_SHA256 = (
    "2c29f696f2b368a334eb4a880e745fa3cd468cc9c385e36346000aed7c91ba9f"
)
RECOVERY_GENERATOR_SHA256 = (
    "2972258d0c363bee0cc7e97668da96bcbb5ea19421fc278eefdae60ddcde9d75"
)
INTEGRATED_CONTROLLER_SHA256 = (
    "2ce507d0e3bf2e7b0c4a9880cb6486ecb2c451423d6fd84eb58ba7a218bc80e8"
)
PROOF_SHA256 = "badb5f3eeffe9927453e43b8d3dbdcfbda87773e5b9ce1cbb7973cc44796bafb"
PRODUCT_SUFFIX = (
    ROOT
    / "audit"
    / "rounds"
    / "fiat-429-audit-record-schema-timestamp-synopsis.md"
)
RECOVERY_LOG_SOURCE = (
    "audit/rounds/fiat-429-recover-issue-429-from-pull-request-552.md"
)
INTEGRATED_UNTAGGED_SOURCE = (
    "audit/rounds/fiat-331-bind-user-supplied-sentences-to-the-recorded.md"
)
PRODUCT_AUDIT_SOURCES = (
    "audit/AUDIT.md",
    "audit/rounds/fiat-429-audit-record-schema-timestamp-synopsis.md",
    RECOVERY_LOG_SOURCE,
    "audit/rounds/fiat-576-give-each-fiat-run-its-own-audit-log-path.md",
    "audit/rounds/fiat-594-bind-a-step-merge-to-the-pull-request-the-di.md",
    "plugins/ariadne/audit/AUDIT.md",
    "plugins/hexaemeron/audit/AUDIT.md",
    "plugins/pandects/audit/AUDIT.md",
    "plugins/probitas/audit/AUDIT.md",
    "plugins/tabularium/audit/AUDIT.md",
)
PRODUCT_SUFFIX_SHA256 = (
    "51891eaf4a387acb79ab65c9508c09cb84828cb40c475a3b363fddcecd74fe8d"
)
ROOT_AUDIT_SHA256 = (
    "c271237691dc76a95059651f08710411e9d095b12d92b3d5f960182e357bb9fa"
)
STUDY_SHA256 = (
    "14576e2985024efc8e950b9ad2a22977fb9f2d6e6c64a7460996d63b577056d2"
)
RUNBOOK_SHA256 = (
    "e2a2488af4cab26db47275c8ac0c9dbf9aa2278b9ca91279005168e87f039e75"
)
OVERLAPS = (
    ".agents/plugins/marketplace.json",
    ".claude-plugin/marketplace.json",
    "audit/AUDIT.md",
    "plugins/hexaemeron/.claude-plugin/plugin.json",
    "plugins/hexaemeron/.codex-plugin/plugin.json",
    "plugins/hexaemeron/README.md",
    "plugins/hexaemeron/agents/warden.md",
    "plugins/hexaemeron/skills/fiat/EVOLUTION.md",
    "plugins/hexaemeron/skills/fiat/SKILL.md",
    "plugins/hexaemeron/skills/fiat/references/audit-loop.md",
    "plugins/hexaemeron/skills/fiat/scripts/hexctl.py",
    "plugins/hexaemeron/tests/test_fiat_skill.py",
    "plugins/hexaemeron/tests/test_hexctl.py",
    "tests/promise_machine_coverage.json",
    "tests/test_evolution_contract.py",
    "tests/test_version_propagation.py",
)
COMPOSITION_MANIFEST = (
    ROOT
    / "plugins"
    / "hexaemeron"
    / "docs"
    / "audit-record-schema-timestamp-synopsis-recovery"
    / "composition-manifest.json"
)
RECOVERY_DOCS = COMPOSITION_MANIFEST.parent
TRAILERS = (
    "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>",
    "Wildcat-Origin: shoggoth",
)


def git(*args, text=False):
    return subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=text,
    ).stdout


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class Issue429RecoveryTests(unittest.TestCase):
    def composition_commit(self):
        matches = []
        for line in git("rev-list", "--parents", "HEAD", text=True).splitlines():
            fields = line.split()
            if len(fields) == 3 and fields[1:] == [PRODUCT_HEAD, PINNED_BASE]:
                matches.append(fields[0])
        self.assertEqual(
            len(matches),
            1,
            "the history must contain one product-first, pinned-base-second join",
        )
        return matches[0]

    def test_composition_has_exact_parent_order_and_signed_header(self):
        commit = self.composition_commit()
        self.assertEqual(commit, COMPOSITION)
        raw = git("cat-file", "commit", commit)
        header = raw.split(b"\n\n", 1)[0]
        self.assertIn(b"gpgsig ", header)
        subprocess.run(
            ["git", "verify-commit", commit],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        message = raw.split(b"\n\n", 1)[1].decode("utf-8")
        for trailer in TRAILERS:
            self.assertEqual(message.splitlines().count(trailer), 1)
        self.assertEqual(
            git("show", "-s", "--format=%P", commit, text=True).strip(),
            f"{PRODUCT_HEAD} {PINNED_BASE}",
        )

    def test_complete_product_range_remains_reachable_with_provenance(self):
        commits = git(
            "rev-list", f"{PINNED_BASE}..{PRODUCT_HEAD}", text=True
        ).splitlines()
        self.assertEqual(len(commits), 52)
        for commit in commits:
            with self.subTest(commit=commit):
                subprocess.run(
                    ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                    cwd=ROOT,
                    check=True,
                )
                raw = git("cat-file", "commit", commit)
                self.assertIn(b"gpgsig ", raw.split(b"\n\n", 1)[0])
                message = raw.split(b"\n\n", 1)[1].decode("utf-8")
                for trailer in TRAILERS:
                    self.assertEqual(message.splitlines().count(trailer), 1)

    def test_manifest_covers_every_overlap_and_both_retained_behaviours(self):
        manifest = json.loads(COMPOSITION_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"], "fiat-429-composition/v1")
        self.assertEqual(manifest["product_head"], PRODUCT_HEAD)
        self.assertEqual(manifest["pinned_base"], PINNED_BASE)
        self.assertEqual(manifest["parent_order"], [PRODUCT_HEAD, PINNED_BASE])
        entries = manifest["overlaps"]
        self.assertEqual(tuple(item["path"] for item in entries), OVERLAPS)
        self.assertEqual(len(entries), 16)
        self.assertEqual(sum(bool(item["textual_conflict"]) for item in entries), 15)
        for item in entries:
            with self.subTest(path=item["path"]):
                self.assertTrue(item["current_behaviour"].strip())
                self.assertTrue(item["product_behaviour"].strip())
                self.assertTrue(item["resolution"].strip())

    def test_root_audit_retains_the_exact_pinned_base_blob_as_its_prefix(self):
        current = (ROOT / "audit" / "AUDIT.md").read_bytes()
        pinned = git("show", f"{PINNED_BASE}:audit/AUDIT.md")
        self.assertEqual(hashlib.sha256(pinned).hexdigest(), ROOT_AUDIT_SHA256)
        self.assertTrue(current.startswith(pinned))

    def test_product_suffix_is_exact_and_keeps_its_record_distribution(self):
        data = PRODUCT_SUFFIX.read_bytes()
        self.assertEqual(data.count(b"\n"), 574)
        self.assertEqual(hashlib.sha256(data).hexdigest(), PRODUCT_SUFFIX_SHA256)
        headings = re.findall(
            rb"^## audit-record-schema-timestamp-synopsis, step ([123]), round ",
            data,
            flags=re.MULTILINE,
        )
        self.assertEqual(Counter(headings), Counter({b"1": 12, b"2": 15, b"3": 2}))
        self.assertEqual(data.count(b"Audit schema: fiat-audit-round/v1\n"), 29)

    def test_receipted_study_and_runbook_have_exact_committed_copies(self):
        self.assertEqual(sha256(RECOVERY_DOCS / "study.md"), STUDY_SHA256)
        self.assertEqual(sha256(RECOVERY_DOCS / "runbook.md"), RUNBOOK_SHA256)

    def test_release_proof_binds_the_composed_runtime_and_generations(self):
        self.assertTrue(PROOF.is_file(), f"missing release proof: {PROOF}")
        self.assertEqual(sha256(PROOF), PROOF_SHA256)
        recovered_generator = git(
            "show",
            f"{STEP_ONE_PRE_PROSE_HEAD}:"
            "plugins/hexaemeron/skills/fiat/scripts/audit_synopsis.py",
        )
        self.assertEqual(
            hashlib.sha256(recovered_generator).hexdigest(),
            RECOVERY_GENERATOR_SHA256,
        )
        proof = PROOF.read_text(encoding="utf-8")
        for value in (
            PRODUCT_HEAD,
            PINNED_BASE,
            COMPOSITION,
            STUDY_SHA256,
            RUNBOOK_SHA256,
            sha256(COMPOSITION_MANIFEST),
            PRODUCT_CONTROLLER_SHA256,
            RECOVERY_GENERATOR_SHA256,
            f"fiat-v{PRODUCT_FIAT_VERSION}",
            f"Hexaemeron {PRODUCT_HEXAEMERON_VERSION}",
        ):
            with self.subTest(value=value):
                self.assertIn(value, proof)

    def test_release_tree_keeps_product_sources_and_current_unique_synopses(self):
        result = subprocess.run(
            ["python3", str(GENERATOR), "--check", str(ROOT)],
            cwd=ROOT,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        rows = [line for line in result.stdout.splitlines() if line.strip()]
        sources = [row.split(": source_lines=", 1)[0] for row in rows]
        self.assertTrue(set(PRODUCT_AUDIT_SOURCES).issubset(sources))
        self.assertIn(INTEGRATED_UNTAGGED_SOURCE, sources)
        self.assertEqual(len(sources), len(set(sources)))
        destinations = []
        for row in rows:
            source = row.split(": source_lines=", 1)[0]
            if source.endswith("/AUDIT.md"):
                destinations.append(str(Path(source).with_name("AUDIT_SYNOPSIS.md")))
            else:
                destinations.append(str(Path(source).with_suffix(".synopsis.md")))
        self.assertEqual(len(destinations), len(set(destinations)))

    def test_integrated_controller_digest_reaches_every_promise_binding(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        digests = [coverage["run_observation_binding"]["controller"]["sha256"]]
        for promise in (
            "fiat-controller-checkpoint",
            "fiat-design-evidence",
            "fiat-final-integration",
            "fiat-local-retirement",
            "fiat-receipted-delivery",
            "fiat-study-amendment",
            "fiat-runbook-amendment",
            "fiat-run-observation-binding",
            "fiat-version-resolution",
        ):
            digests.append(coverage["runtime"][promise]["sha256"])
        self.assertEqual(sha256(CONTROLLER), INTEGRATED_CONTROLLER_SHA256)
        self.assertEqual(
            digests, [INTEGRATED_CONTROLLER_SHA256] * len(digests)
        )


if PROOF_MODE:
    class Issue429DisposableProofTests(unittest.TestCase):
        """Replay the release boundary with the checked-in runtime only."""

        OUTPUT_BYTES_MAX = 2 * 1024 * 1024

        def setUp(self):
            self.command_count = 0
            self.peak_output_bytes = 0

        def run_bounded(self, argv, *, cwd, expected=0, timeout=180):
            result = subprocess.run(
                [str(item) for item in argv],
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
            )
            output_bytes = len(result.stdout) + len(result.stderr)
            self.command_count += 1
            self.peak_output_bytes = max(self.peak_output_bytes, output_bytes)
            self.assertLessEqual(
                output_bytes,
                self.OUTPUT_BYTES_MAX,
                f"bounded command output exceeded {self.OUTPUT_BYTES_MAX} bytes",
            )
            accepted = (expected,) if isinstance(expected, int) else tuple(expected)
            self.assertIn(
                result.returncode,
                accepted,
                "command returned an unexpected exit\n"
                f"argv={argv!r}\nstdout={result.stdout[-4000:]!r}\n"
                f"stderr={result.stderr[-4000:]!r}",
            )
            return result

        @staticmethod
        def file_digest(path):
            path = Path(path)
            return sha256(path) if path.is_file() else None

        def state_ledger(self, worktree):
            state_dir = Path(worktree) / ".hexaemeron"
            return {
                "state": self.file_digest(state_dir / "state.json"),
                "ledger": self.file_digest(state_dir / "ledger.jsonl"),
            }

        @staticmethod
        def synopsis_snapshot(worktree):
            root = Path(worktree)
            result = {}
            for pattern in ("**/AUDIT_SYNOPSIS.md", "**/*.synopsis.md"):
                for path in root.glob(pattern):
                    if path.is_file():
                        result[path.relative_to(root).as_posix()] = path.read_bytes()
            return result

        def controller(self, worktree, *args, expected=0):
            return self.run_bounded(
                [sys.executable, CONTROLLER, "--dir", worktree, *args],
                cwd=worktree,
                expected=expected,
            )

        def bootstrap_run(self, repo, base, topic):
            self.controller(repo, "init", "--topic", topic, "--base", base)
            breadcrumbs = [
                line.strip()
                for line in (Path(repo) / ".hexaemeron" / "worktree")
                .read_text(encoding="utf-8")
                .splitlines()
                if line.strip()
            ]
            worktree = Path(breadcrumbs[-1])
            fixture_dir = worktree / "proof-fixture"
            fixture_dir.mkdir()
            shutil.copyfile(RECOVERY_DOCS / "study.md", fixture_dir / "study.md")
            shutil.copyfile(RECOVERY_DOCS / "runbook.md", fixture_dir / "runbook.md")
            runbook = (fixture_dir / "runbook.md").read_text(encoding="utf-8")
            titles = re.findall(r"(?m)^## Step \d+: (.+)$", runbook)
            (fixture_dir / "steps.json").write_text(
                json.dumps([{"title": title} for title in titles]) + "\n",
                encoding="utf-8",
            )
            self.controller(
                worktree,
                "done",
                "study",
                "--artifact",
                "proof-fixture/study.md",
                "--skills",
                "hexaemeron:protasis",
            )
            self.controller(
                worktree,
                "done",
                "runbook",
                "--artifact",
                "proof-fixture/runbook.md",
                "--steps-file",
                "proof-fixture/steps.json",
            )
            packet = json.loads(self.controller(worktree, "next").stdout)
            return worktree, packet["branch"]

        @staticmethod
        def audit_record(
            risk_ids,
            *,
            omit=(),
            timestamp="2026-08-25T12:00:00Z",
            schema="fiat-audit-round/v2",
            heading_schema=None,
            covered=None,
            verdict="null",
            rows=None,
            terminal_lf=True,
        ):
            heading_schema = heading_schema or schema
            if heading_schema == "fiat-audit-round/v1":
                heading = f"## issue 429 proof, step 1, round 1 -- {timestamp}"
            else:
                heading = f"## Step 1, round 1 -- {timestamp}"
            covered = covered or "; ".join(
                f"{risk_id}=reviewed" for risk_id in risk_ids
            )
            rows = rows or ["| -- | -- | -- | none | -- |"]
            blocks = {
                "heading": [heading],
                "schema": [f"Audit schema: {schema}"],
                "covered": [f"Covered: {covered}"],
                "not_checked": ["Not checked: none"],
                "verdict": [f"Elenchus verdict: {verdict}"],
                "table": [
                    "| id | severity | file | finding | status |",
                    "| --- | --- | --- | --- | --- |",
                    *rows,
                ],
                "leads": ["Leads not pursued: none"],
            }
            lines = []
            for name in (
                "heading",
                "schema",
                "covered",
                "not_checked",
                "verdict",
                "table",
                "leads",
            ):
                if name not in omit:
                    lines.extend(blocks[name])
                    lines.append("")
            encoded = "\n".join(lines).encode("utf-8")
            return encoded if terminal_lf else encoded.rstrip(b"\n")

        def test_checked_in_controller_and_generator_in_disposable_repository(self):
            started = time.monotonic()
            live_state = {
                name: self.file_digest(ROOT / ".hexaemeron" / name)
                for name in ("state.json", "ledger.jsonl")
            }
            temporary_root = None
            refusal_names = []
            source_rows = []
            release_rows = []
            controller_verified = []
            local_valid = hosted_valid = trailer_valid = reachable = 0

            with tempfile.TemporaryDirectory(prefix="fiat-429-release-proof-") as raw:
                temporary_root = Path(raw)
                repo = temporary_root / "repo"
                self.run_bounded(
                    ["git", "clone", "--shared", "--quiet", ROOT, repo],
                    cwd=ROOT,
                )
                self.run_bounded(
                    ["git", "switch", "-C", "main", COMPOSITION],
                    cwd=repo,
                )
                self.run_bounded(
                    ["git", "config", "user.name", "Disposable proof"], cwd=repo
                )
                self.run_bounded(
                    ["git", "config", "user.email", "proof@example.invalid"],
                    cwd=repo,
                )

                worktree, step_branch = self.bootstrap_run(
                    repo, "main", "issue 429 proof"
                )
                unsigned_message = (
                    "unsigned refusal fixture\n\n"
                    + TRAILERS[0]
                    + "\n"
                    + TRAILERS[1]
                )
                self.run_bounded(
                    ["git", "switch", "--detach", COMPOSITION], cwd=repo
                )
                self.run_bounded(
                    [
                        "git",
                        "-c",
                        "commit.gpgsign=false",
                        "commit",
                        "--allow-empty",
                        "-m",
                        unsigned_message,
                    ],
                    cwd=repo,
                )
                unsigned = self.run_bounded(
                    ["git", "rev-parse", "HEAD"], cwd=repo
                ).stdout.decode().strip()
                self.run_bounded(
                    ["git", "branch", step_branch, unsigned], cwd=repo
                )
                before = self.state_ledger(worktree)
                refused = self.controller(
                    worktree,
                    "done",
                    "implement",
                    "--branch",
                    step_branch,
                    "--commit",
                    unsigned,
                    "--tests",
                    "unsigned refusal fixture",
                    expected=2,
                )
                self.assertIn(b"no valid local signature", refused.stderr)
                self.assertEqual(self.state_ledger(worktree), before)
                refusal_names.append("signature")

                self.run_bounded(
                    ["git", "branch", "-f", step_branch, STEP_ONE_HEAD], cwd=repo
                )
                self.controller(
                    worktree,
                    "done",
                    "implement",
                    "--branch",
                    step_branch,
                    "--commit",
                    STEP_ONE_HEAD,
                    "--tests",
                    "checked-in disposable proof",
                )
                self.controller(
                    worktree,
                    "record",
                    "security_suite",
                    json.dumps("waived: no Solidity target in disposable proof"),
                )

                state_path = worktree / ".hexaemeron" / "state.json"
                state = json.loads(state_path.read_text(encoding="utf-8"))
                log_relative = state["config"]["audit"]["log_path"]
                log_path = worktree / Path(log_relative)
                synopsis_path = log_path.with_suffix(".synopsis.md")
                log_path.parent.mkdir(parents=True, exist_ok=True)
                risk_register = re.search(
                    r"(?ms)^```risk-register\s*$\n(?P<body>.*?)^```\s*$",
                    (worktree / "proof-fixture" / "study.md").read_text(
                        encoding="utf-8"
                    ),
                )
                self.assertIsNotNone(risk_register)
                risk_ids = [
                    line.split("|", 1)[0].strip()
                    for line in risk_register.group("body").splitlines()
                    if line.strip()
                ]

                def clear_candidate():
                    log_path.unlink(missing_ok=True)
                    synopsis_path.unlink(missing_ok=True)

                def audit_args(findings=0, extra=()):
                    return (
                        "audit-round",
                        "--findings",
                        str(findings),
                        "--audit-filter",
                        "sapheneia:sapheneia",
                        "--phylax-exit",
                        "0",
                        "--ephoros-exit",
                        "0",
                        "--hypomnema-exit",
                        "0",
                        *extra,
                    )

                valid_covered = "; ".join(
                    f"{risk_id}=reviewed" for risk_id in risk_ids
                )
                malformed = [
                    ("required-schema", {"omit": {"schema"}}, 0, (), b"Audit schema"),
                    ("required-covered", {"omit": {"covered"}}, 0, (), b"Covered"),
                    (
                        "required-not-checked",
                        {"omit": {"not_checked"}},
                        0,
                        (),
                        b"Not checked",
                    ),
                    ("required-verdict", {"omit": {"verdict"}}, 0, (), b"Elenchus"),
                    ("required-table", {"omit": {"table"}}, 0, (), b"findings table"),
                    (
                        "required-leads",
                        {"omit": {"leads"}},
                        0,
                        (),
                        b"row count",
                    ),
                    (
                        "timestamp-shape",
                        {"timestamp": "2026-08-25"},
                        0,
                        (),
                        b"timestamp",
                    ),
                    (
                        "timestamp-calendar",
                        {"timestamp": "2026-02-30T00:00:00Z"},
                        0,
                        (),
                        b"calendar-valid",
                    ),
                    (
                        "grammar-schema",
                        {"schema": "fiat-audit-round/v3"},
                        0,
                        (),
                        b"Audit schema",
                    ),
                    (
                        "grammar-heading",
                        {"heading_schema": "fiat-audit-round/v1"},
                        0,
                        (),
                        b"heading",
                    ),
                    (
                        "risk-missing",
                        {
                            "covered": "; ".join(
                                f"{risk_id}=reviewed" for risk_id in risk_ids[:-1]
                            )
                        },
                        0,
                        (),
                        b"missing a study risk id",
                    ),
                    (
                        "risk-duplicate",
                        {"covered": valid_covered + f"; {risk_ids[0]}=reviewed"},
                        0,
                        (),
                        b"duplicate risk id",
                    ),
                    (
                        "risk-unknown",
                        {"covered": valid_covered + "; unknown-risk=reviewed"},
                        0,
                        (),
                        b"unknown risk id",
                    ),
                    (
                        "risk-disposition",
                        {"covered": valid_covered.replace("=reviewed", "=accepted", 1)},
                        0,
                        (),
                        b"invalid disposition",
                    ),
                    (
                        "count-zero-row",
                        {
                            "rows": [
                                "| F-01 | low | fixture.py | mismatch | open |"
                            ]
                        },
                        0,
                        (),
                        b"zero-finding row",
                    ),
                    (
                        "count-one-row",
                        {},
                        1,
                        (),
                        b"row count",
                    ),
                    (
                        "verdict",
                        {"verdict": "guarded"},
                        0,
                        (),
                        b"does not match",
                    ),
                    (
                        "grammar-eof",
                        {"terminal_lf": False},
                        0,
                        (),
                        b"end with one LF",
                    ),
                ]
                for name, options, findings, extra, fragment in malformed:
                    clear_candidate()
                    log_path.write_bytes(self.audit_record(risk_ids, **options))
                    before = self.state_ledger(worktree)
                    destinations = self.synopsis_snapshot(worktree)
                    source_before = log_path.read_bytes()
                    result = self.controller(
                        worktree, *audit_args(findings, extra), expected=2
                    )
                    self.assertIn(fragment, result.stderr, name)
                    self.assertEqual(self.state_ledger(worktree), before, name)
                    self.assertEqual(self.synopsis_snapshot(worktree), destinations, name)
                    self.assertEqual(log_path.read_bytes(), source_before, name)
                    refusal_names.append(name)

                clear_candidate()
                log_path.write_bytes(self.audit_record(risk_ids))
                self.run_bounded(
                    [sys.executable, GENERATOR, "--write", worktree], cwd=worktree
                )
                synopsis_path.write_bytes(synopsis_path.read_bytes() + b"stale\n")
                before = self.state_ledger(worktree)
                destinations = self.synopsis_snapshot(worktree)
                stale = self.controller(worktree, *audit_args(), expected=2)
                self.assertIn(b"synopsis is stale", stale.stderr)
                self.assertEqual(self.state_ledger(worktree), before)
                self.assertEqual(self.synopsis_snapshot(worktree), destinations)
                refusal_names.append("stale-synopsis")

                self.run_bounded(
                    [sys.executable, GENERATOR, "--write", worktree], cwd=worktree
                )
                before = self.state_ledger(worktree)
                destinations = self.synopsis_snapshot(worktree)
                wrong_path = self.controller(
                    worktree,
                    *audit_args(extra=("--log", "audit/rounds/other.md")),
                    expected=2,
                )
                self.assertIn(b"config audit.log_path", wrong_path.stderr)
                self.assertEqual(self.state_ledger(worktree), before)
                self.assertEqual(self.synopsis_snapshot(worktree), destinations)
                refusal_names.append("path")

                clear_candidate()
                symlink_target = worktree / "proof-fixture" / "symlink-target.md"
                symlink_target.write_bytes(self.audit_record(risk_ids))
                log_path.symlink_to(symlink_target)
                before = self.state_ledger(worktree)
                destinations = self.synopsis_snapshot(worktree)
                symlink = self.controller(worktree, *audit_args(), expected=2)
                self.assertIn(b"symlink", symlink.stderr)
                self.assertEqual(self.state_ledger(worktree), before)
                self.assertEqual(self.synopsis_snapshot(worktree), destinations)
                refusal_names.append("symlink-path")
                clear_candidate()

                log_path.write_bytes(self.audit_record(risk_ids))
                written = self.run_bounded(
                    [sys.executable, GENERATOR, "--write", worktree], cwd=worktree
                )
                self.controller(worktree, *audit_args())
                checked = self.run_bounded(
                    [sys.executable, GENERATOR, "--check", worktree], cwd=worktree
                )
                written_rows = [
                    line for line in written.stdout.decode().splitlines() if line.strip()
                ]
                checked_rows = [
                    line for line in checked.stdout.decode().splitlines() if line.strip()
                ]
                self.assertEqual(len(written_rows), 10)
                self.assertEqual(
                    [re.sub(r" committed=(?:written|match)$", "", row) for row in checked_rows],
                    [re.sub(r" committed=(?:written|match)$", "", row) for row in written_rows],
                )
                state = json.loads(state_path.read_text(encoding="utf-8"))
                controller_verified = state["steps"][0]["receipts"]["implement"][
                    "verified_commits"
                ]
                self.assertEqual(
                    controller_verified, [STEP_ONE_PRE_PROSE_HEAD, STEP_ONE_HEAD]
                )
                round_entry = state["steps"][0]["audit"]["rounds"][-1]
                self.assertEqual(round_entry["schema"], "fiat-audit-round/v2")
                self.assertEqual(round_entry["record_timestamp"], "2026-08-25T12:00:00Z")

                destinations = []
                for diagnostic in written_rows:
                    source = diagnostic.split(": source_lines=", 1)[0]
                    source_path = worktree / Path(source)
                    output = (
                        source_path.with_name("AUDIT_SYNOPSIS.md")
                        if source.endswith("/AUDIT.md")
                        else source_path.with_suffix(".synopsis.md")
                    )
                    destinations.append(output.relative_to(worktree).as_posix())
                    source_bytes = source_path.read_bytes()
                    output_bytes = output.read_bytes()
                    verdict_values = [
                        line.split(":", 1)[1].strip()
                        for line in source_bytes.decode("utf-8").splitlines()
                        if line.startswith("Elenchus verdict:")
                    ]
                    source_rows.append(
                        {
                            "source": source,
                            "output": output.relative_to(worktree).as_posix(),
                            "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
                            "output_sha256": hashlib.sha256(output_bytes).hexdigest(),
                            "source_lines": source_bytes.count(b"\n"),
                            "output_lines": output_bytes.count(b"\n"),
                            "v1": source_bytes.count(b"Audit schema: fiat-audit-round/v1\n"),
                            "v2": source_bytes.count(b"Audit schema: fiat-audit-round/v2\n"),
                            "verdicts": source_bytes.count(b"Elenchus verdict:"),
                            "terminal_verdict": (
                                verdict_values[-1] if verdict_values else None
                            ),
                            "leads": source_bytes.count(b"Leads not pursued:"),
                        }
                    )
                self.assertEqual(len(destinations), len(set(destinations)))
                self.assertEqual(sum(row["v1"] for row in source_rows), 29)
                self.assertEqual(sum(row["v2"] for row in source_rows), 1)
                self.assertTrue(
                    all(
                        100 * row["output_lines"] < 15 * row["source_lines"]
                        for row in source_rows
                    )
                )

                release_check = self.run_bounded(
                    [sys.executable, GENERATOR, "--check", ROOT], cwd=ROOT
                )
                release_diagnostics = [
                    line
                    for line in release_check.stdout.decode().splitlines()
                    if line.strip()
                ]
                release_sources = {
                    row.split(": source_lines=", 1)[0] for row in release_diagnostics
                }
                self.assertTrue(set(PRODUCT_AUDIT_SOURCES).issubset(release_sources))
                self.assertIn(INTEGRATED_UNTAGGED_SOURCE, release_sources)
                for diagnostic in release_diagnostics:
                    source = diagnostic.split(": source_lines=", 1)[0]
                    source_path = ROOT / Path(source)
                    output = (
                        source_path.with_name("AUDIT_SYNOPSIS.md")
                        if source.endswith("/AUDIT.md")
                        else source_path.with_suffix(".synopsis.md")
                    )
                    source_bytes = source_path.read_bytes()
                    output_bytes = output.read_bytes()
                    verdict_values = [
                        line.split(":", 1)[1].strip()
                        for line in source_bytes.decode("utf-8").splitlines()
                        if line.startswith("Elenchus verdict:")
                    ]
                    release_rows.append(
                        {
                            "source": source,
                            "output": output.relative_to(ROOT).as_posix(),
                            "source_sha256": sha256(source_path),
                            "output_sha256": sha256(output),
                            "source_lines": source_bytes.count(b"\n"),
                            "output_lines": output_bytes.count(b"\n"),
                            "v1": source_bytes.count(b"Audit schema: fiat-audit-round/v1\n"),
                            "v2": source_bytes.count(b"Audit schema: fiat-audit-round/v2\n"),
                            "verdicts": source_bytes.count(b"Elenchus verdict:"),
                            "terminal_verdict": (
                                verdict_values[-1] if verdict_values else None
                            ),
                            "leads": source_bytes.count(b"Leads not pursued:"),
                        }
                    )
                release_by_source = {
                    row["source"]: row for row in release_rows
                }
                product_source = PRODUCT_SUFFIX.relative_to(ROOT).as_posix()
                self.assertEqual(
                    (
                        release_by_source[product_source]["v1"],
                        release_by_source[product_source]["v2"],
                    ),
                    (29, 0),
                )
                recovery_row = release_by_source[RECOVERY_LOG_SOURCE]
                self.assertEqual(recovery_row["v1"], 0)
                self.assertGreaterEqual(recovery_row["v2"], 2)
                integrated_row = release_by_source[INTEGRATED_UNTAGGED_SOURCE]
                self.assertEqual((integrated_row["v1"], integrated_row["v2"]), (0, 0))
                for source, row in release_by_source.items():
                    if source != product_source:
                        self.assertEqual(row["v1"], 0)

                specification = importlib.util.spec_from_file_location(
                    "issue_429_checked_generator", GENERATOR
                )
                renderer = importlib.util.module_from_spec(specification)
                specification.loader.exec_module(renderer)
                collision_root = temporary_root / "collision"
                round_dir = collision_root / "audit" / "rounds"
                round_dir.mkdir(parents=True)
                legacy = b"## legacy\nLeads not pursued: none\n" + b"x\n" * 30
                (round_dir / "one.md").write_bytes(legacy)
                (round_dir / "two.md").write_bytes(legacy)
                collision_before = self.synopsis_snapshot(collision_root)
                with mock.patch.object(
                    renderer,
                    "_output_path",
                    return_value="audit/rounds/collision.synopsis.md",
                ):
                    with self.assertRaisesRegex(
                        renderer.SynopsisError, "duplicate synopsis outputs"
                    ):
                        renderer.process_repository(collision_root, write=True)
                self.assertEqual(
                    self.synopsis_snapshot(collision_root), collision_before
                )
                refusal_names.append("collision")
                with self.assertRaises(renderer.SynopsisError):
                    renderer._relative_path("../escape.md")
                refusal_names.append("path-escape")

                parents = self.run_bounded(
                    ["git", "show", "-s", "--format=%P", COMPOSITION], cwd=ROOT
                ).stdout.decode().strip().split()
                self.assertEqual(parents, [PRODUCT_HEAD, PINNED_BASE])

                def require_composition_parent_order(observed):
                    if observed != [PRODUCT_HEAD, PINNED_BASE]:
                        raise ValueError("composition parent order changed")

                with self.assertRaisesRegex(ValueError, "parent order"):
                    require_composition_parent_order(list(reversed(parents)))
                refusal_names.append("parent-order")

                self.run_bounded(
                    ["git", "branch", "trailer-base", TRAILER_FIXTURE_PARENT],
                    cwd=repo,
                )
                trailer_worktree, trailer_branch = self.bootstrap_run(
                    repo, "trailer-base", "issue 429 trailer proof"
                )
                self.run_bounded(
                    ["git", "branch", trailer_branch, TRAILER_FIXTURE], cwd=repo
                )
                before = self.state_ledger(trailer_worktree)
                trailer_refusal = self.controller(
                    trailer_worktree,
                    "done",
                    "implement",
                    "--branch",
                    trailer_branch,
                    "--commit",
                    TRAILER_FIXTURE,
                    "--tests",
                    "trailer refusal fixture",
                    expected=2,
                )
                self.assertIn(b"Shoggoth co-author trailers", trailer_refusal.stderr)
                self.assertEqual(self.state_ledger(trailer_worktree), before)
                refusal_names.append("trailer")

                commits = self.run_bounded(
                    ["git", "rev-list", f"{PINNED_BASE}..{PRODUCT_HEAD}"], cwd=ROOT
                ).stdout.decode().splitlines()
                self.assertEqual(len(commits), 52)
                for commit in commits:
                    self.run_bounded(["git", "verify-commit", commit], cwd=ROOT)
                    local_valid += 1
                    message = self.run_bounded(
                        ["git", "show", "-s", "--format=%B", commit], cwd=ROOT
                    ).stdout.decode()
                    if all(message.splitlines().count(trailer) == 1 for trailer in TRAILERS):
                        trailer_valid += 1
                    if self.run_bounded(
                        ["git", "merge-base", "--is-ancestor", commit, "HEAD"],
                        cwd=ROOT,
                    ).returncode == 0:
                        reachable += 1
                self.assertEqual((local_valid, trailer_valid, reachable), (52, 52, 52))

                hosted = self.run_bounded(
                    [
                        "gh",
                        "api",
                        "--method",
                        "GET",
                        "repos/wildcat-finance/skills/commits",
                        "-f",
                        f"sha={PRODUCT_HEAD}",
                        "-f",
                        "per_page=100",
                    ],
                    cwd=ROOT,
                    timeout=60,
                )
                hosted_commits = [
                    item for item in json.loads(hosted.stdout) if item["sha"] in commits
                ]
                self.assertEqual({item["sha"] for item in hosted_commits}, set(commits))
                for item in hosted_commits:
                    verification = item["commit"]["verification"]
                    self.assertTrue(verification["verified"])
                    self.assertEqual(verification["reason"], "valid")
                    hosted_valid += 1
                self.assertEqual(hosted_valid, 52)

                predecessor_ledger = self.run_bounded(
                    [
                        "git",
                        "show",
                        f"{STEP_ONE_HEAD}:plugins/hexaemeron/skills/fiat/EVOLUTION.md",
                    ],
                    cwd=ROOT,
                ).stdout.decode()
                predecessor_fiat = re.search(
                    r"(?m)^- Current version: `fiat-v([^`]+)`$", predecessor_ledger
                ).group(1)
                predecessor_versions = []
                for relative in (
                    "plugins/hexaemeron/.claude-plugin/plugin.json",
                    "plugins/hexaemeron/.codex-plugin/plugin.json",
                    ".agents/plugins/marketplace.json",
                    ".claude-plugin/marketplace.json",
                ):
                    data = json.loads(
                        self.run_bounded(
                            ["git", "show", f"{STEP_ONE_HEAD}:{relative}"], cwd=ROOT
                        ).stdout
                    )
                    if relative.endswith("plugin.json"):
                        predecessor_versions.append(data["version"])
                    else:
                        predecessor_versions.append(
                            next(
                                item["version"]
                                for item in data["plugins"]
                                if item["name"] == "hexaemeron"
                            )
                        )

                def allocate_successors(fiat_predecessor, package_predecessors):
                    if fiat_predecessor != "5.24.1":
                        raise ValueError("Fiat release predecessor changed")
                    if package_predecessors != ["1.6.0"] * 4:
                        raise ValueError("Hexaemeron release predecessor changed")
                    return PRODUCT_FIAT_VERSION, PRODUCT_HEXAEMERON_VERSION

                self.assertEqual(
                    allocate_successors(predecessor_fiat, predecessor_versions),
                    (PRODUCT_FIAT_VERSION, PRODUCT_HEXAEMERON_VERSION),
                )
                with self.assertRaisesRegex(ValueError, "predecessor changed"):
                    allocate_successors(predecessor_fiat, ["1.6.0"] * 3 + ["1.6.1"])
                refusal_names.append("predecessor")

                skill = (ROOT / "plugins/hexaemeron/skills/fiat/SKILL.md").read_text(
                    encoding="utf-8"
                )
                ledger = (ROOT / "plugins/hexaemeron/skills/fiat/EVOLUTION.md").read_text(
                    encoding="utf-8"
                )
                self.assertIn(f'version: "{INTEGRATED_FIAT_VERSION}"', skill)
                self.assertIn(
                    f"Current version: `fiat-v{INTEGRATED_FIAT_VERSION}`", ledger
                )

            self.assertFalse(temporary_root.exists())
            self.assertEqual(
                {
                    name: self.file_digest(ROOT / ".hexaemeron" / name)
                    for name in ("state.json", "ledger.jsonl")
                },
                live_state,
            )
            summary = {
                "schema": "fiat-429-release-proof/v1",
                "controller_sha256": sha256(CONTROLLER),
                "generator_sha256": sha256(GENERATOR),
                "controller_verified_commits": controller_verified,
                "composition": COMPOSITION,
                "parents": [PRODUCT_HEAD, PINNED_BASE],
                "disposable_sources": source_rows,
                "disposable_source_count": len(source_rows),
                "release_sources": release_rows,
                "release_source_count": len(release_rows),
                "refusals": refusal_names,
                "refusal_count": len(refusal_names),
                "local_valid": local_valid,
                "hosted_valid": hosted_valid,
                "trailer_valid": trailer_valid,
                "reachable": reachable,
                "commands": self.command_count,
                "peak_output_bytes": self.peak_output_bytes,
                "elapsed_seconds": round(time.monotonic() - started, 3),
                "product_fiat": PRODUCT_FIAT_VERSION,
                "product_hexaemeron": PRODUCT_HEXAEMERON_VERSION,
                "integrated_fiat": INTEGRATED_FIAT_VERSION,
                "integrated_hexaemeron": INTEGRATED_HEXAEMERON_VERSION,
                "cleanup": "complete",
            }
            print("\n" + json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    if PROOF_MODE:
        sys.argv.remove("--proof")
    unittest.main()
