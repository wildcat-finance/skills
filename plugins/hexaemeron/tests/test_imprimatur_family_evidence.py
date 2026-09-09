"""Guard the structural-family-evidence-v1 fixture and its checker."""

from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
import unittest


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PLUGIN_ROOT / "skills" / "imprimatur"
SCRIPT = SKILL_ROOT / "scripts" / "check_family_evidence.py"
FIXTURE = SKILL_ROOT / "evals" / "structural-family-evidence-v1"
SCHEMAS = FIXTURE / "schemas"
ISSUE = FIXTURE / "issue-1298.md"
README = FIXTURE / "README.md"

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

    def build_fixture(self, families=None, specimens=None, root=None) -> Path:
        """Write a throwaway fixture; the shipped one is never mutated."""
        if root is None:
            root = Path(tempfile.mkdtemp(prefix="family-evidence-"))
            self.addCleanup(self.remove_tree, root)
        (root / "schemas").mkdir(parents=True, exist_ok=True)
        for name in ("family.schema.json", "specimen.schema.json"):
            (root / "schemas" / name).write_bytes((SCHEMAS / name).read_bytes())
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
        self.assertEqual(len(payload["below_minimum"]), 13)


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
        minimums = {
            "high-value": (2, 2),
            "signal": (2, 1),
            "boundary": (0, 0),
            "existing-family": (0, 0),
            "future": (0, 0),
        }
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

    def test_readme_frozen_digests_match_the_current_files(self):
        table = re.findall(
            r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$",
            README.read_text(encoding="utf-8"),
            flags=re.M,
        )
        self.assertEqual(len(table), 5)
        for relative, expected in table:
            blob = (SKILL_ROOT / relative).read_bytes()
            self.assertEqual(hashlib.sha256(blob).hexdigest(), expected, relative)


if __name__ == "__main__":
    unittest.main()
