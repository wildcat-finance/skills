"""Step 1: the two undelivered boundaries refuse rather than guess."""

from __future__ import annotations

import contextlib
import importlib.util
import io
from pathlib import Path
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
SCRIPT = PLUGIN_ROOT / "skills/anamnesis/scripts/anamnesis.py"
SKILL = PLUGIN_ROOT / "skills/anamnesis/SKILL.md"
POLICY = str(PLUGIN_ROOT / "specimens/pilot/policy.json")


def load():
    spec = importlib.util.spec_from_file_location("anamnesis_reserved", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


anamnesis = load()


class ReservedBase(unittest.TestCase):
    """Shared checks, parameterised by the operation under test."""

    command = None
    code = None
    step = None

    def refuses_by_name(self):
        handler = getattr(anamnesis, f"cmd_{self.command}")
        with self.assertRaises(anamnesis.Refusal) as caught:
            handler(None)
        self.assertEqual(caught.exception.code, self.code)
        self.assertIn(self.step, caught.exception.message)
        self.assertIn(self.command, caught.exception.message)

    def reports_no_result(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exit_code = anamnesis.main([self.command])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn(self.code, err.getvalue())

    def accepts_no_shortcut(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exit_code = anamnesis.main([self.command, "--policy", POLICY])
        self.assertEqual(exit_code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn(self.code, err.getvalue())

    def writes_nothing(self):
        before = sorted(str(p) for p in PLUGIN_ROOT.rglob("*"))
        with contextlib.redirect_stderr(io.StringIO()):
            anamnesis.main([self.command])
        self.assertEqual(before, sorted(str(p) for p in PLUGIN_ROOT.rglob("*")))

    def declares_its_recovery(self, promise, recovery):
        text = SKILL.read_text(encoding="utf-8")
        block = text.split(f"### {promise}", 1)[1].split("### ")[0]
        self.assertIn("- Authorises: Nothing in this version.", block)
        self.assertIn("- Consequence: 0", block)
        self.assertIn(recovery, block)


class Curate(ReservedBase):
    command, code, step = "curate", "A090", "step 2"

    def test_curate_refuses_by_name(self):
        self.refuses_by_name()

    def test_curate_reports_no_result(self):
        self.reports_no_result()

    def test_curate_accepts_no_policy_shortcut(self):
        self.accepts_no_shortcut()

    def test_curate_writes_nothing(self):
        self.writes_nothing()

    def test_curate_declares_its_recovery(self):
        self.declares_its_recovery(
            "anamnesis-corpus-curation",
            "Land runbook step 2 and its evidence, then invoke `curate`.",
        )


class Release(ReservedBase):
    command, code, step = "release", "A091", "step 3"

    def test_release_refuses_by_name(self):
        self.refuses_by_name()

    def test_release_reports_no_result(self):
        self.reports_no_result()

    def test_release_accepts_no_policy_shortcut(self):
        self.accepts_no_shortcut()

    def test_release_writes_nothing(self):
        self.writes_nothing()

    def test_release_declares_its_recovery(self):
        self.declares_its_recovery(
            "anamnesis-corpus-release",
            "Land runbook step 3 and its evidence, then invoke `release`.",
        )


if __name__ == "__main__":
    unittest.main()
