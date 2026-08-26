"""The checked-in Goldfinch fixture runs and remains offline reproducible."""

import ipaddress
from pathlib import Path
import runpy
import socket
import subprocess
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

from lazarus_lib.canonical import load, loads
from lazarus_lib.verifier import verify_fixture

from . import support


FIXTURE = support.PLUGIN_ROOT / "examples" / "goldfinch-v0"
ANCHOR_FIXTURE = support.PLUGIN_ROOT / "examples" / "multi-provider-anchor-v0"
DEMO_PATH = FIXTURE / "demo.py"
TRANSACTION = "0xa46a744d6d52528a660c1d99a4edde403504fe7a308118c7cc947819583ce699"
MARKET = "0x8bbd80f88e662e56b918c353da635e210ece93c6"


def load_demo():
    return SimpleNamespace(**runpy.run_path(str(DEMO_PATH)))


class GoldfinchDemoTests(unittest.TestCase):
    def test_synthetic_multi_provider_fixture_keeps_anchor_claims_false(self):
        report = verify_fixture(ANCHOR_FIXTURE)
        self.assertEqual(
            report["fixture_digest"],
            "188eb293ac1de8036ff4be861e339fe5757b51995c88e8ea1afcfa498134a72e",
        )
        self.assertEqual(
            report["chain_anchors"],
            {
                "records": 2,
                "canonical_chain_claim": False,
                "provider_independence_claim": False,
            },
        )
        self.assertEqual(
            report["evidence_counts"],
            {"proof_backed": 3, "header_bound": 1, "recorded_rpc": 1},
        )
        fixture_bytes = b"".join(
            path.read_bytes() for path in ANCHOR_FIXTURE.rglob("*") if path.is_file()
        )
        self.assertNotIn(b"provider_url", fixture_bytes)
        self.assertNotIn(b"rpc-url", fixture_bytes)

    def test_fixture_verifies_with_expected_evidence_and_provenance(self):
        report = verify_fixture(FIXTURE)
        self.assertEqual(
            report["fixture_digest"],
            "d93cd09fcb2c6bd689a223398ebd4ae4dc480ec7d8fd8e64283b88341d0a7e49",
        )
        self.assertEqual(
            report["evidence_counts"],
            {"proof_backed": 2, "header_bound": 1, "recorded_rpc": 4},
        )
        self.assertEqual(report["proof_backed"]["accounts_included"], 1)
        self.assertEqual(report["proof_backed"]["storage_included"], 1)
        self.assertFalse(report["header_bound"]["canonical_chain_claim"])

        source = (
            support.REPO_ROOT
            / "plugins"
            / "tabularium"
            / "examples"
            / "goldfinch-v0"
            / "events.jsonl"
        )
        first = loads(source.read_text(encoding="utf-8").splitlines()[0].encode())
        self.assertEqual(first["instrument"]["id"], MARKET)
        self.assertEqual(first["transaction"]["hash"], TRANSACTION)

    def test_demo_command_runs_the_complete_application_check(self):
        result = subprocess.run(
            [sys.executable, str(DEMO_PATH)],
            cwd=support.REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("replayed code bytes: 45", result.stdout)
        self.assertIn("replayed logs: 5", result.stdout)
        self.assertIn("slot 0x1 miss: -32070", result.stdout)
        self.assertIn("one-nibble proof mutation: rejected", result.stdout)
        self.assertIn("manifest rebuild: identical", result.stdout)

    def test_manifest_rebuild_is_byte_identical(self):
        demo = load_demo()
        before = (FIXTURE / "manifest.json").read_bytes()
        demo.rebuild_manifest_bytes(load(FIXTURE / "manifest.json"))
        self.assertEqual((FIXTURE / "manifest.json").read_bytes(), before)

    def test_one_nibble_proof_mutation_is_rejected(self):
        demo = load_demo()
        demo.reject_mutated_proof(load(FIXTURE / "manifest.json"))

    def test_application_replay_and_miss_cannot_leave_loopback(self):
        demo = load_demo()
        real_connect = socket.socket.connect
        destinations = []

        def guarded_connect(sock, address):
            destinations.append(address)
            if not ipaddress.ip_address(address[0]).is_loopback:
                raise AssertionError(f"outbound demo connection: {address}")
            return real_connect(sock, address)

        with mock.patch.object(socket.socket, "connect", guarded_connect):
            report = demo.run_demo()
        self.assertEqual(report["miss"], -32070)
        self.assertEqual(report["slot_zero"], "0x" + "00" * 31 + "01")
        self.assertTrue(destinations)
        self.assertTrue(
            all(ipaddress.ip_address(item[0]).is_loopback for item in destinations)
        )

    def test_schema_snapshots_and_fixture_inventory_are_exact(self):
        schema_names = {
            "header-v1.json",
            "manifest-v1.json",
            "plan-v1.json",
            "proof-record-v1.json",
            "rpc-record-v1.json",
        }
        for name in schema_names:
            with self.subTest(name=name):
                self.assertEqual(
                    (FIXTURE / "schemas" / name).read_bytes(),
                    (support.PLUGIN_ROOT / "schemas" / name).read_bytes(),
                )
        manifest = load(FIXTURE / "manifest.json")
        declared = {item["path"] for item in manifest["components"]}
        actual = {
            path.relative_to(FIXTURE).as_posix()
            for path in FIXTURE.rglob("*")
            if path.is_file() and path.name != "manifest.json"
        }
        self.assertEqual(declared, actual)
        self.assertNotIn("rpc_url", DEMO_PATH.read_text(encoding="utf-8").lower())


if __name__ == "__main__":
    unittest.main()
