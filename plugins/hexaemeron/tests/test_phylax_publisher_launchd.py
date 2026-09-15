"""Guard daemon limits without changing host or process resource limits."""
import importlib.util
from pathlib import Path
import plistlib
import resource
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/phylax/scripts"))
KIT = Path(__file__).resolve().parents[1] / "skills/phylax/deployment/macos"


class LaunchdLimitTests(unittest.TestCase):
    def test_system_daemon_never_sets_host_wide_file_or_process_limits(self):
        document = plistlib.loads((KIT / "finance.wildcat.issue-publisher.plist").read_bytes())
        for kind in ("SoftResourceLimits", "HardResourceLimits"):
            self.assertNotIn("NumberOfFiles", document[kind])
            self.assertNotIn("NumberOfProcesses", document[kind])

    def test_service_sets_local_limits_before_constructing_runtime(self):
        spec = importlib.util.spec_from_file_location("publisher_service_limits", KIT / "publisher-service.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        events = []
        def limited(which, values):
            events.append((which, values))
        def runtime(**kwargs):
            events.append("runtime")
            return object()
        with mock.patch.object(module.sys, "argv", [str(KIT / "publisher-service.py")]), \
             mock.patch.object(module.pwd, "getpwnam", return_value=SimpleNamespace(pw_uid=499)), \
             mock.patch.object(module.os, "geteuid", return_value=499), \
             mock.patch.object(module.socket, "socket"), \
             mock.patch.object(module, "OpenSSLSigner"), \
             mock.patch.object(module, "PinnedGitHubTransport"), \
             mock.patch.object(module, "PublisherServer"), \
             mock.patch.object(module, "PublisherRuntime", side_effect=runtime), \
             mock.patch.object(resource, "setrlimit", side_effect=limited):
            self.assertEqual(0, module.main())
        self.assertEqual([(resource.RLIMIT_NOFILE, (64, 64)),
                          (resource.RLIMIT_NPROC, (8, 8)), "runtime"], events)

    def test_reference_tracks_complete_manifest_and_criteria(self):
        reference = (KIT.parents[1] / "references/github-issue-publisher-v1.md").read_text()
        self.assertIn("lists the nine component fixtures", reference)
        self.assertIn("one of the five component criteria", reference)

    def test_kit_conformance_rejects_noncanonical_plist_bytes(self):
        from github_issue_publisher_lib import conformance
        from github_issue_publisher_lib.deployment import daemon_document
        from github_issue_publisher_lib.errors import PublisherError
        original = conformance.read_bounded_file
        document = daemon_document()
        document["inetdCompatibility"]["Wait"] = 0
        integer_zero = plistlib.dumps(document)
        canonical = plistlib.dumps(daemon_document())
        duplicate_key = canonical.replace(b"<key>Wait</key>", b"<key>Wait</key><true/><key>Wait</key>")
        for raw in (integer_zero, duplicate_key, canonical + b"\n"):
            with self.subTest(raw=raw):
                def read(path):
                    return raw if Path(path).suffix == ".plist" else original(path)
                with mock.patch.object(conformance, "read_bounded_file", side_effect=read):
                    with self.assertRaises(PublisherError):
                        conformance.verify_public_surfaces()
