"""Fixture paths remain inside their root and never cross symlinks."""

from pathlib import Path
import os
import stat
import tempfile
import unittest
from unittest import mock

import lazarus_lib.paths as paths_module
from lazarus_lib.errors import PathError, ResourceLimitError
from lazarus_lib.paths import (
    atomic_write_confined,
    list_fixture_files,
    read_confined_bytes,
    validate_relative_path,
)


class PathTests(unittest.TestCase):
    def test_a_segment_that_is_entirely_whitespace_is_refused(self):
        """A legal POSIX filename that renders as nothing. A component listed
        under it reads as an entry nobody can identify."""
        for value in ("   ", " ", "\t", "a/ /b", " /a", "a/  "):
            with self.subTest(path=value), self.assertRaises(PathError):
                validate_relative_path(value)

    def test_a_space_inside_a_segment_is_kept(self):
        self.assertEqual(validate_relative_path("a b"), "a b")
        self.assertEqual(validate_relative_path("dir one/file two.json"),
                         "dir one/file two.json")

    def test_normal_relative_path_resolves(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            target = root / "data" / "record.json"
            target.write_text("{}\n")
            self.assertEqual(
                read_confined_bytes(root, "data/record.json", max_bytes=100), b"{}\n"
            )
            self.assertEqual(list_fixture_files(root), {"data/record.json"})

    def test_absolute_traversal_backslash_and_non_normal_paths_fail(self):
        bad = ("/tmp/x", "../x", "a/../x", "a\\x", "./x", "x\x00y", "")
        for value in bad:
            with self.subTest(value=value), self.assertRaises(PathError):
                validate_relative_path(value)

    def test_a_path_that_names_the_directory_itself_is_refused(self):
        """`PurePosixPath(".")` has no parts, so every part-based check above
        passes over nothing and it came back unchanged as though it named a
        file."""
        for value in (".", "./", "a/..", "./."):
            with self.subTest(value=value), self.assertRaises(PathError):
                validate_relative_path(value)

    def test_file_and_directory_symlinks_fail(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            external = Path(outside) / "secret"
            external.write_text("secret")
            os.symlink(external, root / "linked-file")
            with self.assertRaisesRegex(PathError, "symlink"):
                read_confined_bytes(root, "linked-file", max_bytes=100)
            os.symlink(Path(outside), root / "linked-dir")
            with self.assertRaises(PathError):
                read_confined_bytes(root, "linked-dir/secret", max_bytes=100)
            with self.assertRaisesRegex(PathError, "symlink"):
                list_fixture_files(root)

    def test_missing_non_file_and_oversized_components_fail(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "folder").mkdir()
            with self.assertRaises(PathError):
                read_confined_bytes(root, "missing", max_bytes=100)
            with self.assertRaisesRegex(PathError, "regular file"):
                read_confined_bytes(root, "folder", max_bytes=100)
            target = root / "large"
            target.write_bytes(b"12345")
            with self.assertRaises(ResourceLimitError):
                read_confined_bytes(root, "large", max_bytes=4)

    def test_fixture_entry_count_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").mkdir()
            (root / "two").mkdir()
            (root / "three").mkdir()
            with self.assertRaises(ResourceLimitError):
                list_fixture_files(root, max_entries=2)

    def test_missing_descriptor_inventory_capability_is_a_bounded_refusal(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(
            paths_module.os,
            "scandir",
            side_effect=NotImplementedError("host detail"),
        ):
            try:
                list_fixture_files(Path(directory))
            except PathError as exception:
                self.assertEqual(
                    str(exception),
                    "platform lacks secure fixture directory operations",
                )
            except NotImplementedError as exception:
                self.fail(
                    "fixture inventory leaked an unsupported operation: "
                    f"{exception}"
                )
            else:
                self.fail("fixture inventory accepted an unsupported operation")

    def test_a_descriptor_root_remains_owned_and_usable_by_its_caller(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            nested = root / "nested"
            nested.mkdir()
            target = nested / "record.json"
            target.write_bytes(b"old\n")
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            root_fd = os.open(root, flags)
            identity = os.fstat(root_fd)
            try:
                self.assertEqual(list_fixture_files(root_fd), {"nested/record.json"})
                self.assertEqual(
                    read_confined_bytes(
                        root_fd,
                        "nested/record.json",
                        max_bytes=100,
                    ),
                    b"old\n",
                )
                atomic_write_confined(
                    root_fd,
                    "nested/record.json",
                    b"new\n",
                )
                after = os.fstat(root_fd)
                self.assertEqual(
                    (after.st_dev, after.st_ino),
                    (identity.st_dev, identity.st_ino),
                )
                component = os.open(
                    "nested/record.json",
                    os.O_RDONLY | os.O_NOFOLLOW,
                    dir_fd=root_fd,
                )
                try:
                    self.assertEqual(os.read(component, 100), b"new\n")
                finally:
                    os.close(component)
            finally:
                os.close(root_fd)

    def test_descriptor_inventory_does_not_share_an_active_caller_scan(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected = {"one.json", "two.json", "three.json"}
            for name in expected:
                (root / name).write_bytes(name.encode("utf-8"))
            root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                with os.scandir(root_fd) as caller_scan:
                    first = next(caller_scan).name
                    self.assertEqual(list_fixture_files(root_fd), expected)
                    caller_inventory = {first, *(entry.name for entry in caller_scan)}
                self.assertEqual(caller_inventory, expected)
            finally:
                os.close(root_fd)

    def test_descriptor_root_refuses_a_file_without_closing_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "record.json"
            target.write_bytes(b"record\n")
            descriptor = os.open(target, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                with self.assertRaisesRegex(PathError, "not a directory"):
                    list_fixture_files(descriptor)
                os.lseek(descriptor, 0, os.SEEK_SET)
                self.assertEqual(os.read(descriptor, 100), b"record\n")
            finally:
                os.close(descriptor)

    def test_descriptor_root_survives_rename_and_path_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory)
            root = parent / "fixture"
            root.mkdir()
            (root / "record.json").write_bytes(b"owned\n")
            descriptor = os.open(
                root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
            try:
                root.rename(parent / "moved-fixture")
                root.mkdir()
                (root / "record.json").write_bytes(b"replacement\n")
                self.assertEqual(list_fixture_files(descriptor), {"record.json"})
                self.assertEqual(
                    read_confined_bytes(
                        descriptor,
                        "record.json",
                        max_bytes=100,
                    ),
                    b"owned\n",
                )
            finally:
                os.close(descriptor)

    def test_descriptor_read_refuses_bytes_changed_after_the_first_stat(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "record.json"
            target.write_bytes(b"before\n")
            descriptor = os.open(
                root,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
            )
            real_fstat = paths_module.os.fstat
            changed = False

            def change_after_first_file_stat(fd):
                nonlocal changed
                details = real_fstat(fd)
                if stat.S_ISREG(details.st_mode) and not changed:
                    changed = True
                    target.write_bytes(b"after-change\n")
                return details

            try:
                with mock.patch.object(
                    paths_module.os,
                    "fstat",
                    side_effect=change_after_first_file_stat,
                ):
                    with self.assertRaisesRegex(PathError, "changed while it was read"):
                        read_confined_bytes(
                            descriptor,
                            "record.json",
                            max_bytes=100,
                        )
                self.assertTrue(changed)
                os.fstat(descriptor)
            finally:
                os.close(descriptor)

    def test_descriptor_inventory_keeps_entry_bounds_and_refuses_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "one").mkdir()
            (root / "two").mkdir()
            (root / "three").mkdir()
            root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                with self.assertRaises(ResourceLimitError):
                    list_fixture_files(root_fd, max_entries=2)
            finally:
                os.close(root_fd)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "target"
            target.write_bytes(b"target\n")
            (root / "link").symlink_to(target)
            root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                with self.assertRaisesRegex(PathError, "symlink"):
                    list_fixture_files(root_fd)
            finally:
                os.close(root_fd)

    def test_descriptor_inventory_refuses_a_non_regular_entry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            os.mkfifo(root / "pipe")
            root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                with self.assertRaisesRegex(PathError, "non-regular"):
                    list_fixture_files(root_fd)
            finally:
                os.close(root_fd)


if __name__ == "__main__":
    unittest.main()
