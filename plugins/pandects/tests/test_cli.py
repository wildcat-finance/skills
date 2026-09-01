"""The two subcommands, and what they exit with."""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

import pandects  # noqa: E402
from pandects_lib import run as run_module  # noqa: E402


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            code = pandects.main(argv)
        except SystemExit as exit:
            code = exit.code
    return code, out.getvalue(), err.getvalue()


class LawsTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def empty_catalogue(self):
        path = os.path.join(self.root, "empty.json")
        with open(path, "w") as handle:
            json.dump(
                {
                    "version": "0.1.0",
                    "observables": "ICreditObservables",
                    "families": {"conservation": "held against each other"},
                    "laws": [],
                },
                handle,
            )
        return path

    def test_an_empty_catalogue_says_so_rather_than_printing_nothing(self):
        code, out, _ = run(["laws", "--catalogue", self.empty_catalogue()])
        self.assertEqual(code, 0)
        self.assertIn("no laws yet", out)
        self.assertIn("conservation", out)

    def test_the_shipped_catalogue_lists_its_laws_with_applicability(self):
        code, out, _ = run(["laws"])
        self.assertEqual(code, 0)
        self.assertIn("conservation/value-conserved/v1", out)
        self.assertIn("applies to:", out)

    def test_the_json_form_is_the_catalogue(self):
        code, out, _ = run(["laws", "--json"])
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertIn("families", found)
        self.assertTrue(found["laws"])
        for law in found["laws"]:
            self.assertIn("applicability", law)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, body):
        path = os.path.join(self.root, "catalogue.json")
        with open(path, "w") as handle:
            handle.write(body if isinstance(body, str) else json.dumps(body))
        return path

    def test_the_shipped_catalogue_passes(self):
        code, out, _ = run(["check"])
        self.assertEqual(code, 0)
        self.assertIn("every part present", out)

    def test_a_law_missing_a_part_exits_one_and_names_the_part(self):
        path = self.write(
            {
                "version": "0.1.0",
                "observables": "ICreditObservables",
                "families": {"conservation": "held against each other"},
                "laws": [
                    {
                        "id": "conservation/invented/v1",
                        "family": "conservation",
                        "statement": "Something hopeful.",
                        "component": "src/laws/Absent.sol",
                        "specimen": "specimens/Absent.sol",
                        "counterexample": "test/counterexamples/Absent.t.sol",
                        "applicability": {
                            "accounting_model": "pooled deposits",
                            "assumes": [],
                            "requires": [],
                        },
                        "bounds": "exact",
                    }
                ],
            }
        )
        code, out, _ = run(["check", "--catalogue", path])
        self.assertEqual(code, 1)
        self.assertIn("executes", out)
        self.assertIn("catches", out)
        self.assertIn("has been reduced", out)

    def test_a_malformed_catalogue_exits_two(self):
        path = self.write("{not json")
        code, _, err = run(["check", "--catalogue", path])
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)

    def test_the_json_form_carries_the_verdict(self):
        code, out, _ = run(["check", "--json"])
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertTrue(found["ok"])
        self.assertEqual(found["findings"], [])

    def test_no_subcommand_prints_help_and_exits_two(self):
        code, _, _ = run([])
        self.assertEqual(code, 2)


class RunTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_a_run_without_a_sibling_exercise_map_exits_two_and_names_it(self):
        catalogue = os.path.join(self.root, "catalogue.json")
        with open(catalogue, "w") as handle:
            json.dump(
                {
                    "version": "0.1.0",
                    "observables": "ICreditObservables",
                    "families": {"conservation": "held against each other"},
                    "laws": [],
                },
                handle,
            )
        original = run_module.run_foundry
        run_module.run_foundry = lambda root, match=None, timeout=1800: {
            "argv": ["forge", "test", "-vv"],
            "returncode": 0,
            "output": "",
        }
        try:
            code, _, err = run(["run", "--catalogue", catalogue])
        finally:
            run_module.run_foundry = original
        self.assertEqual(code, 2)
        self.assertIn("exercise.json", err)


if __name__ == "__main__":
    unittest.main()
