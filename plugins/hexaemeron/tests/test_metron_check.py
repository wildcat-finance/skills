"""The Metron budget check reads its three files, and refuses what it cannot read.

The refusals matter more than the happy path here. All three files arrive from outside
the process, and the fault this marketplace keeps producing is a field that satisfies a
presence check while carrying nothing a comparison can use.
"""

import ast
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "metron" / "scripts" / "metron.py"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "metron"
BUDGETS = FIXTURES / "metron-budgets.json"
BASELINE = FIXTURES / "metron-baseline.json"
RUNS = FIXTURES / "runs"

spec = importlib.util.spec_from_file_location("metron_check", SCRIPT)
metron = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metron)


def budget(**overrides):
    """One well-formed budget, with fields replaced or removed by the caller.

    A field set to the sentinel is dropped, which is how the absent-field tests reach
    every required key without writing nine near-identical literals.
    """
    entry = {
        "name": "harvest.usdc.wall_clock",
        "unit": "s",
        "limit": 1200,
        "variance": 0.05,
        "direction": "lower_is_better",
    }
    entry.update(overrides)
    return {key: value for key, value in entry.items() if value is not DROP}


DROP = object()


class TempFiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, document):
        """A file holding the JSON encoding of `document`, whatever its type."""
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(document), encoding="utf-8")
        return str(path)

    def write_raw(self, name, text):
        """A file holding exactly `text`, for the cases that are not JSON at all."""
        path = Path(self.tmp.name) / name
        path.write_text(text, encoding="utf-8")
        return str(path)

    def budgets_file(self, *entries):
        return self.write("budgets.json", {"budgets": list(entries)})

    def refusal(self, path):
        with self.assertRaises(metron.BudgetError) as caught:
            metron.load_budgets(path)
        return str(caught.exception)


class ShippedFixtureTests(unittest.TestCase):
    def test_the_committed_budget_file_loads(self):
        found = metron.load_budgets(str(BUDGETS))
        self.assertEqual(len(found), 3)
        self.assertEqual(found[0]["name"], "harvest.usdc.wall_clock")

    def test_the_committed_fixture_covers_both_directions(self):
        """A fixture with only lower-is-better budgets would never exercise the other
        branch of the comparison."""
        directions = {entry["direction"] for entry in metron.load_budgets(str(BUDGETS))}
        self.assertEqual(directions, set(metron.DIRECTIONS))

    def test_file_order_is_kept(self):
        """The file is reviewed by a person, so the report should read the way it does."""
        names = [entry["name"] for entry in metron.load_budgets(str(BUDGETS))]
        self.assertEqual(names, sorted(names, key=names.index))
        self.assertEqual(names[0], "harvest.usdc.wall_clock")


class BudgetFileTests(TempFiles):
    def test_a_well_formed_budget_loads(self):
        found = metron.load_budgets(self.budgets_file(budget()))
        self.assertEqual(found[0]["limit"], 1200)

    def test_every_required_field_is_required(self):
        for field in metron.REQUIRED:
            with self.subTest(missing=field):
                path = self.budgets_file(budget(**{field: DROP}))
                self.assertIn(field, self.refusal(path))

    def test_a_name_that_names_nothing_is_refused(self):
        for value in ("", "   ", 7, None, True):
            with self.subTest(name=value):
                self.assertIn("name", self.refusal(self.budgets_file(budget(name=value))))

    def test_a_unit_that_states_nothing_is_refused(self):
        for value in ("", "  ", 3, None):
            with self.subTest(unit=value):
                self.assertIn("unit", self.refusal(self.budgets_file(budget(unit=value))))

    def test_a_limit_that_is_not_a_number_is_refused(self):
        for value in ("1200", None, [1200], {}):
            with self.subTest(limit=value):
                self.assertIn("limit", self.refusal(self.budgets_file(budget(limit=value))))

    def test_a_boolean_limit_is_not_a_number(self):
        """Python makes True an integer, so a membership or isinstance check would have
        compared a limit of true against a measurement."""
        self.assertIn("limit", self.refusal(self.budgets_file(budget(limit=True))))

    def test_a_negative_limit_is_refused(self):
        self.assertIn("negative", self.refusal(self.budgets_file(budget(limit=-1))))

    def test_a_zero_limit_is_allowed(self):
        """Zero is a real ceiling for a count: no round trips, no layout shift."""
        found = metron.load_budgets(self.budgets_file(budget(limit=0)))
        self.assertEqual(found[0]["limit"], 0)

    def test_a_variance_outside_its_range_is_refused(self):
        for value in (-0.1, 1.0, 1.5, 5):
            with self.subTest(variance=value):
                self.assertIn(
                    "variance", self.refusal(self.budgets_file(budget(variance=value)))
                )

    def test_a_variance_of_zero_is_allowed(self):
        """A budget that tolerates no drift at all is a choice, not an error."""
        found = metron.load_budgets(self.budgets_file(budget(variance=0)))
        self.assertEqual(found[0]["variance"], 0)

    def test_a_boolean_variance_is_refused(self):
        self.assertIn("variance", self.refusal(self.budgets_file(budget(variance=True))))

    def test_a_direction_outside_the_two_is_refused(self):
        for value in ("faster", "", None, "LOWER_IS_BETTER", True):
            with self.subTest(direction=value):
                self.assertIn(
                    "direction", self.refusal(self.budgets_file(budget(direction=value)))
                )

    def test_a_duplicate_budget_name_is_refused(self):
        path = self.budgets_file(budget(), budget())
        self.assertIn("declared twice", self.refusal(path))

    def test_an_unknown_field_is_refused(self):
        path = self.budgets_file(budget(threshold=5))
        self.assertIn("threshold", self.refusal(path))

    def test_a_top_level_that_is_not_an_object_is_refused(self):
        for document in ([], "budgets", 7, None):
            with self.subTest(document=document):
                path = self.write("odd.json", document)
                self.assertIn("object", self.refusal(path))

    def test_a_budgets_key_that_is_not_a_list_is_refused(self):
        for value in ({}, "one", 3, None):
            with self.subTest(budgets=value):
                path = self.write("odd.json", {"budgets": value})
                self.assertIn("budgets array", self.refusal(path))

    def test_an_empty_budget_list_is_refused(self):
        """A file declaring nothing is not a budget file, and a check over it would pass
        every run without looking at one."""
        self.assertIn("no budgets", self.refusal(self.write("empty.json", {"budgets": []})))

    def test_an_entry_that_is_not_an_object_is_refused(self):
        for value in ("harvest", 7, [], None):
            with self.subTest(entry=value):
                path = self.write("odd.json", {"budgets": [value]})
                self.assertIn("object", self.refusal(path))

    def test_a_file_that_is_not_json_is_refused(self):
        for text in ("not json", "", "{", "[1,"):
            with self.subTest(text=text):
                self.assertIn("readable JSON", self.refusal(self.write_raw("bad.json", text)))

    def test_the_non_standard_json_constants_are_refused(self):
        """json.loads accepts NaN, Infinity and -Infinity by default, which are a Python
        extension rather than JSON. Every comparison against nan is False, including !=, so
        a nan measurement does not fail a threshold: it falls through whichever branch is
        tested last. An infinite limit means nothing ever exceeds it."""
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                text = ('{"budgets":[{"name":"a","unit":"s","limit":%s,'
                        '"variance":0.05,"direction":"lower_is_better"}]}' % token)
                message = self.refusal(self.write_raw("odd.json", text))
                self.assertIn("not permitted", message)
                self.assertIn(token, message)

    def test_a_non_finite_measurement_is_refused(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(token=token):
                path = self.write_raw("run.json", '{"measurements":{"a":%s}}' % token)
                with self.assertRaises(metron.BudgetError) as caught:
                    metron.load_measurements(path, "run")
                self.assertIn("not permitted", str(caught.exception))

    def test_number_accepts_only_finite_reals(self):
        for value in (0, 1, -1, 3.5, -2.25):
            with self.subTest(value=value, expect=True):
                self.assertTrue(metron.number(value))
        for value in (True, False, "1", None, [], {},
                      float("inf"), float("-inf"), float("nan")):
            with self.subTest(value=value, expect=False):
                self.assertFalse(metron.number(value))

    def test_a_json_string_is_not_an_object(self):
        """`"budgets"` is valid JSON and is not a budget file. The refusal has to say which
        of the two problems it met."""
        self.assertIn("object", self.refusal(self.write("odd.json", "budgets")))

    def test_a_file_that_is_not_there_is_refused(self):
        self.assertIn("cannot read", self.refusal(str(Path(self.tmp.name) / "absent.json")))

    def test_nothing_raises_a_bare_exception(self):
        """Every malformed shape gets a BudgetError naming the fault, because a traceback
        out of a CI check tells the reader nothing they can act on."""
        for document in (None, 7, "x", [], {}, {"budgets": None}, {"budgets": [None]},
                         {"budgets": [{}]}, {"budgets": [{"name": None}]}):
            path = self.write("odd.json", document)
            with self.subTest(document=document):
                with self.assertRaises(metron.BudgetError):
                    metron.load_budgets(path)


class MeasurementFileTests(TempFiles):
    def test_a_measurements_object_loads(self):
        path = self.write("run.json", {"measurements": {"a": 1, "b": 2.5}})
        self.assertEqual(metron.load_measurements(path, "run"), {"a": 1, "b": 2.5})

    def test_a_bare_mapping_loads_too(self):
        """Whatever produced the run may not wrap it. Both shapes read the same."""
        path = self.write("run.json", {"a": 1})
        self.assertEqual(metron.load_measurements(path, "run"), {"a": 1})

    def test_a_value_that_is_not_a_number_is_refused(self):
        for value in ("120", None, [1], {}, True):
            with self.subTest(value=value):
                path = self.write("run.json", {"measurements": {"a": value}})
                with self.assertRaises(metron.BudgetError) as caught:
                    metron.load_measurements(path, "run")
                self.assertIn("a", str(caught.exception))

    def test_a_document_carrying_both_shapes_is_refused(self):
        """Taking the wrapped block drops the top-level values in silence, and a dropped
        measurement is the difference between an `undeclared` verdict and no verdict."""
        path = self.write("run.json", {"measurements": {"a": 1}, "b": 2, "c": 3.5})
        with self.assertRaises(metron.BudgetError) as caught:
            metron.load_measurements(path, "run")
        message = str(caught.exception)
        self.assertIn("b", message)
        self.assertIn("c", message)

    def test_metadata_beside_the_block_is_allowed(self):
        """A producer recording a note or a timestamp alongside its numbers is doing the
        right thing, and only a stray number is ambiguous."""
        for extra in ({"note": "why"}, {"recorded_at": "2026-08-19"},
                      {"ok": True}, {"tags": ["nightly"]}):
            with self.subTest(extra=extra):
                document = {"measurements": {"a": 1}}
                document.update(extra)
                path = self.write("run.json", document)
                self.assertEqual(metron.load_measurements(path, "run"), {"a": 1})

    def test_a_negative_measurement_is_allowed(self):
        """A delta or a temperature can be negative. The comparison decides what it means,
        not the loader."""
        path = self.write("run.json", {"measurements": {"a": -3}})
        self.assertEqual(metron.load_measurements(path, "run"), {"a": -3})

    def test_a_top_level_that_is_not_an_object_is_refused(self):
        for document in ([], "run", 7):
            with self.subTest(document=document):
                path = self.write("run.json", document)
                with self.assertRaises(metron.BudgetError):
                    metron.load_measurements(path, "run")

    def test_the_label_appears_in_the_refusal(self):
        """`run` and `baseline` read the same file shape, so the message has to say which
        one was being read."""
        path = self.write("odd.json", [])
        for what in ("run", "baseline"):
            with self.subTest(what=what):
                with self.assertRaises(metron.BudgetError) as caught:
                    metron.load_measurements(path, what)
                self.assertIn(what, str(caught.exception))


class FileHandlingTests(TempFiles):
    def test_a_directory_is_refused_rather_than_raising(self):
        directory = Path(self.tmp.name) / "adir"
        directory.mkdir()
        self.assertIn("cannot read", self.refusal(str(directory)))

    def test_a_file_past_the_cap_is_refused(self):
        path = Path(self.tmp.name) / "big.json"
        path.write_text("{" + " " * (metron.MAX_BYTES + 1) + "}", encoding="utf-8")
        self.assertIn("larger than", self.refusal(str(path)))

    def test_a_file_at_the_cap_is_read(self):
        """The cap keeps a mistaken path from reading something enormous. It should not
        refuse a file that merely approaches it."""
        entry = {"name": "a", "unit": "s", "limit": 1, "variance": 0.05,
                 "direction": "lower_is_better"}
        document = json.dumps({"budgets": [entry]})
        padding = " " * (metron.MAX_BYTES - len(document) - 1)
        path = Path(self.tmp.name) / "wide.json"
        path.write_text(document[:-1] + padding + "}", encoding="utf-8")
        self.assertLessEqual(path.stat().st_size, metron.MAX_BYTES)
        self.assertEqual(len(metron.load_budgets(str(path))), 1)


class CommandLineTests(TempFiles):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_a_run_reporting_every_budget_exits_zero(self):
        run = self.write("run.json", {"measurements": {
            "harvest.usdc.wall_clock": 1100,
            "harvest.usdc.round_trips": 380,
            "release.digest.throughput": 52,
        }})
        proc = self.run_cli("check", "--budgets", str(BUDGETS), "--run", run)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_a_run_reporting_only_one_budget_fails_on_the_rest(self):
        """A partial run is the case `unmeasured` exists for."""
        run = self.write("run.json", {"measurements": {"harvest.usdc.wall_clock": 1100}})
        proc = self.run_cli("check", "--budgets", str(BUDGETS), "--run", run)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.count("unmeasured"), 2)

    def test_a_malformed_budget_file_exits_two(self):
        bad = self.write_raw("bad.json", "not json")
        run = self.write("run.json", {"measurements": {"a": 1}})
        proc = self.run_cli("check", "--budgets", bad, "--run", run)
        self.assertEqual(proc.returncode, 2)
        self.assertIn("metron: error:", proc.stderr)

    def test_no_subcommand_exits_two(self):
        self.assertEqual(self.run_cli().returncode, 2)

    def test_all_three_subcommands_are_offered(self):
        """`check` and `record` measure nothing; `time` is the one recorder beside
        them. A fourth verb is a design change, not a convenience."""
        parser = metron.build_parser()
        for action in parser._subparsers._group_actions:  # noqa: SLF001
            self.assertEqual(sorted(action.choices), ["check", "record", "time"])
            return
        raise AssertionError("the parser offers no subcommands")


class VerdictTests(unittest.TestCase):
    """One fixture per verdict, compared through the same function the CLI uses."""

    @classmethod
    def setUpClass(cls):
        cls.budgets = metron.load_budgets(str(BUDGETS))
        cls.baseline = metron.load_measurements(str(BASELINE), "baseline")

    def verdicts(self, fixture):
        run = metron.load_measurements(str(RUNS / f"{fixture}.json"), "run")
        return {v.name: v for v in metron.compare(self.budgets, run, self.baseline)}

    def only_failure(self, fixture):
        found = self.verdicts(fixture)
        failed = [v for v in found.values() if v.failed]
        self.assertEqual(len(failed), 1, [v.line() for v in found.values()])
        return failed[0]

    def test_a_move_inside_the_variance_is_another_sample(self):
        for verdict in self.verdicts("neutral").values():
            with self.subTest(budget=verdict.name):
                self.assertEqual(verdict.verdict, "neutral")
                self.assertFalse(verdict.failed)

    def test_a_regression_past_the_variance_fails(self):
        found = self.only_failure("regressed")
        self.assertEqual(found.verdict, "regressed")
        self.assertEqual(found.name, "harvest.usdc.wall_clock")
        self.assertAlmostEqual(found.margin, 0.15)

    def test_an_improvement_past_the_variance_is_reported_and_passes(self):
        found = self.verdicts("improved")
        for verdict in found.values():
            with self.subTest(budget=verdict.name):
                self.assertEqual(verdict.verdict, "improved")
                self.assertFalse(verdict.failed)

    def test_a_value_past_the_limit_fails_whatever_the_history(self):
        """The baseline for this budget is 1000 and the run is 1400, so it is also a
        regression. over-budget is reported because a ceiling does not care about drift."""
        found = self.only_failure("over-budget")
        self.assertEqual(found.verdict, "over-budget")
        self.assertIn("limit", found.detail)

    def test_a_budget_the_run_stopped_reporting_fails(self):
        found = self.only_failure("unmeasured")
        self.assertEqual(found.verdict, "unmeasured")
        self.assertEqual(found.name, "harvest.usdc.round_trips")

    def test_a_measurement_no_budget_declares_fails(self):
        """Usually a typo. Silently ignoring it is how a budget stops being checked."""
        found = self.only_failure("undeclared")
        self.assertEqual(found.verdict, "undeclared")
        self.assertEqual(found.name, "harvest.usdc.round_trip")

    def test_a_higher_is_better_budget_regresses_downward(self):
        """41 MB/s is above the limit of 40, so this is not over-budget. It is 18% below
        the baseline of 50, which is a regression for this direction and would read as an
        improvement if the direction were ignored."""
        found = self.only_failure("throughput-regressed")
        self.assertEqual(found.verdict, "regressed")
        self.assertEqual(found.name, "release.digest.throughput")

    def test_every_verdict_has_a_fixture(self):
        """A verdict with no fixture is one nobody exercises."""
        seen = set()
        for fixture in sorted(RUNS.glob("*.json")):
            run = metron.load_measurements(str(fixture), "run")
            seen.update(v.verdict for v in metron.compare(self.budgets, run, self.baseline))
        self.assertEqual(seen, set(metron.PASSING) | set(metron.FAILING))

    def test_declared_order_is_the_report_order(self):
        names = [v.name for v in metron.compare(
            self.budgets,
            metron.load_measurements(str(RUNS / "neutral.json"), "run"),
            self.baseline,
        )]
        self.assertEqual(names, [b["name"] for b in self.budgets])

    def test_an_undeclared_name_comes_after_the_declared_ones(self):
        names = [v.name for v in metron.compare(
            self.budgets,
            metron.load_measurements(str(RUNS / "undeclared.json"), "run"),
            self.baseline,
        )]
        self.assertEqual(names[:3], [b["name"] for b in self.budgets])
        self.assertEqual(names[3], "harvest.usdc.round_trip")


class ComparisonEdgeTests(unittest.TestCase):
    def budget(self, **overrides):
        entry = {"name": "a", "unit": "s", "limit": 1000, "variance": 0.05,
                 "direction": "lower_is_better"}
        entry.update(overrides)
        return entry

    def verdict(self, run, baseline, **overrides):
        found = metron.compare([self.budget(**overrides)], {"a": run}, {"a": baseline})
        return found[0]

    def test_a_move_exactly_at_the_variance_is_neutral(self):
        """The boundary has to fall on one declared side, and inside is the side the skill
        names: a gain equal to the noise is another sample."""
        self.assertEqual(self.verdict(105, 100).verdict, "neutral")
        self.assertEqual(self.verdict(95, 100).verdict, "neutral")

    def test_a_hair_past_the_variance_is_a_verdict(self):
        self.assertEqual(self.verdict(105.1, 100).verdict, "regressed")
        self.assertEqual(self.verdict(94.9, 100).verdict, "improved")

    def test_the_boundary_gives_the_same_answer_twice(self):
        for _ in range(3):
            self.assertEqual(self.verdict(105, 100).verdict, "neutral")

    def test_a_zero_variance_makes_any_move_a_verdict(self):
        self.assertEqual(self.verdict(101, 100, variance=0).verdict, "regressed")
        self.assertEqual(self.verdict(99, 100, variance=0).verdict, "improved")
        self.assertEqual(self.verdict(100, 100, variance=0).verdict, "neutral")

    def test_a_zero_baseline_admits_no_proportion(self):
        """A fraction of zero has no meaning, and zero is a real measurement for a count."""
        self.assertEqual(self.verdict(5, 0).verdict, "regressed")
        self.assertEqual(self.verdict(0, 0).verdict, "neutral")

    def test_a_zero_baseline_on_a_higher_is_better_budget(self):
        """The limit has to move with the direction: for higher-is-better it is a floor, so
        a limit of 1000 would make every small value over-budget before the baseline was
        ever consulted."""
        self.assertEqual(
            self.verdict(5, 0, direction="higher_is_better", limit=0).verdict, "neutral")
        self.assertEqual(
            self.verdict(-5, 0, direction="higher_is_better", limit=-1000).verdict,
            "regressed")

    def test_drift_reports_no_proportion_against_a_zero_baseline(self):
        """Checked directly, because the verdict path reaches it only after the limit."""
        for direction in metron.DIRECTIONS:
            with self.subTest(direction=direction):
                moved, regressed = metron.drift(5, 0, direction)
                self.assertIsNone(moved)
                self.assertEqual(regressed, direction == "lower_is_better")
        moved, regressed = metron.drift(0, 0, "lower_is_better")
        self.assertIsNone(moved)
        self.assertFalse(regressed)

    def test_drift_is_a_fraction_of_the_baseline(self):
        moved, regressed = metron.drift(110, 100, "lower_is_better")
        self.assertAlmostEqual(moved, 0.1)
        self.assertTrue(regressed)
        moved, regressed = metron.drift(90, 100, "lower_is_better")
        self.assertAlmostEqual(moved, 0.1)
        self.assertFalse(regressed)

    def test_no_baseline_entry_is_neutral_rather_than_a_failure(self):
        """A budget declared today has nothing to drift from. Failing it would block the
        commit that introduces it."""
        found = metron.compare([self.budget()], {"a": 900}, {})
        self.assertEqual(found[0].verdict, "neutral")
        self.assertIn("no baseline", found[0].detail)

    def test_the_limit_is_checked_before_the_baseline(self):
        """A value past the ceiling fails as over-budget even when it improved."""
        found = metron.compare([self.budget()], {"a": 1200}, {"a": 5000})
        self.assertEqual(found[0].verdict, "over-budget")

    def test_a_value_exactly_at_the_limit_is_not_over_budget(self):
        self.assertEqual(self.verdict(1000, 1000).verdict, "neutral")

    def test_a_higher_is_better_limit_is_a_floor(self):
        found = metron.compare(
            [self.budget(direction="higher_is_better", limit=40)], {"a": 39}, {"a": 50})
        self.assertEqual(found[0].verdict, "over-budget")

    def test_worse_reads_the_direction(self):
        self.assertTrue(metron.worse(11, 10, "lower_is_better"))
        self.assertFalse(metron.worse(9, 10, "lower_is_better"))
        self.assertTrue(metron.worse(9, 10, "higher_is_better"))
        self.assertFalse(metron.worse(11, 10, "higher_is_better"))


class CheckCommandTests(TempFiles):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def check(self, fixture, *extra):
        return self.run_cli("check", "--budgets", str(BUDGETS),
                            "--baseline", str(BASELINE),
                            "--run", str(RUNS / f"{fixture}.json"), *extra)

    def test_the_failing_fixtures_exit_one(self):
        for fixture in ("regressed", "over-budget", "unmeasured", "undeclared",
                        "throughput-regressed"):
            with self.subTest(fixture=fixture):
                proc = self.check(fixture)
                self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)

    def test_the_passing_fixtures_exit_zero(self):
        for fixture in ("neutral", "improved"):
            with self.subTest(fixture=fixture):
                proc = self.check(fixture)
                self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    def test_the_report_names_the_budget_and_the_margin(self):
        out = self.check("regressed").stdout
        self.assertIn("harvest.usdc.wall_clock", out)
        self.assertIn("15.0% worse", out)
        self.assertIn("past 5.0%", out)

    def test_the_report_counts_the_failures(self):
        self.assertIn("1 of 3 budget(s) failed", self.check("regressed").stdout)
        self.assertIn("3 budget(s), none failed", self.check("neutral").stdout)

    def test_json_output_carries_the_numbers(self):
        found = json.loads(self.check("regressed", "--format", "json").stdout)
        self.assertFalse(found["ok"])
        self.assertEqual(found["failed"], ["harvest.usdc.wall_clock"])
        first = found["verdicts"][0]
        self.assertEqual((first["run"], first["baseline"]), (1150, 1000))

    def test_a_check_without_a_baseline_still_holds_the_limit(self):
        proc = self.run_cli("check", "--budgets", str(BUDGETS),
                            "--run", str(RUNS / "over-budget.json"))
        self.assertEqual(proc.returncode, 1)
        self.assertIn("over-budget", proc.stdout)

    def test_a_malformed_baseline_exits_two(self):
        bad = self.write_raw("bad.json", "{")
        proc = self.run_cli("check", "--budgets", str(BUDGETS),
                            "--baseline", bad, "--run", str(RUNS / "neutral.json"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("baseline", proc.stderr)


class RecordCommandTests(TempFiles):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def test_a_run_is_appended_rather_than_replacing(self):
        ledger = str(Path(self.tmp.name) / "ledger.jsonl")
        for fixture, note in (("regressed", "attempt one"), ("improved", "attempt two")):
            proc = self.run_cli("record", "--budgets", str(BUDGETS),
                                "--baseline", str(BASELINE),
                                "--run", str(RUNS / f"{fixture}.json"),
                                "--ledger", ledger, "--note", note)
            self.assertEqual(proc.returncode, 0, proc.stderr)
        lines = Path(ledger).read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(len(lines), 2)
        notes = [json.loads(line)["note"] for line in lines]
        self.assertEqual(notes, ["attempt one", "attempt two"])

    def test_the_ledger_keeps_the_reverted_attempt(self):
        """SKILL.md asks for this by name: a revert leaves no trace in history, which is why
        the same dead idea comes back next quarter."""
        ledger = str(Path(self.tmp.name) / "ledger.jsonl")
        self.run_cli("record", "--budgets", str(BUDGETS), "--baseline", str(BASELINE),
                     "--run", str(RUNS / "regressed.json"), "--ledger", ledger)
        entry = json.loads(Path(ledger).read_text(encoding="utf-8").strip())
        self.assertIn("regressed", [v["verdict"] for v in entry["verdicts"]])

    def test_recording_does_not_change_the_baseline(self):
        ledger = str(Path(self.tmp.name) / "ledger.jsonl")
        baseline = Path(self.tmp.name) / "baseline.json"
        baseline.write_text(BASELINE.read_text(encoding="utf-8"), encoding="utf-8")
        before = baseline.read_text(encoding="utf-8")
        self.run_cli("record", "--budgets", str(BUDGETS), "--baseline", str(baseline),
                     "--run", str(RUNS / "improved.json"), "--ledger", ledger)
        self.assertEqual(baseline.read_text(encoding="utf-8"), before)

    def test_promote_writes_the_run_over_the_baseline(self):
        ledger = str(Path(self.tmp.name) / "ledger.jsonl")
        baseline = Path(self.tmp.name) / "baseline.json"
        baseline.write_text(BASELINE.read_text(encoding="utf-8"), encoding="utf-8")
        proc = self.run_cli("record", "--budgets", str(BUDGETS), "--baseline", str(baseline),
                            "--run", str(RUNS / "improved.json"), "--ledger", ledger,
                            "--promote")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("promoted", proc.stdout)
        found = json.loads(baseline.read_text(encoding="utf-8"))["measurements"]
        self.assertEqual(found["harvest.usdc.wall_clock"], 700)

    def test_a_failed_promote_leaves_the_baseline_alone(self):
        """The baseline is what every later comparison is measured against, so a write that
        dies partway is worse than one that never started: the previous value is gone and
        nothing says so."""
        baseline = Path(self.tmp.name) / "baseline.json"
        baseline.write_text(BASELINE.read_text(encoding="utf-8"), encoding="utf-8")
        before = baseline.read_text(encoding="utf-8")
        real = os.replace

        def refuse(source, target):
            raise OSError("device full")

        os.replace = refuse
        try:
            with self.assertRaises(OSError):
                metron.write_atomically(str(baseline), '{"measurements": {"a": 1}}')
        finally:
            os.replace = real
        self.assertEqual(baseline.read_text(encoding="utf-8"), before)
        leftovers = [n for n in os.listdir(self.tmp.name) if n.startswith(".metron-")]
        self.assertEqual(leftovers, [])

    def test_a_successful_write_replaces_the_whole_file(self):
        baseline = Path(self.tmp.name) / "baseline.json"
        baseline.write_text('{"measurements": {"a": 1, "b": 2}}\n', encoding="utf-8")
        metron.write_atomically(str(baseline), '{"measurements": {"a": 9}}\n')
        found = json.loads(baseline.read_text(encoding="utf-8"))
        self.assertEqual(found["measurements"], {"a": 9})

    def test_promote_without_a_baseline_is_refused(self):
        ledger = str(Path(self.tmp.name) / "ledger.jsonl")
        proc = self.run_cli("record", "--budgets", str(BUDGETS),
                            "--run", str(RUNS / "improved.json"), "--ledger", ledger,
                            "--promote")
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--baseline", proc.stderr)

    def test_a_note_cannot_break_one_object_per_line(self):
        """The ledger's whole shape is one JSON object per line, so a note carrying a
        newline would split one entry into two unparseable ones if it were not escaped."""
        ledger = Path(self.tmp.name) / "ledger.jsonl"
        notes = ["two\nlines", 'a "quote"', "\u00fc\u00f1\u00ef\u00e7\u00f8d\u00e9",
                 "\r\n", "tab\there"]
        for note in notes:
            metron.append_ledger(str(ledger), {"note": note, "measurements": {"a": 1}})
        lines = ledger.read_text(encoding="utf-8").strip().split("\n")
        self.assertEqual(len(lines), len(notes))
        self.assertEqual([json.loads(line)["note"] for line in lines], notes)

    def test_a_ledger_in_a_missing_directory_is_refused(self):
        proc = self.run_cli("record", "--budgets", str(BUDGETS),
                            "--run", str(RUNS / "neutral.json"),
                            "--ledger", str(Path(self.tmp.name) / "absent" / "l.jsonl"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("does not exist", proc.stderr)

    def test_record_reports_a_failing_run_without_failing(self):
        """record writes the ledger; check is the gate. A reverted attempt has to be
        recordable or the ledger only ever holds the wins."""
        ledger = str(Path(self.tmp.name) / "ledger.jsonl")
        proc = self.run_cli("record", "--budgets", str(BUDGETS), "--baseline", str(BASELINE),
                            "--run", str(RUNS / "regressed.json"), "--ledger", ledger)
        self.assertEqual(proc.returncode, 0)


class TimeCommandTests(TempFiles):
    """The recorder opens the plugin's one subprocess boundary. Each case here is a
    way the number or the file could be wrong: a shell reading the argv, a child
    that outlives the run, a stream that never ends, a failure written as a result."""

    NAME = "harvest.usdc.wall_clock"

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args],
                              capture_output=True, text=True)

    def time(self, *options, command=(), out="run.json"):
        """`time` on `command`, returning the process and the path it was to write."""
        path = Path(self.tmp.name) / out
        proc = self.run_cli("time", "--name", self.NAME, "--out", str(path), *options,
                            "--", *command)
        return proc, path

    def python(self, source):
        """A command running `source` in a fresh interpreter, as the caller would."""
        return (sys.executable, "-c", source)

    def one_budget(self, limit=60000):
        return self.write("one-budget.json", {"budgets": [
            budget(unit="ms", limit=limit),
        ]})

    def wait_gone(self, pid, seconds):
        """True once `pid` no longer exists, polling for up to `seconds`."""
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                return True
            time.sleep(0.05)
        return False

    def test_a_clean_command_writes_the_run_file(self):
        proc, path = self.time(command=self.python("pass"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(sorted(document), ["measurements", "recorder"])
        value = document["measurements"][self.NAME]
        self.assertIsInstance(value, float)
        self.assertTrue(metron.number(value))
        self.assertGreater(value, 0)
        # With one repetition the median is that sample; a value that differed
        # would have been computed from something the file does not show.
        sample = document["recorder"]["repetitions"][0]["wall_clock_ms"]
        self.assertEqual(value, sample)
        self.assertEqual(sample, round(sample, 3))

    def test_the_recorder_block_answers_what_ran_under_which_bounds(self):
        """Ephoros' question for this file: which command produced the number, from
        where, under what timeout, and what each repetition did."""
        proc, path = self.time("--timeout-seconds", "30", "--expect-exit", "0",
                               command=self.python("pass"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        recorder = json.loads(path.read_text(encoding="utf-8"))["recorder"]
        self.assertEqual(sorted(recorder), sorted([
            "schema", "argv", "cwd", "repeat", "warmup", "timeout_ms", "expect_exit",
            "unit", "aggregation", "repetitions", "recorded_at", "platform", "python",
        ]))
        self.assertEqual(recorder["schema"], "metron-timed-run/v1")
        self.assertEqual(recorder["argv"], list(self.python("pass")))
        self.assertEqual(recorder["cwd"], os.getcwd())
        self.assertEqual(recorder["repeat"], 1)
        self.assertEqual(recorder["warmup"], 0)
        self.assertEqual(recorder["timeout_ms"], 30000)
        self.assertEqual(recorder["expect_exit"], 0)
        self.assertEqual(recorder["unit"], "ms")
        self.assertEqual(recorder["aggregation"], "median")
        self.assertEqual(len(recorder["repetitions"]), 1)
        self.assertEqual(sorted(recorder["repetitions"][0]), sorted([
            "index", "wall_clock_ms", "exit", "stdout_bytes", "stderr_bytes",
        ]))
        self.assertEqual(recorder["repetitions"][0]["index"], 1)
        self.assertEqual(recorder["repetitions"][0]["exit"], 0)
        self.assertEqual(recorder["python"], sys.version.split()[0])
        self.assertTrue(recorder["recorded_at"].endswith("+00:00"))

    def test_check_reads_the_run_file_unedited(self):
        """The whole point: a run file the recorder wrote passes through the check with
        no hand edit. A stray number beside `measurements` would be refused there."""
        proc, path = self.time(command=self.python("pass"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        found = metron.load_measurements(str(path), "run")
        self.assertEqual(list(found), [self.NAME])
        proc = self.run_cli("check", "--budgets", self.one_budget(), "--run", str(path))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("neutral", proc.stdout)

    def test_the_output_byte_counts_are_recorded_but_not_the_bytes(self):
        """A recorder that kept the streams would copy whatever the workload printed
        into the run file, credential included."""
        secret = Path(self.tmp.name) / "secret.txt"
        secret.write_text("SECRET-TOKEN", encoding="utf-8")
        proc, path = self.time(command=(
            *self.python("import sys; sys.stdout.write('o' * 10); "
                         "sys.stderr.write(open(sys.argv[1]).read())"),
            str(secret),
        ))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        text = path.read_text(encoding="utf-8")
        entry = json.loads(text)["recorder"]["repetitions"][0]
        self.assertEqual(entry["stdout_bytes"], 10)
        self.assertEqual(entry["stderr_bytes"], 12)
        self.assertNotIn("SECRET-TOKEN", text)

    def test_a_note_is_kept_only_when_given(self):
        proc, path = self.time("--note", "cold cache", command=self.python("pass"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(document["note"], "cold cache")
        self.assertEqual(sorted(document), ["measurements", "note", "recorder"])

    def test_the_argv_reaches_the_command_as_written(self):
        """No shell reads the argv. A word that a shell would expand or split arrives
        at the command as exactly those characters, and only the first `--` is the
        recorder's: a command with its own `--` keeps it."""
        landing = Path(self.tmp.name) / "argv.txt"
        words = ["$HOME; echo * | cat > /dev/null && `id`", "--", "after"]
        proc, _path = self.time(command=(
            *self.python("import sys, pathlib, json; "
                         "pathlib.Path(sys.argv[1]).write_text(json.dumps(sys.argv[2:]))"),
            str(landing), *words,
        ))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(landing.read_text(encoding="utf-8")), words)

    def test_the_script_never_hands_a_command_to_a_shell(self):
        """Phylax P001 and P002 in the test suite's own words: every subprocess call in
        the script takes a list and never a string, and none asks for a shell."""
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        calls = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "subprocess"
        ]
        self.assertEqual([call.func.attr for call in calls], ["Popen"])
        call = calls[0]
        self.assertIsInstance(call.args[0], ast.Name)
        keywords = {keyword.arg: keyword.value for keyword in call.keywords}
        self.assertNotIn("shell", keywords)
        self.assertIs(keywords["start_new_session"].value, True)
        self.assertNotIn("os.system", SCRIPT.read_text(encoding="utf-8"))

    def test_the_run_is_taken_from_the_given_cwd(self):
        inside = Path(self.tmp.name) / "inside"
        inside.mkdir()
        landing = inside / "cwd.txt"
        proc, path = self.time("--cwd", str(inside), command=(
            *self.python("import os, pathlib; pathlib.Path('cwd.txt').write_text(os.getcwd())"),
        ))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(Path(landing.read_text(encoding="utf-8")).resolve(),
                         inside.resolve())
        recorder = json.loads(path.read_text(encoding="utf-8"))["recorder"]
        self.assertEqual(recorder["cwd"], str(inside))

    def test_a_wrong_exit_is_refused_and_no_file_is_written(self):
        proc, path = self.time(command=self.python("import sys; sys.exit(3)"))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stderr.count("\n"), 1)
        self.assertIn("repetition 1", proc.stderr)
        self.assertIn("exit", proc.stderr)
        self.assertFalse(path.exists())

    def test_the_expected_exit_is_the_callers_to_choose(self):
        """A workload whose success is exit 3 is still a workload."""
        proc, path = self.time("--expect-exit", "3",
                               command=self.python("import sys; sys.exit(3)"))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["recorder"]
                         ["repetitions"][0]["exit"], 3)

    def test_a_command_past_the_timeout_is_killed_and_refused(self):
        started = time.monotonic()
        proc, path = self.time("--timeout-seconds", "1",
                               command=self.python("import time; time.sleep(30)"))
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("repetition 1", proc.stderr)
        self.assertIn("timeout", proc.stderr)
        self.assertFalse(path.exists())

    def test_a_stream_past_the_cap_is_killed_and_refused(self):
        """A command that never stops writing would otherwise never be seen to
        finish, and one that writes a great deal would land in memory."""
        started = time.monotonic()
        proc, path = self.time(command=self.python(
            "import sys\n"
            "while True: sys.stdout.write('x' * 65536)"
        ))
        self.assertLess(time.monotonic() - started, 10)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("repetition 1", proc.stderr)
        self.assertIn("output-cap", proc.stderr)
        self.assertFalse(path.exists())

    def test_a_grandchild_does_not_outlive_a_command_that_exits_zero(self):
        """Without the teardown the readers block on the pipe the grandchild still
        holds, so the recorded duration becomes its lifetime and the grandchild
        outlives the run that started it."""
        pid_file = Path(self.tmp.name) / "grandchild.pid"
        proc, path = self.time(command=self.python(
            "import os, sys, time; "
            "child = os.fork() == 0; "
            f"(open({str(pid_file)!r}, 'w').write(str(os.getpid())), time.sleep(30), "
            "os._exit(0)) if child else "
            "(print('parent-done'), sys.stdout.flush(), os._exit(0))"
        ))
        self.assertEqual(proc.returncode, 0, proc.stderr)
        document = json.loads(path.read_text(encoding="utf-8"))
        self.assertLess(document["recorder"]["repetitions"][0]["wall_clock_ms"], 4000)
        pid = int(pid_file.read_text(encoding="utf-8"))
        self.assertTrue(self.wait_gone(pid, 5), f"grandchild {pid} survived the run")

    def test_a_grandchild_that_leaves_the_process_group_is_refused(self):
        """A process group teardown cannot reach a grandchild that called `setsid`. It
        survives and holds the command's pipes, which is both a boundary the recorder
        claims and the number the check reads, so the repetition is refused rather
        than recorded with an inflated duration."""
        pid_file = Path(self.tmp.name) / "escapee.pid"
        proc, path = self.time(command=self.python(
            "import os, sys, time; "
            "child = os.fork() == 0; "
            f"(os.setsid(), open({str(pid_file)!r}, 'w').write(str(os.getpid())), "
            "time.sleep(30), os._exit(0)) if child else "
            "(print('parent-done'), sys.stdout.flush(), os._exit(0))"
        ))
        try:
            self.assertEqual(proc.returncode, 1)
            self.assertIn("repetition 1", proc.stderr)
            self.assertIn("escaped", proc.stderr)
            self.assertFalse(path.exists())
        finally:
            # The escapee is the case under test, not a process to leave behind.
            try:
                os.kill(int(pid_file.read_text(encoding="utf-8")), 9)
            except (OSError, ValueError):
                pass

    def test_a_previous_run_file_survives_a_failure(self):
        """A failed run that overwrote the last good file would leave the check reading
        a number nobody produced this time; one that truncated it would leave nothing
        the check could refuse by name."""
        before = '{"measurements": {"harvest.usdc.wall_clock": 1.5}}\n'
        path = Path(self.tmp.name) / "run.json"
        path.write_text(before, encoding="utf-8")
        proc, _path = self.time(command=self.python("import sys; sys.exit(1)"))
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(path.read_text(encoding="utf-8"), before)
        leftovers = [n for n in os.listdir(self.tmp.name) if n.startswith(".metron-")]
        self.assertEqual(leftovers, [])

    def test_a_timeout_outside_its_bounds_is_refused_before_anything_runs(self):
        landing = Path(self.tmp.name) / "ran.txt"
        for value in ("0", "-1", "3601", "1.5", "ten"):
            with self.subTest(timeout=value):
                proc, path = self.time("--timeout-seconds", value, command=(
                    *self.python("import pathlib, sys; pathlib.Path(sys.argv[1]).touch()"),
                    str(landing),
                ))
                self.assertEqual(proc.returncode, 2)
                self.assertIn("timeout-seconds", proc.stderr)
                self.assertFalse(path.exists())
                self.assertFalse(landing.exists())
        for value in ("1", "3600"):
            with self.subTest(timeout=value):
                proc, _path = self.time("--timeout-seconds", value,
                                        command=self.python("pass"))
                self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_a_missing_separator_is_refused(self):
        path = Path(self.tmp.name) / "run.json"
        proc = self.run_cli("time", "--name", self.NAME, "--out", str(path),
                            *self.python("pass"))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("--", proc.stderr)
        self.assertFalse(path.exists())

    def test_an_empty_command_is_refused(self):
        proc, path = self.time(command=())
        self.assertEqual(proc.returncode, 2)
        self.assertIn("command", proc.stderr)
        self.assertFalse(path.exists())

    def test_a_command_that_cannot_start_is_a_bad_invocation(self):
        """Nothing ran, so there is no number to refuse: this is 2, not 1."""
        missing = str(Path(self.tmp.name) / "no-such-binary")
        proc, path = self.time(command=(missing,))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("could not start", proc.stderr)
        self.assertFalse(path.exists())

    def test_an_unwritable_out_is_refused_before_the_command_runs(self):
        landing = Path(self.tmp.name) / "ran.txt"
        proc, path = self.time(out="absent/run.json", command=(
            *self.python("import pathlib, sys; pathlib.Path(sys.argv[1]).touch()"),
            str(landing),
        ))
        self.assertEqual(proc.returncode, 2)
        self.assertIn("run file", proc.stderr)
        self.assertFalse(path.exists())
        self.assertFalse(landing.exists())



if __name__ == "__main__":
    unittest.main()
