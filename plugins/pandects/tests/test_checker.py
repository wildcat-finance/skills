"""The six parts, each removed in turn.

Every test here builds a law that passes, breaks exactly one part, and asserts
the checker names that part. A test that broke two things at once would pass
for the wrong reason, which is the same discipline the corpus asks of a
specimen.
"""

import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

from pandects_lib import catalogue as catalogue_module  # noqa: E402
from pandects_lib import checker  # noqa: E402

COMPONENT = """// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

import {ICreditObservables} from "../ICreditObservables.sol";
import {Law} from "../Law.sol";

contract Sound is Law {
    function id() external pure override returns (string memory) {
        return "%s";
    }

    function statement() external pure override returns (string memory) {
        return "Assets held cover the claims recorded against them.";
    }

    function check(ICreditObservables target)
        external
        view
        override
        returns (bool held, string memory detail)
    {
        if (target.totalAssets() >= target.totalLenderClaims()) {
            return (true, "covered");
        }
        return (false, "not covered");
    }
}
"""

SPECIMEN = """// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

/// @notice A deliberately broken credit contract. Do not deploy this.
contract Broken {}
"""

COUNTEREXAMPLE = """// SPDX-License-Identifier: Apache-2.0
pragma solidity 0.8.28;

contract Replay {}
"""

IDENTIFIER = "conservation/held-covers-claims/v1"


def law(**overrides):
    entry = {
        "id": IDENTIFIER,
        "family": "conservation",
        "statement": "Assets held cover the claims recorded against them.",
        "component": "src/laws/HeldCoversClaims.sol",
        "specimen": "specimens/DroppedClaim.sol",
        "counterexample": "test/counterexamples/HeldCoversClaims.t.sol",
        "applicability": {
            "accounting_model": "pooled deposits with a withdrawal queue",
            "assumes": ["claims are denominated in the deposit asset"],
            "requires": ["reservedAssets", "totalLenderClaims"],
        },
        "bounds": "exact",
    }
    entry.update(overrides)
    return entry


class CheckerCase(unittest.TestCase):
    """A plugin root on disk, valid until a test breaks one part of it."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        self.write("src/laws/HeldCoversClaims.sol", COMPONENT % IDENTIFIER)
        self.write("specimens/DroppedClaim.sol", SPECIMEN)
        self.write("test/counterexamples/HeldCoversClaims.t.sol", COUNTEREXAMPLE)
        self.entry = law()

    def write(self, relative, body):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as handle:
            handle.write(body)
        return path

    def findings(self, entry=None):
        raw = {
            "version": "0.1.0",
            "observables": "ICreditObservables",
            "families": {"conservation": "held against each other"},
            "laws": [entry if entry is not None else self.entry],
        }
        found = catalogue_module.parse(raw)
        return checker.check(self.root, found)

    def parts(self, entry=None):
        return sorted({f.part for f in self.findings(entry)})


class CompleteLawTests(CheckerCase):
    def test_a_law_with_every_part_passes(self):
        self.assertEqual(self.findings(), [])


class ExecutesTests(CheckerCase):
    def test_a_missing_component_fails(self):
        self.assertIn("executes", self.parts(law(component="src/laws/Absent.sol")))

    def test_a_component_whose_id_disagrees_with_the_catalogue_fails(self):
        self.write("src/laws/HeldCoversClaims.sol", COMPONENT % "something/else/v1")
        found = self.findings()
        self.assertIn("executes", [f.part for f in found])
        self.assertIn("something/else/v1", found[0].detail)

    def test_a_component_outside_the_plugin_is_refused(self):
        self.assertIn("executes", self.parts(law(component="../../../etc/passwd")))

    def test_a_path_the_filesystem_refuses_is_a_finding_rather_than_a_crash(self):
        """An embedded null byte raises out of realpath, not out of this."""
        self.assertIn("executes", self.parts(law(component="src/laws/\x00.sol")))

    def test_a_component_declaring_no_id_fails(self):
        self.write("src/laws/HeldCoversClaims.sol", "contract Nameless {}")
        self.assertIn("executes", self.parts())

    def test_a_law_reverting_to_signal_a_violation_fails(self):
        """Under fail_on_revert = false a revert carries no verdict."""
        reverting = COMPONENT % IDENTIFIER
        reverting = reverting.replace(
            'return (false, "not covered");',
            'require(false, "not covered");\n        return (false, "unreachable");',
        )
        self.write("src/laws/HeldCoversClaims.sol", reverting)
        found = self.findings()
        self.assertIn("judges rather than reverts", [f.part for f in found])

    def test_a_law_may_still_read_a_target_that_reverts(self):
        """The ban is on reverting to mean violated, not on calling a target."""
        self.assertEqual(self.findings(), [])

    def test_assert_is_caught_with_require_and_revert(self):
        """A panic is as silent as any other revert under fail_on_revert."""
        using = COMPONENT % IDENTIFIER
        using = using.replace(
            'return (false, "not covered");', "assert(false);\n        return (false, \"x\");"
        )
        self.write("src/laws/HeldCoversClaims.sol", using)
        found = self.findings()
        self.assertIn("judges rather than reverts", [f.part for f in found])
        self.assertIn("assert", found[0].detail)

    def test_the_word_require_in_a_comment_is_not_evidence(self):
        commented = COMPONENT % IDENTIFIER
        commented = commented.replace(
            "        if (target.totalAssets()",
            "        // this law does not require(x) of its target\n        if (target.totalAssets()",
        )
        self.write("src/laws/HeldCoversClaims.sol", commented)
        self.assertEqual(self.findings(), [])

    def test_the_revert_scan_survives_a_law_formatted_differently(self):
        """The scan reads the component, not a parsed body, so a formatting
        difference cannot silently switch the check off."""
        oneline = (
            "// SPDX-License-Identifier: Apache-2.0\n"
            "contract L { function id() external pure returns (string memory) "
            '{ return "%s"; } '
            "function check() external view { require(false); } }" % IDENTIFIER
        )
        self.write("src/laws/HeldCoversClaims.sol", oneline)
        self.assertIn("judges rather than reverts", self.parts())

    def test_a_helper_named_for_reverting_is_not_a_revert(self):
        """`revertHelper` is a name, not a verdict."""
        named = COMPONENT % IDENTIFIER
        named = named.replace(
            "contract Sound is Law {",
            "contract Sound is Law {\n    function revertHelper(uint256 x) internal pure returns (uint256) { return x; }\n",
        )
        self.write("src/laws/HeldCoversClaims.sol", named)
        self.assertEqual(self.findings(), [])

    def test_a_statement_describing_a_requirement_is_not_a_revert(self):
        """The sentence a law states is prose, and prose is not evidence."""
        describing = COMPONENT % IDENTIFIER
        describing = describing.replace(
            'return "Assets held cover the claims recorded against them.";',
            'return "The system must require(collateral) before it lends.";',
        )
        self.write("src/laws/HeldCoversClaims.sol", describing)
        self.assertEqual(self.findings(), [])

    def test_a_component_that_is_not_text_is_a_finding_rather_than_a_crash(self):
        path = os.path.join(self.root, "src/laws/HeldCoversClaims.sol")
        with open(path, "wb") as handle:
            handle.write(b"\xff\xfe\x00binary")
        found = self.findings()
        self.assertIn("executes", [f.part for f in found])
        self.assertIn("not readable text", found[0].detail)


class CatchesTests(CheckerCase):
    def test_a_missing_specimen_fails(self):
        self.assertIn("catches", self.parts(law(specimen="specimens/Absent.sol")))

    def test_a_specimen_that_is_not_text_is_a_finding_rather_than_a_crash(self):
        path = os.path.join(self.root, "specimens/DroppedClaim.sol")
        with open(path, "wb") as handle:
            handle.write(b"\xff\xfe\x00binary")
        found = self.findings()
        self.assertIn("catches", [f.part for f in found])

    def test_a_specimen_that_does_not_say_it_is_broken_fails(self):
        self.write("specimens/DroppedClaim.sol", "contract Quiet {}")
        found = self.findings()
        self.assertIn("catches", [f.part for f in found])
        self.assertIn("gets copied", found[0].detail)


class ReducedTests(CheckerCase):
    def test_a_missing_counterexample_fails(self):
        self.assertIn(
            "has been reduced",
            self.parts(law(counterexample="test/counterexamples/Absent.t.sol")),
        )


class ApplicabilityTests(CheckerCase):
    def test_a_law_with_no_applicability_fails(self):
        self.assertIn("says where it applies", self.parts(law(applicability={})))

    def test_an_empty_accounting_model_fails(self):
        entry = law()
        entry["applicability"]["accounting_model"] = "   "
        self.assertIn("says where it applies", self.parts(entry))

    def test_assumptions_must_be_a_list_so_empty_is_a_claim(self):
        entry = law()
        entry["applicability"]["assumes"] = "none"
        self.assertIn("says where it applies", self.parts(entry))

    def test_an_empty_assumption_list_is_allowed_because_it_is_a_claim(self):
        entry = law()
        entry["applicability"]["assumes"] = []
        self.assertEqual(self.findings(entry), [])


class BoundsTests(CheckerCase):
    def test_exact_is_a_complete_answer(self):
        self.assertEqual(self.findings(law(bounds="exact")), [])

    def test_a_tolerance_naming_its_arithmetic_passes(self):
        entry = law(
            bounds={
                "tolerance": "1 wei per accrual step",
                "arithmetic": "truncating division in the per-second rate",
            }
        )
        self.assertEqual(self.findings(entry), [])

    def test_a_tolerance_without_its_arithmetic_fails(self):
        entry = law(bounds={"tolerance": "1 wei"})
        found = self.findings(entry)
        self.assertIn("bounds are justified", [f.part for f in found])
        self.assertIn("made a test pass", found[0].detail)

    def test_a_bare_number_is_not_a_bound(self):
        self.assertIn("bounds are justified", self.parts(law(bounds=1)))

    def test_missing_bounds_fails_as_a_finding_rather_than_a_parse_error(self):
        """A missing part is the checker's business, so the reader is told
        which part rather than that the file is malformed."""
        entry = law()
        del entry["bounds"]
        self.assertIn("bounds are justified", self.parts(entry))


class FilingTests(CheckerCase):
    def test_a_family_the_catalogue_does_not_declare_fails(self):
        self.assertIn("is filed", self.parts(law(family="invented")))

    def test_a_component_on_disk_that_no_entry_claims_fails(self):
        self.write("src/laws/Unfiled.sol", COMPONENT % "unfiled/law/v1")
        found = self.findings()
        self.assertIn("is filed", [f.part for f in found])
        self.assertTrue(any("Unfiled.sol" in f.law for f in found))


class StatementTests(CheckerCase):
    def test_an_empty_statement_fails(self):
        self.assertIn("states itself", self.parts(law(statement="  ")))


PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "catalogue", "pandects.json")

PART_FOR_FIELD = {
    "component": "executes",
    "specimen": "catches",
    "counterexample": "has been reduced",
    "applicability": "says where it applies",
    "bounds": "bounds are justified",
    "statement": "states itself",
    "family": "is filed",
}


class ShippedLawsTests(unittest.TestCase):
    """Every part removed in turn, from every law the corpus actually ships.

    The tests above prove the checker works on a law built to be broken. This
    proves it works on the laws in the catalogue, which is a different claim: a
    gate that fires on a synthetic entry and not on a real one has been tested
    against itself.
    """

    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)

    def findings_for(self, entries):
        raw = {
            "version": self.catalogue.version,
            "observables": "ICreditObservables",
            "families": self.catalogue.families,
            "laws": entries,
        }
        return checker.check(PLUGIN_ROOT, catalogue_module.parse(raw))

    def test_every_shipped_law_passes_with_every_part_present(self):
        self.assertEqual(self.findings_for([law.raw for law in self.catalogue.laws]), [])

    def test_every_shipped_law_is_refused_with_any_part_removed(self):
        for law in self.catalogue.laws:
            for field, part in PART_FOR_FIELD.items():
                broken = dict(law.raw)
                del broken[field]
                found = self.findings_for([broken])
                # Filtered to this law's own findings. Checking one law in
                # isolation leaves the other eight components on disk
                # unclaimed, and those are reported under "is filed" too, so an
                # unfiltered assertion would pass for the removal of `family`
                # whatever the checker did.
                named = [
                    f for f in found if f.part == part and f.law == law.id
                ]
                self.assertTrue(
                    named,
                    "%s lost its %s and the checker did not say so: %r"
                    % (law.id, field, [f.line() for f in found]),
                )


if __name__ == "__main__":
    unittest.main()
