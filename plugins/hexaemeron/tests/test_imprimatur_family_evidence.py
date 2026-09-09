"""Guard the structural-family-evidence-v1 fixture and its checker."""

from pathlib import Path
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import unittest
import unittest.mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "imprimatur"
SCRIPT = SKILL_ROOT / "scripts" / "check_family_evidence.py"
COLLECTOR = SKILL_ROOT / "scripts" / "collect_family_evidence.py"
FIXTURE = SKILL_ROOT / "evals" / "structural-family-evidence-v1"
SCHEMAS = FIXTURE / "schemas"
ISSUE = FIXTURE / "issue-1298.md"
README = FIXTURE / "README.md"

# The checker is imported, not restated. Every test below still runs it as a
# subprocess, because its exit code is half of what it promises; what the
# import buys is its declarations. The tier table was a literal here as well
# as in the checker, in the README and on every catalogue row, and only the
# last two were compared, so this module could not see the checker's table
# change. It reads that table now.
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))
import check_family_evidence as checker  # noqa: E402
import collect_family_evidence as collector  # noqa: E402

# One fixture file carries no frozen digest: this README holds the table and
# cannot hold its own digest. Everything else in the fixture has to be pinned,
# so a new file cannot arrive unpinned by omission. `specimens.jsonl` and
# `selection-rejections.jsonl` joined the table when step 3 wrote them.
UNPINNED_FIXTURE_FILES = {
    "README.md": "carries the digest table and cannot hold its own digest",
}

SOURCE_ISSUE = "https://github.com/wildcat-finance/skills/issues/1298"
GROUPS = (
    "Missing conditions and causal wrappers",
    "Hidden actors, authority, and intent",
    "Verb, capability, and purpose shells",
    "Stacked hedges, emphasis, and redundant markers",
    "Existential, reference, and scope constructions needing more evidence",
)
COPIED_FIELDS = {
    "Form": "form",
    "Reader cost": "reader_cost",
    "Direct rewrite": "direct_rewrite",
    "Boundary": "boundary",
    "Disposition": "disposition",
}

FAMILY_ROW = {
    "family_id": "causal_fact_clause_wrapper",
    "group": "Missing conditions and causal wrappers",
    "evidence_tier": "boundary",
    "form": "\"Publication failed due to the fact that the digest changed\".",
    "reader_cost": "A causal connector wraps an already finite cause in a fact noun.",
    "direct_rewrite": "\"Publication failed because the digest changed.\"",
    "boundary": "Cover a closed list of causal connectors followed by \"the fact that\".",
    "disposition": "Strong candidate for evidence.",
    "overlaps": [],
    "discovery_phrases": ["due to the fact that"],
    "minimum_positive": 0,
    "minimum_negative": 0,
    "source_issue": SOURCE_ISSUE,
}

SPECIMEN_TEXT = "Publication failed due to the fact that the digest changed."
SPECIMEN_ROW = {
    "specimen_id": "causal_fact_clause_wrapper-pos-01",
    "family_id": "causal_fact_clause_wrapper",
    "tier": "structural",
    "family": "causal_fact_clause_wrapper",
    "polarity": "positive",
    "decision": "actionable",
    "text": SPECIMEN_TEXT,
    "text_sha256": hashlib.sha256(SPECIMEN_TEXT.encode("utf-8")).hexdigest(),
    "start_byte": 18,
    "end_byte": 38,
    "reason": "A causal connector wraps a finite cause in a fact noun.",
    "rewrite": "Publication failed because the digest changed.",
    "repository": "wildcat-finance/skills",
    "source_url": "https://github.com/wildcat-finance/skills/blob/" + "0" * 40 + "/README.md",
    "source_commit": "0" * 40,
    "source_path": "README.md",
    "source_start_line": 1,
    "source_end_line": 1,
    "source_object": "markdown_paragraph",
    "source_group_id": "wildcat-finance/skills:README.md",
    "origin": "human",
    "annotated_before_lint": True,
    "selection_seed": "imprimatur-structural-family-evidence-v1",
    "selection_rank_within_group": 1,
}


def jsonl(rows) -> str:
    return "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows)


def issue_families(body: str | None = None) -> list[dict]:
    """Parse the checked-in issue body into one record per family heading."""
    group = None
    rows: list[dict] = []
    current = None
    if body is None:
        body = ISSUE.read_text(encoding="utf-8")
    for line in body.splitlines():
        if line.startswith("## "):
            heading = line[3:].strip()
            group = heading if heading in GROUPS else None
            # Leaving a family group closes the open record. Without this a
            # field line under a later section is folded into the last family.
            current = None
            continue
        if line.startswith("### ") and group is not None:
            current = {"family_id": line[4:].strip(), "group": group}
            rows.append(current)
            continue
        if current is None:
            continue
        for label, key in COPIED_FIELDS.items():
            prefix = f"{label}: "
            if line.startswith(prefix):
                current[key] = line[len(prefix):].strip()
    return rows


def issue_evidence_targets() -> tuple[set[str], set[str]]:
    """Read the 13 named evidence targets out of the issue's own packet."""
    body = ISSUE.read_text(encoding="utf-8")
    match = re.search(
        r"The current high-value evidence targets are (.+?)\. "
        r"The signal targets are (.+?)\.",
        body,
    )
    assert match is not None, "the issue no longer names its evidence targets"
    identifier = r"[a-z][a-z0-9]*(?:_[a-z0-9]+)+"
    return (
        set(re.findall(identifier, match.group(1))),
        set(re.findall(identifier, match.group(2))),
    )


class FamilyEvidenceCheckerTest(unittest.TestCase):
    """Every refusal the fixture's checker owes its reader."""

    maxDiff = None

    def run_checker(self, *args: str, env=None) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
            capture_output=True,
            text=True,
            check=False,
            env=env,
        )

    def env_without_gh(self) -> dict:
        """An environment where `gh` cannot be found, so no test can fetch."""
        empty = Path(tempfile.mkdtemp(prefix="family-evidence-nopath-"))
        self.addCleanup(empty.rmdir)
        return dict(os.environ, PATH=str(empty))

    def build_fixture(self, families=None, specimens=None, root=None, schemas=None) -> Path:
        """Write a throwaway fixture; the shipped one is never mutated.

        ``schemas`` takes a callable per file name, applied to the shipped
        schema before it is written, for the cases where the declaration
        rather than a row is what drifts.
        """
        if root is None:
            root = Path(tempfile.mkdtemp(prefix="family-evidence-"))
            self.addCleanup(self.remove_tree, root)
        (root / "schemas").mkdir(parents=True, exist_ok=True)
        for name in ("family.schema.json", "specimen.schema.json"):
            edit = (schemas or {}).get(name)
            if edit is None:
                (root / "schemas" / name).write_bytes((SCHEMAS / name).read_bytes())
                continue
            declared = edit(json.loads((SCHEMAS / name).read_text(encoding="utf-8")))
            (root / "schemas" / name).write_text(
                json.dumps(declared, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        rows = [FAMILY_ROW] if families is None else families
        (root / "families.jsonl").write_text(jsonl(rows), encoding="utf-8")
        (root / "specimens.jsonl").write_text(jsonl(specimens or []), encoding="utf-8")
        return root

    def remove_tree(self, root: Path) -> None:
        for path, directories, files in os.walk(root, topdown=False):
            for name in files:
                Path(path, name).unlink()
            for name in directories:
                target = Path(path, name)
                target.unlink() if target.is_symlink() else target.rmdir()
        root.rmdir()

    def assert_refused(self, root: Path, needle: str, code: int = 1, *args: str) -> None:
        result = self.run_checker("--fixture", str(root), *args)
        self.assertEqual(result.returncode, code, result.stderr)
        self.assertIn(needle, result.stderr)

    def test_clean_fixture_exits_zero(self):
        root = self.build_fixture(specimens=[SPECIMEN_ROW])
        result = self.run_checker("--fixture", str(root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_refuses_symlink(self):
        root = self.build_fixture()
        target = root / "families.jsonl"
        target.unlink()
        target.symlink_to(root / "specimens.jsonl")
        self.assert_refused(root, "symlink refused", code=2)

    def test_refuses_oversized_file(self):
        root = self.build_fixture()
        padded = dict(FAMILY_ROW, reader_cost="x" * 1_100_000)
        (root / "families.jsonl").write_text(jsonl([padded]), encoding="utf-8")
        self.assert_refused(root, "file over 1048576 bytes", code=2)

    def test_refuses_unreadable_json_line(self):
        root = self.build_fixture()
        (root / "families.jsonl").write_text('{"family_id": "broken"\n', encoding="utf-8")
        self.assert_refused(root, "unreadable JSON at families.jsonl:1", code=2)

    def test_refuses_path_outside_the_fixture(self):
        root = self.build_fixture()
        (root / "schemas").rename(root.parent / "escaped-schemas")
        self.addCleanup(self.remove_tree, root.parent / "escaped-schemas")
        (root / "schemas").symlink_to(root.parent / "escaped-schemas")
        self.assert_refused(root, "symlink refused", code=2)

    def test_refuses_row_failing_its_schema(self):
        broken = dict(FAMILY_ROW)
        del broken["reader_cost"]
        root = self.build_fixture(families=[broken])
        self.assert_refused(root, "schema missing keys")

    def test_refuses_duplicate_family_id(self):
        root = self.build_fixture(families=[FAMILY_ROW, dict(FAMILY_ROW)])
        self.assert_refused(root, "duplicate family_id causal_fact_clause_wrapper")

    def test_refuses_unknown_evidence_tier(self):
        root = self.build_fixture(families=[dict(FAMILY_ROW, evidence_tier="promising")])
        self.assert_refused(root, "unknown evidence_tier 'promising'")

    def test_refuses_specimen_naming_unknown_family(self):
        row = dict(SPECIMEN_ROW, family_id="no_such_family", family="no_such_family")
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "names unknown family no_such_family")

    def test_refuses_span_outside_its_text(self):
        row = dict(SPECIMEN_ROW, start_byte=0, end_byte=len(SPECIMEN_TEXT) + 40)
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "lies outside the")

    def test_refuses_span_splitting_a_codepoint(self):
        text = "Publication failed because the digest changed — twice."
        row = dict(
            SPECIMEN_ROW,
            text=text,
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            start_byte=0,
            end_byte=text.encode("utf-8").index(b"\xe2\x80\x94") + 1,
        )
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "splits a UTF-8 codepoint")

    def test_refuses_mismatched_text_sha256(self):
        row = dict(SPECIMEN_ROW, text_sha256="0" * 64)
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "text_sha256 does not match the text")

    def test_refuses_annotation_after_lint(self):
        row = dict(SPECIMEN_ROW, annotated_before_lint=False)
        root = self.build_fixture(specimens=[row])
        self.assert_refused(root, "annotated_before_lint is not true")

    def test_refuses_two_positives_sharing_a_source_group(self):
        second = dict(SPECIMEN_ROW, specimen_id="causal_fact_clause_wrapper-pos-02")
        root = self.build_fixture(specimens=[SPECIMEN_ROW, second])
        self.assert_refused(root, "share source_group_id")

    def test_refuses_a_family_below_its_tier_minimum(self):
        root = self.build_fixture(
            families=[dict(FAMILY_ROW, evidence_tier="high-value", minimum_positive=2, minimum_negative=2)]
        )
        self.assert_refused(root, "below the 2 and 2 its tier requires")

    def test_allow_below_minimum_reports_the_shortfall_instead(self):
        root = self.build_fixture(
            families=[dict(FAMILY_ROW, evidence_tier="high-value", minimum_positive=2, minimum_negative=2)]
        )
        report = root.parent / "report.json"
        self.addCleanup(lambda: report.exists() and report.unlink())
        result = self.run_checker(
            "--fixture", str(root), "--allow-below-minimum", "--report", str(report)
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["families"], 1)
        self.assertEqual(payload["specimens"], 0)
        self.assertEqual(payload["rejections_path"], "selection-rejections.jsonl")
        self.assertEqual([entry["family_id"] for entry in payload["below_minimum"]], ["causal_fact_clause_wrapper"])

    def test_refuses_verify_sources_on_a_row_missing_a_source_field(self):
        row = dict(SPECIMEN_ROW)
        del row["repository"]
        root = self.build_fixture(specimens=[row])
        result = self.run_checker(
            "--fixture", str(root), "--verify-sources", env=self.env_without_gh()
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("schema missing keys", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_refuses_verify_sources_on_a_repository_outside_the_schema(self):
        row = dict(SPECIMEN_ROW, repository="attacker-controlled/evil")
        root = self.build_fixture(specimens=[row])
        result = self.run_checker(
            "--fixture", str(root), "--verify-sources", env=self.env_without_gh()
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("schema pattern mismatch", result.stderr)
        self.assertNotIn("gh", result.stderr)

    def recording_gh(self) -> tuple[dict, Path]:
        """A `gh` on PATH that records its arguments and opens no socket."""
        directory = Path(tempfile.mkdtemp(prefix="family-evidence-gh-"))
        self.addCleanup(self.remove_tree, directory)
        log = directory / "argv.log"
        stub = directory / "gh"
        body = json.dumps({"body": SPECIMEN_TEXT, "commit": {"message": SPECIMEN_TEXT}})
        stub.write_text(
            "#!/bin/sh\n"
            f'printf "%s\\n" "$@" >> "{log}"\n'
            f"printf '%s\\n' '{body}'\n",
            encoding="utf-8",
        )
        stub.chmod(0o755)
        return dict(os.environ, PATH=str(directory)), log

    def hostname_recording_gh(self) -> tuple[dict, Path, Path]:
        """A `gh` recording its arguments and its own GH_HOST, opening no socket.

        Its log paths and its reply come from the environment rather than from
        interpolation, so no value reaches the generated shell script's quoting.
        """
        directory = Path(tempfile.mkdtemp(prefix="family-evidence-host-"))
        self.addCleanup(self.remove_tree, directory)
        argv_log = directory / "argv.log"
        host_log = directory / "host.log"
        stub = directory / "gh"
        stub.write_text(
            "#!/bin/sh\n"
            'printf "%s\\n" "$@" >> "$FAMILY_EVIDENCE_ARGV_LOG"\n'
            'printf "[%s]\\n" "${GH_HOST-unset}" >> "$FAMILY_EVIDENCE_HOST_LOG"\n'
            'printf "%s\\n" "$FAMILY_EVIDENCE_BODY"\n',
            encoding="utf-8",
        )
        stub.chmod(0o755)
        environment = dict(
            os.environ,
            PATH=str(directory),
            GH_HOST="ghe.attacker.example",
            FAMILY_EVIDENCE_ARGV_LOG=str(argv_log),
            FAMILY_EVIDENCE_HOST_LOG=str(host_log),
            FAMILY_EVIDENCE_BODY=SPECIMEN_TEXT,
        )
        return environment, argv_log, host_log

    def test_the_replay_pins_the_github_host(self):
        """A relative path names an object only once a host is fixed.

        `gh` takes the host from `--hostname`, then `GH_HOST`, then the working
        directory's own remote. Only the first is this checker's to state.
        """
        root = self.build_fixture(specimens=[SPECIMEN_ROW])
        env, argv_log, host_log = self.hostname_recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        recorded = argv_log.read_text(encoding="utf-8").splitlines()
        self.assertIn("--hostname", recorded)
        self.assertEqual(recorded[recorded.index("--hostname") + 1], "github.com")
        self.assertEqual(host_log.read_text(encoding="utf-8").splitlines(), ["[unset]"])

    def test_refuses_a_declared_minimum_that_disagrees_with_its_tier(self):
        """The row declares its minimums and TIER_MINIMUMS enforces them."""
        agreeing = self.build_fixture(
            families=[dict(FAMILY_ROW, evidence_tier="signal", minimum_positive=2, minimum_negative=1)]
        )
        self.assert_refused(agreeing, "below the 2 and 1 its tier requires")
        drifted = self.build_fixture(
            families=[dict(FAMILY_ROW, evidence_tier="signal", minimum_positive=1, minimum_negative=0)]
        )
        self.assert_refused(
            drifted,
            "declares minimum_positive 1 and minimum_negative 0, but tier signal "
            "is enforced as 2 and 1",
        )

    def test_refuses_a_required_field_no_enforcement_accounts_for(self):
        """A field can be required and enforced by nothing.

        The schema states requirements and the checker states checks, and the
        two were separate lists: dropping `origin` from the specimen schema's
        `required` list, and adding a field nothing reads, each left all 54
        tests green. Both directions are a finding now, so a field cannot
        enter or leave a schema without a decision about who enforces it.
        """
        dropped = self.build_fixture(
            schemas={
                "specimen.schema.json": lambda declared: dict(
                    declared,
                    required=[name for name in declared["required"] if name != "origin"],
                )
            }
        )
        self.assert_refused(
            dropped,
            "specimen.schema.json: field enforcement names ['origin'], which required does not declare",
        )
        added = self.build_fixture(
            schemas={
                "family.schema.json": lambda declared: dict(
                    declared,
                    required=[*declared["required"], "weight"],
                    properties=dict(declared["properties"], weight={"type": "integer"}),
                )
            }
        )
        self.assert_refused(
            added,
            "family.schema.json: required names ['weight'], which no field enforcement accounts for",
        )

    def test_refuses_a_schema_tier_the_checker_does_not_enforce(self):
        """The tier set was declared in the schema and again in the checker.

        Adding a sixth tier to the enum left all 54 tests green while the
        checker would have refused every row carrying it, so the schema could
        offer a tier no fixture could use.
        """
        def sixth(declared):
            properties = json.loads(json.dumps(declared["properties"]))
            properties["evidence_tier"]["enum"].append("promising")
            return dict(declared, properties=properties)

        root = self.build_fixture(schemas={"family.schema.json": sixth})
        self.assert_refused(root, "family.schema.json: evidence_tier declares")

    def test_refuses_a_schema_seed_that_is_not_the_fixture_seed(self):
        """`FIXTURE_SEED` and the schema's `selection_seed` const were two copies.

        Changing the constant left all 54 tests green, and the report's `seed`
        then named a seed no specimen was allowed to declare.
        """
        def other(declared):
            properties = json.loads(json.dumps(declared["properties"]))
            properties["selection_seed"]["const"] = "some-other-seed"
            return dict(declared, properties=properties)

        root = self.build_fixture(schemas={"specimen.schema.json": other})
        self.assert_refused(root, "selection_seed declares 'some-other-seed'")

    def test_refuses_a_schema_document_this_checker_cannot_read(self):
        """A schema is fixture data, and it was the one input read raw.

        A row's fields pass a schema clause and, where one reaches an
        endpoint, `endpoint_segment`; a `gh` reply's fields pass
        `reply_value`. Every keyword the validator dereferences was taken on
        trust, so a document that is valid JSON and unusable raised an
        uncaught AttributeError, KeyError, TypeError or re.PatternError,
        printed a traceback and exited 1 -- the code reserved for a content
        finding, not the 2 reserved for an unsafe read.
        """
        def property_of(name, key, value):
            def edit(declared):
                properties = json.loads(json.dumps(declared["properties"]))
                properties[name][key] = value
                return dict(declared, properties=properties)

            return edit

        def property_value(name, value):
            def edit(declared):
                properties = json.loads(json.dumps(declared["properties"]))
                properties[name] = value
                return dict(declared, properties=properties)

            return edit

        cases = (
            ("the document is not an object", lambda declared: [], "is not a JSON object"),
            (
                "type names no predicate",
                lambda declared: dict(declared, type="str"),
                "declares a type this checker cannot check: 'str'",
            ),
            (
                "required is not a list of names",
                lambda declared: dict(declared, required=3),
                "declares required, which is not a list of field names",
            ),
            (
                "properties is not an object",
                lambda declared: dict(declared, properties=[]),
                "declares properties, which is not an object",
            ),
            (
                "a property value is not an object",
                property_value("family_id", "string"),
                "family.schema.json/properties/family_id is not a JSON object",
            ),
            (
                "items is not an object",
                property_of("overlaps", "items", "string"),
                "family.schema.json/properties/overlaps/items is not a JSON object",
            ),
            (
                "an enum is not a list of names",
                property_of("evidence_tier", "enum", [1, "signal"]),
                "declares enum, which is not a list of names",
            ),
            (
                "a pattern is not a string",
                property_of("family_id", "pattern", 7),
                "declares a pattern that is not a string",
            ),
            (
                "a pattern does not compile",
                property_of("family_id", "pattern", "([a-z"),
                "declares a pattern that does not compile",
            ),
            (
                "a numeric bound is not a number",
                property_of("form", "minLength", "1"),
                "declares minLength, which is not a number",
            ),
        )
        for label, edit, needle in cases:
            with self.subTest(schema=label):
                root = self.build_fixture(schemas={"family.schema.json": edit})
                result = self.run_checker("--fixture", str(root), env=self.env_without_gh())
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(needle, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_refuses_a_schema_that_does_not_declare_what_this_checker_keys_on(self):
        """A schema clause is what makes several of the checker's own reads safe.

        Gating the schema document made it readable. It did not make these
        clauses load-bearing where the rows are read. With `family_id`'s
        `type` dropped, a row carrying an object cleared `validate_schema` and
        reached `row["family_id"] in seen`, raising an uncaught TypeError,
        printing a traceback and exiting 1 -- the code reserved for a content
        finding, not the 2 reserved for an unsafe read. Five shapes raised
        that way. Dropping `polarity`'s enum was quieter and worse: a positive
        specimen counted as neither polarity, reached no independence count,
        and the fixture exited 0.
        """
        def without(name, keyword):
            def edit(declared):
                properties = json.loads(json.dumps(declared["properties"]))
                properties[name].pop(keyword)
                return dict(declared, properties=properties)

            return edit

        cases = (
            ("family.schema.json", "family_id", "type"),
            ("specimen.schema.json", "specimen_id", "type"),
            ("specimen.schema.json", "family_id", "type"),
            ("specimen.schema.json", "source_group_id", "type"),
            ("specimen.schema.json", "polarity", "enum"),
            ("specimen.schema.json", "source_object", "enum"),
        )
        for schema_name, field, keyword in cases:
            with self.subTest(schema=schema_name, field=field, keyword=keyword):
                root = self.build_fixture(
                    specimens=[SPECIMEN_ROW],
                    schemas={schema_name: without(field, keyword)},
                )
                result = self.run_checker("--fixture", str(root), env=self.env_without_gh())
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn(f"{schema_name}: {field} declares {keyword} None", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_a_row_an_untyped_schema_admits_reaches_no_unhashable_read(self):
        """The reproduction: one clause dropped and one row that exploits it."""
        def untyped(name):
            def edit(declared):
                properties = json.loads(json.dumps(declared["properties"]))
                properties[name] = {}
                return dict(declared, properties=properties)

            return edit

        root = self.build_fixture(
            families=[dict(FAMILY_ROW, family_id={})],
            schemas={"family.schema.json": untyped("family_id")},
        )
        result = self.run_checker("--fixture", str(root), env=self.env_without_gh())
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_refuses_an_overlaps_entry_that_names_no_family(self):
        """`overlaps` declared a link to another family and nothing resolved it."""
        root = self.build_fixture(families=[dict(FAMILY_ROW, overlaps=["no_such_family"])])
        self.assert_refused(
            root,
            "causal_fact_clause_wrapper overlaps 'no_such_family', which is not a family in this catalogue",
        )
        sibling = self.build_fixture(
            families=[
                FAMILY_ROW,
                dict(FAMILY_ROW, family_id="reason_is_because", overlaps=["causal_fact_clause_wrapper"]),
            ]
        )
        result = self.run_checker("--fixture", str(sibling), env=self.env_without_gh())
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_the_report_names_every_field_this_step_does_not_enforce(self):
        """Eight required fields are deferred, and the report says which.

        Four audit rounds found them one at a time from `grep` output. The
        step that writes them reads them here instead.
        """
        directory = Path(tempfile.mkdtemp(prefix="family-evidence-report-"))
        self.addCleanup(self.remove_tree, directory)
        report = directory / "report.json"
        result = self.run_checker(
            "--fixture", str(FIXTURE), "--allow-below-minimum", "--report", str(report),
            env=self.env_without_gh(),
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        written = json.loads(report.read_text(encoding="utf-8"))
        self.assertIn("unenforced_fields", written)
        entries = written.get("unenforced_fields", [])
        self.assertEqual(
            [(entry["row"], entry["field"]) for entry in entries],
            [
                ("families.jsonl", "discovery_phrases"),
                ("specimens.jsonl", "decision"),
                ("specimens.jsonl", "origin"),
                ("specimens.jsonl", "reason"),
                ("specimens.jsonl", "rewrite"),
                ("specimens.jsonl", "selection_rank_within_group"),
                ("specimens.jsonl", "source_end_line"),
                ("specimens.jsonl", "source_start_line"),
            ],
        )
        for entry in entries:
            self.assertEqual(entry["owner"], "step-3")
            self.assertTrue(entry["note"])

    def test_refuses_an_independent_positive_override_without_a_tier(self):
        """The override reaches every tier the run measures, so it names one."""
        alone = self.run_checker(
            "--fixture", str(FIXTURE), "--allow-below-minimum",
            "--min-independent-positive", "2",
            env=self.env_without_gh(),
        )
        self.assertEqual(alone.returncode, 2, alone.stderr)
        self.assertIn("needs --tier", alone.stderr)
        paired = self.run_checker(
            "--fixture", str(FIXTURE), "--allow-below-minimum",
            "--min-independent-positive", "2", "--tier", "high-value",
            env=self.env_without_gh(),
        )
        self.assertEqual(paired.returncode, 0, paired.stderr)

    def test_help_does_not_call_the_replay_immutable(self):
        """The claim round 4 removed from the README shipped on in `--help`.

        Four of the six kinds send no reference, so their replay compares the
        current body, and `--help` is the copy an operator reads.
        """
        result = self.run_checker("--help", env=self.env_without_gh())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--verify-sources", result.stdout)
        self.assertNotIn("immutable", result.stdout)

    def test_refuses_a_repository_outside_the_pinned_prefix(self):
        row = dict(SPECIMEN_ROW, repository="wildcat-finance/../evil-org/evil-repo")
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("not one pinned wildcat-finance repository", result.stderr)
        self.assertFalse(log.exists(), "the refused repository still reached gh")

    def test_refuses_a_source_path_carrying_a_url_delimiter(self):
        row = dict(SPECIMEN_ROW, source_path="README.md#x")
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unusable source_path", result.stderr)
        self.assertFalse(log.exists(), "the refused source_path still reached gh")

    def test_refuses_a_comment_url_without_its_comment_id(self):
        row = dict(
            SPECIMEN_ROW,
            source_object="issue_comment",
            source_path=None,
            source_url="https://github.com/wildcat-finance/skills/issues/1298",
        )
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("cannot read a comment id", result.stderr)
        self.assertFalse(log.exists(), "the id-less comment URL still reached gh")

    def test_a_comment_replays_its_own_comment_id_not_its_issue_number(self):
        row = dict(
            SPECIMEN_ROW,
            source_object="issue_comment",
            source_path=None,
            source_url="https://github.com/wildcat-finance/skills/issues/1298#issuecomment-42",
        )
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            log.read_text(encoding="utf-8").splitlines(),
            [
                "api",
                "--hostname",
                "github.com",
                "repos/wildcat-finance/skills/issues/comments/42",
            ],
        )

    def test_refuses_a_source_commit_carrying_a_trailing_newline(self):
        """The schema's `^[0-9a-f]{40}$` also matches before a trailing newline."""
        row = dict(
            SPECIMEN_ROW,
            source_object="commit_message",
            source_path=None,
            source_commit="a" * 40 + "\n",
            source_url="https://github.com/wildcat-finance/skills/commit/" + "a" * 40,
        )
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unusable source_commit", result.stderr)
        self.assertFalse(log.exists(), "the newline-bearing source_commit still reached gh")

    def test_refuses_an_issue_number_that_is_not_ascii_digits(self):
        """`str.isdigit()` is true for Arabic-Indic digits, which are not a number here."""
        row = dict(
            SPECIMEN_ROW,
            source_object="issue_body",
            source_path=None,
            source_url="https://github.com/wildcat-finance/skills/issues/\u0661\u0662\u0663",
        )
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("cannot read an object number", result.stderr)
        self.assertFalse(log.exists(), "the non-ASCII issue number still reached gh")

    def test_refuses_a_comment_id_carrying_a_trailing_newline(self):
        row = dict(
            SPECIMEN_ROW,
            source_object="issue_comment",
            source_path=None,
            source_url="https://github.com/wildcat-finance/skills/issues/1298#issuecomment-42\n",
        )
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("cannot read a comment id", result.stderr)
        self.assertFalse(log.exists(), "the newline-bearing comment id still reached gh")

    def test_refuses_a_duplicate_key_in_one_row(self):
        """JSON's last-wins rule would enforce a tier the row does not appear to carry."""
        root = self.build_fixture()
        row = json.dumps(FAMILY_ROW)[:-1] + ', "evidence_tier": "high-value"}'
        (root / "families.jsonl").write_text(row + "\n", encoding="utf-8")
        self.assert_refused(root, "duplicate JSON key 'evidence_tier'", code=2)

    def test_refuses_a_row_hidden_behind_a_unicode_line_separator(self):
        """`str.splitlines()` splits on five characters JSON allows in a string."""
        for separator in ("\u2028", "\u2029", "\u0085", "\v", "\f"):
            with self.subTest(separator=f"U+{ord(separator):04X}"):
                root = self.build_fixture()
                smuggled = dict(FAMILY_ROW, family_id="smuggled_row")
                one_line = (
                    json.dumps(FAMILY_ROW, ensure_ascii=False)
                    + separator
                    + json.dumps(smuggled, ensure_ascii=False)
                )
                (root / "families.jsonl").write_text(one_line + "\n", encoding="utf-8")
                self.assert_refused(root, "unreadable JSON at families.jsonl:1", 2)

    def test_a_separator_inside_specimen_text_stays_one_row(self):
        """`json.dumps(..., ensure_ascii=False)` emits U+2028 raw; it is not a row break."""
        text = "Publication failed due to\u2028the fact that the digest changed."
        row = dict(
            SPECIMEN_ROW,
            text=text,
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
            start_byte=0,
            end_byte=len(text.encode("utf-8")),
        )
        root = self.build_fixture(specimens=[row])
        result = self.run_checker("--fixture", str(root))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")

    def test_refuses_a_specimen_whose_family_and_family_id_disagree(self):
        """One family under two field names, with nothing tying them together."""
        for other in ("reason_is_because", "no_such_family_anywhere"):
            with self.subTest(family=other):
                root = self.build_fixture(specimens=[dict(SPECIMEN_ROW, family=other)])
                self.assert_refused(root, "is not its family_id")

    def test_refuses_a_source_group_id_carrying_an_invisible_difference(self):
        """Independence is decided by comparing this value, so it has to be visible."""
        for character in (" ", "\u00a0", "\u200b"):
            with self.subTest(character=f"U+{ord(character):04X}"):
                second = dict(
                    SPECIMEN_ROW,
                    specimen_id="causal_fact_clause_wrapper-pos-02",
                    source_group_id=SPECIMEN_ROW["source_group_id"] + character,
                )
                root = self.build_fixture(specimens=[SPECIMEN_ROW, second])
                self.assert_refused(root, "source_group_id carries")

    def test_refuses_a_source_group_id_that_is_not_normalised(self):
        """A combining mark is neither whitespace nor a non-printing character."""
        composed = "wildcat-finance/skills:docs/café.md"
        decomposed = unicodedata.normalize("NFD", composed)
        self.assertNotEqual(composed, decomposed)
        first = dict(SPECIMEN_ROW, source_group_id=composed)
        second = dict(
            SPECIMEN_ROW,
            specimen_id="causal_fact_clause_wrapper-pos-02",
            source_group_id=decomposed,
        )
        root = self.build_fixture(specimens=[first, second])
        self.assert_refused(root, "is not in Unicode normal form NFC")

    def test_refuses_a_citation_naming_another_repository(self):
        """The endpoint is built from `repository`, so the citation has to agree."""
        row = dict(
            SPECIMEN_ROW,
            source_object="issue_body",
            source_path=None,
            source_url="https://github.com/wildcat-finance/v2-protocol/issues/7",
        )
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("does not cite wildcat-finance/skills", result.stderr)
        self.assertFalse(log.exists(), "the mismatched citation still reached gh")

    def test_refuses_a_citation_naming_another_object(self):
        """Shape says one wildcat-finance object; identity says which one."""
        cases = {
            "markdown_paragraph": (
                "https://github.com/wildcat-finance/skills/blob/" + "0" * 40 + "/docs/OTHER.md",
                "blob/" + "0" * 40 + "/README.md",
            ),
            "commit_message": (
                "https://github.com/wildcat-finance/skills/commit/" + "1" * 40,
                "commit/" + "0" * 40,
            ),
            "pull_request_body": (
                "https://github.com/wildcat-finance/skills/issues/1298",
                "pull/1298",
            ),
        }
        for kind, (url, expected) in cases.items():
            with self.subTest(source_object=kind):
                row = dict(
                    SPECIMEN_ROW,
                    source_object=kind,
                    source_url=url,
                    source_path="README.md" if kind == "markdown_paragraph" else None,
                )
                root = self.build_fixture(specimens=[row])
                env, log = self.recording_gh()
                result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("is not the replayed object", result.stderr)
                self.assertIn(expected, result.stderr)
                self.assertFalse(log.exists(), "the mismatched citation still reached gh")

    def test_an_agreeing_citation_still_replays_the_cited_file(self):
        """A `#L10-L14` fragment cites lines, and `raw/` cites the same file."""
        base = "https://github.com/wildcat-finance/skills/"
        for url in (
            SPECIMEN_ROW["source_url"] + "#L10-L14",
            base + "raw/" + "0" * 40 + "/README.md",
        ):
            with self.subTest(url=url):
                root = self.build_fixture(specimens=[dict(SPECIMEN_ROW, source_url=url)])
                env, log = self.recording_gh()
                result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(
                    "repos/wildcat-finance/skills/contents/README.md?ref=" + "0" * 40,
                    log.read_text(encoding="utf-8").splitlines(),
                )

    def test_a_replayed_object_without_the_text_is_a_finding(self):
        """The replay's own comparison: the text is present, or it is not."""
        directory = Path(tempfile.mkdtemp(prefix="family-evidence-gh-"))
        self.addCleanup(self.remove_tree, directory)
        stub = directory / "gh"
        stub.write_text("#!/bin/sh\nprintf '%s\\n' 'nothing like the specimen'\n", encoding="utf-8")
        stub.chmod(0o755)
        root = self.build_fixture(specimens=[SPECIMEN_ROW])
        result = self.run_checker(
            "--fixture", str(root), "--verify-sources",
            env=dict(os.environ, PATH=str(directory)),
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("text is absent from the replayed object", result.stderr)

    def test_every_source_object_kind_replays_its_own_endpoint(self):
        """One gate guards every endpoint segment; none of the six kinds lost its replay."""
        expected = {
            "markdown_paragraph": (
                "https://github.com/wildcat-finance/skills/blob/" + "0" * 40 + "/README.md",
                "repos/wildcat-finance/skills/contents/README.md?ref=" + "0" * 40,
            ),
            "commit_message": (
                "https://github.com/wildcat-finance/skills/commit/" + "0" * 40,
                "repos/wildcat-finance/skills/commits/" + "0" * 40,
            ),
            "issue_body": (
                "https://github.com/wildcat-finance/skills/issues/1298",
                "repos/wildcat-finance/skills/issues/1298",
            ),
            "pull_request_body": (
                "https://github.com/wildcat-finance/skills/pull/1298",
                "repos/wildcat-finance/skills/issues/1298",
            ),
            "issue_comment": (
                "https://github.com/wildcat-finance/skills/issues/1298#issuecomment-42",
                "repos/wildcat-finance/skills/issues/comments/42",
            ),
            "pull_request_comment": (
                "https://github.com/wildcat-finance/skills/pull/1298#discussion_r99",
                "repos/wildcat-finance/skills/pulls/comments/99",
            ),
        }
        self.assertEqual(len(expected), 6, "the schema's source_object enum has six values")
        for kind, (url, endpoint) in expected.items():
            with self.subTest(source_object=kind):
                row = dict(
                    SPECIMEN_ROW,
                    source_object=kind,
                    source_url=url,
                    source_path="README.md" if kind == "markdown_paragraph" else None,
                )
                root = self.build_fixture(specimens=[row])
                env, log = self.recording_gh()
                result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(endpoint, log.read_text(encoding="utf-8").splitlines())

    def test_refuses_a_comment_citation_that_names_no_thread(self):
        """A fragment cites a comment; the path before it has to cite its thread."""
        base = "https://github.com/wildcat-finance/skills/"
        cases = (
            base + "blob/" + "0" * 40 + "/README.md#issuecomment-42",
            base + "commit/" + "0" * 40 + "#issuecomment-42",
            base + "releases/tag/v9#issuecomment-42",
        )
        for url in cases:
            with self.subTest(url=url):
                row = dict(
                    SPECIMEN_ROW,
                    source_object="issue_comment",
                    source_path=None,
                    source_url=url,
                )
                root = self.build_fixture(specimens=[row])
                env, log = self.recording_gh()
                result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("is not an issue or pull request thread", result.stderr)
                self.assertFalse(log.exists(), "the thread-less citation still reached gh")

    def test_refuses_a_review_comment_cited_under_an_issue_thread(self):
        """`#discussion_r` is a pull request review comment; an issue has none."""
        row = dict(
            SPECIMEN_ROW,
            source_object="pull_request_comment",
            source_path=None,
            source_url="https://github.com/wildcat-finance/skills/issues/1298#discussion_r99",
        )
        root = self.build_fixture(specimens=[row])
        env, log = self.recording_gh()
        result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("cites a review comment under 'issues/1298'", result.stderr)
        self.assertFalse(log.exists(), "the mislabelled review comment still reached gh")

    def test_a_citation_carrying_a_query_string_still_replays_its_object(self):
        """A query is not part of the path, and `?plain=1` is GitHub's own permalink."""
        cases = {
            "markdown_paragraph": (
                SPECIMEN_ROW["source_url"] + "?plain=1#L1-L4",
                "repos/wildcat-finance/skills/contents/README.md?ref=" + "0" * 40,
            ),
            "issue_body": (
                "https://github.com/wildcat-finance/skills/issues/1298?notification_referrer_id=x",
                "repos/wildcat-finance/skills/issues/1298",
            ),
        }
        for kind, (url, endpoint) in cases.items():
            with self.subTest(source_object=kind):
                row = dict(
                    SPECIMEN_ROW,
                    source_object=kind,
                    source_url=url,
                    source_path="README.md" if kind == "markdown_paragraph" else None,
                )
                root = self.build_fixture(specimens=[row])
                env, log = self.recording_gh()
                result = self.run_checker("--fixture", str(root), "--verify-sources", env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(endpoint, log.read_text(encoding="utf-8").splitlines())

    def test_refuses_a_duplicate_specimen_id(self):
        """Two rows for one specimen. A duplicate family_id was already refused."""
        root = self.build_fixture(specimens=[SPECIMEN_ROW, dict(SPECIMEN_ROW)])
        self.assert_refused(root, "duplicate specimen_id causal_fact_clause_wrapper-pos-01")

    def test_duplicate_negatives_cannot_carry_a_tier_minimum(self):
        """One document counted twice satisfied a high-value negative minimum."""
        family = dict(
            FAMILY_ROW,
            evidence_tier="high-value",
            minimum_positive=2,
            minimum_negative=2,
        )
        negative = dict(
            SPECIMEN_ROW,
            specimen_id="causal_fact_clause_wrapper-neg-01",
            polarity="negative",
            decision="negative",
        )
        specimens = [
            dict(SPECIMEN_ROW, source_group_id="wildcat-finance/skills:docs/A.md"),
            dict(
                SPECIMEN_ROW,
                specimen_id="causal_fact_clause_wrapper-pos-02",
                source_group_id="wildcat-finance/skills:docs/B.md",
            ),
            negative,
            dict(negative),
        ]
        root = self.build_fixture(families=[family], specimens=specimens)
        self.assert_refused(root, "duplicate specimen_id causal_fact_clause_wrapper-neg-01")

    def test_refuses_a_raw_field_that_cannot_be_hashed(self):
        """The tier-minimum measurement runs before validation, on raw fields."""
        # `source_group_id` is only counted for a tier that has a minimum, so
        # the family here carries one; `evidence_tier` is looked up before that.
        measured = dict(FAMILY_ROW, evidence_tier="high-value", minimum_positive=2, minimum_negative=2)
        cases = (
            ([measured], [dict(SPECIMEN_ROW, source_group_id=["a"])], "specimen-schema"),
            ([dict(FAMILY_ROW, evidence_tier=[])], [], "family-tier"),
        )
        for families, specimens, needle in cases:
            with self.subTest(needle=needle):
                root = self.build_fixture(families=families, specimens=specimens)
                result = self.run_checker("--fixture", str(root), env=self.env_without_gh())
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(needle, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_refuses_a_gh_reply_that_is_not_the_shape_its_kind_expects(self):
        """A reply is outside data too; a KeyError here would exit 1, not 2."""
        for payload in ('{"body": "x"}', '{"commit": {}}', "not json at all", "[]"):
            with self.subTest(payload=payload):
                directory = Path(tempfile.mkdtemp(prefix="family-evidence-gh-"))
                self.addCleanup(self.remove_tree, directory)
                stub = directory / "gh"
                stub.write_text(
                    "#!/bin/sh\nprintf '%s\\n' '" + payload + "'\n", encoding="utf-8"
                )
                stub.chmod(0o755)
                row = dict(
                    SPECIMEN_ROW,
                    source_object="commit_message",
                    source_path=None,
                    source_url="https://github.com/wildcat-finance/skills/commit/" + "0" * 40,
                )
                root = self.build_fixture(specimens=[row])
                result = self.run_checker(
                    "--fixture", str(root), "--verify-sources",
                    env=dict(os.environ, PATH=str(directory)),
                )
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_refuses_a_bad_invocation(self):
        result = self.run_checker("--fixture", str(FIXTURE), "--tier", "promising")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unknown tier: promising", result.stderr)

    def test_shipped_fixture_reports_forty_two_families(self):
        with tempfile.TemporaryDirectory(prefix="family-evidence-report-") as directory:
            report = Path(directory) / "report.json"
            result = self.run_checker(
                "--fixture", str(FIXTURE), "--allow-below-minimum", "--report", str(report)
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(report.read_text(encoding="utf-8"))
        self.assertEqual(payload["families"], 42)
        # Step 3 collected specimens for the 13 target families and met the
        # tier minimum for nine. The four below it are the families whose form
        # the pinned universe does not carry twice in two source groups, and
        # the README's collection record states, per family, the bounded
        # pattern that established that and what it found; this pins that
        # record. `redundant_connective_pair` and `stacked_epistemic_modal`
        # were in this list until the second reconnaissance pass: the first
        # closed on a per-instance reading of the additive shape the issue's
        # Form names, the second on two attested pairs of the issue's closed
        # class added to `discovery_phrases`.
        self.assertEqual(
            sorted(row["family_id"] for row in payload["below_minimum"]),
            [
                "causal_fact_clause_wrapper",
                "empty_expletive_case",
                "existential_relative_shell",
                "reason_is_because",
            ],
        )
        for row in payload["below_minimum"]:
            self.assertLess(row["independent_positives"], 2, row)
            self.assertGreaterEqual(row["negatives"], row["minimum_negative"], row)


class FamilyCatalogueWordingTest(unittest.TestCase):
    """The catalogue must quote the issue rather than paraphrase it."""

    maxDiff = None

    def setUp(self):
        self.rows = [
            json.loads(line)
            for line in (FIXTURE / "families.jsonl").read_text(encoding="utf-8").splitlines()
        ]

    def test_families_match_the_issue_headings_and_lines(self):
        parsed = issue_families()
        self.assertEqual(len(parsed), 42)
        self.assertEqual([row["family_id"] for row in self.rows], [row["family_id"] for row in parsed])
        for shipped, source in zip(self.rows, parsed):
            self.assertEqual(shipped["group"], source["group"], shipped["family_id"])
            for key in COPIED_FIELDS.values():
                self.assertEqual(shipped[key], source[key], f"{shipped['family_id']}/{key}")

    def test_tier_minimums_follow_the_evidence_tier(self):
        minimums = checker.TIER_MINIMUMS
        for row in self.rows:
            expected = minimums[row["evidence_tier"]]
            self.assertEqual((row["minimum_positive"], row["minimum_negative"]), expected, row["family_id"])
        tiers = [row["evidence_tier"] for row in self.rows]
        self.assertEqual(tiers.count("high-value"), 5)
        self.assertEqual(tiers.count("signal"), 8)

    def test_refuses_an_evidence_tier_the_issue_packet_does_not_name(self):
        high_value, signal = issue_evidence_targets()
        self.assertEqual(len(high_value), 5)
        self.assertEqual(len(signal), 8)
        tiers = {row["family_id"]: row["evidence_tier"] for row in self.rows}
        self.assertEqual({fid for fid, tier in tiers.items() if tier == "high-value"}, high_value)
        self.assertEqual({fid for fid, tier in tiers.items() if tier == "signal"}, signal)
        rest = [tier for fid, tier in tiers.items() if fid not in high_value | signal]
        self.assertEqual(len(rest), 29)
        self.assertEqual(rest.count("boundary"), 9)
        self.assertEqual(rest.count("existing-family"), 4)
        self.assertEqual(rest.count("future"), 16)

    def test_refuses_a_field_line_after_the_last_family(self):
        body = "\n".join(
            [
                f"## {GROUPS[0]}",
                "",
                "### only_family",
                "",
                "Form: kept.",
                "Reader cost: kept.",
                "Direct rewrite: kept.",
                "Boundary: kept.",
                "Disposition: kept.",
                "",
                "## Questions left open",
                "",
                "Disposition: this line belongs to no family.",
                "",
            ]
        )
        parsed = issue_families(body)
        self.assertEqual([row["family_id"] for row in parsed], ["only_family"])
        self.assertEqual(parsed[0]["disposition"], "kept.")

    @staticmethod
    def digest_rows(section: str) -> list[tuple[str, str]]:
        """Return the digest rows of one README section.

        The README carries two digest tables with different bases, so a
        pattern applied to the whole file cannot say which base a row belongs
        to. Splitting on the heading keeps each table with its own base. An
        absent heading returns no rows rather than raising, so its caller
        fails on the comparison it came to make.
        """
        body = README.read_text(encoding="utf-8")
        if section not in body:
            return []
        start = body.index(section) + len(section)
        remainder = body[start:]
        heading = re.search(r"^#{2,3} ", remainder, flags=re.M)
        if heading is not None:
            remainder = remainder[: heading.start()]
        return re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", remainder, flags=re.M)

    def test_readme_frozen_digests_match_the_current_files(self):
        table = self.digest_rows("\n## Frozen digests\n")
        self.assertEqual(len(table), 5)
        for relative, expected in table:
            blob = (SKILL_ROOT / relative).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), expected, relative)

    def test_the_fixture_digest_table_covers_every_fixture_file(self):
        """The oracle the wording test reads was itself unpinned.

        `issue-1298.md` carried no frozen digest for six audit rounds, so an
        edit made consistently to it and to the catalogue left every test
        green. Requiring the table to cover the whole fixture closes the way
        that happened, which was omission rather than a wrong digest.
        """
        table = dict(self.digest_rows("\n### Fixture inputs\n"))
        present = {
            str(path.relative_to(FIXTURE))
            for path in sorted(FIXTURE.rglob("*"))
            if path.is_file()
        }
        self.assertEqual(sorted(table), sorted(present - set(UNPINNED_FIXTURE_FILES)))
        self.assertEqual(sorted(set(UNPINNED_FIXTURE_FILES) - present), [])
        for relative, expected in table.items():
            blob = (FIXTURE / relative).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), expected, relative)

    def test_the_readme_tier_table_states_the_enforced_minimums(self):
        """The README says of its own table that it is what the checker enforces.

        Nothing held it to that. Editing the `signal` row to 1 and 0 while the
        checker enforced 2 and 1 left all 54 tests green, so the document that
        claimed to be the source of the contract was the one copy joined to
        nothing.
        """
        rows = re.findall(
            r"^\| `([a-z-]+)` \| [^|]+ \| ([0-9]+)(?: independent)? \| ([0-9]+) \|$",
            README.read_text(encoding="utf-8"),
            flags=re.M,
        )
        stated = {tier: (int(positive), int(negative)) for tier, positive, negative in rows}
        self.assertEqual(stated, dict(checker.TIER_MINIMUMS))


class FamilyEvidenceCollectorTest(unittest.TestCase):
    """The collector is the executable form of the study's selection rule.

    Every case here is offline: no test opens a socket, and the collector's
    network functions are never called. ``--verify-sources`` on the shipped
    fixture is the online proof, and it runs in the runbook's Exit, not here.
    """

    maxDiff = None

    @staticmethod
    def document(text: str, path: str = "docs/a.md", repository: str = "wildcat-finance/skills",
                 commit: str = "1" * 40) -> dict:
        return {
            "kind": "markdown_paragraph", "repository": repository, "commit": commit,
            "path": path, "number": None, "comment": None, "fragment": None,
            "date": None, "text": text,
        }

    @staticmethod
    def family(family_id: str = "purpose_periphrasis", tier: str = "signal",
               phrases=("in order to",)) -> dict:
        return {"family_id": family_id, "evidence_tier": tier, "discovery_phrases": list(phrases)}

    @staticmethod
    def sentence(words: int, marker: str = "in order to") -> str:
        # Distinct filler words, so the five-gram set is as large as the text
        # and one changed word moves the Jaccard similarity by a known amount.
        filler = [f"w{n}" for n in range(words - 3)]
        return " ".join([marker, *filler]) + "."

    def test_candidates_are_ordered_by_the_seed_digest(self):
        texts = [self.sentence(30) + f" variant {n}" for n in range(6)]
        documents = [self.document(text, path=f"docs/{n}.md") for n, text in enumerate(texts)]
        candidates, rejections = collector.build_candidates(
            [self.family()], documents, "", {1298}, set(), set())
        self.assertEqual(rejections, [])
        self.assertEqual(len(candidates), 6)
        digests = [row["candidate_id"] for row in candidates]
        self.assertEqual(digests, sorted(digests))
        for row in candidates:
            expected = hashlib.sha256(
                (collector.FIXTURE_SEED + row["source_url"] + row["text"]).encode("utf-8")
            ).hexdigest()
            self.assertEqual(row["candidate_id"], expected)
        # The order is the digest's and not the documents', so a candidate
        # cannot be moved up by renaming or reordering its source.
        self.assertNotEqual([row["source_path"] for row in candidates],
                            [f"docs/{n}.md" for n in range(6)])

    def test_a_v1_source_group_is_excluded_whole(self):
        v1_document = ("wildcat-finance/skills", "docs/compound-v3-phase0-study.md")
        v1_commit = ("wildcat-finance/skills", "2" * 40)
        document = self.document(self.sentence(40), path=v1_document[1])
        self.assertEqual(
            collector.document_rejection(document, {1298}, {v1_document}, {v1_commit}),
            "v1-source-group",
        )
        commit = {**self.document(self.sentence(40)), "kind": "commit_message",
                  "path": None, "commit": v1_commit[1]}
        self.assertEqual(
            collector.document_rejection(commit, {1298}, {v1_document}, {v1_commit}),
            "v1-source-group",
        )
        other = self.document(self.sentence(40), path="docs/other.md")
        self.assertIsNone(collector.document_rejection(other, {1298}, {v1_document}, {v1_commit}))
        # The v1 label, adjudication and split files are refused by name: only
        # the sample file may be opened while specimens are chosen.
        with tempfile.TemporaryDirectory() as directory:
            labels = Path(directory) / "labels.jsonl"
            labels.write_text("", encoding="utf-8")
            with self.assertRaises(collector.RefusalError):
                collector.v1_exclusions(labels)

    def test_a_paragraph_outside_the_word_band_is_rejected(self):
        self.assertEqual(collector.paragraph_rejection(self.sentence(17), ""), "outside-word-band")
        self.assertEqual(collector.paragraph_rejection(self.sentence(181), ""), "outside-word-band")
        self.assertIsNone(collector.paragraph_rejection(self.sentence(18), ""))
        self.assertIsNone(collector.paragraph_rejection(self.sentence(180), ""))

    def annotate(self, candidate: dict, specimen_id: str) -> dict:
        return {
            "candidate_id": candidate["candidate_id"], "family_id": candidate["family_id"],
            "specimen_id": specimen_id, "polarity": "negative", "decision": "negative",
            "reason": "a negative", "rewrite": None, "start_byte": 0, "end_byte": 11,
        }

    def test_a_fivegram_jaccard_duplicate_at_the_limit_is_rejected(self):
        base = self.sentence(40)
        near = base.replace(" w36.", " other.")
        far = self.sentence(40).replace("w", "t")
        family = self.family(tier="high-value")
        grams_base = collector.fivegrams(collector.normalise(base))
        self.assertGreaterEqual(
            collector.jaccard(grams_base, collector.fivegrams(collector.normalise(near))),
            collector.JACCARD_LIMIT,
        )
        self.assertLess(
            collector.jaccard(grams_base, collector.fivegrams(collector.normalise(far))),
            collector.JACCARD_LIMIT,
        )
        for other, expected_kept, expected_reasons in (
            (near, 1, ["duplicate-fivegram-jaccard"]),
            (far, 2, []),
        ):
            documents = [self.document(base, path="docs/a.md"), self.document(other, path="docs/b.md")]
            candidates, _ = collector.build_candidates([family], documents, "", {1298}, set(), set())
            annotations = {
                (row["family_id"], row["candidate_id"]): self.annotate(row, f"purpose_periphrasis-neg-0{n}")
                for n, row in enumerate(candidates, 1)
            }
            specimens, rejections, _ = collector.select([family], candidates, annotations, False)
            self.assertEqual(len(specimens), expected_kept, other)
            self.assertEqual([row["reason"] for row in rejections], expected_reasons, other)
            if expected_reasons:
                self.assertIn("five-gram Jaccard", rejections[0]["detail"])

    def test_a_surplus_negative_is_kept_in_the_rejections_not_the_fixture(self):
        family = self.family(tier="signal")
        texts = [self.sentence(40).replace("w", f"t{n}") for n in range(3)]
        documents = [self.document(text, path=f"docs/{n}.md") for n, text in enumerate(texts)]
        candidates, _ = collector.build_candidates([family], documents, "", {1298}, set(), set())
        annotations = {
            (row["family_id"], row["candidate_id"]): self.annotate(row, f"purpose_periphrasis-neg-0{n}")
            for n, row in enumerate(candidates, 1)
        }
        specimens, rejections, shortfalls = collector.select([family], candidates, annotations, False)
        self.assertEqual(len(specimens), 1)
        self.assertEqual([row["reason"] for row in rejections], ["minimum-already-met"] * 2)
        self.assertEqual(len(shortfalls), 1)
        self.assertEqual(shortfalls[0]["negatives"], 1)
        self.assertEqual(shortfalls[0]["independent_positives"], 0)

    def test_the_fixture_is_written_through_a_temporary_file_and_rename(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "specimens.jsonl"
            target.write_text('{"previous": true}\n', encoding="utf-8")
            calls = []
            real_replace = os.replace

            def recording_replace(source, destination):
                calls.append((Path(source).name, Path(destination).name))
                return real_replace(source, destination)

            collector.os.replace = recording_replace
            try:
                collector.write_jsonl_atomic(target, [{"a": 1}, {"b": 2}])
            finally:
                collector.os.replace = real_replace
            self.assertEqual(calls, [("specimens.jsonl.partial", "specimens.jsonl")])
            self.assertEqual(target.read_text(encoding="utf-8"), '{"a": 1}\n{"b": 2}\n')
            self.assertEqual(sorted(path.name for path in Path(directory).iterdir()), ["specimens.jsonl"])

            def failing_replace(source, destination):
                raise OSError("interrupted before the rename")

            collector.os.replace = failing_replace
            try:
                with self.assertRaises(OSError):
                    collector.write_jsonl_atomic(target, [{"c": 3}])
            finally:
                collector.os.replace = real_replace
            # The previous fixture survives an interrupted write intact.
            self.assertEqual(target.read_text(encoding="utf-8"), '{"a": 1}\n{"b": 2}\n')

    def test_refuses_to_run_without_a_pinned_head(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            (fixture / "families.jsonl").write_text(jsonl([FAMILY_ROW]), encoding="utf-8")
            (fixture / "issue-1298.md").write_text("", encoding="utf-8")
            samples = fixture / "samples.jsonl"
            samples.write_text("", encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(COLLECTOR), "--fixture", str(fixture),
                 "--v1-samples", str(samples), "--corpus-in", str(samples)],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertIn("--head is required", completed.stderr)
            self.assertFalse((fixture / "specimens.jsonl").exists())
            self.assertFalse((fixture / "selection-rejections.jsonl").exists())
            # A head that is not one repository=commit pair is refused the same way.
            completed = subprocess.run(
                [sys.executable, str(COLLECTOR), "--fixture", str(fixture),
                 "--v1-samples", str(samples), "--corpus-in", str(samples),
                 "--head", "wildcat-finance/skills=main"],
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(completed.returncode, 2, completed.stderr)
            self.assertIn("unusable pinned commit", completed.stderr)

    def test_the_commit_half_of_the_universe_can_actually_be_fetched(self):
        """`commit_detail` was called three times and defined nowhere.

        `fetch_commits`, `fetch_origin` and `replay` each read a commit
        through it, so the collector raised `NameError: name 'commit_detail'
        is not defined` the moment it reached a commit -- which is every run,
        because the commit messages of all twenty pinned heads are half the
        universe. Nothing failed until the network pass ran, and the pass
        discarded every document already fetched when it did. This drives
        `fetch_commits` against a stub `gh`, which is the call that raised.
        """
        page = json.dumps([
            {"sha": "a" * 40,
             "commit": {"message": "One commit message.\n\nWildcat-Origin: shoggoth",
                        "committer": {"date": "2026-01-02T03:04:05Z"}}},
        ])
        env = self.counting_gh(
            'printf "x\\n" >> "$FAMILY_EVIDENCE_COUNT"\n'
            'if [ -f "$FAMILY_EVIDENCE_COUNT.page1" ]; then\n'
            '  printf "%s\\n" "[]"\n'
            "else\n"
            '  : > "$FAMILY_EVIDENCE_COUNT.page1"\n'
            '  printf "%s\\n" "$FAMILY_EVIDENCE_PAGE"\n'
            "fi\n"
        )
        env["FAMILY_EVIDENCE_PAGE"] = page
        with unittest.mock.patch.dict(os.environ, env, clear=True):
            commits = collector.fetch_commits("wildcat-finance/skills", "b" * 40)
        self.assertEqual(len(commits), 1)
        self.assertEqual(commits[0]["sha"], "a" * 40)
        self.assertEqual(commits[0]["date"], "2026-01-02T03:04:05Z")
        self.assertEqual(collector.origin_from(commits[0]["message"], commits[0]["date"]),
                         "model_assisted")

    def test_commit_detail_reads_a_reply_it_cannot_trust(self):
        """The reply is outside data, so a wrong type reads as absent."""
        self.assertEqual(
            collector.commit_detail(
                {"commit": {"message": "m", "committer": {"date": "2020-01-01T00:00:00Z"}}}),
            ("m", "2020-01-01T00:00:00Z"),
        )
        for reply in (
            None, [], "commit", {}, {"commit": None}, {"commit": []},
            {"commit": {"message": 7, "committer": {"date": 7}}},
            {"commit": {"committer": "2020"}},
        ):
            self.assertEqual(collector.commit_detail(reply), (None, None), reply)
        # A reply carrying no date still yields its message, because the
        # origin rule falls back to unknown rather than refusing the commit.
        self.assertEqual(collector.commit_detail({"commit": {"message": "m"}}), ("m", None))

    def test_an_invented_corpus_is_not_shipped_prose(self):
        """`plugins/lemma/baseline/` says of itself that its prose is invented.

        Its README reads "A small invented corpus", "Everything here is
        fabricated for the purpose" and "None of it corresponds to a deployed
        system, and the prose is written to be chunked rather than to be
        read." A specimen taken there would be evidence of writing nobody
        published, and two of its paragraphs did reach the candidate pool.
        """
        text = self.sentence(30)
        rejected = self.document(text, path="plugins/lemma/baseline/docs/reference/errors.md")
        kept = self.document(text + " kept", path="plugins/lemma/docs/design.md")
        candidates, rejections = collector.build_candidates(
            [self.family()], [rejected, kept], "", {1298}, set(), set())
        self.assertEqual([row["reason"] for row in rejections], ["invented-corpus"])
        self.assertEqual([row["source_path"] for row in candidates],
                         ["plugins/lemma/docs/design.md"])
        self.assertIn("invented-corpus", collector.REJECTION_REASONS)
        # The exclusion is named by repository and prefix, so an unrelated
        # directory called `baseline` in another repository still counts.
        elsewhere = self.document(text, path="baseline/notes.md",
                                  repository="wildcat-finance/wildcat-docs")
        candidates, rejections = collector.build_candidates(
            [self.family()], [elsewhere], "", {1298}, set(), set())
        self.assertEqual(rejections, [])
        self.assertEqual(len(candidates), 1)

    def counting_gh(self, script: str) -> dict:
        """A `gh` on PATH that counts its own invocations and opens no socket.

        The counter file and the reply come from the environment, so no test
        value reaches the generated shell script's quoting.
        """
        directory = Path(tempfile.mkdtemp(prefix="family-evidence-retry-"))
        self.addCleanup(shutil.rmtree, directory, True)
        stub = directory / "gh"
        stub.write_text("#!/bin/sh\n" + script, encoding="utf-8")
        stub.chmod(0o755)
        return dict(
            os.environ,
            PATH=str(directory),
            FAMILY_EVIDENCE_COUNT=str(directory / "count"),
        )

    @staticmethod
    def gh_attempts(env: dict) -> int:
        path = Path(env["FAMILY_EVIDENCE_COUNT"])
        return len(path.read_text(encoding="utf-8").splitlines()) if path.exists() else 0

    def test_a_transient_gh_answer_is_retried_rather_than_ending_the_pass(self):
        """One HTTP 504 at document 900 of 1370 discarded the whole pass.

        The universe is fetched in a single pass of a few thousand calls and
        the corpus is written only when it completes, so one transient answer
        cost every document already fetched. The reproduction is the stub
        below: it answers `HTTP 504` twice and then succeeds, which refused
        before this guard and now returns the body on the third attempt.
        """
        env = self.counting_gh(
            # Only shell built-ins and redirects: PATH holds this stub alone,
            # so `wc` and `tr` are not reachable from here.
            'printf "x\\n" >> "$FAMILY_EVIDENCE_COUNT"\n'
            'for attempt in 1 2; do\n'
            '  if [ ! -f "$FAMILY_EVIDENCE_COUNT.$attempt" ]; then\n'
            '    : > "$FAMILY_EVIDENCE_COUNT.$attempt"\n'
            '    echo "gh: We couldn\'t respond to your request in time. (HTTP 504)" >&2\n'
            "    exit 1\n"
            "  fi\n"
            "done\n"
            'printf "%s\\n" "{}"\n'
        )
        with unittest.mock.patch.object(collector, "GH_RETRY_SECONDS", 0), \
                unittest.mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(collector.gh_fetch(["api", "repos/a/b"]), b"{}\n")
        self.assertEqual(self.gh_attempts(env), 3)

    def test_a_transient_answer_on_every_attempt_is_still_a_refusal(self):
        env = self.counting_gh(
            'printf "x\\n" >> "$FAMILY_EVIDENCE_COUNT"\n'
            'echo "gh: rate limited (HTTP 429)" >&2\n'
            "exit 1\n"
        )
        with unittest.mock.patch.object(collector, "GH_RETRY_SECONDS", 0), \
                unittest.mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(collector.RefusalError) as caught:
                collector.gh_fetch(["api", "repos/a/b"])
        self.assertIn(f"on {collector.GH_ATTEMPTS} attempts", str(caught.exception))
        self.assertEqual(self.gh_attempts(env), collector.GH_ATTEMPTS)

    def test_a_failure_that_is_not_transient_is_not_retried(self):
        """A retry that widened to every failure would hide a real refusal.

        An unauthorised or malformed call is answered the same way every time,
        so retrying it buys nothing and delays the refusal by three waits. The
        decision reads GitHub's own status line and nothing else.
        """
        env = self.counting_gh(
            'printf "x\\n" >> "$FAMILY_EVIDENCE_COUNT"\n'
            'echo "gh: Bad credentials (HTTP 401)" >&2\n'
            "exit 1\n"
        )
        with unittest.mock.patch.object(collector, "GH_RETRY_SECONDS", 0), \
                unittest.mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(collector.RefusalError) as caught:
                collector.gh_fetch(["api", "repos/a/b"])
        self.assertIn("HTTP 401", str(caught.exception))
        self.assertNotIn("attempts", str(caught.exception))
        self.assertEqual(self.gh_attempts(env), 1)

    def test_a_missing_thread_is_not_retried_either(self):
        """The thread enumeration counts a 404 as a hole, on one call."""
        env = self.counting_gh(
            'printf "x\\n" >> "$FAMILY_EVIDENCE_COUNT"\n'
            'echo "gh: Not Found (HTTP 404)" >&2\n'
            "exit 1\n"
        )
        with unittest.mock.patch.object(collector, "GH_RETRY_SECONDS", 0), \
                unittest.mock.patch.dict(os.environ, env, clear=True):
            self.assertIsNone(collector.gh_fetch_optional(["api", "repos/a/b/issues/1"]))
            with self.assertRaises(collector.RefusalError):
                collector.gh_fetch(["api", "repos/a/b/issues/1"])
        self.assertEqual(self.gh_attempts(env), 2)

    def test_a_tree_path_cannot_reach_the_contents_endpoint_unchecked(self):
        """S3-R1-01. The tree listing is outside data and its paths are gated.

        `fetch_tree` returns whatever paths the repository holds, and
        `corpus_from_network` handed them straight to `fetch_document`, which
        interpolated them into `repos/<r>/contents/<path>?ref=<commit>`. The
        first pass really did send `docs/Scale Factor.md` with a literal space
        in the request line. A git path may also carry `?`, `#` or `&`, and
        `docs/x?ref=main&z=.md` would have moved the fetch off the pinned
        commit onto a branch that moves, which is the one property the whole
        selection rests on.
        """
        for path in ("docs/Scale Factor.md", "docs/x?ref=main&z=.md",
                     "docs/a#b.md", ".agents/skills/promise-machine/SKILL.md",
                     "../etc/passwd.md"):
            self.assertFalse(collector.endpoint_path_ok(path), path)
            with self.assertRaises(collector.RefusalError, msg=path):
                collector.fetch_document("wildcat-finance/skills", "0" * 40, path)
        self.assertTrue(collector.endpoint_path_ok("docs/hooks/templates/access.md"))

    def test_an_unfetchable_tree_path_is_recorded_rather_than_requested(self):
        """The document stays in the record; only the request is dropped.

        Skipping the fetch must not skip the document, or the rejection file
        would stop saying that the tree held it.
        """
        tree = ["docs/good.md", ".githooks/README.md", "docs/Scale Factor.md"]
        requested = []

        def stub_document(repository, commit, path):
            requested.append(path)
            return self.sentence(30)

        arguments = collector.argparse.Namespace(
            head=[("wildcat-finance/skills", "1" * 40)], threads=set())
        with unittest.mock.patch.object(collector, "fetch_tree", lambda *_: tree), \
                unittest.mock.patch.object(collector, "fetch_commits", lambda *_: []), \
                unittest.mock.patch.object(collector, "fetch_document", stub_document):
            documents = collector.corpus_from_network(arguments)
        self.assertEqual(requested, ["docs/good.md"])
        self.assertEqual([row["path"] for row in documents], tree)
        self.assertEqual([row["text"] for row in documents][1:], ["", ""])

    def test_a_dot_prefixed_path_is_not_recorded_as_carrying_whitespace(self):
        """S3-R1-02. Four of the six rows the first pass wrote were mislabelled.

        `.agents/...` and `.githooks/...` are refused because an endpoint
        segment may not begin with a dot, and they carry no whitespace at all.
        A reader reproducing the selection from `path-carries-whitespace`
        would look for a space and find none, so the two faults carry two
        reasons and `selection-rejections.jsonl` was relabelled to match.
        """
        for path in (".agents/skills/promise-machine/SKILL.md", ".githooks/README.md",
                     "tests/fixtures/promise-machine/unresolved-router/"
                     ".agents/skills/promise-machine/SKILL.md"):
            self.assertFalse(any(character.isspace() for character in path), path)
            self.assertEqual(
                collector.document_rejection(self.document("", path=path), {1298}, set(), set()),
                "unusable-source-path", path)
        for path in ("docs/Scale Factor.md", "docs/hooks/templates/Access Control Hooks.md"):
            self.assertEqual(
                collector.document_rejection(self.document("", path=path), {1298}, set(), set()),
                "path-carries-whitespace", path)
        for reason in ("unusable-source-path", "path-carries-whitespace"):
            self.assertIn(reason, collector.REJECTION_REASONS)
        # The shipped record carries the same split, so the reason a reader
        # reads is the fault the collector found.
        recorded = [
            json.loads(line)
            for line in (FIXTURE / "selection-rejections.jsonl").read_text(
                encoding="utf-8").splitlines()
            if line.strip()
        ]
        split = {
            row["source_path"]: row["reason"]
            for row in recorded
            if row["reason"] in ("unusable-source-path", "path-carries-whitespace")
        }
        self.assertEqual(len(split), 6)
        for path, reason in split.items():
            self.assertEqual(
                reason,
                "path-carries-whitespace" if any(c.isspace() for c in path)
                else "unusable-source-path", path)

    def test_a_tier_with_no_minimum_still_records_its_candidates(self):
        """S3-R1-03. A zero-minimum family left the walk without a row.

        `boundary`, `existing-family` and `future` ship nothing, and their
        candidates used to leave `select` before any rejection was written.
        The rejection file is silent about them today only because no such
        family records a discovery phrase; the moment one does, the file has
        to say the candidate was seen and why it was not taken.
        """
        for tier in ("boundary", "existing-family", "future"):
            family = self.family(family_id="broad_fact_clause", tier=tier)
            documents = [self.document(self.sentence(40), path=f"docs/{n}.md") for n in range(3)]
            candidates, _ = collector.build_candidates(
                [family], documents, "", {1298}, set(), set())
            self.assertEqual(len(candidates), 3, tier)
            specimens, rejections, shortfalls = collector.select(
                [family], candidates, {}, False)
            self.assertEqual(specimens, [], tier)
            self.assertEqual(shortfalls, [], tier)
            self.assertEqual([row["reason"] for row in rejections],
                             ["tier-has-no-minimum"] * 3, tier)
            self.assertEqual({row["candidate_id"] for row in rejections},
                             {row["candidate_id"] for row in candidates}, tier)
        self.assertIn("tier-has-no-minimum", collector.REJECTION_REASONS)

    def test_a_recorded_corpus_is_read_back_against_its_own_digest(self):
        """S3-R1-04. `--corpus-in` is an ingestion path and had no test.

        The recorded universe is read back the way any other outside input is.
        Its stored digest sits beside the text in the same file, so it catches
        a corrupted or truncated row and not a deliberate edit that recomputes
        the digest; a shipped row's provenance rests on the per-specimen
        replay, which `--no-verify` skips, so on that path the digest is the
        whole check.
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.jsonl"
            documents = [self.document("first text"),
                         self.document("second text", path="docs/b.md")]
            collector.write_corpus(path, documents)
            read = collector.read_corpus(path)
            self.assertEqual([row["text"] for row in read], ["first text", "second text"])
            self.assertEqual(read[0]["text_sha256"], hashlib.sha256(b"first text").hexdigest())
            rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
            rows[1]["text"] = "second text, edited after the digest was taken"
            path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                            encoding="utf-8")
            with self.assertRaises(collector.RefusalError) as caught:
                collector.read_corpus(path)
            self.assertIn("does not match its digest", str(caught.exception))
            for body, expected in (
                ("{not json}\n", "unreadable JSON"),
                ('["a list"]\n', "is not an object"),
                ('{"text": "t"}\n', "carries no text and digest"),
                ('{"text_sha256": "' + "0" * 64 + '"}\n', "carries no text and digest"),
            ):
                path.write_text(body, encoding="utf-8")
                with self.assertRaises(collector.RefusalError) as caught:
                    collector.read_corpus(path)
                self.assertIn(expected, str(caught.exception), body)
            link = Path(directory) / "link.jsonl"
            link.symlink_to(path)
            with self.assertRaises(collector.RefusalError) as caught:
                collector.read_corpus(link)
            self.assertIn("symlink refused", str(caught.exception))

    def test_an_annotation_record_that_cannot_be_keyed_is_refused(self):
        """S3-R1-04. `--annotations` is the other untested ingestion path.

        One paragraph can be a candidate for two families and carry two
        different annotations, so the key is the pair. A record naming no
        family, or naming the same pair twice, is refused rather than guessed:
        guessing would ship one annotation's span under the other's polarity.
        """
        good = {"candidate_id": "a" * 64, "family_id": "purpose_periphrasis"}
        other = {"candidate_id": "a" * 64, "family_id": "reason_is_because"}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "annotations.jsonl"

            def write(rows):
                path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")

            write([good, other])
            keyed = collector.read_annotations(path)
            self.assertEqual(sorted(keyed), [("purpose_periphrasis", "a" * 64),
                                             ("reason_is_because", "a" * 64)])
            for rows, expected in (
                ([good, good], "repeats"),
                ([{"family_id": "purpose_periphrasis"}], "names no candidate_id"),
                ([{"candidate_id": "a" * 64}], "names no family_id"),
                ([{"candidate_id": 7, "family_id": "x"}], "names no candidate_id"),
                (["not an object"], "is not an object"),
            ):
                write(rows)
                with self.assertRaises(collector.RefusalError) as caught:
                    collector.read_annotations(path)
                self.assertIn(expected, str(caught.exception), rows)
            path.write_text("{not json}\n", encoding="utf-8")
            with self.assertRaises(collector.RefusalError) as caught:
                collector.read_annotations(path)
            self.assertIn("unreadable JSON", str(caught.exception))
            link = Path(directory) / "link.jsonl"
            link.symlink_to(path)
            with self.assertRaises(collector.RefusalError) as caught:
                collector.read_annotations(link)
            self.assertIn("symlink refused", str(caught.exception))

    def test_fetch_origin_gates_its_own_endpoint_values(self):
        """S3-R1-05. One endpoint builder took its values on trust.

        `fetch_origin` interpolated `repository`, `commit` and `path` into
        `repos/<r>/commits?sha=<c>&path=<p>` without calling `segment`. It was
        safe only because `build_specimen` runs `replay`, which gates the same
        three values, first; a second caller would not inherit that order, and
        the module's own rule is that every value is gated where the endpoint
        is built. Each bad value is refused before any `gh` call is made.
        """
        with unittest.mock.patch.object(collector, "gh_json") as fetched:
            for repository, commit, path in (
                ("other-org/repo", "1" * 40, "docs/a.md"),
                ("wildcat-finance/skills", "main", "docs/a.md"),
                ("wildcat-finance/skills", "1" * 40, "docs/x?ref=main&z=.md"),
                ("wildcat-finance/skills", "1" * 40, "docs/Scale Factor.md"),
            ):
                with self.assertRaises(collector.RefusalError, msg=(repository, commit, path)):
                    collector.fetch_origin(repository, commit, path)
            fetched.assert_not_called()
            fetched.return_value = [
                {"commit": {"message": "m\n\nWildcat-Origin: shoggoth",
                            "committer": {"date": "2026-01-02T03:04:05Z"}}}
            ]
            self.assertEqual(
                collector.fetch_origin("wildcat-finance/skills", "1" * 40, "docs/a.md"),
                "model_assisted")
            fetched.assert_called_once_with(
                ["api", "repos/wildcat-finance/skills/commits?sha=" + "1" * 40
                 + "&path=docs/a.md&per_page=1"])


if __name__ == "__main__":
    unittest.main()
