"""Scaffold checks for wildcat-agent-instruction/v1."""

from __future__ import annotations

import hashlib
import importlib.util
import contextlib
import io
import json
import copy
import os
from pathlib import Path
import re
import shutil
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
MANIFEST = ROOT / "tests/fixtures/agent-instruction-v1/manifest.json"
MANIFEST_SCHEMA = ROOT / "tests/fixtures/agent-instruction-v1/manifest.schema.json"

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
        from tests.test_boundary_currency import REFRESH, drifted_paths

        self.assertEqual(drifted_paths(ROOT), [], REFRESH)

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


def manifest_record() -> dict:
    return AI.load_canonical_record(MANIFEST.read_bytes())


def fixture_record(fixture_id: str) -> dict:
    return next(item for item in manifest_record()["fixtures"] if item["id"] == fixture_id)


def artifact_record(fixture_id: str, name: str) -> dict:
    fixture = fixture_record(fixture_id)
    return AI.load_canonical_record((ROOT / fixture["artifacts"][name]["path"]).read_bytes())


def fixture_model(fixture_id: str) -> dict:
    fixture = fixture_record(fixture_id)
    return AI.load_canonical_json((ROOT / fixture["artifacts"]["model"]["path"]).read_bytes())


def mutation_by_id(mutation_id: str) -> tuple[str, dict]:
    for fixture in manifest_record()["fixtures"]:
        record = artifact_record(fixture["id"], "mutations")
        for mutation in record["mutations"]:
            if mutation["id"] == mutation_id:
                return fixture["id"], mutation
    raise AssertionError(f"unknown mutation: {mutation_id}")


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
    start_width = 32752
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
    evidence[12] = literal("text", " " * 16352 + "x")
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


def all_compact_literal_bytes_limit_plus_one_model() -> dict:
    """Build a valid model whose compact literal values total exactly cap + 1."""

    identifiers = [f"r{index:03d}" + "a" * 124 for index in range(78)]
    directives = [
        {
            "id": identifier,
            "kind": "require",
            "statement": literal("text", ""),
            "expressions": [],
            "promise": None,
        }
        for identifier in identifiers
    ]
    directives[0]["statement"] = literal("text", "x" * 237)
    relations = [
        {"kind": "before", "source": source, "target": target}
        for left_index, source in enumerate(identifiers)
        for target in identifiers[left_index + 1 :]
    ][:2990]
    bindings = [
        {"source": "src", "node": "doc", "start": "0", "end": "10000", "reviewer": literal("identifier", "r")},
        {"source": "src", "node": "section", "start": "0", "end": "10000", "reviewer": literal("identifier", "r")},
    ]
    bindings.extend(
        {
            "source": "src",
            "node": identifier,
            "start": str(index * 2 + 1),
            "end": str(index * 2 + 2),
            "reviewer": literal("identifier", "r"),
        }
        for index, identifier in enumerate(identifiers)
    )
    bindings.sort(
        key=lambda item: (
            item["source"],
            (len(item["start"]), item["start"]),
            (len(item["end"]), item["end"]),
            item["node"],
            item["reviewer"]["value"],
        )
    )
    return {
        "schema": SCHEMA_ID,
        "document": {"id": "doc", "title": literal("text", "")},
        "sources": [{"id": "src", "path": "source.md", "sha256": "0" * 64}],
        "sections": [{"id": "section", "title": literal("text", ""), "directives": directives}],
        "relations": relations,
        "bindings": bindings,
    }


def compact_literal_byte_total(compact: bytes) -> int:
    parser = AI.CompactParser(compact)
    total = 0
    for _, opcode, fields in parser.records:
        for field in fields:
            if len(field) >= 3 and field[0] in AI.TAG_KINDS and ":" in field[1:]:
                total += len(AI.decode_literal(field)["value"].encode("utf-8"))
        if opcode == "B":
            total += sum(len(fields[index].encode("utf-8")) for index in (2, 3))
    return total


def total_literal_limit_model(extra: int = 0) -> dict:
    model = minimal_model()
    model["document"]["title"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
    model["sections"][0]["title"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
    directive = model["sections"][0]["directives"][0]
    directive["statement"] = literal("text", "x" * AI.MAX_LITERAL_BYTES)
    directive["expressions"] = [
        {"kind": "when", "predicate": literal("text", "x" * AI.MAX_LITERAL_BYTES), "expressions": []}
        for _ in range(9)
    ]
    directive["expressions"].append(
        {"kind": "when", "predicate": literal("text", ""), "expressions": []}
    )
    with mock.patch.object(AI, "validate_model", return_value=model):
        base = compact_literal_byte_total(AI.format_compact(model))
    remainder = AI.MAX_TOTAL_LITERAL_BYTES - base + extra
    if not 0 <= remainder <= AI.MAX_LITERAL_BYTES:
        raise AssertionError(f"invalid total-literal remainder: {remainder}")
    directive["expressions"][-1]["predicate"] = literal("text", "x" * remainder)
    return model


def decimal_span_literal_limit_model(extra: int = 0) -> dict:
    model = minimal_model()
    outer_end = "2" + "0" * (AI.MAX_LITERAL_BYTES - 1 + extra)
    model["bindings"][0]["end"] = outer_end
    model["bindings"][1]["end"] = outer_end
    return model


class RefusalAssertions:
    def assertRefusal(self, code: str, function, *arguments, **keywords):
        with self.assertRaises(AI.CodecError) as raised:
            function(*arguments, **keywords)
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

    def test_duplicate_source_path_alias_refuses(self):
        model = minimal_model()
        model["sources"] = [
            {"id": "src-a", "path": "source.md", "sha256": "0" * 64},
            {"id": "src-b", "path": "source.md", "sha256": "0" * 64},
        ]
        for binding in model["bindings"]:
            binding["source"] = "src-a"
        second = copy.deepcopy(model["sections"][0]["directives"][0])
        second["id"] = "rule-b"
        model["sections"][0]["directives"].append(second)
        model["bindings"].append(
            {
                "source": "src-b",
                "node": "rule-b",
                "start": "20",
                "end": "50",
                "reviewer": reviewer(),
            }
        )
        model["bindings"].sort(
            key=lambda item: (
                item["source"],
                int(item["start"]),
                int(item["end"]),
                item["node"],
                item["reviewer"]["value"],
            )
        )
        self.assertRefusal("WAI-E-REFERENCE.DUPLICATE_SOURCE_PATH", AI.validate_model, model)
        with mock.patch.object(AI, "validate_model", return_value=model):
            compact = AI.format_compact(model)
        self.assertRefusal("WAI-E-REFERENCE.DUPLICATE_SOURCE_PATH", AI.decode_compact, compact)

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

    def test_decimal_span_at_literal_limit_round_trips(self):
        model = decimal_span_literal_limit_model()
        compact = AI.format_compact(model)
        self.assertEqual(AI.decode_compact(compact)[0], model)

    def test_decimal_span_literal_limit_plus_one_refuses(self):
        model = decimal_span_literal_limit_model(extra=1)
        self.assertRefusal("WAI-E-BOUNDS.LITERAL", AI.validate_model, model)

    def test_decimal_schema_cap_matches_runtime(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["$defs"]["decimal"].get("maxLength"), AI.MAX_LITERAL_BYTES)

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
        model = total_literal_limit_model()
        with mock.patch.object(AI, "validate_model", return_value=model):
            compact = AI.format_compact(model)
        self.assertEqual(compact_literal_byte_total(compact), AI.MAX_TOTAL_LITERAL_BYTES)
        AI.validate_model(model)
        self.assertEqual(AI.decode_compact(compact)[0], model)

    def test_total_literal_cap_limit_plus_one_refuses(self):
        model = total_literal_limit_model(extra=1)
        self.assertRefusal("WAI-E-BOUNDS.LITERALS", AI.validate_model, model)

    def test_all_compact_literal_bytes_limit_plus_one_refuses(self):
        model = all_compact_literal_bytes_limit_plus_one_model()
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

    def test_binding_offsets_use_bare_canonical_decimals(self):
        binding_lines = [
            line.split()
            for line in AI.format_compact(complete_model()).decode().splitlines()
            if line.lstrip().startswith("B ")
        ]
        self.assertTrue(binding_lines)
        for fields in binding_lines:
            with self.subTest(fields=fields):
                self.assertRegex(fields[3], r"\A(?:0|[1-9][0-9]*)\Z")
                self.assertRegex(fields[4], r"\A(?:0|[1-9][0-9]*)\Z")

    def test_length_prefixed_binding_offsets_refuse(self):
        model = minimal_model()
        lines = AI.format_compact(model).decode().splitlines()
        binding_index = next(index for index, line in enumerate(lines) if line.lstrip().startswith("B "))
        fields = lines[binding_index].split()
        start = model["bindings"][0]["start"]
        fields[3] = f"n{len(start.encode('utf-8'))}:{start}"
        lines[binding_index] = "  " + " ".join(fields)
        self.assertRefusal(
            "WAI-E-SHAPE.DECIMAL",
            AI.decode_compact,
            ("\n".join(lines) + "\n").encode(),
        )

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

    def test_decoder_counts_reference_fields_in_total_literal_cap(self):
        model = all_compact_literal_bytes_limit_plus_one_model()
        with mock.patch.object(AI, "validate_model", return_value=model):
            compact = AI.format_compact(model)
        self.assertEqual(compact_literal_byte_total(compact), AI.MAX_TOTAL_LITERAL_BYTES + 1)
        with mock.patch.object(AI, "validate_model", return_value=model) as validate:
            self.assertRefusal("WAI-E-BOUNDS.LITERALS", AI.decode_compact, compact)
        validate.assert_not_called()

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


class FixtureBindingTests(RefusalAssertions, unittest.TestCase):
    def copied_root(self, destination: Path) -> Path:
        fixture_destination = destination / "tests/fixtures/agent-instruction-v1"
        fixture_destination.parent.mkdir(parents=True)
        shutil.copytree(ROOT / "tests/fixtures/agent-instruction-v1", fixture_destination)
        for source in {item["source"]["path"] for item in manifest_record()["fixtures"]}:
            target = destination / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / source, target)
        return destination

    def assertCheckRefusal(self, code: str, root: Path) -> None:
        records = AI.check_manifest(root, str(MANIFEST.relative_to(ROOT)))
        refusals = [item for item in records if item["outcome"] == "refused"]
        self.assertTrue(any(item["code"].startswith(code) for item in refusals), refusals)
        self.assertEqual(records[-1]["event"], "run.summary")
        self.assertEqual(records[-1]["outcome"], "refused")

    def test_manifest_schema_loads_as_closed_object(self):
        schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(schema["type"], "object")
        self.assertFalse(schema["additionalProperties"])
        self.assertEqual(schema["properties"]["schema"]["const"], AI.MANIFEST_ID)

    def test_manifest_schema_freezes_ordered_fixture_contracts(self):
        schema = json.loads(MANIFEST_SCHEMA.read_text(encoding="utf-8"))
        rows = schema["properties"]["fixtures"].get("prefixItems", [])
        observed = []
        for row in rows:
            properties = row["properties"]
            source = properties["source"]["properties"]
            observed.append(
                (
                    properties["id"]["const"],
                    source["id"]["const"],
                    source["path"]["const"],
                    properties["binding_count"]["const"],
                    properties["question_count"]["const"],
                    properties["mutation_count"]["const"],
                )
            )
        expected = [
            (fixture_id, item["source_id"], item["source_path"], str(item["binding_count"]), str(item["question_count"]), str(item["mutation_count"]))
            for fixture_id, item in AI.FIXTURE_CONTRACT.items()
        ]
        self.assertEqual(observed, expected)
        self.assertFalse(schema["properties"]["fixtures"]["items"])

    def test_manifest_schema_huge_integer_refuses_stably(self):
        payload = b'{"maximum":' + b"1" * 4301 + b"}\n"
        try:
            AI.load_canonical_record(payload, allow_integers=True)
        except AI.CodecError as error:
            self.assertEqual(error.code, "WAI-E-BOUNDS.NUMBER")
        except Exception as error:
            self.fail(f"manifest schema integer escaped as {type(error).__name__}")
        else:
            self.fail("manifest schema integer was accepted")

    def test_manifest_is_canonical_json(self):
        self.assertEqual(AI.canonical_record_bytes(manifest_record()), MANIFEST.read_bytes())

    def test_manifest_names_exact_three_fixtures(self):
        self.assertEqual(tuple(item["id"] for item in manifest_record()["fixtures"]), AI.FIXTURE_IDS)

    def test_fixture_roots_are_id_derived(self):
        for fixture in manifest_record()["fixtures"]:
            self.assertEqual(fixture["root"], f"{AI.FIXTURE_ROOT}/{fixture['id']}")

    def test_fixture_artifact_names_are_closed(self):
        for fixture in manifest_record()["fixtures"]:
            self.assertEqual(set(fixture["artifacts"]), set(AI.FIXTURE_ARTIFACTS))
            self.assertEqual(
                {Path(item["path"]).name for item in fixture["artifacts"].values()},
                set(AI.FIXTURE_ARTIFACTS.values()),
            )

    def test_manifest_mutation_count_equals_fixture_sum(self):
        manifest = manifest_record()
        self.assertEqual(int(manifest["mutation_count"]), sum(int(item["mutation_count"]) for item in manifest["fixtures"]))

    def test_manifest_freezes_exact_source_and_corpus_counts(self):
        manifest = manifest_record()
        expected = {
            "fiat-study-runbook-phase": ("fiat", "plugins/hexaemeron/skills/fiat/SKILL.md", "7", "3"),
            "horos-boundary-check": ("horos", "plugins/horos/skills/horos/SKILL.md", "4", "3"),
            "promise-machine-router-selection": ("promise-machine", "PROMISE_MACHINE.md", "4", "3"),
        }
        self.assertEqual(manifest.get("binding_count"), "15")
        self.assertEqual(manifest.get("question_count"), "9")
        for fixture in manifest["fixtures"]:
            observed = (
                fixture["source"]["id"],
                fixture["source"]["path"],
                fixture.get("binding_count"),
                fixture.get("question_count"),
            )
            self.assertEqual(observed, expected[fixture["id"]])

    def test_manifest_refuses_a_swapped_source_identity(self):
        manifest = manifest_record()
        manifest["fixtures"][0]["source"] = copy.deepcopy(manifest["fixtures"][1]["source"])
        self.assertRefusal("WAI-E-MANIFEST.SOURCE", AI.validate_manifest, manifest)

    def test_source_blob_digests_match(self):
        for fixture in manifest_record()["fixtures"]:
            self.assertEqual(sha256(ROOT / fixture["source"]["path"]), fixture["source"]["sha256"])

    def test_manifest_source_span_digests_match(self):
        for fixture in manifest_record()["fixtures"]:
            source = (ROOT / fixture["source"]["path"]).read_bytes()
            start, end = int(fixture["source"]["start"]), int(fixture["source"]["end"])
            self.assertEqual(hashlib.sha256(source[start:end]).hexdigest(), fixture["source"]["span_sha256"])

    def test_fixture_models_validate(self):
        for fixture_id in AI.FIXTURE_IDS:
            model = fixture_model(fixture_id)
            self.assertIs(AI.validate_model(model), model)

    def test_model_source_metadata_matches_manifest(self):
        for fixture in manifest_record()["fixtures"]:
            model_source = fixture_model(fixture["id"])["sources"]
            self.assertEqual(len(model_source), 1)
            self.assertEqual(
                model_source[0],
                {field: fixture["source"][field] for field in ("id", "path", "sha256")},
            )

    def test_fiat_model_carries_the_conditional_marketplace_reassessment(self):
        model = fixture_model("fiat-study-runbook-phase")
        directives = {item["id"]: item for item in model["sections"][0]["directives"]}
        self.assertIn("marketplace-reassessment", directives)
        reassessment = directives["marketplace-reassessment"]
        self.assertEqual(reassessment["kind"], "require")
        self.assertEqual(reassessment["expressions"][0]["kind"], "when")
        self.assertEqual(
            reassessment["expressions"][0]["predicate"]["value"],
            "the labs_marketplace receipt exists",
        )
        spans = artifact_record("fiat-study-runbook-phase", "source_spans")["spans"]
        self.assertIn("marketplace-reassessment", {item["node"] for item in spans})
        questions = {
            item["id"]: item["required_answer"]
            for item in artifact_record("fiat-study-runbook-phase", "questions")["questions"]
        }
        self.assertEqual(questions.get("fiat-marketplace-reassessment"), "post-spec-reassessment")

    def test_checked_compact_decodes_to_model(self):
        for fixture in manifest_record()["fixtures"]:
            model_bytes = (ROOT / fixture["artifacts"]["model"]["path"]).read_bytes()
            compact_bytes = (ROOT / fixture["artifacts"]["compact"]["path"]).read_bytes()
            _, decoded = AI.decode_compact(compact_bytes)
            self.assertEqual(decoded, model_bytes)

    def test_formatter_regenerates_checked_compact(self):
        for fixture in manifest_record()["fixtures"]:
            compact = (ROOT / fixture["artifacts"]["compact"]["path"]).read_bytes()
            self.assertEqual(AI.format_compact(fixture_model(fixture["id"])), compact)

    def test_source_span_records_mirror_model_bindings(self):
        for fixture_id in AI.FIXTURE_IDS:
            model = fixture_model(fixture_id)
            record = artifact_record(fixture_id, "source_spans")
            observed = [(item["node"], item["start"], item["end"], item["reviewer"]) for item in record["spans"]]
            expected = [(item["node"], item["start"], item["end"], item["reviewer"]["value"]) for item in model["bindings"]]
            self.assertEqual(observed, expected)

    def test_each_reviewed_span_digest_matches_source_bytes(self):
        for fixture in manifest_record()["fixtures"]:
            source = (ROOT / fixture["source"]["path"]).read_bytes()
            record = artifact_record(fixture["id"], "source_spans")
            for span in record["spans"]:
                data = source[int(span["start"]):int(span["end"])]
                self.assertEqual(hashlib.sha256(data).hexdigest(), span["sha256"])

    def test_reviewed_binding_outside_manifest_source_span_refuses(self):
        fixture = next(item for item in manifest_record()["fixtures"] if item["id"] == "horos-boundary-check")
        source = (ROOT / fixture["source"]["path"]).read_bytes()
        model = fixture_model(fixture["id"])
        record = artifact_record(fixture["id"], "source_spans")
        binding = next(item for item in model["bindings"] if item["node"] == "boundary-check")
        binding["start"], binding["end"] = "0", "10"
        model["bindings"].sort(
            key=lambda item: (
                item["source"],
                AI._decimal_key(item["start"]),
                AI._decimal_key(item["end"]),
                item["node"],
                item["reviewer"]["value"],
            )
        )
        span = next(item for item in record["spans"] if item["node"] == "boundary-check")
        span["start"], span["end"] = "0", "10"
        span["sha256"] = hashlib.sha256(source[:10]).hexdigest()
        spans_by_node = {item["node"]: item for item in record["spans"]}
        record["spans"] = [spans_by_node[item["node"]] for item in model["bindings"]]
        AI.validate_model(model)
        self.assertRefusal(
            "WAI-E-REFERENCE.SPAN",
            AI._validate_source_spans,
            record,
            fixture["id"],
            fixture["source"],
            source,
            model,
        )

    def test_span_reviewer_matches_manifest_review(self):
        fixture = next(item for item in manifest_record()["fixtures"] if item["id"] == "horos-boundary-check")
        source = (ROOT / fixture["source"]["path"]).read_bytes()
        model = fixture_model(fixture["id"])
        record = artifact_record(fixture["id"], "source_spans")
        for binding in model["bindings"]:
            binding["reviewer"]["value"] = "other"
        for span in record["spans"]:
            span["reviewer"] = "other"
        AI.validate_model(model)
        self.assertRefusal(
            "WAI-E-MANIFEST.REVIEW",
            AI._validate_source_spans,
            record,
            fixture["id"],
            fixture["source"],
            source,
            model,
        )

    def test_question_accepted_answers_are_closed_and_nonempty(self):
        for fixture_id in AI.FIXTURE_IDS:
            for question in artifact_record(fixture_id, "questions")["questions"]:
                self.assertTrue(question["accepted_answers"])
                self.assertEqual(len(question["accepted_answers"]), len(set(question["accepted_answers"])))

    def test_question_refusal_answers_are_closed_and_nonempty(self):
        for fixture_id in AI.FIXTURE_IDS:
            for question in artifact_record(fixture_id, "questions")["questions"]:
                self.assertTrue(question["refusal_answers"])
                self.assertFalse(set(question["accepted_answers"]) & set(question["refusal_answers"]))

    def test_required_answer_is_predeclared_as_accepted(self):
        for fixture_id in AI.FIXTURE_IDS:
            for question in artifact_record(fixture_id, "questions")["questions"]:
                self.assertIn(question["required_answer"], question["accepted_answers"])

    def test_question_context_inventory_is_fresh_and_complete(self):
        expected = {"mode", "prior_messages", "examples", "repository_instruction_paths", "tool_definition_ids"}
        for fixture_id in AI.FIXTURE_IDS:
            for question in artifact_record(fixture_id, "questions")["questions"]:
                self.assertEqual(set(question["context"]), expected)
                self.assertEqual(question["context"]["mode"], "fresh")
                self.assertEqual(question["context"]["prior_messages"], [])
                self.assertEqual(question["context"]["examples"], [])

    def test_check_emits_bounded_binding_roundtrip_mutation_and_summary_records(self):
        records = AI.check_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        self.assertEqual(sum(item["event"] == "binding.result" for item in records), 3)
        self.assertEqual(sum(item["event"] == "roundtrip.result" for item in records), 3)
        self.assertEqual(sum(item["event"] == "mutation.result" for item in records), 14)
        self.assertEqual(sum(item["event"] == "run.summary" for item in records), 1)
        self.assertTrue(all("manifest_sha256" in item for item in records))

    def test_cli_check_accepts_exact_manifest(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "check", "--manifest", str(MANIFEST.relative_to(ROOT))],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        records = [json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(len(records), 21)
        self.assertEqual(records[-1]["event"], "run.summary")
        self.assertEqual(records[-1]["mutation_count"], 14)

    def test_stale_source_blob_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            source = copied / "plugins/hexaemeron/skills/fiat/SKILL.md"
            source.write_bytes(source.read_bytes() + b"\n")
            self.assertCheckRefusal("WAI-E-DIGEST.SOURCE", copied)

    def test_stale_model_artifact_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            model = copied / "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/model.json"
            model.write_bytes(model.read_bytes() + b"\n")
            self.assertCheckRefusal("WAI-E-DIGEST.ARTIFACT", copied)

    def test_stale_compact_artifact_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            compact = copied / "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/compact.wai"
            compact.write_bytes(compact.read_bytes() + b"\n")
            self.assertCheckRefusal("WAI-E-DIGEST.ARTIFACT", copied)

    def test_stale_question_artifact_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            questions = copied / "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json"
            questions.write_bytes(questions.read_bytes() + b"\n")
            self.assertCheckRefusal("WAI-E-DIGEST.ARTIFACT", copied)

    def test_stale_source_span_artifact_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            spans = copied / "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json"
            spans.write_bytes(spans.read_bytes() + b"\n")
            self.assertCheckRefusal("WAI-E-DIGEST.ARTIFACT", copied)

    def test_stale_manifest_schema_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            schema = copied / AI.MANIFEST_SCHEMA_PATH
            schema.write_bytes(schema.read_bytes() + b"\n")
            self.assertRefusal("WAI-E-DIGEST.SCHEMA", AI.check_manifest, copied, str(MANIFEST.relative_to(ROOT)))

    def test_rebound_replacement_manifest_schema_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            schema = copied / AI.MANIFEST_SCHEMA_PATH
            replacement = AI.canonical_record_bytes(
                {"$id": AI.MANIFEST_SCHEMA_ID, "additionalProperties": False}
            )
            schema.write_bytes(replacement)
            manifest_path = copied / MANIFEST.relative_to(ROOT)
            manifest = AI.load_canonical_record(manifest_path.read_bytes())
            manifest["schema_sha256"] = hashlib.sha256(replacement).hexdigest()
            manifest_path.write_bytes(AI.canonical_record_bytes(manifest))
            self.assertRefusal("WAI-E-DIGEST.SCHEMA", AI.check_manifest, copied, str(MANIFEST.relative_to(ROOT)))

    def test_cli_manifest_refusal_keeps_the_readable_manifest_digest(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            manifest_path = copied / MANIFEST.relative_to(ROOT)
            manifest = AI.load_canonical_record(manifest_path.read_bytes())
            manifest["binding_count"] = "14"
            manifest_bytes = AI.canonical_record_bytes(manifest)
            manifest_path.write_bytes(manifest_bytes)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "check",
                    "--root",
                    str(copied),
                    "--manifest",
                    str(MANIFEST.relative_to(ROOT)),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 2, result.stderr)
            records = [json.loads(line) for line in result.stdout.splitlines()]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].get("manifest_sha256"), hashlib.sha256(manifest_bytes).hexdigest())

    def test_missing_fixture_artifact_refuses_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            (copied / "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/questions.json").unlink()
            self.assertCheckRefusal("WAI-E-MANIFEST.CLOSURE", copied)

    def test_extra_fixture_artifact_refuses_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            (copied / "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/extra.json").write_bytes(b"{}\n")
            self.assertCheckRefusal("WAI-E-MANIFEST.CLOSURE", copied)

    def test_fixture_closure_refuses_before_materialising_unbounded_entries(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            fixture_root = copied / "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase"
            (fixture_root / "extra.json").write_bytes(b"{}\n")
            with mock.patch.object(AI.os, "listdir", side_effect=RuntimeError("unbounded listdir")):
                try:
                    AI._confined_directory_entries(
                        copied,
                        "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase",
                    )
                except AI.CodecError as error:
                    self.assertEqual(error.code, "WAI-E-MANIFEST.CLOSURE")
                except Exception as error:
                    self.fail(f"fixture closure materialised the directory as {type(error).__name__}")
                else:
                    self.fail("fixture closure accepted a sixth entry")

    def test_question_shrink_with_rebound_digest_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            manifest_path = copied / MANIFEST.relative_to(ROOT)
            manifest = AI.load_canonical_record(manifest_path.read_bytes())
            fixture = next(item for item in manifest["fixtures"] if item["id"] == "fiat-study-runbook-phase")
            questions_path = copied / fixture["artifacts"]["questions"]["path"]
            questions = AI.load_canonical_record(questions_path.read_bytes())
            questions["questions"].pop()
            questions_bytes = AI.canonical_record_bytes(questions)
            questions_path.write_bytes(questions_bytes)
            fixture["artifacts"]["questions"]["sha256"] = hashlib.sha256(questions_bytes).hexdigest()
            manifest_path.write_bytes(AI.canonical_record_bytes(manifest))
            self.assertCheckRefusal("WAI-E-MANIFEST.QUESTION_COUNT", copied)

    def test_governed_node_shrink_with_rebound_derivatives_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            manifest_path = copied / MANIFEST.relative_to(ROOT)
            manifest = AI.load_canonical_record(manifest_path.read_bytes())
            fixture = next(item for item in manifest["fixtures"] if item["id"] == "fiat-study-runbook-phase")
            model_path = copied / fixture["artifacts"]["model"]["path"]
            compact_path = copied / fixture["artifacts"]["compact"]["path"]
            spans_path = copied / fixture["artifacts"]["source_spans"]["path"]
            model = AI.load_canonical_json(model_path.read_bytes())
            model["sections"][0]["directives"] = [
                item for item in model["sections"][0]["directives"] if item["id"] != "receipt-boundary"
            ]
            model["bindings"] = [item for item in model["bindings"] if item["node"] != "receipt-boundary"]
            spans = AI.load_canonical_record(spans_path.read_bytes())
            spans["spans"] = [item for item in spans["spans"] if item["node"] != "receipt-boundary"]
            artifacts = {
                "model": AI.canonical_json_bytes(model),
                "compact": AI.format_compact(model),
                "source_spans": AI.canonical_record_bytes(spans),
            }
            for name, data in artifacts.items():
                path = copied / fixture["artifacts"][name]["path"]
                path.write_bytes(data)
                fixture["artifacts"][name]["sha256"] = hashlib.sha256(data).hexdigest()
            manifest_path.write_bytes(AI.canonical_record_bytes(manifest))
            self.assertCheckRefusal("WAI-E-MANIFEST.BINDING_COUNT", copied)

    def test_missing_governed_binding_refuses(self):
        model = fixture_model("promise-machine-router-selection")
        model["bindings"] = [item for item in model["bindings"] if item["node"] != "router-selection-check"]
        self.assertRefusal("WAI-E-REFERENCE.UNCOVERED", AI.validate_model, model)

    def test_overlapping_sibling_bindings_refuse(self):
        model = fixture_model("fiat-study-runbook-phase")
        sibling = next(item for item in model["bindings"] if item["node"] == "study-phase")
        binding = next(item for item in model["bindings"] if item["node"] == "runbook-phase")
        binding["start"] = str(int(sibling["end"]) - 1)
        self.assertRefusal("WAI-E-REFERENCE.OVERLAP", AI.validate_model, model)

    def test_unsafe_source_path_in_manifest_refuses(self):
        manifest = manifest_record()
        manifest["fixtures"][0]["source"]["path"] = "../outside.md"
        self.assertRefusal("WAI-E-PATH.UNSAFE", AI.validate_manifest, manifest)


class MutationTests(RefusalAssertions, unittest.TestCase):
    def mutation_records(self) -> list[tuple[str, dict]]:
        records = []
        for fixture in manifest_record()["fixtures"]:
            records.extend((fixture["id"], item) for item in artifact_record(fixture["id"], "mutations")["mutations"])
        return records

    def assertDigestMutation(self, mutation_id: str) -> None:
        fixture_id, mutation = mutation_by_id(mutation_id)
        model = fixture_model(fixture_id)
        original = AI.canonical_json_bytes(model)
        changed = AI.canonical_json_bytes(AI.apply_mutation(model, mutation["operation"]))
        self.assertNotEqual(hashlib.sha256(changed).digest(), hashlib.sha256(original).digest())

    def test_manifest_declares_exact_mutation_count(self):
        self.assertEqual(manifest_record()["mutation_count"], "14")
        self.assertEqual(len(self.mutation_records()), 14)

    def test_manifest_declares_exact_risk_inventory(self):
        self.assertEqual(tuple(manifest_record()["risk_classes"]), AI.RISK_CLASSES)

    def test_mutations_cover_every_required_risk_class(self):
        self.assertEqual({item["risk"] for _, item in self.mutation_records()}, set(AI.RISK_CLASSES))

    def test_risk_class_must_match_the_mutated_target(self):
        fixture_id = "promise-machine-router-selection"
        model = fixture_model(fixture_id)
        record = artifact_record(fixture_id, "mutations")
        mutation = next(item for item in record["mutations"] if item["risk"] == "evidence-class")
        mutation["operation"] = {
            "kind": "replace",
            "path": "/document/title/value",
            "value": "unrelated title change",
        }
        questions = AI._validate_questions(artifact_record(fixture_id, "questions"), fixture_id)
        self.assertRefusal(
            "WAI-E-MUTATION.RISK_TARGET",
            AI._validate_mutations,
            record,
            fixture_id,
            model,
            AI.canonical_json_bytes(model),
            6,
            questions,
        )

    def test_mutation_ids_are_unique(self):
        ids = [item["id"] for _, item in self.mutation_records()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_mutation_operations_use_closed_vocabulary(self):
        self.assertEqual({item["operation"]["kind"] for _, item in self.mutation_records()}, {"remove", "replace"})

    def test_mutation_expectations_use_closed_vocabulary(self):
        self.assertEqual(
            {item["expected"]["kind"] for _, item in self.mutation_records()},
            {"answer-change", "model-digest", "structural-refusal"},
        )

    def test_each_fixture_declares_an_answer_change_for_negation(self):
        mutations = [
            (fixture_id, item)
            for fixture_id, item in self.mutation_records()
            if item["risk"] == "negation" and item["expected"].get("kind") == "answer-change"
        ]
        self.assertEqual({fixture_id for fixture_id, _ in mutations}, set(AI.FIXTURE_IDS))
        for fixture_id, mutation in mutations:
            questions = {
                item["id"]: item["required_answer"]
                for item in artifact_record(fixture_id, "questions")["questions"]
            }
            self.assertIn(mutation["expected"].get("question"), questions)
            self.assertNotEqual(
                mutation["expected"].get("value"),
                questions[mutation["expected"]["question"]],
            )

    def test_answer_change_must_name_a_declared_answer(self):
        fixture_id, mutation = mutation_by_id("fiat-negation-001")
        model = fixture_model(fixture_id)
        record = {
            "schema": "wildcat-agent-instruction-mutations/v1",
            "fixture": fixture_id,
            "mutations": [copy.deepcopy(mutation)],
        }
        record["mutations"][0]["expected"]["value"] = "never-declared-answer"
        questions = AI._validate_questions(artifact_record(fixture_id, "questions"), fixture_id)
        self.assertRefusal(
            "WAI-E-MUTATION.EXPECTED",
            AI._validate_mutations,
            record,
            fixture_id,
            model,
            AI.canonical_json_bytes(model),
            1,
            questions,
        )

    def test_exact_literal_mutations_cover_each_used_class(self):
        expected = {"identifier", "path", "sha256", "command", "number", "text"}
        observed = {
            item.get("literal_class")
            for _, item in self.mutation_records()
            if item["risk"] == "exact-literal"
        }
        self.assertEqual(observed, expected)

    def test_checker_emits_one_record_per_mutation(self):
        records = AI.check_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        observed = {item["mutation_id"] for item in records if item["event"] == "mutation.result"}
        self.assertEqual(observed, {item["id"] for _, item in self.mutation_records()})

    def test_precedence_mutation_changes_model_digest(self):
        self.assertDigestMutation("fiat-precedence-001")

    def test_scope_mutation_refuses_structurally(self):
        fixture_id, mutation = mutation_by_id("horos-scope-001")
        changed = AI.apply_mutation(fixture_model(fixture_id), mutation["operation"])
        self.assertRefusal("WAI-E-REFERENCE.EXCEPTION_TARGET", AI.canonical_json_bytes, changed)

    def test_negation_mutation_changes_model_digest(self):
        self.assertDigestMutation("pm-negation-001")

    def test_evidence_class_mutation_changes_model_digest(self):
        self.assertDigestMutation("pm-evidence-class-001")

    def test_authorisation_mutation_changes_model_digest(self):
        self.assertDigestMutation("pm-authorisation-001")

    def test_recovery_mutation_changes_model_digest(self):
        self.assertDigestMutation("pm-recovery-001")

    def test_exact_literal_mutation_changes_model_digest(self):
        self.assertDigestMutation("horos-exact-literal-001")

    def test_noop_digest_mutation_refuses_silent_acceptance(self):
        fixture_id = "promise-machine-router-selection"
        model = fixture_model(fixture_id)
        record = {
            "schema": "wildcat-agent-instruction-mutations/v1",
            "fixture": fixture_id,
            "mutations": [{
                "id": "noop-001",
                "risk": "evidence-class",
                "operation": {
                    "kind": "replace",
                    "path": "/sections/0/directives/0/promise/evidence_classes",
                    "value": model["sections"][0]["directives"][0]["promise"]["evidence_classes"],
                },
                "expected": {"kind": "model-digest", "value": "different"},
            }],
        }
        self.assertRefusal("WAI-E-MUTATION.SILENT", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 1)

    def test_unknown_risk_class_refuses(self):
        fixture_id = "promise-machine-router-selection"
        model = fixture_model(fixture_id)
        record = artifact_record(fixture_id, "mutations")
        record["mutations"][0]["risk"] = "summary-loss"
        self.assertRefusal("WAI-E-MUTATION.RISK", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 6)

    def test_duplicate_mutation_id_refuses(self):
        fixture_id = "promise-machine-router-selection"
        model = fixture_model(fixture_id)
        record = artifact_record(fixture_id, "mutations")
        record["mutations"][1]["id"] = record["mutations"][0]["id"]
        questions = AI._validate_questions(artifact_record(fixture_id, "questions"), fixture_id)
        self.assertRefusal("WAI-E-REFERENCE.DUPLICATE_ID", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 6, questions)

    def test_mutation_count_mismatch_refuses(self):
        fixture_id = "promise-machine-router-selection"
        model = fixture_model(fixture_id)
        record = artifact_record(fixture_id, "mutations")
        self.assertRefusal("WAI-E-MANIFEST.MUTATION_COUNT", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 5)

    def test_wrong_structural_refusal_code_refuses(self):
        fixture_id, mutation = mutation_by_id("horos-scope-001")
        model = fixture_model(fixture_id)
        record = {"schema": "wildcat-agent-instruction-mutations/v1", "fixture": fixture_id, "mutations": [copy.deepcopy(mutation)]}
        record["mutations"][0]["expected"]["value"] = "WAI-E-CYCLE"
        self.assertRefusal("WAI-E-MUTATION.WRONG_REFUSAL", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 1)

    def test_structural_refusal_requires_the_exact_code(self):
        fixture_id, mutation = mutation_by_id("horos-scope-001")
        model = fixture_model(fixture_id)
        record = {"schema": "wildcat-agent-instruction-mutations/v1", "fixture": fixture_id, "mutations": [copy.deepcopy(mutation)]}
        record["mutations"][0]["expected"]["value"] = "WAI-E-"
        self.assertRefusal("WAI-E-MUTATION.WRONG_REFUSAL", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 1)

    def test_exact_literal_class_must_match_the_mutated_field(self):
        fixture_id, mutation = mutation_by_id("horos-exact-literal-001")
        model = fixture_model(fixture_id)
        record = {"schema": "wildcat-agent-instruction-mutations/v1", "fixture": fixture_id, "mutations": [copy.deepcopy(mutation)]}
        record["mutations"][0]["literal_class"] = "text"
        self.assertRefusal("WAI-E-MUTATION.LITERAL_CLASS", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 1)

    def test_exact_literal_non_object_operation_refuses_stably(self):
        fixture_id, mutation = mutation_by_id("horos-exact-literal-001")
        model = fixture_model(fixture_id)
        record = {"schema": "wildcat-agent-instruction-mutations/v1", "fixture": fixture_id, "mutations": [copy.deepcopy(mutation)]}
        record["mutations"][0]["operation"] = []
        try:
            AI._validate_mutations(record, fixture_id, model, AI.canonical_json_bytes(model), 1)
        except AI.CodecError as error:
            self.assertEqual(error.code, "WAI-E-SHAPE.OBJECT")
        except Exception as error:
            self.fail(f"literal mutation operation escaped as {type(error).__name__}")
        else:
            self.fail("literal mutation accepted a non-object operation")

    def test_missing_json_pointer_refuses(self):
        model = fixture_model("horos-boundary-check")
        operation = {"kind": "remove", "path": "/sections/0/absent"}
        self.assertRefusal("WAI-E-MUTATION.POINTER", AI.apply_mutation, model, operation)

    def test_noncanonical_json_pointer_refuses(self):
        model = fixture_model("horos-boundary-check")
        operation = {"kind": "remove", "path": "/sections/~2bad"}
        self.assertRefusal("WAI-E-MUTATION.POINTER", AI.apply_mutation, model, operation)

    def test_unsupported_expectation_kind_refuses(self):
        fixture_id = "horos-boundary-check"
        model = fixture_model(fixture_id)
        record = artifact_record(fixture_id, "mutations")
        record["mutations"] = [record["mutations"][0]]
        record["mutations"][0]["expected"]["kind"] = "silent"
        self.assertRefusal("WAI-E-MUTATION.EXPECTED", AI._validate_mutations, record, fixture_id, model, AI.canonical_json_bytes(model), 1)


FAKE_ADAPTER_SOURCE = r'''import json
import os
import sys
import time

command = sys.argv[1]
if command == "version":
    sys.stdout.write("fake-runtime 1\n")
    raise SystemExit(0)
if command == "identity":
    sys.stdout.write("FROM @sha256-" + sys.argv[2] + "\n")
    raise SystemExit(0)
if command == "environment":
    sys.stdout.write(json.dumps(sorted(os.environ)))
    raise SystemExit(0)

mode = sys.argv[2]
if mode == "sleep":
    time.sleep(2)
if mode == "stdout-cap":
    sys.stdout.write("x" * 128)
    raise SystemExit(0)
if mode == "stderr-cap":
    sys.stderr.write("x" * 128)
    raise SystemExit(0)
if mode == "exit":
    raise SystemExit(7)

request = json.load(sys.stdin)
capture = os.environ.get("FAKE_CAPTURE")
if capture:
    with open(capture, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(request, sort_keys=True, separators=(",", ":")) + "\n")

count = 7
if mode == "negative-count":
    count = -1
elif mode == "non-integer-count":
    count = 1.5
model = request["model"]
if mode == "model-mismatch":
    model = "different:model"

if "messages" in request:
    answer_id = "result-enabled"
    if mode == "unknown-answer":
        answer_id = "unlisted-answer"
    elif mode == "model-refusal":
        answer_id = "refuse-unknown"
    elif mode == "second-answer":
        answer_id = "result-disabled"
    content = json.dumps({"answer_id": answer_id}, sort_keys=True)
    if mode == "malformed-answer":
        content = "{"
    elif mode == "secret-answer":
        content = "token=visible-secret"
    elif mode == "large-answer":
        content = "x" * 513
    payload = {
        "model": model,
        "message": {"role": "assistant", "content": content},
        "done": True,
        "prompt_eval_count": count,
    }
else:
    payload = {
        "model": model,
        "response": "{}",
        "done": True,
        "prompt_eval_count": count,
    }
if mode == "extra-field":
    payload["extra"] = "unlisted"
sys.stdout.write(json.dumps(payload, sort_keys=True, separators=(",", ":")))
'''


class AdapterFixtureTests(RefusalAssertions):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fake = self.root / "fake-runtime.py"
        self.fake.write_text(f"#!{sys.executable}\n" + FAKE_ADAPTER_SOURCE, encoding="utf-8")
        self.fake.chmod(0o700)

    def tearDown(self):
        self.temporary.cleanup()

    def copied_fixture_root(self) -> Path:
        destination = self.root / "repository"
        fixture_destination = destination / "tests/fixtures/agent-instruction-v1"
        fixture_destination.parent.mkdir(parents=True)
        shutil.copytree(ROOT / "tests/fixtures/agent-instruction-v1", fixture_destination)
        for source in {item["source"]["path"] for item in manifest_record()["fixtures"]}:
            target = destination / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / source, target)
        return destination

    def rebind_changed_bootstrap(self, root: Path) -> str:
        manifest_path = root / MANIFEST.relative_to(ROOT)
        manifest = AI.load_canonical_record(manifest_path.read_bytes())
        bootstrap_path = root / manifest["evidence"]["decoder_bootstrap"]["path"]
        bootstrap = bootstrap_path.read_bytes() + b"Regeneration guard.\n"
        bootstrap_path.write_bytes(bootstrap)
        digest = hashlib.sha256(bootstrap).hexdigest()
        manifest["evidence"]["decoder_bootstrap"]["sha256"] = digest
        manifest_path.write_bytes(AI.canonical_record_bytes(manifest))
        return digest

    def profile(
        self,
        *,
        family: bool = False,
        mode: str = "normal",
        identity: str = "a" * 64,
        profile_id: str = "fake-tokenizer",
        family_id: str = "alpha",
        model: str = "fake-alpha:1",
    ) -> dict:
        executable_digest = sha256(self.fake)
        version = b"fake-runtime 1\n"
        acquisition = f"FROM @sha256-{identity}\n".encode("ascii")
        context_mode = "fresh-process" if family else "raw-prompt-count"
        result = {
            "schema": (
                "wildcat-agent-instruction-family-profile/v1"
                if family
                else AI.TOKENIZER_PROFILE_SCHEMA
            ),
            "id": profile_id,
            "adapter": AI.FAMILY_ADAPTER_SCHEMA if family else AI.TOKENIZER_ADAPTER_SCHEMA,
            "model": model,
            "model_blobs_sha256": [identity],
            "vocabulary_sha256": identity,
            "version": "fake-runtime-1",
            "executable": str(self.fake),
            "executable_sha256": executable_digest,
            "runtime_executable": str(self.fake),
            "runtime_executable_sha256": executable_digest,
            "version_argv": ["version"],
            "version_sha256": hashlib.sha256(version).hexdigest(),
            "identity_argv": ["identity", identity],
            "acquisition_sha256": hashlib.sha256(acquisition).hexdigest(),
            "argv": [
                "adapter",
                mode,
                (
                    "http://127.0.0.1:11434/api/chat"
                    if family
                    else "http://127.0.0.1:11434/api/generate"
                ),
            ],
            "environment_allowlist": [],
            "fixed_environment": {"FAKE_SAFE": "1"},
            "input_encoding": "utf-8",
            "context": {
                "mode": context_mode,
                "prior_messages": [],
                "examples": [],
                "repository_instruction_paths": [],
                "tool_definition_ids": [],
            },
            "timeout_seconds": "2",
            "max_stdout_bytes": "4096",
            "max_stderr_bytes": "4096",
            "context_window": "1024",
            "output_tokens": "32",
            "seed": "909",
            "observed_on": "2026-08-30",
        }
        if family:
            result["family"] = family_id
            result["thinking"] = "disabled"
        else:
            result["tokenizer"] = "fake"
        return result

    def family_profiles(self) -> dict:
        return {
            "schema": AI.FAMILY_PROFILES_SCHEMA,
            "profiles": [
                self.profile(
                    family=True,
                    identity="a" * 64,
                    profile_id="fake-alpha",
                    family_id="alpha",
                    model="fake-alpha:1",
                ),
                self.profile(
                    family=True,
                    identity="b" * 64,
                    profile_id="fake-beta",
                    family_id="beta",
                    model="fake-beta:1",
                ),
            ],
        }

    def question(self) -> dict:
        return {
            "id": "fake-question",
            "prompt": "Is the declared result enabled?",
            "accepted_answers": ["result-enabled", "result-disabled"],
            "refusal_answers": ["refuse-insufficient-context", "refuse-unknown"],
            "required_answer": "result-enabled",
            "context": {
                "mode": "fresh",
                "prior_messages": [],
                "examples": [],
                "repository_instruction_paths": [],
                "tool_definition_ids": [],
            },
        }


class MeasurementTests(AdapterFixtureTests, unittest.TestCase):
    def test_measure_regenerates_after_bound_inputs_change(self):
        copied = self.copied_fixture_root()
        bootstrap_sha256 = self.rebind_changed_bootstrap(copied)
        counts = iter([*((10, "{}") for _ in range(3)), (1, "{}"), *((value, "{}") for value in (5, 1) * 3)])
        with (
            mock.patch.object(AI, "_verify_profile_identity"),
            mock.patch.object(AI, "_ollama_generate", side_effect=lambda *args, **kwargs: next(counts)),
        ):
            report, accepted = AI.measure_manifest(copied, str(MANIFEST.relative_to(ROOT)))
        self.assertTrue(accepted)
        self.assertEqual(report["bootstrap_sha256"], bootstrap_sha256)

    def test_fake_tokenizer_profile_verifies_exact_identity(self):
        profile = AI.validate_tokenizer_profile(self.profile())
        AI._verify_profile_identity(profile)

    def test_changed_executable_digest_refuses(self):
        profile = self.profile()
        profile["executable_sha256"] = "0" * 64
        self.assertRefusal("WAI-E-ADAPTER.EXECUTABLE_CHANGED", AI._verify_profile_identity, profile)

    def test_changed_executable_refusal_names_the_tokenizer_and_the_machine(self):
        """skills#1098: the code and node path alone do not say what to do."""
        profile = self.profile()
        profile["executable_sha256"] = "0" * 64
        with self.assertRaises(AI.CodecError) as raised:
            AI._verify_profile_identity(profile)
        detail = raised.exception.detail
        self.assertIsNotNone(detail)
        self.assertIn(profile["id"], detail)
        self.assertIn(profile["runtime_executable"], detail)
        self.assertIn(profile["executable"], detail)
        self.assertIn("re-record", detail)

    def test_refusal_detail_never_reaches_the_emitted_record(self):
        error = AI.CodecError("WAI-E-ADAPTER.EXECUTABLE_CHANGED", "$.profile", "guidance")
        self.assertEqual(error.code, "WAI-E-ADAPTER.EXECUTABLE_CHANGED")
        self.assertEqual(error.node_path, "$.profile")
        self.assertEqual(error.detail, "guidance")
        self.assertNotIn("detail", AI._result("refused", error.code, error.node_path, b""))

    def test_refusal_detail_is_optional_and_bounded(self):
        self.assertIsNone(AI.CodecError("WAI-E-SHAPE.OBJECT", "$").detail)
        self.assertEqual(len(AI.CodecError("WAI-E-SHAPE.OBJECT", "$", "x" * 4096).detail), 1024)

    def test_changed_vocabulary_digest_refuses(self):
        profile = self.profile()
        profile["model_blobs_sha256"] = ["b" * 64]
        profile["vocabulary_sha256"] = "b" * 64
        self.assertRefusal("WAI-E-TOKENIZER.MISMATCH", AI._verify_profile_identity, profile)

    def test_changed_acquisition_digest_refuses(self):
        profile = self.profile()
        profile["acquisition_sha256"] = "0" * 64
        self.assertRefusal("WAI-E-ADAPTER.IDENTITY_CHANGED", AI._verify_profile_identity, profile)

    def test_changed_version_digest_refuses(self):
        profile = self.profile()
        profile["version_sha256"] = "0" * 64
        self.assertRefusal("WAI-E-ADAPTER.VERSION_CHANGED", AI._verify_profile_identity, profile)

    def test_rebound_profile_cannot_select_a_shell_runtime(self):
        manifest = manifest_record()
        profile_path = manifest["evidence"]["tokenizer_profile"]["path"]
        measurement_path = manifest["evidence"]["measurement_record"]["path"]
        profile = AI.load_canonical_record((ROOT / profile_path).read_bytes())
        profile["runtime_executable"] = "/bin/bash"
        profile["runtime_executable_sha256"] = hashlib.sha256(
            Path("/bin/bash").read_bytes()
        ).hexdigest()
        profile["version"] = "self-authorised-shell"
        profile["version_argv"] = ["-c", "printf 'fake-runtime 1\\n'"]
        profile["version_sha256"] = hashlib.sha256(b"fake-runtime 1\n").hexdigest()
        profile["identity_argv"] = [
            "-c",
            f"printf 'FROM @sha256-{profile['model_blobs_sha256'][0]}\\n'",
        ]
        profile["acquisition_sha256"] = hashlib.sha256(
            f"FROM @sha256-{profile['model_blobs_sha256'][0]}\n".encode("ascii")
        ).hexdigest()
        mutated_profile = AI.canonical_record_bytes(profile)
        mutated_profile_sha256 = hashlib.sha256(mutated_profile).hexdigest()
        manifest["evidence"]["tokenizer_profile"]["sha256"] = mutated_profile_sha256

        measurement = AI.load_canonical_record(
            (ROOT / measurement_path).read_bytes(), allow_integers=True
        )
        measurement["tokenizer_profile_sha256"] = mutated_profile_sha256
        mutated_measurement = AI.canonical_record_bytes(measurement, allow_integers=True)
        manifest["evidence"]["measurement_record"]["sha256"] = hashlib.sha256(
            mutated_measurement
        ).hexdigest()

        def artifact_bytes(root, artifact, path):
            if artifact["path"] == profile_path:
                return mutated_profile
            if artifact["path"] == measurement_path:
                return mutated_measurement
            return (ROOT / artifact["path"]).read_bytes()

        with (
            mock.patch.object(AI, "_load_bound_artifact", side_effect=artifact_bytes),
            mock.patch.object(AI, "_validate_measurement_record"),
            mock.patch.object(AI, "_validate_parity_record"),
        ):
            self.assertRefusal(
                "WAI-E-DIGEST.PROFILE",
                AI._load_evidence_artifacts,
                ROOT,
                manifest,
            )

    def test_both_runtime_profile_records_match_source_trust_anchors(self):
        manifest = manifest_record()
        self.assertEqual(
            set(AI.TRUSTED_PROFILE_SHA256),
            {"family_profiles", "tokenizer_profile"},
        )
        for name, expected_sha256 in AI.TRUSTED_PROFILE_SHA256.items():
            with self.subTest(name=name):
                artifact = manifest["evidence"][name]
                self.assertEqual(artifact["sha256"], expected_sha256)
                self.assertEqual(hashlib.sha256((ROOT / artifact["path"]).read_bytes()).hexdigest(), expected_sha256)

    def test_tokenizer_adapter_requires_argv_list(self):
        profile = self.profile()
        profile["argv"] = "adapter"
        self.assertRefusal("WAI-E-SHAPE.ARRAY", AI.validate_tokenizer_profile, profile)

    def test_tokenizer_adapter_refuses_remote_endpoint(self):
        profile = self.profile()
        profile["argv"][-1] = "https://example.invalid/api/generate"
        self.assertRefusal("WAI-E-ADAPTER.ENDPOINT", AI.validate_tokenizer_profile, profile)

    def test_tokenizer_adapter_refuses_credential_argv(self):
        profile = self.profile()
        profile["argv"].insert(-1, "Authorization: Bearer visible-secret")
        self.assertRefusal("WAI-E-ADAPTER.SECRET", AI.validate_tokenizer_profile, profile)

    def test_curl_adapter_must_disable_user_configuration(self):
        manifest = manifest_record()
        profile_path = manifest["evidence"]["tokenizer_profile"]["path"]
        profile = AI.load_canonical_record((ROOT / profile_path).read_bytes())
        profile["argv"] = profile["argv"][1:]
        self.assertRefusal("WAI-E-ADAPTER.ARGV", AI.validate_tokenizer_profile, profile)

    def test_identity_command_refuses_credential_argv(self):
        profile = self.profile()
        profile["identity_argv"].append("api_key=visible-secret")
        self.assertRefusal("WAI-E-ADAPTER.SECRET", AI.validate_tokenizer_profile, profile)

    def test_environment_allowlist_rejects_secret_name(self):
        profile = self.profile()
        profile["environment_allowlist"] = ["API_TOKEN"]
        self.assertRefusal("WAI-E-ADAPTER.ENVIRONMENT", AI.validate_tokenizer_profile, profile)

    def test_environment_allowlist_requires_sorted_names(self):
        profile = self.profile()
        profile["environment_allowlist"] = ["SAFE_Z", "SAFE_A"]
        self.assertRefusal("WAI-E-ADAPTER.ENVIRONMENT", AI.validate_tokenizer_profile, profile)

    def test_cleared_environment_contains_only_declared_values(self):
        stdout, _ = AI._run_bounded(
            str(self.fake),
            ["environment"],
            b"",
            {"FAKE_SAFE": "1"},
            2,
            4096,
            4096,
            "$.fake",
        )
        names = json.loads(stdout)
        self.assertIn("FAKE_SAFE", names)
        self.assertNotIn("HOME", names)
        self.assertFalse(any("TOKEN" in name or "SECRET" in name for name in names))

    def test_fake_negative_token_count_refuses(self):
        profile = self.profile(mode="negative-count")
        self.assertRefusal(
            "WAI-E-TOKENIZER.COUNT",
            AI._ollama_generate,
            profile,
            b"input",
            parity=False,
            path="$.fake",
        )

    def test_fake_non_integer_token_count_refuses(self):
        profile = self.profile(mode="non-integer-count")
        self.assertRefusal(
            "WAI-E-TOKENIZER.COUNT",
            AI._ollama_generate,
            profile,
            b"input",
            parity=False,
            path="$.fake",
        )

    def test_oversized_adapter_integer_refuses_without_escaping(self):
        response = (
            b'{"done":true,"model":"fake-alpha:1","prompt_eval_count":'
            + b"1" * 5_000
            + b',"response":"{}"}'
        )
        try:
            AI._ollama_response(response, "fake-alpha:1", "$.fake")
        except AI.CodecError as error:
            self.assertEqual(error.code, "WAI-E-ADAPTER.JSON")
        except Exception as error:
            self.fail(f"oversized adapter integer escaped as {type(error).__name__}")
        else:
            self.fail("oversized adapter integer was accepted")

    def test_non_scalar_adapter_response_refuses_without_escaping(self):
        response = (
            b'{"done":true,"model":"fake-alpha:1","prompt_eval_count":1,'
            b'"response":"\\ud800"}'
        )
        try:
            AI._ollama_response(response, "fake-alpha:1", "$.fake")
        except AI.CodecError as error:
            self.assertEqual(error.code, "WAI-E-UTF8.SCALAR")
        except Exception as error:
            self.fail(f"non-scalar adapter response escaped as {type(error).__name__}")
        else:
            self.fail("non-scalar adapter response was accepted")

    def test_non_scalar_bound_evidence_record_refuses_without_escaping(self):
        record = b'{"schema":"\\ud800"}\n'
        try:
            AI.load_canonical_record(record, allow_integers=True)
        except AI.CodecError as error:
            self.assertEqual(error.code, "WAI-E-UTF8.SCALAR")
        except Exception as error:
            self.fail(f"non-scalar bound evidence escaped as {type(error).__name__}")
        else:
            self.fail("non-scalar bound evidence was accepted")

    def test_fake_tokenizer_model_mismatch_refuses(self):
        profile = self.profile(mode="model-mismatch")
        self.assertRefusal(
            "WAI-E-TOKENIZER.MISMATCH",
            AI._ollama_generate,
            profile,
            b"input",
            parity=False,
            path="$.fake",
        )

    def test_fake_timeout_refuses(self):
        profile = self.profile(mode="sleep")
        profile["timeout_seconds"] = "1"
        self.assertRefusal(
            "WAI-E-ADAPTER.TIMEOUT",
            AI._ollama_generate,
            profile,
            b"input",
            parity=False,
            path="$.fake",
        )

    def test_fake_stdout_cap_refuses(self):
        self.assertRefusal(
            "WAI-E-ADAPTER.OUTPUT_CAP",
            AI._run_bounded,
            str(self.fake),
            ["adapter", "stdout-cap"],
            b"",
            {},
            2,
            32,
            32,
            "$.fake",
        )

    def test_fake_stderr_cap_refuses(self):
        self.assertRefusal(
            "WAI-E-ADAPTER.OUTPUT_CAP",
            AI._run_bounded,
            str(self.fake),
            ["adapter", "stderr-cap"],
            b"",
            {},
            2,
            32,
            32,
            "$.fake",
        )

    def test_unavailable_executable_refuses(self):
        self.assertRefusal(
            "WAI-E-ADAPTER.UNAVAILABLE",
            AI._run_bounded,
            "/definitely/not/a/runtime",
            ["adapter"],
            b"",
            {},
            1,
            32,
            32,
            "$.fake",
        )

    def test_bootstrap_omission_refuses(self):
        manifest = manifest_record()

        def artifact_bytes(root, artifact, path):
            if path == "$.evidence.decoder_bootstrap":
                return b""
            return (ROOT / artifact["path"]).read_bytes()

        with mock.patch.object(AI, "_load_bound_artifact", side_effect=artifact_bytes):
            self.assertRefusal(
                "WAI-E-MEASURE.BOOTSTRAP",
                AI._load_evidence_artifacts,
                ROOT,
                manifest,
            )

    def test_decoder_bootstrap_carries_record_field_signatures(self):
        manifest = manifest_record()
        bootstrap = (ROOT / manifest["evidence"]["decoder_bootstrap"]["path"]).read_text(
            encoding="utf-8"
        )
        required = (
            "D,0,id,title; S,1,id,path,sha256; H,1,id,title",
            "M,3,id,claim; depth 4 order",
            "I* id,authority,gate,subject,scope,record,expiry,recovery",
            "B,1,source,node,start,end,reviewer",
            "Order D,S*,H*(directives(expressions,M?)),relations*,B*",
            "JSON=(schema document sources sections relations bindings)",
            "literal=(kind value); directive=(id kind statement expressions promise)",
        )
        for signature in required:
            with self.subTest(signature=signature):
                self.assertIn(signature, bootstrap)

    def test_non_negative_compression_delta_refuses(self):
        with (
            mock.patch.object(AI, "_verify_profile_identity"),
            mock.patch.object(AI, "_ollama_generate", return_value=(1, "{}")),
        ):
            report, accepted = AI.measure_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        self.assertFalse(accepted)
        self.assertEqual(report["totals"]["delta_tokens"], "1")
        self.assertEqual(report["summary"]["refusal_codes"], ["WAI-E-MEASURE.NON_NEGATIVE_DELTA"])

    def test_source_baseline_precedes_each_compact_count(self):
        observed = []

        def count(profile, prompt, **kwargs):
            observed.append(prompt)
            return 1, "{}"

        with (
            mock.patch.object(AI, "_verify_profile_identity"),
            mock.patch.object(AI, "_ollama_generate", side_effect=count),
        ):
            AI.measure_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        manifest = manifest_record()
        expected = []
        for fixture in manifest["fixtures"]:
            source = (ROOT / fixture["source"]["path"]).read_bytes()
            expected.append(
                source[int(fixture["source"]["start"]):int(fixture["source"]["end"])]
            )
        expected.append((ROOT / manifest["evidence"]["decoder_bootstrap"]["path"]).read_bytes())
        for fixture in manifest["fixtures"]:
            expected.extend(
                [
                    (ROOT / fixture["artifacts"]["model"]["path"]).read_bytes(),
                    (ROOT / fixture["artifacts"]["compact"]["path"]).read_bytes(),
                ]
            )
        self.assertEqual([hashlib.sha256(item).hexdigest() for item in observed], [hashlib.sha256(item).hexdigest() for item in expected])

    def test_measurement_report_has_exact_ten_integer_cases(self):
        counts = iter([*((10, "{}") for _ in range(3)), (1, "{}"), *((value, "{}") for value in (5, 1) * 3)])
        with (
            mock.patch.object(AI, "_verify_profile_identity"),
            mock.patch.object(AI, "_ollama_generate", side_effect=lambda *args, **kwargs: next(counts)),
        ):
            report, accepted = AI.measure_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        self.assertTrue(accepted)
        self.assertEqual(report["summary"]["case_count"], 10)
        self.assertIsInstance(report["totals"]["source_tokens"], int)
        self.assertIsInstance(report["bootstrap"]["tokens"], int)

    def test_rebound_inconsistent_measurement_record_refuses(self):
        manifest = manifest_record()
        measurement_path = manifest["evidence"]["measurement_record"]["path"]
        measurement = AI.load_canonical_record(
            (ROOT / measurement_path).read_bytes(), allow_integers=True
        )
        measurement["totals"]["source_tokens"] = 0
        mutated = AI.canonical_record_bytes(measurement, allow_integers=True)
        manifest["evidence"]["measurement_record"]["sha256"] = hashlib.sha256(
            mutated
        ).hexdigest()

        def artifact_bytes(root, artifact, path):
            if artifact["path"] == measurement_path:
                return mutated
            return (ROOT / artifact["path"]).read_bytes()

        with mock.patch.object(AI, "_load_bound_artifact", side_effect=artifact_bytes):
            self.assertRefusal(
                "WAI-E-MEASURE.RECORD",
                AI._load_evidence_artifacts,
                ROOT,
                manifest,
            )

    def test_contract_reports_exact_two_document_token_delta(self):
        manifest = manifest_record()
        measurement = AI.load_canonical_record(
            (ROOT / manifest["evidence"]["measurement_record"]["path"]).read_bytes(),
            allow_integers=True,
        )
        two_document = next(
            item for item in measurement["amortised"] if item["document_count"] == 2
        )
        delta = int(two_document["delta_tokens"])
        contract = (ROOT / AI.CONTRACT_PATH).read_text(encoding="utf-8")
        self.assertIn(
            f"The two-document prefix reports `{delta:+d}`",
            contract,
        )

    def test_measure_cli_atomically_replaces_report(self):
        (self.root / "manifest.json").write_bytes(b"{}\n")
        (self.root / "report.json").write_bytes(b"old")
        summary = {
            "event": "run.summary",
            "correlation_id": "c" * 64,
            "case_count": 1,
            "passed": 1,
            "failed": 0,
            "refused": 0,
            "unknown": 0,
            "verdict": "accepted",
            "unknowns": [],
            "refusal_codes": [],
        }
        report = {"schema": AI.MEASUREMENT_SCHEMA, "summary": summary}
        output = io.StringIO()
        with (
            mock.patch.object(AI, "measure_manifest", return_value=(report, True)),
            contextlib.redirect_stdout(output),
        ):
            result = AI.main(
                [
                    "measure",
                    "--root",
                    str(self.root),
                    "--manifest",
                    "manifest.json",
                    "--output",
                    "report.json",
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(
            (self.root / "report.json").read_bytes(),
            AI.canonical_record_bytes(report, allow_integers=True),
        )
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["fake-runtime.py", "manifest.json", "report.json"])


class ParityAdapterTests(AdapterFixtureTests, unittest.TestCase):
    def test_parity_regenerates_after_bound_inputs_change(self):
        copied = self.copied_fixture_root()
        bootstrap_sha256 = self.rebind_changed_bootstrap(copied)

        def answer(profile, prompt, **kwargs):
            return 1, json.dumps({"answer_id": kwargs["answer_ids"][0]})

        with (
            mock.patch.object(AI, "_verify_profile_identity"),
            mock.patch.object(AI, "_ollama_generate", side_effect=answer),
        ):
            report, accepted = AI.parity_manifest(copied, str(MANIFEST.relative_to(ROOT)))
        self.assertTrue(accepted)
        self.assertEqual(report["bootstrap_sha256"], bootstrap_sha256)

    def test_two_genuinely_distinct_fake_families_validate(self):
        profiles = self.family_profiles()
        self.assertIs(AI.validate_family_profiles(profiles), profiles)

    def test_alias_only_family_names_refuse(self):
        profiles = self.family_profiles()
        profiles["profiles"][1]["family"] = profiles["profiles"][0]["family"]
        self.assertRefusal("WAI-E-PARITY.ALIAS", AI.validate_family_profiles, profiles)

    def test_alias_only_model_blobs_refuse(self):
        profiles = self.family_profiles()
        profiles["profiles"][1]["model_blobs_sha256"] = profiles["profiles"][0]["model_blobs_sha256"]
        profiles["profiles"][1]["vocabulary_sha256"] = profiles["profiles"][0]["vocabulary_sha256"]
        self.assertRefusal("WAI-E-PARITY.ALIAS", AI.validate_family_profiles, profiles)

    def test_alias_only_acquisition_records_refuse(self):
        profiles = self.family_profiles()
        profiles["profiles"][1]["acquisition_sha256"] = profiles["profiles"][0]["acquisition_sha256"]
        self.assertRefusal("WAI-E-PARITY.ALIAS", AI.validate_family_profiles, profiles)

    def test_missing_second_family_refuses(self):
        profiles = self.family_profiles()
        profiles["profiles"].pop()
        self.assertRefusal("WAI-E-BOUNDS.COUNT", AI.validate_family_profiles, profiles)

    def test_prior_message_context_reuse_refuses(self):
        profiles = self.family_profiles()
        profiles["profiles"][0]["context"]["prior_messages"] = ["old"]
        self.assertRefusal("WAI-E-PARITY.CONTEXT", AI.validate_family_profiles, profiles)

    def test_example_context_reuse_refuses(self):
        profiles = self.family_profiles()
        profiles["profiles"][0]["context"]["examples"] = ["old"]
        self.assertRefusal("WAI-E-PARITY.CONTEXT", AI.validate_family_profiles, profiles)

    def test_repository_instruction_contamination_refuses(self):
        profiles = self.family_profiles()
        profiles["profiles"][0]["context"]["repository_instruction_paths"] = ["AGENTS.md"]
        self.assertRefusal("WAI-E-PARITY.CONTEXT", AI.validate_family_profiles, profiles)

    def test_tool_definition_contamination_refuses(self):
        profiles = self.family_profiles()
        profiles["profiles"][0]["context"]["tool_definition_ids"] = ["shell"]
        self.assertRefusal("WAI-E-PARITY.CONTEXT", AI.validate_family_profiles, profiles)

    def test_unknown_thinking_mode_refuses(self):
        profiles = self.family_profiles()
        profiles["profiles"][0]["thinking"] = "ambient"
        self.assertRefusal("WAI-E-ADAPTER.THINKING", AI.validate_family_profiles, profiles)

    def test_fake_unavailable_model_refuses(self):
        profile = self.profile(family=True, mode="exit")
        self.assertRefusal(
            "WAI-E-ADAPTER.UNAVAILABLE",
            AI._ollama_generate,
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )

    def test_fake_chat_preserves_accepted_answer(self):
        profile = self.profile(family=True)
        count, response = AI._ollama_generate(
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )
        answer = AI._answer_record(response, self.question())
        self.assertEqual(count, 7)
        self.assertEqual(answer["answer_id"], "result-enabled")
        self.assertEqual(answer["outcome"], "accepted")

    def test_fake_unknown_answer_refuses_without_coercion(self):
        profile = self.profile(family=True, mode="unknown-answer")
        _, response = AI._ollama_generate(
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )
        answer = AI._answer_record(response, self.question())
        self.assertEqual(answer["answer_id"], "unlisted-answer")
        self.assertEqual(answer["code"], "WAI-E-PARITY.UNLISTED")

    def test_fake_malformed_answer_refuses(self):
        profile = self.profile(family=True, mode="malformed-answer")
        _, response = AI._ollama_generate(
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )
        answer = AI._answer_record(response, self.question())
        self.assertIsNone(answer["answer_id"])
        self.assertEqual(answer["code"], "WAI-E-PARITY.ANSWER")

    def test_fake_model_refusal_is_preserved(self):
        profile = self.profile(family=True, mode="model-refusal")
        _, response = AI._ollama_generate(
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )
        answer = AI._answer_record(response, self.question())
        self.assertEqual(answer["answer_id"], "refuse-unknown")
        self.assertEqual(answer["code"], "WAI-E-PARITY.MODEL_REFUSAL")
        self.assertEqual(answer["response"], response)

    def test_fake_chat_response_cap_refuses(self):
        profile = self.profile(family=True, mode="large-answer")
        self.assertRefusal(
            "WAI-E-ADAPTER.RESPONSE",
            AI._ollama_generate,
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )

    def test_fake_chat_non_integer_count_refuses(self):
        profile = self.profile(family=True, mode="non-integer-count")
        self.assertRefusal(
            "WAI-E-TOKENIZER.COUNT",
            AI._ollama_generate,
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )

    def test_oversized_chat_integer_refuses_without_escaping(self):
        response = (
            b'{"done":true,"message":{"content":"{}","role":"assistant"},'
            b'"model":"fake-alpha:1","prompt_eval_count":'
            + b"1" * 5_000
            + b"}"
        )
        try:
            AI._ollama_chat_response(response, "fake-alpha:1", "$.fake")
        except AI.CodecError as error:
            self.assertEqual(error.code, "WAI-E-ADAPTER.JSON")
        except Exception as error:
            self.fail(f"oversized chat integer escaped as {type(error).__name__}")
        else:
            self.fail("oversized chat integer was accepted")

    def test_non_scalar_chat_response_refuses_without_escaping(self):
        response = (
            b'{"done":true,"message":{"content":"\\ud800","role":"assistant"},'
            b'"model":"fake-alpha:1","prompt_eval_count":1}'
        )
        try:
            AI._ollama_chat_response(response, "fake-alpha:1", "$.fake")
        except AI.CodecError as error:
            self.assertEqual(error.code, "WAI-E-UTF8.SCALAR")
        except Exception as error:
            self.fail(f"non-scalar chat response escaped as {type(error).__name__}")
        else:
            self.fail("non-scalar chat response was accepted")

    def test_non_scalar_answer_id_is_preserved_as_a_bounded_refusal(self):
        answer = AI._answer_record('{"answer_id":"\\ud800"}', self.question())
        self.assertIsNone(answer["answer_id"])
        self.assertEqual(answer["code"], "WAI-E-PARITY.ANSWER")
        self.assertEqual(answer["response"], '{"answer_id":"\\ud800"}')

    def test_fake_chat_extra_field_refuses(self):
        profile = self.profile(family=True, mode="extra-field")
        self.assertRefusal(
            "WAI-E-ADAPTER.RESPONSE",
            AI._ollama_generate,
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )

    def test_secret_text_is_redacted_from_refusal_record(self):
        responses = (
            "token=visible-secret",
            '{"api_key":"visible-secret"}',
            "Authorization: Bearer visible-secret",
        )
        for response in responses:
            with self.subTest(response=response):
                answer = AI._answer_record(response, self.question())
                self.assertNotIn("visible-secret", answer["response"])
                self.assertIn("[REDACTED]", answer["response"])

    def test_secret_shaped_unlisted_answer_id_is_redacted_from_refusal_record(self):
        response = json.dumps(
            {"answer_id": "token=visible-secret"},
            sort_keys=True,
            separators=(",", ":"),
        )
        answer = AI._answer_record(response, self.question())
        self.assertEqual(answer["code"], "WAI-E-PARITY.UNLISTED")
        self.assertNotIn("visible-secret", json.dumps(answer, sort_keys=True))
        self.assertEqual(answer["answer_id"], "token=[REDACTED]")

    def test_secret_answer_id_redaction_cannot_expand_past_response_cap(self):
        answer_id = ("token=x " * 60).rstrip()
        response = json.dumps(
            {"answer_id": answer_id},
            sort_keys=True,
            separators=(",", ":"),
        )
        self.assertLessEqual(len(response.encode("utf-8")), AI.MAX_PARITY_RESPONSE_BYTES)
        answer = AI._answer_record(response, self.question())
        self.assertEqual(
            answer["answer_id"],
            "[REDACTED: answer id exceeded stored bound]",
        )
        self.assertLessEqual(
            len(answer["answer_id"].encode("utf-8")),
            AI.MAX_PARITY_RESPONSE_BYTES,
        )
        self.assertEqual(answer["code"], "WAI-E-PARITY.UNLISTED")

    def test_secret_redaction_cannot_expand_past_response_cap(self):
        response = ("token=x " * 64)[: AI.MAX_PARITY_RESPONSE_BYTES]
        self.assertEqual(len(response.encode("utf-8")), AI.MAX_PARITY_RESPONSE_BYTES)
        answer = AI._answer_record(response, self.question())
        self.assertEqual(answer["response"], "[REDACTED: response exceeded stored bound]")
        self.assertLessEqual(
            len(answer["response"].encode("utf-8")), AI.MAX_PARITY_RESPONSE_BYTES
        )
        self.assertEqual(answer["code"], "WAI-E-PARITY.ANSWER")

    def test_prompt_does_not_label_answer_outcome_classes(self):
        template = (ROOT / manifest_record()["evidence"]["parity_prompt"]["path"]).read_bytes()
        prompt = AI._render_parity_prompt(template, "source", b"bootstrap\n", b"document\n", self.question())
        text = prompt.decode("utf-8")
        self.assertIn(
            "Candidate answer ids: refuse-insufficient-context,refuse-unknown,result-disabled,result-enabled",
            text,
        )
        self.assertIn(
            "`refuse-unknown` means refusal because the answer is unknown, not a generic refusal",
            text,
        )
        self.assertNotIn("Document-grounded answer ids", text)
        self.assertNotIn("Evidence-refusal ids", text)

    def test_chat_transport_does_not_enumerate_answer_ids(self):
        capture = self.root / "request.ndjson"
        profile = self.profile(family=True)
        profile["fixed_environment"]["FAKE_CAPTURE"] = str(capture)
        AI._ollama_generate(
            profile,
            b"prompt",
            parity=True,
            path="$.fake",
            answer_ids=["result-enabled", "refuse-unknown"],
        )
        request = json.loads(capture.read_text(encoding="utf-8"))
        self.assertEqual(request["format"]["properties"]["answer_id"], {"type": "string"})

    def test_source_prompt_omits_bootstrap_and_compact_prompt_includes_it(self):
        template = (ROOT / manifest_record()["evidence"]["parity_prompt"]["path"]).read_bytes()
        source = AI._render_parity_prompt(template, "source", b"unique-bootstrap\n", b"document\n", self.question())
        compact = AI._render_parity_prompt(template, "compact", b"unique-bootstrap\n", b"document\n", self.question())
        self.assertNotIn(b"unique-bootstrap", source)
        self.assertIn(b"unique-bootstrap", compact)

    def test_fake_requests_are_isolated_one_message_jobs(self):
        capture = self.root / "requests.ndjson"
        profile = self.profile(family=True)
        profile["fixed_environment"]["FAKE_CAPTURE"] = str(capture)
        for _ in range(2):
            AI._ollama_generate(
                profile,
                b"prompt",
                parity=True,
                path="$.fake",
                answer_ids=["result-enabled", "refuse-unknown"],
            )
        requests = [json.loads(line) for line in capture.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(requests), 2)
        for request in requests:
            self.assertEqual(request["messages"], [{"role": "user", "content": "prompt"}])
            self.assertNotIn("context", request)
            self.assertNotIn("tools", request)
            self.assertNotIn("enum", request["format"]["properties"]["answer_id"])

    def test_validated_question_record_regression_runs_all_pairs(self):
        def answer(profile, prompt, **kwargs):
            return 1, json.dumps({"answer_id": kwargs["answer_ids"][0]})

        with (
            mock.patch.object(AI, "_verify_profile_identity"),
            mock.patch.object(AI, "_ollama_generate", side_effect=answer),
        ):
            report, accepted = AI.parity_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        self.assertTrue(accepted)
        self.assertEqual(len(report["results"]), 18)
        self.assertEqual(report["summary"]["case_count"], 36)
        self.assertEqual(report["summary"]["passed"], 18)

    def test_rebound_inconsistent_parity_record_refuses(self):
        manifest = manifest_record()
        parity_path = manifest["evidence"]["parity_record"]["path"]
        parity = AI.load_canonical_record(
            (ROOT / parity_path).read_bytes(), allow_integers=True
        )
        parity["summary"]["passed"] = 0
        mutated = AI.canonical_record_bytes(parity, allow_integers=True)
        manifest["evidence"]["parity_record"]["sha256"] = hashlib.sha256(
            mutated
        ).hexdigest()

        def artifact_bytes(root, artifact, path):
            if artifact["path"] == parity_path:
                return mutated
            return (ROOT / artifact["path"]).read_bytes()

        with mock.patch.object(AI, "_load_bound_artifact", side_effect=artifact_bytes):
            self.assertRefusal(
                "WAI-E-PARITY.RECORD",
                AI._load_evidence_artifacts,
                ROOT,
                manifest,
            )

    def test_mismatch_and_required_failures_are_reported(self):
        def answer(profile, prompt, **kwargs):
            selected = kwargs["answer_ids"][1] if kwargs["path"].endswith("horos-security-review.compact") else kwargs["answer_ids"][0]
            return 1, json.dumps({"answer_id": selected})

        with (
            mock.patch.object(AI, "_verify_profile_identity"),
            mock.patch.object(AI, "_ollama_generate", side_effect=answer),
        ):
            report, accepted = AI.parity_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        self.assertFalse(accepted)
        failures = [item for item in report["results"] if item["verdict"] == "refused"]
        self.assertEqual(len(failures), 2)
        self.assertIn("WAI-E-PARITY.MISMATCH", failures[0]["refusal_codes"])
        self.assertIn("WAI-E-PARITY.REQUIRED", failures[0]["refusal_codes"])

    def test_parity_cli_atomically_creates_report(self):
        (self.root / "manifest.json").write_bytes(b"{}\n")
        summary = {
            "event": "run.summary",
            "correlation_id": "c" * 64,
            "case_count": 2,
            "question_pair_count": 1,
            "passed": 1,
            "failed": 0,
            "refused": 0,
            "unknown": 0,
            "verdict": "accepted",
            "unknowns": [],
            "refusal_codes": [],
        }
        report = {"schema": AI.PARITY_SCHEMA, "summary": summary}
        output = io.StringIO()
        with (
            mock.patch.object(AI, "parity_manifest", return_value=(report, True)),
            contextlib.redirect_stdout(output),
        ):
            result = AI.main(
                [
                    "parity",
                    "--root",
                    str(self.root),
                    "--manifest",
                    "manifest.json",
                    "--output",
                    "parity.json",
                ]
            )
        self.assertEqual(result, 0)
        self.assertEqual(
            (self.root / "parity.json").read_bytes(),
            AI.canonical_record_bytes(report, allow_integers=True),
        )
        self.assertEqual(sorted(path.name for path in self.root.iterdir()), ["fake-runtime.py", "manifest.json", "parity.json"])


class AgentInstructionIntegrationTests(RefusalAssertions, unittest.TestCase):
    COVERAGE_PATH = ROOT / "tests/promise_machine_coverage.json"
    PROMISE_ID = "promise-machine-agent-instruction-prototype"

    def coverage(self) -> dict:
        return json.loads(self.COVERAGE_PATH.read_text(encoding="utf-8"))["agent_instruction"]

    def copied_root(self, destination: Path) -> Path:
        fixture_destination = destination / "tests/fixtures/agent-instruction-v1"
        fixture_destination.parent.mkdir(parents=True)
        shutil.copytree(ROOT / "tests/fixtures/agent-instruction-v1", fixture_destination)
        for source in {item["source"]["path"] for item in manifest_record()["fixtures"]}:
            target = destination / source
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / source, target)
        return destination

    def assert_bound_paths(self, records: list[dict]) -> None:
        for record in records:
            with self.subTest(path=record["path"]):
                path = ROOT / record["path"]
                self.assertTrue(path.is_file())
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), record["sha256"])

    def test_root_promise_has_complete_exact_field_inventory(self):
        source = (ROOT / "PROMISE_MACHINE.md").read_text(encoding="utf-8")
        block = source.split(f"### {self.PROMISE_ID}\n", 1)[1].split("\n## Installation copies", 1)[0]
        fields = (
            "Promise",
            "Evidence",
            "Evidence classes",
            "Boundary",
            "Authorises",
            "Consequence",
            "Refuses",
            "Recovery",
            "Exceptions",
        )
        for field in fields:
            with self.subTest(field=field):
                self.assertEqual(block.count(f"- {field}:"), 1)

    def test_specialised_coverage_binds_promise_and_contract(self):
        coverage = self.coverage()
        self.assertEqual(coverage["contract"], AI.SCHEMA_ID)
        self.assertEqual(coverage["promise_id"], self.PROMISE_ID)
        self.assertIn("exact checked compact documents", coverage["transition"])

    def test_contract_counts_bare_binding_offsets_in_decoded_byte_budgets(self):
        contract = (ROOT / "docs/agent-instruction-language-v1.md").read_text(encoding="utf-8")
        self.assertIn("| one decoded literal or binding offset | 65,000 | UTF-8 bytes |", contract)
        self.assertIn("| all decoded literals and binding offsets | 786,432 | UTF-8 bytes |", contract)

    def test_specialised_coverage_binds_runtime_documentation_and_manifest(self):
        coverage = self.coverage()
        self.assertEqual(coverage["checker"]["path"], "scripts/agent_instruction.py")
        self.assertEqual(coverage["manifest"]["path"], str(MANIFEST.relative_to(ROOT)))
        self.assertEqual(
            sorted(record["path"] for record in coverage["documentation"]),
            [
                "docs/agent-instruction-language-v1.md",
                "docs/decisions/ADR-062-encode-a-closed-agent-instruction-model.md",
            ],
        )
        records = [coverage["checker"], coverage["manifest"], *coverage["documentation"]]
        self.assert_bound_paths(records)

    def test_specialised_coverage_binds_focused_tests(self):
        record = self.coverage()["tests"]
        self.assertEqual(set(record), {"path", "sha256", "selectors"})
        self.assertEqual(record["path"], "tests/test_agent_instruction.py")
        self.assert_bound_paths([{"path": record["path"], "sha256": record["sha256"]}])
        selectors = record["selectors"]
        self.assertIsInstance(selectors, list)
        self.assertTrue(selectors)
        self.assertEqual(len(selectors), len(set(selectors)))
        source = (ROOT / record["path"]).read_text(encoding="utf-8")
        for selector in selectors:
            with self.subTest(selector=selector):
                self.assertIsInstance(selector, str)
                self.assertIn(f"def {selector}(", source)

    def test_specialised_coverage_binds_all_fixture_artifacts(self):
        coverage = self.coverage()
        manifest = manifest_record()
        records = coverage["fixtures"]
        expected_paths = sorted(
            fixture["artifacts"][artifact]["path"]
            for fixture in manifest["fixtures"]
            for artifact in AI.FIXTURE_ARTIFACTS
        )
        self.assertEqual(sorted(record["path"] for record in records), expected_paths)
        self.assert_bound_paths(records)

    def test_specialised_coverage_binds_all_evidence_records(self):
        coverage = self.coverage()
        expected_paths = sorted(record["path"] for record in manifest_record()["evidence"].values())
        self.assertEqual(sorted(record["path"] for record in coverage["evidence"]), expected_paths)
        self.assert_bound_paths(coverage["evidence"])

    def test_bound_manifest_runs_complete_clean_demonstration(self):
        records = AI.check_manifest(ROOT, str(MANIFEST.relative_to(ROOT)))
        self.assertEqual(records[-1]["outcome"], "accepted")
        self.assertEqual(records[-1]["binding_count"], 15)
        self.assertEqual(records[-1]["mutation_count"], 14)
        self.assertEqual(records[-1]["question_count"], 9)
        self.assertEqual(records[-1]["roundtrip_count"], 3)

    def test_compact_documents_reproduce_from_bound_models(self):
        for fixture in manifest_record()["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                model = AI.load_canonical_record((ROOT / fixture["artifacts"]["model"]["path"]).read_bytes())
                compact = (ROOT / fixture["artifacts"]["compact"]["path"]).read_bytes()
                self.assertEqual(AI.format_compact(model), compact)

    def test_plugin_promise_machine_copies_are_current(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/promise_machine.py"), "sync", "--check", "--json"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_portable_promise_machine_package_is_current(self):
        with tempfile.TemporaryDirectory() as temporary:
            package = Path(temporary) / "package"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/portable_promise_machine.py"),
                    "package",
                    "--out",
                    str(package),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            verifier = (
                package
                / ".agents/skills/promise-machine/scripts/verify_runtime.py"
            )
            verified = subprocess.run(
                [sys.executable, str(verifier)],
                cwd=package,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                verified.returncode, 0, verified.stdout + verified.stderr
            )

    def assert_stale_report_refuses(self, evidence_key: str, field_path: tuple[str, ...], code: str) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied = self.copied_root(Path(temporary))
            manifest_path = copied / MANIFEST.relative_to(ROOT)
            manifest = AI.load_canonical_record(manifest_path.read_bytes())
            report_path = copied / manifest["evidence"][evidence_key]["path"]
            report = AI.load_canonical_record(report_path.read_bytes(), allow_integers=True)
            target = report
            for key in field_path[:-1]:
                target = target[key]
            target[field_path[-1]] = 0
            changed = AI.canonical_record_bytes(report, allow_integers=True)
            report_path.write_bytes(changed)
            manifest["evidence"][evidence_key]["sha256"] = hashlib.sha256(changed).hexdigest()
            manifest_path.write_bytes(AI.canonical_record_bytes(manifest))
            self.assertRefusal(code, AI.check_manifest, copied, str(MANIFEST.relative_to(ROOT)))

    def test_stale_measurement_report_refuses(self):
        self.assert_stale_report_refuses(
            "measurement_record",
            ("totals", "source_tokens"),
            "WAI-E-MEASURE.RECORD",
        )

    def test_stale_parity_report_refuses(self):
        self.assert_stale_report_refuses(
            "parity_record",
            ("summary", "passed"),
            "WAI-E-PARITY.RECORD",
        )


class DigestNeutralProjectionTests(unittest.TestCase):
    """`digest_neutral_projection`, before anything is measured through it.

    The projection exists so that editing a bound instruction document outside
    its reviewed span stops moving the corpus digest. Step 3 of the skills#1098
    runbook switches `_corpus_sha256` onto it; this step only adds it, so every
    case here runs against the committed fixture as it stands and none of them
    writes a file. The bound sources are read and never written: the edit these
    cases reason about is applied to bytes in memory.

    Each case is written to fail if its property is removed. A projection that
    did nothing would pass "changes only the digest positions" vacuously and
    would pass idempotence trivially, so both cases also require the projection
    to have moved the artefacts that carry a bound digest, and the out-of-span
    case compares two byte strings that are known to differ before projection.
    """

    # Appended at end of file, which is past every fixture's reviewed span, so
    # no recorded binding offset and no reviewed byte moves. The edit shape the
    # design is meant to stop charging for.
    OUT_OF_SPAN_EDIT = b"\n<!-- skills#1098 out-of-span edit -->\n"

    PLACEHOLDER = "f" * 64

    def setUp(self) -> None:
        self.manifest = manifest_record()
        self.source_digests = sorted(
            {fixture["source"]["sha256"] for fixture in self.manifest["fixtures"]}
        )

    def bound_artifacts(self) -> dict[str, bytes]:
        """Every file the manifest binds that this projection could touch.

        `mutations` and `questions` are in deliberately. They are bound
        artefacts that embed no source digest, so they are the control on
        "changes nothing else": a projection reaching further than the digest
        would show up as a change to one of them.
        """
        artifacts = {str(MANIFEST.relative_to(ROOT)): MANIFEST.read_bytes()}
        for fixture in self.manifest["fixtures"]:
            for record in fixture["artifacts"].values():
                artifacts[record["path"]] = (ROOT / record["path"]).read_bytes()
        return artifacts

    def occurrences(self, data: bytes) -> list[int]:
        """Every offset at which a bound whole-file source digest starts."""
        found = []
        for digest in self.source_digests:
            needle = digest.encode("ascii")
            start = data.find(needle)
            while start >= 0:
                found.append(start)
                start = data.find(needle, start + 1)
        return sorted(found)

    def test_projection_is_idempotent(self):
        """Projecting a projection changes nothing further.

        The fixed point is reached in one pass, so a caller cannot get a
        different answer by applying the projection a different number of
        times, and step 3 can digest the result without recording how many
        passes produced it. Applying it to the marker itself is the same
        claim from the other side: the marker is not itself rewritten, so the
        substitution cannot cascade.

        Idempotence is trivially true of a projection that does nothing, so
        this also requires the first pass to have moved every artefact that
        carries a bound digest.
        """
        moved = 0
        for path, raw in sorted(self.bound_artifacts().items()):
            with self.subTest(path=path):
                once = AI.digest_neutral_projection(self.manifest, raw)
                twice = AI.digest_neutral_projection(self.manifest, once)
                self.assertEqual(once, twice)
                if self.occurrences(raw):
                    self.assertNotEqual(raw, once, "the projection left the digest in place")
                    moved += 1
        # manifest, plus model, source_spans and compact for each of three
        # fixtures: the four places a bound whole-file digest is embedded.
        self.assertEqual(10, moved)

        marker = self.PLACEHOLDER.encode("ascii")
        self.assertEqual(marker, AI.digest_neutral_projection(self.manifest, marker))

    def test_projection_changes_only_the_bound_source_digest_positions(self):
        """Byte-identical to the committed fixture except where a digest sat.

        Length is preserved, every differing byte falls inside a bound digest's
        own 64 bytes, and each of those runs now reads as the marker. The two
        artefacts that embed no digest come through untouched, which is what
        makes "changes nothing else" an observation rather than a claim.
        """
        for path, raw in sorted(self.bound_artifacts().items()):
            with self.subTest(path=path):
                projected = AI.digest_neutral_projection(self.manifest, raw)
                self.assertEqual(len(raw), len(projected))

                starts = self.occurrences(raw)
                covered = {
                    offset for start in starts for offset in range(start, start + 64)
                }
                differing = {
                    offset
                    for offset in range(len(raw))
                    if raw[offset] != projected[offset]
                }
                self.assertLessEqual(
                    differing, covered, "the projection changed a byte outside a digest"
                )

                for start in starts:
                    self.assertEqual(
                        self.PLACEHOLDER, projected[start : start + 64].decode("ascii")
                    )
                if not starts:
                    self.assertEqual(raw, projected)

    def edited_fixture(self, fixture: dict) -> tuple[dict, dict[str, bytes]]:
        """One bound source edited past its span, with the mechanical passes run.

        Returns the manifest as the passes leave it and the artefacts they
        rewrite. Nothing is written: the edit and every derived artefact are
        built in memory, so the bound documents in the repository are read and
        never touched.
        """
        source_record = fixture["source"]
        source = (ROOT / source_record["path"]).read_bytes()
        old = source_record["sha256"]
        self.assertEqual(old, hashlib.sha256(source).hexdigest())

        start = int(source_record["start"])
        end = int(source_record["end"])
        edited = source + self.OUT_OF_SPAN_EDIT
        self.assertEqual(
            source[start:end], edited[start:end], "the edit moved the reviewed span"
        )
        new = hashlib.sha256(edited).hexdigest()
        self.assertNotEqual(old, new)

        rewritten: dict[str, bytes] = {}
        for name in ("model", "source_spans"):
            record = fixture["artifacts"][name]
            raw = (ROOT / record["path"]).read_bytes()
            self.assertEqual(1, raw.count(old.encode("ascii")))
            rewritten[record["path"]] = raw.replace(
                old.encode("ascii"), new.encode("ascii")
            )
        model_path = fixture["artifacts"]["model"]["path"]
        rewritten[fixture["artifacts"]["compact"]["path"]] = AI.format_compact(
            AI.load_canonical_record(rewritten[model_path])
        )

        manifest = copy.deepcopy(self.manifest)
        entry = next(item for item in manifest["fixtures"] if item["id"] == fixture["id"])
        entry["source"]["sha256"] = new
        for name in ("model", "source_spans", "compact"):
            record = entry["artifacts"][name]
            record["sha256"] = hashlib.sha256(rewritten[record["path"]]).hexdigest()
        return manifest, rewritten

    def test_projection_is_unchanged_by_an_out_of_span_edit(self):
        """The property the whole design rests on, for all three bound sources.

        An edit appended past the reviewed span changes no measured byte: the
        span, its digest and every recorded binding offset stay where they
        were, and `evidence/measurement.json` records the span's byte count as
        the measured source. What it does change is the whole-file digest, and
        with it the three artefacts that embed it. Under the projection those
        three artefacts are identical before and after, so nothing the corpus
        would digest through it has moved.

        The comparison is between two byte strings shown to differ first, so
        this cannot pass by the projection returning its input.
        """
        measurement = AI.load_canonical_record(
            (ROOT / self.manifest["evidence"]["measurement_record"]["path"]).read_bytes(),
            allow_integers=True,
        )
        measured = {item["fixture_id"]: item["source"] for item in measurement["documents"]}

        for fixture in self.manifest["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                # What was measured is the reviewed span, not the whole file:
                # the recorded byte count is the span's length and the recorded
                # digest is the span digest. An out-of-span edit therefore
                # leaves every measured byte alone and moves only the digest
                # this projection neutralises.
                recorded = measured[fixture["id"]]
                span = fixture["source"]
                self.assertEqual(int(span["end"]) - int(span["start"]), recorded["bytes"])
                self.assertEqual(span["span_sha256"], recorded["sha256"])

                after_manifest, rewritten = self.edited_fixture(fixture)
                for path, edited in sorted(rewritten.items()):
                    with self.subTest(path=path):
                        committed = (ROOT / path).read_bytes()
                        self.assertNotEqual(
                            committed, edited, "the edit did not move the artefact"
                        )
                        self.assertEqual(
                            AI.digest_neutral_projection(self.manifest, committed),
                            AI.digest_neutral_projection(after_manifest, edited),
                        )

    def test_the_corpus_subject_still_carries_the_whole_file_source_digest(self):
        """This step adds the projection and does not switch the subject onto it.

        Both committed evidence records still agree with `_corpus_sha256` as it
        stands, which is why no file under `evidence/` changes here, and an
        out-of-span edit still moves that digest -- the refusal skills#1098
        reports is still exactly where step 1 pinned it.

        Step 3 is what inverts the second half of this case, together with the
        one `measure` and one `parity` run that reissue both records. Until
        then, a change that quietly moved the subject early would strand two
        evidence records this repository cannot honestly reissue on demand.
        """
        corpus = AI._corpus_sha256(self.manifest)
        for key in ("measurement_record", "parity_record"):
            with self.subTest(evidence=key):
                path = ROOT / self.manifest["evidence"][key]["path"]
                record = AI.load_canonical_record(path.read_bytes(), allow_integers=True)
                self.assertEqual(corpus, record["corpus_sha256"])

        for fixture in self.manifest["fixtures"]:
            with self.subTest(fixture=fixture["id"]):
                after_manifest, _ = self.edited_fixture(fixture)
                self.assertNotEqual(corpus, AI._corpus_sha256(after_manifest))


if __name__ == "__main__":
    unittest.main()
