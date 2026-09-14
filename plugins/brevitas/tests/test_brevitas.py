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

DIGEST_LOWER = "d" * 64
DIGEST_UPPER = "E" * 64
GIT_FULL_LOWER = "a" * 40
GIT_FULL_UPPER = "B" * 40
GIT_SHORT_LOWER = "c0ffee7"
GIT_SHORT_UPPER = "DEADBEEF"
SELECTOR_LOWER = "0xa9059cbb"
SELECTOR_UPPER = "0xDEADBEEF"


def fiat_audit_record(rows: int = 1) -> str:
    body = [
        "# Fiat audit record",
        "",
        "## S1-R2",
        "",
        "| id | severity | summary |",
        "|---|---|---|",
    ]
    body.extend(f"| S1-R2-{index:02d} | high | defect |" for index in range(1, rows + 1))
    return "\n".join(body) + "\n"


class BrevitasTests(unittest.TestCase):
    def codes(self, text: str, **kwargs) -> set[str]:
        return {issue.code for issue in brevitas.lint_text(text, **kwargs)}

    def protected(self, text: str) -> dict[str, set[str]]:
        return brevitas.protected_tokens(text)

    def category(self, text: str, name: str) -> set[str]:
        return self.protected(text).get(name, set())

    def missing_messages(self, source: str, draft: str = "Evidence omitted.\n") -> set[str]:
        return {
            issue.message
            for issue in brevitas.lint_text(draft, source_text=source)
            if issue.code == "B030"
        }

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

    def test_fiat_audit_record_suppresses_only_small_schema_structure(self) -> None:
        for rows in (0, 1, 2):
            with self.subTest(rows=rows):
                ordinary = self.codes(fiat_audit_record(rows), mode="report")
                specialised = self.codes(
                    fiat_audit_record(rows), mode="fiat-audit-record"
                )
                self.assertTrue({"B010", "B011"}.issubset(ordinary))
                self.assertEqual(ordinary - {"B010", "B011"}, specialised)

    def test_ordinary_modes_do_not_select_the_fiat_audit_exemption(self) -> None:
        source = fiat_audit_record()
        for mode in ("auto", "answer", "report"):
            with self.subTest(mode=mode):
                codes = self.codes(source, mode=mode)
                self.assertIn("B010", codes)
                self.assertIn("B011", codes)

    def test_fiat_audit_record_retains_non_schema_rules(self) -> None:
        cases = {
            "B002": VALID_FINDING + "Evidence: extra.\n",
            "B003": "[High] Claim.\n",
            "B004": '<!-- brevitas: evidence-exception reason="orphan" -->\n',
            "B005": '<!-- brevitas: evidence-exception reason="short" -->\n' + VALID_FINDING,
            "B006": "```text\n" + "\n".join("x" for _ in range(41)) + "\n```\n",
            "B007": "```text\nunclosed\n",
            "B009": (
                '<!-- brevitas: evidence-exception reason="ordered evidence" -->\n'
                + VALID_FINDING
                + "Connective prose remains.\n"
            ),
            "B020": "You asked me to inspect this.\n",
            "B021": "Here are the issues:\n- defect\n",
            "B022": "I will now inspect this.\n",
            "B023": "**Impact:** Value.\n",
            "B024": "Notably, this is asserted.\n",
            "B025": "- defect\nIn summary, unsafe.\n",
            "B026": "Finding.\nLet me know if you want more.\n",
            "B027": "This may possibly fail.\n",
        }
        for code, source in cases.items():
            with self.subTest(code=code):
                self.assertIn(code, self.codes(source, mode="fiat-audit-record"))

        source = "At `src/Foo.sol:42`, 17 calls reach the boundary."
        self.assertIn(
            "B030",
            self.codes(
                "Evidence omitted.\n",
                mode="fiat-audit-record",
                source_text=source,
            ),
        )

    def test_parser_accepts_the_explicit_fiat_audit_record_mode(self) -> None:
        try:
            parsed = brevitas.build_parser().parse_args(
                ["--mode", "fiat-audit-record"]
            )
        except SystemExit as error:
            self.fail(f"parser rejected fiat-audit-record with exit {error.code}")
        self.assertEqual("fiat-audit-record", parsed.mode)

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

    def test_source_evidence_protects_new_hex_token_families(self) -> None:
        source = (
            f"digest {DIGEST_LOWER}; commit {GIT_SHORT_LOWER}; "
            f"object {GIT_FULL_LOWER}; selector {SELECTOR_LOWER}."
        )
        messages = self.missing_messages(source)
        self.assertIn(f"missing protected digest: {DIGEST_LOWER}", messages)
        self.assertIn(f"missing protected Git object id: {GIT_SHORT_LOWER}", messages)
        self.assertIn(f"missing protected Git object id: {GIT_FULL_LOWER}", messages)
        self.assertIn(f"missing protected selector: {SELECTOR_LOWER}", messages)

    def test_new_hex_token_families_recover_when_restored(self) -> None:
        source = (
            f"digest {DIGEST_LOWER}; `" + GIT_SHORT_LOWER + "`; "
            f"object {GIT_FULL_LOWER}; selector {SELECTOR_LOWER}."
        )
        self.assertIn("B030", self.codes("Evidence omitted.\n", source_text=source))
        self.assertNotIn("B030", self.codes(source, source_text=source))

    def test_new_hex_token_literals_remain_case_sensitive(self) -> None:
        source = (
            f"digest {DIGEST_UPPER}; SHA {GIT_SHORT_UPPER}; "
            f"object {GIT_FULL_UPPER}; selector {SELECTOR_UPPER}."
        )
        draft = source.lower()
        messages = self.missing_messages(source, draft)
        self.assertIn(f"missing protected digest: {DIGEST_UPPER}", messages)
        self.assertIn(f"missing protected Git object id: {GIT_SHORT_UPPER}", messages)
        self.assertIn(f"missing protected Git object id: {GIT_FULL_UPPER}", messages)
        self.assertIn(f"missing protected selector: {SELECTOR_UPPER}", messages)

    def test_git_object_ids_are_admitted_only_in_closed_contexts(self) -> None:
        tokens = self.category(
            f"{GIT_FULL_LOWER} `" + GIT_SHORT_LOWER + "` "
            f"commit: {GIT_SHORT_UPPER} owner/repository@abc1234",
            "Git object id",
        )
        self.assertEqual(
            tokens,
            {GIT_FULL_LOWER, GIT_SHORT_LOWER, GIT_SHORT_UPPER, "abc1234"},
        )

    def test_markdown_code_context_requires_matching_backtick_runs(self) -> None:
        admitted = ("`abc1234`", "``abc1234``", "````abc1234````")
        refused = (
            "``abc1234`",
            "`abc1234``",
            "``abc1234```",
            "````abc1234```",
            "```abc1234````",
            "`abc1234",
        )
        for source in admitted:
            with self.subTest(source=source):
                self.assertEqual(self.category(source, "Git object id"), {"abc1234"})
        for source in refused:
            with self.subTest(source=source):
                self.assertEqual(self.category(source, "Git object id"), set())

    def test_each_explicit_git_label_admits_an_abbreviation(self) -> None:
        labels = ("git", "commit", "sha", "sha-1", "oid", "ref", "head", "base", "parent", "tree")
        source = " ".join(f"{label}: {index:07x}" for index, label in enumerate(labels, start=1))
        self.assertEqual(
            self.category(source, "Git object id"),
            {f"{index:07x}" for index in range(1, len(labels) + 1)},
        )

    def test_full_git_object_ids_survive_in_every_admitted_context(self) -> None:
        one = "1" * 40
        two = "2" * 40
        three = "3" * 40
        four = "4" * 40
        source = f"{one} `{two}` commit: {three} owner/repository@{four}"
        self.assertEqual(self.category(source, "Git object id"), {one, two, three, four})

    def test_digest_length_boundary_is_exact(self) -> None:
        short = "a" * 63
        exact = "b" * 64
        long = "c" * 65
        self.assertEqual(self.category(f"{short} {exact} {long}", "digest"), {exact})

    def test_git_length_boundaries_are_exact(self) -> None:
        six = "1" * 6
        seven = "2" * 7
        thirty_nine = "3" * 39
        forty = "4" * 40
        forty_one = "5" * 41
        source = f"commit {six}; commit {seven}; commit {thirty_nine}; {forty}; commit {forty_one}"
        self.assertEqual(
            self.category(source, "Git object id"),
            {seven, thirty_nine, forty},
        )

    def test_selector_length_boundary_is_exact(self) -> None:
        seven = "0x" + "1" * 7
        eight = "0x" + "2" * 8
        nine = "0x" + "3" * 9
        self.assertEqual(self.category(f"{seven} {eight} {nine}", "selector"), {eight})

    def test_hexadecimal_adjacency_refuses_partial_tokens(self) -> None:
        source = " ".join(
            (
                "a" + DIGEST_LOWER,
                DIGEST_LOWER + "b",
                "a" + GIT_FULL_LOWER,
                GIT_FULL_LOWER + "b",
                "a" + SELECTOR_LOWER,
                SELECTOR_LOWER + "b",
                f"commit a{GIT_SHORT_LOWER}",
                f"commit {GIT_SHORT_LOWER}b",
            )
        )
        tokens = self.protected(source)
        self.assertEqual(tokens.get("digest", set()), set())
        self.assertEqual(tokens.get("Git object id", set()), {"a" + GIT_SHORT_LOWER, GIT_SHORT_LOWER + "b"})
        self.assertNotIn(GIT_SHORT_LOWER, tokens.get("Git object id", set()))
        self.assertEqual(tokens.get("selector", set()), set())

    def test_punctuation_delimits_new_hex_tokens(self) -> None:
        source = (
            f"({DIGEST_LOWER}),[{GIT_FULL_LOWER}];`{GIT_SHORT_LOWER}`;"
            f"<{SELECTOR_LOWER}>"
        )
        tokens = self.protected(source)
        self.assertEqual(tokens.get("digest", set()), {DIGEST_LOWER})
        self.assertEqual(tokens.get("Git object id", set()), {GIT_FULL_LOWER, GIT_SHORT_LOWER})
        self.assertEqual(tokens.get("selector", set()), {SELECTOR_LOWER})

    def test_protected_token_category_precedence_is_explicit(self) -> None:
        transaction = "0x" + "1" * 64
        address = "0x" + "2" * 40
        selector = "0x" + "3" * 8
        digest = "a" * 64
        git_oid = "b" * 40
        file_line = "src/Foo.sol:42"
        source = f"{transaction} {address} {selector} {digest} {git_oid} {file_line} 17"
        tokens = self.protected(source)
        self.assertEqual(tokens["transaction hash"], {transaction})
        self.assertEqual(tokens["address"], {address})
        self.assertEqual(tokens.get("selector", set()), {selector})
        self.assertEqual(tokens.get("digest", set()), {digest})
        self.assertEqual(tokens.get("Git object id", set()), {git_oid})
        self.assertEqual(tokens["file:line reference"], {file_line})
        self.assertEqual(tokens["numeric token"], {"42", "17"})

    def test_new_hex_categories_preserve_existing_numeric_extraction(self) -> None:
        numeric_digest = "6" * 64
        numeric_git_oid = "7" * 40
        source = f"{numeric_digest} {numeric_git_oid} commit 0000008 src/Foo.sol:42 17"
        tokens = self.protected(source)
        self.assertEqual(tokens["digest"], {numeric_digest})
        self.assertEqual(tokens["Git object id"], {numeric_git_oid, "0000008"})
        self.assertEqual(
            tokens["numeric token"],
            {numeric_digest, numeric_git_oid, "0000008", "42", "17"},
        )

    def test_duplicate_new_evidence_uses_presence_only_semantics(self) -> None:
        source = f"{DIGEST_LOWER} {DIGEST_LOWER} commit {GIT_SHORT_LOWER} commit {GIT_SHORT_LOWER}"
        draft = f"{DIGEST_LOWER} commit {GIT_SHORT_LOWER}"
        self.assertNotIn("B030", self.codes(draft, source_text=source))

    def test_unlabelled_abbreviated_hex_words_are_not_git_evidence(self) -> None:
        source = "deadbee feedface cafe1234 a1b2c3d4e5f60718"
        self.assertEqual(self.category(source, "Git object id"), set())

    def test_near_miss_git_labels_and_repository_forms_are_rejected(self) -> None:
        source = " ".join(
            (
                "hash: abc1234",
                "commitment: bcd2345",
                "sha-2: cde3456",
                "sha256: def4567",
                "owner@aaa1111",
                "owner/repository#bbb2222",
                "owner//repository@ccc3333",
                "owner/repository@ddd444",
                "owner/repository@" + "e" * 40 + "f",
            )
        )
        self.assertEqual(self.category(source, "Git object id"), set())

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
