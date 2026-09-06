"""Disposable index, stable query and Probitas archive bridge tests."""

import json
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import sys
from unittest import mock

from .test_derivation import COMMAND, DerivationTestCase

from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.index import _logical_digest, inspect_index, rebuild
from alexandria_lib.probitas import translate
from alexandria_lib.query import query, query_bytes
from alexandria_lib.release import verify


PROBITAS = Path(__file__).resolve().parents[2] / "probitas" / "scripts" / "probitas.py"
CLEARPOOL = "0x948d589df907c3f5cef1c62eeb051428fccbc709"
UNKNOWN = "0x" + "f" * 40


class IndexTestCase(DerivationTestCase):
    def build_index(self):
        self.build_derived()
        self.index = self.root / "alexandria.sqlite"
        self.index_digest = rebuild([self.derived_release], self.index)
        return self.index


class IndexBuildTests(IndexTestCase):
    def test_rebuild_returns_a_logical_digest(self):
        self.build_index()
        self.assertRegex(self.index_digest, r"^sha256:[0-9a-f]{64}$")

    def test_rebuild_is_logically_deterministic(self):
        self.build_derived()
        one = self.root / "one.sqlite"
        two = self.root / "two.sqlite"
        self.assertEqual(rebuild([self.derived_release], one), rebuild([self.derived_release], two))

    def test_logical_digest_does_not_depend_on_release_location(self):
        self.build_derived()
        copied = self.root / "elsewhere" / "release"
        copied.parent.mkdir()
        shutil.copytree(self.derived_release, copied)
        self.assertEqual(
            rebuild([self.derived_release], self.root / "one.sqlite"),
            rebuild([copied], self.root / "two.sqlite"),
        )

    def test_rebuild_replaces_an_existing_disposable_index(self):
        self.build_index()
        first = self.index_digest
        self.assertEqual(rebuild([self.derived_release], self.index), first)

    def test_index_output_may_not_replace_a_release_file(self):
        self.build_derived()
        manifest = (self.derived_release / "manifest.json").read_bytes()
        with self.assertRaisesRegex(AlexandriaError, "inside an input release"):
            rebuild([self.derived_release], self.derived_release / "manifest.json")
        self.assertEqual((self.derived_release / "manifest.json").read_bytes(), manifest)
        self.assertEqual(verify(self.derived_release), self.derived_id)

    def test_index_output_may_not_enter_a_release_through_a_parent_symlink(self):
        self.build_derived()
        alias = self.root / "release-alias"
        alias.symlink_to(self.derived_release, target_is_directory=True)
        with self.assertRaisesRegex(AlexandriaError, "inside an input release"):
            rebuild([self.derived_release], alias / "credit-events.jsonl")
        self.assertEqual(verify(self.derived_release), self.derived_id)

    def test_index_refuses_a_raw_release(self):
        self.build_raw()
        with self.assertRaisesRegex(AlexandriaError, "not a derived release"):
            rebuild([self.raw_release], self.root / "index.sqlite")

    def test_index_requires_a_release(self):
        with self.assertRaisesRegex(AlexandriaError, "at least one"):
            rebuild([], self.root / "index.sqlite")

    def test_duplicate_release_input_is_rejected(self):
        self.build_derived()
        with self.assertRaisesRegex(AlexandriaError, "duplicate release"):
            rebuild([self.derived_release, self.derived_release], self.root / "index.sqlite")

    def test_cli_builds_the_index(self):
        self.build_derived()
        path = self.root / "cli.sqlite"
        result = subprocess.run(
            [sys.executable, str(COMMAND), "index", str(self.derived_release), "--output", str(path)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(path.is_file())

    def test_index_records_exact_release_and_raw_identities(self):
        self.build_index()
        checked = inspect_index(self.index)
        try:
            row = checked["connection"].execute(
                "SELECT release_id, source_release_id, component_sha256, capture_id "
                "FROM credit_events ORDER BY row_id LIMIT 1"
            ).fetchone()
        finally:
            checked["connection"].close()
        self.assertEqual(row[0], self.derived_id)
        self.assertEqual(row[1], self.raw_id)
        self.assertRegex(row[2], r"^sha256:[0-9a-f]{64}$")
        self.assertTrue(row[3])

    def test_logical_row_tampering_is_rejected(self):
        self.build_index()
        connection = sqlite3.connect(self.index)
        connection.execute(
            "UPDATE credit_events SET venue = 'changed' WHERE (release_id, row_id) = "
            "(SELECT release_id, row_id FROM credit_events ORDER BY row_id LIMIT 1)"
        )
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(AlexandriaError, "logical digest"):
            inspect_index(self.index)

    def test_rehashed_logical_row_tampering_is_rejected(self):
        self.build_index()
        connection = sqlite3.connect(self.index)
        connection.execute(
            "UPDATE credit_events SET venue = 'changed' WHERE (release_id, row_id) = "
            "(SELECT release_id, row_id FROM credit_events ORDER BY row_id LIMIT 1)"
        )
        connection.execute(
            "UPDATE metadata SET value = ? WHERE key = 'logical_digest'",
            (_logical_digest(connection),),
        )
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(AlexandriaError, "verified release"):
            inspect_index(self.index)

    def test_rehashed_active_set_tampering_is_rejected(self):
        self.build_index()
        connection = sqlite3.connect(self.index)
        connection.execute("UPDATE releases SET active = 0")
        connection.execute(
            "UPDATE metadata SET value = ? WHERE key = 'logical_digest'",
            (_logical_digest(connection),),
        )
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(AlexandriaError, "verified release"):
            inspect_index(self.index)

    def test_unexpected_sqlite_schema_object_is_rejected(self):
        self.build_index()
        connection = sqlite3.connect(self.index)
        connection.execute("CREATE TABLE surprise(value TEXT)")
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(AlexandriaError, "schema does not match"):
            inspect_index(self.index)

    def test_malformed_release_path_fails_cleanly(self):
        self.build_index()
        connection = sqlite3.connect(self.index)
        connection.execute("UPDATE releases SET path = ?", (sqlite3.Binary(b"path"),))
        connection.commit()
        connection.close()
        with self.assertRaisesRegex(AlexandriaError, "malformed release path"):
            inspect_index(self.index)

    def test_stale_release_reference_is_rejected(self):
        self.build_index()
        moved = self.root / "moved-release"
        self.derived_release.rename(moved)
        with self.assertRaisesRegex(AlexandriaError, "stale release reference"):
            inspect_index(self.index)

    def test_stale_inactive_release_reference_is_rejected(self):
        self.build_derived()
        first_raw_id = self.raw_id
        first_derived = self.derived_release
        self.plan["release"] = {
            "name": "credit-view-correction", "created_at": "2026-08-16T13:00:00Z",
            "correction": {"supersedes": [first_raw_id], "reason": "replacement capture"},
        }
        self._write_plan()
        self.raw_release = self.root / "corrected-raw"
        self.derived_release = self.root / "corrected-derived"
        self.build_derived()
        path = self.root / "corrected.sqlite"
        rebuild([first_derived, self.derived_release], path)
        first_derived.rename(self.root / "moved-inactive-release")
        with self.assertRaisesRegex(AlexandriaError, "stale release reference"):
            inspect_index(path)

    def test_multiple_releases_are_indexed(self):
        self.build_derived()
        first = self.derived_release
        first_id = self.derived_id
        source = self.source_json("aave-v4-source")
        source["logs"] = source["logs"][:-1]
        self.write_source("aave-v4-source", source)
        coverage = self.plan["captures"][0]["coverage"]
        for collection in coverage["collections"]:
            if collection["selector"] == "/logs":
                collection["record_count"] -= 1
                coverage["record_count"] -= 1
        self._write_plan()
        self.raw_release = self.root / "second-raw"
        self.derived_release = self.root / "second-derived"
        self.build_derived()
        path = self.root / "multi.sqlite"
        rebuild([first, self.derived_release], path)
        result = query(path, [CLEARPOOL])
        self.assertEqual(len(result["index"]["release_ids"]), 2)
        self.assertEqual(len(result["events"]), 11)
        selected = max(first_id, self.derived_id)
        self.assertTrue(all(item["release_id"] == selected for item in result["events"]))

    def test_active_releases_may_not_disagree_about_one_row_id(self):
        self.build_derived()
        first = self.derived_release
        source = self.source_json("aave-v4-source")
        log = source["logs"][0]
        body = log["data"][2:]
        bumped = int(body[64:128], 16) + 1
        log["data"] = "0x" + body[:64] + "%064x" % bumped + body[128:]
        self.write_source("aave-v4-source", source)
        self.raw_release = self.root / "changed-raw"
        self.derived_release = self.root / "changed-derived"
        self.build_derived()
        with self.assertRaisesRegex(AlexandriaError, "active releases disagree"):
            rebuild([first, self.derived_release], self.root / "conflict.sqlite")

    def test_correction_supersedes_the_old_raw_release(self):
        self.build_derived()
        first_raw_id = self.raw_id
        first_derived = self.derived_release
        self.plan["release"] = {
            "name": "credit-view-correction", "created_at": "2026-08-16T13:00:00Z",
            "correction": {"supersedes": [first_raw_id], "reason": "replacement capture"},
        }
        self._write_plan()
        self.raw_release = self.root / "corrected-raw"
        self.derived_release = self.root / "corrected-derived"
        self.build_derived()
        path = self.root / "corrected.sqlite"
        rebuild([first_derived, self.derived_release], path)
        result = query(path, [CLEARPOOL])
        self.assertEqual(result["index"]["release_ids"], [self.derived_id])
        self.assertTrue(all(item["release_id"] == self.derived_id for item in result["events"]))


class AddressQueryTests(IndexTestCase):
    def test_query_returns_clearpool_rows_in_stable_order(self):
        self.build_index()
        result = query(self.index, [CLEARPOOL])
        self.assertEqual(len([row for row in result["events"] if row["row"]["venue"] == "clearpool"]), 11)
        self.assertEqual(query_bytes(self.index, [CLEARPOOL]), query_bytes(self.index, [CLEARPOOL]))

    def test_query_normalises_address_case(self):
        self.build_index()
        self.assertEqual(query(self.index, [CLEARPOOL.upper()]), query(self.index, [CLEARPOOL]))

    def test_query_accepts_multiple_addresses(self):
        self.build_index()
        result = query(self.index, [CLEARPOOL, UNKNOWN])
        self.assertEqual(result["request"]["addresses"], sorted([CLEARPOOL, UNKNOWN]))

    def test_venue_filter_is_applied(self):
        self.build_index()
        result = query(self.index, [CLEARPOOL], venues=["aave-v4"])
        self.assertFalse(result["events"])
        self.assertEqual([item["venue"] for item in result["coverage"]], ["aave-v4"])

    def test_chain_filter_is_applied(self):
        self.build_index()
        result = query(self.index, [CLEARPOOL], chain="eip155:2")
        self.assertFalse(result["events"])
        self.assertEqual({item["status"] for item in result["coverage"]}, {"uncovered"})

    def test_time_filter_is_applied(self):
        self.build_index()
        all_rows = query(self.index, [CLEARPOOL])["events"]
        boundary = int(all_rows[0]["row"]["transaction"]["timestamp"])
        filtered = query(self.index, [CLEARPOOL], time_start=boundary, time_end=boundary)
        self.assertTrue(all(int(item["row"]["transaction"]["timestamp"]) == boundary for item in filtered["events"]))

    def test_reversed_time_filter_is_rejected(self):
        self.build_index()
        with self.assertRaisesRegex(AlexandriaError, "after"):
            query(self.index, [CLEARPOOL], time_start="2", time_end="1")

    def test_invalid_address_is_rejected(self):
        self.build_index()
        with self.assertRaisesRegex(AlexandriaError, "20-byte"):
            query(self.index, ["not-an-address"])

    def test_every_result_row_names_release_and_raw_object(self):
        self.build_index()
        for item in query(self.index, [CLEARPOOL])["events"]:
            self.assertEqual(item["release_id"], self.derived_id)
            self.assertEqual(item["row_id"], item["row"]["id"])
            self.assertEqual(item["row"]["provenance"]["source_release_id"], self.raw_id)
            self.assertRegex(item["row"]["provenance"]["component_sha256"], r"^sha256:")

    def test_full_dataset_coverage_can_prove_empty(self):
        source = self.source_json("aave-v4-source")
        source["logs"] = []
        self.write_source("aave-v4-source", source)
        coverage = self.plan["captures"][0]["coverage"]
        for collection in coverage["collections"]:
            if collection["selector"] == "/logs":
                coverage["record_count"] -= collection["record_count"]
                collection["record_count"] = 0
        self._write_plan()
        self.build_index()
        aave_v4 = next(item for item in query(self.index, [UNKNOWN])["coverage"] if item["venue"] == "aave-v4")
        self.assertEqual((aave_v4["status"], aave_v4["empty_allowed"]), ("covered", True))

    def test_complete_mapping_coverage_permits_an_empty_answer(self):
        """No shipped mapping leaves an unsupported collection any more.

        The Aave v4 capture is a topic pair over a block range, so every
        captured log is mapped and an unknown subject can be answered empty.
        The refusal path for a venue that does leave collections unmapped has
        no shipped example; it is still enforced by the coverage contract.
        """
        self.build_index()
        aave_v4 = next(item for item in query(self.index, [UNKNOWN])["coverage"] if item["venue"] == "aave-v4")
        self.assertEqual((aave_v4["status"], aave_v4["empty_allowed"]), ("covered", True))

    def test_subject_scope_refuses_false_empty(self):
        self.build_index()
        clearpool = next(item for item in query(self.index, [UNKNOWN])["coverage"] if item["venue"] == "clearpool")
        self.assertEqual((clearpool["status"], clearpool["empty_allowed"]), ("uncovered", False))

    def test_partial_capture_refuses_empty(self):
        self.plan["captures"][0]["coverage"]["status"] = "partial"
        self.plan["captures"][0]["coverage"]["gaps"] = ["provider completeness not established"]
        self._write_plan()
        self.build_index()
        aave_v4 = next(item for item in query(self.index, [UNKNOWN])["coverage"] if item["venue"] == "aave-v4")
        self.assertEqual((aave_v4["status"], aave_v4["empty_allowed"]), ("partial", False))

    def test_time_filtered_block_coverage_refuses_false_empty(self):
        self.build_index()
        clearpool = next(item for item in query(self.index, [CLEARPOOL], time_start="1")["coverage"] if item["venue"] == "clearpool")
        self.assertFalse(clearpool["empty_allowed"])

    def test_open_ended_time_filter_refuses_snapshot_empty(self):
        self.build_index()
        aave_v4 = next(item for item in query(self.index, [UNKNOWN], time_start="1")["coverage"] if item["venue"] == "aave-v4")
        self.assertFalse(aave_v4["empty_allowed"])

    def test_query_is_offline(self):
        self.build_index()
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network attempted")):
            self.assertEqual(query(self.index, [CLEARPOOL])["format"], "alexandria-address-query/v1")

    def test_log_mappings_answer_with_events_and_no_position(self):
        borrower = "0x" + self.source_json("aave-v4-source")["logs"][0]["topics"][2][26:]
        self.build_index()
        answer = query(self.index, [borrower])
        self.assertTrue(answer["events"])
        self.assertEqual(answer["observations"], [])

    def test_cli_emits_canonical_json(self):
        self.build_index()
        result = subprocess.run(
            [sys.executable, str(COMMAND), "query", "--index", str(self.index), "--address", CLEARPOOL],
            capture_output=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertEqual(result.stdout, canonical_bytes(json.loads(result.stdout)))


class ProbitasBridgeTests(IndexTestCase):
    def test_translation_retains_venue_and_evidence(self):
        self.build_index()
        translated = translate(self.index, [CLEARPOOL])
        record = next(item for item in translated["records"] if item["venue"] == "clearpool")
        self.assertEqual(record["values"]["evidence_class"], "archive-log")
        self.assertEqual(record["values"]["source_release_id"], self.raw_id)

    def test_translation_does_not_copy_the_operator_chosen_index_name(self):
        self.build_index()
        renamed = self.index.with_name("index|injected-column.sqlite")
        self.index.rename(renamed)
        translated = translate(renamed, [CLEARPOOL])
        self.assertEqual(
            {item["endpoint"] for item in translated["coverage"]},
            {"Alexandria index"},
        )

    def test_translation_does_not_infer_credit_conclusions(self):
        self.build_index()
        text = json.dumps(translate(self.index, [CLEARPOOL]), sort_keys=True)
        for forbidden in ("defaulted", "fully_repaid", "current_balance", "person_name"):
            self.assertNotIn(forbidden, text)

    def test_uncovered_archive_query_is_a_gap_not_empty(self):
        self.build_index()
        translated = translate(self.index, [UNKNOWN])
        clearpool = next(item for item in translated["coverage"] if item["venue"] == "clearpool")
        self.assertEqual(clearpool["status"], "error")
        self.assertTrue(any(item["subject"].startswith("clearpool") for item in translated["gaps"]))

    def test_multichain_coverage_is_aggregated_conservatively(self):
        self.build_index()
        covered = {
            "captures": [], "chain": "eip155:1", "empty_allowed": True,
            "records": 3, "requested_addresses": {CLEARPOOL: True},
            "status": "covered", "venue": "clearpool",
        }
        partial = {
            "captures": [], "chain": "eip155:2", "empty_allowed": False,
            "records": 0, "requested_addresses": {CLEARPOOL: False},
            "status": "uncovered", "venue": "clearpool",
        }
        with mock.patch(
            "alexandria_lib.probitas.query",
            return_value={"events": [], "observations": [], "coverage": [covered, partial]},
        ):
            translated = translate(self.index, [CLEARPOOL])
        self.assertEqual(len(translated["coverage"]), 1)
        self.assertEqual(translated["coverage"][0]["status"], "error")
        self.assertEqual(translated["coverage"][0]["records"], 3)
        self.assertIn("eip155:2=uncovered", translated["gaps"][0]["reason"])

    def test_probitas_cli_keeps_all_registry_coverage_rows(self):
        self.build_index()
        result = self._collect(CLEARPOOL)
        self.assertEqual(len(result["coverage"]), 15)
        self.assertEqual({row["venue"] for row in result["records"]}, {"clearpool"})

    def test_probitas_archive_evidence_passes_all_five_gates(self):
        self.build_index()
        evidence = self.root / "evidence.json"
        dossier = self.root / "dossier.md"
        collected = subprocess.run(self._command(CLEARPOOL, str(evidence)), capture_output=True, text=True, check=False)
        self.assertEqual(collected.returncode, 0, collected.stderr)
        rendered = subprocess.run([sys.executable, str(PROBITAS), "render", str(evidence), "--out", str(dossier)], capture_output=True, text=True, check=False)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        verified = subprocess.run([sys.executable, str(PROBITAS), "verify", str(dossier), str(evidence)], capture_output=True, text=True, check=False)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual(len(verified.stdout.strip().splitlines()), 5)

    def test_aave_v4_event_keeps_its_evidence_class(self):
        """No mapping emits a position observation now; events carry the class."""
        borrower = "0x" + self.source_json("aave-v4-source")["logs"][0]["topics"][2][26:]
        self.build_index()
        result = self._collect(borrower)
        self.assertFalse(
            any(row["claim"] == "position_observation" for row in result["records"])
        )
        self.assertEqual(
            {item["row"]["provenance"]["evidence_class"]
             for item in query(self.index, [borrower])["events"]},
            {"archive-log"},
        )

    def test_default_fixture_path_remains_available(self):
        result = subprocess.run(
            [sys.executable, str(PROBITAS), "collect", "--entity", "Acme", "--address", CLEARPOOL,
             "--fixtures", str(Path(__file__).resolve().parents[2] / "probitas" / "tests" / "fixtures" / "empty"), "--out", "-"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_probitas_gathers_fixture_and_archive_evidence_in_one_run(self):
        """The union issue 391 asked for, offline and end to end."""
        self.build_index()
        fixture = Path(__file__).resolve().parents[2] / "probitas" / "tests" / "fixtures" / "empty"
        result = subprocess.run(
            self._command(CLEARPOOL)[:-2] + ["--fixtures", str(fixture), "--out", "-"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        sources = {row["venue"]: row["source"] for row in payload["coverage"]}
        self.assertEqual(sources["clearpool"], "archive")
        for venue in ("wildcat", "morpho-blue", "euler", "euler-v1"):
            with self.subTest(venue=venue):
                self.assertEqual(sources[venue], "fixtures")
        archive = next(r for r in payload["coverage"] if r["venue"] == "clearpool")
        self.assertTrue(archive["releases"])
        self.assertTrue(payload["records"])
        self.assertEqual({r["venue"] for r in payload["records"]}, {"clearpool"})

    def test_probitas_still_reaches_no_adapter_on_an_index_alone(self):
        """No invocation that worked before starts making requests."""
        self.build_index()
        payload = self._collect(CLEARPOOL)
        adapter_rows = [
            row for row in payload["coverage"] if row["source"] in ("live", "fixtures")
        ]
        self.assertEqual(adapter_rows, [])

    def test_probitas_refuses_live_and_fixture_backings_together(self):
        self.build_index()
        fixture = Path(__file__).resolve().parents[2] / "probitas" / "tests" / "fixtures" / "empty"
        result = subprocess.run(
            self._command(CLEARPOOL)[:-2]
            + ["--fixtures", str(fixture), "--live", "--out", "-"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with", result.stderr)

    def test_standalone_probitas_refuses_archive_mode_without_alexandria(self):
        standalone = self.root / "standalone" / "probitas"
        shutil.copytree(PROBITAS.parents[1], standalone)
        result = subprocess.run(
            [
                sys.executable,
                str(standalone / "scripts" / "probitas.py"),
                "collect",
                "--entity",
                "Acme",
                "--address",
                CLEARPOOL,
                "--alexandria-index",
                str(self.root / "missing.sqlite"),
                "--out",
                "-",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not installed beside Probitas", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def _command(self, address, output="-"):
        return [
            sys.executable, str(PROBITAS), "collect", "--entity", "Acme",
            "--address", address, "--alexandria-index", str(self.index), "--out", output,
        ]

    def _collect(self, address):
        result = subprocess.run(self._command(address), capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)
