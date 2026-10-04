"""Archive selection, native-value parity and dossier gates without a subgraph."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import importlib.util
import io
import json
import os
from pathlib import Path
import socket
import tempfile
import unittest
from unittest import mock

from . import support
import probitas
from probitas_lib import gates, render, wildcat_archive
from probitas_lib.adapters import wildcat
from probitas_lib.evidence import Evidence, EvidenceError

_spec = importlib.util.spec_from_file_location(
    "tabularium_wildcat_fixture", Path(support.PLUGIN_ROOT).parent / "tabularium/tests/test_wildcat_view.py"
)
fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixture)


class WildcatArchiveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.temp.cleanup)
        cls.root = Path(cls.temp.name).resolve()
        cls.releases = {generation: fixture.release_fixture(cls.root / generation, generation)
                        for generation in ("wildcat-v1", "wildcat-v2")}

    def collect_cli(self, address=fixture.BORROWER, extra=()):
        args = ["collect", "--entity", "Synthetic borrower", "--address", address, "--out", "-"]
        for path in self.releases.values():
            args.extend(("--wildcat-release", str(path)))
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = probitas.main([*args, *extra])
        self.assertEqual(code, 0)
        return json.loads(out.getvalue())

    def test_archive_only_is_offline_and_renders_all_five_gates(self):
        with mock.patch.object(socket, "socket", side_effect=AssertionError("network")):
            payload = self.collect_cli()
        self.assertEqual(len(payload["records"]), 8)
        dossier = render.render(payload)
        self.assertIn("At deployment:", dossier)
        self.assertIn("MarketClosed event recorded", dossier)
        self.assertIn("raw units", dossier)
        self.assertNotIn("closed by the borrower", dossier)
        for result in gates.check(dossier, payload):
            self.assertTrue(result.passed, result.detail)
        for record in payload["records"]:
            self.assertIn("archive_release", record["values"])
            self.assertIn("binding_component_sha256", record["values"])
            self.assertEqual(record["address"], fixture.BORROWER)
            self.assertTrue(record["source"].startswith("doc:sha256:"))

    def test_archive_suppresses_wildcat_adapter_even_beside_live(self):
        with mock.patch.dict(probitas.ADAPTERS, {"wildcat": mock.Mock(side_effect=AssertionError("subgraph"))}, clear=True):
            payload = self.collect_cli(extra=("--live",))
        self.assertEqual(len(payload["records"]), 8)
        self.assertTrue(all(c["source"] == "archive" for c in payload["coverage"] if c["venue"] == "wildcat"))

    def test_repayment_sender_does_not_gain_borrower_history(self):
        payload = self.collect_cli(address=fixture.PAYER)
        self.assertEqual(payload["records"], [])
        self.assertTrue(any("partial" in (c["note"] or "") for c in payload["coverage"] if c["venue"] == "wildcat"))
        self.assertTrue(any("market standing" in gap["subject"] for gap in payload["gaps"]))

    def test_duplicate_generation_refuses_without_mutating_evidence(self):
        evidence = Evidence("Synthetic borrower", [(fixture.BORROWER, "declared")])
        path = self.releases["wildcat-v1"]
        with self.assertRaisesRegex(EvidenceError, "multiple Wildcat"):
            wildcat_archive.collect([path, path], evidence)
        self.assertFalse(evidence.records)

    def test_bad_release_fails_without_subgraph_fallback(self):
        with mock.patch.dict(probitas.ADAPTERS, {"wildcat": mock.Mock(side_effect=AssertionError("subgraph"))}, clear=True):
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                result = probitas.main(["collect", "--entity", "Synthetic", "--address", fixture.BORROWER,
                                        "--wildcat-release", str(self.root / "missing"), "--out", "-"])
        self.assertEqual(result, 2)

    def test_supported_fields_match_subgraph_projection_in_both_generations(self):
        # The old route is a comparison only. Its current-state fields are not
        # supplied to, or consulted by, the archive route.
        payload = self.collect_cli()
        source = json.loads((Path(support.PLUGIN_ROOT) / "tests/fixtures/clean/wildcat.json").read_bytes())
        market = deepcopy(source["markets"][0])
        market.update({"name": "Synthetic market", "originalReserveRatioBips": "2000",
                       "annualInterestBips": "1200", "delinquencyGracePeriod": "7200",
                       "delinquencyFeeBips": "300"})
        market["borrowRecords"] = market["borrowRecords"][:1]
        market["borrowRecords"][0]["assetAmount"] = "123456789"
        market["repaymentRecords"] = market["repaymentRecords"][:1]
        market["repaymentRecords"][0]["assetAmount"] = "98765432"
        original = wildcat._market_records(market, "declared")
        terms = next(record for record in original if record.claim == "market_terms")
        for row in (r for r in payload["records"] if r["claim"] == "market_terms"):
            for field in ("market_name", "reserve_ratio_bips", "annual_interest_bips",
                          "grace_period_seconds", "delinquency_fee_bips"):
                self.assertEqual(row["values"][field], terms.values[field])
            self.assertEqual(row["values"]["terms_at"], "deployment")
        for claim in ("borrow", "repayment"):
            expected = next(record.values["amount"] for record in original if record.claim == claim)
            for row in (r for r in payload["records"] if r["claim"] == claim):
                self.assertEqual(row["values"]["amount"], expected)

    def test_consumer_output_cannot_overwrite_the_preserved_release(self):
        release = self.releases["wildcat-v1"]
        target = release / "manifest.json"
        before = target.read_bytes()
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            code = probitas.main(["collect", "--entity", "Synthetic", "--address", fixture.BORROWER,
                                  "--wildcat-release", str(release), "--out", str(target)])
        self.assertEqual(code, 2)
        self.assertEqual(target.read_bytes(), before)

    def test_output_link_to_preserved_evidence_is_refused(self):
        release = self.releases["wildcat-v1"]
        with tempfile.TemporaryDirectory() as directory:
            linked = Path(directory).resolve() / "alias.json"
            os.link(release / "manifest.json", linked)
            with self.assertRaisesRegex(EvidenceError, "hard-linked"):
                wildcat_archive.output_path(linked, [release])

    def test_archive_cli_writes_an_ordinary_output(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory).resolve() / "evidence.json"
            with redirect_stderr(io.StringIO()):
                code = probitas.main(["collect", "--entity", "Synthetic", "--address", fixture.BORROWER,
                                      "--wildcat-release", str(self.releases["wildcat-v1"]), "--out", str(target)])
            self.assertEqual(code, 0)
            self.assertEqual(len(json.loads(target.read_bytes())["records"]), 4)


if __name__ == "__main__":
    unittest.main()
