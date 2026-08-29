"""Systematic issue-434 carryover inoculation for the run-observation validator."""

import copy
import importlib
import inspect
import io
import json
import re
import tempfile
import unittest
from collections import Counter
from decimal import Decimal
from pathlib import Path

from tests import test_run_observation as focused


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "run-observation"
CARRYOVER = FIXTURES / "434-carryover-v1.json"


scratch_directory = focused.scratch_directory


VALID_FLOWS = ("success.jsonl", "refusal.jsonl", "retry.jsonl", "handoff.jsonl")
FAMILIES = {
    "schema-runtime",
    "recursive-wrong-kind",
    "lifecycle-reference",
    "file-replacement",
    "path-representation",
    "normalized-field-name",
    "report-parity-no-echo",
    "work-repository-context",
}
ROUND_COUNTS = [6, 1, 5, 5, 6, 6, 4, 3]
AGGREGATE_AUDIT_ROUND_COUNTS = [3, 4, 2, 3, 4, 2, 1, 1]
PACKET_SHA256 = "11bbf719ce1b2f59b0344d4ad92d69e467c503d758b35a1689a98c7231156784"
PACKET_CHAIN = [
    {
        "name": "434-CARRYOVER.md",
        "url": "https://github.com/user-attachments/files/31350358/434-CARRYOVER.md",
        "sha256": "11bbf719ce1b2f59b0344d4ad92d69e467c503d758b35a1689a98c7231156784",
        "source_run": "observable run record",
        "source_run_branch": "fiat/434-observable-run-record",
        "source_ref": "archive/434-observable-run-record-attempt-3@9158edb4b3d2c49298d8b2ba8092c7540caeb57a"
    },
    {
        "name": "434-CARRYOVER-2.md",
        "url": "https://github.com/user-attachments/files/31350830/434-CARRYOVER-2.md",
        "sha256": "54469718c5949953dae414da664a65f940aca249868e00382f97139cda03fef0",
        "source_run": "observable run record carryover inoculation",
        "source_run_branch": "fiat/434-observable-run-record-carryover-inoculation",
        "source_ref": "archive/434-observable-run-record-attempt-4@dd5b9269252acc0da860cae0d4a6ec2a012f3cda"
    },
    {
        "name": "434-CARRYOVER-3.md",
        "url": "https://github.com/user-attachments/files/31352421/434-CARRYOVER-3.md",
        "sha256": "5f454dc466109ebaf138959986dcbdfb267d1c1e1291b0db000e18c4f567dcbe",
        "source_run": "observable run record carryover inoculation 2",
        "source_run_branch": "fiat/434-observable-run-record-carryover-inoculation",
        "source_ref": "archive/434-observable-run-record-attempt-5@50a9129c8481e7519d8c640c152f58401035f323",
        "source_implementation": "546b773f6ebd98a16b42c4f1c3a94f54465a5db0"
    }
]
FIXED_ROUND_1_IDS = {
    "I434-C2-S1-R1-01",
    "I434-C2-S1-R1-02",
    "I434-C2-S1-R1-03",
    "I434-C2-S1-R1-04",
}
CURRENT_REPAIR_MECHANISMS = {
    "hidden-work-prefix-suffix-token-compact-camel-acronym",
    "unicode-scalar-nfc-control-bidi-repository-path",
    "bounded-final-named-path-reread-and-digest",
}
AUDIT_ROUND_1_IDS = {
    "I434-C3-S1-R1-01",
    "I434-C3-S1-R1-02",
    "I434-C3-S1-R1-03",
}
AUDIT_ROUND_2_IDS = {
    "I434-C3-S1-R2-01",
    "I434-C3-S1-R2-02",
    "I434-C3-S1-R2-03",
    "I434-C3-S1-R2-04",
}
AUDIT_ROUND_3_IDS = {
    "I434-C3-S1-R3-01",
    "I434-C3-S1-R3-02",
}
AUDIT_ROUND_4_IDS = {
    "I434-C3-S1-R4-01",
    "I434-C3-S1-R4-02",
    "I434-C3-S1-R4-03",
}
AUDIT_ROUND_5_IDS = {
    "I434-C3-S1-R5-01",
    "I434-C3-S1-R5-02",
    "I434-C3-S1-R5-03",
    "I434-C3-S1-R5-04",
}
AUDIT_ROUND_6_IDS = {
    "I434-C3-S1-R6-01",
    "I434-C3-S1-R6-02",
}
AUDIT_ROUND_7_IDS = {
    "I434-C3-S1-R7-01",
}
AUDIT_ROUND_8_IDS = {
    "I434-C3-S1-R8-01",
}

# The recursive count is pinned after the generator is defined. A change to a
# valid fixture or structural walker must update this declaration deliberately.
EXPECTED_CASE_COUNTS = {
    "carryover-map": 36,
    "aggregate-manifest": 61,
    "fixed-round-1-map": 4,
    "current-repair-map": 3,
    "reporter-lead-map": 1,
    "audit-round-1-map": 3,
    "audit-round-2-map": 4,
    "audit-round-3-map": 2,
    "audit-round-4-map": 3,
    "audit-round-5-map": 4,
    "audit-round-6-map": 2,
    "audit-round-7-map": 1,
    "audit-round-8-map": 1,
    "schema-runtime": 309,
    "recursive-wrong-kind": 365,
    "lifecycle-reference": 9,
    "file-replacement": 8,
    "path-representation": 33,
    "normalized-field-name": 384,
    "report-parity-no-echo": 8,
    "work-repository-context": 17,
}
CASE_COUNTS = Counter()
CRASHES = 0
UNEXPECTED_CLEAN = 0


def events(name="success.jsonl"):
    return focused.fixture_events(name)


def path_get(root, path):
    value = root
    for part in path:
        value = value[part]
    return value


def path_set(root, path, value):
    parent = path_get(root, path[:-1])
    parent[path[-1]] = value


def structural_paths(value, prefix=()):
    """Yield every typed structural value, excluding open metadata payloads."""
    if isinstance(value, dict):
        for key, child in value.items():
            current = prefix + (key,)
            if key == "metadata":
                continue
            yield current
            if isinstance(child, (dict, list)):
                yield from structural_paths(child, current)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            current = prefix + (index,)
            yield current
            if isinstance(child, (dict, list)):
                yield from structural_paths(child, current)


def wrong_kind(value):
    if isinstance(value, dict):
        return []
    if isinstance(value, list):
        return {}
    if isinstance(value, str):
        return []
    if type(value) is int:
        return {}
    if type(value) is bool:
        return {}
    if value is None:
        return []
    raise AssertionError(f"no wrong-kind generator for {type(value).__name__}")


def styled_names(parts):
    """Generate separator, camel, Pascal and compact spellings from tokens."""
    first, *rest = parts
    camel = first + "".join(item.title() for item in rest)
    pascal = "".join(item.title() for item in parts)
    return {
        "_".join(parts),
        "-".join(parts),
        camel,
        pascal,
        "".join(parts),
    }


class RunObservationInoculationTests(unittest.TestCase):
    maxDiff = None

    @classmethod
    def tearDownClass(cls):
        summary = {
            "schema": "run-observation-inoculation-summary/v1",
            "families": sorted(FAMILIES),
            "cases": dict(sorted(CASE_COUNTS.items())),
            "total_cases": sum(CASE_COUNTS.values()),
            "crashes": CRASHES,
            "unexpected_clean": UNEXPECTED_CLEAN,
        }
        print("INOCULATION " + json.dumps(summary, sort_keys=True))

    def refuse(self, target, family):
        global CRASHES, UNEXPECTED_CLEAN
        try:
            result = focused.run_observation.validate_path(target)
        except Exception:
            CRASHES += 1
            raise
        if not result:
            UNEXPECTED_CLEAN += 1
        self.assertTrue(result, f"{family} mutation unexpectedly validated")
        CASE_COUNTS[family] += 1
        return result

    def write_and_refuse(self, target, changed, family):
        focused.write_events(target, changed)
        return self.refuse(target, family)

    def test_01_carryover_map_is_a_complete_bijection(self):
        document = json.loads(CARRYOVER.read_text(encoding="utf-8"))
        findings = document["findings"]
        ids = [item["id"] for item in findings]
        self.assertEqual(document["packet_sha256"], PACKET_SHA256)
        self.assertEqual(document["packet_chain"], PACKET_CHAIN)
        self.assertEqual(len(document["packet_chain"]), 3)
        self.assertEqual(
            {item["source_run"] for item in document["packet_chain"]},
            {item["source_run"] for item in PACKET_CHAIN},
        )
        self.assertEqual(
            {item["source_ref"] for item in document["packet_chain"]},
            {item["source_ref"] for item in PACKET_CHAIN},
        )
        self.assertEqual(document["round_counts"], ROUND_COUNTS)
        self.assertEqual(set(document["inoculation_families"]), FAMILIES)
        aggregate_manifest = document["aggregate_manifest"]
        expected_aggregate_ids = {
            f"S2-R{round_number}-{ordinal:02d}"
            for round_number, count in enumerate(ROUND_COUNTS, start=1)
            for ordinal in range(1, count + 1)
        }
        expected_aggregate_ids.update(
            {
                "I434-C3-S1-M-01",
                "I434-C3-S1-M-02",
                "I434-C3-S1-M-03",
                "I434-C3-S1-M-04",
                "RPT-C5-01",
            }
        )
        expected_aggregate_ids.update(
            f"R{round_number}-{ordinal:02d}"
            for round_number, count in enumerate(
                AGGREGATE_AUDIT_ROUND_COUNTS,
                start=1,
            )
            for ordinal in range(1, count + 1)
        )
        self.assertEqual(len(aggregate_manifest), 61)
        self.assertEqual(
            {item["id"] for item in aggregate_manifest},
            expected_aggregate_ids,
        )
        for item in aggregate_manifest:
            self.assertEqual(set(item), {"id", "family", "owner", "guard"})
            self.assertIn(item["family"], FAMILIES)
            self.assertTrue(item["owner"])
            self.assertTrue(item["guard"])
        self.assertEqual(len(findings), 36)
        self.assertEqual(len(set(ids)), 36)
        self.assertEqual(
            [Counter(item["round"] for item in findings)[round_number] for round_number in range(1, 9)],
            ROUND_COUNTS,
        )
        self.assertEqual({item["family"] for item in findings}, FAMILIES)
        self.assertTrue(all(item["remediation_family"] for item in findings))
        for item in findings:
            guard = item["guard"]
            module = importlib.import_module(guard["module"])
            owner = getattr(module, guard["class"])
            method = getattr(owner, guard["method"])
            self.assertTrue(inspect.isfunction(method), item["id"])
        CASE_COUNTS["carryover-map"] = len(findings)
        CASE_COUNTS["aggregate-manifest"] = len(aggregate_manifest)
        fixed_round_1 = document["fixed_round_1_mechanisms"]
        self.assertEqual({item["id"] for item in fixed_round_1}, FIXED_ROUND_1_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in fixed_round_1))
        current_repairs = document["current_repairs"]
        self.assertEqual(
            {item["mechanism"] for item in current_repairs},
            CURRENT_REPAIR_MECHANISMS,
        )
        self.assertTrue(all(item["family"] in FAMILIES for item in current_repairs))
        reporter_lead = document["reporter_lead"]
        self.assertEqual(reporter_lead["status"], "confirmed-and-guarded")
        audit_round_1 = document["audit_round_1_mechanisms"]
        self.assertEqual({item["id"] for item in audit_round_1}, AUDIT_ROUND_1_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_1))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_1))
        audit_round_2 = document["audit_round_2_mechanisms"]
        self.assertEqual({item["id"] for item in audit_round_2}, AUDIT_ROUND_2_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_2))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_2))
        audit_round_3 = document["audit_round_3_mechanisms"]
        self.assertEqual({item["id"] for item in audit_round_3}, AUDIT_ROUND_3_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_3))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_3))
        audit_round_4 = document["audit_round_4_mechanisms"]
        self.assertEqual({item["id"] for item in audit_round_4}, AUDIT_ROUND_4_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_4))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_4))
        audit_round_5 = document["audit_round_5_mechanisms"]
        self.assertEqual({item["id"] for item in audit_round_5}, AUDIT_ROUND_5_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_5))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_5))
        audit_round_6 = document["audit_round_6_mechanisms"]
        self.assertEqual({item["id"] for item in audit_round_6}, AUDIT_ROUND_6_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_6))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_6))
        audit_round_7 = document["audit_round_7_mechanisms"]
        self.assertEqual({item["id"] for item in audit_round_7}, AUDIT_ROUND_7_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_7))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_7))
        audit_round_8 = document.get("audit_round_8_mechanisms", [])
        self.assertEqual({item["id"] for item in audit_round_8}, AUDIT_ROUND_8_IDS)
        self.assertTrue(all(item["family"] in FAMILIES for item in audit_round_8))
        self.assertTrue(all(item["mechanism"] and item["remediation"] for item in audit_round_8))
        for item in [*fixed_round_1, *current_repairs, reporter_lead, *audit_round_1, *audit_round_2, *audit_round_3, *audit_round_4, *audit_round_5, *audit_round_6, *audit_round_7, *audit_round_8]:
            module_name, class_name, method_name = item["guard"].rsplit(".", 2)
            method = getattr(getattr(importlib.import_module(module_name), class_name), method_name)
            self.assertTrue(inspect.isfunction(method))
        CASE_COUNTS["fixed-round-1-map"] = len(fixed_round_1)
        CASE_COUNTS["current-repair-map"] = len(current_repairs)
        CASE_COUNTS["reporter-lead-map"] = 1
        CASE_COUNTS["audit-round-1-map"] = len(audit_round_1)
        CASE_COUNTS["audit-round-2-map"] = len(audit_round_2)
        CASE_COUNTS["audit-round-3-map"] = len(audit_round_3)
        CASE_COUNTS["audit-round-4-map"] = len(audit_round_4)
        CASE_COUNTS["audit-round-5-map"] = len(audit_round_5)
        CASE_COUNTS["audit-round-6-map"] = len(audit_round_6)
        CASE_COUNTS["audit-round-7-map"] = len(audit_round_7)
        CASE_COUNTS["audit-round-8-map"] = len(audit_round_8)

    def test_02_schema_runtime_differential_matrix(self):
        schema = json.loads(focused.SCHEMA.read_text(encoding="utf-8"))
        runtime = focused.run_observation
        path_limit = getattr(runtime, "MAX_REPOSITORY_PATH_BYTES", None)
        self.assertIsNotNone(path_limit)
        exposed_definition = schema["$defs"].get("exposedFactString")
        self.assertIsNotNone(exposed_definition)
        event_names = {
            "run.started": "runStarted",
            "capability.started": "capabilityStarted",
            "capability.finished": "capabilityFinished",
            "transition.refused": "transitionRefused",
            "retry.scheduled": "retryScheduled",
            "handoff.recorded": "handoffRecorded",
            "run.finished": "runFinished",
        }
        checks = [
            (sorted(schema["$defs"]["eventBase"]["required"]), sorted(runtime.COMMON_REQUIRED)),
            (
                sorted(set(schema["$defs"]["eventBase"]["properties"]) - set(schema["$defs"]["eventBase"]["required"])),
                sorted(runtime.COMMON_OPTIONAL),
            ),
            (set(schema["$defs"]["evidenceClass"]["enum"]), runtime.EVIDENCE_CLASSES),
            (
                set(schema["$defs"]["runFinished"]["allOf"][1]["properties"]["status"]["enum"]),
                runtime.RUN_STATUSES,
            ),
            (
                set(schema["$defs"]["capabilityFinished"]["allOf"][1]["properties"]["status"]["enum"]),
                runtime.CAPABILITY_STATUSES,
            ),
            (schema["$defs"]["identity"]["pattern"], runtime.ID_RE.pattern),
            (schema["$defs"]["boundedString"]["pattern"], runtime.OBSERVED_STRING_RE.pattern),
            (
                schema["$defs"]["metadata"]["propertyNames"].get("pattern"),
                runtime.UNKNOWN_FIELD_RE.pattern,
            ),
            (
                schema["$defs"]["metadata"]["additionalProperties"].get("maxLength"),
                runtime.MAX_STRING,
            ),
            (
                schema["$defs"]["repositoryBefore"]["properties"]["path"]["pattern"],
                runtime.REPOSITORY_PATH_RE.pattern,
            ),
            (
                schema["$defs"]["repositoryBefore"]["properties"]["path"]["x-unicode-normalization"],
                runtime.REPOSITORY_PATH_NORMALIZATION,
            ),
            (
                schema["$defs"]["repositoryBefore"]["properties"]["path"].get(
                    "x-forbidden-unicode-categories"
                ),
                ["Cc", "Cf", "Cs"],
            ),
            (
                schema["$defs"]["repositoryBefore"]["properties"]["path"].get(
                    "x-max-utf8-bytes-per-segment"
                ),
                255,
            ),
            (
                schema["$defs"]["repositoryBefore"]["properties"]["path"].get(
                    "x-max-total-utf8-bytes"
                ),
                path_limit,
            ),
            (
                "pattern" in exposed_definition["allOf"][1],
                True,
            ),
            (schema["$defs"]["eventBase"]["properties"]["time"]["pattern"], runtime.TIME_RE.pattern),
            (
                schema["$defs"]["unknown"]["properties"]["field"]["allOf"][1]["pattern"],
                runtime.UNKNOWN_FIELD_RE.pattern,
            ),
        ]
        for actual, expected in checks:
            self.assertEqual(actual, expected)
            CASE_COUNTS["schema-runtime"] += 1
        for event_type, definition in event_names.items():
            shape = schema["$defs"][definition]["allOf"][1]
            self.assertEqual(set(shape["required"]), runtime.EVENT_REQUIRED[event_type])
            self.assertEqual(
                set(shape["properties"]) - set(shape["required"]) - {"type"},
                runtime.EVENT_OPTIONAL[event_type],
            )
            CASE_COUNTS["schema-runtime"] += 2

        integer_fields = (
            schema["$defs"]["eventBase"]["properties"]["sequence"],
            schema["$defs"]["tokenUsage"]["properties"]["input_tokens"],
            schema["$defs"]["tokenUsage"]["properties"]["output_tokens"],
            schema["$defs"]["capabilityFinished"]["allOf"][1]["properties"]["duration_ms"],
            schema["$defs"]["retryScheduled"]["allOf"][1]["properties"]["attempt"],
            schema["$defs"]["retryScheduled"]["allOf"][1]["properties"]["after_ms"],
            schema["$defs"]["runFinished"]["allOf"][1]["properties"]["duration_ms"],
        )
        for field in integer_fields:
            self.assertEqual(Decimal(str(field["maximum"])), runtime.MAX_FINITE_NUMBER)
            CASE_COUNTS["schema-runtime"] += 1

        with scratch_directory() as directory:
            target = Path(directory) / "required.jsonl"
            for flow in VALID_FLOWS:
                original = events(flow)
                for event_index, event in enumerate(original):
                    required = runtime.COMMON_REQUIRED | runtime.EVENT_REQUIRED[event["type"]]
                    for key in sorted(required):
                        changed = copy.deepcopy(original)
                        changed[event_index].pop(key)
                        self.write_and_refuse(target, changed, "schema-runtime")
            for value in (
                "0000-01-01T00:00:00Z",
                "2026-02-30T00:00:00Z",
            ):
                changed = events()
                changed[0]["time"] = value
                self.write_and_refuse(target, changed, "schema-runtime")
            changed = events()
            changed[2]["token_usage"]["source"] = "estimated from text"
            self.write_and_refuse(target, changed, "schema-runtime")
            changed = events()
            changed[0]["host"] = {"source": "approximation", "identity": "host-1"}
            self.write_and_refuse(target, changed, "schema-runtime")
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
                self.assertIsNone(
                    re.fullmatch(exposed_definition["allOf"][1]["pattern"], source)
                )
                CASE_COUNTS["schema-runtime"] += 1
                changed = events()
                changed[2]["token_usage"]["source"] = source
                self.write_and_refuse(target, changed, "schema-runtime")

    def test_03_recursive_wrong_kind_matrix(self):
        with scratch_directory() as directory:
            target = Path(directory) / "wrong-kind.jsonl"
            generated = 0
            for flow in VALID_FLOWS:
                original = events(flow)
                for path in structural_paths(original):
                    old = path_get(original, path)
                    changed = copy.deepcopy(original)
                    path_set(changed, path, wrong_kind(old))
                    self.write_and_refuse(target, changed, "recursive-wrong-kind")
                    generated += 1
        self.assertEqual(generated, EXPECTED_CASE_COUNTS["recursive-wrong-kind"])

    def test_04_lifecycle_and_reference_matrix(self):
        with scratch_directory() as directory:
            target = Path(directory) / "relations.jsonl"
            cases = []

            changed = events()
            changed[1]["sequence"] = 9
            cases.append(("sequence-gap", changed))
            changed = events()
            changed[2]["started_event_id"] = "missing-event"
            cases.append(("missing-start", changed))
            changed = events("retry.jsonl")
            changed[3]["retry_of"]["run_id"] = "different-run"
            cases.append(("cross-run-retry", changed))
            changed = events("retry.jsonl")
            changed[3]["retry_of"]["event_id"] = changed[3]["event_id"]
            cases.append(("self-retry", changed))
            changed = events("handoff.jsonl")
            changed[3]["source_event_id"] = "missing-event"
            cases.append(("missing-handoff-source", changed))
            changed = events("handoff.jsonl")
            changed[3]["consumer"] = changed[3]["producer"]
            cases.append(("same-handoff-skill", changed))
            changed = events()
            changed[-1]["status"] = "handoff"
            cases.append(("missing-handoff-lifecycle", changed))
            changed = events()
            changed[-1]["outcome"]["subject"] = "changed-subject"
            cases.append(("changed-outcome-subject", changed))
            changed = events()
            changed[2]["evidence"][0].update(
                evidence_class="inferred",
                source="fixture-inference-rule",
                selector=changed[2]["event_id"],
            )
            changed[-1]["outcome"]["evidence_refs"][0]["evidence_class"] = "inferred"
            cases.append(("self-inferred-selector", changed))

            for label, changed in cases:
                with self.subTest(label=label):
                    self.write_and_refuse(target, changed, "lifecycle-reference")

    def test_05_file_replacement_matrix(self):
        methods = (
            "test_growth_between_identity_check_and_read_still_hits_total_limit",
            "test_same_size_rewrite_during_read_refuses",
            "test_fifo_swap_before_open_refuses_without_blocking",
            "test_named_path_replacement_during_read_refuses",
            "test_parent_path_replacement_outside_root_refuses",
            "test_reporter_rejects_named_target_swap_during_write",
            "test_equal_length_same_inode_rewrite_after_post_read_fstat_refuses",
            "test_reporter_rejects_same_inode_rewrite_after_fsync",
        )
        for method in methods:
            result = unittest.TestResult()
            focused.RunObservationRefusalTests(method).run(result)
            self.assertEqual(result.failures, [], method)
            self.assertEqual(result.errors, [], method)
            self.assertEqual(result.skipped, [], method)
            CASE_COUNTS["file-replacement"] += 1

    def test_06_path_representation_matrix(self):
        repository_paths = (
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
            "/".join(["😀" * 63] * 17),
        )
        with scratch_directory() as directory:
            target = Path(directory) / "paths.jsonl"
            for value in repository_paths:
                changed = events()
                changed[0]["repository"]["path"] = value
                changed[-1]["repository"]["path"] = value
                self.write_and_refuse(target, changed, "path-representation")
        for value in ("bad\0name", "bad\ud800name"):
            findings = focused.run_observation.validate_path(Path(value))
            self.assertEqual({item.code for item in findings}, {"RO001"})
            CASE_COUNTS["path-representation"] += 1
        for value in (
            Path("outside-" + "x" * (focused.run_observation.MAX_DISPLAY_PATH * 4)),
            Path("outside.jsonl"),
        ):
            findings = focused.run_observation.validate_path(value)
            self.assertEqual({item.code for item in findings}, {"RO001"})
            self.assertLessEqual(len(findings[0].path), focused.run_observation.MAX_DISPLAY_PATH)
            CASE_COUNTS["path-representation"] += 1

    def test_07_normalized_field_name_matrix(self):
        sensitive_parts = (
            ("api", "key"),
            ("access", "token"),
            ("raw", "args"),
            ("prompt", "text"),
            ("tool", "result"),
            ("request", "body"),
            ("raw", "input"),
            ("input", "raw"),
            ("user", "input"),
            ("assistant", "output"),
            ("assistant", "response"),
            ("function", "result"),
            ("tool", "call", "arguments"),
            ("request", "arguments"),
            ("developer", "message"),
            ("agent", "output"),
            ("human", "input"),
            ("ai", "output"),
            ("llm", "response"),
            ("bot", "message"),
            ("assistant", "reply"),
            ("user", "query"),
            ("chat", "history"),
            ("message", "history"),
            ("conversation", "history"),
            ("tool", "return"),
            ("function", "return"),
            ("assistant", "answer"),
            ("llm", "generation"),
            ("ai", "generation"),
            ("tool", "observation"),
            ("function", "invocation"),
            ("request", "parameters"),
            ("request", "params"),
            ("chat", "log"),
            ("conversation", "log"),
            ("user", "content"),
            ("model", "content"),
            ("tool", "call"),
            ("function", "call"),
            ("developer", "directive"),
            ("system", "directive"),
            ("command", "output"),
            ("command", "line"),
            ("shell", "command"),
            ("subprocess", "command"),
            ("shell", "script"),
            ("source", "code"),
            ("stack", "trace"),
            ("execution", "trace"),
            ("trace", "data"),
            ("cli", "arguments"),
            ("chat", "turns"),
            ("conversation", "turns"),
            ("instruction", "set"),
            ("instructions", "text"),
            ("directive", "set"),
        )
        hidden_parts = (
            ("chain", "of", "thought"),
            ("reasoning", "content"),
            ("analysis", "text"),
            ("scratchpad", "content"),
            ("deliberation", "notes"),
            ("internal", "monologue", "buffer"),
            ("cot", "buffer"),
            ("thinking", "text"),
            ("reflection", "notes"),
            ("cognitive", "process"),
        )
        sensitive_parts = sensitive_parts + (
            ("system", "instructions"),
            ("developer", "instructions"),
        )
        generated = []
        for parts in sensitive_parts:
            generated.extend(("RO014", name) for name in styled_names(parts))
        for parts in hidden_parts:
            generated.extend(("RO013", name) for name in styled_names(parts))
        with scratch_directory() as directory:
            target = Path(directory) / "names.jsonl"
            for expected, name in sorted(set(generated)):
                changed = events()
                changed[0]["metadata"] = {name: "rejected-value"}
                findings = self.write_and_refuse(target, changed, "normalized-field-name")
                self.assertIn(expected, {item.code for item in findings})

            aliases = (
                ("RO007", ""),
                ("RO007", "---"),
                ("RO007", "___"),
                ("RO007", "💣"),
                ("RO014", "input"),
                ("RO014", "request"),
                ("RO014", "response"),
                ("RO014", "message"),
                ("RO014", "result"),
                ("RO014", "env"),
                ("RO014", "cookies"),
                ("RO014", "jwt"),
                ("RO013", "analysis"),
                ("RO013", "scratchpad"),
                ("RO013", "deliberation"),
                ("RO013", "innerMonologue"),
                ("RO013", "internalMonologue"),
                ("RO014", "content"),
                ("RO014", "contents"),
                ("RO014", "contentText"),
                ("RO014", "content_body"),
                ("RO014", "contentData"),
                ("RO014", "contentValue"),
                ("RO007", "prоmpt"),
            )
            for expected, name in aliases:
                changed = events()
                changed[0]["metadata"] = {name: "rejected-value"}
                findings = self.write_and_refuse(
                    target, changed, "normalized-field-name"
                )
                self.assertIn(expected, {item.code for item in findings})

            changed = events()
            changed[0]["metadata"] = {"promptCount": "the complete raw prompt text"}
            findings = self.write_and_refuse(
                target, changed, "normalized-field-name"
            )
            self.assertIn("RO014", {item.code for item in findings})

            for name, value in (
                ("contentCount", "the complete raw content"),
                ("contentDigest", "not-a-sha256"),
            ):
                changed = events()
                changed[0]["metadata"] = {name: value}
                findings = self.write_and_refuse(
                    target, changed, "normalized-field-name"
                )
                self.assertIn("RO014", {item.code for item in findings})

            for name, value in (
                ("analysisdigest", "4" * 64),
                ("promptcount", 2),
                ("contentCount", 2),
                ("contentDigest", "4" * 64),
                ("contentcount", 2),
                ("contentdigest", "4" * 64),
            ):
                changed = events()
                changed[0]["metadata"] = {name: value}
                focused.write_events(target, changed)
                self.assertEqual(focused.run_observation.validate_path(target), [])
                CASE_COUNTS["normalized-field-name"] += 1

            known_unknowns = (
                (0, "host_id"),
                (0, "hostName"),
                (0, "hostidentity"),
                (2, "input_token_count"),
                (2, "inputTokenCount"),
                (2, "accounting_id"),
            )
            for event_index, name in known_unknowns:
                changed = events()
                changed[event_index]["unknowns"] = [
                    {"field": name, "reason": "reported unavailable"}
                ]
                self.write_and_refuse(target, changed, "normalized-field-name")
        self.assertEqual(
            CASE_COUNTS["normalized-field-name"],
            EXPECTED_CASE_COUNTS["normalized-field-name"],
        )

    def test_08_report_parity_and_no_echo_matrix(self):
        hostile = (
            ("unknown\nRO000 forged", "secret-value-1"),
            ("unknown\rforged", "secret-value-2"),
            ("unknown/~", "secret-value-3"),
            ("unknown" + "x" * 5000, "secret-value-4"),
        )
        with scratch_directory() as directory:
            target = Path(directory) / "report.jsonl"
            for key, value in hostile:
                changed = events()
                changed[0][key] = value
                focused.write_events(target, changed)
                findings = self.refuse(target, "report-parity-no-echo")
                text = "\n".join(focused.run_observation.text_lines(findings))
                objects = focused.run_observation.finding_objects(findings)
                encoded = json.dumps(objects, sort_keys=True)
                self.assertNotIn(value, text)
                self.assertNotIn(value, encoded)
                self.assertNotIn(key, text)
                self.assertNotIn(key, encoded)
                self.assertTrue(all("\n" not in line and "\r" not in line for line in text.splitlines()))

            for key, value in (
                ("api_key", "secret-value-5"),
                ("chainOfThought", "secret-value-6"),
                ("rawArgs", "secret-value-7"),
                ("promptText", "secret-value-8"),
            ):
                changed = events()
                changed[0]["metadata"] = {key: value}
                focused.write_events(target, changed)
                findings = self.refuse(target, "report-parity-no-echo")
                text = "\n".join(focused.run_observation.text_lines(findings))
                encoded = json.dumps(focused.run_observation.finding_objects(findings), sort_keys=True)
                self.assertNotIn(value, text)
                self.assertNotIn(value, encoded)
                self.assertNotIn(key, text)
                self.assertNotIn(key, encoded)

    def test_09_work_and_repository_context_matrix(self):
        with scratch_directory() as directory:
            target = Path(directory) / "context.jsonl"
            for field in ("issue_or_topic", "step", "role", "selected_skill", "promise_id"):
                changed = events()
                changed[0]["context"].pop(field)
                self.write_and_refuse(target, changed, "work-repository-context")
                changed = events()
                changed[0]["context"][field] = "unknown"
                self.write_and_refuse(target, changed, "work-repository-context")

            changed = events("refusal.jsonl")
            changed[3]["promise_id"] = "different-promise"
            self.write_and_refuse(target, changed, "work-repository-context")
            changed = events("handoff.jsonl")
            changed[3]["producer"] = "different-skill"
            self.write_and_refuse(target, changed, "work-repository-context")
            changed = events("handoff.jsonl")
            changed[3]["consumer"] = changed[3]["producer"]
            self.write_and_refuse(target, changed, "work-repository-context")

            repository_cases = (
                ("opening-missing", lambda value: value[0].pop("repository")),
                ("closing-missing", lambda value: value[-1].pop("repository")),
                ("path", lambda value: value[-1]["repository"].update(path="different/path.py")),
                (
                    "before",
                    lambda value: value[-1]["repository"].update(before_commit="3" * 40),
                ),
            )
            for _, mutate in repository_cases:
                changed = events()
                mutate(changed)
                self.write_and_refuse(target, changed, "work-repository-context")

    def test_10_declared_counts_and_zero_failures(self):
        self.assertEqual(CRASHES, 0)
        self.assertEqual(UNEXPECTED_CLEAN, 0)
        self.assertEqual(dict(CASE_COUNTS), EXPECTED_CASE_COUNTS)


if __name__ == "__main__":
    unittest.main()
