"""The part form of a release statement: projection, bounds and schemas.

The design record's `part-projection-verifies` cell loads the five tests of
`StatementPartProjectionTests` by name. They share one 16,384-component,
16,384-capture release whose single statement exceeds Ariadne's input limit.
The other classes hold each bound at its value and one past it, tie the bounds
to Ariadne's own constants, keep the in-tree pinned statements byte for byte,
and hold both part schemas to the emitted field sets.

Ariadne runs as a stranger runs it, one `ariadne.py verify` child process a
file with its default bounds. Its envelope and gate modules are imported only
to build an unsigned DSSE envelope and to count scanned keys.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PLUGIN_ROOT.parents[1]
FIXTURES = PLUGIN_ROOT / "tests" / "fixtures"
SCHEMAS = PLUGIN_ROOT / "schemas"
ARIADNE_SCRIPTS = REPO_ROOT / "plugins" / "ariadne" / "scripts"
ARIADNE = ARIADNE_SCRIPTS / "ariadne.py"
ARIADNE_SAFEJSON = ARIADNE_SCRIPTS / "ariadne_lib" / "safejson.py"
ARIADNE_CORE_PREDICATE = ARIADNE_SCRIPTS / "ariadne_lib" / "core_predicate.py"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
if str(ARIADNE_SCRIPTS) not in sys.path:
    sys.path.append(str(ARIADNE_SCRIPTS))

from alexandria_lib import emit_statement, ingest  # noqa: E402
from alexandria_lib import release as release_module  # noqa: E402
from alexandria_lib import statement as statement_module  # noqa: E402
from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from ariadne_lib import envelope as ariadne_envelope  # noqa: E402
from ariadne_lib import gates as ariadne_gates  # noqa: E402
from ariadne_lib import statement as ariadne_statement  # noqa: E402
from tests import test_statement as single_statement_tests  # noqa: E402
from tests.test_release_limits import (  # noqa: E402
    synthetic_manifest,
    write_synthetic_release,
)
from tests.test_wildcat_venue import schema_errors  # noqa: E402


PART_SCHEMA = SCHEMAS / "release-statement-part-v1.schema.json"
INDEX_SCHEMA = SCHEMAS / "release-statement-parts-v1.schema.json"
SINGLE_SCHEMA = SCHEMAS / "release-statement-v1.schema.json"
HEAVY_GAPS = 7
HEAVY_GAP_CHARACTERS = 941
FIXTURE_STATEMENT_SHA256 = "041c699bdefc8be359c88d738a8c5b45002e044b6226534d52bace7c09796c43"

# The study's section 3 statements whose release the tree holds or builds:
# label -> (release identifier, SHA-256 of the statement the base emitted).
# The two Wildcat releases live outside the tree; the integration cell reads
# them from ALEXANDRIA_WILDCAT_V1_RELEASE and ALEXANDRIA_WILDCAT_V2_RELEASE.
PINNED = {
    "fixture": ("sha256:e86550e59baba75258093ed4b67c144d1dd520c68f0411d23ba59af050f3fed6",
                FIXTURE_STATEMENT_SHA256),
    "credit-history-raw": ("sha256:6117658c59c96e9ca32594ffe09e994d478dc7d9f2d3799c64bb25050c7fe0e2",
                           "d4846fd64852e5a8e34615679a252a7729976d1278b3be1ec177e1bc2da92fd2"),
    "credit-history-derived": ("sha256:fccc014cd400f553814b58911bb06cd450f395e6145e21c0071a06b092b181ec",
                               "3b12aa332fcf45cff14fb9a7d1c5f379852d3858c6cf56dcea57c26fc78523e6"),
    "usdc-interval-v0": ("sha256:7cf794f07cb74c0383ae3fdd270758324b8036705c9845a7724043993dde40aa",
                         "c92e6cbb3b953acc3ad11e456cf5ca4715b5b2e8dbc98872a15e0c7c455716cf"),
    "usdc-interval-live-v0": ("sha256:30c4e9724b1d7bcb32d95fb6090ca4eed51f837a39779ead7d4b723b2e2b3b32",
                              "64df112deab0c91fe3da1aef1196a3a9226adee0cebc977468b3a609b4bc921f"),
    "usdc-interval-epochs-synthetic": ("sha256:b71996c8450d5f28c36d112fab7bafb636b2176d74e6f609646dbe5162983036",
                                       "656e225fbd67321230f58ff943a9dea3fc6ac265af8dc88beacbae2ba8b81bdd"),
    "usdc-interval-epochs-live": ("sha256:42eb1651533a795b25977cec9e0ef683ebecd7c65ff558913077f5a4da2aad3a",
                                  "76334510a1434645e0f249f4015c0c5d0065c17d0eea5f9814a7c9d12cc53527"),
    "compound-v3-phase0": ("sha256:73db32c8e4dac528c9352362d6b12cae71af0824d2f69c89aa7ff1edba9321ab",
                           "4ebe969c40dbe77eacbe8848e530454596ecbb8ba9a07b3e6c49b11b41ca7a93"),
    "proof-backed-state": ("sha256:fcae7d62fb7bd25f1c90ffac71f81cbd9678f733165c3bcffc7f709515eeea0f",
                           "faaff30f38025379781f35a7289af80cb0e15c9c0ff9c3efd0b9c09f1c77efa5"),
}
DEMOS = {
    "credit-history-v0": {"raw-release": "credit-history-raw",
                          "derived-release": "credit-history-derived"},
    "usdc-interval-v0": {"release": "usdc-interval-v0"},
    "usdc-interval-live-v0": {"release": "usdc-interval-live-v0"},
    "usdc-interval-epochs-v0": {"synthetic-release": "usdc-interval-epochs-synthetic",
                                "live-release": "usdc-interval-epochs-live"},
}
COMMITTED = {
    "compound-v3-phase0": PLUGIN_ROOT / "examples" / "compound-v3-phase0-v0" / "release",
    "proof-backed-state": PLUGIN_ROOT / "examples" / "proof-backed-state-v0" / "release",
}


def child_environment():
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "NO_COLOR": "1",
            "PYTHONDONTWRITEBYTECODE": "1"}


def ariadne_verify(path: Path) -> subprocess.CompletedProcess:
    """One `ariadne.py verify` with its default bounds, as a stranger runs it."""
    return subprocess.run(
        [sys.executable, str(ARIADNE), "verify", str(path)],
        capture_output=True, text=True, check=False, env=child_environment(), timeout=600,
    )


def scanned_characters(body: bytes) -> int:
    """The key characters Ariadne's gates 4 and 7 scan, from Ariadne's own walk."""
    parsed = ariadne_statement.Statement.from_json(body)
    return sum(len(key) for key, _ in ariadne_gates.scanned(parsed))


def reseal(unsigned: dict) -> dict:
    unsigned = dict(unsigned)
    unsigned.pop("release_id", None)
    identity = release_module.sha256(
        canonical_bytes(unsigned, max_nodes=release_module.MAX_MANIFEST_NODES)
    )
    return dict(unsigned, release_id=identity)


def manifest_with_gaps(components: int, captures: int, gaps) -> dict:
    """`synthetic_manifest` with each capture's gaps replaced, resealed."""
    manifest = synthetic_manifest(components, captures)
    for capture in manifest["captures"]:
        capture["coverage"]["gaps"] = list(gaps)
    return reseal(manifest)


def heavy_manifest() -> dict:
    """16,384 components, each capture with seven 941-character gaps."""
    gaps = [f"g{k}" + "x" * (HEAVY_GAP_CHARACTERS - 2) for k in range(HEAVY_GAPS)]
    return manifest_with_gaps(
        release_module.MAX_COMPONENTS, release_module.MAX_CAPTURES, gaps
    )


def decoded(parts):
    return [(name, json.loads(body)) for name, body in parts]


def with_next_component(single, part, position):
    """`part` grown by the manifest's component at `position` and its captures."""
    grown = deepcopy(part)
    predicate = single["predicate"]
    component = predicate["components"][position]
    order = {capture["id"]: index for index, capture in enumerate(predicate["captures"])}
    captures = grown["predicate"]["captures"] + [
        capture for capture in predicate["captures"] if capture["component"] == component["name"]
    ]
    captures.sort(key=lambda capture: order[capture["id"]])
    grown["subject"].append(single["subject"][position + 1])
    grown["predicate"]["components"].append(component)
    grown["predicate"]["captures"] = captures
    grown["predicate"]["part"]["components"] += 1
    grown["predicate"]["part"]["captures"] = len(captures)
    return grown


def over_a_part_bound(statement) -> bool:
    body = canonical_bytes(statement, max_nodes=statement_module.MAX_STATEMENT_BYTES)
    return (
        len(body) > statement_module.MAX_PART_BYTES
        or statement_module.key_characters(statement)
        > statement_module.MAX_STATEMENT_KEY_CHARACTERS
    )


def merged_schema(schema: dict) -> dict:
    """One schema whose references to the single statement's definitions resolve locally."""
    single = json.loads(SINGLE_SCHEMA.read_text(encoding="utf-8"))
    prefix = single["$id"] + "#"

    def rewrite(value):
        if isinstance(value, dict):
            return {
                key: ("#" + item[len(prefix):] if key == "$ref" and isinstance(item, str)
                      and item.startswith(prefix) else rewrite(item))
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [rewrite(item) for item in value]
        return value

    merged = rewrite(schema)
    clashes = set(merged["$defs"]) & set(single["$defs"])
    if clashes:
        raise AssertionError(f"part schema definitions shadow the single schema's: {clashes}")
    merged["$defs"] = dict(single["$defs"], **merged["$defs"])
    return merged


def statement_errors(schema: dict, value: dict) -> list:
    """`schema_errors`, plus the subject array's `prefixItems` it does not read."""
    merged = merged_schema(schema)
    subject = merged["properties"]["subject"]
    errors = schema_errors(
        dict(merged, properties=dict(merged["properties"], subject={"type": "array"})),
        value, merged,
    )
    subjects = value.get("subject", [])
    if not subject["minItems"] <= len(subjects) <= subject["maxItems"]:
        errors.append("$.subject: has an item count outside its bounds")
    for position, item in enumerate(subjects):
        rule = subject["prefixItems"][position] if position < len(subject["prefixItems"]) else subject["items"]
        errors.extend(schema_errors(rule, item, merged, f"$.subject[{position}]"))
    return errors


def pinned_releases(scratch: Path) -> dict:
    releases = dict(COMMITTED)
    for demo, outputs in DEMOS.items():
        output = scratch / demo
        built = subprocess.run(
            [sys.executable, str(PLUGIN_ROOT / "examples" / demo / "demo.py"), "build",
             "--output", str(output)],
            capture_output=True, text=True, check=False, env=child_environment(), timeout=900,
        )
        if built.returncode != 0:
            raise AssertionError(f"{demo} did not build: {built.stderr[-2000:]}")
        for directory, label in outputs.items():
            releases[label] = output / directory
    inputs = scratch / "fixture-inputs"
    shutil.copytree(FIXTURES, inputs)
    releases["fixture"] = scratch / "fixture-release"
    ingest(inputs / "capture-plan.json", releases["fixture"])
    return releases


def fixture_release(scratch: Path) -> Path:
    inputs = scratch / "inputs"
    shutil.copytree(FIXTURES, inputs)
    release = scratch / "release"
    ingest(inputs / "capture-plan.json", release)
    return release


def verified_manifest(release: Path):
    release_id = release_module.verify(release)
    return release_id, statement_module._verified_manifest(release, release_id)


class StatementPartProjectionTests(unittest.TestCase):
    """The five cases the `part-projection-verifies` cell loads by name."""

    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory(prefix="alexandria-statement-parts-")
        cls.addClassCleanup(temporary.cleanup)
        cls.root = Path(temporary.name).resolve()
        release = cls.root / "light"
        written = write_synthetic_release(
            release, release_module.MAX_COMPONENTS, release_module.MAX_CAPTURES
        )
        cls.release_id, cls.manifest = verified_manifest(release)
        if cls.release_id != written:
            raise AssertionError("the synthetic release did not verify to its identifier")
        cls.single = statement_module.statement_for(cls.manifest)
        cls.single_bytes = len(canonical_bytes(
            cls.single, max_nodes=statement_module.MAX_STATEMENT_BYTES
        ))
        cls.projection = statement_module.project_statement(cls.manifest)

    def parts(self):
        self.assertIsInstance(self.projection, statement_module.StatementParts)
        return decoded(self.projection.parts)

    def test_a_release_past_the_limit_projects_into_parts_ariadne_verifies(self):
        self.assertEqual(len(self.manifest["components"]), 16_384)
        self.assertEqual(len(self.manifest["captures"]), 16_384)
        self.assertGreater(self.single_bytes, statement_module.MAX_STATEMENT_BYTES)
        self.assertIsInstance(self.projection, statement_module.StatementParts)
        files = [(statement_module.INDEX_NAME, self.projection.index), *self.projection.parts]
        self.assertGreater(len(files), 2)
        for form in ("bare", "dsse"):
            directory = self.root / f"verify-{form}"
            directory.mkdir()
            for name, body in files:
                data = (
                    body if form == "bare"
                    else ariadne_envelope.Envelope(body).to_json().encode("utf-8")
                )
                path = directory / name
                path.write_bytes(data)
                with self.subTest(form=form, file=name):
                    self.assertLessEqual(len(data), statement_module.MAX_STATEMENT_BYTES)
                    result = ariadne_verify(path)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_every_component_and_capture_lands_in_exactly_one_part_in_order(self):
        interleaved = synthetic_manifest(3_000, 6_000)
        for label, manifest, parts in (
            ("light", self.manifest, self.parts()),
            ("interleaved", interleaved,
             decoded(statement_module.project_statement(interleaved).parts)),
        ):
            with self.subTest(release=label):
                single = statement_module.statement_for(manifest)
                predicate = single["predicate"]
                order = {capture["id"]: index for index, capture in enumerate(predicate["captures"])}
                self.assertEqual(
                    [name for name, _ in parts],
                    [f"part-{number:05d}.json" for number in range(len(parts))],
                )
                first = 0
                placed = []
                for number, (_, part) in enumerate(parts):
                    body = part["predicate"]
                    names = {component["name"] for component in body["components"]}
                    positions = [order[capture["id"]] for capture in body["captures"]]
                    self.assertEqual(part["_type"], statement_module.STATEMENT_TYPE)
                    self.assertEqual(part["predicateType"], statement_module.PART_PREDICATE_TYPE)
                    self.assertEqual(part["subject"][0], single["subject"][0])
                    self.assertEqual(
                        part["subject"][1:],
                        single["subject"][first + 1:first + len(body["components"]) + 1],
                    )
                    self.assertEqual(
                        body["components"],
                        predicate["components"][first:first + len(body["components"])],
                    )
                    self.assertEqual(body["captures"], [
                        capture for capture in predicate["captures"] if capture["component"] in names
                    ])
                    self.assertEqual(positions, sorted(positions))
                    self.assertEqual(body["part"], {
                        "index": number, "first_component": first,
                        "components": len(body["components"]),
                        "captures": len(body["captures"]),
                    })
                    self.assertEqual(body["release"], predicate["release"])
                    self.assertEqual(body["claims"], predicate["claims"])
                    self.assertEqual(body["commands"], [])
                    first += len(body["components"])
                    placed.extend(positions)
                self.assertEqual(first, len(predicate["components"]))
                self.assertEqual(sorted(placed), list(range(len(predicate["captures"]))))

    def test_each_part_stays_within_the_part_limit_and_key_budget(self):
        parts = self.parts()
        encoded = dict(self.projection.parts)
        position = 0
        for number, (name, part) in enumerate(parts):
            with self.subTest(part=name):
                self.assertLessEqual(len(encoded[name]), statement_module.MAX_PART_BYTES)
                self.assertLessEqual(
                    statement_module.key_characters(part),
                    statement_module.MAX_STATEMENT_KEY_CHARACTERS,
                )
                self.assertEqual(encoded[name], canonical_bytes(
                    part, max_nodes=statement_module.MAX_STATEMENT_BYTES
                ))
                position += part["predicate"]["part"]["components"]
                if number + 1 < len(parts):
                    # Greedy: the next component would carry this part past a bound.
                    self.assertTrue(over_a_part_bound(
                        with_next_component(self.single, part, position)
                    ))
        index = json.loads(self.projection.index)
        self.assertLessEqual(len(self.projection.index), statement_module.MAX_PART_BYTES)
        self.assertLessEqual(
            statement_module.key_characters(index), statement_module.MAX_STATEMENT_KEY_CHARACTERS
        )

    def test_the_index_binds_every_part_by_digest(self):
        index = json.loads(self.projection.index)
        self.assertEqual(self.projection.index, canonical_bytes(index))
        self.assertEqual(index["_type"], statement_module.STATEMENT_TYPE)
        self.assertEqual(index["predicateType"], statement_module.INDEX_PREDICATE_TYPE)
        self.assertEqual(index["subject"][0], self.single["subject"][0])
        self.assertEqual(index["subject"][1:], [
            {"name": f"part/{name}", "digest": {"sha256": hashlib.sha256(body).hexdigest()}}
            for name, body in self.projection.parts
        ])
        self.assertEqual(index["predicate"], {
            "release": self.single["predicate"]["release"],
            "parts": {"count": len(self.projection.parts), "components": 16_384,
                      "captures": 16_384},
            "claims": self.single["predicate"]["claims"],
            "commands": [],
        })
        # A capture changed at the same length moves only its own part's bytes,
        # so exactly that part's digest in the index changes.
        changed = deepcopy(self.manifest)
        capture = changed["captures"][10_000]
        capture["coverage"]["gaps"] = ["synthetix"]
        moved = statement_module.project_statement(changed)
        owner = [
            number for number, (_, part) in enumerate(self.parts())
            if capture["id"] in {found["id"] for found in part["predicate"]["captures"]}
        ]
        before, after = index["subject"][1:], json.loads(moved.index)["subject"][1:]
        self.assertEqual(len(after), len(before))
        self.assertEqual(
            [number for number, (old, new) in enumerate(zip(before, after)) if old != new], owner
        )
        self.assertEqual(len(owner), 1)
        self.assertEqual(
            after[owner[0]]["digest"]["sha256"],
            hashlib.sha256(moved.parts[owner[0]][1]).hexdigest(),
        )

    def test_a_release_within_both_bounds_keeps_one_statement(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-statement-single-") as name:
            scratch = Path(name).resolve()
            release = fixture_release(scratch)
            _, manifest = verified_manifest(release)
            projected = statement_module.project_statement(manifest)
            self.assertIsInstance(projected, bytes)
            self.assertEqual(projected, canonical_bytes(statement_module.statement_for(manifest)))
            self.assertEqual(hashlib.sha256(projected).hexdigest(), FIXTURE_STATEMENT_SHA256)
            emitted = scratch / "statement.json"
            emit_statement(release, emitted)
            self.assertEqual(emitted.read_bytes(), projected)

            keys = statement_module.key_characters(json.loads(projected))
            for constant, value in (
                ("MAX_STATEMENT_BYTES", len(projected)),
                ("MAX_STATEMENT_KEY_CHARACTERS", keys),
            ):
                with self.subTest(bound=constant):
                    with mock.patch.object(statement_module, constant, value):
                        self.assertEqual(statement_module.project_statement(manifest), projected)
                    with mock.patch.object(statement_module, constant, value - 1):
                        self.assertIsInstance(
                            statement_module.project_statement(manifest),
                            statement_module.StatementParts,
                        )


class StatementPartBoundTests(unittest.TestCase):
    """Each bound at its value and one past, tied to Ariadne's own constants."""

    def test_the_key_budget_is_ariadnes_aggregate_scan_budget(self):
        budget = runpy.run_path(str(ARIADNE_CORE_PREDICATE))["MAX_STRUCTURED_KEY_CHARACTERS_TOTAL"]
        self.assertEqual(statement_module.MAX_STATEMENT_KEY_CHARACTERS, budget)
        self.assertEqual(statement_module.MAX_STATEMENT_KEY_CHARACTERS, 262_144)

    def test_the_part_limit_is_derived_from_ariadnes_input_limit(self):
        limit = runpy.run_path(str(ARIADNE_SAFEJSON))["DEFAULT_MAX_BYTES"]
        self.assertEqual(statement_module.MAX_PART_BYTES, limit * 3 // 4 - 65_536)
        self.assertEqual(statement_module.MAX_PART_BYTES, 6_225_920)
        base64_bytes = 4 * -(-statement_module.MAX_PART_BYTES // 3)
        self.assertEqual(base64_bytes, 8_301_228)
        self.assertEqual(limit - base64_bytes, 87_380)

    def test_key_characters_agrees_with_the_keys_ariadne_scans(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-statement-keys-") as name:
            _, manifest = verified_manifest(fixture_release(Path(name).resolve()))
            fixture = statement_module.project_statement(manifest)
        band = synthetic_manifest(2_000, 2_000)
        split = statement_module.project_statement(band)
        single = canonical_bytes(
            statement_module.statement_for(band), max_nodes=statement_module.MAX_STATEMENT_BYTES
        )
        for label, body in (
            ("fixture statement", fixture),
            ("2,000-component statement", single),
            ("index", split.index),
            *((name, body) for name, body in split.parts),
        ):
            with self.subTest(statement=label):
                self.assertEqual(
                    statement_module.key_characters(json.loads(body)), scanned_characters(body)
                )

    def test_a_release_under_the_byte_limit_but_over_the_key_budget_projects_into_parts(self):
        manifest = synthetic_manifest(2_000, 2_000)
        single = statement_module.statement_for(manifest)
        body = canonical_bytes(single, max_nodes=statement_module.MAX_STATEMENT_BYTES)
        self.assertLessEqual(len(body), statement_module.MAX_STATEMENT_BYTES)
        self.assertGreater(
            statement_module.key_characters(single), statement_module.MAX_STATEMENT_KEY_CHARACTERS
        )
        projection = statement_module.project_statement(manifest)
        self.assertIsInstance(projection, statement_module.StatementParts)
        self.assertGreater(len(projection.parts), 1)
        with tempfile.TemporaryDirectory(prefix="alexandria-statement-band-") as name:
            directory = Path(name)
            for part_name, data in [(statement_module.INDEX_NAME, projection.index),
                                    *projection.parts]:
                path = directory / part_name
                path.write_bytes(data)
                with self.subTest(file=part_name):
                    result = ariadne_verify(path)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_the_heavy_release_packs_by_bytes_rather_than_keys(self):
        manifest = heavy_manifest()
        release_module.validate_manifest(manifest)
        single = statement_module.statement_for(manifest)
        projection = statement_module.project_statement(manifest)
        self.assertIsInstance(projection, statement_module.StatementParts)
        parts = decoded(projection.parts)
        sizes = [len(body) for _, body in projection.parts]
        position = 0
        for number, (name, part) in enumerate(parts):
            with self.subTest(part=name):
                self.assertLessEqual(sizes[number], statement_module.MAX_PART_BYTES)
                self.assertLess(
                    statement_module.key_characters(part),
                    statement_module.MAX_STATEMENT_KEY_CHARACTERS,
                )
                position += part["predicate"]["part"]["components"]
                if number + 1 < len(parts):
                    grown = with_next_component(single, part, position)
                    self.assertGreater(
                        len(canonical_bytes(grown, max_nodes=statement_module.MAX_STATEMENT_BYTES)),
                        statement_module.MAX_PART_BYTES,
                    )
                    self.assertLessEqual(
                        statement_module.key_characters(grown),
                        statement_module.MAX_STATEMENT_KEY_CHARACTERS,
                    )
        largest = projection.parts[sizes.index(max(sizes))][1]
        with tempfile.TemporaryDirectory(prefix="alexandria-statement-heavy-") as name:
            for form, data in (
                ("bare", largest),
                ("dsse", ariadne_envelope.Envelope(largest).to_json().encode("utf-8")),
            ):
                path = Path(name) / f"largest-{form}.json"
                path.write_bytes(data)
                with self.subTest(form=form):
                    self.assertLessEqual(len(data), statement_module.MAX_STATEMENT_BYTES)
                    result = ariadne_verify(path)
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_a_part_admits_the_byte_limit_at_its_value_and_closes_one_below(self):
        # Past the key budget, so the release takes the part form at any byte limit.
        manifest = synthetic_manifest(2_000, 2_000)
        with mock.patch.object(statement_module, "MAX_PART_BYTES", 100_000):
            first = statement_module.project_statement(manifest).parts[0][1]
        count = json.loads(first)["predicate"]["part"]["components"]
        self.assertGreater(count, 1)
        self.assertLess(
            statement_module.key_characters(json.loads(first)),
            statement_module.MAX_STATEMENT_KEY_CHARACTERS,
        )
        with mock.patch.object(statement_module, "MAX_PART_BYTES", len(first)):
            self.assertEqual(statement_module.project_statement(manifest).parts[0][1], first)
        with mock.patch.object(statement_module, "MAX_PART_BYTES", len(first) - 1):
            smaller = json.loads(statement_module.project_statement(manifest).parts[0][1])
        self.assertEqual(smaller["predicate"]["part"]["components"], count - 1)

    def test_every_part_encodes_to_the_size_it_was_packed_at(self):
        # Hundreds of parts, so the part number and first component run to three
        # and four digits: every term of the packer's size has to be exact, not
        # only the ones part 0 exercises.
        manifest = synthetic_manifest(3_000, 3_000)
        packed = statement_module._part_bytes
        predicted = {}

        def recorded(frame, number, first, components, captures, values):
            size = packed(frame, number, first, components, captures, values)
            predicted[(number, first, components, captures)] = size
            return size

        with mock.patch.object(statement_module, "MAX_PART_BYTES", 20_000), \
                mock.patch.object(statement_module, "_part_bytes", recorded):
            projection = statement_module.project_statement(manifest)
        parts = decoded(projection.parts)
        self.assertGreater(len(parts), 100)
        self.assertGreater(parts[-1][1]["predicate"]["part"]["first_component"], 1_000)
        for (name, part), (_, body) in zip(parts, projection.parts):
            counts = part["predicate"]["part"]
            with self.subTest(part=name):
                self.assertEqual(predicted[(
                    counts["index"], counts["first_component"],
                    counts["components"], counts["captures"],
                )], len(body))

    def test_a_part_admits_the_key_budget_at_its_value_and_closes_one_below(self):
        manifest = synthetic_manifest(20, 20)
        with mock.patch.object(statement_module, "MAX_STATEMENT_KEY_CHARACTERS", 1_500):
            first = statement_module.project_statement(manifest).parts[0][1]
            keys = statement_module.key_characters(json.loads(first))
            count = json.loads(first)["predicate"]["part"]["components"]
            self.assertGreater(count, 1)
        with mock.patch.object(statement_module, "MAX_STATEMENT_KEY_CHARACTERS", keys):
            self.assertEqual(statement_module.project_statement(manifest).parts[0][1], first)
        with mock.patch.object(statement_module, "MAX_STATEMENT_KEY_CHARACTERS", keys - 1):
            smaller = json.loads(statement_module.project_statement(manifest).parts[0][1])
            self.assertEqual(smaller["predicate"]["part"]["components"], count - 1)

    def test_a_component_past_the_part_limit_refuses_by_name(self):
        case = single_statement_tests.OutputBoundaryTests("test_statement_limit_tracks_ariadne_bounded_reader")
        case.setUp()
        self.addCleanup(case.tearDown)
        manifest, _ = case.near_limit_release()
        with self.assertRaises(AlexandriaError) as caught:
            statement_module.project_statement(manifest)
        found = re.fullmatch(
            r"release statement component c000 needs a part of (\d+) bytes, "
            r"above the 6225920-byte part limit",
            str(caught.exception),
        )
        self.assertIsNotNone(found, str(caught.exception))
        needed = int(found.group(1))
        self.assertGreater(needed, statement_module.MAX_PART_BYTES)
        with mock.patch.object(statement_module, "MAX_PART_BYTES", needed):
            projection = statement_module.project_statement(manifest)
        name, body = projection.parts[0]
        self.assertEqual(len(body), needed)
        self.assertEqual(json.loads(body)["predicate"]["part"]["components"], 1)

    def test_a_component_past_the_key_budget_refuses_by_name(self):
        manifest = synthetic_manifest(20, 20)
        with mock.patch.object(statement_module, "MAX_STATEMENT_KEY_CHARACTERS", 50), \
                self.assertRaises(AlexandriaError) as caught:
            statement_module.project_statement(manifest)
        found = re.fullmatch(
            r"release statement component c00000 needs a part of (\d+) key characters, "
            r"above Ariadne's 50-character scan budget",
            str(caught.exception),
        )
        self.assertIsNotNone(found, str(caught.exception))
        needed = int(found.group(1))
        with mock.patch.object(statement_module, "MAX_STATEMENT_KEY_CHARACTERS", needed):
            projection = statement_module.project_statement(manifest)
        self.assertEqual(len(projection.parts), 20)
        with mock.patch.object(statement_module, "MAX_STATEMENT_KEY_CHARACTERS", needed - 1), \
                self.assertRaisesRegex(AlexandriaError, "component c00000 needs a part"):
            statement_module.project_statement(manifest)

    def test_a_part_may_hold_components_without_captures(self):
        manifest = synthetic_manifest(3_000, 1_000)
        parts = decoded(statement_module.project_statement(manifest).parts)
        empty = [part for _, part in parts if not part["predicate"]["captures"]]
        self.assertTrue(empty)
        for part in empty:
            self.assertEqual(part["predicate"]["part"]["captures"], 0)
            self.assertEqual(statement_errors(
                json.loads(PART_SCHEMA.read_text(encoding="utf-8")), part
            ), [])


class PinnedStatementProjectionTests(unittest.TestCase):
    """Every section 3 release in the tree still projects into today's bytes."""

    def test_the_in_tree_pinned_releases_project_to_their_base_statements(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-statement-pinned-") as name:
            releases = pinned_releases(Path(name).resolve())
            self.assertEqual(set(releases), set(PINNED))
            for label, (release_id, digest) in sorted(PINNED.items()):
                with self.subTest(release=label):
                    found_id, manifest = verified_manifest(releases[label])
                    self.assertEqual(found_id, release_id)
                    projected = statement_module.project_statement(manifest)
                    self.assertIsInstance(projected, bytes)
                    self.assertEqual(hashlib.sha256(projected).hexdigest(), digest)


class StatementPartSchemaTests(unittest.TestCase):
    """Both part schemas are closed, catalogued and match what the projection emits."""

    @classmethod
    def setUpClass(cls):
        cls.part_schema = json.loads(PART_SCHEMA.read_text(encoding="utf-8"))
        cls.index_schema = json.loads(INDEX_SCHEMA.read_text(encoding="utf-8"))
        cls.projection = statement_module.project_statement(synthetic_manifest(3_000, 6_000))

    def test_both_schemas_are_closed_and_name_the_emitter_constants(self):
        for schema, predicate_type in (
            (self.part_schema, statement_module.PART_PREDICATE_TYPE),
            (self.index_schema, statement_module.INDEX_PREDICATE_TYPE),
        ):
            with self.subTest(schema=schema["title"]):
                self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
                self.assertEqual(schema["properties"]["_type"]["const"],
                                 statement_module.STATEMENT_TYPE)
                self.assertEqual(schema["properties"]["predicateType"]["const"], predicate_type)
                self.assertEqual(set(schema["required"]), set(schema["properties"]))
                self.assertFalse(schema["additionalProperties"])
                stack, objects = [schema], 0
                while stack:
                    current = stack.pop()
                    if isinstance(current, dict):
                        if current.get("type") == "object":
                            objects += 1
                            self.assertIs(current.get("additionalProperties"), False, current)
                        stack.extend(current.values())
                    elif isinstance(current, list):
                        stack.extend(current)
                self.assertGreaterEqual(objects, 3)
        part = self.part_schema["$defs"]
        index = self.index_schema["$defs"]
        for found, expected in (
            (part["partPredicate"]["properties"], statement_module.PART_PREDICATE_FIELDS),
            (part["partPredicate"]["required"], statement_module.PART_PREDICATE_FIELDS),
            (part["partCounts"]["properties"], statement_module.PART_FIELDS),
            (part["partCounts"]["required"], statement_module.PART_FIELDS),
            (index["indexPredicate"]["properties"], statement_module.INDEX_PREDICATE_FIELDS),
            (index["indexPredicate"]["required"], statement_module.INDEX_PREDICATE_FIELDS),
            (index["indexParts"]["properties"], statement_module.INDEX_PARTS_FIELDS),
            (index["indexParts"]["required"], statement_module.INDEX_PARTS_FIELDS),
        ):
            self.assertEqual(set(found), expected)

    def test_every_shared_definition_resolves_in_the_single_statement_schema(self):
        single = json.loads(SINGLE_SCHEMA.read_text(encoding="utf-8"))
        prefix = single["$id"] + "#/"
        for schema in (self.part_schema, self.index_schema):
            stack, references = [schema], []
            while stack:
                current = stack.pop()
                if isinstance(current, dict):
                    if isinstance(current.get("$ref"), str):
                        references.append(current["$ref"])
                    stack.extend(current.values())
                elif isinstance(current, list):
                    stack.extend(current)
            external = [reference for reference in references if not reference.startswith("#")]
            self.assertTrue(external)
            for reference in external:
                with self.subTest(reference=reference):
                    self.assertTrue(reference.startswith(prefix))
                    target = single
                    for token in reference[len(prefix):].split("/"):
                        target = target[token]
                    self.assertIsInstance(target, dict)

    def test_the_emitted_part_set_matches_both_schemas(self):
        index = json.loads(self.projection.index)
        self.assertEqual(statement_errors(self.index_schema, index), [])
        self.assertEqual(set(index), set(self.index_schema["properties"]))
        self.assertEqual(set(index["predicate"]), statement_module.INDEX_PREDICATE_FIELDS)
        self.assertEqual(set(index["predicate"]["parts"]), statement_module.INDEX_PARTS_FIELDS)
        for name, part in decoded(self.projection.parts):
            with self.subTest(part=name):
                self.assertEqual(statement_errors(self.part_schema, part), [])
                self.assertEqual(set(part), set(self.part_schema["properties"]))
                self.assertEqual(set(part["predicate"]), statement_module.PART_PREDICATE_FIELDS)
                self.assertEqual(set(part["predicate"]["part"]), statement_module.PART_FIELDS)
        wrong = deepcopy(index)
        wrong["predicate"]["parts"]["extra"] = 1
        self.assertTrue(statement_errors(self.index_schema, wrong))
        wrong = json.loads(self.projection.parts[0][1])
        wrong["subject"][1]["name"] = "part/part-00000.json"
        self.assertTrue(statement_errors(self.part_schema, wrong))

    def test_the_catalogue_names_both_schemas_and_predicate_types(self):
        catalogue = (SCHEMAS / "README.md").read_text(encoding="utf-8")
        for token in (
            f"`{PART_SCHEMA.name}`",
            f"`{INDEX_SCHEMA.name}`",
            f"`{statement_module.PART_PREDICATE_TYPE}`",
            f"`{statement_module.INDEX_PREDICATE_TYPE}`",
            "6,225,920 bytes",
            "262,144 key characters",
        ):
            with self.subTest(token=token):
                self.assertIn(token, catalogue)


if __name__ == "__main__":
    unittest.main()
