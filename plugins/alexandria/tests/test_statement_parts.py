"""The part form of a release statement: projection, bounds and schemas.

The design record's `part-projection-verifies` cell loads the five tests of
`StatementPartProjectionTests` by name. They share one 16,384-component,
16,384-capture release whose single statement exceeds Ariadne's input limit.
Its `past-limit-refuses-by-name` and `killed-emit-leaves-no-set` cells load
the six tests of `StatementPartsCommandTests` by name, three each. The other
classes hold each bound at its value and one past it, tie the bounds to
Ariadne's own constants, keep the in-tree pinned statements byte for byte,
hold both part schemas to the emitted field sets, and hold the `--parts`
writer's receipt, its usage and its removal on every failure.

Ariadne runs as a stranger runs it, one `ariadne.py verify` child process a
file with its default bounds. Its envelope and gate modules are imported only
to build an unsigned DSSE envelope and to count scanned keys.
"""

from contextlib import ExitStack, nullcontext
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import signal
import stat
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
COMMAND = PLUGIN_ROOT / "scripts" / "alexandria.py"
sys.path.insert(0, str(PLUGIN_ROOT / "scripts"))
if str(ARIADNE_SCRIPTS) not in sys.path:
    sys.path.append(str(ARIADNE_SCRIPTS))

from alexandria_lib import emit_statement, emit_statement_parts, ingest  # noqa: E402
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
# The two section 3 statements whose preserved release lives outside the tree,
# checked when the variable names it: label -> (variable, identifier, SHA-256).
EXTERNAL_PINNED = {
    "wildcat-v1": ("ALEXANDRIA_WILDCAT_V1_RELEASE",
                   "sha256:eee71d1e9e656b8d14bc855cce201f9981e65aeec54076d132a089b24fa51d69",
                   "679277a2a3367d16a4cb462a12c805c6580291bbaaf7c3a6aa5b4d4e177c00ca"),
    "wildcat-v2": ("ALEXANDRIA_WILDCAT_V2_RELEASE",
                   "sha256:2de87cbd4e80d378d53de553eac93a6389d6457f2f6a7d52785e7ef0e5d2a8a3",
                   "c891c9d510da6cf02136b082766792d520823beb98b79781c4f8cbcbaec7feae"),
}
PARTS_HINT = "alexandria: write this release as an index and parts with --parts <directory>"
FITS_ONE_STATEMENT = (
    "alexandria: release statement fits Ariadne's 8388608-byte input limit and "
    "262144-character scan budget; emit it with --output <file>"
)


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


def run_command(*args, cwd=None) -> subprocess.CompletedProcess:
    """One `alexandria.py` child process, as an operator runs it."""
    return subprocess.run(
        [sys.executable, str(COMMAND), *map(str, args)],
        capture_output=True, text=True, check=False, env=child_environment(),
        timeout=600, cwd=cwd,
    )


def listing(directory: Path) -> dict:
    """Every entry under `directory`: a file's bytes, a link's target, or None."""
    entries = {}
    for path in sorted(Path(directory).rglob("*")):
        if path.is_symlink():
            entries[str(path.relative_to(directory))] = ("link", os.readlink(path))
        elif path.is_dir():
            entries[str(path.relative_to(directory))] = None
        else:
            entries[str(path.relative_to(directory))] = path.read_bytes()
    return entries


def written_set(directory: Path) -> dict:
    """A part set's files by path relative to its directory."""
    return {
        name: body for name, body in listing(directory).items() if body is not None
    }


def expected_set(projection) -> dict:
    return {
        statement_module.INDEX_NAME: projection.index,
        **{f"part/{name}": body for name, body in projection.parts},
    }


class PartsCase(unittest.TestCase):
    """A scratch root with an empty `outputs` directory beside each release."""

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="alexandria-statement-parts-command-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        self.outputs = self.root / "outputs"
        self.outputs.mkdir()

    def band_release(self, name="band"):
        """2,000 components: within the byte limit, past the key budget."""
        release = self.root / name
        return release, write_synthetic_release(release, 2_000, 2_000)

    def near_limit_release(self):
        """One component whose captures pass the byte limit and the part limit."""
        case = single_statement_tests.OutputBoundaryTests(
            "test_statement_limit_tracks_ariadne_bounded_reader"
        )
        case.setUp()
        self.addCleanup(case.tearDown)
        manifest, _ = case.near_limit_release()
        return case.release, manifest

    def assert_refused(self, result, *patterns):
        """Exit 1, no stdout, no traceback, and one stderr line for each pattern."""
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertEqual(result.stdout, "")
        self.assertNotIn("Traceback", result.stderr)
        lines = result.stderr.splitlines()
        self.assertEqual(len(lines), len(patterns), result.stderr)
        found = []
        for line, pattern in zip(lines, patterns):
            self.assertRegex(line, "^" + pattern + "$")
            found.append(re.fullmatch(pattern, line))
        return found


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

    def test_a_component_past_the_part_limit_refuses_by_name_in_a_late_part(self):
        # The refusal's size has to carry the real part number and first component,
        # which run to two and four digits here, not the ones part 0 has.
        manifest = synthetic_manifest(1_500, 1_500)
        capture = manifest["captures"][1_200]
        capture["coverage"]["gaps"] = ["x" * 941] * 40
        manifest = reseal(manifest)
        with mock.patch.object(statement_module, "MAX_PART_BYTES", 20_000), \
                self.assertRaises(AlexandriaError) as caught:
            statement_module.project_statement(manifest)
        found = re.fullmatch(
            r"release statement component c01200 needs a part of (\d+) bytes, "
            r"above the 20000-byte part limit",
            str(caught.exception),
        )
        self.assertIsNotNone(found, str(caught.exception))
        needed = int(found.group(1))
        with mock.patch.object(statement_module, "MAX_PART_BYTES", needed):
            projection = statement_module.project_statement(manifest)
        parts = decoded(projection.parts)
        located = [
            (name, part) for name, part in parts
            if part["predicate"]["part"]["first_component"] == 1_200
        ]
        self.assertEqual(len(located), 1)
        counts = located[0][1]["predicate"]["part"]
        self.assertEqual(counts["components"], 1)
        self.assertGreater(counts["index"], 9)
        body = dict(projection.parts)[located[0][0]]
        self.assertEqual(len(body), needed)
        with mock.patch.object(statement_module, "MAX_PART_BYTES", needed - 1), \
                self.assertRaisesRegex(AlexandriaError, "component c01200 needs a part of"):
            statement_module.project_statement(manifest)

    def test_the_output_check_refuses_a_part_the_packer_undercounts(self):
        manifest = synthetic_manifest(2_000, 2_000)
        with self.subTest(bound="bytes"):
            with mock.patch.object(statement_module, "MAX_PART_BYTES", 100_000), \
                    mock.patch.object(statement_module, "_part_bytes", lambda *_: 0), \
                    self.assertRaisesRegex(
                        AlexandriaError,
                        r"release statement part-00000\.json encodes to \d+ bytes, "
                        r"above the 100000-byte part limit",
                    ):
                statement_module.project_statement(manifest)
        real = statement_module.key_characters

        def blind_to_components(statement):
            return real(statement) if "_type" in statement else 0

        with self.subTest(bound="key characters"):
            with mock.patch.object(statement_module, "MAX_STATEMENT_KEY_CHARACTERS", 1_500), \
                    mock.patch.object(statement_module, "key_characters", blind_to_components), \
                    self.assertRaisesRegex(
                        AlexandriaError,
                        r"release statement part-00000\.json carries \d+ key characters, "
                        r"above Ariadne's 1500-character scan budget",
                    ):
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


class StatementPartsCommandTests(PartsCase):
    """The six cases the `past-limit-refuses-by-name` and `killed-emit-leaves-no-set` cells load."""

    def test_a_component_past_the_part_limit_refuses_by_name(self):
        release, _ = self.near_limit_release()
        target = self.outputs / "set"
        result = run_command("statement", release, "--parts", target)
        (found,) = self.assert_refused(
            result,
            r"alexandria: release statement component c000 needs a part of (\d+) bytes, "
            r"above the 6225920-byte part limit",
        )
        self.assertGreater(int(found.group(1)), statement_module.MAX_PART_BYTES)
        self.assertEqual(listing(self.outputs), {})

    def test_output_refuses_a_release_past_the_single_bounds_naming_parts(self):
        near, near_manifest = self.near_limit_release()
        band, _ = self.band_release()
        band_manifest = json.loads((band / "manifest.json").read_bytes())
        near_bytes = len(canonical_bytes(
            statement_module.statement_for(near_manifest),
            max_nodes=statement_module.MAX_STATEMENT_BYTES,
        ))
        band_keys = statement_module.key_characters(
            statement_module.statement_for(band_manifest)
        )
        self.assertGreater(near_bytes, statement_module.MAX_STATEMENT_BYTES)
        self.assertGreater(band_keys, statement_module.MAX_STATEMENT_KEY_CHARACTERS)
        for label, release, line in (
            ("bytes", near,
             f"release statement encodes to {near_bytes} bytes, above Ariadne's "
             "8388608-byte input limit"),
            ("key characters", band,
             f"release statement carries {band_keys} key characters, above Ariadne's "
             "262144-character scan budget"),
        ):
            with self.subTest(bound=label):
                output = self.outputs / f"{label}.json"
                output.write_bytes(b"keep\n")
                result = run_command("statement", release, "--output", output)
                self.assert_refused(result, re.escape(f"alexandria: {line}"),
                                    re.escape(PARTS_HINT))
                self.assertEqual(output.read_bytes(), b"keep\n")
                with self.assertRaises(statement_module.StatementPastSingleBounds) as caught:
                    emit_statement(release, output)
                self.assertIsInstance(caught.exception, AlexandriaError)
                self.assertEqual(str(caught.exception), line)
                self.assertEqual(output.read_bytes(), b"keep\n")
        self.assertEqual(set(listing(self.outputs)), {"bytes.json", "key characters.json"})

    def test_parts_refuses_a_release_that_fits_one_statement(self):
        release = fixture_release(self.root)
        target = self.outputs / "set"
        result = run_command("statement", release, "--parts", target)
        self.assert_refused(result, re.escape(FITS_ONE_STATEMENT))
        self.assertEqual(listing(self.outputs), {})
        single = self.outputs / "statement.json"
        emitted = run_command("statement", release, "--output", single)
        self.assertEqual(emitted.returncode, 0, emitted.stderr)
        self.assertEqual(hashlib.sha256(single.read_bytes()).hexdigest(), FIXTURE_STATEMENT_SHA256)

    def test_an_interrupted_write_leaves_no_output_directory(self):
        release, release_id = self.band_release()
        target = self.outputs / "set"
        real = statement_module._write_all
        calls = []

        def interrupted(descriptor, body):
            calls.append(len(body))
            if len(calls) == 2:
                raise KeyboardInterrupt
            real(descriptor, body)

        with self.subTest(interruption="in process"):
            with mock.patch.object(statement_module, "_write_all", interrupted), \
                    self.assertRaises(KeyboardInterrupt):
                emit_statement_parts(release, target)
            self.assertEqual(len(calls), 2)
            self.assertEqual(listing(self.outputs), {})

        # A process killed after every file is written and before the rename
        # cannot clean up: what it leaves is a hidden temporary sibling, never
        # a directory at the target, and the next run writes the whole set.
        killer = "\n".join((
            "import os, signal, stat, sys",
            f"sys.path.insert(0, {str(PLUGIN_ROOT / 'scripts')!r})",
            "from alexandria_lib import statement",
            "real = os.fsync",
            "def fsync(descriptor):",
            "    if stat.S_ISDIR(os.fstat(descriptor).st_mode):",
            "        os.kill(os.getpid(), signal.SIGKILL)",
            "    real(descriptor)",
            "statement.os.fsync = fsync",
            f"statement.emit_statement_parts({str(release)!r}, {str(target)!r})",
        ))
        with self.subTest(interruption="killed"):
            killed = subprocess.run(
                [sys.executable, "-c", killer], capture_output=True, text=True, check=False,
                env=child_environment(), timeout=600,
            )
            self.assertEqual(killed.returncode, -signal.SIGKILL, killed.stderr)
            self.assertFalse(os.path.lexists(target))
            left = [path for path in self.outputs.iterdir()]
            self.assertEqual(len(left), 1)
            self.assertTrue(left[0].name.startswith(".set.tmp-"), left[0].name)
            self.assertIn(statement_module.INDEX_NAME, written_set(left[0]))
            result = run_command("statement", release, "--parts", target)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["release_id"], release_id)
            _, manifest = verified_manifest(release)
            self.assertEqual(
                written_set(target), expected_set(statement_module.project_statement(manifest))
            )

    def test_an_existing_output_is_refused_unchanged(self):
        release, _ = self.band_release()
        elsewhere = self.root / "elsewhere"
        elsewhere.mkdir()
        (self.outputs / "empty").mkdir()
        (self.outputs / "full").mkdir()
        (self.outputs / "full" / "index.json").write_bytes(b"keep\n")
        (self.outputs / "file").write_bytes(b"keep\n")
        (self.outputs / "link").symlink_to(elsewhere, target_is_directory=True)
        (self.outputs / "dangling").symlink_to(self.root / "missing")
        written = self.outputs / "written"
        first = run_command("statement", release, "--parts", written)
        self.assertEqual(first.returncode, 0, first.stderr)
        before = listing(self.outputs)
        for name in ("empty", "full", "file", "link", "dangling", "written"):
            with self.subTest(target=name):
                result = run_command("statement", release, "--parts", self.outputs / name)
                self.assert_refused(result, re.escape(
                    f"alexandria: statement parts output already exists: {self.outputs / name}"
                ))
                self.assertEqual(listing(self.outputs), before)
        self.assertEqual(listing(elsewhere), {})

    def test_output_inside_or_through_a_symlink_into_the_release_is_refused(self):
        release, release_id = self.band_release()
        real = self.root / "real"
        real.mkdir()
        (self.outputs / "into-release").symlink_to(release, target_is_directory=True)
        (self.outputs / "outside").symlink_to(real, target_is_directory=True)
        (self.outputs / "set-link").symlink_to(release / "set", target_is_directory=True)
        kept = listing(release)
        before = listing(self.outputs)
        inside = "alexandria: statement output must not be inside the release"
        through = "alexandria: statement output must not pass through a symlink"
        for label, target, line in (
            ("inside", release / "set", inside),
            ("nested inside", release / "objects" / "set", inside),
            ("through a link into the release", self.outputs / "into-release" / "set", inside),
            ("a link to a path inside the release", self.outputs / "set-link", inside),
            ("through a link elsewhere", self.outputs / "outside" / "set", through),
        ):
            with self.subTest(target=label):
                result = run_command("statement", release, "--parts", target)
                self.assert_refused(result, re.escape(line))
                self.assertEqual(listing(release), kept)
                self.assertEqual(listing(self.outputs), before)
                self.assertEqual(listing(real), {})
        self.assertEqual(release_module.verify(release), release_id)


class StatementPartsReceiptTests(PartsCase):
    """What `--parts` prints and writes: canonical, complete and repeatable."""

    def test_the_receipt_is_canonical_and_names_what_was_written(self):
        release, release_id = self.band_release()
        result = run_command("statement", release, "--parts", "set", cwd=self.outputs)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        receipt = json.loads(result.stdout)
        self.assertEqual(result.stdout.encode("utf-8"), canonical_bytes(receipt))
        target = self.outputs / "set"
        _, manifest = verified_manifest(release)
        projection = statement_module.project_statement(manifest)
        self.assertEqual(receipt, {
            "release_id": release_id,
            "part_count": len(projection.parts),
            "component_count": 2_000,
            "capture_count": 2_000,
            "index_predicate_type": statement_module.INDEX_PREDICATE_TYPE,
            "part_predicate_type": statement_module.PART_PREDICATE_TYPE,
            "output": str(target),
        })
        self.assertTrue(Path(receipt["output"]).is_absolute())
        self.assertGreater(receipt["part_count"], 1)
        files = written_set(target)
        self.assertEqual(files, expected_set(projection))
        self.assertEqual(set(listing(target)), {"part", *files})
        index = json.loads(files[statement_module.INDEX_NAME])
        # Every part subject in the index names its file's path in the set.
        self.assertEqual(
            {subject["name"]: subject["digest"]["sha256"] for subject in index["subject"][1:]},
            {name: hashlib.sha256(body).hexdigest()
             for name, body in files.items() if name != statement_module.INDEX_NAME},
        )
        for name in files:
            with self.subTest(file=name):
                verified = ariadne_verify(target / name)
                self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_a_repeated_run_to_a_fresh_directory_writes_identical_bytes(self):
        release, _ = self.band_release()
        receipts = []
        for name in ("first", "second"):
            result = run_command("statement", release, "--parts", self.outputs / name)
            self.assertEqual(result.returncode, 0, result.stderr)
            receipts.append(json.loads(result.stdout))
        self.assertEqual(listing(self.outputs / "first"), listing(self.outputs / "second"))
        self.assertEqual(
            {key: value for key, value in receipts[0].items() if key != "output"},
            {key: value for key, value in receipts[1].items() if key != "output"},
        )


    def test_the_set_is_owner_only_and_every_entry_is_fsynced(self):
        # S3-R1-02 and S3-R1-03: owner-only modes under a permissive umask,
        # and one fsync for every file and both directories before the rename.
        release, _ = self.band_release()
        target = self.outputs / "set"
        real = os.fsync
        synced = set()

        def syncing(descriptor):
            found = os.fstat(descriptor)
            synced.add((found.st_dev, found.st_ino))
            real(descriptor)

        previous = os.umask(0o022)
        try:
            with mock.patch.object(statement_module.os, "fsync", syncing):
                emit_statement_parts(release, target)
        finally:
            os.umask(previous)
        entries = [target, *sorted(target.rglob("*"))]
        # The set's own directory, `part/`, and every file.
        self.assertEqual(len(entries), 2 + len(written_set(target)))
        for path in entries:
            with self.subTest(entry=str(path.relative_to(self.outputs))):
                found = os.lstat(path)
                expected = 0o700 if stat.S_ISDIR(found.st_mode) else 0o600
                self.assertEqual(stat.S_IMODE(found.st_mode), expected)
        self.assertEqual(
            synced, {(os.lstat(path).st_dev, os.lstat(path).st_ino) for path in entries}
        )

class StatementPartsUsageTests(PartsCase):
    """`--output` and `--parts` are a required, mutually exclusive pair."""

    def test_output_and_parts_together_or_neither_is_a_usage_error(self):
        release = self.root / "absent-release"
        for label, arguments, text in (
            ("both", ("--output", self.outputs / "s.json", "--parts", self.outputs / "set"),
             "argument --parts: not allowed with argument --output"),
            ("neither", (), "one of the arguments --output --parts is required"),
        ):
            with self.subTest(arguments=label):
                result = run_command("statement", release, *arguments)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(text, result.stderr)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(result.stdout, "")
                self.assertEqual(listing(self.outputs), {})

    def test_a_parts_output_must_name_a_directory(self):
        release, _ = self.band_release()
        with self.assertRaisesRegex(
            AlexandriaError, "^statement parts output must name a directory$"
        ):
            emit_statement_parts(release, Path("/"))


class StatementPartsFailureTests(PartsCase):
    """Every failure before the rename removes the temporary set and installs nothing."""

    def refuses_leaving_nothing(self, pattern, **patches):
        self.releases = getattr(self, "releases", 0) + 1
        release, release_id = self.band_release(f"release-{self.releases}")
        target = self.outputs / "set"
        with mock.patch.multiple(statement_module, **patches) if patches else nullcontext(), \
                self.assertRaisesRegex(AlexandriaError, pattern):
            emit_statement_parts(release, target)
        self.assertEqual(listing(self.outputs), {})
        return release, release_id

    def test_a_release_changed_before_the_rename_installs_nothing(self):
        real = release_module.verify
        with self.subTest(change="an object's bytes"):
            calls = []

            def changing(root):
                calls.append(root)
                if len(calls) == 2:
                    manifest = json.loads((Path(root) / "manifest.json").read_bytes())
                    path = Path(root) / manifest["components"][0]["object_path"]
                    path.chmod(0o600)
                    path.write_bytes(b"[]\n")
                return real(root)

            self.refuses_leaving_nothing(
                r"^component c00000 digest does not match$", verify=changing
            )
            self.assertEqual(len(calls), 2)
        with self.subTest(change="another identity"):
            calls = []

            def another(root):
                calls.append(root)
                return real(root) if len(calls) == 1 else "sha256:" + "0" * 64

            self.refuses_leaving_nothing(
                r"^release changed while its statement parts were emitted$", verify=another
            )

    def test_a_target_made_before_the_rename_is_refused_unchanged(self):
        real = release_module.verify
        target = self.outputs / "set"
        calls = []

        def racing(root):
            calls.append(root)
            if len(calls) == 2:
                target.mkdir()
                (target / "index.json").write_bytes(b"theirs\n")
            return real(root)

        release, _ = self.band_release()
        with mock.patch.object(statement_module, "verify", racing), \
                self.assertRaisesRegex(AlexandriaError, "^statement parts output already exists: "):
            emit_statement_parts(release, target)
        self.assertEqual(listing(self.outputs), {"set": None, "set/index.json": b"theirs\n"})

    def test_a_failed_file_write_leaves_no_output_or_temporary(self):
        real = statement_module._write_all
        for failing in (1, 2, 3):
            with self.subTest(file=failing):
                calls = []

                def writing(descriptor, body):
                    calls.append(body)
                    if len(calls) == failing:
                        raise OSError("disk full")
                    real(descriptor, body)

                self.refuses_leaving_nothing(
                    r"^cannot write release statement parts: disk full$", _write_all=writing
                )

    def test_a_failed_fsync_leaves_no_output_or_temporary(self):
        real = os.fsync
        for label, failing in (
            ("a file", lambda descriptor: not _is_directory(descriptor)),
            ("a directory", _is_directory),
        ):
            with self.subTest(fsync=label):
                def syncing(descriptor, failing=failing):
                    if failing(descriptor):
                        raise OSError("fsync failed")
                    real(descriptor)

                with mock.patch.object(statement_module.os, "fsync", syncing):
                    self.refuses_leaving_nothing(r"^cannot write release statement parts: fsync failed$")

    def test_a_failed_rename_leaves_no_output_or_temporary(self):
        refused = mock.Mock(side_effect=OSError("rename refused"))
        # The writer checks that its platform renames under a directory
        # descriptor, so the failing rename has to claim that support too.
        with mock.patch.object(statement_module.os, "rename", refused), \
                mock.patch.object(statement_module.os, "supports_dir_fd",
                                  os.supports_dir_fd | {refused}):
            self.refuses_leaving_nothing(r"^cannot write release statement parts: rename refused$")
        self.assertEqual(refused.call_count, 1)


    def test_a_moved_output_parent_installs_nothing(self):
        # S3-R1-01: the parent descriptor still names the directory that was
        # moved away, so the set must not be installed there.
        real = release_module.verify
        target = self.outputs / "set"
        moved = self.root / "outputs-moved"
        calls = []

        def moving(root):
            calls.append(root)
            if len(calls) == 2:
                self.outputs.rename(moved)
                self.outputs.mkdir()
            return real(root)

        release, _ = self.band_release()
        with mock.patch.object(statement_module, "verify", moving), \
                self.assertRaisesRegex(
                    AlexandriaError, "^statement parts output parent changed during emission$"
                ):
            emit_statement_parts(release, target)
        self.assertEqual(listing(self.outputs), {})
        self.assertEqual(listing(moved), {})

    def test_a_swapped_temporary_directory_installs_nothing(self):
        # S3-R1-01: a directory put in place of the temporary set is not the
        # set that was written and fsynced, so it is neither installed nor removed.
        real = release_module.verify
        target = self.outputs / "set"
        calls = []
        swapped = []

        def swapping(root):
            calls.append(root)
            if len(calls) == 2:
                (temporary,) = self.outputs.iterdir()
                temporary.rename(self.outputs / "ours")
                temporary.mkdir()
                (temporary / "index.json").write_bytes(b"theirs\n")
                swapped.append(temporary.name)
            return real(root)

        release, _ = self.band_release()
        with mock.patch.object(statement_module, "verify", swapping), \
                self.assertRaisesRegex(
                    AlexandriaError,
                    "^statement parts temporary directory changed during emission$",
                ):
            emit_statement_parts(release, target)
        (impostor,) = swapped
        self.assertEqual(listing(self.outputs), {
            "ours": None, impostor: None, f"{impostor}/index.json": b"theirs\n",
        })

    def test_a_file_already_in_the_temporary_set_is_not_written_through(self):
        # S3-R2-01: the creates are exclusive, so a file that already exists
        # in the temporary set is refused and keeps its bytes.
        real = statement_module.os.open
        target = self.outputs / "set"

        def opening(name, flags, mode=0o777, *, dir_fd=None):
            if name == statement_module.INDEX_NAME and dir_fd is not None and flags & os.O_CREAT:
                planted = real(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=dir_fd)
                os.write(planted, b"planted\n")
                os.close(planted)
            return real(name, flags, mode, dir_fd=dir_fd)

        release, _ = self.band_release()
        # The writers check that their platform opens under a directory
        # descriptor, so the wrapper has to claim that support too.
        with mock.patch.object(statement_module.os, "open", opening), \
                mock.patch.object(statement_module.os, "supports_dir_fd",
                                  os.supports_dir_fd | {opening}), \
                self.assertRaisesRegex(
                    AlexandriaError, r"^cannot write release statement parts: \[Errno 17\]"
                ):
            emit_statement_parts(release, target)
        (temporary,) = self.outputs.iterdir()
        self.assertEqual(listing(self.outputs), {
            temporary.name: None, f"{temporary.name}/index.json": b"planted\n",
        })

    def test_a_directory_swapped_in_as_it_is_opened_is_refused_and_left_alone(self):
        # S3-R2-02 and S3-R2-03: a directory put at the temporary name between
        # its mkdir and its open is not the one that was made, and cleanup
        # removes only what it made, so the empty impostor stays.
        real = statement_module.os.open
        real_write = statement_module._write_all
        swapped = []
        written = []

        def writing(descriptor, body):
            written.append(body)
            real_write(descriptor, body)

        def opening(name, flags, mode=0o777, *, dir_fd=None):
            if flags & os.O_DIRECTORY and dir_fd is not None and name.startswith(".set.tmp-") \
                    and not swapped:
                swapped.append(name)
                os.rename(name, "ours", src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                os.mkdir(name, 0o700, dir_fd=dir_fd)
            return real(name, flags, mode, dir_fd=dir_fd)

        release, _ = self.band_release()
        # The writers check that their platform opens under a directory
        # descriptor, so the wrapper has to claim that support too.
        with mock.patch.object(statement_module.os, "open", opening), \
                mock.patch.object(statement_module, "_write_all", writing), \
                mock.patch.object(statement_module.os, "supports_dir_fd",
                                  os.supports_dir_fd | {opening}), \
                self.assertRaisesRegex(
                    AlexandriaError,
                    "^statement parts temporary directory changed during emission$",
                ):
            emit_statement_parts(release, self.outputs / "set")
        (impostor,) = swapped
        self.assertEqual(written, [])
        self.assertEqual(listing(self.outputs), {"ours": None, impostor: None})

    def test_cleanup_leaves_a_file_it_did_not_create(self):
        # S3-R2-03: a file put at a name the writer created is not the writer's
        # own, so a failure removes the rest of the set and keeps that file.
        real = release_module.verify
        calls = []

        def replacing(root):
            calls.append(root)
            if len(calls) == 2:
                (temporary,) = self.outputs.iterdir()
                (temporary / statement_module.INDEX_NAME).unlink()
                (temporary / statement_module.INDEX_NAME).write_bytes(b"theirs\n")
            return real(root)

        refused = mock.Mock(side_effect=OSError("rename refused"))
        release, _ = self.band_release()
        with mock.patch.object(statement_module, "verify", replacing), \
                mock.patch.object(statement_module.os, "rename", refused), \
                mock.patch.object(statement_module.os, "supports_dir_fd",
                                  os.supports_dir_fd | {refused}), \
                self.assertRaisesRegex(
                    AlexandriaError, r"^cannot write release statement parts: rename refused$"
                ):
            emit_statement_parts(release, self.outputs / "set")
        (temporary,) = self.outputs.iterdir()
        self.assertEqual(listing(self.outputs), {
            temporary.name: None, f"{temporary.name}/index.json": b"theirs\n",
        })

    def test_a_failed_file_inspection_leaves_no_output_or_temporary(self):
        # S3-R3-07: a file whose fstat fails right after its create is
        # unlinked, so the temporary directory is removed with it. Only a
        # file just created is still empty; the release's files are not.
        real = os.fstat

        def inspecting(descriptor):
            found = real(descriptor)
            if stat.S_ISREG(found.st_mode) and found.st_size == 0:
                raise OSError("fstat failed")
            return found

        with mock.patch.object(statement_module.os, "fstat", inspecting):
            self.refuses_leaving_nothing(r"^cannot write release statement parts: fstat failed$")

    def test_cleanup_passes_over_an_entry_already_gone(self):
        # S3-R3-08: an entry the writer made and something else removed is
        # skipped, the rest is removed, and the original refusal still surfaces.
        real = release_module.verify
        calls = []

        def removing(root):
            calls.append(root)
            if len(calls) == 2:
                (temporary,) = self.outputs.iterdir()
                (temporary / statement_module.INDEX_NAME).unlink()
            return real(root)

        refused = mock.Mock(side_effect=OSError("rename refused"))
        with mock.patch.object(statement_module.os, "rename", refused), \
                mock.patch.object(statement_module.os, "supports_dir_fd",
                                  os.supports_dir_fd | {refused}):
            self.refuses_leaving_nothing(
                r"^cannot write release statement parts: rename refused$", verify=removing
            )

    def test_a_link_swapped_in_for_the_temporary_directory_installs_nothing(self):
        # S3-R3-09: the check before the rename reads the temporary name
        # without following it, so a link to the written set is not installed.
        real = release_module.verify
        target = self.outputs / "set"
        calls = []
        swapped = []

        def linking(root):
            calls.append(root)
            if len(calls) == 2:
                (temporary,) = self.outputs.iterdir()
                temporary.rename(self.outputs / "ours")
                temporary.symlink_to("ours", target_is_directory=True)
                swapped.append(temporary.name)
            return real(root)

        release, _ = self.band_release()
        with mock.patch.object(statement_module, "verify", linking), \
                self.assertRaisesRegex(
                    AlexandriaError,
                    "^statement parts temporary directory changed during emission$",
                ):
            emit_statement_parts(release, target)
        (link,) = swapped
        self.assertFalse(os.path.lexists(target))
        self.assertEqual(listing(self.outputs), {"ours": None, link: ("link", "ours")})

    def test_a_link_put_at_the_temporary_name_as_it_is_opened_is_not_followed(self):
        # S3-R4-01: a link back to the directory just made passes the identity
        # comparison, since it reaches the same inode, so only O_NOFOLLOW on
        # the open refuses it before anything is written through the link.
        real = statement_module.os.open
        real_write = statement_module._write_all
        swapped = []
        written = []

        def writing(descriptor, body):
            written.append(body)
            real_write(descriptor, body)

        def opening(name, flags, mode=0o777, *, dir_fd=None):
            if flags & os.O_DIRECTORY and dir_fd is not None and name.startswith(".set.tmp-") \
                    and not swapped:
                swapped.append(name)
                os.rename(name, "ours", src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                os.symlink("ours", name, dir_fd=dir_fd)
            return real(name, flags, mode, dir_fd=dir_fd)

        release, _ = self.band_release()
        with mock.patch.object(statement_module.os, "open", opening), \
                mock.patch.object(statement_module, "_write_all", writing), \
                mock.patch.object(statement_module.os, "supports_dir_fd",
                                  os.supports_dir_fd | {opening}), \
                self.assertRaisesRegex(
                    AlexandriaError, r"^cannot write release statement parts: "
                ):
            emit_statement_parts(release, self.outputs / "set")
        (link,) = swapped
        self.assertEqual(written, [])
        self.assertEqual(listing(self.outputs), {"ours": None, link: ("link", "ours")})


class StatementPartsBoundaryTests(PartsCase):
    """S3-R3: both single bounds at their values, the receipt counts, inspection, allocation and platform."""

    def test_each_single_bound_admits_its_value_and_refuses_one_past_it(self):
        # S3-R3-01: Ariadne admits a statement at exactly either bound, so
        # `--output` writes one there and refuses only one past it. The limit
        # is set to the fixture statement's own size for the byte half.
        release = fixture_release(self.root)
        size = len(statement_module.project_statement(verified_manifest(release)[1]))
        budget = statement_module.MAX_STATEMENT_KEY_CHARACTERS
        for label, patch, line in (
            ("bytes", ("MAX_STATEMENT_BYTES", size, size - 1),
             f"release statement encodes to {size} bytes, above Ariadne's "
             f"{size - 1}-byte input limit"),
            ("key characters", ("key_characters", mock.Mock(return_value=budget),
                                mock.Mock(return_value=budget + 1)),
             f"release statement carries {budget + 1} key characters, above Ariadne's "
             "262144-character scan budget"),
        ):
            name, at_bound, past_bound = patch
            with self.subTest(bound=label):
                admitted = self.outputs / f"{label} at.json"
                with mock.patch.object(statement_module, name, at_bound):
                    emit_statement(release, admitted)
                self.assertEqual(
                    hashlib.sha256(admitted.read_bytes()).hexdigest(), FIXTURE_STATEMENT_SHA256
                )
                refused = self.outputs / f"{label} past.json"
                with mock.patch.object(statement_module, name, past_bound), \
                        self.assertRaises(statement_module.StatementPastSingleBounds) as caught:
                    emit_statement(release, refused)
                self.assertEqual(str(caught.exception), line)
                self.assertFalse(os.path.lexists(refused))

    def test_the_receipt_counts_components_and_captures_apart(self):
        # S3-R3-02: with fewer captures than components, each count is its own.
        release = self.root / "uneven"
        release_id = write_synthetic_release(release, 2_000, 1_500)
        receipt = emit_statement_parts(release, self.outputs / "set")
        self.assertEqual(receipt["release_id"], release_id)
        self.assertEqual(receipt["component_count"], 2_000)
        self.assertEqual(receipt["capture_count"], 1_500)

    def test_an_uninspectable_target_refuses_by_name(self):
        # S3-R3-03: a target the absence check cannot inspect is refused as
        # such, not treated as absent.
        release, _ = self.band_release()
        with self.assertRaisesRegex(
            AlexandriaError, r"^cannot inspect statement parts output: \[Errno \d+\] "
        ):
            emit_statement_parts(release, self.outputs / ("x" * 300))
        self.assertEqual(listing(self.outputs), {})

    def test_a_taken_temporary_name_is_skipped_and_exhaustion_refuses_by_name(self):
        # S3-R3-04: a temporary name already taken is skipped, and 32 taken
        # names refuse by name; the taken directory is never touched.
        release, _ = self.band_release()
        taken = self.outputs / (".set.tmp-" + "a" * 16)
        taken.mkdir()
        (taken / "index.json").write_bytes(b"theirs\n")
        target = self.outputs / "set"
        with self.subTest(case="one taken name"):
            with mock.patch.object(statement_module.secrets, "token_hex",
                                   side_effect=["a" * 16, "b" * 16]) as names:
                emit_statement_parts(release, target)
            self.assertEqual(names.call_count, 2)
            self.assertEqual(listing(taken), {"index.json": b"theirs\n"})
            _, manifest = verified_manifest(release)
            self.assertEqual(
                written_set(target), expected_set(statement_module.project_statement(manifest))
            )
            shutil.rmtree(target)
        with self.subTest(case="every name taken"):
            with mock.patch.object(statement_module.secrets, "token_hex",
                                   return_value="a" * 16) as names, \
                    self.assertRaisesRegex(
                        AlexandriaError,
                        "^cannot allocate a fresh statement parts temporary directory$",
                    ):
                emit_statement_parts(release, target)
            self.assertEqual(names.call_count, 32)
            self.assertEqual(listing(self.outputs), {
                taken.name: None, f"{taken.name}/index.json": b"theirs\n",
            })

    def test_a_platform_without_confined_directory_calls_refuses_by_name(self):
        # S3-R3-05: each of mkdir, rmdir and rename under a directory
        # descriptor is required before anything is opened or written.
        release, _ = self.band_release()
        for call in (os.mkdir, os.rmdir, os.rename):
            with self.subTest(call=call.__name__):
                with mock.patch.object(statement_module.os, "supports_dir_fd",
                                       os.supports_dir_fd - {call}), \
                        self.assertRaisesRegex(
                            AlexandriaError,
                            "^this platform cannot perform a confined statement parts write$",
                        ):
                    emit_statement_parts(release, self.outputs / "set")
                self.assertEqual(listing(self.outputs), {})


def open_descriptors() -> int:
    return len(os.listdir("/dev/fd"))


class StatementPartsDescriptorTests(PartsCase):
    """S3-R3-06: no descriptor the writer opens outlives it, written or refused."""

    def test_no_descriptor_outlives_a_write_or_a_refusal(self):
        real_verify = release_module.verify
        real_open = statement_module.os.open
        refused = mock.Mock(side_effect=OSError("rename refused"))
        verified = []

        def changing(root):
            verified.append(root)
            return real_verify(root) if len(verified) == 1 else "sha256:" + "0" * 64

        def swapping(name, flags, mode=0o777, *, dir_fd=None):
            if flags & os.O_DIRECTORY and dir_fd is not None and name.startswith(".set.tmp-"):
                os.rename(name, "ours", src_dir_fd=dir_fd, dst_dir_fd=dir_fd)
                os.mkdir(name, 0o700, dir_fd=dir_fd)
            return real_open(name, flags, mode, dir_fd=dir_fd)

        cases = (
            ("written", None, ()),
            ("a changed release",
             "^release changed while its statement parts were emitted$",
             ((statement_module, "verify", changing),)),
            ("a failed rename",
             r"^cannot write release statement parts: rename refused$",
             ((statement_module.os, "rename", refused),
              (statement_module.os, "supports_dir_fd", os.supports_dir_fd | {refused}))),
            ("a directory swapped in as it is opened",
             "^statement parts temporary directory changed during emission$",
             ((statement_module.os, "open", swapping),
              (statement_module.os, "supports_dir_fd", os.supports_dir_fd | {swapping}))),
        )
        for number, (label, pattern, patches) in enumerate(cases):
            with self.subTest(case=label):
                release, _ = self.band_release(f"release-{number}")
                outputs = self.root / f"outputs-{number}"
                outputs.mkdir()
                with ExitStack() as stack:
                    for owner, name, value in patches:
                        stack.enter_context(mock.patch.object(owner, name, value))
                    before = open_descriptors()
                    if pattern is None:
                        emit_statement_parts(release, outputs / "set")
                    else:
                        with self.assertRaisesRegex(AlexandriaError, pattern):
                            emit_statement_parts(release, outputs / "set")
                    self.assertEqual(open_descriptors(), before)


def _is_directory(descriptor) -> bool:
    return stat.S_ISDIR(os.fstat(descriptor).st_mode)


class PinnedStatementOutputTests(unittest.TestCase):
    """The section 3 statements keep their SHA-256 through `statement --output`."""

    def test_the_pinned_statements_keep_their_bytes_through_output(self):
        with tempfile.TemporaryDirectory(prefix="alexandria-statement-pinned-output-") as name:
            scratch = Path(name).resolve()
            releases = pinned_releases(scratch)
            expected = dict(PINNED)
            for label, (variable, release_id, digest) in EXTERNAL_PINNED.items():
                if os.environ.get(variable):
                    releases[label] = Path(os.environ[variable])
                    expected[label] = (release_id, digest)
            self.assertGreaterEqual(len(expected), 9)
            for label, (release_id, digest) in sorted(expected.items()):
                with self.subTest(release=label):
                    output = scratch / f"{label}.statement.json"
                    result = run_command("statement", releases[label], "--output", output)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(json.loads(result.stdout)["release_id"], release_id)
                    self.assertEqual(hashlib.sha256(output.read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
