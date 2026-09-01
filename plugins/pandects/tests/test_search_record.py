"""The search record: its shape, its digest, and what it leaves out.

A campaign result is only worth something if it says how the search was made.
These tests are about the three ways that goes wrong: a record that claims an
engine nobody ran, a record ariadne would refuse, and a digest that does not
track the thing it claims to digest.
"""

import json
import os
import shutil
import tempfile
import unittest

from . import support  # noqa: F401  (sets sys.path)

from pandects_lib import catalogue as catalogue_module  # noqa: E402
from pandects_lib import run as run_module  # noqa: E402

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHIPPED = os.path.join(PLUGIN_ROOT, "catalogue", "pandects.json")

#: Ariadne's determinism gate, restated as the two things it enforces. Kept
#: here rather than imported: the plugins share no code, and a copy that drifts
#: is a failing test, which is the point of pinning it.
ARIADNE_COMMAND_FIELDS = {"name", "argv", "determinism", "output_digest", "detail"}
ARIADNE_DETERMINISM = ("exact", "nondeterministic")


class ShippedRecordTests(unittest.TestCase):
    """The record committed at the plugin root, against the catalogue now.

    A search record is evidence, and a stale one is worse than an absent one: it
    states a law count and a corpus digest with the authority of something a
    script produced, and nothing about reading it says when. The record shipped
    with nine laws in it for as long as there were nine, and there was no check
    that would notice a tenth.
    """

    SHIPPED_RECORD = os.path.join(PLUGIN_ROOT, "search-record.json")

    def setUp(self):
        with open(self.SHIPPED_RECORD, encoding="utf-8") as handle:
            self.record = json.load(handle)
        self.catalogue = catalogue_module.parse(
            json.load(open(SHIPPED, encoding="utf-8"))
        )

    def test_the_shipped_record_counts_the_laws_the_catalogue_holds(self):
        self.assertEqual(
            self.record["corpus"]["laws"],
            len(self.catalogue.laws),
            "regenerate with: python3 scripts/pandects.py run --out search-record.json",
        )

    def test_the_shipped_record_digests_the_corpus_as_it_is(self):
        """The digest is the part a reader cannot check by eye."""
        self.assertEqual(
            self.record["corpus"]["digest"],
            run_module.corpus_digest(PLUGIN_ROOT, self.catalogue),
            "regenerate with: python3 scripts/pandects.py run --out search-record.json",
        )

    def test_the_shipped_record_names_its_corpus_version(self):
        self.assertEqual(
            self.record["corpus"]["version"], self.catalogue.raw["version"]
        )

    def test_the_shipped_record_exercises_every_catalogue_law(self):
        exercised = self.record["commands"][0]["detail"]["laws_exercised"]
        self.assertEqual(
            set(exercised),
            {law.id for law in self.catalogue.laws},
            "regenerate with: python3 scripts/pandects.py run --out search-record.json",
        )


class CommandShapeTests(unittest.TestCase):
    def test_a_command_carries_only_the_fields_ariadne_allows(self):
        entry = run_module.command(
            "fuzz campaign: example", ["forge", "test"], "nondeterministic", {"engine": "foundry"}
        )
        self.assertEqual(set(entry) - ARIADNE_COMMAND_FIELDS, set())
        self.assertIn(entry["determinism"], ARIADNE_DETERMINISM)

    def test_an_empty_argv_is_refused(self):
        """Ariadne's wording: nobody else could run it."""
        with self.assertRaises(run_module.RunError) as caught:
            run_module.command("c", [], "nondeterministic", {})
        self.assertIn("argv", str(caught.exception))

    def test_an_argv_entry_that_is_not_a_string_is_refused(self):
        with self.assertRaises(run_module.RunError):
            run_module.command("c", ["forge", 7], "nondeterministic", {})

    def test_a_determinism_class_outside_the_two_is_refused(self):
        with self.assertRaises(run_module.RunError) as caught:
            run_module.command("c", ["forge"], "mostly", {})
        self.assertIn("mostly", str(caught.exception))

    def test_an_exact_command_without_an_output_digest_is_refused(self):
        """The gate's reason, enforced at the point of writing.

        An exact command promises a replay can be compared byte for byte. With
        no digest there is nothing to compare against, so the promise is empty
        and the record should never have been written.
        """
        with self.assertRaises(run_module.RunError) as caught:
            run_module.command("c", ["forge"], "exact", {})
        self.assertIn("nothing to compare", str(caught.exception))

    def test_an_exact_command_with_a_digest_is_accepted(self):
        entry = run_module.command(
            "c", ["forge"], "exact", {}, output_digest={"sha256": "ab" * 32}
        )
        self.assertEqual(entry["output_digest"], {"sha256": "ab" * 32})


class AbsentEngineTests(unittest.TestCase):
    """An engine that did not run is absent, not present and empty."""

    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)

    def test_a_missing_engine_produces_no_command_at_all(self):
        """Driven rather than asserted in prose.

        `run_foundry` returns None when the engine is not on the path, and the
        record is built from what came back. Pointing it at a directory with no
        `forge` reachable is the same path a machine without Foundry takes.
        """
        original = run_module.run_foundry
        run_module.run_foundry = lambda root, match=None, timeout=1800: None
        try:
            record = run_module.search_record(PLUGIN_ROOT, self.catalogue)
        finally:
            run_module.run_foundry = original
        self.assertEqual(record["commands"], [])

    def test_a_record_with_no_engine_still_names_the_corpus(self):
        """Absence of a search is not absence of a subject.

        The record says which corpus nothing was run against, which is what
        makes an empty `commands` list readable as "nobody searched" rather than
        as a file somebody truncated.
        """
        original = run_module.run_foundry
        run_module.run_foundry = lambda root, match=None, timeout=1800: None
        try:
            record = run_module.search_record(PLUGIN_ROOT, self.catalogue)
        finally:
            run_module.run_foundry = original
        self.assertEqual(record["corpus"]["laws"], len(self.catalogue.laws))
        self.assertIn("sha256", record["corpus"]["digest"])

    def test_a_seed_nobody_can_read_is_absent_rather_than_null(self):
        """Foundry reports no seed, so the record says nothing about one.

        A `"seed": null` would be a claim that the run had no seed. What is true
        is that nobody can read the one it used, and those are different.
        """
        result = {"argv": ["forge", "test"], "returncode": 0, "output": ""}
        entry = run_module.foundry_record(PLUGIN_ROOT, self.catalogue, result)
        self.assertNotIn("seed", entry["detail"])

    def test_an_engine_version_nobody_could_read_is_absent_too(self):
        """The same rule as the seed, applied in the same record.

        A field that is null in one place and absent in another for the same
        reason is a record that has to be read twice. Both mean "nobody could
        read this", so both are absent.
        """
        original = run_module.engine_version
        run_module.engine_version = lambda argv, timeout=60: None
        try:
            result = {"argv": ["forge", "test"], "returncode": 0, "output": ""}
            entry = run_module.foundry_record(PLUGIN_ROOT, self.catalogue, result)
        finally:
            run_module.engine_version = original
        self.assertNotIn("engine_version", entry["detail"])
        self.assertNotIn("seed", entry["detail"])

    def test_no_field_in_a_record_is_ever_null(self):
        """The rule, stated once over the whole record rather than per field."""
        record = run_module.search_record(PLUGIN_ROOT, self.catalogue, match="LawTest")

        def walk(value, path="record"):
            if value is None:
                self.fail("%s is null; absent is how this record says unknown" % path)
            if isinstance(value, dict):
                for key, child in value.items():
                    walk(child, "%s.%s" % (path, key))
            elif isinstance(value, list):
                for i, child in enumerate(value):
                    walk(child, "%s[%d]" % (path, i))

        walk(record)

    def test_a_seed_that_was_given_is_recorded(self):
        result = {"argv": ["echidna", "."], "returncode": 0, "output": ""}
        entry = run_module.foundry_record(
            PLUGIN_ROOT, self.catalogue, result, seed="20260816"
        )
        self.assertEqual(entry["detail"]["seed"], "20260816")


class TimeoutTests(unittest.TestCase):
    """A campaign that was killed is not a campaign that never happened."""

    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)

    def test_a_timed_out_campaign_is_recorded_rather_than_dropped(self):
        result = {
            "argv": ["forge", "test"],
            "returncode": None,
            "timed_out_after": 1800,
            "output": "",
        }
        detail = run_module.foundry_record(PLUGIN_ROOT, self.catalogue, result)["detail"]
        self.assertEqual(detail["outcome"], "timed out")
        self.assertEqual(detail["timed_out_after_seconds"], 1800)

    def test_a_timeout_is_neither_passed_nor_failed(self):
        """Folding it into either verdict loses what a reader needs.

        Called passed, it claims a search that finished. Called failed, it
        claims a law was violated. Neither happened.
        """
        killed = run_module.outcome_of({"returncode": None})
        self.assertNotIn(killed, ("passed", "failed"))
        self.assertEqual(run_module.outcome_of({"returncode": 0}), "passed")
        self.assertEqual(run_module.outcome_of({"returncode": 1}), "failed")


class SettingsTests(unittest.TestCase):
    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)

    def test_the_record_names_every_field_the_gate_asks_for(self):
        result = {"argv": ["forge", "test"], "returncode": 0, "output": ""}
        detail = run_module.foundry_record(PLUGIN_ROOT, self.catalogue, result)["detail"]
        for field in ("engine", "configuration", "sequence_length", "corpus_digest"):
            self.assertIn(field, detail)

    def test_the_configuration_is_read_from_foundry_toml_rather_than_restated(self):
        """A record cannot describe a configuration nobody used."""
        settings = run_module.foundry_settings(PLUGIN_ROOT)
        self.assertEqual(settings.get("fail_on_revert"), "false")
        self.assertIn("depth", settings)

    def test_a_configuration_nobody_could_read_is_refused(self):
        """Rather than reported as an empty one.

        `"configuration": {}` reads as a campaign that ran under no settings.
        What happened is that the settings could not be found, and a record
        whose whole purpose is describing the search must not quietly describe
        a different one.
        """
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        with open(os.path.join(root, "foundry.toml"), "w") as handle:
            handle.write("[profile.default]\nsrc = \"src\"\n")
        with self.assertRaises(run_module.RunError) as caught:
            run_module.foundry_settings(root)
        self.assertIn("empty configuration", str(caught.exception))

    def test_the_profile_scoped_section_is_read_too(self):
        """Both headings are in use, and one reader would miss half of them."""
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        with open(os.path.join(root, "foundry.toml"), "w") as handle:
            handle.write("[profile.default.invariant]\nruns = 128\ndepth = 32\n")
        self.assertEqual(run_module.foundry_settings(root)["runs"], "128")

    def test_a_failing_campaign_is_recorded_as_failed(self):
        result = {"argv": ["forge", "test"], "returncode": 1, "output": ""}
        entry = run_module.foundry_record(PLUGIN_ROOT, self.catalogue, result)
        self.assertEqual(entry["detail"]["outcome"], "failed")


class PerLawExerciseTests(unittest.TestCase):
    CONSERVED = "conservation/value-conserved/v1"
    BACKED = "conservation/reserves-backed-by-claims/v1"
    FALLS = "accrual/debt-falls-only-against-payment/v1"
    AT_REST = "accrual/no-accrual-at-rest/v1"
    PATH = "accrual/path-independent/v1"
    SHRINKS = "claims/recorded-claim-never-shrinks/v1"

    def setUp(self):
        self.catalogue = catalogue_module.load(SHIPPED)
        self.original_version = run_module.engine_version
        run_module.engine_version = lambda argv, timeout=60: None
        self.addCleanup(self.restore_version)

    def restore_version(self):
        run_module.engine_version = self.original_version

    def detail(self, output, returncode=0, argv=None):
        result = {
            "argv": argv or ["forge", "test", "-vv"],
            "returncode": returncode,
            "output": output,
        }
        return run_module.foundry_record(PLUGIN_ROOT, self.catalogue, result)["detail"]

    def test_a_passed_invariant_attributes_one_law_and_its_run_count(self):
        detail = self.detail(
            "Ran 1 test for test/SoundInvariant.t.sol:SoundInvariantTest\n"
            "[PASS] invariant_value_is_conserved() "
            "(runs: 64, calls: 4096, reverts: 0)\n"
        )
        exercised = detail["laws_exercised"]
        self.assertEqual(set(exercised), {self.CONSERVED})
        self.assertEqual(exercised[self.CONSERVED]["evaluations"], 64)
        self.assertEqual(exercised[self.CONSERVED]["surfaces"][0]["outcome"], "passed")

    def test_a_passed_multi_law_surface_attributes_every_mapped_law(self):
        detail = self.detail(
            "Ran 1 test for test/Corpus.t.sol:CorpusTest\n"
            "[PASS] test_minted_claims_breaks_conservation_alone() (gas: 123)\n"
        )
        self.assertEqual(len(detail["laws_exercised"]), 6)

    def test_a_failed_multi_law_surface_attributes_no_law_from_it(self):
        detail = self.detail(
            "Ran 1 test for test/Corpus.t.sol:CorpusTest\n"
            "[FAIL: diagonal broke] test_minted_claims_breaks_conservation_alone() "
            "(gas: 123)\n",
            returncode=1,
        )
        self.assertEqual(detail["laws_exercised"], {})
        self.assertIn(
            "no per-law verdict",
            detail["laws_not_exercised"][self.CONSERVED],
        )

    def test_a_failed_single_law_surface_still_attributes_that_law(self):
        detail = self.detail(
            "Ran 1 test for test/SoundInvariant.t.sol:SoundInvariantTest\n"
            "[FAIL: violated] invariant_value_is_conserved() "
            "(runs: 3, calls: 12, reverts: 0)\n",
            returncode=1,
        )
        self.assertEqual(set(detail["laws_exercised"]), {self.CONSERVED})
        surface = detail["laws_exercised"][self.CONSERVED]["surfaces"][0]
        self.assertEqual(surface["outcome"], "failed")
        self.assertNotIn("evaluations", detail["laws_exercised"][self.CONSERVED])

    def test_forge_1_8_aggregate_runs_apply_to_each_passing_invariant(self):
        detail = self.detail(
            "Ran 1 test for test/SoundInvariant.t.sol:SoundInvariantTest\n"
            "[PASS]\n"
            "SoundInvariantTest invariants:\n"
            "[PASS] invariant_reserves_are_backed_by_claims\n"
            "[PASS] invariant_value_is_conserved\n"
            " SoundInvariantTest invariants (runs: 64, calls: 4096, reverts: 0)\n"
        )
        self.assertEqual(
            detail["laws_exercised"][self.CONSERVED]["evaluations"], 64
        )
        self.assertEqual(detail["laws_exercised"][self.BACKED]["evaluations"], 64)

    def test_forge_1_8_aggregate_runs_exclude_a_non_pass_invariant(self):
        detail = self.detail(
            "Ran 1 test for test/SoundInvariant.t.sol:SoundInvariantTest\n"
            "[FAIL: expected failure] invariant_value_is_conserved\n"
            "SoundInvariantTest invariants: 1/2 invariants broken\n"
            "[FAIL: expected failure] invariant_value_is_conserved\n"
            "[PASS] invariant_reserves_are_backed_by_claims\n"
            " SoundInvariantTest invariants (runs: 3, calls: 6, reverts: 0)\n",
            returncode=1,
        )
        self.assertEqual(
            detail["laws_exercised"][self.BACKED]["evaluations"], 3
        )
        self.assertNotIn("evaluations", detail["laws_exercised"][self.CONSERVED])
        self.assertEqual(
            detail["laws_exercised"][self.CONSERVED]["surfaces"][0]["outcome"],
            "failed",
        )

    def test_recorded_calls_attach_only_to_succession_laws(self):
        detail = self.detail(
            "Ran 1 test for test/Wildcat.t.sol:WildcatTest\n"
            "[PASS] test_the_model_runs_through_the_shipped_adapter() (gas: 123)\n"
            "Logs:\n"
            "  recordedCalls: 5\n"
        )
        for identifier in (self.FALLS, self.AT_REST, self.SHRINKS):
            self.assertEqual(
                detail["laws_exercised"][identifier]["recorded_calls"], 5
            )
        self.assertNotIn(
            "recorded_calls", detail["laws_exercised"][self.CONSERVED]
        )

    def test_zero_and_unreadable_counts_are_absent_not_substituted(self):
        detail = self.detail(
            "Ran 1 test for test/SoundInvariant.t.sol:SoundInvariantTest\n"
            "[PASS] invariant_value_is_conserved() "
            "(runs: 0, calls: 0, reverts: 0)\n"
            "recordedCalls: not-a-number\n"
        )
        self.assertNotIn(
            "evaluations", detail["laws_exercised"][self.CONSERVED]
        )
        self.assertNotIn(
            "recorded_calls", detail["laws_exercised"][self.CONSERVED]
        )

    def test_truncated_or_garbage_output_yields_absence_not_a_guess(self):
        detail = self.detail("Compiling...\n[PASS maybe\n")
        self.assertEqual(detail["laws_exercised"], {})
        self.assertEqual(
            set(detail["laws_not_exercised"]),
            {law.id for law in self.catalogue.laws},
        )

    def test_a_timeout_keeps_per_law_evidence_captured_before_the_kill(self):
        result = {
            "argv": ["forge", "test", "-vv"],
            "returncode": None,
            "timed_out_after": 1800,
            "output": (
                "Ran 1 test for test/SoundInvariant.t.sol:SoundInvariantTest\n"
                "[PASS] invariant_value_is_conserved() "
                "(runs: 9, calls: 36, reverts: 0)\n"
            ),
        }
        detail = run_module.foundry_record(
            PLUGIN_ROOT, self.catalogue, result
        )["detail"]
        self.assertEqual(detail["outcome"], "timed out")
        self.assertEqual(
            detail["laws_exercised"][self.CONSERVED]["evaluations"], 9
        )

    def test_match_output_names_what_no_declared_surface_ran_under(self):
        detail = self.detail(
            "Ran 1 test for test/Law.t.sol:LawTest\n"
            "[PASS] test_a_law_holding_returns_true_with_its_detail() (gas: 12)\n",
            argv=["forge", "test", "-vv", "--match-contract", "LawTest"],
        )
        self.assertEqual(detail["laws_exercised"], {})
        self.assertTrue(
            all(
                "--match LawTest" in reason
                for reason in detail["laws_not_exercised"].values()
            )
        )

    def test_every_law_exercised_omits_the_empty_not_exercised_section(self):
        detail = self.detail(
            "Ran 1 test for test/Corpus.t.sol:CorpusTest\n"
            "[PASS] test_minted_claims_breaks_conservation_alone() (gas: 1)\n"
            "Ran 1 test for test/Pairs.t.sol:PairsTest\n"
            "[PASS] test_no_transition_of_the_sound_reference_breaks_a_pair_law() "
            "(gas: 2)\n"
            "Ran 1 test for test/Pairs.t.sol:PairsTest\n"
            "[PASS] test_the_sound_reference_is_path_independent() (gas: 3)\n"
        )
        self.assertEqual(len(detail["laws_exercised"]), len(self.catalogue.laws))
        self.assertNotIn("laws_not_exercised", detail)

    def test_run_foundry_records_the_verbosity_that_makes_logs_readable(self):
        original = run_module.subprocess.run
        called = {}

        class Finished(object):
            returncode = 0
            stdout = b""

        def fake_run(argv, **kwargs):
            called["argv"] = argv
            return Finished()

        run_module.subprocess.run = fake_run
        try:
            result = run_module.run_foundry(PLUGIN_ROOT)
        finally:
            run_module.subprocess.run = original
        self.assertIn("-vv", called["argv"])
        self.assertEqual(result["argv"], called["argv"])


class CorpusDigestTests(unittest.TestCase):
    """The digest tracks the corpus and nothing else."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)
        for relative in ("catalogue", "src/laws", "specimens", "test/counterexamples"):
            os.makedirs(os.path.join(self.root, relative), exist_ok=True)
        self.write("src/laws/One.sol", 'contract One { function id() external pure returns (string memory) { return "a/b/v1"; } }\n')
        self.write("specimens/Broken.sol", "// deliberately broken\ncontract Broken {}\n")
        self.raw = {
            "version": "0.1.0",
            "observables": "ICreditObservables",
            "families": {"conservation": "held against each other"},
            "laws": [
                {
                    "id": "a/b/v1",
                    "family": "conservation",
                    "statement": "something",
                    "component": "src/laws/One.sol",
                    "specimen": "specimens/Broken.sol",
                    "counterexample": "test/counterexamples/One.t.sol",
                    "applicability": {"accounting_model": "m", "assumes": [], "requires": []},
                    "bounds": "exact",
                }
            ],
        }

    def write(self, relative, body):
        path = os.path.join(self.root, relative)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as handle:
            handle.write(body)

    def digest(self, raw=None):
        return run_module.corpus_digest(
            self.root, catalogue_module.parse(raw or self.raw)
        )["sha256"]

    def test_the_digest_is_stable_across_two_reads(self):
        self.assertEqual(self.digest(), self.digest())

    def test_a_changed_law_changes_the_digest(self):
        before = self.digest()
        self.write("src/laws/One.sol", 'contract One { function id() external pure returns (string memory) { return "a/b/v2"; } }\n')
        self.assertNotEqual(before, self.digest())

    def test_a_changed_specimen_changes_the_digest(self):
        before = self.digest()
        self.write("specimens/Broken.sol", "// deliberately broken\ncontract Broken { uint256 x; }\n")
        self.assertNotEqual(before, self.digest())

    def test_a_changed_catalogue_changes_the_digest(self):
        before = self.digest()
        changed = json.loads(json.dumps(self.raw))
        changed["laws"][0]["statement"] = "something else"
        self.assertNotEqual(before, self.digest(changed))

    def test_a_rewritten_comment_does_not_change_the_digest(self):
        """The point of stripping comments rather than hashing the file.

        A docstring rewrite is not a change to the corpus, and a digest that
        moved every time somebody improved a sentence would be a digest nobody
        could use to say two campaigns searched the same thing.
        """
        before = self.digest()
        self.write(
            "src/laws/One.sol",
            "/// A much better explanation of what this law does.\n"
            "// and a note\n"
            'contract One { function id() external pure returns (string memory) { return "a/b/v1"; } }\n',
        )
        self.assertEqual(before, self.digest())

    def test_a_slash_inside_a_string_is_not_a_comment(self):
        """Where a regex would get it wrong.

        A law's `statement()` is a string literal, and stripping from a `//`
        inside one would silently drop the rest of the law from the digest.
        """
        source = 'contract One { function s() external pure returns (string memory) { return "http://x"; } }\n'
        self.assertIn("http://x", run_module.strip_comments(source))

    def test_a_quote_inside_a_comment_does_not_open_a_string(self):
        source = '// it\'s fine\ncontract One { uint256 x; }\n'
        self.assertIn("contract One", run_module.strip_comments(source))

    def test_a_file_the_catalogue_claims_and_disk_lacks_is_refused(self):
        """Refused rather than skipped.

        A digest that quietly omitted a missing component would be a digest of
        a smaller corpus, reported as the corpus.
        """
        os.remove(os.path.join(self.root, "specimens/Broken.sol"))
        with self.assertRaises(run_module.RunError) as caught:
            self.digest()
        self.assertIn("specimens/Broken.sol", str(caught.exception))

    def test_a_file_on_disk_that_no_law_claims_does_not_change_the_digest(self):
        before = self.digest()
        self.write("src/laws/Unfiled.sol", "contract Unfiled {}\n")
        self.assertEqual(before, self.digest())


class ShippedCorpusTests(unittest.TestCase):
    def test_the_shipped_corpus_digests(self):
        catalogue = catalogue_module.load(SHIPPED)
        found = run_module.corpus_digest(PLUGIN_ROOT, catalogue)
        self.assertEqual(len(found["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
