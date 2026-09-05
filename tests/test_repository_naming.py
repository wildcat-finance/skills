"""Repository names that must describe maintained behaviour."""

from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
ISSUE_NUMBERED_TEST = re.compile(
    r"(?:^|/)test_issue(?:_|-)?[0-9]+(?:[_.-]|$)"
)


def git_environment():
    """Remove inherited Git routing so the query stays in this repository."""
    environment = dict(os.environ)
    for name in (
        "GIT_DIR",
        "GIT_INDEX_FILE",
        "GIT_WORK_TREE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_NAMESPACE",
        "GIT_PREFIX",
        "GIT_INTERNAL_SUPER_PREFIX",
    ):
        environment.pop(name, None)
    return environment


class RepositoryNamingTests(unittest.TestCase):
    def test_test_modules_are_named_for_behaviour_not_issue_numbers(self):
        completed = subprocess.run(  # phylax: allow subprocess: fixed Git query
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            check=True,
            capture_output=True,
            env=git_environment(),
        )
        paths = [os.fsdecode(path) for path in completed.stdout.split(b"\0") if path]
        offenders = sorted(
            path
            for path in paths
            if (ROOT / path).is_file() and ISSUE_NUMBERED_TEST.search(path)
        )
        self.assertEqual(
            offenders,
            [],
            "test modules must name maintained behaviour, not the issue that "
            f"introduced it: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
