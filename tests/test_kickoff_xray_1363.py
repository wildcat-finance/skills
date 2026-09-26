"""Mutate the retained #1363 bundle without changing the checker's fixed pins."""

from __future__ import annotations

import contextlib
import copy
import difflib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("kickoff_xray_1363", ROOT / "scripts/kickoff_xray_1363.py")
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


class CommittedPairTests(unittest.TestCase):
    def test_retained_pair_passes(self):
        result = checker.check_bundle()
        self.assertEqual(result["status"], "passed", result)
        self.assertEqual(result["actions"], {"deployed": 141, "candidate": 269})

    def test_market_creation_retains_concrete_override_events(self):
        linkage = json.loads((checker.DEFAULT_BUNDLE / "linkage.json").read_text())
        signature = "onCreateMarket(address,address,(address,string,string,uint128,uint16,uint16,uint32,uint16,uint32,uint256),bytes)"
        expected = {
            ("deployed", "OpenTermHooks"): {"MinimumDepositUpdated": 155},
            ("deployed", "FixedTermHooks"): {"FixedTermUpdated": 176, "MinimumDepositUpdated": 201},
            ("candidate", "OpenTermHooks"): {"MinimumDepositUpdated": 158},
            ("candidate", "FixedTermHooks"): {"FixedTermUpdated": 182, "MinimumDepositUpdated": 214},
            ("candidate", "PeriodicTermHooks"): {"PeriodicTermUpdated": 267, "MinimumDepositUpdated": 303},
        }
        for (role, contract), event_lines in expected.items():
            with self.subTest(role=role, contract=contract):
                actions = {row["id"]: row for row in linkage["snapshots"][role]["actions"]}
                action = actions[contract + ":" + signature]
                events = {row["signature"].split("(", 1)[0]: row for row in action["events"]}
                self.assertEqual(set(events), set(event_lines))
                self.assertEqual(len(action["events"]), len(event_lines))
                self.assertEqual(action["disposition"], "events")
                for name, line in event_lines.items():
                    event = events[name]
                    self.assertEqual(event["source_ref"], f"src/access/{contract}.sol:{line}")
                    self.assertEqual(event["emitter"], contract)
                    self.assertIsInstance(event["conditions"], list)
                    if name == "MinimumDepositUpdated":
                        self.assertTrue(any("hookedMarket.minimumDeposit > 0" in condition
                                            for condition in event["conditions"]))


class PairRefusalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bundle = self.base / "pair"
        shutil.copytree(checker.DEFAULT_BUNDLE, self.bundle)

    def load(self, name):
        return json.loads((self.bundle / name).read_text())

    def write(self, name, data):
        (self.bundle / name).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")

    def bind(self, name):
        manifest = self.load("manifest.json")
        record = next(row for row in manifest["artifacts"] if row["path"] == name)
        data = (self.bundle / name).read_bytes()
        record.update(sha256=checker.digest(data), bytes=len(data))
        self.write("manifest.json", manifest)

    def change(self, name, mutation):
        data = self.load(name)
        mutation(data)
        self.write(name, data)
        self.bind(name)

    def refused(self, code, path=None):
        result = checker.check_bundle(self.bundle)
        self.assertEqual(result["status"], "failed", result)
        self.assertEqual(result["findings"][0]["code"], code, result)
        if path:
            self.assertIn(path, result["findings"][0]["path"], result)

    def test_missing_report(self):
        (self.bundle / "candidate/invariants.md").unlink()
        self.refused("inventory")

    def test_missing_report_even_when_removed_from_manifest(self):
        name = "candidate/invariants.md"
        (self.bundle / name).unlink()
        manifest = self.load("manifest.json")
        manifest["artifacts"] = [row for row in manifest["artifacts"] if row["path"] != name]
        self.write("manifest.json", manifest)
        self.refused("inventory")

    def test_changed_digest(self):
        with (self.bundle / "candidate/x-ray.md").open("a") as stream:
            stream.write("\nUnreviewed change.\n")
        self.refused("digest", "candidate/x-ray.md")

    def test_swapped_source_roles(self):
        self.change("sources.json", lambda data: data["snapshots"]["deployed"].update(commit=checker.ROLES["candidate"]))
        self.refused("source-role", "sources.deployed.commit")

    def test_changed_receipted_study(self):
        name = "study.md"
        with (self.bundle / name).open("a") as stream:
            stream.write("\nDifferent scope.\n")
        self.bind(name)
        self.refused("specification", name)

    def test_missing_selection_report(self):
        name = "design-reports/source-bound-reports-source-identity.json"
        (self.bundle / name).unlink()
        manifest = self.load("manifest.json")
        manifest["artifacts"] = [row for row in manifest["artifacts"] if row["path"] != name]
        self.write("manifest.json", manifest)
        self.refused("evidence-reference", "design-evidence.results.report")

    def test_source_file_omission(self):
        self.change("sources.json", lambda data: data["snapshots"]["deployed"]["files"].pop())
        self.refused("source-inventory", "sources.deployed")

    def test_false_source_digest(self):
        self.change("sources.json", lambda data: data["snapshots"]["candidate"]["files"][0].update(sha256="0" * 64))
        self.refused("source-inventory", "sources.candidate")

    def test_missing_source_disposition(self):
        self.change("sources.json", lambda data: data["snapshots"]["candidate"]["files"][0].pop("disposition"))
        self.refused("shape", "disposition")

    def test_duplicate_action(self):
        def mutate(data):
            actions = data["snapshots"]["deployed"]["actions"]
            actions.append(copy.deepcopy(actions[0]))
        self.change("linkage.json", mutate)
        self.refused("duplicate", "linkage.deployed.actions")

    def test_dropped_action(self):
        self.change("linkage.json", lambda data: data["snapshots"]["candidate"]["actions"].pop())
        self.refused("action-membership", "linkage.candidate.actions")

    def test_jointly_truncated_linkage_and_comparison(self):
        linkage = self.load("linkage.json")
        removed = linkage["snapshots"]["candidate"]["actions"].pop()["id"]
        self.write("linkage.json", linkage)
        self.bind("linkage.json")
        self.change("comparison.json", lambda data: data.update(actions=[row for row in data["actions"] if row["id"] != removed]))
        self.refused("action-membership", "linkage.candidate.actions")

    def test_mutated_independent_inventory(self):
        self.change("evidence/candidate-action-denominator.json", lambda data: data["actions"].pop())
        self.refused("action-inventory", "candidate-action-denominator.json")

    def test_missing_linkage_disposition(self):
        self.change("linkage.json", lambda data: data["snapshots"]["deployed"]["actions"][0].pop("disposition"))
        self.refused("linkage", "linkage.deployed")

    def test_empty_event_mapping(self):
        self.change("linkage.json", lambda data: data["snapshots"]["deployed"]["actions"][0].update(disposition="events", events=[]))
        self.refused("linkage", "linkage.deployed")

    def test_missing_constructor(self):
        self.change("linkage.json", lambda data: data["snapshots"]["candidate"]["initialization"].pop())
        self.refused("action-membership", "linkage.candidate.initialization")

    def test_missing_semantic_comparison(self):
        self.change("comparison.json", lambda data: data["actions"].pop())
        self.refused("comparison-membership", "comparison.actions")

    def test_wrong_added_status(self):
        def mutate(data):
            added = next(row for row in data["actions"] if row["status"] == "added")
            added["status"] = "unchanged"
        self.change("comparison.json", mutate)
        self.refused("comparison")

    def test_changed_literal_diff(self):
        name = "entry-points.diff"
        (self.bundle / name).write_text("--- deployed/entry-points.md\n+++ candidate/entry-points.md\n")
        self.bind(name)
        self.refused("literal-diff", name)

    def test_missing_coverage_failure(self):
        self.change("evidence/execution.json", lambda data: data["coverage"].pop())
        self.refused("execution", "execution.coverage")

    def test_coverage_relabelled_as_success(self):
        self.change("evidence/execution.json", lambda data: data["coverage"][0].update(exit=0, status="passed"))
        self.refused("execution", "execution.coverage")

    def test_missing_review(self):
        self.change("evidence/review.json", lambda data: data.update(status="pending"))
        self.refused("review", "review")

    def test_self_review(self):
        self.change("evidence/review.json", lambda data: data.update(reviewer=data["producer"]))
        self.refused("review", "review")

    def test_omitted_review_action(self):
        self.change("evidence/review.json", lambda data: data["reviewed_actions"]["candidate"].pop())
        self.refused("review", "review.reviewed_actions.candidate")

    def test_stale_review_digest(self):
        self.change("evidence/review.json", lambda data: data["artifacts"][0].update(sha256="0" * 64))
        self.refused("evidence-reference", "review.artifacts")

    def test_missing_visual_inspection(self):
        self.change("evidence/review.json", lambda data: data["visual_inspections"]["candidate"].update(status="pending"))
        self.refused("review", "review.visual_inspections.candidate")

    def test_unsafe_manifest_path(self):
        manifest = self.load("manifest.json")
        manifest["artifacts"].append({"path": "../escape", "sha256": "0" * 64, "bytes": 0})
        self.write("manifest.json", manifest)
        self.refused("unsafe-path", "manifest.artifacts.path")

    def test_symlinked_evidence(self):
        source = self.bundle / "candidate/invariants.md"
        outside = self.base / "outside.md"
        source.rename(outside)
        source.symlink_to(outside)
        self.refused("unsafe-path", "candidate/invariants.md")

    def test_symlinked_directory(self):
        source = self.bundle / "candidate"
        outside = self.base / "outside"
        source.rename(outside)
        source.symlink_to(outside, target_is_directory=True)
        self.refused("unsafe-path", "candidate")

    def test_special_file(self):
        source = self.bundle / "candidate/invariants.md"
        source.unlink()
        os.mkfifo(source)
        self.refused("unsafe-path", "candidate/invariants.md")

    def test_duplicate_json_key(self):
        path = self.bundle / "manifest.json"
        original = path.read_text()
        path.write_text('{"schema":"issue-1363-manifest/v1",' + original[1:])
        self.refused("json", "manifest.json")

    def test_missing_report_action_despite_rebound_diff(self):
        name = "candidate/entry-points.md"
        identifier = self.load("evidence/candidate-action-denominator.json")["actions"][0]["id"]
        source = self.bundle / name
        source.write_text(source.read_text().replace(identifier, "REMOVED-ACTION"))
        self.bind(name)
        old = (self.bundle / "deployed/entry-points.md").read_text()
        new = source.read_text()
        diff = "".join(difflib.unified_diff(old.splitlines(keepends=True), new.splitlines(keepends=True),
                                         fromfile="deployed/entry-points.md", tofile=name))
        (self.bundle / "entry-points.diff").write_text(diff)
        self.bind("entry-points.diff")
        self.refused("report", name)

    def test_conformance_reports_observed_success(self):
        report = self.base / "conformance.json"
        with contextlib.redirect_stdout(io.StringIO()):
            result = checker.main(["conformance", "--candidate", "source-bound-reports",
                                   "--bundle", str(self.bundle), "--report", str(report)])
        self.assertEqual(result, 0)
        actual = json.loads(report.read_text())
        self.assertEqual(set(actual), {"schema", "candidate", "criterion", "command", "exit", "unit", "value"})
        self.assertEqual(actual["schema"], "protasis-design-report/v1")
        self.assertIs(actual["value"], True)
        self.assertEqual(actual["exit"], 0)

    def test_conformance_failure_cannot_claim_success(self):
        (self.bundle / "candidate/invariants.md").unlink()
        report = self.base / "conformance.json"
        with contextlib.redirect_stdout(io.StringIO()):
            result = checker.main(["conformance", "--candidate", "source-bound-reports",
                                   "--bundle", str(self.bundle), "--report", str(report)])
        self.assertEqual(result, 1)
        actual = json.loads(report.read_text())
        self.assertIs(actual["value"], False)
        self.assertEqual(actual["exit"], 1)

    def test_conformance_preserves_existing_output(self):
        report = self.base / "conformance.json"
        report.write_bytes(b"previous record\n")
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            result = checker.main(["conformance", "--candidate", "source-bound-reports",
                                   "--bundle", str(self.bundle), "--report", str(report)])
        self.assertEqual(result, 1)
        self.assertEqual(report.read_bytes(), b"previous record\n")


class InputBoundaryTests(unittest.TestCase):
    def test_json_depth_is_bounded(self):
        with self.assertRaises(checker.Refusal):
            checker.json_object(b'{"nested":' + b'[' * 65 + b'0' + b']' * 65 + b'}', "hostile.json")

    def test_nonfinite_json_is_refused(self):
        with self.assertRaises(checker.Refusal):
            checker.json_object(b'{"number":NaN}', "hostile.json")

    def test_oversized_regular_file_is_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with (root / "large.json").open("wb") as stream:
                stream.truncate(checker.MAX_FILE_BYTES + 1)
            bundle = checker.Bundle(root)
            try:
                with self.assertRaises(checker.Refusal) as caught:
                    bundle.load("large.json")
                self.assertEqual(caught.exception.finding["code"], "limit")
            finally:
                bundle.close()

    def test_path_escape_and_nonportable_paths_are_refused(self):
        for value in ("../escape", "/absolute", "a/../b", "a//b", "a\\b", "a/./b", "a/\x00b"):
            with self.subTest(value=value), self.assertRaises(checker.Refusal):
                checker.relative_path(value, "specimen")


if __name__ == "__main__":
    unittest.main()
