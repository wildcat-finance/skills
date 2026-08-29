"""Complete offline Alexandria demonstration tests."""

import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
EXAMPLE = PLUGIN_ROOT / "examples" / "credit-history-v0"
DRIVER = EXAMPLE / "demo.py"


def load_demo():
    specification = importlib.util.spec_from_file_location("alexandria_demo_tests", DRIVER)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


demo = load_demo()


def _restore_cleanup_modes(root: Path) -> None:
    """Make a fixture tree removable without following a link out of it.

    ``Path.chmod`` dereferences symlinks, so scrubbing a tree that holds a
    test-planted link to a repository file would rewrite that file's mode
    outside the sandbox.  A symlink needs no mode change to be unlinked, so
    links are left untouched.
    """
    for path in root.rglob("*"):
        try:
            if path.is_symlink():
                continue
            path.chmod(0o700 if path.is_dir() else 0o600)
        except FileNotFoundError:
            pass


class DemoTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.output = self.root / "demo"

    def tearDown(self):
        _restore_cleanup_modes(self.root)
        self.temporary.cleanup()

    def build(self):
        return demo.build_demo(self.output)

    def manifest(self):
        return json.loads((self.output / "derived-release" / "manifest.json").read_text())


class DemoBuildTests(DemoTestCase):
    def test_clean_machine_command_runs_outside_repository(self):
        environment = os.environ.copy()
        environment.pop("PYTHONPATH", None)
        environment.pop("PYTHONHOME", None)
        result = subprocess.run(
            [sys.executable, str(DRIVER), "build", "--output", str(self.output)],
            cwd=self.root, env=environment, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^sha256:[0-9a-f]{64}\n$")

    def test_documented_build_and_verify_commands_run_exactly(self):
        for arguments in (
            ["build", "--output", str(self.output)],
            ["verify", str(self.output)],
        ):
            result = subprocess.run(
                [sys.executable, str(DRIVER), *arguments],
                cwd=REPO_ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_build_refuses_existing_output(self):
        self.output.mkdir()
        with self.assertRaisesRegex(demo.AlexandriaError, "must not already exist"):
            self.build()

    def test_exact_derived_and_mapping_counts(self):
        self.build()
        derivation = self.manifest()["derivation"]
        self.assertEqual(derivation["counts"]["event_rows"], 522)
        self.assertEqual(derivation["counts"]["observation_rows"], 31)
        mappings = {item["adapter"]: item for item in derivation["mappings"]}
        self.assertEqual(mappings["clearpool"]["coverage"]["mapped_records"], 11)
        self.assertEqual(mappings["clearpool"]["coverage"]["context_records"], 1)
        self.assertEqual(mappings["goldfinch"]["coverage"]["mapped_records"], 542)
        self.assertEqual(mappings["goldfinch"]["coverage"]["unsupported_records"], 25)

    def test_exact_query_and_probitas_counts(self):
        summary = self.build()
        self.assertEqual(summary["query"]["events"], {"clearpool": 11})
        self.assertEqual(summary["query"]["observations"], {})
        self.assertEqual(summary["query"]["coverage"], {
            "clearpool": "covered", "goldfinch": "partial",
        })
        self.assertEqual(summary["probitas"]["records"], 11)
        self.assertEqual(summary["probitas"]["coverage"], {
            "checked": 1, "error": 1, "unconfigured": 5, "unimplemented": 8,
        })
        self.assertEqual(len(summary["probitas"]["gate_lines"]), 5)
        self.assertTrue(all("pass" in line for line in summary["probitas"]["gate_lines"]))

    def test_two_builds_have_identical_truth_and_logical_index(self):
        one = self.build()
        other = self.root / "other"
        two = demo.build_demo(other)
        self.assertEqual(one["release_truth"], two["release_truth"])
        self.assertEqual(one["index_logical_digest"], two["index_logical_digest"])
        for directory, files in one["release_truth"].items():
            for name in files:
                self.assertEqual(
                    (self.output / directory / name).read_bytes(),
                    (other / directory / name).read_bytes(),
                )
        for name in ("query.json", "evidence.json", "dossier.md", "summary.json"):
            self.assertEqual((self.output / name).read_bytes(), (other / name).read_bytes())

    def test_example_does_not_duplicate_source_bytes(self):
        for source in (
            REPO_ROOT / "plugins/tabularium/examples/goldfinch-v0/source.json",
            EXAMPLE / "sources/clearpool.json",
        ):
            self.assertFalse(any(
                path.is_file() and path != source and path.read_bytes() == source.read_bytes()
                for path in EXAMPLE.iterdir()
            ))


class DemoVerificationTests(DemoTestCase):
    def test_read_only_network_disabled_verify_changes_no_demo_file(self):
        self.build()
        before = {str(path.relative_to(self.output)): (path.read_bytes(), path.stat().st_mtime_ns)
                  for path in self.output.rglob("*") if path.is_file()}
        for path in sorted(self.output.rglob("*"), reverse=True):
            path.chmod(0o555 if path.is_dir() else 0o444)
        self.output.chmod(0o555)
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            demo.verify_demo(self.output)
        after = {str(path.relative_to(self.output)): (path.read_bytes(), path.stat().st_mtime_ns)
                 for path in self.output.rglob("*") if path.is_file()}
        self.assertEqual(before, after)

    def test_source_pin_tamper_fails_before_ingest(self):
        tampered = self.root / "goldfinch.json"
        source = REPO_ROOT / "plugins/tabularium/examples/goldfinch-v0/source.json"
        tampered.write_bytes(source.read_bytes() + b" ")
        with self.assertRaisesRegex(demo.AlexandriaError, "digest does not match its pin"):
            demo.build_demo(
                self.output, check_expected=False,
                source_paths={"goldfinch-source": tampered},
            )
        self.assertFalse(self.output.exists())

    def test_materialized_source_symlink_is_refused(self):
        self.build()
        path = self.output / "inputs" / "goldfinch.json"
        path.unlink()
        path.symlink_to(
            REPO_ROOT / "plugins/tabularium/examples/goldfinch-v0/source.json"
        )
        with self.assertRaisesRegex(demo.AlexandriaError, "symlink"):
            demo.verify_demo(self.output)

    def test_cleanup_does_not_follow_a_planted_symlink_out_of_the_sandbox(self):
        """The scrub that makes fixtures removable must not chmod through a link.

        The symlink-refusal case above plants a link at a repository file; a
        dereferencing chmod during teardown then rewrites that file's mode
        outside the sandbox, which the check runner's shared-snapshot source
        verification reports as a mutated source.
        """
        victim = self.root / "victim.json"
        victim.write_text("{}\n", encoding="utf-8")
        victim.chmod(0o644)
        sandbox = self.root / "sandbox"
        sandbox.mkdir()
        (sandbox / "escape.json").symlink_to(victim)
        _restore_cleanup_modes(sandbox)
        self.assertEqual(
            victim.stat().st_mode & 0o777, 0o644,
            "fixture cleanup escaped its sandbox through a planted symlink",
        )

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO support required")
    def test_materialized_capture_plan_fifo_is_refused(self):
        self.build()
        path = self.output / "inputs" / "capture-plan.json"
        path.unlink()
        os.mkfifo(path)
        with self.assertRaisesRegex(demo.AlexandriaError, "regular file"):
            demo.verify_demo(self.output)

    def test_raw_object_tamper_fails_at_raw_verification(self):
        self.build()
        path = next((self.output / "raw-release" / "objects").rglob("*"))
        while not path.is_file():
            path = next(item for item in path.rglob("*") if item.is_file())
        path.write_bytes(path.read_bytes() + b"x")
        with self.assertRaisesRegex(demo.AlexandriaError, "byte count does not match"):
            demo.verify_demo(self.output)

    def test_raw_manifest_tamper_fails_at_manifest_identity(self):
        self.build()
        path = self.output / "raw-release" / "manifest.json"
        value = json.loads(path.read_text())
        value["release"]["name"] = "changed"
        path.write_bytes(demo.canonical_bytes(value))
        with self.assertRaisesRegex(demo.AlexandriaError, "identity does not match"):
            demo.verify_demo(self.output)

    def test_derived_row_tamper_fails_at_derived_digest(self):
        self.build()
        path = self.output / "derived-release" / "credit-events.jsonl"
        path.write_bytes(path.read_bytes().replace(b'"borrowing"', b'"repayment"', 1))
        with self.assertRaisesRegex(demo.AlexandriaError, "digest does not match"):
            demo.verify_demo(self.output)

    def test_coverage_tamper_fails_at_release_identity(self):
        self.build()
        path = self.output / "derived-release" / "manifest.json"
        value = json.loads(path.read_text())
        value["captures"][0]["coverage"]["status"] = "partial"
        path.write_bytes(demo.canonical_bytes(value))
        with self.assertRaisesRegex(demo.AlexandriaError, "partial coverage must name"):
            demo.verify_demo(self.output)

    def test_query_provenance_tamper_fails_at_query_boundary(self):
        self.build()
        path = self.output / "query.json"
        value = json.loads(path.read_text())
        value["events"][0]["release_id"] = "sha256:" + "0" * 64
        path.write_bytes(demo.canonical_bytes(value))
        with self.assertRaisesRegex(demo.AlexandriaError, "query output does not rebuild"):
            demo.verify_demo(self.output)

    def test_index_provenance_tamper_fails_before_query(self):
        self.build()
        database = self.output / "alexandria.sqlite"
        connection = sqlite3.connect(database)
        connection.execute(
            "UPDATE credit_events SET capture_id = 'changed' WHERE row_id = "
            "(SELECT MIN(row_id) FROM credit_events)"
        )
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(demo.AlexandriaError, "logical digest does not match"):
            demo.verify_demo(self.output)

    def test_summary_cannot_supply_its_own_index_digest(self):
        self.build()
        path = self.output / "summary.json"
        value = json.loads(path.read_text())
        value["index_logical_digest"] = "sha256:" + "0" * 64
        path.write_bytes(demo.canonical_bytes(value))
        with self.assertRaisesRegex(demo.AlexandriaError, "summary does not rebuild"):
            demo.verify_demo(self.output)

    def test_cli_failure_is_controlled(self):
        result = subprocess.run(
            [sys.executable, str(DRIVER), "verify", str(self.output)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("alexandria-demo:", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


class DemoDocumentationTests(unittest.TestCase):
    def test_data_dictionary_states_the_stable_row_identity_boundary(self):
        dictionary = (PLUGIN_ROOT / "docs/data-dictionary.md").read_text()
        self.assertIn("stable native identity, row kind and mapping rule", dictionary)
        self.assertIn("Economic row content is checked separately", dictionary)

    def test_compound_plan_does_not_treat_logs_as_complete_credit_history(self):
        plan = " ".join(
            (PLUGIN_ROOT / "docs/compound-v3-harvest.md").read_text().split()
        )
        for required in (
            "without a topic filter",
            "unknown topics as raw records",
            "every transaction in each block",
            "direct or internal calls to the proxy",
            "ordered call trace",
            "pre-transaction storage",
            "debt-only transfer has no corresponding",
            "affected transaction unsupported",
        ):
            with self.subTest(required=required):
                self.assertIn(required, plan)

    def test_all_changed_local_markdown_links_resolve(self):
        import re
        documents = [
            REPO_ROOT / "README.md",
            PLUGIN_ROOT / "README.md",
            PLUGIN_ROOT / "docs/compound-v3-harvest.md",
            PLUGIN_ROOT / "docs/data-dictionary.md",
            PLUGIN_ROOT / "examples/README.md",
            EXAMPLE / "README.md",
            PLUGIN_ROOT / "skills/alexandria/SKILL.md",
            REPO_ROOT / "plugins/probitas/skills/probitas/SKILL.md",
        ]
        for document in documents:
            for target in re.findall(r"\[[^]]+\]\(([^)]+)\)", document.read_text()):
                if "://" in target or target.startswith("#") or target.startswith("$"):
                    continue
                path = (document.parent / target.split("#", 1)[0]).resolve()
                self.assertTrue(path.exists(), f"{document}: missing {target}")

    def test_demo_json_documents_parse(self):
        for path in EXAMPLE.glob("*.json"):
            with self.subTest(path=path.name):
                json.loads(path.read_text())


if __name__ == "__main__":
    unittest.main()
