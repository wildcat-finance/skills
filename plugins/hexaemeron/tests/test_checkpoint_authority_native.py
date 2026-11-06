"""Hostile native-boundary cases and independent coverage of real Git history."""
import copy
from dataclasses import replace
import errno
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile
from checkpoint_authority_native_fixture import FIXTURES, approval, fixture, request
from checkpoint_authority import native, native_io as io, native_records as records
from checkpoint_authority.canonical import Refusal, canonical, decode, digest
from checkpoint_authority.coverage import derive, verify_complete


class Temporary(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.root.chmod(0o700)

    def refuses(self, code, function, *args, **kwargs):
        with self.assertRaises(Refusal) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def attempt(self):
        value = native._Attempt.__new__(native._Attempt)
        value.root, value.request, value.approval = self.root, request(), approval()
        value.stages, value.environment = [], {}
        value.started = time.monotonic(); value.deadline = value.started + 10
        value.pin = native.NativePin(self.root, ())
        return value

    def execution(self, stage="inspect", **changes):
        return replace(io.Execution(stage, request().attempt_id, request().outer_sha256,
            0, b"{}", b"", 1), **changes)


class NativeFixtureTests(unittest.TestCase):
    def test_fixture_public_key_uses_closed_step_two_shape(self):
        self.assertEqual(approval().keys()[0]["key"]["algorithm"], "openpgp")

    def test_fixture_has_independent_public_keys_and_four_real_commit_ranges(self):
        value = fixture()
        self.assertTrue(value["producer_private_home_removed"])
        self.assertEqual(value["public_secret_key_count"], 0)
        self.assertEqual(len(value["required"]), 4)
        self.assertEqual(len(value["native_expected"]), 2)
        self.assertEqual(len(value["historical_required"]), 2)
        self.assertTrue(value["synthetic_github"] and value["synthetic_observations"])


class NativeRecordsTests(Temporary):
    def test_actual_native_schemas_and_no_invented_identity_status(self):
        value = fixture()["original_outputs"]
        records.inspect_result(value["inspect"])
        records.restore_result(value["restore"])
        records.identity_result(value["identity"])
        self.assertNotIn("status", value["identity"]["identity"])
        value["identity"]["identity"]["status"] = "bound"
        self.refuses("native-output-shape", records.identity_result, value["identity"])

    def test_missing_unknown_nested_fields_and_false_integer_refuse(self):
        for stage, function in (("inspect", records.inspect_result), ("restore", records.restore_result), ("identity", records.identity_result)):
            for field in fixture()["original_outputs"][stage]:
                with self.subTest(stage=stage, field=field):
                    value = fixture()["original_outputs"][stage]; value.pop(field)
                    self.refuses("native-output-shape", function, value)
        value = fixture()["original_outputs"]["restore"]
        value["restore"]["ledger_entries"] = True
        self.refuses("native-output-shape", records.restore_result, value)

    def test_restore_success_must_join_nested_success_status_and_next(self):
        for mutate in (lambda v: v.update(verify="failed"),
                       lambda v: v["restore"].update(verify="failed"),
                       lambda v: v["restore"].update(status_sha256="a" * 64),
                       lambda v: v["restore"].update(next={}),
                       lambda v: v["restore"].update(recovery="existing")):
            value = fixture()["original_outputs"]["restore"]; mutate(value)
            self.refuses("native-restore-join", records.restore_result, value)

    def test_unbound_inspect_identity_and_duplicate_proof_refuse(self):
        value = fixture()["original_outputs"]["inspect"]
        value["identity"]["status"] = "unavailable"
        self.refuses("native-identity-unavailable", records.inspect_result, value)
        value = fixture()["original_outputs"]["inspect"]
        value["signatures"].append(value["signatures"][0])
        self.refuses("native-coverage-duplicate", records.inspect_result, value)

    def test_identity_digest_and_observations_are_required(self):
        value = fixture()["original_outputs"]["identity"]
        value["snapshot_id"] = "a" * 64
        self.refuses("native-identity-digest", records.identity_result, value)
        value = fixture()["original_outputs"]["identity"]
        value["identity"]["evidence"]["observation_status"] = "absent"
        self.refuses("native-identity-join", records.identity_result, value)

    def test_native_manifest_digest_includes_exact_lf(self):
        meta = records.metadata(FIXTURES / "checkpoint.zip")
        self.assertEqual(digest(meta.manifest_bytes), request().controller_manifest_sha256)
        self.assertEqual(canonical(meta.manifest) + b"\n", meta.manifest_bytes)
        self.assertNotEqual(digest(canonical(meta.manifest)), request().controller_manifest_sha256)
        for replacement in (canonical(meta.manifest), meta.manifest_bytes + b"\n"):
            archive = self.root / (str(len(replacement)) + ".zip")
            with zipfile.ZipFile(FIXTURES / "checkpoint.zip") as source, zipfile.ZipFile(archive, "w") as destination:
                for row in source.infolist():
                    destination.writestr(row, replacement if row.filename == records.MEMBERS[1] else source.read(row))
            self.refuses("native-manifest-encoding", records.metadata, archive)

    def test_metadata_wrong_object_types_refuse_without_traceback(self):
        for index, replacement in enumerate(([], {"schema": "fiat-controller-checkpoint/v1", "source": []})):
            archive = self.root / ("shape-" + str(index) + ".zip")
            with zipfile.ZipFile(FIXTURES / "checkpoint.zip") as source, zipfile.ZipFile(archive, "w") as destination:
                for row in source.infolist():
                    destination.writestr(row, canonical(replacement) + b"\n" if row.filename == records.MEMBERS[1] else source.read(row))
            with self.subTest(index=index), self.assertRaises(Refusal): records.metadata(archive)

    def test_private_custody_and_nested_restore_refuse_before_native(self):
        meta = records.metadata(FIXTURES / "checkpoint.zip")
        for field in ("known_failure_inventory", "worker_probe", "guard_report", "replacement_recovery"):
            value = meta.state
            value["receipts"][field] = {"path": "/must-not-read"}
            self.refuses("native-private-custody-unavailable", records.custody, value, meta.entries)
        entries = meta.entries; entries.append({"event": "checkpoint:restore", "data": {}})
        self.refuses("native-nested-restore-unavailable", records.custody, meta.state, entries)

    def test_unsupported_history_and_corrupt_ledger_are_unavailable(self):
        meta = records.metadata(FIXTURES / "checkpoint.zip")
        entries = meta.entries; entries.append({"event": "execute:guard", "data": {"command": "must-not-run"}})
        self.refuses("native-history-class-unavailable", records.custody, meta.state, entries)
        rows = meta.entries; rows[-1]["prev"] = "a" * 64
        self.refuses("native-producer-ledger", records.ledger, b"".join(canonical(row) + b"\n" for row in rows))


class NativeAttemptTests(Temporary):
    def test_stage_order_and_current_attempt_binding(self):
        for changed in ({"attempt_id": "old"}, {"input_sha256": "a" * 64}, {"stage": "identity"}, {"exit": True}):
            with self.subTest(changed=changed), patch.object(io, "execute", return_value=self.execution(**changed)), patch.object(native.NativePin, "tool", return_value=None):
                self.refuses("native-current-attempt", self.attempt().command, "python", [], self.root, "inspect")
        with patch.object(io, "execute", return_value=self.execution("restore")), patch.object(native.NativePin, "tool", return_value=None):
            self.refuses("native-stage-order", self.attempt().command, "python", [], self.root, "restore")

    def test_each_nonzero_native_stage_refuses_and_preserves_logs(self):
        for index, stage in enumerate(("inspect", "restore", "verify", "identity")):
            attempt = self.attempt(); attempt.stages = [{}] * index
            with patch.object(io, "execute", return_value=self.execution(stage, exit=1, stderr=b"private key identifier")), patch.object(native.NativePin, "tool", return_value=None):
                self.refuses("native-command-failed", attempt.command, "python", [], self.root, stage)
            self.assertEqual((self.root / (stage + ".stderr")).read_bytes(), b"private key identifier")
            self.assertNotIn("identifier", json.dumps(attempt.stages[-1]))

    def test_failed_restore_cannot_be_rescued_by_verify(self):
        attempt = self.attempt(); stages = []
        def command(stage, args):
            stages.append(stage)
            if stage == "restore": raise Refusal("native-command-failed", stage)
            return self.execution(stage, stdout=canonical(fixture()["original_outputs"][stage]))
        with patch.object(attempt, "seed"), patch.object(attempt, "native", side_effect=command):
            self.refuses("native-command-failed", attempt.run, FIXTURES / "checkpoint.zip")
        self.assertEqual(stages, ["inspect", "restore"])

    def test_input_length_digest_and_identity_cannot_cross_attempts(self):
        for field, value, code in (("carrier_length", 1, "native-input-length"),
                ("outer_sha256", "a" * 64, "native-input-digest"),
                ("controller_manifest_sha256", "a" * 64, "native-controller-manifest")):
            with tempfile.TemporaryDirectory() as directory:
                attempt = self.attempt(); attempt.root = Path(directory).resolve()
                attempt.request = replace(request(), **{field: value})
                with patch.object(attempt, "native") as command:
                    self.refuses(code, attempt.run, FIXTURES / "checkpoint.zip")
                    command.assert_not_called()

    def test_missing_history_and_existing_attempt_do_not_execute(self):
        with patch.object(native._Attempt, "run") as run:
            self.refuses("native-trust-required", native.verify_native, FIXTURES / "checkpoint.zip",
                job_root=self.root, pin=native.NativePin(self.root, ()), request=request(), approval=replace(approval(), history=()))
            (self.root / request().attempt_id).mkdir(mode=0o700)
            self.refuses("native-attempt-exists", native.verify_native, FIXTURES / "checkpoint.zip",
                job_root=self.root, pin=native.NativePin(self.root, ()), request=request(), approval=approval())
            run.assert_not_called()

    def test_symlink_ancestors_hardlinks_and_scratch_swap_refuse(self):
        target = self.root / "directory"; target.mkdir(mode=0o700)
        link = self.root / "link"; link.symlink_to(target)
        admitted = False
        with self.assertRaises((OSError, Refusal)) as caught:
            with io.directory(link): admitted = True
        self.assertFalse(admitted)
        if isinstance(caught.exception, Refusal):
            self.assertEqual(caught.exception.code, "native-path-changed")
        else:
            self.assertIn(caught.exception.errno, (errno.ELOOP, errno.ENOTDIR))
        source = self.root / "file"; source.write_bytes(b"x")
        os.link(source, self.root / "hardlink")
        self.refuses("native-file-limit-or-kind", io.read, source)
        with self.assertRaises(Refusal):
            with io.directory(target) as (_, check):
                target.rename(self.root / "old"); target.mkdir(mode=0o700); check()

    def test_public_trust_intervals_are_closed_and_unambiguous(self):
        value = approval(); row = decode(value.history[0]); row["first_step"] = True
        self.refuses("native-output-shape", replace(value, history=(canonical(row),)).keys)
        self.refuses("native-key-history-duplicate", replace(value, history=value.history * 2).keys)
        row = decode(value.history[0]); row["first_step"] = 2
        self.refuses("native-key-history-ambiguous", replace(value, history=(*value.history, canonical(row))).keys)


class NativeProcessTests(Temporary):
    def invoke(self, code, *, seconds=3):
        path = Path(sys.executable).resolve()
        tool = io.NativeTool("python", str(path), hashlib.sha256(path.read_bytes()).hexdigest())
        return io.execute(tool, ["-I", "-c", code], self.root, {"PATH": os.defpath},
            stage="inspect", attempt_id="process-test", input_sha256="a" * 64,
            deadline=time.monotonic() + seconds)

    def test_actual_executor_captures_both_streams_and_exit(self):
        result = self.invoke("import os;os.write(1,b'out');os.write(2,b'err');raise SystemExit(9)")
        self.assertEqual((result.exit, result.stdout, result.stderr), (9, b"out", b"err"))

    def test_output_caps_are_refusals_not_truncation(self):
        for fd, cap in ((1, io.STDOUT_MAX), (2, io.STDERR_MAX)):
            with self.subTest(fd=fd):
                self.refuses("native-output-limit", self.invoke, f"import os;os.write({fd},b'x'*{cap + 1})")

    def test_deadline_stops_live_process(self):
        start = time.monotonic()
        self.refuses("native-deadline", self.invoke, "import time;time.sleep(5)", seconds=0.1)
        self.assertLess(time.monotonic() - start, 2)

    def test_leader_exit_does_not_leave_descendant_alive(self):
        marker = self.root / "escaped"
        code = ("import os,time;pid=os.fork();"
                "\nif pid==0:\n os.close(1);os.close(2);time.sleep(.4);open(" + repr(str(marker)) + ",'w').write('bad')\n"
                "else: os._exit(0)")
        result = self.invoke(code)
        self.assertEqual(result.exit, 0)
        time.sleep(0.5)
        self.assertFalse(marker.exists())


class NativeCoverageTests(Temporary):
    def setUp(self):
        super().setUp()
        self.meta = records.metadata(FIXTURES / "checkpoint.zip")
        self.ident = fixture()["original_outputs"]["identity"]
        self.inspected = fixture()["original_outputs"]["inspect"]
        self.repository = self.root / "repository"; self.repository.mkdir()
        self.git_path = shutil.which("git")
        self.git(["init", "-q"])
        bundle = self.root / "history.bundle"
        with zipfile.ZipFile(FIXTURES / "checkpoint.zip") as archive:
            bundle.write_bytes(archive.read("git/repository.bundle"))
        self.git(["fetch", "--no-tags", str(bundle), "+refs/*:refs/*"])

    def git(self, args):
        result = subprocess.run([self.git_path, "--no-replace-objects", "-c", "core.hooksPath=/dev/null", *args],
            cwd=self.repository, capture_output=True, timeout=10,
            env={"PATH": os.defpath, "HOME": str(self.root), "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"})
        if result.returncode: raise Refusal("native-command-failed", "coverage")
        return result.stdout

    def denominator(self, meta=None):
        return derive(meta or self.meta, self.ident, approval(), self.git)

    def mutated(self, change):
        state, entries = self.meta.state, self.meta.entries
        change(state, entries)
        # These are post-native boundary interface tests, not native-admitted archives.
        previous = "genesis"
        for row in entries:
            row["prev"] = previous
            row["hash"] = digest(canonical({k:v for k,v in row.items() if k != "hash"}))
            previous = row["hash"]
        return replace(self.meta, state_bytes=canonical(state), ledger_bytes=b"".join(canonical(r)+b"\n" for r in entries))

    def test_actual_dag_union_includes_both_steps_and_push_only_commits(self):
        result = self.denominator()
        self.assertEqual(result["required"], sorted(fixture()["required"]))
        self.assertEqual(result["native_expected"], sorted(fixture()["native_expected"]))
        self.assertEqual([row["kind"] for row in result["ranges"]], ["implementation", "push", "implementation", "push"])
        self.assertFalse(result["base_history"]["local_governed_signature_claim"])
        self.assertNotIn(approval().initial_base, result["required"])
        self.assertNotIn(approval().start_commit, result["required"])

    def test_embedded_missing_extra_duplicate_ranges_never_define_denominator(self):
        for replacement in ([], [approval().initial_base], fixture()["required"][:1] * 2):
            def change(state, entries):
                state["steps"][0]["receipts"]["push"]["verified_commits"] = replacement
                next(e for e in entries if e["event"]=="done:push")["data"]["verified_commits"] = replacement
            with self.subTest(replacement=replacement), self.assertRaises(Refusal):
                self.denominator(self.mutated(change))

    def test_unlisted_real_dag_commit_refuses(self):
        original = self.git
        def extra(args):
            result = original(args)
            if args[0] == "rev-list": return approval().initial_base.encode() + b"\n" + result
            return result
        self.refuses("native-range-coverage", derive, self.meta, self.ident, approval(), extra)

    def test_missing_actual_objects_and_moved_refs_refuse(self):
        self.git(["update-ref", "refs/heads/fiat/test-topic-step-1-first", approval().initial_base])
        self.refuses("native-step-ref-moved", self.denominator)

    def test_native_proof_is_exact_current_subset_not_complete_history(self):
        denominator = self.denominator()
        signer = fixture()["fingerprint"]
        result = verify_complete(denominator, self.inspected, approval(), lambda sha: signer)
        self.assertEqual(len(result["verified"]), 4)
        self.assertEqual(len(result["historical_required"]), 2)
        for claims in ([], self.inspected["signatures"] + [dict(self.inspected["signatures"][0], sha=fixture()["historical_required"][0])]):
            self.refuses("native-current-boundary-coverage", verify_complete, denominator,
                dict(self.inspected, signatures=claims), approval(), lambda sha: signer)

    def test_historical_sigs_require_historical_approval_not_uploader(self):
        denominator = self.denominator(); seen = []
        def verify(sha): seen.append(sha); return fixture()["fingerprint"]
        self.refuses("native-signer-unapproved", verify_complete, denominator, self.inspected, approval(first_step=2), verify)
        other_actor = decode(approval().history[0]); other_actor["actor_id"] = 987654321
        approved = replace(approval(), history=(canonical(other_actor),))
        result = verify_complete(denominator, self.inspected, approved, verify)
        self.assertEqual({r["commit"] for r in result["verified"]}, set(fixture()["required"]))

    def test_untrusted_or_contradictory_historical_signatures_refuse(self):
        self.refuses("native-signer-unapproved", verify_complete, self.denominator(), self.inspected,
            approval(), lambda sha: "F" * 40)
        value = copy.deepcopy(self.inspected); value["signatures"][0]["fingerprint"] = "F" * 40
        self.refuses("native-signature-contradiction", verify_complete, self.denominator(), value,
            approval(), lambda sha: fixture()["fingerprint"])

    def test_platform_only_merge_class_never_becomes_local_signature(self):
        def change(state, entries):
            state["steps"][0]["receipts"]["push"]["merge_commit"] = approval().initial_base
            next(e for e in entries if e["event"]=="done:push")["data"]["merge_commit"] = approval().initial_base
        self.refuses("native-platform-evidence-unavailable", self.denominator, self.mutated(change))


if __name__ == "__main__": unittest.main()
