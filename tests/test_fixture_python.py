"""Nested commands keep the declared Python and release their fixture launcher."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock

from tests.fixture_python import pinned_python_path


class PinnedPythonFixtureTests(unittest.TestCase):
    def test_restricted_child_uses_the_declared_interpreter_and_controls(self):
        with mock.patch.dict(os.environ, {"PATH": os.defpath, "GIT_NO_REPLACE_OBJECTS": "1"}):
            before = dict(os.environ)
            with pinned_python_path() as directory:
                child = subprocess.run(
                    ["python3", "-c", "import json,os,sys; print(json.dumps([sys.executable,list(sys.version_info[:3]),os.environ['GIT_NO_REPLACE_OBJECTS']]))"],
                    check=True, capture_output=True, text=True, timeout=10,
                )
                executable, version, replacement_control = json.loads(child.stdout)
                self.assertTrue(Path(executable).samefile(sys.executable))
                self.assertEqual(version, list(sys.version_info[:3]))
                self.assertEqual(replacement_control, "1")
                self.assertTrue((directory / "python3").is_symlink())
            self.assertEqual(dict(os.environ), before)
            self.assertFalse(directory.exists())

    def test_exception_removes_launcher_and_restores_absent_path(self):
        with mock.patch.dict(os.environ):
            os.environ.pop("PATH", None)
            before = dict(os.environ)
            with self.assertRaisesRegex(RuntimeError, "fixture failed"):
                with pinned_python_path() as directory:
                    self.assertEqual(os.environ["PATH"], str(directory) + os.pathsep + os.defpath)
                    raise RuntimeError("fixture failed")
            self.assertEqual(dict(os.environ), before)
            self.assertFalse(directory.exists())

    def test_empty_path_exposes_only_the_fixture_launcher(self):
        with mock.patch.dict(os.environ, {"PATH": ""}):
            with pinned_python_path() as directory:
                self.assertEqual(os.environ["PATH"], str(directory))
                child = subprocess.run(["python3", "--version"], check=True,
                                       capture_output=True, text=True, timeout=10)
                self.assertEqual(child.stdout.strip(), "Python " + ".".join(map(str, sys.version_info[:3])))
            self.assertEqual(os.environ["PATH"], "")
            self.assertFalse(directory.exists())

    def test_nested_launcher_restores_its_enclosing_scope(self):
        before = dict(os.environ)
        with pinned_python_path() as outer:
            outer_path = os.environ["PATH"]
            with pinned_python_path() as inner:
                self.assertNotEqual(inner, outer)
                self.assertTrue((outer / "python3").exists())
            self.assertEqual(os.environ["PATH"], outer_path)
            self.assertFalse(inner.exists())
        self.assertEqual(dict(os.environ), before)
        self.assertFalse(outer.exists())
