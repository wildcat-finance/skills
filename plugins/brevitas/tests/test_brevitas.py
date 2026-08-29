from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
sys.path.insert(0, str(ROOT))
from repo_contract import assert_host_descriptions_agree, assert_router_reaches

SCRIPT = PLUGIN / "skills" / "brevitas" / "scripts" / "brevitas.py"
SPEC = importlib.util.spec_from_file_location("brevitas", SCRIPT)
assert SPEC and SPEC.loader
brevitas = importlib.util.module_from_spec(SPEC)
sys.modules["brevitas"] = brevitas
SPEC.loader.exec_module(brevitas)


VALID_FINDING = """[High] Claim.
Location: `src/Foo.sol:42`
Mechanism: Exact causal path.
Impact: Funds can be lost.
Fix: Reject the state.
"""


class BrevitasTests(unittest.TestCase):
    def codes(self, text: str, **kwargs) -> set[str]:
        return {issue.code for issue in brevitas.lint_text(text, **kwargs)}

    def test_valid_finding(self) -> None:
        self.assertEqual(self.codes(VALID_FINDING), set())

    def test_over_budget_finding(self) -> None:
        self.assertIn("B002", self.codes(VALID_FINDING + "Evidence: extra.\n"))

    def test_evidence_exception_allows_retention(self) -> None:
        text = (
            '<!-- brevitas: evidence-exception reason="six ordered reproduction steps" -->\n'
            + VALID_FINDING
            + "Reproduction: Step 1.\n"
        )
        self.assertNotIn("B002", self.codes(text))

    def test_evidence_exception_rejects_connective_prose(self) -> None:
        text = (
            '<!-- brevitas: evidence-exception reason="six ordered reproduction steps" -->\n'
            + VALID_FINDING
            + "This is a transition.\n"
        )
        self.assertIn("B009", self.codes(text))

    def test_evidence_exception_must_be_needed(self) -> None:
        text = '<!-- brevitas: evidence-exception reason="not needed" -->\n' + VALID_FINDING
        self.assertIn("B005", self.codes(text))

    def test_code_fence_limit(self) -> None:
        text = "```solidity\n" + "\n".join("x" for _ in range(41)) + "\n```\n"
        self.assertIn("B006", self.codes(text))

    def test_a_forty_line_fence_passes(self) -> None:
        text = "```text\n" + "\n".join("x" for _ in range(40)) + "\n```\n"
        self.assertNotIn("B006", self.codes(text))

    def test_two_fences_under_one_point_pass(self) -> None:
        text = "## Install\n\n```bash\na\n```\n\nthen\n\n```bash\nb\n```\n"
        self.assertEqual([c for c in self.codes(text) if c.startswith("B00")], [])

    def test_small_table(self) -> None:
        text = "| a | b | c |\n|---|---|---|\n| 1 | 2 | 3 |\n"
        self.assertIn("B011", self.codes(text))

    def test_two_sections(self) -> None:
        text = "# Title\n## One\nx\n## Two\ny\n"
        self.assertIn("B010", self.codes(text, mode="report"))

    def test_direct_answer_limit(self) -> None:
        text = "\n".join(f"line {index}" for index in range(7))
        self.assertIn("B001", self.codes(text, mode="answer"))

    def test_structural_openers_and_closers(self) -> None:
        text = "Here are the issues:\n- defect\nLet me know if you want more.\n"
        codes = self.codes(text)
        self.assertIn("B021", codes)
        self.assertIn("B026", codes)

    def test_missing_source_evidence(self) -> None:
        source = "At `src/Foo.sol:42`, 17 calls reach 0x1111111111111111111111111111111111111111."
        codes = self.codes("The path is unsafe.\n", source_text=source)
        self.assertIn("B030", codes)

    def test_source_evidence_survives(self) -> None:
        source = "At `src/Foo.sol:42`, 17 calls reach 0x1111111111111111111111111111111111111111."
        self.assertNotIn("B030", self.codes(source, source_text=source))

    def test_source_subject_mismatch_is_refused(self) -> None:
        source = "At `src/Foo.sol:42`, 17 calls reach the boundary."
        draft = "At `src/Foo.sol:42`, 18 calls reach the boundary."
        self.assertIn("B030", self.codes(draft, source_text=source))

    def test_token_survival_does_not_establish_semantic_equivalence(self) -> None:
        source = "The 17 calls are safe."
        draft = "The 17 calls are unsafe."
        self.assertNotIn("B030", self.codes(draft, source_text=source))

    def test_missing_source_evidence_recovers_when_restored(self) -> None:
        source = "At `src/Foo.sol:42`, 17 calls reach the boundary."
        self.assertIn("B030", self.codes("The path is unsafe.\n", source_text=source))
        self.assertNotIn("B030", self.codes(source, source_text=source))

    def test_clean_structure_does_not_establish_factual_accuracy(self) -> None:
        draft = VALID_FINDING.replace("Claim.", "The Moon is made of cheese.")
        self.assertEqual(self.codes(draft), set())

    def test_over_budget_finding_recovers_after_compression(self) -> None:
        self.assertIn("B002", self.codes(VALID_FINDING + "Evidence: extra.\n"))
        self.assertNotIn("B002", self.codes(VALID_FINDING))

    def test_host_descriptions_remain_identical(self) -> None:
        # Cross-host parity is the repo-wide contract; length is brevitas's own bound.
        assert_host_descriptions_agree(self, "brevitas")
        codex = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(codex["description"]), 25)
        self.assertLessEqual(len(codex["description"]), 64)

    def test_promise_machine_router_reaches_the_runtime_contract(self) -> None:
        assert_router_reaches(self, "brevitas")


if __name__ == "__main__":
    unittest.main()
