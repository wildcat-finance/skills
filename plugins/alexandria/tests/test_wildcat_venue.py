"""The Wildcat V2 venue: its pinned registry, per-subject epochs and declared gaps.

`WildcatV2ConformanceTests` and `ConstructedStagingTests` are loaded by name:
the Step 1 conformance harness resolves `wildcat-v2-plan-builds-and-checks`
and part of `constructed-staging-declared-in-coverage` against them. Every
other case here runs the constructed multi-subject path in process, over
`fixtures/wildcat-interval-transport.json`, with no socket opened.
"""

import ast
from copy import deepcopy
import functools
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tests import test_usdc_interval as existing
from alexandria_lib import interval, release as release_module, wildcat_registry
from alexandria_lib.canonical import canonical_bytes
from alexandria_lib.errors import AlexandriaError
from alexandria_lib.interval import (
    IMPLEMENTATION_SLOT,
    OPENING_CLASS,
    SUBJECT_RECEIPT_FORMAT,
    UPGRADED_TOPIC,
    validate_attributions,
    validate_epochs,
)
from alexandria_lib.venues import VENUES, wildcat_v1, wildcat_v2
import usdc_interval
from usdc_interval import Builder, Collector, Reconciler, check_interval


PLUGIN = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN.parents[1]
SCRIPT = PLUGIN / "scripts" / "usdc_interval.py"
FIXTURE = PLUGIN / "tests" / "fixtures" / "wildcat-interval-transport.json"
TARGETS = REPO_ROOT / wildcat_registry.TARGETS_PATH
CAPTURE_RECORD = REPO_ROOT / "docs" / "kickoff" / "1374" / "capture.json"
CREATED_AT = "2026-09-20T06:00:00Z"
SECOND_PROVIDER = "second constructed provider, class only"
COLLATERAL_STORAGE = "0xbbb998043a20a26828617769f37dc3980be25ebc"
# The one market, and its hooks instance, deployed inside the fixture interval.
NEW_MARKET = "0x20632bd54e16fcbcd35dcb2c8882a8a8802ad38d"
NEW_HOOKS = "0xc6eb4b199c1a56aa099fd1ede3e4c1fe702c11fb"
DEPLOY_BLOCK = 25895380
EVIDENCE_COMPONENTS = ("boundary-blocks", "logs", "traces", OPENING_CLASS)


def fixture(venue=None):
    """One venue's constructed transport state; V2's when `venue` is omitted.

    The fixture file carries one keyed state per venue that needs the full
    constructed build-and-check round trip, so a change to one venue's state
    never touches another's bytes.
    """
    if not FIXTURE.is_file():
        raise AssertionError(
            f"the Wildcat transport fixture is missing at {FIXTURE}; this suite proves the "
            "venue end to end and must fail rather than skip without it"
        )
    document = json.loads(FIXTURE.read_text(encoding="utf-8"))
    key = venue or wildcat_v2.VENUE
    if key not in document:
        raise AssertionError(f"the Wildcat transport fixture carries no {key} state")
    return document[key]


@functools.lru_cache(maxsize=1)
def _registry_bytes():
    return wildcat_registry.registry_bytes(REPO_ROOT)


def registry():
    """The generated V2 registry, a fresh copy each time so no case edits another's."""
    return json.loads(_registry_bytes())


@functools.lru_cache(maxsize=1)
def _v1_registry_bytes():
    return wildcat_registry.registry_v1_bytes(REPO_ROOT)


def v1_registry():
    """The generated V1 registry, a fresh copy each time so no case edits another's."""
    return json.loads(_v1_registry_bytes())


def epoch_table(receipt):
    """The `{subject: [epoch, ...]}` table a released receipt's subject rows declare."""
    return interval.subject_epoch_table(receipt["epochs"])


def epoch_row(receipt, subject):
    return next(row for row in receipt["epochs"] if row["subject"] == subject)


def v2_row():
    """The V2 row, by iterating the target list; a recursive walk of this file overflows."""
    for row in json.loads(TARGETS.read_text(encoding="utf-8"))["targets"]:
        if row.get("id") == wildcat_registry.ROW_ID:
            return row
    raise AssertionError("the V2 row is missing from the registry record")


def v1_row():
    """The V1 row, by iterating the target list; a recursive walk of this file overflows."""
    for row in json.loads(TARGETS.read_text(encoding="utf-8"))["targets"]:
        if row.get("id") == wildcat_registry.V1_ROW_ID:
            return row
    raise AssertionError("the V1 row is missing from the registry record")


class WildcatTransport(existing.FixtureTransport):
    """The constructed chain. A storage read is a failure, not an answer.

    `case` names one of the fixture's `first_code_cases`: the block from
    which a subject's code read answers with code, and empty before it.
    """

    def __init__(self, state, *, case=None, **kwargs):
        super().__init__(state, **kwargs)
        self.code_from = dict(state["first_code_cases"][case]) if case else {}

    def code(self, address, number):
        if number < self.code_from.get(address, 0):
            return "0x"
        return super().code(address, number)

    def request(self, payload, label):
        method = json.loads(payload)["method"]
        if method == "eth_getStorageAt":
            raise AssertionError("the immutable-code epoch model issued a storage read")
        return super().request(payload, label)


def schema_errors(schema, value, root=None, path="$"):
    """The subset of JSON Schema the interval schemas use, checked with the standard library."""
    root = root or schema
    if "$ref" in schema:
        target = root
        for token in schema["$ref"].lstrip("#/").split("/"):
            target = target[token]
        return schema_errors(target, value, root, path)
    errors = []
    if "oneOf" in schema:
        matched = sum(1 for option in schema["oneOf"] if not schema_errors(option, value, root, path))
        if matched != 1:
            errors.append(f"{path}: matches {matched} of oneOf")
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: is not {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: is not one of {schema['enum']!r}")
    kinds = schema.get("type")
    if kinds is not None:
        names = {
            "array": list, "integer": int, "null": type(None), "object": dict, "string": str,
        }
        allowed = tuple(names[kind] for kind in ([kinds] if isinstance(kinds, str) else kinds))
        if not isinstance(value, allowed) or (isinstance(value, bool) and bool not in allowed):
            return errors + [f"{path}: is not of type {kinds!r}"]
    if isinstance(value, str):
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"{path}: does not match {schema['pattern']}")
        if len(value) > schema.get("maxLength", len(value)) or len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: has a length outside its bounds")
    if isinstance(value, int) and not isinstance(value, bool):
        if value < schema.get("minimum", value) or value > schema.get("maximum", value):
            errors.append(f"{path}: is outside its bounds")
    if isinstance(value, list):
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", len(value)):
            errors.append(f"{path}: has an item count outside its bounds")
        for index, item in enumerate(value):
            errors.extend(schema_errors(schema.get("items", {}), item, root, f"{path}[{index}]"))
    if isinstance(value, dict):
        if not schema.get("minProperties", 0) <= len(value) <= schema.get("maxProperties", len(value)):
            errors.append(f"{path}: has a property count outside its bounds")
        for name in schema.get("required", []):
            if name not in value:
                errors.append(f"{path}: lacks {name}")
        for name, item in value.items():
            if name in schema.get("properties", {}):
                errors.extend(schema_errors(schema["properties"][name], item, root, f"{path}.{name}"))
                continue
            patterns = [
                sub for pattern, sub in schema.get("patternProperties", {}).items()
                if re.search(pattern, name)
            ]
            for sub in patterns:
                errors.extend(schema_errors(sub, item, root, f"{path}.{name}"))
            if not patterns and schema.get("additionalProperties") is False:
                errors.append(f"{path}: carries the undeclared property {name}")
    return errors


class WildcatCase(unittest.TestCase):
    """Collect, reconcile, build and check over the constructed fixture.

    `VENUE` picks which venue's keyed fixture state and registry this case
    runs against; V2's is the default every case had before V1 existed, so a
    subclass that does not name a venue keeps running exactly as it did.
    """

    VENUE = wildcat_v2.VENUE

    def setUp(self):
        self.state = fixture(self.VENUE)
        self.plan = self.state["plan"]
        self.registry = registry() if self.VENUE == wildcat_v2.VENUE else v1_registry()
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def scratch(self, name):
        root = self.root / name
        root.mkdir()
        return root

    def staged(self, name="release", state=None, second=None):
        state = state or self.state
        staging = self.scratch(f"{name}-staging")
        self.transport = WildcatTransport(state)
        Collector(state["plan"], staging, self.transport, registry=self.registry).collect()
        Reconciler(
            state["plan"], staging, second or WildcatTransport(state), SECOND_PROVIDER,
            registry=self.registry,
        ).reconcile()
        return staging

    def released(self, name="release", state=None):
        state = state or self.state
        staging = self.staged(name, state)
        output = self.root / name
        release_id = Builder(
            state["plan"], staging, self.registry, created_at=CREATED_AT
        ).build(output)
        return output, release_id

    def captures(self, output):
        manifest = json.loads((output / "manifest.json").read_text())
        return {capture["id"]: capture for capture in manifest["captures"]}

    def rewrite(self, output, name, edit):
        path = existing.component_path(output, name)
        document = json.loads(path.read_text())
        edit(document)
        path.write_bytes(canonical_bytes(document))

    def check_without_verify(self, output):
        release_id = json.loads((output / "manifest.json").read_text())["release_id"]
        with mock.patch.object(usdc_interval, "verify", return_value=release_id):
            return check_interval(output)


class RegistryGeneratorTests(unittest.TestCase):
    def test_the_generated_registry_matches_its_digest_constant(self):
        document = wildcat_registry.generate_v2_registry(REPO_ROOT)
        self.assertEqual(
            hashlib.sha256(canonical_bytes(document)).hexdigest(),
            wildcat_registry.WILDCAT_V2_REGISTRY_SHA256,
        )
        wildcat_registry.validate_registry(document)
        self.assertIs(wildcat_v2.validate_registry, wildcat_registry.validate_registry)

    def test_the_digest_constant_is_written_in_the_generator_and_nowhere_else(self):
        literal = wildcat_registry.WILDCAT_V2_REGISTRY_SHA256
        holders = sorted(
            str(path.relative_to(PLUGIN))
            for path in PLUGIN.rglob("*")
            if path.is_file() and path.suffix in (".py", ".json", ".md")
            and literal in path.read_text(encoding="utf-8", errors="replace")
        )
        self.assertEqual(holders, ["scripts/alexandria_lib/wildcat_registry.py"])
        self.assertNotIn(literal, json.dumps(fixture()))

    def test_every_pinned_source_record_is_the_file_on_disk(self):
        for path, sha256, size in wildcat_registry.SOURCE_RECORDS:
            if path == wildcat_registry.TARGETS_PATH:
                continue
            with self.subTest(path=path):
                data = (REPO_ROOT / path).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), sha256)
                self.assertEqual(len(data), size)
        targets = json.loads((REPO_ROOT / wildcat_registry.TARGETS_PATH).read_bytes())
        rows = {row["id"]: row for row in targets["targets"]}
        for row_id, row_sha256 in wildcat_registry.ROW_PINS:
            with self.subTest(row=row_id):
                self.assertEqual(hashlib.sha256(canonical_bytes(rows[row_id])).hexdigest(), row_sha256)

    def test_an_edit_to_another_venue_row_leaves_both_registries_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_sources(directory)
            target = root / wildcat_registry.TARGETS_PATH
            document = json.loads(target.read_bytes())
            other = next(row for row in document["targets"] if row["id"] == "aave-v3")
            other["label"] = other["label"] + " (edited)"
            target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
            self.assertEqual(canonical_bytes(wildcat_registry.generate_v2_registry(root)), _registry_bytes())
            self.assertEqual(
                canonical_bytes(wildcat_registry.generate_v1_registry(root)),
                wildcat_registry.registry_v1_bytes(REPO_ROOT),
            )

    def test_a_changed_wildcat_row_refuses_by_name(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_sources(directory)
            target = root / wildcat_registry.TARGETS_PATH
            for row_id, _row_sha256 in wildcat_registry.ROW_PINS:
                with self.subTest(row=row_id):
                    original = target.read_bytes()
                    document = json.loads(original)
                    row = next(row for row in document["targets"] if row["id"] == row_id)
                    row["label"] = row["label"] + " (edited)"
                    target.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
                    with self.assertRaisesRegex(AlexandriaError, f"row {row_id} does not match its pin"):
                        wildcat_registry.generate_v2_registry(root)
                    with self.assertRaisesRegex(AlexandriaError, f"row {row_id} does not match its pin"):
                        wildcat_registry.generate_v1_registry(root)
                    target.write_bytes(original)

    def copied_sources(self, directory):
        for path, _sha256, _size in wildcat_registry.SOURCE_RECORDS:
            target = Path(directory) / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(REPO_ROOT / path, target)
        return Path(directory)

    def test_a_changed_source_record_refuses(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.copied_sources(directory)
            # The untouched copy generates, so the refusals below are the change.
            self.assertEqual(
                canonical_bytes(wildcat_registry.generate_v2_registry(root)), _registry_bytes()
            )
            for path, _sha256, _size in wildcat_registry.SOURCE_RECORDS:
                with self.subTest(path=path):
                    target = root / path
                    original = target.read_bytes()
                    # One address digit moved; the byte count is unchanged.
                    target.write_bytes(original.replace(b"0xfeb516d9", b"0xfeb516d8", 1))
                    self.assertNotEqual(target.read_bytes(), original)
                    with self.assertRaisesRegex(AlexandriaError, "does not match its pin"):
                        wildcat_registry.generate_v2_registry(root)
                    target.write_bytes(original)

    def test_the_registry_covers_all_137_subjects_by_role(self):
        document = registry()
        counts = {}
        for entry in document["entries"]:
            counts[entry["role"]] = counts.get(entry["role"], 0) + 1
        self.assertEqual(len(document["entries"]), 137)
        self.assertEqual(
            {role: count for role, count in counts.items() if count > 1},
            {"market": 80, "hooks-instance": 42, "hooks-template": 3, "lens": 2},
        )
        self.assertEqual(
            sorted(role for role, count in counts.items() if count == 1),
            sorted([
                "registry", "sanctions-sentinel", "factory", "market-init-code-storage",
                "wrapper-factory", "fee-recipient", "collateral-factory",
                "collateral-init-code-storage", "collateral-lens", "role-provider",
            ]),
        )
        self.assertEqual(
            [address for address in (e["address"] for e in document["entries"])],
            [contract["address"] for contract in v2_row()["deployment"]["contracts"]],
        )

    def test_the_subject_addresses_reproduce_the_rows_recorded_list_digests(self):
        row = v2_row()
        instances = row["deployment"]["instances"]
        document = registry()

        def compact(addresses):
            body = json.dumps(sorted(a.lower() for a in addresses), separators=(",", ":"))
            return hashlib.sha256(body.encode()).hexdigest()

        lists = {
            "v2_markets_sha256": [e["address"] for e in document["entries"] if e["role"] == "market"],
            "hooks_instances_sha256": [
                e["address"] for e in document["entries"] if e["role"] == "hooks-instance"
            ],
            "registered_markets_sha256": document["registered_markets"],
        }
        self.assertEqual([len(lists[name]) for name in lists], [80, 42, 87])
        recorded = {item["name"]: item for item in document["list_digests"]}
        self.assertEqual(list(recorded), list(lists))
        for name, addresses in lists.items():
            with self.subTest(digest=name):
                self.assertEqual(compact(addresses), instances[name])
                self.assertEqual(recorded[name]["sha256"], instances[name])
                self.assertEqual(recorded[name]["canonical_form"], "compact-sorted-json")
                self.assertEqual(recorded[name]["count"], len(addresses))
        # The form is the row's own declaration, mapped rather than assumed.
        self.assertEqual(
            wildcat_registry.DECLARED_METHODS[instances["sha256_method"]], "compact-sorted-json"
        )
        # The other estate's form does not reproduce these digests, so a
        # generator that assumed one form for both rows would be caught.
        joined = "\n".join(sorted(lists["v2_markets_sha256"])) + "\n"
        self.assertNotEqual(
            hashlib.sha256(joined.encode()).hexdigest(), instances["v2_markets_sha256"]
        )

    def test_an_undeclared_digest_method_or_form_refuses(self):
        with mock.patch.dict(wildcat_registry.DECLARED_METHODS, clear=True):
            with self.assertRaisesRegex(AlexandriaError, "digest method"):
                wildcat_registry.generate_v2_registry(REPO_ROOT)
        with self.assertRaisesRegex(AlexandriaError, "canonical form"):
            wildcat_registry.list_digest(["0x" + "11" * 20], "newline-joined")

    def test_a_recorded_form_that_does_not_reproduce_its_digest_refuses(self):
        document = registry()
        document["list_digests"][0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(AlexandriaError, "does not reproduce"):
            wildcat_registry.validate_registry(document)

    def test_the_validator_refuses_anything_but_the_pinned_document(self):
        edited = registry()
        edited["entries"][5]["deployment_block"] += 1
        with self.assertRaisesRegex(AlexandriaError, "do not match the pinned registry"):
            wildcat_registry.validate_registry(edited)
        with self.assertRaisesRegex(AlexandriaError, "format is unknown"):
            wildcat_registry.validate_registry(existing.registry())
        # The disagreement is refused from either side: each venue's validator
        # refuses the other venue's registry.
        with self.assertRaisesRegex(AlexandriaError, "Compound registry"):
            VENUES["compound-v3"].validate_registry(registry())
        for specimen in (None, [], {"format": wildcat_registry.REGISTRY_FORMAT}):
            with self.subTest(specimen=specimen):
                with self.assertRaises(AlexandriaError):
                    wildcat_registry.validate_registry(specimen)

    def test_only_the_collateral_init_code_storage_lacks_a_creation_block(self):
        unblocked = [e["address"] for e in registry()["entries"] if e["deployment_block"] is None]
        self.assertEqual(unblocked, [COLLATERAL_STORAGE])
        self.assertEqual(wildcat_registry.NO_CREATION_BLOCK, (COLLATERAL_STORAGE,))
        edited = registry()
        next(e for e in edited["entries"] if e["address"] == COLLATERAL_STORAGE).update(
            deployment_block=1, deployment_block_source="contract-record"
        )
        with self.assertRaisesRegex(AlexandriaError, "not the reviewed set"):
            wildcat_registry.validate_registry(edited)

    def test_the_generator_runs_no_subprocess(self):
        tree = ast.parse(Path(wildcat_registry.__file__).read_text(encoding="utf-8"))
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & {"subprocess", "os", "socket", "urllib"})


class EpochModelTests(WildcatCase):
    def epochs(self, output):
        return epoch_table(existing.component_document(output, "epoch-table"))

    def test_every_subject_has_one_epoch_that_tiles_its_own_extent(self):
        output, _release_id = self.released()
        epochs = self.epochs(output)
        self.assertEqual(list(epochs), sorted(self.plan["subjects"]))
        codes = {
            record["address"]: record["code"]
            for record in existing.component_document(output, "implementation-code")["records"]
        }
        entries = wildcat_registry.subject_entries(self.registry)
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        for subject, table in epochs.items():
            with self.subTest(subject=subject):
                self.assertEqual(len(table), 1)
                epoch = table[0]
                self.assertIsNone(epoch["upgrade"])
                self.assertEqual(epoch["implementation"], subject)
                self.assertEqual(epoch["proxy"], subject)
                first = max(start, entries[subject]["deployment_block"] or start)
                self.assertEqual(epoch["start_block"], str(first))
                self.assertEqual(epoch["end_block"], str(end))
                self.assertEqual(
                    epoch["implementation_code_sha256"],
                    hashlib.sha256(bytes.fromhex(codes[subject][2:])).hexdigest(),
                )
        validate_epochs(epochs, start, end)

    def test_a_table_that_does_not_tile_refuses(self):
        output, _release_id = self.released()
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        mutations = {
            "stops short": lambda epoch: epoch.update(
                end_block=str(end - 1),
                end_position={"block_number": str(end), "log_index": None, "transaction_index": None},
            ),
            "opens after its first block": lambda epoch: epoch.update(
                start_position={
                    "block_number": epoch["start_block"], "log_index": 0, "transaction_index": 0,
                },
            ),
            "claims an upgrade": lambda epoch: epoch.update(upgrade={
                "block_number": epoch["start_block"], "log_index": 0, "transaction_index": 0,
                "transaction_hash": "0x" + "11" * 32,
            }),
        }
        path = existing.component_path(output, "epoch-table")
        released = path.read_bytes()
        validate_epochs(self.epochs(output), start, end)
        for label, mutate in mutations.items():
            with self.subTest(mutation=label):
                # Each mutation starts from the released table, never from
                # the one before it, so each refusal is its own.
                path.write_bytes(released)
                epochs = self.epochs(output)
                mutate(epochs[NEW_MARKET][0])
                with self.assertRaises(AlexandriaError):
                    validate_epochs(epochs, start, end)
                self.rewrite(
                    output, "epoch-table",
                    lambda receipt: receipt.__setitem__("epochs", interval.subject_epoch_rows(epochs)),
                )
                with self.assertRaises(AlexandriaError):
                    self.check_without_verify(output)
        path.write_bytes(released)
        self.check_without_verify(output)
        empty = self.epochs(output)
        empty[NEW_MARKET] = []
        with self.assertRaises(AlexandriaError):
            validate_epochs(empty, start, end)

    def test_a_subject_deployed_inside_the_interval_starts_at_its_own_block(self):
        output, _release_id = self.released()
        epochs = self.epochs(output)
        for subject in (NEW_MARKET, NEW_HOOKS):
            self.assertEqual(epochs[subject][0]["start_block"], str(DEPLOY_BLOCK))
            self.assertEqual(
                epochs[subject][0]["start_position"],
                {"block_number": str(DEPLOY_BLOCK), "log_index": None, "transaction_index": None},
            )
            self.assertEqual(epochs[subject][0]["start_hash"], self.state["blocks"][str(DEPLOY_BLOCK)])
        self.assertNotEqual(str(DEPLOY_BLOCK), self.plan["interval"]["start"])
        # The code digest is of the read made at that block, not at the start.
        reads = [
            json.loads(entry["request"])
            for entry in existing.opening_entries(self.root / "release-staging")
        ]
        code_reads = {r["params"][0]: r["params"][1] for r in reads if r["method"] == "eth_getCode"}
        self.assertEqual(code_reads[NEW_MARKET], hex(DEPLOY_BLOCK))
        self.assertEqual(code_reads[COLLATERAL_STORAGE], hex(int(self.plan["interval"]["start"])))
        headers = [int(r["params"][0], 16) for r in reads if r["method"] == "eth_getBlockByNumber"]
        self.assertEqual(headers, [int(self.plan["interval"]["start"]), DEPLOY_BLOCK])

    def test_a_log_before_its_subjects_deployment_block_refuses(self):
        state = deepcopy(self.state)
        record = deepcopy(state["logs"]["3"][0])
        record.update(
            blockNumber=hex(25895345), blockHash=state["blocks"]["25895345"], logIndex=hex(13),
            transactionIndex=hex(3), transactionHash=state["logs"]["0"][0]["transactionHash"],
        )
        state["logs"]["0"].append(record)
        staging = self.scratch("early-log")
        with self.assertRaisesRegex(AlexandriaError, "no positional epoch owner"):
            Collector(state["plan"], staging, WildcatTransport(state), registry=self.registry).collect()
            Reconciler(
                state["plan"], staging, WildcatTransport(state), SECOND_PROVIDER,
                registry=self.registry,
            ).reconcile()
            Builder(state["plan"], staging, self.registry, created_at=CREATED_AT).build(
                self.root / "early-log-release"
            )

    def test_the_collateral_storage_starts_at_the_interval_start_with_a_declared_gap(self):
        output, _release_id = self.released()
        epoch = self.epochs(output)[COLLATERAL_STORAGE][0]
        self.assertEqual(epoch["start_block"], self.plan["interval"]["start"])
        captures = self.captures(output)
        for name in EVIDENCE_COMPONENTS + ("registry",):
            with self.subTest(component=name):
                named = [
                    gap for gap in captures[name]["coverage"]["gaps"]
                    if COLLATERAL_STORAGE in gap and "no creation block" in gap
                ]
                self.assertEqual(len(named), 1)
                self.assertIn("deployment block is not established", named[0])

    def test_a_subject_deployed_after_the_interval_end_has_no_epoch_and_is_named(self):
        state = deepcopy(self.state)
        plan = state["plan"]
        plan["interval"] = {"start": "25336200", "end": "25336279"}
        plan["shards"] = interval.plan_shards(25336200, 25336279, plan["shard_width"])
        state["logs"] = {str(index): [] for index in range(4)}
        state["traces"] = {str(index): [] for index in range(4)}
        output, _release_id = self.released("earlier", state)
        epochs = epoch_table(existing.component_document(output, "epoch-table"))
        self.assertNotIn(NEW_MARKET, epochs)
        self.assertNotIn(NEW_HOOKS, epochs)
        self.assertEqual(len(epochs), 135)
        self.assertEqual(check_interval(output)["epochs"], 135)
        for name in EVIDENCE_COMPONENTS:
            gaps = self.captures(output)[name]["coverage"]["gaps"]
            for subject in (NEW_MARKET, NEW_HOOKS):
                self.assertTrue(any(subject in gap and "outside the interval" in gap for gap in gaps))

    def test_the_epoch_model_infers_no_implementation_it_was_not_given(self):
        start = int(self.plan["interval"]["start"])
        self.assertNotIn(COLLATERAL_STORAGE, wildcat_v2.first_blocks(self.plan, self.registry))
        blocks = wildcat_v2.first_blocks(self.plan, self.registry, {COLLATERAL_STORAGE: start})
        hashes = {block: "0x" + f"{block:064x}" for block in set(blocks.values())}
        hashes[int(self.plan["interval"]["end"])] = "0x" + "ee" * 32
        codes = {subject: self.state["code"][subject] for subject in blocks}
        arguments = dict(
            chain=self.plan["chain"], deployment=self.plan["deployment"],
            interval=self.plan["interval"], first_blocks=blocks,
        )
        self.assertEqual(
            len(wildcat_v2.derive_epochs(code_reads=codes, block_hashes=hashes, **arguments)), 137
        )
        without_code = dict(codes)
        del without_code[NEW_MARKET]
        with self.assertRaisesRegex(AlexandriaError, "no implementation is inferred"):
            wildcat_v2.derive_epochs(code_reads=without_code, block_hashes=hashes, **arguments)
        without_header = dict(hashes)
        del without_header[DEPLOY_BLOCK]
        with self.assertRaisesRegex(AlexandriaError, "no preserved block hash"):
            wildcat_v2.derive_epochs(code_reads=codes, block_hashes=without_header, **arguments)
        with self.assertRaisesRegex(AlexandriaError, "empty runtime code"):
            wildcat_v2.derive_epochs(
                code_reads=dict(codes, **{NEW_MARKET: "0x"}), block_hashes=hashes, **arguments
            )

    def test_the_venue_module_never_names_the_slot_or_the_upgrade_topic(self):
        source = Path(wildcat_v2.__file__).read_text(encoding="utf-8")
        names = {
            node.id if isinstance(node, ast.Name) else node.attr
            for node in ast.walk(ast.parse(source))
            if isinstance(node, (ast.Name, ast.Attribute))
        }
        imported = {
            alias.name for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom) for alias in node.names
        }
        for constant, value in (
            ("IMPLEMENTATION_SLOT", IMPLEMENTATION_SLOT), ("UPGRADED_TOPIC", UPGRADED_TOPIC),
        ):
            with self.subTest(constant=constant):
                self.assertNotIn(constant, names | imported)
                self.assertNotIn(value, source)
                self.assertFalse(hasattr(wildcat_v2, constant))

    def test_no_storage_read_is_issued_and_no_log_is_read_as_an_upgrade(self):
        state = deepcopy(self.state)
        # A subject's log carrying the ERC-1967 topic, in the interval's first
        # block: the single-proxy model refuses exactly this as an upgrade
        # with no preceding implementation evidence.
        announcement = deepcopy(state["logs"]["0"][0])
        start = int(state["plan"]["interval"]["start"])
        announcement.update(
            blockNumber=hex(start), blockHash=state["blocks"][str(start)], logIndex=hex(1),
            transactionIndex=hex(0), transactionHash="0x" + "77" * 32,
            topics=[UPGRADED_TOPIC, "0x" + "0" * 24 + "42" * 20],
        )
        state["logs"]["0"].insert(0, announcement)
        with self.assertRaises(AlexandriaError):
            interval.proxy_log_positions(
                [announcement], state["plan"]["subjects"], state["plan"]["interval"]
            )
        output, _release_id = self.released("announced", state)
        self.assertNotIn("eth_getStorageAt", {method for method, _label in self.transport.calls})
        rows = existing.component_document(output, "epoch-table")["log_attributions"]
        self.assertEqual({row["kind"] for row in rows}, {"proxy-log"})
        self.assertEqual(len(rows), 10)
        self.assertEqual(check_interval(output)["epochs"], 137)


class WildcatV2ConformanceTests(WildcatCase):
    """The two assertions `wildcat-v2-plan-builds-and-checks` resolves, through the CLI."""

    def command(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True, text=True, check=False, timeout=300,
        )

    def built(self):
        staging = self.staged("cli")
        plan_path = self.root / "plan.json"
        registry_path = self.root / "registry.json"
        plan_path.write_bytes(canonical_bytes(self.plan))
        registry_path.write_bytes(_registry_bytes())
        output = self.root / "cli-release"
        result = self.command(
            "build", "--plan", str(plan_path), "--staging", str(staging),
            "--registry", str(registry_path), "--created-at", CREATED_AT,
            "--output", str(output),
        )
        return result, output

    def test_wildcat_v2_plan_builds_a_release(self):
        self.assertEqual(len(self.plan["subjects"]), 137)
        self.assertEqual(self.plan["venue"], "wildcat-v2")
        result, output = self.built()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"\Asha256:[0-9a-f]{64}\n\Z")
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(manifest["release_id"], result.stdout.strip())
        self.assertEqual(
            {component["name"] for component in manifest["components"]},
            set(usdc_interval.FIXED_COMPONENTS) | set(EVIDENCE_COMPONENTS),
        )
        self.assertEqual({capture["venue"] for capture in manifest["captures"]}, {"wildcat-v2"})
        receipt = existing.component_document(output, "epoch-table")
        self.assertEqual(receipt["format"], SUBJECT_RECEIPT_FORMAT)
        self.assertEqual(len(receipt["epochs"]), 137)

    def test_wildcat_v2_release_checks(self):
        result, output = self.built()
        self.assertEqual(result.returncode, 0, result.stderr)
        checked = self.command("check", str(output))
        self.assertEqual(checked.returncode, 0, checked.stderr)
        summary = json.loads(checked.stdout)
        self.assertEqual(summary["release_id"], result.stdout.strip())
        self.assertEqual(summary["epochs"], 137)
        self.assertEqual(summary["receipt_semantics"], "v3-subject-positional")
        self.assertEqual(summary["reconciliation"], "agreed")
        self.assertEqual(summary["shard_statuses"], {"complete": 4})
        self.assertEqual(set(summary["implementations"]), set(self.plan["subjects"]))
        # The same check refuses the same bytes once one of them moves.
        path = existing.component_path(output, "logs")
        path.write_bytes(path.read_bytes().replace(b"abab", b"abac", 1))
        refused = self.command("check", str(output))
        self.assertEqual(refused.returncode, 1)
        self.assertTrue(refused.stderr.startswith("usdc-interval: "))


class WildcatV1ConformanceTests(WildcatCase):
    """The four assertions `wildcat-v1-plan-builds-and-checks` and `v1-source-gap-declared` resolve.

    Unlike Wildcat V2, every one of this venue's 16 declared subjects carries
    an established source commit, so the release declares no source-identity
    coverage gap; what it does carry is the row's own checkout ambiguity,
    recorded as a caveat, and a real, separate deployment-block gap on the 12
    of 16 subjects the row records no creation block for.
    """

    VENUE = wildcat_v1.VENUE

    def command(self, *arguments):
        return subprocess.run(
            [sys.executable, str(SCRIPT), *arguments],
            capture_output=True, text=True, check=False, timeout=300,
        )

    def built(self):
        staging = self.staged("cli")
        plan_path = self.root / "plan.json"
        registry_path = self.root / "registry.json"
        plan_path.write_bytes(canonical_bytes(self.plan))
        registry_path.write_bytes(_v1_registry_bytes())
        output = self.root / "cli-release"
        result = self.command(
            "build", "--plan", str(plan_path), "--staging", str(staging),
            "--registry", str(registry_path), "--created-at", CREATED_AT,
            "--output", str(output),
        )
        return result, output

    def test_wildcat_v1_plan_builds_a_release(self):
        self.assertEqual(len(self.plan["subjects"]), 16)
        self.assertEqual(self.plan["venue"], "wildcat-v1")
        result, output = self.built()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"\Asha256:[0-9a-f]{64}\n\Z")
        manifest = json.loads((output / "manifest.json").read_text())
        self.assertEqual(manifest["release_id"], result.stdout.strip())
        self.assertEqual(
            {component["name"] for component in manifest["components"]},
            set(usdc_interval.FIXED_COMPONENTS) | set(EVIDENCE_COMPONENTS),
        )
        self.assertEqual({capture["venue"] for capture in manifest["captures"]}, {"wildcat-v1"})
        receipt = existing.component_document(output, "epoch-table")
        self.assertEqual(receipt["format"], SUBJECT_RECEIPT_FORMAT)
        # The factory and MarketLens are declared but deployed after this
        # fixture's interval end, so 14 of the 16 declared subjects carry an
        # epoch; the other two appear in the registry capture's own gaps as
        # "deployed after the interval end", not as missing here.
        self.assertEqual(len(receipt["epochs"]), 14)

    def test_wildcat_v1_release_checks(self):
        result, output = self.built()
        self.assertEqual(result.returncode, 0, result.stderr)
        checked = self.command("check", str(output))
        self.assertEqual(checked.returncode, 0, checked.stderr)
        summary = json.loads(checked.stdout)
        self.assertEqual(summary["release_id"], result.stdout.strip())
        self.assertEqual(summary["epochs"], 14)
        self.assertEqual(summary["receipt_semantics"], "v3-subject-positional")
        self.assertEqual(summary["reconciliation"], "agreed")
        self.assertEqual(summary["shard_statuses"], {"complete": 2})
        # The same check refuses the same bytes once one of them moves.
        path = existing.component_path(output, "registry")
        data = path.read_bytes()
        path.write_bytes(data[:-1] + bytes([data[-1] ^ 0x01]))
        refused = self.command("check", str(output))
        self.assertEqual(refused.returncode, 1)
        self.assertTrue(refused.stderr.startswith("usdc-interval: "))

    def test_unreproduced_source_subjects_carry_a_declared_gap(self):
        document = v1_registry()
        # The real row establishes a source commit for every one of its 16
        # subjects, so the real release declares no gap of this kind.
        self.assertEqual([e["address"] for e in document["entries"] if not e["source_commit"]], [])
        self.assertFalse(any("establish no source commit" in gap for gap in wildcat_v1.gaps(document)))
        # The mechanism that would declare one still fires against a
        # constructed row with an absent source commit.
        fake = deepcopy(document)
        target = fake["entries"][0]["address"]
        fake["entries"][0] = dict(fake["entries"][0], source_commit=None)
        matches = [
            gap for gap in wildcat_v1.gaps(fake)
            if "establish no source commit" in gap and target in gap
        ]
        self.assertEqual(len(matches), 1)

    def test_v1_release_claims_no_source_identity_it_cannot_support(self):
        row = v1_row()
        contracts_by_address = {c["address"]: c for c in row["deployment"]["contracts"]}
        document = v1_registry()
        self.assertEqual(len(document["entries"]), 16)
        for entry in document["entries"]:
            raw = contracts_by_address[entry["address"]]
            self.assertEqual(entry["source_commit"], raw["code_match"]["source_commit"])
        source_meta = row["source"]
        self.assertEqual(document["source"]["commit"], source_meta["commit"])
        self.assertEqual(
            sorted(document["source"]["equivalent_commits"]), sorted(source_meta["equivalent_commits"])
        )
        self.assertEqual(len(document["source"]["equivalent_commits"]), 4)
        self.assertEqual(document["source"]["equivalence_note"], source_meta["equivalence_note"])
        by_commit = {}
        for entry in document["entries"]:
            by_commit.setdefault(entry["source_commit"], []).append(entry["address"])
        self.assertEqual(len(by_commit.get("da74452aa7d1a0f024d99efd22cc6d950a8116b7", [])), 14)
        self.assertEqual(len(by_commit.get("6164ddd4c75ef6da2181e5623b99795b9829e31c", [])), 1)
        self.assertEqual(len(by_commit.get("488b30d08c73a93be3e4bf99128c774997411d3a", [])), 1)
        # A release that asserts one of the four equivalent commits as a
        # subject's own source commit, rather than the row's recorded one,
        # refuses; the row's own checkout among the five cannot be determined.
        fake = deepcopy(document)
        equivalent = fake["source"]["equivalent_commits"][0]
        index = next(
            i for i, e in enumerate(fake["entries"]) if e["source_commit"] == fake["source"]["commit"]
        )
        fake["entries"][index] = dict(fake["entries"][index], source_commit=equivalent)
        with self.assertRaisesRegex(AlexandriaError, "asserts one of the row's equivalent commits"):
            wildcat_registry._validate_v1_shape(fake)


class V1RegistryGeneratorTests(unittest.TestCase):
    def test_the_generated_v1_registry_matches_its_digest_constant(self):
        document = wildcat_registry.generate_v1_registry(REPO_ROOT)
        self.assertEqual(
            hashlib.sha256(canonical_bytes(document)).hexdigest(),
            wildcat_registry.WILDCAT_V1_REGISTRY_SHA256,
        )

    def test_the_v1_registry_covers_all_16_subjects_by_role(self):
        document = v1_registry()
        counts = {}
        for entry in document["entries"]:
            counts[entry["role"]] = counts.get(entry["role"], 0) + 1
        self.assertEqual(counts, wildcat_registry.V1_EXPECTED_ROLE_COUNTS)
        self.assertEqual(len(document["entries"]), 16)

    def test_the_v1_subject_set_has_exactly_16_members_from_the_three_declared_lists(self):
        row = v1_row()
        deployment = row["deployment"]
        contract_addresses = {c["address"] for c in deployment["contracts"]}
        recorded = {
            c["address"] for c in deployment["contracts"] if c["role"] not in ("controller", "market")
        }
        controllers = set(deployment["instances"]["controllers"])
        markets = set(deployment["instances"]["markets"])
        self.assertEqual(len(recorded), 6)
        self.assertEqual(len(controllers), 3)
        self.assertEqual(len(markets), 7)
        derived = recorded | controllers | markets
        self.assertEqual(len(derived), 16)
        self.assertEqual(derived, contract_addresses)
        self.assertEqual(contract_addresses, set(wildcat_registry.subject_entries(v1_registry())))

    def test_a_set_built_from_the_arch_controllers_registered_count_differs_and_is_refused(self):
        # docs/kickoff/1359/evidence/ethereum-mainnet.json: the arch
        # controller's own getRegisteredControllersCount is 4 and includes
        # the V2 HooksFactory; the controller factory's own deployed count,
        # which the row and this registry use, is 3.
        estate = json.loads(
            (REPO_ROOT / "docs" / "kickoff" / "1359" / "evidence" / "ethereum-mainnet.json")
            .read_text(encoding="utf-8")
        )
        registered_controllers = {
            address.lower() for address in estate["arch_controller"]["getRegisteredControllers"]
        }
        deployed_controllers = {
            address.lower() for address in estate["v1_controller_factory"]["getDeployedControllers"]
        }
        self.assertEqual(estate["arch_controller"]["getRegisteredControllersCount"], 4)
        self.assertEqual(estate["v1_controller_factory"]["getDeployedControllersCount"], 3)
        self.assertEqual(len(registered_controllers), 4)
        self.assertEqual(len(deployed_controllers), 3)
        self.assertNotEqual(registered_controllers, deployed_controllers)
        v2_hooks_factory = "0xdd7dd3b5076cf89440d05585ff56d246386207be"
        self.assertIn(v2_hooks_factory, registered_controllers)
        self.assertNotIn(v2_hooks_factory, deployed_controllers)
        controller_entries = {
            entry["address"] for entry in v1_registry()["entries"] if entry["role"] == "controller"
        }
        self.assertEqual(controller_entries, deployed_controllers)
        self.assertNotEqual(controller_entries, registered_controllers)

    def test_the_v1_market_list_digest_reproduces_under_the_newline_joined_form(self):
        row = v1_row()
        markets = row["deployment"]["instances"]["markets"]
        expected = row["deployment"]["instances"]["markets_sha256"]
        recomputed = hashlib.sha256(
            ("\n".join(sorted(address.lower() for address in markets)) + "\n").encode("utf-8")
        ).hexdigest()
        self.assertEqual(recomputed, expected)
        digest_entry = v1_registry()["list_digests"][0]
        self.assertEqual(digest_entry["sha256"], expected)
        self.assertEqual(digest_entry["canonical_form"], wildcat_registry.NEWLINE_JOINED_TRAILING)
        # Not V2's compact-JSON form.
        compact = hashlib.sha256(
            json.dumps(sorted(address.lower() for address in markets), separators=(",", ":"))
            .encode("utf-8")
        ).hexdigest()
        self.assertNotEqual(compact, expected)

    def test_the_deployment_block_split_is_4_carrying_one_against_12_that_do_not(self):
        row = v1_row()
        contracts = row["deployment"]["contracts"]
        with_block = [c for c in contracts if c.get("code_match", {}).get("deployment_block") is not None]
        without_block = [c for c in contracts if c.get("code_match", {}).get("deployment_block") is None]
        # The runbook's Exit and Tests text disagree with each other here (2
        # vs. 12-against-2, which leaves 2 of 16 unaccounted for); re-reading
        # the row directly gives 4 carrying one and 12 that do not, matching
        # neither figure exactly, though it agrees with the "12 carry none"
        # half of both the Tests and Why paragraphs.
        self.assertEqual(len(with_block), 4)
        self.assertEqual(len(without_block), 12)
        document = v1_registry()
        blocked = [e for e in document["entries"] if e["deployment_block"] is not None]
        unblocked = [e for e in document["entries"] if e["deployment_block"] is None]
        self.assertEqual(len(blocked), 4)
        self.assertEqual(len(unblocked), 12)
        registry_gaps = wildcat_v1.gaps(document)
        for entry in unblocked:
            self.assertTrue(any(
                entry["address"] in gap and "deployment block is not established" in gap
                for gap in registry_gaps
            ))

    def test_every_v1_subject_carries_a_code_digest_length_and_observed_block(self):
        for entry in v1_registry()["entries"]:
            self.assertRegex(entry["code_keccak256"], r"^0x[0-9a-f]{64}$")
            self.assertGreater(entry["code_length"], 0)
            self.assertGreater(entry["observed_block_number"], 0)
        # The epoch model reads runtime code from the collection's own opening
        # reads, not from these registry digests: they were read at each
        # subject's own observed block, not necessarily this capture's.
        self.assertTrue(any(
            entry["observed_block_number"] != int(fixture(wildcat_v1.VENUE)["plan"]["interval"]["start"])
            for entry in v1_registry()["entries"]
        ))

    def test_the_v2_release_still_carries_no_source_gap(self):
        document = registry()
        self.assertEqual(len(document["entries"]), 137)
        self.assertTrue(all(entry["source_commit"] for entry in document["entries"]))
        self.assertFalse(any("no source commit" in gap for gap in wildcat_v2.gaps(document)))


class SharedSubjectTests(unittest.TestCase):
    """The two assertions `shared-subject-attributed-per-venue` resolves."""

    def test_arch_controller_is_a_subject_of_both_venues(self):
        v1_document = v1_registry()
        v2_document = registry()
        wildcat_registry.validate_shared_subjects(v1_document, v2_document)
        v1_addresses = set(wildcat_registry.subject_entries(v1_document))
        v2_addresses = set(wildcat_registry.subject_entries(v2_document))
        for address in wildcat_registry.SHARED_SUBJECTS:
            self.assertIn(address, v1_addresses)
            self.assertIn(address, v2_addresses)
        self.assertEqual(v1_addresses & v2_addresses, wildcat_registry.SHARED_SUBJECTS)
        self.assertEqual(len(v1_addresses | v2_addresses), 151)
        # A third shared subject fails the reviewed assertion rather than
        # silently widening the intersection.
        widened = dict(v1_document)
        extra = next(iter(v2_addresses - v1_addresses))
        widened["entries"] = list(v1_document["entries"]) + [
            dict(v1_document["entries"][0], address=extra)
        ]
        with self.assertRaisesRegex(AlexandriaError, "exact two-address intersection|reviewed shared"):
            wildcat_registry.validate_shared_subjects(widened, v2_document)

    def test_constructed_shared_logs_are_attributed_to_each_capturing_venue(self):
        for venue, document in (("wildcat-v1", v1_registry()), ("wildcat-v2", registry())):
            with self.subTest(venue=venue), tempfile.TemporaryDirectory() as temporary:
                state = fixture(venue)
                start = int(state["plan"]["interval"]["start"])
                transport = WildcatTransport(state)
                for index, address in enumerate(sorted(wildcat_registry.SHARED_SUBJECTS)):
                    state["logs"]["0"].append({
                        "address": address, "blockHash": transport._hash(start),
                        "blockNumber": hex(start), "data": "0x", "logIndex": hex(index),
                        "removed": False, "topics": ["0x" + "ab" * 32],
                        "transactionHash": transport.transactions(start)[0],
                        "transactionIndex": "0x0",
                    })
                state["logs"]["0"].sort(key=lambda row: (
                    int(row["blockNumber"], 16), int(row["transactionIndex"], 16),
                    int(row["logIndex"], 16),
                ))
                root = Path(temporary)
                staging = root / "staging"
                staging.mkdir()
                Collector(state["plan"], staging, transport, registry=document).collect()
                Reconciler(
                    state["plan"], staging, WildcatTransport(state), SECOND_PROVIDER,
                    registry=document,
                ).reconcile()
                output = root / "release"
                Builder(state["plan"], staging, document, created_at=CREATED_AT).build(output)
                self.assertEqual(check_interval(output)["reconciliation"], "agreed")
                captures = json.loads((output / "manifest.json").read_text())["captures"]
                self.assertEqual({capture["venue"] for capture in captures}, {venue})
                receipt = existing.component_document(output, "epoch-table")
                for address in wildcat_registry.SHARED_SUBJECTS:
                    self.assertTrue(any(
                        row["subject"] == address for row in receipt["log_attributions"]
                    ))


    def test_neither_venue_attributes_the_other_venues_subject(self):
        v1_plan = fixture(wildcat_v1.VENUE)["plan"]
        v2_plan = fixture(wildcat_v2.VENUE)["plan"]
        only_v2 = next(address for address in v2_plan["subjects"] if address not in v1_plan["subjects"])
        only_v1 = next(address for address in v1_plan["subjects"] if address not in v2_plan["subjects"])
        with self.assertRaisesRegex(AlexandriaError, "not emitted by a declared subject"):
            interval.proxy_log_positions(
                [{"address": only_v2}], v1_plan["subjects"], v1_plan["interval"], upgrade_topic=None
            )
        with self.assertRaisesRegex(AlexandriaError, "not emitted by a declared subject"):
            interval.proxy_log_positions(
                [{"address": only_v1}], v2_plan["subjects"], v2_plan["interval"], upgrade_topic=None
            )


class V1PreservedAdmissionTests(WildcatCase):
    VENUE = wildcat_v1.VENUE

    def test_only_the_reviewed_deployment_omits_the_constructed_gap(self):
        self.assertEqual(wildcat_v1.PRESERVED_DEPLOYMENTS, frozenset({"wildcat-v1-archcontroller"}))
        for admitted in (False, True):
            state = deepcopy(self.state)
            if admitted:
                state["plan"]["deployment"] = "wildcat-v1-archcontroller"
            output, _ = self.released(str(admitted), state)
            self.assertEqual(check_interval(output)["reconciliation"], "agreed")
            for capture in self.captures(output).values():
                gaps = capture["coverage"]["gaps"]
                constructed = any("constructed rather than collected" in gap for gap in gaps)
                self.assertEqual(constructed, not admitted and capture["id"] in EVIDENCE_COMPONENTS)



class ConstructedStagingTests(WildcatCase):
    def expected_gap(self):
        return wildcat_v2.CONSTRUCTED_STAGING_GAP.format(
            deployment=self.plan["deployment"], venue="wildcat-v2"
        )

    def test_constructed_staging_gap_present_for_fixture_deployment(self):
        self.assertEqual(wildcat_v2.PRESERVED_DEPLOYMENTS, frozenset({"wildcat-v2-hooksfactory"}))
        self.assertNotIn(self.plan["deployment"], wildcat_v2.PRESERVED_DEPLOYMENTS)
        output, _release_id = self.released()
        captures = self.captures(output)
        gap = self.expected_gap()
        self.assertIn("constructed rather than collected", gap)
        self.assertIn(self.plan["deployment"], gap)
        for name, capture in captures.items():
            with self.subTest(component=name):
                if name in EVIDENCE_COMPONENTS:
                    self.assertEqual(capture["coverage"]["gaps"].count(gap), 1)
                    self.assertEqual(capture["coverage"]["status"], "partial")
                else:
                    self.assertNotIn(gap, capture["coverage"]["gaps"])
        self.assertEqual(
            sorted(name for name, capture in captures.items() if gap in capture["coverage"]["gaps"]),
            sorted(EVIDENCE_COMPONENTS),
        )

    def test_a_release_that_drops_the_gap_does_not_check(self):
        output, _release_id = self.released()
        self.check_without_verify(output)
        gap = self.expected_gap()
        path = output / "manifest.json"
        manifest = json.loads(path.read_text())
        next(c for c in manifest["captures"] if c["id"] == "traces")["coverage"]["gaps"].remove(gap)
        path.write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(AlexandriaError, "traces coverage does not name a gap its venue owes"):
            self.check_without_verify(output)

    def test_a_release_built_with_the_gap_still_checks_once_its_name_is_admitted(self):
        output, _release_id = self.released()
        with mock.patch.object(
            wildcat_v2, "PRESERVED_DEPLOYMENTS", frozenset({self.plan["deployment"]})
        ):
            self.assertEqual(check_interval(output)["epochs"], 137)
            rebuilt = self.root / "admitted"
            Builder(
                self.plan, self.root / "release-staging", self.registry, created_at=CREATED_AT
            ).build(rebuilt)
            self.assertNotIn(
                self.expected_gap(), self.captures(rebuilt)["logs"]["coverage"]["gaps"]
            )

    def test_constructed_staging_gap_absent_for_admitted_deployment(self):
        """wildcat-v2-hooksfactory is genuinely admitted; the Step 6 fixture name is not.

        Unlike the two cases above, nothing here is mocked: this is the real
        module-level `PRESERVED_DEPLOYMENTS` Step 9 admitted. A plan naming the
        admitted deployment carries no constructed-staging gap on any evidence
        scope; a plan naming the Step 6 fixture deployment still does.
        """
        self.assertEqual(wildcat_v2.PRESERVED_DEPLOYMENTS, frozenset({"wildcat-v2-hooksfactory"}))
        admitted_state = deepcopy(self.state)
        admitted_state["plan"]["deployment"] = "wildcat-v2-hooksfactory"
        output, _release_id = self.released("admitted-release", admitted_state)
        self.assertEqual(check_interval(output)["epochs"], 137)
        gap = wildcat_v2.CONSTRUCTED_STAGING_GAP.format(
            deployment="wildcat-v2-hooksfactory", venue="wildcat-v2"
        )
        for name, capture in self.captures(output).items():
            with self.subTest(component=name):
                self.assertNotIn(gap, capture["coverage"]["gaps"])
        fixture_output, _fixture_release_id = self.released()
        fixture_gap = self.expected_gap()
        for name, capture in self.captures(fixture_output).items():
            if name in EVIDENCE_COMPONENTS:
                with self.subTest(component=name):
                    self.assertIn(fixture_gap, capture["coverage"]["gaps"])

    def test_no_plan_field_admits_a_deployment_as_preserved(self):
        for field in ("preserved", "staging", "provenance"):
            with self.subTest(field=field):
                plan = deepcopy(self.plan)
                plan[field] = True
                with self.assertRaisesRegex(AlexandriaError, "unknown shape"):
                    Collector(plan, self.scratch(field), WildcatTransport(self.state), registry=self.registry)

    def test_the_label_follows_the_reviewed_constant_and_nothing_else(self):
        logs = [record for shard in self.state["logs"].values() for record in shard]
        self.assertIn(self.expected_gap(), wildcat_v2.evidence_gaps(self.plan, self.registry, logs))
        with mock.patch.object(
            wildcat_v2, "PRESERVED_DEPLOYMENTS", frozenset({self.plan["deployment"]})
        ):
            self.assertNotIn(
                self.expected_gap(), wildcat_v2.evidence_gaps(self.plan, self.registry, logs)
            )
            renamed = dict(self.plan, deployment="another-constructed-fixture")
            self.assertTrue(any(
                "another-constructed-fixture" in gap and "constructed" in gap
                for gap in wildcat_v2.evidence_gaps(renamed, self.registry, logs)
            ))


class CollectorConnectionTests(WildcatCase):
    """Collect through check over a subject set: every consumer the single proxy used to own."""

    def test_the_constructed_path_runs_from_collect_through_check(self):
        staging = self.scratch("path-staging")
        transport = WildcatTransport(self.state)
        summary = Collector(self.plan, staging, transport, registry=self.registry).collect()
        self.assertEqual(summary["record_counts"], {"boundary-blocks": 4, "logs": 9, "traces": 3})
        self.assertEqual(summary["opening_reads"], {"issued": 139, "resumed_from": 0, "total": 139})
        entries = existing.opening_entries(staging)
        self.assertEqual(len(entries), 139)
        self.assertEqual({entry["shard"] for entry in entries}, {len(self.plan["shards"])})
        document = Reconciler(
            self.plan, staging, WildcatTransport(self.state), SECOND_PROVIDER, registry=self.registry,
        ).reconcile()
        # 4 boundary hashes, 4 transaction orders, 9 log identities, 3 trace
        # identities (the targeted-trace derivation, compared against the
        # second provider's own trace_transaction answers), 139 opening reads.
        self.assertEqual(document["reconciliation"]["compared"], 159)
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        output = self.root / "path-release"
        release_id = Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(output)
        again = Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(
            self.root / "path-release-again"
        )
        self.assertEqual(release_id, again)
        summary = check_interval(output)
        self.assertEqual(summary["release_id"], release_id)
        self.assertEqual(summary["epochs"], 137)

    def test_a_subject_set_plan_never_reaches_a_proxy_lookup(self):
        class SubjectPlan(dict):
            def __getitem__(self, key):
                if key == "proxy":
                    raise AssertionError("a subject-set plan reached plan['proxy']")
                return super().__getitem__(key)

            def get(self, key, default=None):
                if key == "proxy":
                    raise AssertionError("a subject-set plan reached plan.get('proxy')")
                return super().get(key, default)

        plan = SubjectPlan(self.plan)
        staging = self.scratch("guarded-staging")
        Collector(plan, staging, WildcatTransport(self.state), registry=self.registry).collect()
        Reconciler(
            plan, staging, WildcatTransport(self.state), SECOND_PROVIDER, registry=self.registry,
        ).reconcile()
        output = self.root / "guarded-release"
        Builder(plan, staging, self.registry, created_at=CREATED_AT).build(output)
        real = dict.__getitem__
        with mock.patch.object(usdc_interval, "validate_plan", wraps=usdc_interval.validate_plan):
            loaded = usdc_interval.load_bytes

            def guarded(data, label, **kwargs):
                value = loaded(data, label, **kwargs)
                return SubjectPlan(value) if label == "component interval-plan" else value

            with mock.patch.object(usdc_interval, "load_bytes", side_effect=guarded):
                self.assertEqual(check_interval(output)["epochs"], 137)
        self.assertEqual(real(plan, "venue"), "wildcat-v2")

    def test_a_subject_set_under_the_single_proxy_venue_refuses_before_any_request(self):
        plan = deepcopy(self.plan)
        plan["venue"] = "compound-v3"
        transport = WildcatTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, "subject-set plan has no opening reads"):
            Collector(plan, self.scratch("compound-subjects"), transport)
        self.assertEqual(transport.calls, [])
        with self.assertRaisesRegex(AlexandriaError, "subject-set plan has no opening reads"):
            Reconciler(plan, self.scratch("compound-reconcile"), transport, SECOND_PROVIDER)
        with self.assertRaisesRegex(AlexandriaError, "subject-set plan has no opening reads"):
            Builder(plan, self.scratch("compound-build"), existing.registry(), created_at=CREATED_AT)
        # `check` replays the opening reads through the same dispatch.
        output, _release_id = self.released()
        documents = {
            name: existing.component_document(output, name)
            for name in ("logs", "registry", OPENING_CLASS)
        }
        parts = usdc_interval.journal_components(plan, tuple(plan["evidence_classes"]))
        with self.assertRaisesRegex(AlexandriaError, "subject-set plan has no opening reads"):
            usdc_interval._replay_release_opening(plan, documents, plan["evidence_classes"], parts)
        replayed = usdc_interval._replay_release_opening(
            self.plan, documents, self.plan["evidence_classes"], parts
        )
        self.assertEqual(len(replayed.codes), 137)

    def test_a_single_proxy_plan_under_this_venue_refuses(self):
        plan = deepcopy(existing.fixture()["plan"])
        plan["venue"] = "wildcat-v2"
        with self.assertRaisesRegex(AlexandriaError, "single-proxy plan names none"):
            Collector(plan, self.scratch("proxy-plan"), WildcatTransport(self.state), registry=self.registry)

    def test_the_venue_needs_its_registry_and_refuses_another_one(self):
        with self.assertRaisesRegex(AlexandriaError, "none was supplied"):
            Collector(self.plan, self.scratch("no-registry"), WildcatTransport(self.state))
        with self.assertRaisesRegex(AlexandriaError, "format is unknown"):
            Collector(
                self.plan, self.scratch("other-registry"), WildcatTransport(self.state),
                registry=existing.registry(),
            )
        with self.assertRaisesRegex(AlexandriaError, "format is unknown"):
            Builder(self.plan, self.scratch("other-build"), existing.registry(), created_at=CREATED_AT)
        edited = registry()
        edited["entries"][0]["deployment_block"] = 1
        with self.assertRaisesRegex(AlexandriaError, "do not match the pinned registry"):
            Collector(self.plan, self.scratch("edited"), WildcatTransport(self.state), registry=edited)

    def test_the_network_commands_take_the_registry_and_refuse_before_the_endpoint_is_read(self):
        plan_path = self.root / "plan.json"
        registry_path = self.root / "registry.json"
        plan_path.write_bytes(canonical_bytes(self.plan))
        registry_path.write_bytes(_registry_bytes())
        for command in (
            ["collect", "--plan", str(plan_path), "--staging", str(self.root / "cli-staging")],
            ["reconcile", "--plan", str(plan_path), "--staging", str(self.root / "cli-staging"),
             "--provider-class", SECOND_PROVIDER],
        ):
            with self.subTest(command=command[0]):
                environment = mock.Mock(side_effect=AssertionError("the endpoint was read"))
                stderr = existing.io.StringIO()
                with mock.patch.object(usdc_interval.HttpsTransport, "from_environment", environment):
                    with mock.patch.object(sys, "stderr", stderr):
                        self.assertEqual(usdc_interval.main(command), 1)
                self.assertIn("none was supplied", stderr.getvalue())
                # With the registry the same command reaches the endpoint, which is absent here.
                reached = mock.Mock(side_effect=AlexandriaError("endpoint reached"))
                stderr = existing.io.StringIO()
                with mock.patch.object(usdc_interval.HttpsTransport, "from_environment", reached):
                    with mock.patch.object(sys, "stderr", stderr):
                        self.assertEqual(
                            usdc_interval.main(command + ["--registry", str(registry_path)]), 1
                        )
                self.assertIn("endpoint reached", stderr.getvalue())
        self.assertFalse((self.root / "cli-staging").exists())

    def test_a_subject_the_registry_does_not_list_refuses(self):
        plan = deepcopy(self.plan)
        plan["subjects"][3] = "0x" + "12" * 20
        transport = WildcatTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, "registry does not list"):
            Collector(plan, self.scratch("stranger"), transport, registry=self.registry)
        self.assertEqual(transport.calls, [])

    def test_a_log_from_an_undeclared_address_refuses_and_closes_its_journals(self):
        state = deepcopy(self.state)
        state["logs"]["1"][0]["address"] = "0x" + "12" * 20
        staging = self.scratch("stray-log")
        collector = Collector(state["plan"], staging, WildcatTransport(state), registry=self.registry)
        with self.assertRaisesRegex(AlexandriaError, "not emitted by a declared subject"):
            collector.collect()
        self.assertEqual(collector.staging._handles, {})
        receipts = [
            json.loads(line) for line in (staging / "receipts" / "errors.jsonl").read_bytes().splitlines()
        ]
        self.assertEqual([receipt["code"] for receipt in receipts], ["malformed-staged-log"])
        self.assertEqual(existing.opening_entries(staging), [])

    def test_an_opening_refusal_closes_every_journal_handle_it_owned(self):
        label = f"opening read 5 implementation-code block {self.plan['interval']['start']}"
        empty = lambda envelope: canonical_bytes(  # noqa: E731
            {"id": envelope["id"], "jsonrpc": "2.0", "result": "0x"}
        )
        staging = self.scratch("refused-opening")
        state = deepcopy(self.state)
        state["plan"]["shards_per_component"] = 1
        collector = Collector(
            state["plan"], staging, WildcatTransport(state, faults={label: empty}),
            registry=self.registry, rpc_concurrency=1,
        )
        opened = []
        handle = collector.staging._handle

        def watched(name):
            value = handle(name)
            if value not in opened:
                opened.append(value)
            return value

        with mock.patch.object(collector.staging, "_handle", side_effect=watched):
            # A subject with a recorded block and no code there is a wrong
            # registry, refused by name; it is never bisected.
            with self.assertRaisesRegex(AlexandriaError, "the registry is wrong about it"):
                collector.collect()
        # One probe of the unrecorded subject, then the three recorded code reads.
        code_reads = [label for method, label in collector.transport.calls if method == "eth_getCode"]
        self.assertEqual(len(code_reads), 4)
        self.assertEqual(sum("first-code-probe" in label for label in code_reads), 1)
        # One handle per physical journal: three classes over four components, and the opening journal.
        self.assertEqual(len(opened), 13)
        self.assertTrue(all(value.closed for value in opened))
        self.assertEqual(collector.staging._handles, {})
        receipts = [
            json.loads(line) for line in (staging / "receipts" / "errors.jsonl").read_bytes().splitlines()
        ]
        self.assertEqual(receipts[-1]["code"], "no-code-at-recorded-block")
        # The refused run resumes: the five committed reads are replayed, not re-issued.
        resumed = Collector(state["plan"], staging, WildcatTransport(state), registry=self.registry)
        self.assertEqual(
            resumed.collect()["opening_reads"], {"issued": 134, "resumed_from": 5, "total": 139}
        )

    def test_two_subjects_emitting_in_one_block_and_transaction_each_keep_their_own_epoch(self):
        output, _release_id = self.released()
        receipt = existing.component_document(output, "epoch-table")
        rows = receipt["log_attributions"]
        shared = [row for row in rows if row["block_number"] == "25895345"]
        self.assertEqual([row["log_index"] for row in shared], [10, 11, 12])
        self.assertEqual(len({row["transaction_hash"] for row in shared}), 1)
        self.assertEqual(len({row["subject"] for row in shared}), 2)
        self.assertEqual(shared[0]["subject"], shared[2]["subject"])
        deploy = [row for row in rows if row["block_number"] == str(DEPLOY_BLOCK)]
        self.assertEqual(len({row["transaction_hash"] for row in deploy}), 1)
        self.assertEqual(
            {row["subject"] for row in deploy},
            {NEW_MARKET, NEW_HOOKS, next(
                e["address"] for e in self.registry["entries"] if e["role"] == "factory"
            )},
        )
        for row in rows:
            self.assertEqual(row["epoch_index"], 0)
            self.assertEqual(row["kind"], "proxy-log")
            self.assertEqual(row["block_hash"], self.state["blocks"][row["block_number"]])

    def test_every_retained_attribution_passes_its_schema_and_the_runtime_validator(self):
        output, _release_id = self.released()
        receipt = existing.component_document(output, "epoch-table")
        schema = json.loads((PLUGIN / "schemas" / "interval-receipt-v3.schema.json").read_text())
        self.assertEqual(schema["properties"]["format"]["const"], SUBJECT_RECEIPT_FORMAT)
        self.assertEqual(schema_errors(schema, receipt), [])
        self.assertEqual(len(receipt["log_attributions"]), 9)
        validate_attributions(receipt["log_attributions"], subjects=self.plan["subjects"])
        # The validator above is not the oracle for itself: each malformed
        # receipt below is one the schema refuses too.
        for label, edit in {
            "a row without its subject": lambda r: r["log_attributions"][0].pop("subject"),
            "a flat epoch list": lambda r: r.__setitem__("epochs", epoch_row(r, NEW_MARKET)["epochs"]),
            "a table keyed by subject": lambda r: r.__setitem__("epochs", epoch_table(r)),
            "a subject that is not an address": lambda r: r["epochs"][0].__setitem__("subject", "market"),
            "a row with an undeclared field": lambda r: r["epochs"][0].__setitem__("count", 1),
            "a subject with no epochs": lambda r: r["epochs"][0].__setitem__("epochs", []),
            "the single-proxy format": lambda r: r.__setitem__("format", "alexandria-interval-receipt/v2"),
            "no first-code rows": lambda r: r.pop("first_code"),
            "a first-code row with another opening": lambda r: r["first_code"][0].__setitem__("opening", "recorded"),
            "a first-code row with another field": lambda r: r["first_code"][0].__setitem__("note", "x"),
        }.items():
            with self.subTest(specimen=label):
                specimen = deepcopy(receipt)
                edit(specimen)
                self.assertNotEqual(schema_errors(schema, specimen), [])
        single = json.loads((PLUGIN / "schemas" / "interval-receipt-v2.schema.json").read_text())
        self.assertNotEqual(schema_errors(single, receipt), [])

    def test_check_recomputes_every_attribution_from_the_preserved_logs(self):
        edits = {
            "another declared subject": lambda rows: rows[0].__setitem__("subject", NEW_MARKET),
            "another epoch": lambda rows: rows[0].__setitem__("epoch_index", 1),
            "a dropped row": lambda rows: rows.pop(),
            "an upgrade boundary": lambda rows: rows[0].__setitem__("kind", "upgrade-boundary"),
        }
        for label, edit in edits.items():
            with self.subTest(edit=label):
                output, _release_id = self.released(re.sub(r"\W", "-", label))
                self.check_without_verify(output)
                self.rewrite(output, "epoch-table", lambda r: edit(r["log_attributions"]))
                with self.assertRaisesRegex(AlexandriaError, "log attributions do not match"):
                    self.check_without_verify(output)

    def test_wrong_identities_and_mismatched_shapes_refuse_as_alexandria_errors(self):
        stranger = "0x" + "12" * 20

        def undeclared_key(receipt):
            table = epoch_table(receipt)
            table[stranger] = deepcopy(table[NEW_MARKET])
            table[stranger][0].update(proxy=stranger, implementation=stranger)
            receipt["epochs"] = interval.subject_epoch_rows(table)

        def wrong_owner(receipt):
            epoch_row(receipt, NEW_MARKET)["epochs"][0]["proxy"] = NEW_HOOKS

        def repeated(receipt):
            receipt["epochs"].insert(1, deepcopy(receipt["epochs"][0]))

        def unsorted(receipt):
            receipt["epochs"][0], receipt["epochs"][1] = receipt["epochs"][1], receipt["epochs"][0]

        specimens = {
            "an undeclared subject key": (undeclared_key, "undeclared subject"),
            "an epoch owned by another subject": (wrong_owner, "does not belong to its table subject"),
            "a subject row repeated": (repeated, "repeat a subject or are not in ascending"),
            "subject rows out of order": (unsorted, "repeat a subject or are not in ascending"),
            "a table keyed by subject": (
                lambda r: r.__setitem__("epochs", epoch_table(r)), "list of subject epoch rows",
            ),
            "a row with an undeclared field": (
                lambda r: r["epochs"][0].__setitem__("count", 1), "subject row has an unknown shape",
            ),
            "a subject that is not an address": (
                lambda r: r["epochs"][0].__setitem__("subject", "market"), "not a lowercase address",
            ),
            "a flat epoch list": (
                lambda r: r.__setitem__("epochs", epoch_row(r, NEW_MARKET)["epochs"]),
                "subject row has an unknown shape",
            ),
            "an empty subject table": (
                lambda r: epoch_row(r, NEW_MARKET).__setitem__("epochs", []), "epoch",
            ),
            "a subject's epochs that are not a list": (
                lambda r: epoch_row(r, NEW_MARKET).__setitem__("epochs", {}), "non-empty list",
            ),
            "no subject rows": (lambda r: r.__setitem__("epochs", []), "names no subject"),
            "a null epoch table": (lambda r: r.__setitem__("epochs", None), "epoch"),
            "a row without its subject": (
                lambda r: r["log_attributions"][0].pop("subject"), "unknown shape",
            ),
            "a row naming an undeclared subject": (
                lambda r: r["log_attributions"][0].__setitem__("subject", stranger),
                "undeclared subject",
            ),
            "rows that are not a list": (
                lambda r: r.__setitem__("log_attributions", {"rows": []}), "not a list",
            ),
            "the single-proxy receipt format": (
                lambda r: (r.__setitem__("format", "alexandria-interval-receipt/v2"), r.pop("first_code")),
                "does not match the plan's subject form",
            ),
            "a missing subject's epochs": (
                lambda r: r["epochs"].remove(epoch_row(r, NEW_MARKET)), "which no epoch names",
            ),
        }
        output, _release_id = self.released()
        original = existing.component_path(output, "epoch-table").read_bytes()
        for label, (edit, message) in specimens.items():
            with self.subTest(specimen=label):
                existing.component_path(output, "epoch-table").write_bytes(original)
                self.rewrite(output, "epoch-table", edit)
                with self.assertRaisesRegex(AlexandriaError, message):
                    self.check_without_verify(output)
        existing.component_path(output, "epoch-table").write_bytes(original)
        self.check_without_verify(output)

    def test_a_release_whose_registry_moved_does_not_check(self):
        output, _release_id = self.released()
        self.rewrite(
            output, "registry",
            lambda document: document["entries"][0].__setitem__("deployment_block", 1),
        )
        with self.assertRaisesRegex(AlexandriaError, "do not match the pinned registry"):
            self.check_without_verify(output)

    def test_a_second_provider_that_disagrees_is_recorded_not_settled(self):
        second_state = deepcopy(self.state)
        second_state["code"][NEW_MARKET] = "0x60806040" + "cd" * 32
        second_state["blocks"][str(DEPLOY_BLOCK)] = "0x" + "99" * 32
        for record in second_state["logs"]["2"]:
            record["blockHash"] = self.state["blocks"][str(DEPLOY_BLOCK)]
        staging = self.staged("disputed", second=WildcatTransport(second_state))
        record = json.loads((staging / "reconciliation" / "reconciliation.json").read_text())
        self.assertEqual(record["reconciliation"]["status"], "disputed")
        self.assertEqual(
            [(item["kind"], item["identity"]) for item in record["reconciliation"]["disputed"]],
            [
                ("first-block-hash", f"block {DEPLOY_BLOCK}"),
                ("code-digest", f"code of {NEW_MARKET} at block {DEPLOY_BLOCK}"),
            ],
        )
        # Both providers' bytes are kept for the disputed opening reads.
        kept = [
            json.loads(line)
            for line in (staging / "reconciliation" / "disputed.jsonl").read_bytes().splitlines()
        ]
        self.assertEqual(
            [(item["class"], item["shard"]) for item in kept],
            [(OPENING_CLASS, len(self.plan["shards"]))] * 2,
        )


class MarketDeployTests(WildcatCase):
    def logs(self, state=None):
        return [record for shard in (state or self.state)["logs"].values() for record in shard]

    def test_the_deploy_logs_agree_with_the_80_declared_markets(self):
        report = wildcat_v2.market_deploy_report(self.plan, self.registry, self.logs())
        self.assertTrue(report["compared"])
        self.assertEqual(report["declared"], 80)
        self.assertEqual(report["expected"], [NEW_MARKET])
        self.assertEqual(report["observed"], [NEW_MARKET])
        self.assertEqual((report["missing"], report["undeclared"]), ([], []))
        self.assertFalse(any(
            "MarketDeployed" in gap for gap in wildcat_v2.evidence_gaps(self.plan, self.registry, self.logs())
        ))

    def test_the_deploy_topic_is_the_one_the_merged_record_preserves(self):
        estate = json.loads((REPO_ROOT / wildcat_registry.ESTATE_PATH).read_text(encoding="utf-8"))
        topics = {
            event["topics"][0] for event in estate["factory_events"]["events"]
            if event["event"] == "MarketDeployed"
        }
        self.assertEqual(topics, {wildcat_v2.MARKET_DEPLOYED_TOPIC})
        named = {
            "0x" + event["topics"][2][26:] for event in estate["factory_events"]["events"]
            if event["event"] == "MarketDeployed"
        }
        self.assertEqual(named, {e["address"] for e in self.registry["entries"] if e["role"] == "market"})

    def test_a_declared_market_with_no_deploy_log_is_reported_in_the_release(self):
        state = deepcopy(self.state)
        state["logs"]["2"] = [
            record for record in state["logs"]["2"]
            if record["topics"][0] != wildcat_v2.MARKET_DEPLOYED_TOPIC
        ]
        report = wildcat_v2.market_deploy_report(state["plan"], self.registry, self.logs(state))
        self.assertEqual(report["missing"], [NEW_MARKET])
        output, _release_id = self.released("missing-deploy", state)
        self.assertEqual(check_interval(output)["epochs"], 137)
        for name in EVIDENCE_COMPONENTS:
            gaps = self.captures(output)[name]["coverage"]["gaps"]
            self.assertEqual(
                sum(1 for gap in gaps if NEW_MARKET in gap and "no preserved MarketDeployed log" in gap), 1
            )

    def test_a_deploy_log_naming_an_undeclared_market_is_reported_in_the_release(self):
        stranger = "0x" + "12" * 20
        state = deepcopy(self.state)
        extra = deepcopy(next(
            record for record in state["logs"]["2"]
            if record["topics"][0] == wildcat_v2.MARKET_DEPLOYED_TOPIC
        ))
        extra["topics"][2] = "0x" + "0" * 24 + stranger[2:]
        extra["logIndex"] = hex(120)
        state["logs"]["2"].append(extra)
        report = wildcat_v2.market_deploy_report(state["plan"], self.registry, self.logs(state))
        self.assertEqual(report["undeclared"], [(stranger, DEPLOY_BLOCK)])
        self.assertEqual(report["missing"], [])
        output, _release_id = self.released("undeclared-deploy", state)
        self.assertEqual(check_interval(output)["epochs"], 137)
        gaps = self.captures(output)["logs"]["coverage"]["gaps"]
        self.assertEqual(sum(1 for gap in gaps if stranger in gap and "80 markets" in gap), 1)

    def test_a_plan_without_the_factory_says_the_markets_were_not_compared(self):
        factory = next(e["address"] for e in self.registry["entries"] if e["role"] == "factory")
        plan = deepcopy(self.plan)
        plan["subjects"].remove(factory)
        logs = [record for record in self.logs() if record["address"] != factory]
        report = wildcat_v2.market_deploy_report(plan, self.registry, logs)
        self.assertFalse(report["compared"])
        gaps = wildcat_v2.evidence_gaps(plan, self.registry, logs)
        self.assertEqual(sum(1 for gap in gaps if factory in gap and "not compared" in gap), 1)
        self.assertTrue(any("1 of the 137" in gap for gap in wildcat_v2.gaps(self.registry, plan)))

    def test_a_malformed_deploy_log_refuses(self):
        logs = self.logs()
        record = next(r for r in logs if r["topics"][0] == wildcat_v2.MARKET_DEPLOYED_TOPIC)
        record["topics"] = record["topics"][:2]
        with self.assertRaisesRegex(AlexandriaError, "does not name its market"):
            wildcat_v2.market_deploy_report(self.plan, self.registry, logs)


class CoverageParityTests(WildcatCase):
    # Where each field a recorded Compound coverage row carries lives in a capture.
    FIELD_PATHS = {
        "component": ("component",),
        "evidence_class": ("evidence_class",),
        "finality": ("scope", "finality"),
        "gaps": ("coverage", "gaps"),
        "record_count": ("coverage", "record_count"),
        "status": ("coverage", "status"),
        "unsupported_collections": ("coverage", "unsupported_collections"),
    }

    def test_every_capture_carries_the_fields_the_nine_recorded_rows_carry(self):
        rows = json.loads(CAPTURE_RECORD.read_text(encoding="utf-8"))["pattern_release"]["coverage"]
        self.assertEqual(len(rows), 9)
        for row in rows:
            self.assertEqual(set(row), set(self.FIELD_PATHS))
        output, _release_id = self.released()
        captures = self.captures(output)
        self.assertTrue({row["component"] for row in rows} <= set(captures))
        recorded_types = {field: {type(row[field]) for row in rows} for field in self.FIELD_PATHS}
        for name, capture in captures.items():
            for field, path in self.FIELD_PATHS.items():
                with self.subTest(component=name, field=field):
                    value = capture
                    for key in path:
                        self.assertIn(key, value)
                        value = value[key]
                    self.assertIn(type(value), recorded_types[field])


class GeneratorCrossRecordTests(unittest.TestCase):
    """The generator's checks between its two records, which no pinned byte can reach.

    Both records are pinned, so a disagreement between them cannot be staged
    on disk without failing the pin first. Each case edits one parsed record
    after the real pin check has passed.
    """

    def generated(self, edit):
        real = wildcat_registry.read_source

        def edited(repo_root, path, sha256, size):
            record = real(repo_root, path, sha256, size)
            edit(path, record)
            return record

        with mock.patch.object(wildcat_registry, "read_source", side_effect=edited):
            return wildcat_registry.generate_v2_registry(REPO_ROOT)

    @staticmethod
    def row(record):
        return next(r for r in record["targets"] if r.get("id") == wildcat_registry.ROW_ID)

    def test_records_that_disagree_with_each_other_refuse(self):
        targets, estate = wildcat_registry.TARGETS_PATH, wildcat_registry.ESTATE_PATH

        def other_estate_pin(path, record):
            if path == targets:
                record["evidence_digests"][estate] = "0" * 64

        def second_deployment_block(path, record):
            if path == targets:
                factory = next(
                    c for c in self.row(record)["deployment"]["contracts"] if c["role"] == "factory"
                )
                factory["deployment_block"] = 1

        def unregistered_market(path, record):
            if path == estate:
                record["arch_controller"]["getRegisteredMarkets"].pop()

        def other_registered_digest(path, record):
            if path == estate:
                record["arch_controller"]["registered_markets_sha256"] = "0" * 64

        self.assertEqual(
            canonical_bytes(self.generated(lambda path, record: None)), _registry_bytes()
        )
        for edit, message in (
            (other_estate_pin, "pins another digest"),
            (second_deployment_block, "records disagree about its deployment block"),
            (unregistered_market, "registered markets are not exactly"),
            (other_registered_digest, "disagree about the registered-market digest"),
        ):
            with self.subTest(edit=edit.__name__):
                with self.assertRaisesRegex(AlexandriaError, message):
                    self.generated(edit)

    def test_a_recorded_form_that_is_not_a_name_refuses_as_an_alexandria_error(self):
        """A list or an object there raised TypeError from the membership test."""
        for specimen in ([], {}, ["compact-sorted-json"], None, 1):
            with self.subTest(specimen=specimen):
                document = registry()
                document["list_digests"][0]["canonical_form"] = specimen
                with self.assertRaises(Exception) as raised:
                    wildcat_registry.validate_registry(document)
                self.assertIsInstance(raised.exception, AlexandriaError)
                self.assertRegex(str(raised.exception), "canonical form")


class OpeningIdentityTests(WildcatCase):
    """A subject's first-block header has to be that block's, on both providers."""

    LABEL = f"opening read 2 subject-first-block-header block {DEPLOY_BLOCK}"

    def other_number(self, envelope):
        return canonical_bytes({"id": envelope["id"], "jsonrpc": "2.0", "result": {
            "hash": self.state["blocks"][str(DEPLOY_BLOCK)],
            "number": hex(DEPLOY_BLOCK + 1),
            "transactions": [],
        }})

    def test_a_header_under_another_block_number_refuses_at_collection(self):
        staging = self.scratch("other-number")
        collector = Collector(
            self.plan, staging, WildcatTransport(self.state, faults={self.LABEL: self.other_number}),
            registry=self.registry,
        )
        with self.assertRaisesRegex(AlexandriaError, "carries another block number"):
            collector.collect()
        receipts = [
            json.loads(line) for line in (staging / "receipts" / "errors.jsonl").read_bytes().splitlines()
        ]
        self.assertEqual(receipts[-1]["code"], "malformed-header")
        # The probe of the unrecorded subject and the first header are committed.
        self.assertEqual(len(existing.opening_entries(staging)), 2)

    def test_a_second_provider_with_the_right_hash_under_another_number_is_disputed(self):
        staging = self.staged(
            "second-other-number",
            second=WildcatTransport(
                self.state, faults={f"{self.LABEL} second provider": self.other_number}
            ),
        )
        record = json.loads((staging / "reconciliation" / "reconciliation.json").read_text())
        self.assertEqual(record["reconciliation"]["status"], "disputed")
        self.assertEqual(
            [(item["kind"], item["identity"]) for item in record["reconciliation"]["disputed"]],
            [("first-block-hash", f"block {DEPLOY_BLOCK}")],
        )

    def test_a_plan_on_another_chain_refuses_before_any_request(self):
        plan = deepcopy(self.plan)
        plan["chain"] = "eip155:10"
        transport = WildcatTransport(self.state)
        with self.assertRaisesRegex(AlexandriaError, "not the chain the wildcat-v2 registry describes"):
            Collector(plan, self.scratch("other-chain"), transport, registry=self.registry)
        self.assertEqual(transport.calls, [])


class DeployLogBlockTests(WildcatCase):
    """A deploy log that contradicts the registry's block is reported, not absorbed."""

    def logs(self, state):
        return [record for shard in state["logs"].values() for record in shard]

    def deploy_log(self, state):
        return next(
            record for record in state["logs"]["2"]
            if record["topics"][0] == wildcat_v2.MARKET_DEPLOYED_TOPIC
        )

    def test_a_declared_market_deployed_at_another_block_is_reported_in_the_release(self):
        state = deepcopy(self.state)
        moved = DEPLOY_BLOCK + 1
        self.deploy_log(state).update(
            blockNumber=hex(moved), blockHash=WildcatTransport(state)._hash(moved),
            transactionHash="0x" + "78" * 32,
        )
        state["logs"]["2"].sort(key=lambda r: (int(r["blockNumber"], 16), int(r["logIndex"], 16)))
        report = wildcat_v2.market_deploy_report(state["plan"], self.registry, self.logs(state))
        self.assertEqual(report.get("misplaced"), [(NEW_MARKET, moved, DEPLOY_BLOCK)])
        self.assertEqual((report["missing"], report["undeclared"]), ([], []))
        output, _release_id = self.released("moved-deploy", state)
        self.assertEqual(check_interval(output)["epochs"], 137)
        for name in EVIDENCE_COMPONENTS:
            gaps = self.captures(output)[name]["coverage"]["gaps"]
            self.assertEqual(
                sum(
                    1 for gap in gaps
                    if NEW_MARKET in gap and f"block {moved}" in gap and f"block {DEPLOY_BLOCK}" in gap
                ),
                1,
            )

    def test_a_market_the_registry_places_before_the_interval_is_reported_too(self):
        state = deepcopy(self.state)
        entries = wildcat_registry.subject_entries(self.registry)
        start = int(self.plan["interval"]["start"])
        earlier = next(
            address for address, entry in entries.items()
            if entry["role"] == "market" and entry["deployment_block"] < start
        )
        extra = deepcopy(self.deploy_log(state))
        extra["topics"][2] = "0x" + "0" * 24 + earlier[2:]
        extra["logIndex"] = hex(120)
        state["logs"]["2"].append(extra)
        report = wildcat_v2.market_deploy_report(state["plan"], self.registry, self.logs(state))
        self.assertEqual(
            report.get("misplaced"),
            [(earlier, DEPLOY_BLOCK, entries[earlier]["deployment_block"])],
        )
        self.assertNotIn(earlier, report["expected"])
        self.assertTrue(any(
            earlier in gap and "epoch start follows the registry" in gap
            for gap in wildcat_v2.evidence_gaps(state["plan"], self.registry, self.logs(state))
        ))
        # The fixture as released disagrees nowhere.
        clean = wildcat_v2.market_deploy_report(self.plan, self.registry, self.logs(self.state))
        self.assertEqual(clean["misplaced"], [])

    def test_a_deploy_log_with_no_block_number_refuses(self):
        state = deepcopy(self.state)
        for value in (None, "25895380", "0xzz"):
            with self.subTest(block_number=value):
                self.deploy_log(state)["blockNumber"] = value
                with self.assertRaisesRegex(AlexandriaError, "carries no block number"):
                    wildcat_v2.market_deploy_report(state["plan"], self.registry, self.logs(state))

    def test_only_the_factorys_own_log_names_a_deployed_market(self):
        stranger = "0x" + "12" * 20
        state = deepcopy(self.state)
        imitation = deepcopy(self.deploy_log(state))
        imitation["address"] = NEW_HOOKS
        imitation["topics"][2] = "0x" + "0" * 24 + stranger[2:]
        imitation["logIndex"] = hex(121)
        state["logs"]["2"].append(imitation)
        report = wildcat_v2.market_deploy_report(state["plan"], self.registry, self.logs(state))
        self.assertEqual(report["observed"], [NEW_MARKET])
        self.assertEqual((report["missing"], report["undeclared"]), ([], []))


class JournalCloseTests(WildcatCase):
    """A close that fails releases every handle and does not replace the refusal."""

    class FailingFlush:
        def __init__(self, handle):
            self.handle = handle

        def flush(self):
            raise OSError("constructed flush failure")

        def close(self):
            self.handle.close()

    def test_one_failed_flush_still_closes_every_other_handle(self):
        staging = interval.Staging(self.scratch("close"), self.plan)
        names = ["boundary-blocks", "logs", "traces"]
        handles = [staging._handle(name) for name in names]
        staging._handles[names[0]] = self.FailingFlush(handles[0])
        staging._handles[names[2]] = self.FailingFlush(handles[2])
        with self.assertRaises(Exception) as raised:
            staging.close()
        # Both failing journals are named; the second is not lost behind the first.
        self.assertIsInstance(raised.exception, AlexandriaError)
        self.assertRegex(
            str(raised.exception),
            "journal boundary-blocks, traces could not be flushed and closed: constructed flush failure",
        )
        self.assertTrue(all(handle.closed for handle in handles))
        self.assertEqual(staging._handles, {})

    def test_a_close_failure_does_not_replace_the_opening_refusal(self):
        label = f"opening read 5 implementation-code block {self.plan['interval']['start']}"
        empty = lambda envelope: canonical_bytes(  # noqa: E731
            {"id": envelope["id"], "jsonrpc": "2.0", "result": "0x"}
        )
        collector = Collector(
            self.plan, self.scratch("close-refusal"),
            WildcatTransport(self.state, faults={label: empty}), registry=self.registry,
        )
        close = collector.staging.close
        opened = []

        def failing():
            # `resume` closes too, before anything is refused; only the close
            # made while the refusal is under way fails.
            if sys.exc_info()[0] is None:
                return close()
            # Whatever the refusal left open, and one journal whose flush fails.
            broken = collector.staging._handle("logs")
            opened.extend(collector.staging._handles.values())
            collector.staging._handles["logs"] = self.FailingFlush(broken)
            close()

        with mock.patch.object(collector.staging, "close", side_effect=failing):
            with self.assertRaises(Exception) as raised:
                collector.collect()
        self.assertIsInstance(raised.exception, AlexandriaError)
        self.assertRegex(str(raised.exception), "the registry is wrong about it")
        self.assertTrue(opened)
        self.assertTrue(all(handle.closed for handle in opened))
        self.assertEqual(collector.staging._handles, {})

    def test_a_close_failure_after_a_clean_collection_is_not_swallowed(self):
        collector = Collector(
            self.plan, self.scratch("close-clean"), WildcatTransport(self.state),
            registry=self.registry,
        )
        close = collector.staging.close
        opening = collector._open_interval
        finished = []

        def opened():
            finished.append(opening())
            return finished[-1]

        def failing():
            # `resume` closes as well; only the close after the last read fails.
            close()
            if finished:
                raise OSError("constructed close failure")

        with mock.patch.object(collector, "_open_interval", side_effect=opened):
            with mock.patch.object(collector.staging, "close", side_effect=failing):
                with self.assertRaisesRegex(OSError, "constructed close failure"):
                    collector.collect()
        self.assertEqual(finished[0]["total"], 139)


class ManySubjectTests(WildcatCase):
    """A subject set larger than a capture's collection limit, collected through checked.

    The pinned registry lists 137 subjects, so the set is constructed: a
    registry of the same entry shape, admitted by replacing the venue's pin
    check for the length of one case, over code and blocks generated here.
    Nothing but the pin check is replaced; every other path is the venue's own.
    """

    IN_INTERVAL = 280
    AFTER_END = 20

    def many(self):
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        shape = self.registry["entries"][0]
        addresses = [f"0x{index + 1:040x}" for index in range(self.IN_INTERVAL + self.AFTER_END)]
        entries = []
        for index, address in enumerate(addresses):
            entry = dict(shape, address=address, name=f"constructed subject {index}", code_length=24)
            entry["role"] = "factory" if index == 0 else "market"
            entry["deployment_block"] = (
                start - 1 - index if index < self.IN_INTERVAL else end + 1 + index
            )
            entry["deployment_block_source"] = "contract-record"
            entries.append(entry)
        many = dict(self.registry, entries=entries)
        state = deepcopy(self.state)
        # Declared in descending order, so the receipt's ascending rows are its own.
        state["plan"]["subjects"] = list(reversed(addresses))
        state["plan"]["deployment"] = "wildcat-v2-constructed-many-subjects"
        state["logs"] = {str(index): [] for index in range(len(state["plan"]["shards"]))}
        state["traces"] = dict(state["logs"])
        state["code"] = {address: "0x6080604052" + address[2:] for address in addresses}
        interval.validate_plan(state["plan"])
        return state, many, addresses

    def released_many(self, name):
        state, many, addresses = self.many()
        self.registry = many
        output, release_id = self.released(name, state)
        return state, addresses, output, release_id

    def test_a_release_over_more_subjects_than_the_collection_limit_builds_and_checks(self):
        self.assertGreater(self.IN_INTERVAL, release_module.MAX_COLLECTIONS)
        few_output, _few = self.released("few")
        few = {name: len(c["coverage"]["collections"]) for name, c in self.captures(few_output).items()}
        with mock.patch.object(wildcat_v2, "validate_registry", lambda registry: None):
            state, addresses, output, release_id = self.released_many("many")
            summary = check_interval(output)
        self.assertEqual(summary["release_id"], release_id)
        self.assertEqual(summary["epochs"], self.IN_INTERVAL)
        self.assertEqual(summary["receipt_semantics"], "v3-subject-positional")
        receipt = existing.component_document(output, "epoch-table")
        in_interval = sorted(addresses[:self.IN_INTERVAL])
        self.assertEqual([row["subject"] for row in receipt["epochs"]], in_interval)
        self.assertTrue(all(len(row["epochs"]) == 1 for row in receipt["epochs"]))
        captures = self.captures(output)
        # One collection, whose count a reader recomputes as the length of `/epochs`.
        self.assertEqual(
            captures["epoch-table"]["coverage"]["collections"],
            [{"name": "epochs", "record_count": self.IN_INTERVAL, "selector": "/epochs"}],
        )
        self.assertEqual(captures["epoch-table"]["coverage"]["record_count"], len(receipt["epochs"]))
        # No capture's collection list grew with the subject set.
        self.assertEqual(
            {name: len(c["coverage"]["collections"]) for name, c in captures.items()}, few
        )
        schema = json.loads((PLUGIN / "schemas" / "interval-receipt-v3.schema.json").read_text())
        self.assertEqual(schema_errors(schema, receipt), [])

    def test_the_plans_own_subject_limit_is_the_bound_on_a_release(self):
        self.IN_INTERVAL, self.AFTER_END = interval.MAX_SUBJECTS, 0
        with mock.patch.object(wildcat_v2, "validate_registry", lambda registry: None):
            _state, _addresses, output, release_id = self.released_many("limit")
            summary = check_interval(output)
            self.assertEqual((summary["release_id"], summary["epochs"]), (release_id, interval.MAX_SUBJECTS))
            # One more subject is refused while the plan is validated, by name.
            self.IN_INTERVAL += 1
            with self.assertRaisesRegex(AlexandriaError, "4096-subject limit"):
                self.many()
        self.assertEqual(
            self.captures(output)["epoch-table"]["coverage"]["collections"],
            [{"name": "epochs", "record_count": interval.MAX_SUBJECTS, "selector": "/epochs"}],
        )

    def test_the_gaps_a_large_subject_set_owes_stay_bounded(self):
        with mock.patch.object(wildcat_v2, "validate_registry", lambda registry: None):
            state, addresses, output, _release_id = self.released_many("bounded")
            owed = wildcat_v2.evidence_gaps(state["plan"], self.registry, [])
        outside = [gap for gap in owed if "after the interval end" in gap]
        self.assertEqual(len(outside), wildcat_v2.LISTED_GAPS + 1)
        listed = [a for a in state["plan"]["subjects"] if a in addresses[self.IN_INTERVAL:]]
        self.assertEqual(len(listed), self.AFTER_END)
        for address, gap in zip(listed[:wildcat_v2.LISTED_GAPS], outside):
            self.assertIn(address, gap)
        self.assertIn(
            f"{self.AFTER_END - wildcat_v2.LISTED_GAPS} further declared subjects, "
            f"{self.AFTER_END} in all",
            outside[-1],
        )
        for name in EVIDENCE_COMPONENTS:
            gaps = self.captures(output)[name]["coverage"]["gaps"]
            self.assertEqual([gap for gap in gaps if "after the interval end" in gap], outside)
            self.assertLess(len(gaps), release_module.MAX_GAPS)

    def test_each_kind_of_deploy_gap_is_bounded_and_still_counted(self):
        factory = next(e["address"] for e in self.registry["entries"] if e["role"] == "factory")
        template = next(
            record for record in self.state["logs"]["2"]
            if record["topics"][0] == wildcat_v2.MARKET_DEPLOYED_TOPIC
        )
        self.assertEqual(template["address"], factory)
        earlier = [
            e["address"] for e in self.registry["entries"]
            if e["role"] == "market" and e["deployment_block"] < int(self.plan["interval"]["start"])
        ]
        count = wildcat_v2.LISTED_GAPS + 5
        self.assertGreaterEqual(len(earlier), count)
        logs = []
        for index in range(count):
            for market in (f"0x{0xabc000 + index:040x}", earlier[index]):
                record = deepcopy(template)
                record["topics"][2] = "0x" + "0" * 24 + market[2:]
                logs.append(record)
        owed = wildcat_v2.evidence_gaps(self.plan, self.registry, logs)
        for phrase, summary in (
            ("is not one of the 80 markets", "name a market the registry does not declare"),
            ("its epoch start follows the registry", "at another block than the registry records"),
        ):
            with self.subTest(kind=summary):
                self.assertEqual(sum(1 for gap in owed if phrase in gap), wildcat_v2.LISTED_GAPS)
                counted = [gap for gap in owed if summary in gap]
                self.assertEqual(len(counted), 1)
                self.assertIn(f"5 further preserved MarketDeployed logs, {count} in all", counted[0])
        self.assertTrue(all(len(gap) <= 1000 for gap in owed))
        report = wildcat_v2.market_deploy_report(self.plan, self.registry, logs)
        self.assertEqual((len(report["undeclared"]), len(report["misplaced"])), (count, count))

    def test_check_re_derives_the_counted_sentence_a_release_carries(self):
        """Through a release: the bounded sentences `check` owes are the ones `build` wrote."""
        state = deepcopy(self.state)
        template = next(
            record for record in state["logs"]["2"]
            if record["topics"][0] == wildcat_v2.MARKET_DEPLOYED_TOPIC
        )
        count = wildcat_v2.LISTED_GAPS + 4
        for index in range(count):
            record = deepcopy(template)
            record["topics"][2] = "0x" + "0" * 24 + f"{0xabc000 + index:040x}"
            record["logIndex"] = hex(130 + index)
            state["logs"]["2"].append(record)
        output, _release_id = self.released("counted", state)
        self.assertEqual(check_interval(output)["epochs"], 137)
        gaps = self.captures(output)["logs"]["coverage"]["gaps"]
        self.assertEqual(
            sum(1 for gap in gaps if "is not one of the 80 markets" in gap), wildcat_v2.LISTED_GAPS
        )
        counted = [gap for gap in gaps if "name a market the registry does not declare" in gap]
        self.assertEqual(len(counted), 1)
        self.assertIn(f"4 further preserved MarketDeployed logs, {count} in all", counted[0])
        # Dropping the counted sentence is refused like any other owed gap.
        path = output / "manifest.json"
        manifest = json.loads(path.read_text())
        next(c for c in manifest["captures"] if c["id"] == "logs")["coverage"]["gaps"].remove(counted[0])
        path.write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(AlexandriaError, "logs coverage does not name a gap its venue owes"):
            self.check_without_verify(output)

    def test_a_subject_set_whose_code_cannot_fit_refuses_before_any_request(self):
        entries = wildcat_registry.subject_entries(self.registry)
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        cost = lambda subject: 2 * entries[subject]["code_length"] + wildcat_v2.OPENING_ENTRY_OVERHEAD  # noqa: E731
        # A recorded subject is read once; an unrecorded one may answer every probe with its code.
        needed = sum(cost(s) for s in wildcat_v2.first_blocks(self.plan, self.registry)) + (
            wildcat_v2.max_probes(start, end) * cost(COLLATERAL_STORAGE)
        )
        self.assertEqual(wildcat_v2.unrecorded_subjects(self.plan, self.registry), [COLLATERAL_STORAGE])
        self.assertLess(needed, wildcat_v2.MAX_JOURNAL_BYTES)
        # The overhead constant is measured, not assumed: no journaled code
        # read here adds more than it beyond the code's own digits.
        staging = self.staged("measured")
        lines = (staging / "journals" / f"{OPENING_CLASS}.jsonl").read_bytes().splitlines()
        code_lines = [line for line in lines if b"eth_getCode" in line]
        self.assertEqual(len(code_lines), 137)
        for line in code_lines:
            subject = json.loads(json.loads(line)["request"])["params"][0]
            digits = len(self.state["code"][subject]) - 2
            self.assertLessEqual(len(line) + 1 - digits, wildcat_v2.OPENING_ENTRY_OVERHEAD)
        transport = WildcatTransport(self.state)
        with mock.patch.object(wildcat_v2, "MAX_JOURNAL_BYTES", needed - 1):
            with self.assertRaisesRegex(AlexandriaError, "above the .* journal limit"):
                Collector(self.plan, self.scratch("too-much-code"), transport, registry=self.registry)
            with self.assertRaisesRegex(AlexandriaError, "declare fewer subjects per plan"):
                Builder(self.plan, staging, self.registry, created_at=CREATED_AT)
        self.assertEqual(transport.calls, [])
        with mock.patch.object(wildcat_v2, "MAX_JOURNAL_BYTES", needed):
            Collector(self.plan, self.scratch("just-fits"), transport, registry=self.registry)


class FirstCodeTests(WildcatCase):
    """A subject with no recorded creation block opens where this collection reads its code."""

    OBSERVED = 25895371
    SHARD_METHODS = {"eth_getLogs", "trace_transaction"}

    def staged_case(self, name, case, second_case="same"):
        staging = self.scratch(f"{name}-staging")
        self.transport = WildcatTransport(self.state, case=case)
        Collector(self.plan, staging, self.transport, registry=self.registry).collect()
        second = WildcatTransport(self.state, case=case if second_case == "same" else second_case)
        document = Reconciler(
            self.plan, staging, second, SECOND_PROVIDER, registry=self.registry
        ).reconcile()
        return staging, document

    def released_case(self, name, case):
        staging, document = self.staged_case(name, case)
        output = self.root / name
        Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(output)
        return staging, document, output

    def probes(self, calls):
        return [
            int(label.rsplit(" ", 1)[1]) for method, label in calls
            if method == "eth_getCode" and "first-code-probe" in label
        ]

    def storage_gaps(self, output, name):
        return [
            gap for gap in self.captures(output)[name]["coverage"]["gaps"]
            if COLLATERAL_STORAGE in gap
        ]

    def test_code_at_the_interval_start_opens_the_epoch_there_with_one_read(self):
        start = int(self.plan["interval"]["start"])
        _staging, _document, output = self.released_case("at-start", None)
        self.assertEqual(self.probes(self.transport.calls), [start])
        # The probe is the first opening read, asked before any shard request.
        methods = [method for method, _label in self.transport.calls]
        self.assertLess(methods.index("eth_getCode"), methods.index("eth_getLogs"))
        receipt = existing.component_document(output, "epoch-table")
        self.assertEqual(receipt["first_code"], [{
            "code_block": str(start), "empty_block": None,
            "opening": "interval-start", "subject": COLLATERAL_STORAGE,
        }])
        self.assertEqual(epoch_row(receipt, COLLATERAL_STORAGE)["epochs"][0]["start_block"], str(start))
        self.assertEqual(check_interval(output)["epochs"], 137)
        for name in EVIDENCE_COMPONENTS:
            (gap,) = self.storage_gaps(output, name)
            self.assertIn("deployment block is not established", gap)
            self.assertIn(f"has runtime code at the interval start, block {start}", gap)
            self.assertNotIn("observed", gap)
        (registry_gap,) = self.storage_gaps(output, "registry")
        self.assertIn("deployment block is not established", registry_gap)
        self.assertNotIn(f"block {start}", registry_gap)

    def test_no_code_at_the_interval_start_opens_at_the_observed_block(self):
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        staging, document, output = self.released_case("observed", "no-code-at-the-interval-start")
        calls = self.transport.calls
        probed = self.probes(calls)
        # Read empty at the start and with code at the end before any bisection,
        # then halve: every probe is fixed by the answers before it.
        expected, low, high = [start, end], start, end
        while high - low > 1:
            middle = (low + high) // 2
            expected.append(middle)
            low, high = (low, middle) if middle >= self.OBSERVED else (middle, high)
        self.assertEqual(probed, expected)
        self.assertEqual((low, high), (self.OBSERVED - 1, self.OBSERVED))
        self.assertLessEqual(len(probed), wildcat_v2.max_probes(start, end))
        self.assertEqual(wildcat_v2.max_probes(start, end), 2 + 7)
        # Every probe came before the first shard request.
        methods = [method for method, _label in calls]
        first_shard = min(methods.index(name) for name in self.SHARD_METHODS)
        first_probe = methods.index("eth_getCode")
        self.assertEqual(
            methods[first_probe:first_probe + len(probed)], ["eth_getCode"] * len(probed)
        )
        self.assertLess(first_probe + len(probed), first_shard)
        # Only the finality binding came before them.
        self.assertTrue(all("finality" in label for _method, label in calls[:first_probe]))
        # No other subject was probed or read twice.
        code_reads = [label for method, label in calls if method == "eth_getCode"]
        self.assertEqual(len(code_reads), len(probed) + 136)
        # The journal holds the probes as its first opening reads, both sides
        # of the boundary among them.
        entries = existing.opening_entries(staging)
        answers = {}
        for entry in entries[:len(probed)]:
            request = json.loads(entry["request"])
            self.assertEqual((request["method"], request["params"][0]), ("eth_getCode", COLLATERAL_STORAGE))
            answers[int(request["params"][1], 16)] = json.loads(entry["response"])["result"]
        self.assertEqual(list(answers), probed)
        self.assertEqual(answers[self.OBSERVED - 1], "0x")
        self.assertEqual(answers[self.OBSERVED], self.state["code"][COLLATERAL_STORAGE])
        # The second transport re-read every one of them and agreed.
        self.assertEqual(document["reconciliation"]["status"], "agreed")
        # 159 with code at the start (including the 3 trace identities); here
        # the probes and one more subject header replace that single read.
        self.assertEqual(document["reconciliation"]["compared"], 159 + len(probed))
        self.assertEqual(len(entries), 139 + len(probed))
        receipt = existing.component_document(output, "epoch-table")
        self.assertEqual(receipt["first_code"], [{
            "code_block": str(self.OBSERVED), "empty_block": str(self.OBSERVED - 1),
            "opening": "observed-block", "subject": COLLATERAL_STORAGE,
        }])
        epoch = epoch_row(receipt, COLLATERAL_STORAGE)["epochs"][0]
        self.assertEqual(epoch["start_block"], str(self.OBSERVED))
        self.assertEqual(epoch["start_hash"], WildcatTransport(self.state)._hash(self.OBSERVED))
        self.assertEqual(
            epoch["implementation_code_sha256"],
            hashlib.sha256(bytes.fromhex(self.state["code"][COLLATERAL_STORAGE][2:])).hexdigest(),
        )
        schema = json.loads((PLUGIN / "schemas" / "interval-receipt-v3.schema.json").read_text())
        self.assertEqual(schema_errors(schema, receipt), [])
        self.assertEqual(check_interval(output)["epochs"], 137)
        for name in EVIDENCE_COMPONENTS:
            (gap,) = self.storage_gaps(output, name)
            self.assertIn("deployment block is not established", gap)
            self.assertIn(f"no code for it at block {self.OBSERVED - 1}", gap)
            self.assertIn(f"runtime code at block {self.OBSERVED}", gap)
            self.assertIn("not a recorded deployment block", gap)

    def test_no_code_at_the_interval_end_refuses_before_any_shard(self):
        staging = self.scratch("never")
        transport = WildcatTransport(self.state, case="no-code-at-the-interval-end")
        collector = Collector(self.plan, staging, transport, registry=self.registry)
        with self.assertRaisesRegex(
            AlexandriaError,
            f"subject {COLLATERAL_STORAGE} has no recorded creation block and no runtime code at "
            "the interval end",
        ):
            collector.collect()
        # The finality binding, the probe at the start and the probe at the end: nothing else.
        after_finality = [(m, label) for m, label in transport.calls if "finality" not in label]
        self.assertEqual([method for method, _label in after_finality], ["eth_getCode", "eth_getCode"])
        self.assertFalse(self.SHARD_METHODS & {method for method, _label in transport.calls})
        self.assertEqual(existing.opening_entries(staging), [])
        self.assertEqual(existing.journals(staging).get("logs", b""), b"")
        receipts = [
            json.loads(line) for line in (staging / "receipts" / "errors.jsonl").read_bytes().splitlines()
        ]
        self.assertEqual([receipt["code"] for receipt in receipts], ["no-code-at-interval-end"])
        self.assertEqual(collector.staging._handles, {})

    def test_a_second_transport_that_places_the_boundary_elsewhere_is_disputed(self):
        state = deepcopy(self.state)
        state["first_code_cases"]["second"] = {COLLATERAL_STORAGE: self.OBSERVED - 4}
        self.state = state
        staging, document = self.staged_case("second", "no-code-at-the-interval-start", "second")
        self.assertEqual(document["reconciliation"]["status"], "disputed")
        disputed = [(item["kind"], item["identity"]) for item in document["reconciliation"]["disputed"]]
        self.assertIn(("code-digest", f"code of {COLLATERAL_STORAGE} at block {self.OBSERVED - 1}"), disputed)
        self.assertTrue(all(kind == "code-digest" and COLLATERAL_STORAGE in identity for kind, identity in disputed))
        kept = (staging / "reconciliation" / "disputed.jsonl").read_bytes().splitlines()
        self.assertEqual(len(kept), len(disputed))

    def test_check_refuses_first_code_rows_the_preserved_reads_do_not_give(self):
        _staging, _document, output = self.released_case("edited", "no-code-at-the-interval-start")
        path = existing.component_path(output, "epoch-table")
        released = path.read_bytes()
        self.check_without_verify(output)
        start = self.plan["interval"]["start"]
        edits = {
            "a code block that is not the epoch's first": (
                lambda row: row.update(code_block=str(self.OBSERVED + 1), empty_block=str(self.OBSERVED)),
                "do not bracket its epoch's first block",
            ),
            "an empty read two blocks back": (
                lambda row: row.update(empty_block=str(self.OBSERVED - 2)),
                "do not bracket its epoch's first block",
            ),
            "an observed block passed off as the interval start": (
                lambda row: row.update(opening="interval-start", empty_block=None),
                "names another block or an empty read",
            ),
            "an unknown opening": (lambda row: row.update(opening="recorded"), "unknown opening"),
            "an empty block that is a number": (
                lambda row: row.update(empty_block=self.OBSERVED - 1), "do not bracket",
            ),
        }
        for label, (edit, message) in edits.items():
            with self.subTest(edit=label):
                path.write_bytes(released)
                self.rewrite(output, "epoch-table", lambda receipt: edit(receipt["first_code"][0]))
                with self.assertRaisesRegex(AlexandriaError, message):
                    self.check_without_verify(output)
        path.write_bytes(released)
        self.rewrite(output, "epoch-table", lambda receipt: receipt["first_code"].clear())
        with self.assertRaisesRegex(AlexandriaError, "do not match the opening reads"):
            self.check_without_verify(output)
        # An epoch moved to the interval start, with its row: the preserved probes disagree.
        path.write_bytes(released)

        def moved(receipt):
            epoch = epoch_row(receipt, COLLATERAL_STORAGE)["epochs"][0]
            epoch.update(start_block=start, start_position=dict(epoch["start_position"], block_number=start))
            receipt["first_code"][0].update(code_block=start, empty_block=None, opening="interval-start")

        self.rewrite(output, "epoch-table", moved)
        with self.assertRaises(AlexandriaError):
            self.check_without_verify(output)
        path.write_bytes(released)
        self.check_without_verify(output)

    def test_a_dropped_or_swapped_gap_sentence_does_not_check(self):
        _staging, _document, output = self.released_case("gap", "no-code-at-the-interval-start")
        path = output / "manifest.json"
        manifest = json.loads(path.read_text())
        gaps = next(c for c in manifest["captures"] if c["id"] == "logs")["coverage"]["gaps"]
        index = next(i for i, gap in enumerate(gaps) if COLLATERAL_STORAGE in gap)
        gaps[index] = wildcat_v2._missing_block_gap(COLLATERAL_STORAGE, {
            "code_block": self.plan["interval"]["start"], "empty_block": None,
            "opening": "interval-start", "subject": COLLATERAL_STORAGE,
        })
        path.write_bytes(canonical_bytes(manifest))
        with self.assertRaisesRegex(AlexandriaError, "logs coverage does not name a gap its venue owes"):
            self.check_without_verify(output)

    def test_a_run_stopped_among_the_shards_asks_the_probes_again_and_journals_them_once(self):
        def stop(_envelope):
            raise AlexandriaError("constructed interruption")

        staging = self.scratch("stopped")
        first = WildcatTransport(self.state, case="no-code-at-the-interval-start", faults={"shard 2 logs": stop})
        with self.assertRaisesRegex(AlexandriaError, "constructed interruption"):
            Collector(self.plan, staging, first, registry=self.registry).collect()
        # Two shards are committed and no opening read is: a checkpoint cannot
        # commit one while a shard is uncollected.
        self.assertEqual(existing.checkpoint(staging)["next_shard"], 2)
        self.assertEqual(existing.checkpoint(staging)["offsets"][OPENING_CLASS], 0)
        second = WildcatTransport(self.state, case="no-code-at-the-interval-start")
        summary = Collector(self.plan, staging, second, registry=self.registry).collect()
        probed = self.probes(second.calls)
        self.assertEqual(probed, self.probes(first.calls))
        # Two first headers besides the interval's own, 136 recorded code reads, and the probes.
        self.assertEqual(summary["opening_reads"]["total"], 139 + len(probed))
        # The probes asked before the shards are this run's reads too.
        self.assertEqual(summary["opening_reads"]["issued"], 139 + len(probed))
        self.assertEqual(len(existing.opening_entries(staging)), 139 + len(probed))
        Reconciler(
            self.plan, staging, WildcatTransport(self.state, case="no-code-at-the-interval-start"),
            SECOND_PROVIDER, registry=self.registry,
        ).reconcile()
        output = self.root / "stopped-release"
        Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(output)
        self.assertEqual(check_interval(output)["epochs"], 137)
        # A finished tree collected again asks nothing: every opening read is replayed.
        third = WildcatTransport(self.state, case="no-code-at-the-interval-start")
        again = Collector(self.plan, staging, third, registry=self.registry).collect()
        self.assertEqual(again["opening_reads"]["issued"], 0)
        self.assertNotIn("eth_getCode", [method for method, _label in third.calls])

    def test_the_probe_bound_holds_at_the_edges(self):
        self.assertEqual(wildcat_v2.max_probes(100, 100), 1)
        self.assertEqual(wildcat_v2.max_probes(100, 101), 2)
        self.assertEqual(wildcat_v2.max_probes(100, 102), 3)
        self.assertEqual(wildcat_v2.max_probes(0, 2 ** 20), 22)
        self.assertEqual(wildcat_v2.max_probes(0, 2 ** 20 + 1), 23)
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        for first in (start + 1, start + 2, end - 1, end):
            with self.subTest(first_code_block=first):
                state = deepcopy(self.state)
                state["first_code_cases"]["edge"] = {COLLATERAL_STORAGE: first}
                transport = WildcatTransport(state, case="edge")
                phase = wildcat_v2.opening_phase(self.plan, self.registry, [])
                asked = 0
                for read in phase.preliminary_reads():
                    asked += 1
                    phase.accept(read, transport.code(read["address"], read["block"]))
                self.assertLessEqual(asked, wildcat_v2.max_probes(start, end))
                self.assertEqual(phase.first_code_rows(), [{
                    "code_block": str(first), "empty_block": str(first - 1),
                    "opening": "observed-block", "subject": COLLATERAL_STORAGE,
                }])
                # Both sides of the reported boundary are reads the phase accepted.
                self.assertEqual(phase.probes[(COLLATERAL_STORAGE, first - 1)], "")
                self.assertTrue(phase.probes[(COLLATERAL_STORAGE, first)])

    def test_a_probe_drawn_before_its_predecessor_is_answered_refuses(self):
        phase = wildcat_v2.opening_phase(self.plan, self.registry, [])
        reads = phase.preliminary_reads()
        next(reads)
        with self.assertRaisesRegex(AlexandriaError, "was not answered before the next"):
            next(reads)
        with self.assertRaisesRegex(AlexandriaError, "first block was not observed"):
            wildcat_v2.opening_phase(self.plan, self.registry, []).first_code_rows()
        with self.assertRaisesRegex(AlexandriaError, "no opening read says where its epoch opened"):
            wildcat_v2.evidence_gaps(self.plan, self.registry, [], [])


class HeldProbeTests(WildcatCase):
    """What a stopped run leaves, and that resuming reproduces the uninterrupted journals."""

    CASE = "no-code-at-the-interval-start"
    PROBES = 8

    def transport(self, **kwargs):
        return WildcatTransport(self.state, case=self.CASE, **kwargs)

    @staticmethod
    def files(root):
        return {
            str(path.relative_to(root)): path.read_bytes()
            for path in sorted(Path(root).rglob("*"))
            if path.is_file() and "receipts" not in path.parts
        }

    def collected(self, name, transport):
        root = self.scratch(name)
        return root, Collector(self.plan, root, transport, registry=self.registry)

    def uninterrupted(self):
        root, collector = self.collected("uninterrupted", self.transport())
        collector.collect()
        return self.files(root)

    @staticmethod
    def stop(_envelope):
        raise AlexandriaError("constructed stop")

    def test_a_run_stopped_at_three_points_resumes_to_the_same_bytes(self):
        expected = self.uninterrupted()
        start = self.plan["interval"]["start"]
        points = {
            # After the probes, before the first shard: nothing is on disk.
            "before the first shard": ("shard 0 boundary-blocks", {}, self.PROBES),
            # After the held probes are journaled: they are committed and replayed.
            "after the probes are journaled": (
                f"opening read {self.PROBES} first-block-header block {start}", None, 0,
            ),
        }
        for label, (fault, left, asked_again) in points.items():
            with self.subTest(stopped=label):
                root, collector = self.collected(
                    re.sub(r"\W", "-", label), self.transport(faults={fault: self.stop})
                )
                with self.assertRaisesRegex(AlexandriaError, "constructed stop"):
                    collector.collect()
                if left is not None:
                    self.assertEqual(self.files(root), left)
                else:
                    self.assertEqual(len(existing.opening_entries(root)), self.PROBES)
                resumed = self.transport()
                Collector(self.plan, root, resumed, registry=self.registry).collect()
                self.assertEqual(
                    sum("first-code-probe" in name for _method, name in resumed.calls), asked_again
                )
                self.assertEqual(self.files(root), expected)

    def test_a_run_stopped_as_the_first_held_probe_is_journaled_asks_them_again(self):
        expected = self.uninterrupted()
        root, collector = self.collected("first-record", self.transport())
        record = collector.staging.record

        def refusing(shard, name, request, response, **kwargs):
            if name == OPENING_CLASS:
                raise AlexandriaError("constructed stop at the first opening record")
            return record(shard, name, request, response, **kwargs)

        with mock.patch.object(collector.staging, "record", side_effect=refusing):
            with self.assertRaisesRegex(AlexandriaError, "constructed stop"):
                collector.collect()
        # Every shard is committed and no opening read is.
        self.assertEqual(existing.checkpoint(root)["next_shard"], len(self.plan["shards"]))
        self.assertEqual(existing.checkpoint(root)["offsets"][OPENING_CLASS], 0)
        resumed = self.transport()
        Collector(self.plan, root, resumed, registry=self.registry).collect()
        self.assertEqual(
            sum("first-code-probe" in name for _method, name in resumed.calls), self.PROBES
        )
        self.assertEqual(self.files(root), expected)

    def test_a_reorg_rewind_drops_the_journaled_probes_and_asks_them_again(self):
        root, collector = self.collected("reorg", self.transport())
        collector.collect()
        moved = self.plan["shards"][2]["start"] + 3
        again = self.transport(reorg_from=moved)
        summary = Collector(self.plan, root, again, registry=self.registry).collect()
        self.assertEqual(summary["resumed_from"], 2)
        self.assertEqual(
            sum("first-code-probe" in name for _method, name in again.calls), self.PROBES
        )
        self.assertEqual(
            summary["opening_reads"], {"issued": 147, "resumed_from": 0, "total": 147}
        )
        Reconciler(
            self.plan, root, self.transport(reorg_from=moved), SECOND_PROVIDER, registry=self.registry,
        ).reconcile()
        output = self.root / "reorg-release"
        Builder(self.plan, root, self.registry, created_at=CREATED_AT).build(output)
        self.assertEqual(check_interval(output)["epochs"], 137)

    def test_held_bytes_for_another_request_are_not_journaled(self):
        root, collector = self.collected("other-held", self.transport())
        preliminary = collector._preliminary_reads

        def swapped():
            preliminary()
            payload, data, result = collector._held[0]
            collector._held[0] = (payload + b" ", data, result)

        with mock.patch.object(collector, "_preliminary_reads", side_effect=swapped):
            collector.collect()
        # The first probe was asked twice: once held, and once more because
        # the held request was not the one its position names.
        first = f"opening read 0 first-code-probe block {self.plan['interval']['start']}"
        self.assertEqual(sum(name == first for _method, name in collector.transport.calls), 2)
        self.assertEqual(self.files(root), self.uninterrupted())

    def test_a_probe_answer_that_is_not_code_refuses_before_any_shard(self):
        label = f"opening read 0 first-code-probe block {self.plan['interval']['start']}"
        for index, specimen in enumerate((None, 7, {}, [], "0xzz", "0x1", "60806040")):
            with self.subTest(answer=specimen):
                answer = lambda envelope, value=specimen: canonical_bytes(  # noqa: E731
                    {"id": envelope["id"], "jsonrpc": "2.0", "result": value}
                )
                transport = self.transport(faults={label: answer})
                root, collector = self.collected(f"answer-{index}", transport)
                with self.assertRaises(Exception) as raised:
                    collector.collect()
                self.assertIsInstance(raised.exception, AlexandriaError)
                self.assertFalse({"eth_getLogs", "trace_transaction"} & {m for m, _name in transport.calls})


class BisectionEdgeTests(WildcatCase):
    """Termination and bounds where the interval or the boundary is at an edge."""

    def drive(self, start, end, answer):
        plan = deepcopy(self.plan)
        plan["interval"] = {"start": str(start), "end": str(end)}
        plan["shards"] = interval.plan_shards(start, end, plan["shard_width"])
        interval.validate_plan(plan)
        phase = wildcat_v2.opening_phase(plan, self.registry, [])
        asked = []
        for read in phase.preliminary_reads():
            asked.append(read["block"])
            phase.accept(read, answer(read["block"]))
        return asked, phase

    def test_intervals_of_one_and_two_blocks(self):
        base = int(self.plan["interval"]["start"])
        code = self.state["code"][COLLATERAL_STORAGE]
        asked, phase = self.drive(base, base, lambda block: code)
        self.assertEqual((asked, phase.first_code_rows()[0]["opening"]), ([base], "interval-start"))
        with self.assertRaisesRegex(AlexandriaError, "no runtime code at the interval end"):
            self.drive(base, base, lambda block: "0x")
        asked, phase = self.drive(base, base + 1, lambda block: code if block > base else "0x")
        self.assertEqual(asked, [base, base + 1])
        self.assertEqual(
            (phase.first_code_rows()[0]["empty_block"], phase.first_code_rows()[0]["code_block"]),
            (str(base), str(base + 1)),
        )
        with self.assertRaisesRegex(AlexandriaError, "no runtime code at the interval end"):
            self.drive(base, base + 1, lambda block: "0x")

    def test_every_first_code_block_in_the_interval_is_found_within_the_bound(self):
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        code = self.state["code"][COLLATERAL_STORAGE]
        worst = 0
        for first in range(start + 1, end + 1):
            asked, phase = self.drive(start, end, lambda block, first=first: code if block >= first else "0x")
            row = phase.first_code_rows()[0]
            self.assertEqual((row["empty_block"], row["code_block"]), (str(first - 1), str(first)))
            self.assertEqual(len(asked), len(set(asked)))
            worst = max(worst, len(asked))
        self.assertEqual(worst, wildcat_v2.max_probes(start, end))

    def test_answers_that_are_not_monotonic_still_end_on_a_pair_that_was_read(self):
        """A bisection cannot see code that comes and goes between its reads.

        Every block it has read below its lower bound was empty and every one
        above its upper bound had code, so no answer contradicts another. It
        neither loops nor invents a boundary: it ends within the bound on two
        adjacent blocks it read. What it misses is the collector document's
        stated limit.
        """
        start, end = (int(self.plan["interval"][key]) for key in ("start", "end"))
        code = self.state["code"][COLLATERAL_STORAGE]
        patterns = {
            "code, then none, then code": lambda b: code if start + 10 <= b <= start + 20 or b >= start + 61 else "0x",
            "code at the first midpoint only": lambda b: code if b == start + 39 or b >= start + 70 else "0x",
        }
        for label, answer in patterns.items():
            with self.subTest(pattern=label):
                asked, phase = self.drive(start, end, answer)
                row = phase.first_code_rows()[0]
                low, high = int(row["empty_block"]), int(row["code_block"])
                self.assertLessEqual(len(asked), wildcat_v2.max_probes(start, end))
                self.assertEqual(high, low + 1)
                self.assertIn(low, asked)
                self.assertIn(high, asked)
                self.assertEqual((answer(low), answer(high)), ("0x", code))


class FirstCodeReconciliationTests(WildcatCase):
    """One probe the second transport answers differently, or cannot answer."""

    CASE = "no-code-at-the-interval-start"
    OBSERVED = FirstCodeTests.OBSERVED
    staged_case = FirstCodeTests.staged_case
    released_case = FirstCodeTests.released_case

    def reconciled(self, name, faults):
        staging = self.scratch(f"{name}-staging")
        Collector(
            self.plan, staging, WildcatTransport(self.state, case=self.CASE), registry=self.registry
        ).collect()
        second = WildcatTransport(self.state, case=self.CASE, faults=faults)
        document = Reconciler(
            self.plan, staging, second, SECOND_PROVIDER, registry=self.registry
        ).reconcile()
        self.assertEqual(sum(name in faults for _method, name in second.calls), 1)
        return staging, document

    def answer(self, value):
        return lambda envelope: canonical_bytes(
            {"id": envelope["id"], "jsonrpc": "2.0", "result": value}
        )

    def test_exactly_one_probe_answered_differently_is_exactly_one_dispute(self):
        code = self.state["code"][COLLATERAL_STORAGE]
        specimens = {
            "empty at the code block": (6, self.OBSERVED, "0x"),
            "code at the empty block": (7, self.OBSERVED - 1, code),
            "other code at the interval end": (1, int(self.plan["interval"]["end"]), "0x60806040" + "cd" * 16),
        }
        for label, (position, block, value) in specimens.items():
            with self.subTest(second=label):
                fault = f"opening read {position} first-code-probe block {block} second provider"
                _staging, document = self.reconciled(re.sub(r"\W", "-", label), {fault: self.answer(value)})
                record = document["reconciliation"]
                self.assertEqual(record["status"], "disputed")
                self.assertEqual(record["compared"] - record["matched"], 1)
                self.assertEqual(record["disputed"], [{
                    "identity": f"code of {COLLATERAL_STORAGE} at block {block}",
                    "kind": "code-digest", "shard": len(self.plan["shards"]),
                }])

    def test_a_second_transport_that_cannot_serve_a_probe_leaves_the_interval_unreconciled(self):
        def cannot(_envelope):
            raise AlexandriaError("constructed: state pruned")

        end = self.plan["interval"]["end"]
        fault = f"opening read 1 first-code-probe block {end} second provider"
        errors = {
            "a transport failure": cannot,
            "an error object": lambda envelope: canonical_bytes({
                "id": envelope["id"], "jsonrpc": "2.0",
                "error": {"code": -32000, "message": "missing trie node"},
            }),
        }
        for label, answer in errors.items():
            with self.subTest(second=label):
                staging, document = self.reconciled(re.sub(r"\W", "-", label), {fault: answer})
                self.assertEqual(document["reconciliation"]["status"], "unreconciled")
                self.assertEqual(document["reconciliation"]["disputed"], [])
                output = self.root / f"{re.sub(r'[^a-z]', '-', label)}-release"
                Builder(self.plan, staging, self.registry, created_at=CREATED_AT).build(output)
                self.assertEqual(check_interval(output)["reconciliation"], "unreconciled")
                for name in EVIDENCE_COMPONENTS:
                    coverage = self.captures(output)[name]["coverage"]
                    self.assertEqual(coverage["status"], "partial")
                    self.assertIn("the interval was not reconciled against a second provider", coverage["gaps"])

    def test_check_refuses_a_first_code_row_for_a_subject_with_a_recorded_block(self):
        _staging, _document, output = self.released_case("recorded-row", self.CASE)
        path = existing.component_path(output, "epoch-table")
        released = path.read_bytes()
        row = {
            "code_block": str(DEPLOY_BLOCK), "empty_block": str(DEPLOY_BLOCK - 1),
            "opening": "observed-block", "subject": NEW_MARKET,
        }
        # The row brackets that subject's first block, so only the preserved reads refuse it.
        receipt = json.loads(released)
        interval.validate_first_code([row], epoch_table(receipt), int(self.plan["interval"]["start"]))
        edits = {
            "beside the unrecorded subject's row": (
                lambda rows: rows.__setitem__(slice(None), sorted(rows + [row], key=lambda r: r["subject"])),
                "do not match the opening reads",
            ),
            "in place of it": (lambda rows: rows.__setitem__(slice(None), [row]), "do not match the opening reads"),
            "two rows for one subject": (lambda rows: rows.append(dict(rows[0])), "repeat a subject"),
            "rows out of order": (
                lambda rows: rows.__setitem__(
                    slice(None), sorted(rows + [row], key=lambda r: r["subject"], reverse=True)
                ),
                "ascending subject order",
            ),
        }
        for label, (edit, message) in edits.items():
            with self.subTest(edit=label):
                path.write_bytes(released)
                self.rewrite(output, "epoch-table", lambda r: edit(r["first_code"]))
                with self.assertRaisesRegex(AlexandriaError, message):
                    self.check_without_verify(output)
        path.write_bytes(released)
        self.check_without_verify(output)


class ExitClauseTests(WildcatCase):
    """Clauses of the step's Exit and Tests that no other case pins over the whole estate."""

    def test_the_estates_80_preserved_deploy_events_agree_with_the_registry(self):
        """Every declared market, not only the one inside the fixture interval."""
        estate = json.loads((REPO_ROOT / wildcat_registry.ESTATE_PATH).read_text(encoding="utf-8"))
        factory = next(e["address"] for e in self.registry["entries"] if e["role"] == "factory")
        events = [e for e in estate["factory_events"]["events"] if e["event"] == "MarketDeployed"]
        self.assertEqual(len(events), 80)
        logs = []
        for event in events:
            number = event["block_number"]
            logs.append({
                "address": factory, "topics": event["topics"],
                "blockNumber": number if isinstance(number, str) else hex(number),
            })
        blocks = [int(log["blockNumber"], 16) for log in logs]
        plan = deepcopy(self.plan)
        plan["interval"] = {"start": str(min(blocks)), "end": str(max(blocks))}
        report = wildcat_v2.market_deploy_report(plan, self.registry, logs)
        self.assertTrue(report["compared"])
        self.assertEqual((report["declared"], len(report["expected"]), len(report["observed"])), (80, 80, 80))
        self.assertEqual((report["missing"], report["misplaced"], report["undeclared"]), ([], [], []))
        # One event moved by a block is the disagreement the release would report.
        logs[0] = dict(logs[0], blockNumber=hex(blocks[0] + 1))
        moved = wildcat_v2.market_deploy_report(plan, self.registry, logs)
        self.assertEqual(len(moved["misplaced"]), 1)

    def test_every_split_evidence_scope_says_which_opening_applied(self):
        state = deepcopy(self.state)
        state["plan"]["shards_per_component"] = 1
        case = "no-code-at-the-interval-start"
        staging = self.scratch("split-staging")
        Collector(state["plan"], staging, WildcatTransport(state, case=case), registry=self.registry).collect()
        Reconciler(
            state["plan"], staging, WildcatTransport(state, case=case), SECOND_PROVIDER,
            registry=self.registry,
        ).reconcile()
        output = self.root / "split"
        Builder(state["plan"], staging, self.registry, created_at=CREATED_AT).build(output)
        self.assertEqual(check_interval(output)["epochs"], 137)
        scopes = [c for c in self.captures(output).values() if c["evidence_class"] == "recorded-rpc"]
        # Three classes over four components, and the one opening journal.
        self.assertEqual(len(scopes), 13)
        for capture in scopes:
            with self.subTest(scope=capture["id"]):
                gaps = capture["coverage"]["gaps"]
                named = [gap for gap in gaps if COLLATERAL_STORAGE in gap]
                self.assertEqual(len(named), 1)
                self.assertIn("not a recorded deployment block", named[0])
                self.assertEqual(sum("constructed rather than collected" in gap for gap in gaps), 1)

    def test_the_registry_capture_speaks_of_an_epoch_only_for_a_declared_subject(self):
        declared = [gap for gap in wildcat_v2.gaps(self.registry, self.plan) if COLLATERAL_STORAGE in gap]
        self.assertEqual(len(declared), 1)
        self.assertIn("its epoch opens at the interval start when", declared[0])
        self.assertEqual(wildcat_v2.gaps(self.registry), wildcat_v2.gaps(self.registry, None))
        plan = deepcopy(self.plan)
        plan["subjects"].remove(COLLATERAL_STORAGE)
        undeclared = [gap for gap in wildcat_v2.gaps(self.registry, plan) if COLLATERAL_STORAGE in gap]
        self.assertEqual(len(undeclared), 1)
        self.assertIn("deployment block is not established", undeclared[0])
        self.assertNotIn("epoch", undeclared[0])
        self.assertTrue(any("1 of the 137" in gap for gap in wildcat_v2.gaps(self.registry, plan)))
        # With the subject undeclared there is no first-code row and no evidence-scope sentence.
        self.assertEqual(
            [gap for gap in wildcat_v2.evidence_gaps(plan, self.registry, [], []) if COLLATERAL_STORAGE in gap],
            [],
        )
        schema = json.loads((PLUGIN / "schemas" / "interval-receipt-v3.schema.json").read_text())
        self.assertIn("declared subject", schema["properties"]["first_code"]["description"])

    def test_the_plan_time_estimate_is_the_figure_the_collector_document_gives(self):
        entries = wildcat_registry.subject_entries(self.registry)
        cost = lambda subject: 2 * entries[subject]["code_length"] + wildcat_v2.OPENING_ENTRY_OVERHEAD  # noqa: E731
        once = sum(cost(subject) for subject in entries)
        long = once + (wildcat_v2.max_probes(21866550, 25960042) - 1) * cost(COLLATERAL_STORAGE)
        self.assertEqual((round(once / 1e6, 1), round(long / 1e6, 1)), (5.6, 6.0))
        document = (PLUGIN / "docs" / "usdc-interval-collector.md").read_text(encoding="utf-8")
        self.assertIn("about\n5.6 MB of it read once each", document)
        self.assertIn("about 6.0 MB over an interval of 4.1 million blocks", document)


class FixtureTests(unittest.TestCase):
    def test_the_fixture_declares_the_registrys_subjects_and_says_it_is_constructed(self):
        state = fixture()
        self.assertEqual(
            state["plan"]["subjects"], [entry["address"] for entry in registry()["entries"]]
        )
        self.assertEqual(
            set(state), (set(existing.fixture()) - {"slots"}) | {"first_code_cases"},
            "the constructed fixture follows the Compound fixture's shape, without slot words, "
            "and adds the first-code cases",
        )
        self.assertEqual(
            state["first_code_cases"],
            {
                "no-code-at-the-interval-end": {COLLATERAL_STORAGE: int(state["plan"]["interval"]["end"]) + 1},
                "no-code-at-the-interval-start": {COLLATERAL_STORAGE: 25895371},
            },
        )
        self.assertEqual(set(state["code"]), set(state["plan"]["subjects"]))
        self.assertIn("was not observed on any chain", state["note"])
        interval.validate_plan(state["plan"])


if __name__ == "__main__":
    unittest.main()
