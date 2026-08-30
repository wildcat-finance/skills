"""Scaffold checks for wildcat-agent-instruction/v1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "docs/compact-agent-instruction-language/study.md"
RUNBOOK = ROOT / "docs/compact-agent-instruction-language/runbook.md"
CONTRACT = ROOT / "docs/agent-instruction-language-v1.md"
SCHEMA = ROOT / "schemas/agent-instruction-v1.schema.json"
SCRIPT = ROOT / "scripts/agent_instruction.py"
FIXTURE_README = ROOT / "tests/fixtures/agent-instruction-v1/README.md"

STUDY_SHA256 = "28c3319301ea86e91bc872d1b803fc1b7e00b9b5a9826c2b0e990d2f7d7f64aa"
RUNBOOK_SHA256 = "dd5c41a647f7119ae16db67b059ce4cf4e3fdebe5e7a27b7e9faa5019c88a93b"
SCHEMA_ID = "wildcat-agent-instruction/v1"
MAGIC = "WAI1"
FIXTURE_IDS = (
    "promise-machine-router-selection",
    "fiat-study-runbook-phase",
    "horos-boundary-check",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_script():
    spec = importlib.util.spec_from_file_location("agent_instruction", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentInstructionScaffoldTests(unittest.TestCase):
    def test_study_copy_matches_receipted_digest(self):
        self.assertEqual(sha256(STUDY), STUDY_SHA256)

    def test_runbook_copy_matches_receipted_digest(self):
        self.assertEqual(sha256(RUNBOOK), RUNBOOK_SHA256)

    def test_schema_loads_as_closed_json_object(self):
        document = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(document["type"], "object")
        self.assertFalse(document["additionalProperties"])
        self.assertEqual(
            set(document["required"]),
            {"schema", "document", "sources", "sections", "relations", "bindings"},
        )

    def test_schema_freezes_version_and_directive_vocabulary(self):
        document = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(document["properties"]["schema"]["const"], SCHEMA_ID)
        self.assertEqual(
            document["$defs"]["directive"]["properties"]["kind"]["enum"],
            ["require", "forbid", "permit", "refuse", "recover", "unknown"],
        )

    def test_schema_promise_carries_the_governed_claim(self):
        document = json.loads(SCHEMA.read_text(encoding="utf-8"))
        promise = document["$defs"]["promise"]
        self.assertIn("claim", promise["required"])
        self.assertEqual(promise["properties"]["claim"], {"$ref": "#/$defs/literal"})

    def test_script_freezes_version_magic(self):
        module = load_script()
        self.assertEqual(module.SCHEMA_ID, SCHEMA_ID)
        self.assertEqual(module.MAGIC, MAGIC)

    def test_cli_help_links_contract_and_schema(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("docs/agent-instruction-language-v1.md", result.stdout)
        self.assertIn("schemas/agent-instruction-v1.schema.json", result.stdout)

    def test_fixture_layout_sentinel_names_exact_corpus(self):
        text = FIXTURE_README.read_text(encoding="utf-8")
        entries = tuple(
            line.removeprefix("- `").removesuffix("`")
            for line in text.splitlines()
            if line.startswith("- `") and line.endswith("`")
        )
        self.assertEqual(entries, FIXTURE_IDS)

    def test_horos_boundary_is_current_for_the_scaffold(self):
        from tests.test_boundary_currency import drifted_paths

        self.assertEqual(drifted_paths(ROOT), [])

    def test_existing_repository_licence_is_apache_2(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)

    def test_existing_python_pin_matches_project_minor(self):
        self.assertEqual((ROOT / ".python-version").read_text().strip(), "3.14.6")
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('requires-python = "==3.14.*"', project)

    def test_contract_cites_existing_licence_and_python_pin(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("[Apache-2.0 licence](../LICENSE)", text)
        self.assertIn("[`.python-version`](../.python-version)", text)
        self.assertNotIn("TERMS AND CONDITIONS FOR USE", text)


if __name__ == "__main__":
    unittest.main()
