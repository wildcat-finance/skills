"""The demonstration ledger contract and its refusals."""

from __future__ import annotations

import copy
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import demonstrations  # noqa: E402
from shoggoth_topology import GovernedSkill, discover_topology  # noqa: E402


FIXTURES = ROOT / "tests" / "fixtures" / "demonstrations"
SPECIMEN = GovernedSkill(id="specimen", plugin_id="specimen", directory="plugins/specimen")


def fixture_record(name: str) -> dict:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    return demonstrations.extract_record(text, where=name)


def check(record: dict, skill: GovernedSkill = SPECIMEN, *, verify_bytes: bool = False) -> dict:
    return demonstrations.check_record(
        ROOT if verify_bytes else None, skill, record, verify_bytes=verify_bytes
    )


class LiveLedgerTests(unittest.TestCase):
    """Every governed skill carries exactly one checked record."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.topology = discover_topology(ROOT)
        cls.records = demonstrations.load_records(ROOT)

    def test_discovery_parity_with_the_topology_reader(self):
        directories = {skill.directory for skill in self.topology.governed_skills}
        self.assertEqual(set(self.records), directories)
        self.assertEqual(len(self.records), 26)

    def test_every_record_names_its_own_owner(self):
        for skill in self.topology.governed_skills:
            record = self.records[skill.directory]
            self.assertEqual(record["skill"], skill.id, skill.directory)
            self.assertEqual(record["plugin"], skill.plugin_id, skill.directory)

    def test_every_frontier_digest_recomputes(self):
        for directory, record in self.records.items():
            frontier = record["frontier"]
            self.assertEqual(
                frontier["sha256"],
                demonstrations.frontier_digest(
                    frontier["status"],
                    frontier["revision"],
                    frontier["current"],
                    frontier["next"],
                ),
                directory,
            )

    def test_claim_ids_are_unique(self):
        claims = [record["claim_id"] for record in self.records.values()]
        self.assertEqual(len(claims), len(set(claims)))

    def test_the_demo_lane_is_independent_of_the_behaviour_lane(self):
        for skill in self.topology.governed_skills:
            demo_version = self.records[skill.directory]["frontier"]["version"]
            evolution = (ROOT / skill.directory / "EVOLUTION.md").read_text(encoding="utf-8")
            self.assertIn("-demo-v", demo_version)
            self.assertNotIn(demo_version, evolution, skill.directory)

    def test_the_ranking_is_deterministic_and_gap_first(self):
        ranked = demonstrations.rank_demo_frontier(self.records)
        keys = [
            (-demonstrations.STATUS_GAP[record["status"]], record["skill"])
            for record in ranked
        ]
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(
            ranked, demonstrations.rank_demo_frontier(dict(reversed(list(self.records.items()))))
        )

    def test_every_status_value_the_tree_uses_is_closed(self):
        for record in self.records.values():
            self.assertIn(record["status"], demonstrations.STATUSES)


class StatusTests(unittest.TestCase):
    """All five status values are accepted, and inflation is refused."""

    def setUp(self):
        self.valid = fixture_record("valid-ledger.md")

    def test_the_five_status_values_are_accepted(self):
        for status in demonstrations.STATUSES:
            record = copy.deepcopy(self.valid)
            record["status"] = status
            if status not in demonstrations.EXECUTABLE_STATUSES:
                record["sources"] = []
                record["commands"] = []
                record["observations"] = []
            if status == "mixed":
                record["sources"] = record["sources"] + [
                    {
                        "id": "model-answers",
                        "class": "model-record",
                        "path": "tests/fixtures/demonstrations/valid-ledger.md",
                        "sha256": "0" * 64,
                    }
                ]
            if status == "constructed":
                record["sources"] = [
                    {
                        "id": "corpus",
                        "class": "fixture",
                        "path": "tests/fixtures/demonstrations/valid-ledger.md",
                        "sha256": "0" * 64,
                    }
                ]
            check(record)

    def test_a_material_model_record_refuses_real_data(self):
        record = fixture_record("mixed-as-real.md")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D017", str(caught.exception))

    def test_mixed_requires_both_kinds_of_source(self):
        record = copy.deepcopy(self.valid)
        record["status"] = "mixed"
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D018", str(caught.exception))

    def test_constructed_refuses_a_preserved_source(self):
        record = copy.deepcopy(self.valid)
        record["status"] = "constructed"
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D019", str(caught.exception))

    def test_an_absent_record_carries_no_executable_path(self):
        record = copy.deepcopy(self.valid)
        record["status"] = "absent"
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D016", str(caught.exception))


class ShapeTests(unittest.TestCase):
    """The record is a closed object with checked leaves."""

    def setUp(self):
        self.valid = fixture_record("valid-ledger.md")

    def test_the_valid_fixture_passes(self):
        self.assertEqual(check(self.valid)["claim_id"], "specimen-chain-replay")

    def test_an_unknown_key_is_refused(self):
        record = copy.deepcopy(self.valid)
        record["notes"] = "extra"
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D005", str(caught.exception))

    def test_a_missing_key_is_refused(self):
        record = copy.deepcopy(self.valid)
        del record["non_claim"]
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D005", str(caught.exception))

    def test_a_duplicate_json_key_is_refused(self):
        text = (FIXTURES / "duplicate-key.md").read_text(encoding="utf-8")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.extract_record(text, where="duplicate-key.md")
        self.assertIn("D004", str(caught.exception))

    def test_an_unsafe_argv_word_is_refused(self):
        record = fixture_record("unsafe-argv.md")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D031", str(caught.exception))

    def test_a_missing_declared_source_is_refused(self):
        record = fixture_record("missing-source.md")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record, verify_bytes=True)
        self.assertIn("D025", str(caught.exception))

    def test_a_wrong_source_digest_is_refused(self):
        record = copy.deepcopy(self.valid)
        record["status"] = "constructed"
        record["sources"] = [
            {
                "id": "corpus",
                "class": "fixture",
                "path": "tests/fixtures/demonstrations/valid-ledger.md",
                "sha256": "0" * 64,
            }
        ]
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record, verify_bytes=True)
        self.assertIn("D026", str(caught.exception))

    def test_a_tampered_frontier_digest_is_refused(self):
        record = copy.deepcopy(self.valid)
        record["frontier"] = dict(record["frontier"], sha256="f" * 64)
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D044", str(caught.exception))

    def test_a_mature_frontier_holds_no_next_job(self):
        record = copy.deepcopy(self.valid)
        frontier = dict(record["frontier"], status="mature")
        frontier["sha256"] = demonstrations.frontier_digest(
            "mature", frontier["revision"], frontier["current"], frontier["next"]
        )
        record["frontier"] = frontier
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D043", str(caught.exception))

    def test_a_foreign_owner_is_refused(self):
        other = GovernedSkill(id="other", plugin_id="specimen", directory="plugins/specimen")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(self.valid, other)
        self.assertIn("D007", str(caught.exception))

    def test_a_duplicate_claim_id_is_refused(self):
        first = check(fixture_record("valid-ledger.md"))
        second = fixture_record("duplicate-job.md")
        checked = check(second, GovernedSkill(id="second", plugin_id="second", directory="plugins/second"))
        self.assertEqual(first["claim_id"], checked["claim_id"])
        seen = {first["claim_id"]: "plugins/specimen"}
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations._require(
                checked["claim_id"] not in seen,
                "D050",
                f"claim id {checked['claim_id']!r} is claimed twice",
            )
        self.assertIn("D050", str(caught.exception))

    def test_an_absent_record_cannot_hold_a_mature_demo_frontier(self):
        record = copy.deepcopy(self.valid)
        record["status"] = "absent"
        record["sources"] = []
        record["commands"] = []
        record["observations"] = []
        frontier = dict(record["frontier"], status="mature", next="None -- mature")
        frontier["sha256"] = demonstrations.frontier_digest(
            "mature", frontier["revision"], frontier["current"], frontier["next"]
        )
        record["frontier"] = frontier
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D045", str(caught.exception))

    def test_a_not_applicable_record_may_hold_a_mature_demo_frontier(self):
        record = copy.deepcopy(self.valid)
        record["status"] = "not-applicable"
        record["sources"] = []
        record["commands"] = []
        record["observations"] = []
        frontier = dict(record["frontier"], status="mature", next="None -- mature")
        frontier["sha256"] = demonstrations.frontier_digest(
            "mature", frontier["revision"], frontier["current"], frontier["next"]
        )
        record["frontier"] = frontier
        self.assertEqual(check(record)["status"], "not-applicable")

    def test_the_run_source_budget_bounds_every_read_together(self):
        budget = demonstrations._Budget(maximum=16)
        record = copy.deepcopy(self.valid)
        record["status"] = "constructed"
        record["sources"] = [
            {
                "id": "corpus",
                "class": "fixture",
                "path": "tests/fixtures/demonstrations/valid-ledger.md",
                "sha256": "0" * 64,
            }
        ]
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.check_record(
                ROOT, SPECIMEN, record, verify_bytes=True, budget=budget
            )
        self.assertIn("D028", str(caught.exception))

    def test_a_symlinked_source_refuses_before_it_spends_the_budget(self):
        budget = demonstrations._Budget(maximum=64)
        with tempfile.TemporaryDirectory() as name:
            root = pathlib.Path(name)
            (root / "corpus").mkdir()
            target = root / "large.json"
            target.write_bytes(b"{}" + b" " * 4096)
            os.symlink(target, root / "corpus" / "linked.json")
            record = copy.deepcopy(self.valid)
            record["status"] = "constructed"
            record["sources"] = [
                {
                    "id": "corpus",
                    "class": "fixture",
                    "path": "corpus/linked.json",
                    "sha256": "0" * 64,
                }
            ]
            with self.assertRaises(demonstrations.DemonstrationError) as caught:
                demonstrations.check_record(
                    root, SPECIMEN, record, verify_bytes=True, budget=budget
                )
            self.assertIn("D025", str(caught.exception))
        self.assertEqual(budget.remaining, 64)

    def test_the_default_budget_covers_the_whole_live_check(self):
        self.assertGreater(
            demonstrations.MAX_RUN_SOURCE_BYTES, demonstrations.MAX_SOURCE_BYTES
        )
        budget = demonstrations._Budget()
        budget.spend(demonstrations.MAX_RUN_SOURCE_BYTES, where="whole budget")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            budget.spend(1, where="one byte past it")
        self.assertIn("D028", str(caught.exception))

    def test_an_allowlisted_endpoint_never_records_a_secret_value(self):
        record = copy.deepcopy(self.valid)
        record["network"] = {
            "policy": "allowlisted",
            "endpoints": ["https://example.invalid/rpc"],
            "secret_env": ["WILDCAT_RPC_TOKEN"],
        }
        self.assertEqual(check(record)["network"]["secret_env"], ["WILDCAT_RPC_TOKEN"])
        record["network"] = {"policy": "allowlisted", "endpoints": ["http://example.invalid"]}
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D011", str(caught.exception))


class BoundaryTests(unittest.TestCase):
    """Reads are bounded, no-follow, and single-record."""

    def _tree(self, stack: tempfile.TemporaryDirectory) -> pathlib.Path:
        root = pathlib.Path(stack.name)
        (root / "plugins" / "specimen").mkdir(parents=True)
        return root

    def test_a_symlinked_ledger_is_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = self._tree(type("S", (), {"name": name})())
            target = root / "elsewhere.md"
            target.write_text("# elsewhere\n", encoding="utf-8")
            os.symlink(target, root / "plugins" / "specimen" / "DEMONSTRATION.md")
            with self.assertRaises(demonstrations.DemonstrationError) as caught:
                demonstrations.read_ledger(root, "plugins/specimen")
            self.assertIn("D001", str(caught.exception))

    def test_a_missing_ledger_is_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = self._tree(type("S", (), {"name": name})())
            with self.assertRaises(demonstrations.DemonstrationError) as caught:
                demonstrations.read_ledger(root, "plugins/specimen")
            self.assertIn("D001", str(caught.exception))

    def test_an_oversized_ledger_is_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = self._tree(type("S", (), {"name": name})())
            ledger = root / "plugins" / "specimen" / "DEMONSTRATION.md"
            ledger.write_bytes(b"#" * (demonstrations.MAX_LEDGER_BYTES + 1))
            with self.assertRaises(demonstrations.DemonstrationError) as caught:
                demonstrations.read_ledger(root, "plugins/specimen")
            self.assertIn("D001", str(caught.exception))

    def test_two_record_fences_are_refused(self):
        text = (FIXTURES / "valid-ledger.md").read_text(encoding="utf-8")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.extract_record(text + text, where="doubled")
        self.assertIn("D003", str(caught.exception))

    def test_no_record_fence_is_refused(self):
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.extract_record("# empty\n", where="empty")
        self.assertIn("D003", str(caught.exception))


class CommandTests(unittest.TestCase):
    """The two published commands behave as the contract says."""

    def test_check_reports_every_record_and_exits_zero(self):
        proc = subprocess.run(
            [sys.executable, "scripts/demonstrations.py", "check", "--root", "."],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("26 record(s)", proc.stdout)

    def test_the_demo_lane_reads_only_demonstration_ledgers(self):
        proc = subprocess.run(
            [sys.executable, "scripts/demonstrations.py", "frontier",
             "--root", ".", "--lane", "demo", "--dry-run"],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("DEMONSTRATION.md only", proc.stdout)
        self.assertIn("read-only", proc.stdout)
        self.assertNotIn("EVOLUTION.md", proc.stdout)

    def test_the_demo_lane_refuses_another_lane(self):
        proc = subprocess.run(
            [sys.executable, "scripts/demonstrations.py", "frontier",
             "--root", ".", "--lane", "behaviour", "--dry-run"],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        self.assertNotEqual(proc.returncode, 0)

    def test_the_dry_run_leaves_git_and_kronos_untouched(self):
        before = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT,
            capture_output=True, text=True, timeout=120,
        ).stdout
        kronos = ROOT / ".kronos"
        existed = kronos.exists()
        subprocess.run(
            [sys.executable, "scripts/demonstrations.py", "frontier",
             "--root", ".", "--lane", "demo", "--dry-run"],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        after = subprocess.run(
            ["git", "status", "--porcelain"], cwd=ROOT,
            capture_output=True, text=True, timeout=120,
        ).stdout
        self.assertEqual(before, after)
        self.assertEqual(existed, kronos.exists())

    def test_the_module_starts_no_process_of_its_own(self):
        source = (ROOT / "scripts" / "demonstrations.py").read_text(encoding="utf-8")
        for banned in ("subprocess", "os.system", "os.exec", "socket", "urllib"):
            self.assertNotIn(banned, source)


if __name__ == "__main__":
    unittest.main()
