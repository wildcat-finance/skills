"""Log attributions in plan-derived parts: the build, receipt v4 and `check`.

The design record's `split-parts-rederive-and-refuse` cell loads the seven
tests of `AttributionPartBuildTests` and `AttributionPartCheckTests` by name.
The other classes cover the plan field's refusals, the plan-time component
count, receipt v4 under the wrong plan, the part budgets, the part capture,
unreadable or changed parts and the schemas. Every case runs the constructed
Wildcat path in process over `fixtures/wildcat-interval-transport.json`,
re-planned with `shards_per_component`. None opens a socket or starts a child
process.

A release that has to reach one of `check`'s own refusals is re-ingested after
its edit, so `verify` accepts it and the refusal is `check`'s. Only the cases
that change a release after verification patch `verify` instead.
"""

from contextlib import redirect_stderr
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import re
import socket
import tempfile
import unittest
from unittest import mock

from tests import test_usdc_interval as existing
from tests.test_wildcat_venue import (
    CREATED_AT,
    SECOND_PROVIDER,
    WildcatCase,
    WildcatTransport,
    schema_errors,
)
from alexandria_lib import interval, release as release_module
from alexandria_lib.canonical import MAX_LARGE_NODES, canonical_bytes
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.interval import (
    PARTS_FIELD,
    PARTS_RECEIPT_FORMAT,
    PARTS_RULE,
    SPLIT_FIELD,
    SUBJECT_RECEIPT_FORMAT,
    plan_digest,
    plan_shards,
    validate_plan,
)
from alexandria_lib.release import MAX_COMPONENTS, MAX_RAW_COMPONENT_BYTES
from alexandria_lib.venues import wildcat_v1
import usdc_interval
from usdc_interval import (
    FIXED_COMPONENTS,
    PART_CLASS,
    PART_FORMAT,
    Builder,
    Collector,
    Reconciler,
    attribution_part_gap,
    attribution_parts,
    check_interval,
    journal_components,
)


def repository_root() -> Path:
    """The checkout holding this module, found by its marketplace manifest rather than by depth."""
    here = Path(__file__).resolve()
    for candidate in here.parents:
        if (
            (candidate / ".claude-plugin" / "marketplace.json").is_file()
            and (candidate / "plugins" / "alexandria" / "tests" / here.name).is_file()
        ):
            return candidate
    raise AssertionError(
        f"no directory above {here} holds both .claude-plugin/marketplace.json and this module"
    )


REPO_ROOT = repository_root()
PLUGIN = REPO_ROOT / "plugins" / "alexandria"
SCHEMAS = PLUGIN / "schemas"
COLLECTOR_DOCUMENT = PLUGIN / "docs" / "usdc-interval-collector.md"

# What the constructed fixtures build at the Step 1 head,
# a14977e50491f42170cb14aa11fe72c6ebaff0ca, measured from an export of that
# commit: the release identifier, the plan digest and the collector
# checkpoint's SHA-256, per venue and `shards_per_component` (None: no
# split). A plan without the part field has to keep all three.
TODAYS_BYTES = {
    ("wildcat-v2", None): (
        "sha256:0ca5520ff5b1744d6f5ddb5c7c32b90e4776952139182cd3743517569b8219dc",
        "fdae651554b9443153aff84ad422a57d5d2f8034e5485281ba4b8a5bff13c465",
        "12ce518499b6330a7fe1b31ed49f33b124663368dfafa13fd644a99929fe2243",
    ),
    ("wildcat-v2", 1): (
        "sha256:04860e7497d587371f6e546e8097fbf7d01015f101a0573cfb02ca7bdcc655b2",
        "82033bbae7d401291c7062b4b6f1c747a115dcd68b77e709852b72d1df37e926",
        "60ed84219e6954cc0ab0890ac0ec9ab115313699fbc7a0015710d4d4ef03feab",
    ),
    ("wildcat-v2", 2): (
        "sha256:990904318e7a72d2983ef3299851f5afaefe1f1bb5c8ba0db0570578daa57fb4",
        "cac4b500bc4cbd5d45d05ee5d4740bd90d0c698c35d308c32395e65168f8e73c",
        "92b1737df5c62fe1436b6425d6c0dc31937df5ba5fe23293c63ecd7fd9cdff92",
    ),
    ("wildcat-v1", None): (
        "sha256:5298309b97aa00c3c0e5609ff6df95aa876732c754fda7269eb7dc5aa192c30b",
        "96352a04a8b62463534d78b498e74365211f7abdb7531e8c9d34acc3154c5a9c",
        "8744d865522d5048a65ff7c3140c8d6ea9d650340641467fc5358c824309c66a",
    ),
}
V4_SEMANTICS = "v4-subject-positional-parts"


def replanned(state, shards_per_component=1, *, parts=True):
    """The fixture state re-planned with the journal split and, unless told otherwise, the part rule."""
    state = deepcopy(state)
    state["plan"][SPLIT_FIELD] = shards_per_component
    if parts:
        state["plan"][PARTS_FIELD] = PARTS_RULE
    return state


def without_logs(state, shard):
    """The state with one shard's preserved logs removed, so its range holds no row."""
    state = deepcopy(state)
    state["logs"][str(shard)] = []
    return state


def pointer(document, selector):
    """The value a coverage selector names, or None where it names nothing."""
    current = document
    for token in selector.split("/")[1:]:
        if not isinstance(current, dict) or token not in current:
            return None
        current = current[token]
    return current


def recount(capture, document):
    """Redo one capture's counts for its edited document, so `ingest` accepts the bytes.

    A document the selectors no longer resolve in, and raw bytes (None), keep
    no counted collection: the capture stays partial on its gap sentence.
    """
    coverage = capture["coverage"]
    values = [
        None if document is None else pointer(document, item["selector"])
        for item in coverage["collections"]
    ]
    if any(not isinstance(value, list) for value in values):
        coverage["collections"] = []
        coverage["record_count"] = 0
        return
    for item, value in zip(coverage["collections"], values):
        item["record_count"] = len(value)
    coverage["record_count"] = sum(len(value) for value in values)


def reissue(source, output, *, edit=None, raw=None, captures=None):
    """Re-ingest `source` after an edit, so `verify` accepts what `check` has to refuse.

    `edit(documents)` changes the component documents, keyed by name, in
    place: deleting a key drops that component and its capture, adding one
    adds a component. `raw` maps a name to the exact bytes to ship instead.
    Every kept capture's counts are redone for the edited bytes before
    `captures(by_id)` edits the captures. Only fresh paths are written.
    """
    source, output = Path(source), Path(output)
    if os.path.lexists(output):
        raise AssertionError(f"{output} already exists; a reissued release needs a fresh path")
    manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    declared = {item["name"]: item for item in manifest["components"]}
    documents = {
        name: json.loads((source / item["object_path"]).read_text(encoding="utf-8"))
        for name, item in declared.items()
    }
    if edit is not None:
        edit(documents)
    raw = dict(raw or {})
    names = sorted(set(documents) | set(raw))
    by_id = {}
    for capture in manifest["captures"]:
        if capture["component"] in names:
            copied = deepcopy(capture)
            del copied["component_sha256"]
            recount(copied, None if copied["component"] in raw else documents[copied["component"]])
            by_id[copied["id"]] = copied
    if captures is not None:
        captures(by_id)
    with tempfile.TemporaryDirectory(prefix="alexandria-reissue-") as directory:
        work = Path(directory)
        entries = []
        for name in names:
            data = raw[name] if name in raw else canonical_bytes(
                documents[name], max_nodes=MAX_LARGE_NODES,
            )
            with open(work / f"{name}.json", "xb") as handle:
                handle.write(data)
            template = declared.get(name, {
                "access": "public", "media_type": "application/json",
                "redistribution": "permitted", "role": "log-attributions",
            })
            entries.append({
                "access": template["access"], "media_type": template["media_type"],
                "name": name, "path": f"{name}.json",
                "redistribution": template["redistribution"], "role": template["role"],
            })
        plan = {
            "captures": [by_id[key] for key in sorted(by_id)],
            "components": entries,
            "format": "alexandria-capture-plan/v1",
            "release": manifest["release"],
        }
        with open(work / "capture-plan.json", "xb") as handle:
            handle.write(canonical_bytes(plan))
        return release_module.ingest(work / "capture-plan.json", output)


def nodes(value) -> int:
    """Count nodes the way the canonical encoder does: every value, never a key."""
    total, stack = 0, [value]
    while stack:
        current = stack.pop()
        total += 1
        if isinstance(current, list):
            stack.extend(current)
        elif isinstance(current, dict):
            stack.extend(current.values())
    return total


def label(name, part):
    """The part's name and shard range, as every part refusal writes them, for a pattern."""
    return re.escape(f"{name} (shards {part['first']} to {part['last']})")


class PartCase(WildcatCase):
    """The constructed V2 path, re-planned so each journal range carries its own part."""

    def split(self, name="split", shards_per_component=1, *, state=None, parts=True):
        """Build one release from the re-planned fixture; return it with its plan."""
        state = replanned(state or self.state, shards_per_component, parts=parts)
        output, _release_id = self.released(name, state)
        return output, state["plan"]

    def document(self, output, name):
        return existing.component_document(output, name)

    def manifest(self, output):
        return json.loads((Path(output) / "manifest.json").read_text(encoding="utf-8"))

    def reissued(self, output, name, **edits):
        target = self.root / name
        reissue(output, target, **edits)
        return target

    def refuses(self, release, pattern):
        """`check` refuses the release with an AlexandriaError whose whole message matches."""
        with self.assertRaises(AlexandriaError) as caught:
            check_interval(release)
        self.assertRegex(str(caught.exception), f"^{pattern}$")

    def part_sizes(self, output, plan):
        manifest = {item["name"]: item for item in self.manifest(output)["components"]}
        return {name: manifest[name]["bytes"] for name in attribution_parts(plan)}


class AttributionPartBuildTests(PartCase):
    """A split plan writes one part per journal range; a plan without the field builds today's bytes."""

    def test_a_split_plan_writes_one_part_per_journal_range(self):
        whole, _release_id = self.released("whole")
        today = self.document(whole, "epoch-table")
        rows = today["log_attributions"]
        for size in (1, 2, 3, 4):
            with self.subTest(shards_per_component=size):
                output, plan = self.split(f"split-{size}", size)
                parts = attribution_parts(plan)
                journals = journal_components(plan, tuple(plan["evidence_classes"]))
                logs = [part for part in journals.values() if part["class"] == "logs"]
                self.assertEqual(
                    [(part["index"], part["first"], part["last"]) for part in parts.values()],
                    [(part["index"], part["first"], part["last"]) for part in logs],
                )
                self.assertEqual(list(parts), [f"{PART_CLASS}.{index}" for index in range(len(logs))])
                manifest = self.manifest(output)
                names = {item["name"] for item in manifest["components"]}
                self.assertEqual(names, set(FIXED_COMPONENTS) | set(journals) | set(parts))
                roles = {item["name"]: item["role"] for item in manifest["components"]}

                receipt = self.document(output, "epoch-table")
                self.assertEqual(receipt["format"], PARTS_RECEIPT_FORMAT)
                self.assertNotIn("log_attributions", receipt)
                self.assertEqual(
                    {key: value for key, value in receipt.items()
                     if key not in ("format", "log_attribution_parts")},
                    {key: value for key, value in today.items()
                     if key not in ("format", "log_attributions")},
                )
                listing, joined = [], []
                captures = self.captures(output)
                for name, part in parts.items():
                    low = plan["shards"][part["first"]]["start"]
                    high = plan["shards"][part["last"]]["end"]
                    expected = [row for row in rows if low <= int(row["block_number"]) <= high]
                    self.assertEqual(self.document(output, name), {
                        "first_shard": part["first"], "format": PART_FORMAT,
                        "last_shard": part["last"], "part": part["index"], "rows": expected,
                    }, name)
                    listing.append({
                        "component": name, "first_shard": part["first"],
                        "last_shard": part["last"], "rows": len(expected),
                    })
                    joined.extend(expected)
                    capture = captures[name]
                    self.assertEqual(roles[name], "log-attributions", name)
                    self.assertEqual(capture["evidence_class"], "header-bound", name)
                    self.assertEqual(capture["coverage"]["collections"], [
                        {"name": PART_CLASS, "record_count": len(expected), "selector": "/rows"},
                    ], name)
                    self.assertEqual(capture["coverage"]["status"], "partial", name)
                    sentence = attribution_part_gap(plan, part)
                    self.assertIn(sentence, capture["coverage"]["gaps"], name)
                    self.assertIn(
                        f"shards {part['first']} to {part['last']}, blocks {low} to {high}", sentence,
                    )
                    self.assertEqual(
                        set(capture["scope"]["interval"]), {"end", "kind", "start"}, name,
                    )
                self.assertEqual(receipt["log_attribution_parts"], listing)
                # Every row once, in the order `attribute_logs` gives them.
                self.assertEqual(joined, rows)
                self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)

        output, _plan = self.split("empty-range", 1, state=without_logs(self.state, 1))
        self.assertEqual(self.document(output, f"{PART_CLASS}.1")["rows"], [])
        self.assertEqual(
            self.document(output, "epoch-table")["log_attribution_parts"][1]["rows"], 0,
        )
        self.assertEqual(
            self.captures(output)[f"{PART_CLASS}.1"]["coverage"]["record_count"], 0,
        )
        self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)

    def test_a_plan_without_the_field_builds_todays_bytes(self):
        for size in (None, 1, 2):
            with self.subTest(shards_per_component=size):
                state = deepcopy(self.state)
                if size is not None:
                    state["plan"][SPLIT_FIELD] = size
                plan = state["plan"]
                self.assertNotIn(PARTS_FIELD, plan)
                self.assertEqual(attribution_parts(plan), {})
                staging = self.staged(f"today-{size}", state)
                existing.historical_reconciliation(staging)
                checkpoint = (staging / interval.CHECKPOINT_NAME).read_bytes()
                output = self.root / f"today-{size}"
                release_id = Builder(plan, staging, self.registry, created_at=CREATED_AT).build(output)
                self.assertEqual(
                    (release_id, plan_digest(plan), hashlib.sha256(checkpoint).hexdigest()),
                    TODAYS_BYTES[("wildcat-v2", size)],
                )
                receipt = self.document(output, "epoch-table")
                self.assertEqual(receipt["format"], SUBJECT_RECEIPT_FORMAT)
                self.assertIn("log_attributions", receipt)
                names = {item["name"] for item in self.manifest(output)["components"]}
                self.assertFalse(any(name.startswith(PART_CLASS) for name in names))
                self.assertEqual(check_interval(output)["receipt_semantics"], "v3-subject-positional")


class AttributionPartCheckTests(PartCase):
    """`check` re-derives every part from its own shards and refuses a wrong part by name."""

    def test_check_rederives_every_part_from_its_own_shards(self):
        whole, _release_id = self.released("whole")
        today = check_interval(whole)
        original = usdc_interval.attribute_logs
        for size in (1, 2):
            with self.subTest(shards_per_component=size):
                output, plan = self.split(f"split-{size}", size)
                calls = []

                def recording(*args, **kwargs):
                    rows = original(*args, **kwargs)
                    calls.append((kwargs, rows))
                    return rows

                with mock.patch.object(usdc_interval, "attribute_logs", recording), \
                        mock.patch.object(socket.socket, "connect",
                                          side_effect=AssertionError("network used")):
                    summary = check_interval(output)
                self.assertEqual(summary["receipt_semantics"], V4_SEMANTICS)
                for field in ("epochs", "implementations", "interval", "reconciliation", "shard_statuses"):
                    self.assertEqual(summary[field], today[field], field)
                # One call, made exactly as for an unsplit release, and each
                # part is the slice of its rows that its own shards cover.
                self.assertEqual(len(calls), 1)
                kwargs, derived = calls[0]
                self.assertEqual(set(kwargs), {"upgrade_topic"})
                joined = []
                for name, part in attribution_parts(plan).items():
                    low = plan["shards"][part["first"]]["start"]
                    high = plan["shards"][part["last"]]["end"]
                    held = self.document(output, name)["rows"]
                    self.assertEqual(
                        held, [row for row in derived if low <= int(row["block_number"]) <= high],
                        name,
                    )
                    journal = self.document(output, f"logs.{part['index']}")
                    preserved = {
                        (int(entry["blockNumber"], 16), int(entry["logIndex"], 16))
                        for record in journal["records"]
                        for entry in json.loads(record["response"])["result"]
                    }
                    self.assertEqual(
                        {(int(row["block_number"]), row["log_index"]) for row in held}, preserved, name,
                    )
                    joined.extend(held)
                self.assertEqual(joined, derived)

        output, _plan = self.split("empty-range", 1, state=without_logs(self.state, 1))
        self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)
        self.assertEqual(self.document(output, f"{PART_CLASS}.1")["rows"], [])

    def test_a_missing_part_refuses_by_name(self):
        output, _plan = self.split()

        def drop(documents):
            del documents[f"{PART_CLASS}.2"]

        def unlist(documents):
            del documents["epoch-table"]["log_attribution_parts"][3]

        def uncapture(by_id):
            del by_id[f"{PART_CLASS}.1"]

        cases = {
            "component": (
                dict(edit=drop),
                r"the release lacks its log-attributions\.2 \(shards 2 to 2\) component",
            ),
            "receipt entry": (
                dict(edit=unlist),
                r"the interval receipt does not list log-attributions\.3 \(shards 3 to 3\)",
            ),
            "capture": (
                dict(captures=uncapture),
                r"the release carries no capture for its log-attributions\.1 \(shards 1 to 1\) "
                r"component",
            ),
        }
        for case, (edits, pattern) in cases.items():
            with self.subTest(missing=case):
                self.refuses(self.reissued(output, case.replace(" ", "-"), **edits), pattern)

    def test_an_extra_part_refuses_by_name(self):
        output, _plan = self.split()
        extra = f"{PART_CLASS}.4"

        def add(documents):
            documents[extra] = dict(documents[f"{PART_CLASS}.3"], first_shard=4, last_shard=4, part=4)

        def capture(by_id):
            copied = deepcopy(by_id[f"{PART_CLASS}.3"])
            copied["id"] = copied["component"] = extra
            by_id[extra] = copied

        def overlist(documents):
            documents["epoch-table"]["log_attribution_parts"].append(
                {"component": extra, "first_shard": 4, "last_shard": 4, "rows": 0}
            )

        self.refuses(
            self.reissued(output, "added", edit=add, captures=capture),
            r"the release carries a log-attributions\.4 component the plan does not declare",
        )
        self.refuses(
            self.reissued(output, "overlisted", edit=overlist),
            r"the interval receipt lists log-attributions\.4 at position 4, beyond the 4 "
            r"log-attributions parts the plan derives",
        )

        # A part in a release whose plan declares none is a component the
        # plan does not declare either.
        whole, _release_id = self.released("whole")

        def stray(documents):
            documents[f"{PART_CLASS}.0"] = {
                "first_shard": 0, "format": PART_FORMAT, "last_shard": 0, "part": 0, "rows": [],
            }

        self.refuses(
            self.reissued(whole, "stray", edit=stray),
            r"the release carries a log-attributions\.0 component the plan does not declare",
        )

    def test_reordered_parts_refuse_by_name(self):
        output, _plan = self.split()

        def swap_entries(documents):
            listing = documents["epoch-table"]["log_attribution_parts"]
            listing[0], listing[1] = listing[1], listing[0]

        def swap_documents(documents):
            one, two = f"{PART_CLASS}.1", f"{PART_CLASS}.2"
            documents[one], documents[two] = documents[two], documents[one]

        def swap_rows(documents):
            one, two = documents[f"{PART_CLASS}.1"], documents[f"{PART_CLASS}.2"]
            one["rows"], two["rows"] = two["rows"], one["rows"]
            listing = documents["epoch-table"]["log_attribution_parts"]
            listing[1]["rows"], listing[2]["rows"] = len(one["rows"]), len(two["rows"])

        def reverse_rows(documents):
            documents[f"{PART_CLASS}.0"]["rows"].reverse()

        cases = {
            "receipt entries": (
                swap_entries,
                r"the interval receipt lists log-attributions\.1 at position 0, where the plan "
                r"derives log-attributions\.0 \(shards 0 to 0\)",
            ),
            "part documents": (
                swap_documents,
                r"component log-attributions\.1 \(shards 1 to 1\) names itself part 2, not part 1",
            ),
            "rows across parts": (
                swap_rows,
                r"component log-attributions\.1 \(shards 1 to 1\) holds a row at block 25895380, "
                r"outside its blocks 25895360 to 25895379",
            ),
            "rows inside a part": (
                reverse_rows,
                r"component log-attributions\.0 \(shards 0 to 0\) does not hold the rows "
                r"attribute_logs derives from the preserved logs of its shards",
            ),
        }
        for case, (edit, pattern) in cases.items():
            with self.subTest(reordered=case):
                self.refuses(self.reissued(output, case.replace(" ", "-"), edit=edit), pattern)

    def test_an_altered_part_refuses_by_name(self):
        output, plan = self.split()
        other = "0x" + "ab" * 32
        for name, part in attribution_parts(plan).items():
            def alter(documents, name=name):
                documents[name]["rows"][0]["transaction_hash"] = other

            with self.subTest(part=name, altered="a row"):
                self.refuses(
                    self.reissued(output, f"altered-{part['index']}", edit=alter),
                    f"component {label(name, part)} does not hold the rows attribute_logs "
                    "derives from the preserved logs of its shards",
                )

        def invent(documents):
            row = dict(documents[f"{PART_CLASS}.3"]["rows"][0], log_index=99)
            documents[f"{PART_CLASS}.3"]["rows"].append(row)
            documents["epoch-table"]["log_attribution_parts"][3]["rows"] = 2

        with self.subTest(altered="an invented row"):
            self.refuses(
                self.reissued(output, "invented", edit=invent),
                r"component log-attributions\.3 \(shards 3 to 3\) does not hold the rows "
                r"attribute_logs derives from the preserved logs of its shards",
            )

        # Altered after verification: the bytes `check` reads are not the
        # ones the verified manifest records, whatever they now say.
        release_id = self.manifest(output)["release_id"]
        path = existing.component_path(output, f"{PART_CLASS}.2")
        document = json.loads(path.read_text(encoding="utf-8"))
        document["rows"][0]["transaction_hash"] = other
        path.write_bytes(canonical_bytes(document))
        with self.subTest(altered="after verification"), \
                mock.patch.object(usdc_interval, "verify", return_value=release_id):
            self.refuses(
                output,
                r"component log-attributions\.2 \(shards 2 to 2\) does not carry the size and "
                r"SHA-256 the verified manifest records, so it changed after the release was "
                r"verified",
            )


class PartShapeTests(PartCase):
    """Every field of the part list and of a part document is the plan's, or refuses naming the part."""

    def test_a_part_or_its_receipt_entry_in_another_shape_refuses_by_name(self):
        output, _plan = self.split()
        part = f"{PART_CLASS}.2"
        named = r"log-attributions\.2 \(shards 2 to 2\)"

        def on_part(change):
            return lambda documents: change(documents[part])

        def on_entry(change):
            return lambda documents: change(documents["epoch-table"]["log_attribution_parts"][2])

        cases = {
            "part format": (
                on_part(lambda value: value.__setitem__("format", "alexandria-interval-log-attributions/v0")),
                rf"component {named} is not an alexandria-interval-log-attributions/v1 document",
            ),
            "part field": (
                on_part(lambda value: value.__setitem__("extra", 1)),
                rf"component {named} is not an alexandria-interval-log-attributions/v1 document",
            ),
            "part index": (
                on_part(lambda value: value.__setitem__("part", 3)),
                rf"component {named} names itself part 3, not part 2",
            ),
            "part range": (
                on_part(lambda value: value.__setitem__("first_shard", 1)),
                rf"component {named} declares another shard range than the plan derives for it",
            ),
            "part range type": (
                on_part(lambda value: value.__setitem__("last_shard", "2")),
                rf"component {named} declares another shard range than the plan derives for it",
            ),
            "part rows": (
                on_part(lambda value: value.__setitem__("rows", {"rows": []})),
                rf"component {named} carries no row list",
            ),
            "row shape": (
                on_part(lambda value: value["rows"][0].__setitem__("extra", 1)),
                rf"component {named}: log attribution has an unknown shape",
            ),
            "row subject": (
                on_part(lambda value: value["rows"][0].__setitem__("subject", "0x" + "1" * 40)),
                rf"component {named}: log attribution names an undeclared subject",
            ),
            "row index": (
                on_part(lambda value: value["rows"][0].__setitem__("log_index", True)),
                rf"component {named}: log attribution indexes must be non-negative integers",
            ),
            "row block": (
                on_part(lambda value: value["rows"][0].__setitem__("block_number", "25895400")),
                rf"component {named} holds a row at block 25895400, outside its blocks "
                r"25895380 to 25895399",
            ),
            "entry shape": (
                on_entry(lambda value: value.__setitem__("extra", 1)),
                rf"the interval receipt's entry for {named} has an unknown shape",
            ),
            "entry range": (
                on_entry(lambda value: value.__setitem__("first_shard", 1)),
                rf"the interval receipt names another shard range for {named}",
            ),
            "entry range type": (
                on_entry(lambda value: value.__setitem__("last_shard", "2")),
                rf"the interval receipt names another shard range for {named}",
            ),
            "entry count type": (
                on_entry(lambda value: value.__setitem__("rows", "4")),
                rf"the interval receipt's row count for {named} is not a count",
            ),
            "entry count": (
                on_entry(lambda value: value.__setitem__("rows", 5)),
                rf"component {named} holds 4 rows, but the interval receipt counts 5",
            ),
        }
        for case, (edit, pattern) in cases.items():
            with self.subTest(case=case):
                self.refuses(self.reissued(output, case.replace(" ", "-"), edit=edit), pattern)

    def test_a_boolean_never_stands_for_a_part_index_or_shard(self):
        output, _plan = self.split()
        part = f"{PART_CLASS}.1"
        named = r"log-attributions\.1 \(shards 1 to 1\)"
        cases = {
            "part": (
                lambda documents: documents[part].__setitem__("part", True),
                rf"component {named} names itself part True, not part 1",
            ),
            "first shard": (
                lambda documents: documents[part].__setitem__("first_shard", True),
                rf"component {named} declares another shard range than the plan derives for it",
            ),
            "entry shard": (
                lambda documents: documents["epoch-table"]["log_attribution_parts"][1]
                .__setitem__("last_shard", True),
                rf"the interval receipt names another shard range for {named}",
            ),
            "entry count": (
                lambda documents: documents["epoch-table"]["log_attribution_parts"][1]
                .__setitem__("rows", True),
                rf"the interval receipt's row count for {named} is not a count",
            ),
        }
        for case, (edit, pattern) in cases.items():
            with self.subTest(case=case):
                self.refuses(self.reissued(output, f"bool-{case.replace(' ', '-')}", edit=edit), pattern)

    def test_a_part_list_that_is_not_a_list_refuses(self):
        output, _plan = self.split()

        def replace(documents):
            documents["epoch-table"]["log_attribution_parts"] = {}

        self.refuses(
            self.reissued(output, "not-a-list", edit=replace),
            r"the interval receipt's log_attribution_parts is not a list",
        )


class PartReadTests(PartCase):
    """A part `check` cannot read, or one changed after verification, refuses naming the part."""

    def test_unreadable_part_bytes_refuse_by_name(self):
        output, _plan = self.split()
        named = r"component log-attributions\.1 \(shards 1 to 1\)"
        cases = {
            "not json": (b"{\n", rf"{named} is not valid JSON"),
            "duplicate key": (b'{"part":1,"part":1}\n', rf"{named} contains duplicate key 'part'"),
            "nan": (b'{"part":NaN}\n', rf"{named} contains a non-finite number"),
            "float": (b'{"part":1.5}\n', rf"{named} contains a floating-point number"),
            "not utf-8": (b'{"part":"\xff"}\n', rf"{named} is not UTF-8"),
            "bom": (b'\xef\xbb\xbf{"part":1}\n', rf"{named} must not start with a UTF-8 BOM"),
            "list": (b"[]\n", rf"{named} is not an alexandria-interval-log-attributions/v1 document"),
        }
        for case, (data, pattern) in cases.items():
            with self.subTest(case=case):
                self.refuses(
                    self.reissued(output, case.replace(" ", "-"), raw={f"{PART_CLASS}.1": data}),
                    pattern,
                )

    def test_the_cli_names_the_unreadable_part_without_a_traceback(self):
        output, _plan = self.split()
        broken = self.reissued(output, "broken", raw={f"{PART_CLASS}.1": b"{\n"})
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            code = usdc_interval.main(["check", str(broken)])
        self.assertEqual(code, 1)
        self.assertEqual(
            stderr.getvalue(),
            "usdc-interval: component log-attributions.1 (shards 1 to 1) is not valid JSON\n",
        )

    def test_a_part_object_swapped_after_verification_refuses_by_name(self):
        output, _plan = self.split()
        release_id = self.manifest(output)["release_id"]
        path = existing.component_path(output, f"{PART_CLASS}.1")
        other = existing.component_path(output, f"{PART_CLASS}.3")
        named = r"release component log-attributions\.1 \(shards 1 to 1\)"
        cases = {
            "directory": (lambda: path.mkdir(), rf"{named} must name a regular file"),
            "symlink": (lambda: path.symlink_to(other), rf"{named} must not pass through a symlink"),
        }
        saved = path.read_bytes()
        for case, (swap, pattern) in cases.items():
            with self.subTest(case=case):
                path.unlink()
                swap()
                try:
                    with mock.patch.object(usdc_interval, "verify", return_value=release_id):
                        self.refuses(output, pattern)
                finally:
                    if path.is_symlink() or path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        path.rmdir()
                    with open(path, "xb") as handle:
                        handle.write(saved)
        self.assertEqual(check_interval(output)["receipt_semantics"], V4_SEMANTICS)

    def test_a_manifest_changed_after_verification_refuses(self):
        output, _plan = self.split()
        release_id = self.manifest(output)["release_id"]
        path = Path(output) / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        for capture in manifest["captures"]:
            if capture["id"] == f"{PART_CLASS}.2":
                capture["coverage"]["gaps"].append("a sentence verification never saw")
        path.write_bytes(canonical_bytes(manifest))
        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
            self.refuses(
                output,
                r"the manifest check read does not hash to the release identity verification "
                r"accepted, so the release changed after it was verified",
            )


class PartPlanTests(PartCase):
    """The plan field refuses by name wherever it is not admitted, and the part count is planned."""

    def test_the_field_refuses_by_name_on_a_single_proxy_plan(self):
        state = existing.fixture()
        plan = deepcopy(state["plan"])
        plan[SPLIT_FIELD] = 1
        plan[PARTS_FIELD] = PARTS_RULE
        message = (
            r"^interval plan log_attribution_parts is admitted only on an "
            r"alexandria-interval-plan/v2 subject-set plan$"
        )
        with self.assertRaisesRegex(AlexandriaError, message):
            validate_plan(plan)
        transport = existing.FixtureTransport(state)
        with self.assertRaisesRegex(AlexandriaError, message):
            Collector(plan, self.scratch("single-proxy"), transport)
        self.assertEqual(transport.calls, [])

    def test_the_field_refuses_by_name_without_shards_per_component(self):
        plan = deepcopy(self.plan)
        plan[PARTS_FIELD] = PARTS_RULE
        message = (
            r"^interval plan log_attribution_parts requires shards_per_component, whose journal "
            r"ranges the parts share$"
        )
        with self.assertRaisesRegex(AlexandriaError, message):
            validate_plan(plan)
        transport = WildcatTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, message):
            Collector(plan, self.scratch("unsplit"), transport, registry=self.registry)
        self.assertEqual(transport.calls, [])

    def test_the_field_refuses_by_name_with_another_value(self):
        for value in ("journal-range", "", "JOURNAL-RANGES", None, 1, True, [PARTS_RULE], {"rule": PARTS_RULE}):
            with self.subTest(value=value):
                plan = replanned(self.state, 1)["plan"]
                plan[PARTS_FIELD] = value
                with self.assertRaisesRegex(
                    AlexandriaError,
                    r"^interval plan log_attribution_parts must be 'journal-ranges', its one "
                    r"admitted value$",
                ):
                    validate_plan(plan)

    def test_the_part_count_refuses_before_any_request(self):
        # Over the shard limit's 4,096 one-block shards, one per range, the parts
        # take the count to 16,391: 6 fixed, the opening journal, three classes
        # of 4,096 journals and 4,096 parts, seven above the cap.
        plan = replanned(self.state, 1)["plan"]
        start = int(plan["interval"]["start"])
        end = start + interval.MAX_SHARDS - 1
        plan["interval"]["end"] = str(end)
        plan["finality"]["block_number"] = str(end)
        plan["shard_width"] = 1
        plan["shards"] = plan_shards(start, end, 1)
        message = (
            r"^the plan derives 12289 journal components and 4096 log-attributions parts, so its "
            rf"release would carry 16391 components, above the {MAX_COMPONENTS}-component limit$"
        )
        transport = WildcatTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, message):
            Collector(plan, self.scratch("too-many"), transport, registry=self.registry)
        with self.assertRaisesRegex(AlexandriaError, message):
            Reconciler(
                plan, self.scratch("too-many-reconcile"), transport, SECOND_PROVIDER,
                registry=self.registry,
            )
        with self.assertRaisesRegex(AlexandriaError, message):
            Builder(plan, self.scratch("too-many-build"), self.registry, created_at=CREATED_AT)
        self.assertEqual(transport.calls, [])
        # The same journals without the parts fit.
        del plan[PARTS_FIELD]
        Collector(plan, self.scratch("fits"), WildcatTransport(self.state), registry=self.registry)
        self.assertEqual(
            len(FIXED_COMPONENTS) + len(journal_components(plan, tuple(plan["evidence_classes"]))),
            12295,
        )

    def test_a_parts_plan_stages_the_same_tree_as_its_split_twin(self):
        split = self.staged("twin", replanned(self.state, 1, parts=False))
        parts_state = replanned(self.state, 1)
        parts = self.staged("parts", parts_state)
        self.assertEqual(existing.journal_files(parts), existing.journal_files(split))
        with_parts = json.loads((parts / interval.CHECKPOINT_NAME).read_text(encoding="utf-8"))
        twin = json.loads((split / interval.CHECKPOINT_NAME).read_text(encoding="utf-8"))
        self.assertEqual(with_parts.pop("plan_sha256"), plan_digest(parts_state["plan"]))
        twin.pop("plan_sha256")
        self.assertEqual(with_parts, twin)


class ReceiptFormatTests(PartCase):
    """Receipt v4 appears exactly when the plan declares the part rule."""

    def test_a_v4_receipt_under_a_plan_without_the_field_refuses(self):
        output, _plan = self.split()

        def unsplit(documents):
            plan = documents["interval-plan"]
            del plan[PARTS_FIELD]
            documents["reconciliation"]["plan_sha256"] = plan_digest(plan)
            for name in [name for name in documents if name.startswith(PART_CLASS)]:
                del documents[name]

        self.refuses(
            self.reissued(output, "v4-unsplit", edit=unsplit),
            r"the interval receipt is alexandria-interval-receipt/v4, but the plan declares no "
            r"log_attribution_parts",
        )

    def test_a_v3_receipt_under_a_split_plan_refuses(self):
        output, _plan = self.split()

        def fold(documents):
            receipt = documents["epoch-table"]
            receipt["log_attributions"] = [
                row for entry in receipt.pop("log_attribution_parts")
                for row in documents[entry["component"]]["rows"]
            ]
            receipt["format"] = SUBJECT_RECEIPT_FORMAT

        self.refuses(
            self.reissued(output, "v3-split", edit=fold),
            r"the plan declares log_attribution_parts, so its receipt must be "
            r"alexandria-interval-receipt/v4, not alexandria-interval-receipt/v3",
        )


class PartBudgetTests(PartCase):
    """A part above the component byte ceiling or the node limit refuses by name in the build and in `check`."""

    def largest(self, output, plan):
        sizes = self.part_sizes(output, plan)
        name = max(sizes, key=sizes.get)
        others = [size for other, size in sizes.items() if other != name]
        self.assertTrue(all(size < sizes[name] - 1 for size in others))
        return name, sizes[name]

    def test_the_part_bounds_are_the_component_bounds(self):
        self.assertEqual(usdc_interval.MAX_PART_BYTES, MAX_RAW_COMPONENT_BYTES)
        self.assertEqual(usdc_interval.MAX_PART_BYTES, 67_108_864)
        self.assertEqual(usdc_interval.MAX_PART_NODES, usdc_interval.MAX_RESPONSE_NODES)
        self.assertEqual(usdc_interval.MAX_PART_NODES, 2_000_000)

    def test_a_part_over_the_byte_budget_refuses_by_name_in_the_build(self):
        output, plan = self.split("measured")
        name, size = self.largest(output, plan)
        part = attribution_parts(plan)[name]
        staging = self.staged("over", replanned(self.state, 1))
        with mock.patch.object(usdc_interval, "MAX_PART_BYTES", size - 1):
            with self.assertRaises(AlexandriaError) as caught:
                Builder(plan, staging, self.registry, created_at=CREATED_AT).build(self.root / "over")
        self.assertEqual(
            str(caught.exception),
            f"{name} (shards {part['first']} to {part['last']}) encodes to {size} bytes, above "
            f"the {size - 1}-byte component ceiling",
        )
        self.assertFalse((self.root / "over").exists())

    def test_a_part_over_the_node_budget_refuses_by_name_in_the_build(self):
        output, plan = self.split("measured")
        counts = {name: nodes(self.document(output, name)) for name in attribution_parts(plan)}
        name = max(counts, key=counts.get)
        self.assertTrue(all(count < counts[name] for other, count in counts.items() if other != name))
        part = attribution_parts(plan)[name]
        limit = counts[name] - 1
        staging = self.staged("over", replanned(self.state, 1))
        with mock.patch.object(usdc_interval, "MAX_PART_NODES", limit):
            with self.assertRaises(AlexandriaError) as caught:
                Builder(plan, staging, self.registry, created_at=CREATED_AT).build(self.root / "over")
        self.assertEqual(
            str(caught.exception),
            f"{name} (shards {part['first']} to {part['last']}) cannot be written: JSON value "
            f"exceeds the {limit}-node limit",
        )

    def test_a_part_over_the_byte_budget_refuses_by_name_in_check(self):
        output, plan = self.split()
        name, size = self.largest(output, plan)
        part = attribution_parts(plan)[name]
        with mock.patch.object(usdc_interval, "MAX_PART_BYTES", size - 1):
            self.refuses(
                output,
                rf"component {label(name, part)} holds {size} bytes, above the {size - 1}-byte "
                "component ceiling",
            )

    def test_a_part_over_the_node_budget_refuses_by_name_in_check(self):
        output, plan = self.split()
        counts = {name: nodes(self.document(output, name)) for name in attribution_parts(plan)}
        name = max(counts, key=counts.get)
        part = attribution_parts(plan)[name]
        limit = counts[name] - 1
        with mock.patch.object(usdc_interval, "MAX_PART_NODES", limit):
            self.refuses(output, rf"component {label(name, part)} exceeds the {limit}-node limit")


class PartCaptureTests(PartCase):
    """A part's capture names its shards and blocks, counts `/rows` and claims nothing else."""

    def test_a_part_capture_without_its_gap_sentence_refuses(self):
        output, plan = self.split()
        parts = attribution_parts(plan)
        name = f"{PART_CLASS}.2"
        other = attribution_part_gap(plan, parts[f"{PART_CLASS}.1"])

        def replace(by_id):
            by_id[name]["coverage"]["gaps"] = [other]

        def remove(by_id):
            coverage = by_id[name]["coverage"]
            coverage["gaps"] = []
            coverage["status"] = "complete"

        pattern = (
            r"the log-attributions\.2 \(shards 2 to 2\) coverage does not name the shards and "
            r"blocks the plan derives for it"
        )
        for case, edit in (("another part's sentence", replace), ("no sentence", remove)):
            with self.subTest(case=case):
                self.refuses(self.reissued(output, case.replace(" ", "-").replace("'", ""), captures=edit), pattern)

    def test_a_part_capture_that_claims_more_refuses(self):
        output, _plan = self.split()
        name = f"{PART_CLASS}.2"
        named = r"log-attributions\.2 \(shards 2 to 2\)"

        def evidence(by_id):
            by_id[name]["evidence_class"] = "recorded-rpc"

        def hashes(by_id):
            by_id[name]["scope"] = deepcopy(by_id["logs.2"]["scope"])

        def collection(by_id):
            by_id[name]["coverage"]["collections"][0]["name"] = "rows"

        def reference(by_id):
            by_id[name]["source"]["reference"] = "derived offline from the collected interval, epoch-table"

        cases = {
            "evidence class": (evidence, rf"the {named} capture's evidence_class is not the one the plan gives every part"),
            "scope": (hashes, rf"the {named} capture's scope is not the one the plan gives every part"),
            "source": (reference, rf"the {named} capture's source is not the one the plan gives every part"),
            "collection": (
                collection,
                rf"the {named} coverage does not count its 4 rows under /rows as a partial part",
            ),
        }
        for case, (edit, pattern) in cases.items():
            with self.subTest(case=case):
                self.refuses(self.reissued(output, case.replace(" ", "-"), captures=edit), pattern)


class PartSchemaTests(PartCase):
    """The plan schema admits the field, and both new schemas are closed, named, catalogued and met."""

    def schema(self, name):
        return json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))

    def test_the_v2_plan_schema_admits_the_optional_field(self):
        schema = self.schema("interval-plan-v2")
        field = schema["properties"][PARTS_FIELD]
        self.assertEqual(field["const"], PARTS_RULE)
        self.assertNotIn(PARTS_FIELD, schema["required"])
        self.assertEqual(schema["dependentRequired"], {PARTS_FIELD: [SPLIT_FIELD]})
        self.assertFalse(schema["additionalProperties"])
        plan = replanned(self.state, 1)["plan"]
        self.assertEqual(schema_errors(schema, plan), [])
        plan[PARTS_FIELD] = "journal-range"
        self.assertNotEqual(schema_errors(schema, plan), [])
        single = self.schema("interval-plan-v1")
        self.assertNotIn(PARTS_FIELD, single["properties"])
        self.assertFalse(single["additionalProperties"])

    def test_the_v4_receipt_schema_is_closed_named_and_met_by_a_built_receipt(self):
        schema = self.schema("interval-receipt-v4")
        subject = self.schema("interval-receipt-v3")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["format"]["const"], PARTS_RECEIPT_FORMAT)
        self.assertEqual(
            set(schema["required"]),
            set(subject["required"]) - {"log_attributions"} | {"log_attribution_parts"},
        )
        self.assertNotIn("log_attributions", schema["properties"])
        for section in ("epoch", "position", "shard", "reconciliation", "subject_epochs", "first_code"):
            self.assertEqual(schema["$defs"][section], subject["$defs"][section], section)
        entry = schema["$defs"]["part_entry"]
        self.assertFalse(entry["additionalProperties"])
        self.assertEqual(set(entry["required"]), {"component", "first_shard", "last_shard", "rows"})
        pattern = entry["properties"]["component"]["pattern"]
        self.assertRegex(f"{PART_CLASS}.0", pattern)
        self.assertRegex(f"{PART_CLASS}.4095", pattern)
        self.assertNotRegex("logs.0", pattern)
        self.assertNotRegex(f"{PART_CLASS}.01", pattern)
        output, _plan = self.split()
        self.assertEqual(schema_errors(schema, self.document(output, "epoch-table")), [])

    def test_the_part_schema_is_closed_named_and_met_by_every_built_part(self):
        schema = self.schema("interval-log-attributions-v1")
        subject = self.schema("interval-receipt-v3")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["format"]["const"], PART_FORMAT)
        self.assertEqual(set(schema["required"]), {"first_shard", "format", "last_shard", "part", "rows"})
        row = schema["$defs"]["row"]
        self.assertEqual(row, subject["properties"]["log_attributions"]["items"])
        self.assertFalse(row["additionalProperties"])
        output, plan = self.split(state=without_logs(self.state, 1))
        for name in attribution_parts(plan):
            with self.subTest(part=name):
                self.assertEqual(schema_errors(schema, self.document(output, name)), [])

    def test_the_catalogue_and_the_collector_document_name_the_part_rule(self):
        catalogue = (SCHEMAS / "README.md").read_text(encoding="utf-8")
        collector = COLLECTOR_DOCUMENT.read_text(encoding="utf-8")
        for token in (
            "`interval-receipt-v4.schema.json`",
            "`interval-log-attributions-v1.schema.json`",
            f"`{PARTS_RECEIPT_FORMAT}`",
            f"`{PART_FORMAT}`",
            f"`{PARTS_FIELD}`",
            f"`{PARTS_RULE}`",
        ):
            with self.subTest(catalogue=token):
                self.assertIn(token, catalogue)
        for token in (
            f"`{PARTS_FIELD}`",
            f"`{PARTS_RULE}`",
            f"`{PARTS_RECEIPT_FORMAT}`",
            f"`{PART_FORMAT}`",
            "`log-attributions.<k>`",
            f"`{V4_SEMANTICS}`",
        ):
            with self.subTest(collector=token):
                self.assertIn(token, collector)


class V1FixtureTests(PartCase):
    """The Wildcat V1 fixture, whose plan declares no part rule, still builds today's v3 release."""

    VENUE = wildcat_v1.VENUE

    def test_the_v1_fixture_still_builds_its_v3_release_and_checkpoint(self):
        plan = self.plan
        self.assertNotIn(PARTS_FIELD, plan)
        staging = self.staged("today")
        existing.historical_reconciliation(staging)
        checkpoint = (staging / interval.CHECKPOINT_NAME).read_bytes()
        output = self.root / "today"
        release_id = Builder(plan, staging, self.registry, created_at=CREATED_AT).build(output)
        self.assertEqual(
            (release_id, plan_digest(plan), hashlib.sha256(checkpoint).hexdigest()),
            TODAYS_BYTES[("wildcat-v1", None)],
        )
        self.assertEqual(self.document(output, "epoch-table")["format"], SUBJECT_RECEIPT_FORMAT)
        self.assertEqual(check_interval(output)["receipt_semantics"], "v3-subject-positional")


if __name__ == "__main__":
    unittest.main()
