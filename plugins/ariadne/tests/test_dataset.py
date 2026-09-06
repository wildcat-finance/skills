"""Gates 2 and 5 for the dataset predicate, and its coverage and inputs checks."""

import hashlib
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import statement  # noqa: E402
from ariadne_lib.predicates import dataset  # noqa: E402

EVENTS = {"sha256": hashlib.sha256(b"events").hexdigest()}
MAPPING = {"sha256": hashlib.sha256(b"mapping").hexdigest()}
PREVIOUS = {"sha256": hashlib.sha256(b"previous release").hexdigest()}
PARAMETERS = {"sha256": hashlib.sha256(b"parameters").hexdigest()}
CAPTURE = {"sha256": hashlib.sha256(b"capture").hexdigest()}


def predicate(**overrides):
    out = {
        "producer": {
            "tool": "tabularium",
            "tool_version": "0.3.0",
            "command": ["python3", "tabularium.py", "release"],
            "parameters_digest": PARAMETERS,
        },
        "inputs": [
            {
                "name": "aave-v4 capture",
                "locator": "alexandria://aave-v4/2024-01",
                "digest": CAPTURE,
            }
        ],
        "dataset_subjects": [
            {
                "name": "credit-events",
                "path": "events.jsonl",
                "digest": EVENTS,
                "record_count": 8412,
            },
            {
                "name": "mapping-provenance",
                "path": "mapping.json",
                "digest": MAPPING,
                "record_count": 37,
            },
        ],
        "coverage": {
            "dimension": "block",
            "start": 11370000,
            "end": 15000000,
            "gaps": [
                {
                    "start": 12000000,
                    "end": 12000100,
                    "reason": "archive node returned no receipts for this range",
                }
            ],
        },
        "deltas": {
            "baseline": {"name": "aave-v4-v1", "digest": PREVIOUS},
            "current": {"name": "aave-v4-v2", "digest": EVENTS},
            "records": {"added": ["0xabc"], "removed": [], "changed": []},
        },
        "claims": [],
        "commands": [],
    }
    out.update(overrides)
    return out


def built(predicate_body, subject=None):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": subject
            or [
                {"name": "events.jsonl", "digest": EVENTS},
                {"name": "mapping.json", "digest": MAPPING},
            ],
            "predicateType": dataset.TYPE,
            "predicate": predicate_body,
        }
    )


def gate(number, predicate_body, subject=None):
    for found in dataset.check(built(predicate_body, subject)):
        if found.number == number:
            return found
    raise AssertionError("no gate %r" % number)


def named(name, predicate_body, subject=None):
    for found in dataset.check(built(predicate_body, subject)):
        if found.name == name:
            return found
    raise AssertionError("no check named %r" % name)


class Stub(object):
    """The two attributes every gate here reads, and nothing else.

    Used to reach the type guards that `Statement` would otherwise refuse before
    a gate ever saw the value.
    """

    def __init__(self, predicate):
        self.predicate = predicate
        self.subjects = []

    def covers(self, digest):
        return False


def without(block, field):
    """A copy of a predicate block with one field removed."""
    out = dict(block)
    out.pop(field, None)
    return out


class GateTwoTests(unittest.TestCase):
    def test_a_complete_producer_record_passes(self):
        found = gate(2, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("tabularium 0.3.0", found.detail)
        self.assertIn("2 released file(s)", found.detail)

    def test_a_tool_version_alone_is_not_a_producer_record(self):
        body = predicate(producer={"tool": "tabularium", "tool_version": "0.3.0"})
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("command", found.detail)
        self.assertIn("parameters_digest", found.detail)

    def test_a_producer_command_that_is_not_an_argv_fails(self):
        """An empty list is caught one step earlier, by the absent-field check, so
        this asserts the fault names the field rather than a fixed sentence."""
        for value in ("python3 tabularium.py release", ["forge", ""], [], ["forge", 3]):
            body = predicate()
            body["producer"]["command"] = value
            with self.subTest(command=repr(value)):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn("command", found.detail)

    def test_an_argv_carrying_an_empty_word_is_not_what_ran(self):
        for word in ("", "   ", "\t"):
            body = predicate()
            body["producer"]["command"] = ["forge", word]
            with self.subTest(word=repr(word)):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn("argv of non-empty strings", found.detail)

    def test_a_producer_tool_or_version_of_whitespace_names_nothing(self):
        for field in ("tool", "tool_version"):
            body = predicate()
            body["producer"][field] = "   "
            with self.subTest(field=field):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn("must name something", found.detail)

    def test_an_input_name_or_locator_that_names_nothing_fails(self):
        for field in ("name", "locator"):
            for value in ("   ", 1.5, True):
                body = predicate()
                body["inputs"][0][field] = value
                with self.subTest(field=field, value=repr(value)):
                    found = gate(2, body)
                    self.assertFalse(found.passed)
                    self.assertIn("must name something", found.detail)

    def test_a_released_file_without_a_name_fails(self):
        body = predicate()
        body["dataset_subjects"][0]["name"] = "   "
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("has no name", found.detail)

    def test_a_path_of_whitespace_is_not_a_path(self):
        body = predicate()
        body["dataset_subjects"][0]["path"] = "   "
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("release-relative", found.detail)

    def test_a_gap_reason_that_is_not_a_string_is_no_reason(self):
        for value in (1.5, 0, True, ["no receipts"]):
            body = predicate()
            body["coverage"]["gaps"] = [{"start": 12000000, "end": 12000100, "reason": value}]
            with self.subTest(reason=repr(value)):
                self.assertFalse(named("coverage", body).passed)

    def test_a_record_identifier_that_identifies_nothing_fails(self):
        for key in ("added", "removed"):
            for value in ("", "   ", None, 1.5, True):
                body = predicate()
                body["deltas"]["records"] = {"added": [], "removed": [], "changed": []}
                body["deltas"]["records"][key] = [value]
                with self.subTest(key=key, value=repr(value)):
                    found = gate(5, body)
                    self.assertFalse(found.passed)
                    self.assertIn("identifies no record", found.detail)

    def test_a_changed_record_whose_side_identifies_nothing_fails(self):
        for side in ("baseline", "current"):
            body = predicate()
            body["deltas"]["records"]["changed"] = [{"baseline": "x", "current": "y"}]
            body["deltas"]["records"]["changed"][0][side] = "   "
            with self.subTest(side=side):
                found = gate(5, body)
                self.assertFalse(found.passed)
                self.assertIn("identifies no record", found.detail)

    def test_a_parameters_digest_that_is_not_hex_fails(self):
        body = predicate()
        body["producer"]["parameters_digest"] = {"sha256": "NOTHEX"}
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("parameters_digest", found.detail)

    def test_a_released_file_the_statement_does_not_cover_fails(self):
        body = predicate()
        body["dataset_subjects"][0]["digest"] = {
            "sha256": hashlib.sha256(b"unlisted").hexdigest()
        }
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_an_empty_released_file_list_fails(self):
        found = gate(2, predicate(dataset_subjects=[]))
        self.assertFalse(found.passed)
        self.assertIn("non-empty array", found.detail)

    def test_a_released_file_missing_its_record_count_fails(self):
        body = predicate()
        body["dataset_subjects"][0] = without(body["dataset_subjects"][0], "record_count")
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("record_count", found.detail)

    def test_a_released_file_with_no_records_is_allowed(self):
        """Zero is a count. Reading it as absent would refuse an empty slice of a
        dataset, which is a real thing to publish."""
        body = predicate()
        body["dataset_subjects"][0]["record_count"] = 0
        found = gate(2, body)
        self.assertTrue(found.passed, found.detail)

    def test_a_record_count_that_is_not_a_whole_number_fails(self):
        body = predicate()
        body["dataset_subjects"][0]["record_count"] = "8412"
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("whole number", found.detail)

    def test_a_boolean_record_count_is_not_a_whole_number(self):
        body = predicate()
        body["dataset_subjects"][0]["record_count"] = True
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("whole number", found.detail)

    def test_a_negative_record_count_fails(self):
        """The published schema said minimum 0 and the gate did not check, so a
        statement claiming minus five records verified clean."""
        body = predicate()
        body["dataset_subjects"][0]["record_count"] = -5
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("whole number of records", found.detail)

    def test_the_same_path_listed_twice_fails(self):
        """One file cannot carry two digests, and the release digest is over this
        listing."""
        body = predicate()
        body["dataset_subjects"][1]["path"] = body["dataset_subjects"][0]["path"]
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("listed twice", found.detail)

    def test_a_path_that_leaves_the_release_fails(self):
        """A consumer resolves this against a release directory. The capture path
        never writes one of these; a statement written by hand can."""
        for bad in ("../../etc/passwd", "/etc/passwd", "by-pool/../../outside.jsonl"):
            body = predicate()
            body["dataset_subjects"][0]["path"] = bad
            with self.subTest(path=bad):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn("release-relative", found.detail)

    def test_a_backslash_traversal_is_refused(self):
        """A single backslash separates segments on Windows. This function
        normalised only a doubled backslash, so `by-pool\\..\\..\\outside.jsonl`
        reached a POSIX consumer as one odd filename and a Windows consumer as a
        traversal out of the release. Found by sweeping the same function in the
        state-fixture predicate, which was copied from this one, in round 5 of that
        step."""
        for bad in ("by-pool\\..\\..\\outside.jsonl", "..\\outside.jsonl",
                    "\\\\server\\share\\x.jsonl"):
            body = predicate()
            body["dataset_subjects"][0]["path"] = bad
            with self.subTest(path=bad):
                found = gate(2, body)
                self.assertFalse(found.passed)
                self.assertIn("release-relative", found.detail)

    def test_a_backslash_inside_a_name_is_not_a_traversal(self):
        """Refusing every backslash would refuse a legitimate POSIX filename that
        happens to contain one."""
        body = predicate()
        body["dataset_subjects"][0]["path"] = "odd\\name.jsonl"
        self.assertTrue(gate(2, body).passed)

    def test_a_nested_release_relative_path_is_allowed(self):
        body = predicate()
        body["dataset_subjects"][0]["path"] = "by-pool/pool-a.jsonl"
        self.assertTrue(gate(2, body).passed)

    def test_two_files_with_the_same_content_are_allowed(self):
        """Duplicate content is a real thing to publish. Only a duplicate path is
        incoherent."""
        body = predicate()
        body["dataset_subjects"][1]["digest"] = body["dataset_subjects"][0]["digest"]
        self.assertTrue(gate(2, body).passed)

    def test_an_input_missing_its_locator_fails(self):
        body = predicate()
        body["inputs"][0] = without(body["inputs"][0], "locator")
        found = gate(2, body)
        self.assertFalse(found.passed)
        self.assertIn("locator", found.detail)

    def test_a_release_derived_from_nothing_passes_with_an_empty_input_list(self):
        found = gate(2, predicate(inputs=[]))
        self.assertTrue(found.passed, found.detail)
        self.assertIn("0 input(s)", found.detail)

    def test_a_predicate_that_is_not_an_object_fails_without_raising(self):
        """`Statement` refuses a non-object predicate at construction, so a real
        statement never carries one. The guard stays, and is exercised through a
        stub, because these gates are also reachable from a caller assembling a
        predicate by hand."""
        found = [f for f in dataset.check(Stub("a dataset, honestly")) if f.number == 2]
        self.assertEqual(len(found), 1)
        self.assertFalse(found[0].passed)
        self.assertIn("no predicate", found[0].detail)

    def test_no_check_raises_on_a_predicate_that_is_not_an_object(self):
        for found in dataset.check(Stub(["not", "an", "object"])):
            with self.subTest(check=found.name):
                self.assertFalse(found.passed)


class GateFiveTests(unittest.TestCase):
    def test_a_comparison_naming_both_sides_passes(self):
        found = gate(5, predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("aave-v4-v2 against aave-v4-v1", found.detail)

    def test_an_absent_deltas_block_fails(self):
        body = predicate()
        body.pop("deltas")
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("no deltas block", found.detail)

    def test_a_first_release_passes_with_a_null_baseline_and_a_reason(self):
        found = gate(
            5,
            predicate(
                deltas={
                    "baseline": None,
                    "current": {"name": "aave-v4-v1", "digest": EVENTS},
                    "reason": "first release of this dataset",
                }
            ),
        )
        self.assertTrue(found.passed, found.detail)
        self.assertIn("first release", found.detail)

    def test_a_first_release_still_has_its_current_side_checked(self):
        """The null-baseline branch used to return before reaching the current
        side, so a first release could name a current side with no name and no
        digest and still verify clean."""
        for side, expected in (
            ({"digest": EVENTS}, "no name"),
            ({"name": "aave-v4-v1"}, "current side"),
            ({"name": "", "digest": EVENTS}, "no name"),
        ):
            with self.subTest(side=side):
                found = gate(
                    5,
                    predicate(
                        deltas={
                            "baseline": None,
                            "current": side,
                            "reason": "first release of this dataset",
                        }
                    ),
                )
                self.assertFalse(found.passed)
                self.assertIn(expected, found.detail)

    def test_a_first_release_naming_a_digest_the_statement_lacks_fails(self):
        found = gate(
            5,
            predicate(
                deltas={
                    "baseline": None,
                    "current": {
                        "name": "somebody else's release",
                        "digest": {"sha256": hashlib.sha256(b"elsewhere").hexdigest()},
                    },
                    "reason": "first release of this dataset",
                }
            ),
        )
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_a_release_compared_against_itself_fails(self):
        body = predicate()
        body["deltas"]["baseline"] = {"name": "aave-v4-v1", "digest": EVENTS}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("comparison against itself", found.detail)

    def test_a_null_baseline_without_a_reason_fails(self):
        found = gate(
            5,
            predicate(
                deltas={
                    "baseline": None,
                    "current": {"name": "aave-v4-v1", "digest": EVENTS},
                }
            ),
        )
        self.assertFalse(found.passed)
        self.assertIn("needs a reason", found.detail)

    def test_differences_against_a_null_baseline_fail(self):
        found = gate(
            5,
            predicate(
                deltas={
                    "baseline": None,
                    "current": {"name": "aave-v4-v1", "digest": EVENTS},
                    "reason": "first release of this dataset",
                    "records": {"added": ["0xabc"], "removed": [], "changed": []},
                }
            ),
        )
        self.assertFalse(found.passed)
        self.assertIn("against a null baseline", found.detail)

    def test_a_side_named_only_whitespace_fails(self):
        """`"   "` is truthy. `check_side` is shared by all three predicates and
        used a bare presence test, so a side could identify nothing and pass."""
        for side in ("baseline", "current"):
            for value in (" ", "   ", "\t"):
                body = predicate()
                body["deltas"][side] = dict(body["deltas"][side], name=value)
                with self.subTest(side=side, name=value):
                    found = gate(5, body)
                    self.assertFalse(found.passed)
                    self.assertIn("has no name", found.detail)

    def test_a_baseline_without_a_digest_fails(self):
        body = predicate()
        body["deltas"]["baseline"] = {"name": "aave-v4-v1"}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("baseline side", found.detail)

    def test_a_changed_record_naming_one_side_fails(self):
        body = predicate()
        body["deltas"]["records"]["changed"] = [{"current": "0xdef"}]
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("names no baseline", found.detail)

    def test_a_records_section_that_is_not_an_object_fails(self):
        body = predicate()
        body["deltas"]["records"] = "all of them"
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("must be an object", found.detail)

    def test_a_current_side_the_statement_does_not_cover_fails(self):
        body = predicate()
        body["deltas"]["current"] = {
            "name": "somebody else's release",
            "digest": {"sha256": hashlib.sha256(b"elsewhere").hexdigest()},
        }
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("not a subject of this statement", found.detail)

    def test_an_unknown_key_inside_records_fails(self):
        """An unknown section at the deltas level is refused, so an unknown key one
        level down cannot pass either. Both are undeclared content inside a digested
        comparison."""
        body = predicate()
        body["deltas"]["records"]["renamed"] = [{"baseline": "x", "current": "y"}]
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("unknown keys", found.detail)

    def test_the_declared_record_keys_are_allowed(self):
        body = predicate()
        body["deltas"]["records"] = {
            "added": ["0xa"],
            "removed": ["0xb"],
            "changed": [{"baseline": "0xc", "current": "0xd"}],
        }
        self.assertTrue(gate(5, body).passed)

    def test_an_unknown_delta_section_fails(self):
        body = predicate()
        body["deltas"]["columns"] = {"added": ["borrower"]}
        found = gate(5, body)
        self.assertFalse(found.passed)
        self.assertIn("unknown sections", found.detail)


class CoverageTests(unittest.TestCase):
    def test_an_interval_with_its_gaps_recorded_passes(self):
        found = named("coverage", predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("block 11370000 to 15000000", found.detail)
        self.assertIn("1 gap(s)", found.detail)

    def test_an_absent_coverage_block_fails(self):
        body = predicate()
        body.pop("coverage")
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("no coverage block", found.detail)

    def test_an_absent_gaps_key_fails(self):
        """The whole point. An interval printed with no gaps reads as complete,
        and this is the one field a dataset can most easily mislead with."""
        body = predicate()
        body["coverage"] = without(body["coverage"], "gaps")
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("no gaps block", found.detail)

    def test_an_empty_gap_list_passes_and_asserts_the_producer_looked(self):
        body = predicate()
        body["coverage"]["gaps"] = []
        found = named("coverage", body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("0 gap(s)", found.detail)

    def test_a_reversed_interval_fails(self):
        body = predicate()
        body["coverage"]["start"] = 15000000
        body["coverage"]["end"] = 11370000
        body["coverage"]["gaps"] = []
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("starts at 15000000 and ends at 11370000", found.detail)

    def test_a_gap_outside_the_bounds_fails(self):
        body = predicate()
        body["coverage"]["gaps"] = [
            {"start": 9000000, "end": 9000100, "reason": "before the deployment"}
        ]
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("outside the coverage", found.detail)

    def test_a_gap_without_a_reason_fails(self):
        body = predicate()
        body["coverage"]["gaps"] = [{"start": 12000000, "end": 12000100}]
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("reason", found.detail)

    def test_a_reversed_gap_fails(self):
        body = predicate()
        body["coverage"]["gaps"] = [
            {"start": 12000100, "end": 12000000, "reason": "transposed by hand"}
        ]
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("starts at 12000100 and ends at 12000000", found.detail)

    def test_overlapping_gaps_fail(self):
        body = predicate()
        body["coverage"]["gaps"] = [
            {"start": 12000000, "end": 12000200, "reason": "no receipts"},
            {"start": 12000100, "end": 12000300, "reason": "no receipts either"},
        ]
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("overlap", found.detail)

    def test_adjacent_gaps_do_not_overlap(self):
        body = predicate()
        body["coverage"]["gaps"] = [
            {"start": 12000000, "end": 12000100, "reason": "no receipts"},
            {"start": 12000101, "end": 12000200, "reason": "a separate outage"},
        ]
        found = named("coverage", body)
        self.assertTrue(found.passed, found.detail)

    def test_a_dimension_that_names_nothing_fails(self):
        for value in ("", "   ", 7, None):
            body = predicate()
            body["coverage"]["dimension"] = value
            with self.subTest(dimension=repr(value)):
                self.assertFalse(named("coverage", body).passed)

    def test_a_gap_reason_of_whitespace_is_no_reason(self):
        """`missing` reads "" as absent but not "   ". The reason is the record, so
        whitespace is treated the way gate 3 treats a whitespace claim reason."""
        body = predicate()
        body["coverage"]["gaps"] = [{"start": 12000000, "end": 12000100, "reason": "   "}]
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("reason", found.detail)

    def test_a_bound_that_is_not_a_whole_number_fails(self):
        body = predicate()
        body["coverage"]["end"] = "15000000"
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("whole number", found.detail)

    def test_a_gap_carrying_an_unknown_field_fails(self):
        body = predicate()
        body["coverage"]["gaps"][0]["confidence"] = "high"
        found = named("coverage", body)
        self.assertFalse(found.passed)
        self.assertIn("unknown fields", found.detail)

    def test_a_zero_bound_is_a_bound(self):
        body = predicate()
        body["coverage"]["start"] = 0
        body["coverage"]["gaps"] = [{"start": 0, "end": 10, "reason": "genesis"}]
        found = named("coverage", body)
        self.assertTrue(found.passed, found.detail)


class InputsTests(unittest.TestCase):
    def test_a_digested_input_passes(self):
        found = named("inputs", predicate())
        self.assertTrue(found.passed, found.detail)
        self.assertIn("1 digested", found.detail)

    def test_an_input_with_neither_digest_nor_disposition_fails(self):
        body = predicate()
        body["inputs"][0] = without(body["inputs"][0], "digest")
        found = named("inputs", body)
        self.assertFalse(found.passed)
        self.assertIn("neither a digest nor a disposition", found.detail)

    def test_an_input_recorded_absent_with_a_reason_passes(self):
        body = predicate()
        body["inputs"][0] = {
            "name": "aave-v4 capture",
            "locator": "alexandria://aave-v4/2024-01",
            "disposition": "redacted",
            "reason": "the upstream capture is under an embargo until 2027",
        }
        found = named("inputs", body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("1 recorded absent", found.detail)

    def test_an_input_recorded_absent_without_a_reason_fails(self):
        body = predicate()
        body["inputs"][0] = {
            "name": "aave-v4 capture",
            "locator": "alexandria://aave-v4/2024-01",
            "disposition": "skipped",
        }
        found = named("inputs", body)
        self.assertFalse(found.passed)
        self.assertIn("the reason is the record", found.detail)

    def test_an_input_passed_without_a_digest_fails(self):
        """`passed` was a one-word way around this check: it asserted the input was
        read while recording nothing about what was read, and the tally called it
        recorded absent."""
        body = predicate()
        body["inputs"][0] = {
            "name": "aave-v4 capture",
            "locator": "alexandria://aave-v4/2024-01",
            "disposition": "passed",
        }
        found = named("inputs", body)
        self.assertFalse(found.passed)
        self.assertIn("passed with no digest", found.detail)

    def test_an_input_passed_with_a_digest_is_the_ordinary_case(self):
        body = predicate()
        body["inputs"][0]["disposition"] = "passed"
        found = named("inputs", body)
        self.assertTrue(found.passed, found.detail)
        self.assertIn("1 digested", found.detail)

    def test_every_absence_disposition_needs_a_reason(self):
        for disposition in dataset.INPUT_DISPOSITIONS:
            body = predicate()
            body["inputs"][0] = {
                "name": "aave-v4 capture",
                "locator": "alexandria://aave-v4/2024-01",
                "disposition": disposition,
            }
            with self.subTest(disposition=disposition):
                found = named("inputs", body)
                self.assertFalse(found.passed)
                self.assertIn("the reason is the record", found.detail)

    def test_passed_is_not_an_absence_disposition(self):
        self.assertNotIn("passed", dataset.INPUT_DISPOSITIONS)

    def test_a_disposition_outside_the_vocabulary_fails(self):
        body = predicate()
        body["inputs"][0] = {
            "name": "aave-v4 capture",
            "locator": "alexandria://aave-v4/2024-01",
            "disposition": "probably fine",
        }
        found = named("inputs", body)
        self.assertFalse(found.passed)
        self.assertIn("outside", found.detail)

    def test_an_input_carrying_an_unknown_field_fails(self):
        body = predicate()
        body["inputs"][0]["fetched_at"] = "2026-01-01"
        found = named("inputs", body)
        self.assertFalse(found.passed)
        self.assertIn("unknown fields", found.detail)

    def test_an_absent_inputs_block_fails(self):
        body = predicate()
        body.pop("inputs")
        found = named("inputs", body)
        self.assertFalse(found.passed)
        self.assertIn("no inputs block", found.detail)


class FieldTests(unittest.TestCase):
    def test_a_predicate_within_the_shape_passes(self):
        found = named("predicate-fields", predicate())
        self.assertTrue(found.passed, found.detail)

    def test_a_field_outside_the_shape_fails(self):
        found = named("predicate-fields", predicate(licence="CC-BY-4.0"))
        self.assertFalse(found.passed)
        self.assertIn("licence", found.detail)

    def test_every_required_field_is_a_declared_field(self):
        self.assertEqual(set(dataset.REQUIRED_FIELDS) - set(dataset.PREDICATE_FIELDS), set())


class RegistrationTests(unittest.TestCase):
    def test_the_module_carries_what_the_registry_requires(self):
        self.assertTrue(dataset.TYPE.startswith("https://"))
        self.assertTrue(dataset.SUMMARY)
        self.assertTrue(callable(dataset.check))

    def test_the_check_reports_both_predicate_gates(self):
        numbers = [found.number for found in dataset.check(built(predicate()))]
        self.assertIn(2, numbers)
        self.assertIn(5, numbers)

    def test_a_clean_dataset_predicate_passes_every_check(self):
        failed = [f.name for f in dataset.check(built(predicate())) if not f.passed]
        self.assertEqual(failed, [])


if __name__ == "__main__":
    unittest.main()
