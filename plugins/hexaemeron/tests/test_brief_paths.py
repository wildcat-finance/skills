"""An audit brief's path-valued fields never count as a claim.

`WardenContinuityCases.test_the_field_never_claims_a_document_was_read` once
searched every byte of the brief for "read", `plugin_root` included, so it
failed whenever the checkout path spelled the word, as the skills#2093 run
worktree does. This guard runs that case under a controller whose plugin root
names "read", so it fails on a check that still reads path-derived fields.
"""

import os
from pathlib import Path
import shutil
import sys
import tempfile
from unittest import mock

try:
    from plugins.hexaemeron.tests import test_hexctl as controller_tests
except ModuleNotFoundError:  # direct discovery from this directory
    import test_hexctl as controller_tests


HexctlCase = controller_tests.HexctlCase
CASES = controller_tests.WardenContinuityCases


# Large trees an audit brief never reads stay links; the controller refuses a
# linked file wherever it reads one, so everything else is a real copy.
LINKED = ("assets", "docs", "harness", "tests", "skills/fiat/checkpoint-authority")


def mirrored_controller(root):
    """A copy of the plugin, with its large trees linked, at `root/hexaemeron`."""
    source = Path(controller_tests.HEXCTL).resolve().parents[3]
    mirror = Path(root) / "hexaemeron"

    def skipped(directory, names):
        relative = Path(directory).relative_to(source)
        return [
            name for name in names
            if name == "__pycache__" or (relative / name).as_posix() in LINKED
        ]

    shutil.copytree(source, mirror, ignore=skipped)
    for relative in LINKED:
        if (source / relative).exists():
            (mirror / relative).symlink_to(source / relative)
    return mirror, mirror / "skills" / "fiat" / "scripts" / "hexctl.py"


class BriefPaths(HexctlCase):
    def test_plugin_root_naming_read(self):
        holder = tempfile.mkdtemp(prefix="thread-")
        self.addCleanup(shutil.rmtree, holder, True)
        mirror, controller = mirrored_controller(holder)
        harness = sys.modules[HexctlCase.__module__]
        with mock.patch.object(harness, "HEXCTL", str(controller)):
            CASES.test_the_field_never_claims_a_document_was_read(self)
            brief = self.audit_brief()
        self.assertEqual(brief["plugin_root"], os.path.realpath(mirror))
        self.assertIn("read", brief["plugin_root"])


# The case's own helpers and constants, never its tests, which run in
# `test_hexctl`.
for _name, _value in vars(CASES).items():
    if not _name.startswith(("test_", "__")):
        setattr(BriefPaths, _name, _value)

del _name, _value
