"""The Wildcat demonstration must check its fixed inputs and fail closed."""

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/wildcat-mainnet-v0"
spec = importlib.util.spec_from_file_location("wildcat_demo", EXAMPLE / "demo.py")
demo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(demo)


class WildcatDemoTests(unittest.TestCase):
    def test_offline_demo_reaches_all_named_gates(self):
        result = subprocess.run([sys.executable, str(EXAMPLE / "demo.py")], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["components"], 18)
        self.assertEqual(report["cases"], 10)
        self.assertEqual(set(report["refusals"]), {"citation", "block", "missing-read"})
        self.assertFalse(report["model_executed"])

    def test_changed_statement_is_refused_before_rebuild(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "statement.json"
            target.write_bytes((EXAMPLE / "grounded-agent.intoto.json").read_bytes() + b"\n")
            with patch.object(demo.rebuild, "build") as build:
                with self.assertRaisesRegex(demo.BereanError, "statement: fixed bytes changed"):
                    demo.demonstrate(statement_path=target)
                build.assert_not_called()

    def test_unlisted_release_file_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "release"
            shutil.copytree(EXAMPLE / "release", target)
            (target / "unlisted.txt").write_bytes(b"undeclared")
            with self.assertRaisesRegex(demo.BereanError, "original: release gates failed"):
                demo.demonstrate(reference=target)

    def test_rebuilt_promotion_bytes_are_checked(self):
        original = demo.rebuild.build
        def changed(inputs, target):
            digest = original(inputs, target)
            with (target / "promotions.jsonl").open("ab") as handle:
                handle.write(b"\n")
            return digest
        with patch.object(demo.rebuild, "build", side_effect=changed):
            with self.assertRaises(demo.grounded_agent.CaptureError):
                demo.demonstrate()


if __name__ == "__main__":
    unittest.main()
