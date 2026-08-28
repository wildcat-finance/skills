import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run_observation.py"
REPORTER_SCRIPT = ROOT / "tests" / "emit_run_observation_report.py"
SCHEMA = ROOT / "schemas" / "promise-machine-run-observation-v1.schema.json"
FIXTURES = ROOT / "tests" / "fixtures" / "run-observation"
CONTRACT = "promise-machine-run-observation/v1"
ADR_014 = ROOT / "docs" / "decisions" / "ADR-014-reallocate-the-live-wave-atlas-from-a-complete-census.md"
ADR_015 = ROOT / "docs" / "decisions" / "ADR-015-define-the-promise-machine-run-observation-record.md"
AUDIT_LOG = ROOT / "audit" / "AUDIT.md"


def scratch_directory(prefix="run-observation-"):
    """A transient in-repository directory that `git status` never sees.

    The validator and writers confine paths under the repository root, so
    scratch space must stay inside it -- but a temporary directory under the
    tracked fixture tree (or the repository top level) makes the repository
    non-quiescent while a case runs, and the disposable-signing guard's
    outer-stability assertion races against it under parallel shards.  The
    ignored top-level tmp/ satisfies both: confined, and invisible to status.
    """
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)
RUNBOOK = ROOT / "docs" / "promise-machine" / "run-observation-runbook.md"

SPEC = importlib.util.spec_from_file_location("run_observation", SCRIPT)
run_observation = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = run_observation
SPEC.loader.exec_module(run_observation)

REPORTER_SPEC = importlib.util.spec_from_file_location(
    "emit_run_observation_report_for_tests", REPORTER_SCRIPT
)
reporter = importlib.util.module_from_spec(REPORTER_SPEC)
sys.modules[REPORTER_SPEC.name] = reporter
REPORTER_SPEC.loader.exec_module(reporter)


def fixture_events(name="success.jsonl"):
    return [
        json.loads(line)
        for line in (FIXTURES / "valid" / name).read_text(encoding="utf-8").splitlines()
    ]


def write_events(path, events, *, final_newline=True):
    text = "\n".join(json.dumps(item, separators=(",", ":")) for item in events)
    path.write_text(text + ("\n" if final_newline else ""), encoding="utf-8")


def codes(path):
    return {finding.code for finding in run_observation.validate_path(path)}


def run_cli(path, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "check", str(path), *extra],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def run_prefix_cli(path, *extra):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "check-prefix", str(path), *extra],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


class RunObservationSchemaTests(unittest.TestCase):
    def test_observation_decision_is_adr_015_and_adr_014_remains_distinct(self):
        self.assertEqual(
            ADR_015.read_text(encoding="utf-8").splitlines()[0],
            "# ADR-015: Define the Promise Machine run observation record",
        )
        self.assertEqual(
            ADR_014.read_text(encoding="utf-8").splitlines()[0],
            "# ADR-014: Reallocate the live Wave Atlas from a complete census",
        )
        audit = AUDIT_LOG.read_text(encoding="utf-8")
        stale = [
            phrase
            for phrase in (
                "ADR-014 records root Promise Machine ownership",
                "two receipted copies, ADR-014 and the generated Horos boundary",
            )
            if phrase in audit
        ]
        self.assertEqual(
            stale,
            [],
            "observation-record audit history must retain the ADR-015 identity",
        )

    def test_schema_binds_the_contract_and_closed_event_union(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$id"], CONTRACT)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(len(schema["oneOf"]), 7)
        self.assertEqual(
            {
                schema["$defs"][name]["allOf"][1]["properties"]["type"]["const"]
                for name in (
                    "runStarted",
                    "capabilityStarted",
                    "capabilityFinished",
                    "transitionRefused",
                    "retryScheduled",
                    "handoffRecorded",
                    "runFinished",
                )
            },
            run_observation.EVENT_TYPES,
        )
        for name in (
            "runStarted",
            "capabilityStarted",
            "capabilityFinished",
            "transitionRefused",
            "retryScheduled",
            "handoffRecorded",
            "runFinished",
        ):
            self.assertFalse(schema["$defs"][name]["unevaluatedProperties"])

    def test_schema_and_runtime_field_sets_and_enums_agree(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        event_names = {
            "run.started": "runStarted",
            "capability.started": "capabilityStarted",
            "capability.finished": "capabilityFinished",
            "transition.refused": "transitionRefused",
            "retry.scheduled": "retryScheduled",
            "handoff.recorded": "handoffRecorded",
            "run.finished": "runFinished",
        }
        base = schema["$defs"]["eventBase"]
        self.assertEqual(set(base["required"]), run_observation.COMMON_REQUIRED)
        self.assertEqual(
            set(base["properties"]) - set(base["required"]),
            run_observation.COMMON_OPTIONAL,
        )
        for event_type, name in event_names.items():
            event = schema["$defs"][name]["allOf"][1]
            self.assertEqual(
                set(event["required"]), run_observation.EVENT_REQUIRED[event_type]
            )
            self.assertEqual(
                set(event["properties"]) - set(event["required"]) - {"type"},
                run_observation.EVENT_OPTIONAL[event_type],
            )
        self.assertEqual(
            set(schema["$defs"]["evidenceClass"]["enum"]),
            run_observation.EVIDENCE_CLASSES,
        )
        self.assertEqual(
            set(schema["$defs"]["runFinished"]["allOf"][1]["properties"]["status"]["enum"]),
            run_observation.RUN_STATUSES,
        )
        self.assertEqual(
            set(schema["$defs"]["capabilityFinished"]["allOf"][1]["properties"]["status"]["enum"]),
            run_observation.CAPABILITY_STATUSES,
        )
        self.assertEqual(
            schema["$defs"]["metadata"]["propertyNames"]["maxLength"],
            run_observation.MAX_STRING,
        )
        self.assertEqual(
            schema["$defs"]["metadata"]["propertyNames"].get("pattern"),
            run_observation.UNKNOWN_FIELD_RE.pattern,
        )
        self.assertEqual(
            schema["$defs"]["metadata"]["additionalProperties"].get("maxLength"),
            run_observation.MAX_STRING,
        )
        self.assertEqual(
            Decimal(str(schema["$defs"]["metadata"]["additionalProperties"]["maximum"])),
            run_observation.MAX_FINITE_NUMBER,
        )
        integer_fields = (
            schema["$defs"]["eventBase"]["properties"]["sequence"],
            schema["$defs"]["tokenUsage"]["properties"]["input_tokens"],
            schema["$defs"]["tokenUsage"]["properties"]["output_tokens"],
            schema["$defs"]["capabilityFinished"]["allOf"][1]["properties"]["duration_ms"],
            schema["$defs"]["retryScheduled"]["allOf"][1]["properties"]["attempt"],
            schema["$defs"]["retryScheduled"]["allOf"][1]["properties"]["after_ms"],
            schema["$defs"]["runFinished"]["allOf"][1]["properties"]["duration_ms"],
        )
        self.assertTrue(
            all(
                Decimal(str(field["maximum"])) == run_observation.MAX_FINITE_NUMBER
                for field in integer_fields
            )
        )
        inferred = schema["$defs"]["evidence"]["allOf"][0]
        self.assertEqual(
            inferred["if"]["properties"]["evidence_class"]["const"],
            "inferred",
        )
        self.assertEqual(inferred["then"]["required"], ["selector"])
        self.assertEqual(
            set(schema["$defs"]["runContext"]["required"]),
            {"issue_or_topic", "step", "role", "selected_skill", "promise_id"},
        )
        self.assertFalse(schema["$defs"]["runContext"]["additionalProperties"])
        self.assertEqual(
            set(schema["$defs"]["repositoryBefore"]["required"]),
            {"path", "before_commit"},
        )
        self.assertEqual(
            set(schema["$defs"]["repositoryAfter"]["required"]),
            {"path", "before_commit", "after_commit"},
        )

    def test_schema_and_runtime_placeholder_rules_agree(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            schema["$defs"]["identity"]["pattern"],
            run_observation.ID_RE.pattern,
        )
        self.assertEqual(
            schema["$defs"]["boundedString"]["pattern"],
            run_observation.OBSERVED_STRING_RE.pattern,
        )
        self.assertEqual(
            schema["$defs"]["repositoryBefore"]["properties"]["path"]["pattern"],
            run_observation.REPOSITORY_PATH_RE.pattern,
        )
        self.assertEqual(
            schema["$defs"]["repositoryBefore"]["properties"]["path"]["x-unicode-normalization"],
            run_observation.REPOSITORY_PATH_NORMALIZATION,
        )
        self.assertEqual(
            schema["$defs"]["repositoryAfter"]["properties"]["path"]["$ref"],
            "#/$defs/repositoryBefore/properties/path",
        )
        self.assertEqual(
            schema["$defs"]["eventBase"]["properties"]["time"]["pattern"],
            run_observation.TIME_RE.pattern,
        )
        time_pattern = schema["$defs"]["eventBase"]["properties"]["time"]["pattern"]
        for non_profile_time in (
            "2016-12-31T23:59:60Z",
            "2026-13-01T00:00:00Z",
            "2026-08-23T24:00:00Z",
        ):
            self.assertIsNone(re.fullmatch(time_pattern, non_profile_time))
        self.assertEqual(
            schema["$defs"]["unknown"]["properties"]["field"]["allOf"][1]["pattern"],
            run_observation.UNKNOWN_FIELD_RE.pattern,
        )

    def test_schema_and_runtime_reject_impossible_civil_dates(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        pattern = schema["$defs"]["eventBase"]["properties"]["time"]["pattern"]
        self.assertEqual(pattern, run_observation.TIME_RE.pattern)
        for value in (
            "0000-01-01T00:00:00Z",
            "1900-02-29T00:00:00Z",
            "2026-02-29T00:00:00Z",
            "2026-02-30T00:00:00Z",
            "2026-04-31T00:00:00Z",
        ):
            with self.subTest(value=value):
                self.assertIsNone(re.fullmatch(pattern, value))
        for value in (
            "2000-02-29T00:00:00Z",
            "2024-02-29T23:59:59.123456789+14:00",
            "2026-04-30T00:00:00-00:00",
        ):
            with self.subTest(value=value):
                self.assertIsNotNone(re.fullmatch(pattern, value))

    def test_schema_integral_numbers_are_runtime_integers(self):
        with scratch_directory() as directory:
            target = Path(directory) / "integral-numbers.jsonl"
            integer_fields = {
                "sequence",
                "duration_ms",
                "after_ms",
                "attempt",
                "input_tokens",
                "output_tokens",
            }

            def convert(value):
                if isinstance(value, dict):
                    for key, child in value.items():
                        if key in integer_fields and isinstance(child, int):
                            value[key] = float(child)
                        else:
                            convert(child)
                elif isinstance(value, list):
                    for child in value:
                        convert(child)

            for name in ("success.jsonl", "refusal.jsonl", "retry.jsonl", "handoff.jsonl"):
                with self.subTest(name=name):
                    events = fixture_events(name)
                    convert(events)
                    write_events(target, events)
                    self.assertEqual(run_observation.validate_path(target), [])

    def test_non_integral_numbers_do_not_round_into_runtime_integers(self):
        with scratch_directory() as directory:
            target = Path(directory) / "rounded-number.jsonl"
            raw = (FIXTURES / "valid" / "success.jsonl").read_text(encoding="utf-8")
            raw = raw.replace(
                '"input_tokens":10',
                '"input_tokens":9007199254740993.1',
            )
            target.write_text(raw, encoding="utf-8")
            self.assertIn("RO016", codes(target))

    def test_exact_decimal_parser_is_total_and_matches_the_numeric_ceiling(self):
        with scratch_directory() as directory:
            target = Path(directory) / "numbers.jsonl"
            raw = (FIXTURES / "valid" / "success.jsonl").read_text(encoding="utf-8")
            cases = (
                raw.replace(
                    '"subject":"fixture-success"',
                    '"subject":"fixture-success","metadata":{"temperature":1e309}',
                    1,
                ),
                raw.replace('"input_tokens":10', '"input_tokens":1e309', 1),
                raw.replace(
                    '"subject":"fixture-success"',
                    '"subject":"fixture-success","metadata":{"temperature":1e999999999999999999999999999999999}',
                    1,
                ),
                raw.replace(
                    '"subject":"fixture-success"',
                    '"subject":"fixture-success","metadata":{"quantity":' + "9" * 5_000 + "}",
                    1,
                ),
            )
            for index, record in enumerate(cases):
                with self.subTest(index=index):
                    target.write_text(record, encoding="utf-8")
                    findings = run_observation.validate_path(target)
                    self.assertTrue(findings)
                    self.assertTrue(
                        any(item.code in {"RO004", "RO007", "RO016"} for item in findings)
                    )


class RunObservationValidFlowTests(unittest.TestCase):
    def test_captured_byte_and_stable_path_validation_are_equivalent(self):
        paths = sorted((FIXTURES / "valid").glob("*.jsonl"))
        paths.extend(sorted((FIXTURES / "invalid").glob("*.jsonl")))
        for path in paths:
            display = run_observation.display_path(
                path, run_observation.repository_root()
            )
            with self.subTest(path=path):
                self.assertEqual(
                    run_observation.validate_bytes(
                        path.read_bytes(), display_path=display
                    ),
                    run_observation.validate_path(path),
                )

        prefix = b"".join(
            (FIXTURES / "valid" / "success.jsonl").read_bytes().splitlines(
                keepends=True
            )[:-1]
        )
        with scratch_directory() as directory:
            path = Path(directory) / "captured-prefix.jsonl"
            path.write_bytes(prefix)
            display = run_observation.display_path(
                path, run_observation.repository_root()
            )
            self.assertEqual(
                run_observation.validate_bytes(
                    prefix, display_path=display, allow_prefix=True
                ),
                run_observation.validate_path(path, allow_prefix=True),
            )

    def test_valid_records_are_accepted(self):
        for name in ("success.jsonl", "refusal.jsonl", "retry.jsonl", "handoff.jsonl"):
            with self.subTest(name=name):
                path = FIXTURES / "valid" / name
                self.assertEqual(run_observation.validate_path(path), [])
                completed = run_cli(path)
                self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
                self.assertIn(CONTRACT, completed.stdout)

    def test_recorded_and_unknown_token_cases_are_distinct_and_valid(self):
        success = fixture_events("success.jsonl")
        refusal = fixture_events("refusal.jsonl")
        self.assertEqual(success[2]["token_usage"]["source"], "fixture-host")
        self.assertEqual(refusal[0]["unknowns"][0]["field"], "tokens")
        self.assertNotIn("token_usage", refusal[0])

    def test_all_event_types_have_a_positive_fixture(self):
        observed = set()
        for path in sorted((FIXTURES / "valid").glob("*.jsonl")):
            observed.update(json.loads(line)["type"] for line in path.read_text().splitlines())
        self.assertEqual(observed, run_observation.EVENT_TYPES)

    def test_safe_unfinished_prefix_is_accepted_without_weakening_full_check(self):
        events = fixture_events("success.jsonl")[:-1]
        with scratch_directory() as directory:
            target = Path(directory) / "unfinished.jsonl"
            write_events(target, events)

            self.assertEqual(
                run_observation.validate_path(target, allow_prefix=True), []
            )
            self.assertIn("RO009", codes(target))
            self.assertEqual(run_prefix_cli(target).returncode, 0)
            self.assertEqual(run_cli(target).returncode, 1)

    def test_prefix_still_refuses_an_unclosed_capability(self):
        events = fixture_events("success.jsonl")[:2]
        with scratch_directory() as directory:
            target = Path(directory) / "unclosed-capability.jsonl"
            write_events(target, events)

            findings = run_observation.validate_path(target, allow_prefix=True)
            self.assertIn("RO009", {finding.code for finding in findings})
            self.assertEqual(run_prefix_cli(target).returncode, 1)


class RunObservationRefusalTests(unittest.TestCase):
    def test_issue_acceptance_faults_have_distinct_codes(self):
        expected = {
            "missing-run-id.jsonl": "RO008",
            "bad-order.jsonl": "RO009",
            "unbound-evidence.jsonl": "RO011",
            "strengthened-evidence.jsonl": "RO012",
            "hidden-reasoning.jsonl": "RO013",
        }
        for name, code in expected.items():
            with self.subTest(name=name):
                path = FIXTURES / "invalid" / name
                self.assertIn(code, codes(path))
                self.assertEqual(run_cli(path).returncode, 1)

    def test_text_and_json_use_the_same_finding_objects(self):
        path = FIXTURES / "invalid" / "strengthened-evidence.jsonl"
        findings = run_observation.validate_path(path)
        json_result = run_cli(path, "--json")
        text_result = run_cli(path)
        report = json.loads(json_result.stdout)
        self.assertEqual(report["findings"], run_observation.finding_objects(findings))
        self.assertEqual(text_result.stdout.splitlines(), run_observation.text_lines(findings))
        self.assertFalse(report["ok"])

    def test_optional_host_facts_paths_payloads_and_closed_shapes_refuse(self):
        with scratch_directory() as directory:
            target = Path(directory) / "invalid.jsonl"
            cases = {
                "RO015": lambda events: events[0].update(
                    {"host": {"source": "fixture", "identity": "unknown"}}
                ),
                "RO017": lambda events: events[0].update(
                    {
                        "repository": {
                            "path": "../escape",
                            "before_commit": "1" * 40,
                        }
                    }
                ),
                "RO014": lambda events: events[0].update({"metadata": {"prompt": "raw"}}),
                "RO007": lambda events: events[0].update({"undeclared": "value"}),
            }
            for expected, mutate in cases.items():
                with self.subTest(expected=expected):
                    events = fixture_events()
                    mutate(events)
                    write_events(target, events)
                    self.assertIn(expected, codes(target))

    def test_metadata_keys_name_observable_facts_and_redact_forbidden_names(self):
        cases = (
            ("", "RO007"),
            ("---", "RO007"),
            ("___", "RO007"),
            ("💣", "RO007"),
            ("input", "RO014"),
            ("request", "RO014"),
            ("response", "RO014"),
            ("message", "RO014"),
            ("result", "RO014"),
            ("env", "RO014"),
            ("cookies", "RO014"),
            ("analysis", "RO013"),
            ("scratchpad", "RO013"),
            ("deliberation", "RO013"),
            ("innerMonologue", "RO013"),
            ("internalMonologue", "RO013"),
            ("analysisText", "RO013"),
            ("scratchpadContent", "RO013"),
            ("deliberationNotes", "RO013"),
            ("internalMonologueBuffer", "RO013"),
            ("textAnalysis", "RO013"),
            ("COTBuffer", "RO013"),
            ("developerDirective", "RO014"),
            ("instructionSet", "RO014"),
            ("instructionsText", "RO014"),
            ("directiveSet", "RO014"),
            ("cognitiveProcess", "RO013"),
            ("prоmpt", "RO007"),
        )
        with scratch_directory() as directory:
            target = Path(directory) / "metadata-names.jsonl"
            for name, expected in cases:
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: "opaque"}
                    write_events(target, events)
                    findings = run_observation.validate_path(target)
                    self.assertIn(expected, {item.code for item in findings})
                    if expected in {"RO013", "RO014"}:
                        self.assertNotIn(name, "\n".join(item.path for item in findings))

    def test_hidden_work_descriptors_remain_bounded_metadata(self):
        with scratch_directory() as directory:
            target = Path(directory) / "safe-hidden-descriptors.jsonl"
            for name, value in (
                ("analysisCount", 2),
                ("scratchpad_digest", "4" * 64),
                ("deliberationFormat", "json"),
                ("internalMonologueStatus", "absent"),
                ("chainOfThoughtPresent", False),
                ("COTCount", 0),
                ("analysisdigest", "4" * 64),
                ("promptcount", 2),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: value}
                    write_events(target, events)
                    self.assertEqual(codes(target), set())

    def test_safe_descriptor_suffixes_require_descriptor_values(self):
        with scratch_directory() as directory:
            target = Path(directory) / "descriptor-values.jsonl"
            for name, value in (
                ("promptCount", "the complete raw prompt text"),
                ("assistantOutputDigest", "raw assistant output"),
                ("reasoningPresent", "full hidden reasoning"),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: value}
                    write_events(target, events)
                    self.assertTrue({"RO013", "RO014"} & codes(target))

    def test_raw_content_names_refuse_but_typed_descriptors_remain_bounded(self):
        with scratch_directory() as directory:
            target = Path(directory) / "round6-names.jsonl"
            for name in (
                "content",
                "contents",
                "contentText",
                "content_body",
                "contentData",
                "contentValue",
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: "raw payload bytes"}
                    write_events(target, events)
                    findings = run_observation.validate_path(target)
                    self.assertIn("RO014", {item.code for item in findings})
                    self.assertNotIn(name, "\n".join(item.path for item in findings))

            for name, value in (
                ("contentCount", "the complete raw content"),
                ("contentDigest", "not-a-sha256"),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: value}
                    write_events(target, events)
                    self.assertIn("RO014", codes(target))

            for name, value in (
                ("contentCount", 2),
                ("contentDigest", "4" * 64),
                ("contentcount", 2),
                ("contentdigest", "4" * 64),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: value}
                    write_events(target, events)
                    self.assertEqual(codes(target), set())

    def test_reporter_rejects_named_target_swap_during_write(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            parent = Path(directory)
            target = parent / "report.json"
            displaced = parent / "created.json"
            parsed = reporter.report_target([str(target)])
            real_write = os.write
            swapped = False

            def swap_named_target(descriptor, data):
                nonlocal swapped
                written = real_write(descriptor, data)
                if not swapped:
                    swapped = True
                    target.rename(displaced)
                    target.write_text('{"schema":"forged"}\n', encoding="utf-8")
                return written

            with mock.patch.object(reporter.os, "write", swap_named_target):
                with self.assertRaises(OSError):
                    reporter.write_report(parsed, {"schema": "expected"})
            self.assertEqual(
                target.read_text(encoding="utf-8"), '{"schema":"forged"}\n'
            )

    def test_reporter_rejects_same_inode_rewrite_after_fsync(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as directory:
            target = Path(directory) / "report.json"
            parsed = reporter.report_target([str(target)])
            payload = {"schema": "expected", "padding": "x" * 32}
            expected = (json.dumps(payload, sort_keys=True) + "\n").encode("utf-8")
            forged = bytearray(expected)
            offset = forged.index(b"expected")
            forged[offset : offset + 8] = b"forged!!"
            self.assertEqual(len(forged), len(expected))
            original_fsync = reporter.os.fsync
            raced = False

            def rewrite_after_fsync(descriptor):
                nonlocal raced
                original_fsync(descriptor)
                if not raced:
                    raced = True
                    with target.open("r+b", buffering=0) as handle:
                        handle.write(forged)

            with mock.patch.object(reporter.os, "fsync", rewrite_after_fsync):
                with self.assertRaises(OSError):
                    reporter.write_report(parsed, payload)
            self.assertFalse(target.exists())

    def test_reporter_includes_the_exact_coverage_guard(self):
        self.assertIn(
            Path("tests/test_promise_machine_contract.py"),
            reporter.REQUIRED_SURFACE,
        )
        self.assertIn("tests.test_promise_machine_contract", reporter.MODULES)

    def test_boolean_token_count_refuses(self):
        with scratch_directory() as directory:
            target = Path(directory) / "tokens.jsonl"
            events = fixture_events()
            events[2]["token_usage"]["input_tokens"] = True
            write_events(target, events)
            self.assertIn("RO016", codes(target))

    def test_nested_duplicate_keys_refuse(self):
        with scratch_directory() as directory:
            target = Path(directory) / "duplicate.jsonl"
            first = (FIXTURES / "valid" / "success.jsonl").read_text().splitlines()[0]
            first = first[:-1] + ',"metadata":{"nested":1,"nested":2}}\n'
            target.write_text(first, encoding="utf-8")
            self.assertIn("RO005", codes(target))

    def test_non_finite_numbers_and_wrong_reference_types_refuse_without_crashing(self):
        with scratch_directory() as directory:
            base = Path(directory)
            non_finite = base / "non-finite.jsonl"
            events = fixture_events()
            events[0]["metadata"] = {"temperature": float("nan")}
            write_events(non_finite, events)
            self.assertIn("RO004", codes(non_finite))

            wrong_reference = base / "wrong-reference.jsonl"
            events = fixture_events("refusal.jsonl")
            events[3]["caused_by"] = {"event_id": "evt-3"}
            write_events(wrong_reference, events)
            self.assertIn("RO010", codes(wrong_reference))

    def test_non_finite_exponent_refuses(self):
        with scratch_directory() as directory:
            target = Path(directory) / "non-finite-exponent.jsonl"
            first = (FIXTURES / "valid" / "success.jsonl").read_text().splitlines()[0]
            first = first[:-1] + ',"metadata":{"temperature":1e999}}\n'
            target.write_text(first, encoding="utf-8")
            self.assertIn("RO007", codes(target))

    def test_malformed_retry_attempt_refuses_without_crashing(self):
        with scratch_directory() as directory:
            target = Path(directory) / "retry.jsonl"
            events = fixture_events("retry.jsonl")
            events[3]["attempt"] = "2"
            write_events(target, events)
            self.assertIn("RO007", codes(target))

    def test_unhashable_and_non_string_typed_fields_refuse_without_crashing(self):
        with scratch_directory() as directory:
            target = Path(directory) / "types.jsonl"

            cases = []
            events = fixture_events()
            events[0]["type"] = []
            cases.append(events)

            events = fixture_events()
            events[2]["status"] = []
            cases.append(events)

            events = fixture_events()
            events[2]["evidence"][0].pop("selector")
            events[2]["evidence"][0]["digest"] = 1
            cases.append(events)

            events = fixture_events()
            events[-1]["status"] = []
            cases.append(events)

            events = fixture_events("handoff.jsonl")
            events[2]["type"] = []
            cases.append(events)

            for value in (None, True, 1):
                events = fixture_events("handoff.jsonl")
                events[-1]["outcome"]["evidence_refs"] = value
                cases.append(events)

            for index, events in enumerate(cases):
                with self.subTest(index=index):
                    write_events(target, events)
                    self.assertIn("RO007", codes(target))

    def test_empty_evidence_selector_refuses(self):
        with scratch_directory() as directory:
            target = Path(directory) / "selector.jsonl"
            events = fixture_events()
            events[2]["evidence"][0]["selector"] = ""
            write_events(target, events)
            self.assertIn("RO007", codes(target))

    def test_outcome_subject_must_match_bound_evidence(self):
        with scratch_directory() as directory:
            target = Path(directory) / "outcome.jsonl"
            events = fixture_events()
            events[-1]["outcome"]["subject"] = "different-subject"
            write_events(target, events)
            self.assertIn("RO012", codes(target))

    def test_sensitive_and_hidden_field_aliases_refuse(self):
        with scratch_directory() as directory:
            target = Path(directory) / "sensitive.jsonl"
            cases = {
                "RO014": {"api_key": "redacted"},
                "RO013": {"chainOfThought": "not observable"},
            }
            for expected, metadata in cases.items():
                with self.subTest(expected=expected):
                    events = fixture_events()
                    events[0]["metadata"] = metadata
                    write_events(target, events)
                    self.assertIn(expected, codes(target))

    def test_compact_sensitive_and_hidden_aliases_refuse(self):
        with scratch_directory() as directory:
            target = Path(directory) / "aliases.jsonl"
            cases = {
                "RO014": ("APIKey", "apikey", "rawArgs"),
                "RO013": ("chainofthought",),
            }
            for expected, names in cases.items():
                for name in names:
                    with self.subTest(expected=expected, name=name):
                        events = fixture_events()
                        events[0]["metadata"] = {name: "not observable"}
                        write_events(target, events)
                        findings = run_observation.validate_path(target)
                        self.assertIn(expected, {item.code for item in findings})
                        self.assertNotIn(
                            name,
                            json.dumps(run_observation.finding_objects(findings)),
                        )

    def test_suffixed_sensitive_and_hidden_aliases_refuse(self):
        with scratch_directory() as directory:
            target = Path(directory) / "aliases.jsonl"
            cases = {
                "RO014": (
                    "accessTokenValue",
                    "apikeyValue",
                    "authorizationHeader",
                    "privateKeyValue",
                    "promptText",
                    "rawToolOutput",
                    "systemPrompt",
                    "authHeader",
                    "refreshToken",
                    "idToken",
                    "argumentsText",
                    "toolResult",
                    "messages",
                    "chatMessages",
                    "systemMessage",
                    "inputText",
                    "requestBody",
                    "responseBody",
                    "functionArguments",
                    "functionCallArguments",
                    "envVars",
                    "headers",
                    "apiToken",
                    "oauthToken",
                    "requestHeaders",
                    "chatMessageContent",
                    "responseData",
                    "rawValue",
                    "rawInput",
                    "inputRaw",
                    "userInput",
                    "assistantOutput",
                    "assistantResponse",
                    "functionResult",
                    "toolCallArguments",
                    "requestArguments",
                    "jwt",
                ),
                "RO013": (
                    "chainOfThoughtText",
                    "chainofthoughttext",
                    "reasoningContent",
                    "thoughtSignature",
                ),
            }
            for expected, names in cases.items():
                for name in names:
                    with self.subTest(expected=expected, name=name):
                        events = fixture_events()
                        events[0]["metadata"] = {name: "not observable"}
                        write_events(target, events)
                        self.assertIn(expected, codes(target))

            events = fixture_events()
            events[0]["metadata"] = {
                "argument_count": 1,
                "chat_message_count": 2,
                "function_arguments_count": 3,
                "header_names": "content-type",
                "output_format": "json",
                "prompt_digest": "4" * 64,
            }
            write_events(target, events)
            self.assertEqual(run_observation.validate_path(target), [])

    def test_actor_payload_aliases_refuse_but_descriptors_remain_valid(self):
        with scratch_directory() as directory:
            target = Path(directory) / "actor-payloads.jsonl"
            for name in (
                "developerMessage",
                "developermessage",
                "agentOutput",
                "agentoutput",
                "humanInput",
                "humaninput",
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: "raw actor payload"}
                    write_events(target, events)
                    self.assertIn("RO014", codes(target))
            for name, value in (
                ("developerMessageCount", 1),
                ("agent_output_digest", "4" * 64),
                ("humanInputFormat", "json"),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: value}
                    write_events(target, events)
                    self.assertEqual(codes(target), set())

    def test_actor_payload_synonyms_refuse_but_descriptors_remain_valid(self):
        with scratch_directory() as directory:
            target = Path(directory) / "actor-payload-synonyms.jsonl"
            for name in (
                "aiOutput",
                "llmResponse",
                "botMessage",
                "assistantReply",
                "userQuery",
                "chatHistory",
                "messageHistory",
                "conversationHistory",
                "toolReturn",
                "functionReturn",
                "assistantAnswer",
                "llmGeneration",
                "aiGeneration",
                "toolObservation",
                "functionInvocation",
                "requestParameters",
                "requestParams",
                "chatLog",
                "conversationLog",
                "userContent",
                "modelContent",
                "toolCall",
                "functionCall",
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: "raw actor payload"}
                    write_events(target, events)
                    findings = run_observation.validate_path(target)
                    self.assertIn("RO014", {item.code for item in findings})
                    self.assertNotIn(
                        name,
                        json.dumps(run_observation.finding_objects(findings)),
                    )
            for name, value in (
                ("aiOutputDigest", "4" * 64),
                ("llm_response_count", 2),
                ("assistantReplyHash", "5" * 64),
                ("userQueryLength", 20),
                ("chatHistoryFormat", "jsonl"),
                ("toolReturnStatus", "complete"),
                ("modelContentType", "text"),
                ("toolCallId", "call-1"),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: value}
                    write_events(target, events)
                    self.assertEqual(codes(target), set())

    def test_execution_source_and_trace_payload_aliases_refuse(self):
        with scratch_directory() as directory:
            target = Path(directory) / "execution-source-trace-aliases.jsonl"
            for name in (
                "command",
                "shellCommand",
                "subprocessCommand",
                "commandLine",
                "shellScript",
                "sourceCode",
                "stackTrace",
                "executionTrace",
                "traceData",
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: "raw execution payload"}
                    write_events(target, events)
                    self.assertIn("RO014", codes(target))

    def test_instruction_and_hidden_work_synonyms_refuse_but_descriptors_remain_valid(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        metadata = schema["$defs"]["metadata"]
        families = metadata.get("x-runtime-forbidden-name-families", ())
        self.assertIn("instruction", families)
        self.assertIn("directive", families)
        with scratch_directory() as directory:
            target = Path(directory) / "instruction-hidden-synonyms.jsonl"
            for name, expected in (
                ("systemInstructions", "RO014"),
                ("developerInstructions", "RO014"),
                ("instructionSet", "RO014"),
                ("directiveText", "RO014"),
                ("thinkingText", "RO013"),
                ("reflectionNotes", "RO013"),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: "raw internal content"}
                    write_events(target, events)
                    findings = run_observation.validate_path(target)
                    self.assertIn(expected, {item.code for item in findings})
                    self.assertNotIn(
                        name,
                        json.dumps(run_observation.finding_objects(findings)),
                    )
            for name, value in (
                ("systemInstructionCount", 1),
                ("developer_instructions_digest", "4" * 64),
                ("instructionSetCount", 1),
                ("directive_digest", "4" * 64),
                ("thinkingFormat", "json"),
                ("reflectionStatus", "absent"),
            ):
                with self.subTest(name=name):
                    events = fixture_events()
                    events[0]["metadata"] = {name: value}
                    write_events(target, events)
                    self.assertEqual(codes(target), set())

    def test_optional_facts_refuse_explicit_estimates(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        exposed = schema["$defs"].get("exposedFactString")
        self.assertIsNotNone(exposed)
        if exposed is None:
            return
        schema_pattern = exposed["allOf"][1].get("pattern")
        self.assertIsNotNone(schema_pattern)
        if schema_pattern is None:
            return
        with scratch_directory() as directory:
            target = Path(directory) / "estimated-facts.jsonl"
            cases = []
            events = fixture_events()
            events[2]["token_usage"]["source"] = "estimated from text"
            cases.append((events, "RO016"))
            events = fixture_events()
            events[2]["token_usage"]["accounting_id"] = "approximation"
            cases.append((events, "RO016"))
            events = fixture_events()
            events[0]["host"] = {"source": "estimate", "identity": "host-1"}
            cases.append((events, "RO015"))
            for source in (
                "guessed from text",
                "heuristic token count",
                "projected from characters",
                "predicted by tokenizer",
                "forecast from prompt",
                "ballpark from text",
                "assumed from context",
                "extrapolated from prior count",
                "modeled from text",
                "modelled from text",
                "rough count",
                "approx count",
                "derived from text",
                "inferred from text",
                "calculated from prompt",
                "rounded count",
                "circa 100",
                "about 100",
                "unmeasured count",
                "synthetic count",
                "speculative count",
                "best effort count",
                "rule of thumb",
                "likely 100",
                "maybe 100",
            ):
                self.assertIsNone(re.fullmatch(schema_pattern, source))
                events = fixture_events()
                events[2]["token_usage"]["source"] = source
                cases.append((events, "RO016"))
            for events, expected in cases:
                with self.subTest(expected=expected):
                    write_events(target, events)
                    self.assertIn(expected, codes(target))

    def test_unknowns_do_not_repeat_or_contradict_supplied_facts(self):
        with scratch_directory() as directory:
            target = Path(directory) / "unknowns.jsonl"

            events = fixture_events()
            events[0]["unknowns"].append(
                {"field": "host", "reason": "host is unavailable"}
            )
            write_events(target, events)
            self.assertIn("RO007", codes(target))

            events = fixture_events()
            events[2]["unknowns"] = [
                {"field": "token_usage", "reason": "counts are unavailable"}
            ]
            write_events(target, events)
            self.assertIn("RO007", codes(target))

            events = fixture_events("refusal.jsonl")
            events[0]["unknowns"].append(
                {"field": "tokens", "reason": "still unavailable"}
            )
            write_events(target, events)
            self.assertIn("RO007", codes(target))

            for field in ("host_id", "hostName"):
                with self.subTest(field=field):
                    events = fixture_events()
                    events[0]["unknowns"] = [
                        {"field": field, "reason": "reported unavailable"}
                    ]
                    write_events(target, events)
                    self.assertIn("RO007", codes(target))

            for field in ("input_token_count", "accounting_id"):
                with self.subTest(field=field):
                    events = fixture_events()
                    events[2]["unknowns"] = [
                        {"field": field, "reason": "reported unavailable"}
                    ]
                    write_events(target, events)
                    self.assertIn("RO007", codes(target))

            events = fixture_events("refusal.jsonl")
            events[0]["unknowns"] = [
                {"field": "---", "reason": "field name was unavailable"}
            ]
            write_events(target, events)
            self.assertIn("RO007", codes(target))

    def test_run_context_is_closed_and_binds_refusals_and_handoffs(self):
        with scratch_directory() as directory:
            target = Path(directory) / "context.jsonl"

            events = fixture_events()
            events[0].pop("context")
            write_events(target, events)
            self.assertIn("RO007", codes(target))

            events = fixture_events()
            events[0]["context"]["role"] = "unknown"
            write_events(target, events)
            self.assertIn("RO007", codes(target))

            events = fixture_events("refusal.jsonl")
            events[3]["promise_id"] = "different-promise"
            write_events(target, events)
            self.assertIn("RO008", codes(target))

            events = fixture_events("handoff.jsonl")
            events[3]["producer"] = "different-skill"
            write_events(target, events)
            self.assertIn("RO008", codes(target))

            events = fixture_events("handoff.jsonl")
            events[3]["consumer"] = events[3]["producer"]
            write_events(target, events)
            self.assertIn("RO008", codes(target))

    def test_repository_before_and_after_identities_are_bound(self):
        events = fixture_events()
        opening = events[0]["repository"]
        closing = events[-1]["repository"]
        self.assertEqual(opening["path"], closing["path"])
        self.assertEqual(opening["before_commit"], closing["before_commit"])
        self.assertNotEqual(closing["before_commit"], closing["after_commit"])

        with scratch_directory() as directory:
            target = Path(directory) / "repository-transition.jsonl"
            cases = (
                ("path", "different/path.py"),
                ("before_commit", "3" * 40),
                ("after_commit", "not-a-git-id"),
            )
            for key, value in cases:
                with self.subTest(key=key):
                    events = fixture_events()
                    events[-1]["repository"][key] = value
                    write_events(target, events)
                    self.assertIn("RO017", codes(target))

            events = fixture_events()
            events[-1].pop("repository")
            write_events(target, events)
            self.assertIn("RO017", codes(target))

            events = fixture_events()
            events[0].pop("repository")
            write_events(target, events)
            self.assertIn("RO017", codes(target))

    def test_inferred_evidence_names_a_prior_event_selector(self):
        with scratch_directory() as directory:
            target = Path(directory) / "inferred.jsonl"
            events = fixture_events()
            definition = events[2]["evidence"][0]
            definition.update(
                evidence_class="inferred",
                source="fixture-inference-rule",
                selector="evt-2",
            )
            events[-1]["outcome"]["evidence_refs"][0]["evidence_class"] = "inferred"
            write_events(target, events)
            self.assertEqual(run_observation.validate_path(target), [])

            events[2]["evidence"][0]["selector"] = "not-an-event"
            write_events(target, events)
            self.assertIn("RO010", codes(target))

            events[2]["evidence"][0]["selector"] = events[2]["event_id"]
            write_events(target, events)
            self.assertIn("RO010", codes(target))

    def test_handoff_evidence_is_carried_by_the_source_event(self):
        with scratch_directory() as directory:
            target = Path(directory) / "handoff-source.jsonl"
            events = fixture_events("handoff.jsonl")
            second_start = dict(events[1])
            second_start.update(
                sequence=4,
                event_id="evt-x",
                parent_event_id="evt-3",
                capability_id="cap-x",
            )
            second_finish = dict(events[2])
            second_finish.pop("evidence")
            second_finish.update(
                sequence=5,
                event_id="evt-y",
                parent_event_id="evt-x",
                capability_id="cap-x",
                started_event_id="evt-x",
                status="failed",
            )
            events[3].update(
                sequence=6,
                parent_event_id="evt-y",
                source_event_id="evt-y",
            )
            events[4].update(sequence=7, parent_event_id="evt-4")
            events = events[:3] + [second_start, second_finish] + events[3:]
            write_events(target, events)
            self.assertIn("RO011", codes(target))

    def test_final_handoff_and_refusal_statuses_have_matching_events(self):
        with scratch_directory() as directory:
            target = Path(directory) / "final-status.jsonl"
            events = fixture_events()
            events[-1]["status"] = "handoff"
            write_events(target, events)
            self.assertIn("RO009", codes(target))

            events = fixture_events()
            events[-1]["status"] = "refused"
            events[-1]["outcome"]["evidence_refs"] = []
            write_events(target, events)
            self.assertIn("RO009", codes(target))

    def test_final_handoff_outcome_uses_handed_off_evidence(self):
        with scratch_directory() as directory:
            target = Path(directory) / "handoff-outcome.jsonl"
            events = fixture_events("handoff.jsonl")
            second = dict(events[2]["evidence"][0])
            second["evidence_id"] = "evidence-2"
            second["digest"] = "3" * 64
            second.pop("selector")
            events[2]["evidence"].append(second)
            events[-1]["outcome"]["evidence_refs"][0]["evidence_id"] = "evidence-2"
            write_events(target, events)
            self.assertIn("RO011", codes(target))

            events[3]["evidence_refs"] = None
            write_events(target, events)
            self.assertIn("RO007", codes(target))

    def test_placeholders_cannot_authorise_an_observed_outcome(self):
        with scratch_directory() as directory:
            target = Path(directory) / "placeholder.jsonl"
            events = fixture_events()
            events[0]["subject"] = "unknown"
            events[0]["scope"] = "unknown"
            definition = events[2]["evidence"][0]
            definition.update(
                subject="unknown",
                scope="unknown",
                time_domain="unknown",
                source="unknown",
                selector="unknown",
            )
            reference = events[3]["outcome"]["evidence_refs"][0]
            reference.update(
                subject="unknown", scope="unknown", time_domain="unknown"
            )
            events[3]["outcome"].update(subject="unknown", summary="unknown")
            write_events(target, events)
            self.assertIn("RO007", codes(target))

    def test_repository_paths_are_portable_and_control_free(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        declaration = schema["$defs"]["repositoryBefore"]["properties"]["path"]
        pattern = declaration["pattern"]
        self.assertEqual(declaration["x-unicode-normalization"], "NFC")
        self.assertEqual(declaration.get("x-max-utf8-bytes-per-segment"), 255)
        with scratch_directory() as directory:
            target = Path(directory) / "repository.jsonl"
            for repository_path in (
                "C:/Windows/system.ini",
                "C:relative.txt",
                "bad\npath",
                "unknown",
                "https://example.com/record.jsonl",
                "CON",
                "aux.txt",
                "folder/CONIN$",
                "COM¹",
                "COM².txt",
                "LPT³.log",
                "trailing.",
                "trailing ",
                "a//b",
                "./a",
                "a/./b",
                "x" * 256,
                "bad\ud800path",
                "e\u0301/path",
                "safe\u202ename",
                "safe\u2066name",
                "safe\u0085name",
                "safe\u00adname",
                "safe\u200bname",
                "safe\u2060name",
                "safe\ufeffname",
                "é" * 128,
                "😀" * 64,
            ):
                with self.subTest(repository_path=repository_path):
                    events = fixture_events()
                    events[0]["repository"]["path"] = repository_path
                    events[-1]["repository"]["path"] = repository_path
                    write_events(target, events)
                    self.assertIn("RO017", codes(target))
                    if repository_path not in {
                        "e\u0301/path",
                        "é" * 128,
                        "😀" * 64,
                    }:
                        self.assertIsNone(re.fullmatch(pattern, repository_path))
            events = fixture_events()
            events[0]["repository"]["path"] = "é/path"
            events[-1]["repository"]["path"] = "é/path"
            write_events(target, events)
            self.assertEqual(codes(target), set())

    def test_repository_path_total_utf8_bytes_are_bounded(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        declaration = schema["$defs"]["repositoryBefore"]["properties"]["path"]
        path_limit = getattr(run_observation, "MAX_REPOSITORY_PATH_BYTES", None)
        self.assertIsNotNone(path_limit)
        if path_limit is None:
            return
        self.assertEqual(
            declaration.get("x-max-total-utf8-bytes"),
            path_limit,
        )
        segment = "😀" * 63
        accepted = "/".join([segment] * 16)
        refused = "/".join([segment] * 17)
        self.assertLessEqual(
            len(accepted.encode("utf-8")),
            path_limit,
        )
        self.assertGreater(
            len(refused.encode("utf-8")),
            path_limit,
        )
        with scratch_directory() as directory:
            target = Path(directory) / "repository-total-bytes.jsonl"
            events = fixture_events()
            events[0]["repository"]["path"] = accepted
            events[-1]["repository"]["path"] = accepted
            write_events(target, events)
            self.assertEqual(codes(target), set())
            events[0]["repository"]["path"] = refused
            events[-1]["repository"]["path"] = refused
            write_events(target, events)
            self.assertIn("RO017", codes(target))
            events = fixture_events()
            events[0]["repository"]["path"] = "😀" * 63
            events[-1]["repository"]["path"] = "😀" * 63
            write_events(target, events)
            self.assertEqual(codes(target), set())

    def test_object_key_strings_share_the_string_limit(self):
        with scratch_directory() as directory:
            target = Path(directory) / "long-key.jsonl"
            events = fixture_events()
            events[0]["metadata"] = {"k" * (run_observation.MAX_STRING + 1): "value"}
            write_events(target, events)
            findings = run_observation.validate_path(target)
            self.assertTrue(any(item.code == "RO006" for item in findings))
            self.assertTrue(
                all(len(line) < 1_000 for line in run_observation.text_lines(findings))
            )

    def test_unknown_field_names_do_not_split_text_reports(self):
        with scratch_directory() as directory:
            target = Path(directory) / "unknown-key.jsonl"
            hostile_name = "forged\nRO000 injected"
            events = fixture_events()
            events[0][hostile_name] = "value"
            write_events(target, events)
            findings = run_observation.validate_path(target)
            lines = run_observation.text_lines(findings)
            self.assertTrue(any(item.code == "RO007" for item in findings))
            self.assertNotIn(hostile_name, "\n".join(lines))
            self.assertTrue(all("\n" not in line and "\r" not in line for line in lines))

    def test_combined_hostile_probes_refuse(self):
        with scratch_directory() as directory:
            base = Path(directory)

            oversized = base / "oversized.jsonl"
            first = (FIXTURES / "valid" / "success.jsonl").read_bytes().splitlines(keepends=True)[0]
            oversized.write_bytes(first + b"{" + b" " * run_observation.MAX_LINE_BYTES + b"}\n")
            self.assertIn("RO003", codes(oversized))

            symlink = base / "symlink.jsonl"
            symlink.symlink_to(FIXTURES / "valid" / "success.jsonl")
            self.assertEqual(codes(symlink), {"RO001"})

            cross_run = base / "cross-run.jsonl"
            retry = fixture_events("retry.jsonl")
            retry[3]["retry_of"]["run_id"] = "different-run"
            write_events(cross_run, retry)
            self.assertIn("RO010", codes(cross_run))

            nested_reasoning = base / "reasoning.jsonl"
            events = fixture_events()
            events[0]["metadata"] = {"nested": {"chain_of_thought": "not observable"}}
            write_events(nested_reasoning, events)
            self.assertIn("RO013", codes(nested_reasoning))

            truncated = base / "truncated.jsonl"
            write_events(truncated, fixture_events(), final_newline=False)
            self.assertIn("RO004", codes(truncated))

            after_finish = base / "after-finish.jsonl"
            events = fixture_events("refusal.jsonl")
            extra = dict(events[-2])
            extra.update(sequence=6, event_id="evt-6", parent_event_id="evt-5")
            events.append(extra)
            write_events(after_finish, events)
            self.assertIn("RO009", codes(after_finish))

    def test_growth_between_identity_check_and_read_still_hits_total_limit(self):
        with scratch_directory() as directory:
            target = Path(directory) / "growing.jsonl"
            target.write_bytes((FIXTURES / "valid" / "success.jsonl").read_bytes())
            original_open = run_observation.os.open
            grown = False

            def grow_then_open(path, flags):
                nonlocal grown
                if not grown:
                    grown = True
                    line = b'{"padding":"' + b"x" * 60_000 + b'"}\n'
                    with target.open("ab") as handle:
                        handle.write(line * 18)
                return original_open(path, flags)

            with mock.patch.object(run_observation.os, "open", grow_then_open):
                self.assertIn("RO002", codes(target))

    def test_fifo_swap_before_open_refuses_without_blocking(self):
        if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
            self.skipTest("FIFO non-blocking open is not available on this platform")
        with scratch_directory() as directory:
            target = Path(directory) / "raced.jsonl"
            target.write_bytes((FIXTURES / "valid" / "success.jsonl").read_bytes())
            original_open = run_observation.os.open
            swapped = False

            def swap_then_open(path, flags):
                nonlocal swapped
                self.assertTrue(flags & os.O_NONBLOCK)
                if not swapped:
                    swapped = True
                    target.unlink()
                    os.mkfifo(target)
                return original_open(path, flags)

            with mock.patch.object(run_observation.os, "open", swap_then_open):
                self.assertEqual(codes(target), {"RO001"})

    def test_one_growing_overlong_line_still_hits_total_limit(self):
        with scratch_directory() as directory:
            target = Path(directory) / "growing-line.jsonl"
            target.write_bytes((FIXTURES / "valid" / "success.jsonl").read_bytes())
            original_open = run_observation.os.open
            grown = False

            def grow_then_open(path, flags):
                nonlocal grown
                if not grown:
                    grown = True
                    with target.open("ab") as handle:
                        handle.write(b"{" + b"x" * (run_observation.MAX_TOTAL_BYTES + 1) + b"}\n")
                return original_open(path, flags)

            with mock.patch.object(run_observation.os, "open", grow_then_open):
                self.assertIn("RO002", codes(target))

    def test_same_size_rewrite_during_read_refuses(self):
        with scratch_directory() as directory:
            target = Path(directory) / "rewritten.jsonl"
            valid = (FIXTURES / "valid" / "success.jsonl").read_bytes()
            invalid = valid.replace(b'"status":"success"', b'"status":"unknown"', 1)
            self.assertEqual(len(valid), len(invalid))
            target.write_bytes(invalid)
            original_fdopen = run_observation.os.fdopen

            class RacingReader:
                def __init__(self, descriptor):
                    self.handle = original_fdopen(descriptor, "rb", buffering=0)
                    self.calls = 0

                def __enter__(self):
                    return self

                def __exit__(self, *_):
                    self.handle.close()

                def fileno(self):
                    return self.handle.fileno()

                def readline(self, limit=-1):
                    self.calls += 1
                    if self.calls == 1:
                        target.write_bytes(valid)
                    result = self.handle.readline(limit)
                    if self.calls == 4:
                        target.write_bytes(invalid)
                    return result

            def racing_fdopen(descriptor, _mode):
                return RacingReader(descriptor)

            with mock.patch.object(run_observation.os, "fdopen", racing_fdopen):
                self.assertIn("RO001", codes(target))
            self.assertEqual(target.read_bytes(), invalid)

    def test_equal_length_same_inode_rewrite_after_post_read_fstat_refuses(self):
        with scratch_directory() as directory:
            target = Path(directory) / "last-window.jsonl"
            valid = (FIXTURES / "valid" / "success.jsonl").read_bytes()
            invalid = valid.replace(b'"status":"success"', b'"status":"unknown"', 1)
            self.assertEqual(len(valid), len(invalid))
            target.write_bytes(valid)
            original_fstat = run_observation.os.fstat
            calls = 0

            def rewrite_after_post_read_fstat(descriptor):
                nonlocal calls
                calls += 1
                result = original_fstat(descriptor)
                if calls == 2:
                    target.write_bytes(invalid)
                return result

            with mock.patch.object(run_observation.os, "fstat", rewrite_after_post_read_fstat):
                self.assertIn("RO001", codes(target))
            self.assertEqual(target.read_bytes(), invalid)

    def test_named_path_replacement_during_read_refuses(self):
        with scratch_directory() as directory:
            target = Path(directory) / "replaced.jsonl"
            valid = (FIXTURES / "valid" / "success.jsonl").read_bytes()
            invalid = (FIXTURES / "invalid" / "missing-run-id.jsonl").read_bytes()
            target.write_bytes(valid)
            original_fdopen = run_observation.os.fdopen

            class ReplacingReader:
                def __init__(self, descriptor):
                    self.handle = original_fdopen(descriptor, "rb", buffering=0)

                def __enter__(self):
                    target.unlink()
                    target.write_bytes(invalid)
                    return self

                def __exit__(self, *_):
                    self.handle.close()

                def fileno(self):
                    return self.handle.fileno()

                def readline(self, limit=-1):
                    return self.handle.readline(limit)

            def replacing_fdopen(descriptor, _mode):
                return ReplacingReader(descriptor)

            with mock.patch.object(run_observation.os, "fdopen", replacing_fdopen):
                self.assertIn("RO001", codes(target))
            self.assertEqual(target.read_bytes(), invalid)

    def test_parent_path_replacement_outside_root_refuses(self):
        with scratch_directory() as directory:
            base = Path(directory)
            confined_root = base / "root"
            inside = confined_root / "inside"
            outside = base / "outside"
            moved = confined_root / "moved"
            inside.mkdir(parents=True)
            outside.mkdir()
            target = inside / "record.jsonl"
            target.write_bytes((FIXTURES / "valid" / "success.jsonl").read_bytes())
            os.link(target, outside / "record.jsonl")
            original_fdopen = run_observation.os.fdopen

            class ReplacingParentReader:
                def __init__(self, descriptor):
                    self.handle = original_fdopen(descriptor, "rb", buffering=0)

                def __enter__(self):
                    inside.rename(moved)
                    inside.symlink_to(outside, target_is_directory=True)
                    return self

                def __exit__(self, *_):
                    self.handle.close()

                def fileno(self):
                    return self.handle.fileno()

                def readline(self, limit=-1):
                    return self.handle.readline(limit)

            def replacing_parent_fdopen(descriptor, _mode):
                return ReplacingParentReader(descriptor)

            with mock.patch.object(
                run_observation.os,
                "fdopen",
                replacing_parent_fdopen,
            ):
                findings = run_observation.validate_path(target, root=confined_root)
            self.assertIn("RO001", {item.code for item in findings})
            self.assertFalse(target.resolve().is_relative_to(confined_root.resolve()))

    def test_unrepresentable_caller_paths_refuse_without_crashing(self):
        for value in ("bad\0name", "bad\ud800name"):
            with self.subTest(value=ascii(value)):
                findings = run_observation.validate_path(Path(value))
                self.assertEqual({item.code for item in findings}, {"RO001"})

    def test_control_characters_do_not_split_text_reports(self):
        with scratch_directory() as directory:
            invalid = Path(directory) / "bad\nname.jsonl"
            invalid.write_bytes(
                (FIXTURES / "invalid" / "missing-run-id.jsonl").read_bytes()
            )
            lines = run_observation.text_lines(run_observation.validate_path(invalid))
            self.assertTrue(lines)
            self.assertTrue(all("\n" not in line and "\r" not in line for line in lines))

            valid = Path(directory) / "good\nname.jsonl"
            valid.write_bytes((FIXTURES / "valid" / "success.jsonl").read_bytes())
            completed = run_cli(valid)
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(completed.stdout.count("\n"), 1)

            hostile = Path(directory) / "hostile.jsonl"
            events = fixture_events()
            events[0]["run_id"] = "run-good\nRO000 forged"
            events[0]["event_id"] = "evt-good\rforged"
            events[0]["correlation_id"] = "corr-good\nforged"
            events[0]["metadata"] = {"prompt/\n~": "raw"}
            write_events(hostile, events)
            findings = run_observation.validate_path(hostile)
            lines = run_observation.text_lines(findings)
            self.assertTrue(lines)
            self.assertTrue(all("\n" not in line and "\r" not in line for line in lines))
            self.assertTrue(all(item.run_id is None for item in findings if item.line == 1))
            self.assertTrue(all(item.event_id is None for item in findings if item.line == 1))
            self.assertTrue(
                all(item.correlation_id is None for item in findings if item.line == 1)
            )
            payload = next(item for item in findings if item.code == "RO014")
            self.assertTrue(payload.path.endswith("/metadata/[invalid-field]"))
            self.assertNotIn(
                "prompt", json.dumps(run_observation.finding_objects(findings))
            )

    def test_display_paths_are_bounded_and_content_addressed(self):
        hostile = Path("outside-" + "x" * (run_observation.MAX_DISPLAY_PATH * 4))
        findings = run_observation.validate_path(hostile)
        self.assertEqual({item.code for item in findings}, {"RO001"})
        self.assertLessEqual(len(findings[0].path), run_observation.MAX_DISPLAY_PATH)
        self.assertRegex(findings[0].path, r"\[sha256=[0-9a-f]{64}\]$")
        self.assertTrue(
            all(
                len(line) < run_observation.MAX_DISPLAY_PATH + 400
                for line in run_observation.text_lines(findings)
            )
        )

        with mock.patch.object(
            run_observation.os.path,
            "relpath",
            side_effect=ValueError("different drives"),
        ):
            findings = run_observation.validate_path(Path("outside.jsonl"))
        self.assertEqual({item.code for item in findings}, {"RO001"})

    def test_handoff_subject_change_refuses(self):
        path = FIXTURES / "invalid" / "strengthened-evidence.jsonl"
        findings = run_observation.validate_path(path)
        self.assertTrue(any(item.code == "RO012" and item.event_id == "evt-4" for item in findings))

    def test_runbook_separates_direct_and_elenchus_report_targets(self):
        runbook = RUNBOOK.read_text(encoding="utf-8")
        self.assertIn(
            'REPORT_PATH="$(pwd -P)/.elenchus/run-observation.json"', runbook
        )
        self.assertIn(
            'python3 tests/emit_run_observation_report.py "$REPORT_PATH"', runbook
        )
        self.assertIn('--report-file .elenchus/run-observation.json', runbook)
        self.assertNotIn(
            'python3 tests/emit_run_observation_report.py .elenchus/run-observation.json',
            runbook,
        )
        self.assertNotIn('--report-file "$REPORT_PATH"', runbook)
        self.assertIn(
            "Elenchus replaces `{report}` with a canonical absolute descendant",
            runbook,
        )
        self.assertNotIn(
            "/tmp/fiat/fiat-434-observable-run-record-carryover-inoculation",
            runbook,
        )


if __name__ == "__main__":
    unittest.main()
