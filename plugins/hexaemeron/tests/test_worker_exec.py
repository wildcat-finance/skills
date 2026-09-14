"""Native worker effects, lifetime and admission boundaries."""

import ctypes
import errno
import importlib.util
import json
import os
from pathlib import Path
import platform
import signal
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "skills/fiat/scripts/worker_exec.py"
SPEC = importlib.util.spec_from_file_location("fiat_worker_exec", SCRIPT)
worker = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = worker
SPEC.loader.exec_module(worker)
PYTHON = str(Path(sys.executable).resolve())


@unittest.skipUnless(platform.system() == "Darwin", "native Darwin policy required")
class ControllerLaunchTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        helper_spec = importlib.util.spec_from_file_location("launch_proofs", Path(__file__).with_name("prove_issue_508.py"))
        self.proofs = importlib.util.module_from_spec(helper_spec)
        helper_spec.loader.exec_module(self.proofs)
        self.controller = SCRIPT.with_name("hexctl.py")

    def launch(self):
        request = self.proofs.dispatch_request(self.root,
                    "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('immutable')")
        return worker.controller_launch(self.root, request, self.controller)

    def test_controller_dispatch_conformance_uses_real_tools_and_detached_writer(self):
        self.proofs.execute("whole-launch-dispatch", self.root)

    def test_origin_drift_is_preserved_and_fresh_launch_resnapshots(self):
        self.proofs.execute("origin-drift-recovery", self.root)

    def test_receipt_digest_mismatch_never_promotes(self):
        launch = self.launch()
        with self.assertRaisesRegex(worker.Refusal, "launch-receipt-mismatch"):
            worker.controller_admit(self.root, launch["receipt"], "0"*64, self.controller)
        self.assertFalse((self.root / ".hexaemeron/reports/result.json").exists())

    def test_private_snapshot_replacement_and_source_change_refuse(self):
        launch = self.launch()
        snapshot = Path(launch["record"]["capture"]["snapshot"]) / "result.json"
        snapshot.chmod(0o600)
        snapshot.write_text("replaced")
        with self.assertRaisesRegex(worker.Refusal, "private-snapshot-mismatch"):
            worker.controller_admit(self.root, launch["receipt"], launch["sha256"], self.controller)
        other_source = self.root / "controller.py"
        other_source.write_text("changed")
        with self.assertRaisesRegex(worker.Refusal, "stale-launch-receipt"):
            worker.controller_admit(self.root, launch["receipt"], launch["sha256"], other_source)

    def test_destination_alias_and_existing_bytes_are_never_overwritten(self):
        launch = self.launch()
        destination = self.root / ".hexaemeron/reports/result.json"
        original = self.root / "outside"
        original.write_text("preserve")
        destination.symlink_to(original)
        with self.assertRaises(FileExistsError):
            worker.controller_admit(self.root, launch["receipt"], launch["sha256"], self.controller)
        self.assertEqual(original.read_text(), "preserve")

    def test_request_rejects_metadata_destinations_and_duplicate_operands(self):
        request = self.proofs.dispatch_request(self.root, "pass")
        request["reports"][0]["source"] = ".hexaemeron/state.json"
        with self.assertRaisesRegex(worker.Refusal, "invalid-report-destination"):
            worker.controller_launch(self.root, request, self.controller)
        request = self.proofs.dispatch_request(self.root, "pass")
        request["reports"].append(dict(request["reports"][0]))
        with self.assertRaisesRegex(worker.Refusal, "duplicate-report-destination"):
            worker.controller_launch(self.root, request, self.controller)

    def test_origin_changes_before_capture_returns_refuse_without_rollback(self):
        origin = self.root / "user.txt"
        origin.write_text("before")
        request = self.proofs.dispatch_request(self.root,
                    "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('candidate')",
                    origin={"root": str(self.root), "paths": ["user.txt"]})
        real_run = worker.run_worker
        def independent_change(*args, **kwargs):
            capture = real_run(*args, **kwargs)
            origin.write_text("independent")
            return capture
        with mock.patch.object(worker, "run_worker", side_effect=independent_change):
            launch = worker.controller_launch(self.root, request, self.controller)
        self.assertEqual(launch["record"]["origin_status"], "changed-unattributed")
        self.assertEqual(launch["record"]["status"], "refused")
        self.assertEqual(launch["record"]["attribution"], "unknown")
        self.assertEqual(origin.read_text(), "independent")
        with self.assertRaisesRegex(worker.Refusal, "stale-launch-receipt"):
            worker.controller_admit(self.root, launch["receipt"], launch["sha256"], self.controller)

    def test_promotion_is_one_shot_and_controller_metadata_alias_refuses(self):
        launch = self.launch()
        result = worker.controller_admit(self.root, launch["receipt"], launch["sha256"], self.controller)
        self.assertEqual(result["status"], "admitted")
        with self.assertRaises(FileExistsError):
            worker.controller_admit(self.root, launch["receipt"], launch["sha256"], self.controller)
        fresh = self.root / "fresh"
        fresh.mkdir()
        (fresh / ".hexaemeron").symlink_to(self.root / ".hexaemeron", target_is_directory=True)
        with self.assertRaises(OSError):
            worker.controller_launch(fresh, self.proofs.dispatch_request(fresh, "pass"), self.controller)

    def test_multiple_reports_keep_their_source_mapping_and_shared_cap(self):
        request = self.proofs.dispatch_request(self.root,
                    "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('aa'); "
                    "pathlib.Path(sys.argv[2]).write_text('bbb')")
        request["argv"].append(".hexaemeron/reports/second.json")
        request["reports"].append({"index": 5, "source": request["argv"][5], "output": "a.json"})
        request["output_cap_bytes"] = 5
        launch = worker.controller_launch(self.root, request, self.controller)
        worker.controller_admit(self.root, launch["receipt"], launch["sha256"], self.controller)
        self.assertEqual((self.root / ".hexaemeron/reports/result.json").read_text(), "aa")
        self.assertEqual((self.root / ".hexaemeron/reports/second.json").read_text(), "bbb")
        fresh = self.root / "capped"
        fresh.mkdir()
        request["root"] = str(fresh)
        request["output_cap_bytes"] = 4
        refused = worker.controller_launch(fresh, request, self.controller)
        self.assertEqual(refused["record"]["status"], "refused")
        self.assertEqual(refused["record"]["capture"]["code"], "output-cap")

    def test_real_controller_directory_substitution_refuses_before_promotion(self):
        for relative in (".hexaemeron/reports", ".hexaemeron/worker-launches", ".hexaemeron"):
            with self.subTest(relative=relative), tempfile.TemporaryDirectory() as temp:
                root = Path(temp).resolve()
                request = self.proofs.dispatch_request(root,
                    "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('candidate')")
                launch = worker.controller_launch(root, request, self.controller)
                directory = root / relative
                retired = root / "retired-directory"
                directory.rename(retired)
                shutil.copytree(retired, directory)
                sentinel = directory / "independent.txt"
                sentinel.write_text("preserve")
                with self.assertRaisesRegex(worker.Refusal, "controller-directory-drift"):
                    worker.controller_admit(root, launch["receipt"], launch["sha256"], self.controller)
                self.assertEqual(sentinel.read_text(), "preserve")
                self.assertFalse((root / ".hexaemeron/reports/result.json").exists())

    def test_directory_rename_during_promotion_refuses_and_preserves_partial_evidence(self):
        launch = self.launch()
        original = worker._exclusive
        retired = self.root / "retired-controller"
        def replace_directory(directory, name, data):
            if name == "result.json":
                (self.root / ".hexaemeron").rename(retired)
                (self.root / ".hexaemeron/reports").mkdir(parents=True)
                (self.root / ".hexaemeron/reports/independent.txt").write_text("preserve")
            return original(directory, name, data)
        with mock.patch.object(worker, "_exclusive", side_effect=replace_directory):
            with self.assertRaisesRegex(worker.Refusal, "controller-directory-drift"):
                worker.controller_admit(self.root, launch["receipt"], launch["sha256"], self.controller)
        self.assertEqual((self.root / ".hexaemeron/reports/independent.txt").read_text(), "preserve")
        self.assertFalse((self.root / ".hexaemeron/reports/result.json").exists())
        # This interleaving occurs after the pre-check. The held descriptor
        # preserves the old directory; the post-check must refuse completion.
        self.assertEqual((retired / "reports/result.json").read_text(), "immutable")
        self.assertFalse(list((retired / "worker-launches").glob("*.complete.json")))


class RequestTests(unittest.TestCase):
    def test_unsupported_host_refuses_before_filesystem_effects(self):
        with mock.patch.object(worker.platform, "system", return_value="Unsupported"):
            with self.assertRaisesRegex(worker.Refusal, "unsupported-native-host"):
                worker.run_worker("/nonexistent", [PYTHON])

    def test_invalid_limits_and_tools_refuse_before_launch(self):
        for kwargs in ({"deadline_seconds": True}, {"deadline_seconds": float("nan")},
                       {"output_cap_bytes": True}, {"output_cap_bytes": 0},
                       {"tools": None}, {"tools": ["shell"]}):
            with self.subTest(kwargs=kwargs), self.assertRaises(worker.Refusal):
                worker.run_worker("/nonexistent", [PYTHON], **kwargs)

    def test_group_signals_precede_reaping_even_when_permission_is_denied(self):
        events = []
        process = mock.Mock(pid=1234)
        process.wait.side_effect = lambda **kw: events.append("wait")
        def killpg(pid, sig):
            events.append(sig)
            raise PermissionError("zombie-only group")
        with mock.patch.object(worker.os, "killpg", side_effect=killpg):
            self.assertEqual(worker._terminate(process), "signal-denied-retired")
        self.assertEqual(events, [signal.SIGTERM, signal.SIGKILL, "wait"])


@unittest.skipUnless(platform.system() == "Darwin", "native backend requires Darwin")
class NativeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def run_code(self, code, **kwargs):
        return worker.run_worker(self.root, [PYTHON, "-I", "-c", code],
                                 deadline_seconds=kwargs.pop("deadline_seconds", 5), **kwargs)

    def assert_captured(self, capture):
        self.assertEqual(capture.record["status"], "captured", (capture.record, capture.stderr))
        self.assertFalse(capture.record["scratch_reusable"])
        self.assertLessEqual(capture.record["stream_bytes"] + capture.record["artifact_bytes"],
                             capture.record["output_cap_bytes"])

    def assert_refused(self, capture, code=None):
        self.assertEqual(capture.record["status"], "refused", capture.record)
        self.assertIsNone(capture.record["snapshot"])
        self.assertEqual(capture.record["artifacts"], [])
        if code is not None:
            self.assertEqual(capture.record["code"], code, capture.record)

    def test_due_conformance_executes_deadline_and_exact_output_boundaries(self):
        sys.path.insert(0, str(Path(__file__).parent))
        import prove_issue_508
        for criterion in ("worker-deadline", "worker-output-cap"):
            with self.subTest(criterion=criterion):
                evidence = prove_issue_508.execute(criterion, self.root)
                self.assertTrue(evidence["captures"])
                self.assertTrue(evidence["specimens"])

    def test_supported_host_startup_imports_shell_and_private_snapshot(self):
        capture = self.run_code(
            "import os,ssl,sqlite3,lzma,decimal,compression.zstd,subprocess; "
            "subprocess.run(['/bin/sh','-c','printf shell'],check=True); "
            "open(os.environ['FIAT_OUTPUT_DIR']+'/result','wb').write(b'original')",
            outputs=["result"])
        self.assert_captured(capture)
        self.assertEqual(capture.stdout, b"shell")
        scratch = Path(capture.record["scratch_root"])
        (scratch / "output/result").write_bytes(b"changed")
        saved = Path(capture.record["snapshot"]) / "result"
        self.assertEqual(saved.read_bytes(), b"original")
        self.assertEqual(saved.stat().st_mode & 0o777, 0o400)
        self.assertIn("/bin/bash", [x["path"] for x in capture.record["executables"]])
        self.assertTrue(capture.record["runtime_dependencies"])

    def test_missing_root_read_is_a_real_supported_host_preflight_failure(self):
        original = worker.policy_text
        def broken(*args):
            return original(*args).replace('(allow file-read-data (literal "/"))', '')
        with mock.patch.object(worker, "policy_text", side_effect=broken):
            capture = self.run_code("print('must not run')")
        self.assert_refused(capture, "native-policy-preflight")
        self.assertEqual(capture.stdout, b"")

    def test_shell_and_patch_are_actual_declared_executors(self):
        code = ("import os,subprocess; "
                "open('result','w').write('before\\n'); "
                "subprocess.run(['/usr/bin/patch','result'], input="
                "b'--- result\\n+++ result\\n@@ -1 +1 @@\\n-before\\n+after\\n', "
                "check=True,stdout=subprocess.DEVNULL); os.rename('result',os.environ['FIAT_OUTPUT_DIR']+'/result')")
        capture = self.run_code(code, outputs=["result"])
        self.assert_captured(capture)
        self.assertEqual((Path(capture.record["snapshot"])/"result").read_text(), "after\n")

    def test_clean_environment_and_closed_inherited_descriptor(self):
        with (self.root/"inherited").open("wb") as handle:
            os.set_inheritable(handle.fileno(), True)
            code = ("import os\nassert 'PRIVATE_WORKER_TEST_TOKEN' not in os.environ\n"
                    f"try: os.write({handle.fileno()},b'leak')\n"
                    "except OSError: print('closed')\nelse: raise SystemExit(9)\n")
            with mock.patch.dict(os.environ, {"PRIVATE_WORKER_TEST_TOKEN": "secret"}):
                capture = self.run_code(code)
        self.assert_captured(capture)
        self.assertEqual(capture.stdout, b"closed\n")
        self.assertEqual((self.root/"inherited").read_bytes(), b"")

    def test_live_metadata_aliases_and_outside_content_are_denied(self):
        metadata = self.root/".hexaemeron"
        git = self.root/"shared-git"
        metadata.mkdir(); git.mkdir()
        sentinels = [metadata/"state.json", git/"config"]
        for path in sentinels:
            path.write_bytes(b"preserve")
        code = "import os\ndenied=0\n"
        for index, path in enumerate(sentinels):
            for expression in (f"open({str(path)!r},'rb').read()",
                               f"open({str(path)!r},'wb').write(b'bad')",
                               f"os.link({str(path)!r},'alias{index}')"):
                code += f"try: {expression}\nexcept PermissionError: denied+=1\nelse: raise SystemExit(8)\n"
            code += (f"os.symlink({str(path)!r},'symlink{index}')\n"
                     f"try: open('symlink{index}','rb').read()\n"
                     "except PermissionError: denied+=1\nelse: raise SystemExit(9)\n")
        code += "assert denied==8\nprint('denied')\n"
        capture = self.run_code(code)
        self.assert_captured(capture)
        self.assertEqual(capture.stdout, b"denied\n")
        for path in sentinels:
            self.assertEqual(path.read_bytes(), b"preserve")
            self.assertEqual(path.stat().st_nlink, 1)

    def test_other_process_environment_is_denied_by_sysctl(self):
        marker = b"warden-harmless-procargs-sentinel"
        child = subprocess.Popen(
            [PYTHON, "-I", "-c", "import select,sys; "
             "select.select([sys.stdin],[],[],15); print('stopped',flush=True)"],
            env={"WARDEN_TEST_VALUE": marker.decode()}, close_fds=True,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            self.assertIsNone(child.poll())
            for variant in (38, 49):  # KERN_PROCARGS and KERN_PROCARGS2
                with self.subTest(variant=variant):
                    mib = (ctypes.c_int * 3)(1, variant, child.pid)
                    buffer = ctypes.create_string_buffer(1024 * 1024)
                    size = ctypes.c_size_t(len(buffer))
                    libc = ctypes.CDLL(None, use_errno=True)
                    self.assertEqual(libc.sysctl(mib, 3, buffer, ctypes.byref(size), None, 0), 0)
                    self.assertIn(marker, buffer.raw[:size.value])
                    code = ("import ctypes,json,os\n"
                            "assert len(os.uname()) == 5\n"
                            "libc=ctypes.CDLL(None,use_errno=True)\n"
                            f"mib=(ctypes.c_int*3)(1,{variant},{child.pid})\n"
                            "buffer=ctypes.create_string_buffer(1024*1024)\n"
                            "size=ctypes.c_size_t(len(buffer))\n"
                            "result=libc.sysctl(mib,3,buffer,ctypes.byref(size),None,0)\n"
                            "print(json.dumps({'result':result,'errno':ctypes.get_errno(),"
                            f"'sentinel_found':{marker!r} in buffer.raw[:size.value]}}))\n")
                    capture = self.run_code(code)
                    self.assert_captured(capture)
                    observed = json.loads(capture.stdout)
                    self.assertEqual(observed["result"], -1, observed)
                    self.assertIn(observed["errno"], (errno.EPERM, errno.EACCES), observed)
                    self.assertFalse(observed["sentinel_found"], observed)
        finally:
            stdout, stderr = child.communicate(b"stop", timeout=5)
            self.assertEqual(child.returncode, 0, stderr)
            self.assertEqual(stdout, b"stopped\n")

    def test_network_unix_ipc_and_undeclared_deputy_are_denied(self):
        code = ("import socket,subprocess,os\n"
                "for family,address in [(socket.AF_INET,('127.0.0.1',9)),"
                "(socket.AF_UNIX,'socket')]:\n"
                " try:\n  s=socket.socket(family); s.bind(address)\n"
                " except PermissionError: pass\n else: raise SystemExit(8)\n"
                "try: subprocess.run(['/usr/bin/sandbox-exec','-p','(version 1)(allow default)','/bin/sh','-c','true'],check=True)\n"
                "except PermissionError: pass\nelse: raise SystemExit(9)\n")
        self.assert_captured(self.run_code(code))

    def test_unsafe_output_kinds_and_undeclared_files_refuse(self):
        specimens = {
            "symlink": "os.symlink('/dev/null',p)",
            "fifo": "os.mkfifo(p)",
            "hardlink": "open('source','wb').write(b'x'); os.link('source',p)",
            "undeclared": "open(p+'-other','wb').write(b'x')",
        }
        for name, body in specimens.items():
            with self.subTest(name=name):
                capture = self.run_code("import os; p=os.environ['FIAT_OUTPUT_DIR']+'/x'; "+body,
                                        outputs=["x"])
                self.assert_refused(capture)

    def test_replaced_output_directory_is_not_admitted(self):
        capture = self.run_code("import os; p=os.environ['FIAT_OUTPUT_DIR']; "
                                "os.rename(p,p+'-old'); os.mkdir(p); "
                                "open(p+'/x','wb').write(b'x')", outputs=["x"])
        self.assert_refused(capture, "artifact-directory-drift")

    def test_changed_file_during_capture_is_not_admitted(self):
        original = worker._snapshot
        def changed(output_fd, private, inventory, remaining, deadline):
            fd=os.open("x",os.O_WRONLY,dir_fd=output_fd)
            os.write(fd,b"changed"); os.close(fd)
            return original(output_fd, private, inventory, remaining, deadline)
        with mock.patch.object(worker, "_snapshot", side_effect=changed):
            capture=self.run_code("import os; open(os.environ['FIAT_OUTPUT_DIR']+'/x','wb').write(b'x')",outputs=["x"])
        self.assert_refused(capture,"artifact-drift")

    def test_many_outputs_and_shared_stream_artifact_cap(self):
        for body, outputs in [("[open(p+str(i),'wb').write(b'xx') for i in range(32)]", [str(i) for i in range(32)]),
                              ("open(p+'x','wb').write(b'xxxx'); os.write(1,b'xxx'); os.write(2,b'xxxx')", ["x"])]:
            with self.subTest(body=body):
                self.assert_refused(self.run_code("import os; p=os.environ['FIAT_OUTPUT_DIR']+'/'; "+body,
                                                  outputs=outputs,output_cap_bytes=10),"output-cap")

    def test_missing_output_refuses_and_invalid_inventory_never_launches(self):
        self.assert_refused(self.run_code("pass",outputs=["missing"]),"missing-artifact")
        for outputs in ([[]],["../x"],["x","x"],[str(i) for i in range(33)]):
            with self.subTest(outputs=outputs),self.assertRaises(worker.Refusal):
                self.run_code("pass",outputs=outputs)

    def test_detached_descendant_cannot_change_private_capture(self):
        # Cooperative stop/ack needs no authority over a released numeric PID.
        child = ("import os,time,pathlib\nos.setsid()\nos.close(1); os.close(2)\n"
                 "pathlib.Path('ready').write_text('yes')\ntime.sleep(.8)\n"
                 "pathlib.Path(os.environ['FIAT_OUTPUT_DIR']+'/x').write_bytes(b'later')\n"
                 "until=time.monotonic()+5\n"
                 "while time.monotonic()<until and not pathlib.Path('stop').exists(): time.sleep(.02)\n"
                 "pathlib.Path('stopped').write_text('ack')\n")
        code = ("import os,subprocess,time; open(os.environ['FIAT_OUTPUT_DIR']+'/x','wb').write(b'first'); "
                f"subprocess.Popen([{PYTHON!r},'-I','-c',{child!r}])\n"
                "while not os.path.exists('ready'): time.sleep(.01)\n")
        capture=self.run_code(code,outputs=["x"])
        scratch=Path(capture.record['scratch_root'])
        try:
            self.assert_captured(capture)
            time.sleep(1)
            self.assertEqual((scratch/'output/x').read_bytes(),b'later')
            self.assertEqual((Path(capture.record['snapshot'])/'x').read_bytes(),b'first')
            self.assertIn(capture.record['cleanup'],('unverified-retired','signal-denied-retired'))
        finally:
            (scratch/'stop').write_text('stop')
            until=time.monotonic()+2
            while time.monotonic()<until and not (scratch/'stopped').exists():
                time.sleep(.02)
            self.assertTrue((scratch/'stopped').exists())


if __name__ == "__main__":
    unittest.main()
