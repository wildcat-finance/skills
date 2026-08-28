"""Every subcommand the parser offers, and the exit codes they use.

The count is not stated here on purpose. A docstring naming it goes stale the next
time one is added, which is how registry.py came to say the registry was empty and
test_cli.py came to say there were two subcommands when there were six.
"""

import contextlib
import io
import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import envelope, statement  # noqa: E402

STATEMENT = {
    "_type": statement.STATEMENT_TYPE,
    "subject": [{"name": "Escrow", "digest": {"sha256": "ab" * 32}}],
    "predicateType": "https://ariadne.wildcat.finance/example/v1",
    "predicate": {"claims": []},
}


def run(argv):
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = ariadne.main(argv)
    return code, out.getvalue(), err.getvalue()


class PredicatesTests(unittest.TestCase):
    def test_predicates_lists_the_solidity_release_predicate(self):
        code, out, _ = run(["predicates"])
        self.assertEqual(code, 0)
        self.assertIn("https://ariadne.wildcat.finance/solidity-release/v1", out)

    def test_predicates_lists_the_dataset_predicate(self):
        code, out, _ = run(["predicates"])
        self.assertEqual(code, 0)
        self.assertIn("https://ariadne.wildcat.finance/dataset/v1", out)

    def test_predicates_lists_both_state_fixture_versions(self):
        code, out, _ = run(["predicates"])
        self.assertEqual(code, 0)
        self.assertIn("https://ariadne.wildcat.finance/state-fixture/v1", out)
        self.assertIn("https://ariadne.wildcat.finance/state-fixture/v2", out)

    def test_predicates_json_carries_the_type_and_summary(self):
        code, out, _ = run(["predicates", "--json"])
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertEqual(
            [entry["type"] for entry in found],
            [
                "https://ariadne.wildcat.finance/dataset/v1",
                "https://ariadne.wildcat.finance/grounded-agent/v1",
                "https://ariadne.wildcat.finance/solidity-release/v1",
                "https://ariadne.wildcat.finance/state-fixture/v1",
                "https://ariadne.wildcat.finance/state-fixture/v2",
            ],
        )
        self.assertTrue(all(entry["summary"] for entry in found))

    def test_capture_state_fixture_help_names_version_dispatch(self):
        parser = ariadne.build_parser()
        for action in parser._subparsers._group_actions:  # noqa: SLF001
            fixture_parser = action.choices["capture-state-fixture"]
            break
        else:
            self.fail("capture-state-fixture is not registered")
        self.assertIn("v1 or v2 fixture", fixture_parser.format_help())


class InspectTests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def write(self, name, content):
        path = os.path.join(self.root, name)
        with open(path, "wb") as handle:
            handle.write(content if isinstance(content, bytes) else content.encode())
        return path

    def test_a_bare_statement_is_reported_unsigned(self):
        path = self.write("statement.json", json.dumps(STATEMENT))
        code, out, _ = run(["inspect", path])
        self.assertEqual(code, 0)
        self.assertIn("unsigned", out)
        self.assertIn("Escrow", out)
        self.assertIn("not registered here", out)

    def test_an_envelope_is_unwrapped_and_reported(self):
        wrapped = envelope.wrap(json.dumps(STATEMENT).encode("utf-8"))
        path = self.write("envelope.json", wrapped.to_json())
        code, out, _ = run(["inspect", path, "--json"])
        self.assertEqual(code, 0)
        found = json.loads(out)
        self.assertEqual(found["predicateType"], STATEMENT["predicateType"])
        self.assertFalse(found["predicateTypeKnown"])
        self.assertIn("unsigned", found["signatureState"])

    def test_inspect_escapes_a_subject_name_that_utf8_cannot_encode(self):
        candidate = dict(STATEMENT)
        candidate["subject"] = [dict(STATEMENT["subject"][0])]
        candidate["subject"][0]["name"] = "subject\ud800"
        path = self.write("surrogate.json", json.dumps(candidate))
        code, out, _ = run(["inspect", path])
        self.assertEqual(code, 0)
        self.assertIn(r"subject\ud800", out)
        self.assertNotIn("subject\ud800", out)

    def test_a_missing_file_exits_two(self):
        code, _, err = run(["inspect", os.path.join(self.root, "absent.json")])
        self.assertEqual(code, 2)
        self.assertIn("no such file", err)

    def test_a_malformed_statement_exits_two_with_the_reason(self):
        path = self.write("bad.json", json.dumps({"_type": "wrong"}))
        code, _, err = run(["inspect", path])
        self.assertEqual(code, 2)
        self.assertIn("_type", err)

    def test_a_deeply_nested_file_exits_two_rather_than_one(self):
        """Exit 1 means a gate was breached. Unreadable input is exit 2, and an
        escaping RecursionError would have reported the wrong one."""
        depth = 200000
        path = self.write("deep.json", '{"a":' * depth + "1" + "}" * depth)
        code, _, err = run(["inspect", path])
        self.assertEqual(code, 2)
        self.assertIn("nested deeper", err)

    def test_no_subcommand_prints_help_and_exits_two(self):
        code, _, _ = run([])
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
