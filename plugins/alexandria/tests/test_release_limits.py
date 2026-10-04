"""The release caps, the manifest limits and the checkpoint limit, at their values and one past.

The design record's `release-limits-hold-at-the-cap` cell loads the four tests
of `ReleaseCapTests`, `ManifestLimitTests` and `CheckpointLimitTests` by name,
with the re-derived `JournalSplitTests` refusal in `test_usdc_interval`. Its
`split-release-over-128-components` cell loads `SplitReleaseTests`. Every case
runs in process: none starts a child process, and none opens a socket.

A limit shared by every reader lives in `alexandria_lib.release` or
`alexandria_lib.interval`, and the readers look it up there when they run, so
a case may patch it down to one document's own size to show the reader admits
that document at the limit and refuses it one below.
"""

from contextlib import ExitStack
from copy import deepcopy
import json
from pathlib import Path
import re
import shutil
import socket
import statistics
import tempfile
import unittest
from unittest import mock

from tests.test_log_attribution_parts import nodes as count_nodes, repository_root
from tests.test_usdc_interval import component_document
from tests.test_wildcat_venue import CREATED_AT, WildcatCase
from alexandria_lib import (
    canonical,
    compound_phase0,
    derivation,
    index as index_module,
    interval,
    release as release_module,
    statement as statement_module,
)
from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.interval import PARTS_FIELD, PARTS_RULE, SPLIT_FIELD, Staging, plan_shards
import usdc_interval
from usdc_interval import (
    FIXED_COMPONENTS,
    Builder,
    attribution_parts,
    check_interval,
    journal_components,
)


REPO_ROOT = repository_root()
PLUGIN = REPO_ROOT / "plugins" / "alexandria"
FIXTURES = PLUGIN / "tests" / "fixtures"
SCHEMAS = PLUGIN / "schemas"
COMPOUND_RELEASE = PLUGIN / "examples" / "compound-v3-phase0-v0" / "release"
COMPOUND_RELEASE_ID = "sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab"
SYNTHETIC_AT = "2026-09-24T00:00:00Z"
V4_SEMANTICS = "v4-subject-positional-parts"
DECISION_DRAFT = (
    REPO_ROOT / "docs" / "decisions" / "drafts"
    / "split-interval-log-attributions-across-components.md"
)
PROOF = PLUGIN / "docs" / "epoch-table-split" / "proof.md"
STUDY = PLUGIN / "docs" / "epoch-table-split" / "study.md"


def schema(name):
    return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))


def synthetic_capture(index: int, component: str) -> dict:
    """One well-formed plan capture: full-dataset, partial on one declared gap."""
    return {
        "chain": "eip155:1",
        "component": component,
        "coverage": {
            "collections": [], "gaps": ["synthetic"], "record_count": 0,
            "status": "partial", "unsupported_collections": [],
        },
        "evidence_class": "archive-log",
        "id": f"x{index:05d}",
        "scope": {
            "deployment": "d", "finality": "unknown",
            "interval": {"kind": "snapshot", "observed_at": SYNTHETIC_AT},
            "kind": "full-dataset",
        },
        "source": {"kind": "local", "locator_class": "local-fixture", "reference": "synthetic"},
        "venue": "v",
    }


def synthetic_plan(components: int, captures: int) -> dict:
    names = [f"c{index:05d}" for index in range(components)]
    return {
        "captures": [synthetic_capture(index, names[index % components]) for index in range(captures)],
        "components": [
            {
                "access": "public", "media_type": "application/json", "name": name,
                "path": f"{name}.json", "redistribution": "permitted", "role": "raw",
            }
            for name in names
        ],
        "format": release_module.PLAN_FORMAT,
        "release": {"created_at": SYNTHETIC_AT, "name": "limits"},
    }


OBJECT = b"{}\n"
OBJECT_DIGEST = release_module.sha256(OBJECT)
OBJECT_PATH = f"objects/sha256/{OBJECT_DIGEST[7:9]}/{OBJECT_DIGEST[7:]}"


def synthetic_manifest(components: int, captures: int) -> dict:
    """A manifest of the given counts, every component naming one shared object."""
    names = [f"c{index:05d}" for index in range(components)]
    unsigned = {
        "captures": [
            dict(synthetic_capture(index, names[index % components]), component_sha256=OBJECT_DIGEST)
            for index in range(captures)
        ],
        "components": [
            {
                "access": "public", "bytes": len(OBJECT), "media_type": "application/json",
                "name": name, "object_path": OBJECT_PATH, "redistribution": "permitted",
                "role": "raw", "sha256": OBJECT_DIGEST,
            }
            for name in names
        ],
        "format": release_module.MANIFEST_FORMAT,
        "release": {"created_at": SYNTHETIC_AT, "name": "limits"},
    }
    identity = release_module.sha256(
        canonical_bytes(unsigned, max_nodes=release_module.MAX_MANIFEST_NODES)
    )
    return dict(unsigned, release_id=identity)


def write_synthetic_release(root: Path, components: int, captures: int) -> str:
    """A verifiable release of the given counts, created in a directory that must not exist."""
    manifest = synthetic_manifest(components, captures)
    root.mkdir()
    (root / OBJECT_PATH).parent.mkdir(parents=True)
    with open(root / OBJECT_PATH, "xb") as handle:
        handle.write(OBJECT)
    with open(root / "manifest.json", "xb") as handle:
        handle.write(canonical_bytes(manifest, max_nodes=release_module.MAX_MANIFEST_NODES))
    return manifest["release_id"]


def measure(path: Path):
    """A manifest-like file's bytes and its node count as the canonical reader counts them."""
    data = Path(path).read_bytes()
    return len(data), count_nodes(json.loads(data))


def one_block_state(state):
    """The fixture state re-planned with one-block shards, each log and trace filed under its block's shard."""
    state = deepcopy(state)
    plan = state["plan"]
    start, end = int(plan["interval"]["start"]), int(plan["interval"]["end"])
    plan["shard_width"] = 1
    plan["shards"] = plan_shards(start, end, 1)
    logs = {str(shard["index"]): [] for shard in plan["shards"]}
    for records in state["logs"].values():
        for record in records:
            logs[str(int(record["blockNumber"], 16) - start)].append(record)
    traces = {str(shard["index"]): [] for shard in plan["shards"]}
    for frames in state["traces"].values():
        for frame in frames:
            traces[str(int(frame["blockNumber"]) - start)].append(frame)
    state["logs"], state["traces"] = logs, traces
    return state


def no_socket():
    """Deny Python socket construction, so any network use fails the case."""
    return mock.patch.object(socket, "socket", side_effect=AssertionError("a socket was constructed"))


def manifest_limits(*, size=None, nodes=None):
    """Patch the shared manifest limits, which every reader and writer looks up in `release`."""
    stack = ExitStack()
    if size is not None:
        stack.enter_context(mock.patch.object(release_module, "MAX_MANIFEST_BYTES", size))
    if nodes is not None:
        stack.enter_context(mock.patch.object(release_module, "MAX_MANIFEST_NODES", nodes))
    return stack


def checkpoint_limits(*, size=None, nodes=None):
    """Patch the checkpoint limits `Staging` looks up in `interval`."""
    stack = ExitStack()
    if size is not None:
        stack.enter_context(mock.patch.object(interval, "MAX_CHECKPOINT_BYTES", size))
    if nodes is not None:
        stack.enter_context(mock.patch.object(interval, "MAX_CHECKPOINT_NODES", nodes))
    return stack


def refusal(text: str) -> str:
    """A pattern matching exactly one refusal message."""
    return "^" + re.escape(text) + "$"


class ReleaseCapTests(unittest.TestCase):
    """`validate_plan` and `validate_manifest` admit each cap and refuse one entry more, by name."""

    def test_the_component_cap_admits_its_value_and_refuses_one_more(self):
        cap = release_module.MAX_COMPONENTS
        self.assertEqual(cap, 16_384)
        release_module.validate_plan(synthetic_plan(cap, 1))
        release_module.validate_manifest(synthetic_manifest(cap, 1))
        above = cap + 1
        with self.assertRaisesRegex(
            AlexandriaError, refusal(f"capture plan lists {above} components, above the {cap}-component limit"),
        ):
            release_module.validate_plan(synthetic_plan(above, 1))
        with self.assertRaisesRegex(
            AlexandriaError, refusal(f"manifest lists {above} components, above the {cap}-component limit"),
        ):
            release_module.validate_manifest(synthetic_manifest(above, 1))
        # Each schema that lists components carries the same cap. A statement has
        # one subject per component and one for the release.
        self.assertEqual(schema("capture-plan-v1")["properties"]["components"]["maxItems"], cap)
        self.assertEqual(schema("archive-manifest-v1")["properties"]["components"]["maxItems"], cap)
        statement = schema("release-statement-v1")
        self.assertEqual(statement["$defs"]["predicate"]["properties"]["components"]["maxItems"], cap)
        self.assertEqual(statement["properties"]["subject"]["maxItems"], cap + 1)

    def test_the_capture_cap_admits_its_value_and_refuses_one_more(self):
        cap = release_module.MAX_CAPTURES
        self.assertEqual(cap, 16_384)
        release_module.validate_plan(synthetic_plan(1, cap))
        release_module.validate_manifest(synthetic_manifest(1, cap))
        above = cap + 1
        with self.assertRaisesRegex(
            AlexandriaError, refusal(f"capture plan lists {above} captures, above the {cap}-capture limit"),
        ):
            release_module.validate_plan(synthetic_plan(1, above))
        with self.assertRaisesRegex(
            AlexandriaError, refusal(f"manifest lists {above} captures, above the {cap}-capture limit"),
        ):
            release_module.validate_manifest(synthetic_manifest(1, above))
        self.assertEqual(schema("capture-plan-v1")["properties"]["captures"]["maxItems"], cap)
        self.assertEqual(schema("archive-manifest-v1")["properties"]["captures"]["maxItems"], cap)
        self.assertEqual(
            schema("address-query-v1")["$defs"]["coverage"]["properties"]["captures"]["maxItems"], cap,
        )
        self.assertEqual(
            schema("release-statement-v1")["$defs"]["predicate"]["properties"]["captures"]["maxItems"],
            cap,
        )


class ManifestLimitTests(WildcatCase):
    """Every manifest and capture-plan reader and writer holds the published limits, refusing by name."""

    PUBLISHED = (
        (release_module, "MAX_COMPONENTS", 16_384),
        (release_module, "MAX_CAPTURES", 16_384),
        (release_module, "MAX_MANIFEST_BYTES", 134_217_728),
        (release_module, "MAX_MANIFEST_NODES", 2_000_000),
        (interval, "MAX_CHECKPOINT_NODES", 2_000_000),
        (interval, "MAX_CHECKPOINT_BYTES", 8_388_608),
        # The limits this change leaves as they were.
        (release_module, "MAX_RAW_COMPONENT_BYTES", 67_108_864),
        (interval, "MAX_JOURNAL_BYTES", 67_108_864),
        (interval, "MAX_SHARDS", 4_096),
        (statement_module, "MAX_STATEMENT_BYTES", 8_388_608),
        (canonical, "MAX_CONTROL_BYTES", 8_388_608),
        (canonical, "MAX_NODES", 200_000),
    )

    def refuses(self, pattern, call, *args):
        with self.assertRaises(AlexandriaError) as caught:
            call(*args)
        self.assertRegex(str(caught.exception), pattern)

    def read_refusals(self, label, size, nodes, call, *args):
        """`call` refuses the document one byte and one node below its own size, naming both."""
        with manifest_limits(size=size - 1):
            self.refuses(refusal(f"{label} of {size} bytes exceeds the {size - 1}-byte limit"), call, *args)
        with manifest_limits(nodes=nodes - 1):
            self.refuses(refusal(f"{label} of {size} bytes exceeds the {nodes - 1}-node limit"), call, *args)

    def write_refusals(self, label, size, nodes, call, *args):
        """`call` refuses to write the document one byte and one node below its own size."""
        with manifest_limits(size=size - 1):
            self.refuses(refusal(f"{label} encodes to {size} bytes, above the {size - 1}-byte limit"), call, *args)
        with manifest_limits(nodes=nodes - 1):
            self.refuses(refusal(f"{label} holds {nodes} nodes, above the {nodes - 1}-node limit"), call, *args)

    def credit_releases(self):
        """The raw and derived releases the credit-view sources build."""
        declaration = json.loads((FIXTURES / "credit-view-sources.json").read_text(encoding="utf-8"))
        inputs = self.scratch("credit-inputs")
        plan = {
            "captures": declaration["captures"], "components": [],
            "format": release_module.PLAN_FORMAT, "release": declaration["release"],
        }
        for component in declaration["components"]:
            component = deepcopy(component)
            shutil.copy2(REPO_ROOT / component.pop("repository_path"), inputs / component["path"])
            plan["components"].append(component)
        with open(inputs / "capture-plan.json", "xb") as handle:
            handle.write(canonical_bytes(plan))
        raw, derived = self.root / "credit-raw", self.root / "credit-derived"
        return (
            raw, release_module.ingest(inputs / "capture-plan.json", raw),
            derived, derivation.derive(raw, derived),
        )

    def check_ingest(self):
        inputs = self.scratch("ingest-inputs")
        for name in ("full-dataset.json", "subject-scoped.json"):
            shutil.copy2(FIXTURES / name, inputs / name)
        plan = inputs / "capture-plan.json"
        with open(plan, "xb") as handle:
            handle.write(canonical_bytes(json.loads((FIXTURES / "capture-plan.json").read_bytes())))
        release_id = release_module.ingest(plan, self.root / "ingest-first")
        plan_size, plan_nodes = measure(plan)
        size, nodes = measure(self.root / "ingest-first" / "manifest.json")
        # The manifest `ingest` writes is the larger document, so it sets the
        # limits the whole path is admitted at.
        self.assertGreater(size, plan_size)
        self.assertGreater(nodes, plan_nodes)
        with manifest_limits(size=size, nodes=nodes):
            self.assertEqual(release_module.ingest(plan, self.root / "ingest-at"), release_id)
        refused = self.root / "ingest-refused"
        self.read_refusals("capture plan", plan_size, plan_nodes, release_module.ingest, plan, refused)
        self.write_refusals("manifest", size, nodes, release_module.ingest, plan, refused)
        self.assertFalse(refused.exists())

    def check_verify(self, release, release_id):
        size, nodes = measure(release / "manifest.json")
        with manifest_limits(size=size, nodes=nodes):
            self.assertEqual(release_module.verify(release), release_id)
        self.read_refusals("manifest", size, nodes, release_module.verify, release)

    def check_derive(self, raw, derived, derived_id):
        raw_size, raw_nodes = measure(raw / "manifest.json")
        size, nodes = measure(derived / "manifest.json")
        self.assertGreater(size, raw_size)
        self.assertGreater(nodes, raw_nodes)
        with manifest_limits(size=size, nodes=nodes):
            self.assertEqual(derivation.derive(raw, self.root / "derive-at"), derived_id)
        refused = self.root / "derive-refused"
        self.read_refusals("manifest", raw_size, raw_nodes, derivation.derive, raw, refused)
        self.write_refusals("manifest", size, nodes, derivation.derive, raw, refused)
        self.assertFalse(refused.exists())

    def check_index(self, derived, derived_id):
        size, nodes = measure(derived / "manifest.json")
        database = self.root / "index-at.sqlite"
        with manifest_limits(size=size, nodes=nodes):
            digest = index_module.rebuild([derived], database)
            checked = index_module.inspect_index(database)
            try:
                self.assertEqual(checked["logical_digest"], digest)
            finally:
                index_module.close_index(checked)
        refused = self.root / "index-refused.sqlite"
        self.read_refusals("manifest", size, nodes, index_module.rebuild, [derived], refused)
        self.assertFalse(refused.exists())
        # Opening an index re-reads every release it names under the same limits.
        with manifest_limits(size=size - 1):
            self.refuses(
                refusal(
                    f"index has a stale release reference for {derived_id}: manifest of {size} "
                    f"bytes exceeds the {size - 1}-byte limit"
                ),
                index_module.inspect_index, database,
            )
        # The rows are indexed from files held to the manifest verification read:
        # a JSONL file changed once verification has passed refuses by name.
        changed = self.root / "index-changed"
        shutil.copytree(derived, changed)
        events = changed / derivation.EVENTS_PATH
        verified = index_module.verify_release

        def verified_then_changed(path):
            result = verified(path)
            with open(events, "ab") as handle:
                handle.write(b"\n")
            return result

        with mock.patch.object(index_module, "verify_release", side_effect=verified_then_changed):
            self.refuses(
                refusal(
                    f"derived output {derivation.EVENTS_PATH} does not carry the size and SHA-256 "
                    "its verified manifest records, so it changed after the release was verified"
                ),
                index_module.rebuild, [changed], self.root / "index-changed.sqlite",
            )
        self.assertFalse((self.root / "index-changed.sqlite").exists())

    def check_compound(self):
        size, nodes = measure(COMPOUND_RELEASE / "manifest.json")
        with manifest_limits(size=size, nodes=nodes):
            self.assertEqual(compound_phase0.load_phase0(COMPOUND_RELEASE)[0], COMPOUND_RELEASE_ID)
        self.read_refusals("manifest", size, nodes, compound_phase0.load_phase0, COMPOUND_RELEASE)

    def check_statement(self, raw, raw_id):
        size, nodes = measure(raw / "manifest.json")
        # The statement writer refuses an output path through a symlink, and a
        # temporary directory can sit behind one.
        output = self.root.resolve() / "statement.json"
        with manifest_limits(size=size, nodes=nodes):
            self.assertEqual(statement_module.emit_statement(raw, output)["release_id"], raw_id)
        kept = output.read_bytes()
        self.read_refusals("manifest", size, nodes, statement_module.emit_statement, raw, output)
        # The statement's own second read of the manifest, reached with the
        # first verification patched out.
        with mock.patch.object(statement_module, "verify", return_value=raw_id):
            self.read_refusals("manifest", size, nodes, statement_module.emit_statement, raw, output)
        self.assertEqual(output.read_bytes(), kept)

    def check_statement_beyond_the_old_limits(self):
        # Both releases pass the default 200,000 nodes, so only the raised
        # manifest limits admit them. The smaller statement also passes that
        # node count and still emits; the larger is refused by Ariadne's byte
        # limit, by name, not by the encoder's node default.
        fits = self.root / "statement-fits"
        fits_id = write_synthetic_release(fits, 6_500, 6_500)
        self.assertGreater(measure(fits / "manifest.json")[1], canonical.MAX_NODES)
        output = self.root.resolve() / "statement-fits.json"
        self.assertEqual(statement_module.emit_statement(fits, output)["release_id"], fits_id)
        emitted = output.read_bytes()
        self.assertGreater(count_nodes(json.loads(emitted)), canonical.MAX_NODES)
        self.assertLessEqual(len(emitted), statement_module.MAX_STATEMENT_BYTES)
        large = self.root / "statement-large"
        write_synthetic_release(large, release_module.MAX_COMPONENTS, release_module.MAX_CAPTURES)
        refused = self.root.resolve() / "statement-large.json"
        with self.assertRaises(AlexandriaError) as caught:
            statement_module.emit_statement(large, refused)
        found = re.fullmatch(
            r"release statement encodes to (\d+) bytes, above Ariadne's 8388608-byte input limit",
            str(caught.exception),
        )
        self.assertIsNotNone(found, str(caught.exception))
        self.assertGreater(int(found.group(1)), statement_module.MAX_STATEMENT_BYTES)
        self.assertFalse(refused.exists())

    def check_interval_release(self):
        output, release_id = self.released("interval")
        size, nodes = measure(output / "manifest.json")
        with manifest_limits(size=size, nodes=nodes):
            self.assertEqual(check_interval(output)["release_id"], release_id)
        self.read_refusals("manifest", size, nodes, check_interval, output)
        # `check`'s own second read of the manifest, reached with verification
        # patched out.
        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
            self.read_refusals("manifest", size, nodes, check_interval, output)

    def check_builder(self):
        staging = self.staged("builder")

        def builder():
            return Builder(self.plan, staging, self.registry, created_at=CREATED_AT)

        written = []

        def recording(plan, output):
            # The capture plan the build wrote, read before `ingest` consumes it.
            written.append(Path(plan).read_bytes())
            return release_module.ingest(plan, output)

        first = self.root / "builder-first"
        with mock.patch.object(usdc_interval, "ingest", side_effect=recording):
            release_id = builder().build(first)
        (plan_bytes,) = written
        plan_size, plan_nodes = len(plan_bytes), count_nodes(json.loads(plan_bytes))
        size, nodes = measure(first / "manifest.json")
        self.assertGreater(size, plan_size)
        self.assertGreater(nodes, plan_nodes)
        with manifest_limits(size=size, nodes=nodes):
            self.assertEqual(builder().build(self.root / "builder-at"), release_id)
        refused = self.root / "builder-refused"
        self.write_refusals("capture plan", plan_size, plan_nodes, builder().build, refused)
        self.assertFalse(refused.exists())

    def test_every_manifest_reader_admits_the_limits_and_refuses_above(self):
        for module, name, value in self.PUBLISHED:
            with self.subTest(limit=name):
                self.assertEqual(getattr(module, name), value)
        raw, raw_id, derived, derived_id = self.credit_releases()
        with self.subTest(reader="ingest"):
            self.check_ingest()
        with self.subTest(reader="verify"):
            self.check_verify(raw, raw_id)
            self.check_verify(derived, derived_id)
        with self.subTest(reader="derive, _read_manifest and verify_derivation"):
            self.check_derive(raw, derived, derived_id)
        with self.subTest(reader="index"):
            self.check_index(derived, derived_id)
        with self.subTest(reader="load_phase0"):
            self.check_compound()
        with self.subTest(reader="statement"):
            self.check_statement(raw, raw_id)
            self.check_statement_beyond_the_old_limits()
        with self.subTest(reader="check_interval"):
            self.check_interval_release()
        with self.subTest(reader="Builder.build"):
            self.check_builder()


class CheckpointLimitTests(WildcatCase):
    """`Staging` writes and reads its checkpoint under 2,000,000 nodes and the unchanged 8,388,608 bytes."""

    def planned(self, ranges, *, parts=True):
        """The fixture plan over `ranges` one-block shards, one journal range each."""
        plan = deepcopy(self.plan)
        start = int(plan["interval"]["start"])
        end = start + ranges - 1
        plan["interval"]["end"] = str(end)
        plan["finality"]["block_number"] = str(end)
        plan["shard_width"] = 1
        plan["shards"] = plan_shards(start, end, 1)
        plan[SPLIT_FIELD] = 1
        if parts:
            plan[PARTS_FIELD] = PARTS_RULE
        return plan

    def worst_case_round_trip(self, name, plan, checkpoint):
        """A full history with every offset at the journal ceiling reads back through `Staging`."""
        worst = deepcopy(checkpoint)
        start = int(plan["interval"]["start"])
        entry = worst["history"][-1]
        worst["history"] = [
            dict(entry, shard=shard, block_number=str(start + shard)) for shard in range(interval.MAX_HISTORY)
        ]
        worst["next_shard"] = interval.MAX_HISTORY
        worst["last_accepted"] = {"block_hash": entry["block_hash"], "block_number": str(start + 15)}
        for offsets in [worst["offsets"], *(item["offsets"] for item in worst["history"])]:
            for journal in offsets:
                offsets[journal] = 0 if journal == interval.OPENING_CLASS else interval.MAX_JOURNAL_BYTES
        # dict(entry, ...) shares one offsets object; give each entry its own.
        worst["history"] = [dict(item, offsets=dict(item["offsets"])) for item in worst["history"]]
        data = canonical_bytes(worst, max_nodes=interval.MAX_CHECKPOINT_NODES)
        self.assertGreater(count_nodes(worst), canonical.MAX_NODES)
        self.assertLessEqual(len(data), interval.MAX_CHECKPOINT_BYTES)
        root = self.scratch(name)
        Staging(root, plan)
        with open(root / "checkpoint.json", "xb") as handle:
            handle.write(data)
        self.assertEqual(Staging(root, plan).committed()["offsets"], worst["offsets"])
        return data

    def test_a_checkpoint_for_the_largest_admitted_plan_round_trips(self):
        self.assertEqual(interval.MAX_CHECKPOINT_NODES, 2_000_000)
        self.assertEqual(interval.MAX_CHECKPOINT_BYTES, 8_388_608)
        plan = self.planned(4_094)
        classes = tuple(plan["evidence_classes"])
        # 4,094 ranges is the largest split plan with parts the component cap
        # admits: 6 fixed, the opening journal, 3 x 4,094 journals and 4,094 parts.
        self.assertEqual(
            len(FIXED_COMPONENTS) + len(journal_components(plan, classes)) + len(attribution_parts(plan)),
            16_383,
        )
        with self.assertRaisesRegex(AlexandriaError, "would carry 16387 components, above the 16384-component limit$"):
            journal_components(self.planned(4_095), classes)
        root = self.scratch("largest")
        start = int(plan["interval"]["start"])
        with Staging(root, plan) as staging:
            self.assertEqual(len(staging.journal_names), 12_283)
            staging.resume()
            for shard in range(interval.MAX_HISTORY):
                staging.record(shard, "boundary-blocks", b'{"id":1}', b'{"result":null}')
                checkpoint = staging.commit(shard, start + shard, "0x" + f"{shard + 1:064x}")
        self.assertEqual(len(checkpoint["history"]), interval.MAX_HISTORY)
        data = (root / "checkpoint.json").read_bytes()
        nodes = count_nodes(checkpoint)
        # More nodes than the default the checkpoint was read under before this
        # change, inside its own node limit, under the unchanged byte limit.
        self.assertGreater(nodes, canonical.MAX_NODES)
        self.assertLessEqual(nodes, interval.MAX_CHECKPOINT_NODES)
        self.assertLessEqual(len(data), interval.MAX_CHECKPOINT_BYTES)
        self.assertEqual(data, canonical_bytes(checkpoint, max_nodes=interval.MAX_CHECKPOINT_NODES))
        committed = Staging(root, plan).committed()
        self.assertEqual(committed, {key: checkpoint[key] for key in committed})
        self.assertEqual(Staging(root, plan).resume()["history"], checkpoint["history"])
        self.worst_case_round_trip("largest-worst", plan, checkpoint)
        # Held at this checkpoint's own size a reader admits it; one below, it refuses by name.
        with checkpoint_limits(size=len(data), nodes=nodes):
            self.assertEqual(Staging(root, plan).committed()["history"], checkpoint["history"])
        with checkpoint_limits(size=len(data) - 1), self.assertRaisesRegex(
            AlexandriaError,
            refusal(f"interval checkpoint of {len(data)} bytes exceeds the {len(data) - 1}-byte limit"),
        ):
            Staging(root, plan).committed()
        with checkpoint_limits(nodes=nodes - 1), self.assertRaisesRegex(
            AlexandriaError,
            refusal(f"interval checkpoint of {len(data)} bytes exceeds the {nodes - 1}-node limit"),
        ):
            Staging(root, plan).committed()
        # A write past either limit refuses before the checkpoint on disk changes.
        following = interval.MAX_HISTORY
        with Staging(root, plan) as writer:
            writer.resume()
            with checkpoint_limits(nodes=nodes - 1), self.assertRaisesRegex(
                AlexandriaError,
                refusal(f"the interval checkpoint holds {nodes} nodes, above the {nodes - 1}-node limit"),
            ):
                writer.commit(following, start + following, "0x" + f"{following + 1:064x}")
        limit = len(data) // 2
        with Staging(root, plan) as writer:
            writer.resume()
            with checkpoint_limits(size=limit), self.assertRaises(AlexandriaError) as caught:
                writer.commit(following, start + following, "0x" + f"{following + 1:064x}")
        found = re.fullmatch(
            rf"the interval checkpoint encodes to (\d+) bytes, above the {limit}-byte limit",
            str(caught.exception),
        )
        self.assertIsNotNone(found, str(caught.exception))
        self.assertGreater(int(found.group(1)), limit)
        self.assertEqual((root / "checkpoint.json").read_bytes(), data)
        with self.subTest(plan="4,096 ranges without parts, the schema's offset bound"):
            widest = self.planned(interval.MAX_SHARDS, parts=False)
            self.assertLessEqual(
                len(FIXED_COMPONENTS) + len(journal_components(widest, classes)),
                release_module.MAX_COMPONENTS,
            )
            with Staging(self.scratch("widest"), widest) as staging:
                staging.resume()
                first = staging.commit(0, start, "0x" + f"{1:064x}")
            self.assertEqual(len(first["offsets"]), 3 * interval.MAX_SHARDS + 1)
            offsets = schema("interval-checkpoint-v2")["properties"]["offsets"]
            history = schema("interval-checkpoint-v2")["properties"]["history"]["items"]
            self.assertEqual(offsets["maxProperties"], len(first["offsets"]))
            self.assertEqual(history["properties"]["offsets"]["maxProperties"], len(first["offsets"]))
            self.worst_case_round_trip("widest-worst", widest, first)


class SplitReleaseTests(WildcatCase):
    """A split release of more than 128 components builds, checks and verifies offline."""

    def test_a_release_over_128_components_builds_checks_and_verifies_offline(self):
        state = one_block_state(self.state)
        plan = state["plan"]
        plan[SPLIT_FIELD] = 1
        plan[PARTS_FIELD] = PARTS_RULE
        parts = attribution_parts(plan)
        derived = (
            len(FIXED_COMPONENTS) + len(journal_components(plan, tuple(plan["evidence_classes"])))
            + len(parts)
        )
        self.assertEqual((len(plan["shards"]), len(parts), derived), (80, 80, 327))
        output = self.root / "over-128"
        with no_socket():
            staging = self.staged("over-128", state)
            release_id = Builder(plan, staging, self.registry, created_at=CREATED_AT).build(output)
            report = check_interval(output)
            verified = release_module.verify(output)
        manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(manifest["components"]), 327)
        self.assertGreater(len(manifest["components"]), 128)
        self.assertEqual(len(manifest["captures"]), 327)
        self.assertEqual(report["release_id"], release_id)
        self.assertEqual(verified, release_id)
        self.assertEqual(report["receipt_semantics"], V4_SEMANTICS)
        # The parts hold, in order, exactly the rows the unsplit build writes.
        whole, _whole_id = self.released("whole")
        rows = component_document(whole, "epoch-table")["log_attributions"]
        joined = [row for name in parts for row in component_document(output, name)["rows"]]
        self.assertEqual(joined, rows)
        self.assertTrue(rows)


def empty_clearpool_plan(inputs: Path, captures: int) -> Path:
    """A capture plan of `captures` complete, zero-record Clearpool captures, one component each."""
    declaration = json.loads((FIXTURES / "credit-view-sources.json").read_text(encoding="utf-8"))
    template = next(item for item in declaration["captures"] if item["venue"] == "clearpool")
    kind = next(item for item in declaration["components"] if item["name"] == template["component"])
    source = canonical_bytes({"block_times": {}, "currencies": {}, "factory_pools": [], "pool_logs": {}})
    plan = {
        "captures": [], "components": [],
        "format": release_module.PLAN_FORMAT, "release": declaration["release"],
    }
    for index in range(captures):
        component = {key: value for key, value in kind.items() if key != "repository_path"}
        component["name"] = f"clearpool-empty-{index:05d}"
        component["path"] = f"clearpool-empty-{index:05d}.json"
        with open(inputs / component["path"], "xb") as handle:
            handle.write(source)
        capture = deepcopy(template)
        capture["id"] = f"clearpool-empty-{index:05d}"
        capture["component"] = component["name"]
        capture["coverage"] = {
            "collections": [{"name": "factory-pools", "record_count": 0, "selector": "/factory_pools"}],
            "gaps": [], "record_count": 0, "status": "complete", "unsupported_collections": [],
        }
        plan["components"].append(component)
        plan["captures"].append(capture)
    path = inputs / "capture-plan.json"
    with open(path, "xb") as handle:
        handle.write(canonical_bytes(plan, max_nodes=release_module.MAX_MANIFEST_NODES))
    return path


class DerivationMappingLimitTests(unittest.TestCase):
    """`derive` keeps the derived view's 1,024-mapping limit under the raised capture cap."""

    def test_derive_refuses_a_release_past_the_mapping_limit_before_mapping_a_capture(self):
        limit = 1024
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "fits").mkdir()
            (root / "above").mkdir()
            release_module.ingest(empty_clearpool_plan(root / "fits", limit), root / "fits-raw")
            derived_id = derivation.derive(root / "fits-raw", root / "fits-derived")
            self.assertEqual(release_module.verify(root / "fits-derived"), derived_id)
            # The raised capture cap admits one capture more, so ingest builds it.
            release_module.ingest(empty_clearpool_plan(root / "above", limit + 1), root / "above-raw")
            mapped = []
            original = derivation.map_capture

            def counting(*args, **kwargs):
                mapped.append(args[0]["id"])
                return original(*args, **kwargs)

            with mock.patch.object(derivation, "map_capture", side_effect=counting):
                with self.assertRaisesRegex(
                    AlexandriaError,
                    refusal(
                        f"manifest lists {limit + 1} captures, above the {limit}-mapping limit "
                        "of a derived view, which maps each capture once"
                    ),
                ):
                    derivation.derive(root / "above-raw", root / "above-derived")
            self.assertEqual(mapped, [])
            self.assertFalse((root / "above-derived").exists())


class HostileManifestRecordTests(unittest.TestCase):
    """The decision draft states the order the manifest limits apply in, and what that costs."""

    def test_the_node_limit_applies_to_the_parsed_tree_as_the_decision_draft_states(self):
        # The byte limit is checked before a byte is read; the node limit can
        # only be counted on the tree the parser has already built.
        data = b"[" + b"0," * 20 + b"0]\n"
        with mock.patch.object(canonical.json, "loads", wraps=json.loads) as parse:
            with manifest_limits(nodes=20), self.assertRaisesRegex(
                AlexandriaError, refusal(f"manifest of {len(data)} bytes exceeds the 20-node limit"),
            ):
                release_module.load_manifest(data, "manifest")
        self.assertEqual(parse.call_count, 1)
        text = " ".join(DECISION_DRAFT.read_text(encoding="utf-8").split())
        self.assertNotIn("Readers enforce both limits before parsing.", text)
        self.assertNotIn("estimated 1 GB", text)
        self.assertIn("one above the node limit after parsing it, before accepting it", text)


def section(case, text, start, end):
    """The text between two markers, whitespace folded; a missing marker fails by name."""
    text = " ".join(text.split())
    case.assertIn(start, text)
    first = text.index(start)
    case.assertIn(end, text[first:])
    return text[first:text.index(end, first)]


def byte_counts(cell):
    """The byte counts one table cell lists, separated by semicolons."""
    return [int(value.strip().replace(",", "")) for value in cell.split(";")]


class RebuildProofRecordTests(unittest.TestCase):
    """The Step 4 proof states what the step changed, what it checked and what its runs resolve.

    Each check reads identifiers, paths and numbers rather than whole
    sentences, so a reword that keeps them passes.
    """

    def setUp(self):
        self.raw = PROOF.read_text(encoding="utf-8")

    def test_the_proof_names_the_commit_it_ran_on_and_every_test_file_the_step_changes(self):
        opening = section(self, self.raw, "# Epoch table split", "## Demonstrations")
        for token in (
            "`d97d3c5bd3055384e5df9ebfac23048ea79b4b5b`",
            "`3ffc3d45469ddeacad1ae68723c9d0c005fce181`",
            "`tests/test_version_propagation.py`",
            "`plugins/alexandria/tests/test_release_limits.py`",
            "`RebuildProofRecordTests`",
        ):
            self.assertIn(token, opening)
        self.assertNotRegex(opening, r"changes no [\w ,]*?\btests?\b\s*[.;]")

    def test_every_run_the_proof_records_names_the_commit_rather_than_the_step_tree(self):
        # Once the audit branch folds in, "the Step 4 tree" holds the audit
        # fixes too, and no recorded run used that tree.
        whole = " ".join(self.raw.split())
        self.assertNotIn("Step 4 tree", whole)
        memory = section(self, self.raw, "## Wildcat V2 check memory", "no budget is claimed")
        self.assertIn("on the Step 4 commit", memory)

    def test_the_proof_checks_every_section_3_identifier_and_states_the_count_it_corrects(self):
        study = section(
            self, STUDY.read_text(encoding="utf-8"),
            "**Byte identity.**", "**External dependencies.**",
        )
        pinned = list(dict.fromkeys(re.findall(r"sha256:[0-9a-f]{64}", study)))
        table = section(self, self.raw, "## Pinned identifiers", "## Split fixture")
        rows = re.findall(r"\| `(sha256:[0-9a-f]{64})` \|", table)
        self.assertEqual((len(pinned), len(rows)), (8, 8))
        self.assertEqual(rows, pinned)
        # Six interval identifiers and two committed releases, against the
        # runbook Exit's and section 6's "seven".
        prose = table.split("|", 1)[0]
        self.assertIn("seven", prose)
        self.assertIn("six distinct", prose)

    def test_the_proof_bounds_the_memory_comparison_by_the_base_spread(self):
        memory = section(self, self.raw, "## Wildcat V2 check memory", "no budget is claimed")
        table = self.raw[self.raw.index("## Wildcat V2 check memory"):]
        cells = {
            row.split("|")[1].strip(): row.split("|")[4]
            for row in table.splitlines()
            if row.startswith(("| Base, re-measured", "| Step 4 "))
        }
        base, step = byte_counts(cells["Base, re-measured"]), byte_counts(cells["Step 4"])
        self.assertEqual((len(base), len(step)), (3, 3))
        spread = max(base) - min(base)
        for figure in (
            f"{(min(step) / max(base) - 1) * 100:.2f}%",
            f"{(max(step) / min(base) - 1) * 100:.2f}%",
            f"{int(statistics.median(step) - statistics.median(base)):,} bytes",
            f"{spread:,} bytes",
            f"{(max(base) / min(base) - 1) * 100:.2f}%",
        ):
            self.assertIn(figure, memory)
        self.assertIn("resolve", memory)


if __name__ == "__main__":
    unittest.main()
