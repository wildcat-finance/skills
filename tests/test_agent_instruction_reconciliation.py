"""Staging, publication and recovery against complete disposable Git baselines."""

from __future__ import annotations

import json
import io
import contextlib
import copy
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import agent_instruction_reconciliation as air


class ReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = tempfile.TemporaryDirectory(prefix="air-test-baseline-")
        cls.base = Path(cls.template.name).resolve()
        cls.manifest = json.loads((ROOT / air.MANIFEST).read_bytes())
        cls.files = {p: (ROOT / p).read_bytes() for p in air.closure(cls.manifest)}
        for name, body in cls.files.items():
            target = cls.base / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
        cls.git(cls.base, "init", "--quiet")
        cls.git(cls.base, "add", ".")
        cls.git(cls.base, "-c", "user.name=Fixture", "-c", "user.email=fixture@example.test",
                "-c", "commit.gpgsign=false", "commit", "--quiet", "-m", "accepted bounded baseline")
        cls.commit = cls.git(cls.base, "rev-parse", "HEAD").strip()

    @classmethod
    def tearDownClass(cls):
        cls.template.cleanup()

    @staticmethod
    def git(root, *args):
        result = subprocess.run(["/usr/bin/git", *args], cwd=root, capture_output=True,
                                text=True, check=True, env={"PATH": "/usr/bin:/bin",
                                "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"})
        return result.stdout

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="air-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve() / "repo"
        shutil.copytree(self.base, self.root, copy_function=shutil.copy2)

    def edit(self, fixture_id, placement="after"):
        fixture = next(f for f in self.manifest["fixtures"] if f["id"] == fixture_id)
        source = fixture["source"]["path"]
        body = self.files[source]
        marker = b"\n<!-- independent out-of-span edit -->\n"
        edited = marker + body if placement == "before" else body + marker
        (self.root / source).write_bytes(edited)
        return source, edited, len(marker)

    def prepare(self, fixture_id="horos-boundary-check", placement="after"):
        source, edited, delta = self.edit(fixture_id, placement)
        result = air.prepare(self.root, baseline=self.commit, source=source, stage="tmp/stage")
        return result, source, edited, delta

    def test_all_six_placements_select_and_relocate_exact_bytes(self):
        for fixture in self.manifest["fixtures"]:
            for placement in ("before", "after"):
                with self.subTest(fixture=fixture["id"], placement=placement):
                    source, edited, delta = self.edit(fixture["id"], placement)
                    stage = "tmp/" + fixture["id"] + "-" + placement
                    result = air.prepare(self.root, baseline=self.commit, source=source, stage=stage)
                    self.assertEqual(result["affected_fixtures"], [fixture["id"]])
                    self.assertEqual(result["outcome"], "needs-evidence" if placement == "before" else "ready")
                    self.assertEqual(result["measured_streams"][fixture["id"]]["source"]["state"], "ready")
                    self.assertEqual(result["measured_streams"][fixture["id"]]["model"]["state"],
                                     "needs-evidence" if placement == "before" else "ready")
                    plan = json.loads((self.root / stage / "plan.json").read_bytes())
                    offsets = plan["offsets"][fixture["id"]]
                    self.assertEqual(offsets["delta"], delta if placement == "before" else 0)
                    for name, original in self.files.items():
                        self.assertEqual((self.root / name).read_bytes(), edited if name == source else original)
                    self.assertEqual((self.root / stage / "work" / source).read_bytes(), edited)
                    (self.root / source).write_bytes(self.files[source])

    def test_changed_and_duplicate_reviewed_anchors_refuse(self):
        fixture = self.manifest["fixtures"][1]
        path = fixture["source"]["path"]
        body = self.files[path]; start = int(fixture["source"]["start"]); end = int(fixture["source"]["end"])
        for edited in (body[:start] + b"X" + body[start+1:], body + body[start:end]):
            with self.subTest(duplicate=len(edited) > len(body)):
                (self.root / path).write_bytes(edited)
                with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-REVIEW"):
                    air.prepare(self.root, baseline=self.commit, source=path, stage="tmp/stage")
                self.assertFalse((self.root / "tmp/stage").exists())

    def test_unrelated_bound_sibling_drift_refuses(self):
        source, _, _ = self.edit("horos-boundary-check")
        (self.root / air.prover.MEASUREMENT).write_bytes(b"{}")
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-SIBLING.DRIFT"):
            air.prepare(self.root, baseline=self.commit, source=source, stage="tmp/stage")

    def test_baseline_is_full_commit_and_inherited_git_redirection_is_ignored(self):
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-BASELINE.ID"):
            air.Baseline(self.root, "HEAD")
        with mock.patch.dict(os.environ, {"GIT_DIR": "/does/not/exist", "GIT_WORK_TREE": "/",
                                         "GIT_OBJECT_DIRECTORY": "/does/not/exist"}):
            base = air.Baseline(self.root, self.commit)
            self.assertEqual(base.read(air.MANIFEST), self.files[air.MANIFEST])

    def test_object_bytes_are_verified_against_the_requested_digest(self):
        with mock.patch.object(air, "bounded_command", return_value=(0, b"substituted", b"")):
            with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-BASELINE.OBJECT"):
                air.Baseline(self.root, self.commit)

    def test_duplicate_json_and_path_aliases_refuse(self):
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-JSON.DUPLICATE"):
            air.record(b'{"a":1,"a":2}')
        for value in ("../escape", "/tmp/escape", "a/../b", "a//b", "a/./b", "a\\b", ".git/config"):
            with self.subTest(path=value), self.assertRaises(air.ReconciliationError):
                air.relative(value)

    def test_symlink_hardlink_fifo_and_parent_alias_refuse(self):
        (self.root / "alias").symlink_to("PROMISE_MACHINE.md")
        os.link(self.root / "PROMISE_MACHINE.md", self.root / "hard")
        os.mkfifo(self.root / "fifo")
        (self.root / "parent").symlink_to("tests")
        with air.Root(self.root) as root:
            for path in ("alias", "hard", "fifo", "parent/promise_machine_coverage.json"):
                with self.subTest(path=path), self.assertRaises(air.ReconciliationError):
                    root.read(path)

    def test_apply_checks_complete_stage_and_publishes_inputs_before_manifest(self):
        result, source, edited, _ = self.prepare()
        phases = []
        checked = air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"], check_only=True)
        self.assertEqual(checked["outcome"], "ready")
        for path, body in self.files.items():
            self.assertEqual((self.root / path).read_bytes(), edited if path == source else body)
        with contextlib.redirect_stdout(io.StringIO()):
            applied = air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"],
                                phase_hook=lambda phase, path: phases.append((phase, path)))
        self.assertEqual(applied["outcome"], "accepted")
        self.assertEqual(phases[0], ("journal-durable", None))
        self.assertEqual([p for phase, p in phases if phase == "target-published"][-2:], [air.MANIFEST, air.COVERAGE])
        self.assertEqual((self.root / source).read_bytes(), edited)
        self.assertFalse((self.root / air.ACTIVE).exists())
        self.assertEqual(air.check_corpus(self.root)[-1]["outcome"], "accepted")

    def test_handled_partial_publication_restores_and_fresh_retry_succeeds(self):
        result, source, edited, _ = self.prepare()

        def fault(phase, path):
            if phase == "target-published":
                raise OSError("injected publication fault")

        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(air.ReconciliationError, "AIR-E-APPLY.ROLLED-BACK"):
            air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"], phase_hook=fault)
        for path, body in self.files.items():
            self.assertEqual((self.root / path).read_bytes(), edited if path == source else body)
        result = air.prepare(self.root, baseline=self.commit, source=source, stage="tmp/retry")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(air.apply(self.root, stage="tmp/retry", plan_sha256=result["plan_sha256"])["outcome"], "accepted")

    def test_stale_reports_do_not_earn_apply_and_no_journal_or_live_write_occurs(self):
        result, source, edited, _ = self.prepare("promise-machine-router-selection", "before")
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-CHECK"):
            air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"])
        self.assertFalse((self.root / air.ACTIVE).exists())
        for path, body in self.files.items():
            self.assertEqual((self.root / path).read_bytes(), edited if path == source else body)

    def test_stage_mutation_live_identity_race_and_partial_evidence_pair_refuse(self):
        result, _, _, _ = self.prepare()
        plan_sha = result["plan_sha256"]
        profile = self.manifest["evidence"]["tokenizer_profile"]["path"]
        target = self.root / "tmp/stage/work" / profile
        target.write_bytes(b"{}")
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-STAGE.DRIFT"):
            air.apply(self.root, stage="tmp/stage", plan_sha256=plan_sha)
        target.write_bytes(self.files[profile])
        acquisition = self.root / "tmp/stage/work/acquisitions/measurement.json"
        acquisition.write_bytes(self.files[air.prover.MEASUREMENT])
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-EVIDENCE.PAIR"):
            air.apply(self.root, stage="tmp/stage", plan_sha256=plan_sha)
        acquisition.unlink()
        (self.root / profile).touch()
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-LIVE.DRIFT"):
            air.apply(self.root, stage="tmp/stage", plan_sha256=plan_sha)

    def test_actual_sigkill_blocks_next_operation_and_recovery_is_idempotent(self):
        result, source, edited, _ = self.prepare()
        script = """import sys,time
sys.path.insert(0,sys.argv[1])
import agent_instruction_reconciliation as a
def hook(phase,path):
 if phase=='target-published':
  print('FIRST-WRITE',flush=True)
  time.sleep(60)
a.apply(sys.argv[2],stage='tmp/stage',plan_sha256=sys.argv[3],phase_hook=hook)
"""
        child = subprocess.Popen([sys.executable, "-c", script, str(ROOT / "scripts"), str(self.root), result["plan_sha256"]],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            event = json.loads(child.stdout.readline())
            self.assertEqual(child.stdout.readline().strip(), "FIRST-WRITE")
            child.kill()
            child.communicate(timeout=10)
            self.assertEqual(child.returncode, -9)
        finally:
            if child.poll() is None:
                child.kill(); child.communicate(timeout=10)
        digest = event["journal_sha256"]
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-JOURNAL.PENDING"):
            air.prepare(self.root, baseline=self.commit, source=source, stage="tmp/blocked")
        self.assertEqual(air.recover(self.root, journal_sha256=digest)["outcome"], "recovered")
        self.assertEqual(air.recover(self.root, journal_sha256=digest)["outcome"], "already-recovered")
        for path, body in self.files.items():
            self.assertEqual((self.root / path).read_bytes(), edited if path == source else body)

    def test_third_version_refuses_rollback_and_recovery_without_overwrite(self):
        result, _, _, _ = self.prepare()
        changed = []

        def fault(phase, path):
            if phase == "target-published":
                (self.root / path).write_bytes(b"independent third version")
                changed.append(path)
                raise OSError("independent writer")

        output = io.StringIO()
        with contextlib.redirect_stdout(output), self.assertRaisesRegex(air.ReconciliationError, "AIR-E-APPLY.RECOVERY"):
            air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"], phase_hook=fault)
        event = json.loads(output.getvalue())
        before = {p: (self.root / p).read_bytes() for p in self.files}
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-RECOVERY.THIRD"):
            air.recover(self.root, journal_sha256=event["journal_sha256"])
        self.assertEqual(before, {p: (self.root / p).read_bytes() for p in self.files})
        self.assertEqual((self.root / changed[0]).read_bytes(), b"independent third version")

    def test_every_affected_sibling_is_selected_by_source_not_a_fixed_id(self):
        manifest = copy.deepcopy(self.manifest)
        sibling = copy.deepcopy(manifest["fixtures"][1])
        sibling["id"] = "second-reviewed-horos-binding"
        manifest["fixtures"].append(sibling)
        files = dict(self.files)
        files[air.MANIFEST] = air.codec.canonical_record_bytes(manifest)
        source = sibling["source"]["path"]
        updated, _, offsets, _ = air.derive(manifest, files, source, b"\n" + files[source])
        self.assertEqual(set(offsets), {"horos-boundary-check", sibling["id"]})
        for entry in updated["fixtures"]:
            if entry["source"]["path"] == source:
                self.assertEqual(entry["source"]["start"], str(int(sibling["source"]["start"]) + 1))

    def test_missing_or_duplicate_node_bytes_refuse_before_derivation(self):
        owner = air.prover.Reconciliation(self.root, checker=air.codec)
        for haystack, needle in ((b"anchor", b"absent"), (b"node node", b"node")):
            with self.subTest(haystack=haystack), self.assertRaises(air.prover.ProverError):
                owner._locate(haystack, needle, "reviewed node")

    def test_file_target_and_total_limits_refuse_without_live_writes(self):
        with air.Root(self.root) as root:
            with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-LIMIT.FILE"):
                root.write("oversized", b"x" * (air.MAX_FILE_BYTES + 1), fresh=True)
            self.assertFalse((self.root / "oversized").exists())
            with mock.patch.object(air, "MAX_TARGETS", 2):
                with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-LIMIT.TARGETS"):
                    air.closure(self.manifest)
            with mock.patch.object(air, "MAX_TOTAL_BYTES", 10):
                with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-LIMIT.TOTAL"):
                    air.materialize(root, "over-total", {"one": b"x" * 11})
            self.assertFalse((self.root / "over-total").exists())

    def test_writer_detects_target_replacement_while_temporary_file_is_flushed(self):
        target = self.root / "victim"; target.write_bytes(b"old")
        real_fsync = os.fsync
        injected = []

        def fsync(fd):
            if not injected and air.stat.S_ISREG(os.fstat(fd).st_mode):
                target.write_bytes(b"third version")
                injected.append(True)
            return real_fsync(fd)

        with air.Root(self.root) as root:
            _, key = root.read("victim")
            with mock.patch.object(air.os, "fsync", side_effect=fsync):
                with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-TARGET.RACE"):
                    root.write("victim", b"planned", expected=key)
        self.assertEqual(target.read_bytes(), b"third version")

    def test_final_publication_syscall_preserves_concurrent_version(self):
        target = self.root / "victim"; target.write_bytes(b"old")
        injected = []
        exchange = getattr(air, "exchange_files", None)
        replace = os.replace

        def inject(*args, **kwargs):
            if not injected:
                target.write_bytes(b"third version")
                injected.append(True)
            return exchange(*args, **kwargs) if exchange else replace(*args, **kwargs)

        with air.Root(self.root) as root:
            _, key = root.read("victim")
            patch = mock.patch.object(air, "exchange_files", side_effect=inject) if exchange else mock.patch.object(air.os, "replace", side_effect=inject)
            with patch:
                caught = None
                try:
                    root.write("victim", b"planned", expected=key)
                except air.ReconciliationError as error:
                    caught = error
            self.assertIsNotNone(caught, "publication accepted and lost the concurrent version")
            self.assertTrue(injected)
            self.assertEqual(caught.conflict["target"], "victim")
            self.assertEqual(root.read(caught.conflict["path"])[0], b"third version")
            self.assertEqual(caught.conflict["sha256"], air.sha(b"third version"))

    def test_exchange_preserves_third_and_fourth_versions_without_exchange_back(self):
        target = self.root / "victim"; target.write_bytes(b"old")
        exchange = air.exchange_files; calls = []

        def inject(*args):
            target.write_bytes(b"third version")
            exchange(*args); calls.append(True)
            target.write_bytes(b"fourth version")

        with air.Root(self.root) as root:
            _, key = root.read("victim")
            with mock.patch.object(air, "exchange_files", side_effect=inject):
                with self.assertRaises(air.ReconciliationError) as caught:
                    root.write("victim", b"planned", expected=key)
            self.assertEqual(len(calls), 1)
            self.assertEqual(root.read(caught.exception.conflict["path"])[0], b"third version")
            self.assertEqual(target.read_bytes(), b"fourth version")

    def test_journalled_exchange_conflict_blocks_apply_and_recovery(self):
        for same_bytes in (False, True):
            with self.subTest(same_bytes=same_bytes):
                self.root = Path(self.temp.name).resolve() / ("same" if same_bytes else "third")
                shutil.copytree(self.base, self.root, copy_function=shutil.copy2)
                result, _, _, _ = self.prepare()
                exchange = air.exchange_files; injected = []

                def inject(source_fd, source, target_fd, target):
                    if not injected:
                        original = os.open(target, os.O_RDONLY, dir_fd=target_fd)
                        body = os.read(original, air.MAX_FILE_BYTES); os.close(original)
                        replacement = os.open("independent", os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644, dir_fd=target_fd)
                        os.write(replacement, body if same_bytes else b"third version"); os.close(replacement)
                        os.replace("independent", target, src_dir_fd=target_fd, dst_dir_fd=target_fd)
                        injected.append(body if same_bytes else b"third version")
                    return exchange(source_fd, source, target_fd, target)

                output = io.StringIO()
                with contextlib.redirect_stdout(output), mock.patch.object(air, "exchange_files", side_effect=inject):
                    with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-APPLY.RECOVERY") as caught:
                        air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"])
                descriptor = caught.exception.conflict
                self.assertEqual((self.root / descriptor["path"]).read_bytes(), injected[0])
                self.assertEqual(descriptor["sha256"], air.sha(injected[0]))
                event = json.loads(output.getvalue())
                before = {p: (self.root / p).read_bytes() for p in self.files}
                with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-TARGET.CONFLICT"):
                    air.recover(self.root, journal_sha256=event["journal_sha256"])
                self.assertTrue((self.root / air.ACTIVE).exists())
                self.assertEqual(before, {p: (self.root / p).read_bytes() for p in self.files})
                self.assertEqual((self.root / descriptor["path"]).read_bytes(), injected[0])

    def test_recovery_exchange_retains_a_new_conflict(self):
        result, _, _, _ = self.prepare()
        exchange = air.exchange_files; calls = []

        def inject(source_fd, source, target_fd, target):
            calls.append(True)
            if len(calls) == 2:
                fd = os.open(target, os.O_WRONLY | os.O_TRUNC, dir_fd=target_fd)
                os.write(fd, b"third during restoration"); os.close(fd)
            return exchange(source_fd, source, target_fd, target)

        def fault(phase, path):
            if phase == "target-published":
                raise OSError("handled fault requires restoration")

        output = io.StringIO()
        with contextlib.redirect_stdout(output), mock.patch.object(air, "exchange_files", side_effect=inject):
            with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-APPLY.RECOVERY") as caught:
                air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"], phase_hook=fault)
        descriptor = caught.exception.conflict
        self.assertEqual((self.root / descriptor["path"]).read_bytes(), b"third during restoration")
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-TARGET.CONFLICT"):
            air.recover(self.root, journal_sha256=json.loads(output.getvalue())["journal_sha256"])
        self.assertEqual(len(calls), 2)

    def test_sigkill_immediately_after_exchange_recovers_retained_slot(self):
        result, source, edited, _ = self.prepare()
        script = """import sys,time
sys.path.insert(0,sys.argv[1])
import agent_instruction_reconciliation as a
real=a.exchange_files
def exchange(*args):
 real(*args)
 print('EXCHANGED',flush=True)
 time.sleep(60)
a.exchange_files=exchange
a.apply(sys.argv[2],stage='tmp/stage',plan_sha256=sys.argv[3])
"""
        child = subprocess.Popen([sys.executable, "-c", script, str(ROOT / "scripts"), str(self.root), result["plan_sha256"]],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            event = json.loads(child.stdout.readline())
            self.assertEqual(child.stdout.readline().strip(), "EXCHANGED")
            child.kill(); child.communicate(timeout=10)
            self.assertEqual(child.returncode, -9)
        finally:
            if child.poll() is None:
                child.kill(); child.communicate(timeout=10)
        self.assertEqual(air.recover(self.root, journal_sha256=event["journal_sha256"])["outcome"], "recovered")
        for path, body in self.files.items():
            self.assertEqual((self.root / path).read_bytes(), edited if path == source else body)

    def test_exchange_refuses_unsupported_hosts_and_keeps_stable_identity(self):
        target = self.root / "victim"; target.write_bytes(b"old")
        with air.Root(self.root) as root:
            _, key = root.read("victim")
            with mock.patch.object(air.sys, "platform", "unsupported"), mock.patch.object(air.os, "replace", side_effect=AssertionError("unsafe fallback")):
                with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-EXCHANGE.UNSUPPORTED"):
                    root.write("victim", b"planned", expected=key)
            self.assertEqual(root.read("victim")[0], b"old")
            root.write("victim", b"planned", expected=key)
            slots = list(self.root.glob(".air-*"))
            self.assertEqual(len(slots), 1)
            retained, retained_key = root.read(slots[0].name)
            self.assertEqual(retained, b"old")
            self.assertEqual(retained_key[:-1], key[:-1])

    def test_stage_race_after_journal_blocks_publication(self):
        result, source, edited, _ = self.prepare()

        def fault(phase, path):
            if phase == "journal-durable":
                (self.root / "tmp/stage/work" / air.MANIFEST).write_bytes(b"tampered")

        with contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(air.ReconciliationError, "AIR-E-APPLY.RECOVERY"):
            air.apply(self.root, stage="tmp/stage", plan_sha256=result["plan_sha256"], phase_hook=fault)
        for path, body in self.files.items():
            self.assertEqual((self.root / path).read_bytes(), edited if path == source else body)
        self.assertTrue((self.root / air.ACTIVE).exists())

    def test_output_and_wall_time_limits_kill_the_bounded_command(self):
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-COMMAND.OUTPUT"):
            air.bounded_command([sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'x'*(2**20+1))"], self.root)
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-COMMAND.TIMEOUT"):
            air.bounded_command([sys.executable, "-c", "import time;time.sleep(60)"], self.root, timeout=0.05)

    def test_legacy_law_and_horos_selection_is_the_behavioral_counterfactual(self):
        for fixture_id in ("horos-boundary-check", "promise-machine-router-selection"):
            source, _, _ = self.edit(fixture_id)
            with self.subTest(fixture=fixture_id):
                with self.assertRaisesRegex(air.prover.ProverError, "has drifted elsewhere"):
                    air.prover.LiveReconciliation(self.root, checker=air.codec)
                current = air.prepare(self.root, baseline=self.commit, source=source, stage="tmp/" + fixture_id)
                self.assertEqual(current["affected_fixtures"], [fixture_id])
                self.assertEqual(current["outcome"], "ready")
            (self.root / source).write_bytes(self.files[source])


class DemonstrationVerificationTests(unittest.TestCase):
    RECORD = "docs/agent-instruction-reconciliation/demonstration.json"

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="air-demo-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.value = json.loads((ROOT / self.RECORD).read_bytes())
        for path in [self.RECORD, *self.value["dependencies"]]:
            destination = self.root / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / path, destination)

    def save(self):
        (self.root / self.RECORD).write_bytes(air.encoded(self.value))

    def replace(self, path, body):
        (self.root / path).write_bytes(body)
        self.value["dependencies"][path] = air.sha(body)

    def test_record_verifies_with_no_git_history_subprocess_or_model(self):
        with mock.patch.object(air, "bounded_command", side_effect=AssertionError("offline verifier started a subprocess")):
            result = air.verify_demonstration(self.root, self.RECORD)
        self.assertEqual(set(result), {"schema", "outcome", "record_sha256", "structural_placements",
                                     "complete_law_repairs", "unchanged_reviewed_bindings", "verified_dependencies"})
        self.assertEqual(result["structural_placements"], 6)
        self.assertEqual(result["complete_law_repairs"], 1)
        self.assertEqual(result["unchanged_reviewed_bindings"], 15)

    def test_every_declared_dependency_is_checked_including_unused_raw_attempts(self):
        path = next(iter(self.value["dependencies"]))
        (self.root / path).write_bytes(b"changed after recording")
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-DEMO.DIGEST"):
            air.verify_demonstration(self.root, self.RECORD)

    def test_missing_preserved_tree_object_does_not_fetch_history(self):
        del self.value["baseline"]["objects"]["tree:" + self.value["baseline"]["tree"]]
        self.save()
        with mock.patch.object(air, "bounded_command", side_effect=AssertionError("fetch")):
            with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-DEMO.OBJECT"):
                air.verify_demonstration(self.root, self.RECORD)

    def test_rehashed_old_writer_cannot_replace_demonstrated_implementation(self):
        path = self.value["boundary"]["implementation"]["scripts/agent_instruction_reconciliation.py"]
        self.replace(path, (self.root / path).read_bytes() + b"\n# changed implementation\n")
        self.save()
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-DEMO.BOUNDARY"):
            air.verify_demonstration(self.root, self.RECORD)

    def test_self_rehashed_invalid_measurement_still_fails_owner_semantics(self):
        law = next(case for case in self.value["cases"] if case["accepted"] is not None)
        mapping = law["accepted"]
        report_path = mapping[air.prover.MEASUREMENT]
        report = json.loads((self.root / report_path).read_bytes())
        report["documents"][0]["canonical_model"]["tokens"] += 1
        self.replace(report_path, air.codec.canonical_record_bytes(report, allow_integers=True))
        manifest_path = mapping[air.MANIFEST]
        manifest = json.loads((self.root / manifest_path).read_bytes())
        manifest["evidence"]["measurement_record"]["sha256"] = air.sha((self.root / report_path).read_bytes())
        self.replace(manifest_path, air.codec.canonical_record_bytes(manifest))
        accepted = {name: (self.root / path).read_bytes() for name, path in mapping.items()}
        coverage_path = mapping[air.COVERAGE]
        coverage, _ = air.rebind_coverage((self.root / coverage_path).read_bytes(), accepted)
        self.replace(coverage_path, coverage)
        self.save()
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-CHECK"):
            air.verify_demonstration(self.root, self.RECORD)

    def test_declared_success_does_not_replace_missing_kill_observation(self):
        path = self.value["boundary"]["observations"]
        observations = json.loads((self.root / path).read_bytes())
        del observations["tests"]["test_actual_sigkill_blocks_next_operation_and_recovery_is_idempotent"]
        self.replace(path, air.encoded(observations)); self.save()
        with self.assertRaisesRegex(air.ReconciliationError, "AIR-E-DEMO.BOUNDARY"):
                air.verify_demonstration(self.root, self.RECORD)


class ReconciliationCoverageTests(unittest.TestCase):
    def test_coverage_binds_staged_runtime_and_its_behavioral_guards(self):
        row = json.loads((ROOT / air.COVERAGE).read_bytes())["agent_instruction"]["staged_reconciliation"]
        self.assertEqual(set(row), {"helper", "tests"})
        for role, path in (("helper", "scripts/agent_instruction_reconciliation.py"),
                           ("tests", "tests/test_agent_instruction_reconciliation.py")):
            self.assertEqual(row[role], {"path": path, "sha256": air.sha((ROOT / path).read_bytes())})


if __name__ == "__main__":
    unittest.main()
