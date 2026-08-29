from pathlib import Path
import json
import re
import sys
import unittest


PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
sys.path.insert(0, str(ROOT))
from repo_contract import assert_host_descriptions_agree, assert_router_reaches

SKILL = PLUGIN / "skills" / "sapheneia" / "SKILL.md"


class SapheneiaContractTests(unittest.TestCase):
    def test_ranked_contract_has_exactly_ten_rules(self):
        text = SKILL.read_text(encoding="utf-8")
        rules = [int(value) for value in re.findall(r"(?m)^### ([0-9]+)\. ", text)]
        self.assertEqual(rules, list(range(1, 11)))

    def test_contract_applies_to_agent_replies_and_persists(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Apply this skill to the agent itself.", text)
        self.assertIn("commentary, progress updates", text)
        self.assertIn("Keep it active for the rest of the session.", text)
        self.assertIn("The reader's stated preference outranks this default.", text)

    def test_host_descriptions_remain_identical(self):
        # Cross-host parity is the repo-wide contract; length is sapheneia's own bound.
        assert_host_descriptions_agree(self, "sapheneia")
        codex = json.loads(
            (PLUGIN / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(len(codex["description"]), 25)
        self.assertLessEqual(len(codex["description"]), 64)

    def test_promise_machine_router_reaches_the_runtime_contract(self):
        assert_router_reaches(self, "sapheneia")
        text = (ROOT / ".agents" / "skills" / "promise-machine" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("durable agent-authored audit records", text)
        self.assertIn("GitHub issue titles, bodies and comments", text)

    def test_durable_record_contract_is_bounded_and_preserves_evidence(self):
        text = SKILL.read_text(encoding="utf-8")
        promise = text.split("### sapheneia-durable-record-shape", 1)[1]
        promise = promise.split("\n### ", 1)[0]
        for surface in (
            "agent-authored audit record",
            "GitHub issue title and body",
            "GitHub issue comment",
        ):
            self.assertIn(surface, text)
        for protected in (
            "file:line",
            "hashes",
            "selectors",
            "unknowns",
            "negative evidence",
            "required host structure",
        ):
            self.assertIn(protected, text)
        self.assertIn("does not activate session-wide Sapheneia", text)
        self.assertIn("Consequence: 1", promise)
        self.assertIn("existing durable records", promise)

    def test_root_issue_publication_rule_freezes_structure_and_orders_passes(self):
        text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        publication = text.split("## Issue and comment publication", 1)[1]
        publication = publication.split("\n## ", 1)[0]
        for queue in ("{skill}-next", "{skill}-N", "{skill}-wish", "framework-N"):
            self.assertIn(queue, publication)
        ordered = [
            "freeze the required title prefix, body opening and protected evidence inventory",
            "apply `sapheneia-durable-record-shape`",
            "run Imprimatur",
            "apply Vulgate",
            "re-run Imprimatur on the exact publishable bytes",
        ]
        positions = [publication.index(item) for item in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("GitHub does not enforce this repository rule", publication)
        self.assertIn("Do not publish", publication)


if __name__ == "__main__":
    unittest.main()
