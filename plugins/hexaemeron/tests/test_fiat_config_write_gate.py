"""Fiat configuration writes stop at the operator's explicit allowlist."""

import json
import os

try:
    from plugins.hexaemeron.tests.test_hexctl import HexctlCase
except ModuleNotFoundError:
    from test_hexctl import HexctlCase


class FiatConfigWriteGateTests(HexctlCase):
    def config_bytes(self):
        state_path = os.path.join(self.target, ".hexaemeron", "state.json")
        ledger_path = os.path.join(self.target, ".hexaemeron", "ledger.jsonl")
        with open(state_path, "rb") as handle:
            state = handle.read()
        with open(ledger_path, "rb") as handle:
            ledger = handle.read()
        return state, ledger

    def test_config_set_refuses_paths_outside_log_path_and_git(self):
        self.init()
        for path, value in (
            ("audit.max_rounds", "9"),
            ("audit.fold", "true"),
            ("audit.stacked_suffix", '"--other"'),
            ("audit", "{}"),
            ("skills.prose_lint", '"other"'),
            ("skills", "{}"),
            ("solidity", "true"),
        ):
            with self.subTest(path=path):
                before = self.config_bytes()
                proc = self.run_ctl("config", "set", path, value, expect=2)
                self.assertIn("config path is immutable", proc.stderr)
                self.assertIn("audit.log_path", proc.stderr)
                self.assertIn("git", proc.stderr)
                self.assertEqual(self.config_bytes(), before)

    def test_config_set_allows_the_whole_git_section(self):
        self.init()
        git_config = json.loads(self.run_ctl("config", "get", "git").stdout)
        git_config["draft_pr"] = True
        self.run_ctl("config", "set", "git", json.dumps(git_config))
        self.assertEqual(
            json.loads(self.run_ctl("config", "get", "git").stdout), git_config
        )

    def test_the_solidity_key_is_immutable(self):
        self.init()
        for value in ('"auto"', "true", "false"):
            with self.subTest(value=value):
                proc = self.run_ctl("config", "set", "solidity", value, expect=2)
                self.assertIn("config path is immutable", proc.stderr)
        self.assertEqual(
            json.loads(self.run_ctl("config", "get", "solidity").stdout), "auto"
        )
