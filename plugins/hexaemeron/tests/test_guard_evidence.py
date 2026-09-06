"""Maintained guard-evidence admission tests for Fiat inoculation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest

try:
    from .test_hexctl import hexctl_module
except ImportError:
    from test_hexctl import hexctl_module


FIXTURE_ROOT = Path(__file__).parent / "fixtures/issue-453"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def canonical_report(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")


def git_blob_oid(raw: bytes) -> str:
    header = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(header + raw).hexdigest()


class GuardEvidenceTests(unittest.TestCase):
    def test_guard_json_depth_measures_over_limit_without_recursing(self):
        controller = hexctl_module()
        document = {}
        cursor = document
        for _ in range(1_000):
            child = {}
            cursor["child"] = child
            cursor = child

        self.assertGreater(
            controller._guard_json_depth(document),
            controller.GUARD_MANIFEST_DEPTH_MAX,
        )

    def test_kf_453_03_parent_report_is_bound(self):
        fixture = load_fixture("guard-evidence.json")
        raw_report = canonical_report(fixture["raw_report"]["payload"])
        self.assertEqual(fixture["raw_report"]["bytes"], len(raw_report))

        controller = hexctl_module()
        guard_blobs = []
        for row in fixture["guard_blob_payloads"]:
            raw = row["content"].encode("utf-8")
            guard_blobs.append(
                {
                    "path": row["path"],
                    "status": row["status"],
                    "mode": row["mode"],
                    "oid": git_blob_oid(raw),
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
        retained_report = {
            "path": fixture["retained_report"],
            "bytes": len(raw_report),
            "sha256": hashlib.sha256(raw_report).hexdigest(),
        }
        manifest = controller._build_guard_manifest(
            finding_id=fixture["finding_id"],
            consuming_step=fixture["consuming_step"],
            controller_run_id=fixture["controller_run_id"],
            worktree_identity=fixture["worktree_identity"],
            capture=fixture["capture"],
            step_parent=fixture["step_parent"],
            guard_commit=fixture["guard_commit"],
            changed_paths=fixture["changed_paths"],
            guard_blobs=guard_blobs,
            test_command=fixture["test_command"],
            test_argv=fixture["test_argv"],
            report_format=fixture["report_format"],
            report_file=fixture["report_file"],
            retained_report=retained_report,
            runner_exit=1,
            counters=fixture["counters"],
            verdict="guarded",
        )

        self.assertEqual("elenchus-guard-manifest/v1", manifest["schema"])
        self.assertEqual(set(fixture["manifest_fields"]), set(manifest))
        self.assertEqual(fixture["changed_paths"], manifest["changed_paths"])
        self.assertEqual(guard_blobs, manifest["guard_blobs"])
        self.assertEqual(retained_report, manifest["retained_report"])
        self.assertEqual(set(fixture["capture_fields"]), set(manifest["capture"]))
        self.assertEqual(set(fixture["counter_fields"]), set(manifest["counters"]))

    def test_kf_453_04_only_strict_guard_evidence_is_admitted(self):
        fixture = load_fixture("guard-outcomes.json")
        controller = hexctl_module()
        guarded = fixture["outcomes"][0]
        self.assertEqual(
            fixture["expected_counters"],
            controller._guard_admission_counters(
                "unittest-json-v1",
                canonical_report(guarded["report"]),
                guarded["result"],
            ),
        )
        for group in ("outcomes", "malformed", "counter_mismatches"):
            rows = fixture[group][1:] if group == "outcomes" else fixture[group]
            for row in rows:
                with self.subTest(group=group, case=row["id"]):
                    with self.assertRaises(ValueError):
                        controller._guard_admission_counters(
                            "unittest-json-v1",
                            canonical_report(row["report"]),
                            row["result"],
                        )


if __name__ == "__main__":
    unittest.main()
