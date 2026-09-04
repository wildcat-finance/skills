"""Step 1 and Step 2 guards for the framework-74 research boundary."""

from __future__ import annotations

import ast
import copy
from contextlib import contextmanager
from functools import lru_cache
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import selectors
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "research/instruction-architecture/benchmark.py"
HEXCTL = ROOT / "plugins/hexaemeron/skills/fiat/scripts/hexctl.py"
FIXTURES = ROOT / "tests/fixtures/instruction-architecture"
MANIFEST = FIXTURES / "corpus-manifest.json"
PROFILES = FIXTURES / "invocation-profiles.json"
GRAPH = FIXTURES / "loader-graph.json"
PARTITION = FIXTURES / "byte-partition.json"
COHORTS = FIXTURES / "cohorts.json"
SEAL = FIXTURES / "holdout-seal.json"
INVENTORY = FIXTURES / "artifact-inventory.json"
SCHEMA = ROOT / "research/instruction-architecture/schemas/source-bound-v1.schema.json"
PROFILE_SCHEMA = ROOT / "research/instruction-architecture/schemas/invocation-profile-v1.schema.json"
DEVELOPMENT_SCHEMA = ROOT / "research/instruction-architecture/schemas/development-v1.schema.json"
DEVELOPMENT_CASES = FIXTURES / "development/cases.json"
DEVELOPMENT_REPORT = FIXTURES / "evidence/development/report.json"
DEVELOPMENT_INVENTORY = FIXTURES / "evidence/development/artifact-inventory.json"
HOSTILE_SPECIMENS = FIXTURES / "hostile/specimens.json"
HOSTILE_EXECUTION = FIXTURES / "hostile/execution.json"
CONTROL_SNAPSHOT_MANIFEST = FIXTURES / "controls/snapshots/manifest.json"
DEVELOPMENT_CONTROLS = {
    arm: FIXTURES / "controls" / f"{arm}.json"
    for arm in ("raw", "wai1", "noema", "simple", "section-graph")
}
DEVELOPMENT_RESULTS = {
    arm: FIXTURES / "evidence/development" / f"{arm}.json"
    for arm in ("raw", "wai1", "noema", "simple", "section-graph")
}
EXPERIMENT_SCHEMA = ROOT / "research/instruction-architecture/schemas/experiment-v1.schema.json"
CONFORMANCE_CONTRACT = ROOT / ".fiat/conformance-overlay-contract.json"
CONFORMANCE_CONTRACT_SCHEMA = (
    ROOT / "research/instruction-architecture/schemas/conformance-contract-v1.schema.json"
)
CONFORMANCE_OVERLAY_SCHEMA = (
    ROOT / "research/instruction-architecture/schemas/conformance-overlay-v1.schema.json"
)
DEVELOPMENT_SELECTION = FIXTURES / "development-selection.json"
PREREGISTRATION = FIXTURES / "preregistration.json"
MODEL_RUNTIME_MANIFEST = FIXTURES / "model-runtime-manifest.json"
PROMPT_TEMPLATE = FIXTURES / "prompt-template.txt"
SCORER = FIXTURES / "scorer.json"
HOLDOUT_PACKET_COMMITMENT = FIXTURES / "holdout-packet-commitment.json"
FROZEN_PACKET_ROOT = FIXTURES / "evidence/frozen"
NATIVE_PREREGISTRATION = FIXTURES / "native-deployment-preregistration.json"
NATIVE_RUNTIME_MANIFEST = FIXTURES / "native-runtime-manifest.json"
NATIVE_CACHE_ACCOUNTING = FIXTURES / "native-cache-accounting.json"
NATIVE_PROMPT_TEMPLATE = FIXTURES / "native-prompt-template.txt"
NATIVE_PACKET_COMMITMENT = FIXTURES / "native-lifecycle-packet-commitment.json"
FROZEN_NATIVE_ROOT = FROZEN_PACKET_ROOT / "native"
STUDY = ROOT / "docs/instruction-architecture/study.md"
RUNBOOK = ROOT / "docs/instruction-architecture/runbook.md"
RESEARCH_REPORT = ROOT / "docs/instruction-architecture/research-report.md"
RECEIPTED_STUDY_SHA256 = (
    "fdc6db5b11af226b488a2f02fd9c99df25ad4405990269491b58679eb40d6129"
)
AMENDED_RUNBOOK_SHA256 = (
    "fc9bb7487c74d30b1f683418061854fdcb49a1e5c0a817739d909076f1172609"
)
EXPECTED_KRONOS_RANKING_LEDGERS = {
    "plugins/alexandria/skills/alexandria/EVOLUTION.md",
    "plugins/anamnesis/skills/anamnesis/EVOLUTION.md",
    "plugins/ariadne/skills/ariadne/EVOLUTION.md",
    "plugins/berean/skills/berean/EVOLUTION.md",
    "plugins/brevitas/skills/brevitas/EVOLUTION.md",
    "plugins/hermes/skills/hermes/EVOLUTION.md",
    "plugins/hexaemeron/skills/elenchus/EVOLUTION.md",
    "plugins/hexaemeron/skills/ephoros/EVOLUTION.md",
    "plugins/hexaemeron/skills/fiat/EVOLUTION.md",
    "plugins/hexaemeron/skills/hypomnema/EVOLUTION.md",
    "plugins/hexaemeron/skills/imprimatur/EVOLUTION.md",
    "plugins/hexaemeron/skills/metron/EVOLUTION.md",
    "plugins/hexaemeron/skills/phylax/EVOLUTION.md",
    "plugins/hexaemeron/skills/protasis/EVOLUTION.md",
    "plugins/hexaemeron/skills/vulgate/EVOLUTION.md",
    "plugins/homologia/skills/homologia/EVOLUTION.md",
    "plugins/horos/skills/horos/EVOLUTION.md",
    "plugins/janus/skills/janus/EVOLUTION.md",
    "plugins/lazarus/skills/lazarus/EVOLUTION.md",
    "plugins/lemma/skills/lemma/EVOLUTION.md",
    "plugins/pandects/skills/pandects/EVOLUTION.md",
    "plugins/probitas/skills/probitas/EVOLUTION.md",
    "plugins/sapheneia/skills/sapheneia/EVOLUTION.md",
    "plugins/synkrisis/skills/synkrisis/EVOLUTION.md",
    "plugins/tabularium/skills/tabularium/EVOLUTION.md",
}

EXPECTED_STRUCTURED_REFERENCES = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": (177_562, "5d1773f9a5f51e957bd769deb3b030b670fa10499e33fce4a8df3a2e221bd5ac"),
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": (3_779, "d2ecc41b3da60df47d5a7ce86f338dbadf7beb18080957dee21881dae4503d1d"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": (3_716, "e554ab6f9661d88095f285c6651983c980bd672b854287f74daa288b1dabc34c"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": (7_842, "a6ad7adbc6c8e06512032cf460c92749a49a6c139b4f2aee101de8bdc95df844"),
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": (3_843, "908e20c6319b587e95fa21de5949a10c0088ed698d546b0a1048686211826240"),
    "plugins/homologia/references/manifest-v1.schema.json": (3_554, "b60b46a65def47e11347fe408709c137b17accdd6fe2b39872c102c7c7db7413"),
    "plugins/homologia/references/vectors-v1.schema.json": (3_494, "1031838d2405c949a2ad7fcb9c693119499f1f8183286fe2019e02fa6680b056"),
    "plugins/synkrisis/references/cohort-v1.schema.json": (3_204, "5e71420816444af4582e0380b9d6e7ff845e4b3686126233c24a9d1ab5335b0d"),
    "plugins/synkrisis/references/findings-v1.schema.json": (4_152, "52cf6589e57a93fa82eef75520be44f10636d2469eafe2dae9c91e1d457627c8"),
    "plugins/synkrisis/references/policy-v1.schema.json": (1_982, "04d440bdbd96fcff165d4b0badc029a79634bf17b1a7ac380baee85630c873bb"),
    "plugins/synkrisis/references/rule-v1.schema.json": (3_087, "c8b45c1b6e2b9de010d7ce17109a6f7d49a4797d5a79b07186eabdfa1ed44698"),
    "plugins/synkrisis/references/rules-v1.json": (2_361, "e754bb72235103290ec4ea58b2c71b851782573c3e27eb16a08fe762c3f3a4af"),
}

EXPECTED_OPERATION_REFERENCES = {
    "docs/fiat-run-observation-binding-v1.md",
    "plugins/alexandria/docs/runbook.md",
    "plugins/alexandria/docs/study.md",
    "plugins/alexandria/docs/usdc-interval-collector.md",
    "plugins/anamnesis/docs/demo.md",
    "plugins/ariadne/docs/capturing-a-dataset.md",
    "plugins/ariadne/docs/capturing-a-grounded-agent.md",
    "plugins/ariadne/docs/capturing-a-release.md",
    "plugins/ariadne/docs/capturing-a-state-fixture.md",
    "plugins/ariadne/docs/conformance.md",
    "plugins/ariadne/docs/dataset.md",
    "plugins/ariadne/docs/grounded-agent.md",
    "plugins/ariadne/docs/solidity-release.md",
    "plugins/ariadne/docs/state-fixture.md",
    "plugins/lazarus/docs/chain-anchors.md",
    "plugins/lazarus/docs/preservation-release.md",
    "plugins/lazarus/docs/runbook.md",
    "plugins/lazarus/docs/study.md",
    "plugins/lemma/INVARIANTS.md",
    "plugins/pandects/docs/applicability.md",
    "plugins/pandects/docs/writing-a-law.md",
    "plugins/pandects/integrations/wildcat/APPLICABILITY.md",
    "plugins/probitas/docs/adding-a-venue.md",
    "plugins/tabularium/docs/adding-an-adapter.md",
    "plugins/tabularium/docs/release-policy.md",
}

EXPECTED_ARIADNE_OPERATIONS = {
    "operation:ariadne:capture-dataset": {
        "plugins/ariadne/docs/capturing-a-dataset.md",
        "plugins/ariadne/docs/dataset.md",
    },
    "operation:ariadne:capture-grounded-agent": {
        "plugins/ariadne/docs/capturing-a-grounded-agent.md",
        "plugins/ariadne/docs/grounded-agent.md",
    },
    "operation:ariadne:capture-release": {
        "plugins/ariadne/docs/capturing-a-release.md",
        "plugins/ariadne/docs/solidity-release.md",
    },
    "operation:ariadne:capture-state-fixture": {
        "plugins/ariadne/docs/capturing-a-state-fixture.md",
        "plugins/ariadne/docs/state-fixture.md",
    },
    "operation:ariadne:conformance": {"plugins/ariadne/docs/conformance.md"},
}


def load_module():
    spec = importlib.util.spec_from_file_location("instruction_architecture", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


AI = load_module()


def load_hexctl_module():
    spec = importlib.util.spec_from_file_location("fiat_hexctl", HEXCTL)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not load {HEXCTL}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def canonical(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode()


def linked_codex_schema_records():
    request_definitions = {
        "ThreadStartParams": {
            "type": "object",
            "properties": {
                "allowProviderModelFallback": {"type": "boolean"},
                "approvalPolicy": {
                    "anyOf": [
                        {"$ref": "#/definitions/AskForApproval"},
                        {"type": "null"},
                    ]
                },
                "baseInstructions": {"type": ["string", "null"]},
                "cwd": {"type": ["string", "null"]},
                "dynamicTools": {"type": ["array", "null"]},
                "environments": {"type": ["array", "null"]},
                "ephemeral": {"type": ["boolean", "null"]},
                "experimentalRawEvents": {"type": "boolean"},
                "model": {"type": ["string", "null"]},
                "sandbox": {
                    "anyOf": [
                        {"$ref": "#/definitions/SandboxMode"},
                        {"type": "null"},
                    ]
                },
            },
        },
        "ThreadResumeParams": {
            "type": "object",
            "properties": {"threadId": {"type": "string"}},
            "required": ["threadId"],
        },
        "ThreadCompactStartParams": {
            "type": "object",
            "properties": {"threadId": {"type": "string"}},
            "required": ["threadId"],
        },
        "TurnStartParams": {
            "type": "object",
            "properties": {
                "input": {
                    "items": {"$ref": "#/definitions/UserInput"},
                    "type": "array",
                },
                "outputSchema": {},
                "threadId": {"type": "string"},
            },
            "required": ["input", "threadId"],
        },
        "AskForApproval": {
            "oneOf": [
                {"enum": ["untrusted", "on-request", "never"], "type": "string"}
            ]
        },
        "SandboxMode": {
            "enum": ["read-only", "workspace-write", "danger-full-access"],
            "type": "string",
        },
        "UserInput": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "type": {"enum": ["text"], "type": "string"},
                    },
                    "required": ["text", "type"],
                }
            ]
        },
    }

    def method_variant(method, definition, *, request):
        required = ["method", "params"]
        properties = {
            "method": {"enum": [method]},
            "params": {"$ref": f"#/definitions/{definition}"},
        }
        if request:
            required.insert(0, "id")
            properties["id"] = {}
        return {"type": "object", "properties": properties, "required": required}

    client = {
        "definitions": request_definitions,
        "oneOf": [
            method_variant(method, definition, request=True)
            for method, definition in (
                ("thread/start", "ThreadStartParams"),
                ("thread/resume", "ThreadResumeParams"),
                ("thread/compact/start", "ThreadCompactStartParams"),
                ("turn/start", "TurnStartParams"),
            )
        ],
    }
    notification_definitions = {
        "ThreadTokenUsageUpdatedNotification": {
            "type": "object",
            "properties": {
                "threadId": {"type": "string"},
                "tokenUsage": {"$ref": "#/definitions/ThreadTokenUsage"},
                "turnId": {"type": "string"},
            },
            "required": ["threadId", "tokenUsage", "turnId"],
        },
        "ThreadTokenUsage": {
            "type": "object",
            "properties": {
                "last": {"$ref": "#/definitions/TokenUsageBreakdown"},
                "total": {"$ref": "#/definitions/TokenUsageBreakdown"},
            },
            "required": ["last", "total"],
        },
        "TokenUsageBreakdown": {
            "type": "object",
            "properties": {
                "inputTokens": {"type": "integer"},
                "cachedInputTokens": {"type": "integer"},
                "cacheWriteInputTokens": {"type": "integer"},
            },
            "required": ["inputTokens", "cachedInputTokens"],
        },
        "ItemCompletedNotification": {
            "type": "object",
            "properties": {
                "item": {"$ref": "#/definitions/ThreadItem"},
                "threadId": {"type": "string"},
                "turnId": {"type": "string"},
            },
            "required": ["item", "threadId", "turnId"],
        },
        "ThreadItem": {
            "oneOf": [
                {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "type": {"enum": ["contextCompaction"]},
                    },
                    "required": ["id", "type"],
                }
            ]
        },
    }
    notifications = {
        "definitions": notification_definitions,
        "oneOf": [
            method_variant(
                "thread/tokenUsage/updated",
                "ThreadTokenUsageUpdatedNotification",
                request=False,
            ),
            method_variant(
                "item/completed", "ItemCompletedNotification", request=False
            ),
        ],
    }
    return [
        {"path": "ClientRequest.json", "value": client},
        {"path": "ServerNotification.json", "value": notifications},
    ]


def authority_fixture() -> dict:
    return {
        "authority": {
            "amended_on": "2026-09-03",
            "authorized_on": "2026-08-31",
            "scope": "framework-74 seven-model behavioral holdout only",
        },
        "budget": {
            "currency": "USD",
            "gross_ceiling": "4500.00",
            "objective_role": "hard-guard-only-never-a-selection-weight",
        },
        "credential": {
            "file": "/not-opened-in-unit-tests",
            "label": "openrouter-api-key",
            "report_value": False,
        },
        "current_credit_observation": {
            "account_endpoint": AI.OPENROUTER_ENDPOINTS["account"],
            "available_credit": "1.00",
            "credit_endpoint": AI.OPENROUTER_ENDPOINTS["credits"],
            "observed_on": "2026-09-03",
            "state": "proved-from-credits-endpoint",
            "total_credits": "1.00",
            "total_usage": "0.00",
        },
        "ledger": {
            "reserved_gross": "0.00",
            "settled_gross": "0.00",
            "uncertain_gross": "0.00",
        },
        "redaction": {
            "forbidden": [
                "credential bytes",
                "authorization header",
                "key hash",
            ]
        },
        "reservation": {
            "fee_rate": "0.055",
            "lost_or_uncertain_attempt": (
                "retain reservation as uncertain until provider settlement is proved"
            ),
        },
        "retry_cap": 1,
        "schema": "wildcat-instruction-architecture-model-evaluation-authority/v1",
    }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clear_source_cache() -> None:
    for name in (
        "_control_ref_mode",
        "_control_snapshot",
        "_git_blob_at",
        "_source_mode",
        "_inventory_source_snapshot",
        "_source_object",
        "_frozen_tree_paths",
    ):
        cached = getattr(AI, name, None)
        if cached is not None:
            cached.cache_clear()
    oracle_source_mode.cache_clear()
    oracle_inventory_snapshot.cache_clear()
    oracle_inventory_sources.cache_clear()
    oracle_tree_paths.cache_clear()
    ORACLE_SOURCE_CACHE.clear()


def scratch_directory(prefix: str = "instruction-architecture-"):
    """Keep confined-path fixtures under the repository's ignored scratch root."""
    scratch = ROOT / "tmp"
    scratch.mkdir(exist_ok=True)
    return tempfile.TemporaryDirectory(dir=scratch, prefix=prefix)


ORACLE_SOURCE_REF = "a2b634d8e039af988bf30c8316defccf70071d8d"
ORACLE_MAX_JSON_BYTES = 8 * 1024 * 1024
ORACLE_MAX_GIT_OUTPUT = 4 * 1024 * 1024
ORACLE_MAX_GIT_ERROR = 64 * 1024
ORACLE_MAX_SOURCE_BYTES = 2 * 1024 * 1024
ORACLE_MAX_STEP1_DEPENDENCY_BYTES = 8 * 1024 * 1024
ORACLE_MAX_FROZEN_TREE_PATHS = 10_000
ORACLE_STEP1_PARENT_DEPENDENCIES = (
    "docs/instruction-architecture/corpus-reconciliation.md",
    "docs/instruction-architecture/runbook.md",
    "docs/instruction-architecture/study.md",
    "research/instruction-architecture/benchmark.py",
    "research/instruction-architecture/schemas/invocation-profile-v1.schema.json",
    "research/instruction-architecture/schemas/source-bound-v1.schema.json",
    "tests/fixtures/instruction-architecture/artifact-inventory.json",
    "tests/fixtures/instruction-architecture/byte-partition.json",
    "tests/fixtures/instruction-architecture/cohorts.json",
    "tests/fixtures/instruction-architecture/corpus-manifest.json",
    "tests/fixtures/instruction-architecture/holdout-seal.json",
    "tests/fixtures/instruction-architecture/invocation-profiles.json",
    "tests/fixtures/instruction-architecture/loader-graph.json",
)
ORACLE_STEP2_PARENT_CODE_PATHS = (
    "research/instruction-architecture/benchmark.py",
    "tests/test_instruction_architecture.py",
)
ORACLE_RECEIPTED_APPEND_ONLY_DEPENDENCIES = (
    "docs/instruction-architecture/runbook.md",
    "docs/instruction-architecture/study.md",
)
ORACLE_BASELINE_INVENTORY_SHA256 = (
    "7e8566c5e9148ca151323636f51d7d69d7ff0215fb937619eefd4b621fc5bcb9"
)
ORACLE_SKILL_PATHS = {
    "alexandria": "plugins/alexandria/skills/alexandria/SKILL.md",
    "anamnesis": "plugins/anamnesis/skills/anamnesis/SKILL.md",
    "ariadne": "plugins/ariadne/skills/ariadne/SKILL.md",
    "berean": "plugins/berean/skills/berean/SKILL.md",
    "brevitas": "plugins/brevitas/skills/brevitas/SKILL.md",
    "elenchus": "plugins/hexaemeron/skills/elenchus/SKILL.md",
    "ephoros": "plugins/hexaemeron/skills/ephoros/SKILL.md",
    "fiat": "plugins/hexaemeron/skills/fiat/SKILL.md",
    "fizz": "plugins/hexaemeron/skills/fizz/SKILL.md",
    "fizz-convert": "plugins/hexaemeron/skills/fizz/skills/fizz-convert/SKILL.md",
    "fizz-sync": "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md",
    "hermes": "plugins/hermes/skills/hermes/SKILL.md",
    "homologia": "plugins/homologia/skills/homologia/SKILL.md",
    "horos": "plugins/horos/skills/horos/SKILL.md",
    "hypomnema": "plugins/hexaemeron/skills/hypomnema/SKILL.md",
    "imprimatur": "plugins/hexaemeron/skills/imprimatur/SKILL.md",
    "janus": "plugins/janus/skills/janus/SKILL.md",
    "kronos": "plugins/hexaemeron/skills/kronos/SKILL.md",
    "lazarus": "plugins/lazarus/skills/lazarus/SKILL.md",
    "lemma": "plugins/lemma/skills/lemma/SKILL.md",
    "metron": "plugins/hexaemeron/skills/metron/SKILL.md",
    "pandects": "plugins/pandects/skills/pandects/SKILL.md",
    "phylax": "plugins/hexaemeron/skills/phylax/SKILL.md",
    "probitas": "plugins/probitas/skills/probitas/SKILL.md",
    "protasis": "plugins/hexaemeron/skills/protasis/SKILL.md",
    "sapheneia": "plugins/sapheneia/skills/sapheneia/SKILL.md",
    "solidity-auditor": "plugins/hexaemeron/skills/solidity-auditor/SKILL.md",
    "synkrisis": "plugins/synkrisis/skills/synkrisis/SKILL.md",
    "tabularium": "plugins/tabularium/skills/tabularium/SKILL.md",
    "vulgate": "plugins/hexaemeron/skills/vulgate/SKILL.md",
    "x-ray": "plugins/hexaemeron/skills/x-ray/SKILL.md",
}
ORACLE_FIXED_INPUTS = {
    ".python-version": "agent-or-prompt",
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": "mandatory-executable",
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": "mandatory-executable",
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": "mandatory-executable",
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": "mandatory-executable",
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": "mandatory-executable",
    "plugins/hexaemeron/skills/solidity-auditor/VERSION": "agent-or-prompt",
    "plugins/hexaemeron/skills/x-ray/VERSION": "agent-or-prompt",
    "plugins/synkrisis/references/rules-v1.json": "mandatory-executable",
}
ORACLE_EVIDENCE_PROJECTION_SHA256 = (
    "a095623b489914a089d7d3c0233d8fdc7ba5a24a3d8dfaf63de7f3e656b98975"
)
ORACLE_PROFILE_EVIDENCE_COUNTS = {
    "document_reference": 963,
    "fixed_input": 53,
    "frontier_ledger": 625,
    "frontier_policy": 25,
    "operation_reference": 22,
    "overlay_contract": 149,
    "related_skill": 2_013,
    "selected_skill": 519,
    "structured_reference": 427,
    "worker_prompt": 288,
}
ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS = {
    "fixed_input": 3,
    "markdown_reference": 3,
    "operation_reference": 3,
    "structured_reference": 12,
}
ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": 1,
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": 1,
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": 1,
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": 1,
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": 1,
    "plugins/synkrisis/references/rules-v1.json": 1,
}
ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": 4,
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": 4,
    "plugins/synkrisis/references/rules-v1.json": 3,
}
ORACLE_GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_LITERAL_PATHSPECS": "1",
    "GIT_NO_LAZY_FETCH": "1",
    "GIT_NO_REPLACE_OBJECTS": "1",
    "GIT_TERMINAL_PROMPT": "0",
    "LANG": "C",
    "LC_ALL": "C",
}
ORACLE_SOURCE_CACHE: dict[str, bytes] = {}


def oracle_identity(metadata: os.stat_result) -> tuple[int, ...]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_mode,
        metadata.st_nlink,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def oracle_open_parent(path: Path) -> tuple[int, str]:
    """Open one repository parent without following mutable path components."""
    if (
        not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "O_NONBLOCK")
    ):
        raise AssertionError("independent no-follow reads are unavailable")
    try:
        relative = path.relative_to(ROOT)
    except ValueError as exc:
        raise AssertionError("independent input leaves repository") from exc
    if not relative.parts or any(
        part in {"", ".", ".."} for part in relative.parts
    ):
        raise AssertionError("independent input path is unsafe")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        descriptor = os.open(ROOT, flags)
    except OSError as exc:
        raise AssertionError(
            "independent input root is unavailable or unsafe"
        ) from exc
    try:
        for part in relative.parent.parts:
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except OSError as exc:
                raise AssertionError(
                    "independent input parent is unavailable or unsafe"
                ) from exc
            metadata = os.fstat(child)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(child)
                raise AssertionError(
                    "independent input parent is unavailable or unsafe"
                )
            os.close(descriptor)
            descriptor = child
        return descriptor, relative.name
    except BaseException:
        os.close(descriptor)
        raise


def oracle_read_regular(path: Path, limit: int) -> bytes:
    """Read one bounded regular file and bind its name to the observed inode."""
    parent, name = oracle_open_parent(path)
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    try:
        descriptor = os.open(name, flags, dir_fd=parent)
    except OSError as exc:
        os.close(parent)
        raise AssertionError("independent input is unavailable or unsafe") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
            raise AssertionError(
                "independent input is not a single-link regular file"
            )
        if before.st_size > limit:
            raise AssertionError("independent input exceeds byte limit")
        chunks: list[bytes] = []
        size = 0
        while True:
            chunk = os.read(descriptor, min(65_536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
            if size > limit:
                raise AssertionError("independent input exceeds byte limit")
        after = os.fstat(descriptor)
        if oracle_identity(before) != oracle_identity(after):
            raise AssertionError("independent input changed during read")
    finally:
        os.close(descriptor)
        os.close(parent)

    current_parent, current_name = oracle_open_parent(path)
    try:
        try:
            current = os.open(current_name, flags, dir_fd=current_parent)
        except OSError as exc:
            raise AssertionError("independent input changed during read") from exc
        try:
            if oracle_identity(os.fstat(current)) != oracle_identity(after):
                raise AssertionError("independent input changed during read")
        finally:
            os.close(current)
    finally:
        os.close(current_parent)
    return b"".join(chunks)


def oracle_git(
    *arguments: str,
    input_data: bytes | None = None,
    limit: int = ORACLE_MAX_GIT_OUTPUT,
) -> subprocess.CompletedProcess[bytes]:
    """Capture one independent Git read without trusting production helpers."""
    if type(limit) is not int or not 0 < limit <= ORACLE_MAX_GIT_OUTPUT:
        raise AssertionError("independent Git output limit is invalid")
    if input_data is not None:
        if type(input_data) is not bytes:
            raise AssertionError("independent Git input is not bytes")
        if len(input_data) > 4_096:
            raise AssertionError("independent Git input exceeds byte limit")
    command = [
        "/usr/bin/git",
        "--no-lazy-fetch",
        "--no-optional-locks",
        "-C",
        str(ROOT),
        *arguments,
    ]
    try:
        process = subprocess.Popen(
            command,
            stdin=(
                subprocess.PIPE if input_data is not None else subprocess.DEVNULL
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=ORACLE_GIT_ENV,
            start_new_session=True,
        )
    except OSError as exc:
        raise AssertionError("independent Git read failed") from exc
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stderr = bytearray()
    deadline = time.monotonic() + 20
    leader_reaped = False
    try:
        if input_data is not None:
            assert process.stdin is not None
            try:
                process.stdin.write(input_data)
                process.stdin.close()
            except OSError as exc:
                raise AssertionError("independent Git input failed") from exc
        selector.register(process.stdout, selectors.EVENT_READ, (stdout, limit))
        selector.register(
            process.stderr,
            selectors.EVENT_READ,
            (stderr, ORACLE_MAX_GIT_ERROR),
        )
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise AssertionError("independent Git read timed out")
            try:
                events = selector.select(remaining)
            except OSError as exc:
                raise AssertionError(
                    "independent Git output capture failed"
                ) from exc
            if not events:
                raise AssertionError("independent Git read timed out")
            for key, _ in events:
                buffer, cap = key.data
                try:
                    chunk = os.read(
                        key.fd, min(65_536, cap + 1 - len(buffer))
                    )
                except OSError as exc:
                    raise AssertionError(
                        "independent Git output capture failed"
                    ) from exc
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffer.extend(chunk)
                if len(buffer) > cap:
                    stream = "stdout" if buffer is stdout else "stderr"
                    raise AssertionError(
                        f"independent Git {stream} exceeds byte limit"
                    )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise AssertionError("independent Git read timed out")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise AssertionError("independent Git read timed out") from exc
        leader_reaped = True
        return subprocess.CompletedProcess(
            command, returncode, bytes(stdout), bytes(stderr)
        )
    finally:
        selector.close()
        leader_reaped = leader_reaped or process.returncode is not None
        if not leader_reaped:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                try:
                    process.kill()
                except OSError:
                    pass
        if process.poll() is None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
        for stream in (process.stdout, process.stderr):
            try:
                stream.close()
            except OSError:
                pass
        if process.stdin is not None and not process.stdin.closed:
            try:
                process.stdin.close()
            except OSError:
                pass


@lru_cache(maxsize=1)
def oracle_source_mode() -> str:
    expression = f"{ORACLE_SOURCE_REF}^{{commit}}"
    probe = oracle_git(
        "cat-file",
        "--batch-check=%(objectname) %(objecttype)",
        input_data=f"{expression}\n".encode("ascii"),
        limit=ORACLE_MAX_GIT_OUTPUT,
    )
    if len(probe.stdout) > ORACLE_MAX_GIT_OUTPUT:
        raise AssertionError("independent oracle source probe exceeds byte limit")
    if probe.returncode != 0:
        raise AssertionError("independent oracle source probe failed")
    if probe.stdout == f"{ORACLE_SOURCE_REF} commit\n".encode("ascii"):
        return "git"
    if probe.stdout != f"{expression} missing\n".encode("ascii"):
        raise AssertionError("independent oracle source probe was ambiguous")
    shallow = oracle_git(
        "rev-parse",
        "--is-shallow-repository",
        limit=ORACLE_MAX_GIT_OUTPUT,
    )
    if len(shallow.stdout) > ORACLE_MAX_GIT_OUTPUT:
        raise AssertionError("independent shallow probe exceeds byte limit")
    if shallow.returncode != 0 or shallow.stdout != b"true\n":
        raise AssertionError("independent oracle could not resolve the frozen source")
    return "inventory"


@lru_cache(maxsize=1)
def oracle_inventory_snapshot() -> tuple[dict[str, bytes], tuple[str, ...]]:
    """Bind shallow source bytes and tree paths in one independent snapshot."""
    inventory_raw = oracle_read_regular(INVENTORY, ORACLE_MAX_JSON_BYTES)
    if (
        hashlib.sha256(inventory_raw).hexdigest()
        != ORACLE_BASELINE_INVENTORY_SHA256
    ):
        raise AssertionError("independent inventory differs from its source anchor")
    inventory = json.loads(inventory_raw)
    if canonical(inventory) != inventory_raw:
        raise AssertionError("independent inventory snapshot is not canonical")
    if (
        inventory.get("schema")
        != "wildcat-instruction-architecture-artifact-inventory/v1"
        or inventory.get("source_ref") != ORACLE_SOURCE_REF
    ):
        raise AssertionError("independent inventory snapshot identity mismatch")

    bound: dict[str, dict] = {}
    for name, path in (
        ("corpus-manifest.json", MANIFEST),
        ("invocation-profiles.json", PROFILES),
        ("loader-graph.json", GRAPH),
    ):
        raw = oracle_read_regular(path, ORACLE_MAX_JSON_BYTES)
        identity = inventory.get("artifacts", {}).get(name)
        if (
            not isinstance(identity, dict)
            or identity.get("bytes") != len(raw)
            or identity.get("sha256") != hashlib.sha256(raw).hexdigest()
        ):
            raise AssertionError(f"independent inventory binding mismatch: {name}")
        value = json.loads(raw)
        if canonical(value) != raw:
            raise AssertionError(f"independent inventory record is not canonical: {name}")
        bound[name] = value

    manifest = bound["corpus-manifest.json"]
    source = manifest.get("source")
    if (
        not isinstance(source, dict)
        or set(source) != {"ref", "repository_paths", "tree_sha256"}
        or source.get("ref") != ORACLE_SOURCE_REF
    ):
        raise AssertionError("independent manifest source ref mismatch")
    repository_paths = source.get("repository_paths")
    if (
        not isinstance(repository_paths, list)
        or not repository_paths
        or len(repository_paths) > ORACLE_MAX_FROZEN_TREE_PATHS
        or any(not isinstance(path, str) for path in repository_paths)
        or repository_paths != sorted(set(repository_paths))
        or any(
            PurePosixPath(path).is_absolute()
            or str(PurePosixPath(path)) != path
            or "\\" in path
            or any(part in {"", ".", ".."} for part in PurePosixPath(path).parts)
            for path in repository_paths
        )
    ):
        raise AssertionError("independent manifest repository paths are malformed")
    digests: dict[str, tuple[int | None, str]] = {}
    spans: list[tuple[str, int, int, str]] = []
    for document in manifest.get("documents", []):
        path = document.get("path")
        size = document.get("bytes")
        digest = document.get("sha256")
        if (
            not isinstance(path, str)
            or type(size) is not int
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or path in digests
        ):
            raise AssertionError("independent manifest source identity is malformed")
        digests[path] = (size, digest)

    def collect(value: object) -> None:
        if isinstance(value, list):
            for item in value:
                collect(item)
            return
        if not isinstance(value, dict):
            return
        if {
            "path",
            "source_sha256",
            "span_sha256",
            "start",
            "end",
        } <= set(value):
            path = value["path"]
            digest = value["source_sha256"]
            span_digest = value["span_sha256"]
            start = value["start"]
            end = value["end"]
            if (
                not isinstance(path, str)
                or not isinstance(digest, str)
                or not isinstance(span_digest, str)
                or type(start) is not int
                or type(end) is not int
                or start < 0
                or end <= start
            ):
                raise AssertionError("independent source evidence is malformed")
            existing = digests.get(path)
            if existing is not None and existing[1] != digest:
                raise AssertionError("independent source evidence conflicts")
            digests[path] = (existing[0] if existing is not None else None, digest)
            spans.append((path, start, end, span_digest))
        for item in value.values():
            collect(item)

    for value in bound.values():
        collect(value)
    if not set(digests) <= set(repository_paths):
        raise AssertionError("independent manifest omits a source evidence path")
    sources: dict[str, bytes] = {}
    for path, (size, digest) in sorted(digests.items()):
        source_path = ROOT / path
        data = oracle_read_regular(source_path, ORACLE_MAX_SOURCE_BYTES)
        if (
            (size is not None and len(data) != size)
            or hashlib.sha256(data).hexdigest() != digest
        ):
            raise AssertionError(f"independent snapshot source drift: {path}")
        sources[path] = data
    for path, start, end, digest in spans:
        data = sources[path]
        if end > len(data) or hashlib.sha256(data[start:end]).hexdigest() != digest:
            raise AssertionError(f"independent snapshot span drift: {path}")
    return sources, tuple(repository_paths)


@lru_cache(maxsize=1)
def oracle_inventory_sources() -> dict[str, bytes]:
    """Return source bytes from the independently bound shallow snapshot."""
    return oracle_inventory_snapshot()[0]


@lru_cache(maxsize=1)
def oracle_tree_paths() -> tuple[str, ...]:
    """Enumerate the frozen tree without using the production path reader."""
    if oracle_source_mode() == "git":
        process = oracle_git(
            "ls-tree",
            "-r",
            "-z",
            "--name-only",
            ORACLE_SOURCE_REF,
            limit=ORACLE_MAX_GIT_OUTPUT,
        )
        if process.returncode != 0:
            raise AssertionError("independent oracle could not enumerate source paths")
        raw = process.stdout
        path_count = raw.count(b"\0")
        if (
            len(raw) > ORACLE_MAX_GIT_OUTPUT
            or not raw
            or not raw.endswith(b"\0")
            or raw.startswith(b"\0")
            or b"\0\0" in raw
        ):
            raise AssertionError(
                "independent source path inventory is not canonically framed"
            )
        if path_count > ORACLE_MAX_FROZEN_TREE_PATHS:
            raise AssertionError(
                "independent source path inventory exceeds count limit"
            )
        try:
            paths = tuple(
                item.decode("utf-8", errors="strict")
                for item in raw.split(b"\0")[:-1]
            )
        except UnicodeDecodeError as exc:
            raise AssertionError("independent source path is not UTF-8") from exc
    else:
        _, paths = oracle_inventory_snapshot()
    if (
        not paths
        or len(paths) > ORACLE_MAX_FROZEN_TREE_PATHS
        or list(paths) != sorted(set(paths))
    ):
        raise AssertionError("independent source path inventory is not canonical")
    for path in paths:
        try:
            encoded = path.encode("utf-8", errors="strict")
        except UnicodeEncodeError as exc:
            raise AssertionError("independent source path is unsafe") from exc
        candidate = PurePosixPath(path)
        if (
            len(encoded) > 1_024
            or any(byte < 0x20 or byte > 0x7E for byte in encoded)
            or path == "."
            or candidate.is_absolute()
            or "\\" in path
            or candidate.as_posix() != path
            or any(part in {"", ".", ".."} for part in candidate.parts)
        ):
            raise AssertionError("independent source path is unsafe")
    return paths


def oracle_source(path: str) -> bytes:
    """Read the frozen blob without importing the production source reader."""
    if path in ORACLE_SOURCE_CACHE:
        expected = ORACLE_SOURCE_CACHE[path]
    elif oracle_source_mode() == "git":
        process = oracle_git(
            "cat-file",
            "blob",
            f"{ORACLE_SOURCE_REF}:{path}",
            limit=ORACLE_MAX_SOURCE_BYTES,
        )
        if process.returncode != 0:
            raise AssertionError(f"independent oracle could not read {path}")
        if len(process.stdout) > ORACLE_MAX_SOURCE_BYTES:
            raise AssertionError("independent source blob exceeds byte limit")
        expected = process.stdout
    else:
        expected = oracle_inventory_sources().get(path)
        if expected is None:
            raise AssertionError(f"independent oracle has no snapshot source: {path}")
    live = oracle_read_regular(ROOT / path, ORACLE_MAX_SOURCE_BYTES)
    if live != expected:
        raise AssertionError(f"independent oracle observed source drift: {path}")
    ORACLE_SOURCE_CACHE[path] = expected
    return expected


def oracle_head_oid() -> str:
    """Resolve one immutable parent-test authority before reading its objects."""
    process = oracle_git(
        "rev-parse", "--verify", "HEAD^{commit}", limit=128
    )
    if (
        process.returncode != 0
        or process.stderr
        or not re.fullmatch(rb"(?:[0-9a-f]{40}|[0-9a-f]{64})\n", process.stdout)
    ):
        raise AssertionError("independent tracked oracle commit is unavailable")
    return process.stdout[:-1].decode("ascii")


def oracle_parent_blob_oid(oid: str, path: str) -> str:
    """Resolve one typed blob identity below an already-resolved commit."""
    expression = f"{oid}:{path}"
    probe = oracle_git(
        "cat-file",
        "--batch-check=%(objectname) %(objecttype)",
        input_data=f"{expression}\n".encode("ascii"),
        limit=128,
    )
    match = re.fullmatch(rb"([0-9a-f]{40}|[0-9a-f]{64}) blob\n", probe.stdout)
    if (
        probe.returncode != 0
        or probe.stderr
        or match is None
        or len(match.group(1)) != len(oid)
    ):
        raise AssertionError("independent tracked oracle dependencies unavailable")
    return match.group(1).decode("ascii")


def oracle_blob_oid(data: bytes, oid_length: int) -> str:
    """Compute the repository-format Git identity for exact blob bytes."""
    header = f"blob {len(data)}\0".encode("ascii")
    if oid_length == 40:
        hasher = hashlib.sha1(usedforsecurity=False)
    elif oid_length == 64:
        hasher = hashlib.sha256()
    else:
        raise AssertionError("independent tracked oracle object format is invalid")
    hasher.update(header)
    hasher.update(data)
    return hasher.hexdigest()


def oracle_parent_step1_dependencies(source: bytes) -> tuple[str, ...]:
    """Read the immutable dependency declaration from the exact parent test."""
    try:
        tree = ast.parse(source.decode("utf-8"), filename="<parent-test>")
    except (SyntaxError, UnicodeError) as exc:
        raise AssertionError(
            "independent tracked oracle dependency declaration is malformed"
        ) from exc
    declarations = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name)
            and target.id == "ORACLE_STEP1_PARENT_DEPENDENCIES"
            for target in node.targets
        ):
            continue
        declarations.append(node.value)
    if len(declarations) != 1 or not isinstance(declarations[0], ast.Tuple):
        raise AssertionError(
            "independent tracked oracle dependency declaration is unavailable"
        )
    dependencies = []
    for element in declarations[0].elts:
        if not isinstance(element, ast.Constant) or not isinstance(
            element.value, str
        ):
            raise AssertionError(
                "independent tracked oracle dependency declaration is malformed"
            )
        path = element.value
        pure = PurePosixPath(path)
        if (
            not path
            or not path.isascii()
            or len(path.encode("ascii")) > 1_024
            or pure.is_absolute()
            or str(pure) != path
            or ".." in pure.parts
        ):
            raise AssertionError(
                "independent tracked oracle dependency declaration is malformed"
            )
        dependencies.append(path)
    if not dependencies or len(dependencies) != len(set(dependencies)):
        raise AssertionError(
            "independent tracked oracle dependency declaration is malformed"
        )
    return tuple(dependencies)


def oracle_assert_step1_parent_dependencies(
    oid: str, dependencies: tuple[str, ...] | None = None
) -> None:
    """Accept exact parent bytes or the two exact receipted append-only copies."""
    selected = ORACLE_STEP1_PARENT_DEPENDENCIES if dependencies is None else dependencies
    for path in selected:
        parent_blob_oid = oracle_parent_blob_oid(oid, path)
        live = oracle_read_regular(
            ROOT / path, ORACLE_MAX_STEP1_DEPENDENCY_BYTES
        )
        if oracle_blob_oid(live, len(oid)) == parent_blob_oid:
            continue
        if path not in ORACLE_RECEIPTED_APPEND_ONLY_DEPENDENCIES:
            raise AssertionError("independent tracked oracle dependency drift")
        parent = oracle_tracked_source(oid, path)
        prefix_is_exact = len(live) > len(parent) and live.startswith(parent)
        if path == "docs/instruction-architecture/runbook.md":
            terminal_is_receipted = (
                hashlib.sha256(live).hexdigest() == AMENDED_RUNBOOK_SHA256
            )
        elif path == "docs/instruction-architecture/study.md":
            terminal_is_receipted = (
                live.count(b"](../../plugins/") == 10
                and hashlib.sha256(
                    live.replace(b"](../../plugins/", b"](../plugins/")
                ).hexdigest()
                == RECEIPTED_STUDY_SHA256
            )
        else:
            terminal_is_receipted = False
        if (
            not prefix_is_exact or not terminal_is_receipted
        ):
            raise AssertionError("independent tracked oracle dependency drift")


def oracle_tracked_source(oid: str, path: str) -> bytes:
    """Read one bounded object from the already-resolved parent commit."""
    process = oracle_git(
        "show", f"{oid}:{path}", limit=ORACLE_MAX_GIT_OUTPUT
    )
    if (
        process.returncode != 0
        or process.stderr
        or not process.stdout
        or len(process.stdout) > ORACLE_MAX_GIT_OUTPUT
    ):
        raise AssertionError("independent tracked oracle object is unavailable")
    return process.stdout


def oracle_tracked_benchmark(
    source: bytes, oid: str, blob_oid: str | None = None
) -> types.ModuleType:
    """Compile the parent benchmark bytes without consulting the worktree."""
    module = types.ModuleType("tracked_instruction_architecture_benchmark")
    module.__file__ = str(SCRIPT)
    module.__source_oid__ = oid
    module.__source_sha256__ = hashlib.sha256(source).hexdigest()
    module.__source_blob_oid__ = blob_oid
    try:
        code = compile(source, module.__file__, "exec")
        # phylax: allow exact tracked benchmark bytes as bounded parent evidence
        exec(code, module.__dict__)
    except (SyntaxError, UnicodeError) as exc:
        raise AssertionError("independent tracked benchmark is malformed") from exc
    return module


def oracle_head_module() -> types.ModuleType:
    """Load parent code objects after its immutable live inputs match HEAD."""
    oid = oracle_head_oid()
    code_blob_oids = {
        path: oracle_parent_blob_oid(oid, path)
        for path in ORACLE_STEP2_PARENT_CODE_PATHS
    }
    code_sources = {
        path: oracle_tracked_source(oid, path)
        for path in ORACLE_STEP2_PARENT_CODE_PATHS
    }
    for path in ORACLE_STEP2_PARENT_CODE_PATHS:
        if oracle_blob_oid(code_sources[path], len(oid)) != code_blob_oids[path]:
            raise AssertionError("independent tracked oracle object identity drift")
    benchmark_path, test_path = ORACLE_STEP2_PARENT_CODE_PATHS
    benchmark_source = code_sources[benchmark_path]
    test_source = code_sources[test_path]
    parent_dependencies = oracle_parent_step1_dependencies(test_source)
    parent_code_dependencies = tuple(
        path for path in parent_dependencies if path in ORACLE_STEP2_PARENT_CODE_PATHS
    )
    if parent_code_dependencies != (benchmark_path,) or test_path in parent_dependencies:
        raise AssertionError(
            "independent tracked oracle compatibility boundary drift"
        )
    immutable_dependencies = tuple(
        path for path in parent_dependencies if path not in ORACLE_STEP2_PARENT_CODE_PATHS
    )
    oracle_assert_step1_parent_dependencies(oid, immutable_dependencies)

    class TrackedBenchmarkLoader:
        def create_module(self, _spec):
            return None

        def exec_module(self, target):
            tracked = oracle_tracked_benchmark(
                benchmark_source, oid, code_blob_oids[benchmark_path]
            )
            target.__dict__.update(tracked.__dict__)

    loader = TrackedBenchmarkLoader()
    tracked_spec = importlib.util.spec_from_loader(
        "instruction_architecture", loader, origin=str(SCRIPT)
    )
    if tracked_spec is None:
        raise AssertionError("independent tracked benchmark is unavailable")
    real_spec = importlib.util.spec_from_file_location

    def parent_spec(name, location, *arguments, **keywords):
        if name == "instruction_architecture" and Path(location) == SCRIPT:
            return tracked_spec
        return real_spec(name, location, *arguments, **keywords)

    module = types.ModuleType("tracked_instruction_architecture_oracle")
    module.__file__ = str(Path(__file__).resolve())
    try:
        code = compile(test_source, module.__file__, "exec")
        with mock.patch.object(
            importlib.util, "spec_from_file_location", side_effect=parent_spec
        ):
            # phylax: allow exact tracked test bytes as bounded parent evidence
            exec(code, module.__dict__)
    except (SyntaxError, UnicodeError) as exc:
        raise AssertionError("independent tracked oracle is malformed") from exc

    def load_tracked_benchmark():
        return oracle_tracked_benchmark(
            benchmark_source, oid, code_blob_oids[benchmark_path]
        )

    module.AI = load_tracked_benchmark()
    module.load_module = load_tracked_benchmark
    module.__source_oid__ = oid
    module.__source_sha256__ = hashlib.sha256(test_source).hexdigest()
    module.__source_blob_oid__ = code_blob_oids[test_path]
    module.__immutable_dependency_count__ = len(immutable_dependencies)
    return module


def oracle_guard_module() -> types.ModuleType:
    """Route ordinary guards to candidate and the supplemental helper to HEAD."""
    authority = os.environ.get("FIAT1046_ELENCHUS_PARENT")
    if authority is None:
        return sys.modules[__name__]
    if authority != "1":
        raise AssertionError("independent oracle guard authority is invalid")
    return oracle_head_module()


def oracle_evidence(obligation: str, path: str, needle: str) -> dict:
    """Build one test-owned frozen span without production evidence helpers."""
    data = oracle_source(path)
    encoded = needle.encode("utf-8")
    start = data.find(encoded)
    if start < 0:
        raise AssertionError(f"independent semantic anchor is absent: {path}")
    return {
        "obligation": obligation,
        "path": path,
        "start": start,
        "end": start + len(encoded),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "span_sha256": hashlib.sha256(encoded).hexdigest(),
    }


def oracle_span(path: str, needle: str) -> dict:
    """Build test-owned evidence without an obligation projection field."""
    evidence = oracle_evidence("", path, needle)
    del evidence["obligation"]
    return evidence


def oracle_manifest_source_anchor(path: str) -> tuple[str, str, str]:
    """Resolve all manifest source relations without production metadata."""
    anchors = {
        ".python-version": (
            "fixed_input",
            "AGENTS.md",
            "Every `python3` command below means the exact interpreter recorded in\n"
            "[`.python-version`](.python-version).",
        ),
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["hermes"],
            "Every candidate names a rule from "
            "[references/gas-rule-corpus.json](references/gas-rule-corpus.json)",
        ),
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["hermes"],
            "A corpus that fails its own schema",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "`gated.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "`hard.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "`structural.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/agent-replies.md": (
            "markdown_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "references/agent-replies.md",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md": (
            "markdown_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "references/lexicon-rationale.md",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/rewriting.md": (
            "markdown_reference",
            ORACLE_SKILL_PATHS["imprimatur"],
            "references/rewriting.md",
        ),
        "plugins/hexaemeron/skills/solidity-auditor/VERSION": (
            "fixed_input",
            ORACLE_SKILL_PATHS["solidity-auditor"],
            "Read the local `VERSION` file from the same directory as this skill",
        ),
        "plugins/hexaemeron/skills/x-ray/VERSION": (
            "fixed_input",
            ORACLE_SKILL_PATHS["x-ray"],
            "Read the local `VERSION` file from `$SKILL_DIR/VERSION`",
        ),
        "plugins/homologia/references/manifest-v1.schema.json": (
            "structured_reference",
            "plugins/homologia/docs/checked-inputs/runbook.md",
            "plugins/homologia/references/manifest-v1.schema.json",
        ),
        "plugins/homologia/references/vectors-v1.schema.json": (
            "structured_reference",
            "plugins/homologia/docs/checked-inputs/runbook.md",
            "plugins/homologia/references/vectors-v1.schema.json",
        ),
        "plugins/pandects/docs/applicability.md": (
            "operation_reference",
            ORACLE_SKILL_PATHS["pandects"],
            "`docs/applicability.md` states the rules once",
        ),
        "plugins/pandects/docs/writing-a-law.md": (
            "operation_reference",
            ORACLE_SKILL_PATHS["pandects"],
            "`docs/writing-a-law.md`",
        ),
        "plugins/pandects/integrations/wildcat/APPLICABILITY.md": (
            "operation_reference",
            ORACLE_SKILL_PATHS["pandects"],
            "`integrations/wildcat/APPLICABILITY.md` carries all of them",
        ),
        "plugins/synkrisis/references/rules-v1.json": (
            "structured_reference",
            ORACLE_SKILL_PATHS["synkrisis"],
            "python3 plugins/synkrisis/scripts/synkrisis.py diagnose \\\n"
            "  --cohort build/synkrisis/cohort.json \\\n"
            "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
            "  --out build/synkrisis/findings.json",
        ),
    }
    for name in (
        "cohort-v1.schema.json",
        "findings-v1.schema.json",
        "policy-v1.schema.json",
        "rule-v1.schema.json",
    ):
        candidate = f"plugins/synkrisis/references/{name}"
        anchors[candidate] = (
            "structured_reference",
            candidate,
            f'"$id": "https://github.com/wildcat-finance/skills/{candidate}"',
        )
    try:
        return anchors[path]
    except KeyError as error:
        raise AssertionError(
            f"independent manifest source relation is unowned: {path}"
        ) from error


def oracle_runtime_anchor(target: str, context: str) -> tuple[str, str]:
    """Resolve every executable input through a test-owned runtime grammar."""
    if target == "plugins/hermes/skills/hermes/references/gas-rule-corpus.json":
        return (
            "plugins/hermes/skills/hermes/scripts/hermes.py",
            "raw = corpus_path.read_bytes()",
        )
    if target == "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json":
        return (
            "plugins/hermes/skills/hermes/scripts/hermes.py",
            'schema = json.loads(schema_path.read_text(encoding="utf-8"))',
        )
    if target in {
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
    }:
        return (
            "plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py",
            'return rd("hard.json"), rd("gated.json"), rd("structural.json")',
        )
    if target != "plugins/synkrisis/references/rules-v1.json":
        raise AssertionError(
            f"independent runtime target is unowned: {target}"
        )
    needles = {
        "manifest": (
            "def load_rules(root: Path, raw_path: str, budget: InputBudget):\n"
            '    target = confined_relative(raw_path, root, label="rules")\n'
            "    shown = shown_path(raw_path)\n"
            "    payload = bounded_read(target, shown, MAX_FILE_BYTES)"
        ),
        "diagnose": (
            "def command_diagnose(root: Path, arguments):\n"
            "    budget = InputBudget()\n"
            "    cohort = load_cohort(root, arguments.cohort, budget)\n"
            "    rules_document, _ = load_rules(root, arguments.rules, budget)"
        ),
        "verify": (
            '            "rebuild the cohort with the cohort command from the original inputs",\n'
            "        )\n"
            "    rules_document, _ = load_rules(root, arguments.rules, budget)"
        ),
    }
    try:
        return "plugins/synkrisis/scripts/synkrisis.py", needles[context]
    except KeyError as error:
        raise AssertionError(
            f"independent Synkrisis runtime context is unowned: {context}"
        ) from error


def oracle_validate_manifest_semantic_anchors(manifest: dict) -> None:
    """Close every manifest source/runtime row under test-owned anchors."""
    source_counts = {
        name: 0 for name in ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS
    }
    runtime_counts = {
        target: 0 for target in ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS
    }
    documents = manifest.get("documents")
    if not isinstance(documents, list):
        raise AssertionError("independent manifest document ledger is not an array")
    for item in documents:
        evidence = item.get("source_evidence")
        if evidence is not None:
            evidence_class, source, needle = oracle_manifest_source_anchor(
                item["path"]
            )
            if (
                item.get("document_class") != evidence_class
                or evidence != oracle_span(source, needle)
            ):
                raise AssertionError(
                    f"independent manifest source anchor mismatch: {item['path']}"
                )
            source_counts[evidence_class] += 1
        runtime = item.get("runtime_evidence")
        if runtime is not None:
            runtime_path, runtime_needle = oracle_runtime_anchor(
                item["path"], "manifest"
            )
            if runtime != oracle_span(runtime_path, runtime_needle):
                raise AssertionError(
                    f"independent manifest runtime anchor mismatch: {item['path']}"
                )
            runtime_counts[item["path"]] += 1
    if source_counts != ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS or sum(
        source_counts.values()
    ) != sum(item.get("source_evidence") is not None for item in documents):
        raise AssertionError("independent manifest source coverage mismatch")
    if runtime_counts != ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS or sum(
        runtime_counts.values()
    ) != sum(item.get("runtime_evidence") is not None for item in documents):
        raise AssertionError("independent manifest runtime coverage mismatch")


def oracle_validate_runtime_edges(record: dict, graph: dict) -> None:
    """Close every host/scenario runtime row under test-owned anchors."""
    profiles = {
        row["id"]: row for row in record.get("profiles", [])
    }
    roots = {
        row["id"]: row for row in graph.get("scenario_roots", [])
    }
    runtime_counts = {
        target: 0 for target in ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS
    }
    validated_scenario_relations: dict[
        tuple[str, str, str, str], list[dict]
    ] = {}
    scenario_rows = 0
    scenario_edges = graph.get("scenario_edges", [])
    if not isinstance(scenario_edges, list):
        raise AssertionError("independent scenario edge ledger is not an array")
    for edge in scenario_edges:
        runtime = edge.get("runtime_evidence")
        mandatory = edge.get("load_type") == "mandatory-executable"
        if (runtime is not None) != mandatory:
            raise AssertionError(
                f"independent scenario runtime presence mismatch: {edge.get('id')}"
            )
        if runtime is None:
            continue
        target = edge.get("target")
        context = "scenario"
        if target == "plugins/synkrisis/references/rules-v1.json":
            operations = set()
            for identifier in edge.get("active_scenarios", []):
                root = roots.get(identifier)
                if root is None or root.get("profile_id") not in profiles:
                    raise AssertionError(
                        "independent Synkrisis runtime scope escapes route roots"
                    )
                state = profiles[root["profile_id"]].get("branch_state")
                if not isinstance(state, list) or not state:
                    raise AssertionError(
                        "independent Synkrisis runtime profile has no branch state"
                    )
                operations.add(state[-1])
            if len(operations) != 1 or not operations <= {"diagnose", "verify"}:
                raise AssertionError(
                    "independent Synkrisis runtime scope mixes operations"
                )
            context = next(iter(operations))
        runtime_path, runtime_needle = oracle_runtime_anchor(target, context)
        if runtime != oracle_span(runtime_path, runtime_needle):
            raise AssertionError(
                f"independent scenario runtime anchor mismatch: {edge.get('id')}"
            )
        relation = (
            edge.get("source"),
            target,
            edge.get("kind"),
            edge.get("load_type"),
        )
        validated_scenario_relations.setdefault(relation, []).append(runtime)
        runtime_counts[target] += 1
        scenario_rows += 1

    host_rows = 0
    host_edges = graph.get("edges", [])
    if not isinstance(host_edges, list):
        raise AssertionError("independent host edge ledger is not an array")
    for edge in host_edges:
        runtime = edge.get("runtime_evidence")
        mandatory = edge.get("load_type") == "mandatory-executable"
        if (runtime is not None) != mandatory:
            raise AssertionError(
                f"independent host runtime presence mismatch: {edge.get('id')}"
            )
        if runtime is None:
            continue
        relation = (
            edge.get("source"),
            edge.get("target"),
            edge.get("kind"),
            edge.get("load_type"),
        )
        if runtime not in validated_scenario_relations.get(relation, []):
            raise AssertionError(
                f"independent host runtime anchor mismatch: {edge.get('id')}"
            )
        runtime_counts[edge["target"]] += 1
        host_rows += 1
    if (
        scenario_rows != 12
        or host_rows != 11
        or runtime_counts != ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS
    ):
        raise AssertionError("independent graph runtime coverage mismatch")


def cross_target_runtime_specimens(
    rows: list[dict], target_field: str
) -> dict[str, tuple[int, str, dict]]:
    """Choose one valid runtime span from a different implementation per target."""
    specimens: dict[str, tuple[int, str, dict]] = {}
    for index, row in enumerate(rows):
        runtime = row.get("runtime_evidence")
        target = row.get(target_field)
        if runtime is None or target in specimens:
            continue
        for donor in rows:
            donor_runtime = donor.get("runtime_evidence")
            donor_target = donor.get(target_field)
            if (
                donor_runtime is not None
                and donor_target != target
                and donor_runtime["path"] != runtime["path"]
                and donor_runtime != runtime
            ):
                specimens[target] = (
                    index,
                    donor_target,
                    copy.deepcopy(donor_runtime),
                )
                break
    if set(specimens) != set(ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS):
        raise AssertionError("runtime rebind specimens do not cover every target")
    return specimens


def oracle_semantic_anchor(profile: dict, obligation: str) -> tuple[str, str]:
    """Name exact skill/frontier relations from the frozen source grammar."""
    selected_skill = profile["selected_skill"]
    selected = ORACLE_SKILL_PATHS[selected_skill]
    skill_by_path = {path: skill for skill, path in ORACLE_SKILL_PATHS.items()}
    if obligation == selected:
        return selected, f"name: {selected_skill}"

    if obligation.endswith("/EVOLUTION.md"):
        selected_evolution = str(Path(selected).with_name("EVOLUTION.md")).replace(
            os.sep, "/"
        )
        if obligation == selected_evolution:
            return selected, "[EVOLUTION.md](EVOLUTION.md)"
        if selected_skill != "kronos":
            raise AssertionError("independent frontier relation escaped Kronos")
        return (
            selected,
            "Walk the whole scope and find every `EVOLUTION.md` beneath it, descending\n"
            "   into each plugin's own skills directory.",
        )

    if not obligation.endswith("/SKILL.md") or obligation not in skill_by_path:
        raise AssertionError("independent semantic anchor received a non-skill path")
    target_skill = skill_by_path[obligation]

    if selected_skill == "kronos":
        dispatch = profile["branch_state"][-1]
        if not dispatch.startswith("dispatch-"):
            raise AssertionError("independent Kronos relation escaped dispatch")
        if target_skill not in {"fiat", dispatch.removeprefix("dispatch-")}:
            raise AssertionError("independent Kronos dispatch target mismatch")
        return (
            selected,
            "Read the selected skill's canonical instructions, its ledger, and Fiat's\n"
            "   `SKILL.md`.",
        )

    if selected_skill == "fiat":
        direct = {
            name: f"[{name}](../{name}/SKILL.md)"
            for name in (
                "protasis",
                "phylax",
                "ephoros",
                "metron",
                "elenchus",
                "hypomnema",
            )
        }
        if target_skill in direct:
            return selected, direct[target_skill]
        if target_skill == "brevitas":
            return (
                "plugins/hexaemeron/agents/scribe.md",
                "Where an artefact is engineering review, audit, gas, protocol-property, or\n"
                "specification commentary, apply Brevitas after the vocabulary and register\n"
                "passes without deleting evidence.",
            )
        if target_skill == "hermes":
            return (
                "plugins/hexaemeron/agents/mason.md",
                "Hermes owns Solidity gas. Do not silently import a sibling's job into the step.",
            )
        if target_skill == "fizz-sync":
            return (
                ORACLE_SKILL_PATHS["elenchus"],
                "When the fix touched contracts, run `fizz-sync` first.",
            )
        if target_skill == "fizz":
            return (
                "plugins/hexaemeron/agents/warden.md",
                "`fizz`\nis in the suite, follow `<plugin-root>/skills/fizz/SKILL.md`",
            )
        if target_skill in {"x-ray", "solidity-auditor"}:
            return (
                "plugins/hexaemeron/skills/fiat/references/audit-loop.md",
                "`x-ray` pass first, then `solidity-auditor`. Both are vendored under\n"
                "   `$PLUGIN_ROOT/skills/<name>/` (as defined in the entry skill) -- read\n"
                "   each SKILL.md and follow\n"
                "   it.",
            )
        if target_skill == "imprimatur":
            if profile["phase"] == "prose directive":
                return (
                    "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                    '`python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" <file>`',
                )
            if profile["id"] == "fiat:integrate-task-issue":
                return (
                    selected,
                    "under the repository's Sapheneia,\n"
                    "Imprimatur, Vulgate, Imprimatur publication order.",
                )
            return selected, "Run the `imprimatur` lint on each artefact before receipting it"
        if target_skill == "vulgate":
            return (
                "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                "$PLUGIN_ROOT/skills/vulgate/SKILL.md",
            )
        if target_skill == "sapheneia":
            if profile["phase"] in {"Solidity audit round", "non-Solidity audit round"}:
                return (
                    "plugins/hexaemeron/skills/fiat/references/audit-loop.md",
                    "apply Sapheneia's bounded audit-record operation",
                )
            if profile["phase"] == "prose directive":
                return (
                    "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                    "Sapheneia -> Imprimatur -> Vulgate -> Imprimatur",
                )
            return (
                selected,
                "under the repository's Sapheneia,\n"
                "Imprimatur, Vulgate, Imprimatur publication order.",
            )
        raise AssertionError(f"independent Fiat skill relation is unowned: {target_skill}")

    if selected_skill == "fizz" and target_skill == "x-ray":
        return (
            selected,
            "Resolve `{SKILL_PATH}/../x-ray/SKILL.md`, read it completely, and execute "
            "its instructions against `{PROJECT_ROOT}`.",
        )
    if selected_skill == "elenchus" and target_skill == "fizz-sync":
        return selected, "When the fix touched contracts, run `fizz-sync` first."
    if selected_skill == "ephoros" and target_skill == "phylax":
        return selected, "`phylax` sets this rule and this skill inherits it"
    if selected_skill == "protasis" and target_skill in {
        "ephoros",
        "phylax",
        "metron",
        "elenchus",
        "hypomnema",
    }:
        return selected, f"[{target_skill}](../{target_skill}/SKILL.md)"
    raise AssertionError(
        f"independent skill relation is unowned: {selected_skill} -> {target_skill}"
    )


def oracle_document_anchor(selected_skill: str, obligation: str) -> tuple[str, str]:
    """Resolve document relations from a test-owned, closed source grammar."""
    fiat = ORACLE_SKILL_PATHS["fiat"]
    fizz = ORACLE_SKILL_PATHS["fizz"]
    solidity = ORACLE_SKILL_PATHS["solidity-auditor"]
    xray = ORACLE_SKILL_PATHS["x-ray"]
    name = Path(obligation).name
    if (
        selected_skill == "kronos"
        and obligation
        == "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"
    ):
        return (
            ORACLE_SKILL_PATHS["kronos"],
            "`../fiat/references/plugin-currency.md` names the host\n"
            "   mechanism.",
        )
    if obligation.startswith("plugins/hexaemeron/skills/fiat/references/"):
        source = fiat
        if name == "xray-reuse.md":
            source = "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
        elif name == "controller-checkpoint.md":
            source = "plugins/hexaemeron/skills/fiat/references/push-discipline.md"
        return source, name
    if obligation == "plugins/hermes/skills/hermes/references/optimisation-catalogue.md":
        return ORACLE_SKILL_PATHS["hermes"], "references/optimisation-catalogue.md"
    if obligation == "plugins/hexaemeron/skills/metron/references/budget-check.md":
        return ORACLE_SKILL_PATHS["metron"], "references/budget-check.md"
    if obligation == "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md":
        return ORACLE_SKILL_PATHS["phylax"], name
    if obligation.startswith("plugins/hexaemeron/skills/fizz/references/"):
        if name == "property-generation.md" and selected_skill == "fiat":
            return (
                "plugins/hexaemeron/skills/fizz/agents/implementers/"
                "specific-property-implementer.md",
                name,
            )
        return fizz, name
    if obligation.startswith("plugins/hexaemeron/skills/solidity-auditor/references/"):
        if name == "shared-rules.md":
            if selected_skill == "solidity-auditor":
                return solidity, "references/hacking-agents/shared-rules.md"
            return (
                "plugins/hexaemeron/skills/solidity-auditor/references/"
                "senior-auditor-sop.md",
                name,
            )
        if name == "senior-auditor-sop.md" and selected_skill != "solidity-auditor":
            return (
                "plugins/hexaemeron/skills/solidity-auditor/references/"
                "hacking-agents/shared-rules.md",
                name,
            )
        return solidity, name
    if obligation == "plugins/hexaemeron/skills/x-ray/references/templates.md":
        if selected_skill == "x-ray":
            return xray, "references/templates.md"
        return "plugins/hexaemeron/skills/x-ray/references/threats.md", name
    if obligation == "plugins/hexaemeron/skills/x-ray/references/threats.md":
        return xray, "references/threats.md"
    if obligation in {
        "plugins/probitas/skills/probitas/references/gates.md",
        "plugins/probitas/skills/probitas/references/venues.md",
    }:
        return ORACLE_SKILL_PATHS["probitas"], f"references/{name}"
    raise AssertionError(f"independent document relation is unowned: {obligation}")


def oracle_python_pin_anchor(profile: dict) -> tuple[str, str]:
    """Resolve the pin through a test-owned exact operation allowlist."""
    anchors = {
        "anamnesis:demo-or-rebuild": (
            ORACLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "anamnesis:ordinary": (
            ORACLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "berean:ordinary": (
            ORACLE_SKILL_PATHS["berean"],
            "Run everything from `$PLUGIN_ROOT` with the exact interpreter in the suite\n"
            "[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version)",
        ),
        "brevitas:ordinary": (
            "plugins/brevitas/AGENTS.md",
            "- Run the checker with the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version)",
        ),
        "hermes:gas-operation": (
            "plugins/hermes/AGENTS.md",
            "Run the harness with\n  the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "lemma:changed-or-unexpected": (
            "plugins/lemma/AGENTS.md",
            "- Use the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "lemma:ordinary": (
            "plugins/lemma/AGENTS.md",
            "- Use the exact interpreter in the suite\n"
            "  [pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "probitas:add-venue": (
            "plugins/probitas/docs/adding-a-venue.md",
            "Run this with the exact interpreter in the suite\n"
            "[pin](https://github.com/wildcat-finance/skills/blob/main/.python-version).",
        ),
        "synkrisis:cohort-or-render": (
            ORACLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:diagnose": (
            ORACLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:verify": (
            ORACLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
    }
    try:
        return anchors[profile["id"]]
    except (KeyError, TypeError) as error:
        raise AssertionError(
            f"independent Python pin relation is unowned: {profile.get('id')}"
        ) from error


def oracle_full_semantic_anchor(
    profile: dict, obligation: str
) -> tuple[str, str, str]:
    """Classify every obligation and derive one test-owned semantic anchor."""
    selected_skill = profile["selected_skill"]
    selected = ORACLE_SKILL_PATHS[selected_skill]
    if obligation == selected:
        source, needle = oracle_semantic_anchor(profile, obligation)
        return "selected_skill", source, needle
    if obligation.endswith("/EVOLUTION.md"):
        source, needle = oracle_semantic_anchor(profile, obligation)
        return "frontier_ledger", source, needle
    if obligation.endswith("/SKILL.md"):
        source, needle = oracle_semantic_anchor(profile, obligation)
        return "related_skill", source, needle

    if obligation in EXPECTED_OPERATION_REFERENCES:
        source = selected
        if obligation == "plugins/probitas/docs/adding-a-venue.md":
            source = "plugins/probitas/skills/probitas/references/venues.md"
        return (
            "operation_reference",
            source,
            posixpath.relpath(obligation, posixpath.dirname(source)),
        )

    fiat_workers = {
        "plugins/hexaemeron/agents/mason.md",
        "plugins/hexaemeron/agents/scribe.md",
        "plugins/hexaemeron/agents/surveyor.md",
        "plugins/hexaemeron/agents/warden.md",
    }
    if obligation in fiat_workers:
        return "worker_prompt", ORACLE_SKILL_PATHS["fiat"], f"`{Path(obligation).stem}`"
    if obligation.startswith("plugins/hexaemeron/skills/fizz/agents/"):
        return (
            "worker_prompt",
            ORACLE_SKILL_PATHS["fizz"],
            posixpath.relpath(
                obligation, posixpath.dirname(ORACLE_SKILL_PATHS["fizz"])
            ),
        )
    if obligation == "plugins/hexaemeron/PROMISES.md":
        return (
            "overlay_contract",
            "plugins/hexaemeron/AGENTS.md",
            "[PROMISES.md](PROMISES.md)",
        )
    if obligation == "plugins/hexaemeron/skills/VERSIONING.md":
        return (
            "frontier_policy",
            "plugins/hexaemeron/AGENTS.md",
            "`skills/VERSIONING.md`",
        )

    if obligation == ".python-version":
        source, needle = oracle_python_pin_anchor(profile)
        return "fixed_input", source, needle

    if obligation in ORACLE_FIXED_INPUTS:
        if obligation == "plugins/hexaemeron/skills/x-ray/VERSION":
            return (
                "fixed_input",
                ORACLE_SKILL_PATHS["x-ray"],
                "Read the local `VERSION` file from `$SKILL_DIR/VERSION`",
            )
        if obligation == "plugins/hexaemeron/skills/solidity-auditor/VERSION":
            return (
                "fixed_input",
                ORACLE_SKILL_PATHS["solidity-auditor"],
                "Read the local `VERSION` file from the same directory as this skill",
            )
        if obligation == "plugins/hermes/skills/hermes/references/gas-rule-corpus.json":
            return (
                "structured_reference",
                ORACLE_SKILL_PATHS["hermes"],
                "Every candidate names a rule from "
                "[references/gas-rule-corpus.json](references/gas-rule-corpus.json)",
            )
        if obligation == "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json":
            return (
                "structured_reference",
                ORACLE_SKILL_PATHS["hermes"],
                "A corpus that fails its own schema",
            )
        if obligation.startswith("plugins/hexaemeron/skills/imprimatur/lexicon/"):
            return (
                "structured_reference",
                ORACLE_SKILL_PATHS["imprimatur"],
                f"`{Path(obligation).name}`",
            )
        if obligation == "plugins/synkrisis/references/rules-v1.json":
            needles = {
                "diagnose": (
                    "python3 plugins/synkrisis/scripts/synkrisis.py diagnose \\\n"
                    "  --cohort build/synkrisis/cohort.json \\\n"
                    "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
                    "  --out build/synkrisis/findings.json"
                ),
                "verify": (
                    "python3 plugins/synkrisis/scripts/synkrisis.py verify \\\n"
                    "  --manifest plugins/synkrisis/examples/cross-run-v0/manifest.json \\\n"
                    "  --policy plugins/synkrisis/examples/cross-run-v0/policy.json \\\n"
                    "  --cohort build/synkrisis/cohort.json \\\n"
                    "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
                    "  --findings build/synkrisis/findings.json"
                ),
            }
            operation = profile["branch_state"][-1]
            if operation not in needles:
                raise AssertionError("independent Synkrisis operation drift")
            return "structured_reference", ORACLE_SKILL_PATHS["synkrisis"], needles[operation]
        raise AssertionError(f"independent fixed relation is unowned: {obligation}")

    source, needle = oracle_document_anchor(selected_skill, obligation)
    return "document_reference", source, needle


def oracle_validate_semantic_anchors(profile: dict) -> dict[str, int]:
    """Require all obligations to carry independently derived semantic anchors."""
    evidence_by_obligation = {
        row["obligation"]: row for row in profile["source_evidence"]
    }
    counts = {name: 0 for name in ORACLE_PROFILE_EVIDENCE_COUNTS}
    for obligation in profile["required_documents"]:
        evidence_class, path, needle = oracle_full_semantic_anchor(profile, obligation)
        if evidence_class not in counts:
            raise AssertionError(
                f"independent semantic class is unowned: {evidence_class}"
            )
        expected = oracle_evidence(obligation, path, needle)
        if evidence_by_obligation.get(obligation) != expected:
            raise AssertionError(
                f"independent semantic anchor mismatch: {profile['id']}: {obligation}"
            )
        counts[evidence_class] += 1
    if sum(counts.values()) != len(profile["required_documents"]):
        raise AssertionError(f"independent semantic coverage gap: {profile['id']}")
    return counts


def oracle_add_profile(
    profiles: list[dict],
    skill: str,
    local_id: str,
    phase: str,
    documents: tuple[str, ...] = (),
    workers: tuple[str, ...] = (),
) -> None:
    required = sorted({ORACLE_SKILL_PATHS[skill], *documents})
    worker_prompts = sorted(set(workers))
    profiles.append(
        {
            "id": f"{skill}:{local_id}",
            "selected_skill": skill,
            "phase": phase,
            "applicability": f"bounded-operation:{skill}:{phase}",
            "branch_state": local_id.split("__"),
            "exclusive_group": f"{skill}:{phase}",
            "required_documents": required,
            "worker_prompts": worker_prompts,
            "fixed_inputs": [
                {"path": path, "load_semantics": ORACLE_FIXED_INPUTS[path]}
                for path in required
                if path in ORACLE_FIXED_INPUTS
            ],
        }
    )


def oracle_profiles() -> list[dict]:
    """Reconstruct the frozen bounded-operation grammar without production code."""
    rows: list[dict] = []
    evolution = {
        name: str(Path(path).with_name("EVOLUTION.md")).replace(os.sep, "/")
        for name, path in ORACLE_SKILL_PATHS.items()
        if name
        not in {"fizz", "fizz-convert", "fizz-sync", "solidity-auditor", "x-ray"}
    }
    versioning = "plugins/hexaemeron/skills/VERSIONING.md"
    promises = "plugins/hexaemeron/PROMISES.md"
    python_pin = (".python-version",)
    xray_version = "plugins/hexaemeron/skills/x-ray/VERSION"
    sol_aud_version = "plugins/hexaemeron/skills/solidity-auditor/VERSION"

    def add(
        skill: str,
        local_id: str,
        phase: str,
        documents: tuple[str, ...] = (),
        workers: tuple[str, ...] = (),
    ) -> None:
        oracle_add_profile(rows, skill, local_id, phase, documents, workers)

    def frontier(skill: str) -> None:
        add(skill, "frontier-gate", "gate-only frontier admission", (evolution[skill], versioning))

    add("alexandria", "ordinary", "capture/query/release")
    add(
        "alexandria",
        "ethereum-usdc-interval",
        "Ethereum USDC interval capture",
        (
            "plugins/alexandria/docs/usdc-interval-collector.md",
            "plugins/alexandria/docs/study.md",
            "plugins/alexandria/docs/runbook.md",
        ),
    )
    frontier("alexandria")
    add("anamnesis", "ordinary", "capture/verify/release", python_pin)
    add(
        "anamnesis",
        "demo-or-rebuild",
        "demo or verify-rebuild",
        python_pin + ("plugins/anamnesis/docs/demo.md",),
    )
    frontier("anamnesis")
    add("ariadne", "ordinary", "inspect/verify/replay")
    for local_id, phase, documents in (
        ("capture-release", "capture release", ("plugins/ariadne/docs/capturing-a-release.md", "plugins/ariadne/docs/solidity-release.md")),
        ("capture-dataset", "capture dataset", ("plugins/ariadne/docs/capturing-a-dataset.md", "plugins/ariadne/docs/dataset.md")),
        ("capture-state-fixture", "capture state fixture", ("plugins/ariadne/docs/capturing-a-state-fixture.md", "plugins/ariadne/docs/state-fixture.md")),
        ("capture-grounded-agent", "capture grounded agent", ("plugins/ariadne/docs/capturing-a-grounded-agent.md", "plugins/ariadne/docs/grounded-agent.md")),
        ("conformance", "conformance", ("plugins/ariadne/docs/conformance.md",)),
    ):
        add("ariadne", local_id, phase, documents)
    frontier("ariadne")
    for skill in ("berean", "brevitas", "homologia", "horos", "hypomnema", "janus", "sapheneia", "vulgate"):
        documents = python_pin if skill in {"berean", "brevitas"} else ()
        add(skill, "ordinary", "ordinary operation", documents)
        frontier(skill)

    hermes_runtime = (
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json",
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json",
        "plugins/hermes/skills/hermes/references/optimisation-catalogue.md",
    )
    add("hermes", "gas-operation", "gas analysis", python_pin + hermes_runtime)
    frontier("hermes")
    add("elenchus", "ordinary", "ordinary failure analysis")
    add("elenchus", "contract-fix", "contract failure", (ORACLE_SKILL_PATHS["fizz-sync"], promises))
    frontier("elenchus")
    add("ephoros", "ordinary", "telemetry operation", (ORACLE_SKILL_PATHS["phylax"],))
    frontier("ephoros")

    fizz_common = tuple(
        f"plugins/hexaemeron/skills/fizz/references/{name}.md"
        for name in ("template-map", "selection-policy", "setup-playbook", "handler-patterns")
    )
    fizz_report = ("plugins/hexaemeron/skills/fizz/agents/report-writer.md",)
    fizz_workers = (
        "plugins/hexaemeron/skills/fizz/agents/implementers/global-property-implementer.md",
        "plugins/hexaemeron/skills/fizz/agents/implementers/specific-property-implementer.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/adversarial-profit-maximizer.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/conservation-auditor.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/protocol-type-specialist.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/roundtrip-rounding-analyst.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/state-transition-mapper.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/synthesizer.md",
        "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md",
        fizz_report[0],
    )
    fizz_invariant = (
        "plugins/hexaemeron/skills/fizz/references/property-generation.md",
        *tuple(path for path in fizz_workers if path not in {fizz_report[0], "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md"}),
    )
    xray_full = (
        ORACLE_SKILL_PATHS["x-ray"],
        xray_version,
        promises,
        "plugins/hexaemeron/skills/x-ray/references/threats.md",
        "plugins/hexaemeron/skills/x-ray/references/templates.md",
    )
    for xray_state, invariant_state in itertools.product(("existing", "acquire", "fallback"), ("off", "on")):
        documents = fizz_common + fizz_report + (promises,)
        workers = fizz_report
        if xray_state in {"acquire", "fallback"}:
            documents += xray_full
        if xray_state == "fallback":
            analyzer = "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md"
            documents += (analyzer,)
            workers += (analyzer,)
        if invariant_state == "on":
            documents += fizz_invariant
            workers += tuple(path for path in fizz_invariant if "/agents/" in path)
        add("fizz", f"xray-{xray_state}__invariants-{invariant_state}", "fuzz-suite generation", documents, workers)
    add("fizz-convert", "convert", "property conversion", (promises,))
    add("fizz-sync", "sync", "harness reconciliation", (promises,))

    lexicons = (
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
    )
    add("imprimatur", "lint", "production lint", lexicons)
    frontier("imprimatur")
    add("metron", "ordinary", "measurement")
    add("metron", "budget-check", "budget check", ("plugins/hexaemeron/skills/metron/references/budget-check.md",))
    frontier("metron")
    add("phylax", "ordinary", "off-chain review")
    add("phylax", "model-proxy", "model proxy review", ("plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",))
    frontier("phylax")
    disciplines = tuple(ORACLE_SKILL_PATHS[name] for name in ("ephoros", "phylax", "metron", "elenchus", "hypomnema"))
    add("protasis", "runbook", "runbook validation")
    add("protasis", "study", "study validation", disciplines)
    frontier("protasis")

    sol_general = tuple(
        f"plugins/hexaemeron/skills/solidity-auditor/references/{name}.md"
        for name in ("report-formatting", "judging", "senior-auditor-sop")
    )
    sol_agents = tuple(
        path
        for path in oracle_tree_paths()
        if path.startswith(
            "plugins/hexaemeron/skills/solidity-auditor/"
            "references/hacking-agents/"
        )
        and path.endswith("-agent.md")
    )
    sol_shared = ("plugins/hexaemeron/skills/solidity-auditor/references/hacking-agents/shared-rules.md",)
    add("solidity-auditor", "audit", "Solidity audit", (sol_aud_version, promises) + sol_general + sol_shared + sol_agents, sol_agents)
    add("x-ray", "audit", "pre-audit analysis", xray_full[1:])

    add("lazarus", "ordinary", "capture/verify/replay")
    add("lazarus", "anchored-capture", "anchored capture", ("plugins/lazarus/docs/chain-anchors.md",))
    add("lazarus", "preservation-release", "preservation release", ("plugins/lazarus/docs/preservation-release.md",))
    add("lazarus", "maintenance", "maintenance", ("plugins/lazarus/docs/study.md", "plugins/lazarus/docs/runbook.md"))
    frontier("lazarus")
    add("lemma", "ordinary", "generate/verify", python_pin)
    add(
        "lemma",
        "changed-or-unexpected",
        "change/judge/unexpected-output",
        python_pin + ("plugins/lemma/INVARIANTS.md",),
    )
    frontier("lemma")
    add("pandects", "ordinary", "law operation")
    frontier("pandects")
    probitas = ("plugins/probitas/skills/probitas/references/gates.md", "plugins/probitas/skills/probitas/references/venues.md")
    add("probitas", "dossier", "dossier operation", probitas)
    add(
        "probitas",
        "add-venue",
        "add venue",
        python_pin + probitas + ("plugins/probitas/docs/adding-a-venue.md",),
    )
    frontier("probitas")
    rules = ("plugins/synkrisis/references/rules-v1.json",)
    add("synkrisis", "cohort-or-render", "cohort or render", python_pin)
    add("synkrisis", "diagnose", "diagnose", python_pin + rules)
    add("synkrisis", "verify", "verify", python_pin + rules)
    frontier("synkrisis")
    add("tabularium", "ordinary", "capture/verify")
    add("tabularium", "add-adapter", "add adapter", ("plugins/tabularium/docs/adding-an-adapter.md",))
    add("tabularium", "mapping-or-release", "correct mapping or release-policy", ("plugins/tabularium/docs/release-policy.md",))
    frontier("tabularium")

    full_ledgers = tuple(sorted(path for name, path in evolution.items() if name != "kronos"))
    kronos_currency = (
        "plugins/hexaemeron/skills/fiat/references/plugin-currency.md",
    )
    open_full = (
        "alexandria", "anamnesis", "berean", "brevitas", "hermes", "ephoros",
        "fiat", "hypomnema", "imprimatur", "metron", "vulgate", "homologia",
        "horos", "janus", "lazarus", "lemma", "pandects", "probitas",
        "sapheneia", "synkrisis", "tabularium",
    )
    phase_scope = ("protasis", "phylax", "ephoros", "metron", "elenchus", "hypomnema")

    def kronos(scope: str, targets: tuple[str, ...], ledgers: tuple[str, ...]) -> None:
        common = (evolution["kronos"],) + ledgers
        add("kronos", f"{scope}__rank-only", f"{scope} rank-only pass", common)
        for target in targets:
            add(
                "kronos",
                f"{scope}__dispatch-{target}",
                f"{scope} rank plus one target dispatch",
                common
                + kronos_currency
                + (ORACLE_SKILL_PATHS["fiat"], ORACLE_SKILL_PATHS[target]),
            )

    kronos("full", open_full, full_ledgers)
    kronos(
        "phase",
        ("ephoros", "metron", "hypomnema"),
        tuple(evolution[name] for name in phase_scope),
    )

    phylax_states = {
        "none": (),
        "phylax": (ORACLE_SKILL_PATHS["phylax"],),
        "phylax-proxy": (ORACLE_SKILL_PATHS["phylax"], "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md"),
        "ephoros-phylax": (ORACLE_SKILL_PATHS["ephoros"], ORACLE_SKILL_PATHS["phylax"]),
        "ephoros-phylax-proxy": (ORACLE_SKILL_PATHS["ephoros"], ORACLE_SKILL_PATHS["phylax"], "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md"),
    }
    metron_states = {
        "none": (),
        "metron": (ORACLE_SKILL_PATHS["metron"],),
        "metron-budget": (ORACLE_SKILL_PATHS["metron"], "plugins/hexaemeron/skills/metron/references/budget-check.md"),
    }
    elenchus_states = {
        "none": (),
        "elenchus": (ORACLE_SKILL_PATHS["elenchus"],),
        "elenchus-contract": (ORACLE_SKILL_PATHS["elenchus"], ORACLE_SKILL_PATHS["fizz-sync"], promises),
    }
    hypomnema_states = {"none": (), "hypomnema": (ORACLE_SKILL_PATHS["hypomnema"],)}
    hermes_states = {"none": (), "hermes": (ORACLE_SKILL_PATHS["hermes"],) + hermes_runtime}
    for worker, phylax, metron, elenchus, hypomnema, hermes in itertools.product(
        ("inline", "mason"), phylax_states, metron_states, elenchus_states, hypomnema_states, hermes_states
    ):
        documents = (
            (ORACLE_SKILL_PATHS["protasis"],)
            + phylax_states[phylax]
            + metron_states[metron]
            + elenchus_states[elenchus]
            + hypomnema_states[hypomnema]
            + hermes_states[hermes]
        )
        workers: tuple[str, ...] = ()
        if worker == "mason":
            workers = ("plugins/hexaemeron/agents/mason.md",)
            documents += workers
        add(
            "fiat",
            f"implement__{worker}__{phylax}__{metron}__{elenchus}__{hypomnema}__{hermes}",
            "implement directive",
            documents,
            workers,
        )

    audit_loop = "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
    sapheneia = ORACLE_SKILL_PATHS["sapheneia"]
    for worker, phylax, fix in itertools.product(
        ("inline", "warden"), ("phylax", "phylax-proxy"), ("none", "elenchus")
    ):
        documents = (
            audit_loop,
            sapheneia,
            ORACLE_SKILL_PATHS["phylax"],
            ORACLE_SKILL_PATHS["ephoros"],
            ORACLE_SKILL_PATHS["hypomnema"],
        )
        if phylax == "phylax-proxy":
            documents += ("plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",)
        if fix == "elenchus":
            documents += (ORACLE_SKILL_PATHS["elenchus"],)
        workers = ()
        if worker == "warden":
            workers = ("plugins/hexaemeron/agents/warden.md",)
            documents += workers
        add("fiat", f"audit-nonsol__{worker}__{phylax}__fix-{fix}", "non-Solidity audit round", documents, workers)

    sol_full = (ORACLE_SKILL_PATHS["solidity-auditor"], sol_aud_version, promises) + sol_general + sol_shared + sol_agents
    fizz_audit = {
        "absent": (),
        "later-campaign": (ORACLE_SKILL_PATHS["fizz"], promises),
        "full-generation": (ORACLE_SKILL_PATHS["fizz"], promises) + fizz_common + fizz_report + fizz_invariant,
    }
    for worker, fizz_state, fix in itertools.product(
        ("inline", "warden"), fizz_audit, ("none", "elenchus", "elenchus-contract")
    ):
        documents = (audit_loop, "plugins/hexaemeron/skills/fiat/references/xray-reuse.md", sapheneia) + xray_full + sol_full + fizz_audit[fizz_state]
        if fix == "elenchus":
            documents += (ORACLE_SKILL_PATHS["elenchus"],)
        elif fix == "elenchus-contract":
            documents += (ORACLE_SKILL_PATHS["elenchus"], ORACLE_SKILL_PATHS["fizz-sync"], promises)
        workers = sol_agents
        if fizz_state == "full-generation":
            workers += fizz_report + tuple(path for path in fizz_invariant if "/agents/" in path)
        if worker == "warden":
            workers += ("plugins/hexaemeron/agents/warden.md",)
            documents += ("plugins/hexaemeron/agents/warden.md",)
        add("fiat", f"audit-solidity__{worker}__fizz-{fizz_state}__fix-{fix}", "Solidity audit round", documents, workers)

    prose_base = (
        "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
        ORACLE_SKILL_PATHS["hypomnema"],
        ORACLE_SKILL_PATHS["imprimatur"],
        *lexicons,
        ORACLE_SKILL_PATHS["vulgate"],
    )
    for worker, brevitas, task_issue, last_step in itertools.product(
        ("inline", "scribe"), (False, True), (False, True), (False, True)
    ):
        documents = prose_base
        workers = ()
        if worker == "scribe":
            workers = ("plugins/hexaemeron/agents/scribe.md",)
            documents += workers
        if brevitas:
            documents += (ORACLE_SKILL_PATHS["brevitas"],)
        if task_issue:
            documents += (sapheneia,)
        if last_step:
            documents += ("plugins/hexaemeron/skills/fiat/references/push-discipline.md",)
        add("fiat", f"prose__{worker}__brevitas-{int(brevitas)}__issue-{int(task_issue)}__last-{int(last_step)}", "prose directive", documents, workers)

    for worker in ("inline", "surveyor"):
        documents = (ORACLE_SKILL_PATHS["protasis"],) + disciplines + (ORACLE_SKILL_PATHS["imprimatur"],) + lexicons
        workers = ()
        if worker == "surveyor":
            workers = ("plugins/hexaemeron/agents/surveyor.md",)
            documents += workers
        add("fiat", f"study__{worker}", "study directive", documents, workers)

    fiat_other = {
        "controller-basic": (),
        "frontier-gate": (evolution["fiat"], versioning),
        "marketplace-day1": ("plugins/hexaemeron/skills/fiat/references/wildcat-marketplace.md",),
        "marketplace-post-spec": ("plugins/hexaemeron/skills/fiat/references/wildcat-marketplace.md", "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"),
        "currency-remediation": ("plugins/hexaemeron/skills/fiat/references/plugin-currency.md",),
        "checkpoint-transfer": ("plugins/hexaemeron/skills/fiat/references/push-discipline.md", "plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md"),
        "observation-receipt": ("docs/fiat-run-observation-binding-v1.md",),
        "runbook": (ORACLE_SKILL_PATHS["protasis"], ORACLE_SKILL_PATHS["imprimatur"], *lexicons),
        "close-audit": (audit_loop,),
        "delivery": ("plugins/hexaemeron/skills/fiat/references/push-discipline.md",),
        "integrate-task-issue": ("plugins/hexaemeron/skills/fiat/references/push-discipline.md", sapheneia, ORACLE_SKILL_PATHS["imprimatur"], *lexicons, ORACLE_SKILL_PATHS["vulgate"]),
    }
    for local_id, documents in fiat_other.items():
        add("fiat", local_id, "bounded controller operation", documents)

    return sorted(rows, key=lambda row: row["id"])


def oracle_validate_profiles_and_routes(record: dict, graph: dict) -> None:
    """Check profiles, frozen spans, and 5N reachability without production helpers."""
    expected = oracle_profiles()
    observed = record.get("profiles")
    if not isinstance(observed, list):
        raise TypeError("oracle profile ledger is not an array")
    stripped = [
        {key: value for key, value in row.items() if key != "source_evidence"}
        for row in observed
    ]
    if stripped != expected:
        raise AssertionError("independent profile grammar mismatch")

    expected_counts = {
        skill: sum(row["selected_skill"] == skill for row in expected)
        for skill in sorted(ORACLE_SKILL_PATHS)
    }
    count = len(expected)
    expected_totals = {
        "normalized_profiles": count,
        "repository_roots": count * 2,
        "agent_skills_roots": count * 2,
        "standalone_roots": count,
        "scenario_roots": count * 5,
    }
    if record.get("counts") != expected_counts or record.get("totals") != expected_totals:
        raise AssertionError("independent profile denominator mismatch")

    semantic_counts = {name: 0 for name in ORACLE_PROFILE_EVIDENCE_COUNTS}
    for row in observed:
        row_counts = oracle_validate_semantic_anchors(row)
        for name, count_for_row in row_counts.items():
            semantic_counts[name] += count_for_row
    if semantic_counts != ORACLE_PROFILE_EVIDENCE_COUNTS or sum(
        semantic_counts.values()
    ) != sum(len(row["required_documents"]) for row in observed):
        raise AssertionError("independent semantic evidence denominator mismatch")

    evidence_projection = [
        {"id": row["id"], "source_evidence": row["source_evidence"]}
        for row in observed
    ]
    if hashlib.sha256(canonical(evidence_projection)).hexdigest() != ORACLE_EVIDENCE_PROJECTION_SHA256:
        raise AssertionError("independent obligation evidence projection mismatch")
    for row in observed:
        evidence_rows = row["source_evidence"]
        if [item.get("obligation") for item in evidence_rows] != row["required_documents"]:
            raise AssertionError(f"independent obligation coverage mismatch: {row['id']}")
        for evidence in evidence_rows:
            if set(evidence) != {
                "obligation", "path", "start", "end", "source_sha256", "span_sha256"
            }:
                raise AssertionError("independent evidence field mismatch")
            data = oracle_source(evidence["path"])
            start = evidence["start"]
            end = evidence["end"]
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start < 0
                or end <= start
                or end > len(data)
                or hashlib.sha256(data).hexdigest() != evidence["source_sha256"]
                or hashlib.sha256(data[start:end]).hexdigest() != evidence["span_sha256"]
            ):
                raise AssertionError(f"independent frozen span mismatch: {row['id']}")

    expected_roots: dict[str, dict] = {}
    profiles = {row["id"]: row for row in observed}
    for row in observed:
        skill = row["selected_skill"]
        plugin = ORACLE_SKILL_PATHS[skill].split("/")[1]
        for route, credentials in (
            ("repository", ("absent", "github-contributor")),
            ("agent-skills", ("absent", "github-contributor")),
            ("standalone", ("absent",)),
        ):
            base = (
                f"standalone:{plugin}:skill:{skill}"
                if route == "standalone"
                else f"{route}:skill:{skill}"
            )
            node = {
                "repository": "AGENTS.md",
                "agent-skills": ".agents/skills/promise-machine/SKILL.md",
                "standalone": f"plugins/{plugin}/AGENTS.md",
            }[route]
            for credential in credentials:
                identifier = f"{base}:profile:{row['id']}:credential:{credential}"
                conditions = [f"profile:{row['id']}"]
                if credential == "github-contributor":
                    conditions.append("credential:github-contributor")
                expected_roots[identifier] = {
                    "node": node,
                    "base_scenario": base,
                    "route": route,
                    "selected_skill": skill,
                    "profile_id": row["id"],
                    "credential": credential,
                    "conditions": sorted(conditions),
                }
    roots = {row["id"]: row for row in graph.get("scenario_roots", [])}
    if set(roots) != set(expected_roots):
        raise AssertionError("independent 5N route identity mismatch")
    for identifier, expected_root in expected_roots.items():
        root = roots[identifier]
        for field, value in expected_root.items():
            if root.get(field) != value:
                raise AssertionError(f"independent route binding mismatch: {identifier}")

    adjacency: dict[str, dict[str, set[str]]] = {
        identifier: {} for identifier in roots
    }
    for edge in graph.get("scenario_edges", []):
        for identifier in edge.get("active_scenarios", []):
            if identifier not in adjacency:
                raise AssertionError("independent edge scope escapes 5N roots")
            adjacency[identifier].setdefault(edge["source"], set()).add(edge["target"])
    for identifier, root in roots.items():
        profile = profiles[root["profile_id"]]
        skill = profile["selected_skill"]
        plugin = ORACLE_SKILL_PATHS[skill].split("/")[1]
        selected = ORACLE_SKILL_PATHS[skill]
        expected_documents = set(profile["required_documents"])
        expected_documents.update(
            {f"plugins/{plugin}/AGENTS.md", f"plugins/{plugin}/PROMISE_MACHINE.md", selected}
        )
        if root["route"] == "repository":
            expected_documents.update(
                {"AGENTS.md", "SHOGGOTH.md", "PROMISE_MACHINE.md", ".agents/skills/promise-machine/SKILL.md"}
            )
        elif root["route"] == "agent-skills":
            expected_documents.update(
                {
                    "AGENTS.md", "SHOGGOTH.md", "PROMISE_MACHINE.md",
                    ".agents/skills/promise-machine/SKILL.md",
                    ".agents/skills/promise-machine/PORTABLE.md",
                }
            )
        if root["credential"] == "github-contributor":
            expected_documents.add("CONTRIBUTORS.md")
        pending = [root["node"]]
        reached: set[str] = set()
        while pending:
            node = pending.pop()
            if node in reached:
                continue
            reached.add(node)
            pending.extend(adjacency[identifier].get(node, ()))
        if reached != expected_documents:
            raise AssertionError(f"independent route union mismatch: {identifier}")
    oracle_validate_runtime_edges(record, graph)


def command(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        check=False,
        timeout=90,
    )


class CorpusManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)

    def test_exact_inventory_and_denominators(self):
        self.assertEqual(self.manifest["counts"], AI.EXPECTED_COUNTS)
        self.assertEqual(self.manifest["totals"], AI.EXPECTED_TOTALS)
        paths = [item["path"] for item in self.manifest["documents"]]
        self.assertEqual(paths, sorted(paths))
        self.assertEqual(len(paths), len(set(paths)))

    def test_shallow_checkout_rebuilds_from_inventory_bound_sources(self):
        if not hasattr(AI, "_source_mode"):
            self.skipTest("the parent has no inventory-bound source mode")
        clear_source_cache()
        try:
            with mock.patch.object(AI, "_source_mode", return_value="inventory"):
                rebuilt = AI.build_manifest(AI.build_invocation_profiles())
            self.assertEqual(rebuilt, self.manifest)
        finally:
            clear_source_cache()

    def test_shallow_checkout_refuses_source_drift(self):
        if not hasattr(AI, "_inventory_source_snapshot"):
            self.skipTest("the parent has no inventory-bound source snapshot")
        clear_source_cache()
        original_read = AI._read_regular

        def changed_source(path: Path, limit: int) -> bytes:
            data = original_read(path, limit)
            if path == ROOT / "AGENTS.md":
                return data + b"\n"
            return data

        try:
            with (
                mock.patch.object(AI, "_source_mode", return_value="inventory"),
                mock.patch.object(AI, "_read_regular", side_effect=changed_source),
                self.assertRaisesRegex(AI.Refusal, "inventory snapshot source drift"),
            ):
                AI._source_blob("AGENTS.md")
        finally:
            clear_source_cache()

    def test_shallow_checkout_does_not_hide_source_probe_failure(self):
        if not hasattr(AI, "_source_mode"):
            self.skipTest("the parent has no inventory-bound source mode")

        def failed_probe(arguments, limit=AI.MAX_GIT_OUTPUT, **kwargs):
            if arguments[0] == "cat-file":
                raise AI.Refusal("bounded Git read timed out")
            if arguments == ["rev-parse", "--is-shallow-repository"]:
                return b"true\n"
            raise AssertionError(f"unexpected Git probe: {arguments}")

        clear_source_cache()
        try:
            with (
                mock.patch.object(AI, "_git", side_effect=failed_probe),
                self.assertRaisesRegex(AI.Refusal, "bounded Git read timed out"),
            ):
                AI._source_mode()
        finally:
            clear_source_cache()

    def test_independent_shallow_oracle_does_not_hide_source_probe_failure(self):
        def failed_probe(*arguments, **kwargs):
            if arguments[0] == "cat-file":
                return subprocess.CompletedProcess(arguments, 128, b"", b"failed")
            if arguments == ("rev-parse", "--is-shallow-repository"):
                return subprocess.CompletedProcess(arguments, 0, b"true\n", b"")
            raise AssertionError(f"unexpected Git probe: {arguments}")

        clear_source_cache()
        try:
            with (
                mock.patch.object(
                    sys.modules[__name__], "oracle_git", side_effect=failed_probe
                ),
                self.assertRaisesRegex(
                    AssertionError, "independent oracle source probe failed"
                ),
            ):
                oracle_source_mode()
        finally:
            clear_source_cache()

    def test_manifest_source_topology_runtime_contract_is_closed(self):
        mutations = {
            "missing": lambda source: source.pop("repository_paths"),
            "extra": lambda source: source.__setitem__("extra", True),
            "duplicate": lambda source: source["repository_paths"].append(
                source["repository_paths"][0]
            ),
            "over-cap": lambda source: source.__setitem__(
                "repository_paths",
                [f"synthetic/{index:05d}" for index in range(10_001)],
            ),
        }
        for label, mutate in mutations.items():
            changed = copy.deepcopy(self.manifest)
            mutate(changed["source"])
            with self.subTest(label=label):
                with self.assertRaisesRegex(
                    AI.Refusal, "manifest source.*(field set|malformed)"
                ):
                    AI._validate_manifest_shape(changed)

        changed = copy.deepcopy(self.manifest)
        changed["source"]["repository_paths"] = changed["source"][
            "repository_paths"
        ][:-1]
        with self.assertRaisesRegex(AI.Refusal, "manifest source topology drift"):
            AI._validate_manifest_shape(changed)

    def test_manifest_validator_refuses_derivation_drift_without_command_rebuild(self):
        mutations = {
            "document-bytes": lambda value: value["documents"][0].__setitem__(
                "bytes", 1
            ),
            "document-sha256": lambda value: value["documents"][0].__setitem__(
                "sha256", "0" * 64
            ),
            "class-count": lambda value: value["counts"].__setitem__(
                "skill_contract", 0
            ),
            "physical-total": lambda value: value["totals"].__setitem__(
                "physical_bytes", 1
            ),
            "missing-ordinary-document": lambda value: value["documents"].pop(
                next(
                    index
                    for index, item in enumerate(value["documents"])
                    if item["source_evidence"] is None
                    and item["runtime_evidence"] is None
                )
            ),
            "host-reachability": lambda value: value["documents"][0].__setitem__(
                "loader_roots", ["repository"]
            ),
            "scenario-reachability": lambda value: value["documents"][0].__setitem__(
                "scenario_reachability",
                [
                    value["documents"][0]["scenario_reachability"][0].replace(
                        "agent-skills:", "repository:", 1
                    )
                ],
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.manifest)
                mutate(changed)
                with self.assertRaisesRegex(
                    AI.Refusal, "manifest differs from its source-bound derivation"
                ):
                    AI._validate_manifest_shape(changed)

    def test_independent_oracle_tree_paths_share_the_anchored_snapshot(self):
        clear_source_cache()
        changed = copy.deepcopy(self.manifest)
        unbound = "zz-unbound-topology.md"
        changed["source"]["repository_paths"] = sorted(
            [*changed["source"]["repository_paths"], unbound]
        )
        try:
            with mock.patch.object(
                sys.modules[__name__], "oracle_source_mode", return_value="inventory"
            ):
                oracle_inventory_snapshot()
                with mock.patch.object(
                    sys.modules[__name__], "load", return_value=changed
                ):
                    paths = oracle_tree_paths()
            self.assertNotIn(unbound, paths)
        finally:
            clear_source_cache()

    def test_independent_inventory_refuses_oversized_input_before_digest(self):
        with scratch_directory("oversized-oracle-inventory-") as temporary:
            oversized = Path(temporary) / "artifact-inventory.json"
            oversized.write_bytes(b" " * (8 * 1024 * 1024 + 1))
            clear_source_cache()
            try:
                with (
                    mock.patch.object(
                        sys.modules[__name__], "INVENTORY", oversized
                    ),
                    self.assertRaisesRegex(
                        AssertionError, "independent input exceeds byte limit"
                    ),
                ):
                    oracle_inventory_snapshot()
            finally:
                clear_source_cache()

    def test_independent_inventory_refuses_symlink_substitution(self):
        with scratch_directory("symlinked-oracle-inventory-") as temporary:
            symlink = Path(temporary) / "artifact-inventory.json"
            symlink.symlink_to(INVENTORY)
            clear_source_cache()
            try:
                with (
                    mock.patch.object(sys.modules[__name__], "INVENTORY", symlink),
                    self.assertRaisesRegex(
                        AssertionError, "independent input is unavailable or unsafe"
                    ),
                ):
                    oracle_inventory_snapshot()
            finally:
                clear_source_cache()

    def test_depth_one_checkout_replays_the_frozen_source(self):
        with scratch_directory("depth-one-checkout-") as temporary:
            checkout = Path(temporary) / "checkout"
            head = subprocess.run(
                ["/usr/bin/git", "-C", str(ROOT), "rev-parse", "HEAD"],
                capture_output=True,
                check=True,
                text=True,
                timeout=20,
            ).stdout.strip()
            subprocess.run(
                ["/usr/bin/git", "init", "--quiet", str(checkout)],
                capture_output=True,
                check=True,
                timeout=20,
            )
            subprocess.run(
                [
                    "/usr/bin/git",
                    "-C",
                    str(checkout),
                    "fetch",
                    "--quiet",
                    "--depth",
                    "1",
                    "--no-tags",
                    ROOT.as_uri(),
                    head,
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            subprocess.run(
                [
                    "/usr/bin/git",
                    "-C",
                    str(checkout),
                    "checkout",
                    "--quiet",
                    "--detach",
                    "FETCH_HEAD",
                ],
                capture_output=True,
                check=True,
                timeout=30,
            )
            self.assertEqual(
                subprocess.run(
                    [
                        "/usr/bin/git",
                        "-C",
                        str(checkout),
                        "rev-parse",
                        "--is-shallow-repository",
                    ],
                    capture_output=True,
                    check=True,
                    timeout=20,
                ).stdout,
                b"true\n",
            )
            verify = subprocess.run(
                [
                    sys.executable,
                    str(checkout / "research/instruction-architecture/benchmark.py"),
                    "verify-loader",
                    "--profiles",
                    str(checkout / "tests/fixtures/instruction-architecture/invocation-profiles.json"),
                    "--manifest",
                    str(checkout / "tests/fixtures/instruction-architecture/corpus-manifest.json"),
                    "--graph",
                    str(checkout / "tests/fixtures/instruction-architecture/loader-graph.json"),
                ],
                cwd=checkout,
                capture_output=True,
                text=True,
                check=False,
                timeout=90,
            )
            shallow_suite = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "tests.test_instruction_architecture.CorpusManifestTests.test_build_baseline_reproduces_all_committed_outputs",
                    "tests.test_instruction_architecture.CorpusManifestTests.test_independent_markdown_fixed_point_detects_an_unclassified_directive",
                    "tests.test_instruction_architecture.InvocationProfileTests.test_independent_source_owned_profile_and_route_oracle",
                    "tests.test_instruction_architecture.LoaderGraphTests.test_independent_runtime_semantic_evidence_coverage_is_closed",
                    "tests.test_instruction_architecture.ControlSnapshotTests.test_snapshot_generation_refuses_unowned_entries_before_writing",
                    "tests.test_instruction_architecture.ControlSnapshotTests.test_snapshot_generation_completes_owned_partial_and_clean_refresh",
                    "-v",
                ],
                cwd=checkout,
                capture_output=True,
                text=True,
                check=False,
                timeout=180,
            )
            self.assertEqual(
                (verify.returncode, shallow_suite.returncode),
                (0, 0),
                f"verify-loader:\n{verify.stderr}\nshallow suite:\n{shallow_suite.stderr}",
            )

    def test_source_directed_admission_is_exact_and_anchored(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        admissions = AI._additional_metadata()
        self.assertEqual(len(admissions), 70)
        self.assertEqual(
            {
                item["path"]
                for item in self.manifest["documents"]
                if item["admission_kind"] != "issue-census"
            },
            set(admissions)
            | set(AI._structured_metadata())
            | set(AI._fixed_agent_metadata()),
        )
        self.assertEqual(sum(documents[path]["bytes"] for path in admissions), 526_326)
        self.assertEqual(
            {
                class_name: sum(
                    1
                    for metadata in admissions.values()
                    if metadata["document_class"] == class_name
                )
                for class_name in sorted(
                    {metadata["document_class"] for metadata in admissions.values()}
                )
            },
            {
                "frontier_ledger": 26,
                "frontier_policy": 1,
                "identity_contract": 1,
                "identity_roster": 1,
                "operation_reference": 25,
                "overlay_contract": 1,
                "router_install_contract": 1,
                "worker_prompt": 14,
            },
        )
        for path, metadata in admissions.items():
            with self.subTest(path=path):
                self.assertEqual(
                    documents[path]["document_class"], metadata["document_class"]
                )
                evidence = AI._evidence(
                    metadata["source_path"], metadata["source_needle"]
                )
                self.assertGreater(evidence["end"], evidence["start"])

    def test_structured_reference_inventory_and_evidence_are_exact(self):
        documents = {
            item["path"]: item
            for item in self.manifest["documents"]
            if item["document_class"] == "structured_reference"
        }
        self.assertEqual(
            {
                path: (item["bytes"], item["sha256"])
                for path, item in documents.items()
            },
            EXPECTED_STRUCTURED_REFERENCES,
        )
        metadata = AI._structured_metadata()
        self.assertEqual(set(documents), set(metadata))
        self.assertEqual(sum(item["bytes"] for item in documents.values()), 218_576)
        for path, item in documents.items():
            with self.subTest(path=path):
                row = metadata[path]
                self.assertEqual(item["canonical_owner"], row["canonical_owner"])
                self.assertEqual(item["load_semantics"], row["load_semantics"])
                self.assertEqual(
                    item["source_evidence"],
                    AI._evidence(row["source_path"], row["source_needle"]),
                )
                if row["runtime_path"] is None:
                    self.assertIsNone(item["runtime_evidence"])
                    self.assertEqual(item["loader_roots"], [])
                    self.assertEqual(item["scenario_reachability"], [])
                else:
                    self.assertEqual(
                        item["runtime_evidence"],
                        AI._evidence(row["runtime_path"], row["runtime_needle"]),
                    )
                    self.assertTrue(item["loader_roots"])
                    self.assertTrue(item["scenario_reachability"])

    def manifest_source_rebinding_specimens(self):
        rows = [
            (index, item)
            for index, item in enumerate(self.manifest["documents"])
            if item["source_evidence"] is not None
        ]
        specimens = {}
        for index, item in rows:
            evidence_class = item["document_class"]
            if evidence_class in specimens:
                continue
            for _, donor in rows:
                if (
                    donor["document_class"] != evidence_class
                    and donor["path"] != item["path"]
                    and donor["source_evidence"]["path"]
                    != item["source_evidence"]["path"]
                    and donor["source_evidence"] != item["source_evidence"]
                ):
                    specimens[evidence_class] = (
                        index,
                        donor["path"],
                        copy.deepcopy(donor["source_evidence"]),
                    )
                    break
        self.assertEqual(
            set(specimens), set(ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS)
        )
        return specimens

    def test_independent_manifest_semantic_evidence_coverage_is_closed(self):
        oracle_validate_manifest_semantic_anchors(self.manifest)
        self.assertEqual(
            sum(
                item["source_evidence"] is not None
                for item in self.manifest["documents"]
            ),
            sum(ORACLE_MANIFEST_SOURCE_EVIDENCE_COUNTS.values()),
        )
        self.assertEqual(
            sum(
                item["runtime_evidence"] is not None
                for item in self.manifest["documents"]
            ),
            sum(ORACLE_MANIFEST_RUNTIME_EVIDENCE_COUNTS.values()),
        )

    def test_manifest_validator_does_not_trust_structured_source_metadata(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["source_path"] = metadata[donor]["source_path"]
        metadata[target]["source_needle"] = metadata[donor]["source_needle"]
        changed = copy.deepcopy(self.manifest)
        by_path = {item["path"]: item for item in changed["documents"]}
        by_path[target]["source_evidence"] = copy.deepcopy(
            by_path[donor]["source_evidence"]
        )
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "manifest semantic source anchor drift"
            ):
                AI._validate_manifest_shape(changed)

    def test_manifest_validator_refuses_all_synchronised_runtime_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.manifest["documents"], "path"
        )
        original_metadata = AI._structured_metadata()
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                metadata = copy.deepcopy(original_metadata)
                metadata[target]["runtime_path"] = original_metadata[donor_target][
                    "runtime_path"
                ]
                metadata[target]["runtime_needle"] = original_metadata[donor_target][
                    "runtime_needle"
                ]
                changed = copy.deepcopy(self.manifest)
                changed["documents"][index]["runtime_evidence"] = donor_runtime
                with mock.patch.object(
                    AI, "_structured_metadata", return_value=metadata
                ):
                    with self.assertRaisesRegex(
                        AI.Refusal, "manifest semantic runtime anchor drift"
                    ):
                        AI._validate_manifest_shape(changed)

    def test_independent_manifest_oracle_refuses_cross_class_source_rebindings(self):
        for evidence_class, (index, donor_path, donor_evidence) in (
            self.manifest_source_rebinding_specimens().items()
        ):
            with self.subTest(evidence_class=evidence_class, donor=donor_path):
                changed = copy.deepcopy(self.manifest)
                changed["documents"][index]["source_evidence"] = donor_evidence
                with self.assertRaisesRegex(
                    AssertionError, "independent manifest source anchor mismatch"
                ):
                    oracle_validate_manifest_semantic_anchors(changed)

    def test_independent_manifest_oracle_refuses_all_runtime_target_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.manifest["documents"], "path"
        )
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.manifest)
                changed["documents"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AssertionError, "independent manifest runtime anchor mismatch"
                ):
                    oracle_validate_manifest_semantic_anchors(changed)

    def test_fixed_agent_inputs_are_exact_and_never_executable(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            ".python-version": (
                7,
                "3a55324cbeddc91df012407d051dad08c88624c95a82fbdb856728729fbd14ab",
            ),
            "plugins/hexaemeron/skills/x-ray/VERSION": (
                2,
                "53c234e5e8472b6ac51c1ae1cab3fe06fad053beb8ebfd8977b010655bfdd3c3",
            ),
            "plugins/hexaemeron/skills/solidity-auditor/VERSION": (
                2,
                "1121cfccd5913f0a63fec40a6ffd44ea64f9dc135c66634ba001d10bcf4302a2",
            ),
        }
        self.assertEqual(set(AI._fixed_agent_metadata()), set(expected))
        for path, (size, digest) in expected.items():
            with self.subTest(path=path):
                item = documents[path]
                metadata = AI._fixed_agent_metadata()[path]
                self.assertEqual((item["bytes"], item["sha256"]), (size, digest))
                self.assertEqual(item["document_class"], "fixed_input")
                self.assertEqual(item["load_semantics"], "agent-or-prompt")
                self.assertIsNone(item["runtime_evidence"])
                self.assertEqual(
                    item["source_evidence"],
                    AI._evidence(metadata["source_path"], metadata["source_needle"]),
                )
                self.assertTrue(item["loader_roots"])
                self.assertTrue(item["scenario_reachability"])

    def test_operation_reference_closure_and_anamnesis_anchor_are_independent(self):
        operations = {
            item["path"]
            for item in self.manifest["documents"]
            if item["document_class"] == "operation_reference"
        }
        self.assertEqual(operations, EXPECTED_OPERATION_REFERENCES)
        demo = next(
            item
            for item in self.manifest["documents"]
            if item["path"] == "plugins/anamnesis/docs/demo.md"
        )
        self.assertEqual(demo["bytes"], 2_605)
        self.assertEqual(
            demo["sha256"],
            "b523e14fc000502dfc4aafc8732a77091803ab25b7e9ab990ff234f9702673cb",
        )
        self.assertEqual(
            demo["canonical_owner"],
            "plugins/anamnesis/skills/anamnesis/SKILL.md",
        )
        evidence = AI._evidence(
            "plugins/anamnesis/skills/anamnesis/SKILL.md", "../../docs/demo.md"
        )
        self.assertEqual((evidence["start"], evidence["end"]), (7_636, 7_654))
        self.assertEqual(
            evidence["span_sha256"],
            "9dfc4f04bae4c35cad57e454454283642f1676e2bb1e75178e1d83da81b793bc",
        )

    def test_independent_markdown_fixed_point_detects_an_unclassified_directive(self):
        derived = AI._derive_operative_markdown_targets(self.manifest["documents"])
        manifest_paths = {item["path"] for item in self.manifest["documents"]}
        self.assertEqual(derived["occurrences"], 298)
        self.assertEqual(len(derived["targets"]), 112)
        self.assertEqual(len(derived["excluded"]), 127)
        self.assertIn("plugins/anamnesis/docs/demo.md", derived["targets"])
        self.assertFalse(set(derived["targets"]) - manifest_paths)

        without_demo = [
            item
            for item in self.manifest["documents"]
            if item["path"] != "plugins/anamnesis/docs/demo.md"
        ]
        second_pass = AI._derive_operative_markdown_targets(without_demo)
        self.assertIn(
            "plugins/anamnesis/docs/demo.md",
            set(second_pass["targets"]) - {item["path"] for item in without_demo},
        )

        source = "plugins/anamnesis/skills/anamnesis/SKILL.md"
        synthetic = {
            "plugins/anamnesis/docs/new-operation.md",
            "plugins/anamnesis/docs/new-runbook.md",
        }
        repurposed = "plugins/pandects/docs/catalogue.md"
        changed_source = AI._source_blob(source) + (
            b"\nRead [the new operation](../../docs/new-operation.md) before acting.\n"
            b"Read [the new runbook](../../docs/new-runbook.md) before acting.\n"
            b"Read [the catalogue](../../../pandects/docs/catalogue.md) before acting.\n"
        )
        changed = AI._derive_operative_markdown_targets(
            self.manifest["documents"],
            source_overrides={source: changed_source},
            tree_paths={*AI._frozen_tree_paths(), *synthetic},
        )
        self.assertLessEqual(
            synthetic | {repurposed}, set(changed["targets"]) - manifest_paths
        )
        self.assertFalse(
            any(
                item["target"] in synthetic | {repurposed}
                for item in changed["excluded"]
            )
        )

    def test_independent_fixed_point_deriver_is_required(self):
        self.assertTrue(
            callable(getattr(AI, "_derive_operative_markdown_targets", None))
        )

    def test_markdown_link_scan_caps_candidate_restarts_before_regex(self):
        document = [{"path": "bounded.md", "document_class": "skill_contract"}]

        def derive(data):
            return AI._derive_operative_markdown_targets(
                document,
                source_overrides={"bounded.md": data},
                tree_paths={"bounded.md"},
            )

        for label, source in {
            "opener-at-limit": b"[" * 4_096,
            "line-at-limit": b"x" * 16_384,
        }.items():
            with self.subTest(label=label):
                self.assertEqual(derive(source)["targets"], [])

        for label, (source, message) in {
            "opener-over-limit": (
                b"[" * 4_097,
                "Markdown link opener count exceeds limit",
            ),
            "line-over-limit": (
                b"x" * 16_385,
                "Markdown line exceeds character limit",
            ),
        }.items():
            with self.subTest(label=label), mock.patch.object(
                AI, "INLINE_MARKDOWN_LINK"
            ) as matcher, self.assertRaisesRegex(AI.Refusal, message):
                derive(source)
            matcher.finditer.assert_not_called()

    def test_markdown_link_scan_refuses_cross_line_suffixes_before_regex(self):
        document = [{"path": "bounded.md", "document_class": "skill_contract"}]

        def derive(data):
            return AI._derive_operative_markdown_targets(
                document,
                source_overrides={"bounded.md": data},
                tree_paths={"bounded.md"},
            )

        for label, source in {
            "multiline-title": b"[label](target title\ncontinues)\n",
            "unmatched-title": b"[label](target title\ncontinues\n",
        }.items():
            with self.subTest(label=label), mock.patch.object(
                AI, "INLINE_MARKDOWN_LINK"
            ) as matcher, self.assertRaisesRegex(
                AI.Refusal, "Markdown link suffix crosses line boundary"
            ):
                derive(source)
            matcher.finditer.assert_not_called()

        for source in (
            b"[first](target title [second](target title)\n",
            b"[first](target title [second](target title))\n",
        ):
            with self.subTest(label="multiple-candidates-one-later-close"):
                self.assertEqual(derive(source)["targets"], [])

    def test_extension_agnostic_fixed_point_and_runtime_anchor_mutations(self):
        derived = AI._derive_corpus_fixed_point(self.manifest["documents"])
        self.assertEqual(
            set(derived["structured_targets"]), set(EXPECTED_STRUCTURED_REFERENCES)
        )
        mandatory = {
            path
            for path, row in AI._structured_metadata().items()
            if row["load_semantics"] == "mandatory-executable"
        }
        self.assertEqual(set(derived["mandatory_executable_targets"]), mandatory)

        synthetic = "plugins/hermes/skills/hermes/references/new-rules.data"
        decoys = {
            "plugins/hermes/skills/hermes/scripts/generated-rules.json",
            "plugins/hexaemeron/skills/fizz/templates/output.json",
            "plugins/hermes/tests/fixtures/rules.json",
            "plugins/synkrisis/examples/specimens/rules.json",
            "project-inputs/rules.json",
        }
        with_synthetic = AI._derive_corpus_fixed_point(
            self.manifest["documents"],
            tree_paths={*AI._frozen_tree_paths(), synthetic, *decoys},
        )
        self.assertIn(synthetic, with_synthetic["structured_targets"])
        self.assertFalse(decoys & set(with_synthetic["structured_targets"]))

        for path in sorted(mandatory):
            row = AI._structured_metadata()[path]
            runtime_path = row["runtime_path"]
            self.assertIsNotNone(runtime_path)
            runtime = AI._source_blob(runtime_path)
            needle = row["runtime_needle"].encode()
            self.assertIn(needle, runtime)
            changed = AI._derive_corpus_fixed_point(
                self.manifest["documents"],
                source_overrides={runtime_path: runtime.replace(needle, b"", 1)},
            )
            self.assertNotIn(path, changed["mandatory_executable_targets"])
            source_path = row["source_path"]
            source = AI._source_blob(source_path)
            source_needle = row["source_needle"].encode()
            self.assertIn(source_needle, source)
            changed = AI._derive_corpus_fixed_point(
                self.manifest["documents"],
                source_overrides={
                    source_path: source.replace(source_needle, b"", 1)
                },
            )
            self.assertNotIn(path, changed["mandatory_executable_targets"])

    def test_every_structured_input_omission_and_move_refuses(self):
        tree = set(AI._frozen_tree_paths())
        for path in sorted(EXPECTED_STRUCTURED_REFERENCES):
            changed = tuple(sorted(tree - {path}))
            with self.subTest(path=path):
                with mock.patch.object(AI, "_frozen_tree_paths", return_value=changed):
                    with self.assertRaisesRegex(
                        AI.Refusal, "structured reference missing|topology drift"
                    ):
                        AI._corpus_paths()
        lexicon = "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json"
        moved = "plugins/hexaemeron/skills/imprimatur/templates/hard.json"
        with mock.patch.object(
            AI,
            "_frozen_tree_paths",
            return_value=tuple(sorted((tree - {lexicon}) | {moved})),
        ):
            with self.assertRaisesRegex(AI.Refusal, "structured reference missing"):
                AI._corpus_paths()

    def test_reference_suffix_does_not_control_non_markdown_admission(self):
        original = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        renamed = original.removesuffix(".json") + ".bin"
        tree = (set(AI._frozen_tree_paths()) - {original}) | {renamed}
        changed = AI._derive_corpus_fixed_point(
            self.manifest["documents"], tree_paths=tree
        )
        self.assertNotIn(original, changed["structured_targets"])
        self.assertIn(renamed, changed["structured_targets"])

    def test_same_repository_url_requires_exact_repository_ref_and_path(self):
        self.assertEqual(
            AI._same_repository_markdown_url(AI.CONTRIBUTORS_CANONICAL_URL),
            "CONTRIBUTORS.md",
        )
        for changed in (
            AI.CONTRIBUTORS_CANONICAL_URL.replace("wildcat-finance", "attacker"),
            AI.CONTRIBUTORS_CANONICAL_URL.replace("/main/", "/other/"),
            AI.CONTRIBUTORS_CANONICAL_URL.replace(
                "CONTRIBUTORS.md", "contributors.md"
            ),
            f"{AI.CONTRIBUTORS_CANONICAL_URL}?raw=1",
        ):
            with self.subTest(changed=changed):
                self.assertIsNone(AI._same_repository_markdown_url(changed))

    def test_exact_duplicate_group_is_only_promise_machine(self):
        groups: dict[str, list[dict]] = {}
        for item in self.manifest["documents"]:
            if item["exact_duplicate_group"] is not None:
                groups.setdefault(item["exact_duplicate_group"], []).append(item)
        self.assertEqual(len(groups), 1)
        members = next(iter(groups.values()))
        self.assertEqual(len(members), 18)
        self.assertEqual(
            {item["logical_document"] for item in members}, {"promise-machine/v1"}
        )
        self.assertTrue(
            all(
                item["canonical_content_path"] == "PROMISE_MACHINE.md"
                for item in members
            )
        )

    def test_manifest_rebuild_is_exact(self):
        self.assertEqual(self.manifest, AI.build_manifest(load(PROFILES)))
        first = command(
            "verify-corpus", "--profiles", str(PROFILES), "--manifest", str(MANIFEST)
        )
        second = command(
            "verify-corpus", "--profiles", str(PROFILES), "--manifest", str(MANIFEST)
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_artifact_inventory_binds_every_baseline_record(self):
        inventory = load(INVENTORY)
        expected = {
            "corpus-manifest.json",
            "invocation-profiles.json",
            "loader-graph.json",
            "byte-partition.json",
            "cohorts.json",
            "holdout-seal.json",
        }
        self.assertEqual(set(inventory["artifacts"]), expected)
        for name, record in inventory["artifacts"].items():
            path = FIXTURES / name
            self.assertEqual(
                record, {"bytes": path.stat().st_size, "sha256": sha256(path)}
            )
        reconciliation = ROOT / "docs/instruction-architecture/corpus-reconciliation.md"
        self.assertEqual(
            inventory["reconciliation"],
            {
                "bytes": reconciliation.stat().st_size,
                "sha256": sha256(reconciliation),
            },
        )

    def test_committed_reader_refuses_coherently_resealed_generation(self):
        original_read = AI._read_regular
        graph = load(GRAPH)
        graph["unbound_reseal"] = True
        graph_raw = canonical(graph)
        inventory = load(INVENTORY)
        inventory["artifacts"]["loader-graph.json"] = {
            "bytes": len(graph_raw),
            "sha256": hashlib.sha256(graph_raw).hexdigest(),
        }
        inventory_raw = canonical(inventory)

        def resealed_generation(path: Path, limit: int) -> bytes:
            if path == INVENTORY:
                return inventory_raw
            if path == GRAPH:
                return graph_raw
            return original_read(path, limit)

        with mock.patch.object(
            AI, "_read_regular", side_effect=resealed_generation
        ):
            with self.assertRaisesRegex(
                AI.Refusal, "artifact inventory differs from its frozen source anchor"
            ):
                AI._load_committed_baseline(
                    {"invocation-profiles.json": PROFILES}
                )

    def test_independent_oracle_refuses_coherently_resealed_generation(self):
        original_read = oracle_read_regular
        graph = load(GRAPH)
        graph["unbound_reseal"] = True
        graph_raw = canonical(graph)
        inventory = load(INVENTORY)
        inventory["artifacts"]["loader-graph.json"] = {
            "bytes": len(graph_raw),
            "sha256": hashlib.sha256(graph_raw).hexdigest(),
        }
        inventory_raw = canonical(inventory)

        def resealed_generation(path: Path, limit: int) -> bytes:
            if path == INVENTORY:
                return inventory_raw
            if path == GRAPH:
                return graph_raw
            return original_read(path, limit)

        clear_source_cache()
        try:
            with (
                mock.patch.object(
                    sys.modules[__name__],
                    "oracle_read_regular",
                    side_effect=resealed_generation,
                ),
                self.assertRaisesRegex(
                    AssertionError,
                    "independent inventory differs from its source anchor",
                ),
            ):
                oracle_inventory_sources()
        finally:
            clear_source_cache()

    def test_committed_reader_refuses_changed_unrequested_payload(self):
        original_read = AI._read_regular

        def changed_graph(path: Path, limit: int) -> bytes:
            raw = original_read(path, limit)
            return raw + b" " if path == GRAPH else raw

        with mock.patch.object(AI, "_read_regular", side_effect=changed_graph):
            with self.assertRaisesRegex(
                AI.Refusal, "artifact inventory identity mismatch: loader-graph.json"
            ):
                AI._load_committed_baseline(
                    {"invocation-profiles.json": PROFILES}
                )

    def test_committed_reader_refuses_inventory_swap_during_snapshot(self):
        original_read = AI._read_regular
        inventory_reads = 0

        def changed_inventory(path: Path, limit: int) -> bytes:
            nonlocal inventory_reads
            raw = original_read(path, limit)
            if path == INVENTORY:
                inventory_reads += 1
                if inventory_reads == 2:
                    return raw + b" "
            return raw

        with mock.patch.object(AI, "_read_regular", side_effect=changed_inventory):
            with self.assertRaisesRegex(
                AI.Refusal, "artifact inventory changed during generation read"
            ):
                AI._load_committed_baseline(
                    {"invocation-profiles.json": PROFILES}
                )

    def test_build_baseline_reproduces_all_committed_outputs(self):
        with scratch_directory("instruction-architecture-rebuild-") as inside:
            output = Path(inside) / "records"
            reconciliation = Path(inside) / "corpus-reconciliation.md"
            AI.build_baseline(
                mock.Mock(output=output, reconciliation=reconciliation)
            )
            for name in (*AI.BASELINE_RECORD_NAMES, "artifact-inventory.json"):
                self.assertEqual((output / name).read_bytes(), (FIXTURES / name).read_bytes())
            self.assertEqual(
                reconciliation.read_bytes(),
                (ROOT / "docs/instruction-architecture/corpus-reconciliation.md").read_bytes(),
            )

    def test_build_baseline_commits_all_eight_outputs_as_one_generation(self):
        profiles: dict = {}
        manifest = {
            "source": {"ref": AI.SOURCE_REF, "tree_sha256": "a" * 64},
            "totals": {},
        }
        graph = {"edges": []}
        partition: dict = {}
        cohorts = {"holdout": {"logical_skills": []}}
        seal: dict = {}
        new_records = dict(
            zip(
                AI.BASELINE_RECORD_NAMES,
                map(canonical, (manifest, profiles, graph, partition, cohorts, seal)),
            )
        )
        new_reconciliation = b"new reconciliation\n"

        def seed_old_generation(output: Path, reconciliation: Path) -> None:
            output.mkdir(parents=True)
            artifacts = {}
            for name in AI.BASELINE_RECORD_NAMES:
                raw = canonical({"generation": "old", "name": name})
                (output / name).write_bytes(raw)
                artifacts[name] = {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                }
            old_reconciliation = b"old reconciliation\n"
            reconciliation.write_bytes(old_reconciliation)
            inventory = {
                "schema": f"{AI.SCHEMA_PREFIX}-artifact-inventory/v1",
                "source_ref": AI.SOURCE_REF,
                "source_tree_sha256": "a" * 64,
                "artifacts": artifacts,
                "reconciliation": {
                    "bytes": len(old_reconciliation),
                    "sha256": hashlib.sha256(old_reconciliation).hexdigest(),
                },
            }
            (output / "artifact-inventory.json").write_bytes(canonical(inventory))

        def independently_committed(
            output: Path, reconciliation: Path
        ) -> tuple[bool, str | None]:
            try:
                inventory = load(output / "artifact-inventory.json")
                if set(inventory) != {
                    "schema",
                    "source_ref",
                    "source_tree_sha256",
                    "artifacts",
                    "reconciliation",
                }:
                    return False, None
                if set(inventory["artifacts"]) != set(AI.BASELINE_RECORD_NAMES):
                    return False, None
                generations = set()
                for name, record in inventory["artifacts"].items():
                    raw = (output / name).read_bytes()
                    if record != {
                        "bytes": len(raw),
                        "sha256": hashlib.sha256(raw).hexdigest(),
                    }:
                        return False, None
                    value = json.loads(raw)
                    generations.add(value.get("generation", "new"))
                reconciliation_record = inventory["reconciliation"]
                raw = reconciliation.read_bytes()
                if {
                    "bytes": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                } != {
                    "bytes": reconciliation_record["bytes"],
                    "sha256": reconciliation_record["sha256"],
                }:
                    return False, None
                generations.add("old" if raw.startswith(b"old ") else "new")
                if len(generations) != 1:
                    return False, None
                return True, next(iter(generations))
            except (KeyError, OSError, TypeError, ValueError):
                return False, None

        derivations = (
            mock.patch.object(AI, "build_invocation_profiles", return_value=profiles),
            mock.patch.object(AI, "_validate_invocation_profiles"),
            mock.patch.object(AI, "build_manifest", return_value=manifest),
            mock.patch.object(AI, "build_loader_graph", return_value=graph),
            mock.patch.object(AI, "build_partition", return_value=partition),
            mock.patch.object(AI, "build_cohorts", return_value=cohorts),
            mock.patch.object(AI, "build_holdout_seal", return_value=seal),
            mock.patch.object(
                AI, "_reconciliation_markdown", return_value=new_reconciliation
            ),
        )
        with scratch_directory("instruction-architecture-transaction-") as inside:
            root = Path(inside)
            with (
                derivations[0],
                derivations[1],
                derivations[2],
                derivations[3],
                derivations[4],
                derivations[5],
                derivations[6],
                derivations[7],
            ):
                for boundary in range(1, 9):
                    output = root / f"records-{boundary}"
                    reconciliation = root / f"reconciliation-{boundary}.md"
                    seed_old_generation(output, reconciliation)
                    original_write = AI._atomic_write
                    calls = 0

                    def inject(path: Path, data: bytes) -> None:
                        nonlocal calls
                        calls += 1
                        if calls == boundary:
                            raise RuntimeError(f"injected refusal before write {boundary}")
                        original_write(path, data)

                    with mock.patch.object(AI, "_atomic_write", side_effect=inject):
                        with self.assertRaisesRegex(
                            RuntimeError, f"injected refusal before write {boundary}"
                        ):
                            AI.build_baseline(
                                mock.Mock(
                                    output=output,
                                    reconciliation=reconciliation,
                                )
                            )
                    accepted, generation = independently_committed(
                        output, reconciliation
                    )
                    self.assertFalse(
                        accepted and generation not in {"old", "new"},
                        f"mixed generation accepted after write boundary {boundary}",
                    )
                    self.assertEqual(
                        (accepted, generation),
                        (True, "old") if boundary == 1 else (False, None),
                    )

                output = root / "records-complete"
                reconciliation = root / "reconciliation-complete.md"
                seed_old_generation(output, reconciliation)
                writes = []
                original_write = AI._atomic_write

                def observe(path: Path, data: bytes) -> None:
                    writes.append(path.name)
                    original_write(path, data)

                with mock.patch.object(AI, "_atomic_write", side_effect=observe):
                    AI.build_baseline(
                        mock.Mock(output=output, reconciliation=reconciliation)
                    )
                self.assertEqual(len(writes), 8)
                self.assertEqual(writes[-1], "artifact-inventory.json")
                self.assertEqual(
                    {name: (output / name).read_bytes() for name in AI.BASELINE_RECORD_NAMES},
                    new_records,
                )
                self.assertEqual(reconciliation.read_bytes(), new_reconciliation)
                self.assertEqual(
                    independently_committed(output, reconciliation),
                    (True, "new"),
                )
                AI._load_committed_baseline(
                    {"invocation-profiles.json": output / "invocation-profiles.json"},
                    reconciliation,
                )

    def test_moved_runtime_and_fixtures_are_excluded(self):
        paths = [item["path"] for item in self.manifest["documents"]]
        self.assertFalse(
            any(path.startswith("distribution/skills-runtime/") for path in paths)
        )
        self.assertFalse(
            any("/fixtures/" in path or path.startswith("tests/") for path in paths)
        )

    def test_external_runtime_ownership_is_explicit(self):
        external = {
            item["path"]
            for item in self.manifest["documents"]
            if item["external_runtime_owner"] == "upstream-pashov"
        }
        self.assertTrue(any(path.endswith("/fizz/SKILL.md") for path in external))
        self.assertTrue(any(path.endswith("/x-ray/SKILL.md") for path in external))
        self.assertTrue(
            any(path.endswith("/solidity-auditor/SKILL.md") for path in external)
        )

    def test_changed_manifest_refuses(self):
        changed = copy.deepcopy(self.manifest)
        changed["totals"]["physical_bytes"] += 1
        self.assertNotEqual(changed, AI.build_manifest(load(PROFILES)))

    def test_live_source_drift_refuses(self):
        clear_source_cache()
        with (
            mock.patch.object(AI, "_source_object", return_value=b"the Git blob"),
            mock.patch.object(AI, "_read_regular", return_value=b"not the Git blob"),
        ):
            with self.assertRaisesRegex(AI.Refusal, "source drift"):
                AI._source_blob("AGENTS.md")
        clear_source_cache()

    def test_cached_git_object_never_skips_live_source_drift_check(self):
        clear_source_cache()
        self.addCleanup(clear_source_cache)
        with (
            mock.patch.object(AI, "_source_mode", return_value="git"),
            mock.patch.object(AI, "_git", return_value=b"pinned"),
            mock.patch.object(
                AI, "_read_regular", side_effect=[b"pinned", b"drifted"]
            ) as live_read,
        ):
            self.assertEqual(AI._source_blob("AGENTS.md"), b"pinned")
            with self.assertRaisesRegex(AI.Refusal, "source drift"):
                AI._source_blob("AGENTS.md")
            self.assertEqual(live_read.call_count, 2)

    def test_git_tree_path_count_and_record_shape_are_capped_before_split(self):
        self.addCleanup(clear_source_cache)

        def tree(count: int) -> bytes:
            return b"".join(f"p/{index:05d}\0".encode() for index in range(count))

        at_limit = tree(AI.MAX_FROZEN_TREE_PATHS)
        over_limit = tree(AI.MAX_FROZEN_TREE_PATHS + 1)
        specimens = (
            (over_limit, "path count limit"),
            (b"p/00000", "not canonical"),
            (b"p/00000\0\0p/00001\0", "not canonical"),
            (b"", "not canonical"),
        )
        with (
            mock.patch.object(AI, "_source_mode", return_value="git"),
            mock.patch.object(AI, "_git", return_value=at_limit),
        ):
            AI._frozen_tree_paths.cache_clear()
            self.assertEqual(len(AI._frozen_tree_paths()), AI.MAX_FROZEN_TREE_PATHS)
        for raw, reason in specimens:
            with (
                self.subTest(reason=reason, raw_bytes=len(raw)),
                mock.patch.object(AI, "_source_mode", return_value="git"),
                mock.patch.object(AI, "_git", return_value=raw),
            ):
                AI._frozen_tree_paths.cache_clear()
                with self.assertRaisesRegex(AI.Refusal, reason):
                    AI._frozen_tree_paths()

    def test_independent_git_capture_caps_stdout_and_stderr(self):
        for descriptor, amount, stream in (
            (1, ORACLE_MAX_GIT_OUTPUT + 1, "stdout"),
            (2, ORACLE_MAX_GIT_ERROR + 1, "stderr"),
        ):
            with self.subTest(stream=stream):
                tracked = oracle_guard_module()
                real_popen = subprocess.Popen
                oversized = subprocess.CompletedProcess(
                    ("git",),
                    0,
                    b"x" * amount if descriptor == 1 else b"",
                    b"x" * amount if descriptor == 2 else b"",
                )

                def spawn(*_arguments, **keywords):
                    return real_popen(
                        [
                            sys.executable,
                            "-c",
                            f"import os; os.write({descriptor}, b'x' * {amount})",
                        ],
                        **keywords,
                    )

                with (
                    mock.patch.object(subprocess, "Popen", side_effect=spawn),
                    mock.patch.object(subprocess, "run", return_value=oversized),
                    self.assertRaisesRegex(
                        AssertionError,
                        rf"independent Git {stream} exceeds byte limit",
                    ),
                ):
                    tracked.oracle_git("ignored")

    def test_independent_git_cap_kills_inherited_pipe_producer(self):
        tracked = oracle_guard_module()
        real_popen = subprocess.Popen
        with scratch_directory("oracle-git-cap-") as temporary:
            marker = Path(temporary) / "producer-finished"
            producer = (
                "import os\n"
                "from pathlib import Path\n"
                "import time\n"
                "for _ in range(6):\n"
                "    os.write(1, b'x' * 1048576)\n"
                "    time.sleep(0.05)\n"
                f"Path({str(marker)!r}).write_text('done')\n"
            )
            leader = (
                "import subprocess\n"
                "import sys\n"
                f"subprocess.Popen([sys.executable, '-c', {producer!r}])\n"
            )

            def spawn(*_arguments, **keywords):
                return real_popen(
                    [sys.executable, "-c", leader],
                    **keywords,
                )

            oversized = subprocess.CompletedProcess(
                ("git",), 0, b"x" * (ORACLE_MAX_GIT_OUTPUT + 1), b""
            )
            with (
                mock.patch.object(subprocess, "Popen", side_effect=spawn),
                mock.patch.object(subprocess, "run", return_value=oversized),
                self.assertRaisesRegex(
                    AssertionError, "independent Git stdout exceeds byte limit"
                ),
            ):
                tracked.oracle_git("ignored")
            time.sleep(0.75)
            self.assertFalse(marker.exists())

    def test_independent_git_timeout_kills_process_group(self):
        tracked = oracle_guard_module()
        real_popen = subprocess.Popen
        with scratch_directory("oracle-git-timeout-") as temporary:
            marker = Path(temporary) / "descendant-finished"
            descendant = (
                "from pathlib import Path\n"
                "import time\n"
                "time.sleep(0.5)\n"
                f"Path({str(marker)!r}).write_text('done')\n"
                "time.sleep(5)\n"
            )
            leader = (
                "import os\n"
                "import subprocess\n"
                "import sys\n"
                "import time\n"
                f"subprocess.Popen([sys.executable, '-c', {descendant!r}])\n"
                "os.write(1, b'ready')\n"
                "time.sleep(5)\n"
            )

            def spawn(*_arguments, **keywords):
                return real_popen(
                    [sys.executable, "-c", leader],
                    **keywords,
                )

            legacy = subprocess.CompletedProcess(("git",), 0, b"ready", b"")
            with (
                mock.patch.object(subprocess, "Popen", side_effect=spawn),
                mock.patch.object(subprocess, "run", return_value=legacy),
                mock.patch.object(
                    tracked.time, "monotonic", side_effect=(0.0, 0.0, 21.0)
                ),
                self.assertRaisesRegex(
                    AssertionError, "independent Git read timed out"
                ),
            ):
                tracked.oracle_git("ignored")
            time.sleep(0.75)
            self.assertFalse(marker.exists())

    def test_independent_git_successfully_writes_bounded_stdin(self):
        tracked = oracle_guard_module()
        real_popen = subprocess.Popen
        payload = b"source-object^{commit}\n"
        observed: list[bytes] = []

        def spawn(*_arguments, **keywords):
            return real_popen(
                [
                    sys.executable,
                    "-c",
                    "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())",
                ],
                **keywords,
            )

        def legacy(*_arguments, **keywords):
            observed.append(keywords["input"])
            return subprocess.CompletedProcess(("git",), 0, payload, b"")

        with (
            mock.patch.object(subprocess, "Popen", side_effect=spawn),
            mock.patch.object(subprocess, "run", side_effect=legacy),
        ):
            process = tracked.oracle_git("ignored", input_data=payload)
        self.assertEqual(
            (process.returncode, process.stdout, process.stderr),
            (0, payload, b""),
        )
        self.assertIn(observed, ([], [payload]))

    def test_independent_oracle_guard_refuses_ambiguous_parent_authority(self):
        with (
            mock.patch.dict(
                os.environ, {"FIAT1046_ELENCHUS_PARENT": "true"}, clear=False
            ),
            self.assertRaisesRegex(
                AssertionError, "independent oracle guard authority is invalid"
            ),
        ):
            oracle_guard_module()

    def test_independent_parent_oracle_pins_test_and_benchmark_to_one_oid(self):
        tracked = oracle_guard_module()
        parent = tracked.oracle_head_module()
        test_oid = getattr(parent, "__source_oid__", None)
        benchmark_oid = getattr(parent.AI, "__source_oid__", None)
        self.assertIsNotNone(test_oid)
        self.assertEqual(test_oid, benchmark_oid)
        self.assertEqual(
            getattr(parent.AI, "__source_sha256__", None),
            hashlib.sha256(
                oracle_git(
                    "show",
                    f"{test_oid}:research/instruction-architecture/benchmark.py",
                    limit=ORACLE_MAX_GIT_OUTPUT,
                ).stdout
            ).hexdigest(),
        )

    def test_independent_parent_oracle_pins_benchmark_reloads(self):
        tracked = oracle_guard_module()
        parent = tracked.oracle_head_module()
        reloaded = parent.load_module()
        expected_oid = oracle_head_oid()
        expected_source = oracle_git(
            "show",
            f"{expected_oid}:research/instruction-architecture/benchmark.py",
            limit=ORACLE_MAX_GIT_OUTPUT,
        ).stdout
        self.assertEqual(getattr(reloaded, "__source_oid__", None), expected_oid)
        self.assertEqual(
            getattr(reloaded, "__source_sha256__", None),
            hashlib.sha256(expected_source).hexdigest(),
        )

    def test_independent_parent_oracle_uses_exact_parent_code_not_live_bytes(self):
        tracked = oracle_guard_module()
        code_paths = tuple(tracked.ORACLE_STEP2_PARENT_CODE_PATHS)
        code_targets = {tracked.ROOT / path for path in code_paths}
        observed = []
        real_read = tracked.oracle_read_regular

        def hostile_live_code(path, limit):
            observed.append(path)
            if path in code_targets:
                return b"raise AssertionError('live Step 2 code escaped')\n"
            return real_read(path, limit)

        with mock.patch.object(
            tracked, "oracle_read_regular", side_effect=hostile_live_code
        ):
            parent = tracked.oracle_head_module()
        self.assertTrue(code_targets.isdisjoint(observed))
        self.assertEqual(parent.__immutable_dependency_count__, 12)
        expected_oid = tracked.oracle_head_oid()
        for path, loaded in (
            (code_paths[0], parent.AI),
            (code_paths[1], parent),
        ):
            source = tracked.oracle_tracked_source(expected_oid, path)
            self.assertEqual(
                loaded.__source_sha256__, hashlib.sha256(source).hexdigest()
            )
            self.assertEqual(
                loaded.__source_blob_oid__,
                tracked.oracle_parent_blob_oid(expected_oid, path),
            )

    def test_independent_parent_oracle_refuses_synchronised_immutable_rebinding(self):
        tracked = oracle_guard_module()
        target = next(
            path
            for path in tracked.ORACLE_STEP1_PARENT_DEPENDENCIES
            if path not in tracked.ORACLE_STEP2_PARENT_CODE_PATHS
        )
        donor = next(
            path
            for path in tracked.ORACLE_STEP1_PARENT_DEPENDENCIES
            if path != target and path not in tracked.ORACLE_STEP2_PARENT_CODE_PATHS
        )
        rebound = tuple(
            donor if path == target else path
            for path in tracked.ORACLE_STEP1_PARENT_DEPENDENCIES
        )
        real_read = tracked.oracle_read_regular

        def synchronised_drift(path, limit):
            data = real_read(path, limit)
            return data + b"\n" if path == tracked.ROOT / target else data

        with (
            mock.patch.object(
                tracked, "ORACLE_STEP1_PARENT_DEPENDENCIES", rebound
            ),
            mock.patch.object(
                tracked, "oracle_read_regular", side_effect=synchronised_drift
            ),
            self.assertRaisesRegex(
                AssertionError, "independent tracked oracle dependency drift"
            ),
        ):
            tracked.oracle_head_module()

    def test_independent_parent_oracle_refuses_step1_dependency_drift(self):
        tracked = oracle_guard_module()
        real_read = tracked.oracle_read_regular
        target = tracked.ROOT / tracked.ORACLE_STEP1_PARENT_DEPENDENCIES[0]

        def hidden_drift(path, limit):
            data = real_read(path, limit)
            return data + b"\n" if path == target else data

        with (
            mock.patch.object(
                tracked, "oracle_read_regular", side_effect=hidden_drift
            ),
            self.assertRaisesRegex(
                AssertionError, "independent tracked oracle dependency drift"
            ),
        ):
            tracked.oracle_head_module()

    def test_independent_parent_oracle_refuses_unreceipted_document_append(self):
        tracked = oracle_guard_module()
        real_read = tracked.oracle_read_regular
        target = tracked.ROOT / "docs/instruction-architecture/runbook.md"

        def unreceipted_append(path, limit):
            data = real_read(path, limit)
            return data + b"\n" if path == target else data

        with (
            mock.patch.object(
                tracked, "oracle_read_regular", side_effect=unreceipted_append
            ),
            self.assertRaisesRegex(
                AssertionError, "independent tracked oracle dependency drift"
            ),
        ):
            tracked.oracle_head_module()

    def test_independent_parent_oracle_refuses_receipted_nonprefix_rebinding(self):
        tracked = oracle_guard_module()
        real_read = tracked.oracle_read_regular
        target = tracked.ROOT / "docs/instruction-architecture/runbook.md"
        live = real_read(target, tracked.ORACLE_MAX_STEP1_DEPENDENCY_BYTES)
        rebound = bytes([live[0] ^ 1]) + live[1:]

        def nonprefix_rebinding(path, limit):
            return rebound if path == target else real_read(path, limit)

        with (
            mock.patch.object(
                tracked,
                "AMENDED_RUNBOOK_SHA256",
                hashlib.sha256(rebound).hexdigest(),
            ),
            mock.patch.object(
                tracked, "oracle_read_regular", side_effect=nonprefix_rebinding
            ),
            self.assertRaisesRegex(
                AssertionError, "independent tracked oracle dependency drift"
            ),
        ):
            tracked.oracle_head_module()

    def test_independent_parent_oracle_refuses_index_hidden_dependency_drift(self):
        tracked = oracle_guard_module()
        for flag in ("--assume-unchanged", "--skip-worktree"):
            with (
                self.subTest(flag=flag),
                scratch_directory("oracle-index-drift-") as temporary,
            ):
                repository = Path(temporary) / "repository"
                repository.mkdir()

                def git(*arguments: str) -> str:
                    process = subprocess.run(
                        ["/usr/bin/git", "-C", str(repository), *arguments],
                        stdin=subprocess.DEVNULL,
                        capture_output=True,
                        text=True,
                        check=False,
                        timeout=20,
                        env=tracked.ORACLE_GIT_ENV,
                    )
                    self.assertEqual(process.returncode, 0, process.stderr)
                    return process.stdout.strip()

                git("init", "--quiet")
                dependency = repository / "dependency"
                dependency.write_bytes(b"parent\n")
                git("add", "dependency")
                tree = git("write-tree")
                git("update-index", flag, "dependency")
                dependency.write_bytes(b"candidate\n")
                self.assertEqual(
                    git(
                        "diff",
                        "--quiet",
                        "--no-ext-diff",
                        "--no-textconv",
                        tree,
                        "--",
                        "dependency",
                    ),
                    "",
                )
                with (
                    mock.patch.object(tracked, "ROOT", repository),
                    mock.patch.object(
                        tracked,
                        "ORACLE_STEP1_PARENT_DEPENDENCIES",
                        ("dependency",),
                    ),
                    self.assertRaisesRegex(
                        AssertionError,
                        "independent tracked oracle dependency drift",
                    ),
                ):
                    tracked.oracle_assert_step1_parent_dependencies(tree)

    def test_independent_parent_oracle_refuses_filter_hidden_dependency_drift(self):
        tracked = oracle_guard_module()
        with scratch_directory("oracle-filter-drift-") as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()

            def git(*arguments: str) -> str:
                process = subprocess.run(
                    ["/usr/bin/git", "-C", str(repository), *arguments],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=20,
                    env=tracked.ORACLE_GIT_ENV,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                return process.stdout.strip()

            git("init", "--quiet")
            dependency = repository / "dependency"
            dependency.write_bytes(b"parent\n")
            (repository / ".gitattributes").write_text(
                "dependency filter=mask\n", encoding="utf-8"
            )
            git("config", "filter.mask.clean", "printf 'parent\\n'")
            git("add", "dependency", ".gitattributes")
            tree = git("write-tree")
            dependency.write_bytes(b"candidate\n")
            self.assertEqual(
                git(
                    "diff",
                    "--quiet",
                    "--no-ext-diff",
                    "--no-textconv",
                    tree,
                    "--",
                    "dependency",
                ),
                "",
            )
            with (
                mock.patch.object(tracked, "ROOT", repository),
                mock.patch.object(
                    tracked,
                    "ORACLE_STEP1_PARENT_DEPENDENCIES",
                    ("dependency",),
                ),
                self.assertRaisesRegex(
                    AssertionError,
                    "independent tracked oracle dependency drift",
                ),
            ):
                tracked.oracle_assert_step1_parent_dependencies(tree)

    def test_independent_parent_oracle_supports_both_git_object_formats(self):
        tracked = oracle_guard_module()
        parent = b"parent\n"
        candidate = b"candidate\n"
        for oid_length, algorithm in ((40, "sha1"), (64, "sha256")):
            with self.subTest(algorithm=algorithm):
                header = f"blob {len(parent)}\0".encode("ascii")
                hasher = hashlib.new(
                    algorithm, usedforsecurity=algorithm != "sha1"
                )
                hasher.update(header)
                hasher.update(parent)
                object_oid = hasher.hexdigest().encode("ascii")

                def git(*arguments, **_keywords):
                    if arguments and arguments[0] == "cat-file":
                        return subprocess.CompletedProcess(
                            arguments, 0, object_oid + b" blob\n", b""
                        )
                    return subprocess.CompletedProcess(arguments, 0, b"", b"")

                with (
                    mock.patch.object(tracked, "oracle_git", side_effect=git),
                    mock.patch.object(
                        tracked,
                        "ORACLE_STEP1_PARENT_DEPENDENCIES",
                        ("dependency",),
                    ),
                ):
                    with mock.patch.object(
                        tracked, "oracle_read_regular", return_value=parent
                    ):
                        tracked.oracle_assert_step1_parent_dependencies(
                            "0" * oid_length
                        )
                    with (
                        mock.patch.object(
                            tracked,
                            "oracle_read_regular",
                            return_value=candidate,
                        ),
                        self.assertRaisesRegex(
                            AssertionError,
                            "independent tracked oracle dependency drift",
                        ),
                    ):
                        tracked.oracle_assert_step1_parent_dependencies(
                            "0" * oid_length
                        )

    def test_independent_parent_oracle_dependency_byte_limit_is_exact(self):
        tracked = oracle_guard_module()
        with scratch_directory("oracle-dependency-limit-") as temporary:
            repository = Path(temporary) / "repository"
            repository.mkdir()

            def git(*arguments: str) -> str:
                process = subprocess.run(
                    ["/usr/bin/git", "-C", str(repository), *arguments],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=20,
                    env=tracked.ORACLE_GIT_ENV,
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                return process.stdout.strip()

            git("init", "--quiet")
            dependency = repository / "dependency"
            dependency.write_bytes(b"x" * ORACLE_MAX_STEP1_DEPENDENCY_BYTES)
            git("add", "dependency")
            tree = git("write-tree")
            with (
                mock.patch.object(tracked, "ROOT", repository),
                mock.patch.object(
                    tracked,
                    "ORACLE_STEP1_PARENT_DEPENDENCIES",
                    ("dependency",),
                ),
            ):
                tracked.oracle_assert_step1_parent_dependencies(tree)
                git("update-index", "--assume-unchanged", "dependency")
                dependency.write_bytes(
                    b"x" * (ORACLE_MAX_STEP1_DEPENDENCY_BYTES + 1)
                )
                with self.assertRaisesRegex(
                    AssertionError, "independent input exceeds byte limit"
                ):
                    tracked.oracle_assert_step1_parent_dependencies(tree)

    def test_independent_git_tree_caps_count_and_requires_canonical_nuls(self):
        tracked = oracle_guard_module()

        def tree(count: int) -> bytes:
            return b"".join(f"p/{index:05d}\0".encode() for index in range(count))

        at_limit = tree(ORACLE_MAX_FROZEN_TREE_PATHS)
        with (
            mock.patch.object(tracked, "oracle_source_mode", return_value="git"),
            mock.patch.object(
                tracked,
                "oracle_git",
                return_value=subprocess.CompletedProcess(("git",), 0, at_limit, b""),
            ),
        ):
            tracked.oracle_tree_paths.cache_clear()
            self.assertEqual(
                len(tracked.oracle_tree_paths()), ORACLE_MAX_FROZEN_TREE_PATHS
            )

        specimens = (
            (tree(ORACLE_MAX_FROZEN_TREE_PATHS + 1), "count limit"),
            (b"p/00000", "canonically framed"),
            (b"p/00000\0\0p/00001\0", "canonically framed"),
            (b"\0p/00000\0", "canonically framed"),
            (b".\0", "unsafe"),
        )
        for raw, reason in specimens:
            with (
                self.subTest(reason=reason, raw_bytes=len(raw)),
                mock.patch.object(
                    tracked, "oracle_source_mode", return_value="git"
                ),
                mock.patch.object(
                    tracked,
                    "oracle_git",
                    return_value=subprocess.CompletedProcess(
                        ("git",), 0, raw, b""
                    ),
                ),
                self.assertRaisesRegex(AssertionError, reason),
            ):
                tracked.oracle_tree_paths.cache_clear()
                tracked.oracle_tree_paths()

    def test_independent_git_blob_cap_is_enforced_before_live_comparison(self):
        tracked = oracle_guard_module()
        path = "AGENTS.md"
        at_limit = b"x" * ORACLE_MAX_SOURCE_BYTES
        at_limit_git = mock.Mock(
            return_value=subprocess.CompletedProcess(("git",), 0, at_limit, b"")
        )
        with (
            mock.patch.object(tracked, "oracle_source_mode", return_value="git"),
            mock.patch.object(tracked, "oracle_git", at_limit_git),
            mock.patch.object(tracked, "oracle_read_regular", return_value=at_limit),
        ):
            tracked.ORACLE_SOURCE_CACHE.clear()
            self.assertEqual(tracked.oracle_source(path), at_limit)
        with self.subTest(boundary="call-site-limit"):
            self.assertEqual(
                at_limit_git.call_args.kwargs.get("limit"), ORACLE_MAX_SOURCE_BYTES
            )

        oversized = b"x" * (ORACLE_MAX_SOURCE_BYTES + 1)
        with (
            self.subTest(boundary="over-limit"),
            mock.patch.object(tracked, "oracle_source_mode", return_value="git"),
            mock.patch.object(
                tracked,
                "oracle_git",
                return_value=subprocess.CompletedProcess(
                    ("git",), 0, oversized, b""
                ),
            ),
            mock.patch.object(
                tracked, "oracle_read_regular", return_value=oversized
            ) as live_read,
            self.assertRaisesRegex(
                AssertionError, "independent source blob exceeds byte limit"
            ),
        ):
            tracked.ORACLE_SOURCE_CACHE.clear()
            tracked.oracle_source(path)
        live_read.assert_not_called()

    def test_independent_oracle_cache_never_skips_live_source_drift_check(self):
        clear_source_cache()
        self.addCleanup(clear_source_cache)
        with (
            mock.patch.object(
                sys.modules[__name__], "oracle_source_mode", return_value="git"
            ),
            mock.patch.object(
                sys.modules[__name__],
                "oracle_git",
                return_value=mock.Mock(returncode=0, stdout=b"pinned"),
            ),
            mock.patch.object(
                sys.modules[__name__],
                "oracle_read_regular",
                side_effect=[b"pinned", b"drifted"],
            ) as live_read,
        ):
            self.assertEqual(oracle_source("AGENTS.md"), b"pinned")
            with self.assertRaisesRegex(
                AssertionError, "independent oracle observed source drift"
            ):
                oracle_source("AGENTS.md")
            self.assertEqual(live_read.call_count, 2)

    def test_git_output_limit_stops_producer_before_completion(self):
        with scratch_directory() as inside:
            root = Path(inside)
            binary = root / "bin"
            binary.mkdir()
            marker = root / "producer-finished"
            fake_git = binary / "git"
            producer = (
                "import os\n"
                "from pathlib import Path\n"
                "import time\n"
                "for _ in range(8):\n"
                "    os.write(1, b'x' * 512)\n"
                "    time.sleep(0.1)\n"
                f"Path({str(marker)!r}).write_text('done')\n"
            )
            fake_git.write_text(
                f"#!{sys.executable}\n"
                "import subprocess\n"
                "import sys\n"
                f"subprocess.Popen([sys.executable, '-c', {producer!r}])\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            environment = {
                "PATH": f"{binary}{os.pathsep}{os.environ.get('PATH', '')}"
            }
            with (
                mock.patch.object(
                    AI,
                    "_git_executable",
                    return_value=str(fake_git.resolve()),
                    create=True,
                ),
                mock.patch.dict(AI.os.environ, environment, clear=False),
            ):
                with self.assertRaisesRegex(AI.Refusal, "output exceeded"):
                    AI._git(["ignored"], limit=1_024)
            time.sleep(1)
            self.assertFalse(marker.exists())

    def test_git_child_is_absolute_closed_and_network_inert(self):
        with scratch_directory() as inside:
            fake_git = Path(inside) / "git"
            fake_git.write_text(
                f"#!{sys.executable}\n"
                "import json\n"
                "import os\n"
                "import sys\n"
                "print(json.dumps({'argv': sys.argv, 'env': dict(os.environ)}, sort_keys=True))\n",
                encoding="utf-8",
            )
            fake_git.chmod(0o755)
            spawned: dict[str, str] = {}
            real_popen = AI.subprocess.Popen

            def capture_environment(*arguments, **keywords):
                spawned.update(keywords["env"])
                return real_popen(*arguments, **keywords)

            with (
                mock.patch.object(
                    AI,
                    "_git_executable",
                    return_value=str(fake_git.resolve()),
                    create=True,
                ),
                mock.patch.object(
                    AI.subprocess, "Popen", side_effect=capture_environment
                ),
                mock.patch.dict(
                    AI.os.environ,
                    {
                        "INSTRUCTION_ARCHITECTURE_SECRET": "do-not-copy",
                        "PATH": f"{inside}{os.pathsep}{os.environ.get('PATH', '')}",
                    },
                    clear=False,
                ),
            ):
                observed = json.loads(AI._git(["version"]))
        self.assertEqual(observed["argv"][0], str(fake_git.resolve()))
        self.assertIn("--no-lazy-fetch", observed["argv"])
        expected_environment = {
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_LITERAL_PATHSPECS": "1",
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_NO_REPLACE_OBJECTS": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "LANG": "C",
            "LC_ALL": "C",
        }
        self.assertEqual(spawned, expected_environment)
        self.assertEqual(
            {key: observed["env"].get(key) for key in expected_environment},
            expected_environment,
        )
        self.assertNotIn("INSTRUCTION_ARCHITECTURE_SECRET", observed["env"])
        self.assertNotIn("HOME", observed["env"])
        self.assertNotIn("PATH", observed["env"])

    def test_git_executable_ignores_ambient_path(self):
        with scratch_directory() as inside:
            fake_git = Path(inside) / "git"
            fake_git.write_text("not executable by the workbench\n", encoding="utf-8")
            fake_git.chmod(0o755)
            with mock.patch.dict(AI.os.environ, {"PATH": str(inside)}, clear=False):
                resolver = getattr(AI, "_git_executable", lambda: "git")
                executable = Path(resolver())
        self.assertTrue(executable.is_absolute())
        self.assertNotEqual(executable, fake_git)

    def test_nonzero_git_exit_never_signals_a_reaped_process_group(self):
        with mock.patch.object(AI.os, "killpg") as killpg:
            with self.assertRaisesRegex(AI.Refusal, "refused the source"):
                AI._git(["definitely-not-a-git-command"])
        killpg.assert_not_called()

    def test_git_replace_ref_cannot_pivot_the_source_object(self):
        with scratch_directory("instruction-architecture-git-") as inside:
            repository = Path(inside) / "repository"
            repository.mkdir()

            def git(*arguments: str) -> str:
                result = subprocess.run(
                    ["git", "-C", str(repository), *arguments],
                    stdin=subprocess.DEVNULL,
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return result.stdout.strip()

            git("init", "--quiet")
            git("config", "user.name", "fixture")
            git("config", "user.email", "fixture@example.invalid")
            git("config", "commit.gpgsign", "false")
            source = repository / "source.md"
            source.write_text("original\n", encoding="utf-8")
            git("add", "source.md")
            git("commit", "--quiet", "-m", "original")
            original = git("rev-parse", "HEAD")
            source.write_text("replacement\n", encoding="utf-8")
            git("commit", "--quiet", "-am", "replacement")
            replacement = git("rev-parse", "HEAD")
            git("replace", original, replacement)
            self.assertEqual(
                git("cat-file", "blob", f"{original}:source.md"), "replacement"
            )
            with mock.patch.object(AI, "ROOT", repository):
                self.assertEqual(
                    AI._git(["cat-file", "blob", f"{original}:source.md"]),
                    b"original\n",
                )

    def test_regular_read_refuses_parent_symlink_escape(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            outside_record = Path(outside) / "record.json"
            outside_record.write_text("{}\n", encoding="utf-8")
            escape = Path(inside) / "escape"
            escape.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(
                AI.Refusal, "outside repository|unavailable or unsafe"
            ):
                AI._read_regular(escape / "record.json", AI.MAX_JSON_BYTES)

    def test_regular_read_refuses_fifo_without_blocking(self):
        with scratch_directory("fifo-input-") as temporary:
            fifo = Path(temporary) / "record.json"
            os.mkfifo(fifo)
            probe = "\n".join(
                (
                    "from pathlib import Path",
                    "import sys",
                    "from tests.test_instruction_architecture import AI",
                    "try:",
                    "    AI._read_regular(Path(sys.argv[1]), AI.MAX_JSON_BYTES)",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO input was accepted')",
                )
            )
            process = subprocess.Popen(
                [sys.executable, "-c", probe, str(fifo)],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                self.fail("regular-file input open blocked on a FIFO")
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(
                stdout.strip(), "input is not a single-link regular file"
            )

    def _assert_fifo_output_probe(
        self, probe: str, target: Path, expected: str, blocked: str
    ) -> None:
        process = subprocess.Popen(
            [sys.executable, "-c", probe, str(target)],
            cwd=ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            self.fail(blocked)
        self.assertEqual(process.returncode, 0, stderr)
        self.assertEqual(stdout.strip(), expected)

    def test_atomic_write_refuses_fifo_stage_replacement_without_blocking(self):
        with scratch_directory("fifo-output-stage-") as temporary:
            target = Path(temporary) / "record.json"
            probe = "\n".join(
                (
                    "import os",
                    "from pathlib import Path",
                    "import sys",
                    "from unittest import mock",
                    "from tests.test_instruction_architecture import AI",
                    "target = Path(sys.argv[1])",
                    "real_open = os.open",
                    "real_unlink = os.unlink",
                    "real_mkfifo = os.mkfifo",
                    "swapped = False",
                    "def racing_open(path, flags, *args, **kwargs):",
                    "    global swapped",
                    "    if (not swapped and isinstance(path, str)",
                    "            and path.startswith('.record.json.')",
                    "            and not flags & os.O_WRONLY):",
                    "        swapped = True",
                    "        real_unlink(path, dir_fd=kwargs['dir_fd'])",
                    "        real_mkfifo(path, dir_fd=kwargs['dir_fd'])",
                    "    return real_open(path, flags, *args, **kwargs)",
                    "try:",
                    "    with mock.patch.object(AI.os, 'open', side_effect=racing_open):",
                    "        AI._atomic_write(target, b'{}\\n')",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO stage replacement was accepted')",
                )
            )
            self._assert_fifo_output_probe(
                probe,
                target,
                "output stage changed before publication",
                "output stage verification blocked on a FIFO replacement",
            )

    def test_atomic_write_refuses_fifo_published_replacement_without_blocking(self):
        with scratch_directory("fifo-published-output-") as temporary:
            target = Path(temporary) / "record.json"
            probe = "\n".join(
                (
                    "import os",
                    "from pathlib import Path",
                    "import sys",
                    "from unittest import mock",
                    "from tests.test_instruction_architecture import AI",
                    "target = Path(sys.argv[1])",
                    "real_replace = os.replace",
                    "real_unlink = os.unlink",
                    "real_mkfifo = os.mkfifo",
                    "def racing_replace(source, destination, *args, **kwargs):",
                    "    real_replace(source, destination, *args, **kwargs)",
                    "    real_unlink(destination, dir_fd=kwargs['dst_dir_fd'])",
                    "    real_mkfifo(destination, dir_fd=kwargs['dst_dir_fd'])",
                    "try:",
                    "    with mock.patch.object(AI.os, 'replace', side_effect=racing_replace):",
                    "        AI._atomic_write(target, b'{}\\n')",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO published replacement was accepted')",
                )
            )
            self._assert_fifo_output_probe(
                probe,
                target,
                "input is not a single-link regular file",
                "published output verification blocked on a FIFO replacement",
            )

    def test_fresh_named_identity_refuses_fifo_without_blocking(self):
        with scratch_directory("fifo-output-identity-") as temporary:
            target = Path(temporary) / "record.json"
            probe = "\n".join(
                (
                    "import os",
                    "from pathlib import Path",
                    "import sys",
                    "from tests.test_instruction_architecture import AI",
                    "target = Path(sys.argv[1])",
                    "target.write_bytes(b'{}\\n')",
                    "expected = target.stat()",
                    "relative = AI._repository_relative(target, 'output')",
                    "parent, _ = AI._open_parent(relative, create=False, label='output')",
                    "try:",
                    "    parent_identity = AI._directory_identity(os.fstat(parent))",
                    "finally:",
                    "    os.close(parent)",
                    "target.unlink()",
                    "os.mkfifo(target)",
                    "try:",
                    "    AI._fresh_named_identity(relative, parent_identity, expected)",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO identity replacement was accepted')",
                )
            )
            self._assert_fifo_output_probe(
                probe,
                target,
                "output changed during publication",
                "final output identity check blocked on a FIFO replacement",
            )

    def test_atomic_write_refuses_hardlinked_stage_before_publication(self):
        with scratch_directory("hardlinked-output-stage-") as temporary:
            target = Path(temporary) / "record.json"
            original_open = os.open
            original_fsync = os.fsync
            stage: tuple[str, int] | None = None
            linked = False

            def observe_open(path, flags, *arguments, **keywords):
                nonlocal stage
                descriptor = original_open(path, flags, *arguments, **keywords)
                if (
                    stage is None
                    and isinstance(path, str)
                    and path.startswith(".record.json.")
                    and flags & os.O_WRONLY
                ):
                    stage = (path, keywords["dir_fd"])
                return descriptor

            def racing_fsync(descriptor):
                nonlocal linked
                result = original_fsync(descriptor)
                if not linked and stage is not None:
                    linked = True
                    os.link(
                        stage[0],
                        ".retained-stage-link",
                        src_dir_fd=stage[1],
                        dst_dir_fd=stage[1],
                    )
                return result

            with (
                mock.patch.object(AI.os, "open", side_effect=observe_open),
                mock.patch.object(AI.os, "fsync", side_effect=racing_fsync),
                self.assertRaisesRegex(
                    AI.Refusal, "output stage is not a single-link regular file"
                ),
            ):
                AI._atomic_write(target, b"{}\n")
            self.assertFalse(target.exists())

    def test_atomic_write_refuses_same_bytes_stage_replacement(self):
        with scratch_directory("same-bytes-stage-replacement-") as temporary:
            target = Path(temporary) / "record.json"
            original_replace = os.replace

            def racing_replace(source, destination, *arguments, **keywords):
                os.unlink(source, dir_fd=keywords["src_dir_fd"])
                descriptor = os.open(
                    source,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=keywords["src_dir_fd"],
                )
                try:
                    os.write(descriptor, b"{}\n")
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                return original_replace(
                    source, destination, *arguments, **keywords
                )

            with (
                mock.patch.object(AI.os, "replace", side_effect=racing_replace),
                self.assertRaisesRegex(
                    AI.Refusal, "published output does not match the verified stage"
                ),
            ):
                AI._atomic_write(target, b"{}\n")

    def test_atomic_write_refuses_same_bytes_published_replacement(self):
        with scratch_directory("same-bytes-published-replacement-") as temporary:
            target = Path(temporary) / "record.json"
            original_replace = os.replace

            def racing_replace(source, destination, *arguments, **keywords):
                result = original_replace(
                    source, destination, *arguments, **keywords
                )
                os.unlink(destination, dir_fd=keywords["dst_dir_fd"])
                descriptor = os.open(
                    destination,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=keywords["dst_dir_fd"],
                )
                try:
                    os.write(descriptor, b"{}\n")
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
                return result

            with (
                mock.patch.object(AI.os, "replace", side_effect=racing_replace),
                self.assertRaisesRegex(
                    AI.Refusal, "published output does not match the verified stage"
                ),
            ):
                AI._atomic_write(target, b"{}\n")

    def test_regular_read_refuses_concurrent_parent_swap(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            holder = Path(inside)
            outside = Path(outside)
            safe = holder / "safe"
            safe.mkdir()
            target = safe / "record.json"
            target.write_text("inside\n", encoding="utf-8")
            (outside / "record.json").write_text("outside\n", encoding="utf-8")
            original_open = os.open
            swapped = False

            def racing_open(path, flags, *arguments, **keywords):
                nonlocal swapped
                if not swapped and path == "record.json" and "dir_fd" in keywords:
                    swapped = True
                    safe.rename(holder / "safe-old")
                    safe.symlink_to(outside, target_is_directory=True)
                return original_open(path, flags, *arguments, **keywords)

            with mock.patch.object(AI.os, "open", side_effect=racing_open):
                with self.assertRaisesRegex(AI.Refusal, "parent|changed"):
                    AI._read_regular(target, AI.MAX_JSON_BYTES)

    def test_atomic_write_refuses_concurrent_parent_swap_without_escape(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            holder = Path(inside)
            outside = Path(outside)
            safe = holder / "safe"
            safe.mkdir()
            target = safe / "record.json"
            original_replace = os.replace
            swapped = False

            def racing_replace(source, destination, *arguments, **keywords):
                nonlocal swapped
                if not swapped:
                    swapped = True
                    safe.rename(holder / "safe-old")
                    safe.symlink_to(outside, target_is_directory=True)
                    if "src_dir_fd" not in keywords:
                        staged = holder / "safe-old" / Path(source).name
                        staged.rename(outside / Path(source).name)
                return original_replace(source, destination, *arguments, **keywords)

            with mock.patch.object(AI.os, "replace", side_effect=racing_replace):
                with self.assertRaisesRegex(
                    AI.Refusal, "parent|outside repository"
                ):
                    AI._atomic_write(target, b"bounded\n")
            self.assertFalse((outside / "record.json").exists())

    def test_json_depth_and_token_caps_refuse_before_decode(self):
        depth_ceiling = AI.MAX_JSON_DEPTH
        token_ceiling = AI.MAX_JSON_TOKENS
        with scratch_directory() as inside:
            deep = Path(inside) / "deep.json"
            deep.write_bytes(
                b"[" * (depth_ceiling + 1) + b"0" + b"]" * (depth_ceiling + 1)
            )
            with self.assertRaisesRegex(AI.Refusal, "JSON depth limit"):
                AI._load_record(deep)

            wide = Path(inside) / "wide.json"
            wide.write_bytes(
                b'{"items":[' + b"0," * (token_ceiling + 1) + b"0]}\n"
            )
            with self.assertRaisesRegex(AI.Refusal, "JSON token limit"):
                AI._load_record(wide)

    def test_oversized_json_integer_refuses_without_parser_exception(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(b'{"value":' + b"1" * 5_000 + b"}\n")
            try:
                AI._load_record(record)
            except Exception as exc:
                self.assertIsInstance(exc, AI.Refusal)
                self.assertRegex(str(exc), "number length limit|strict UTF-8 JSON")
            else:
                self.fail("oversized JSON integer was accepted")

    def test_integer_bound_does_not_depend_on_the_host_python_limit(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(b'{"value":' + b"1" * 5_000 + b"}\n")
            prior_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(0)
                with self.assertRaisesRegex(AI.Refusal, "number length limit"):
                    AI._load_record(record)
            finally:
                sys.set_int_max_str_digits(prior_limit)

    def test_integer_bound_remains_usable_at_the_lowest_host_limit(self):
        with scratch_directory() as inside:
            record = Path(inside) / "integer.json"
            record.write_bytes(
                b'{"value":' + b"1" * AI.MAX_JSON_NUMBER_CHARS + b"}\n"
            )
            prior_limit = sys.get_int_max_str_digits()
            try:
                sys.set_int_max_str_digits(sys.int_info.str_digits_check_threshold)
                value, _ = AI._load_record(record)
            finally:
                sys.set_int_max_str_digits(prior_limit)
            self.assertEqual(len(str(value["value"])), AI.MAX_JSON_NUMBER_CHARS)

    def test_non_scalar_json_refuses_without_encoder_exception(self):
        with scratch_directory() as inside:
            record = Path(inside) / "surrogate.json"
            record.write_bytes(b'{"value":"\\ud800"}\n')
            duplicate = Path(inside) / "duplicate-surrogate.json"
            duplicate.write_bytes(b'{"\\ud800":1,"\\ud800":2}\n')
            for specimen in (record, duplicate):
                with self.subTest(specimen=specimen.name):
                    try:
                        AI._load_record(specimen)
                    except AI.Refusal as exc:
                        self.assertTrue(str(exc).isascii())
                    except Exception as exc:
                        self.fail(f"unbounded parser exception: {type(exc).__name__}")
                    else:
                        self.fail("non-scalar JSON was accepted")

    def test_build_baseline_refuses_unowned_output_paths_before_derivation(self):
        manifest = {"source": {"tree_sha256": "0" * 64}, "totals": {}}
        graph = {"roots": [], "edges": []}
        cohorts = {"holdout": {"logical_skills": []}}
        for output, reconciliation in (
            (ROOT, None),
            (FIXTURES, ROOT / "AGENTS.md"),
            (FIXTURES, ROOT / ".git/config"),
        ):
            with self.subTest(output=output, reconciliation=reconciliation):
                arguments = mock.Mock(output=output, reconciliation=reconciliation)
                with (
                    mock.patch.object(AI, "build_manifest", return_value=manifest) as derive,
                    mock.patch.object(AI, "build_loader_graph", return_value=graph),
                    mock.patch.object(AI, "build_partition", return_value={}),
                    mock.patch.object(AI, "build_cohorts", return_value=cohorts),
                    mock.patch.object(AI, "build_holdout_seal", return_value={}),
                    mock.patch.object(AI, "_reconciliation_markdown", return_value=b""),
                    mock.patch.object(AI, "_atomic_write") as write,
                ):
                    try:
                        AI.build_baseline(arguments)
                    except AI.Refusal:
                        refused = True
                    else:
                        refused = False
                self.assertTrue(refused, "unowned output path was accepted")
                derive.assert_not_called()
                write.assert_not_called()

    def test_build_baseline_refuses_output_aliases_before_derivation(self):
        with scratch_directory("instruction-architecture-alias-") as inside:
            output = Path(inside) / "records"
            for reconciliation in (
                output,
                output / "corpus-manifest.json",
                output / "artifact-inventory.json",
                output / "corpus-manifest.json" / "nested.md",
            ):
                with self.subTest(reconciliation=reconciliation):
                    arguments = mock.Mock(
                        output=output,
                        reconciliation=reconciliation,
                    )
                    with mock.patch.object(AI, "build_manifest") as derive:
                        with self.assertRaisesRegex(AI.Refusal, "overlaps"):
                            AI.build_baseline(arguments)
                    derive.assert_not_called()

    def test_output_refuses_parent_symlink_escape_without_writing(self):
        with (
            scratch_directory() as inside,
            tempfile.TemporaryDirectory() as outside,
        ):
            escape = Path(inside) / "escape"
            escape.symlink_to(outside, target_is_directory=True)
            target = escape / "record.json"
            with self.assertRaisesRegex(
                AI.Refusal, "not a real directory|parent is unavailable or unsafe"
            ):
                AI._safe_output(target)
            self.assertFalse((Path(outside) / "record.json").exists())

    def test_schema_closes_every_object_definition(self):
        schema = load(SCHEMA)
        self.assertEqual(
            {item["$ref"] for item in schema["oneOf"]},
            {
                "#/$defs/artifactInventory",
                "#/$defs/cohorts",
                "#/$defs/holdoutSeal",
                "#/$defs/loaderGraph",
                "#/$defs/manifest",
                "#/$defs/partition",
            },
        )
        object_definitions = [
            value for value in schema["$defs"].values() if value.get("type") == "object"
        ]
        self.assertGreaterEqual(len(object_definitions), 15)
        self.assertTrue(
            all(
                value.get("additionalProperties") is False
                for value in object_definitions
            )
        )

    def test_runtime_and_schema_share_the_canonical_path_language(self):
        schema = load(SCHEMA)["$defs"]["path"]
        pattern = re.compile(schema["pattern"])

        def schema_accepts(value: str) -> bool:
            return (
                schema["minLength"] <= len(value) <= schema["maxLength"]
                and pattern.search(value) is not None
            )

        accepted = ("a", "a b", "a/b", "a" * 1_024)
        refused = (
            "",
            ".",
            "..",
            "a/.",
            "a/..",
            "a//b",
            "a/",
            "/a",
            "a\\b",
            "a\x00b",
            "a\x1fb",
            "a\n",
            "a\r",
            "a\x7fb",
            "é",
            "a" * 1_025,
        )
        for specimen in accepted:
            with self.subTest(accepted=repr(specimen[:32])):
                self.assertEqual(AI._safe_relative(specimen).as_posix(), specimen)
                self.assertTrue(schema_accepts(specimen))
        for specimen in refused:
            with self.subTest(refused=repr(specimen[:32])):
                with self.assertRaises(AI.Refusal):
                    AI._safe_relative(specimen)
                self.assertFalse(schema_accepts(specimen))

    def test_runtime_refuses_a_noncanonical_path_before_normalisation(self):
        with self.assertRaises(AI.Refusal):
            AI._safe_relative("a//b")

    def test_study_copy_changes_only_relative_link_depth(self):
        shipped = STUDY.read_bytes()
        self.assertEqual(shipped.count(b"](../../plugins/"), 10)
        receipted = shipped.replace(b"](../../plugins/", b"](../plugins/")
        self.assertEqual(hashlib.sha256(receipted).hexdigest(), RECEIPTED_STUDY_SHA256)
        self.assertEqual(sha256(RUNBOOK), AMENDED_RUNBOOK_SHA256)


class FollowOnAudit2ParentGuardTests(unittest.TestCase):
    """Guards that stay assertion-red on the exact follow-on-2 parent."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.graph = load(GRAPH)

    def test_source_owned_profile_product_replaces_singleton_witnesses(self):
        self.assertEqual(len(self.graph["scenario_roots"]), 2_595)
        self.assertTrue(
            self.graph["constraints"].get("invocation_profiles_are_source_owned")
        )
        self.assertTrue(
            self.graph["constraints"].get("profile_route_product_is_exact")
        )

    def test_local_version_files_are_fixed_read_only_agent_inputs(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            "plugins/hexaemeron/skills/solidity-auditor/VERSION",
            "plugins/hexaemeron/skills/x-ray/VERSION",
        }
        self.assertLessEqual(expected, set(documents))
        for path in expected:
            self.assertEqual(documents[path]["load_semantics"], "agent-or-prompt")
            incoming = [
                edge
                for edge in self.graph["scenario_edges"]
                if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(all(edge["kind"] == "fixed-agent-input" for edge in incoming))

    def test_human_reference_docs_have_no_production_reachability(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        expected = {
            "plugins/hexaemeron/skills/imprimatur/references/agent-replies.md",
            "plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md",
            "plugins/hexaemeron/skills/imprimatur/references/rewriting.md",
            "plugins/pandects/docs/applicability.md",
            "plugins/pandects/docs/writing-a-law.md",
            "plugins/pandects/integrations/wildcat/APPLICABILITY.md",
        }
        for path in expected:
            self.assertEqual(documents[path]["load_semantics"], "reference-only")
            self.assertEqual(documents[path]["loader_roots"], [])
            self.assertEqual(documents[path]["scenario_reachability"], [])


class FollowOnAudit6ParentGuardTests(unittest.TestCase):
    """Guards that stay assertion-red on exact parent 46572571528e."""

    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)

    def test_profile_validator_rejects_a_valid_non_skill_span_rebinding(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            row for row in changed["profiles"] if row["id"] == "fiat:close-audit"
        )
        selected = next(
            row
            for row in profile["source_evidence"]
            if row["obligation"] == ORACLE_SKILL_PATHS["fiat"]
        )
        audit_loop = next(
            row
            for row in profile["source_evidence"]
            if row["obligation"]
            == "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
        )
        for key in ("path", "start", "end", "source_sha256", "span_sha256"):
            audit_loop[key] = selected[key]
        digest = hashlib.sha256(canonical(changed["profiles"])).hexdigest()
        changed["projection_sha256"] = digest
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
                AI._validate_invocation_profiles(changed)

    def test_manifest_validator_rejects_synchronised_source_metadata_drift(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["source_path"] = metadata[donor]["source_path"]
        metadata[target]["source_needle"] = metadata[donor]["source_needle"]
        changed = copy.deepcopy(self.manifest)
        by_path = {item["path"]: item for item in changed["documents"]}
        by_path[target]["source_evidence"] = copy.deepcopy(
            by_path[donor]["source_evidence"]
        )
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "manifest semantic source anchor drift"
            ):
                AI._validate_manifest_shape(changed)

    def test_graph_builder_rejects_synchronised_runtime_metadata_drift(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["runtime_path"] = metadata[donor]["runtime_path"]
        metadata[target]["runtime_needle"] = metadata[donor]["runtime_needle"]
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "scenario runtime semantic anchor drift"
            ):
                changed_manifest = AI.build_manifest(self.profiles)
                AI.build_loader_graph(changed_manifest, self.profiles)


class InvocationProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)

    def reseal(self, changed: dict) -> str:
        digest = hashlib.sha256(canonical(changed["profiles"])).hexdigest()
        changed["projection_sha256"] = digest
        return digest

    def validate_synchronized_production_projection(self, changed: dict) -> None:
        digest = self.reseal(changed)
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            AI._validate_invocation_profiles(changed)

    def test_profile_ledger_is_exact_and_source_owned(self):
        self.assertEqual(self.profiles, AI.build_invocation_profiles())
        AI._validate_invocation_profiles(self.profiles)
        self.assertEqual(
            self.profiles["projection_sha256"],
            "b09aeb1ba087dff0c34c3fad63a9096c4862aad71b14fe6c6a12a14819c94c07",
        )
        self.assertEqual(self.profiles["counts"], AI.EXPECTED_PROFILE_COUNTS)

    def test_direct_profile_validator_refuses_non_object_records_without_crashing(self):
        tracked = oracle_guard_module().AI
        nested_profile = copy.deepcopy(self.profiles)
        nested_profile["profiles"][0] = [
            "id",
            "selected_skill",
            "phase",
            "applicability",
            "branch_state",
            "exclusive_group",
            "required_documents",
            "worker_prompts",
            "fixed_inputs",
            "source_evidence",
        ]
        nested_profile["projection_sha256"] = tracked._sha256(
            tracked._canonical_json(nested_profile["profiles"])
        )
        specimens = (
            None,
            [
                "schema",
                "source_ref",
                "counts",
                "totals",
                "projection_sha256",
                "profiles",
            ],
            nested_profile,
        )
        with mock.patch.object(
            tracked,
            "EXPECTED_PROFILE_PROJECTION_SHA256",
            nested_profile["projection_sha256"],
        ):
            for specimen in specimens:
                with self.subTest(specimen=type(specimen).__name__):
                    try:
                        tracked._validate_invocation_profiles(specimen)
                    except tracked.Refusal as exc:
                        self.assertRegex(str(exc), "must be an object")
                    except Exception as exc:
                        self.fail(
                            "non-object invocation profiles crashed with "
                            f"{type(exc).__name__}"
                        )
                    else:
                        self.fail("non-object invocation profiles were accepted")

    def test_independent_source_owned_profile_and_route_oracle(self):
        oracle_validate_profiles_and_routes(self.profiles, self.graph)

    def semantic_cross_class_rebinding_specimens(self):
        specimens = {}
        for profile_index, profile in enumerate(self.profiles["profiles"]):
            for evidence_index, evidence in enumerate(profile["source_evidence"]):
                evidence_class, _, _ = oracle_full_semantic_anchor(
                    profile, evidence["obligation"]
                )
                if evidence_class in specimens:
                    continue
                identity = {
                    key: evidence[key]
                    for key in ("path", "start", "end", "source_sha256", "span_sha256")
                }
                for donor_index, donor in enumerate(profile["source_evidence"]):
                    donor_class, _, _ = oracle_full_semantic_anchor(
                        profile, donor["obligation"]
                    )
                    donor_identity = {
                        key: donor[key]
                        for key in (
                            "path",
                            "start",
                            "end",
                            "source_sha256",
                            "span_sha256",
                        )
                    }
                    if (
                        donor_index != evidence_index
                        and donor_class != evidence_class
                        and donor["path"] != evidence["path"]
                        and donor_identity != identity
                    ):
                        specimens[evidence_class] = (
                            profile_index,
                            evidence_index,
                            donor_identity,
                        )
                        break
        self.assertEqual(set(specimens), set(ORACLE_PROFILE_EVIDENCE_COUNTS))
        return specimens

    def test_validator_refuses_valid_cross_class_cross_target_rebinding(self):
        for evidence_class, (
            profile_index,
            evidence_index,
            donor_identity,
        ) in self.semantic_cross_class_rebinding_specimens().items():
            with self.subTest(evidence_class=evidence_class):
                changed = copy.deepcopy(self.profiles)
                evidence = changed["profiles"][profile_index]["source_evidence"][
                    evidence_index
                ]
                evidence.update(donor_identity)
                digest = hashlib.sha256(canonical(changed["profiles"])).hexdigest()
                changed["projection_sha256"] = digest
                with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
                    with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
                        AI._validate_invocation_profiles(changed)

    def test_independent_oracle_refuses_cross_class_cross_target_rebinding(self):
        for evidence_class, (
            profile_index,
            evidence_index,
            donor_identity,
        ) in self.semantic_cross_class_rebinding_specimens().items():
            with self.subTest(evidence_class=evidence_class):
                profile = copy.deepcopy(self.profiles["profiles"][profile_index])
                profile["source_evidence"][evidence_index].update(donor_identity)
                with self.assertRaisesRegex(
                    AssertionError, "independent semantic anchor mismatch"
                ):
                    oracle_validate_semantic_anchors(profile)

    def test_independent_semantic_anchor_coverage_is_closed(self):
        observed = {name: 0 for name in ORACLE_PROFILE_EVIDENCE_COUNTS}
        required = 0
        evidence = 0
        for profile in self.profiles["profiles"]:
            counts = oracle_validate_semantic_anchors(profile)
            for name, count_for_profile in counts.items():
                observed[name] += count_for_profile
            required += len(profile["required_documents"])
            evidence += len(profile["source_evidence"])
        self.assertEqual(observed, ORACLE_PROFILE_EVIDENCE_COUNTS)
        self.assertEqual(required, 5_084)
        self.assertEqual(evidence, required)

    def test_every_required_document_has_one_named_source_witness(self):
        evidence_rows = 0
        required_documents = 0
        for profile in self.profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                obligations = [
                    evidence.get("obligation")
                    for evidence in profile["source_evidence"]
                ]
                self.assertEqual(obligations, profile["required_documents"])
                self.assertEqual(len(obligations), len(set(obligations)))
                evidence_rows += len(obligations)
                required_documents += len(profile["required_documents"])
        self.assertEqual(evidence_rows, 5_084)
        self.assertEqual(required_documents, 5_084)

    def test_every_skill_and_frontier_witness_is_semantically_attributable(self):
        checked = 0
        for profile in self.profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                oracle_validate_semantic_anchors(profile)
                checked += sum(
                    path.endswith(("/SKILL.md", "/EVOLUTION.md"))
                    for path in profile["required_documents"]
                )
        self.assertEqual(checked, 3_157)

    def test_profile_route_denominators_are_exact(self):
        self.assertEqual(
            self.profiles["totals"],
            {
                "normalized_profiles": 519,
                "repository_roots": 1_038,
                "agent_skills_roots": 1_038,
                "standalone_roots": 519,
                "scenario_roots": 2_595,
            },
        )
        self.assertEqual(len(self.graph["scenario_roots"]), 2_595)

    def test_fiat_phase_product_is_not_a_curated_edge_count(self):
        phases: dict[str, int] = {}
        for profile in self.profiles["profiles"]:
            if profile["selected_skill"] == "fiat":
                phases[profile["phase"]] = phases.get(profile["phase"], 0) + 1
        self.assertEqual(
            phases,
            {
                "implement directive": 360,
                "Solidity audit round": 18,
                "non-Solidity audit round": 8,
                "prose directive": 16,
                "study directive": 2,
                "bounded controller operation": 11,
            },
        )

    def test_kronos_dispatch_profiles_load_the_repin_boundary(self):
        currency = (
            "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"
        )
        source = ORACLE_SKILL_PATHS["kronos"]
        needle = (
            "`../fiat/references/plugin-currency.md` names the host\n"
            "   mechanism."
        )
        self.assertIn("and the Kronos re-pin boundary.", oracle_source(currency).decode())
        self.assertIn(needle, oracle_source(source).decode())

        kronos = [
            row
            for row in self.profiles["profiles"]
            if row["selected_skill"] == "kronos"
        ]
        dispatch = [row for row in kronos if "dispatch-" in row["id"]]
        rank_only = [row for row in kronos if "rank-only" in row["id"]]
        self.assertEqual((len(dispatch), len(rank_only)), (24, 2))
        expected_evidence = oracle_evidence(currency, source, needle)
        for profile in dispatch:
            with self.subTest(profile=profile["id"]):
                self.assertIn(currency, profile["required_documents"])
                evidence = {
                    row["obligation"]: row for row in profile["source_evidence"]
                }
                self.assertEqual(evidence[currency], expected_evidence)
        self.assertTrue(
            all(currency not in profile["required_documents"] for profile in rank_only)
        )

        currency_reach = {
            root
            for edge in self.graph["scenario_edges"]
            if edge["target"] == currency
            for root in edge["active_scenarios"]
        }
        dispatch_ids = {row["id"] for row in dispatch}
        rank_only_ids = {row["id"] for row in rank_only}
        dispatch_roots = {
            row["id"]
            for row in self.graph["scenario_roots"]
            if row["profile_id"] in dispatch_ids
        }
        rank_only_roots = {
            row["id"]
            for row in self.graph["scenario_roots"]
            if row["profile_id"] in rank_only_ids
        }
        self.assertEqual(len(dispatch_roots), 120)
        self.assertLessEqual(dispatch_roots, currency_reach)
        self.assertTrue(rank_only_roots.isdisjoint(currency_reach))

    def test_every_profile_document_union_and_worker_set_is_closed(self):
        for profile in self.profiles["profiles"]:
            with self.subTest(profile=profile["id"]):
                documents = profile["required_documents"]
                workers = profile["worker_prompts"]
                self.assertEqual(documents, sorted(set(documents)))
                self.assertEqual(workers, sorted(set(workers)))
                self.assertLessEqual(set(workers), set(documents))
                self.assertIn(
                    AI.SELECTABLE_SKILL_PATHS[profile["selected_skill"]], documents
                )

    def test_profile_schema_is_closed_at_every_object(self):
        schema = load(PROFILE_SCHEMA)
        self.assertFalse(schema["additionalProperties"])
        objects = [
            value
            for value in schema["$defs"].values()
            if value.get("type") == "object"
        ]
        self.assertGreaterEqual(len(objects), 5)
        self.assertTrue(all(value.get("additionalProperties") is False for value in objects))

    def test_verify_profiles_is_read_only_and_repeatable(self):
        first = command("verify-profiles", "--profiles", str(PROFILES))
        second = command("verify-profiles", "--profiles", str(PROFILES))
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_projection_mutation_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["projection_sha256"] = "0" * 64
        with self.assertRaisesRegex(AI.Refusal, "projection digest"):
            AI._validate_invocation_profiles(changed)

    def test_one_profile_omission_refuses_even_when_totals_are_forged(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"].pop()
        with self.assertRaisesRegex(AI.Refusal, "denominator"):
            self.validate_synchronized_production_projection(changed)

    def test_duplicate_profile_id_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"][1]["id"] = changed["profiles"][0]["id"]
        with self.assertRaisesRegex(AI.Refusal, "id product"):
            self.validate_synchronized_production_projection(changed)

    def test_worker_outside_required_union_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(item for item in changed["profiles"] if item["worker_prompts"])
        profile["required_documents"].remove(profile["worker_prompts"][0])
        with self.assertRaisesRegex(AI.Refusal, "document or worker union"):
            self.validate_synchronized_production_projection(changed)

    def test_reference_only_document_in_profile_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = changed["profiles"][0]
        profile["required_documents"].append(sorted(AI.REFERENCE_ONLY_MARKDOWN)[0])
        profile["required_documents"].sort()
        with self.assertRaisesRegex(AI.Refusal, "human reference"):
            self.validate_synchronized_production_projection(changed)

    def test_fixed_input_execution_fiction_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item
            for item in changed["profiles"]
            if any(row["path"].endswith("/VERSION") for row in item["fixed_inputs"])
        )
        version = next(
            row for row in profile["fixed_inputs"] if row["path"].endswith("/VERSION")
        )
        version["load_semantics"] = "mandatory-executable"
        with self.assertRaisesRegex(AI.Refusal, "fixed input semantics"):
            self.validate_synchronized_production_projection(changed)

    def test_source_span_drift_refuses(self):
        changed = copy.deepcopy(self.profiles)
        changed["profiles"][0]["source_evidence"][0]["span_sha256"] = "0" * 64
        with self.assertRaisesRegex(AI.Refusal, "source span"):
            self.validate_synchronized_production_projection(changed)

    def test_synchronized_obligation_fiction_refuses_both_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"] if item["id"] == "alexandria:ordinary"
        )
        invented = ORACLE_SKILL_PATHS["phylax"]
        profile["required_documents"].append(invented)
        profile["required_documents"].sort()
        evidence = copy.deepcopy(profile["source_evidence"][0])
        evidence["obligation"] = invented
        profile["source_evidence"].append(evidence)
        profile["source_evidence"].sort(key=lambda row: row["obligation"])

        with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "independent profile grammar"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_bare_basename_refuses_both_semantic_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"]
            if item["selected_skill"] == "fiat"
            and ORACLE_SKILL_PATHS["phylax"] in item["required_documents"]
        )
        obligation = ORACLE_SKILL_PATHS["phylax"]
        index = profile["required_documents"].index(obligation)
        profile["source_evidence"][index] = oracle_evidence(
            obligation, "plugins/hexaemeron/PROMISES.md", "SKILL.md"
        )

        with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "semantic anchor"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_first_occurrence_refuses_both_semantic_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"]
            if item["selected_skill"] == "fiat"
            and ORACLE_SKILL_PATHS["phylax"] in item["required_documents"]
        )
        obligation = ORACLE_SKILL_PATHS["phylax"]
        index = profile["required_documents"].index(obligation)
        profile["source_evidence"][index] = oracle_evidence(
            obligation, ORACLE_SKILL_PATHS["fiat"], "SKILL.md"
        )

        with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "semantic anchor"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_valid_span_rebinding_refuses_both_validators(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            item for item in changed["profiles"]
            if item["selected_skill"] == "fiat"
            and ORACLE_SKILL_PATHS["phylax"] in item["required_documents"]
            and ORACLE_SKILL_PATHS["ephoros"] in item["required_documents"]
        )
        obligation = ORACLE_SKILL_PATHS["phylax"]
        replacement = copy.deepcopy(
            next(
                row for row in profile["source_evidence"]
                if row["obligation"] == ORACLE_SKILL_PATHS["ephoros"]
            )
        )
        replacement["obligation"] = obligation
        index = profile["required_documents"].index(obligation)
        profile["source_evidence"][index] = replacement

        with self.assertRaisesRegex(AI.Refusal, "semantic anchor drift"):
            self.validate_synchronized_production_projection(changed)
        with self.assertRaisesRegex(AssertionError, "semantic anchor"):
            oracle_validate_profiles_and_routes(changed, self.graph)

    def test_synchronized_profile_and_routes_refuse_independent_oracle(self):
        changed_profiles = copy.deepcopy(self.profiles)
        changed_graph = copy.deepcopy(self.graph)
        old_profile_id = "alexandria:ordinary"
        new_profile_id = "alexandria:invented"
        profile = next(
            item
            for item in changed_profiles["profiles"]
            if item["id"] == old_profile_id
        )
        profile["id"] = new_profile_id

        root_ids: dict[str, str] = {}
        for root in changed_graph["scenario_roots"]:
            if root["profile_id"] != old_profile_id:
                continue
            old_root_id = root["id"]
            new_root_id = old_root_id.replace(
                f":profile:{old_profile_id}:",
                f":profile:{new_profile_id}:",
            )
            root_ids[old_root_id] = new_root_id
            root["id"] = new_root_id
            root["profile_id"] = new_profile_id
            root["conditions"] = [
                f"profile:{new_profile_id}"
                if condition == f"profile:{old_profile_id}"
                else condition
                for condition in root["conditions"]
            ]
        changed_graph["scenario_roots"].sort(key=lambda row: row["id"])
        self.assertEqual(len(root_ids), 5)
        for edge in changed_graph["scenario_edges"]:
            edge["active_scenarios"] = sorted(
                root_ids.get(identifier, identifier)
                for identifier in edge["active_scenarios"]
            )

        digest = self.reseal(changed_profiles)
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            AI._validate_invocation_profiles(changed_profiles)
            AI._validate_complete_scenarios(changed_graph, changed_profiles)
        with self.assertRaisesRegex(AssertionError, "independent profile grammar"):
            oracle_validate_profiles_and_routes(changed_profiles, changed_graph)

    def test_missing_bundle_edge_refuses_against_profile_union(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["kind"] == "worker-dispatch"
        )
        removed = edge["active_scenarios"].pop()
        edge["eligible_base_scenarios"] = sorted(
            {
                root["base_scenario"]
                for root in changed["scenario_roots"]
                if root["id"] in edge["active_scenarios"]
            }
        )
        with self.assertRaisesRegex(AI.Refusal, "scenario document union"):
            AI._validate_complete_scenarios(changed, self.profiles)
        self.assertTrue(removed)

    def test_synchronized_route_omission_refuses_5n_oracle(self):
        changed = copy.deepcopy(self.graph)
        profile_id = self.profiles["profiles"][0]["id"]
        removed = {
            root["id"]
            for root in changed["scenario_roots"]
            if root["profile_id"] == profile_id
        }
        changed["scenario_roots"] = [
            root for root in changed["scenario_roots"] if root["id"] not in removed
        ]
        for edge in changed["scenario_edges"]:
            edge["active_scenarios"] = [
                item for item in edge["active_scenarios"] if item not in removed
            ]
            if edge["active_scenarios"]:
                edge["eligible_base_scenarios"] = sorted(
                    {
                        root["base_scenario"]
                        for root in changed["scenario_roots"]
                        if root["id"] in edge["active_scenarios"]
                    }
                )
        changed["scenario_edges"] = [
            edge for edge in changed["scenario_edges"] if edge["active_scenarios"]
        ]
        with self.assertRaisesRegex(AI.Refusal, "denominator|5N"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_bogus_profile_binding_refuses(self):
        changed = copy.deepcopy(self.graph)
        changed["scenario_roots"][0]["profile_id"] = "fiat:invented"
        with self.assertRaisesRegex(AI.Refusal, "5N|unknown profile"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_credential_roster_leak_refuses(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["target"] == "CONTRIBUTORS.md"
        )
        absent = next(
            root["id"]
            for root in changed["scenario_roots"]
            if root["route"] == "repository"
            and root["credential"] == "absent"
            and root["base_scenario"] in edge["eligible_base_scenarios"]
        )
        edge["active_scenarios"].append(absent)
        edge["active_scenarios"].sort()
        with self.assertRaisesRegex(AI.Refusal, "scenario document union"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_reference_only_reachability_refuses(self):
        changed = copy.deepcopy(self.graph)
        target = changed["reference_only"][0]["path"]
        edge = copy.deepcopy(changed["scenario_edges"][0])
        edge["id"] = "scenario-edge-99999"
        edge["target"] = target
        changed["scenario_edges"].append(edge)
        with self.assertRaisesRegex(AI.Refusal, "scenario document union|reference-only"):
            AI._validate_complete_scenarios(changed, self.profiles)

    def test_fixed_input_edge_kind_mutation_refuses(self):
        changed = copy.deepcopy(self.graph)
        edge = next(
            item
            for item in changed["scenario_edges"]
            if item["kind"] == "fixed-agent-input"
        )
        edge["kind"] = "mandatory-executable"
        with self.assertRaisesRegex(AI.Refusal, "fixed agent input"):
            AI._validate_complete_scenarios(changed, self.profiles)


class BytePartitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.partition = load(PARTITION)
        cls.sources = {item["path"]: item for item in cls.manifest["documents"]}

    def test_every_range_is_ordered_gapless_and_digest_bound(self):
        self.assertEqual(len(self.partition["files"]), 191)
        for file_record in self.partition["files"]:
            source = AI._source_blob(file_record["path"])
            cursor = 0
            for item in file_record["ranges"]:
                self.assertEqual(item["start"], cursor)
                self.assertGreater(item["end"], item["start"])
                self.assertEqual(
                    item["span_sha256"],
                    hashlib.sha256(source[item["start"] : item["end"]]).hexdigest(),
                )
                cursor = item["end"]
            self.assertEqual(cursor, len(source))
            self.assertEqual(
                file_record["source_sha256"],
                self.sources[file_record["path"]]["sha256"],
            )

    def test_partition_totals_reconcile(self):
        self.assertEqual(sum(self.partition["totals"].values()), 2_290_450)
        self.assertEqual(self.partition["unsupported_operative_bytes"], 0)
        self.assertEqual(self.partition["totals"]["generated_duplicate"], 471_444)
        self.assertEqual(
            self.partition["totals"],
            {
                "exact_literal_or_evidence": 345_771,
                "generated_duplicate": 471_444,
                "governed_operative_semantics": 1_473_235,
                "human_only_explanation_or_rationale": 0,
                "unsupported_or_unknown": 0,
            },
        )

    def test_only_generated_promise_copies_use_duplicate_class(self):
        generated = {
            item["path"]
            for item in self.partition["files"]
            if {row["classification"] for row in item["ranges"]}
            == {"generated_duplicate"}
        }
        self.assertEqual(len(generated), 17)
        self.assertNotIn("PROMISE_MACHINE.md", generated)
        self.assertTrue(all(path.endswith("/PROMISE_MACHINE.md") for path in generated))

    def test_structured_references_are_whole_file_exact_evidence(self):
        by_path = {item["path"]: item for item in self.partition["files"]}
        for path, (size, digest) in EXPECTED_STRUCTURED_REFERENCES.items():
            with self.subTest(path=path):
                self.assertEqual(
                    by_path[path]["ranges"],
                    [{
                        "start": 0,
                        "end": size,
                        "classification": "exact_literal_or_evidence",
                        "span_sha256": digest,
                    }],
                )

    def test_nested_fences_remain_exact_literal_evidence(self):
        specimens = {
            "plugins/hexaemeron/skills/fiat/references/push-discipline.md": b"plugin-ci-workflow | filed",
            "plugins/hexaemeron/skills/solidity-auditor/references/report-formatting.md": b"- vulnerable line(s)",
        }
        by_path = {item["path"]: item for item in self.partition["files"]}
        for path, needle in specimens.items():
            source = AI._source_blob(path)
            position = source.index(needle)
            containing = next(
                item
                for item in by_path[path]["ranges"]
                if item["start"] <= position < item["end"]
            )
            self.assertEqual(
                containing["classification"], "exact_literal_or_evidence", path
            )

    def test_space_indented_fence_pairs_remain_exact_literal_evidence(self):
        """Independently retain fenced literals nested under list containers."""
        by_path = {item["path"]: item for item in self.partition["files"]}
        observed: list[tuple[str, int, int]] = []
        marker = re.compile(rb"^( {4,})(`{3,}|~{3,})([^\r\n]*)")
        for path, file_record in by_path.items():
            if not path.endswith(".md"):
                continue
            source = oracle_source(path)
            lines = source.splitlines(keepends=True)
            offsets = list(
                itertools.accumulate((len(line) for line in lines), initial=0)
            )
            for index, line in enumerate(lines):
                opening = marker.match(line)
                if opening is None or not opening.group(3).strip(b" \t"):
                    continue
                indent = opening.group(1)
                fence = opening.group(2)
                closing = re.compile(
                    rb"^"
                    + re.escape(indent)
                    + re.escape(fence[:1])
                    + rb"{"
                    + str(len(fence)).encode("ascii")
                    + rb",}[ \t]*(?:\r?\n)?$"
                )
                close_index = next(
                    (
                        candidate
                        for candidate in range(index + 1, len(lines))
                        if closing.match(lines[candidate])
                    ),
                    None,
                )
                if close_index is None:
                    continue
                start = offsets[index]
                end = offsets[close_index + 1]
                observed.append((path, start, end))
                for position in (start, end - 1):
                    containing = next(
                        item
                        for item in file_record["ranges"]
                        if item["start"] <= position < item["end"]
                    )
                    self.assertEqual(
                        containing["classification"],
                        "exact_literal_or_evidence",
                        f"{path}:{index + 1}-{close_index + 1}",
                    )
        self.assertEqual(
            observed,
            [
                (
                    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/"
                    "protocol-type-specialist.md",
                    2368,
                    2975,
                ),
                (
                    "plugins/hexaemeron/skills/fizz/skills/fizz-sync/SKILL.md",
                    11063,
                    11227,
                ),
            ],
        )

    def test_nested_list_fence_parser_keeps_literal_and_resumes_prose(self):
        source = (
            b"1. outer\n"
            b"   - example:\n"
            b"     ```solidity\n"
            b"     uint256 value = 1;\n"
            b"     ```\n"
            b"   - after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("nested-list.md", generated=False)
        literal = source.index(b"uint256")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_nested_fence_retains_deepest_applicable_list_baseline(self):
        """A root-valid opener must still close relative to its list item."""
        for opening_indent, closing_indent in itertools.product((2, 3), (4, 5)):
            ranges = None
            source = (
                b"- item\n"
                + b" " * opening_indent
                + b"```text\n"
                + b"  body\n"
                + b" " * closing_indent
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(
                opening_indent=opening_indent,
                closing_indent=closing_indent,
            ), mock.patch.object(AI, "_source_blob", return_value=source):
                try:
                    ranges = AI._partition_ranges("nested-list.md", generated=False)
                except AI.Refusal as exc:
                    self.fail(f"valid list-contained fence was refused: {exc}")
            if ranges is None:
                continue
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_fence_container_falls_back_to_root_after_list_exit(self):
        source = (
            b"- item\n"
            b"\n"
            b"```text\n"
            b"root literal\n"
            b"```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("root-fallback.md", generated=False)
        literal = source.index(b"root literal")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_list_marker_tab_padding_uses_absolute_tab_stops(self):
        """Marker padding tabs advance from the marker's ending column."""
        for marker in (b"-\titem", b"- \titem", b"10.\titem"):
            source = (
                marker
                + b"\n"
                + b"    ```text\n"
                + b"    body\n"
                + b"      ```\n"
                + b"after\n"
            )
            with self.subTest(marker=marker), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges("tab-list.md", generated=False)
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_same_line_nested_markers_retain_the_deepest_baseline(self):
        source = (
            b"- - item\n"
            b"    ```text\n"
            b"    body\n"
            b"      ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("same-line-nested.md", generated=False)
        literal = source.index(b"body")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_fence_after_same_line_list_markers_uses_deepest_baseline(self):
        specimens = {
            "bullet-backtick": (b"- ", b"```", 2),
            "ordered-tilde": (b"10. ", b"~~~", 4),
            "nested-backtick": (b"- - ", b"```", 4),
            "tab-padded-tilde": (b"-\t", b"~~~", 4),
            "mixed-tab-backtick": (b"- \t", b"```", 4),
            "ordered-tab-backtick": (b"10.\t", b"```", 4),
            "indented-bullet-backtick": (b"   - ", b"```", 5),
            "triple-nested-tilde": (b"1. - + ", b"~~~~", 7),
        }
        for name, (prefix, fence, baseline) in specimens.items():
            for close_offset in range(4):
                ranges = None
                source = (
                    prefix
                    + fence
                    + b"text\n"
                    + b" " * baseline
                    + b"body\n"
                    + b" " * (baseline + close_offset)
                    + fence
                    + b"\nafter\n"
                )
                with self.subTest(
                    name=name, close_offset=close_offset
                ), mock.patch.object(AI, "_source_blob", return_value=source):
                    try:
                        ranges = AI._partition_ranges(
                            f"{name}.md", generated=False
                        )
                    except AI.Refusal as exc:
                        self.fail(
                            f"valid same-line list fence was refused: {exc}"
                        )
                if ranges is None:
                    continue
                for needle in (prefix + fence, b"body"):
                    position = source.index(needle)
                    self.assertEqual(
                        next(
                            item["classification"]
                            for item in ranges
                            if item["start"] <= position < item["end"]
                        ),
                        "exact_literal_or_evidence",
                    )
                prose = source.index(b"after")
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= prose < item["end"]
                    ),
                    "governed_operative_semantics",
                )

    def test_empty_list_items_establish_their_content_baseline(self):
        """A blank first block uses one column after the list marker."""
        specimens = {
            "bullet": (b"-\n", 2),
            "spaced-bullet": (b"-   \n", 2),
            "ordered": (b"10.\n", 4),
            "spaced-ordered": (b"10.  \n", 4),
        }
        for name, (prefix, baseline) in specimens.items():
            for close_offset in range(4):
                source = (
                    prefix
                    + b" " * baseline
                    + b"```text\n"
                    + b" " * baseline
                    + b"body\n"
                    + b" " * (baseline + close_offset)
                    + b"```\n"
                    + b"after\n"
                )
                with self.subTest(
                    name=name, close_offset=close_offset
                ), mock.patch.object(AI, "_source_blob", return_value=source):
                    ranges = AI._partition_ranges(
                        f"empty-{name}.md", generated=False
                    )
                literal = source.index(b"body")
                prose = source.index(b"after")
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= literal < item["end"]
                    ),
                    "exact_literal_or_evidence",
                )
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= prose < item["end"]
                    ),
                    "governed_operative_semantics",
                )

    def test_thematic_breaks_do_not_establish_list_baselines(self):
        for thematic in (b"- - -\n", b"* * *\n"):
            source = (
                thematic
                + b"    ```text\n"
                + b"    body\n"
                + b"      ```\n"
                + b"after\n"
            )
            with self.subTest(thematic=thematic), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges("thematic.md", generated=False)
            for needle in (b"```text", b"body", b"after"):
                position = source.index(needle)
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= position < item["end"]
                    ),
                    "governed_operative_semantics",
                )

        source = (
            b"- + item\n"
            b"    ```text\n"
            b"    body\n"
            b"       ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("mixed-list.md", generated=False)
        literal = source.index(b"body")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_thematic_precedence_does_not_expand_per_marker(self):
        """One admitted line needs constant thematic-suffix state."""
        marker_count = 32_768
        source = b"* " * (marker_count - 1) + b"*\n"
        real_set = set
        real_fullmatch = AI.re.fullmatch
        materialized_items = 0
        regex_input_bytes = 0

        def counted_set(value=()):
            nonlocal materialized_items
            items = list(value)
            materialized_items += len(items)
            return real_set(items)

        def counted_fullmatch(pattern, value, *args, **kwargs):
            nonlocal regex_input_bytes
            regex_input_bytes += len(value)
            return real_fullmatch(pattern, value, *args, **kwargs)

        with mock.patch.object(
            AI, "_source_blob", return_value=source
        ), mock.patch.object(
            AI, "set", side_effect=counted_set, create=True
        ), mock.patch.object(
            AI.re, "fullmatch", side_effect=counted_fullmatch
        ):
            ranges = AI._partition_ranges(
                "thematic-expansion.md", generated=False
            )
        self.assertEqual(
            {item["classification"] for item in ranges},
            {"governed_operative_semantics"},
        )
        self.assertLessEqual(materialized_items, 4)
        self.assertLessEqual(regex_input_bytes, 4)

        separated = (
            b"* x * * *\n"
            b"    ```text\n"
            b"  body\n"
            b"    ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=separated):
            ranges = AI._partition_ranges(
                "thematic-separated-prefix.md", generated=False
            )
        literal = separated.index(b"body")
        prose = separated.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_partition_preflight_caps_lines_and_fence_events_before_fanout(self):
        for label, source in {
            "line-limit": b"prose\n" * 16_384,
            "cr-line-limit": b"prose\r" * 16_384,
            "crlf-line-limit": b"prose\r\n" * 16_384,
            "fence-event-limit": b"   ```\n" * 4_096,
        }.items():
            with self.subTest(label=label), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                AI._partition_ranges(f"{label}.md", generated=False)

        for label, (source, message) in {
            "line-over-limit": (
                b"prose\n" * 16_385,
                "Markdown physical line count exceeds limit",
            ),
            "cr-line-over-limit": (
                b"prose\r" * 16_385,
                "Markdown physical line count exceeds limit",
            ),
            "crlf-line-over-limit": (
                b"prose\r\n" * 16_385,
                "Markdown physical line count exceeds limit",
            ),
            "fence-event-over-limit": (
                b"   ```\n" * 4_097,
                "Markdown root-leading fence event count exceeds limit",
            ),
        }.items():
            with self.subTest(label=label), mock.patch.object(
                AI, "_source_blob", return_value=source
            ), self.assertRaisesRegex(AI.Refusal, message):
                AI._partition_ranges(f"{label}.md", generated=False)

    def test_list_container_depth_is_capped_before_append(self):
        at_limit = b"- " * 4_096 + b"item\n"
        with mock.patch.object(AI, "_source_blob", return_value=at_limit):
            ranges = AI._partition_ranges("list-depth-limit.md", generated=False)
        self.assertEqual(
            {item["classification"] for item in ranges},
            {"governed_operative_semantics"},
        )

        over_limit = b"- " * 4_097 + b"item\n"
        with mock.patch.object(
            AI, "_source_blob", return_value=over_limit
        ), self.assertRaisesRegex(
            AI.Refusal, "Markdown list container depth exceeds limit"
        ):
            AI._partition_ranges("list-depth-over-limit.md", generated=False)

    def test_lazy_paragraph_continuation_retains_the_list_baseline(self):
        specimens = {
            "bullet": (b"- item\n", 2),
            "ordered": (b"1. item\n", 3),
        }
        for name, (prefix, baseline) in specimens.items():
            source = (
                prefix
                + b"lazy continuation\n"
                + b" " * (baseline + 2)
                + b"```text\n"
                + b" " * baseline
                + b"body\n"
                + b" " * (baseline + 3)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(name=name), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges(
                    f"lazy-{name}.md", generated=False
                )
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

        source = (
            b"- item\n"
            b"\n"
            b"outside\n"
            b"    ```text\n"
            b"    body\n"
            b"    ```\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("ended-list.md", generated=False)
        for needle in (b"```text", b"body"):
            position = source.index(needle)
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= position < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_ancestor_relative_block_interrupt_ends_inner_lazy_paragraph(self):
        outer_items = {
            "four-column": (b"10. outer\n", 4),
            "eleven-column": (b"000000001. outer\n", 11),
        }
        blocks = {
            "thematic": b"---\n",
            "heading": b"# head\n",
            "blockquote": b"> quote\n",
        }
        for (outer_name, (outer, baseline)), (
            block_name,
            block,
        ) in itertools.product(outer_items.items(), blocks.items()):
            source = (
                outer
                + b" " * baseline
                + b"- inner paragraph\n"
                + b" " * baseline
                + block
                + b" " * (baseline + 4)
                + b"```text\n"
                + b" " * (baseline + 4)
                + b"body\n"
                + b" " * (baseline + 5)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(
                outer=outer_name, block=block_name
            ), mock.patch.object(AI, "_source_blob", return_value=source):
                ranges = AI._partition_ranges(
                    f"ancestor-{outer_name}-{block_name}.md", generated=False
                )
            for needle in (b"```text", b"body", b"after"):
                position = source.index(needle)
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= position < item["end"]
                    ),
                    "governed_operative_semantics",
                )

        for outer, baseline in outer_items.values():
            source = (
                outer
                + b" " * baseline
                + b"- inner paragraph\n"
                + b" " * baseline
                + b"lazy continuation\n"
                + b" " * (baseline + 4)
                + b"```text\n"
                + b" " * (baseline + 4)
                + b"body\n"
                + b" " * (baseline + 5)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(
                outer=outer, block="lazy-text-inverse"
            ), mock.patch.object(AI, "_source_blob", return_value=source):
                ranges = AI._partition_ranges(
                    "ancestor-lazy-text.md", generated=False
                )
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_only_ordered_one_can_interrupt_an_open_paragraph(self):
        for ordinal in (b"2.", b"10.", b"123456789."):
            source = (
                b"paragraph\n"
                + ordinal
                + b" item\n"
                + b" " * (len(ordinal) + 1)
                + b"```text\n"
                + b" " * (len(ordinal) + 1)
                + b"body\n"
                + b" " * (len(ordinal) + 3)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(ordinal=ordinal), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                if ordinal == b"2.":
                    with self.assertRaisesRegex(
                        AI.Refusal, "unterminated Markdown fence"
                    ):
                        AI._partition_ranges(
                            "paragraph-ordered.md", generated=False
                        )
                    continue
                ranges = AI._partition_ranges(
                    "paragraph-ordered.md", generated=False
                )
                for needle in (b"```text", b"body", b"after"):
                    position = source.index(needle)
                    self.assertEqual(
                        next(
                            item["classification"]
                            for item in ranges
                            if item["start"] <= position < item["end"]
                        ),
                        "governed_operative_semantics",
                    )

        source = (
            b"paragraph\n"
            b"1. item\n"
            b"   ```text\n"
            b"   body\n"
            b"     ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("paragraph-one.md", generated=False)
        literal = source.index(b"body")
        prose = source.index(b"after")
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= literal < item["end"]
            ),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            next(
                item["classification"]
                for item in ranges
                if item["start"] <= prose < item["end"]
            ),
            "governed_operative_semantics",
        )

    def test_leading_zero_numeric_one_interrupts_an_open_paragraph(self):
        for ordinal, delimiter in itertools.product(
            (b"01", b"001", b"000000001"), (b".", b")")
        ):
            marker = ordinal + delimiter
            baseline = len(marker) + 1
            source = (
                b"paragraph\n"
                + marker
                + b" item\n"
                + b" " * baseline
                + b"```text\n"
                + b" " * baseline
                + b"body\n"
                + b" " * (baseline + 3)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(
                ordinal=ordinal, delimiter=delimiter
            ), mock.patch.object(AI, "_source_blob", return_value=source):
                ranges = AI._partition_ranges(
                    "paragraph-leading-zero-one.md", generated=False
                )
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

        for ordinal in (b"000000000", b"000000002"):
            marker = ordinal + b"."
            baseline = len(marker) + 1
            source = (
                b"paragraph\n"
                + marker
                + b" item\n"
                + b" " * baseline
                + b"```text\n"
                + b" " * baseline
                + b"body\n"
                + b" " * (baseline + 3)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(ordinal=ordinal), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges(
                    "paragraph-leading-zero-non-one.md", generated=False
                )
            for needle in (b"```text", b"body", b"after"):
                position = source.index(needle)
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= position < item["end"]
                    ),
                    "governed_operative_semantics",
                )

    def test_indented_code_item_does_not_seed_a_lazy_paragraph(self):
        specimens = {
            "bullet-spaces": (b"-     code\n", 2),
            "bullet-tab-stop": (b"-   \tcode\n", 2),
            "ordered-spaces": (b"1.     code\n", 3),
            "ordered-tab-stop": (b"1.  \tcode\n", 3),
        }
        for name, (prefix, baseline) in specimens.items():
            source = (
                prefix
                + b"outside\n"
                + b"    ```text\n"
                + b"    body\n"
                + b"    ```\n"
                + b"after\n"
            )
            with self.subTest(name=name, transition="exit"), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges(
                    f"indented-code-{name}.md", generated=False
                )
            for needle in (b"```text", b"body", b"after"):
                position = source.index(needle)
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= position < item["end"]
                    ),
                    "governed_operative_semantics",
                )

            source = (
                prefix
                + b" " * baseline
                + b"```text\n"
                + b" " * baseline
                + b"body\n"
                + b" " * (baseline + 3)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(
                name=name, transition="retained-container"
            ), mock.patch.object(AI, "_source_blob", return_value=source):
                ranges = AI._partition_ranges(
                    f"indented-code-{name}.md", generated=False
                )
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

        for prefix, baseline in (
            (b"-    item\n", 5),
            (b"-\titem\n", 4),
            (b"1.    item\n", 6),
            (b"1.\titem\n", 4),
        ):
            source = (
                prefix
                + b"lazy continuation\n"
                + b" " * baseline
                + b"```text\n"
                + b" " * baseline
                + b"body\n"
                + b" " * (baseline + 3)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(
                prefix=prefix, transition="paragraph-padding"
            ), mock.patch.object(AI, "_source_blob", return_value=source):
                ranges = AI._partition_ranges(
                    "bounded-padding-paragraph.md", generated=False
                )
            literal = source.index(b"body")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )

    def test_underindented_list_marker_replaces_the_lazy_container(self):
        specimens = {
            "wider-ordered-sibling": (b"1. first\n", b"10. second\n", 4),
            "zero-padded-sibling": (b"1. first\n", b"010. second\n", 5),
            "changed-delimiter": (b"1. first\n", b"10) second\n", 4),
            "ordered-after-bullet": (b"- first\n", b"2. second\n", 3),
            "empty-ordered-after-bullet": (b"- first\n", b"2.\n", 3),
            "empty-bullet-after-ordered": (b"1. first\n", b"-\n", 2),
        }
        for name, (first, second, baseline) in specimens.items():
            ranges = None
            source = (
                first
                + second
                + b" " * baseline
                + b"```text\n"
                + b" " * baseline
                + b"body\n"
                + b" " * (baseline + 3)
                + b"```\n"
                + b"after\n"
            )
            with self.subTest(name=name), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges(
                    f"list-transition-{name}.md", generated=False
                )
            if ranges is None:
                continue
            literal = source.index(b"body")
            prose = source.index(b"after")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "exact_literal_or_evidence",
            )
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= prose < item["end"]
                ),
                "governed_operative_semantics",
            )

        source = (
            b"paragraph\n"
            b"10. item\n"
            b"    ```text\n"
            b"    body\n"
            b"       ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges(
                "root-paragraph-non-one.md", generated=False
            )
        for needle in (b"```text", b"body", b"after"):
            position = source.index(needle)
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= position < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_deep_list_container_lookup_does_not_rescan_the_stack(self):
        depth = 128
        continuations = 128
        source = (
            b"- " * depth
            + b"item\n"
            + b"lazy continuation\n" * continuations
        )
        real_reversed = reversed
        real_list = list
        real_fullmatch = AI.re.fullmatch
        visits = 0
        copies = 0
        thematic_bytes = 0

        def counted_reversed(value):
            iterator = real_reversed(value)

            def counted_items():
                nonlocal visits
                for item in iterator:
                    visits += 1
                    yield item

            return counted_items()

        def counted_list(value=()):
            nonlocal copies
            copies += 1
            return real_list(value)

        def counted_fullmatch(*args, **kwargs):
            nonlocal thematic_bytes
            thematic_bytes += len(args[1])
            return real_fullmatch(*args, **kwargs)

        with mock.patch.object(
            AI, "_source_blob", return_value=source
        ), mock.patch.object(
            AI, "list", side_effect=counted_list, create=True
        ), mock.patch.object(
            AI.re, "fullmatch", side_effect=counted_fullmatch
        ), mock.patch("builtins.reversed", side_effect=counted_reversed):
            ranges = AI._partition_ranges("deep-list.md", generated=False)
        self.assertEqual(
            {item["classification"] for item in ranges},
            {"governed_operative_semantics"},
        )
        with self.subTest(metric="container-iterations"):
            self.assertLessEqual(visits, depth + continuations)
        with self.subTest(metric="baseline-copies"):
            self.assertLessEqual(copies, 2)
        with self.subTest(metric="thematic-scan-bytes"):
            self.assertLessEqual(thematic_bytes, len(source) * 8)

    def test_nested_template_balance_does_not_rescan_suffixes(self):
        fence_pattern = rb"^( *)(`{3,}|~{3,})([^\r\n]*)"
        real_match = AI.re.match

        def classification(ranges, position):
            return next(
                item["classification"]
                for item in ranges
                if item["start"] <= position < item["end"]
            )

        def counted_partition(source, path):
            marker_scans = 0

            def counted_match(pattern, *args, **kwargs):
                nonlocal marker_scans
                if pattern == fence_pattern:
                    marker_scans += 1
                return real_match(pattern, *args, **kwargs)

            with mock.patch.object(
                AI, "_source_blob", return_value=source
            ), mock.patch.object(AI.re, "match", side_effect=counted_match):
                ranges = AI._partition_ranges(path, generated=False)
            return ranges, marker_scans

        semantic_specimens = {
            "equal-backtick": b"```outer\n```inner\n```\n```\nafter\n",
            "equal-tilde": b"~~~outer\n~~~inner\n~~~\n~~~\nafter\n",
            "inner-longer": b"```outer\n````inner\n````\n```\nafter\n",
            "outer-longer": b"````outer\n```inner\n```\n````\nafter\n",
            "mixed-family": b"```outer\n~~~inner\n~~~\n```\nafter\n",
            "balanced-tail": b"```outer\n```inner\n```\nafter\n",
        }
        for name, source in semantic_specimens.items():
            with self.subTest(name=name):
                with mock.patch.object(
                    AI, "_source_blob", return_value=source
                ):
                    ranges = AI._partition_ranges(name, generated=False)
                self.assertEqual(
                    classification(ranges, source.index(b"inner")),
                    "exact_literal_or_evidence",
                )
                self.assertEqual(
                    classification(ranges, source.index(b"after")),
                    "governed_operative_semantics",
                )

        unmatched = b"```outer\n```inner\n```\n~~~orphan\n"
        with mock.patch.object(AI, "_source_blob", return_value=unmatched):
            with self.assertRaisesRegex(
                AI.Refusal, r"^unterminated Markdown fence: unmatched-tail$"
            ):
                AI._partition_ranges("unmatched-tail", generated=False)

        frozen_transitions = {
            "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/"
            "protocol-type-specialist.md": (2368, 2974, 3297),
            "plugins/hexaemeron/skills/solidity-auditor/SKILL.md": (
                12810,
                13018,
                13019,
            ),
        }
        for path, (opening, close_end, resumed) in frozen_transitions.items():
            with self.subTest(path=path, transition="frozen-template"):
                ranges = AI._partition_ranges(path, generated=False)
                for position in (opening, close_end):
                    self.assertEqual(
                        classification(ranges, position),
                        "exact_literal_or_evidence",
                    )
                self.assertEqual(
                    classification(ranges, resumed),
                    "governed_operative_semantics",
                )

        depth = 64
        cross_indent_parts = [b"- " * depth + b"item\n"]
        for level in range(depth, 0, -1):
            baseline = level * 2
            indent = b" " * baseline
            cross_indent_parts.extend(
                (
                    indent + b"```outer\n",
                    indent + b"```inner\n",
                    indent + b"```\n",
                    indent + b"```\n",
                )
            )
            if level > 1:
                cross_indent_parts.append(
                    b" " * (baseline - 2) + b"# exit\n"
                )
        cross_indent_parts.append(b"after\n")
        cross_indent = b"".join(cross_indent_parts)
        ranges, marker_scans = counted_partition(
            cross_indent, "cross-indent-template-stress.md"
        )
        cursor = 0
        while True:
            cursor = cross_indent.find(b"outer", cursor)
            if cursor < 0:
                break
            self.assertEqual(
                classification(ranges, cursor), "exact_literal_or_evidence"
            )
            cursor += 1
        self.assertEqual(
            classification(ranges, cross_indent.index(b"after")),
            "governed_operative_semantics",
        )
        self.assertLessEqual(
            marker_scans, len(cross_indent.splitlines()) * 3
        )

        templates = 128
        same_indent = (
            b"```outer\n"
            + b"```inner\n```\n" * templates
            + b"```\nafter\n"
        )
        ranges, marker_scans = counted_partition(
            same_indent, "nested-template-stress.md"
        )
        self.assertEqual(
            classification(ranges, same_indent.index(b"inner")),
            "exact_literal_or_evidence",
        )
        self.assertEqual(
            classification(ranges, same_indent.index(b"after")),
            "governed_operative_semantics",
        )
        self.assertLessEqual(
            marker_scans, len(same_indent.splitlines()) * 3
        )

    def test_list_fences_allow_zero_to_three_spaces_after_the_baseline(self):
        specimens = {
            "bullet": (b"- item\n", 2),
            "ordered": (b"10. item\n", 4),
            "nested": (b"- - - item\n", 6),
        }
        for name, (prefix, baseline) in specimens.items():
            for fence in (b"```", b"~~~~"):
                for opening_offset, closing_offset in itertools.product(
                    range(4), repeat=2
                ):
                    source = (
                        prefix
                        + b" " * (baseline + opening_offset)
                        + fence
                        + b"text\n"
                        + b" " * baseline
                        + b"body\n"
                        + b" " * (baseline + closing_offset)
                        + fence
                        + b"\nafter\n"
                    )
                    with self.subTest(
                        name=name,
                        fence=fence,
                        opening_offset=opening_offset,
                        closing_offset=closing_offset,
                    ), mock.patch.object(AI, "_source_blob", return_value=source):
                        ranges = AI._partition_ranges(
                            f"{name}.md", generated=False
                        )
                    literal = source.index(b"body")
                    prose = source.index(b"after")
                    self.assertEqual(
                        next(
                            item["classification"]
                            for item in ranges
                            if item["start"] <= literal < item["end"]
                        ),
                        "exact_literal_or_evidence",
                    )
                    self.assertEqual(
                        next(
                            item["classification"]
                            for item in ranges
                            if item["start"] <= prose < item["end"]
                        ),
                        "governed_operative_semantics",
                    )

    def test_invalid_same_line_marker_prefixes_do_not_open_a_fence(self):
        specimens = {
            "baseline-plus-four": (
                b"-     ```text\n"
                b"      body\n"
                b"      ```\n"
                b"after\n"
            ),
            "baseline-plus-four-tilde": (
                b"+     ~~~text\n"
                b"      body\n"
                b"      ~~~\n"
                b"after\n"
            ),
            "text-before-fence": (
                b"- label ```text\n"
                b"  body\n"
                b"  label ```\n"
                b"after\n"
            ),
            "ten-digit-ordered-marker": (
                b"1234567890. ```text\n"
                b"body\n"
                b"end ```\n"
                b"after\n"
            ),
            "missing-marker-padding": (
                b"-```text\n"
                b"body\n"
                b"-```\n"
                b"after\n"
            ),
        }
        for name, source in specimens.items():
            with self.subTest(name=name), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges(f"{name}.md", generated=False)
            opener = b"~~~text" if b"~~~text" in source else b"```text"
            for needle in (opener, b"body"):
                position = source.index(needle)
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= position < item["end"]
                    ),
                    "governed_operative_semantics",
                )

    def test_same_line_nested_marker_plus_four_does_not_open_a_fence(self):
        source = (
            b"- - item\n"
            b"        ```text\n"
            b"        body\n"
            b"        ```\n"
            b"after\n"
        )
        with mock.patch.object(AI, "_source_blob", return_value=source):
            ranges = AI._partition_ranges("same-line-too-deep.md", generated=False)
        for needle in (b"```text", b"body"):
            position = source.index(needle)
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= position < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_arbitrary_indentation_does_not_create_a_fence(self):
        specimens = {
            "plain-indented-code": (
                b"prose\n"
                b"    ```solidity\n"
                b"    uint256 value = 1;\n"
                b"    ```\n"
                b"after\n"
            ),
            "past-container-allowance": (
                b"- item\n"
                b"      ```solidity\n"
                b"      uint256 value = 1;\n"
                b"      ```\n"
                b"after\n"
            ),
        }
        for name, source in specimens.items():
            with self.subTest(name=name), mock.patch.object(
                AI, "_source_blob", return_value=source
            ):
                ranges = AI._partition_ranges(f"{name}.md", generated=False)
            literal = source.index(b"uint256")
            self.assertEqual(
                next(
                    item["classification"]
                    for item in ranges
                    if item["start"] <= literal < item["end"]
                ),
                "governed_operative_semantics",
            )

    def test_shorter_or_mismatched_fence_inside_long_fence_is_literal(self):
        specimens = {
            "shorter-backtick": b"````text\n```\nstill literal\n````\nafter\n",
            "shorter-backtick-info": b"````text\n```python\nstill literal\n````\nafter\n",
            "mismatched-tilde": b"````text\n~~~\nstill literal\n````\nafter\n",
            "mismatched-tilde-info": b"````text\n~~~text\nstill literal\n````\nafter\n",
        }
        for name, source in specimens.items():
            with self.subTest(name=name):
                with mock.patch.object(AI, "_source_blob", return_value=source):
                    try:
                        ranges = AI._partition_ranges(f"{name}.md", generated=False)
                    except AI.Refusal as exc:
                        self.fail(f"valid outer fence was refused: {exc}")
                literal = source.index(b"still literal")
                prose = source.index(b"after")
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= literal < item["end"]
                    ),
                    "exact_literal_or_evidence",
                )
                self.assertEqual(
                    next(
                        item["classification"]
                        for item in ranges
                        if item["start"] <= prose < item["end"]
                    ),
                    "governed_operative_semantics",
                )

    def test_partition_rebuild_and_command_are_exact(self):
        self.assertEqual(self.partition, AI.build_partition(self.manifest))
        first = command(
            "verify-partition",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--partition",
            str(PARTITION),
        )
        second = command(
            "verify-partition",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--partition",
            str(PARTITION),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)

    def test_overlap_mutation_refuses(self):
        changed = copy.deepcopy(self.partition)
        changed["files"][0]["ranges"][0]["start"] = 1
        with self.assertRaisesRegex(AI.Refusal, "overlap, gap, or are unordered"):
            AI._validate_partition_closure(changed, self.manifest)

    def test_partition_validator_refuses_derivation_drift_without_command_rebuild(self):
        mutations = {
            "source-sha256": lambda value: value["files"][0].__setitem__(
                "source_sha256", "0" * 64
            ),
            "class-total": lambda value: value["totals"].__setitem__(
                "governed_operative_semantics", 0
            ),
            "missing-file": lambda value: value["files"].pop(),
            "duplicate-file": lambda value: value["files"].append(
                copy.deepcopy(value["files"][0])
            ),
            "coherent-reclassification": lambda value: value["files"][0][
                "ranges"
            ][0].__setitem__(
                "classification", "human_only_explanation_or_rationale"
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.partition)
                mutate(changed)
                with self.assertRaisesRegex(
                    AI.Refusal, "partition differs from its source-bound derivation"
                ):
                    try:
                        AI._validate_partition_closure(changed, self.manifest)
                    except TypeError:
                        # Exact parent accepted these mutations through the
                        # one-argument boundary. Keep that parent-red path
                        # executable while exercising the repaired join.
                        AI._validate_partition_closure(changed)


class LoaderGraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)
        cls.profile_by_id = {
            item["id"]: item for item in cls.profiles["profiles"]
        }
        cls.root_by_id = {
            item["id"]: item for item in cls.graph["scenario_roots"]
        }
        cls.host_reach = AI._reachability_by_root(
            cls.graph["roots"], cls.graph["edges"], "active_roots"
        )
        cls.scenario_reach = AI._reachability_by_root(
            cls.graph["scenario_roots"],
            cls.graph["scenario_edges"],
            "active_scenarios",
        )

    def test_exact_graph_counts_are_derived_outputs(self):
        self.assertEqual(
            (
                len(self.graph["roots"]),
                len(self.graph["edges"]),
                len(self.graph["scenario_roots"]),
                len(self.graph["scenario_edges"]),
                len(self.graph["reference_only"]),
            ),
            (19, 332, 2_595, 337, 12),
        )

    def test_independent_oracle_accepts_inventory_bound_shallow_sources(self):
        clear_source_cache()
        try:
            with mock.patch.object(
                sys.modules[__name__], "oracle_source_mode", return_value="inventory"
            ):
                oracle_validate_runtime_edges(self.profiles, self.graph)
        finally:
            clear_source_cache()

    def test_profile_constraints_are_explicit(self):
        constraints = self.graph["constraints"]
        self.assertTrue(constraints["invocation_profiles_are_source_owned"])
        self.assertTrue(constraints["profile_route_product_is_exact"])
        self.assertTrue(constraints["fixed_agent_inputs_are_not_executed"])

    def test_graph_binds_the_profile_fixture_digest(self):
        self.assertEqual(
            self.graph["invocation_profiles_sha256"],
            hashlib.sha256(PROFILES.read_bytes()).hexdigest(),
        )

    def test_every_graph_evidence_span_binds_frozen_bytes(self):
        relations = [
            *self.graph["roots"],
            *self.graph["edges"],
            *self.graph["scenario_roots"],
            *self.graph["scenario_edges"],
            *self.graph["excluded_links"],
        ]
        for relation in relations:
            AI._validate_source_evidence(relation["evidence"], "test evidence")
        for relation in self.graph["reference_only"]:
            AI._validate_source_evidence(
                relation["source_evidence"], "test reference evidence"
            )

    def test_runtime_evidence_exists_only_for_executable_edges(self):
        for edge in [*self.graph["edges"], *self.graph["scenario_edges"]]:
            with self.subTest(edge=edge["id"]):
                self.assertEqual(
                    edge["runtime_evidence"] is not None,
                    edge["load_type"] == "mandatory-executable",
                )

    def test_independent_runtime_semantic_evidence_coverage_is_closed(self):
        oracle_validate_runtime_edges(self.profiles, self.graph)
        self.assertEqual(
            sum(
                edge["runtime_evidence"] is not None
                for edge in self.graph["scenario_edges"]
            ),
            12,
        )
        self.assertEqual(
            sum(
                edge["runtime_evidence"] is not None
                for edge in self.graph["edges"]
            ),
            11,
        )
        self.assertEqual(
            sum(ORACLE_GRAPH_RUNTIME_EVIDENCE_COUNTS.values()), 23
        )

    def test_graph_validator_does_not_trust_generator_runtime_metadata(self):
        target = "plugins/hermes/skills/hermes/references/gas-rule-corpus.json"
        donor = (
            "plugins/hermes/skills/hermes/references/"
            "gas-rule-corpus.schema.json"
        )
        metadata = copy.deepcopy(AI._structured_metadata())
        metadata[target]["runtime_path"] = metadata[donor]["runtime_path"]
        metadata[target]["runtime_needle"] = metadata[donor]["runtime_needle"]
        with mock.patch.object(AI, "_structured_metadata", return_value=metadata):
            with self.assertRaisesRegex(
                AI.Refusal, "scenario runtime semantic anchor drift"
            ):
                AI.build_loader_graph(self.manifest, self.profiles)

    def test_graph_validator_refuses_all_scenario_runtime_target_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.graph["scenario_edges"], "target"
        )
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["scenario_edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AI.Refusal, "scenario runtime semantic anchor drift"
                ):
                    AI._validate_complete_scenarios(changed, self.profiles)

    def test_graph_validator_refuses_all_host_runtime_target_rebindings(self):
        specimens = cross_target_runtime_specimens(self.graph["edges"], "target")
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AI.Refusal, "host runtime semantic anchor drift"
                ):
                    AI._validate_complete_scenarios(changed, self.profiles)

    def test_independent_oracle_refuses_all_scenario_runtime_rebindings(self):
        specimens = cross_target_runtime_specimens(
            self.graph["scenario_edges"], "target"
        )
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["scenario_edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AssertionError, "independent scenario runtime anchor mismatch"
                ):
                    oracle_validate_runtime_edges(self.profiles, changed)

    def test_independent_oracle_refuses_all_host_runtime_rebindings(self):
        specimens = cross_target_runtime_specimens(self.graph["edges"], "target")
        for target, (index, donor_target, donor_runtime) in specimens.items():
            with self.subTest(target=target, donor=donor_target):
                changed = copy.deepcopy(self.graph)
                changed["edges"][index]["runtime_evidence"] = donor_runtime
                with self.assertRaisesRegex(
                    AssertionError, "independent host runtime anchor mismatch"
                ):
                    oracle_validate_runtime_edges(self.profiles, changed)

    def test_host_root_identities_are_exact(self):
        self.assertEqual(
            {item["id"] for item in self.graph["roots"]},
            {"repository", "agent-skills"}
            | {f"standalone:{name}" for name in {
                AI._plugin(path) for path in AI.SELECTABLE_SKILL_PATHS.values()
            }},
        )

    def test_host_edge_scopes_are_closed(self):
        known = {item["id"] for item in self.graph["roots"]}
        for edge in self.graph["edges"]:
            self.assertEqual(edge["active_roots"], sorted(set(edge["active_roots"])))
            self.assertTrue(set(edge["active_roots"]) <= known)
            self.assertNotIn("*", edge["active_roots"])

    def test_manifest_host_reachability_is_graph_derived(self):
        for document in self.manifest["documents"]:
            self.assertEqual(
                set(document["loader_roots"]),
                self.host_reach.get(document["path"], set()),
            )

    def test_manifest_scenario_reachability_is_graph_derived(self):
        for document in self.manifest["documents"]:
            self.assertEqual(
                set(document["scenario_reachability"]),
                self.scenario_reach.get(document["path"], set()),
            )

    def test_scenario_denominator_is_exactly_5n(self):
        self.assertEqual(
            len(self.graph["scenario_roots"]),
            5 * self.profiles["totals"]["normalized_profiles"],
        )

    def test_scenario_route_totals_are_2n_2n_n(self):
        counts = {
            route: sum(root["route"] == route for root in self.graph["scenario_roots"])
            for route in ("repository", "agent-skills", "standalone")
        }
        self.assertEqual(
            counts,
            {"repository": 1_038, "agent-skills": 1_038, "standalone": 519},
        )

    def test_each_profile_has_five_scenario_roots(self):
        counts = {identifier: 0 for identifier in self.profile_by_id}
        for root in self.graph["scenario_roots"]:
            counts[root["profile_id"]] += 1
        self.assertEqual(set(counts.values()), {5})

    def test_route_credential_matrix_is_exact(self):
        for profile_id in self.profile_by_id:
            rows = [
                (root["route"], root["credential"])
                for root in self.graph["scenario_roots"]
                if root["profile_id"] == profile_id
            ]
            self.assertEqual(
                set(rows),
                {
                    ("repository", "absent"),
                    ("repository", "github-contributor"),
                    ("agent-skills", "absent"),
                    ("agent-skills", "github-contributor"),
                    ("standalone", "absent"),
                },
            )

    def test_route_skill_base_product_has_93_members(self):
        self.assertEqual(
            len({root["base_scenario"] for root in self.graph["scenario_roots"]}),
            93,
        )

    def test_root_conditions_bind_profile_and_optional_credential(self):
        for root in self.graph["scenario_roots"]:
            expected = [f"profile:{root['profile_id']}"]
            if root["credential"] == "github-contributor":
                expected.append("credential:github-contributor")
            self.assertEqual(root["conditions"], sorted(expected))
            self.assertEqual(root["mode"], "conditional")

    def test_each_scenario_starts_at_its_real_host_entry(self):
        for root in self.graph["scenario_roots"]:
            plugin = AI._plugin(AI.SELECTABLE_SKILL_PATHS[root["selected_skill"]])
            expected = {
                "repository": "AGENTS.md",
                "agent-skills": ".agents/skills/promise-machine/SKILL.md",
                "standalone": f"plugins/{plugin}/AGENTS.md",
            }[root["route"]]
            self.assertEqual(root["node"], expected)

    def test_each_reached_union_exactly_matches_its_profile_and_route(self):
        for identifier, root in self.root_by_id.items():
            expected = AI._scenario_expected_documents(
                root["route"],
                root["credential"],
                self.profile_by_id[root["profile_id"]],
            )
            observed = {
                path for path, scope in self.scenario_reach.items() if identifier in scope
            }
            self.assertEqual(observed, expected)

    def test_scenario_edge_scopes_are_sorted_closed_and_nonempty(self):
        known = set(self.root_by_id)
        for edge in self.graph["scenario_edges"]:
            scope = edge["active_scenarios"]
            self.assertTrue(scope)
            self.assertEqual(scope, sorted(set(scope)))
            self.assertNotIn("*", scope)
            self.assertTrue(set(scope) <= known)

    def test_edge_base_scopes_are_derived_from_active_roots(self):
        for edge in self.graph["scenario_edges"]:
            self.assertEqual(
                edge["eligible_base_scenarios"],
                sorted(
                    {
                        self.root_by_id[identifier]["base_scenario"]
                        for identifier in edge["active_scenarios"]
                    }
                ),
            )

    def test_every_scenario_edge_has_a_realisable_witness(self):
        for edge in self.graph["scenario_edges"]:
            for identifier in edge["active_scenarios"]:
                self.assertIn(identifier, self.scenario_reach[edge["source"]])
                self.assertIn(identifier, self.scenario_reach[edge["target"]])

    def test_profile_scopes_replace_edge_minimised_conditions(self):
        self.assertTrue(
            all(edge["condition"] is None for edge in self.graph["scenario_edges"])
        )
        self.assertTrue(
            all(root["conditions"][0].startswith(("credential:", "profile:")) for root in self.graph["scenario_roots"])
        )

    def test_reference_only_ledger_is_exact(self):
        expected = {
            path
            for path, row in AI._structured_metadata().items()
            if row["load_semantics"] == "reference-only"
        } | set(AI.REFERENCE_ONLY_MARKDOWN)
        self.assertEqual({row["path"] for row in self.graph["reference_only"]}, expected)

    def test_reference_only_documents_have_zero_reachability(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        for row in self.graph["reference_only"]:
            document = documents[row["path"]]
            self.assertEqual(document["loader_roots"], [])
            self.assertEqual(document["scenario_reachability"], [])

    def test_fixed_agent_inputs_have_nonexecuting_edges(self):
        for path in AI._fixed_agent_metadata():
            incoming = [
                edge for edge in self.graph["scenario_edges"] if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(
                all(
                    edge["kind"] == "fixed-agent-input"
                    and edge["load_type"] == "agent-or-prompt"
                    and edge["runtime_evidence"] is None
                    for edge in incoming
                )
            )

    def test_fixed_input_scopes_equal_profile_declarations(self):
        for path in AI._fixed_agent_metadata():
            expected = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if path in self.profile_by_id[root["profile_id"]]["required_documents"]
            }
            self.assertEqual(self.scenario_reach[path], expected)

    def test_mandatory_inputs_keep_executable_semantics(self):
        for path, metadata in AI._structured_metadata().items():
            if metadata["load_semantics"] != "mandatory-executable":
                continue
            incoming = [
                edge for edge in self.graph["scenario_edges"] if edge["target"] == path
            ]
            self.assertTrue(incoming)
            self.assertTrue(
                all(
                    edge["kind"] == "mandatory-executable"
                    and edge["runtime_evidence"] is not None
                    for edge in incoming
                )
            )

    def test_mandatory_input_scopes_equal_profile_declarations(self):
        for path, metadata in AI._structured_metadata().items():
            if metadata["load_semantics"] != "mandatory-executable":
                continue
            expected = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if path in self.profile_by_id[root["profile_id"]]["required_documents"]
            }
            self.assertEqual(self.scenario_reach[path], expected)

    def test_synkrisis_rule_runtime_has_two_exclusive_operation_spans(self):
        path = "plugins/synkrisis/references/rules-v1.json"
        spans = {
            edge["runtime_evidence"]["span_sha256"]
            for edge in self.graph["scenario_edges"]
            if edge["target"] == path
        }
        expected = {
            AI._evidence(
                AI._structured_metadata()[path]["runtime_path"], needle
            )["span_sha256"]
            for needle in AI.SYNKRISIS_RULE_RUNTIME_NEEDLES.values()
        }
        self.assertEqual(spans, expected)

    def test_every_declared_worker_is_reached_in_all_five_routes(self):
        for profile in self.profiles["profiles"]:
            roots = {
                root["id"]
                for root in self.graph["scenario_roots"]
                if root["profile_id"] == profile["id"]
            }
            for worker in profile["worker_prompts"]:
                self.assertLessEqual(roots, self.scenario_reach[worker])

    def test_kronos_is_bounded_to_one_rank_or_one_dispatch_iteration(self):
        profiles = [
            row for row in self.profiles["profiles"] if row["selected_skill"] == "kronos"
        ]
        self.assertEqual(len(profiles), 26)
        self.assertEqual(sum("rank-only" in row["id"] for row in profiles), 2)
        self.assertTrue(
            all("rank-only" in row["id"] or "dispatch-" in row["id"] for row in profiles)
        )

    def test_graph_rebuild_is_exact(self):
        self.assertEqual(
            self.graph,
            AI.build_loader_graph(self.manifest, self.profiles),
        )

    def test_graph_validator_refuses_derivation_drift_without_command_rebuild(self):
        mutations = {
            "host-scope": lambda value: value["edges"][0].__setitem__(
                "active_roots", []
            ),
            "constraint": lambda value: value["constraints"].__setitem__(
                "profile_route_product_is_exact", False
            ),
            "excluded-link": lambda value: value["excluded_links"].pop(),
            "manifest-identity": lambda value: value.__setitem__(
                "manifest_sha256", "0" * 64
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.graph)
                mutate(changed)
                with self.assertRaisesRegex(
                    AI.Refusal, "loader graph differs from its source-bound derivation"
                ):
                    validator = getattr(AI, "_validate_loader_graph", None)
                    if validator is None:
                        # Exact parent exposed only the scenario-fragment
                        # validator, which accepted these whole-graph drifts.
                        AI._validate_complete_scenarios(changed, self.profiles)
                    else:
                        validator(changed, self.manifest, self.profiles)

    def test_verify_loader_is_read_only_and_repeatable(self):
        arguments = (
            "verify-loader",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--graph",
            str(GRAPH),
        )
        first = command(*arguments)
        second = command(*arguments)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


class FollowOnAudit18ParentGuardTests(unittest.TestCase):
    """Guards that stay assertion-red on exact parent fa48ff7a5881."""

    PIN = ".python-version"
    PIN_SHA256 = "3a55324cbeddc91df012407d051dad08c88624c95a82fbdb856728729fbd14ab"
    EXPECTED_PROFILES = {
        "anamnesis:demo-or-rebuild",
        "anamnesis:ordinary",
        "berean:ordinary",
        "brevitas:ordinary",
        "hermes:gas-operation",
        "lemma:changed-or-unexpected",
        "lemma:ordinary",
        "probitas:add-venue",
        "synkrisis:cohort-or-render",
        "synkrisis:diagnose",
        "synkrisis:verify",
    }

    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)

    @staticmethod
    def reseal_profiles(record: dict) -> str:
        digest = hashlib.sha256(canonical(record["profiles"])).hexdigest()
        record["projection_sha256"] = digest
        return digest

    @classmethod
    def independent_profile_scope(cls, profiles: list[dict]) -> None:
        expected = {
            row["id"]
            for row in oracle_profiles()
            if cls.PIN in row["required_documents"]
        }
        observed = {
            row.get("id")
            for row in profiles
            if isinstance(row, dict)
            and isinstance(row.get("required_documents"), list)
            and cls.PIN in row["required_documents"]
        }
        if expected != cls.EXPECTED_PROFILES or observed != expected:
            raise AssertionError("independent Python pin profile scope mismatch")

    @classmethod
    def independent_manifest_pin(cls, manifest: dict) -> None:
        documents = manifest.get("documents")
        if not isinstance(documents, list):
            raise AssertionError("independent Python pin manifest is malformed")
        matches = [row for row in documents if row.get("path") == cls.PIN]
        if len(matches) != 1:
            raise AssertionError("independent Python pin manifest identity mismatch")
        pin = matches[0]
        expected_evidence = oracle_span(
            "AGENTS.md",
            "Every `python3` command below means the exact interpreter recorded in\n"
            "[`.python-version`](.python-version).",
        )
        expected = {
            "admission_kind": "fixed-agent-input",
            "authority_tier": "fixed_input",
            "bytes": 7,
            "canonical_content_path": cls.PIN,
            "canonical_owner": "AGENTS.md",
            "document_class": "fixed_input",
            "external_runtime_owner": None,
            "load_semantics": "agent-or-prompt",
            "logical_document": "suite-runtime",
            "path": cls.PIN,
            "runtime_evidence": None,
            "sha256": cls.PIN_SHA256,
            "source_evidence": expected_evidence,
        }
        if any(pin.get(field) != value for field, value in expected.items()):
            raise AssertionError("independent Python pin manifest identity mismatch")
        if len(pin.get("scenario_reachability", [])) != 55:
            raise AssertionError("independent Python pin manifest route scope mismatch")

    @classmethod
    def independent_route_scope(cls, graph: dict) -> None:
        expected: set[str] = set()
        for profile_id in cls.EXPECTED_PROFILES:
            skill = profile_id.split(":", 1)[0]
            plugin = ORACLE_SKILL_PATHS[skill].split("/")[1]
            for route, credentials in (
                ("repository", ("absent", "github-contributor")),
                ("agent-skills", ("absent", "github-contributor")),
                ("standalone", ("absent",)),
            ):
                base = (
                    f"standalone:{plugin}:skill:{skill}"
                    if route == "standalone"
                    else f"{route}:skill:{skill}"
                )
                for credential in credentials:
                    expected.add(
                        f"{base}:profile:{profile_id}:credential:{credential}"
                    )
        roots = {
            row.get("id")
            for row in graph.get("scenario_roots", [])
            if row.get("profile_id") in cls.EXPECTED_PROFILES
        }
        incoming = [
            edge
            for edge in graph.get("scenario_edges", [])
            if edge.get("target") == cls.PIN
        ]
        active = {
            identifier
            for edge in incoming
            for identifier in edge.get("active_scenarios", [])
        }
        if roots != expected or active != expected or len(expected) != 55:
            raise AssertionError("independent Python pin route scope mismatch")
        if not incoming or any(
            edge.get("kind") != "fixed-agent-input"
            or edge.get("load_type") != "agent-or-prompt"
            or edge.get("runtime_evidence") is not None
            for edge in incoming
        ):
            raise AssertionError("independent Python pin execution semantics mismatch")

    def test_suite_runtime_pin_is_an_exact_nonexecuting_fixed_input(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        pin = documents[self.PIN]
        self.assertEqual(pin["document_class"], "fixed_input")
        self.assertEqual(pin["admission_kind"], "fixed-agent-input")
        self.assertEqual(pin["load_semantics"], "agent-or-prompt")
        self.assertEqual((pin["bytes"], pin["sha256"]), (7, self.PIN_SHA256))
        self.assertIsNone(pin["runtime_evidence"])
        self.independent_manifest_pin(self.manifest)

    def test_suite_runtime_pin_scope_is_exact_across_all_five_routes(self):
        profiles = {
            row["id"]
            for row in self.profiles["profiles"]
            if self.PIN in row["required_documents"]
        }
        self.assertEqual(profiles, self.EXPECTED_PROFILES)
        roots = {
            row["id"]
            for row in self.graph["scenario_roots"]
            if row["profile_id"] in profiles
        }
        self.assertEqual(len(roots), 55)
        incoming = [
            edge for edge in self.graph["scenario_edges"] if edge["target"] == self.PIN
        ]
        self.assertTrue(incoming)
        self.assertEqual(
            {root for edge in incoming for root in edge["active_scenarios"]}, roots
        )
        self.assertTrue(
            all(
                edge["kind"] == "fixed-agent-input"
                and edge["load_type"] == "agent-or-prompt"
                and edge["runtime_evidence"] is None
                for edge in incoming
            )
        )
        self.independent_profile_scope(self.profiles["profiles"])
        self.independent_route_scope(self.graph)

    def test_every_allowed_profile_refuses_pin_omission(self):
        for profile_id in sorted(self.EXPECTED_PROFILES):
            with self.subTest(profile_id=profile_id):
                changed = copy.deepcopy(self.profiles)
                profile = next(
                    row for row in changed["profiles"] if row["id"] == profile_id
                )
                profile["required_documents"].remove(self.PIN)
                profile["fixed_inputs"] = [
                    row for row in profile["fixed_inputs"] if row["path"] != self.PIN
                ]
                profile["source_evidence"] = [
                    row
                    for row in profile["source_evidence"]
                    if row["obligation"] != self.PIN
                ]
                digest = self.reseal_profiles(changed)
                with mock.patch.object(
                    AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest
                ):
                    with self.assertRaisesRegex(
                        AI.Refusal, "Python pin scope drift"
                    ):
                        AI._validate_invocation_profiles(changed)
                with self.assertRaisesRegex(
                    AssertionError, "independent Python pin profile scope mismatch"
                ):
                    self.independent_profile_scope(changed["profiles"])

    def test_every_allowed_profile_refuses_pin_demotion(self):
        for profile_id in sorted(self.EXPECTED_PROFILES):
            with self.subTest(profile_id=profile_id):
                changed = copy.deepcopy(self.profiles)
                profile = next(
                    row for row in changed["profiles"] if row["id"] == profile_id
                )
                fixed = next(
                    row for row in profile["fixed_inputs"] if row["path"] == self.PIN
                )
                fixed["load_semantics"] = "reference-only"
                digest = self.reseal_profiles(changed)
                with mock.patch.object(
                    AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest
                ):
                    with self.assertRaisesRegex(
                        AI.Refusal, "fixed input semantics drift"
                    ):
                        AI._validate_invocation_profiles(changed)
                expected = next(
                    row for row in oracle_profiles() if row["id"] == profile_id
                )
                observed = {
                    key: value
                    for key, value in profile.items()
                    if key != "source_evidence"
                }
                self.assertNotEqual(observed, expected)

    def test_every_excluded_profile_has_no_pin_semantic_anchor(self):
        excluded = [
            row
            for row in self.profiles["profiles"]
            if row["id"] not in self.EXPECTED_PROFILES
        ]
        self.assertEqual(len(excluded), 508)
        for profile in excluded:
            with self.subTest(profile_id=profile["id"]):
                with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
                    AI._python_pin_profile_anchor(
                        profile["selected_skill"], tuple(profile["branch_state"])
                    )
                with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
                    AI._validation_python_pin_anchor(profile)
                with self.assertRaisesRegex(AssertionError, "relation is unowned"):
                    oracle_python_pin_anchor(profile)

    def test_synchronised_excluded_profile_pin_addition_refuses(self):
        changed = copy.deepcopy(self.profiles)
        profile = next(
            row
            for row in changed["profiles"]
            if row["id"] == "anamnesis:frontier-gate"
        )
        donor = next(
            row
            for row in changed["profiles"]
            if row["id"] == "anamnesis:ordinary"
        )
        profile["required_documents"].append(self.PIN)
        profile["required_documents"].sort()
        profile["fixed_inputs"].append(
            {"path": self.PIN, "load_semantics": "agent-or-prompt"}
        )
        profile["fixed_inputs"].sort(key=lambda row: row["path"])
        evidence = copy.deepcopy(
            next(
                row
                for row in donor["source_evidence"]
                if row["obligation"] == self.PIN
            )
        )
        profile["source_evidence"].append(evidence)
        profile["source_evidence"].sort(key=lambda row: row["obligation"])
        digest = self.reseal_profiles(changed)
        with mock.patch.object(AI, "EXPECTED_PROFILE_PROJECTION_SHA256", digest):
            with self.assertRaisesRegex(AI.Refusal, "relation is unowned"):
                AI._validate_invocation_profiles(changed)
        with self.assertRaisesRegex(
            AssertionError, "independent Python pin profile scope mismatch"
        ):
            self.independent_profile_scope(changed["profiles"])

    def test_pin_manifest_bytes_digest_execution_and_source_weakening_refuse(self):
        executable = next(
            row["runtime_evidence"]
            for row in self.manifest["documents"]
            if row["runtime_evidence"] is not None
        )

        def pin_in(manifest: dict) -> dict:
            return next(
                row for row in manifest["documents"] if row["path"] == self.PIN
            )

        mutations = {
            "bytes": lambda pin: pin.__setitem__("bytes", 6),
            "digest": lambda pin: pin.__setitem__("sha256", "0" * 64),
            "executable": lambda pin: pin.update(
                {
                    "load_semantics": "mandatory-executable",
                    "runtime_evidence": copy.deepcopy(executable),
                }
            ),
            "weak-source-span": lambda pin: pin.__setitem__(
                "source_evidence", oracle_span("AGENTS.md", ".python-version")
            ),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                changed = copy.deepcopy(self.manifest)
                mutate(pin_in(changed))
                with self.assertRaises(AI.Refusal):
                    AI._validate_manifest_shape(changed, self.profiles)
                with self.assertRaisesRegex(
                    AssertionError, "independent Python pin manifest identity mismatch"
                ):
                    self.independent_manifest_pin(changed)
                if label == "weak-source-span":
                    with self.assertRaisesRegex(
                        AssertionError, "independent manifest source anchor mismatch"
                    ):
                        oracle_validate_manifest_semantic_anchors(changed)

    def test_pin_graph_refuses_executable_fiction(self):
        changed = copy.deepcopy(self.graph)
        pin_edge = next(
            edge
            for edge in changed["scenario_edges"]
            if edge["target"] == self.PIN
        )
        runtime = next(
            edge["runtime_evidence"]
            for edge in changed["scenario_edges"]
            if edge["runtime_evidence"] is not None
        )
        pin_edge["load_type"] = "mandatory-executable"
        pin_edge["runtime_evidence"] = copy.deepcopy(runtime)
        with self.assertRaises(AI.Refusal):
            AI._validate_complete_scenarios(changed, self.profiles)
        with self.assertRaisesRegex(
            AssertionError, "independent Python pin execution semantics mismatch"
        ):
            self.independent_route_scope(changed)

    def test_each_pin_route_variant_refuses_deletion(self):
        roots = [
            row
            for row in self.graph["scenario_roots"]
            if row["profile_id"] == "anamnesis:ordinary"
        ]
        self.assertEqual(
            {(row["route"], row["credential"]) for row in roots},
            {
                ("repository", "absent"),
                ("repository", "github-contributor"),
                ("agent-skills", "absent"),
                ("agent-skills", "github-contributor"),
                ("standalone", "absent"),
            },
        )
        for removed in roots:
            with self.subTest(
                route=removed["route"], credential=removed["credential"]
            ):
                changed = copy.deepcopy(self.graph)
                identifier = removed["id"]
                changed["scenario_roots"] = [
                    row
                    for row in changed["scenario_roots"]
                    if row["id"] != identifier
                ]
                for edge in changed["scenario_edges"]:
                    if identifier in edge["active_scenarios"]:
                        edge["active_scenarios"].remove(identifier)
                with self.assertRaisesRegex(
                    AI.Refusal, "scenario root denominator or identity drift"
                ):
                    AI._validate_complete_scenarios(changed, self.profiles)
                with self.assertRaisesRegex(
                    AssertionError, "independent Python pin route scope mismatch"
                ):
                    self.independent_route_scope(changed)


class HoldoutSealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.profiles = load(PROFILES)
        cls.graph = load(GRAPH)
        cls.cohorts = load(COHORTS)
        cls.seal = load(SEAL)

    def test_cohorts_are_disjoint_and_meet_byte_gates(self):
        development = set(self.cohorts["development"]["paths"])
        holdout = set(self.cohorts["holdout"]["paths"])
        self.assertFalse(development & holdout)
        self.assertGreaterEqual(
            float(self.cohorts["development"]["unique_byte_ratio"]), 0.50
        )
        self.assertGreaterEqual(
            float(self.cohorts["holdout"]["unique_byte_ratio"]), 0.20
        )
        self.assertGreaterEqual(len(self.cohorts["development"]["logical_skills"]), 12)
        self.assertEqual(
            self.cohorts["holdout"]["logical_skills"],
            ["alexandria", "fizz", "phylax", "probitas", "sapheneia"],
        )
        self.assertEqual(len(self.cohorts["holdout"]["paths"]), 31)
        self.assertEqual(self.cohorts["holdout"]["unique_bytes"], 363_804)
        self.assertEqual(self.cohorts["holdout"]["unique_byte_ratio"], "0.200002")
        self.assertEqual(self.cohorts["development"]["unique_bytes"], 1_455_202)
        self.assertEqual(
            self.cohorts["development"]["unique_byte_ratio"], "0.799998"
        )
        self.assertEqual(self.cohorts["selection"]["seed"], AI.SELECTION_SEED)

    def test_development_covers_roots_tiers_constructs_and_deciles(self):
        development = set(self.cohorts["development"]["paths"])
        self.assertIn("AGENTS.md", development)
        self.assertIn("PROMISE_MACHINE.md", development)
        self.assertIn(".agents/skills/promise-machine/SKILL.md", development)
        self.assertEqual(self.cohorts["development"]["size_deciles"], list(range(10)))
        self.assertEqual(
            set(self.cohorts["development"]["constructs"]),
            {
                "authority",
                "cross-document",
                "exact-literal",
                "exception",
                "failure",
                "negation",
                "order",
                "recovery",
                "refusal",
                "scope",
                "unknown",
            },
        )
        self.assertEqual(
            set(self.cohorts["development"]["authority_tiers"]),
            {
                item["authority_tier"]
                for item in self.manifest["documents"]
                if item["path"] == item["canonical_content_path"]
            },
        )
        self.assertEqual(
            set(self.cohorts["development"]["document_classes"]),
            set(AI.EXPECTED_COUNTS),
        )

    def test_sealed_envelope_has_required_classes_without_answers(self):
        envelope = self.seal["closed_future_case_envelope"]
        self.assertEqual(len(envelope["slots"]), 16)
        self.assertEqual(
            {slot["semantic_class"] for slot in envelope["slots"]},
            {"authority", "failure", "recovery", "exact-literal", "cross-document"},
        )
        forbidden = set(envelope["forbidden_until_open"])
        self.assertEqual(
            forbidden, {"prompt", "expected_answer", "scorer_key", "model_output"}
        )
        self.assertTrue(all(not forbidden & set(slot) for slot in envelope["slots"]))
        self.assertIs(self.seal["opened"], False)

    def test_commitments_recompute(self):
        membership = self.seal["membership"]
        envelope = self.seal["closed_future_case_envelope"]
        self.assertEqual(
            self.seal["membership_sha256"],
            hashlib.sha256(canonical(membership)).hexdigest(),
        )
        self.assertEqual(
            self.seal["case_envelope_sha256"],
            hashlib.sha256(canonical(envelope)).hexdigest(),
        )
        body = dict(self.seal)
        commitment = body.pop("commitment_sha256")
        self.assertEqual(commitment, hashlib.sha256(canonical(body)).hexdigest())

    def test_seal_binds_exact_profile_and_graph_identities(self):
        expected = {
            "invocation_profiles_sha256": hashlib.sha256(
                canonical(self.profiles)
            ).hexdigest(),
            "loader_graph_sha256": hashlib.sha256(canonical(self.graph)).hexdigest(),
        }
        for field, digest in expected.items():
            with self.subTest(field=field):
                self.assertEqual(self.seal.get(field), digest)

    def test_resealed_profile_or_graph_identity_mismatch_refuses(self):
        for field in ("invocation_profiles_sha256", "loader_graph_sha256"):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.seal)
                changed[field] = "0" * 64
                body = dict(changed)
                body.pop("commitment_sha256")
                changed["commitment_sha256"] = hashlib.sha256(
                    canonical(body)
                ).hexdigest()
                with self.assertRaisesRegex(AI.Refusal, "input identity"):
                    AI._validate_holdout_seal(
                        changed,
                        self.manifest,
                        self.cohorts,
                        self.profiles,
                        self.graph,
                    )

    def reseal(self, changed):
        body = dict(changed)
        body.pop("commitment_sha256", None)
        changed["commitment_sha256"] = hashlib.sha256(
            canonical(body)
        ).hexdigest()

    def validate_changed_seal(self, changed):
        AI._validate_holdout_seal(
            changed,
            self.manifest,
            self.cohorts,
            self.profiles,
            self.graph,
        )

    def test_coherently_resealed_membership_drift_refuses(self):
        changed = copy.deepcopy(self.seal)
        changed["membership"]["paths"] = changed["membership"]["paths"][1:]
        changed["membership_sha256"] = hashlib.sha256(
            canonical(changed["membership"])
        ).hexdigest()
        self.reseal(changed)
        with self.assertRaisesRegex(AI.Refusal, "membership drift"):
            self.validate_changed_seal(changed)

    def test_coherently_resealed_upstream_cohort_drift_refuses(self):
        cohorts = copy.deepcopy(self.cohorts)
        cohorts["holdout"]["logical_skills"] = cohorts["holdout"][
            "logical_skills"
        ][1:]
        cohorts["holdout"]["paths"] = cohorts["holdout"]["paths"][1:]
        replacement_skill = cohorts["holdout"]["logical_skills"][0]
        for slot in cohorts["holdout"]["case_slots"]:
            slot["logical_skill"] = replacement_skill

        changed = copy.deepcopy(self.seal)
        changed["cohorts_sha256"] = hashlib.sha256(canonical(cohorts)).hexdigest()
        changed["membership"] = {
            "logical_skills": cohorts["holdout"]["logical_skills"],
            "paths": cohorts["holdout"]["paths"],
        }
        changed["membership_sha256"] = hashlib.sha256(
            canonical(changed["membership"])
        ).hexdigest()
        changed["closed_future_case_envelope"] = {
            "slots": cohorts["holdout"]["case_slots"],
            "forbidden_until_open": [
                "prompt",
                "expected_answer",
                "scorer_key",
                "model_output",
            ],
        }
        changed["case_envelope_sha256"] = hashlib.sha256(
            canonical(changed["closed_future_case_envelope"])
        ).hexdigest()
        self.reseal(changed)

        with self.assertRaisesRegex(
            AI.Refusal, "cohorts differ from their source-bound derivation"
        ):
            AI._validate_holdout_seal(
                changed,
                self.manifest,
                cohorts,
                self.profiles,
                self.graph,
            )

    def test_stale_membership_digest_refuses_after_outer_reseal(self):
        changed = copy.deepcopy(self.seal)
        changed["membership_sha256"] = "0" * 64
        self.reseal(changed)
        with self.assertRaisesRegex(AI.Refusal, "membership digest drift"):
            self.validate_changed_seal(changed)

    def test_coherently_resealed_case_envelope_drift_refuses(self):
        for mutation in ("slot", "forbidden"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.seal)
                envelope = changed["closed_future_case_envelope"]
                if mutation == "slot":
                    envelope["slots"][0]["logical_skill"] = "sapheneia"
                else:
                    envelope["forbidden_until_open"].remove("expected_answer")
                changed["case_envelope_sha256"] = hashlib.sha256(
                    canonical(envelope)
                ).hexdigest()
                self.reseal(changed)
                with self.assertRaisesRegex(AI.Refusal, "case envelope drift"):
                    self.validate_changed_seal(changed)

    def test_stale_case_envelope_digest_refuses_after_outer_reseal(self):
        changed = copy.deepcopy(self.seal)
        changed["case_envelope_sha256"] = "0" * 64
        self.reseal(changed)
        with self.assertRaisesRegex(AI.Refusal, "case envelope digest drift"):
            self.validate_changed_seal(changed)

    def test_resealed_source_identity_drift_refuses(self):
        for field, value in (
            ("schema", "wildcat-instruction-architecture-holdout-seal/v2"),
            ("source_ref", "0" * 40),
            ("selection_seed", "attacker-seed"),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.seal)
                changed[field] = value
                self.reseal(changed)
                with self.assertRaisesRegex(AI.Refusal, "source identity drift"):
                    self.validate_changed_seal(changed)

    def test_resealed_outer_field_set_drift_refuses(self):
        for mutation in ("missing", "extra"):
            with self.subTest(mutation=mutation):
                changed = copy.deepcopy(self.seal)
                if mutation == "missing":
                    changed.pop("membership_sha256")
                else:
                    changed["unbound_extension"] = "accepted by the exact parent"
                self.reseal(changed)
                with self.assertRaisesRegex(AI.Refusal, "non-closed field set"):
                    self.validate_changed_seal(changed)

    def test_non_object_seal_refuses(self):
        with self.assertRaisesRegex(AI.Refusal, "must be an object"):
            self.validate_changed_seal([])

    def test_seed_replay_and_command_are_exact(self):
        rebuilt = AI.build_cohorts(self.manifest)
        self.assertEqual(rebuilt, self.cohorts)
        self.assertEqual(
            AI.build_holdout_seal(
                self.manifest, rebuilt, self.profiles, self.graph
            ),
            self.seal,
        )
        first = command(
            "verify-seal",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--cohorts",
            str(COHORTS),
            "--seal",
            str(SEAL),
        )
        second = command(
            "verify-seal",
            "--profiles",
            str(PROFILES),
            "--manifest",
            str(MANIFEST),
            "--cohorts",
            str(COHORTS),
            "--seal",
            str(SEAL),
        )
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)


class DevelopmentFixtureMixin:
    @classmethod
    def setUpClass(cls):
        cls.manifest = load(MANIFEST)
        cls.graph = load(GRAPH)
        cls.cohorts = load(COHORTS)
        cls.cases = load(DEVELOPMENT_CASES)
        cls.report = load(DEVELOPMENT_REPORT)
        cls.controls = {arm: load(path) for arm, path in DEVELOPMENT_CONTROLS.items()}
        cls.results = {arm: load(path) for arm, path in DEVELOPMENT_RESULTS.items()}

    def validate_adapter_result(self, arm, record):
        validator = AI._validate_adapter_results
        if validator.__code__.co_argcount == 1:
            return validator(record)
        return validator(
            record,
            self.cases,
            self.manifest,
            self.graph,
            self.controls[arm],
        )


class NeutralSchemaTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_schema_covers_every_neutral_record_and_closes_objects(self):
        schema = load(DEVELOPMENT_SCHEMA)
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(
            {item["$ref"] for item in schema["oneOf"]},
            {
                "#/$defs/adapterResults",
                "#/$defs/aggregateReport",
                "#/$defs/casesFile",
                "#/$defs/controlFile",
                "#/$defs/controlSnapshotFile",
                "#/$defs/developmentInventory",
                "#/$defs/mutationsFile",
                "#/$defs/mutationResultsFile",
                "#/$defs/prompt",
                "#/$defs/resourceFile",
                "#/$defs/score",
            },
        )
        objects = [
            value
            for value in schema["$defs"].values()
            if value.get("type") == "object"
        ]
        self.assertTrue(objects)
        self.assertTrue(all(value.get("additionalProperties") is False for value in objects))

    def test_every_committed_record_is_canonical_closed_json(self):
        paths = [
            *DEVELOPMENT_CONTROLS.values(),
            CONTROL_SNAPSHOT_MANIFEST,
            DEVELOPMENT_CASES,
            HOSTILE_SPECIMENS,
            HOSTILE_EXECUTION,
            DEVELOPMENT_REPORT,
            DEVELOPMENT_INVENTORY,
            FIXTURES / "evidence/development/resource-samples.json",
            *DEVELOPMENT_RESULTS.values(),
        ]
        for path in paths:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                raw = path.read_bytes()
                value = AI._decode_record(raw)
                self.assertEqual(raw, canonical(value))

    def test_all_arms_share_one_candidate_independent_contract(self):
        contracts = {canonical(control["contract"]) for control in self.controls.values()}
        self.assertEqual(len(contracts), 1)
        for control in self.controls.values():
            self.assertFalse(control["claims"]["candidate_defines_semantics"])
            self.assertFalse(control["claims"]["fallback_is_native_coverage"])
            self.assertFalse(control["claims"]["fallback_is_aggregate_success"])
            mechanism = control["mechanism_evidence"]
            self.assertTrue(mechanism["current_native_in_current_coverage"])
            self.assertFalse(mechanism["synthetic_in_current_coverage"])
            self.assertFalse(mechanism["synthetic_in_aggregate_success"])

    def test_runtime_closes_cases_prompts_scores_and_reports(self):
        try:
            AI._validate_development_cases(
                self.cases, self.manifest, self.cohorts, self.graph
            )
        except AI.Refusal as exc:
            if str(exc) != "development cases has a non-closed field set":
                raise
            self.fail(f"development case validator rejected its repaired contract: {exc}")
        try:
            AI._validate_development_report(self.report)
        except KeyError as err:
            self.fail(f"development report validator crashed on its field contract: {err}")
        for arm, result in self.results.items():
            self.validate_adapter_result(arm, result)


class ControlSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest_raw = CONTROL_SNAPSHOT_MANIFEST.read_bytes()
        cls.manifest = json.loads(cls.manifest_raw)

    @contextmanager
    def _checked_generation_source(self):
        """Isolate publication checks from the generator's full-ref precondition."""
        paths_by_ref: dict[str, list[str]] = {}
        oid_by_source: dict[tuple[str, str], str] = {}
        expected_prefixes = dict(AI.CONTROL_SNAPSHOT_GROUPS)
        for record in self.manifest["artifacts"]:
            ref = record["ref"]
            path = record["path"]
            oid = record["blob_oid"]
            paths_by_ref.setdefault(ref, []).append(path)
            oid_by_source[(ref, path)] = oid

        def control_paths(ref: str, prefixes: tuple[str, ...]) -> list[str]:
            if expected_prefixes.get(ref) != prefixes:
                raise AssertionError("generation requested an unknown control source")
            return sorted(paths_by_ref[ref])

        def blob_identity(ref: str, path: str) -> str:
            try:
                return oid_by_source[(ref, path)]
            except KeyError as exc:
                raise AssertionError("generation requested an unknown control blob") from exc

        with (
            mock.patch.object(AI, "_git_control_paths", side_effect=control_paths),
            mock.patch.object(AI, "_git_blob_identity_at", side_effect=blob_identity),
        ):
            yield

    def test_snapshot_manifest_and_every_object_are_self_bound(self):
        self.assertEqual(
            hashlib.sha256(self.manifest_raw).hexdigest(),
            AI.EXPECTED_CONTROL_SNAPSHOT_SHA256,
        )
        self.assertEqual(
            self.manifest["totals"], AI.EXPECTED_CONTROL_SNAPSHOT_COUNTS
        )
        artifacts = self.manifest["artifacts"]
        objects = self.manifest["objects"]
        self.assertEqual(
            [(item["ref"], item["path"]) for item in artifacts],
            sorted({(item["ref"], item["path"]) for item in artifacts}),
        )
        self.assertEqual(
            [item["oid"] for item in objects],
            sorted({item["oid"] for item in objects}),
        )
        by_oid = {item["oid"]: item for item in objects}
        observed = {}
        for oid, record in by_oid.items():
            data = (CONTROL_SNAPSHOT_MANIFEST.parent / "objects" / oid).read_bytes()
            self.assertEqual(len(data), record["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
            self.assertEqual(oracle_blob_oid(data, len(oid)), oid)
            observed[oid] = data
        for record in artifacts:
            source = by_oid[record["blob_oid"]]
            self.assertEqual(record["bytes"], source["bytes"])
            self.assertEqual(record["sha256"], source["sha256"])
        self.assertEqual(set(observed), {item["blob_oid"] for item in artifacts})

    def test_snapshot_manifest_regenerates_byte_identically_from_its_objects(self):
        objects = {
            item["oid"]: (
                CONTROL_SNAPSHOT_MANIFEST.parent / "objects" / item["oid"]
            ).read_bytes()
            for item in self.manifest["objects"]
        }
        rebuilt = AI._control_snapshot_manifest(self.manifest["artifacts"], objects)
        self.assertEqual(canonical(rebuilt), self.manifest_raw)

    def test_available_control_refs_retain_stronger_commit_path_binding(self):
        shallow = oracle_git("rev-parse", "--is-shallow-repository", limit=16)
        self.assertEqual(shallow.returncode, 0)
        self.assertIn(shallow.stdout, {b"true\n", b"false\n"})
        by_ref = {}
        for record in self.manifest["artifacts"]:
            by_ref.setdefault(record["ref"], []).append(record)
        for ref, records in by_ref.items():
            expression = f"{ref}^{{commit}}"
            probe = oracle_git(
                "cat-file",
                "--batch-check=%(objectname) %(objecttype)",
                input_data=f"{expression}\n".encode("ascii"),
                limit=128,
            )
            self.assertEqual(probe.returncode, 0)
            if probe.stdout == f"{expression} missing\n".encode("ascii"):
                self.assertEqual(shallow.stdout, b"true\n")
                continue
            self.assertEqual(probe.stdout, f"{ref} commit\n".encode("ascii"))
            for record in records:
                self.assertEqual(
                    oracle_parent_blob_oid(ref, record["path"]),
                    record["blob_oid"],
                )

    def test_snapshot_mode_reads_no_git_object_or_network_fallback(self):
        record = self.manifest["artifacts"][0]
        clear_source_cache()
        try:
            with (
                mock.patch.object(AI, "_control_ref_mode", return_value="snapshot"),
                mock.patch.object(
                    AI, "_git", side_effect=AssertionError("snapshot escaped to Git")
                ),
            ):
                data = AI._git_blob_at(record["ref"], record["path"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), record["sha256"])
        finally:
            clear_source_cache()

    def test_control_ref_snapshot_admission_fails_closed(self):
        ref = AI.WAI1_CONTROL_REF
        expression = f"{ref}^{{commit}}"

        def missing_complete(arguments, limit=AI.MAX_GIT_OUTPUT, **kwargs):
            if arguments[0] == "cat-file":
                return f"{expression} missing\n".encode("ascii")
            if arguments == ["rev-parse", "--is-shallow-repository"]:
                return b"false\n"
            raise AssertionError(f"unexpected Git probe: {arguments}")

        def ambiguous(arguments, limit=AI.MAX_GIT_OUTPUT, **kwargs):
            if arguments[0] == "cat-file":
                return b"ambiguous\n"
            raise AssertionError(f"unexpected Git probe: {arguments}")

        for fake, message in (
            (missing_complete, "absent from a non-shallow"),
            (ambiguous, "unexpected control identity"),
        ):
            with self.subTest(message=message):
                AI._control_ref_mode.cache_clear()
                with (
                    mock.patch.object(AI, "_git", side_effect=fake),
                    self.assertRaisesRegex(AI.Refusal, message),
                ):
                    AI._control_ref_mode(ref)
        AI._control_ref_mode.cache_clear()

    def test_existing_control_path_mismatch_does_not_fall_back(self):
        record = self.manifest["artifacts"][0]
        clear_source_cache()
        try:
            with (
                mock.patch.object(AI, "_control_ref_mode", return_value="git"),
                mock.patch.object(AI, "_git_blob_identity_at", return_value="0" * 40),
                self.assertRaisesRegex(AI.Refusal, "differs from its snapshot"),
            ):
                AI._git_blob_at(record["ref"], record["path"])
        finally:
            clear_source_cache()

    def test_snapshot_object_byte_drift_refuses(self):
        oid = self.manifest["objects"][0]["oid"]
        target = CONTROL_SNAPSHOT_MANIFEST.parent / "objects" / oid
        original_read = AI._read_regular

        def corrupt(path: Path, limit: int) -> bytes:
            data = original_read(path, limit)
            if path == target:
                return bytes([data[0] ^ 1]) + data[1:]
            return data

        clear_source_cache()
        try:
            with (
                mock.patch.object(AI, "_read_regular", side_effect=corrupt),
                self.assertRaisesRegex(AI.Refusal, "size, digest, or blob identity"),
            ):
                AI._control_snapshot()
        finally:
            clear_source_cache()

    def test_snapshot_object_directory_is_closed(self):
        with scratch_directory("control-snapshot-extra-") as temporary:
            snapshot = Path(temporary) / "snapshot"
            shutil.copytree(CONTROL_SNAPSHOT_MANIFEST.parent, snapshot)
            (snapshot / "objects" / ("0" * 40)).write_bytes(b"unlisted")
            relative = PurePosixPath(snapshot.relative_to(ROOT).as_posix())
            clear_source_cache()
            try:
                with (
                    mock.patch.object(AI, "CONTROL_SNAPSHOT_ROOT", relative),
                    mock.patch.object(
                        AI,
                        "CONTROL_SNAPSHOT_MANIFEST",
                        relative / "manifest.json",
                    ),
                    self.assertRaisesRegex(
                        AI.Refusal,
                        "object inventory exceeds its bound|object directory differs from its manifest",
                    ),
                ):
                    AI._control_snapshot()
            finally:
                clear_source_cache()

    def test_snapshot_directory_inventory_refuses_at_its_count_bound(self):
        with scratch_directory("control-snapshot-inventory-bound-") as temporary:
            snapshot = Path(temporary) / "snapshot"
            objects = snapshot / "objects"
            objects.mkdir(parents=True)
            (objects / "owned").write_bytes(b"owned")
            (objects / "unowned").write_bytes(b"unowned")
            relative = PurePosixPath(snapshot.relative_to(ROOT).as_posix())
            with self.assertRaisesRegex(
                AI.Refusal, "control snapshot object inventory exceeds its bound"
            ):
                AI._preflight_snapshot_publication(relative, {"owned"})

    def test_snapshot_root_directory_is_closed(self):
        with scratch_directory("control-snapshot-root-extra-") as temporary:
            snapshot = Path(temporary) / "snapshot"
            shutil.copytree(CONTROL_SNAPSHOT_MANIFEST.parent, snapshot)
            (snapshot / "EXTRA").write_bytes(b"unlisted")
            relative = PurePosixPath(snapshot.relative_to(ROOT).as_posix())
            clear_source_cache()
            try:
                with (
                    mock.patch.object(AI, "CONTROL_SNAPSHOT_ROOT", relative),
                    mock.patch.object(
                        AI,
                        "CONTROL_SNAPSHOT_MANIFEST",
                        relative / "manifest.json",
                    ),
                    self.assertRaisesRegex(
                        AI.Refusal,
                        "root inventory exceeds its bound|root directory is not closed",
                    ),
                ):
                    AI._control_snapshot()
            finally:
                clear_source_cache()

    def test_snapshot_generation_refuses_unowned_entries_before_writing(self):
        for relative_extra in ("EXTRA", "objects/EXTRA"):
            with self.subTest(relative_extra=relative_extra):
                with scratch_directory("control-snapshot-generate-extra-") as temporary:
                    snapshot = Path(temporary) / "snapshot"
                    (snapshot / "objects").mkdir(parents=True)
                    extra = snapshot / relative_extra
                    extra.parent.mkdir(parents=True, exist_ok=True)
                    extra.write_bytes(b"unowned")
                    with (
                        self._checked_generation_source(),
                        mock.patch.object(AI, "_atomic_write") as write,
                        self.assertRaisesRegex(
                            AI.Refusal, "not closed|unowned entry"
                        ),
                    ):
                        AI.snapshot_controls(types.SimpleNamespace(output=snapshot))
                    write.assert_not_called()

    def test_snapshot_generation_completes_owned_partial_and_clean_refresh(self):
        with scratch_directory("control-snapshot-generate-owned-") as temporary:
            snapshot = Path(temporary) / "snapshot"
            objects = snapshot / "objects"
            objects.mkdir(parents=True)
            first_oid = self.manifest["objects"][0]["oid"]
            shutil.copy2(
                CONTROL_SNAPSHOT_MANIFEST.parent / "objects" / first_oid,
                objects / first_oid,
            )
            arguments = types.SimpleNamespace(output=snapshot)
            with self._checked_generation_source():
                first = AI.snapshot_controls(arguments)
                second = AI.snapshot_controls(arguments)
            self.assertEqual(first, second)
            self.assertEqual(
                {path.name for path in snapshot.iterdir()},
                {"manifest.json", "objects"},
            )
            self.assertEqual(
                {path.name for path in objects.iterdir()},
                {item["oid"] for item in self.manifest["objects"]},
            )
            self.assertEqual(snapshot.joinpath("manifest.json").read_bytes(), self.manifest_raw)
            for item in self.manifest["objects"]:
                self.assertEqual(
                    (objects / item["oid"]).read_bytes(),
                    (
                        CONTROL_SNAPSHOT_MANIFEST.parent
                        / "objects"
                        / item["oid"]
                    ).read_bytes(),
                )

    def _one_commit_shallow_checkout(self, *, development: bool):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        checkout = Path(temporary.name) / "repo"
        checkout.mkdir()
        script_target = checkout / SCRIPT.relative_to(ROOT)
        script_target.parent.mkdir(parents=True)
        shutil.copy2(SCRIPT, script_target)
        if development:
            shutil.copytree(FIXTURES, checkout / FIXTURES.relative_to(ROOT))
            live_paths = set(oracle_inventory_sources())
            live_paths.add("docs/instruction-architecture/corpus-reconciliation.md")
            live_paths.update(
                record["path"]
                for record in self.manifest["artifacts"]
                if record["ref"] == ORACLE_SOURCE_REF
            )
            for relative in sorted(live_paths):
                source = ROOT / relative
                destination = checkout / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)
        else:
            shutil.copytree(
                CONTROL_SNAPSHOT_MANIFEST.parent,
                checkout / CONTROL_SNAPSHOT_MANIFEST.parent.relative_to(ROOT),
            )
        git_environment = {
            **ORACLE_GIT_ENV,
            "GIT_AUTHOR_DATE": "2026-01-01T00:00:00Z",
            "GIT_AUTHOR_EMAIL": "shallow-guard@example.invalid",
            "GIT_AUTHOR_NAME": "shallow guard",
            "GIT_COMMITTER_DATE": "2026-01-01T00:00:00Z",
            "GIT_COMMITTER_EMAIL": "shallow-guard@example.invalid",
            "GIT_COMMITTER_NAME": "shallow guard",
        }
        initialise = subprocess.run(
            [
                "/usr/bin/git",
                "init",
                "--quiet",
                str(checkout),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env=git_environment,
            check=False,
            timeout=30,
        )
        self.assertEqual(
            initialise.returncode,
            0,
            initialise.stderr.decode(errors="replace"),
        )
        for arguments in (
            ["add", "--all"],
            ["commit", "--quiet", "--no-gpg-sign", "-m", "shallow guard"],
        ):
            result = subprocess.run(
                ["/usr/bin/git", *arguments],
                cwd=checkout,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                env=git_environment,
                check=False,
                timeout=30,
            )
            self.assertEqual(
                result.returncode, 0, result.stderr.decode(errors="replace")
            )
        head = subprocess.run(
            ["/usr/bin/git", "rev-parse", "HEAD"],
            cwd=checkout,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env=git_environment,
            check=False,
            timeout=10,
        )
        self.assertEqual(head.returncode, 0, head.stderr.decode(errors="replace"))
        (checkout / ".git/shallow").write_bytes(head.stdout)
        self.assertEqual(
            subprocess.run(
                ["/usr/bin/git", "rev-list", "--count", "HEAD"],
                cwd=checkout,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                env=git_environment,
                check=False,
                timeout=10,
            ).stdout,
            b"1\n",
        )
        self.assertEqual(
            subprocess.run(
                ["/usr/bin/git", "rev-parse", "--is-shallow-repository"],
                cwd=checkout,
                stdin=subprocess.DEVNULL,
                capture_output=True,
                env=git_environment,
                check=False,
                timeout=10,
            ).stdout,
            b"true\n",
        )
        return checkout

    def test_one_commit_shallow_checkout_reads_checked_control_snapshot(self):
        checkout = self._one_commit_shallow_checkout(development=False)
        checker = next(
            record
            for record in self.manifest["artifacts"]
            if record["ref"] == ORACLE_SOURCE_REF
            and record["path"] == "scripts/agent_instruction.py"
        )
        probe = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "import hashlib,importlib.util,pathlib;"
                    "p=pathlib.Path('research/instruction-architecture/benchmark.py').resolve();"
                    "s=importlib.util.spec_from_file_location('ai',p);"
                    "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);"
                    "d=m._git_blob_at(m.WAI1_CONTROL_REF,'scripts/agent_instruction.py');"
                    f"assert hashlib.sha256(d).hexdigest()=='{checker['sha256']}'"
                ),
            ],
            cwd=checkout,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
            timeout=30,
        )
        self.assertEqual(probe.returncode, 0, probe.stderr.decode(errors="replace"))

    def test_one_commit_shallow_checkout_replays_development_cli(self):
        checkout = self._one_commit_shallow_checkout(development=True)
        replay = subprocess.run(
            [
                sys.executable,
                "research/instruction-architecture/benchmark.py",
                "replay",
                "--cohort",
                "development",
                "--evidence",
                "tests/fixtures/instruction-architecture/evidence/development",
            ],
            cwd=checkout,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            check=False,
            timeout=90,
        )
        self.assertEqual(replay.returncode, 0, replay.stderr.decode(errors="replace"))
        self.assertIn(b'"command":"replay-development"', replay.stdout)


class RawAdapterTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_raw_inventory_is_the_complete_physical_and_unique_corpus(self):
        control = self.controls["raw"]
        summary = control["coverage"]["summary"]
        self.assertEqual(
            (
                summary["native_ranges"],
                summary["native_physical_files"],
                summary["native_physical_bytes"],
                summary["native_unique_bytes"],
                summary["fallback_ranges"],
            ),
            (191, 191, 2_290_450, 1_819_006, 0),
        )
        self.assertEqual(
            hashlib.sha256(DEVELOPMENT_CONTROLS["raw"].read_bytes()).hexdigest(),
            "bfc416cc7fd3d9a1a569fea4eaa6e6577770bf89f77b68eb23378633d57da23e",
        )

    def test_raw_ranges_recover_every_exact_source(self):
        rows = self.controls["raw"]["coverage"]["ranges"]
        self.assertEqual([item["path"] for item in rows], sorted(item["path"] for item in rows))
        for row in rows:
            data = AI._source_blob(row["path"])
            self.assertEqual((row["start"], row["end"]), (0, len(data)))
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])

    def test_raw_prompt_follows_verified_scenario_graph(self):
        result = self.results["raw"]["results"][0]
        expected_paths = AI._scenario_paths(self.manifest, self.graph, result["scenario_id"])
        components = result["prompt"]["components"][1:]
        self.assertEqual([item["source"]["path"] for item in components], expected_paths)
        for component in components:
            source = component["source"]
            data = AI._source_blob(source["path"])[source["start"] : source["end"]]
            self.assertEqual(component["content"].encode(), data)


class Wai1ControlTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_wai1_binds_three_exact_current_envelopes_and_checker(self):
        control = self.controls["wai1"]
        summary = control["coverage"]["summary"]
        self.assertEqual(control["binding"]["product_ref"], AI.SOURCE_REF)
        self.assertEqual(len(control["binding"]["artifacts"]), 32)
        self.assertEqual(control["binding"]["checker"]["record_count"], 21)
        self.assertEqual(control["mechanism_evidence"]["current_native_envelopes"], 3)
        self.assertEqual(
            (
                summary["native_ranges"],
                summary["native_physical_bytes"],
                summary["native_unique_bytes"],
                summary["fallback_ranges"],
                summary["fallback_physical_bytes"],
                summary["fallback_unique_bytes"],
            ),
            (3, 11_170, 11_170, 194, 2_279_280, 1_807_836),
        )

    def test_wai1_control_and_native_mappings_are_immutable(self):
        path = DEVELOPMENT_CONTROLS["wai1"]
        self.assertEqual(
            hashlib.sha256(path.read_bytes()).hexdigest(),
            "d45599ba946cf515a72491310a105db6e257847d67541f218398877ea84e0ac1",
        )
        for mapping in self.controls["wai1"]["native_mappings"]:
            source = AI._source_blob(mapping["path"])[mapping["start"] : mapping["end"]]
            compact = AI._git_blob_at(AI.WAI1_CONTROL_REF, mapping["representation_path"])
            self.assertEqual(hashlib.sha256(source).hexdigest(), mapping["source_sha256"])
            self.assertEqual(hashlib.sha256(compact).hexdigest(), mapping["representation_sha256"])

    def test_wai1_only_claims_exact_recovery_for_prompt_carried_source_bytes(self):
        aggregate = self.results["wai1"]["aggregate"]
        self.assertEqual(
            (
                aggregate.get("exact_source_recovery_cases"),
                aggregate.get("native_mapping_cases"),
                aggregate.get("native_exact_source_recovery_cases"),
                aggregate["fallback_cases"],
            ),
            (7, 3, 0, 7),
        )
        for result in self.results["wai1"]["results"]:
            if result["score"]["fallback_used"]:
                self.assertTrue(result["score"]["exact_source_recovery"])
                self.assertFalse(result["score"]["native_mapping_used"])
                self.assertFalse(result["score"]["native_exact_source_recovery"])
            else:
                self.assertTrue(result["score"]["native_mapping_used"])
                self.assertFalse(result["score"]["exact_source_recovery"])
                self.assertFalse(result["score"]["native_exact_source_recovery"])
                self.assertEqual(result["outcome"]["status"], "exact-source-unavailable")
                self.assertIsNone(result["outcome"]["recovery"])

    def test_every_compact_prompt_carries_one_bound_decoder_bootstrap(self):
        loader = getattr(AI, "_wai1_decoder_bootstrap", None)
        self.assertIsNotNone(loader, "WAI1 compact prompts omit their decoder bootstrap")
        bootstrap_path, bootstrap = loader()
        self.assertTrue(
            any(
                item["path"] == bootstrap_path
                and item["sha256"] == hashlib.sha256(bootstrap).hexdigest()
                for item in self.controls["wai1"]["binding"]["artifacts"]
            )
        )
        for result in self.results["wai1"]["results"]:
            compact = [
                item
                for item in result["prompt"]["components"]
                if item["encoding"] == "wai1-compact"
            ]
            bootstraps = [
                item
                for item in result["prompt"]["components"]
                if item["encoding"] == "wai1-decoder-bootstrap"
            ]
            self.assertTrue(compact)
            self.assertEqual(len(bootstraps), 1)
            self.assertEqual(bootstraps[0]["content"].encode(), bootstrap)
            self.assertIsNone(bootstraps[0]["source"])


class NoemaControlTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_noema_binds_product_and_review_without_copying_product_paths(self):
        control = self.controls["noema"]
        self.assertEqual(control["binding"]["product_ref"], AI.NOEMA_PRODUCT_REF)
        self.assertEqual(control["binding"]["review_ref"], AI.NOEMA_REVIEW_REF)
        self.assertEqual(len(control["binding"]["artifacts"]), 140)
        self.assertEqual(
            hashlib.sha256(DEVELOPMENT_CONTROLS["noema"].read_bytes()).hexdigest(),
            "2c52f72927eeb630c1abbc6a2a994221235c6f1aa81d33ff9965002cddbc2a4b",
        )

    def test_full_corpus_exact_binding_and_development_outcomes_are_separate(self):
        control = self.controls["noema"]
        summary = control["coverage"]["summary"]
        self.assertEqual(
            (
                summary["native_ranges"],
                summary["native_physical_bytes"],
                summary["native_unique_bytes"],
                summary["fallback_ranges"],
                summary["fallback_physical_bytes"],
                summary["fallback_unique_bytes"],
            ),
            (10, 655, 655, 201, 2_289_795, 1_818_351),
        )
        native_paths = {
            row["path"]
            for row in control["coverage"]["ranges"]
            if row["mode"] == "native"
        }
        self.assertEqual(native_paths, {"plugins/sapheneia/skills/sapheneia/SKILL.md"})
        self.assertTrue(native_paths <= set(self.cohorts["holdout"]["paths"]))
        case_paths = {case["source"]["path"] for case in self.cases["cases"]}
        self.assertFalse(native_paths & case_paths)
        self.assertEqual(
            self.results["noema"]["aggregate"].get("native_mapping_cases"), 0
        )

    def test_synthetic_mechanism_evidence_is_never_current_or_aggregate_success(self):
        mechanism = self.controls["noema"]["mechanism_evidence"]
        self.assertEqual(
            (mechanism["synthetic_mapped_spans"], mechanism["synthetic_mapped_bytes"]),
            (40, 3_173),
        )
        self.assertTrue(mechanism["current_native_in_current_coverage"])
        self.assertFalse(mechanism["synthetic_in_current_coverage"])
        self.assertFalse(mechanism["synthetic_in_aggregate_success"])
        row = next(item for item in self.report["arms"] if item["arm"] == "noema")
        self.assertFalse(row["synthetic_in_current_coverage"])
        self.assertFalse(row["synthetic_in_aggregate_success"])
        self.assertEqual(
            (
                row["full_current_corpus_native_ranges"],
                row["full_current_corpus_native_bytes"],
                row.get("development_native_mapping_cases"),
                row.get("development_native_exact_source_recovery_cases"),
            ),
            (10, 655, 0, 0),
        )

    def test_denominator_substitution_and_fallback_relabelling_refuse(self):
        for field, value in (
            ("full_current_corpus_native_bytes", 0),
            ("full_current_corpus_native_ranges", 0),
            ("development_native_mapping_cases", 1),
            ("development_native_exact_source_recovery_cases", 1),
        ):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.report)
                row = next(item for item in changed["arms"] if item["arm"] == "noema")
                row[field] = value
                try:
                    with self.assertRaisesRegex(AI.Refusal, "relabels"):
                        AI._validate_development_report(changed)
                except KeyError as err:
                    self.fail(f"development report validator crashed on its field contract: {err}")

    def test_holdout_owned_native_spans_are_bound_but_not_emitted_in_development(self):
        control = self.controls["noema"]
        self.assertEqual(len(control["native_mappings"]), 10)
        bundles = [
            item
            for result in self.results["noema"]["results"]
            for item in result["prompt"]["components"]
            if item["encoding"] == "noema-first-use"
        ]
        self.assertEqual(
            bundles,
            [],
            "development prompts emit a bundle whose only current mapping is holdout-owned",
        )
        expected = {item["representation_sha256"] for item in control["native_mappings"]}
        bound = set()
        for mapping in control["native_mappings"]:
            relative_root = Path(mapping["representation_path"]).parent.relative_to(
                Path("tests/fixtures/noema-v1")
            )
            path, payload = AI._noema_prompt_bundle(relative_root.as_posix())
            self.assertEqual(path, mapping["representation_path"])
            bound.add(hashlib.sha256(payload).hexdigest())
        self.assertEqual(expected, bound)


class SimpleControlTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_simple_control_is_only_file_addressing_dedup_and_selection(self):
        control = self.controls["simple"]
        self.assertEqual(len(control["graph"]["nodes"]), 174)
        self.assertEqual(len(control["graph"]["edges"]), 17)
        self.assertEqual({edge["kind"] for edge in control["graph"]["edges"]}, {"exact-content-alias"})
        self.assertEqual(control["coverage"]["summary"]["native_physical_bytes"], 2_290_450)
        self.assertEqual(
            hashlib.sha256(DEVELOPMENT_CONTROLS["simple"].read_bytes()).hexdigest(),
            "f4de11d7c9b0c05dc902c5971dc71d348e7879e6d357294627247b7faee8b5c4",
        )

    def test_simple_prompt_deduplicates_only_equal_whole_files(self):
        for result in self.results["simple"]["results"]:
            ids = [row["representation_id"] for row in result["selection_trace"]]
            self.assertEqual(len(ids), len(set(ids)))
            for row in result["selection_trace"]:
                self.assertTrue(row["representation_id"].startswith("file:"))
                digests = {
                    next(item for item in self.manifest["documents"] if item["path"] == path)["sha256"]
                    for path in row["original_paths"]
                }
                self.assertEqual(len(digests), 1)


class SectionGraphTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_section_graph_has_exact_stable_nodes_dependencies_and_fallback(self):
        control = self.controls["section-graph"]
        summary = control["coverage"]["summary"]
        self.assertEqual(len(control["graph"]["nodes"]), 1_471)
        self.assertEqual(
            (
                summary["native_ranges"],
                summary["native_physical_files"],
                summary["native_physical_bytes"],
                summary["native_unique_bytes"],
                summary["fallback_ranges"],
                summary["fallback_physical_bytes"],
            ),
            (1_896, 176, 2_071_863, 1_600_419, 15, 218_587),
        )
        ids = {node["id"] for node in control["graph"]["nodes"]}
        self.assertEqual(len(ids), 1_471)
        parent_edges = [
            edge for edge in control["graph"]["edges"] if edge["kind"] == "section-parent"
        ]
        self.assertTrue(
            all(edge["source"] in ids and edge["target"] in ids for edge in parent_edges)
        )
        self.assertEqual(
            hashlib.sha256(DEVELOPMENT_CONTROLS["section-graph"].read_bytes()).hexdigest(),
            "64f62560d56b65c782c792854a7803e90c864cb7fa590e75618f2f744c8d40a1",
        )

    def test_every_markdown_file_round_trips_by_exact_sections(self):
        by_path = {}
        for node in self.controls["section-graph"]["graph"]["nodes"]:
            by_path.setdefault(node["path"], []).append(node)
        for path, nodes in by_path.items():
            with self.subTest(path=path):
                data = AI._source_blob(path)
                recovered = b"".join(
                    data[node["start"] : node["end"]]
                    for node in sorted(nodes, key=lambda item: item["start"])
                )
                self.assertEqual(recovered, data)

    def test_missing_dependency_edge_refuses(self):
        changed = copy.deepcopy(self.controls["section-graph"])
        changed["graph"]["edges"].pop()
        with self.assertRaisesRegex(AI.Refusal, "misses an edge"):
            AI._validate_section_graph(changed, self.manifest)

    def test_authority_selection_and_alias_mutations_refuse(self):
        mutations = []
        missing_selection = copy.deepcopy(self.controls["section-graph"])
        missing_selection["graph"].pop("selection", None)
        mutations.append(missing_selection)
        changed_authority = copy.deepcopy(self.controls["section-graph"])
        changed_authority["graph"]["nodes"][0]["authority_tier"] = "invented"
        mutations.append(changed_authority)
        missing_alias = copy.deepcopy(self.controls["section-graph"])
        alias_index = next(
            index
            for index, edge in enumerate(missing_alias["graph"]["edges"])
            if edge["kind"] == "exact-content-alias"
        )
        missing_alias["graph"]["edges"].pop(alias_index)
        mutations.append(missing_alias)
        for changed in mutations:
            with self.subTest(), self.assertRaisesRegex(AI.Refusal, "differs|misses"):
                AI._validate_section_graph(changed, self.manifest)

    def test_section_graph_declares_authority_selection_and_exact_alias_dedup(self):
        control = self.controls["section-graph"]
        graph = control["graph"]
        documents = {item["path"]: item for item in self.manifest["documents"]}
        selection = graph.get("selection")
        self.assertIsInstance(
            selection,
            dict,
            "section graph omits its deterministic scenario-root and closure policy",
        )
        self.assertEqual(
            selection,
            {
                "closure": "selected-sections-plus-transitive-parents",
                "deduplication": "exact-whole-file-canonical-content",
                "fallback": "whole-source-for-unsupported-non-markdown",
                "roots": "all-sections-of-loader-reachable-canonical-files",
                "scenario_source": "verified-loader-graph",
            },
        )
        nodes = graph["nodes"]
        self.assertTrue(nodes)
        self.assertTrue(
            all(node.get("authority_tier") == documents[node["path"]]["authority_tier"] for node in nodes),
            "section nodes omit or misstate source-owned authority",
        )
        self.assertTrue(
            all(documents[node["path"]]["canonical_content_path"] == node["path"] for node in nodes),
            "section graph parses physical duplicates as independent authority",
        )
        aliases = [edge for edge in graph["edges"] if edge["kind"] == "exact-content-alias"]
        self.assertEqual(len(aliases), len(self.cohorts["generated_duplicates_excluded"]))
        grouped = [
            row
            for result in self.results["section-graph"]["results"]
            for row in result["selection_trace"]
            if len(row["original_paths"]) > 1
        ]
        self.assertTrue(grouped, "section prompts do not deduplicate exact physical aliases")
        for row in grouped:
            self.assertEqual(
                1,
                len({documents[path]["sha256"] for path in row["original_paths"]}),
            )


class DevelopmentCaseTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_closed_case_set_uses_only_exact_development_source_spans(self):
        self.assertEqual(
            [case["semantic_class"] for case in self.cases["cases"]],
            list(AI.DEVELOPMENT_CLASSES),
        )
        try:
            AI._validate_development_cases(
                self.cases, self.manifest, self.cohorts, self.graph
            )
        except AI.Refusal as exc:
            if str(exc) != "development cases has a non-closed field set":
                raise
            self.fail(f"development case validator rejected its repaired contract: {exc}")
        holdout = set(self.cohorts["holdout"]["paths"])
        self.assertFalse({case["source"]["path"] for case in self.cases["cases"]} & holdout)

    def test_all_arms_run_identical_cases_and_tasks_without_scorer_keys(self):
        expected_ids = [case["id"] for case in self.cases["cases"]]
        expected_tasks = {case["id"]: case["task"] for case in self.cases["cases"]}
        for arm, record in self.results.items():
            with self.subTest(arm=arm):
                self.assertEqual([item["case_id"] for item in record["results"]], expected_ids)
                for item in record["results"]:
                    prompt = item["prompt"]
                    self.assertEqual(prompt["components"][0]["content"], expected_tasks[item["case_id"]])
                    serialized = canonical(prompt).decode()
                    self.assertNotIn('"expected_answer"', serialized)
                    self.assertNotIn('"scorer_key"', serialized)
                    self.assertNotIn('"arm"', serialized)

    def test_holdout_remains_unopened_and_unaccessed(self):
        self.assertEqual(self.report["holdout"], {"cases_accessed": 0, "opened": False})
        seal = load(SEAL)
        self.assertFalse(seal["opened"])
        self.assertTrue(all(not case["id"].startswith("holdout-") for case in self.cases["cases"]))

    def test_behavioral_development_cohort_meets_issue_coverage_and_isolation(self):
        documents = {item["path"]: item for item in self.manifest["documents"]}
        physical_paths = {
            path
            for case in self.cases["cases"]
            for path in AI._scenario_paths(self.manifest, self.graph, case["scenario_id"])
        }
        holdout_paths = set(self.cohorts["holdout"]["paths"])
        self.assertFalse(
            physical_paths & holdout_paths,
            "development prompts expose holdout-owned source paths",
        )
        canonical_paths = {
            documents[path]["canonical_content_path"] for path in physical_paths
        }
        shared_paths = getattr(AI, "SHARED_BEHAVIORAL_PATHS", None)
        self.assertIsNotNone(
            shared_paths,
            "development coverage has no explicit shared-contract inventory",
        )
        self.assertLessEqual(set(shared_paths), canonical_paths)
        unique_bytes = sum(documents[path]["bytes"] for path in canonical_paths)
        self.assertGreaterEqual(
            unique_bytes * 2,
            self.manifest["totals"]["unique_bytes"],
            "behavioral development prompts cover less than 50 percent of canonical bytes",
        )
        logical_skills = {
            documents[path]["logical_document"]
            for path in canonical_paths
            if documents[path]["logical_document"].startswith("skill:")
        }
        self.assertGreaterEqual(len(logical_skills), 12)
        self.assertEqual(
            {documents[path]["authority_tier"] for path in canonical_paths},
            set(self.cohorts["development"]["authority_tiers"]),
        )
        self.assertEqual(
            set(AI._observed_constructs(sorted(canonical_paths))),
            set(self.cohorts["development"]["constructs"]),
        )
        deciles = AI._size_deciles(
            [
                item
                for item in self.manifest["documents"]
                if item["path"] == item["canonical_content_path"]
            ]
        )
        self.assertEqual(
            sorted({deciles[path] for path in canonical_paths}),
            list(range(10)),
        )
        self.assertEqual(self.cases["coverage"]["size_deciles"], list(range(10)))

    def test_case_validator_refuses_holdout_exposure_and_subthreshold_coverage(self):
        holdout_exposure = copy.deepcopy(self.cases)
        holdout_exposure["cases"][0]["scenario_id"] = (
            "repository:skill:fiat:profile:fiat:audit-nonsol__inline__"
            "phylax-proxy__fix-elenchus:credential:absent"
        )
        with self.assertRaisesRegex(AI.Refusal, "sealed holdout"):
            AI._validate_development_cases(
                holdout_exposure, self.manifest, self.cohorts, self.graph
            )

        subthreshold = copy.deepcopy(self.cases)
        subthreshold["cases"][5]["scenario_id"] = (
            "agent-skills:skill:hermes:profile:hermes:gas-operation:"
            "credential:github-contributor"
        )
        with self.assertRaisesRegex(AI.Refusal, "below 50 percent"):
            AI._validate_development_cases(
                subthreshold, self.manifest, self.cohorts, self.graph
            )

    def test_exact_source_recovery_requires_source_bytes_in_the_complete_prompt(self):
        self.assertEqual(
            sum(
                record["aggregate"].get("exact_source_recovery_cases", -1)
                for record in self.results.values()
            ),
            47,
        )
        self.assertEqual(
            {
                arm: record["aggregate"].get("exact_source_recovery_cases")
                for arm, record in self.results.items()
            },
            {"noema": 10, "raw": 10, "section-graph": 10, "simple": 10, "wai1": 7},
        )
        for record in self.results.values():
            self.assertTrue(all(item["score"]["trace_complete"] for item in record["results"]))

    def test_scores_and_outcomes_are_rederived_from_the_complete_prompt(self):
        changed = copy.deepcopy(self.results["wai1"])
        result = changed["results"][0]
        compact = next(
            item for item in result["prompt"]["components"] if item["encoding"] == "wai1-compact"
        )
        compact["content"] = "corrupt-but-schema-valid"
        body = {key: value for key, value in result["prompt"].items() if key != "sha256"}
        result["prompt"]["sha256"] = hashlib.sha256(canonical(body)).hexdigest()
        changed["aggregate"]["prompt_bytes"] = sum(
            len(canonical(item["prompt"])) for item in changed["results"]
        )
        refused = False
        try:
            self.validate_adapter_result("wai1", changed)
        except AI.Refusal as exc:
            self.assertRegex(str(exc), "correlation|representation-bound")
            refused = True
        self.assertTrue(refused, "a compact prompt mutation retained its oracle-derived score")
        for record in self.results.values():
            for item in record["results"]:
                self.assertNotIn("recovered_source", item["outcome"])
                if item["score"]["exact_source_recovery"]:
                    self.assertEqual(item["outcome"]["status"], "exact-source-recovered")
                    self.assertEqual(
                        item["outcome"]["recovery"]["sha256"],
                        item["outcome"]["source_expectation"]["sha256"],
                    )
                else:
                    self.assertEqual(
                        item["outcome"]["status"], "exact-source-unavailable"
                    )
                    self.assertIsNone(item["outcome"].get("recovery"))

    def test_adapter_result_identity_and_case_coverage_are_context_bound(self):
        changed = copy.deepcopy(self.results["wai1"])
        changed["case_set_sha256"] = "0" * 64
        refused = False
        try:
            self.validate_adapter_result("wai1", changed)
        except AI.Refusal as exc:
            self.assertRegex(str(exc), "identity")
            refused = True
        self.assertTrue(refused, "adapter results accept a substituted case set")

        changed = copy.deepcopy(self.results["wai1"])
        changed["control_sha256"] = "0" * 64
        refused = False
        try:
            self.validate_adapter_result("wai1", changed)
        except AI.Refusal as exc:
            self.assertRegex(str(exc), "identity")
            refused = True
        self.assertTrue(refused, "adapter results accept a substituted control")

        changed = copy.deepcopy(self.results["wai1"])
        changed["results"].pop()
        changed["aggregate"] = {
            "cases": len(changed["results"]),
            "exact_source_recovery_cases": sum(
                item["score"]["exact_source_recovery"]
                for item in changed["results"]
            ),
            "fallback_cases": sum(
                item["score"]["fallback_used"] for item in changed["results"]
            ),
            "native_exact_source_recovery_cases": sum(
                item["score"]["native_exact_source_recovery"]
                for item in changed["results"]
            ),
            "native_mapping_cases": sum(
                item["score"]["native_mapping_used"]
                for item in changed["results"]
            ),
            "prompt_bytes": sum(
                len(canonical(item["prompt"])) for item in changed["results"]
            ),
        }
        refused = False
        try:
            self.validate_adapter_result("wai1", changed)
        except AI.Refusal as exc:
            self.assertRegex(str(exc), "case order or coverage")
            refused = True
        self.assertTrue(refused, "adapter results accept incomplete case coverage")


class MutationTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_hostile_inventory_is_closed_and_covers_named_failure_classes(self):
        specimens = load(HOSTILE_SPECIMENS)["specimens"]
        self.assertEqual(len(specimens), 12)
        risks = {item["risk_class"] for item in specimens}
        self.assertTrue(
            {
                "concurrent-change",
                "digest",
                "hostile-output",
                "malformed-input",
                "missing-edge",
                "parser-differential",
                "path-boundary",
                "resource-bound",
                "stale-source",
            }
            <= risks
        )

    def test_every_hostile_specimen_executes_and_refuses_on_all_five_arms(self):
        builder = getattr(AI, "_hostile_execution", None)
        self.assertIsNotNone(
            builder, "hostile specimens are inventoried but never executed"
        )
        self.assertTrue(HOSTILE_EXECUTION.is_file())
        committed = load(HOSTILE_EXECUTION)
        specimens = load(HOSTILE_SPECIMENS)
        self.assertEqual(len(committed["results"]), 60)
        self.assertEqual(
            {
                (item["arm"], item["specimen_id"])
                for item in committed["results"]
            },
            {
                (arm, specimen["id"])
                for arm in AI.DEVELOPMENT_ARMS
                for specimen in specimens["specimens"]
            },
        )
        self.assertTrue(all(item["status"] == "refused" for item in committed["results"]))
        try:
            rebuilt = builder(
                specimens,
                self.cases,
                self.manifest,
                self.cohorts,
                self.graph,
                self.controls,
                self.results,
            )
        except AI.Refusal as exc:
            if str(exc) != (
                "hostile specimen refused for the wrong reason: "
                "raw:hostile-02-stale-source"
            ):
                raise
            self.fail(f"hostile replay rejected its repaired evidence contract: {exc}")
        self.assertEqual(committed, rebuilt)

    def test_duplicate_key_noncanonical_and_unicode_scalar_refuse(self):
        with self.assertRaisesRegex(AI.Refusal, "duplicate JSON key"):
            AI._decode_record(b'{"a":1,"a":2}\n')
        with self.assertRaisesRegex(AI.Refusal, "canonical JSON"):
            AI._decode_record(b'{ "a": 1 }\n')
        with self.assertRaisesRegex(AI.Refusal, "non-Unicode-scalar"):
            AI._canonical_json({"a": "\ud800"})

    def test_fallback_cannot_be_relabelled_as_native_exact_source_recovery(self):
        changed = copy.deepcopy(self.results["noema"]["results"][0]["score"])
        changed["native_mapping_used"] = True
        changed["native_exact_source_recovery"] = True
        with self.assertRaisesRegex(AI.Refusal, "exclusive|predicates"):
            AI._validate_score(changed)

    def test_missing_loader_edge_refuses(self):
        scenario = self.cases["cases"][0]["scenario_id"]
        expected_path = self.cases["cases"][0]["source"]["path"]
        changed = copy.deepcopy(self.graph)
        for index, edge in enumerate(changed["scenario_edges"]):
            if scenario in edge["active_scenarios"] and edge["target"] == expected_path:
                changed["scenario_edges"].pop(index)
                break
        else:
            self.fail("case source had no removable scenario edge")
        with self.assertRaisesRegex(AI.Refusal, "missing or invented edge"):
            AI._scenario_paths(self.manifest, changed, scenario)

    def test_section_parser_differential_and_hostile_output_refuse(self):
        with self.assertRaisesRegex(AI.Refusal, "unclosed fenced block"):
            AI._markdown_sections("hostile.md", b"# admitted\n```text\nnot closed\n")
        with self.assertRaisesRegex(AI.Refusal, "model output exceeds"):
            AI._validate_model_output(b"x" * (AI.MAX_MODEL_OUTPUT_BYTES + 1))

    def test_section_parser_keeps_nonblank_fence_markers_literal(self):
        source = (
            b"# outer\n"
            b"```text\n"
            b"```not-a-close\n"
            b"# code heading\n"
            b"````also-not-a-close\n"
            b"# still code\n"
            b"```\n"
            b"# after\n"
        )
        after = source.index(b"# after")
        try:
            nodes = AI._markdown_sections("hostile.md", source)
        except AI.Refusal as exc:
            self.fail(f"valid fenced Markdown was refused: {exc}")
        self.assertEqual(
            [(node["start"], node["end"]) for node in nodes],
            [(0, after), (after, len(source))],
        )


class PathBoundaryTests(unittest.TestCase):
    def test_noncanonical_paths_refuse(self):
        for path in ("../escape", "/absolute", "a//b", "a/./b", "a\\b", "a/", "\u00e9"):
            with self.subTest(path=path), self.assertRaisesRegex(AI.Refusal, "unsafe repository path"):
                AI._safe_relative(path)

    def test_symlink_input_refuses(self):
        with scratch_directory("development-symlink-") as temporary:
            link = Path(temporary) / "input.json"
            link.symlink_to(MANIFEST)
            with self.assertRaisesRegex(AI.Refusal, "unavailable or unsafe"):
                AI._read_regular(link, AI.MAX_JSON_BYTES)

    def test_replacement_race_refuses(self):
        with scratch_directory("development-race-") as temporary:
            target = Path(temporary) / "input.json"
            replacement = Path(temporary) / "replacement.json"
            target.write_bytes(b"{}\n")
            replacement.write_bytes(b'{"changed":true}\n')
            original = AI._read_descriptor

            def replace_after_read(descriptor, limit):
                data, metadata = original(descriptor, limit)
                os.replace(replacement, target)
                return data, metadata

            with mock.patch.object(AI, "_read_descriptor", side_effect=replace_after_read):
                with self.assertRaisesRegex(AI.Refusal, "input changed during read"):
                    AI._read_regular(target, AI.MAX_JSON_BYTES)

    def test_replay_refuses_non_object_artifact_inventory(self):
        inventory = load(DEVELOPMENT_INVENTORY)
        inventory["artifacts"] = 7
        evidence = AI.ROOT / "tmp/elenchus-r3/evidence/development"
        with mock.patch.object(AI, "_read_regular", return_value=canonical(inventory)):
            try:
                AI._load_development_evidence(evidence)
            except AI.Refusal as exc:
                self.assertRegex(str(exc), "inventory identity drift")
            except Exception as exc:
                self.fail(f"malformed inventory escaped refusal as {type(exc).__name__}")
            else:
                self.fail("malformed inventory was accepted")

    def test_atomic_output_round_trip(self):
        with scratch_directory("development-atomic-") as temporary:
            target = Path(temporary) / "result.json"
            AI._atomic_write(target, b'{"generation":1}\n')
            AI._atomic_write(target, b'{"generation":2}\n')
            self.assertEqual(AI._read_regular(target, 1024), b'{"generation":2}\n')


class ResourceBoundTests(DevelopmentFixtureMixin, unittest.TestCase):
    def test_resource_record_accounts_for_every_executed_source_and_process(self):
        record = load(FIXTURES / "evidence/development/resource-samples.json")
        checker_path = "scripts/agent_instruction.py"
        checker = AI._git_blob_at(AI.WAI1_CONTROL_REF, checker_path)
        benchmark = AI._read_regular(Path(AI.__file__), 4 * 1024 * 1024)

        sources = record.get("executable_sources")
        self.assertIsInstance(
            sources,
            list,
            "resource evidence omits the dynamically executed WAI1 checker",
        )
        by_path = {item["path"]: item for item in sources}
        expected = {
            "research/instruction-architecture/benchmark.py": (
                "workbench",
                None,
                benchmark,
            ),
            checker_path: ("pinned-checker", AI.WAI1_CONTROL_REF, checker),
        }
        self.assertEqual(set(by_path), set(expected))
        for path, (kind, ref, source) in expected.items():
            row = by_path[path]
            text = source.decode("utf-8", errors="strict")
            executable_loc = sum(
                bool(line.strip()) and not line.lstrip().startswith("#")
                for line in text.splitlines()
            )
            digest_source = source
            digest_scope = "exact"
            if kind == "workbench":
                self_reference = AI.EXPECTED_DEVELOPMENT_INVENTORY_SHA256.encode(
                    "ascii"
                )
                self.assertEqual(source.count(self_reference), 1)
                digest_source = source.replace(self_reference, b"0" * 64)
                digest_scope = "development-inventory-self-reference-normalised"
            expected_row = {
                "digest_scope": digest_scope,
                "kind": kind,
                "loc": executable_loc,
                "path": path,
                "ref": ref,
                "sha256": hashlib.sha256(digest_source).hexdigest(),
            }
            self.assertEqual(row, expected_row)
        self.assertEqual(
            record["executable_loc"], sum(item["loc"] for item in sources)
        )

        standard = set()
        external = set()
        for path, (_, _, source) in expected.items():
            source_standard, source_external = AI._runtime_dependency_modules(
                source.decode("utf-8", errors="strict"), filename=path
            )
            standard.update(source_standard)
            external.update(source_external)
        self.assertFalse(external)
        self.assertEqual(
            record["dependency_modules"]["standard_library"], sorted(standard)
        )
        self.assertEqual(record["dependency_modules"]["external_runtime"], ["git"])
        self.assertEqual(record["dependency_count"]["external_runtime"], 1)

    def test_resource_record_freezes_workload_limits_loc_and_dependencies(self):
        record = load(FIXTURES / "evidence/development/resource-samples.json")
        self.assertEqual(record["dependency_count"]["external_runtime"], 1)
        self.assertGreater(record["dependency_count"]["standard_library_modules"], 0)
        self.assertIn("dependency_modules", record)
        self.assertEqual(record["dependency_modules"]["external_runtime"], ["git"])
        self.assertEqual(
            record["dependency_count"]["standard_library_modules"],
            len(record["dependency_modules"]["standard_library"]),
        )
        self.assertGreater(record["executable_loc"], 0)
        self.assertGreater(record["artifact_payload_bytes"], 0)
        snapshot = record["control_snapshot"]
        self.assertEqual(snapshot["artifact_records"], 172)
        self.assertEqual(snapshot["objects"], 157)
        self.assertEqual(snapshot["object_bytes"], 2_095_430)
        self.assertEqual(
            snapshot["published_bytes"],
            snapshot["manifest_bytes"] + snapshot["object_bytes"],
        )
        self.assertEqual(
            snapshot["manifest_sha256"], AI.EXPECTED_CONTROL_SNAPSHOT_SHA256
        )
        self.assertEqual([item["phase"] for item in record["samples"]], ["parse-validate", "select", "assemble"])

    def test_resource_record_reconciles_the_complete_published_generation(self):
        record = load(FIXTURES / "evidence/development/resource-samples.json")
        inventory = load(DEVELOPMENT_INVENTORY)
        disk = record.get("disk_bytes")
        self.assertIsInstance(
            disk,
            dict,
            "resource record reports a preliminary payload subtotal as disk bytes",
        )
        payload_bytes = sum(
            (FIXTURES / relative).stat().st_size for relative in inventory["artifacts"]
        )
        inventory_bytes = DEVELOPMENT_INVENTORY.stat().st_size
        self.assertEqual(disk["artifact_payloads"], payload_bytes)
        self.assertEqual(disk["artifact_inventory"], inventory_bytes)
        self.assertEqual(disk["published_generation"], payload_bytes + inventory_bytes)

    def test_dependency_counts_are_ast_derived_and_external_imports_fail_closed(self):
        classifier = getattr(AI, "_runtime_dependency_modules", None)
        self.assertIsNotNone(
            classifier, "resource evidence hardcodes zero external dependencies"
        )
        standard, external = classifier(
            "import os, requests\nfrom pathlib import Path\nfrom vendor.pkg import value\n"
        )
        self.assertEqual(standard, ["os", "pathlib"])
        self.assertEqual(external, ["requests", "vendor"])

    def test_json_depth_and_model_output_byte_limits_refuse(self):
        deep = b'{"x":' + b"[" * (AI.MAX_JSON_DEPTH + 1) + b"0" + b"]" * (AI.MAX_JSON_DEPTH + 1) + b"}\n"
        with self.assertRaisesRegex(AI.Refusal, "depth"):
            AI._decode_record(deep)
        with self.assertRaisesRegex(AI.Refusal, "model output exceeds"):
            AI._validate_model_output(b"0" * (AI.MAX_MODEL_OUTPUT_BYTES + 1))

    def test_section_and_prompt_count_limits_refuse(self):
        hostile = b"# x\n" * (AI.MAX_SECTION_COUNT + 1)
        with self.assertRaisesRegex(AI.Refusal, "physical line count|section count"):
            AI._markdown_sections("hostile.md", hostile)
        component = {
            "content": "x",
            "encoding": "exact-source",
            "id": "x",
            "kind": "representation",
            "source": {"end": 1, "path": "AGENTS.md", "sha256": "0" * 64, "start": 0},
        }
        prompt = {
            "case_id": "x",
            "components": [component] * (AI.MAX_PROMPT_COMPONENTS + 1),
            "scenario_id": "x",
            "schema": f"{AI.SCHEMA_PREFIX}-prompt/v1",
            "sha256": "0" * 64,
        }
        with self.assertRaisesRegex(AI.Refusal, "component count"):
            AI._validate_prompt(prompt)

    def test_section_parser_refuses_excess_physical_lines(self):
        hostile = b"\n" * (AI.MAX_MARKDOWN_PHYSICAL_LINES + 1)
        with self.assertRaisesRegex(AI.Refusal, "physical line count"):
            AI._markdown_sections("hostile.md", hostile)

    def test_committed_inventory_binds_all_fifteen_payloads(self):
        inventory = load(DEVELOPMENT_INVENTORY)
        self.assertEqual(set(inventory["artifacts"]), set(AI.DEVELOPMENT_RECORD_PATHS))
        self.assertEqual(len(inventory["artifacts"]), 15)
        for relative, identity in inventory["artifacts"].items():
            path = FIXTURES / relative
            self.assertEqual(path.stat().st_size, identity["bytes"])
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), identity["sha256"])


class ExperimentFixtureMixin:
    @classmethod
    def setUpClass(cls):
        cls.selection = load(DEVELOPMENT_SELECTION)
        cls.preregistration = load(PREREGISTRATION)
        cls.model_manifest = load(MODEL_RUNTIME_MANIFEST)
        cls.scorer = load(SCORER)
        cls.native_preregistration = load(NATIVE_PREREGISTRATION)
        cls.native_manifest = load(NATIVE_RUNTIME_MANIFEST)
        cls.accounting = load(NATIVE_CACHE_ACCOUNTING)


class DevelopmentAggregateTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_development_aggregate_reconciles_every_arm_and_denominator(self):
        try:
            AI._validate_development_selection(self.selection)
        except AI.Refusal as exc:
            cause = exc.__cause__
            if (
                str(exc) == "development selection repository evidence is malformed"
                and isinstance(cause, AI.Refusal)
                and str(cause)
                == "development inventory differs from its frozen digest"
            ):
                self.fail("development evidence requires the current frozen validator")
            raise
        self.assertEqual(
            [item["arm"] for item in self.selection["arms"]],
            list(AI.DEVELOPMENT_ARMS),
        )
        for item in self.selection["arms"]:
            coverage = item["coverage"]
            cases = coverage["cases"]
            self.assertLessEqual(coverage["exact_source_recovery_cases"], cases)
            self.assertLessEqual(coverage["native_exact_source_recovery_cases"], cases)
            self.assertLessEqual(coverage["native_mapping_cases"], cases)
            self.assertGreater(item["maximum_complete_prompt_bytes"], 0)
            for count in item["token_counts"]:
                self.assertEqual(
                    count["aggregation"],
                    "sum-of-complete-prompts-with-no-cross-case-merges",
                )

    def test_live_measurements_are_not_claimed_rebuild_identical(self):
        identity = self.selection["measurement_identity"]
        self.assertTrue(identity["live_peak_rss_and_timing_are_observations"])
        self.assertTrue(identity["selection_rebuild_is_not_claimed_byte_identical"])
        self.assertTrue(identity["committed_selection_is_bound_by_digest"])

    def test_nonlist_development_nominee_refuses_before_membership(self):
        for malformed in (None, 0, True):
            with self.subTest(malformed=malformed):
                changed = copy.deepcopy(self.selection)
                changed["development_nominee"] = malformed
                changed.pop("sha256")
                changed = AI._digested_record(changed)
                try:
                    AI._validate_development_selection_structure(changed)
                except Exception as exc:
                    self.assertIsInstance(exc, AI.Refusal)
                else:
                    self.fail("malformed development nominee set was accepted")

    def test_development_selection_replays_repository_owned_evidence(self):
        changed = copy.deepcopy(self.selection)
        changed["development_evidence_sha256"] = "0" * 64
        changed.pop("sha256")
        substitutions = [("inventory", AI._digested_record(changed))]

        changed = copy.deepcopy(self.selection)
        changed["arms"][0]["control_sha256"] = "0" * 64
        changed.pop("sha256")
        substitutions.append(("control", AI._digested_record(changed)))

        arms = copy.deepcopy(self.selection["arms"])
        wai1 = next(item for item in arms if item["arm"] == "wai1")
        wai1["deterministic_critical_failure"] = False
        wai1["failure_causes"] = []
        substitutions.append(
            (
                "derived-critical-state",
                AI._selection_from_development(
                    arms,
                    self.selection["development_evidence_sha256"],
                    self.selection["resources"],
                ),
            )
        )
        malformed_observation = copy.deepcopy(self.selection["arms"])
        malformed_observation[0]["timing"] = {}
        with self.assertRaisesRegex(AI.Refusal, "timing observation"):
            AI._selection_from_development(
                malformed_observation,
                self.selection["development_evidence_sha256"],
                self.selection["resources"],
            )
        for field, value in (
            ("complete_assembled_bytes", "not-an-integer"),
            ("coverage", []),
            ("failure_causes", None),
            ("operational_feasibility", []),
        ):
            with self.subTest(hostile_field=field):
                malformed = copy.deepcopy(self.selection)
                malformed["arms"][0][field] = value
                malformed.pop("sha256")
                malformed = AI._digested_record(malformed)
                try:
                    AI._validate_development_selection_structure(malformed)
                except Exception as exc:
                    self.assertIsInstance(exc, AI.Refusal)
                else:
                    self.fail("malformed selection arm was accepted")
        for label, substituted in substitutions:
            with self.subTest(label=label):
                with self.assertRaisesRegex(AI.Refusal, "repository inputs"):
                    AI._validate_development_selection(substituted)

    def test_research_report_replays_current_artifact_identities(self):
        report = RESEARCH_REPORT.read_text(encoding="utf-8")
        expected = (
            hashlib.sha256(DEVELOPMENT_INVENTORY.read_bytes()).hexdigest(),
            load(DEVELOPMENT_SELECTION)["sha256"],
            hashlib.sha256(HOLDOUT_PACKET_COMMITMENT.read_bytes()).hexdigest(),
            hashlib.sha256(NATIVE_PACKET_COMMITMENT.read_bytes()).hexdigest(),
        )
        for digest in expected:
            with self.subTest(digest=digest):
                self.assertIn(f"`{digest}`", report)

    def test_source_edit_measurement_executes_both_mutations_for_every_arm(self):
        builder = AI._source_edit_amplification
        raw_result = load(DEVELOPMENT_RESULTS["raw"])
        if builder.__code__.co_argcount == 1:
            measured = builder(raw_result)
        else:
            measured = builder(
                "raw",
                raw_result,
                load(DEVELOPMENT_CASES),
                load(DEVELOPMENT_CONTROLS["raw"]),
            )
        self.assertEqual(
            measured.get("mutation_classes"),
            ["one-byte-replacement", "version-length-insertion"],
        )
        self.assertEqual(measured.get("samples"), 2 * len(AI.DEVELOPMENT_CLASSES))
        self.assertEqual(
            measured.get("rebind_attempts", {}).get("successful"), 0
        )
        for arm in self.selection["arms"]:
            measurement = arm["source_edit_amplification"]
            with self.subTest(arm=arm["arm"]):
                self.assertEqual(
                    measurement.get("mutation_classes"),
                    ["one-byte-replacement", "version-length-insertion"],
                )
                self.assertEqual(
                    measurement.get("samples"), 2 * len(AI.DEVELOPMENT_CLASSES)
                )
                self.assertEqual(
                    measurement.get("rebind_attempts", {}).get("successful"), 0
                )
                self.assertTrue(measurement.get("touched_artifacts"))
                self.assertTrue(
                    measurement.get("rebind_attempts", {}).get("failure_messages")
                )


class CandidateSelectionTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_simple_control_is_a_valid_provisional_winner(self):
        self.assertEqual(self.selection["development_nominee"], ["simple"])
        self.assertIn("simple", self.selection["development_frontier"])
        self.assertEqual(self.selection["mandatory_native_baselines"], ["raw", "simple"])

    def test_deterministic_critical_failure_cannot_be_nominated(self):
        failed = {
            item["arm"]
            for item in self.selection["arms"]
            if item["deterministic_critical_failure"]
        }
        self.assertEqual(failed, {"wai1"})
        self.assertTrue(failed.isdisjoint(self.selection["development_nominee"]))

    def test_legacy_prompt_ratio_is_descriptive_and_never_a_veto(self):
        changed = copy.deepcopy(self.selection["arms"])
        raw = next(item for item in changed if item["arm"] == "raw")
        raw["complete_assembled_bytes"] *= 100
        rebuilt = AI._selection_from_development(
            changed,
            self.selection["development_evidence_sha256"],
            self.selection["resources"],
        )
        self.assertFalse(rebuilt["legacy_prompt_ratios"]["admission_veto"])
        self.assertEqual(rebuilt["development_nominee"], ["simple"])


class AdmissionRuleTests(ExperimentFixtureMixin, unittest.TestCase):
    def admitted(self, rows):
        try:
            return AI.admitted_native_arms(self.selection, rows)
        except AI.Refusal as exc:
            cause = exc.__cause__
            if (
                str(exc) == "development selection repository evidence is malformed"
                and isinstance(cause, AI.Refusal)
                and str(cause)
                == "development inventory differs from its frozen digest"
            ):
                self.fail("admission evidence requires the current frozen validator")
            raise

    def rows(self):
        return [
            {
                "arm": arm,
                "behavior_equal": True,
                "paired_interval_overlaps_frontier": False,
                "sole_compatible_survivor": False,
                "strictly_dominated_on_available_token_axes": True,
            }
            for arm in AI.DEVELOPMENT_ARMS
        ]

    def test_interval_overlap_requires_admission(self):
        rows = self.rows()
        next(row for row in rows if row["arm"] == "noema")[
            "paired_interval_overlaps_frontier"
        ] = True
        self.assertIn("noema", self.admitted(rows))

    def test_sole_compatible_survivor_requires_admission(self):
        rows = self.rows()
        next(row for row in rows if row["arm"] == "section-graph")[
            "sole_compatible_survivor"
        ] = True
        self.assertIn("section-graph", self.admitted(rows))

    def test_unknown_behavior_is_not_equal_and_critical_failure_stays_excluded(self):
        rows = self.rows()
        noema = next(row for row in rows if row["arm"] == "noema")
        noema["behavior_equal"] = None
        noema["paired_interval_overlaps_frontier"] = True
        wai1 = next(row for row in rows if row["arm"] == "wai1")
        wai1["sole_compatible_survivor"] = True
        admitted = self.admitted(rows)
        self.assertNotIn("noema", admitted)
        self.assertNotIn("wai1", admitted)

    def test_unhashable_behavioral_arm_refuses(self):
        try:
            AI.admitted_native_arms(self.selection, [{"arm": []}])
        except AI.Refusal as exc:
            self.assertRegex(str(exc), "unknown arm")
        except Exception as exc:
            self.fail(f"unhashable arm escaped as {type(exc).__name__}")
        else:
            self.fail("unhashable arm was accepted")


class PreregistrationTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_behavioral_preregistration_binds_full_answer_matrix(self):
        seal = load(SEAL)
        try:
            AI._validate_behavioral_preregistration(self.preregistration, seal)
        except AI.Refusal as exc:
            self.fail(f"frozen behavioral preregistration refused: {exc}")
        self.assertEqual(self.preregistration["logical_calls_before_retries"], 1120)
        self.assertEqual(len(self.preregistration["case_slots"]), 16)
        self.assertEqual(len(self.preregistration["arms"]), 5)
        self.assertEqual(len(self.model_manifest["models"]), 7)
        self.assertEqual(
            self.preregistration["pair_comparability"].get("required_arm_set"),
            list(AI.DEVELOPMENT_ARMS),
        )

    def test_experiment_schema_closes_every_declared_object(self):
        schema = load(EXPERIMENT_SCHEMA)
        refs = {item["$ref"] for item in schema["oneOf"]}
        self.assertIn("#/$defs/developmentSelection", refs)
        self.assertIn("#/$defs/nativePreregistration", refs)

        def walk(value):
            if isinstance(value, dict):
                if value.get("type") == "object":
                    self.assertFalse(value.get("additionalProperties", True))
                    self.assertNotIn("patternProperties", value)
                    self.assertEqual(
                        set(value.get("required", [])),
                        set(value.get("properties", {})),
                    )
                    self.assertNotIn("hostile_extra", value["properties"])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(schema)

    def test_behavioral_preregistration_replays_every_repository_input_binding(self):
        seal = load(SEAL)
        base = copy.deepcopy(self.preregistration)
        base["pair_comparability"]["required_arm_set"] = list(AI.DEVELOPMENT_ARMS)
        mutations = []
        for path in (
            ("model_runtime_manifest_sha256",),
            ("prompt_template_sha256",),
            ("scorer_sha256",),
            ("arms", 0, "control_sha256"),
        ):
            changed = copy.deepcopy(base)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = "0" * 64
            changed.pop("sha256")
            mutations.append((path, AI._digested_record(changed)))
        for path, changed in mutations:
            with self.subTest(path=path):
                with self.assertRaisesRegex(AI.Refusal, "repository inputs"):
                    AI._validate_behavioral_preregistration(changed, seal)

    def test_experiment_schema_has_no_wildcard_extra_key_escape(self):
        schema = load(EXPERIMENT_SCHEMA)

        def walk(value):
            if isinstance(value, dict):
                if value.get("type") == "object":
                    properties = value.get("properties", {})
                    hostile = dict.fromkeys(properties, None)
                    hostile["hostile_extra"] = "accepted-by-old-patternProperties"
                    admitted = {
                        key
                        for key in hostile
                        if key in properties
                        or any(
                            re.fullmatch(pattern, key)
                            for pattern in value.get("patternProperties", {})
                        )
                    }
                    self.assertNotIn("hostile_extra", admitted)
                    self.assertFalse(value["additionalProperties"])
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(schema)

    def test_post_freeze_rule_change_invalidates_selection(self):
        changed = copy.deepcopy(self.selection)
        changed["admission_rule"]["final_architecture_decided"] = True
        with self.assertRaisesRegex(AI.Refusal, "digest drift"):
            AI._validate_development_selection(changed)

    def test_model_id_substitution_refuses(self):
        changed = copy.deepcopy(self.model_manifest)
        changed["models"][0]["id"] = "anthropic/substitute"
        with self.assertRaisesRegex(AI.Refusal, "matrix drift"):
            AI._validate_model_runtime_manifest(changed)

    def test_batching_is_one_tuple_in_an_immutable_full_permutation(self):
        batching = self.model_manifest["batching"]
        self.assertEqual(batching["logical_calls_per_batch"], 1)
        self.assertEqual(batching["batch_count"], 1120)
        self.assertEqual(batching["block_count"], 224)
        self.assertEqual(batching["block_size"], 5)
        self.assertFalse(batching["may_reorder_or_shrink"])
        packet = load(FROZEN_PACKET_ROOT / "packet.json")
        order = packet["logical_call_order"]
        self.assertEqual(len(order), 1120)
        self.assertEqual(
            [item["batch_index"] for item in order], list(range(1120))
        )
        pair_counts = {}
        for item in order:
            pair_counts[item["pair_id"]] = pair_counts.get(item["pair_id"], 0) + 1
        self.assertEqual(set(pair_counts.values()), {5})
        for offset in range(0, len(order), 5):
            block = order[offset : offset + 5]
            self.assertEqual(len({item["pair_id"] for item in block}), 1)
            self.assertEqual([item["arm_index"] for item in block], list(range(5)))
            self.assertEqual(
                {item["block_index"] for item in block}, {offset // 5}
            )


class BehavioralCaseGeneratorTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_post_freeze_generator_mutation_refuses_after_coherent_reseal(self):
        changed = copy.deepcopy(self.preregistration)
        changed["case_generator"]["algorithm"] = "mutable-after-open"
        changed.pop("sha256")
        changed = AI._digested_record(changed)
        with self.assertRaisesRegex(
            AI.Refusal, "case generator drift|differs from repository inputs"
        ):
            AI._validate_behavioral_preregistration(changed, load(SEAL))

    def test_synthetic_exact_literal_is_objective_and_source_bound(self):
        skill_path = "plugins/probitas/skills/probitas/SKILL.md"
        fixed_path = ".python-version"
        skill_raw = b"source-owned obligation"
        fixed_raw = b"3.14.6\n"
        evidence = {
            "end": len(skill_raw),
            "obligation": skill_path,
            "path": skill_path,
            "source_sha256": hashlib.sha256(skill_raw).hexdigest(),
            "span_sha256": hashlib.sha256(skill_raw).hexdigest(),
            "start": 0,
        }
        profiles = {
            "profiles": [
                {
                    "applicability": "bounded-operation:probitas:add venue",
                    "branch_state": ["add-venue"],
                    "fixed_inputs": [
                        {"load_semantics": "mandatory-executable", "path": fixed_path}
                    ],
                    "id": "probitas:add-venue",
                    "phase": "add venue",
                    "required_documents": [fixed_path, skill_path],
                    "selected_skill": "probitas",
                    "source_evidence": [evidence],
                }
            ],
            "source_ref": AI.SOURCE_REF,
        }
        manifest = {
            "documents": [
                {
                    "bytes": len(fixed_raw),
                    "path": fixed_path,
                    "sha256": hashlib.sha256(fixed_raw).hexdigest(),
                }
            ],
            "source": {"ref": AI.SOURCE_REF},
        }
        plan = {
            "corpus_manifest_sha256": AI._artifact_digest(manifest),
            "generator_sha256": "1" * 64,
            "invocation_profiles_sha256": AI._artifact_digest(profiles),
            "logical_skill": "probitas",
            "profile_selection_seed": "2" * 64,
            "response_schema": AI._behavioral_response_schema(
                "exact-literal", "structured-plan"
            ),
            "response_shape": "structured-plan",
            "scorer_sha256": "3" * 64,
            "semantic_class": "exact-literal",
            "slot_id": "synthetic-01",
            "witness_rule": AI.SEMANTIC_WITNESS_RULES["exact-literal"],
        }
        materialized = AI.materialize_behavioral_case(
            plan,
            profiles,
            manifest,
            {skill_path: skill_raw, fixed_path: fixed_raw},
        )
        self.assertNotIn("3.14.6", materialized["task"])
        self.assertEqual(
            materialized["oracle"]["result"]["fixed_input"]["text"],
            "3.14.6\n",
        )
        score = AI.score_behavioral_response(
            materialized["oracle"], AI._canonical_json(materialized["oracle"])
        )
        self.assertTrue(score["success"])
        adversarial = {**materialized["oracle"], "success": True}
        score = AI.score_behavioral_response(
            materialized["oracle"], AI._canonical_json(adversarial)
        )
        self.assertFalse(score["success"])
        self.assertTrue(score["critical_policy_violation"])
        with self.assertRaisesRegex(AI.Refusal, "differs from its manifest"):
            AI.materialize_behavioral_case(
                plan,
                profiles,
                manifest,
                {skill_path: skill_raw, fixed_path: b"3.13.0\n"},
            )

    def test_pair_comparability_qualifies_both_unknown_but_refuses_one_known(self):
        rows = [
            {
                "arm": arm,
                "model_id": "m",
                "provider_name": "p",
                "model_revision": None,
                "tokenizer_digest": None,
            }
            for arm in AI.DEVELOPMENT_ARMS
        ]
        observed = AI.behavioral_pair_comparability(rows)
        self.assertTrue(observed["comparable"])
        self.assertFalse(observed["token_pooling_allowed"])
        rows[0]["model_revision"] = "r1"
        self.assertFalse(AI.behavioral_pair_comparability(rows)["comparable"])

    def test_pair_comparability_refuses_non_object_rows(self):
        try:
            AI.behavioral_pair_comparability([None] * len(AI.DEVELOPMENT_ARMS))
        except AI.Refusal as exc:
            self.assertRegex(str(exc), "malformed")
        except Exception as exc:
            self.fail(f"malformed row escaped as {type(exc).__name__}")
        else:
            self.fail("malformed row was accepted")

    def test_pair_comparability_requires_closed_arms_and_valid_identity_types(self):
        rows = [
            {
                "arm": arm,
                "model_id": "m",
                "provider_name": "p",
                "model_revision": None,
                "tokenizer_digest": None,
            }
            for arm in AI.DEVELOPMENT_ARMS
        ]
        duplicated = [dict(rows[0]) for _ in AI.DEVELOPMENT_ARMS]
        with self.assertRaisesRegex(AI.Refusal, "one row per frozen arm"):
            AI.behavioral_pair_comparability(duplicated)
        rows[0]["model_revision"] = 7
        observed = AI.behavioral_pair_comparability(rows)
        self.assertFalse(observed["comparable"])
        self.assertEqual(observed["identity_quality"], "model_revision-unknown")

    def test_pair_comparability_rejects_blank_identity_values(self):
        rows = [
            {
                "arm": arm,
                "model_id": "m",
                "provider_name": "p",
                "model_revision": None,
                "tokenizer_digest": None,
            }
            for arm in AI.DEVELOPMENT_ARMS
        ]
        for field in (
            "model_id",
            "provider_name",
            "model_revision",
            "tokenizer_digest",
        ):
            changed = copy.deepcopy(rows)
            for row in changed:
                row[field] = " \t "
            with self.subTest(field=field):
                observed = AI.behavioral_pair_comparability(changed)
                self.assertFalse(observed["comparable"])
                self.assertIn("unknown", observed["identity_quality"])


class PromptContaminationTests(unittest.TestCase):
    def test_scorer_and_answer_material_refuse_in_behavioral_prompt(self):
        raw = PROMPT_TEMPLATE.read_bytes()
        for contamination in (b"\nexpected_answer\n", b"\nscorer_key\n"):
            with self.subTest(contamination=contamination):
                with self.assertRaisesRegex(AI.Refusal, "contaminated"):
                    AI._validate_behavioral_prompt_template(raw + contamination)

    def test_competing_representation_name_refuses_in_native_prompt(self):
        raw = NATIVE_PROMPT_TEMPLATE.read_bytes()
        with self.assertRaisesRegex(AI.Refusal, "forbidden material"):
            AI._validate_native_prompt_template(raw + b"\nnoema\n")

    def test_unstable_prefix_order_refuses(self):
        raw = NATIVE_PROMPT_TEMPLATE.read_text(encoding="utf-8")
        changed = raw.replace("{{representation}}", "TEMP", 1).replace(
            "{{task_suffix}}", "{{representation}}", 1
        ).replace("TEMP", "{{task_suffix}}", 1)
        with self.assertRaisesRegex(AI.Refusal, "stable prefix|placeholders"):
            AI._validate_native_prompt_template(changed.encode())

    def test_native_prompt_partition_freezes_prefix_once_and_suffix_per_turn(self):
        partitioner = getattr(AI, "_native_prompt_partition", None)
        self.assertIsNotNone(partitioner)
        partition = partitioner(NATIVE_PROMPT_TEMPLATE.read_bytes())
        self.assertEqual(partition["stable_prefix_injections_per_chain"], 1)
        self.assertEqual(
            partition["first_turn_input"], "{stable_prefix}{task_suffix}"
        )
        self.assertEqual(partition["continuation_input"], "{task_suffix}")
        self.assertNotEqual(
            partition["stable_prefix_template_sha256"],
            partition["task_suffix_template_sha256"],
        )


class StatisticsTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_exact_loss_event_bound_is_powered_at_frozen_pair_count(self):
        minimum = AI._minimum_zero_event_pairs(
            AI.BEHAVIORAL_ALPHA, AI.BEHAVIORAL_MAX_DEGRADATION
        )
        self.assertEqual(minimum, 149)
        self.assertGreater(
            AI.paired_degradation_upper_bound(0, minimum - 1),
            AI.BEHAVIORAL_MAX_DEGRADATION,
        )
        self.assertLessEqual(
            AI.paired_degradation_upper_bound(0, minimum),
            AI.BEHAVIORAL_MAX_DEGRADATION,
        )

    def test_estimand_is_raw_only_loss_not_net_paired_difference(self):
        self.assertIn("raw-only success", self.scorer["aggregation"]["degradation_event"])
        estimand = self.scorer["aggregation"]["estimand"]
        self.assertIn("raw-only loss probability", estimand)
        self.assertIn("net paired success-rate difference", estimand)

    def test_heterogeneous_bound_requires_zero_events_and_independent_dispatch(self):
        with self.assertRaisesRegex(AI.Refusal, "only for zero events"):
            AI.paired_degradation_upper_bound(1, 224)
        self.assertEqual(
            AI.behavioral_inferential_gate(
                0, 224, independent_stateless_dispatch=False
            )["status"],
            "inconclusive",
        )
        self.assertEqual(
            AI.behavioral_inferential_gate(
                0, 224, independent_stateless_dispatch=True
            )["status"],
            "pass",
        )
        self.assertEqual(
            AI.behavioral_inferential_gate(
                1, 224, independent_stateless_dispatch=True
            )["status"],
            "fail",
        )

    def test_underpowered_zero_event_sample_remains_inconclusive(self):
        observed = AI.behavioral_inferential_gate(
            0, 148, independent_stateless_dispatch=True
        )
        self.assertEqual(observed["status"], "inconclusive")
        self.assertGreater(
            AI.Decimal(observed["upper_bound"]),
            AI.BEHAVIORAL_MAX_DEGRADATION,
        )


class BudgetLedgerTests(unittest.TestCase):
    def setUp(self):
        self.authority = authority_fixture()

    def test_missing_fee_refuses(self):
        changed = copy.deepcopy(self.authority)
        changed["reservation"].pop("fee_rate")
        with self.assertRaisesRegex(AI.Refusal, "fee is missing"):
            AI._validate_authority(changed, AI.Decimal("4500.00"))

    def test_over_budget_reservation_refuses(self):
        with self.assertRaisesRegex(AI.Refusal, "exceeds"):
            AI.budget_reservation(self.authority, AI.Decimal("4500.01"))

    def test_lost_attempt_stays_in_gross_exposure(self):
        ledger = {
            "reserved_gross": "7.50",
            "settled_gross": "1.00",
            "uncertain_gross": "2.00",
        }
        observed = AI.budget_attempt_outcome(ledger, AI.Decimal("7.50"), "lost")
        self.assertEqual(observed["reserved_gross"], "0.00")
        self.assertEqual(observed["uncertain_gross"], "9.50")


class ConformanceOverlayTests(unittest.TestCase):
    def setUp(self):
        required_paths = (
            CONFORMANCE_CONTRACT,
            CONFORMANCE_CONTRACT_SCHEMA,
            CONFORMANCE_OVERLAY_SCHEMA,
        )
        required_symbols = (
            "CONFORMANCE_OVERLAY",
            "STEP4_GATED_COMMANDS",
            "_requires_step4_conformance",
            "_validate_conformance_contract",
            "build_conformance_overlay",
        )
        missing = [str(path) for path in required_paths if not path.is_file()]
        missing.extend(name for name in required_symbols if not hasattr(AI, name))
        if not missing:
            return
        causal = {
            "test_contract_closes_exact_three_by_three_commands_and_immutable_base",
            "test_every_step4_effect_boundary_checks_controller_before_parsing",
        }
        if self._testMethodName in causal:
            self.fail("parent lacks the tracked conformance overlay gate")
        self.skipTest("requires the tracked conformance overlay gate")

    def contract(self):
        return load(CONFORMANCE_CONTRACT)

    @contextmanager
    def exact_private_inputs(self, *, omit_evidence=None, stale_command=None):
        with tempfile.TemporaryDirectory(prefix="step3-conformance-") as temporary:
            root = Path(temporary)
            (root / ".hexaemeron/design-reports").mkdir(parents=True)
            (root / ".fiat").mkdir()
            contract = copy.deepcopy(self.contract())
            base = {
                "results": [
                    {
                        "candidate": row["candidate"],
                        "criterion": row["criterion"],
                        "state": "pending",
                        **row["base_pending"],
                    }
                    for row in contract["rows"]
                    if row["base_pending"] is not None
                ],
                "schema": "protasis-design-evidence/v1",
            }
            base_raw = (json.dumps(base, indent=2, sort_keys=True) + "\n").encode()
            contract["base"]["sha256"] = hashlib.sha256(base_raw).hexdigest()
            contract_raw = canonical(contract)
            (root / ".fiat/conformance-overlay-contract.json").write_bytes(contract_raw)
            (root / ".hexaemeron/design-evidence.json").write_bytes(base_raw)
            for row in contract["rows"]:
                identity = (row["candidate"], row["criterion"])
                command = row["command"]
                if stale_command == identity:
                    command = command.replace("--max-gross-usd 4500", "--max-gross-usd 100")
                report = {
                    "candidate": row["candidate"],
                    "command": command,
                    "criterion": row["criterion"],
                    "exit": 0,
                    "schema": "protasis-design-report/v1",
                    "unit": "boolean",
                    "value": True,
                }
                evidence = AI._digested_record({
                    "candidate": row["candidate"],
                    "criterion": row["criterion"],
                    "facts": row["required_facts"],
                    "invocation": command,
                    "schema": f"{AI.SCHEMA_PREFIX}-preflight-evidence/v1",
                })
                (root / row["report_path"]).write_bytes(canonical(report))
                if omit_evidence != identity:
                    (root / row["evidence_path"]).write_bytes(canonical(evidence))
            with (
                mock.patch.object(AI, "ROOT", root),
                mock.patch.object(
                    AI, "_tracked_conformance_contract", return_value=(contract, contract_raw)
                ),
            ):
                yield root, contract

    def test_contract_closes_exact_three_by_three_commands_and_immutable_base(self):
        contract = self.contract()
        AI._validate_conformance_contract(contract)
        self.assertEqual(len(contract["rows"]), 9)
        self.assertEqual(
            "117dd4d94d8f7b464f069332e0845d3ee9fd789950020a553b6b2096cafa6f48",
            contract["base"]["sha256"],
        )
        self.assertEqual(
            {(row["candidate"], row["criterion"]) for row in contract["rows"]},
            set(itertools.product(contract["candidates"], contract["criteria"])),
        )
        paid = [row for row in contract["rows"] if row["criterion"] == "paid-evaluation-preflight"]
        self.assertTrue(all("--max-gross-usd 4500" in row["command"] for row in paid))
        self.assertTrue(all(
            "--max-gross-usd 100" in row["base_pending"]["resolver"]
            for row in paid
        ))

    def test_overlay_builds_nine_bound_pairs_without_touching_the_immutable_base(self):
        with self.exact_private_inputs() as (root, contract):
            before = (root / contract["base"]["path"]).read_bytes()
            output = root / AI.CONFORMANCE_OVERLAY
            result = AI.build_conformance_overlay(types.SimpleNamespace(output=output))
            record = load(output)
            self.assertEqual(len(record["rows"]), 9)
            self.assertEqual(result.count(b'"sessions_launched":0'), 1)
            self.assertEqual((root / contract["base"]["path"]).read_bytes(), before)
            self.assertEqual(hashlib.sha256(before).hexdigest(), contract["base"]["sha256"])

    def test_private_overlay_changes_only_six_bound_resolvers(self):
        controller = load_hexctl_module()
        with self.exact_private_inputs() as (root, contract):
            base = root / contract["base"]["path"]
            before = base.read_bytes()
            output = root / AI.CONFORMANCE_OVERLAY
            AI.build_conformance_overlay(types.SimpleNamespace(output=output))
            checked = controller._validate_conformance_bundle(
                str(root),
                contract_raw=(root / AI.CONFORMANCE_CONTRACT).read_bytes(),
                overlay_raw=output.read_bytes(),
            )
            original = json.loads(before)
            patched = json.loads(checked["patched_base"])
            self.assertEqual(len(checked["design_reports"]), 6)
            for old, new in zip(original["results"], patched["results"]):
                self.assertEqual(
                    {key: value for key, value in old.items() if key != "resolver"},
                    {key: value for key, value in new.items() if key != "resolver"},
                )
                if old["criterion"] == "paid-evaluation-preflight":
                    self.assertIn("--max-gross-usd 100", old["resolver"])
                else:
                    self.assertEqual(old["resolver"], new["resolver"])
                self.assertEqual(
                    next(
                        row["command"] for row in contract["rows"]
                        if (row["candidate"], row["criterion"])
                        == (old["candidate"], old["criterion"])
                    ),
                    new["resolver"],
                )
            self.assertEqual(base.read_bytes(), before)

    def test_missing_native_evidence_refuses_before_overlay_publication(self):
        identity = ("neutral-evidence-workbench", "native-gate-preflight")
        with self.exact_private_inputs(omit_evidence=identity) as (root, _):
            output = root / AI.CONFORMANCE_OVERLAY
            with self.assertRaisesRegex(AI.Refusal, "unavailable or unsafe"):
                AI.build_conformance_overlay(types.SimpleNamespace(output=output))
            self.assertFalse(output.exists())

    def test_stale_resolver_report_cannot_be_relabelled_by_the_overlay(self):
        identity = ("neutral-evidence-workbench", "paid-evaluation-preflight")
        with self.exact_private_inputs(stale_command=identity) as (root, _):
            output = root / AI.CONFORMANCE_OVERLAY
            with self.assertRaisesRegex(AI.Refusal, "exact frozen pass"):
                AI.build_conformance_overlay(types.SimpleNamespace(output=output))
            self.assertFalse(output.exists())

    def test_partial_or_stale_overlay_is_never_replaced(self):
        with self.exact_private_inputs() as (root, _):
            output = root / AI.CONFORMANCE_OVERLAY
            output.write_bytes(b'{"partial":')
            with self.assertRaisesRegex(AI.Refusal, "stale bytes"):
                AI.build_conformance_overlay(types.SimpleNamespace(output=output))
            self.assertEqual(output.read_bytes(), b'{"partial":')

    def test_changed_immutable_base_refuses_before_overlay_publication(self):
        with self.exact_private_inputs() as (root, contract):
            base = root / contract["base"]["path"]
            base.write_bytes(base.read_bytes() + b" ")
            output = root / AI.CONFORMANCE_OVERLAY
            with self.assertRaisesRegex(AI.Refusal, "base digest changed"):
                AI.build_conformance_overlay(types.SimpleNamespace(output=output))
            self.assertFalse(output.exists())

    def test_every_step4_effect_boundary_checks_controller_before_parsing(self):
        commands = sorted(AI.STEP4_GATED_COMMANDS)
        for command in commands:
            with self.subTest(command=command):
                with (
                    mock.patch.object(
                        AI,
                        "_verify_step4_conformance",
                        side_effect=AI.Refusal("missing"),
                    ) as verify,
                    mock.patch.object(AI, "parser") as parser_mock,
                ):
                    self.assertEqual(AI.main([command]), 2)
                verify.assert_called_once_with()
                parser_mock.assert_not_called()
        self.assertTrue(AI._requires_step4_conformance(["replay", "--cohort", "holdout"]))
        self.assertTrue(AI._requires_step4_conformance(["replay", "--cohort=holdout"]))
        self.assertTrue(AI._requires_step4_conformance(["replay", "--coh", "holdout"]))
        self.assertTrue(AI._requires_step4_conformance([
            "replay", "--cohort", "development", "--cohort", "holdout",
        ]))
        self.assertFalse(AI._requires_step4_conformance(["replay", "--cohort", "development"]))

    def test_step4_checker_requires_the_exact_bounded_controller_result(self):
        valid = {
            "schema": "fiat-conformance-overlay-receipt/v1",
            "transition": "step:4",
            "overlay_sha256": "a" * 64,
            "rows": 9,
            "ledger_entries": 61,
        }
        with mock.patch.object(
            AI,
            "_bounded_process",
            return_value=(0, canonical(valid), b""),
        ):
            AI._verify_step4_conformance()

        hostile = []
        extra = dict(valid)
        extra["unverified"] = True
        hostile.append(extra)
        for field, value in (
            ("rows", True),
            ("ledger_entries", True),
            ("ledger_entries", 0),
            ("ledger_entries", "61"),
        ):
            changed = dict(valid)
            changed[field] = value
            hostile.append(changed)
        for record in hostile:
            with (
                self.subTest(record=record),
                mock.patch.object(
                    AI,
                    "_bounded_process",
                    return_value=(0, canonical(record), b""),
                ),
                self.assertRaisesRegex(AI.Refusal, "wrong receipt"),
            ):
                AI._verify_step4_conformance()

    def test_conformance_schemas_close_every_object(self):
        expected_path = {
            "maxLength": 1024,
            "minLength": 1,
            "pattern": (
                r"^(?!/)(?!.*//)(?!.*(?:^|/)\.\.?(?:/|$))(?!.*\\)"
                r"(?!.*\/$)[\u0020-\u007e]+(?![\s\S])"
            ),
            "type": "string",
        }
        for path in (CONFORMANCE_CONTRACT_SCHEMA, CONFORMANCE_OVERLAY_SCHEMA):
            schema = load(path)
            self.assertEqual(schema["$defs"]["path"], expected_path)

            def walk(value):
                if isinstance(value, dict):
                    if value.get("type") == "object":
                        self.assertFalse(value.get("additionalProperties", True))
                        self.assertEqual(
                            set(value.get("required", [])),
                            set(value.get("properties", {})),
                        )
                    for child in value.values():
                        walk(child)
                elif isinstance(value, list):
                    for child in value:
                        walk(child)

            walk(schema)


class ModelPreflightTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_manifest_requires_one_exact_ordered_policy_and_zdr(self):
        AI._validate_model_runtime_manifest(self.model_manifest)
        self.assertTrue(self.model_manifest["provider"]["zdr"])
        self.assertFalse(self.model_manifest["allow_model_substitution"])
        self.assertTrue(
            all(model["ordered_provider_policy"] for model in self.model_manifest["models"])
        )

    def test_non_zdr_route_refuses_before_report_publication(self):
        model_rows = {
            "data": [
                {
                    "architecture": {"tokenizer": row["tokenizer"]},
                    "context_length": row["context_length"],
                    "id": row["id"],
                    "pricing": {"completion": "0.1", "prompt": "0.1"},
                }
                for row in self.model_manifest["models"]
            ]
        }
        args = types.SimpleNamespace(
            candidate=AI.EVALUATOR_CANDIDATES[0],
            models=",".join(AI.MODEL_IDS),
            require_zdr=True,
            report=ROOT / AI.NATIVE_REPORT_PATHS[AI.EVALUATOR_CANDIDATES[0]],
        )
        with mock.patch.object(AI, "_http_json", side_effect=[model_rows, {"data": []}]):
            with self.assertRaisesRegex(AI.Refusal, "no active frozen ZDR route"):
                AI.preflight_model_matrix(args)

    def test_duplicate_model_catalog_identity_refuses(self):
        rows = [
            {
                "architecture": {"tokenizer": row["tokenizer"]},
                "context_length": row["context_length"],
                "id": row["id"],
                "pricing": {"completion": "0.1", "prompt": "0.1"},
            }
            for row in self.model_manifest["models"]
        ]
        rows.append(
            {
                **copy.deepcopy(rows[0]),
                "architecture": {"tokenizer": "hostile-duplicate"},
            }
        )
        args = types.SimpleNamespace(
            candidate=AI.EVALUATOR_CANDIDATES[0],
            models=",".join(AI.MODEL_IDS),
            require_zdr=True,
            report=ROOT / AI.NATIVE_REPORT_PATHS[AI.EVALUATOR_CANDIDATES[0]],
        )
        with mock.patch.object(
            AI, "_http_json", side_effect=[{"data": rows}, {"data": []}]
        ):
            with self.assertRaisesRegex(AI.Refusal, "duplicate id"):
                AI.preflight_model_matrix(args)

    def test_malformed_zdr_supported_parameters_refuse(self):
        frozen = self.model_manifest["models"][0]
        route = {
            "model_id": frozen["id"],
            "pricing": {"completion": "0.1", "prompt": "0.1"},
            "provider_name": frozen["ordered_provider_policy"][0],
            "status": 0,
            "supported_parameters": None,
        }
        try:
            AI._eligible_zdr_routes(frozen, [route])
        except AI.Refusal as exc:
            self.assertRegex(str(exc), "supported parameters")
        except Exception as exc:
            self.fail(f"malformed supported parameters escaped as {type(exc).__name__}")
        else:
            self.fail("malformed supported parameters were accepted")

    def test_worst_fallback_price_is_reserved(self):
        frozen = self.model_manifest["models"][0]
        routes = [
            {
                "model_id": frozen["id"],
                "pricing": {"prompt": "0.1", "completion": "0.2"},
                "provider_name": frozen["ordered_provider_policy"][0],
                "status": 0,
                "supported_parameters": ["response_format", "structured_outputs"],
            },
            {
                "model_id": frozen["id"],
                "pricing": {"prompt": "0.3", "completion": "0.4"},
                "provider_name": frozen["ordered_provider_policy"][1],
                "status": 0,
                "supported_parameters": ["response_format", "structured_outputs"],
            },
        ]
        self.assertEqual(
            AI._worst_eligible_prices(frozen, routes),
            (AI.Decimal("0.3"), AI.Decimal("0.4")),
        )

    def test_null_key_limit_does_not_replace_credit_balance_proof(self):
        endpoint_rows = {
            "data": [
                {
                    "model_id": row["id"],
                    "pricing": {"completion": "0.000001", "prompt": "0.000001"},
                    "provider_name": row["ordered_provider_policy"][0],
                    "status": 0,
                    "supported_parameters": [
                        "response_format",
                        "structured_outputs",
                    ],
                }
                for row in self.model_manifest["models"]
            ]
        }
        responses = [
            {"data": {"limit_remaining": None, "usage": "1"}},
            {"data": {"total_credits": "1", "total_usage": "1"}},
            endpoint_rows,
        ]
        with scratch_directory("step3-authority-") as directory:
            authority = Path(directory) / "authority.json"
            authority.write_bytes(canonical(authority_fixture()))
            args = types.SimpleNamespace(
                authority=authority,
                candidate=AI.EVALUATOR_CANDIDATES[0],
                max_gross_usd="4500.00",
                report=ROOT
                / ".hexaemeron/design-reports/neutral-evidence-workbench-paid-evaluation-preflight.json",
            )
            with mock.patch.object(AI, "_external_secret", return_value=b"test-key"):
                with mock.patch.object(AI, "_http_json", side_effect=responses):
                    with mock.patch.object(
                        AI, "_publish_preflight_report"
                    ) as publish:
                        with self.assertRaisesRegex(AI.Refusal, "does not cover"):
                            AI.preflight_spend(args)
        publish.assert_not_called()

    def test_key_spend_limit_must_cover_the_next_atomic_reservation(self):
        responses = [
            {"data": {"limit_remaining": "0.50", "usage": "1"}},
            {"data": {"total_credits": "5000", "total_usage": "0"}},
            {"data": []},
        ]
        with scratch_directory("step3-key-limit-") as directory:
            authority = Path(directory) / "authority.json"
            authority.write_bytes(canonical(authority_fixture()))
            args = types.SimpleNamespace(
                authority=authority,
                candidate=AI.EVALUATOR_CANDIDATES[0],
                max_gross_usd="4500.00",
                report=ROOT
                / ".hexaemeron/design-reports/neutral-evidence-workbench-paid-evaluation-preflight.json",
            )
            with (
                mock.patch.object(AI, "_external_secret", return_value=b"test-key"),
                mock.patch.object(AI, "_http_json", side_effect=responses),
                mock.patch.object(
                    AI,
                    "_matrix_gross_bound",
                    return_value=(
                        AI.Decimal("100"),
                        {},
                        AI.Decimal("1"),
                        {"call_id": "frozen"},
                    ),
                ),
                mock.patch.object(AI, "_publish_preflight_report") as publish,
            ):
                with self.assertRaisesRegex(AI.Refusal, "does not cover"):
                    AI.preflight_spend(args)
        publish.assert_not_called()

    def test_missing_key_spend_limit_refuses_before_report_publication(self):
        responses = [
            {"data": {"usage": "1"}},
            {"data": {"total_credits": "5000", "total_usage": "0"}},
            {"data": []},
        ]
        with scratch_directory("step3-missing-key-limit-") as directory:
            authority = Path(directory) / "authority.json"
            authority.write_bytes(canonical(authority_fixture()))
            args = types.SimpleNamespace(
                authority=authority,
                candidate=AI.EVALUATOR_CANDIDATES[0],
                max_gross_usd="4500.00",
                report=ROOT
                / ".hexaemeron/design-reports/neutral-evidence-workbench-paid-evaluation-preflight.json",
            )
            with (
                mock.patch.object(AI, "_external_secret", return_value=b"test-key"),
                mock.patch.object(AI, "_http_json", side_effect=responses),
                mock.patch.object(
                    AI,
                    "_matrix_gross_bound",
                    return_value=(
                        AI.Decimal("100"),
                        {},
                        AI.Decimal("1"),
                        {"call_id": "frozen"},
                    ),
                ),
                mock.patch.object(AI, "_publish_preflight_report") as publish,
            ):
                with self.assertRaisesRegex(AI.Refusal, "omits limit remaining"):
                    AI.preflight_spend(args)
        publish.assert_not_called()


class BoundedProcessTests(unittest.TestCase):
    def test_reaped_leader_with_descendant_held_pipes_still_kills_group(self):
        stdout_read, stdout_write = os.pipe()
        stderr_read, stderr_write = os.pipe()

        class ReapedLeader:
            pid = 424242
            returncode = 0
            stdout = os.fdopen(stdout_read, "rb", buffering=0)
            stderr = os.fdopen(stderr_read, "rb", buffering=0)

            @staticmethod
            def wait(timeout=None):
                return 0

            @staticmethod
            def poll():
                return 0

            @staticmethod
            def kill():
                return None

        leader = ReapedLeader()
        try:
            with mock.patch.object(AI.subprocess, "Popen", return_value=leader):
                with mock.patch.object(AI.os, "killpg") as kill_group:
                    with self.assertRaisesRegex(AI.Refusal, "timed out"):
                        AI._bounded_process(
                            ["fake-runtime"], environment={}, cwd=ROOT, timeout=1
                        )
            kill_group.assert_called_once_with(leader.pid, signal.SIGKILL)
        finally:
            leader.stdout.close()
            leader.stderr.close()
            os.close(stdout_write)
            os.close(stderr_write)


class NativePreflightBoundaryTests(unittest.TestCase):
    def test_system_temp_ignores_repository_tmp_symlink(self):
        with tempfile.TemporaryDirectory(
            prefix="step3-hostile-repository-"
        ) as temporary:
            parent = Path(temporary)
            repository = parent / "repository"
            repository.mkdir()
            redirect = parent / "redirect"
            redirect.mkdir()
            (repository / "tmp").symlink_to(redirect, target_is_directory=True)
            real_temporary_directory = AI.tempfile.TemporaryDirectory

            def system_only(*args, **kwargs):
                self.assertIsNone(kwargs.get("dir"))
                return real_temporary_directory(*args, **kwargs)

            with mock.patch.object(AI, "ROOT", repository):
                with mock.patch.object(
                    AI.tempfile,
                    "TemporaryDirectory",
                    side_effect=system_only,
                ):
                    with AI._private_system_temporary_directory() as private:
                        self.assertEqual(stat.S_IMODE(private.stat().st_mode), 0o700)
                        self.assertFalse(
                            private.resolve().is_relative_to(redirect.resolve())
                        )
                        (private / "marker").write_bytes(b"private")
            self.assertTrue((repository / "tmp").is_symlink())
            self.assertEqual(list(redirect.iterdir()), [])

    def test_auth_copy_compares_opened_source_identity(self):
        with scratch_directory("step3-auth-identity-") as temporary:
            source = Path(temporary) / "auth.json"
            destination = Path(temporary) / "copy.json"
            replacement = Path(temporary) / "replacement.json"
            source.write_bytes(b"secret")
            source.chmod(0o600)
            replacement.write_bytes(b"other")
            replacement.chmod(0o600)
            real_lstat = Path.lstat

            def replaced_identity(candidate):
                if candidate == source:
                    return real_lstat(replacement)
                return real_lstat(candidate)

            with mock.patch.object(
                Path, "lstat", autospec=True, side_effect=replaced_identity
            ):
                with self.assertRaisesRegex(AI.Refusal, "changed during access"):
                    AI._copy_external_auth(source, destination, 64)
            self.assertFalse(destination.exists())

    def test_auth_copy_closes_source_when_destination_open_fails(self):
        with scratch_directory("step3-auth-close-") as temporary:
            source = Path(temporary) / "auth.json"
            destination = Path(temporary) / "copy.json"
            source.write_bytes(b"secret")
            source.chmod(0o600)
            real_open = AI.os.open
            source_descriptor = []

            def guarded_open(path, *args, **kwargs):
                if Path(path) == destination:
                    raise OSError("synthetic destination failure")
                descriptor = real_open(path, *args, **kwargs)
                if Path(path) == source:
                    source_descriptor.append(descriptor)
                return descriptor

            with mock.patch.object(AI.os, "open", side_effect=guarded_open):
                with self.assertRaisesRegex(AI.Refusal, "unavailable or unsafe"):
                    AI._copy_external_auth(source, destination, 64)
            self.assertEqual(len(source_descriptor), 1)
            with self.assertRaises(OSError):
                os.fstat(source_descriptor[0])

    def test_auth_copy_reopens_source_nonblocking_and_nofollow(self):
        with scratch_directory("step3-auth-nonblocking-") as temporary:
            source = Path(temporary) / "auth.json"
            destination = Path(temporary) / "copy.json"
            source.write_bytes(b"secret")
            source.chmod(0o600)
            real_open = AI.os.open

            def guarded_open(path, flags, *args, **kwargs):
                if Path(path) == source:
                    self.assertTrue(flags & os.O_NONBLOCK)
                    self.assertTrue(flags & os.O_NOFOLLOW)
                return real_open(path, flags, *args, **kwargs)

            with mock.patch.object(AI.os, "open", side_effect=guarded_open):
                AI._copy_external_auth(source, destination, 64)
            self.assertEqual(destination.read_bytes(), b"secret")

    def test_external_digest_refuses_named_replacement_during_read(self):
        with scratch_directory("step3-executable-race-") as temporary:
            target = Path(temporary) / "runtime"
            replacement = Path(temporary) / "replacement"
            target.write_bytes(b"original-runtime")
            replacement.write_bytes(b"replacement-runtime")
            target.chmod(0o700)
            replacement.chmod(0o700)
            real_read = AI.os.read
            replaced = False

            def racing_read(descriptor, size):
                nonlocal replaced
                chunk = real_read(descriptor, size)
                if chunk and not replaced:
                    replaced = True
                    os.replace(replacement, target)
                return chunk

            with (
                mock.patch.object(AI.os, "read", side_effect=racing_read),
                self.assertRaisesRegex(AI.Refusal, "changed during (access|hashing)"),
            ):
                AI._external_file_digest(target)

    def test_external_attestation_detects_swap_back(self):
        attester = getattr(AI, "_external_file_attestation", None)
        self.assertIsNotNone(attester)
        with scratch_directory("step3-executable-swap-back-") as temporary:
            root = Path(temporary)
            target = root / "runtime"
            original = root / "original"
            hostile = root / "hostile"
            target.write_bytes(b"original-runtime")
            hostile.write_bytes(b"hostile-runtime")
            target.chmod(0o700)
            hostile.chmod(0o700)
            before = attester(target)
            os.replace(target, original)
            os.replace(hostile, target)
            self.assertEqual(target.read_bytes(), b"hostile-runtime")
            os.replace(target, hostile)
            os.replace(original, target)
            after = attester(target)
            self.assertEqual(before[0], after[0])
            self.assertNotEqual(before[1], after[1])

    def test_external_executable_stage_binds_verified_private_copy(self):
        stage = getattr(AI, "_stage_external_executable", None)
        self.assertIsNotNone(stage)
        with scratch_directory("step3-executable-stage-") as temporary:
            root = Path(temporary)
            private = root / "private"
            private.mkdir(mode=0o700)
            source = root / "runtime"
            source.write_bytes(b"runtime")
            source.chmod(0o700)
            destination = private / "runtime"
            attestation = stage(source, destination)
            self.assertEqual(destination.read_bytes(), b"runtime")
            self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o500)
            self.assertEqual(attestation, AI._external_file_attestation(destination))

    def test_source_swap_back_cannot_change_staged_execution(self):
        stage = getattr(AI, "_stage_external_executable", None)
        self.assertIsNotNone(stage)
        with scratch_directory("step3-executable-stage-swap-back-") as temporary:
            root = Path(temporary)
            private = root / "private"
            private.mkdir(mode=0o700)
            source = root / "runtime"
            original = root / "original"
            hostile = root / "hostile"
            source.write_bytes(b"#!/bin/sh\nprintf 'original\\n'\n")
            hostile.write_bytes(b"#!/bin/sh\nprintf 'hostile\\n'\n")
            source.chmod(0o700)
            hostile.chmod(0o700)
            before = AI._external_file_attestation(source)
            destination = private / "runtime"
            staged = stage(source, destination)
            private.chmod(0o500)
            os.replace(source, original)
            os.replace(hostile, source)
            try:
                code, stdout, stderr = AI._bounded_process(
                    [str(destination)],
                    environment={"LANG": "C", "PATH": os.environ["PATH"]},
                    cwd=root,
                )
            finally:
                os.replace(source, hostile)
                os.replace(original, source)
                private.chmod(0o700)
            after = AI._external_file_attestation(source)
            self.assertEqual(after[0], before[0])
            self.assertEqual(after[1][:-1], before[1][:-1])
            self.assertEqual(staged[0], before[0])
            self.assertEqual((code, stdout, stderr), (0, b"original\n", b""))

    def test_external_digest_refuses_fifo_without_blocking(self):
        with scratch_directory("step3-executable-fifo-") as temporary:
            fifo = Path(temporary) / "runtime"
            os.mkfifo(fifo)
            probe = "\n".join(
                (
                    "from pathlib import Path",
                    "import sys",
                    "from tests.test_instruction_architecture import AI",
                    "try:",
                    "    AI._external_file_digest(Path(sys.argv[1]))",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO executable was accepted')",
                )
            )
            process = subprocess.Popen(
                [sys.executable, "-c", probe, str(fifo)],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                self.fail("executable digest open blocked on a FIFO")
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(stdout.strip(), "external file metadata is unsafe")

    def test_external_digest_refuses_symlink_and_unsafe_mode(self):
        with scratch_directory("step3-executable-kind-") as temporary:
            root = Path(temporary)
            executable = root / "runtime"
            executable.write_bytes(b"runtime")
            executable.chmod(0o700)
            linked = root / "linked-runtime"
            linked.symlink_to(executable)
            with self.assertRaisesRegex(AI.Refusal, "unavailable or unsafe"):
                AI._external_file_digest(linked)
            executable.chmod(0o722)
            with self.assertRaisesRegex(AI.Refusal, "metadata is unsafe"):
                AI._external_file_digest(executable)

    def test_external_process_text_is_strict_utf8(self):
        decoder = getattr(AI, "_decode_external_utf8", None)
        self.assertIsNotNone(decoder)
        with self.assertRaisesRegex(AI.Refusal, "not UTF-8"):
            decoder(b"\xff", "native version output")

    def test_external_secret_refuses_fifo_without_blocking(self):
        with scratch_directory("step3-secret-fifo-") as temporary:
            fifo = Path(temporary) / "credential"
            os.mkfifo(fifo)
            probe = "\n".join(
                (
                    "from pathlib import Path",
                    "import sys",
                    "from tests.test_instruction_architecture import AI",
                    "try:",
                    "    AI._external_secret(str(Path(sys.argv[1]).resolve()))",
                    "except AI.Refusal as exc:",
                    "    print(exc)",
                    "else:",
                    "    raise AssertionError('FIFO credential was accepted')",
                )
            )
            process = subprocess.Popen(
                [sys.executable, "-c", probe, str(fifo)],
                cwd=ROOT,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            try:
                stdout, stderr = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.communicate()
                self.fail("credential open blocked on a FIFO")
            self.assertEqual(process.returncode, 0, stderr)
            self.assertEqual(stdout.strip(), "credential metadata is unsafe")

    def test_external_secret_refuses_symlink_and_directory(self):
        with scratch_directory("step3-secret-kind-") as temporary:
            root = Path(temporary)
            secret = root / "secret"
            secret.write_bytes(b"secret")
            secret.chmod(0o600)
            linked = root / "linked"
            linked.symlink_to(secret)
            for hostile in (linked, root):
                with self.subTest(hostile=hostile):
                    with self.assertRaisesRegex(
                        AI.Refusal, "unavailable or unsafe|metadata is unsafe"
                    ):
                        AI._external_secret(str(hostile))

    def test_generated_schema_walk_refuses_symlink_and_oversized_cardinality(self):
        with scratch_directory("step3-schema-walk-") as temporary:
            root = Path(temporary)
            target = root / "target.json"
            target.write_bytes(b"{}\n")
            (root / "linked.json").symlink_to(target)
            with self.assertRaisesRegex(AI.Refusal, "symlink"):
                AI._read_generated_schema_bundle(root)
        with scratch_directory("step3-schema-count-") as temporary:
            root = Path(temporary)
            for index in range(2049):
                (root / f"{index:04d}.json").write_bytes(b"{}\n")
            with self.assertRaisesRegex(AI.Refusal, "cardinality"):
                AI._read_generated_schema_bundle(root)

    def test_codex_schema_validation_tolerates_exact_external_decimals(self):
        records = linked_codex_schema_records()
        records[0]["value"]["definitions"]["ExternalDecimal"] = {
            "minimum": AI.Decimal("0.1")
        }
        AI._validate_codex_schema_bundle(records)

    def test_codex_schema_tokens_must_be_linked_to_exact_protocol_roots(self):
        tokens = {
            token: {}
            for token in (
                "thread/start",
                "thread/resume",
                "thread/compact/start",
                "turn/start",
                "contextCompaction",
                "inputTokens",
                "cachedInputTokens",
                "cacheWriteInputTokens",
                "outputSchema",
            )
        }
        tokens["request"] = {
            "properties": {
                name: {}
                for name in (
                    "allowProviderModelFallback",
                    "approvalPolicy",
                    "baseInstructions",
                    "cwd",
                    "dynamicTools",
                    "environments",
                    "ephemeral",
                    "experimentalRawEvents",
                    "model",
                    "sandbox",
                )
            }
        }
        with self.assertRaisesRegex(AI.Refusal, "exact ClientRequest.json"):
            AI._validate_codex_schema_bundle(
                [{"path": "unrelated.json", "value": tokens}]
            )

        unlinked = linked_codex_schema_records()
        unlinked[1]["value"]["definitions"][
            "ThreadTokenUsageUpdatedNotification"
        ]["properties"]["tokenUsage"] = []
        with self.assertRaisesRegex(AI.Refusal, "(property|reference) linkage"):
            AI._validate_codex_schema_bundle(unlinked)

        incompatible = linked_codex_schema_records()
        incompatible[0]["value"]["definitions"]["ThreadResumeParams"][
            "properties"
        ]["threadId"] = {"type": "integer"}
        with self.assertRaisesRegex(AI.Refusal, "property type"):
            AI._validate_codex_schema_bundle(incompatible)

        uncorrelated = linked_codex_schema_records()
        uncorrelated[1]["value"]["definitions"][
            "ThreadTokenUsageUpdatedNotification"
        ]["required"] = ["tokenUsage"]
        with self.assertRaisesRegex(AI.Refusal, "object linkage"):
            AI._validate_codex_schema_bundle(uncorrelated)


class NativeRuntimeManifestTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_native_runtime_manifest_is_portable_isolated_and_schema_bound(self):
        try:
            AI._validate_native_runtime_manifest(self.native_manifest)
        except AI.Refusal as exc:
            self.fail(f"frozen native runtime manifest refused: {exc}")
        self.assertNotIn("/Users/", json.dumps(self.native_manifest))
        for runtime in self.native_manifest["runtimes"]:
            self.assertEqual(
                runtime.get("isolated_workspace"),
                {
                    "cwd": "{isolated_workspace}",
                    "mode": "0700",
                    "must_be_fresh_empty_directory": True,
                },
            )
        codex = self.native_manifest["runtimes"][1]
        claude = self.native_manifest["runtimes"][0]
        self.assertEqual(
            claude["invocation"].get("start_input", {}).get("message", {}).get("content"),
            "{stable_prefix}{task_suffix}",
        )
        self.assertEqual(
            claude["invocation"]
            .get("continuation_input", {})
            .get("message", {})
            .get("content"),
            "{task_suffix}",
        )
        params = codex["invocation"]["start_request"]["params"]
        self.assertEqual(params["baseInstructions"], "{stable_prefix}")
        self.assertEqual(
            codex["invocation"]["turn_request"]["params"]["input"][0]["text"],
            "{task_suffix}",
        )
        self.assertFalse(params["ephemeral"])
        self.assertFalse(params["allowProviderModelFallback"])
        self.assertEqual(params["dynamicTools"], [])
        self.assertEqual(params["environments"], [])
        self.assertIn("--experimental", codex["protocol_schema"]["command"])

    def test_enabled_response_reuse_refuses(self):
        changed = copy.deepcopy(self.native_manifest)
        changed["response_reuse"]["enabled"] = True
        with self.assertRaisesRegex(AI.Refusal, "response-cache"):
            AI._validate_native_runtime_manifest(changed)

    def test_mismatched_runtime_id_refuses(self):
        changed = copy.deepcopy(self.native_manifest)
        changed["runtimes"][0]["id"] = "claude-api"
        with self.assertRaisesRegex(AI.Refusal, "identity"):
            AI._validate_native_runtime_manifest(changed)

    def test_safe_invocation_values_are_exactly_committed(self):
        mutations = []

        changed = copy.deepcopy(self.native_manifest)
        changed["runtimes"][1]["invocation"]["start_request"]["params"][
            "sandbox"
        ] = "danger-full-access"
        mutations.append(changed)

        changed = copy.deepcopy(self.native_manifest)
        changed["runtimes"][1]["invocation"]["start_request"]["params"][
            "approvalPolicy"
        ] = "on-request"
        mutations.append(changed)

        for replacement in (
            ["-p", "--permission-mode", "bypassPermissions"],
            ["-p", "--safe-mode", "--tools", "Bash"],
        ):
            changed = copy.deepcopy(self.native_manifest)
            changed["runtimes"][0]["invocation"]["common_argv"] = replacement
            mutations.append(changed)

        for changed in mutations:
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(AI.Refusal, "safe invocation"):
                    AI._validate_native_runtime_manifest(changed)

    def test_claude_stable_prefix_reinjection_contract_refuses(self):
        changed = copy.deepcopy(self.native_manifest)
        continuation = changed["runtimes"][0]["invocation"].get(
            "continuation_input"
        )
        self.assertIsNotNone(continuation)
        continuation["message"]["content"] = "{stable_prefix}{task_suffix}"
        with self.assertRaisesRegex(AI.Refusal, "safe invocation|isolation"):
            AI._validate_native_runtime_manifest(changed)

    def test_preflight_refuses_mutated_executable_command_before_subprocess(self):
        changed = copy.deepcopy(self.native_manifest)
        changed["runtimes"][1]["protocol_schema"]["command"] = [
            "codex",
            "exec",
            "answer-producing-prompt",
        ]
        args = types.SimpleNamespace(
            no_session=True,
            runtimes="claude-code,codex",
        )
        with mock.patch.object(
            AI,
            "_load_fixture_record",
            return_value=(changed, canonical(changed)),
        ):
            with mock.patch.object(AI, "_bounded_process") as bounded:
                with self.assertRaisesRegex(AI.Refusal, "executable command drift"):
                    AI.preflight_native_gate(args)
        bounded.assert_not_called()

    def test_native_preflight_executes_only_in_manifest_bound_isolation(self):
        calls = []
        auth_calls = {"claude": 0, "codex": 0}

        def resolved(name):
            return Path(f"/opt/frozen-runtime/{name}")

        def staged(_source, destination):
            return "0" * 64, (1,) * 7

        def bounded(argv, *, environment, cwd, **_kwargs):
            executable_path = Path(argv[0])
            executable = executable_path.name
            calls.append(
                (executable_path, tuple(argv[1:]), dict(environment), Path(cwd))
            )
            if argv[1:] == ["--version"]:
                version = next(
                    row["version"]["expected"]
                    for row in self.native_manifest["runtimes"]
                    if row["executable"] == executable
                )
                return 0, version.encode(), b""
            if executable == "claude" and argv[1:4] == ["auth", "status", "--json"]:
                auth_calls[executable] += 1
                logged_in = auth_calls[executable] == 2
                return (
                    0 if logged_in else 1,
                    canonical({"loggedIn": logged_in}),
                    b"",
                )
            if executable == "codex" and argv[1:3] == ["login", "status"]:
                auth_calls[executable] += 1
                logged_in = auth_calls[executable] == 2
                return (
                    0 if logged_in else 1,
                    b"Logged in using ChatGPT" if logged_in else b"Not logged in",
                    b"",
                )
            if executable == "codex" and argv[1:4] == [
                "app-server",
                "generate-json-schema",
                "--experimental",
            ]:
                return 0, b"", b""
            self.fail(f"unexpected native preflight command: {argv}")

        args = types.SimpleNamespace(
            candidate=AI.EVALUATOR_CANDIDATES[0],
            no_session=True,
            report=ROOT / AI.NATIVE_REPORT_PATHS[AI.EVALUATOR_CANDIDATES[0]],
            runtimes=",".join(AI.NATIVE_RUNTIMES),
        )
        with (
            mock.patch.object(AI, "_resolved_runtime_executable", side_effect=resolved),
            mock.patch.object(
                AI, "_stage_external_executable", create=True, side_effect=staged
            ) as executable_stage,
            mock.patch.object(AI, "_bounded_process", side_effect=bounded),
            mock.patch.object(
                AI,
                "_external_file_attestation",
                create=True,
                return_value=("0" * 64, (1,) * 7),
            ) as executable_attestation,
            mock.patch.object(
                AI, "_external_file_digest", return_value="0" * 64
            ) as executable_digest,
            mock.patch.object(AI, "_macos_claude_credential", return_value=b"secret"),
            mock.patch.object(AI, "_write_isolated_secret"),
            mock.patch.object(AI, "_copy_external_auth"),
            mock.patch.object(
                AI, "_read_generated_schema_bundle", return_value=("1" * 64, [{}])
            ),
            mock.patch.object(AI, "_validate_codex_schema_bundle"),
            mock.patch.object(AI, "_publish_preflight_report", return_value=b"{}\n") as publish,
        ):
            try:
                AI.preflight_native_gate(args)
            except AI.Refusal as exc:
                self.fail(f"frozen native preflight refused: {exc}")

        self.assertEqual(auth_calls, {"claude": 2, "codex": 2})
        attested = [
            Path(call.args[0]).name
            for call in executable_attestation.call_args_list
        ]
        self.assertEqual(attested.count("claude"), 1)
        self.assertEqual(attested.count("codex"), 2)
        self.assertEqual(executable_digest.call_count, 0)
        self.assertEqual(executable_stage.call_count, 2)
        self.assertTrue(calls)
        for executable_path, argv, environment, cwd in calls:
            executable = executable_path.name
            self.assertEqual(executable_path.parent.name, "executables")
            self.assertNotEqual(cwd, ROOT)
            self.assertEqual(cwd.name, f"{executable if executable == 'codex' else 'claude-code'}-workspace")
            state_name = "CLAUDE_CONFIG_DIR" if executable == "claude" else "CODEX_HOME"
            expected_leaf = (
                "claude"
                if executable == "claude"
                else "codex-schema-state"
                if argv[:3]
                == ("app-server", "generate-json-schema", "--experimental")
                else "codex"
            )
            self.assertEqual(Path(environment[state_name]).name, expected_leaf)
        evidence = publish.call_args.args[2]
        self.assertTrue(evidence.get("isolated_workspace_proved"))


class NativeCacheAccountingTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_cached_tokens_count_in_full_and_churn_excludes_reads(self):
        try:
            AI._validate_native_cache_accounting(self.accounting)
        except AI.Refusal as exc:
            self.fail(f"frozen native cache accounting refused: {exc}")
        claude = AI.native_token_vector(
            "claude-code",
            {
                "input_tokens": 7,
                "cache_creation_input_tokens": 11,
                "cache_read_input_tokens": 13,
            },
        )
        self.assertEqual(claude["complete_logical_input_tokens"], 31)
        self.assertEqual(claude["fresh_token_churn"], 18)
        codex = AI.native_token_vector(
            "codex",
            {"inputTokens": 31, "cachedInputTokens": 13, "cacheWriteInputTokens": 11},
        )
        self.assertEqual(codex["uncached_suffix_or_miss_tokens"], 7)
        self.assertEqual(codex["fresh_token_churn"], 18)

    def test_overlapping_cache_categories_refuse(self):
        with self.assertRaisesRegex(AI.Refusal, "overlap"):
            AI.native_token_vector(
                "codex",
                {"inputTokens": 10, "cachedInputTokens": 8, "cacheWriteInputTokens": 4},
            )

    def test_missing_write_telemetry_keeps_split_unknown_but_churn_exact(self):
        observed = AI.native_token_vector(
            "codex", {"inputTokens": 10, "cachedInputTokens": 8}
        )
        self.assertIsNone(observed["cache_write_tokens"])
        self.assertIsNone(observed["uncached_suffix_or_miss_tokens"])
        self.assertEqual(observed["fresh_token_churn"], 2)

    def test_cross_tokenizer_pooling_refuses_and_dollar_weighting_refuses(self):
        left = {
            "runtime_id": "codex",
            "model_id": "m",
            "tokenizer_id": "a",
            "complete_logical_context_high_water": 1,
            "cumulative_fresh_token_churn": 1,
        }
        right = {**left, "tokenizer_id": "b"}
        with self.assertRaisesRegex(AI.Refusal, "pool"):
            AI.native_vector_dominates(left, right)
        for absent in ({}, {"runtime_id": None}, {"runtime_id": ""}):
            with self.assertRaisesRegex(AI.Refusal, "identity is missing"):
                AI.native_vector_dominates(absent, copy.deepcopy(absent))
        changed = copy.deepcopy(self.accounting)
        changed["comparison"]["dollar_weighting"] = True
        with self.assertRaisesRegex(AI.Refusal, "objective drift"):
            AI._validate_native_cache_accounting(changed)

    def test_negative_token_axis_refuses_before_dominance(self):
        baseline = {
            "runtime_id": "codex",
            "model_id": "gpt-5.6-sol",
            "tokenizer_id": "frozen-tokenizer",
            "complete_logical_context_high_water": 1,
            "cumulative_fresh_token_churn": 1,
        }
        for side in ("left", "right"):
            for axis in (
                "complete_logical_context_high_water",
                "cumulative_fresh_token_churn",
            ):
                with self.subTest(side=side, axis=axis):
                    left = copy.deepcopy(baseline)
                    right = copy.deepcopy(baseline)
                    (left if side == "left" else right)[axis] = -1
                    with self.assertRaisesRegex(AI.Refusal, "axis is negative"):
                        AI.native_vector_dominates(left, right)

    def test_invalidation_is_not_a_fourth_token_category(self):
        changed = copy.deepcopy(self.accounting)
        changed["categories"]["invalidation_tokens"] = "wrong"
        with self.assertRaisesRegex(AI.Refusal, "overlap or are incomplete"):
            AI._validate_native_cache_accounting(changed)

    def test_reinjected_stable_prefix_is_fresh_churn(self):
        self.assertEqual(
            self.accounting["categories"].get("reinjected_stable_prefix"),
            "ordinary cache-write or uncached suffix-or-miss tokens included in "
            "cumulative fresh-token churn",
        )
        changed = copy.deepcopy(self.accounting)
        changed["categories"]["reinjected_stable_prefix"] = "ignored"
        with self.assertRaisesRegex(AI.Refusal, "reinjection"):
            AI._validate_native_cache_accounting(changed)

    def test_formula_aggregation_and_none_selection_are_exactly_committed(self):
        mutations = []
        changed = copy.deepcopy(self.accounting)
        changed["runtime_semantics"]["codex"]["fresh_churn"] = "inputTokens"
        mutations.append(changed)
        changed = copy.deepcopy(self.accounting)
        changed["axes"]["complete_logical_context_high_water"][
            "aggregation"
        ] = "sum"
        mutations.append(changed)
        changed = copy.deepcopy(self.accounting)
        changed["comparison"]["selection_may_be_none"] = False
        mutations.append(changed)
        for changed in mutations:
            with self.subTest(changed=changed):
                with self.assertRaisesRegex(AI.Refusal, "frozen formula"):
                    AI._validate_native_cache_accounting(changed)


class NativeLifecyclePreregistrationTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_native_preregistration_freezes_lifecycle_and_baselines(self):
        try:
            AI._validate_native_preregistration(self.native_preregistration)
        except AI.Refusal as exc:
            self.fail(f"frozen native preregistration refused: {exc}")
        self.assertEqual(
            self.native_preregistration["lifecycle_order"], list(AI.NATIVE_LIFECYCLES)
        )
        self.assertEqual(
            self.native_preregistration["admission"]["mandatory_baselines"],
            ["raw", "simple"],
        )
        workload = self.native_preregistration["workload"]
        self.assertEqual(workload["scheduled_task_count"], 5)
        self.assertEqual(workload["maximum_chains_before_admission_filter"], 10)
        self.assertEqual(workload["maximum_observations_before_admission_filter"], 50)
        self.assertEqual(
            [item["lifecycle_id"] for item in workload["task_slots"]],
            list(AI.NATIVE_LIFECYCLES),
        )
        self.assertEqual(
            len({item["task_commitment"] for item in workload["task_slots"]}), 5
        )
        partition = self.native_preregistration["prompt"].get("partition")
        self.assertIsNotNone(partition)
        self.assertEqual(partition["stable_prefix_injections_per_chain"], 1)
        self.assertEqual(partition["continuation_input"], "{task_suffix}")

    def test_native_packet_binds_baseline_first_five_task_chains(self):
        packet = load(FROZEN_NATIVE_ROOT / "packet.json")
        self.assertEqual(
            packet.get("prompt_partition_sha256"),
            hashlib.sha256(
                canonical(self.native_preregistration["prompt"]["partition"])
            ).hexdigest(),
        )
        chains = packet["chain_order"]
        self.assertEqual(len(chains), 10)
        for runtime_offset in (0, 5):
            runtime = chains[runtime_offset : runtime_offset + 5]
            self.assertEqual(
                [item["execution_tier"] for item in runtime[:2]],
                ["mandatory-baseline", "mandatory-baseline"],
            )
            for chain in runtime:
                self.assertEqual(
                    [item["lifecycle_id"] for item in chain["observations"]],
                    list(AI.NATIVE_LIFECYCLES),
                )
                self.assertEqual(
                    len(
                        {
                            item["task_commitment"]
                            for item in chain["observations"]
                        }
                    ),
                    5,
                )

    def test_task_repetition_and_scorer_mutations_refuse_after_reseal(self):
        for mutate in ("task", "repetition", "scorer"):
            changed = copy.deepcopy(self.native_preregistration)
            if mutate == "task":
                changed["workload"]["task_slots"][0]["task_commitment"] = "0" * 64
            elif mutate == "repetition":
                changed["workload"]["repetitions_per_runtime_arm_chain"] = 2
            else:
                changed["behavior_scoring"]["scorer_sha256"] = "0" * 64
            changed.pop("sha256")
            changed = AI._digested_record(changed)
            with self.subTest(mutate=mutate):
                with self.assertRaisesRegex(
                    AI.Refusal, "contract drift|task or repetition|behavior scorer"
                ):
                    AI._validate_native_preregistration(changed)

    def test_native_preregistration_replays_every_repository_input_binding(self):
        mutations = []
        for path in (
            ("runtime_manifest_sha256",),
            ("cache_accounting_sha256",),
            ("selection_sha256",),
            ("prompt", "template_sha256"),
        ):
            changed = copy.deepcopy(self.native_preregistration)
            target = changed
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = "0" * 64
            changed.pop("sha256")
            mutations.append((path, AI._digested_record(changed)))
        for path, changed in mutations:
            with self.subTest(path=path):
                with self.assertRaisesRegex(AI.Refusal, "repository inputs"):
                    AI._validate_native_preregistration(changed)

    def test_unproved_or_mixed_claude_expiry_is_inconclusive(self):
        self.assertIsNone(AI.claude_expiry_wait_seconds({}))
        self.assertIsNone(
            AI.claude_expiry_wait_seconds(
                {
                    "cache_creation": {
                        "ephemeral_1h_input_tokens": 1,
                        "ephemeral_5m_input_tokens": 1,
                    }
                }
            )
        )
        self.assertEqual(
            AI.claude_expiry_wait_seconds(
                {"cache_creation": {"ephemeral_5m_input_tokens": 10}}
            ),
            360,
        )

    def test_unknown_claude_cache_creation_class_is_inconclusive(self):
        self.assertIsNone(
            AI.claude_expiry_wait_seconds(
                {
                    "cache_creation": {
                        "ephemeral_5m_input_tokens": 10,
                        "future_ttl_input_tokens": 10,
                    }
                }
            )
        )

    def test_no_session_flag_is_mandatory(self):
        args = types.SimpleNamespace(
            no_session=False,
            preregistration=NATIVE_PREREGISTRATION,
            commitment=NATIVE_PACKET_COMMITMENT,
        )
        with self.assertRaisesRegex(AI.Refusal, "requires --no-session"):
            AI.verify_native_preregistration(args)


class PacketCommitmentTests(ExperimentFixtureMixin, unittest.TestCase):
    def test_both_frozen_packets_reproduce_from_repository_bytes(self):
        seal = load(SEAL)
        try:
            behavioral = AI._opaque_behavioral_packet(self.preregistration, seal)
            loaded_behavioral = AI._load_frozen_packet(
                AI.FROZEN_BEHAVIORAL_ROOT,
                behavioral,
                allowed_directories=("native",),
            )
            AI._verify_packet_commitment(
                self.preregistration,
                load(HOLDOUT_PACKET_COMMITMENT),
                f"{AI.SCHEMA_PREFIX}-holdout-packet-commitment/v1",
                loaded_behavioral,
            )
            native = AI._opaque_native_packet(self.native_preregistration)
            loaded_native = AI._load_frozen_packet(AI.FROZEN_NATIVE_ROOT, native)
            AI._verify_packet_commitment(
                self.native_preregistration,
                load(NATIVE_PACKET_COMMITMENT),
                f"{AI.SCHEMA_PREFIX}-native-lifecycle-packet-commitment/v1",
                loaded_native,
            )
        except AI.Refusal as exc:
            self.fail(f"frozen packet refused: {exc}")

    def test_packet_mutation_and_removal_refuse(self):
        expected = AI._opaque_native_packet(self.native_preregistration)
        with scratch_directory("step3-packet-mutation-") as temporary:
            root = Path(temporary)
            relative = PurePosixPath(root.relative_to(ROOT).as_posix())
            for name, raw in expected.items():
                (root / name).write_bytes(raw)
            (root / "packet.json").write_bytes(b"{}\n")
            with self.assertRaisesRegex(AI.Refusal, "differ"):
                AI._load_frozen_packet(relative, expected)
            (root / "packet.json").unlink()
            with self.assertRaisesRegex(AI.Refusal, "non-closed"):
                AI._load_frozen_packet(relative, expected)

    def test_frozen_packet_enumeration_refuses_at_the_exact_entry_bound(self):
        expected = AI._opaque_native_packet(self.native_preregistration)
        with scratch_directory("step3-packet-bound-") as temporary:
            root = Path(temporary)
            relative = PurePosixPath(root.relative_to(ROOT).as_posix())
            for name, raw in expected.items():
                (root / name).write_bytes(raw)
            (root / "excess.json").write_bytes(b"{}\n")
            with self.assertRaisesRegex(AI.Refusal, "entry bound"):
                AI._load_frozen_packet(relative, expected)

    def test_terminal_commitment_never_precedes_payload_and_stale_mix_refuses(self):
        with scratch_directory("step3-publication-") as temporary:
            root = Path(temporary)
            payload = root / "packet.json"
            terminal = root / "commitment.json"
            AI._publish_committed_set(
                [(payload, b"payload\n"), (terminal, b"commitment\n")],
                terminal=terminal,
            )
            self.assertEqual(payload.read_bytes(), b"payload\n")
            with self.assertRaisesRegex(AI.Refusal, "stale bytes"):
                AI._publish_committed_set(
                    [(payload, b"changed\n"), (terminal, b"commitment\n")],
                    terminal=terminal,
                )

    def test_committed_publication_never_overwrites_a_concurrent_target(self):
        with scratch_directory("step3-publication-race-") as temporary:
            root = Path(temporary)
            payload = root / "packet.json"
            terminal = root / "commitment.json"
            original_write = AI._atomic_write

            def collide(path, raw, **kwargs):
                if path == payload and not path.exists():
                    path.write_bytes(b"concurrent\n")
                return original_write(path, raw, **kwargs)

            with (
                mock.patch.object(AI, "_atomic_write", side_effect=collide),
                self.assertRaisesRegex(AI.Refusal, "changed during publication"),
            ):
                AI._publish_committed_set(
                    [(payload, b"payload\n"), (terminal, b"commitment\n")],
                    terminal=terminal,
                )
            self.assertEqual(payload.read_bytes(), b"concurrent\n")
            self.assertFalse(terminal.exists())

    def test_progressive_report_is_publish_once(self):
        with scratch_directory("step3-report-") as temporary:
            target = Path(temporary) / "report.json"
            args = types.SimpleNamespace(
                candidate=AI.EVALUATOR_CANDIDATES[0],
                models=",".join(AI.MODEL_IDS),
                report=target,
            )
            with mock.patch.object(AI, "_expected_report", return_value=target):
                AI._publish_preflight_report(args, "seven-model-preflight", {"run": 1})
                report = load(target)
                self.assertEqual(
                    report["command"],
                    AI._preflight_invocation(args, "seven-model-preflight"),
                )
                self.assertFalse(report["command"].startswith("{"))
                evidence = load(target.with_name("report-evidence.json"))
                AI._validate_digested_record(evidence, "preflight evidence")
                with self.assertRaisesRegex(AI.Refusal, "stale bytes"):
                    AI._publish_preflight_report(
                        args, "seven-model-preflight", {"run": 2}
                    )


if __name__ == "__main__":
    unittest.main()
