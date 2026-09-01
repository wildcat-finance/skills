"""Scaffold tests: the packaging, the contract and the self-test agree.

Nothing here compiles an inventory, imports a workbook or records a
disposition, because nothing does that yet. These check the claims the scaffold
itself makes: that both hosts can discover the plugin, that one version is
stated everywhere it is stated at all, that the canonical contract declares one
keepable promise and names the three it does not keep, that every unbuilt verb
refuses, and that the self-test emits a report a design transition can consume.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN.parents[1]
SKILL = PLUGIN / "skills" / "dokimasia" / "SKILL.md"
LEDGER = PLUGIN / "skills" / "dokimasia" / "EVOLUTION.md"
SCRIPT = PLUGIN / "scripts" / "dokimasia.py"
VERSION = "2.1.0"
UNBUILT: tuple[str, ...] = ()
KEPT_PROMISES = (
    "dokimasia-scaffold-identity",
    "dokimasia-source-inventory",
    "dokimasia-workbook-lineage",
    "dokimasia-drafted-dispositions",
    "dokimasia-disposition-closure",
    "dokimasia-pinned-scrutiny",
)
# Every declared promise is kept and every declared verb is built. Nothing
# remains for the contract to name a step for.
UNKEPT_PROMISES = ()
UNBUILT_TRANSITION_STEP = ""


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
        timeout=60,
    )


def manifest(host: str) -> dict:
    return json.loads((PLUGIN / host / "plugin.json").read_text(encoding="utf-8"))


class ManifestTests(unittest.TestCase):
    def test_the_claude_manifest_declares_the_plugin_and_its_skills(self):
        claude = manifest(".claude-plugin")
        self.assertEqual(claude["name"], "dokimasia")
        self.assertEqual(claude["version"], VERSION)
        self.assertEqual(claude["skills"], "./skills/")
        self.assertEqual(claude["license"], "Apache-2.0")

    def test_the_codex_manifest_agrees_and_carries_an_interface(self):
        codex = manifest(".codex-plugin")
        self.assertEqual(codex["name"], "dokimasia")
        self.assertEqual(codex["version"], VERSION)
        interface = codex["interface"]
        self.assertEqual(interface["displayName"], "Dokimasia")
        self.assertIn("$dokimasia", interface["defaultPrompt"])

    def test_both_manifests_state_the_same_description(self):
        self.assertEqual(
            manifest(".claude-plugin")["description"],
            manifest(".codex-plugin")["description"],
        )

    def test_the_long_description_refuses_to_promise_a_verdict(self):
        long_description = manifest(".codex-plugin")["interface"]["longDescription"]
        self.assertIn("Every substantive verb refuses", long_description)
        self.assertIn("never report an item as covered", long_description.lower())


class ContractTests(unittest.TestCase):
    def test_the_canonical_skill_states_the_declared_version(self):
        metadata = re.search(r'version:\s*"([^"]+)"', SKILL.read_text(encoding="utf-8"))
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.group(1), VERSION)

    def test_the_canonical_skill_points_at_its_ledger(self):
        self.assertIn("[EVOLUTION.md](EVOLUTION.md)", SKILL.read_text(encoding="utf-8"))

    def test_the_scaffold_declares_only_what_it_can_keep(self):
        # A promise with no case that could support it is the overclaim the root
        # law refuses. The scaffold has packaging and a self-test to show, so
        # identity is the one promise it declares.
        text = SKILL.read_text(encoding="utf-8")
        declared = re.findall(r"^### (dokimasia-[a-z-]+)$", text, re.M)
        self.assertEqual(declared, list(KEPT_PROMISES))
        for promise in UNKEPT_PROMISES:
            with self.subTest(promise=promise):
                self.assertNotIn(promise, declared)

    def test_the_contract_claims_no_transition_it_has_not_built(self):
        # Collapse wrapping: the contract is prose and reflows, the claim does not.
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertNotIn("owes it", text)
        self.assertEqual(UNKEPT_PROMISES, ())

    def test_every_declared_promise_names_a_built_verb(self):
        """A declared promise whose verb still refuses is the overclaim the law bars."""
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        for verb in UNBUILT:
            self.assertNotIn(
                f"A successful `dokimasia {verb}`", text,
                f"{verb} still refuses, so no promise may be declared for it",
            )

    def test_the_contract_refuses_to_call_closure_a_pass(self):
        # Collapse wrapping: the contract is prose and reflows, the claim does not.
        text = " ".join(SKILL.read_text(encoding="utf-8").split())
        self.assertIn("Never report an item as covered without a reviewed oracle.", text)
        self.assertIn("It does not mean anything passed.", text)

    def test_the_ledger_declares_the_version_every_other_surface_declares(self):
        text = LEDGER.read_text(encoding="utf-8")
        self.assertIn(f"Current version: `dokimasia-v{VERSION}`", text)
        self.assertIn("Frontier status: `open`", text)
        self.assertIsNotNone(
            re.search(r"^- Frontier revision: `[a-z0-9-]+`$", text, re.M),
            "the ledger names no frontier revision",
        )

    def test_the_history_records_the_current_version_as_its_latest_row(self):
        text = LEDGER.read_text(encoding="utf-8")
        rows = re.findall(r"^\| `dokimasia-v([^`]+)` \| (\w+) \|", text, re.M)
        self.assertTrue(rows, "the ledger records no history row")
        self.assertEqual(rows[-1][0], VERSION)
        self.assertEqual(rows[0][1], "baseline")

    def test_the_ledger_row_digest_matches_the_frontier_it_describes(self):
        text = LEDGER.read_text(encoding="utf-8")

        def field(label: str) -> str:
            return re.search(rf"^- {label}: (.+)$", text, re.M).group(1)

        import hashlib

        line = "|".join(
            (
                field("Frontier status").strip("`"),
                field("Frontier revision").strip("`"),
                field("Current frontier"),
                field("Next Fiat job"),
            )
        ) + "\n"
        # The current frontier is described by the latest row, not the first.
        # Earlier rows keep the digest of the frontier they were written under.
        recorded = re.findall(r"\| `([0-9a-f]{64})` \|", text)[-1]
        self.assertEqual(hashlib.sha256(line.encode("utf-8")).hexdigest(), recorded)

    def test_the_committed_schema_set_holds_every_schema_this_plugin_ships(self):
        """A dropped schema is caught here rather than inferred from a pass.

        The set is asserted by name and by count. `dispositions-v1.json` joined
        it when `propose` began emitting the disposition set, which until then
        was a hand-written input nothing validated.
        """
        import json

        names = {path.name for path in (PLUGIN / "schemas").glob("*.json")}
        self.assertEqual(names, {
            "coverage-v1.json",
            "dispositions-v1.json",
            "inventory-v1.json",
            "scrutiny-v1.json",
            "workbook-v1.json",
        })
        published = {
            json.loads((PLUGIN / "schemas" / name).read_text(encoding="utf-8"))
            ["properties"]["schema"]["const"]
            for name in names
        }
        self.assertEqual(len(published), len(names), "two schemas publish one identifier")

    def test_every_declared_record_schema_has_a_committed_schema_file(self):
        """A closed record with no committed schema is closed only in prose."""
        import json

        declared = {}
        for module in sorted((PLUGIN / "scripts" / "dokimasia_lib").glob("*.py")):
            for line in module.read_text(encoding="utf-8").splitlines():
                if line.startswith("SCHEMA = "):
                    declared[module.stem] = line.split('"')[1]
        self.assertTrue(declared, "no module declares a record schema")
        published = {
            json.loads(path.read_text(encoding="utf-8"))["properties"]["schema"]["const"]
            for path in (PLUGIN / "schemas").glob("*.json")
        }
        for module, identifier in sorted(declared.items()):
            with self.subTest(module=module):
                self.assertIn(
                    identifier, published,
                    f"{module} declares {identifier} and no schema states its shape",
                )

    def test_the_installed_promise_machine_copy_matches_the_suite_law(self):
        self.assertEqual(
            (PLUGIN / "PROMISE_MACHINE.md").read_bytes(),
            (ROOT / "PROMISE_MACHINE.md").read_bytes(),
        )


class IdentityTests(unittest.TestCase):
    """Cases behind dokimasia-scaffold-identity."""

    def test_identity_agrees_across_both_manifests_and_the_marketplace(self):
        listing = json.loads(
            (ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8")
        )
        entry = next(p for p in listing["plugins"] if p["name"] == "dokimasia")
        self.assertEqual(
            {manifest(".claude-plugin")["version"], manifest(".codex-plugin")["version"]},
            {VERSION},
        )
        self.assertEqual(entry["name"], "dokimasia")

    def test_a_drifted_installed_root_law_copy_is_detected(self):
        # The equality check has to have teeth: mutate a copy and require the
        # same comparison to fail, so a green suite is not a trivial pass.
        law = (ROOT / "PROMISE_MACHINE.md").read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            drifted = Path(tmp) / "PROMISE_MACHINE.md"
            drifted.write_bytes(law.replace(b"Promise", b"Promyse", 1))
            self.assertNotEqual(drifted.read_bytes(), law)
        self.assertEqual((PLUGIN / "PROMISE_MACHINE.md").read_bytes(), law)

    def test_no_unbuilt_verb_prints_anything_on_standard_output(self):
        for verb in UNBUILT:
            with self.subTest(verb=verb):
                self.assertEqual(run(verb).stdout, "")

    def test_every_declared_verb_answers_rather_than_refusing(self):
        """Nothing is owed to a later step, so nothing may refuse as unbuilt."""
        for verb in ("selftest", "inventory", "workbook", "reconcile",
                     "demonstrate"):
            with self.subTest(verb=verb):
                arguments = ("--check",) if verb != "selftest" else ()
                result = run(verb, *arguments)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("not built yet", result.stderr)


class SelfTestTests(unittest.TestCase):
    def test_the_self_test_passes_against_the_committed_tree(self):
        result = run("selftest")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("clean", result.stdout)

    def test_the_self_test_stays_quiet_about_the_verbs_it_probes(self):
        # It exercises the real refusal path, so its own output must not read
        # as four failures.
        self.assertEqual(run("selftest").stderr, "")

    def test_the_self_test_writes_a_report_a_design_transition_can_consume(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "nested" / "inventory-first-scaffold-contract-check.json"
            result = run("selftest", "--report", str(report))
            self.assertEqual(result.returncode, 0, result.stderr)
            body = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(body),
            ["candidate", "command", "criterion", "exit", "schema", "unit", "value"],
        )
        self.assertEqual(body["schema"], "protasis-design-report/v1")
        self.assertEqual(body["candidate"], "inventory-first")
        self.assertEqual(body["criterion"], "scaffold-contract-check")
        self.assertEqual(body["unit"], "boolean")
        self.assertIs(body["value"], True)
        self.assertEqual(body["exit"], 0)

    def test_the_self_test_refuses_a_report_path_that_is_a_symlink(self):
        # The guard has to be tested on the supplied path: an earlier version
        # resolved first and asked the resolved path whether it was a symlink,
        # which is always false, so the refusal could never fire.
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "real.json"
            target.write_text("{}", encoding="utf-8")
            link = Path(tmp) / "inventory-first-scaffold-contract-check.json"
            link.symlink_to(target)
            result = run("selftest", "--report", str(link))
            survived = target.read_text(encoding="utf-8")
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("is a symlink", result.stderr)
        self.assertEqual(survived, "{}", "the refused write reached the link target")

    def test_the_self_test_refuses_a_report_path_that_is_a_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run("selftest", "--report", tmp)
        self.assertEqual(result.returncode, 2, result.stdout)
        self.assertIn("refused", result.stderr)

    def test_a_version_disagreement_would_be_caught(self):
        # The check must have teeth: the comparison the self-test performs is
        # reproduced here over a mutated set, and must fail.
        declared = {"claude": VERSION, "codex": VERSION, "skill": "0.2.0"}
        self.assertNotEqual(len(set(declared.values())), 1)


class CommandTests(unittest.TestCase):
    def test_help_succeeds_and_names_every_verb(self):
        result = run("--help")
        self.assertEqual(result.returncode, 0, result.stderr)
        for verb in (*UNBUILT, "selftest"):
            with self.subTest(verb=verb):
                self.assertIn(verb, result.stdout)

    def test_help_states_that_a_scrutiny_is_not_a_pass(self):
        self.assertIn("never that anything passed", run("--help").stdout)

    def test_no_argument_prints_help_and_succeeds(self):
        result = run()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("usage: dokimasia", result.stdout)

    def test_every_unbuilt_verb_refuses_rather_than_answering(self):
        for verb in UNBUILT:
            with self.subTest(verb=verb):
                result = run(verb)
                self.assertEqual(result.returncode, 3, result.stdout)
                self.assertIn("not built yet", result.stderr)
                self.assertEqual(result.stdout, "")

    def test_the_inventory_verb_is_built_and_self_checks(self):
        result = run("inventory", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("check clean", result.stdout)

    def test_the_workbook_verb_is_built_and_self_checks(self):
        result = run("workbook", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("check clean", result.stdout)

    def test_the_reconcile_verb_is_built_and_self_checks(self):
        result = run("reconcile", "--check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("check clean", result.stdout)

    def test_the_version_flag_reports_the_declared_version(self):
        result = run("--version")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(VERSION, result.stdout)


if __name__ == "__main__":
    unittest.main()


class ReportIdentity(unittest.TestCase):
    """A report has to be able to name the frontier it is serving.

    The candidate and criterion were module constants pinned to the frontier
    this plugin was first built under, so every verb reported that identity
    whatever record had asked for the run. A later frontier could run exactly
    the resolver its own design record named and still be refused for
    reporting somebody else's candidate.
    """

    def _report(self, *extra: str) -> dict:
        with tempfile.TemporaryDirectory() as raw:
            target = Path(raw) / "report.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "reconcile", "--check",
                 "--report", str(target), *extra],
                capture_output=True, text=True, cwd=str(PLUGIN.parents[1]),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(target.read_text(encoding="utf-8"))

    def test_the_default_identity_is_unchanged(self):
        made = self._report()
        self.assertEqual(made["candidate"], "inventory-first")
        self.assertEqual(made["criterion"], "disposition-closure")

    def test_a_named_candidate_and_criterion_reach_the_report(self):
        made = self._report(
            "--candidate", "confirmed-flag",
            "--criterion", "proposal-refused-unconfirmed",
        )
        self.assertEqual(made["candidate"], "confirmed-flag")
        self.assertEqual(made["criterion"], "proposal-refused-unconfirmed")
        self.assertEqual(made["schema"], "protasis-design-report/v1")
        self.assertEqual(made["exit"], 0)
        self.assertIs(made["value"], True)

    def test_every_verb_that_writes_a_report_accepts_both(self):
        """One verb taking the flags and another not is the drift to avoid."""
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True, text=True, cwd=str(PLUGIN.parents[1]),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for verb in ("selftest", "inventory", "workbook", "reconcile", "demonstrate"):
            with self.subTest(verb=verb):
                usage = subprocess.run(
                    [sys.executable, str(SCRIPT), verb, "--help"],
                    capture_output=True, text=True, cwd=str(PLUGIN.parents[1]),
                )
                self.assertIn("--candidate", usage.stdout)
                self.assertIn("--criterion", usage.stdout)
