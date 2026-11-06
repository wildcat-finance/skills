"""A leftover part-set temporary directory beside a `--parts` target.

A killed `--parts` run leaves its hidden sibling `.<name>.tmp-<16 hex>`
behind. The next run into that parent names every such directory and refuses
before it creates anything, and it removes none, whatever made it.

These cases live in their own module because the issue 1892 design record's
conformance harness loads `StatementPartsCommandTests` by name, and its
runbook says that class carries exactly six cases. The module imports
`test_statement_parts` as a module rather than its classes, so discovery does
not load `PartsCase` or the command tests a second time.
"""

from contextlib import ExitStack
import errno
import json
import os
from pathlib import Path
import re
import unittest
from unittest import mock

from tests import test_statement_parts as parts_tests


statement_module = parts_tests.statement_module
emit_statement_parts = parts_tests.emit_statement_parts
AlexandriaError = parts_tests.AlexandriaError
listing = parts_tests.listing
run_command = parts_tests.run_command
written_set = parts_tests.written_set
expected_set = parts_tests.expected_set
verified_manifest = parts_tests.verified_manifest

ONE = "statement parts output has a leftover temporary directory beside it: "
SEVERAL = "statement parts output has leftover temporary directories beside it: "
PLATFORM = "^this platform cannot perform a confined statement parts write$"


class LeftoverPartsDirectoryTests(parts_tests.PartsCase):
    """The writer names and refuses a leftover, and never removes one."""

    def leftover(self, name: str) -> Path:
        """One directory the writer did not make, with a file and a `part/` file."""
        directory = self.outputs / name
        directory.mkdir()
        (directory / "index.json").write_bytes(b"theirs\n")
        (directory / "part").mkdir()
        (directory / "part" / "part-1.json").write_bytes(b"theirs too\n")
        return directory

    def assert_written(self, release: Path, target: Path) -> None:
        _, manifest = verified_manifest(release)
        self.assertEqual(
            written_set(target), expected_set(statement_module.project_statement(manifest))
        )

    def test_a_leftover_directory_the_writer_did_not_make_is_named_and_left_alone(self):
        release, _ = self.band_release()
        target = self.outputs / "set"
        leftover = self.leftover(".set.tmp-0123456789abcdef")
        before = listing(self.outputs)
        with self.subTest(run="command"):
            result = run_command("statement", release, "--parts", target)
            self.assert_refused(result, re.escape(f"alexandria: {ONE}{leftover}"))
            self.assertFalse(os.path.lexists(target))
            self.assertEqual(listing(self.outputs), before)
        with self.subTest(run="library"):
            with self.assertRaisesRegex(
                AlexandriaError, f"^{re.escape(ONE)}{re.escape(str(leftover))}$"
            ):
                emit_statement_parts(release, target)
            self.assertFalse(os.path.lexists(target))
            self.assertEqual(listing(self.outputs), before)

    def test_every_leftover_directory_is_named_in_name_order(self):
        release, _ = self.band_release()
        target = self.outputs / "set"
        last = self.leftover(".set.tmp-" + "f" * 16)
        first = self.leftover(".set.tmp-" + "0" * 16)
        before = listing(self.outputs)
        result = run_command("statement", release, "--parts", target)
        self.assert_refused(result, re.escape(f"alexandria: {SEVERAL}{first}, {last}"))
        self.assertFalse(os.path.lexists(target))
        self.assertEqual(listing(self.outputs), before)

    def test_an_entry_that_only_resembles_the_temporary_name_is_ignored(self):
        release, release_id = self.band_release()
        target = self.outputs / "set"
        token = "a" * 16
        for name in (
            ".set.tmp-" + "a" * 15,
            ".set.tmp-" + "a" * 17,
            ".set.tmp-" + "A" * 16,
            ".set.tmp-" + "a" * 15 + "g",
            ".other.tmp-" + token,
            ".se.tmp-" + token,
            "set.tmp-" + token,
            ".set.tmp" + token,
        ):
            self.leftover(name)
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (elsewhere / "index.json").write_bytes(b"elsewhere\n")
        (self.outputs / (".set.tmp-" + "1" * 16)).write_bytes(b"a file\n")
        (self.outputs / (".set.tmp-" + "2" * 16)).symlink_to(elsewhere, target_is_directory=True)
        (self.outputs / (".set.tmp-" + "3" * 16)).symlink_to(self.root / "missing")
        before = listing(self.outputs)
        result = run_command("statement", release, "--parts", target)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["release_id"], release_id)
        self.assert_written(release, target)
        after = {
            name: body for name, body in listing(self.outputs).items()
            if name != "set" and not name.startswith("set/")
        }
        self.assertEqual(after, before)
        self.assertEqual(listing(elsewhere), {"index.json": b"elsewhere\n"})

    def test_an_existing_output_is_refused_before_a_leftover_is_looked_for(self):
        release, _ = self.band_release()
        target = self.outputs / "set"
        target.mkdir()
        (target / "index.json").write_bytes(b"keep\n")
        self.leftover(".set.tmp-" + "0" * 16)
        before = listing(self.outputs)
        looked = mock.Mock(side_effect=AssertionError("looked for a leftover"))
        with mock.patch.object(statement_module, "_is_temporary_parts_name", looked), \
                self.assertRaisesRegex(
                    AlexandriaError,
                    f"^statement parts output already exists: {re.escape(str(target))}$",
                ):
            emit_statement_parts(release, target)
        self.assertEqual(looked.call_count, 0)
        self.assertEqual(listing(self.outputs), before)

    def test_a_leftover_refuses_before_the_temporary_directory_is_allocated(self):
        release, _ = self.band_release()
        target = self.outputs / "set"
        leftover = self.leftover(".set.tmp-" + "0" * 16)
        before = listing(self.outputs)
        allocated = mock.Mock(side_effect=AssertionError("allocated a temporary directory"))
        with mock.patch.object(statement_module, "_temporary_parts_directory", allocated), \
                self.assertRaisesRegex(
                    AlexandriaError, f"^{re.escape(ONE)}{re.escape(str(leftover))}$"
                ):
            emit_statement_parts(release, target)
        self.assertEqual(allocated.call_count, 0)
        self.assertFalse(os.path.lexists(target))
        self.assertEqual(listing(self.outputs), before)

    def test_a_leftover_that_cannot_be_inspected_refuses_and_one_that_vanished_is_ignored(self):
        release, _ = self.band_release()
        target = self.outputs / "set"
        leftover = self.leftover(".set.tmp-" + "0" * 16)
        contents = listing(leftover)
        before = listing(self.outputs)
        real = os.stat

        def failing(error):
            def inspecting(path, *args, **kwargs):
                if path == leftover.name and kwargs.get("dir_fd") is not None:
                    raise error
                return real(path, *args, **kwargs)

            return inspecting

        def patched(inspecting):
            # The writer checks that its platform inspects under a directory
            # descriptor without following links, so the patch claims both.
            stack = ExitStack()
            stack.enter_context(mock.patch.object(statement_module.os, "stat", inspecting))
            stack.enter_context(mock.patch.object(
                statement_module.os, "supports_dir_fd", os.supports_dir_fd | {inspecting}
            ))
            stack.enter_context(mock.patch.object(
                statement_module.os, "supports_follow_symlinks",
                os.supports_follow_symlinks | {inspecting},
            ))
            return stack

        with self.subTest(inspection="refused"):
            denied = PermissionError(errno.EACCES, os.strerror(errno.EACCES))
            with patched(failing(denied)), self.assertRaisesRegex(
                AlexandriaError,
                r"^cannot inspect statement parts output parent: \[Errno 13\] ",
            ):
                emit_statement_parts(release, target)
            self.assertEqual(listing(self.outputs), before)
        with self.subTest(inspection="vanished"):
            gone = FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT))
            with patched(failing(gone)):
                emit_statement_parts(release, target)
            self.assert_written(release, target)
            self.assertEqual(listing(leftover), contents)

    def test_the_writers_own_name_pattern_is_the_one_looked_for(self):
        token = "0123456789abcdef"
        for output_name, name, expected in (
            ("set", ".set.tmp-" + token, True),
            ("set", ".set.tmp-" + "f" * 16, True),
            ("set", ".set.tmp-" + token[:15], False),
            ("set", ".set.tmp-" + token + "0", False),
            ("set", ".set.tmp-" + token.upper(), False),
            ("set", ".set.tmp-" + token[:15] + "g", False),
            ("set", ".set.tmp-" + token[:15] + " ", False),
            ("set", ".sets.tmp-" + token, False),
            ("set", ".se.tmp-" + token, False),
            ("set", "set.tmp-" + token, False),
            ("set", ".set.tmp" + token, False),
            ("set", ".set.tmp-", False),
            ("release.v1", ".release.v1.tmp-" + token, True),
            ("release.v1", ".release.tmp-" + token, False),
            ("release.v1", ".releasexv1.tmp-" + token, False),
            ("a+b (1)", ".a+b (1).tmp-" + token, True),
            ("a+b (1)", ".aab (1).tmp-" + token, False),
        ):
            with self.subTest(output=output_name, name=name):
                self.assertIs(
                    statement_module._is_temporary_parts_name(name, output_name), expected
                )
        with self.subTest(name="the allocator's own"):
            parent_fd = os.open(self.outputs, os.O_RDONLY | os.O_DIRECTORY)
            try:
                name, descriptor = statement_module._temporary_parts_directory(
                    parent_fd, "set", []
                )
                os.close(descriptor)
            finally:
                os.close(parent_fd)
            self.assertTrue(statement_module._is_temporary_parts_name(name, "set"), name)

    def test_a_platform_that_cannot_list_a_directory_descriptor_refuses_by_name(self):
        release, _ = self.band_release()
        self.leftover(".set.tmp-" + "0" * 16)
        before = listing(self.outputs)
        unlisted = os.supports_fd - {os.listdir}
        with mock.patch.object(statement_module.os, "supports_fd", unlisted), \
                self.assertRaisesRegex(AlexandriaError, PLATFORM):
            emit_statement_parts(release, self.outputs / "set")
        self.assertEqual(listing(self.outputs), before)


if __name__ == "__main__":
    unittest.main()
