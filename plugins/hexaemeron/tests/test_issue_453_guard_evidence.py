"""Historical red guards for issue 453 Step 3 evidence admission."""

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
    def test_kf_453_03_parent_report_is_bound(self):
        fixture = load_fixture("guard-evidence.json")
        raw_report = canonical_report(fixture["raw_report"]["payload"])
        self.assertEqual(fixture["raw_report"]["bytes"], len(raw_report))

        controller = hexctl_module()
        build_manifest = getattr(controller, "_build_guard_manifest", None)
        self.assertTrue(
            callable(build_manifest),
            "Fiat does not bind retained parent reports into guard manifests",
        )

        self.assertEqual(
            fixture["raw_report"]["sha256"], hashlib.sha256(raw_report).hexdigest()
        )
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
        manifest = build_manifest(
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

        self.assertEqual(
            {
                "schema": "elenchus-guard-manifest/v1",
                "finding_id": fixture["finding_id"],
                "consuming_step": fixture["consuming_step"],
                "controller_run_id": fixture["controller_run_id"],
                "worktree_identity": fixture["worktree_identity"],
                "capture": fixture["capture"],
                "step_parent": fixture["step_parent"],
                "guard_commit": fixture["guard_commit"],
                "changed_paths": fixture["changed_paths"],
                "guard_blobs": guard_blobs,
                "test_command": fixture["test_command"],
                "test_argv": fixture["test_argv"],
                "report_format": fixture["report_format"],
                "report_file": fixture["report_file"],
                "retained_report": retained_report,
                "runner_exit": 1,
                "counters": fixture["counters"],
                "verdict": "guarded",
            },
            manifest,
        )
        self.assertEqual(set(fixture["manifest_fields"]), set(manifest))
        self.assertEqual(
            set(fixture["worktree_identity_fields"]),
            set(manifest["worktree_identity"]),
        )
        self.assertEqual(set(fixture["capture_fields"]), set(manifest["capture"]))
        self.assertEqual(
            set(fixture["guard_blob_fields"]), set(manifest["guard_blobs"][0])
        )
        self.assertEqual(
            set(fixture["retained_report_fields"]),
            set(manifest["retained_report"]),
        )
        self.assertEqual(set(fixture["counter_fields"]), set(manifest["counters"]))
        self.assertEqual(fixture["changed_paths"], manifest["changed_paths"])
        self.assertEqual(guard_blobs, manifest["guard_blobs"])
        self.assertEqual(retained_report, manifest["retained_report"])

    def test_kf_453_04_only_strict_guard_evidence_is_admitted(self):
        fixture = load_fixture("guard-outcomes.json")
        self.assertEqual("guarded", fixture["outcomes"][0]["id"])

        controller = hexctl_module()
        admit = getattr(controller, "_guard_admission_counters", None)
        self.assertTrue(
            callable(admit),
            "Fiat has no strict parent-guard evidence admission gate",
        )

        guarded = fixture["outcomes"][0]
        guarded_raw = canonical_report(guarded["report"])
        guarded_result = guarded["result"]
        self.assertEqual(
            fixture["expected_counters"],
            admit("unittest-json-v1", guarded_raw, guarded_result),
        )

        for row in fixture["outcomes"][1:]:
            with self.subTest(outcome=row["id"]):
                self.assertFalse(row["admitted"])
                with self.assertRaises(ValueError):
                    admit(
                        "unittest-json-v1",
                        canonical_report(row["report"]),
                        row["result"],
                    )
        for row in fixture["malformed"]:
            with self.subTest(malformed=row["id"]):
                with self.assertRaises(ValueError):
                    admit(
                        "unittest-json-v1",
                        canonical_report(row["report"]),
                        row["result"],
                    )
        for row in fixture["counter_mismatches"]:
            with self.subTest(counter_mismatch=row["id"]):
                with self.assertRaises(ValueError):
                    admit(
                        "unittest-json-v1",
                        canonical_report(row["report"]),
                        row["result"],
                    )


if __name__ == "__main__":
    unittest.main()
