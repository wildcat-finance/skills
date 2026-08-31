"""Corpus build and verify, and every refusal class the pin rests on."""

import json
import os
import tempfile
import unittest

from tests.support import SCRIPTS  # noqa: F401

from berean_lib import BereanError, corpus


def make_tree(root, files):
    for relative, data in files.items():
        full = os.path.join(root, *relative.split("/"))
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "wb") as handle:
            handle.write(data)


def failures(checks):
    return [check.name for check in checks if not check.passed]


TREE = {"guide/a.md": "alpha café\n".encode("utf-8"), "b.md": b"bravo\n"}


class BuildTests(unittest.TestCase):
    def test_build_then_verify_is_clean(self):
        with tempfile.TemporaryDirectory() as root:
            make_tree(root, TREE)
            document = corpus.build(root, "v1")
            self.assertEqual(failures(corpus.verify(document, root)), [])

    def test_two_builds_are_byte_identical(self):
        from berean_lib import canonical

        with tempfile.TemporaryDirectory() as root:
            make_tree(root, TREE)
            one = canonical.dumps(corpus.build(root, "v1"))
            two = canonical.dumps(corpus.build(root, "v1"))
            self.assertEqual(one, two)

    def test_an_empty_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(BereanError):
                corpus.build(root, "v1")

    def test_a_symlink_in_the_tree_is_refused(self):
        with tempfile.TemporaryDirectory() as root:
            make_tree(root, TREE)
            os.symlink(os.path.join(root, "b.md"), os.path.join(root, "c.md"))
            with self.assertRaises(BereanError):
                corpus.build(root, "v1")

    def test_write_stages_and_lands_whole(self):
        with tempfile.TemporaryDirectory() as root:
            make_tree(root, TREE)
            out = os.path.join(root, "..", "manifest.json")
            out = os.path.abspath(out)
            document = corpus.build(root, "v1")
            corpus.write(document, out)
            with open(out, "r", encoding="utf-8") as handle:
                self.assertEqual(json.loads(handle.read()), document)
            staging = [n for n in os.listdir(os.path.dirname(out)) if n.endswith(".staging")]
            self.assertEqual(staging, [])

    def test_write_refuses_an_invalid_document(self):
        with tempfile.TemporaryDirectory() as root:
            make_tree(root, TREE)
            document = corpus.build(root, "v1")
            document["corpus_digest"] = "0" * 64
            out = os.path.join(root, "manifest.json")
            with self.assertRaises(BereanError):
                corpus.write(document, out)
            self.assertFalse(os.path.exists(out))


class VerifyTests(unittest.TestCase):
    def build(self, root):
        make_tree(root, TREE)
        return corpus.build(root, "v1")

    def test_a_one_byte_edit_fails_corpus_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            with open(os.path.join(root, "b.md"), "wb") as handle:
                handle.write(b"Bravo\n")
            self.assertEqual(failures(corpus.verify(document, root)), ["corpus-bytes"])

    def test_a_missing_file_fails_corpus_complete(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            os.remove(os.path.join(root, "b.md"))
            self.assertIn("corpus-complete", failures(corpus.verify(document, root)))

    def test_an_unpinned_extra_file_fails_corpus_complete(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            make_tree(root, {"extra.md": b"stray\n"})
            self.assertEqual(failures(corpus.verify(document, root)), ["corpus-complete"])

    def test_a_pinned_path_swapped_for_a_symlink_fails_corpus_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            target = os.path.join(root, "b.md")
            os.remove(target)
            os.symlink(os.path.join(root, "guide", "a.md"), target)
            checks = corpus.verify(document, root)
            self.assertEqual(failures(checks), ["corpus-bytes"])
            detail = [c.detail for c in checks if c.name == "corpus-bytes"][0]
            self.assertIn("symlink", detail)

    def test_a_tampered_listing_digest_fails_the_shape(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            document["corpus_digest"] = "0" * 64
            self.assertEqual(failures(corpus.verify(document, root)), ["manifest-shape"])

    def test_an_undeclared_field_fails_the_shape(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            document["verdict"] = "fine"
            self.assertEqual(failures(corpus.verify(document, root)), ["manifest-shape"])

    def test_a_duplicate_pin_fails_the_shape(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            document["files"].append(dict(document["files"][0]))
            self.assertEqual(failures(corpus.verify(document, root)), ["manifest-shape"])

    def test_an_absolute_pinned_path_fails_the_shape(self):
        with tempfile.TemporaryDirectory() as root:
            document = self.build(root)
            document["files"][0]["path"] = "/etc/passwd"
            self.assertEqual(failures(corpus.verify(document, root)), ["manifest-shape"])


class SchemaAgreementTests(unittest.TestCase):
    def test_the_shipped_schema_names_the_format_and_closes_the_table(self):
        from tests.support import SCHEMAS

        with open(SCHEMAS / "corpus-manifest-v1.json", "r", encoding="utf-8") as handle:
            schema = json.load(handle)
        self.assertEqual(schema["properties"]["format"]["const"], corpus.FORMAT)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            tuple(schema["required"]), corpus.FIELDS
        )
        entry = schema["properties"]["files"]["items"]
        self.assertEqual(tuple(entry["required"]), corpus.FILE_FIELDS)
        from berean_lib import digests

        self.assertEqual(entry["properties"]["bytes"]["maximum"], digests.MAX_FILE_BYTES)
        self.assertEqual(schema["properties"]["files"]["maxItems"], digests.MAX_FILES)


if __name__ == "__main__":
    unittest.main()
