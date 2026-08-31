import json
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "promise_machine.py"
LAW = ROOT / "PROMISE_MACHINE.md"
LICENSE = ROOT / "LICENSE"
FIXTURE = ROOT / "tests" / "fixtures" / "promise-machine" / "divergent-copy"
FIXTURES = ROOT / "tests" / "fixtures" / "promise-machine"
PROMISE_FIELDS = (
    "Promise",
    "Evidence",
    "Evidence classes",
    "Boundary",
    "Authorises",
    "Consequence",
    "Refuses",
    "Recovery",
    "Exceptions",
)


def discovered_plugins():
    """Count what ships rather than what a literal here remembers.

    Every count below used to be written in by hand, so a new plugin landed
    with these cases passing while none of them had looked at it. Deriving the
    expectations from disk and from the coverage ledger turns that omission
    back into a failure.
    """
    return sorted(
        path.parent.parent.name
        for path in (ROOT / "plugins").glob("*/.claude-plugin/plugin.json")
    )


def discovered_canonical_skills():
    """Every SKILL.md under a plugin's skills tree, nested ones included.

    Fizz carries two sub-skills, so a shallow glob undercounts. The checker
    walks the tree; this walks the same tree rather than restating its total.
    """
    return sorted((ROOT / "plugins").glob("*/skills/**/SKILL.md"))


# The vendored Pashov set is upstream-owned and fixed at five skills. That one
# stays a written expectation: the suite should refuse a silent addition to
# somebody else's licensed tree, not absorb it.
VENDORED_SKILLS = 5


def coverage_rows():
    payload = json.loads(
        (ROOT / "tests" / "promise_machine_coverage.json").read_text(encoding="utf-8")
    )
    return payload["rows"]


def rows_in(*groups):
    return [row for row in coverage_rows() if row["group"] in groups]



def run_cli(*arguments):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, arguments)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def make_plugin(root, name="example"):
    plugin = root / "plugins" / name
    for host in (".claude-plugin", ".codex-plugin"):
        manifest = plugin / host / "plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text(
            json.dumps({"name": name, "version": "0.0.0"}) + "\n",
            encoding="utf-8",
        )
    return plugin


def make_licensed_plugin(root, name="example"):
    plugin = make_plugin(root, name)
    licence = LICENSE.read_bytes()
    (root / "LICENSE").write_bytes(licence)
    (plugin / "LICENSE").write_bytes(licence)
    for host in (".claude-plugin", ".codex-plugin"):
        manifest = plugin / host / "plugin.json"
        document = json.loads(manifest.read_text(encoding="utf-8"))
        document["license"] = "Apache-2.0"
        document["author"] = {"name": "Wildcat Labs"}
        manifest.write_text(json.dumps(document) + "\n", encoding="utf-8")
    write_skill(plugin)
    return plugin


def write_skill(plugin, name="example", *, promise_id="example-check", fields=None):
    directory = plugin / "skills" / name
    directory.mkdir(parents=True)
    values = {
        "Promise": "The named check accepted the subject.",
        "Evidence": "example check record",
        "Evidence classes": "checked",
        "Boundary": "No claim beyond the named rule.",
        "Authorises": "Use of the checked result.",
        "Consequence": "1",
        "Refuses": "Use of a missing or failed result.",
        "Recovery": "Repair the input and rerun the check.",
        "Exceptions": "none",
    }
    if fields is not None:
        values = fields
    rows = "\n".join(f"- {field}: {value}" for field, value in values.items())
    (directory / "SKILL.md").write_text(
        "---\n"
        f"name: {name}\n"
        "description: A fixture skill.\n"
        "---\n\n"
        f"# {name}\n\n"
        "## Promise Machine contract\n\n"
        f"### {promise_id}\n\n"
        f"{rows}\n",
        encoding="utf-8",
    )
    (directory / "EVOLUTION.md").write_text("# Evolution\n", encoding="utf-8")
    return directory


def write_vendored_skill(plugin, name="upstream"):
    directory = plugin / "skills" / name
    directory.mkdir(parents=True)
    skill = directory / "SKILL.md"
    skill.write_text(
        "---\n"
        f"name: {name}\n"
        "description: A vendored fixture skill.\n"
        "---\n\n"
        f"# {name}\n",
        encoding="utf-8",
    )
    (directory / "NOTICE.md").write_text(
        "# Notice\n\n"
        "This directory is vendored verbatim.\n\n"
        "- Upstream: https://example.invalid/upstream\n"
        "- Release tag: v0.0.0\n"
        "- Vendored: 2026-08-20\n",
        encoding="utf-8",
    )
    (directory / "LICENSE").write_text("Fixture licence.\n", encoding="utf-8")
    return skill


def write_overlay(root, skill, *, promise_id="hexaemeron-upstream-run", digest=None):
    digest = digest or hashlib.sha256(skill.read_bytes()).hexdigest()
    path = skill.relative_to(root).as_posix()
    overlay = root / "plugins" / "hexaemeron" / "PROMISES.md"
    overlay.write_text(
        "# Hexaemeron Promise Machine overlays\n\n"
        f"### {promise_id}\n\n"
        f"- Path: `{path}`\n"
        f"- SHA-256: `{digest}`\n"
        "- Promise: The named vendored operation completed.\n"
        "- Evidence: The digest-matched instruction and operation record.\n"
        "- Evidence classes: checked, recorded\n"
        "- Boundary: The result covers only the named operation.\n"
        "- Authorises: Use of the recorded result inside its boundary.\n"
        "- Consequence: 1\n"
        "- Refuses: A stale digest or failed operation.\n"
        "- Recovery: Reconcile the instruction and rerun the operation.\n"
        "- Exceptions: none\n",
        encoding="utf-8",
    )
    return overlay


def write_coverage_fixture(root):
    plugin = make_plugin(root, "hexaemeron")
    write_skill(plugin, "elenchus")
    vendored = write_vendored_skill(plugin)
    write_overlay(root, vendored)
    evidence_path = root / "tests" / "evidence.py"
    evidence_path.parent.mkdir(parents=True)
    selectors = {
        "p": "test_positive",
        "m": "test_missing",
        "s": "test_subject_mismatch",
        "o": "test_overclaim",
        "r": "test_recovery",
    }
    evidence_path.write_text(
        "\n".join(f"def {selector}():\n    pass\n" for selector in selectors.values()),
        encoding="utf-8",
    )
    evidence = {
        key: {
            "path": "tests/evidence.py",
            "selector": selector,
            "claim": f"Fixture {key} evidence.",
        }
        for key, selector in selectors.items()
    }
    document = {
        "contract": "promise-machine/v1",
        "schema": "promise-machine-coverage/v1",
        "handoffs": [],
        "evidence": evidence,
        "rows": [
            {
                "promise_id": "example-check",
                "skill_path": "plugins/hexaemeron/skills/elenchus/SKILL.md",
                "group": "executable",
                "cases": {
                    "P": "p",
                    "M": "m",
                    "S": "s",
                    "O": "o",
                    "R": "r",
                    "X": {
                        "not_applicable": True,
                        "reason": "The fixture supports no exceptions.",
                    },
                },
            },
            {
                "promise_id": "hexaemeron-upstream-run",
                "skill_path": "plugins/hexaemeron/skills/upstream/SKILL.md",
                "group": "vendored",
                "cases": None,
                "pending": "Runbook Step 8 classifies vendored evidence.",
            },
        ],
    }
    coverage = root / "tests" / "promise_machine_coverage.json"
    coverage.write_text(json.dumps(document), encoding="utf-8")
    return coverage, document


class PromiseLawTests(unittest.TestCase):
    def test_repository_law_and_copies_are_clean(self):
        completed = run_cli("check", "--only", "law,copies")
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertIn(
            "clean: %d plugin(s), %d copy/copies"
            % (len(discovered_plugins()), len(discovered_plugins())),
            completed.stdout,
        )

    def test_sync_check_is_read_only_and_clean(self):
        before = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        completed = run_cli("sync", "--check")
        after = {path: path.read_bytes() for path in ROOT.glob("plugins/*/PROMISE_MACHINE.md")}
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(before, after)

    def test_all_plugin_copies_are_exact_and_marked(self):
        law = LAW.read_bytes()
        copies = sorted(ROOT.glob("plugins/*/PROMISE_MACHINE.md"))
        self.assertEqual(len(copies), len(discovered_plugins()))
        for copy in copies:
            with self.subTest(copy=copy):
                self.assertEqual(copy.read_bytes(), law)
                self.assertTrue(
                    any(
                        b"copies=generated" in line
                        for line in copy.read_bytes().splitlines()[:5]
                    )
                )


class PromiseLicenceTests(unittest.TestCase):
    def test_repository_first_party_licences_are_clean(self):
        completed = run_cli("check", "--only", "licences", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(
            report["counts"]["licensed_plugins"], len(discovered_plugins())
        )

    def test_missing_root_licence_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            (target / "LICENSE").unlink()
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM072", [item["code"] for item in report["findings"]])

    def test_drifting_plugin_licence_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            (plugin / "LICENSE").write_text("different\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM074", [item["code"] for item in report["findings"]])

    def test_inconsistent_host_manifest_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            manifest = plugin / ".codex-plugin" / "plugin.json"
            document = json.loads(manifest.read_text(encoding="utf-8"))
            document["license"] = "MIT"
            manifest.write_text(json.dumps(document) + "\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM075", [item["code"] for item in report["findings"]])

    def test_vendored_skill_licence_is_outside_first_party_check(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_licensed_plugin(target)
            vendored = write_vendored_skill(plugin)
            self.assertNotEqual((vendored.parent / "LICENSE").read_bytes(), LICENSE.read_bytes())
            completed = run_cli(
                "check", "--root", target, "--only", "licences", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])

    def test_json_report_matches_the_text_result(self):
        completed = run_cli("check", "--only", "law,copies", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        report = json.loads(completed.stdout)
        self.assertEqual(report["contract"], "promise-machine/v1")
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], len(discovered_plugins()))
        self.assertEqual(report["findings"], [])

    def test_divergent_copy_fixture_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            shutil.copytree(FIXTURE / "plugins", target / "plugins")
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertEqual([item["code"] for item in report["findings"]], ["PM014"])

    def test_empty_plugin_set_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            completed = run_cli("check", "--root", target, "--only", "law,copies", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM010", [item["code"] for item in report["findings"]])

    def test_copy_only_refuses_an_absent_root_law(self):
        completed = run_cli(
            "check", "--root", FIXTURE, "--only", "copies", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertFalse(report["ok"])
        self.assertIn("PM001", [item["code"] for item in report["findings"]])

    def test_law_only_does_not_require_a_plugin_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            completed = run_cli(
                "check", "--root", target, "--only", "law", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["plugins"], 0)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_copy_is_refused_without_following_it(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            outside = Path(directory) / "outside.md"
            outside.write_bytes(LAW.read_bytes())
            (plugin / LAW.name).symlink_to(outside)
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM013", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_plugin_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            shutil.copy2(LAW, target / LAW.name)
            (target / "plugins").mkdir()
            outside = Path(directory) / "outside"
            make_plugin(outside)
            (target / "plugins" / "escape").symlink_to(outside / "plugins" / "example")
            completed = run_cli("sync", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM011", [item["code"] for item in report["findings"]])

    def test_sync_repairs_a_divergent_fixed_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copy2(LAW, target / LAW.name)
            plugin = make_plugin(target)
            destination = plugin / LAW.name
            destination.write_text("drift\n", encoding="utf-8")
            completed = run_cli("sync", "--root", target, "--json")
            leftovers = list(plugin.glob(f".{LAW.name}.*"))
            repaired = destination.read_bytes()
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["written"], 1)
        self.assertEqual(repaired, LAW.read_bytes())
        self.assertEqual(leftovers, [])


class PromiseInventoryTests(unittest.TestCase):
    def test_repository_inventory_is_derived_from_disk(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["plugins"], len(discovered_plugins()))
        discovered = len(discovered_canonical_skills())
        self.assertEqual(report["counts"]["canonical_skills"], discovered)
        self.assertEqual(
            report["counts"]["governed_skills"], discovered - VENDORED_SKILLS
        )
        self.assertEqual(report["counts"]["vendored_skills"], VENDORED_SKILLS)
        self.assertEqual(report["counts"]["routers"], 1)

    def test_nested_fizz_subsidiaries_are_discovered(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        paths = {item["path"] for item in report["inventory"]["skills"]}
        self.assertIn(
            "plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md", paths
        )
        self.assertIn(
            "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md", paths
        )

    def test_inventory_text_and_json_results_agree(self):
        json_run = run_cli("inventory", "--json")
        text_run = run_cli("inventory")
        report = json.loads(json_run.stdout)
        self.assertEqual(json_run.returncode, text_run.returncode)
        for key in ("plugins", "canonical_skills", "governed_skills", "vendored_skills"):
            self.assertIn(f"{key}={report['counts'][key]}", text_run.stdout)

    def test_empty_canonical_skill_set_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            make_plugin(target)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM020", [item["code"] for item in report["findings"]])

    def test_unclassified_skill_fixture_is_refused(self):
        completed = run_cli(
            "inventory", "--root", FIXTURES / "unclassified-skill", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM024", [item["code"] for item in report["findings"]])

    def test_vendored_skill_without_complete_ownership_binding_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = plugin / "skills" / "upstream"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: upstream\ndescription: fixture\n---\n", encoding="utf-8"
            )
            (skill / "NOTICE.md").write_text(
                "This skill is vendored verbatim.\n\n- Upstream: https://example.invalid\n"
                "- Release tag: v1\n- Vendored: today\n",
                encoding="utf-8",
            )
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM026", [item["code"] for item in report["findings"]])

    def test_inventory_does_not_claim_copy_checks_it_did_not_run(self):
        completed = run_cli("inventory", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(report["counts"]["copies"], 0)
        checked = run_cli("check", "--only", "inventory,structure")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)
        self.assertIn("0 copy/copies", checked.stdout)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_router_directory_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            plugin = make_plugin(target)
            write_skill(plugin)
            router_root = target / ".agents" / "skills"
            router_root.mkdir(parents=True)
            outside = Path(directory) / "outside" / "router"
            outside.mkdir(parents=True)
            (outside / "SKILL.md").write_text(
                "---\nname: router\ndescription: fixture\n---\n", encoding="utf-8"
            )
            (router_root / "router").symlink_to(outside, target_is_directory=True)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM025", [item["code"] for item in report["findings"]])

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlinked_overlay_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "repo"
            target.mkdir()
            plugin = make_plugin(target)
            write_skill(plugin)
            outside = Path(directory) / "outside.md"
            outside.write_text("# Outside\n", encoding="utf-8")
            (plugin / "PROMISES.md").symlink_to(outside)
            completed = run_cli("inventory", "--root", target, "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM025", [item["code"] for item in report["findings"]])


class PromiseStructureTests(unittest.TestCase):
    def test_standalone_contract_population_is_complete(self):
        expected = {
            "plugins/alexandria/skills/alexandria/SKILL.md": {
                "alexandria-raw-release",
                "alexandria-derived-view",
                "alexandria-release-statement",
                "alexandria-address-query",
                "alexandria-compound-method-proof",
            },
            "plugins/ariadne/skills/ariadne/SKILL.md": {
                "ariadne-capture-statement",
                "ariadne-inspect-statement",
                "ariadne-verify-statement",
                "ariadne-replay-command",
            },
            "plugins/berean/skills/berean/SKILL.md": {
                "berean-corpus-binding",
                "berean-answer-evidence",
                "berean-evaluation-report",
                "berean-release-promotion",
            },
            "plugins/brevitas/skills/brevitas/SKILL.md": {
                "brevitas-structure-check",
                "brevitas-evidence-preservation",
            },
            "plugins/hermes/skills/hermes/SKILL.md": {
                "hermes-corpus-selection",
                "hermes-sealed-baseline",
                "hermes-candidate-acceptance",
                "hermes-baseline-promotion",
            },
            "plugins/horos/skills/horos/SKILL.md": {
                "horos-boundary-scan",
                "horos-boundary-check",
                "horos-census",
                "horos-skeleton-map",
            },
            "plugins/janus/skills/janus/SKILL.md": {
                "janus-manifest-validation",
                "janus-bounded-conformance",
                "janus-report-rendering",
            },
            "plugins/lazarus/skills/lazarus/SKILL.md": {
                "lazarus-fixture-capture",
                "lazarus-fixture-verification",
                "lazarus-exact-replay",
                "lazarus-preservation-release",
            },
            "plugins/lemma/skills/lemma/SKILL.md": {
                "lemma-solidity-chunks",
                "lemma-markdown-chunks",
                "lemma-chunk-validation",
                "lemma-corpus-provenance",
            },
            "plugins/pandects/skills/pandects/SKILL.md": {
                "pandects-law-contract",
                "pandects-catalogue-render",
                "pandects-broken-specimen",
                "pandects-search-record",
            },
            "plugins/probitas/skills/probitas/SKILL.md": {
                "probitas-evidence-collection",
                "probitas-dossier-rendering",
                "probitas-dossier-verification",
            },
            "plugins/sapheneia/skills/sapheneia/SKILL.md": {
                "sapheneia-session-shape",
                "sapheneia-deactivation",
                "sapheneia-durable-record-shape",
            },
            "plugins/synkrisis/skills/synkrisis/SKILL.md": {
                "synkrisis-cohort-construction",
                "synkrisis-bounded-diagnosis",
                "synkrisis-report-verification",
            },
            "plugins/tabularium/skills/tabularium/SKILL.md": {
                "tabularium-release-build",
                "tabularium-release-verification",
                "tabularium-compound-witness",
            },
        }
        for path, promise_ids in expected.items():
            with self.subTest(path=path):
                text = (ROOT / path).read_text(encoding="utf-8")
                self.assertEqual(text.splitlines().count("## Promise Machine contract"), 1)
                contract = text.split("## Promise Machine contract", 1)[1]
                contract = contract.split("\n## ", 1)[0]
                self.assertEqual(
                    {
                        line.removeprefix("### ")
                        for line in contract.splitlines()
                        if line.startswith("### ")
                    },
                    promise_ids,
                )

        completed = run_cli("check", "--only", "structure,contracts", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(
            report["counts"]["promises"], len(rows_in("executable", "prompt"))
        )

    def test_hexaemeron_contract_population_is_complete(self):
        expected = {
            "elenchus": {"elenchus-fixed-and-guarded"},
            "ephoros": {"ephoros-mechanical-gate", "ephoros-observability-review"},
            "fiat": {
                "fiat-controller-checkpoint",
                "fiat-design-evidence",
                "fiat-study-amendment",
                "fiat-runbook-amendment",
                "fiat-run-observation-binding",
                "fiat-receipted-delivery",
                "fiat-local-retirement",
                "fiat-version-resolution",
                "fiat-final-integration",
            },
            "hypomnema": {"hypomnema-pointer-gate", "hypomnema-record-placement"},
            "imprimatur": {"imprimatur-prose-gate"},
            "kronos": {
                "kronos-frontier-ranking",
                "kronos-fiat-dispatch",
                "kronos-parked-lane",
            },
            "metron": {"metron-budget-verdict", "metron-change-decision"},
            "phylax": {"phylax-mechanical-gate", "phylax-boundary-review"},
            "protasis": {"protasis-study-readiness", "protasis-runbook-readiness"},
            "vulgate": {"vulgate-register-rewrite"},
        }
        for skill, promise_ids in expected.items():
            path = ROOT / "plugins" / "hexaemeron" / "skills" / skill / "SKILL.md"
            with self.subTest(skill=skill):
                text = path.read_text(encoding="utf-8")
                self.assertEqual(text.splitlines().count("## Promise Machine contract"), 1)
                contract = text.split("## Promise Machine contract", 1)[1]
                contract = contract.split("\n## ", 1)[0]
                self.assertEqual(
                    {
                        line.removeprefix("### ")
                        for line in contract.splitlines()
                        if line.startswith("### ")
                    },
                    promise_ids,
                )


class PromiseOverlayTests(unittest.TestCase):
    def test_repository_overlay_population_is_complete_and_digest_bound(self):
        expected = {
            "plugins/hexaemeron/skills/fizz/SKILL.md":
                "62a60df4cec160511b8ef36433eef7c8805d0b4a398491293eb4542ab73539bd",
            "plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md":
                "59cd4b4ef5dc56315782a7d25222afb286a24e63e438530cbd0044293ea54af7",
            "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md":
                "e969cd8a447941989715840e24aa6a915c0fd795effabd912b3c627598a95e16",
            "plugins/hexaemeron/skills/x-ray/SKILL.md":
                "b23bb94517805c1b8ce717d0e1e0282b0b5c14c7b16f4c32e73940292d3d4a41",
            "plugins/hexaemeron/skills/solidity-auditor/SKILL.md":
                "1c1cf4e99d042e7aadc56b622d97a07d3286f4786838a05510697c814d1e983f",
        }
        text = (ROOT / "plugins" / "hexaemeron" / "PROMISES.md").read_text(
            encoding="utf-8"
        )
        for path, digest in expected.items():
            with self.subTest(path=path):
                self.assertIn(f"- Path: `{path}`", text)
                self.assertIn(f"- SHA-256: `{digest}`", text)

        completed = run_cli("check", "--only", "contracts,overlays", "--json")
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["promises"], len(coverage_rows()))
        self.assertEqual(report["counts"]["overlays"], 1)

    def test_one_byte_vendored_mutation_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            skill = write_vendored_skill(plugin)
            write_overlay(target, skill)
            clean = run_cli("check", "--root", target, "--only", "overlays", "--json")
            skill.write_bytes(skill.read_bytes() + b"x")
            drifted = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        self.assertEqual(clean.returncode, 0, clean.stdout + clean.stderr)
        report = json.loads(drifted.stdout)
        self.assertEqual(drifted.returncode, 1)
        self.assertIn("PM057", [item["code"] for item in report["findings"]])

    def test_missing_overlay_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            write_vendored_skill(plugin)
            completed = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM050", [item["code"] for item in report["findings"]])

    def test_overlay_cannot_bind_a_first_party_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target, "hexaemeron")
            skill = write_skill(plugin) / "SKILL.md"
            write_overlay(target, skill)
            completed = run_cli(
                "check", "--root", target, "--only", "overlays", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM055", [item["code"] for item in report["findings"]])


class PromiseStructureValidationTests(unittest.TestCase):
    def test_contract_component_refuses_an_absent_section(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: A fixture skill.\n---\n\n# Example\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "contracts", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM031", [item["code"] for item in report["findings"]])

    def test_missing_contract_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "missing-contract",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM031", [item["code"] for item in report["findings"]])

    def test_each_missing_promise_field_is_refused(self):
        for missing in PROMISE_FIELDS:
            with self.subTest(field=missing), tempfile.TemporaryDirectory() as directory:
                target = Path(directory)
                plugin = make_plugin(target)
                values = {
                    field: "none" if field == "Exceptions" else "fixture value"
                    for field in PROMISE_FIELDS
                    if field != missing
                }
                if "Evidence classes" in values:
                    values["Evidence classes"] = "checked"
                if "Consequence" in values:
                    values["Consequence"] = "1"
                write_skill(plugin, fields=values)
                completed = run_cli(
                    "check", "--root", target, "--only", "inventory,structure", "--json"
                )
            report = json.loads(completed.stdout)
            self.assertEqual(completed.returncode, 1)
            self.assertIn("PM034", [item["code"] for item in report["findings"]])

    def test_unsupported_evidence_class_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unsupported-evidence-class",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM036", [item["code"] for item in report["findings"]])

    def test_no_recovery_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "no-recovery",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM034", [item["code"] for item in report["findings"]])

    def test_duplicate_promise_ids_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin, "one", promise_id="same-promise")
            write_skill(plugin, "two", promise_id="same-promise")
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM035", [item["code"] for item in report["findings"]])

    def test_unattributed_exception_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unattributed-exception",
            "--only",
            "inventory,structure",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM038", [item["code"] for item in report["findings"]])

    def test_exception_keywords_without_structured_attribution_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            fields = {
                "Promise": "The named check accepted the subject.",
                "Evidence": "example record",
                "Evidence classes": "checked",
                "Boundary": "No claim beyond the named rule.",
                "Authorises": "Use of the checked result.",
                "Consequence": "1",
                "Refuses": "Use of a failed result.",
                "Recovery": "Repair and rerun.",
                "Exceptions": (
                    "Authority is absent, scope is unknown, no record exists and expiry never applies."
                ),
            }
            write_skill(plugin, fields=fields)
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM038", [item["code"] for item in report["findings"]])

    def test_vendored_instruction_cannot_author_its_own_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = write_skill(plugin, "upstream")
            (skill / "EVOLUTION.md").unlink()
            (skill / "LICENSE").write_text("fixture licence\n", encoding="utf-8")
            (skill / "NOTICE.md").write_text(
                "This skill is vendored verbatim.\n\n- Upstream: https://example.invalid\n"
                "- Release tag: v1\n- Vendored: today\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "inventory,structure", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM029", [item["code"] for item in report["findings"]])


class PromiseIdentityTests(unittest.TestCase):
    def test_repository_identity_router_versions_and_hosts_are_clean(self):
        completed = run_cli(
            "check", "--only", "identity,routers,versions,hosts", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(
            report["counts"]["canonical_skills"], len(discovered_canonical_skills())
        )
        self.assertEqual(report["counts"]["routers"], 1)
        shipped = len(discovered_plugins())
        self.assertEqual(report["counts"]["claude_plugins"], shipped)
        self.assertEqual(report["counts"]["codex_plugins"], shipped)
        self.assertEqual(report["counts"]["package_versions"], len(discovered_plugins()))
        self.assertEqual(
            report["counts"]["skill_versions"],
            len(discovered_canonical_skills()) - VENDORED_SKILLS,
        )

    def test_unresolved_router_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "unresolved-router",
            "--only",
            "routers",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM041", [item["code"] for item in report["findings"]])

    def test_duplicate_canonical_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "duplicate-canonical",
            "--only",
            "identity",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM044", [item["code"] for item in report["findings"]])

    def test_package_as_skill_version_fixture_is_refused(self):
        completed = run_cli(
            "check",
            "--root",
            FIXTURES / "package-as-skill-version",
            "--only",
            "versions",
            "--json",
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM046", [item["code"] for item in report["findings"]])

    def test_router_with_a_behavioural_version_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin)
            router = target / ".agents" / "skills" / "promise-machine" / "SKILL.md"
            router.parent.mkdir(parents=True)
            router.write_text(
                "---\nname: promise-machine\ndescription: fixture\n"
                "metadata:\n  version: \"1.0.0\"\n---\n\n"
                "# Promise Machine\n\n[Root](../../../AGENTS.md)\n",
                encoding="utf-8",
            )
            (target / "AGENTS.md").write_text("# Runtime\n", encoding="utf-8")
            completed = run_cli(
                "check", "--root", target, "--only", "routers", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM043", [item["code"] for item in report["findings"]])

    def test_body_text_cannot_supply_frontmatter_identity_or_version(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = plugin / "skills" / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\ndescription: fixture\n---\n\n# Example\n\n"
                "name: example\n\n  version: \"0.0.0\"\n",
                encoding="utf-8",
            )
            (skill / "EVOLUTION.md").write_text(
                "# Evolution\n\n- Current version: `example-v0.0.0`\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "identity,versions", "--json"
            )
        report = json.loads(completed.stdout)
        codes = [item["code"] for item in report["findings"]]
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM023", codes)
        self.assertIn("PM046", codes)

    def test_duplicate_skill_metadata_versions_are_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            skill = plugin / "skills" / "example"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: example\ndescription: fixture\nmetadata:\n"
                "  version: \"0.0.0\"\n  version: \"0.0.0\"\n---\n",
                encoding="utf-8",
            )
            (skill / "EVOLUTION.md").write_text(
                "# Evolution\n\n- Current version: `example-v0.0.0`\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "versions", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM046", [item["code"] for item in report["findings"]])

    def test_package_marketplace_version_mismatch_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin)
            marketplace = target / ".claude-plugin" / "marketplace.json"
            marketplace.parent.mkdir()
            marketplace.write_text(
                json.dumps(
                    {
                        "name": "fixture",
                        "plugins": [
                            {
                                "name": "example",
                                "source": "./plugins/example",
                                "version": "9.9.9",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "versions", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM045", [item["code"] for item in report["findings"]])

    def test_body_version_example_does_not_version_the_router(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            plugin = make_plugin(target)
            write_skill(plugin)
            (target / "AGENTS.md").write_text("# Root runtime\n", encoding="utf-8")
            (plugin / "AGENTS.md").write_text(
                "# Plugin runtime\n\n`skills/example/SKILL.md`\n", encoding="utf-8"
            )
            router = target / ".agents" / "skills" / "promise-machine" / "SKILL.md"
            router.parent.mkdir(parents=True)
            router.write_text(
                "---\nname: promise-machine\ndescription: fixture\n---\n\n"
                "# Promise Machine\n\n[Root](../../../AGENTS.md)\n"
                "[Example](../../../plugins/example/AGENTS.md)\n\n"
                "An unrelated example may contain:\n\n  version: \"1.0.0\"\n",
                encoding="utf-8",
            )
            completed = run_cli(
                "check", "--root", target, "--only", "routers", "--json"
            )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


class PromiseCoverageTests(unittest.TestCase):
    def test_repository_executable_coverage_is_complete(self):
        completed = run_cli(
            "coverage", "--check", "--group", "executable", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["coverage_rows"], len(coverage_rows()))
        self.assertEqual(
            report["counts"]["coverage_selected"], len(rows_in("executable"))
        )

    def test_berean_and_janus_boundaries_are_explicit(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        rows = {row["promise_id"]: row for row in coverage["rows"]}
        self.assertEqual(
            set(rows["berean-answer-evidence"]["preserves"]),
            {
                "answer-truth-refused",
                "read-class",
                "source-class",
                "subject",
                "time-domain",
            },
        )
        self.assertEqual(
            set(rows["janus-bounded-conformance"]["preserves"]),
            {
                "adapter",
                "bounded-search",
                "cross-host-refused",
                "manifest",
                "recorder",
                "safety-refused",
                "unknown-effect-refused",
            },
        )
        self.assertEqual(
            {
                (handoff["producer"], handoff["consumer"])
                for handoff in coverage["handoffs"]
            },
            {
                ("lazarus-fixture-verification", "berean-answer-evidence"),
                ("berean-release-promotion", "ariadne-capture-statement"),
            },
        )

    def test_run_observation_coverage_binds_the_exact_release_surface(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )["run_observation"]
        self.assertEqual(coverage["contract"], "promise-machine-run-observation/v1")
        self.assertEqual(
            coverage["promise_id"],
            "promise-machine-run-observation-structural-validation",
        )
        self.assertIn(
            "### promise-machine-run-observation-structural-validation",
            (ROOT / "PROMISE_MACHINE.md").read_text(encoding="utf-8"),
        )
        bound = [coverage["runtime"], coverage["schema_source"], coverage["documentation"]]
        bound.extend(coverage["fixtures"])
        bound.append({key: coverage["tests"][key] for key in ("path", "sha256")})
        for item in bound:
            with self.subTest(path=item["path"]):
                path = ROOT / item["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"])
        tests = (ROOT / coverage["tests"]["path"]).read_text(encoding="utf-8")
        for selector in coverage["tests"]["selectors"]:
            with self.subTest(selector=selector):
                self.assertIn(f"def {selector}(", tests)
        self.assertIn("structurally conforming", coverage["transition"])

    def test_run_observation_binding_coverage_binds_the_exact_release_surface(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )["run_observation_binding"]
        self.assertEqual(coverage["contract"], "fiat-run-observation-binding/v1")
        self.assertIn(
            "fiat-run-observation-binding",
            {row["promise_id"] for row in json.loads(
                (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                    encoding="utf-8"
                )
            )["rows"]},
        )
        self.assertIn(
            "### fiat-run-observation-binding",
            (ROOT / "plugins/hexaemeron/skills/fiat/SKILL.md").read_text(
                encoding="utf-8"
            ),
        )
        bound = [
            coverage["controller"],
            coverage["validator"],
            coverage["documentation"],
            coverage["decision"],
            coverage["fixture_manifest"],
            coverage["reporter"],
        ]
        bound.extend(
            {key: item[key] for key in ("path", "sha256")}
            for item in coverage["tests"]
        )
        for item in bound:
            with self.subTest(path=item["path"]):
                path = ROOT / item["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(), item["sha256"]
                )
        for item in coverage["tests"]:
            source = (ROOT / item["path"]).read_text(encoding="utf-8")
            for selector in item["selectors"]:
                with self.subTest(path=item["path"], selector=selector):
                    self.assertIn(f"def {selector}(", source)
        self.assertIn("without advancing Fiat", coverage["transition"])

    def test_repository_high_consequence_runtime_bindings_are_complete(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        expected_fields = {
            "promise_id",
            "subject",
            "scope",
            "evidence_references",
            "evidence_classes",
            "unknowns",
            "transition",
            "exception",
        }
        self.assertEqual(len(coverage["runtime"]), 40)
        for promise_id, binding in coverage["runtime"].items():
            with self.subTest(promise_id=promise_id):
                self.assertEqual(set(binding), {"source", "sha256", "bindings"})
                self.assertEqual(set(binding["bindings"]), expected_fields)
                self.assertTrue((ROOT / binding["source"]).is_file())

    def test_high_consequence_promise_without_runtime_binding_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM070", [item["code"] for item in report["findings"]])

    def test_runtime_binding_source_must_be_confined(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            document["runtime"] = {
                "example-check": {
                    "source": "../outside.json",
                    "sha256": "0" * 64,
                    "bindings": {
                        "promise_id": "promise id",
                        "subject": "subject",
                        "scope": "scope",
                        "evidence_references": "evidence references",
                        "evidence_classes": "evidence classes",
                        "unknowns": "unknowns",
                        "transition": "transition",
                        "exception": "exception",
                    },
                }
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM070", [item["code"] for item in report["findings"]])

    def test_runtime_binding_source_digest_must_be_current(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            document["runtime"] = {
                "example-check": {
                    "source": "tests/evidence.py",
                    "sha256": "0" * 64,
                    "bindings": {
                        "promise_id": "promise id",
                        "subject": "subject",
                        "scope": "scope",
                        "evidence_references": "evidence references",
                        "evidence_classes": "evidence classes",
                        "unknowns": "unknowns",
                        "transition": "transition",
                        "exception": "exception",
                    },
                }
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM071", [item["code"] for item in report["findings"]])

    def test_runtime_binding_source_read_is_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            skill = target / "plugins/hexaemeron/skills/elenchus/SKILL.md"
            skill.write_text(
                skill.read_text(encoding="utf-8").replace(
                    "- Consequence: 1", "- Consequence: 2"
                ),
                encoding="utf-8",
            )
            oversized = target / "tests/oversized.bin"
            oversized.write_bytes(b"x" * (1024 * 1024 + 1))
            document["runtime"] = {
                "example-check": {
                    "source": "tests/oversized.bin",
                    "sha256": hashlib.sha256(oversized.read_bytes()).hexdigest(),
                    "bindings": {
                        "promise_id": "promise id",
                        "subject": "subject",
                        "scope": "scope",
                        "evidence_references": "evidence references",
                        "evidence_classes": "evidence classes",
                        "unknowns": "unknowns",
                        "transition": "transition",
                        "exception": "exception",
                    },
                }
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage", "--check", "--root", target, "--group", "executable", "--json"
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM070", [item["code"] for item in report["findings"]])

    def test_repository_prompt_and_vendored_coverage_is_complete(self):
        completed = run_cli(
            "coverage", "--check", "--group", "prompt,vendored", "--json"
        )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertTrue(report["ok"])
        self.assertEqual(report["counts"]["coverage_rows"], len(coverage_rows()))
        self.assertEqual(report["counts"]["coverage_selected"], 17)

    def test_prompt_and_vendored_evaluations_never_claim_proof(self):
        coverage = json.loads(
            (ROOT / "tests" / "promise_machine_coverage.json").read_text(
                encoding="utf-8"
            )
        )
        selected = [
            row for row in coverage["rows"] if row["group"] in {"prompt", "vendored"}
        ]
        self.assertEqual(len(selected), 17)
        self.assertTrue(all("pending" not in row for row in selected))
        self.assertTrue(
            all(row["evaluation"]["status"] in {"recorded", "unknown"} for row in selected)
        )

    def run_mutation(self, mutate):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            mutate(document)
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "executable",
                "--json",
            )
        return completed, json.loads(completed.stdout)

    def run_vendored_mutation(self, mutate):
        def complete(document):
            row = document["rows"][1]
            row["cases"] = dict(document["rows"][0]["cases"])
            row.pop("pending")
            for evidence in document["evidence"].values():
                evidence["evidence_class"] = "checked"
            row["evaluation"] = {
                "status": "recorded",
                "model": "not-run",
                "prompt": "Fixture prompt.",
                "corpus": "tests/evidence.py",
                "disposition": "Fixture classifications recorded.",
            }
            mutate(document)

        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            complete(document)
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "vendored",
                "--json",
            )
        return completed, json.loads(completed.stdout)

    def test_missing_coverage_row_is_refused(self):
        completed, report = self.run_mutation(
            lambda document: document["rows"].pop(0)
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM062", [item["code"] for item in report["findings"]])

    def test_unresolved_test_selector_is_refused(self):
        def mutate(document):
            document["evidence"]["p"]["selector"] = "test_absent"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM065", [item["code"] for item in report["findings"]])

    def test_one_selector_cannot_satisfy_incompatible_cases(self):
        def mutate(document):
            document["rows"][0]["cases"]["M"] = "p"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM067", [item["code"] for item in report["findings"]])

    def test_material_missing_case_cannot_be_inapplicable(self):
        def mutate(document):
            document["rows"][0]["cases"]["M"] = {
                "not_applicable": True,
                "reason": "Fixture claim.",
            }

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM066", [item["code"] for item in report["findings"]])

    def test_inapplicability_requires_a_reason(self):
        def mutate(document):
            document["rows"][0]["cases"]["X"] = {"not_applicable": True}

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM064", [item["code"] for item in report["findings"]])

    def test_unsupported_evidence_class_is_refused(self):
        def mutate(document):
            document["evidence"]["p"]["evidence_class"] = "anecdotal"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM064", [item["code"] for item in report["findings"]])

    def test_evidence_class_must_be_accepted_by_the_promise(self):
        def mutate(document):
            document["evidence"]["p"]["evidence_class"] = "recorded"

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM064", [item["code"] for item in report["findings"]])

    def test_duplicate_json_key_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, _ = write_coverage_fixture(target)
            coverage_path.write_text(
                '{"contract":"promise-machine/v1",'
                '"contract":"promise-machine/v1"}',
                encoding="utf-8",
            )
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "executable",
                "--json",
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM061", [item["code"] for item in report["findings"]])

    def test_selected_pending_row_is_refused(self):
        def mutate(document):
            document["rows"][0]["cases"] = None
            document["rows"][0]["pending"] = "Later."

        completed, report = self.run_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM066", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_provenance_is_required(self):
        completed, report = self.run_vendored_mutation(
            lambda document: document["rows"][1].pop("evaluation")
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_may_not_claim_proof(self):
        def mutate(document):
            document["rows"][1]["evaluation"]["status"] = "proved"

        completed, report = self.run_vendored_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_corpus_must_resolve(self):
        def mutate(document):
            document["rows"][1]["evaluation"]["corpus"] = "tests/missing.json"

        completed, report = self.run_vendored_mutation(mutate)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])

    def test_prompt_or_vendored_evaluation_corpus_must_be_repository_relative(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            coverage_path, document = write_coverage_fixture(target)
            row = document["rows"][1]
            row["cases"] = dict(document["rows"][0]["cases"])
            row.pop("pending")
            for evidence in document["evidence"].values():
                evidence["evidence_class"] = "checked"
            row["evaluation"] = {
                "status": "recorded",
                "model": "not-run",
                "prompt": "Fixture prompt.",
                "corpus": str((target / "tests" / "evidence.py").resolve()),
                "disposition": "Fixture classifications recorded.",
            }
            coverage_path.write_text(json.dumps(document), encoding="utf-8")
            completed = run_cli(
                "coverage",
                "--check",
                "--root",
                target,
                "--group",
                "vendored",
                "--json",
            )
        report = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 1)
        self.assertIn("PM069", [item["code"] for item in report["findings"]])


if __name__ == "__main__":
    unittest.main()
