"""The campaign record agrees with the tree it claims to describe.

`fizz_data/campaign.json` is generated from a forge run's captured output,
committed beside it as `fizz_data/campaign-output.txt`. A hand-edited record,
or one left behind after the suite changed, disagrees with the vendored
emitter files, the case names in the `.t.sol` files, the provenance record or
the captured output, and this suite fails. Nothing here writes.
"""

import hashlib
import importlib.util
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, os.pardir, "harness"))
CAMPAIGN = os.path.join(HARNESS, "fizz_data", "campaign.json")
OUTPUT = os.path.join(HARNESS, "fizz_data", "campaign-output.txt")
PROVENANCE = os.path.join(HARNESS, "src", "vendor", "PROVENANCE.json")
TEST_DIR = os.path.join(HARNESS, "test")
TEST_FUNCTION = re.compile(r"^\s*function (test\w*)\s*\(", re.MULTILINE)
FULL_SHA = re.compile(r"^[0-9a-f]{40}$")
SEED = re.compile(r"^0x[0-9a-f]{64}$")

REQUIRED = {
    "command": str,
    "counterexample_count": int,
    "counterexamples": list,
    "cwd": str,
    "emitter_case_names": list,
    "emitter_count": int,
    "engine": dict,
    "exit_code": int,
    "fuzz_case_count": int,
    "fuzz_runs": int,
    "fuzz_seed": str,
    "harness_src_tree": str,
    "harness_test_tree": str,
    "output_bytes": int,
    "output_sha256": str,
    "protocol": dict,
    "repository_commit": str,
    "schema": str,
    "suites": list,
    "summary": dict,
    "test_count": int,
    "tests_failed": int,
    "tests_passed": int,
    "tests_skipped": int,
}


def load(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def pairing():
    """The pairing suite's emitter count, derived from the vendored files."""
    spec = importlib.util.spec_from_file_location(
        "harness_pairing", os.path.join(HERE, "test_harness_pairing.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def solidity_case_names():
    names = []
    for entry in sorted(os.listdir(TEST_DIR)):
        if entry.endswith(".t.sol"):
            with open(os.path.join(TEST_DIR, entry), "rb") as fh:
                names.extend(TEST_FUNCTION.findall(fh.read().decode("utf-8")))
    return names


class HarnessCampaignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.record = load(CAMPAIGN)
        cls.recorded_tests = [t for s in cls.record["suites"] for t in s["tests"]]

    def test_required_keys_are_present_with_their_types(self):
        for key, kind in REQUIRED.items():
            self.assertIn(key, self.record)
            self.assertIsInstance(self.record[key], kind, key)
        self.assertEqual(self.record["schema"], "wildcat.hexaemeron-harness-campaign.v1")
        self.assertEqual(self.record["engine"]["name"], "forge")
        self.assertRegex(self.record["engine"]["commit"], FULL_SHA)
        self.assertRegex(self.record["repository_commit"], FULL_SHA)
        self.assertRegex(self.record["harness_src_tree"], FULL_SHA)
        self.assertRegex(self.record["harness_test_tree"], FULL_SHA)
        self.assertRegex(self.record["fuzz_seed"], SEED)
        self.assertRegex(self.record["output_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(self.record["cwd"], "plugins/hexaemeron/harness")
        self.assertIn("--fuzz-seed " + self.record["fuzz_seed"], self.record["command"])
        self.assertIn("--fuzz-runs %d" % self.record["fuzz_runs"], self.record["command"])

    def test_the_file_is_canonical_json_with_a_trailing_newline(self):
        with open(CAMPAIGN, "rb") as fh:
            raw = fh.read()
        canonical = json.dumps(self.record, indent=2, sort_keys=True) + "\n"
        self.assertEqual(raw.decode("utf-8"), canonical)

    def test_the_emitter_count_equals_the_pairing_count(self):
        module = pairing()
        emitters = module.emitter_names()
        self.assertEqual(self.record["emitter_count"], len(emitters))
        self.assertEqual(self.record["emitter_count"], module.EXPECTED_EMITTERS)
        self.assertEqual(len(self.record["emitter_case_names"]), len(emitters))
        recorded = sorted(
            name[len("test_emit_"):].rsplit("_", 1)[0] for name in self.record["emitter_case_names"]
        )
        self.assertEqual(recorded, sorted(emitters))

    def test_the_test_count_matches_the_case_names_in_the_solidity_files(self):
        names = solidity_case_names()
        self.assertEqual(sorted(names), sorted(set(names)), "a case is duplicated")
        self.assertEqual(self.record["test_count"], len(names))
        self.assertEqual(sorted(t["name"] for t in self.recorded_tests), sorted(names))
        self.assertEqual(self.record["summary"]["total"], len(names))

    def test_the_run_was_green_with_zero_counterexamples(self):
        self.assertEqual(self.record["exit_code"], 0)
        self.assertEqual(self.record["counterexample_count"], 0)
        self.assertEqual(self.record["counterexamples"], [])
        self.assertEqual(self.record["tests_failed"], 0)
        self.assertEqual(self.record["tests_skipped"], 0)
        self.assertEqual(self.record["tests_passed"], self.record["test_count"])
        self.assertEqual(self.record["summary"]["passed"], self.record["test_count"])
        self.assertEqual(self.record["summary"]["failed"], 0)
        self.assertEqual([t["name"] for t in self.recorded_tests if t["status"] != "pass"], [])

    def test_the_run_length_exceeds_the_profile_and_every_fuzz_case_reports_it(self):
        self.assertGreater(self.record["fuzz_runs"], 256)
        fuzz = [t for t in self.recorded_tests if t["kind"] == "fuzz"]
        self.assertEqual(len(fuzz), self.record["fuzz_case_count"])
        self.assertEqual({t["runs"] for t in fuzz}, {self.record["fuzz_runs"]})
        for name in self.record["emitter_case_names"]:
            self.assertIn(name, [t["name"] for t in fuzz])

    def test_the_protocol_ref_equals_the_provenance_record(self):
        provenance = load(PROVENANCE)
        self.assertEqual(self.record["protocol"]["ref"], provenance["ref"])
        self.assertEqual(self.record["protocol"]["repository"], provenance["repository"])

    def test_the_captured_output_is_committed_and_the_record_is_read_from_it(self):
        # S4-R1-01: the bytes `output_sha256` names live in the tree, and every
        # per-test row, run count and the summary line are lines of them.
        with open(OUTPUT, "rb") as fh:
            raw = fh.read()
        self.assertEqual(len(raw), self.record["output_bytes"])
        self.assertEqual(hashlib.sha256(raw).hexdigest(), self.record["output_sha256"])
        lines = raw.decode("utf-8").splitlines()
        self.assertIn(self.record["summary"]["line"], lines)
        for suite in self.record["suites"]:
            self.assertIn("Ran %d tests for %s" % (suite["declared"], suite["name"]), lines)
        for test in self.recorded_tests:
            prefix = "[PASS] " + test["signature"] + " ("
            if test["kind"] == "fuzz":
                prefix += "runs: %d," % test["runs"]
            self.assertTrue(any(line.startswith(prefix) for line in lines), test["signature"])
        self.assertEqual(
            sum(1 for line in lines if line.startswith("[PASS] ")), self.record["tests_passed"]
        )
        self.assertEqual(sum(1 for line in lines if line.startswith("[FAIL")), self.record["tests_failed"])


if __name__ == "__main__":
    unittest.main()
