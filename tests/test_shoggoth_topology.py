"""Prove the bounded Shoggoth plugin and governed-skill topology reader."""

from __future__ import annotations

import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from scripts import shoggoth_topology
from scripts.shoggoth_topology import (
    MAX_MANIFEST_BYTES,
    MAX_SKILL_ENTRIES,
    TopologyError,
    discover_topology,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "shoggoth-topology"
EXPECTED_CANONICAL = (
    "alexandria",
    "anamnesis",
    "ariadne",
    "berean",
    "brevitas",
    "fiat",
    "hermes",
    "homologia",
    "horos",
    "janus",
    "lazarus",
    "lemma",
    "pandects",
    "probitas",
    "sapheneia",
    "synkrisis",
    "tabularium",
)
EXPECTED_PHASES = (
    "elenchus",
    "ephoros",
    "hypomnema",
    "imprimatur",
    "kronos",
    "metron",
    "phylax",
    "protasis",
    "vulgate",
)


def _fixture_document(name: str) -> dict:
    path = FIXTURES / name
    document = json.loads(path.read_text(encoding="utf-8"))
    schema = document.get("schema")
    if schema == "shoggoth-topology-fixture/v1":
        if set(document) != {"schema", "plugins", "skills"}:
            raise AssertionError(f"open fixture shape: {path}")
        plugins = list(document["plugins"])
        return {
            "claude_plugins": plugins,
            "codex_plugins": list(plugins),
            "skills": [
                {"plugin": plugin, "skill": skill, "skill_file": True}
                for plugin, skill in document["skills"]
            ],
        }
    if schema != "shoggoth-topology-fixture-mutation/v1":
        raise AssertionError(f"unknown fixture schema: {path}")
    result = copy.deepcopy(_fixture_document(document["base"]))
    operation = document.get("operation")
    if operation == "duplicate-plugin":
        expected = {"schema", "base", "operation", "host", "plugin"}
        if set(document) != expected:
            raise AssertionError(f"open duplicate-plugin fixture: {path}")
        result[f"{document['host']}_plugins"].append(document["plugin"])
    elif operation == "remove-skill-file":
        expected = {"schema", "base", "operation", "plugin", "skill"}
        if set(document) != expected:
            raise AssertionError(f"open missing-skill fixture: {path}")
        matches = [
            skill
            for skill in result["skills"]
            if skill["plugin"] == document["plugin"]
            and skill["skill"] == document["skill"]
        ]
        if len(matches) != 1:
            raise AssertionError(f"missing mutation target: {path}")
        matches[0]["skill_file"] = False
    elif operation == "add-governed-skill":
        expected = {"schema", "base", "operation", "plugin", "skill"}
        if set(document) != expected:
            raise AssertionError(f"open unexpected-phase fixture: {path}")
        result["skills"].append(
            {
                "plugin": document["plugin"],
                "skill": document["skill"],
                "skill_file": True,
            }
        )
    else:
        raise AssertionError(f"unknown fixture operation {operation!r}: {path}")
    return result


def _write_manifests(root: Path, fixture: dict) -> None:
    claude_entries = [
        {"name": plugin, "source": f"./plugins/{plugin}"}
        for plugin in fixture["claude_plugins"]
    ]
    codex_entries = [
        {
            "name": plugin,
            "source": {"source": "local", "path": f"./plugins/{plugin}"},
        }
        for plugin in fixture["codex_plugins"]
    ]
    claude = root / ".claude-plugin" / "marketplace.json"
    codex = root / ".agents" / "plugins" / "marketplace.json"
    claude.parent.mkdir(parents=True)
    codex.parent.mkdir(parents=True)
    claude.write_text(
        json.dumps({"plugins": claude_entries}, indent=2) + "\n",
        encoding="utf-8",
    )
    codex.write_text(
        json.dumps({"plugins": codex_entries}, indent=2) + "\n",
        encoding="utf-8",
    )


def _build_tree(root: Path, fixture: dict) -> None:
    _write_manifests(root, fixture)
    plugin_ids = {
        *fixture["claude_plugins"],
        *fixture["codex_plugins"],
        *(skill["plugin"] for skill in fixture["skills"]),
    }
    for plugin in plugin_ids:
        (root / "plugins" / plugin / "skills").mkdir(parents=True)
    for skill in fixture["skills"]:
        directory = (
            root / "plugins" / skill["plugin"] / "skills" / skill["skill"]
        )
        directory.mkdir(parents=True)
        (directory / "EVOLUTION.md").write_text("# Evolution\n", encoding="utf-8")
        if skill["skill_file"]:
            (directory / "SKILL.md").write_text(
                f"---\nname: {skill['skill']}\n---\n",
                encoding="utf-8",
            )


class ShoggothTopologyTests(unittest.TestCase):
    def test_valid_fixture_and_live_tree_return_17_26_17_9(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            fixture_root = Path(temporary)
            _build_tree(fixture_root, fixture)
            specimen = discover_topology(fixture_root)

        live = discover_topology(ROOT)
        for topology in (specimen, live):
            with self.subTest(root="fixture" if topology is specimen else "live"):
                self.assertEqual(len(topology.plugin_ids), 17)
                self.assertEqual(len(topology.governed_skills), 26)
                self.assertEqual(len(topology.canonical_ids), 17)
                self.assertEqual(len(topology.phase_ids), 9)
                self.assertEqual(topology.canonical_ids, EXPECTED_CANONICAL)
                self.assertEqual(topology.phase_ids, EXPECTED_PHASES)
        self.assertEqual(specimen.plugin_ids, live.plugin_ids)
        self.assertEqual(specimen.governed_ids, live.governed_ids)

    def test_duplicate_plugin_fixture_is_rejected(self):
        fixture = _fixture_document("duplicate-plugin.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            with self.assertRaisesRegex(TopologyError, r"T007 duplicate plugin id"):
                discover_topology(root)

    def test_missing_skill_fixture_is_rejected(self):
        fixture = _fixture_document("missing-skill.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            with self.assertRaisesRegex(TopologyError, r"T013 governed skill lacks"):
                discover_topology(root)

    def test_unexpected_phase_fixture_is_rejected(self):
        fixture = _fixture_document("unexpected-phase.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            with self.assertRaisesRegex(TopologyError, r"T017 unexpected phase"):
                discover_topology(root)

    def test_host_manifest_disagreement_is_rejected(self):
        fixture = _fixture_document("valid-17-26.json")
        fixture["codex_plugins"].pop()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            with self.assertRaisesRegex(TopologyError, r"T014 host marketplace disagreement"):
                discover_topology(root)

    def test_manifest_path_outside_plugins_is_rejected(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            manifest = root / ".claude-plugin" / "marketplace.json"
            document = json.loads(manifest.read_text(encoding="utf-8"))
            document["plugins"][0]["source"] = "../outside"
            manifest.write_text(json.dumps(document) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(TopologyError, r"T008 plugin path is outside"):
                discover_topology(root)

    def test_duplicate_json_key_is_rejected(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            manifest = root / ".claude-plugin" / "marketplace.json"
            text = manifest.read_text(encoding="utf-8")
            text = text.replace(
                '"name": "alexandria"',
                '"name": "alexandria", "name": "alexandria"',
                1,
            )
            manifest.write_text(text, encoding="utf-8")
            with self.assertRaisesRegex(TopologyError, r"T004 invalid JSON"):
                discover_topology(root)

    def test_oversized_manifest_is_rejected_before_json_parsing(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            manifest = root / ".claude-plugin" / "marketplace.json"
            manifest.write_bytes(b" " * (MAX_MANIFEST_BYTES + 1))
            with self.assertRaisesRegex(TopologyError, r"T003 input exceeds"):
                discover_topology(root)

    def test_manifest_changed_while_read_is_rejected(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            manifest = root / ".claude-plugin" / "marketplace.json"
            manifest_inode = manifest.stat().st_ino
            replacement = manifest.read_text(encoding="utf-8").replace(
                "./plugins/alexandria", "./plugins/anaXandria", 1
            )
            real_read = shoggoth_topology.os.read
            changed = False

            def racing_read(descriptor, amount):
                nonlocal changed
                chunk = real_read(descriptor, amount)
                if (
                    not changed
                    and shoggoth_topology.os.fstat(descriptor).st_ino
                    == manifest_inode
                ):
                    manifest.write_text(replacement, encoding="utf-8")
                    changed = True
                return chunk

            with patch.object(shoggoth_topology.os, "read", racing_read):
                with self.assertRaisesRegex(TopologyError, r"T019 input changed"):
                    discover_topology(root)
            self.assertTrue(changed)

    def test_entry_ceiling_stops_scan_before_consuming_the_rest(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            wide = root / "plugins" / "alexandria" / "skills"
            for index in range(MAX_SKILL_ENTRIES + 2):
                (wide / f"dummy-{index:04d}").touch()

            real_scandir = shoggoth_topology.os.scandir

            class CappedScan:
                def __init__(self, target):
                    self.context = real_scandir(target)
                    self.iterator = None
                    self.count = 0

                def __enter__(self):
                    self.iterator = self.context.__enter__()
                    return self

                def __exit__(self, *arguments):
                    return self.context.__exit__(*arguments)

                def __iter__(self):
                    return self

                def __next__(self):
                    self.count += 1
                    if self.count > MAX_SKILL_ENTRIES + 1:
                        raise AssertionError(
                            "scanner consumed past the declared entry ceiling"
                        )
                    return next(self.iterator)

            with patch.object(shoggoth_topology.os, "scandir", CappedScan):
                with self.assertRaisesRegex(TopologyError, r"T010 skill tree exceeds"):
                    discover_topology(root)

    def test_symlinked_skill_directory_is_rejected(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            skill = root / "plugins" / "alexandria" / "skills" / "alexandria"
            outside = root / "outside-skill"
            skill.rename(outside)
            skill.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(TopologyError, r"T011 symlinked skill-tree entry"):
                discover_topology(root)

    def test_symlinked_plugins_directory_is_rejected_without_following_it(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            root = base / "root"
            outside = base / "outside"
            root.mkdir()
            _build_tree(outside, fixture)
            _write_manifests(root, fixture)
            (root / "plugins").symlink_to(
                outside / "plugins", target_is_directory=True
            )
            with self.assertRaisesRegex(TopologyError, r"T009 directory .*symlinked"):
                discover_topology(root)

    def test_symlinked_manifest_is_rejected_without_following_it(self):
        fixture = _fixture_document("valid-17-26.json")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _build_tree(root, fixture)
            manifest = root / ".claude-plugin" / "marketplace.json"
            outside = root / "outside-marketplace.json"
            shutil.move(manifest, outside)
            manifest.symlink_to(outside)
            with self.assertRaisesRegex(TopologyError, r"T002 cannot read regular file"):
                discover_topology(root)


if __name__ == "__main__":
    unittest.main()
