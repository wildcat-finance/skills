"""End-to-end tests for hexctl, run through the CLI the way the skill uses it.

The fixture these run on -- `HexctlCase`, its fake delivery tools, and the
constants a receipt is shaped from -- lives in `hexctl_harness`. It was moved
there so this file's bounded-read budget is spent on test law rather than on the
harness under it. The names are re-exported here because sibling modules import
them from this module and the fixture is still, to them, where the tests are.
"""

# Nothing below is safe to drop for looking unused here. The five sibling
# `*_cases.py` modules carry no imports of their own: each builder calls
# `globals().update(context)` on the namespace this module passes it, so every
# name its test bodies resolve is one of these. ExitStack, BytesIO and
# TextIOWrapper have no reader in this file and sixteen subtests in
# audit_record_schema_cases fail with NameError without them.
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

try:
    from .hexctl_harness import (
        AUDIT_FILTER,
        AUDIT_SYNOPSIS,
        COMPLETE_STUDY,
        HERE,
        HEXCTL,
        LINTS_CLEAN,
        PROTASIS,
        SUITE,
        HexctlCase,
        OriginCheckoutMixin,
        audit_synopsis_module,
        hexctl_module,
        make_origin_checkout,
        protasis_module,
        run_target,
    )
except ImportError:
    from hexctl_harness import (
        AUDIT_FILTER,
        AUDIT_SYNOPSIS,
        COMPLETE_STUDY,
        HERE,
        HEXCTL,
        LINTS_CLEAN,
        PROTASIS,
        SUITE,
        HexctlCase,
        OriginCheckoutMixin,
        audit_synopsis_module,
        hexctl_module,
        make_origin_checkout,
        protasis_module,
        run_target,
    )


class TestLifecycle(HexctlCase):
    def test_init_creates_state_ledger_and_gitignore(self):
        self.init()
        root = os.path.join(self.target, ".hexaemeron")
        self.assertTrue(os.path.exists(os.path.join(root, "state.json")))
        self.assertTrue(os.path.exists(os.path.join(root, "ledger.jsonl")))
        with open(os.path.join(root, ".gitignore")) as fh:
            self.assertEqual(fh.read().strip(), "*")

    def test_init_twice_fails(self):
        self.init()
        proc = self.run_ctl("init", "--topic", "again", expect=2)
        self.assertIn("already exists", proc.stderr)

    def test_next_initial_is_study(self):
        self.init("widget factory")
        out = self.next_json()
        self.assertEqual(out["do"], "study")
        self.assertEqual(out["topic"], "widget factory")

    def test_done_out_of_order_rejected(self):
        self.init()
        rb = self.write("runbook.md")
        steps = self.write("steps.json", '["a"]')
        proc = self.run_ctl("done", "runbook", "--artifact", rb,
                            "--steps-file", steps, expect=2)
        self.assertIn("out of order", proc.stderr)

    def test_study_requires_existing_artifact(self):
        self.init()
        proc = self.run_ctl("done", "study", "--artifact", "missing.md",
                            expect=2)
        self.assertIn("not found", proc.stderr)

    def test_runbook_registers_steps_and_opens_first(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study)
        rb = self.write(
            "runbook.md",
            "## Step 1: Scaffold\n\n**Goal.** Scaffold.\n\n"
            "## Step 2: Core\n\n**Goal.** Core.\n",
        )
        steps = self.write("steps.json",
                           json.dumps(["Scaffold", {"title": "Core"}]))
        self.run_ctl("done", "runbook", "--artifact", rb, "--steps-file", steps)
        out = self.next_json()
        self.assertEqual(out["do"], "implement")
        self.assertEqual(out["step"], 1)
        self.assertEqual(out["title"], "Scaffold")


class TestDesignEvidenceLifecycle(HexctlCase):
    def controller_bytes(self):
        root = os.path.join(self.target, ".hexaemeron")
        return tuple(
            Path(os.path.join(root, name)).read_bytes()
            for name in ("state.json", "ledger.jsonl")
        )

    def record(self):
        path = os.path.join(self.target, ".hexaemeron", "design-evidence.json")
        with open(path, encoding="utf-8") as handle:
            return path, json.load(handle)

    def write_record(self, path, record):
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(record, handle, indent=2, sort_keys=True)
            handle.write("\n")

    def study(self):
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\none | boundary | check\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        return study

    def test_study_lock_requires_the_fixed_checked_record_without_mutation(self):
        self.init()
        os.unlink(os.path.join(self.target, ".hexaemeron", "design-evidence.json"))
        before = self.controller_bytes()
        study = self.write("study.md", "# Study\n")
        refused = self.run_ctl(
            "done", "study", "--artifact", study, expect=2
        )
        self.assertIn("design-evidence artefact is unavailable", refused.stderr)
        self.assertEqual(self.controller_bytes(), before)

    def test_selection_pending_names_the_exact_recovery_and_cannot_lock(self):
        self.init()
        path, record = self.record()
        result = next(
            item for item in record["results"]
            if item["candidate"] == "bounded" and item["criterion"] == "peak-space"
        )
        result.clear()
        result.update({
            "candidate": "bounded",
            "criterion": "peak-space",
            "state": "pending",
            "resolver": "python3 measure-space.py",
            "report": "design-reports/bounded-peak-space-later.json",
            "blocks": "design-lock",
        })
        self.write_record(path, record)
        before = self.controller_bytes()
        study = self.write("study.md", "# Study\n")
        refused = self.run_ctl(
            "done", "study", "--artifact", study, expect=2
        )
        self.assertIn("D007", refused.stderr)
        self.assertIn("python3 measure-space.py", refused.stderr)
        self.assertEqual(self.controller_bytes(), before)

    def test_runbook_must_bind_the_exact_design_lock(self):
        self.init()
        self.study()
        self.auto_design_lock = False
        body = "# Runbook\n\n## Step 1: Core\n\n**Goal.** Core.\n"
        runbook = self.write("runbook.md", body)
        steps = self.write("steps.json", '["Core"]')
        before = self.controller_bytes()
        missing = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("requires a design-lock block", missing.stderr)
        self.assertEqual(self.controller_bytes(), before)

        wrong = self.design_lock_block().replace(
            self.state()["receipts"]["study"]["design_evidence"]["sha256"],
            "f" * 64,
        )
        self.write("runbook.md", wrong + "\n" + body)
        mismatch = self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps,
            expect=2,
        )
        self.assertIn("does not match the receipted", mismatch.stderr)
        self.assertEqual(self.controller_bytes(), before)

        self.write("runbook.md", self.design_lock_block() + "\n" + body)
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        receipt = self.state()["receipts"]["runbook"]
        self.assertEqual(receipt["design_lock"]["candidate"], "bounded")

    def test_pending_conformance_blocks_only_its_named_step(self):
        self.init()
        path, record = self.record()
        criterion = next(
            item for item in record["criteria"] if item["id"] == "restart-safe"
        )
        criterion["stage"] = "conformance"
        criterion["blocks"] = "step:2"
        result = next(
            item for item in record["results"]
            if item["candidate"] == "bounded" and item["criterion"] == "restart-safe"
        )
        result.clear()
        result.update({
            "candidate": "bounded",
            "criterion": "restart-safe",
            "state": "pending",
            "resolver": "python3 prove-restart.py",
            "report": "design-reports/bounded-restart-later.json",
            "blocks": "step:2",
        })
        self.write_record(path, record)
        study = self.study()
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Core\n\n**Goal.** Core.\n\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n",
        )
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
        for step in state["steps"]:
            self.git("branch", self.step_branch(step["n"], state))
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc1",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        before = self.controller_bytes()
        push_args = (
            "done", "push", "--pr-url",
            "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", self.fake_sha("head1"),
            "--pr-base", self.step_base(1),
        )
        refused = self.run_ctl(*push_args, expect=2)
        self.assertIn("D008", refused.stderr)
        self.assertIn("bounded/restart-safe", refused.stderr)
        self.assertEqual(self.controller_bytes(), before)

        payload = {
            "schema": "protasis-design-report/v1",
            "candidate": "bounded",
            "criterion": "restart-safe",
            "value": True,
            "unit": "boolean",
            "command": "python3 prove-restart.py",
            "exit": 0,
        }
        report = os.path.join(
            self.target, ".hexaemeron", "design-reports",
            "bounded-restart-later.json",
        )
        with open(report, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, sort_keys=True)
            handle.write("\n")
        self.run_ctl(*push_args)
        state = self.state()
        self.assertEqual(state["current_step"], 2)
        transition = state["receipts"]["study"]["design_evidence"]["transitions"][-1]
        self.assertEqual(transition["transition"], "step:2")
        self.assertEqual(
            [(item["candidate"], item["criterion"]) for item in transition["reports"]],
            [("bounded", "restart-safe")],
        )

    def test_verify_replays_report_receipts_and_detects_tampering(self):
        self.to_steps(("Core",))
        self.run_ctl("verify")
        report = os.path.join(
            self.target, ".hexaemeron", "design-reports", "bounded-warm-time.json"
        )
        with open(report, "a", encoding="utf-8") as handle:
            handle.write(" ")
        refused = self.run_ctl("verify", expect=2)
        self.assertIn("report digest does not match", refused.stderr)

    def test_legacy_state_continues_without_fabricated_design_evidence(self):
        self.init()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state.pop("contracts")
        hexctl_module().commit(
            self.target, state, "fixture:legacy-design-contract", {}
        )
        os.unlink(os.path.join(self.target, ".hexaemeron", "design-evidence.json"))
        study = self.write("study.md", "# Legacy study\n")
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: Core\n\n**Goal.** Core.\n"
        )
        steps = self.write("steps.json", '["Core"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        self.assertNotIn(
            "design_evidence", self.state()["receipts"]["study"]
        )


class TestDelegationPackets(HexctlCase):
    def assert_packet(self, directive, agent, fields):
        self.assertEqual(directive["agent"], agent)
        self.assertEqual(set(directive["brief"]), set(fields))
        self.assertRegex(directive["state_sha256"], r"^[0-9a-f]{64}$")

    def test_surveyor_packet_is_total_and_reproducible(self):
        self.init("packet work")
        first = self.run_ctl("next").stdout
        second = self.run_ctl("next").stdout
        self.assertEqual(first, second)
        out = json.loads(first)
        self.assert_packet(
            out,
            "surveyor",
            ("topic", "target_dir", "base_ref", "output_path", "design_output_path"),
        )
        self.assertEqual(out["brief"]["topic"], "packet work")
        self.assertEqual(out["brief"]["target_dir"], os.path.realpath(self.target))
        self.assertEqual(out["brief"]["base_ref"], "main")
        self.assertEqual(
            out["brief"]["output_path"],
            os.path.realpath(os.path.join(self.target, ".hexaemeron", "study.md")),
        )
        self.assertEqual(
            out["brief"]["design_output_path"],
            os.path.realpath(
                os.path.join(self.target, ".hexaemeron", "design-evidence.json")
            ),
        )
        self.assertEqual(out["state_sha256"], hashlib.sha256(
            json.dumps(self.state(), sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest())

    def test_all_four_role_briefs_and_inline_nulls(self):
        self.init()
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "one | boundary | check\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        self.assertEqual(self.next_json()["agent"], None)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n## Step 1: Core\n\n**Goal.** Build.\n",
        )
        steps = self.write("steps.json", '["Core"]')
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "base")
        state = self.state()
        self.git("branch", self.step_branch(1, state))

        mason = self.next_json()
        self.assert_packet(
            mason,
            "mason",
            ("runbook_step", "branch", "branch_from", "design_evidence"),
        )
        self.assertEqual(
            set(mason["brief"]["design_evidence"]),
            {"schema", "path", "sha256", "selected"},
        )
        source = mason["brief"]["runbook_step"]
        self.assertEqual(
            set(source),
            {
                "markdown", "baseline_markdown", "baseline_sha256",
                "amendments", "effective_sha256", "path", "sha256",
                "number", "title",
            },
        )
        self.assertEqual(source["baseline_markdown"], source["markdown"])
        self.assertEqual(source["amendments"], [])
        self.assertEqual(source["number"], 1)
        self.assertEqual(source["title"], "Core")
        self.assertTrue(source["markdown"].startswith("## Step 1: Core\n"))

        self.run_ctl("done", "implement", "--branch", self.step_branch(1),
                     "--commit", "abc")
        inline = self.next_json()
        self.assertEqual((inline["do"], inline["agent"], inline["brief"]),
                         ("resolve-security-suite", None, {}))
        self.run_ctl("record", "security_suite", SUITE)
        warden = self.next_json()
        self.assert_packet(
            warden,
            "warden",
            ("step_branch", "stacked_branch", "security_suite", "plugin_root",
             "audit_log_path", "round", "audit_filter", "risk_register",
             "runbook_step", "design_evidence"),
        )
        risk = warden["brief"]["risk_register"]
        self.assertEqual(set(risk), {"markdown", "path", "sha256"})
        self.assertEqual(risk["markdown"],
                         "```risk-register\none | boundary | check\n```\n")
        self.assertEqual(warden["brief"]["runbook_step"], source)

        self.run_ctl("audit-round", "--findings", "0")
        closed = self.next_json()
        self.assertEqual((closed["do"], closed["agent"], closed["brief"]),
                         ("close-audit", None, {}))
        self.run_ctl("done", "audit")
        scribe = self.next_json()
        self.assert_packet(
            scribe, "scribe", ("files", "pr_base", "pr_draft_path", "plugin_root")
        )
        # The harness commits the audit records on the run branch, so they
        # reach this step's diff as deletions.  A removed path carries no prose
        # to rewrite and the packet no longer names one; the positive case is
        # test_hexctl_prose_packet_bounds.
        self.assertEqual(scribe["brief"]["files"], [])
        self.run_ctl("done", "prose", "--files", "1", "--skills",
                     "hexaemeron:imprimatur,hexaemeron:vulgate")
        push = self.next_json()
        self.assertEqual((push["do"], push["agent"], push["brief"]),
                         ("push", None, {}))
        self.run_ctl("done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
                     "--head-commit", "abc", "--pr-base", self.step_base(1))
        merge = self.next_json()
        self.assertEqual((merge["do"], merge["agent"], merge["brief"]),
                         ("merge-step", None, {}))
        self.run_ctl("done", "merge-step", "--step", "1", "--merge-commit", "1" * 40)
        integrate = self.next_json()
        self.assertEqual((integrate["do"], integrate["agent"], integrate["brief"]),
                         ("integrate", None, {}))
        self.write_run_pr()
        self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                     "--merge-commit", "f" * 40)
        done = self.next_json()
        self.assertEqual((done["do"], done["agent"], done["brief"]),
                         ("done", None, {}))

    def test_receipts_bind_bytes_and_mutation_refuses_packets(self):
        self.to_steps(("Core",))
        state = self.state()
        for name in ("study", "runbook"):
            receipt = state["receipts"][name]
            self.assertRegex(receipt["sha256"], r"^[0-9a-f]{64}$")
        self.write("runbook.md", "# changed\n")
        proc = self.run_ctl("next", expect=2)
        self.assertIn("runbook artefact digest changed", proc.stderr)

    def test_amend_study_command_is_registered(self):
        self.to_steps(("Core",))
        parser = hexctl_module().build_parser()
        args = parser.parse_args(
            ["--dir", self.dir, "amend", "study", "--artifact", "study.md"]
        )
        self.assertEqual(args.fn.__name__, "cmd_amend_study")

    def test_amend_study_replaces_the_digest_refusal_before_next(self):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read()
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            "## Step 1: Core\n\n**Goal.** Core.\n\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n",
        )
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        amendment = (
            "\n### Amendment -- 2026-08-22\n\n"
            "**What changed.** The fixture assumption was corrected.\n"
            "**Why.** The receipted baseline disproved it.\n"
            "**Steps touched.** Steps 1 and 2.\n"
            "**Still holding.** Step 1: entry holds; exit holds. "
            "Step 2: entry holds; exit holds.\n"
        )
        candidate = self.write("candidate.md", original + amendment)
        self.write("study.md", original + amendment)

        refused = self.run_ctl("next", expect=2)
        self.assertIn("study artefact digest changed", refused.stderr)

        self.run_ctl("amend", "study", "--artifact", candidate)
        packet = self.next_json()
        self.assertEqual((packet["do"], packet["agent"]), ("implement", "mason"))

    def test_risk_block_drift_and_ambiguous_step_refuse(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.write("study.md", "# changed\n")
        proc = self.run_ctl("next", expect=2)
        self.assertIn("study artefact digest changed", proc.stderr)

        other = HexctlCase(methodName="runTest")
        other.setUp()
        try:
            other.init()
            study = other.write(
                "study.md", "```risk-register\none | boundary | check\n```\n"
            )
            other.run_ctl("done", "study", "--artifact", study)
            runbook = other.write(
                "runbook.md",
                "## Step 1: Core\n\nA.\n\n## Step 1: Core\n\nB.\n",
            )
            steps = other.write("steps.json", '["Core"]')
            other.run_ctl("done", "runbook", "--artifact", runbook,
                          "--steps-file", steps)
            proc = other.run_ctl("next", expect=2)
            self.assertIn("ambiguous runbook step", proc.stderr)
        finally:
            other.tearDown()

    def test_fenced_heading_and_register_decoys_are_not_selectors(self):
        self.init()
        study = self.write(
            "study.md",
            "~~~markdown\n```risk-register\nfake | fake | fake\n```\n~~~\n"
            "```risk-register\nreal | boundary | check\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "~~~markdown\n## Step 1: Core\n\nDecoy.\n~~~\n"
            "## Step 1: Core\n\n**Goal.** Real.\n",
        )
        steps = self.write("steps.json", '["Core"]')
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)
        mason = self.next_json()
        self.assertEqual(
            mason["brief"]["runbook_step"]["markdown"],
            "## Step 1: Core\n\n**Goal.** Real.\n",
        )
        self.run_ctl("done", "implement", "--branch", self.step_branch(1),
                     "--commit", "abc")
        self.run_ctl("record", "security_suite", SUITE)
        warden = self.next_json()
        self.assertEqual(
            warden["brief"]["risk_register"]["markdown"],
            "```risk-register\nreal | boundary | check\n```\n",
        )

    def test_source_selectors_accept_the_protasis_spacing_grammar(self):
        controller = hexctl_module()
        protasis = protasis_module()
        heading = "## Step 1: Core   "
        self.assertIsNotNone(protasis.STEP.fullmatch(heading))
        step_source = {
            "text": heading + "\n\n**Goal.** Real.\n",
            "path": "/target/runbook.md",
            "sha256": "a" * 64,
        }
        selected = controller.source_runbook_step(
            step_source, {"n": 1, "title": "Core"}
        )
        self.assertEqual(selected["markdown"], heading + "\n\n**Goal.** Real.\n")

        register_lines = ["``` risk-register", "one | boundary | check", "```"]
        self.assertEqual(
            protasis._register_lines(register_lines, 1),
            [(2, "one | boundary | check")],
        )
        risk_source = {
            "text": "\n".join(register_lines) + "\n",
            "path": "/target/study.md",
            "sha256": "b" * 64,
        }
        selected = controller.source_risk_register(risk_source)
        self.assertEqual(selected["markdown"], "\n".join(register_lines) + "\n")

    def test_warden_refuses_an_invalid_assembled_stacked_branch(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.record_legacy_config("audit.stacked_suffix", " bad")
        proc = self.run_ctl("next", expect=2)
        self.assertIn("stacked_branch is not a valid Git branch", proc.stderr)

    def test_path_and_source_byte_caps_refuse(self):
        self.init()
        outside = tempfile.NamedTemporaryFile("w", delete=False)
        try:
            outside.write("outside\n")
            outside.close()
            proc = self.run_ctl("done", "study", "--artifact", outside.name,
                                expect=2)
            self.assertIn("escapes target directory", proc.stderr)
        finally:
            os.unlink(outside.name)

        large = self.write("large.md", "x" * (2 * 1024 * 1024 + 1))
        proc = self.run_ctl("done", "study", "--artifact", large, expect=2)
        self.assertIn("exceeds 2097152-byte cap", proc.stderr)

    def test_legacy_receipts_do_not_claim_source_binding(self):
        self.to_steps(("Core",))
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["runbook"].pop("sha256")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        out = self.next_json()
        self.assertEqual((out["agent"], out["brief"]), (None, {}))

    def test_missing_receipted_source_refuses(self):
        self.to_steps(("Core",))
        os.unlink(os.path.join(self.target, "runbook.md"))
        proc = self.run_ctl("next", expect=2)
        self.assertIn("runbook artefact is not a regular file", proc.stderr)

    def test_scribe_diff_is_sorted_and_holds_only_the_retained_paths(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        branch = self.step_branch(1)
        self.git("checkout", branch)
        for name in ("zeta.md", "alpha.md"):
            self.write(name, name)
        self.git("add", "zeta.md", "alpha.md")
        self.git("commit", "-m", "step")
        # The two audit records sit on the run branch rather than this one, so
        # they arrive as deletions and the packet drops them.  The ceiling that
        # remains is PROSE_PATHS_MAX, exercised over a mocked path list in
        # test_hexctl_prose_packet_bounds rather than by writing four thousand
        # files through this fixture.
        self.assertEqual(
            self.next_json()["brief"]["files"],
            ["alpha.md", "zeta.md"],
        )

    def test_git_output_and_returned_path_caps_refuse(self):
        module = hexctl_module()
        fake_bin = os.path.join(self.dir, "fake-bin")
        os.makedirs(fake_bin)
        fake_git = os.path.join(fake_bin, "git")
        with open(fake_git, "w", encoding="utf-8") as handle:
            handle.write("#!/bin/sh\nprintf '../escape.md\\0'\n")
        os.chmod(fake_git, 0o755)
        path = fake_bin + os.pathsep + os.environ.get("PATH", "")
        error = StringIO()
        with mock.patch.dict(os.environ, {"PATH": path}), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.scribe_files(self.dir, "base", "branch")
        self.assertIn("escapes target directory", error.getvalue())

        with open(fake_git, "w", encoding="utf-8") as handle:
            handle.write(
                "#!/usr/bin/env python3\n"
                "import sys\n"
                f"sys.stdout.buffer.write(b'x' * {2 * 1024 * 1024 + 1})\n"
            )
        error = StringIO()
        with mock.patch.dict(os.environ, {"PATH": path}), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.bounded_git(self.dir, ["diff"])
        self.assertIn("2097152-byte output cap", error.getvalue())


    def test_brief_out_diverts_the_body_and_leaves_the_directive_readable(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        inline = self.next_json()
        self.assertTrue(inline["brief"])
        diverted = json.loads(
            self.run_ctl("next", "--brief-out", ".hexaemeron/brief.json").stdout
        )
        self.assertEqual(diverted["brief"], {})
        self.assertEqual(
            diverted["brief_path"],
            os.path.realpath(os.path.join(self.target, ".hexaemeron", "brief.json")),
        )
        with open(diverted["brief_path"], encoding="utf-8") as handle:
            self.assertEqual(json.load(handle), inline["brief"])
        for key in ("do", "agent", "step", "round", "state_sha256", "audit_filter"):
            self.assertEqual(diverted.get(key), inline.get(key))

    def test_brief_out_refuses_a_path_outside_the_target(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("next", "--brief-out", "../escape.json", expect=2)

    def test_brief_out_leaves_an_inline_directive_alone(self):
        self.init("packet work")
        self.run_ctl("halt", "--reason", "waiting on the user")
        out = json.loads(
            self.run_ctl("next", "--brief-out", ".hexaemeron/brief.json").stdout
        )
        self.assertEqual(out["do"], "halted")
        self.assertNotIn("brief_path", out)
        self.assertFalse(
            os.path.exists(os.path.join(self.target, ".hexaemeron", "brief.json"))
        )

    def test_status_field_returns_one_value_not_the_state(self):
        self.to_audit()
        whole = json.loads(self.run_ctl("status", "--json").stdout)
        one = self.run_ctl("status", "--field", "observation_run_id").stdout
        self.assertEqual(json.loads(one), whole["observation_run_id"])
        self.assertLess(len(one), len(json.dumps(whole)))
        for absent in ("steps", "receipts", "config"):
            self.assertNotIn(absent, one)

    def test_status_field_walks_a_dotted_path(self):
        self.to_audit()
        whole = json.loads(self.run_ctl("status", "--json").stdout)
        out = self.run_ctl("status", "--field", "config.audit.max_rounds").stdout
        self.assertEqual(json.loads(out), whole["config"]["audit"]["max_rounds"])

    def test_status_field_refuses_an_unknown_path(self):
        self.to_audit()
        self.run_ctl("status", "--field", "config.audit.nope", expect=2)
        self.run_ctl("status", "--field", "not_a_key", expect=2)

    def test_status_field_and_json_are_mutually_exclusive(self):
        self.to_audit()
        self.run_ctl("status", "--json", "--field", "observation_run_id", expect=2)

class XRayReuseStateSeparationTests(HexctlCase):
    FORBIDDEN_FIELDS = frozenset(
        {
            "cache",
            "cache_key",
            "cache_path",
            "cache_payload",
            "cache_verdict",
            "preparation_entries",
            "reuse_cache",
            "reuse_candidate",
            "reuse_plan",
            "xray_reuse",
        }
    )
    FORBIDDEN_PAYLOAD_MARKERS = (
        "hexaemeron.xray.",
        "candidate_sha256",
        "dependency_digests",
        "reverse_invalidated",
        "source_sha256",
    )

    def field_names(self, value):
        if isinstance(value, dict):
            for key, nested in value.items():
                yield key
                yield from self.field_names(nested)
        elif isinstance(value, list):
            for nested in value:
                yield from self.field_names(nested)

    def assert_no_reuse_material(self, surface, value):
        present = self.FORBIDDEN_FIELDS.intersection(self.field_names(value))
        self.assertEqual(present, set(), f"{surface} gained reuse material")
        encoded = json.dumps(value, sort_keys=True)
        for marker in self.FORBIDDEN_PAYLOAD_MARKERS:
            self.assertNotIn(marker, encoded, f"{surface} gained reuse payload")

    def test_audit_directive_state_ledger_and_receipt_keep_existing_shapes(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        directive = self.next_json()

        self.run_ctl("audit-round", "--findings", "0")
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        with open(ledger_path, encoding="utf-8") as handle:
            ledger = [json.loads(line) for line in handle if line.strip()]
        receipt = state["steps"][0]["audit"]["rounds"][0]

        for name, value in (
            ("audit directive", directive),
            ("state", state),
            ("ledger", ledger),
            ("audit receipt", receipt),
        ):
            with self.subTest(surface=name):
                self.assert_no_reuse_material(name, value)


class TestStudyAmendments(HexctlCase):
    def test_temporary_git_repositories_demonstrate_holding_and_broken_runs(self):
        original = self.to_amendable_steps()
        self.git("init", "-b", "main")
        self.git("config", "--local", "commit.gpgsign", "false")
        self.git("config", "user.email", "tests@example.com")
        self.git("config", "user.name", "Hexctl Tests")
        self.git("add", "study.md", "runbook.md", "steps.json")
        self.git("commit", "-m", "temporary holding run")
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)
        self.run_ctl("amend", "study", "--artifact", candidate)
        state = self.state()
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_path, encoding="utf-8") as handle:
            ledger = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(state["receipts"]["study"]["sha256"],
                         hashlib.sha256(candidate_text.encode()).hexdigest())
        self.assertEqual(ledger[-1]["event"], "amend:study")
        self.assertEqual((self.next_json()["do"], self.next_json()["agent"]),
                         ("implement", "mason"))

        broken = HexctlCase(methodName="runTest")
        broken.setUp()
        try:
            original = broken.to_amendable_steps()
            broken.git("init", "-b", "main")
            broken.git("config", "--local", "commit.gpgsign", "false")
            broken.git("config", "user.email", "tests@example.com")
            broken.git("config", "user.name", "Hexctl Tests")
            broken.git("add", "study.md", "runbook.md", "steps.json")
            broken.git("commit", "-m", "temporary broken run")
            candidate = broken.write(
                "candidate.md",
                original + broken.amendment(
                    "Step 1: entry holds; exit broken. "
                    "Step 2: entry holds; exit holds."
                ),
            )
            broken.run_ctl("amend", "study", "--artifact", candidate)
            directive = broken.next_json()
            self.assertEqual((directive["do"], directive["agent"], directive["brief"]),
                             ("blocked", None, {}))
            self.assertIn("exit broken", directive["reason"])
        finally:
            broken.tearDown()

    def test_valid_append_records_digest_history_and_reconstructs_the_packet(self):
        original = self.to_amendable_steps()
        prior = hashlib.sha256(original.encode()).hexdigest()
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)

        result = self.run_ctl("amend", "study", "--artifact", candidate)
        state = self.state()
        receipt = state["receipts"]["study"]
        amendment = receipt["amendments"][0]
        new = hashlib.sha256(candidate_text.encode()).hexdigest()
        suffix = candidate_text[len(original):].encode()

        self.assertEqual(receipt["sha256"], new)
        self.assertEqual(amendment["prior_sha256"], prior)
        self.assertEqual(amendment["new_sha256"], new)
        self.assertEqual(amendment["amendment_sha256"], hashlib.sha256(suffix).hexdigest())
        self.assertEqual(amendment["steps_touched"], [1, 2])
        self.assertEqual(
            amendment["step_verdicts"],
            [
                {"step": 1, "entry": "holds", "exit": "holds"},
                {"step": 2, "entry": "holds", "exit": "holds"},
            ],
        )
        self.assertIn(prior, result.stdout)
        self.assertIn(new, result.stdout)
        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), candidate_text)
        with open(os.path.join(self.target, ".hexaemeron", "ledger.jsonl"), encoding="utf-8") as handle:
            ledger = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(ledger[-1]["event"], "amend:study")
        self.assertEqual(ledger[-1]["data"], amendment)
        first = self.next_json()
        second = self.next_json()
        self.assertEqual(first, second)
        self.assertEqual((first["do"], first["agent"]), ("implement", "mason"))

    def test_broken_current_step_is_recorded_and_durably_blocks_work(self):
        original = self.to_amendable_steps()
        candidate = self.write(
            "candidate.md",
            original + self.amendment(
                "Step 1: entry broken; exit holds. "
                "Step 2: entry holds; exit holds."
            ),
        )
        result = self.run_ctl("amend", "study", "--artifact", candidate)
        self.assertIn("dependent work is blocked", result.stdout)
        blocked = self.next_json()
        self.assertEqual((blocked["do"], blocked["agent"], blocked["brief"]),
                         ("blocked", None, {}))
        self.assertRegex(blocked["amendment_sha256"], r"^[0-9a-f]{64}$")
        self.assertIn("runbook-repair transition", blocked["recovery"])
        proc = self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc", expect=2,
        )
        self.assertIn("study amendment blocks step 1", proc.stderr)
        self.assertIn("BLOCKED:", self.run_ctl("status").stdout)
        self.run_ctl("verify")

    def test_prefix_drift_refuses_without_mutating_any_durable_record(self):
        original = self.to_amendable_steps()
        state_before = self.state()
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger_path, "rb") as handle:
            ledger_before = handle.read()
        candidate = self.write("candidate.md", "changed\n" + original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("exact prefix", proc.stderr)
        self.assertEqual(self.state(), state_before)
        with open(ledger_path, "rb") as handle:
            self.assertEqual(handle.read(), ledger_before)
        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), original)

    def test_protasis_owns_shape_before_record_or_mutation(self):
        original = self.to_amendable_steps()
        paths = [Path(self.target, name) for name in (
            ".hexaemeron/state.json", ".hexaemeron/ledger.jsonl", "study.md"
        )]
        before = [path.read_bytes() for path in paths]
        why = "**Why.** The receipted baseline disproved it.\n"
        what = "**What changed.** The fixture assumption was corrected.\n"
        cases = {
            "invalid date": self.amendment(date="2026-02-30"),
            "missing field": self.amendment().replace(why, ""),
            "duplicate field": self.amendment().replace(
                why, "**Why.** First.\n**Why.** Second.\n"
            ),
            "empty field": self.amendment(what=""),
            "wrong order": self.amendment().replace(what + why, why + what),
        }
        for label, suffix in cases.items():
            with self.subTest(label=label):
                candidate = self.write("candidate.md", original + suffix)
                proc = self.run_ctl(
                    "amend", "study", "--artifact", candidate, expect=2
                )
                self.assertIn("Protasis rejected the amendment candidate", proc.stderr)

        module = hexctl_module()
        with (
            mock.patch.object(
                module,
                "_study_amendment_record",
                side_effect=AssertionError,
            ),
            redirect_stderr(StringIO()),
            self.assertRaises(SystemExit),
        ):
            module.cmd_amend_study(argparse.Namespace(
                dir=self.target, artifact=os.path.join(self.target, candidate)
            ))
        self.assertEqual([path.read_bytes() for path in paths], before)
        self.assertFalse(Path(self.target, ".hexaemeron/study-amendment-pending.json").exists())

    def test_every_unbuilt_step_gets_one_unambiguous_entry_and_exit_verdict(self):
        cases = {
            "missing": ("Step 1: entry holds; exit holds.", "missing verdict(s)"),
            "duplicate": (
                "Step 1: entry holds; exit holds. "
                "Step 1: entry holds; exit holds. "
                "Step 2: entry holds; exit holds.",
                "duplicate step verdict",
            ),
            "ambiguous": (
                "Step 1 probably holds. Step 2 should hold.", "only unambiguous"
            ),
            "unknown": (
                "Step 1: entry holds; exit holds. "
                "Step 2: entry holds; exit holds. "
                "Step 3: entry holds; exit holds.",
                "completed or unknown step",
            ),
        }
        for label, (verdicts, message) in cases.items():
            with self.subTest(label=label):
                other = HexctlCase(methodName="runTest")
                other.setUp()
                try:
                    original = other.to_amendable_steps()
                    candidate = other.write(
                        "candidate.md", original + other.amendment(verdicts)
                    )
                    proc = other.run_ctl(
                        "amend", "study", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                finally:
                    other.tearDown()

    def test_completed_step_cannot_be_touched_or_given_a_new_verdict(self):
        original = self.to_amendable_steps()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["steps"][0]["status"] = "done"
        state["steps"][0]["phase"] = "push"
        state["steps"][1]["status"] = "open"
        state["steps"][1]["phase"] = "implement"
        state["current_step"] = 2
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        candidate = self.write("candidate.md", original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("cannot rewrite completed step(s): [1]", proc.stderr)

    def test_wrong_phase_and_legacy_unbound_receipt_refuse(self):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read()
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        candidate = self.write("candidate.md", original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("only while build steps are active", proc.stderr)

        other = HexctlCase(methodName="runTest")
        other.setUp()
        try:
            original = other.to_amendable_steps()
            state_path = os.path.join(other.target, ".hexaemeron", "state.json")
            with open(state_path, encoding="utf-8") as handle:
                state = json.load(handle)
            state["receipts"]["study"].pop("sha256")
            with open(state_path, "w", encoding="utf-8") as handle:
                json.dump(state, handle)
            candidate = other.write("candidate.md", original + other.amendment())
            proc = other.run_ctl(
                "amend", "study", "--artifact", candidate, expect=2
            )
            self.assertIn("source-bound study receipt", proc.stderr)
        finally:
            other.tearDown()

    def test_candidate_path_and_size_bounds_refuse(self):
        original = self.to_amendable_steps()
        outside = tempfile.NamedTemporaryFile("w", delete=False)
        try:
            outside.write(original + self.amendment())
            outside.close()
            proc = self.run_ctl(
                "amend", "study", "--artifact", outside.name, expect=2
            )
            self.assertIn("escapes target directory", proc.stderr)
        finally:
            os.unlink(outside.name)

        large = self.write(
            "large.md", original + self.amendment() + "x" * (2 * 1024 * 1024)
        )
        proc = self.run_ctl("amend", "study", "--artifact", large, expect=2)
        self.assertIn("exceeds 2097152-byte cap", proc.stderr)

    def test_complete_candidate_must_pass_the_bundled_protasis_checker(self):
        self.to_steps(("Core", "Finish"))
        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            original = handle.read()
        candidate = self.write("candidate.md", original + self.amendment())
        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("Protasis rejected the amendment candidate", proc.stderr)
        self.assertNotIn("S001", proc.stderr)

    def test_live_controller_writer_blocks_amendment_mutation(self):
        original = self.to_amendable_steps()
        candidate = self.write("candidate.md", original + self.amendment())
        holder, _, release = self.start_lock_holder(command="cmd_record")
        try:
            proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=1)
            self.assertIn("another hexctl is holding this run", proc.stderr)
        finally:
            self.release_lock_holder(holder, release)

    def test_fenced_decoy_is_ignored_but_duplicate_block_and_trailing_section_refuse(self):
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            fixture = handle.read()
        decoy = fixture.replace(
            "## 1. Problem statement",
            "```markdown\n### Amendment -- 2026-01-01\n```\n\n"
            "## 1. Problem statement",
        )
        self.init()
        study = self.write("study.md", decoy)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md", "## Step 1: Core\n\n**Goal.** Core.\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n"
        )
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl("done", "runbook", "--artifact", runbook, "--steps-file", steps)
        candidate = self.write("candidate.md", decoy + self.amendment())
        self.run_ctl("amend", "study", "--artifact", candidate)

        for label, suffix, message in (
            ("duplicate", self.amendment() + self.amendment(), "more than one"),
            (
                "trailing",
                self.amendment() + "\n## Notes\n\nLater.\n",
                "Protasis rejected the amendment candidate",
            ),
        ):
            with self.subTest(label=label):
                other = HexctlCase(methodName="runTest")
                other.setUp()
                try:
                    original = other.to_amendable_steps()
                    candidate = other.write("candidate.md", original + suffix)
                    proc = other.run_ctl(
                        "amend", "study", "--artifact", candidate, expect=2
                    )
                    self.assertIn(message, proc.stderr)
                finally:
                    other.tearDown()

    def test_short_fence_cannot_expose_an_amendment_heading_inside_a_long_fence(self):
        self.init()
        with open(COMPLETE_STUDY, encoding="utf-8") as handle:
            original = handle.read() + "\n````markdown\n```\n"
        study = self.write("study.md", original)
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            "## Step 1: Core\n\n**Goal.** Core.\n\n"
            "## Step 2: Finish\n\n**Goal.** Finish.\n",
        )
        steps = self.write("steps.json", '["Core", "Finish"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        candidate = self.write("candidate.md", original + self.amendment())

        proc = self.run_ctl("amend", "study", "--artifact", candidate, expect=2)
        self.assertIn("exact prefix", proc.stderr)

    def test_interrupted_replacement_is_durable_pending_work_and_recovers(self):
        original = self.to_amendable_steps()
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)
        candidate_path = os.path.join(self.target, candidate)
        module = hexctl_module()

        with mock.patch.object(
            module,
            "commit",
            side_effect=KeyboardInterrupt(
                "simulated interruption after artefact replacement"
            ),
        ):
            with self.assertRaises(KeyboardInterrupt):
                module.cmd_amend_study(
                    argparse.Namespace(dir=self.target, artifact=candidate_path)
                )

        with open(os.path.join(self.target, "study.md"), encoding="utf-8") as handle:
            self.assertEqual(handle.read(), candidate_text)
        pending = os.path.join(
            self.target, ".hexaemeron", "study-amendment-pending.json"
        )
        self.assertTrue(os.path.isfile(pending))
        refused = self.run_ctl("verify", expect=2)
        self.assertIn("study amendment transaction is pending", refused.stderr)

        recovered = self.run_ctl(
            "amend", "study", "--artifact", os.path.join(self.target, "study.md")
        )
        self.assertIn("recovered", recovered.stdout)
        self.assertFalse(os.path.exists(pending))
        self.run_ctl("verify")
        self.assertEqual(
            self.state()["receipts"]["study"]["sha256"],
            hashlib.sha256(candidate_text.encode()).hexdigest(),
        )

    def test_recovery_completes_a_written_ledger_event_without_duplicating_it(self):
        original = self.to_amendable_steps()
        candidate_text = original + self.amendment()
        candidate = self.write("candidate.md", candidate_text)
        module = hexctl_module()

        with mock.patch.object(
            module,
            "save_state",
            side_effect=OSError("simulated interruption before state replacement"),
        ):
            with self.assertRaises(OSError):
                module.cmd_amend_study(
                    argparse.Namespace(
                        dir=self.target,
                        artifact=os.path.join(self.target, candidate),
                    )
                )

        recovered = self.run_ctl(
            "amend", "study", "--artifact", os.path.join(self.target, "study.md")
        )
        self.assertIn("recovered", recovered.stdout)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            events = [json.loads(line)["event"] for line in handle if line.strip()]
        self.assertEqual(events.count("amend:study"), 1)
        self.run_ctl("verify")

    def test_same_path_candidate_and_multiple_holding_amendments_are_supported(self):
        original = self.to_amendable_steps()
        first_text = original + self.amendment()
        self.write("study.md", first_text)
        self.run_ctl("amend", "study", "--artifact", "study.md")
        second_text = first_text + self.amendment(
            date="2026-08-23", what="A second baseline fact changed."
        )
        second = self.write("second.md", second_text)
        self.run_ctl("amend", "study", "--artifact", second)
        history = self.state()["receipts"]["study"]["amendments"]
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["prior_sha256"], history[0]["new_sha256"])

    def test_post_amendment_drift_refuses_next_and_verify(self):
        original = self.to_amendable_steps()
        candidate = self.write("candidate.md", original + self.amendment())
        self.run_ctl("amend", "study", "--artifact", candidate)
        self.write("study.md", original + self.amendment() + "drift\n")
        for command in (("next",), ("verify",)):
            with self.subTest(command=command[0]):
                proc = self.run_ctl(*command, expect=2)
                self.assertIn("study artefact digest changed", proc.stderr)


try:
    from .host_identity_cases import build_host_identity_cases
    from .replacement_object_cases import build_replacement_object_cases
except ImportError:
    from host_identity_cases import build_host_identity_cases
    from replacement_object_cases import build_replacement_object_cases


HostIdentityRefusalCases, FooterReappearanceCases = build_host_identity_cases(
    globals()
)
(ReplacementObjectCases,) = build_replacement_object_cases(globals())


class TestCommitVerification(
    HostIdentityRefusalCases, ReplacementObjectCases, HexctlCase
):
    def test_local_fake_git_negative_matrix_is_fail_closed_and_secret_safe(self):
        module = hexctl_module()
        module.GIT_TIMEOUT = 0.05
        for mode in (
            "nonzero", "timeout", "overflow", "missing-trailer",
            "duplicate-trailer", "host-author", "host-committer",
            "host-coauthor", "host-byline", "range-confusion",
            "malformed-range", "missing-commit",
        ):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {"PATH": self.env["PATH"], "FAKE_GIT_MODE": mode},
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verify_local_range(self.dir, "base", "head", "step")
                self.assertNotIn("ghp_FAKE_SECRET", error.getvalue())
                self.assertNotIn("FAKE SIGNATURE MATERIAL", error.getvalue())

    def test_authorised_publisher_committer_keeps_shoggoth_author(self):
        module = hexctl_module()
        commit = "a" * 40
        with mock.patch.dict(
            os.environ,
            {"PATH": self.env["PATH"], "FAKE_GIT_MODE": "publisher-committer"},
        ):
            self.assertEqual(
                module.verify_local_commit(self.dir, commit, "step"), commit
            )
            self.assertEqual(
                module.commit_author(self.dir, commit, "step"),
                ("Shoggoth", "shoggoth@wildcat.finance"),
            )
            self.assertEqual(
                module.commit_committer(self.dir, commit, "step"),
                ("Laurence Day", "laurence@wildcat.finance"),
            )

    def test_pull_request_refuses_host_author_and_byline(self):
        module = hexctl_module()
        url = "https://github.com/wildcat-finance/example/pull/1"
        branch = "fiat/run-step-1"
        base = "fiat/run"
        head = "a" * 40
        payload = self.fake_pr(url, branch, base, head)
        for mode in ("host-pr-author", "host-pr-byline"):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {
                        "PATH": self.env["PATH"],
                        "FAKE_GH_MODE": mode,
                        "FAKE_GH_PRS": json.dumps({url: payload}),
                    },
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.inspect_pull_request(
                            self.dir,
                            url,
                            expected_head=branch,
                            expected_base=base,
                            expected_head_sha=head,
                            expected_merge_sha=None,
                        )
                self.assertIn("runtime", error.getvalue())

    def test_local_success_checks_every_intermediate_commit(self):
        module = hexctl_module()
        log_path = os.path.join(self.dir, "verified.log")
        with mock.patch.dict(
            os.environ,
            {
                "PATH": self.env["PATH"],
                "FAKE_GIT_MODE": "intermediate",
                "FAKE_GIT_LOG": log_path,
            },
        ):
            commits = module.verify_local_range(self.dir, "base", "head", "step")
        with open(log_path, encoding="utf-8") as handle:
            checked = handle.read().splitlines()
        self.assertEqual(commits, checked)
        self.assertEqual(len(checked), 2)

    def test_fake_github_negative_matrix_is_fail_closed_and_secret_safe(self):
        module = hexctl_module()
        module.GIT_TIMEOUT = 0.05
        for mode in (
            "nonzero", "timeout", "overflow", "invalid-json",
            "verified-false", "invalid-reason", "missing-sha",
        ):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {"PATH": self.env["PATH"], "FAKE_GH_MODE": mode},
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verify_github_commits(self.dir, ["a" * 40])
                self.assertNotIn("ghp_FAKE_SECRET", error.getvalue())
                self.assertNotIn("RAW FAKE SIGNATURE", error.getvalue())

        reasons = (
            "unknown_signature_type", "no_user", "unverified_email",
            "bad_email", "unknown_key", "malformed_signature", "invalid",
            "expired_key", "not_signing_key", "gpgverify_error",
            "gpgverify_unavailable", "unsigned",
        )
        for reason in reasons:
            with self.subTest(reason=reason):
                error = StringIO()
                with mock.patch.dict(
                    os.environ,
                    {
                        "PATH": self.env["PATH"],
                        "FAKE_GH_MODE": "invalid-reason",
                        "FAKE_GH_REASON": reason,
                    },
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verify_github_commits(self.dir, ["a" * 40])


try:
    from .github_transport_cases import build_github_transport_tests
except ImportError:
    from github_transport_cases import build_github_transport_tests


TestGithubTransport = build_github_transport_tests(globals())


class TestMergedAttribution(HexctlCase):
    """Who a run published under, recorded without an address.

    The GitHub commits endpoint is the source: its `author` is the account the
    commit was matched to, and it is `null` when nothing matched. These drive
    the reader directly where the shape is the subject, and through the CLI
    where the recorded receipt is.
    """

    def to_push(self):
        self.to_steps(("Ship",))
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )

    def attribution_of(self, mode, commits=("a" * 40,)):
        module = hexctl_module()
        with mock.patch.dict(
            os.environ, {"PATH": self.env["PATH"], "FAKE_GH_MODE": mode}
        ):
            return module.verified_github_attribution(self.dir, list(commits))[1]

    def test_an_external_author_is_recorded_by_account_and_normalised_digest(self):
        record = self.attribution_of("external-author")[0]
        self.assertEqual(record["login"], "kethcode")
        self.assertEqual(record["name"], "Kethcode")
        self.assertEqual(record["commit"], "a" * 40)
        self.assertEqual(
            record["email_sha256"],
            hashlib.sha256(b"kethcode@example.invalid").hexdigest(),
        )

    def test_an_unlinked_author_records_an_explicit_null(self):
        record = self.attribution_of("unlinked-author")[0]
        self.assertIsNone(record["login"])
        self.assertEqual(len(record["email_sha256"]), 64)

    def test_every_coauthor_trailer_becomes_its_own_identity(self):
        record = self.attribution_of("attribution-second-coauthor")[0]
        self.assertEqual(
            [entry["name"] for entry in record["coauthors"]],
            ["Shoggoth", "Kethcode"],
        )
        self.assertEqual(
            len({entry["email_sha256"] for entry in record["coauthors"]}), 2
        )

    def test_attribution_negative_matrix_is_fail_closed_and_secret_safe(self):
        module = hexctl_module()
        for mode, expected in (
            ("attribution-host-account", "runtime host account"),
            ("attribution-account-not-object", "account is not an object"),
            ("attribution-null-account-object", "account login is not a string"),
            ("attribution-bad-login", "account login is malformed"),
            ("attribution-host-author", "runtime host as author"),
            ("attribution-host-committer-account", "runtime host account"),
            ("attribution-host-committer", "runtime host"),
            ("attribution-missing-committer", "identity is not an object"),
            ("attribution-bad-committer-login", "account login is malformed"),
            ("attribution-missing-identity", "identity is not an object"),
            ("attribution-blank-name", "identity name is malformed"),
            ("attribution-long-name", "identity name is malformed"),
            ("attribution-spaced-email", "identity address is malformed"),
            ("attribution-long-email", "identity address is malformed"),
            ("attribution-missing-message", "commit message is missing"),
            ("attribution-host-coauthor", "runtime host as co-author"),
            ("attribution-many-coauthors", "co-author trailers"),
        ):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ, {"PATH": self.env["PATH"], "FAKE_GH_MODE": mode}
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.verified_github_attribution(self.dir, ["a" * 40])
                self.assertIn(expected, error.getvalue())
                self.assertNotIn("RAW FAKE SIGNATURE", error.getvalue())
                self.assertNotIn("ghp_FAKE_SECRET", error.getvalue())

    def test_author_and_publisher_committer_are_recorded_separately(self):
        record = self.attribution_of("publisher-committer")[0]
        self.assertEqual(record["login"], "shoggoth-wildcat")
        self.assertEqual(record["name"], "Shoggoth")
        self.assertEqual(record["committer"]["login"], "laurenceday")
        self.assertEqual(record["committer"]["name"], "Laurence Day")
        self.assertNotEqual(
            record["email_sha256"], record["committer"]["email_sha256"]
        )

    def test_verification_alone_does_not_apply_the_attribution_checks(self):
        """A merge commit refuses on its signature, never on its identity shape.

        `verify_github_commits` also covers the merge and sync receipts. If it
        read identities too, an unexpected author shape on a merge commit would
        refuse a receipt that has nothing to do with attribution.
        """
        module = hexctl_module()
        for mode in ("attribution-long-name", "attribution-missing-message",
                     "attribution-null-account-object"):
            with self.subTest(mode=mode):
                with mock.patch.dict(
                    os.environ, {"PATH": self.env["PATH"], "FAKE_GH_MODE": mode}
                ):
                    self.assertEqual(
                        module.verify_github_commits(self.dir, ["a" * 40]),
                        ["a" * 40],
                    )

    def test_verification_and_attribution_share_one_request_per_sha(self):
        module = hexctl_module()
        log_path = os.path.join(self.dir, "gh.log")
        with mock.patch.dict(
            os.environ,
            {"PATH": self.env["PATH"], "FAKE_GH_LOG": log_path},
        ):
            module.verified_github_attribution(self.dir, ["a" * 40, "b" * 40])
        with open(log_path, encoding="utf-8") as handle:
            calls = [json.loads(line) for line in handle if line.strip()]
        commit_reads = [
            call for call in calls if any("/commits/" in value for value in call)
        ]
        self.assertEqual(len(commit_reads), 2)

    def test_the_push_receipt_records_the_accounts_and_no_address(self):
        self.to_push()
        self.env["FAKE_GH_MODE"] = "external-author"
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        receipt = self.state()["steps"][0]["receipts"]["push"]
        attribution = receipt["attribution"]
        self.assertEqual(attribution["pull_request_author"], "shoggoth-wildcat")
        self.assertEqual(
            [entry["login"] for entry in attribution["commits"]], ["kethcode"]
        )
        self.assertEqual(receipt["pull_request"]["author_login"], "shoggoth-wildcat")
        self.assertNotIn("@", json.dumps(attribution))

    def test_the_ledger_carries_the_attribution_and_no_address(self):
        self.to_push()
        self.env["FAKE_GH_MODE"] = "unlinked-author"
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(path, encoding="utf-8") as handle:
            events = [json.loads(line) for line in handle if line.strip()]
        pushed = [event for event in events if event["event"] == "done:push"]
        self.assertEqual(len(pushed), 1)
        recorded = pushed[0]["data"]["attribution"]
        self.assertIsNone(recorded["commits"][0]["login"])
        self.assertNotIn("@", json.dumps(recorded))
        self.run_ctl("verify")

    def test_the_push_receipt_records_the_author_and_human_publisher(self):
        self.to_push()
        self.env["FAKE_GIT_MODE"] = "publisher-committer"
        self.env["FAKE_GH_MODE"] = "publisher-committer"
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        attribution = self.state()["steps"][0]["receipts"]["push"]["attribution"]
        self.assertEqual(attribution["pull_request_author"], "laurenceday")
        self.assertEqual(attribution["commits"][0]["login"], "shoggoth-wildcat")
        self.assertEqual(
            attribution["commits"][0]["committer"]["login"], "laurenceday"
        )
        self.assertNotIn("@", json.dumps(attribution))
        authors = hexctl_module().recorded_run_attribution(self.state())
        self.assertEqual([entry["login"] for entry in authors], ["shoggoth-wildcat"])
        self.assertNotIn("committer", authors[0])
        self.run_ctl("verify")


class TestMergedState(HexctlCase):
    """Whether the base still carries the identities a run published under."""

    URL = "https://github.com/wildcat-finance/example/pull/1"
    RUN_URL = "https://github.com/wildcat-finance/example/pull/9"

    def to_integrate(self, push_mode="external-author", base=None):
        self.to_steps(("Ship",), base=base)
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.env["FAKE_GH_MODE"] = push_mode
        self.run_ctl(
            "done", "push", "--pr-url", self.URL,
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        self.env.pop("FAKE_GH_MODE", None)
        self.run_ctl(
            "done", "merge-step", "--step", "1", "--merge-commit", "e" * 40
        )
        self.write_run_pr()

    def integrate(self, *, expect=0, git_mode=None, gh_mode=None):
        if expect != 0:
            # `run_ctl` seeds the integration pull request only for expected
            # successes; a refusal case stands it up itself or fails on the
            # topology read instead of the check under test.
            state = self.state()
            self.fake_refs[state["run_branch"]] = "e" * 40
            self.fake_prs[self.RUN_URL] = self.fake_pr(
                self.RUN_URL, state["run_branch"], self.integration_base(state),
                "e" * 40, "f" * 40,
            )
        if git_mode:
            self.env["FAKE_GIT_MODE"] = git_mode
        if gh_mode:
            self.env["FAKE_GH_MODE"] = gh_mode
        try:
            return self.run_ctl(
                "done", "integrate", "--pr-url", self.RUN_URL,
                "--merge-commit", "f" * 40, expect=expect,
            )
        finally:
            self.env.pop("FAKE_GIT_MODE", None)
            self.env.pop("FAKE_GH_MODE", None)

    def recorded(self):
        return self.state()["receipts"]["integrate"]["attribution"]

    def test_a_preserved_merge_records_the_ancestor_mechanism(self):
        self.to_integrate()
        self.integrate()
        recorded = self.recorded()
        self.assertEqual(recorded["mechanisms"], ["ancestor"])
        self.assertEqual(
            [entry["login"] for entry in recorded["identities"]], ["kethcode"]
        )
        self.assertEqual(recorded["carriers"], {})
        self.assertEqual(
            [entry["carrier"] for entry in recorded["identities"]], [None]
        )
        self.run_ctl("verify")

    def test_a_rewritten_merge_may_be_carried_by_the_merge_author(self):
        self.to_integrate()
        self.integrate(git_mode="not-ancestor", gh_mode="external-author")
        recorded = self.recorded()
        self.assertEqual(recorded["mechanisms"], ["merge-author"])
        # The step's own merge into the run branch is tried before the base
        # merge, and under this fixture it carries the identity.
        self.assertEqual(
            [entry["carrier"] for entry in recorded["identities"]], ["e" * 40]
        )
        self.assertEqual(recorded["carriers"], {"e" * 40: "kethcode"})

    def test_a_rewritten_merge_may_be_carried_by_a_coauthor_trailer(self):
        self.to_integrate()
        self.integrate(git_mode="not-ancestor", gh_mode="attribution-merge-coauthor")
        recorded = self.recorded()
        self.assertEqual(recorded["mechanisms"], ["merge-coauthor"])
        self.assertEqual(recorded["carriers"], {"e" * 40: "maintainer"})

    def test_a_rewritten_merge_that_dropped_the_identity_refuses(self):
        self.to_integrate()
        proc = self.integrate(
            expect=2, git_mode="not-ancestor", gh_mode="attribution-merge-stranger"
        )
        self.assertIn("no merge this run recorded carries that commit", proc.stderr)
        self.assertIn("kethcode", proc.stderr)
        self.assertNotIn("@", proc.stderr)
        self.assertEqual(self.state()["phase"], "integrate")

    def test_an_unanswerable_ancestry_call_refuses_rather_than_reporting_no(self):
        self.to_integrate()
        proc = self.integrate(expect=2, git_mode="ancestry-error")
        self.assertIn("ancestry", proc.stderr)
        self.assertIn("could not be determined", proc.stderr)

    def test_a_legacy_receipt_without_attribution_still_integrates(self):
        self.to_integrate()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["steps"][0]["receipts"]["push"].pop("attribution", None)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)
        ledger_path = os.path.join(
            self.target, ".hexaemeron", "ledger.jsonl"
        )
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        entries[-1]["state"] = hexctl_module().state_fingerprint(state)
        entries[-1]["hash"] = hashlib.sha256(
            hexctl_module().canonical(
                {
                    "ts": entries[-1]["ts"],
                    "event": entries[-1]["event"],
                    "data": entries[-1]["data"],
                    "prev": entries[-1]["prev"],
                    "state": entries[-1]["state"],
                }
            ).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")
        self.integrate()
        recorded = self.recorded()
        self.assertEqual(recorded["identities"], [])
        self.assertEqual(recorded["mechanisms"], [])
        self.assertEqual(recorded["carriers"], {})

    def test_a_step_merge_is_tried_before_the_base_merge(self):
        """A squashed step keeps its identity on its own merge, not the base one.

        The base merge's message names no contributor, so a fallback that
        looked only there would refuse an identity that did reach the base.
        """
        self.to_integrate()
        state = self.state()
        self.assertEqual(
            state["integrate"]["merges"]["1"]["merge_commit"], "e" * 40
        )
        self.integrate(git_mode="not-ancestor", gh_mode="attribution-merge-coauthor")
        identities = self.recorded()["identities"]
        self.assertEqual([entry["carrier"] for entry in identities], ["e" * 40])
        self.assertNotIn("f" * 40, self.recorded()["carriers"])

    def test_a_step_merge_that_never_reached_the_base_is_not_a_carrier(self):
        """A recorded merge only counts while it is reachable from the base."""
        self.to_integrate()
        self.env["FAKE_GIT_NOT_ANCESTOR"] = ",".join(("d" * 40, "e" * 40))
        try:
            self.integrate(git_mode="not-ancestor", gh_mode="external-author")
        finally:
            self.env.pop("FAKE_GIT_NOT_ANCESTOR", None)
        identities = self.recorded()["identities"]
        self.assertEqual([entry["carrier"] for entry in identities], ["f" * 40])
        self.assertEqual(self.recorded()["carriers"], {"f" * 40: "kethcode"})

    def test_an_empty_repaired_container_is_current_not_absent(self):
        """A repair that recorded no commits does not fall back to stale data.

        `effective_push` is the fresher record by construction. Reading it by
        truthiness rather than presence would treat an empty container as
        absent and quietly use the head the repair replaced.
        """
        module = hexctl_module()
        state = {
            "steps": [{"n": 1, "receipts": {"push": {"attribution": {
                "commits": [{"commit": "d" * 40, "login": "stale"}]}}}}],
            "integrate": {"merges": {"1": {"effective_push": {"attribution": {}}}}},
        }
        self.assertEqual(module.recorded_run_attribution(state), [])

    def test_the_integrate_directive_names_the_preserving_merge_method(self):
        self.to_integrate()
        directive = self.next_json()
        self.assertEqual(directive["do"], "integrate")
        self.assertEqual(directive["attribution"]["recorded_identities"], 1)
        self.assertIn("merge commit", directive["attribution"]["preserved_by"])
        self.assertIn("squash", directive["attribution"]["preserved_by"])

    def test_a_merge_time_repair_refreshes_the_attribution(self):
        """A repaired head must not be described by the old head's identities.

        The lead step 2's round 1 carried forward: the repair path recomputes
        the verified range and GitHub's result, so the attribution beside them
        has to be recomputed too or it describes commits that are gone.
        """
        self.to_steps(("Ship",))
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.env["FAKE_GH_MODE"] = "external-author"
        self.run_ctl(
            "done", "push", "--pr-url", self.URL,
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        self.env.pop("FAKE_GH_MODE", None)
        branch = self.step_branch(1)
        self.fake_refs[branch] = "c" * 40
        self.fake_prs[self.URL]["head"]["sha"] = "c" * 40
        self.env["FAKE_GH_MODE"] = "unlinked-author"
        self.run_ctl(
            "done", "merge-step", "--step", "1", "--merge-commit", "e" * 40
        )
        self.env.pop("FAKE_GH_MODE", None)
        effective = self.state()["integrate"]["merges"]["1"]["effective_push"]
        self.assertTrue(effective["repaired"])
        self.assertEqual(effective["head"], "c" * 40)
        refreshed = effective["attribution"]["commits"]
        self.assertEqual([entry["login"] for entry in refreshed], [None])
        self.assertEqual([entry["commit"] for entry in refreshed], ["c" * 40])
        self.assertNotIn("@", json.dumps(effective["attribution"]))

        # The integration check reads the refreshed container, not the stale one.
        self.write_run_pr()
        self.integrate()
        self.assertEqual(
            [entry["commit"] for entry in self.recorded()["identities"]], ["c" * 40]
        )


class TestPublicationBindings(FooterReappearanceCases, HexctlCase):
    def to_push(self, base=None):
        self.to_steps(("Ship",), base=base)
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )

    def to_merge_step(self, base=None):
        self.to_push(base=base)
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )

    def to_integrate(self, base=None):
        self.to_merge_step(base=base)
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        self.write_run_pr()

    def edit_push_receipt(self, edit):
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as handle:
            state = json.load(handle)
        edit(state["steps"][0]["receipts"]["push"])
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)

    def prime_step_merge(self, merge_sha="e" * 40):
        pr = self.fake_prs["https://github.com/wildcat-finance/example/pull/1"]
        pr["state"] = "closed"
        pr["merged"] = True
        pr["merge_commit_sha"] = merge_sha

    def set_post_push_head(self, head):
        branch = self.step_branch(1)
        self.fake_refs[branch] = head
        self.fake_prs["https://github.com/wildcat-finance/example/pull/1"][
            "head"
        ]["sha"] = head

    def test_merge_repairs_legacy_push_receipt_missing_verified_head(self):
        self.to_merge_step()
        self.edit_push_receipt(
            lambda receipt: (
                receipt.pop("github_verified", None),
                receipt.pop("verified_commits", None),
            )
        )
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        repair = self.state()["integrate"]["merges"]["1"]["effective_push"]
        self.assertTrue(repair["repaired"])
        self.assertEqual(repair["head"], "d" * 40)

    def test_merge_repairs_signed_post_push_head(self):
        self.to_merge_step()
        repaired_head = "7" * 40
        self.set_post_push_head(repaired_head)
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40,
        )
        repair = self.state()["integrate"]["merges"]["1"]["effective_push"]
        self.assertTrue(repair["repaired"])
        self.assertEqual(repair["head"], repaired_head)

    def test_merge_time_repair_refuses_invalid_local_signature(self):
        self.to_merge_step()
        self.edit_push_receipt(lambda receipt: receipt.pop("github_verified", None))
        self.prime_step_merge()
        self.env["FAKE_GIT_MODE"] = "unsigned"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("valid local signature", proc.stderr)

    def test_merge_time_repair_refuses_invalid_github_verification(self):
        self.to_merge_step()
        self.set_post_push_head("7" * 40)
        self.prime_step_merge()
        self.env["FAKE_GH_MODE"] = "verified-false"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("not verified:true", proc.stderr)

    def test_merge_time_repair_refuses_remote_pr_head_mismatch(self):
        self.to_merge_step()
        self.fake_prs["https://github.com/wildcat-finance/example/pull/1"][
            "head"
        ]["sha"] = "7" * 40
        self.prime_step_merge()
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("remote branch tip", proc.stderr)

    def test_merge_time_repair_refuses_pr_topology_mismatch(self):
        self.to_merge_step()
        self.prime_step_merge()
        self.env["FAKE_GH_MODE"] = "pr-mismatch"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "e" * 40, expect=2,
        )
        self.assertIn("topology", proc.stderr)

    def test_implement_head_must_equal_declared_branch_tip(self):
        self.to_steps(("Ship",))
        proc = self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123", expect=2,
        )
        self.assertIn("branch tip", proc.stderr)

    def test_push_refuses_cross_repository_pr_and_mismatched_head(self):
        self.to_push()
        branch = self.step_branch(1)
        self.fake_refs[branch] = self.fake_sha("def456")
        proc = self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/elsewhere/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
            expect=2,
        )
        self.assertIn("repository", proc.stderr)

    def test_push_head_must_equal_pushed_branch_tip(self):
        self.to_push()
        proc = self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
            expect=2,
        )
        self.assertIn("branch tip", proc.stderr)

    def test_repository_identity_is_bound_to_target_origin(self):
        module = hexctl_module()
        error = StringIO()
        with mock.patch.dict(
            os.environ,
            {"PATH": self.env["PATH"], "FAKE_GH_MODE": "repo-mismatch"},
        ), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.github_repository(self.dir)
        self.assertIn("target origin", error.getvalue())

    def test_invalid_github_value_is_refused_before_gh_and_not_echoed(self):
        module = hexctl_module()
        log_path = os.path.join(self.dir, "gh.log")
        error = StringIO()
        with mock.patch.dict(
            os.environ,
            {"PATH": self.env["PATH"], "FAKE_GH_LOG": log_path},
        ), redirect_stderr(error):
            with self.assertRaises(SystemExit):
                module.verify_github_commits(self.dir, ["ghp_FAKE_SECRET"])
        self.assertNotIn("ghp_FAKE_SECRET", error.getvalue())
        self.assertFalse(os.path.exists(log_path))

    def test_merge_step_refuses_pr_topology_mismatch(self):
        self.to_push()
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
        )
        self.env["FAKE_GH_MODE"] = "pr-mismatch"
        proc = self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "b" * 40, expect=2,
        )
        self.assertIn("pull request", proc.stderr)

    def test_integrate_refuses_pr_topology_mismatch(self):
        self.to_push()
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "def456", "--pr-base", self.step_base(1),
        )
        self.run_ctl(
            "done", "merge-step", "--step", "1",
            "--merge-commit", "b" * 40,
        )
        self.write_run_pr()
        self.env["FAKE_GH_MODE"] = "pr-mismatch"
        proc = self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "c" * 40, expect=2,
        )
        self.assertIn("pull request", proc.stderr)

    def test_integrate_pr_head_must_equal_remote_run_branch_tip(self):
        self.to_integrate()
        state = self.state()
        url = "https://github.com/wildcat-finance/example/pull/2"
        self.fake_prs[url] = self.fake_pr(
            url,
            state["run_branch"],
            self.integration_base(state),
            self.fake_refs[state["run_branch"]],
            "f" * 40,
        )
        self.env["FAKE_GH_MODE"] = "pr-head-mismatch"
        proc = self.run_ctl(
            "done", "integrate",
            "--pr-url", url,
            "--merge-commit", "f" * 40, expect=2,
        )
        self.assertIn("remote run branch tip", proc.stderr)

    def test_remote_run_branch_tip_requires_one_exact_full_ref(self):
        module = hexctl_module()
        branch = "fiat/run"
        tip = "8" * 40
        base_env = {
            "PATH": self.env["PATH"],
            "FAKE_GIT_REFS": json.dumps({branch: tip}),
        }
        with mock.patch.dict(os.environ, base_env):
            self.assertEqual(module.remote_branch_tip(self.dir, branch), tip)
        for mode in ("remote-absent", "remote-malformed", "remote-duplicate"):
            with self.subTest(mode=mode):
                error = StringIO()
                with mock.patch.dict(
                    os.environ, {**base_env, "FAKE_GIT_MODE": mode}
                ), redirect_stderr(error):
                    with self.assertRaises(SystemExit):
                        module.remote_branch_tip(self.dir, branch)
                self.assertIn("remote run branch tip", error.getvalue())

    def test_integrate_remote_tip_must_equal_final_recorded_step_merge(self):
        self.to_integrate()
        state = self.state()
        url = "https://github.com/wildcat-finance/example/pull/2"
        divergent_tip = "8" * 40
        self.fake_refs[state["run_branch"]] = divergent_tip
        self.fake_prs[url] = self.fake_pr(
            url,
            state["run_branch"],
            self.integration_base(state),
            divergent_tip,
            "f" * 40,
        )
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", url,
            "--merge-commit", "f" * 40, expect=2,
        )
        self.assertIn("final recorded step merge", proc.stderr)

    def prepare_run_sync(
        self, sync_sha="7" * 40, base_sha="6" * 40, starting_base=None
    ):
        self.to_integrate(base=starting_base)
        state = self.state()
        final_merge = state["integrate"]["merges"]["1"]["merge_commit"]
        base_before = "4" * 40
        self.fake_refs[state["run_branch"]] = sync_sha
        self.fake_refs[self.integration_base(state)] = base_sha
        self.fake_parents[sync_sha] = [final_merge, base_sha]
        self.env["FAKE_GIT_MERGE_BASE"] = base_before
        self.env["FAKE_GIT_DIFF_PATHS"] = json.dumps(
            {
                f"{base_before}..{final_merge}": [
                    "product.py",
                    "shared.json",
                ],
                f"{base_before}..{base_sha}": [
                    "shared.json",
                    "upstream.py",
                ],
                f"{final_merge}..{sync_sha}": [
                    "shared.json",
                    "upstream.py",
                ],
            }
        )
        return state, sync_sha, base_sha

    def test_pinned_starting_commit_syncs_and_integrates_into_the_named_base(self):
        starting_base = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.dir,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        _, sync_sha, base_sha = self.prepare_run_sync(
            starting_base=starting_base
        )
        directive = self.next_json()
        self.assertEqual(directive["base"], "main")
        self.assertEqual(directive["starting_base"], starting_base)

        revalidation = self.write_integration_revalidation()
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
        )
        self.assertIn("synced with main", proc.stdout)
        sync = self.state()["integrate"]["sync"]
        self.assertEqual(sync["base"], "main")
        self.assertEqual(sync["starting_base"], starting_base)

        self.write_run_pr()
        self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
        )
        receipt = self.state()["receipts"]["integrate"]
        self.assertEqual(receipt["base"], "main")
        self.assertEqual(receipt["starting_base"], starting_base)

    def test_integration_base_distinguishes_a_branch_from_a_pinned_commit(self):
        module = hexctl_module()
        self.assertEqual(
            module.integration_base_of(
                {"base": "release/one", "config": {"git": {"base": "main"}}}
            ),
            "release/one",
        )
        for configured, message in (
            (None, "needs config.git.base"),
            ("6" * 40, "must name an integration branch"),
            ("../main", "not a usable branch name"),
        ):
            with self.subTest(configured=configured):
                error = StringIO()
                state = {
                    "base": "5" * 40,
                    "config": {"git": {"base": configured}},
                }
                with redirect_stderr(error), self.assertRaises(SystemExit):
                    module.integration_base_of(state)
                self.assertIn(message, error.getvalue())

    def write_integration_revalidation(
        self, *, affected_paths=None, checks=None
    ):
        affected_paths = (
            ["shared.json", "upstream.py"]
            if affected_paths is None else affected_paths
        )
        checks = checks or [
            {
                "id": "root-suite",
                "command": "python3 -m unittest discover -s tests",
                "paths": affected_paths,
                "exit": 0,
            }
        ]
        return self.write(
            ".hexaemeron/integration-revalidation.json",
            json.dumps(
                {
                    "schema": "fiat-integration-revalidation/v1",
                    "affected_paths": affected_paths,
                    "checks": checks,
                }
            ),
        )

    def configure_sync_replacement(self, sync_sha, base_sha):
        state = self.state()
        final_merge = state["integrate"]["merges"]["1"]["merge_commit"]
        base_before = "4" * 40
        self.fake_refs[state["run_branch"]] = sync_sha
        self.fake_refs[self.integration_base(state)] = base_sha
        self.fake_parents[sync_sha] = [final_merge, base_sha]
        self.env["FAKE_GIT_DIFF_PATHS"] = json.dumps(
            {
                f"{base_before}..{final_merge}": [
                    "product.py",
                    "shared.json",
                ],
                f"{base_before}..{base_sha}": [
                    "controller.py",
                    "shared.json",
                    "upstream.py",
                ],
                f"{final_merge}..{sync_sha}": [
                    "controller.py",
                    "shared.json",
                    "upstream.py",
                ],
            }
        )
        return self.write_integration_revalidation(
            affected_paths=["controller.py", "shared.json", "upstream.py"]
        )

    def test_sync_run_receipts_exact_merge_and_allows_integration(self):
        state, sync_sha, base_sha = self.prepare_run_sync()
        before = self.state()
        revalidation = self.write_integration_revalidation()
        self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
        )
        after_sync = self.state()
        self.assertEqual(before["steps"], after_sync["steps"])
        sync = after_sync["integrate"]["sync"]
        self.assertEqual(sync["product_evidence"]["head"], "e" * 40)
        self.assertEqual(sync["revalidation"]["base_before"], "4" * 40)
        self.assertEqual(sync["revalidation"]["product_paths"], [
            "product.py", "shared.json",
        ])
        self.assertEqual(sync["revalidation"]["upstream_paths"], [
            "shared.json", "upstream.py",
        ])
        self.assertEqual(sync["revalidation"]["overlap_paths"], ["shared.json"])
        self.assertEqual(sync["revalidation"]["composition_paths"], [
            "shared.json", "upstream.py",
        ])
        self.assertEqual(sync["revalidation"]["affected_paths"], [
            "shared.json", "upstream.py",
        ])
        self.assertEqual(
            sync["resolution_guard"],
            {
                "schema": "fiat-sync-resolution-guard/v1",
                "side_selected_paths": [],
                "superseded_intersection_paths": [],
                "acknowledged_paths": [],
            },
        )
        status = self.run_ctl("status").stdout
        self.assertIn("product eeeeeeeeeeee preserved", status)
        self.assertIn("1 integration revalidation check(s) recorded", status)
        self.write_run_pr()
        self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
        )
        receipt = self.state()["receipts"]["integrate"]
        self.assertEqual(receipt["run_head"], sync_sha)
        self.assertEqual(receipt["sync"]["base_head"], base_sha)
        self.assertEqual(receipt["sync"]["parents"], ["e" * 40, base_sha])

    def test_sync_run_supersedes_one_failed_composition_without_reopening_product(self):
        _, first_sync, first_base = self.prepare_run_sync()
        first_revalidation = self.write_integration_revalidation()
        self.run_ctl(
            "done", "sync-run", "--commit", first_sync,
            "--base-commit", first_base,
            "--revalidation", first_revalidation,
        )
        product = self.state()["integrate"]["sync"]["product_evidence"]

        replacement_sync = "8" * 40
        replacement_base = "9" * 40
        replacement_revalidation = self.configure_sync_replacement(
            replacement_sync, replacement_base
        )
        proc = self.run_ctl(
            "done", "sync-run",
            "--commit", replacement_sync,
            "--base-commit", replacement_base,
            "--revalidation", replacement_revalidation,
            "--supersede-sync", first_sync,
            "--reason", "the required integration check failed in a shallow clone",
        )
        self.assertIn("superseded", proc.stdout)

        integrate = self.state()["integrate"]
        self.assertEqual(integrate["sync"]["commit"], replacement_sync)
        self.assertEqual(integrate["sync"]["base_head"], replacement_base)
        self.assertEqual(integrate["sync"]["product_evidence"], product)
        self.assertEqual(len(integrate["superseded_syncs"]), 1)
        prior = integrate["superseded_syncs"][0]
        self.assertEqual(prior["sync"]["commit"], first_sync)
        self.assertEqual(prior["superseded_by"], replacement_sync)
        self.assertEqual(
            prior["reason"],
            "the required integration check failed in a shallow clone",
        )
        status = self.run_ctl("status").stdout
        self.assertIn("1 superseded sync(s) retained", status)
        directive = self.next_json()
        self.assertEqual(
            directive["base_advance"]["recovery"],
            "supersede-sync-and-revalidate",
        )
        self.assertIn(
            f"--supersede-sync {replacement_sync}",
            directive["base_advance"]["then"],
        )

        self.write_run_pr()
        self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
        )
        receipt = self.state()["receipts"]["integrate"]
        self.assertEqual(receipt["sync"]["commit"], replacement_sync)
        self.assertEqual(
            receipt["superseded_syncs"][0]["sync"]["commit"], first_sync
        )

    def test_sync_supersession_requires_a_receipt_and_reason(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
        )
        proc = self.run_ctl(
            "done", "sync-run", "--commit", "8" * 40,
            "--base-commit", base_sha, "--revalidation", revalidation,
            expect=2,
        )
        self.assertIn("use --supersede-sync", proc.stderr)
        proc = self.run_ctl(
            "done", "sync-run", "--commit", "8" * 40,
            "--base-commit", base_sha, "--revalidation", revalidation,
            "--supersede-sync", sync_sha, expect=2,
        )
        self.assertIn("--reason is required", proc.stderr)

    def test_sync_supersession_refuses_stale_or_malformed_subject_evidence(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
        )
        proc = self.run_ctl(
            "done", "sync-run", "--commit", "8" * 40,
            "--base-commit", base_sha, "--revalidation", revalidation,
            "--supersede-sync", "5" * 40,
            "--reason", "a failed check", expect=2,
        )
        self.assertIn("active recorded sync", proc.stderr)
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
            "--supersede-sync", sync_sha, "--reason", "a failed check",
            expect=2,
        )
        self.assertIn("must use a new signed commit", proc.stderr)

        for reason in ("   ", "line one\nline two", "bad\x7fvalue", "é" * 513):
            with self.subTest(reason=repr(reason)):
                proc = self.run_ctl(
                    "done", "sync-run", "--commit", "8" * 40,
                    "--base-commit", base_sha, "--revalidation", revalidation,
                    "--supersede-sync", sync_sha, "--reason", reason,
                    expect=2,
                )
                self.assertIn("reason is invalid", proc.stderr)

    def test_sync_supersession_is_bounded_and_requires_an_existing_receipt(self):
        _, active_sync, active_base = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        proc = self.run_ctl(
            "done", "sync-run", "--commit", active_sync,
            "--base-commit", active_base, "--revalidation", revalidation,
            "--supersede-sync", "5" * 40, "--reason", "nothing active yet",
            expect=2,
        )
        self.assertIn("requires an active recorded sync", proc.stderr)
        proc = self.run_ctl(
            "done", "sync-run", "--commit", active_sync,
            "--base-commit", active_base, "--revalidation", revalidation,
            "--reason", "not attached to a receipt", expect=2,
        )
        self.assertIn("--reason requires --supersede-sync", proc.stderr)
        self.run_ctl(
            "done", "sync-run", "--commit", active_sync,
            "--base-commit", active_base, "--revalidation", revalidation,
        )

        for number in range(8):
            replacement_sync = hashlib.sha1(
                f"replacement-sync-{number}".encode()
            ).hexdigest()
            replacement_base = hashlib.sha1(
                f"replacement-base-{number}".encode()
            ).hexdigest()
            replacement_revalidation = self.configure_sync_replacement(
                replacement_sync, replacement_base
            )
            self.run_ctl(
                "done", "sync-run", "--commit", replacement_sync,
                "--base-commit", replacement_base,
                "--revalidation", replacement_revalidation,
                "--supersede-sync", active_sync,
                "--reason", f"bounded replacement {number + 1}",
            )
            active_sync = replacement_sync

        self.assertEqual(len(self.state()["integrate"]["superseded_syncs"]), 8)
        proc = self.run_ctl(
            "done", "sync-run", "--commit", "a" * 40,
            "--base-commit", "b" * 40,
            "--revalidation", revalidation,
            "--supersede-sync", active_sync,
            "--reason", "one replacement too many", expect=2,
        )
        self.assertIn("supersession limit", proc.stderr)

    def test_sync_and_integration_refuse_edited_state_before_receipt_laundering(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
        )
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, "rb") as handle:
            valid_state = handle.read()
        with open(ledger_path, "rb") as handle:
            valid_ledger = handle.read()

        for command in ("sync", "integrate"):
            with self.subTest(command=command):
                state = json.loads(valid_state)
                state["integrate"]["sync"]["commit"] = "8" * 40
                with open(state_path, "w", encoding="utf-8") as handle:
                    json.dump(state, handle)
                if command == "sync":
                    proc = self.run_ctl(
                        "done", "sync-run", "--commit", "9" * 40,
                        "--base-commit", base_sha,
                        "--revalidation", revalidation,
                        "--supersede-sync", "8" * 40,
                        "--reason", "try to absorb edited state", expect=1,
                    )
                else:
                    proc = self.run_ctl(
                        "done", "integrate",
                        "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                        "--merge-commit", "f" * 40, expect=1,
                    )
                self.assertIn("edited outside hexctl", proc.stderr)
                with open(ledger_path, "rb") as handle:
                    self.assertEqual(handle.read(), valid_ledger)
                with open(state_path, "wb") as handle:
                    handle.write(valid_state)

    def test_sync_run_requires_bounded_green_revalidation(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, expect=2,
        )
        self.assertIn("--revalidation is required", proc.stderr)

        failed = self.write_integration_revalidation(
            checks=[
                {
                    "id": "root-suite",
                    "command": "python3 -m unittest discover -s tests",
                    "paths": ["shared.json", "upstream.py"],
                    "exit": 1,
                }
            ]
        )
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", failed, expect=2,
        )
        self.assertIn("must record exit 0", proc.stderr)

    def test_sync_run_revalidation_covers_the_computed_composition_surface(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        outside = self.write_integration_revalidation(
            affected_paths=["not-in-delta.py"]
        )
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", outside, expect=2,
        )
        self.assertIn("outside the computed integration delta", proc.stderr)

        omitted = self.write_integration_revalidation(
            affected_paths=["upstream.py"],
            checks=[
                {
                    "id": "upstream-suite",
                    "command": "python3 -m unittest upstream_tests",
                    "paths": ["upstream.py"],
                    "exit": 0,
                }
            ],
        )
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", omitted, expect=2,
        )
        self.assertIn("omits the computed integration surface", proc.stderr)

        uncovered = self.write_integration_revalidation(
            affected_paths=["shared.json", "upstream.py"],
            checks=[
                {
                    "id": "shared-suite",
                    "command": "python3 -m unittest shared_tests",
                    "paths": ["shared.json"],
                    "exit": 0,
                }
            ],
        )
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", uncovered, expect=2,
        )
        self.assertIn("do not cover every affected path", proc.stderr)

    def test_integrate_directive_preserves_product_evidence_on_base_drift(self):
        self.to_integrate()
        directive = self.next_json()
        self.assertEqual(
            directive["product_evidence"]["status"], "preserved-exact-tree"
        )
        self.assertEqual(directive["product_evidence"]["head"], "e" * 40)
        self.assertEqual(
            directive["base_advance"]["recovery"], "sync-run-and-revalidate"
        )
        self.assertIn(
            "--revalidation .hexaemeron/integration-revalidation.json",
            directive["base_advance"]["then"],
        )
        self.assertIn(
            "does not authorise a carryover",
            directive["base_advance"]["boundary"],
        )

    def test_sync_run_refuses_wrong_merge_parents(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        self.fake_parents[sync_sha] = ["9" * 40, base_sha]
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
            expect=2,
        )
        self.assertIn("merge parents", proc.stderr)

    def test_sync_run_refuses_unsigned_commit(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        self.env["FAKE_GIT_MODE"] = "unsigned"
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
            expect=2,
        )
        self.assertIn("valid local signature", proc.stderr)

    def test_sync_run_refuses_stale_remote_base(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", "5" * 40, "--revalidation", revalidation,
            expect=2,
        )
        self.assertIn("remote base branch tip", proc.stderr)

    def test_sync_run_refuses_invalid_github_verification(self):
        _, sync_sha, base_sha = self.prepare_run_sync()
        revalidation = self.write_integration_revalidation()
        self.env["FAKE_GH_MODE"] = "verified-false"
        proc = self.run_ctl(
            "done", "sync-run", "--commit", sync_sha,
            "--base-commit", base_sha, "--revalidation", revalidation,
            expect=2,
        )
        self.assertIn("not verified:true", proc.stderr)


class TestDelegationPacketLifecycle(HexctlCase):
    def stable_next(self, expected_do, expected_agent):
        first = self.run_ctl("next").stdout
        second = self.run_ctl("next").stdout
        self.assertEqual(first, second)
        packet = json.loads(first)
        self.assertEqual(packet["do"], expected_do)
        self.assertEqual(packet["agent"], expected_agent)
        return packet

    def test_fresh_run_emits_packets_through_integrate(self):
        self.init("fresh packet proof")
        self.stable_next("study", "surveyor")
        study = self.write(
            "study.md",
            "# Study\n\n```risk-register\n"
            "packet-state-drift | packet | compare state hash\n```\n",
        )
        self.run_ctl(
            "done", "study", "--artifact", study,
            "--skills", "hexaemeron:imprimatur",
        )
        self.stable_next("runbook", None)
        runbook = self.write(
            "runbook.md", "# Runbook\n\n## Step 1: Ship\n\n**Goal.** Ship.\n"
        )
        steps = self.write("steps.json", '["Ship"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )
        self.git("add", study, runbook, steps)
        self.git("commit", "-m", "fixture")
        state = self.state()
        self.git("branch", self.step_branch(1, state))
        self.stable_next("implement", "mason")
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "a" * 40,
        )
        self.stable_next("resolve-security-suite", None)
        self.run_ctl("record", "security_suite", SUITE)
        self.stable_next("audit-round", "warden")
        self.run_ctl("audit-round", "--findings", "0")
        self.stable_next("close-audit", None)
        self.run_ctl("done", "audit")
        self.stable_next("prose", "scribe")
        self.run_ctl(
            "done", "prose", "--files", "1", "--skills",
            "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        self.stable_next("push", None)
        self.run_ctl(
            "done", "push",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "d" * 40, "--pr-base", self.step_base(1),
        )
        self.stable_next("merge-step", None)
        self.run_ctl(
            "done", "merge-step", "--step", "1", "--merge-commit", "e" * 40
        )
        self.stable_next("integrate", None)
        self.write_run_pr()
        self.run_ctl(
            "done", "integrate",
            "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
        )
        self.stable_next("done", None)
        state = self.state()
        self.assertTrue(state["steps"][0]["receipts"]["implement"]["verified_commits"])
        self.assertTrue(state["steps"][0]["receipts"]["push"]["github_verified"])
        self.assertEqual(
            state["integrate"]["merges"]["1"]["github_verified"], ["e" * 40]
        )
        self.assertFalse(
            state["integrate"]["merges"]["1"]["effective_push"]["repaired"]
        )
        self.assertEqual(
            state["receipts"]["integrate"]["github_verified"], ["f" * 40]
        )
        self.assertEqual(state["receipts"]["integrate"]["run_head"], "e" * 40)
        self.assertEqual(
            state["receipts"]["integrate"]["final_step_merge"], "e" * 40
        )
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            ledger = handle.read()
        evidence = json.dumps(state) + ledger
        self.assertNotIn("FAKE SIGNATURE MATERIAL", evidence)
        self.assertNotIn("RAW FAKE SIGNATURE", evidence)
        self.run_ctl("verify")


class TestRunLock(HexctlCase):
    def test_live_holder_refuses_a_second_writer_with_an_actionable_message(self):
        self.init()
        holder, _, release = self.start_lock_holder()
        result = self.run_ctl("record", "key", '"value"', expect=1)
        self.assertIn(f"pid {holder.pid}", result.stderr)
        self.assertIn("`cmd_record`", result.stderr)
        # `git worktree add ../<name> main` was the old advice and it fails
        # whenever the base is already checked out, which is the ordinary case.
        self.assertNotIn("git worktree add", result.stderr)
        self.assertIn("hexctl --dir <checkout> init --topic", result.stderr)
        self.release_lock_holder(holder, release)

    def test_read_only_commands_answer_while_a_writer_holds_the_run(self):
        self.init()
        holder, _, release = self.start_lock_holder()
        for arguments in (("next",), ("status", "--json"), ("verify",)):
            with self.subTest(command=arguments[0]):
                self.run_ctl(*arguments)
        self.release_lock_holder(holder, release)

    def test_crashed_holder_needs_no_manual_cleanup(self):
        self.init()
        holder, _, _ = self.start_lock_holder()
        holder.kill()
        holder.communicate(timeout=5)
        self.run_ctl("record", "after_crash", '"accepted"')

    def test_normal_exit_clears_holder_metadata(self):
        self.init()
        holder, _, release = self.start_lock_holder()
        self.release_lock_holder(holder, release)
        path = os.path.join(self.target, ".hexaemeron", "lock")
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), b"")

    def test_two_contenders_after_a_crash_cannot_both_take_the_lock(self):
        self.init()
        stale, _, _ = self.start_lock_holder("stale")
        stale.kill()
        stale.communicate(timeout=5)

        paths = []
        contenders = []
        for name in ("first", "second"):
            ready = os.path.join(self.dir, f"{name}.ready")
            release = os.path.join(self.dir, f"{name}.release")
            contenders.append(self.spawn_lock_holder(ready, release))
            paths.append((ready, release))

        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            ready_indexes = [
                index
                for index, (ready, _) in enumerate(paths)
                if os.path.exists(ready)
            ]
            exited_indexes = [
                index
                for index, process in enumerate(contenders)
                if process.poll() is not None
            ]
            if len(ready_indexes) == 1 and len(exited_indexes) == 1:
                break
            time.sleep(0.01)
        else:
            self.fail("contenders did not resolve to one holder and one refusal")

        winner = ready_indexes[0]
        loser = exited_indexes[0]
        self.assertNotEqual(winner, loser)
        loser_out, loser_err = contenders[loser].communicate(timeout=5)
        self.assertEqual(contenders[loser].returncode, 1, (loser_out, loser_err))
        self.assertIn("another hexctl is holding this run", loser_err)
        self.assertIn(f"pid {contenders[winner].pid}", loser_err)
        self.release_lock_holder(contenders[winner], paths[winner][1])


class TestStepGates(HexctlCase):
    def test_step_phase_order_enforced(self):
        self.to_steps()
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("out of order", proc.stderr)

    def test_legacy_issue_phase_advances_without_creating_an_issue(self):
        self.to_steps()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["steps"][0]["phase"] = "issue"
        canonical_state = json.dumps(
            state, sort_keys=True, separators=(",", ":")
        )
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        entries[-1]["state"] = hashlib.sha256(canonical_state.encode()).hexdigest()
        unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
        entries[-1]["hash"] = hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

        self.run_ctl("verify")
        directive = self.next_json()
        self.assertEqual(directive["do"], "implement")
        self.assertTrue(directive["legacy_issue_phase_skipped"])
        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.assertEqual(self.next_json()["do"], "resolve-security-suite")


class TestAuditLoop(HexctlCase):
    def test_round_requires_security_suite_receipt(self):
        self.to_audit()
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn("security_suite", proc.stderr)
        out = self.next_json()
        self.assertEqual(out["do"], "resolve-security-suite")

    def test_rounds_advance_and_next_tracks_them(self):
        self.to_audit()
        self.run_ctl("record", "security_suite",
                     '["pashov-xray","pashov-solidity-auditor"]')
        self.assertEqual(self.next_json()["do"], "audit-round")
        self.run_ctl("audit-round", "--findings", "3")
        out = self.next_json()
        self.assertEqual(out["do"], "audit-round")
        self.assertEqual(out["round"], 2)
        self.assertEqual(out["prior_findings"], 3)

    def test_close_blocked_while_findings_open(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        self.run_ctl("audit-round", "--findings", "2", *LINTS_CLEAN)
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("open", proc.stderr)

    def test_clean_close_requires_fixes_evidence_when_findings_existed(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "2")
        self.run_ctl("audit-round", "--findings", "0")
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("fixes", proc.stderr)
        self.run_ctl("done", "audit", "--fixes-ref", "issue-1--audit@deadbeef")
        self.assertEqual(self.next_json()["do"], "prose")

    def test_fixes_commit_on_round_satisfies_evidence(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "1",
                     "--fixes-commit", "beef01",
                     "--elenchus-verdict", "guarded")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_no_further_leads_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "b1",
            "--elenchus-verdict", "guarded",
        )
        proc = self.run_ctl("done", "audit", "--no-further-leads", expect=2)
        self.assertIn("--reason", proc.stderr)
        self.run_ctl("done", "audit", "--no-further-leads",
                     "--reason", "remaining lead is a gas nit, out of scope")

    def test_max_rounds_forces_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.record_legacy_config("audit.max_rounds", 2)
        self.run_ctl(
            "audit-round", "--findings", "2", "--fixes-commit", "b1",
            "--elenchus-verdict", "guarded",
        )
        self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "b2",
            "--elenchus-verdict", "guarded",
        )
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn("max audit rounds", proc.stderr)
        out = self.next_json()
        self.assertEqual(out["do"], "audit-verdict")
        self.assertEqual(out["open_findings"], 1)


class ElenchusVerdictReceiptTests(HexctlCase):
    VERDICTS = ("guarded", "unguarded", "passed", "inconclusive")

    def to_receiptable_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)

    def state_ledger_digests(self):
        paths = (
            os.path.join(self.target, ".hexaemeron", "state.json"),
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
        )
        digests = []
        for path in paths:
            with open(path, "rb") as handle:
                digests.append(hashlib.sha256(handle.read()).hexdigest())
        return tuple(digests)

    def audit_events(self):
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        entries = []
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry["event"] == "audit-round":
                    entries.append(entry)
        return entries

    def make_last_round_legacy(self):
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["steps"][0]["audit"]["rounds"][-1].pop("elenchus_verdict")
        state["steps"][0]["audit"]["rounds"][-1].pop("audit_filter")
        canonical_state = json.dumps(state, sort_keys=True, separators=(",", ":"))
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")

        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(entries[-1]["event"], "audit-round")
        entries[-1]["data"].pop("elenchus_verdict")
        entries[-1]["data"].pop("audit_filter")
        entries[-1]["state"] = hashlib.sha256(canonical_state.encode()).hexdigest()
        unsigned = {key: value for key, value in entries[-1].items() if key != "hash"}
        entries[-1]["hash"] = hashlib.sha256(
            json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for entry in entries:
                handle.write(json.dumps(entry, sort_keys=True) + "\n")

    def test_the_closed_enum_records_state_ledger_and_stdout(self):
        self.to_receiptable_audit()
        for index, verdict in enumerate(self.VERDICTS, 1):
            with self.subTest(verdict=verdict):
                result = self.run_ctl(
                    "audit-round", "--findings", "1",
                    "--fixes-commit", f"fix-{index}",
                    "--elenchus-verdict", verdict,
                )
                self.assertIn(f"Elenchus {verdict}", result.stdout)

        rounds = self.state()["steps"][0]["audit"]["rounds"]
        self.assertEqual(
            [round_entry["elenchus_verdict"] for round_entry in rounds],
            list(self.VERDICTS),
        )
        self.assertEqual(
            [entry["data"]["elenchus_verdict"] for entry in self.audit_events()],
            list(self.VERDICTS),
        )

    def test_a_fix_without_a_verdict_is_refused_without_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "fix-1",
            expect=2,
        )
        self.assertIn("--elenchus-verdict", result.stderr)
        for verdict in self.VERDICTS:
            self.assertIn(verdict, result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_an_unknown_verdict_is_refused_without_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "1", "--fixes-commit", "fix-1",
            "--elenchus-verdict", "unknown", expect=2,
        )
        self.assertIn("--elenchus-verdict", result.stderr)
        for verdict in self.VERDICTS:
            self.assertIn(verdict, result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_a_verdict_without_a_fix_is_refused_without_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "1",
            "--elenchus-verdict", "guarded", expect=2,
        )
        self.assertIn("--elenchus-verdict requires --fixes-commit", result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_a_no_fix_round_records_an_explicit_null(self):
        self.to_receiptable_audit()
        result = self.run_ctl("audit-round", "--findings", "0")
        self.assertIn("Elenchus null", result.stdout)
        round_entry = self.state()["steps"][0]["audit"]["rounds"][0]
        self.assertIn("elenchus_verdict", round_entry)
        self.assertIsNone(round_entry["elenchus_verdict"])
        event = self.audit_events()[0]
        self.assertIn("elenchus_verdict", event["data"])
        self.assertIsNone(event["data"]["elenchus_verdict"])

    def test_next_names_the_conditional_obligation_and_exact_values(self):
        self.to_receiptable_audit()
        expected = {
            "flag": "--elenchus-verdict",
            "required_with": "--fixes-commit",
            "choices": list(self.VERDICTS),
        }
        self.assertEqual(self.next_json()["elenchus_verdict"], expected)
        self.run_ctl("audit-round", "--findings", "1")
        self.assertEqual(self.next_json()["elenchus_verdict"], expected)

    def test_warden_reconstructs_the_exact_mason_runbook_step(self):
        self.to_steps(("Core",))
        mason_first = self.next_json()
        mason_second = self.next_json()
        self.assertEqual(mason_first, mason_second)
        self.assertEqual(
            set(mason_first["brief"]),
            {"runbook_step", "branch", "branch_from", "design_evidence"},
        )
        expected_markdown = "## Step 1: Core\n\n**Goal.** Ship Core.\n"
        expected_source = {
            "markdown": expected_markdown,
            "baseline_markdown": expected_markdown,
            "baseline_sha256": hashlib.sha256(expected_markdown.encode()).hexdigest(),
            "amendments": [],
            "effective_sha256": hashlib.sha256(expected_markdown.encode()).hexdigest(),
            "path": os.path.realpath(os.path.join(self.target, "runbook.md")),
            "sha256": self.state()["receipts"]["runbook"]["sha256"],
            "number": 1,
            "title": "Core",
        }
        self.assertEqual(mason_first["brief"]["runbook_step"], expected_source)

        self.run_ctl(
            "done", "implement", "--branch", self.step_branch(1),
            "--commit", "abc123",
        )
        self.run_ctl("record", "security_suite", SUITE)
        warden_first = self.next_json()
        warden_second = self.next_json()
        self.assertEqual(warden_first, warden_second)
        self.assertEqual(
            warden_first["brief"]["runbook_step"],
            mason_first["brief"]["runbook_step"],
        )
        self.assertEqual(
            set(warden_first["brief"]),
            {
                "step_branch", "stacked_branch", "security_suite", "plugin_root",
                "audit_log_path", "round", "audit_filter", "risk_register",
                "runbook_step", "design_evidence",
            },
        )
        self.assertEqual(
            warden_first["brief"]["design_evidence"],
            mason_first["brief"]["design_evidence"],
        )

    def test_a_legacy_absent_key_survives_every_reader_and_later_round(self):
        self.to_receiptable_audit()
        self.run_ctl("audit-round", "--findings", "1")
        self.make_last_round_legacy()
        log_path = self.state()["config"]["audit"]["log_path"]
        self.env["FAKE_GIT_BASELINE_HEX"] = Path(
            os.path.join(self.target, *log_path.split("/"))
        ).read_bytes().hex()

        self.run_ctl("status")
        directive = self.next_json()
        self.assertEqual(directive["do"], "audit-round")
        self.run_ctl("verify")

        self.run_ctl(
            "audit-round", "--findings", "0", "--fixes-commit", "legacy-fix",
            "--elenchus-verdict", "passed",
        )
        self.run_ctl("done", "audit")
        self.run_ctl("verify")
        rounds = self.state()["steps"][0]["audit"]["rounds"]
        self.assertNotIn("elenchus_verdict", rounds[0])
        self.assertNotIn("audit_filter", rounds[0])
        self.assertEqual(rounds[1]["elenchus_verdict"], "passed")
        self.assertEqual(rounds[1]["audit_filter"], "sapheneia:sapheneia")
        self.assertEqual(self.state()["steps"][0]["phase"], "prose")


try:
    from .audit_record_schema_cases import (
        build_audit_record_schema_tests,
        build_audit_synopsis_resource_boundary_tests,
    )
except ImportError:
    from audit_record_schema_cases import (
        build_audit_record_schema_tests,
        build_audit_synopsis_resource_boundary_tests,
    )


AuditSynopsisResourceBoundaryTests = (
    build_audit_synopsis_resource_boundary_tests(globals())
)
AuditRecordSchemaTests = build_audit_record_schema_tests(globals())

class TestProseAndPush(HexctlCase):
    def to_prose(self, task_issue=None):
        self.to_audit(task_issue=task_issue)
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_prose_requires_both_configured_skills(self):
        self.to_prose()
        proc = self.run_ctl("done", "prose", "--files", "3",
                            "--skills", "hexaemeron:imprimatur", expect=2)
        self.assertIn("hexaemeron:vulgate", proc.stderr)
        self.run_ctl("done", "prose", "--files", "3",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")

    def test_push_requires_pr_url(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        proc = self.run_ctl("done", "push", expect=2)
        self.assertIn("--pr-url", proc.stderr)
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1", expect=2
        )
        self.assertIn("--head-commit", proc.stderr)
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", expect=2,
        )
        self.assertIn("--pr-base", proc.stderr)
        self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
        )

    def test_step_pull_request_may_not_target_the_repository_base(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", "main", expect=2,
        )
        self.assertIn("--pr-base must be", proc.stderr)
        self.assertIn(self.run_branch(), proc.stderr)

    def test_step_pull_request_is_not_merged_during_the_run(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
            "--merge-commit", "def456", expect=2,
        )
        self.assertIn("integrate", proc.stderr)

    def test_second_step_stacks_on_the_first(self):
        self.to_steps(("Scaffold", "Core"))
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        directive = self.next_json()
        self.assertEqual(directive["branch"], self.step_branch(1))
        self.assertEqual(directive["branch_from"], self.run_branch())
        self.assertEqual(directive["pr_base"], self.run_branch())
        self.assertFalse(directive["merge_now"])
        self.finish_step(1)
        directive = self.next_json()
        self.assertEqual(directive["branch"], self.step_branch(2))
        self.assertEqual(directive["branch_from"], self.step_branch(1))
        self.assertEqual(directive["pr_base"], self.step_branch(1))

    def test_run_branch_defaults_to_the_topic_slug_and_may_be_named(self):
        self.init("Borrowing-base covenant hook for V2.5")
        self.assertEqual(self.run_branch(), "fiat/borrowing-base-covenant-hook-for-v2-5")
        self.assertNotEqual(self.run_branch(), self.state()["base"])
        self.run_ctl("reset", expect=2)

    def test_task_issue_is_bound_to_the_initial_state_and_run_branch(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init("Carry the task issue number", task_issue=issue)
        state = self.state()
        self.assertEqual(state["version"], 1)
        self.assertEqual(state["run_branch"], "fiat/438-carry-the-task-issue-number")
        self.assertEqual(state["receipts"]["task_issue"], issue)
        with open(
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
            encoding="utf-8",
        ) as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["event"], "init")
        self.assertEqual(entries[0]["data"]["task_issue"], issue)
        self.assertEqual(entries[0]["state"], hexctl_module().state_fingerprint(state))
        self.run_ctl("verify")

    def test_init_help_describes_the_issue_aware_branch_default(self):
        proc = self.run_ctl("init", "--help")
        self.assertIn("prefixed by task issue when supplied", proc.stdout)

    def test_task_issue_prefix_survives_a_long_topic(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init("x" * 100, task_issue=issue)
        branch = self.run_branch()
        self.assertEqual(branch, "fiat/438-" + "x" * 44)
        self.assertEqual(len(branch.removeprefix("fiat/")), 48)

    def test_task_issue_prefix_uses_run_for_an_empty_topic_slug(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init("###", task_issue=issue)
        self.assertEqual(self.run_branch(), "fiat/438-run")

    def test_task_issue_and_override_are_validated_before_state_creation(self):
        invalid_issues = (
            "not-a-url",
            "not-a-url/issues/438",
            "https:///issues/438",
            "javascript:payload/issues/438",
            "https://github.com/wildcat-finance/skills/issues/4\n38",
            "https://github.com/wildcat-finance/skills/issues/0",
            "https://github.com/wildcat-finance/skills/issues/0438",
            "https://github.com/wildcat-finance/skills/issues/438/extra",
            "https://github.com/wildcat-finance/skills/pull/438",
        )
        for issue in invalid_issues:
            with self.subTest(issue=issue):
                proc = self.run_ctl(
                    "init", "--topic", "t", "--task-issue", issue, expect=2
                )
                self.assertIn("--task-issue", proc.stderr)
                root = os.path.join(self.target, ".hexaemeron")
                self.assertFalse(os.path.exists(os.path.join(root, "state.json")))
                self.assertFalse(os.path.exists(os.path.join(root, "ledger.jsonl")))

        issue = "https://github.com/wildcat-finance/skills/issues/438"
        for branch in ("release/438-prep", "fiat/prep", "fiat/1438-prep"):
            with self.subTest(branch=branch):
                proc = self.run_ctl(
                    "init", "--topic", "t", "--task-issue", issue,
                    "--run-branch", branch, expect=2,
                )
                self.assertIn("fiat/438-", proc.stderr)
                root = os.path.join(self.target, ".hexaemeron")
                self.assertFalse(os.path.exists(os.path.join(root, "state.json")))
                self.assertFalse(os.path.exists(os.path.join(root, "ledger.jsonl")))

    def test_task_issue_allows_an_exact_issue_bearing_override(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.run_ctl(
            "init", "--topic", "t", "--task-issue", issue,
            "--run-branch", "fiat/438-prep",
        )
        self.assertEqual(self.run_branch(), "fiat/438-prep")

    def test_task_issue_run_branch_propagates_to_step_directives(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.to_steps(("Scaffold", "Core"), task_issue=issue)
        first = self.next_json()
        self.assertEqual(first["run_branch"], "fiat/438-test-topic")
        self.assertEqual(first["branch"], "fiat/438-test-topic-step-1-scaffold")
        self.assertEqual(first["branch_from"], "fiat/438-test-topic")
        self.assertEqual(first["pr_base"], "fiat/438-test-topic")
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        self.finish_step(1)
        second = self.next_json()
        self.assertEqual(second["branch"], "fiat/438-test-topic-step-2-core")
        self.assertEqual(second["branch_from"], first["branch"])
        self.assertEqual(second["pr_base"], first["branch"])

    def test_task_issue_cannot_first_be_recorded_after_init(self):
        self.init()
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, "rb") as handle:
            state_before = handle.read()
        with open(ledger_path, "rb") as handle:
            ledger_before = handle.read()
        proc = self.run_ctl(
            "record", "task_issue",
            '"https://github.com/wildcat-finance/skills/issues/438"', expect=2,
        )
        self.assertIn("--task-issue", proc.stderr)
        with open(state_path, "rb") as handle:
            self.assertEqual(handle.read(), state_before)
        with open(ledger_path, "rb") as handle:
            self.assertEqual(handle.read(), ledger_before)

    def test_task_issue_repeat_is_idempotent_and_cannot_change(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.init(task_issue=issue)
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, "rb") as handle:
            state_before = handle.read()
        with open(ledger_path, "rb") as handle:
            ledger_before = handle.read()

        self.run_ctl("record", "task_issue", json.dumps(issue))
        proc = self.run_ctl(
            "record", "task_issue",
            '"https://github.com/wildcat-finance/skills/issues/439"', expect=2,
        )
        self.assertIn("cannot be changed", proc.stderr)
        with open(state_path, "rb") as handle:
            self.assertEqual(handle.read(), state_before)
        with open(ledger_path, "rb") as handle:
            self.assertEqual(handle.read(), ledger_before)

    def test_legacy_task_issue_state_keeps_its_stored_branch(self):
        issue = "https://github.com/wildcat-finance/skills/issues/438"
        self.to_steps(("One",))
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, encoding="utf-8") as handle:
            state = json.load(handle)
        state["receipts"]["task_issue"] = issue
        state["receipts"].pop("run_anchor")
        with open(ledger_path, encoding="utf-8") as handle:
            entries = [json.loads(line) for line in handle if line.strip()]
        controller = hexctl_module()
        entries[0]["data"].pop("run_anchor_sha256")
        previous = "genesis"
        for index, entry in enumerate(entries):
            entry["prev"] = previous
            entry.pop("hash")
            if index == len(entries) - 1:
                entry["state"] = controller.state_fingerprint(state)
            entry["hash"] = hashlib.sha256(
                controller.canonical(entry).encode()
            ).hexdigest()
            previous = entry["hash"]
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2)
            handle.write("\n")
        with open(ledger_path, "w", encoding="utf-8") as handle:
            for item in entries:
                handle.write(json.dumps(item, sort_keys=True) + "\n")

        self.run_ctl("verify")
        self.assertEqual(self.state()["run_branch"], "fiat/test-topic")
        directive = self.next_json()
        self.assertEqual(directive["run_branch"], "fiat/test-topic")
        self.assertEqual(directive["branch"], "fiat/test-topic-step-1-one")

    def test_named_run_branch_is_honoured_and_checked(self):
        proc = self.run_ctl("init", "--topic", "t", "--run-branch", "bad branch",
                            expect=2)
        self.assertIn("not a usable branch name", proc.stderr)
        proc = self.run_ctl("init", "--topic", "t", "--run-branch", "main",
                            "--base", "main", expect=2)
        self.assertIn("must differ from --base", proc.stderr)
        self.run_ctl("init", "--topic", "t", "--run-branch", "release/prep")
        self.assertEqual(self.run_branch(), "release/prep")

    def test_titleless_step_still_yields_a_usable_branch(self):
        self.to_steps(("###",))
        self.assertEqual(self.next_json()["branch"],
                         f"{self.run_branch()}-step-1-untitled")

    def test_step_branch_name_is_the_controller_s_to_give(self):
        self.to_steps(("Scaffold",))
        proc = self.run_ctl("done", "implement", "--branch", "step1",
                            "--commit", "abc123", expect=2)
        self.assertIn(self.step_branch(1), proc.stderr)

    def test_pre_stack_run_keeps_the_old_per_step_merge_contract(self):
        self.to_prose()
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        self.strip_run_branch()
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", expect=2,
        )
        self.assertIn("--merge-commit", proc.stderr)
        self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--merge-commit", "d" * 40,
        )
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("implement", 2))
        self.assertNotIn("pr_base", out)

    def test_recorded_task_issue_must_be_closed_before_the_run_completes(self):
        self.to_prose(task_issue="https://x/issues/74")
        self.run_ctl(
            "done", "prose", "--files", "1",
            "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate",
        )
        proc = self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
            "--closed-issue-url", "https://x/issues/74", expect=2,
        )
        self.assertIn("integrate phase", proc.stderr)
        self.run_ctl(
            "done", "push", "--pr-url", "https://github.com/wildcat-finance/example/pull/1",
            "--head-commit", "abc123", "--pr-base", self.step_base(1),
        )
        self.finish_step(2)
        self.merge_stack()
        self.assertIn(
            "--closed-issue-url", self.next_json()["then"]
        )
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "runmerge", expect=2,
        )
        self.assertIn("--closed-issue-url", proc.stderr)
        proc = self.run_ctl(
            "done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
            "--closed-issue-url", "https://x/issues/75", expect=2,
        )
        self.assertIn("does not match", proc.stderr)
        self.write_run_pr()
        self.run_ctl(
            "done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
            "--merge-commit", "f" * 40,
            "--closed-issue-url", "https://x/issues/74",
        )
        self.assertEqual(self.next_json()["do"], "done")

    def test_push_advances_steps_then_the_stack_integrates(self):
        self.to_steps(("One", "Two"))
        self.run_ctl("record", "security_suite", SUITE)
        run_branch = self.run_branch()
        first, second = self.step_branch(1), self.step_branch(2)
        self.finish_step(1)
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("implement", 2))
        self.finish_step(2)

        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("merge-step", 1))
        self.assertEqual((out["branch"], out["into"]), (first, run_branch))

        proc = self.run_ctl("done", "merge-step", "--step", "2",
                            "--merge-commit", "m2", expect=2)
        self.assertIn("step order", proc.stderr)
        proc = self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                            "--merge-commit", "runmerge", expect=2)
        self.assertIn("still has to merge", proc.stderr)

        self.run_ctl("done", "merge-step", "--step", "1", "--merge-commit", "1" * 40)
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("merge-step", 2))
        self.assertEqual((out["branch"], out["into"]), (second, run_branch))
        self.run_ctl("done", "merge-step", "--step", "2", "--merge-commit", "2" * 40)

        out = self.next_json()
        self.assertEqual(out["do"], "integrate")
        self.assertEqual((out["run_branch"], out["base"]), (run_branch, "main"))
        proc = self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                            expect=2)
        self.assertIn("--merge-commit", proc.stderr)
        self.write_run_pr()
        self.run_ctl("done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                     "--merge-commit", "f" * 40)
        self.assertEqual(self.next_json()["do"], "done")
        self.run_ctl("verify")

    def test_integrate_refuses_a_run_that_never_said_what_it_left_undone(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", SUITE)
        self.finish_step(1)
        self.merge_stack()
        args = ["done", "integrate", "--pr-url", "https://github.com/wildcat-finance/example/pull/2",
                "--merge-commit", "f" * 40]

        proc = self.run_ctl(*args, expect=2)
        self.assertIn("cannot be read", proc.stderr)

        self.write(os.path.join(".hexaemeron", "run-pr.md"),
                   "Run body with no section.\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("Carried forward", proc.stderr)

        self.write_run_pr(carried="\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("nothing under it", proc.stderr)

        # A later section cannot stand in for this one.
        self.write(os.path.join(".hexaemeron", "run-pr.md"),
                   "Run body.\n\n## Carried forward\n\n## Checks\n\n- root 38\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("nothing under it", proc.stderr)

        # Prose that names the item but disposes of nothing. The section is not
        # empty, so the older check passed it; the item still has no issue.
        self.write_run_pr(carried="- no CI workflow for this plugin yet\n")
        proc = self.run_ctl(*args, expect=2)
        self.assertIn("carries no `carryover` block", proc.stderr)
        self.assertIn("Integration cannot proceed", proc.stderr)

        self.write_run_pr(
            rows="plugin-ci-workflow | filed | "
                 "https://github.com/wildcat-finance/skills/issues/1041\n"
                 "xray-source-drift | duplicate | "
                 "https://github.com/wildcat-finance/skills/issues/842\n"
                 "comment-density-nit | none | fixed in the same commit\n"
        )
        self.run_ctl(*args)
        receipt = self.state()["receipts"]["integrate"]["carried_forward"]
        self.assertEqual(receipt["lines"], 5)
        self.assertEqual(receipt["path"], ".hexaemeron/run-pr.md")
        self.assertEqual(len(receipt["sha256"]), 64)
        self.assertEqual(receipt["filed"], ["plugin-ci-workflow"])
        self.assertEqual(receipt["duplicates"], ["xray-source-drift"])
        self.assertEqual(
            [row["id"] for row in receipt["carryover"]],
            ["plugin-ci-workflow", "xray-source-drift", "comment-density-nit"],
        )
        self.run_ctl("verify")

    def test_reset_refuses_a_run_whose_stack_has_not_landed(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", SUITE)
        self.finish_step(1)
        proc = self.run_ctl("reset", expect=2)
        self.assertIn("integrate", proc.stderr)


try:
    from .task_issue_closure_cases import build_task_issue_closure_tests
except ImportError:
    from task_issue_closure_cases import build_task_issue_closure_tests


TestTaskIssueClosure = build_task_issue_closure_tests(globals())


class TestControls(HexctlCase):
    def test_halt_blocks_progress_and_resume_restores(self):
        self.to_steps()
        self.run_ctl("halt", "--reason", "waiting on Oliver")
        self.assertEqual(self.next_json()["do"], "halted")
        proc = self.run_ctl("done", "implement", "--branch", "step-1",
                            "--commit", "abc123",
                            expect=2)
        self.assertIn("halted", proc.stderr)
        self.run_ctl("resume", "--note", "cleared")
        self.assertEqual(self.next_json()["do"], "implement")

    def test_verify_ok_and_tamper_detected(self):
        self.to_steps()
        self.run_ctl("verify")
        ledger = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(ledger) as fh:
            lines = fh.read().splitlines()
        entry = json.loads(lines[0])
        entry["data"]["topic"] = "someone edited history"
        lines[0] = json.dumps(entry, sort_keys=True)
        with open(ledger, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        proc = self.run_ctl("verify", expect=1)
        self.assertIn("chain broken", proc.stderr)

    def test_verify_preserves_receipt_assertions_without_proving_them(self):
        self.to_steps(("One",))
        assertion = "all dragons defeated"
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(1),
            "--commit",
            "abc123",
            "--tests",
            assertion,
        )
        self.run_ctl("verify")
        state = json.loads(self.run_ctl("status", "--json").stdout)
        receipt = state["steps"][0]["receipts"]["implement"]
        self.assertEqual(receipt["tests"], assertion)

    def test_record_and_status_json(self):
        self.init()
        self.run_ctl("record", "note", '"local run"')
        state = json.loads(self.run_ctl("status", "--json").stdout)
        self.assertEqual(state["receipts"]["note"], "local run")
        self.assertEqual(state["phase"], "study")

    def test_reset_archives_completed_run_and_allows_reinit(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", SUITE)
        self.finish_step(1)
        self.integrate_run()
        self.assertEqual(self.next_json()["do"], "done")

        # A worktree run archives into its starting checkout: archiving inside
        # the tree and then removing the tree would destroy the archive.
        root = os.path.join(self.dir, ".hexaemeron")
        self.run_ctl("reset")
        self.assertFalse(os.path.exists(os.path.join(root, "state.json")))
        archives = os.listdir(os.path.join(root, "archive"))
        self.assertEqual(len(archives), 1)
        archived = os.path.join(root, "archive", archives[0])
        self.assertTrue(os.path.exists(os.path.join(archived, "state.json")))
        self.assertTrue(os.path.exists(os.path.join(archived, "ledger.jsonl")))

        self.init("next topic")
        state = json.loads(self.run_ctl("status", "--json").stdout)
        self.assertEqual(state["topic"], "next topic")

    def test_reset_refuses_incomplete_run(self):
        self.init()
        proc = self.run_ctl("reset", expect=2)
        self.assertIn("refusing to reset an incomplete run", proc.stderr)
        self.assertEqual(self.next_json()["do"], "study")

    def test_config_get_set_roundtrip(self):
        self.init()
        self.run_ctl("config", "set", "git.draft_pr", "true")
        out = self.run_ctl("config", "get", "git.draft_pr").stdout.strip()
        self.assertEqual(out, "true")
        proc = self.run_ctl("config", "get", "audit.nope", expect=2)
        self.assertIn("not found", proc.stderr)

class TestFuzzRegressions(HexctlCase):
    """Pins for the day-5 fuzz findings (F-01..F-09)."""

    def state_file(self):
        return os.path.join(self.target, ".hexaemeron", "state.json")

    def ledger_file(self):
        return os.path.join(self.target, ".hexaemeron", "ledger.jsonl")

    def to_audit_with_suite(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '["x","y"]')

    def test_state_edit_detected_by_verify(self):
        self.to_audit_with_suite()
        self.run_ctl("audit-round", "--findings", "2",
                     "--fixes-commit", "fff", "--elenchus-verdict", "guarded")
        with open(self.state_file()) as fh:
            st = json.load(fh)
        st["steps"][0]["audit"]["rounds"][0]["findings"] = 0
        with open(self.state_file(), "w") as fh:
            json.dump(st, fh)
        proc = self.run_ctl("verify", expect=1)
        self.assertIn("edited outside hexctl", proc.stderr)

    def test_corrupt_state_dies_cleanly(self):
        self.to_audit_with_suite()
        with open(self.state_file(), "w") as fh:
            fh.write("{broken")
        for argv in (["status"], ["next"], ["record", "k", "v"]):
            proc = self.run_ctl(*argv, expect=1)
            self.assertNotIn("Traceback", proc.stderr)
            self.assertIn("unreadable", proc.stderr)

    def test_corrupt_ledger_dies_cleanly(self):
        self.to_audit_with_suite()
        with open(self.ledger_file(), "a") as fh:
            fh.write("garbage\n")
        proc = self.run_ctl("verify", expect=1)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("chain broken", proc.stderr)
        proc = self.run_ctl("record", "k", "v", expect=1)
        self.assertNotIn("Traceback", proc.stderr)

    def test_bad_steps_json_dies_cleanly(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        bad = self.write("bad.json", "{not json")
        proc = self.run_ctl("done", "runbook", "--artifact", runbook,
                            "--steps-file", bad, expect=2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("not valid JSON", proc.stderr)

    def test_blank_step_title_refused(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        sf = self.write("s.json", '["ok", "  "]')
        proc = self.run_ctl("done", "runbook", "--artifact", runbook,
                            "--steps-file", sf, expect=2)
        self.assertIn("non-empty", proc.stderr)

    def test_max_rounds_validated(self):
        self.to_audit_with_suite()
        self.record_legacy_config("audit.max_rounds", "eight")
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("must be an integer", proc.stderr)
        self.record_legacy_config("audit.max_rounds", 0)
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn(">= 1", proc.stderr)
        self.record_legacy_config("audit.max_rounds", 8)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("verify")

    def test_prose_nonstring_config_ids(self):
        self.to_audit_with_suite()
        self.record_legacy_config("skills.prose_lint", 123)
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")
        proc = self.run_ctl("done", "prose", "--files", "1",
                            "--skills", "hexaemeron:vulgate", expect=2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("123", proc.stderr)
        self.run_ctl("done", "prose", "--files", "1",
                     "--skills", "123,hexaemeron:vulgate")

    def test_record_reserved_keys_refused(self):
        self.to_audit_with_suite()
        proc = self.run_ctl("record", "study", '"forged"', expect=2)
        self.assertIn("phase receipt", proc.stderr)

    def test_status_strips_control_chars(self):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        sf = self.write("s.json", json.dumps(["\u001b[31mEVIL\u001b[0m step"]))
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", sf)
        proc = self.run_ctl("status")
        self.assertNotIn("\x1b", proc.stdout)


class StateContainerValidationTests(HexctlCase):
    """Every state-backed command crosses one ordered, value-free shape gate."""

    def setUp(self):
        super().setUp()
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)
        self.run_ctl("audit-round", "--findings", "1")
        self.state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        self.ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(self.state_path, "rb") as handle:
            self.valid_state_bytes = handle.read()
        with open(self.ledger_path, "rb") as handle:
            self.valid_ledger_bytes = handle.read()

    @staticmethod
    def replace_at(state, parts, value):
        node = state
        for part in parts[:-1]:
            node = node[part]
        node[parts[-1]] = value

    @staticmethod
    def remove_at(state, parts):
        node = state
        for part in parts[:-1]:
            node = node[part]
        del node[parts[-1]]

    def write_state(self, state):
        with open(self.state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle)

    def assert_command_parity(self, state, path, kind):
        self.write_state(state)
        with open(self.state_path, "rb") as handle:
            state_before = handle.read()
        expected = f"hexctl: error: state key '{path}' must be an {kind}\n"
        commands = (
            ("status",),
            ("next",),
            ("verify",),
            ("record", "shape_probe", '"secret-shaped-value"'),
        )
        for command in commands:
            with self.subTest(path=path, kind=kind, command=command[0]):
                proc = self.run_ctl(*command, expect=1)
                self.assertEqual(proc.stdout, "")
                self.assertEqual(proc.stderr, expected)
                self.assertNotIn("secret-shaped-value", proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)
                with open(self.state_path, "rb") as handle:
                    self.assertEqual(handle.read(), state_before)
                with open(self.ledger_path, "rb") as handle:
                    self.assertEqual(handle.read(), self.valid_ledger_bytes)

    def test_required_container_matrix_is_shared_by_every_command(self):
        cases = (
            ("config", "object", ("config",), []),
            ("config.skills", "object", ("config", "skills"), []),
            ("config.audit", "object", ("config", "audit"), []),
            ("config.git", "object", ("config", "git"), []),
            ("receipts", "object", ("receipts",), []),
            ("steps", "array", ("steps",), {}),
            ("steps[0].receipts", "object", ("steps", 0, "receipts"), []),
            ("steps[0].audit", "object", ("steps", 0, "audit"), []),
            (
                "steps[0].audit.rounds",
                "array",
                ("steps", 0, "audit", "rounds"),
                {},
            ),
        )
        self.assert_command_parity([], "$", "object")
        for path, kind, parts, wrong_kind in cases:
            with self.subTest(path=path, specimen="missing"):
                state = json.loads(self.valid_state_bytes)
                self.remove_at(state, parts)
                self.assert_command_parity(state, path, kind)
            with self.subTest(path=path, specimen="wrong-kind"):
                state = json.loads(self.valid_state_bytes)
                self.replace_at(state, parts, wrong_kind)
                self.assert_command_parity(state, path, kind)

        member_cases = (
            ("steps[0]", "object", ("steps", 0)),
            ("steps[1]", "object", ("steps", 1)),
            (
                "steps[0].audit.rounds[0]",
                "object",
                ("steps", 0, "audit", "rounds", 0),
            ),
        )
        for path, kind, parts in member_cases:
            with self.subTest(path=path, specimen="wrong-kind"):
                state = json.loads(self.valid_state_bytes)
                self.replace_at(state, parts, "secret-shaped-value")
                self.assert_command_parity(state, path, kind)

    def test_first_fault_follows_the_documented_order(self):
        cases = []

        state = json.loads(self.valid_state_bytes)
        del state["config"]
        state["receipts"] = []
        state["steps"] = {}
        cases.append((state, "config", "object"))

        state = json.loads(self.valid_state_bytes)
        state["config"]["skills"] = []
        state["receipts"] = []
        cases.append((state, "config.skills", "object"))

        state = json.loads(self.valid_state_bytes)
        state["steps"][0]["receipts"] = []
        state["steps"][0]["audit"] = []
        cases.append((state, "steps[0].receipts", "object"))

        state = json.loads(self.valid_state_bytes)
        state["steps"][0]["receipts"] = []
        state["steps"][1] = "secret-shaped-value"
        cases.append((state, "steps[1]", "object"))

        for state, path, kind in cases:
            with self.subTest(path=path):
                self.assert_command_parity(state, path, kind)

    def test_version_one_legacy_and_heterogeneous_receipts_still_load(self):
        state = json.loads(self.valid_state_bytes)
        state.pop("frontier")
        state.pop("run_branch")
        state["steps"][0]["phase"] = "issue"
        state["receipts"]["legacy_null"] = None
        state["receipts"]["legacy_list"] = [1, "two", {"three": True}]
        state["steps"][0]["receipts"]["legacy_scalar"] = 7
        state["steps"][0]["audit"]["rounds"][0]["legacy_leaf"] = [None]
        self.write_state(state)

        loaded = hexctl_module().load_state(self.target)

        self.assertEqual(loaded, state)
        self.assertEqual(loaded["version"], 1)


class AuditFilterReceiptTests(HexctlCase):
    """The exact Sapheneia declaration is visible, checked, and retained."""

    def to_receiptable_audit(self, *, solidity=True):
        self.to_audit()
        receipt = SUITE if solidity else '"waived: prose-only repo"'
        self.run_ctl("record", "security_suite", receipt)

    def state_ledger_digests(self):
        paths = (
            os.path.join(self.target, ".hexaemeron", "state.json"),
            os.path.join(self.target, ".hexaemeron", "ledger.jsonl"),
        )
        digests = []
        for path in paths:
            with open(path, "rb") as handle:
                digests.append(hashlib.sha256(handle.read()).hexdigest())
        return tuple(digests)

    def audit_events(self):
        path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        entries = []
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                entry = json.loads(line)
                if entry["event"] == "audit-round":
                    entries.append(entry)
        return entries

    def test_missing_declaration_is_refused_without_state_or_ledger_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "0", expect=2, audit_filter=False
        )
        self.assertIn("--audit-filter sapheneia:sapheneia", result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_different_declaration_is_refused_without_state_or_ledger_drift(self):
        self.to_receiptable_audit()
        before = self.state_ledger_digests()
        result = self.run_ctl(
            "audit-round", "--findings", "0",
            "--audit-filter", "something:else", expect=2,
        )
        self.assertIn("must equal sapheneia:sapheneia", result.stderr)
        self.assertEqual(self.state_ledger_digests(), before)

    def test_exact_declaration_reaches_round_state_ledger_and_stdout(self):
        self.to_receiptable_audit()
        result = self.run_ctl("audit-round", "--findings", "0", *AUDIT_FILTER)
        self.assertIn("audit filter sapheneia:sapheneia", result.stdout)
        round_entry = self.state()["steps"][0]["audit"]["rounds"][0]
        self.assertEqual(round_entry["audit_filter"], "sapheneia:sapheneia")
        self.assertEqual(
            self.audit_events()[0]["data"]["audit_filter"],
            "sapheneia:sapheneia",
        )

    def test_next_and_warden_brief_name_the_exact_obligation_every_round(self):
        self.to_receiptable_audit()
        expected = {
            "flag": "--audit-filter",
            "value": "sapheneia:sapheneia",
        }
        first = self.next_json()
        self.assertEqual(first["audit_filter"], expected)
        self.assertEqual(first["brief"]["audit_filter"], expected)
        self.run_ctl("audit-round", "--findings", "1", *AUDIT_FILTER)
        second = self.next_json()
        self.assertEqual(second["round"], 2)
        self.assertEqual(second["audit_filter"], expected)
        self.assertEqual(second["brief"]["audit_filter"], expected)

    def test_non_solidity_round_needs_the_same_exact_declaration(self):
        self.to_receiptable_audit(solidity=False)
        self.run_ctl(
            "audit-round", "--findings", "0", *AUDIT_FILTER, *LINTS_CLEAN
        )
        self.assertEqual(
            self.state()["steps"][0]["audit"]["rounds"][0]["audit_filter"],
            "sapheneia:sapheneia",
        )


class LintReceiptTests(HexctlCase):
    """The three lint results a non-Solidity round owes, and the refusals."""

    def to_waived_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')

    def to_solidity_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", SUITE)

    def rounds(self):
        return self.state()["steps"][0]["audit"]["rounds"]

    def test_a_non_solidity_round_is_refused_without_any_of_the_three(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", expect=2)
        for lint in ("phylax", "ephoros", "hypomnema"):
            self.assertIn(f"--{lint}-exit", proc.stderr)

    def test_the_refusal_names_only_what_is_still_missing(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0",
                            "--phylax-exit", "0", "--ephoros-exit", "0", expect=2)
        self.assertIn("--hypomnema-exit", proc.stderr)
        self.assertNotIn("--phylax-exit", proc.stderr)
        self.assertNotIn("--ephoros-exit", proc.stderr)

    def test_the_refusal_points_at_the_immutable_classification(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", expect=2)
        self.assertIn("security_suite receipt", proc.stderr)
        self.assertIn("Solidity config is immutable", proc.stderr)

    def test_a_complete_round_records_all_three(self):
        self.to_waived_audit()
        out = self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN).stdout
        self.assertIn("lints phylax 0, ephoros 0, hypomnema 0", out)
        self.assertEqual(
            self.rounds()[0]["lints"],
            {"phylax": 0, "ephoros": 0, "hypomnema": 0},
        )

    def test_a_recorded_non_zero_exit_survives_onto_the_round(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "3",
                     "--phylax-exit", "1", "--ephoros-exit", "0", "--hypomnema-exit", "2")
        self.assertEqual(
            self.rounds()[0]["lints"], {"phylax": 1, "ephoros": 0, "hypomnema": 2}
        )

    def test_zero_findings_beside_a_failing_lint_is_refused(self):
        """A non-zero lint exit is a finding like any other, so the two halves of the
        receipt would otherwise contradict each other."""
        self.to_waived_audit()
        for flag in ("--phylax-exit", "--ephoros-exit", "--hypomnema-exit"):
            with self.subTest(flag=flag):
                args = ["audit-round", "--findings", "0", *LINTS_CLEAN]
                args[args.index(flag) + 1] = "1"
                proc = self.run_ctl(*args, expect=2)
                self.assertIn("0 findings", proc.stderr)
                self.assertIn("finding like any other", proc.stderr)

    def test_a_failing_lint_with_findings_recorded_is_accepted(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "1",
                     "--phylax-exit", "1", "--ephoros-exit", "0", "--hypomnema-exit", "0")
        self.assertEqual(self.rounds()[0]["findings"], 1)

    def test_a_negative_exit_is_refused(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "-1",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("non-negative exit status", proc.stderr)

    def test_a_non_integer_exit_is_refused_by_the_parser(self):
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "clean",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("invalid int value", proc.stderr)

    def test_a_solidity_round_needs_none_of_them(self):
        self.to_solidity_audit()
        self.run_ctl("audit-round", "--findings", "0")
        self.assertIsNone(self.rounds()[0]["lints"])

    def test_a_solidity_round_may_still_record_them(self):
        self.to_solidity_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.assertEqual(
            self.rounds()[0]["lints"], {"phylax": 0, "ephoros": 0, "hypomnema": 0}
        )

    def test_the_consistency_rule_applies_to_a_solidity_round_too(self):
        """If the exits are recorded at all, they have to agree with the count."""
        self.to_solidity_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "1",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("finding like any other", proc.stderr)

    def test_the_override_lifts_the_requirement(self):
        self.to_waived_audit()
        self.record_legacy_config("solidity", True)
        self.run_ctl("audit-round", "--findings", "0")
        self.assertIsNone(self.rounds()[0]["lints"])

    def test_the_override_can_impose_it_on_a_recorded_suite(self):
        self.to_solidity_audit()
        self.record_legacy_config("solidity", False)
        proc = self.run_ctl("audit-round", "--findings", "0", expect=2)
        self.assertIn("--phylax-exit", proc.stderr)

    def test_next_names_the_flags_a_non_solidity_round_owes(self):
        self.to_waived_audit()
        out = self.next_json()
        self.assertEqual(out["do"], "audit-round")
        self.assertEqual(
            out["lints"], ["--phylax-exit", "--ephoros-exit", "--hypomnema-exit"]
        )

    def test_next_stays_quiet_about_lints_on_a_solidity_round(self):
        self.to_solidity_audit()
        self.assertNotIn("lints", self.next_json())

    def test_next_still_names_them_on_a_later_round(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "2", *LINTS_CLEAN)
        out = self.next_json()
        self.assertEqual(out["round"], 2)
        self.assertEqual(out["prior_findings"], 2)
        self.assertIn("--phylax-exit", out["lints"])

    def test_closing_the_audit_reads_a_round_that_carries_lints(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit")
        self.assertEqual(self.state()["steps"][0]["phase"], "prose")

    def test_a_clean_close_now_implies_the_lints_passed(self):
        """An emergent property worth pinning. `done audit` calls a close clean when the
        last round found nothing, and the consistency rule forbids a zero findings count
        beside a non-zero exit, so a clean close cannot sit on a failing lint. Nothing
        asserted that, and it is the property the whole change buys."""
        self.to_waived_audit()
        proc = self.run_ctl("audit-round", "--findings", "0", "--phylax-exit", "1",
                            "--ephoros-exit", "0", "--hypomnema-exit", "0", expect=2)
        self.assertIn("finding like any other", proc.stderr)

        self.run_ctl("audit-round", "--findings", "1", "--phylax-exit", "1",
                     "--ephoros-exit", "0", "--hypomnema-exit", "0")
        blocked = self.run_ctl("done", "audit", expect=2)
        self.assertIn("open", blocked.stderr)

        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.run_ctl("done", "audit", "--fixes-ref", "deadbeef")
        receipt = self.state()["steps"][0]["receipts"]["audit"]
        self.assertTrue(receipt["clean"])
        rounds = self.rounds()
        self.assertEqual(rounds[-1]["findings"], 0)
        self.assertEqual(set(rounds[-1]["lints"].values()), {0})

    def test_a_round_recorded_before_this_existed_still_reads(self):
        """Rounds already on disk carry no lints key. Every reader has to treat it as
        absent rather than assume it."""
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state["steps"][0]["audit"]["rounds"][0].pop("lints")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        self.run_ctl("status")
        self.run_ctl("next")
        self.run_ctl("done", "audit")
        self.assertEqual(self.state()["steps"][0]["phase"], "prose")


class RoundClassifierTests(unittest.TestCase):
    """Which rounds have to carry lint results, and why."""

    @classmethod
    def setUpClass(cls):
        cls.ctl = hexctl_module()

    def classify(self, suite=..., mode="auto"):
        receipts = {} if suite is ... else {"security_suite": suite}
        return self.ctl.solidity_round({"config": {"solidity": mode}, "receipts": receipts})

    def test_a_waiver_means_the_lints_are_the_mechanical_part(self):
        self.assertFalse(self.classify("waived: prose-only repo"))

    def test_a_waiver_is_recognised_whatever_its_case_and_spacing(self):
        for value in ("waived: x", "Waived: x", "  WAIVED: x  ", "waived x"):
            with self.subTest(receipt=value):
                self.assertFalse(self.classify(value))

    def test_a_recorded_suite_means_the_pashov_pair_ran(self):
        self.assertTrue(self.classify(["hexaemeron:x-ray", "hexaemeron:solidity-auditor"]))

    def test_an_empty_suite_list_is_not_a_suite_that_ran(self):
        """Recording no ids is not recording a suite. Demanding the lints is the safe
        direction when the receipt cannot be read as one."""
        self.assertFalse(self.classify([]))

    def test_a_receipt_that_is_neither_demands_the_lints(self):
        for value in ("suite", 7, {"suite": True}, None, True):
            with self.subTest(receipt=value):
                self.assertFalse(self.classify(value))

    def test_a_missing_receipt_infers_nothing(self):
        """`cmd_audit_round` refuses a missing receipt before asking this, so the
        classifier must not invent a requirement out of its absence."""
        self.assertTrue(self.classify())

    def test_the_config_key_overrides_the_receipt_in_both_directions(self):
        self.assertTrue(self.classify("waived: x", mode=True))
        self.assertFalse(self.classify(["hexaemeron:x-ray"], mode=False))

    def test_the_default_mode_is_auto(self):
        self.assertEqual(self.ctl.DEFAULT_CONFIG["solidity"], "auto")

    def test_the_waiver_prefix_is_what_preflight_writes(self):
        self.assertTrue("waived: reason".startswith(self.ctl.WAIVER_PREFIX))

    def test_the_three_lints_are_named_once(self):
        self.assertEqual(self.ctl.LINTS, ("phylax", "ephoros", "hypomnema"))

    def test_a_waiver_is_its_first_word_not_merely_a_prefix(self):
        """`startswith` alone read `waivedX` and `waived-ish` as waivers, which is not
        what the rule beside WAIVER_PREFIX says."""
        for value in ("waived: x", "waived", "  WAIVED: y  ", "waived x"):
            with self.subTest(receipt=value, expect=True):
                self.assertTrue(self.ctl.is_waiver(value))
        for value in ("waivedX", "waived-ish", "waivers: x", "unwaived: x", "not waived", ""):
            with self.subTest(receipt=value, expect=False):
                self.assertFalse(self.ctl.is_waiver(value))

    def test_direct_classifier_calls_with_non_object_containers_do_not_raise(self):
        """The load boundary rejects these shapes for state-backed commands.

        Keep the classifier itself total for isolated callers and optional leaves.
        """
        for config in (None, [], "auto", 7):
            with self.subTest(config=config):
                self.assertIsInstance(
                    self.ctl.solidity_round({"config": config, "receipts": {}}), bool
                )
        for receipts in (None, [], "waived", 7):
            with self.subTest(receipts=receipts):
                self.assertIsInstance(
                    self.ctl.solidity_round(
                        {"config": {"solidity": "auto"}, "receipts": receipts}
                    ),
                    bool,
                )
        self.assertIsInstance(self.ctl.solidity_round({}), bool)

    def test_as_dict_defeats_a_stored_null(self):
        """d.get(key, {}) returns the stored value when the key exists, so a state
        holding "integrate": null defeated the default and the next .get raised. Four
        chained reads in the controller had that shape."""
        for value in (None, [], "x", 7, True):
            with self.subTest(value=value):
                self.assertEqual(self.ctl.as_dict(value), {})
        self.assertEqual(self.ctl.as_dict({"a": 1}), {"a": 1})

    def test_no_chained_read_uses_a_container_default(self):
        """The pattern this run removed, asserted against the source so it does not
        come back: `.get(x, {}).` and `.get(x, []).` are both defeated by a stored
        null."""
        import re

        with open(HEXCTL, encoding="utf-8") as fh:
            source = fh.read()
        offenders = re.findall(r"\.get\([^)]*,\s*(?:\{\}|\[\])\)\s*\.", source)
        self.assertEqual(offenders, [], "use as_dict() instead")

    def test_an_integer_is_not_a_mode(self):
        for value in (0, 1, 2):
            with self.subTest(value=value):
                self.assertFalse(self.ctl.solidity_mode(value))
        for value in (True, False, "auto"):
            with self.subTest(value=value):
                self.assertTrue(self.ctl.solidity_mode(value))


if __name__ == "__main__":
    unittest.main(verbosity=2)


class StaleControllerTests(OriginCheckoutMixin, unittest.TestCase):
    """A run driven by an installed plugin older than the repository it edits.

    A marketplace plugin is installed from a published copy, so a repository that
    also holds Fiat's source can be a whole evolution ahead of the controller
    driving the run. Every rule the newer one enforces then goes unenforced, and
    the receipt cannot show it: a flag the controller does not accept looks
    exactly like a rule nobody wrote. This shipped after a run recorded its lint
    results as prose because the installed `audit-round` was a version behind the
    flags its own ledger documented.
    """

    def _repo(self, directory, version):
        path = os.path.join(
            directory, "plugins", "hexaemeron", "skills", "fiat"
        )
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "EVOLUTION.md"), "w", encoding="utf-8") as fh:
            fh.write(f"- Current version: `{version}`\n")
        return directory

    def test_ledger_version_reads_the_declared_version(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "EVOLUTION.md")
            with open(path, "w", encoding="utf-8") as fh:
                fh.write("# Ledger\n\n- Current version: `fiat-v4.4.1`\n- Frontier status: `open`\n")
            self.assertEqual(module.ledger_version(path), "fiat-v4.4.1")

    def test_ledger_version_is_none_when_absent_or_unreadable(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as directory:
            missing = os.path.join(directory, "nope.md")
            self.assertIsNone(module.ledger_version(missing))
            empty = os.path.join(directory, "empty.md")
            with open(empty, "w", encoding="utf-8") as fh:
                fh.write("# Ledger\n\nno version line here\n")
            self.assertIsNone(module.ledger_version(empty))

    def test_a_newer_checked_in_copy_is_reported(self):
        module = hexctl_module()
        running = module.ledger_version(
            os.path.join(os.path.dirname(HEXCTL), os.pardir, "EVOLUTION.md")
        )
        self.assertIsNotNone(running)
        with tempfile.TemporaryDirectory() as directory:
            self._repo(directory, "fiat-v99.9.9")
            found = module.stale_controller(directory)
        self.assertIsNotNone(found)
        self.assertEqual(found[0], running)
        self.assertEqual(found[1], "fiat-v99.9.9")
        self.assertIn("EVOLUTION.md", found[2])

    def test_matching_versions_are_silent(self):
        module = hexctl_module()
        running = module.ledger_version(
            os.path.join(os.path.dirname(HEXCTL), os.pardir, "EVOLUTION.md")
        )
        with tempfile.TemporaryDirectory() as directory:
            self._repo(directory, running)
            self.assertIsNone(module.stale_controller(directory))

    def test_a_target_without_fiat_is_silent(self):
        module = hexctl_module()
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(module.stale_controller(directory))

    def test_the_plugins_own_source_tree_is_not_compared_against_itself(self):
        """Running Fiat on the repository that holds it must not warn.

        The candidate it would find is the very ledger it just read, so a naive
        comparison is silent only by luck of the versions matching. It is skipped
        by identity instead.
        """
        module = hexctl_module()
        target = os.path.realpath(os.path.join(HERE, "..", "..", ".."))
        own = os.path.join(target, "plugins", "hexaemeron", "skills", "fiat", "EVOLUTION.md")
        if not os.path.isfile(own):
            self.skipTest("not running from the plugin's own checkout")
        self.assertIsNone(module.stale_controller(target))

    def test_init_warns_on_stderr_without_failing_the_run(self):
        module_dir = tempfile.mkdtemp()
        try:
            make_origin_checkout(module_dir)
            self._repo(module_dir, "fiat-v99.9.9")
            done = subprocess.run(
                [sys.executable, HEXCTL, "--dir", module_dir, "init",
                 "--topic", "stale probe", "--base", "main"],
                capture_output=True, text=True,
            )
            self.assertEqual(done.returncode, 0, done.stderr)
            self.assertIn("warning", done.stderr)
            self.assertIn("fiat-v99.9.9", done.stderr)
            self.assertIn("initialised", done.stdout)
            # A warning that does not say what to do gets read and ignored.
            self.assertIn("plugin-currency.md", done.stderr)
            self.assertIn("controller_version", done.stderr)
        finally:
            import shutil
            shutil.rmtree(module_dir, ignore_errors=True)


LEDGER_HEADER = """# Widget evolution ledger

- Current version: `{version}`
- Frontier status: `{status}`
- Frontier revision: `{revision}`
- Current frontier: {frontier}
- Next Fiat job: {job}

## History

| Version | Axis | Frontier revision | Frontier SHA-256 | Evidence | Change |
| --- | --- | --- | --- | --- | --- |
"""


def widget_ledger(path, rows, *, version, status="open", revision="held-thing",
                  frontier="The widget does not do the thing.",
                  job="Make the widget do the thing."):
    """A governed ledger with the header and rows a caller dictates."""
    text = LEDGER_HEADER.format(version=version, status=status, revision=revision,
                                frontier=frontier, job=job) + "".join(rows)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return text


def frontier_digest(status, revision, frontier, job):
    return hashlib.sha256(
        ("|".join((status, revision, frontier, job)) + "\n").encode("utf-8")
    ).hexdigest()


def row(version, axis, revision, digest, change="Did the thing."):
    return f"| `{version}` | {axis} | `{revision}` | `{digest}` | [e](f) | {change} |\n"


class FrontierGateTests(OriginCheckoutMixin, unittest.TestCase):
    """A frontier run proves its ledger update instead of asserting it.

    The maturity gate says to update the ledger exactly once per completed
    frontier job, in prose. This repository has already had to reconstruct two
    broken evolutions, so the terminal receipt now refuses until the ledger
    carries exactly one new row valid under the versioning contract.
    """

    HELD = ("open", "held-thing", "The widget does not do the thing.",
            "Make the widget do the thing.")
    NEXT = ("open", "new-thing", "The widget does the thing; the next is undone.",
            "Make the widget do the next thing.")

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        make_origin_checkout(self.dir)
        self.ledger = os.path.join(
            self.dir, "plugins", "demo", "skills", "widget", "EVOLUTION.md")
        self.base_digest = frontier_digest(*self.HELD)
        self.base_row = row("widget-v1.1.0", "baseline", self.HELD[1],
                            self.base_digest, "Versioning starts here.")
        widget_ledger(self.ledger, [self.base_row], version="widget-v1.1.0",
                      status=self.HELD[0], revision=self.HELD[1],
                      frontier=self.HELD[2], job=self.HELD[3])
        with open(self.ledger, "rb") as handle:
            ledger_sha256 = hashlib.sha256(handle.read()).hexdigest()
        self.before = {
            "ledger": os.path.relpath(self.ledger, self.dir),
            "sha256": ledger_sha256,
            "rows": 1,
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def fault(self):
        return hexctl_module().frontier_close_fault(self.ledger, self.before)

    def close_with(self, version, axis, header=None, digest=None, extra=()):
        header = header or self.NEXT
        widget_ledger(
            self.ledger,
            [self.base_row, row(version, axis, header[1],
                                digest or frontier_digest(*header)), *extra],
            version=version, status=header[0], revision=header[1],
            frontier=header[2], job=header[3])

    def test_an_untouched_ledger_is_refused(self):
        self.assertIn("byte-for-byte what it was at init", self.fault())

    def test_a_correct_evolution_row_closes(self):
        self.close_with("widget-v2.1.0", "evolution")
        self.assertIsNone(self.fault())

    def test_a_wrong_digest_is_refused(self):
        self.close_with("widget-v2.1.0", "evolution", digest="0" * 64)
        self.assertIn("digest does not match", self.fault())

    def test_wrong_axis_arithmetic_is_refused(self):
        self.close_with("widget-v9.1.0", "evolution")
        self.assertIn("must be widget-v2.1.0", self.fault())

    def test_two_new_rows_are_refused(self):
        self.close_with("widget-v2.1.0", "evolution",
                        extra=[row("widget-v3.1.0", "evolution", self.NEXT[1],
                                   frontier_digest(*self.NEXT))])
        self.assertIn("gained 2 history row(s)", self.fault())

    def test_a_generation_must_hold_the_frontier(self):
        # Same axis arithmetic, but the revision moved, which a generation may
        # not do: the held target has to survive it byte for byte.
        self.close_with("widget-v1.2.0", "generation")
        self.assertIn("retain the prior frontier revision", self.fault())

    def test_a_generation_holding_the_frontier_closes(self):
        self.close_with("widget-v1.2.0", "generation", header=self.HELD)
        self.assertIsNone(self.fault())

    def test_a_header_row_mismatch_is_refused(self):
        widget_ledger(
            self.ledger,
            [self.base_row, row("widget-v2.1.0", "evolution", self.NEXT[1],
                                frontier_digest(*self.NEXT))],
            version="widget-v7.7.7", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("they have to be the same row", self.fault())

    def test_a_mature_frontier_needs_no_next_job(self):
        mature = ("mature", "new-thing", "Nothing evidenced remains.",
                  "Make the widget do the next thing.")
        self.close_with("widget-v2.1.0", "evolution", header=mature)
        self.assertIn("`None -- mature`", self.fault())

    def test_a_mature_frontier_with_none_closes(self):
        mature = ("mature", "new-thing", "Nothing evidenced remains.",
                  "None -- mature")
        self.close_with("widget-v2.1.0", "evolution", header=mature)
        self.assertIsNone(self.fault())

    def test_an_unreadable_ledger_is_reported_not_raised(self):
        os.remove(self.ledger)
        self.assertIn("cannot be read", self.fault())

    def test_init_refuses_a_frontier_that_is_not_a_ledger(self):
        plain = os.path.join(self.dir, "notes.md")
        with open(plain, "w", encoding="utf-8") as fh:
            fh.write("# notes\n\nno version line\n")
        done = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "t",
             "--base", "main", "--frontier", "notes.md"],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 2)
        self.assertIn("states no `Current version`", done.stderr)

    def test_init_without_frontier_records_none(self):
        done = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "t",
             "--base", "main"], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertNotIn("frontier run:", done.stdout)
        with open(os.path.join(self.target, ".hexaemeron", "state.json"),
                  encoding="utf-8") as fh:
            self.assertIsNone(json.load(fh)["frontier"])

    def test_init_in_frontier_mode_records_and_announces(self):
        done = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "t",
             "--base", "main", "--frontier", self.before["ledger"]],
            capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("frontier run:", done.stdout)
        self.assertIn("widget-v1.1.0", done.stdout)
        with open(os.path.join(self.target, ".hexaemeron", "state.json"),
                  encoding="utf-8") as fh:
            held = json.load(fh)["frontier"]
        self.assertEqual(held["rows"], 1)
        self.assertEqual(held["sha256"], self.before["sha256"])


def compact_row(version, axis, revision, digest, change="Did the thing."):
    return f"- `{version}` | {axis} | `{revision}` | `{digest}` | [e](f) | {change}\n"


class LedgerRowShapeTests(unittest.TestCase):
    """The gate and the suite parse the same row set, whichever shape a
    ledger spells its history in.

    tests/test_evolution_contract.py accepts a table row and a compact bullet
    row; the issue 322 run halted because the gate read only the first, saw a
    two-row ledger as empty at init, and refused the one real new row at
    integrate (skills#443).
    """

    def test_a_compact_bullet_row_parses(self):
        digest = "a" * 64
        rows = hexctl_module().ledger_rows(
            compact_row("example-v0.1.0", "baseline", "held-job", digest))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["version"], "example-v0.1.0")
        self.assertEqual(rows[0]["digest"], digest)

    def test_a_table_row_still_parses(self):
        digest = "b" * 64
        rows = hexctl_module().ledger_rows(
            row("example-v0.1.0", "baseline", "held-job", digest))
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["version"], "example-v0.1.0")

    def test_the_gate_parses_every_governed_ledger_in_the_tree(self):
        repo = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ledgers = sorted(
            glob.glob(os.path.join(repo, "plugins", "*", "skills", "*", "EVOLUTION.md")))
        self.assertTrue(ledgers)
        module = hexctl_module()
        for ledger in ledgers:
            with self.subTest(ledger=os.path.relpath(ledger, repo)):
                with open(ledger, encoding="utf-8") as fh:
                    text = fh.read()
                self.assertTrue(
                    module.ledger_rows(text),
                    "a governed ledger parsed as having no history rows")


class FrontierGateCompactTests(FrontierGateTests):
    """The whole gate, over a ledger spelled in the compact bullet shape."""

    def setUp(self):
        super().setUp()
        self.base_row = compact_row(
            "widget-v1.1.0", "baseline", self.HELD[1], self.base_digest,
            "Versioning starts here.")
        widget_ledger(self.ledger, [self.base_row], version="widget-v1.1.0",
                      status=self.HELD[0], revision=self.HELD[1],
                      frontier=self.HELD[2], job=self.HELD[3])
        with open(self.ledger, "rb") as handle:
            self.before["sha256"] = hashlib.sha256(handle.read()).hexdigest()

    def close_with(self, version, axis, header=None, digest=None, extra=()):
        header = header or self.NEXT
        widget_ledger(
            self.ledger,
            [self.base_row, compact_row(version, axis, header[1],
                                        digest or frontier_digest(*header)),
             *extra],
            version=version, status=header[0], revision=header[1],
            frontier=header[2], job=header[3])

    def test_two_new_rows_are_refused(self):
        self.close_with("widget-v2.1.0", "evolution",
                        extra=[compact_row("widget-v3.1.0", "evolution",
                                           self.NEXT[1],
                                           frontier_digest(*self.NEXT))])
        self.assertIn("gained 2 history row(s)", self.fault())

    def test_a_header_row_mismatch_is_refused(self):
        widget_ledger(
            self.ledger,
            [self.base_row, compact_row("widget-v2.1.0", "evolution",
                                        self.NEXT[1],
                                        frontier_digest(*self.NEXT))],
            version="widget-v7.7.7", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("they have to be the same row", self.fault())


class FrontierGateLegacySnapshotTests(OriginCheckoutMixin, unittest.TestCase):
    """A snapshot taken while the gate could not see compact rows counted a
    real history as empty. The gate anchors on the init-time version instead
    of trusting that count, so such a run can still close honestly."""

    HELD = FrontierGateTests.HELD
    NEXT = FrontierGateTests.NEXT

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        make_origin_checkout(self.dir)
        self.ledger = os.path.join(
            self.dir, "plugins", "demo", "skills", "widget", "EVOLUTION.md")
        digest = frontier_digest(*self.HELD)
        self.rows = [
            compact_row("widget-v0.1.0", "baseline", self.HELD[1], digest,
                        "Versioning starts here."),
            compact_row("widget-v1.1.0", "evolution", self.HELD[1], digest),
        ]
        widget_ledger(self.ledger, self.rows, version="widget-v1.1.0",
                      status=self.HELD[0], revision=self.HELD[1],
                      frontier=self.HELD[2], job=self.HELD[3])
        with open(self.ledger, "rb") as handle:
            ledger_sha256 = hashlib.sha256(handle.read()).hexdigest()
        self.before = {
            "ledger": os.path.relpath(self.ledger, self.dir),
            "sha256": ledger_sha256,
            "rows": 0,
            "version_at_init": "widget-v1.1.0",
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def fault(self):
        return hexctl_module().frontier_close_fault(self.ledger, self.before)

    def test_one_row_after_the_init_version_closes(self):
        widget_ledger(
            self.ledger,
            [*self.rows, compact_row("widget-v2.1.0", "evolution", self.NEXT[1],
                                     frontier_digest(*self.NEXT))],
            version="widget-v2.1.0", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIsNone(self.fault())

    def test_two_rows_after_the_init_version_are_refused(self):
        widget_ledger(
            self.ledger,
            [*self.rows,
             compact_row("widget-v2.1.0", "evolution", self.NEXT[1],
                         frontier_digest(*self.NEXT)),
             compact_row("widget-v3.1.0", "evolution", self.NEXT[1],
                         frontier_digest(*self.NEXT))],
            version="widget-v3.1.0", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("gained 2 history row(s)", self.fault())

    def test_a_vanished_init_version_row_is_refused(self):
        widget_ledger(
            self.ledger,
            [compact_row("widget-v2.1.0", "evolution", self.NEXT[1],
                         frontier_digest(*self.NEXT))],
            version="widget-v2.1.0", status=self.NEXT[0], revision=self.NEXT[1],
            frontier=self.NEXT[2], job=self.NEXT[3])
        self.assertIn("no longer carries the init-time version row", self.fault())


class WorktreePathTests(unittest.TestCase):
    """Deriving one run's worktree path, and refusing every path that is not it.

    These call the deriver and the validator directly. Neither touches state, a
    ledger or the filesystem, so driving them through a command would only report
    them indirectly, and the point of the step is that a bad path is refused
    before anything exists to inspect.
    """

    def setUp(self):
        self.module = hexctl_module()
        self.dir = tempfile.mkdtemp()
        self.repo = os.path.join(self.dir, "repo")
        os.makedirs(self.repo)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        self.root = os.path.realpath(self.repo)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def refuse(self, *args, **kwargs):
        """Call the validator and return the single refusal line it printed."""
        error = StringIO()
        with redirect_stderr(error):
            with self.assertRaises(SystemExit) as caught:
                self.module.check_worktree_path(*args, **kwargs)
        self.assertNotEqual(caught.exception.code, 0)
        lines = [line for line in error.getvalue().splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, f"expected one refusal line, got {lines}")
        return lines[0]

    # -- the deriver ----------------------------------------------------

    def test_plain_run_branch_derives_the_expected_path(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/worktree-demo")
        self.assertEqual(
            derived,
            os.path.join(self.root, "tmp", "fiat", "fiat-worktree-demo"),
        )

    def test_issue_backed_branch_keeps_its_leading_number(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/439-run-in-a-worktree")
        self.assertEqual(os.path.basename(derived), "fiat-439-run-in-a-worktree")

    def test_one_run_branch_maps_to_one_path(self):
        first = self.module.run_worktree_path(self.repo, "fiat/a-topic")
        second = self.module.run_worktree_path(self.repo, "fiat/a-topic")
        other = self.module.run_worktree_path(self.repo, "fiat/another-topic")
        self.assertEqual(first, second)
        self.assertNotEqual(first, other)

    def test_deriver_creates_nothing(self):
        before = sorted(os.listdir(self.repo))
        derived = self.module.run_worktree_path(self.repo, "fiat/untouched")
        self.assertFalse(os.path.exists(derived))
        self.assertEqual(sorted(os.listdir(self.repo)), before)

    def test_a_target_that_is_not_a_repository_refuses(self):
        plain = os.path.join(self.dir, "not-a-repo")
        os.makedirs(plain)
        error = StringIO()
        with redirect_stderr(error):
            with self.assertRaises(SystemExit) as caught:
                self.module.run_worktree_path(plain, "fiat/topic")
        self.assertNotEqual(caught.exception.code, 0)
        self.assertIn("not a git repository", error.getvalue())

    # -- the validator --------------------------------------------------

    def test_a_fresh_derived_path_is_accepted(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/fresh")
        self.assertEqual(
            self.module.check_worktree_path(self.root, derived), derived
        )

    def test_this_runs_registered_worktree_is_accepted_when_it_exists(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/resumed")
        os.makedirs(derived)
        self.assertEqual(
            self.module.check_worktree_path(self.root, derived, registered=derived),
            derived,
        )

    def test_a_path_that_already_exists_as_a_file_refuses(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/occupied")
        os.makedirs(os.path.dirname(derived))
        with open(derived, "w", encoding="utf-8") as handle:
            handle.write("not a worktree")
        self.assertIn("occupied", self.refuse(self.root, derived))

    def test_a_path_that_already_exists_as_an_unrelated_directory_refuses(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/squatted")
        os.makedirs(derived)
        with open(os.path.join(derived, "someone-elses.txt"), "w", encoding="utf-8") as h:
            h.write("work")
        self.assertIn("occupied", self.refuse(self.root, derived))

    def test_a_path_escaping_the_root_by_dotdot_refuses(self):
        self.assertIn(
            "escapes", self.refuse(self.root, os.path.join("tmp", "fiat", "..", "..", "..", "away"))
        )

    def test_an_absolute_path_outside_the_repository_refuses(self):
        outside = os.path.join(self.dir, "outside")
        self.assertIn("escapes", self.refuse(self.root, outside))

    def test_a_component_symlink_leaving_the_repository_refuses(self):
        outside = os.path.join(self.dir, "elsewhere")
        os.makedirs(outside)
        home = os.path.join(self.root, "tmp")
        os.symlink(outside, home)
        derived = os.path.join(home, "fiat", "fiat-topic")
        self.assertIn("symlink", self.refuse(self.root, derived))

    def test_a_final_component_symlink_leaving_the_repository_refuses(self):
        outside = os.path.join(self.dir, "target")
        os.makedirs(outside)
        os.makedirs(os.path.join(self.root, "tmp", "fiat"))
        derived = os.path.join(self.root, "tmp", "fiat", "fiat-linked")
        os.symlink(outside, derived)
        self.assertIn("symlink", self.refuse(self.root, derived))

    def test_the_repository_root_itself_refuses(self):
        self.assertIn("escapes", self.refuse(self.root, self.root))

    def test_a_refusal_leaves_no_state_no_ledger_and_no_breadcrumb(self):
        before = sorted(os.listdir(self.repo))
        self.refuse(self.root, os.path.join(self.dir, "outside"))
        self.assertEqual(sorted(os.listdir(self.repo)), before)
        self.assertFalse(os.path.exists(os.path.join(self.repo, ".hexaemeron")))

    def test_a_refusal_names_the_path_without_echoing_its_contents(self):
        derived = self.module.run_worktree_path(self.repo, "fiat/secret")
        os.makedirs(os.path.dirname(derived))
        with open(derived, "w", encoding="utf-8") as handle:
            handle.write("SENSITIVE-TOKEN-VALUE")
        line = self.refuse(self.root, derived)
        self.assertIn("fiat-secret", line)
        self.assertNotIn("SENSITIVE-TOKEN-VALUE", line)

    def test_a_dangling_symlink_at_the_derived_path_refuses(self):
        """A link that resolves nowhere still occupies the path.

        Occupancy was read off the resolved target, and a dangling link resolves
        to a path that does not exist, so the check saw a free path. It then
        returned the link's target rather than the path it was asked about, which
        would put the run's tree somewhere the deriver never chose.
        """
        derived = self.module.run_worktree_path(self.repo, "fiat/dangling")
        os.makedirs(os.path.dirname(derived))
        os.symlink(os.path.join(self.root, "nowhere-yet"), derived)
        self.assertIn("symlink", self.refuse(self.root, derived))

    def test_a_symlink_to_a_real_directory_inside_the_repository_refuses(self):
        """The run's tree is a real directory at the derived path, or it is nothing."""
        derived = self.module.run_worktree_path(self.repo, "fiat/redirected")
        inside = os.path.join(self.root, "real-dir")
        os.makedirs(inside)
        os.makedirs(os.path.dirname(derived))
        os.symlink(inside, derived)
        self.assertIn("symlink", self.refuse(self.root, derived))


class WorktreeCreationTests(HexctlCase):
    """`init` arranges the run's isolation, so no run can forget to.

    The origin checkout is the thing under test as much as the worktree is: a run
    that leaves it on a branch it created, or with a `git status` it did not have
    before, has failed even if every receipt it wrote is correct.
    """

    def origin(self, *args):
        proc = subprocess.run(["git", *args], cwd=self.dir, capture_output=True,
                              text=True, check=True)
        return proc.stdout.strip()

    def worktree_entries(self):
        listing = self.origin("worktree", "list", "--porcelain")
        return [line[len("worktree "):] for line in listing.splitlines()
                if line.startswith("worktree ")]

    # -- what a successful init arranges ---------------------------------

    def test_init_creates_the_tree_and_the_run_branch(self):
        before = self.worktree_entries()
        self.init()
        after = self.worktree_entries()
        self.assertEqual(len(after), len(before) + 1)
        created = [entry for entry in after if entry not in before][0]
        self.assertEqual(os.path.realpath(created), os.path.realpath(self.target))
        self.assertEqual(
            self.origin("rev-parse", "--abbrev-ref", "HEAD"), "main"
        )
        self.assertEqual(
            subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"],
                           cwd=self.target, capture_output=True, text=True).stdout.strip(),
            "fiat/test-topic",
        )

    def test_the_runs_state_lands_in_the_tree_not_the_checkout(self):
        self.init()
        self.assertNotEqual(os.path.realpath(self.target), os.path.realpath(self.dir))
        self.assertTrue(os.path.exists(
            os.path.join(self.target, ".hexaemeron", "state.json")))
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, ".hexaemeron", "state.json")))

    def test_the_breadcrumb_names_the_tree(self):
        self.init()
        with open(os.path.join(self.dir, ".hexaemeron", "worktree"),
                  encoding="utf-8") as handle:
            recorded = handle.read().strip()
        self.assertEqual(os.path.realpath(recorded), os.path.realpath(self.target))

    def test_the_checkout_keeps_only_the_breadcrumb_and_the_lock(self):
        """The breadcrumb is the only thing the run itself writes there.

        The directory around it is the kernel lock's, taken before any command
        runs, and the self-ignoring `.gitignore` the controller has always
        written. No state, no ledger, and nothing git can see.
        """
        self.init()
        kept = sorted(os.listdir(os.path.join(self.dir, ".hexaemeron")))
        self.assertEqual(kept, [".gitignore", "lock", "worktree"])

    def test_init_prints_the_dir_to_use_next(self):
        proc = self.run_ctl("init", "--topic", "printed path")
        self.assertIn(f"hexctl --dir {self.target} next", proc.stdout)

    # -- what it leaves alone --------------------------------------------

    def test_the_origin_checkout_is_unchanged_across_a_successful_init(self):
        before_head = self.origin("rev-parse", "HEAD")
        before_branch = self.origin("rev-parse", "--abbrev-ref", "HEAD")
        before_status = self.origin("status", "--short")
        self.init()
        self.assertEqual(self.origin("rev-parse", "HEAD"), before_head)
        self.assertEqual(self.origin("rev-parse", "--abbrev-ref", "HEAD"), before_branch)
        self.assertEqual(self.origin("status", "--short"), before_status)

    def test_the_worktree_home_does_not_show_as_untracked(self):
        """The home ignores itself, so the promise does not depend on the
        target repository already ignoring `tmp/`."""
        before = self.origin("status", "--short")
        self.init()
        self.assertEqual(self.origin("status", "--short"), before)
        self.assertNotIn("tmp/", self.origin("status", "--short"))

    def test_a_run_starts_from_a_dirty_origin_checkout(self):
        """The dirty tree is no longer the run's tree, so it no longer blocks."""
        with open(os.path.join(self.dir, "operators-work.txt"), "w",
                  encoding="utf-8") as handle:
            handle.write("uncommitted\n")
        before_status = self.origin("status", "--short")
        self.assertIn("operators-work.txt", before_status)
        self.init()
        self.assertEqual(self.origin("status", "--short"), before_status)
        self.assertTrue(os.path.exists(
            os.path.join(self.target, ".hexaemeron", "state.json")))

    # -- what it refuses --------------------------------------------------

    def test_a_run_branch_already_checked_out_elsewhere_refuses(self):
        other = os.path.join(self.dir, "other-tree")
        subprocess.run(["git", "worktree", "add", "-q", "-b", "fiat/test-topic",
                        other, "main"], cwd=self.dir, check=True, capture_output=True)
        proc = self.run_ctl("init", "--topic", "test topic", expect=2)
        self.assertIn("already checked out", proc.stderr)
        self.assertIn(other, proc.stderr)
        self.assert_nothing_recorded()

    def test_a_failing_worktree_add_refuses(self):
        """A branch that exists but is checked out nowhere still stops `add -b`."""
        subprocess.run(["git", "branch", "fiat/test-topic"], cwd=self.dir,
                       check=True, capture_output=True)
        proc = self.run_ctl("init", "--topic", "test topic", expect=2)
        self.assertIn("could not create the run worktree", proc.stderr)
        self.assert_nothing_recorded()

    def test_a_target_that_is_not_a_repository_refuses(self):
        plain = tempfile.mkdtemp()
        try:
            proc = subprocess.run(
                [sys.executable, HEXCTL, "--dir", plain, "init", "--topic", "t"],
                capture_output=True, text=True,
            )
            self.assertEqual(proc.returncode, 2)
            self.assertIn("not a git repository", proc.stderr)
            for name in ("state.json", "ledger.jsonl", "worktree"):
                self.assertFalse(
                    os.path.exists(os.path.join(plain, ".hexaemeron", name)), name
                )
        finally:
            shutil.rmtree(plain, ignore_errors=True)

    def assert_nothing_recorded(self):
        """A refusal leaves no state, no ledger, no breadcrumb and no tree."""
        state_dir = os.path.join(self.dir, ".hexaemeron")
        self.assertFalse(os.path.exists(os.path.join(state_dir, "worktree")))
        self.assertFalse(os.path.exists(os.path.join(state_dir, "state.json")))
        self.assertFalse(os.path.exists(os.path.join(state_dir, "ledger.jsonl")))
        derived = os.path.join(self.dir, "tmp", "fiat", "fiat-test-topic")
        self.assertFalse(os.path.exists(derived))

    def test_two_runs_against_one_repository_each_get_their_own_tree(self):
        """The issue asks for two runs that do not contend, not for a second
        run that is refused."""
        self.init("run alpha")
        alpha = self.target
        second = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "run beta"],
            capture_output=True, text=True,
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        beta = os.path.join(self.dir, "tmp", "fiat", "fiat-run-beta")
        self.assertNotEqual(os.path.realpath(alpha), os.path.realpath(beta))
        for tree, branch in ((alpha, "fiat/run-alpha"), (beta, "fiat/run-beta")):
            self.assertTrue(os.path.exists(os.path.join(tree, ".hexaemeron", "state.json")))
            self.assertEqual(
                subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=tree,
                               capture_output=True, text=True).stdout.strip(),
                branch,
            )
        self.assertEqual(self.origin("rev-parse", "--abbrev-ref", "HEAD"), "main")

    def test_the_breadcrumb_records_every_live_run(self):
        self.init("run alpha")
        subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "run beta"],
            capture_output=True, text=True, check=True,
        )
        with open(os.path.join(self.dir, ".hexaemeron", "worktree"),
                  encoding="utf-8") as handle:
            recorded = [line.strip() for line in handle if line.strip()]
        self.assertEqual(len(recorded), 2)
        self.assertEqual(
            sorted(os.path.basename(entry) for entry in recorded),
            ["fiat-run-alpha", "fiat-run-beta"],
        )

    def test_repeating_a_topic_refuses_and_names_the_existing_tree(self):
        self.init("run alpha")
        existing = self.target
        again = subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, "init", "--topic", "run alpha"],
            capture_output=True, text=True,
        )
        self.assertEqual(again.returncode, 2)
        self.assertIn(existing, again.stderr)
        self.assertIn("--dir", again.stderr)


class ResumeAndRetirementTests(HexctlCase):
    """Finding the run again, and putting its tree away once it has landed."""

    def origin_ctl(self, *args):
        return subprocess.run(
            [sys.executable, HEXCTL, "--dir", self.dir, *args],
            capture_output=True, text=True,
        )

    def state_dir_listing(self):
        return sorted(os.listdir(os.path.join(self.dir, ".hexaemeron")))

    # -- resume -----------------------------------------------------------

    def test_status_from_the_checkout_names_the_runs_worktree(self):
        self.init()
        proc = self.origin_ctl("status")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(self.target, proc.stderr)
        self.assertIn(f"hexctl --dir {self.target} next", proc.stderr)

    def test_next_from_the_checkout_names_the_runs_worktree(self):
        self.init()
        proc = self.origin_ctl("next")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(f"hexctl --dir {self.target} next", proc.stderr)

    def test_pointing_at_the_checkout_changes_nothing(self):
        self.init()
        before = self.state_dir_listing()
        self.origin_ctl("status")
        self.origin_ctl("next")
        self.assertEqual(self.state_dir_listing(), before)
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, ".hexaemeron", "state.json")))

    def test_both_runs_are_named_when_the_checkout_started_two(self):
        self.init("run alpha")
        alpha = self.target
        subprocess.run([sys.executable, HEXCTL, "--dir", self.dir, "init",
                        "--topic", "run beta"], capture_output=True, check=True)
        beta = os.path.join(self.dir, "tmp", "fiat", "fiat-run-beta")
        proc = self.origin_ctl("status")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(alpha, proc.stderr)
        self.assertIn(beta, proc.stderr)

    def test_a_recorded_worktree_that_is_gone_refuses_by_name(self):
        self.init()
        recorded = self.target
        shutil.rmtree(recorded)
        proc = self.origin_ctl("status")
        self.assertEqual(proc.returncode, 2)
        self.assertIn(recorded, proc.stderr)
        self.assertIn("no longer there", proc.stderr)

    def test_a_recorded_worktree_that_is_gone_does_not_start_a_second_run(self):
        self.init()
        shutil.rmtree(self.target)
        self.origin_ctl("next")
        self.assertFalse(os.path.exists(
            os.path.join(self.dir, ".hexaemeron", "state.json")))
        self.assertFalse(os.path.exists(os.path.join(self.dir, "tmp", "fiat",
                                                     "fiat-test-topic")))

    def test_state_already_in_a_checkout_still_resumes(self):
        """A run that predates the worktree keeps working where it is."""
        legacy = os.path.join(self.dir, ".hexaemeron")
        os.makedirs(legacy, exist_ok=True)
        self.init()
        shutil.copytree(os.path.join(self.target, ".hexaemeron"),
                        legacy, dirs_exist_ok=True)
        os.remove(os.path.join(legacy, "worktree"))
        proc = self.origin_ctl("status", "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout)["topic"], "test topic")

    # -- retirement -------------------------------------------------------

    def land_a_run(self):
        """A one-step run, driven all the way to the integrate phase."""
        self.to_steps(titles=("Scaffold",))
        self.run_ctl("record", "security_suite", '"waived: fixture"')
        self.finish_step(1)

    def test_reset_removes_a_clean_tree_and_archives_its_evidence(self):
        self.land_a_run()
        self.integrate_run()
        self.assertTrue(os.path.isdir(self.retired),
                        "integrate leaves the tree so status and verify still run")
        self.run_ctl("reset")
        self.assertFalse(os.path.isdir(self.retired))
        archives = os.listdir(os.path.join(self.dir, ".hexaemeron", "archive"))
        self.assertEqual(len(archives), 1)
        archived = os.path.join(self.dir, ".hexaemeron", "archive", archives[0])
        for name in ("state.json", "ledger.jsonl"):
            self.assertTrue(os.path.exists(os.path.join(archived, name)), name)

    def test_the_integrate_receipt_records_the_tree_as_clean(self):
        self.land_a_run()
        self.integrate_run()
        self.assertIs(self.state()["receipts"]["integrate"]["worktree_clean"], True)

    def test_a_tree_holding_work_is_kept_and_never_forced(self):
        self.land_a_run()
        held = self.target
        with open(os.path.join(held, "someone-was-working.txt"), "w",
                  encoding="utf-8") as handle:
            handle.write("do not lose me\n")
        self.integrate_run()
        self.run_ctl("reset")
        self.assertTrue(os.path.isdir(held))
        self.assertTrue(os.path.exists(
            os.path.join(held, "someone-was-working.txt")))
        archives = os.listdir(os.path.join(self.dir, ".hexaemeron", "archive"))
        self.assertEqual(len(archives), 1)

    def test_a_retired_run_drops_out_of_the_breadcrumb(self):
        self.land_a_run()
        self.integrate_run()
        self.run_ctl("reset")
        with open(os.path.join(self.dir, ".hexaemeron", "worktree"),
                  encoding="utf-8") as handle:
            self.assertEqual(handle.read().strip(), "")

    @property
    def retired(self):
        return os.path.join(self.dir, "tmp", "fiat", "fiat-test-topic")


class FrontierRowAttributionTests(OriginCheckoutMixin, unittest.TestCase):
    """A run is charged for its own rows and no others.

    The gate counted every row added since `init`, which cannot tell this run's
    row from one another run published meanwhile. The issue 466 run added
    `fiat-v5.15.1`, absorbed `fiat-v5.14.1` in its one permitted sync, and was
    refused for two rows. It could renumber neither: `done_integrate` freezes
    the run branch at the sync commit.
    """

    HELD = ("open", "held-thing", "The widget does not do the thing.",
            "Make the widget do the thing.")
    FOREIGN = "widget-v1.2.0"
    OWN = "widget-v1.3.0"

    def setUp(self):
        self.dir = tempfile.mkdtemp()
        make_origin_checkout(self.dir)
        self.ledger = os.path.join(
            self.dir, "plugins", "demo", "skills", "widget", "EVOLUTION.md")
        self.base_digest = frontier_digest(*self.HELD)
        self.base_row = row("widget-v1.1.0", "baseline", self.HELD[1],
                            self.base_digest, "Versioning starts here.")
        widget_ledger(self.ledger, [self.base_row], version="widget-v1.1.0",
                      status=self.HELD[0], revision=self.HELD[1],
                      frontier=self.HELD[2], job=self.HELD[3])
        with open(self.ledger, "rb") as handle:
            ledger_sha256 = hashlib.sha256(handle.read()).hexdigest()
        self.before = {
            "ledger": os.path.relpath(self.ledger, self.dir),
            "sha256": ledger_sha256,
            "rows": 1,
        }

    def tearDown(self):
        import shutil
        shutil.rmtree(self.dir, ignore_errors=True)

    def held_row(self, version):
        """One generation row retaining the held revision and digest."""
        return row(version, "generation", self.HELD[1], self.base_digest)

    def write_chain(self, versions, header_version=None):
        widget_ledger(
            self.ledger,
            [self.base_row, *(self.held_row(v) for v in versions)],
            version=header_version or versions[-1],
            status=self.HELD[0], revision=self.HELD[1],
            frontier=self.HELD[2], job=self.HELD[3],
        )

    def fault_with(self, published):
        return hexctl_module().frontier_close_fault(
            self.ledger, self.before, frozenset(published)
        )

    def test_a_row_published_meanwhile_is_not_charged_to_this_run(self):
        self.write_chain([self.FOREIGN, self.OWN])
        self.assertIsNone(self.fault_with({self.FOREIGN}))

    def test_without_the_published_set_the_same_ledger_is_refused(self):
        """The red side of the issue 466 refusal, on the same topology."""
        self.write_chain([self.FOREIGN, self.OWN])
        fault = self.fault_with(set())
        self.assertIn("gained 2 history row(s)", fault)
        self.assertNotIn("already published", fault)

    def test_the_refusal_says_how_many_it_subtracted(self):
        self.write_chain([self.FOREIGN, self.OWN, "widget-v1.4.0"])
        fault = self.fault_with({self.FOREIGN})
        self.assertIn("gained 2 history row(s)", fault)
        self.assertIn("after subtracting 1 already published", fault)

    def test_two_rows_of_its_own_are_still_refused(self):
        self.write_chain([self.FOREIGN, self.OWN])
        self.assertIn("gained 2", self.fault_with({"widget-v9.9.9"}))

    def test_the_newest_row_may_not_be_a_published_one(self):
        """One own row, then a row published on top of it during the sync."""
        self.write_chain([self.FOREIGN, self.OWN], header_version=self.OWN)
        fault = self.fault_with({self.OWN})
        self.assertIn("was already published in the recorded base", fault)
        self.assertIn("has to be the newest", fault)

    def test_a_duplicated_published_label_cannot_subtract_twice(self):
        self.write_chain([self.FOREIGN, self.FOREIGN], header_version=self.FOREIGN)
        self.assertIn("gained 0", self.fault_with({self.FOREIGN}))

    def test_the_base_ledger_read_returns_the_versions_it_committed(self):
        module = hexctl_module()
        self.write_chain([self.FOREIGN])
        relative = self.before["ledger"]
        subprocess.run(["git", "add", relative], cwd=self.dir, check=True,
                       capture_output=True)
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", "commit", "-q", "-m", "ledger"],
            cwd=self.dir,
            check=True,
            capture_output=True,
        )
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.dir,
                              check=True, capture_output=True,
                              text=True).stdout.strip()
        self.assertEqual(
            module.base_ledger_versions(self.dir, head, relative),
            frozenset({"widget-v1.1.0", self.FOREIGN}),
        )

    def test_an_unreadable_base_ledger_subtracts_nothing(self):
        module = hexctl_module()
        self.write_chain([self.FOREIGN, self.OWN])
        relative = self.before["ledger"]
        for base in ("", "not-a-sha", "0" * 40):
            with self.subTest(base=base):
                self.assertEqual(
                    module.base_ledger_versions(self.dir, base, relative),
                    frozenset(),
                )
        # A read that answers nothing leaves the older, stricter arithmetic.
        self.assertIn(
            "gained 2",
            self.fault_with(module.base_ledger_versions(self.dir, "0" * 40, relative)),
        )

    def test_the_receipt_records_only_what_was_subtracted(self):
        """Not the whole base ledger: the rows the refusal actually discounted."""
        module = hexctl_module()
        self.write_chain([self.FOREIGN, self.OWN])
        # A base carrying an unrelated row as well; only the overlap counts.
        published = frozenset({self.FOREIGN, "widget-v0.9.0"})
        self.assertEqual(
            module.frontier_subtracted_rows(self.dir, self.before, published),
            [self.FOREIGN],
        )

    def test_nothing_published_records_nothing(self):
        module = hexctl_module()
        self.write_chain([self.OWN])
        self.assertEqual(
            module.frontier_subtracted_rows(self.dir, self.before, frozenset()),
            [],
        )

    def test_the_gate_and_the_receipt_slice_the_same_rows(self):
        """One slicing rule, so a refusal cannot count rows the receipt omits."""
        module = hexctl_module()
        self.write_chain([self.FOREIGN, self.OWN])
        rows = module.ledger_rows(open(self.ledger, encoding="utf-8").read())
        after = module.frontier_rows_after_anchor(rows, self.before)
        self.assertEqual([entry["version"] for entry in after],
                         [self.FOREIGN, self.OWN])
        self.assertEqual(
            module.frontier_subtracted_rows(
                self.dir, self.before, frozenset({self.FOREIGN})),
            [self.FOREIGN],
        )

    def test_a_missing_ledger_path_subtracts_nothing(self):
        module = hexctl_module()
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.dir,
                              check=True, capture_output=True,
                              text=True).stdout.strip()
        self.assertEqual(
            module.base_ledger_versions(self.dir, head, "nowhere/EVOLUTION.md"),
            frozenset(),
        )


class GitHubSignerDiagnosis(unittest.TestCase):
    """A refusal must name GitHub's key as the cause, not just fail.

    A commit GitHub rewrote carries GitHub's web-flow signature. `verify-commit`
    then fails against a local keyring, and the bare message sends whoever reads
    it looking for a broken signing setup rather than at the branch rewrite that
    actually happened. The wrong repair for that message is importing GitHub's
    public key, which makes the check pass and removes the guarantee it exists
    for, so the message says so explicitly.
    """

    def setUp(self):
        self.hexctl = hexctl_module()

    def test_the_known_github_keys_are_declared(self):
        self.assertIn("B5690EEEBB952194", self.hexctl.GITHUB_SIGNING_KEYS)
        self.assertIn("4AEE18F83AFDEB23", self.hexctl.GITHUB_SIGNING_KEYS)

    def _refusal(self, key):
        """The message verify_local_commit dies with, for a given signing key."""
        module = self.hexctl
        captured = StringIO()
        with mock.patch.object(module, "bounded_tool_status", return_value=1), \
             mock.patch.object(module, "signing_key", return_value=key), \
             mock.patch.object(module, "require_full_sha", side_effect=lambda s, _l: s), \
             redirect_stderr(captured):
            with self.assertRaises(SystemExit):
                module.verify_local_commit(".", "a" * 40, "step 1")
        return captured.getvalue()

    def test_a_github_signed_commit_is_refused_and_the_cause_is_named(self):
        message = self._refusal("b5690eeebb952194")
        self.assertIn("signed by GitHub", message)
        self.assertIn("B5690EEEBB952194", message)
        self.assertIn("stacked", message, "the rewrite that causes this must be named")
        self.assertIn(
            "Do not import GitHub's public key",
            message,
            "the wrong repair is the obvious one and has to be ruled out in the message",
        )

    def test_an_unknown_key_is_reported_without_blaming_github(self):
        message = self._refusal("DEADBEEFDEADBEEF")
        self.assertIn("DEADBEEFDEADBEEF", message)
        self.assertIn("no valid local signature", message)
        self.assertNotIn("signed by GitHub", message)

    def test_an_unsigned_commit_keeps_the_plain_message(self):
        message = self._refusal("")
        self.assertIn("no valid local signature", message)
        self.assertNotIn("signed by GitHub", message)

    def test_a_verifying_commit_is_not_refused_by_the_signature_check(self):
        """The diagnosis must not turn a passing verification into a refusal.

        Checks which refusal, not whether one happened. A commit that verifies
        still goes on to the author and trailer checks, and those refuse this
        synthetic sha for reasons that have nothing to do with signing. What must
        not appear is a signature complaint.
        """
        module = self.hexctl
        captured = StringIO()
        with mock.patch.object(module, "bounded_tool_status", return_value=0), \
             mock.patch.object(module, "require_full_sha", side_effect=lambda s, _l: s), \
             redirect_stderr(captured):
            try:
                module.verify_local_commit(".", "a" * 40, "step 1")
            except BaseException:
                pass
        message = captured.getvalue()
        self.assertNotIn("no valid local signature", message)
        self.assertNotIn("signed by GitHub", message)

    def test_the_signature_check_runs_before_anything_else(self):
        """A later check must not mask an unverifiable signature."""
        module = self.hexctl
        captured = StringIO()
        with mock.patch.object(module, "bounded_tool_status", return_value=1), \
             mock.patch.object(module, "signing_key", return_value=""), \
             mock.patch.object(module, "require_full_sha", side_effect=lambda s, _l: s), \
             mock.patch.object(module, "commit_author",
                               side_effect=AssertionError("author read before signature check")), \
             redirect_stderr(captured):
            with self.assertRaises(SystemExit):
                module.verify_local_commit(".", "a" * 40, "step 1")
        self.assertIn("no valid local signature", captured.getvalue())


class RewrittenStackRefusal(unittest.TestCase):
    """A waiting non-ancestor is refused before another merge is receipted.

    This synthetic fixture supplies native ancestry status 1 for unequal tips.
    The controller can therefore name the observed branch and relation without
    asserting which external operation caused the history to move.
    """

    def setUp(self):
        self.hexctl = hexctl_module()

    def _state(self):
        return {
            "integrate": {"merged": [1]},
            "steps": [
                {"n": 1, "title": "one",
                 "receipts": {"push": {"head_commit": "a" * 40}}},
                {"n": 2, "title": "two",
                 "receipts": {"push": {"head_commit": "b" * 40}}},
                {"n": 3, "title": "three",
                 "receipts": {"push": {"head_commit": "c" * 40}}},
            ],
        }

    def _refusal(self, state, current_step, tips):
        """The stderr the check dies with, or None when it returns."""
        module = self.hexctl

        def tip(_dir, branch, label="remote run branch tip"):
            value = tips[branch]
            if value is SystemExit:
                module.die(f"{label} could not be read")
            return value

        captured = StringIO()
        with mock.patch.object(module, "step_branch_name",
                               side_effect=lambda _s, step: f"branch-{step['n']}"), \
             mock.patch.object(module, "remote_branch_tip", side_effect=tip), \
             mock.patch.object(module, "_native_ancestry_status", return_value=1), \
             redirect_stderr(captured):
            try:
                module.refuse_rewritten_stack(".", state, current_step)
            except SystemExit:
                return captured.getvalue()
        return None

    def test_an_untouched_stack_passes(self):
        message = self._refusal(
            self._state(), 2, {"branch-3": "c" * 40}
        )
        self.assertIsNone(message)

    def test_a_nonancestor_waiting_branch_is_refused_without_a_cause_claim(self):
        message = self._refusal(
            self._state(), 2, {"branch-3": "d" * 40}
        )
        self.assertIsNotNone(message, "a non-ancestor waiting branch was not refused")
        self.assertIn("no longer contains its receipted head", message)
        self.assertIn("is not an ancestor", message)
        self.assertIn("branch-3", message)
        self.assertIn("c" * 40, message)
        self.assertIn("d" * 40, message)
        self.assertIn(
            "do not import GitHub's public key",
            message,
            "the wrong repair is the obvious one and must be ruled out in the message",
        )
        self.assertNotIn("GitHub's stacked-pull-request flow", message)
        self.assertNotIn("re-signs", message)

    def test_the_step_being_merged_is_never_queried(self):
        """The current step's branch may legitimately differ from its receipt
        after audit-branch fast-forwards; only the WAITING steps are the rewrite
        signal. Step order is enforced before this check runs, so the current
        step is always the lowest unmerged one and everything below it is in
        `merged`."""
        module = self.hexctl
        queried = []

        def tip(_dir, branch, label="remote run branch tip"):
            queried.append(branch)
            return "c" * 40

        with mock.patch.object(module, "step_branch_name",
                               side_effect=lambda _s, step: f"branch-{step['n']}"), \
             mock.patch.object(module, "remote_branch_tip", side_effect=tip):
            module.refuse_rewritten_stack(".", self._state(), 2)
        self.assertEqual(queried, ["branch-3"], "only the waiting steps are compared")

    def test_merged_steps_are_not_compared(self):
        state = self._state()
        state["integrate"]["merged"] = [1, 2]
        message = self._refusal(state, 3, {})
        self.assertIsNone(message)

    def test_an_unreadable_waiting_branch_is_reported_not_skipped(self):
        message = self._refusal(
            self._state(), 2, {"branch-3": SystemExit}
        )
        self.assertIsNotNone(message)
        self.assertIn("could not be read", message)
        self.assertIn("step 3", message)

    def test_a_step_without_a_push_receipt_is_left_alone(self):
        state = self._state()
        state["steps"][2]["receipts"] = {}
        message = self._refusal(state, 2, {})
        self.assertIsNone(message)
