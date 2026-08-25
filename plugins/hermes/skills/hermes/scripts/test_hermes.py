#!/usr/bin/env python3
"""Hermetic tests for the Hermes verification harness."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any, Sequence
from unittest import mock


SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
import hermes  # noqa: E402


FAKE_FORGE = r'''#!/usr/bin/env python3
import json
import sys
from pathlib import Path

repo = Path.cwd()
args = sys.argv[1:]

def read_int(name, default):
    path = repo / name
    return int(path.read_text().strip()) if path.exists() else default

if args == ["--version"]:
    print("forge Version: hermes-test")
    raise SystemExit(0)

if args == ["config", "--json"]:
    config = {"profile": "default", "optimizer": True, "optimizer_runs": 200,
              "solc": "0.8.25", "evm_version": "cancun", "via_ir": False}
    import os
    override = os.environ.get("HERMES_TEST_CONFIG_OVERRIDE")
    if override and Path(override).exists():
        config.update(json.loads(Path(override).read_text()))
    print(json.dumps(config))
    raise SystemExit(0)

if args and args[0] == "snapshot":
    baseline = read_int(".baseline-gas", 100)
    candidate = read_int(".candidate-gas", baseline)
    if "--diff" in args:
        arrow = "↓" if candidate < baseline else ("↑" if candidate > baseline else "━")
        delta = candidate - baseline
        percentage = (delta / baseline) * 100
        print(f"{arrow} CTest::testGas_target() (gas: {baseline} → {candidate} | {delta:+d} {percentage:+.3f}%)")
        print(f"Total tests: 1, ↑ {int(delta > 0)}, ↓ {int(delta < 0)}, ━ {int(delta == 0)}")
        raise SystemExit(0)
    if "--snap" in args:
        output = Path(args[args.index("--snap") + 1])
        gas = candidate
    else:
        output = repo / ".gas-snapshot"
        gas = baseline
    output.parent.mkdir(parents=True, exist_ok=True)
    snapshot = f"CTest:testGas_target() (gas: {gas})\n"
    if (repo / ".include-invariant").exists():
        calls = read_int(".candidate-invariant-calls", 60000) if (repo / ".candidate-gas").exists() else 60000
        snapshot += f"InvariantTest:invariant_callSummary() (runs: 2000, calls: {calls}, reverts: 0)\n"
    if (repo / ".include-fuzz").exists():
        mean = read_int(".candidate-fuzz-mean", 120)
        runs = read_int(".candidate-fuzz-runs", 1000)
        snapshot += f"CTest:testFuzz_stat(uint256) (runs: {runs}, μ: {mean}, ~: 115)\n"
    output.write_text(snapshot)
    print("snapshot ok")
    raise SystemExit(0)

if args and args[0] == "test":
    if "--gas-report" in args and (repo / ".fail-gas-report").exists():
        print("gas report failed", file=sys.stderr)
        raise SystemExit(1)
    if "--match-path" in args and (repo / ".fail-targeted").exists():
        print("targeted property failed", file=sys.stderr)
        raise SystemExit(1)
    if "--gas-report" not in args and "--match-path" not in args and (repo / ".fail-full-test").exists():
        print("full suite failed", file=sys.stderr)
        raise SystemExit(1)
    print("Suite result: ok. 1 passed; 0 failed; 0 skipped")
    raise SystemExit(0)

if args and args[0] == "inspect":
    if args[2] == "methodIdentifiers":
        print(json.dumps({"read()": "57de26a4", "value()": "3fa4f245"}))
        raise SystemExit(0)
    slot = read_int(".layout-slot", 0)
    ast_id = read_int(".layout-ast-id", 1)
    type_ast_id = read_int(".layout-type-ast-id", 1234)
    type_name = f"t_contract(Token){type_ast_id}"
    print(json.dumps({"storage": [{"astId": ast_id, "contract": args[1], "label": "value", "offset": 0, "slot": str(slot), "type": type_name}], "types": {type_name: {"encoding": "inplace", "label": "contract Token", "numberOfBytes": "20"}}}))
    raise SystemExit(0)

print(f"unsupported fake forge invocation: {args}", file=sys.stderr)
raise SystemExit(64)
'''


SOURCE_BASELINE = """// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.25;

contract C {
    uint256 public value;

    function read() external view returns (uint256) {
        return value;
    }
}
"""


SOURCE_CACHED = """// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.25;

contract C {
    uint256 public value;

    function read() external view returns (uint256 result) {
        result = value;
    }
}
"""


SOURCE_UNCHECKED = """// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.25;

contract C {
    uint256 public value;

    function read() external view returns (uint256 result) {
        unchecked { result = value + 1; }
    }
}
"""


class HarnessFixture:
    """The hermetic repository, fake Forge and baseline every gate case needs.

    Deliberately not a TestCase: a fixture that is one gets collected, and a
    subclass then re-runs every case it inherited under whatever the subclass
    overrode. That is how this file briefly ran its fourteen harness cases
    twice, the second time through a `verify` the subclass had changed.
    """

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="hermes-tests-")
        self.root = Path(self.temporary.name)
        self.repo = self.root / "repo"
        self.run_dir = self.root / "evidence"
        self.bin_dir = self.root / "bin"
        (self.repo / "src").mkdir(parents=True)
        (self.repo / "test").mkdir()
        self.bin_dir.mkdir()
        (self.repo / "foundry.toml").write_text("[profile.default]\noptimizer = true\n")
        (self.repo / "src" / "C.sol").write_text(SOURCE_BASELINE)
        (self.repo / "test" / "C.t.sol").write_text(
            "// SPDX-License-Identifier: UNLICENSED\npragma solidity ^0.8.25;\ncontract CTest { function testGas_target() public {} }\n"
        )
        forge = self.bin_dir / "forge"
        forge.write_text(FAKE_FORGE)
        forge.chmod(0o755)
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(
            ["git", "config", "--local", "commit.gpgsign", "false"],
            cwd=self.repo,
            check=True,
        )
        subprocess.run(["git", "config", "user.name", "Hermes Tests"], cwd=self.repo, check=True)
        subprocess.run(["git", "config", "user.email", "hermes@example.invalid"], cwd=self.repo, check=True)
        subprocess.run(["git", "add", "foundry.toml", "src/C.sol", "test/C.t.sol"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "baseline"], cwd=self.repo, check=True)
        self.environment = os.environ.copy()
        self.environment["PATH"] = f"{self.bin_dir}{os.pathsep}{self.environment['PATH']}"
        self.path_patch = mock.patch.dict(os.environ, self.environment, clear=True)
        self.path_patch.start()

    def tearDown(self) -> None:
        self.path_patch.stop()
        self.temporary.cleanup()

    def baseline(self, protected: bool = True) -> None:
        contract_args = (
            ["--protected-contract", "C=src/C.sol:C"]
            if protected
            else ["--assert-no-protected-contracts", "--layout-contract", "C=src/C.sol:C"]
        )
        code = hermes.main(
            [
                "baseline",
                "--repo",
                str(self.repo),
                "--evidence-dir",
                str(self.run_dir),
                "--fuzz-seed",
                "0x5EED",
                *contract_args,
            ]
        )
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.run_dir / "state.json").read_text())["status"], "baseline_ready")

    # One rule per class the cases use, with an answer for each obligation the
    # rule's own statement makes. STO-09 states one, CTL-05 states two.
    RULES = {
        "storage-load-caching": ("STO-09", [
            "1=The cache lives inside the one function and dies with the call frame.",
        ]),
        "unchecked-arithmetic": ("CTL-05", [
            "1=Every intermediate is bounded by the array length, proved at the loop head.",
            "2=The unchecked region is three lines and the bound is stated beside it.",
        ]),
        "constants-immutables": ("STO-15", []),
        "storage-packing": ("STO-01", []),
    }

    def override_config(self, **fields: Any) -> None:
        """Point the fake Forge at a configuration written outside the
        repository, so Gate 1 still sees a clean tree."""
        path = self.root / "forge-config-override.json"
        path.write_text(json.dumps(fields))
        os.environ["HERMES_TEST_CONFIG_OVERRIDE"] = str(path)
        self.addCleanup(os.environ.pop, "HERMES_TEST_CONFIG_OVERRIDE", None)

    def verify(self, *extra: str, optimisation_class: str = "storage-load-caching",
               rule: str | None = None, obligations: Sequence[str] | None = None) -> int:
        default_rule, default_obligations = self.RULES[optimisation_class]
        answers = default_obligations if obligations is None else obligations
        return hermes.main(
            [
                "verify",
                "--run-dir",
                str(self.run_dir),
                "--optimisation-class",
                optimisation_class,
                "--attest-single-class",
                "--rule",
                rule or default_rule,
                *[argument for answer in answers for argument in ("--obligation", answer)],
                "--gas-target",
                "testGas_target",
                *extra,
            ]
        )

    def prepare_candidate(self, source: str = SOURCE_CACHED, gas: int = 90) -> None:
        (self.repo / "src" / "C.sol").write_text(source)
        (self.repo / ".candidate-gas").write_text(str(gas))


class HermesHarnessTests(HarnessFixture, unittest.TestCase):
    def test_accepts_and_promotes_a_fully_verified_candidate(self) -> None:
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["status"], "accepted")
        self.assertEqual([gate["id"] for gate in result["gates"]], [1, 2, 3, 4, 5, 6])
        self.assertEqual(result["storage_layouts"][0]["status"], "identical")
        self.assertEqual(result["method_identifiers"][0]["status"], "identical")
        self.assertEqual(hermes.main(["promote", "--run-dir", str(self.run_dir)]), 0)
        self.assertIn("(gas: 90)", (self.repo / ".gas-snapshot").read_text())

    def test_rejects_any_gas_regression_at_gate_three(self) -> None:
        self.baseline()
        self.prepare_candidate(gas=101)
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 30)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 3)
        self.assertIn("gas regression", result["reason"])

    def test_accepts_unchanged_invariant_snapshot_rows(self) -> None:
        (self.repo / ".include-invariant").write_text("1")
        subprocess.run(["git", "add", ".include-invariant"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable invariant snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        comparison = json.loads((self.run_dir / "gas-comparison.json").read_text())
        self.assertEqual(
            comparison["invariants"],
            [
                {
                    "calls": 60000,
                    "measurement": "InvariantTest:invariant_callSummary()",
                    "reverts": 0,
                    "runs": 2000,
                    "status": "identical",
                }
            ],
        )

    def test_rejects_changed_invariant_snapshot_rows(self) -> None:
        (self.repo / ".include-invariant").write_text("1")
        subprocess.run(["git", "add", ".include-invariant"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable invariant snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".candidate-invariant-calls").write_text("59999")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 30)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 3)
        self.assertIn("invariant snapshot changed", result["reason"])

    def test_accepts_fuzz_statistic_snapshot_rows(self) -> None:
        (self.repo / ".include-fuzz").write_text("1")
        subprocess.run(["git", "add", ".include-fuzz"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable fuzz snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        comparison = json.loads((self.run_dir / "gas-comparison.json").read_text())
        self.assertEqual(comparison["fuzz_statistics"][0]["runs"], 1000)
        self.assertEqual(comparison["fuzz_statistics"][0]["status"], "informational_not_comparable")

    def test_records_changed_fuzz_statistics_without_calling_them_a_regression(self) -> None:
        (self.repo / ".include-fuzz").write_text("1")
        subprocess.run(["git", "add", ".include-fuzz"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable fuzz snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".candidate-fuzz-mean").write_text("121")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        comparison = json.loads((self.run_dir / "gas-comparison.json").read_text())
        self.assertEqual(comparison["fuzz_statistics"][0]["mean_delta"], 1)

    def test_rejects_changed_fuzz_run_count(self) -> None:
        (self.repo / ".include-fuzz").write_text("1")
        subprocess.run(["git", "add", ".include-fuzz"], cwd=self.repo, check=True)
        subprocess.run(["git", "commit", "-qm", "enable fuzz snapshot"], cwd=self.repo, check=True)
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".candidate-fuzz-runs").write_text("999")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 30)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertIn("fuzz snapshot run count changed", result["reason"])

    def test_rejects_full_suite_failure_at_gate_four(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".fail-full-test").write_text("1")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 40)
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 4)

    def test_hard_aborts_on_protected_layout_change(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".layout-slot").write_text("1")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 50)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["failed_gate"], 5)
        self.assertIn("storage layout changed", result["reason"])

    def test_accepts_compiler_ast_id_only_layout_difference(self) -> None:
        self.baseline()
        self.prepare_candidate()
        (self.repo / ".layout-ast-id").write_text("99")
        (self.repo / ".layout-type-ast-id").write_text("5678")
        self.assertEqual(self.verify("--no-sensitive-unchecked"), 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["storage_layouts"][0]["status"], "identical")
        before_raw = self.run_dir / "storage-layout" / "C.before.raw.json"
        after_raw = self.run_dir / "storage-layout" / "C.after.raw.json"
        self.assertNotEqual(before_raw.read_bytes(), after_raw.read_bytes())

    def test_records_declared_layout_change_on_non_frozen_contract(self) -> None:
        self.baseline(protected=False)
        self.prepare_candidate()
        (self.repo / ".layout-slot").write_text("1")
        code = self.verify(
            "--no-sensitive-unchecked",
            "--allow-unprotected-layout-change",
            "--layout-change-rationale",
            "No proxy, hook, role provider, delegate call, factory deployment, or indexer reads this layout.",
            optimisation_class="storage-packing",
        )
        self.assertEqual(code, 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertEqual(result["storage_layouts"][0]["status"], "changed_permitted")

    def test_rejects_unchecked_hidden_inside_another_class(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        self.assertEqual(
            self.verify(
                "--no-sensitive-unchecked",
                "--non-sensitive-rationale",
                "This arithmetic cannot affect persistent state, asset balances, or external call parameters.",
            ),
            20,
        )
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 2)

    def test_requires_and_runs_targeted_sensitive_property_test(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        code = self.verify(
            "--sensitive-unchecked",
            "--targeted-match-path",
            "test/C.t.sol",
            "--targeted-match-test",
            "testFuzz_stateDifferential",
            "--property-proof",
            "Compare checked and unchecked state transitions across the complete bounded input domain.",
            optimisation_class="unchecked-arithmetic",
        )
        self.assertEqual(code, 0)
        result = json.loads((self.run_dir / "result.json").read_text())
        self.assertTrue(result["sensitive_unchecked"]["applicable"])
        self.assertEqual(result["sensitive_unchecked"]["status"], "passed")

    def test_targeted_sensitive_property_failure_rejects_gate_six(self) -> None:
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        (self.repo / ".fail-targeted").write_text("1")
        code = self.verify(
            "--sensitive-unchecked",
            "--targeted-match-path",
            "test/C.t.sol",
            "--targeted-match-test",
            "testFuzz_stateDifferential",
            "--property-proof",
            "Compare checked and unchecked state transitions across the complete bounded input domain.",
            optimisation_class="unchecked-arithmetic",
        )
        self.assertEqual(code, 60)
        self.assertEqual(json.loads((self.run_dir / "result.json").read_text())["failed_gate"], 6)


class CorpusValidationTests(unittest.TestCase):
    """The corpus is what judges a candidate, so a corpus that cannot be
    trusted has to refuse rather than pass a candidate under advice nobody
    checked. Each case here mutates one field of the shipped corpus in a
    temporary directory; nothing writes into the skill's own references."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="hermes-corpus-")
        self.directory = Path(self.temporary.name)
        self.addCleanup(self.temporary.cleanup)
        self.shipped, self.schema_path = hermes.corpus_paths()
        shutil.copy(self.shipped, self.directory / self.shipped.name)
        shutil.copy(self.schema_path, self.directory / self.schema_path.name)

    def load(self) -> tuple[dict, dict]:
        corpus, schema, _ = hermes.load_corpus(self.directory)
        return corpus, schema

    def faults(self, mutate) -> list[str]:
        corpus, schema = self.load()
        mutate(corpus, schema)
        return hermes.validate_corpus(corpus, schema)

    def test_the_shipped_corpus_validates(self) -> None:
        corpus, schema = self.load()
        self.assertEqual(hermes.validate_corpus(corpus, schema), [])

    def test_the_shipped_corpus_carries_the_source_counts(self) -> None:
        corpus, _ = self.load()
        self.assertEqual(len(corpus["myths"]), 28)
        self.assertEqual(len(corpus["references"]), 40)
        self.assertEqual(corpus["source"]["sha256"],
                         "297c926dc0a2e011e31da5245273c136273b8faa390f3691910c22c870068449")

    def test_every_citation_id_resolves_exactly_once(self) -> None:
        """REF-25 appears in the source at the start of a line as a citation
        and again as a footnote definition, which is the shape that turns one
        reference into two during transcription."""
        corpus, _ = self.load()
        identifiers = [entry["id"] for entry in corpus["references"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        self.assertEqual(identifiers.count("REF-25"), 1)

    def test_a_duplicate_record_id_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"].append(dict(corpus["myths"][0]))
        self.assertIn("duplicate id", " ".join(self.faults(mutate)))

    def test_an_unknown_field_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["severity"] = "high"
        self.assertIn("unknown field 'severity'", " ".join(self.faults(mutate)))

    def test_a_missing_field_is_refused(self) -> None:
        def mutate(corpus, _schema):
            del corpus["myths"][0]["correction"]
        self.assertIn("missing field 'correction'", " ".join(self.faults(mutate)))

    def test_an_empty_correction_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["correction"] = "   "
        self.assertIn("expected non-empty text", " ".join(self.faults(mutate)))

    def test_a_citation_that_no_reference_defines_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["references"] = ["REF-99"]
        self.assertIn("cites 'REF-99'", " ".join(self.faults(mutate)))

    def test_a_malformed_source_digest_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["source"]["sha256"] = "297C926D"
        self.assertIn("expected a lowercase sha256 digest", " ".join(self.faults(mutate)))

    def test_a_wrong_schema_declaration_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["schema"] = "hermes/gas-rule-corpus/v2"
        faults = self.faults(mutate)
        self.assertEqual(len(faults), 1, faults)
        self.assertIn("expected 'hermes/gas-rule-corpus/v1'", faults[0])

    def test_an_id_outside_its_pattern_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["myths"][0]["id"] = "MYTH-1"
        self.assertIn("does not match", " ".join(self.faults(mutate)))

    def test_a_type_token_this_build_cannot_check_is_a_fault(self) -> None:
        """A schema that grew a token the validator does not implement must
        fail loudly. The alternative is a field nobody checks and no sign of
        it."""
        def mutate(_corpus, schema):
            schema["records"]["myths"]["required"]["claim"] = "sonnet"
        self.assertIn("cannot check", " ".join(self.faults(mutate)))

    def test_a_rule_class_outside_the_twelve_is_refused(self) -> None:
        def mutate(corpus, _schema):
            corpus["rules"].append(_rule_record(hermes_class="storage-golf"))
        self.assertIn("neither null nor a Hermes class", " ".join(self.faults(mutate)))

    def test_a_rule_scope_naming_an_unknown_fork_is_refused(self) -> None:
        def mutate(corpus, _schema):
            record = _rule_record()
            record["scope"]["evm_floor"] = "verkle"
            corpus["rules"].append(record)
        self.assertIn("is not a name in fork_order", " ".join(self.faults(mutate)))

    def test_a_fully_formed_rule_record_validates(self) -> None:
        """The rule shape steps three and four fill in, proved against the
        schema before any of those records exist."""
        def mutate(corpus, _schema):
            corpus["rules"].append(_rule_record())
        self.assertEqual(self.faults(mutate), [])

    def test_a_schema_class_the_header_does_not_name_is_still_a_record_class(self) -> None:
        """Round 1 finding: the header check named the three record classes
        itself, so a schema that grew a fourth reported it as an unknown
        top-level field instead of validating it."""
        def mutate(corpus, schema):
            schema["records"]["gates"] = {
                "id_pattern": "^GATE-[0-9]{2}$",
                "required": {"id": "id", "title": "text"},
                "optional": {},
            }
            corpus["gates"] = [{"id": "GATE-01", "title": "pin the build"}]
        self.assertEqual(self.faults(mutate), [])

    def test_the_command_reports_clean_and_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "hermes.py"), "corpus", "--validate", "--json"],
            capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["status"], "clean")
        self.assertEqual(summary["counts"]["myths"], 28)
        self.assertEqual(summary["counts"]["references"], 40)
        self.assertEqual(summary["faults"], [])

    def test_the_command_refuses_without_validate(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT_DIR / "hermes.py"), "corpus"],
            capture_output=True, text=True, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--validate", result.stderr)


def _rule_record(**overrides) -> dict:
    """A rule record in the shape the schema declares.

    `STO-99` deliberately matches the id pattern without naming a rule the
    corpus holds, so appending it does not collide with real data.
    """
    statement = ("load storage once when no mutation or callback can invalidate "
                 "the value. keep the cache's lifetime narrow.")
    record = {
        "id": "STO-99",
        "title": "cache repeated storage reads",
        "kind": "technique",
        "category": "state-model-and-storage",
        "priority": "P1",
        "evidence_grade": "A",
        "automation": "safe",
        "hermes_class": "storage-load-caching",
        "statement": statement,
        "obligations": ["keep the cache's lifetime narrow."],
        "references": ["REF-10"],
        "source_section": "5",
        "verified_on": {"compiler": "0.8.25", "evm": "cancun"},
        "scope": {
            "compiler_min": "0.8.0",
            "compiler_max_exclusive": "0.9.0",
            "compiler_reason": "SLOAD pricing is an EVM property, not a compiler one.",
            "evm_floor": "berlin",
            "evm_reason": "EIP-2929 introduced the warm and cold distinction the saving rests on.",
            "pipelines": ["legacy", "via-ir"],
            "pipeline_reason": "Neither pipeline removes a repeated storage read.",
        },
    }
    record.update(overrides)
    return record



class CorpusGateTests(HarnessFixture, unittest.TestCase):
    """Gate 2 refuses seven ways before Gate 3 spends a Forge run.

    Inherits the harness fixture: same fake Forge, same baseline, same
    candidate. Each case asserts the exit code, the failed gate and the
    machine-readable refusal reason, because the exit code names the gate and
    the reason names the condition.
    """

    def refusal(self) -> dict:
        return json.loads((self.run_dir / "result.json").read_text())

    def verify(self, *extra: str, **kwargs) -> int:  # type: ignore[override]
        """Every case here is an ordinary candidate unless it says otherwise,
        so the classification flag the parser demands is supplied once."""
        if not any(argument.endswith("sensitive-unchecked") for argument in extra):
            extra = ("--no-sensitive-unchecked", *extra)
        return super().verify(*extra, **kwargs)

    def assert_refused(self, code: int, reason: str) -> dict:
        self.assertEqual(code, 20)
        result = self.refusal()
        self.assertEqual(result["failed_gate"], 2)
        self.assertEqual(result["refusal"], reason)
        return result

    def test_an_unknown_rule_id_is_refused(self) -> None:
        self.baseline()
        self.prepare_candidate()
        self.assert_refused(self.verify(rule="STO-99"), "corpus/unknown-rule")

    def test_a_rejected_universal_rule_cannot_be_selected(self) -> None:
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(self.verify(rule="MYTH-02"), "corpus/myth-selected")
        self.assertIn("canonical loops are automatically handled", result["reason"])

    def test_a_rule_naming_no_class_is_refused(self) -> None:
        """58 of the 120 rules are advice the record carries, not candidates."""
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(self.verify(rule="CMP-01"), "corpus/rule-names-no-class")
        self.assertIn("not a candidate", result["reason"])

    def test_a_class_disagreement_is_refused(self) -> None:
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(
            self.verify(rule="STO-15", obligations=[]), "corpus/class-disagreement")
        self.assertIn("constants-immutables", result["reason"])

    def test_a_myth_cited_as_justification_is_refused(self) -> None:
        """Naming a rejected rule as the reason a candidate is sound is
        refused with the correction quoted back."""
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        code = self.verify(
            "--no-sensitive-unchecked",
            "--non-sensitive-rationale",
            "Safe by MYTH-28: ordinary unit tests cover the unchecked block.",
            optimisation_class="unchecked-arithmetic",
        )
        result = self.assert_refused(code, "corpus/myth-cited")
        self.assertIn("every intermediate bound needs a durable proof", result["reason"])

    def test_an_unanswered_obligation_is_refused(self) -> None:
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(
            self.verify(obligations=[]), "corpus/obligation-unanswered")
        self.assertIn("keep the cache", result["reason"])

    def test_a_blank_obligation_answer_is_refused(self) -> None:
        self.baseline()
        self.prepare_candidate()
        self.assert_refused(self.verify(obligations=["1=    "]),
                            "corpus/obligation-unanswered")

    def test_an_obligation_index_the_rule_does_not_have_is_refused(self) -> None:
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(
            self.verify(obligations=["1=The cache lives inside one call frame and dies with it.",
                                     "2=There is no second obligation to answer here."]),
            "corpus/obligation-malformed")
        self.assertIn("there is no obligation 2", result["reason"])

    def test_a_malformed_obligation_answer_is_refused(self) -> None:
        self.baseline()
        self.prepare_candidate()
        self.assert_refused(self.verify(obligations=["no index here at all, just prose"]),
                            "corpus/obligation-malformed")

    def test_an_unpinned_solc_refuses_rather_than_assuming_one(self) -> None:
        """The failure the source document sets up: its header pins 0.8.25, and
        a target that pins nothing at all must not be read as matching it."""
        self.override_config(solc=None)
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(self.verify(), "corpus/scope-unresolved")
        self.assertIn("does not pin a readable solc", result["reason"])
        self.assertIn("foundry.toml", result["reason"])

    def test_a_fork_below_the_rules_floor_is_refused(self) -> None:
        """Istanbul, not Paris: Paris is later than Berlin in the order and so
        satisfies STO-09's floor. Reaching for the newest-sounding name is how
        a scope check gets a passing test that proves nothing."""
        self.override_config(evm_version="istanbul")
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(self.verify(), "corpus/out-of-scope")
        self.assertIn("needs berlin or later", result["reason"])
        self.assertIn("EIP-2929", result["reason"])

    def test_a_fork_above_the_floor_is_in_scope(self) -> None:
        """Ordering, not string equality. The source was written against
        Cancun and the Foundry build in this checkout defaults to Osaka, so an
        equality check would refuse every correct candidate."""
        self.override_config(evm_version="osaka")
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify(), 0)
        self.assertEqual(self.refusal()["status"], "accepted")

    def test_an_unknown_fork_name_refuses(self) -> None:
        self.override_config(evm_version="verkle")
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(self.verify(), "corpus/scope-unresolved")
        self.assertIn("not a fork this corpus orders", result["reason"])

    def test_a_compiler_outside_the_rules_range_is_refused(self) -> None:
        self.override_config(solc="0.7.6")
        self.baseline()
        self.prepare_candidate()
        result = self.assert_refused(self.verify(), "corpus/out-of-scope")
        self.assertIn("0.7.6", result["reason"])

    def test_a_pipeline_outside_the_rules_set_is_refused(self) -> None:
        """No rule in the corpus is single-pipeline today, so this drives the
        check through a rule whose scope is narrowed in place."""
        self.baseline()
        self.prepare_candidate()
        self.assertTrue((self.run_dir / "baseline.gas-rule-corpus.json").is_file())
        corpus, schema, _digest = hermes.load_corpus()
        for rule in corpus["rules"]:
            if rule["id"] == "STO-09":
                rule["scope"]["pipelines"] = ["via-ir"]
        state = json.loads((self.run_dir / "state.json").read_text())
        with mock.patch.object(
            hermes, "load_corpus",
            return_value=(corpus, schema, state["baseline"]["corpus_sha256"]),
        ):
            result = self.assert_refused(self.verify(), "corpus/out-of-scope")
        self.assertIn("legacy", result["reason"])

    def test_a_corpus_edited_after_the_baseline_is_refused(self) -> None:
        self.baseline()
        self.prepare_candidate()
        corpus, schema, _digest = hermes.load_corpus()
        with mock.patch.object(hermes, "load_corpus",
                               return_value=(corpus, schema, "0" * 64)):
            result = self.assert_refused(self.verify(), "corpus/digest-moved")
        self.assertIn("changed after the baseline", result["reason"])

    def test_verify_without_a_rule_is_refused_by_the_parser(self) -> None:
        self.baseline()
        self.prepare_candidate()
        with self.assertRaises(SystemExit) as raised:
            hermes.main(["verify", "--run-dir", str(self.run_dir),
                         "--optimisation-class", "storage-load-caching",
                         "--attest-single-class", "--gas-target", "testGas_target"])
        self.assertNotEqual(raised.exception.code, 0)

    def test_a_baseline_sealed_before_the_corpus_gate_refuses(self) -> None:
        """Round 1 finding: a run directory from the previous Hermes carries
        neither the corpus digest nor the sealed configuration, and reading a
        missing key is a traceback rather than a refusal."""
        self.baseline()
        self.prepare_candidate()
        state_path = self.run_dir / "state.json"
        state = json.loads(state_path.read_text())
        del state["baseline"]["corpus_sha256"]
        state_path.write_text(json.dumps(state))
        result = self.assert_refused(self.verify(), "corpus/baseline-predates-corpus")
        self.assertIn("take a fresh baseline", result["reason"])

    def test_a_floor_the_corpus_does_not_order_is_a_refusal_not_a_traceback(self) -> None:
        """Round 1 finding: `resolve_scope` indexed `fork_order` for the rule's
        floor without checking it was there, so a corpus fault escaped as a
        ValueError instead of a refusal with an exit code.

        Driven directly rather than through `verify`, because `validate_corpus`
        runs first and catches the same corpus with its own message. The guard
        is at the function boundary and that is where it is proved.
        """
        corpus, _schema, _digest = hermes.load_corpus()
        corpus["fork_order"] = ["homestead", "cancun"]
        rule = next(r for r in corpus["rules"] if r["id"] == "STO-09")
        with self.assertRaises(hermes.CorpusRefusal) as raised:
            hermes.resolve_scope(rule, corpus,
                                 {"solc": "0.8.25", "evm_version": "cancun", "via_ir": False})
        self.assertEqual(raised.exception.reason, "corpus/invalid")
        self.assertIn("does not order", str(raised.exception))

    def test_a_lowercased_myth_citation_is_still_refused(self) -> None:
        """Round 1 finding: the citation scan was case-sensitive, so the same
        citation written in lower case went unnoticed."""
        self.baseline()
        self.prepare_candidate(source=SOURCE_UNCHECKED)
        code = self.verify(
            "--no-sensitive-unchecked",
            "--non-sensitive-rationale",
            "This is safe for the reason given in myth-28 about unit tests.",
            optimisation_class="unchecked-arithmetic",
        )
        result = self.assert_refused(code, "corpus/myth-cited")
        self.assertIn("myth-28 (MYTH-28)", result["reason"])
        self.assertIn("every intermediate bound needs a durable proof", result["reason"])

    def test_an_accepted_candidate_records_the_corpus_that_judged_it(self) -> None:
        self.baseline()
        self.prepare_candidate()
        self.assertEqual(self.verify(), 0)
        result = self.refusal()
        self.assertEqual(result["status"], "accepted")
        rule = result["rule"]
        self.assertEqual(rule["id"], "STO-09")
        self.assertEqual(rule["evidence_grade"], "A")
        self.assertEqual(rule["automation"], "safe")
        self.assertEqual(len(rule["corpus_sha256"]), 64)
        self.assertEqual(rule["scope_resolution"],
                         {"solc": "0.8.25", "evm_version": "cancun", "pipeline": "legacy"})
        self.assertEqual(len(rule["obligations"]), 1)
        self.assertEqual(rule["obligations"][0]["kind"], "recorded judgement")
        self.assertIn("one function", rule["obligations"][0]["answer"])

    def test_the_baseline_seals_the_corpus_beside_the_configuration(self) -> None:
        self.baseline()
        state = json.loads((self.run_dir / "state.json").read_text())
        _corpus, _schema, digest = hermes.load_corpus()
        self.assertEqual(state["baseline"]["corpus_sha256"], digest)
        self.assertEqual(state["baseline"]["forge_config"],
                         {"solc": "0.8.25", "evm_version": "cancun", "via_ir": False})
        sealed = self.run_dir / "baseline.gas-rule-corpus.json"
        self.assertIn(str(sealed.relative_to(self.run_dir)),
                      state["baseline"]["artifact_hashes"])


def _repository_root() -> Path:
    """The checkout this skill ships from, or None when it ships alone.

    The source document lives under the repository's `docs/`, which a plugin
    install does not carry, so the fidelity checks below skip rather than fail
    outside the source tree.
    """
    for candidate in [SCRIPT_DIR, *SCRIPT_DIR.parents]:
        if (candidate / ".git").exists():
            return candidate
    return None


class CorpusFidelityTests(unittest.TestCase):
    """The transcribed fields have to be the source's words, not a paraphrase
    that drifted. Structure is the shipped validator's job; equality with the
    pinned document is this repository's."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.root = _repository_root()
        if cls.root is None:
            raise unittest.SkipTest("not running from the source checkout")
        cls.corpus, _schema, _digest = hermes.load_corpus()
        source = cls.root / cls.corpus["source"]["path"]
        if not source.is_file():
            raise unittest.SkipTest(f"pinned source not in this tree: {source}")
        cls.source_text = source.read_text(encoding="utf-8")
        cls.source_bytes = source.read_bytes()

    def test_the_pinned_source_matches_its_recorded_digest(self) -> None:
        self.assertEqual(hermes.sha256_bytes(self.source_bytes),
                         self.corpus["source"]["sha256"])

    def source_rules(self) -> dict:
        pattern = re.compile(
            r"(?m)^### (?P<id>(?:CMP|STO|TRN|MEM|CTL|EXT|DEP|YUL)-\d{2}) — (?P<title>.+?)\n+"
            r"\*\*(?P<priority>P\d) · (?P<grade>[ABCX]) · (?P<automation>safe|guarded|never)\*\*\n"
            r"(?P<body>.*?)(?=\n#{2,3} |\Z)", re.S)
        found = {}
        for match in pattern.finditer(self.source_text):
            body = re.sub(r"\[\^REF-\d{2}\]", "", match.group("body"))
            found[match.group("id")] = {
                "title": match.group("title").strip(),
                "priority": match.group("priority"),
                "evidence_grade": match.group("grade"),
                "automation": match.group("automation"),
                "statement": " ".join(body.split()),
                "references": sorted(set(re.findall(r"\[\^(REF-\d{2})\]", match.group("body")))),
            }
        return found

    def test_the_source_states_one_hundred_and_twenty_rules(self) -> None:
        self.assertEqual(len(self.source_rules()), 120)

    def test_every_transcribed_field_matches_the_source(self) -> None:
        source = self.source_rules()
        for rule in self.corpus["rules"]:
            with self.subTest(rule=rule["id"]):
                self.assertIn(rule["id"], source)
                expected = source[rule["id"]]
                for field in ("title", "priority", "evidence_grade",
                              "automation", "statement", "references"):
                    self.assertEqual(rule[field], expected[field], field)

    def test_every_obligation_is_a_substring_of_its_own_statement(self) -> None:
        for rule in self.corpus["rules"]:
            for obligation in rule["obligations"]:
                with self.subTest(rule=rule["id"], obligation=obligation[:40]):
                    self.assertIn(obligation, rule["statement"])

    def test_the_corpus_holds_every_rule_the_source_states(self) -> None:
        counts = {}
        for rule in self.corpus["rules"]:
            prefix = rule["id"].split("-")[0]
            counts[prefix] = counts.get(prefix, 0) + 1
        self.assertEqual(counts, {"CMP": 12, "STO": 27, "TRN": 7, "MEM": 16,
                                  "CTL": 18, "EXT": 14, "DEP": 12, "YUL": 14})
        self.assertEqual(len(self.corpus["rules"]), 120)
        self.assertEqual(sorted(r["id"] for r in self.corpus["rules"]),
                         sorted(self.source_rules()))

    def test_the_catalogue_index_agrees_with_the_corpus(self) -> None:
        """The catalogue tells a reader which rules name which class, and prose
        that states a mapping without deriving it drifts the moment the corpus
        moves. This regenerates the block and requires the committed bytes."""
        catalogue = (self.root / "plugins" / "hermes" / "skills" / "hermes"
                     / "references" / "optimisation-catalogue.md")
        if not catalogue.is_file():
            self.skipTest("catalogue not in this tree")
        text = catalogue.read_text(encoding="utf-8")
        start = text.index("<!-- corpus-index:start -->")
        end = text.index("<!-- corpus-index:end -->") + len("<!-- corpus-index:end -->")
        committed = text[start:end]

        by_class: dict[str, list[str]] = {}
        for rule in self.corpus["rules"]:
            by_class.setdefault(rule["hermes_class"] or "", []).append(rule["id"])
        unclassed = by_class.pop("", [])
        lines = ["<!-- corpus-index:start -->"]
        for name in hermes.OPTIMISATION_CLASSES:
            lines.append(f"- `{name}`: {', '.join(sorted(by_class.get(name, [])))}")
        lines.append("")
        lines.append(
            f"{len(unclassed)} of the {len(self.corpus['rules'])} rules name no class. They "
            "constrain how a run is conducted, or they are architecture, so no candidate "
            "implements them and `verify` refuses them with that reason. Every `CMP` and `DEP` "
            "rule is one of them, as is every `TRN` rule, because no class names transient "
            "state.")
        lines.append("<!-- corpus-index:end -->")
        self.assertEqual(committed, "\n".join(lines))

    def test_a_rule_with_no_class_is_recorded_rather_than_guessed(self) -> None:
        """58 of the 120 rules name no candidate: they constrain how a run is
        conducted, or they are architecture. The count is asserted because
        quietly mapping one of them to the nearest-sounding class is the
        failure worth catching, and because the size of that number is the
        finding this corpus produced about Hermes itself."""
        unclassed = [r["id"] for r in self.corpus["rules"] if r["hermes_class"] is None]
        self.assertEqual(len(unclassed), 58)
        self.assertEqual(sum(1 for r in self.corpus["rules"] if r["hermes_class"]), 62)
        for identifier in ("CMP-01", "TRN-01", "STO-23", "MEM-15",
                           "STO-12", "MEM-09", "CTL-07", "EXT-13"):
            self.assertIn(identifier, unclassed)

    def test_every_deployment_rule_names_no_class(self) -> None:
        """Every DEP rule is an architecture decision rather than a change
        inside one contract, so the whole section carries null."""
        deployment = [r for r in self.corpus["rules"] if r["id"].startswith("DEP-")]
        self.assertEqual(len(deployment), 12)
        for rule in deployment:
            with self.subTest(rule=rule["id"]):
                self.assertIsNone(rule["hermes_class"])
                self.assertEqual(rule["kind"], "architecture")

    def test_every_assembly_section_rule_takes_the_assembly_class(self) -> None:
        """The one section where the class vocabulary fits exactly."""
        yul = [r for r in self.corpus["rules"] if r["id"].startswith("YUL-")]
        self.assertEqual(len(yul), 14)
        for rule in yul:
            with self.subTest(rule=rule["id"]):
                self.assertEqual(rule["hermes_class"], "assembly")

    def test_the_require_custom_error_prohibition_stops_at_its_release(self) -> None:
        """EXT-01 is the one rule whose upper bound matters: the source says
        custom-error arguments to require arrived after 0.8.25, so the
        prohibition cannot be carried into the release that introduced them."""
        rule = next(r for r in self.corpus["rules"] if r["id"] == "EXT-01")
        self.assertEqual(rule["scope"]["compiler_max_exclusive"], "0.8.26")
        self.assertEqual(rule["hermes_class"], "custom-errors")

    def test_the_canonical_loop_rule_floors_at_the_release_that_changed_it(self) -> None:
        rule = next(r for r in self.corpus["rules"] if r["id"] == "CTL-04")
        self.assertEqual(rule["scope"]["compiler_min"], "0.8.22")
        self.assertIn("0.8.22", rule["scope"]["compiler_reason"])

    def test_a_rule_stating_its_own_assembly_takes_the_assembly_class(self) -> None:
        """Round 1 finding: MEM-12 states its implementation is scratch-memory
        hashing, and Gate 2 refuses added assembly outside the assembly class,
        so any other class would have been refused every time."""
        rule = next(r for r in self.corpus["rules"] if r["id"] == "MEM-12")
        self.assertEqual(rule["hermes_class"], "assembly")
        self.assertIn("scratch-memory", rule["statement"])

    def test_a_code_size_rule_is_not_floored_at_the_initcode_fork(self) -> None:
        """Round 1 finding: DEP-07 and DEP-08 hold where EIP-170 already
        applies, so a Shanghai floor refused advice correct on every earlier
        fork."""
        for identifier in ("DEP-07", "DEP-08"):
            rule = next(r for r in self.corpus["rules"] if r["id"] == identifier)
            with self.subTest(rule=identifier):
                self.assertEqual(rule["scope"]["evm_floor"], "homestead")
                self.assertIn("EIP-3860", rule["scope"]["evm_reason"])

    def test_every_class_the_harness_knows_is_reachable_from_some_rule(self) -> None:
        """A class no rule names would be a class the corpus cannot select,
        which is the other half of the mapping question."""
        named = {r["hermes_class"] for r in self.corpus["rules"]} - {None}
        self.assertEqual(named, set(hermes.OPTIMISATION_CLASSES))

    def test_every_measurement_rule_names_no_class(self) -> None:
        for rule in self.corpus["rules"]:
            if rule["kind"] == "measurement":
                with self.subTest(rule=rule["id"]):
                    self.assertIsNone(rule["hermes_class"])

    def test_every_scope_reason_is_written_out(self) -> None:
        for rule in self.corpus["rules"]:
            scope = rule["scope"]
            with self.subTest(rule=rule["id"]):
                for field in ("compiler_reason", "evm_reason", "pipeline_reason"):
                    self.assertGreater(len(scope[field]), 40, field)

    def test_a_transient_rule_floors_at_cancun(self) -> None:
        """The scope bound that would otherwise ship advice a Paris chain
        cannot execute. TRN-07 is deliberately outside it: that rule is the
        capability check itself, so flooring it at Cancun would refuse it on
        exactly the targets it exists to protect."""
        for rule in self.corpus["rules"]:
            if rule["id"].startswith("TRN-") and rule["id"] != "TRN-07":
                with self.subTest(rule=rule["id"]):
                    self.assertEqual(rule["scope"]["evm_floor"], "cancun")
                    self.assertEqual(rule["scope"]["compiler_min"], "0.8.25")

    def test_the_chain_capability_gate_applies_below_cancun(self) -> None:
        gate = next(r for r in self.corpus["rules"] if r["id"] == "TRN-07")
        self.assertEqual(gate["scope"]["evm_floor"], "homestead")
        self.assertIn("below Cancun", gate["scope"]["evm_reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
