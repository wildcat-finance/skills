"""Focused tests for the report-only dead-code scaffold."""

import gc
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
import warnings
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dead_code.py"
SCHEMA_PATH = ROOT / "schemas" / "dead-code-report-v1.schema.json"
WORKFLOW_PATH = ROOT / ".github" / "workflows" / "dead-code.yml"
CHECK_MAP_PATH = ROOT / "tests" / "check-map-v1.json"
STUDY_PATH = ROOT / "docs" / "dead-code" / "study.md"
RUNBOOK_PATH = ROOT / "docs" / "dead-code" / "runbook.md"
ADR_PATH = (
    ROOT
    / "docs"
    / "decisions"
    / "ADR-051-keep-dead-code-discovery-report-only.md"
)
EXPECTED_STUDY_SHA256 = "da8ceed7ee91168e4ab60b1d3ba27c4e59df40be3a9dadd87d0dba17af8059e6"
EXPECTED_RUNBOOK_SHA256 = "e5ea55c688615d9d1d0322e8c82bba335acfd6745cac99f49b471a564f860857"
NL = chr(10)

SPEC = importlib.util.spec_from_file_location("dead_code", SCRIPT)
dead_code = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = dead_code
SPEC.loader.exec_module(dead_code)


def git(directory, *arguments):
    return subprocess.run(
        ["git", "-C", str(directory), *arguments],
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def horos_entry(
    path,
    *,
    category="generated",
    evidence="classified by the fixture",
    grade="hard",
):
    return {
        "path": path,
        "category": category,
        "evidence": evidence,
        "grade": grade,
        "bytes": 1,
    }


def boundary_document(entries):
    return {
        "schema": 2,
        "tool": "horos",
        "universe": "tracked",
        "counts": {},
        "entries": entries,
    }


def build_repository(
    directory,
    *,
    files=None,
    entries=None,
    boundary_text=None,
    commit=True,
):
    files = {"a.py": "x = 1" + NL} if files is None else files
    entries = [] if entries is None else entries
    git(directory, "init", "--quiet", "--initial-branch=main")
    git(directory, "config", "user.email", "test@example.invalid")
    git(directory, "config", "user.name", "Test")
    git(directory, "config", "commit.gpgsign", "false")
    for relative, content in files.items():
        target = directory / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    target = directory / ".horos" / "boundary.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    if boundary_text is None:
        boundary_text = json.dumps(boundary_document(entries), sort_keys=True) + NL
    target.write_text(boundary_text, encoding="utf-8")
    git(directory, "add", "-A")
    if commit:
        git(directory, "commit", "--quiet", "-m", "fixture")
    return directory


class TemporaryRepositoryTestCase(unittest.TestCase):
    def setUp(self):
        self._temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary.cleanup)
        self.root = Path(self._temporary.name).resolve()


class UniverseDiscoveryTests(TemporaryRepositoryTestCase):
    def test_bounded_process_closes_both_capture_pipes(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            dead_code.run_process(
                ["git", "--version"],
                cwd=self.root,
                timeout_seconds=5,
                output_limit=4096,
            )
            gc.collect()
        leaked = [item for item in caught if item.category is ResourceWarning]
        self.assertEqual(leaked, [])

    def test_universe_binds_the_exact_commit_and_git_tree(self):
        build_repository(
            self.root,
            files={"b.py": "b = 2" + NL, "a.py": "a = 1" + NL},
        )
        universe = dead_code.discover(self.root)
        self.assertEqual(universe.commit, git(self.root, "rev-parse", "HEAD").strip())
        self.assertEqual(
            universe.tree,
            git(self.root, "rev-parse", "HEAD^{tree}").strip(),
        )
        self.assertEqual(len(universe.commit), 40)
        self.assertEqual(len(universe.tree), 40)

    def test_universe_paths_are_sorted_and_identity_is_recomputed(self):
        build_repository(
            self.root,
            files={"z.py": "z = 1" + NL, "a.py": "a = 1" + NL},
        )
        universe = dead_code.discover(self.root)
        self.assertEqual(universe.analysed, tuple(sorted(universe.analysed)))
        self.assertEqual(
            universe.identity,
            dead_code.universe_identity(
                universe.tree,
                universe.analysed,
                universe.excluded,
            ),
        )

    def test_untracked_files_do_not_enter_the_committed_universe(self):
        build_repository(self.root)
        (self.root / "scratch.txt").write_text("scratch", encoding="utf-8")
        universe = dead_code.discover(self.root)
        self.assertNotIn("scratch.txt", universe.analysed)

    def test_modified_tracked_bytes_refuse_before_discovery(self):
        build_repository(self.root)
        (self.root / "a.py").write_text("x = 2" + NL, encoding="utf-8")
        with self.assertRaisesRegex(dead_code.Refusal, "modified tracked"):
            dead_code.discover(self.root)

    def test_staged_tracked_bytes_refuse_before_discovery(self):
        build_repository(self.root)
        (self.root / "a.py").write_text("x = 2" + NL, encoding="utf-8")
        git(self.root, "add", "a.py")
        with self.assertRaisesRegex(dead_code.Refusal, "modified tracked"):
            dead_code.discover(self.root)

    def test_empty_analysed_walk_refuses_instead_of_reporting_clean(self):
        build_repository(
            self.root,
            files={"generated.txt": "generated" + NL},
            entries=[
                horos_entry("generated.txt"),
                horos_entry(".horos/boundary.json"),
            ],
        )
        with self.assertRaisesRegex(dead_code.Refusal, "collapsed walk"):
            dead_code.discover(self.root)

    def test_discovery_outside_a_git_worktree_refuses(self):
        with self.assertRaises(dead_code.Refusal):
            dead_code.repository_root(self.root)


class ClassificationJoinTests(TemporaryRepositoryTestCase):
    def test_hard_file_classification_excludes_and_carries_evidence(self):
        build_repository(
            self.root,
            files={
                "a.py": "x = 1" + NL,
                "CONTRIBUTORS.md": "generated" + NL,
            },
            entries=[
                horos_entry(
                    "CONTRIBUTORS.md",
                    evidence="generation marker in the first 4096 bytes",
                )
            ],
        )
        universe = dead_code.discover(self.root)
        excluded = {entry.path: entry for entry in universe.excluded}
        self.assertNotIn("CONTRIBUTORS.md", universe.analysed)
        self.assertIn("generation marker", excluded["CONTRIBUTORS.md"].evidence)
        self.assertEqual(excluded["CONTRIBUTORS.md"].grade, "hard")

    def test_candidate_grade_remains_in_the_fail_open_universe(self):
        build_repository(
            self.root,
            files={"a.py": "x = 1" + NL, "maybe.txt": "maybe" + NL},
            entries=[horos_entry("maybe.txt", grade="candidate")],
        )
        universe = dead_code.discover(self.root)
        self.assertIn("maybe.txt", universe.analysed)

    def test_boundary_entry_for_an_absent_path_excludes_nothing(self):
        build_repository(self.root, entries=[horos_entry("gone.txt")])
        self.assertEqual(dead_code.discover(self.root).excluded, ())

    def test_hard_directory_classification_excludes_every_descendant(self):
        build_repository(
            self.root,
            files={
                "a.py": "x = 1" + NL,
                "vendor/pkg/a.py": "a = 1" + NL,
                "vendor/pkg/b.py": "b = 1" + NL,
            },
            entries=[
                horos_entry(
                    "vendor/",
                    category="vendored",
                    evidence="directory name vendor",
                )
            ],
        )
        universe = dead_code.discover(self.root)
        self.assertIn("a.py", universe.analysed)
        self.assertNotIn("vendor/pkg/a.py", universe.analysed)
        self.assertNotIn("vendor/pkg/b.py", universe.analysed)
        self.assertEqual(universe.excluded_by_category(), {"vendored": 2})

    def test_inherited_exclusion_names_the_classified_tree(self):
        build_repository(
            self.root,
            files={"a.py": "x = 1" + NL, "build/out.json": "{}" + NL},
            entries=[
                horos_entry(
                    "build/",
                    evidence="directory name build",
                )
            ],
        )
        excluded = {
            entry.path: entry for entry in dead_code.discover(self.root).excluded
        }
        self.assertIn("directory name build", excluded["build/out.json"].evidence)
        self.assertIn("classified tree build/", excluded["build/out.json"].evidence)

    def test_directory_prefix_does_not_capture_a_sibling_with_the_same_stem(self):
        build_repository(
            self.root,
            files={
                "lib/vendored.py": "x = 1" + NL,
                "libexec/kept.py": "y = 2" + NL,
            },
            entries=[
                horos_entry(
                    "lib/",
                    category="vendored",
                    evidence="directory name lib",
                )
            ],
        )
        universe = dead_code.discover(self.root)
        self.assertNotIn("lib/vendored.py", universe.analysed)
        self.assertIn("libexec/kept.py", universe.analysed)

    def test_longest_classified_directory_supplies_descendant_evidence(self):
        build_repository(
            self.root,
            files={
                "a.py": "x = 1" + NL,
                "tree/nested/item.txt": "item" + NL,
            },
            entries=[
                horos_entry("tree/", evidence="outer tree"),
                horos_entry("tree/nested/", evidence="inner tree"),
            ],
        )
        excluded = {
            entry.path: entry for entry in dead_code.discover(self.root).excluded
        }
        self.assertIn("inner tree", excluded["tree/nested/item.txt"].evidence)
        self.assertNotIn("outer tree", excluded["tree/nested/item.txt"].evidence)

    def test_exclusion_counts_are_sorted_by_category(self):
        build_repository(
            self.root,
            files={
                "a.py": "x" + NL,
                "z.txt": "z" + NL,
                "a.txt": "a" + NL,
            },
            entries=[
                horos_entry("z.txt", category="vendored"),
                horos_entry("a.txt", category="binary"),
            ],
        )
        counts = dead_code.discover(self.root).excluded_by_category()
        self.assertEqual(list(counts), ["binary", "vendored"])


class BoundaryRefusalTests(TemporaryRepositoryTestCase):
    def _replace_boundary(self, text):
        build_repository(self.root)
        target = self.root / ".horos" / "boundary.json"
        target.write_text(text, encoding="utf-8")
        git(self.root, "add", "-A")
        git(self.root, "commit", "--quiet", "-m", "boundary")

    def test_absent_boundary_refuses_by_name(self):
        build_repository(self.root)
        target = self.root / ".horos" / "boundary.json"
        target.unlink()
        git(self.root, "add", "-A")
        git(self.root, "commit", "--quiet", "-m", "drop boundary")
        with self.assertRaisesRegex(dead_code.Refusal, ".horos/boundary.json"):
            dead_code.load_boundary(self.root)

    def test_boundary_symlink_refuses_as_non_regular(self):
        outside = self.root.parent / (self.root.name + "-outside.json")
        self.addCleanup(outside.unlink, missing_ok=True)
        outside.write_text(
            json.dumps(boundary_document([])),
            encoding="utf-8",
        )
        build_repository(self.root)
        target = self.root / ".horos" / "boundary.json"
        target.unlink()
        target.symlink_to(outside)
        with self.assertRaisesRegex(dead_code.Refusal, "not a regular file"):
            dead_code.load_boundary(self.root)

    def test_oversized_boundary_refuses_before_json_parse(self):
        build_repository(self.root)
        with mock.patch.object(dead_code, "MAX_BOUNDARY_BYTES", 8):
            with self.assertRaisesRegex(dead_code.Refusal, "exceeds 8 bytes"):
                dead_code.load_boundary(self.root)

    def test_malformed_boundary_json_refuses(self):
        self._replace_boundary("{not json")
        with self.assertRaisesRegex(dead_code.Refusal, "not valid JSON"):
            dead_code.load_boundary(self.root)

    def test_duplicate_json_key_refuses_instead_of_overwriting(self):
        self._replace_boundary(
            '{"schema":2,"tool":"horos","tool":"other","entries":[]}'
        )
        with self.assertRaisesRegex(dead_code.Refusal, "repeats JSON key tool"):
            dead_code.load_boundary(self.root)

    def test_wrong_boundary_schema_refuses_as_stale(self):
        self._replace_boundary(
            json.dumps({"schema": 1, "tool": "horos", "entries": []})
        )
        with self.assertRaisesRegex(dead_code.Refusal, "schema 2"):
            dead_code.load_boundary(self.root)

    def test_wrong_boundary_tool_refuses(self):
        self._replace_boundary(
            json.dumps({"schema": 2, "tool": "other", "entries": []})
        )
        with self.assertRaisesRegex(dead_code.Refusal, "tool horos"):
            dead_code.load_boundary(self.root)

    def test_missing_entries_list_refuses(self):
        self._replace_boundary(json.dumps({"schema": 2, "tool": "horos"}))
        with self.assertRaisesRegex(dead_code.Refusal, "no entries list"):
            dead_code.load_boundary(self.root)

    def test_entry_missing_evidence_refuses(self):
        broken = {
            "path": "a.py",
            "category": "generated",
            "grade": "hard",
        }
        self._replace_boundary(
            json.dumps(
                {
                    "schema": 2,
                    "tool": "horos",
                    "entries": [broken],
                }
            )
        )
        with self.assertRaisesRegex(dead_code.Refusal, "evidence"):
            dead_code.load_boundary(self.root)

    def test_duplicate_classified_path_refuses(self):
        duplicate = horos_entry("a.py")
        self._replace_boundary(
            json.dumps(
                {
                    "schema": 2,
                    "tool": "horos",
                    "entries": [duplicate, duplicate],
                }
            )
        )
        with self.assertRaisesRegex(dead_code.Refusal, "repeats classified path"):
            dead_code.load_boundary(self.root)

    def test_unsafe_classified_path_refuses(self):
        self._replace_boundary(
            json.dumps(
                {
                    "schema": 2,
                    "tool": "horos",
                    "entries": [horos_entry("../outside")],
                }
            )
        )
        with self.assertRaisesRegex(dead_code.Refusal, "safe repository-relative"):
            dead_code.load_boundary(self.root)


class RenderingTests(TemporaryRepositoryTestCase):
    def _report(self):
        build_repository(
            self.root,
            files={
                "b.py": "b = 2" + NL,
                "a.py": "a = 1" + NL,
                "generated.txt": "g" + NL,
            },
            entries=[horos_entry("generated.txt")],
        )
        return dead_code.build_report(self.root)

    def test_json_has_the_schema_fixed_top_level_shape(self):
        document = json.loads(dead_code.render_json(self._report()))
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(document), set(schema["required"]))
        self.assertEqual(document["schema"], "dead-code-report/v1")
        self.assertEqual(document["tool"], {"id": "dead-code", "version": "1"})

    def test_schema_fixes_tool_universe_status_and_finding_identities(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        definitions = schema["$defs"]
        self.assertEqual(
            definitions["toolIdentity"]["properties"]["id"]["const"],
            "dead-code",
        )
        self.assertEqual(
            definitions["analysisStatus"]["properties"]["id"]["const"],
            "analysis",
        )
        self.assertEqual(
            definitions["universeIdentity"]["properties"]["id"]["$ref"],
            "#/$defs/sha256Identity",
        )
        self.assertEqual(
            definitions["finding"]["properties"]["id"]["$ref"],
            "#/$defs/sha256Identity",
        )

    def test_text_and_json_carry_the_same_tree_universe_status_and_counts(self):
        report = self._report()
        document = json.loads(dead_code.render_json(report))
        text = dead_code.render_text(report)
        for value in (
            document["tree"]["commit"],
            document["tree"]["git_tree"],
            document["universe"]["id"],
            document["status"]["state"],
        ):
            self.assertIn(value, text)
        self.assertIn(
            f"{document['universe']['analysed_count']} analysed",
            text,
        )
        self.assertIn(
            f"{document['universe']['excluded_count']} excluded",
            text,
        )

    def test_report_explicitly_says_that_no_analyser_ran(self):
        report = self._report()
        document = json.loads(dead_code.render_json(report))
        text = dead_code.render_text(report)
        self.assertEqual(document["status"]["state"], "not-run")
        self.assertEqual(document["analysers"], [])
        self.assertIn("none ran", text)
        self.assertIn("no reachability result", text)

    def test_finding_identity_and_evidence_match_in_both_renderings(self):
        base = self._report()
        status = dead_code.AnalyserStatus(
            analyser_id="python",
            state="ran",
            version="1",
            detail="fixture analyser completed",
        )
        finding = dead_code.Finding(
            analyser_id="python",
            path=base.universe.analysed[0],
            symbol="candidate",
            evidence="no static reference in the fixture graph",
            confidence="medium",
            false_positive_boundary="a computed import could reach the symbol",
        )
        report = dead_code.Report(
            universe=base.universe,
            statuses=(status,),
            findings=(finding,),
        )
        dead_code.validate_report(report)
        document = json.loads(dead_code.render_json(report))
        text = dead_code.render_text(report)
        self.assertEqual(document["findings"][0]["id"], finding.identity)
        for value in (
            finding.identity,
            finding.path,
            finding.symbol,
            finding.evidence,
            finding.false_positive_boundary,
        ):
            self.assertIn(value, text)

    def test_collect_sorts_statuses_and_findings_from_one_model(self):
        build_repository(
            self.root,
            files={"b.py": "b = 1" + NL, "a.py": "a = 1" + NL},
        )
        universe = dead_code.discover(self.root)

        def analyser(name, path):
            def run(root, supplied_universe):
                self.assertEqual(supplied_universe, universe)
                return (
                    dead_code.AnalyserStatus(name, "ran", "1", "done"),
                    (
                        dead_code.Finding(
                            name,
                            path,
                            None,
                            "fixture evidence",
                            "low",
                            "fixture boundary",
                        ),
                    ),
                )
            return run

        with mock.patch.dict(
            dead_code.ANALYSERS,
            {
                "zeta": analyser("zeta", "b.py"),
                "alpha": analyser("alpha", "a.py"),
            },
            clear=True,
        ):
            statuses, findings = dead_code.collect(self.root, universe)
        self.assertEqual(
            [item.analyser_id for item in statuses],
            ["alpha", "zeta"],
        )
        self.assertEqual(
            [(item.analyser_id, item.path) for item in findings],
            [("alpha", "a.py"), ("zeta", "b.py")],
        )

    def test_unreported_analyser_cannot_supply_a_finding(self):
        base = self._report()
        finding = dead_code.Finding(
            "missing",
            base.universe.analysed[0],
            None,
            "evidence",
            "low",
            "boundary",
        )
        report = dead_code.Report(base.universe, (), (finding,))
        with self.assertRaisesRegex(dead_code.Refusal, "unreported analyser"):
            dead_code.validate_report(report)

    def test_candidate_count_does_not_change_the_report_exit_contract(self):
        base = self._report()
        status = dead_code.AnalyserStatus("python", "ran", "1", "done")
        finding = dead_code.Finding(
            "python",
            base.universe.analysed[0],
            None,
            "evidence",
            "low",
            "boundary",
        )
        report = dead_code.Report(base.universe, (status,), (finding,))
        dead_code.validate_report(report)
        self.assertIn("1 candidate(s); report-only", dead_code.render_text(report))

    def test_rendering_never_strengthens_candidates_into_deletion_authority(self):
        report = self._report()
        rendered = (dead_code.render_text(report) + dead_code.render_json(report)).lower()
        for forbidden in (
            "is dead",
            "safe to delete",
            "can be removed",
            "proves unused",
        ):
            self.assertNotIn(forbidden, rendered)


class WriteBoundaryTests(TemporaryRepositoryTestCase):
    def setUp(self):
        super().setUp()
        build_repository(self.root)

    def test_parent_escape_is_refused(self):
        with self.assertRaisesRegex(dead_code.Refusal, "escapes"):
            dead_code.confine(self.root, "../escape.json")

    def test_absolute_output_is_refused(self):
        with self.assertRaisesRegex(dead_code.Refusal, "repository-relative"):
            dead_code.confine(self.root, str(self.root / "out.json"))

    def test_repository_root_is_not_an_output_file(self):
        with self.assertRaises(dead_code.Refusal):
            dead_code.confine(self.root, ".")

    def test_null_byte_output_is_refused(self):
        with self.assertRaisesRegex(dead_code.Refusal, "null byte"):
            dead_code.confine(self.root, "out" + chr(0) + ".json")

    def test_descendant_output_is_confined_to_the_repository(self):
        target = dead_code.confine(self.root, ".dead-code/report.json")
        self.assertEqual(target, self.root / ".dead-code" / "report.json")

    def test_output_outside_the_owned_dead_code_sink_is_refused(self):
        with self.assertRaisesRegex(dead_code.Refusal, "owned .dead-code"):
            dead_code.confine(self.root, "a.py")

    def test_symlinked_output_ancestor_is_refused(self):
        outside = self.root.parent / (self.root.name + "-outside")
        outside.mkdir()
        self.addCleanup(outside.rmdir)
        (self.root / ".dead-code").symlink_to(outside, target_is_directory=True)
        target = dead_code.confine(self.root, ".dead-code/out.json")
        with self.assertRaisesRegex(dead_code.Refusal, "not a real directory"):
            dead_code.atomic_write(self.root, target, "{}" + NL)

    def test_symlinked_output_target_is_refused(self):
        outside = self.root.parent / (self.root.name + "-outside.json")
        outside.write_text("old", encoding="utf-8")
        self.addCleanup(outside.unlink, missing_ok=True)
        (self.root / ".dead-code").mkdir()
        target = self.root / ".dead-code" / "out.json"
        target.symlink_to(outside)
        with self.assertRaisesRegex(dead_code.Refusal, "not a regular file"):
            dead_code.atomic_write(self.root, target, "new" + NL)
        self.assertEqual(outside.read_text(encoding="utf-8"), "old")

    def test_atomic_write_publishes_complete_bytes_and_no_temporary(self):
        target = dead_code.confine(self.root, ".dead-code/report.json")
        dead_code.atomic_write(self.root, target, "payload" + NL)
        self.assertEqual(target.read_text(encoding="utf-8"), "payload" + NL)
        leftovers = [
            item
            for item in target.parent.iterdir()
            if item.name.startswith(dead_code.TEMP_PREFIX)
        ]
        self.assertEqual(leftovers, [])

    def test_failed_replace_leaves_the_previous_report_intact(self):
        target = dead_code.confine(self.root, ".dead-code/report.json")
        target.parent.mkdir()
        target.write_text("previous" + NL, encoding="utf-8")
        with mock.patch.object(
            dead_code.os,
            "replace",
            side_effect=OSError("fixture interruption"),
        ):
            with self.assertRaisesRegex(dead_code.Refusal, "report write failed"):
                dead_code.atomic_write(self.root, target, "replacement" + NL)
        self.assertEqual(target.read_text(encoding="utf-8"), "previous" + NL)
        leftovers = [
            item
            for item in target.parent.iterdir()
            if item.name.startswith(dead_code.TEMP_PREFIX)
        ]
        self.assertEqual(leftovers, [])

    def test_ancestor_substitution_cannot_redirect_the_atomic_replace(self):
        target = dead_code.confine(self.root, ".dead-code/report.json")
        outside = self.root.parent / (self.root.name + "-outside-directory")
        held = self.root / ".dead-code-opened"
        outside.mkdir()
        self.addCleanup(outside.rmdir)
        real_replace = os.replace

        def substitute_ancestor(source, destination, **kwargs):
            target.parent.rename(held)
            target.parent.symlink_to(outside, target_is_directory=True)
            real_replace(source, destination, **kwargs)

        refusal = None
        try:
            with mock.patch.object(
                dead_code.os,
                "replace",
                side_effect=substitute_ancestor,
            ):
                dead_code.atomic_write(self.root, target, "payload" + NL)
        except dead_code.Refusal as error:
            refusal = str(error)
        self.assertIsNone(refusal, refusal)
        self.assertFalse((outside / "report.json").exists())
        self.assertEqual(
            (held / "report.json").read_text(encoding="utf-8"),
            "payload" + NL,
        )

    def test_atomic_write_does_not_sweep_an_unrelated_owned_temporary(self):
        directory = self.root / ".dead-code"
        directory.mkdir()
        orphan = directory / (dead_code.TEMP_PREFIX + "old")
        bystander = directory / "keep.json"
        orphan.write_text("half", encoding="utf-8")
        bystander.write_text("keep", encoding="utf-8")
        dead_code.atomic_write(self.root, directory / "report.json", "payload" + NL)
        self.assertTrue(orphan.exists())
        self.assertTrue(bystander.exists())


class CommandLineTests(TemporaryRepositoryTestCase):
    def setUp(self):
        super().setUp()
        build_repository(
            self.root,
            files={
                "a.py": "a = 1" + NL,
                "b.py": "b = 1" + NL,
                "generated.txt": "generated" + NL,
            },
            entries=[horos_entry("generated.txt")],
        )

    def _run(self, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--directory",
                str(self.root),
                *arguments,
            ],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_text_report_exits_zero_with_tree_and_not_run_status(self):
        completed = self._run("report")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("dead-code 1 report", completed.stdout)
        self.assertIn("tree      ", completed.stdout)
        self.assertIn("status    not-run", completed.stdout)

    def test_json_report_exits_zero_and_parses(self):
        completed = self._run("report", "--json")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        document = json.loads(completed.stdout)
        self.assertEqual(document["schema"], "dead-code-report/v1")
        self.assertEqual(document["universe"]["analysed_count"], 3)
        self.assertEqual(document["status"]["state"], "not-run")

    def test_dirty_tree_refusal_exits_two_without_stdout(self):
        (self.root / "a.py").write_text("changed" + NL, encoding="utf-8")
        completed = self._run("report")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("modified tracked", completed.stderr)
        self.assertEqual(completed.stdout, "")

    def test_output_flag_writes_schema_valid_shape_inside_repository(self):
        completed = self._run(
            "report",
            "--json",
            "--output",
            ".dead-code/report.json",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        document = json.loads(
            (self.root / ".dead-code" / "report.json").read_text(encoding="utf-8")
        )
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(set(document), set(schema["required"]))
        self.assertEqual(
            document["universe"]["tracked_count"],
            document["universe"]["analysed_count"]
            + document["universe"]["excluded_count"],
        )

    def test_unsafe_output_path_exits_two(self):
        completed = self._run("report", "--output", "../escape.json")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("escapes", completed.stderr)

    def test_output_flag_cannot_overwrite_a_tracked_source_file(self):
        target = self.root / "a.py"
        before = target.read_bytes()
        completed = self._run("report", "--output", "a.py")
        self.assertEqual(completed.returncode, 2)
        self.assertIn("owned .dead-code", completed.stderr)
        self.assertEqual(target.read_bytes(), before)
        self.assertEqual(git(self.root, "status", "--porcelain"), "")


class ShippedSurfaceTests(unittest.TestCase):
    def test_receipted_study_and_runbook_digests_are_preserved(self):
        self.assertEqual(
            hashlib.sha256(STUDY_PATH.read_bytes()).hexdigest(),
            EXPECTED_STUDY_SHA256,
        )
        self.assertEqual(
            hashlib.sha256(RUNBOOK_PATH.read_bytes()).hexdigest(),
            EXPECTED_RUNBOOK_SHA256,
        )

    def test_adr_has_the_repository_shape_and_records_both_ownership_boundaries(self):
        text = ADR_PATH.read_text(encoding="utf-8")
        for heading in (
            "## Status",
            "## Context",
            "## Decision",
            "## Alternatives",
            "## Consequences",
        ):
            self.assertIn(heading, text)
        self.assertIn("report-only", text)
        self.assertIn("Horos", text)
        self.assertIn("checked runner", text)
        self.assertIn("one analyser in every plugin", text)

    def test_schema_is_closed_at_every_named_record_identity(self):
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertFalse(schema["additionalProperties"])
        for name in (
            "toolIdentity",
            "treeIdentity",
            "universeIdentity",
            "analysisStatus",
            "analyserStatus",
            "finding",
        ):
            self.assertFalse(schema["$defs"][name]["additionalProperties"])

    def test_check_map_declares_the_focused_dead_code_scope(self):
        check_map = json.loads(CHECK_MAP_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            check_map["scopes"]["dead-code"]["checks"],
            ["dead-code-suite"],
        )
        self.assertEqual(
            check_map["checks"]["dead-code-suite"]["argv"],
            ["python3", "-m", "unittest", "tests.test_dead_code", "-v"],
        )

    def test_check_map_assigns_every_dead_code_surface_to_the_scope(self):
        check_map = json.loads(CHECK_MAP_PATH.read_text(encoding="utf-8"))
        owners = {
            entry["path"]: entry["scope"]
            for entry in check_map["owners"]
        }
        expected = (
            ".github/workflows/dead-code.yml",
            "docs/dead-code",
            "docs/decisions/ADR-051-keep-dead-code-discovery-report-only.md",
            "schemas/dead-code-report-v1.schema.json",
            "scripts/dead_code.py",
            "tests/emit_dead_code_report.py",
            "tests/test_dead_code.py",
        )
        for path in expected:
            self.assertEqual(owners.get(path), "dead-code", path)

    def test_workflow_is_read_only_and_runs_the_checked_scope(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        self.assertIn("contents: read", text)
        self.assertNotIn("contents: write", text)
        self.assertIn("scripts/run_checks.py --scope dead-code", text)
        self.assertIn('python-version-file: ".python-version"', text)

    def test_workflow_summary_names_tree_universe_analyser_and_non_gating_state(self):
        text = WORKFLOW_PATH.read_text(encoding="utf-8")
        for field in ("commit", "git_tree", "universe", "status", "analysers"):
            self.assertIn(field, text)
        self.assertIn("Candidates are reported, not gated", text)
        self.assertNotIn("findings']) > 0", text)

    def test_source_contains_no_source_removal_or_shell_execution(self):
        source = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("shutil.rmtree", "os.remove(", "shell=True"):
            self.assertNotIn(forbidden, source)

    def test_owned_temporary_and_report_paths_are_ignored(self):
        text = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(dead_code.TEMP_PREFIX, text)
        self.assertIn("/.dead-code/report.json", text)
        self.assertIn("/.dead-code/checks.json", text)


if __name__ == "__main__":
    unittest.main()
