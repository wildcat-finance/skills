"""Fixed Euler release bytes, rebuilds and offline tamper checks."""

import hashlib
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from . import support
from tabularium_lib.core import TabulariumError, canonical_json, sha256_bytes
from tabularium_lib.verifier import verify


EXAMPLES = support.PLUGIN_ROOT / "examples"
RELEASES = {
    "euler-v1-v0": {
        "source.json": "1241cbed85189e79f9b0f8418e6838b297b4b661ad3e9f2d8a86903e22a6e790",
        "capture.json": "59cd57ad5d8c54e1fd97cd4e62d37e31ac0d157ee5fa8f396c00be042c25041a",
        "events.jsonl": "4034622f8b34147dead8a87d7c16b2a7c7197ed6417809fec41716a8028552aa",
        "coverage.json": "ba4c5c127449b9be257069d302b442484fbd5d83023798eb9247aa893a45d301",
    },
    "euler-v2-v0": {
        "source.json": "10f5c8e8242ef3745fbd69c4d8aed458f31b165fc4526f638e76df59a69a18cc",
        "capture.json": "bcf2c85907243ccb40bc79234e30457d2e7e8b7dc3addc32d7301f804c772b9e",
        "events.jsonl": "f563baa00c737384a3901f1bb3a7ae977f68f52a813eae9d02071eb2f4d0a5fe",
        "coverage.json": "9892768315484ff05771e998f301b30daebd079a445e4226c9e55b12323c2a4b",
    },
}


class EulerReleaseTests(unittest.TestCase):
    def test_all_eight_release_artifact_hashes_are_fixed(self):
        for release, expected in RELEASES.items():
            for name, digest in expected.items():
                self.assertEqual(hashlib.sha256((EXAMPLES / release / name).read_bytes()).hexdigest(), digest, "%s/%s" % (release, name))

    def test_both_releases_verify_without_network_or_writes(self):
        for release in RELEASES:
            root = EXAMPLES / release
            paths = tuple(root / name for name in RELEASES[release])
            before = {path: path.read_bytes() for path in paths}
            with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
                report = verify(root / "coverage.json")
            self.assertGreater(report.rows, 0)
            self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_both_documented_rebuilds_match_committed_bytes(self):
        for release in RELEASES:
            result = subprocess.run([sys.executable, str(EXAMPLES / release / "rebuild.py")], cwd=support.REPO_ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("rebuild matches", result.stdout)

    def copied_release(self, release):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / release
        shutil.copytree(EXAMPLES / release, root)
        return root

    def test_source_tamper_fails_declared_digest(self):
        root = self.copied_release("euler-v2-v0")
        (root / "source.json").write_bytes((root / "source.json").read_bytes() + b"\n")
        with self.assertRaisesRegex(TabulariumError, "source digest"):
            verify(root / "coverage.json")

    def test_canonical_tamper_fails_offline_rebuild_after_rebinding(self):
        root = self.copied_release("euler-v1-v0")
        events = root / "events.jsonl"
        row = json.loads(events.read_text())
        row["amounts"][0]["base_units"] = "1"
        events.write_bytes(canonical_json(row) + b"\n")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["canonical"]["sha256"] = sha256_bytes(events.read_bytes())
        manifest["canonical"]["bytes"] = len(events.read_bytes())
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "offline source rebuild"):
            verify(manifest_path)

    def test_protocol_and_source_version_mismatch_fails(self):
        root = self.copied_release("euler-v2-v0")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["source"]["protocol_generation"] = "euler-v1"
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "version fields"):
            verify(manifest_path)

    def test_capture_request_drift_fails_after_rebinding(self):
        root = self.copied_release("euler-v2-v0")
        capture_path = root / "capture.json"
        capture = json.loads(capture_path.read_text())
        capture["request"]["query"]["limit"] = "99"
        capture_path.write_bytes(canonical_json(capture) + b"\n")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["capture_manifest"]["sha256"] = sha256_bytes(capture_path.read_bytes())
        manifest["capture_manifest"]["bytes"] = len(capture_path.read_bytes())
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "request does not match"):
            verify(manifest_path)

    def test_capture_timestamp_must_match_preserved_response(self):
        root = self.copied_release("euler-v2-v0")
        capture_path = root / "capture.json"
        capture = json.loads(capture_path.read_text())
        capture["captured_at"] = "2026-08-17T02:32:00.000Z"
        capture_path.write_bytes(canonical_json(capture) + b"\n")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["capture_manifest"]["sha256"] = sha256_bytes(capture_path.read_bytes())
        manifest["capture_manifest"]["bytes"] = len(capture_path.read_bytes())
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "timestamp does not match"):
            verify(manifest_path)

    def test_euler_v1_request_id_is_bound_to_the_response(self):
        root = self.copied_release("euler-v1-v0")
        capture_path = root / "capture.json"
        capture = json.loads(capture_path.read_text())
        del capture["request"]["id"]
        capture_path.write_bytes(canonical_json(capture) + b"\n")
        manifest_path = root / "coverage.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["capture_manifest"]["sha256"] = sha256_bytes(capture_path.read_bytes())
        manifest["capture_manifest"]["bytes"] = len(capture_path.read_bytes())
        manifest_path.write_bytes(canonical_json(manifest) + b"\n")
        with self.assertRaisesRegex(TabulariumError, "request does not match"):
            verify(manifest_path)


V1_RELEASES = {
    "euler-v1-v1": {
        "predecessor": "euler-v1-v0",
        "release": "euler-v1-borrow-block-14531589-v1",
        "superseded": "euler-v1-borrow-block-14531589-v0",
        "rows": 1,
        "digests": {
            "source.json":
                "1241cbed85189e79f9b0f8418e6838b297b4b661ad3e9f2d8a86903e22a6e790",
            "capture.json":
                "63d63a29d7d29c0f7be2f62fb4408ea7c5732b79bc0fe76b48a61527d7359aba",
            "events.jsonl":
                "5b1016a9bc143f42e9bea46de71b3d1917bf6731d93b4c49f974df3660bc8595",
            "coverage.json":
                "825c7b7ad59ed5fedd4e4f403a2f2b3bac9c60fc06fd9b49612f2f7a771b2e18",
        },
    },
    "euler-v2-v1": {
        "predecessor": "euler-v2-v0",
        "release": "euler-v2-owner-activity-1786933919-v1",
        "superseded": "euler-v2-owner-activity-1786933919-v0",
        "rows": 2,
        "digests": {
            "source.json":
                "10f5c8e8242ef3745fbd69c4d8aed458f31b165fc4526f638e76df59a69a18cc",
            "capture.json":
                "46b623f4c2c832f1529bb9b4fa4b992229890240db04efaaa2c8f0c40a045b9a",
            "events.jsonl":
                "f2b227058f53cd644c11359e911c8494924d6fef7da7072e8a33a4baf952d02a",
            "coverage.json":
                "cd23d3b89d949ccd9afad7ef7284b2172303af2bf8c1fb8151cd9c82c9fc22c7",
        },
    },
}


class EulerSupersedingReleaseTests(unittest.TestCase):
    """The two Euler v1 releases restate their v0 releases under schema 3."""

    def test_all_eight_v1_release_artifact_hashes_are_fixed(self):
        for release, declared in V1_RELEASES.items():
            for name, digest in declared["digests"].items():
                self.assertEqual(
                    hashlib.sha256((EXAMPLES / release / name).read_bytes()).hexdigest(),
                    digest,
                    "%s/%s" % (release, name),
                )

    def test_each_v1_source_is_its_v0_source_byte_for_byte(self):
        for release, declared in V1_RELEASES.items():
            predecessor = declared["predecessor"]
            self.assertEqual(
                (EXAMPLES / release / "source.json").read_bytes(),
                (EXAMPLES / predecessor / "source.json").read_bytes(),
                release,
            )
            self.assertEqual(
                declared["digests"]["source.json"],
                RELEASES[predecessor]["source.json"],
                release,
            )

    def test_each_v1_capture_differs_from_its_v0_capture_in_release_alone(self):
        for release, declared in V1_RELEASES.items():
            v0 = json.loads(
                (EXAMPLES / declared["predecessor"] / "capture.json").read_text()
            )
            v1 = json.loads((EXAMPLES / release / "capture.json").read_text())
            differing = sorted(
                key for key in set(v0) | set(v1) if v0.get(key) != v1.get(key)
            )
            self.assertEqual(differing, ["release"], release)
            self.assertEqual(v0["release"], declared["superseded"], release)
            self.assertEqual(v1["release"], declared["release"], release)
            self.assertEqual(v1["request"], v0["request"], release)

    def test_the_euler_v1_capture_keeps_the_request_id_the_response_is_bound_to(self):
        """The identifier the preserved RPC response answers.

        `verify` reconciles the capture's request with the preserved response,
        and the v1 capture was derived from the v0 bytes rather than rewritten,
        so this is what proves the derivation kept the whole request object and
        not only the fields a JSON round trip happens to preserve.
        """
        capture = json.loads((EXAMPLES / "euler-v1-v1" / "capture.json").read_text())
        self.assertEqual(capture["request"]["id"], 1)
        source = json.loads((EXAMPLES / "euler-v1-v1" / "source.json").read_text())
        self.assertEqual(source["id"], capture["request"]["id"])

    def test_both_v1_releases_verify_offline_as_schema_three(self):
        for release, declared in V1_RELEASES.items():
            root = EXAMPLES / release
            paths = tuple(root / name for name in declared["digests"])
            before = {path: path.read_bytes() for path in paths}
            with mock.patch.object(
                socket.socket, "connect", side_effect=AssertionError("network used")
            ):
                report = verify(root / "coverage.json")
            self.assertEqual(report.schema_version, 3, release)
            self.assertEqual(report.release, declared["release"], release)
            self.assertEqual(report.rows, declared["rows"], release)
            self.assertEqual({path: path.read_bytes() for path in paths}, before)

    def test_both_v1_manifests_and_rows_state_schema_three(self):
        for release, declared in V1_RELEASES.items():
            manifest = json.loads((EXAMPLES / release / "coverage.json").read_text())
            self.assertEqual(manifest["schema_version"], 3, release)
            self.assertEqual(manifest["versions"]["event_schema"], 3, release)
            self.assertEqual(manifest["release"], declared["release"], release)
            rows = [
                json.loads(line)
                for line in (EXAMPLES / release / "events.jsonl").read_text().splitlines()
                if line
            ]
            self.assertEqual(len(rows), declared["rows"], release)
            self.assertEqual({row["schema_version"] for row in rows}, {3}, release)

    def test_both_documented_v1_rebuilds_match_committed_bytes(self):
        for release in V1_RELEASES:
            result = subprocess.run(
                [sys.executable, str(EXAMPLES / release / "rebuild.py")],
                cwd=support.REPO_ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("rebuild matches", result.stdout)

    def test_each_release_readme_names_the_other(self):
        """On-call question 4 of the study, checked in both directions."""
        for release, declared in V1_RELEASES.items():
            predecessor = declared["predecessor"]
            v0_readme = (EXAMPLES / predecessor / "README.md").read_text()
            v1_readme = (EXAMPLES / release / "README.md").read_text()
            self.assertIn(declared["release"], v0_readme, predecessor)
            self.assertIn("../%s/README.md" % release, v0_readme, predecessor)
            self.assertIn(declared["superseded"], v1_readme, release)
            self.assertIn("../%s/README.md" % predecessor, v1_readme, release)


if __name__ == "__main__":
    unittest.main()
