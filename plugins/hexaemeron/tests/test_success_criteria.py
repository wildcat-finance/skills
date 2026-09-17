"""Bounded declaration parsing and exact runbook Exit joins."""

import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[3]


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


criteria = load(
    ROOT / "plugins/hexaemeron/skills/protasis/scripts/success_criteria.py",
    "success_criteria_tests",
)
gates = load(
    ROOT / "plugins/hexaemeron/skills/protasis/scripts/gate_commands.py",
    "gate_commands_success_criteria_tests",
)

COMMAND = "python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py draft.md"
AMENDED = "python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py amended.md"


def declaration(*rows):
    value = {"schema": criteria.SCHEMA, "criteria": list(rows)}
    return "```success-criteria\n" + json.dumps(value) + "\n```\n"


def row(identifier="one", step=1, command=COMMAND, claim="the claim"):
    return {"id": identifier, "claim": claim, "step": step, "command": command}


RUNBOOK = (
    "## Step 1: Check the declaration\n\n"
    "**Goal.** A bounded check.\n"
    "**Entry.** A clean source.\n"
    "**Exit.** Proved by `" + COMMAND + "`.\n"
    "**Files.** `draft.md`.\n"
    "**Tests.** The parser tests.\n"
    "**Disciplines.** none.\n"
)


class ParseTests(unittest.TestCase):
    def test_absent_declaration_is_distinct_from_empty_or_invalid(self):
        self.assertIsNone(criteria.parse("ordinary study prose"))
        with self.assertRaisesRegex(criteria.Refusal, "success-criteria-empty"):
            criteria.parse(declaration().replace('"criteria": []', '"criteria": []'))

    def test_one_column_zero_fence_returns_canonical_descriptors(self):
        record = criteria.parse(declaration(row()))
        self.assertEqual(record, {"schema": criteria.SCHEMA, "criteria": [row()]})
        self.assertEqual(criteria.declaration_digest(record),
                         criteria.digest(criteria.canonical_bytes(record)))

    def test_duplicate_fences_and_nested_decoys(self):
        with self.assertRaisesRegex(criteria.Refusal, "fence-ambiguous"):
            criteria.parse(declaration(row()) + declaration(row("two")))
        nested = "````markdown\n" + declaration(row()) + "````\n"
        self.assertIsNone(criteria.parse(nested))
        for indent in (" ", "  ", "   "):
            with self.subTest(indent=len(indent)), self.assertRaisesRegex(
                    criteria.Refusal, "not-column-zero"):
                criteria.parse(indent + "```success-criteria\n" +
                               json.dumps({"schema": criteria.SCHEMA,
                                           "criteria": [row()]}) +
                               "\n" + indent + "```\n")

    def test_duplicate_keys_unknown_fields_and_schema_refuse(self):
        duplicate = ('```success-criteria\n{"schema":"%s","schema":"%s",'
                     '"criteria":[%s]}\n```\n' %
                     (criteria.SCHEMA, criteria.SCHEMA, json.dumps(row())))
        with self.assertRaisesRegex(criteria.Refusal, "duplicate-key"):
            criteria.parse(duplicate)
        for value in (
            {"schema": criteria.SCHEMA, "criteria": [dict(row(), extra=True)]},
            {"schema": "other/v1", "criteria": [row()]},
            {"schema": criteria.SCHEMA, "criteria": [{**row(), "step": 1,
                                                          "claim": "ok", "id": "one",
                                                          "command": COMMAND,
                                                          "extra": None}]},
        ):
            with self.subTest(value=value), self.assertRaises(criteria.Refusal):
                criteria.parse("```success-criteria\n" + json.dumps(value) +
                               "\n```\n")

    def test_boolean_integer_and_unsafe_or_empty_values_refuse(self):
        cases = [
            {"step": True}, {"step": 0}, {"step": criteria.MAX_STEP + 1},
            {"id": ""}, {"id": "not safe"}, {"id": "Upper"},
            {"claim": ""}, {"claim": " padded "}, {"command": ""},
            {"command": "python3\nnext"}, {"command": "python3\x00next"},
        ]
        for change in cases:
            value = row()
            value.update(change)
            source = declaration(value)
            with self.subTest(change=change), self.assertRaises(criteria.Refusal):
                criteria.parse(source)

    def test_count_and_document_bounds_are_fail_closed(self):
        too_many = [row(str(number)) for number in range(criteria.MAX_CRITERIA + 1)]
        with self.assertRaisesRegex(criteria.Refusal, "success-criteria-count"):
            criteria.parse(declaration(*too_many))
        with self.assertRaisesRegex(criteria.Refusal, "input-too-large"):
            criteria.parse(("x" * criteria.MAX_DOCUMENT_BYTES).encode() + b"\n")


class JoinTests(unittest.TestCase):
    def join(self, record, runbook=RUNBOOK):
        return criteria.join(criteria.parse(declaration(*record)), runbook)

    def test_wrong_step_tests_only_and_missing_exit_refuse(self):
        for record, runbook in (
            ([row(step=2)], RUNBOOK),
            ([row(command="python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py tests.md")],
             RUNBOOK.replace("**Tests.** The parser tests.",
                             "**Tests.** `python3 plugins/brevitas/skills/brevitas/scripts/brevitas.py tests.md`.")),
            ([row()], RUNBOOK.replace("**Exit.** Proved by `" + COMMAND + "`.\n", "")),
        ):
            with self.subTest(runbook=runbook), self.assertRaisesRegex(
                    criteria.Refusal, "criteria-exit-missing"):
                self.join(record, runbook)

    def test_duplicate_exit_command_is_ambiguous(self):
        runbook = RUNBOOK.replace(
            "**Exit.** Proved by `" + COMMAND + "`.\n",
            "**Exit.** Proved by `" + COMMAND + "` and `" + COMMAND + "`.\n",
        )
        with self.assertRaisesRegex(criteria.Refusal, "criteria-exit-ambiguous"):
            self.join([row()], runbook)

    def test_multiple_descriptors_share_one_exact_exit_observation(self):
        result = self.join([row(), row("two", claim="the other claim")])
        self.assertEqual(len(result["criteria"]), 2)
        self.assertEqual(result["criteria"][0]["exit"]["command"], COMMAND)
        self.assertEqual(result["criteria"][0]["exit"]["offset"],
                         result["criteria"][1]["exit"]["offset"])

    def test_amended_exit_replaces_baseline_and_preserves_exact_identity(self):
        amended = RUNBOOK + (
            "\n### Amendment -- 2026-09-16\n\n"
            "**What changed.** Complete replacement Exit: Proved by `" + AMENDED + "`.\n"
            "**Why.** The command changed.\n"
            "**Steps touched.** Step 1.\n"
            "**Still holding.** Step 1: entry holds; exit holds.\n"
        )
        with self.assertRaisesRegex(criteria.Refusal, "criteria-exit-missing"):
            self.join([row()], amended)
        result = self.join([row(command=AMENDED)], amended)
        self.assertEqual(result["criteria"][0]["exit"]["command"], AMENDED)

    def test_adapter_admission_is_inert_and_binds_real_current_runbook(self):
        declaration_bytes = (ROOT / "docs/protasis-success-criteria/study.md").read_bytes()
        runbook_bytes = (ROOT / "docs/protasis-success-criteria/runbook.md").read_bytes()
        result = gates.validate_with_criteria(ROOT, declaration_bytes, runbook_bytes)
        self.assertEqual(result["schema"], "protasis-success-criteria-admission/v1")
        self.assertFalse(result["operation_ran"])
        self.assertEqual(len(result["join"]["criteria"]), 8)
        self.assertEqual(result["join"]["criteria"][0]["id"], "declared-exit-join")
        self.assertEqual(result["join"]["criteria"][0]["exit"]["step"], 2)
        self.assertEqual(result["gate_commands"]["operation_ran"], False)

    def test_adapter_requires_a_declaration(self):
        with self.assertRaisesRegex(gates.Refusal, "success-criteria-missing"):
            gates.validate_with_criteria(ROOT, b"ordinary prose", RUNBOOK.encode())


if __name__ == "__main__":
    unittest.main()
