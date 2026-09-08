"""Finite capture boundaries and byte-identical rebuilding for the Wildcat specimen."""

import importlib.util
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

EXAMPLE = Path(__file__).resolve().parents[1] / "examples/wildcat-mainnet-v0"
SPEC = importlib.util.spec_from_file_location("wildcat_rebuild", EXAMPLE / "rebuild.py")
BUILDER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILDER)


def inventory(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


class WildcatReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.inputs = self.root / "inputs"
        import shutil
        shutil.copytree(EXAMPLE / "inputs", self.inputs)
        self.output = self.root / "release"

    def assert_refused(self, pattern):
        with self.assertRaisesRegex(BUILDER.BereanError, pattern):
            BUILDER.build(self.inputs, self.output)
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob(".wildcat-stage-*")))

    def mutate_reads(self, mutate):
        path = self.inputs / "lazarus-fixture/rpc.jsonl"
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        mutate(rows)
        for row in rows:
            row["request_key"] = BUILDER.reads.request_key(row["method"], row["params"])
        path.write_text("".join(json.dumps(row) + "\n" for row in rows))

    def test_rebuild_identical_with_network_disabled(self):
        original = inventory(EXAMPLE / "release")
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network forbidden")), \
                mock.patch.object(socket, "create_connection", side_effect=AssertionError("network forbidden")), \
                mock.patch.object(socket, "getaddrinfo", side_effect=AssertionError("network forbidden")):
            digest = BUILDER.build(self.inputs, self.output)
        self.assertEqual(original, inventory(self.output))
        self.assertEqual(digest, json.loads(original["release.json"])["release_digest"])

    def test_recorded_values_and_exact_official_blobs(self):
        content, decoded = BUILDER.load_inputs(self.inputs)
        self.assertEqual({key: pair[1] for key, pair in decoded.items()}, {
            "delinquencyfeebips": 0, "delinquencygraceperiod": 172800,
            "registered-market": True,
            "asset": "0xdac17f958d2ee523a2206206994597c13d831ec7",
            "borrower": "0xde8845ff1d67b84e755a57481097e712460ac21b",
        })
        official = {key.removeprefix("fixtures/docs/"): data for key, data in content.items()
                    if key.startswith("fixtures/docs/")}
        self.assertEqual(len(official), 3)
        self.assertEqual(sum(map(len, official.values())), 40001)
        self.assertEqual(official, inventory(EXAMPLE / "release/corpus/fixtures/docs/official"))
        self.assertEqual(content["lazarus-fixture/rpc.jsonl"], (EXAMPLE / "release/reads.jsonl").read_bytes())

    def test_altered_source_even_with_rewritten_provenance(self):
        path = self.inputs / "fixtures/docs/using-wildcat/delinquency.md"
        path.write_bytes(path.read_bytes() + b"changed")
        provenance = self.inputs / "docs-provenance.json"
        rows = json.loads(provenance.read_text())
        rows[1]["sha256"] = BUILDER.digests.of_file(str(path))
        provenance.write_text(json.dumps(rows))
        self.assert_refused("captured bytes changed")

    def test_missing_component(self):
        (self.inputs / "lazarus-fixture/rpc.jsonl").unlink()
        self.assert_refused("missing component")

    def test_missing_read(self):
        self.mutate_reads(lambda rows: rows.pop())
        self.assert_refused("expected five records")

    def test_changed_read(self):
        self.mutate_reads(lambda rows: rows[0]["outcome"].update(result="0x" + "0" * 63 + "2"))
        self.assert_refused("captured bytes changed")

    def test_wrong_chain_or_block(self):
        path = self.inputs / "lazarus-fixture/manifest.json"
        original = path.read_bytes()
        for field in ("chain", "block"):
            with self.subTest(field=field):
                document = json.loads(original)
                if field == "chain":
                    document["chain_id"] = "0xa"
                else:
                    document["block"]["hash"] = "0x" + "a" * 64
                path.write_text(json.dumps(document))
                self.assert_refused("wrong chain or block")

    def test_method_target_selector_and_call_block_drift(self):
        path = self.inputs / "lazarus-fixture/rpc.jsonl"
        original = path.read_bytes()
        mutations = (
            lambda rows: rows[0].update(method="eth_getStorageAt"),
            lambda rows: rows[0]["params"][0].update(to="0x" + "1" * 40),
            lambda rows: rows[0]["params"][0].update(data="0xffffffff"),
            lambda rows: rows[0]["params"].__setitem__(1, "latest"),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                path.write_bytes(original)
                self.mutate_reads(mutation)
                self.assert_refused("method, target, selector, block or evidence drift")

    def test_abi_word_length_and_padding(self):
        path = self.inputs / "lazarus-fixture/rpc.jsonl"
        original = path.read_bytes()
        for word in ("0x0", "0x" + "0" * 66, "0x" + "g" * 64):
            with self.subTest(word=word):
                path.write_bytes(original)
                self.mutate_reads(lambda rows: rows[0]["outcome"].update(result=word))
                self.assert_refused("canonical ABI word")
        for name, word, error in (("asset", "0x" + "f" * 64, "address padding"),
                                  ("registered-market", "0x" + "0" * 63 + "2", "invalid ABI bool")):
            path.write_bytes(original)
            self.mutate_reads(lambda rows: next(row for row in rows if row["name"] == name)["outcome"].update(result=word))
            self.assert_refused(error)

    def test_occupied_destination_preserves_promotion_chain(self):
        BUILDER.build(self.inputs, self.output)
        before = inventory(self.output)
        with self.assertRaisesRegex(BUILDER.BereanError, "occupied"):
            BUILDER.build(self.inputs, self.output)
        self.assertEqual(before, inventory(self.output))
        self.assertEqual(before["promotions.jsonl"], (self.output / "promotions.jsonl").read_bytes())

    def test_existing_empty_directory_and_symlink_refused(self):
        self.output.mkdir()
        with self.assertRaisesRegex(BUILDER.BereanError, "occupied"):
            BUILDER.build(self.inputs, self.output)
        self.output.rmdir()
        self.output.symlink_to(self.root / "absent")
        with self.assertRaisesRegex(BUILDER.BereanError, "occupied"):
            BUILDER.build(self.inputs, self.output)
        self.assertTrue(self.output.is_symlink())

    def test_input_links_and_undeclared_files_refused(self):
        path = self.inputs / "blockscout-anchor.json"
        original = path.read_bytes()
        path.unlink()
        path.symlink_to(EXAMPLE / "inputs/blockscout-anchor.json")
        with self.assertRaisesRegex(BUILDER.BereanError, "symlink component"):
            BUILDER.build(self.inputs, self.output)
        self.assertFalse(self.output.exists())
        path.unlink()
        path.write_bytes(original)
        (self.inputs / "extra.txt").write_text("extra")
        self.assert_refused("undeclared component")

    def test_empty_undeclared_tree_is_not_traversed(self):
        deep = self.inputs / "extra"
        for _ in range(40):
            deep = deep / "empty"
        deep.mkdir(parents=True)
        self.assert_refused("undeclared component")

    def test_atomic_landing_refuses_concurrent_empty_directory(self):
        stage = self.root / "stage"
        stage.mkdir()
        (stage / "sentinel").write_bytes(b"kept")
        self.output.mkdir()
        with self.assertRaises(FileExistsError):
            BUILDER.land_exclusively(stage, self.output)
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertEqual((stage / "sentinel").read_bytes(), b"kept")

    def test_failure_cleans_stage_and_never_lands_partial(self):
        with mock.patch.object(BUILDER.release, "build", side_effect=BUILDER.BereanError("forced verification failure")):
            self.assert_refused("forced verification failure")

    def test_all_adversarial_classes_and_scope_refusals(self):
        cases = json.loads((EXAMPLE / "release/evals/cases.json").read_text())["cases"]
        self.assertEqual({case["adversarial"] for case in cases if case["adversarial"]}, {
            "stale-state", "poisoned-document", "prompt-injection", "citation-mismatch", "unsupported-inference"})
        self.assertEqual({case["answer"]["refusal"]["boundary"] for case in cases
                          if case["answer"]["kind"] == "refusal"}, set(BUILDER.BOUNDARIES))
        report, _ = BUILDER.evals.run(str(EXAMPLE / "release"))
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["cases"], 10)


if __name__ == "__main__":
    unittest.main()
