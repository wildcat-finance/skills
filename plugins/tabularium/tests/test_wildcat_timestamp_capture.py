"""Constructed producer captures and hostile event-header inventory boundaries."""

from contextlib import redirect_stderr
from copy import deepcopy
import io
import json
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from test_wildcat_view import release_fixture, _transport
from alexandria_lib import event_headers, interval
from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.errors import AlexandriaError
import usdc_interval as collector


class HeaderTransport(_transport.FixtureTransport):
    def request(self, payload, label):
        response = json.loads(super().request(payload, label))
        if json.loads(payload)["method"] == "eth_getBlockByNumber":
            response["result"]["timestamp"] = hex(1_800_000_000 + int(response["result"]["number"], 16))
        return canonical_bytes(response)


def captured(root, generation, *, split=False, reuse=False):
    saved = {}
    def edit(state, registry):
        state["plan"][event_headers.FIELD] = event_headers.RULE
        if split:
            state["plan"][interval.SPLIT_FIELD] = 1
        # Four family observations across three blocks, one shared pair.
        logs = state["logs"]["0"]
        for log in logs:
            if log["topics"][0] in event_headers.TOPICS:
                delta = 1 if log["topics"][0] == sorted(event_headers.TOPICS)[0] else 2
                number = int(log["blockNumber"], 16) + delta
                if reuse and log["topics"][0] == "0x9dc30b8eda31a6a144e092e5de600955523a6a925cc15cc1d1b9b4872cfa6155":
                    number = state["plan"]["shards"][0]["end"]
                transport = HeaderTransport(state)
                log.update(blockNumber=hex(number), blockHash=transport._hash(number),
                           transactionHash=transport.transactions(number)[0])
        logs.sort(key=lambda row: (int(row["blockNumber"], 16), int(row["transactionIndex"], 16), int(row["logIndex"], 16)))
        saved.update(state=state, registry=registry)
    with mock.patch.object(_transport, "FixtureTransport", HeaderTransport):
        output = release_fixture(root, generation, edit=edit)
    return output, saved["state"], saved["registry"]


class CaptureTests(unittest.TestCase):
    def test_v1_and_v2_capture_build_verify_deduplicate(self):
        for generation in event_headers.DEPLOY:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                output, state, registry = captured(Path(temporary), generation)
                with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
                    collector.check_interval(output)
                manifest = json.loads((output / "manifest.json").read_bytes())
                part = next(c for c in manifest["components"] if c["name"] == event_headers.CLASS)
                records = json.loads((output / part["object_path"]).read_bytes())["records"]
                expected = event_headers.identities(state["plan"], sum(state["logs"].values(), []), registry)
                self.assertEqual(len(records), len(expected))
                self.assertEqual(len(expected), 3)
                collector.verify_event_headers(state["plan"], expected, records)
                self.assertEqual(len({r["request"] for r in records}), 3)

    def test_split_partition_retains_one_bounded_inventory(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, state, _ = captured(Path(temporary), "wildcat-v2", split=True)
            self.assertEqual(len(collector.journal_components(state["plan"], collector.declared_classes(state["plan"]))), 3 * len(state["plan"]["shards"]) + 2)
            collector.check_interval(output)

    def test_exact_boundary_header_reuse_preserves_original_source(self):
        for generation in event_headers.DEPLOY:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                output, state, registry = captured(Path(temporary), generation, reuse=True)
                stage = interval.Staging(Path(temporary) / "staging", state["plan"])
                records = list(stage.entries(event_headers.CLASS))
                logs = sum(state["logs"].values(), [])
                pairs = collector.missing_event_headers(state["plan"], logs, registry, stage.entries(interval.OPENING_CLASS), stage.entries("boundary-blocks"))
                self.assertEqual(len(event_headers.identities(state["plan"], logs, registry)), 3)
                self.assertEqual(len(pairs), 2)
                self.assertEqual(len(records), 2)
                collector.check_interval(output)
                transport = HeaderTransport(state)
                with redirect_stderr(io.StringIO()):
                    summary = collector.Collector(state["plan"], stage.root, transport, registry=registry).collect()
                self.assertEqual(summary["event_header_reads"]["reused"], 1)
                self.assertEqual(summary["event_header_reads"]["issued"], 0)

    def test_unmatched_or_undated_existing_headers_are_not_reused(self):
        pair = (12, "0x" + "ab" * 32)
        for header in ({"number": "0xc", "hash": "0x" + "bc" * 32, "timestamp": "0x0"},
                       {"number": "0xd", "hash": pair[1], "timestamp": "0x0"},
                       {"number": "0xc", "hash": pair[1]},
                       {"number": "0xc", "hash": pair[1], "timestamp": "0x00"}):
            self.assertEqual(event_headers.missing([pair], [header]), [pair])
        self.assertEqual(event_headers.missing([pair], [{"number": "0xc", "hash": pair[1], "timestamp": "0x0"}]), [])
        zero = {"number": "0xc", "hash": pair[1], "timestamp": "0x0"}
        one = dict(zero, timestamp="0x1")
        self.assertEqual(event_headers.missing([pair], [zero, dict(zero)]), [])
        for headers in ([zero, one], [one, zero]):
            with self.assertRaisesRegex(AlexandriaError, "disagree about their timestamp"):
                event_headers.missing([pair], headers)

    def test_changed_retained_prefix_refuses_fixed_checkpoint_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, state, _ = captured(Path(temporary), "wildcat-v2")
            staging = Path(temporary) / "staging"
            path = staging / "journals" / (event_headers.CLASS + ".jsonl")
            content = path.read_bytes()
            records = [json.loads(line) for line in content.splitlines()]
            response = json.loads(records[0]["response"])
            response["result"]["timestamp"] = hex(int(response["result"]["timestamp"], 16) + 1)
            records[0]["response"] = canonical_bytes(response).decode()
            changed = b"".join(canonical_bytes(row) for row in records)
            self.assertEqual(len(changed), len(content))
            path.write_bytes(changed)
            with self.assertRaisesRegex(AlexandriaError, "digest differs"):
                interval.Staging(staging, state["plan"]).resume()
            self.assertEqual(path.read_bytes(), changed)
            path.write_bytes(content)
            checkpoint = staging / interval.CHECKPOINT_NAME
            original = checkpoint.read_bytes()
            document = json.loads(original)
            document["offsets"][event_headers.CLASS] -= 1
            document["history"][-1]["offsets"][event_headers.CLASS] -= 1
            checkpoint.write_bytes(canonical_bytes(document))
            with self.assertRaisesRegex(AlexandriaError, "digest differs"):
                interval.Staging(staging, state["plan"]).resume()
            self.assertEqual(path.read_bytes(), content)
            document = json.loads(original)
            del document["event_headers_sha256"]
            checkpoint.write_bytes(canonical_bytes(document))
            with self.assertRaises(AlexandriaError):
                interval.Staging(staging, state["plan"]).resume()
            checkpoint.write_bytes(original)
            path.unlink()
            with self.assertRaises(AlexandriaError):
                interval.Staging(staging, state["plan"]).resume()

    def test_legacy_plans_and_inventory_unchanged(self):
        for generation in event_headers.DEPLOY:
            with self.subTest(generation=generation), tempfile.TemporaryDirectory() as temporary:
                output = release_fixture(Path(temporary), generation)
                manifest = json.loads((output / "manifest.json").read_bytes())
                self.assertNotIn(event_headers.CLASS, {c["name"] for c in manifest["components"]})
                collector.check_interval(output)

    def test_marker_shape_and_non_wildcat_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, state, _ = captured(Path(temporary), "wildcat-v2")
            for field, value in ((event_headers.FIELD, None), (event_headers.FIELD, True),
                                 (event_headers.FIELD, "neighbour"), ("venue", "compound-v3"),
                                 ("evidence_classes", ["boundary-blocks"])):
                plan = deepcopy(state["plan"])
                plan[field] = value
                with self.subTest(field=field, value=value), self.assertRaises(AlexandriaError):
                    interval.validate_plan(plan)

    def test_header_missing_malformed_mismatch_and_zero(self):
        pair = (12, "0x" + "ab" * 32)
        valid = {"number": "0xc", "hash": pair[1], "timestamp": "0x0"}
        event_headers.accept(valid, pair)
        for field, value in (("number", "0xd"), ("hash", "0x" + "bc" * 32),
                             ("timestamp", None), ("timestamp", True), ("timestamp", "0x00"),
                             ("timestamp", "0x" + "a" * 65)):
            bad = dict(valid, **{field: value})
            with self.subTest(field=field, value=value), self.assertRaises(AlexandriaError):
                event_headers.accept(bad, pair)

    def test_interrupted_prefix_resumes_only_missing_headers(self):
        with tempfile.TemporaryDirectory() as temporary, redirect_stderr(io.StringIO()):
            root = Path(temporary)
            _, state, registry = captured(root / "seed", "wildcat-v2")
            staging = root / "staging"
            staging.mkdir()
            class Interrupted(HeaderTransport):
                headers = 0
                def request(self, payload, label):
                    if label == "selected event header":
                        self.headers += 1
                        if self.headers == 2:
                            raise AlexandriaError("constructed interruption")
                    return super().request(payload, label)
            with self.assertRaises(AlexandriaError):
                collector.Collector(state["plan"], staging, Interrupted(state), registry=registry).collect()
            path = staging / "journals" / (event_headers.CLASS + ".jsonl")
            prefix = path.read_bytes()
            resumed = HeaderTransport(state)
            result = collector.Collector(state["plan"], staging, resumed, registry=registry).collect()
            self.assertEqual(result["event_header_reads"], {"issued": 2, "resumed_from": 1, "total": 3, "reused": 0})
            self.assertTrue(path.read_bytes().startswith(prefix))
            self.assertEqual(sum(label == "selected event header" for _, label in resumed.calls), 2)

    def test_incomplete_inventory_and_tampered_request_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            output, state, registry = captured(Path(temporary), "wildcat-v2")
            staging = Path(temporary) / "staging"
            records = list(interval.Staging(staging, state["plan"]).entries(event_headers.CLASS))
            pairs = event_headers.identities(state["plan"], sum(state["logs"].values(), []), registry)
            with self.assertRaises(AlexandriaError):
                collector.verify_event_headers(state["plan"], pairs, records[:-1])
            records[0]["request"] = records[1]["request"]
            with self.assertRaises(AlexandriaError):
                collector.verify_event_headers(state["plan"], pairs, records)

    def test_checkpoint_wrong_inventory_and_short_prefix_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, state, _ = captured(Path(temporary), "wildcat-v2")
            staging = Path(temporary) / "staging"
            checkpoint = staging / interval.CHECKPOINT_NAME
            original = checkpoint.read_bytes()
            document = json.loads(original)
            del document["offsets"][event_headers.CLASS]
            checkpoint.write_bytes(canonical_bytes(document))
            with self.assertRaises(AlexandriaError):
                interval.Staging(staging, state["plan"]).resume()
            checkpoint.write_bytes(original)
            (staging / "journals" / (event_headers.CLASS + ".jsonl")).write_bytes(b"")
            with self.assertRaises(AlexandriaError):
                interval.Staging(staging, state["plan"]).resume()

    def test_conflicting_event_hash_and_unselected_topics(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, state, registry = captured(Path(temporary), "wildcat-v2")
            logs = sum(state["logs"].values(), [])
            selected = next(log for log in logs if log["topics"][0] in event_headers.TOPICS)
            conflicting = dict(selected, blockHash="0x" + "bb" * 32)
            with self.assertRaises(AlexandriaError):
                event_headers.identities(state["plan"], logs + [conflicting], registry)
            unrelated = dict(conflicting, topics=["0x" + "00" * 32])
            self.assertEqual(event_headers.identities(state["plan"], logs + [unrelated], registry),
                             event_headers.identities(state["plan"], logs, registry))

    def test_symlink_journal_refuses_without_touching_target(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, state, _ = captured(Path(temporary), "wildcat-v2")
            staging = Path(temporary) / "staging"
            path = staging / "journals" / (event_headers.CLASS + ".jsonl")
            source = Path(temporary) / "source"
            source.write_bytes(path.read_bytes())
            path.unlink()
            path.symlink_to(source)
            before = source.read_bytes()
            with self.assertRaises(AlexandriaError):
                list(interval.Staging(staging, state["plan"]).entries(event_headers.CLASS))
            self.assertEqual(source.read_bytes(), before)

    def test_request_component_byte_and_time_bounds(self):
        with tempfile.TemporaryDirectory() as temporary:
            _, state, registry = captured(Path(temporary), "wildcat-v2")
            logs = sum(state["logs"].values(), [])
            with mock.patch.object(event_headers, "MAX_HEADERS", 2), self.assertRaises(AlexandriaError):
                event_headers.identities(state["plan"], logs, registry)
            legacy = dict(state["plan"])
            legacy.pop(event_headers.FIELD)
            parts = collector.journal_components(legacy, collector.declared_classes(legacy))
            cap = len(collector.FIXED_COMPONENTS) + len(parts)
            with mock.patch.object(collector, "MAX_COMPONENTS", cap):
                self.assertEqual(collector.journal_components(legacy, collector.declared_classes(legacy)), parts)
                with self.assertRaises(AlexandriaError):
                    collector.journal_components(state["plan"], collector.declared_classes(state["plan"]))
            for mode in ("bytes", "time", "journal"):
                staging = Path(temporary) / mode
                staging.mkdir()
                instance = collector.Collector(state["plan"], staging, HeaderTransport(state), registry=registry)
                original = instance._event_headers
                def limited():
                    target = collector if mode != "journal" else interval
                    name = {"bytes": "MAX_COLLECT_BYTES", "time": "MAX_COLLECT_SECONDS", "journal": "MAX_JOURNAL_BYTES"}[mode]
                    with mock.patch.object(target, name, 0), self.assertRaises(AlexandriaError):
                        original()
                    raise AlexandriaError("bounded refusal observed")
                with mock.patch.object(instance, "_event_headers", limited), redirect_stderr(io.StringIO()), self.assertRaises(AlexandriaError):
                    instance.collect()


if __name__ == "__main__":
    unittest.main()
