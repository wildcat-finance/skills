"""Row-local date support from exact preserved header identities."""

import hashlib
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from test_wildcat_timestamp_capture import captured, HeaderTransport
from test_wildcat_view import release_fixture, _transport, BORROWER
from tabularium_lib import wildcat_view, wildcat_timestamps
from tabularium_lib.core import TabulariumError
from tabularium_lib.wildcat_timestamps import HeaderIndex

PROBITAS = Path(__file__).resolve().parents[2] / "probitas/scripts"
sys.path.insert(0, str(PROBITAS))
from probitas_lib import wildcat_archive, render, gates, registry
from probitas_lib.adapters import unchecked_coverage
from probitas_lib.evidence import Evidence

EVENT = {"blockNumber": "0xc", "blockHash": "0x" + "ab" * 32}
SOURCE = {"component": "headers", "journal_selector": "/records/0/response", "selector": "/result/timestamp"}
HEADER = {"number": "0xc", "hash": EVENT["blockHash"], "timestamp": "0x0"}


class MappingTests(unittest.TestCase):
    def test_supplied_zero_is_supported(self):
        value = HeaderIndex([(HEADER, SOURCE)]).resolve(EVENT)
        self.assertEqual(value["observed_at"], 0)
        self.assertEqual(value["status"], "supported")

    def test_missing_header_is_not_zero(self):
        self.assertEqual(HeaderIndex([]).resolve(EVENT), {"status": "unsupported", "reason": "header-missing"})

    def test_wrong_hash_is_local_gap(self):
        header = dict(HEADER, hash="0x" + "bc" * 32)
        self.assertEqual(HeaderIndex([(header, SOURCE)]).resolve(EVENT)["reason"], "header-hash-mismatch")

    def test_wrong_number_is_local_gap(self):
        self.assertEqual(HeaderIndex([(dict(HEADER, number="0xd"), SOURCE)]).resolve(EVENT)["reason"], "header-number-mismatch")

    def test_missing_or_malformed_date_is_not_zero(self):
        for value in (None, "0x00", 0, True, "0x", "0x" + "f" * 65):
            with self.subTest(value=value):
                result = HeaderIndex([(dict(HEADER, timestamp=value), SOURCE)]).resolve(EVENT)
                self.assertEqual(result["reason"], "header-timestamp-missing-or-malformed")
                self.assertNotIn("observed_at", result)

    def test_conflicts_refuse_in_both_orders(self):
        candidates = [(HEADER, SOURCE), (dict(HEADER, timestamp="0x1"), SOURCE)]
        for sequence in (candidates, list(reversed(candidates))):
            self.assertEqual(HeaderIndex(sequence).resolve(EVENT)["reason"], "header-timestamps-conflict")

    def test_identical_duplicates_keep_all_sources(self):
        second = dict(SOURCE, journal_selector="/records/1/response")
        self.assertEqual(len(HeaderIndex([(HEADER, SOURCE), (HEADER, second)]).resolve(EVENT)["sources"]), 2)

    def test_duplicate_provenance_fanout_has_an_aggregate_budget(self):
        index = HeaderIndex([(HEADER, SOURCE), (HEADER, SOURCE)])
        with mock.patch.object(wildcat_timestamps, "MAX_SOURCE_REFERENCES", 2, create=True):
            self.assertEqual(index.resolve(EVENT)["status"], "supported")
            with self.assertRaisesRegex(TabulariumError, "source-reference budget"):
                index.resolve(EVENT)

    def test_conflicting_identity_is_resolved_once_without_repeated_source_work(self):
        index = HeaderIndex([(HEADER, SOURCE), (dict(HEADER, timestamp="0x1"), SOURCE)])
        index.resolve(EVENT)
        with mock.patch.object(wildcat_timestamps, "quantity", wraps=wildcat_timestamps.quantity) as parse:
            self.assertEqual(index.resolve(EVENT)["reason"], "header-timestamps-conflict")
            self.assertEqual(parse.call_count, 1)  # Only the event number, not duplicate headers.

    def test_one_bad_identity_does_not_poison_another_row(self):
        other = dict(HEADER, number="0xd", hash="0x" + "cd" * 32, timestamp="0x2")
        index = HeaderIndex([(dict(HEADER, timestamp="0x00"), SOURCE), (other, SOURCE)])
        self.assertEqual(index.resolve(EVENT)["status"], "unsupported")
        self.assertEqual(index.resolve({"blockNumber": "0xd", "blockHash": other["hash"]})["observed_at"], 2)

    def test_capture_maps_all_four_families_and_native_close_remains_separate(self):
        for generation in ("wildcat-v1", "wildcat-v2"):
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                output, _, _ = captured(Path(temporary), generation, reuse=True)
                with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
                    result = wildcat_view.make_wildcat_view(output)
                self.assertEqual({r["claim"] for r in result["records"]}, {"market_terms", "market_closed", "borrow", "repayment"})
                self.assertEqual(result["timestamp_coverage"], {"supported": 4})
                for row in result["records"]:
                    self.assertEqual(row["observed_at"], 1_800_000_000 + int(row["native"]["blockNumber"], 16))
                close = next(r for r in result["records"] if r["claim"] == "market_closed")
                self.assertEqual(close["values"]["timestamp"], "1800000000")
                self.assertNotEqual(close["observed_at"], int(close["values"]["timestamp"]))

    def test_header_selectors_and_all_digests_resolve_to_actual_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, _, _ = captured(Path(temporary), "wildcat-v2", reuse=True)
            result = wildcat_view.make_wildcat_view(output)
            components = {c["name"]: c for c in json.loads((output / "manifest.json").read_bytes())["components"]}
            seen = set()
            for row in result["records"]:
                for source in row["timestamp_support"]["sources"]:
                    seen.add(source["component"])
                    component = components[source["component"]]
                    raw = (output / component["object_path"]).read_bytes()
                    self.assertEqual(source["component_sha256"], "sha256:" + hashlib.sha256(raw).hexdigest())
                    entry = json.loads(raw)["records"][int(source["journal_selector"].split("/")[2])]
                    for field in ("request", "response"):
                        self.assertEqual(source[field + "_sha256"], "sha256:" + hashlib.sha256(entry[field].encode()).hexdigest())
                    self.assertEqual(int(json.loads(entry["response"])["result"]["timestamp"], 16), row["observed_at"])
            self.assertIn("event-block-headers", seen)
            self.assertIn("boundary-blocks", seen)

    def test_legacy_without_marker_can_reuse_recorded_boundary_header(self):
        def edit(state, _):
            end = state["plan"]["shards"][0]["end"]
            for log in state["logs"]["0"]:
                if log["topics"][0] == wildcat_view.BORROW:
                    transport = HeaderTransport(state)
                    log.update(blockNumber=hex(end), blockHash=transport._hash(end), transactionHash=transport.transactions(end)[0])
            state["logs"]["0"].sort(key=lambda row: (int(row["blockNumber"], 16), int(row["logIndex"], 16)))
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(_transport, "FixtureTransport", HeaderTransport):
            output = release_fixture(Path(temporary), "wildcat-v2", edit=edit)
            result = wildcat_view.make_wildcat_view(output)
            self.assertEqual(result["timestamp_coverage"], {"header-missing": 3, "supported": 1})
            borrow = next(r for r in result["records"] if r["claim"] == "borrow")
            self.assertEqual(borrow["timestamp_support"]["sources"][0]["component"], "boundary-blocks")
            evidence = Evidence("Synthetic borrower", [(BORROWER, "declared")])
            wildcat_archive.collect([output], evidence)
            for venue in registry.all_venues():
                if venue.id != "wildcat":
                    evidence.add_coverage(unchecked_coverage(venue, ("archive",)))
            payload = evidence.to_dict()
            self.assertEqual(sum("observed_at" in r for r in payload["records"]), 1)
            self.assertEqual(sum("observed_at_unsupported" in r["values"] for r in payload["records"]), 3)
            self.assertTrue(any("header-missing" in gap["reason"] for gap in payload["gaps"]))
            dossier = render.render(payload)
            for gate in gates.check(dossier, payload):
                self.assertTrue(gate.passed, gate.detail)

    def test_legacy_exact_opening_header_keeps_original_selector(self):
        def edit(state, _):
            start = state["plan"]["shards"][0]["start"]
            for log in state["logs"]["0"]:
                if log["topics"][0] == wildcat_view.BORROW:
                    transport = HeaderTransport(state)
                    log.update(blockNumber=hex(start), blockHash=transport._hash(start), transactionHash=transport.transactions(start)[0])
            state["logs"]["0"].sort(key=lambda row: (int(row["blockNumber"], 16), int(row["logIndex"], 16)))
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(_transport, "FixtureTransport", HeaderTransport):
            output = release_fixture(Path(temporary), "wildcat-v2", edit=edit)
            row = next(r for r in wildcat_view.make_wildcat_view(output)["records"] if r["claim"] == "borrow")
            self.assertEqual(row["timestamp_support"]["status"], "supported")
            self.assertEqual(row["timestamp_support"]["sources"][0]["component"], "epoch-evidence")

    def test_zero_survives_real_archive_and_probitas_wire(self):
        class ZeroTransport(HeaderTransport):
            def request(self, payload, label):
                response = json.loads(super().request(payload, label))
                if json.loads(payload)["method"] == "eth_getBlockByNumber":
                    response["result"]["timestamp"] = "0x0"
                return json.dumps(response).encode()
        def edit(state, _):
            state["plan"]["wildcat_event_headers"] = "selected-event-blocks/v1"
        with tempfile.TemporaryDirectory() as temporary, mock.patch.object(_transport, "FixtureTransport", ZeroTransport):
            output = release_fixture(Path(temporary), "wildcat-v2", edit=edit)
            evidence = Evidence("Synthetic borrower", [(BORROWER, "declared")])
            wildcat_archive.collect([output], evidence)
            self.assertEqual([row["observed_at"] for row in evidence.to_dict()["records"]], [0] * 4)

    def test_probitas_supplies_integer_date_and_exact_provenance(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, _, _ = captured(Path(temporary), "wildcat-v1")
            evidence = Evidence("Synthetic borrower", [(BORROWER, "declared")])
            with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
                wildcat_archive.collect([output], evidence)
            for venue in registry.all_venues():
                if venue.id != "wildcat":
                    evidence.add_coverage(unchecked_coverage(venue, ("archive",)))
            payload = evidence.to_dict()
            for row in payload["records"]:
                self.assertIs(type(row["observed_at"]), int)
                for field in ("component_sha256", "response_sha256", "request_sha256", "request_selector", "selector"):
                    self.assertIn("date_0_" + field, row["values"])
            dossier = render.render(payload)
            for gate in gates.check(dossier, payload):
                self.assertTrue(gate.passed, gate.detail)
