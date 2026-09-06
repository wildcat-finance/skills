"""The CLI, exercised the way an operator would run it."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from . import support

from probitas_lib import registry  # noqa: E402
from probitas_lib.evidence import EVIDENCE_SCHEMA  # noqa: E402

PROBITAS = os.path.join(support.SCRIPTS, "probitas.py")
FIXTURES = os.path.join(support.PLUGIN_ROOT, "tests", "fixtures")


def run(*args):
    return subprocess.run(
        [sys.executable, PROBITAS, *args],
        capture_output=True,
        text=True,
        check=False,
    )


class TestVenuesCommand(unittest.TestCase):
    def test_it_lists_every_venue(self):
        result = run("venues", "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        venues = json.loads(result.stdout)
        self.assertEqual(len(venues), len(registry.all_venues()))
        self.assertIn("wildcat", [v["id"] for v in venues])

    def test_the_plain_listing_says_which_are_implemented(self):
        result = run("venues")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("not implemented", result.stdout)


class TestTheRouteTable(unittest.TestCase):
    """Every row of the documented table, without reaching the network.

    Route selection is a pure function, so the whole table is provable here.
    Only the offline rows can then be run end to end: a test that quietly made
    a live request would pass on a laptop and tell you nothing either way.
    """

    def routes(self, **flags):
        import argparse

        import probitas

        namespace = argparse.Namespace(fixtures=None, live=False, alexandria_index=None)
        for key, value in flags.items():
            setattr(namespace, key, value)
        return probitas.routes_for(namespace)

    def test_no_flags_run_the_live_adapter_route_alone(self):
        self.assertEqual(self.routes(), ("live",))

    def test_fixtures_back_the_adapter_route_alone(self):
        self.assertEqual(self.routes(fixtures="/dir"), ("fixtures",))

    def test_live_alone_names_the_existing_default(self):
        self.assertEqual(self.routes(live=True), ("live",))

    def test_an_index_alone_runs_no_adapter(self):
        """The property every existing archive invocation depends on."""
        self.assertEqual(self.routes(alexandria_index="x.sqlite"), ("archive",))

    def test_fixtures_and_an_index_run_both_routes_offline(self):
        self.assertEqual(
            self.routes(fixtures="/dir", alexandria_index="x.sqlite"),
            ("fixtures", "archive"),
        )

    def test_live_and_an_index_run_both_routes(self):
        self.assertEqual(
            self.routes(live=True, alexandria_index="x.sqlite"), ("live", "archive")
        )

    def test_live_and_fixtures_are_refused_with_exit_two(self):
        result = run(
            "collect", "--entity", "Acme", "--address", "0x" + "a1" * 20,
            "--live", "--fixtures", os.path.join(FIXTURES, "empty"), "--out", "-",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not allowed with", result.stderr)
        self.assertIn("--live", result.stderr)


class TestTheGapRule(unittest.TestCase):
    """A venue one route answered for is not a hole because another missed it."""

    def evidence(self):
        import probitas
        from probitas_lib.evidence import Coverage, Evidence

        subject = Evidence(
            entity="Acme", addresses=[("0x" + "a1" * 20, "declared")], run_id="test"
        )
        return probitas, Coverage, subject

    def test_a_venue_one_route_answered_is_not_also_a_gap(self):
        probitas, Coverage, subject = self.evidence()
        subject.add_coverage(
            Coverage("wildcat", "checked", source="fixtures", block_range="1-2")
        )
        subject.add_coverage(
            Coverage("wildcat", "unconfigured", source="none", note="nobody looked")
        )
        probitas._record_gaps(subject)
        self.assertEqual([gap.subject for gap in subject.gaps], [])

    def test_a_failed_route_still_leaves_a_gap(self):
        probitas, Coverage, subject = self.evidence()
        subject.add_coverage(
            Coverage("wildcat", "checked", source="fixtures", block_range="1-2")
        )
        subject.add_coverage(Coverage("wildcat", "error", source="archive", note="502"))
        probitas._record_gaps(subject)
        self.assertEqual(
            [gap.subject for gap in subject.gaps], ["wildcat borrowing history"]
        )

    def test_a_venue_nobody_reached_is_named_once(self):
        probitas, Coverage, subject = self.evidence()
        subject.add_coverage(
            Coverage("maple", "unimplemented", source="none", note="no adapter")
        )
        probitas._record_gaps(subject)
        self.assertEqual(
            [gap.subject for gap in subject.gaps], ["maple borrowing history"]
        )


class TestCollectCommand(unittest.TestCase):
    address = "0x" + "a1" * 20

    def collect(self, *extra, case="empty"):
        """Always against a fixture.

        The suite must never reach the network. A test that quietly makes a
        live request passes on a laptop, fails in CI behind a proxy, and tells
        you nothing either way.
        """
        result = run(
            "collect",
            "--entity",
            "Acme Trading Ltd",
            "--address",
            self.address,
            "--fixtures",
            os.path.join(FIXTURES, case),
            "--out",
            "-",
            *extra,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_the_evidence_file_has_the_five_top_level_blocks(self):
        payload = self.collect()
        for key in ("run", "subject", "records", "coverage", "gaps"):
            self.assertIn(key, payload)

    def test_every_registry_venue_appears_in_coverage(self):
        payload = self.collect()
        self.assertEqual(len(payload["coverage"]), len(registry.all_venues()))

    def test_an_unchecked_venue_becomes_a_named_gap(self):
        payload = self.collect()
        subjects = [gap["subject"] for gap in payload["gaps"]]
        self.assertIn("maple borrowing history", subjects)
        # Venues with no adapter remain named gaps. A venue that was checked
        # and came back empty is a finding rather than a hole.
        self.assertNotIn("wildcat borrowing history", subjects)
        self.assertNotIn("morpho-blue borrowing history", subjects)
        self.assertNotIn("euler borrowing history", subjects)
        self.assertEqual(len(payload["gaps"]), len(registry.unimplemented()))

    def test_midnight_empty_is_checked_without_a_gap_and_keeps_the_schema(self):
        payload = self.collect()
        coverage = next(
            row for row in payload["coverage"] if row["venue"] == "morpho-midnight"
        )
        self.assertEqual(payload["schema"], EVIDENCE_SCHEMA)
        self.assertEqual(coverage["status"], "empty")
        self.assertIn("cursor walk(s) exhausted", coverage["note"])
        self.assertNotIn(
            "morpho-midnight borrowing history",
            {gap["subject"] for gap in payload["gaps"]},
        )

    def test_midnight_refusal_becomes_error_coverage_and_a_named_gap(self):
        with tempfile.TemporaryDirectory() as directory:
            source = os.path.join(FIXTURES, "empty")
            for name in os.listdir(source):
                if name != "morpho-midnight.json":
                    shutil.copyfile(
                        os.path.join(source, name), os.path.join(directory, name)
                    )
            payload = self.collect(case=directory)

        coverage = next(
            row for row in payload["coverage"] if row["venue"] == "morpho-midnight"
        )
        gap = next(
            gap
            for gap in payload["gaps"]
            if gap["subject"] == "morpho-midnight borrowing history"
        )
        self.assertEqual(coverage["status"], "error")
        self.assertEqual(gap["reason"], coverage["note"])
        self.assertIn("no records emitted", coverage["note"])
        self.assertNotIn(directory, coverage["note"])

    def test_every_coverage_row_names_its_source(self):
        payload = self.collect()
        sources = {row["source"] for row in payload["coverage"]}
        self.assertEqual(sources, {"fixtures", "none"})
        self.assertEqual(payload["schema"], 2)

    def test_a_fixture_run_never_reports_itself_as_live(self):
        """The route stamps this, so a fixture run cannot read as a live one."""
        payload = self.collect()
        queried = [r for r in payload["coverage"] if r["status"] in ("checked", "empty")]
        self.assertTrue(queried)
        self.assertTrue(all(row["source"] == "fixtures" for row in queried))

    def test_inferred_addresses_stay_in_their_own_tier(self):
        payload = self.collect("--inferred", "0x" + "b2" * 20)
        tiers = {a["address"]: a["provenance"] for a in payload["subject"]["addresses"]}
        self.assertEqual(tiers[self.address], "declared")
        self.assertEqual(tiers["0x" + "b2" * 20], "inferred")

    def test_a_bad_address_is_refused_with_exit_two(self):
        result = run(
            "collect",
            "--entity",
            "Acme",
            "--address",
            "not-an-address",
            "--fixtures",
            os.path.join(FIXTURES, "empty"),
            "--out",
            "-",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a 20-byte hex address", result.stderr)

    def test_writing_to_a_file_reports_what_it_wrote(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "evidence.json")
            result = run(
                "collect",
                "--entity",
                "Acme",
                "--address",
                self.address,
                "--fixtures",
                os.path.join(FIXTURES, "empty"),
                "--out",
                path,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(
                f"{len(registry.implemented())} of "
                f"{len(registry.all_venues())} venue(s) checked",
                result.stderr,
            )
            # Counted over venues, not rows: a union run holds more rows than
            # venues and the line would otherwise understate its own coverage.
            self.assertIn(
                f"over {len(registry.all_venues())} row(s)", result.stderr
            )
            self.assertIn("routes: fixtures (", result.stderr)
            with open(path, encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["schema"], 2)

    def test_two_runs_produce_identical_bytes(self):
        arguments = (
            "collect",
            "--entity",
            "Acme",
            "--address",
            self.address,
            "--fixtures",
            os.path.join(FIXTURES, "defaulted"),
            "--out",
            "-",
            "--run-id",
            "fixed",
        )
        self.assertEqual(run(*arguments).stdout, run(*arguments).stdout)

    def test_every_aggregate_fixture_has_deterministic_midnight_bytes(self):
        for case in (
            "clean",
            "cured",
            "defaulted",
            "demo",
            "empty",
            "euler-borrower",
            "euler-empty",
            "morpho-bad-debt",
            "morpho-clean",
            "morpho-empty",
            "morpho-liquidated",
        ):
            with self.subTest(case=case):
                first = self.collect(case=case)
                second = self.collect(case=case)
                self.assertEqual(first, second)
                coverage = next(
                    row
                    for row in first["coverage"]
                    if row["venue"] == "morpho-midnight"
                )
                expected = "checked" if case == "demo" else "empty"
                self.assertEqual(coverage["status"], expected)


class TestTheWholeSequence(unittest.TestCase):
    """collect, render, verify, the way an operator runs it."""

    address = "0x" + "a1" * 20

    def pipeline(self, case="defaulted"):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        evidence = os.path.join(directory.name, "evidence.json")
        dossier = os.path.join(directory.name, "dossier.md")

        collected = run(
            "collect",
            "--entity",
            "Acme Trading Ltd",
            "--address",
            self.address,
            "--fixtures",
            os.path.join(FIXTURES, case),
            "--run-id",
            "demo",
            "--out",
            evidence,
        )
        self.assertEqual(collected.returncode, 0, collected.stderr)

        rendered = run("render", evidence, "--out", dossier)
        self.assertEqual(rendered.returncode, 0, rendered.stderr)

        return evidence, dossier, run("verify", dossier, evidence)

    def test_the_demo_path_ends_with_every_gate_passing(self):
        _, _, verified = self.pipeline()
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertEqual(len(verified.stdout.strip().splitlines()), 5)
        self.assertNotIn("FAIL", verified.stdout)

    def test_a_breached_gate_exits_one_and_says_which(self):
        _, dossier, _ = self.pipeline()
        with open(dossier, encoding="utf-8") as handle:
            document = handle.read()
        with open(dossier, "w", encoding="utf-8") as handle:
            handle.write(document.replace("## What could not be established", "## Notes"))
        evidence = os.path.join(os.path.dirname(dossier), "evidence.json")
        result = run("verify", dossier, evidence)
        self.assertEqual(result.returncode, 1)
        self.assertIn("gate 4", result.stdout)
        self.assertIn("does not ship", result.stderr)

    def test_rendering_twice_gives_identical_bytes(self):
        evidence, _, _ = self.pipeline()
        self.assertEqual(
            run("render", evidence, "--out", "-").stdout,
            run("render", evidence, "--out", "-").stdout,
        )

    def test_rendering_a_schema_one_file_exits_two_and_says_to_collect_again(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = os.path.join(directory.name, "old-evidence.json")
        source, _, _ = self.pipeline()
        with open(source, encoding="utf-8") as handle:
            payload = json.load(handle)
        payload["schema"] = 1
        for row in payload["coverage"]:
            row.pop("source", None)
            row.pop("releases", None)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        result = run("render", path, "--out", "-")
        self.assertEqual(result.returncode, 2)
        self.assertIn("schema 1", result.stderr)
        self.assertIn("collect again", result.stderr)

    def test_rendering_something_that_is_not_evidence_exits_two(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = os.path.join(directory.name, "not-evidence.json")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('{"hello": "world"}')
        result = run("render", path, "--out", "-")
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a probitas evidence file", result.stderr)

    def test_evidence_the_renderer_refuses_exits_two(self):
        # The load-time twin above guards the same contract. Rendering refuses
        # later than loading does, so the caller has to hold both to the
        # bounded diagnostic rather than letting one become a traceback.
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        path = os.path.join(directory.name, "empty-entity.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(
                {
                    "schema": EVIDENCE_SCHEMA,
                    "subject": {
                        "entity": "",
                        "addresses": [
                            {
                                "address": "0x" + "11" * 20,
                                "provenance": "declared",
                            }
                        ],
                    },
                    "records": [],
                    "coverage": [],
                    "gaps": [],
                },
                handle,
            )
        result = run("render", path, "--out", "-")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("subject entity is empty", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_the_dossier_puts_the_gaps_before_the_summary(self):
        _, dossier, _ = self.pipeline()
        with open(dossier, encoding="utf-8") as handle:
            document = handle.read()
        self.assertLess(
            document.index("## What could not be established"),
            document.index("## Summary"),
        )


class TestDiffCommand(unittest.TestCase):
    """Two verified fixture runs become one offline change artifact."""

    address = "0x" + "a1" * 20

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.prior = self._collect("empty", "prior")
        self.current = self._collect("defaulted", "current")

    def _collect(self, case, run_id):
        path = os.path.join(self.directory.name, f"{run_id}.json")
        result = run(
            "collect",
            "--entity",
            "Acme Trading Ltd",
            "--address",
            self.address,
            "--fixtures",
            os.path.join(FIXTURES, case),
            "--run-id",
            run_id,
            "--out",
            path,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return path

    def test_markdown_and_json_reports_run_end_to_end(self):
        report = os.path.join(self.directory.name, "borrower-change-report.md")
        result = run("diff", self.prior, self.current, "--out", report)
        self.assertEqual(result.returncode, 0, result.stderr)
        with open(report, encoding="utf-8") as handle:
            markdown = handle.read()
        self.assertIn("# Borrower change report: Acme Trading Ltd", markdown)
        self.assertIn("## Coverage changes", markdown)
        self.assertIn("## Record differences", markdown)
        self.assertIn("roles chosen by the operator", markdown)

        result = run("diff", self.prior, self.current, "--json", "--out", "-")
        self.assertEqual(result.returncode, 0, result.stderr)
        comparison = json.loads(result.stdout)
        self.assertEqual(comparison["schema"], "probitas-evidence-delta/v1")
        self.assertEqual(comparison["inputs"]["prior"]["run"]["id"], "prior")
        self.assertEqual(comparison["inputs"]["current"]["run"]["id"], "current")

    def test_a_gate_breach_exits_one_without_partial_output(self):
        with open(self.current, encoding="utf-8") as handle:
            payload = json.load(handle)
        payload["coverage"] = [
            row for row in payload["coverage"] if row["venue"] != "maple"
        ]
        with open(self.current, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

        report = os.path.join(self.directory.name, "must-not-exist.md")
        result = run("diff", self.prior, self.current, "--out", report)

        self.assertEqual(result.returncode, 1)
        self.assertIn("current evidence failed its generated dossier", result.stderr)
        self.assertFalse(os.path.exists(report))

    def test_repairing_the_input_and_rerunning_replaces_the_old_report(self):
        with open(self.current, "rb") as handle:
            valid_current = handle.read()
        payload = json.loads(valid_current)
        payload["coverage"] = [
            row for row in payload["coverage"] if row["venue"] != "maple"
        ]
        with open(self.current, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        report = os.path.join(self.directory.name, "borrower-change-report.md")
        old_report = b"previous report stays until a complete replacement\n"
        with open(report, "wb") as handle:
            handle.write(old_report)

        failed = run("diff", self.prior, self.current, "--out", report)
        self.assertEqual(failed.returncode, 1)
        with open(report, "rb") as handle:
            self.assertEqual(handle.read(), old_report)

        with open(self.current, "wb") as handle:
            handle.write(valid_current)
        recovered = run("diff", self.prior, self.current, "--out", report)
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        with open(report, "rb") as handle:
            self.assertNotEqual(handle.read(), old_report)

    def test_a_broken_success_notice_does_not_turn_a_committed_report_into_failure(self):
        report = os.path.join(self.directory.name, "borrower-change-report.md")
        old_report = b"old report\n"
        with open(report, "wb") as handle:
            handle.write(old_report)

        read_descriptor, write_descriptor = os.pipe()
        process = None
        try:
            process = subprocess.Popen(
                [
                    sys.executable,
                    PROBITAS,
                    "diff",
                    self.prior,
                    self.current,
                    "--out",
                    report,
                ],
                stdout=subprocess.DEVNULL,
                stderr=write_descriptor,
            )
            os.close(write_descriptor)
            write_descriptor = None
            os.close(read_descriptor)
            read_descriptor = None
            returncode = process.wait(timeout=10)
        finally:
            if write_descriptor is not None:
                os.close(write_descriptor)
            if read_descriptor is not None:
                os.close(read_descriptor)
            if process is not None and process.poll() is None:
                process.kill()
                process.wait()

        self.assertEqual(returncode, 0)
        with open(report, "rb") as handle:
            self.assertNotEqual(handle.read(), old_report)

    def test_an_input_cannot_be_replaced_directly_or_through_a_symlink(self):
        with open(self.prior, "rb") as handle:
            before = handle.read()
        alias = os.path.join(self.directory.name, "prior-alias.json")
        os.symlink(self.prior, alias)

        for output in (self.prior, alias):
            with self.subTest(output=output):
                result = run("diff", self.prior, self.current, "--out", output)
                self.assertEqual(result.returncode, 2)
                self.assertIn("must not replace either evidence input", result.stderr)
                with open(self.prior, "rb") as handle:
                    self.assertEqual(handle.read(), before)

    def test_a_fifo_input_is_refused_without_waiting_for_a_writer(self):
        fifo = os.path.join(self.directory.name, "blocking-input")
        os.mkfifo(fifo)

        result = subprocess.run(
            [sys.executable, PROBITAS, "diff", fifo, self.current, "--out", "-"],
            capture_output=True,
            text=True,
            check=False,
            timeout=2,
        )

        self.assertEqual(result.returncode, 2)
        self.assertIn("not a regular file", result.stderr)

    def test_a_non_text_venue_exits_two_without_a_traceback(self):
        with open(self.prior, encoding="utf-8") as handle:
            malformed = json.load(handle)
        malformed["coverage"][0]["venue"] = ["wildcat"]
        with open(self.prior, "w", encoding="utf-8") as handle:
            json.dump(malformed, handle)

        result = run("diff", self.prior, self.current, "--out", "-")

        self.assertEqual(result.returncode, 2)
        self.assertIn("venue must be text", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_diff_accepts_a_gate_checkable_many_address_collector_output(self):
        evidence = os.path.join(self.directory.name, "many-addresses.json")
        arguments = [
            "collect",
            "--entity",
            "Acme Trading Ltd",
            "--fixtures",
            os.path.join(FIXTURES, "empty"),
            "--run-id",
            "many-addresses",
            "--out",
            evidence,
        ]
        for index in range(1, 258):
            arguments.extend(("--address", f"0x{index:040x}"))

        collected = run(*arguments)
        self.assertEqual(collected.returncode, 0, collected.stderr)

        compared = run("diff", evidence, evidence, "--json", "--out", "-")
        self.assertEqual(compared.returncode, 0, compared.stderr)


if __name__ == "__main__":
    unittest.main()
