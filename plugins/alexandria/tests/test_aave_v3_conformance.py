"""Guard pending conformance and the accepted selection evidence for the Aave
V3 interval design record (fifteen resolvers, three rejected candidates)."""

import contextlib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN = Path(__file__).resolve().parents[1]
ROOT = PLUGIN / "docs/aave-v3-interval"
SPEC = importlib.util.spec_from_file_location("aave_v3_conformance", ROOT / "design/conformance.py")
conformance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(conformance)

DESIGN_LOCK_SHA256 = "cf64d97fe0c852da6df96bb1ba8a4cc21b07366d85faf5030691c1c592e19ae3"
REJECTED_CANDIDATES = (
    "single-interval-venue",
    "log-discovered-subjects",
    "global-transaction-order-rule",
)
GENERATED = ["design-evidence.json", "design/model-observations.json"]
CHAIN_READS = ("design/preflight-sample.json", "design/upgrade-transaction-specimen.json")
# An endpoint, host, header or credential in any key or value of a chain-read
# record.  "loopback" names a transport class, not a host.
LEAK = re.compile(
    r"://|\blocalhost\b|\b\d{1,3}(?:\.\d{1,3}){3}\b|\[?::1\]?|:\d{2,5}\b"
    r"|\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:com|net|org|io|xyz|dev|app|cloud|finance|co|sh)\b"
    r"|authorization|bearer|api[-_]?key|x-[a-z]+-key|\bheaders?\b|\btoken\b|secret|password",
    re.IGNORECASE,
)


class Loader:
    errors = []

    def __init__(self, suite):
        self.suite = suite

    def loadTestsFromNames(self, names):
        return self.suite


class MissingLoader(unittest.TestLoader):
    def loadTestsFromNames(self, names):
        return super().loadTestsFromNames(["tests.missing_aave_specimen.test"] * len(names))


def passing_suite(name, executed):
    class Passed(unittest.TestCase):
        def runTest(self):
            self.assertEqual(2 + 2, 4)
            executed.append("executed")

    return unittest.TestSuite(Passed() for _ in conformance.CASES[name])


def absent_criteria():
    """Criteria whose owning suite module is not in the tree yet."""
    names = []
    for name, ids in conformance.CASES.items():
        modules = {i.split(".")[1] for i in ids}
        if not all((PLUGIN / "tests" / f"{m}.py").exists() for m in modules):
            names.append(name)
    return names


def strings(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from strings(item)
    elif isinstance(value, str):
        yield value


class AaveConformanceHarnessTests(unittest.TestCase):
    """While venue code is absent, every resolver whose identifiers are missing
    refuses, and existing-release-identities-retained runs its four."""

    def test_fifteen_resolver_names_are_declared(self):
        self.assertEqual(
            set(conformance.CASES),
            {
                "registry-reproduces-recorded-subject-set",
                "registry-pin-change-refuses",
                "per-subject-proxy-epochs-derived",
                "unsupported-upgrade-shapes-refuse",
                "other-venues-keep-upgrade-transaction-refusal",
                "wrong-chain-or-market-refuses",
                "collection-refusal-battery",
                "transaction-index-only-disagreement-declared",
                "credential-absent-from-artefacts",
                "segment-plans-tile-the-interval",
                "segment-budget-within-ceilings",
                "preflight-measurement-recorded",
                "production-segments-preserved-and-rebuilt",
                "existing-release-identities-retained",
                "aave-fixture-rebuilds-offline-without-sockets",
            },
        )
        self.assertEqual(conformance.CANDIDATE, "segmented-proxy-set-venue")

    def test_resolvers_match_the_design_record(self):
        record = json.loads((ROOT / "design-evidence.json").read_text())
        rows = [r for r in record["results"]
                if r["candidate"] == conformance.CANDIDATE and r["state"] == "pending"]
        self.assertEqual({r["criterion"] for r in rows}, set(conformance.CASES))
        for row in rows:
            with self.subTest(criterion=row["criterion"]):
                self.assertEqual(row["report"], f"reports/conformance/{conformance.CANDIDATE}-{row['criterion']}.json")
                self.assertEqual(
                    row["resolver"],
                    f"python3 .hexaemeron/design/conformance.py {row['criterion']} --candidate {conformance.CANDIDATE}",
                )

    def test_missing_venue_code_refuses_each_criterion_with_named_counts(self):
        for name in conformance.CASES:
            with self.subTest(criterion=name):
                passed, observed, detail = conformance.execute(name, MissingLoader())
                self.assertFalse(passed)
                self.assertEqual(observed["criterion"], name)
                self.assertEqual(observed["required"], len(conformance.CASES[name]))
                self.assertGreater(observed["loader_errors"], 0)
                self.assertTrue(observed["unresolved"])
                self.assertEqual(observed["reason"], "assertions-unresolved")
                self.assertIn("missing_aave_specimen", detail)

    def test_absent_suite_modules_refuse_through_the_real_loader(self):
        names = absent_criteria()
        if not names:
            self.skipTest("every criterion's suite module exists")
        with mock.patch.object(sys, "path", [str(PLUGIN), *sys.path]):
            for name in names:
                with self.subTest(criterion=name):
                    passed, observed, _ = conformance.execute(name)
                    self.assertFalse(passed)
                    self.assertEqual(observed["reason"], "assertions-unresolved")

    def test_existing_release_identities_run_through_the_real_loader(self):
        # S1-R1-01: this criterion's four identifiers exist at the base commit,
        # so its resolver runs them and passes while the other fourteen refuse.
        name = "existing-release-identities-retained"
        self.assertNotIn(name, absent_criteria())
        with mock.patch.object(sys, "path", [str(PLUGIN), *sys.path]):
            passed, observed, detail = conformance.execute(name)
        self.assertTrue(passed, detail)
        self.assertEqual(observed["required"], 4)
        self.assertEqual(observed["tests_run"], 4)
        self.assertEqual(observed["loader_errors"], 0)
        self.assertEqual(observed["unresolved"], [])
        self.assertIsNone(observed["reason"])

    def test_zero_tests_cannot_pass(self):
        for name in conformance.CASES:
            passed, observed, _ = conformance.execute(name, Loader(unittest.TestSuite()))
            self.assertFalse(passed)
            self.assertEqual(observed["tests_run"], 0)
            self.assertEqual(observed["reason"], "no-assertions-executed")

    def test_fewer_assertions_than_required_cannot_pass(self):
        name = "collection-refusal-battery"
        suite = passing_suite(name, [])
        short = unittest.TestSuite(list(suite)[:-1])
        passed, observed, _ = conformance.execute(name, Loader(short))
        self.assertFalse(passed)
        self.assertEqual(observed["reason"], "assertion-count-mismatch")

    def test_failed_assertions_cannot_pass(self):
        class Failed(unittest.TestCase):
            def runTest(self):
                self.assertEqual("old", "new")

        name = "wrong-chain-or-market-refuses"
        suite = unittest.TestSuite(Failed() for _ in conformance.CASES[name])
        passed, observed, _ = conformance.execute(name, Loader(suite))
        self.assertFalse(passed)
        self.assertEqual(observed["failures"], len(conformance.CASES[name]))
        self.assertEqual(observed["reason"], "assertions-failed")

    def test_skipped_assertions_cannot_pass(self):
        class Skipped(unittest.TestCase):
            @unittest.skip("specimen")
            def runTest(self):
                self.fail("unreachable")

        name = "wrong-chain-or-market-refuses"
        suite = unittest.TestSuite(Skipped() for _ in conformance.CASES[name])
        passed, observed, _ = conformance.execute(name, Loader(suite))
        self.assertFalse(passed)
        self.assertEqual(observed["skipped"], len(conformance.CASES[name]))
        self.assertEqual(observed["reason"], "assertions-skipped")

    def test_refusal_names_the_criterion_and_counts_and_emits_no_report(self):
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", MissingLoader):
                    for name in conformance.CASES:
                        with self.subTest(criterion=name):
                            stdout = io.StringIO()
                            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                                self.assertEqual(conformance.main([name]), 1)
                            line = json.loads(stdout.getvalue())
                            self.assertIs(line["passed"], False)
                            self.assertEqual(line["criterion"], name)
                            self.assertEqual(line["required"], len(conformance.CASES[name]))
                            self.assertEqual(line["reason"], "assertions-unresolved")
                            for key in ("tests_run", "failures", "errors", "skipped", "loader_errors"):
                                self.assertIsInstance(line[key], int)
            self.assertFalse((Path(directory) / ".hexaemeron").exists())

    def test_package_is_inserted_ahead_of_every_other_tests_package(self):
        # The repository root also holds a `tests` package; an identifier must
        # resolve in plugins/alexandria/tests, so the insertion is at position 0.
        seen = []

        class Recording(unittest.TestLoader):
            def loadTestsFromNames(self, names):
                seen.append(sys.path[0])
                return unittest.TestSuite()

        with tempfile.TemporaryDirectory() as directory:
            (Path(directory) / "plugins/alexandria").mkdir(parents=True)
            with mock.patch.object(sys, "path", list(sys.path)):
                with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                    with mock.patch.object(conformance.unittest, "TestLoader", Recording):
                        stdout = io.StringIO()
                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(io.StringIO()):
                            self.assertEqual(conformance.main(["wrong-chain-or-market-refuses"]), 1)
            self.assertEqual(seen, [str(Path(directory) / "plugins/alexandria")])
            self.assertIs(json.loads(stdout.getvalue())["package_found"], True)

    def test_command_line_refusal_from_a_checkout_writes_nothing(self):
        names = absent_criteria()
        if not names:
            self.skipTest("every criterion's suite module exists")
        with tempfile.TemporaryDirectory() as directory:
            checkout = Path(directory)
            (checkout / "plugins").mkdir()
            os.symlink(PLUGIN, checkout / "plugins/alexandria")
            result = subprocess.run(  # phylax: allow subprocess: fixed local resolver argv, no shell
                [sys.executable, str(ROOT / "design/conformance.py"), names[0]],
                cwd=checkout, capture_output=True, text=True, timeout=120,
                env={**os.environ, "NO_COLOR": "1", "FORCE_COLOR": ""},
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            line = json.loads(result.stdout)
            self.assertIs(line["package_found"], True)
            self.assertEqual(line["criterion"], names[0])
            self.assertEqual(line["reason"], "assertions-unresolved")
            self.assertFalse((checkout / ".hexaemeron").exists())

    def test_criterion_outside_the_fixed_set_refuses_before_loading(self):
        blocked = mock.Mock(side_effect=AssertionError("loaded before the criterion check"))
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", blocked):
                    for criterion in ("../../escape", "registry-pin-change-refuses.json", ""):
                        with self.subTest(criterion=criterion):
                            with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                                with self.assertRaises(SystemExit):
                                    conformance.main([criterion])
            blocked.assert_not_called()
            self.assertFalse((Path(directory) / ".hexaemeron").exists())

    def test_report_follows_complete_successful_execution(self):
        executed = []
        name = "segment-budget-within-ceilings"
        suite = passing_suite(name, executed)
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", return_value=Loader(suite)):
                    with contextlib.redirect_stdout(io.StringIO()):
                        self.assertEqual(conformance.main([name]), 0)
            path = Path(directory) / f".hexaemeron/reports/conformance/{conformance.CANDIDATE}-{name}.json"
            report = json.loads(path.read_text())
            self.assertEqual(len(executed), len(conformance.CASES[name]))
            self.assertIs(report["value"], True)
            self.assertEqual(report["criterion"], name)
            self.assertEqual(report["candidate"], conformance.CANDIDATE)
            self.assertEqual(report["schema"], "protasis-design-report/v1")

    def test_rejected_candidate_refuses_by_name_before_loading_anything(self):
        for candidate in REJECTED_CANDIDATES:
            with self.subTest(candidate=candidate):
                blocked = mock.Mock(side_effect=AssertionError("loaded before the candidate check"))
                with mock.patch.object(conformance.unittest, "TestLoader", blocked):
                    stderr = io.StringIO()
                    with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
                        with self.assertRaises(SystemExit):
                            conformance.main(["registry-pin-change-refuses", "--candidate", candidate])
                    blocked.assert_not_called()
                    self.assertIn(candidate, stderr.getvalue())

    def test_every_resolver_name_refuses_each_rejected_candidate(self):
        # One criterion names regression tests that already pass, so a missing
        # candidate check would run them and write a report into the working
        # directory.  The loader is blocked and the directory is disposable.
        blocked = mock.Mock(side_effect=AssertionError("loaded before the candidate check"))
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)), mock.patch.object(
                conformance.unittest, "TestLoader", blocked
            ):
                for name in conformance.CASES:
                    for candidate in REJECTED_CANDIDATES:
                        with self.subTest(criterion=name, candidate=candidate):
                            stderr = io.StringIO()
                            with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(io.StringIO()):
                                with self.assertRaises(SystemExit):
                                    conformance.main([name, "--candidate", candidate])
                            self.assertIn(candidate, stderr.getvalue())
            blocked.assert_not_called()
            self.assertFalse((Path(directory) / ".hexaemeron").exists())

    def test_rejected_candidate_refusal_cannot_write_a_report(self):
        name = "segment-budget-within-ceilings"
        suite = passing_suite(name, [])
        with tempfile.TemporaryDirectory() as directory:
            with mock.patch.object(conformance.Path, "cwd", return_value=Path(directory)):
                with mock.patch.object(conformance.unittest, "TestLoader", return_value=Loader(suite)):
                    for candidate in REJECTED_CANDIDATES:
                        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
                            with self.assertRaises(SystemExit):
                                conformance.main([name, "--candidate", candidate])
            self.assertFalse((Path(directory) / ".hexaemeron").exists())

    def test_rerun_executes_fresh_and_accepts_only_identical_report(self):
        name = "segment-budget-within-ceilings"
        required = len(conformance.CASES[name])
        executed = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.object(conformance.Path, "cwd", return_value=root), mock.patch.object(
                conformance.unittest, "TestLoader", side_effect=lambda: Loader(passing_suite(name, executed))
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    self.assertEqual(conformance.main([name]), 0)
                    path = root / f".hexaemeron/reports/conformance/{conformance.CANDIDATE}-{name}.json"
                    original = path.read_bytes()
                    # A second, identical rerun is a byte-for-byte no-op success.
                    self.assertEqual(conformance.main([name]), 0)
                    self.assertEqual(path.read_bytes(), original)
                    self.assertEqual(len(executed), 2 * required)
                    # A drifted report of the same length is refused, not overwritten.
                    drifted = original.replace(b'"value": true', b'"value": null')
                    self.assertNotEqual(drifted, original)
                    self.assertEqual(len(drifted), len(original))
                    path.write_bytes(drifted)
                    with self.assertRaises(SystemExit):
                        conformance.main([name])
                    self.assertEqual(len(executed), 3 * required)
                    self.assertEqual(path.read_bytes(), drifted)
                    # A drifted report of another length is refused the same way.
                    shorter = original.replace(b'"value": true', b'"value":false')
                    path.write_bytes(shorter)
                    with self.assertRaises(SystemExit):
                        conformance.main([name])
                    self.assertEqual(path.read_bytes(), shorter)

    def test_symlinked_report_is_refused_and_left_alone(self):
        name = "segment-budget-within-ceilings"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "elsewhere.json"
            target.write_bytes(b"{}\n")
            reports = root / ".hexaemeron/reports/conformance"
            reports.mkdir(parents=True)
            os.symlink(target, reports / f"{conformance.CANDIDATE}-{name}.json")
            with mock.patch.object(conformance.Path, "cwd", return_value=root), mock.patch.object(
                conformance.unittest, "TestLoader", return_value=Loader(passing_suite(name, []))
            ):
                with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit):
                        conformance.main([name])
            self.assertEqual(target.read_bytes(), b"{}\n")


class AaveSelectionEvidenceTests(unittest.TestCase):
    """The committed selection evidence recomputes from its generator."""

    def recompute(self, drop_inputs=()):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        dest = Path(directory.name)
        shutil.copytree(ROOT, dest, dirs_exist_ok=True)
        paths = GENERATED + [str(p.relative_to(ROOT)) for p in (ROOT / "reports/selection").glob("*.json")]
        # The copy carries the committed outputs, so they go before the
        # generator runs.  Left in place they are what the comparison reads,
        # and a generator that wrote nothing would compare equal to itself.
        for relative in paths + list(drop_inputs):
            (dest / relative).unlink()
        spec = importlib.util.spec_from_file_location("aave_v3_model", dest / "design/build_design_evidence.py")
        model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(model)
        with contextlib.redirect_stdout(io.StringIO()):
            model.main()
        return dest, paths

    def test_selection_reports_recompute_byte_identically(self):
        dest, paths = self.recompute()
        self.assertEqual(len(paths), 30)
        for relative in paths:
            with self.subTest(path=relative):
                self.assertTrue((dest / relative).is_file())
                self.assertEqual((ROOT / relative).read_bytes(), (dest / relative).read_bytes())
        produced = sorted(p.name for p in (dest / "reports/selection").glob("*.json"))
        committed = sorted(p.name for p in (ROOT / "reports/selection").glob("*.json"))
        self.assertEqual(produced, committed)
        self.assertEqual(len(committed), 28)
        self.assertFalse((dest / "reports/conformance").exists())
        record = json.loads((dest / "design-evidence.json").read_text())
        self.assertEqual(len(record["results"]), 88)
        self.assertEqual(sum(row["state"] == "pending" for row in record["results"]), 60)
        self.assertEqual(sum(row["state"] == "pass" for row in record["results"]), 24)
        self.assertEqual(sum(row["state"] == "fail" for row in record["results"]), 4)
        self.assertEqual(record["selection"]["candidate"], "segmented-proxy-set-venue")

    def test_generator_reads_the_committed_preflight_sample(self):
        with self.assertRaises(FileNotFoundError):
            self.recompute(drop_inputs=["design/preflight-sample.json"])

    def test_design_record_matches_the_design_lock_and_its_reports(self):
        data = (ROOT / "design-evidence.json").read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(), DESIGN_LOCK_SHA256)
        for row in json.loads(data)["results"]:
            if isinstance(row["report"], dict):
                with self.subTest(report=row["report"]["path"]):
                    body = (ROOT / row["report"]["path"]).read_bytes()
                    self.assertEqual(hashlib.sha256(body).hexdigest(), row["report"]["sha256"])

    def test_chain_read_records_carry_no_endpoint_or_credential(self):
        for relative in CHAIN_READS:
            with self.subTest(record=relative):
                text = (ROOT / relative).read_text()
                self.assertIsNone(LEAK.search(text), relative)
                for value in strings(json.loads(text)):
                    self.assertIsNone(LEAK.search(value), value)

    def test_leak_pattern_catches_each_class_it_names(self):
        for specimen in (
            "https://rpc.example/v1", "localhost", "127.0.0.1", "[::1]", "node:8545",
            "eth.provider.io", "Authorization", "Bearer abc", "x-api-key", "header",
        ):
            with self.subTest(specimen=specimen):
                self.assertIsNotNone(LEAK.search(specimen))
        self.assertIsNone(LEAK.search("reth/v1.11.0-564ffa5/aarch64-apple-darwin over loopback"))


if __name__ == "__main__":
    unittest.main()
