"""Lifecycle checks for source-bound inoculation before implementation."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
from contextlib import redirect_stderr
from unittest import mock

try:
    from .test_hexctl import HexctlCase, hexctl_module
except ImportError:
    from test_hexctl import HexctlCase, hexctl_module


class InoculationLifecycleTests(HexctlCase):
    NO_KNOWN_FIXTURE = (
        Path(__file__).parent / "fixtures/issue-453/no-known-findings.json"
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

    def test_assigned_declaration_without_manifests_refuses_unchanged(self):
        self.prepare_capture(assigned=True)
        self.write(".hexaemeron/checkpoints/probe", "checkpoint bytes\n")
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("guard_manifests is empty", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_zero_assigned_record_receipts_the_closed_shape(self):
        directive, _ = self.prepare_capture()
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

    def test_verify_binds_the_inoculation_receipt_to_its_ledger_event(self):
        self.prepare_capture()
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
        self.prepare_capture(assigned=True, assigned_step=2)
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
        self.prepare_capture()
        self.write_no_known_findings(
            mutate=lambda record: record.update({"unsupported": True})
        )
        before = self.controller_bytes()

        refused = self.run_ctl("done", "inoculate", expect=2)

        self.assertIn("does not match", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_duplicate_inoculation_receipt_refuses_unchanged(self):
        self.prepare_capture()
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
        _, source_path = self.prepare_capture()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        before = self.controller_bytes()
        self.write(source_path, "changed after inoculation receipt\n")

        refused = self.run_ctl("next", expect=2)

        self.assertIn("K005", refused.stderr)
        self.assertEqual(before, self.controller_bytes())

    def test_post_receipt_parent_drift_refuses_implementation_delegation(self):
        directive, _ = self.prepare_capture()
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
        self.prepare_capture()
        self.write_no_known_findings()
        self.run_ctl("done", "inoculate")
        directive = self.next_json()
        state = self.state()
        step = state["steps"][0]
        capture = state["receipts"]["runbook"]["known_failure_inventory"]
        parent = step["receipts"]["inoculate"]["step_parent"]
        branch = self.step_branch(1, state)
        head = "b" * 40
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
        self.prepare_capture(amendable=True)
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
