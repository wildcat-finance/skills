"""Historical guard for issue 453's missing inoculation transition."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

try:
    from .test_hexctl import HexctlCase
except ImportError:
    from test_hexctl import HexctlCase


class InoculationLifecycleTests(HexctlCase):
    def test_kf_453_02_inoculation_precedes_implementation(self):
        self.init()

        source_path = "audit/rounds/source.md"
        source = "fixture audit source\n"
        source_sha256 = hashlib.sha256(source.encode()).hexdigest()
        view_path = "audit/rounds/source.synopsis.md"
        view = (
            "Synopsis schema=fiat-audit-synopsis/v1 | "
            f"source={source_path} | source_sha256={source_sha256} | h2_count=0\n"
        )
        view_sha256 = hashlib.sha256(view.encode()).hexdigest()
        self.write(source_path, source)
        self.write(view_path, view)

        checked_views = [
            {
                "id": "fixture-audit",
                "source_sha256": source_sha256,
                "view_sha256": view_sha256,
            }
        ]
        inventory = {
            "schema": "protasis-known-failure-inventory/v1",
            "source_views": [
                {
                    "id": "fixture-audit",
                    "path": view_path,
                    "source_sha256": source_sha256,
                    "view_sha256": view_sha256,
                }
            ],
            "findings": [],
            "no_known_findings": {
                "source_views": checked_views,
                "consuming_step": 1,
                "surveyor_assertion": "no-known-findings",
            },
        }
        study = self.write(
            "study.md",
            "# Study\n\n```known-failure-inventory\n"
            + json.dumps(inventory, indent=2)
            + "\n```\n",
        )
        self.run_ctl("done", "study", "--artifact", study)
        runbook = self.write(
            "runbook.md",
            "# Runbook\n\n"
            "## Step 1: Guarded step\n\n"
            "**Goal.** Exercise the pre-implementation transition.\n",
        )
        steps = self.write("steps.json", '["Guarded step"]')
        self.run_ctl(
            "done", "runbook", "--artifact", runbook, "--steps-file", steps
        )

        directive = self.next_json()
        self.assertEqual("inoculate", directive["do"])

        controller_root = Path(self.target, ".hexaemeron")
        before = tuple(
            Path(controller_root, name).read_bytes()
            for name in ("state.json", "ledger.jsonl")
        )
        self.run_ctl(
            "done",
            "implement",
            "--branch",
            self.step_branch(1),
            "--commit",
            "guard-head",
            expect=2,
        )
        after = tuple(
            Path(controller_root, name).read_bytes()
            for name in ("state.json", "ledger.jsonl")
        )
        self.assertEqual(before, after)
