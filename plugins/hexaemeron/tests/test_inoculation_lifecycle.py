"""Lifecycle checks for source-bound inoculation before implementation."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

try:
    from .test_hexctl import HexctlCase, hexctl_module
except ImportError:
    from test_hexctl import HexctlCase, hexctl_module


class InoculationLifecycleTests(HexctlCase):
    NO_KNOWN_FIXTURE = (
        Path(__file__).parent / "fixtures/issue-453/no-known-findings.json"
    )
    PATH_BOUNDARY_FIXTURE = (
        Path(__file__).parent / "fixtures/issue-453/path-boundary.json"
    )

    def controller_bytes(self):
        controller_root = Path(self.target, ".hexaemeron")
        checkpoint_root = controller_root / "checkpoints"
        checkpoint_files = tuple(
            (path.relative_to(controller_root).as_posix(), path.read_bytes())
            for path in sorted(checkpoint_root.rglob("*"))
            if path.is_file()
        ) if checkpoint_root.exists() else ()
        return (
            (controller_root / "state.json").read_bytes(),
            (controller_root / "ledger.jsonl").read_bytes(),
            checkpoint_files,
        )

    def guard_authority_bytes(self):
        root = Path(self.target)
        controller_root = root / ".hexaemeron"
        controller_files = tuple(
            (path.relative_to(controller_root).as_posix(), path.read_bytes())
            for path in sorted(controller_root.rglob("*"))
            if path.is_file()
        )
        branch_tip = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.target,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        return controller_files, branch_tip

    def prepare_legacy_run(self):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Legacy\n\n**Goal.** Continue.\n",
        )
        steps = self.write("steps.json", '["Legacy"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

    def prepare_amendable_legacy_run(self):
        self.init()
        study_text = (
            Path(__file__).parent / "fixtures/protasis/complete-study.md"
        ).read_text(encoding="utf-8")
        study = self.write("study.md", study_text)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Legacy\n\n"
            "**Goal.** Continue the pre-capture run.\n"
            "**Entry.** The study is receipted.\n"
            "**Exit.** Run `python3 -m unittest`.\n"
            "**Files.** `controller.py`.\n"
            "**Tests.** Run `python3 -m unittest`.\n"
            "**Disciplines.** none, fixture only.\n",
        )
        steps = self.write("steps.json", '["Legacy"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

    def rewrite_last_controller_state(self, state, *, mutate_event=None):
        controller_root = Path(self.target, ".hexaemeron")
        state_path = controller_root / "state.json"
        ledger_path = controller_root / "ledger.jsonl"
        state_path.write_text(
            json.dumps(state, indent=2) + "\n",
            encoding="utf-8",
        )
        entries = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        if mutate_event is not None:
            mutate_event(entries[-1]["data"])
        entries[-1]["state"] = hexctl_module().state_fingerprint(state)
        entries[-1]["hash"] = hashlib.sha256(
            hexctl_module().canonical(
                {
                    key: entries[-1][key]
                    for key in ("ts", "event", "data", "prev", "state")
                }
            ).encode()
        ).hexdigest()
        ledger_path.write_text(
            "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
            encoding="utf-8",
        )

    def test_loader_bridge_refuses_an_outside_leaf_symlink(self):
        controller = hexctl_module()
        plugin = Path(self.target, "fake-plugin")
        source = plugin / "skills/protasis/scripts/known_failure_inventory.py"
        source.parent.mkdir(parents=True)
        outside = Path(self.target, "outside-loader.py")
        outside.write_text(
            "def load_checked_inventory(*args, **kwargs):\n    return None\n",
            encoding="utf-8",
        )
        source.symlink_to(outside)
        controller._KNOWN_FAILURE_INVENTORY_MODULE = None
        self.addCleanup(
            setattr, controller, "_KNOWN_FAILURE_INVENTORY_MODULE", None
        )

        with mock.patch.object(controller, "plugin_root", return_value=str(plugin)):
            with redirect_stderr(io.StringIO()) as errors:
                with self.assertRaises(SystemExit) as refused:
                    controller._known_failure_inventory_module()

        self.assertEqual(2, refused.exception.code)
        self.assertIn("not one stable bounded regular file", errors.getvalue())

    def prepare_capture(self, *, assigned=False, assigned_step=1, amendable=False):
        self.init()
        source_path = "audit/rounds/source.md"
        source = "fixture audit source\n"
        source_sha256 = hashlib.sha256(source.encode()).hexdigest()
        view_path = "audit/rounds/source.synopsis.md"
        view = (
            "Synopsis schema=fiat-audit-synopsis/v1 | "
            f"source={source_path} | source_sha256={source_sha256} | h2_count=0\n"
        )
        view_sha256 = hashlib.sha256(view.encode()).hexdigest()
        self.write(source_path, source)
        self.write(view_path, view)

        checked_views = [
            {
                "id": "fixture-audit",
                "source_sha256": source_sha256,
                "view_sha256": view_sha256,
            }
        ]
        source_views = [
            {
                "id": "fixture-audit",
                "path": view_path,
                "source_sha256": source_sha256,
                "view_sha256": view_sha256,
            }
        ]
        findings = []
        no_known_findings = {
            "source_views": checked_views,
            "consuming_step": 1,
            "surveyor_assertion": "no-known-findings",
        }
        assignment = ""
        if assigned:
            findings = [
                {
                    "id": "kf-453-02",
                    "source_ref": "fixture-audit:1",
                    "failure": "implementation opens before inoculation",
                    "guard_paths": [
                        "plugins/hexaemeron/tests/test_inoculation_lifecycle.py",
                        "plugins/hexaemeron/tests/emit_issue_453_guard_report.py",
                    ],
                    "test_command": (
                        "python3 plugins/hexaemeron/tests/"
                        "emit_issue_453_guard_report.py --case kf-453-02 "
                        "--report {report}"
                    ),
                    "report_format": "unittest-json-v1",
                    "report_file": ".elenchus/issue-453-kf-453-02.json",
                    "expected_guard_verdict": "guarded",
                    "green_command": (
                        "python3 plugins/hexaemeron/tests/"
                        "emit_issue_453_guard_report.py --case kf-453-02 "
                        "--report .elenchus/issue-453-kf-453-02-green.json"
                    ),
                    "consuming_step": assigned_step,
                }
            ]
            no_known_findings = None
            assignment = (
                f"\nKnown-failure assignment: `kf-453-02` -> Step "
                f"{assigned_step}\n"
            )
        inventory = {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": source_views,
            "findings": findings,
            "no_known_findings": no_known_findings,
        }
        study_prefix = "# Study\n"
        if amendable:
            study_prefix = (
                Path(__file__).parent / "fixtures/protasis/complete-study.md"
            ).read_text(encoding="utf-8").rstrip()
        study = self.write(
            "study.md",
            study_prefix
            + "\n\n```known-failure-inventory\n"
            + json.dumps(inventory, indent=2)
            + "\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        runbook_text = "# Runbook\n\n## Step 1: Guarded step\n\n"
        if amendable:
            runbook_text += (
                "**Goal.** Exercise the pre-implementation transition.\n"
                "**Entry.** The capture is receipted.\n"
                "**Exit.** Run `python3 -m unittest`.\n"
                "**Files.** `controller.py`.\n"
                "**Tests.** Run `python3 -m unittest`.\n"
                "**Disciplines.** none, fixture only.\n"
            )
        else:
            runbook_text += (
                "**Goal.** Exercise the pre-implementation transition.\n\n"
                "**Exit.** The source-bound transition is checked.\n"
            )
        titles = ["Guarded step"]
        if assigned and assigned_step == 2:
            runbook_text += (
                "\n## Step 2: Assigned later\n\n"
                "**Goal.** Preserve the later assignment.\n\n"
                "**Exit.** The declaration remains closed.\n"
            )
            titles.append("Assigned later")
        runbook = self.write("runbook.md", runbook_text + assignment)
        steps = self.write("steps.json", json.dumps(titles))
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        return self.next_json(), source_path

    def write_no_known_findings(self, *, mutate=None):
        state = self.state()
        capture = state["receipts"]["runbook"]["known_failure_inventory"]
        record = json.loads(self.NO_KNOWN_FIXTURE.read_text(encoding="utf-8"))
        checked_views = [
            {
                "id": source_view["id"],
                "source_sha256": source_view["source_sha256"],
                "view_sha256": source_view["view_sha256"],
            }
            for source_view in capture["source_views"]
        ]
        record.update(
            {
                "study_sha256": capture["study_sha256"],
                "inventory_sha256": capture["inventory_sha256"],
                "source_views": checked_views,
                "consuming_step": state["current_step"],
            }
        )
        if mutate is not None:
            mutate(record)
        relative = (
            f".hexaemeron/steps/{state['current_step']}/inoculation/"
            "no-known-findings.json"
        )
        self.write(relative, json.dumps(record, indent=2, sort_keys=True) + "\n")
        return record

    def prepare_guard_retention(self, *, inherited_audit=False):
        """Build one real disposable guard commit around capture-aware state."""
        self.prepare_capture(assigned=True)
        self.git(
            "add",
            "--",
            "study.md",
            "runbook.md",
            "steps.json",
            "audit/rounds/source.md",
            "audit/rounds/source.synopsis.md",
        )
        self.git("commit", "-q", "-m", "fixture guard parent")
        parent = self.git("rev-parse", "HEAD").stdout.strip()
        state = self.state()
        state["steps"][0]["inoculation_parent"] = parent
        audit_paths = None
        if inherited_audit:
            log_path = state["config"]["audit"]["log_path"]
            synopsis_path = str(Path(log_path).with_suffix("")) + ".synopsis.md"
            log_bytes = (
                "## Step 1, round 1 -- 2026-09-06T00:00:00Z\n\n"
                "Audit schema: fiat-audit-round/v2\n\n"
                "Covered: fixture=reviewed\n\n"
                "Not checked: none\n\n"
                "Elenchus verdict: guarded\n\n"
                "| id | severity | file | finding | status |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| -- | -- | -- | none | -- |\n\n"
                "Leads not pursued: none\n"
            ).encode("utf-8")
            try:
                from .test_hexctl import audit_synopsis_module
            except ImportError:
                from test_hexctl import audit_synopsis_module
            rendered = audit_synopsis_module().render_source(log_path, log_bytes)
            Path(self.target, log_path).parent.mkdir(parents=True, exist_ok=True)
            Path(self.target, log_path).write_bytes(log_bytes)
            Path(self.target, synopsis_path).write_bytes(rendered["bytes"])
            state["steps"][0]["audit"]["rounds"] = [
                {
                    "log": log_path,
                    "log_end_offset": len(log_bytes),
                    "synopsis_sha256": rendered["synopsis_sha256"],
                }
            ]
            audit_paths = (log_path, synopsis_path)
        self.rewrite_last_controller_state(state)
        branch = self.step_branch(1, state)
        self.git("checkout", "-q", "-b", branch)
        reporter = Path(
            self.target,
            "plugins/hexaemeron/tests/emit_issue_453_guard_report.py",
        )
        reporter.parent.mkdir(parents=True, exist_ok=True)
        reporter.write_text(
            "import json, sys\n"
            "payload = {\"schema\": \"elenchus.unittest.v1\", "
            "\"complete\": True, \"testsRun\": 1, \"failures\": 1, "
            "\"errors\": 0, \"skipped\": 0, \"expectedFailures\": 0, "
            "\"unexpectedSuccesses\": 0}\n"
            "open(sys.argv[-1], \"w\").write(json.dumps(payload) + \"\\n\")\n"
            "raise SystemExit(1)\n",
            encoding="utf-8",
        )
        guard_test = Path(
            self.target,
            "plugins/hexaemeron/tests/test_inoculation_lifecycle.py",
        )
        guard_test.write_text(
            "def test_guard():\n    assert False\n", encoding="utf-8"
        )
        self.git(
            "add",
            "--",
            reporter.relative_to(self.target).as_posix(),
            guard_test.relative_to(self.target).as_posix(),
        )
        self.git("commit", "-q", "-m", "fixture red guard")
        guard_commit = self.git("rev-parse", "HEAD").stdout.strip()
        return hexctl_module(), state, guard_commit, audit_paths

    def prepare_no_known_boundary(
        self,
        *,
        assigned=False,
        assigned_step=1,
        amendable=False,
        tracked_product=False,
        tracked_executable=False,
        tracked_gitlink=False,
    ):
        """Put a zero-assigned Step on its exact clean pre-edit branch."""
        _directive, source_path = self.prepare_capture(
            assigned=assigned,
            assigned_step=assigned_step,
            amendable=amendable,
        )
        paths = [
            "study.md",
            "runbook.md",
            "steps.json",
            "audit/rounds/source.md",
            "audit/rounds/source.synopsis.md",
        ]
        if tracked_product:
            self.write("product.py", "VALUE = 'baseline'\n")
            paths.append("product.py")
        if tracked_executable:
            tool = Path(self.target, "tool.sh")
            self.write("tool.sh", "#!/bin/sh\nexit 0\n")
            tool.chmod(0o755)
            paths.append("tool.sh")
        self.git("add", "--", *paths)
        if tracked_gitlink:
            self.git(
                "update-index",
                "--add",
                "--cacheinfo",
                "160000," + "1" * 40 + ",vendor/absent-submodule",
            )
        self.git("commit", "-q", "-m", "fixture no-known parent")
        parent = self.git("rev-parse", "HEAD").stdout.strip()
        state = self.state()
        state["steps"][0]["inoculation_parent"] = parent
        self.rewrite_last_controller_state(state)
        self.fake_refs[state["run_branch"]] = parent
        self.git("checkout", "-q", "-b", self.step_branch(1, state))
        if tracked_gitlink:
            Path(self.target, "vendor/absent-submodule").mkdir(parents=True)
        return self.next_json(), source_path

    def retain_guard(self, controller, guard_commit):
        output = io.StringIO()
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stdout(output),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        return json.loads(output.getvalue())

    def current_guard_status(self, controller, guard_commit):
        state = controller.load_state(self.target)
        capture = controller.receipted_known_failure_inventory(
            self.target, state
        )
        with mock.patch.object(
            controller, "verify_local_commit", return_value=guard_commit
        ):
            return controller.inoculation_status(state, capture, self.target)

    def guard_controller_tree(self):
        root = Path(self.target, ".hexaemeron")
        return {
            path.relative_to(root).as_posix(): (
                path.read_bytes(),
                path.stat().st_mode & 0o777,
            )
            for path in sorted(root.rglob("*"))
            if path.is_file()
        }

    def restore_guard_controller_tree(self, snapshot):
        root = Path(self.target, ".hexaemeron")
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file() and path.relative_to(root).as_posix() not in snapshot:
                path.unlink()
        for relative, (payload, mode) in snapshot.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            path.chmod(mode)

    def test_kf_453_02_inoculation_precedes_implementation(self):
        directive, _ = self.prepare_capture()

        self.assertEqual("inoculate", directive["do"])
        before = self.controller_bytes()
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(1),
            "--commit",
            "guard-head",
            expect=2,
        )
        self.assertEqual(before, self.controller_bytes())

    def test_kf_453_05_undeclared_product_path_refuses(self):
        fixture = json.loads(
            self.PATH_BOUNDARY_FIXTURE.read_text(encoding="utf-8")
        )
        self.assertEqual(6, len(fixture["allowed_paths"]))
        self.init()
        self.write(".hexaemeron/checkpoints/step-3/probe", "checkpoint bytes\n")
        self.write(
            ".hexaemeron/steps/3/inoculation/reports/existing.report",
            "existing report bytes\n",
        )
        self.write(
            ".hexaemeron/steps/3/inoculation/manifests/existing.json",
            '{"existing":true}\n',
        )
        before = self.guard_authority_bytes()
        controller = hexctl_module()

        accepted = controller._validate_guard_delta_rows(
            fixture["valid_rows"], fixture["allowed_paths"]
        )
        self.assertEqual(fixture["valid_rows"], accepted)
        with self.assertRaisesRegex(ValueError, "undeclared guard path"):
            controller._validate_guard_delta_rows(
                fixture["valid_rows"] + [fixture["invalid_extra"]],
                fixture["allowed_paths"],
            )
        self.assertEqual(before, self.guard_authority_bytes())

    def test_guard_worktree_identity_requires_three_physical_directories(self):
        self.prepare_capture(assigned=True)
        controller = hexctl_module()
        state = self.state()
        physical = Path(self.target)
        alias = Path(self.dir, "worktree-alias")
        alias.symlink_to(physical, target_is_directory=True)
        regular = Path(self.dir, "not-a-worktree")
        regular.write_text("not a directory\n", encoding="utf-8")

        cases = []
        for configured in (alias, regular):
            altered = json.loads(json.dumps(state))
            altered["config"]["git"]["worktree"] = str(configured)
            cases.append(
                (
                    f"configured-{configured.name}",
                    str(physical),
                    altered,
                    None,
                )
            )
        cases.extend(
            [
                (
                    "reported-symlink",
                    str(physical),
                    state,
                    (str(alias) + "\n").encode("utf-8"),
                ),
                ("supplied-symlink", str(alias), state, None),
            ]
        )

        for name, supplied, candidate_state, reported in cases:
            with self.subTest(name=name):
                patcher = (
                    mock.patch.object(
                        controller, "_guard_native_git", return_value=reported
                    )
                    if reported is not None
                    else mock.patch.object(
                        controller,
                        "_guard_native_git",
                        wraps=controller._guard_native_git,
                    )
                )
                with (
                    patcher,
                    redirect_stderr(io.StringIO()),
                    self.assertRaises(SystemExit) as refused,
                ):
                    controller._guard_worktree_identity(
                        supplied, candidate_state
                    )
                self.assertEqual(2, refused.exception.code)

    def test_assigned_guard_native_reads_ignore_a_hostile_caller_path(self):
        controller, state, _unsigned_guard, _audit_paths = (
            self.prepare_guard_retention()
        )
        system_git = controller.shutil.which("git", path=controller.os.defpath)
        keygen = controller.shutil.which("ssh-keygen", path=controller.os.defpath)
        if system_git is None or keygen is None:
            self.skipTest("system Git and ssh-keygen are required")
        signer = Path(self.tmp.name, "guard-signing-key")
        subprocess.run(
            [keygen, "-q", "-t", "ed25519", "-N", "", "-f", str(signer)],
            check=True,
            capture_output=True,
        )
        allowed_signers = Path(self.tmp.name, "allowed-signers")
        public_key = signer.with_suffix(".pub").read_text(encoding="utf-8")
        allowed_signers.write_text(
            "fixture@example.invalid " + public_key,
            encoding="utf-8",
        )
        self.git("config", "gpg.format", "ssh")
        self.git("config", "user.signingkey", str(signer))
        self.git("config", "gpg.ssh.allowedSignersFile", str(allowed_signers))
        subprocess.run(
            [
                system_git,
                "-c",
                "commit.gpgsign=true",
                "commit",
                "--amend",
                "-q",
                "-m",
                (
                    "fixture signed red guard\n\n"
                    "Co-authored-by: Shoggoth <shoggoth@wildcat.finance>\n"
                    "Wildcat-Origin: shoggoth"
                ),
            ],
            cwd=self.target,
            check=True,
            capture_output=True,
        )
        guard_commit = self.git("rev-parse", "HEAD").stdout.strip()
        capture = controller.receipted_known_failure_inventory(
            self.target, state
        )
        hostile_bin = Path(self.tmp.name, "hostile-path")
        hostile_bin.mkdir()
        sentinel = Path(self.tmp.name, "hostile-git-ran")
        hostile_git = hostile_bin / "git"
        hostile_git.write_text(
            "#!/bin/sh\n"
            ": > \"${HOSTILE_GIT_SENTINEL:?}\"\n"
            "exit 97\n",
            encoding="utf-8",
        )
        hostile_git.chmod(0o700)

        with mock.patch.dict(
            controller.os.environ,
            {
                "PATH": str(hostile_bin),
                "HOSTILE_GIT_SENTINEL": str(sentinel),
            },
        ):
            writer_evidence = controller._guard_commit_evidence(
                self.target,
                state,
                capture,
                state["steps"][0],
                guard_commit,
                writer=True,
            )
            reader_evidence = controller._guard_commit_evidence(
                self.target,
                state,
                capture,
                state["steps"][0],
                guard_commit,
                writer=False,
            )

        self.assertEqual(guard_commit, writer_evidence["guard_commit"])
        self.assertEqual(writer_evidence, reader_evidence)
        self.assertFalse(sentinel.exists())

    def test_guard_status_cannot_hide_dirty_moved_or_untracked_submodules(self):
        controller = hexctl_module()
        system_git = controller.shutil.which("git", path=controller.os.defpath)
        self.assertIsNotNone(system_git)

        def run_git(repository, *argv):
            return subprocess.run(
                [system_git, "-c", "commit.gpgsign=false", *argv],
                cwd=repository,
                check=True,
                capture_output=True,
                text=True,
            )

        for case in ("dirty", "moved-head", "untracked"):
            with self.subTest(case=case):
                child = Path(self.tmp.name, f"status-child-{case}")
                superproject = Path(
                    self.tmp.name, f"status-superproject-{case}"
                )
                child.mkdir()
                superproject.mkdir()
                for repository in (child, superproject):
                    run_git(repository, "init", "-q", "-b", "main")
                    run_git(repository, "config", "user.name", "Fixture")
                    run_git(
                        repository,
                        "config",
                        "user.email",
                        "fixture@example.invalid",
                    )
                (child / "tracked.txt").write_text("clean\n", encoding="utf-8")
                run_git(child, "add", "--", "tracked.txt")
                run_git(child, "commit", "-q", "-m", "fixture submodule")
                run_git(
                    superproject,
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    "-q",
                    str(child),
                    "vendor/tracked",
                )
                run_git(
                    superproject,
                    "config",
                    "-f",
                    ".gitmodules",
                    "submodule.vendor/tracked.ignore",
                    "all",
                )
                run_git(
                    superproject,
                    "add",
                    "--",
                    ".gitmodules",
                    "vendor/tracked",
                )
                run_git(
                    superproject,
                    "commit",
                    "-q",
                    "-m",
                    "fixture superproject",
                )
                submodule = superproject / "vendor/tracked"
                if case == "dirty":
                    (submodule / "tracked.txt").write_text(
                        "dirty\n", encoding="utf-8"
                    )
                elif case == "moved-head":
                    run_git(submodule, "config", "user.name", "Fixture")
                    run_git(
                        submodule,
                        "config",
                        "user.email",
                        "fixture@example.invalid",
                    )
                    (submodule / "tracked.txt").write_text(
                        "moved\n", encoding="utf-8"
                    )
                    run_git(submodule, "add", "--", "tracked.txt")
                    run_git(submodule, "commit", "-q", "-m", "move gitlink")
                else:
                    (submodule / "untracked.txt").write_text(
                        "untracked\n", encoding="utf-8"
                    )
                self.assertEqual(
                    "",
                    run_git(superproject, "status", "--porcelain").stdout,
                )

                rows = controller._guard_status_rows(str(superproject))

                self.assertTrue(rows)
                self.assertEqual(
                    ["vendor/tracked"], sorted({path for _status, path in rows})
                )

    def test_fresh_step_one_retains_guard_from_an_exact_zero_row_boundary(self):
        controller, state, guard_commit, audit_paths = self.prepare_guard_retention()
        self.assertIsNone(audit_paths)
        configured_log = Path(
            self.target, state["config"]["audit"]["log_path"]
        )
        derived_synopsis = Path(str(configured_log.with_suffix("")) + ".synopsis.md")
        self.assertFalse(configured_log.exists())
        self.assertFalse(derived_synopsis.exists())
        output = io.StringIO()
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stdout(output),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        result = json.loads(output.getvalue())
        self.assertEqual("created", result["disposition"])
        final_paths = (
            Path(self.target, result["retained_report"]["path"]),
            Path(self.target, result["manifest"]["path"]),
        )
        final_before = tuple(
            (path.read_bytes(), path.stat().st_mtime_ns) for path in final_paths
        )
        replay = io.StringIO()
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_elenchus_guard_module",
                side_effect=AssertionError("idempotent replay ran Elenchus"),
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stdout(replay),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        self.assertEqual("already-retained", json.loads(replay.getvalue())["disposition"])
        self.assertEqual(
            final_before,
            tuple((path.read_bytes(), path.stat().st_mtime_ns) for path in final_paths),
        )
        current = controller.load_state(self.target)
        capture = controller.receipted_known_failure_inventory(
            self.target, current
        )
        with mock.patch.object(
            controller, "verify_local_commit", return_value=guard_commit
        ):
            status = controller.inoculation_status(current, capture, self.target)
        self.assertEqual(["kf-453-02"], status["completed_ids"])
        self.assertEqual([], status["remaining_ids"])
        self.assertEqual(guard_commit, status["guard_commit"])
        self.assertEqual("inoculate", state["steps"][0]["phase"])
        with mock.patch.object(
            controller, "verify_local_commit", return_value=guard_commit
        ):
            resume_directive = controller._next_directive(current, self.target)
            resume_packet = controller.delegation_packet(
                self.target, current, resume_directive
            )
        self.assertEqual("inoculate", resume_directive["do"])
        self.assertEqual(guard_commit, resume_directive["guard_commit"])
        self.assertEqual(guard_commit, resume_packet["brief"]["guard_commit"])
        self.assertEqual(["kf-453-02"], resume_packet["brief"]["completed_ids"])
        self.assertEqual([], resume_packet["brief"]["remaining_ids"])
        self.assertEqual([], resume_packet["brief"]["assigned_findings"])
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                current,
            )
        completed_state = controller.load_state(self.target)
        completed = completed_state["steps"][0]
        self.assertEqual("implement", completed["phase"])
        self.assertEqual(
            ["kf-453-02"], completed["receipts"]["inoculate"]["assigned_ids"]
        )
        with mock.patch.object(
            controller, "verify_local_commit", return_value=guard_commit
        ):
            next_directive = controller._next_directive(completed_state, self.target)
            packet = controller.delegation_packet(
                self.target, completed_state, next_directive
            )
        self.assertEqual(guard_commit, next_directive["guard_commit"])
        self.assertEqual(guard_commit, packet["guard_commit"])
        self.assertEqual(guard_commit, packet["brief"]["guard_commit"])

    def test_fresh_step_refuses_ignored_configured_audit_leaves(self):
        controller, state, guard_commit, audit_paths = self.prepare_guard_retention()
        self.assertIsNone(audit_paths)
        log_path = state["config"]["audit"]["log_path"]
        synopsis_path = str(Path(log_path).with_suffix("")) + ".synopsis.md"
        git_exclude = Path(
            self.git("rev-parse", "--git-path", "info/exclude").stdout.strip()
        )
        if not git_exclude.is_absolute():
            git_exclude = Path(self.target, git_exclude)
        with git_exclude.open("a", encoding="utf-8") as handle:
            handle.write(f"/{log_path}\n/{synopsis_path}\n")

        controller_before = self.controller_bytes()
        for relative in (log_path, synopsis_path):
            with self.subTest(relative=relative):
                stale = Path(self.target, relative)
                stale.parent.mkdir(parents=True, exist_ok=True)
                stale.write_text("ignored stale audit evidence\n", encoding="utf-8")
                self.assertEqual("", self.git("status", "--porcelain").stdout)
                with (
                    mock.patch.object(
                        controller,
                        "verify_local_commit",
                        return_value=guard_commit,
                    ),
                    controller.held_lock(self.target, "cmd_retain_guard"),
                    redirect_stderr(io.StringIO()) as errors,
                    self.assertRaises(SystemExit) as refused,
                ):
                    controller.cmd_retain_guard(
                        argparse.Namespace(
                            dir=self.target,
                            finding_id="kf-453-02",
                            guard_commit=guard_commit,
                        )
                    )
                self.assertEqual(2, refused.exception.code)
                self.assertIn("must be absent", errors.getvalue())
                self.assertEqual(controller_before, self.controller_bytes())
                stale.unlink()

    def test_done_inoculate_rediscovers_changed_pair_before_commit(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        retained = self.retain_guard(controller, guard_commit)
        report = Path(self.target, retained["retained_report"]["path"])
        current = controller.load_state(self.target)
        controller_before = self.controller_bytes()
        report_before = report.read_bytes()
        real_evidence = controller._guard_commit_evidence
        writer_calls = 0

        def mutate_after_final_git_audit_check(*args, **kwargs):
            nonlocal writer_calls
            result = real_evidence(*args, **kwargs)
            if kwargs.get("writer"):
                writer_calls += 1
                if writer_calls == 2:
                    report.write_bytes(report_before + b" ")
            return result

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_guard_commit_evidence",
                side_effect=mutate_after_final_git_audit_check,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                current,
            )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(2, writer_calls)
        self.assertEqual(controller_before, self.controller_bytes())
        self.assertEqual(
            "inoculate", controller.load_state(self.target)["steps"][0]["phase"]
        )

    def test_interrupted_manifest_rename_remains_partial_and_recovers(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        real_publish = controller._guard_atomic_no_replace

        def interrupt_after_manifest_rename(directory, stage, final, label):
            real_publish(directory, stage, final, label)
            if final == "kf-453-02.json":
                raise KeyboardInterrupt("fixture interruption after rename")

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_guard_atomic_no_replace",
                side_effect=interrupt_after_manifest_rename,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        self.assertTrue(pending.is_file())
        self.assertTrue(manifest.is_file())
        self.assertEqual(
            [],
            self.current_guard_status(controller, guard_commit)["completed_ids"],
        )

        result = self.retain_guard(controller, guard_commit)
        self.assertEqual("created", result["disposition"])
        self.assertFalse(pending.exists())
        self.assertEqual(
            ["kf-453-02"],
            self.current_guard_status(controller, guard_commit)["completed_ids"],
        )

    def test_pending_a_report_a_recover_without_rerun_b(self):
        controller, state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        report = evidence_root / "reports/kf-453-02.report"
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        completion = evidence_root / "manifests/.complete-kf-453-02.json"
        intent = evidence_root / "manifests/.intent-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        real_publish = controller._guard_atomic_no_replace

        def interrupt_after_manifest_rename(directory, stage, final, label):
            real_publish(directory, stage, final, label)
            if final == "kf-453-02.json":
                raise KeyboardInterrupt("fixture interruption after rename")

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_guard_atomic_no_replace",
                side_effect=interrupt_after_manifest_rename,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        def exact_leaf(path):
            info = path.lstat()
            return path.read_bytes(), (
                info.st_dev,
                info.st_ino,
                info.st_mode,
                info.st_nlink,
                info.st_size,
                info.st_mtime_ns,
                info.st_ctime_ns,
            )

        before = {
            "report": exact_leaf(report),
            "pending": exact_leaf(pending),
            "manifest": exact_leaf(manifest),
            "controller": self.controller_bytes(),
        }
        report_b = (
            json.dumps(
                json.loads(report.read_text(encoding="utf-8")),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        result_b = {
            "ref": state["steps"][0]["inoculation_parent"],
            "status": "guarded",
            "tests": ["fixture"],
            "detail": "ordinary assertion failure",
            "report": {
                "complete": True,
                "executed": 1,
                "assertion_failures": 1,
                "errors": 0,
                "skipped": 0,
            },
            "raw_report": report_b,
            "exit_code": 1,
            "output": "",
        }
        elenchus_b = mock.Mock()
        elenchus_b.parent_guard_evidence.return_value = result_b
        output = io.StringIO()
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller, "_elenchus_guard_module", return_value=elenchus_b
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stdout(output),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        recovered = json.loads(output.getvalue())
        self.assertEqual("created", recovered["disposition"])
        elenchus_b.parent_guard_evidence.assert_not_called()
        self.assertEqual(before["report"], exact_leaf(report))
        self.assertEqual(before["manifest"], exact_leaf(manifest))
        self.assertFalse(pending.exists())
        self.assertTrue(completion.is_file())
        self.assertEqual(before["pending"][0], intent.read_bytes())
        self.assertEqual(before["controller"], self.controller_bytes())
        self.assertEqual(
            ["kf-453-02"],
            self.current_guard_status(controller, guard_commit)["completed_ids"],
        )

    def test_pending_report_reconstructs_missing_manifest_without_runner(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        report = evidence_root / "reports/kf-453-02.report"
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        completion = evidence_root / "manifests/.complete-kf-453-02.json"
        intent = evidence_root / "manifests/.intent-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_guard_publish_manifest",
                side_effect=KeyboardInterrupt("fixture after pending publication"),
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        self.assertTrue(report.is_file())
        self.assertTrue(pending.is_file())
        self.assertFalse(manifest.exists())
        self.assertFalse(completion.exists())
        report_bytes = report.read_bytes()
        pending_bytes = pending.read_bytes()
        marker = json.loads(pending_bytes)
        controller_before = self.controller_bytes()

        restarted = hexctl_module()
        elenchus = mock.Mock()
        output = io.StringIO()
        with (
            mock.patch.object(
                restarted, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                restarted, "_elenchus_guard_module", return_value=elenchus
            ),
            restarted.held_lock(self.target, "cmd_retain_guard"),
            redirect_stdout(output),
        ):
            restarted.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        recovered = json.loads(output.getvalue())
        self.assertEqual("created", recovered["disposition"])
        elenchus.parent_guard_evidence.assert_not_called()
        self.assertEqual(report_bytes, report.read_bytes())
        self.assertEqual(
            marker["manifest_sha256"], hashlib.sha256(manifest.read_bytes()).hexdigest()
        )
        recovered_manifest = json.loads(manifest.read_bytes())
        self.assertEqual(marker["runner_exit"], recovered_manifest["runner_exit"])
        self.assertEqual(marker["counters"], recovered_manifest["counters"])
        self.assertFalse(pending.exists())
        self.assertEqual(pending_bytes, intent.read_bytes())
        self.assertTrue(completion.is_file())
        self.assertEqual(controller_before, self.controller_bytes())

    def test_failed_pending_directory_fsync_recovers_before_manifest_staging(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        report = evidence_root / "reports/kf-453-02.report"
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        completion = evidence_root / "manifests/.complete-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        manifest_directory = manifest.parent
        real_fsync = controller.os.fsync
        failed = False

        def fail_pending_directory_fsync(descriptor):
            nonlocal failed
            opened = controller.os.fstat(descriptor)
            directory = (
                manifest_directory.stat()
                if manifest_directory.exists()
                else None
            )
            if (
                not failed
                and report.is_file()
                and pending.is_file()
                and not manifest.exists()
                and not completion.exists()
                and directory is not None
                and (opened.st_dev, opened.st_ino)
                == (directory.st_dev, directory.st_ino)
            ):
                failed = True
                raise OSError("fixture pending directory fsync failure")
            return real_fsync(descriptor)

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller.os,
                "fsync",
                side_effect=fail_pending_directory_fsync,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        self.assertTrue(failed)
        self.assertEqual(2, refused.exception.code)
        self.assertTrue(report.is_file())
        self.assertTrue(pending.is_file())
        self.assertFalse(manifest.exists())
        self.assertFalse(completion.exists())
        pending_bytes = pending.read_bytes()

        restarted = hexctl_module()
        events = []
        pending_durable = False
        pending_reread = False
        real_directory_fsync = restarted._guard_fsync_directory
        real_read_publication = restarted._guard_read_publication
        real_commit_evidence = restarted._guard_commit_evidence
        real_write_stage = restarted._guard_write_stage

        def record_directory_fsync(directory, label):
            nonlocal pending_durable
            result = real_directory_fsync(directory, label)
            if label == "guard publication marker kf-453-02":
                pending_durable = True
                events.append("pending-durable")
            return result

        def record_publication_read(directory, finding_id, *, missing_ok):
            nonlocal pending_reread
            result = real_read_publication(
                directory, finding_id, missing_ok=missing_ok
            )
            if pending_durable and not pending_reread:
                self.assertIsNotNone(result)
                self.assertEqual(pending_bytes, result[0])
                pending_reread = True
                events.append("pending-reread")
            return result

        def record_commit_evidence(*args, **kwargs):
            result = real_commit_evidence(*args, **kwargs)
            if pending_reread and "revalidated" not in events:
                events.append("revalidated")
            return result

        def record_write_stage(directory, payload, label, *, limit):
            if label == "guard manifest kf-453-02":
                events.append("manifest-stage")
            return real_write_stage(directory, payload, label, limit=limit)

        elenchus = mock.Mock()
        module_loader = mock.Mock(return_value=elenchus)
        output = io.StringIO()
        with (
            mock.patch.object(
                restarted, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                restarted,
                "_guard_fsync_directory",
                side_effect=record_directory_fsync,
            ),
            mock.patch.object(
                restarted,
                "_guard_read_publication",
                side_effect=record_publication_read,
            ),
            mock.patch.object(
                restarted,
                "_guard_commit_evidence",
                side_effect=record_commit_evidence,
            ),
            mock.patch.object(
                restarted,
                "_guard_write_stage",
                side_effect=record_write_stage,
            ),
            mock.patch.object(
                restarted, "_elenchus_guard_module", module_loader
            ),
            restarted.held_lock(self.target, "cmd_retain_guard"),
            redirect_stdout(output),
        ):
            restarted.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        self.assertEqual(
            ["pending-durable", "pending-reread", "revalidated", "manifest-stage"],
            events[:4],
        )
        self.assertEqual("created", json.loads(output.getvalue())["disposition"])
        module_loader.assert_not_called()
        elenchus.parent_guard_evidence.assert_not_called()
        self.assertFalse(pending.exists())
        self.assertTrue(manifest.is_file())
        self.assertTrue(completion.is_file())

    def test_pending_mismatch_matrix_refuses_without_runner_or_mutation(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        report = evidence_root / "reports/kf-453-02.report"
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        completion = evidence_root / "manifests/.complete-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        foreign = evidence_root / "manifests/foreign.json"

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_guard_publish_manifest",
                side_effect=KeyboardInterrupt("fixture after pending publication"),
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        baseline = self.guard_controller_tree()
        marker_bytes = pending.read_bytes()

        def rewrite_marker(mutate):
            marker = json.loads(marker_bytes)
            mutate(marker)
            pending.write_bytes(
                (
                    json.dumps(marker, sort_keys=True, separators=(",", ":"))
                    + "\n"
                ).encode("ascii")
            )
            pending.chmod(0o600)

        cases = (
            (
                "runner_exit",
                lambda: rewrite_marker(
                    lambda marker: marker.__setitem__(
                        "runner_exit", marker["runner_exit"] + 1
                    )
                ),
                "immutable context",
            ),
            (
                "report",
                lambda: report.write_bytes(report.read_bytes() + b" "),
                "differs from its pending publication marker",
            ),
            (
                "digest",
                lambda: rewrite_marker(
                    lambda marker: marker.__setitem__("manifest_sha256", "0" * 64)
                ),
                "immutable context",
            ),
            (
                "context",
                lambda: self.rewrite_last_controller_state(
                    {
                        **controller.load_state(self.target),
                        "topic": controller.load_state(self.target)["topic"]
                        + " context drift",
                    }
                ),
                "immutable context",
            ),
            (
                "mode",
                lambda: pending.chmod(0o640),
                "does not retain mode 0600",
            ),
            (
                "foreign_leaf",
                lambda: foreign.write_bytes(b"foreign guard evidence\n"),
                "foreign final leaf",
            ),
            (
                "counters",
                lambda: rewrite_marker(
                    lambda marker: marker["counters"].__setitem__(
                        "assertion_failures", 2
                    )
                ),
                "not admissible",
            ),
        )

        for name, mutate, expected_error in cases:
            with self.subTest(name=name):
                self.restore_guard_controller_tree(baseline)
                mutate()
                before = self.guard_controller_tree()
                elenchus = mock.Mock()
                module_loader = mock.Mock(return_value=elenchus)
                with (
                    mock.patch.object(
                        controller, "verify_local_commit", return_value=guard_commit
                    ),
                    mock.patch.object(
                        controller, "_elenchus_guard_module", module_loader
                    ),
                    controller.held_lock(self.target, "cmd_retain_guard"),
                    redirect_stderr(io.StringIO()) as errors,
                    self.assertRaises(SystemExit) as refused,
                ):
                    controller.cmd_retain_guard(
                        argparse.Namespace(
                            dir=self.target,
                            finding_id="kf-453-02",
                            guard_commit=guard_commit,
                        )
                    )

                self.assertEqual(2, refused.exception.code)
                self.assertIn(expected_error, errors.getvalue())
                module_loader.assert_not_called()
                elenchus.parent_guard_evidence.assert_not_called()
                self.assertEqual(before, self.guard_controller_tree())
                self.assertFalse(manifest.exists())
                self.assertFalse(completion.exists())

        self.restore_guard_controller_tree(baseline)

    def test_orphan_final_manifest_refuses_before_elenchus_or_mutation(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        result = self.retain_guard(controller, guard_commit)
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        report = Path(self.target, result["retained_report"]["path"])
        manifest = Path(self.target, result["manifest"]["path"])
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        completion = evidence_root / "manifests/.complete-kf-453-02.json"
        intent = evidence_root / "manifests/.intent-kf-453-02.json"
        completion.unlink()
        intent.unlink()

        self.assertTrue(report.is_file())
        self.assertTrue(manifest.is_file())
        self.assertFalse(pending.exists())
        self.assertFalse(completion.exists())
        before = self.guard_controller_tree()
        elenchus = mock.Mock()
        module_loader = mock.Mock(return_value=elenchus)
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller, "_elenchus_guard_module", module_loader
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        self.assertEqual(2, refused.exception.code)
        self.assertIn("has no pending or completion authority", errors.getvalue())
        module_loader.assert_not_called()
        elenchus.parent_guard_evidence.assert_not_called()
        self.assertEqual(before, self.guard_controller_tree())

    def test_failed_manifest_directory_fsync_is_not_authority_and_recovers(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        manifest_directory = manifest.parent
        real_fsync = controller.os.fsync
        failed = False

        def fail_first_post_rename_directory_fsync(descriptor):
            nonlocal failed
            opened = controller.os.fstat(descriptor)
            directory = (
                manifest_directory.stat()
                if manifest_directory.exists()
                else None
            )
            if (
                not failed
                and manifest.exists()
                and pending.exists()
                and directory is not None
                and (opened.st_dev, opened.st_ino)
                == (directory.st_dev, directory.st_ino)
            ):
                failed = True
                raise OSError("fixture manifest directory fsync failure")
            return real_fsync(descriptor)

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller.os,
                "fsync",
                side_effect=fail_first_post_rename_directory_fsync,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        self.assertTrue(failed)
        self.assertEqual(2, refused.exception.code)
        self.assertTrue(pending.is_file())
        self.assertTrue(manifest.is_file())
        self.assertEqual(
            [],
            self.current_guard_status(controller, guard_commit)["completed_ids"],
        )

        result = self.retain_guard(controller, guard_commit)
        self.assertEqual("created", result["disposition"])
        self.assertFalse(pending.exists())
        self.assertEqual(
            ["kf-453-02"],
            self.current_guard_status(controller, guard_commit)["completed_ids"],
        )

    def test_guard_completion_fsync_failure_stays_partial_and_recovers(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        report = evidence_root / "reports/kf-453-02.report"
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        completion = evidence_root / "manifests/.complete-kf-453-02.json"
        intent = evidence_root / "manifests/.intent-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        manifest_directory = manifest.parent
        real_fsync = controller.os.fsync
        failed = False

        def fail_completion_directory_fsync(descriptor):
            nonlocal failed
            opened = controller.os.fstat(descriptor)
            directory = (
                manifest_directory.stat()
                if manifest_directory.exists()
                else None
            )
            if (
                not failed
                and report.is_file()
                and manifest.is_file()
                and pending.is_file()
                and completion.is_file()
                and directory is not None
                and (opened.st_dev, opened.st_ino)
                == (directory.st_dev, directory.st_ino)
            ):
                failed = True
                raise OSError("fixture completion directory fsync failure")
            return real_fsync(descriptor)

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller.os,
                "fsync",
                side_effect=fail_completion_directory_fsync,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        self.assertTrue(failed)
        self.assertEqual(2, refused.exception.code)
        self.assertIn("completion record", errors.getvalue())
        self.assertTrue(report.is_file())
        self.assertTrue(manifest.is_file())
        self.assertTrue(pending.is_file())
        self.assertTrue(completion.is_file())
        self.assertFalse(intent.exists())
        pending_bytes = pending.read_bytes()

        restarted = hexctl_module()
        self.assertEqual(
            [],
            self.current_guard_status(restarted, guard_commit)["completed_ids"],
        )
        self.assertEqual(pending_bytes, pending.read_bytes())
        result = self.retain_guard(restarted, guard_commit)
        self.assertEqual("created", result["disposition"])
        self.assertFalse(pending.exists())
        self.assertEqual(pending_bytes, intent.read_bytes())
        self.assertEqual(
            ["kf-453-02"],
            self.current_guard_status(restarted, guard_commit)["completed_ids"],
        )

    def test_guard_completion_interruption_before_intent_retirement_recovers(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        completion = evidence_root / "manifests/.complete-kf-453-02.json"
        intent = evidence_root / "manifests/.intent-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        replacement = b"post-completion opaque guard intent\n"
        real_publish = controller._guard_atomic_no_replace

        def interrupt_before_retirement(directory, source, destination, label):
            if (
                source == ".pending-kf-453-02.json"
                and destination == ".intent-kf-453-02.json"
            ):
                pending.write_bytes(replacement)
                pending.chmod(0o600)
                raise KeyboardInterrupt("fixture before intent retirement")
            return real_publish(directory, source, destination, label)

        before = self.controller_bytes()
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_guard_atomic_no_replace",
                side_effect=interrupt_before_retirement,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        self.assertTrue(manifest.is_file())
        self.assertTrue(pending.is_file())
        self.assertTrue(completion.is_file())
        self.assertFalse(intent.exists())
        self.assertEqual(replacement, pending.read_bytes())
        self.assertEqual(before, self.controller_bytes())

        restarted = hexctl_module()
        restarted_state = restarted.load_state(self.target)
        with (
            restarted.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()) as done_errors,
            self.assertRaises(SystemExit) as refused_done,
        ):
            restarted.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=restarted.cmd_done,
                    phase="inoculate",
                ),
                restarted_state,
            )
        self.assertEqual(2, refused_done.exception.code)
        self.assertIn("empty or incomplete", done_errors.getvalue())
        self.assertEqual(before, self.controller_bytes())
        self.assertEqual(
            [],
            self.current_guard_status(restarted, guard_commit)["completed_ids"],
        )
        result = self.retain_guard(restarted, guard_commit)
        self.assertEqual("created", result["disposition"])
        self.assertFalse(pending.exists())
        self.assertTrue(intent.is_file())
        self.assertEqual(replacement, intent.read_bytes())
        self.assertEqual(
            ["kf-453-02"],
            self.current_guard_status(restarted, guard_commit)["completed_ids"],
        )

    def test_guard_intent_swap_is_preserved_but_cannot_change_completion(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        manifest_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation/manifests"
        )
        pending = manifest_root / ".pending-kf-453-02.json"
        completion = manifest_root / ".complete-kf-453-02.json"
        intent = manifest_root / ".intent-kf-453-02.json"
        replacement = b"swapped ignored intent bytes\n"
        real_publish = controller._guard_atomic_no_replace

        def swap_pending_at_retirement(directory, source, destination, label):
            if (
                source == ".pending-kf-453-02.json"
                and destination == ".intent-kf-453-02.json"
            ):
                pending.write_bytes(replacement)
                pending.chmod(0o600)
            return real_publish(directory, source, destination, label)

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller,
                "_guard_atomic_no_replace",
                side_effect=swap_pending_at_retirement,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stdout(io.StringIO()),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )

        self.assertFalse(pending.exists())
        self.assertTrue(completion.is_file())
        self.assertEqual(replacement, intent.read_bytes())
        self.assertEqual(
            ["kf-453-02"],
            self.current_guard_status(controller, guard_commit)["completed_ids"],
        )

    def test_preoccupied_guard_intent_is_not_overwritten(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        manifest_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation/manifests"
        )
        manifest_root.mkdir(parents=True, exist_ok=True)
        pending = manifest_root / ".pending-kf-453-02.json"
        completion = manifest_root / ".complete-kf-453-02.json"
        intent = manifest_root / ".intent-kf-453-02.json"
        occupied = b"preoccupied intent\n"
        intent.write_bytes(occupied)

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        self.assertEqual(2, refused.exception.code)
        self.assertIn("became occupied", errors.getvalue())
        self.assertEqual(occupied, intent.read_bytes())
        self.assertTrue(pending.is_file())
        self.assertTrue(completion.is_file())
        self.assertEqual(
            [], self.current_guard_status(controller, guard_commit)["completed_ids"]
        )

    def test_manifest_binding_is_revalidated_after_staging_before_rename(self):
        controller, _state, guard_commit, _audit_paths = self.prepare_guard_retention()
        evidence_root = Path(
            self.target, ".hexaemeron/steps/1/inoculation"
        )
        pending = evidence_root / "manifests/.pending-kf-453-02.json"
        manifest = evidence_root / "manifests/kf-453-02.json"
        state_before = self.controller_bytes()
        real_stage = controller._guard_write_stage
        published_names = []

        def stage_then_drift(directory, payload, label, *, limit):
            staged = real_stage(directory, payload, label, limit=limit)
            if label == "guard manifest kf-453-02":
                self.write("post-stage-foreign-row", "binding drift\n")
            return staged

        real_publish = controller._guard_atomic_no_replace

        def record_publish(directory, stage, final, label):
            published_names.append(final)
            return real_publish(directory, stage, final, label)

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            mock.patch.object(
                controller, "_guard_write_stage", side_effect=stage_then_drift
            ),
            mock.patch.object(
                controller,
                "_guard_atomic_no_replace",
                side_effect=record_publish,
            ),
            controller.held_lock(self.target, "cmd_retain_guard"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        self.assertEqual(2, refused.exception.code)
        self.assertTrue(pending.is_file())
        self.assertFalse(manifest.exists())
        self.assertNotIn("kf-453-02.json", published_names)
        self.assertEqual(state_before, self.controller_bytes())

    def test_inherited_audit_pair_refuses_a_third_dirty_row_unchanged(self):
        controller, _state, guard_commit, audit_paths = self.prepare_guard_retention(
            inherited_audit=True
        )
        self.assertIsNotNone(audit_paths)
        self.write("foreign-untracked.txt", "not part of the audit pair\n")
        before = self.controller_bytes()
        pair_before = tuple(Path(self.target, path).read_bytes() for path in audit_paths)
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
            controller.held_lock(self.target, "cmd_retain_guard"),
        ):
            controller.cmd_retain_guard(
                argparse.Namespace(
                    dir=self.target,
                    finding_id="kf-453-02",
                    guard_commit=guard_commit,
                )
            )
        self.assertEqual(2, refused.exception.code)
        self.assertIn("exactly the untracked audit pair", errors.getvalue())
        self.assertEqual(before, self.controller_bytes())
        self.assertEqual(
            pair_before,
            tuple(Path(self.target, path).read_bytes() for path in audit_paths),
        )

    def test_clean_capture_reconstructs_the_exact_mason_packet(self):
        directive, _ = self.prepare_capture(assigned=True)
        capture = self.state()["receipts"]["runbook"]["known_failure_inventory"]

        self.assertEqual("inoculate", directive["do"])
        self.assertEqual("mason", directive["agent"])
        self.assertEqual(
            {
                "study_sha256",
                "runbook_sha256",
                "inventory_sha256",
                "known_failure_inventory",
                "consuming_step",
                "assigned_findings",
                "allowed_guard_paths",
                "completed_ids",
                "remaining_ids",
                "reporter_contracts",
                "branch",
                "branch_from",
                "step_parent",
                "evidence_directory",
                "plugin_root",
                "design_evidence",
            },
            set(directive["brief"]),
        )
        self.assertEqual(capture, directive["brief"]["known_failure_inventory"])
        self.assertEqual(capture["study_sha256"], directive["brief"]["study_sha256"])
        self.assertEqual(capture["runbook_sha256"], directive["brief"]["runbook_sha256"])
        self.assertEqual(capture["inventory_sha256"], directive["inventory_sha256"])
        self.assertEqual(["kf-453-02"], directive["remaining_ids"])
        self.assertEqual([], directive["brief"]["completed_ids"])
        self.assertEqual(["kf-453-02"], directive["brief"]["remaining_ids"])
        self.assertEqual(1, directive["assigned_count"])
        self.assertEqual([], directive["completed_ids"])
        self.assertEqual(
            capture["findings"], directive["brief"]["assigned_findings"]
        )
        self.assertEqual(
            sorted(capture["findings"][0]["guard_paths"]),
            directive["brief"]["allowed_guard_paths"],
        )
        self.assertEqual(directive["step_parent"], directive["brief"]["step_parent"])
        self.assertTrue(
            directive["brief"]["evidence_directory"].endswith(
                "/.hexaemeron/steps/1/inoculation"
            )
        )
        self.assertEqual(
            [
                {
                    "finding_id": "kf-453-02",
                    "test_command": capture["findings"][0]["test_command"],
                    "report_format": "unittest-json-v1",
                    "report_file": ".elenchus/issue-453-kf-453-02.json",
                    "green_command": capture["findings"][0]["green_command"],
                }
            ],
            directive["brief"]["reporter_contracts"],
        )

    def test_zero_assigned_mason_packet_drives_the_exact_branch_boundary(self):
        self.prepare_capture()
        self.git(
            "add",
            "--",
            "study.md",
            "runbook.md",
            "steps.json",
            "audit/rounds/source.md",
            "audit/rounds/source.synopsis.md",
        )
        self.git("commit", "-q", "-m", "fixture no-known packet parent")
        parent = self.git("rev-parse", "HEAD").stdout.strip()
        state = self.state()
        state["steps"][0]["inoculation_parent"] = parent
        self.rewrite_last_controller_state(state)
        self.fake_refs[state["run_branch"]] = parent
        directive = self.next_json()
        brief = directive["brief"]

        self.assertEqual([], brief["assigned_findings"])
        self.assertEqual([], brief["allowed_guard_paths"])
        self.assertEqual([], brief["completed_ids"])
        self.assertEqual([], brief["remaining_ids"])
        self.assertEqual([], brief["reporter_contracts"])
        self.assertNotIn("guard_commit", brief)
        self.git("checkout", "-q", "-b", brief["branch"], brief["step_parent"])
        record = self.write_no_known_findings()

        self.run_ctl("done", "inoculate")
        implementation = self.next_json()

        self.assertEqual("implement", implementation["do"])
        self.assertEqual(brief["step_parent"], implementation["step_parent"])
        self.assertEqual(
            brief["step_parent"], implementation["brief"]["step_parent"]
        )
        self.assertNotIn("guard_commit", implementation)
        self.assertNotIn("guard_commit", implementation["brief"])
        self.assertEqual(
            record,
            self.state()["steps"][0]["receipts"]["inoculate"][
                "no_known_findings"
            ],
        )

    def test_assigned_declaration_without_manifests_refuses_unchanged(self):
        self.prepare_capture(assigned=True)
        self.write(".hexaemeron/checkpoints/probe", "checkpoint bytes\n")
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("guard_manifests is empty", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_zero_assigned_record_receipts_the_closed_shape(self):
        directive, _ = self.prepare_no_known_boundary()
        record = self.write_no_known_findings()

        result = self.run_ctl("done", "inoculate")

        self.assertIn("phase -> implement", result.stdout)
        state = self.state()
        receipt = state["steps"][0]["receipts"]["inoculate"]
        self.assertEqual(
            {
                "schema",
                "step",
                "study_sha256",
                "runbook_sha256",
                "inventory_sha256",
                "step_parent",
                "assigned_ids",
                "source_views",
                "no_known_findings",
                "guard_manifests",
            },
            set(receipt),
        )
        self.assertEqual("fiat-known-failure-inoculation/v1", receipt["schema"])
        self.assertEqual(directive["step_parent"], receipt["step_parent"])
        self.assertEqual([], receipt["assigned_ids"])
        self.assertEqual([], receipt["guard_manifests"])
        self.assertEqual(record, receipt["no_known_findings"])
        self.assertEqual("implement", self.next_json()["do"])
        self.run_ctl("verify")

    def test_no_known_accepts_and_binds_an_absent_gitlink_object(self):
        gitlink_oid = "1" * 40
        directive, _ = self.prepare_no_known_boundary(tracked_gitlink=True)
        controller = hexctl_module()
        system_git = controller.shutil.which("git", path=controller.os.defpath)
        self.assertIsNotNone(system_git)
        missing = subprocess.run(
            [system_git, "cat-file", "-e", f"{gitlink_oid}^{{commit}}"],
            cwd=self.target,
            capture_output=True,
        )
        self.assertNotEqual(0, missing.returncode)
        raw_tree = controller._guard_exact_git(
            self.target,
            ["ls-tree", "-r", "-z", "--full-tree", directive["step_parent"]],
            "fixture HEAD tree cannot be read",
        )

        tracked = controller._guard_tracked_worktree(
            self.target, directive["step_parent"]
        )

        rows = [row for row in raw_tree.split(b"\0") if row]
        self.assertIn(
            (
                f"160000 commit {gitlink_oid}\t"
                "vendor/absent-submodule"
            ).encode("ascii"),
            rows,
        )
        self.assertEqual(len(rows), tracked["count"])
        self.assertEqual(hashlib.sha256(raw_tree).hexdigest(), tracked["tree_sha256"])
        self.write_no_known_findings()
        completed = self.run_ctl("done", "inoculate")
        self.assertIn("phase -> implement", completed.stdout)
        self.run_ctl("verify")

    def test_no_known_refuses_mismatched_gitlink_tree_metadata(self):
        controller = hexctl_module()
        oid = "1" * 40
        rows = (
            f"160000 blob {oid}\tvendor/submodule\0".encode("ascii"),
            f"100644 commit {oid}\tvendor/submodule\0".encode("ascii"),
        )
        for raw_tree in rows:
            with self.subTest(raw_tree=raw_tree), mock.patch.object(
                controller, "_guard_exact_git", return_value=raw_tree
            ), redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as refused:
                controller._guard_tracked_worktree(self.target, "a" * 40)
            self.assertEqual(2, refused.exception.code)

    def test_no_known_refuses_an_unauthorised_product_commit_unchanged(self):
        self.prepare_no_known_boundary(tracked_product=True)
        self.write_no_known_findings()
        self.write("product.py", "VALUE = 'unauthorised commit'\n")
        self.git("add", "--", "product.py")
        self.git("commit", "-q", "-m", "unauthorised product commit")
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("exact Step branch", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_refuses_a_dirty_tracked_product_edit_unchanged(self):
        self.prepare_no_known_boundary(tracked_product=True)
        self.write_no_known_findings()
        self.write("product.py", "VALUE = 'dirty product edit'\n")
        self.assertIn(" M product.py", self.git("status", "--porcelain").stdout)
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("differs from native HEAD", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_refuses_assume_unchanged_tracked_edit_unchanged(self):
        self.prepare_no_known_boundary(tracked_product=True)
        self.write_no_known_findings()
        self.git("update-index", "--assume-unchanged", "--", "product.py")
        self.write("product.py", "VALUE = 'hidden dirty edit'\n")
        self.assertEqual("", self.git("status", "--porcelain").stdout)
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("differs from native HEAD", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_refuses_hidden_loss_of_owner_execute_unchanged(self):
        self.prepare_no_known_boundary(tracked_executable=True)
        self.write_no_known_findings()
        tool = Path(self.target, "tool.sh")
        self.git("update-index", "--assume-unchanged", "--", "tool.sh")
        tool.chmod(0o655)
        self.assertEqual("", self.git("status", "--porcelain").stdout)
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("wrong executable mode", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_refuses_a_worktree_alias_unchanged(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        alias = Path(self.dir, "no-known-worktree-alias")
        alias.symlink_to(self.target, target_is_directory=True)
        before = self.controller_bytes()

        with (
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=str(alias),
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertEqual(2, refused.exception.code)
        self.assertIn("physical directory", errors.getvalue())
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_revalidates_exact_record_bytes_before_commit(self):
        self.prepare_no_known_boundary()
        record = self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        record_path = Path(
            self.target,
            ".hexaemeron/steps/1/inoculation/no-known-findings.json",
        )
        before = self.controller_bytes()
        real_boundary = controller._guard_no_known_boundary
        boundary_calls = 0

        def reformat_after_initial_snapshot(*args, **kwargs):
            nonlocal boundary_calls
            result = real_boundary(*args, **kwargs)
            boundary_calls += 1
            if boundary_calls == 2:
                record_path.write_text(
                    json.dumps(record, sort_keys=True, separators=(",", ":"))
                    + "\n",
                    encoding="utf-8",
                )
            return result

        with (
            mock.patch.object(
                controller,
                "_guard_no_known_boundary",
                side_effect=reformat_after_initial_snapshot,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(4, boundary_calls)
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_revalidates_state_observation_before_commit(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        before = self.controller_bytes()
        observed = json.loads(json.dumps(state))
        observed["steps"][0]["title"] = "changed observation"

        with (
            mock.patch.object(controller, "load_state", return_value=observed),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_rederives_capture_after_middle_source_mutation(self):
        _directive, source_path = self.prepare_no_known_boundary()
        self.write_no_known_findings()
        self.git("update-index", "--assume-unchanged", "--", source_path)
        controller = hexctl_module()
        state = controller.load_state(self.target)
        before = self.controller_bytes()
        real_snapshot = controller._no_known_findings_snapshot
        snapshot_calls = 0

        def mutate_source_after_middle_snapshot(*args, **kwargs):
            nonlocal snapshot_calls
            result = real_snapshot(*args, **kwargs)
            snapshot_calls += 1
            if snapshot_calls == 2:
                Path(self.target, source_path).write_text(
                    "changed source hidden from Git status\n",
                    encoding="utf-8",
                )
            return result

        with (
            mock.patch.object(
                controller,
                "_no_known_findings_snapshot",
                side_effect=mutate_source_after_middle_snapshot,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(2, snapshot_calls)
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_final_record_read_is_closed_by_head_boundary(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        before = self.controller_bytes()
        real_snapshot = controller._no_known_findings_snapshot
        snapshot_calls = 0

        def advance_head_after_last_record(*args, **kwargs):
            nonlocal snapshot_calls
            result = real_snapshot(*args, **kwargs)
            snapshot_calls += 1
            if snapshot_calls == 3:
                self.write("late-record-head.py", "LATE = True\n")
                self.git("add", "--", "late-record-head.py")
                self.git("commit", "-q", "-m", "fixture final-record HEAD advance")
            return result

        with (
            mock.patch.object(
                controller,
                "_no_known_findings_snapshot",
                side_effect=advance_head_after_last_record,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(3, snapshot_calls)
        self.assertIn("exact Step branch", errors.getvalue())
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_final_capture_read_is_closed_by_head_boundary(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        before = self.controller_bytes()
        real_capture = controller.receipted_known_failure_inventory
        capture_calls = 0

        def advance_head_after_last_capture(*args, **kwargs):
            nonlocal capture_calls
            result = real_capture(*args, **kwargs)
            capture_calls += 1
            if capture_calls == 3:
                self.write("late-head.py", "LATE = True\n")
                self.git("add", "--", "late-head.py")
                self.git("commit", "-q", "-m", "fixture late HEAD advance")
            return result

        with (
            mock.patch.object(
                controller,
                "receipted_known_failure_inventory",
                side_effect=advance_head_after_last_capture,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(3, capture_calls)
        self.assertIn("exact Step branch", errors.getvalue())
        self.assertEqual(before, self.controller_bytes())

    def test_no_known_transaction_binds_mutation_after_third_snapshot(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        record_path = Path(
            self.target,
            ".hexaemeron/steps/1/inoculation/no-known-findings.json",
        )
        original = record_path.read_bytes()
        record = json.loads(original)
        before = self.controller_bytes()
        real_snapshot = controller._no_known_findings_snapshot
        snapshot_calls = 0

        def reformat_after_third_snapshot(*args, **kwargs):
            nonlocal snapshot_calls
            result = real_snapshot(*args, **kwargs)
            snapshot_calls += 1
            if snapshot_calls == 3:
                record_path.write_text(
                    json.dumps(record, sort_keys=True, separators=(",", ":"))
                    + "\n",
                    encoding="utf-8",
                )
            return result

        with (
            mock.patch.object(
                controller,
                "_no_known_findings_snapshot",
                side_effect=reformat_after_third_snapshot,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        marker = Path(
            self.target, ".hexaemeron", controller.NO_KNOWN_TRANSACTION_FILE
        )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(4, snapshot_calls)
        self.assertIn("transaction evidence changed", errors.getvalue())
        self.assertTrue(marker.is_file())
        self.assertEqual(before, self.controller_bytes())
        blocked = self.run_ctl("status", "--json", expect=2)
        self.assertIn("transaction is pending", blocked.stderr)

        record_path.write_bytes(original)
        recovered = self.run_ctl("done", "inoculate")
        self.assertIn("phase -> implement", recovered.stdout)
        self.assertFalse(marker.exists())

    def test_no_known_transaction_binds_head_after_fourth_boundary(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        before = self.controller_bytes()
        real_boundary = controller._guard_no_known_boundary
        boundary_calls = 0

        def advance_head_after_fourth_boundary(*args, **kwargs):
            nonlocal boundary_calls
            boundary_calls += 1
            result = real_boundary(*args, **kwargs)
            if boundary_calls == 4:
                self.write("post-boundary-head.py", "LATE = True\n")
                self.git("add", "--", "post-boundary-head.py")
                self.git("commit", "-q", "-m", "fixture post-boundary HEAD advance")
            return result

        with (
            mock.patch.object(
                controller,
                "_guard_no_known_boundary",
                side_effect=advance_head_after_fourth_boundary,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        marker = Path(
            self.target, ".hexaemeron", controller.NO_KNOWN_TRANSACTION_FILE
        )
        self.assertEqual(2, refused.exception.code)
        self.assertEqual(5, boundary_calls, errors.getvalue())
        self.assertIn("exact Step branch", errors.getvalue())
        self.assertTrue(marker.is_file())
        self.assertEqual(before, self.controller_bytes())
        blocked = self.run_ctl("next", expect=2)
        self.assertIn("transaction is pending", blocked.stderr)

    def test_no_known_completion_fsync_failure_recovers_before_authority(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        state_root = Path(self.target, ".hexaemeron")
        pending = state_root / controller.NO_KNOWN_TRANSACTION_FILE
        completion = state_root / controller._no_known_completion_name(1)
        intent = state_root / controller._no_known_retired_name(1)
        root_identity = state_root.stat()
        real_fsync = controller.os.fsync
        failed = False

        def fail_positive_completion_directory_fsync(descriptor):
            nonlocal failed
            opened = controller.os.fstat(descriptor)
            if (
                not failed
                and pending.is_file()
                and completion.is_file()
                and (opened.st_dev, opened.st_ino)
                == (root_identity.st_dev, root_identity.st_ino)
            ):
                failed = True
                raise OSError("fixture no-known completion fsync failure")
            return real_fsync(descriptor)

        before = self.controller_bytes()
        with (
            mock.patch.object(
                controller.os,
                "fsync",
                side_effect=fail_positive_completion_directory_fsync,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertTrue(failed)
        self.assertEqual(2, refused.exception.code)
        self.assertIn("completion", errors.getvalue())
        self.assertTrue(pending.is_file())
        self.assertTrue(completion.is_file())
        self.assertFalse(intent.exists())
        self.assertEqual(before, self.controller_bytes())
        blocked = self.run_ctl("status", "--json", expect=2)
        self.assertIn("transaction is pending", blocked.stderr)

        recovered = self.run_ctl("done", "inoculate")
        self.assertIn("phase -> implement", recovered.stdout)
        self.assertFalse(pending.exists())
        self.assertTrue(completion.is_file())
        self.assertTrue(intent.is_file())
        self.run_ctl("verify")

    def test_no_known_completion_binds_the_exact_full_ledger_entry(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        state_root = Path(self.target, ".hexaemeron")
        pending = state_root / controller.NO_KNOWN_TRANSACTION_FILE
        completion = state_root / controller._no_known_completion_name(1)

        with (
            mock.patch.object(
                controller,
                "_append_no_known_ledger_entry",
                side_effect=KeyboardInterrupt("fixture before exact ledger append"),
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stderr(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertTrue(pending.is_file())
        self.assertTrue(completion.is_file())
        marker = json.loads(completion.read_text(encoding="utf-8"))
        attacker = dict(marker["ledger_entry"])
        attacker["ts"] = "2099-01-01T00:00:00Z"
        attacker["hash"] = hashlib.sha256(
            controller.canonical(
                {
                    key: attacker[key]
                    for key in ("ts", "event", "data", "prev", "state")
                }
            ).encode()
        ).hexdigest()
        with Path(self.target, ".hexaemeron/ledger.jsonl").open(
            "a", encoding="utf-8"
        ) as handle:
            handle.write(json.dumps(attacker, sort_keys=True) + "\n")

        refused = self.run_ctl("done", "inoculate", expect=1)

        self.assertIn("unrelated transition", refused.stderr)
        retained_state = json.loads(
            Path(self.target, ".hexaemeron/state.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual("inoculate", retained_state["steps"][0]["phase"])
        self.assertNotEqual(attacker, marker["ledger_entry"])

    def test_no_known_partial_ledger_stage_leaves_final_recoverable(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        state_root = Path(self.target, ".hexaemeron")
        ledger = state_root / "ledger.jsonl"
        pending = state_root / controller.NO_KNOWN_TRANSACTION_FILE
        completion = state_root / controller._no_known_completion_name(1)
        before_ledger = ledger.read_bytes()
        real_write = controller._guard_write_all
        interrupted = False

        def interrupt_partial_stage(descriptor, payload, label):
            nonlocal interrupted
            if label == "no-known inoculation ledger replacement":
                interrupted = True
                controller.os.write(descriptor, payload[: len(payload) // 2])
                raise KeyboardInterrupt("fixture partial ledger stage")
            return real_write(descriptor, payload, label)

        with (
            mock.patch.object(
                controller,
                "_guard_write_all",
                side_effect=interrupt_partial_stage,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertTrue(interrupted)
        self.assertEqual(before_ledger, ledger.read_bytes())
        self.assertTrue(pending.is_file())
        self.assertTrue(completion.is_file())
        self.assertEqual(
            "inoculate",
            json.loads((state_root / "state.json").read_text())["steps"][0][
                "phase"
            ],
        )

        recovered = self.run_ctl("done", "inoculate")

        self.assertIn("phase -> implement", recovered.stdout)
        self.assertNotEqual(before_ledger, ledger.read_bytes())
        self.run_ctl("verify")

    def test_no_known_state_uses_fsynced_random_no_follow_stage(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        state_root = Path(self.target, ".hexaemeron")
        sentinel = Path(self.tmp.name, "outside-state-sentinel")
        sentinel.write_bytes(b"outside sentinel stays exact\n")
        fixed_stage = state_root / "state.json.tmp"
        fixed_stage.symlink_to(sentinel)
        before_sentinel = sentinel.read_bytes()
        fsynced = set()
        state_replace_checked = False
        real_fsync = controller.os.fsync
        real_replace = controller._guard_atomic_replace

        def record_fsync(descriptor):
            identity = controller.os.fstat(descriptor)
            fsynced.add((identity.st_dev, identity.st_ino))
            return real_fsync(descriptor)

        def require_fsynced_stage(directory, stage, final, label):
            nonlocal state_replace_checked
            if final == controller.STATE_FILE:
                staged = controller.os.stat(
                    stage, dir_fd=directory, follow_symlinks=False
                )
                self.assertIn((staged.st_dev, staged.st_ino), fsynced)
                state_replace_checked = True
            return real_replace(directory, stage, final, label)

        with (
            mock.patch.object(controller.os, "fsync", side_effect=record_fsync),
            mock.patch.object(
                controller,
                "_guard_atomic_replace",
                side_effect=require_fsynced_stage,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )

        self.assertTrue(state_replace_checked)
        self.assertTrue(fixed_stage.is_symlink())
        self.assertEqual(before_sentinel, sentinel.read_bytes())
        self.assertEqual("implement", self.next_json()["do"])
        self.run_ctl("verify")

    def test_no_known_completion_seals_raw_bytes_before_input_drift(self):
        self.prepare_no_known_boundary()
        record = self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        record_path = Path(
            self.target,
            ".hexaemeron/steps/1/inoculation/no-known-findings.json",
        )
        original = record_path.read_bytes()
        changed = (
            json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        real_revalidate = controller._revalidate_no_known_transaction
        revalidated = False

        def drift_after_final_live_observation(*args, **kwargs):
            nonlocal revalidated
            result = real_revalidate(*args, **kwargs)
            if not revalidated:
                revalidated = True
                record_path.write_bytes(changed)
            return result

        with (
            mock.patch.object(
                controller,
                "_revalidate_no_known_transaction",
                side_effect=drift_after_final_live_observation,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertTrue(revalidated)
        self.assertEqual(changed, record_path.read_bytes())
        completed = controller.load_no_known_completion(self.target, 1)
        self.assertIsNotNone(completed)
        self.assertEqual(original.decode("utf-8"), completed[2]["no_known_text"])
        self.assertEqual(record, completed[2]["receipt"]["no_known_findings"])
        self.assertEqual("implement", self.next_json()["do"])
        self.run_ctl("verify")

    def test_no_known_intent_swap_is_inert_after_positive_completion(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        state_root = Path(self.target, ".hexaemeron")
        pending = state_root / controller.NO_KNOWN_TRANSACTION_FILE
        completion = state_root / controller._no_known_completion_name(1)
        intent = state_root / controller._no_known_retired_name(1)
        replacement = b"swapped inert no-known intent\n"
        real_publish = controller._guard_atomic_no_replace

        def swap_intent_at_retirement(directory, source, destination, label):
            if (
                source == controller.NO_KNOWN_TRANSACTION_FILE
                and destination == controller._no_known_retired_name(1)
            ):
                pending.write_bytes(replacement)
                pending.chmod(0o600)
            return real_publish(directory, source, destination, label)

        with (
            mock.patch.object(
                controller,
                "_guard_atomic_no_replace",
                side_effect=swap_intent_at_retirement,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertFalse(pending.exists())
        self.assertTrue(completion.is_file())
        self.assertEqual(replacement, intent.read_bytes())
        self.assertEqual("implement", self.next_json()["do"])
        self.run_ctl("verify")

    def test_no_known_mutated_pending_crash_before_retirement_recovers(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        controller = hexctl_module()
        state = controller.load_state(self.target)
        state_root = Path(self.target, ".hexaemeron")
        pending = state_root / controller.NO_KNOWN_TRANSACTION_FILE
        completion = state_root / controller._no_known_completion_name(1)
        intent = state_root / controller._no_known_retired_name(1)
        replacement = b"post-completion opaque no-known intent\n"
        real_publish = controller._guard_atomic_no_replace

        def interrupt_before_retirement(directory, source, destination, label):
            if (
                source == controller.NO_KNOWN_TRANSACTION_FILE
                and destination == controller._no_known_retired_name(1)
            ):
                pending.write_bytes(replacement)
                pending.chmod(0o600)
                raise KeyboardInterrupt("fixture before no-known retirement")
            return real_publish(directory, source, destination, label)

        with (
            mock.patch.object(
                controller,
                "_guard_atomic_no_replace",
                side_effect=interrupt_before_retirement,
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
            self.assertRaises(KeyboardInterrupt),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                state,
            )
        self.assertTrue(completion.is_file())
        self.assertTrue(pending.is_file())
        self.assertFalse(intent.exists())
        self.assertEqual(replacement, pending.read_bytes())

        restarted = hexctl_module()
        recovered_state = restarted.load_state(
            self.target, allow_pending_no_known=True
        )
        with (
            restarted.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
        ):
            restarted.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=restarted.cmd_done,
                    phase="inoculate",
                ),
                recovered_state,
            )
        self.assertFalse(pending.exists())
        self.assertEqual(replacement, intent.read_bytes())
        self.assertEqual("implement", self.next_json()["do"])
        self.run_ctl("verify")

    def test_completed_no_known_state_requires_positive_completion(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        controller = hexctl_module()
        completion = Path(
            self.target,
            ".hexaemeron",
            controller._no_known_completion_name(1),
        )
        completion.unlink()
        before = self.controller_bytes()

        refused = self.run_ctl("status", "--json", expect=1)

        self.assertIn("no positive completion record", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_verify_binds_the_inoculation_receipt_to_its_ledger_event(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        ledger_path = Path(self.target, ".hexaemeron", "ledger.jsonl")
        entries = [
            json.loads(line)
            for line in ledger_path.read_text(encoding="utf-8").splitlines()
            if line
        ]
        self.assertEqual("done:inoculate", entries[-1]["event"])
        entries[-1]["event"] = "record:forged-inoculation"
        entries[-1]["hash"] = hashlib.sha256(
            hexctl_module().canonical(
                {
                    key: entries[-1][key]
                    for key in ("ts", "event", "data", "prev", "state")
                }
            ).encode()
        ).hexdigest()
        ledger_path.write_text(
            "".join(json.dumps(entry, sort_keys=True) + "\n" for entry in entries),
            encoding="utf-8",
        )

        refused = self.run_ctl("verify", expect=1)

        self.assertIn("does not match its controller ledger events", refused.stderr)

    def test_zero_assigned_step_uses_capture_views_when_other_steps_have_findings(self):
        self.prepare_no_known_boundary(assigned=True, assigned_step=2)
        capture = self.state()["receipts"]["runbook"]["known_failure_inventory"]
        self.assertIsNone(capture["no_known_findings"])
        record = self.write_no_known_findings()

        self.run_ctl("done", "inoculate")

        receipt = self.state()["steps"][0]["receipts"]["inoculate"]
        self.assertEqual(record, receipt["no_known_findings"])
        self.assertEqual("implement", self.next_json()["do"])

    def test_status_and_next_do_not_print_declared_report_content(self):
        directive, _ = self.prepare_capture(assigned=True)
        marker = "UNRECEIPTED-REPORT-CONTENT-MUST-STAY-OUT"
        self.write(
            ".elenchus/issue-453-kf-453-02.json",
            marker,
        )

        status = self.run_ctl("status", "--json")
        status_payload = json.loads(status.stdout)
        expected = {
            "inventory_sha256": directive["inventory_sha256"],
            "assigned_count": 1,
            "completed_ids": [],
            "remaining_ids": ["kf-453-02"],
        }
        for payload in (directive, status_payload):
            self.assertEqual(
                expected,
                {
                    key: payload[key]
                    for key in (
                        "inventory_sha256",
                        "assigned_count",
                        "completed_ids",
                        "remaining_ids",
                    )
                },
            )
        self.assertNotIn(marker, status.stdout)
        self.assertNotIn(marker, json.dumps(directive))

    def test_foreign_done_options_refuse_before_any_controller_mutation(self):
        self.prepare_capture()
        self.write_no_known_findings()
        self.write(".hexaemeron/checkpoints/probe", "checkpoint bytes\n")
        before = self.controller_bytes()

        for arguments in (
            ("--artifact", "foreign.md"),
            ("--branch", "foreign"),
            ("--no-further-leads",),
            ("--acknowledge-sync-path", "foreign.md"),
        ):
            with self.subTest(arguments=arguments):
                refused = self.run_ctl("done", "inoculate", *arguments, expect=2)
                self.assertIn("accepts no phase-specific options", refused.stderr)
                self.assertEqual(before, self.controller_bytes())

    def test_changed_parent_refuses_before_reading_the_no_known_record(self):
        directive, _ = self.prepare_capture()
        parent = directive["branch_from"]
        self.fake_refs[parent] = self.fake_sha("changed-parent")
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("inoculation parent changed", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_malformed_no_known_record_refuses_unchanged(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings(
            mutate=lambda record: record.update({"unsupported": True})
        )
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("does not match", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_duplicate_inoculation_receipt_refuses_unchanged(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("out of order", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_source_drift_refuses_next_without_controller_mutation(self):
        _, source_path = self.prepare_capture()
        before = self.controller_bytes()
        self.write(source_path, "changed audit source\n")

        refused = self.run_ctl("next", expect=2)

        self.assertIn("K005", refused.stderr)
        self.assertIn("source_sha256 expected", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_post_receipt_source_drift_refuses_implementation_delegation(self):
        _, source_path = self.prepare_no_known_boundary()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        before = self.controller_bytes()
        self.write(source_path, "changed after inoculation receipt\n")

        refused = self.run_ctl("next", expect=2)

        self.assertIn("K005", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_post_receipt_parent_drift_refuses_implementation_delegation(self):
        directive, _ = self.prepare_no_known_boundary()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        before = self.controller_bytes()
        self.fake_refs[directive["branch_from"]] = self.fake_sha(
            "changed-after-inoculation"
        )

        refused = self.run_ctl("next", expect=2)

        self.assertIn("inoculation parent changed", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_implementation_range_stays_bound_to_the_receipted_parent_sha(self):
        self.prepare_no_known_boundary()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        directive = self.next_json()
        state = self.state()
        step = state["steps"][0]
        capture = state["receipts"]["runbook"]["known_failure_inventory"]
        parent = step["receipts"]["inoculate"]["step_parent"]
        branch = self.step_branch(1, state)
        self.write("implementation.py", "VALUE = 'implemented'\n")
        self.git("add", "--", "implementation.py")
        self.git("commit", "-q", "-m", "fixture implementation")
        head = self.git("rev-parse", "HEAD").stdout.strip()
        controller = hexctl_module()

        with (
            mock.patch.object(
                controller,
                "receipted_known_failure_inventory",
                return_value=capture,
            ),
            mock.patch.object(
                controller, "_inoculation_parent", return_value=parent
            ),
            mock.patch.object(controller, "resolved_commit", return_value=head),
            mock.patch.object(
                controller, "verify_local_range", return_value=[head]
            ) as verified,
            mock.patch.object(controller, "commit"),
        ):
            controller.done_implement(
                argparse.Namespace(
                    dir=self.target,
                    branch=branch,
                    commit=head,
                    tests="green",
                ),
                state,
            )

        self.assertEqual(parent, directive["step_parent"])
        self.assertEqual(parent, directive["brief"]["step_parent"])
        self.assertEqual(parent, verified.call_args.args[1])

    def test_implementation_refuses_a_sibling_that_omits_the_guard_commit(self):
        controller, state, guard_commit, _ = self.prepare_guard_retention()
        self.retain_guard(controller, guard_commit)
        current = controller.load_state(self.target)
        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            controller.held_lock(self.target, "cmd_done"),
            redirect_stdout(io.StringIO()),
        ):
            controller.done_inoculate(
                argparse.Namespace(
                    dir=self.target,
                    cmd="done",
                    fn=controller.cmd_done,
                    phase="inoculate",
                ),
                current,
            )
        implementation_state = controller.load_state(self.target)
        parent = implementation_state["steps"][0]["inoculation_parent"]
        branch = self.step_branch(1, implementation_state)
        self.git("checkout", "-q", "--detach", parent)
        self.write("sibling.py", "VALUE = 'guard omitted'\n")
        self.git("add", "--", "sibling.py")
        self.git("commit", "-q", "-m", "fixture sibling implementation")
        sibling = self.git("rev-parse", "HEAD").stdout.strip()
        self.git("checkout", "-q", "-b", "fixture-ambient-guard", guard_commit)
        self.git("branch", "-f", branch, sibling)
        before = self.controller_bytes()
        errors = io.StringIO()

        with (
            mock.patch.object(
                controller, "verify_local_commit", return_value=guard_commit
            ),
            redirect_stderr(errors),
            self.assertRaises(SystemExit) as refused,
        ):
            controller.done_implement(
                argparse.Namespace(
                    dir=self.target,
                    branch=branch,
                    commit=sibling,
                    tests="green",
                ),
                implementation_state,
            )

        self.assertEqual(2, refused.exception.code)
        self.assertIn("declared Step branch checked out", errors.getvalue())
        self.assertEqual(before, self.controller_bytes())

    def test_capture_aware_amendments_derive_current_source_digests(self):
        self.prepare_capture(amendable=True)
        study_path = Path(self.target, "study.md")
        study_candidate = self.write(
            "study-candidate.md",
            study_path.read_text(encoding="utf-8")
            + self.amendment(
                "Step 1: entry holds; exit holds.",
                touched="Step 1.",
            ),
        )
        self.run_ctl("amend", "study", "--artifact", study_candidate)
        after_study = self.state()
        capture = hexctl_module().receipted_known_failure_inventory(
            self.target, after_study
        )
        self.assertEqual(after_study["receipts"]["study"]["sha256"], capture["study_sha256"])
        self.assertEqual(after_study["receipts"]["runbook"]["sha256"], capture["runbook_sha256"])

        runbook_path = Path(self.target, "runbook.md")
        runbook_candidate = self.write(
            "runbook-candidate.md",
            runbook_path.read_text(encoding="utf-8")
            + self.runbook_amendment(
                "Step 1: entry holds; exit holds.",
                touched="Step 1.",
            ),
        )
        self.run_ctl("amend", "runbook", "--artifact", runbook_candidate)
        after_runbook = self.state()
        capture = hexctl_module().receipted_known_failure_inventory(
            self.target, after_runbook
        )
        self.assertEqual(after_runbook["receipts"]["study"]["sha256"], capture["study_sha256"])
        self.assertEqual(after_runbook["receipts"]["runbook"]["sha256"], capture["runbook_sha256"])
        self.assertEqual("inoculate", self.next_json()["do"])
        self.run_ctl("verify")

    def test_holding_amendments_preserve_a_historical_inoculation_receipt(self):
        self.prepare_no_known_boundary(amendable=True)
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        before = self.state()["steps"][0]["receipts"]["inoculate"]

        study_path = Path(self.target, "study.md")
        study_candidate = self.write(
            "study-candidate.md",
            study_path.read_text(encoding="utf-8")
            + self.amendment(
                "Step 1: entry holds; exit holds.",
                touched="Step 1.",
            ),
        )
        self.run_ctl("amend", "study", "--artifact", study_candidate)

        runbook_path = Path(self.target, "runbook.md")
        runbook_candidate = self.write(
            "runbook-candidate.md",
            runbook_path.read_text(encoding="utf-8")
            + self.runbook_amendment(
                "Step 1: entry holds; exit holds.",
                touched="Step 1.",
            ),
        )
        self.run_ctl("amend", "runbook", "--artifact", runbook_candidate)

        state = self.state()
        self.assertEqual(before, state["steps"][0]["receipts"]["inoculate"])
        capture = hexctl_module().receipted_known_failure_inventory(
            self.target, state
        )
        self.assertNotEqual(before["study_sha256"], capture["study_sha256"])
        self.assertNotEqual(before["runbook_sha256"], capture["runbook_sha256"])
        directive = self.next_json()
        self.assertEqual("implement", directive["do"])
        self.assertEqual(before["step_parent"], directive["step_parent"])
        self.assertEqual(before["step_parent"], directive["brief"]["step_parent"])
        self.run_ctl("verify")

    def test_capture_aware_committed_amendment_recovers_with_fresh_capture(self):
        self.prepare_capture(amendable=True)
        runbook_path = Path(self.target, "runbook.md")
        candidate = self.write(
            "runbook-candidate.md",
            runbook_path.read_text(encoding="utf-8")
            + self.runbook_amendment(
                "Step 1: entry holds; exit holds.",
                touched="Step 1.",
            ),
        )
        controller = hexctl_module()
        with mock.patch.object(
            controller,
            "verify_run",
            side_effect=KeyboardInterrupt("after committed amendment"),
        ):
            with self.assertRaises(KeyboardInterrupt):
                controller.cmd_amend_runbook(
                    argparse.Namespace(
                        dir=self.target,
                        artifact=str(Path(self.target, candidate)),
                    )
                )

        recovered = self.run_ctl(
            "amend", "runbook", "--artifact", str(runbook_path)
        )
        self.assertIn("recovered", recovered.stdout)
        state = self.state()
        capture = hexctl_module().receipted_known_failure_inventory(
            self.target, state
        )
        self.assertEqual(state["receipts"]["study"]["sha256"], capture["study_sha256"])
        self.assertEqual(state["receipts"]["runbook"]["sha256"], capture["runbook_sha256"])
        self.run_ctl("verify")

    def test_capture_aware_replacement_before_commit_recovers_once(self):
        self.prepare_capture(amendable=True)
        runbook_path = Path(self.target, "runbook.md")
        candidate = self.write(
            "runbook-candidate.md",
            runbook_path.read_text(encoding="utf-8")
            + self.runbook_amendment(
                "Step 1: entry holds; exit holds.",
                touched="Step 1.",
            ),
        )
        controller = hexctl_module()
        with mock.patch.object(
            controller,
            "commit",
            side_effect=KeyboardInterrupt("after canonical replacement"),
        ):
            with self.assertRaises(KeyboardInterrupt):
                controller.cmd_amend_runbook(
                    argparse.Namespace(
                        dir=self.target,
                        artifact=str(Path(self.target, candidate)),
                    )
                )

        self.assertIn("runbook", controller.pending_amendments(self.target))
        recovered = self.run_ctl(
            "amend", "runbook", "--artifact", str(runbook_path)
        )
        self.assertIn("recovered: recorded", recovered.stdout)
        self.assertEqual({}, controller.pending_amendments(self.target))
        self.run_ctl("verify")

    def test_capture_aware_semantic_amendment_refuses_before_mutation(self):
        self.prepare_capture(amendable=True)
        runbook_path = Path(self.target, "runbook.md")
        original = runbook_path.read_text(encoding="utf-8")
        candidate = self.write(
            "runbook-candidate.md",
            original
            + self.runbook_amendment(
                "Step 1: entry holds; exit holds.",
                what=(
                    "Complete replacement Exit: Run `python3 -m unittest`.\n"
                    "Known-failure assignment: `kf-453-99` -> Step 1"
                ),
                touched="Step 1.",
            ),
        )
        before = self.controller_bytes()

        refused = self.run_ctl(
            "amend", "runbook", "--artifact", candidate, expect=2
        )

        self.assertIn("known-failure inventory refused", refused.stderr)
        self.assertEqual(before, self.controller_bytes())
        self.assertEqual(original, runbook_path.read_text(encoding="utf-8"))
        self.assertEqual({}, hexctl_module().pending_amendments(self.target))

    def test_capture_aware_semantic_comparison_refuses_before_pending_marker(self):
        self.prepare_capture(amendable=True)
        runbook_path = Path(self.target, "runbook.md")
        original = runbook_path.read_text(encoding="utf-8")
        candidate = self.write(
            "runbook-candidate.md",
            original
            + self.runbook_amendment(
                "Step 1: entry holds; exit holds.",
                touched="Step 1.",
            ),
        )
        controller = hexctl_module()
        drifted = json.loads(
            json.dumps(
                self.state()["receipts"]["runbook"]["known_failure_inventory"]
            )
        )
        drifted["no_known_findings"]["consuming_step"] = 2
        drifted["study_sha256"] = self.state()["receipts"]["study"]["sha256"]
        drifted["runbook_sha256"] = hashlib.sha256(
            Path(self.target, candidate).read_bytes()
        ).hexdigest()
        drifted["inventory_sha256"] = hashlib.sha256(
            controller.canonical(
                {
                    "schema": controller.KNOWN_FAILURE_INVENTORY_SCHEMA,
                    "source_views": drifted["source_views"],
                    "findings": drifted["findings"],
                    "no_known_findings": drifted["no_known_findings"],
                }
            ).encode()
        ).hexdigest()
        controller._validate_known_failure_capture(drifted)
        before = self.controller_bytes()

        with (
            mock.patch.object(
                controller, "_load_checked_inventory", return_value=drifted
            ),
            redirect_stderr(io.StringIO()) as errors,
            self.assertRaises(SystemExit) as refused,
        ):
            controller.cmd_amend_runbook(
                argparse.Namespace(
                    dir=self.target,
                    artifact=str(Path(self.target, candidate)),
                )
            )

        self.assertEqual(2, refused.exception.code)
        self.assertIn("inventory semantics changed", errors.getvalue())
        self.assertEqual(before, self.controller_bytes())
        self.assertEqual(original, runbook_path.read_text(encoding="utf-8"))
        self.assertEqual({}, controller.pending_amendments(self.target))

    def test_partial_assignment_surface_refuses_runbook_receipt(self):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Partial\n\n"
            "**Exit.** Incomplete.\n"
            "Known-failure assignment: `kf-453-02` -> Step 1\n",
        )
        steps = self.write("steps.json", '["Partial"]')
        before = self.controller_bytes()

        refused = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )

        self.assertIn("K001", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_inventory_surface_in_runbook_refuses_without_controller_mutation(self):
        self.init()
        study = self.write("study.md", "# Study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Misplaced\n\n"
            "```known-failure-inventory\n{}\n```\n",
        )
        steps = self.write("steps.json", '["Misplaced"]')
        before = self.controller_bytes()

        refused = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )

        self.assertIn("K001", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_assignment_surface_in_study_refuses_without_controller_mutation(self):
        self.init()
        study = self.write(
            "study.md",
            "# Study\n\nKnown-failure assignment: `kf-453-02` -> Step 1\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Misplaced\n\n**Goal.** Refuse.\n",
        )
        steps = self.write("steps.json", '["Misplaced"]')
        before = self.controller_bytes()

        refused = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )

        self.assertIn("K001", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_absent_surfaces_retain_the_legacy_implementation_path(self):
        self.prepare_legacy_run()

        state = self.state()
        self.assertEqual("implement", self.next_json()["do"])
        self.assertNotIn(
            "known_failure_inventory", state["receipts"]["runbook"]
        )
        self.assertNotIn("inoculate", state["steps"][0]["receipts"])

    def test_legacy_study_amendment_refuses_a_partial_inventory_surface(self):
        self.prepare_amendable_legacy_run()
        study_path = Path(self.target, "study.md")
        original = study_path.read_text(encoding="utf-8")
        candidate = self.write(
            "study-candidate.md",
            original
            + self.amendment(
                "Step 1: entry holds; exit holds.",
                what=(
                    "The attempted inventory follows.\n\n"
                    "```known-failure-inventory\n{}\n```\n"
                ),
                touched="Step 1.",
            ),
        )
        before = self.controller_bytes()

        refused = self.run_ctl(
            "amend", "study", "--artifact", candidate, expect=2
        )

        self.assertIn("known-failure inventory refused", refused.stderr)
        self.assertEqual(before, self.controller_bytes())
        self.assertEqual(original, study_path.read_text(encoding="utf-8"))
        self.assertEqual({}, hexctl_module().pending_amendments(self.target))

    def test_legacy_study_amendment_cannot_retrofit_a_clean_capture(self):
        self.prepare_amendable_legacy_run()
        source_path = "audit/rounds/legacy-source.md"
        source = "legacy source\n"
        source_sha256 = hashlib.sha256(source.encode()).hexdigest()
        view_path = "audit/rounds/legacy-source.synopsis.md"
        view = (
            "Synopsis schema=fiat-audit-synopsis/v1 | "
            f"source={source_path} | source_sha256={source_sha256} | h2_count=0\n"
        )
        view_sha256 = hashlib.sha256(view.encode()).hexdigest()
        self.write(source_path, source)
        self.write(view_path, view)
        inventory = {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": [
                {
                    "id": "legacy-source",
                    "path": view_path,
                    "source_sha256": source_sha256,
                    "view_sha256": view_sha256,
                }
            ],
            "findings": [],
            "no_known_findings": {
                "source_views": [
                    {
                        "id": "legacy-source",
                        "source_sha256": source_sha256,
                        "view_sha256": view_sha256,
                    }
                ],
                "consuming_step": 1,
                "surveyor_assertion": "no-known-findings",
            },
        }
        study_path = Path(self.target, "study.md")
        original = study_path.read_text(encoding="utf-8")
        candidate = self.write(
            "study-candidate.md",
            original
            + self.amendment(
                "Step 1: entry holds; exit holds.",
                what=(
                    "The complete inventory follows.\n\n"
                    "```known-failure-inventory\n"
                    + json.dumps(inventory, indent=2)
                    + "\n```\n"
                ),
                touched="Step 1.",
            ),
        )
        before = self.controller_bytes()

        refused = self.run_ctl(
            "amend", "study", "--artifact", candidate, expect=2
        )

        self.assertIn("cannot retrofit a known-failure capture", refused.stderr)
        self.assertEqual(before, self.controller_bytes())
        self.assertEqual(original, study_path.read_text(encoding="utf-8"))
        self.assertEqual({}, hexctl_module().pending_amendments(self.target))

    def test_explicit_null_capture_is_not_accepted_as_legacy(self):
        self.prepare_legacy_run()
        state = self.state()
        state["receipts"]["runbook"]["known_failure_inventory"] = None
        self.rewrite_last_controller_state(
            state,
            mutate_event=lambda data: data.update(
                {"known_failure_inventory": None}
            ),
        )

        refused = self.run_ctl("verify", expect=1)

        self.assertIn("receipted known-failure capture", refused.stderr)
        self.assertIn("unsupported field set", refused.stderr)

    def test_legacy_step_refuses_an_invented_inoculation_parent(self):
        self.prepare_legacy_run()
        state = self.state()
        state["steps"][0]["inoculation_parent"] = self.fake_sha("invented-parent")
        self.rewrite_last_controller_state(state)

        refused = self.run_ctl("verify", expect=1)

        self.assertIn("legacy Step carries invented inoculation state", refused.stderr)

    def test_legacy_step_refuses_an_explicit_null_inoculation_receipt(self):
        self.prepare_legacy_run()
        state = self.state()
        state["steps"][0]["receipts"]["inoculate"] = None
        self.rewrite_last_controller_state(state)

        refused = self.run_ctl("verify", expect=1)

        self.assertIn("legacy Step carries invented inoculation state", refused.stderr)

    def test_legacy_step_refuses_an_invented_inoculation_phase(self):
        self.prepare_legacy_run()
        state = self.state()
        state["steps"][0]["phase"] = "inoculate"
        self.rewrite_last_controller_state(state)

        refused = self.run_ctl("verify", expect=1)

        self.assertIn("legacy Step carries invented inoculation state", refused.stderr)
