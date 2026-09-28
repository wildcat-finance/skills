"""The V1 emitter harness is bound to its source, its compiler and #1962's rows.

`plugins/hexaemeron/harness/v1/` holds the V1 counterpart of the V2 emitter
suite (#1964). Its protocol source is named by identity in
`v1/PROVENANCE.json` and fetched under `v1/src/vendor/`, and it builds under
the `v1` Foundry profile. These tests hold that record's shape, bind the
profile to the compiler the accepted registry records for the V1 builds, pair
every fetched emitter with one fuzz case, and reconcile the mirror references
with every row of the #1962 emitter table. The registry and the table live in
the repository root, so the tests that read them skip where the plugin is
installed alone. Nothing here fetches or writes.
"""

import importlib.util
import json
import os
import re
import tomllib
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.normpath(os.path.join(HERE, os.pardir, "harness"))
REPOSITORY = os.path.normpath(os.path.join(HARNESS, os.pardir, os.pardir, os.pardir))
V1 = os.path.join(HARNESS, "v1")
RECORD = os.path.join(V1, "PROVENANCE.json")
PROFILE = os.path.join(HARNESS, "foundry.toml")
IGNORE = os.path.join(HARNESS, ".gitignore")
FETCHER = os.path.join(HARNESS, "fetch_protocol.py")
MIRROR = os.path.join(V1, "src", "MirrorEmitReference.sol")
SUITE = os.path.join(V1, "test", "EmitterFidelity.t.sol")
REGISTRY = os.path.join(REPOSITORY, "docs", "kickoff", "1359", "targets.json")
TABLE = os.path.join(REPOSITORY, "docs", "kickoff", "1962", "emitters.json")
EMITTER_FILES = (
    os.path.join(V1, "src", "vendor", "libraries", "MarketEvents.sol"),
    os.path.join(V1, "src", "vendor", "spherex", "SphereXProtectedEvents.sol"),
)
PROTOCOL_REF = "da74452aa7d1a0f024d99efd22cc6d950a8116b7"
EXPECTED_FILES = 16
EXPECTED_TOTAL_BYTES = 68288
EXPECTED_EMITTERS = 26
EXPECTED_ROWS = 37
EMITTER_PATTERN = re.compile(r"^function emit_(\w+)\s*\(", re.MULTILINE)
CASE_PATTERN = re.compile(r"^\s*function test_emit_(\w+?)_(indexed\d)\s*\(", re.MULTILINE)
MIRROR_PATTERN = re.compile(r"^\s*function mirror_([A-Za-z0-9]+)_([A-Za-z0-9]+)\s*\(", re.MULTILINE)
PAIR_PATTERN = re.compile(r"function _pair_(\w+)\s*\((.*?)\n  \}", re.DOTALL)
MIRROR_CALL = re.compile(r"mirror\.mirror_([A-Za-z0-9]+)_([A-Za-z0-9]+)\s*\(")


def read(path):
    with open(path, "rb") as fh:
        return fh.read().decode("utf-8")


def load_json(path):
    return json.loads(read(path))


def load_fetcher():
    spec = importlib.util.spec_from_file_location("harness_fetch_protocol_v1", FETCHER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fetched():
    return all(os.path.isfile(path) for path in EMITTER_FILES)


def emitter_names():
    names = []
    for path in EMITTER_FILES:
        names.extend(EMITTER_PATTERN.findall(read(path)))
    return names


def registry_row():
    rows = load_json(REGISTRY)["targets"]
    return next(row for row in rows if row["id"] == "wildcat-v1-ethereum-mainnet")


def mirrors():
    return MIRROR_PATTERN.findall(read(MIRROR))


def pair_calls():
    """{event: [declaring types the event's pairing helper calls, in order]}."""
    calls = {}
    for event, body in PAIR_PATTERN.findall(read(SUITE)):
        found = MIRROR_CALL.findall(body)
        if not all(name == event for _declaring, name in found):
            raise AssertionError(f"_pair_{event} calls a mirror of another event")
        calls[event] = [declaring for declaring, _name in found]
    return calls


class V1ProvenanceTests(unittest.TestCase):
    def test_record_names_wildcat_protocol_at_the_registry_commit(self):
        record = load_json(RECORD)
        self.assertEqual(record["schema"], "wildcat.hexaemeron-harness-source.v1")
        self.assertEqual(record["repository"], "wildcat-finance/wildcat-protocol")
        self.assertEqual(record["ref"], PROTOCOL_REF)
        self.assertEqual(record["destination"], "v1/src/vendor")
        self.assertEqual(record["registry_row"], "wildcat-v1-ethereum-mainnet")
        self.assertTrue(record["source_url_template"].startswith("https://raw.githubusercontent.com/"))

    def test_every_entry_is_a_digest_under_the_destination_mirroring_upstream(self):
        record = load_json(RECORD)
        self.assertEqual(len(record["files"]), EXPECTED_FILES)
        paths = [entry["path"] for entry in record["files"]]
        self.assertEqual(len(paths), len(set(paths)))
        for entry in record["files"]:
            with self.subTest(path=entry["path"]):
                self.assertRegex(entry["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(entry["bytes"], 0)
                self.assertEqual(entry["path"], "v1/src/vendor/" + entry["upstream_path"][len("src/"):])
        self.assertEqual(sum(entry["bytes"] for entry in record["files"]), EXPECTED_TOTAL_BYTES)
        self.assertEqual(record["total_bytes"], EXPECTED_TOTAL_BYTES)

    def test_the_record_loads_through_the_fetcher_and_is_one_of_its_records(self):
        fetcher = load_fetcher()
        self.assertIn(RECORD, fetcher.RECORDS)
        self.assertEqual(fetcher.load_record(RECORD)["ref"], PROTOCOL_REF)

    def test_a_clone_read_must_name_its_record(self):
        fetcher = load_fetcher()
        with self.assertRaises(SystemExit) as caught:
            fetcher.main(["--from-git", "/nonexistent"])
        self.assertEqual(caught.exception.code, 2)

    def test_the_fetched_directory_is_never_committed(self):
        self.assertIn("/v1/src/vendor/", read(IGNORE).splitlines())

    @unittest.skipUnless(fetched(), "V1 source not fetched; run plugins/hexaemeron/harness/fetch_protocol.py")
    def test_every_fetched_file_carries_its_recorded_bytes(self):
        fetcher = load_fetcher()
        self.assertEqual(fetcher.check(fetcher.load_record(RECORD), HARNESS), [])


class V1ProfileTests(unittest.TestCase):
    def setUp(self):
        with open(PROFILE, "rb") as fh:
            self.profiles = tomllib.load(fh)["profile"]

    def test_the_v1_profile_has_its_own_trees_and_no_library(self):
        v1 = self.profiles["v1"]
        self.assertEqual((v1["src"], v1["test"], v1["out"], v1["libs"]), ("v1/src", "v1/test", "out/v1", []))
        self.assertEqual(self.profiles["default"]["src"], "src")

    @unittest.skipUnless(os.path.isfile(REGISTRY), "the accepted registry is not in this tree")
    def test_the_v1_profile_uses_the_compiler_the_registry_records(self):
        v1, compiler = self.profiles["v1"], registry_row()["source"]["compiler"]
        self.assertEqual(compiler["solc"].split("+")[0], v1["solc"])
        self.assertEqual(compiler["evm_version"], v1["evm_version"])
        self.assertEqual(compiler["optimizer_runs"], v1["optimizer_runs"])
        self.assertEqual(compiler["via_ir"], v1["via_ir"])
        self.assertEqual(compiler["bytecode_hash"], v1["bytecode_hash"])
        self.assertTrue(v1["optimizer"])

    @unittest.skipUnless(os.path.isfile(REGISTRY), "the accepted registry is not in this tree")
    def test_the_provenance_commit_is_the_registry_commit(self):
        self.assertEqual(registry_row()["source"]["commit"], load_json(RECORD)["ref"])


@unittest.skipUnless(fetched(), "V1 source not fetched; run plugins/hexaemeron/harness/fetch_protocol.py")
class V1PairingTests(unittest.TestCase):
    def test_the_two_emitter_files_declare_the_pinned_emitter_count(self):
        self.assertEqual(len(emitter_names()), EXPECTED_EMITTERS)

    def test_every_emitter_has_exactly_one_case_and_no_case_is_orphaned(self):
        cases = [name for name, _label in CASE_PATTERN.findall(read(SUITE))]
        self.assertEqual(sorted(cases), sorted(set(cases)), "a case is duplicated")
        self.assertEqual(sorted(cases), sorted(emitter_names()))


class V1RowReconciliationTests(unittest.TestCase):
    """Each #1962 row has its own reference, and its emitter's case calls it."""

    def test_mirror_functions_are_unique(self):
        found = mirrors()
        self.assertEqual(len(found), len(set(found)))
        self.assertEqual(len(found), EXPECTED_ROWS)

    def test_every_mirror_is_called_by_its_emitters_pairing_helper(self):
        called = sorted((declaring, event) for event, types in pair_calls().items() for declaring in types)
        self.assertEqual(called, sorted(mirrors()))

    @unittest.skipUnless(os.path.isfile(TABLE), "the #1962 table is not in this tree")
    def test_every_row_of_the_1962_table_has_a_reference_and_nothing_else_does(self):
        table = load_json(TABLE)
        self.assertEqual(table["source"]["commit"], PROTOCOL_REF)
        rows = sorted((r["declaration"].split(".")[0], r["emitter"][len("emit_"):]) for r in table["rows"])
        self.assertEqual(len(rows), EXPECTED_ROWS)
        self.assertEqual(rows, sorted(mirrors()))

    @unittest.skipUnless(os.path.isfile(TABLE), "the #1962 table is not in this tree")
    def test_the_1962_table_leaves_no_row_unreviewed_unreached_or_mismatched(self):
        summary = load_json(TABLE)["summary"]
        self.assertEqual((summary["unreviewed"], summary["unreached_rows"], summary["mismatch_rows"]), (0, 0, 0))


if __name__ == "__main__":
    unittest.main()
