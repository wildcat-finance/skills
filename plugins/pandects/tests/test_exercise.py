"""The declared Foundry exercise map, checked against laws and test surfaces."""

import json
import os
import re
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)
from .exercise_trace import (  # noqa: E402
    NON_JUDGING_SURFACES,
    TEST_SURFACE_FILES,
    reviewed_surface_laws,
)

from pandects_lib import catalogue as catalogue_module  # noqa: E402
from pandects_lib import checker  # noqa: E402


KINDS = (
    "invariant-fuzz",
    "deterministic",
    "deterministic-transition",
    "driver-adapter",
    "probe",
)


def law(identifier, component):
    return {
        "id": identifier,
        "family": "conservation",
        "statement": "A declared relation holds.",
        "component": component,
        "specimen": "specimens/Broken.sol",
        "counterexample": "test/counterexamples/Replay.t.sol",
        "applicability": {
            "accounting_model": "pooled deposits",
            "assumes": [],
            "requires": [],
        },
        "bounds": "exact",
    }


class ExerciseMapTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.catalogue_path = os.path.join(self.root, "catalogue", "pandects.json")
        self.exercise_path = os.path.join(self.root, "catalogue", "exercise.json")
        self.one = "conservation/one/v1"
        self.two = "conservation/two/v1"
        self.write(
            "src/laws/One.sol",
            self.component("One", self.one),
        )
        self.write(
            "src/laws/Two.sol",
            self.component("Two", self.two),
        )
        self.write(
            "specimens/Broken.sol",
            "// deliberately broken\ncontract Broken {}\n",
        )
        self.write("test/counterexamples/Replay.t.sol", "contract Replay {}\n")
        self.write(
            "test/Surface.t.sol",
            "contract SurfaceTest {\n"
            "    function test_judges_both() external {}\n"
            "}\n",
        )
        self.write_json(
            "catalogue/pandects.json",
            {
                "version": "0.1.0",
                "observables": "ICreditObservables",
                "families": {"conservation": "held against each other"},
                "laws": [
                    law(self.one, "src/laws/One.sol"),
                    law(self.two, "src/laws/Two.sol"),
                ],
            },
        )

    @staticmethod
    def component(name, identifier):
        return (
            "contract %s {\n"
            "    function id() external pure returns (string memory) {\n"
            "        return \"%s\";\n"
            "    }\n"
            "}\n" % (name, identifier)
        )

    def write(self, relative, body):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(body)
        return path

    def write_json(self, relative, body):
        self.write(relative, json.dumps(body))

    def valid_map(self):
        surface = {
            "contract": "SurfaceTest",
            "function": "test_judges_both",
            "kind": "deterministic",
        }
        return {
            "engine": "foundry",
            "laws": {
                self.one: {"surfaces": [dict(surface)]},
                self.two: {"surfaces": [dict(surface)]},
            },
        }

    def findings(self, exercise=None):
        if exercise is not None:
            self.write_json("catalogue/exercise.json", exercise)
        catalogue = catalogue_module.load(self.catalogue_path)
        return [
            finding
            for finding in checker.check(self.root, catalogue)
            if finding.part.startswith("exercise")
        ]

    def test_an_absent_map_is_not_a_check_finding(self):
        self.assertEqual(self.findings(), [])

    def test_a_complete_map_with_real_surfaces_passes(self):
        self.assertEqual(self.findings(self.valid_map()), [])

    def test_a_map_law_not_in_the_catalogue_is_a_finding(self):
        exercise = self.valid_map()
        exercise["laws"]["conservation/unknown/v1"] = exercise["laws"][self.one]
        found = self.findings(exercise)
        self.assertTrue(any("unknown/v1" in finding.detail for finding in found))

    def test_a_catalogue_law_absent_from_the_map_is_a_finding(self):
        exercise = self.valid_map()
        del exercise["laws"][self.two]
        found = self.findings(exercise)
        self.assertTrue(any(self.two in finding.detail for finding in found))

    def test_a_surface_function_missing_from_its_contract_is_a_finding(self):
        exercise = self.valid_map()
        exercise["laws"][self.one]["surfaces"][0]["function"] = "test_absent"
        found = self.findings(exercise)
        self.assertTrue(any("test_absent" in finding.detail for finding in found))

    def test_a_surface_kind_outside_the_fixed_vocabulary_is_a_finding(self):
        exercise = self.valid_map()
        exercise["laws"][self.one]["surfaces"][0]["kind"] = "maybe-fuzz"
        found = self.findings(exercise)
        self.assertTrue(any("maybe-fuzz" in finding.detail for finding in found))
        self.assertEqual(
            set(KINDS),
            checker.EXERCISE_KINDS,
            "the test and checker must name the same closed vocabulary",
        )


PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "catalogue", "pandects.json")
SHIPPED_EXERCISE = os.path.join(PLUGIN_ROOT, "catalogue", "exercise.json")


class ShippedExerciseTests(unittest.TestCase):
    def exercise(self):
        with open(SHIPPED_EXERCISE, encoding="utf-8") as handle:
            return json.load(handle)

    def by_surface(self):
        found = {}
        for identifier, entry in self.exercise()["laws"].items():
            for surface in entry["surfaces"]:
                key = (surface["contract"], surface["function"])
                found.setdefault(key, {})[identifier] = surface["kind"]
        return found

    def test_the_shipped_map_exists_and_validates_clean(self):
        self.assertTrue(os.path.isfile(SHIPPED_EXERCISE))
        catalogue = catalogue_module.load(SHIPPED)
        exercise_findings = [
            finding
            for finding in checker.check(PLUGIN_ROOT, catalogue)
            if finding.part.startswith("exercise")
        ]
        self.assertEqual(exercise_findings, [])

    def test_the_adapter_surface_does_not_claim_the_unchecked_pooled_law(self):
        pooled = self.exercise()["laws"][
            "claims/pooled-claims-cover-open-batches/v1"
        ]["surfaces"]
        self.assertNotIn(
            {
                "contract": "WildcatTest",
                "function": "test_the_model_runs_through_the_shipped_adapter",
                "kind": "driver-adapter",
            },
            pooled,
        )

    def test_the_shipped_map_matches_the_complete_reviewed_call_trace(self):
        self.assertEqual(self.by_surface(), reviewed_surface_laws())

    def test_every_solidity_test_surface_has_a_reviewed_classification(self):
        pattern = re.compile(
            r"\bfunction\s+((?:test_|invariant_)[A-Za-z_][A-Za-z0-9_]*)\s*\("
        )
        discovered = set()
        for contract, relative in TEST_SURFACE_FILES.items():
            with open(os.path.join(PLUGIN_ROOT, relative), encoding="utf-8") as handle:
                for function in pattern.findall(handle.read()):
                    discovered.add((contract, function))
        reviewed = set(reviewed_surface_laws())
        self.assertTrue(reviewed.isdisjoint(NON_JUDGING_SURFACES))
        self.assertEqual(discovered, reviewed | NON_JUDGING_SURFACES)
        self.assertEqual(len(discovered), 79)
        self.assertEqual(len(reviewed), 69)


if __name__ == "__main__":
    unittest.main()
