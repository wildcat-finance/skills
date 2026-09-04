"""The derived topology must agree with itself, and refuse what it cannot count.

Public prose has repeatedly carried plugin and skill counts a person typed once
and nobody updated. `scripts/shoggoth_topology.py` derives those numbers from
the tree and the two marketplace manifests instead, so this suite asks whether
the derivation is trustworthy rather than whether it prints a number somebody
expected.

Against the live tree it therefore asserts **agreement, never a literal**. Both
manifests and tree discovery must return the same plugin set; every plugin must
have exactly one canonical entry skill, with Fiat as Hexaemeron's; canonical
plus phase must equal governed; and the hypomnema design-bridge fixture must
stay outside the count. A new plugin landing in this repository moves every one
of those numbers together, and no case here notices.

That distinction is the reason this file exists. The predecessor run asserted
`specimen.plugin_ids == live.plugin_ids`, which froze a synthetic fixture
against a tree that legitimately grows, so the next plugin to land broke a test
that had nothing to do with it. Every literal count below belongs to a
specimen that declares its own arbitrary ids, and no assertion compares a
specimen identity set with a live one.
"""

from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))  # noqa: E402  (locates shoggoth_topology.py)

import shoggoth_topology  # noqa: E402

SPECIMENS = ROOT / "tests" / "fixtures" / "shoggoth-topology"

# The one live structural constant this repository declares about itself: the
# phase host and the entry skill that stands in for its own name.
PHASE_HOST = "hexaemeron"
PHASE_HOST_ENTRY = "fiat"

DESIGN_BRIDGE = "plugins/hexaemeron/tests/fixtures/hypomnema/design-bridge"


def write_json(path: Path, body: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def plant(root: Path, plugins, *, ledger=shoggoth_topology.LEDGER_NAME) -> None:
    """Materialise a skill tree and both manifests under `root`.

    The reader only asks whether `EVOLUTION.md` and `SKILL.md` are regular
    files, so placeholder bodies are enough and keep the temporary trees small.
    """
    claude = []
    agents = []
    for plugin in plugins:
        pid = plugin["id"]
        claude.append({"name": pid, "source": f"./plugins/{pid}"})
        agents.append(
            {
                "name": pid,
                "source": {"source": "local", "path": f"./plugins/{pid}"},
            }
        )
        for skill in plugin["skills"]:
            where = root / "plugins" / pid / "skills" / skill["name"]
            where.mkdir(parents=True, exist_ok=True)
            if skill.get("ledger", True):
                (where / ledger).write_text("# ledger\n", encoding="utf-8")
            if skill.get("entry", True):
                (where / shoggoth_topology.ENTRY_NAME).write_text(
                    "# skill\n", encoding="utf-8"
                )
    write_json(
        root / ".claude-plugin" / "marketplace.json",
        {"name": "specimen", "owner": "specimen", "plugins": claude},
    )
    write_json(
        root / ".agents" / "plugins" / "marketplace.json",
        {"name": "specimen", "interface": "specimen", "plugins": agents},
    )


def as_plant_spec(topology) -> list[dict]:
    """Turn a derived topology back into the tree specification that plants it."""
    by_plugin: dict[str, list[dict]] = {plugin: [] for plugin in topology.plugins}
    for governed in topology.governed:
        _, plugin, _, skill = governed.split("/")
        by_plugin[plugin].append({"name": skill, "ledger": True, "entry": True})
    return [{"id": pid, "skills": skills} for pid, skills in by_plugin.items()]


def mirror_live(root: Path, live) -> None:
    """Rebuild only what the reader reads from the live tree, under `root`.

    Copying the repository would be slow and would drag in everything the
    reader never opens. This plants the same governed shape the live tree
    derives, so a case can mutate it and compare the derivation before and
    after. It is seeded from the live derivation on every run, so it is not a
    frozen fixture and a new plugin landing moves both sides together.
    """
    plant(root, as_plant_spec(live))


def load_specimen(name: str) -> dict:
    return json.loads((SPECIMENS / f"{name}.json").read_text(encoding="utf-8"))


def read_specimen(root: Path, specimen: dict):
    plant(root, specimen["plugins"])
    return shoggoth_topology.read(
        root,
        phase_host=specimen["phase_host"],
        phase_host_entry=specimen["phase_host_entry"],
    )


class SpecimenTests(unittest.TestCase):
    """Frozen synthetic trees with their own ids, and exact literal counts.

    A specimen is self-describing: it declares the tree to plant and either the
    counts that tree must derive or the refusal code it must raise. Its ids are
    arbitrary and share nothing with this repository, so no assertion here can
    be broken by a plugin landing.
    """

    def test_every_specimen_is_exercised(self):
        """The specimen directory is closed; a new file must gain a case."""
        found = {path.stem for path in SPECIMENS.glob("*.json")}
        self.assertEqual(
            found,
            {
                "valid-quarry",
                "duplicate-plugin-id",
                "missing-canonical-entry",
                "phase-outside-host",
            },
        )

    def test_the_valid_specimen_derives_its_declared_counts(self):
        specimen = load_specimen("valid-quarry")
        with tempfile.TemporaryDirectory() as tmp:
            derived = read_specimen(Path(tmp), specimen)
        expect = specimen["expect"]
        self.assertEqual(derived.counts(), {
            "plugins": expect["plugins"],
            "governed": expect["governed"],
            "canonical": expect["canonical"],
            "phase": expect["phase"],
        })
        self.assertEqual(list(derived.phase_ids), expect["phase_ids"])
        # The ungoverned directory in this specimen carries no ledger, so it is
        # a skill the tree holds and the contract does not govern.
        self.assertNotIn("plugins/quarry/skills/rubble", derived.governed)

    def test_the_invalid_specimens_refuse_with_their_declared_code(self):
        for name in (
            "duplicate-plugin-id",
            "missing-canonical-entry",
            "phase-outside-host",
        ):
            with self.subTest(specimen=name):
                specimen = load_specimen(name)
                with tempfile.TemporaryDirectory() as tmp:
                    with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                        read_specimen(Path(tmp), specimen)
                self.assertEqual(caught.exception.code, specimen["refusal"])


class RefusalTests(unittest.TestCase):
    """Each refusal is driven over a temporary tree it can actually happen in."""

    def setUp(self):
        self.specimen = load_specimen("valid-quarry")

    def _read(self, root: Path):
        return shoggoth_topology.read(
            root,
            phase_host=self.specimen["phase_host"],
            phase_host_entry=self.specimen["phase_host_entry"],
        )

    def test_a_symlinked_skill_directory_is_refused(self):
        """A ledger reachable only through a link must not be counted.

        Discovery walks with `O_NOFOLLOW`, so a skill tree entry that is a
        symbolic link is a refusal rather than a governed skill whose real
        location nobody checked.
        """
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            self.assertEqual(self._read(root).counts()["governed"], 6)
            outside = root / "elsewhere" / "smuggled"
            outside.mkdir(parents=True)
            (outside / shoggoth_topology.LEDGER_NAME).write_text("x\n", encoding="utf-8")
            (outside / shoggoth_topology.ENTRY_NAME).write_text("x\n", encoding="utf-8")
            os.symlink(outside, root / "plugins" / "quarry" / "skills" / "smuggled")
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "symlinked-entry")

    def test_a_symlinked_ledger_leaf_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            ledger = (
                root
                / "plugins"
                / "quarry"
                / "skills"
                / "granite"
                / shoggoth_topology.LEDGER_NAME
            )
            outside = root / "outside-ledger.md"
            outside.write_text("# outside\n", encoding="utf-8")
            ledger.unlink()
            ledger.symlink_to(outside)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "symlinked-entry")

    def test_a_dangling_symlinked_skills_root_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            skills = root / "plugins" / "quarry" / "skills"
            skills.rename(skills.with_name("skills-real"))
            skills.symlink_to(root / "missing-skills", target_is_directory=True)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "unsafe-path")

    def test_a_source_outside_plugins_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            for relative in (
                Path(".claude-plugin") / "marketplace.json",
                Path(".agents") / "plugins" / "marketplace.json",
            ):
                path = root / relative
                body = json.loads(path.read_text(encoding="utf-8"))
                entry = body["plugins"][0]
                if isinstance(entry["source"], str):
                    entry["source"] = "./elsewhere/lantern"
                else:
                    entry["source"]["path"] = "./elsewhere/lantern"
                write_json(path, body)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "path-outside-plugins")

    def test_manifests_that_disagree_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            path = root / ".agents" / "plugins" / "marketplace.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            body["plugins"].append(
                {
                    "name": "phantom",
                    "source": {"source": "local", "path": "./plugins/phantom"},
                }
            )
            write_json(path, body)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "manifest-disagreement")

    def test_a_manifest_the_tree_does_not_carry_is_refused(self):
        """Agreement runs in both directions, not manifest-to-tree alone."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plugins = list(self.specimen["plugins"])
            plugins.append({"id": "phantom", "skills": []})
            plant(root, plugins)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "manifest-disagreement")

    def test_a_duplicate_json_key_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            path = root / ".claude-plugin" / "marketplace.json"
            path.write_text(
                '{"name": "a", "name": "b", "plugins": []}\n', encoding="utf-8"
            )
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "duplicate-json-key")

    def test_manifest_plugin_ids_cannot_traverse(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            path = root / ".claude-plugin" / "marketplace.json"
            body = json.loads(path.read_text(encoding="utf-8"))
            body["plugins"][0]["name"] = "../../outside"
            write_json(path, body)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "invalid-plugin-id")

    def test_manifest_plugin_source_must_name_its_own_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            for relative in (
                Path(".claude-plugin") / "marketplace.json",
                Path(".agents") / "plugins" / "marketplace.json",
            ):
                path = root / relative
                body = json.loads(path.read_text(encoding="utf-8"))
                entry = body["plugins"][0]
                other = body["plugins"][1]["name"]
                if isinstance(entry["source"], str):
                    entry["source"] = f"./plugins/{other}"
                else:
                    entry["source"]["path"] = f"./plugins/{other}"
                write_json(path, body)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "path-outside-plugins")

    def test_a_tree_only_governed_plugin_is_a_manifest_disagreement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            where = root / "plugins" / "sundial" / "skills" / "sundial"
            where.mkdir(parents=True)
            (where / shoggoth_topology.LEDGER_NAME).write_text(
                "# ledger\n", encoding="utf-8"
            )
            (where / shoggoth_topology.ENTRY_NAME).write_text(
                "# skill\n", encoding="utf-8"
            )
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "manifest-disagreement")
        self.assertEqual(caught.exception.detail["tree-only"], ["sundial"])

    def test_tree_plugin_ids_are_validated_before_their_contents(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            (root / "plugins" / "Bad Plugin").mkdir()
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "invalid-plugin-id")

    def test_nested_governed_skill_is_discovered(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            where = root / "plugins" / "quarry" / "skills" / "nested" / "sundial"
            where.mkdir(parents=True)
            (where / shoggoth_topology.LEDGER_NAME).write_text(
                "# ledger\n", encoding="utf-8"
            )
            (where / shoggoth_topology.ENTRY_NAME).write_text(
                "# skill\n", encoding="utf-8"
            )
            derived = self._read(root)
        self.assertIn(
            "plugins/quarry/skills/nested/sundial", derived.governed
        )
        self.assertIn("sundial", derived.phase_ids)

    def test_skill_tree_depth_is_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            where = root / "plugins" / "quarry" / "skills"
            depth_limit = getattr(shoggoth_topology, "MAX_SKILL_DEPTH", 8)
            for depth in range(depth_limit + 1):
                where /= f"layer-{depth}"
            where.mkdir(parents=True)
            (where / shoggoth_topology.LEDGER_NAME).write_text(
                "# ledger\n", encoding="utf-8"
            )
            (where / shoggoth_topology.ENTRY_NAME).write_text(
                "# skill\n", encoding="utf-8"
            )
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "tree-oversized")

    def test_governed_skill_id_must_be_portable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            where = root / "plugins" / "quarry" / "skills" / "Bad Skill"
            where.mkdir()
            (where / shoggoth_topology.LEDGER_NAME).write_text(
                "# ledger\n", encoding="utf-8"
            )
            (where / shoggoth_topology.ENTRY_NAME).write_text(
                "# skill\n", encoding="utf-8"
            )
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "invalid-skill-id")

    def test_duplicate_governed_skill_ids_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            where = root / "plugins" / "lantern" / "skills" / "granite"
            where.mkdir(parents=True)
            (where / shoggoth_topology.LEDGER_NAME).write_text(
                "# ledger\n", encoding="utf-8"
            )
            (where / shoggoth_topology.ENTRY_NAME).write_text(
                "# skill\n", encoding="utf-8"
            )
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "duplicate-skill-id")

    def test_entry_cap_stops_iteration_before_consuming_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            wide = root / "plugins" / "quarry" / "skills"
            for index in range(shoggoth_topology.MAX_SKILLS_PER_PLUGIN + 2):
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
                    if self.count > shoggoth_topology.MAX_SKILLS_PER_PLUGIN + 1:
                        raise AssertionError(
                            "scanner consumed past the declared entry cap"
                        )
                    return next(self.iterator)

            with (
                patch.object(shoggoth_topology.os, "scandir", CappedScan),
                patch.object(
                    shoggoth_topology.os,
                    "listdir",
                    side_effect=AssertionError("unbounded listdir consumed the tree"),
                ),
            ):
                with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                    shoggoth_topology._governed_skills(root, "quarry")
        self.assertEqual(caught.exception.code, "tree-oversized")

    def test_manifest_identity_must_stay_stable_through_the_read(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            manifest = root / ".claude-plugin" / "marketplace.json"
            manifest_inode = manifest.stat().st_ino
            replacement = manifest.read_text(encoding="utf-8").replace(
                "quarry", "quarxy", 1
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
                    staged = manifest.with_suffix(".replacement")
                    staged.write_text(replacement, encoding="utf-8")
                    os.replace(staged, manifest)
                    changed = True
                return chunk

            with patch.object(shoggoth_topology.os, "read", racing_read):
                with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                    shoggoth_topology._read_confined_regular(
                        root,
                        shoggoth_topology.CLAUDE_MANIFEST,
                        label="claude manifest",
                    )
            self.assertTrue(changed)
        self.assertEqual(caught.exception.code, "file-changed-during-read")

    def test_platform_without_no_follow_flags_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for flag in ("O_NOFOLLOW", "O_DIRECTORY"):
                with self.subTest(flag=flag):
                    with patch.object(shoggoth_topology.os, flag, 0):
                        with self.assertRaises(
                            shoggoth_topology.TopologyError
                        ) as caught:
                            shoggoth_topology._open_confined_directory(root, ())
                    self.assertEqual(caught.exception.code, "unsupported-platform")

    def test_regular_file_open_is_nonblocking_before_type_check(self):
        if not getattr(shoggoth_topology.os, "O_NONBLOCK", 0):
            self.skipTest("platform does not expose O_NONBLOCK")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            plant(root, self.specimen["plugins"])
            real_open = shoggoth_topology.os.open
            checked_leaf = False

            def checked_open(target, flags, *arguments, **keywords):
                nonlocal checked_leaf
                if target == "marketplace.json":
                    checked_leaf = True
                    self.assertTrue(flags & shoggoth_topology.os.O_NONBLOCK)
                return real_open(target, flags, *arguments, **keywords)

            with patch.object(shoggoth_topology.os, "open", checked_open):
                shoggoth_topology._read_confined_regular(
                    root,
                    shoggoth_topology.CLAUDE_MANIFEST,
                    label="claude manifest",
                )
            self.assertTrue(checked_leaf)

    def test_a_symlinked_plugins_ancestor_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "root"
            root.mkdir()
            plant(root, self.specimen["plugins"])
            outside = Path(tmp) / "outside-plugins"
            (root / "plugins").rename(outside)
            (root / "plugins").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(shoggoth_topology.TopologyError) as caught:
                self._read(root)
        self.assertEqual(caught.exception.code, "unsafe-path")


class LiveTreeAgreementTests(unittest.TestCase):
    """Against this repository, agreement only. No case asserts a literal.

    Every assertion here relates one derived answer to another derived answer.
    A plugin landing changes both sides at once, which is the property the
    predecessor run's frozen comparison lacked.
    """

    @classmethod
    def setUpClass(cls):
        cls.live = shoggoth_topology.read(ROOT)

    def test_both_manifests_and_the_tree_return_the_same_plugin_set(self):
        claude = shoggoth_topology._declared(
            shoggoth_topology._load_manifest(
                ROOT, shoggoth_topology.CLAUDE_MANIFEST, label="claude manifest"
            ),
            label="claude manifest",
        )
        agents = shoggoth_topology._declared(
            shoggoth_topology._load_manifest(
                ROOT, shoggoth_topology.AGENTS_MANIFEST, label="agent manifest"
            ),
            label="agent manifest",
        )
        from_tree = sorted({path.split("/")[1] for path in self.live.governed})
        self.assertEqual(sorted(claude), sorted(agents))
        self.assertEqual(sorted(claude), from_tree)
        self.assertEqual(from_tree, list(self.live.plugins))

    def test_every_plugin_has_exactly_one_canonical_entry_skill(self):
        by_plugin: dict[str, list[str]] = {}
        for path in self.live.canonical:
            by_plugin.setdefault(path.split("/")[1], []).append(path)
        self.assertEqual(sorted(by_plugin), list(self.live.plugins))
        for plugin, paths in sorted(by_plugin.items()):
            with self.subTest(plugin=plugin):
                self.assertEqual(len(paths), 1)

    def test_fiat_is_the_canonical_entry_skill_for_hexaemeron(self):
        self.assertIn(
            f"plugins/{PHASE_HOST}/skills/{PHASE_HOST_ENTRY}", self.live.canonical
        )
        self.assertNotIn(
            f"plugins/{PHASE_HOST}/skills/{PHASE_HOST_ENTRY}", self.live.phase
        )
        for plugin in self.live.plugins:
            if plugin == PHASE_HOST:
                continue
            with self.subTest(plugin=plugin):
                self.assertIn(
                    f"plugins/{plugin}/skills/{plugin}", self.live.canonical
                )

    def test_canonical_plus_phase_equals_governed(self):
        self.assertEqual(
            sorted(set(self.live.canonical) | set(self.live.phase)),
            list(self.live.governed),
        )
        self.assertEqual(set(self.live.canonical) & set(self.live.phase), set())
        self.assertEqual(
            self.live.canonical_count + self.live.phase_count,
            self.live.governed_count,
        )

    def test_every_phase_skill_sits_under_the_phase_host(self):
        for path in self.live.phase:
            with self.subTest(path=path):
                self.assertEqual(path.split("/")[1], PHASE_HOST)

    def test_the_design_bridge_fixture_is_not_counted(self):
        """The fixture carries a real ledger and must still stay outside.

        It lives under `plugins/hexaemeron/tests/`, not `plugins/<id>/skills/`,
        so anchoring discovery at the skills directory is what excludes it. The
        assertion below fails if the fixture ever disappears, because a case
        that silently stops testing anything is worse than no case.
        """
        bridge = ROOT / DESIGN_BRIDGE
        self.assertTrue(
            (bridge / "plugins" / "example" / "skills" / "example" / "EVOLUTION.md").is_file(),
            "the design-bridge fixture this case guards has moved",
        )
        for path in self.live.governed:
            with self.subTest(path=path):
                self.assertFalse(path.startswith(DESIGN_BRIDGE))
        self.assertNotIn("example", self.live.plugins)


class DerivationMovesWithTheTreeTests(unittest.TestCase):
    """Adding a plugin must move exactly the derived numbers and nothing else."""

    def test_a_further_plugin_moves_only_the_derived_numbers(self):
        live = shoggoth_topology.read(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            mirror_live(root, live)
            before = shoggoth_topology.read(root)
            # The mirror must derive what the live tree derives, or the rest of
            # this case is measuring the mirror rather than the derivation.
            self.assertEqual(before.counts(), live.counts())

            added = "sundial"
            self.assertNotIn(added, before.plugins)
            # `plant` rewrites both manifests, so the whole set is replanted
            # with the new plugin appended rather than added to one side.
            grown = as_plant_spec(before)
            grown.append(
                {"id": added, "skills": [
                    {"name": added, "ledger": True, "entry": True}
                ]}
            )
            plant(root, grown)
            after = shoggoth_topology.read(root)

        self.assertEqual(after.plugin_count, before.plugin_count + 1)
        self.assertEqual(after.governed_count, before.governed_count + 1)
        self.assertEqual(after.canonical_count, before.canonical_count + 1)
        self.assertEqual(after.phase_count, before.phase_count)
        self.assertEqual(after.phase, before.phase)
        self.assertEqual(
            set(after.plugins) - set(before.plugins), {added}
        )
        self.assertEqual(
            set(after.canonical) - set(before.canonical),
            {f"plugins/{added}/skills/{added}"},
        )


if __name__ == "__main__":
    unittest.main()
