"""Wildcat V2 hook-call MarketState observations under adapter 1.5.0 (skills#2144).

A constructed V2 interval, collected and built through Alexandria, holds one
call from the market to its hooks instance under each of the five mapped hooks,
plus a failed call, a call under a failed parent, a call from an address that
is not a registered market and an unmapped `onBorrow` call. Each successful
mapped call becomes one observation whose fields equal the call input; the
other three stay recorded gaps, and a truncated or malformed frame refuses the
build. Every record is constructed; none was observed on a chain.
"""

from copy import deepcopy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import wildcat_hook_state_fixtures as fixture  # noqa: E402
from wildcat_accrual_public_fixtures import build_accrual_release  # noqa: E402

from tabularium_lib import verifier  # noqa: E402
from tabularium_lib.core import TabulariumError, canonical_json, sha256_bytes  # noqa: E402
from tabularium_lib.keccak import keccak256  # noqa: E402
from tabularium_lib.wildcat_hooks import (  # noqa: E402
    EVIDENCE_CLASS, GAP_REASONS, LAYOUTS, LIMITATIONS, PIN, RULE, map_hook_calls,
)
from tabularium_lib.wildcat_release import build_wildcat_canonical  # noqa: E402
from tabularium_lib.wildcat_rows import context_selector, selector  # noqa: E402
from tabularium_lib.wildcat_source import load_raw  # noqa: E402


def _document(root, name):
    return json.loads((root / name).read_bytes())


def _native(values):
    """A state as the observation states it: booleans stay JSON booleans."""
    return {name: value if isinstance(value, bool) else str(value) for name, value in values.items()}


def _frame(frames, trace_address):
    return next(frame for frame, _ in frames if frame["traceAddress"] == trace_address)


def _rows(root):
    return [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]


def _span(offset):
    """The hexadecimal character span of the calldata word at a byte offset."""
    return 2 + 2 * offset, 2 + 2 * (offset + 32)


class HookStateReleaseTests(unittest.TestCase):
    """One raw release built under 1.5.0 and under 1.4.0."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="tabularium-hook-state-")
        cls.base = Path(cls.temporary.name).resolve()
        cls.raw = fixture.raw_release(cls.base)
        cls.new = fixture.canonical_release(cls.raw, cls.base / "new", "1.5.0")
        cls.old = fixture.canonical_release(cls.raw, cls.base / "old", "1.4.0")
        cls.source = _document(cls.new, "source.json")
        cls.section = cls.source["state_observations"]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def test_each_successful_hook_call_maps_one_observation(self):
        records = self.section["records"]
        self.assertEqual([r["hook"] for r in records], [hook for hook, *_ in fixture.MAPPED])
        for record, (hook, path, _leading, seed, _extra) in zip(records, fixture.MAPPED, strict=True):
            with self.subTest(hook=hook):
                self.assertEqual(record["market_state"], _native(fixture.state(seed)))
                self.assertEqual(list(record["market_state"]), sorted(fixture.FIELDS))
                self.assertEqual((record["market"], record["hooks_instance"]), (fixture.MARKET, fixture.HOOKS))
                self.assertEqual(record["transaction"], {
                    "hash": fixture.ACTIVITY, "block_hash": _frame_hash(), "block_number": fixture.START,
                    "transaction_index": 1, "trace_address": path})
                self.assertEqual((record["evidence_class"], record["rule"]), (EVIDENCE_CLASS, RULE))
                self.assertEqual(record["signature"], fixture.LAYOUT[hook][0])
                self.assertEqual(record["selector"], "0x" + keccak256(record["signature"].encode())[:4].hex())

    def test_failed_and_unregistered_calls_stay_recorded_gaps(self):
        gaps = [(g["hook"], g["reason"], g["transaction"]["trace_address"]) for g in self.section["gaps"]]
        self.assertEqual(gaps, [("onDeposit", "failed-call", [5]),
                                ("onRepay", "failed-ancestor", [6, 0]),
                                ("onTransfer", "caller-not-registered-market", [7])])
        for gap in self.section["gaps"]:
            self.assertIn(gap["reason"], GAP_REASONS)
            self.assertEqual(gap["gap"], "hook-state:%s:%s" % (gap["hook"], gap["reason"]))
            self.assertNotIn("market_state", gap)
        self.assertEqual(self.section["gaps"][2]["caller"], fixture.STRANGER)

    def test_on_borrow_and_other_hooks_stay_unmapped(self):
        paths = [item["transaction"]["trace_address"] for item in self.section["records"] + self.section["gaps"]]
        self.assertNotIn([8], paths)
        self.assertEqual({LAYOUTS[key]["hook"] for key in LAYOUTS},
                         {"onDeposit", "onQueueWithdrawal", "onTransfer", "onExecuteWithdrawal", "onRepay"})

    def test_each_observation_cites_its_frame_and_context(self):
        frames = fixture.activity_frames()
        registry = next(item for item in self.source["contexts"][fixture.MARKET]["source"]
                        if item["class"] == "checked-registry-context")
        for record in self.section["records"]:
            with self.subTest(hook=record["hook"]):
                self.assertEqual(record["source_selector"], selector(record["reference"]))
                self.assertEqual(record["reference"]["selector"].split("/")[1], "result")
                self.assertEqual(record["native_record"], _frame([(f, None) for f in frames],
                                                                 record["transaction"]["trace_address"]))
                self.assertIn(context_selector(registry), record["supporting_selectors"])
                self.assertEqual(record["limitations"], list(LIMITATIONS))

    def test_section_names_its_pinned_source_and_coverage(self):
        self.assertEqual(self.section["coverage"], "recorded-trace-frames")
        self.assertEqual(self.section["source"]["commit"], PIN)
        self.assertEqual(sorted(self.section["source"]["units"]),
                         ["src/access/IHooks.sol", "src/libraries/MarketState.sol", "src/types/HooksConfig.sol"])

    def test_older_adapter_versions_carry_no_observation(self):
        old = _document(self.old, "source.json")
        self.assertNotIn("state_observations", old)
        self.assertEqual({key: value for key, value in self.source.items() if key != "state_observations"}, old)
        new_rows, old_rows = _rows(self.new), _rows(self.old)
        for rows, version in ((new_rows, "1.5.0"), (old_rows, "1.4.0")):
            for row in rows:
                self.assertEqual(row["provenance"].pop("adapter_version"), version)
        self.assertEqual(new_rows, old_rows)
        self.assertEqual(_document(self.new, "coverage.json")["coverage"], _document(self.old, "coverage.json")["coverage"])

    def test_verify_rechecks_every_observation_byte(self):
        for change in ("value", "boolean", "drop-gap"):
            with self.subTest(change=change), tempfile.TemporaryDirectory() as temporary:
                target = Path(temporary).resolve() / "release"
                shutil.copytree(self.new, target)
                source = _document(target, "source.json")
                section = source["state_observations"]
                if change == "value":
                    section["records"][0]["market_state"]["scaleFactor"] = "1"
                elif change == "boolean":
                    section["records"][1]["market_state"]["isDelinquent"] = False
                else:
                    section["gaps"].pop()
                data = canonical_json(source) + b"\n"
                (target / "source.json").write_bytes(data)
                coverage = _document(target, "coverage.json")
                coverage["source"].update(sha256=sha256_bytes(data), bytes=len(data))
                (target / "coverage.json").write_bytes(canonical_json(coverage) + b"\n")
                with self.assertRaises(TabulariumError):
                    verifier.verify(target / "coverage.json")


def _frame_hash():
    return fixture._hash(fixture.VENUE, "block", fixture.START)


class HookStateRefusalTests(unittest.TestCase):
    """Malformed frames refuse; failed or foreign calls never do."""

    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix="tabularium-hook-refusal-")
        cls.base = Path(cls.temporary.name).resolve()
        cls.raw = fixture.raw_release(cls.base)
        admitted = load_raw(cls.raw, hook_state=True)
        cls.contexts, cls.traces = admitted["contexts"], admitted["hook_traces"]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def mutated(self, trace_address, change):
        traces = deepcopy(self.traces)
        change(_frame(traces[fixture.ACTIVITY], trace_address))
        return traces

    def assert_refused(self, trace_address, change, message):
        with self.assertRaises(TabulariumError) as caught:
            map_hook_calls(fixture.VENUE, self.contexts, self.mutated(trace_address, change))
        self.assertIn(message, str(caught.exception))

    def test_default_admission_holds_no_hook_frames(self):
        self.assertIsNone(load_raw(self.raw)["hook_traces"])
        self.assertTrue(self.traces)

    def test_truncated_market_state_refuses_the_build(self):
        frames = fixture.activity_frames()
        deposit = _frame([(f, None) for f in frames], [0])
        deposit["action"]["input"] = deposit["action"]["input"][:2 + 2 * (4 + 0x40 + 32 * 10)]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            raw = fixture.raw_release(base, frames)
            with self.assertRaises(TabulariumError) as caught:
                build_wildcat_canonical(raw, base / "new", "constructed-truncated", "1.5.0")
            self.assertIn("truncated", str(caught.exception))
            self.assertFalse((base / "new").exists())
            fixture.canonical_release(raw, base / "old", "1.4.0")

    def test_words_outside_their_declared_width_refuse(self):
        layout = LAYOUTS["0x83d9e1eb"]
        state = 4 + layout["state_offset"]
        cases = (
            ("isClosed", state, 2, "neither zero nor one"),
            ("isDelinquent", state + 32 * 7, 2, "neither zero nor one"),
            ("scaledTotalSupply", state + 32 * 4, 1 << 104, "exceeds its declared width"),
            ("scaleFactor", state + 32 * 12, 1 << 112, "exceeds its declared width"),
            ("protocolFeeBips", state + 32 * 9, 1 << 16, "exceeds its declared width"),
            ("extraData offset", 4 + layout["extra_head"], 0x40, "extraData offset"),
            ("extraData length", 4 + layout["extra_head"] + 32, 1, "extraData length"),
        )
        for name, offset, value, message in cases:
            with self.subTest(field=name):
                def change(frame, offset=offset, value=value):
                    start, end = _span(offset)
                    text = frame["action"]["input"]
                    frame["action"]["input"] = text[:start] + value.to_bytes(32, "big").hex() + text[end:]
                self.assert_refused([4], change, message)

    def test_leading_address_padding_refuses(self):
        def change(frame):
            text = frame["action"]["input"]
            frame["action"]["input"] = text[:10] + "ff" + text[12:]
        self.assert_refused([0], change, "nonzero padding")

    def test_frames_off_the_market_hook_binding_refuse(self):
        other_hooks = next(address for address, context in self.contexts.items()
                           if context["role"] == "hooks-instance" and address != fixture.HOOKS)
        cases = (
            ("target-role", lambda f: f["action"].update(to=fixture.MARKET), "registered hooks instance"),
            ("target-binding", lambda f: f["action"].update(to=other_hooks), "deployment hooks"),
            ("call-type", lambda f: f["action"].update(callType="delegatecall"), "plain call"),
            ("trace-address", lambda f: f.update(traceAddress=[-1]), "trace address"),
            ("block-hash", lambda f: f.update(blockHash="0x12"), "blockHash"),
            ("non-hex", lambda f: f["action"].update(input=f["action"]["input"] + "0"), "hexadecimal"),
        )
        for name, change, message in cases:
            with self.subTest(case=name):
                self.assert_refused([2], change, message)

    def test_a_repeated_frame_identity_refuses(self):
        traces = deepcopy(self.traces)
        frames = traces[fixture.ACTIVITY]
        frame, reference = next(item for item in frames if item[0]["traceAddress"] == [1])
        frames.append((deepcopy(frame), dict(reference, selector="/result/99")))
        with self.assertRaises(TabulariumError) as caught:
            map_hook_calls(fixture.VENUE, self.contexts, traces)
        self.assertIn("repeats a trace identity", str(caught.exception))

    def test_failed_calls_never_refuse_on_malformed_input(self):
        def change(frame):
            frame["action"]["input"] = frame["action"]["input"][:20]
        section = map_hook_calls(fixture.VENUE, self.contexts, self.mutated([5], change))
        self.assertEqual([g["reason"] for g in section["gaps"]][0], "failed-call")
        self.assertEqual(len(section["records"]), len(fixture.MAPPED))

    def test_releases_without_trace_frames_state_no_coverage(self):
        self.assertIsNone(map_hook_calls("wildcat-v1", self.contexts, self.traces))
        empty = map_hook_calls(fixture.VENUE, self.contexts, None)
        self.assertEqual((empty["coverage"], empty["records"], empty["gaps"]), ("not-established", [], []))
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary).resolve()
            for venue in ("wildcat-v1", "wildcat-v2"):
                build_accrual_release(base / venue, venue, "constructed-hook-state-" + venue, "1.5.0")
                source = _document(base / venue, "source.json")
                if venue == "wildcat-v1":
                    self.assertNotIn("state_observations", source)
                else:
                    self.assertEqual(source["state_observations"]["coverage"], "not-established")
                    self.assertEqual(source["state_observations"]["records"], [])

    def test_selectors_and_sizes_match_the_pinned_layout(self):
        for layout in LAYOUTS.values():
            with self.subTest(hook=layout["hook"]):
                signature, state, head, base = fixture.LAYOUT[layout["hook"]]
                self.assertEqual(layout["signature"], signature)
                self.assertEqual(layout["selector"], "0x" + keccak256(signature.encode())[:4].hex())
                self.assertEqual((layout["state_offset"], layout["extra_head"], layout["base_size"]),
                                 (state, head, base))


if __name__ == "__main__":
    unittest.main()
