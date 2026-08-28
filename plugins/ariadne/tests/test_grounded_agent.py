"""The grounded-agent body, its seven gates and the Elenchus runner."""

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace
import tempfile
import unittest
from unittest import mock

from . import run_tests as delivery_runner
from . import support  # noqa: F401  (sets sys.path)

import ariadne  # noqa: E402
from ariadne_lib import digests, envelope, registry, statement, verify  # noqa: E402
from ariadne_lib.predicates import grounded_agent as agent  # noqa: E402


def hex_digest(label):
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def component(path, name=None, byte_count=None):
    return {
        "name": name or path,
        "path": path,
        "sha256": hex_digest("bytes:" + path),
        "bytes": len(path.encode("utf-8")) if byte_count is None else byte_count,
    }


def predicate():
    body = {
        "release": {
            "format": agent.BEREAN_FORMAT,
            "release_version": "goldfinch-demo-v0",
            "release_digest": "0" * 64,
            "document": component("release.json", "Berean release document"),
        },
        "given": {
            "corpus": {
                "path": "corpus",
                "corpus_version": "demo-v2",
                "corpus_digest": hex_digest("semantic corpus"),
                "manifest": component("corpus-manifest.json", "corpus manifest"),
                "components": [
                    component("corpus/terms.md", "corpus terms"),
                    component("corpus/history.md", "corpus history"),
                ],
            },
            "reads": {
                "component": component("reads.jsonl", "block-bound reads"),
                "chain_id": 1,
                "block_number": 13097494,
                "block_hash": "0x" + hex_digest("block"),
                "source": "copied preserved RPC records; evidence classes unchanged",
            },
            "reads_absence_reason": None,
        },
        "produced": {
            "answers": [
                component("answers/grounded.json", "grounded answer"),
                component("answers/refusal.json", "refusal answer"),
            ],
            "evaluations": {
                "cases": component("evals/cases.json", "evaluation cases"),
                "report": component("evals/report.json", "evaluation report"),
            },
            "evaluations_absence_reason": None,
            "promotion": {
                "component": component("promotions.jsonl", "promotion chain"),
                "format": agent.BEREAN_PROMOTION_FORMAT,
                "terminal": {
                    "sequence": 1,
                    "action": "promote",
                    "target_release_digest": "0" * 64,
                },
            },
            "promotion_absence_reason": None,
        },
        "policy": {
            "question_families": ["demonstration subject state"],
            "refusal_conditions": ["questions outside the pinned corpus"],
            "rules": {
                "source_classes": list(agent.BEREAN_SOURCE_CLASSES),
                "evidence_classes": list(agent.BEREAN_EVIDENCE_CLASSES),
            },
            "allowlists": {
                "chains": [1],
                "contracts": ["0x" + "1" * 40],
            },
            "retention": "none",
        },
        "adapter": {
            "tool": "ariadne",
            "tool_version": "2.2.0",
            "command": ["python3", "scripts/ariadne.py", "capture-grounded-agent"],
            "parameters_digest": {"sha256": hex_digest("adapter parameters")},
        },
        "comparison": {
            "baseline": None,
            "current": {
                "name": "goldfinch-demo-v0",
                "release_digest": "0" * 64,
            },
            "first_capture_reason": "first Ariadne capture of this release",
        },
        "claims": [],
        "commands": [],
    }
    return finalise(body)


def finalise(body):
    release_digest = agent.semantic_release_digest(body)
    body["release"]["release_digest"] = release_digest
    body["comparison"]["current"]["release_digest"] = release_digest
    promotion = body["produced"].get("promotion")
    if isinstance(promotion, dict) and promotion.get("terminal", {}).get("action") == "promote":
        promotion["terminal"]["target_release_digest"] = release_digest
    return body


def subjects(body):
    return [
        {
            "name": entry.get("name", "malformed component"),
            "digest": {"sha256": entry["sha256"]},
        }
        for _, entry in agent.components(body)
        if isinstance(entry, dict) and agent.sha256(entry.get("sha256"))
    ]


def built(body, subject_list=None):
    return statement.Statement.from_dict(
        {
            "_type": statement.STATEMENT_TYPE,
            "subject": subjects(body) if subject_list is None else subject_list,
            "predicateType": agent.TYPE,
            "predicate": body,
        }
    )


def report(body, subject_list=None):
    raw = built(body, subject_list).to_json().encode("utf-8")
    return verify.report(envelope.read(raw), registry.DEFAULT)


def named(name, body, subject_list=None):
    for found in agent.check(built(body, subject_list)):
        if found.name == name:
            return found
    raise AssertionError("no check named %r" % name)


def numbered(number, body, subject_list=None):
    for found in agent.check(built(body, subject_list)):
        if found.number == number:
            return found
    raise AssertionError("no gate %r" % number)


class RegisteredContractTests(unittest.TestCase):
    def test_the_default_registry_has_five_predicates_and_this_is_one(self):
        self.assertEqual(len(registry.DEFAULT), 5)
        self.assertIs(registry.DEFAULT.get(agent.TYPE), agent)

    def test_the_predicates_command_lists_the_new_type(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(ariadne.main(["predicates"]), 0)
        self.assertIn(agent.TYPE, output.getvalue())

    def test_a_hand_authored_statement_runs_all_seven_gates(self):
        found = report(predicate())
        self.assertTrue(found.ok, "\n".join(found.lines()))
        self.assertEqual(found.unchecked, [])
        self.assertEqual(
            [gate.number for gate in found.ordered if gate.number is not None],
            [1, 2, 3, 4, 5, 6, 7],
        )

    def test_the_body_keeps_given_and_produced_evidence_apart(self):
        body = predicate()
        self.assertEqual(
            set(body),
            {"release", "given", "produced", "policy", "adapter", "comparison", "claims", "commands"},
        )
        self.assertIn("corpus", body["given"])
        self.assertIn("answers", body["produced"])


class ClosedShapeTests(unittest.TestCase):
    def test_every_top_level_field_is_required(self):
        for field in agent.REQUIRED_FIELDS:
            body = predicate()
            del body[field]
            with self.subTest(field=field):
                found = report(body)
                self.assertFalse(found.ok)
                self.assertIn(field, "\n".join(found.lines()))

    def test_every_nested_field_table_is_required(self):
        cases = (
            (("release",), agent.RELEASE_FIELDS),
            (("given",), agent.GIVEN_FIELDS),
            (("given", "corpus"), agent.CORPUS_FIELDS),
            (("given", "reads"), agent.READS_FIELDS),
            (("produced",), agent.PRODUCED_FIELDS),
            (("produced", "evaluations"), agent.EVALUATIONS_FIELDS),
            (("produced", "promotion"), agent.PROMOTION_FIELDS),
            (("produced", "promotion", "terminal"), agent.PROMOTION_TERMINAL_FIELDS),
            (("policy",), agent.POLICY_FIELDS),
            (("policy", "rules"), agent.RULES_FIELDS),
            (("policy", "allowlists"), agent.ALLOWLIST_FIELDS),
            (("adapter",), agent.ADAPTER_FIELDS),
            (("comparison",), agent.COMPARISON_FIELDS),
            (("comparison", "current"), agent.COMPARISON_SIDE_FIELDS),
            (("release", "document"), agent.COMPONENT_FIELDS),
        )
        for path, fields in cases:
            for field in fields:
                body = predicate()
                target = body
                for part in path:
                    target = target[part]
                del target[field]
                with self.subTest(path=".".join(path), field=field):
                    found = named("predicate-fields", body)
                    self.assertFalse(found.passed, found.detail)

    def test_unknown_fields_are_refused_at_every_domain_object_layer(self):
        paths = (
            ("release",),
            ("release", "document"),
            ("given",),
            ("given", "corpus"),
            ("given", "reads"),
            ("produced",),
            ("produced", "evaluations"),
            ("produced", "promotion"),
            ("produced", "promotion", "terminal"),
            ("policy",),
            ("policy", "rules"),
            ("policy", "allowlists"),
            ("adapter",),
            ("comparison",),
            ("comparison", "current"),
        )
        for path in paths:
            body = predicate()
            target = body
            for part in path:
                target = target[part]
            target["undeclared"] = "no"
            with self.subTest(path=".".join(path)):
                self.assertFalse(named("predicate-fields", body).passed)

    def test_core_blocks_follow_the_published_bounded_contract(self):
        body = predicate()
        digest = {"sha256": body["release"]["document"]["sha256"]}
        cases = (
            {"claims": [{"subject": digest, "disposition": "passed"}]},
            {
                "claims": [
                    {"name": " ", "subject": digest, "disposition": "passed"}
                ]
            },
            {
                "claims": [
                    {
                        "name": "failed claim",
                        "subject": digest,
                        "disposition": "failed",
                    }
                ]
            },
            {
                "claims": [
                    {
                        "name": "failed claim",
                        "subject": digest,
                        "disposition": "failed",
                        "reason": "x" * (agent.MAX_TEXT + 1),
                    }
                ]
            },
            {
                "claims": [
                    {
                        "name": "claim with null detail",
                        "subject": digest,
                        "disposition": "passed",
                        "detail": None,
                    }
                ]
            },
            {
                "commands": [
                    {"argv": ["tool"], "determinism": "nondeterministic"}
                ]
            },
            {
                "commands": [
                    {
                        "name": " ",
                        "argv": ["tool"],
                        "determinism": "nondeterministic",
                    }
                ]
            },
            {
                "commands": [
                    {
                        "name": "command with null digest",
                        "argv": ["tool"],
                        "determinism": "nondeterministic",
                        "output_digest": None,
                    }
                ]
            },
            {
                "commands": [
                    {
                        "name": "command with null detail",
                        "argv": ["tool"],
                        "determinism": "nondeterministic",
                        "detail": None,
                    }
                ]
            },
            {
                "commands": [
                    {
                        "name": "oversized argv",
                        "argv": ["x"] * (agent.MAX_COMMAND_WORDS + 1),
                        "determinism": "nondeterministic",
                    }
                ]
            },
            {
                "commands": [
                    {
                        "name": "exact command",
                        "argv": ["tool"],
                        "determinism": "exact",
                    }
                ]
            },
        )
        for index, replacement in enumerate(cases):
            candidate = predicate()
            candidate.update(replacement)
            with self.subTest(case=index):
                self.assertFalse(named("predicate-fields", candidate).passed)


class SemanticDigestTests(unittest.TestCase):
    def test_semantic_and_release_json_byte_digests_are_distinct(self):
        body = predicate()
        self.assertEqual(body["release"]["release_digest"], agent.semantic_release_digest(body))
        self.assertNotEqual(body["release"]["release_digest"], body["release"]["document"]["sha256"])
        self.assertTrue(named("release-digest", body).passed)

    def test_an_identity_change_without_a_new_semantic_digest_is_refused(self):
        body = predicate()
        body["policy"]["refusal_conditions"][0] = "a different boundary"
        found = named("release-digest", body)
        self.assertFalse(found.passed)
        self.assertIn("does not match", found.detail)

    def test_the_release_json_file_digest_cannot_replace_the_semantic_digest(self):
        body = predicate()
        mistaken = body["release"]["document"]["sha256"]
        body["release"]["release_digest"] = mistaken
        body["comparison"]["current"]["release_digest"] = mistaken
        body["produced"]["promotion"]["terminal"]["target_release_digest"] = mistaken
        self.assertFalse(named("release-digest", body).passed)

    def test_changing_only_release_json_bytes_does_not_change_semantic_identity(self):
        body = predicate()
        before = body["release"]["release_digest"]
        body["release"]["document"]["sha256"] = hex_digest("different release.json bytes")
        self.assertEqual(agent.semantic_release_digest(body), before)
        self.assertTrue(named("release-digest", body).passed)
        self.assertTrue(named("components", body).passed)


class ComponentTests(unittest.TestCase):
    def test_every_component_is_a_subject_and_no_extra_subject_is_accepted(self):
        body = predicate()
        self.assertTrue(named("components", body).passed)
        missing = subjects(body)[1:]
        self.assertFalse(named("components", body, missing).passed)
        extra = subjects(body) + [{"name": "extra", "digest": {"sha256": hex_digest("extra")}}]
        found = named("components", body, extra)
        self.assertFalse(found.passed)
        self.assertIn("does not name a declared component", found.detail)

    def test_hostile_path_and_subject_values_are_not_echoed(self):
        body = predicate()
        hostile_path = "bad\npath.json"
        body["release"]["document"]["path"] = hostile_path
        found = named("components", body)
        self.assertFalse(found.passed)
        self.assertNotIn(hostile_path, found.detail)

        body = predicate()
        hostile_name = "hostile\nsubject"
        extra = subjects(body) + [
            {"name": hostile_name, "digest": {"sha256": hex_digest("extra")}}
        ]
        found = named("components", body, extra)
        self.assertFalse(found.passed)
        self.assertNotIn(hostile_name, found.detail)

    def test_component_digest_and_byte_count_boundaries(self):
        cases = (
            ("sha256", "A" * 64),
            ("sha256", "0" * 63),
            ("bytes", True),
            ("bytes", 1.5),
            ("bytes", -1),
            ("bytes", agent.MAX_COMPONENT_BYTES + 1),
        )
        for field, value in cases:
            body = predicate()
            body["release"]["document"][field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(named("components", body).passed)

    def test_one_digest_cannot_claim_conflicting_component_byte_counts(self):
        body = predicate()
        first, second = body["given"]["corpus"]["components"]
        second["sha256"] = first["sha256"]
        second["bytes"] = first["bytes"] + 1
        found = named("components", body)
        self.assertFalse(found.passed)
        self.assertIn("same sha256", found.detail)

    def test_unsafe_component_paths_are_refused(self):
        for path in (
            "/absolute.json",
            "../outside.json",
            "corpus/../outside.json",
            "corpus\\outside.json",
            "C:outside.json",
            "./release.json",
            "corpus//file.json",
            "corpus/\u200b",
            "x" * (agent.MAX_PATH + 1),
        ):
            body = predicate()
            body["release"]["document"]["path"] = path
            with self.subTest(path=repr(path[:40])):
                self.assertFalse(named("components", body).passed)

    def test_duplicate_paths_and_normalisation_colliding_names_are_refused(self):
        body = predicate()
        body["given"]["corpus"]["components"][0]["name"] = "e\u0301 document"
        body["given"]["corpus"]["components"][1]["name"] = "\u00e9 document"
        body["given"]["corpus"]["components"][1]["path"] = body["given"]["corpus"]["components"][0]["path"]
        found = named("components", body)
        self.assertFalse(found.passed)
        self.assertIn("normalisation", found.detail)
        self.assertIn("repeats component path", found.detail)

    def test_nonportable_and_colliding_statement_subject_names_are_refused(self):
        body = predicate()
        outer = subjects(body)
        outer[0]["name"] = "e\u0301 subject"
        outer[1]["name"] = "\u00e9 subject"
        found = named("subject-names", body, outer)
        self.assertFalse(found.passed)
        self.assertIn("normalisation", found.detail)
        outer = subjects(body)
        outer[0]["name"] = "\u200b"
        self.assertFalse(named("subject-names", body, outer).passed)

    def test_ecmascript_bom_whitespace_is_refused_at_name_and_path_edges(self):
        for value in ("\ufeffname", "name\ufeff"):
            with self.subTest(kind="name", value=repr(value)):
                self.assertFalse(agent.portable_name(value))
            with self.subTest(kind="path", value=repr(value)):
                self.assertFalse(agent.usable_path(value))

    def test_the_component_count_is_bounded_before_full_walk(self):
        body = predicate()
        body["given"]["corpus"]["components"] = [
            component("corpus/%d.json" % index, "component-%d" % index)
            for index in range(agent.MAX_COMPONENTS + 1)
        ]
        found = numbered(2, body)
        self.assertFalse(found.passed)
        self.assertIn("reads at most", found.detail)

    def test_the_subject_count_bounds_coverage_work_before_full_walk(self):
        body = predicate()
        outer = subjects(body)
        digest = outer[0]["digest"]["sha256"]
        outer.extend(
            {
                "name": "oversized-subject-%d" % index,
                "digest": {"sha256": digest},
            }
            for index in range(agent.MAX_SUBJECTS + 1 - len(outer))
        )
        built_statement = built(body, outer)
        with mock.patch.object(
            built_statement,
            "covers",
            side_effect=AssertionError("unbounded subject scan"),
        ) as covers:
            faults, _, _ = agent.component_faults(built_statement)
        self.assertFalse(covers.called)
        self.assertTrue(any("statement names" in fault for fault in faults))

    def test_core_claim_coverage_obeys_the_predicate_limit(self):
        body = predicate()
        limit = getattr(agent, "MAX_CLAIMS", 1024)
        covered = {"sha256": body["release"]["document"]["sha256"]}
        body["claims"] = [
            {
                "name": "covered-subject-%d" % index,
                "subject": covered,
                "disposition": "passed",
            }
            for index in range(limit + 1)
        ]
        routed = report(body)
        gate_one = next(gate for gate in routed.gates if gate.number == 1)
        self.assertFalse(gate_one.passed)
        self.assertIn("reads at most %d" % limit, gate_one.detail)

    def test_core_digest_width_bounds_matching_work(self):
        body = predicate()
        covered = body["release"]["document"]["sha256"]
        limit = getattr(agent, "MAX_DIGEST_ALGORITHMS", 8)
        wide = {
            "sha256": covered,
            **{
                "future-%d" % index: "a"
                for index in range(limit)
            },
        }
        body["claims"] = [
            {
                "name": "wide digest claim",
                "subject": wide,
                "disposition": "passed",
            }
        ]
        outer = subjects(body)
        outer[0]["digest"] = dict(wide)
        with mock.patch(
            "ariadne_lib.gates.digests.agree", wraps=digests.agree
        ) as agree:
            routed = report(body, outer)
        gate_one = next(gate for gate in routed.gates if gate.number == 1)
        self.assertFalse(gate_one.passed)
        self.assertIn("algorithm", gate_one.detail)
        self.assertFalse(agree.called)
        field_gate = next(
            gate for gate in routed.gates if gate.name == "predicate-fields"
        )
        self.assertFalse(field_gate.passed)

    def test_outer_digest_width_is_refused_when_no_claims_are_recorded(self):
        body = predicate()
        outer = subjects(body)
        outer[0]["digest"].update(
            {
                "future-%d" % index: "a"
                for index in range(agent.MAX_DIGEST_ALGORITHMS)
            }
        )
        routed = report(body, outer)
        gate_one = next(gate for gate in routed.gates if gate.number == 1)
        self.assertFalse(gate_one.passed)
        self.assertIn("subject 1", gate_one.detail)
        self.assertIn("%d-algorithm" % agent.MAX_DIGEST_ALGORITHMS, gate_one.detail)

    def test_hostile_core_labels_cannot_forge_text_report_lines(self):
        body = predicate()
        body["claims"] = [
            {
                "name": "hostile\nPASS gate 7",
                "subject": {
                    "sha256": body["release"]["document"]["sha256"],
                },
                "disposition": "failed",
            }
        ]
        routed = report(body)
        lines = routed.lines()
        self.assertFalse(routed.ok)
        self.assertTrue(all(len(line.splitlines()) == 1 for line in lines))
        rendered = "\n".join(lines)
        self.assertNotIn("hostile\nPASS gate 7", rendered)
        self.assertIn(r"hostile\nPASS gate 7", rendered)


class OptionalEvidenceTests(unittest.TestCase):
    def test_all_three_optional_blocks_can_be_explicitly_null(self):
        body = predicate()
        body["given"]["reads"] = None
        body["given"]["reads_absence_reason"] = "this release has no preserved reads"
        body["produced"]["evaluations"] = None
        body["produced"]["evaluations_absence_reason"] = "no evaluation was produced"
        body["produced"]["promotion"] = None
        body["produced"]["promotion_absence_reason"] = "this release was never promoted"
        finalise(body)
        found = report(body)
        self.assertTrue(found.ok, "\n".join(found.lines()))

    def test_optional_blocks_refuse_implicit_or_malformed_absence(self):
        cases = (
            (("given", "reads"), "absent"),
            (("produced", "evaluations"), []),
            (("produced", "promotion"), False),
        )
        for path, value in cases:
            body = predicate()
            target = body
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            with self.subTest(path=".".join(path)):
                self.assertFalse(named("optional-evidence", body).passed)

    def test_absent_blocks_need_reasons_and_present_blocks_forbid_them(self):
        cases = (
            (("given", "reads"), ("given", "reads_absence_reason")),
            (
                ("produced", "evaluations"),
                ("produced", "evaluations_absence_reason"),
            ),
            (("produced", "promotion"), ("produced", "promotion_absence_reason")),
        )
        for block_path, reason_path in cases:
            body = predicate()
            block = body
            reason = body
            for part in block_path[:-1]:
                block = block[part]
            for part in reason_path[:-1]:
                reason = reason[part]
            block[block_path[-1]] = None
            for value in (None, " ", 1):
                reason[reason_path[-1]] = value
                with self.subTest(block=".".join(block_path), absent_reason=value):
                    self.assertFalse(named("optional-evidence", body).passed)

            body = predicate()
            reason = body
            for part in reason_path[:-1]:
                reason = reason[part]
            reason[reason_path[-1]] = "contradicts present evidence"
            with self.subTest(block=".".join(block_path), evidence="present"):
                self.assertFalse(named("optional-evidence", body).passed)

    def test_promotion_projects_no_conclusion_or_result_vocabulary(self):
        for key in ("score", "grade", "verdict", "thresholds", "passed", "failed"):
            body = predicate()
            body["produced"]["promotion"]["terminal"][key] = 1
            with self.subTest(key=key):
                self.assertFalse(named("predicate-fields", body).passed)
                if key in ("score", "grade", "verdict"):
                    gate4 = next(g for g in report(body).gates if g.number == 4)
                    self.assertFalse(gate4.passed)

    def test_a_promote_terminal_targets_this_release_and_rollback_may_name_an_earlier_one(self):
        body = predicate()
        body["produced"]["promotion"]["terminal"]["target_release_digest"] = hex_digest("other")
        self.assertFalse(named("optional-evidence", body).passed)
        body["produced"]["promotion"]["terminal"]["action"] = "rollback"
        body["produced"]["promotion"]["terminal"]["sequence"] = 2
        self.assertTrue(named("optional-evidence", body).passed)

    def test_any_promotion_terminal_requires_the_release_evaluations(self):
        for action in agent.BEREAN_PROMOTION_ACTIONS:
            body = predicate()
            terminal = body["produced"]["promotion"]["terminal"]
            terminal["action"] = action
            terminal["sequence"] = 2 if action == "rollback" else 1
            if action == "rollback":
                terminal["target_release_digest"] = hex_digest("earlier release")
            body["produced"]["evaluations"] = None
            body["produced"]["evaluations_absence_reason"] = "no evaluation was produced"
            finalise(body)
            with self.subTest(action=action):
                found = named("optional-evidence", body)
                self.assertFalse(found.passed)
                self.assertIn("promotion terminal requires evaluations", found.detail)

    def test_a_rollback_terminal_cannot_restore_the_current_release(self):
        body = predicate()
        terminal = body["produced"]["promotion"]["terminal"]
        terminal["action"] = "rollback"
        found = named("optional-evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("rollback terminal must target another release", found.detail)

    def test_promotion_sequence_matches_the_berean_chain_boundary(self):
        limit = getattr(agent, "BEREAN_MAX_PROMOTION_RECORDS", None)
        self.assertEqual(limit, 1000)
        body = predicate()
        body["produced"]["promotion"]["terminal"]["sequence"] = (
            limit
        )
        self.assertTrue(named("optional-evidence", body).passed)

        body["produced"]["promotion"]["terminal"]["sequence"] += 1
        found = named("optional-evidence", body)
        self.assertFalse(found.passed)
        self.assertIn(str(limit), found.detail)

        body = predicate()
        terminal = body["produced"]["promotion"]["terminal"]
        terminal["action"] = "rollback"
        terminal["target_release_digest"] = hex_digest("earlier release")
        terminal["sequence"] = 1
        found = named("optional-evidence", body)
        self.assertFalse(found.passed)
        self.assertIn("cannot be the first", found.detail)


class GateTwoAndFiveTests(unittest.TestCase):
    def test_gate_two_requires_format_policy_adapter_and_parameters(self):
        self.assertTrue(numbered(2, predicate()).passed)
        cases = (
            (("release", "format"), "other-release/v1"),
            (("policy", "question_families"), []),
            (("adapter", "tool"), " "),
            (("adapter", "parameters_digest"), {}),
        )
        for path, value in cases:
            body = predicate()
            target = body
            for part in path[:-1]:
                target = target[part]
            target[path[-1]] = value
            with self.subTest(path=".".join(path)):
                self.assertFalse(numbered(2, body).passed)

    def test_gate_five_accepts_first_capture_and_baseline_branches(self):
        first = predicate()
        self.assertTrue(numbered(5, first).passed)
        later = predicate()
        later["comparison"]["baseline"] = {
            "name": "goldfinch-demo-v-minus-one",
            "release_digest": hex_digest("baseline release"),
        }
        later["comparison"]["first_capture_reason"] = None
        self.assertTrue(numbered(5, later).passed)

    def test_gate_five_refuses_every_ambiguous_branch(self):
        cases = []
        body = predicate()
        body["comparison"]["first_capture_reason"] = None
        cases.append(body)
        body = predicate()
        body["comparison"]["current"]["name"] = " "
        cases.append(body)
        body = predicate()
        body["comparison"]["current"]["release_digest"] = hex_digest("not current")
        cases.append(body)
        body = predicate()
        body["comparison"]["baseline"] = copy.deepcopy(body["comparison"]["current"])
        body["comparison"]["first_capture_reason"] = None
        cases.append(body)
        body = predicate()
        body["comparison"]["baseline"] = {"name": "old", "release_digest": "bad"}
        body["comparison"]["first_capture_reason"] = None
        cases.append(body)
        body = predicate()
        body["comparison"]["baseline"] = {"name": "old", "release_digest": hex_digest("old")}
        body["comparison"]["first_capture_reason"] = "not first"
        cases.append(body)
        for index, candidate in enumerate(cases):
            with self.subTest(case=index):
                self.assertFalse(numbered(5, candidate).passed)


class EvidenceBoundaryTests(unittest.TestCase):
    def test_source_and_evidence_vocabularies_cannot_be_upgraded(self):
        for field, replacement in (
            ("source_classes", ["model_asserted"]),
            ("evidence_classes", ["proved"]),
        ):
            body = predicate()
            body["policy"]["rules"][field] = replacement
            with self.subTest(field=field):
                found = named("evidence-boundary", body)
                self.assertFalse(found.passed)

    def test_scalar_rule_vocabularies_fail_a_named_check_without_raising(self):
        for field in ("source_classes", "evidence_classes"):
            for value in (None, 0, True, 3.5):
                body = predicate()
                body["policy"]["rules"][field] = value
                with self.subTest(field=field, value=value):
                    found = named("evidence-boundary", body)
                    self.assertFalse(found.passed)
                    self.assertIn(field, found.detail)

    def test_core_gate_four_refuses_a_conclusion_key_anywhere(self):
        body = predicate()
        body["produced"]["promotion"]["terminal"]["score"] = 100
        gate = next(found for found in report(body).gates if found.number == 4)
        self.assertFalse(gate.passed)
        self.assertIn("score", gate.detail)

    def test_core_gate_seven_refuses_an_authorship_key_anywhere(self):
        body = predicate()
        body["adapter"]["verified_by"] = "ariadne"
        gate = next(found for found in report(body).gates if found.number == 7)
        self.assertFalse(gate.passed)
        self.assertIn("verified_by", gate.detail)


class RunnerTests(unittest.TestCase):
    def test_missing_report_value_is_refused(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            delivery_runner.report_target(["--elenchus-report"])
        self.assertEqual(raised.exception.code, 2)

    def test_existing_outside_and_symlinked_targets_are_refused(self):
        with tempfile.TemporaryDirectory(prefix="ariadne-runner-") as directory:
            root = Path(directory).resolve()
            existing = root / "existing.json"
            existing.write_text("keep\n", encoding="utf-8")
            real = root / "real.json"
            real.write_text("keep\n", encoding="utf-8")
            link = root / "link.json"
            link.symlink_to(real)
            outside = root.parent / (root.name + "-outside.json")
            for value in (existing, link, outside, Path("../outside.json")):
                with self.subTest(value=str(value)), mock.patch.object(
                    delivery_runner, "worktree_root", return_value=root
                ), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                    delivery_runner.report_target(["--elenchus-report", str(value)])
                self.assertEqual(raised.exception.code, 2)

    def test_a_target_created_after_validation_is_not_replaced(self):
        with tempfile.TemporaryDirectory(prefix="ariadne-runner-") as directory:
            root = Path(directory).resolve()
            report_path = root / "report.json"
            with mock.patch.object(delivery_runner, "worktree_root", return_value=root):
                target = delivery_runner.report_target(["--elenchus-report", str(report_path)])
            report_path.write_text("keep\n", encoding="utf-8")
            with self.assertRaises(OSError):
                delivery_runner.write_report(
                    target,
                    delivery_runner.result_payload(
                        SimpleNamespace(
                            testsRun=1,
                            failures=[],
                            errors=[],
                            skipped=[],
                            expectedFailures=[],
                            unexpectedSuccesses=[],
                        )
                    ),
                )
            self.assertEqual(report_path.read_text(encoding="utf-8"), "keep\n")

    def test_a_parent_replaced_by_a_symlink_is_refused(self):
        with tempfile.TemporaryDirectory(prefix="ariadne-runner-") as directory:
            root = Path(directory).resolve()
            outside = root.parent / (root.name + "-outside")
            outside.mkdir()
            self.addCleanup(outside.rmdir)
            report_path = root / "reports" / "result.json"
            with mock.patch.object(delivery_runner, "worktree_root", return_value=root):
                target = delivery_runner.report_target(["--elenchus-report", str(report_path)])
            report_path.parent.symlink_to(outside, target_is_directory=True)
            with self.assertRaises(OSError):
                delivery_runner.write_report(
                    target,
                    delivery_runner.result_payload(
                        SimpleNamespace(
                            testsRun=1,
                            failures=[],
                            errors=[],
                            skipped=[],
                            expectedFailures=[],
                            unexpectedSuccesses=[],
                        )
                    ),
                )
            self.assertFalse((outside / "result.json").exists())

    def test_a_report_without_a_proved_inode_is_not_unlinked(self):
        with tempfile.TemporaryDirectory(prefix="ariadne-runner-") as directory:
            root = Path(directory).resolve()
            report_path = root / "reports" / "result.json"
            with mock.patch.object(delivery_runner, "worktree_root", return_value=root):
                target = delivery_runner.report_target(
                    ["--elenchus-report", str(report_path)]
                )

            real_fstat = os.fstat

            def fail_regular_file(descriptor):
                found = real_fstat(descriptor)
                if stat.S_ISREG(found.st_mode):
                    raise OSError("identity unavailable")
                return found

            with mock.patch.object(
                delivery_runner.os, "fstat", side_effect=fail_regular_file
            ), mock.patch.object(
                delivery_runner.os, "unlink", wraps=os.unlink
            ) as unlink, self.assertRaises(OSError):
                delivery_runner.write_report(
                    target,
                    delivery_runner.result_payload(
                        SimpleNamespace(
                            testsRun=1,
                            failures=[],
                            errors=[],
                            skipped=[],
                            expectedFailures=[],
                            unexpectedSuccesses=[],
                        )
                    ),
                )
            self.assertFalse(unlink.called)
            self.assertTrue(report_path.exists())

    def test_a_successful_runner_writes_a_fresh_complete_report(self):
        suite = unittest.TestSuite([unittest.FunctionTestCase(lambda: None)])
        with tempfile.TemporaryDirectory(prefix="ariadne-runner-") as directory:
            root = Path(directory).resolve()
            report_path = root / "tmp" / "elenchus" / "result.json"
            with mock.patch.object(
                delivery_runner, "worktree_root", return_value=root
            ), mock.patch.object(
                delivery_runner.unittest.defaultTestLoader, "discover", return_value=suite
            ), contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(
                    delivery_runner.main(["--elenchus-report", str(report_path)]), 0
                )
            payload = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(payload["schema"], "elenchus.unittest.v1")
            self.assertTrue(payload["complete"])
            self.assertEqual(payload["testsRun"], 1)
            self.assertEqual(payload["failures"], 0)
            self.assertEqual(report_path.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
