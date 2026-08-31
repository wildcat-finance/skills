"""Writing a preservation release, and refusing to write one.

The release is the artefact somebody keeps. So the tests that matter most are
not the ones where it is written: they are the ones where it is not, and nothing
is left behind for a later reader to mistake for a release.
"""

import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import lazarus_lib.release as release_module
from lazarus_lib.binding import CHECKS
from lazarus_lib.canonical import dump, dumps, loads
from lazarus_lib.errors import (
    FormatError,
    IntegrityError,
    LazarusError,
    PathError,
    ResourceLimitError,
)
from lazarus_lib.manifest import build_manifest, write_manifest
from lazarus_lib.records import (
    write_anchor_records,
    write_proof_records,
    write_rpc_records,
)
from lazarus_lib.release import (
    FIXTURE_DIRECTORY,
    RELEASE_NAME,
    STATEMENT_NAME,
    build_release,
    release_digest,
    verify_release,
    write_release,
)
from lazarus_lib.verifier import verify_fixture

from . import support

COMPONENTS = ("header.json", "plan.json", "proofs.jsonl", "rpc.jsonl")
ANCHORED_COMPONENTS = (*COMPONENTS, "anchors.jsonl")
STATE_FIXTURE_TYPE = "https://ariadne.wildcat.finance/state-fixture/v1"
STATE_FIXTURE_TYPE_V2 = "https://ariadne.wildcat.finance/state-fixture/v2"
CLI = support.PLUGIN_ROOT / "scripts" / "lazarus.py"


def write_fixture(root: Path, *, hash_source=None, anchor_source_ids=None):
    """A fixture that verifies, built from synthetic material.

    `hash_source` changes one string nothing verifies against, which is enough
    to make a second fixture that verifies to a different digest.
    """
    material = support.synthetic_fixture_material()
    if hash_source is not None:
        material["plan"]["block"]["hash_source"] = hash_source
    components = COMPONENTS
    if anchor_source_ids is not None:
        material["plan"]["schema_version"] = 2
        material["plan"]["anchor_sources"] = [
            {"source_id": source_id} for source_id in anchor_source_ids
        ]
        components = ANCHORED_COMPONENTS
    dump(root / "plan.json", material["plan"])
    dump(root / "header.json", material["header"])
    write_rpc_records(root / "rpc.jsonl", material["rpc_records"])
    write_proof_records(root / "proofs.jsonl", material["proof_records"])
    if anchor_source_ids is not None:
        write_anchor_records(
            root / "anchors.jsonl",
            [
                support.sample_anchor_record(
                    source_id,
                    block_number=material["header"]["number"],
                    block_hash=material["header"]["hash"],
                )
                for source_id in anchor_source_ids
            ],
        )
    manifest = build_manifest(
        root,
        components,
        chain_id="0x1",
        block_number=material["header"]["number"],
        block_hash=material["header"]["hash"],
    )
    write_manifest(root, manifest)
    return material


def statement_for(root: Path):
    """A statement that binds, built from what the fixture verifies to.

    Written here rather than captured, so these tests do not depend on another
    plugin being installed. The shape is the one Ariadne writes.
    """
    report = verify_fixture(root)
    manifest = report["manifest"]
    subjects = [
        {
            "name": entry["path"],
            "path": entry["path"],
            "digest": {"sha256": entry["sha256"]},
            "bytes": entry["bytes"],
        }
        for entry in manifest["components"]
    ]
    version = manifest["schema_version"]
    chain = {
        "chain_id": int(manifest["chain_id"], 16),
        "block_number": int(report["block_number"], 16),
        "block_hash": report["block_hash"],
        "state_root": report["state_root"],
    }
    replay = {"reaches_network": False, "canonical_chain_claim": False}
    predicate_type = STATE_FIXTURE_TYPE
    if version == 2:
        predicate_type = STATE_FIXTURE_TYPE_V2
        chain["receipts_root"] = report["receipts_root"]
        replay["provider_independence_claim"] = False
    predicate = {
        "chain": chain,
        "evidence": dict(report["evidence_counts"]),
        "replay": replay,
        "fixture_subjects": subjects,
    }
    if version == 2:
        predicate.update(
            {
                "capture": {
                    "tool": "lazarus",
                    "tool_version": manifest["tool_version"],
                    "command": ["lazarus", "capture", str(root)],
                    "parameters_digest": {"sha256": "f" * 64},
                },
                "deltas": {
                    "baseline": None,
                    "current": {
                        "name": "synthetic-v0",
                        "digest": {"sha256": report["fixture_digest"]},
                    },
                    "reason": "first receipt-aware fixture",
                },
                "claims": [],
                "commands": [],
            }
        )
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "predicateType": predicate_type,
        "subject": [
            {"name": entry["name"], "digest": entry["digest"]} for entry in subjects
        ]
        + [{"name": "synthetic-v0", "digest": {"sha256": report["fixture_digest"]}}],
        "predicate": predicate,
    }


class Prepared:
    """A fixture, a statement beside it, and somewhere to write."""

    def __init__(self, directory):
        self.root = Path(directory)
        self.fixture = self.root / "fixture-source"
        self.fixture.mkdir()
        write_fixture(self.fixture)
        self.statement = self.root / "statement.json"
        self.document = statement_for(self.fixture)
        self.write_statement(self.document)
        self.out = self.root / "release"

    def write_statement(self, document):
        self.statement.write_bytes(json.dumps(document, indent=2).encode())

    def release(self, **changes):
        return write_release(
            changes.get("fixture", self.fixture),
            changes.get("statement", self.statement),
            changes.get("out", self.out),
        )

    def staged(self):
        return sorted(
            path.name for path in self.out.parent.glob(".*") if path.is_dir()
        )


class PreparedV2(Prepared):
    """The checked receipt-proof fixture with its matching v2 statement."""

    def __init__(self, directory):
        self.root = Path(directory)
        self.fixture = self.root / "fixture-source"
        shutil.copytree(support.RECEIPT_PROOF_FIXTURE, self.fixture)
        self.statement = self.root / "statement.json"
        self.document = statement_for(self.fixture)
        self.write_statement(self.document)
        self.out = self.root / "release"


class WrittenReleaseTests(unittest.TestCase):
    def test_an_anchored_fixture_round_trips_without_changing_release_v1(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture = root / "fixture-source"
            fixture.mkdir()
            write_fixture(
                fixture, anchor_source_ids=("archive-a", "archive-b")
            )
            statement_path = root / "statement.json"
            statement_path.write_bytes(
                json.dumps(statement_for(fixture), indent=2).encode()
            )
            out = root / "release"
            document = write_release(fixture, statement_path, out)
            read_back = verify_release(out)
            fixture_report = verify_fixture(out / FIXTURE_DIRECTORY)

            self.assertIn("chain_anchors", fixture_report)
            self.assertEqual(fixture_report["chain_anchors"]["records"], 2)
            self.assertEqual(
                set(document),
                {
                    "schema_version",
                    "tool_version",
                    "fixture",
                    "statement",
                    "verified",
                    "binding",
                    "release_digest",
                },
            )
            self.assertEqual(
                set(document["verified"]),
                {"block_hash", "evidence_counts", "canonical_chain_claim"},
            )
            self.assertNotIn("chain_anchors", document)
            self.assertNotIn("chain_anchors", read_back)
            self.assertEqual(
                document["fixture"]["fixture_digest"],
                fixture_report["fixture_digest"],
            )
            self.assertTrue(
                (out / FIXTURE_DIRECTORY / "anchors.jsonl").is_file()
            )
            self.assertEqual(document["binding"]["checks"], list(CHECKS))

    def test_a_release_holds_the_fixture_the_statement_and_the_document(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            self.assertTrue((prepared.out / FIXTURE_DIRECTORY).is_dir())
            self.assertTrue((prepared.out / STATEMENT_NAME).is_file())
            self.assertTrue((prepared.out / RELEASE_NAME).is_file())

    def test_the_fixture_copy_verifies_to_the_same_digest(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            copied = verify_fixture(prepared.out / FIXTURE_DIRECTORY)
            self.assertEqual(
                copied["fixture_digest"], document["fixture"]["fixture_digest"]
            )

    def test_the_statement_is_the_bytes_that_were_handed_over(self):
        """A re-encoded document is a different document, and the release
        digests the bytes."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            written = (prepared.out / STATEMENT_NAME).read_bytes()
            self.assertEqual(written, prepared.statement.read_bytes())
            import hashlib

            self.assertEqual(
                document["statement"]["sha256"], hashlib.sha256(written).hexdigest()
            )

    def test_the_document_records_what_verification_established(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            report = verify_fixture(prepared.fixture)
            self.assertEqual(
                document["verified"]["evidence_counts"], report["evidence_counts"]
            )
            self.assertEqual(document["verified"]["block_hash"], report["block_hash"])
            self.assertIs(document["verified"]["canonical_chain_claim"], False)

    def test_the_document_names_every_check_the_binding_made(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            self.assertEqual(document["binding"]["checks"], list(CHECKS))

    def test_the_document_on_disk_is_the_document_returned(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            self.assertEqual(loads((prepared.out / RELEASE_NAME).read_bytes()), document)

    def test_the_release_digest_covers_the_document(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            self.assertEqual(document["release_digest"], release_digest(document))
            for field in ("fixture", "statement", "verified", "binding"):
                edited = copy.deepcopy(document)
                edited[field] = {"tampered": True}
                with self.subTest(field=field):
                    self.assertNotEqual(release_digest(edited), document["release_digest"])

    def test_nothing_is_staged_once_the_release_is_written(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            self.assertEqual(prepared.staged(), [])


class ReceiptAwareReleaseTests(unittest.TestCase):
    def test_v2_records_the_recomputed_root_four_counts_and_witness(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            report = verify_fixture(prepared.fixture)
            document = prepared.release()

            self.assertEqual(document["schema_version"], 2)
            self.assertEqual(
                document["statement"]["predicate_type"], STATE_FIXTURE_TYPE_V2
            )
            self.assertEqual(
                document["verified"]["receipts_root"], report["receipts_root"]
            )
            self.assertEqual(
                document["verified"]["evidence_counts"], report["evidence_counts"]
            )
            self.assertEqual(
                set(document["verified"]["evidence_counts"]),
                {
                    "proof_backed",
                    "header_bound",
                    "recorded_rpc",
                    "receipt_trie_proved",
                },
            )
            self.assertTrue(
                (prepared.out / FIXTURE_DIRECTORY / "receipt-witness.json").is_file()
            )
            self.assertNotIn("transaction_hash", json.dumps(document).lower())

    def test_v2_verifies_after_its_source_fixture_is_unavailable(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            document = prepared.release()
            shutil.rmtree(prepared.fixture)
            report = verify_release(prepared.out)
            self.assertEqual(
                report["receipts_root"], document["verified"]["receipts_root"]
            )

    def test_v1_and_v2_statements_are_not_cross_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            statement = copy.deepcopy(prepared.document)
            statement["predicateType"] = STATE_FIXTURE_TYPE
            prepared.write_statement(statement)
            with self.assertRaisesRegex(IntegrityError, "state-fixture/v2"):
                prepared.release()
            self.assertFalse(prepared.out.exists())
            self.assertEqual(prepared.staged(), [])

    def test_release_and_fixture_versions_are_not_cross_read(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            prepared.release()
            document = loads((prepared.out / RELEASE_NAME).read_bytes())
            document["schema_version"] = 1
            del document["verified"]["receipts_root"]
            del document["verified"]["evidence_counts"]["receipt_trie_proved"]
            document["statement"]["predicate_type"] = STATE_FIXTURE_TYPE
            document["release_digest"] = release_digest(document)
            (prepared.out / RELEASE_NAME).write_bytes(dumps(document) + b"\n")
            with self.assertRaisesRegex(IntegrityError, "never upgraded implicitly"):
                verify_release(prepared.out)

    def test_restamped_v2_root_count_statement_and_release_drift_are_refused(self):
        edits = (
            ("root", lambda document: document["verified"].__setitem__(
                "receipts_root", "0x" + "99" * 32
            )),
            ("count", lambda document: document["verified"]["evidence_counts"].__setitem__(
                "receipt_trie_proved", 3
            )),
        )
        for name, edit in edits:
            with tempfile.TemporaryDirectory() as directory:
                prepared = PreparedV2(directory)
                prepared.release()
                document = loads((prepared.out / RELEASE_NAME).read_bytes())
                edit(document)
                document["release_digest"] = release_digest(document)
                (prepared.out / RELEASE_NAME).write_bytes(dumps(document) + b"\n")
                with self.subTest(field=name), self.assertRaises(IntegrityError):
                    verify_release(prepared.out)

        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            prepared.release()
            statement = prepared.out / STATEMENT_NAME
            statement.write_bytes(statement.read_bytes() + b" ")
            with self.assertRaisesRegex(IntegrityError, "statement digests"):
                verify_release(prepared.out)


class RefusedReleaseTests(unittest.TestCase):
    """Every one of these must also leave nothing behind."""

    def refuse(self, prepared, error=LazarusError, **changes):
        with self.assertRaises(error) as caught:
            prepared.release(**changes)
        out = Path(changes.get("out", prepared.out))
        self.assertFalse(out.exists(), "an output directory was left behind")
        self.assertEqual(prepared.staged(), [], "a staged directory was left behind")
        return caught.exception

    def test_a_statement_claiming_more_than_the_records_support_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = copy.deepcopy(prepared.document)
            document["predicate"]["evidence"]["proof_backed"] += 4
            document["predicate"]["evidence"]["recorded_rpc"] = 0
            prepared.write_statement(document)
            error = self.refuse(prepared, IntegrityError)
            self.assertIn("proof_backed", str(error))
            self.assertIn("more than the records support", str(error))

    def test_v2_refuses_subject_references_ariadne_would_reject(self):
        def uncover_current(document):
            document["predicate"]["deltas"]["current"]["digest"] = {
                "sha256": "9" * 64
            }

        def uncover_claim(document):
            document["predicate"]["claims"] = [
                {
                    "name": "receipt membership",
                    "subject": {"sha256": "9" * 64},
                    "disposition": "passed",
                }
            ]

        for name, mutate in (
            ("current delta", uncover_current),
            ("claim", uncover_claim),
        ):
            with tempfile.TemporaryDirectory() as directory:
                prepared = PreparedV2(directory)
                mutate(prepared.document)
                prepared.write_statement(prepared.document)
                with self.subTest(reference=name):
                    self.refuse(prepared, IntegrityError)

    def test_v2_refuses_noncanonical_chain_hash_spellings(self):
        for field in ("block_hash", "state_root", "receipts_root"):
            with tempfile.TemporaryDirectory() as directory:
                prepared = PreparedV2(directory)
                value = prepared.document["predicate"]["chain"][field]
                prepared.document["predicate"]["chain"][field] = (
                    value.upper().replace("0X", "0x")
                )
                prepared.write_statement(prepared.document)
                with self.subTest(field=field):
                    self.refuse(prepared, IntegrityError)

    def test_a_statement_about_another_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = copy.deepcopy(prepared.document)
            document["predicate"]["chain"]["block_hash"] = "0x" + "99" * 32
            prepared.write_statement(document)
            self.refuse(prepared, IntegrityError)

    def test_a_fixture_that_does_not_verify_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            component = prepared.fixture / "plan.json"
            component.write_bytes(
                component.read_bytes().replace(b"ethereum-mainnet", b"ethereum-testnet")
            )
            error = self.refuse(prepared, IntegrityError)
            self.assertIn("plan.json", str(error))

    def test_an_output_that_already_exists_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.out.mkdir()
            with self.assertRaises(FormatError) as caught:
                prepared.release()
            self.assertIn("already exists", str(caught.exception))
            self.assertEqual(sorted(prepared.out.iterdir()), [])

    def test_an_output_that_is_a_file_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.out.write_bytes(b"not a release")
            with self.assertRaises(FormatError):
                prepared.release()

    def test_an_output_inside_the_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            error = self.refuse(
                prepared, FormatError, out=prepared.fixture / "release"
            )
            self.assertIn("inside the fixture", str(error))

    def test_an_output_that_is_the_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(FormatError) as caught:
                prepared.release(out=prepared.fixture)
            self.assertIn("is the fixture", str(caught.exception))

    def test_a_fixture_inside_the_output_is_refused(self):
        """The output already exists here, so the absence check the other cases
        make does not apply; the overlap is what is being refused."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(FormatError) as caught:
                prepared.release(out=prepared.root)
            self.assertIn("sits inside", str(caught.exception))
            self.assertEqual(prepared.staged(), [])

    def test_an_output_whose_parent_does_not_exist_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            error = self.refuse(
                prepared, FormatError, out=prepared.root / "missing" / "release"
            )
            self.assertIn("parent", str(error))

    @unittest.skipIf(
        hasattr(os, "geteuid") and os.geteuid() == 0,
        "root ignores directory permissions, so there is nothing to refuse",
    )
    def test_an_output_that_cannot_be_written_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            closed = prepared.root / "closed"
            closed.mkdir(mode=0o500)
            try:
                with self.assertRaises(OSError):
                    prepared.release(out=closed / "release")
            finally:
                closed.chmod(0o700)

    def test_a_statement_that_is_not_json_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.statement.write_bytes(b"{not json")
            self.refuse(prepared)

    def test_a_statement_that_is_not_an_object_is_refused(self):
        """Refused by the binding, in the words it uses for every other shape it
        will not read, rather than by a second check here saying the same thing."""
        for text in (b"[]", b'"a statement"', b"12345", b"null", b"true"):
            with tempfile.TemporaryDirectory() as directory:
                prepared = Prepared(directory)
                prepared.statement.write_bytes(text)
                with self.subTest(statement=text):
                    error = self.refuse(prepared, FormatError)
                    self.assertIn("statement must be an object", str(error))

    def test_an_output_that_is_a_dangling_symlink_is_refused(self):
        """`exists` follows the link and says no. The name is still taken, and
        a rename onto it would replace the link rather than write beside it."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.out.symlink_to(prepared.root / "nothing-here")
            with self.assertRaises(FormatError) as caught:
                prepared.release()
            self.assertIn("already exists", str(caught.exception))
            self.assertTrue(prepared.out.is_symlink())
            self.assertEqual(prepared.staged(), [])

    def test_a_statement_carrying_a_number_json_should_not_have_is_refused(self):
        """`json.loads` accepts NaN and Infinity. Nothing downstream would."""
        for text in (b'{"a": NaN}', b'{"a": Infinity}', b'{"a": -Infinity}'):
            with tempfile.TemporaryDirectory() as directory:
                prepared = Prepared(directory)
                prepared.statement.write_bytes(text)
                with self.subTest(statement=text):
                    self.refuse(prepared)

    def test_a_statement_naming_one_key_twice_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.statement.write_bytes(b'{"_type": "a", "_type": "b"}')
            self.refuse(prepared)

    def test_a_statement_that_is_not_a_regular_file_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            error = self.refuse(
                prepared, PathError, statement=prepared.root / "not-there.json"
            )
            self.assertIn("regular file", str(error))

    def test_a_statement_that_is_a_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            somewhere = prepared.root / "a-directory"
            somewhere.mkdir()
            self.refuse(prepared, PathError, statement=somewhere)

    def test_a_statement_that_is_a_symlink_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            link = prepared.root / "linked.json"
            link.symlink_to(prepared.statement)
            error = self.refuse(prepared, PathError, statement=link)
            self.assertIn("symlink", str(error))

    def test_a_statement_below_a_symlinked_parent_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            real = prepared.root / "statement-parent"
            real.mkdir()
            (real / "statement.json").write_bytes(prepared.statement.read_bytes())
            link = prepared.root / "statement-link"
            link.symlink_to(real, target_is_directory=True)

            error = self.refuse(
                prepared, PathError, statement=link / "statement.json"
            )
            self.assertIn("symlink", str(error))

    def test_each_exact_darwin_root_alias_records_its_bounded_class(self):
        aliases = {
            "etc": b"private/etc",
            "tmp": b"private/tmp",
            "var": b"private/var",
        }
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        for alias, link_text in aliases.items():
            with tempfile.TemporaryDirectory() as directory, self.subTest(
                accepted_alias=alias
            ):
                root = Path(directory)
                physical = root / "private" / alias
                physical.mkdir(parents=True)
                (root / alias).symlink_to(os.fsdecode(link_text))
                root_fd = os.open(root, flags)
                opened = None
                try:
                    with mock.patch.object(release_module.sys, "platform", "darwin"):
                        opened = release_module._open_darwin_root_alias(
                            root_fd,
                            alias,
                            flags,
                            Path(f"/{alias}/statement.json"),
                        )
                        self.assertIsNotNone(opened)
                        target_fd, guard = opened
                        self.assertEqual(guard[0], alias)
                        self.assertEqual(guard[1], link_text)
                        self.assertEqual(
                            (os.fstat(target_fd).st_dev, os.fstat(target_fd).st_ino),
                            guard[3],
                        )
                        release_module._recheck_darwin_root_alias(
                            root_fd,
                            guard,
                            flags,
                            Path(f"/{alias}/statement.json"),
                        )
                finally:
                    if opened is not None:
                        os.close(opened[0])
                    os.close(root_fd)

    def test_a_wrong_darwin_root_alias_target_is_refused(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "private" / "elsewhere").mkdir(parents=True)
            (root / "var").symlink_to("private/elsewhere")
            root_fd = os.open(root, flags)
            try:
                with mock.patch.object(
                    release_module.sys, "platform", "darwin"
                ), self.assertRaisesRegex(PathError, "symlink or non-directory"):
                    release_module._open_darwin_root_alias(
                        root_fd,
                        "var",
                        flags,
                        Path("/var/statement.json"),
                    )
            finally:
                os.close(root_fd)

    def test_a_darwin_root_alias_replaced_by_a_directory_is_refused(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "var").mkdir()
            root_fd = os.open(root, flags)
            try:
                with mock.patch.object(
                    release_module.sys, "platform", "darwin"
                ), self.assertRaisesRegex(PathError, "symlink or non-directory"):
                    release_module._open_darwin_root_alias(
                        root_fd,
                        "var",
                        flags,
                        Path("/var/statement.json"),
                    )
            finally:
                os.close(root_fd)

    def test_a_changed_darwin_root_target_identity_is_refused(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "private" / "var"
            target.mkdir(parents=True)
            (root / "var").symlink_to("private/var")
            root_fd = os.open(root, flags)
            opened = None
            try:
                with mock.patch.object(release_module.sys, "platform", "darwin"):
                    opened = release_module._open_darwin_root_alias(
                        root_fd,
                        "var",
                        flags,
                        Path("/var/statement.json"),
                    )
                    self.assertIsNotNone(opened)
                    target.rename(root / "private" / "former-var")
                    target.mkdir()
                    with self.assertRaisesRegex(
                        PathError, "symlink or non-directory"
                    ):
                        release_module._recheck_darwin_root_alias(
                            root_fd,
                            opened[1],
                            flags,
                            Path("/var/statement.json"),
                        )
            finally:
                if opened is not None:
                    os.close(opened[0])
                os.close(root_fd)

    def test_darwin_root_alias_drift_between_checks_is_refused(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "private" / "var").mkdir(parents=True)
            (root / "private" / "other").mkdir()
            alias = root / "var"
            alias.symlink_to("private/var")
            root_fd = os.open(root, flags)
            opened = None
            try:
                with mock.patch.object(release_module.sys, "platform", "darwin"):
                    opened = release_module._open_darwin_root_alias(
                        root_fd,
                        "var",
                        flags,
                        Path("/var/statement.json"),
                    )
                    self.assertIsNotNone(opened)
                    alias.unlink()
                    alias.symlink_to("private/other")
                    with self.assertRaisesRegex(
                        PathError, "symlink or non-directory"
                    ):
                        release_module._recheck_darwin_root_alias(
                            root_fd,
                            opened[1],
                            flags,
                            Path("/var/statement.json"),
                        )
            finally:
                if opened is not None:
                    os.close(opened[0])
                os.close(root_fd)

    def test_a_darwin_root_alias_removed_before_the_recheck_is_refused(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "private" / "var").mkdir(parents=True)
            alias = root / "var"
            alias.symlink_to("private/var")
            root_fd = os.open(root, flags)
            opened = None
            try:
                with mock.patch.object(release_module.sys, "platform", "darwin"):
                    opened = release_module._open_darwin_root_alias(
                        root_fd,
                        "var",
                        flags,
                        Path("/var/statement.json"),
                    )
                    self.assertIsNotNone(opened)
                    alias.unlink()
                    with self.assertRaisesRegex(
                        PathError, "symlink or non-directory"
                    ):
                        release_module._recheck_darwin_root_alias(
                            root_fd,
                            opened[1],
                            flags,
                            Path("/var/statement.json"),
                        )
            finally:
                if opened is not None:
                    os.close(opened[0])
                os.close(root_fd)

    def test_a_fixed_shaped_alias_below_root_is_still_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            physical = prepared.root / "private" / "var"
            physical.mkdir(parents=True)
            nested = prepared.root / "var"
            nested.symlink_to("private/var")
            (physical / "statement.json").write_bytes(
                prepared.statement.read_bytes()
            )

            error = self.refuse(
                prepared,
                PathError,
                statement=nested / "statement.json",
            )
            self.assertIn("symlink", str(error))

    @unittest.skipUnless(
        sys.platform == "darwin",
        "macOS root aliases exist only on Darwin",
    )
    def test_a_parent_segment_cannot_normalise_into_a_darwin_root_alias(self):
        with tempfile.TemporaryDirectory(
            prefix="fiat881-alias-parent-"
        ) as directory:
            root = Path(directory)
            deep = root / "elsewhere" / "deep"
            deep.mkdir(parents=True)
            (root / "gate").symlink_to(deep, target_is_directory=True)
            filename = f"{root.name}-statement.json"
            kernel_path = root / filename
            normalised_path = root.parent / filename
            kernel_path.write_bytes(b"kernel-path-bytes")
            with normalised_path.open("xb") as handle:
                handle.write(b"normalised-path-bytes")
            handed = root / "gate" / ".." / ".." / filename
            try:
                self.assertNotEqual(
                    os.path.realpath(handed),
                    os.path.abspath(handed),
                )
                with self.assertRaisesRegex(PathError, "parent segment"):
                    release_module._read_statement(handed)
            finally:
                normalised_path.unlink(missing_ok=True)

    def test_linux_does_not_enter_the_darwin_root_alias_exception(self):
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "private" / "var").mkdir(parents=True)
            (root / "var").symlink_to("private/var")
            root_fd = os.open(root, flags)
            try:
                with mock.patch.object(release_module.sys, "platform", "linux"):
                    self.assertIsNone(
                        release_module._open_darwin_root_alias(
                            root_fd,
                            "var",
                            flags,
                            Path("/var/statement.json"),
                        )
                    )
            finally:
                os.close(root_fd)

    @unittest.skipUnless(
        sys.platform == "darwin",
        "default macOS temporary roots exist only on Darwin",
    )
    def test_default_macos_temporary_statement_writes_and_verifies_a_release(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            accepted_alias = Path(directory).parts[1]
            self.assertIn(accepted_alias, release_module._DARWIN_ROOT_ALIASES)
            written = prepared.release()
            verified = verify_release(prepared.out)

            self.assertEqual(
                written["statement"]["sha256"],
                verified["statement_sha256"],
            )
            self.assertEqual(
                written["release_digest"],
                verified["release_digest"],
            )

    def test_a_checked_statement_cannot_be_swapped_to_a_symlink_before_read(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            outside = prepared.root / "matching-statement.json"
            outside.write_bytes(prepared.statement.read_bytes())
            mismatching = copy.deepcopy(prepared.document)
            mismatching["predicate"]["chain"]["block_hash"] = "0x" + "99" * 32
            prepared.write_statement(mismatching)

            original_is_file = Path.is_file
            swapped = {"done": False}

            def swap_after_check(path):
                result = original_is_file(path)
                if path == prepared.statement and result and not swapped["done"]:
                    swapped["done"] = True
                    path.unlink()
                    path.symlink_to(outside)
                return result

            with mock.patch.object(Path, "is_file", swap_after_check):
                self.refuse(prepared, IntegrityError)
            self.assertFalse(swapped["done"])

    def test_a_statement_larger_than_the_read_cap_is_refused(self):
        from lazarus_lib.canonical import MAX_JSON_BYTES

        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.statement.write_bytes(b'{"a": "' + b"x" * MAX_JSON_BYTES + b'"}')
            error = self.refuse(prepared, FormatError)
            self.assertIn(str(MAX_JSON_BYTES), str(error))

    def test_an_oversized_statement_is_refused_before_its_body_is_read(self):
        from lazarus_lib.canonical import MAX_JSON_BYTES

        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with prepared.statement.open("wb") as handle:
                handle.truncate(MAX_JSON_BYTES + 1)
            with mock.patch.object(
                Path,
                "read_bytes",
                side_effect=AssertionError("oversized statement body was read"),
            ):
                error = self.refuse(prepared, FormatError)
            self.assertIn(str(MAX_JSON_BYTES), str(error))

    def test_a_staged_directory_already_in_the_way_is_refused(self):
        """Its name is not a release, and a run that overwrote it would be
        writing over whatever left it there."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            (prepared.root / (".%s.staged" % prepared.out.name)).mkdir()
            with self.assertRaises(FormatError) as caught:
                prepared.release()
            self.assertIn("staged", str(caught.exception))
            self.assertFalse(prepared.out.exists())

    def test_a_statement_inside_the_fixture_is_refused(self):
        """It refuses itself either way: an unlisted file fails verification, a
        listed one would have to carry its own digest. Neither refusal names the
        reason, and the reason is that the fixture digest would cover the
        statement made about the fixture."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            inside = prepared.fixture / "statement.json"
            inside.write_bytes(prepared.statement.read_bytes())
            error = self.refuse(prepared, FormatError, statement=inside)
            self.assertIn("sits inside the fixture it describes", str(error))

    def test_a_statement_below_the_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            below = prepared.fixture / "schemas"
            below.mkdir(exist_ok=True)
            inside = below / "statement.json"
            inside.write_bytes(prepared.statement.read_bytes())
            error = self.refuse(prepared, FormatError, statement=inside)
            self.assertIn("sits inside", str(error))

    def test_a_statement_path_through_a_symlink_loop_is_refused(self):
        """Which refusal you get depends on the interpreter, and that is fine.

        Up to Python 3.12 `Path.resolve` raises on a loop and the containment
        check refuses it. From 3.13 it resolves the loop to a path instead, and
        the read refuses it a moment later. Either way it is refused, which is
        the claim; the branch that turns a resolve failure into a refusal is
        covered directly below rather than by asking the operating system to
        produce one.
        """
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            first = prepared.root / "loop-a"
            second = prepared.root / "loop-b"
            first.symlink_to(second)
            second.symlink_to(first)
            self.refuse(prepared, PathError, statement=first / "statement.json")

    def test_a_path_the_interpreter_cannot_resolve_is_refused(self):
        """The guard itself, without depending on what any interpreter does.

        Skipping the containment check because a path would not resolve is the
        quiet failure this plugin refuses everywhere else. `pathlib` reports a
        loop as a `RuntimeError` on some versions and an `OSError` on others, so
        both are put through it here.
        """
        for raised in (OSError(62, "Too many levels of symbolic links"),
                       RuntimeError("Symlink loop from '/somewhere'")):
            with tempfile.TemporaryDirectory() as directory:
                prepared = Prepared(directory)
                original = Path.resolve

                def refusing(self, *arguments, **keywords):
                    raise raised

                Path.resolve = refusing
                try:
                    with self.subTest(raised=type(raised).__name__):
                        with self.assertRaises(PathError) as caught:
                            prepared.release()
                        self.assertIn("cannot resolve the", str(caught.exception))
                finally:
                    Path.resolve = original

    def test_a_statement_beside_the_fixture_is_read(self):
        """The rule is about being inside, not about being nearby."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            beside = prepared.fixture.parent / "fixture-source-statement.json"
            beside.write_bytes(prepared.statement.read_bytes())
            prepared.release(statement=beside)
            self.assertTrue((prepared.out / RELEASE_NAME).is_file())

    def test_a_fixture_that_is_not_there_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            self.refuse(prepared, fixture=prepared.root / "no-fixture")


class KilledRunTests(unittest.TestCase):
    def test_a_run_killed_while_writing_leaves_no_release(self):
        """The copy is the longest part, so that is where the kill lands."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module._copy_fixture

            def killed(*arguments, **keywords):
                original(*arguments, **keywords)
                raise KeyboardInterrupt("killed mid-write")

            module._copy_fixture = killed
            try:
                with self.assertRaises(KeyboardInterrupt):
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertFalse(prepared.out.exists())
            self.assertEqual(prepared.staged(), [])

    def test_a_copy_of_another_fixture_leaves_no_release(self):
        """A copy that verifies is not enough. It has to verify to the digest
        the release records, or the release describes a fixture it does not
        hold."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            other = prepared.root / "other-fixture"
            other.mkdir()
            write_fixture(other, hash_source="a second synthetic offline test vector")
            from lazarus_lib import release as module

            original = module._copy_fixture

            def elsewhere(source, target, manifest):
                original(other, target, verify_fixture(other)["manifest"])

            module._copy_fixture = elsewhere
            try:
                with self.assertRaises(IntegrityError) as caught:
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertIn("verifies to", str(caught.exception))
            self.assertFalse(prepared.out.exists())
            self.assertEqual(prepared.staged(), [])

    def test_a_copy_that_does_not_verify_leaves_no_release(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module._copy_fixture

            def short(source, target, manifest):
                original(source, target, manifest)
                (target / "plan.json").write_bytes(b"{}")

            module._copy_fixture = short
            try:
                with self.assertRaises(IntegrityError):
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertFalse(prepared.out.exists())
            self.assertEqual(prepared.staged(), [])


class OneReadTests(unittest.TestCase):
    """The decision the module docstring leads with, pinned.

    Verification and binding both need the manifest. Reading it twice reads two
    states, and nothing after the first read would notice a component changing
    between them.
    """

    def test_the_binding_is_given_the_manifest_the_report_was_computed_from(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module.bind
            seen = {}

            def watched(statement, manifest, report):
                seen["manifest"] = manifest
                seen["report"] = report
                return original(statement, manifest, report)

            module.bind = watched
            try:
                prepared.release()
            finally:
                module.bind = original
            self.assertIs(seen["manifest"], seen["report"]["manifest"])

    def test_reading_a_release_binds_against_the_manifest_the_report_carried(self):
        """The same decision as the write, at the site the write's test does not
        reach.

        Mutation found this one: replacing the read's manifest with a second
        read of the directory left the suite green, because in a test nothing
        changes between the two reads. What the rule is for is the case where
        something does, and an identity check pins it without having to stage a
        race.
        """
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            from lazarus_lib import release as module

            original = module.bind
            seen = {}

            def watched(statement, manifest, report):
                seen["manifest"] = manifest
                seen["report"] = report
                return original(statement, manifest, report)

            module.bind = watched
            try:
                verify_release(prepared.out)
            finally:
                module.bind = original
            self.assertIs(seen["manifest"], seen["report"]["manifest"])

    def test_a_release_records_the_digest_the_report_carried(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            report = verify_fixture(prepared.fixture)
            self.assertEqual(
                document["fixture"]["fixture_digest"],
                report["manifest"]["fixture_digest"],
            )


class DocumentTests(unittest.TestCase):
    def test_a_document_the_schema_refuses_is_not_returned(self):
        """The block hash comes out of verification lowercased. A report that
        carried it otherwise would build a document the schema refuses, and the
        release must not be the thing that discovers this later."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            report = verify_fixture(prepared.fixture)
            report["block_hash"] = report["block_hash"].upper().replace("0X", "0x")
            with self.assertRaises(FormatError):
                build_release(prepared.document, b"{}", report, list(CHECKS))

    def test_a_document_with_no_checks_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            report = verify_fixture(prepared.fixture)
            with self.assertRaises(FormatError):
                build_release(prepared.document, b"{}", report, [])

    def test_a_check_that_names_nothing_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            report = verify_fixture(prepared.fixture)
            for name in ("", "   ", "\u200b"):
                with self.subTest(check=repr(name)), self.assertRaises(FormatError):
                    build_release(prepared.document, b"{}", report, [name])


class CopyTests(unittest.TestCase):
    def test_the_copy_holds_the_manifest_and_every_component(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            copied = prepared.out / FIXTURE_DIRECTORY
            held = {
                path.relative_to(copied).as_posix()
                for path in copied.rglob("*")
                if path.is_file()
            }
            self.assertEqual(held, {"manifest.json"} | set(COMPONENTS))

    def test_the_copy_is_byte_for_byte(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            for relative in ("manifest.json",) + COMPONENTS:
                with self.subTest(component=relative):
                    self.assertEqual(
                        (prepared.out / FIXTURE_DIRECTORY / relative).read_bytes(),
                        (prepared.fixture / relative).read_bytes(),
                    )

    def test_a_file_the_manifest_does_not_list_does_not_ride_along(self):
        """Verification refuses an unlisted file, so this cannot happen through
        the command. The copy is driven by the manifest anyway."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib.release import _copy_fixture

            report = verify_fixture(prepared.fixture)
            (prepared.fixture / "stowaway.txt").write_bytes(b"not listed")
            target = prepared.root / "copy"
            _copy_fixture(prepared.fixture, target, report["manifest"])
            self.assertFalse((target / "stowaway.txt").exists())

    def test_a_component_grown_after_verification_is_not_copied(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            report = verify_fixture(prepared.fixture)
            target = prepared.root / "copy"
            victim = "plan.json"
            grown = (prepared.fixture / victim).read_bytes() + b"x"
            from lazarus_lib import release as module

            original = module.read_confined_bytes

            def changed(root, relative, *, max_bytes):
                if relative == victim:
                    if len(grown) > max_bytes:
                        raise ResourceLimitError("simulated post-verification growth")
                    return grown
                return original(root, relative, max_bytes=max_bytes)

            with mock.patch.object(
                module, "read_confined_bytes", side_effect=changed
            ):
                with self.assertRaises(ResourceLimitError):
                    module._copy_fixture(
                        prepared.fixture, target, report["manifest"]
                    )
            self.assertFalse((target / victim).exists())

    def test_a_same_size_component_change_is_refused_before_copying(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            report = verify_fixture(prepared.fixture)
            target = prepared.root / "copy"
            victim = "plan.json"
            original_bytes = (prepared.fixture / victim).read_bytes()
            changed_bytes = bytes([original_bytes[0] ^ 1]) + original_bytes[1:]
            from lazarus_lib import release as module

            original = module.read_confined_bytes

            def changed(root, relative, *, max_bytes):
                if relative == victim:
                    return changed_bytes
                return original(root, relative, max_bytes=max_bytes)

            with mock.patch.object(
                module, "read_confined_bytes", side_effect=changed
            ):
                with self.assertRaisesRegex(IntegrityError, "after verification"):
                    module._copy_fixture(
                        prepared.fixture, target, report["manifest"]
                    )
            self.assertFalse((target / victim).exists())

    def test_the_copy_is_not_writable_by_anybody_else(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            mode = stat.S_IMODE(os.stat(prepared.out / FIXTURE_DIRECTORY).st_mode)
            self.assertEqual(mode & (stat.S_IWGRP | stat.S_IWOTH), 0)


class ReproducibleTests(unittest.TestCase):
    def test_two_runs_over_one_fixture_and_statement_agree(self):
        """A release nobody can rebuild is a release nobody can check."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            first = prepared.release()
            again = prepared.root / "release-again"
            second = write_release(prepared.fixture, prepared.statement, again)
            self.assertEqual(first, second)
            self.assertEqual(
                (prepared.out / RELEASE_NAME).read_bytes(),
                (again / RELEASE_NAME).read_bytes(),
            )
            for relative in ("manifest.json",) + COMPONENTS:
                with self.subTest(component=relative):
                    self.assertEqual(
                        (prepared.out / FIXTURE_DIRECTORY / relative).read_bytes(),
                        (again / FIXTURE_DIRECTORY / relative).read_bytes(),
                    )


class DigestIdentityTests(unittest.TestCase):
    """The claim the digest function's docstring makes, held to.

    A field added to the schema and not to the identity is a digest that quietly
    stops covering part of the document. This is the test that makes that a
    failure rather than a discovery.
    """

    def test_the_digest_covers_every_field_the_schema_requires(self):
        from lazarus_lib.schemas import _schema

        required = set(_schema("release", 1)["required"]) - {"release_digest"}
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            for field in sorted(required):
                edited = copy.deepcopy(document)
                edited[field] = "changed"
                with self.subTest(field=field):
                    self.assertNotEqual(
                        release_digest(edited),
                        document["release_digest"],
                        "%s is required by the schema and not covered by the digest"
                        % field,
                    )

    def test_the_digest_does_not_cover_itself(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = prepared.release()
            edited = copy.deepcopy(document)
            edited["release_digest"] = "f" * 64
            self.assertEqual(release_digest(edited), release_digest(document))


class RenameWindowTests(unittest.TestCase):
    """What a lost race costs, recorded rather than assumed.

    The output name is free when a run begins and the copy takes time. Between
    the last check and the rename the name is still unheld. Rename replaces an
    empty directory and nothing else, so these tests record where the boundary
    sits.
    """

    def race(self, prepared, prepare):
        from lazarus_lib import release as module

        original = module.os.replace

        def racing(source, target, *arguments, **keywords):
            path = Path(target)
            if not path.exists() and not path.is_symlink():
                prepare(path)
            return original(source, target, *arguments, **keywords)

        module.os.replace = racing
        try:
            return prepared.release()
        finally:
            module.os.replace = original

    def test_a_directory_holding_anything_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)

            def prepare(path):
                path.mkdir()
                (path / "someone-elses.txt").write_bytes(b"mine")

            with self.assertRaises(OSError):
                self.race(prepared, prepare)
            self.assertTrue((prepared.out / "someone-elses.txt").is_file())
            self.assertEqual(prepared.staged(), [])

    def test_a_file_in_the_way_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(OSError):
                self.race(prepared, lambda path: path.write_bytes(b"mine"))
            self.assertEqual(prepared.out.read_bytes(), b"mine")
            self.assertEqual(prepared.staged(), [])

    def test_a_symlink_in_the_way_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            with self.assertRaises(OSError):
                self.race(
                    prepared, lambda path: path.symlink_to(prepared.root / "nowhere")
                )
            self.assertTrue(prepared.out.is_symlink())
            self.assertEqual(prepared.staged(), [])

    def test_an_output_that_appears_during_the_copy_is_refused(self):
        """The check before the rename, which the long part of the run makes
        worth making."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            from lazarus_lib import release as module

            original = module._copy_fixture

            def slow(source, target, manifest):
                original(source, target, manifest)
                prepared.out.mkdir()

            module._copy_fixture = slow
            try:
                with self.assertRaises(FormatError) as caught:
                    prepared.release()
            finally:
                module._copy_fixture = original
            self.assertIn("appeared while it was built", str(caught.exception))
            self.assertTrue(prepared.out.is_dir())
            self.assertEqual(prepared.staged(), [])


class StagedNameTests(unittest.TestCase):
    def test_a_staged_name_taken_by_something_else_is_refused(self):
        for kind in ("symlink", "file", "directory"):
            with tempfile.TemporaryDirectory() as directory:
                prepared = Prepared(directory)
                staged = prepared.root / (".%s.staged" % prepared.out.name)
                if kind == "symlink":
                    staged.symlink_to(prepared.root / "nowhere")
                elif kind == "file":
                    staged.write_bytes(b"not a staging directory")
                else:
                    staged.mkdir()
                with self.subTest(kind=kind):
                    with self.assertRaises(FormatError) as caught:
                        prepared.release()
                    self.assertIn("staged", str(caught.exception))
                    self.assertTrue(staged.exists() or staged.is_symlink())
                    self.assertFalse(prepared.out.exists())


class ModeTests(unittest.TestCase):
    def test_nothing_in_a_release_is_readable_by_anybody_else(self):
        """A release is not published by being written. Whoever hands it over
        opens it up deliberately."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            for path in [prepared.out] + sorted(prepared.out.rglob("*")):
                mode = stat.S_IMODE(path.stat().st_mode)
                with self.subTest(path=path.name):
                    self.assertEqual(
                        mode & (stat.S_IRWXG | stat.S_IRWXO),
                        0,
                        "%s is %s" % (path, oct(mode)),
                    )


class CommandTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(CLI), "release", *[str(a) for a in arguments]],
            capture_output=True,
            text=True,
        )

    def test_the_command_writes_a_release_and_prints_the_counts(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            result = self.run_cli(
                prepared.fixture, "--statement", prepared.statement, "--out", prepared.out
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("release: ", result.stdout)
            self.assertIn("proof-backed: 3", result.stdout)
            self.assertIn("header-bound: 1", result.stdout)
            self.assertIn("recorded-rpc: 1", result.stdout)
            for check in CHECKS:
                self.assertIn(check, result.stdout)

    def test_the_command_refuses_a_statement_that_claims_more(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            document = copy.deepcopy(prepared.document)
            document["predicate"]["evidence"]["proof_backed"] += 1
            prepared.write_statement(document)
            result = self.run_cli(
                prepared.fixture, "--statement", prepared.statement, "--out", prepared.out
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("more than the records support", result.stderr)
            self.assertEqual(result.stdout, "")
            self.assertFalse(prepared.out.exists())

    def test_the_command_validates_the_document_it_wrote(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            self.run_cli(
                prepared.fixture, "--statement", prepared.statement, "--out", prepared.out
            )
            checked = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "validate",
                    "release",
                    str(prepared.out / RELEASE_NAME),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(checked.returncode, 0, checked.stderr)


if __name__ == "__main__":
    unittest.main()


class VerifiedReleaseTests(unittest.TestCase):
    """Reading a release back, and refusing to.

    Everything the write did is done again from the bytes on disk. Nothing is
    taken from the document except the two paths it names, because a document
    checking itself against its own numbers checks nothing.
    """

    def released(self, directory):
        prepared = Prepared(directory)
        prepared.release()
        return prepared

    def test_a_release_written_by_the_command_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            report = verify_release(prepared.out)
            written = json.loads((prepared.out / RELEASE_NAME).read_bytes())
            self.assertEqual(report["release_digest"], written["release_digest"])
            self.assertEqual(
                report["fixture_digest"], written["fixture"]["fixture_digest"]
            )
            self.assertEqual(report["checks"], list(CHECKS))

    def test_it_reports_what_the_fixture_verifies_to(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            report = verify_release(prepared.out)
            fixture = verify_fixture(prepared.fixture)
            self.assertEqual(report["evidence_counts"], fixture["evidence_counts"])
            self.assertEqual(report["block_hash"], fixture["block_hash"])
            self.assertEqual(report["predicate_type"], STATE_FIXTURE_TYPE)

    def test_a_component_byte_edited_after_the_fact_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            component = prepared.out / FIXTURE_DIRECTORY / "plan.json"
            edited = component.read_bytes().replace(
                b"ethereum-mainnet", b"ethereum-testnet", 1
            )
            self.assertNotEqual(edited, component.read_bytes())
            component.write_bytes(edited)
            with self.assertRaises(IntegrityError) as caught:
                verify_release(prepared.out)
            self.assertIn("plan.json", str(caught.exception))

    def test_a_statement_edited_after_the_fact_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            document = json.loads((prepared.out / STATEMENT_NAME).read_bytes())
            document["predicate"]["evidence"]["proof_backed"] += 1
            (prepared.out / STATEMENT_NAME).write_bytes(
                json.dumps(document).encode()
            )
            with self.assertRaises(IntegrityError) as caught:
                verify_release(prepared.out)
            self.assertIn("the statement digests to", str(caught.exception))

    def test_a_statement_reformatted_but_unchanged_is_refused(self):
        """The release digests bytes. Re-encoding is a different document even
        when it says the same thing, and a release that accepted it would be
        recording a digest nobody can reproduce."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            document = json.loads((prepared.out / STATEMENT_NAME).read_bytes())
            (prepared.out / STATEMENT_NAME).write_bytes(
                json.dumps(document, indent=4).encode()
            )
            with self.assertRaises(IntegrityError):
                verify_release(prepared.out)

    def test_a_document_edited_after_the_fact_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
            document["verified"]["evidence_counts"]["proof_backed"] += 1
            (prepared.out / RELEASE_NAME).write_bytes(json.dumps(document).encode())
            with self.assertRaises(IntegrityError) as caught:
                verify_release(prepared.out)
            self.assertIn("release digest does not cover", str(caught.exception))

    def test_a_document_edited_and_restamped_is_refused(self):
        """Restamping the digest gets past the digest and into the numbers,
        which is where the fixture disagrees."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
            document["verified"]["evidence_counts"]["proof_backed"] += 1
            document["release_digest"] = release_digest(document)
            (prepared.out / RELEASE_NAME).write_bytes(json.dumps(document).encode())
            with self.assertRaises(IntegrityError) as caught:
                verify_release(prepared.out)
            self.assertIn("evidence counts", str(caught.exception))

    def test_each_recorded_claim_restamped_is_refused(self):
        """One at a time, with the digest restamped each time, so what is being
        refused is the claim rather than the digest."""
        edits = {
            "the fixture digest": ("fixture", "fixture_digest", "f" * 64),
            "the statement digest": ("statement", "sha256", "e" * 64),
            "the block": ("verified", "block_hash", "0x" + "99" * 32),
        }
        for what, (block, field, value) in edits.items():
            with tempfile.TemporaryDirectory() as directory:
                prepared = self.released(directory)
                document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
                document[block][field] = value
                document["release_digest"] = release_digest(document)
                (prepared.out / RELEASE_NAME).write_bytes(
                    json.dumps(document).encode()
                )
                with self.subTest(claim=what), self.assertRaises(IntegrityError):
                    verify_release(prepared.out)

    def test_a_check_the_binding_does_not_make_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
            document["binding"]["checks"] = ["everything-was-fine"]
            document["release_digest"] = release_digest(document)
            (prepared.out / RELEASE_NAME).write_bytes(json.dumps(document).encode())
            with self.assertRaises(IntegrityError) as caught:
                verify_release(prepared.out)
            self.assertIn("everything-was-fine", str(caught.exception))

    def test_a_predicate_type_the_statement_does_not_declare_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
            document["statement"]["predicate_type"] = "https://example.invalid/x/v1"
            document["release_digest"] = release_digest(document)
            (prepared.out / RELEASE_NAME).write_bytes(json.dumps(document).encode())
            with self.assertRaises(IntegrityError) as caught:
                verify_release(prepared.out)
            self.assertIn("example.invalid", str(caught.exception))

    def test_a_document_claiming_the_canonical_chain_is_refused(self):
        """The schema pins the field to false, which is why nothing in
        `verify_release` checks it: a document claiming it does not get that
        far."""
        for value in (True, "false", 0, 1, None, "no"):
            with tempfile.TemporaryDirectory() as directory:
                prepared = self.released(directory)
                document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
                document["verified"]["canonical_chain_claim"] = value
                document["release_digest"] = release_digest(document)
                (prepared.out / RELEASE_NAME).write_bytes(
                    json.dumps(document).encode()
                )
                with self.subTest(claim=value), self.assertRaises(FormatError):
                    verify_release(prepared.out)

    def test_a_report_claiming_the_canonical_chain_is_refused_by_the_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            from lazarus_lib import release as module

            original = module.verify_fixture

            def claiming(root):
                report = original(root)
                report["header_bound"]["canonical_chain_claim"] = True
                return report

            module.verify_fixture = claiming
            try:
                with self.assertRaises(IntegrityError) as caught:
                    verify_release(prepared.out)
            finally:
                module.verify_fixture = original
            self.assertIn("canonical chain", str(caught.exception))

    def test_a_release_missing_each_of_its_three_parts_is_refused(self):
        for part in (RELEASE_NAME, STATEMENT_NAME, FIXTURE_DIRECTORY):
            with tempfile.TemporaryDirectory() as directory:
                prepared = self.released(directory)
                target = prepared.out / part
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
                with self.subTest(part=part), self.assertRaises(LazarusError):
                    verify_release(prepared.out)

    def test_a_file_the_document_does_not_account_for_is_refused(self):
        """The same rule the fixture manifest applies to its own directory."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            (prepared.out / "stowaway.txt").write_bytes(b"unaccounted for")
            with self.assertRaises(IntegrityError) as caught:
                verify_release(prepared.out)
            self.assertIn("stowaway.txt", str(caught.exception))

    def test_a_symlink_beside_the_document_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            (prepared.out / "link.json").symlink_to(prepared.out / RELEASE_NAME)
            with self.assertRaises(PathError) as caught:
                verify_release(prepared.out)
            self.assertIn("symlink", str(caught.exception))

    def test_a_fixture_reached_through_a_symlinked_segment_is_refused(self):
        """`list_fixture_files` refuses a symlinked fixture root and
        `read_confined_bytes` refuses a symlinked component. Neither sees the
        segments in between, and O_NOFOLLOW applies only to the last one.

        The symlink is buried a level down on purpose. At the top of the release
        it would be refused for being an unaccounted symlink, which would leave
        the confinement rule untested while looking tested.
        """
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            outside = prepared.root / "outside"
            shutil.move(str(prepared.out / FIXTURE_DIRECTORY), str(outside))
            nest = prepared.out / "nest"
            nest.mkdir()
            (nest / "through").symlink_to(outside.parent)
            document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
            document["fixture"]["path"] = "nest/through/outside"
            document["release_digest"] = release_digest(document)
            (prepared.out / RELEASE_NAME).write_bytes(json.dumps(document).encode())
            with self.assertRaises(PathError) as caught:
                verify_release(prepared.out)
            self.assertIn("symlink", str(caught.exception))

    def test_the_same_fixture_reached_without_a_symlink_verifies(self):
        """Without this the test above would pass for a fixture that simply is
        not there, rather than for one reached the wrong way."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            nest = prepared.out / "nest"
            nest.mkdir()
            shutil.move(
                str(prepared.out / FIXTURE_DIRECTORY), str(nest / "carried")
            )
            document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
            document["fixture"]["path"] = "nest/carried"
            document["release_digest"] = release_digest(document)
            (prepared.out / RELEASE_NAME).write_bytes(json.dumps(document).encode())
            self.assertEqual(verify_release(prepared.out)["checks"], list(CHECKS))

    def test_a_release_that_is_not_there_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PathError):
                verify_release(Path(directory) / "no-release")

    def test_a_document_that_is_not_json_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            (prepared.out / RELEASE_NAME).write_bytes(b"{not json")
            with self.assertRaises(LazarusError):
                verify_release(prepared.out)

    def test_a_document_the_schema_refuses_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            (prepared.out / RELEASE_NAME).write_bytes(b'{"schema_version": 1}')
            with self.assertRaises(FormatError):
                verify_release(prepared.out)

    def test_a_moved_release_still_verifies(self):
        """Every path a release names is relative to itself."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            first = verify_release(prepared.out)
            moved = prepared.root / "carried-elsewhere"
            shutil.move(str(prepared.out), str(moved))
            self.assertEqual(verify_release(moved), first)

    def test_verifying_twice_reports_the_same_thing(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)
            self.assertEqual(verify_release(prepared.out), verify_release(prepared.out))

    def test_verifying_changes_nothing_in_the_release(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = self.released(directory)

            def snapshot():
                return {
                    path.relative_to(prepared.out).as_posix(): (
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                        path.stat().st_mode,
                    )
                    for path in sorted(prepared.out.rglob("*"))
                    if path.is_file()
                }

            before = snapshot()
            verify_release(prepared.out)
            self.assertEqual(snapshot(), before)


class WriteAndReadAgreeTests(unittest.TestCase):
    """Two functions, one release. They have to say the same thing about it."""

    def test_every_claim_the_write_recorded_the_read_confirms(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            written = prepared.release()
            read = verify_release(prepared.out)
            self.assertEqual(written["release_digest"], read["release_digest"])
            self.assertEqual(
                written["fixture"]["fixture_digest"], read["fixture_digest"]
            )
            self.assertEqual(written["statement"]["sha256"], read["statement_sha256"])
            self.assertEqual(
                written["statement"]["predicate_type"], read["predicate_type"]
            )
            self.assertEqual(written["verified"]["block_hash"], read["block_hash"])
            self.assertEqual(
                written["verified"]["evidence_counts"], read["evidence_counts"]
            )
            self.assertEqual(written["binding"]["checks"], read["checks"])


class OtherLayoutTests(unittest.TestCase):
    """The reader honours the paths the document names.

    Nothing requires a release to use the names the writer chose. A reader that
    looked for `fixture` and `statement.json` regardless would be reading a
    layout rather than a document, and the two path fields would be decoration.
    """

    def laid_out(self, prepared, target, fixture_path, statement_path):
        target.mkdir(parents=True)
        shutil.copytree(prepared.out / FIXTURE_DIRECTORY, target / fixture_path)
        (target / statement_path).write_bytes(
            (prepared.out / STATEMENT_NAME).read_bytes()
        )
        document = json.loads((prepared.out / RELEASE_NAME).read_bytes())
        document["fixture"]["path"] = fixture_path
        document["statement"]["path"] = statement_path
        document["release_digest"] = release_digest(document)
        (target / RELEASE_NAME).write_bytes(json.dumps(document).encode())
        return target

    def test_a_release_using_its_own_names_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            hand = self.laid_out(
                prepared, prepared.root / "by-hand", "state", "attestation.json"
            )
            self.assertEqual(verify_release(hand)["checks"], list(CHECKS))

    def test_a_fixture_a_level_down_verifies(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            nested = self.laid_out(
                prepared, prepared.root / "nested", "inner/state", "note.json"
            )
            self.assertEqual(verify_release(nested)["checks"], list(CHECKS))

    def test_the_unlisted_rule_follows_the_document_rather_than_the_names(self):
        """With the fixture at `inner/state`, `inner` is the entry the document
        accounts for. A rule keyed on the word `fixture` would refuse it."""
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            nested = self.laid_out(
                prepared, prepared.root / "nested", "inner/state", "note.json"
            )
            (nested / "unaccounted.txt").write_bytes(b"nobody said")
            with self.assertRaises(IntegrityError) as caught:
                verify_release(nested)
            self.assertIn("unaccounted.txt", str(caught.exception))

    def test_a_file_beside_a_nested_v2_fixture_is_unaccounted(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = PreparedV2(directory)
            prepared.release()
            nested = self.laid_out(
                prepared, prepared.root / "nested-v2", "inner/state", "note.json"
            )
            stowaway = nested / "inner" / "unaccounted.txt"
            stowaway.write_bytes(b"neither the release nor the fixture lists this")
            with self.assertRaises(IntegrityError) as caught:
                verify_release(nested)
            self.assertIn("inner/unaccounted.txt", str(caught.exception))


class TwoReleasesTests(unittest.TestCase):
    """Neither release will accept the other's parts."""

    def pair(self, directory):
        root = Path(directory)
        first = Prepared(directory)
        first.release()
        other = root / "second"
        other.mkdir()
        write_fixture(other, hash_source="a second synthetic offline test vector")
        statement = root / "second-statement.json"
        statement.write_bytes(json.dumps(statement_for(other), indent=2).encode())
        second = root / "second-release"
        write_release(other, statement, second)
        return first, second

    def test_another_releases_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = self.pair(directory)
            shutil.rmtree(first.out / FIXTURE_DIRECTORY)
            shutil.copytree(second / FIXTURE_DIRECTORY, first.out / FIXTURE_DIRECTORY)
            with self.assertRaises(IntegrityError) as caught:
                verify_release(first.out)
            self.assertIn("the fixture verifies to", str(caught.exception))

    def test_another_releases_statement_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = self.pair(directory)
            (first.out / STATEMENT_NAME).write_bytes(
                (second / STATEMENT_NAME).read_bytes()
            )
            with self.assertRaises(IntegrityError) as caught:
                verify_release(first.out)
            self.assertIn("the statement digests to", str(caught.exception))

    def test_another_releases_document_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            first, second = self.pair(directory)
            (first.out / RELEASE_NAME).write_bytes(
                (second / RELEASE_NAME).read_bytes()
            )
            with self.assertRaises(IntegrityError):
                verify_release(first.out)

    def test_each_release_verifies_on_its_own(self):
        """Without this the tests above would pass for a pair that never
        verified in the first place."""
        with tempfile.TemporaryDirectory() as directory:
            first, second = self.pair(directory)
            self.assertEqual(verify_release(first.out)["checks"], list(CHECKS))
            self.assertEqual(verify_release(second)["checks"], list(CHECKS))


class VerifyCommandTests(unittest.TestCase):
    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(CLI), "verify-release", *[str(a) for a in arguments]],
            capture_output=True,
            text=True,
        )

    def test_the_command_prints_the_counts_and_the_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            result = self.run_cli(prepared.out)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("proof-backed: 3", result.stdout)
            self.assertIn("header-bound: 1", result.stdout)
            self.assertIn("recorded-rpc: 1", result.stdout)
            for check in CHECKS:
                self.assertIn(check, result.stdout)

    def test_the_command_exits_one_and_names_the_disagreement(self):
        with tempfile.TemporaryDirectory() as directory:
            prepared = Prepared(directory)
            prepared.release()
            component = prepared.out / FIXTURE_DIRECTORY / "header.json"
            component.write_bytes(component.read_bytes().replace(b"0x", b"0X", 1))
            result = self.run_cli(prepared.out)
            self.assertEqual(result.returncode, 1)
            self.assertIn("header.json", result.stderr)
            self.assertEqual(result.stdout, "")
