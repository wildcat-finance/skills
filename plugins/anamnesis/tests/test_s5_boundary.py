"""Step 5: the corpus projection is legible without Synkrisis.

ADR-005 keeps corpus projections outside the Synkrisis cohort boundary and says
the projection is read directly instead. That claim only holds if the projection
carries what a reader needs, so these are the guards behind it.
"""

from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
RELEASE = PLUGIN_ROOT / "specimens/pilot/release"

SELF_SUFFICIENCY = ("denominators", "exclusions", "unknowns", "not_established")


def load():
    spec = importlib.util.spec_from_file_location("anamnesis_boundary", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anamnesis = load()


class ProjectionCase(unittest.TestCase):
    """Shared fixture; carries no test of its own."""

    def setUp(self) -> None:
        self.view = anamnesis.observations(
            str(RELEASE), "every public finding in the release"
        )

    def check(self, payload):
        return anamnesis.check_projection(
            payload, anamnesis.OBSERVATION_SCHEMA, anamnesis.OBSERVATION_FIELDS
        )


class ProjectionIsReadableOnItsOwnTerms(ProjectionCase):
    def test_the_producer_is_anamnesis_and_not_synkrisis(self) -> None:
        self.assertEqual(self.view["producer"], "anamnesis-synkrisis-observation/v1")
        self.assertEqual(self.view["schema"], self.view["producer"])
        self.assertNotEqual(self.view["producer"], "promise-machine-run-observation/v1")

    def test_the_included_count_has_a_denominator_to_be_read_against(self) -> None:
        cohort = self.view["cohort"]
        denominators = self.view["denominators"]
        self.assertIn("findings", denominators)
        self.assertEqual(cohort["included"], len(cohort["members"]))
        self.assertLessEqual(cohort["included"], denominators["findings"])

    def test_every_self_sufficiency_field_is_present_and_says_something(self) -> None:
        for field in SELF_SUFFICIENCY:
            with self.subTest(field=field):
                self.assertIn(field, self.view)
        self.assertTrue(self.view["not_established"].strip())
        self.assertTrue(self.view["denominators"])


class RemovingWhatMakesItLegibleIsRefused(ProjectionCase):
    """One specimen per field the projection cannot be read without."""

    def refuse_without(self, field: str) -> None:
        payload = copy.deepcopy(self.view)
        del payload[field]
        with self.assertRaises(anamnesis.Refusal):
            self.check(payload)

    def test_a_projection_without_denominators_is_refused(self) -> None:
        self.refuse_without("denominators")

    def test_a_projection_without_exclusions_is_refused(self) -> None:
        self.refuse_without("exclusions")

    def test_a_projection_without_unknowns_is_refused(self) -> None:
        self.refuse_without("unknowns")

    def test_a_projection_without_not_established_is_refused(self) -> None:
        self.refuse_without("not_established")


if __name__ == "__main__":
    unittest.main()
