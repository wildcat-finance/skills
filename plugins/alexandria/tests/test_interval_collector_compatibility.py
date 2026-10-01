"""Recorded imports retain the collector's public and private module state."""

from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

import interval_collector
import usdc_interval


class CompatibilityTests(unittest.TestCase):
    def test_old_import_shares_all_names_and_mutable_state(self):
        self.assertIs(usdc_interval, interval_collector)
        self.assertIs(usdc_interval.Builder, interval_collector.Builder)
        self.assertIs(usdc_interval._receipt_shards, interval_collector._receipt_shards)
        with mock.patch.object(usdc_interval, "MAX_COLLECT_BYTES", 123):
            self.assertEqual(interval_collector.MAX_COLLECT_BYTES, 123)

    def test_old_cli_preserves_failure_status_and_diagnostic(self):
        results = [subprocess.run(
            [sys.executable, str(PLUGIN / "scripts" / name),
             "check", str(PLUGIN / "absent-release")],
            capture_output=True, check=False,
        ) for name in ("interval_collector.py", "usdc_interval.py")]
        self.assertEqual(results[0].returncode, 1)
        self.assertEqual(results[0].returncode, results[1].returncode)
        self.assertEqual(results[0].stdout, results[1].stdout)
        self.assertEqual(results[0].stderr, results[1].stderr)
