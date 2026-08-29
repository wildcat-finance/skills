"""Hostile capture-profile probes: excluded bytes must not survive any result."""

from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_observation_capture.py"
capture = None
if SCRIPT.is_file():
    SPEC = importlib.util.spec_from_file_location("capture_inoculation", SCRIPT)
    capture = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = capture
    assert SPEC.loader is not None
    SPEC.loader.exec_module(capture)


HOSTILE_LOCATIONS = {
    "prompt": "MULTILINE-PROMPT-SENTINEL-435\\nsecond-line",
    "headers": {"Authorization": "Bearer HEADER-SENTINEL-435"},
    "environment": {"TOKEN": "ENV-SENTINEL-435"},
    "arguments": ["--secret=ARGV-SENTINEL-435"],
    "exception": "TRACE-SENTINEL-435", "url": "https://name:URL-SENTINEL-435@example.invalid/a?token=QUERY-SENTINEL-435",
    "payload": {"nested": ["NESTED-SENTINEL-435"]},
    "source": "SOURCE-SENTINEL-435", "trace": "TRACE-TEXT-SENTINEL-435",
}


class CaptureInoculationTests(unittest.TestCase):
    def setUp(self):
        if capture is None:
            self.skipTest("capture runtime is absent in the detached parent worktree")

    def baseline(self):
        return {"event": {"run_id": "run-435", "event_id": "event-435", "event_type": "run.started", "time": "2026-08-23T22:00:00Z", "status": "success"}, "repository_path": "docs"}

    def test_every_hostile_location_becomes_a_safe_gap(self):
        for field, value in HOSTILE_LOCATIONS.items():
            with self.subTest(field=field):
                candidate = self.baseline()
                candidate[field] = value
                result = capture.capture_candidate(candidate, ROOT)
                public = json.dumps(result.public(), ensure_ascii=False)
                self.assertEqual(result.outcome, "gap")
                self.assertNotIn(field, public)
                self.assertNotIn("SENTINEL-435", public)

    def test_aliases_nested_values_and_unknown_objects_do_not_bypass_allowlist(self):
        for field in ("api_key", "command", "messages", "request", "response", "signed_payload", "unknown_blob"):
            with self.subTest(field=field):
                candidate = self.baseline()
                candidate[field] = {"deep": ["ALIAS-SENTINEL-435"]}
                result = capture.capture_candidate(candidate, ROOT)
                self.assertIn(result.outcome, {"gap", "refused"})
                self.assertNotIn("ALIAS-SENTINEL-435", json.dumps(result.public()))

    def test_bad_redaction_unknown_method_and_low_entropy_do_not_persist(self):
        candidate = self.baseline()
        candidate["redactions"] = [{"field_class": "content", "reason_code": "forbidden_content", "method": "erase"}]
        self.assertEqual(capture.capture_candidate(candidate, ROOT).outcome, "refused")
        candidate = self.baseline()
        candidate["fingerprint"] = {"scope": "scope", "value_b64": "c2VjcmV0", "entropy_bits": 1}
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual((result.outcome, result.code), ("gap", "ineligible_fingerprint"))
        self.assertNotIn("c2VjcmV0", json.dumps(result.public()))

    def test_non_nfc_and_symlink_escape_paths_are_gaps(self):
        candidate = self.baseline()
        candidate["repository_path"] = "do\u0301cs"
        self.assertEqual(capture.capture_candidate(candidate, ROOT).code, "invalid_path")
        candidate = self.baseline()
        candidate["repository_path"] = "../docs"
        self.assertEqual(capture.capture_candidate(candidate, ROOT).code, "invalid_path")

    def test_container_and_input_ceilings_refuse_without_echo(self):
        candidate = self.baseline()
        candidate["redactions"] = [{"field_class": "content", "reason_code": "forbidden_content", "method": "omitted"}] * (capture.MAX_REDACTIONS + 1)
        self.assertEqual(capture.capture_candidate(candidate, ROOT).code, "unsafe_shape")
        candidate = self.baseline()
        candidate["event"]["name"] = "OVERSIZE-SENTINEL-435" * 100
        result = capture.capture_candidate(candidate, ROOT)
        self.assertEqual(result.outcome, "refused")
        self.assertNotIn("OVERSIZE-SENTINEL-435", json.dumps(result.public()))
