"""No test may anchor temporary scratch under a status-visible tree path.

Scratch created inside the tracked tree makes the repository transiently
non-quiescent while a test runs: `git status` gains `??` entries that race
any concurrent stability assertion -- the disposable-signing guard's
before/after porcelain comparison is the live victim -- and the check
runner's shared-snapshot source verification then reports a mutated source.
Audit finding S3-R1-01 on issue #622 recorded exactly this class after
fifty-eight sites had already been repaired and two survived.

The rule this guard enforces is structural, so it fails deterministically
without ever racing: a `dir=` argument on a `tempfile` construction inside a
test module is permitted only inside the vetted `scratch_directory` helpers,
which anchor at the gitignored top-level `tmp/`.  Every other test-module
`tempfile` construction must use the system default location.
"""

from __future__ import annotations

import ast
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPFILE_CONSTRUCTORS = {
    "TemporaryDirectory",
    "mkdtemp",
    "mkstemp",
    "NamedTemporaryFile",
    "TemporaryFile",
    "SpooledTemporaryFile",
}
ALLOWED_ENCLOSING_FUNCTION = "scratch_directory"


def anchored_scratch_violations(source: str, filename: str) -> list[str]:
    """Return one line per `dir=`-anchored tempfile construction outside the helper."""
    tree = ast.parse(source, filename=filename)
    violations = []

    def visit(node: ast.AST, enclosing: str | None) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            enclosing = node.name
        if isinstance(node, ast.Call):
            callee = node.func
            named = (
                callee.attr
                if isinstance(callee, ast.Attribute)
                else callee.id if isinstance(callee, ast.Name) else None
            )
            if named in TEMPFILE_CONSTRUCTORS:
                for keyword in node.keywords:
                    if keyword.arg == "dir" and enclosing != ALLOWED_ENCLOSING_FUNCTION:
                        violations.append(
                            f"{filename}:{node.lineno}: {named}(dir=...) outside "
                            f"{ALLOWED_ENCLOSING_FUNCTION}"
                        )
        for child in ast.iter_child_nodes(node):
            visit(child, enclosing)

    visit(tree, None)
    return violations


def tracked_test_sources() -> list[str]:
    listed = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=str(ROOT),
        check=True,
        capture_output=True,
        shell=False,
    )
    return sorted(
        path
        for path in listed.stdout.decode("utf-8").split("\0")
        if path.endswith(".py")
        and (path.startswith("tests/") or "/tests/" in path)
    )


class ScratchQuiescenceTests(unittest.TestCase):
    def test_no_test_module_anchors_scratch_outside_the_helper(self):
        sources = tracked_test_sources()
        self.assertGreater(len(sources), 50, "test-source discovery collapsed")
        violations = []
        for rel in sources:
            source = (ROOT / rel).read_text(encoding="utf-8")
            violations.extend(anchored_scratch_violations(source, rel))
        self.assertEqual(
            violations, [],
            "tests anchor scratch under a status-visible path; use the "
            "scratch_directory helper on the ignored top-level tmp/",
        )

    def test_the_helper_anchor_stays_gitignored(self):
        ignore = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(
            "/tmp/", ignore,
            "the top-level tmp/ scratch anchor must stay ignored, or every "
            "helper-created directory becomes status-visible at once",
        )

    def test_detector_is_red_on_the_recorded_defect_forms(self):
        """Hostile specimens: the exact anchored forms S3-R1-01 and ff92fdd removed."""
        specimens = {
            "parent-41f074ba": (
                "import tempfile\n"
                "def test_case(self):\n"
                '    with tempfile.TemporaryDirectory(dir=ROOT / "tests") as d:\n'
                "        pass\n"
            ),
            "fixtures-anchor": (
                "import tempfile\n"
                "def test_case(self):\n"
                "    with tempfile.TemporaryDirectory(dir=FIXTURES) as d:\n"
                "        pass\n"
            ),
            "root-anchor": (
                "from tempfile import TemporaryDirectory\n"
                "def test_case(self):\n"
                "    with TemporaryDirectory(dir=ROOT) as d:\n"
                "        pass\n"
            ),
            "module-level": (
                "import tempfile\n"
                "scratch = tempfile.mkdtemp(dir=SOMEWHERE)\n"
            ),
        }
        for name, source in specimens.items():
            with self.subTest(specimen=name):
                self.assertTrue(
                    anchored_scratch_violations(source, name),
                    "the detector passed a specimen of the recorded defect",
                )

    def test_detector_accepts_the_helper_and_system_temp(self):
        clean = (
            "import tempfile\n"
            f"def {ALLOWED_ENCLOSING_FUNCTION}(prefix='x-'):\n"
            '    scratch = ROOT / "tmp"\n'
            "    scratch.mkdir(exist_ok=True)\n"
            "    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)\n"
            "def test_case(self):\n"
            "    with tempfile.TemporaryDirectory() as outside:\n"
            "        pass\n"
        )
        self.assertEqual(anchored_scratch_violations(clean, "clean"), [])


if __name__ == "__main__":
    unittest.main()
