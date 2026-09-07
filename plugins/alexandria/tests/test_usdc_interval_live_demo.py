"""The preserved live interval: rebuilt offline, byte-bound, and not skippable.

The bytes under `examples/usdc-interval-live-v0/staging/` are the only evidence
anyone will ever have that the live collection happened as described, so these
tests hold the demonstration to them: the rebuild reproduces the identifier the
example pins, one flipped byte in a preserved journal changes it, and a missing
journal, plan, checkpoint or expectation fails rather than skips.

The example is loaded by path under its own module name. The synthetic
`usdc-interval-v0` demonstration ships a `demo.py` too, and putting either
example's directory on `sys.path` would let one shadow the other.
"""

import importlib.util
import json
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN / "examples" / "usdc-interval-live-v0"
STAGING = EXAMPLE / "staging"
MODULE_NAME = "usdc_interval_live_demo"
REQUIRED = (
    "demo.py",
    "plan.json",
    "registry.json",
    "expected.json",
    "README.md",
    "staging/checkpoint.json",
    "staging/journals/boundary-blocks.jsonl",
    "staging/journals/epoch-evidence.jsonl",
    "staging/journals/logs.jsonl",
    "staging/reconciliation/reconciliation.json",
)

sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.errors import AlexandriaError  # noqa: E402


def demo():
    """Import the demonstration, failing rather than skipping when it is absent.

    A preserved capture whose files are gone is a defect, and a skip there
    turns the only proof of the live run into a silence that reads as a pass.
    """
    missing = [name for name in REQUIRED if not (EXAMPLE / name).is_file()]
    if missing:
        raise AssertionError(
            f"the preserved live interval is missing {', '.join(missing)} at {EXAMPLE}; "
            "this suite is the proof the capture rebuilds and must fail rather than skip"
        )
    if MODULE_NAME in sys.modules:
        return sys.modules[MODULE_NAME]
    spec = importlib.util.spec_from_file_location(MODULE_NAME, EXAMPLE / "demo.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


class LiveDemoTestCase(unittest.TestCase):
    def setUp(self):
        self.module = demo()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.expected = json.loads((EXAMPLE / "expected.json").read_text(encoding="utf-8"))

    def build(self, name="built"):
        output = self.root / name
        return output, self.module.build(output)


class DemoReproducesReleaseIdTests(LiveDemoTestCase):
    """The conformance evidence for `demo-reproduces-live-release-id`."""

    def test_the_rebuild_reproduces_the_pinned_identifier(self):
        _output, summary = self.build()
        self.assertEqual(summary["release_id"], self.expected["release_id"])
        self.assertEqual(summary["epochs"], 2)
        self.assertEqual(summary["reconciliation"], "agreed")
        self.assertEqual(summary["shard_statuses"], {"complete": 4})

    def test_verify_compares_every_pinned_identity(self):
        output, _summary = self.build()
        derived = self.module.verify(output)
        self.assertEqual(derived["release_id"], self.expected["release_id"])
        self.assertEqual(derived["epochs"], self.expected["epochs"])
        self.assertEqual(derived["reconciliation"], self.expected["reconciliation"])
        self.assertEqual(derived["implementations"], self.expected["implementations"])
        self.assertEqual(len(derived["implementations"]), 2)
        self.assertEqual(derived["start_hash"], self.expected["start_hash"])
        self.assertEqual(derived["end_hash"], self.expected["end_hash"])

    def test_the_interval_spans_two_implementations_of_one_proxy(self):
        output, _summary = self.build()
        manifest = json.loads((output / "release" / "manifest.json").read_text(encoding="utf-8"))
        table = next(
            output / "release" / component["object_path"]
            for component in manifest["components"]
            if component["name"] == "epoch-table"
        )
        epochs = json.loads(table.read_text(encoding="utf-8"))["epochs"]
        self.assertEqual(len(epochs), 2)
        self.assertIsNone(epochs[0]["upgrade"])
        self.assertIsNotNone(epochs[1]["upgrade"])
        self.assertNotEqual(epochs[0]["implementation"], epochs[1]["implementation"])
        for epoch in epochs:
            self.assertEqual(
                self.expected["implementations"][epoch["implementation"]],
                epoch["implementation_code_sha256"],
            )

    def test_every_capture_binds_both_boundary_hashes(self):
        output, _summary = self.build()
        manifest = json.loads((output / "release" / "manifest.json").read_text(encoding="utf-8"))
        captures = [
            capture for capture in manifest["captures"]
            if capture["id"] in ("boundary-blocks", "logs", "epoch-evidence")
        ]
        self.assertEqual(len(captures), 3)
        for capture in captures:
            self.assertEqual(capture["scope"]["finality"], "finalized", capture["id"])
            self.assertEqual(capture["scope"]["interval"]["start_hash"], self.expected["start_hash"])
            self.assertEqual(capture["scope"]["interval"]["end_hash"], self.expected["end_hash"])

    def test_two_rebuilds_agree_byte_for_byte(self):
        first, _ = self.build("first")
        second, _ = self.build("second")
        self.assertEqual(
            (first / "summary.json").read_bytes(), (second / "summary.json").read_bytes()
        )

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

    def test_an_existing_output_refuses(self):
        output = self.root / "occupied"
        output.mkdir()
        with self.assertRaisesRegex(AlexandriaError, "already exists"):
            self.module.build(output)
        self.assertTrue(output.exists())


class PreservedBytesIdentityTests(LiveDemoTestCase):
    """The guard for `preserved-bytes-identity`: the journals are the release."""

    def copied_example(self):
        """A whole copy of the example, so a tampered byte never touches the tree."""
        copy = self.root / "example"
        shutil.copytree(EXAMPLE, copy)
        return copy

    def rebuild_from(self, copy, name="rebuilt"):
        output = self.root / name
        with mock.patch.multiple(
            self.module,
            PLAN=copy / "plan.json",
            REGISTRY=copy / "registry.json",
            STAGING=copy / "staging",
            EXPECTED=copy / "expected.json",
        ):
            return output, self.module.build(output)

    def test_an_untouched_copy_still_reproduces_the_identifier(self):
        _output, summary = self.rebuild_from(self.copied_example(), "clean")
        self.assertEqual(summary["release_id"], self.expected["release_id"])

    def test_one_flipped_byte_in_a_preserved_journal_changes_the_identifier(self):
        copy = self.copied_example()
        journal = copy / "staging" / "journals" / "logs.jsonl"
        original = journal.read_text(encoding="utf-8")
        marker = '\\"data\\":\\"0x'
        at = original.index(marker) + len(marker)
        flipped = "1" if original[at] == "0" else "0"
        journal.write_text(original[:at] + flipped + original[at + 1:], encoding="utf-8")
        self.assertNotEqual(journal.read_text(encoding="utf-8"), original)
        _output, summary = self.rebuild_from(copy, "flipped")
        self.assertNotEqual(summary["release_id"], self.expected["release_id"])

    def test_verify_refuses_a_release_whose_identifier_moved(self):
        copy = self.copied_example()
        journal = copy / "staging" / "journals" / "logs.jsonl"
        original = journal.read_text(encoding="utf-8")
        marker = '\\"data\\":\\"0x'
        at = original.index(marker) + len(marker)
        flipped = "1" if original[at] == "0" else "0"
        journal.write_text(original[:at] + flipped + original[at + 1:], encoding="utf-8")
        output, _summary = self.rebuild_from(copy, "moved")
        with self.assertRaisesRegex(AlexandriaError, "release_id"):
            self.module.verify(output)

    def test_verify_refuses_a_tampered_release(self):
        output, _summary = self.build("tampered")
        manifest = json.loads((output / "release" / "manifest.json").read_text(encoding="utf-8"))
        target = next(
            output / "release" / component["object_path"]
            for component in manifest["components"]
            if component["name"] == "logs"
        )
        target.write_bytes(target.read_bytes().replace(b'"logs"', b'"logz"', 1))
        with self.assertRaises(AlexandriaError):
            self.module.verify(output)

    def test_verify_refuses_a_summary_that_disagrees_with_the_pin(self):
        output, _summary = self.build("edited")
        summary = json.loads((output / "summary.json").read_text(encoding="utf-8"))
        summary["epochs"] += 1
        (output / "summary.json").write_text(json.dumps(summary, sort_keys=True), encoding="utf-8")
        with self.assertRaisesRegex(AlexandriaError, "recorded summary's epochs"):
            self.module.verify(output)


class OfflineBoundaryTests(LiveDemoTestCase):
    """Neither path opens a socket, and no endpoint survives in the committed bytes."""

    def test_neither_path_opens_a_socket(self):
        with mock.patch.object(
            socket.socket, "connect", side_effect=AssertionError("network used")
        ):
            output, _summary = self.build("offline")
            self.module.verify(output)

    def test_the_committed_capture_carries_no_endpoint(self):
        """No `https://` in the plan, the preserved bytes or the expectation.

        The endpoint reaches the collector through one environment variable and
        is written nowhere; this is the check that the capture kept that
        promise once the bytes were checked in.
        """
        subjects = [EXAMPLE / "plan.json", EXAMPLE / "expected.json"]
        subjects.extend(sorted(path for path in STAGING.rglob("*") if path.is_file()))
        self.assertGreaterEqual(len(subjects), 7)
        for path in subjects:
            self.assertNotIn(
                "https://", path.read_text(encoding="utf-8"), f"{path} names an endpoint"
            )

    def test_the_plan_declares_its_classes_and_a_provider_class_without_a_host(self):
        plan = json.loads((EXAMPLE / "plan.json").read_text(encoding="utf-8"))
        self.assertEqual(plan["evidence_classes"], ["boundary-blocks", "logs"])
        self.assertEqual(plan["finality"]["policy"], "finalized")
        provider = plan["provider"]["class"]
        self.assertEqual(provider, "archive gateway, public tier, no trace methods")
        for forbidden in ("http", "://", ".io", ".com", ".finance"):
            self.assertNotIn(forbidden, provider)

    def test_the_reconciliation_names_a_provider_class_and_no_dispute(self):
        record = json.loads(
            (STAGING / "reconciliation" / "reconciliation.json").read_text(encoding="utf-8")
        )["reconciliation"]
        self.assertEqual(record["status"], "agreed")
        self.assertEqual(record["disputed"], [])
        self.assertGreaterEqual(record["compared"], 8)
        self.assertEqual(record["compared"], record["matched"])
        self.assertEqual(
            record["provider_class"],
            "public relay endpoint, archive logs and state, no trace methods",
        )


class MissingArtefactTests(LiveDemoTestCase):
    """A missing preserved artefact fails; it never skips and never falls back."""

    def test_a_missing_plan_fails(self):
        with mock.patch.object(self.module, "PLAN", self.root / "absent.json"):
            with self.assertRaisesRegex(AlexandriaError, "interval plan is missing"):
                self.module.build(self.root / "unplanned")
        self.assertFalse((self.root / "unplanned").exists())

    def test_a_missing_registry_fails(self):
        with mock.patch.object(self.module, "REGISTRY", self.root / "absent.json"):
            with self.assertRaisesRegex(AlexandriaError, "registry is missing"):
                self.module.build(self.root / "unregistered")
        self.assertFalse((self.root / "unregistered").exists())

    def test_a_missing_checkpoint_fails(self):
        empty = self.root / "empty-staging"
        empty.mkdir()
        with mock.patch.object(self.module, "STAGING", empty):
            with self.assertRaisesRegex(AlexandriaError, "staging tree is missing"):
                self.module.build(self.root / "unstaged")
        self.assertFalse((self.root / "unstaged").exists())

    def test_a_missing_journal_fails(self):
        copy = self.root / "example"
        shutil.copytree(EXAMPLE, copy)
        (copy / "staging" / "journals" / "logs.jsonl").unlink()
        with mock.patch.multiple(
            self.module,
            PLAN=copy / "plan.json",
            REGISTRY=copy / "registry.json",
            STAGING=copy / "staging",
        ):
            with self.assertRaises(AlexandriaError):
                self.module.build(self.root / "unjournalled")
        self.assertFalse((self.root / "unjournalled").exists())

    def test_a_missing_expectation_fails(self):
        output, _summary = self.build("unpinned")
        with mock.patch.object(self.module, "EXPECTED", self.root / "absent.json"):
            with self.assertRaisesRegex(AlexandriaError, "pinned expectation is missing"):
                self.module.verify(output)

    def test_the_example_says_what_it_does_and_does_not_establish(self):
        readme = (EXAMPLE / "README.md").read_text(encoding="utf-8").lower()
        for claim in ("finalized", "traces", "no network", "provider class"):
            self.assertIn(claim, readme)
        self.assertNotIn("https://", readme)


if __name__ == "__main__":
    unittest.main()
