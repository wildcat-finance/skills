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
MONITOR_SCRIPT = ROOT / "scripts" / "dead_code_monitoring" / "sitecustomize.py"
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

MONITOR_SPEC = importlib.util.spec_from_file_location("dead_code_monitor", MONITOR_SCRIPT)
dead_code_monitor = importlib.util.module_from_spec(MONITOR_SPEC)
sys.modules[MONITOR_SPEC.name] = dead_code_monitor
MONITOR_SPEC.loader.exec_module(dead_code_monitor)


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

    def test_transient_boundary_edit_cannot_change_the_commit_universe(self):
        build_repository(
            self.root,
            files={
                "a.py": "a = 1" + NL,
                "generated.txt": "generated" + NL,
            },
            entries=[horos_entry("generated.txt")],
        )
        boundary = self.root / ".horos" / "boundary.json"
        committed = boundary.read_text(encoding="utf-8")
        replacement = json.dumps(
            boundary_document([horos_entry("a.py")]),
            sort_keys=True,
        ) + NL
        real_require_clean_tree = dead_code.require_clean_tree
        real_load_boundary = dead_code.load_boundary

        def edit_after_clean_check(root, *args, **kwargs):
            real_require_clean_tree(root, *args, **kwargs)
            boundary.write_text(replacement, encoding="utf-8")

        def load_then_restore(*args, **kwargs):
            try:
                return real_load_boundary(*args, **kwargs)
            finally:
                boundary.write_text(committed, encoding="utf-8")

        with (
            mock.patch.object(
                dead_code,
                "require_clean_tree",
                side_effect=edit_after_clean_check,
            ),
            mock.patch.object(
                dead_code,
                "load_boundary",
                side_effect=load_then_restore,
            ),
        ):
            universe = dead_code.discover(self.root)

        self.assertIn("a.py", universe.analysed)
        self.assertNotIn("generated.txt", universe.analysed)

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
        git(self.root, "add", "-A")
        git(self.root, "commit", "--quiet", "-m", "symlink boundary")
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

    def test_boolean_record_telemetry_is_not_an_integer(self):
        base = self._report()
        status = dead_code.AnalyserStatus(
            "repository",
            "ran",
            "repository-graph/1",
            "done",
            (
                dead_code.AnalyserRecord(
                    "fixture",
                    "family",
                    "parsed",
                    "done",
                    True,
                ),
            ),
        )
        with self.assertRaisesRegex(dead_code.Refusal, "invalid record"):
            dead_code.validate_report(dead_code.Report(base.universe, (status,), ()))

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

    def test_text_rendering_escapes_untrusted_record_newlines(self):
        base = self._report()
        status = dead_code.AnalyserStatus(
            "solidity",
            "degraded",
            "slither+forge/1",
            "tool incomplete",
            (
                dead_code.AnalyserRecord(
                    ".:slither",
                    "project",
                    "failed",
                    "tool failed",
                    1,
                    "0.11.4",
                    1,
                    0,
                    "warning\nstatus forged",
                ),
            ),
        )
        text = dead_code.render_text(dead_code.Report(base.universe, (status,), ()))
        self.assertNotIn("\nstatus forged", text)
        self.assertIn(r"warning\nstatus forged", text)


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

    def test_repository_substitution_cannot_redirect_directory_traversal(self):
        target = dead_code.confine(self.root, ".dead-code/report.json")
        outside = self.root.parent / (self.root.name + "-outside-directory")
        held = self.root.parent / (self.root.name + "-opened-repository")
        outside.mkdir()

        def restore_repository():
            outside_report = outside / ".dead-code" / "report.json"
            outside_report.unlink(missing_ok=True)
            try:
                outside_report.parent.rmdir()
            except FileNotFoundError:
                pass
            if self.root.is_symlink():
                self.root.unlink()
            if held.exists():
                held.rename(self.root)
            outside.rmdir()

        self.addCleanup(restore_repository)
        real_output_parts = dead_code.output_parts

        def substitute_repository(root, output):
            parts = real_output_parts(root, output)
            self.root.rename(held)
            self.root.symlink_to(outside, target_is_directory=True)
            return parts

        refusal = None
        try:
            with mock.patch.object(
                dead_code,
                "output_parts",
                side_effect=substitute_repository,
            ):
                dead_code.atomic_write(self.root, target, "payload" + NL)
        except dead_code.Refusal as error:
            refusal = str(error)
        self.assertIsNone(refusal, refusal)
        self.assertFalse((outside / ".dead-code" / "report.json").exists())
        self.assertEqual(
            (held / ".dead-code" / "report.json").read_text(encoding="utf-8"),
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

    def test_repository_substitution_after_render_cannot_redirect_output(self):
        outside = self.root.parent / (self.root.name + "-outside-directory")
        held = self.root.parent / (self.root.name + "-opened-repository")
        outside.mkdir()

        def restore_repository():
            outside_report = outside / ".dead-code" / "report.json"
            outside_report.unlink(missing_ok=True)
            try:
                outside_report.parent.rmdir()
            except FileNotFoundError:
                pass
            if self.root.is_symlink():
                self.root.unlink()
            if held.exists():
                held.rename(self.root)
            outside.rmdir()

        self.addCleanup(restore_repository)
        real_render_json = dead_code.render_json

        def substitute_repository(report):
            rendered = real_render_json(report)
            self.root.rename(held)
            self.root.symlink_to(outside, target_is_directory=True)
            return rendered

        arguments = dead_code.argparse.Namespace(
            directory=str(self.root),
            json=True,
            output=".dead-code/report.json",
        )
        with mock.patch.object(
            dead_code,
            "render_json",
            side_effect=substitute_repository,
        ):
            result = dead_code.command_report(arguments)
        self.assertEqual(result, 0)
        self.assertFalse((outside / ".dead-code" / "report.json").exists())
        report_path = held / ".dead-code" / "report.json"
        self.assertEqual(
            json.loads(report_path.read_text(encoding="utf-8"))["schema"],
            "dead-code-report/v1",
        )

    def test_repository_substitution_before_discovery_keeps_the_opened_tree(self):
        original_commit = git(self.root, "rev-parse", "HEAD").strip()
        outside_temporary = tempfile.TemporaryDirectory()
        self.addCleanup(outside_temporary.cleanup)
        outside = Path(outside_temporary.name).resolve()
        build_repository(
            outside,
            files={"outside.py": "outside = True" + NL},
        )
        self.assertNotEqual(
            original_commit,
            git(outside, "rev-parse", "HEAD").strip(),
        )
        held = self.root.parent / (self.root.name + "-opened-repository")
        real_build_report = dead_code.build_report

        def substitute_repository(root, *args, **kwargs):
            self.root.rename(held)
            self.root.symlink_to(outside, target_is_directory=True)
            return real_build_report(root, *args, **kwargs)

        arguments = dead_code.argparse.Namespace(
            directory=str(self.root),
            json=True,
            output=".dead-code/report.json",
        )
        try:
            with mock.patch.object(
                dead_code,
                "build_report",
                side_effect=substitute_repository,
            ):
                result = dead_code.command_report(arguments)
            report = json.loads(
                (held / ".dead-code" / "report.json").read_text(encoding="utf-8")
            )
        finally:
            if self.root.is_symlink():
                self.root.unlink()
            if held.exists():
                held.rename(self.root)

        self.assertEqual(result, 0)
        self.assertEqual(report["tree"]["commit"], original_commit)
        self.assertIn("a.py", report["universe"]["analysed"])
        self.assertNotIn("outside.py", report["universe"]["analysed"])

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


class PythonAnalyserTests(TemporaryRepositoryTestCase):
    def _analyse(self, files):
        build_repository(self.root, files=files)
        universe = dead_code.discover(self.root)
        return universe, dead_code.analyse_python(self.root, universe)

    def test_every_python_file_has_a_parse_record(self):
        _universe, (status, _findings) = self._analyse(
            {"main.py": "x = 1" + NL, "pkg/mod.py": "y = 2" + NL}
        )
        self.assertEqual(status.state, "ran")
        self.assertEqual([item.record_id for item in status.records], ["main.py", "pkg/mod.py"])
        self.assertTrue(all(item.state == "parsed" for item in status.records))

    def test_syntax_error_degrades_and_names_the_file(self):
        _universe, (status, findings) = self._analyse(
            {"main.py": "if True print('no')" + NL, "ok.py": "x = 1" + NL}
        )
        self.assertEqual(status.state, "degraded")
        record = next(item for item in status.records if item.record_id == "main.py")
        self.assertEqual(record.state, "parse-error")
        self.assertIn("SyntaxError", record.detail)
        self.assertFalse(any(item.path == "main.py" for item in findings))

    def test_unused_import_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "import os" + NL + "value = 1" + NL}
        )
        self.assertTrue(any(item.symbol == "os@1" for item in findings))

    def test_loaded_import_is_retained(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "import os" + NL + "value = os.name" + NL}
        )
        self.assertFalse(any(item.symbol == "os@1" for item in findings))

    def test_unused_local_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "def f():" + NL + "    spare = 1" + NL + "    return 2" + NL}
        )
        self.assertTrue(any(item.symbol == "f.spare@2" for item in findings))

    def test_loaded_local_is_retained(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "def f():" + NL + "    kept = 1" + NL + "    return kept" + NL}
        )
        self.assertFalse(any(item.symbol == "f.kept@2" for item in findings))

    def test_statement_after_return_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "def f():" + NL + "    return 1" + NL + "    spare()" + NL}
        )
        self.assertTrue(any(item.symbol == "line:3:unreachable" for item in findings))

    def test_statement_before_return_is_not_unreachable(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "def f():" + NL + "    kept()" + NL + "    return 1" + NL}
        )
        self.assertFalse(any(item.symbol == "line:2:unreachable" for item in findings))

    def test_literal_constant_branch_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "if False:" + NL + "    spare()" + NL}
        )
        self.assertTrue(any(item.symbol == "line:1:constant-false" for item in findings))

    def test_computed_import_lowers_candidate_confidence(self):
        _universe, (status, findings) = self._analyse(
            {
                "main.py": (
                    "import os" + NL
                    + "import importlib" + NL
                    + "name = 'pkg.mod'" + NL
                    + "importlib.import_module(name)" + NL
                )
            }
        )
        record = status.records[0]
        self.assertIn("computed-import", record.detail)
        candidate = next(item for item in findings if item.symbol == "os@1")
        self.assertEqual(candidate.confidence, "low")

    def test_literal_import_edge_reaches_the_module(self):
        _universe, (_status, findings) = self._analyse(
            {
                "main.py": "import live" + NL + "if __name__ == '__main__':" + NL + "    print(live.value)" + NL,
                "live.py": "value = 1" + NL,
            }
        )
        self.assertFalse(any(item.path == "live.py" and item.symbol == "<module>" for item in findings))

    def test_unreachable_import_graph_module_is_low_confidence(self):
        _universe, (_status, findings) = self._analyse(
            {
                "main.py": "if __name__ == '__main__':" + NL + "    print('entry')" + NL,
                "orphan.py": "value = 1" + NL,
            }
        )
        candidate = next(item for item in findings if item.path == "orphan.py" and item.symbol == "<module>")
        self.assertEqual(candidate.confidence, "low")

    def test_decorator_registration_retains_the_definition(self):
        source = "@registry" + NL + "def retained():" + NL + "    return 1" + NL
        build_repository(self.root, files={"main.py": source})
        snapshot = dead_code.parse_python_snapshot(self.root, dead_code.discover(self.root))
        item = snapshot.files[0]
        self.assertIn("retained", item.retained_names)
        self.assertNotIn(("retained", 3), list(dead_code._function_targets(item)))

    def test_dynamic_registration_argument_retains_the_definition(self):
        source = "def retained():" + NL + "    return 1" + NL + "register(retained)" + NL
        build_repository(self.root, files={"main.py": source})
        item = dead_code.parse_python_snapshot(self.root, dead_code.discover(self.root)).files[0]
        self.assertIn("retained", item.retained_names)

    def test_literal_all_retains_exported_import(self):
        _universe, (_status, findings) = self._analyse(
            {"main.py": "from pkg import retained" + NL + "__all__ = ['retained']" + NL}
        )
        self.assertFalse(any(item.symbol == "retained@1" for item in findings))

    def test_computed_getattr_is_a_visible_dynamic_boundary(self):
        _universe, (status, _findings) = self._analyse(
            {"main.py": "name = 'x'" + NL + "value = getattr(target, name)" + NL}
        )
        self.assertIn("computed-getattr", status.records[0].detail)

    def test_main_guard_seeds_the_cli_module(self):
        build_repository(
            self.root,
            files={"cli.py": "if __name__ == '__main__':" + NL + "    main()" + NL},
        )
        snapshot = dead_code.parse_python_snapshot(self.root, dead_code.discover(self.root))
        self.assertIn("cli.py", snapshot.entry_paths)
        self.assertIn("main", snapshot.files[0].retained_names)

    def test_test_fixture_definitions_are_retained(self):
        build_repository(
            self.root,
            files={"tests/fixtures/sample.py": "def helper():" + NL + "    return 1" + NL},
        )
        item = dead_code.parse_python_snapshot(self.root, dead_code.discover(self.root)).files[0]
        self.assertIn("helper", item.retained_names)

    def test_analysis_never_imports_the_parsed_module(self):
        marker = self.root.parent / (self.root.name + "-executed")
        source = f"from pathlib import Path{NL}Path({str(marker)!r}).write_text('bad'){NL}"
        self._analyse({"hostile.py": source})
        self.assertFalse(marker.exists())

    def test_aggregate_python_limit_is_visible_as_skipped(self):
        build_repository(self.root, files={"a.py": "x = 1" + NL, "b.py": "y = 2" + NL})
        universe = dead_code.discover(self.root)
        with mock.patch.object(dead_code, "MAX_PYTHON_TOTAL_BYTES", 1):
            snapshot = dead_code.parse_python_snapshot(self.root, universe)
        self.assertTrue(snapshot.degraded)
        self.assertTrue(any(item.state == "skipped" for item in snapshot.records))

    def test_global_assignment_is_not_reported_as_an_unused_local(self):
        _universe, (_status, findings) = self._analyse(
            {
                "main.py": (
                    "def configure():" + NL
                    + "    global setting" + NL
                    + "    setting = 1" + NL
                )
            }
        )
        self.assertFalse(any(item.symbol == "configure.setting@3" for item in findings))

    def test_nested_assignment_is_not_attributed_to_the_enclosing_function(self):
        _universe, (_status, findings) = self._analyse(
            {
                "main.py": (
                    "def outer():" + NL
                    + "    def inner():" + NL
                    + "        nested = 1" + NL
                    + "    return inner" + NL
                )
            }
        )
        self.assertFalse(any(item.symbol == "outer.nested@3" for item in findings))

    def test_comprehension_target_is_not_reported_as_a_function_local(self):
        _universe, (_status, findings) = self._analyse(
            {
                "main.py": (
                    "def values(items):" + NL
                    + "    return [1 for item in items]" + NL
                )
            }
        )
        self.assertFalse(any(item.symbol == "values.item@2" for item in findings))


class RepositoryAnalyserTests(TemporaryRepositoryTestCase):
    @staticmethod
    def _check_map(*, checks=None, scopes=None):
        return json.dumps(
            {
                "schema": "wildcat.check-map.v1",
                "checks": {} if checks is None else checks,
                "groups": {},
                "scopes": {} if scopes is None else scopes,
            },
            sort_keys=True,
        ) + NL

    def _analyse(self, files):
        build_repository(self.root, files=files)
        universe = dead_code.discover(self.root)
        return universe, dead_code.analyse_repository(self.root, universe)

    @staticmethod
    def _family_findings(findings, family):
        return [item for item in findings if item.symbol and item.symbol.startswith(f"{family}:")]

    def test_unreferenced_fixture_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"tests/fixtures/orphan.json": "{}" + NL, "README.md": "root" + NL}
        )
        self.assertEqual(
            [item.path for item in self._family_findings(findings, "fixture")],
            ["tests/fixtures/orphan.json"],
        )

    def test_literal_fixture_reference_retains_it(self):
        _universe, (_status, findings) = self._analyse(
            {
                "tests/fixtures/live.json": "{}" + NL,
                "tests/test_live.py": "FIXTURE = 'tests/fixtures/live.json'" + NL,
            }
        )
        self.assertFalse(self._family_findings(findings, "fixture"))

    def test_unreferenced_schema_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"schemas/orphan.schema.json": "{}" + NL, "README.md": "root" + NL}
        )
        self.assertEqual(
            [item.path for item in self._family_findings(findings, "schema")],
            ["schemas/orphan.schema.json"],
        )

    def test_markdown_schema_link_retains_it(self):
        _universe, (_status, findings) = self._analyse(
            {
                "schemas/live.schema.json": "{}" + NL,
                "README.md": "[schema](schemas/live.schema.json)" + NL,
            }
        )
        self.assertFalse(self._family_findings(findings, "schema"))

    def test_unreferenced_document_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"docs/orphan.md": "# orphan" + NL, "README.md": "root" + NL}
        )
        self.assertEqual(
            [item.path for item in self._family_findings(findings, "document")],
            ["docs/orphan.md"],
        )

    def test_markdown_document_link_retains_it(self):
        _universe, (_status, findings) = self._analyse(
            {
                "docs/live.md": "# live" + NL,
                "README.md": "[live](docs/live.md)" + NL,
            }
        )
        self.assertFalse(self._family_findings(findings, "document"))

    def test_unreferenced_cli_target_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"scripts/orphan.py": "print('orphan')" + NL, "README.md": "root" + NL}
        )
        self.assertEqual(
            [item.path for item in self._family_findings(findings, "cli")],
            ["scripts/orphan.py"],
        )

    def test_check_map_cli_declaration_retains_target(self):
        check_map = self._check_map(
            checks={"live": {"argv": ["python3", "scripts/live.py"]}},
            scopes={"root": {"checks": ["live"]}},
        )
        _universe, (_status, findings) = self._analyse(
            {"scripts/live.py": "print('live')" + NL, "tests/check-map-v1.json": check_map}
        )
        self.assertFalse(self._family_findings(findings, "cli"))

    def test_unreferenced_generated_copy_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {
                "copies/law.md": "<!-- canonical=PROMISE_MACHINE.md; copies=generated -->" + NL,
                "PROMISE_MACHINE.md": "law" + NL,
            }
        )
        self.assertEqual(
            [item.path for item in self._family_findings(findings, "generated-copy")],
            ["copies/law.md"],
        )

    def test_canonical_generated_copy_reference_retains_it(self):
        _universe, (_status, findings) = self._analyse(
            {
                "copies/law.md": "<!-- canonical=PROMISE_MACHINE.md; copies=generated -->" + NL,
                "PROMISE_MACHINE.md": "[copy](copies/law.md)" + NL,
            }
        )
        self.assertFalse(self._family_findings(findings, "generated-copy"))

    def test_unreferenced_router_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {
                ".agents/skills/orphan/SKILL.md": "---" + NL + "name: orphan" + NL + "---" + NL,
                "README.md": "root" + NL,
            }
        )
        self.assertEqual(
            [item.path for item in self._family_findings(findings, "router")],
            [".agents/skills/orphan/SKILL.md"],
        )

    def test_portable_promise_machine_router_is_an_external_root(self):
        _universe, (_status, findings) = self._analyse(
            {
                ".agents/skills/promise-machine/SKILL.md": "---" + NL + "name: promise-machine" + NL + "---" + NL,
                "README.md": "root" + NL,
            }
        )
        self.assertFalse(self._family_findings(findings, "router"))

    def test_unreferenced_manifest_is_reported(self):
        _universe, (_status, findings) = self._analyse(
            {"orphan/plugin.json": "{}" + NL, "README.md": "root" + NL}
        )
        self.assertEqual(
            [item.path for item in self._family_findings(findings, "manifest")],
            ["orphan/plugin.json"],
        )

    def test_host_manifest_is_an_external_root(self):
        _universe, (_status, findings) = self._analyse(
            {".codex-plugin/plugin.json": "{}" + NL, "README.md": "root" + NL}
        )
        self.assertFalse(self._family_findings(findings, "manifest"))

    def test_unscoped_check_map_object_is_reported(self):
        check_map = self._check_map(
            checks={"orphan": {"argv": ["python3", "-V"]}},
            scopes={"root": {"checks": []}},
        )
        _universe, (_status, findings) = self._analyse(
            {"tests/check-map-v1.json": check_map, "README.md": "root" + NL}
        )
        self.assertEqual(
            [item.symbol for item in self._family_findings(findings, "check-map")],
            ["check-map:check:orphan"],
        )

    def test_scoped_check_map_object_is_retained(self):
        check_map = self._check_map(
            checks={"live": {"argv": ["python3", "-V"]}},
            scopes={"root": {"checks": ["live"]}},
        )
        _universe, (_status, findings) = self._analyse(
            {"tests/check-map-v1.json": check_map, "README.md": "root" + NL}
        )
        self.assertFalse(self._family_findings(findings, "check-map"))

    def test_computed_reference_lowers_confidence_and_names_boundary(self):
        _universe, (_status, findings) = self._analyse(
            {
                "tests/fixtures/orphan.json": "{}" + NL,
                "tests/test_dynamic.py": "target = Path('tests/fixtures') / name" + NL,
            }
        )
        candidate = self._family_findings(findings, "fixture")[0]
        self.assertEqual(candidate.confidence, "low")
        self.assertIn("computed-path", candidate.false_positive_boundary)
        self.assertIn("tests/test_dynamic.py", candidate.false_positive_boundary)

    def test_family_record_names_parsed_edge_set_and_computed_boundary_count(self):
        _universe, (status, _findings) = self._analyse(
            {
                "tests/fixtures/live.json": "{}" + NL,
                "tests/test_live.py": "FIXTURE = 'tests/fixtures/live.json'" + NL,
                "tests/test_dynamic.py": "target = Path('tests/fixtures') / name" + NL,
            }
        )
        record = next(item for item in status.records if item.record_id == "fixture")
        self.assertRegex(record.detail, r"edge_set=sha256:[0-9a-f]{64}")
        self.assertIn("computed_boundaries=1", record.detail)
        self.assertGreaterEqual(record.evidence_count, 1)

    def test_f_string_reference_is_a_named_dynamic_boundary(self):
        _universe, (_status, findings) = self._analyse(
            {
                "tests/fixtures/orphan.json": "{}" + NL,
                "tests/test_dynamic.py": "target = f'tests/fixtures/{name}.json'" + NL,
            }
        )
        candidate = self._family_findings(findings, "fixture")[0]
        self.assertEqual(candidate.confidence, "low")
        self.assertIn("computed-path:f-string", candidate.false_positive_boundary)

    def test_malformed_check_map_degrades_only_its_family(self):
        _universe, (status, findings) = self._analyse(
            {"tests/check-map-v1.json": "{not json" + NL, "README.md": "root" + NL}
        )
        self.assertEqual(status.state, "degraded")
        record = next(item for item in status.records if item.record_id == "check-map")
        self.assertEqual(record.state, "parse-error")
        self.assertIsNotNone(record.reason)
        self.assertFalse(self._family_findings(findings, "check-map"))

    def test_empty_object_discovery_is_a_visible_zero_not_a_clean_claim(self):
        _universe, (status, findings) = self._analyse({"a.txt": "plain" + NL})
        self.assertEqual(status.state, "ran")
        self.assertEqual(findings, ())
        self.assertEqual(len(status.records), len(dead_code.REPOSITORY_FAMILIES))
        self.assertTrue(all(item.evidence_count == 0 for item in status.records))

    def test_unreadable_referrer_degrades_every_family_and_suppresses_candidates(self):
        build_repository(
            self.root,
            files={
                "tests/fixtures/orphan.json": "{}" + NL,
                "tests/test_large.py": "x" * 128 + NL,
            },
        )
        universe = dead_code.discover(self.root)
        with mock.patch.object(dead_code, "MAX_REPOSITORY_FILE_BYTES", 16):
            status, findings = dead_code.analyse_repository(self.root, universe)
        self.assertEqual(status.state, "degraded")
        self.assertEqual(findings, ())
        self.assertTrue(all(record.state == "parse-error" for record in status.records))
        self.assertTrue(all(record.reason for record in status.records))

    def test_repository_finding_survives_report_rendering(self):
        universe, (status, findings) = self._analyse(
            {"docs/orphan.md": "# orphan" + NL, "README.md": "root" + NL}
        )
        report = dead_code.Report(universe, (status,), findings)
        dead_code.validate_report(report)
        document = json.loads(dead_code.render_json(report))
        self.assertEqual(document["findings"][0]["id"], findings[0].identity)
        self.assertIn(findings[0].identity, dead_code.render_text(report))


class SolidityAnalyserTests(TemporaryRepositoryTestCase):
    @staticmethod
    def _slither_document(detectors=None):
        return json.dumps(
            {
                "success": True,
                "error": None,
                "results": {"detectors": [] if detectors is None else detectors},
            }
        ).encode()

    @staticmethod
    def _forge_summary(percent="100.00", covered="1", total="1"):
        metrics = f"{percent}% ({covered}/{total})"
        return (
            "| File | % Lines | % Statements | % Branches | % Funcs |" + NL
            + "|--------------+-----------+--------------+------------+---------|" + NL
            + f"| src/Dead.sol | {metrics} | {metrics} | {metrics} | {metrics} |" + NL
            + "|--------------+-----------+--------------+------------+---------|" + NL
            + f"| Total | {metrics} | {metrics} | {metrics} | {metrics} |" + NL
        ).encode()

    def _project(self, prefix=""):
        stem = f"{prefix}/" if prefix else ""
        return {
            f"{stem}foundry.toml": "[profile.default]" + NL + "src = 'src'" + NL,
            f"{stem}src/Dead.sol": "pragma solidity ^0.8.20; contract Dead { uint256 value; }" + NL,
        }

    def _universe(self, files=None):
        build_repository(self.root, files=self._project() if files is None else files)
        return dead_code.discover(self.root)

    def _successful_runner(self, calls, *, detectors=None, forge_summary=None):
        original_run_process = dead_code.run_process
        slither = self._slither_document(detectors)
        forge = self._forge_summary() if forge_summary is None else forge_summary

        def run(argv, **kwargs):
            calls.append((tuple(argv), kwargs["cwd"]))
            if argv[0] == "git":
                return original_run_process(argv, **kwargs)
            if argv == ["slither", "--version"]:
                return b"0.11.4\n", b"", 0
            if argv == ["forge", "--version"]:
                return b"forge 1.7.1\n", b"", 0
            if argv == ["slither", ".", "--detect", "dead-code,unused-state", "--json", "-"]:
                return slither, b"", 0
            if argv == ["forge", "coverage", "--report", "summary"]:
                return forge, b"", 0
            self.fail(f"unexpected argv: {argv!r}")

        return run

    def test_multiple_foundry_projects_are_discovered_from_tracked_configs(self):
        files = {**self._project("one"), **self._project("two")}
        universe = self._universe(files)
        calls = []
        with mock.patch.object(dead_code, "run_process", side_effect=self._successful_runner(calls)):
            status, _findings = dead_code.analyse_solidity(self.root, universe)
        projects = {item.record_id.split(":", 1)[0] for item in status.records}
        self.assertEqual(projects, {"one", "two"})

    def test_absent_slither_is_degraded_not_zero_findings(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[0] == "slither":
                raise dead_code.Refusal("slither is not available on PATH")
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(status.state, "degraded")
        slither = next(item for item in status.records if item.record_id.endswith(":slither"))
        self.assertEqual(slither.state, "unavailable")
        self.assertEqual(findings, ())

    def test_absent_forge_is_degraded_not_zero_findings(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[0] == "forge":
                raise dead_code.Refusal("forge is not available on PATH")
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(status.state, "degraded")
        forge = next(item for item in status.records if item.record_id.endswith(":forge"))
        self.assertEqual(forge.state, "unavailable")
        self.assertEqual(findings, ())

    def test_both_tools_absent_is_not_available(self):
        universe = self._universe()
        with mock.patch.object(
            dead_code,
            "run_process",
            side_effect=dead_code.Refusal("tool is not available on PATH"),
        ):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(status.state, "not-available")
        self.assertEqual(findings, ())

    def test_non_zero_tool_exit_degrades_project(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["slither", "."]:
                return b"", b"compile failed", 1
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(status.state, "degraded")
        self.assertEqual(findings, ())
        self.assertIn("exit 1", next(item for item in status.records if item.record_id.endswith(":slither")).reason)

    def test_non_zero_tool_stdout_preserves_json_failure_reason(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["slither", "."]:
                return b'{"success":false,"error":"compiler root cause"}', b"warning", 255
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, _findings = dead_code.analyse_solidity(self.root, universe)
        record = next(item for item in status.records if item.record_id.endswith(":slither"))
        self.assertIn("compiler root cause", record.reason)

    def test_non_zero_slither_success_keeps_positive_detector_evidence(self):
        universe = self._universe()
        detector = {
            "check": "dead-code",
            "confidence": "Medium",
            "elements": [
                {
                    "type": "function",
                    "name": "spare",
                    "source_mapping": {"filename_relative": "src/Dead.sol", "lines": [1]},
                }
            ],
        }
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["slither", "."]:
                return self._slither_document([detector]), b"warning", 255
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        record = next(item for item in status.records if item.record_id.endswith(":slither"))
        self.assertEqual(status.state, "degraded")
        self.assertEqual(record.state, "failed")
        self.assertEqual(record.evidence_count, 1)
        self.assertTrue(any("dead-code" in item.evidence for item in findings))

    def test_long_tool_stderr_preserves_the_terminal_failure_reason(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["slither", "."]:
                return b"", b"warning\n" * 100 + b"terminal root cause", 1
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, _findings = dead_code.analyse_solidity(self.root, universe)
        record = next(item for item in status.records if item.record_id.endswith(":slither"))
        self.assertIn("terminal root cause", record.reason)

    def test_tool_timeout_degrades_project(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["slither", "."]:
                raise dead_code.Refusal("slither timed out after 600s")
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, _findings = dead_code.analyse_solidity(self.root, universe)
        record = next(item for item in status.records if item.record_id.endswith(":slither"))
        self.assertEqual(record.state, "failed")
        self.assertIn("timed out", record.reason)

    def test_oversized_tool_output_degrades_project(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["forge", "coverage"]:
                raise dead_code.Refusal("forge output exceeded 1024 bytes")
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, _findings = dead_code.analyse_solidity(self.root, universe)
        record = next(item for item in status.records if item.record_id.endswith(":forge"))
        self.assertEqual(record.state, "failed")
        self.assertIn("exceeded", record.reason)

    def test_malformed_slither_json_degrades_without_absence_findings(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["slither", "."]:
                return b"not-json", b"", 0
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(status.state, "degraded")
        self.assertEqual(findings, ())
        self.assertEqual(
            next(item for item in status.records if item.record_id.endswith(":slither")).state,
            "parse-error",
        )

    def test_successful_slither_result_without_detector_key_is_empty_evidence(self):
        universe = self._universe()
        payload = json.dumps(
            {"success": True, "error": None, "results": {}}
        ).encode()
        findings, evidence_count = dead_code._slither_findings(
            payload,
            project=".",
            universe=universe,
        )
        self.assertEqual(findings, ())
        self.assertEqual(evidence_count, 0)

    def test_fixed_argv_and_project_cwd_are_used(self):
        universe = self._universe()
        calls = []
        with mock.patch.object(dead_code, "run_process", side_effect=self._successful_runner(calls)):
            dead_code.analyse_solidity(self.root, universe)
        expected = {
            ("slither", ".", "--detect", "dead-code,unused-state", "--json", "-"),
            ("forge", "coverage", "--report", "summary"),
        }
        analysis_calls = [(argv, cwd) for argv, cwd in calls if argv in expected]
        self.assertEqual({argv for argv, _cwd in analysis_calls}, expected)
        for _argv, cwd in analysis_calls:
            self.assertTrue(cwd.is_absolute())
            self.assertFalse(cwd.is_relative_to(self.root))
            self.assertEqual(cwd.name, "repository")

    def test_foundry_outputs_are_confined_outside_the_repository(self):
        universe = self._universe()
        environments = []
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] in (["slither", "."], ["forge", "coverage"]):
                environments.append(kwargs.get("env"))
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(len(environments), 2)
        for environment in environments:
            self.assertIsNotNone(environment)
            for name in ("FOUNDRY_OUT", "FOUNDRY_CACHE_PATH", "FOUNDRY_BROADCAST"):
                target = Path(environment[name])
                self.assertTrue(target.is_absolute())
                self.assertFalse(target.is_relative_to(self.root))

    def test_tool_execution_cannot_mutate_the_live_project(self):
        universe = self._universe()
        source = self.root / "src" / "Dead.sol"
        before = source.read_bytes()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["forge", "coverage"]:
                (kwargs["cwd"] / "src" / "Dead.sol").write_text(
                    "mutated by project code" + NL,
                    encoding="utf-8",
                )
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(source.read_bytes(), before)

    def test_disposable_project_has_a_conventional_foundry_output_directory(self):
        universe = self._universe()
        successful = self._successful_runner([])

        def run(argv, **kwargs):
            if argv[:2] == ["forge", "coverage"]:
                (kwargs["cwd"] / "out" / "findings.test.json").write_text(
                    "disposable evidence" + NL,
                    encoding="utf-8",
                )
            return successful(argv, **kwargs)

        with mock.patch.object(dead_code, "run_process", side_effect=run):
            status, _findings = dead_code.analyse_solidity(self.root, universe)
        forge = next(item for item in status.records if item.record_id.endswith(":forge"))
        self.assertEqual(forge.state, "passed")
        self.assertFalse((self.root / "out").exists())

    def test_slither_detector_maps_to_project_attributed_finding(self):
        universe = self._universe()
        detector = {
            "check": "unused-state",
            "confidence": "High",
            "elements": [
                {
                    "type": "variable",
                    "name": "value",
                    "source_mapping": {"filename_relative": "src/Dead.sol", "lines": [1]},
                }
            ],
        }
        with mock.patch.object(
            dead_code,
            "run_process",
            side_effect=self._successful_runner([], detectors=[detector]),
        ):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        self.assertEqual(status.state, "ran")
        candidate = next(item for item in findings if "unused-state" in item.evidence)
        self.assertEqual(candidate.path, "src/Dead.sol")
        self.assertEqual(candidate.symbol, "unused-state:variable:value@1")
        self.assertEqual(candidate.confidence, "high")

    def test_uncovered_forge_summary_row_maps_to_low_confidence_finding(self):
        universe = self._universe()
        with mock.patch.object(
            dead_code,
            "run_process",
            side_effect=self._successful_runner(
                [], forge_summary=self._forge_summary("0.00", "0", "1")
            ),
        ):
            _status, findings = dead_code.analyse_solidity(self.root, universe)
        candidate = next(item for item in findings if item.symbol and item.symbol.startswith("forge-coverage:"))
        self.assertEqual(candidate.path, "src/Dead.sol")
        self.assertEqual(candidate.confidence, "low")

    def test_partially_malformed_forge_table_refuses_all_rows(self):
        files = {
            **self._project(),
            "src/Other.sol": "pragma solidity ^0.8.20; contract Other {}" + NL,
        }
        universe = self._universe(files)
        payload = self._forge_summary("0.00", "0", "1").replace(
            b"| Total",
            b"| src/Other.sol | malformed | malformed | malformed | malformed |\n| Total",
            1,
        )
        with self.assertRaisesRegex(dead_code.Refusal, "malformed"):
            dead_code._forge_findings(payload, project=".", universe=universe)

    def test_real_forge_summary_isolated_from_other_pipe_tables(self):
        universe = self._universe()
        payload = (
            "| Contract | Selector | Calls | Reverts | Discards |" + NL
            + "| Sound | advance | 1 | 0 | 0 |" + NL
            + "|----------+----------+-------+---------+----------|" + NL
            + "| File | % Lines | % Statements | % Branches | % Funcs |" + NL
            + "|----------+-----------+--------------+------------+---------|" + NL
            + "| src/Dead.sol | 0.00% (0/1) | 0.00% (0/1) | 0.00% (0/1) | 0.00% (0/1) |" + NL
            + "|----------+-----------+--------------+------------+---------|" + NL
            + "| Total | 0.00% (0/1) | 0.00% (0/1) | 0.00% (0/1) | 0.00% (0/1) |" + NL
        ).encode()
        findings, evidence_count = dead_code._forge_findings(
            payload,
            project=".",
            universe=universe,
        )
        self.assertEqual(evidence_count, 1)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].path, "src/Dead.sol")

    def test_solidity_finding_survives_report_rendering(self):
        universe = self._universe()
        detector = {
            "check": "dead-code",
            "confidence": "Medium",
            "elements": [
                {
                    "type": "function",
                    "name": "spare",
                    "source_mapping": {"filename_relative": "src/Dead.sol", "lines": [1]},
                }
            ],
        }
        with mock.patch.object(
            dead_code,
            "run_process",
            side_effect=self._successful_runner([], detectors=[detector]),
        ):
            status, findings = dead_code.analyse_solidity(self.root, universe)
        report = dead_code.Report(universe, (status,), findings)
        dead_code.validate_report(report)
        document = json.loads(dead_code.render_json(report))
        self.assertEqual(document["findings"][0]["id"], findings[0].identity)


class CoverageAggregationTests(unittest.TestCase):
    def setUp(self):
        self.run_id = "a" * 32
        self.plan = {
            "schema": "wildcat.check-plan.v1",
            "map_digest": "b" * 64,
            "requested_scopes": ["dead-code"],
            "selected_checks": [
                {"id": "alpha", "argv": ["python3", "alpha.py"], "cwd": "."}
            ],
        }
        self.run = {
            **self.plan,
            "schema": "wildcat.check-run.v1",
            "outcome": "green",
            "checks": [
                {"check": "alpha", "status": "passed", "duration_seconds": 0.1}
            ],
        }
        self.universe = dead_code.Universe(
            commit="1" * 40,
            tree="2" * 40,
            identity="sha256:" + "3" * 64,
            tracked_count=1,
            analysed=("alpha.py",),
            excluded=(),
        )

    def _process(self, *, pid=10, marker="group-a", state="ran", argv=None):
        return {
            "schema": "dead-code-process-coverage/v1",
            "run": self.run_id,
            "process": {
                "pid": pid,
                "parent_pid": 1,
                "containment": marker,
                "argv": ["python3", "alpha.py"] if argv is None else argv,
                "cwd": "/snapshot",
            },
            "status": {"state": state, "truncated": False, "errors": []},
            "lines": [{"path": "alpha.py", "function": "f", "line": 2}],
            "branches": [
                {
                    "path": "alpha.py",
                    "function": "f",
                    "from_line": 2,
                    "to_line": 3,
                    "direction": "left",
                }
            ],
        }

    def _aggregate(self, documents, run=None):
        return dead_code.aggregate_coverage(
            self.plan,
            self.run if run is None else run,
            [(document, 100) for document in documents],
            self.universe,
        )

    def test_line_identity_survives_aggregation(self):
        report = self._aggregate([self._process()])
        self.assertEqual(report["processes"][0]["lines"][0]["line"], 2)

    def test_branch_identity_survives_aggregation(self):
        report = self._aggregate([self._process()])
        branch = report["processes"][0]["branches"][0]
        self.assertEqual((branch["from_line"], branch["to_line"]), (2, 3))

    def test_multiple_processes_are_attributed_to_one_check(self):
        report = self._aggregate([self._process(), self._process(pid=11)])
        self.assertEqual(report["checks"][0]["processes"], 2)
        self.assertEqual(report["checks"][0]["bytes"], 200)

    def test_aggregation_is_deterministic_across_input_order(self):
        first = self._process(pid=10)
        second = self._process(pid=11)
        self.assertEqual(
            self._aggregate([first, second]),
            self._aggregate([second, first]),
        )

    def test_public_coverage_does_not_retain_process_argv(self):
        root_process = self._process(pid=10)
        first_child = self._process(
            pid=11,
            argv=["python3", "child.py", "--token=first-secret"],
        )
        second_child = self._process(
            pid=11,
            argv=["python3", "child.py", "--token=second-secret"],
        )

        first = self._aggregate([root_process, first_child])
        second = self._aggregate([root_process, second_child])

        self.assertTrue(all("argv" not in process for process in first["processes"]))
        first_child_id = next(
            process["id"] for process in first["processes"] if process["pid"] == 11
        )
        second_child_id = next(
            process["id"] for process in second["processes"] if process["pid"] == 11
        )
        self.assertEqual(first_child_id, second_child_id)
        self.assertNotIn("first-secret", json.dumps(first))

    def test_failed_check_degrades_coverage(self):
        run = {
            **self.run,
            "outcome": "red",
            "checks": [{"check": "alpha", "status": "failed", "duration_seconds": 0.1}],
        }
        report = self._aggregate([self._process()], run)
        self.assertEqual(report["status"]["state"], "degraded")
        self.assertIn("ended failed", report["status"]["detail"])

    def test_not_started_check_degrades_coverage(self):
        run = {
            **self.run,
            "outcome": "red",
            "checks": [{"check": "alpha", "status": "not-started"}],
        }
        report = self._aggregate([], run)
        self.assertEqual(report["status"]["state"], "degraded")
        self.assertIn("no process record", report["status"]["detail"])

    def test_degraded_process_degrades_coverage(self):
        report = self._aggregate([self._process(state="degraded")])
        self.assertEqual(report["status"]["state"], "degraded")

    def test_unattributed_process_degrades_coverage(self):
        report = self._aggregate([self._process(argv=["python3", "other.py"])])
        self.assertEqual(report["status"]["state"], "degraded")
        self.assertEqual(report["processes"], [])

    def test_terminal_check_set_must_match_the_plan(self):
        run = {**self.run, "checks": []}
        with self.assertRaisesRegex(dead_code.Refusal, "do not match"):
            self._aggregate([self._process()], run)

    def test_duplicate_terminal_check_refuses_instead_of_overwriting(self):
        run = {**self.run, "checks": [*self.run["checks"], *self.run["checks"]]}
        with self.assertRaisesRegex(dead_code.Refusal, "repeated"):
            self._aggregate([self._process()], run)

    def test_contradictory_complete_process_status_degrades(self):
        process = self._process()
        process["status"]["truncated"] = True
        report = self._aggregate([process])
        self.assertEqual(report["status"]["state"], "degraded")

    def test_non_string_process_state_refuses_instead_of_crashing(self):
        process = self._process()
        process["status"]["state"] = []
        with self.assertRaisesRegex(dead_code.Refusal, "process status"):
            self._aggregate([process])

    def test_wrapper_recursion_is_detected_in_declared_argv(self):
        self.assertTrue(
            dead_code._coverage_recurses(
                ["python3", "scripts/dead_code.py", "coverage", "--scope", "dead-code"]
            )
        )

    def test_non_python_declared_command_is_not_coverable(self):
        self.assertFalse(dead_code._python_argv(["forge", "test"]))

    def test_plan_scope_mismatch_refuses(self):
        payload = json.dumps({**self.plan, "requested_scopes": ["other"]}).encode()
        with mock.patch.object(dead_code, "run_process", return_value=(payload, b"", 0)):
            with self.assertRaisesRegex(dead_code.Refusal, "not bound"):
                dead_code._runner_plan(ROOT, ("dead-code",))

    def test_coverage_environment_prepends_the_current_runtime(self):
        with mock.patch.dict(
            os.environ,
            {"PATH": "/usr/bin", "PYTHONPATH": "/fixture"},
            clear=True,
        ):
            environment = dead_code._coverage_environment(
                ROOT,
                ROOT / ".dead-code" / "processes",
                self.run_id,
            )
        self.assertEqual(
            environment["PATH"].split(os.pathsep)[0],
            str(Path(sys.executable).parent),
        )
        self.assertEqual(
            environment["PYTHONPATH"].split(os.pathsep)[0],
            str(ROOT / dead_code.MONITOR_DIRECTORY),
        )

    def test_run_map_digest_must_match_the_preflight_plan(self):
        run = {**self.run, "map_digest": "c" * 64}
        with self.assertRaisesRegex(dead_code.Refusal, "preflight plan"):
            self._aggregate([self._process()], run)


class MonitoringProbeTests(TemporaryRepositoryTestCase):
    def _free_tool_id(self):
        return next(identifier for identifier in range(6) if sys.monitoring.get_tool(identifier) is None)

    @staticmethod
    def _release_tool_id(identifier):
        if sys.monitoring.get_tool(identifier) is None:
            return
        sys.monitoring.set_events(identifier, 0)
        for event in (
            sys.monitoring.events.LINE,
            sys.monitoring.events.BRANCH_LEFT,
            sys.monitoring.events.BRANCH_RIGHT,
        ):
            sys.monitoring.register_callback(identifier, event, None)
        sys.monitoring.free_tool_id(identifier)

    def test_probe_restores_its_tool_id_and_event_mask(self):
        output = self.root / "records"
        output.mkdir()
        probe = dead_code_monitor.MonitoringProbe(output, ROOT, "a" * 32)
        probe.tool_id = self._free_tool_id()
        self.assertTrue(probe.start())
        self.assertNotEqual(sys.monitoring.get_events(probe.tool_id), 0)
        probe.close()
        self.assertIsNone(sys.monitoring.get_tool(probe.tool_id))
        self.assertEqual(sys.monitoring.get_events(probe.tool_id), 0)

    def test_probe_does_not_clobber_an_occupied_tool_id(self):
        identifier = self._free_tool_id()
        sys.monitoring.use_tool_id(identifier, "fixture-owner")
        self.addCleanup(sys.monitoring.free_tool_id, identifier)
        output = self.root / "records"
        output.mkdir()
        probe = dead_code_monitor.MonitoringProbe(output, ROOT, "a" * 32)
        probe.tool_id = identifier
        self.assertFalse(probe.start())
        probe.close()
        self.assertEqual(sys.monitoring.get_tool(identifier), "fixture-owner")

    def test_probe_does_not_clobber_a_reassigned_tool_id(self):
        identifier = self._free_tool_id()
        output = self.root / "records"
        output.mkdir()
        probe = dead_code_monitor.MonitoringProbe(output, ROOT, "a" * 32)
        probe.tool_id = identifier
        self.assertTrue(probe.start())
        self._release_tool_id(identifier)
        sys.monitoring.use_tool_id(identifier, "replacement-owner")
        self.addCleanup(self._release_tool_id, identifier)

        probe.close()

        self.assertEqual(sys.monitoring.get_tool(identifier), "replacement-owner")
        document = json.loads(next(output.iterdir()).read_text(encoding="utf-8"))
        self.assertIn("restore:ownership-changed", document["status"]["errors"])

    def test_probe_writes_named_lines_and_branches(self):
        output = self.root / "records"
        output.mkdir()
        probe = dead_code_monitor.MonitoringProbe(output, ROOT, "a" * 32)
        probe.tool_id = self._free_tool_id()
        probe.start()

        def exercised(value):
            if value:
                return "left"
            return "right"

        exercised(True)
        probe.close()
        documents = [json.loads(path.read_text(encoding="utf-8")) for path in output.iterdir()]
        self.assertEqual(len(documents), 1)
        self.assertTrue(any(item["function"].endswith("exercised") for item in documents[0]["lines"]))
        self.assertTrue(documents[0]["branches"])

    def test_event_cap_marks_the_process_record_truncated(self):
        output = self.root / "records"
        output.mkdir()
        probe = dead_code_monitor.MonitoringProbe(output, ROOT, "a" * 32)
        with mock.patch.object(dead_code_monitor, "MAX_EVENTS", 0):
            probe._remember_line(self.test_event_cap_marks_the_process_record_truncated.__code__, 1)
        self.assertTrue(probe.truncated)

    def test_line_callback_never_resolves_the_filesystem(self):
        output = self.root / "records"
        output.mkdir()
        probe = dead_code_monitor.MonitoringProbe(output, ROOT, "a" * 32)
        with mock.patch.object(Path, "resolve", side_effect=AssertionError("hot-path resolve")):
            result = probe._remember_line(
                self.test_line_callback_never_resolves_the_filesystem.__code__,
                1,
            )
        self.assertIs(result, sys.monitoring.DISABLE)


class CoverageContainmentTests(unittest.TestCase):
    @staticmethod
    def _stop(process):
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)

    def test_recovery_terminates_a_process_carrying_the_run_identity(self):
        run_id = "d" * 32
        environment = dict(os.environ)
        environment[dead_code.COVERAGE_ACTIVE_ENV] = run_id
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(30)"],
            env=environment,
            start_new_session=True,
        )
        self.addCleanup(self._stop, process)
        dead_code._terminate_coverage_processes(run_id)
        process.wait(timeout=5)
        self.assertIsNotNone(process.returncode)


class CoverageCommandTests(TemporaryRepositoryTestCase):
    def test_green_report_cannot_disagree_with_the_runner_exit(self):
        build_repository(self.root)
        universe = dead_code.discover(self.root)
        plan = {
            "schema": "wildcat.check-plan.v1",
            "map_digest": "a" * 64,
            "requested_scopes": ["dead-code"],
            "selected_checks": [
                {"id": "alpha", "argv": [sys.executable, "a.py"], "cwd": "."}
            ],
        }
        run = {
            **plan,
            "schema": "wildcat.check-run.v1",
            "outcome": "green",
            "checks": [
                {"check": "alpha", "status": "passed", "duration_seconds": 0.1}
            ],
        }

        def failed_runner(*_args, **_kwargs):
            target = self.root / ".dead-code" / "checks.json"
            target.write_text(json.dumps(run), encoding="utf-8")
            return b"", b"runner failed", 1

        arguments = dead_code.argparse.Namespace(
            directory=str(self.root),
            scope=["dead-code"],
            output=".dead-code/coverage.json",
        )
        with (
            mock.patch.object(dead_code, "repository_root", return_value=self.root),
            mock.patch.object(dead_code, "discover", return_value=universe),
            mock.patch.object(dead_code, "_runner_plan", return_value=plan),
            mock.patch.object(dead_code, "run_process", side_effect=failed_runner),
            mock.patch.object(dead_code, "_coverage_survivor_pids", return_value=[]),
            mock.patch.dict(os.environ, {dead_code.COVERAGE_ACTIVE_ENV: ""}),
        ):
            with self.assertRaisesRegex(dead_code.Refusal, "exit 1.*green"):
                dead_code.command_coverage(arguments)


class CoverageAnalyserTests(TemporaryRepositoryTestCase):
    SOURCE = (
        "def plain(flag):" + NL
        + "    if flag:" + NL
        + "        return 1" + NL
        + "    else:" + NL
        + "        return 2" + NL
    )

    def _fixture(self, *, state="ran", branches=None, lines=None, source=None):
        build_repository(
            self.root,
            files={"app.py": self.SOURCE if source is None else source},
        )
        universe = dead_code.discover(self.root)
        target = self.root / ".dead-code" / "coverage.json"
        target.parent.mkdir()
        document = {
            "schema": dead_code.COVERAGE_SCHEMA_ID,
            "tool": {"id": "sys.monitoring", "python": "3.14.6"},
            "tree": {
                "commit": universe.commit,
                "git_tree": universe.tree,
                "universe": universe.identity,
            },
            "plan": {
                "schema": "wildcat.check-plan.v1",
                "map_digest": "a" * 64,
                "requested_scopes": ["dead-code"],
                "selected_checks": ["alpha"],
            },
            "status": {"state": state, "detail": "fixture status"},
            "checks": [
                {
                    "id": "alpha",
                    "state": "passed" if state == "ran" else "failed",
                    "duration_seconds": 0.1,
                    "processes": 1,
                    "bytes": 100,
                }
            ],
            "processes": [
                {
                    "check": "alpha",
                    "bytes": 100,
                    "status": {"state": "ran", "truncated": False, "errors": []},
                    "lines": [] if lines is None else lines,
                    "branches": [] if branches is None else branches,
                }
            ],
        }
        target.write_text(json.dumps(document), encoding="utf-8")
        return universe, target, document

    def test_incomplete_coverage_emits_no_never_executed_findings(self):
        universe, _target, _document = self._fixture(state="degraded")
        status, findings = dead_code.analyse_coverage(
            self.root, universe, ".dead-code/coverage.json"
        )
        self.assertEqual(status.state, "degraded")
        self.assertEqual(findings, ())

    def test_observed_branch_is_not_reported_and_other_branch_is(self):
        branch = {
            "path": "app.py",
            "function": "plain",
            "from_line": 2,
            "to_line": 3,
            "direction": "left",
        }
        universe, _target, _document = self._fixture(
            branches=[branch], lines=[{"path": "app.py", "function": "plain", "line": 2}]
        )
        status, findings = dead_code.analyse_coverage(
            self.root, universe, ".dead-code/coverage.json"
        )
        self.assertEqual(status.state, "ran")
        symbols = {item.symbol for item in findings}
        self.assertNotIn("branch:2->3:body", symbols)
        self.assertIn("branch:2->5:else", symbols)

    def test_observed_function_skips_its_optimised_away_docstring(self):
        source = (
            "def documented():" + NL
            + "    \"\"\"metadata, not an executable body line\"\"\"" + NL
            + "    return 1" + NL
        )
        universe, _target, _document = self._fixture(
            source=source,
            lines=[{"path": "app.py", "function": "documented", "line": 3}],
        )

        status, findings = dead_code.analyse_coverage(
            self.root, universe, ".dead-code/coverage.json"
        )

        self.assertEqual(status.state, "ran")
        self.assertFalse(any(item.symbol.startswith("documented@") for item in findings))

    def test_coverage_tool_identity_is_required(self):
        universe, target, document = self._fixture()
        document["tool"]["id"] = "not-sys-monitoring"
        target.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(dead_code.Refusal, "sys.monitoring"):
            dead_code.analyse_coverage(
                self.root, universe, ".dead-code/coverage.json"
            )

    def test_coverage_plan_schema_is_required(self):
        universe, target, document = self._fixture()
        document["plan"]["schema"] = "unknown-plan"
        target.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(dead_code.Refusal, "check-plan"):
            dead_code.analyse_coverage(
                self.root, universe, ".dead-code/coverage.json"
            )

    def test_stale_coverage_identity_degrades_without_findings(self):
        universe, target, document = self._fixture()
        document["tree"]["commit"] = "f" * 40
        target.write_text(json.dumps(document), encoding="utf-8")
        status, findings = dead_code.analyse_coverage(
            self.root, universe, ".dead-code/coverage.json"
        )
        self.assertEqual(status.state, "degraded")
        self.assertEqual(findings, ())

    def test_missing_coverage_argument_refuses_by_name(self):
        build_repository(self.root, files={"app.py": self.SOURCE})
        with self.assertRaisesRegex(dead_code.Refusal, "requires --coverage"):
            dead_code.analyse_coverage(self.root, dead_code.discover(self.root), None)

    def test_claimed_complete_without_process_aggregate_degrades(self):
        universe, target, document = self._fixture()
        document["checks"][0]["processes"] = 1
        document["processes"] = []
        target.write_text(json.dumps(document), encoding="utf-8")
        status, findings = dead_code.analyse_coverage(
            self.root, universe, ".dead-code/coverage.json"
        )
        self.assertEqual(status.state, "degraded")
        self.assertEqual(findings, ())

    def test_malformed_line_event_refuses_instead_of_implying_absence(self):
        universe, target, document = self._fixture(
            lines=[{"path": "app.py", "function": "plain", "line": "two"}]
        )
        target.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(dead_code.Refusal, "line event"):
            dead_code.analyse_coverage(
                self.root, universe, ".dead-code/coverage.json"
            )

    def test_boolean_line_identity_refuses_instead_of_aliasing_line_one(self):
        universe, target, document = self._fixture(
            lines=[{"path": "app.py", "function": "plain", "line": True}]
        )
        target.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(dead_code.Refusal, "line event"):
            dead_code.analyse_coverage(
                self.root, universe, ".dead-code/coverage.json"
            )

    def test_non_string_branch_direction_refuses_instead_of_crashing(self):
        universe, target, document = self._fixture(
            branches=[
                {
                    "path": "app.py",
                    "function": "plain",
                    "from_line": 2,
                    "to_line": 3,
                    "direction": [],
                }
            ]
        )
        target.write_text(json.dumps(document), encoding="utf-8")
        with self.assertRaisesRegex(dead_code.Refusal, "branch event"):
            dead_code.analyse_coverage(
                self.root, universe, ".dead-code/coverage.json"
            )


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
            "analyserRecord",
            "finding",
        ):
            self.assertFalse(schema["$defs"][name]["additionalProperties"])
        record = dead_code.AnalyserRecord(
            "fixture",
            "family",
            "parsed",
            "fixture record",
            1,
            "repository-graph/1",
            2,
            3,
            None,
        ).as_dict()
        self.assertEqual(
            set(record),
            set(schema["$defs"]["analyserRecord"]["required"]),
        )

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
            "scripts/dead_code_monitoring",
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
        self.assertIn("/.dead-code/coverage.json", text)
        self.assertIn("/.dead-code/coverage-processes-*/", text)


if __name__ == "__main__":
    unittest.main()
