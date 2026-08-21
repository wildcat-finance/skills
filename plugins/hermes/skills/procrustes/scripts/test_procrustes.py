#!/usr/bin/env python3
"""Hermetic tests for the Procrustes size-baseline harness."""

from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import procrustes  # noqa: E402

FAKE_FORGE = r'''#!/usr/bin/env python3
import json
import sys
from pathlib import Path

repo = Path.cwd()
args = sys.argv[1:]

if args == ["--version"]:
    print("forge Version: procrustes-test")
    raise SystemExit(0)

if args == ["config", "--json"]:
    print(json.dumps({"profile": "default", "optimizer": True, "optimizer_runs": 200}))
    raise SystemExit(0)

if args[:1] == ["build"]:
    if (repo / ".fail-sizes").exists():
        print("build failed", file=sys.stderr)
        raise SystemExit(1)
    if (repo / ".garbage-sizes").exists():
        print("Compiling 1 file with 0.8.28")
        raise SystemExit(0)
    if (repo / ".shapeless-sizes").exists():
        print(json.dumps({"A": {"runtime_size": "297", "init_size": 325}}))
        raise SystemExit(0)
    runtime = 297
    init = 325
    if (repo / ".over-limit").exists():
        runtime = 25000
        init = 25400
    print(json.dumps({"A": {
        "runtime_size": runtime,
        "init_size": init,
        "runtime_margin": 24576 - runtime,
        "init_margin": 49152 - init,
    }}))
    raise SystemExit(0)

if args[:1] == ["test"]:
    if (repo / ".fail-test").exists():
        print("suite failed", file=sys.stderr)
        raise SystemExit(1)
    print("Suite result: ok. 1 passed; 0 failed; 0 skipped")
    raise SystemExit(0)

if args[:1] == ["inspect"]:
    if args[2] == "methodIdentifiers":
        print(json.dumps({"setX(uint256)": "4018d879"}))
        raise SystemExit(0)
    print(json.dumps({
        "storage": [{"astId": 1, "contract": args[1], "label": "x", "offset": 0, "slot": "0", "type": "t_uint256"}],
        "types": {"t_uint256": {"encoding": "inplace", "label": "uint256", "numberOfBytes": "32"}},
    }))
    raise SystemExit(0)

print(f"unsupported fake forge invocation: {args}", file=sys.stderr)
raise SystemExit(64)
'''

SOURCE = """// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.28;

contract A {
    uint256 public x;

    function setX(uint256 v) external {
        require(v < 1000, "too big");
        x = v;
    }
}
"""


class HarnessCase(unittest.TestCase):
    """A temporary Foundry-shaped git repository with a fake forge on PATH."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.repo = root / "target"
        self.evidence = root / "evidence"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "foundry.toml").write_text("[profile.default]\nsrc = 'src'\n", encoding="utf-8")
        (self.repo / "src" / "A.sol").write_text(SOURCE, encoding="utf-8")

        self.bin_dir = root / "bin"
        self.bin_dir.mkdir()
        forge = self.bin_dir / "forge"
        forge.write_text(FAKE_FORGE, encoding="utf-8")
        forge.chmod(0o755)

        for command in (
            ["git", "init", "--quiet"],
            ["git", "config", "user.email", "test@example.com"],
            ["git", "config", "user.name", "Procrustes Test"],
            ["git", "add", "-A"],
            ["git", "commit", "--quiet", "-m", "fixture"],
        ):
            subprocess.run(command, cwd=self.repo, check=True)

        self.environment = dict(os.environ)
        self.environment["PATH"] = f"{self.bin_dir}{os.pathsep}{self.environment['PATH']}"
        self.addCleanup(self.temporary.cleanup)

    def marker(self, name: str) -> None:
        (self.repo / name).write_text("", encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", name], cwd=self.repo, check=True)

    def run_baseline(self, *extra: str, evidence: Path | None = None) -> int:
        argv = [
            "baseline",
            "--repo",
            str(self.repo),
            "--evidence-dir",
            str(evidence if evidence is not None else self.evidence),
            "--size-target",
            "^A$",
            "--assert-no-protected-contracts",
            *extra,
        ]
        with mock.patch.dict(os.environ, self.environment, clear=True):
            return procrustes.main(argv)

    def result(self, evidence: Path | None = None) -> dict:
        path = (evidence if evidence is not None else self.evidence) / "result.json"
        return json.loads(path.read_text(encoding="utf-8"))


class BaselineTests(HarnessCase):
    def test_seals_a_green_baseline_with_measured_sizes(self) -> None:
        self.assertEqual(self.run_baseline(), 0)
        result = self.result()
        self.assertEqual(result["status"], "sealed")
        self.assertEqual(result["over_limit"], [])
        sizes = json.loads((self.evidence / "sizes.json").read_text(encoding="utf-8"))
        self.assertEqual(sizes["sizes"]["A"]["runtime_size"], 297)
        self.assertEqual(sizes["targets"], {"^A$": ["A"]})
        self.assertEqual(sizes["limits"]["eip170_runtime"], 24576)
        self.assertTrue((self.evidence / "baseline-source-manifest.json").is_file())
        self.assertTrue((self.evidence / "logs" / "gate1.forge-test.log").is_file())

    def test_rejects_a_missing_or_unparsable_size_report(self) -> None:
        self.marker(".garbage-sizes")
        self.assertEqual(self.run_baseline(), 10)
        self.assertIn("did not return valid JSON", self.result()["reason"])

    def test_rejects_a_shapeless_size_report(self) -> None:
        self.marker(".shapeless-sizes")
        self.assertEqual(self.run_baseline(), 10)
        self.assertIn("integer runtime_size and init_size", self.result()["reason"])

    def test_rejects_a_failed_size_build(self) -> None:
        self.marker(".fail-sizes")
        self.assertEqual(self.run_baseline(), 10)
        self.assertIn("forge build --sizes --json exited 1", self.result()["reason"])

    def test_rejects_a_dirty_tree(self) -> None:
        (self.repo / "src" / "A.sol").write_text(SOURCE + "\n// edited\n", encoding="utf-8")
        self.assertEqual(self.run_baseline(), 10)
        self.assertIn("uncommitted changes", self.result()["reason"])

    def test_records_initcode_beside_runtime_without_calling_either_the_limit(self) -> None:
        self.assertEqual(self.run_baseline(), 0)
        sizes = json.loads((self.evidence / "sizes.json").read_text(encoding="utf-8"))
        entry = sizes["sizes"]["A"]
        self.assertEqual(entry["init_size"], 325)
        self.assertNotEqual(entry["init_size"], entry["runtime_size"])
        self.assertEqual(entry["runtime_margin"], 24576 - 297)
        self.assertEqual(entry["init_margin"], 49152 - 325)
        self.assertEqual(sizes["limits"]["eip3860_initcode"], 49152)

    def test_rejects_a_size_target_matching_no_contract(self) -> None:
        argv = [
            "baseline",
            "--repo",
            str(self.repo),
            "--evidence-dir",
            str(self.evidence),
            "--size-target",
            "^NoSuchContract$",
            "--assert-no-protected-contracts",
        ]
        with mock.patch.dict(os.environ, self.environment, clear=True):
            self.assertEqual(procrustes.main(argv), 10)
        self.assertIn("matched no compiled contract", self.result()["reason"])

    def test_rejects_an_invalid_size_target_expression(self) -> None:
        argv = [
            "baseline",
            "--repo",
            str(self.repo),
            "--evidence-dir",
            str(self.evidence),
            "--size-target",
            "A(",
            "--assert-no-protected-contracts",
        ]
        with mock.patch.dict(os.environ, self.environment, clear=True):
            self.assertEqual(procrustes.main(argv), 10)
        self.assertIn("invalid --size-target", self.result()["reason"])

    def test_rejects_a_red_behaviour_suite(self) -> None:
        self.marker(".fail-test")
        self.assertEqual(self.run_baseline(), 10)
        self.assertIn("forge test exited 1", self.result()["reason"])

    def test_records_a_contract_over_the_limit_without_refusing_it(self) -> None:
        self.marker(".over-limit")
        self.assertEqual(self.run_baseline(), 0)
        result = self.result()
        self.assertEqual(result["status"], "sealed")
        self.assertEqual(result["over_limit"], ["A"])
        sizes = json.loads((self.evidence / "sizes.json").read_text(encoding="utf-8"))
        self.assertEqual(sizes["over_limit"]["A"]["runtime_size"], 25000)
        self.assertLess(sizes["over_limit"]["A"]["runtime_margin"], 0)

    def test_seals_a_protected_layout_and_selector_set(self) -> None:
        with mock.patch.dict(os.environ, self.environment, clear=True):
            code = procrustes.main([
                "baseline",
                "--repo",
                str(self.repo),
                "--evidence-dir",
                str(self.evidence),
                "--size-target",
                "^A$",
                "--protected-contract",
                "A=src/A.sol:A",
            ])
        self.assertEqual(code, 0)
        self.assertTrue((self.evidence / "storage-layout" / "A.baseline.json").is_file())
        self.assertTrue((self.evidence / "method-identifiers" / "A.baseline.json").is_file())

    def test_requires_a_protected_set_or_an_explicit_denial(self) -> None:
        argv = [
            "baseline",
            "--repo",
            str(self.repo),
            "--evidence-dir",
            str(self.evidence),
            "--size-target",
            "^A$",
        ]
        with mock.patch.dict(os.environ, self.environment, clear=True):
            self.assertEqual(procrustes.main(argv), 10)
        self.assertIn("--protected-contract", self.result()["reason"])

    def test_rejects_an_evidence_directory_inside_the_target(self) -> None:
        inside = self.repo / "evidence"
        with mock.patch.dict(os.environ, self.environment, clear=True):
            self.assertEqual(self.run_baseline(evidence=inside), 10)
        self.assertFalse((inside / "result.json").exists())

    def test_rejects_a_non_empty_evidence_directory(self) -> None:
        self.evidence.mkdir(parents=True)
        (self.evidence / "stray.json").write_text("{}", encoding="utf-8")
        self.assertEqual(self.run_baseline(), 10)

    def test_rejects_a_target_without_a_foundry_root(self) -> None:
        (self.repo / "foundry.toml").unlink()
        subprocess.run(["git", "add", "-A"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "--quiet", "-m", "drop config"], cwd=self.repo, check=True)
        self.assertEqual(self.run_baseline(), 10)

    def test_status_prints_the_recorded_result(self) -> None:
        self.assertEqual(self.run_baseline(), 0)
        with mock.patch.dict(os.environ, self.environment, clear=True):
            self.assertEqual(procrustes.main(["status", "--run-dir", str(self.evidence)]), 0)


class CouplingTests(unittest.TestCase):
    def test_pinned_hermes_surface_matches_the_live_module(self) -> None:
        self.assertEqual(procrustes.pinned_surface_drift(), {})

    def test_every_pinned_name_is_used_by_the_harness(self) -> None:
        source = (SCRIPT_DIR / "procrustes.py").read_text(encoding="utf-8")
        for name in procrustes.PINNED_HERMES_SURFACE:
            with self.subTest(name=name):
                self.assertIn(f"hermes.{name}", source)

    def test_drift_is_detected_when_a_pinned_signature_moves(self) -> None:
        with mock.patch.dict(
            procrustes.PINNED_HERMES_SURFACE, {"utc_now": "(tz: 'str') -> 'str'"}, clear=False
        ):
            self.assertEqual(procrustes.pinned_surface_drift(), {"utc_now": "() -> 'str'"})

    def test_drift_is_detected_when_a_pinned_name_disappears(self) -> None:
        with mock.patch.dict(
            procrustes.PINNED_HERMES_SURFACE, {"never_existed": "() -> 'None'"}, clear=False
        ):
            self.assertEqual(procrustes.pinned_surface_drift(), {"never_existed": "absent"})

    def test_main_refuses_to_run_under_a_moved_surface(self) -> None:
        with mock.patch.object(procrustes, "pinned_surface_drift", return_value={"utc_now": "absent"}):
            self.assertEqual(procrustes.main(["status", "--run-dir", "/nonexistent"]), 70)

    def test_the_limits_are_the_consensus_numbers(self) -> None:
        self.assertEqual(procrustes.EIP170_RUNTIME_LIMIT, 24576)
        self.assertEqual(procrustes.EIP3860_INITCODE_LIMIT, 49152)
        self.assertEqual(procrustes.EIP3860_INITCODE_LIMIT, 2 * procrustes.EIP170_RUNTIME_LIMIT)

    def test_the_harness_names_itself_in_its_records(self) -> None:
        self.assertEqual(procrustes.SKILL_NAME, "procrustes")
        self.assertEqual(procrustes.SCHEMA, "procrustes-run/v1")
        self.assertNotEqual(procrustes.SCHEMA, procrustes.hermes.SCHEMA)

    def test_the_pinned_map_carries_signatures_rather_than_names(self) -> None:
        for name, signature in procrustes.PINNED_HERMES_SURFACE.items():
            with self.subTest(name=name):
                self.assertTrue(signature.startswith("("), signature)
                self.assertEqual(
                    signature, str(inspect.signature(getattr(procrustes.hermes, name)))
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)
