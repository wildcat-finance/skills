#!/usr/bin/env python3
"""Focused checks for the labelled-prose-v1 evaluator and evidence."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[1]
EVALUATOR_PATH = SKILL_ROOT / "scripts" / "evaluate_labelled_corpus.py"
FIXTURE = SKILL_ROOT / "evals" / "labelled-prose-v1"

SPEC = importlib.util.spec_from_file_location("evaluate_labelled_corpus", EVALUATOR_PATH)
assert SPEC and SPEC.loader
EVALUATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(EVALUATOR)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class LabelledCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = EVALUATOR.load_fixture(FIXTURE)
        cls.validated = EVALUATOR.validate_fixture(cls.data)
        cls.agreement = EVALUATOR.agreement(cls.validated)
        cls.freeze = load(FIXTURE / "candidate-freeze.json")

    def test_fixture_shape_and_cutoff(self):
        summary = self.validated["summary"]
        self.assertEqual(summary["samples"], 64)
        self.assertEqual(summary["groups"], 16)
        self.assertEqual(summary["origins"], {"human": 32, "model_assisted": 32})
        self.assertEqual(summary["split_samples"], {"calibration": 32, "holdout": 32})
        self.assertEqual(summary["human_cutoff"], "2025-08-01T00:00:00Z")

    def test_agreement_denominators_and_values(self):
        sample = self.agreement["sample_by_tier"]
        spans = self.agreement["raw_span"]
        self.assertEqual((sample["denominator"], sample["a_positive"], sample["b_positive"]), (192, 37, 36))
        self.assertEqual(sample["kappa"], 0.64482)
        self.assertEqual((spans["a_spans"], spans["b_spans"], spans["matched"]), (99, 90, 46))
        self.assertEqual(spans["f1"], 0.486772)

    def test_holdout_coverage_failure_is_preserved(self):
        rows = EVALUATOR.coverage(self.validated, self.validated["split"]["holdout"])
        self.assertEqual(rows["hard"]["actionable_spans"], 12)
        self.assertEqual(rows["gated"]["actionable_spans"], 25)
        self.assertEqual(rows["structural"]["actionable_spans"], 2)
        self.assertTrue(all(row["negative_samples"] >= 8 for row in rows.values()))
        self.assertFalse(all(row["actionable_spans"] >= 8 for row in rows.values()))

    def test_blind_schemas_reject_origin_encoding(self):
        for name in ("annotation-packet.schema.json", "raw-label.schema.json", "adjudication.schema.json"):
            pattern = load(FIXTURE / "schemas" / name)["properties"]["sample_id"]["pattern"]
            self.assertIsNotNone(EVALUATOR.re.fullmatch(pattern, "B-001"))
            self.assertIsNone(EVALUATOR.re.fullmatch(pattern, "H-TD-01-01"))
            self.assertIsNone(EVALUATOR.re.fullmatch(pattern, "M-GH-01-01"))

    def test_commit_message_ordinals_retain_short_subject(self):
        message = "Short subject\n\nFirst paragraph has enough words to remain eligible for the labelled prose fixture and retain ordinal number two."
        self.assertEqual(EVALUATOR.message_paragraphs(message), [(2, "First paragraph has enough words to remain eligible for the labelled prose fixture and retain ordinal number two.")])

    def test_span_pairing_is_one_to_one_and_family_bound(self):
        text = "alpha beta gamma delta"
        predicted = [
            {"tier": "hard", "family": "one", "start_byte": 0, "end_byte": 10},
            {"tier": "hard", "family": "two", "start_byte": 0, "end_byte": 10},
        ]
        gold = [
            {"tier": "hard", "family": "one", "start_byte": 0, "end_byte": 5},
            {"tier": "hard", "family": "one", "start_byte": 6, "end_byte": 10},
        ]
        matches, used_predicted, used_gold = EVALUATOR.match_spans(text, predicted, gold)
        self.assertEqual(len(matches), 1)
        self.assertEqual(len(used_predicted), 1)
        self.assertEqual(len(used_gold), 1)

    def test_undefined_ratios_stay_null(self):
        self.assertIsNone(EVALUATOR.ratio(0, 0))
        self.assertIsNone(EVALUATOR.f1(None, 1.0))

    def test_frozen_candidate_hashes_are_current(self):
        self.assertEqual(EVALUATOR.file_hashes(), self.freeze["candidate_hashes"])
        self.assertEqual(self.freeze["candidate"], "untouched-imprimatur-v1.1.0")

    def test_holdout_label_digest_is_bound(self):
        holdout = set(self.data["split"]["holdout_samples"])
        rows = [row for row in self.data["labels"] if row["sample_id"] in holdout]
        blob = "".join(
            json.dumps(row, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n"
            for row in rows
        ).encode("utf-8")
        self.assertEqual(hashlib.sha256(blob).hexdigest(), self.freeze["holdout_labels_sha256"])

    def test_published_seals_bind_fixture_and_schemas(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / FIXTURE.name
            shutil.copytree(FIXTURE, copied)
            labels = copied / "labels.jsonl"
            rows = labels.read_text(encoding="utf-8").splitlines()
            first = json.loads(rows[0])
            first["adjudicator_reason"] += " altered"
            rows[0] = json.dumps(first, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            labels.write_text("\n".join(rows) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(EVALUATOR.EvaluationError, "candidate freeze mismatch"):
                EVALUATOR.validate_fixture(EVALUATOR.load_fixture(copied))

        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / FIXTURE.name
            shutil.copytree(FIXTURE, copied)
            schema = copied / "schemas" / "sample.schema.json"
            schema.write_bytes(schema.read_bytes() + b" ")
            with self.assertRaisesRegex(EVALUATOR.EvaluationError, "annotation seal mismatch"):
                EVALUATOR.validate_fixture(EVALUATOR.load_fixture(copied))

    def test_json_schemas_reject_unpublished_row_shapes(self):
        with tempfile.TemporaryDirectory() as directory:
            copied = Path(directory) / FIXTURE.name
            shutil.copytree(FIXTURE, copied)
            samples = copied / "samples.jsonl"
            rows = samples.read_text(encoding="utf-8").splitlines()
            first = json.loads(rows[0])
            first["unsealed_field"] = True
            rows[0] = json.dumps(first, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            samples.write_text("\n".join(rows) + "\n", encoding="utf-8")
            seal = load(copied / "annotation-seal.json")
            seal["samples_sha256"] = hashlib.sha256(samples.read_bytes()).hexdigest()
            (copied / "annotation-seal.json").write_text(
                json.dumps(seal, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            freeze = load(copied / "candidate-freeze.json")
            freeze["fixture_hashes"]["samples.jsonl"] = seal["samples_sha256"]
            (copied / "candidate-freeze.json").write_text(
                json.dumps(freeze, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            with self.assertRaisesRegex(EVALUATOR.EvaluationError, "schema extra keys"):
                EVALUATOR.validate_fixture(EVALUATOR.load_fixture(copied))

    def test_calibration_report_replays_byte_for_byte(self):
        completed = subprocess.run(
            [
                sys.executable,
                str(EVALUATOR_PATH),
                "--fixture",
                str(FIXTURE),
                "--split",
                "calibration",
                "--expect",
                str(FIXTURE / "baseline.json"),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_final_report_records_spent_holdout(self):
        report = load(FIXTURE / "final.json")
        self.assertTrue(report["provisional"])
        self.assertTrue(report["holdout_spent"])
        self.assertEqual(report["calibration"], load(FIXTURE / "baseline.json"))
        self.assertEqual(report["holdout"]["split"], "holdout")
        self.assertEqual(report["holdout"]["candidate_hashes"], self.freeze["candidate_hashes"])
        self.assertFalse(report["holdout"]["gates"]["agreement_sample_by_tier_kappa_at_least_0_80"])
        self.assertFalse(report["holdout"]["gates"]["holdout_eight_actionable_per_tier"])

    def test_dot_fixture_combined_report_replays_byte_for_byte(self):
        completed = subprocess.run(
            [
                sys.executable,
                "../../scripts/evaluate_labelled_corpus.py",
                "--fixture",
                ".",
                "--split",
                "both",
                "--expect",
                "final.json",
            ],
            cwd=FIXTURE,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)

    def test_frontier_digest_and_version(self):
        ledger = (SKILL_ROOT / "EVOLUTION.md").read_text(encoding="utf-8")
        skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
        fields = {}
        for name in ("Frontier status", "Frontier revision", "Current frontier", "Next Fiat job"):
            match = re.search(rf"(?m)^- {re.escape(name)}: (.+)$", ledger)
            self.assertIsNotNone(match)
            fields[name] = match.group(1).strip("`")
        line = "|".join(fields[name] for name in ("Frontier status", "Frontier revision", "Current frontier", "Next Fiat job")) + "\n"
        digest = hashlib.sha256(line.encode("utf-8")).hexdigest()
        self.assertIn(f"| `{digest}` |", ledger)
        self.assertIn('- Current version: `imprimatur-v2.1.0`', ledger)
        self.assertIn('  version: "2.1.0"', skill)

if __name__ == "__main__":
    unittest.main()
