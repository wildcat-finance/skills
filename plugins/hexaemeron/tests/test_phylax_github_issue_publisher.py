"""Cause-level guards for GitHub issue publication admission."""

from __future__ import annotations

import ast
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = PLUGIN_ROOT / "skills" / "phylax" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "github-issue-publisher-v1"
CLI = SCRIPT_DIR / "github_issue_publisher.py"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from github_issue_publisher_lib import (  # noqa: E402
    AUTHORITY_SCHEMA,
    CANDIDATE_SCHEMA,
    FRAMEWORK_OPENING,
    FROZEN_SCHEMA,
    IMPRIMATUR_VERSION,
    MAX_JSON_MEMBERS,
    MAX_REQUEST_BYTES,
    MAX_STRING_BYTES,
    OPERATION,
    PublisherError,
    REPOSITORY,
    REQUEST_SCHEMA,
    SAPHENEIA_CHECKS,
    SAPHENEIA_VERSION,
    VULGATE_CHECKS,
    VULGATE_VERSION,
    admit_request,
    candidate_sha256,
    canonical_json,
    frozen_sha256,
    parse_json_bytes,
    read_bounded_file,
)
import github_issue_publisher_lib.policy as publisher_policy  # noqa: E402
from github_issue_publisher_lib.policy import default_imprimatur  # noqa: E402
import github_issue_publisher as publisher_cli  # noqa: E402


ROOT_FRAMEWORK_OPENING = (
    "Protasis decides which skill or skills this observation upgrades. "
    "The filer is the wrong party to guess."
)
CARRYOVER_ROW = "none | none | This publication carries no work into another issue."


def issue_body(opening: str, prose: str) -> str:
    sections = [prose, "Fiat-Required: 1", f"```carryover\n{CARRYOVER_ROW}\n```"]
    if opening:
        sections.insert(0, opening)
    return "\n\n".join(sections)


def candidate(title: str, body: str) -> dict[str, str]:
    return {"schema": CANDIDATE_SCHEMA, "title": title, "body": body}


def valid_document(
    *,
    title: str = "framework-56: checked publication boundary",
    body: str | None = None,
    queue: str = "observation",
    labels: list[str] | None = None,
    title_prefix: str = "framework-56",
    body_opening: str = FRAMEWORK_OPENING,
    host_structure: list[str] | None = None,
    protected_inventory: list[str] | None = None,
) -> dict[str, object]:
    if body is None:
        body = issue_body(
            FRAMEWORK_OPENING,
            "## Status\n\nThe publisher checks exact bytes before it asks for a credential.",
        )
    labels = (
        ["fiat-run-needed", "observation", "origin:ai"]
        if labels is None
        else labels
    )
    host_structure = ["## Status"] if host_structure is None else host_structure
    protected_inventory = (
        [
            "framework-56",
            FRAMEWORK_OPENING,
            "## Status",
            "exact bytes",
            "credential",
            "Fiat-Required: 1",
            CARRYOVER_ROW,
        ]
        if protected_inventory is None
        else protected_inventory
    )
    source = candidate(title, body)
    shaped = candidate(title, body)
    final = candidate(title, body)
    source_digest = candidate_sha256(title, body)
    shaped_digest = candidate_sha256(title, body)
    final_digest = candidate_sha256(title, body)
    frozen = {
        "schema": FROZEN_SCHEMA,
        "title_prefix": title_prefix,
        "body_opening": body_opening,
        "host_structure": host_structure,
        "protected_inventory": protected_inventory,
    }
    frozen_digest = frozen_sha256(frozen)
    gates = [
        {
            "stage": "sapheneia",
            "tool": "sapheneia:sapheneia",
            "version": SAPHENEIA_VERSION,
            "outcome": "passed",
            "source_sha256": source_digest,
            "candidate_sha256": shaped_digest,
            "subject_sha256": shaped_digest,
            "frozen_sha256": frozen_digest,
            "checks": list(SAPHENEIA_CHECKS),
        },
        {
            "stage": "imprimatur",
            "tool": "hexaemeron:imprimatur",
            "version": IMPRIMATUR_VERSION,
            "outcome": "clean",
            "subject_sha256": shaped_digest,
            "defects": 0,
        },
        {
            "stage": "vulgate",
            "tool": "hexaemeron:vulgate",
            "version": VULGATE_VERSION,
            "outcome": "parity",
            "source_sha256": shaped_digest,
            "candidate_sha256": final_digest,
            "subject_sha256": final_digest,
            "frozen_sha256": frozen_digest,
            "checks": list(VULGATE_CHECKS),
        },
        {
            "stage": "imprimatur-final",
            "tool": "hexaemeron:imprimatur",
            "version": IMPRIMATUR_VERSION,
            "outcome": "clean",
            "subject_sha256": final_digest,
            "defects": 0,
        },
    ]
    return {
        "schema": REQUEST_SCHEMA,
        "operation": OPERATION,
        "repository": REPOSITORY,
        "queue": queue,
        "labels": labels,
        "frozen": frozen,
        "source": source,
        "sapheneia_candidate": shaped,
        "final_candidate": final,
        "authority": {
            "schema": AUTHORITY_SCHEMA,
            "kind": "explicit-user-request",
            "outcome": "recorded",
            "reference": "skills#925",
            "subject_sha256": final_digest,
        },
        "gates": gates,
    }


def encoded(document: dict[str, object]) -> bytes:
    return canonical_json(document)


class AdmissionTests(unittest.TestCase):
    def assert_refused(
        self,
        value: dict[str, object] | bytes,
        code: str,
        field: str | None = None,
        *,
        runner=None,
    ) -> PublisherError:
        raw = value if isinstance(value, bytes) else encoded(value)
        with self.assertRaises(PublisherError) as caught:
            admit_request(raw, imprimatur_runner=runner or (lambda _text: {"defects": 0}))
        self.assertEqual(code, caught.exception.code)
        if field is not None:
            self.assertEqual(field, caught.exception.field)
        self.assertEqual(0, caught.exception.mint_attempts)
        self.assertEqual(0, caught.exception.post_attempts)
        self.assertEqual(0, caught.exception.diagnostic()["mint_attempts"])
        self.assertEqual(0, caught.exception.diagnostic()["post_attempts"])
        return caught.exception

    def test_valid_request_runs_both_imprimatur_passes(self):
        observed: list[str] = []

        def runner(text: str) -> dict[str, int]:
            observed.append(text)
            return {"defects": 0}

        document = valid_document()
        result = admit_request(encoded(document), imprimatur_runner=runner)
        self.assertEqual("observation", result.queue)
        self.assertEqual(
            ("fiat-run-needed", "observation", "origin:ai"), result.labels
        )
        self.assertEqual(2, len(observed))
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(0, result.mint_attempts)
        self.assertEqual(0, result.post_attempts)
        self.assertEqual(result.final_sha256, result.document()["final_sha256"])
        self.assertNotIn("title", result.document())
        self.assertNotIn("body", result.document())

    def test_root_publication_contract_is_enforced_before_imprimatur(self):
        self.assertEqual(ROOT_FRAMEWORK_OPENING, FRAMEWORK_OPENING)
        document = valid_document(
            body=(
                f"{ROOT_FRAMEWORK_OPENING}\n\n"
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential."
            ),
            protected_inventory=[
                "framework-56",
                ROOT_FRAMEWORK_OPENING,
                "## Status",
                "exact bytes",
                "credential",
            ],
        )
        self.assert_refused(document, "GIP132", "publication.fiat-required")
        document = valid_document(
            body=(
                f"{ROOT_FRAMEWORK_OPENING}\n\n"
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential.\n\n"
                "Fiat-Required: 1"
            ),
            protected_inventory=[
                "framework-56",
                ROOT_FRAMEWORK_OPENING,
                "## Status",
                "exact bytes",
                "credential",
                "Fiat-Required: 1",
            ],
        )
        self.assert_refused(document, "GIP132", "publication.carryover")
        document = valid_document(labels=["observation", "only-pr-needed", "origin:ai"])
        self.assert_refused(document, "GIP131", "publication.decision-label")

    def test_golden_candidate_passes_the_root_publication_contract(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_publisher_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        document = valid_document()
        final = document["final_candidate"]
        record, faults = module.issue_publication_contract_faults(
            final["title"], document["labels"], final["body"], "golden request"
        )
        self.assertEqual([], faults)
        self.assertEqual("framework-N", record["queue"])
        self.assertEqual(1, record["fiat_required"])
        self.assertEqual("none", record["carryover"][0]["id"])

    def test_root_valid_top_status_block_is_admitted(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_status_block_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        body = (
            "<!-- status:start -->\n"
            "Publication is pending a current admission record.\n"
            "<!-- status:end -->\n\n"
            + issue_body(
                ROOT_FRAMEWORK_OPENING,
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential.",
            )
        )
        document = valid_document(body=body)
        record, faults = module.issue_publication_contract_faults(
            document["final_candidate"]["title"],
            document["labels"],
            body,
            "status-block request",
        )
        self.assertEqual([], faults)
        self.assertEqual([1, 3], record["status_block"])
        result = admit_request(encoded(document))
        self.assertEqual("observation", result.queue)
        self.assertEqual(0, result.mint_attempts)
        self.assertEqual(0, result.post_attempts)

    def test_root_valid_leading_metadata_comment_is_admitted(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_metadata_comment_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        body = (
            "<!-- wildcat-origin: shoggoth -->\n\n"
            + issue_body(
                ROOT_FRAMEWORK_OPENING,
                "## Status\n\n"
                "The publisher checks exact bytes before it asks for a credential.",
            )
        )
        document = valid_document(body=body)
        record, faults = module.issue_publication_contract_faults(
            document["final_candidate"]["title"],
            document["labels"],
            body,
            "metadata-comment request",
        )
        self.assertEqual([], faults)
        self.assertEqual("framework-N", record["queue"])
        refusal = None
        try:
            result = admit_request(encoded(document))
        except PublisherError as error:
            refusal = (
                error.code,
                error.field,
                error.mint_attempts,
                error.post_attempts,
            )
        if refusal is not None:
            self.assertEqual(("GIP141", "frozen.body_opening", 0, 0), refusal)
            self.fail(
                "root-valid leading metadata comment was refused at "
                f"{refusal[0]}:{refusal[1]}"
            )
        self.assertEqual("observation", result.queue)
        self.assertEqual(0, result.mint_attempts)
        self.assertEqual(0, result.post_attempts)

    def test_root_queue_number_and_summary_grammar_is_enforced(self):
        for prefix in ("framework-0", "framework-01"):
            with self.subTest(prefix=prefix):
                document = valid_document(
                    title=f"{prefix}: checked publication boundary",
                    title_prefix=prefix,
                    protected_inventory=[
                        prefix,
                        FRAMEWORK_OPENING,
                        "## Status",
                        "exact bytes",
                        "credential",
                        "Fiat-Required: 1",
                        CARRYOVER_ROW,
                    ],
                )
                self.assert_refused(document, "GIP130", "queue.title_prefix")
        document = valid_document(title="framework-56:  checked publication boundary")
        self.assert_refused(document, "GIP130", "queue.title")

    def test_valid_fixture_is_the_canonical_golden_request(self):
        fixture = (FIXTURES / "valid-request.json").read_bytes().removesuffix(b"\n")
        self.assertEqual(encoded(valid_document()), fixture)
        result = admit_request(fixture, imprimatur_runner=lambda _text: {"defects": 0})
        self.assertEqual(
            "b7e467f4923807aa4dd70cdaeccd8f2c6dd418f09535dd230dc2c92daeebb2bb",
            result.final_sha256,
        )

    def test_default_imprimatur_accepts_clean_fixture(self):
        result = admit_request(encoded(valid_document()))
        self.assertEqual("observation", result.queue)

        class ExitingLoader:
            @staticmethod
            def create_module(_spec):
                return None

            @staticmethod
            def exec_module(_module):
                raise SystemExit("import aborted")

        specification = importlib.util.spec_from_loader(
            "github_issue_publisher_imprimatur", ExitingLoader()
        )
        with (
            mock.patch.object(publisher_policy, "_IMPRIMATUR_MODULE", None),
            mock.patch.object(
                publisher_policy.importlib.util,
                "spec_from_file_location",
                return_value=specification,
            ),
            self.assertRaises(PublisherError) as caught,
        ):
            admit_request(encoded(valid_document()))
        self.assertEqual("GIP152", caught.exception.code)
        self.assertEqual("gates.imprimatur.load", caught.exception.field)
        self.assertEqual(0, caught.exception.mint_attempts)
        self.assertEqual(0, caught.exception.post_attempts)

    def test_imprimatur_runner_failure_refuses(self):
        for failure in (RuntimeError("raw candidate"), SystemExit("runner aborted")):
            with self.subTest(failure=type(failure).__name__):
                self.assert_refused(
                    valid_document(),
                    "GIP152",
                    "gates.imprimatur.run",
                    runner=lambda _text, failure=failure: (_ for _ in ()).throw(failure),
                )

    def test_imprimatur_defect_refuses(self):
        self.assert_refused(
            valid_document(),
            "GIP151",
            "gates.imprimatur.defects",
            runner=lambda _text: {"defects": 1},
        )

    def test_exact_issue_855_is_digest_pinned_and_refused_before_authority(self):
        title = (FIXTURES / "issue-855-title.txt").read_text(encoding="utf-8").removesuffix("\n")
        body = (FIXTURES / "issue-855-body.txt").read_text(encoding="utf-8")
        source = json.loads((FIXTURES / "issue-855-source.json").read_text(encoding="utf-8"))
        self.assertEqual(source["title_sha256"], hashlib.sha256(title.encode()).hexdigest())
        self.assertEqual(source["body_sha256"], hashlib.sha256(body.encode()).hexdigest())
        self.assertEqual(source["candidate_sha256"], candidate_sha256(title, body))
        document = valid_document(
            title=title,
            body=body,
            title_prefix="framework-51",
            body_opening="",
            host_structure=["## What it looks like", "## Why it matters beyond one PR"],
            protected_inventory=[
                "framework-51",
                "shoggoth-wildcat-labs",
                "## What it looks like",
                "wildcat-finance/skills#853",
                "## Why it matters beyond one PR",
                "HOST_PR_LOGINS",
            ],
        )
        document["gates"] = []
        self.assert_refused(document, "GIP130", "queue.body_opening")

    def test_issue_855_prose_is_rejected_by_in_service_imprimatur(self):
        title = (FIXTURES / "issue-855-title.txt").read_text(encoding="utf-8").removesuffix("\n")
        original = (FIXTURES / "issue-855-body.txt").read_text(encoding="utf-8")
        body = issue_body(FRAMEWORK_OPENING, original)
        document = valid_document(
            title=title,
            body=body,
            title_prefix="framework-51",
            host_structure=["## What it looks like", "## Why it matters beyond one PR"],
            protected_inventory=[
                "framework-51",
                FRAMEWORK_OPENING,
                "shoggoth-wildcat-labs",
                "## What it looks like",
                "## Why it matters beyond one PR",
                "HOST_PR_LOGINS",
            ],
        )
        lint = default_imprimatur(f"{title}\n\n{body}")
        self.assertIn(
            ("structural_metaphor", "load-bearing"),
            {(hit["family"], hit["term"]) for hit in lint["hits"]},
        )
        with self.assertRaises(PublisherError) as caught:
            admit_request(encoded(document))
        self.assertEqual("GIP151", caught.exception.code)
        self.assertEqual("gates.imprimatur.defects", caught.exception.field)
        self.assertEqual(0, caught.exception.mint_attempts)
        self.assertEqual(0, caught.exception.post_attempts)

    def test_gate_order_is_closed(self):
        document = valid_document()
        document["gates"][0], document["gates"][1] = document["gates"][1], document["gates"][0]
        self.assert_refused(document, "GIP120", "gates.sapheneia")

    def test_gate_count_is_closed(self):
        for gates in ([], valid_document()["gates"][:3], valid_document()["gates"] * 2):
            with self.subTest(count=len(gates)):
                document = valid_document()
                document["gates"] = gates
                self.assert_refused(document, "GIP150", "gates")

    def test_gate_fields_are_closed(self):
        for index in range(4):
            with self.subTest(index=index, mutation="missing"):
                document = valid_document()
                document["gates"][index].pop("outcome")
                self.assert_refused(document, "GIP120")
            with self.subTest(index=index, mutation="extra"):
                document = valid_document()
                document["gates"][index]["note"] = "unchecked"
                self.assert_refused(document, "GIP120")

    def test_gate_versions_are_pinned(self):
        for index in range(4):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index]["version"] = "99.0.0"
                self.assert_refused(document, "GIP150")

    def test_sapheneia_source_and_candidate_are_bound(self):
        for key in ("source_sha256", "candidate_sha256", "frozen_sha256"):
            with self.subTest(key=key):
                document = valid_document()
                document["gates"][0][key] = "0" * 64
                self.assert_refused(document, "GIP150", "gates.sapheneia")

    def test_vulgate_source_candidate_and_frozen_are_bound(self):
        for key in ("source_sha256", "candidate_sha256", "frozen_sha256"):
            with self.subTest(key=key):
                document = valid_document()
                document["gates"][2][key] = "0" * 64
                self.assert_refused(document, "GIP150", "gates.vulgate")

    def test_judgement_check_lists_are_exact_and_ordered(self):
        for index in (0, 2):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index]["checks"] = list(reversed(document["gates"][index]["checks"]))
                self.assert_refused(document, "GIP150")

    def test_each_gate_subject_is_bound(self):
        for index, key in ((0, "subject_sha256"), (1, "subject_sha256"), (2, "subject_sha256"), (3, "subject_sha256")):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index][key] = "0" * 64
                self.assert_refused(document, "GIP150")

    def test_gate_outcomes_fail_closed(self):
        for index in range(4):
            with self.subTest(index=index):
                document = valid_document()
                document["gates"][index]["outcome"] = "failed"
                self.assert_refused(document, "GIP150")

    def test_candidate_mutation_breaks_digest_chain(self):
        document = valid_document()
        document["final_candidate"]["body"] += "\nChanged after the record."
        document["authority"]["subject_sha256"] = candidate_sha256(
            document["final_candidate"]["title"], document["final_candidate"]["body"]
        )
        self.assert_refused(document, "GIP150", "gates.vulgate")

    def test_authority_is_bound_to_final_candidate(self):
        document = valid_document()
        document["authority"]["subject_sha256"] = "0" * 64
        self.assert_refused(document, "GIP160", "authority")

    def test_recorded_authority_is_not_promoted_to_proof(self):
        document = valid_document()
        document["authority"]["outcome"] = "proved"
        self.assert_refused(document, "GIP160", "authority")

    def test_queue_forms(self):
        fixture = json.loads((FIXTURES / "queue-cases.json").read_text(encoding="utf-8"))
        self.assertEqual("github-issue-publisher-queue-cases/v1", fixture["schema"])
        self.assertEqual(4, len(fixture["cases"]))
        for case in fixture["cases"]:
            queue = case["queue"]
            prefix = case["prefix"]
            labels = case["labels"]
            with self.subTest(queue=queue):
                title = f"{prefix}: checked publication boundary"
                opening = case["body_opening"]
                body = issue_body(
                    opening,
                    "## Status\n\nThe publisher preserves exact bytes and credential evidence.",
                )
                document = valid_document(
                    title=title,
                    body=body,
                    queue=queue,
                    labels=labels,
                    title_prefix=prefix,
                    body_opening=opening,
                    protected_inventory=(
                        [
                            prefix,
                            opening,
                            "## Status",
                            "exact bytes",
                            "credential",
                            "Fiat-Required: 1",
                            CARRYOVER_ROW,
                        ]
                        if opening
                        else [
                            prefix,
                            "## Status",
                            "exact bytes",
                            "credential",
                            "Fiat-Required: 1",
                            CARRYOVER_ROW,
                        ]
                    ),
                )
                result = admit_request(encoded(document), imprimatur_runner=lambda _text: {"defects": 0})
                self.assertEqual(queue, result.queue)

        glued = valid_document(body=f"{FRAMEWORK_OPENING}continued without a line boundary")
        self.assert_refused(glued, "GIP141", "frozen.body_opening")
        blank_title = valid_document(title="framework-56:   ")
        self.assert_refused(blank_title, "GIP141", "frozen.title_prefix")

    def test_framework_cannot_pose_as_skill_queue(self):
        document = valid_document(
            title="framework-7: wrong queue",
            body="## Status\n\nExact bytes remain present.",
            queue="wish",
            labels=["wish"],
            title_prefix="framework-7",
            body_opening="",
            protected_inventory=["framework-7", "## Status", "Exact bytes"],
        )
        self.assert_refused(document, "GIP130", "queue.skill")

    def test_labels_are_sorted_unique_and_queue_bound(self):
        cases = (
            (["origin:ai", "observation"], "GIP131"),
            (["observation", "observation"], "GIP131"),
            (["origin:ai"], "GIP130"),
            (["held-job", "observation", "origin:ai"], "GIP130"),
        )
        for labels, code in cases:
            with self.subTest(labels=labels):
                self.assert_refused(valid_document(labels=labels), code)

    def test_frozen_inventory_must_survive_every_stage(self):
        document = valid_document()
        document["sapheneia_candidate"]["body"] = document["sapheneia_candidate"]["body"].replace(
            "exact bytes", "the candidate"
        )
        self.assert_refused(document, "GIP141", "frozen.protected_inventory")

    def test_request_rejects_unknown_top_level_field(self):
        document = valid_document()
        document["endpoint"] = "https://example.invalid"
        self.assert_refused(document, "GIP120", "request")

    def test_request_requires_every_top_level_field(self):
        for key in valid_document():
            with self.subTest(key=key):
                document = valid_document()
                document.pop(key)
                self.assert_refused(document, "GIP120", "request")

    def test_request_pins_schema_operation_and_repository(self):
        for key in ("schema", "operation", "repository"):
            with self.subTest(key=key):
                document = valid_document()
                document[key] = "future-value"
                self.assert_refused(document, "GIP120", f"request.{key}")

    def test_candidate_shape_is_closed(self):
        for name in ("source", "sapheneia_candidate", "final_candidate"):
            with self.subTest(name=name, mutation="missing"):
                document = valid_document()
                document[name].pop("body")
                self.assert_refused(document, "GIP120", name)
            with self.subTest(name=name, mutation="extra"):
                document = valid_document()
                document[name]["path"] = "fw51.md"
                self.assert_refused(document, "GIP120", name)
            with self.subTest(name=name, mutation="schema"):
                document = valid_document()
                document[name]["schema"] = "github-issue-candidate/v2"
                self.assert_refused(document, "GIP120", f"{name}.schema")

    def test_request_rejects_duplicate_json_name(self):
        self.assert_refused(b'{"schema":"a","schema":"b"}', "GIP102", "request.duplicate")

    def test_request_rejects_invalid_utf8(self):
        self.assert_refused(b"\xff", "GIP101", "request.utf8")
        for surrogate in ("\ud800", "\udfff"):
            with self.subTest(surrogate=ascii(surrogate)):
                document = valid_document()
                document["source"]["body"] += surrogate
                self.assert_refused(document, "GIP103", "request.string")

    def test_request_requires_canonical_json(self):
        raw = json.dumps(valid_document(), indent=2).encode("utf-8")
        self.assert_refused(raw, "GIP104", "request.canonical")

    def test_request_rejects_float_and_boolean_as_defect_count(self):
        raw = encoded(valid_document()).replace(b'"defects":0', b'"defects":0.0', 1)
        self.assert_refused(raw, "GIP103", "request.number")
        document = valid_document()
        document["gates"][1]["defects"] = False
        self.assert_refused(document, "GIP150", "gates.imprimatur")
        document = valid_document()
        document["gates"][1]["defects"] = -1
        self.assert_refused(document, "GIP150", "gates.imprimatur")

    def test_request_rejects_null_and_excessive_depth(self):
        document = valid_document()
        document["source"] = None
        self.assert_refused(document, "GIP120", "source")
        nested: object = "leaf"
        for _ in range(10):
            nested = [nested]
        raw_document = valid_document()
        raw_document["extra"] = nested
        self.assert_refused(encoded(raw_document), "GIP103", "request.depth")

    def test_request_rejects_member_and_byte_caps(self):
        raw_document = {f"field-{index}": index for index in range(257)}
        self.assert_refused(encoded(raw_document), "GIP103", "request.members")
        at_string_limit = {"x" * MAX_STRING_BYTES: 0}
        self.assertEqual(at_string_limit, parse_json_bytes(encoded(at_string_limit)))
        above_string_limit = {"x" * (MAX_STRING_BYTES + 1): 0}
        self.assert_refused(
            encoded(above_string_limit), "GIP103", "request.string"
        )
        self.assert_refused(b"{" + b" " * (1 << 20), "GIP100", "request.bytes")

    def test_text_must_be_nfc_and_control_free(self):
        document = valid_document()
        document["source"]["title"] = "framework-56: cafe\u0301"
        self.assert_refused(document, "GIP110", "source.title")
        document = valid_document()
        document["source"]["body"] += "\u202e"
        self.assert_refused(document, "GIP110", "source.body")

    def test_title_rejects_nonprinting_unicode_before_imprimatur(self):
        controller = PLUGIN_ROOT / "skills" / "fiat" / "scripts" / "hexctl.py"
        specification = importlib.util.spec_from_file_location(
            "hexctl_nonprinting_title_contract", controller
        )
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        for character in ("\u00a0", "\u2028", "\u2029"):
            with self.subTest(codepoint=f"U+{ord(character):04X}"):
                title = f"framework-56: checked{character}publication boundary"
                document = valid_document(title=title)
                _, faults = module.issue_publication_contract_faults(
                    title,
                    document["labels"],
                    document["final_candidate"]["body"],
                    "nonprinting-title request",
                )
                self.assertTrue(
                    any("title contains a control character" in fault for fault in faults)
                )
                calls: list[str] = []
                self.assert_refused(
                    document,
                    "GIP110",
                    "source.title",
                    runner=lambda text: calls.append(text) or {"defects": 0},
                )
                self.assertEqual([], calls)

    def test_frozen_shape_is_closed_and_nonempty(self):
        document = valid_document()
        document["frozen"]["path"] = "fw51.md"
        self.assert_refused(document, "GIP120", "frozen")
        for key in ("host_structure", "protected_inventory"):
            with self.subTest(key=key):
                document = valid_document()
                document["frozen"][key] = []
                self.assert_refused(document, "GIP140", "frozen.items")

    def test_frozen_items_are_unique(self):
        document = valid_document()
        document["frozen"]["host_structure"] *= 2
        self.assert_refused(document, "GIP140", "frozen.duplicate")

    def test_authority_shape_is_closed(self):
        document = valid_document()
        document["authority"]["proven"] = True
        self.assert_refused(document, "GIP120", "authority")

    def test_rejection_fixture_names_the_required_regressions(self):
        fixture = json.loads((FIXTURES / "rejection-cases.json").read_text(encoding="utf-8"))
        self.assertEqual("github-issue-publisher-rejection-cases/v1", fixture["schema"])
        self.assertEqual(
            {
                "issue-855-missing-framework-opening",
                "missing-gate",
                "failed-gate",
                "reordered-gate",
                "gate-subject-mismatch",
                "imprimatur-defect",
                "authority-subject-mismatch",
                "missing-fiat-required",
                "missing-carryover",
                "noncanonical-title",
                "decision-label-mismatch",
            },
            {case["id"] for case in fixture["cases"]},
        )

    def test_bounded_file_refuses_symlink_and_hardlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / "request.json"
            regular.write_bytes(encoded(valid_document()))
            link = root / "link.json"
            link.symlink_to(regular)
            with self.assertRaises(PublisherError) as caught:
                read_bounded_file(link)
            self.assertEqual("GIP105", caught.exception.code)
            hard = root / "hard.json"
            os.link(regular, hard)
            with self.assertRaises(PublisherError) as caught:
                read_bounded_file(regular)
            self.assertEqual("GIP105", caught.exception.code)

    def test_bounded_file_refuses_non_regular_input(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PublisherError) as caught:
                read_bounded_file(directory)
            self.assertEqual("GIP105", caught.exception.code)

    def test_cli_has_no_partial_publication_operation(self):
        completed = subprocess.run(
            [sys.executable, str(CLI)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5,
            check=False,
        )
        self.assertEqual(2, completed.returncode)
        self.assertEqual(b"", completed.stdout)
        diagnostic = json.loads(completed.stderr)
        self.assertEqual("GIP199", diagnostic["code"])
        self.assertEqual(0, diagnostic["mint_attempts"])
        self.assertEqual(0, diagnostic["post_attempts"])

    def test_selected_conformance_resolvers_emit_closed_reports(self):
        values = {
            "ordered-admission-chain": (True, "boolean"),
            "request-work-bound": (MAX_JSON_MEMBERS, "count"),
            "request-byte-bound": (MAX_REQUEST_BYTES, "bytes"),
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_root = (
                root
                / "plugins/hexaemeron/tests/fixtures/github-issue-publisher-v1"
            )
            shutil.copytree(FIXTURES, fixture_root)
            report_root = root / ".hexaemeron/design-reports"
            report_root.mkdir(parents=True)
            for criterion, (value, unit) in values.items():
                with self.subTest(criterion=criterion):
                    report_path = (
                        ".hexaemeron/design-reports/"
                        f"isolated-publisher-{criterion}.json"
                    )
                    arguments = [
                        sys.executable,
                        str(CLI),
                        "conformance",
                        "--manifest",
                        "plugins/hexaemeron/tests/fixtures/"
                        "github-issue-publisher-v1/manifest.json",
                        "--design-candidate",
                        "isolated-publisher",
                        "--design-criterion",
                        criterion,
                        "--design-report",
                        report_path,
                    ]
                    completed = subprocess.run(
                        arguments,
                        cwd=root,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        timeout=10,
                        check=False,
                    )
                    self.assertEqual(0, completed.returncode, completed.stderr)
                    self.assertEqual(b"", completed.stderr)
                    report_bytes = (root / report_path).read_bytes()
                    self.assertEqual(completed.stdout, report_bytes)
                    report = json.loads(report_bytes)
                    self.assertEqual(
                        {
                            "schema",
                            "candidate",
                            "criterion",
                            "value",
                            "unit",
                            "command",
                            "exit",
                        },
                        set(report),
                    )
                    self.assertEqual("protasis-design-report/v1", report["schema"])
                    self.assertEqual("isolated-publisher", report["candidate"])
                    self.assertEqual(criterion, report["criterion"])
                    self.assertEqual(value, report["value"])
                    self.assertEqual(unit, report["unit"])
                    self.assertEqual(0, report["exit"])
                    self.assertEqual(
                        "python3 plugins/hexaemeron/skills/phylax/scripts/"
                        "github_issue_publisher.py conformance --manifest "
                        "plugins/hexaemeron/tests/fixtures/"
                        "github-issue-publisher-v1/manifest.json "
                        "--design-candidate isolated-publisher "
                        f"--design-criterion {criterion} "
                        f"--design-report {report_path}",
                        report["command"],
                    )
                    self.assertEqual(canonical_json(report) + b"\n", report_bytes)

    def test_conformance_refuses_changed_fixture_without_a_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fixture_root = (
                root
                / "plugins/hexaemeron/tests/fixtures/github-issue-publisher-v1"
            )
            shutil.copytree(FIXTURES, fixture_root)
            changed = fixture_root / "valid-request.json"
            changed.write_bytes(changed.read_bytes() + b" ")
            report = (
                root
                / ".hexaemeron/design-reports/"
                "isolated-publisher-ordered-admission-chain.json"
            )
            report.parent.mkdir(parents=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "conformance",
                    "--manifest",
                    "plugins/hexaemeron/tests/fixtures/"
                    "github-issue-publisher-v1/manifest.json",
                    "--design-candidate",
                    "isolated-publisher",
                    "--design-criterion",
                    "ordered-admission-chain",
                    "--design-report",
                    ".hexaemeron/design-reports/"
                    "isolated-publisher-ordered-admission-chain.json",
                ],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertEqual(b"", completed.stdout)
            diagnostic = json.loads(completed.stderr)
            self.assertEqual("GIP199", diagnostic["code"])
            self.assertEqual("conformance.fixture", diagnostic["field"])
            self.assertEqual(0, diagnostic["mint_attempts"])
            self.assertEqual(0, diagnostic["post_attempts"])
            self.assertFalse(report.exists())

    def test_conformance_report_refuses_an_intermediate_symlink(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "work"
            outside = Path(directory) / "outside"
            fixture_root = (
                root
                / "plugins/hexaemeron/tests/fixtures/github-issue-publisher-v1"
            )
            shutil.copytree(FIXTURES, fixture_root)
            (outside / "design-reports").mkdir(parents=True)
            (root / ".hexaemeron").symlink_to(outside, target_is_directory=True)
            report = (
                outside
                / "design-reports/isolated-publisher-ordered-admission-chain.json"
            )
            completed = subprocess.run(
                [
                    sys.executable,
                    str(CLI),
                    "conformance",
                    "--manifest",
                    "plugins/hexaemeron/tests/fixtures/"
                    "github-issue-publisher-v1/manifest.json",
                    "--design-candidate",
                    "isolated-publisher",
                    "--design-criterion",
                    "ordered-admission-chain",
                    "--design-report",
                    ".hexaemeron/design-reports/"
                    "isolated-publisher-ordered-admission-chain.json",
                ],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
                check=False,
            )
            self.assertEqual(2, completed.returncode)
            self.assertEqual(b"", completed.stdout)
            diagnostic = json.loads(completed.stderr)
            self.assertEqual("GIP199", diagnostic["code"])
            self.assertEqual("conformance.report", diagnostic["field"])
            self.assertEqual(0, diagnostic["mint_attempts"])
            self.assertEqual(0, diagnostic["post_attempts"])
            self.assertFalse(report.exists())

    def test_conformance_checks_policy_refusals_instead_of_only_fixture_names(self):
        manifest = publisher_cli.read_bounded_file(publisher_cli.MANIFEST_PATH)
        files = publisher_cli._closed_manifest(manifest)
        fixtures = publisher_cli._fixture_bytes(Path(publisher_cli.MANIFEST_PATH).parent, files)

        class Bypass:
            mint_attempts = 0
            post_attempts = 0
            gate_versions = ("0.3.0", "2.3.0", "1.1.0", "2.3.0")

        with (
            mock.patch.object(publisher_cli, "admit_request", return_value=Bypass()),
            self.assertRaises(PublisherError) as caught,
        ):
            publisher_cli._verify_fixture_contract(fixtures)
        self.assertEqual("GIP199", caught.exception.code)
        self.assertEqual("conformance.rejection-cases", caught.exception.field)

    def test_step_one_surface_has_no_signer_or_transport_modules(self):
        package = SCRIPT_DIR / "github_issue_publisher_lib"
        self.assertEqual(
            {"__init__.py", "canonical.py", "errors.py", "policy.py"},
            {path.name for path in package.glob("*.py")},
        )
        cli_source = CLI.read_text(encoding="utf-8")
        self.assertNotIn("urllib", cli_source)
        self.assertNotIn("http.client", cli_source)
        self.assertNotIn("subprocess", cli_source)
        forbidden_imports = {"http", "requests", "socket", "ssl", "subprocess", "urllib"}
        forbidden_literals = {
            "/access_tokens",
            "api.github.com",
            "begin private key",
            "shoggoth-wildcat-labs.pem",
        }
        for path in (CLI, *sorted(package.glob("*.py"))):
            with self.subTest(path=path.name):
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
                imports = {
                    alias.name.split(".", 1)[0]
                    for node in ast.walk(tree)
                    if isinstance(node, (ast.Import, ast.ImportFrom))
                    for alias in (
                        node.names
                        if isinstance(node, ast.Import)
                        else [ast.alias(name=node.module or "")]
                    )
                }
                self.assertFalse(imports & forbidden_imports)
                lowered = source.casefold()
                self.assertFalse(
                    {literal for literal in forbidden_literals if literal in lowered}
                )


class ContractTests(unittest.TestCase):
    def test_tracked_specifications_match_receipted_sources(self):
        root = PLUGIN_ROOT.parents[1]
        durable = root / "docs/phylax-github-issue-publisher"
        expected = {
            "study.md": "45981759eb011b4c82515127b3124d792342ab03903e7a0a8c8f53fc50f78706",
            "runbook.md": "0e6a4fc2cdc805cfded6f3a8dac88ad8563c0319d397a6cff4ace998acf5d583",
            "design-evidence.json": "d74fd663f1ec76d8169fe3bfa536749d3440127b3e00ec3bd2c6894ae0280587",
            "design-topology.json": "bf373194c7c1dae82bfbe5e6ccdfeca612677b0d59d02c268bb675542fa66716",
        }
        for name, digest in expected.items():
            with self.subTest(name=name):
                self.assertEqual(
                    digest,
                    hashlib.sha256((durable / name).read_bytes()).hexdigest(),
                )

        evidence = json.loads((durable / "design-evidence.json").read_text())
        resolved = [
            result for result in evidence["results"]
            if isinstance(result["report"], dict)
        ]
        self.assertEqual(20, len(resolved))
        for result in resolved:
            report = result["report"]
            with self.subTest(report=report["path"]):
                self.assertEqual(
                    report["sha256"],
                    hashlib.sha256((durable / report["path"]).read_bytes()).hexdigest(),
                )

    def test_reference_names_judgement_and_live_deployment_limits(self):
        reference = (
            PLUGIN_ROOT / "skills/phylax/references/github-issue-publisher-v1.md"
        ).read_text(encoding="utf-8")
        self.assertIn("They do not establish factual truth", reference)
        self.assertIn("live_isolation: not-established", reference)
        self.assertIn("Admission is a necessary input", reference)
        self.assertIn("github-issue-publisher-admission-manifest/v1", reference)
        self.assertIn("version `0.3.0`", reference)
        self.assertNotIn("ADR-054", reference)

    def test_adr_rejects_same_identity_and_file_watcher_routes(self):
        adr = (
            PLUGIN_ROOT.parents[1]
            / "docs/decisions/drafts/use-a-credential-owning-github-issue-publisher.md"
        ).read_text(encoding="utf-8")
        self.assertIn("adr/use-a-credential-owning-github-issue-publisher", adr)
        self.assertIn("selected `isolated-publisher` design", adr)
        self.assertIn("### Add checks to the shell helper", adr)
        self.assertIn("### Watch `fw51.md`", adr)
        self.assertIn("### Run a same-UID broker", adr)
        self.assertIn("dedicated non-login account", adr)
        self.assertIn(
            "Step 1 establishes neither live deployment nor live isolation",
            adr,
        )
        self.assertNotIn("ADR-054", adr)


if __name__ == "__main__":
    unittest.main()
