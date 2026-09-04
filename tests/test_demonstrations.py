"""The demonstration ledger contract and its refusals."""

from __future__ import annotations

import copy
import contextlib
import io
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from shoggoth_topology import read as discover_topology  # noqa: E402

try:
    import demonstrations  # noqa: E402
except ModuleNotFoundError as error:  # the Elenchus parent has no Step 2 checker
    if error.name != "demonstrations":
        raise
    demonstrations = None


FIXTURES = ROOT / "tests" / "fixtures" / "demonstrations"
POLICY = ROOT / "plugins" / "hexaemeron" / "skills" / "DEMONSTRATIONS.md"
ENTRY_COMMIT = "7b16284f95c63e723718a0708008db1243fa7480"
REFUSAL_SPECIMENS = (
    "duplicate-job.md",
    "duplicate-key.md",
    "missing-source.md",
    "missing-status.md",
    "mixed-as-real.md",
    "unknown-key.md",
    "unknown-status.md",
    "unsafe-argv.md",
)
SPECIMEN = (
    demonstrations.GovernedSkill(
        id="specimen", plugin_id="specimen", directory="plugins/specimen"
    )
    if demonstrations is not None
    else None
)


def fixture_record(name: str) -> dict:
    text = (FIXTURES / name).read_text(encoding="utf-8")
    return demonstrations.extract_record(text, where=name)


def check(
    record: dict,
    skill: demonstrations.GovernedSkill = SPECIMEN,
    *,
    verify_bytes: bool = False,
) -> dict:
    return demonstrations.check_record(
        ROOT if verify_bytes else None, skill, record, verify_bytes=verify_bytes
    )


class EntryParentGuardTests(unittest.TestCase):
    """Each refusal specimen is red before the Step 2 checker exists."""

    def test_each_refusal_specimen_requires_the_step_two_checker(self):
        for name in REFUSAL_SPECIMENS:
            with self.subTest(specimen=name):
                self.assertTrue((FIXTURES / name).is_file())
                self.assertIsNotNone(
                    demonstrations, f"{name} has no checker on the entry parent"
                )


@unittest.skipIf(demonstrations is None, "Step 2 checker is absent on the entry parent")
class LiveLedgerTests(unittest.TestCase):
    """Every governed skill carries exactly one checked record."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.topology = discover_topology(ROOT)
        cls.skills = demonstrations.governed_skills(ROOT)
        cls.records = demonstrations.load_records(ROOT)

    def test_discovery_parity_with_the_topology_reader(self):
        directories = set(self.topology.governed)
        self.assertEqual(set(self.records), directories)
        self.assertEqual({skill.directory for skill in self.skills}, directories)

    def test_every_record_names_its_own_owner(self):
        for skill in self.skills:
            record = self.records[skill.directory]
            self.assertEqual(record["skill"], skill.id, skill.directory)
            self.assertEqual(record["plugin"], skill.plugin_id, skill.directory)

    def test_every_relative_ledger_link_resolves_from_its_own_directory(self):
        for skill in self.skills:
            ledger = ROOT / skill.directory / demonstrations.LEDGER_NAME
            for target in re.findall(
                r"\[[^]]+\]\(([^)]+)\)", ledger.read_text(encoding="utf-8")
            ):
                with self.subTest(ledger=skill.directory, target=target):
                    self.assertNotIn("://", target)
                    relative = target.split("#", 1)[0]
                    self.assertTrue((ledger.parent / relative).resolve().exists())

    def test_dokimasia_is_real_data_with_its_primary_input_caveat(self):
        record = self.records["plugins/dokimasia/skills/dokimasia"]
        self.assertEqual(record["status"], "real-data")
        self.assertIn("not preserved", record["non_claim"])
        self.assertIn("does not regenerate", record["non_claim"])

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
        for skill in self.skills:
            demo_version = self.records[skill.directory]["frontier"]["version"]
            evolution = (ROOT / skill.directory / "EVOLUTION.md").read_text(encoding="utf-8")
            self.assertIn("-demo-v", demo_version)
            self.assertNotIn(demo_version, evolution, skill.directory)

    def test_every_evolution_ledger_is_byte_identical_to_the_entry_tree(self):
        for skill in self.skills:
            relative = f"{skill.directory}/EVOLUTION.md"
            entry = subprocess.run(
                ["git", "show", f"{ENTRY_COMMIT}:{relative}"],
                cwd=ROOT,
                capture_output=True,
                check=True,
                timeout=120,
            ).stdout
            self.assertEqual((ROOT / relative).read_bytes(), entry, relative)

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


@unittest.skipIf(demonstrations is None, "Step 2 checker is absent on the entry parent")
class ContractTests(unittest.TestCase):
    """The committed policy, schema, and checker name one closed contract."""

    def test_the_committed_schema_is_closed_and_loaded(self):
        schema = demonstrations.load_schema(ROOT)
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(
            set(schema["required"]), set(demonstrations.EXPECTED_RECORD_KEYS)
        )
        self.assertEqual(
            set(schema["properties"]), set(demonstrations.EXPECTED_RECORD_KEYS)
        )

    def test_the_policy_and_checker_have_the_same_refusal_catalogue(self):
        text = POLICY.read_text(encoding="utf-8")
        section = text.split("<!-- refusal-catalogue:start -->", 1)[1].split(
            "<!-- refusal-catalogue:end -->", 1
        )[0]
        policy_codes = re.findall(r"^- `(?P<code>D[0-9]{3})` -- ", section, re.MULTILINE)
        self.assertEqual(len(policy_codes), len(set(policy_codes)))
        self.assertEqual(len(policy_codes), len(demonstrations.REFUSALS))
        self.assertEqual(set(policy_codes), set(demonstrations.REFUSALS))

    def test_the_schema_itself_refuses_an_unknown_key(self):
        record = fixture_record("unknown-key.md")
        schema = demonstrations.load_schema(ROOT)
        with self.assertRaises(demonstrations._SchemaMismatch):
            demonstrations._validate_schema(
                record, schema, schema, where="unknown-key.md"
            )


@unittest.skipIf(demonstrations is None, "Step 2 checker is absent on the entry parent")
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

    def test_a_missing_status_is_refused_not_inferred(self):
        record = fixture_record("missing-status.md")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D005", str(caught.exception))

    def test_a_status_outside_the_closed_five_is_refused(self):
        record = fixture_record("unknown-status.md")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record)
        self.assertIn("D008", str(caught.exception))

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


@unittest.skipIf(demonstrations is None, "Step 2 checker is absent on the entry parent")
class ShapeTests(unittest.TestCase):
    """The record is a closed object with checked leaves."""

    def setUp(self):
        self.valid = fixture_record("valid-ledger.md")

    def test_the_valid_fixture_passes(self):
        self.assertEqual(check(self.valid)["claim_id"], "specimen-chain-replay")

    def test_an_unknown_key_is_refused(self):
        record = fixture_record("unknown-key.md")
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
        other = demonstrations.GovernedSkill(
            id="other", plugin_id="specimen", directory="plugins/specimen"
        )
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(self.valid, other)
        self.assertIn("D007", str(caught.exception))

    def test_a_duplicate_claim_id_is_refused(self):
        first = check(fixture_record("valid-ledger.md"))
        second = fixture_record("duplicate-job.md")
        checked = check(
            second,
            demonstrations.GovernedSkill(
                id="second", plugin_id="second", directory="plugins/second"
            ),
        )
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


@unittest.skipIf(demonstrations is None, "Step 2 checker is absent on the entry parent")
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

    def test_a_fifo_ledger_is_refused_without_blocking(self):
        with tempfile.TemporaryDirectory() as name:
            root = self._tree(type("S", (), {"name": name})())
            os.mkfifo(root / "plugins" / "specimen" / "DEMONSTRATION.md")
            with self.assertRaises(demonstrations.DemonstrationError) as caught:
                demonstrations.read_ledger(root, "plugins/specimen")
            self.assertIn("D001", str(caught.exception))

    def test_a_symlinked_schema_is_refused(self):
        with tempfile.TemporaryDirectory() as name:
            root = pathlib.Path(name)
            (root / "schemas").mkdir()
            os.symlink(
                ROOT / demonstrations.SCHEMA_PATH,
                root / demonstrations.SCHEMA_PATH,
            )
            with self.assertRaises(demonstrations.DemonstrationError) as caught:
                demonstrations.load_schema(root)
            self.assertIn("D060", str(caught.exception))

    def test_two_record_fences_are_refused(self):
        text = (FIXTURES / "valid-ledger.md").read_text(encoding="utf-8")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.extract_record(text + text, where="doubled")
        self.assertIn("D003", str(caught.exception))

    def test_no_record_fence_is_refused(self):
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.extract_record("# empty\n", where="empty")
        self.assertIn("D003", str(caught.exception))

    def test_excessive_json_depth_is_refused(self):
        nested = "[]"
        for _ in range(demonstrations.MAX_JSON_DEPTH + 1):
            nested = f"[{nested}]"
        text = f"{demonstrations.FENCE_OPEN}\n{{\"too_deep\":{nested}}}\n```\n"
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.extract_record(text, where="too-deep")
        self.assertIn("D004", str(caught.exception))


@unittest.skipIf(demonstrations is None, "Step 2 checker is absent on the entry parent")
class CommandTests(unittest.TestCase):
    """The two published commands behave as the contract says."""

    def test_check_reports_every_record_and_exits_zero(self):
        proc = subprocess.run(
            [sys.executable, "scripts/demonstrations.py", "check", "--root", "."],
            cwd=ROOT, capture_output=True, text=True, timeout=300,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        count = len(demonstrations.governed_skills(ROOT))
        self.assertIn(f"{count} record(s)", proc.stdout)
        events = [
            json.loads(line)
            for line in proc.stdout.splitlines()
            if line.startswith("{")
        ]
        self.assertEqual(len(events), count)
        self.assertEqual(
            {event["event"] for event in events},
            {"demonstration.public_claim.checked"},
        )

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
        events = [
            json.loads(line)
            for line in proc.stdout.splitlines()
            if line.startswith("{")
        ]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event"], "demonstration.frontier.selection")

    def test_no_eligible_demo_job_is_a_bounded_event_not_silence(self):
        record = fixture_record("valid-ledger.md")
        frontier = dict(record["frontier"], status="mature", next="None -- mature")
        frontier["sha256"] = demonstrations.frontier_digest(
            frontier["status"],
            frontier["revision"],
            frontier["current"],
            frontier["next"],
        )
        record["frontier"] = frontier
        args = type("Args", (), {"root": ROOT, "lane": "demo"})()
        output = io.StringIO()
        with mock.patch.object(
            demonstrations, "load_records", return_value={"plugins/specimen": record}
        ), contextlib.redirect_stdout(output):
            self.assertEqual(demonstrations.command_frontier(args), 0)
        events = [
            json.loads(line)
            for line in output.getvalue().splitlines()
            if line.startswith("{")
        ]
        self.assertEqual(
            events,
            [
                {
                    "eligible": 0,
                    "event": "demonstration.frontier.selection",
                    "lane": "demo",
                    "outcome": "none",
                    "records": 1,
                }
            ],
        )

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
