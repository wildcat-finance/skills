"""How the controller reads a remote ref, in its own module.

`test_hexctl.py` is cited as authored law by the promise machine, whose
bounded read refuses a contract over 262144 bytes, and the file has under a
kilobyte of headroom left. The case drives `remote_branch_tip` through the
same fixtures -- `HexctlCase` and its fake delivery tools -- so only the file
boundary moved, not the arrangement under test.
"""

import json
import os
from contextlib import redirect_stderr
from io import StringIO
from unittest import mock

try:
    from plugins.hexaemeron.tests.test_hexctl import HexctlCase, hexctl_module
except ModuleNotFoundError:
    from test_hexctl import HexctlCase, hexctl_module


class TestRemoteBranchTipDiagnostics(HexctlCase):
    def test_an_absent_remote_branch_is_diagnosed_apart_from_a_malformed_one(self):
        """The recovery only exists for one of them, so the message has to differ.

        `done integrate` reads the run branch tip until its own receipt exists,
        and deleting branches straight after merging the integration pull
        request is the natural instinct. Reporting that as a ref-count problem
        sends the reader looking for malformed remote output instead of the
        branch they just deleted, which is still reachable from the base.
        """
        module = hexctl_module()
        branch = "fiat/run"
        base_env = {
            "PATH": self.env["PATH"],
            "FAKE_GIT_REFS": json.dumps({branch: "8" * 40}),
        }

        seen = {}
        for mode in ("remote-absent", "remote-duplicate"):
            error = StringIO()
            with mock.patch.dict(
                os.environ, {**base_env, "FAKE_GIT_MODE": mode}
            ), redirect_stderr(error):
                with self.assertRaises(SystemExit):
                    module.remote_branch_tip(self.dir, branch)
            seen[mode] = error.getvalue()

        self.assertIn("names no ref", seen["remote-absent"])
        self.assertIn(f"refs/heads/{branch}", seen["remote-absent"])
        self.assertIn("restore it", seen["remote-absent"])

        self.assertNotIn("names no ref", seen["remote-duplicate"])
        self.assertIn("exactly one ref", seen["remote-duplicate"])
