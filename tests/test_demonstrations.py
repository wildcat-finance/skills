"""The demonstration ledger contract and its refusals."""

from __future__ import annotations

import copy
import contextlib
import hashlib
import io
import json
import os
import pathlib
import platform
import re
import subprocess
import sys
import tempfile
import time
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
RUNNER_SPECIMENS = (
    "network-attempt.md",
    "oversized-output.md",
    "timeout.md",
    "partial-report.md",
    "stale-source.md",
    "traversing-report-path.md",
    "empty-selection.md",
)
RUNNER = demonstrations is not None and hasattr(demonstrations, "run_demonstrations")
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
    """Each refusal specimen is red before the checker or runner it needs exists."""

    def test_each_refusal_specimen_requires_the_step_two_checker(self):
        for name in REFUSAL_SPECIMENS:
            with self.subTest(specimen=name):
                self.assertTrue((FIXTURES / name).is_file())
                self.assertIsNotNone(
                    demonstrations, f"{name} has no checker on the entry parent"
                )

    def test_each_runner_specimen_requires_the_step_three_runner(self):
        for name in RUNNER_SPECIMENS:
            with self.subTest(specimen=name):
                self.assertTrue((FIXTURES / name).is_file())
                self.assertTrue(RUNNER, f"{name} has no runner on the entry parent")


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

    def test_every_evolution_ledger_is_byte_identical_across_the_demo_lane(self):
        # The entry tree is the tree these commands start from. Pinning a
        # commit id here instead would freeze every behaviour ledger against
        # one historical tree and fail the root suite on the next legitimate
        # EVOLUTION.md advance anywhere in the repository.
        ledgers = {
            skill.directory: (ROOT / skill.directory / "EVOLUTION.md").read_bytes()
            for skill in self.skills
        }
        self.assertTrue(ledgers)
        for argv in (
            ["check", "--root", "."],
            ["frontier", "--root", ".", "--lane", "demo", "--dry-run"],
        ):
            proc = subprocess.run(
                [sys.executable, "scripts/demonstrations.py", *argv],
                cwd=ROOT, capture_output=True, text=True, timeout=300,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)
        for directory, entry in ledgers.items():
            self.assertEqual(
                (ROOT / directory / "EVOLUTION.md").read_bytes(), entry, directory
            )

    def test_no_live_tree_assertion_pins_a_commit_id(self):
        source = pathlib.Path(__file__).read_text(encoding="utf-8")
        self.assertNotRegex(source, r"\b[0-9a-f]{40}\b")

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

    def test_every_ledger_cites_the_decision_record_by_stable_identity(self):
        # A numbered `docs/decisions/ADR-NNN-<slug>.md` path dangles the moment
        # the integration composition assigns the record its final number; the
        # `adr/<slug>` identity survives that assignment.
        identity = "`adr/govern-real-data-demonstrations-separately`"
        documents = [POLICY] + [
            ROOT / skill.directory / demonstrations.LEDGER_NAME
            for skill in demonstrations.governed_skills(ROOT)
        ]
        self.assertGreater(len(documents), 1)
        for document in documents:
            text = document.read_text(encoding="utf-8")
            with self.subTest(document=str(document.relative_to(ROOT))):
                self.assertIn(identity, text)
                self.assertNotRegex(text, r"ADR-[0-9]{3}")

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

    def test_check_and_frontier_start_no_process_of_their_own(self):
        # Only `run` executes anything. The checker and the ranking read files.
        source = (ROOT / "scripts" / "demonstrations.py").read_text(encoding="utf-8")
        for banned in ("os.system", "os.exec", "urllib", "shell=True"):
            self.assertNotIn(banned, source)
        check_args = type("Args", (), {"root": ROOT})()
        frontier_args = type("Args", (), {"root": ROOT, "lane": "demo"})()
        with mock.patch.object(
            subprocess, "Popen", side_effect=AssertionError("a process was started")
        ), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(demonstrations.command_check(check_args), 0)
            self.assertEqual(demonstrations.command_frontier(frontier_args), 0)


def _events(output: str) -> list[dict]:
    return [json.loads(line) for line in output.splitlines() if line.startswith("{")]


def _skill(name: str = "specimen") -> "demonstrations.GovernedSkill":
    return demonstrations.GovernedSkill(id=name, plugin_id=name, directory=f"plugins/{name}")


@unittest.skipUnless(RUNNER, "Step 3 runner is absent on the entry parent")
class RunnerHarness(unittest.TestCase):
    """Shared fixtures for driving the runner through its Python entry point."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.out = pathlib.Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        self.interpreter = {
            "executable": sys.executable,
            "version": platform.python_version(),
            "pinned": platform.python_version(),
        }

    def run_records(self, records, *, report="report.json", repeat=1, ceiling_ms=None,
                    mode="record", root=ROOT):
        output = io.StringIO()
        target = self.out / report
        with contextlib.redirect_stdout(output):
            code, payload = demonstrations.run_demonstrations(
                root, records, report=str(target), output_root=self.out,
                repeat=repeat, ceiling_ms=ceiling_ms, correlation_id="c0ffee",
                interpreter=self.interpreter, mode=mode,
            )
        return code, payload, _events(output.getvalue()), target

    def run_specimen(self, name, **kwargs):
        record = check(fixture_record(name))
        return self.run_records([(SPECIMEN, record)], **kwargs)

    def run_argv(self, argv, observations, *, timeout_seconds=30, environ=None):
        record = check(fixture_record("valid-ledger.md"))
        record["timeout_seconds"] = timeout_seconds
        record["commands"] = [{"id": "run", "argv": argv, "expect_exit": 0}]
        record["observations"] = observations
        record = check(record)
        if environ is None:
            return self.run_records([(SPECIMEN, record)])
        with mock.patch.dict(os.environ, environ, clear=False):
            return self.run_records([(SPECIMEN, record)])


class RunnerSpecimenTests(RunnerHarness):
    """Each named refusal condition is refused, never skipped or passed."""

    def test_a_child_that_opens_a_socket_is_refused_even_when_it_exits_zero(self):
        code, payload, events, _target = self.run_specimen("network-attempt.md")
        self.assertEqual(code, 2)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D074")
        command = entry["repetitions"][0]["commands"][0]
        self.assertEqual(command["exit"], 0)
        self.assertTrue(command["network_attempt"])
        self.assertIn("swallowed", command["stdout_tail"])
        self.assertEqual(
            [event["code"] for event in events if event["event"] == "demonstration.refused"],
            ["D074"],
        )

    def test_a_child_past_the_output_cap_is_truncated_and_refused(self):
        code, payload, _events, _target = self.run_specimen("oversized-output.md")
        self.assertEqual(code, 2)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D077")
        command = entry["repetitions"][0]["commands"][0]
        self.assertTrue(command["truncated"])
        self.assertEqual(command["stdout_bytes"], demonstrations.MAX_OUTPUT_BYTES)
        self.assertLessEqual(len(command["stdout_tail"]), demonstrations.MAX_OUTPUT_TAIL)

    def test_a_child_past_its_timeout_is_killed_with_its_process_group(self):
        code, payload, _events, _target = self.run_specimen("timeout.md")
        self.assertEqual(code, 2)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D076")
        command = entry["repetitions"][0]["commands"][0]
        self.assertTrue(command["timed_out"])
        self.assertLessEqual(command["timeout_ms"], 1000)
        grandchild = int(command["stdout_tail"].strip())
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                os.kill(grandchild, 0)
            except ProcessLookupError:
                break
            time.sleep(0.05)
        else:
            self.fail(f"grandchild {grandchild} survived the process-group teardown")

    def test_a_partial_report_is_never_published(self):
        with mock.patch.object(os, "link", side_effect=OSError("disk full")):
            with self.assertRaises(demonstrations.RunRefusal) as caught:
                self.run_specimen("partial-report.md")
        self.assertEqual(caught.exception.code, "D081")
        self.assertFalse((self.out / "report.json").exists())
        self.assertEqual(
            [path.name for path in self.out.iterdir() if ".partial-" in path.name], []
        )

    def test_a_stale_source_is_refused_before_execution(self):
        record = fixture_record("stale-source.md")
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            check(record, verify_bytes=True)
        self.assertIn("D026", str(caught.exception))
        stderr = io.StringIO()
        with mock.patch.object(
            demonstrations, "load_records", side_effect=demonstrations.DemonstrationError(
                "D026 sources[0].path digest differs"
            )
        ), mock.patch.object(
            subprocess, "Popen", side_effect=AssertionError("a command started")
        ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(stderr):
            code = demonstrations.main([
                "run", "--root", str(ROOT), "--record", "plugins/specimen",
                "--report", str(self.out / "stale.json"), "--output-root", str(self.out),
            ])
        self.assertEqual(code, 2)
        self.assertIn("D026", stderr.getvalue())
        self.assertFalse((self.out / "stale.json").exists())

    def test_a_traversing_or_escaping_or_existing_report_path_is_refused(self):
        record = check(fixture_record("traversing-report-path.md"))
        (self.out / "taken.json").write_text("{}", encoding="utf-8")
        outside = pathlib.Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        for report in (
            str(self.out / ".." / "escape.json"),
            str(self.out / "nested" / ".." / ".." / "escape.json"),
            str(outside / "escape.json"),
            str(self.out / "taken.json"),
            str(self.out),
        ):
            with self.subTest(report=report):
                with mock.patch.object(
                    subprocess, "Popen", side_effect=AssertionError("a command started")
                ), contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(demonstrations.RunRefusal) as caught:
                        demonstrations.run_demonstrations(
                            ROOT, [(SPECIMEN, record)], report=report, output_root=self.out,
                            repeat=1, ceiling_ms=None, correlation_id="c0ffee",
                            interpreter=self.interpreter, mode="record",
                        )
                self.assertEqual(caught.exception.code, "D080")
        self.assertFalse((self.out.parent / "escape.json").exists())
        self.assertFalse((outside / "escape.json").exists())

    def test_an_empty_selection_exits_nonzero_and_is_visible(self):
        record = check(fixture_record("empty-selection.md"))
        self.assertEqual(record["status"], "absent")
        output, stderr = io.StringIO(), io.StringIO()
        with mock.patch.object(
            demonstrations, "load_records", return_value={"plugins/specimen": record}
        ), mock.patch.object(
            demonstrations, "governed_skills", return_value=(SPECIMEN,)
        ), contextlib.redirect_stdout(output), contextlib.redirect_stderr(stderr):
            code = demonstrations.main([
                "run", "--root", str(ROOT), "--record", "plugins/specimen",
                "--report", str(self.out / "empty.json"), "--output-root", str(self.out),
            ])
        self.assertEqual(code, 2)
        self.assertIn("D070", stderr.getvalue())
        events = _events(output.getvalue())
        selected = [event for event in events if event["event"] == "demonstration.selected"]
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0]["count"], 0)
        refused = [event for event in events if event["event"] == "demonstration.refused"]
        self.assertEqual([event["code"] for event in refused], ["D070"])
        self.assertEqual(selected[0]["correlation_id"], refused[0]["correlation_id"])
        self.assertFalse((self.out / "empty.json").exists())


class RunnerBoundaryTests(RunnerHarness):
    """The runner's subprocess, environment, path and interpreter boundaries."""

    def test_shell_metacharacters_are_passed_literally(self):
        hostile = "$HOME; echo pwned > /tmp/pwned `id` $(id) | cat"
        code, payload, _events, _target = self.run_argv(
            ["python3", "-c", "import sys; print(sys.argv[1])", hostile],
            [f"run: line {json.dumps(hostile)}"],
        )
        self.assertEqual(code, 0, payload["demonstrations"][0]["refusal"])

    def test_only_the_reserved_work_token_is_expanded(self):
        code, payload, _events, _target = self.run_argv(
            [
                "python3", "-c",
                "import os, sys; print(os.path.isdir(os.path.dirname(sys.argv[1]))); print(sys.argv[2])",
                "{work}/credit-history-v0", "{other}",
            ],
            ['run: line "True"', 'run: line "{other}"'],
        )
        self.assertEqual(code, 0, payload["demonstrations"][0]["refusal"])
        command = payload["demonstrations"][0]["repetitions"][0]["commands"][0]
        self.assertEqual(command["argv"][3], "{work}/credit-history-v0")
        self.assertTrue(payload["work_root_removed"])

    def test_credential_and_git_environment_keys_never_reach_the_child(self):
        hostile = {
            "GIT_DIR": "/nowhere",
            "GIT_AUTHOR_NAME": "nobody",
            "WILDCAT_RPC_TOKEN": "not-a-real-value",  # phylax: allow test material shaped like a credential
            "AWS_SECRET_ACCESS_KEY": "not-a-real-value",  # phylax: allow test material shaped like a credential
            "SSH_AUTH_SOCK": "/nowhere",
        }
        code, payload, _events, _target = self.run_argv(
            ["python3", "-c", "import json, os; print('env'); print(json.dumps(sorted(os.environ)))"],
            ['run: line "env"'],
            environ=hostile,
        )
        self.assertEqual(code, 0, payload["demonstrations"][0]["refusal"])
        tail = payload["demonstrations"][0]["repetitions"][0]["commands"][0]["stdout_tail"]
        keys = json.loads(tail.strip().splitlines()[-1])
        for name in hostile:
            self.assertNotIn(name, keys)
        allowed = set(demonstrations.CHILD_ENVIRONMENT_KEYS) | {
            "PYTHONPATH", "PYTHONDONTWRITEBYTECODE", "PYTHONIOENCODING",
            "__CF_USER_TEXT_ENCODING",  # injected by the macOS runtime, not by the runner
        }
        self.assertLessEqual(set(keys), allowed)

    def test_the_child_pythonpath_is_the_socket_hook_alone(self):
        code, payload, _events, _target = self.run_argv(
            ["python3", "-c", "import os; print(os.environ['PYTHONPATH'].count(os.pathsep))"],
            ['run: line "0"'],
            environ={"PYTHONPATH": "/nowhere"},
        )
        self.assertEqual(code, 0, payload["demonstrations"][0]["refusal"])

    def test_a_dns_lookup_is_a_network_attempt(self):
        code, payload, _events, _target = self.run_argv(
            [
                "python3", "-c",
                "with __import__('contextlib').suppress(Exception): print('x'); __import__('socket').getaddrinfo('example.invalid', 443)",
            ],
            ['run: line "x"'],
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["demonstrations"][0]["refusal"]["code"], "D074")

    def test_an_absent_command_program_fails_rather_than_skips(self):
        code, payload, _events, _target = self.run_argv(
            ["python3", "plugins/specimen/scripts/absent.py"], ['run: line "ok"'],
        )
        self.assertEqual(code, 2)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D072")
        self.assertEqual(entry["repetitions"], [])

    def test_a_nonzero_exit_is_refused_against_the_declared_expectation(self):
        code, payload, _events, _target = self.run_argv(
            ["python3", "-c", "raise SystemExit(3)"], ['run: line "ok"'],
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["demonstrations"][0]["refusal"]["code"], "D075")

    def test_a_record_that_allowlists_the_network_is_refused_in_this_run(self):
        record = check(fixture_record("valid-ledger.md"))
        record["network"] = {"policy": "allowlisted", "endpoints": ["https://example.invalid/rpc"]}
        record["commands"] = [{"id": "run", "argv": ["python3", "-c", "print('ok')"], "expect_exit": 0}]
        record["observations"] = ['run: line "ok"']
        code, payload, _events, _target = self.run_records([(SPECIMEN, check(record))])
        self.assertEqual(code, 2)
        self.assertEqual(payload["demonstrations"][0]["refusal"]["code"], "D074")

    def test_the_interpreter_must_match_the_pin(self):
        pinned = demonstrations.pinned_python_version(ROOT)
        self.assertEqual(pinned, platform.python_version())
        with mock.patch.object(platform, "python_version", return_value="0.0.0"):
            with self.assertRaises(demonstrations.RunRefusal) as caught:
                demonstrations.require_pinned_interpreter(ROOT)
        self.assertEqual(caught.exception.code, "D073")
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(demonstrations.RunRefusal) as caught:
                demonstrations.pinned_python_version(pathlib.Path(name))
        self.assertEqual(caught.exception.code, "D073")

    def test_the_ceiling_bounds_every_command_and_the_aggregate(self):
        record = check(fixture_record("valid-ledger.md"))
        record["commands"] = [
            {"id": "run", "argv": ["python3", "-c", "import time; time.sleep(2)"], "expect_exit": 0}
        ]
        record["observations"] = ['run: line "unreached"']
        code, payload, _events, _target = self.run_records(
            [(SPECIMEN, check(record))], ceiling_ms=50, mode="public-set"
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["ceiling_ms"], 50)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D076")
        self.assertLessEqual(entry["repetitions"][0]["commands"][0]["timeout_ms"], 50)
        self.assertIn("D082", [refusal["code"] for refusal in payload["refusals"]])


class RunnerObservationTests(RunnerHarness):
    """Observations are checked against output, never against prose."""

    def test_prose_is_not_a_checkable_observation(self):
        for index, text in enumerate((
            "The command exits 0 in about 0.1 seconds with no network.",
            "run: line unquoted",
            'run: json relation.receipt_count',
            'run: stdout "x"',
            'other: line "ok"',
        )):
            with self.subTest(observation=text):
                record = check(fixture_record("valid-ledger.md"))
                record["commands"] = [{"id": "run", "argv": ["python3", "-c", "print('ok')"], "expect_exit": 0}]
                record["observations"] = [text]
                with mock.patch.object(
                    subprocess, "Popen", side_effect=AssertionError("a command started")
                ):
                    code, payload, _events, _target = self.run_records(
                        [(SPECIMEN, check(record))], report=f"prose-{index}.json"
                    )
                self.assertEqual(code, 2)
                self.assertEqual(payload["demonstrations"][0]["refusal"]["code"], "D078")

    def test_an_observation_that_does_not_hold_is_refused(self):
        code, payload, _events, _target = self.run_argv(
            ["python3", "-c", "print('{\"count\": 224}')"],
            ['run: json count 224', 'run: json count 225'],
        )
        self.assertEqual(code, 2)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D079")
        self.assertEqual(
            entry["repetitions"][0]["commands"][0]["observations"], ["run: json count 224"]
        )

    def test_the_grammar_parses_lines_and_json_paths(self):
        line = demonstrations.parse_observation('run: line "a b"', where="t")
        self.assertEqual((line.command, line.kind, line.line), ("run", "line", "a b"))
        nested = demonstrations.parse_observation(
            'run: json relation.target_index "0xbf"', where="t"
        )
        self.assertEqual(nested.path, ("relation", "target_index"))
        self.assertTrue(demonstrations.observation_holds(
            nested, b'noise\n{"relation": {"target_index": "0xbf"}}\n'
        ))
        self.assertFalse(demonstrations.observation_holds(nested, b"not json\n"))
        indexed = demonstrations.parse_observation('run: json 0 1', where="t")
        self.assertTrue(demonstrations.observation_holds(indexed, b"[1]\n"))
        self.assertFalse(demonstrations.observation_holds(indexed, b"[2]\n"))
        self.assertFalse(demonstrations.observation_holds(indexed, b""))

    def test_every_public_set_ledger_declares_only_checkable_observations(self):
        records = demonstrations.load_records(ROOT)
        skills = {skill.directory: skill for skill in demonstrations.governed_skills(ROOT)}
        selected = demonstrations.select_records(
            records, skills, public_set=True, record_directory=None
        )
        self.assertEqual(len(selected), len(demonstrations.PUBLIC_SET))
        for skill, record in selected:
            with self.subTest(skill=skill.id):
                result = demonstrations.preflight_record(ROOT, skill, record)
                # Preflight reports the observations and what it established
                # about each program. Asserting the shape keeps this a failed
                # assertion on a tree that returns observations alone, rather
                # than an unpacking error the guard check cannot classify.
                self.assertIsInstance(result, tuple)
                parsed, programs = result
                self.assertEqual(len(parsed), len(record["observations"]))
                self.assertEqual(record["status"], "real-data")
                # Every public-set command that names a file program runs one
                # whose digest a source declared, so preflight verifies it
                # rather than merely finding it.
                self.assertTrue(programs)
                for entry in programs.values():
                    self.assertEqual(entry["evidence"], "verified")


class BundledInterpreterOptionTests(unittest.TestCase):
    """A hook-disabling option is refused whether it stands alone or bundles.

    Round 1 refused `-S`, `-E` and `-I` as whole words. CPython bundles short
    options, so `-Sc` reaches the same interpreter state by another spelling:
    the child skips `site`, never loads the socket hook, builds a real socket
    and resolves a name while the run records `network_attempt` false.
    """

    def _admit(self, argv):
        return demonstrations.preflight_record(
            ROOT, SPECIMEN,
            {"sources": [], "commands": [{"id": "run", "argv": argv, "expect_exit": 0}],
             "observations": []},
        )

    def test_a_bundled_hook_disabling_option_is_refused(self):
        for word in ("-Sc", "-Ic", "-Ec", "-EsSc", "-sSc", "-IB"):
            with self.subTest(word=word):
                with self.assertRaises(demonstrations.DemonstrationError) as caught:
                    self._admit(["python3", word, "pass"])
                self.assertIn("D074", str(caught.exception))

    def test_a_standalone_hook_disabling_option_is_still_refused(self):
        for word in demonstrations.HOOK_DISABLING_OPTIONS:
            with self.subTest(word=word):
                with self.assertRaises(demonstrations.DemonstrationError) as caught:
                    self._admit(["python3", word, "-c", "pass"])
                self.assertIn("D074", str(caught.exception))

    def test_an_option_that_does_not_disable_the_hook_is_admitted(self):
        # Over-refusing here would refuse the live records, which pass
        # `--specimen`, `--output` and `--check` to their programs.
        for argv in (
            ["python3", "-c", "pass"],
            ["python3", "-u", "-c", "pass"],
            ["python3", "-OO", "-c", "pass"],
            ["python3", "-X", "importtime", "-c", "pass"],
            ["python3", "-W", "ignore", "-c", "pass"],
            ["python3", "-m", "json.tool", "--help"],
        ):
            with self.subTest(argv=argv):
                self._admit(argv)

    def test_a_long_option_is_never_read_as_a_bundle(self):
        # Checked through the admission path rather than the helper alone, so
        # a tree without the helper fails this assertion instead of raising.
        self.assertTrue(hasattr(demonstrations, "_disables_socket_hook"))
        for word in ("--specimen", "--output", "--check", "--Set", "--Isolated"):
            with self.subTest(word=word):
                self.assertIsNone(demonstrations._disables_socket_hook(word))


class DeclaredProgramTests(unittest.TestCase):
    """A registered public demonstration digests the program it runs."""

    def _public(self, claim_id=demonstrations.PUBLIC_SET[0]):
        records = demonstrations.load_records(ROOT)
        skills = {s.directory: s for s in demonstrations.governed_skills(ROOT)}
        for directory, record in records.items():
            if record["claim_id"] == claim_id:
                return skills[directory], copy.deepcopy(record)
        raise AssertionError(f"{claim_id} has no ledger")

    @staticmethod
    def _program(argv):
        """The file program an argv runs, derived without the new helper."""

        if len(argv) < 2:
            return None
        word = argv[1]
        if word.startswith("-") or demonstrations.WORK_TOKEN in word:
            return None
        return word

    def test_every_public_set_record_declares_its_command_program(self):
        for claim_id in demonstrations.PUBLIC_SET:
            skill, record = self._public(claim_id)
            declared = {s["path"] for s in record["sources"] if "path" in s}
            with self.subTest(claim_id=claim_id):
                for command in record["commands"]:
                    program = self._program(command["argv"])
                    if program is not None:
                        self.assertIn(program, declared)

    def test_an_undeclared_public_program_is_refused(self):
        skill, record = self._public()
        program = self._program(record["commands"][0]["argv"])
        record["sources"] = [s for s in record["sources"] if s.get("path") != program]
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.check_record(ROOT, skill, record)
        self.assertIn("D084", str(caught.exception))

    def test_a_program_whose_bytes_drift_is_refused_before_execution(self):
        skill, record = self._public()
        program = self._program(record["commands"][0]["argv"])
        declared = [s for s in record["sources"] if s.get("path") == program]
        # On a tree where the program is not declared there is nothing to
        # drift, which is the gap this guard exists to catch.
        self.assertTrue(declared)
        for source in declared:
            source["sha256"] = "0" * 64
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            demonstrations.preflight_record(ROOT, skill, record)
        self.assertIn("D084", str(caught.exception))

    def test_a_public_program_is_reported_as_verified(self):
        skill, record = self._public()
        result = demonstrations.preflight_record(ROOT, skill, record)
        self.assertIsInstance(result, tuple)
        _observations, programs = result
        self.assertTrue(programs)
        for entry in programs.values():
            self.assertEqual(entry["evidence"], "verified")
            self.assertTrue(demonstrations.DIGEST_RE.fullmatch(entry["sha256"]))

    def test_an_undeclared_program_outside_the_public_set_is_reported_as_found(self):
        # The rule binds registered public demonstrations. Every other record
        # keeps the weaker evidence, and the report says which it holds.
        record = check(fixture_record("valid-ledger.md"))
        record["commands"] = [
            {"id": "run", "argv": ["python3", "scripts/demonstrations.py", "--help"],
             "expect_exit": 0}
        ]
        record["observations"] = ['run: line "usage"']
        result = demonstrations.preflight_record(ROOT, SPECIMEN, record)
        self.assertIsInstance(result, tuple)
        _observations, programs = result
        self.assertEqual(
            [entry["evidence"] for entry in programs.values()], ["found"]
        )

    def test_an_option_or_work_path_program_carries_no_entry(self):
        self.assertTrue(hasattr(demonstrations, "_command_program"))
        for argv in (
            ["python3", "-c", "print(1)"],
            ["python3", "-m", "json.tool", "--help"],
            ["python3", "{work}/built.py"],
        ):
            with self.subTest(argv=argv):
                self.assertIsNone(demonstrations._command_program(argv))


class RunnerSelectionTests(RunnerHarness):
    """Only a checked record or the closed public set can be selected."""

    def setUp(self):
        super().setUp()
        self.records = demonstrations.load_records(ROOT)
        self.skills = {skill.directory: skill for skill in demonstrations.governed_skills(ROOT)}

    def test_the_public_set_is_closed_and_real_data(self):
        self.assertEqual(len(demonstrations.PUBLIC_SET), len(set(demonstrations.PUBLIC_SET)))
        selected = demonstrations.select_records(
            self.records, self.skills, public_set=True, record_directory=None
        )
        self.assertEqual(
            [record["claim_id"] for _skill, record in selected], list(demonstrations.PUBLIC_SET)
        )

    def test_a_missing_public_member_fails_rather_than_skips(self):
        records = {
            directory: record for directory, record in self.records.items()
            if record["claim_id"] != demonstrations.PUBLIC_SET[1]
        }
        with self.assertRaises(demonstrations.RunRefusal) as caught:
            demonstrations.select_records(
                records, self.skills, public_set=True, record_directory=None
            )
        self.assertEqual(caught.exception.code, "D071")

    def test_a_downgraded_public_member_is_refused(self):
        records = copy.deepcopy(self.records)
        for record in records.values():
            if record["claim_id"] == demonstrations.PUBLIC_SET[0]:
                record["status"] = "mixed"
        with self.assertRaises(demonstrations.RunRefusal) as caught:
            demonstrations.select_records(
                records, self.skills, public_set=True, record_directory=None
            )
        self.assertEqual(caught.exception.code, "D071")

    def test_an_ungoverned_directory_is_refused(self):
        with self.assertRaises(demonstrations.RunRefusal) as caught:
            demonstrations.select_records(
                self.records, self.skills, public_set=False, record_directory="plugins/nowhere"
            )
        self.assertEqual(caught.exception.code, "D071")


class RunnerReportTests(RunnerHarness):
    """The report is one closed object, published atomically, repeating the non-claim."""

    def test_a_verified_run_publishes_the_report_and_its_events(self):
        code, payload, events, target = self.run_specimen("partial-report.md", repeat=2)
        self.assertEqual(code, 0, payload["demonstrations"][0]["refusal"])
        self.assertEqual(payload["schema"], demonstrations.REPORT_SCHEMA)
        self.assertEqual(payload["status"], "verified")
        self.assertEqual(payload["repeat"], 2)
        published = json.loads(target.read_text(encoding="utf-8"))
        self.assertEqual(published, payload)
        entry = payload["demonstrations"][0]
        record = fixture_record("partial-report.md")
        self.assertEqual(entry["non_claim"], record["non_claim"])
        self.assertEqual(entry["record_sha256"], demonstrations.record_digest(record))
        self.assertEqual(entry["sources"][0]["evidence"], "recorded")
        self.assertEqual(entry["sources"][0]["anchor"], record["sources"][0]["anchor"])
        self.assertEqual(len(entry["repetitions"]), 2)
        self.assertEqual({event["correlation_id"] for event in events}, {"c0ffee"})
        self.assertEqual(
            [event["event"] for event in events],
            [
                "demonstration.selected",
                "demonstration.started",
                "demonstration.started",
                "demonstration.verified",
                "demonstration.report",
            ],
        )
        self.assertEqual(events[0]["count"], 1)
        self.assertEqual(events[-1]["sha256"], hashlib_of(target))
        with self.assertRaises(demonstrations.RunRefusal) as caught:
            self.run_specimen("partial-report.md")
        self.assertEqual(caught.exception.code, "D080")

    def test_the_public_set_runs_and_is_asserted_against_its_ledgers(self):
        records = demonstrations.load_records(ROOT)
        skills = {skill.directory: skill for skill in demonstrations.governed_skills(ROOT)}
        selected = demonstrations.select_records(
            records, skills, public_set=True, record_directory=None
        )
        code, payload, events, _target = self.run_records(
            selected, report="public-set.json",
            ceiling_ms=demonstrations.PUBLIC_SET_CEILING_MS, mode="public-set",
        )
        self.assertEqual(code, 0, payload["refusals"])
        self.assertEqual(payload["status"], "verified")
        self.assertLessEqual(payload["aggregate_ms"], demonstrations.PUBLIC_SET_CEILING_MS)
        self.assertEqual(
            [entry["claim_id"] for entry in payload["demonstrations"]],
            list(demonstrations.PUBLIC_SET),
        )
        for (_skill, record), entry in zip(selected, payload["demonstrations"]):
            with self.subTest(claim_id=record["claim_id"]):
                self.assertEqual(entry["result"], "verified")
                self.assertEqual(entry["non_claim"], record["non_claim"])
                held = [
                    text
                    for command in entry["repetitions"][0]["commands"]
                    for text in command["observations"]
                ]
                self.assertEqual(sorted(held), sorted(record["observations"]))
                for command in entry["repetitions"][0]["commands"]:
                    self.assertFalse(command["network_attempt"])
                    self.assertFalse(command["truncated"])
        self.assertEqual(
            [event["event"] for event in events if event["event"] == "demonstration.verified"],
            ["demonstration.verified"] * len(demonstrations.PUBLIC_SET),
        )


def hashlib_of(path: pathlib.Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


class HorosCensusCurrencyTests(unittest.TestCase):
    """The committed Horos census describes the tree the ledgers ship with.

    The step permits the generated Horos files only when the deterministic scan
    changes them. `horos.py check .` and the root boundary guard re-derive
    `.horos/boundary.json` alone, so a commit that adds files and refreshes the
    boundary can leave `.horos/census.json` describing the previous tree with
    every gate green. Step 2, round 1 did exactly that. This is the guard.
    """

    def test_the_committed_census_matches_a_fresh_scan(self):
        sys.path.insert(0, str(ROOT / "plugins" / "horos" / "skills" / "horos" / "scripts"))
        import horos  # noqa: E402  (locates horos.py)

        committed = json.loads(
            (ROOT / horos.CENSUS_RELPATH).read_text(encoding="utf-8")
        )
        boundary = horos.load_boundary(str(ROOT))
        fresh = horos.census_document(
            horos.scan_tree(
                str(ROOT),
                census=True,
                include_untracked=boundary.get("universe") == "tracked+untracked",
            )
        )
        self.assertEqual(
            committed,
            json.loads(horos.render(fresh)),
            "regenerate with: python3 plugins/horos/skills/horos/scripts/horos.py"
            " scan . --census --write",
        )


@unittest.skipUnless(RUNNER, "Step 3 runner is absent on the entry parent")
class RunnerExecutionBoundaryTests(RunnerHarness):
    """The execution boundary is the pinned interpreter under a live hook."""

    def test_a_program_other_than_the_pinned_interpreter_is_refused(self):
        code, payload, _events_seen, _target = self.run_argv(
            ["sh", "-c", "echo shell-ran"], ['run: line "shell-ran"'],
        )
        self.assertEqual(code, 2)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D072")
        self.assertEqual(entry["repetitions"], [])

    def test_an_interpreter_option_that_turns_the_hook_off_is_refused(self):
        options = ("-S", "-E", "-I")
        # Named here rather than read from the module so an unfixed tree fails
        # this by assertion instead of erroring on a constant it does not have.
        self.assertEqual(
            getattr(demonstrations, "HOOK_DISABLING_OPTIONS", None), options
        )
        for option in options:
            with self.subTest(option=option):
                record = check(fixture_record("valid-ledger.md"))
                record["commands"] = [{
                    "id": "run",
                    "argv": ["python3", option, "-c", "import socket; socket.socket()"],
                    "expect_exit": 0,
                }]
                record["observations"] = ['run: line "unreachable"']
                code, payload, _events_seen, _target = self.run_records(
                    [(SPECIMEN, check(record))], report=f"report{option}.json",
                )
                self.assertEqual(code, 2)
                entry = payload["demonstrations"][0]
                self.assertEqual(entry["refusal"]["code"], "D074")
                self.assertEqual(entry["repetitions"], [])

    def test_an_interpreter_given_no_work_is_refused(self):
        code, payload, _events_seen, _target = self.run_argv(
            ["python3"], ['run: line "unreachable"'],
        )
        self.assertEqual(code, 2)
        self.assertEqual(payload["demonstrations"][0]["refusal"]["code"], "D072")

    def test_a_child_that_erases_the_network_marker_is_still_refused(self):
        code, payload, _events_seen, _target = self.run_argv(
            [
                "python3", "-c",
                "import atexit, os, socket;"
                " atexit.register(lambda: os.unlink(os.path.join("
                "os.path.dirname(os.environ['PYTHONPATH']), 'network-attempt')));"
                " socket.socket()",
            ],
            ['run: line "erased"'],
        )
        self.assertEqual(code, 2)
        entry = payload["demonstrations"][0]
        self.assertEqual(entry["refusal"]["code"], "D074")
        self.assertTrue(entry["repetitions"][0]["commands"][0]["network_attempt"])

    def test_a_grandchild_does_not_outlive_a_command_that_exits_zero(self):
        sentinel = self.out / "grandchild-survived"
        code, payload, _events_seen, _target = self.run_argv(
            [
                "python3", "-c",
                "import os, sys, time;"
                " child = os.fork() == 0;"
                f" (time.sleep(6), open({str(sentinel)!r}, 'w').write('alive'),"
                " os._exit(0)) if child else"
                " (print('parent-done'), sys.stdout.flush(), os._exit(0))",
            ],
            ['run: line "parent-done"'],
        )
        self.assertEqual(code, 0, payload["demonstrations"][0]["refusal"])
        command = payload["demonstrations"][0]["repetitions"][0]["commands"][0]
        # Without the teardown the reader threads block on the pipe the
        # grandchild still holds, so the recorded duration becomes its lifetime
        # and the grandchild outlives the run that started it.
        self.assertLess(command["duration_ms"], 4000)
        time.sleep(8)
        self.assertFalse(sentinel.exists())


@unittest.skipUnless(RUNNER, "Step 3 runner is absent on the entry parent")
class ReportPublicationBoundaryTests(unittest.TestCase):
    """Publication is bound to the directory containment actually proved."""

    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = pathlib.Path(
            self.stack.enter_context(tempfile.TemporaryDirectory())
        ).resolve()
        self.outside = pathlib.Path(
            self.stack.enter_context(tempfile.TemporaryDirectory())
        ).resolve()

    def test_a_parent_swapped_after_resolution_refuses_rather_than_escaping(self):
        (self.root / "reports").mkdir()
        target = demonstrations.resolve_report_target(
            str(self.root / "reports" / "r.json"), self.root
        )
        os.rename(self.root / "reports", self.root / "reports-real")
        os.symlink(self.outside, self.root / "reports")
        # A tree whose publisher takes no output root raises rather than
        # refusing; naming the outcome keeps that an assertion, not an error.
        try:
            demonstrations.publish_report(target, {"probe": True}, self.root)
        except demonstrations.RunRefusal as refusal:
            outcome = refusal.code
        except Exception as exc:  # noqa: BLE001
            outcome = type(exc).__name__
        else:
            outcome = "published"
        self.assertEqual(outcome, "D081")
        self.assertFalse((self.outside / "r.json").exists())

    def test_a_report_still_publishes_through_a_confined_parent(self):
        target = demonstrations.resolve_report_target(
            str(self.root / "a" / "b" / "r.json"), self.root
        )
        try:
            digest = demonstrations.publish_report(target, {"probe": True}, self.root)
        except Exception as exc:  # noqa: BLE001
            self.fail(f"a confined report was not published: {exc!r}")
        self.assertTrue(target.exists())
        self.assertEqual(digest, hashlib.sha256(target.read_bytes()).hexdigest())
        self.assertEqual(
            [name for name in os.listdir(target.parent) if ".partial-" in name], []
        )


@unittest.skipUnless(RUNNER, "Step 3 runner is absent on the entry parent")
class RunnerRefusalEventTests(unittest.TestCase):
    """A run that fails its checks is visible in the event stream."""

    def test_a_ledger_refusal_during_a_run_emits_a_refused_event(self):
        with tempfile.TemporaryDirectory() as name:
            out = pathlib.Path(name)
            (out / ".python-version").write_text(
                platform.python_version() + "\n", encoding="utf-8"
            )
            args = demonstrations.build_parser().parse_args([
                "run", "--root", str(out), "--public-set",
                "--report", str(out / "r.json"), "--output-root", str(out),
            ])
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                with self.assertRaises(Exception):
                    demonstrations.command_run(args)
        events = _events(output.getvalue())
        refused = [event for event in events if event["event"] == "demonstration.refused"]
        self.assertEqual(len(refused), 1, events)
        self.assertTrue(refused[0]["correlation_id"])
        self.assertTrue(refused[0]["code"])


if __name__ == "__main__":
    unittest.main()
