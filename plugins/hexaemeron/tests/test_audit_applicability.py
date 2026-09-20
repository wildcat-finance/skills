"""Exercise byte custody and inert routing over authored synthetic sources."""
import copy
from dataclasses import FrozenInstanceError
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "plugins/hexaemeron/skills/protasis/scripts/audit_applicability.py"
spec = importlib.util.spec_from_file_location("audit_applicability_tests_subject", SCRIPT)
app = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = app
spec.loader.exec_module(app)
COMMAND = "python3 tests/observed.py"
SOURCE = "## Synthetic audit\nStatus: open\nStatus: not checked\nStatus: repaired with limits\nStatus: open upstream\nλ witness\n".encode()


def fence(name, value):
    return "```" + name + "\n" + json.dumps(value, ensure_ascii=True) + "\n```\n\n"


class Fixture:
    """Only authored files and declarations; declared runners never execute."""
    def __init__(self, root, *, regression=True):
        self.root = root
        self.study = root / "study.md"
        self.runbook = root / "runbook.md"
        self.source = root / "audit/source.md"
        self.view = root / "audit/view.md"
        self.source.parent.mkdir(parents=True, exist_ok=True)
        self.source.write_bytes(SOURCE)
        self.view.write_text("Synopsis schema=fiat-audit-synopsis/v1 | source=audit/source.md | "
                             "source_sha256=" + app.digest(SOURCE) + " | h2_count=1\n")
        view = {"id": "audit", "path": "audit/view.md", "source_sha256": app.digest(SOURCE),
                "view_sha256": app.digest(self.view.read_bytes())}
        finding = {"id": "kf-local", "source_ref": "audit:local", "failure": "Synthetic wrong total",
                   "guard_paths": ["tests/guard.py"],
                   "test_command": "python3 tests/guard.py --case kf-local --report {report}",
                   "report_format": "unittest-json-v1", "report_file": ".elenchus/local.json",
                   "expected_guard_verdict": "guarded",
                   "green_command": "python3 tests/guard.py --case kf-local --report .elenchus/local-green.json",
                   "consuming_step": 1}
        self.inventory = {"schema": app.inventory.SCHEMA, "source_views": [view],
                          "findings": [finding] if regression else [],
                          "no_known_findings": None if regression else {
                              "source_views": [{k: view[k] for k in ("id", "source_sha256", "view_sha256")}],
                              "consuming_step": 1, "surveyor_assertion": "no-known-findings"}}
        self.criteria = {"schema": app.criteria.SCHEMA, "criteria": [
            {"id": "native", "claim": "Observe the synthetic boundary", "step": 1, "command": COMMAND}]}
        self.declaration = {"schema": app.SCHEMA, "source_views": copy.deepcopy([view]), "entries": []}
        for disposition, status in (("local-regression", "open"),
                                    ("integration-requirement", "not checked"),
                                    ("historical", "repaired with limits"),
                                    ("out-of-scope", "open upstream"), ("historical", None)):
            if disposition == "local-regression" and not regression:
                continue
            self.declaration["entries"].append({
                "id": disposition + ("-unknown" if status is None else ""), "source_ref": "audit:" + disposition,
                "source_span": {"start_byte": 0, "end_byte": len(SOURCE), "sha256": app.digest(SOURCE)},
                "source_status": status, "disposition": disposition, "rationale": "Synthetic review with its limits.",
                "finding_id": "kf-local" if disposition == "local-regression" else None,
                "criterion_id": "native" if disposition == "integration-requirement" else None,
                "tracking": ["https://github.com/wildcat-finance/skills/issues/1596"] if disposition == "out-of-scope" else []})
        self.runbook.write_text("## Step 1: Observe\n\n"
                                "**Goal.** A bounded fixture.\n**Entry.** Authored inputs.\n"
                                "**Exit.** Run `" + COMMAND + "`.\n"
                                "**Files.** Synthetic files.\n**Tests.** Fixture checks.\n**Disciplines.** phylax.\n" +
                                ("\nKnown-failure assignment: `kf-local` -> Step 1\n" if regression else ""))
        self.write()

    def write(self):
        self.study.write_text(fence("known-failure-inventory", self.inventory) +
                              fence("success-criteria", self.criteria) +
                              fence(app.FENCE_INFO, self.declaration))

    def load(self):
        return app.load_checked_applicability(self.study, self.runbook, self.root)

    def replace_source(self, data):
        self.source.write_bytes(data)
        self.view.write_text("Synopsis schema=fiat-audit-synopsis/v1 | source=audit/source.md | "
                             "source_sha256=" + app.digest(data) + " | h2_count=1\n")
        for views in (self.inventory["source_views"], self.declaration["source_views"]):
            views[0].update(source_sha256=app.digest(data), view_sha256=app.digest(self.view.read_bytes()))
        if self.inventory["no_known_findings"]:
            self.inventory["no_known_findings"]["source_views"] = [
                {k: row[k] for k in ("id", "source_sha256", "view_sha256")}
                for row in self.inventory["source_views"]]
        for row in self.declaration["entries"]:
            row["source_span"] = {"start_byte": 0, "end_byte": min(len(data), app.MAX_SPAN_BYTES),
                                  "sha256": app.digest(data[:app.MAX_SPAN_BYTES])}
            row["source_status"] = None
        self.write()


def maximum_fixture(root):
    """Build a valid simultaneous document, pair, row, file and aggregate limit.

    One source and one view reach 2 MiB; the other 62 files fill the exact
    16 MiB aggregate. There are 32 pairs, 128 rows and 64 KiB cited spans.
    The fixture is authored and is no assertion about a historical audit.
    """
    fixture = Fixture(root, regression=False)
    views = []
    total = 0
    # Header lengths are independent of digest content, which is fixed-width.
    headers = []
    for i in range(app.MAX_SOURCE_VIEWS):
        headers.append(("Synopsis schema=fiat-audit-synopsis/v1 | source=audit/source-" + str(i) +
                        ".md | source_sha256=" + "0" * 64 + " | h2_count=1\n").encode())
    view_sizes = [app.MAX_SOURCE_BYTES] + [len(header) for header in headers[1:]]
    remaining = app.MAX_AGGREGATE_BYTES - sum(view_sizes) - app.MAX_SOURCE_BYTES
    source_sizes = [app.MAX_SOURCE_BYTES] + [remaining // 31] * 30
    source_sizes.append(remaining - sum(source_sizes[1:]))
    for i, (source_size, view_size) in enumerate(zip(source_sizes, view_sizes)):
        data = b"s" * 1024 + b"a" * (source_size - 1024)
        source_path = "audit/source-" + str(i) + ".md"
        view_path = "audit/view-" + str(i) + ".md"
        (root / source_path).write_bytes(data)
        header = headers[i].replace(b"0" * 64, app.digest(data).encode())
        view = header + b"v" * (view_size - len(header))
        (root / view_path).write_bytes(view)
        total += len(data) + len(view)
        views.append({"id": "audit-" + str(i), "path": view_path,
                      "source_sha256": app.digest(data), "view_sha256": app.digest(view)})
    fixture.inventory["source_views"] = views
    fixture.source.unlink()
    fixture.view.unlink()
    fixture.inventory["no_known_findings"]["source_views"] = [
        {k: row[k] for k in ("id", "source_sha256", "view_sha256")} for row in views]
    fixture.declaration["source_views"] = copy.deepcopy(views)
    raw = (root / "audit/source-0.md").read_bytes()[:app.MAX_SPAN_BYTES]
    template = {"id": "row", "source_ref": "audit-0:budget", "source_span": {
        "start_byte": 0, "end_byte": len(raw), "sha256": app.digest(raw)},
        "source_status": "s" * 1024, "disposition": "historical",
        "rationale": "Synthetic budget input; no historical claim.",
        "finding_id": None, "criterion_id": None,
        "tracking": [f"https://github.com/o/r/issues/{n}" for n in range(1, 9)]}
    fixture.declaration["entries"] = [dict(template, id=f"row-{n}", source_status=None)
                                        for n in range(app.MAX_ENTRIES)]
    fixture.declaration["entries"][0].update(source_status="s" * 1024,
        rationale="r" * app.MAX_TEXT_BYTES, source_ref="audit-0:" + "d" * (app.MAX_TEXT_BYTES - 8))
    fixture.write()
    data = fixture.study.read_bytes()
    assert len(data) <= app.MAX_DOCUMENT_BYTES
    fixture.study.write_bytes(data + b" " * (app.MAX_DOCUMENT_BYTES - len(data)))
    assert total == app.MAX_AGGREGATE_BYTES
    return fixture


class ApplicabilityParserTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.fixture = Fixture(self.root)

    def assertClean(self):
        result = self.fixture.load()
        self.assertEqual(result.status, "clean", result.findings)
        return result

    def assertRefused(self, code=None):
        result = self.fixture.load()
        self.assertEqual(result.status, "refused")
        self.assertIsNone(result.capture)
        self.assertEqual(len(result.findings), 1)
        if code:
            self.assertEqual(result.findings[0].code, code)
        return result

    def test_all_dispositions_statuses_and_derived_routes(self):
        capture = self.assertClean().capture
        self.assertEqual(capture["entries"], self.fixture.declaration["entries"])
        self.assertEqual(capture["source_views"], self.fixture.inventory["source_views"])
        routes = capture["routes"]
        self.assertEqual([row["owner"] for row in routes], ["known-failure", "success-criteria", None, None, None])
        self.assertEqual(routes[0]["binding"], self.fixture.inventory["findings"][0])
        self.assertEqual(routes[1]["binding"]["command"], COMMAND)
        self.assertEqual(routes[1]["binding"]["step"], 1)
        self.assertIsNone(capture["entries"][-1]["source_status"])
        for row in routes:
            self.assertEqual(row["binding_sha256"], None if row["binding"] is None else app.digest(app.canonical_bytes(row["binding"])))

    def test_result_is_immutable_with_defensive_projection(self):
        result = self.assertClean()
        original = result.capture_bytes
        result.capture["entries"][0]["disposition"] = "historical"
        self.assertEqual(result.capture_bytes, original)
        self.assertEqual(result.capture["entries"][0]["disposition"], "local-regression")
        with self.assertRaises(FrozenInstanceError):
            result.status = "absent"

    def test_absence_allows_ordinary_prose_and_inline_marker(self):
        self.fixture.study.write_text("The `audit-applicability` declaration is optional.\n")
        self.assertEqual(self.fixture.load().status, "absent")

    def test_real_accepted_study_is_absent(self):
        docs = ROOT / "docs/native-guard-admission"
        self.assertEqual(app.load_checked_applicability(docs / "study.md", docs / "runbook.md", ROOT).status, "absent")

    def test_every_attempted_malformed_fence_refuses(self):
        original = self.fixture.study.read_text()
        for marker in (" ```audit-applicability", "    ```audit-applicability", "\t```audit-applicability",
                       "``audit-applicability", "~~audit-applicability", "``` audit-applicability",
                       "```audit-applicability extra", "```audit-applicabilityx", "```AUDIT-APPLICABILITY",
                       "> ```audit-applicability"):
            with self.subTest(marker=marker):
                self.fixture.study.write_text(original.replace("```audit-applicability", marker))
                self.assertRefused("A001")
        self.fixture.study.write_text(original[:original.rfind("```")])
        self.assertRefused("A001")

    def test_duplicate_nested_partial_and_unisolated_fences_refuse(self):
        declaration = fence(app.FENCE_INFO, self.fixture.declaration)
        cases = [declaration + declaration, "````markdown\n" + declaration + "````\n",
                 "prefix\n" + declaration, declaration.rstrip() + "\ntrailing\n"]
        for text in cases:
            with self.subTest(text=text[:20]):
                self.fixture.study.write_text(text)
                self.assertRefused("A001")

    def test_runbook_declaration_cannot_hide_as_absence(self):
        self.fixture.study.write_text("Absent.\n")
        self.fixture.runbook.write_text(fence(app.FENCE_INFO, self.fixture.declaration))
        self.assertRefused("A001")

    def test_indented_surrounding_fences_refuse_at_applicability_boundary(self):
        original = self.fixture.study.read_text()
        target = fence(app.FENCE_INFO, self.fixture.declaration)
        for indent in (" ", "  ", "   "):
            text = original.replace(target, indent + "````text\n\n" + target + indent + "````\n\n")
            self.fixture.study.write_text(text)
            self.assertRefused("A001")
            with self.assertRaises(app.Refusal):
                app._fence(text)

    def test_duplicate_keys_nonfinite_depth_and_invalid_json(self):
        original = self.fixture.study.read_text()
        for payload in ('{"schema":1,"schema":2}', '{"x":NaN}', '{"x":Infinity}',
                        '{"x":1e999}', '[' * 40 + '0' + ']' * 40, '{} trailing', '{'):
            self.fixture.study.write_text(original.split("```audit-applicability")[0] +
                                          "```audit-applicability\n" + payload + "\n```\n")
            self.assertRefused("A002")

    def test_unknown_schema_and_open_fields(self):
        for value in ([1], {"schema": "other"}, {**self.fixture.declaration, "extra": None}):
            self.fixture.study.write_text(fence(app.FENCE_INFO, value))
            self.assertRefused("A002")

    def test_inventory_is_required_even_for_empty_regressions(self):
        self.fixture.study.write_text(fence(app.FENCE_INFO, self.fixture.declaration))
        self.assertRefused("A003")

    def test_empty_inventory_claim_is_checked(self):
        self.fixture = Fixture(self.root, regression=False)
        self.assertClean()
        self.fixture.inventory["no_known_findings"] = None
        self.fixture.write()
        self.assertRefused("A003")

    def test_source_views_must_equal_complete_checked_set(self):
        original = copy.deepcopy(self.fixture.declaration["source_views"])
        for views in ([], original + [dict(original[0], id="extra", path="audit/other.md")],
                      [dict(original[0], source_sha256="0" * 64)], [dict(original[0], extra=True)]):
            self.fixture.declaration["source_views"] = views
            self.fixture.write()
            self.assertRefused("A004")

    def test_duplicate_ids_open_entries_and_conflicting_targets(self):
        original = copy.deepcopy(self.fixture.declaration["entries"])
        cases = [original + [original[0]], [{**original[0], "command": COMMAND}],
                 [{**original[0], "consuming_step": 1}], [{**original[0], "id": "UPPER"}],
                 [{**original[0], "rationale": ""}], [{**original[0], "source_ref": None}],
                 [{**original[2], "finding_id": "kf-local"}]]
        for rows in cases:
            self.fixture.declaration["entries"] = rows
            self.fixture.write()
            self.assertRefused("A005")

    def test_exact_source_prefix_and_nonempty_detail(self):
        row = self.fixture.declaration["entries"][0]
        for ref in ("audit-extra:local", "audi:local", "missing:local", "audit:", "audit: ", "audit"):
            row["source_ref"] = ref
            self.fixture.write()
            self.assertRefused("A006")
        row["source_ref"] = "audit:opaque:detail"
        self.fixture.write()
        self.assertClean()

    def test_opaque_detail_and_rationale_do_not_become_fence_markers(self):
        self.fixture.declaration["entries"][0].update(
            source_ref="audit:opaque ```audit-applicability locator",
            rationale="Discuss the ```audit-applicability spelling without declaring it.")
        self.fixture.write()
        self.assertClean()

    def test_non_markdown_line_separator_cannot_open_a_fence(self):
        original = self.fixture.study.read_text()
        for prefix in ("\u2028", "\u2029", "\v", "\f"):
            self.fixture.study.write_text(original.replace("```audit-applicability", prefix + "```audit-applicability"))
            self.assertRefused("A001")

    def test_missing_secure_read_primitives_refuses(self):
        with mock.patch.object(app.inventory, "_secure_read_primitives", return_value=False):
            self.assertRefused("A000")

    def test_span_shape_boolean_empty_outside_and_digest(self):
        original = self.fixture.declaration["entries"][0]["source_span"]
        for changes in ({"start_byte": True}, {"end_byte": True}, {"start_byte": -1},
                        {"end_byte": 0}, {"end_byte": len(SOURCE) + 1},
                        {"sha256": "0" * 64}, {"extra": 1}, {"start_byte": 1.0}):
            self.fixture.declaration["entries"][0]["source_span"] = {**original, **changes}
            self.fixture.write()
            self.assertRefused("A002" if type(changes.get("start_byte")) is float else "A006")

    def test_utf8_source_and_span_boundaries(self):
        index = SOURCE.index("λ".encode())
        for start, end in ((index + 1, len(SOURCE)), (0, index + 1)):
            raw = SOURCE[start:end]
            self.fixture.declaration["entries"][0].update(source_status=None, source_span={
                "start_byte": start, "end_byte": end, "sha256": app.digest(raw)})
            self.fixture.write()
            self.assertRefused("A006")
        self.fixture.replace_source(b"invalid\xff source")
        self.assertRefused("A006")

    def test_status_change_is_not_a_repair(self):
        self.fixture.declaration["entries"][0]["source_status"] = "closed"
        self.fixture.write()
        self.assertRefused("A006")

    def test_tracking_closed_urls_duplicates_and_count(self):
        row = self.fixture.declaration["entries"][0]
        for tracking in (["https://github.com/o/r/issues/1#comment"], ["http://github.com/o/r/issues/1"],
                         ["https://github.com/o/r/issues/0"], ["x", "x"], [None],
                         [f"https://github.com/o/r/issues/{i}" for i in range(1, 10)]):
            row["tracking"] = tracking
            self.fixture.write()
            self.assertRefused("A005")
        row["tracking"] = [f"https://github.com/o/r/issues/{i}" for i in range(1, 9)]
        self.fixture.write()
        self.assertClean()

    def test_every_regression_appears_exactly_once(self):
        original = copy.deepcopy(self.fixture.declaration["entries"])
        for rows in (original[1:], original + [dict(original[0], id="another")]):
            self.fixture.declaration["entries"] = rows
            self.fixture.write()
            self.assertRefused("A007")

    def test_regression_cannot_move_to_integration_or_unknown_finding(self):
        row = self.fixture.declaration["entries"][0]
        for changes in ({"finding_id": "kf-unknown"}, {"criterion_id": "native"},
                        {"disposition": "integration-requirement", "finding_id": None, "criterion_id": "native"}):
            original = copy.deepcopy(row)
            row.update(changes)
            self.fixture.write()
            self.assertRefused("A007")
            row.clear(); row.update(original)

    def test_unknown_criteria_and_conflicting_targets_refuse(self):
        row = self.fixture.declaration["entries"][1]
        for changes in ({"criterion_id": "unknown"}, {"finding_id": "kf-local"}):
            original = copy.deepcopy(row)
            row.update(changes)
            self.fixture.write()
            self.assertRefused("A008")
            row.clear(); row.update(original)

    def test_multiple_sources_can_share_one_exact_criterion(self):
        self.fixture.declaration["entries"].append(dict(self.fixture.declaration["entries"][1], id="second-requirement"))
        self.fixture.criteria["criteria"].append(dict(self.fixture.criteria["criteria"][0], id="ordinary"))
        self.fixture.write()
        capture = self.assertClean().capture
        self.assertEqual(capture["routes"][1]["binding"], capture["routes"][-1]["binding"])

    def test_changed_criterion_command_has_no_exit_join(self):
        self.fixture.criteria["criteria"][0]["command"] = "python3 other.py"
        self.fixture.write()
        self.assertRefused("A008")

    def test_protasis_cli_checks_applicability_without_running_the_exit(self):
        cli = "plugins/hexaemeron/tests/run_tests.py"
        target = self.root / cli
        target.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / cli, target)
        command = "python3 " + cli + " --jobs 8"
        self.fixture.criteria["criteria"][0]["command"] = command
        self.fixture.runbook.write_text(self.fixture.runbook.read_text().replace(COMMAND, command))
        self.fixture.write()
        argv = [sys.executable, str(SCRIPT.with_name("protasis.py")), str(self.fixture.runbook),
                "--gate-root", str(self.root), "--applicability", str(self.fixture.study), "--format", "json"]
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout), [])
        self.fixture.declaration["entries"][0]["source_status"] = "closed"
        self.fixture.write()
        result = subprocess.run(argv, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(json.loads(result.stdout)[0]["code"], "A006")

    def test_source_and_view_digest_drift(self):
        for path in (self.fixture.source, self.fixture.view):
            original = path.read_bytes()
            path.write_bytes(original + b"changed")
            self.assertRefused("A003")
            path.write_bytes(original)

    def test_no_declared_command_is_executed_or_file_written(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with mock.patch("subprocess.run", side_effect=AssertionError("command execution")), \
                mock.patch("subprocess.Popen", side_effect=AssertionError("process launch")):
            self.assertClean()
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_refusal_exposes_no_source_text(self):
        self.fixture.declaration["entries"][0]["source_status"] = "private-shaped-never-emit"
        self.fixture.write()
        found = self.assertRefused("A006").findings[0]
        self.assertNotIn("private-shaped", json.dumps(found.as_dict()))

    def test_text_and_status_exact_limits_and_one_over(self):
        row = self.fixture.declaration["entries"][0]
        for field in ("rationale", "source_ref"):
            row[field] = "x" * app.MAX_TEXT_BYTES if field == "rationale" else "audit:" + "x" * (app.MAX_TEXT_BYTES - 6)
            self.fixture.write()
            self.assertClean()
            row[field] += "x"
            self.fixture.write()
            self.assertRefused("A005")
            row[field] = "synthetic" if field == "rationale" else "audit:local"
        self.fixture.replace_source(b"s" * app.MAX_STATUS_BYTES)
        row["source_status"] = "s" * app.MAX_STATUS_BYTES
        self.fixture.write(); self.assertClean()
        row["source_status"] += "s"
        self.fixture.write(); self.assertRefused("A006")

    def test_entry_count_exact_limit_and_one_over(self):
        self.fixture = Fixture(self.root, regression=False)
        template = self.fixture.declaration["entries"][1]
        self.fixture.declaration["entries"] = [dict(template, id=f"row-{i}") for i in range(app.MAX_ENTRIES)]
        self.fixture.write(); self.assertClean()
        self.fixture.declaration["entries"].append(dict(template, id="one-over"))
        self.fixture.write(); self.assertRefused("A005")

    def test_span_exact_limit_and_one_over(self):
        self.fixture.replace_source(b"a" * (app.MAX_SPAN_BYTES + 1))
        self.assertClean()
        row = self.fixture.declaration["entries"][0]
        row["source_span"].update(end_byte=app.MAX_SPAN_BYTES + 1,
                                   sha256=app.digest(self.fixture.source.read_bytes()))
        self.fixture.write(); self.assertRefused("A006")

    def test_document_exact_limit_and_one_over(self):
        raw = self.fixture.study.read_bytes()
        self.fixture.study.write_bytes(raw + b" " * (app.MAX_DOCUMENT_BYTES - len(raw)))
        self.assertClean()
        with self.fixture.study.open("ab") as file:
            file.write(b" ")
        self.assertRefused("A000")


class ApplicabilityReaderTests(unittest.TestCase):
    setUp = ApplicabilityParserTests.setUp
    assertClean = ApplicabilityParserTests.assertClean
    assertRefused = ApplicabilityParserTests.assertRefused
    def test_leaf_and_ancestor_links_and_nonregular_files(self):
        for target in ("source", "view", "study"):
            path = getattr(self.fixture, target)
            saved = path.with_suffix(".saved")
            path.rename(saved)
            path.symlink_to(saved.name)
            self.assertRefused()
            path.unlink(); saved.rename(path)
        directory = self.root / "audit"
        directory.rename(self.root / "saved-audit")
        directory.symlink_to("saved-audit", target_is_directory=True)
        self.assertRefused("A003")
        directory.unlink(); (self.root / "saved-audit").rename(directory)
        self.fixture.source.unlink(); os.mkfifo(self.fixture.source)
        self.assertRefused("A003")
        self.fixture.source.unlink(); self.fixture.source.mkdir()
        self.assertRefused("A003")

    def test_hardlinks_refuse(self):
        os.link(self.fixture.source, self.root / "linked.md")
        self.assertRefused("A003")

    def test_portable_view_aliases_refuse(self):
        first = self.fixture.declaration["source_views"][0]
        self.fixture.declaration["source_views"].append(dict(first, id="alias", path="AUDIT/view.md"))
        self.fixture.write(); self.assertRefused("A004")

    def test_unsafe_source_paths_refuse(self):
        for path in ("../outside", "audit/../source.md", "audit\\source.md", "/tmp/source.md"):
            self.fixture.declaration["source_views"][0]["path"] = path
            self.fixture.write(); self.assertRefused("A004")

    def test_source_exact_limit_and_one_over(self):
        self.fixture.replace_source(b"a" * app.MAX_SOURCE_BYTES)
        self.assertClean()
        self.fixture.replace_source(b"a" * (app.MAX_SOURCE_BYTES + 1))
        self.assertRefused("A003")

    def test_replacement_between_checked_read_and_span_check_refuses(self):
        original = app._rows
        def replace(*args):
            result = original(*args)
            replacement = self.root / "replacement"
            replacement.write_bytes(self.fixture.source.read_bytes())
            os.replace(replacement, self.fixture.source)
            return result
        with mock.patch.object(app, "_rows", replace):
            self.assertRefused("A009")

    def test_directory_replacement_during_read_refuses(self):
        original = os.read
        moved = False
        def replace(fd, count):
            nonlocal moved
            result = original(fd, count)
            if result == SOURCE and not moved:
                moved = True
                os.rename(self.root / "audit", self.root / "prior-audit")
                shutil.copytree(self.root / "prior-audit", self.root / "audit")
            return result
        with mock.patch.object(app.inventory.os, "read", replace):
            self.assertRefused("A003")
        self.assertTrue(moved)

    def test_same_size_source_change_during_read_refuses(self):
        original = os.read
        changed = False
        def change(fd, count):
            nonlocal changed
            result = original(fd, count)
            if result == SOURCE and not changed:
                changed = True
                self.fixture.source.write_bytes(b"x" * len(SOURCE))
            return result
        with mock.patch.object(app.inventory.os, "read", change):
            self.assertRefused("A003")
        self.assertTrue(changed)


    def test_pair_limit_before_source_reads(self):
        fixture = maximum_fixture(self.root)
        self.fixture = fixture
        self.assertClean()
        extra = dict(fixture.inventory["source_views"][0], id="extra", path="audit/extra.md")
        fixture.inventory["source_views"].append(extra)
        fixture.declaration["source_views"].append(extra)
        fixture.write()
        with mock.patch.object(app.inventory._CapturedReads, "source", side_effect=AssertionError("source read")):
            self.assertRefused("A004")

    def test_exact_aggregate_budget_and_one_over(self):
        self.fixture = maximum_fixture(self.root)
        self.assertClean()
        source = self.root / "audit/source-31.md"
        source.write_bytes(source.read_bytes() + b"x")
        view = self.root / "audit/view-31.md"
        old = self.fixture.inventory["source_views"][-1]["source_sha256"]
        new = app.digest(source.read_bytes())
        view.write_bytes(view.read_bytes().replace(old.encode(), new.encode()))
        for rows in (self.fixture.inventory["source_views"], self.fixture.declaration["source_views"],
                     self.fixture.inventory["no_known_findings"]["source_views"]):
            rows[-1].update(source_sha256=new, view_sha256=app.digest(view.read_bytes()))
        self.fixture.write()
        self.assertRefused("A003")

    def test_source_view_paths_cannot_alias(self):
        view = self.fixture.view
        original = self.fixture.source.read_bytes()
        # A second view naming the same physical source would otherwise evade
        # an aggregate sum by counting that source only once.
        other = self.root / "audit/other.md"
        other.write_bytes(view.read_bytes())
        row = dict(self.fixture.inventory["source_views"][0], id="second", path="audit/other.md")
        self.fixture.inventory["source_views"].append(row)
        self.fixture.declaration["source_views"].append(copy.deepcopy(row))
        self.fixture.write()
        self.assertRefused("A003")
        self.assertEqual(self.fixture.source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
