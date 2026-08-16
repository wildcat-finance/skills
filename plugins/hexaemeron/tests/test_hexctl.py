"""End-to-end tests for hexctl, run through the CLI the way the skill uses it."""

import json
import hashlib
import os
import subprocess
import sys
import tempfile
import time
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HEXCTL = os.path.join(HERE, "..", "skills", "fiat", "scripts", "hexctl.py")


class HexctlCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.processes = []

    def tearDown(self):
        for process in self.processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)
        self.tmp.cleanup()

    def run_ctl(self, *args, expect=0):
        proc = subprocess.run(
            [sys.executable, HEXCTL, *args],
            cwd=self.dir,
            capture_output=True,
            text=True,
        )
        if proc.returncode != expect:
            raise AssertionError(
                f"hexctl {' '.join(args)} -> rc {proc.returncode} "
                f"(expected {expect})\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
            )
        return proc

    def next_json(self):
        return json.loads(self.run_ctl("next").stdout)

    def write(self, name, content="stub\n"):
        path = os.path.join(self.dir, name)
        os.makedirs(os.path.dirname(path) or self.dir, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(content)
        return name

    def init(self, topic="test topic"):
        self.run_ctl("init", "--topic", topic)

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
                self.dir,
                command,
                ready,
                release,
            ],
            cwd=self.dir,
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

    def to_steps(self, titles=("Scaffold", "Core")):
        self.init()
        study = self.write("study.md")
        self.run_ctl("done", "study", "--artifact", study,
                     "--skills", "hexaemeron:imprimatur")
        runbook = self.write("runbook.md")
        steps = self.write("steps.json", json.dumps(list(titles)))
        self.run_ctl("done", "runbook", "--artifact", runbook,
                     "--steps-file", steps)

    def to_audit(self):
        self.to_steps()
        self.run_ctl("done", "implement", "--branch", "step-1-scaffold",
                     "--commit", "abc123")

    def finish_step(self, step_no=1):
        self.run_ctl("done", "implement", "--branch", f"step-{step_no}",
                     "--commit", "abc123")
        self.run_ctl("audit-round", "--findings", "0", "--log", "audit/AUDIT.md")
        self.run_ctl("done", "audit")
        self.run_ctl("done", "prose", "--files", "3",
                     "--skills", "hexaemeron:imprimatur,hexaemeron:vulgate")
        self.run_ctl("done", "push", "--pr-url", f"https://x/pr/{step_no}")


class TestLifecycle(HexctlCase):
    def test_init_creates_state_ledger_and_gitignore(self):
        self.init()
        root = os.path.join(self.dir, ".hexaemeron")
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
        rb = self.write("runbook.md")
        steps = self.write("steps.json",
                           json.dumps(["Scaffold", {"title": "Core"}]))
        self.run_ctl("done", "runbook", "--artifact", rb, "--steps-file", steps)
        out = self.next_json()
        self.assertEqual(out["do"], "implement")
        self.assertEqual(out["step"], 1)
        self.assertEqual(out["title"], "Scaffold")


class TestRunLock(HexctlCase):
    def test_live_holder_refuses_a_second_writer_with_an_actionable_message(self):
        self.init()
        holder, _, release = self.start_lock_holder()
        result = self.run_ctl("record", "key", '"value"', expect=1)
        self.assertIn(f"pid {holder.pid}", result.stderr)
        self.assertIn("`cmd_record`", result.stderr)
        self.assertIn("git worktree add", result.stderr)
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
        path = os.path.join(self.dir, ".hexaemeron", "lock")
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
        state_path = os.path.join(self.dir, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.dir, ".hexaemeron", "ledger.jsonl")
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
            "done", "implement", "--branch", "step-1", "--commit", "abc123"
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
        self.run_ctl("audit-round", "--findings", "3", "--log", "audit/AUDIT.md")
        out = self.next_json()
        self.assertEqual(out["do"], "audit-round")
        self.assertEqual(out["round"], 2)
        self.assertEqual(out["prior_findings"], 3)

    def test_close_blocked_while_findings_open(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')
        self.run_ctl("audit-round", "--findings", "2")
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("open", proc.stderr)

    def test_clean_close_requires_fixes_evidence_when_findings_existed(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("audit-round", "--findings", "2")
        self.run_ctl("audit-round", "--findings", "0")
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("fixes", proc.stderr)
        self.run_ctl("done", "audit", "--fixes-ref", "issue-1--audit@deadbeef")
        self.assertEqual(self.next_json()["do"], "prose")

    def test_fixes_commit_on_round_satisfies_evidence(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("audit-round", "--findings", "1",
                     "--fixes-commit", "beef01")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("done", "audit")

    def test_no_further_leads_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("audit-round", "--findings", "1", "--fixes-commit", "b1")
        proc = self.run_ctl("done", "audit", "--no-further-leads", expect=2)
        self.assertIn("--reason", proc.stderr)
        self.run_ctl("done", "audit", "--no-further-leads",
                     "--reason", "remaining lead is a gas nit, out of scope")

    def test_max_rounds_forces_verdict(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
        self.run_ctl("config", "set", "audit.max_rounds", "2")
        self.run_ctl("audit-round", "--findings", "2", "--fixes-commit", "b1")
        self.run_ctl("audit-round", "--findings", "1", "--fixes-commit", "b2")
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn("max audit rounds", proc.stderr)
        out = self.next_json()
        self.assertEqual(out["do"], "audit-verdict")
        self.assertEqual(out["open_findings"], 1)


class TestProseAndPush(HexctlCase):
    def to_prose(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"suite"')
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
        self.run_ctl("done", "push", "--pr-url", "https://x/pr/1")

    def test_push_advances_steps_then_run_completes(self):
        self.to_steps(("One", "Two"))
        self.run_ctl("record", "security_suite", '"suite"')
        self.finish_step(1)
        out = self.next_json()
        self.assertEqual((out["do"], out["step"]), ("implement", 2))
        self.finish_step(2)
        self.assertEqual(self.next_json()["do"], "done")


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
        ledger = os.path.join(self.dir, ".hexaemeron", "ledger.jsonl")
        with open(ledger) as fh:
            lines = fh.read().splitlines()
        entry = json.loads(lines[0])
        entry["data"]["topic"] = "someone edited history"
        lines[0] = json.dumps(entry, sort_keys=True)
        with open(ledger, "w") as fh:
            fh.write("\n".join(lines) + "\n")
        proc = self.run_ctl("verify", expect=1)
        self.assertIn("chain broken", proc.stderr)

    def test_record_and_status_json(self):
        self.init()
        self.run_ctl("record", "note", '"local run"')
        state = json.loads(self.run_ctl("status", "--json").stdout)
        self.assertEqual(state["receipts"]["note"], "local run")
        self.assertEqual(state["phase"], "study")

    def test_reset_archives_completed_run_and_allows_reinit(self):
        self.to_steps(("One",))
        self.run_ctl("record", "security_suite", '"suite"')
        self.finish_step(1)
        self.assertEqual(self.next_json()["do"], "done")

        self.run_ctl("reset")
        root = os.path.join(self.dir, ".hexaemeron")
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
        self.run_ctl("config", "set", "audit.max_rounds", "3")
        out = self.run_ctl("config", "get", "audit.max_rounds").stdout.strip()
        self.assertEqual(out, "3")
        proc = self.run_ctl("config", "get", "audit.nope", expect=2)
        self.assertIn("not found", proc.stderr)



class TestFuzzRegressions(HexctlCase):
    """Pins for the day-5 fuzz findings (F-01..F-09)."""

    def state_file(self):
        return os.path.join(self.dir, ".hexaemeron", "state.json")

    def ledger_file(self):
        return os.path.join(self.dir, ".hexaemeron", "ledger.jsonl")

    def to_audit_with_suite(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '["x","y"]')

    def test_state_edit_detected_by_verify(self):
        self.to_audit_with_suite()
        self.run_ctl("audit-round", "--findings", "2", "--log", "a.md",
                     "--fixes-commit", "fff")
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
        self.run_ctl("config", "set", "audit.max_rounds", '"eight"')
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertNotIn("Traceback", proc.stderr)
        self.assertIn("must be an integer", proc.stderr)
        self.run_ctl("config", "set", "audit.max_rounds", "0")
        proc = self.run_ctl("audit-round", "--findings", "1", expect=2)
        self.assertIn(">= 1", proc.stderr)
        self.run_ctl("config", "set", "audit.max_rounds", "8")
        self.run_ctl("audit-round", "--findings", "0")
        self.run_ctl("verify")

    def test_prose_nonstring_config_ids(self):
        self.to_audit_with_suite()
        self.run_ctl("config", "set", "skills.prose_lint", "123")
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
