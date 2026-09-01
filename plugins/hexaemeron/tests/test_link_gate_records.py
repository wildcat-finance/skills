"""Step 1: the committed design record says what the run decided, and both
committed documents already obey the rule the run is about to enforce."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import unittest


PLUGIN_ROOT = Path(__file__).resolve(strict=True).parents[1]
GATE = PLUGIN_ROOT / "docs/link-gate"
RECORD = GATE / "design-evidence.json"
DOCUMENTS = (
    PLUGIN_ROOT / "docs/link-gate-study.md",
    PLUGIN_ROOT / "docs/link-gate-runbook.md",
)

CONCERNS = {"correctness", "time", "space", "compatibility", "recovery"}
MARKDOWN_LINK = re.compile(r"\]\(([^)]+)\)")


class CommittedDesignRecord(unittest.TestCase):
    def setUp(self) -> None:
        self.record = json.loads(RECORD.read_text(encoding="utf-8"))

    def test_the_record_declares_the_protasis_schema(self) -> None:
        self.assertEqual(self.record["schema"], "protasis-design-evidence/v1")

    def test_three_candidates_and_every_concern_is_covered(self) -> None:
        self.assertEqual(len(self.record["candidates"]), 3)
        self.assertEqual(
            {c["concern"] for c in self.record["criteria"]}, CONCERNS
        )

    def test_selection_is_location_independence_on_a_unique_frontier(self) -> None:
        selection = self.record["selection"]
        self.assertEqual(selection["candidate"], "require-location-independent")
        self.assertEqual(selection["rule"], "unique-frontier")
        failed = {
            r["candidate"] for r in self.record["results"] if r["state"] == "fail"
        }
        self.assertEqual(failed, {"lint-in-place", "declare-only"})

    def test_every_cell_names_a_report_whose_bytes_match_its_digest(self) -> None:
        self.assertEqual(len(self.record["results"]), 18)
        for result in self.record["results"]:
            report = result["report"]
            path = GATE / report["path"]
            with self.subTest(report=report["path"]):
                self.assertTrue(path.is_file(), f"missing report {report['path']}")
                body = path.read_bytes()
                self.assertEqual(hashlib.sha256(body).hexdigest(), report["sha256"])
                document = json.loads(body)
                self.assertEqual(document["schema"], "protasis-design-report/v1")
                self.assertEqual(document["exit"], 0)


class CommittedDocumentsObeyTheRuleTheyPropose(unittest.TestCase):
    def test_no_committed_document_links_relative_to_its_own_file(self) -> None:
        for path in DOCUMENTS:
            # Not a skip: a renamed document must fail here rather than drop out.
            self.assertTrue(path.is_file(), f"{path} is named here but absent")
            targets = MARKDOWN_LINK.findall(path.read_text(encoding="utf-8"))
            self.assertTrue(targets, f"{path.name} carries no links to check")
            relative = [t for t in targets if not t.startswith(("http://", "https://", "/"))]
            self.assertEqual(
                relative, [], f"{path.name} carries file-relative link(s): {relative}"
            )


if __name__ == "__main__":
    unittest.main()
