"""Executable custody survives unrelated directory changes."""

import os
from pathlib import Path
import tempfile
import unittest

from test_elenchus_checker import elenchus


class ExecutableDirectoryStabilityTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="elenchus-directory-binding-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.ancestor = self.root / "bin"
        self.ancestor.mkdir(mode=0o755)
        self.runner = self.ancestor / "runner"
        self.runner.write_bytes(b"#!/bin/sh\nexit 0\n")
        self.runner.chmod(0o755)
        self.binding = elenchus._trusted_executable(str(self.runner))
        self.addCleanup(self.binding.close)

    def test_unrelated_sibling_creation_does_not_invalidate_the_executable(self):
        original = os.fstat(self.binding.descriptor)
        (self.ancestor / "unrelated").mkdir()
        self.assertEqual(elenchus._file_identity(original),
                         elenchus._file_identity(os.fstat(self.binding.descriptor)))
        self.assertTrue(self.binding.stable())

    def test_restored_ancestor_is_valid_but_its_replacement_is_not(self):
        held = self.root / "held"
        self.ancestor.rename(held)
        self.ancestor.mkdir()
        try:
            self.assertFalse(self.binding.stable())
        finally:
            self.ancestor.rmdir()
            held.rename(self.ancestor)
        self.assertTrue(self.binding.stable())

    def test_ancestor_permission_changes_are_refused(self):
        self.ancestor.chmod(0o700)
        self.assertFalse(self.binding.stable())

    def test_replaced_executable_is_refused_even_with_matching_bytes_and_mtime(self):
        original = self.runner.stat()
        replacement = self.ancestor / "replacement"
        replacement.write_bytes(self.runner.read_bytes())
        replacement.chmod(original.st_mode)
        os.utime(replacement, ns=(original.st_atime_ns, original.st_mtime_ns))
        replacement.replace(self.runner)
        self.assertFalse(self.binding.stable())
