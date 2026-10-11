"""Executed constructed capture, offline projection and dossier boundaries."""

import hashlib
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

from test_wildcat_timestamp_mapping import (BORROWER, Evidence, gates, registry,
                                            render, unchecked_coverage,
                                            wildcat_archive, wildcat_view)
from test_wildcat_timestamp_capture import captured, HeaderTransport
from test_wildcat_view import release_fixture, _transport
from alexandria_lib import event_headers, interval
from alexandria_lib.errors import AlexandriaError
import usdc_interval as collector

FAMILIES = {"market_terms", "market_closed", "borrow", "repayment"}
GENERATIONS = ("wildcat-v1", "wildcat-v2")


def dossier_roundtrip(release):
    evidence = Evidence("Synthetic borrower", [(BORROWER, "declared")])
    wildcat_archive.collect([release], evidence)
    for venue in registry.all_venues():
        if venue.id != "wildcat":
            evidence.add_coverage(unchecked_coverage(venue, ("archive",)))
    payload = json.loads(json.dumps(evidence.to_dict()))
    text = render.render(payload)
    checked = gates.check(text, payload)
    if not checked or not all(gate.passed for gate in checked):
        raise AssertionError("constructed dossier gates failed")
    return payload, len(checked)


class DemonstrationTests(unittest.TestCase):
    observations = {}

    @classmethod
    def setUpClass(cls):
        cls.observations = {}

    def test_capture_offline_rebuild_and_dossier_both_generations(self):
        observations = []
        for generation in GENERATIONS:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary).resolve()
                release, state, _ = captured(root, generation, reuse=True)
                before = {str(p.relative_to(release)): hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in release.rglob("*") if p.is_file()}
                with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
                    collector.check_interval(release)
                    output = root / "view.json"
                    built = wildcat_view.build_wildcat_view(release, output)
                    self.assertEqual(wildcat_view.verify_wildcat_view(release, output), built)
                    projected = json.loads(output.read_bytes())
                    payload, gate_count = dossier_roundtrip(release)
                self.assertEqual({r["claim"] for r in projected["records"]}, FAMILIES)
                self.assertEqual(projected["timestamp_coverage"], {"supported": 4})
                self.assertEqual(len(payload["records"]), 4)
                self.assertTrue(all(type(r["observed_at"]) is int for r in payload["records"]))
                for row in payload["records"]:
                    self.assertIn("date_0_response_sha256", row["values"])
                close = next(r for r in projected["records"] if r["claim"] == "market_closed")
                self.assertNotEqual(close["observed_at"], int(close["values"]["timestamp"]))
                self.assertEqual(before, {str(p.relative_to(release)): hashlib.sha256(p.read_bytes()).hexdigest()
                                          for p in release.rglob("*") if p.is_file()})
                journal = list(interval.Staging(root / "staging", state["plan"]).entries(event_headers.CLASS))
                observations.append({"generation": generation, "archive_rows": 4,
                                     "families": sorted(FAMILIES), "supported": 4,
                                     "selected_distinct_blocks": 3, "reused_headers": 1,
                                     "added_header_requests": len(journal),
                                     "journal_bytes": (root / "staging/journals/event-block-headers.jsonl").stat().st_size,
                                     "request_response_bytes": sum(len(r[f].encode()) for r in journal for f in ("request", "response")),
                                     "dossier_gates": gate_count, "raw_release_unchanged": True})
        self.observations["capture-to-dossier"] = observations

    def test_wrong_hash_refuses_new_capture(self):
        class WrongHash(HeaderTransport):
            def request(self, payload, label):
                response = json.loads(super().request(payload, label))
                if label == "selected event header":
                    response["result"]["hash"] = "0x" + "ff" * 32
                return json.dumps(response).encode()
        for generation in GENERATIONS:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                with mock.patch.object(_transport, "FixtureTransport", WrongHash), self.assertRaises(AlexandriaError):
                    release_fixture(Path(temporary), generation, edit=lambda state, _: state["plan"].update({event_headers.FIELD: event_headers.RULE}))
        self.observations["wrong-hash-refused"] = True

    def test_incomplete_journal_refuses_offline_inventory(self):
        for generation in GENERATIONS:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                _, state, pinned = captured(Path(temporary), generation)
                entries = list(interval.Staging(Path(temporary) / "staging", state["plan"]).entries(event_headers.CLASS))
                pairs = event_headers.identities(state["plan"], sum(state["logs"].values(), []), pinned)
                with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), self.assertRaises(AlexandriaError):
                    collector.verify_event_headers(state["plan"], pairs, entries[:-1])
        self.observations["incomplete-inventory-refused"] = True

    def test_legacy_mixed_dates_survive_offline_dossier(self):
        def edit(state, _):
            end = state["plan"]["shards"][0]["end"]
            transport = HeaderTransport(state)
            for log in state["logs"]["0"]:
                if log["topics"][0] == wildcat_view.BORROW:
                    log.update(blockNumber=hex(end), blockHash=transport._hash(end),
                               transactionHash=transport.transactions(end)[0])
            state["logs"]["0"].sort(key=lambda r: (int(r["blockNumber"], 16), int(r["logIndex"], 16)))
        for generation in GENERATIONS:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                with mock.patch.object(_transport, "FixtureTransport", HeaderTransport):
                    release = release_fixture(Path(temporary), generation, edit=edit)
                with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
                    result = wildcat_view.make_wildcat_view(release)
                    payload, _ = dossier_roundtrip(release)
                self.assertEqual(result["timestamp_coverage"], {"supported": 1, "header-missing": 3})
                self.assertEqual(sum("observed_at" in r for r in payload["records"]), 1)
                self.assertEqual(sum(r["values"].get("observed_at_unsupported") == "header-missing" for r in payload["records"]), 3)
        self.observations["legacy-mixed-dates"] = True

    def test_legacy_absence_does_not_supply_zero(self):
        for generation in GENERATIONS:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                release = release_fixture(Path(temporary), generation)
                with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
                    projected = wildcat_view.make_wildcat_view(release)
                    payload, _ = dossier_roundtrip(release)
                self.assertEqual(projected["timestamp_coverage"], {"header-missing": 4})
                self.assertTrue(all("observed_at" not in r for r in payload["records"]))
        self.observations["legacy-absence-undated"] = True
