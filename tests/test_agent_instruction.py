"""Scaffold checks for wildcat-agent-instruction/v1."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import copy
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
STUDY = ROOT / "docs/compact-agent-instruction-language/study.md"
RUNBOOK = ROOT / "docs/compact-agent-instruction-language/runbook.md"
CONTRACT = ROOT / "docs/agent-instruction-language-v1.md"
SCHEMA = ROOT / "schemas/agent-instruction-v1.schema.json"
SCRIPT = ROOT / "scripts/agent_instruction.py"
FIXTURE_README = ROOT / "tests/fixtures/agent-instruction-v1/README.md"
CODEC_FIXTURES = ROOT / "tests/fixtures/agent-instruction-v1/codec"

STUDY_SHA256 = "28c3319301ea86e91bc872d1b803fc1b7e00b9b5a9826c2b0e990d2f7d7f64aa"
RUNBOOK_SHA256 = "dd5c41a647f7119ae16db67b059ce4cf4e3fdebe5e7a27b7e9faa5019c88a93b"
SCHEMA_ID = "wildcat-agent-instruction/v1"
MAGIC = "WAI1"
FIXTURE_IDS = (
    "promise-machine-router-selection",
    "fiat-study-runbook-phase",
    "horos-boundary-check",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_script():
    spec = importlib.util.spec_from_file_location("agent_instruction", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class AgentInstructionScaffoldTests(unittest.TestCase):
    def test_study_copy_matches_receipted_digest(self):
        self.assertEqual(sha256(STUDY), STUDY_SHA256)

    def test_runbook_copy_matches_receipted_digest(self):
        self.assertEqual(sha256(RUNBOOK), RUNBOOK_SHA256)

    def test_schema_loads_as_closed_json_object(self):
        document = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(document["type"], "object")
        self.assertFalse(document["additionalProperties"])
        self.assertEqual(
            set(document["required"]),
            {"schema", "document", "sources", "sections", "relations", "bindings"},
        )

    def test_schema_freezes_version_and_directive_vocabulary(self):
        document = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(document["properties"]["schema"]["const"], SCHEMA_ID)
        self.assertEqual(
            document["$defs"]["directive"]["properties"]["kind"]["enum"],
            ["require", "forbid", "permit", "refuse", "recover", "unknown"],
        )

    def test_schema_promise_carries_the_governed_claim(self):
        document = json.loads(SCHEMA.read_text(encoding="utf-8"))
        promise = document["$defs"]["promise"]
        self.assertIn("claim", promise["required"])
        self.assertEqual(promise["properties"]["claim"], {"$ref": "#/$defs/literal"})

    def test_script_freezes_version_magic(self):
        module = load_script()
        self.assertEqual(module.SCHEMA_ID, SCHEMA_ID)
        self.assertEqual(module.MAGIC, MAGIC)

    def test_cli_help_links_contract_and_schema(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("docs/agent-instruction-language-v1.md", result.stdout)
        self.assertIn("schemas/agent-instruction-v1.schema.json", result.stdout)

    def test_fixture_layout_sentinel_names_exact_corpus(self):
        text = FIXTURE_README.read_text(encoding="utf-8")
        entries = tuple(
            line.removeprefix("- `").removesuffix("`")
            for line in text.splitlines()
            if line.startswith("- `") and line.endswith("`")
        )
        self.assertEqual(entries, FIXTURE_IDS)

    def test_horos_boundary_is_current_for_the_scaffold(self):
        from tests.test_boundary_currency import drifted_paths

        self.assertEqual(drifted_paths(ROOT), [])

    def test_existing_repository_licence_is_apache_2(self):
        text = (ROOT / "LICENSE").read_text(encoding="utf-8")
        self.assertIn("Apache License", text)
        self.assertIn("Version 2.0, January 2004", text)

    def test_existing_python_pin_matches_project_minor(self):
        self.assertEqual((ROOT / ".python-version").read_text().strip(), "3.14.6")
        project = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('requires-python = "==3.14.*"', project)

    def test_contract_cites_existing_licence_and_python_pin(self):
        text = CONTRACT.read_text(encoding="utf-8")
        self.assertIn("[Apache-2.0 licence](../LICENSE)", text)
        self.assertIn("[`.python-version`](../.python-version)", text)
        self.assertNotIn("TERMS AND CONDITIONS FOR USE", text)


AI = load_script()


def literal(kind: str, value: str) -> dict[str, str]:
    return {"kind": kind, "value": value}


def reviewer() -> dict[str, str]:
    return literal("identifier", "shoggoth")


def minimal_model() -> dict:
    return {
        "schema": SCHEMA_ID,
        "document": {"id": "doc", "title": literal("text", "Minimal model")},
        "sources": [{"id": "src", "path": "source.md", "sha256": "0" * 64}],
        "sections": [
            {
                "id": "section",
                "title": literal("text", "Section"),
                "directives": [
                    {
                        "id": "rule",
                        "kind": "require",
                        "statement": literal("text", "Keep exact bytes"),
                        "expressions": [],
                        "promise": None,
                    }
                ],
            }
        ],
        "relations": [],
        "bindings": [
            {"source": "src", "node": "doc", "start": "0", "end": "90", "reviewer": reviewer()},
            {"source": "src", "node": "section", "start": "0", "end": "90", "reviewer": reviewer()},
            {"source": "src", "node": "rule", "start": "10", "end": "70", "reviewer": reviewer()},
        ],
    }


def complete_model() -> dict:
    evidence = [
        literal("identifier", "evidence-id"),
        literal("path", "evidence/file.md"),
        literal("sha256", "a" * 64),
        literal("command", "python3 -m unittest"),
        literal("number", "42"),
        literal("date", "2026-08-30"),
        literal("link", "https://example.invalid/evidence"),
        literal("quotation", "exact quotation"),
        literal("text", "plain text"),
    ]
    promise = {
        "id": "promise",
        "claim": literal("text", "A complete claim"),
        "evidence": evidence,
        "evidence_classes": list(AI.EVIDENCE_CLASSES),
        "boundary": literal("text", "Only these bytes"),
        "authorises": [literal("command", "format")],
        "consequence": "2",
        "refuses": [literal("text", "Unknown input")],
        "recovery": [literal("text", "Restore authored source")],
        "exceptions": [
            {
                "id": "promise-exception",
                "authority": literal("identifier", "creator"),
                "gate": literal("text", "explicit approval"),
                "subject": literal("text", "one model"),
                "scope": literal("path", "docs/contract.md"),
                "record": literal("sha256", "b" * 64),
                "expiry": literal("date", "2026-12-31"),
                "recovery": literal("text", "remove exception"),
            }
        ],
    }
    directives = [
        {
            "id": "require-rule",
            "kind": "require",
            "statement": literal("text", "Require"),
            "expressions": [
                {
                    "kind": "when",
                    "predicate": literal("text", "condition"),
                    "expressions": [
                        {
                            "kind": "unless",
                            "predicate": literal("text", "counter-condition"),
                            "expressions": [],
                        }
                    ],
                },
                {
                    "kind": "scope",
                    "scope": "scope-a",
                    "expressions": [
                        {
                            "kind": "exception",
                            "target": "scope-a",
                            "predicate": literal("text", "scoped exception"),
                            "expressions": [],
                        }
                    ],
                },
                {
                    "kind": "exception",
                    "target": "require-rule",
                    "predicate": literal("text", "directive exception"),
                    "expressions": [],
                },
            ],
            "promise": promise,
        },
        {"id": "forbid-rule", "kind": "forbid", "statement": literal("text", "Forbid"), "expressions": [], "promise": None},
        {"id": "permit-rule", "kind": "permit", "statement": literal("text", "Permit"), "expressions": [], "promise": None},
        {"id": "refuse-rule", "kind": "refuse", "statement": literal("text", "Refuse"), "expressions": [], "promise": None},
        {"id": "recover-rule", "kind": "recover", "statement": literal("text", "Recover"), "expressions": [], "promise": None},
        {"id": "unknown-rule", "kind": "unknown", "statement": literal("text", "Unknown"), "expressions": [], "promise": None},
    ]
    spans = {
        "doc": (0, 1000),
        "section": (0, 1000),
        "require-rule": (10, 190),
        "scope-a": (20, 80),
        "promise": (90, 170),
        "promise-exception": (100, 140),
        "forbid-rule": (200, 290),
        "permit-rule": (300, 390),
        "refuse-rule": (400, 490),
        "recover-rule": (500, 590),
        "unknown-rule": (600, 690),
    }
    bindings = [
        {
            "source": "src",
            "node": node,
            "start": str(start),
            "end": str(end),
            "reviewer": reviewer(),
        }
        for node, (start, end) in spans.items()
    ]
    bindings.sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
    return {
        "schema": SCHEMA_ID,
        "document": {"id": "doc", "title": literal("text", "Complete model")},
        "sources": [{"id": "src", "path": "source.md", "sha256": "0" * 64}],
        "sections": [{"id": "section", "title": literal("text", "All forms"), "directives": directives}],
        "relations": [
            {"kind": "after", "source": "permit-rule", "target": "require-rule"},
            {"kind": "before", "source": "require-rule", "target": "forbid-rule"},
            {"kind": "overrides", "source": "forbid-rule", "target": "permit-rule"},
        ],
        "bindings": bindings,
    }


def section_count_model(count: int) -> dict:
    model = minimal_model()
    sections = []
    bindings = [{"source": "src", "node": "doc", "start": "0", "end": str(count * 10 + 10), "reviewer": reviewer()}]
    for index in range(count):
        section_id = f"section-{index:03d}"
        directive_id = f"rule-{index:03d}"
        start = index * 10
        sections.append(
            {
                "id": section_id,
                "title": literal("text", "s"),
                "directives": [
                    {
                        "id": directive_id,
                        "kind": "require",
                        "statement": literal("text", "r"),
                        "expressions": [],
                        "promise": None,
                    }
                ],
            }
        )
        bindings.extend(
            [
                {"source": "src", "node": section_id, "start": str(start), "end": str(start + 9), "reviewer": reviewer()},
                {"source": "src", "node": directive_id, "start": str(start + 1), "end": str(start + 8), "reviewer": reviewer()},
            ]
        )
    bindings.sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
    model["sections"] = sections
    model["bindings"] = bindings
    return model


def directive_count_model(count: int) -> dict:
    model = minimal_model()
    directives = []
    bindings = [
        {"source": "src", "node": "doc", "start": "0", "end": str(count * 3 + 10), "reviewer": reviewer()},
        {"source": "src", "node": "section", "start": "0", "end": str(count * 3 + 10), "reviewer": reviewer()},
    ]
    for index in range(count):
        identifier = f"rule-{index:04d}"
        start = index * 3 + 1
        directives.append(
            {
                "id": identifier,
                "kind": "require",
                "statement": literal("text", "r"),
                "expressions": [],
                "promise": None,
            }
        )
        bindings.append(
            {"source": "src", "node": identifier, "start": str(start), "end": str(start + 1), "reviewer": reviewer()}
        )
    bindings.sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
    model["sections"][0]["directives"] = directives
    model["bindings"] = bindings
    return model


def relation_count_model(count: int) -> dict:
    directive_count = 129
    model = directive_count_model(directive_count)
    ids = [entry["id"] for entry in model["sections"][0]["directives"]]
    relations = []
    for left_index, source in enumerate(ids):
        for target in ids[left_index + 1 :]:
            relations.append({"kind": "before", "source": source, "target": target})
            if len(relations) == count:
                model["relations"] = relations
                return model
    raise AssertionError("not enough unique acyclic relation pairs")


def exception_count_model(count: int) -> dict:
    model = minimal_model()
    directive = model["sections"][0]["directives"][0]
    directive["promise"] = {
        "id": "promise",
        "claim": literal("text", "claim"),
        "evidence": [literal("text", "e")],
        "evidence_classes": ["checked"],
        "boundary": literal("text", "b"),
        "authorises": [literal("text", "a")],
        "consequence": "0",
        "refuses": [literal("text", "j")],
        "recovery": [literal("text", "z")],
        "exceptions": [],
    }
    exceptions = []
    bindings = [
        {"source": "src", "node": "doc", "start": "0", "end": str(count * 3 + 30), "reviewer": reviewer()},
        {"source": "src", "node": "section", "start": "0", "end": str(count * 3 + 30), "reviewer": reviewer()},
        {"source": "src", "node": "rule", "start": "1", "end": str(count * 3 + 20), "reviewer": reviewer()},
        {"source": "src", "node": "promise", "start": "2", "end": str(count * 3 + 10), "reviewer": reviewer()},
    ]
    for index in range(count):
        identifier = f"exception-{index:04d}"
        exceptions.append(
            {
                "id": identifier,
                "authority": literal("text", "a"),
                "gate": literal("text", "g"),
                "subject": literal("text", "s"),
                "scope": literal("text", "c"),
                "record": literal("text", "r"),
                "expiry": literal("text", "e"),
                "recovery": literal("text", "z"),
            }
        )
        start = index * 3 + 3
        bindings.append(
            {"source": "src", "node": identifier, "start": str(start), "end": str(start + 1), "reviewer": reviewer()}
        )
    directive["promise"]["exceptions"] = exceptions
    bindings.sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
    model["bindings"] = bindings
    return model


def line_limit_model(end_extra: int = 0) -> dict:
    model = minimal_model()
    start_width = 32745
    end_width = start_width + end_extra
    start = "1" + "0" * (start_width - 1)
    end = ("2" if end_extra == 0 else "1") + "0" * (end_width - 1)
    outer_end = "1" + "0" * end_width
    model["bindings"][0]["end"] = outer_end
    model["bindings"][1]["end"] = outer_end
    model["bindings"][2]["start"] = start
    model["bindings"][2]["end"] = end
    return model


def file_and_line_count_limit_model() -> dict:
    model = minimal_model()
    directive = model["sections"][0]["directives"][0]
    evidence = [literal("text", "") for _ in range(AI.MAX_EXPRESSIONS)]
    authorisation_count = AI.MAX_LINES - 15 - len(evidence)
    evidence[:12] = [literal("text", " " * 32759) for _ in range(12)]
    evidence[12] = literal("text", " " * 16340 + "x")
    directive["promise"] = {
        "id": "promise",
        "claim": literal("text", ""),
        "evidence": evidence,
        "evidence_classes": ["checked"],
        "boundary": literal("text", ""),
        "authorises": [literal("text", "") for _ in range(authorisation_count)],
        "consequence": "0",
        "refuses": [literal("text", "")],
        "recovery": [literal("text", "")],
        "exceptions": [],
    }
    model["bindings"] = [
        {"source": "src", "node": "doc", "start": "0", "end": "100", "reviewer": reviewer()},
        {"source": "src", "node": "section", "start": "0", "end": "100", "reviewer": reviewer()},
        {"source": "src", "node": "rule", "start": "10", "end": "90", "reviewer": reviewer()},
        {"source": "src", "node": "promise", "start": "20", "end": "80", "reviewer": reviewer()},
    ]
    return model


class RefusalAssertions:
    def assertRefusal(self, code: str, function, *arguments):
        with self.assertRaises(AI.CodecError) as raised:
            function(*arguments)
        self.assertTrue(raised.exception.code.startswith(code), raised.exception.code)
        self.assertLessEqual(len(raised.exception.node_path), 512)


class CanonicalModelTests(RefusalAssertions, unittest.TestCase):
    def test_minimal_model_validates(self):
        model = minimal_model()
        self.assertIs(AI.validate_model(model), model)

    def test_complete_model_validates_every_field(self):
        model = complete_model()
        self.assertIs(AI.validate_model(model), model)

    def test_canonical_json_has_sorted_keys_and_final_lf(self):
        encoded = AI.canonical_json_bytes(minimal_model())
        self.assertTrue(encoded.endswith(b"\n"))
        self.assertTrue(encoded.startswith(b'{"bindings":'))

    def test_canonical_json_load_round_trip(self):
        model = minimal_model()
        encoded = AI.canonical_json_bytes(model)
        self.assertEqual(AI.load_canonical_json(encoded), model)

    def test_duplicate_json_key_refuses(self):
        data = (CODEC_FIXTURES / "invalid-duplicate-key.json").read_bytes()
        self.assertRefusal("WAI-E-JSON.DUPLICATE_KEY", AI.load_canonical_json, data)

    def test_json_integer_refuses(self):
        self.assertRefusal("WAI-E-JSON.NUMBER", AI.load_canonical_json, b'{"x":1}\n')

    def test_json_float_refuses(self):
        self.assertRefusal("WAI-E-JSON.NUMBER", AI.load_canonical_json, b'{"x":1.0}\n')

    def test_json_nan_refuses(self):
        self.assertRefusal("WAI-E-JSON.NUMBER", AI.load_canonical_json, b'{"x":NaN}\n')

    def test_json_bom_refuses(self):
        self.assertRefusal("WAI-E-UTF8.BOM", AI.load_canonical_json, b"\xef\xbb\xbf{}\n")

    def test_json_invalid_utf8_refuses(self):
        self.assertRefusal("WAI-E-UTF8.DECODE", AI.load_canonical_json, b"\xff")

    def test_noncanonical_json_whitespace_refuses(self):
        data = json.dumps(minimal_model(), indent=2).encode() + b"\n"
        self.assertRefusal("WAI-E-CANONICAL.JSON", AI.load_canonical_json, data)

    def test_unknown_root_field_refuses(self):
        model = minimal_model()
        model["extra"] = None
        self.assertRefusal("WAI-E-SHAPE.FIELDS", AI.validate_model, model)

    def test_missing_root_field_refuses(self):
        model = minimal_model()
        del model["relations"]
        self.assertRefusal("WAI-E-SHAPE.FIELDS", AI.validate_model, model)

    def test_unsupported_directive_kind_refuses(self):
        model = minimal_model()
        model["sections"][0]["directives"][0]["kind"] = "suggest"
        self.assertRefusal("WAI-E-SHAPE.DIRECTIVE_KIND", AI.validate_model, model)

    def test_unsupported_literal_kind_refuses(self):
        model = minimal_model()
        model["document"]["title"]["kind"] = "prose"
        self.assertRefusal("WAI-E-SHAPE.LITERAL_KIND", AI.validate_model, model)

    def test_unsupported_expression_kind_refuses(self):
        model = minimal_model()
        model["sections"][0]["directives"][0]["expressions"] = [
            {"kind": "maybe", "predicate": literal("text", "x"), "expressions": []}
        ]
        self.assertRefusal("WAI-E-SHAPE.EXPRESSION_KIND", AI.validate_model, model)

    def test_unsupported_relation_kind_refuses(self):
        model = complete_model()
        model["relations"][0]["kind"] = "equals"
        self.assertRefusal("WAI-E-SHAPE.RELATION_KIND", AI.validate_model, model)

    def test_unsupported_schema_version_refuses(self):
        model = minimal_model()
        model["schema"] = "wildcat-agent-instruction/v2"
        self.assertRefusal("WAI-E-VERSION.SCHEMA", AI.validate_model, model)

    def test_dangling_binding_source_refuses(self):
        model = minimal_model()
        model["bindings"][0]["source"] = "missing"
        model["bindings"].sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
        self.assertRefusal("WAI-E-REFERENCE.BINDING", AI.validate_model, model)

    def test_dangling_binding_node_refuses(self):
        model = minimal_model()
        model["bindings"][0]["node"] = "missing"
        model["bindings"].sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
        self.assertRefusal("WAI-E-REFERENCE.BINDING", AI.validate_model, model)

    def test_duplicate_node_id_refuses(self):
        model = minimal_model()
        model["sections"][0]["id"] = "doc"
        self.assertRefusal("WAI-E-REFERENCE.DUPLICATE_ID", AI.validate_model, model)

    def test_source_order_refuses(self):
        model = minimal_model()
        model["sources"] = [
            {"id": "z", "path": "z.md", "sha256": "0" * 64},
            {"id": "a", "path": "a.md", "sha256": "1" * 64},
        ]
        self.assertRefusal("WAI-E-CANONICAL.SOURCES", AI.validate_model, model)

    def test_relation_order_refuses(self):
        model = complete_model()
        model["relations"].reverse()
        self.assertRefusal("WAI-E-CANONICAL.RELATIONS", AI.validate_model, model)

    def test_binding_order_refuses(self):
        model = minimal_model()
        model["bindings"].reverse()
        self.assertRefusal("WAI-E-CANONICAL.BINDINGS", AI.validate_model, model)

    def test_evidence_class_order_refuses(self):
        model = complete_model()
        model["sections"][0]["directives"][0]["promise"]["evidence_classes"][:2] = ["recomputed", "checked"]
        self.assertRefusal("WAI-E-CANONICAL.EVIDENCE_CLASSES", AI.validate_model, model)

    def test_dangling_relation_refuses(self):
        model = complete_model()
        model["relations"][0]["target"] = "missing"
        self.assertRefusal("WAI-E-REFERENCE.RELATION", AI.validate_model, model)

    def test_self_relation_refuses(self):
        model = complete_model()
        model["relations"][0]["target"] = model["relations"][0]["source"]
        self.assertRefusal("WAI-E-REFERENCE.SELF_RELATION", AI.validate_model, model)

    def test_precedence_cycle_refuses(self):
        model = complete_model()
        model["relations"] = [
            {"kind": "before", "source": "forbid-rule", "target": "require-rule"},
            {"kind": "before", "source": "require-rule", "target": "forbid-rule"},
        ]
        self.assertRefusal("WAI-E-CYCLE.PRECEDENCE", AI.validate_model, model)

    def test_exception_outside_ancestor_scope_refuses(self):
        model = complete_model()
        expression = model["sections"][0]["directives"][0]["expressions"][1]["expressions"][0]
        expression["target"] = "forbid-rule"
        self.assertRefusal("WAI-E-REFERENCE.EXCEPTION_TARGET", AI.validate_model, model)

    def test_exception_can_target_containing_directive(self):
        model = complete_model()
        AI.validate_model(model)

    def test_exception_can_target_ancestor_scope(self):
        model = complete_model()
        nested = model["sections"][0]["directives"][0]["expressions"][1]["expressions"][0]
        self.assertEqual(nested["target"], "scope-a")
        AI.validate_model(model)

    def test_nested_scope_has_declared_binding_ancestry(self):
        model = complete_model()
        outer = model["sections"][0]["directives"][0]["expressions"][1]
        outer["expressions"] = [{"kind": "scope", "scope": "scope-b", "expressions": outer["expressions"]}]
        scope_b = {"source": "src", "node": "scope-b", "start": "30", "end": "70", "reviewer": reviewer()}
        model["bindings"].append(scope_b)
        model["bindings"].sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
        nested_exception = outer["expressions"][0]["expressions"][0]
        nested_exception["target"] = "scope-b"
        AI.validate_model(model)

    def test_uncovered_governed_node_refuses(self):
        model = minimal_model()
        model["bindings"] = [entry for entry in model["bindings"] if entry["node"] != "rule"]
        self.assertRefusal("WAI-E-REFERENCE.UNCOVERED", AI.validate_model, model)

    def test_empty_span_refuses(self):
        model = minimal_model()
        model["bindings"][2]["end"] = model["bindings"][2]["start"]
        self.assertRefusal("WAI-E-REFERENCE.SPAN", AI.validate_model, model)

    def test_large_decimal_spans_validate_without_runtime_conversion(self):
        model = minimal_model()
        outer_end = "2" + "0" * 4301
        inner_start = "9" * 4301
        inner_end = "1" + "0" * 4301
        model["bindings"][0]["end"] = outer_end
        model["bindings"][1]["end"] = outer_end
        model["bindings"][2]["start"] = inner_start
        model["bindings"][2]["end"] = inner_end
        try:
            compact = AI.format_compact(model)
        except Exception as error:
            self.fail(f"valid decimal spans raised {type(error).__name__}")
        decoded, canonical = AI.decode_compact(compact)
        self.assertEqual(decoded, model)
        self.assertEqual(canonical, AI.canonical_json_bytes(model))

    def test_unrelated_binding_overlap_refuses(self):
        model = complete_model()
        forbid = next(entry for entry in model["bindings"] if entry["node"] == "forbid-rule")
        forbid["start"], forbid["end"] = "100", "180"
        model["bindings"].sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
        self.assertRefusal("WAI-E-REFERENCE.OVERLAP", AI.validate_model, model)

    def test_declared_nested_binding_overlap_is_valid(self):
        AI.validate_model(complete_model())

    def test_identifier_at_limit_is_valid(self):
        model = minimal_model()
        identifier = "a" + "b" * (AI.MAX_ID_BYTES - 1)
        model["sections"][0]["directives"][0]["id"] = identifier
        model["bindings"][2]["node"] = identifier
        AI.validate_model(model)

    def test_identifier_limit_plus_one_refuses(self):
        model = minimal_model()
        identifier = "a" + "b" * AI.MAX_ID_BYTES
        model["sections"][0]["directives"][0]["id"] = identifier
        model["bindings"][2]["node"] = identifier
        self.assertRefusal("WAI-E-BOUNDS.IDENTIFIER", AI.validate_model, model)

    def test_literal_at_limit_is_valid(self):
        model = minimal_model()
        model["document"]["title"]["value"] = "x" * AI.MAX_LITERAL_BYTES
        AI.validate_model(model)
        AI.format_compact(model)

    def test_literal_limit_plus_one_refuses(self):
        model = minimal_model()
        model["document"]["title"]["value"] = "x" * (AI.MAX_LITERAL_BYTES + 1)
        self.assertRefusal("WAI-E-BOUNDS.LITERAL", AI.validate_model, model)

    def test_source_count_at_limit_is_valid(self):
        model = minimal_model()
        model["sources"] = [
            {"id": f"s{index:02d}", "path": f"s{index:02d}.md", "sha256": f"{index:064x}"}
            for index in range(AI.MAX_SOURCES)
        ]
        model["bindings"] = [{**entry, "source": "s00"} for entry in model["bindings"]]
        AI.validate_model(model)

    def test_source_count_limit_plus_one_refuses(self):
        model = minimal_model()
        model["sources"] = [
            {"id": f"s{index:02d}", "path": f"s{index:02d}.md", "sha256": f"{index:064x}"}
            for index in range(AI.MAX_SOURCES + 1)
        ]
        self.assertRefusal("WAI-E-BOUNDS.COUNT", AI.validate_model, model)

    def test_unsafe_source_path_refuses(self):
        model = minimal_model()
        model["sources"][0]["path"] = "../source.md"
        self.assertRefusal("WAI-E-PATH.UNSAFE", AI.validate_model, model)

    def test_object_member_cap_at_limit_is_valid(self):
        value = {f"k{index}": "v" for index in range(AI.MAX_OBJECT_MEMBERS)}
        self.assertIs(AI._object(value, tuple(value), "$"), value)

    def test_object_member_cap_limit_plus_one_refuses(self):
        value = {f"k{index}": "v" for index in range(AI.MAX_OBJECT_MEMBERS + 1)}
        self.assertRefusal("WAI-E-BOUNDS.MEMBERS", AI._object, value, tuple(value), "$")

    def test_path_cap_at_limit_is_valid(self):
        model = minimal_model()
        model["sources"][0]["path"] = "p" * AI.MAX_PATH_BYTES
        AI.validate_model(model)

    def test_path_cap_limit_plus_one_refuses(self):
        model = minimal_model()
        model["sources"][0]["path"] = "p" * (AI.MAX_PATH_BYTES + 1)
        self.assertRefusal("WAI-E-BOUNDS.PATH", AI.validate_model, model)

    def test_total_literal_cap_at_limit_is_valid(self):
        model = minimal_model()
        model["document"]["title"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
        model["sections"][0]["title"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
        directive = model["sections"][0]["directives"][0]
        directive["statement"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
        directive["expressions"] = [
            {"kind": "when", "predicate": literal("text", "x" * AI.MAX_LITERAL_BYTES), "expressions": []}
            for _ in range(9)
        ]
        remainder = AI.MAX_TOTAL_LITERAL_BYTES - (12 * AI.MAX_LITERAL_BYTES) - (3 * len("shoggoth"))
        directive["expressions"].append(
            {"kind": "when", "predicate": literal("text", "x" * remainder), "expressions": []}
        )
        AI.validate_model(model)
        AI.format_compact(model)

    def test_total_literal_cap_limit_plus_one_refuses(self):
        model = minimal_model()
        model["document"]["title"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
        model["sections"][0]["title"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
        directive = model["sections"][0]["directives"][0]
        directive["statement"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
        directive["expressions"] = [
            {"kind": "when", "predicate": literal("text", "x" * AI.MAX_LITERAL_BYTES), "expressions": []}
            for _ in range(9)
        ]
        remainder = AI.MAX_TOTAL_LITERAL_BYTES - (12 * AI.MAX_LITERAL_BYTES) - (3 * len("shoggoth")) + 1
        directive["expressions"].append(
            {"kind": "when", "predicate": literal("text", "x" * remainder), "expressions": []}
        )
        self.assertRefusal("WAI-E-BOUNDS.LITERALS", AI.validate_model, model)

    def test_section_cap_at_limit_is_valid(self):
        AI.validate_model(section_count_model(AI.MAX_SECTIONS))

    def test_section_cap_limit_plus_one_refuses(self):
        self.assertRefusal("WAI-E-BOUNDS.COUNT", AI.validate_model, section_count_model(AI.MAX_SECTIONS + 1))

    def test_directive_cap_at_limit_is_valid(self):
        AI.validate_model(directive_count_model(AI.MAX_DIRECTIVES))

    def test_directive_cap_limit_plus_one_refuses(self):
        self.assertRefusal("WAI-E-BOUNDS.COUNT", AI.validate_model, directive_count_model(AI.MAX_DIRECTIVES + 1))

    def test_expression_cap_at_limit_is_valid(self):
        model = minimal_model()
        model["sections"][0]["directives"][0]["expressions"] = [
            {"kind": "when", "predicate": literal("text", ""), "expressions": []}
            for _ in range(AI.MAX_EXPRESSIONS)
        ]
        AI.validate_model(model)

    def test_expression_cap_limit_plus_one_refuses(self):
        model = minimal_model()
        model["sections"][0]["directives"][0]["expressions"] = [
            {"kind": "when", "predicate": literal("text", ""), "expressions": []}
            for _ in range(AI.MAX_EXPRESSIONS + 1)
        ]
        self.assertRefusal("WAI-E-BOUNDS.COUNT", AI.validate_model, model)

    def test_relation_cap_at_limit_is_valid(self):
        AI.validate_model(relation_count_model(AI.MAX_RELATIONS))

    def test_relation_cap_limit_plus_one_refuses(self):
        model = relation_count_model(AI.MAX_RELATIONS)
        model["relations"].append(copy.deepcopy(model["relations"][-1]))
        self.assertRefusal("WAI-E-BOUNDS.COUNT", AI.validate_model, model)

    def test_binding_cap_at_limit_is_valid(self):
        model = minimal_model()
        bindings = [
            {"source": "src", "node": "doc", "start": "0", "end": str(1000 + index), "reviewer": reviewer()}
            for index in range(AI.MAX_BINDINGS - 2)
        ]
        bindings.extend(
            [
                {"source": "src", "node": "section", "start": "0", "end": "900", "reviewer": reviewer()},
                {"source": "src", "node": "rule", "start": "1", "end": "2", "reviewer": reviewer()},
            ]
        )
        bindings.sort(key=lambda item: (item["source"], int(item["start"]), int(item["end"]), item["node"], item["reviewer"]["value"]))
        model["bindings"] = bindings
        AI.validate_model(model)

    def test_binding_cap_limit_plus_one_refuses(self):
        model = minimal_model()
        model["bindings"] = [copy.deepcopy(model["bindings"][0]) for _ in range(AI.MAX_BINDINGS + 1)]
        self.assertRefusal("WAI-E-BOUNDS.COUNT", AI.validate_model, model)

    def test_promise_exception_cap_at_limit_is_valid(self):
        AI.validate_model(exception_count_model(AI.MAX_PROMISE_EXCEPTIONS))

    def test_promise_exception_cap_limit_plus_one_refuses(self):
        self.assertRefusal(
            "WAI-E-BOUNDS.COUNT",
            AI.validate_model,
            exception_count_model(AI.MAX_PROMISE_EXCEPTIONS + 1),
        )


class CompactCodecTests(RefusalAssertions, unittest.TestCase):
    def test_minimal_round_trip_bytes(self):
        model = minimal_model()
        compact = AI.format_compact(model)
        decoded, canonical = AI.decode_compact(compact)
        self.assertEqual(decoded, model)
        self.assertEqual(canonical, AI.canonical_json_bytes(model))

    def test_complete_round_trip_covers_every_field(self):
        model = complete_model()
        decoded, _ = AI.decode_compact(AI.format_compact(model))
        self.assertEqual(decoded, model)

    def test_formatter_is_idempotent(self):
        compact = AI.format_compact(complete_model())
        model, _ = AI.decode_compact(compact)
        self.assertEqual(AI.format_compact(model), compact)

    def test_output_has_exact_final_newline(self):
        compact = AI.format_compact(minimal_model())
        self.assertTrue(compact.endswith(b"\n"))
        self.assertFalse(compact.endswith(b"\n\n"))

    def test_output_uses_two_space_nesting(self):
        lines = AI.format_compact(complete_model()).decode().splitlines()
        self.assertTrue(any(line.startswith("      W ") for line in lines))
        self.assertTrue(any(line.startswith("        N ") for line in lines))
        self.assertFalse(any(line.startswith("\t") for line in lines))

    def test_every_opcode_is_emitted(self):
        opcodes = {line.lstrip().split(" ", 1)[0] for line in AI.format_compact(complete_model()).decode().splitlines()[1:]}
        self.assertEqual(opcodes, set("DSHRFPXYUWNCMVKGAQJZI<>^BE"))

    def test_every_literal_tag_is_emitted(self):
        compact = AI.format_compact(complete_model()).decode()
        for tag in AI.LITERAL_TAGS.values():
            self.assertRegex(compact, rf"(?:^| ){re.escape(tag)}[0-9]+:")

    def test_unicode_length_counts_utf8_bytes(self):
        token = AI.encode_literal(literal("text", "猫"))
        self.assertEqual(token, "t3:猫")
        self.assertEqual(AI.decode_literal(token), literal("text", "猫"))

    def test_empty_literal_has_zero_length(self):
        self.assertEqual(AI.encode_literal(literal("text", "")), "t0:")
        self.assertEqual(AI.decode_literal("t0:"), literal("text", ""))

    def test_declared_length_too_short_refuses(self):
        self.assertRefusal("WAI-E-COMPACT.LENGTH", AI.decode_literal, "t1:cat")

    def test_declared_length_too_long_refuses(self):
        self.assertRefusal("WAI-E-COMPACT.LENGTH", AI.decode_literal, "t4:cat")

    def test_oversized_decimal_length_refuses_without_runtime_conversion(self):
        try:
            AI.decode_literal("t" + "9" * 4301 + ":")
        except Exception as error:
            self.assertIsInstance(error, AI.CodecError)
            self.assertTrue(error.code.startswith("WAI-E-BOUNDS.LITERAL"), error.code)
        else:
            self.fail("oversized decimal length was accepted")

    def test_lowercase_hex_escape_refuses(self):
        self.assertRefusal("WAI-E-COMPACT.ESCAPE", AI.decode_literal, "t1:\\x0f")

    def test_hex_escape_for_printable_refuses(self):
        self.assertRefusal("WAI-E-CANONICAL.ESCAPE", AI.decode_literal, "t1:\\x41")

    def test_raw_colon_refuses(self):
        self.assertRefusal("WAI-E-CANONICAL.ESCAPE", AI.decode_literal, "t1::")

    def test_wrong_magic_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"WAI1", b"WAI2", 1)
        self.assertRefusal("WAI-E-VERSION.MAGIC", AI.decode_compact, compact)

    def test_unknown_opcode_refuses(self):
        data = (CODEC_FIXTURES / "invalid-unknown-opcode.wai").read_bytes()
        self.assertRefusal("WAI-E-COMPACT.OPCODE", AI.decode_compact, data)

    def test_unknown_literal_tag_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"D i3:doc", b"D v3:doc", 1)
        self.assertRefusal("WAI-E-COMPACT.LITERAL", AI.decode_compact, compact)

    def test_missing_final_lf_refuses(self):
        compact = AI.format_compact(minimal_model()).rstrip(b"\n")
        self.assertRefusal("WAI-E-COMPACT.NEWLINE", AI.decode_compact, compact)

    def test_double_final_lf_refuses(self):
        compact = AI.format_compact(minimal_model()) + b"\n"
        self.assertRefusal("WAI-E-COMPACT.NEWLINE", AI.decode_compact, compact)

    def test_crlf_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"\n", b"\r\n")
        self.assertRefusal("WAI-E-COMPACT.NEWLINE", AI.decode_compact, compact)

    def test_blank_record_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"\n  S", b"\n\n  S", 1)
        self.assertRefusal("WAI-E-COMPACT.WHITESPACE", AI.decode_compact, compact)

    def test_trailing_space_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"\n  S", b" \n  S", 1)
        self.assertRefusal("WAI-E-COMPACT.WHITESPACE", AI.decode_compact, compact)

    def test_tab_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"  S", b"\tS", 1)
        self.assertRefusal("WAI-E-COMPACT.WHITESPACE", AI.decode_compact, compact)

    def test_odd_indentation_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"  S", b" S", 1)
        self.assertRefusal("WAI-E-COMPACT.INDENT", AI.decode_compact, compact)

    def test_depth_limit_plus_one_refuses(self):
        compact = b"WAI1\n" + b"  " * (AI.MAX_DEPTH + 1) + b"D i3:doc t1:x\n"
        self.assertRefusal("WAI-E-BOUNDS.DEPTH", AI.decode_compact, compact)

    def test_depth_limit_at_limit_round_trips(self):
        model = minimal_model()
        expression = {"kind": "when", "predicate": literal("text", "x"), "expressions": []}
        for _ in range(AI.MAX_DEPTH - 3):
            expression = {"kind": "when", "predicate": literal("text", "x"), "expressions": [expression]}
        model["sections"][0]["directives"][0]["expressions"] = [expression]
        compact = AI.format_compact(model)
        self.assertEqual(AI.decode_compact(compact)[0], model)

    def test_line_limit_plus_one_refuses(self):
        try:
            AI.format_compact(line_limit_model(end_extra=1))
        except Exception as error:
            self.assertIsInstance(error, AI.CodecError)
            self.assertTrue(error.code.startswith("WAI-E-BOUNDS.LINE"), error.code)
        else:
            self.fail("a valid record one byte over the line limit was accepted")

    def test_line_limit_at_limit_round_trips(self):
        model = line_limit_model()
        try:
            compact = AI.format_compact(model)
        except Exception as error:
            self.fail(f"valid line-limit model raised {type(error).__name__}")
        self.assertEqual(max(len(line) for line in compact.splitlines()), AI.MAX_LINE_BYTES)
        self.assertEqual(AI.decode_compact(compact)[0], model)

    def test_file_and_physical_line_caps_at_limit_round_trip(self):
        model = file_and_line_count_limit_model()
        compact = AI.format_compact(model)
        self.assertEqual(len(compact), AI.MAX_FILE_BYTES)
        self.assertEqual(len(compact.splitlines()), AI.MAX_LINES)
        self.assertEqual(AI.decode_compact(compact)[0], model)

    def test_physical_line_count_limit_plus_one_refuses(self):
        compact = b"WAI1\n" + b"?\n" * AI.MAX_LINES
        self.assertRefusal("WAI-E-BOUNDS.LINES", AI.decode_compact, compact)

    def test_file_cap_limit_plus_one_refuses(self):
        data = b"WAI1\n" + b"x" * (AI.MAX_FILE_BYTES - len(b"WAI1\n") + 1)
        self.assertRefusal("WAI-E-BOUNDS.FILE", AI.decode_compact, data)

    def test_record_out_of_order_refuses(self):
        compact = AI.format_compact(minimal_model())
        lines = compact.splitlines(keepends=True)
        malformed = b"".join([lines[0], lines[1], lines[3], lines[2], *lines[4:]])
        self.assertRefusal("WAI-E-COMPACT.ORDER", AI.decode_compact, malformed)

    def test_extra_record_field_refuses(self):
        compact = AI.format_compact(minimal_model()).replace(b"D i3:doc", b"D i3:doc i1:x", 1)
        self.assertRefusal("WAI-E-COMPACT.FIELDS", AI.decode_compact, compact)

    def test_truncated_promise_refuses(self):
        data = (CODEC_FIXTURES / "invalid-truncated-literal.wai").read_bytes()
        self.assertRefusal("WAI-E-COMPACT", AI.decode_compact, data)

    def test_noncanonical_relation_order_refuses(self):
        lines = AI.format_compact(complete_model()).splitlines(keepends=True)
        positions = [index for index, line in enumerate(lines) if line.startswith((b"  <", b"  >", b"  ^"))]
        lines[positions[0]], lines[positions[1]] = lines[positions[1]], lines[positions[0]]
        self.assertRefusal("WAI-E-CANONICAL.RELATIONS", AI.decode_compact, b"".join(lines))

    def test_bad_evidence_class_token_refuses(self):
        compact = AI.format_compact(complete_model()).replace(b"K checked", b"K guessed", 1)
        self.assertRefusal("WAI-E-COMPACT.TOKEN", AI.decode_compact, compact)

    def test_bad_consequence_token_refuses(self):
        compact = AI.format_compact(complete_model()).replace(b"Q 2", b"Q 9", 1)
        self.assertRefusal("WAI-E-COMPACT.TOKEN", AI.decode_compact, compact)

    def test_decoder_refusal_returns_no_partial_model(self):
        try:
            AI.decode_compact(b"WAI1\n?\n")
        except AI.CodecError as error:
            self.assertIsInstance(error.code, str)
            self.assertFalse(hasattr(error, "model"))
        else:
            self.fail("malformed compact input was accepted")

    def test_valid_fixture_round_trips(self):
        canonical = (CODEC_FIXTURES / "valid-minimal.json").read_bytes()
        model = AI.load_canonical_json(canonical)
        self.assertEqual(AI.decode_compact(AI.format_compact(model))[1], canonical)

    def test_valid_compact_fixture_matches_formatter(self):
        model = AI.load_canonical_json((CODEC_FIXTURES / "valid-minimal.json").read_bytes())
        compact = (CODEC_FIXTURES / "valid-minimal.wai").read_bytes()
        self.assertEqual(AI.format_compact(model), compact)
        self.assertEqual(AI.decode_compact(compact)[0], model)


def _make_escape_test(name: str, value: str, expected: str):
    def test(self):
        token = AI.encode_literal(literal("text", value))
        self.assertEqual(token, expected)
        self.assertEqual(AI.decode_literal(token), literal("text", value))

    test.__name__ = f"test_escape_{name}"
    return test


for _name, _value, _expected in (
    ("backslash", "\\", "t1:\\\\"),
    ("space", " ", "t1:\\s"),
    ("colon", ":", "t1:\\:"),
    ("tab", "\t", "t1:\\t"),
    ("newline", "\n", "t1:\\n"),
    ("carriage_return", "\r", "t1:\\r"),
    ("nul", "\x00", "t1:\\x00"),
    ("delete", "\x7f", "t1:\\x7F"),
):
    setattr(CompactCodecTests, f"test_escape_{_name}", _make_escape_test(_name, _value, _expected))


class PathBoundaryTests(RefusalAssertions, unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_read_regular_file(self):
        (self.root / "input.json").write_bytes(b"bytes")
        self.assertEqual(AI.read_confined(self.root, "input.json"), b"bytes")

    def test_traversal_refuses(self):
        self.assertRefusal("WAI-E-PATH.UNSAFE", AI.read_confined, self.root, "../input")

    def test_absolute_path_refuses(self):
        self.assertRefusal("WAI-E-PATH.UNSAFE", AI.read_confined, self.root, "/input")

    def test_backslash_path_refuses(self):
        self.assertRefusal("WAI-E-PATH.UNSAFE", AI.read_confined, self.root, "a\\b")

    def test_non_ascii_path_refuses(self):
        self.assertRefusal("WAI-E-PATH.ASCII", AI.read_confined, self.root, "猫")

    def test_symlink_input_refuses(self):
        (self.root / "target").write_bytes(b"data")
        (self.root / "link").symlink_to("target")
        self.assertRefusal("WAI-E-PATH.LEAF", AI.read_confined, self.root, "link")

    def test_symlink_parent_refuses(self):
        (self.root / "real").mkdir()
        (self.root / "parent").symlink_to("real", target_is_directory=True)
        self.assertRefusal("WAI-E-PATH.COMPONENT", AI.read_confined, self.root, "parent/input")

    def test_directory_input_refuses(self):
        (self.root / "directory").mkdir()
        self.assertRefusal("WAI-E-PATH.SPECIAL", AI.read_confined, self.root, "directory")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO creation is unavailable")
    def test_wai_path_001_fifo_input_refuses_without_blocking(self):
        os.mkfifo(self.root / "fifo")
        self.assertRefusal("WAI-E-PATH.SPECIAL", AI.read_confined, self.root, "fifo")

    def test_oversized_input_refuses(self):
        (self.root / "large").write_bytes(b"x" * (AI.MAX_FILE_BYTES + 1))
        self.assertRefusal("WAI-E-BOUNDS.FILE", AI.read_confined, self.root, "large")

    def test_input_and_output_file_cap_at_limit_is_valid(self):
        data = b"x" * AI.MAX_FILE_BYTES
        AI.write_confined_atomic(self.root, "large", data)
        self.assertEqual(AI.read_confined(self.root, "large"), data)

    def test_output_file_cap_limit_plus_one_refuses(self):
        self.assertRefusal(
            "WAI-E-BOUNDS.FILE",
            AI.write_confined_atomic,
            self.root,
            "large",
            b"x" * (AI.MAX_FILE_BYTES + 1),
        )

    def test_atomic_write_creates_regular_file(self):
        AI.write_confined_atomic(self.root, "output", b"new")
        self.assertEqual((self.root / "output").read_bytes(), b"new")
        self.assertTrue((self.root / "output").is_file())

    def test_atomic_write_replaces_regular_file(self):
        (self.root / "output").write_bytes(b"old")
        AI.write_confined_atomic(self.root, "output", b"new")
        self.assertEqual((self.root / "output").read_bytes(), b"new")

    @unittest.skipUnless(hasattr(os, "pathconf"), "filesystem name limits are unavailable")
    def test_atomic_write_replaces_maximum_component_length_file(self):
        name_max = os.pathconf(self.root, "PC_NAME_MAX")
        leaf = "a" * min(AI.MAX_PATH_BYTES, name_max)
        (self.root / leaf).write_bytes(b"old")
        try:
            AI.write_confined_atomic(self.root, leaf, b"new")
        except AI.CodecError as error:
            self.fail(f"valid maximum-length output raised {error.code}")
        self.assertEqual((self.root / leaf).read_bytes(), b"new")

    def test_atomic_replace_failure_preserves_old_file_and_cleans_temp(self):
        (self.root / "output").write_bytes(b"old")
        with mock.patch.object(AI.os, "replace", side_effect=OSError("injected")):
            self.assertRefusal("WAI-E-IO.WRITE", AI.write_confined_atomic, self.root, "output", b"new")
        self.assertEqual((self.root / "output").read_bytes(), b"old")
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["output"])

    def test_symlink_output_refuses_without_touching_target(self):
        (self.root / "target").write_bytes(b"safe")
        (self.root / "output").symlink_to("target")
        self.assertRefusal("WAI-E-PATH.SPECIAL", AI.write_confined_atomic, self.root, "output", b"unsafe")
        self.assertEqual((self.root / "target").read_bytes(), b"safe")

    def test_directory_output_refuses(self):
        (self.root / "output").mkdir()
        self.assertRefusal("WAI-E-PATH.SPECIAL", AI.write_confined_atomic, self.root, "output", b"data")

    def test_missing_parent_refuses(self):
        self.assertRefusal("WAI-E-PATH.COMPONENT", AI.write_confined_atomic, self.root, "missing/output", b"data")

    def test_atomic_write_leaves_no_temporary_file(self):
        AI.write_confined_atomic(self.root, "output", b"data")
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["output"])

    def test_cli_validate_emits_one_bounded_result(self):
        (self.root / "model.json").write_bytes(AI.canonical_json_bytes(minimal_model()))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "validate", "--root", str(self.root), "--input", "model.json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event["code"], "WAI-OK")
        self.assertEqual(event["event"], "validation")
        self.assertEqual(event["outcome"], "accepted")
        self.assertIn("input_sha256", event)

    def test_cli_refusal_emits_one_stable_result(self):
        (self.root / "bad.json").write_bytes(b"{}\n")
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "validate", "--root", str(self.root), "--input", "bad.json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertTrue(event["code"].startswith("WAI-E-"))
        self.assertLessEqual(len(event["node_path"]), 512)

    def test_cli_format_and_decode_use_confined_outputs(self):
        canonical = AI.canonical_json_bytes(minimal_model())
        (self.root / "model.json").write_bytes(canonical)
        formatted = subprocess.run(
            [sys.executable, str(SCRIPT), "format", "--root", str(self.root), "--input", "model.json", "--output", "model.wai"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(formatted.returncode, 0, formatted.stderr)
        decoded = subprocess.run(
            [sys.executable, str(SCRIPT), "decode", "--root", str(self.root), "--input", "model.wai", "--output", "decoded.json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(decoded.returncode, 0, decoded.stderr)
        self.assertEqual((self.root / "decoded.json").read_bytes(), canonical)


if __name__ == "__main__":
    unittest.main()
