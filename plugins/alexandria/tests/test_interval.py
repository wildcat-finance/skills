"""Shard planning, journal staging and checkpointed resume."""

from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import (  # noqa: E402
    CHECKPOINT_FORMAT,
    EVIDENCE_CLASSES,
    IMPLEMENTATION_SLOT,
    UPGRADED_TOPIC,
    discover_epochs,
    validate_epochs,
    MAX_SHARDS,
    MAX_SHARD_WIDTH,
    PLAN_FORMAT,
    RECEIPT_FORMAT,
    Staging,
    contained,
    plan_digest,
    plan_shards,
    resolve_root,
    validate_checkpoint,
    validate_plan,
)

PROXY = "0xc3d688b66703497daa19211eedff47f25384cdc3"
HASH = "0x" + "ab" * 32
OTHER_HASH = "0x" + "cd" * 32


def plan(start=1000, end=1099, width=25, **overrides):
    value = {
        "chain": "eip155:1",
        "deployment": "ethereum-usdc-comet",
        "evidence_classes": list(EVIDENCE_CLASSES),
        "finality": {
            "block_hash": HASH,
            "block_number": str(end + 64),
            "policy": "finalized",
        },
        "format": PLAN_FORMAT,
        "interval": {"end": str(end), "start": str(start)},
        "proxy": PROXY,
        "shard_width": width,
        "shards": plan_shards(start, end, width),
        "venue": "compound-v3",
    }
    value.update(overrides)
    return value


class ShardPlannerTests(unittest.TestCase):
    def test_shards_tile_an_exact_multiple(self):
        shards = plan_shards(100, 199, 25)
        self.assertEqual(len(shards), 4)
        self.assertEqual(shards[0], {"end": 124, "index": 0, "start": 100})
        self.assertEqual(shards[-1], {"end": 199, "index": 3, "start": 175})

    def test_a_ragged_interval_is_covered_exactly_by_a_short_final_shard(self):
        shards = plan_shards(100, 109, 4)
        self.assertEqual([item["start"] for item in shards], [100, 104, 108])
        self.assertEqual(shards[-1]["end"], 109)
        covered = [block for item in shards for block in range(item["start"], item["end"] + 1)]
        self.assertEqual(covered, list(range(100, 110)))

    def test_a_single_block_interval_is_one_shard(self):
        self.assertEqual(plan_shards(7, 7, 2000), [{"end": 7, "index": 0, "start": 7}])

    def test_shards_never_overlap_and_leave_no_hole(self):
        shards = plan_shards(0, 1000, 7)
        for earlier, later in zip(shards, shards[1:]):
            self.assertEqual(later["start"], earlier["end"] + 1)

    def test_a_reversed_interval_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "must not precede"):
            plan_shards(200, 199, 10)

    def test_a_negative_start_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "must not be negative"):
            plan_shards(-1, 10, 10)

    def test_a_zero_width_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "at least"):
            plan_shards(0, 10, 0)

    def test_an_oversized_width_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "must not exceed"):
            plan_shards(0, 10, MAX_SHARD_WIDTH + 1)

    def test_an_unbounded_interval_refuses_by_shard_count(self):
        with self.assertRaisesRegex(AlexandriaError, "shard limit"):
            plan_shards(0, MAX_SHARDS * 10, 1)

    def test_a_boolean_is_not_a_block_number(self):
        with self.assertRaisesRegex(AlexandriaError, "must be an integer"):
            plan_shards(True, 10, 1)


class PlanValidationTests(unittest.TestCase):
    def test_a_well_formed_plan_is_accepted(self):
        validate_plan(plan())

    def test_an_unknown_field_refuses(self):
        value = plan()
        value["extra"] = 1
        with self.assertRaisesRegex(AlexandriaError, "unknown shape"):
            validate_plan(value)

    def test_shards_that_do_not_tile_the_interval_refuse(self):
        value = plan()
        value["shards"] = value["shards"][:-1]
        with self.assertRaisesRegex(AlexandriaError, "do not tile"):
            validate_plan(value)

    def test_an_end_above_the_finality_boundary_refuses(self):
        value = plan()
        value["finality"]["block_number"] = "1"
        with self.assertRaisesRegex(AlexandriaError, "above its finality boundary"):
            validate_plan(value)

    def test_an_unrecognised_finality_policy_refuses(self):
        value = plan()
        value["finality"]["policy"] = "probably-fine"
        with self.assertRaisesRegex(AlexandriaError, "finality policy"):
            validate_plan(value)

    def test_a_confirmation_policy_carries_its_depth(self):
        value = plan()
        value["finality"] = {
            "block_hash": HASH,
            "block_number": "2000",
            "confirmations": 64,
            "policy": "confirmations",
        }
        validate_plan(value)
        value["finality"]["confirmations"] = 0
        with self.assertRaisesRegex(AlexandriaError, "positive integer"):
            validate_plan(value)

    def test_a_confirmation_depth_on_a_finalized_policy_refuses(self):
        value = plan()
        value["finality"]["confirmations"] = 64
        with self.assertRaisesRegex(AlexandriaError, "unknown shape"):
            validate_plan(value)

    def test_a_mixed_case_proxy_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "lowercase address"):
            validate_plan(plan(proxy=PROXY.upper()))

    def test_reordered_evidence_classes_refuse(self):
        value = plan()
        value["evidence_classes"] = list(reversed(EVIDENCE_CLASSES))
        with self.assertRaisesRegex(AlexandriaError, "evidence classes"):
            validate_plan(value)


class CheckpointValidationTests(unittest.TestCase):
    def checkpoint(self, **overrides):
        value = {
            "format": CHECKPOINT_FORMAT,
            "last_accepted": {"block_hash": HASH, "block_number": "1024"},
            "next_shard": 1,
            "offsets": {name: 0 for name in EVIDENCE_CLASSES},
            "plan_sha256": "a" * 64,
            "records": 3,
        }
        value.update(overrides)
        return value

    def test_a_well_formed_checkpoint_is_accepted(self):
        validate_checkpoint(self.checkpoint(), "a" * 64, 4)

    def test_a_checkpoint_from_another_plan_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "different plan"):
            validate_checkpoint(self.checkpoint(), "b" * 64, 4)

    def test_a_shard_outside_the_plan_refuses(self):
        with self.assertRaisesRegex(AlexandriaError, "outside its plan"):
            validate_checkpoint(self.checkpoint(next_shard=9), "a" * 64, 4)

    def test_missing_offsets_refuse(self):
        value = self.checkpoint(offsets={"logs": 0})
        with self.assertRaisesRegex(AlexandriaError, "every evidence class"):
            validate_checkpoint(value, "a" * 64, 4)

    def test_progress_without_an_accepted_block_refuses(self):
        value = self.checkpoint(last_accepted=None)
        with self.assertRaisesRegex(AlexandriaError, "accepted block"):
            validate_checkpoint(value, "a" * 64, 4)

    def test_a_truncated_block_hash_refuses(self):
        value = self.checkpoint(last_accepted={"block_hash": "0xab", "block_number": "1"})
        with self.assertRaisesRegex(AlexandriaError, "32-byte hash"):
            validate_checkpoint(value, "a" * 64, 4)


class StagingRootTests(unittest.TestCase):
    def test_a_missing_root_refuses(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(AlexandriaError, "cannot resolve"):
                resolve_root(Path(name) / "absent")

    def test_a_file_is_not_a_root(self):
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "file"
            target.write_text("x")
            with self.assertRaisesRegex(AlexandriaError, "must be a directory"):
                resolve_root(target)

    def test_an_unresolved_alias_still_contains_its_own_children(self):
        """The macOS /var/folders alias for /private/var/folders must not refuse."""
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            self.assertEqual(
                contained(root, root / "journals" / "logs.jsonl"),
                root.resolve() / "journals" / "logs.jsonl",
            )

    def test_traversal_above_the_root_refuses(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaisesRegex(AlexandriaError, "escapes the staging root"):
                contained(Path(name), Path(name) / ".." / "elsewhere")

    def test_an_absolute_path_outside_the_root_refuses(self):
        with tempfile.TemporaryDirectory() as outer, tempfile.TemporaryDirectory() as other:
            with self.assertRaisesRegex(AlexandriaError, "escapes the staging root"):
                contained(Path(outer), Path(other) / "logs.jsonl")

    def test_a_symlinked_journal_refuses(self):
        with tempfile.TemporaryDirectory() as name, tempfile.TemporaryDirectory() as elsewhere:
            root = Path(name)
            (root / "journals").mkdir()
            (root / "journals" / "logs.jsonl").symlink_to(Path(elsewhere) / "captured")
            staging = Staging(root, plan())
            staging.resume()
            with self.assertRaisesRegex(AlexandriaError, "must not be a symlink"):
                staging.record(0, "logs", b"{}", b"{}")
            staging.close()
            self.assertFalse((Path(elsewhere) / "captured").exists())


def collect(staging, shards, torn=None):
    """Stage every class of every shard, optionally tearing one mid-shard."""
    start = staging.resume()["next_shard"]
    for shard in range(start, shards):
        for index, name in enumerate(EVIDENCE_CLASSES):
            if torn is not None and shard == torn and index == 1:
                return
            staging.record(
                shard,
                name,
                json.dumps({"class": name, "shard": shard}).encode(),
                json.dumps({"result": [name, shard]}).encode(),
            )
        staging.commit(shard, 1000 + shard, HASH)


def projection(root):
    return {
        path.name: path.read_bytes()
        for path in sorted((Path(root) / "journals").iterdir())
    }


class StagingTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.plan = plan(1000, 1099, 25)

    def test_records_land_in_their_class_journal(self):
        with Staging(self.root, self.plan) as staging:
            collect(staging, 4)
        journals = projection(self.root)
        self.assertEqual(sorted(journals), ["boundary-blocks.jsonl", "logs.jsonl", "traces.jsonl"])
        for name, data in journals.items():
            self.assertEqual(len(data.splitlines()), 4, name)

    def test_the_checkpoint_names_the_next_shard_its_block_and_every_offset(self):
        with Staging(self.root, self.plan) as staging:
            collect(staging, 2)
        checkpoint = json.loads((self.root / "checkpoint.json").read_text())
        self.assertEqual(checkpoint["format"], CHECKPOINT_FORMAT)
        self.assertEqual(checkpoint["next_shard"], 2)
        self.assertEqual(checkpoint["last_accepted"], {"block_hash": HASH, "block_number": "1001"})
        self.assertEqual(set(checkpoint["offsets"]), set(EVIDENCE_CLASSES))
        self.assertEqual(checkpoint["plan_sha256"], plan_digest(self.plan))
        self.assertEqual(checkpoint["records"], 6)
        for name, offset in checkpoint["offsets"].items():
            self.assertEqual(offset, (self.root / "journals" / f"{name}.jsonl").stat().st_size)

    def test_resume_without_a_checkpoint_starts_at_zero_and_discards_orphans(self):
        with Staging(self.root, self.plan) as staging:
            staging.resume()
            staging.record(0, "logs", b"{}", b"{}")
        with Staging(self.root, self.plan) as staging:
            self.assertEqual(staging.resume(), {"last_accepted": None, "next_shard": 0, "records": 0})
        self.assertEqual((self.root / "journals" / "logs.jsonl").stat().st_size, 0)

    def test_resume_after_a_clean_boundary_continues_from_the_next_shard(self):
        with Staging(self.root, self.plan) as staging:
            collect(staging, 2)
        with Staging(self.root, self.plan) as staging:
            self.assertEqual(staging.resume()["next_shard"], 2)

    def test_a_torn_shard_leaves_nothing_a_resumed_run_keeps(self):
        clean = tempfile.TemporaryDirectory()
        self.addCleanup(clean.cleanup)
        with Staging(Path(clean.name), self.plan) as staging:
            collect(staging, 4)
        expected = projection(clean.name)

        with Staging(self.root, self.plan) as staging:
            collect(staging, 4, torn=2)
        torn = projection(self.root)
        self.assertNotEqual(torn, expected)
        with Staging(self.root, self.plan) as staging:
            collect(staging, 4)
        self.assertEqual(projection(self.root), expected)

    def test_a_journal_shorter_than_its_committed_offset_refuses(self):
        with Staging(self.root, self.plan) as staging:
            collect(staging, 3)
        path = self.root / "journals" / "logs.jsonl"
        with open(path, "r+b") as handle:
            handle.truncate(4)
        with Staging(self.root, self.plan) as staging:
            with self.assertRaisesRegex(AlexandriaError, "shorter than its committed offset"):
                staging.resume()

    def test_a_checkpoint_for_another_plan_refuses_on_resume(self):
        with Staging(self.root, self.plan) as staging:
            collect(staging, 2)
        with Staging(self.root, plan(1000, 1099, 20)) as staging:
            with self.assertRaisesRegex(AlexandriaError, "different plan"):
                staging.resume()

    def test_a_shard_outside_the_plan_refuses(self):
        with Staging(self.root, self.plan) as staging:
            staging.resume()
            with self.assertRaisesRegex(AlexandriaError, "outside the plan"):
                staging.record(999, "logs", b"{}", b"{}")
            with self.assertRaisesRegex(AlexandriaError, "outside the plan"):
                staging.commit(999, 1000, HASH)

    def test_an_unknown_evidence_class_refuses(self):
        with Staging(self.root, self.plan) as staging:
            staging.resume()
            with self.assertRaisesRegex(AlexandriaError, "unknown evidence class"):
                staging.record(0, "../escape", b"{}", b"{}")

    def test_a_malformed_commit_hash_refuses(self):
        with Staging(self.root, self.plan) as staging:
            staging.resume()
            with self.assertRaisesRegex(AlexandriaError, "32-byte hash"):
                staging.commit(0, 1000, "0xnope")

    def test_entries_are_read_back_in_the_order_they_were_kept(self):
        with Staging(self.root, self.plan) as staging:
            collect(staging, 3)
            entries = list(staging.entries("logs"))
        self.assertEqual([item["shard"] for item in entries], [0, 1, 2])
        self.assertEqual(entries[0]["class"], "logs")
        self.assertEqual(json.loads(entries[0]["response"]), {"result": ["logs", 0]})

    def test_staging_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            with Staging(self.root, self.plan) as staging:
                collect(staging, 2)
                staging.resume()



class StagingGuardTests(unittest.TestCase):
    """One case per round-1 audit finding, each failing against the parent."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)
        self.plan = plan(1000, 1099, 25)

    def test_a_symlinked_checkpoint_refuses_instead_of_discarding_the_journals(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        with Staging(self.root, self.plan) as staging:
            collect(staging, 1)
        journal = self.root / "journals" / "logs.jsonl"
        staged = journal.stat().st_size
        self.assertGreater(staged, 0)

        checkpoint = self.root / "checkpoint.json"
        moved = Path(elsewhere.name) / "checkpoint.json"
        moved.write_bytes(checkpoint.read_bytes())
        checkpoint.unlink()
        checkpoint.symlink_to(moved)

        with Staging(self.root, self.plan) as staging:
            with self.assertRaisesRegex(AlexandriaError, "must not be a symlink"):
                staging.resume()
        self.assertEqual(journal.stat().st_size, staged)

    def test_a_checkpoint_that_is_not_a_regular_file_refuses(self):
        (self.root / "checkpoint.json").mkdir()
        with Staging(self.root, self.plan) as staging:
            with self.assertRaisesRegex(AlexandriaError, "not a regular file"):
                staging.resume()

    def test_a_journal_directory_that_is_a_symlinked_file_refuses_without_a_traceback(self):
        elsewhere = tempfile.TemporaryDirectory()
        self.addCleanup(elsewhere.cleanup)
        target = Path(elsewhere.name) / "captured"
        target.write_text("")
        root = self.root / "hostile"
        root.mkdir()
        (root / "journals").symlink_to(target)
        with self.assertRaises(AlexandriaError):
            Staging(root, self.plan)

    def test_a_record_past_the_journal_ceiling_refuses_where_it_is_written(self):
        with mock.patch("alexandria_lib.interval.MAX_JOURNAL_BYTES", 64):
            with Staging(self.root, self.plan) as staging:
                staging.resume()
                with self.assertRaisesRegex(AlexandriaError, "would exceed"):
                    staging.record(0, "logs", b"{}", b'{"result":"' + b"x" * 200 + b'"}')
        self.assertEqual((self.root / "journals" / "logs.jsonl").stat().st_size, 0)

    def test_the_written_journal_can_always_be_read_back(self):
        with mock.patch("alexandria_lib.interval.MAX_JOURNAL_BYTES", 4096):
            with Staging(self.root, self.plan) as staging:
                staging.resume()
                for shard in range(4):
                    staging.record(shard, "logs", b"{}", b'{"result":"' + b"x" * 64 + b'"}')
                staging.commit(3, 1003, HASH)
                self.assertEqual(len(list(staging.entries("logs"))), 4)

    def test_a_commit_before_resume_refuses_rather_than_undercounting(self):
        with Staging(self.root, self.plan) as staging:
            collect(staging, 1)
        with Staging(self.root, self.plan) as staging:
            staging.record(1, "logs", b"{}", b"{}")
            with self.assertRaisesRegex(AlexandriaError, "record baseline"):
                staging.commit(1, 1001, HASH)



EPOCH_FIXTURE = PLUGIN / "tests" / "fixtures" / "usdc-epochs.json"


def epoch_evidence(**overrides):
    value = json.loads(EPOCH_FIXTURE.read_text(encoding="utf-8"))
    value = {
        "block_hashes": value["block_hashes"],
        "chain": value["chain"],
        "code_reads": value["code_reads"],
        "deployment": value["deployment"],
        "interval": value["interval"],
        "proxy": value["proxy"],
        "slot_reads": value["slot_reads"],
        "upgrade_logs": value["upgrade_logs"],
    }
    value = deepcopy(value)
    value.update(overrides)
    return value


class EpochDiscoveryTests(unittest.TestCase):
    def test_the_pinned_constants_are_the_ones_the_preserved_capture_used(self):
        corpus = json.loads(
            (PLUGIN / "examples" / "compound-v3-phase0-v0" / "input" / "corpus.json")
            .read_text(encoding="utf-8")
        )
        slots = {
            item["params"][1]
            for item in corpus["requests"]
            if item["name"].endswith("implementation-slot")
        }
        self.assertEqual(slots, {IMPLEMENTATION_SLOT})
        code = json.loads(
            (PLUGIN / "examples" / "compound-v3-phase0-v0" / "input" / "responses"
             / "old-proxy-code.json").read_text(encoding="utf-8")
        )
        self.assertIn(UPGRADED_TOPIC[2:], code["result"])

    def test_a_two_upgrade_interval_is_tiled_exactly(self):
        epochs = discover_epochs(**epoch_evidence())
        self.assertEqual(len(epochs), 3)
        self.assertEqual(epochs[0]["start_block"], "15331586")
        self.assertEqual(epochs[-1]["end_block"], "15341585")
        for earlier, later in zip(epochs, epochs[1:]):
            self.assertEqual(int(later["start_block"]), int(earlier["end_block"]) + 1)
        self.assertEqual(
            len({epoch["implementation_code_sha256"] for epoch in epochs}), 3
        )

    def test_the_first_epoch_is_clipped_to_the_interval_and_names_no_upgrade(self):
        epochs = discover_epochs(**epoch_evidence())
        self.assertIsNone(epochs[0]["upgrade"])
        for epoch in epochs[1:]:
            self.assertEqual(epoch["upgrade"]["block_number"], epoch["start_block"])

    def test_an_interval_with_no_upgrade_is_one_epoch(self):
        evidence = epoch_evidence(upgrade_logs=[], interval={"end": "15333999", "start": "15331586"})
        evidence["block_hashes"]["15333999"] = evidence["block_hashes"]["15333999"]
        epochs = discover_epochs(**evidence)
        self.assertEqual(len(epochs), 1)
        self.assertIsNone(epochs[0]["upgrade"])

    def test_a_zero_address_slot_read_refuses(self):
        evidence = epoch_evidence()
        evidence["slot_reads"]["15331586"] = "0x" + "0" * 64
        with self.assertRaisesRegex(AlexandriaError, "zero address"):
            discover_epochs(**evidence)

    def test_an_empty_runtime_code_read_refuses_with_its_own_message(self):
        evidence = epoch_evidence()
        first = "0x1b0e765f6224c21223aea2af16c1c46e38885a40"
        evidence["code_reads"][first] = "0x"
        with self.assertRaisesRegex(AlexandriaError, "empty runtime code"):
            discover_epochs(**evidence)

    def test_a_slot_read_that_is_not_a_word_refuses(self):
        evidence = epoch_evidence()
        evidence["slot_reads"]["15331586"] = "0xdeadbeef"
        with self.assertRaisesRegex(AlexandriaError, "32-byte word"):
            discover_epochs(**evidence)

    def test_a_slot_read_carrying_more_than_an_address_refuses(self):
        evidence = epoch_evidence()
        evidence["slot_reads"]["15331586"] = "0x" + "1" * 64
        with self.assertRaisesRegex(AlexandriaError, "left-padded address"):
            discover_epochs(**evidence)

    def test_unordered_upgrade_logs_refuse(self):
        evidence = epoch_evidence()
        evidence["upgrade_logs"] = list(reversed(evidence["upgrade_logs"]))
        with self.assertRaisesRegex(AlexandriaError, "ascending block order"):
            discover_epochs(**evidence)

    def test_an_upgrade_log_outside_the_interval_refuses(self):
        evidence = epoch_evidence()
        evidence["upgrade_logs"][1]["blockNumber"] = hex(15_400_000)
        with self.assertRaisesRegex(AlexandriaError, "outside the declared interval"):
            discover_epochs(**evidence)

    def test_a_boundary_with_no_slot_read_of_its_own_refuses(self):
        evidence = epoch_evidence()
        del evidence["slot_reads"]["15338500"]
        with self.assertRaisesRegex(AlexandriaError, "no implementation slot read of its own"):
            discover_epochs(**evidence)

    def test_a_log_from_another_address_refuses(self):
        evidence = epoch_evidence()
        evidence["upgrade_logs"][0]["address"] = "0x" + "ab" * 20
        with self.assertRaisesRegex(AlexandriaError, "not emitted by the proxy"):
            discover_epochs(**evidence)

    def test_a_log_carrying_another_topic_refuses(self):
        evidence = epoch_evidence()
        evidence["upgrade_logs"][0]["topics"][0] = "0x" + "cd" * 32
        with self.assertRaisesRegex(AlexandriaError, "not an Upgraded"):
            discover_epochs(**evidence)

    def test_a_missing_block_hash_refuses(self):
        evidence = epoch_evidence()
        del evidence["block_hashes"]["15341585"]
        with self.assertRaisesRegex(AlexandriaError, "no preserved block hash"):
            discover_epochs(**evidence)

    def test_a_table_that_leaves_a_hole_refuses(self):
        epochs = discover_epochs(**epoch_evidence())
        epochs[1]["start_block"] = str(int(epochs[1]["start_block"]) + 1)
        with self.assertRaisesRegex(AlexandriaError, "uncovered"):
            validate_epochs(epochs, 15_331_586, 15_341_585)

    def test_a_table_that_overlaps_refuses(self):
        epochs = discover_epochs(**epoch_evidence())
        epochs[1]["start_block"] = str(int(epochs[1]["start_block"]) - 1)
        with self.assertRaisesRegex(AlexandriaError, "overlaps"):
            validate_epochs(epochs, 15_331_586, 15_341_585)

    def test_a_table_short_of_the_interval_end_refuses(self):
        epochs = discover_epochs(**epoch_evidence())
        epochs[-1]["end_block"] = str(int(epochs[-1]["end_block"]) - 1)
        with self.assertRaisesRegex(AlexandriaError, "uncovered"):
            validate_epochs(epochs, 15_331_586, 15_341_585)

    def test_the_table_matches_the_receipt_schema(self):
        epochs = discover_epochs(**epoch_evidence())
        schema = json.loads(
            (PLUGIN / "schemas" / "interval-receipt-v1.schema.json").read_text()
        )
        definition = schema["$defs"]["epoch"]
        self.assertFalse(definition["additionalProperties"])
        for epoch in epochs:
            self.assertEqual(set(epoch), set(definition["required"]))
        upgrade = definition["properties"]["upgrade"]["oneOf"][1]
        self.assertEqual(set(epochs[1]["upgrade"]), set(upgrade["required"]))

    def test_a_log_announcing_another_implementation_refuses(self):
        evidence = epoch_evidence()
        evidence["upgrade_logs"][0]["topics"][1] = "0x" + "0" * 24 + "de" * 20
        with self.assertRaisesRegex(AlexandriaError, "announces .* while the"):
            discover_epochs(**evidence)

    def test_a_log_naming_another_block_hash_refuses(self):
        evidence = epoch_evidence()
        evidence["upgrade_logs"][0]["blockHash"] = "0x" + "ff" * 32
        with self.assertRaisesRegex(AlexandriaError, "different block hash"):
            discover_epochs(**evidence)

    def test_a_log_with_no_block_hash_refuses(self):
        evidence = epoch_evidence()
        del evidence["upgrade_logs"][0]["blockHash"]
        with self.assertRaisesRegex(AlexandriaError, "has no blockHash"):
            discover_epochs(**evidence)

    def test_an_implementation_topic_that_is_not_an_address_refuses(self):
        evidence = epoch_evidence()
        evidence["upgrade_logs"][0]["topics"][1] = "0x" + "1" * 64
        with self.assertRaisesRegex(AlexandriaError, "left-padded address"):
            discover_epochs(**evidence)

    def test_a_checksummed_runtime_code_key_still_resolves(self):
        evidence = epoch_evidence()
        first = "0x1b0e765f6224c21223aea2af16c1c46e38885a40"
        evidence["code_reads"]["0x1B0E765F6224C21223AEA2AF16C1C46E38885A40"] = (
            evidence["code_reads"].pop(first)
        )
        epochs = discover_epochs(**evidence)
        self.assertEqual(epochs[0]["implementation"], first)

    def test_two_different_bodies_for_one_implementation_refuse(self):
        evidence = epoch_evidence()
        first = "0x1b0e765f6224c21223aea2af16c1c46e38885a40"
        evidence["code_reads"]["0x1B0E765F6224C21223AEA2AF16C1C46E38885A40"] = "0xdeadbeef"
        with self.assertRaisesRegex(AlexandriaError, "two different bodies"):
            discover_epochs(**evidence)

    def test_discovery_opens_no_socket(self):
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            discover_epochs(**epoch_evidence())


class SchemaTests(unittest.TestCase):
    def schema(self, name):
        return json.loads((PLUGIN / "schemas" / f"{name}.schema.json").read_text())

    def test_the_three_interval_schemas_are_closed_and_named(self):
        for name, const in (
            ("interval-plan-v1", PLAN_FORMAT),
            ("interval-checkpoint-v1", CHECKPOINT_FORMAT),
            ("interval-receipt-v1", RECEIPT_FORMAT),
        ):
            with self.subTest(schema=name):
                schema = self.schema(name)
                self.assertFalse(schema["additionalProperties"])
                self.assertEqual(schema["properties"]["format"]["const"], const)

    def test_the_plan_schema_accepts_the_fields_the_module_emits(self):
        schema = self.schema("interval-plan-v1")
        self.assertEqual(set(schema["required"]), set(plan()))
        self.assertEqual(
            set(schema["$defs"]["shard"]["required"]),
            set(plan_shards(0, 9, 5)[0]),
        )

    def test_the_checkpoint_schema_accepts_the_fields_the_module_emits(self):
        with tempfile.TemporaryDirectory() as name:
            with Staging(Path(name), plan()) as staging:
                staging.resume()
                staging.record(0, "logs", b"{}", b"{}")
                checkpoint = staging.commit(0, 1000, HASH)
        schema = self.schema("interval-checkpoint-v1")
        self.assertEqual(set(schema["required"]), set(checkpoint))

    def test_the_receipt_schema_declares_epochs_shards_and_reconciliation(self):
        schema = self.schema("interval-receipt-v1")
        self.assertEqual(
            set(schema["required"]),
            {"format", "epochs", "shards", "reconciliation"},
        )
        for section in ("epoch", "shard", "reconciliation"):
            with self.subTest(section=section):
                self.assertFalse(schema["$defs"][section]["additionalProperties"])
        self.assertEqual(
            schema["$defs"]["shard"]["properties"]["status"]["enum"],
            ["complete", "partial", "failed"],
        )

    def test_the_schema_catalogue_indexes_all_three(self):
        catalogue = (PLUGIN / "schemas" / "README.md").read_text(encoding="utf-8")
        for name in ("interval-plan-v1", "interval-checkpoint-v1", "interval-receipt-v1"):
            with self.subTest(schema=name):
                self.assertIn(f"`{name}.schema.json`", catalogue)


if __name__ == "__main__":
    unittest.main()
