"""The checked-in interval demonstration: offline, deterministic, and not skippable."""

import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN / "examples" / "usdc-interval-v0"
sys.path.insert(0, str(PLUGIN / "scripts"))
sys.path.insert(0, str(EXAMPLE))

from alexandria_lib.errors import AlexandriaError  # noqa: E402


def demo():
    """Import the demonstration, failing rather than skipping when it is absent.

    Alexandria present with its demonstration missing is a defect, and a skip
    there turns the only end-to-end proof of this capability into a silence
    that reads as a pass. Finding S4-R1-01 of the issue-391 run is exactly
    that failure in a sibling plugin.
    """
    for required in ("demo.py", "expected.json", "fixtures/primary.json",
                     "fixtures/secondary.json", "fixtures/epochs.json"):
        if not (EXAMPLE / required).is_file():
            raise AssertionError(
                f"the interval demonstration is missing {required} at {EXAMPLE}; this "
                "suite proves the collector end to end and must fail rather than skip"
            )
    import demo as module

    return module


class IntervalDemoTests(unittest.TestCase):
    """The conformance evidence for `demo-reproduces-release-id`."""

    def setUp(self):
        self.module = demo()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.expected = json.loads((EXAMPLE / "expected.json").read_text(encoding="utf-8"))

    def build(self, name="built"):
        output = self.root / name
        summary = self.module.build(output)
        return output, summary

    def test_the_offline_path_reproduces_the_pinned_release_id(self):
        output, summary = self.build()
        self.assertEqual(summary["release_id"], self.expected["release_id"])
        self.assertEqual(summary["shard_statuses"], self.expected["shard_statuses"])
        self.assertEqual(summary["reconciliation"], self.expected["reconciliation"])
        self.assertEqual(summary["epochs"], self.expected["epochs"])
        self.assertEqual(self.module.verify(output)["release_id"], self.expected["release_id"])

    def test_the_path_is_interrupted_and_resumed_once(self):
        _output, summary = self.build()
        self.assertEqual(summary["interrupted_at"], self.module.KILL_AT)
        self.assertEqual(summary["resumed_from_shard"], self.expected["resumed_from_shard"])
        self.assertGreater(summary["resumed_from_shard"], 0)

    def test_two_builds_agree_byte_for_byte(self):
        first, _ = self.build("first")
        second, _ = self.build("second")
        self.assertEqual(
            (first / "summary.json").read_bytes(), (second / "summary.json").read_bytes()
        )

    def test_a_partial_output_is_removed_after_a_failure(self):
        output = self.root / "doomed"
        with mock.patch.object(self.module, "REGISTRY", self.root / "absent.json"):
            with self.assertRaises(AlexandriaError):
                self.module.build(output)
        self.assertFalse(output.exists())

    def test_an_existing_output_refuses(self):
        output = self.root / "occupied"
        output.mkdir()
        with self.assertRaisesRegex(AlexandriaError, "already exists"):
            self.module.build(output)
        self.assertTrue(output.exists())

    def test_verify_refuses_a_tampered_release(self):
        output, _ = self.build("tampered")
        manifest = json.loads((output / "release" / "manifest.json").read_text())
        target = next(
            output / "release" / component["object_path"]
            for component in manifest["components"]
            if component["name"] == "logs"
        )
        target.write_bytes(target.read_bytes().replace(b'"logs"', b'"logz"', 1))
        with self.assertRaises(AlexandriaError):
            self.module.verify(output)

    def test_verify_refuses_a_summary_that_disagrees_with_the_pin(self):
        output, _ = self.build("edited")
        summary = json.loads((output / "summary.json").read_text())
        summary["resumed_from_shard"] += 1
        (output / "summary.json").write_text(json.dumps(summary, sort_keys=True))
        with self.assertRaisesRegex(AlexandriaError, "resume point"):
            self.module.verify(output)

    def test_neither_path_opens_a_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            output, _ = self.build("offline")
            self.module.verify(output)

    def test_the_command_line_runs_both_paths(self):
        output = self.root / "cli"
        built = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "build", "--output", str(output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(built.returncode, 0, built.stderr)
        self.assertIn(self.expected["release_id"], built.stdout)
        verified = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py"), "verify", str(output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertNotIn("Traceback", verified.stderr)

    def test_the_command_line_reports_a_controlled_usage_error(self):
        result = subprocess.run(
            [sys.executable, str(EXAMPLE / "demo.py")],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_the_example_says_what_it_does_not_establish(self):
        readme = (EXAMPLE / "README.md").read_text(encoding="utf-8")
        for claim in ("synthetic", "no network", "not observed"):
            self.assertIn(claim, readme.lower())


if __name__ == "__main__":
    unittest.main()
