"""Digest sets, and the ways a loose one lets a subject match the wrong bytes."""

import hashlib
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

from ariadne_lib import digests  # noqa: E402

SHA256_OF_EMPTY = hashlib.sha256(b"").hexdigest()


class CheckTests(unittest.TestCase):
    def test_a_well_formed_set_passes_through_unchanged(self):
        found = {"sha256": SHA256_OF_EMPTY}
        self.assertIs(digests.check(found), found)

    def test_empty_set_is_refused(self):
        with self.assertRaises(digests.DigestError) as caught:
            digests.check({})
        self.assertIn("empty", str(caught.exception))

    def test_uppercase_hex_is_refused(self):
        with self.assertRaises(digests.DigestError) as caught:
            digests.check({"sha256": SHA256_OF_EMPTY.upper()})
        self.assertIn("lowercase", str(caught.exception))

    def test_short_value_is_refused(self):
        with self.assertRaises(digests.DigestError) as caught:
            digests.check({"sha256": SHA256_OF_EMPTY[:32]})
        self.assertIn("expected 64", str(caught.exception))

    def test_non_hex_value_is_refused(self):
        with self.assertRaises(digests.DigestError) as caught:
            digests.check({"sha256": "z" * 64})
        self.assertIn("not hex", str(caught.exception))

    def test_a_set_of_only_unsupported_algorithms_is_refused(self):
        with self.assertRaises(digests.DigestError) as caught:
            digests.check({"sha1": "a" * 40})
        self.assertIn("no supported algorithm", str(caught.exception))

    def test_sha1_alongside_sha256_is_carried_but_does_not_stand_alone(self):
        found = {"sha1": "a" * 40, "sha256": SHA256_OF_EMPTY}
        self.assertIs(digests.check(found), found)

    def test_a_non_object_is_refused(self):
        with self.assertRaises(digests.DigestError):
            digests.check([SHA256_OF_EMPTY])


class AgreementTests(unittest.TestCase):
    def test_sets_sharing_an_algorithm_and_value_agree(self):
        self.assertTrue(
            digests.agree(
                {"sha256": SHA256_OF_EMPTY},
                {"sha256": SHA256_OF_EMPTY, "sha512": "b" * 128},
            )
        )

    def test_sets_sharing_nothing_do_not_agree(self):
        self.assertFalse(
            digests.agree({"sha256": SHA256_OF_EMPTY}, {"sha512": "b" * 128})
        )

    def test_agreement_on_an_unsupported_algorithm_alone_is_not_agreement(self):
        """A match resting on sha1 alone is a match anyone can manufacture."""
        left = {"sha1": "a" * 40, "sha256": SHA256_OF_EMPTY}
        right = {"sha1": "a" * 40, "sha512": "b" * 128}
        self.assertFalse(digests.agree(left, right))

    def test_disagreement_anywhere_beats_agreement_elsewhere(self):
        left = {"sha256": SHA256_OF_EMPTY, "sha512": "b" * 128}
        right = {"sha256": SHA256_OF_EMPTY, "sha512": "c" * 128}
        self.assertFalse(digests.agree(left, right))

    def test_agreement_does_not_rescan_the_wider_digest_set(self):
        """One wide claim compared with many subjects stays linear in its input."""

        class RefuseIteration(dict):
            def __iter__(self):
                raise AssertionError("the wider digest set was iterated")

        wide = RefuseIteration(
            {"sha256": SHA256_OF_EMPTY, **{"unknown-%d" % i: "a" for i in range(32)}}
        )
        narrow = {"sha256": SHA256_OF_EMPTY}
        self.assertTrue(digests.agree(wide, narrow))
        self.assertTrue(digests.agree(narrow, wide))


class FileAndTreeTests(unittest.TestCase):
    def test_a_fifo_is_refused_rather_than_read(self):
        """`open` on a fifo blocks until something writes to it. `tree_listing`
        has refused this since the first build; `of_file` did not, and both
        capture paths call it directly."""
        directory = tempfile.mkdtemp(prefix="ariadne-fifo-")
        self.addCleanup(shutil.rmtree, directory, True)
        path = os.path.join(directory, "pipe")
        os.mkfifo(path)
        with self.assertRaises(digests.DigestError) as caught:
            digests.of_file(path)
        self.assertIn("not a regular file", str(caught.exception))

    def test_a_directory_is_refused_rather_than_read(self):
        directory = tempfile.mkdtemp(prefix="ariadne-fifo-")
        self.addCleanup(shutil.rmtree, directory, True)
        with self.assertRaises(digests.DigestError):
            digests.of_file(directory)

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, relative, content):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as handle:
            handle.write(content)
        return path

    def test_file_digest_matches_hashlib(self):
        path = self.write("a.txt", b"hello")
        self.assertEqual(
            digests.of_file(path),
            {"sha256": hashlib.sha256(b"hello").hexdigest()},
        )

    def test_bytes_digest_rejects_an_unsupported_algorithm(self):
        with self.assertRaises(digests.DigestError):
            digests.of_bytes(b"hello", "md5")

    def test_tree_digest_is_stable_and_notices_a_rename(self):
        self.write("src/a.sol", b"contract A {}")
        first = digests.of_tree(self.root)
        self.assertEqual(first, digests.of_tree(self.root))

        os.rename(
            os.path.join(self.root, "src", "a.sol"),
            os.path.join(self.root, "src", "b.sol"),
        )
        self.assertNotEqual(first, digests.of_tree(self.root))

    def test_tree_digest_notices_swapped_contents(self):
        self.write("a.txt", b"one")
        self.write("b.txt", b"two")
        first = digests.of_tree(self.root)
        self.write("a.txt", b"two")
        self.write("b.txt", b"one")
        self.assertNotEqual(first, digests.of_tree(self.root))

    def test_tree_digest_skips_the_git_directory(self):
        self.write("a.txt", b"one")
        first = digests.of_tree(self.root)
        self.write(".git/objects/deadbeef", b"whatever")
        self.assertEqual(first, digests.of_tree(self.root))

    def test_a_symlinked_file_is_refused_rather_than_followed(self):
        self.write("real.txt", b"one")
        os.symlink(
            os.path.join(self.root, "real.txt"), os.path.join(self.root, "link.txt")
        )
        with self.assertRaises(digests.DigestError) as caught:
            digests.of_tree(self.root)
        self.assertIn("symlink", str(caught.exception))

    def test_a_symlinked_directory_is_refused(self):
        self.write("sub/real.txt", b"one")
        os.symlink(os.path.join(self.root, "sub"), os.path.join(self.root, "linked"))
        with self.assertRaises(digests.DigestError) as caught:
            digests.of_tree(self.root)
        self.assertIn("symlink", str(caught.exception))

    def test_of_file_refuses_a_symlink(self):
        path = self.write("real.txt", b"one")
        link = os.path.join(self.root, "link.txt")
        os.symlink(path, link)
        with self.assertRaises(digests.DigestError):
            digests.of_file(link)

    def test_a_fifo_is_refused_rather_than_opened(self):
        """Opening a fifo for reading blocks until somebody writes to it."""
        self.write("a.txt", b"one")
        os.mkfifo(os.path.join(self.root, "pipe"))
        with self.assertRaises(digests.DigestError) as caught:
            digests.of_tree(self.root)
        self.assertIn("not a regular file", str(caught.exception))

    def test_an_unreadable_directory_is_refused_rather_than_skipped(self):
        """os.walk drops what it cannot read, which would make a tree digest
        cover less than the caller believes without saying so."""
        self.write("sub/a.txt", b"one")
        closed = os.path.join(self.root, "sub")
        os.chmod(closed, 0o000)
        self.addCleanup(os.chmod, closed, 0o700)
        if os.access(closed, os.R_OK):
            self.skipTest("running with rights that ignore directory modes")
        with self.assertRaises(digests.DigestError) as caught:
            digests.of_tree(self.root)
        self.assertIn("cannot read", str(caught.exception))

    def test_an_unreadable_file_is_a_digest_error_not_an_os_error(self):
        path = self.write("a.txt", b"one")
        os.chmod(path, 0o000)
        self.addCleanup(os.chmod, path, 0o600)
        if os.access(path, os.R_OK):
            self.skipTest("running with rights that ignore file modes")
        with self.assertRaises(digests.DigestError):
            digests.of_file(path)

    def test_tree_digest_refuses_a_path_that_is_not_a_directory(self):
        path = self.write("a.txt", b"one")
        with self.assertRaises(digests.DigestError):
            digests.of_tree(path)


class RenderingTests(unittest.TestCase):
    def test_short_prefers_the_strongest_algorithm_present(self):
        found = digests.short({"sha256": SHA256_OF_EMPTY, "sha512": "b" * 128})
        self.assertTrue(found.startswith("sha512:"))


if __name__ == "__main__":
    unittest.main()
