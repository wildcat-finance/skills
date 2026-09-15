"""The positional epoch demonstration: literal owners, offline, and refusing.

`examples/usdc-interval-epochs-v0` builds a synthetic v2 release over an upgrade
block with a proxy log on each side of the announcement, and a second v2
release from the preserved live staging bytes. These tests hold it to the
literal owners, to the pinned identifiers, to its refusal probes and to the
bytes it reads but must not change. The example is loaded by path under its own
module name, because two sibling examples also ship a `demo.py`.
"""

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import socket
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
EXAMPLE = PLUGIN / "examples" / "usdc-interval-epochs-v0"
MODULE_NAME = "usdc_interval_epochs_demo"

sys.path.insert(0, str(PLUGIN / "scripts"))

from alexandria_lib.canonical import canonical_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402


def demo():
    """Import the demonstration, failing rather than skipping when it is absent."""
    for name in ("demo.py", "expected.json", "live-v2-expected.json", "README.md"):
        if not (EXAMPLE / name).is_file():
            raise AssertionError(f"the positional epoch demonstration is missing {name} at {EXAMPLE}")
    if MODULE_NAME not in sys.modules:
        spec = importlib.util.spec_from_file_location(MODULE_NAME, EXAMPLE / "demo.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[MODULE_NAME] = module
        spec.loader.exec_module(module)
    return sys.modules[MODULE_NAME]


def tree_digests(root):
    return {
        path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and "__pycache__" not in path.parts
    }


class EpochDemoTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module = demo()
        cls.directory = tempfile.TemporaryDirectory()
        cls.root = Path(cls.directory.name)
        with mock.patch.object(socket.socket, "connect", side_effect=AssertionError("network used")):
            cls.summary = cls.module.build(cls.root / "shared")
            cls.verified = cls.module.verify(cls.root / "shared")

    @classmethod
    def tearDownClass(cls):
        cls.directory.cleanup()

    def copy(self, name):
        target = self.root / name
        shutil.copytree(self.root / "shared", target)
        self.addCleanup(shutil.rmtree, target, True)
        return target

    def row(self, block, transaction, log):
        rows = [
            row for row in self.summary["synthetic"]["ownership"]
            if (row["block_number"], row["transaction_index"], row["log_index"]) == (block, transaction, log)
        ]
        self.assertEqual(len(rows), 1)
        return rows[0]


class LiteralOwnershipTests(EpochDemoTestCase):
    def test_build_and_verify_agree_without_a_socket(self):
        self.assertEqual(self.summary, self.verified)

    def test_the_upgrade_block_has_literal_old_and_new_owners(self):
        before = self.row("15331626", 1, 3)
        boundary = self.row("15331626", 2, 4)
        after = self.row("15331626", 3, 5)
        self.assertEqual((before["kind"], before["epoch_index"]), ("proxy-log", 0))
        self.assertEqual(before["implementation"], "0x42f9505a376761b180e27a01ba0554244ed1de7d")
        self.assertEqual((boundary["kind"], boundary["epoch_index"]), ("upgrade-boundary", 1))
        self.assertEqual(boundary["implementation"], "0x8b3e1f2a4c5d6e7f8091a2b3c4d5e6f708192a3b")
        self.assertEqual((after["kind"], after["epoch_index"]), ("proxy-log", 1))
        self.assertEqual(after["implementation"], "0x8b3e1f2a4c5d6e7f8091a2b3c4d5e6f708192a3b")

    def test_every_preserved_log_has_one_owner(self):
        rows = self.summary["synthetic"]["ownership"]
        self.assertEqual(len(rows), 17)
        self.assertEqual([row["kind"] for row in rows].count("upgrade-boundary"), 1)
        self.assertEqual(sum(1 for row in rows if row["epoch_index"] == 0), 7)

    def test_both_releases_state_positional_semantics(self):
        self.assertEqual(self.summary["synthetic"]["receipt_semantics"], "v2-positional")
        self.assertEqual(self.summary["live"]["receipt_semantics"], "v2-positional")

    def test_the_live_rebuild_has_its_own_recorded_identifier(self):
        live = self.summary["live"]
        pinned = json.loads((EXAMPLE / "live-v2-expected.json").read_text(encoding="utf-8"))
        historical = json.loads((PLUGIN / "examples/usdc-interval-live-v0/expected.json").read_text(encoding="utf-8"))
        self.assertEqual(live["release_id"], pinned["release_id"])
        self.assertEqual(live["historical_release_id"], historical["release_id"])
        self.assertNotEqual(live["release_id"], historical["release_id"])
        self.assertEqual(live["boundaries"], [{"block_number": "25904935", "log_index": 524, "transaction_index": 193}])
        self.assertEqual(sum(sum(counts.values()) for counts in live["attributions"].values()), 93)


class RefusalProbeTests(EpochDemoTestCase):
    def test_ordinary_logs_in_the_upgrade_transaction_refuse(self):
        refusals = self.summary["unsupported_attribution"]
        for name, log in (("ordinary-log-before-announcement", 3), ("ordinary-log-after-announcement", 5)):
            self.assertEqual(refusals[name]["codes"], ["malformed-upgrade-log"])
            self.assertEqual(
                refusals[name]["refusal"],
                f"ordinary proxy log at (15331626, 2, {log}) in an upgrade transaction is unsupported",
            )

    def test_rebound_releases_refuse_on_ownership_not_digests(self):
        hostile = self.summary["hostile_releases"]
        self.assertEqual(hostile["moved-owner"], "log attributions do not match ownership derived from preserved logs")
        self.assertEqual(hostile["moved-boundary"], "the epoch table does not match the epochs the preserved opening reads derive")

    def test_a_rebinding_probe_cannot_pass_by_being_accepted(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(self.module, "check_interval", return_value={}):
                with self.assertRaisesRegex(AlexandriaError, "was accepted"):
                    self.module.rebound_refusal(
                        self.root / "shared" / "synthetic-release", Path(directory), "owner", self.module._move_owner,
                    )

    def test_the_synthetic_fixture_first_block_answer_refuses_under_v2(self):
        self.assertEqual(self.summary["historical_first_block"], "proxy log hash contradicts its epoch boundary")

    def test_an_index_only_disagreement_still_reconciles_as_agreed(self):
        """The open gap the ledger names: the comparison tuple omits transactionIndex."""
        probe = self.summary["index_only_reconciliation"]
        self.assertEqual((probe["primary_transaction_index"], probe["second_transaction_index"]), ("0x3", "0x7"))
        self.assertEqual((probe["status"], probe["disputed"]), ("agreed", 0))


class PreservationTests(EpochDemoTestCase):
    def test_a_second_build_is_identical_and_leaves_its_sources_unchanged(self):
        sources = {
            "live": tree_digests(PLUGIN / "examples" / "usdc-interval-live-v0"),
            "synthetic": tree_digests(PLUGIN / "examples" / "usdc-interval-v0"),
        }
        second = self.root / "second"
        self.addCleanup(shutil.rmtree, second, True)
        self.assertEqual(self.module.build(second), self.summary)
        self.assertEqual(sources["live"], tree_digests(PLUGIN / "examples" / "usdc-interval-live-v0"))
        self.assertEqual(sources["synthetic"], tree_digests(PLUGIN / "examples" / "usdc-interval-v0"))

    def test_a_changed_live_staging_tree_refuses_and_removes_the_output(self):
        output = self.root / "staging-changed"
        digests = iter(["before", "after"])
        with mock.patch.object(self.module, "staging_digest", side_effect=lambda _root: next(digests)):
            with self.assertRaisesRegex(AlexandriaError, "changed the preserved staging bytes"):
                self.module.build(output)
        self.assertFalse(output.exists())

    def test_a_changed_synthetic_source_refuses_and_leaves_no_output(self):
        output = self.root / "source-changed"
        with mock.patch.object(self.module, "SOURCE_SHA256", "0" * 64):
            with self.assertRaisesRegex(AlexandriaError, "pinned digest"):
                self.module.build(output)
        self.assertFalse(output.exists())

    def test_an_existing_output_is_refused_and_kept(self):
        existing = self.root / "existing"
        existing.mkdir()
        (existing / "keep").write_text("preserve", encoding="utf-8")
        self.addCleanup(shutil.rmtree, existing, True)
        with self.assertRaisesRegex(AlexandriaError, "already exists"):
            self.module.build(existing)
        self.assertEqual((existing / "keep").read_text(encoding="utf-8"), "preserve")


class VerifyTamperTests(EpochDemoTestCase):
    def test_a_rewritten_summary_owner_refuses(self):
        built = self.copy("summary-owner")
        summary = json.loads((built / "summary.json").read_text(encoding="utf-8"))
        summary["synthetic"]["ownership"][6]["epoch_index"] = 1
        (built / "summary.json").write_bytes(canonical_bytes(summary))
        with self.assertRaisesRegex(AlexandriaError, "recorded summary"):
            self.module.verify(built)

    def test_a_changed_expectation_owner_refuses(self):
        expected = json.loads((EXAMPLE / "expected.json").read_text(encoding="utf-8"))
        expected["synthetic"]["ownership"][6]["implementation"] = "0x8b3e1f2a4c5d6e7f8091a2b3c4d5e6f708192a3b"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "expected.json"
            path.write_bytes(canonical_bytes(expected))
            with mock.patch.object(self.module, "EXPECTED", path):
                with self.assertRaisesRegex(AlexandriaError, "pinned expectation"):
                    self.module.verify(self.root / "shared")

    def test_a_removed_release_refuses(self):
        built = self.copy("no-live-release")
        shutil.rmtree(built / "live-release")
        with self.assertRaises(AlexandriaError):
            self.module.verify(built)

    def test_the_command_line_returns_one_for_a_missing_build(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            code = self.module.main(["verify", str(self.root / "missing")])
        self.assertEqual(code, 1)
        self.assertIn("usdc-interval-epochs-demo:", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
