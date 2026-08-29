"""The dataset capture path: what it reads, what it refuses, and what it never guesses."""

import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, registry, statement, verify  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402  (registers the shipped predicates)
from ariadne_lib.capture import dataset as capture  # noqa: E402

FIXTURES = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "fixtures", "dataset-release"
)
V1 = os.path.join(FIXTURES, "v1")
V2 = os.path.join(FIXTURES, "v2")

COUNTS = {"mapping.json": 1}


def grab(release=V2, **overrides):
    kwargs = {
        "name": "goldfinch-credit-events-v2",
        "coverage_dimension": "block",
        "coverage_start": 11370000,
        "coverage_end": 15000000,
        "record_counts": COUNTS,
        "first_release_reason": "the first release of this dataset",
        "producer_tool": "tabularium",
        "producer_version": "0.3.0",
        "producer_command": ["python3", "scripts/tabularium.py", "release"],
    }
    kwargs.update(overrides)
    return capture.capture(release, **kwargs)


def report(document):
    raw = json.dumps(document).encode("utf-8")
    return verify.report(envelope.read(raw), registry.DEFAULT)


class CaptureTests(unittest.TestCase):
    def test_a_captured_release_verifies_clean(self):
        found = report(grab())
        self.assertTrue(found.ok, "\n".join(g.line() for g in found.gates if not g.passed))

    def test_a_captured_release_leaves_no_gate_unchecked(self):
        """The whole reason this predicate exists. A dataset statement used to be
        told that gates 2 and 5 belonged to a type nothing here knew."""
        self.assertEqual(report(grab()).unchecked, [])

    def test_the_predicate_type_is_the_dataset_type(self):
        self.assertEqual(grab()["predicateType"], capture.predicate.TYPE)

    def test_every_released_file_is_a_subject(self):
        document = grab()
        subjects = {json.dumps(s["digest"], sort_keys=True) for s in document["subject"]}
        for entry in document["predicate"]["dataset_subjects"]:
            with self.subTest(path=entry["path"]):
                self.assertIn(json.dumps(entry["digest"], sort_keys=True), subjects)

    def test_the_release_bundle_is_a_subject_of_its_own(self):
        document = grab()
        names = [s["name"] for s in document["subject"]]
        self.assertIn("goldfinch-credit-events-v2", names)

    def test_two_captures_of_the_same_tree_agree(self):
        """A statement that differs run to run cannot be compared with anything."""
        self.assertEqual(json.dumps(grab(), sort_keys=True), json.dumps(grab(), sort_keys=True))

    def test_the_files_come_out_sorted(self):
        paths = [e["path"] for e in grab()["predicate"]["dataset_subjects"]]
        self.assertEqual(paths, sorted(paths))


class RecordCountTests(unittest.TestCase):
    def test_line_delimited_json_is_counted_from_the_file(self):
        entries = {e["path"]: e for e in grab()["predicate"]["dataset_subjects"]}
        self.assertEqual(entries["events.jsonl"]["record_count"], 5)

    def test_the_earlier_release_has_fewer_records(self):
        entries = {e["path"]: e for e in grab(V1)["predicate"]["dataset_subjects"]}
        self.assertEqual(entries["events.jsonl"]["record_count"], 3)

    def test_a_stated_count_is_used_for_a_format_that_cannot_be_derived(self):
        entries = {e["path"]: e for e in grab()["predicate"]["dataset_subjects"]}
        self.assertEqual(entries["mapping.json"]["record_count"], 1)

    def test_a_count_that_is_neither_derivable_nor_stated_is_refused(self):
        """Guessing would put a number in the statement that nobody produced."""
        with self.assertRaises(capture.CaptureError) as caught:
            grab(record_counts={})
        self.assertIn("record count cannot be derived", str(caught.exception))
        self.assertIn("--record-count", str(caught.exception))

    def test_a_stated_count_overrides_a_derivable_one(self):
        entries = {
            e["path"]: e
            for e in grab(record_counts={"mapping.json": 1, "events.jsonl": 99})[
                "predicate"
            ]["dataset_subjects"]
        }
        self.assertEqual(entries["events.jsonl"]["record_count"], 99)


class LineCountTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, name, content):
        path = os.path.join(self.root, name)
        with open(path, "wb") as handle:
            handle.write(content)
        return path

    def test_a_trailing_newline_does_not_add_a_record(self):
        self.assertEqual(capture.line_count(self.write("a.jsonl", b'{"a":1}\n{"a":2}\n')), 2)

    def test_a_final_line_without_a_newline_is_still_a_record(self):
        self.assertEqual(capture.line_count(self.write("b.jsonl", b'{"a":1}\n{"a":2}')), 2)

    def test_an_empty_file_holds_no_records(self):
        self.assertEqual(capture.line_count(self.write("c.jsonl", b"")), 0)

    def test_a_file_larger_than_one_block_is_counted_in_blocks(self):
        """The read is in fixed blocks, so a release file never lands in memory
        whole. 4000 records is several blocks."""
        body = b"".join(b'{"n":%d}\n' % n for n in range(20000))
        self.assertGreater(len(body), 65536)
        self.assertEqual(capture.line_count(self.write("d.jsonl", body)), 20000)


class RefusalTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_a_release_that_is_not_a_directory_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(os.path.join(V2, "events.jsonl"))
        self.assertIn("is not a directory", str(caught.exception))

    def test_a_release_that_does_not_exist_is_refused(self):
        with self.assertRaises(capture.CaptureError):
            grab(os.path.join(self.root, "absent"))

    def test_an_empty_release_is_refused(self):
        empty = os.path.join(self.root, "empty")
        os.mkdir(empty)
        with self.assertRaises(capture.CaptureError) as caught:
            grab(empty, record_counts={})
        self.assertIn("holds no files", str(caught.exception))

    def test_a_symlink_out_of_the_release_is_refused(self):
        """The file reads fine. Its digest would describe something the release
        does not contain."""
        release = os.path.join(self.root, "release")
        os.mkdir(release)
        outside = os.path.join(self.root, "outside.jsonl")
        with open(outside, "wb") as handle:
            handle.write(b'{"a":1}\n')
        try:
            os.symlink(outside, os.path.join(release, "events.jsonl"))
        except (OSError, NotImplementedError):
            self.skipTest("this filesystem does not support symlinks")
        with self.assertRaises(capture.CaptureError) as caught:
            grab(release, record_counts={})
        self.assertIn("is a symlink", str(caught.exception))

    def test_a_symlinked_directory_inside_the_release_is_refused(self):
        """os.walk does not descend a symlink to a directory, so leaving one in
        place dropped everything under it from the statement and from the release
        digest with nothing saying so. That is the silent absence the gates exist
        to refuse."""
        release = os.path.join(self.root, "release")
        os.mkdir(release)
        with open(os.path.join(release, "events.jsonl"), "wb") as handle:
            handle.write(b'{"a":1}\n')
        outside = os.path.join(self.root, "elsewhere")
        os.mkdir(outside)
        with open(os.path.join(outside, "more.jsonl"), "wb") as handle:
            handle.write(b'{"b":2}\n{"b":3}\n')
        try:
            os.symlink(outside, os.path.join(release, "extra"))
        except (OSError, NotImplementedError):
            self.skipTest("this filesystem does not support symlinks")
        with self.assertRaises(capture.CaptureError) as caught:
            grab(release, record_counts={})
        self.assertIn("symlink to a directory", str(caught.exception))
        self.assertIn("without anything saying so", str(caught.exception))

    def test_a_refused_directory_name_inside_the_release_is_refused(self):
        """Skipping it quietly would leave the bundle digest covering part of the
        tree while the statement said nothing about the rest."""
        for name in sorted(capture.REFUSED_NAMES):
            release = os.path.join(self.root, "release-" + name.strip("._"))
            os.mkdir(release)
            with open(os.path.join(release, "events.jsonl"), "wb") as handle:
                handle.write(b'{"a":1}\n')
            os.mkdir(os.path.join(release, name))
            with self.subTest(directory=name):
                with self.assertRaises(capture.CaptureError) as caught:
                    grab(release, record_counts={})
                self.assertIn(name, str(caught.exception))

    def test_a_directory_that_cannot_be_read_is_refused(self):
        """os.walk swallows a directory it cannot read, which drops its contents
        the same way a symlinked directory did. Simulated rather than done with
        permissions, because a run as root would read it anyway and the test would
        pass without exercising anything."""
        release = os.path.join(self.root, "unreadable")
        locked = os.path.join(release, "locked")
        os.makedirs(locked)
        with open(os.path.join(release, "events.jsonl"), "wb") as handle:
            handle.write(b'{"a":1}\n')
        with open(os.path.join(locked, "hidden.jsonl"), "wb") as handle:
            handle.write(b'{"b":2}\n')

        real_scandir = os.scandir

        def refusing(path="."):
            if os.path.realpath(str(path)) == os.path.realpath(locked):
                raise PermissionError(13, "Permission denied", str(path))
            return real_scandir(path)

        os.scandir = refusing
        try:
            with self.assertRaises(capture.CaptureError) as caught:
                grab(release, record_counts={})
        finally:
            os.scandir = real_scandir
        self.assertIn("cannot be read whole", str(caught.exception))

    def test_a_nested_directory_of_records_is_captured_rather_than_skipped(self):
        release = os.path.join(self.root, "nested")
        os.makedirs(os.path.join(release, "by-pool"))
        with open(os.path.join(release, "events.jsonl"), "wb") as handle:
            handle.write(b'{"a":1}\n')
        with open(os.path.join(release, "by-pool", "pool-a.jsonl"), "wb") as handle:
            handle.write(b'{"a":1}\n{"a":2}\n')
        paths = [
            e["path"]
            for e in grab(release, record_counts={})["predicate"]["dataset_subjects"]
        ]
        self.assertEqual(sorted(paths), [os.path.join("by-pool", "pool-a.jsonl"), "events.jsonl"])

    def test_a_parent_segment_in_the_release_path_resolves_before_use(self):
        found = grab(os.path.join(V2, "..", "v2"))
        self.assertTrue(report(found).ok)

    def test_a_reversed_coverage_interval_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(coverage_start=15000000, coverage_end=11370000)
        self.assertIn("starts at 15000000", str(caught.exception))

    def test_a_coverage_bound_that_is_not_a_whole_number_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(coverage_end="15000000")
        self.assertIn("whole number", str(caught.exception))

    def test_a_gap_outside_the_coverage_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(gaps=[{"start": 9000000, "end": 9000100, "reason": "before the venue existed"}])
        self.assertIn("outside the coverage", str(caught.exception))

    def test_a_gap_without_a_reason_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(gaps=[{"start": 12000000, "end": 12000100}])
        self.assertIn("needs reason", str(caught.exception))

    def test_a_previous_release_without_a_name_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(previous=V1)
        self.assertIn("--previous-name", str(caught.exception))

    def test_a_first_release_without_a_reason_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(first_release_reason=None)
        self.assertIn("--first-release-reason", str(caught.exception))

    def test_a_producer_tool_or_version_that_was_not_stated_is_refused(self):
        """A default would put this tool's own name in the field gate 2 reads as
        the thing that made the files. Ariadne read them."""
        for field, flag in (
            ("producer_tool", "--producer-tool"),
            ("producer_version", "--producer-version"),
        ):
            for value in (None, "", "   "):
                with self.subTest(field=field, value=repr(value)):
                    with self.assertRaises(capture.CaptureError) as caught:
                        grab(**{field: value})
                    self.assertIn(flag, str(caught.exception))

    def test_a_producer_command_that_was_not_stated_is_refused(self):
        for value in (None, [], [""], ["forge", 3]):
            with self.subTest(value=repr(value)):
                with self.assertRaises(capture.CaptureError) as caught:
                    grab(producer_command=value)
                self.assertIn("--producer-command", str(caught.exception))

    def test_a_stated_count_naming_a_file_the_release_does_not_hold_is_refused(self):
        """A typo would otherwise pass unremarked, and the count the caller
        believed they supplied would not be the one in the statement."""
        with self.assertRaises(capture.CaptureError) as caught:
            grab(record_counts={"mapping.json": 1, "events.jsnol": 5})
        self.assertIn("events.jsnol", str(caught.exception))
        self.assertIn("the release does not hold", str(caught.exception))


class ArgumentTests(unittest.TestCase):
    """A library caller can pass shapes argparse would have coerced.

    Each of these used to raise a bare ValueError or TypeError from inside the
    capture, or produce a statement that verify then refused. A capture reports
    what is wrong with its arguments the same way it reports what is wrong with a
    release.
    """

    def test_a_release_name_that_was_not_stated_is_refused(self):
        for value in (None, "", "   ", 7):
            with self.subTest(value=repr(value)):
                with self.assertRaises(capture.CaptureError) as caught:
                    grab(name=value)
                self.assertIn("--name", str(caught.exception))

    def test_inputs_that_are_not_a_list_of_objects_are_refused(self):
        for value, expected in (
            ("alexandria://x", "must be a list"),
            (["alexandria://x"], "must be an object"),
            ([None], "must be an object"),
        ):
            with self.subTest(value=repr(value)):
                with self.assertRaises(capture.CaptureError) as caught:
                    grab(inputs=value)
                self.assertIn(expected, str(caught.exception))

    def test_gaps_that_are_not_a_list_of_objects_are_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(gaps="12000000")
        self.assertIn("must be a list", str(caught.exception))

    def test_parameters_that_are_not_a_mapping_are_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(parameters=["venue", "goldfinch"])
        self.assertIn("--parameter must be a mapping", str(caught.exception))

    def test_record_counts_that_are_not_a_mapping_are_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(record_counts=["events.jsonl", 2])
        self.assertIn("--record-count must be a mapping", str(caught.exception))

    def test_a_stated_count_that_is_not_a_whole_number_is_refused(self):
        for value in ("two", -2, 1.5, True):
            with self.subTest(value=repr(value)):
                with self.assertRaises(capture.CaptureError) as caught:
                    grab(record_counts={"events.jsonl": value})
                self.assertIn("whole number of records", str(caught.exception))

    def test_comparing_a_release_against_itself_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            grab(V2, previous=V2, previous_name="itself")
        self.assertIn("comparison against itself", str(caught.exception))

    def test_a_blank_first_release_reason_is_refused(self):
        """It used to produce a statement that gate 5 then refused, which breaks
        the capture's contract: what it writes, verify accepts unedited."""
        with self.assertRaises(capture.CaptureError) as caught:
            grab(first_release_reason="   ")
        self.assertIn("--first-release-reason", str(caught.exception))


class CoverageTests(unittest.TestCase):
    def test_an_empty_gap_list_is_written_rather_than_omitted(self):
        """The predicate refuses an absent gaps key, because that is the
        difference between a producer who looked and one who did not."""
        found = grab()["predicate"]["coverage"]
        self.assertIn("gaps", found)
        self.assertEqual(found["gaps"], [])

    def test_a_recorded_gap_survives_into_the_statement(self):
        gap = {"start": 12000000, "end": 12000100, "reason": "no receipts for this range"}
        found = grab(gaps=[gap])["predicate"]["coverage"]
        self.assertEqual(found["gaps"], [gap])


class DeltaTests(unittest.TestCase):
    def test_a_first_release_carries_a_null_baseline_and_its_reason(self):
        found = grab()["predicate"]["deltas"]
        self.assertIsNone(found["baseline"])
        self.assertIn("first release", found["reason"])

    def test_a_comparison_identifies_both_sides(self):
        found = grab(previous=V1, previous_name="goldfinch-credit-events-v1")["predicate"]["deltas"]
        self.assertEqual(found["baseline"]["name"], "goldfinch-credit-events-v1")
        self.assertEqual(found["current"]["name"], "goldfinch-credit-events-v2")
        self.assertNotEqual(found["baseline"]["digest"], found["current"]["digest"])

    def test_no_record_level_difference_is_invented(self):
        """Telling which records changed needs a record identity this capture does
        not have, so it records none and says so."""
        document = grab(previous=V1, previous_name="goldfinch-credit-events-v1")
        self.assertNotIn("records", document["predicate"]["deltas"])
        skipped = [
            c for c in document["predicate"]["claims"] if c["disposition"] == "skipped"
        ]
        self.assertEqual(len(skipped), 1)
        self.assertIn("record identity", skipped[0]["reason"])

    def test_a_comparison_verifies_clean(self):
        found = report(grab(previous=V1, previous_name="goldfinch-credit-events-v1"))
        self.assertTrue(found.ok, "\n".join(g.line() for g in found.gates if not g.passed))


class InputTests(unittest.TestCase):
    def test_a_release_derived_from_nothing_records_an_empty_list(self):
        self.assertEqual(grab()["predicate"]["inputs"], [])

    def test_an_input_claiming_passed_without_a_digest_does_not_verify(self):
        """The capture takes inputs from the caller verbatim, so the predicate is
        what stops this reaching a reader."""
        document = grab(
            inputs=[
                {
                    "name": "goldfinch capture",
                    "locator": "alexandria://goldfinch/2024-01",
                    "disposition": "passed",
                }
            ]
        )
        found = report(document)
        self.assertFalse(found.ok)
        failed = [g.name for g in found.gates if not g.passed]
        self.assertEqual(failed, ["inputs"])

    def test_an_input_recorded_absent_survives_and_verifies(self):
        entry = {
            "name": "subgraph backfill",
            "locator": "https://api.thegraph.com/subgraphs/name/goldfinch",
            "disposition": "skipped",
            "reason": "the endpoint was retired before this release was built",
        }
        document = grab(inputs=[entry])
        self.assertEqual(document["predicate"]["inputs"], [entry])
        self.assertTrue(report(document).ok)


class ProducerTests(unittest.TestCase):
    def test_the_producer_block_carries_what_the_caller_stated(self):
        found = grab()["predicate"]["producer"]
        self.assertEqual(found["tool"], "tabularium")
        self.assertEqual(found["tool_version"], "0.3.0")
        self.assertEqual(found["command"], ["python3", "scripts/tabularium.py", "release"])

    def test_the_parameters_digest_is_stable_across_key_order(self):
        one = grab(parameters={"venue": "goldfinch", "mode": "offline"})
        two = grab(parameters={"mode": "offline", "venue": "goldfinch"})
        self.assertEqual(
            one["predicate"]["producer"]["parameters_digest"],
            two["predicate"]["producer"]["parameters_digest"],
        )

    def test_different_parameters_give_a_different_digest(self):
        one = grab(parameters={"venue": "goldfinch"})
        two = grab(parameters={"venue": "clearpool"})
        self.assertNotEqual(
            one["predicate"]["producer"]["parameters_digest"],
            two["predicate"]["producer"]["parameters_digest"],
        )


class WriteTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_a_written_statement_reads_back_whole(self):
        path = os.path.join(self.root, "out.json")
        capture.write(path, json.dumps(grab(), indent=2) + "\n")
        with open(path, "rb") as handle:
            self.assertTrue(json.loads(handle.read().decode("utf-8")))

    def test_writer_pins_utf8_and_literal_lf(self):
        path = os.path.join(self.root, "unicode.json")
        with mock.patch.object(
            capture.tempfile,
            "NamedTemporaryFile",
            wraps=tempfile.NamedTemporaryFile,
        ) as temporary:
            capture.write(path, '{"label": "caf\u00e9"}\n')
        self.assertEqual(temporary.call_args.kwargs["encoding"], "utf-8")
        self.assertEqual(temporary.call_args.kwargs["newline"], "\n")
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), b'{"label": "caf\xc3\xa9"}\n')

    def test_a_failed_write_leaves_nothing_behind(self):
        """A capture that died before the replace used to leave a truncated file
        where the next run would read it as complete. The temporary file goes too,
        so a failed run does not litter the output directory."""
        path = os.path.join(self.root, "out.json")
        original = os.replace

        def refuse(source, target):
            raise OSError("replace failed")

        os.replace = refuse
        try:
            with self.assertRaises(OSError):
                capture.write(path, '{"a": 1}\n')
        finally:
            os.replace = original
        self.assertFalse(os.path.exists(path))
        leftovers = [n for n in os.listdir(self.root) if n.startswith(".ariadne-")]
        self.assertEqual(leftovers, [])

    def test_a_write_replaces_an_existing_file_atomically(self):
        path = os.path.join(self.root, "out.json")
        capture.write(path, '{"first": true}\n')
        capture.write(path, '{"second": true}\n')
        with open(path, "rb") as handle:
            self.assertEqual(json.loads(handle.read().decode("utf-8")), {"second": True})


if __name__ == "__main__":
    unittest.main()
