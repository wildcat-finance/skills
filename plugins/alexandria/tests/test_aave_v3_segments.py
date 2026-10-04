"""The Aave V3 preflight record and the segment table derived from it.

`SegmentTableTests`, `SegmentBudgetTests` and `PreflightRecordTests` are loaded
by name: the Aave conformance harness resolves `segment-plans-tile-the-interval`,
`segment-budget-within-ceilings` and `preflight-measurement-recorded` against
them. Every other case here covers a clause of the same runbook step.

`examples/aave-v3-interval-v0/preflight.json` holds what the preflight
measured on both transports: counts, bytes, timings, hashes and the command
lines that produced them. `derive` below is the one rule that turns that record
into a shard width, a `shards_per_component`, a trace concurrency and the
segment boundaries, and `segments.json` with its `plans/segment-<index>.json`
files is what that rule wrote. The tests re-derive the table from the record
and compare it with the committed bytes, so a figure edited in either place
without the other fails here.

The estimates are upper bounds from sampled windows, not measurements of the
segments themselves. Step 7's collection measures each segment; a segment whose
real bytes, nodes or log counts exceed what this table planned refuses in the
collector or builder by name, and the table changes rather than the subject set.
"""

from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import unittest
from unittest import mock

PLUGIN = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN.parents[1]
sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib import canonical  # noqa: E402
from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import (  # noqa: E402
    MAX_JOURNAL_BYTES,
    MAX_PAGE_LIMIT,
    MAX_SHARD_WIDTH,
    MAX_SHARDS,
    PARTS_FIELD,
    PARTS_RULE,
    SPLIT_FIELD,
    plan_digest,
    plan_shards,
    validate_plan,
)
from alexandria_lib.release import MAX_COMPONENTS, MAX_RAW_COMPONENT_BYTES  # noqa: E402
from alexandria_lib.venues import aave_v3  # noqa: E402
import usdc_interval  # noqa: E402
from usdc_interval import (  # noqa: E402
    FIXED_COMPONENTS,
    MAX_PART_BYTES,
    MAX_PART_NODES,
    MAX_RESPONSE_NODES,
    attribution_parts,
    journal_components,
)

EXAMPLE = PLUGIN / "examples" / "aave-v3-interval-v0"
PREFLIGHT = EXAMPLE / "preflight.json"
SEGMENTS = EXAMPLE / "segments.json"
REGISTRY = EXAMPLE / "registry.json"
TARGETS = REPO_ROOT / "docs" / "kickoff" / "1359" / "targets.json"
PREFLIGHT_FORMAT = "alexandria-aave-v3-preflight/v1"
SEGMENTS_FORMAT = "alexandria-aave-v3-segment-table/v1"
# The local node's eth_getLogs answer limit, the figure the runbook step names;
# the record's probe shows the node refusing one width past it.
LOCAL_LOG_ANSWER_LIMIT = 20_000
# `{"id", "jsonrpc", "result"}` around a shard's logs or kept trace frames:
# the object, its two scalar values and the result list. Each such record is
# written and read under `MAX_RESPONSE_NODES` (`Collector._targeted_traces`,
# `staged_results` and `preserved_result` in `scripts/usdc_interval.py`).
RECORD_ENVELOPE_NODES = 4
# The journal ranges one split plan may carry: `journal_components` counts 7
# components plus 4 per range against `MAX_COMPONENTS`, which
# `docs/usdc-interval-collector.md` states as at most 4,094 ranges.
MAX_RANGES = (MAX_COMPONENTS - 7) // 4
EVIDENCE_CLASSES = ["boundary-blocks", "logs", "traces"]
SCRIPT = "python3 plugins/alexandria/scripts/usdc_interval.py"


def load(path):
    return json.loads(path.read_bytes())


def preflight():
    if not PREFLIGHT.is_file():
        raise AssertionError(f"the Aave preflight record is missing at {PREFLIGHT}")
    return load(PREFLIGHT)


def segments():
    if not SEGMENTS.is_file():
        raise AssertionError(f"the Aave segment table is missing at {SEGMENTS}")
    return load(SEGMENTS)


def registry():
    return load(REGISTRY)


def ruled_interval():
    """The merged aave-v3 row's start and end blocks with their hashes."""
    rows = [row for row in load(TARGETS)["targets"] if row.get("id") == "aave-v3"]
    if len(rows) != 1:
        raise AssertionError("targets.json carries no single aave-v3 row")
    deployment = rows[0]["deployment"]
    return {
        "start": deployment["start_block"]["number"],
        "start_hash": deployment["start_block"]["hash"],
        "end": deployment["observed_block"]["number"],
        "end_hash": deployment["observed_block"]["hash"],
    }


def field(document, *path):
    """One nested field, refused by its dotted name when it is absent."""
    value = document
    for index, key in enumerate(path):
        if not isinstance(value, dict) or key not in value:
            raise AlexandriaError(
                f"the preflight record has no field {'.'.join(path[:index + 1])}"
            )
        value = value[key]
    return value


def fraction(value, name):
    """A recorded ratio: a two-integer [numerator, denominator] list."""
    if (
        not isinstance(value, list) or len(value) != 2
        or not all(isinstance(item, int) and not isinstance(item, bool) for item in value)
        or value[1] <= 0 or value[0] < 0
    ):
        raise AlexandriaError(f"the preflight record field {name} is not a [numerator, denominator] pair")
    return Fraction(value[0], value[1])


def sample_plan(record, window):
    """Rebuild one declared sample plan from the record's template and the window."""
    template = field(record, "sample_plans")
    entries = aave_v3.subject_entries(registry())
    plan = {
        "chain": template["chain"],
        "deployment": template["deployment"],
        "evidence_classes": list(window["classes"]),
        "finality": dict(template["finality"]),
        "format": template["format"],
        "interval": {"end": str(window["end"]), "start": str(window["start"])},
        "provider": {
            "class": record["transports"][window["transport"]]["class"],
            "page_limit": template["page_limit"],
            "timeout_seconds": template["timeout_seconds"],
        },
        "shard_width": window["shard_width"],
        "shards": plan_shards(window["start"], window["end"], window["shard_width"]),
        "subjects": list(entries),
        "venue": template["venue"],
    }
    for key in (SPLIT_FIELD, PARTS_FIELD):
        if key in window:
            plan[key] = window[key]
    return plan


def density_windows(record):
    """The primary's complete windows that carry a densest-span ladder, by start block."""
    windows = [
        window for window in field(record, "windows")
        if window["transport"] == "primary" and window["exit"] == 0 and "densest" in window
    ]
    if not windows:
        raise AlexandriaError("the preflight record has no complete primary window with a densest ladder")
    return sorted(windows, key=lambda window: (window["start"], window["end"]))


def rates(window):
    """One window's journal bytes, logs and traced transactions per block, as exact fractions."""
    blocks = window["end"] - window["start"] + 1
    counts = window["counts"]
    return {
        "log_bytes": Fraction(counts["logs"]["bytes"], blocks),
        "trace_bytes": Fraction(counts["traces"]["bytes"], blocks),
        "logs": Fraction(counts["logs"]["records"], blocks),
        "transactions": Fraction(counts["traces"]["transactions"], blocks),
    }


class Envelope:
    """An upper envelope of the sampled per-block rates across the interval.

    Between two sampled windows' centres a block takes the larger of the two
    windows' rates; before the first centre and after the last it takes the
    nearest window's. The integral over a block range is exact.
    """

    def __init__(self, windows, start, end):
        self.points = [
            (Fraction(window["start"] + window["end"], 2), rates(window)) for window in windows
        ]
        self.start, self.end = start, end

    def pieces(self):
        """(first block, last block, rates) pieces tiling [start, end]."""
        result = []
        first_centre, first_rates = self.points[0]
        if self.start < math.floor(first_centre):
            result.append((self.start, math.floor(first_centre) - 1, first_rates))
        for (left, left_rates), (right, right_rates) in zip(self.points, self.points[1:]):
            if math.floor(right) > math.floor(left):
                result.append((math.floor(left), math.floor(right) - 1, {
                    key: max(left_rates[key], right_rates[key]) for key in left_rates
                }))
        last_centre, last_rates = self.points[-1]
        result.append((math.floor(last_centre), self.end, last_rates))
        return result

    def total(self, key, low, high):
        """The envelope's integral of one rate over blocks low to high, rounded up."""
        amount = Fraction(0)
        for first, last, value in self.pieces():
            a, b = max(first, low), min(last, high)
            if a <= b:
                amount += value[key] * (b - a + 1)
        return math.ceil(amount)


def derive(record, interval=None):
    """Shard width, split, trace concurrency and segments, from the record alone.

    Refuses by name when the second transport did not answer the full subject
    filter: no plan over these subjects can then be reconciled, and the subject
    set is not the thing that changes.
    """
    interval = interval or ruled_interval()
    start, end = interval["start"], interval["end"]
    if field(record, "second_transport", "filter", "answered") is not True:
        raise AlexandriaError(
            "the second transport refused the "
            f"{field(record, "second_transport", 'filter', 'addresses')}-address filter, so no segment plan over "
            "the pinned subject set can be reconciled; the plan has to change and the subject "
            "set does not"
        )
    cap = field(record, "second_transport", "range_cap", "accepted_width")
    headroom = fraction(field(record, "derivation", "shard_headroom"), "derivation.shard_headroom")
    range_share = fraction(field(record, "derivation", "range_share"), "derivation.range_share")
    memory_share = fraction(field(record, "derivation", "memory_share"), "derivation.memory_share")
    log_nodes = fraction(field(record, "derivation", "log_nodes_per_log"), "derivation.log_nodes_per_log")
    journal_factor = {
        name: fraction(field(record, "derivation", "journal_bytes_per_result_byte", name),
                       f"derivation.journal_bytes_per_result_byte.{name}")
        for name in ("logs", "traces")
    }
    windows = density_windows(record)
    ladder = sorted({int(width) for window in windows for width in window["densest"]})

    def densest(width, key):
        return max(window["densest"][str(width)][key] for window in windows if str(width) in window["densest"])

    width = None
    for candidate in reversed(ladder):
        if candidate > min(cap, MAX_SHARD_WIDTH):
            continue
        logs = densest(candidate, "logs")
        if (
            logs <= headroom * LOCAL_LOG_ANSWER_LIMIT and logs <= MAX_PAGE_LIMIT
            and logs * log_nodes + RECORD_ENVELOPE_NODES <= headroom * MAX_RESPONSE_NODES
            and densest(candidate, "trace_nodes") + RECORD_ENVELOPE_NODES <= headroom * MAX_RESPONSE_NODES
        ):
            width = candidate
            break
    if width is None:
        raise AlexandriaError("no sampled shard width keeps the densest shard under its log and node limits")

    bytes_per_row = fraction(field(record, "memory", "attribution", "bytes_per_row"), "memory.attribution.bytes_per_row")
    nodes_per_row = fraction(field(record, "memory", "attribution", "nodes_per_row"), "memory.attribution.nodes_per_row")
    range_budget = range_share * MAX_RAW_COMPONENT_BYTES

    def range_estimate(blocks):
        """Planned bytes and nodes of one journal range of `blocks` at the densest sampled span."""
        span = min(value for value in ladder if value >= blocks)
        logs = densest(span, "logs")
        return {
            "logs": math.ceil(densest(span, "log_bytes") * journal_factor["logs"]),
            "traces": math.ceil(densest(span, "trace_bytes") * journal_factor["traces"]),
            "log-attributions": math.ceil(logs * bytes_per_row),
        }, math.ceil(logs * nodes_per_row)

    split = None
    for candidate in range(MAX_SHARDS, 0, -1):
        blocks = candidate * width
        if blocks > ladder[-1]:
            continue
        sizes, nodes = range_estimate(blocks)
        if all(size <= range_budget for size in sizes.values()) and nodes <= MAX_PART_NODES:
            split = candidate
            break
    if split is None:
        raise AlexandriaError("no shards_per_component keeps a journal range under the range budget")
    range_bytes, part_nodes = range_estimate(split * width)

    latency = field(record, "trace_latency", "by_concurrency")
    throughput = {
        int(level): fraction(field(record, "trace_latency", "by_concurrency", level, "transactions_per_second"),
                             f"trace_latency.by_concurrency.{level}.transactions_per_second")
        for level, value in latency.items()
    }
    if sorted(throughput) != [1, 4, 8]:
        raise AlexandriaError("the preflight record does not time trace concurrency 1, 4 and 8")
    concurrency = max(sorted(throughput), key=lambda level: (throughput[level], -level))

    ratio = fraction(field(record, "memory", "ratio"), "memory.ratio")
    host = field(record, "host", "physical_memory_bytes")
    bound = math.floor(memory_share * host / ratio)
    envelope = Envelope(windows, start, end)
    fixed = field(record, "derivation", "release_overhead", "fixed_bytes")
    per_shard = math.ceil(fraction(field(record, "derivation", "release_overhead", "bytes_per_shard"), "derivation.release_overhead.bytes_per_shard"))
    # The interval's shard grid at this width; each segment takes a contiguous
    # run of it, so every segment plan's own `plan_shards` gives the same cuts.
    grid = [
        {"start": low, "end": min(low + width - 1, end)} for low in range(start, end + 1, width)
    ]
    shard_limit = min(MAX_SHARDS, MAX_RANGES * split)

    def estimate(first, last):
        low, high = grid[first]["start"], grid[last]["end"]
        shards = last - first + 1
        ranges = math.ceil(shards / split)
        components = len(FIXED_COMPONENTS) + 1 + ranges * (len(EVIDENCE_CLASSES) + 1)
        logs = envelope.total("logs", low, high)
        release = (
            envelope.total("log_bytes", low, high) + envelope.total("trace_bytes", low, high)
            + math.ceil(logs * bytes_per_row) + fixed + shards * per_shard
        )
        return {
            "components": components, "logs": logs, "ranges": ranges,
            "release_bytes": release, "shards": shards,
            "transactions": envelope.total("transactions", low, high),
        }

    def fits(first, last, limit):
        value = estimate(first, last)
        return (
            value["shards"] <= shard_limit and value["release_bytes"] <= limit
            and value["components"] <= MAX_COMPONENTS
        )

    def greedy(limit):
        """The cuts that take as many shards as fit under `limit`, or None where one shard does not."""
        cuts, first = [], 0
        while first < len(grid):
            if not fits(first, first, limit):
                return None
            low, high = first, min(len(grid) - 1, first + shard_limit - 1)
            while low < high:
                middle = (low + high + 1) // 2
                if fits(first, middle, limit):
                    low = middle
                else:
                    high = middle - 1
            cuts.append((first, low))
            first = low + 1
        return cuts

    # The fewest segments the bound allows, then the smallest byte limit that
    # still gives that count, so the segments come out as even as the grid allows.
    fewest = greedy(bound)
    if fewest is None:
        raise AlexandriaError("one shard alone exceeds the segment bound")
    low, high = 1, bound
    while low < high:
        middle = (low + high) // 2
        cuts = greedy(middle)
        if cuts is not None and len(cuts) <= len(fewest):
            high = middle
        else:
            low = middle + 1
    boundaries = greedy(low)
    table = []
    for index, (a, b) in enumerate(boundaries):
        value = estimate(a, b)
        value.update({
            "index": index, "start": grid[a]["start"], "end": grid[b]["end"],
            "peak_memory_bytes": math.ceil(value["release_bytes"] * ratio),
            "range_bytes": dict(range_bytes),
            "part_nodes": part_nodes,
        })
        table.append(value)
    return {
        "shard_width": width,
        "shards_per_component": split,
        "trace_concurrency": concurrency,
        "segment_bound_bytes": bound,
        "densest_shard": {
            "logs": densest(width, "logs"),
            "log_nodes": math.ceil(densest(width, "logs") * log_nodes) + RECORD_ENVELOPE_NODES,
            "trace_nodes": densest(width, "trace_nodes") + RECORD_ENVELOPE_NODES,
        },
        "segments": table,
    }


def segment_plan(table_row, derivation):
    """The production plan one segment row declares."""
    interval = ruled_interval()
    entries = aave_v3.subject_entries(registry())
    return {
        "chain": aave_v3.CHAIN,
        "deployment": aave_v3.PRODUCTION_DEPLOYMENT,
        "evidence_classes": list(EVIDENCE_CLASSES),
        "finality": {
            "block_hash": interval["end_hash"], "block_number": str(interval["end"]),
            "policy": "finalized",
        },
        "format": "alexandria-interval-plan/v2",
        "interval": {"end": str(table_row["end"]), "start": str(table_row["start"])},
        "log_attribution_parts": PARTS_RULE,
        "provider": {
            "class": preflight()["transports"]["primary"]["class"],
            "page_limit": MAX_PAGE_LIMIT, "timeout_seconds": 3600,
        },
        "shard_width": derivation["shard_width"],
        "shards": plan_shards(table_row["start"], table_row["end"], derivation["shard_width"]),
        "shards_per_component": derivation["shards_per_component"],
        "subjects": list(entries),
        "venue": aave_v3.VENUE,
    }


def committed_plans():
    """Each committed segment plan's bytes and document, in table order."""
    result = []
    for row in segments()["segments"]:
        path = EXAMPLE / row["plan"]
        if not path.is_file():
            raise AssertionError(f"segment {row['index']} names plan {row['plan']}, which is missing")
        data = path.read_bytes()
        result.append((row, data, json.loads(data)))
    return result


class SegmentTableTests(unittest.TestCase):
    """The pinned table tiles the ruled interval with plans that validate."""

    def test_segments_tile_the_ruled_interval(self):
        interval = ruled_interval()
        table = segments()
        self.assertEqual(table["format"], SEGMENTS_FORMAT)
        self.assertEqual(table["interval"], {"end": interval["end"], "start": interval["start"]})
        rows = table["segments"]
        self.assertEqual([row["index"] for row in rows], list(range(len(rows))))
        self.assertEqual(rows[0]["start"], interval["start"])
        self.assertEqual(rows[-1]["end"], interval["end"])
        for previous, current in zip(rows, rows[1:]):
            self.assertEqual(current["start"], previous["end"] + 1, current["index"])
        for row, _data, plan in committed_plans():
            self.assertEqual(
                plan["interval"], {"end": str(row["end"]), "start": str(row["start"])}, row["index"],
            )
        self.assertEqual(
            sum(row["end"] - row["start"] + 1 for row in rows), interval["end"] - interval["start"] + 1,
        )

    def test_every_segment_plan_validates_and_is_pinned(self):
        interval = ruled_interval()
        entries = aave_v3.subject_entries(registry())
        plans = committed_plans()
        self.assertEqual(len(aave_v3.SEGMENT_PLAN_SHA256), len(plans))
        for (row, data, plan), pinned in zip(plans, aave_v3.SEGMENT_PLAN_SHA256, strict=True):
            with self.subTest(segment=row["index"]):
                validate_plan(plan)
                self.assertEqual(aave_v3.validate_plan_scope(plan, registry()), list(entries))
                self.assertEqual(len(plan["subjects"]), 356)
                self.assertEqual(plan["deployment"], aave_v3.PRODUCTION_DEPLOYMENT)
                self.assertEqual(plan["venue"], aave_v3.VENUE)
                self.assertEqual(plan["evidence_classes"], EVIDENCE_CLASSES)
                self.assertEqual(plan["finality"], {
                    "block_hash": interval["end_hash"], "block_number": "26022093",
                    "policy": "finalized",
                })
                self.assertEqual(plan[PARTS_FIELD], PARTS_RULE)
                self.assertEqual(plan[SPLIT_FIELD], segments()["derivation"]["shards_per_component"])
                self.assertEqual(data, canonical_bytes(plan))
                self.assertEqual(hashlib.sha256(data).hexdigest(), plan_digest(plan))
                self.assertEqual(row["plan_sha256"], pinned)
                self.assertEqual(plan_digest(plan), pinned)
                self.assertEqual(row["plan"], f"plans/segment-{row['index']}.json")

    def test_the_table_names_the_pinned_registry(self):
        # The table names the registry by path; its digest is written in the generator alone.
        self.assertEqual(EXAMPLE / segments()["registry"], REGISTRY)
        self.assertEqual(hashlib.sha256(REGISTRY.read_bytes()).hexdigest(), aave_v3.AAVE_V3_REGISTRY_SHA256)

    def test_an_unpinned_plan_under_the_production_name_refuses(self):
        _row, _data, plan = committed_plans()[0]
        edited = dict(plan, shards_per_component=plan["shards_per_component"] + 1)
        validate_plan(edited)
        with self.assertRaises(AlexandriaError) as caught:
            aave_v3.validate_plan_scope(edited, registry())
        self.assertEqual(
            str(caught.exception),
            f"the plan names the production deployment {aave_v3.PRODUCTION_DEPLOYMENT}, but its "
            f"SHA-256 {plan_digest(edited)} is not one of the {len(aave_v3.SEGMENT_PLAN_SHA256)} "
            "pinned segment plan digests in SEGMENT_PLAN_SHA256",
        )

    def test_the_collector_refuses_an_unpinned_production_plan_before_any_read(self):
        _row, _data, plan = committed_plans()[0]
        edited = dict(plan, shards_per_component=plan["shards_per_component"] + 1)
        with self.assertRaises(AlexandriaError) as caught:
            usdc_interval.opening_phase(edited, [], registry=registry())
        self.assertIn("is not one of the", str(caught.exception))
        self.assertIn(plan_digest(edited), str(caught.exception))

    def test_a_pinned_plan_under_another_name_is_not_refused_by_the_pin(self):
        _row, _data, plan = committed_plans()[0]
        renamed = dict(plan, deployment="aave-v3-ethereum-preflight")
        self.assertEqual(len(aave_v3.validate_plan_scope(renamed, registry())), 356)

    def test_the_pin_admits_nothing_as_preserved(self):
        self.assertNotIn(aave_v3.PRODUCTION_DEPLOYMENT, aave_v3.PRESERVED_DEPLOYMENTS)

    def test_the_ported_1888_limits_hold(self):
        """The #1888 port gives releases 16,384 components and plans a journal-range split."""
        from alexandria_lib import release

        self.assertEqual(release.MAX_COMPONENTS, 16_384)
        self.assertEqual(release.MAX_CAPTURES, 16_384)
        plans = committed_plans()
        self.assertTrue(plans)
        for row, _data, plan in plans:
            with self.subTest(segment=row["index"]):
                self.assertEqual(plan["log_attribution_parts"], "journal-ranges")
                validate_plan(plan)
        unsplit = dict(plans[0][2])
        del unsplit["log_attribution_parts"]
        validate_plan(unsplit)


class SegmentBudgetTests(unittest.TestCase):
    """Every segment's planned bytes, nodes and counts sit under their ceilings."""

    def setUp(self):
        self.table = segments()
        self.derivation = self.table["derivation"]

    def test_every_segment_estimate_fits_its_component_ceiling(self):
        budget = fraction(preflight()["derivation"]["range_share"], "range_share") * MAX_RAW_COMPONENT_BYTES
        self.assertEqual(budget, 48 * 1024 * 1024)
        for row, _data, plan in committed_plans():
            with self.subTest(segment=row["index"]):
                for name, size in row["range_bytes"].items():
                    self.assertLessEqual(size, budget, name)
                    self.assertLessEqual(size, MAX_JOURNAL_BYTES, name)
                self.assertEqual(sorted(row["range_bytes"]), ["log-attributions", "logs", "traces"])
                self.assertLessEqual(row["range_bytes"]["log-attributions"], MAX_PART_BYTES)
                components = journal_components(plan, plan["evidence_classes"])
                parts = attribution_parts(plan)
                self.assertEqual(len(parts), row["ranges"])
                self.assertEqual(len(FIXED_COMPONENTS) + len(components) + len(parts), row["components"])
                self.assertLessEqual(row["components"], MAX_COMPONENTS)
                self.assertLessEqual(row["ranges"], MAX_RANGES)

    def test_every_part_estimate_stays_under_the_part_node_limit(self):
        for row in self.table["segments"]:
            self.assertLessEqual(row["part_nodes"], MAX_PART_NODES, row["index"])
            self.assertLessEqual(row["range_bytes"]["log-attributions"], 48 * 1024 * 1024, row["index"])

    def test_every_segment_declares_the_journal_range_split(self):
        for row, _data, plan in committed_plans():
            self.assertEqual(plan[PARTS_FIELD], PARTS_RULE, row["index"])
            self.assertEqual(plan[SPLIT_FIELD], self.derivation["shards_per_component"], row["index"])

    def test_every_segment_fits_the_memory_bound(self):
        record = preflight()
        ratio = fraction(record["memory"]["ratio"], "memory.ratio")
        host = record["host"]["physical_memory_bytes"]
        for row in self.table["segments"]:
            with self.subTest(segment=row["index"]):
                self.assertLessEqual(row["release_bytes"] * ratio, Fraction(3, 4) * host)
                self.assertEqual(row["peak_memory_bytes"], math.ceil(row["release_bytes"] * ratio))

    def test_the_densest_shard_stays_under_the_local_log_limit_and_page_limit(self):
        densest = self.derivation["densest_shard"]
        self.assertLess(densest["logs"], LOCAL_LOG_ANSWER_LIMIT)
        self.assertLessEqual(densest["logs"], MAX_PAGE_LIMIT)
        self.assertEqual(densest["logs"], derive(preflight())["densest_shard"]["logs"])

    def test_the_densest_shard_records_stay_under_the_response_node_limit(self):
        densest = self.derivation["densest_shard"]
        self.assertLessEqual(densest["trace_nodes"], MAX_RESPONSE_NODES)
        self.assertLessEqual(densest["log_nodes"], MAX_RESPONSE_NODES)

    def test_the_record_says_why_no_release_byte_threshold_applies(self):
        reason = preflight()["derivation"]["release_byte_threshold"]
        self.assertIsNone(reason["bytes"])
        self.assertIn("8,589,934,592", reason["why"])
        self.assertIn("128", reason["why"])

    def test_shard_width_and_count_stay_under_the_interval_limits(self):
        cap = preflight()["second_transport"]["range_cap"]["accepted_width"]
        for row, _data, plan in committed_plans():
            with self.subTest(segment=row["index"]):
                self.assertLessEqual(plan["shard_width"], MAX_SHARD_WIDTH)
                self.assertLessEqual(plan["shard_width"], cap)
                self.assertLessEqual(len(plan["shards"]), MAX_SHARDS)
                self.assertEqual(len(plan["shards"]), row["shards"])
                for shard in plan["shards"]:
                    self.assertLessEqual(shard["end"] - shard["start"] + 1, cap)

    def test_every_fixture_component_and_journal_is_under_the_ceiling(self):
        from tests import test_aave_v3_collector as collector

        case = collector.AaveCase("run")
        case.setUp()
        try:
            staging = case.staged("ceiling")
            journals = sorted((staging / "journals").iterdir())
            self.assertTrue(journals)
            for path in journals:
                self.assertLessEqual(path.stat().st_size, MAX_JOURNAL_BYTES, path.name)
            output, _release_id = case.released("ceiling-release")
            manifest = json.loads((output / "manifest.json").read_bytes())
            self.assertTrue(manifest["components"])
            for component in manifest["components"]:
                self.assertLessEqual(component["bytes"], MAX_RAW_COMPONENT_BYTES, component["name"])
        finally:
            case.doCleanups()


class PreflightRecordTests(unittest.TestCase):
    """The record counts what it sampled, and the table derives from it."""

    def test_preflight_record_counts_every_sampled_window(self):
        record = preflight()
        self.assertEqual(record["format"], PREFLIGHT_FORMAT)
        windows = record["windows"]
        self.assertEqual(len({window["label"] for window in windows}), len(windows))
        totals = {}
        for window in windows:
            with self.subTest(window=window["label"]):
                plan = sample_plan(record, window)
                validate_plan(plan)
                self.assertEqual(plan_digest(plan), window["plan_sha256"])
                self.assertEqual(window["command"], (
                    f"{SCRIPT} collect --plan <sample-plan> --staging <scratch-staging> "
                    f"--registry plugins/alexandria/examples/aave-v3-interval-v0/registry.json "
                    f"--concurrency {window['concurrency']} "
                    f"--trace-concurrency {window['trace_concurrency']}"
                ))
                self.assertIsInstance(window["seconds"], (int, float))
                if window["exit"] != 0:
                    self.assertIsInstance(window["refusal"], str)
                    continue
                self.assertIsNone(window["refusal"])
                self.assertEqual(sorted(window["counts"]), sorted(window["classes"]))
                for name in window["classes"]:
                    counts = window["counts"][name]
                    for key in ("records", "bytes"):
                        self.assertIsInstance(counts[key], int, f"{name}.{key}")
                    if name in ("logs", "traces"):
                        self.assertIsInstance(counts["transactions"], int, name)
                shards = len(plan["shards"])
                self.assertEqual(window["counts"]["boundary-blocks"]["records"], shards)
                row = totals.setdefault(window["transport"], {"windows": 0, "blocks": 0, "logs": 0,
                                                              "traced_transactions": 0, "trace_frames": 0})
                row["windows"] += 1
                row["blocks"] += window["end"] - window["start"] + 1
                row["logs"] += window["counts"].get("logs", {}).get("records", 0)
                row["traced_transactions"] += window["counts"].get("traces", {}).get("transactions", 0)
                row["trace_frames"] += window["counts"].get("traces", {}).get("records", 0)
        self.assertEqual(record["totals"], totals)

    def test_shard_width_and_concurrency_derive_from_the_record(self):
        derived = derive(preflight())
        table = segments()
        self.assertEqual(table["derivation"], {key: value for key, value in derived.items() if key != "segments"})
        self.assertEqual(len(table["segments"]), len(derived["segments"]))
        for row, expected in zip(table["segments"], derived["segments"], strict=True):
            self.assertEqual({key: value for key, value in row.items() if key not in ("plan", "plan_sha256")}, expected)
        for row, data, plan in committed_plans():
            self.assertEqual(data, canonical_bytes(segment_plan(row, table["derivation"])), row["index"])

    def test_both_transports_read_the_ruled_boundary_hashes(self):
        interval = ruled_interval()
        boundaries = preflight()["boundaries"]
        self.assertEqual(sorted(boundaries), ["primary", "second"])
        for transport, value in boundaries.items():
            with self.subTest(transport=transport):
                self.assertEqual(value[str(interval["start"])], interval["start_hash"])
                self.assertEqual(value[str(interval["end"])], interval["end_hash"])
                self.assertEqual(value["finality"], "finalized")
                self.assertTrue(value["finalized_at_or_above_end"])

    def test_the_second_transport_answered_the_filter_and_its_range_cap_is_recorded(self):
        second = preflight()["second_transport"]
        self.assertEqual(second["filter"]["addresses"], 356)
        self.assertIs(second["filter"]["answered"], True)
        cap = second["range_cap"]
        self.assertEqual(cap["refused_width"], cap["accepted_width"] + 1)
        labels = {window["label"]: window for window in preflight()["windows"]}
        self.assertEqual(labels[cap["accepted_probe"]]["exit"], 0)
        self.assertEqual(labels[cap["accepted_probe"]]["shard_width"], cap["accepted_width"])
        self.assertNotEqual(labels[cap["refused_probe"]]["exit"], 0)
        self.assertEqual(labels[cap["refused_probe"]]["shard_width"], cap["refused_width"])

    def test_the_memory_ratio_names_its_host_and_commands(self):
        record = preflight()
        self.assertEqual(record["host"]["command"], "sysctl -n hw.memsize")
        memory = record["memory"]
        ratios = []
        for sample in memory["samples"]:
            for step in ("build", "check"):
                self.assertTrue(sample[step]["command"].startswith("/usr/bin/time -l " + SCRIPT + " " + step))
                ratios.append(Fraction(sample[step]["peak_rss_bytes"], sample["release_bytes"]))
        self.assertEqual(fraction(memory["ratio"], "memory.ratio"), max(ratios))

    def test_the_record_states_the_implied_totals(self):
        totals = segments()["implied"]
        rows = segments()["segments"]
        self.assertEqual(totals["release_bytes"], sum(row["release_bytes"] for row in rows))
        self.assertEqual(totals["shards"], sum(row["shards"] for row in rows))
        self.assertEqual(totals["traced_transactions"], sum(row["transactions"] for row in rows))
        self.assertEqual(totals["requests_per_transport"]["eth_getLogs"], totals["shards"])
        self.assertEqual(totals["requests_per_transport"]["eth_getBlockByNumber"], totals["shards"])
        self.assertEqual(totals["requests_per_transport"]["trace_transaction"], totals["traced_transactions"])

    def test_a_width_refusal_narrows_the_shard_and_keeps_the_subjects(self):
        record = preflight()
        narrow = json.loads(json.dumps(record))
        narrow["second_transport"]["range_cap"]["accepted_width"] = 50
        derived = derive(narrow)
        self.assertEqual(derived["shard_width"], 50)
        rows = derived["segments"]
        self.assertEqual(rows[0]["start"], ruled_interval()["start"])
        self.assertEqual(rows[-1]["end"], ruled_interval()["end"])
        plan = segment_plan(rows[0], derived)
        self.assertEqual(plan["subjects"], list(aave_v3.subject_entries(registry())))
        validate_plan(plan)

    def test_a_refused_filter_refuses_the_derivation_by_name(self):
        record = json.loads(json.dumps(preflight()))
        record["second_transport"]["filter"]["answered"] = False
        with self.assertRaises(AlexandriaError) as caught:
            derive(record)
        self.assertEqual(
            str(caught.exception),
            "the second transport refused the 356-address filter, so no segment plan over the "
            "pinned subject set can be reconciled; the plan has to change and the subject set "
            "does not",
        )

    def test_a_missing_record_field_refuses_by_name(self):
        record = json.loads(json.dumps(preflight()))
        del record["memory"]["ratio"]
        with self.assertRaises(AlexandriaError) as caught:
            derive(record)
        self.assertEqual(str(caught.exception), "the preflight record has no field memory.ratio")

    def test_a_malformed_ratio_refuses_by_name(self):
        record = json.loads(json.dumps(preflight()))
        record["derivation"]["range_share"] = [3, 0]
        with self.assertRaises(AlexandriaError) as caught:
            derive(record)
        self.assertEqual(
            str(caught.exception),
            "the preflight record field derivation.range_share is not a [numerator, denominator] pair",
        )

    def test_unavailable_windows_ran_inside_a_recorded_outage(self):
        """A window is labelled node-unavailable exactly when it started inside a recorded outage."""
        record = preflight()
        self.assertTrue("node_unavailable" in record, "the preflight record names no node_unavailable outage span")
        events = {event["at"] for event in field(record, "node_events")}
        spans = field(record, "node_unavailable")
        self.assertTrue(spans)
        for span in spans:
            self.assertLess(span["from"], span["until"])
            self.assertIn(span["until"], events)
        for window in field(record, "windows"):
            if window["transport"] != "primary":
                continue
            inside = any(span["from"] <= window["started_at"] < span["until"] for span in spans)
            with self.subTest(window=window["label"]):
                self.assertEqual(window["node_state"] == "unavailable", inside, window["node_state"])

    def test_the_record_names_the_frame_hash_left_on_the_default(self):
        """`trace_identity` hashes one frame under the canonical default, as the record says."""
        limits = field(preflight(), "primary_limits", "response_nodes_before_step_6")
        self.assertTrue("not_changed" in limits, "the preflight record does not name the frame hash left on the default")
        statement = limits["not_changed"]
        self.assertIn("trace_identity", statement)
        self.assertIn(f"{canonical.MAX_NODES:,}", statement)
        frame = {"transactionHash": "0x" + "11" * 32, "traceAddress": [], "type": "call"}
        self.assertTrue(usdc_interval.trace_identity(frame).startswith(frame["transactionHash"]))
        with self.assertRaises(AlexandriaError) as caught:
            usdc_interval.trace_identity(dict(frame, padding=[0] * canonical.MAX_NODES))
        self.assertEqual(str(caught.exception), f"JSON value exceeds the {canonical.MAX_NODES}-node limit")

    def test_no_url_host_header_or_bearer_in_the_record_or_any_plan(self):
        paths = [PREFLIGHT, SEGMENTS] + [EXAMPLE / row["plan"] for row in segments()["segments"]]
        host = re.compile(
            r"(?i)\b(?:localhost|\d{1,3}(?:\.\d{1,3}){3}|[a-z0-9-]+(?:\.[a-z0-9-]+)*\."
            r"(?:com|net|org|io|xyz|dev|cloud|app|network|tech|co|finance|pro))\b"
        )
        secret = os.environ.get(usdc_interval.BEARER_ENV)
        endpoint = os.environ.get(usdc_interval.ENDPOINT_ENV)
        for path in paths:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertNotIn("://", text)
                self.assertIsNone(host.search(text), host.search(text) and host.search(text).group(0))
                self.assertNotRegex(text, r"(?i)authorization|bearer\s+[a-z0-9]")
                self.assertNotIn(usdc_interval.ENDPOINT_ENV, text)
                self.assertNotIn(usdc_interval.BEARER_ENV, text)
                if secret:
                    self.assertNotIn(secret, text)
                if endpoint:
                    self.assertNotIn(endpoint, text)


def _nodes(value):
    """Count JSON values the way `canonical._check_tree` does."""
    count, stack = 0, [value]
    while stack:
        current = stack.pop()
        count += 1
        if isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, dict):
            stack.extend(current.values())
    return count


# Nodes added to one record: past the canonical default and well under
# `MAX_RESPONSE_NODES`; and, split across two transactions whose answers each
# stay under it, past `MAX_RESPONSE_NODES` once they are combined.
DENSE_PADDING = canonical.MAX_NODES + 10_000
OVER_PADDING = usdc_interval.MAX_RESPONSE_NODES // 2 + 10_000


def padded_transport(base, padding):
    """An Aave fixture transport whose answers carry `padding` extra nodes where named.

    `padding` maps ("traces", tx_hash) or ("logs", shard_index) to a node
    count. A trace answer gains that many nodes as copies of its first frame,
    each under its own `traceAddress` and under the plan's page limit in
    number; a log answer's first log gains a
    `padding` list of that many zeros. The answer is encoded under a node limit large enough to hold
    it, as a provider would send it.
    """

    class Padded(base):
        def trace_transaction(self, tx_hash):
            frames = super().trace_transaction(tx_hash)
            extra = padding.get(("traces", tx_hash))
            if extra and frames:
                # Many ordinary frames rather than one large one: a real dense
                # shard is dense by frame count, and each frame is hashed alone.
                # Half the plan's page limit in frames, each long enough in
                # `traceAddress` to carry its share of the extra nodes.
                copies = self.state["plan"]["provider"]["page_limit"] // 2
                depth = -(-extra // copies)
                frames = frames + [
                    dict(frames[0], traceAddress=[index] + [0] * depth) for index in range(copies)
                ]
            return frames

        def logs(self, shard):
            records = super().logs(shard)
            extra = padding.get(("logs", shard["index"]))
            if extra and records:
                records[0] = dict(records[0], padding=[0] * extra)
            return records

        def request(self, payload, label):
            envelope = json.loads(payload)
            if envelope["method"] == "trace_transaction":
                result = self.trace_transaction(envelope["params"][0])
            elif envelope["method"] == "eth_getLogs":
                result = self.logs(self._shard_for(int(envelope["params"][0]["toBlock"], 16)))
            else:
                return super().request(payload, label)
            self.calls.append((envelope["method"], label))
            return canonical_bytes(
                {"id": envelope["id"], "jsonrpc": "2.0", "result": result}, max_nodes=10 ** 8,
            )

    return Padded


class ResponseNodeLimitTests(unittest.TestCase):
    """Whole shard trace and log records are written and read under `MAX_RESPONSE_NODES` on every path.

    `trace_identity` still hashes each single trace frame under the canonical
    default when reconcile compares frames; the preflight record states that,
    and `test_the_record_names_the_frame_hash_left_on_the_default` holds it.

    Before Step 6, `Collector._targeted_traces`, `Reconciler._second_traces`,
    `staged_results`, `preserved_result`, `Reconciler._staged` and
    `_replay_release_opening` used the canonical default, `canonical.MAX_NODES`,
    so the dense case below refused at collect and each case here failed.
    """

    def setUp(self):
        from tests import test_aave_v3_collector as collector

        self.collector = collector
        self.case = collector.AaveCase("run")
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        state = self.case.state
        self.shard = next(int(index) for index, rows in sorted(state["logs"].items()) if rows)
        hashes = []
        for log in state["logs"][str(self.shard)]:
            if log["transactionHash"] not in hashes:
                hashes.append(log["transactionHash"])
        self.hashes = hashes

    def transport(self, padding):
        return padded_transport(self.collector.AaveTransport, padding)(self.case.state)

    def collect(self, name, padding):
        staging = self.case.scratch(name)
        usdc_interval.Collector(
            self.case.state["plan"], staging, self.transport(padding), registry=self.case.registry,
        ).collect()
        return staging

    def reconcile(self, staging, padding):
        return usdc_interval.Reconciler(
            self.case.state["plan"], staging, self.transport(padding),
            self.collector.SECOND_PROVIDER, registry=self.case.registry,
        ).reconcile()

    def build(self, staging, name):
        output = self.case.root / name
        usdc_interval.Builder(
            self.case.state["plan"], staging, self.case.registry,
            created_at=self.collector.CREATED_AT,
        ).build(output)
        return output

    def largest_record(self, staging, name):
        """The node count of the largest staged response of one class."""
        sizes = [
            _nodes(json.loads(json.loads(line)["response"]))
            for path in (staging / "journals").glob(f"{name}*.jsonl")
            for line in path.read_bytes().splitlines() if line
        ]
        return max(sizes)

    def dense(self):
        return {("traces", self.hashes[0]): DENSE_PADDING, ("logs", self.shard): DENSE_PADDING}

    def test_a_dense_trace_and_log_shard_collects_reconciles_builds_and_checks(self):
        staging = self.collect("dense", self.dense())
        for name in ("traces", "logs"):
            size = self.largest_record(staging, name)
            self.assertGreater(size, canonical.MAX_NODES, name)
            self.assertLess(size, usdc_interval.MAX_RESPONSE_NODES, name)
        document = self.reconcile(staging, self.dense())
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        output = self.build(staging, "dense-release")
        self.assertEqual(usdc_interval.check_interval(output)["reconciliation"], "agreed")

    def test_a_combined_trace_record_over_the_limit_refuses_at_collect(self):
        self.assertGreaterEqual(len(self.hashes), 2, "the fixture shard needs two transactions")
        padding = {("traces", tx): OVER_PADDING for tx in self.hashes[:2]}
        staging = self.case.scratch("over-collect")
        with self.assertRaises(AlexandriaError) as caught:
            usdc_interval.Collector(
                self.case.state["plan"], staging, self.transport(padding), registry=self.case.registry,
            ).collect()
        self.assertEqual(
            str(caught.exception),
            f"shard {self.shard} traces combined record cannot be written: JSON value exceeds "
            f"the {usdc_interval.MAX_RESPONSE_NODES}-node limit",
        )

    def test_a_second_provider_trace_record_over_the_limit_refuses_at_reconcile(self):
        self.assertGreaterEqual(len(self.hashes), 2, "the fixture shard needs two transactions")
        staging = self.collect("over-second", {})
        padding = {("traces", tx): OVER_PADDING for tx in self.hashes[:2]}
        document = self.reconcile(staging, padding)
        self.assertEqual(document["reconciliation"]["status"], "unreconciled")
        receipts = [
            json.loads(line) for line in
            (staging / "reconciliation" / "errors.jsonl").read_text().splitlines() if line
        ]
        self.assertEqual([receipt["message"] for receipt in receipts], [
            f"shard {self.shard} second-provider traces combined record cannot be compared: "
            f"JSON value exceeds the {usdc_interval.MAX_RESPONSE_NODES}-node limit",
        ])

    def test_a_staged_record_over_the_limit_refuses_at_reconcile_build_and_check(self):
        """Each reader refuses a record past the limit it reads under, by the record's name.

        The limit is lowered to the canonical default for these calls, so a
        record the dense case shows passing at `MAX_RESPONSE_NODES` stands
        over it; the refusal each reader gives is the one a record past the
        real limit gets.
        """
        staging = self.collect("over-staged", self.dense())
        self.reconcile(staging, self.dense())
        output = self.build(staging, "over-staged-release")
        lowered = canonical.MAX_NODES
        with mock.patch.object(usdc_interval, "MAX_RESPONSE_NODES", lowered):
            with self.assertRaises(AlexandriaError) as reconcile:
                self.reconcile(staging, self.dense())
            with self.assertRaises(AlexandriaError) as build:
                self.build(staging, "over-staged-rebuild")
            with self.assertRaises(AlexandriaError) as check:
                usdc_interval.check_interval(output)
        self.assertRegex(
            str(reconcile.exception), rf"^staged (logs|traces) response exceeds the {lowered}-node limit$",
        )
        self.assertEqual(str(build.exception), f"staged logs response exceeds the {lowered}-node limit")
        self.assertRegex(str(check.exception), rf"exceeds the {lowered}-node limit$")



class ExistingReleaseIdentityTests(unittest.TestCase):
    """The collector change leaves every pinned release identifier where it was."""

    IDENTIFIERS = (
        "tests.test_usdc_interval_live_demo.DemoReproducesReleaseIdTests"
        ".test_the_rebuild_reproduces_the_pinned_identifier",
        "tests.test_epoch_positions_demo.LiteralOwnershipTests"
        ".test_the_live_rebuild_has_its_own_recorded_identifier",
        "tests.test_wildcat_v1_interval_demo.PreservedArtefactsTests"
        ".test_verify_preserved_passes_against_the_committed_artefacts",
        "tests.test_wildcat_v2_interval_demo.PreservedArtefactsTests"
        ".test_verify_preserved_passes_against_the_committed_artefacts",
    )

    def test_the_compound_identifiers_and_both_wildcat_releases_are_unchanged(self):
        import io

        suite = unittest.TestLoader().loadTestsFromNames(self.IDENTIFIERS)
        stream = io.StringIO()
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
        self.assertEqual(result.testsRun, len(self.IDENTIFIERS), stream.getvalue())
        self.assertTrue(result.wasSuccessful(), stream.getvalue())
        self.assertEqual(result.skipped, [], stream.getvalue())

if __name__ == "__main__":
    unittest.main()
