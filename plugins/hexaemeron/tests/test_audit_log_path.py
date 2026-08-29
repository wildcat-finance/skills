"""Where a run's audit record goes, and what a round may say about it.

Split out of `test_hexctl.py` rather than added to it: issue 554's amendment
tests and this run's landed in the same release, and together they took that
module past the Promise Machine's 262144-byte bounded-read ceiling. Neither
side crossed it alone. The cases are unchanged.
"""

import json
import os
import shutil
import tempfile
import unittest

import sys

# `run_tests.py` discovers from this directory and puts it on the path; a reader
# running this module on its own does not get that, and the shared harness lives
# next door rather than in a package.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from test_hexctl import HexctlCase, LINTS_CLEAN, hexctl_module


class AuditRoundLogBindingTests(HexctlCase):
    """A round records the file it was told to write, not a free string.

    `--log` was stored verbatim while the Warden packet named
    `config audit.log_path`, so a receipt could name a file the round never
    opened and nothing noticed.
    """

    def to_waived_audit(self):
        self.to_audit()
        self.run_ctl("record", "security_suite", '"waived: prose-only repo"')

    def rounds(self):
        return self.state()["steps"][0]["audit"]["rounds"]

    def configured(self):
        return json.loads(self.run_ctl("config", "get", "audit.log_path").stdout)

    def state_bytes(self):
        with open(os.path.join(self.target, ".hexaemeron", "state.json"), "rb") as fh:
            return fh.read()

    def test_a_round_naming_the_configured_path_is_recorded(self):
        self.to_waived_audit()
        self.run_ctl(
            "audit-round", "--findings", "0", "--log", self.configured(),
            *LINTS_CLEAN,
        )
        self.assertEqual(self.rounds()[0]["log"], self.configured())

    def test_a_round_naming_another_file_is_refused(self):
        self.to_waived_audit()
        proc = self.run_ctl(
            "audit-round", "--findings", "0", "--log", "audit/AUDIT.md",
            *LINTS_CLEAN, expect=2,
        )
        self.assertIn("audit/AUDIT.md", proc.stderr)
        self.assertIn(self.configured(), proc.stderr)
        self.assertEqual(self.rounds(), [])

    def test_a_refused_round_leaves_the_state_file_byte_identical(self):
        self.to_waived_audit()
        before = self.state_bytes()
        self.run_ctl(
            "audit-round", "--findings", "0", "--log", "somewhere/else.md",
            *LINTS_CLEAN, expect=2,
        )
        self.assertEqual(self.state_bytes(), before)

    def test_a_round_with_no_declaration_records_the_configured_path(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        self.assertEqual(self.rounds()[0]["log"], self.configured())

    def test_another_spelling_of_the_same_file_is_accepted(self):
        """Refusing a leading `./` would be refusing punctuation."""
        self.to_waived_audit()
        self.run_ctl(
            "audit-round", "--findings", "0", "--log", "./" + self.configured(),
            *LINTS_CLEAN,
        )
        self.assertEqual(self.rounds()[0]["log"], self.configured())

    def test_the_directive_names_the_file_the_round_owes(self):
        """An inline caller learns the path before the refusal, not from it."""
        self.to_waived_audit()
        self.assertEqual(self.next_json()["log_path"], self.configured())

    def test_closing_the_audit_refuses_a_divergent_declaration(self):
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        proc = self.run_ctl(
            "done", "audit", "--log", "audit/AUDIT.md", expect=2
        )
        self.assertIn("audit/AUDIT.md", proc.stderr)
        self.assertEqual(self.state()["steps"][0]["phase"], "audit")

    def test_closing_the_audit_keeps_a_round_recorded_before_this_check(self):
        """Nothing rewrites a receipt that is already on the ledger."""
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state["steps"][0]["audit"]["rounds"][0]["log"] = "audit/AUDIT.md"
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        self.run_ctl("done", "audit")
        self.assertEqual(
            self.state()["steps"][0]["receipts"]["audit"]["log"], "audit/AUDIT.md"
        )

    def test_a_closure_keeping_a_recorded_log_does_not_need_the_config(self):
        """Round 1 finding. Config was read even when nothing wanted it."""
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state["steps"][0]["audit"]["rounds"][0]["log"] = "audit/AUDIT.md"
        del state["config"]["audit"]["log_path"]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        self.run_ctl("done", "audit")
        self.assertEqual(
            self.state()["steps"][0]["receipts"]["audit"]["log"], "audit/AUDIT.md"
        )

    def test_a_closure_with_nothing_recorded_and_no_config_still_refuses(self):
        """The fix narrows when config is read, not whether absence bites."""
        self.to_waived_audit()
        self.run_ctl("audit-round", "--findings", "0", *LINTS_CLEAN)
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state["steps"][0]["audit"]["rounds"][0]["log"] = None
        del state["config"]["audit"]["log_path"]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        proc = self.run_ctl("done", "audit", expect=2)
        self.assertIn("config audit.log_path is missing", proc.stderr)

    def test_a_run_with_no_configured_path_refuses_rather_than_recording_none(self):
        """Fail closed: a round with nowhere to write is not a round."""
        self.to_waived_audit()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        del state["config"]["audit"]["log_path"]
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        proc = self.run_ctl(
            "audit-round", "--findings", "0", *LINTS_CLEAN, expect=2
        )
        self.assertIn("config audit.log_path is missing", proc.stderr)


class AuditLogPathTests(HexctlCase):
    """A run's rounds go to a file no other run writes.

    The shared literal put every run's log on both sides of `sync-run`'s
    product/upstream intersection, so a run that only appended to that file
    still owed a green check over it before it could integrate. `init` derives
    the path from the run branch instead. An override may move the directory,
    because three plugins here keep their rounds under their own tree, but it
    may not take the name, because the name is what keeps two runs apart.
    """

    def log_path(self):
        return json.loads(self.run_ctl("config", "get", "audit.log_path").stdout)

    def derived_name(self):
        return self.run_branch().replace("/", "-") + ".md"

    def state_bytes(self):
        with open(os.path.join(self.target, ".hexaemeron", "state.json"), "rb") as fh:
            return fh.read()

    def test_a_fresh_run_derives_its_own_log_path(self):
        self.init(topic="give each run its own log")
        self.assertEqual(self.log_path(), "audit/rounds/" + self.derived_name())

    def test_no_literal_log_path_survives_in_the_config_template(self):
        """A literal here is what a run copies, so there is no literal here."""
        self.assertNotIn("log_path", hexctl_module().DEFAULT_CONFIG["audit"])

    def test_two_run_branches_derive_two_paths(self):
        derive = hexctl_module().run_audit_log_path
        self.assertEqual(derive("fiat/576-one"), "audit/rounds/fiat-576-one.md")
        self.assertEqual(derive("fiat/577-two"), "audit/rounds/fiat-577-two.md")

    def test_an_override_may_move_the_directory(self):
        self.init()
        moved = "plugins/hexaemeron/audit/rounds/" + self.derived_name()
        self.run_ctl("config", "set", "audit.log_path", json.dumps(moved))
        self.assertEqual(self.log_path(), moved)

    def test_an_override_may_not_take_another_records_name(self):
        self.init()
        for value in (
            "audit/AUDIT.md",
            "audit/rounds/fiat-999-somebody-elses-run.md",
            "audit/rounds/" + self.derived_name().removesuffix(".md"),
        ):
            with self.subTest(value=value):
                proc = self.run_ctl(
                    "config", "set", "audit.log_path", json.dumps(value), expect=2
                )
                self.assertIn("must end in", proc.stderr)
                self.assertIn(self.derived_name(), proc.stderr)

    def test_an_absolute_override_is_refused(self):
        self.init()
        proc = self.run_ctl(
            "config", "set", "audit.log_path",
            json.dumps("/tmp/" + self.derived_name()), expect=2,
        )
        self.assertIn("absolute path", proc.stderr)

    def test_an_override_climbing_out_with_dotdot_is_refused(self):
        self.init()
        proc = self.run_ctl(
            "config", "set", "audit.log_path",
            json.dumps("../" + self.derived_name()), expect=2,
        )
        self.assertIn("'..' component", proc.stderr)

    def test_a_control_character_in_the_directory_is_refused(self):
        """In the directory, so the basename check cannot be what refuses it."""
        self.init()
        proc = self.run_ctl(
            "config", "set", "audit.log_path",
            json.dumps("aud\u0001it/rounds/" + self.derived_name()), expect=2,
        )
        self.assertIn("control character", proc.stderr)

    def test_an_override_reaching_outside_through_a_symlink_is_refused(self):
        """Every textual check passes; only resolving the path catches this."""
        self.init()
        outside = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, outside, True)
        os.symlink(outside, os.path.join(self.target, "elsewhere"))
        proc = self.run_ctl(
            "config", "set", "audit.log_path",
            json.dumps("elsewhere/" + self.derived_name()), expect=2,
        )
        self.assertIn("escapes target directory", proc.stderr)

    def test_a_value_that_is_not_a_non_empty_string_is_refused(self):
        self.init()
        for value in ("null", "3", "[]", '""'):
            with self.subTest(value=value):
                proc = self.run_ctl(
                    "config", "set", "audit.log_path", value, expect=2
                )
                self.assertIn("non-empty string", proc.stderr)

    def test_a_refused_override_leaves_the_state_file_byte_identical(self):
        self.init()
        before = self.state_bytes()
        self.run_ctl("config", "set", "audit.log_path", '"audit/AUDIT.md"', expect=2)
        self.assertEqual(self.state_bytes(), before)

    def test_replacing_the_whole_audit_section_is_immutable(self):
        self.init()
        section = json.loads(self.run_ctl("config", "get", "audit").stdout)
        section["log_path"] = "plugins/hexaemeron/audit/rounds/" + self.derived_name()
        proc = self.run_ctl(
            "config", "set", "audit", json.dumps(section), expect=2
        )
        self.assertIn("config path is immutable", proc.stderr)
        self.assertEqual(self.log_path(), "audit/rounds/" + self.derived_name())

    def test_only_the_log_path_leaf_may_move_the_record(self):
        self.init()
        moved = "plugins/hexaemeron/audit/rounds/" + self.derived_name()
        self.run_ctl("config", "set", "audit.log_path", json.dumps(moved))
        self.assertEqual(self.log_path(), moved)

    def test_a_branch_stored_as_the_wrong_type_answers_rather_than_raising(self):
        """Round 1 finding. The flattening runs a regex over the stored value."""
        self.init()
        path = os.path.join(self.target, ".hexaemeron", "state.json")
        with open(path, encoding="utf-8") as fh:
            state = json.load(fh)
        state["run_branch"] = 17
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(state, fh)
        proc = self.run_ctl("config", "set", "audit.log_path", '"audit/AUDIT.md"')
        self.assertNotIn("Traceback", proc.stderr)
        self.assertEqual(self.log_path(), "audit/AUDIT.md")

    def test_a_run_with_no_recorded_branch_keeps_the_older_freedom(self):
        """Nothing to derive from, so the constraint has nothing to say."""
        self.init()
        self.strip_run_branch()
        self.run_ctl("config", "set", "audit.log_path", '"audit/AUDIT.md"')
        self.assertEqual(self.log_path(), "audit/AUDIT.md")
