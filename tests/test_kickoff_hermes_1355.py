from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from scripts import kickoff_hermes_1355 as checker


def group(group_id: str) -> dict:
    expected = checker.GROUPS[group_id]
    return {
        "id": group_id,
        "repository": expected["repository"],
        "source_access": expected["source_access"],
        "source_commit": expected["source_commit"],
        "prepared_commit": "1" * 40,
        "signature": {
            "status": "verified",
            "fingerprint": checker.SIGNER,
        },
        "compiler_profile": deepcopy(expected["profile"]),
        "admitted_test_paths": list(expected["changed"]),
        "parity": {
            "changed_paths": list(expected["changed"]),
            "production_diff_count": 0,
            "configuration_diff_count": 0,
            "dependency_diff_count": 0,
            "submodule_diff_count": 0,
        },
        "tests": {
            "command": ["forge", "test", "--fuzz-seed", "0x5EED"],
            "seed": "0x5EED",
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "duration_seconds": 1.0,
            "log_sha256": "2" * 64,
            "runner": deepcopy(
                checker.HISTORICAL_RUNNER
                if group_id == "v2-c7be4039"
                else checker.CURRENT_RUNNER
            ),
        },
        "restricted_evidence_sha256": "3" * 64,
    }


def manifest() -> dict:
    return {
        "schema": "hermes-prepared-harnesses-public/v1",
        "candidate": "prepared-source-group",
        "criterion": "prepared-state",
        "access_boundary": {
            "public": "identities-counts-and-digests",
            "restricted": "source-worktrees-complete-logs-and-private-source",
        },
        "groups": [group(group_id) for group_id in checker.GROUPS],
    }


def profile_data(group_id: str) -> dict:
    expected = checker.GROUPS[group_id]["profile"]
    return {
        "solc": expected["solc"],
        "evm_version": expected["evm_version"],
        "via_ir": expected["via_ir"],
        "optimizer": expected["optimizer"],
        "optimizer_runs": expected["optimizer_runs"],
        "bytecode_hash": expected["bytecode_hash"],
    }


class PreparedHarnessManifestTests(unittest.TestCase):
    def assert_refused(self, value: dict, fragment: str) -> None:
        with self.assertRaisesRegex(checker.EvidenceError, fragment):
            checker.validate_public_data(value)

    def test_all_nine_groups_pass(self) -> None:
        checker.validate_public_data(manifest())

    def test_missing_group_is_refused(self) -> None:
        value = manifest()
        value["groups"].pop()
        self.assert_refused(value, "group-count")

    def test_altered_production_bytes_are_refused(self) -> None:
        value = manifest()
        value["groups"][0]["parity"]["production_diff_count"] = 1
        self.assert_refused(value, "production_diff_count")

    def test_altered_configuration_bytes_are_refused(self) -> None:
        value = manifest()
        value["groups"][0]["parity"]["configuration_diff_count"] = 1
        self.assert_refused(value, "configuration_diff_count")

    def test_unsigned_revision_is_refused(self) -> None:
        value = manifest()
        value["groups"][0]["signature"]["status"] = "unknown"
        self.assert_refused(value, "signature")

    def test_wrong_parent_identity_is_refused(self) -> None:
        value = manifest()
        value["groups"][0]["source_commit"] = "4" * 40
        self.assert_refused(value, "source_commit")

    def test_missing_tests_are_refused(self) -> None:
        value = manifest()
        value["groups"][0]["tests"]["passed"] = 0
        self.assert_refused(value, "suite-not-green")

    def test_red_suite_is_refused(self) -> None:
        value = manifest()
        value["groups"][0]["tests"]["failed"] = 1
        self.assert_refused(value, "suite-not-green")

    def test_skipped_suite_is_refused(self) -> None:
        value = manifest()
        value["groups"][0]["tests"]["skipped"] = 1
        self.assert_refused(value, "suite-not-green")

    def test_weakened_fuzz_metadata_is_refused(self) -> None:
        value = manifest()
        value["groups"][0]["tests"]["seed"] = "random"
        self.assert_refused(value, "fuzz-seed")

    def test_digest_drift_is_refused(self) -> None:
        value = manifest()
        value["groups"][0]["tests"]["log_sha256"] = "short"
        self.assert_refused(value, "log_sha256")

    def test_historical_runner_digest_drift_is_refused(self) -> None:
        value = manifest()
        c7 = next(row for row in value["groups"] if row["id"] == "v2-c7be4039")
        c7["tests"]["runner"]["binary_sha256"] = "4" * 64
        self.assert_refused(value, "runner")

    def test_private_payload_is_refused(self) -> None:
        value = manifest()
        value["groups"][0]["tests"]["command"][0] = "/private/tmp/forge"
        self.assert_refused(value, "private-or-absolute-path")

    def test_path_escape_is_refused(self) -> None:
        with self.assertRaisesRegex(checker.EvidenceError, "path-escape"):
            checker.safe_leaf(checker.ROOT, "../outside")

    def test_current_forge_aggregate_summary_is_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "forge.log"
            path.write_text(
                "Ran 42 test suites in 1.00s: 723 tests passed, 0 failed, 0 skipped\n",
                encoding="utf-8",
            )
            self.assertEqual(checker.parse_log(path), (723, 0, 0))

    def test_legacy_forge_summary_is_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "forge.log"
            path.write_text(
                "Test result: ok. 2 passed; 0 failed; 0 skipped; finished in 1.00ms\n",
                encoding="utf-8",
            )
            self.assertEqual(checker.parse_log(path), (2, 0, 0))

    def test_executed_compiler_profile_passes(self) -> None:
        checker.validate_profile_data(profile_data("v2-a70f297f"), "v2-a70f297f")

    def test_executed_compiler_profile_drift_is_refused(self) -> None:
        value = profile_data("v2-a70f297f")
        value["optimizer_runs"] = 200
        with self.assertRaisesRegex(checker.EvidenceError, "executed-compiler-profile"):
            checker.validate_profile_data(value, "v2-a70f297f")


if __name__ == "__main__":
    unittest.main()
