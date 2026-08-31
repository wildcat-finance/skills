"""Scaffold and hostile-boundary tests for the Noema shadow prototype."""

from __future__ import annotations

import argparse
import contextlib
from concurrent.futures import ThreadPoolExecutor
import copy
from decimal import Decimal
from hashlib import sha256
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "noema.py"
SCHEMA = ROOT / "schemas" / "noema-v1.schema.json"
INVENTORY = ROOT / "tests" / "fixtures" / "noema-v1" / "seed-inventory.json"
STUDY = ROOT / "docs" / "noema" / "study.md"
RUNBOOK = ROOT / "docs" / "noema" / "runbook.md"
NOEMA_FIXTURES = ROOT / "tests" / "fixtures" / "noema-v1"
CODEC_FIXTURE = NOEMA_FIXTURES / "codec" / "complete.noe"
MODULES_FIXTURE = NOEMA_FIXTURES / "modules"
PROFILE_FIXTURE = NOEMA_FIXTURES / "profiles" / "ascii-baseline.json"
KERNEL_FIXTURE = NOEMA_FIXTURES / "profiles" / "kernel.noe"
CORE_DIGEST = "df97b7f39b31fcad8d75fe6d7079b12ee7c8326bd4ec1758a6577764ad1b6b76"
BOUND_SOURCE = NOEMA_FIXTURES / "codec" / "bound-source.txt"
SOURCE_DIGEST = "34a6411e347aa461190a71ceaa666418923ac947101c4d6db2f5e62f2b386dac"
RUNTIME_FIXTURE = NOEMA_FIXTURES / "runtime"
CORPUS_MANIFEST = NOEMA_FIXTURES / "manifest.json"
MEASUREMENT_PROFILES = NOEMA_FIXTURES / "profiles" / "measurement.json"
SPECIMEN_FIXTURES = NOEMA_FIXTURES / "specimens"
SEED_REFERENCE = NOEMA_FIXTURES / "seed-reference"
SPECIMEN_NAMES = ("brevitas", "fiat", "phylax", "sapheneia")


def load_noema():
    """Load the repository entrypoint without relying on import-path state."""
    spec = importlib.util.spec_from_file_location("noema_v1", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


noema = load_noema()


def scratch_directory(prefix="noema-"):
    """Return transient in-repository space below the ignored scratch root."""
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


def source_binding(start: int = 0, end: int = 1):
    return [
        "src",
        "tests/fixtures/noema-v1/codec/bound-source.txt",
        SOURCE_DIGEST,
        str(start),
        str(end),
    ]


def base_records(directive=None, *, literals=None, definitions=None):
    records = [["import", "core", CORE_DIGEST]]
    records.extend(literals or [])
    records.extend(definitions or [])
    records.append(
        [
            "rule",
            "rule.test",
            directive or ["+", ["core.ready", [":", "state", "ready"]]],
            source_binding(),
        ]
    )
    return records


def compile_records(records):
    raw = noema._canonical_source(records)
    return noema.compile_source(raw, MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)


def checked_fact(proposition, value="true", label="fact"):
    return {
        "id": noema.fact_id(proposition),
        "value": value,
        "evidence_sha256": sha256(label.encode()).hexdigest(),
    }


def runtime_selection(
    operation,
    *,
    state="blocked",
    target="repository",
    tools=(),
    authority=(),
    facts=(),
):
    return {
        "operation": operation,
        "state": state,
        "target": target,
        "tools": sorted(tools),
        "authority": sorted(authority),
        "facts": sorted(facts, key=lambda item: item["id"]),
    }


def select_records(records, selection):
    build, artifacts = compile_records(records)
    profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
    manifest, projection = noema.select_runtime(
        build,
        profile,
        sha256(artifacts["profile"]).hexdigest(),
        selection,
    )
    return build, manifest, projection


def runtime_fixture(selection_name="selection.json"):
    build, _raw, artifacts = noema.load_build(
        RUNTIME_FIXTURE / "build.json",
        RUNTIME_FIXTURE / "modules",
        RUNTIME_FIXTURE / "profile.json",
        RUNTIME_FIXTURE / "kernel.noe",
    )
    selection, _raw = noema._read_canonical_json(
        RUNTIME_FIXTURE / selection_name,
        "selection",
    )
    profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
    manifest, projection = noema.select_runtime(
        build,
        profile,
        sha256(artifacts["profile"]).hexdigest(),
        selection,
    )
    return build, selection, manifest, projection


def write_bytes(path: Path, payload: bytes) -> None:
    """Write one test-owned file below its disposable directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


@contextlib.contextmanager
def copied_corpus():
    """Yield one disposable copy of the complete Noema fixture tree."""
    with scratch_directory("noema-corpus-") as temporary:
        target = Path(temporary) / "noema-v1"
        shutil.copytree(NOEMA_FIXTURES, target)
        yield target


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_canonical_json(path: Path, value: object) -> None:
    write_bytes(path, noema._canonical_json(value))


FAKE_ADAPTER_SOURCE = b'''#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import time

raw = sys.stdin.buffer.read()
mode = os.environ.get("NOEMA_FAKE_MODE", "success")
sequence = os.environ.get("NOEMA_FAKE_SEQUENCE")
state_path = os.environ.get("NOEMA_FAKE_STATE")
if sequence and state_path:
    try:
        with open(state_path, "r", encoding="ascii") as state_file:
            sequence_index = int(state_file.read())
    except (FileNotFoundError, ValueError):
        sequence_index = 0
    with open(state_path, "w", encoding="ascii") as state_file:
        state_file.write(str(sequence_index + 1))
    sequence_modes = sequence.split(",")
    mode = sequence_modes[min(sequence_index, len(sequence_modes) - 1)]
if mode == "timeout":
    time.sleep(5)
if mode == "exit":
    raise SystemExit(7)
if mode == "stdout-cap":
    sys.stdout.write("x" * 100000)
    raise SystemExit(0)
if mode == "stderr-cap":
    sys.stderr.write("x" * 100000)
    raise SystemExit(0)
if mode == "malformed":
    sys.stdout.write("{")
    raise SystemExit(0)
if mode == "duplicate-json":
    sys.stdout.write('{"a":1,"a":2}\\n')
    raise SystemExit(0)
request = json.loads(raw)
request_digest = hashlib.sha256(raw).hexdigest()
prompt = request["prompt"].encode("utf-8")
response = {
    "answer_code": "NOE-OK",
    "answer_id": (os.environ.get("NOEMA_FAKE_ANSWER", "answer.fake")
                  if request["mode"] == "evaluation" else None),
    "cost_usd": "0.000001",
    "finish_reason": "stop",
    "generation_id": "generation." + request_digest[:24],
    "input_tokens": 7 if not prompt else 8 + len(prompt) // 4,
    "model": os.environ["NOEMA_FAKE_MODEL"],
    "output_tokens": 1,
    "provider": os.environ["NOEMA_FAKE_PROVIDER"],
    "request_sha256": request_digest,
    "schema": "noema-adapter-response/v1",
    "status": "recorded",
}
if mode == "unknown":
    response.update(answer_code="NOE-E-ADAPTER.REMOTE", answer_id=None,
                    cost_usd="0", finish_reason="unknown",
                    generation_id="unknown", input_tokens=0,
                    model="unknown", output_tokens=0, provider="unknown",
                    status="unknown")
elif mode == "policy-unknown":
    response.update(answer_code="NOE-E-ADAPTER.PROVIDER_POLICY", answer_id=None,
                    cost_usd="0", finish_reason="unknown",
                    generation_id="unknown", input_tokens=0,
                    model="unknown", output_tokens=0, provider="unknown",
                    status="unknown")
elif mode == "extra-field":
    response["extra"] = "x"
elif mode == "negative-count":
    response["input_tokens"] = -1
elif mode == "float-count":
    response["input_tokens"] = 1.5
elif mode == "bool-count":
    response["input_tokens"] = True
elif mode == "wrong-request":
    response["request_sha256"] = "0" * 64
elif mode == "wrong-model":
    response["model"] = "wrong/model"
elif mode == "wrong-provider":
    response["provider"] = "wrong-provider"
elif mode == "secret-answer":
    response["answer_id"] = "sk-or-v1-not-a-real-secret"
elif mode == "null-answer":
    response["answer_id"] = None
elif mode == "high-cost":
    response["cost_usd"] = "0.9"
elif mode == "invalid-code":
    response["answer_code"] = "looks-good"
elif mode == "invented-unknown":
    response.update(answer_code="NOE-E-ADAPTER.REMOTE", answer_id=None,
                    generation_id="unknown", model="unknown", provider="unknown",
                    status="unknown")
elif mode == "output-overrun":
    response["output_tokens"] = request["max_output_tokens"] + 1
encoded = json.dumps(response, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\\n"
if mode == "noncanonical":
    encoded = json.dumps(response, sort_keys=True) + "\\n"
sys.stdout.write(encoded)
'''


def fake_external_profile(
    executable: Path,
    *,
    identifier: str = "fake.openai",
    family: str = "openai",
    model: str = "fake/openai-current",
    provider: str = "fake-provider-openai",
    roles=("evaluation", "measurement"),
    mode: str = "success",
    answer: str = "answer.fake",
):
    role_values = sorted(roles)
    vocabulary = sha256(f"{family}-vocabulary".encode()).hexdigest()
    endpoint_model = model + "-20260830"
    acquisition = {
        "catalog_endpoint": f"https://openrouter.ai/api/v1/models/{model}/endpoints",
        "context_length": 131072,
        "endpoint_name": f"{provider} | {endpoint_model}",
        "endpoint_model": endpoint_model,
        "max_completion_tokens": 4096,
        "max_prompt_tokens": 126976,
        "model": model,
        "observed_on": "2026-08-30",
        "pricing": {
            "completion": "0.000001",
            "prompt": "0.000001",
            "request": "0",
        },
        "pricing_overrides": [],
        "provider": provider,
        "provider_tag": "fake/local",
        "quantization": "exact-test-double",
        "supported_parameters": ["max_tokens", "response_format", "seed", "structured_outputs"],
        "vocabulary_sha256": vocabulary,
    }
    return {
        "acquisition": acquisition,
        "acquisition_sha256": noema._value_sha256(acquisition),
        "adapter": "noema-process-json/v1",
        "argv": [],
        "context": {
            "examples": 0,
            "messages": 1,
            "mode": "fresh-process",
            "repository_instructions": 0,
            "tools": 0,
        },
        "endpoint": "local-process",
        "endpoint_model": acquisition["endpoint_model"],
        "environment_allowlist": [],
        "evaluation_output_tokens": 64,
        "evaluation_seed": 0 if "evaluation" in role_values else None,
        "executable": str(executable),
        "executable_sha256": sha256(executable.read_bytes()).hexdigest(),
        "family": family,
        "fixed_environment": {
            "NOEMA_FAKE_ANSWER": answer,
            "NOEMA_FAKE_MODE": mode,
            "NOEMA_FAKE_MODEL": model,
            "NOEMA_FAKE_PROVIDER": provider,
        },
        "id": identifier,
        "invocation_files": [],
        "max_stderr_bytes": 4096,
        "max_stdout_bytes": 4096,
        "max_token_parameter": "max_tokens",
        "measurement_output_tokens": 1,
        "model": model,
        "provider": provider,
        "provider_policy": {
            "allow_fallbacks": False,
            "data_collection": "deny",
            "max_price": {"completion": "1", "prompt": "1", "request": "0"},
            "only": [acquisition["provider_tag"]],
            "require_parameters": True,
            "zdr": True,
        },
        "roles": role_values,
        "schema": "noema-external-profile/v1",
        "timeout_seconds": 2,
        "tokenizer": model + "/provider-accounting",
        "tokenizer_identity": acquisition["endpoint_model"] + "/provider-accounting",
        "vocabulary_sha256": vocabulary,
        "vocabulary_status": "exact",
    }


def fake_profile_set(executable: Path):
    specifications = (
        ("fake.anthropic", "anthropic", "fake/claude-current", "fake-provider-anthropic", ("evaluation", "measurement")),
        ("fake.google", "google", "fake/gemini-current", "fake-provider-google", ("measurement",)),
        ("fake.open-weight", "open-weight", "fake/qwen-current", "fake-provider-open-weight", ("measurement",)),
        ("fake.openai", "openai", "fake/openai-current", "fake-provider-openai", ("evaluation", "measurement")),
    )
    return {
        "observed_on": "2026-08-30",
        "profiles": [
            fake_external_profile(
                executable,
                identifier=identifier,
                family=family,
                model=model,
                provider=provider,
                roles=roles,
            )
            for identifier, family, model, provider, roles in specifications
        ],
        "schema": "noema-external-profiles/v1",
    }


def valid_evaluation_answers(packet: dict[str, object], packet_raw: bytes):
    answers = []
    for family in packet["family_profiles"]:
        for case in packet["cases"]:
            for prompt in case["prompts"]:
                key = (
                    str(family["id"]),
                    str(case["id"]),
                    str(prompt["mode"]),
                    str(prompt["context_nonce"]),
                )
                invocation = next(
                    item["attempts"][0]
                    for item in prompt["requests"]
                    if item["family_id"] == family["id"]
                )
                answers.append(
                    {
                        "acquisition_sha256": family["acquisition_sha256"],
                        "answer_code": "NOE-OK",
                        "answer_id": case["required_answer_id"],
                        "case_id": case["id"],
                        "context_nonce": prompt["context_nonce"],
                        "family": family["family"],
                        "family_id": family["id"],
                        "id": "result."
                        + noema._correlation("evaluation-answer", *key),
                        "mode": prompt["mode"],
                        "model": family["model"],
                        "profile_sha256": family["profile_sha256"],
                        "prompt_sha256": prompt["sha256"],
                        "provider": family["provider"],
                        "provenance": {
                            "attempts": [
                                {
                                    "answer_code": "NOE-OK",
                                    "attempt": invocation["attempt"],
                                    "context_nonce": invocation["context_nonce"],
                                    "request_sha256": invocation["sha256"],
                                    "status": "recorded",
                                }
                            ],
                            "cost_usd": "0.000001",
                            "finish_reason": "stop",
                            "generation_id": "generation." + invocation["sha256"][:24],
                            "input_tokens": 1,
                            "output_tokens": 1,
                            "request_sha256": invocation["sha256"],
                        },
                        "status": "recorded",
                    }
                )
    return {
        "answers": answers,
        "case_set_sha256": packet["case_set_sha256"],
        "packet_sha256": sha256(packet_raw).hexdigest(),
        "profile_set_sha256": packet["profile_set_sha256"],
        "repository_tree": packet["repository_tree"],
        "schema": noema.EVALUATION_ANSWERS_SCHEMA,
        "summary": {
            "expected": len(answers),
            "recorded": len(answers),
            "status": "recorded",
            "unknown": 0,
        },
    }


def specimen_directory(name: str, root: Path = NOEMA_FIXTURES) -> Path:
    return root / "specimens" / name


def mutation_index(root: Path = NOEMA_FIXTURES):
    values = {}
    for name in SPECIMEN_NAMES:
        directory = specimen_directory(name, root)
        plan = read_json(directory / "mutation-plan.json")
        results = read_json(directory / "mutation-results.json")
        for planned, outcome in zip(
            plan["mutations"], results["results"], strict=True
        ):
            values[planned["category"]] = (planned, outcome)
    return values


def nested_proposition(wrappers):
    proposition = [
        "=",
        [":", "state", "ready"],
        [":", "state", "ready"],
    ]
    for _index in range(wrappers):
        proposition = ["~", proposition]
    return proposition


def assert_build_and_projection_round_trip(test, build, artifacts, modules):
    profile = noema._decode_json(
        artifacts["profile"],
        "profile",
        canonical=True,
    )
    with tempfile.TemporaryDirectory() as temporary:
        build_path = Path(temporary) / "build.json"
        write_bytes(build_path, artifacts["build"])
        actions = (
            (
                "build",
                lambda: noema.load_build(
                    build_path,
                    modules,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )[0],
                build,
            ),
            (
                "projection",
                lambda: noema.recover_projection(
                    noema.project_build(
                        build,
                        profile,
                        build["lock"]["profile_sha256"],
                    ),
                    profile,
                ),
                build["graph"],
            ),
        )
        for name, action, expected in actions:
            with test.subTest(name=name):
                try:
                    recovered = action()
                except noema.Refusal as raised:
                    test.fail(
                        f"maximum-depth {name} round trip refused: {raised.code}"
                    )
                test.assertEqual(recovered, expected)


def zip_info(name: str, kind: int = stat.S_IFREG, compression: int = zipfile.ZIP_DEFLATED):
    """Return one Unix-attributed ZipInfo for a hostile fixture."""
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.compress_type = compression
    permissions = 0o755 if kind == stat.S_IFDIR else 0o644
    info.external_attr = (kind | permissions) << 16
    if kind == stat.S_IFDIR:
        info.external_attr |= 0x10
    return info


def archive_bytes(
    files: list[tuple[str, bytes]],
    *,
    root: str = "seed/",
    include_root: bool = True,
    special: tuple[str, int, bytes] | None = None,
    compression: int = zipfile.ZIP_DEFLATED,
) -> bytes:
    """Build one bounded archive entirely in memory."""
    import io

    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        if include_root:
            archive.writestr(zip_info(root, stat.S_IFDIR, compression), b"")
        for name, payload in files:
            archive.writestr(zip_info(root + name, stat.S_IFREG, compression), payload)
        if special is not None:
            name, kind, payload = special
            archive.writestr(zip_info(root + name, kind, compression), payload)
    return output.getvalue()


def inventory_for(payload: bytes, files: list[tuple[str, bytes]], *, root: str = "seed/"):
    """Return the exact closed inventory for one synthetic archive."""
    return {
        "schema": noema.INVENTORY_SCHEMA,
        "archive": {
            "name": "noema-v0-evidence.zip",
            "url": "https://example.invalid/noema-v0-evidence.zip",
            "bytes": len(payload),
            "sha256": sha256(payload).hexdigest(),
            "root": root,
        },
        "files": [
            {
                "path": name,
                "bytes": len(content),
                "sha256": sha256(content).hexdigest(),
            }
            for name, content in sorted(files)
        ],
    }


def write_case(
    directory: Path,
    files: list[tuple[str, bytes]],
    *,
    payload: bytes | None = None,
    inventory: dict[str, object] | None = None,
    **archive_options,
) -> tuple[Path, Path]:
    """Write one archive/inventory pair and return both paths."""
    encoded = payload if payload is not None else archive_bytes(files, **archive_options)
    record = inventory if inventory is not None else inventory_for(
        encoded, files, root=archive_options.get("root", "seed/")
    )
    archive_path = directory / "seed.zip"
    inventory_path = directory / "inventory.json"
    write_bytes(archive_path, encoded)
    write_bytes(
        inventory_path,
        (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode(),
    )
    return archive_path, inventory_path


def refusal(archive_path: Path, inventory_path: Path) -> noema.Refusal:
    """Return the stable refusal for one invalid pair."""
    with unittest.TestCase().assertRaises(noema.Refusal) as raised:
        noema.verify_seed(archive_path, inventory_path)
    return raised.exception


class NoemaScaffoldTests(unittest.TestCase):
    def test_receipted_study_copy_is_exact(self):
        self.assertEqual(
            sha256(STUDY.read_bytes()).hexdigest(),
            "4a7c0e7bdfc3d44535d36d3666b3272436d1662463aabc6c82380bd554e5ffec",
        )

    def test_receipted_runbook_copy_is_exact(self):
        self.assertEqual(
            sha256(RUNBOOK.read_bytes()).hexdigest(),
            "266bd5fd197b9380ecad81111347be1fec55fa5f125481df6146565a2a99dfc4",
        )

    def test_repository_python_pin_is_exact(self):
        self.assertEqual((ROOT / ".python-version").read_text().strip(), "3.14.6")

    def test_schema_is_closed_and_names_all_record_families(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            set(schema), {"$schema", "$id", "title", "oneOf", "$defs"}
        )
        public_records = {
            "seedInventory", "module", "profile", "build", "projection",
            "semanticDiff", "lock", "manifest", "sliceProjection", "result",
            "evidence", "sourceIdentity", "sourceSpans", "literalSet",
            "questionSet", "answerSet", "mutationPlan", "mutationResults",
            "specimenCorpus", "externalProfiles", "measurement",
            "evaluationPacket", "evaluationAnswers", "evaluationReport",
            "corpusEvidence",
        }
        self.assertEqual(
            public_records,
            {reference["$ref"].rsplit("/", 1)[-1] for reference in schema["oneOf"]},
        )
        for name in public_records:
            self.assertFalse(schema["$defs"][name]["additionalProperties"])

    def test_schema_rejects_noncanonical_archive_member_paths(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        pattern = schema["$defs"]["relativePath"]["pattern"]
        for path in ("a/./b", "a//b", "a/"):
            with self.subTest(path=path):
                self.assertIsNone(re.fullmatch(pattern, path))

    def test_runtime_path_alphabets_match_the_published_schema(self):
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        self.assertEqual(
            noema.SEED_RELATIVE_PATH_RE.pattern,
            schema["$defs"]["relativePath"]["pattern"],
        )
        self.assertEqual(
            noema.SEED_ROOT_PATH_RE.pattern,
            schema["$defs"]["seedInventory"]["properties"]["archive"]
            ["properties"]["root"]["pattern"],
        )

    def test_schema_binds_each_specimen_id_to_its_canonical_source(self):
        source_identity = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"][
            "sourceIdentity"
        ]
        published = {
            branch["properties"]["id"]["const"]: branch["properties"]["path"]["const"]
            for branch in source_identity["oneOf"]
        }
        self.assertEqual(published, noema.SPECIMEN_SOURCE_PATHS)

    def test_schema_keeps_every_prototype_specimen_shadow_only(self):
        record = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"][
            "specimenRecord"
        ]["properties"]
        self.assertEqual(record["shadow"], {"const": True})
        self.assertEqual(record["unsupported_remainders"]["minimum"], 1)
        self.assertEqual(record["artifact_inventory_sha256"], {"$ref": "#/$defs/sha256"})

    def test_live_profile_set_is_closed_current_and_digest_bound(self):
        record, _raw, profiles = noema.load_external_profiles(
            MEASUREMENT_PROFILES,
            require_measurement_families=True,
            verify_files=False,
        )
        self.assertEqual(record["observed_on"], "2026-08-30")
        self.assertEqual(
            [profile["family"] for profile in profiles],
            ["anthropic", "google", "open-weight", "openai"],
        )
        self.assertEqual(
            [profile["roles"] for profile in profiles],
            [
                ["measurement"],
                ["evaluation", "measurement"],
                ["measurement"],
                ["evaluation", "measurement"],
            ],
        )
        self.assertEqual(
            [profile["evaluation_seed"] for profile in profiles],
            [None, 0, None, 0],
        )

    def test_schema_binds_mutation_assignments_and_critical_vectors(self):
        definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]
        published_assignments = {}
        for branch in definitions["mutationPlan"]["oneOf"]:
            properties = branch["properties"]
            specimen = properties["specimen"]["const"]
            published_assignments[specimen] = tuple(
                (
                    entry["properties"]["id"]["const"],
                    entry["properties"]["category"]["const"],
                )
                for entry in properties["mutations"]["prefixItems"]
            )
        expected_assignments = {
            specimen: tuple(
                (f"{specimen}.{category}", category) for category in categories
            )
            for specimen, categories in noema.SPECIMEN_MUTATION_CATEGORIES.items()
        }
        self.assertEqual(published_assignments, expected_assignments)
        published_vectors = {
            branch["properties"]["id"]["const"]: tuple(
                branch["properties"]["mutations"]["const"]
            )
            for branch in definitions["criticalVector"]["oneOf"]
        }
        self.assertEqual(published_vectors, noema.CRITICAL_MUTATION_IDS)

    def test_schema_closes_graph_tuple_shapes(self):
        definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]
        self.assertEqual(set(definitions["term"]), {"oneOf"})
        term_tags = set()
        call_branches = 0
        for branch in definitions["term"]["oneOf"]:
            head = branch["prefixItems"][0]
            if "const" in head:
                term_tags.add(head["const"])
            elif "enum" in head:
                term_tags.update(head["enum"])
            else:
                self.assertEqual(head, {"$ref": "#/$defs/qualifiedIdentifier"})
                call_branches += 1
        self.assertEqual(term_tags, set(noema.TERM_TAGS | noema.OPERATORS))
        self.assertEqual(call_branches, 1)
        source_records = {
            branch["prefixItems"][0]["const"]: branch
            for branch in definitions["sourceRecord"]["oneOf"]
        }
        expected_arities = {
            "import": 3,
            "literal": 5,
            "definition": 4,
            "rule": 4,
            "precedence": 6,
            "override": 7,
            "transition": 8,
            "promise": 11,
            "handoff": 11,
            "exception": 9,
        }
        for form, arity in expected_arities.items():
            with self.subTest(form=form):
                self.assertEqual(len(source_records[form]["prefixItems"]), arity)
                self.assertEqual(source_records[form]["minItems"], arity)
                self.assertEqual(source_records[form]["maxItems"], arity)
        for collection, item_ref in {
            "types": "#/$defs/typeDeclaration",
            "signatures": "#/$defs/signature",
            "definitions": "#/$defs/moduleDefinition",
        }.items():
            self.assertEqual(
                definitions["module"]["properties"][collection]["items"]["$ref"],
                item_ref,
            )
        self.assertEqual(
            definitions["profile"]["properties"]["reserved"],
            {"const": sorted(noema.RESERVED_SYMBOLS)},
        )
        self.assertEqual(
            definitions["identifier"]["not"], {"pattern": r"\.\."}
        )

    def test_schema_covers_every_emitted_result_dimension(self):
        definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]
        digest_dimensions = set(definitions["digestSet"]["properties"])
        count_dimensions = set(definitions["countSet"]["properties"])
        self.assertTrue(
            {"archive", "inventory", "source", "graph", "build", "profile",
             "projection", "manifest", "facts", "receipts", "output",
             "before", "after", "diff", "cases"} <= digest_dimensions
        )
        self.assertTrue(
            {"bytes", "members", "records", "modules", "aliases", "entries"}
            <= count_dimensions
        )

    def test_maximum_definition_refusal_field_fits_the_result_schema(self):
        name = "local." + "x" * 122
        records = base_records(
            definitions=[
                [
                    "definition",
                    name,
                    [],
                    ["=", [":", "actor", "x"], [":", "scope", "x"]],
                ]
            ]
        )
        try:
            compile_records(records)
        except noema.Refusal as raised:
            result = noema._result(
                "parse",
                "refuse",
                raised.code,
                field=raised.field,
                message=raised.message,
            )
        else:
            self.fail("unlike definition operands compiled")
        maximum = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"][
            "result"
        ]["properties"]["field"]["maxLength"]
        self.assertEqual(len(result["field"]), 144)
        self.assertLessEqual(len(result["field"]), maximum)

    def test_contract_magic_and_about_result_are_fixed(self):
        self.assertEqual((noema.CONTRACT, noema.SOURCE_MAGIC, noema.PROJECTION_MAGIC),
                         ("noema/v1", "NOE1", "NT1"))
        result = noema.about()
        self.assertEqual(result["schema"], "noema-result/v1")
        self.assertEqual(result["code"], "NOE-I-ABOUT")
        self.assertEqual(result["verdict"], "ok")
        self.assertRegex(result["correlation_id"], r"^[0-9a-f]{64}$")

    def test_public_contract_names_every_emitted_refusal_family(self):
        emitted = set(
            re.findall(
                r'''["'](NOE-E-[A-Z_]+)(?:\.[A-Z0-9_]+)?["']''',
                SCRIPT.read_text(encoding="utf-8"),
            )
        )
        declared = set(
            re.findall(
                r"\| `(NOE-E-[A-Z_]+)` \|",
                (ROOT / "docs" / "noema-v1.md").read_text(encoding="utf-8"),
            )
        )
        self.assertLessEqual(emitted, declared)

    def test_cli_help_names_only_scaffold_and_reserved_operations(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("verify-seed", completed.stdout)
        for command in noema.UNIMPLEMENTED:
            self.assertIn(command, completed.stdout)

    def test_every_reserved_operation_refuses_with_one_json_line(self):
        for command in noema.UNIMPLEMENTED:
            with self.subTest(command=command):
                completed = subprocess.run(
                    [sys.executable, str(SCRIPT), command],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(completed.returncode, 2)
                self.assertEqual(completed.stderr, "")
                self.assertEqual(len(completed.stdout.splitlines()), 1)
                result = json.loads(completed.stdout)
                self.assertEqual(result["code"], "NOE-E-UNIMPLEMENTED")
                self.assertEqual(result["command"], command)
                self.assertEqual(result["verdict"], "refuse")

    def test_malformed_cli_is_bounded_json_without_argument_echo(self):
        hostile = "x" * 200_000
        for arguments, expected_command in (
            (["about", hostile], "about"),
            ([hostile], "invalid"),
        ):
            with self.subTest(expected_command=expected_command):
                stdout = io.StringIO()
                stderr = io.StringIO()
                try:
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        status = noema.main(arguments)
                except SystemExit as error:
                    status = error.code
                self.assertEqual(status, 2)
                self.assertEqual(stderr.getvalue(), "")
                self.assertNotIn(hostile, stdout.getvalue())
                self.assertLess(len(stdout.getvalue().encode("utf-8")), 1_024)
                lines = stdout.getvalue().splitlines()
                self.assertEqual(len(lines), 1)
                result = json.loads(lines[0])
                self.assertEqual(result["command"], expected_command)
                self.assertEqual(result["code"], "NOE-E-TYPE.ARGUMENTS")
                self.assertEqual(result["verdict"], "refuse")

        commands = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]["result"]["properties"]["command"]["enum"]
        self.assertIn("invalid", commands)

    def test_committed_seed_inventory_has_exact_public_shape(self):
        inventory, raw = noema.load_inventory(INVENTORY)
        self.assertEqual(len(inventory["files"]), 17)
        self.assertEqual(inventory["archive"]["bytes"], 24_907)
        self.assertEqual(
            inventory["archive"]["sha256"],
            "1e1eb5e9908551f1337b7ec58a37ae7f37fd97e41d5ac424bc4992eb1d11b540",
        )
        self.assertEqual(sha256(raw).hexdigest(), sha256(INVENTORY.read_bytes()).hexdigest())

    def test_valid_synthetic_archive_verifies_without_extraction(self):
        files = [("a.txt", b"alpha\n"), ("nested.json", b"{}\n")]
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(Path(temporary), files)
            before = set(Path(temporary).iterdir())
            result = noema.verify_seed(archive_path, inventory_path)
            self.assertEqual(result["code"], "NOE-OK")
            self.assertEqual(result["counts"]["members"], 2)
            self.assertEqual(set(Path(temporary).iterdir()), before)

    def test_archive_byte_cap_refuses_before_zip_parsing(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive_path = directory / "oversized.zip"
            write_bytes(archive_path, b"z" * (noema.MAX_ARCHIVE_BYTES + 1))
            _, inventory_path = write_case(directory / "record", [("a", b"a")])
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.FILE")

    def test_member_count_cap_includes_the_root_directory(self):
        files = [(f"f{index:02}.txt", b"x") for index in range(noema.MAX_MEMBERS)]
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(Path(temporary), files)
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.MEMBERS")

    def test_inventory_rejects_one_member_above_its_byte_cap(self):
        files = [("a.txt", b"a")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["bytes"] = noema.MAX_MEMBER_BYTES + 1
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.INTEGER")

    def test_inventory_rejects_aggregate_member_bytes_above_cap(self):
        files = [("a", b"a"), ("b", b"b")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["bytes"] = 600_000
        record["files"][1]["bytes"] = 600_000
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-BOUNDS.TOTAL")

    def test_duplicate_archive_member_refuses(self):
        files = [("a.txt", b"alpha")]
        import io

        output = io.BytesIO()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(output, "w") as archive:
                archive.writestr(zip_info("seed/", stat.S_IFDIR), b"")
                archive.writestr(zip_info("seed/a.txt"), b"alpha")
                archive.writestr(zip_info("seed/a.txt"), b"alpha")
        payload = output.getvalue()
        record = inventory_for(payload, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-REFERENCE.DUPLICATE_MEMBER")

    def test_extra_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes(expected + [("extra.txt", b"extra")])
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-REFERENCE.EXTRA_MEMBER")

    def test_traversal_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes([("../escape", b"alpha")])
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.TRAVERSAL")

    def test_absolute_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes([], include_root=True)
        import io

        output = io.BytesIO()
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr(zip_info("seed/", stat.S_IFDIR), b"")
            archive.writestr(zip_info("/absolute.txt"), b"alpha")
        payload = output.getvalue()
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.ROOT")

    def test_backslash_archive_member_refuses(self):
        expected = [("a.txt", b"alpha")]
        payload = archive_bytes([("bad\\name", b"alpha")])
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.RELATIVE")

    def test_noncanonical_archive_member_path_refuses(self):
        for name in ("a/./b", "a//b"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                files = [(name, b"alpha")]
                archive_path, inventory_path = write_case(Path(temporary), files)
                error = refusal(archive_path, inventory_path)
                self.assertEqual(error.code, "NOE-E-PATH.RELATIVE")

    def test_noncanonical_archive_root_refuses(self):
        files = [("a.txt", b"alpha")]
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, root="seed//"
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.ROOT")

    def test_schema_invalid_archive_member_path_refuses(self):
        for name in ("a b", "C:policy"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                files = [(name, b"alpha")]
                archive_path, inventory_path = write_case(Path(temporary), files)
                error = refusal(archive_path, inventory_path)
                self.assertEqual(error.code, "NOE-E-PATH.RELATIVE")

    def test_schema_invalid_archive_root_refuses(self):
        files = [("a.txt", b"alpha")]
        for root in ("seed space/", "C:seed/"):
            with self.subTest(root=root), tempfile.TemporaryDirectory() as temporary:
                archive_path, inventory_path = write_case(
                    Path(temporary), files, root=root
                )
                error = refusal(archive_path, inventory_path)
                self.assertEqual(error.code, "NOE-E-PATH.ROOT")

    def test_descriptor_read_failure_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input"
            write_bytes(path, b"alpha")
            with mock.patch.object(
                noema.os, "read", side_effect=OSError("injected read fault")
            ), self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(path, "archive", 16)
            self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_descriptor_inspection_failure_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input"
            write_bytes(path, b"alpha")
            with mock.patch.object(
                noema.os, "fstat", side_effect=OSError("injected fstat fault")
            ), self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(path, "archive", 16)
            self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_descriptor_close_failure_refuses(self):
        real_close = os.close

        def close_then_fail(descriptor):
            real_close(descriptor)
            raise OSError("injected close fault")

        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "input"
            write_bytes(path, b"alpha")
            with mock.patch.object(
                noema.os, "close", side_effect=close_then_fail
            ), self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(path, "archive", 16)
            self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_symbolic_link_archive_member_refuses(self):
        expected = [("link", b"target")]
        payload = archive_bytes([], special=("link", stat.S_IFLNK, b"target"))
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.SPECIAL")

    def test_fifo_archive_member_refuses(self):
        expected = [("pipe", b"")]
        payload = archive_bytes([], special=("pipe", stat.S_IFIFO, b""))
        record = inventory_for(payload, expected)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), expected, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.SPECIAL")

    def test_unsupported_archive_compression_refuses(self):
        if not hasattr(zipfile, "ZIP_BZIP2"):
            self.skipTest("BZIP2 Zip support is unavailable")
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files, compression=zipfile.ZIP_BZIP2)
        record = inventory_for(payload, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.COMPRESSION")

    def test_corrupt_deflate_member_refuses(self):
        import io

        files = [("a.txt", b"alpha" * 8)]
        payload = bytearray(archive_bytes(files))
        with zipfile.ZipFile(io.BytesIO(payload), "r") as archive:
            info = archive.getinfo("seed/a.txt")
            compressed_start = (
                info.header_offset
                + 30
                + len(info.filename.encode("utf-8"))
                + len(info.extra)
            )
        payload[compressed_start] ^= 0x55
        corrupted = bytes(payload)
        record = inventory_for(corrupted, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=corrupted, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.ZIP")

    def test_archive_digest_mismatch_refuses_before_member_read(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["archive"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-DIGEST.ARCHIVE")

    def test_member_size_mismatch_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["bytes"] = 4
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-DIGEST.MEMBER_SIZE")

    def test_member_digest_mismatch_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["files"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-DIGEST.MEMBER")

    def test_missing_root_directory_entry_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files, include_root=False)
        record = inventory_for(payload, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-REFERENCE.ROOT")

    def test_duplicate_inventory_key_refuses(self):
        text = (
            '{"schema":"noema-seed-inventory/v1",'
            '"schema":"noema-seed-inventory/v1","archive":{},"files":[]}'
        )
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "inventory.json"
            write_bytes(path, text.encode())
            with self.assertRaises(noema.Refusal) as raised:
                noema.load_inventory(path)
            self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.DUPLICATE_KEY")

    def test_inventory_extra_key_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["extra"] = True
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-TYPE.KEYS")

    def test_lone_surrogate_inventory_string_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = archive_bytes(files)
        record = inventory_for(payload, files)
        record["archive"]["url"] = "https://example.invalid/\ud800"
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=payload, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.UNICODE")

    def test_invalid_utf8_archive_name_refuses(self):
        files = [("a.txt", b"alpha")]
        payload = bytearray(archive_bytes(files))
        local = payload.index(b"PK\x03\x04")
        central = payload.index(b"PK\x01\x02")
        for header, flag_offset, name_offset in (
            (local, 6, 30),
            (central, 8, 46),
        ):
            flags = int.from_bytes(payload[header + flag_offset:header + flag_offset + 2], "little")
            payload[header + flag_offset:header + flag_offset + 2] = (flags | 0x800).to_bytes(2, "little")
            payload[header + name_offset] = 0xFF
        malformed = bytes(payload)
        record = inventory_for(malformed, files)
        with tempfile.TemporaryDirectory() as temporary:
            archive_path, inventory_path = write_case(
                Path(temporary), files, payload=malformed, inventory=record
            )
            error = refusal(archive_path, inventory_path)
            self.assertEqual(error.code, "NOE-E-SYNTAX.ZIP")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_symbolic_link_archive_path_refuses(self):
        files = [("a.txt", b"alpha")]
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            archive_path, inventory_path = write_case(directory, files)
            linked = directory / "linked.zip"
            linked.symlink_to(archive_path)
            error = refusal(linked, inventory_path)
            self.assertEqual(error.code, "NOE-E-PATH.REGULAR")


class CanonicalSourceTests(unittest.TestCase):
    def test_checked_in_source_is_byte_identical_after_format(self):
        raw = CODEC_FIXTURE.read_bytes()
        build, artifacts = noema.compile_source(raw, MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        self.assertEqual(artifacts["source"], raw)
        self.assertEqual(noema._canonical_source(build["graph"]["records"]), raw)

    def test_noncanonical_json_spacing_refuses(self):
        raw = b'NOE1\n["import", "core","' + CORE_DIGEST.encode() + b'"]\n'
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(raw)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.CANONICAL")

    def test_missing_final_lf_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.FINAL_LF")

    def test_extra_final_lf_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1\n\n")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.LINES")

    def test_cr_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1\r\n")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.LINES")

    def test_wrong_magic_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE0\n")
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.MAGIC")

    def test_record_order_refuses(self):
        records = base_records()
        records.reverse()
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_duplicate_record_key_refuses(self):
        records = base_records()
        records.append(records[-1])
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_unknown_record_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records([["wat", "x"]])
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.RECORD")

    def test_duplicate_json_key_refuses(self):
        raw = b'NOE1\n{"x":1,"x":2}\n'
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(raw)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.DUPLICATE_KEY")

    def test_line_cap_accepts_exact_and_refuses_plus_one(self):
        exact_line = b'"' + b"a" * (noema.MAX_LINE_BYTES - 3) + b'"\n'
        self.assertEqual(len(exact_line), noema.MAX_LINE_BYTES)
        self.assertEqual(len(noema._parse_source_lines(b"NOE1\n" + exact_line)), 1)
        too_long = b'"' + b"a" * (noema.MAX_LINE_BYTES - 2) + b'"\n'
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(b"NOE1\n" + too_long)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.LINE")

    def test_input_cap_accepts_exact_and_refuses_plus_one(self):
        remaining = noema.MAX_INPUT_BYTES - len(b"NOE1\n")
        lines = []
        while remaining:
            size = min(noema.MAX_LINE_BYTES, remaining)
            if size < 3:
                take = 3 - size
                lines[-1] = lines[-1][:-take]
                remaining += take
                continue
            lines.append(b'"' + b"a" * (size - 3) + b'"\n')
            remaining -= size
        exact = b"NOE1\n" + b"".join(lines)
        self.assertEqual(len(exact), noema.MAX_INPUT_BYTES)
        noema._parse_source_lines(exact)
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(exact + b"0\n")
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.FILE")

    def test_record_cap_accepts_exact_and_refuses_plus_one(self):
        exact = b"NOE1\n" + b"[]\n" * noema.MAX_RECORDS
        self.assertEqual(len(noema._parse_source_lines(exact)), noema.MAX_RECORDS)
        with self.assertRaises(noema.Refusal) as raised:
            noema._parse_source_lines(exact + b"[]\n")
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.RECORDS")

    def test_literal_cap_accepts_exact_and_refuses_plus_one(self):
        value = "x" * noema.MAX_LITERAL_BYTES
        literal = ["literal", "lit.big", "text", str(noema.MAX_LITERAL_BYTES), value]
        compile_records(base_records(literals=[literal]))
        literal[4] += "x"
        literal[3] = str(noema.MAX_LITERAL_BYTES + 1)
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(literals=[literal]))
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.STRING")

    def test_literal_aggregate_cap_accepts_exact_and_refuses_plus_one(self):
        sizes = [65_000] * 12 + [6_432]
        literals = [
            ["literal", f"lit.{index:02d}", "text", str(size), "x" * size]
            for index, size in enumerate(sizes)
        ]
        compile_records(base_records(literals=literals))
        literals[-1][3] = "6433"
        literals[-1][4] += "x"
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(literals=literals))
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.LITERAL_TOTAL")

    def test_import_cap_accepts_exact_and_refuses_plus_one(self):
        exact = [["import", f"m{index:02d}", "0" * 64] for index in range(noema.MAX_IMPORTS)]
        imports, _definitions = noema._preflight_records(exact)
        self.assertEqual(len(imports), noema.MAX_IMPORTS)
        extra = exact + [["import", "mz", "0" * 64]]
        with self.assertRaises(noema.Refusal) as raised:
            noema._preflight_records(extra)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.IMPORTS")

    def test_finite_set_cap_accepts_exact_and_refuses_plus_one(self):
        literals = [
            ["literal", f"n{index:04d}", "number", "1", "1"]
            for index in range(noema.MAX_SET_MEMBERS + 1)
        ]
        members = [["$", f"n{index:04d}"] for index in range(noema.MAX_SET_MEMBERS)]
        quantified = ["all", ["x", "value"], ["{}", "value", *members], ["=", ["%", "x"], ["$", "n0000"]]]
        compile_records(base_records(["+", quantified], literals=literals[:-1]))
        quantified[2].append(["$", f"n{noema.MAX_SET_MEMBERS:04d}"])
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["+", quantified], literals=literals))
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.SET")

    def test_very_long_decimal_never_enters_integer_conversion(self):
        literal = ["literal", "n", "number", "65000", "9" * 65_000]
        compile_records(base_records(literals=[literal]))


class GraphValidationTests(unittest.TestCase):
    def test_source_alias_uses_stable_file_identity_not_mutable_metadata(self):
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "a",
                ["+", [":", "effect", "x"]],
                ["src", "a.txt", sha256(b"a").hexdigest(), "0", "1"],
            ],
            [
                "rule",
                "b",
                ["+", [":", "effect", "y"]],
                ["src", "b.txt", sha256(b"b").hexdigest(), "0", "1"],
            ],
        ]
        mode = stat.S_IFREG | 0o644
        observations = {
            "a.txt": (b"a", (1, 2, mode, 1, 10, 10)),
            "b.txt": (b"b", (1, 2, mode, 1, 20, 20)),
        }

        def same_inode_different_observation(_root, relative, _field, _limit):
            return observations[relative]

        with mock.patch.object(
            noema,
            "_read_repository_regular",
            side_effect=same_inode_different_observation,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.SOURCE_ALIAS")

    def test_macro_expansion_counts_repeated_parameter_substitution(self):
        self.assertEqual(4 * (2**14), noema.MAX_EXPANDED_NODES)
        definitions = [
            [
                "definition",
                "local.dup",
                [["x", "proposition"]],
                ["&", ["%", "x"], ["%", "x"]],
            ]
        ]

        def expanded(levels):
            proposition = [
                "=",
                [":", "state", "ready"],
                [":", "state", "ready"],
            ]
            for _index in range(levels):
                proposition = ["local.dup", proposition]
            return proposition

        compile_records(
            base_records(["+", expanded(14)], definitions=definitions)
        )
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(
                base_records(
                    ["+", ["~", expanded(14)]],
                    definitions=definitions,
                )
            )
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_maximum_depth_source_build_and_projection_round_trip(self):
        records = base_records(
            ["+", nested_proposition(noema.MAX_DEPTH - 5)]
        )
        build, artifacts = compile_records(records)
        assert_build_and_projection_round_trip(
            self,
            build,
            artifacts,
            MODULES_FIXTURE,
        )

        with self.assertRaises(noema.Refusal) as raised:
            compile_records(
                base_records(
                    ["+", nested_proposition(noema.MAX_DEPTH - 4)]
                )
            )
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.DEPTH")

    def test_container_record_and_term_tags_refuse_without_raw_type_errors(self):
        cases = (
            ([[[]]], "NOE-E-TYPE.RECORD"),
            (
                base_records(
                    definitions=[["definition", "local.bad", [], [[]]]]
                ),
                "NOE-E-TYPE.TERM",
            ),
        )
        for records, code in cases:
            with self.subTest(code=code):
                try:
                    compile_records(records)
                except noema.Refusal as raised:
                    self.assertEqual(raised.code, code)
                except TypeError:
                    self.fail("container tag escaped the refusal channel")
                else:
                    self.fail("container tag compiled")

    def test_structural_results_cannot_be_minted_by_typed_atoms(self):
        for directive in (
            [":", "directive", "anything"],
            ["+", [":", "proposition", "anything"]],
            ["+", ["=", [":", "relation", "anything"], [":", "relation", "anything"]]],
        ):
            with self.subTest(directive=directive):
                try:
                    compile_records(base_records(directive))
                except noema.Refusal as raised:
                    self.assertEqual(raised.code, "NOE-E-TYPE.STRUCTURAL_ATOM")
                else:
                    self.fail("typed atom minted a structural result")

    def test_source_bindings_require_utf8_and_scalar_boundaries(self):
        modules = noema._load_modules(MODULES_FIXTURE, [("core", CORE_DIGEST)])
        for payload, end, code in (
            (b"\xff", 1, "NOE-E-SYNTAX.SOURCE_UTF8"),
            ("é".encode("utf-8"), 1, "NOE-E-REFERENCE.SPAN_UTF8"),
        ):
            records = base_records()
            records[-1][3][2] = sha256(payload).hexdigest()
            records[-1][3][4] = str(end)
            source = noema._canonical_source(records)
            with self.subTest(payload=payload):
                with mock.patch.object(
                    noema, "_read_regular", return_value=payload
                ), mock.patch.object(
                    noema,
                    "_read_repository_regular",
                    return_value=(payload, (1, 1)),
                    create=True,
                ), self.assertRaises(noema.Refusal) as raised:
                    noema._compile_records(records, modules, source)
                self.assertEqual(raised.exception.code, code)

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_source_binding_refuses_a_linked_ancestor(self):
        with scratch_directory(
            prefix="noema-source-"
        ) as inside, tempfile.TemporaryDirectory(prefix="noema-outside-") as outside:
            inside_path = Path(inside)
            payload = b"x"
            (Path(outside) / "payload.txt").write_bytes(payload)
            (inside_path / "escape").symlink_to(outside, target_is_directory=True)
            relative = (
                inside_path.relative_to(ROOT) / "escape" / "payload.txt"
            ).as_posix()
            records = base_records()
            records[-1][3] = [
                "src",
                relative,
                sha256(payload).hexdigest(),
                "0",
                "1",
            ]
            modules = noema._load_modules(MODULES_FIXTURE, [("core", CORE_DIGEST)])
            with self.assertRaises(noema.Refusal) as raised:
                noema._compile_records(
                    records,
                    modules,
                    noema._canonical_source(records),
                )
            self.assertEqual(raised.exception.code, "NOE-E-PATH.CONFINEMENT")

    def test_finite_set_members_are_unique_and_canonically_ordered(self):
        duplicate = ["+", ["in", [":", "actor", "a"], ["{}", "actor", [":", "actor", "a"], [":", "actor", "a"]]]]
        reversed_members = ["+", ["in", [":", "actor", "a"], ["{}", "actor", [":", "actor", "b"], [":", "actor", "a"]]]]
        for directive in (duplicate, reversed_members):
            with self.subTest(directive=directive):
                with self.assertRaises(noema.Refusal) as raised:
                    compile_records(base_records(directive))
                self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.SET_ORDER")

    def test_unknown_operator_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["wat", [":", "state", "ready"]]))
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.OPERATOR")

    def test_wrong_arity_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["+", [":", "effect", "x"], [":", "effect", "y"]]))
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.ARITY")

    def test_type_mismatch_refuses(self):
        directive = ["@", [":", "actor", "alice"], ["+", [":", "effect", "x"]]]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(directive))
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.MISMATCH")

    def test_unresolved_literal_refuses(self):
        directive = ["+", ["core.invokes", [":", "effect", "x"], ["$", "absent"]]]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(directive))
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.LITERAL")

    def test_unresolved_predicate_refuses(self):
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(["+", ["core.absent"]]))
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.PREDICATE")

    def test_definition_cycle_refuses(self):
        definitions = [
            ["definition", "local.a", [], ["local.b"]],
            ["definition", "local.b", [], ["local.a"]],
        ]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(base_records(definitions=definitions))
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.DEFINITION_CYCLE")

    def test_precedence_cycle_refuses(self):
        records = [["import", "core", CORE_DIGEST]]
        records.extend(
            [
                ["rule", "a", ["+", [":", "effect", "x"]], source_binding(0, 1)],
                ["rule", "b", ["+", [":", "effect", "y"]], source_binding(1, 2)],
                ["precedence", "a", "b", [":", "actor", "x"], [":", "scope", "x"], [":", "evidence", "x"]],
                ["precedence", "b", "a", [":", "actor", "x"], [":", "scope", "x"], [":", "evidence", "x"]],
            ]
        )
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.RELATION_CYCLE")

    def test_override_and_mixed_relation_cycles_refuse(self):
        actor = [":", "actor", "x"]
        scope = [":", "scope", "x"]
        evidence = [":", "evidence", "x"]
        prefix = [
            ["import", "core", CORE_DIGEST],
            ["rule", "a", ["+", [":", "effect", "x"]], source_binding(0, 1)],
            ["rule", "b", ["+", [":", "effect", "y"]], source_binding(1, 2)],
        ]
        for relations in (
            [
                ["override", "o1", actor, "a", "b", scope, evidence],
                ["override", "o2", actor, "b", "a", scope, evidence],
            ],
            [
                ["precedence", "a", "b", actor, scope, evidence],
                ["override", "o1", actor, "b", "a", scope, evidence],
            ],
        ):
            with self.subTest(relations=relations):
                try:
                    compile_records(prefix + relations)
                except noema.Refusal as raised:
                    self.assertEqual(
                        raised.code,
                        "NOE-E-REFERENCE.RELATION_CYCLE",
                    )
                else:
                    self.fail("cyclic governing relation compiled")

    def test_long_acyclic_definition_chain_does_not_recurse(self):
        count = 1_200
        definitions = [
            ["definition", f"local.d{index:04d}", [], [f"local.d{index + 1:04d}"]]
            for index in range(count - 1)
        ]
        definitions.append(
            ["definition", f"local.d{count - 1:04d}", [], [":", "effect", "x"]]
        )
        try:
            compile_records(
                base_records(["+", ["local.d0000"]], definitions=definitions)
            )
        except RecursionError:
            self.fail("acyclic definition chain reached the interpreter recursion limit")

    def test_long_acyclic_precedence_chain_does_not_recurse(self):
        count = 1_500
        source_digest = sha256(SCRIPT.read_bytes()).hexdigest()
        records = [["import", "core", CORE_DIGEST]]
        records.extend(
            [
                [
                    "rule",
                    f"r{index:04d}",
                    ["+", [":", "effect", "x"]],
                    ["src", "scripts/noema.py", source_digest, str(index), str(index + 1)],
                ]
                for index in range(count)
            ]
        )
        records.extend(
            [
                [
                    "precedence",
                    f"r{index:04d}",
                    f"r{index + 1:04d}",
                    [":", "actor", "x"],
                    [":", "scope", "x"],
                    [":", "evidence", "x"],
                ]
                for index in range(count - 1)
            ]
        )
        try:
            compile_records(records)
        except RecursionError:
            self.fail("acyclic precedence chain reached the interpreter recursion limit")

    def test_overlapping_source_spans_refuse(self):
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "a", ["+", [":", "effect", "x"]], source_binding(0, 2)],
            ["rule", "b", ["+", [":", "effect", "y"]], source_binding(1, 3)],
        ]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.SPAN")

    def test_graph_node_budget_refuses_limit_plus_one(self):
        budget = noema._Budget()
        for _index in range(noema.MAX_GRAPH_NODES):
            budget.node("test")
        with self.assertRaises(noema.Refusal) as raised:
            budget.node("test")
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.NODES")


class ModuleLockTests(unittest.TestCase):
    @staticmethod
    def module_bytes(
        module_id,
        *,
        imports=None,
        types=None,
        signatures=None,
        definitions=None,
    ):
        return noema._canonical_json(
            {
                "schema": "noema-module/v1",
                "id": module_id,
                "imports": imports or [],
                "types": types or [],
                "signatures": signatures or [],
                "definitions": definitions or [],
            }
        )

    def _module_chain(self, directory, count):
        child = None
        child_digest = None
        root_digest = None
        for index in reversed(range(count)):
            module_id = f"m{index:02d}"
            value = {
                "schema": noema.MODULE_SCHEMA,
                "id": module_id,
                "imports": [] if child is None else [[child, child_digest]],
                "types": [],
                "signatures": [],
                "definitions": [],
            }
            raw = noema._canonical_json(value)
            (directory / f"{module_id}.json").write_bytes(raw)
            child = module_id
            child_digest = sha256(raw).hexdigest()
            root_digest = child_digest
        return root_digest

    def _signature_module(self, directory, count):
        value = {
            "schema": noema.MODULE_SCHEMA,
            "id": "m",
            "imports": [],
            "types": [],
            "signatures": [
                [f"m.p{index:05d}", [], "value"] for index in range(count)
            ],
            "definitions": [],
        }
        raw = noema._canonical_json(value)
        (directory / "m.json").write_bytes(raw)
        return sha256(raw).hexdigest()

    def test_maximum_depth_module_build_and_projection_round_trip(self):
        def module_at(wrappers):
            return self.module_bytes(
                "m",
                definitions=[["m.deep", [], nested_proposition(wrappers)]],
            )

        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            module = module_at(noema.MAX_DEPTH - 6)
            write_bytes(directory / "m.json", module)
            records = [
                ["import", "m", sha256(module).hexdigest()],
                ["rule", "rule.test", ["+", ["m.deep"]], source_binding()],
            ]
            build, artifacts = noema.compile_source(
                noema._canonical_source(records),
                directory,
                PROFILE_FIXTURE,
                KERNEL_FIXTURE,
            )
            assert_build_and_projection_round_trip(
                self,
                build,
                artifacts,
                directory,
            )

            too_deep = module_at(noema.MAX_DEPTH - 5)
            write_bytes(directory / "m.json", too_deep)
            too_deep_records = [
                ["import", "m", sha256(too_deep).hexdigest()],
                ["rule", "rule.test", ["+", ["m.deep"]], source_binding()],
            ]
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(
                    noema._canonical_source(too_deep_records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.DEPTH")

    def test_lock_binds_every_dependency_byte_string(self):
        build, artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        lock = build["lock"]
        self.assertEqual(lock["source_sha256"], sha256(artifacts["source"]).hexdigest())
        self.assertEqual(lock["graph_sha256"], sha256(artifacts["graph"]).hexdigest())
        self.assertEqual(lock["kernel_sha256"], sha256(KERNEL_FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(lock["profile_sha256"], sha256(PROFILE_FIXTURE.read_bytes()).hexdigest())
        self.assertEqual(lock["modules"], [{"id": "core", "sha256": CORE_DIGEST}])

    def test_stale_module_digest_refuses(self):
        records = base_records()
        records[0][2] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MODULE")

    def test_absent_module_refuses(self):
        records = [["import", "absent", "0" * 64]]
        with self.assertRaises(noema.Refusal) as raised:
            compile_records(records)
        self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_ambient_module_file_is_not_loaded(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "core.json").write_bytes((MODULES_FIXTURE / "core.json").read_bytes())
            (directory / "ambient.json").write_text("not json\n")
            raw = noema._canonical_source(base_records())
            build, _artifacts = noema.compile_source(raw, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual([item["id"] for item in build["graph"]["modules"]], ["core"])

    def test_module_symbol_requires_its_declared_import_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            child = self.module_bytes(
                "b",
                signatures=[["b.pred", [], "proposition"]],
            )
            child_digest = sha256(child).hexdigest()
            parent = self.module_bytes(
                "a",
                definitions=[["a.ready", [], ["b.pred"]]],
            )
            write_bytes(directory / "a.json", parent)
            write_bytes(directory / "b.json", child)
            records = [
                ["import", "a", sha256(parent).hexdigest()],
                ["import", "b", child_digest],
                ["rule", "rule.test", ["+", ["a.ready"]], source_binding()],
            ]
            try:
                noema.compile_source(
                    noema._canonical_source(records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            except noema.Refusal as raised:
                self.assertEqual(
                    raised.code,
                    "NOE-E-REFERENCE.MODULE_AMBIENT",
                )
            else:
                self.fail("module used a source co-import as an ambient dependency")

            parent = self.module_bytes(
                "a",
                imports=[["b", child_digest]],
                definitions=[["a.ready", [], ["b.pred"]]],
            )
            write_bytes(directory / "a.json", parent)
            records[0][2] = sha256(parent).hexdigest()
            build, _artifacts = noema.compile_source(
                noema._canonical_source(records),
                directory,
                PROFILE_FIXTURE,
                KERNEL_FIXTURE,
            )
            self.assertEqual(
                [item["id"] for item in build["graph"]["modules"]],
                ["a", "b"],
            )

    def test_module_definition_cannot_bind_a_source_local_definition(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            module = self.module_bytes(
                "a",
                definitions=[["a.ready", [], ["local.helper"]]],
            )
            write_bytes(directory / "a.json", module)
            records = [
                ["import", "a", sha256(module).hexdigest()],
                [
                    "definition",
                    "local.helper",
                    [],
                    ["=", [":", "state", "ready"], [":", "state", "ready"]],
                ],
                ["rule", "rule.test", ["+", ["a.ready"]], source_binding()],
            ]
            try:
                noema.compile_source(
                    noema._canonical_source(records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            except noema.Refusal as raised:
                self.assertEqual(
                    raised.code,
                    "NOE-E-REFERENCE.MODULE_AMBIENT",
                )
            else:
                self.fail("module bound a source-local definition")

    def test_module_cannot_capture_the_source_local_namespace(self):
        for module_id in ("local", "local.vendor"):
            with self.subTest(module_id=module_id), tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                module = self.module_bytes(
                    module_id,
                    definitions=[
                        [
                            f"{module_id}.ready",
                            [],
                            ["=", [":", "state", "ready"], [":", "state", "ready"]],
                        ]
                    ],
                )
                write_bytes(directory / f"{module_id}.json", module)
                records = [
                    ["import", module_id, sha256(module).hexdigest()],
                    [
                        "rule",
                        "rule.test",
                        ["+", [f"{module_id}.ready"]],
                        source_binding(),
                    ],
                ]
                try:
                    noema.compile_source(
                        noema._canonical_source(records),
                        directory,
                        PROFILE_FIXTURE,
                        KERNEL_FIXTURE,
                    )
                except noema.Refusal as raised:
                    self.assertEqual(
                        raised.code,
                        "NOE-E-REFERENCE.MODULE_NAMESPACE",
                    )
                else:
                    self.fail("module captured the source-local namespace")

    def test_module_signature_cannot_construct_a_directive(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            module = self.module_bytes(
                "m",
                signatures=[["m.make", [], "directive"]],
            )
            write_bytes(directory / "m.json", module)
            records = [
                ["import", "m", sha256(module).hexdigest()],
                ["rule", "rule.test", ["m.make"], source_binding()],
            ]
            try:
                noema.compile_source(
                    noema._canonical_source(records),
                    directory,
                    PROFILE_FIXTURE,
                    KERNEL_FIXTURE,
                )
            except noema.Refusal as raised:
                self.assertEqual(raised.code, "NOE-E-TYPE.SIGNATURE_RESULT")
            else:
                self.fail("module signature constructed a directive")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_linked_module_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "core.json").symlink_to(MODULES_FIXTURE / "core.json")
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(noema._canonical_source(base_records()), directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_module_directory_cannot_be_replaced_after_confinement_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "modules"
            displaced = root / "modules-displaced"
            directory.mkdir()
            shutil.copy2(MODULES_FIXTURE / "core.json", directory / "core.json")
            original = noema._read_directory_regular
            swapped = False

            def replace_before_read(descriptor, leaf, field, limit):
                nonlocal swapped
                if not swapped and leaf == "core.json" and field == "module.core":
                    directory.rename(displaced)
                    directory.symlink_to(MODULES_FIXTURE, target_is_directory=True)
                    swapped = True
                return original(descriptor, leaf, field, limit)

            with mock.patch.object(
                noema,
                "_read_directory_regular",
                side_effect=replace_before_read,
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    noema.compile_source(
                        noema._canonical_source(base_records()),
                        directory,
                        PROFILE_FIXTURE,
                        KERNEL_FIXTURE,
                    )
            self.assertTrue(swapped)
            self.assertIn(
                raised.exception.code,
                {
                    "NOE-E-IO.CHANGED",
                    "NOE-E-IO.READ",
                    "NOE-E-PATH.CONFINEMENT",
                    "NOE-E-PATH.IDENTITY",
                },
            )

    def test_stale_build_lock_refuses(self):
        build, _artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        build["lock"]["compiler_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._verify_build_value(build, MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.BUILD")

    def test_kernel_profile_mismatch_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            kernel = Path(temporary) / "kernel"
            kernel.write_text("different\n")
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, kernel)
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.KERNEL")

    def test_transitive_module_cap_accepts_exact_and_refuses_plus_one(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._module_chain(directory, noema.MAX_IMPORTS)
            source = noema._canonical_source([["import", "m00", digest]])
            build, _artifacts = noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(len(build["graph"]["modules"]), noema.MAX_IMPORTS)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._module_chain(directory, noema.MAX_IMPORTS + 1)
            source = noema._canonical_source([["import", "m00", digest]])
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.IMPORTS")

    def test_module_declarations_consume_the_graph_node_budget(self):
        exact_signatures = noema.MAX_GRAPH_NODES - 2
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._signature_module(directory, exact_signatures)
            source = noema._canonical_source([["import", "m", digest]])
            noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            digest = self._signature_module(directory, exact_signatures + 1)
            source = noema._canonical_source([["import", "m", digest]])
            with self.assertRaises(noema.Refusal) as raised:
                noema.compile_source(source, directory, PROFILE_FIXTURE, KERNEL_FIXTURE)
            self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.NODES")


class ProjectionTests(unittest.TestCase):
    def setUp(self):
        self.build, self.artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)
        self.profile = noema._decode_json(PROFILE_FIXTURE.read_bytes(), "profile", canonical=True)
        self.profile_digest = sha256(PROFILE_FIXTURE.read_bytes()).hexdigest()

    def test_projection_recovers_exact_graph(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        self.assertEqual(noema.recover_projection(bundle, self.profile), self.build["graph"])

    def test_projection_text_is_idempotent(self):
        first = noema.project_build(self.build, self.profile, self.profile_digest)
        second = noema.project_build(self.build, self.profile, self.profile_digest)
        self.assertEqual(noema._canonical_json(first), noema._canonical_json(second))

    def test_alias_collision_with_visible_literal_refuses(self):
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"][0][1] = "operator"
        with self.assertRaises(noema.Refusal) as raised:
            noema.project_build(self.build, profile, self.profile_digest)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.COLLISION")

    def test_alias_collision_by_arity_still_refuses(self):
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"][1][1] = profile["aliases"][0][1]
        with self.assertRaises(noema.Refusal) as raised:
            noema.project_build(self.build, profile, self.profile_digest)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.COLLISION")

    def test_alias_cannot_overload_predicate_and_literal_id(self):
        literal = ["literal", "core.ready", "text", "1", "x"]
        build, _artifacts = compile_records(base_records(literals=[literal]))
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"].insert(4, ["core.ready", "q"])
        profile_digest = sha256(noema._canonical_json(profile)).hexdigest()
        build["lock"]["profile_sha256"] = profile_digest
        with self.assertRaises(noema.Refusal) as raised:
            noema.project_build(build, profile, profile_digest)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.OVERLOAD")

    def test_unused_alias_is_inert(self):
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"].append(["zz.absent", "Z"])
        profile_digest = sha256(noema._canonical_json(profile)).hexdigest()
        build = json.loads(json.dumps(self.build))
        build["lock"]["profile_sha256"] = profile_digest
        bundle = noema.project_build(build, profile, profile_digest)
        self.assertEqual(noema.recover_projection(bundle, profile), build["graph"])

    def test_tampered_projection_refuses(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        bundle["text"] = bundle["text"].replace("NT1", "NT0", 1)
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, self.profile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROJECTION")

    def test_manifest_profile_mismatch_refuses(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        bundle["manifest"]["profile_sha256"] = "0" * 64
        bundle["lock"]["profile_sha256"] = "0" * 64
        bundle["manifest"]["lock_sha256"] = sha256(noema._canonical_json(bundle["lock"])).hexdigest()
        bundle["manifest"]["projection_sha256"] = sha256(bundle["text"].encode()).hexdigest()
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, self.profile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROFILE")

    def test_manifest_lock_mismatch_refuses(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        bundle["manifest"]["lock_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, self.profile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.LOCK")

    def test_recovery_normalizes_malformed_alias_shape(self):
        bundle = noema.project_build(self.build, self.profile, self.profile_digest)
        profile = json.loads(json.dumps(self.profile))
        profile["aliases"] = [[]]
        profile_digest = sha256(noema._canonical_json(profile)).hexdigest()
        bundle["lock"]["profile_sha256"] = profile_digest
        bundle["manifest"]["profile_sha256"] = profile_digest
        bundle["manifest"]["aliases_sha256"] = sha256(noema._canonical_json(profile["aliases"])).hexdigest()
        bundle["manifest"]["lock_sha256"] = sha256(noema._canonical_json(bundle["lock"])).hexdigest()
        header, graph, _empty = bundle["text"].split("\n")
        _magic, _old_profile, graph_digest = header.split(" ")
        bundle["text"] = f"NT1 {profile_digest} {graph_digest}\n{graph}\n"
        bundle["manifest"]["projection_sha256"] = sha256(bundle["text"].encode()).hexdigest()
        with self.assertRaises(noema.Refusal) as raised:
            noema.recover_projection(bundle, profile)
        self.assertEqual(raised.exception.code, "NOE-E-ALIAS.SHAPE")


class SemanticDiffTests(unittest.TestCase):
    def setUp(self):
        self.build, _artifacts = noema.compile_source(CODEC_FIXTURE.read_bytes(), MODULES_FIXTURE, PROFILE_FIXTURE, KERNEL_FIXTURE)

    def test_noop_diff_has_no_entries(self):
        self.assertEqual(noema.semantic_diff(self.build, self.build)["entries"], [])

    def test_effect_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[4][2] = ["-", ["core.ready", [":", "state", "ready"]]]
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("effect", kinds)

    def test_exception_subject_change_is_named_as_an_effect(self):
        exception = [
            "exception",
            "exception.test",
            [":", "actor", "alice"],
            ["=", [":", "state", "ready"], [":", "state", "ready"]],
            [":", "effect", "old"],
            [":", "scope", "repository"],
            [":", "evidence", "record"],
            [":", "value", "never"],
            ["-", [":", "effect", "recovery"]],
        ]
        records = base_records() + [exception]
        before, _artifacts = compile_records(records)
        changed_records = json.loads(json.dumps(records))
        changed_records[-1][4][2] = "new"
        after, _artifacts = compile_records(changed_records)
        kinds = {
            entry["kind"]
            for entry in noema.semantic_diff(before, after)["entries"]
        }
        self.assertIn("effect", kinds)

    def test_source_binding_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[4][3][4] = "9"
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("source_binding", kinds)

    def test_literal_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[1][3:] = ["11", "git status!"]
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("literal", kinds)

    def test_precedence_change_is_named(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[-1][3] = [":", "actor", "alternate"]
        changed, _artifacts = compile_records(records)
        kinds = {entry["kind"] for entry in noema.semantic_diff(self.build, changed)["entries"]}
        self.assertIn("authority", kinds)

    def test_diff_entries_are_closed_and_digest_bound(self):
        records = json.loads(json.dumps(self.build["graph"]["records"]))
        records[4][2] = ["-", ["core.ready", [":", "state", "ready"]]]
        changed, _artifacts = compile_records(records)
        diff = noema.semantic_diff(self.build, changed)
        for entry in diff["entries"]:
            self.assertEqual(set(entry), {"node", "kind", "change", "before", "after"})
            for digest in (entry["before"], entry["after"]):
                if digest is not None:
                    self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_maximum_precedence_node_fits_the_public_schema(self):
        high = "a" + "x" * 127
        low = "b" + "x" * 127
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", high, ["+", [":", "effect", "x"]], source_binding(0, 1)],
            ["rule", low, ["+", [":", "effect", "y"]], source_binding(1, 2)],
            [
                "precedence",
                high,
                low,
                [":", "actor", "x"],
                [":", "scope", "x"],
                [":", "evidence", "x"],
            ],
        ]
        before, _artifacts = compile_records(records)
        records[-1][3] = [":", "actor", "y"]
        after, _artifacts = compile_records(records)
        node = noema.semantic_diff(before, after)["entries"][0]["node"]
        maximum = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"][
            "diffEntry"
        ]["properties"]["node"]["maxLength"]
        self.assertEqual(len(node), 268)
        self.assertLessEqual(len(node), maximum)


class SliceTests(unittest.TestCase):
    def test_relation_closure_materializes_the_selectable_index_once(self):
        effect = "relation.index"
        records = [["import", "core", CORE_DIGEST]]
        for index in range(5):
            records.append(
                [
                    "rule",
                    f"rule.relation.{index}",
                    ["+", [":", "effect", effect]],
                    source_binding(index, index + 1),
                ]
            )
        for index in range(4):
            records.append(
                [
                    "precedence",
                    f"rule.relation.{index}",
                    f"rule.relation.{index + 1}",
                    [":", "actor", "reviewer"],
                    [":", "scope", "repository"],
                    [":", "evidence", f"relation.{index}"],
                ]
            )
        build, artifacts = compile_records(records)
        profile = noema._decode_json(
            artifacts["profile"],
            "profile",
            canonical=True,
        )
        real_set = set
        selectable_materializations = 0

        def indexed_set(value=()):
            nonlocal selectable_materializations
            if isinstance(value, dict) and any(
                str(key).startswith("rule.relation.") for key in value
            ):
                selectable_materializations += 1
            return real_set(value)

        with mock.patch.object(noema, "set", indexed_set, create=True):
            noema.select_runtime(
                build,
                profile,
                sha256(artifacts["profile"]).hexdigest(),
                runtime_selection(effect),
            )
        self.assertEqual(selectable_materializations, 1)

    def test_selection_rules_share_one_truth_expansion_budget(self):
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.guard.a",
                [
                    "?",
                    ["core.checked", [":", "evidence", "guard.a"]],
                    ["+", [":", "effect", "guard.a"]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.guard.b",
                [
                    "?",
                    ["core.checked", [":", "evidence", "guard.b"]],
                    ["+", [":", "effect", "guard.b"]],
                ],
                source_binding(1, 2),
            ],
        ]
        with mock.patch.object(
            noema,
            "MAX_TRUTH_EXPANSION_NODES",
            8,
            create=True,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                select_records(
                    records,
                    runtime_selection("absent", target="nowhere"),
                )
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_manifest_omission_validation_uses_an_included_index(self):
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.included",
                ["+", [":", "effect", "included"]],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.omitted",
                ["+", [":", "effect", "omitted"]],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("included"),
        )
        original = noema._validate_node_id_set

        class NoLinearMembership(list):
            def __contains__(self, item):
                raise AssertionError("omission validation searched the included list")

        def indexed_nodes(value, field):
            result = original(value, field)
            if field == "manifest.included_ids":
                return NoLinearMembership(result)
            return result

        with mock.patch.object(noema, "_validate_node_id_set", indexed_nodes):
            noema._validate_manifest_value(manifest)

    def test_unsealed_runtime_objects_refuse_before_deep_validation(self):
        class TraversalTrap(dict):
            def __iter__(self):
                raise AssertionError("unsealed data was traversed")

        with self.assertRaises(noema.Refusal) as build_raised:
            noema._runtime_build(TraversalTrap())
        self.assertEqual(build_raised.exception.code, "NOE-E-DIGEST.BUILD")
        with self.assertRaises(noema.Refusal) as manifest_raised:
            noema._runtime_manifest(TraversalTrap())
        self.assertEqual(
            manifest_raised.exception.code,
            "NOE-E-DIGEST.MANIFEST",
        )

    def test_slice_closure_has_a_closed_scan_budget(self):
        records = [["import", "core", CORE_DIGEST]]
        links = [f"link.{index}" for index in range(4)]
        for index in range(4):
            left = "root" if index == 0 else f"step.{index}"
            directives = [
                [
                    "!",
                    [
                        "core.effect_on",
                        [":", "effect", left],
                        [":", "artifact", links[index]],
                    ],
                ]
            ]
            if index:
                directives.append(
                    [
                        "!",
                        [
                            "core.effect_on",
                            [":", "effect", left],
                            [":", "artifact", links[index - 1]],
                        ],
                    ]
                )
            records.append(
                [
                    "rule",
                    f"rule.chain.{index}",
                    [";", *directives],
                    source_binding(index, index + 1),
                ]
            )
        with mock.patch.object(noema, "MAX_SLICE_SCANS", 5, create=True):
            with self.assertRaises(noema.Refusal) as raised:
                select_records(records, runtime_selection("root"))
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.SLICE")

    def test_transition_root_matches_only_the_selected_from_state(self):
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.inspect",
                ["+", [":", "effect", "inspect"]],
                source_binding(0, 1),
            ],
            [
                "transition",
                "transition.unrelated",
                [":", "state", "other.machine"],
                [":", "state", "other.from"],
                [":", "event", "other.event"],
                ["=", [":", "state", "other.from"], [":", "state", "other.from"]],
                [":", "state", "idle"],
                ["+", [":", "effect", "other.effect"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("inspect", state="idle"),
        )
        self.assertNotIn("transition.unrelated", manifest["included_ids"])

    def test_structurally_valid_forged_build_cannot_mint_a_sealed_manifest(self):
        effect = "forged.build"
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                ["-", [":", "effect", effect]],
                source_binding(1, 2),
            ],
        ]
        build, artifacts = compile_records(records)
        forged = json.loads(json.dumps(build))
        forged["graph"]["records"] = [
            record
            for record in forged["graph"]["records"]
            if not (record[0] == "rule" and record[1] == "rule.deny")
        ]
        forged["lock"]["graph_sha256"] = noema._value_sha256(forged["graph"])
        profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
        with self.assertRaises(noema.Refusal) as raised:
            noema.select_runtime(
                forged,
                profile,
                sha256(artifacts["profile"]).hexdigest(),
                runtime_selection(effect),
            )
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.BUILD")

    def test_profile_value_must_match_the_locked_profile_digest(self):
        build, artifacts = compile_records(base_records())
        profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
        profile["tokenizer"] = "forged-tokenizer"
        with self.assertRaises(noema.Refusal) as raised:
            noema.select_runtime(
                build,
                profile,
                build["lock"]["profile_sha256"],
                runtime_selection("ready"),
            )
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROFILE")

    def test_checked_in_manifest_recomputes_exactly(self):
        manifest, projection = noema._verify_manifest_path(
            RUNTIME_FIXTURE / "manifest.json"
        )
        self.assertEqual(manifest["projection_sha256"], sha256(projection["text"].encode()).hexdigest())

    def test_same_inputs_return_identical_manifest_and_projection(self):
        _build, _selection, first_manifest, first_projection = runtime_fixture()
        _build, _selection, second_manifest, second_projection = runtime_fixture()
        self.assertEqual(first_manifest, second_manifest)
        self.assertEqual(first_projection, second_projection)

    def test_included_and_omitted_ids_partition_selectable_graph(self):
        build, _selection, manifest, _projection = runtime_fixture()
        selectable = {
            noema._runtime_record_id(record)
            for record in build["graph"]["records"]
            if record[0] in noema.SELECTABLE_FORMS
        }
        omitted = {item["id"] for item in manifest["omitted"]}
        self.assertEqual(set(manifest["included_ids"]) | omitted, selectable)
        self.assertFalse(set(manifest["included_ids"]) & omitted)

    def test_primary_slice_closes_support_records_and_governance(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertTrue(
            {
                "promise.inspect",
                "handoff.inspect",
                "exception.deploy",
                "override.deploy",
                "precedence:rule.deploy.prohibit>rule.deploy.permit",
            }
            <= set(manifest["included_ids"])
        )

    def test_secondary_relation_root_closes_both_named_rules(self):
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.alpha",
                ["+", [":", "effect", "alpha"]],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.beta",
                ["+", [":", "effect", "beta"]],
                source_binding(1, 2),
            ],
            [
                "precedence",
                "rule.alpha",
                "rule.beta",
                [":", "actor", "reviewer"],
                [":", "scope", "selected"],
                [":", "evidence", "order"],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("absent", target="selected"),
        )
        self.assertEqual(
            set(manifest["included_ids"]),
            {
                "rule.alpha",
                "rule.beta",
                "precedence:rule.alpha>rule.beta",
            },
        )

    def test_secondary_relation_with_an_inactive_endpoint_falls_back_safely(self):
        guard = ["core.checked", [":", "evidence", "beta.active"]]
        fact = checked_fact(guard, "false", "beta-inactive")
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.alpha",
                ["+", [":", "effect", "alpha"]],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.beta",
                ["?", guard, ["+", [":", "effect", "beta"]]],
                source_binding(1, 2),
            ],
            [
                "precedence",
                "rule.alpha",
                "rule.beta",
                [":", "actor", "reviewer"],
                [":", "scope", "selected"],
                [":", "evidence", "order"],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("absent", target="selected", facts=(fact,)),
        )
        self.assertEqual(manifest["included_ids"], ["rule.alpha"])
        omissions = {item["id"]: item["reason"] for item in manifest["omitted"]}
        self.assertEqual(omissions["rule.beta"], "checked-false-guard")
        self.assertEqual(
            omissions["precedence:rule.alpha>rule.beta"],
            "not-reachable",
        )

    def test_recovery_directive_survives_support_closure(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        promise = next(item for item in manifest["tape"] if item[0] == "promise")
        self.assertIn(["+", [":", "effect", "recover"]], promise)

    def test_macro_dependency_is_reachable(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(manifest["definitions"], ["local.operator_authorized"])

    def test_only_reachable_literals_enter_the_tape(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(manifest["literals"], ["lit.instruction", "lit.note"])
        self.assertNotIn("lit.unreachable", manifest["literals"])

    def test_unknown_guard_retains_its_rule(self):
        _build, _selection, manifest, _projection = runtime_fixture(
            "selection-unknown.json"
        )
        self.assertIn("rule.review", manifest["included_ids"])

    def test_checked_false_guard_carries_exact_proof(self):
        _build, selection, manifest, _projection = runtime_fixture(
            "selection-false.json"
        )
        omission = next(item for item in manifest["omitted"] if item["id"] == "rule.beta")
        self.assertEqual(omission["reason"], "checked-false-guard")
        self.assertEqual(omission["fact"], selection["facts"][0]["id"])
        self.assertEqual(omission["evidence_sha256"], selection["facts"][0]["evidence_sha256"])

    def test_changed_fact_changes_manifest_identity(self):
        build, selection, manifest, _projection = runtime_fixture("selection-false.json")
        changed = json.loads(json.dumps(selection))
        changed["facts"][0]["value"] = "true"
        profile = json.loads((RUNTIME_FIXTURE / "profile.json").read_text())
        other, _projection = noema.select_runtime(
            build,
            profile,
            build["lock"]["profile_sha256"],
            changed,
        )
        self.assertNotEqual(noema._value_sha256(manifest), noema._value_sha256(other))

    def test_changed_operation_changes_manifest_identity(self):
        build, selection, manifest, _projection = runtime_fixture()
        changed = dict(selection)
        changed["operation"] = "review"
        profile = json.loads((RUNTIME_FIXTURE / "profile.json").read_text())
        other, _projection = noema.select_runtime(
            build,
            profile,
            build["lock"]["profile_sha256"],
            changed,
        )
        self.assertNotEqual(manifest["selection_sha256"], other["selection_sha256"])

    def test_manifest_tape_digest_is_exact(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(manifest["tape_sha256"], noema._value_sha256(manifest["tape"]))

    def test_slice_projection_recovers_exact_tape(self):
        _build, _selection, manifest, projection = runtime_fixture()
        profile = json.loads((RUNTIME_FIXTURE / "profile.json").read_text())
        self.assertEqual(noema._validate_slice_projection(projection, manifest, profile), projection)

    def test_omission_evidence_mismatch_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture("selection-false.json")
        hostile = json.loads(json.dumps(manifest))
        omission = next(item for item in hostile["omitted"] if item["id"] == "rule.beta")
        omission["evidence_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_manifest_value(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.OMISSION")

    def test_tape_digest_mismatch_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(manifest))
        hostile["tape_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_manifest_value(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.TAPE")

    def test_unsorted_facts_refuse(self):
        _build, selection, _manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(selection))
        hostile["facts"] = list(reversed(hostile["facts"]))
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_selection(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_arbitrary_fact_identity_refuses(self):
        fact = {"id": "fact.claimed", "value": "true", "evidence_sha256": "0" * 64}
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_facts([fact], "facts")
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.FACT_ID")

    def test_artifact_path_escape_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(manifest))
        hostile["artifacts"]["build"] = "../build.json"
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_manifest_value(hostile)
        self.assertEqual(raised.exception.code, "NOE-E-PATH.LEAF")

    def test_stale_selection_artifact_refuses_manifest_verification(self):
        with scratch_directory("noema-runtime-stale-") as temporary:
            root = Path(temporary)
            (root / "modules").mkdir()
            for name in ("build.json", "profile.json", "kernel.noe", "projection.json", "manifest.json"):
                write_bytes(root / name, (RUNTIME_FIXTURE / name).read_bytes())
            write_bytes(root / "modules" / "core.json", (RUNTIME_FIXTURE / "modules" / "core.json").read_bytes())
            selection = json.loads((RUNTIME_FIXTURE / "selection.json").read_text())
            selection["operation"] = "review"
            write_bytes(root / "selection.json", noema._canonical_json(selection))
            with self.assertRaises(noema.Refusal) as raised:
                noema._verify_manifest_path(root / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")

    def test_absent_root_falls_back_to_full_conservative_slice(self):
        records = base_records(["+", [":", "effect", "known"]])
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("absent", target="nowhere"),
        )
        self.assertEqual(manifest["included_ids"], ["rule.test"])

    def test_macro_hidden_prohibition_remains_reachable(self):
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "definition",
                "local.hidden_prohibition",
                [],
                [
                    "core.authorized",
                    [":", "actor", "admin"],
                    [":", "effect", "hidden"],
                ],
            ],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "hidden"]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["-", ["local.hidden_prohibition"]],
                ],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("hidden"),
        )
        self.assertIn("rule.deny", manifest["included_ids"])
        result = noema.check_runtime("hidden", [], manifest)
        self.assertEqual(result["output"]["reason"], "prohibition")

    def test_composite_guard_needs_one_exact_fact_before_omission(self):
        first = ["core.checked", [":", "evidence", "guard.first"]]
        second = ["core.checked", [":", "evidence", "guard.second"]]
        facts = sorted(
            (
                checked_fact(first, "false", "guard-first"),
                checked_fact(second, "false", "guard-second"),
            ),
            key=lambda item: item["id"],
        )
        _build, manifest, _projection = select_records(
            base_records(
                ["?", ["|", first, second], ["+", [":", "effect", "guarded"]]]
            ),
            runtime_selection("guarded", facts=facts),
        )
        self.assertIn("rule.test", manifest["included_ids"])


class PolicyCheckTests(unittest.TestCase):
    def test_policy_rules_share_one_directive_expansion_budget(self):
        effect = "directive.aggregate"
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.directive.a",
                ["+", [":", "effect", effect]],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.directive.b",
                ["+", [":", "effect", effect]],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        with mock.patch.object(
            noema,
            "MAX_DIRECTIVE_EXPANSION_NODES",
            5,
            create=True,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_policy_rules_share_one_truth_expansion_budget(self):
        effect = "truth.aggregate"
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.truth.a",
                [
                    "?",
                    ["core.checked", [":", "evidence", "truth.a"]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.truth.b",
                [
                    "?",
                    ["core.checked", [":", "evidence", "truth.b"]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        with mock.patch.object(
            noema,
            "MAX_TRUTH_EXPANSION_NODES",
            5,
            create=True,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_high_consequence_controller_supplies_the_authority(self):
        effect = "authority.controller"
        consequence = [":", "core.consequence", "3"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.early.unwrapped",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.late.authorized",
                [
                    "^",
                    [":", "actor", "operator"],
                    [
                        ";",
                        ["!", ["=", consequence, consequence]],
                        ["+", [":", "effect", effect]],
                    ],
                ],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect, authority=("operator",)),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")
        self.assertEqual(
            result["output"]["controlling_node"],
            "rule.late.authorized",
        )

    def test_allowed_consequence_zero_case_permits(self):
        _build, selection, manifest, _projection = runtime_fixture()
        result = noema.check_runtime("inspect", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_consequence_three_prohibition_refuses(self):
        _build, selection, manifest, _projection = runtime_fixture(
            "selection-deploy.json"
        )
        result = noema.check_runtime("deploy", selection["facts"], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["consequence"]), ("refuse", 3))

    def test_unknown_guard_returns_unknown(self):
        _build, selection, manifest, _projection = runtime_fixture(
            "selection-unknown.json"
        )
        result = noema.check_runtime("review", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "unknown")

    def test_permission_never_cancels_prohibition(self):
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.allow", ["+", [":", "effect", "conflict"]], source_binding(0, 1)],
            ["rule", "rule.deny", ["-", [":", "effect", "conflict"]], source_binding(1, 2)],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("conflict"))
        result = noema.check_runtime("conflict", [], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["reason"]), ("refuse", "prohibition"))

    def test_missing_policy_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture("selection-unknown.json")
        result = noema.check_runtime("absent", [], manifest)
        self.assertEqual(result["output"]["reason"], "no-applicable-policy")

    def test_fact_set_must_match_manifest(self):
        _build, selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("inspect", selection["facts"][:-1], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.FACTS")

    def test_scope_mismatch_keeps_high_consequence_default_deny(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "@",
            [":", "scope", "other"],
            ["^", [":", "actor", "operator"], [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", "scoped"]]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("scoped", authority=("operator",)),
        )
        result = noema.check_runtime("scoped", [], manifest)
        self.assertEqual(result["output"]["reason"], "default-deny")

    def test_inactive_nested_low_consequence_permission_does_not_default_permit(self):
        gate = ["core.checked", [":", "evidence", "disabled"]]
        fact = checked_fact(gate, "false", "disabled")
        consequence = [":", "core.consequence", "0"]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", gate, ["+", [":", "effect", "inactive.low"]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("inactive.low", facts=(fact,)),
        )
        result = noema.check_runtime("inactive.low", [fact], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_out_of_scope_low_consequence_permission_does_not_default_permit(self):
        consequence = [":", "core.consequence", "0"]
        directive = [
            "@",
            [":", "scope", "other"],
            [
                ";",
                ["!", ["=", consequence, consequence]],
                ["+", [":", "effect", "scoped.low"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("scoped.low", target="repository"),
        )
        result = noema.check_runtime("scoped.low", [], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_nested_authority_wrappers_accumulate(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "^",
            [":", "actor", "outer"],
            [
                "^",
                [":", "actor", "inner"],
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "nested.authority"]],
                ],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection("nested.authority", authority=("inner",)),
        )
        result = noema.check_runtime("nested.authority", [], manifest)
        self.assertEqual(result["output"]["decision"], "refuse")

    def test_nested_scope_wrappers_accumulate(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "^",
            [":", "actor", "operator"],
            [
                "@",
                [":", "scope", "other"],
                [
                    "@",
                    [":", "scope", "repository"],
                    [
                        ";",
                        ["!", ["=", consequence, consequence]],
                        ["+", [":", "effect", "nested.scope"]],
                    ],
                ],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(
                "nested.scope",
                target="repository",
                authority=("operator",),
            ),
        )
        result = noema.check_runtime("nested.scope", [], manifest)
        self.assertEqual(result["output"]["decision"], "refuse")

    def test_all_nested_authorities_and_scopes_can_apply_together(self):
        consequence = [":", "core.consequence", "3"]
        directive = [
            "^",
            [":", "actor", "outer"],
            [
                "^",
                [":", "actor", "inner"],
                [
                    "@",
                    [":", "scope", "repository"],
                    [
                        "@",
                        [":", "scope", "target"],
                        [
                            ";",
                            ["!", ["=", consequence, consequence]],
                            ["+", [":", "effect", "nested.all"]],
                        ],
                    ],
                ],
            ],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(
                "nested.all",
                target="target",
                authority=("inner", "outer"),
            ),
        )
        result = noema.check_runtime("nested.all", [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_authority_wrapper_mismatch_refuses(self):
        directive = ["^", [":", "actor", "admin"], ["+", [":", "effect", "owned"]]]
        _build, manifest, _projection = select_records(
            base_records(directive), runtime_selection("owned", authority=("operator",))
        )
        result = noema.check_runtime("owned", [], manifest)
        self.assertEqual(result["output"]["reason"], "authority-mismatch")

    def test_false_requirement_refuses(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "required"]]
        fact = checked_fact(proposition, "false", "required-false")
        directive = [";", ["!", proposition], ["+", [":", "effect", "required"]]]
        _build, manifest, _projection = select_records(
            base_records(directive), runtime_selection("required", facts=(fact,))
        )
        result = noema.check_runtime("required", [fact], manifest)
        self.assertEqual(result["output"]["reason"], "failed-requirement")

    def test_opposed_requirements_need_typed_override(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "opposed"]]
        consequence = [":", "core.consequence", "0"]
        fact = checked_fact(proposition, "true", "opposed")
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.high", [";", ["!", ["=", consequence, consequence]], ["!", proposition]], source_binding(0, 1)],
            ["rule", "rule.low", [";", ["!", ["=", consequence, consequence]], ["!", ["~", proposition]]], source_binding(1, 2)],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("opposed", facts=(fact,)))
        result = noema.check_runtime("opposed", [fact], manifest)
        self.assertEqual(result["output"]["reason"], "conflicting-requirements")

    def test_checked_higher_authority_override_resolves_requirements(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "opposed"]]
        consequence = [":", "core.consequence", "0"]
        evidence = [":", "evidence", "override"]
        facts = (
            checked_fact(proposition, "true", "opposed"),
            checked_fact(["core.checked", evidence], "true", "override"),
        )
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.high", [";", ["!", ["=", consequence, consequence]], ["!", proposition]], source_binding(0, 1)],
            ["rule", "rule.low", [";", ["!", ["=", consequence, consequence]], ["!", ["~", proposition]]], source_binding(1, 2)],
            ["override", "override.opposed", [":", "actor", "admin"], "rule.high", "rule.low", [":", "scope", "repository"], evidence],
        ]
        selection = runtime_selection("opposed", authority=("admin",), facts=facts)
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime("opposed", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_override_expands_typed_authority_and_scope_definitions(self):
        effect = "override.defined"
        proposition = [
            "core.authorized",
            [":", "actor", "operator"],
            [":", "effect", effect],
        ]
        consequence = [":", "core.consequence", "0"]
        evidence = [":", "evidence", "override.defined"]
        facts = (
            checked_fact(proposition, "true", "opposed-defined"),
            checked_fact(["core.checked", evidence], "true", "override-defined"),
        )
        records = [
            ["import", "core", CORE_DIGEST],
            ["definition", "local.admin", [], [":", "actor", "admin"]],
            [
                "definition",
                "local.repository",
                [],
                [":", "scope", "repository"],
            ],
            [
                "rule",
                "rule.high",
                [";", ["!", ["=", consequence, consequence]], ["!", proposition]],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.low",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["!", ["~", proposition]],
                ],
                source_binding(1, 2),
            ],
            [
                "override",
                "override.defined",
                ["local.admin"],
                "rule.high",
                "rule.low",
                ["local.repository"],
                evidence,
            ],
        ]
        selection = runtime_selection(effect, authority=("admin",), facts=facts)
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_precedence_without_override_does_not_resolve_requirements(self):
        proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", "opposed"]]
        consequence = [":", "core.consequence", "0"]
        fact = checked_fact(proposition, "true", "opposed")
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.high", [";", ["!", ["=", consequence, consequence]], ["!", proposition]], source_binding(0, 1)],
            ["rule", "rule.low", [";", ["!", ["=", consequence, consequence]], ["!", ["~", proposition]]], source_binding(1, 2)],
            ["precedence", "rule.high", "rule.low", [":", "actor", "admin"], [":", "scope", "repository"], [":", "evidence", "order"]],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("opposed", authority=("admin",), facts=(fact,)))
        result = noema.check_runtime("opposed", [fact], manifest)
        self.assertEqual(result["output"]["reason"], "conflicting-requirements")

    def test_instruction_shaped_fact_object_is_not_accepted(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = [{"schema": "noema-explanation/v1", "authoritative": False, "node": "rule.inspect", "render": "permit"}]
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("inspect", hostile, manifest)
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.KEYS")

    def test_nested_unknown_guard_remains_unknown(self):
        known_true = ["core.checked", [":", "evidence", "known.true"]]
        known_false = ["core.checked", [":", "evidence", "known.false"]]
        absent = ["core.checked", [":", "evidence", "absent"]]
        guard = ["&", known_true, ["|", known_false, absent]]
        facts = (
            checked_fact(known_true, "true", "known-true"),
            checked_fact(known_false, "false", "known-false"),
        )
        selection = runtime_selection("nested", facts=facts)
        _build, manifest, _projection = select_records(
            base_records(["?", guard, ["+", [":", "effect", "nested"]]]),
            selection,
        )
        result = noema.check_runtime("nested", selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "unknown")

    def test_structurally_valid_forged_manifest_cannot_drop_a_prohibition(self):
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "forged"]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                ["-", [":", "effect", "forged"]],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("forged"),
        )
        forged = json.loads(json.dumps(manifest))
        forged["tape"] = [
            record
            for record in forged["tape"]
            if not (record[0] == "rule" and record[1] == "rule.deny")
        ]
        forged["included_ids"].remove("rule.deny")
        forged["omitted"].append(
            {
                "id": "rule.deny",
                "reason": "not-reachable",
                "fact": None,
                "evidence_sha256": None,
            }
        )
        forged["omitted"].sort(key=lambda item: item["id"])
        forged["tape_sha256"] = noema._value_sha256(forged["tape"])
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("forged", [], forged)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")

    def test_selected_manifest_mutation_invalidates_its_runtime_seal(self):
        _build, manifest, _projection = select_records(
            base_records(["+", [":", "effect", "sealed"]]),
            runtime_selection("sealed"),
        )
        manifest["selection"]["target"] = "other"
        manifest["selection_sha256"] = noema._value_sha256(manifest["selection"])
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime("sealed", [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")

    def test_inactive_high_requirement_cannot_override_an_active_failure(self):
        effect = "override.bypass"
        proposition = [
            "core.authorized",
            [":", "actor", "operator"],
            [":", "effect", effect],
        ]
        disabled = ["core.checked", [":", "evidence", "high.disabled"]]
        override_evidence = [":", "evidence", "override.checked"]
        consequence = [":", "core.consequence", "0"]
        facts = sorted(
            (
                checked_fact(proposition, "false", "requirement-false"),
                checked_fact(disabled, "false", "high-disabled"),
                checked_fact(
                    ["core.checked", override_evidence],
                    "true",
                    "override-checked",
                ),
            ),
            key=lambda item: item["id"],
        )
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.high",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["?", disabled, ["!", ["~", proposition]]],
                ],
                source_binding(1, 2),
            ],
            [
                "rule",
                "rule.low",
                [";", ["!", ["=", consequence, consequence]], ["!", proposition]],
                source_binding(2, 3),
            ],
            [
                "override",
                "override.bypass",
                [":", "actor", "admin"],
                "rule.high",
                "rule.low",
                [":", "scope", "repository"],
                override_evidence,
            ],
        ]
        selection = runtime_selection(
            effect,
            authority=("admin",),
            facts=facts,
        )
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "failed-requirement"),
        )

    def test_expired_exception_refuses_beside_a_low_consequence_permission(self):
        effect = "exception.bypass"
        evidence = [":", "evidence", "exception.checked"]
        gate = ["core.checked", evidence]
        fact = checked_fact(gate, "true", "exception-checked")
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "exception",
                "exception.expired",
                [":", "actor", "admin"],
                gate,
                [":", "effect", effect],
                [":", "scope", "repository"],
                evidence,
                [":", "value", "expired"],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection(
            effect,
            authority=("admin",),
            facts=(fact,),
        )
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "invalid-exception"),
        )

    def test_exception_recovery_effect_is_not_its_policy_subject(self):
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.recover",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "recover"]],
                ],
                source_binding(0, 1),
            ],
            [
                "exception",
                "exception.deploy",
                [":", "actor", "admin"],
                ["core.checked", [":", "evidence", "emergency"]],
                [":", "effect", "deploy"],
                [":", "scope", "repository"],
                [":", "evidence", "emergency"],
                [":", "value", "expired"],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("recover"),
        )
        self.assertIn("exception.deploy", manifest["included_ids"])
        result = noema.check_runtime("recover", [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_valid_exception_cannot_mint_permission(self):
        effect = "exception.valid"
        evidence = [":", "evidence", "exception.valid"]
        gate = ["core.checked", evidence]
        fact = checked_fact(gate, "true", "exception-valid")
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "exception",
                "exception.valid",
                [":", "actor", "admin"],
                gate,
                [":", "effect", effect],
                [":", "scope", "repository"],
                evidence,
                [":", "value", "active"],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection(effect, authority=("admin",), facts=(fact,))
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_exception_expands_typed_field_definitions(self):
        effect = "exception.defined"
        evidence = [":", "evidence", "exception.defined"]
        gate = ["core.checked", evidence]
        fact = checked_fact(gate, "true", "exception-defined")
        records = [
            ["import", "core", CORE_DIGEST],
            ["definition", "local.active", [], [":", "value", "active"]],
            ["definition", "local.admin", [], [":", "actor", "admin"]],
            [
                "definition",
                "local.repository",
                [],
                [":", "scope", "repository"],
            ],
            [
                "exception",
                "exception.defined",
                ["local.admin"],
                gate,
                [":", "effect", effect],
                ["local.repository"],
                evidence,
                ["local.active"],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection(effect, authority=("admin",), facts=(fact,))
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(result["output"]["reason"], "no-applicable-policy")

    def test_missing_consequence_marker_is_not_masked_by_an_explicit_zero(self):
        effect = "mixed.consequence"
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.explicit",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", effect]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.missing",
                ["+", [":", "effect", effect]],
                source_binding(1, 2),
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.CONSEQUENCE")

    def test_out_of_range_consequence_marker_refuses(self):
        effect = "invalid.consequence"
        consequence = [":", "core.consequence", "4"]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["+", [":", "effect", effect]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect, authority=("operator",)),
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.CONSEQUENCE")

    def test_requirement_pair_work_has_a_closed_runtime_budget(self):
        effect = "policy.budget"
        records = [["import", "core", CORE_DIGEST]]
        for index in range(4):
            records.append(
                [
                    "rule",
                    f"rule.budget.{index}",
                    [
                        "!",
                        [
                            "core.authorized",
                            [":", "actor", f"actor.{index}"],
                            [":", "effect", effect],
                        ],
                    ],
                    source_binding(index, index + 1),
                ]
            )
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        with mock.patch.object(noema, "MAX_POLICY_PAIRS", 4, create=True):
            with self.assertRaises(noema.Refusal) as raised:
                noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.POLICY")

    def test_quantified_truth_shares_one_expansion_budget(self):
        effect = "truth.budget"
        consequence = [":", "core.consequence", "0"]
        members = [
            [":", "actor", "actor.five"],
            [":", "actor", "actor.four"],
            [":", "actor", "actor.one"],
            [":", "actor", "actor.three"],
            [":", "actor", "actor.two"],
        ]
        proposition = [
            "all",
            ["item", "actor"],
            ["{}", "actor", *members],
            ["=", ["%", "item"], ["%", "item"]],
        ]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", proposition, ["+", [":", "effect", effect]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect),
        )
        with mock.patch.object(
            noema,
            "MAX_TRUTH_EXPANSION_NODES",
            45,
            create=True,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_nested_directives_share_one_expansion_budget(self):
        effect = "directive.budget"
        consequence = [":", "core.consequence", "0"]
        guard = ["=", [":", "state", "ready"], [":", "state", "ready"]]
        nested = ["+", [":", "effect", effect]]
        for _index in range(6):
            nested = ["?", guard, nested]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            nested,
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect),
        )
        with mock.patch.object(
            noema,
            "MAX_DIRECTIVE_EXPANSION_NODES",
            80,
            create=True,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                noema.check_runtime(effect, [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_requirement_alone_never_permits_an_effect(self):
        proposition = [
            "core.authorized",
            [":", "actor", "operator"],
            [":", "effect", "require.only"],
        ]
        fact = checked_fact(proposition, "true", "require-only")
        directive = [
            "^",
            [":", "actor", "operator"],
            ["!", proposition],
        ]
        selection = runtime_selection(
            "require.only",
            authority=("operator",),
            facts=(fact,),
        )
        _build, manifest, _projection = select_records(
            base_records(directive),
            selection,
        )
        result = noema.check_runtime("require.only", selection["facts"], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "default-deny"),
        )

    def test_unsigned_comparison_does_not_depend_on_host_integer_limit(self):
        effect = "large.decimal"
        consequence = [":", "core.consequence", "0"]
        left = "1" + ("0" * 5_000)
        right = "9" * 5_000
        guard = ["gt", [":", "value", left], [":", "value", right]]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", guard, ["+", [":", "effect", effect]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_finite_set_count_is_a_numeric_comparison_operand(self):
        effect = "count.numeric"
        consequence = [":", "core.consequence", "0"]
        collection = [
            "{}",
            "actor",
            [":", "actor", "alpha"],
            [":", "actor", "beta"],
        ]
        guard = ["gt", ["count", collection], [":", "value", "1"]]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", guard, ["+", [":", "effect", effect]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_number_literal_is_a_numeric_comparison_operand(self):
        effect = "literal.numeric"
        consequence = [":", "core.consequence", "0"]
        guard = ["lt", ["$", "lit.one"], [":", "value", "2"]]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", guard, ["+", [":", "effect", effect]]],
        ]
        records = [
            ["import", "core", CORE_DIGEST],
            ["literal", "lit.one", "number", "1", "1"],
            ["rule", "rule.literal.numeric", directive, source_binding()],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_literal_references_are_distinct_finite_set_scalars(self):
        effect = "literal.set"
        consequence = [":", "core.consequence", "0"]
        collection = [
            "{}",
            "literal",
            ["$", "lit.alpha"],
            ["$", "lit.beta"],
        ]
        singleton = ["{}", "literal", ["$", "lit.alpha"]]
        guard = [
            "&",
            ["=", ["count", collection], [":", "value", "2"]],
            ["in", ["$", "lit.alpha"], collection],
            ["subset", singleton, collection],
        ]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", guard, ["+", [":", "effect", effect]]],
        ]
        records = [
            ["import", "core", CORE_DIGEST],
            ["literal", "lit.alpha", "text", "12", "same-payload"],
            ["literal", "lit.beta", "text", "12", "same-payload"],
            ["rule", "rule.literal.set", directive, source_binding()],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(effect),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_expanded_set_aliases_do_not_inflate_cardinality(self):
        effect = "set.cardinality"
        consequence = [":", "core.consequence", "0"]
        collection = [
            "{}",
            "actor",
            [":", "actor", "zeta"],
            ["local.actor_zeta"],
        ]
        guard = ["=", ["count", collection], [":", "value", "2"]]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", guard, ["+", [":", "effect", effect]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(
                directive,
                definitions=[
                    [
                        "definition",
                        "local.actor_zeta",
                        [],
                        [":", "actor", "zeta"],
                    ]
                ],
            ),
            runtime_selection(effect),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_expanded_set_equality_is_order_independent(self):
        effect = "set.equality"
        consequence = [":", "core.consequence", "0"]
        left = [
            "{}",
            "actor",
            [":", "actor", "beta"],
            ["local.actor_alpha"],
        ]
        right = [
            "{}",
            "actor",
            [":", "actor", "alpha"],
            [":", "actor", "beta"],
        ]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", ["=", left, right], ["+", [":", "effect", effect]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(
                directive,
                definitions=[
                    [
                        "definition",
                        "local.actor_alpha",
                        [],
                        [":", "actor", "alpha"],
                    ]
                ],
            ),
            runtime_selection(effect),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_exactly_one_is_false_after_two_established_truths(self):
        effect = "one.decisive"
        consequence = [":", "core.consequence", "0"]
        members = [
            [":", "actor", "alpha"],
            [":", "actor", "beta"],
            [":", "actor", "gamma"],
        ]
        body = [
            "core.authorized",
            ["%", "item"],
            [":", "effect", effect],
        ]
        quantified = [
            "one",
            ["item", "actor"],
            ["{}", "actor", *members],
            body,
        ]
        facts = tuple(
            sorted(
                (
                    checked_fact(
                        ["core.authorized", members[0], [":", "effect", effect]],
                        "true",
                        "one-alpha",
                    ),
                    checked_fact(
                        ["core.authorized", members[1], [":", "effect", effect]],
                        "true",
                        "one-beta",
                    ),
                ),
                key=lambda item: item["id"],
            )
        )
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["/", quantified, ["+", [":", "effect", effect]]],
        ]
        selection = runtime_selection(effect, facts=facts)
        _build, manifest, _projection = select_records(
            base_records(directive),
            selection,
        )
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], "permit")

    def test_nested_quantifier_binders_do_not_capture_outer_values(self):
        effect = "quantifier.shadow"
        consequence = [":", "core.consequence", "0"]
        outer = [":", "actor", "alpha"]
        inner = [":", "actor", "beta"]
        proposition = [
            "all",
            ["item", "actor"],
            ["{}", "actor", outer],
            [
                "any",
                ["item", "actor"],
                ["{}", "actor", inner],
                ["=", ["%", "item"], outer],
            ],
        ]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", proposition, ["+", [":", "effect", effect]]],
        ]
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect),
        )
        result = noema.check_runtime(effect, [], manifest)
        self.assertEqual(
            (result["output"]["decision"], result["output"]["reason"]),
            ("refuse", "no-applicable-policy"),
        )

    def test_closed_truth_refuses_a_contradictory_checked_fact(self):
        proposition = [
            "=",
            [":", "effect", "fact.bypass"],
            [":", "effect", "fact.bypass"],
        ]
        fact = checked_fact(proposition, "false", "contradictory")
        consequence = [":", "core.consequence", "0"]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.allow",
                [
                    ";",
                    ["!", ["=", consequence, consequence]],
                    ["+", [":", "effect", "fact.bypass"]],
                ],
                source_binding(0, 1),
            ],
            [
                "rule",
                "rule.deny",
                ["?", proposition, ["-", [":", "effect", "fact.bypass"]]],
                source_binding(1, 2),
            ],
        ]
        with self.assertRaises(noema.Refusal) as raised:
            select_records(
                records,
                runtime_selection("fact.bypass", facts=(fact,)),
            )
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.FACT_CONFLICT")

    def test_composite_truth_preserves_authored_subfact_identity(self):
        effect = "subfact.conflict"
        consequence = [":", "core.consequence", "0"]
        call = ["local.always"]
        fact = checked_fact(call, "false", "subfact-false")
        guard = [
            "&",
            call,
            ["=", [":", "state", "ready"], [":", "state", "ready"]],
        ]
        directive = [
            ";",
            ["!", ["=", consequence, consequence]],
            ["?", guard, ["+", [":", "effect", effect]]],
        ]
        selection = runtime_selection(effect, facts=(fact,))
        _build, manifest, _projection = select_records(
            base_records(
                directive,
                definitions=[
                    [
                        "definition",
                        "local.always",
                        [],
                        [
                            "=",
                            [":", "state", "ready"],
                            [":", "state", "ready"],
                        ],
                    ]
                ],
            ),
            selection,
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.FACT_CONFLICT")


class TransitionTests(unittest.TestCase):
    def test_transitions_share_one_truth_expansion_budget(self):
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.move",
                ["+", [":", "effect", "move"]],
                source_binding(0, 1),
            ],
            [
                "transition",
                "transition.budget.a",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                ["core.checked", [":", "evidence", "transition.a"]],
                [":", "state", "ready.a"],
                ["+", [":", "effect", "step.a"]],
            ],
            [
                "transition",
                "transition.budget.b",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                ["core.checked", [":", "evidence", "transition.b"]],
                [":", "state", "ready.b"],
                ["+", [":", "effect", "step.b"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("move", state="idle"),
        )
        with mock.patch.object(
            noema,
            "MAX_TRUTH_EXPANSION_NODES",
            5,
            create=True,
        ):
            with self.assertRaises(noema.Refusal) as raised:
                noema.next_runtime("machine", "idle", "go", [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.EXPANSION")

    def test_transition_expands_its_typed_state_definition(self):
        gate = ["=", [":", "state", "idle"], [":", "state", "idle"]]
        records = [
            ["import", "core", CORE_DIGEST],
            ["definition", "local.ready", [], [":", "state", "ready"]],
            [
                "rule",
                "rule.move",
                ["+", [":", "effect", "move"]],
                source_binding(0, 1),
            ],
            [
                "transition",
                "transition.defined",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                gate,
                ["local.ready"],
                ["+", [":", "effect", "move"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("move", state="idle"),
        )
        result = noema.next_runtime("machine", "idle", "go", [], manifest)
        self.assertEqual(result["output"]["next_state"], "ready")

    def test_established_transition_returns_ordered_effects(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        receipts = noema._read_fact_array(RUNTIME_FIXTURE / "receipts.json", "receipts")
        result = noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertEqual(result["output"]["status"], "transition")
        self.assertEqual([item[1][2] for item in result["output"]["effects"]], ["inspect", "record"])

    def test_wrong_event_stops(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.next_runtime("workflow", "idle", "other", [], manifest)
        self.assertEqual((result["output"]["status"], result["output"]["reason"]), ("stop", "no-enabled-transition"))

    def test_wrong_machine_stops(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.next_runtime("other", "idle", "requested", [], manifest)
        self.assertEqual(result["output"]["controlling_node"], "default.stop")

    def test_wrong_state_refuses_outside_the_selected_slice(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("workflow", "ready", "requested", [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.TRANSITION")

    def test_omitted_state_transition_cannot_be_reported_as_a_clean_stop(self):
        gate = ["=", [":", "state", "ready"], [":", "state", "ready"]]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.seed",
                ["+", [":", "effect", "seed"]],
                source_binding(0, 1),
            ],
            [
                "transition",
                "transition.ready",
                [":", "state", "machine"],
                [":", "state", "ready"],
                [":", "event", "go"],
                gate,
                [":", "state", "done"],
                ["+", [":", "effect", "finish"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("seed", state="idle"),
        )
        self.assertNotIn("transition.ready", manifest["included_ids"])
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("machine", "ready", "go", [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.TRANSITION")

    def test_unknown_transition_guard_stops_unknown(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.next_runtime("workflow", "idle", "requested", [], manifest)
        self.assertEqual((result["verdict"], result["output"]["reason"]), ("unknown", "unestablished-guard"))

    def test_false_transition_guard_stops(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        proposition = ["core.checked", [":", "evidence", "receipt"]]
        receipt = checked_fact(proposition, "false", "receipt-false")
        result = noema.next_runtime("workflow", "idle", "requested", [receipt], manifest)
        self.assertEqual(result["output"]["reason"], "no-enabled-transition")

    def test_contradictory_receipt_refuses(self):
        build, selection, manifest, projection = runtime_fixture()
        proposition = ["core.ready", [":", "state", "idle"]]
        conflict = checked_fact(proposition, "false", "different-evidence")
        conflict["id"] = selection["facts"][0]["id"]
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("workflow", "idle", "requested", [conflict], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.FACTS")

    def test_multiple_enabled_transitions_refuse(self):
        gate = ["=", [":", "state", "idle"], [":", "state", "idle"]]
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.move", ["+", [":", "effect", "move"]], source_binding(0, 1)],
            ["transition", "transition.a", [":", "state", "machine"], [":", "state", "idle"], [":", "event", "go"], gate, [":", "state", "state.one"], ["+", [":", "effect", "step.one"]]],
            ["transition", "transition.b", [":", "state", "machine"], [":", "state", "idle"], [":", "event", "go"], gate, [":", "state", "state.two"], ["+", [":", "effect", "step.two"]]],
        ]
        _build, manifest, _projection = select_records(records, runtime_selection("move", state="idle"))
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("machine", "idle", "go", [], manifest)
        self.assertEqual(raised.exception.code, "NOE-E-POLICY.TRANSITION")

    def test_established_transition_stops_for_an_unknown_competitor(self):
        established = ["=", [":", "state", "idle"], [":", "state", "idle"]]
        unknown = ["core.checked", [":", "evidence", "transition.maybe"]]
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "rule",
                "rule.move",
                ["+", [":", "effect", "move"]],
                source_binding(0, 1),
            ],
            [
                "transition",
                "transition.established",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                established,
                [":", "state", "state.one"],
                ["+", [":", "effect", "step.one"]],
            ],
            [
                "transition",
                "transition.unknown",
                [":", "state", "machine"],
                [":", "state", "idle"],
                [":", "event", "go"],
                unknown,
                [":", "state", "state.two"],
                ["+", [":", "effect", "step.two"]],
            ],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("move", state="idle"),
        )
        result = noema.next_runtime("machine", "idle", "go", [], manifest)
        self.assertEqual(
            (result["output"]["status"], result["output"]["reason"]),
            ("stop", "unestablished-guard"),
        )

    def test_receipts_must_be_sorted(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        first = checked_fact(["core.ready", [":", "state", "x"]], label="x")
        second = checked_fact(["core.ready", [":", "state", "y"]], label="y")
        receipts = sorted([first, second], key=lambda item: item["id"], reverse=True)
        with self.assertRaises(noema.Refusal) as raised:
            noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_transition_is_deterministic(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        receipts = noema._read_fact_array(RUNTIME_FIXTURE / "receipts.json", "receipts")
        first = noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        second = noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertEqual(first, second)

    def test_transition_does_not_execute_instruction_literal(self):
        marker = Path("/tmp/noema-owned")
        marker.unlink(missing_ok=True)
        _build, _selection, manifest, _projection = runtime_fixture()
        receipts = noema._read_fact_array(RUNTIME_FIXTURE / "receipts.json", "receipts")
        noema.next_runtime("workflow", "idle", "requested", receipts, manifest)
        self.assertFalse(marker.exists())


class LiteralTests(unittest.TestCase):
    def test_reachable_literal_returns_exact_bytes(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.literal_runtime("lit.instruction", manifest)
        self.assertEqual(result["output"]["value"], "$(touch /tmp/noema-owned)")

    def test_reachable_literal_retains_kind(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.literal_runtime("lit.instruction", manifest)
        self.assertEqual(result["output"]["kind"], "command")

    def test_literal_digest_covers_exact_utf8(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.literal_runtime("lit.note", manifest)
        self.assertEqual(result["output"]["sha256"], sha256(b"inspect only").hexdigest())

    def test_unreachable_literal_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.literal_runtime("lit.unreachable", manifest)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.LITERAL")

    def test_literal_is_inert_even_when_command_shaped(self):
        marker = Path("/tmp/noema-owned")
        marker.unlink(missing_ok=True)
        _build, _selection, manifest, _projection = runtime_fixture()
        noema.literal_runtime("lit.instruction", manifest)
        self.assertFalse(marker.exists())

    def test_malformed_literal_id_refuses_without_echo(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.literal_runtime("$(touch bad)", manifest)
        self.assertEqual(raised.exception.field, "literal")
        self.assertNotIn("touch", raised.exception.message)

    def test_unsealed_literal_manifest_refuses_before_inventory_validation(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = json.loads(json.dumps(manifest))
        hostile["literals"] = []
        with self.assertRaises(noema.Refusal) as raised:
            noema.literal_runtime("lit.instruction", hostile)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")


class ExplainTests(unittest.TestCase):
    def test_explanation_is_explicitly_non_authoritative(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.explain_runtime("rule.inspect", manifest)
        self.assertEqual((result["code"], result["output"]["authoritative"]), ("NOE-I-NON_AUTHORITATIVE", False))

    def test_explanation_render_is_canonical_record_json(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        result = noema.explain_runtime("rule.inspect", manifest)
        record = next(item for item in manifest["tape"] if item[0] == "rule" and item[1] == "rule.inspect")
        self.assertEqual(result["output"]["render"], noema._canonical_json(record).decode().rstrip("\n"))

    def test_missing_node_refuses(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        with self.assertRaises(noema.Refusal) as raised:
            noema.explain_runtime("rule.absent", manifest)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.NODE")

    def test_literal_node_cannot_bypass_the_literal_result_channel(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        hostile = "$(touch /tmp/noema-owned)"
        with self.assertRaises(noema.Refusal) as raised:
            noema.explain_runtime("lit.instruction", manifest)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.NODE")
        self.assertNotIn(hostile, raised.exception.message)

    def test_precedence_node_can_be_explained(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        node = "precedence:rule.deploy.prohibit>rule.deploy.permit"
        result = noema.explain_runtime(node, manifest)
        self.assertEqual(result["output"]["node"], node)

    def test_explanation_cannot_be_consumed_as_facts(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        explanation = noema.explain_runtime("rule.inspect", manifest)["output"]
        with self.assertRaises(noema.Refusal):
            noema.check_runtime("inspect", [explanation], manifest)

    def test_unsealed_explanation_cannot_be_consumed_as_manifest(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        explanation = noema.explain_runtime("rule.inspect", manifest)["output"]
        with self.assertRaises(noema.Refusal) as raised:
            noema.explain_runtime("rule.inspect", explanation)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.MANIFEST")

    def test_explanation_is_deterministic(self):
        _build, _selection, manifest, _projection = runtime_fixture()
        self.assertEqual(
            noema.explain_runtime("rule.inspect", manifest),
            noema.explain_runtime("rule.inspect", manifest),
        )


class RuntimeResultTests(unittest.TestCase):
    def run_main(self, arguments):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = noema.main(arguments)
        lines = output.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        return status, json.loads(lines[0])

    def test_runtime_self_test_cli_passes(self):
        status, result = self.run_main(["runtime-self-test"])
        self.assertEqual((status, result["counts"]["cases"]), (0, 7))
        self.assertEqual(
            result["correlation_id"],
            noema._correlation(
                "runtime-self-test",
                result["digests"]["manifest"],
                result["digests"]["cases"],
            ),
        )

    def test_final_emission_enforces_the_result_byte_limit(self):
        oversized = noema._result(
            "about",
            "ok",
            "NOE-OK",
            message="x" * noema.MAX_OUTPUT_BYTES,
        )
        with mock.patch.object(noema, "about", return_value=oversized):
            status, result = self.run_main(["about"])
        self.assertEqual(status, 2)
        self.assertEqual(result["code"], "NOE-E-BOUNDS.OUTPUT")
        self.assertEqual(result["field"], "output")

    def test_manifest_verify_cli_passes(self):
        status, result = self.run_main(["verify", "--manifest", str(RUNTIME_FIXTURE / "manifest.json")])
        self.assertEqual((status, result["verdict"]), (0, "ok"))
        self.assertEqual(
            result["correlation_id"],
            noema._correlation("verify", result["digests"]["manifest"]),
        )

    def test_runtime_self_test_binds_receipts_and_case_selections(self):
        with scratch_directory("noema-self-test-evidence-") as temporary:
            root = Path(temporary)
            fixture = root / "tests" / "fixtures" / "noema-v1" / "runtime"
            shutil.copytree(RUNTIME_FIXTURE, fixture)
            script = root / "scripts" / "noema.py"
            script.parent.mkdir()
            shutil.copy2(SCRIPT, script)
            with mock.patch.object(noema, "__file__", str(script)):
                baseline = noema.runtime_self_test()

                receipts_path = fixture / "receipts.json"
                receipts = json.loads(receipts_path.read_text(encoding="utf-8"))
                receipts[0]["evidence_sha256"] = "f" * 64
                receipts_path.write_bytes(noema._canonical_json(receipts))
                changed_receipts = noema.runtime_self_test()

                selection_path = fixture / "selection-deploy.json"
                selection = json.loads(selection_path.read_text(encoding="utf-8"))
                selection["facts"][0]["evidence_sha256"] = "e" * 64
                selection_path.write_bytes(noema._canonical_json(selection))
                changed_selection = noema.runtime_self_test()

        self.assertNotEqual(
            baseline["digests"]["cases"], changed_receipts["digests"]["cases"]
        )
        self.assertNotEqual(
            baseline["correlation_id"], changed_receipts["correlation_id"]
        )
        self.assertNotEqual(
            changed_receipts["digests"]["cases"],
            changed_selection["digests"]["cases"],
        )
        self.assertNotEqual(
            changed_receipts["correlation_id"],
            changed_selection["correlation_id"],
        )

    def test_check_cli_returns_policy_data(self):
        status, result = self.run_main([
            "check", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--effect", "inspect", "--facts", str(RUNTIME_FIXTURE / "facts.json"),
        ])
        self.assertEqual((status, result["output"]["decision"]), (0, "permit"))

    def test_next_cli_returns_ordered_data(self):
        status, result = self.run_main([
            "next", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--machine", "workflow", "--state", "idle", "--event", "requested",
            "--receipts", str(RUNTIME_FIXTURE / "receipts.json"),
        ])
        self.assertEqual((status, len(result["output"]["effects"])), (0, 2))

    def test_literal_cli_returns_data(self):
        status, result = self.run_main([
            "literal", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--id", "lit.note",
        ])
        self.assertEqual((status, result["output"]["value"]), (0, "inspect only"))

    def test_explain_cli_labels_render(self):
        status, result = self.run_main([
            "explain", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--node", "rule.inspect",
        ])
        self.assertEqual((status, result["output"]["authoritative"]), (0, False))

    def test_runtime_commands_expose_no_output_path(self):
        help_actions = {
            action.dest
            for action in noema.parser()._subparsers._group_actions[0].choices["check"]._actions
        }
        self.assertNotIn("output", help_actions)

    def test_policy_refusal_is_a_successful_command_result(self):
        _build, selection, manifest, _projection = runtime_fixture("selection-deploy.json")
        result = noema.check_runtime("deploy", selection["facts"], manifest)
        self.assertEqual((result["verdict"], result["code"]), ("refuse", "NOE-I-POLICY_REFUSE"))

    def test_unknown_is_distinct_from_refusal(self):
        _build, selection, manifest, _projection = runtime_fixture("selection-unknown.json")
        result = noema.check_runtime("review", selection["facts"], manifest)
        self.assertEqual((result["verdict"], result["code"]), ("unknown", "NOE-I-POLICY_UNKNOWN"))

    def test_every_runtime_result_has_bounded_correlation(self):
        _build, selection, manifest, _projection = runtime_fixture()
        results = [
            noema.check_runtime("inspect", selection["facts"], manifest),
            noema.next_runtime("workflow", "idle", "other", [], manifest),
            noema.literal_runtime("lit.note", manifest),
            noema.explain_runtime("rule.inspect", manifest),
        ]
        for result in results:
            with self.subTest(command=result["command"]):
                self.assertRegex(result["correlation_id"], r"^[0-9a-f]{64}$")
                self.assertLessEqual(len(result["message"]), 512)

    def test_runtime_results_bind_the_slice_inputs_and_exact_output(self):
        _build, selection, manifest, _projection = runtime_fixture()
        receipts = noema._read_fact_array(
            RUNTIME_FIXTURE / "receipts.json",
            "receipts",
        )
        check = noema.check_runtime("inspect", selection["facts"], manifest)
        transition = noema.next_runtime(
            "workflow",
            "idle",
            "requested",
            receipts,
            manifest,
        )
        literal = noema.literal_runtime("lit.note", manifest)
        explanation = noema.explain_runtime("rule.inspect", manifest)
        manifest_digest = noema._value_sha256(manifest)
        receipts_digest = noema._value_sha256(receipts)
        correlations = {
            "check": noema._correlation(
                "check",
                manifest_digest,
                manifest["facts_sha256"],
                "inspect",
            ),
            "next": noema._correlation(
                "next",
                manifest_digest,
                "workflow",
                "idle",
                "requested",
                receipts_digest,
            ),
            "literal": noema._correlation("literal", manifest_digest, "lit.note"),
            "explain": noema._correlation("explain", manifest_digest, "rule.inspect"),
        }
        for result in (check, transition, literal, explanation):
            with self.subTest(command=result["command"]):
                self.assertEqual(
                    result["correlation_id"],
                    correlations[result["command"]],
                )
                self.assertEqual(result["digests"]["manifest"], manifest_digest)
                self.assertEqual(
                    result["digests"]["output"],
                    noema._value_sha256(result["output"]),
                )
        self.assertEqual(check["digests"]["facts"], manifest["facts_sha256"])
        self.assertEqual(transition["digests"]["facts"], manifest["facts_sha256"])
        self.assertEqual(transition["digests"]["receipts"], receipts_digest)
        self.assertEqual(
            transition["digests"]["output"],
            noema._value_sha256(transition["output"]),
        )

    def test_select_result_binds_the_manifest_and_exact_output(self):
        arguments = [
            "select",
            "--build", str(RUNTIME_FIXTURE / "build.json"),
            "--modules", str(RUNTIME_FIXTURE / "modules"),
            "--profile", str(RUNTIME_FIXTURE / "profile.json"),
            "--kernel", str(RUNTIME_FIXTURE / "kernel.noe"),
            "--selection", str(RUNTIME_FIXTURE / "selection.json"),
        ]
        status, result = self.run_main(arguments)
        self.assertEqual(status, 0)
        self.assertEqual(
            result["correlation_id"],
            noema._correlation("select", result["digests"]["manifest"], "none"),
        )
        self.assertEqual(
            result["digests"]["output"],
            noema._value_sha256(result["output"]),
        )

    def test_select_comparison_names_its_baseline(self):
        status, result = self.run_main([
            "select",
            "--build", str(RUNTIME_FIXTURE / "build.json"),
            "--modules", str(RUNTIME_FIXTURE / "modules"),
            "--profile", str(RUNTIME_FIXTURE / "profile.json"),
            "--kernel", str(RUNTIME_FIXTURE / "kernel.noe"),
            "--selection", str(RUNTIME_FIXTURE / "selection.json"),
            "--previous-manifest", str(RUNTIME_FIXTURE / "manifest.json"),
        ])
        self.assertEqual(status, 0)
        self.assertFalse(result["output"]["changed"])
        self.assertEqual(
            result["digests"]["before"],
            result["digests"]["manifest"],
        )
        self.assertEqual(
            result["digests"]["after"],
            result["digests"]["manifest"],
        )
        self.assertEqual(
            result["correlation_id"],
            noema._correlation(
                "select",
                result["digests"]["manifest"],
                result["digests"]["before"],
            ),
        )

    def test_invalid_effect_is_redacted(self):
        status, result = self.run_main([
            "check", "--manifest", str(RUNTIME_FIXTURE / "manifest.json"),
            "--effect", "$(touch /tmp/noema-bad)", "--facts", str(RUNTIME_FIXTURE / "facts.json"),
        ])
        self.assertEqual(status, 2)
        self.assertNotIn("touch", result["message"])

    def test_result_schema_closes_runtime_output(self):
        definitions = json.loads(SCHEMA.read_text())["$defs"]
        self.assertEqual(
            {item["$ref"].rsplit("/", 1)[-1] for item in definitions["runtimeOutput"]["oneOf"]},
            {"selectOutput", "checkOutput", "nextOutput", "literalOutput", "explainOutput"},
        )
        for name in ("selectOutput", "checkOutput", "nextOutput", "literalOutput", "explainOutput"):
            self.assertFalse(definitions[name]["additionalProperties"])


class PathBoundaryTests(unittest.TestCase):
    def test_non_scalar_output_leaf_refuses_through_cli(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = str(Path(temporary) / "output") + "\udcff"
            arguments = [
                "parse",
                "--source",
                str(CODEC_FIXTURE),
                "--modules",
                str(MODULES_FIXTURE),
                "--profile",
                str(PROFILE_FIXTURE),
                "--kernel",
                str(KERNEL_FIXTURE),
                "--output",
                output,
            ]
            stdout = io.StringIO()
            try:
                with contextlib.redirect_stdout(stdout):
                    status = noema.main(arguments)
            except UnicodeEncodeError:
                self.fail("non-scalar output leaf escaped the refusal channel")
            self.assertEqual(status, 2)
            lines = stdout.getvalue().splitlines()
            self.assertEqual(len(lines), 1)
            result = json.loads(lines[0])
            self.assertEqual(result["code"], "NOE-E-PATH.LEAF")
            self.assertEqual(result["field"], "output")
            self.assertEqual(list(Path(temporary).iterdir()), [])

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_linked_input_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            link = Path(temporary) / "source.noe"
            link.symlink_to(CODEC_FIXTURE)
            with self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(link, "source", noema.MAX_INPUT_BYTES)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    def test_directory_input_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(Path(temporary), "source", noema.MAX_INPUT_BYTES)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are unavailable")
    def test_fifo_input_refuses_without_opening(self):
        with tempfile.TemporaryDirectory() as temporary:
            fifo = Path(temporary) / "pipe"
            os.mkfifo(fifo)
            with self.assertRaises(noema.Refusal) as raised:
                noema._read_regular(fifo, "source", noema.MAX_INPUT_BYTES)
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_linked_output_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "target"
            target.write_text("old")
            link = directory / "link"
            link.symlink_to(target)
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(link, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")
            self.assertEqual(target.read_text(), "old")

    def test_directory_output_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(Path(temporary), b"new")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFOs are unavailable")
    def test_fifo_output_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            fifo = Path(temporary) / "pipe"
            os.mkfifo(fifo)
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(fifo, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    def test_partial_writes_are_completed(self):
        real_write = os.write
        calls = 0

        def partial(descriptor, payload):
            nonlocal calls
            calls += 1
            return real_write(descriptor, payload[: max(1, len(payload) // 2)])

        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "output"
            with mock.patch.object(noema.os, "write", side_effect=partial):
                noema._atomic_write(target, b"abcdefghij")
            self.assertGreater(calls, 1)
            self.assertEqual(target.read_bytes(), b"abcdefghij")

    def test_zero_write_refuses_and_leaks_no_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            with mock.patch.object(noema.os, "write", return_value=0), self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(directory / "output", b"x")
            self.assertEqual(raised.exception.code, "NOE-E-IO.WRITE")
            self.assertEqual(list(directory.iterdir()), [])

    def test_sync_failure_preserves_old_target_and_leaks_no_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "output"
            target.write_bytes(b"old")
            with mock.patch.object(noema.os, "fsync", side_effect=OSError("fault")), self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(target, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-IO.WRITE")
            self.assertEqual(target.read_bytes(), b"old")
            self.assertEqual([path.name for path in directory.iterdir()], ["output"])

    def test_replace_failure_preserves_old_target_and_leaks_no_temporary(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "output"
            target.write_bytes(b"old")
            with mock.patch.object(noema.os, "replace", side_effect=OSError("fault")), self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(target, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-IO.WRITE")
            self.assertEqual(target.read_bytes(), b"old")
            self.assertEqual([path.name for path in directory.iterdir()], ["output"])

    def test_unsupported_descriptor_replace_is_a_bounded_refusal(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            target = directory / "output"
            target.write_bytes(b"old")
            with mock.patch.object(
                noema.os,
                "replace",
                side_effect=TypeError("descriptor replacement is unavailable"),
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    noema._atomic_write(target, b"new")
            self.assertEqual(raised.exception.code, "NOE-E-IO.WRITE")
            self.assertEqual(target.read_bytes(), b"old")
            self.assertEqual([path.name for path in directory.iterdir()], ["output"])

    def test_maximum_leaf_name_succeeds_and_plus_one_refuses(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            exact = directory / ("a" * 255)
            noema._atomic_write(exact, b"x")
            self.assertEqual(exact.read_bytes(), b"x")
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_write(directory / ("b" * 256), b"x")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.LEAF")

    def test_temporary_prefix_is_target_independent(self):
        real_open = os.open
        observed = []

        def capture(path, flags, mode=0o777, *, dir_fd=None):
            if dir_fd is not None and flags & os.O_CREAT:
                observed.append(str(path))
            if dir_fd is None:
                return real_open(path, flags, mode)
            return real_open(path, flags, mode, dir_fd=dir_fd)

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(noema.os, "open", side_effect=capture):
                noema._atomic_write(Path(temporary) / "secret-target-name", b"x")
        self.assertEqual(len(observed), 1)
        self.assertTrue(observed[0].startswith(".noema-write-"))
        self.assertNotIn("secret-target-name", observed[0])

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_output_parent_cannot_be_replaced_after_validation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            parent = root / "safe"
            displaced = root / "safe-displaced"
            outside = root / "outside"
            parent.mkdir()
            outside.mkdir()
            target = parent / "output"
            outside_target = outside / "output"
            target.write_bytes(b"old-safe")
            outside_target.write_bytes(b"old-outside")
            real_replace = os.replace
            swapped = False

            def replace_after_validation(
                source,
                destination,
                *,
                src_dir_fd=None,
                dst_dir_fd=None,
            ):
                nonlocal swapped
                if not swapped:
                    parent.rename(displaced)
                    parent.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return real_replace(
                    source,
                    destination,
                    src_dir_fd=src_dir_fd,
                    dst_dir_fd=dst_dir_fd,
                )

            with mock.patch.object(
                noema.os,
                "replace",
                side_effect=replace_after_validation,
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    noema._atomic_write(target, b"new")
            self.assertTrue(swapped)
            self.assertEqual(outside_target.read_bytes(), b"old-outside")
            self.assertEqual((displaced / "output").read_bytes(), b"new")
            self.assertEqual(raised.exception.code, "NOE-E-IO.SYNC")

    @unittest.skipUnless(hasattr(os, "symlink"), "symbolic links are unavailable")
    def test_manifest_parent_is_anchored_through_artifact_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            directory = root / "runtime"
            displaced = root / "runtime-displaced"
            outside = root / "outside"
            shutil.copytree(RUNTIME_FIXTURE, directory)
            shutil.copytree(RUNTIME_FIXTURE, outside)
            manifest_path = directory / "manifest.json"
            build_path = directory / "build.json"
            original = noema._read_canonical_json
            swapped = False

            def replace_before_path_reads(path, field, **kwargs):
                nonlocal swapped
                if not swapped and Path(path) == build_path:
                    directory.rename(displaced)
                    directory.symlink_to(outside, target_is_directory=True)
                    swapped = True
                return original(path, field, **kwargs)

            with mock.patch.object(
                noema,
                "_read_canonical_json",
                side_effect=replace_before_path_reads,
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    noema._verify_manifest_path(manifest_path)
            self.assertTrue(swapped)
            self.assertIn(
                raised.exception.code,
                {"NOE-E-IO.CHANGED", "NOE-E-PATH.IDENTITY"},
            )


class SourceBindingTests(unittest.TestCase):
    def test_corpus_verifier_binds_four_specimens(self):
        verified = noema.verify_specimen_corpus(CORPUS_MANIFEST)
        self.assertEqual(verified["counts"]["specimens"], 4)
        self.assertEqual(verified["counts"]["members"], 17)

    def test_corpus_evidence_binds_one_complete_accepted_run(self):
        corpus = read_json(CORPUS_MANIFEST)
        evidence = corpus["evidence"]
        measurement = read_json(NOEMA_FIXTURES / evidence["measurement"])
        answers = read_json(NOEMA_FIXTURES / evidence["answers"])
        evaluation = read_json(NOEMA_FIXTURES / evidence["evaluation"])
        self.assertEqual(measurement["summary"]["status"], "accepted")
        self.assertEqual(
            answers["summary"],
            {
                "expected": 32,
                "recorded": 32,
                "status": "recorded",
                "unknown": 0,
            },
        )
        self.assertEqual(
            evaluation["summary"],
            {"failed": 0, "pairs": 16, "passed": 16, "status": "accepted"},
        )

    def test_corpus_evidence_retains_both_cohorts_and_all_final_ledgers(self):
        evidence_root = NOEMA_FIXTURES / "evidence"
        retained = {
            "answers-cohort-1.json":
                "0f4c63b987cef6f454b0f62b9f7c0c66c4797ea5e8468665c074e73bee031a99",
            "evaluation-cohort-1.json":
                "91e58fbf333006406ca188b1f04399ed2dcc65a57b8a079a77da7d1701f2401d",
            "ledger-6e48bb02-attempt-1.json":
                "2b91972438cf3aed6acb151b135b0554841cd5b6444f98c162d6ba0ff8f2026c",
            "ledger-cohort-1.json":
                "df634c7aa71e3587b35c825cf0bba536c8a7474115e32572f476f7f863113b4e",
            "ledger-cohort-2.json":
                "b351a74fb7d68a5ba87ab4af49336eb208549e90633abb92c9a96feeb9530349",
            "ledger-measurement.json":
                "f50723555895dd44ab77be8ad1ac662763779a8c059e2b3c7e32c7a5e5e0fb4c",
            "measurement-6e48bb02-attempt-1.json":
                "104d5e95b5a93ef90280f426e3e9de79fa6f89f736cbff34b7f2242c7a2897f6",
            "measurement-6e48bb02-attempt-2.json":
                "6bdb9240453cc53dcf5aca1fc10e4eadeb7f54b380aa129465eb864eca9bc2dd",
        }
        for name, expected in retained.items():
            actual = sha256((evidence_root / name).read_bytes()).hexdigest()
            self.assertEqual(actual, expected)

        verified = noema.verify_specimen_corpus(CORPUS_MANIFEST)
        corpus = verified["manifest"]
        evidence = corpus["evidence"]
        profiles_path = NOEMA_FIXTURES / evidence["profiles"]
        _record, profiles_raw, profiles = noema.load_external_profiles(
            profiles_path,
            require_measurement_families=True,
            verify_files=False,
        )
        packet, packet_raw, _files = noema._build_evaluation_packet(
            CORPUS_MANIFEST,
            verified,
            profiles_raw,
            profiles,
            evidence["repository_commit"],
            evidence["repository_tree"],
        )
        answers_raw = (evidence_root / "answers-cohort-1.json").read_bytes()
        first_report, success = noema._tally_evaluation_values(
            packet,
            packet_raw,
            json.loads(answers_raw),
            answers_raw,
        )
        self.assertTrue(success)
        self.assertEqual(
            first_report,
            read_json(evidence_root / "evaluation-cohort-1.json"),
        )

        expected_ledgers = {
            "ledger-measurement.json": ("30", "2.9930459", 271, 1),
            "ledger-cohort-1.json": ("8", "0.67074575", 32, 2),
            "ledger-cohort-2.json": ("8", "0.639935975", 32, 2),
        }
        for name, expected in expected_ledgers.items():
            ledger = read_json(evidence_root / name)
            self.assertEqual(
                (
                    ledger["budget_usd"],
                    ledger["spent_usd"],
                    ledger["calls"],
                    len(ledger["reservations"]),
                ),
                expected,
            )
            self.assertIsNone(ledger["breach"])

    def test_corpus_evidence_byte_tamper_refuses(self):
        with copied_corpus() as root:
            path = root / "evidence/evaluation.json"
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.EVIDENCE")

    def test_each_specimen_id_names_its_fixed_canonical_source(self):
        for name in SPECIMEN_NAMES:
            identity = read_json(specimen_directory(name) / "source.json")
            self.assertEqual(identity["path"], noema.SPECIMEN_SOURCE_PATHS[name])

    def test_valid_alternate_source_path_refuses_before_becoming_identity(self):
        identity = read_json(specimen_directory("fiat") / "source.json")
        alternate = ROOT / "docs/noema-v1.md"
        raw = alternate.read_bytes()
        identity.update(
            {
                "path": alternate.relative_to(ROOT).as_posix(),
                "bytes": len(raw),
                "sha256": sha256(raw).hexdigest(),
                "governed": {"start": 0, "end": len(raw)},
            }
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema._source_identity(identity, ROOT)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.SOURCE")

    def test_seed_reference_names_match_the_closed_inventory(self):
        inventory = read_json(INVENTORY)
        expected = [item["path"] for item in inventory["files"]]
        self.assertEqual(expected, sorted(path.name for path in SEED_REFERENCE.iterdir()))

    def test_seed_reference_bytes_match_every_inventory_digest(self):
        inventory = read_json(INVENTORY)
        for item in inventory["files"]:
            raw = (SEED_REFERENCE / item["path"]).read_bytes()
            self.assertEqual((len(raw), sha256(raw).hexdigest()), (item["bytes"], item["sha256"]))

    def test_seed_reference_files_are_regular_and_non_executable(self):
        for path in SEED_REFERENCE.iterdir():
            mode = path.stat(follow_symlinks=False).st_mode
            self.assertTrue(stat.S_ISREG(mode))
            self.assertFalse(mode & 0o111)

    def test_seed_reference_aggregate_digest_is_manifest_bound(self):
        inventory = read_json(INVENTORY)
        evidence = [
            {"path": item["path"], "bytes": item["bytes"], "sha256": item["sha256"]}
            for item in inventory["files"]
        ]
        corpus = read_json(CORPUS_MANIFEST)
        self.assertEqual(corpus["seed"]["reference_sha256"], noema._value_sha256(evidence))

    def test_seed_inventory_exact_bytes_are_manifest_bound(self):
        corpus = read_json(CORPUS_MANIFEST)
        self.assertEqual(
            corpus["seed"]["inventory_sha256"],
            sha256(INVENTORY.read_bytes()).hexdigest(),
        )

    def test_seed_inventory_byte_tamper_refuses(self):
        with copied_corpus() as root:
            path = root / "seed-inventory.json"
            path.write_bytes(path.read_bytes() + b"\n")
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.INVENTORY")

    def test_seed_inventory_snapshot_is_held_through_the_corpus_verdict(self):
        with copied_corpus() as root:
            original = noema._verify_specimen
            mutated = False

            def mutate_after_specimen(directory, repository_root, snapshots=None):
                nonlocal mutated
                result = original(directory, repository_root, snapshots)
                if not mutated:
                    path = root / "seed-inventory.json"
                    path.write_bytes(path.read_bytes() + b"\n")
                    mutated = True
                return result

            with mock.patch.object(
                noema,
                "_verify_specimen",
                side_effect=mutate_after_specimen,
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    noema.verify_specimen_corpus(root / "manifest.json")
        self.assertTrue(mutated)
        self.assertEqual(raised.exception.code, "NOE-E-IO.CHANGED")

    def test_seed_inventory_metadata_uses_the_full_archive_validator(self):
        with copied_corpus() as root:
            inventory_path = root / "seed-inventory.json"
            inventory = read_json(inventory_path)
            inventory["archive"]["name"] = "substituted.zip"
            write_canonical_json(inventory_path, inventory)
            manifest_path = root / "manifest.json"
            manifest = read_json(manifest_path)
            manifest["seed"]["inventory_sha256"] = sha256(
                inventory_path.read_bytes()
            ).hexdigest()
            write_canonical_json(manifest_path, manifest)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(manifest_path)
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.ARCHIVE_NAME")

    def test_reference_can_rebuild_a_verified_seed_archive(self):
        inventory = read_json(INVENTORY)
        files = [
            (item["path"], (SEED_REFERENCE / item["path"]).read_bytes())
            for item in inventory["files"]
        ]
        payload = archive_bytes(files, root=inventory["archive"]["root"])
        with scratch_directory("noema-seed-rebuild-") as temporary:
            archive = Path(temporary) / "noema-v0-evidence.zip"
            rebuilt_inventory = copy.deepcopy(inventory)
            rebuilt_inventory["archive"]["bytes"] = len(payload)
            rebuilt_inventory["archive"]["sha256"] = sha256(payload).hexdigest()
            archive.write_bytes(payload)
            inventory_path = Path(temporary) / "inventory.json"
            inventory_path.write_text(json.dumps(rebuilt_inventory), encoding="utf-8")
            result = noema.verify_seed(archive, inventory_path)
        self.assertEqual((result["verdict"], result["counts"]["members"]), ("ok", 17))

    def test_source_span_maps_form_complete_byte_partitions(self):
        for name in SPECIMEN_NAMES:
            spans = read_json(specimen_directory(name) / "source-spans.json")
            cursor = 0
            for item in spans["spans"]:
                self.assertEqual(item["start"], cursor)
                cursor = item["end"]
            self.assertEqual(cursor, spans["governed"]["end"])

    def test_unsupported_remainders_never_name_nodes_or_authority(self):
        for name in SPECIMEN_NAMES:
            spans = read_json(specimen_directory(name) / "source-spans.json")
            for item in spans["spans"]:
                if item["kind"] == "unsupported-remainder":
                    self.assertIsNone(item["node"])
                    self.assertEqual(item["reason"], "unsupported-by-noema-v1")

    def test_each_specimen_remains_explicitly_shadow_only(self):
        corpus = read_json(CORPUS_MANIFEST)
        self.assertTrue(all(item["shadow"] for item in corpus["specimens"]))
        self.assertEqual(sum(item["unsupported_remainders"] for item in corpus["specimens"]), 44)

    def test_critical_nodes_bind_source_text_that_names_their_semantics(self):
        expected = {
            ("brevitas", "rule.exact"): "brevitas: evidence-exception",
            ("fiat", "rule.authorized"): "Wildcat contributor explicitly asks",
            ("fiat", "rule.negated"): "status` and `next` are the truth",
            ("fiat", "rule.ordered"): "receipt it, ask for the next one",
            ("phylax", "rule.blocked"): "model output to a shell",
            ("phylax", "rule.default"): "Adding a dependency.",
            ("phylax", "rule.authorized"): "approval a widened trust boundary",
            ("sapheneia", "rule.authorized"): "destructive action",
            ("sapheneia", "rule.unknown"): "genuinely ambiguous",
        }
        for (specimen, node), fragment in expected.items():
            directory = specimen_directory(specimen)
            identity = read_json(directory / "source.json")
            source = (ROOT / identity["path"]).read_bytes()
            spans = read_json(directory / "source-spans.json")["spans"]
            span = next(item for item in spans if item.get("node") == node)
            excerpt = source[span["start"] : span["end"]].decode("utf-8")
            self.assertIn(fragment, excerpt, (specimen, node))

    def test_specimen_effect_vocabularies_are_not_one_shared_scaffold(self):
        vocabularies = {}
        for specimen in SPECIMEN_NAMES:
            records = noema._parse_source_lines(
                (specimen_directory(specimen) / "source.noe").read_bytes()
            )
            vocabularies[specimen] = {
                value
                for record in records
                if record[0] == "rule"
                for kind, value in noema._typed_atoms(record[2])
                if kind == "effect"
            }
            self.assertGreaterEqual(len(vocabularies[specimen]), 10)
        for index, left in enumerate(SPECIMEN_NAMES):
            for right in SPECIMEN_NAMES[index + 1 :]:
                self.assertFalse(vocabularies[left] & vocabularies[right])

    def test_source_authority_conditions_are_explicit_checked_facts(self):
        expected = {
            "fiat": "fiat-request-explicit",
            "sapheneia": "destructive-action-confirmed",
        }
        for specimen, evidence in expected.items():
            directory = specimen_directory(specimen)
            records = noema._parse_source_lines((directory / "source.noe").read_bytes())
            rule = next(
                record
                for record in records
                if record[:2] == ["rule", "rule.authorized"]
            )
            proposition = rule[2][2][1]
            self.assertEqual(
                proposition,
                ["core.checked", [":", "evidence", evidence]],
            )
            facts = {
                item["id"]: item
                for item in read_json(directory / "selection.json")["facts"]
            }
            self.assertEqual(facts[noema.fact_id(proposition)]["value"], "true")

    def test_corpus_record_cannot_promote_a_fully_mapped_specimen(self):
        record = copy.deepcopy(read_json(CORPUS_MANIFEST)["specimens"][0])
        record["unsupported_remainders"] = 0
        record["shadow"] = False
        with self.assertRaises(noema.Refusal) as raised:
            noema._specimen_record(record, "corpus.specimens[0]")
        self.assertEqual(raised.exception.code, "NOE-E-AUTHORITY.SHADOW")

    def test_source_digest_tamper_refuses(self):
        with copied_corpus() as root:
            path = specimen_directory("fiat", root) / "source.json"
            value = read_json(path)
            value["sha256"] = "0" * 64
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.SOURCE")

    def test_canonical_source_snapshot_is_held_through_the_corpus_verdict(self):
        with copied_corpus() as root, tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            for relative in noema.SPECIMEN_SOURCE_PATHS.values():
                target = repository / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / relative, target)
            original = noema._verify_specimen
            calls = 0

            def mutate_after_later_specimen(
                directory,
                repository_root,
                snapshots=None,
            ):
                nonlocal calls
                result = original(directory, repository_root, snapshots)
                calls += 1
                if calls == 2:
                    relative = noema.SPECIMEN_SOURCE_PATHS["brevitas"]
                    target = repository / relative
                    target.write_bytes(target.read_bytes() + b"\n")
                return result

            with mock.patch.object(
                noema,
                "_verify_specimen",
                side_effect=mutate_after_later_specimen,
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    with noema._SnapshotSet() as snapshots:
                        noema._verify_specimen_corpus_impl(
                            root / "manifest.json",
                            snapshots,
                            repository_root=repository,
                        )
        self.assertEqual(calls, 4)
        self.assertEqual(raised.exception.code, "NOE-E-IO.CHANGED")

    def test_source_span_gap_refuses(self):
        with copied_corpus() as root:
            path = specimen_directory("fiat", root) / "source-spans.json"
            value = read_json(path)
            value["spans"][1]["start"] += 1
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.SPAN_GAP")

    def test_source_span_overlap_refuses(self):
        with copied_corpus() as root:
            path = specimen_directory("phylax", root) / "source-spans.json"
            value = read_json(path)
            value["spans"][1]["start"] -= 1
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.SPAN_OVERLAP")

    def test_remainder_cannot_mint_a_node(self):
        with copied_corpus() as root:
            path = specimen_directory("sapheneia", root) / "source-spans.json"
            value = read_json(path)
            remainder = next(item for item in value["spans"] if item["kind"] == "unsupported-remainder")
            remainder["node"] = "rule.inject"
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-AUTHORITY.REMAINDER")

    def test_shadow_flag_cannot_hide_remainders(self):
        with copied_corpus() as root:
            path = specimen_directory("brevitas", root) / "source-spans.json"
            value = read_json(path)
            value["shadow"] = False
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-AUTHORITY.SHADOW")

    def test_extra_seed_reference_member_refuses(self):
        with copied_corpus() as root:
            (root / "seed-reference/extra.txt").write_bytes(b"extra")
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.EXTRA_MEMBER")

    def test_executable_seed_reference_member_refuses(self):
        with copied_corpus() as root:
            path = next((root / "seed-reference").iterdir())
            path.chmod(0o755)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-AUTHORITY.SEED")

    def test_seed_mode_is_checked_on_the_same_bytes_that_are_hashed(self):
        with copied_corpus() as root:
            reference = root / "seed-reference"
            target = reference / "bootstrap.txt"
            target.chmod(0o755)
            seed = read_json(root / "manifest.json")["seed"]
            original = noema._read_directory_regular
            hid_mode = False

            def hide_mode_after_read(descriptor, leaf, field, limit):
                nonlocal hid_mode
                raw, identity = original(descriptor, leaf, field, limit)
                if leaf == "bootstrap.txt":
                    target.chmod(0o644)
                    hid_mode = True
                return raw, identity

            with mock.patch.object(
                noema,
                "_read_directory_regular",
                side_effect=hide_mode_after_read,
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    noema._verify_seed_reference(root, seed)
            self.assertTrue(hid_mode)
            self.assertEqual(raised.exception.code, "NOE-E-AUTHORITY.SEED")

    def test_symlinked_seed_reference_member_refuses(self):
        with copied_corpus() as root:
            path = root / "seed-reference/bootstrap.txt"
            path.unlink()
            path.symlink_to(root / "seed-reference/coverage.md")
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-PATH.REGULAR")

    def test_noncanonical_corpus_manifest_refuses(self):
        with copied_corpus() as root:
            path = root / "manifest.json"
            value = read_json(path)
            path.write_text(json.dumps(value, indent=2), encoding="utf-8")
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(path)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.CANONICAL")


class SpecimenRoundTripTests(unittest.TestCase):
    def test_corpus_manifest_records_distinct_derived_objects(self):
        corpus = read_json(CORPUS_MANIFEST)
        keys = (
            "source_sha256", "canonical_sha256", "graph_sha256",
            "full_projection_sha256", "manifest_sha256", "projection_sha256",
            "literals_sha256", "kernel_sha256", "definitions_sha256",
        )
        for specimen in corpus["specimens"]:
            self.assertEqual(len({specimen[key] for key in keys}), len(keys))

    def test_corpus_uses_all_ten_literal_kinds(self):
        values = read_json(specimen_directory("brevitas") / "literals.json")
        self.assertEqual({item["kind"] for item in values["literals"]}, set(noema.LITERAL_KINDS))

    def test_literal_payloads_do_not_mint_nodes_aliases_or_effects(self):
        directory = specimen_directory("brevitas")
        literals = read_json(directory / "literals.json")["literals"]
        graph = read_json(directory / "build.json")["graph"]
        profile = read_json(directory / "profile.json")
        nodes = {item[1] for item in graph["records"] if item[0] != "import"}
        aliases = {value for pair in profile["aliases"] for value in pair}
        effects = set()
        for record in graph["records"]:
            if record[0] == "rule":
                effects.update(value for kind, value in noema._typed_atoms(record[2]) if kind == "effect")
        for item in literals:
            self.assertNotIn(item["value"], nodes)
            self.assertNotIn(item["value"], aliases)
            self.assertNotIn(item["value"], effects)

    def test_question_sets_cover_all_three_policy_decisions(self):
        for name in SPECIMEN_NAMES:
            questions = read_json(specimen_directory(name) / "questions.json")
            self.assertEqual(
                {item["expected"]["decision"] for item in questions["questions"]},
                {"permit", "refuse", "unknown"},
            )

    def test_corpus_outputs_are_deterministic_across_two_verifications(self):
        first = noema.verify_specimen_corpus(CORPUS_MANIFEST)
        second = noema.verify_specimen_corpus(CORPUS_MANIFEST)
        self.assertEqual(first, second)

    def test_top_level_verify_dispatches_to_the_specimen_corpus(self):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "verify", "--manifest", str(CORPUS_MANIFEST)],
            check=False,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(completed.returncode, 0)
        self.assertEqual((result["verdict"], result["counts"]["specimens"]), ("ok", 4))

    def test_specimen_output_inventory_is_closed(self):
        inputs = {
            "kernel.noe", "mutation-plan.json", "profile.json", "questions.json",
            "selection.json", "source.json", "source.noe", "modules", "mutations",
        }
        for name in SPECIMEN_NAMES:
            actual = {path.name for path in specimen_directory(name).iterdir()}
            self.assertEqual(actual, inputs | set(noema.SPECIMEN_OUTPUTS))

    def test_specimen_artifact_inventory_digest_matches_the_closed_tree(self):
        corpus = read_json(CORPUS_MANIFEST)
        for committed in corpus["specimens"]:
            directory = specimen_directory(committed["id"])
            build = read_json(directory / "build.json")
            plan = noema._mutation_plan(
                read_json(directory / "mutation-plan.json"),
                committed["id"],
            )
            paths = noema._specimen_artifact_paths(build, plan)
            inventory = noema._closed_specimen_inventory(
                directory,
                committed["id"],
                paths,
            )
            self.assertEqual(
                noema._value_sha256(inventory),
                committed["artifact_inventory_sha256"],
            )

    def test_specimen_root_replacement_cannot_hide_an_extra_member(self):
        with copied_corpus() as root:
            directory = specimen_directory("brevitas", root)
            displaced = directory.with_name("brevitas-displaced")
            alternate = directory.with_name("brevitas-alternate")
            shutil.copytree(directory, alternate)
            (alternate / "undeclared.txt").write_bytes(b"hidden after listing")
            build = read_json(directory / "build.json")
            plan = noema._mutation_plan(
                read_json(directory / "mutation-plan.json"),
                "brevitas",
            )
            paths = noema._specimen_artifact_paths(build, plan)
            real_scandir = os.scandir
            swapped = False

            class SwapAfterListing:
                def __init__(self, entries):
                    self.entries = entries

                def __enter__(self):
                    self.entries.__enter__()
                    return self

                def __exit__(self, *args):
                    return self.entries.__exit__(*args)

                def __iter__(self):
                    return self

                def __next__(self):
                    nonlocal swapped
                    try:
                        return next(self.entries)
                    except StopIteration:
                        if not swapped:
                            directory.rename(displaced)
                            alternate.rename(directory)
                            swapped = True
                        raise

            calls = 0

            def replace_after_root_listing(path):
                nonlocal calls
                calls += 1
                entries = real_scandir(path)
                if calls == 1:
                    return SwapAfterListing(entries)
                return entries

            with mock.patch.object(noema.os, "scandir", side_effect=replace_after_root_listing):
                with self.assertRaises(noema.Refusal) as raised:
                    noema._closed_specimen_inventory(directory, "brevitas", paths)
            self.assertTrue(swapped)
            self.assertIn(
                raised.exception.code,
                {"NOE-E-PATH.IDENTITY", "NOE-E-IO.CHANGED"},
            )

    def test_earlier_specimen_snapshot_is_held_through_the_corpus_verdict(self):
        with copied_corpus() as root:
            manifest_path = root / "manifest.json"
            manifest = read_json(manifest_path)
            manifest.pop("evidence")
            write_canonical_json(manifest_path, manifest)
            original = noema._verify_specimen
            calls = 0

            def mutate_after_later_specimen(
                directory,
                repository_root,
                snapshots=None,
            ):
                nonlocal calls
                result = original(directory, repository_root, snapshots)
                calls += 1
                if calls == 2:
                    target = specimen_directory("brevitas", root) / "source.noe"
                    target.write_bytes(target.read_bytes() + b"\n")
                return result

            with mock.patch.object(
                noema,
                "_verify_specimen",
                side_effect=mutate_after_later_specimen,
            ):
                with self.assertRaises(noema.Refusal) as raised:
                    noema.verify_specimen_corpus(manifest_path)
        self.assertEqual(raised.exception.code, "NOE-E-IO.CHANGED")

    def test_closed_inventory_stops_at_the_first_unexpected_member(self):
        class Entry:
            name = "unexpected"

        class HostileEntries:
            def __init__(self):
                self.calls = 0

            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def __iter__(self):
                return self

            def __next__(self):
                self.calls += 1
                if self.calls == 1:
                    return Entry()
                raise AssertionError("directory enumeration continued after an extra member")

        directory = specimen_directory("brevitas")
        build = read_json(directory / "build.json")
        plan = noema._mutation_plan(
            read_json(directory / "mutation-plan.json"),
            "brevitas",
        )
        paths = noema._specimen_artifact_paths(build, plan)
        entries = HostileEntries()
        with mock.patch.object(noema.os, "scandir", return_value=entries):
            with self.assertRaises(noema.Refusal) as raised:
                noema._closed_specimen_inventory(directory, "brevitas", paths)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.EXTRA_MEMBER")
        self.assertEqual(entries.calls, 1)

    def test_closed_inventory_enforces_the_aggregate_bound_while_reading(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            (directory / "a").write_bytes(b"a" * 700_000)
            (directory / "b").write_bytes(b"b" * 700_000)
            with self.assertRaises(noema.Refusal) as raised:
                noema._closed_specimen_inventory(
                    directory,
                    "bounded",
                    {"a", "b"},
                )
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.ARTIFACTS")

    def test_snapshot_set_closes_retained_directory_descriptors(self):
        directory = specimen_directory("brevitas")
        build = read_json(directory / "build.json")
        plan = noema._mutation_plan(
            read_json(directory / "mutation-plan.json"),
            "brevitas",
        )
        closed = noema._closed_specimen_inventory(
            directory,
            "brevitas",
            noema._specimen_artifact_paths(build, plan),
            hold_snapshot=True,
        )
        self.assertIsInstance(closed, tuple)
        _inventory, snapshot = closed
        descriptors = [
            snapshot.root_descriptor,
            *(descriptor for descriptor, _identity in snapshot.children.values()),
        ]
        with noema._SnapshotSet() as snapshots:
            snapshots.add(snapshot)
        for descriptor in descriptors:
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_extra_specimen_root_member_refuses(self):
        with copied_corpus() as root:
            (specimen_directory("brevitas", root) / "undeclared.txt").write_bytes(
                b"unbound payload"
            )
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.EXTRA_MEMBER")

    def test_extra_module_or_mutation_member_refuses(self):
        for relative in ("modules/extra.json", "mutations/extra.noe"):
            with self.subTest(relative=relative), copied_corpus() as root:
                (specimen_directory("brevitas", root) / relative).write_bytes(b"extra")
                with self.assertRaises(noema.Refusal) as raised:
                    noema.verify_specimen_corpus(root / "manifest.json")
                self.assertEqual(
                    raised.exception.code,
                    "NOE-E-REFERENCE.EXTRA_MEMBER",
                )

    def test_unreachable_hostile_literals_remain_out_of_the_operation_slice(self):
        directory = specimen_directory("brevitas")
        manifest = read_json(directory / "manifest.json")
        self.assertEqual(manifest["literals"], ["lit.quote"])
        self.assertNotIn("lit.command", manifest["literals"])
        self.assertNotIn("lit.url", manifest["literals"])

    def test_formal_kernel_is_complete_and_shared_by_every_projection(self):
        kernel = KERNEL_FIXTURE.read_bytes()
        self.assertGreater(len(kernel), 800)
        for required in (
            b"D[\"?\",g,d]=T:d,F:none,U:block(d)",
            b"D[\"^\",actor,d]=actor is exclusive authority",
            b"FACT id=sha256(canonical proposition)",
            b"check(effect): active prohibit=>refuse",
            b"execute=never",
        ):
            self.assertIn(required, kernel)
        copies = [RUNTIME_FIXTURE / "kernel.noe"] + [
            specimen_directory(name) / "kernel.noe" for name in SPECIMEN_NAMES
        ]
        for path in copies:
            self.assertEqual(path.read_bytes(), kernel)

    def test_every_checked_fact_has_one_exposed_graph_proposition(self):
        for specimen in SPECIMEN_NAMES:
            directory = specimen_directory(specimen)
            build = read_json(directory / "build.json")
            selection = read_json(directory / "selection.json")
            context = noema._evaluation_runtime_context(
                build["graph"],
                selection,
            )
            self.assertEqual(
                [item["id"] for item in context["facts"]],
                [item["id"] for item in selection["facts"]],
            )
            for item in context["facts"]:
                self.assertEqual(noema.fact_id(item["proposition"]), item["id"])

    def test_unbound_checked_fact_cannot_enter_evaluation_context(self):
        directory = specimen_directory("sapheneia")
        build = read_json(directory / "build.json")
        selection = copy.deepcopy(read_json(directory / "selection.json"))
        selection["facts"] = [
            {
                "evidence_sha256": "0" * 64,
                "id": "fact." + "0" * 64,
                "value": "unknown",
            }
        ]
        with self.assertRaises(noema.Refusal) as raised:
            noema._evaluation_runtime_context(build["graph"], selection)
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.FACT_CONTEXT")

    def test_non_proposition_graph_list_cannot_enter_evaluation_context(self):
        directory = specimen_directory("sapheneia")
        build = read_json(directory / "build.json")
        selection = copy.deepcopy(read_json(directory / "selection.json"))
        rule = next(
            record
            for record in build["graph"]["records"]
            if record[:2] == ["rule", "rule.authorized"]
        )
        selection["facts"] = [
            {
                "evidence_sha256": "0" * 64,
                "id": noema.fact_id(rule[2]),
                "value": "unknown",
            }
        ]
        with self.assertRaises(noema.Refusal) as raised:
            noema._evaluation_runtime_context(build["graph"], selection)
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.FACT_CONTEXT")

    def test_expanded_checked_fact_is_exposed_as_its_exact_proposition(self):
        directory = specimen_directory("fiat")
        build = read_json(directory / "build.json")
        selection = copy.deepcopy(read_json(directory / "selection.json"))
        rule = next(
            record
            for record in build["graph"]["records"]
            if record[:2] == ["rule", "rule.defined"]
        )
        _literals, definitions = noema._runtime_registry(build["graph"])
        expanded = noema._expand_runtime_term(rule[2][1], definitions)
        selection["facts"] = [
            {
                "evidence_sha256": "0" * 64,
                "id": noema.fact_id(expanded),
                "value": "true",
            }
        ]
        context = noema._evaluation_runtime_context(build["graph"], selection)
        self.assertEqual(context["facts"][0]["proposition"], expanded)

    def test_full_projection_and_slice_are_separate_objects(self):
        for name in SPECIMEN_NAMES:
            directory = specimen_directory(name)
            self.assertNotEqual(
                sha256((directory / "full-projection.json").read_bytes()).hexdigest(),
                sha256((directory / "projection.json").read_bytes()).hexdigest(),
            )

    def test_stored_answer_tamper_refuses(self):
        with copied_corpus() as root:
            path = specimen_directory("fiat", root) / "answers.json"
            value = read_json(path)
            value["answers"][0]["result"]["output"]["decision"] = "refuse"
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.ANSWER")


class MutationTests(unittest.TestCase):
    def test_corpus_contains_each_hostile_category_exactly_once(self):
        self.assertEqual(set(mutation_index()), set(noema.MUTATION_CATEGORIES))
        self.assertEqual(len(mutation_index()), 13)

    def test_mutations_command_reports_all_thirteen(self):
        result = noema.mutations_command(CORPUS_MANIFEST)
        self.assertEqual((result["verdict"], result["counts"]["mutations"]), ("ok", 13))

    def test_mutation_artifacts_are_confined_to_their_specimens(self):
        for planned, _outcome in mutation_index().values():
            suffix = ".json" if planned["kind"] == "profile" else ".noe"
            self.assertEqual(planned["artifact"], f"mutations/{planned['id']}{suffix}")

    def test_every_mutation_artifact_matches_its_one_change_recipe(self):
        for name in SPECIMEN_NAMES:
            directory = specimen_directory(name)
            baseline_source = (directory / "source.noe").read_bytes()
            baseline_profile = (directory / "profile.json").read_bytes()
            plan = read_json(directory / "mutation-plan.json")
            for planned in plan["mutations"]:
                artifact = (directory / planned["artifact"]).read_bytes()
                noema._validate_mutation_artifact(
                    planned,
                    artifact,
                    baseline_source,
                    baseline_profile,
                    planned["id"],
                )

    def test_source_mutation_recipes_are_pairwise_distinct(self):
        source_categories = sorted(noema.MUTATION_CATEGORIES - {"alias-collision"})
        fingerprints = {}
        for category in source_categories:
            outcomes = []
            for name in SPECIMEN_NAMES:
                baseline_source = (
                    specimen_directory(name) / "source.noe"
                ).read_bytes()
                try:
                    artifact = noema._expected_source_mutation(
                        category,
                        baseline_source,
                        f"test.{category}.{name}",
                    )
                except noema.Refusal as error:
                    outcomes.append((name, "refused", error.code))
                else:
                    outcomes.append((name, "changed", sha256(artifact).hexdigest()))
            fingerprints[category] = tuple(outcomes)
        self.assertEqual(len(set(fingerprints.values())), len(source_categories))

    def test_alias_collision_rejects_a_different_colliding_profile(self):
        directory = specimen_directory("brevitas")
        baseline_source = (directory / "source.noe").read_bytes()
        baseline_profile = (directory / "profile.json").read_bytes()
        profile = json.loads(baseline_profile)
        profile["aliases"].append(["rule", "P"])
        profile["aliases"].sort(key=lambda item: item[0])
        planned = read_json(directory / "mutation-plan.json")["mutations"][0]
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_mutation_artifact(
                planned,
                noema._canonical_json(profile),
                baseline_source,
                baseline_profile,
                "test.alias",
            )
        self.assertEqual(
            raised.exception.code,
            "NOE-E-REFERENCE.MUTATION_ARTIFACT",
        )

    def test_refused_mutation_bytes_are_bound_even_when_the_outcome_is_unchanged(self):
        with copied_corpus() as root:
            path = specimen_directory("sapheneia", root) / (
                "mutations/sapheneia.unknown-opcode.noe"
            )
            original = path.read_bytes()
            changed = original.replace(b'"zap"', b'"zip"')
            self.assertNotEqual(changed, original)
            path.write_bytes(changed)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(root / "manifest.json")
        self.assertEqual(
            raised.exception.code,
            "NOE-E-REFERENCE.MUTATION_ARTIFACT",
        )

    def test_swapped_actor_cannot_substitute_missing_authority(self):
        with copied_corpus() as root:
            directory = specimen_directory("sapheneia", root)
            path = directory / "mutations/sapheneia.swapped-actor.noe"
            path.write_bytes(
                (
                    specimen_directory("fiat", root)
                    / "mutations/fiat.missing-authority.noe"
                ).read_bytes()
            )
            with self.assertRaises(noema.Refusal) as raised:
                noema._derive_specimen(directory, ROOT)
        self.assertEqual(
            raised.exception.code,
            "NOE-E-REFERENCE.MUTATION_ARTIFACT",
        )

    def test_omitted_dependency_cannot_substitute_an_unknown_predicate(self):
        with copied_corpus() as root:
            directory = specimen_directory("phylax", root)
            records = noema._parse_source_lines(
                (directory / "source.noe").read_bytes()
            )
            definition = next(item for item in records if item[0] == "definition")
            definition[3] = ["missing.predicate", ["%", "effect"]]
            path = directory / "mutations/phylax.omitted-dependency.noe"
            path.write_bytes(noema._canonical_source(records))
            with self.assertRaises(noema.Refusal) as raised:
                noema._derive_specimen(directory, ROOT)
        self.assertEqual(
            raised.exception.code,
            "NOE-E-REFERENCE.MUTATION_ARTIFACT",
        )

    def test_changed_mutations_change_both_graph_and_observation(self):
        for _planned, outcome in mutation_index().values():
            if outcome["status"] == "changed":
                self.assertNotEqual(outcome["diff"]["before_graph_sha256"], outcome["graph_sha256"])
                self.assertNotEqual(outcome["baseline_answer_sha256"], outcome["answer_sha256"])

    def test_refused_mutations_retain_a_checked_baseline(self):
        for _planned, outcome in mutation_index().values():
            self.assertEqual(
                outcome["baseline_answer_sha256"],
                noema._value_sha256(outcome["baseline_answer"]),
            )

    def test_unchanged_mutation_refuses_before_a_result_can_pass(self):
        with copied_corpus() as root:
            directory = specimen_directory("brevitas", root)
            (directory / "mutations/brevitas.changed-exact-literal.noe").write_bytes(
                (directory / "source.noe").read_bytes()
            )
            with self.assertRaises(noema.Refusal) as raised:
                noema._derive_specimen(directory, ROOT)
        self.assertEqual(
            raised.exception.code,
            "NOE-E-REFERENCE.MUTATION_ARTIFACT",
        )

    def test_wrong_mutation_query_refuses_the_fixed_contract(self):
        plan = read_json(specimen_directory("fiat") / "mutation-plan.json")
        plan["mutations"][0]["query"]["effect"] = "authorized"
        with self.assertRaises(noema.Refusal) as raised:
            noema._mutation_plan(plan, "fiat")
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.MUTATION_CONTRACT")

    def test_mutation_category_cannot_move_between_specimen_ids(self):
        plan = read_json(specimen_directory("fiat") / "mutation-plan.json")
        target = next(
            item for item in plan["mutations"] if item["id"] == "fiat.missing-authority"
        )
        target["category"] = "swapped-actor"
        with self.assertRaises(noema.Refusal) as raised:
            noema._mutation_plan(plan, "fiat")
        self.assertEqual(
            raised.exception.code,
            "NOE-E-REFERENCE.MUTATION_ASSIGNMENT",
        )

    def test_specimen_cannot_omit_an_assigned_mutation(self):
        plan = read_json(specimen_directory("fiat") / "mutation-plan.json")
        plan["mutations"].pop()
        with self.assertRaises(noema.Refusal) as raised:
            noema._mutation_plan(plan, "fiat")
        self.assertEqual(
            raised.exception.code,
            "NOE-E-REFERENCE.MUTATION_ASSIGNMENT",
        )

    def test_wrong_mutation_artifact_name_refuses(self):
        plan = read_json(specimen_directory("fiat") / "mutation-plan.json")
        plan["mutations"][0]["artifact"] = "mutations/other.noe"
        with self.assertRaises(noema.Refusal) as raised:
            noema._mutation_plan(plan, "fiat")
        self.assertEqual(raised.exception.code, "NOE-E-PATH.MUTATION")

    def test_mutation_baseline_digest_tamper_refuses(self):
        directory = specimen_directory("fiat")
        plan = noema._mutation_plan(read_json(directory / "mutation-plan.json"), "fiat")
        results = read_json(directory / "mutation-results.json")
        results["results"][0]["baseline_answer_sha256"] = "0" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_mutation_results(results, "fiat", plan)
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.ANSWER")

    def test_mutation_facet_tamper_refuses(self):
        directory = specimen_directory("fiat")
        plan = noema._mutation_plan(read_json(directory / "mutation-plan.json"), "fiat")
        results = read_json(directory / "mutation-results.json")
        outcome = results["results"][0]
        outcome["diff"]["entries"][0]["kind"] = "literal"
        outcome["diff_sha256"] = noema._value_sha256(outcome["diff"])
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_mutation_results(results, "fiat", plan)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.MUTATION_FACETS")

    def test_ordering_mutation_is_an_exact_two_effect_swap(self):
        _planned, outcome = mutation_index()["reordered-effects"]
        before = json.loads(outcome["baseline_answer"]["output"]["render"])
        after = json.loads(outcome["answer"]["output"]["render"])
        self.assertEqual(after[2], [before[2][0], before[2][1], before[2][3], before[2][2]])

    def test_exact_literal_mutation_preserves_kind_and_changes_bytes(self):
        _planned, outcome = mutation_index()["changed-exact-literal"]
        before = outcome["baseline_answer"]["output"]
        after = outcome["answer"]["output"]
        self.assertEqual((before["id"], before["kind"]), (after["id"], after["kind"]))
        self.assertNotEqual((before["bytes"], before["sha256"]), (after["bytes"], after["sha256"]))


class CriticalVectorTests(unittest.TestCase):
    def test_critical_vector_inventory_is_complete_and_sorted(self):
        vectors = read_json(CORPUS_MANIFEST)["critical_vectors"]
        self.assertEqual([item["id"] for item in vectors], sorted(noema.CRITICAL_VECTORS))
        self.assertEqual(
            {item["id"]: tuple(item["mutations"]) for item in vectors},
            noema.CRITICAL_MUTATION_IDS,
        )

    def test_every_critical_mutation_has_a_checked_outcome(self):
        outcomes = {planned["id"]: outcome for planned, outcome in mutation_index().values()}
        vectors = read_json(CORPUS_MANIFEST)["critical_vectors"]
        for vector in vectors:
            for identifier in vector["mutations"]:
                self.assertIn(outcomes[identifier]["status"], {"changed", "refused"})

    def test_wrong_category_under_a_critical_vector_refuses(self):
        with copied_corpus() as root:
            path = root / "manifest.json"
            value = read_json(path)
            authority = next(item for item in value["critical_vectors"] if item["id"] == "authority")
            authority["mutations"] = ["fiat.dropped-negation"]
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(path)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.CRITICAL")

    def test_missing_critical_vector_refuses(self):
        with copied_corpus() as root:
            path = root / "manifest.json"
            value = read_json(path)
            value["critical_vectors"].pop()
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(path)
        self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.CRITICAL")

    def test_critical_vector_subset_is_not_complete_coverage(self):
        with copied_corpus() as root:
            path = root / "manifest.json"
            value = read_json(path)
            authority = next(
                item for item in value["critical_vectors"] if item["id"] == "authority"
            )
            authority["mutations"] = ["fiat.missing-authority"]
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(path)
        self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.CRITICAL")

    def test_duplicate_critical_mutation_refuses(self):
        with copied_corpus() as root:
            path = root / "manifest.json"
            value = read_json(path)
            value["critical_vectors"][0]["mutations"] *= 2
            write_canonical_json(path, value)
            with self.assertRaises(noema.Refusal) as raised:
                noema.verify_specimen_corpus(path)
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_critical_vector_count_is_reported_as_seven(self):
        result = noema.verify_specimen_corpus(CORPUS_MANIFEST)
        self.assertEqual(result["counts"]["critical"], 7)


def _source_specimen_test(name, assertion):
    expected_paths = {
        "brevitas": "plugins/brevitas/skills/brevitas/SKILL.md",
        "fiat": "plugins/hexaemeron/skills/fiat/SKILL.md",
        "phylax": "plugins/hexaemeron/skills/phylax/SKILL.md",
        "sapheneia": "plugins/sapheneia/skills/sapheneia/SKILL.md",
    }

    def test(self):
        directory = specimen_directory(name)
        identity = read_json(directory / "source.json")
        raw = (ROOT / identity["path"]).read_bytes()
        spans = read_json(directory / "source-spans.json")
        graph = read_json(directory / "build.json")["graph"]
        if assertion == "path":
            self.assertEqual(identity["path"], expected_paths[name])
        elif assertion == "digest":
            self.assertEqual((identity["bytes"], identity["sha256"]), (len(raw), sha256(raw).hexdigest()))
        elif assertion == "governed":
            self.assertEqual(identity["governed"], {"start": 0, "end": len(raw)})
            self.assertEqual(spans["governed"], identity["governed"])
        elif assertion == "nodes":
            nodes = [item["node"] for item in spans["spans"] if item["kind"] == "node"]
            self.assertEqual(len(nodes), 10)
            self.assertEqual(len(set(nodes)), 10)
        elif assertion == "bindings":
            by_node = {
                record[1]: record[3]
                for record in graph["records"]
                if record[0] == "rule"
            }
            for item in spans["spans"]:
                if item["kind"] != "node":
                    continue
                binding = by_node[item["node"]]
                self.assertEqual((item["start"], item["end"]), (int(binding[3]), int(binding[4])))
                self.assertTrue(raw[item["start"]:item["end"]].decode("utf-8"))
        else:
            self.fail(f"unknown source assertion {assertion}")

    return test


for _specimen_name in SPECIMEN_NAMES:
    for _source_assertion in ("path", "digest", "governed", "nodes", "bindings"):
        setattr(
            SourceBindingTests,
            f"test_{_specimen_name}_{_source_assertion}",
            _source_specimen_test(_specimen_name, _source_assertion),
        )


def _specimen_round_trip_test(name, assertion):
    def test(self):
        directory = specimen_directory(name)
        build, _raw, artifacts = noema.load_build(
            directory / "build.json",
            directory / "modules",
            directory / "profile.json",
            directory / "kernel.noe",
        )
        profile = noema._decode_json(artifacts["profile"], "profile", canonical=True)
        if assertion == "source":
            self.assertEqual(
                (directory / "source.noe").read_bytes(),
                noema._canonical_source(build["graph"]["records"]),
            )
        elif assertion == "full_projection":
            projection = read_json(directory / "full-projection.json")
            self.assertEqual(noema.recover_projection(projection, profile), build["graph"])
        elif assertion == "slice":
            manifest, projection = noema._verify_manifest_path(directory / "manifest.json")
            self.assertEqual(manifest["projection_sha256"], sha256(projection["text"].encode()).hexdigest())
        elif assertion == "regeneration":
            outputs, _record, _plan, _results = noema._derive_specimen(directory, ROOT)
            for filename, payload in outputs.items():
                self.assertEqual((directory / filename).read_bytes(), payload)
        elif assertion == "answers":
            questions = read_json(directory / "questions.json")["questions"]
            answers = read_json(directory / "answers.json")["answers"]
            self.assertEqual(
                [(item["id"], item["expected"]) for item in questions],
                [(item["id"], item["result"]["output"]) for item in answers],
            )
        elif assertion == "rules":
            manifest = read_json(directory / "manifest.json")
            expected = {f"rule.{value}" for value in (
                "authorized", "blocked", "default", "defined", "exact",
                "negated", "ordered", "permit", "scoped", "unknown",
            )}
            self.assertTrue(expected <= set(manifest["included_ids"]))
        elif assertion == "lock":
            lock = read_json(directory / "lock.json")
            self.assertEqual(lock, build["lock"])
            self.assertEqual(lock["graph_sha256"], noema._value_sha256(build["graph"]))
        else:
            self.fail(f"unknown round-trip assertion {assertion}")

    return test


for _specimen_name in SPECIMEN_NAMES:
    for _round_trip_assertion in (
        "source", "full_projection", "slice", "regeneration", "answers", "rules", "lock",
    ):
        setattr(
            SpecimenRoundTripTests,
            f"test_{_specimen_name}_{_round_trip_assertion}_round_trip",
            _specimen_round_trip_test(_specimen_name, _round_trip_assertion),
        )


def _hostile_literal_test(kind):
    def test(self):
        directory = specimen_directory("brevitas")
        item = next(
            value
            for value in read_json(directory / "literals.json")["literals"]
            if value["kind"] == kind
        )
        self.assertEqual(item["bytes"], len(item["value"].encode("utf-8")))
        self.assertEqual(item["sha256"], sha256(item["value"].encode("utf-8")).hexdigest())
        manifest, _projection = noema._verify_manifest_path(directory / "manifest.json")
        if kind == "quote":
            result = noema.literal_runtime(item["id"], manifest)
            self.assertEqual(result["output"]["value"], item["value"])
        else:
            self.assertNotIn(item["id"], manifest["literals"])

    return test


for _hostile_kind in sorted(noema.LITERAL_KINDS):
    setattr(
        SpecimenRoundTripTests,
        f"test_hostile_{_hostile_kind}_literal_is_inert",
        _hostile_literal_test(_hostile_kind),
    )


def _mutation_category_test(category):
    def test(self):
        planned, outcome = mutation_index()[category]
        contract = noema.MUTATION_CONTRACTS[category]
        self.assertEqual((planned["kind"], planned["query"]), (contract["kind"], contract["query"]))
        self.assertEqual(outcome["status"], contract["status"])
        noema._validate_mutation_semantics(outcome, planned, f"test.{category}")

    return test


for _mutation_category in sorted(noema.MUTATION_CATEGORIES):
    setattr(
        MutationTests,
        f"test_category_{_mutation_category.replace('-', '_')}",
        _mutation_category_test(_mutation_category),
    )


def _critical_vector_test(identifier):
    def test(self):
        vectors = {
            item["id"]: item
            for item in read_json(CORPUS_MANIFEST)["critical_vectors"]
        }
        by_id = {
            planned["id"]: (planned, outcome)
            for planned, outcome in mutation_index().values()
        }
        represented = {by_id[value][0]["category"] for value in vectors[identifier]["mutations"]}
        self.assertTrue(represented)
        self.assertLessEqual(represented, set(noema.CRITICAL_VECTORS[identifier]))
        for value in vectors[identifier]["mutations"]:
            noema._validate_mutation_semantics(by_id[value][1], by_id[value][0], f"critical.{identifier}")

    return test


for _critical_identifier in sorted(noema.CRITICAL_VECTORS):
    setattr(
        CriticalVectorTests,
        f"test_vector_{_critical_identifier.replace('-', '_')}",
        _critical_vector_test(_critical_identifier),
    )


def _runtime_consequence_test(level, authorised):
    def test(self):
        effect = f"consequence{level}{'a' if authorised else 'u'}"
        consequence = [":", "core.consequence", str(level)]
        directive = [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", effect]]]
        authority = ()
        if authorised:
            directive = ["^", [":", "actor", "operator"], directive]
            authority = ("operator",)
        _build, manifest, _projection = select_records(
            base_records(directive),
            runtime_selection(effect, authority=authority),
        )
        result = noema.check_runtime(effect, [], manifest)
        expected = "permit" if level < 2 or authorised else "refuse"
        self.assertEqual((result["output"]["decision"], result["output"]["consequence"]), (expected, level))

    return test


for _level in range(4):
    for _authorised in (False, True):
        setattr(
            PolicyCheckTests,
            f"test_consequence_{_level}_{'authorised' if _authorised else 'unowned'}",
            _runtime_consequence_test(_level, _authorised),
        )


def _runtime_guard_test(operator, truth, expected):
    def test(self):
        effect = f"guard{operator == '/'}{truth}"
        proposition = ["core.checked", [":", "evidence", effect]]
        fact = checked_fact(proposition, truth, effect)
        consequence = [":", "core.consequence", "0"]
        directive = [
            operator,
            proposition,
            [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", effect]]],
        ]
        selection = runtime_selection(effect, facts=(fact,))
        _build, manifest, _projection = select_records(base_records(directive), selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual(result["output"]["decision"], expected)

    return test


for _operator, _truth, _expected in (
    ("?", "true", "permit"),
    ("?", "false", "refuse"),
    ("?", "unknown", "unknown"),
    ("/", "true", "refuse"),
    ("/", "false", "permit"),
    ("/", "unknown", "unknown"),
):
    setattr(
        PolicyCheckTests,
        f"test_{'when' if _operator == '?' else 'unless'}_{_truth}",
        _runtime_guard_test(_operator, _truth, _expected),
    )


def _exception_cannot_authorize_test(expiry, scope, checked):
    def test(self):
        evidence = [":", "evidence", "exception"]
        gate = ["core.checked", evidence]
        facts = (checked_fact(gate, "true", "exception"),) if checked else ()
        records = [
            ["import", "core", CORE_DIGEST],
            [
                "exception",
                "exception.only",
                [":", "actor", "admin"],
                gate,
                [":", "effect", "exceptional"],
                [":", "scope", scope],
                evidence,
                [":", "value", expiry],
                ["+", [":", "effect", "recover"]],
            ],
        ]
        selection = runtime_selection("exceptional", authority=("admin",), facts=facts)
        _build, manifest, _projection = select_records(records, selection)
        result = noema.check_runtime("exceptional", selection["facts"], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["reason"]), ("refuse", "invalid-exception"))

    return test


for _name, _expiry, _scope, _checked in (
    ("missing_evidence", "active", "repository", False),
    ("expired", "expired", "repository", True),
    ("over_broad", "active", "other", True),
):
    setattr(
        PolicyCheckTests,
        f"test_exception_{_name}_cannot_mint_authority",
        _exception_cannot_authorize_test(_expiry, _scope, _checked),
    )


def _separation_fact_test(label):
    def test(self):
        effect = f"separate.{label}"
        consequence = [":", "core.consequence", "3"]
        directive = [";", ["!", ["=", consequence, consequence]], ["+", [":", "effect", effect]]]
        if label == "authority":
            proposition = ["core.authorized", [":", "actor", "operator"], [":", "effect", effect]]
        else:
            proposition = ["core.checked", [":", "evidence", label]]
        fact = checked_fact(proposition, "true", label)
        selection = runtime_selection(effect, authority=("operator",), facts=(fact,))
        _build, manifest, _projection = select_records(base_records(directive), selection)
        result = noema.check_runtime(effect, selection["facts"], manifest)
        self.assertEqual((result["output"]["decision"], result["output"]["reason"]), ("refuse", "default-deny"))

    return test


for _separation in ("capability", "authority", "done", "receipt", "verification"):
    setattr(
        PolicyCheckTests,
        f"test_{_separation}_does_not_imply_effect_authority",
        _separation_fact_test(_separation),
    )


def _runtime_literal_kind_test(kind, value):
    def test(self):
        encoded = value.encode("utf-8")
        literal = ["literal", f"lit.{kind}", kind, str(len(encoded)), value]
        directive = [
            ";",
            ["!", ["=", ["$", f"lit.{kind}"], ["$", f"lit.{kind}"]]],
            ["+", [":", "effect", f"read.{kind}"]],
        ]
        records = base_records(directive, literals=[literal])
        _build, manifest, _projection = select_records(
            records,
            runtime_selection(f"read.{kind}"),
        )
        result = noema.literal_runtime(f"lit.{kind}", manifest)
        self.assertEqual((result["output"]["kind"], result["output"]["value"]), (kind, value))

    return test


for _runtime_kind, _runtime_value in {
    "id": "alpha",
    "path": "a/b",
    "sha256": "0" * 64,
    "command": "printf inert",
    "number": "123",
    "date": "2026-08-30",
    "url": "https://example.invalid/x",
    "quote": "say 'x'",
    "text": "plain text",
    "bytes": "00ff",
}.items():
    setattr(
        LiteralTests,
        f"test_runtime_literal_kind_{_runtime_kind}",
        _runtime_literal_kind_test(_runtime_kind, _runtime_value),
    )


def _transition_truth_test(truth, expected_status, expected_verdict):
    def test(self):
        proposition = ["core.checked", [":", "evidence", "gate"]]
        fact = checked_fact(proposition, truth, f"transition-{truth}")
        records = [
            ["import", "core", CORE_DIGEST],
            ["rule", "rule.move", ["+", [":", "effect", "move"]], source_binding()],
            ["transition", "transition.move", [":", "state", "machine"], [":", "state", "idle"], [":", "event", "go"], proposition, [":", "state", "ready"], ["+", [":", "effect", "move"]]],
        ]
        _build, manifest, _projection = select_records(
            records,
            runtime_selection("move", state="idle"),
        )
        result = noema.next_runtime("machine", "idle", "go", [fact], manifest)
        self.assertEqual((result["output"]["status"], result["verdict"]), (expected_status, expected_verdict))

    return test


for _truth, _status, _verdict in (
    ("true", "transition", "ok"),
    ("false", "stop", "ok"),
    ("unknown", "stop", "unknown"),
):
    setattr(
        TransitionTests,
        f"test_three_valued_guard_{_truth}",
        _transition_truth_test(_truth, _status, _verdict),
    )


def _literal_test(kind, value):
    def test(self):
        encoded = value.encode("utf-8")
        literal = ["literal", f"lit.{kind}", kind, str(len(encoded)), value]
        build, _artifacts = compile_records(base_records(literals=[literal]))
        self.assertEqual(build["graph"]["records"][1], literal)

    return test


for _kind, _value in {
    "id": "alpha",
    "path": "a/b",
    "sha256": "0" * 64,
    "command": "git status",
    "number": "123",
    "date": "2026-08-30",
    "url": "https://example.invalid/x",
    "quote": "say 'x'",
    "text": "plain text",
    "bytes": "00ff",
}.items():
    setattr(CanonicalSourceTests, f"test_literal_kind_{_kind}", _literal_test(_kind, _value))


def _core_type_test(type_name):
    def test(self):
        atom = [":", type_name, "x"]
        build, _artifacts = compile_records(base_records(["+", ["=", atom, atom]]))
        self.assertEqual(build["schema"], noema.BUILD_SCHEMA)

    return test


for _type_name in sorted(noema.CORE_TYPES):
    setattr(GraphValidationTests, f"test_core_type_{_type_name}", _core_type_test(_type_name))


def _operator_term(operator):
    proposition = ["core.ready", [":", "state", "ready"]]
    permit = ["+", proposition]
    atom = [":", "actor", "a"]
    finite = ["{}", "actor", atom]
    cases = {
        "!": ["!", proposition],
        "-": ["-", proposition],
        "+": permit,
        "?": ["?", proposition, permit],
        "/": ["/", proposition, permit],
        "@": ["@", [":", "scope", "repo"], permit],
        "^": ["^", [":", "actor", "owner"], permit],
        ";": [";", permit, ["-", proposition]],
        "&": ["+", ["&", proposition, proposition]],
        "|": ["+", ["|", proposition, proposition]],
        "~": ["+", ["~", proposition]],
        "=": ["+", ["=", atom, atom]],
        "=>": ["+", ["=>", proposition, proposition]],
        "all": ["+", ["all", ["x", "actor"], finite, ["=", ["%", "x"], atom]]],
        "any": ["+", ["any", ["x", "actor"], finite, ["=", ["%", "x"], atom]]],
        "one": ["+", ["one", ["x", "actor"], finite, ["=", ["%", "x"], atom]]],
        "in": ["+", ["in", atom, finite]],
        "subset": ["+", ["subset", finite, finite]],
        "lt": ["+", ["lt", [":", "value", "1"], [":", "value", "2"]]],
        "le": ["+", ["le", [":", "value", "1"], [":", "value", "2"]]],
        "gt": ["+", ["gt", [":", "value", "2"], [":", "value", "1"]]],
        "ge": ["+", ["ge", [":", "value", "2"], [":", "value", "1"]]],
        "count": ["+", ["=", ["count", finite], [":", "value", "1"]]],
    }
    return cases.get(operator)


def _operator_test(operator):
    def test(self):
        if operator == "<":
            definitions = [["definition", "local.order", [], ["<", [":", "state", "a"], [":", "state", "b"]]]]
            build, _artifacts = compile_records(base_records(definitions=definitions))
        else:
            build, _artifacts = compile_records(base_records(_operator_term(operator)))
        self.assertEqual(build["schema"], noema.BUILD_SCHEMA)

    return test


for _operator in sorted(noema.OPERATORS):
    safe_name = {"!": "require", "-": "prohibit", "+": "permit", "?": "when_true", "/": "when_false", "@": "scope", "^": "authority", ";": "sequence", "&": "and", "|": "or", "~": "not", "=": "equal", "=>": "implies", "<": "before"}.get(_operator, _operator)
    setattr(GraphValidationTests, f"test_operator_{safe_name}", _operator_test(_operator))


class ExternalAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = scratch_directory("noema-adapter-")
        self.directory = Path(self.temporary.name)
        self.executable = self.directory / "fake-adapter.py"
        write_bytes(self.executable, FAKE_ADAPTER_SOURCE)
        self.executable.chmod(0o700)
        self.ledger = self.directory / "budget.json"

    def tearDown(self):
        self.temporary.cleanup()

    def profile(self, mode="success", **changes):
        profile = fake_external_profile(self.executable, mode=mode)
        profile.update(changes)
        return profile

    def invoke(self, profile, *, prompt=b"bounded public input", mode="evaluation", budget="1"):
        return noema.invoke_adapter(
            profile,
            prompt,
            mode=mode,
            context_nonce="context.test",
            credential=None,
            budget=Decimal(budget),
            budget_ledger=self.ledger,
        )

    def profile_refusal(self, profile):
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_external_profile(
                profile,
                ROOT,
                "profile",
                verify_files=True,
            )
        return raised.exception

    def invoke_openrouter_child(self, request_raw, provider_response):
        credential = self.directory / "openrouter-key"
        write_bytes(credential, b"sk-or-v1-test-only-value\n")
        credential.chmod(0o600)

        class CaptureOpener:
            request = None

            def open(self, request, timeout):
                self.request = request
                self.timeout = timeout
                return io.BytesIO(provider_response)

        opener = CaptureOpener()
        stdin = mock.Mock()
        stdin.buffer = io.BytesIO(request_raw)
        stdout = mock.Mock()
        stdout.buffer = io.BytesIO()
        with (
            mock.patch.object(noema.sys, "stdin", stdin),
            mock.patch.object(noema.sys, "stdout", stdout),
            mock.patch.object(noema.urllib.request, "build_opener", return_value=opener),
            mock.patch.dict(
                noema.os.environ,
                {noema.OPENROUTER_KEY_PATH_ENV: str(credential)},
                clear=False,
            ),
        ):
            self.assertEqual(noema._openrouter_adapter(), 0)
        return opener, json.loads(stdout.buffer.getvalue())

    def invoke_refusal(self, mode, expected, **profile_changes):
        with self.assertRaises(noema.Refusal) as raised:
            self.invoke(self.profile(mode, **profile_changes))
        self.assertEqual(raised.exception.code, expected)

    def test_fake_profile_is_a_closed_valid_external_boundary(self):
        profile = self.profile()
        self.assertIs(
            noema._validate_external_profile(profile, ROOT, "profile", verify_files=True),
            profile,
        )

    def test_changed_executable_digest_refuses(self):
        profile = self.profile(executable_sha256="0" * 64)
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.EXECUTABLE_CHANGED")

    def test_changed_invocation_file_digest_refuses(self):
        profile = self.profile(
            invocation_files=[{"path": "scripts/noema.py", "sha256": "0" * 64}]
        )
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.EXECUTABLE_CHANGED")

    def test_exact_vocabulary_requires_digest(self):
        profile = self.profile(vocabulary_sha256=None)
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-TYPE.SHA256")

    def test_private_vocabulary_rejects_invented_digest(self):
        profile = self.profile(vocabulary_status="provider-private")
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-TOKENIZER.IDENTITY")

    def test_acquisition_digest_mismatch_refuses(self):
        profile = self.profile(acquisition_sha256="0" * 64)
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-DIGEST.ACQUISITION")

    def test_acquisition_vocabulary_mismatch_refuses(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        profile["acquisition"]["vocabulary_sha256"] = "1" * 64
        profile["acquisition_sha256"] = noema._value_sha256(profile["acquisition"])
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-EVALUATION.PROFILE")

    def test_acquisition_catalogue_identity_mismatch_refuses(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        profile["acquisition"]["endpoint_name"] = "another endpoint"
        profile["acquisition_sha256"] = noema._value_sha256(profile["acquisition"])
        self.assertEqual(
            self.profile_refusal(profile).code,
            "NOE-E-EVALUATION.PROFILE",
        )

    def test_provider_fallback_refuses(self):
        profile = self.profile()
        profile["provider_policy"] = copy.deepcopy(profile["provider_policy"])
        profile["provider_policy"]["allow_fallbacks"] = True
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PROVIDER_POLICY")

    def test_provider_collection_refuses(self):
        profile = self.profile()
        profile["provider_policy"] = copy.deepcopy(profile["provider_policy"])
        profile["provider_policy"]["data_collection"] = "allow"
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PROVIDER_POLICY")

    def test_provider_route_tag_change_refuses(self):
        profile = self.profile()
        profile["provider_policy"] = copy.deepcopy(profile["provider_policy"])
        profile["provider_policy"]["only"] = [profile["provider"]]
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PROVIDER_POLICY")

    def test_provider_price_ceiling_change_refuses(self):
        profile = self.profile()
        profile["provider_policy"] = copy.deepcopy(profile["provider_policy"])
        profile["provider_policy"]["max_price"]["completion"] = "2"
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PROVIDER_POLICY")

    def test_missing_request_price_refuses(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        del profile["acquisition"]["pricing"]["request"]
        profile["acquisition_sha256"] = noema._value_sha256(
            profile["acquisition"]
        )
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-TYPE.KEYS")

    def test_request_price_ceiling_change_refuses(self):
        profile = self.profile()
        profile["provider_policy"] = copy.deepcopy(profile["provider_policy"])
        profile["provider_policy"]["max_price"]["request"] = "0.1"
        self.assertEqual(
            self.profile_refusal(profile).code,
            "NOE-E-ADAPTER.PROVIDER_POLICY",
        )

    def test_missing_structured_output_support_refuses_evaluation_profile(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        profile["acquisition"]["supported_parameters"].remove("structured_outputs")
        profile["acquisition_sha256"] = noema._value_sha256(profile["acquisition"])
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PARAMETER")

    def test_missing_seed_support_refuses_evaluation_profile(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        profile["acquisition"]["supported_parameters"].remove("seed")
        profile["acquisition_sha256"] = noema._value_sha256(profile["acquisition"])
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PARAMETER")

    def test_missing_evaluation_seed_refuses(self):
        profile = self.profile()
        del profile["evaluation_seed"]
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-TYPE.KEYS")

    def test_changed_evaluation_seed_refuses(self):
        profile = self.profile(evaluation_seed=1)
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PARAMETER")

    def test_measurement_only_profile_requires_null_evaluation_seed(self):
        profile = fake_external_profile(self.executable, roles=("measurement",))
        self.assertIsNone(profile["evaluation_seed"])
        self.assertIs(
            noema._validate_external_profile(profile, ROOT, "profile", verify_files=True),
            profile,
        )
        profile["evaluation_seed"] = 0
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.PARAMETER")

    def test_adapter_request_applies_seed_only_to_evaluation(self):
        profile = self.profile()
        evaluation_raw, _evaluation_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="evaluation",
            context_nonce="context.evaluation",
        )
        measurement_raw, _measurement_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="measurement",
            context_nonce="context.measurement",
        )
        self.assertEqual(json.loads(evaluation_raw)["evaluation_seed"], 0)
        self.assertIsNone(json.loads(measurement_raw)["evaluation_seed"])

    def test_measurement_only_profile_cannot_invoke_evaluation(self):
        profile = fake_external_profile(self.executable, roles=("measurement",))
        with self.assertRaises(noema.Refusal) as raised:
            noema._adapter_request_bytes(
                profile,
                b"bounded public input",
                mode="evaluation",
                context_nonce="context.evaluation",
            )
        self.assertEqual(raised.exception.code, "NOE-E-ADAPTER.MODE")

    def test_openrouter_child_refuses_measurement_seed_leakage(self):
        profile = self.profile(
            adapter="noema-openrouter-chat/v1",
            endpoint=noema.OPENROUTER_ENDPOINT,
        )
        request_raw, _request_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="measurement",
            context_nonce="context.measurement",
        )
        request = json.loads(request_raw)
        request["evaluation_seed"] = 0
        stdin = mock.Mock()
        stdin.buffer = io.BytesIO(noema._canonical_json(request))
        stdout = mock.Mock()
        stdout.buffer = io.BytesIO()
        with (
            mock.patch.object(noema.sys, "stdin", stdin),
            mock.patch.object(noema.sys, "stdout", stdout),
        ):
            self.assertEqual(noema._openrouter_adapter(), 0)
        response = json.loads(stdout.buffer.getvalue())
        self.assertEqual(response["answer_code"], "NOE-E-ADAPTER.PARAMETER")
        self.assertEqual(response["status"], "unknown")

    def test_openrouter_child_sends_the_bound_evaluation_seed(self):
        profile = self.profile(
            adapter="noema-openrouter-chat/v1",
            endpoint=noema.OPENROUTER_ENDPOINT,
        )
        request_raw, _request_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="evaluation",
            context_nonce="context.evaluation",
        )
        provider_response = noema._canonical_json(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"answer_id":"answer.fake"}'},
                    }
                ],
                "id": "generation.test",
                "model": profile["model"],
                "provider": profile["provider"],
                "usage": {"completion_tokens": 1, "cost": "0.000001", "prompt_tokens": 8},
            }
        )

        opener, response = self.invoke_openrouter_child(request_raw, provider_response)
        self.assertIsNotNone(opener.request)
        self.assertEqual(json.loads(opener.request.data)["seed"], 0)
        self.assertEqual(response["status"], "recorded")

    def test_openrouter_child_normalises_malformed_provider_envelope(self):
        profile = self.profile(
            adapter="noema-openrouter-chat/v1",
            endpoint=noema.OPENROUTER_ENDPOINT,
        )
        request_raw, _request_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="evaluation",
            context_nonce="context.evaluation",
        )
        _opener, response = self.invoke_openrouter_child(request_raw, b"{}\n")
        self.assertEqual(response["answer_code"], "NOE-E-ADAPTER.RESPONSE")
        self.assertEqual(response["status"], "unknown")

    def test_openrouter_child_normalises_missing_token_accounting(self):
        profile = self.profile(
            adapter="noema-openrouter-chat/v1",
            endpoint=noema.OPENROUTER_ENDPOINT,
        )
        request_raw, _request_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="evaluation",
            context_nonce="context.evaluation",
        )
        provider_response = noema._canonical_json(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"answer_id":"answer.fake"}'},
                    }
                ],
                "id": "generation.test",
                "model": profile["model"],
                "provider": profile["provider"],
            }
        )
        _opener, response = self.invoke_openrouter_child(
            request_raw,
            provider_response,
        )
        self.assertEqual(response["answer_code"], "NOE-E-ADAPTER.RESPONSE")
        self.assertEqual(response["status"], "unknown")

    def test_openrouter_child_refuses_unbounded_provider_cost_exponent(self):
        profile = self.profile(
            adapter="noema-openrouter-chat/v1",
            endpoint=noema.OPENROUTER_ENDPOINT,
        )
        request_raw, _request_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="evaluation",
            context_nonce="context.evaluation",
        )
        provider_response = noema._canonical_json(
            {
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"content": '{"answer_id":"answer.fake"}'},
                    }
                ],
                "id": "generation.test",
                "model": profile["model"],
                "provider": profile["provider"],
                "usage": {
                    "completion_tokens": 1,
                    "cost": "1e1000000000",
                    "prompt_tokens": 8,
                },
            }
        ).replace(b'"1e1000000000"', b"1e1000000000")
        _opener, response = self.invoke_openrouter_child(request_raw, provider_response)
        self.assertEqual(response["answer_code"], "NOE-E-BOUNDS.DECIMAL")
        self.assertEqual(response["status"], "unknown")

    def test_provider_policy_requires_exact_json_number(self):
        self.assertEqual(
            noema._provider_json_number(Decimal("0.75"), "policy"),
            0.75,
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema._provider_json_number(
                Decimal("0.1000000000000000000000001"),
                "policy",
            )
        self.assertEqual(raised.exception.code, "NOE-E-ADAPTER.PROVIDER_POLICY")

    def test_openrouter_child_refuses_lossy_price_before_network(self):
        profile = self.profile(
            adapter="noema-openrouter-chat/v1",
            endpoint=noema.OPENROUTER_ENDPOINT,
        )
        request_raw, _request_digest = noema._adapter_request_bytes(
            profile,
            b"bounded public input",
            mode="evaluation",
            context_nonce="context.evaluation",
        )
        request = json.loads(request_raw)
        request["provider_policy"]["max_price"]["prompt"] = (
            "0.1000000000000000000000001"
        )
        opener, response = self.invoke_openrouter_child(
            noema._canonical_json(request),
            b"{}\n",
        )
        self.assertIsNone(opener.request)
        self.assertEqual(response["answer_code"], "NOE-E-ADAPTER.PROVIDER_POLICY")
        self.assertEqual(response["status"], "unknown")

    def test_provider_decimal_bounds_fixed_expansion_before_render(self):
        small = noema._provider_decimal(Decimal("1e-7"), "cost")
        self.assertEqual(noema._decimal_string(small), "0.0000001")
        self.assertEqual(
            noema._provider_decimal(Decimal("0e-1000000000"), "cost"),
            Decimal(0),
        )
        with self.assertRaises(noema.Refusal) as raised:
            noema._provider_decimal(Decimal("1e-1000000000"), "cost")
        self.assertEqual(raised.exception.code, "NOE-E-TYPE.DECIMAL")

    def test_environment_overlap_refuses(self):
        profile = self.profile(environment_allowlist=["NOEMA_FAKE_MODE"])
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.ENVIRONMENT")

    def test_local_adapter_cannot_receive_provider_credential_path(self):
        profile = self.profile(environment_allowlist=[noema.OPENROUTER_KEY_PATH_ENV])
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.ENVIRONMENT")

    def test_secret_shaped_argv_refuses(self):
        profile = self.profile(argv=["--api-key=value"])
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-ADAPTER.ARGV")

    def test_relative_executable_refuses(self):
        profile = self.profile(executable="fake-adapter.py")
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-PATH.EXECUTABLE")

    def test_unknown_family_refuses(self):
        profile = self.profile(family="same-provider-release")
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-EVALUATION.FAMILY")

    def test_unknown_role_refuses(self):
        profile = self.profile(roles=["authority"])
        self.assertEqual(self.profile_refusal(profile).code, "NOE-E-EVALUATION.PROFILE")

    def test_nonisolated_context_refuses(self):
        context = copy.deepcopy(self.profile()["context"])
        context["messages"] = 2
        self.assertEqual(self.profile_refusal(self.profile(context=context)).code, "NOE-E-EVALUATION.CONTEXT")

    def test_success_response_settles_budget(self):
        response = self.invoke(self.profile())
        self.assertEqual((response["status"], response["answer_id"]), ("recorded", "answer.fake"))
        ledger, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual((ledger["calls"], ledger["reservations"]), (1, []))

    def test_unknown_response_retains_conservative_reservation(self):
        response = self.invoke(self.profile("unknown"))
        self.assertEqual(response["status"], "unknown")
        ledger, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual(len(ledger["reservations"]), 1)

    def test_transient_unknown_retries_only_the_failed_invocation(self):
        state = self.directory / "retry-state"
        profile = self.profile()
        profile["fixed_environment"].update(
            NOEMA_FAKE_SEQUENCE="unknown,success",
            NOEMA_FAKE_STATE=str(state),
        )
        with mock.patch.object(noema.time, "sleep") as sleep:
            response, attempts = noema._invoke_adapter_with_retries(
                profile,
                b"bounded public input",
                mode="evaluation",
                context_nonce="context.retry",
                credential=None,
                budget=Decimal("1"),
                budget_ledger=self.ledger,
            )
        self.assertEqual(response["status"], "recorded")
        self.assertEqual(
            [(item["attempt"], item["status"]) for item in attempts],
            [(1, "unknown"), (2, "recorded")],
        )
        self.assertEqual(len({item["request_sha256"] for item in attempts}), 2)
        # Patching the shared time module can also observe subprocess wait
        # polling; count only the adapter's preregistered backoff.
        self.assertEqual(sleep.call_args_list.count(mock.call(1)), 1)
        ledger, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual((ledger["calls"], len(ledger["reservations"])), (1, 1))
        self.assertEqual(
            ledger["reservations"][0]["request_sha256"],
            attempts[0]["request_sha256"],
        )

    def test_transient_retry_exhaustion_is_bounded_and_conservative(self):
        state = self.directory / "retry-state"
        profile = self.profile()
        profile["fixed_environment"].update(
            NOEMA_FAKE_SEQUENCE="unknown,unknown,unknown",
            NOEMA_FAKE_STATE=str(state),
        )
        with mock.patch.object(noema.time, "sleep") as sleep:
            response, attempts = noema._invoke_adapter_with_retries(
                profile,
                b"bounded public input",
                mode="evaluation",
                context_nonce="context.retry",
                credential=None,
                budget=Decimal("1"),
                budget_ledger=self.ledger,
            )
        self.assertEqual(response["status"], "unknown")
        self.assertEqual([item["attempt"] for item in attempts], [1, 2, 3])
        self.assertEqual(sleep.call_args_list, [mock.call(1), mock.call(2)])
        ledger, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual((ledger["calls"], len(ledger["reservations"])), (0, 3))

    def test_independent_repeat_uses_a_fresh_bounded_ledger(self):
        state = self.directory / "repeat-state"
        profile = self.profile()
        profile["fixed_environment"].update(
            NOEMA_FAKE_SEQUENCE="unknown,success,success",
            NOEMA_FAKE_STATE=str(state),
        )
        second_ledger = self.directory / "second-budget.json"
        with mock.patch.object(noema.time, "sleep"):
            first, first_attempts = noema._invoke_adapter_with_retries(
                profile,
                b"bounded public input",
                mode="evaluation",
                context_nonce="context.repeat",
                credential=None,
                budget=Decimal("1"),
                budget_ledger=self.ledger,
            )
            second, second_attempts = noema._invoke_adapter_with_retries(
                profile,
                b"bounded public input",
                mode="evaluation",
                context_nonce="context.repeat",
                credential=None,
                budget=Decimal("1"),
                budget_ledger=second_ledger,
            )
        self.assertEqual((first["status"], second["status"]), ("recorded", "recorded"))
        self.assertEqual([item["attempt"] for item in first_attempts], [1, 2])
        self.assertEqual([item["attempt"] for item in second_attempts], [1])
        first_budget = noema._budget_record(self.ledger, Decimal("1"))
        second_budget = noema._budget_record(second_ledger, Decimal("1"))
        self.assertEqual(len(first_budget["reservations"]), 1)
        self.assertEqual((second_budget["calls"], second_budget["reservations"]), (1, []))

    def test_nonretryable_unknown_stops_after_one_attempt(self):
        profile = self.profile("policy-unknown")
        with mock.patch.object(noema.time, "sleep") as sleep:
            response, attempts = noema._invoke_adapter_with_retries(
                profile,
                b"bounded public input",
                mode="evaluation",
                context_nonce="context.retry",
                credential=None,
                budget=Decimal("1"),
                budget_ledger=self.ledger,
            )
        self.assertEqual(response["answer_code"], "NOE-E-ADAPTER.PROVIDER_POLICY")
        self.assertEqual(len(attempts), 1)
        sleep.assert_not_called()

    def test_local_attempt_refusal_retains_the_exact_request_binding(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._invoke_adapter_with_retries(
                self.profile("wrong-request"),
                b"bounded public input",
                mode="evaluation",
                context_nonce="context.retry",
                credential=None,
                budget=Decimal("1"),
                budget_ledger=self.ledger,
            )
        attempts = raised.exception.attempts
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.ADAPTER")
        self.assertEqual(len(attempts), 1)
        self.assertEqual(attempts[0]["answer_code"], raised.exception.code)
        self.assertEqual(attempts[0]["status"], "refused")

    def test_malformed_response_refuses(self):
        self.invoke_refusal("malformed", "NOE-E-SYNTAX.JSON")

    def test_duplicate_json_key_refuses(self):
        self.invoke_refusal("duplicate-json", "NOE-E-SYNTAX.DUPLICATE_KEY")

    def test_noncanonical_response_refuses(self):
        self.invoke_refusal("noncanonical", "NOE-E-SYNTAX.CANONICAL")

    def test_extra_response_field_refuses(self):
        self.invoke_refusal("extra-field", "NOE-E-TYPE.KEYS")

    def test_response_code_outside_closed_alphabet_refuses(self):
        self.invoke_refusal("invalid-code", "NOE-E-ADAPTER.RESPONSE")

    def test_unknown_response_cannot_invent_accounting(self):
        self.invoke_refusal("invented-unknown", "NOE-E-ADAPTER.RESPONSE")

    def test_negative_token_count_refuses(self):
        self.invoke_refusal("negative-count", "NOE-E-BOUNDS.INTEGER")

    def test_fractional_token_count_refuses(self):
        self.invoke_refusal("float-count", "NOE-E-BOUNDS.INTEGER")

    def test_boolean_token_count_refuses(self):
        self.invoke_refusal("bool-count", "NOE-E-BOUNDS.INTEGER")

    def test_cross_request_response_refuses(self):
        self.invoke_refusal("wrong-request", "NOE-E-DIGEST.ADAPTER")

    def test_changed_model_identity_refuses(self):
        self.invoke_refusal("wrong-model", "NOE-E-ADAPTER.IDENTITY_CHANGED")
        ledger, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual((ledger["calls"], ledger["reservations"]), (1, []))

    def test_changed_provider_identity_refuses(self):
        self.invoke_refusal("wrong-provider", "NOE-E-ADAPTER.IDENTITY_CHANGED")

    def test_secret_shaped_answer_refuses(self):
        self.invoke_refusal("secret-answer", "NOE-E-EVALUATION.SECRET_OUTPUT")

    def test_success_without_answer_refuses(self):
        self.invoke_refusal("null-answer", "NOE-E-EVALUATION.ANSWER")

    def test_child_exit_refuses_as_unavailable(self):
        self.invoke_refusal("exit", "NOE-E-ADAPTER.UNAVAILABLE")

    def test_timeout_kills_the_process_group(self):
        self.invoke_refusal("timeout", "NOE-E-ADAPTER.TIMEOUT", timeout_seconds=1)

    def test_stdout_cap_refuses(self):
        self.invoke_refusal("stdout-cap", "NOE-E-ADAPTER.OUTPUT_CAP")

    def test_stderr_cap_refuses(self):
        self.invoke_refusal("stderr-cap", "NOE-E-ADAPTER.OUTPUT_CAP")

    def test_provider_cost_above_reservation_refuses(self):
        self.invoke_refusal("high-cost", "NOE-E-BUDGET.OVERRUN")
        ledger, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual((ledger["calls"], ledger["spent_usd"], ledger["reservations"]), (1, "0.9", []))
        self.assertEqual(ledger["breach"]["reason"], "reservation-exceeded")
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_reserve(
                self.ledger,
                Decimal("1"),
                "f" * 64,
                Decimal("0.01"),
            )
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.BREACH")

    def test_provider_output_above_requested_bound_refuses(self):
        self.invoke_refusal("output-overrun", "NOE-E-ADAPTER.PARAMETER")
        ledger, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual((ledger["calls"], ledger["reservations"]), (1, []))

    def test_budget_reserve_and_finalize_are_atomic(self):
        request = "a" * 64
        noema._budget_reserve(self.ledger, Decimal("1"), request, Decimal("0.2"))
        noema._budget_finalize(self.ledger, Decimal("1"), request, Decimal("0.1"))
        ledger = noema._budget_record(self.ledger, Decimal("1"))
        self.assertEqual((ledger["calls"], ledger["spent_usd"], ledger["reservations"]), (1, "0.1", []))

    def test_budget_refuses_request_past_ceiling(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_reserve(self.ledger, Decimal("0.1"), "b" * 64, Decimal("0.1000001"))
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.LIMIT")

    def test_live_command_requires_explicit_budget_authority(self):
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_arguments(
                argparse.Namespace(
                    budget_ledger=self.ledger,
                    budget_usd=None,
                )
            )
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.AUTHORITY")

    def test_budget_refuses_duplicate_unresolved_request(self):
        noema._budget_reserve(self.ledger, Decimal("1"), "c" * 64, Decimal("0.1"))
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_reserve(self.ledger, Decimal("1"), "c" * 64, Decimal("0.1"))
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.DUPLICATE")

    def test_budget_refuses_tampered_overcommit(self):
        record = {
            "breach": None,
            "budget_usd": "1",
            "calls": 0,
            "reservations": [{"estimated_usd": "0.6", "request_sha256": "d" * 64}],
            "schema": noema.BUDGET_LEDGER_SCHEMA,
            "spent_usd": "0.5",
        }
        write_canonical_json(self.ledger, record)
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_record(self.ledger, Decimal("1"))
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.LEDGER")

    def test_budget_refuses_overcommit_hidden_by_decimal_context_rounding(self):
        record = {
            "breach": None,
            "budget_usd": "1",
            "calls": 0,
            "reservations": [
                {
                    "estimated_usd": "0.00000000000000000000000000006",
                    "request_sha256": "e" * 64,
                }
            ],
            "schema": noema.BUDGET_LEDGER_SCHEMA,
            "spent_usd": "0.99999999999999999999999999995",
        }
        write_canonical_json(self.ledger, record)
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_record(self.ledger, Decimal("1"))
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.LEDGER")

    def test_budget_refuses_combined_call_and_reservation_overflow(self):
        record = {
            "breach": None,
            "budget_usd": "1",
            "calls": noema.MAX_BUDGET_CALLS,
            "reservations": [
                {"estimated_usd": "0", "request_sha256": "e" * 64}
            ],
            "schema": noema.BUDGET_LEDGER_SCHEMA,
            "spent_usd": "0",
        }
        write_canonical_json(self.ledger, record)
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_record(self.ledger, Decimal("1"))
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.LEDGER")

    def test_budget_refuses_reservation_at_call_cap(self):
        record = {
            "breach": None,
            "budget_usd": "1",
            "calls": noema.MAX_BUDGET_CALLS,
            "reservations": [],
            "schema": noema.BUDGET_LEDGER_SCHEMA,
            "spent_usd": "0",
        }
        write_canonical_json(self.ledger, record)
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_reserve(
                self.ledger,
                Decimal("1"),
                "e" * 64,
                Decimal("0.1"),
            )
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.LIMIT")

    def test_budget_migrates_legacy_ledger_on_next_write(self):
        record = {
            "budget_usd": "1",
            "calls": 0,
            "reservations": [],
            "schema": noema.LEGACY_BUDGET_LEDGER_SCHEMA,
            "spent_usd": "0",
        }
        write_canonical_json(self.ledger, record)
        noema._budget_reserve(
            self.ledger,
            Decimal("1"),
            "e" * 64,
            Decimal("0.1"),
        )
        migrated, _raw = noema._read_canonical_json(self.ledger, "ledger")
        self.assertEqual(migrated["schema"], noema.BUDGET_LEDGER_SCHEMA)
        self.assertIsNone(migrated["breach"])

    def test_budget_missing_parent_refuses_without_traceback(self):
        missing = self.directory / "missing" / "budget.json"
        with self.assertRaises(noema.Refusal) as raised:
            noema._budget_reserve(
                missing,
                Decimal("1"),
                "e" * 64,
                Decimal("0.1"),
            )
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.LOCK")

    def test_budget_lock_serialises_parallel_reservations_and_settlements(self):
        requests = [f"{index:064x}" for index in range(24)]
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(
                pool.map(
                    lambda request: noema._budget_reserve(
                        self.ledger,
                        Decimal("10"),
                        request,
                        Decimal("0.1"),
                    ),
                    requests,
                )
            )
        record = noema._budget_record(self.ledger, Decimal("10"))
        self.assertEqual(len(record["reservations"]), len(requests))
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(
                pool.map(
                    lambda request: noema._budget_finalize(
                        self.ledger,
                        Decimal("10"),
                        request,
                        Decimal("0.05"),
                    ),
                    requests,
                )
            )
        record = noema._budget_record(self.ledger, Decimal("10"))
        self.assertEqual((record["calls"], record["spent_usd"], record["reservations"]), (24, "1.2", []))

    def test_cost_bound_is_above_byte_worst_case_and_completion(self):
        profile = self.profile()
        bound = noema._request_cost_bound(profile, b"x" * 1000, 64)
        expected = Decimal(1000 + 4096 + 64) * Decimal("0.000001")
        self.assertGreater(bound, expected)

    def test_cost_bound_reserves_the_per_request_price(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        profile["acquisition"]["pricing"]["request"] = "0.25"
        bound = noema._request_cost_bound(profile, b"", 1)
        self.assertGreaterEqual(bound, Decimal("0.2625"))

    def test_conservative_prompt_bound_refuses_endpoint_overflow(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        profile["acquisition"]["max_prompt_tokens"] = 4096
        profile["acquisition_sha256"] = noema._value_sha256(profile["acquisition"])
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_request_capacity(profile, b"x", 1)
        self.assertEqual(raised.exception.code, "NOE-E-ADAPTER.INPUT_CAP")

    def test_unauthorised_pricing_override_refuses_before_spend(self):
        profile = self.profile()
        profile["acquisition"] = copy.deepcopy(profile["acquisition"])
        profile["acquisition"]["pricing_overrides"] = [
            {
                "completion": "0.000002",
                "min_prompt_tokens": 1,
                "prompt": "0.000002",
            }
        ]
        profile["acquisition_sha256"] = noema._value_sha256(profile["acquisition"])
        with self.assertRaises(noema.Refusal) as raised:
            noema._validate_request_capacity(profile, b"x", 1)
        self.assertEqual(raised.exception.code, "NOE-E-BUDGET.PRICE_TIER")

    def test_private_credential_file_mode_is_required(self):
        credential = self.directory / "key"
        write_bytes(credential, b"sk-or-v1-test-only-value\n")
        credential.chmod(0o644)
        with self.assertRaises(noema.Refusal) as raised:
            noema._credential_path(credential)
        self.assertEqual(raised.exception.code, "NOE-E-ADAPTER.CREDENTIAL")

    def test_openrouter_child_requires_isolated_python(self):
        profiles = read_json(MEASUREMENT_PROFILES)["profiles"]
        self.assertTrue(profiles)
        self.assertEqual(
            {tuple(profile["argv"]) for profile in profiles},
            {("-I", "scripts/noema.py", "_openrouter-adapter")},
        )

    def test_live_evaluation_profiles_use_the_bounded_reasoning_ceiling(self):
        profiles = read_json(MEASUREMENT_PROFILES)["profiles"]
        evaluation = [
            profile for profile in profiles if "evaluation" in profile["roles"]
        ]
        self.assertEqual(len(evaluation), 2)
        self.assertEqual(
            {profile["evaluation_output_tokens"] for profile in evaluation},
            {2048},
        )
        self.assertEqual({profile["evaluation_seed"] for profile in evaluation}, {0})
        self.assertTrue(
            all("seed" in profile["acquisition"]["supported_parameters"] for profile in evaluation)
        )

    def test_clean_git_identity_rejects_untracked_bytes(self):
        repository = self.directory / "repository"
        repository.mkdir()
        write_bytes(repository / "tracked.txt", b"tracked\n")
        commands = (
            ["/usr/bin/git", "init", "--quiet", str(repository)],
            ["/usr/bin/git", "-C", str(repository), "add", "tracked.txt"],
            [
                "/usr/bin/git",
                "-C",
                str(repository),
                "-c",
                "user.name=Noema Test",
                "-c",
                "user.email=noema@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "fixture",
            ],
        )
        for command in commands:
            subprocess.run(command, check=True, capture_output=True, env={})
        noema._git_identity(repository, require_clean=True)
        write_bytes(repository / "shadow.py", b"raise RuntimeError('shadowed')\n")
        with self.assertRaises(noema.Refusal) as raised:
            noema._git_identity(repository, require_clean=True)
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.TREE")


class MeasurementEvaluationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = scratch_directory("noema-measure-evaluation-")
        cls.directory = Path(cls.temporary.name)
        cls.executable = cls.directory / "fake-adapter.py"
        write_bytes(cls.executable, FAKE_ADAPTER_SOURCE)
        cls.executable.chmod(0o700)
        cls.profile_path = cls.directory / "profiles.json"
        write_canonical_json(cls.profile_path, fake_profile_set(cls.executable))
        cls.profile_record, cls.profile_raw, cls.profiles = noema.load_external_profiles(
            cls.profile_path,
            require_measurement_families=True,
        )
        cls.corpus_root = cls.directory / "corpus"
        shutil.copytree(NOEMA_FIXTURES, cls.corpus_root)
        cls.manifest = cls.corpus_root / "manifest.json"
        corpus = read_json(cls.manifest)
        corpus.pop("evidence", None)
        write_canonical_json(cls.manifest, corpus)
        cls.verified = noema.verify_specimen_corpus(cls.manifest)
        cls.documents = noema._measurement_documents(cls.manifest, cls.verified)
        cls.measurement, cls.measurement_success = noema.measure_corpus(
            cls.manifest,
            cls.profile_path,
            credential=None,
            budget=Decimal("5"),
            budget_ledger=cls.directory / "measurement-budget.json",
        )
        cls.packet_directory = cls.directory / "packet"
        noema.emit_evaluation_packet(
            cls.manifest,
            cls.profile_path,
            cls.packet_directory,
        )
        cls.packet, cls.packet_raw = noema._load_packet(
            cls.packet_directory / "manifest.json"
        )
        cls.answers = valid_evaluation_answers(cls.packet, cls.packet_raw)

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def validate_measurement(self, value):
        corpus = self.verified["manifest"]
        return noema._validate_measurement_report(
            value,
            corpus_sha256=noema._value_sha256(noema._corpus_identity_value(corpus)),
            counts=self.verified["counts"],
            profile_record=self.profile_record,
            profile_raw=self.profile_raw,
            profiles=self.profiles,
            documents=self.documents,
            repository_commit=self.measurement["repository_commit"],
            repository_tree=self.measurement["repository_tree"],
        )

    def measurement_refusal(self, value):
        with self.assertRaises(noema.Refusal) as raised:
            self.validate_measurement(value)
        return raised.exception

    def unknown_measurement_profile(self, recorded, attempts, refusal_code):
        identity_names = {
            "acquisition_sha256",
            "family",
            "id",
            "model",
            "profile_sha256",
            "provider",
            "tokenizer",
            "vocabulary_sha256",
            "vocabulary_status",
        }
        unknown = {name: recorded[name] for name in identity_names}
        unknown.update(
            attempts=attempts,
            refusal_code=refusal_code,
            status="unknown",
            unknowns=["counts"],
        )
        return unknown

    def answers_file(self, value):
        path = self.directory / ("answers-" + os.urandom(8).hex() + ".json")
        write_canonical_json(path, value)
        return path

    @contextlib.contextmanager
    def copied_packet(self):
        with scratch_directory("noema-packet-copy-") as temporary:
            target = Path(temporary) / "packet"
            shutil.copytree(self.packet_directory, target)
            yield target

    def test_fake_measurement_crosses_all_four_unlike_profiles(self):
        self.assertTrue(self.measurement_success)
        checked, accepted = self.validate_measurement(self.measurement)
        self.assertTrue(accepted)
        self.assertEqual(checked["summary"]["measured_profiles"], 4)

    def test_fake_measurement_recovers_one_transient_invocation_in_place(self):
        profile = copy.deepcopy(self.profiles[0])
        state = self.directory / "measurement-retry-state"
        profile["fixed_environment"].update(
            NOEMA_FAKE_SEQUENCE="unknown,success",
            NOEMA_FAKE_STATE=str(state),
        )
        attempts = []
        ledger = self.directory / "measurement-retry-budget.json"
        with mock.patch.object(noema.time, "sleep") as sleep:
            result = noema._measure_one_profile(
                profile,
                self.documents,
                credential=None,
                budget=Decimal("5"),
                budget_ledger=ledger,
                attempt_log=attempts,
            )
        plan = noema._measurement_invocation_plan(profile, self.documents)
        self.assertEqual(result["status"], "recorded")
        self.assertEqual(len(attempts), len(plan) + 1)
        self.assertEqual(
            [(item["attempt"], item["status"]) for item in attempts[:3]],
            [(1, "unknown"), (2, "recorded"), (1, "recorded")],
        )
        sleep.assert_called_once_with(1)
        budget = noema._budget_record(ledger, Decimal("5"))
        self.assertEqual((budget["calls"], len(budget["reservations"])), (len(plan), 1))

    def test_fake_measurement_preserves_bounded_terminal_attempts(self):
        profile = copy.deepcopy(self.profiles[0])
        state = self.directory / "measurement-exhaustion-state"
        profile["fixed_environment"].update(
            NOEMA_FAKE_SEQUENCE="unknown,unknown,unknown",
            NOEMA_FAKE_STATE=str(state),
        )
        attempts = []
        ledger = self.directory / "measurement-exhaustion-budget.json"
        with (
            mock.patch.object(noema.time, "sleep"),
            self.assertRaises(noema.Refusal) as raised,
        ):
            noema._measure_one_profile(
                profile,
                self.documents,
                credential=None,
                budget=Decimal("5"),
                budget_ledger=ledger,
                attempt_log=attempts,
            )
        self.assertEqual(raised.exception.code, "NOE-E-ADAPTER.REMOTE")
        self.assertEqual([item["attempt"] for item in attempts], [1, 2, 3])
        budget = noema._budget_record(ledger, Decimal("5"))
        self.assertEqual((budget["calls"], len(budget["reservations"])), (0, 3))

    def test_recorded_measurement_attempt_cannot_claim_a_refusal(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["attempts"][-1]["answer_code"] = (
            "NOE-E-ADAPTER.HTTP_502"
        )
        self.assertEqual(
            self.measurement_refusal(value).code,
            "NOE-E-MEASURE.UNKNOWN",
        )

    def test_unknown_measurement_refusal_binds_its_terminal_attempt(self):
        value = copy.deepcopy(self.measurement)
        recorded = value["profiles"][0]
        attempt = copy.deepcopy(recorded["attempts"][0])
        attempt.update(
            answer_code="NOE-E-ADAPTER.PROVIDER_POLICY",
            status="unknown",
        )
        value["profiles"][0] = self.unknown_measurement_profile(
            recorded,
            [attempt],
            "NOE-E-ADAPTER.CREDENTIAL",
        )
        self.assertEqual(
            self.measurement_refusal(value).code,
            "NOE-E-MEASURE.UNKNOWN",
        )

    def test_unknown_measurement_cannot_omit_attempt_provenance(self):
        value = copy.deepcopy(self.measurement)
        recorded = value["profiles"][0]
        value["profiles"][0] = self.unknown_measurement_profile(
            recorded,
            [],
            "NOE-E-ADAPTER.CREDENTIAL",
        )
        self.assertEqual(
            self.measurement_refusal(value).code,
            "NOE-E-BOUNDS.ATTEMPTS",
        )

    def test_transient_measurement_exhaustion_is_a_valid_unknown_report(self):
        value = copy.deepcopy(self.measurement)
        recorded = value["profiles"][0]
        bindings = noema._adapter_request_attempt_bindings(
            self.profiles[0],
            noema._measurement_prompt(b""),
            mode="measurement",
            context_nonce=f"measure.{self.profiles[0]['id']}.transport",
        )
        attempts = [
            {
                "answer_code": "NOE-E-ADAPTER.HTTP_502",
                "attempt": binding["attempt"],
                "context_nonce": binding["context_nonce"],
                "request_sha256": binding["sha256"],
                "status": "unknown",
            }
            for binding in bindings
        ]
        value["profiles"][0] = self.unknown_measurement_profile(
            recorded,
            attempts,
            "NOE-E-ADAPTER.HTTP_502",
        )
        value["summary"].update(
            measured_profiles=3,
            status="unknown",
            unknown_profiles=1,
        )
        checked, accepted = self.validate_measurement(value)
        self.assertFalse(accepted)
        self.assertEqual(checked["summary"]["unknown_profiles"], 1)

    def test_post_response_measurement_refusal_is_a_valid_unknown_report(self):
        value = copy.deepcopy(self.measurement)
        recorded = value["profiles"][0]
        value["profiles"][0] = self.unknown_measurement_profile(
            recorded,
            [copy.deepcopy(recorded["attempts"][0])],
            "NOE-E-TOKENIZER.COUNT",
        )
        value["summary"].update(
            measured_profiles=3,
            status="unknown",
            unknown_profiles=1,
        )
        _checked, accepted = self.validate_measurement(value)
        self.assertFalse(accepted)

    def test_public_schema_names_every_emitted_step_five_field(self):
        definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]

        def closed(name, value):
            definition = definitions[name]
            self.assertLessEqual(set(definition["required"]), set(value), name)
            self.assertLessEqual(set(value), set(definition["properties"]), name)

        self.assertEqual(definitions["adapterAttemptLog"]["minItems"], 1)
        closed("externalProfiles", self.profile_record)
        for profile in self.profiles:
            closed("externalProfile", profile)
            closed("externalAcquisition", profile["acquisition"])
            closed("providerPolicy", profile["provider_policy"])
        closed("measurement", self.measurement)
        for profile in self.measurement["profiles"]:
            closed("recordedMeasurementProfile", profile)
            for attempt in profile["attempts"]:
                closed("adapterAttempt", attempt)
            closed("measurementTransport", profile["transport"])
            closed("measurementTotals", profile["totals"])
            for observation in profile["observations"]:
                closed("measurementObservation", observation)
            for document in profile["documents"]:
                closed("measurementDocument", document)
                closed("measurementComponents", document["components"])
                for component in document["components"].values():
                    closed("measuredComponent", component)
                for gate in document["gates"].values():
                    closed("ratio", gate)
            for amortised in profile["amortised"]:
                closed("measurementAmortised", amortised)
        closed("evaluationPacket", self.packet)
        for profile in self.packet["family_profiles"]:
            closed("evaluationFamilyProfile", profile)
        for case in self.packet["cases"]:
            closed("evaluationCase", case)
            closed("evaluationRuntimeContext", case["runtime_context"])
            for fact in case["runtime_context"]["facts"]:
                closed("evaluationFactContext", fact)
            for candidate in case["candidate_answers"]:
                closed("evaluationCandidate", candidate)
                closed("answerView", candidate["value"])
            for prompt in case["prompts"]:
                closed("evaluationPrompt", prompt)
                for request in prompt["requests"]:
                    for attempt in request["attempts"]:
                        closed("adapterRequestAttempt", attempt)
        closed("evaluationAnswers", self.answers)
        for answer in self.answers["answers"]:
            closed("evaluationAnswer", answer)
            closed("answerProvenance", answer["provenance"])
            for attempt in answer["provenance"]["attempts"]:
                closed("adapterAttempt", attempt)
        report, _success = noema._tally_evaluation_values(
            self.packet,
            self.packet_raw,
            self.answers,
            noema._canonical_json(self.answers),
        )
        closed("evaluationReport", report)

    def test_public_schema_accepts_module_lock_identifiers(self):
        definitions = json.loads(SCHEMA.read_text(encoding="utf-8"))["$defs"]
        self.assertEqual(
            definitions["moduleLock"]["properties"]["id"],
            {"$ref": "#/$defs/identifier"},
        )
        runtime_lock = read_json(RUNTIME_FIXTURE / "build.json")["lock"]
        self.assertTrue(runtime_lock["modules"])
        self.assertTrue(all(item["id"] == "core" for item in runtime_lock["modules"]))
        for directory in (specimen_directory(name) for name in SPECIMEN_NAMES):
            lock = read_json(directory / "lock.json")
            self.assertTrue(lock["modules"])
            self.assertTrue(all(item["id"] == "core" for item in lock["modules"]))

    def test_measurement_component_omission_refuses(self):
        value = copy.deepcopy(self.measurement)
        del value["profiles"][0]["documents"][0]["components"]["alias_dictionary"]
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-TYPE.KEYS")

    def test_measurement_requires_byte_identical_shared_amortisation_components(self):
        for name in ("kernel", "alias_dictionary"):
            with self.subTest(component=name):
                documents = copy.deepcopy(self.documents)
                documents[1][name] += b"x"
                with mock.patch.object(
                    noema,
                    "invoke_adapter",
                    side_effect=AssertionError(
                        "adapter called before component validation"
                    ),
                ) as invoke:
                    with self.assertRaises(noema.Refusal) as raised:
                        noema._measure_one_profile(
                            self.profiles[0],
                            documents,
                            credential=None,
                            budget=Decimal("5"),
                            budget_ledger=(
                                self.directory / f"shared-{name}-budget.json"
                            ),
                        )
                self.assertEqual(
                    raised.exception.code,
                    "NOE-E-MEASURE.COMPONENT",
                )
                invoke.assert_not_called()
                with self.assertRaises(noema.Refusal) as replayed:
                    noema._validate_measurement_report(
                        self.measurement,
                        corpus_sha256=noema._value_sha256(
                            noema._corpus_identity_value(
                                self.verified["manifest"]
                            )
                        ),
                        counts=self.verified["counts"],
                        profile_record=self.profile_record,
                        profile_raw=self.profile_raw,
                        profiles=self.profiles,
                        documents=documents,
                        repository_commit=self.measurement["repository_commit"],
                        repository_tree=self.measurement["repository_tree"],
                    )
                self.assertEqual(
                    replayed.exception.code,
                    "NOE-E-MEASURE.COMPONENT",
                )

    def test_measurement_dictionary_undercount_refuses(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["documents"][0]["components"]["alias_dictionary"]["tokens"] -= 1
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-TOKENIZER.COUNT")

    def test_measurement_transport_change_refuses(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["transport"]["input_tokens"] += 1
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-TOKENIZER.COUNT")

    def test_measurement_transport_binds_the_fixed_inert_wrapper(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["transport"]["prompt_sha256"] = "0" * 64
        self.assertEqual(
            self.measurement_refusal(value).code,
            "NOE-E-DIGEST.MEASUREMENT",
        )

    def test_measurement_source_must_precede_projection_counts(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["source_baseline_sequence"] = 1
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-MEASURE.BASELINE")

    def test_measurement_source_baseline_boundary_cannot_include_projection(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["source_baseline_sequence"] += 1
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-MEASURE.BASELINE")

    def test_measurement_unreferenced_observation_refuses(self):
        value = copy.deepcopy(self.measurement)
        profile = value["profiles"][0]
        observation = copy.deepcopy(profile["observations"][-1])
        observation.update(
            generation_id="generation.extra",
            request_sha256="e" * 64,
            sequence=len(profile["observations"]) + 1,
            sha256="f" * 64,
        )
        observation["observation_sha256"] = noema._value_sha256(
            {key: item for key, item in observation.items() if key != "observation_sha256"}
        )
        profile["observations"].append(observation)
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-MEASURE.COMPONENT")

    def test_measurement_profile_gate_uses_the_declared_corpus(self):
        value = copy.deepcopy(self.measurement["profiles"][0])
        self.assertTrue(noema._measurement_profile_passes(value))
        value["gates"]["steady_state"]["passes"] = False
        self.assertFalse(noema._measurement_profile_passes(value))

    def test_measurement_profile_family_change_refuses_unlike_cohort(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["family"] = value["profiles"][1]["family"]
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-MEASURE.COHORT")

    def test_measurement_summary_is_recomputed(self):
        value = copy.deepcopy(self.measurement)
        value["summary"]["measured_profiles"] = 3
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-DIGEST.MEASUREMENT")

    def test_measurement_observation_digest_is_recomputed(self):
        value = copy.deepcopy(self.measurement)
        value["profiles"][0]["observations"][0]["observation_sha256"] = "0" * 64
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-DIGEST.MEASUREMENT")

    def test_measurement_observation_binds_the_exact_adapter_request(self):
        value = copy.deepcopy(self.measurement)
        profile = value["profiles"][0]
        observation = profile["observations"][0]
        old_digest = observation["observation_sha256"]
        observation["request_sha256"] = "f" * 64
        observation["observation_sha256"] = noema._value_sha256(
            {
                key: item
                for key, item in observation.items()
                if key != "observation_sha256"
            }
        )
        new_digest = observation["observation_sha256"]
        for document in profile["documents"]:
            for component in document["components"].values():
                if component["observation_sha256"] == old_digest:
                    component["observation_sha256"] = new_digest
        for amortised in profile["amortised"]:
            for component in (amortised["source"], amortised["first_use"]):
                if component["observation_sha256"] == old_digest:
                    component["observation_sha256"] = new_digest
        self.assertEqual(self.measurement_refusal(value).code, "NOE-E-DIGEST.ADAPTER")

    def test_measurement_gate_boundary_is_integer_exact(self):
        self.assertTrue(noema._ratio(7, 10, 70)["passes"])
        self.assertFalse(noema._ratio(701, 1000, 70)["passes"])

    def test_measure_command_replays_anchored_evidence_without_adapter_calls(self):
        report = copy.deepcopy(self.measurement)
        raw = noema._canonical_json(report)
        arguments = argparse.Namespace(
            budget_ledger=self.directory / "unused-budget.json",
            budget_usd=None,
            credential_file=None,
            manifest=self.manifest,
            output=self.directory / "replayed-measurement.json",
            profiles=self.profile_path,
        )
        with (
            mock.patch.object(noema, "_recorded_measurement", return_value=(report, raw)),
            mock.patch.object(noema, "measure_corpus") as live_measure,
        ):
            result, success = noema._measure_command(arguments)
        self.assertTrue(success)
        live_measure.assert_not_called()
        self.assertEqual(arguments.output.read_bytes(), raw)
        self.assertEqual(result["digests"]["output"], sha256(raw).hexdigest())

    def test_replayed_failed_measurement_uses_public_refusal_verdict(self):
        report = copy.deepcopy(self.measurement)
        report["summary"]["status"] = "rejected"
        raw = noema._canonical_json(report)
        arguments = argparse.Namespace(
            budget_ledger=self.directory / "unused-rejected-budget.json",
            budget_usd=None,
            credential_file=None,
            manifest=self.manifest,
            output=self.directory / "replayed-rejected-measurement.json",
            profiles=self.profile_path,
        )
        with mock.patch.object(
            noema,
            "_recorded_measurement",
            return_value=(report, raw),
        ):
            result, success = noema._measure_command(arguments)
        self.assertFalse(success)
        self.assertEqual(result["verdict"], "refuse")

    def test_packet_emission_is_deterministic_at_one_tree(self):
        with scratch_directory("noema-packet-repeat-") as temporary:
            repeated = Path(temporary) / "packet"
            noema.emit_evaluation_packet(
                self.manifest,
                self.profile_path,
                repeated,
            )
            names = sorted(path.name for path in self.packet_directory.iterdir())
            self.assertEqual(names, sorted(path.name for path in repeated.iterdir()))
            for name in names:
                self.assertEqual(
                    (self.packet_directory / name).read_bytes(),
                    (repeated / name).read_bytes(),
                )

    def test_packet_has_one_nonce_per_case_and_representation(self):
        nonces = [
            prompt["context_nonce"]
            for case in self.packet["cases"]
            for prompt in case["prompts"]
        ]
        self.assertEqual((len(nonces), len(set(nonces))), (16, 16))

    def test_packet_prompts_do_not_leak_the_oracle(self):
        for prompt in self.packet_directory.glob("prompt-*.txt"):
            lowered = prompt.read_bytes().lower()
            self.assertNotIn(b"required_answer", lowered)
            self.assertNotIn(b"correct answer", lowered)

    def test_candidate_order_is_deterministically_counterbalanced(self):
        positions = [
            next(
                index
                for index, candidate in enumerate(case["candidate_answers"])
                if candidate["id"] == case["required_answer_id"]
            )
            for case in self.packet["cases"]
        ]
        self.assertEqual(positions, [0, 1, 0, 1, 0, 1, 0, 1])
        required_is_low = [
            case["required_answer_id"]
            == min(candidate["id"] for candidate in case["candidate_answers"])
            for case in self.packet["cases"]
        ]
        self.assertEqual(
            required_is_low,
            [True, True, False, False, True, True, False, False],
        )

    def test_noema_prompts_do_not_include_markdown_binding_excerpt(self):
        for case in self.packet["cases"]:
            prompt = next(item for item in case["prompts"] if item["mode"] == "noema")
            payload = (self.packet_directory / prompt["path"]).read_bytes()
            self.assertNotIn(case["source_excerpt"]["text"].encode(), payload)

    def test_each_prompt_carries_the_exact_runtime_context_and_bounded_focus(self):
        for case in self.packet["cases"]:
            context = noema._canonical_json(case["runtime_context"]).rstrip()
            source_excerpt = case["source_excerpt"]["text"].encode()
            for prompt in case["prompts"]:
                payload = (self.packet_directory / prompt["path"]).read_bytes()
                self.assertIn(b"runtime_context: " + context + b"\n", payload)
                if prompt["mode"] == "source":
                    self.assertIn(source_excerpt, payload)
                else:
                    self.assertNotIn(source_excerpt, payload)

    def test_each_prompt_defines_runtime_context_semantics(self):
        context_contract = (
            b"runtime_context contract: authority lists established authorizing actors; "
            b"facts bind exact propositions to true, false, or unknown; "
            b"absent conditions are unknown.\n"
        )
        decision_contract = (
            b"decision contract: when the document conditions the queried effect on asking, "
            b"confirmation, or approval and authority is empty, the effect is not permitted; "
            b"candidate outcome fields are alternatives, not governing evidence.\n"
        )
        for case in self.packet["cases"]:
            for prompt in case["prompts"]:
                payload = (self.packet_directory / prompt["path"]).read_bytes()
                self.assertEqual(payload.count(context_contract), 1)
                self.assertEqual(payload.count(decision_contract), 1)

    def test_phylax_consequence_case_binds_ask_first_without_minting_approval(self):
        directory = specimen_directory("phylax")
        source = (ROOT / read_json(directory / "source.json")["path"]).read_bytes()
        records = noema._parse_source_lines((directory / "source.noe").read_bytes())
        rule = next(record for record in records if record[:2] == ["rule", "rule.default"])
        self.assertEqual(rule[2][-1], ["+", [":", "effect", "dependency.add"]])
        self.assertEqual(source[int(rule[3][3]) : int(rule[3][4])], b"**Ask first.** Adding a dependency.")
        self.assertEqual(read_json(directory / "selection.json")["authority"], [])

    def test_packet_fact_proposition_tamper_refuses(self):
        with self.copied_packet() as packet:
            manifest = read_json(packet / "manifest.json")
            fact = manifest["cases"][0]["runtime_context"]["facts"][0]
            fact["proposition"] = [
                "core.checked",
                [":", "evidence", "substituted"],
            ]
            write_canonical_json(packet / "manifest.json", manifest)
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.FACTS")

    def test_packet_missing_prompt_refuses(self):
        with self.copied_packet() as packet:
            (packet / "prompt-01-noema.txt").unlink()
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-IO.READ")

    def test_packet_extra_file_refuses(self):
        with self.copied_packet() as packet:
            write_bytes(packet / "extra.txt", b"x")
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-REFERENCE.EXTRA_MEMBER")

    def test_packet_prompt_change_refuses(self):
        with self.copied_packet() as packet:
            path = packet / "prompt-01-noema.txt"
            write_bytes(path, path.read_bytes() + b"x")
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROMPT")

    def test_packet_duplicate_nonce_refuses(self):
        with self.copied_packet() as packet:
            manifest = read_json(packet / "manifest.json")
            manifest["cases"][0]["prompts"][1]["context_nonce"] = manifest["cases"][0]["prompts"][0]["context_nonce"]
            write_canonical_json(packet / "manifest.json", manifest)
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.CONTEXT")

    def test_rehashed_packet_attempt_tamper_refuses_before_calls(self):
        with self.copied_packet() as packet:
            manifest = read_json(packet / "manifest.json")
            manifest["cases"][0]["prompts"][0]["requests"][0]["attempts"][0][
                "sha256"
            ] = "f" * 64
            manifest["case_set_sha256"] = noema._value_sha256(
                [
                    {
                        "case_sha256": case["case_sha256"],
                        "id": case["id"],
                        "prompts": case["prompts"],
                    }
                    for case in manifest["cases"]
                ]
            )
            write_canonical_json(packet / "manifest.json", manifest)
            with (
                mock.patch.object(noema, "invoke_adapter") as invoke,
                self.assertRaises(noema.Refusal) as raised,
            ):
                noema.run_evaluation(
                    packet / "manifest.json",
                    self.manifest,
                    self.profile_path,
                    credential=None,
                    budget=Decimal("5"),
                    budget_ledger=self.directory / "tampered-attempt-budget.json",
                )
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.EVALUATION")
            invoke.assert_not_called()

    def test_packet_attempt_digest_tamper_refuses(self):
        with self.copied_packet() as packet:
            manifest = read_json(packet / "manifest.json")
            manifest["cases"][0]["prompts"][0]["requests"][0]["attempts"][0][
                "sha256"
            ] = "f" * 64
            write_canonical_json(packet / "manifest.json", manifest)
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.CASE_SET")

    def test_packet_answer_leakage_refuses_even_when_rehashed(self):
        with self.copied_packet() as packet:
            manifest = read_json(packet / "manifest.json")
            prompt_record = manifest["cases"][0]["prompts"][0]
            prompt_path = packet / prompt_record["path"]
            payload = prompt_path.read_bytes() + b"required_answer\n"
            write_bytes(prompt_path, payload)
            prompt_record["bytes"] = len(payload)
            prompt_record["sha256"] = sha256(payload).hexdigest()
            manifest["case_set_sha256"] = noema._value_sha256(
                [
                    {"case_sha256": case["case_sha256"], "id": case["id"], "prompts": case["prompts"]}
                    for case in manifest["cases"]
                ]
            )
            write_canonical_json(packet / "manifest.json", manifest)
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.LEAKAGE")

    def test_packet_family_alias_refuses(self):
        with self.copied_packet() as packet:
            manifest = read_json(packet / "manifest.json")
            manifest["family_profiles"][1]["family"] = manifest["family_profiles"][0]["family"]
            write_canonical_json(packet / "manifest.json", manifest)
            with self.assertRaises(noema.Refusal) as raised:
                noema._load_packet(packet / "manifest.json")
            self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.ALIAS")

    def test_valid_answer_set_tallies_all_critical_pairs(self):
        report, success = noema._tally_evaluation_values(
            self.packet,
            self.packet_raw,
            self.answers,
            noema._canonical_json(self.answers),
        )
        self.assertTrue(success)
        self.assertEqual((report["summary"]["pairs"], report["summary"]["passed"]), (16, 16))

    def test_transient_retry_chain_tallies_against_preregistered_requests(self):
        value = copy.deepcopy(self.answers)
        answer = value["answers"][0]
        case = next(item for item in self.packet["cases"] if item["id"] == answer["case_id"])
        prompt = next(item for item in case["prompts"] if item["mode"] == answer["mode"])
        bindings = next(
            item["attempts"]
            for item in prompt["requests"]
            if item["family_id"] == answer["family_id"]
        )
        answer["provenance"]["attempts"] = [
            {
                "answer_code": "NOE-E-ADAPTER.HTTP_502",
                "attempt": bindings[0]["attempt"],
                "context_nonce": bindings[0]["context_nonce"],
                "request_sha256": bindings[0]["sha256"],
                "status": "unknown",
            },
            {
                "answer_code": "NOE-OK",
                "attempt": bindings[1]["attempt"],
                "context_nonce": bindings[1]["context_nonce"],
                "request_sha256": bindings[1]["sha256"],
                "status": "recorded",
            },
        ]
        answer["provenance"]["request_sha256"] = bindings[1]["sha256"]
        answer["provenance"]["generation_id"] = "generation." + bindings[1]["sha256"][:24]
        _report, accepted = noema._tally_evaluation_values(
            self.packet,
            self.packet_raw,
            value,
            noema._canonical_json(value),
        )
        self.assertTrue(accepted)

    def test_answer_code_binds_the_terminal_attempt(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0]["provenance"]["attempts"][-1][
            "answer_code"
        ] = "NOE-E-EVALUATION.ANSWER"
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(
                self.packet,
                self.packet_raw,
                value,
                noema._canonical_json(value),
            )
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.ADAPTER")

    def test_semantic_refusal_cannot_authorise_a_retry_chain(self):
        value = copy.deepcopy(self.answers)
        answer = value["answers"][0]
        case = next(item for item in self.packet["cases"] if item["id"] == answer["case_id"])
        prompt = next(item for item in case["prompts"] if item["mode"] == answer["mode"])
        bindings = next(
            item["attempts"]
            for item in prompt["requests"]
            if item["family_id"] == answer["family_id"]
        )
        answer["provenance"]["attempts"] = [
            {
                "answer_code": "NOE-E-ADAPTER.PROVIDER_POLICY",
                "attempt": bindings[0]["attempt"],
                "context_nonce": bindings[0]["context_nonce"],
                "request_sha256": bindings[0]["sha256"],
                "status": "unknown",
            },
            {
                "answer_code": "NOE-OK",
                "attempt": bindings[1]["attempt"],
                "context_nonce": bindings[1]["context_nonce"],
                "request_sha256": bindings[1]["sha256"],
                "status": "recorded",
            },
        ]
        answer["provenance"]["request_sha256"] = bindings[1]["sha256"]
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(
                self.packet,
                self.packet_raw,
                value,
                noema._canonical_json(value),
            )
        self.assertEqual(raised.exception.code, "NOE-E-ADAPTER.RETRY")

    def test_duplicate_answer_refuses(self):
        value = copy.deepcopy(self.answers)
        value["answers"].append(copy.deepcopy(value["answers"][0]))
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.DUPLICATE")

    def test_missing_answer_refuses(self):
        value = copy.deepcopy(self.answers)
        value["answers"].pop()
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.MISSING")

    def test_unknown_candidate_answer_refuses(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0]["answer_id"] = "answer.outside"
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.UNKNOWN_ANSWER")

    def test_answer_summary_mismatch_refuses(self):
        value = copy.deepcopy(self.answers)
        value["summary"]["recorded"] -= 1
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.EVALUATION")

    def test_answer_result_identity_mismatch_refuses(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0]["id"] = "result.wrong"
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.EVALUATION")

    def test_answer_provenance_binds_the_exact_packet_request(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0]["provenance"]["request_sha256"] = "f" * 64
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(
                self.packet,
                self.packet_raw,
                value,
                noema._canonical_json(value),
            )
        self.assertEqual(raised.exception.code, "NOE-E-DIGEST.ADAPTER")

    def test_cross_paired_answer_context_refuses(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0]["context_nonce"] = value["answers"][1]["context_nonce"]
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.CROSS_PAIR")

    def test_answer_order_is_canonical(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0], value["answers"][1] = value["answers"][1], value["answers"][0]
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-SYNTAX.ORDER")

    def test_reused_generation_identity_refuses(self):
        value = copy.deepcopy(self.answers)
        value["answers"][1]["provenance"]["generation_id"] = value["answers"][0]["provenance"]["generation_id"]
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.CONTEXT")

    def test_unknown_status_cannot_carry_candidate(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0]["status"] = "unknown"
        value["answers"][0]["answer_code"] = "NOE-E-ADAPTER.REMOTE"
        value["summary"].update(recorded=31, status="unknown", unknown=1)
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.ANSWER")

    def test_recorded_error_cannot_carry_candidate(self):
        value = copy.deepcopy(self.answers)
        value["answers"][0]["answer_code"] = "NOE-E-ADAPTER.REMOTE"
        value["summary"]["status"] = "unknown"
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.ANSWER")

    def test_unknown_answer_cannot_claim_recorded_provenance(self):
        value = copy.deepcopy(self.answers)
        answer = value["answers"][0]
        answer.update(
            answer_code="NOE-E-ADAPTER.PROVIDER_POLICY",
            answer_id=None,
            status="unknown",
        )
        answer["provenance"]["attempts"][-1].update(
            answer_code="NOE-E-ADAPTER.PROVIDER_POLICY",
            status="unknown",
        )
        answer["provenance"].update(
            cost_usd="0",
            finish_reason="unknown",
            generation_id="unknown",
            input_tokens=1,
            output_tokens=0,
        )
        value["summary"].update(recorded=31, status="unknown", unknown=1)
        with self.assertRaises(noema.Refusal) as raised:
            noema._tally_evaluation_values(self.packet, self.packet_raw, value, noema._canonical_json(value))
        self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.ANSWER")

    def test_wrong_required_answer_is_recorded_as_rejection(self):
        value = copy.deepcopy(self.answers)
        first = value["answers"][0]
        case = next(item for item in self.packet["cases"] if item["id"] == first["case_id"])
        first["answer_id"] = next(
            candidate["id"]
            for candidate in case["candidate_answers"]
            if candidate["id"] != case["required_answer_id"]
        )
        report, success = noema._tally_evaluation_values(
            self.packet,
            self.packet_raw,
            value,
            noema._canonical_json(value),
        )
        self.assertFalse(success)
        self.assertEqual(report["summary"]["status"], "rejected")

    def test_fake_live_runner_records_all_32_isolated_answers(self):
        required_by_nonce = {
            prompt["context_nonce"]: case["required_answer_id"]
            for case in self.packet["cases"]
            for prompt in case["prompts"]
        }

        def recorded_answer(profile, _prompt, *, context_nonce, **_kwargs):
            _request_raw, request_digest = noema._adapter_request_bytes(
                profile,
                _prompt,
                mode="evaluation",
                context_nonce=context_nonce,
            )
            return {
                "answer_code": "NOE-OK",
                "answer_id": required_by_nonce[context_nonce],
                "cost_usd": "0.000001",
                "finish_reason": "stop",
                "generation_id": "generation." + request_digest[:24],
                "input_tokens": 100,
                "model": profile["model"],
                "output_tokens": 1,
                "provider": profile["provider"],
                "request_sha256": request_digest,
                "schema": noema.ADAPTER_RESPONSE_SCHEMA,
                "status": "recorded",
            }

        with mock.patch.object(noema, "invoke_adapter", side_effect=recorded_answer):
            report, success = noema.run_evaluation(
                self.packet_directory / "manifest.json",
                self.manifest,
                self.profile_path,
                credential=None,
                budget=Decimal("5"),
                budget_ledger=self.directory / "evaluation-budget.json",
            )
        self.assertTrue(success)
        self.assertEqual((report["summary"]["expected"], report["summary"]["recorded"]), (32, 32))

    def test_live_runner_marks_an_out_of_set_model_answer_unknown(self):
        def outside_answer(profile, prompt, *, context_nonce, **_kwargs):
            _request_raw, request_digest = noema._adapter_request_bytes(
                profile,
                prompt,
                mode="evaluation",
                context_nonce=context_nonce,
            )
            return {
                "answer_code": "NOE-OK",
                "answer_id": "answer.outside",
                "cost_usd": "0.000001",
                "finish_reason": "stop",
                "generation_id": "generation." + request_digest[:24],
                "input_tokens": 100,
                "model": profile["model"],
                "output_tokens": 1,
                "provider": profile["provider"],
                "request_sha256": request_digest,
                "schema": noema.ADAPTER_RESPONSE_SCHEMA,
                "status": "recorded",
            }

        with mock.patch.object(
            noema,
            "invoke_adapter",
            side_effect=outside_answer,
        ):
            report, success = noema.run_evaluation(
                self.packet_directory / "manifest.json",
                self.manifest,
                self.profile_path,
                credential=None,
                budget=Decimal("5"),
                budget_ledger=self.directory / "outside-budget.json",
            )
        self.assertFalse(success)
        self.assertTrue(
            all(
                answer["answer_code"] == "NOE-E-EVALUATION.UNKNOWN_ANSWER"
                and answer["answer_id"] is None
                for answer in report["answers"]
            )
        )

    def test_live_runner_preserves_request_identity_on_adapter_refusal(self):
        failure = noema.Refusal(
            "NOE-E-ADAPTER.REMOTE",
            "provider",
            "provider request failed",
        )
        with mock.patch.object(noema, "invoke_adapter", side_effect=failure):
            answers, success = noema.run_evaluation(
                self.packet_directory / "manifest.json",
                self.manifest,
                self.profile_path,
                credential=None,
                budget=Decimal("5"),
                budget_ledger=self.directory / "refusal-budget.json",
            )
        self.assertFalse(success)
        request_digests = [
            answer["provenance"]["request_sha256"]
            for answer in answers["answers"]
        ]
        self.assertNotIn("0" * 64, request_digests)
        self.assertEqual(len(request_digests), len(set(request_digests)))
        report, accepted = noema._tally_evaluation_values(
            self.packet,
            self.packet_raw,
            answers,
            noema._canonical_json(answers),
        )
        self.assertFalse(accepted)
        self.assertEqual(report["summary"]["failed"], 16)

    def test_live_runner_refuses_stale_repository_tree_before_calls(self):
        with self.copied_packet() as packet:
            manifest = read_json(packet / "manifest.json")
            manifest["repository_tree"] = "0" * 40
            write_canonical_json(packet / "manifest.json", manifest)
            with self.assertRaises(noema.Refusal) as raised:
                noema.run_evaluation(
                    packet / "manifest.json",
                    self.manifest,
                    self.profile_path,
                    credential=None,
                    budget=Decimal("5"),
                    budget_ledger=self.directory / "stale-budget.json",
                )
            self.assertEqual(raised.exception.code, "NOE-E-EVALUATION.TREE")

    def test_live_runner_rereads_exact_prompt_before_each_call(self):
        with self.copied_packet() as packet:
            original_load = noema._load_packet

            def load_then_change(path):
                loaded = original_load(path)
                prompt = packet / "prompt-01-noema.txt"
                write_bytes(prompt, prompt.read_bytes() + b"changed\n")
                return loaded

            with mock.patch.object(noema, "_load_packet", side_effect=load_then_change):
                with self.assertRaises(noema.Refusal) as raised:
                    noema.run_evaluation(
                        packet / "manifest.json",
                        self.manifest,
                        self.profile_path,
                        credential=None,
                        budget=Decimal("5"),
                        budget_ledger=self.directory / "changed-prompt-budget.json",
                    )
            self.assertEqual(raised.exception.code, "NOE-E-DIGEST.PROMPT")

    def test_packet_publication_refuses_existing_target(self):
        with scratch_directory("noema-packet-existing-") as temporary:
            target = Path(temporary) / "packet"
            target.mkdir()
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_packet_directory(target, {"prompt.txt": b"x"}, b"{}\n")
            self.assertEqual(raised.exception.code, "NOE-E-PATH.EXISTS")

    def test_packet_publication_refuses_aggregate_overflow(self):
        with scratch_directory("noema-packet-overflow-") as temporary:
            target = Path(temporary) / "packet"
            with self.assertRaises(noema.Refusal) as raised:
                noema._atomic_packet_directory(
                    target,
                    {"prompt.txt": b"x" * noema.MAX_PACKET_BYTES},
                    b"{}\n",
                )
            self.assertEqual(raised.exception.code, "NOE-E-BOUNDS.PACKET")


if __name__ == "__main__":
    unittest.main()
