"""Offline hostile specimens and deployment predicate mutation guards."""
from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import http.client
import json
import os
from pathlib import Path
import plistlib
import stat
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/phylax/scripts"
sys.path.insert(0, str(SCRIPTS))
from github_issue_publisher_lib import conformance as proof
from github_issue_publisher_lib import deployment as deploy
from github_issue_publisher_lib.canonical import canonical_json
from github_issue_publisher_lib.errors import PublisherError
from github_issue_publisher_lib.signer import OPENSSL_ARGUMENTS, PEM_PATH

FIXTURES = Path(__file__).parent / "fixtures/github-issue-publisher-v1"


class OfflineOnlyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        real_popen, real_open = subprocess.Popen, os.open
        def popen(*args, **kwargs):
            command = kwargs.get("args", args[0] if args else ())
            if isinstance(command, (list, tuple)) and (tuple(command) == OPENSSL_ARGUMENTS or PEM_PATH in command):
                raise AssertionError("production signer prohibited in offline tests")
            return real_popen(*args, **kwargs)
        def opening(path, *args, **kwargs):
            if str(path) in (PEM_PATH, deploy.KEY_PATH):
                raise AssertionError("credential read prohibited in offline tests")
            return real_open(path, *args, **kwargs)
        cls.guards = [mock.patch.object(subprocess, "Popen", side_effect=popen),
                      mock.patch.object(os, "open", side_effect=opening),
                      mock.patch.object(http.client, "HTTPSConnection", side_effect=AssertionError("network prohibited"))]
        for guard in cls.guards:
            guard.start()
            cls.addClassCleanup(guard.stop)

    def fixtures(self):
        files = proof._closed_manifest((FIXTURES / "manifest.json").read_bytes())
        return proof._fixture_bytes(FIXTURES, files)

    def probe(self):
        return proof.FixtureProbe(json.loads((FIXTURES / "deployment.json").read_bytes()))

    def check(self, probe):
        return deploy.check_deployment(caller="fixturecaller", release_sha256=probe.release,
                                       probe=probe, inventory=probe.inventory)

    def test_offline_guard_blocks_production_signer_and_key_open(self):
        with self.assertRaises(AssertionError):
            subprocess.Popen(OPENSSL_ARGUMENTS)
        with self.assertRaises(AssertionError):
            os.open(deploy.KEY_PATH, os.O_RDONLY)

    def test_positive_manifest_executes_every_study_risk(self):
        result = proof.verify_hostile(self.fixtures())
        self.assertEqual(32, result["case_count"])
        self.assertEqual(31, result["hostile_count"])
        self.assertEqual(0, result["unexpected_outcomes"])
        self.assertEqual(0, result["issue_855_signer_attempts"])
        self.assertEqual(0, result["issue_855_post_attempts"])
        self.assertEqual("not-established", result["live_isolation"])
        self.assertEqual(list(proof.CASE_IDS), [r["id"] for r in result["cases"]])
        study = Path(__file__).resolve().parents[3] / "docs/phylax-github-issue-publisher/study.md"
        self.assertTrue(study.exists())
        source = study.read_text().split("```risk-register\n")[1].split("```", 1)[0]
        self.assertEqual(tuple(line.split(" | ")[0] for line in source.splitlines()), proof.RISK_IDS)

    def test_missing_changed_unknown_duplicate_reordered_manifest_rows_refuse(self):
        fixtures = self.fixtures()
        original = json.loads(fixtures["hostile-cases.json"])
        variants = []
        for action in ("missing", "unknown", "duplicate", "reordered", "expected"):
            doc = deepcopy(original)
            if action == "missing": doc["cases"].pop()
            if action == "unknown": doc["cases"][1]["id"] = "unknown"
            if action == "duplicate": doc["cases"][1] = doc["cases"][0]
            if action == "reordered": doc["cases"].reverse()
            if action == "expected": doc["cases"][1]["expected"] = "pass"
            variants.append(doc)
        for doc in variants:
            with self.subTest(doc=doc), self.assertRaises(PublisherError):
                proof.verify_hostile({**fixtures, "hostile-cases.json": canonical_json(doc) + b"\n"})

    def test_exact_855_executes_no_signer_or_post(self):
        fixtures = self.fixtures()
        original = json.loads(fixtures["valid-request.json"])
        raw = canonical_json(proof._rejection_request(original, "issue-855-missing-framework-opening", fixtures))
        self.assertEqual({"outcome": "refused", "signer_attempts": 0, "post_attempts": 0, "code": "GIP130"}, proof._runtime_case(fixtures, raw))

    def test_deployment_positive_is_metadata_only_and_not_live_isolation(self):
        probe = self.probe()
        before = deepcopy(probe.status)
        result = self.check(probe)
        self.assertEqual("passed", result["outcome"])
        self.assertTrue(all(result["predicates"].values()))
        self.assertEqual("not-established", result["live_isolation"])
        self.assertEqual(before, probe.status)
        self.assertEqual([deploy.DAEMON_PATH], probe.reads)

    def test_every_deployment_predicate_has_a_refusal_mutation(self):
        def release(p): p.inventory_value["publisher-service.py"] = "f" * 64
        mutations = {
            "platform": lambda p: setattr(p, "platform", "linux"),
            "verifier-identity": lambda p: setattr(p, "verifier_uid", lambda: 502),
            "service-identity": lambda p: setattr(p.service, "pw_shell", "/bin/zsh"),
            "caller-identity": lambda p: p.admin.gr_mem.append("fixturecaller"),
            "distinct-identity": lambda p: setattr(p.caller, "pw_uid", p.service.pw_uid),
            "group": lambda p: p.members.gr_mem.clear(),
            "parents": lambda p: setattr(p.status["/Library"], "st_mode", stat.S_IFDIR | 0o777),
            "key": lambda p: setattr(p.status[deploy.KEY_PATH], "st_mode", stat.S_IFREG | 0o644),
            "socket": lambda p: setattr(p.status[deploy.SOCKET_PATH], "st_mode", stat.S_IFREG | 0o660),
            "daemon": lambda p: setattr(p, "daemon", b"garbage"),
            "program": lambda p: setattr(p.status[deploy.PROGRAM_PATH], "st_uid", 502),
            "working": lambda p: setattr(p.status[deploy.WORKING_PATH], "st_mode", stat.S_IFDIR | 0o777),
            "interpreter": lambda p: setattr(p.status[deploy.PYTHON_PATH], "st_mode", stat.S_IFREG | 0o777),
            "helpers": lambda p: p.status.update({"/Users/fixturecaller/.config/gh-app/file_as_app.sh": p.status[deploy.PROGRAM_PATH]}),
            "legacy-key": lambda p: p.status.update({"/Users/fixturecaller/.config/gh-app/shoggoth-wildcat-labs.pem": p.status[deploy.KEY_PATH]}),
            "release": release,
        }
        self.assertEqual(set(deploy.PREDICATES), set(mutations))
        for predicate, mutation in mutations.items():
            with self.subTest(predicate=predicate):
                probe = self.probe()
                mutation(probe)
                result = self.check(probe)
                self.assertEqual("refused", result["outcome"])
                self.assertFalse(result["predicates"][predicate])

    def test_key_program_daemon_socket_owner_group_mode_acl_and_link_mutations(self):
        for path in (deploy.KEY_PATH, deploy.PROGRAM_PATH, deploy.DAEMON_PATH, deploy.SOCKET_PATH):
            for field, value in (("st_uid", 502), ("st_gid", 777), ("st_mode", stat.S_IFLNK | 0o777), ("st_nlink", 2)):
                with self.subTest(path=path, field=field):
                    probe = self.probe()
                    setattr(probe.status[path], field, value)
                    self.assertEqual("refused", self.check(probe)["outcome"])
            probe = self.probe()
            probe.acl.add(path)
            self.assertEqual("refused", self.check(probe)["outcome"])

    def test_deployment_missing_identity_or_path_refuses(self):
        probe = self.probe()
        probe.user = lambda name: (_ for _ in ()).throw(KeyError())
        self.assertEqual("refused", self.check(probe)["outcome"])
        for path in self.probe().status:
            probe = self.probe()
            del probe.status[path]
            self.assertEqual("refused", self.check(probe)["outcome"])

    def test_deployment_snapshot_does_not_expose_paths_or_caller(self):
        result = canonical_json(self.check(self.probe()))
        for needle in (b"fixturecaller", b"/Library", b".pem", b"shoggoth-wildcat-labs"):
            self.assertNotIn(needle, result)

    def test_daemon_has_exact_inetd_names_numeric_socket_owners_and_limits(self):
        doc = deploy.daemon_document()
        self.assertEqual({"Wait": False}, doc["inetdCompatibility"])
        self.assertEqual(499, doc["Sockets"]["Listener"]["SockPathOwner"])
        self.assertEqual(499, doc["Sockets"]["Listener"]["SockPathGroup"])
        self.assertEqual(doc["SoftResourceLimits"], doc["HardResourceLimits"])
        for name in doc:
            probe = self.probe()
            changed = dict(doc)
            del changed[name]
            probe.daemon = plistlib.dumps(changed)
            self.assertFalse(self.check(probe)["predicates"]["daemon"])

    def test_public_surfaces_have_no_alternative_capability(self):
        proof.verify_public_surfaces()
        for option in ("mint", "token", "post", "--url", "--header", "--pem", "source", "install", "bootout"):
            import github_issue_publisher as cli
            with mock.patch.object(cli.sys, "stderr", SimpleNamespace(buffer=__import__('io').BytesIO())):
                self.assertEqual(2, cli.main([option]))

    def test_digest_mutation_is_a_subject_mismatch(self):
        probe = self.probe()
        probe.release = "0" * 64
        self.assertFalse(self.check(probe)["predicates"]["release"])

    def test_refusal_recovers_when_exact_predicate_is_restored(self):
        probe = self.probe()
        probe.acl.add(deploy.KEY_PATH)
        self.assertEqual("refused", self.check(probe)["outcome"])
        probe.acl.clear()
        self.assertEqual("passed", self.check(probe)["outcome"])

    def test_publisher_promise_keeps_publication_and_component_distinct(self):
        skill = (SCRIPTS.parent / "SKILL.md").read_text()
        self.assertIn("### phylax-github-issue-publisher", skill)
        contract = skill.split("### phylax-github-issue-publisher", 1)[1]
        self.assertIn("- Consequence: 3", contract)
        self.assertIn("live deployment", contract)
        self.assertIn("administrators", contract)
        self.assertIn("judgement", contract)

    def test_public_reader_refuses_symlink_hardlink_directory_and_oversize(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            good = root / "good"
            good.write_bytes(b"reviewed")
            self.assertEqual(b"reviewed", deploy._public_read(good))
            alias = root / "alias"
            alias.symlink_to(good)
            with self.assertRaises((OSError, PublisherError)):
                deploy._public_read(alias)
            folder = root / "folder"
            folder.mkdir()
            nested = folder / "nested"
            nested.write_bytes(b"reviewed")
            linked = root / "linked"
            linked.symlink_to(folder)
            with self.assertRaises((OSError, PublisherError)):
                deploy._public_read(linked / "nested")
            hard = root / "hard"
            os.link(good, hard)
            with self.assertRaises(PublisherError):
                deploy._public_read(hard)
            with self.assertRaises(PublisherError):
                deploy._public_read(folder)
            huge = root / "huge"
            huge.write_bytes(b"x" * (deploy.MAX_DEPLOYMENT_BYTES + 1))
            with self.assertRaises(PublisherError):
                deploy._public_read(huge)

    def test_release_inventory_binds_program_and_lexicon_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            for name in ("publisher-service.py", "publisher-client.py", "python3",
                         "plugins/hexaemeron/skills/imprimatur/SKILL.md"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"reviewed")
            for name in ("plugins/hexaemeron/skills/phylax/scripts/github_issue_publisher_lib",
                         "plugins/hexaemeron/skills/imprimatur/scripts",
                         "plugins/hexaemeron/skills/imprimatur/lexicon"):
                path = root / name
                path.mkdir(parents=True, exist_ok=True)
                for i in range(2):
                    (path / (str(i)+".py")).write_bytes(b"reviewed")
            before = deploy.release_inventory(root)
            (root / "publisher-service.py").write_bytes(b"changed")
            after = deploy.release_inventory(root)
            self.assertNotEqual(before["publisher-service.py"], after["publisher-service.py"])
            self.assertEqual(10, len(before))
            extra = root / "plugins/hexaemeron/skills/imprimatur/lexicon/cache"
            extra.mkdir()
            with self.assertRaises(PublisherError):
                deploy.release_inventory(root)

    def test_app_is_not_a_host_login(self):
        source = SCRIPTS.parents[2] / "skills/fiat/scripts/hexctl.py"
        tree = ast.parse(source.read_bytes())
        node = next(n for n in tree.body if isinstance(n, ast.Assign)
                    and any(isinstance(t, ast.Name) and t.id == "HOST_PR_LOGINS" for t in n.targets))
        self.assertIsInstance(node.value, ast.Call)
        values = ast.literal_eval(node.value.args[0])
        self.assertNotIn("shoggoth-wildcat-labs[bot]", values)

    def test_public_design_criterion_emits_true_only_after_full_conformance(self):
        with mock.patch.object(proof, "_write_report") as writer, mock.patch.object(proof.sys, "stdout", SimpleNamespace(buffer=__import__('io').BytesIO())):
            criterion = "public-route-and-deployment-check"
            args = ["conformance", "--manifest", proof.MANIFEST_PATH, "--design-candidate",
                    "isolated-publisher", "--design-criterion", criterion,
                    "--design-report", proof._report_path("isolated-publisher", criterion)]
            self.assertEqual(0, proof.run_command(args))
            report = json.loads(writer.call_args.args[1])
            self.assertIs(True, report["value"])
            self.assertEqual("protasis-design-report/v1", report["schema"])
            self.assertEqual(0, report["exit"])

    def test_daemon_wrong_plist_types_and_duplicate_keys_cannot_compare_equal(self):
        probe = self.probe()
        document = deploy.daemon_document()
        document["inetdCompatibility"]["Wait"] = 0
        probe.daemon = plistlib.dumps(document)
        self.assertFalse(self.check(probe)["predicates"]["daemon"])
        probe = self.probe()
        probe.daemon = probe.daemon.replace(b"<dict>", b"<dict><key>Label</key><string>wrong</string>", 1)
        self.assertFalse(self.check(probe)["predicates"]["daemon"])

    def test_deployment_snapshot_binds_caller_and_reviewed_release(self):
        probe = self.probe()
        result = self.check(probe)
        expected = hashlib.sha256(canonical_json({"caller": "fixturecaller", "release_sha256": probe.release})).hexdigest()
        self.assertEqual(expected, result["subject_sha256"])
        probe.release = "2" * 64
        self.assertNotEqual(expected, self.check(probe)["subject_sha256"])
