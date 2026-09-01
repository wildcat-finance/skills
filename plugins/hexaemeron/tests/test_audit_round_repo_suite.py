"""What an audit-round directive says about the repository's own suite.

Issue 1067: two steps were receipted through implement, audit, prose and push
with the three lints green, and hosted CI then failed both on root tests,
because nothing in the loop names the repository's own suite. The directive now
carries the `root-suite` command from a discoverable `tests/check-map-v1.json`
the way it already carries the log path and the lint flags. Carriage is
informational and fail-open, and these are the guards in both directions: a
declared suite rides the directive, and every malformed or absent shape leaves
the directive without the field rather than refusing it.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_hexctl import HexctlCase, hexctl_module


def check_map(argv=("python3", "-m", "unittest", "discover", "-s", "tests")):
    return json.dumps(
        {
            "schema": "wildcat.check-map.v1",
            "checks": {
                "root-suite": {
                    "title": "Root repository suite",
                    "argv": list(argv),
                    "cwd": ".",
                    "kind": "suite",
                    "script": "tests",
                }
            },
        }
    )


class AuditRoundRepoSuiteDirectiveTests(HexctlCase):
    """The CLI surface: what `next` carries into an audit round."""

    def to_waived_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')

    def test_a_declared_root_suite_rides_the_audit_round_directive(self):
        self.to_waived_audit()
        self.write("tests/check-map-v1.json", check_map())
        packet = self.next_json()
        self.assertEqual(packet["do"], "audit-round")
        self.assertEqual(
            packet["repo_suite"],
            {
                "source": "tests/check-map-v1.json",
                "check": "root-suite",
                "argv": ["python3", "-m", "unittest", "discover", "-s", "tests"],
                "cwd": ".",
            },
        )

    def test_without_a_map_the_directive_carries_no_suite(self):
        self.to_waived_audit()
        packet = self.next_json()
        self.assertEqual(packet["do"], "audit-round")
        self.assertNotIn("repo_suite", packet)

    def test_two_reads_of_the_same_directive_agree(self):
        self.to_waived_audit()
        self.write("tests/check-map-v1.json", check_map())
        self.assertEqual(self.run_ctl("next").stdout, self.run_ctl("next").stdout)


class RepositoryCheckCommandTests(unittest.TestCase):
    """The discovery function, driven over every refusal shape directly."""

    @classmethod
    def setUpClass(cls):
        cls.hexctl = hexctl_module()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = self.tmp.name

    def write_map(self, payload):
        path = os.path.join(self.root, "tests", "check-map-v1.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(payload)

    def discovered(self):
        return self.hexctl.repository_check_command(self.root)

    def test_a_valid_map_yields_the_root_check(self):
        self.write_map(check_map())
        self.assertEqual(
            self.discovered(),
            {
                "source": "tests/check-map-v1.json",
                "check": "root-suite",
                "argv": ["python3", "-m", "unittest", "discover", "-s", "tests"],
                "cwd": ".",
            },
        )

    def test_no_base_dir_discovers_nothing(self):
        self.assertIsNone(self.hexctl.repository_check_command(None))

    def test_no_map_discovers_nothing(self):
        self.assertIsNone(self.discovered())

    def test_invalid_json_discovers_nothing(self):
        self.write_map("{not json")
        self.assertIsNone(self.discovered())

    def test_duplicate_keys_discover_nothing(self):
        body = check_map()
        duplicated = body[:-1] + ', "schema": "wildcat.check-map.v1"}'
        self.write_map(duplicated)
        self.assertIsNone(self.discovered())

    def test_a_foreign_schema_discovers_nothing(self):
        self.write_map(check_map().replace("wildcat.check-map.v1", "someone.else/v9"))
        self.assertIsNone(self.discovered())

    def test_a_document_that_is_not_an_object_discovers_nothing(self):
        self.write_map('["wildcat.check-map.v1"]')
        self.assertIsNone(self.discovered())

    def test_checks_that_are_not_an_object_discover_nothing(self):
        self.write_map('{"schema": "wildcat.check-map.v1", "checks": []}')
        self.assertIsNone(self.discovered())

    def test_a_missing_root_check_discovers_nothing(self):
        self.write_map(check_map().replace("root-suite", "elsewhere-suite"))
        self.assertIsNone(self.discovered())

    def test_an_argv_that_is_not_a_list_discovers_nothing(self):
        self.write_map(
            '{"schema": "wildcat.check-map.v1",'
            ' "checks": {"root-suite": {"argv": "python3 -m unittest"}}}'
        )
        self.assertIsNone(self.discovered())

    def test_an_empty_argv_discovers_nothing(self):
        self.write_map(
            '{"schema": "wildcat.check-map.v1",'
            ' "checks": {"root-suite": {"argv": []}}}'
        )
        self.assertIsNone(self.discovered())

    def test_a_non_string_argv_member_discovers_nothing(self):
        self.write_map(
            '{"schema": "wildcat.check-map.v1",'
            ' "checks": {"root-suite": {"argv": ["python3", 3]}}}'
        )
        self.assertIsNone(self.discovered())

    def test_an_empty_argv_member_discovers_nothing(self):
        self.write_map(
            '{"schema": "wildcat.check-map.v1",'
            ' "checks": {"root-suite": {"argv": ["python3", ""]}}}'
        )
        self.assertIsNone(self.discovered())

    def test_a_cwd_that_is_not_a_string_discovers_nothing(self):
        self.write_map(
            '{"schema": "wildcat.check-map.v1",'
            ' "checks": {"root-suite": {"argv": ["python3"], "cwd": 4}}}'
        )
        self.assertIsNone(self.discovered())

    def test_a_missing_cwd_defaults_to_the_repository_root(self):
        self.write_map(
            '{"schema": "wildcat.check-map.v1",'
            ' "checks": {"root-suite": {"argv": ["python3"]}}}'
        )
        self.assertEqual(self.discovered()["cwd"], ".")

    def test_an_oversized_map_discovers_nothing(self):
        body = check_map()
        padding = " " * (self.hexctl.CHECK_MAP_BYTES_MAX + 1 - len(body))
        self.write_map(body + padding)
        self.assertIsNone(self.discovered())


if __name__ == "__main__":
    unittest.main()
