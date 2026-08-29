"""The Alexandria scaffold is portable and makes no operational claim."""

import json
from pathlib import Path
import re
import subprocess
import sys
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
sys.path.insert(0, str(REPO_ROOT))
from repo_contract import (
    assert_version_agreement,
    assert_router_reaches,
    assert_marketplace_source_path,
)

COMMAND = PLUGIN_ROOT / "scripts" / "alexandria.py"
COMPOUND_COMMAND = PLUGIN_ROOT / "scripts" / "compound_v3_phase0.py"
SKILL = PLUGIN_ROOT / "skills" / "alexandria" / "SKILL.md"
PLANNED = ("ingest", "verify", "statement", "derive", "index", "query")


def run(*args):
    return subprocess.run(
        [sys.executable, str(COMMAND), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class AlexandriaScaffoldTests(unittest.TestCase):
    def test_help_names_every_planned_operation(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("offline lending-data archive", result.stdout)
        for command in PLANNED:
            with self.subTest(command=command):
                self.assertIn(command, result.stdout)

    def test_compound_phase0_cli_keeps_network_capture_explicit(self):
        result = subprocess.run(
            [sys.executable, str(COMPOUND_COMMAND), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for command in ("registry", "capture", "build", "check"):
            self.assertIn(command, result.stdout)

    def test_no_command_is_a_controlled_usage_error(self):
        result = run()
        self.assertEqual(result.returncode, 2)
        self.assertIn("usage:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_subcommand_help_succeeds_without_running_an_operation(self):
        for command in PLANNED:
            with self.subTest(command=command):
                result = run(command, "--help")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout)
                self.assertNotIn("not implemented", result.stderr)

    def test_implemented_operations_require_their_inputs(self):
        for command in (
            "ingest",
            "verify",
            "statement",
            "derive",
            "index",
            "query",
        ):
            with self.subTest(command=command):
                result = run(command)
                self.assertEqual(result.returncode, 2)
                self.assertIn("required", result.stderr)

    def test_unknown_operation_is_a_controlled_parser_error(self):
        result = run("harvest")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_skill_is_canonical_and_has_no_browsable_readme_shadow(self):
        self.assertTrue(SKILL.is_file())
        self.assertFalse((SKILL.parent / "README.md").exists())

    def test_skill_frontmatter_matches_its_directory(self):
        text = SKILL.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        match = re.search(r"(?m)^name:\s*([^\n]+)$", text)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1).strip(), SKILL.parent.name)
        self.assertIn("Raw release and registered", text)
        self.assertIn("unsigned in-toto release statements", text)

    def test_package_metadata_agrees_and_points_at_the_skill(self):
        assert_version_agreement(self, "alexandria")
        manifests = [
            json.loads((PLUGIN_ROOT / host / "plugin.json").read_text(encoding="utf-8"))
            for host in (".claude-plugin", ".codex-plugin")
        ]
        self.assertEqual([item["name"] for item in manifests], ["alexandria"] * 2)
        self.assertEqual([item["skills"] for item in manifests], ["./skills/"] * 2)
        self.assertTrue(SKILL.is_file())

    def test_promise_machine_router_resolves_to_runtime_contract(self):
        assert_router_reaches(self, "alexandria")

    def test_marketplaces_use_the_local_plugin_path(self):
        assert_marketplace_source_path(self, "alexandria")

    def test_design_records_are_committed(self):
        study = (PLUGIN_ROOT / "docs" / "study.md").read_text(encoding="utf-8")
        runbook = (PLUGIN_ROOT / "docs" / "runbook.md").read_text(encoding="utf-8")
        statement_study = (
            PLUGIN_ROOT / "docs" / "release-statement-study.md"
        ).read_text(encoding="utf-8")
        statement_runbook = (
            PLUGIN_ROOT / "docs" / "release-statement-runbook.md"
        ).read_text(encoding="utf-8")
        statement_document = (
            PLUGIN_ROOT / "docs" / "release-statements.md"
        ).read_text(encoding="utf-8")
        self.assertTrue(study.startswith("# Alexandria study\n"))
        self.assertTrue(runbook.startswith("# Alexandria implementation runbook\n"))
        self.assertEqual(runbook.count("## Step "), 5)
        self.assertIn("83fef6634a560860b930a532861dbfff8cbb3442", runbook)
        self.assertTrue(
            statement_study.startswith("# Alexandria release-statement study\n")
        )
        self.assertTrue(
            statement_runbook.startswith(
                "# Runbook: emit an Ariadne-ready Alexandria release statement\n"
            )
        )
        self.assertIn("### Amendment -- 2026-08-26", statement_runbook)
        self.assertTrue(
            statement_document.startswith("# Alexandria release statements\n")
        )

    def test_scaffold_directories_and_licence_are_present(self):
        for relative in (
            "schemas",
            "examples",
            "docs",
            "scripts/alexandria_lib",
            "skills/alexandria/agents",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((PLUGIN_ROOT / relative).is_dir())
        licence = (PLUGIN_ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", licence)
        self.assertIn("Copyright 2026 Wildcat Labs", licence)

    def test_all_plugin_json_files_parse(self):
        paths = list(PLUGIN_ROOT.rglob("*.json"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            with self.subTest(path=path):
                json.loads(path.read_text(encoding="utf-8"))

    def test_tabularium_schema_defines_mapping_coverage_and_counts(self):
        schema = json.loads(
            (PLUGIN_ROOT / "schemas" / "tabularium-view-v1.schema.json").read_text()
        )
        self.assertEqual(
            schema["properties"]["mappings"]["items"],
            {"$ref": "#/$defs/mapping"},
        )
        self.assertEqual(
            schema["properties"]["counts"],
            {"$ref": "#/$defs/counts"},
        )
        self.assertFalse(schema["$defs"]["mapping"]["additionalProperties"])
        self.assertFalse(schema["$defs"]["counts"]["additionalProperties"])


if __name__ == "__main__":
    unittest.main()
