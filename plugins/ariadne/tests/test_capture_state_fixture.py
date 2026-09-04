"""Reading a Lazarus fixture directory into a statement.

The shipped fixture is the one this capture was written against, so the tests that
matter most run over it rather than over a mock: a capture that only works on a tree
this file built is a capture nobody has tried.
"""

import copy
import hashlib
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import envelope, registry, verify  # noqa: E402
import ariadne_lib.predicates  # noqa: F401,E402
from ariadne_lib.capture import state_fixture as capture  # noqa: E402
from ariadne_lib.predicates import state_fixture as predicate  # noqa: E402

LAZARUS_FIXTURE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))))),
    "plugins", "lazarus", "examples", "aave-v4-spoke-v0",
)
RECEIPT_FIXTURE = support.LAZARUS_RECEIPT_FIXTURE

COMMAND = ["python3", "scripts/lazarus.py", "verify", "examples/aave-v4-spoke-v0"]
REASON = "first capture of this block; nothing earlier to compare against"


def read_json(path):
    with open(path, "rb") as handle:
        return json.loads(handle.read().decode("utf-8"))


def taken(root, **overrides):
    arguments = {
        "name": "aave-v4-spoke-v0",
        "capture_tool": "lazarus",
        "capture_command": COMMAND,
        "first_capture_reason": REASON,
    }
    arguments.update(overrides)
    return capture.capture(root, **arguments)


def report_for(statement):
    return verify.report(
        envelope.read(json.dumps(statement).encode("utf-8")), registry.DEFAULT
    )


class SkipUnlessLazarusFixture(unittest.TestCase):
    def setUp(self):
        if not os.path.isdir(LAZARUS_FIXTURE):
            self.skipTest("Lazarus is not beside this plugin in this checkout")


class SkipUnlessReceiptFixture(unittest.TestCase):
    def setUp(self):
        if not os.path.isdir(RECEIPT_FIXTURE):
            self.skipTest("the Lazarus receipt fixture is not beside Ariadne")


class ReceiptFixtureTests(SkipUnlessReceiptFixture):
    def test_manifest_v2_emits_and_verifies_state_fixture_v2(self):
        statement = taken(RECEIPT_FIXTURE)
        manifest = read_json(os.path.join(RECEIPT_FIXTURE, "manifest.json"))
        report = report_for(statement)

        self.assertTrue(report.ok, "\n".join(g.line() for g in report.gates))
        self.assertEqual(statement["predicateType"], predicate.V2.TYPE)
        self.assertEqual(
            statement["predicate"]["chain"]["receipts_root"],
            manifest["receipts_root"],
        )
        self.assertEqual(
            statement["predicate"]["evidence"], manifest["evidence_counts"]
        )
        self.assertEqual(
            statement["predicate"]["replay"],
            {
                "reaches_network": False,
                "canonical_chain_claim": False,
                "provider_independence_claim": False,
            },
        )
        self.assertEqual(statement["predicate"]["commands"], [])

    def test_capture_claims_no_chain_provider_or_transaction_hash_authority(self):
        claims = taken(RECEIPT_FIXTURE)["predicate"]["claims"]
        names = (
            "canonical",
            "independent providers",
            "transaction hash attributed",
        )
        for phrase in names:
            matching = [claim for claim in claims if phrase in claim["name"]]
            with self.subTest(phrase=phrase):
                self.assertTrue(matching)
                self.assertTrue(
                    all(claim["disposition"] == "skipped" for claim in matching)
                )

    def test_a_source_mutation_after_capture_does_not_rewrite_the_statement(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = os.path.join(directory, "receipt-fixture")
            shutil.copytree(RECEIPT_FIXTURE, fixture)
            statement = taken(fixture)
            before = json.dumps(statement, sort_keys=True)
            witness = os.path.join(fixture, "receipt-witness.json")
            with open(witness, "ab") as handle:
                handle.write(b" ")
            self.assertEqual(json.dumps(statement, sort_keys=True), before)
            self.assertTrue(report_for(statement).ok)
            with self.assertRaises(capture.CaptureError):
                taken(fixture)

    def test_an_unlisted_consensus_witness_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = os.path.join(directory, "receipt-fixture")
            shutil.copytree(RECEIPT_FIXTURE, fixture)
            path = os.path.join(fixture, "manifest.json")
            manifest = read_json(path)
            manifest["components"] = [
                component
                for component in manifest["components"]
                if component["path"] != "receipt-witness.json"
            ]
            with open(path, "w") as handle:
                json.dump(manifest, handle)
            with self.assertRaisesRegex(capture.CaptureError, "receipt-witness.json"):
                taken(fixture)

    def test_cross_version_baselines_are_refused(self):
        with self.assertRaisesRegex(capture.CaptureError, "cross-version"):
            taken(
                RECEIPT_FIXTURE,
                previous=LAZARUS_FIXTURE,
                previous_name="aave-v4-spoke-v0",
                first_capture_reason=None,
            )

    def test_manifest_v2_component_count_is_bounded_before_file_reads(self):
        maximum = 1024
        with tempfile.TemporaryDirectory() as directory:
            fixture = os.path.join(directory, "receipt-fixture")
            shutil.copytree(RECEIPT_FIXTURE, fixture)
            path = os.path.join(fixture, "manifest.json")
            manifest = read_json(path)
            manifest["components"] = [
                copy.deepcopy(manifest["components"][0])
                for _ in range(maximum + 1)
            ]
            with open(path, "w") as handle:
                json.dump(manifest, handle)
            with mock.patch.object(
                capture,
                "components_of",
                side_effect=AssertionError("components were read before the cap"),
            ):
                with self.assertRaisesRegex(
                    capture.CaptureError,
                    "records at most %d" % maximum,
                ):
                    taken(fixture)

    def test_manifest_v2_total_bytes_are_bounded_before_file_reads(self):
        manifest = read_json(os.path.join(RECEIPT_FIXTURE, "manifest.json"))
        for entry in manifest["components"][:5]:
            entry["bytes"] = predicate.MAX_BYTES
        by_path = {entry["path"]: entry for entry in manifest["components"]}
        present = [
            (relative, os.path.join(RECEIPT_FIXTURE, relative))
            for relative in by_path
        ] + [
            (
                capture.MANIFEST,
                os.path.join(RECEIPT_FIXTURE, capture.MANIFEST),
            )
        ]

        def pretend_read(root, relative, what, max_bytes, keep_bytes=False):
            entry = by_path[relative]
            return (
                {"sha256": entry["sha256"]},
                entry["bytes"],
                b"{}" if keep_bytes else None,
            )

        maximum_bytes = 2 * 1024 * 1024 * 1024
        with mock.patch.object(
            capture.tree, "files", return_value=present
        ) as walked, mock.patch.object(
            capture, "read_component", side_effect=pretend_read
        ) as reader:
            with self.assertRaisesRegex(capture.CaptureError, str(maximum_bytes)):
                capture.components_of(RECEIPT_FIXTURE, manifest)
        walked.assert_not_called()
        reader.assert_not_called()

    def test_manifest_v2_refuses_a_component_segment_that_names_nothing(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = os.path.join(directory, "receipt-fixture")
            shutil.copytree(RECEIPT_FIXTURE, fixture)
            source = os.path.join(fixture, "plan.json")
            os.mkdir(os.path.join(fixture, "a"))
            os.rename(source, os.path.join(fixture, "a", " "))
            path = os.path.join(fixture, "manifest.json")
            manifest = read_json(path)
            for component in manifest["components"]:
                if component["path"] == "plan.json":
                    component["path"] = "a/ "
            with open(path, "w") as handle:
                json.dump(manifest, handle)
            with self.assertRaisesRegex(capture.CaptureError, "fixture-relative"):
                taken(fixture)

    def test_manifest_v2_refuses_an_invisible_component_segment(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = os.path.join(directory, "receipt-fixture")
            shutil.copytree(RECEIPT_FIXTURE, fixture)
            source = os.path.join(fixture, "plan.json")
            os.mkdir(os.path.join(fixture, "a"))
            invisible = "\u200b"
            os.rename(source, os.path.join(fixture, "a", invisible))
            path = os.path.join(fixture, "manifest.json")
            manifest = read_json(path)
            for component in manifest["components"]:
                if component["path"] == "plan.json":
                    component["path"] = "a/" + invisible
            with open(path, "w") as handle:
                json.dump(manifest, handle)
            with self.assertRaisesRegex(capture.CaptureError, "fixture-relative"):
                taken(fixture)

    def test_manifest_v2_refuses_release_invisible_capture_identifiers(self):
        invisible = ("\u200b", "\x00", "\ue000", "\u2060")
        for value in invisible:
            for field, overrides in (
                ("capture tool", {"capture_tool": value}),
                ("capture command", {"capture_command": [value]}),
                ("fixture name", {"name": value}),
            ):
                with self.subTest(field=field, value=repr(value)):
                    with self.assertRaisesRegex(
                        capture.CaptureError, "portable graphic"
                    ):
                        taken(RECEIPT_FIXTURE, **overrides)

    def test_manifest_v2_refuses_a_current_name_colliding_with_a_component(self):
        with self.assertRaisesRegex(capture.CaptureError, "subject names"):
            taken(RECEIPT_FIXTURE, name="header.json")

    def test_each_component_read_is_bounded_by_its_declared_size(self):
        manifest = read_json(os.path.join(RECEIPT_FIXTURE, "manifest.json"))
        by_path = {entry["path"]: entry for entry in manifest["components"]}
        present = [
            (relative, os.path.join(RECEIPT_FIXTURE, relative))
            for relative in by_path
        ] + [
            (
                capture.MANIFEST,
                os.path.join(RECEIPT_FIXTURE, capture.MANIFEST),
            )
        ]
        observed = {}

        def pretend_read(root, relative, what, max_bytes, keep_bytes=False):
            observed[relative] = max_bytes
            entry = by_path[relative]
            return (
                {"sha256": entry["sha256"]},
                entry["bytes"],
                b"{}" if keep_bytes else None,
            )

        with mock.patch.object(
            capture.tree, "files", return_value=present
        ), mock.patch.object(
            capture, "read_component", side_effect=pretend_read
        ):
            capture.components_of(RECEIPT_FIXTURE, manifest)

        for path, entry in by_path.items():
            expected = entry["bytes"]
            if path == capture.HEADER:
                expected = min(expected, capture.MAX_MANIFEST_BYTES)
            with self.subTest(path=path):
                self.assertEqual(observed[path], expected)

    def test_manifest_shape_is_settled_before_component_reads(self):
        def invalid_chain_id(manifest):
            manifest["chain_id"] = "one"

        def invalid_block_number(manifest):
            manifest["block"]["number"] = "0x01"

        def invalid_block_hash(manifest):
            manifest["block"]["hash"] = "0xnot-a-block-hash"

        def invalid_evidence_count(manifest):
            manifest["evidence_counts"]["proof_backed"] = True

        def invalid_component_digest(manifest):
            manifest["components"][0]["sha256"] = "not-a-digest"

        for label, mutate in (
            ("chain id", invalid_chain_id),
            ("block number", invalid_block_number),
            ("block hash", invalid_block_hash),
            ("evidence count", invalid_evidence_count),
            ("component digest", invalid_component_digest),
        ):
            with self.subTest(field=label), tempfile.TemporaryDirectory() as directory:
                fixture = os.path.join(directory, "receipt-fixture")
                shutil.copytree(RECEIPT_FIXTURE, fixture)
                path = os.path.join(fixture, "manifest.json")
                manifest = read_json(path)
                mutate(manifest)
                with open(path, "w") as handle:
                    json.dump(manifest, handle)

                original = capture.read_component
                component_reads = []

                def observe(root, relative, what, max_bytes, keep_bytes=False):
                    if relative != capture.MANIFEST:
                        component_reads.append(relative)
                    return original(root, relative, what, max_bytes, keep_bytes)

                with mock.patch.object(
                    capture, "read_component", side_effect=observe
                ):
                    with self.assertRaises(capture.CaptureError):
                        taken(fixture)
                self.assertEqual(component_reads, [])

    def test_empty_directories_count_against_the_capture_tree_bound(self):
        class EmptyDirectory:
            def __init__(self, root, index):
                self.name = "empty-%04d" % index
                self.path = os.path.join(root, self.name)

            def is_dir(self, follow_symlinks=True):
                return True

            def is_symlink(self):
                return False

            def stat(self, follow_symlinks=True):
                return os.stat_result((0o040755, 0, 0, 1, 0, 0, 0, 0, 0, 0))

        class WideScan:
            def __init__(self, root):
                self.entries = iter(
                    EmptyDirectory(root, index)
                    for index in range(capture.tree.MAX_FILES + 1)
                )

            def __enter__(self):
                return self

            def __exit__(self, *_):
                pass

            def __iter__(self):
                return self

            def __next__(self):
                return next(self.entries)

            def close(self):
                pass

        with mock.patch.object(
            capture.tree.os,
            "scandir",
            return_value=WideScan(RECEIPT_FIXTURE),
        ):
            with self.assertRaisesRegex(
                capture.CaptureError,
                "more than %d entries" % capture.tree.MAX_FILES,
            ):
                capture.tree.files(RECEIPT_FIXTURE, "fixture")


class TheShippedFixtureTests(SkipUnlessLazarusFixture):
    def test_it_captures_and_verifies_clean(self):
        report = report_for(taken(LAZARUS_FIXTURE))
        self.assertTrue(
            report.ok, "\n".join(g.line() for g in report.gates if not g.passed)
        )
        self.assertFalse(report.unchecked)

    def test_the_pin_is_the_one_the_manifest_carries(self):
        manifest = read_json(os.path.join(LAZARUS_FIXTURE, "manifest.json"))
        header = read_json(os.path.join(LAZARUS_FIXTURE, "header.json"))
        chain = taken(LAZARUS_FIXTURE)["predicate"]["chain"]
        self.assertEqual(chain["chain_id"], int(manifest["chain_id"], 16))
        self.assertEqual(chain["block_number"], int(manifest["block"]["number"], 16))
        self.assertEqual(chain["block_hash"], manifest["block"]["hash"].lower())
        self.assertEqual(chain["state_root"], header["state_root"].lower())

    def test_the_counts_are_read_rather_than_computed(self):
        """The rule this capture exists for. Recomputing one would mean deciding
        for Lazarus which of its records were checked against the state root."""
        manifest = read_json(os.path.join(LAZARUS_FIXTURE, "manifest.json"))
        body = taken(LAZARUS_FIXTURE)["predicate"]
        self.assertEqual(body["evidence"], manifest["evidence_counts"])

    def test_every_component_the_manifest_declares_is_described(self):
        manifest = read_json(os.path.join(LAZARUS_FIXTURE, "manifest.json"))
        body = taken(LAZARUS_FIXTURE)["predicate"]
        self.assertEqual(
            sorted(entry["path"] for entry in body["fixture_subjects"]),
            sorted(entry["path"] for entry in manifest["components"]),
        )

    def test_every_component_digest_is_a_subject(self):
        statement = taken(LAZARUS_FIXTURE)
        covered = {
            json.dumps(entry["digest"], sort_keys=True) for entry in statement["subject"]
        }
        for entry in statement["predicate"]["fixture_subjects"]:
            with self.subTest(path=entry["path"]):
                self.assertIn(json.dumps(entry["digest"], sort_keys=True), covered)

    def test_replay_is_written_closed_and_is_not_a_parameter(self):
        body = taken(LAZARUS_FIXTURE)["predicate"]
        self.assertIs(body["replay"]["reaches_network"], False)
        self.assertIs(body["replay"]["canonical_chain_claim"], False)

    def test_the_version_comes_from_the_manifest(self):
        manifest = read_json(os.path.join(LAZARUS_FIXTURE, "manifest.json"))
        body = taken(LAZARUS_FIXTURE)["predicate"]
        self.assertEqual(body["capture"]["tool_version"], manifest["tool_version"])

    def test_a_stated_version_that_disagrees_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            taken(LAZARUS_FIXTURE, capture_version="9.9.9")
        self.assertIn("the manifest is what the tool wrote", str(caught.exception))

    def test_a_stated_version_that_agrees_is_accepted(self):
        manifest = read_json(os.path.join(LAZARUS_FIXTURE, "manifest.json"))
        self.assertTrue(
            report_for(taken(LAZARUS_FIXTURE, capture_version=manifest["tool_version"])).ok
        )

    def test_capture_is_deterministic(self):
        self.assertEqual(taken(LAZARUS_FIXTURE), taken(LAZARUS_FIXTURE))

    def test_it_records_that_it_did_not_recheck_the_proofs(self):
        body = taken(LAZARUS_FIXTURE)["predicate"]
        skipped = [c for c in body["claims"] if c["disposition"] == "skipped"]
        reasons = " ".join(c["reason"] for c in skipped)
        self.assertIn("does not re-verify", reasons)
        self.assertIn("canonical", reasons)


class CopiedFixtureTests(SkipUnlessLazarusFixture):
    """A copy of the shipped fixture, damaged one way at a time."""

    def setUp(self):
        super(CopiedFixtureTests, self).setUp()
        self.root = tempfile.mkdtemp(prefix="ariadne-fixture-")
        self.fixture = os.path.join(self.root, "aave-v4-spoke-v0")
        shutil.copytree(LAZARUS_FIXTURE, self.fixture)
        self.addCleanup(shutil.rmtree, self.root, True)

    def manifest(self):
        with open(os.path.join(self.fixture, "manifest.json")) as handle:
            return json.load(handle)

    def rewrite(self, manifest):
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            json.dump(manifest, handle)

    def refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            taken(self.fixture)
        return str(caught.exception)

    def test_the_copy_captures_clean(self):
        """The control. Without it every refusal below could be the copy."""
        self.assertTrue(report_for(taken(self.fixture)).ok)

    def test_a_missing_manifest_is_refused(self):
        os.unlink(os.path.join(self.fixture, "manifest.json"))
        self.assertIn("has no manifest.json", self.refused())

    def test_a_manifest_that_is_not_json_is_refused(self):
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            handle.write("{not json")
        self.assertIn("is not JSON", self.refused())

    def test_a_manifest_naming_one_key_twice_is_refused(self):
        path = os.path.join(self.fixture, "manifest.json")
        with open(path, "rb") as handle:
            raw = handle.read()
        with open(path, "wb") as handle:
            handle.write(b'{"schema_version": 1,' + raw.lstrip()[1:])
        self.assertIn("duplicate key", self.refused())

    def test_a_parse_refusal_retains_none_of_the_hostile_document(self):
        marker = "PRIVATE_PROVIDER_VALUE_"
        path = os.path.join(self.fixture, "manifest.json")
        with open(path, "w") as handle:
            handle.write('{"%s%s": ' % (marker, "x" * 100000))
        with self.assertRaises(capture.CaptureError) as caught:
            taken(self.fixture)
        error = caught.exception
        self.assertNotIn(marker, str(error))
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)

    def test_a_symlinked_manifest_is_refused_before_its_target_is_read(self):
        target = os.path.join(self.root, "manifest.json")
        shutil.move(os.path.join(self.fixture, "manifest.json"), target)
        os.symlink(target, os.path.join(self.fixture, "manifest.json"))
        self.assertIn("manifest.json is a symlink", self.refused())

    def test_a_manifest_that_is_a_list_is_refused(self):
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            handle.write("[]")
        self.assertIn("rather than an object", self.refused())

    def test_a_manifest_carrying_nan_is_refused(self):
        """`json.loads` accepts NaN as a Python extension, and every comparison
        against it is false including the one that would refuse it."""
        with open(os.path.join(self.fixture, "manifest.json"), "w") as handle:
            handle.write('{"schema_version": 1, "evidence_counts": {"proof_backed": NaN}}')
        self.assertIn("which is not JSON", self.refused())

    def test_each_manifest_field_this_capture_reads_is_required(self):
        for field in capture.MANIFEST_REQUIRED:
            manifest = self.manifest()
            del manifest[field]
            self.rewrite(manifest)
            with self.subTest(field=field):
                self.assertIn(field, self.refused())
            self.rewrite(self.manifest())
            shutil.rmtree(self.fixture)
            shutil.copytree(LAZARUS_FIXTURE, self.fixture)

    def test_a_later_schema_version_is_refused(self):
        manifest = self.manifest()
        manifest["schema_version"] = 3
        self.rewrite(manifest)
        self.assertIn("reads only 1 or 2", self.refused())

    def test_a_boolean_schema_version_is_refused(self):
        """`True == 1` in Python, so a plain inequality let `true` through the one
        check that refuses a manifest this capture cannot read. Found by sweeping
        the manifest with values that satisfy a presence test."""
        manifest = self.manifest()
        manifest["schema_version"] = True
        self.rewrite(manifest)
        self.assertIn("schema_version", self.refused())

    def test_a_fixture_digest_that_is_not_a_digest_is_refused(self):
        """The field is required and unused. Requiring it and accepting any value
        would be a presence test carrying nothing, and it would let this capture
        call a document a Lazarus manifest on the strength of a key holding
        `{"a": 1}`."""
        for value in (None, "", "   ", 0, True, [], {}, {"a": 1}, "beef",
                      "F" * 64, "0x" + "a" * 64, "a" * 64 + "\n"):
            manifest = self.manifest()
            manifest["fixture_digest"] = value
            self.rewrite(manifest)
            with self.subTest(fixture_digest=value):
                self.assertIn("fixture_digest", self.refused())

    def test_a_real_fixture_digest_is_accepted(self):
        manifest = self.manifest()
        manifest["fixture_digest"] = "a" * 64
        self.rewrite(manifest)
        self.assertTrue(report_for(taken(self.fixture)).ok)

    def test_the_capture_does_not_use_the_manifests_fixture_digest(self):
        """It is Lazarus's digest over Lazarus's listing, by a method this tool has
        not reimplemented. Presenting it as the digest of what Ariadne read would
        assert a derivation nobody here performed."""
        manifest = self.manifest()
        before = taken(self.fixture)["predicate"]["deltas"]["current"]["digest"]
        manifest["fixture_digest"] = "b" * 64
        self.rewrite(manifest)
        after = taken(self.fixture)["predicate"]["deltas"]["current"]["digest"]
        self.assertEqual(before, after)
        self.assertNotIn("b" * 64, json.dumps(taken(self.fixture)))

    def test_a_missing_header_leaves_the_state_root_out(self):
        """A capture that proved nothing has no use for one, and the predicate's
        evidence check is what refuses a proof-backed count without it."""
        os.unlink(os.path.join(self.fixture, "header.json"))
        manifest = self.manifest()
        manifest["components"] = [
            c for c in manifest["components"] if c["path"] != "header.json"
        ]
        manifest["evidence_counts"] = {
            "proof_backed": 0,
            "header_bound": 0,
            "recorded_rpc": 4,
        }
        self.rewrite(manifest)
        body = taken(self.fixture)["predicate"]
        self.assertNotIn("state_root", body["chain"])
        self.assertTrue(report_for(taken(self.fixture)).ok)

    def test_a_missing_header_beside_proved_records_fails_the_statement(self):
        """The capture writes it, and the predicate refuses it. The claim written
        beside it says why, so a reader of the capture's output sees the reason
        before running verify."""
        os.unlink(os.path.join(self.fixture, "header.json"))
        manifest = self.manifest()
        manifest["components"] = [
            c for c in manifest["components"] if c["path"] != "header.json"
        ]
        self.rewrite(manifest)
        statement = taken(self.fixture)
        report = report_for(statement)
        self.assertFalse(report.ok)
        failed = [g.name for g in report.gates if not g.passed]
        self.assertEqual(failed, ["evidence"])
        stated = [c for c in statement["predicate"]["claims"] if c["disposition"] == "failed"]
        self.assertTrue(stated)
        self.assertIn("no state root", stated[0]["reason"])

    def rewrite_header(self, header):
        """The header is a component, so the manifest has to follow it."""
        path = os.path.join(self.fixture, "header.json")
        with open(path, "w") as handle:
            json.dump(header, handle)
        with open(path, "rb") as handle:
            raw = handle.read()
        manifest = self.manifest()
        for entry in manifest["components"]:
            if entry["path"] == "header.json":
                entry["sha256"] = hashlib.sha256(raw).hexdigest()
                entry["bytes"] = len(raw)
        self.rewrite(manifest)

    def header(self):
        return read_json(os.path.join(self.fixture, "header.json"))

    def test_a_malformed_state_root_in_the_header_is_refused(self):
        """The header is read off disk like the manifest. A mutation probe removed
        the check on it and the suite stayed green, so the rule held and nothing
        pinned it."""
        for label, value in (
            ("all zero", predicate.ZERO_HASH),
            ("too short", "0xdeadbeef"),
            ("no prefix", "f" * 64),
            ("not a string", 12345),
            ("null", None),
        ):
            header = self.header()
            header["state_root"] = value
            self.rewrite_header(header)
            with self.subTest(state_root=label):
                self.assertIn("state_root", self.refused())

    def test_an_uppercased_state_root_is_lowered_rather_than_refused(self):
        """Two spellings of one value, as with the block hash."""
        header = self.header()
        header["state_root"] = header["state_root"].upper().replace("0X", "0x")
        self.rewrite_header(header)
        body = taken(self.fixture)["predicate"]
        self.assertEqual(body["chain"]["state_root"], header["state_root"].lower())
        self.assertTrue(report_for(taken(self.fixture)).ok)

    def test_a_header_with_no_state_root_leaves_it_out(self):
        header = self.header()
        del header["state_root"]
        self.rewrite_header(header)
        body = taken(self.fixture)["predicate"]
        self.assertNotIn("state_root", body["chain"])
        report = report_for(taken(self.fixture))
        self.assertFalse(report.ok)
        self.assertEqual([g.name for g in report.gates if not g.passed], ["evidence"])

    def test_a_header_that_is_not_json_is_refused(self):
        path = os.path.join(self.fixture, "header.json")
        with open(path, "w") as handle:
            handle.write("{not json")
        with open(path, "rb") as handle:
            raw = handle.read()
        manifest = self.manifest()
        for entry in manifest["components"]:
            if entry["path"] == "header.json":
                entry["sha256"] = hashlib.sha256(raw).hexdigest()
                entry["bytes"] = len(raw)
        self.rewrite(manifest)
        self.assertIn("is not JSON", self.refused())

    def test_a_symlinked_header_is_refused_before_its_target_is_read(self):
        target = os.path.join(self.root, "header.json")
        shutil.move(os.path.join(self.fixture, "header.json"), target)
        os.symlink(target, os.path.join(self.fixture, "header.json"))
        self.assertIn("header.json is a symlink", self.refused())

    def test_the_state_root_comes_from_the_header_bytes_that_were_digested(self):
        before = self.header()["state_root"].lower()
        original = capture.components_of

        def mutate_after_components(*arguments, **keywords):
            result = original(*arguments, **keywords)
            header = self.header()
            header["state_root"] = "0x" + "77" * 32
            with open(os.path.join(self.fixture, "header.json"), "w") as handle:
                json.dump(header, handle)
            return result

        with mock.patch.object(
            capture, "components_of", side_effect=mutate_after_components
        ):
            statement = taken(self.fixture)
        self.assertEqual(statement["predicate"]["chain"]["state_root"], before)

    def test_a_component_swap_to_a_symlink_after_the_check_is_refused(self):
        target = os.path.join(self.fixture, "plan.json")
        outside = os.path.join(self.root, "outside-plan.json")
        with open(target, "rb") as handle:
            replacement = handle.read() + b" "
        with open(outside, "wb") as handle:
            handle.write(replacement)
        manifest = self.manifest()
        for entry in manifest["components"]:
            if entry["path"] == "plan.json":
                entry["sha256"] = hashlib.sha256(replacement).hexdigest()
                entry["bytes"] = len(replacement)
        self.rewrite(manifest)

        original_is_file = os.path.isfile
        calls = {"target": 0}

        def swap_after_check(path):
            result = original_is_file(path)
            if path == target:
                calls["target"] += 1
                if calls["target"] == 2 and result:
                    os.unlink(target)
                    os.symlink(outside, target)
            return result

        with mock.patch.object(os.path, "isfile", side_effect=swap_after_check):
            self.assertIn("digests to", self.refused())

    def test_an_over_limit_declared_component_is_refused_before_digesting(self):
        manifest = self.manifest()
        manifest["components"][0]["bytes"] = predicate.MAX_BYTES + 1
        self.rewrite(manifest)
        with mock.patch.object(
            capture.digests,
            "of_file",
            side_effect=AssertionError("component bytes were read before the cap"),
        ):
            self.assertIn(str(predicate.MAX_BYTES), self.refused())

    def test_a_component_the_directory_lacks_is_refused(self):
        os.unlink(os.path.join(self.fixture, "plan.json"))
        self.assertIn("which the fixture does not hold", self.refused())

    def test_a_file_the_manifest_does_not_declare_is_refused(self):
        with open(os.path.join(self.fixture, "notes.txt"), "w") as handle:
            handle.write("added later\n")
        message = self.refused()
        self.assertIn("notes.txt", message)
        self.assertIn("does not declare", message)

    def test_a_digest_that_disagrees_is_refused(self):
        path = os.path.join(self.fixture, "plan.json")
        with open(path, "rb") as handle:
            changed = bytearray(handle.read())
        changed[-1] ^= 1
        with open(path, "wb") as handle:
            handle.write(changed)
        self.assertIn("and it digests to", self.refused())

    def test_a_byte_count_that_disagrees_is_refused(self):
        manifest = self.manifest()
        for entry in manifest["components"]:
            if entry["path"] == "plan.json":
                entry["bytes"] = entry["bytes"] + 1
        self.rewrite(manifest)
        message = self.refused()
        self.assertIn("plan.json", message)
        self.assertIn("bytes", message)

    def test_a_component_path_leaving_the_fixture_is_refused(self):
        manifest = self.manifest()
        manifest["components"][0]["path"] = "../outside.json"
        self.rewrite(manifest)
        self.assertIn("fixture-relative", self.refused())

    def test_a_component_declared_twice_is_refused(self):
        manifest = self.manifest()
        manifest["components"].append(dict(manifest["components"][0]))
        self.rewrite(manifest)
        self.assertIn("twice", self.refused())

    def test_an_evidence_class_left_out_is_refused(self):
        for name in predicate.EVIDENCE_CLASSES:
            manifest = self.manifest()
            del manifest["evidence_counts"][name]
            self.rewrite(manifest)
            with self.subTest(evidence_class=name):
                self.assertIn(name, self.refused())
            self.rewrite(self.manifest())
            shutil.rmtree(self.fixture)
            shutil.copytree(LAZARUS_FIXTURE, self.fixture)

    def test_an_unknown_evidence_class_is_refused(self):
        manifest = self.manifest()
        manifest["evidence_counts"]["trusted_oracle"] = 3
        self.rewrite(manifest)
        self.assertIn("trusted_oracle", self.refused())

    def test_a_boolean_count_is_refused(self):
        manifest = self.manifest()
        manifest["evidence_counts"]["header_bound"] = True
        self.rewrite(manifest)
        self.assertIn("whole number", self.refused())

    def test_a_count_over_the_ceiling_is_refused(self):
        manifest = self.manifest()
        manifest["evidence_counts"]["recorded_rpc"] = predicate.MAX_COUNT + 1
        self.rewrite(manifest)
        self.assertIn("whole number", self.refused())

    def test_a_fifo_where_a_component_belongs_is_refused(self):
        """It used to hang. `open` on a fifo blocks until something writes to it,
        so a capture over a directory holding one produced no output, no error and
        no timeout. `digests.tree_listing` had refused this since the first build
        and its comment names the same hazard, but both captures call
        `digests.of_file` directly and it had no such guard."""
        target = os.path.join(self.fixture, "plan.json")
        os.unlink(target)
        os.mkfifo(target)
        self.assertIn("not a regular file", self.refused())

    def test_a_symlinked_component_is_refused(self):
        target = os.path.join(self.fixture, "plan.json")
        moved = os.path.join(self.root, "plan.json")
        shutil.move(target, moved)
        os.symlink(moved, target)
        self.assertIn("symlink", self.refused())

    def test_a_hex_quantity_with_a_leading_zero_is_refused(self):
        """Two spellings of one number would give two statements for one fixture."""
        manifest = self.manifest()
        manifest["block"]["number"] = "0x0c7da16"
        self.rewrite(manifest)
        self.assertIn("leading zero", self.refused())

    def test_a_decimal_block_number_is_refused(self):
        manifest = self.manifest()
        manifest["block"]["number"] = 25870892
        self.rewrite(manifest)
        self.assertIn("hex quantity", self.refused())

    def test_an_unset_block_hash_is_refused(self):
        manifest = self.manifest()
        manifest["block"]["hash"] = predicate.ZERO_HASH
        self.rewrite(manifest)
        self.assertIn("identifies something", self.refused())

    def test_an_uppercased_block_hash_is_lowered_rather_than_refused(self):
        """Lazarus accepts either case and this predicate accepts only lowercase,
        so the conversion belongs here. It is the same value."""
        manifest = self.manifest()
        manifest["block"]["hash"] = manifest["block"]["hash"].upper().replace("0X", "0x")
        self.rewrite(manifest)
        body = taken(self.fixture)["predicate"]
        self.assertEqual(body["chain"]["block_hash"], manifest["block"]["hash"].lower())

    def test_a_comparison_against_a_previous_capture(self):
        other = os.path.join(self.root, "aave-v4-v1")
        shutil.copytree(LAZARUS_FIXTURE, other)
        statement = taken(
            self.fixture, previous=other, previous_name="aave-v4-spoke-v0",
            name="aave-v4-v1", first_capture_reason=None,
        )
        report = report_for(statement)
        self.assertTrue(report.ok, [g.line() for g in report.gates if not g.passed])
        deltas = statement["predicate"]["deltas"]
        self.assertEqual(deltas["baseline"]["name"], "aave-v4-spoke-v0")
        self.assertEqual(deltas["current"]["name"], "aave-v4-v1")

    def test_a_comparison_against_itself_is_refused(self):
        with self.assertRaises(capture.CaptureError) as caught:
            taken(self.fixture, previous=self.fixture, previous_name="itself")
        self.assertIn("records nothing", str(caught.exception))


class ArgumentTests(SkipUnlessLazarusFixture):
    def test_the_tool_name_has_no_default(self):
        for value in (None, "", "   "):
            with self.subTest(tool=value):
                with self.assertRaises(capture.CaptureError) as caught:
                    taken(LAZARUS_FIXTURE, capture_tool=value)
                self.assertIn("does not name the tool", str(caught.exception))

    def test_the_command_is_required_as_an_argv(self):
        for value in (
            None,
            [],
            "lazarus verify fixture",
            ["forge", ""],
            ["forge", "  "],
            [1],
        ):
            with self.subTest(command=value):
                with self.assertRaises(capture.CaptureError):
                    taken(LAZARUS_FIXTURE, capture_command=value)

    def test_a_name_is_required(self):
        for value in (None, "", "   "):
            with self.subTest(name=value):
                with self.assertRaises(capture.CaptureError):
                    taken(LAZARUS_FIXTURE, name=value)

    def test_a_first_capture_needs_its_reason(self):
        for value in (None, "", "   "):
            with self.subTest(reason=value):
                with self.assertRaises(capture.CaptureError) as caught:
                    taken(LAZARUS_FIXTURE, first_capture_reason=value)
                self.assertIn("--first-capture-reason", str(caught.exception))

    def test_a_previous_needs_its_name(self):
        for value in (None, "", "   "):
            with self.subTest(previous_name=value):
                with self.assertRaises(capture.CaptureError) as caught:
                    taken(LAZARUS_FIXTURE, previous=LAZARUS_FIXTURE, previous_name=value)
                self.assertIn("--previous-name", str(caught.exception))

    def test_v1_retains_its_historical_nonblank_identifier_contract(self):
        statement = taken(
            LAZARUS_FIXTURE,
            name="\u200b",
            capture_tool="\u200b",
            capture_command=["\u200b"],
        )
        self.assertTrue(report_for(statement).ok)

    def test_a_fixture_that_is_not_a_directory_is_refused(self):
        with self.assertRaises(capture.CaptureError):
            taken(os.path.join(LAZARUS_FIXTURE, "manifest.json"))

    def test_the_parameters_digest_covers_the_parameters(self):
        one = taken(LAZARUS_FIXTURE, parameters={"a": 1})
        two = taken(LAZARUS_FIXTURE, parameters={"a": 2})
        same = taken(LAZARUS_FIXTURE, parameters={"a": 1})
        self.assertNotEqual(
            one["predicate"]["capture"]["parameters_digest"],
            two["predicate"]["capture"]["parameters_digest"],
        )
        self.assertEqual(
            one["predicate"]["capture"]["parameters_digest"],
            same["predicate"]["capture"]["parameters_digest"],
        )

    def test_the_parameters_digest_does_not_depend_on_key_order(self):
        one = taken(LAZARUS_FIXTURE, parameters={"a": 1, "b": 2})
        two = taken(LAZARUS_FIXTURE, parameters={"b": 2, "a": 1})
        self.assertEqual(
            one["predicate"]["capture"]["parameters_digest"],
            two["predicate"]["capture"]["parameters_digest"],
        )


class WriteTests(unittest.TestCase):
    def test_a_statement_is_replaced_rather_than_truncated(self):
        directory = tempfile.mkdtemp(prefix="ariadne-write-")
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "statement.json")
        capture.write(path, '{"first": true}')
        capture.write(path, '{"second": true}')
        with open(path) as handle:
            self.assertEqual(json.load(handle), {"second": True})
        leftovers = [n for n in os.listdir(directory) if n.startswith(".ariadne-")]
        self.assertEqual(leftovers, [])

    def test_writer_pins_utf8_and_literal_lf(self):
        directory = tempfile.mkdtemp(prefix="ariadne-write-")
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "unicode.json")
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

    def test_a_failed_write_leaves_no_temporary_file(self):
        directory = tempfile.mkdtemp(prefix="ariadne-write-")
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "statement.json")

        # `write` takes text. Handing it something else fails inside the `with`,
        # which is the moment the temporary file exists and the replace has not
        # happened. An earlier version of this test subclassed `str` and overrode
        # `__len__`, which `handle.write` never calls, so it raised nothing and
        # passed for the wrong reason.
        with self.assertRaises(TypeError):
            capture.write(path, 12345)
        leftovers = [n for n in os.listdir(directory) if n.startswith(".ariadne-")]
        self.assertEqual(leftovers, [])
        self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
