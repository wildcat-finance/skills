"""Step 1, round 1: the filesystem and parser boundaries the audit found.

Each case names the exact specimen that reproduced the defect. Every one of
them passes against the fixed tree and fails against its parent.
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
PILOT = PLUGIN_ROOT / "specimens/pilot/policy.json"


def load():
    spec = importlib.util.spec_from_file_location("anamnesis_boundaries", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anamnesis = load()


class Sandbox(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)


class EventStreamBoundary(Sandbox):
    """A001: the stream path is operator input and was followed as a symlink."""

    def test_an_event_stream_symlink_is_refused(self):
        victim = self.root / "victim.txt"
        victim.write_text("untouched", encoding="utf-8")
        link = self.root / "events.jsonl"
        os.symlink(str(victim), str(link))

        events = anamnesis.Events(str(link))
        with self.assertRaises(OSError):
            events.emit("anamnesis.source.refused", "v", "d", "r", {"rule": "X"})
        self.assertEqual(victim.read_text(encoding="utf-8"), "untouched")

    def test_an_ordinary_event_stream_still_appends(self):
        stream = self.root / "events.jsonl"
        events = anamnesis.Events(str(stream))
        events.emit("anamnesis.source.admitted", "v", "d", "r", {"bytes": 1})
        events.emit("anamnesis.source.admitted", "v", "d", "s", {"bytes": 2})
        lines = stream.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[0])["record"], "r")


class ReportStagingBoundary(Sandbox):
    """A002: staging opened through whatever sat at a fixed ".partial" name."""

    def test_a_staged_report_symlink_is_refused(self):
        victim = self.root / "victim.txt"
        victim.write_text("untouched", encoding="utf-8")
        target = self.root / "report.json"
        # The pre-fix staging name was exactly this.
        os.symlink(str(victim), f"{target}.partial")

        anamnesis.write_report(str(target), "seed-source-rights-admitted", True, "c")
        self.assertEqual(victim.read_text(encoding="utf-8"), "untouched")
        self.assertEqual(
            json.loads(target.read_text(encoding="utf-8"))["criterion"],
            "seed-source-rights-admitted",
        )

    def test_two_reports_do_not_share_a_staging_name(self):
        first = self.root / "a.json"
        second = self.root / "b.json"
        anamnesis.write_report(str(first), "seed-source-rights-admitted", True, "c")
        anamnesis.write_report(str(second), "seed-source-rights-admitted", True, "c")
        leftovers = [p.name for p in self.root.iterdir() if p.name.endswith(".partial")]
        self.assertEqual(leftovers, [])

    def test_a_report_replaces_an_existing_one_atomically(self):
        target = self.root / "report.json"
        target.write_text("stale", encoding="utf-8")
        anamnesis.write_report(str(target), "seed-source-rights-admitted", True, "c")
        self.assertEqual(
            json.loads(target.read_text(encoding="utf-8"))["value"], True
        )


class DuplicateKeyBoundary(Sandbox):
    """A003: json.loads kept the last of a duplicated key silently."""

    def policy_text(self, body):
        return body

    def test_a_duplicated_policy_key_is_refused(self):
        policy = json.loads(PILOT.read_text(encoding="utf-8"))
        raw = json.dumps(policy, indent=2)
        # Declare policy_version twice: a reader sees the first, the parser the
        # last. Neither should be trusted, so the whole policy is refused.
        injected = raw.replace(
            '"policy_version"', '"policy_version": "shadowed",\n  "policy_version"', 1
        )
        path = self.root / "policy.json"
        path.write_text(injected, encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.admit(str(path), anamnesis.Events())
        self.assertEqual(caught.exception.code, "A025")
        self.assertIn("policy_version", caught.exception.message)

    def test_a_duplicated_nested_key_is_refused(self):
        policy = json.loads(PILOT.read_text(encoding="utf-8"))
        raw = json.dumps(policy, indent=2)
        injected = raw.replace('"sha256"', '"sha256": "0",\n      "sha256"', 1)
        path = self.root / "policy.json"
        path.write_text(injected, encoding="utf-8")
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.admit(str(path), anamnesis.Events())
        self.assertEqual(caught.exception.code, "A025")

    def test_a_policy_without_duplicates_still_parses(self):
        path = self.root / "policy.json"
        path.write_text(PILOT.read_text(encoding="utf-8"), encoding="utf-8")
        policy = anamnesis.parse_policy(path.read_bytes(), "policy")
        self.assertEqual(policy["schema"], anamnesis.POLICY_SCHEMA)


if __name__ == "__main__":
    unittest.main()


class RefusalEventCoverage(Sandbox):
    """S1-R2-02: only per-source refusals left a durable event behind."""

    def setUp(self):
        super().setUp()
        (self.root / "sources").mkdir()
        self.policy = json.loads(PILOT.read_text(encoding="utf-8"))
        for source in self.policy["sources"]:
            origin = PLUGIN_ROOT / "specimens/pilot" / source["path"]
            (self.root / source["path"]).write_bytes(origin.read_bytes())

    def refuse(self, policy):
        path = self.root / "policy.json"
        path.write_text(json.dumps(policy, indent=2), encoding="utf-8")
        events = anamnesis.Events()
        with self.assertRaises(anamnesis.Refusal) as caught:
            anamnesis.admit(str(path), events)
        return caught.exception, events

    def assert_recorded(self, refusal, events):
        refused = [e for e in events.emitted if e["event"] == "anamnesis.source.refused"]
        self.assertEqual(len(refused), 1)
        self.assertEqual(refused[0]["rule"], refusal.code)
        self.assertEqual(refused[0]["policy_version"], self.policy["policy_version"])
        self.assertEqual(len(refused[0]["correlation_id"]), 16)

    def test_a_record_level_refusal_is_recorded(self):
        self.policy["records"][0]["source"] = "no-such-source"
        refusal, events = self.refuse(self.policy)
        self.assertEqual(refusal.code, "A072")
        self.assert_recorded(refusal, events)

    def test_a_duplicate_record_id_refusal_is_recorded(self):
        self.policy["records"].append(dict(self.policy["records"][0]))
        refusal, events = self.refuse(self.policy)
        self.assertEqual(refusal.code, "A071")
        self.assert_recorded(refusal, events)

    def test_an_unknown_record_key_refusal_is_recorded(self):
        self.policy["records"][0]["extra"] = True
        refusal, events = self.refuse(self.policy)
        self.assertEqual(refusal.code, "A011")
        self.assert_recorded(refusal, events)

    def test_a_source_refusal_is_still_recorded_once(self):
        self.policy["sources"][0]["sha256"] = "0" * 64
        refusal, events = self.refuse(self.policy)
        self.assertEqual(refusal.code, "A057")
        self.assert_recorded(refusal, events)
