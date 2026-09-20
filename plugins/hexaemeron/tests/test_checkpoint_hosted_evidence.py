"""Hostile hosted specimens stay inert; only authenticated readback can admit."""
import copy
import hashlib
import io
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

import checkpoint_hosted_evidence as hosted
from checkpoint_authority import network, network_policy, release
import test_checkpoint_authority_release_conformance as fixtures


class HostedEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.ReleaseConformanceTests("test_valid")
        self.fixture.setUp(); self.addCleanup(self.fixture.doCleanups)
        self.root = hosted.ROOT

    def sample(self, profile="ubuntu-24.04"):
        system, machine, runner_os, runner_arch, asset = hosted.PROFILES[profile]
        policy = network_policy.for_host(system, machine)
        tools = [{"name": name, "path": policy.launcher if name == "sandbox" else "/fixture/" + name,
                  "sha256": "a" * 64} for name in hosted.TOOL_NAMES]
        tool_profile = json.loads((self.root / release.CORPUS / "tool-profile.json").read_bytes())
        tools[1]["sha256"] = tool_profile["cosign"]["assets"][asset]["sha256"]
        expected = network.Boundary("a" * 64, policy).expected()
        value = self.fixture.value()
        value["demonstration"]["network_boundary"] = expected
        value["workload"]["environment"]["machine"] = machine
        value["demonstration"]["manifest_sha256"] = hosted.native._hash(self.root, release.MANIFEST)
        log = b"synthetic parser fixture; no hosted execution\n"
        value["output_sha256"] = hashlib.sha256(log).hexdigest()
        files = {"direct.stdout": network.PROBE_OUTPUT, "direct.stderr": b"",
                 "descendant.stdout": network.PROBE_OUTPUT, "descendant.stderr": b"",
                 "release.stdout": hosted.encode(value), "release.stderr": b"", "tests.log": log}
        host = {"schema": "checkpoint-hosted-execution/v1", "profile": profile,
                "repository": hosted.REPOSITORY, "run_id": 100, "run_attempt": 2,
                "checkout_sha": "1" * 40, "event": "pull_request", "event_sha": "2" * 40,
                "event_head_sha": "1" * 40, "event_merge_sha": "2" * 40,
                "runner": {"os": runner_os, "arch": runner_arch, "name": "GitHub Actions 1"},
                "runtime": {"platform": system, "machine": machine,
                            "os_version": "24.04" if system == "linux" else "15.7", "python": value["python"]},
                "started_at": "2026-09-20T12:00:00Z", "completed_at": "2026-09-20T12:01:00Z",
                "source": hosted.inventory(self.root), "tools": tools, "policy": hosted.policy_descriptor(policy),
                "network": expected, "release_exit": 0, "files": self.rows(files)}
        files["host.json"] = hosted.encode(host)
        return files

    @staticmethod
    def rows(files):
        return [{"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                for name, data in sorted(files.items()) if name != "host.json"]

    def modify(self, files, change):
        value = json.loads(files["host.json"]); change(value)
        files["host.json"] = hosted.encode(value)
        return files

    def execution(self, files, change):
        value = json.loads(files["release.stdout"]); change(value)
        files["release.stdout"] = hosted.encode(value)
        return self.modify(files, lambda host: host.update(files=self.rows(files)))

    @staticmethod
    def archive(files, extra=None):
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zipped:
            for name, value in files.items(): zipped.writestr(name, value)
            if extra: zipped.writestr(*extra)
        return output.getvalue()

    def metadata(self, files, profile="ubuntu-24.04"):
        host = json.loads(files["host.json"])
        request = {"schema": "checkpoint-hosted-request/v1", "run_id": 100, "run_attempt": 2,
                   "artifact_id": 300, "checkout_sha": "1" * 40}
        run = {"id": 100, "run_attempt": 2, "head_sha": "1" * 40, "path": hosted.WORKFLOW,
               "event": "pull_request", "status": "completed", "conclusion": "success",
               "repository": {"id": hosted.REPOSITORY_ID, "full_name": hosted.REPOSITORY}}
        job = {"id": 200, "run_id": 100, "run_attempt": 2, "head_sha": "1" * 40,
               "name": "checkpoint (" + profile + ")", "status": "completed", "conclusion": "success",
               "labels": [profile], "runner_name": "GitHub Actions 1", "runner_group_name": "GitHub Actions",
               "runner_group_id": 0, "started_at": "2026-09-20T11:59:00Z", "completed_at": "2026-09-20T12:02:00Z",
               "steps": [{"name": "Run checkpoint conformance", "status": "completed", "conclusion": "success"}]}
        archive = self.archive(files)
        artifact = {"id": 300, "name": hosted.artifact_name(profile, 100, 2), "expired": False,
                    "digest": "sha256:" + hashlib.sha256(archive).hexdigest(), "size_in_bytes": len(archive),
                    "workflow_run": {"id": 100, "repository_id": hosted.REPOSITORY_ID,
                                     "head_repository_id": hosted.REPOSITORY_ID, "head_sha": "1" * 40},
                    "created_at": "2026-09-20T12:01:30Z"}
        return host, request, run, {"total_count": 1, "jobs": [job]}, artifact, hashlib.sha256(archive).hexdigest()

    def test_foreign_host_parser_does_not_prepare_or_execute_a_sandbox(self):
        for profile in hosted.PROFILES:
            files = self.sample(profile)
            with self.subTest(profile=profile), patch.object(network, "prepare", side_effect=AssertionError("not execution")):
                parsed = hosted.archive_members(self.archive(files))
                host, report = hosted.validate_files(self.root, profile, parsed)
                self.assertEqual(host["profile"], profile)
                self.assertEqual(report["tests_run"], len(hosted.native.inputs(self.root)["cases"]))
                self.assertNotIn("admission", host)

    def test_positive_accounting_is_required(self):
        mutations = (lambda v: v.update(tests_run=v["tests_run"] + 1), lambda v: v.update(tests_run=True),
                     lambda v: v.update(complete=False), lambda v: v.update(passed=False),
                     lambda v: v.update(workload=None), lambda v: v.update(demonstration=None),
                     lambda v: v.update(completed=v["completed"][:-1]),
                     lambda v: v.update(started=v["started"][1:]), lambda v: v.update(skips=1),
                     lambda v: v.update(expected_failures=1), lambda v: v.update(unexpected_successes=1),
                     lambda v: v["demonstration"].update(interoperability_cases=4),
                     lambda v: v["demonstration"]["network_boundary"].pop("descendant_probe_exit"),
                     lambda v: v["workload"]["environment"].update(machine="arm64"))
        original = self.sample()
        for change in mutations:
            with self.subTest(change=change), self.assertRaises((hosted.owner.Refusal, hosted.NativeRefusal)):
                hosted.validate_files(self.root, "ubuntu-24.04", self.execution(copy.deepcopy(original), change))

    def test_policy_argv_abi_tool_source_and_field_mutations_refuse(self):
        changes = (lambda h: h["policy"].update(argv=[]), lambda h: h["policy"].update(abi="arm64"),
                   lambda h: h["policy"].update(filter_sha256="0" * 64),
                   lambda h: h["network"].update(mechanism="allow-all"),
                   lambda h: h["network"].pop("descendant_probe_sha256"),
                   lambda h: h["network"].update(probe_operations=3),
                   lambda h: h["network"].update(probe_exit=False),
                   lambda h: h["source"]["files"][0].update(sha256="0" * 64),
                   lambda h: h["tools"][1].update(sha256="0" * 64),
                   lambda h: h["tools"].pop(), lambda h: h.update(extra=True),
                   lambda h: h.update(release_exit=False), lambda h: h.update(run_attempt=True),
                   lambda h: h["runtime"].update(machine="arm64"),
                   lambda h: h["runtime"].update(os_version="22.04"),
                   lambda h: h["runner"].update(arch="ARM64"), lambda h: h.update(profile="macos-15"),
                   lambda h: h.update(event_head_sha="3" * 40))
        original = self.sample()
        for change in changes:
            with self.subTest(change=change), self.assertRaises((hosted.owner.Refusal, hosted.NativeRefusal)):
                hosted.validate_files(self.root, "ubuntu-24.04", self.modify(copy.deepcopy(original), change))

    def test_raw_bytes_and_denial_cannot_be_replaced_by_success_labels(self):
        original = self.sample()
        for field, raw in (("descendant.stdout", b""), ("direct.stdout", b"success"),
                           ("direct.stderr", b"diagnostic"), ("release.stderr", b"failed"),
                           ("tests.log", b"a different execution")):
            files = copy.deepcopy(original); files[field] = raw
            self.modify(files, lambda h: h.update(files=self.rows(files)))
            with self.subTest(field=field), self.assertRaises(hosted.owner.Refusal):
                hosted.validate_files(self.root, "ubuntu-24.04", files)
        files = copy.deepcopy(original); files.pop("descendant.stdout")
        with self.assertRaises(hosted.owner.Refusal): hosted.validate_files(self.root, "ubuntu-24.04", files)

    def test_archive_limits_members_links_and_duplicate_json_refuse(self):
        original = self.sample()
        for bad in (b"not a zip", b"x" * (hosted.ZIP_MAX + 1),
                    self.archive(original, ("../escape", b"bad")),
                    self.archive({key: value for key, value in original.items() if key != "tests.log"}),
                    self.archive({**original, "tests.log": b"x" * (hosted.HOST_MAX + 1)})):
            with self.subTest(size=len(bad)), self.assertRaises(hosted.owner.Refusal): hosted.archive_members(bad)
        for malformed in (b'{"x":1,"x":2}', b'{"x":NaN}', b'[' * 20 + b'0' + b']' * 20,
                          b'\xff', b'{} trailing', b'{}' + b' ' * hosted.HOST_MAX):
            with self.subTest(malformed=malformed[:20]), self.assertRaises(hosted.owner.Refusal): hosted.decode(malformed)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as zipped:
            for name, data in original.items():
                info = zipfile.ZipInfo(name); info.create_system = 3
                info.external_attr = ((stat.S_IFLNK if name == "tests.log" else stat.S_IFREG) | 0o600) << 16
                zipped.writestr(info, data)
        with self.assertRaises(hosted.owner.Refusal): hosted.archive_members(output.getvalue())

    def test_metadata_checks_actual_attempt_job_artifact_and_checkout(self):
        host, request, run, jobs, artifact, sha = self.metadata(self.sample())
        joined = hosted.validate_metadata(host, "ubuntu-24.04", request, run, jobs, artifact, sha)
        self.assertEqual(joined["job_id"], 200)
        self.assertIn("do not directly attest", joined["association_boundary"])
        changes = (
            lambda r,j,a: r.update(conclusion="failure"), lambda r,j,a: r.update(status="in_progress"),
            lambda r,j,a: r.update(run_attempt=1), lambda r,j,a: r.update(head_sha="2" * 40),
            lambda r,j,a: r.update(path="other.yml"), lambda r,j,a: r["repository"].update(id=1),
            lambda r,j,a: j["jobs"][0].update(conclusion="failure"),
            lambda r,j,a: j["jobs"][0].update(conclusion="skipped"),
            lambda r,j,a: j["jobs"][0].update(run_attempt=1),
            lambda r,j,a: j["jobs"][0].update(labels=["macos-15"]),
            lambda r,j,a: j["jobs"][0].update(runner_name="another runner"),
            lambda r,j,a: j["jobs"][0]["steps"][0].update(conclusion="skipped"),
            lambda r,j,a: j.update(jobs=[]), lambda r,j,a: j.update(total_count=101),
            lambda r,j,a: a.update(expired=True), lambda r,j,a: a.update(id=301),
            lambda r,j,a: a.update(name=hosted.artifact_name("ubuntu-24.04", 100, 1)),
            lambda r,j,a: a.update(digest="sha256:" + "0" * 64),
            lambda r,j,a: a["workflow_run"].update(head_sha="2" * 40),
            lambda r,j,a: a.update(created_at="2026-09-20T11:58:00Z"),
            lambda r,j,a: a.update(created_at="2026-09-20T12:03:00Z"))
        for change in changes:
            r,j,a = copy.deepcopy((run,jobs,artifact)); change(r,j,a)
            with self.subTest(change=change), self.assertRaises(hosted.owner.Refusal):
                hosted.validate_metadata(host, "ubuntu-24.04", request, r,j,a,sha)

    def test_local_captures_cannot_supply_authenticated_admission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); evidence = ".hexaemeron/sources/ci/ubuntu-24.04"
            destination = root / evidence; destination.mkdir(parents=True)
            request = self.metadata(self.sample())[1]
            (destination / "request.json").write_bytes(hosted.encode(request))
            (destination / "admission.json").write_bytes(b'{"passed":true}')
            with patch.object(hosted, "inventory", return_value={}), patch.object(hosted, "checkout", return_value="1" * 40), \
                    patch.object(hosted, "pin"), patch.object(hosted, "command", side_effect=hosted.owner.Refusal("auth-unavailable")) as call:
                with self.assertRaisesRegex(hosted.owner.Refusal, "auth-unavailable"):
                    hosted.admit(root, "ubuntu-24.04", evidence)
                call.assert_called_once()
            self.assertEqual(len(list(destination.glob("observation-*/refusal.json"))), 1)

    def test_injected_readback_retains_exact_bytes_and_rechecks_metadata(self):
        # This transport is an offline specimen; no real Actions claim follows.
        files = self.sample()
        host, request, run, jobs, artifact, _ = self.metadata(files)
        archived = self.archive(files)
        originals = [hosted.encode(run), hosted.encode(jobs), hosted.encode(artifact)]
        validate = hosted.validate_files
        for drift in (False, True):
            with self.subTest(drift=drift), tempfile.TemporaryDirectory() as directory:
                root = Path(directory); evidence = ".hexaemeron/sources/ci/ubuntu-24.04"
                destination = root / evidence; destination.mkdir(parents=True)
                (destination / "request.json").write_bytes(hosted.encode(request))
                reread = originals[:]
                if drift:
                    changed = copy.deepcopy(run); changed["head_sha"] = "3" * 40
                    reread[0] = hosted.encode(changed)
                with patch.object(hosted, "inventory", return_value=host["source"]), \
                        patch.object(hosted, "checkout", return_value=request["checkout_sha"]), \
                        patch.object(hosted, "pin"), \
                        patch.object(hosted, "command", return_value=SimpleNamespace(stdout=b'{"login":"fixture","id":42}')), \
                        patch.object(hosted, "github", side_effect=[*originals, archived, *reread]) as fetch, \
                        patch.object(hosted, "validate_files", side_effect=lambda _, profile, members: validate(self.root, profile, members)):
                    if drift:
                        with self.assertRaises(hosted.owner.Refusal): hosted.admit(root, "ubuntu-24.04", evidence)
                        self.assertEqual(list(destination.glob("observation-*/admission.json")), [])
                        self.assertEqual(len(list(destination.glob("observation-*/refusal.json"))), 1)
                    else:
                        result = hosted.admit(root, "ubuntu-24.04", evidence)
                        self.assertTrue(result["complete"])
                        capture = root / result["capture"]
                        self.assertEqual((capture / "artifact.zip").read_bytes(), archived)
                        self.assertEqual((capture / "run.json").read_bytes(), originals[0])
                        self.assertEqual((capture / "run-after.json").read_bytes(), originals[0])
                    self.assertEqual(fetch.call_count, 7)

    def test_collection_refusal_preserves_profile_without_claiming_execution(self):
        with tempfile.TemporaryDirectory() as directory, patch.dict(hosted.os.environ, {"GITHUB_ACTIONS": "false"}):
            destination = Path(directory) / "evidence"
            with self.assertRaisesRegex(hosted.owner.Refusal, "runtime-host"):
                hosted.collect(self.root, "ubuntu-24.04", destination)
            record = hosted.decode((destination / "failure.json").read_bytes())
            self.assertFalse(record["complete"])
            self.assertEqual(record["profile"], "ubuntu-24.04")
            self.assertIsNone(record["source"])
            self.assertEqual(sorted(p.name for p in destination.iterdir()), ["failure.json"])
            before = (destination / "failure.json").read_bytes()
            with self.assertRaises(FileExistsError): hosted.collect(self.root, "ubuntu-24.04", destination)
            self.assertEqual((destination / "failure.json").read_bytes(), before)

    def test_api_host_and_repository_are_closed(self):
        for path in ("https://attacker.invalid", "repos/other/repo/actions/runs/1", "repos/wildcat-finance/skills/actions/../secrets"):
            with self.subTest(path=path), patch.object(hosted, "command") as child, self.assertRaises(hosted.owner.Refusal):
                hosted.github(path, self.root)
            child.assert_not_called()


if __name__ == "__main__":
    unittest.main()
