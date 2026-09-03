#!/usr/bin/env python3
"""Source-bound workbench for framework-74 instruction architecture research.

Step 1 owns the corpus, loader, byte partition, and sealed cohort boundary.
Later steps extend this CLI without changing the authority of the Markdown
sources recorded here.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation, localcontext
import hashlib
import importlib
import importlib.util
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import posixpath
import pwd
import re
import resource
import secrets
import selectors
import shlex
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from bisect import bisect_left, bisect_right
from functools import lru_cache
from typing import Any, Iterable, Iterator
from urllib.error import HTTPError, URLError
from urllib.request import HTTPSHandler, HTTPRedirectHandler, Request, build_opener


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REF = "a2b634d8e039af988bf30c8316defccf70071d8d"
SCHEMA_PREFIX = "wildcat-instruction-architecture"
SELECTION_SEED = "framework-74-holdout-v1-2026-08-31"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_GIT_OUTPUT = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_FROZEN_TREE_PATHS = 10_000
MAX_JSON_DEPTH = 64
MAX_JSON_TOKENS = 1_000_000
MAX_JSON_NUMBER_CHARS = 640
MAX_MARKDOWN_LINK_OPENERS = 4_096
MAX_MARKDOWN_LINE_CHARS = 16_384
MAX_MARKDOWN_PHYSICAL_LINES = 16_384
MAX_MARKDOWN_FENCE_EVENTS = 4_096
MAX_MARKDOWN_LIST_DEPTH = 4_096
EXPECTED_COUNTS = {
    "fixed_input": 3,
    "skill_contract": 32,
    "structured_reference": 12,
    "runtime_contract": 18,
    "promise_machine_contract": 18,
    "markdown_reference": 38,
    "identity_contract": 1,
    "identity_roster": 1,
    "router_install_contract": 1,
    "overlay_contract": 1,
    "frontier_policy": 1,
    "frontier_ledger": 26,
    "worker_prompt": 14,
    "operation_reference": 25,
}
EXPECTED_TOTALS = {
    "physical_files": 191,
    "physical_bytes": 2_290_450,
    "unique_files": 174,
    "unique_bytes": 1_819_006,
}
PARTITION_CLASSES = (
    "governed_operative_semantics",
    "exact_literal_or_evidence",
    "human_only_explanation_or_rationale",
    "generated_duplicate",
    "unsupported_or_unknown",
)
EXTERNAL_SKILL_PREFIXES = (
    "plugins/hexaemeron/skills/fizz/",
    "plugins/hexaemeron/skills/solidity-auditor/",
    "plugins/hexaemeron/skills/x-ray/",
)
BASELINE_FIXTURE_ROOT = PurePosixPath("tests/fixtures/instruction-architecture")
BASELINE_RECONCILIATION = PurePosixPath(
    "docs/instruction-architecture/corpus-reconciliation.md"
)
SCRATCH_ROOT = PurePosixPath("tmp")
BASELINE_RECORD_NAMES = (
    "corpus-manifest.json",
    "invocation-profiles.json",
    "loader-graph.json",
    "byte-partition.json",
    "cohorts.json",
    "holdout-seal.json",
)
EXPECTED_BASELINE_INVENTORY_SHA256 = (
    "7e8566c5e9148ca151323636f51d7d69d7ff0215fb937619eefd4b621fc5bcb9"
)

DEVELOPMENT_SCHEMA = PurePosixPath(
    "research/instruction-architecture/schemas/development-v1.schema.json"
)
DEVELOPMENT_FIXTURE_ROOT = PurePosixPath("tests/fixtures/instruction-architecture")
DEVELOPMENT_EVIDENCE_ROOT = DEVELOPMENT_FIXTURE_ROOT / "evidence/development"
DEVELOPMENT_RECORD_PATHS = (
    "controls/noema.json",
    "controls/raw.json",
    "controls/section-graph.json",
    "controls/simple.json",
    "controls/wai1.json",
    "development/cases.json",
    "hostile/specimens.json",
    "hostile/execution.json",
    "evidence/development/noema.json",
    "evidence/development/raw.json",
    "evidence/development/report.json",
    "evidence/development/resource-samples.json",
    "evidence/development/section-graph.json",
    "evidence/development/simple.json",
    "evidence/development/wai1.json",
)
DEVELOPMENT_ARMS = ("raw", "wai1", "noema", "simple", "section-graph")
DEVELOPMENT_CLASSES = (
    "order",
    "scope",
    "negation",
    "exception",
    "literal",
    "alias",
    "unknown",
    "refusal",
    "recovery",
    "authority",
)
SECTION_SELECTION = {
    "closure": "selected-sections-plus-transitive-parents",
    "deduplication": "exact-whole-file-canonical-content",
    "fallback": "whole-source-for-unsupported-non-markdown",
    "roots": "all-sections-of-loader-reachable-canonical-files",
    "scenario_source": "verified-loader-graph",
}
SHARED_BEHAVIORAL_PATHS = (
    ".agents/skills/promise-machine/PORTABLE.md",
    ".agents/skills/promise-machine/SKILL.md",
    "AGENTS.md",
    "PROMISE_MACHINE.md",
    "SHOGGOTH.md",
)
WAI1_CONTROL_REF = SOURCE_REF
NOEMA_PRODUCT_REF = "07ee0475d1559a2b09488f925645a83f786d1f3c"
NOEMA_REVIEW_REF = "7344de8874f9de8a2a2ef78a31f7e760f56e491e"
CONTROL_SNAPSHOT_ROOT = DEVELOPMENT_FIXTURE_ROOT / "controls/snapshots"
CONTROL_SNAPSHOT_MANIFEST = CONTROL_SNAPSHOT_ROOT / "manifest.json"
WAI1_CONTROL_PREFIXES = (
    "docs/agent-instruction-language-v1.md",
    "schemas/agent-instruction-v1.schema.json",
    "scripts/agent_instruction.py",
    "tests/fixtures/agent-instruction-v1",
)
NOEMA_PRODUCT_PREFIXES = (
    "docs/decisions/ADR-066-evaluate-noema-as-a-sliced-instruction-ir.md",
    "docs/noema-v1.md",
    "schemas/noema-v1.schema.json",
    "scripts/noema.py",
    "tests/fixtures/noema-v1",
)
NOEMA_REVIEW_PREFIXES = (
    "audit/rounds/fiat-942-prototype-noema-as-a-model-native-sliced-ins.md",
    "audit/rounds/fiat-942-prototype-noema-as-a-model-native-sliced-ins.synopsis.md",
)
CONTROL_SNAPSHOT_GROUPS = (
    (WAI1_CONTROL_REF, WAI1_CONTROL_PREFIXES),
    (NOEMA_PRODUCT_REF, NOEMA_PRODUCT_PREFIXES),
    (NOEMA_REVIEW_REF, NOEMA_REVIEW_PREFIXES),
)
EXPECTED_CONTROL_SNAPSHOT_SHA256 = (
    "696d67a87f3c564b9c02d68fb8630132ffad2f98d2319af76390cfd80a28fc7a"
)
EXPECTED_CONTROL_SNAPSHOT_COUNTS = {
    "artifact_records": 172,
    "object_bytes": 2_095_430,
    "objects": 157,
}
MAX_CONTROL_PATHS = 1_024
MAX_DEVELOPMENT_CASES = 128
MAX_PROMPT_COMPONENTS = 8_192
MAX_PROMPT_BYTES = 4 * 1024 * 1024
MAX_SECTION_COUNT = 32_768
MAX_HOSTILE_SPECIMENS = 128
MAX_MODEL_OUTPUT_BYTES = 256 * 1024
EXPECTED_DEVELOPMENT_INVENTORY_SHA256 = (
    "8879361a57f9270dbbc5b7d8ef0fe5900e20555afbed7ee27a256a02328660cd"
)
EXPECTED_CONTROL_SHA256 = {
    "noema": "2c52f72927eeb630c1abbc6a2a994221235c6f1aa81d33ff9965002cddbc2a4b",
    "raw": "bfc416cc7fd3d9a1a569fea4eaa6e6577770bf89f77b68eb23378633d57da23e",
    "section-graph": "64f62560d56b65c782c792854a7803e90c864cb7fa590e75618f2f744c8d40a1",
    "simple": "f4de11d7c9b0c05dc902c5971dc71d348e7879e6d357294627247b7faee8b5c4",
    "wai1": "d45599ba946cf515a72491310a105db6e257847d67541f218398877ea84e0ac1",
}

EXPERIMENT_SCHEMA = PurePosixPath(
    "research/instruction-architecture/schemas/experiment-v1.schema.json"
)
EXPERIMENT_FIXTURE_ROOT = PurePosixPath("tests/fixtures/instruction-architecture")
CORPUS_MANIFEST = EXPERIMENT_FIXTURE_ROOT / "corpus-manifest.json"
DEVELOPMENT_SELECTION = EXPERIMENT_FIXTURE_ROOT / "development-selection.json"
BEHAVIORAL_PREREGISTRATION = EXPERIMENT_FIXTURE_ROOT / "preregistration.json"
MODEL_RUNTIME_MANIFEST = EXPERIMENT_FIXTURE_ROOT / "model-runtime-manifest.json"
BEHAVIORAL_PROMPT_TEMPLATE = EXPERIMENT_FIXTURE_ROOT / "prompt-template.txt"
BEHAVIORAL_SCORER = EXPERIMENT_FIXTURE_ROOT / "scorer.json"
BEHAVIORAL_COMMITMENT = EXPERIMENT_FIXTURE_ROOT / "holdout-packet-commitment.json"
FROZEN_BEHAVIORAL_ROOT = EXPERIMENT_FIXTURE_ROOT / "evidence/frozen"
NATIVE_PREREGISTRATION = (
    EXPERIMENT_FIXTURE_ROOT / "native-deployment-preregistration.json"
)
NATIVE_RUNTIME_MANIFEST = EXPERIMENT_FIXTURE_ROOT / "native-runtime-manifest.json"
NATIVE_CACHE_ACCOUNTING = EXPERIMENT_FIXTURE_ROOT / "native-cache-accounting.json"
NATIVE_PROMPT_TEMPLATE = EXPERIMENT_FIXTURE_ROOT / "native-prompt-template.txt"
NATIVE_COMMITMENT = (
    EXPERIMENT_FIXTURE_ROOT / "native-lifecycle-packet-commitment.json"
)
FROZEN_NATIVE_ROOT = FROZEN_BEHAVIORAL_ROOT / "native"
MODEL_IDS = (
    "anthropic/claude-opus-5",
    "google/gemini-3.7-flash",
    "qwen/qwen3.8-27b",
    "openai/gpt-5.6-sol",
    "deepseek/deepseek-v4-pro-0813",
    "moonshotai/kimi-k3",
    "z-ai/glm-5.3",
)
EVALUATOR_CANDIDATES = (
    "neutral-evidence-workbench",
    "wai1-hosted-evaluator",
    "noema-hosted-evaluator",
)
NATIVE_RUNTIMES = ("claude-code", "codex")
NATIVE_RESPONSE_REUSE_SHA256 = (
    "1895eb199f74072637c05a3fc3826f9602433de717d776fb5dfaadedb1860a33"
)
NATIVE_RUNTIME_RECORD_SHA256 = {
    "claude-code": "147a80d9d34f24837562f9fb0c8aa086d6029bb72aff9f249f4209564d612fae",
    "codex": "ac9e2cf5bb89cabff77096db17a6f0af64112ee48ee67c38a7d98292697b2f4f",
}
NATIVE_CACHE_ACCOUNTING_SHA256 = (
    "e58fc949a40f89dbc44b7a85e8e26bc92723fa5a18a0068d863d58ffcbcb77ad"
)
NATIVE_LIFECYCLES = (
    "cold-start",
    "continuous-warm",
    "resume-within-ttl",
    "resume-after-expiry",
    "post-compaction",
)
BEHAVIORAL_ACTIONS = {
    "decision": "decide",
    "refusal": "refuse",
    "recovery": "recover",
    "structured-plan": "plan",
    "tool-invocation": "invoke",
}
SEMANTIC_WITNESS_RULES = {
    "authority": "closed profile phase plus primary skill obligation witness",
    "failure": "closed profile branch state plus primary skill obligation witness",
    "recovery": "closed required-document set plus primary skill obligation witness",
    "exact-literal": "closed ordered document set plus primary skill obligation witness",
    "cross-document": "closed dependency set plus first two obligation witnesses",
}
CASE_GENERATOR_ALGORITHM = "source-ref-invocation-profile-oracle/v1"
NATIVE_REPETITIONS = 1
BEHAVIORAL_COHORTS = ("cohort-a", "cohort-b")
OPENROUTER_ENDPOINTS = {
    "account": "https://openrouter.ai/api/v1/key",
    "credits": "https://openrouter.ai/api/v1/credits",
    "models": "https://openrouter.ai/api/v1/models",
    "zdr": "https://openrouter.ai/api/v1/endpoints/zdr",
}
BATCH_ORDER_SEED = (
    "7d7eee40bc69b0273a41d56572f2afbcec1132075ac30581b1a54e0e24af836c"
)
MAX_HTTP_BYTES = 4 * 1024 * 1024
HTTP_TIMEOUT_SECONDS = 20
MAX_COMMAND_OUTPUT_BYTES = 2 * 1024 * 1024
DESIGN_REPORT_ROOT = PurePosixPath(".hexaemeron/design-reports")
BEHAVIORAL_TRIALS = 2
BEHAVIORAL_CASES = 16
BEHAVIORAL_LOGICAL_CALLS = (
    len(DEVELOPMENT_ARMS) * len(MODEL_IDS) * BEHAVIORAL_TRIALS * BEHAVIORAL_CASES
)
BEHAVIORAL_ALPHA = Decimal("0.05")
BEHAVIORAL_MAX_DEGRADATION = Decimal("0.02")
NATIVE_REPORT_PATHS = {
    candidate: PurePosixPath(
        f".hexaemeron/design-reports/{candidate}-native-gate-preflight.json"
    )
    for candidate in EVALUATOR_CANDIDATES
}

INVOCATION_PROFILE_SCHEMA = PurePosixPath(
    "research/instruction-architecture/schemas/invocation-profile-v1.schema.json"
)
EXPECTED_PROFILE_COUNTS = {
    "alexandria": 3,
    "anamnesis": 3,
    "ariadne": 7,
    "berean": 2,
    "brevitas": 2,
    "elenchus": 3,
    "ephoros": 2,
    "fiat": 415,
    "fizz": 6,
    "fizz-convert": 1,
    "fizz-sync": 1,
    "hermes": 2,
    "homologia": 2,
    "horos": 2,
    "hypomnema": 2,
    "imprimatur": 2,
    "janus": 2,
    "kronos": 26,
    "lazarus": 5,
    "lemma": 3,
    "metron": 3,
    "pandects": 2,
    "phylax": 3,
    "probitas": 3,
    "protasis": 3,
    "sapheneia": 2,
    "solidity-auditor": 1,
    "synkrisis": 4,
    "tabularium": 4,
    "vulgate": 2,
    "x-ray": 1,
}
EXPECTED_PROFILE_PROJECTION_SHA256 = (
    "b09aeb1ba087dff0c34c3fad63a9096c4862aad71b14fe6c6a12a14819c94c07"
)
EXPECTED_PROFILE_EVIDENCE_COUNTS = {
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
EXPECTED_MANIFEST_SOURCE_EVIDENCE_COUNTS = {
    "fixed_input": 3,
    "markdown_reference": 3,
    "operation_reference": 3,
    "structured_reference": 12,
}
EXPECTED_GRAPH_RUNTIME_EVIDENCE_COUNTS = {
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": 4,
    "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": 4,
    "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": 4,
    "plugins/synkrisis/references/rules-v1.json": 3,
}
VALIDATION_OPERATION_REFERENCE_PATHS = frozenset(
    {
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
)
VALIDATION_FIAT_WORKER_PROMPTS = frozenset(
    {
        "plugins/hexaemeron/agents/mason.md",
        "plugins/hexaemeron/agents/scribe.md",
        "plugins/hexaemeron/agents/surveyor.md",
        "plugins/hexaemeron/agents/warden.md",
    }
)
VALIDATION_FIZZ_WORKER_PROMPTS = frozenset(
    {
        "plugins/hexaemeron/skills/fizz/agents/implementers/global-property-implementer.md",
        "plugins/hexaemeron/skills/fizz/agents/implementers/specific-property-implementer.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/adversarial-profit-maximizer.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/conservation-auditor.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/protocol-type-specialist.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/roundtrip-rounding-analyst.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/state-transition-mapper.md",
        "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/synthesizer.md",
        "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md",
        "plugins/hexaemeron/skills/fizz/agents/report-writer.md",
    }
)
VALIDATION_STRUCTURED_REFERENCE_PATHS = frozenset(
    {
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json",
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
        "plugins/synkrisis/references/rules-v1.json",
    }
)
VALIDATION_FIXED_INPUT_PATHS = frozenset(
    {
        ".python-version",
        "plugins/hexaemeron/skills/solidity-auditor/VERSION",
        "plugins/hexaemeron/skills/x-ray/VERSION",
    }
)
VALIDATION_PYTHON_PIN_PROFILE_IDS = frozenset(
    {
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
)

FRONTIER_SKILLS = (
    "plugins/alexandria/skills/alexandria",
    "plugins/anamnesis/skills/anamnesis",
    "plugins/ariadne/skills/ariadne",
    "plugins/berean/skills/berean",
    "plugins/brevitas/skills/brevitas",
    "plugins/hermes/skills/hermes",
    "plugins/hexaemeron/skills/elenchus",
    "plugins/hexaemeron/skills/ephoros",
    "plugins/hexaemeron/skills/fiat",
    "plugins/hexaemeron/skills/hypomnema",
    "plugins/hexaemeron/skills/imprimatur",
    "plugins/hexaemeron/skills/kronos",
    "plugins/hexaemeron/skills/metron",
    "plugins/hexaemeron/skills/phylax",
    "plugins/hexaemeron/skills/protasis",
    "plugins/hexaemeron/skills/vulgate",
    "plugins/homologia/skills/homologia",
    "plugins/horos/skills/horos",
    "plugins/janus/skills/janus",
    "plugins/lazarus/skills/lazarus",
    "plugins/lemma/skills/lemma",
    "plugins/pandects/skills/pandects",
    "plugins/probitas/skills/probitas",
    "plugins/sapheneia/skills/sapheneia",
    "plugins/synkrisis/skills/synkrisis",
    "plugins/tabularium/skills/tabularium",
)

FIAT_WORKER_PROMPTS = (
    "plugins/hexaemeron/agents/mason.md",
    "plugins/hexaemeron/agents/scribe.md",
    "plugins/hexaemeron/agents/surveyor.md",
    "plugins/hexaemeron/agents/warden.md",
)

FIZZ_WORKER_PROMPTS = (
    "plugins/hexaemeron/skills/fizz/agents/implementers/global-property-implementer.md",
    "plugins/hexaemeron/skills/fizz/agents/implementers/specific-property-implementer.md",
    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/adversarial-profit-maximizer.md",
    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/conservation-auditor.md",
    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/protocol-type-specialist.md",
    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/roundtrip-rounding-analyst.md",
    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/state-transition-mapper.md",
    "plugins/hexaemeron/skills/fizz/agents/invariant-discovery/synthesizer.md",
    "plugins/hexaemeron/skills/fizz/agents/protocol-analyzer.md",
    "plugins/hexaemeron/skills/fizz/agents/report-writer.md",
)

SELECTABLE_SKILL_PATHS = {
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

FIXED_AGENT_INPUTS = (
    (
        ".python-version",
        "AGENTS.md",
        "AGENTS.md",
        "Every `python3` command below means the exact interpreter recorded in\n"
        "[`.python-version`](.python-version).",
    ),
    (
        "plugins/hexaemeron/skills/x-ray/VERSION",
        "plugins/hexaemeron/skills/x-ray/SKILL.md",
        "plugins/hexaemeron/skills/x-ray/SKILL.md",
        "Read the local `VERSION` file from `$SKILL_DIR/VERSION`",
    ),
    (
        "plugins/hexaemeron/skills/solidity-auditor/VERSION",
        "plugins/hexaemeron/skills/solidity-auditor/SKILL.md",
        "plugins/hexaemeron/skills/solidity-auditor/SKILL.md",
        "Read the local `VERSION` file from the same directory as this skill",
    ),
)

REFERENCE_ONLY_MARKDOWN = {
    "plugins/hexaemeron/skills/imprimatur/references/agent-replies.md": (
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "references/agent-replies.md",
        "the link occurs only in the human References section",
    ),
    "plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md": (
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "references/lexicon-rationale.md",
        "the link occurs only in the human References section",
    ),
    "plugins/hexaemeron/skills/imprimatur/references/rewriting.md": (
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "references/rewriting.md",
        "the link occurs only in the human References section",
    ),
    "plugins/pandects/docs/applicability.md": (
        "plugins/pandects/skills/pandects/SKILL.md",
        "`docs/applicability.md` states the rules once",
        "the source describes the document but never directs an agent to read it",
    ),
    "plugins/pandects/docs/writing-a-law.md": (
        "plugins/pandects/skills/pandects/SKILL.md",
        "`docs/writing-a-law.md`",
        "the source describes the document but never directs an agent to read it",
    ),
    "plugins/pandects/integrations/wildcat/APPLICABILITY.md": (
        "plugins/pandects/skills/pandects/SKILL.md",
        "`integrations/wildcat/APPLICABILITY.md` carries all of them",
        "the source describes the document but never directs an agent to read it",
    ),
}

# path, canonical owner, source path, exact source needle
OPERATION_REFERENCES = (
    ("plugins/alexandria/docs/runbook.md", "plugins/alexandria/skills/alexandria/SKILL.md", "plugins/alexandria/skills/alexandria/SKILL.md", "../../docs/runbook.md"),
    ("plugins/alexandria/docs/study.md", "plugins/alexandria/skills/alexandria/SKILL.md", "plugins/alexandria/skills/alexandria/SKILL.md", "../../docs/study.md"),
    ("plugins/alexandria/docs/usdc-interval-collector.md", "plugins/alexandria/skills/alexandria/SKILL.md", "plugins/alexandria/skills/alexandria/SKILL.md", "../../docs/usdc-interval-collector.md"),
    ("plugins/anamnesis/docs/demo.md", "plugins/anamnesis/skills/anamnesis/SKILL.md", "plugins/anamnesis/skills/anamnesis/SKILL.md", "../../docs/demo.md"),
    ("plugins/ariadne/docs/capturing-a-dataset.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/capturing-a-dataset.md"),
    ("plugins/ariadne/docs/capturing-a-grounded-agent.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/capturing-a-grounded-agent.md"),
    ("plugins/ariadne/docs/capturing-a-release.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/capturing-a-release.md"),
    ("plugins/ariadne/docs/capturing-a-state-fixture.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/capturing-a-state-fixture.md"),
    ("plugins/ariadne/docs/conformance.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/conformance.md"),
    ("plugins/ariadne/docs/dataset.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/dataset.md"),
    ("plugins/ariadne/docs/grounded-agent.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/grounded-agent.md"),
    ("plugins/ariadne/docs/solidity-release.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/solidity-release.md"),
    ("plugins/ariadne/docs/state-fixture.md", "plugins/ariadne/skills/ariadne/SKILL.md", "plugins/ariadne/skills/ariadne/SKILL.md", "../../docs/state-fixture.md"),
    ("docs/fiat-run-observation-binding-v1.md", "plugins/hexaemeron/skills/fiat/SKILL.md", "plugins/hexaemeron/skills/fiat/SKILL.md", "../../../../docs/fiat-run-observation-binding-v1.md"),
    ("plugins/lazarus/docs/chain-anchors.md", "plugins/lazarus/skills/lazarus/SKILL.md", "plugins/lazarus/skills/lazarus/SKILL.md", "../../docs/chain-anchors.md"),
    ("plugins/lazarus/docs/preservation-release.md", "plugins/lazarus/skills/lazarus/SKILL.md", "plugins/lazarus/skills/lazarus/SKILL.md", "../../docs/preservation-release.md"),
    ("plugins/lazarus/docs/runbook.md", "plugins/lazarus/skills/lazarus/SKILL.md", "plugins/lazarus/skills/lazarus/SKILL.md", "../../docs/runbook.md"),
    ("plugins/lazarus/docs/study.md", "plugins/lazarus/skills/lazarus/SKILL.md", "plugins/lazarus/skills/lazarus/SKILL.md", "../../docs/study.md"),
    ("plugins/lemma/INVARIANTS.md", "plugins/lemma/skills/lemma/SKILL.md", "plugins/lemma/skills/lemma/SKILL.md", "../../INVARIANTS.md"),
    ("plugins/pandects/docs/applicability.md", "plugins/pandects/skills/pandects/SKILL.md", "plugins/pandects/skills/pandects/SKILL.md", "docs/applicability.md"),
    ("plugins/pandects/docs/writing-a-law.md", "plugins/pandects/skills/pandects/SKILL.md", "plugins/pandects/skills/pandects/SKILL.md", "docs/writing-a-law.md"),
    ("plugins/pandects/integrations/wildcat/APPLICABILITY.md", "plugins/pandects/skills/pandects/SKILL.md", "plugins/pandects/skills/pandects/SKILL.md", "integrations/wildcat/APPLICABILITY.md"),
    ("plugins/probitas/docs/adding-a-venue.md", "plugins/probitas/skills/probitas/SKILL.md", "plugins/probitas/skills/probitas/references/venues.md", "../../../docs/adding-a-venue.md"),
    ("plugins/tabularium/docs/adding-an-adapter.md", "plugins/tabularium/skills/tabularium/SKILL.md", "plugins/tabularium/skills/tabularium/SKILL.md", "../../docs/adding-an-adapter.md"),
    ("plugins/tabularium/docs/release-policy.md", "plugins/tabularium/skills/tabularium/SKILL.md", "plugins/tabularium/skills/tabularium/SKILL.md", "../../docs/release-policy.md"),
)

ARIADNE_OPERATION_CONDITIONS = {
    "plugins/ariadne/docs/capturing-a-release.md": "operation:ariadne:capture-release",
    "plugins/ariadne/docs/solidity-release.md": "operation:ariadne:capture-release",
    "plugins/ariadne/docs/capturing-a-dataset.md": "operation:ariadne:capture-dataset",
    "plugins/ariadne/docs/dataset.md": "operation:ariadne:capture-dataset",
    "plugins/ariadne/docs/capturing-a-state-fixture.md": "operation:ariadne:capture-state-fixture",
    "plugins/ariadne/docs/state-fixture.md": "operation:ariadne:capture-state-fixture",
    "plugins/ariadne/docs/capturing-a-grounded-agent.md": "operation:ariadne:capture-grounded-agent",
    "plugins/ariadne/docs/grounded-agent.md": "operation:ariadne:capture-grounded-agent",
    "plugins/ariadne/docs/conformance.md": "operation:ariadne:conformance",
}

EXCLUDED_LINK_CLASSES = (
    ("human_or_background", "README.md", "AGENTS.md", "A person can begin with `README.md`; an agent begins here."),
    ("generated_reader", "plugins/pandects/docs/catalogue.md", "plugins/pandects/skills/pandects/SKILL.md", "rather than a second source"),
    ("historical_record", "audit/AUDIT.md", "plugins/hexaemeron/skills/fiat/references/audit-loop.md", "audit/AUDIT.md"),
    ("dynamic_target", ".hexaemeron/study.md", "plugins/hexaemeron/agents/surveyor.md", ".hexaemeron/study.md"),
    ("example_or_evidence", "plugins/probitas/docs/example-dossier.md", "plugins/probitas/docs/adding-a-venue.md", "example-dossier.md"),
    ("unavailable_operation", "plugins/alexandria/docs/compound-v3-harvest.md", "plugins/alexandria/skills/alexandria/SKILL.md", "more than this collector covers"),
)

INLINE_MARKDOWN_LINK = re.compile(
    r"(?<!!)\[[^\]\n]+\]\(\s*<?([^)\s>]+)>?(?:\s+[^)]*)?\)"
)


def _preflight_markdown_links(text: str, source: str) -> None:
    """Bound regex restart work before scanning one admitted Markdown source."""
    openers = 0
    line_chars = 0
    pending_suffix = False
    previous = ""
    for value in text:
        if value == "\n":
            if pending_suffix:
                raise Refusal(
                    f"fixed-point Markdown link suffix crosses line boundary: {source}"
                )
            line_chars = 0
            pending_suffix = False
            previous = ""
        else:
            line_chars += 1
            if line_chars > MAX_MARKDOWN_LINE_CHARS:
                raise Refusal(
                    f"fixed-point Markdown line exceeds character limit: {source}"
                )
            if value == ")":
                pending_suffix = False
            elif value == "(" and previous == "]":
                pending_suffix = True
            previous = value
        if value == "[":
            openers += 1
            if openers > MAX_MARKDOWN_LINK_OPENERS:
                raise Refusal(
                    f"fixed-point Markdown link opener count exceeds limit: {source}"
                )
    if pending_suffix:
        raise Refusal(
            f"fixed-point Markdown link suffix crosses line boundary: {source}"
        )


def _preflight_partition_markdown(data: bytes, source: str) -> None:
    """Cap line and root-leading fence fanout before splitting source bytes."""
    if len(data) > MAX_SOURCE_BYTES:
        raise Refusal(f"partition Markdown exceeds byte limit: {source}")
    line_count = 0
    fence_events = 0
    leading_spaces = True
    ended_with_break = False
    index = 0
    while index < len(data):
        value = data[index]
        if value in (0x0A, 0x0D):
            line_count += 1
            if line_count > MAX_MARKDOWN_PHYSICAL_LINES:
                raise Refusal(
                    f"partition Markdown physical line count exceeds limit: {source}"
                )
            leading_spaces = True
            ended_with_break = True
            if value == 0x0D and index + 1 < len(data) and data[index + 1] == 0x0A:
                index += 2
            else:
                index += 1
            continue
        ended_with_break = False
        if leading_spaces:
            if value != 0x20:
                if (
                    value in (0x60, 0x7E)
                    and index + 2 < len(data)
                    and data[index + 1] == value
                    and data[index + 2] == value
                ):
                    fence_events += 1
                    if fence_events > MAX_MARKDOWN_FENCE_EVENTS:
                        raise Refusal(
                            "partition Markdown root-leading fence event count "
                            f"exceeds limit: {source}"
                        )
                leading_spaces = False
        index += 1
    if data and not ended_with_break:
        line_count += 1
        if line_count > MAX_MARKDOWN_PHYSICAL_LINES:
            raise Refusal(
                f"partition Markdown physical line count exceeds limit: {source}"
            )
FIXED_POINT_EXCLUDED_COMPONENTS = {
    "audit",
    "decisions",
    "evals",
    "evidence",
    "examples",
    "fixtures",
    "specimens",
    "tests",
}
FIXED_POINT_PROVENANCE_LINKS = {
    (
        "plugins/homologia/skills/homologia/SKILL.md",
        "plugins/homologia/docs/homologia-study.md",
    ),
    (
        "plugins/probitas/docs/adding-a-venue.md",
        "plugins/probitas/docs/euler-goldsky-discovery.md",
    ),
    (
        "plugins/tabularium/skills/tabularium/SKILL.md",
        "plugins/tabularium/docs/euler-preservation-study.md",
    ),
    (
        "plugins/tabularium/skills/tabularium/SKILL.md",
        "plugins/tabularium/docs/euler-preservation-runbook.md",
    ),
}

CONTRIBUTORS_CANONICAL_URL = (
    "https://github.com/wildcat-finance/skills/blob/main/CONTRIBUTORS.md"
)
SAME_REPOSITORY_MARKDOWN_URLS = {
    CONTRIBUTORS_CANONICAL_URL: "CONTRIBUTORS.md",
}


# path, owner, admission kind, load semantics, source path, source needle,
# runtime path, runtime needle. A reference-only row has no production read.
STRUCTURED_REFERENCES = (
    (
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json",
        "plugins/hermes/skills/hermes/SKILL.md",
        "structured-reference",
        "mandatory-executable",
        "plugins/hermes/skills/hermes/SKILL.md",
        "Every candidate names a rule from "
        "[references/gas-rule-corpus.json](references/gas-rule-corpus.json)",
        "plugins/hermes/skills/hermes/scripts/hermes.py",
        "raw = corpus_path.read_bytes()",
    ),
    (
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json",
        "plugins/hermes/skills/hermes/SKILL.md",
        "structured-reference",
        "mandatory-executable",
        "plugins/hermes/skills/hermes/SKILL.md",
        "A corpus that fails its own schema",
        "plugins/hermes/skills/hermes/scripts/hermes.py",
        'schema = json.loads(schema_path.read_text(encoding="utf-8"))',
    ),
    (
        "plugins/homologia/references/manifest-v1.schema.json",
        "plugins/homologia/skills/homologia/SKILL.md",
        "structured-reference",
        "reference-only",
        "plugins/homologia/docs/checked-inputs/runbook.md",
        "plugins/homologia/references/manifest-v1.schema.json",
        None,
        None,
    ),
    (
        "plugins/homologia/references/vectors-v1.schema.json",
        "plugins/homologia/skills/homologia/SKILL.md",
        "structured-reference",
        "reference-only",
        "plugins/homologia/docs/checked-inputs/runbook.md",
        "plugins/homologia/references/vectors-v1.schema.json",
        None,
        None,
    ),
    (
        "plugins/synkrisis/references/cohort-v1.schema.json",
        "plugins/synkrisis/skills/synkrisis/SKILL.md",
        "structured-reference",
        "reference-only",
        "plugins/synkrisis/references/cohort-v1.schema.json",
        '"$id": "https://github.com/wildcat-finance/skills/plugins/synkrisis/references/cohort-v1.schema.json"',
        None,
        None,
    ),
    (
        "plugins/synkrisis/references/findings-v1.schema.json",
        "plugins/synkrisis/skills/synkrisis/SKILL.md",
        "structured-reference",
        "reference-only",
        "plugins/synkrisis/references/findings-v1.schema.json",
        '"$id": "https://github.com/wildcat-finance/skills/plugins/synkrisis/references/findings-v1.schema.json"',
        None,
        None,
    ),
    (
        "plugins/synkrisis/references/policy-v1.schema.json",
        "plugins/synkrisis/skills/synkrisis/SKILL.md",
        "structured-reference",
        "reference-only",
        "plugins/synkrisis/references/policy-v1.schema.json",
        '"$id": "https://github.com/wildcat-finance/skills/plugins/synkrisis/references/policy-v1.schema.json"',
        None,
        None,
    ),
    (
        "plugins/synkrisis/references/rule-v1.schema.json",
        "plugins/synkrisis/skills/synkrisis/SKILL.md",
        "structured-reference",
        "reference-only",
        "plugins/synkrisis/references/rule-v1.schema.json",
        '"$id": "https://github.com/wildcat-finance/skills/plugins/synkrisis/references/rule-v1.schema.json"',
        None,
        None,
    ),
    (
        "plugins/synkrisis/references/rules-v1.json",
        "plugins/synkrisis/skills/synkrisis/SKILL.md",
        "structured-reference",
        "mandatory-executable",
        "plugins/synkrisis/skills/synkrisis/SKILL.md",
        "python3 plugins/synkrisis/scripts/synkrisis.py diagnose \\\n"
        "  --cohort build/synkrisis/cohort.json \\\n"
        "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
        "  --out build/synkrisis/findings.json",
        "plugins/synkrisis/scripts/synkrisis.py",
        "def load_rules(root: Path, raw_path: str, budget: InputBudget):\n"
        '    target = confined_relative(raw_path, root, label="rules")\n'
        "    shown = shown_path(raw_path)\n"
        "    payload = bounded_read(target, shown, MAX_FILE_BYTES)",
    ),
    (
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "mandatory-rule-data",
        "mandatory-executable",
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "`gated.json`",
        "plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py",
        'return rd("hard.json"), rd("gated.json"), rd("structural.json")',
    ),
    (
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "mandatory-rule-data",
        "mandatory-executable",
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "`hard.json`",
        "plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py",
        'return rd("hard.json"), rd("gated.json"), rd("structural.json")',
    ),
    (
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "mandatory-rule-data",
        "mandatory-executable",
        "plugins/hexaemeron/skills/imprimatur/SKILL.md",
        "`structural.json`",
        "plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py",
        'return rd("hard.json"), rd("gated.json"), rd("structural.json")',
    ),
)

SYNKRISIS_RULE_OPERATIONS = (
    "operation:synkrisis:diagnose",
    "operation:synkrisis:verify",
)
SYNKRISIS_RULE_RUNTIME_NEEDLES = {
    "operation:synkrisis:diagnose": (
        "def command_diagnose(root: Path, arguments):\n"
        "    budget = InputBudget()\n"
        "    cohort = load_cohort(root, arguments.cohort, budget)\n"
        "    rules_document, _ = load_rules(root, arguments.rules, budget)"
    ),
    "operation:synkrisis:verify": (
        '            "rebuild the cohort with the cohort command from the original inputs",\n'
        "        )\n"
        "    rules_document, _ = load_rules(root, arguments.rules, budget)"
    ),
}
SYNKRISIS_RULE_SOURCE_NEEDLES = {
    "operation:synkrisis:diagnose": (
        "python3 plugins/synkrisis/scripts/synkrisis.py diagnose \\\n"
        "  --cohort build/synkrisis/cohort.json \\\n"
        "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
        "  --out build/synkrisis/findings.json"
    ),
    "operation:synkrisis:verify": (
        "python3 plugins/synkrisis/scripts/synkrisis.py verify \\\n"
        "  --manifest plugins/synkrisis/examples/cross-run-v0/manifest.json \\\n"
        "  --policy plugins/synkrisis/examples/cross-run-v0/policy.json \\\n"
        "  --cohort build/synkrisis/cohort.json \\\n"
        "  --rules plugins/synkrisis/references/rules-v1.json \\\n"
        "  --findings build/synkrisis/findings.json"
    ),
}


@lru_cache(maxsize=1)
def _structured_metadata() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for (
        path,
        owner,
        admission_kind,
        load_semantics,
        source_path,
        source_needle,
        runtime_path,
        runtime_needle,
    ) in STRUCTURED_REFERENCES:
        if path in result:
            raise Refusal(f"duplicate structured reference: {path}")
        if (runtime_path is None) != (runtime_needle is None):
            raise Refusal(f"incomplete runtime anchor: {path}")
        if (load_semantics == "reference-only") != (runtime_path is None):
            raise Refusal(f"structured reference load semantics drift: {path}")
        result[path] = {
            "canonical_owner": owner,
            "admission_kind": admission_kind,
            "load_semantics": load_semantics,
            "source_path": source_path,
            "source_needle": source_needle,
            "runtime_path": runtime_path,
            "runtime_needle": runtime_needle,
        }
    if len(result) != 12:
        raise Refusal(f"structured reference inventory drift: {len(result)}")
    return result


@lru_cache(maxsize=1)
def _fixed_agent_metadata() -> dict[str, dict[str, str]]:
    """Return source-required non-Markdown bytes read into agent context."""
    result: dict[str, dict[str, str]] = {}
    for path, owner, source_path, source_needle in FIXED_AGENT_INPUTS:
        if path in result:
            raise Refusal(f"duplicate fixed agent input: {path}")
        result[path] = {
            "canonical_owner": owner,
            "admission_kind": "fixed-agent-input",
            "load_semantics": "agent-or-prompt",
            "source_path": source_path,
            "source_needle": source_needle,
        }
    if len(result) != 3:
        raise Refusal(f"fixed agent input inventory drift: {len(result)}")
    return result


@lru_cache(maxsize=1)
def _additional_metadata() -> dict[str, dict[str, str]]:
    """Return the receipted, source-anchored 70-path corpus admission."""
    result: dict[str, dict[str, str]] = {
        "SHOGGOTH.md": {
            "document_class": "identity_contract",
            "admission_kind": "identity-contract",
            "canonical_owner": "SHOGGOTH.md",
            "source_path": "AGENTS.md",
            "source_needle": "[Shoggoth collective identity](SHOGGOTH.md)",
            "edge_kind": "unconditional",
        },
        "CONTRIBUTORS.md": {
            "document_class": "identity_roster",
            "admission_kind": "credential-identity",
            "canonical_owner": "SHOGGOTH.md",
            "source_path": "SHOGGOTH.md",
            "source_needle": (
                CONTRIBUTORS_CANONICAL_URL
            ),
            "edge_kind": "credential-identity",
        },
        ".agents/skills/promise-machine/PORTABLE.md": {
            "document_class": "router_install_contract",
            "admission_kind": "installed-route",
            "canonical_owner": ".agents/skills/promise-machine/SKILL.md",
            "source_path": ".agents/skills/promise-machine/SKILL.md",
            "source_needle": "read `PORTABLE.md`",
            "edge_kind": "installed-route",
        },
        "plugins/hexaemeron/PROMISES.md": {
            "document_class": "overlay_contract",
            "admission_kind": "vendored-overlay",
            "canonical_owner": "plugins/hexaemeron/AGENTS.md",
            "source_path": "plugins/hexaemeron/AGENTS.md",
            "source_needle": "[PROMISES.md](PROMISES.md)",
            "edge_kind": "vendored-overlay",
        },
        "plugins/hexaemeron/skills/VERSIONING.md": {
            "document_class": "frontier_policy",
            "admission_kind": "frontier-gate",
            "canonical_owner": "plugins/hexaemeron/AGENTS.md",
            "source_path": "plugins/hexaemeron/AGENTS.md",
            "source_needle": "`skills/VERSIONING.md`",
            "edge_kind": "frontier-gate",
        },
    }
    for prefix in FRONTIER_SKILLS:
        skill = f"{prefix}/SKILL.md"
        ledger = f"{prefix}/EVOLUTION.md"
        result[ledger] = {
            "document_class": "frontier_ledger",
            "admission_kind": "frontier-gate",
            "canonical_owner": skill,
            "source_path": skill,
            "source_needle": "EVOLUTION.md",
            "edge_kind": "frontier-gate",
        }
    for path in FIAT_WORKER_PROMPTS:
        role = PurePosixPath(path).stem
        result[path] = {
            "document_class": "worker_prompt",
            "admission_kind": "worker-dispatch",
            "canonical_owner": "plugins/hexaemeron/skills/fiat/SKILL.md",
            "source_path": "plugins/hexaemeron/skills/fiat/SKILL.md",
            "source_needle": f"`{role}`",
            "edge_kind": "worker-dispatch",
        }
    for path in FIZZ_WORKER_PROMPTS:
        relative = PurePosixPath(path).relative_to(
            "plugins/hexaemeron/skills/fizz"
        )
        result[path] = {
            "document_class": "worker_prompt",
            "admission_kind": "worker-dispatch",
            "canonical_owner": "plugins/hexaemeron/skills/fizz/SKILL.md",
            "source_path": "plugins/hexaemeron/skills/fizz/SKILL.md",
            "source_needle": relative.as_posix(),
            "edge_kind": "worker-dispatch",
        }
    for path, owner, source, needle in OPERATION_REFERENCES:
        result[path] = {
            "document_class": "operation_reference",
            "admission_kind": "operation-branch",
            "canonical_owner": owner,
            "source_path": source,
            "source_needle": needle,
            "edge_kind": "operation-branch",
        }
    if len(result) != 70:
        raise Refusal(f"receipted admission inventory drift: {len(result)}")
    return result


class Refusal(ValueError):
    """A bounded input or source relation failed closed."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            + "\n"
        ).encode("utf-8")
    except UnicodeEncodeError as exc:
        raise Refusal("record contains a non-Unicode-scalar string") from exc


def _reject_constant(value: str) -> None:
    raise Refusal(f"non-finite JSON number: {value}")


def _parse_integer(value: str) -> int:
    if len(value.removeprefix("-")) > MAX_JSON_NUMBER_CHARS:
        raise Refusal("record exceeds JSON number length limit")
    return int(value)


def _parse_float(value: str) -> float:
    if len(value) > MAX_JSON_NUMBER_CHARS:
        raise Refusal("record exceeds JSON number length limit")
    result = float(value)
    if not math.isfinite(result):
        raise Refusal(f"non-finite JSON number: {value}")
    return result


def _closed_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise Refusal("duplicate JSON key")
        result[key] = value
    return result


def _safe_relative(path: str) -> PurePosixPath:
    if not isinstance(path, str) or not path:
        raise Refusal("unsafe repository path")
    try:
        encoded = path.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise Refusal("unsafe repository path") from exc
    if len(encoded) > 1024 or any(byte < 0x20 or byte > 0x7E for byte in encoded):
        raise Refusal("unsafe repository path")
    candidate = PurePosixPath(path)
    if (
        candidate.is_absolute()
        or "\\" in path
        or not candidate.parts
        or candidate.as_posix() != path
    ):
        raise Refusal("unsafe repository path")
    if any(part in ("", ".", "..") for part in candidate.parts):
        raise Refusal("unsafe repository path")
    return candidate


def _identity(item: os.stat_result) -> tuple[int, ...]:
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )


def _directory_identity(item: os.stat_result) -> tuple[int, ...]:
    return (item.st_dev, item.st_ino, item.st_mode)


def _rename_stable_identity(item: os.stat_result) -> tuple[int, ...]:
    """Bind one file object across a same-directory atomic replacement."""
    return (
        item.st_dev,
        item.st_ino,
        item.st_mode,
        item.st_nlink,
        item.st_uid,
        item.st_gid,
        item.st_size,
        item.st_mtime_ns,
    )


def _repository_relative(path: Path, label: str) -> PurePosixPath:
    try:
        relative = path.relative_to(ROOT).as_posix()
    except ValueError as exc:
        raise Refusal(f"{label} leaves repository") from exc
    return _safe_relative(relative)


def _confined_output(
    path: Path,
    label: str,
    *,
    exact: tuple[PurePosixPath, ...],
    roots: tuple[PurePosixPath, ...],
) -> Path:
    relative = _repository_relative(path, label)
    if relative in exact or any(
        relative == root or root in relative.parents for root in roots
    ):
        return ROOT / Path(*relative.parts)
    raise Refusal(f"{label} leaves its owned output scope")


def _directory_flags() -> int:
    if not hasattr(os, "O_DIRECTORY") or not hasattr(os, "O_NOFOLLOW"):
        raise Refusal("descriptor-relative no-follow operations are unavailable")
    flags = os.O_RDONLY
    return flags | os.O_DIRECTORY | os.O_NOFOLLOW


def _regular_read_flags() -> int:
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_NONBLOCK"):
        raise Refusal("nonblocking no-follow input reads are unavailable")
    return os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK


def _open_parent(
    relative: PurePosixPath, *, create: bool, label: str
) -> tuple[int, str]:
    """Open a repository-relative parent one no-follow component at a time."""
    flags = _directory_flags()
    try:
        descriptor = os.open(ROOT, flags)
    except OSError as exc:
        raise Refusal(f"{label} root is unavailable or unsafe") from exc
    try:
        for part in relative.parent.parts:
            try:
                child = os.open(part, flags, dir_fd=descriptor)
            except FileNotFoundError:
                if not create:
                    raise Refusal(f"{label} parent is unavailable or unsafe")
                try:
                    os.mkdir(part, mode=0o755, dir_fd=descriptor)
                    child = os.open(part, flags, dir_fd=descriptor)
                except OSError as exc:
                    raise Refusal(f"{label} parent is unavailable or unsafe") from exc
            except OSError as exc:
                raise Refusal(f"{label} parent is unavailable or unsafe") from exc
            metadata = os.fstat(child)
            if not stat.S_ISDIR(metadata.st_mode):
                os.close(child)
                raise Refusal(f"{label} parent is unavailable or unsafe")
            os.close(descriptor)
            descriptor = child
        return descriptor, relative.name
    except BaseException:
        os.close(descriptor)
        raise


def _read_descriptor(descriptor: int, limit: int) -> tuple[bytes, os.stat_result]:
    before = os.fstat(descriptor)
    _validate_input_metadata(before.st_mode, before.st_nlink, before.st_size, limit)
    chunks: list[bytes] = []
    size = 0
    while True:
        chunk = os.read(descriptor, min(65_536, limit + 1 - size))
        if not chunk:
            break
        chunks.append(chunk)
        size += len(chunk)
        if size > limit:
            raise Refusal("input exceeds byte limit")
    after = os.fstat(descriptor)
    _require_unchanged_input(_identity(before), _identity(after))
    return b"".join(chunks), after


def _validate_input_metadata(mode: int, links: int, size: int, limit: int) -> None:
    """Apply the regular-file and byte predicates used by every input read."""
    if not stat.S_ISREG(mode) or links != 1:
        raise Refusal("input is not a single-link regular file")
    if size > limit:
        raise Refusal("input exceeds byte limit")


def _require_unchanged_input(before: tuple[int, ...], after: tuple[int, ...]) -> None:
    """Keep the concurrent-change predicate independently exercisable."""
    if before != after:
        raise Refusal("input changed during read")


def _read_regular(path: Path, limit: int) -> bytes:
    relative = _repository_relative(path, "path")
    flags = _regular_read_flags()
    parent, name = _open_parent(relative, create=False, label="input")
    try:
        descriptor = os.open(name, flags, dir_fd=parent)
    except OSError as exc:
        os.close(parent)
        raise Refusal("input is unavailable or unsafe") from exc
    try:
        data, after = _read_descriptor(descriptor, limit)
    finally:
        os.close(descriptor)
        os.close(parent)

    current_parent, current_name = _open_parent(relative, create=False, label="input")
    try:
        try:
            current = os.open(current_name, flags, dir_fd=current_parent)
        except OSError as exc:
            raise Refusal("input changed during read") from exc
        try:
            _require_unchanged_input(_identity(after), _identity(os.fstat(current)))
        finally:
            os.close(current)
    finally:
        os.close(current_parent)
    return data


def _preflight_json(raw: bytes) -> None:
    depth = 0
    tokens = 0
    in_string = False
    escaped = False
    for byte in raw:
        if in_string:
            if escaped:
                escaped = False
            elif byte == 0x5C:
                escaped = True
            elif byte == 0x22:
                in_string = False
            continue
        if byte == 0x22:
            in_string = True
        elif byte in (0x7B, 0x5B):
            depth += 1
            tokens += 1
            if depth > MAX_JSON_DEPTH:
                raise Refusal("record exceeds JSON depth limit")
        elif byte in (0x7D, 0x5D):
            depth -= 1
        elif byte in (0x2C, 0x3A):
            tokens += 1
        if tokens > MAX_JSON_TOKENS:
            raise Refusal("record exceeds JSON token limit")


def _decode_record(raw: bytes) -> dict[str, Any]:
    _preflight_json(raw)
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_closed_object,
            parse_int=_parse_integer,
            parse_float=_parse_float,
            parse_constant=_reject_constant,
        )
    except Refusal:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise Refusal("record is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise Refusal("record root must be an object")
    if _canonical_json(value) != raw:
        raise Refusal("record is not canonical JSON")
    return value


def _load_record(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular(path, MAX_JSON_BYTES)
    value = _decode_record(raw)
    return value, raw


def _require_fields(
    value: dict[str, Any], required: Iterable[str], allowed: Iterable[str], where: str
) -> None:
    if not isinstance(value, dict):
        raise Refusal(f"{where} must be an object")
    required_set = set(required)
    allowed_set = set(allowed)
    keys = set(value)
    if not required_set <= keys or not keys <= allowed_set:
        raise Refusal(f"{where} has a non-closed field set")


def _git_executable() -> str:
    """Select Git from a closed set of absolute, system-owned paths."""
    for candidate in (Path("/usr/bin/git"), Path("/bin/git")):
        try:
            resolved = candidate.resolve(strict=True)
            metadata = resolved.stat()
        except OSError:
            continue
        if (
            stat.S_ISREG(metadata.st_mode)
            and metadata.st_mode & 0o111
            and metadata.st_uid == 0
            and not metadata.st_mode & 0o022
        ):
            return str(resolved)
    raise Refusal("bounded Git executable is unavailable or unsafe")


def _git(
    arguments: list[str],
    limit: int = MAX_GIT_OUTPUT,
    *,
    input_data: bytes | None = None,
) -> bytes:
    if input_data is not None and len(input_data) > 4_096:
        raise Refusal("bounded Git input exceeded its limit")
    environment = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_LITERAL_PATHSPECS": "1",
        "GIT_NO_LAZY_FETCH": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
    }
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            [
                _git_executable(),
                "--no-lazy-fetch",
                "--no-optional-locks",
                "-C",
                str(ROOT),
                *arguments,
            ],
            stdin=(
                subprocess.PIPE if input_data is not None else subprocess.DEVNULL
            ),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            start_new_session=True,
        )
    except OSError as exc:
        raise Refusal("bounded Git read failed") from exc
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
                raise Refusal("bounded Git input failed") from exc
        selector.register(process.stdout, selectors.EVENT_READ, (stdout, limit))
        selector.register(process.stderr, selectors.EVENT_READ, (stderr, 65_536))
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Refusal("bounded Git read timed out")
            try:
                events = selector.select(remaining)
            except OSError as exc:
                raise Refusal("bounded Git output capture failed") from exc
            if not events:
                raise Refusal("bounded Git read timed out")
            for key, _ in events:
                buffer, cap = key.data
                try:
                    chunk = os.read(key.fd, min(65_536, cap + 1 - len(buffer)))
                except OSError as exc:
                    raise Refusal("bounded Git output capture failed") from exc
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffer.extend(chunk)
                if len(buffer) > cap:
                    raise Refusal("bounded Git output exceeded its limit")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Refusal("bounded Git read timed out")
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise Refusal("bounded Git read timed out") from exc
        # Reaping releases the numeric process-group id. Do not signal that id
        # afterwards: another session may own it by the time cleanup runs.
        leader_reaped = True
        if returncode != 0:
            raise Refusal("bounded Git read refused the source")
        return bytes(stdout)
    finally:
        selector.close()
        # Popen sets returncode before wait returns. Preserve that evidence if
        # an asynchronous exception lands between the return and assignment.
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
        try:
            process.stdout.close()
            process.stderr.close()
        except OSError:
            pass
        if process.stdin is not None and not process.stdin.closed:
            try:
                process.stdin.close()
            except OSError:
                pass


@lru_cache(maxsize=1)
def _source_mode() -> str:
    """Use the pinned Git object when present, or its bound checkout snapshot."""
    expression = f"{SOURCE_REF}^{{commit}}"
    probe = _git(
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        128,
        input_data=f"{expression}\n".encode("ascii"),
    )
    if probe == f"{SOURCE_REF} commit\n".encode("ascii"):
        return "git"
    if probe != f"{expression} missing\n".encode("ascii"):
        raise Refusal("bounded Git read returned an unexpected source identity")
    shallow = _git(["rev-parse", "--is-shallow-repository"], 16)
    if shallow != b"true\n":
        raise Refusal("pinned source commit is absent from a non-shallow repository")
    return "inventory"


def _collect_snapshot_evidence(
    value: Any,
    digests: dict[str, tuple[int | None, str]],
    spans: list[tuple[str, int, int, str]],
) -> None:
    """Collect only source-bound evidence records from inventory-bound JSON."""
    if isinstance(value, list):
        for item in value:
            _collect_snapshot_evidence(item, digests, spans)
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
        source_sha256 = value["source_sha256"]
        span_sha256 = value["span_sha256"]
        start = value["start"]
        end = value["end"]
        if (
            not isinstance(path, str)
            or not isinstance(source_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", source_sha256) is None
            or not isinstance(span_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", span_sha256) is None
            or type(start) is not int
            or type(end) is not int
            or start < 0
            or end <= start
        ):
            raise Refusal("inventory snapshot evidence is malformed")
        _safe_relative(path)
        existing = digests.get(path)
        if existing is not None and existing[1] != source_sha256:
            raise Refusal(f"inventory snapshot has conflicting source digests: {path}")
        digests[path] = (existing[0] if existing is not None else None, source_sha256)
        spans.append((path, start, end, span_sha256))
    for item in value.values():
        _collect_snapshot_evidence(item, digests, spans)


@lru_cache(maxsize=1)
def _inventory_source_snapshot() -> dict[str, Any]:
    """Recover frozen source bytes from a signed shallow checkout.

    The artifact inventory is the publication commit point. It binds the
    manifest, profiles, and graph whose source digests admit checkout bytes.
    This path is available only when Git reports a shallow repository and the
    pinned commit object is absent.
    """
    requested = {
        name: ROOT / Path(*BASELINE_FIXTURE_ROOT.parts) / name
        for name in BASELINE_RECORD_NAMES
    }
    records = _load_committed_baseline(requested)
    manifest = records["corpus-manifest.json"][0]
    profiles = records["invocation-profiles.json"][0]
    graph = records["loader-graph.json"][0]
    if (
        not isinstance(manifest, dict)
        or set(manifest) != {"counts", "documents", "schema", "source", "totals"}
        or manifest.get("schema") != f"{SCHEMA_PREFIX}-corpus-manifest/v1"
        or not isinstance(manifest.get("source"), dict)
        or set(manifest["source"])
        != {"ref", "repository_paths", "tree_sha256"}
        or manifest["source"].get("ref") != SOURCE_REF
        or not isinstance(manifest.get("documents"), list)
    ):
        raise Refusal("inventory snapshot manifest is malformed")

    repository_paths = manifest["source"].get("repository_paths")
    if (
        not isinstance(repository_paths, list)
        or not repository_paths
        or len(repository_paths) > MAX_FROZEN_TREE_PATHS
        or any(not isinstance(path, str) for path in repository_paths)
        or repository_paths != sorted(set(repository_paths))
    ):
        raise Refusal("inventory snapshot repository paths are malformed")
    for path in repository_paths:
        _safe_relative(path)

    digests: dict[str, tuple[int | None, str]] = {}
    corpus_paths: list[str] = []
    tree_paths = set(repository_paths)
    for document in manifest["documents"]:
        if not isinstance(document, dict):
            raise Refusal("inventory snapshot document is malformed")
        path = document.get("path")
        size = document.get("bytes")
        digest = document.get("sha256")
        if (
            not isinstance(path, str)
            or type(size) is not int
            or size < 1
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise Refusal("inventory snapshot document identity is malformed")
        _safe_relative(path)
        if path in digests:
            raise Refusal("inventory snapshot document paths are duplicated")
        digests[path] = (size, digest)
        corpus_paths.append(path)
    if corpus_paths != sorted(corpus_paths):
        raise Refusal("inventory snapshot document paths are not canonical")
    if len(corpus_paths) != EXPECTED_TOTALS["physical_files"]:
        raise Refusal("inventory snapshot document count drift")
    if not set(corpus_paths) <= tree_paths:
        raise Refusal("inventory snapshot omits a corpus path")
    tree_rows = [
        f"{path}\0{digests[path][0]}\0{digests[path][1]}\n"
        for path in corpus_paths
    ]
    if _sha256("".join(tree_rows).encode("utf-8")) != manifest["source"].get(
        "tree_sha256"
    ):
        raise Refusal("inventory snapshot source tree digest mismatch")

    spans: list[tuple[str, int, int, str]] = []
    for record in (manifest, profiles, graph):
        _collect_snapshot_evidence(record, digests, spans)
    excluded_links = graph.get("excluded_links")
    if not isinstance(excluded_links, list):
        raise Refusal("inventory snapshot excluded-link set is malformed")
    for record in excluded_links:
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            raise Refusal("inventory snapshot excluded link is malformed")
        path = str(_safe_relative(record["path"]))
        if path not in tree_paths and record.get("class") != "dynamic_target":
            raise Refusal("inventory snapshot omits an excluded link")
    if not set(digests) <= tree_paths:
        raise Refusal("inventory snapshot omits a source evidence path")

    sources: dict[str, bytes] = {}
    for path, (expected_size, expected_digest) in sorted(digests.items()):
        data = _read_regular(ROOT / Path(*PurePosixPath(path).parts), MAX_SOURCE_BYTES)
        if (
            (expected_size is not None and len(data) != expected_size)
            or _sha256(data) != expected_digest
        ):
            raise Refusal(f"inventory snapshot source drift: {path}")
        sources[path] = data
    for path, start, end, span_sha256 in spans:
        data = sources[path]
        if end > len(data) or _sha256(data[start:end]) != span_sha256:
            raise Refusal(f"inventory snapshot span drift: {path}")
    return {
        "corpus_paths": tuple(corpus_paths),
        "sources": sources,
        "tree_paths": tuple(repository_paths),
    }


@lru_cache(maxsize=256)
def _source_object(path: str) -> bytes:
    _safe_relative(path)
    if _source_mode() == "git":
        return _git(["cat-file", "blob", f"{SOURCE_REF}:{path}"], MAX_SOURCE_BYTES)
    source = _inventory_source_snapshot()["sources"].get(path)
    if source is None:
        raise Refusal(f"source is absent from the inventory snapshot: {path}")
    return source


def _source_blob(path: str) -> bytes:
    blob = _source_object(path)
    live = _read_regular(ROOT / path, MAX_SOURCE_BYTES)
    if live != blob:
        raise Refusal(f"source drift: {path}")
    return blob


@lru_cache(maxsize=1)
def _frozen_tree_paths() -> tuple[str, ...]:
    if _source_mode() == "inventory":
        return _inventory_source_snapshot()["tree_paths"]
    raw = _git(["ls-tree", "-r", "-z", "--name-only", SOURCE_REF])
    path_count = raw.count(b"\0")
    if (
        not raw
        or not raw.endswith(b"\0")
        or raw.startswith(b"\0")
        or b"\0\0" in raw
    ):
        raise Refusal("Git tree path inventory is not canonical")
    if path_count > MAX_FROZEN_TREE_PATHS:
        raise Refusal("Git tree path inventory exceeds its path count limit")
    try:
        names = [
            item.decode("utf-8", errors="strict") for item in raw.split(b"\0")[:-1]
        ]
    except UnicodeDecodeError as exc:
        raise Refusal("Git tree contains a non-UTF-8 path") from exc
    if not names or len(names) != path_count or len(names) > MAX_FROZEN_TREE_PATHS:
        raise Refusal("Git tree path inventory exceeds its path count limit")
    if names != sorted(set(names)):
        raise Refusal("Git tree path inventory is not canonical")
    for name in names:
        _safe_relative(name)
    return tuple(names)


def _corpus_paths() -> list[str]:
    names = list(_frozen_tree_paths())
    selected: list[str] = []
    for name in names:
        if name == "AGENTS.md" or (
            name.startswith("plugins/") and name.endswith("/AGENTS.md")
        ):
            selected.append(name)
        elif name == "PROMISE_MACHINE.md" or (
            name.startswith("plugins/") and name.endswith("/PROMISE_MACHINE.md")
        ):
            selected.append(name)
        elif name == ".agents/skills/promise-machine/SKILL.md":
            selected.append(name)
        elif (
            name.startswith("plugins/")
            and name.endswith("/SKILL.md")
            and "/tests/" not in name
        ):
            selected.append(name)
        elif re.fullmatch(
            r"plugins/[^/]+/(?:skills/.+/)?references/.+", name
        ):
            selected.append(name)
    structured = _structured_metadata()
    missing_structured = set(structured) - set(names)
    if missing_structured:
        raise Refusal(f"structured reference missing: {min(missing_structured)}")
    selected_structured = {
        path for path in selected if not path.lower().endswith(".md")
    }
    reference_structured = {
        path
        for path in structured
        if "/references/" in path
    }
    if selected_structured != reference_structured:
        missing = sorted(reference_structured - selected_structured)
        extra = sorted(selected_structured - reference_structured)
        detail = missing[0] if missing else extra[0]
        raise Refusal(f"structured reference topology drift: {detail}")
    selected.extend(
        sorted(path for path in structured if path not in reference_structured)
    )
    fixed_agent = _fixed_agent_metadata()
    missing_fixed_agent = set(fixed_agent) - set(names)
    if missing_fixed_agent:
        raise Refusal(f"fixed agent input missing: {min(missing_fixed_agent)}")
    selected.extend(sorted(fixed_agent))
    admitted = set(_additional_metadata())
    missing = admitted - set(names)
    if missing:
        raise Refusal(f"admitted source missing at frozen ref: {min(missing)}")
    selected.extend(sorted(admitted))
    result = sorted(set(selected))
    if len(result) != len(selected):
        raise Refusal("corpus selection produced duplicate paths")
    if any(path.startswith("distribution/skills-runtime/") for path in result):
        raise Refusal("moved skills-runtime package entered the corpus")
    return result


def _document_class(path: str) -> str:
    if path in _fixed_agent_metadata():
        return "fixed_input"
    if path in _structured_metadata():
        return "structured_reference"
    admission = _additional_metadata().get(path)
    if admission is not None:
        return admission["document_class"]
    if path == "AGENTS.md" or path.endswith("/AGENTS.md"):
        return "runtime_contract"
    if path == "PROMISE_MACHINE.md" or path.endswith("/PROMISE_MACHINE.md"):
        return "promise_machine_contract"
    if path.endswith("/SKILL.md"):
        return "skill_contract"
    return "markdown_reference"


def _fixed_point_exclusion(
    source: str, source_class: str, target: str
) -> str | None:
    """Classify a local Markdown link that is not already in the corpus."""
    target_path = PurePosixPath(target)
    name = target_path.name.lower()
    if source_class == "frontier_ledger":
        return "historical-ledger-evidence"
    if (source, target) in {(item[2], item[1]) for item in EXCLUDED_LINK_CLASSES}:
        return "explicit-non-operative-link"
    if name in {"changelog.md", "contributing.md", "license.md", "readme.md"}:
        return "reader-background"
    if FIXED_POINT_EXCLUDED_COMPONENTS & set(target_path.parts):
        return "decision-example-or-evidence"
    if (source, target) in FIXED_POINT_PROVENANCE_LINKS:
        return "delivery-provenance-or-source-history"
    return None


def _derive_operative_markdown_targets(
    documents: list[dict[str, Any]],
    *,
    source_overrides: dict[str, bytes] | None = None,
    tree_paths: set[str] | None = None,
) -> dict[str, Any]:
    """Independently derive existing local Markdown targets from admitted bytes."""
    overrides = source_overrides or {}
    by_path = {item["path"]: item for item in documents}
    if len(by_path) != len(documents) or not set(overrides) <= set(by_path):
        raise Refusal("fixed-point source inventory is invalid")
    frozen_tree = set(_frozen_tree_paths()) if tree_paths is None else set(tree_paths)
    for path in frozen_tree:
        _safe_relative(path)
    targets: set[str] = set()
    excluded: list[dict[str, str]] = []
    occurrences = 0
    for source, item in sorted(by_path.items()):
        data = overrides[source] if source in overrides else _source_blob(source)
        if len(data) > MAX_SOURCE_BYTES:
            raise Refusal(f"fixed-point source exceeds byte limit: {source}")
        try:
            text = data.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise Refusal(f"fixed-point source is not UTF-8: {source}") from exc
        _preflight_markdown_links(text, source)
        for match in INLINE_MARKDOWN_LINK.finditer(text):
            raw_target = match.group(1)
            repository_target = _same_repository_markdown_url(raw_target)
            if repository_target is not None:
                target = repository_target
            else:
                if raw_target.startswith(("#", "http://", "https://", "mailto:")):
                    continue
                relative = raw_target.split("#", 1)[0].split("?", 1)[0]
                if not relative.lower().endswith(".md"):
                    continue
                target = posixpath.normpath(
                    posixpath.join(posixpath.dirname(source), relative)
                )
                try:
                    _safe_relative(target)
                except Refusal:
                    continue
            if target not in frozen_tree:
                continue
            occurrences += 1
            if target in by_path:
                targets.add(target)
                continue
            exclusion = _fixed_point_exclusion(
                source, item["document_class"], target
            )
            if exclusion is None:
                targets.add(target)
            else:
                excluded.append(
                    {"class": exclusion, "source": source, "target": target}
                )
    return {
        "occurrences": occurrences,
        "targets": sorted(targets),
        "excluded": sorted(
            excluded, key=lambda item: (item["source"], item["target"], item["class"])
        ),
    }


def _derive_corpus_fixed_point(
    documents: list[dict[str, Any]],
    *,
    source_overrides: dict[str, bytes] | None = None,
    tree_paths: set[str] | None = None,
) -> dict[str, Any]:
    """Derive operative Markdown plus extension-agnostic structured inputs."""
    overrides = source_overrides or {}
    frozen_tree = set(_frozen_tree_paths()) if tree_paths is None else set(tree_paths)
    for path in frozen_tree:
        _safe_relative(path)
    anchor_paths = {
        path
        for metadata in _structured_metadata().values()
        for path in (metadata["source_path"], metadata["runtime_path"])
        if path is not None
    }
    anchor_paths.update(
        metadata["source_path"] for metadata in _fixed_agent_metadata().values()
    )
    document_paths = {item["path"] for item in documents}
    if not set(overrides) <= document_paths | anchor_paths:
        raise Refusal("fixed-point source inventory is invalid")
    markdown = _derive_operative_markdown_targets(
        documents,
        source_overrides={
            path: data for path, data in overrides.items() if path in document_paths
        },
        tree_paths=frozen_tree,
    )
    reference_structured = {
        path
        for path in frozen_tree
        if re.fullmatch(r"plugins/[^/]+/(?:skills/.+/)?references/.+", path)
        and not path.lower().endswith(".md")
    }
    mandatory_executable: set[str] = set()
    for path, metadata in _structured_metadata().items():
        if metadata["load_semantics"] != "mandatory-executable":
            continue
        source_path = metadata["source_path"]
        runtime_path = metadata["runtime_path"]
        runtime_needle = metadata["runtime_needle"]
        if runtime_path is None or runtime_needle is None:
            raise Refusal(f"mandatory data lacks a runtime anchor: {path}")
        source_data = (
            overrides[source_path]
            if source_path in overrides
            else _source_blob(source_path)
        )
        runtime_data = (
            overrides[runtime_path]
            if runtime_path in overrides
            else _source_blob(runtime_path)
        )
        if (
            path in frozen_tree
            and metadata["source_needle"].encode("utf-8") in source_data
            and runtime_needle.encode("utf-8") in runtime_data
        ):
            mandatory_executable.add(path)
    mandatory_data = {
        path
        for path in mandatory_executable
        if _structured_metadata()[path]["admission_kind"] == "mandatory-rule-data"
    }
    structured = reference_structured | mandatory_data
    fixed_agent: set[str] = set()
    for path, metadata in _fixed_agent_metadata().items():
        source_data = (
            overrides[metadata["source_path"]]
            if metadata["source_path"] in overrides
            else _source_blob(metadata["source_path"])
        )
        if (
            path in frozen_tree
            and metadata["source_needle"].encode("utf-8") in source_data
        ):
            fixed_agent.add(path)
    return {
        "occurrences": markdown["occurrences"],
        "markdown_targets": markdown["targets"],
        "structured_targets": sorted(structured),
        "mandatory_executable_targets": sorted(mandatory_executable),
        "fixed_agent_targets": sorted(fixed_agent),
        "targets": sorted(set(markdown["targets"]) | structured | fixed_agent),
        "excluded": markdown["excluded"],
    }


def _plugin(path: str) -> str | None:
    parts = PurePosixPath(path).parts
    return parts[1] if len(parts) > 1 and parts[0] == "plugins" else None


def _reference_owner(path: str) -> str:
    parts = list(PurePosixPath(path).parts)
    index = parts.index("references")
    return PurePosixPath(*parts[:index], "SKILL.md").as_posix()


@lru_cache(maxsize=64)
def _skill_name(path: str) -> str:
    text = _source_blob(path).decode("utf-8", errors="strict")
    match = re.search(r"(?m)^name:\s*([^\s]+)\s*$", text[:4096])
    if match:
        return match.group(1)
    return PurePosixPath(path).parent.name


def _logical_document(path: str, document_class: str) -> str:
    if document_class == "promise_machine_contract":
        return "promise-machine/v1"
    if path == "AGENTS.md":
        return "suite-runtime"
    if document_class == "runtime_contract":
        return f"plugin:{_plugin(path)}"
    if document_class in ("identity_contract", "identity_roster"):
        return "suite-identity"
    if document_class == "router_install_contract":
        return "promise-machine/router"
    if document_class in ("overlay_contract", "frontier_policy"):
        return "plugin:hexaemeron"
    if document_class in ("frontier_ledger", "worker_prompt", "operation_reference"):
        owner = _additional_metadata()[path]["canonical_owner"]
        return f"skill:{_skill_name(owner)}"
    if document_class == "markdown_reference":
        return f"skill:{_skill_name(_reference_owner(path))}"
    if document_class == "fixed_input":
        if path == ".python-version":
            return "suite-runtime"
        owner = _fixed_agent_metadata()[path]["canonical_owner"]
        return f"skill:{_skill_name(owner)}"
    if document_class == "structured_reference":
        owner = _structured_metadata()[path]["canonical_owner"]
        return f"skill:{_skill_name(owner)}"
    return f"skill:{_skill_name(path)}"


def _authority_tier(path: str, document_class: str) -> str:
    if path == "AGENTS.md":
        return "suite_runtime"
    if path == "PROMISE_MACHINE.md":
        return "suite_law"
    if document_class == "promise_machine_contract":
        return "generated_copy"
    if path == ".agents/skills/promise-machine/SKILL.md":
        return "router"
    if document_class == "runtime_contract":
        return "plugin_runtime"
    if document_class == "skill_contract":
        return "canonical_skill"
    if document_class == "fixed_input":
        return "fixed_input"
    if document_class == "structured_reference":
        return "conditional_reference"
    additional = {
        "identity_contract": "suite_identity",
        "identity_roster": "identity_roster",
        "router_install_contract": "router_install",
        "overlay_contract": "plugin_overlay",
        "frontier_policy": "frontier_policy",
        "frontier_ledger": "frontier_ledger",
        "worker_prompt": "worker_prompt",
        "operation_reference": "conditional_reference",
    }
    if document_class in additional:
        return additional[document_class]
    return "conditional_reference"


def _external_owner(path: str) -> str | None:
    if any(path.startswith(prefix) for prefix in EXTERNAL_SKILL_PREFIXES):
        return "upstream-pashov"
    return None


def _same_repository_markdown_url(value: str) -> str | None:
    """Map only a known canonical URL into this pinned source repository."""
    return SAME_REPOSITORY_MARKDOWN_URLS.get(value)


def _canonical_owner(path: str, document_class: str) -> str:
    if document_class == "fixed_input":
        return _fixed_agent_metadata()[path]["canonical_owner"]
    if document_class == "structured_reference":
        return _structured_metadata()[path]["canonical_owner"]
    admission = _additional_metadata().get(path)
    if admission is not None:
        return admission["canonical_owner"]
    if document_class == "markdown_reference":
        return _reference_owner(path)
    if document_class == "promise_machine_contract":
        return "PROMISE_MACHINE.md"
    return path


def build_manifest(profiles: dict[str, Any] | None = None) -> dict[str, Any]:
    repository_paths = list(_frozen_tree_paths())
    paths = _corpus_paths()
    provisional: list[dict[str, Any]] = []
    by_digest: dict[str, list[str]] = {}
    for path in paths:
        blob = _source_blob(path)
        digest = _sha256(blob)
        by_digest.setdefault(digest, []).append(path)
        document_class = _document_class(path)
        owner = _canonical_owner(path, document_class)
        admission = _additional_metadata().get(path)
        structured = _structured_metadata().get(path)
        fixed_agent = _fixed_agent_metadata().get(path)
        reference_only = REFERENCE_ONLY_MARKDOWN.get(path)
        provisional.append(
            {
                "path": path,
                "logical_document": _logical_document(path, document_class),
                "document_class": document_class,
                "admission_kind": (
                    structured["admission_kind"]
                    if structured is not None
                    else fixed_agent["admission_kind"]
                    if fixed_agent is not None
                    else (
                        "issue-census"
                        if admission is None
                        else admission["admission_kind"]
                    )
                ),
                "bytes": len(blob),
                "sha256": digest,
                "exact_duplicate_group": None,
                "canonical_content_path": None,
                "canonical_owner": owner,
                "authority_tier": _authority_tier(path, document_class),
                "load_semantics": (
                    structured["load_semantics"]
                    if structured is not None
                    else fixed_agent["load_semantics"]
                    if fixed_agent is not None
                    else "reference-only"
                    if reference_only is not None
                    else "agent-or-prompt"
                ),
                "loader_roots": [],
                "scenario_reachability": [],
                "source_evidence": (
                    _evidence(
                        structured["source_path"], structured["source_needle"]
                    )
                    if structured is not None
                    else _evidence(
                        fixed_agent["source_path"], fixed_agent["source_needle"]
                    )
                    if fixed_agent is not None
                    else _evidence(reference_only[0], reference_only[1])
                    if reference_only is not None
                    else None
                ),
                "runtime_evidence": (
                    _evidence(
                        structured["runtime_path"], structured["runtime_needle"]
                    )
                    if structured is not None
                    and structured["runtime_path"] is not None
                    else None
                ),
                "external_runtime_owner": _external_owner(path),
            }
        )
    closure = _derive_corpus_fixed_point(provisional)
    missing_closure = set(closure["targets"]) - set(paths)
    if missing_closure:
        raise Refusal(f"corpus fixed point omits {min(missing_closure)}")
    if set(closure["structured_targets"]) != set(_structured_metadata()):
        raise Refusal("structured fixed-point inventory disagrees with its anchors")
    if set(closure["fixed_agent_targets"]) != set(_fixed_agent_metadata()):
        raise Refusal("fixed agent input inventory disagrees with its anchors")
    if set(closure["mandatory_executable_targets"]) != {
        path
        for path, metadata in _structured_metadata().items()
        if metadata["load_semantics"] == "mandatory-executable"
    }:
        raise Refusal("mandatory executable semantics disagree with live anchors")
    topology = _build_topology(provisional, profiles)
    loader_reachability = _reachability_by_root(
        topology["roots"], topology["edges"], "active_roots"
    )
    scenario_reachability = _reachability_by_root(
        topology["scenario_roots"],
        topology["scenario_edges"],
        "active_scenarios",
    )
    for record in provisional:
        record["loader_roots"] = sorted(
            loader_reachability.get(record["path"], set())
        )
        record["scenario_reachability"] = sorted(
            scenario_reachability.get(record["path"], set())
        )
        if record["load_semantics"] == "reference-only":
            if record["loader_roots"] or record["scenario_reachability"]:
                raise Refusal(
                    f"reference-only document became reachable: {record['path']}"
                )
        elif not record["loader_roots"] or not record["scenario_reachability"]:
            raise Refusal(f"unreachable admitted document: {record['path']}")
    canonical_by_digest: dict[str, str] = {}
    for digest, members in by_digest.items():
        canonical_by_digest[digest] = (
            "PROMISE_MACHINE.md" if "PROMISE_MACHINE.md" in members else min(members)
        )
    for record in provisional:
        members = by_digest[record["sha256"]]
        record["canonical_content_path"] = canonical_by_digest[record["sha256"]]
        if len(members) > 1:
            record["exact_duplicate_group"] = f"sha256:{record['sha256']}"
    class_counts = {
        name: sum(1 for item in provisional if item["document_class"] == name)
        for name in sorted(EXPECTED_COUNTS)
    }
    unique_records = [
        item for item in provisional if item["path"] == item["canonical_content_path"]
    ]
    totals = {
        "physical_files": len(provisional),
        "physical_bytes": sum(item["bytes"] for item in provisional),
        "unique_files": len(unique_records),
        "unique_bytes": sum(item["bytes"] for item in unique_records),
    }
    if class_counts != EXPECTED_COUNTS:
        raise Refusal(f"corpus class count drift: {class_counts}")
    if totals != EXPECTED_TOTALS:
        raise Refusal(f"corpus denominator drift: {totals}")
    tree_rows = [
        f"{item['path']}\0{item['bytes']}\0{item['sha256']}\n" for item in provisional
    ]
    return {
        "schema": f"{SCHEMA_PREFIX}-corpus-manifest/v1",
        "source": {
            "ref": SOURCE_REF,
            "repository_paths": repository_paths,
            "tree_sha256": _sha256("".join(tree_rows).encode("utf-8")),
        },
        "counts": class_counts,
        "totals": totals,
        "documents": provisional,
    }


def _artifact_digest(value: dict[str, Any]) -> str:
    return _sha256(_canonical_json(value))


def _evidence(path: str, needle: str) -> dict[str, Any]:
    data = _source_blob(path)
    encoded = needle.encode("utf-8")
    start = data.find(encoded)
    if start < 0:
        raise Refusal(f"loader evidence missing in {path}")
    end = start + len(encoded)
    return {
        "path": path,
        "start": start,
        "end": end,
        "source_sha256": _sha256(data),
        "span_sha256": _sha256(data[start:end]),
    }


def _profile_semantic_anchor(
    selected_skill: str, branch_state: tuple[str, ...], obligation: str
) -> tuple[str, str]:
    """Resolve generic-path obligations to a source sentence naming the relation."""
    selected = SELECTABLE_SKILL_PATHS[selected_skill]
    skill_by_path = {path: skill for skill, path in SELECTABLE_SKILL_PATHS.items()}

    if obligation.endswith("/EVOLUTION.md"):
        selected_evolution = str(PurePosixPath(selected).with_name("EVOLUTION.md"))
        if obligation == selected_evolution:
            return selected, "[EVOLUTION.md](EVOLUTION.md)"
        if selected_skill != "kronos":
            raise Refusal("profile frontier relation escapes Kronos")
        return (
            selected,
            "Walk the whole scope and find every `EVOLUTION.md` beneath it, descending\n"
            "   into each plugin's own skills directory.",
        )

    if not obligation.endswith("/SKILL.md") or obligation not in skill_by_path:
        raise Refusal("profile semantic anchor received a non-skill path")
    target_skill = skill_by_path[obligation]

    if selected_skill == "kronos":
        dispatch = branch_state[-1]
        if not dispatch.startswith("dispatch-"):
            raise Refusal("profile Kronos relation escapes dispatch")
        if target_skill not in {"fiat", dispatch.removeprefix("dispatch-")}:
            raise Refusal("profile Kronos dispatch target drift")
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
                SELECTABLE_SKILL_PATHS["elenchus"],
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
            if branch_state[0] == "prose":
                return (
                    "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                    '`python3 "$PLUGIN_ROOT/skills/imprimatur/scripts/imprimatur.py" <file>`',
                )
            if branch_state[0] == "integrate-task-issue":
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
            if branch_state[0].startswith("audit-"):
                return (
                    "plugins/hexaemeron/skills/fiat/references/audit-loop.md",
                    "apply Sapheneia's bounded audit-record operation",
                )
            if branch_state[0] == "prose":
                return (
                    "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
                    "Sapheneia -> Imprimatur -> Vulgate -> Imprimatur",
                )
            return (
                selected,
                "under the repository's Sapheneia,\n"
                "Imprimatur, Vulgate, Imprimatur publication order.",
            )
        raise Refusal(f"profile Fiat skill relation is unowned: {target_skill}")

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
    raise Refusal(
        f"profile skill relation is unowned: {selected_skill} -> {target_skill}"
    )


def _python_pin_profile_anchor(
    selected_skill: str, branch_state: tuple[str, ...]
) -> tuple[str, str]:
    """Bind the suite pin only to operations that normatively require it."""
    profile_id = f"{selected_skill}:{'__'.join(branch_state)}"
    anchors = {
        "anamnesis:demo-or-rebuild": (
            SELECTABLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "anamnesis:ordinary": (
            SELECTABLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "berean:ordinary": (
            SELECTABLE_SKILL_PATHS["berean"],
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
            SELECTABLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:diagnose": (
            SELECTABLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:verify": (
            SELECTABLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
    }
    try:
        return anchors[profile_id]
    except KeyError as exc:
        raise Refusal(f"profile Python pin relation is unowned: {profile_id}") from exc


def _profile_obligation_evidence(
    selected_skill: str,
    branch_state: tuple[str, ...],
    required_documents: tuple[str, ...],
    obligation: str,
) -> dict[str, Any]:
    """Bind one required document to the frozen bytes that require it."""
    selected = SELECTABLE_SKILL_PATHS[selected_skill]
    if obligation == selected:
        evidence = _evidence(selected, f"name: {selected_skill}")
    elif obligation.endswith(("/SKILL.md", "/EVOLUTION.md")):
        source, needle = _profile_semantic_anchor(
            selected_skill, branch_state, obligation
        )
        evidence = _evidence(source, needle)
    elif (
        selected_skill == "kronos"
        and obligation
        == "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"
    ):
        evidence = _evidence(
            selected,
            "`../fiat/references/plugin-currency.md` names the host\n"
            "   mechanism.",
        )
    elif obligation == ".python-version":
        source, needle = _python_pin_profile_anchor(selected_skill, branch_state)
        evidence = _evidence(source, needle)
    else:
        metadata = (
            _additional_metadata().get(obligation)
            or _structured_metadata().get(obligation)
            or _fixed_agent_metadata().get(obligation)
        )
        if metadata is not None:
            needle = metadata["source_needle"]
            if obligation == "plugins/synkrisis/references/rules-v1.json":
                operation = f"operation:synkrisis:{branch_state[-1]}"
                needle = SYNKRISIS_RULE_SOURCE_NEEDLES.get(operation, needle)
            evidence = _evidence(metadata["source_path"], needle)
        elif (
            selected_skill == "ephoros"
            and obligation == SELECTABLE_SKILL_PATHS["phylax"]
        ):
            evidence = _evidence(
                selected,
                "`phylax` sets this rule and this skill inherits it",
            )
        else:
            reachable = set(required_documents) - {obligation}
            link = _reference_link(selected, obligation, reachable)
            if link is None:
                raise Refusal(
                    f"profile obligation has no source witness: "
                    f"{selected_skill}: {obligation}"
                )
            else:
                source, needle = link
                evidence = _evidence(source, needle)
    return {"obligation": obligation, **evidence}


def _profile_source_evidence(
    selected_skill: str,
    branch_state: tuple[str, ...],
    required_documents: tuple[str, ...],
) -> list[dict[str, Any]]:
    """Bind every profile obligation to one attributable frozen source span."""
    return [
        _profile_obligation_evidence(
            selected_skill, branch_state, required_documents, obligation
        )
        for obligation in required_documents
    ]


def _profile_fixed_inputs(required_documents: tuple[str, ...]) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for path in sorted(required_documents):
        metadata = _structured_metadata().get(path)
        if metadata is None:
            metadata = _fixed_agent_metadata().get(path)
        if metadata is None:
            continue
        if metadata["load_semantics"] == "reference-only":
            raise Refusal(f"profile loads a reference-only input: {path}")
        result.append({"path": path, "load_semantics": metadata["load_semantics"]})
    return result


def build_invocation_profiles() -> dict[str, Any]:
    """Expand the finite source-declared bounded invocation grammar."""
    profiles: list[dict[str, Any]] = []
    evolution = {
        name: str(PurePosixPath(path).with_name("EVOLUTION.md"))
        for name, path in SELECTABLE_SKILL_PATHS.items()
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
        *,
        documents: tuple[str, ...] = (),
        workers: tuple[str, ...] = (),
    ) -> None:
        required = tuple(
            sorted(dict.fromkeys((SELECTABLE_SKILL_PATHS[skill],) + documents))
        )
        worker_prompts = tuple(sorted(dict.fromkeys(workers)))
        branch_state = tuple(local_id.split("__"))
        if not set(worker_prompts) <= set(required):
            raise Refusal(f"profile worker leaves required documents: {skill}:{local_id}")
        profile_id = f"{skill}:{local_id}"
        profiles.append(
            {
                "id": profile_id,
                "selected_skill": skill,
                "phase": phase,
                "applicability": f"bounded-operation:{skill}:{phase}",
                "branch_state": list(branch_state),
                "exclusive_group": f"{skill}:{phase}",
                "required_documents": list(required),
                "worker_prompts": list(worker_prompts),
                "fixed_inputs": _profile_fixed_inputs(required),
                "source_evidence": _profile_source_evidence(
                    skill, branch_state, required
                ),
            }
        )

    def frontier(skill: str) -> None:
        add(
            skill,
            "frontier-gate",
            "gate-only frontier admission",
            documents=(evolution[skill], versioning),
        )

    add("alexandria", "ordinary", "capture/query/release")
    add(
        "alexandria",
        "ethereum-usdc-interval",
        "Ethereum USDC interval capture",
        documents=(
            "plugins/alexandria/docs/usdc-interval-collector.md",
            "plugins/alexandria/docs/study.md",
            "plugins/alexandria/docs/runbook.md",
        ),
    )
    frontier("alexandria")

    add(
        "anamnesis",
        "ordinary",
        "capture/verify/release",
        documents=python_pin,
    )
    add(
        "anamnesis",
        "demo-or-rebuild",
        "demo or verify-rebuild",
        documents=python_pin + ("plugins/anamnesis/docs/demo.md",),
    )
    frontier("anamnesis")

    add("ariadne", "ordinary", "inspect/verify/replay")
    for local_id, phase, documents in (
        (
            "capture-release",
            "capture release",
            (
                "plugins/ariadne/docs/capturing-a-release.md",
                "plugins/ariadne/docs/solidity-release.md",
            ),
        ),
        (
            "capture-dataset",
            "capture dataset",
            (
                "plugins/ariadne/docs/capturing-a-dataset.md",
                "plugins/ariadne/docs/dataset.md",
            ),
        ),
        (
            "capture-state-fixture",
            "capture state fixture",
            (
                "plugins/ariadne/docs/capturing-a-state-fixture.md",
                "plugins/ariadne/docs/state-fixture.md",
            ),
        ),
        (
            "capture-grounded-agent",
            "capture grounded agent",
            (
                "plugins/ariadne/docs/capturing-a-grounded-agent.md",
                "plugins/ariadne/docs/grounded-agent.md",
            ),
        ),
        (
            "conformance",
            "conformance",
            ("plugins/ariadne/docs/conformance.md",),
        ),
    ):
        add("ariadne", local_id, phase, documents=documents)
    frontier("ariadne")

    for name in (
        "berean",
        "brevitas",
        "homologia",
        "horos",
        "hypomnema",
        "janus",
        "sapheneia",
        "vulgate",
    ):
        documents = python_pin if name in {"berean", "brevitas"} else ()
        add(name, "ordinary", "ordinary operation", documents=documents)
        frontier(name)

    hermes_runtime = (
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json",
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json",
        "plugins/hermes/skills/hermes/references/optimisation-catalogue.md",
    )
    add(
        "hermes",
        "gas-operation",
        "gas analysis",
        documents=python_pin + hermes_runtime,
    )
    frontier("hermes")

    add("elenchus", "ordinary", "ordinary failure analysis")
    add(
        "elenchus",
        "contract-fix",
        "contract failure",
        documents=(SELECTABLE_SKILL_PATHS["fizz-sync"], promises),
    )
    frontier("elenchus")

    add(
        "ephoros",
        "ordinary",
        "telemetry operation",
        documents=(SELECTABLE_SKILL_PATHS["phylax"],),
    )
    frontier("ephoros")

    fizz_common = tuple(
        f"plugins/hexaemeron/skills/fizz/references/{name}.md"
        for name in ("template-map", "selection-policy", "setup-playbook", "handler-patterns")
    )
    fizz_report = ("plugins/hexaemeron/skills/fizz/agents/report-writer.md",)
    fizz_invariant = (
        "plugins/hexaemeron/skills/fizz/references/property-generation.md",
        *tuple(path for path in FIZZ_WORKER_PROMPTS if path != fizz_report[0] and not path.endswith("protocol-analyzer.md")),
    )
    xray_full = (
        SELECTABLE_SKILL_PATHS["x-ray"],
        xray_version,
        promises,
        "plugins/hexaemeron/skills/x-ray/references/threats.md",
        "plugins/hexaemeron/skills/x-ray/references/templates.md",
    )
    for xray_state, invariant_state in itertools.product(
        ("existing", "acquire", "fallback"), ("off", "on")
    ):
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
        add(
            "fizz",
            f"xray-{xray_state}__invariants-{invariant_state}",
            "fuzz-suite generation",
            documents=documents,
            workers=workers,
        )

    add("fizz-convert", "convert", "property conversion", documents=(promises,))
    add("fizz-sync", "sync", "harness reconciliation", documents=(promises,))

    imprimatur_lexicons = (
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
    )
    add("imprimatur", "lint", "production lint", documents=imprimatur_lexicons)
    frontier("imprimatur")

    add("metron", "ordinary", "measurement")
    add(
        "metron",
        "budget-check",
        "budget check",
        documents=("plugins/hexaemeron/skills/metron/references/budget-check.md",),
    )
    frontier("metron")

    add("phylax", "ordinary", "off-chain review")
    add(
        "phylax",
        "model-proxy",
        "model proxy review",
        documents=("plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",),
    )
    frontier("phylax")

    protasis_disciplines = tuple(
        SELECTABLE_SKILL_PATHS[name]
        for name in ("ephoros", "phylax", "metron", "elenchus", "hypomnema")
    )
    add("protasis", "runbook", "runbook validation")
    add("protasis", "study", "study validation", documents=protasis_disciplines)
    frontier("protasis")

    sol_aud_general = tuple(
        f"plugins/hexaemeron/skills/solidity-auditor/references/{name}.md"
        for name in ("report-formatting", "judging", "senior-auditor-sop")
    )
    sol_aud_agents = tuple(
        path
        for path in _frozen_tree_paths()
        if path.startswith(
            "plugins/hexaemeron/skills/solidity-auditor/references/hacking-agents/"
        )
        and path.endswith("-agent.md")
    )
    sol_aud_shared = (
        "plugins/hexaemeron/skills/solidity-auditor/references/hacking-agents/shared-rules.md",
    )
    add(
        "solidity-auditor",
        "audit",
        "Solidity audit",
        documents=(sol_aud_version, promises)
        + sol_aud_general
        + sol_aud_shared
        + sol_aud_agents,
        workers=sol_aud_agents,
    )
    add(
        "x-ray",
        "audit",
        "pre-audit analysis",
        documents=xray_full[1:],
    )

    add("lazarus", "ordinary", "capture/verify/replay")
    add(
        "lazarus",
        "anchored-capture",
        "anchored capture",
        documents=("plugins/lazarus/docs/chain-anchors.md",),
    )
    add(
        "lazarus",
        "preservation-release",
        "preservation release",
        documents=("plugins/lazarus/docs/preservation-release.md",),
    )
    add(
        "lazarus",
        "maintenance",
        "maintenance",
        documents=("plugins/lazarus/docs/study.md", "plugins/lazarus/docs/runbook.md"),
    )
    frontier("lazarus")

    add("lemma", "ordinary", "generate/verify", documents=python_pin)
    add(
        "lemma",
        "changed-or-unexpected",
        "change/judge/unexpected-output",
        documents=python_pin + ("plugins/lemma/INVARIANTS.md",),
    )
    frontier("lemma")

    add("pandects", "ordinary", "law operation")
    frontier("pandects")

    probitas_base = (
        "plugins/probitas/skills/probitas/references/gates.md",
        "plugins/probitas/skills/probitas/references/venues.md",
    )
    add("probitas", "dossier", "dossier operation", documents=probitas_base)
    add(
        "probitas",
        "add-venue",
        "add venue",
        documents=python_pin
        + probitas_base
        + ("plugins/probitas/docs/adding-a-venue.md",),
    )
    frontier("probitas")

    synkrisis_rules = ("plugins/synkrisis/references/rules-v1.json",)
    add(
        "synkrisis",
        "cohort-or-render",
        "cohort or render",
        documents=python_pin,
    )
    add(
        "synkrisis",
        "diagnose",
        "diagnose",
        documents=python_pin + synkrisis_rules,
    )
    add(
        "synkrisis",
        "verify",
        "verify",
        documents=python_pin + synkrisis_rules,
    )
    frontier("synkrisis")

    add("tabularium", "ordinary", "capture/verify")
    add(
        "tabularium",
        "add-adapter",
        "add adapter",
        documents=("plugins/tabularium/docs/adding-an-adapter.md",),
    )
    add(
        "tabularium",
        "mapping-or-release",
        "correct mapping or release-policy",
        documents=("plugins/tabularium/docs/release-policy.md",),
    )
    frontier("tabularium")

    kronos_own = (evolution["kronos"],)
    kronos_currency = (
        "plugins/hexaemeron/skills/fiat/references/plugin-currency.md",
    )
    full_ledgers = tuple(
        sorted(path for name, path in evolution.items() if name != "kronos")
    )
    open_full_targets = (
        "alexandria",
        "anamnesis",
        "berean",
        "brevitas",
        "hermes",
        "ephoros",
        "fiat",
        "hypomnema",
        "imprimatur",
        "metron",
        "vulgate",
        "homologia",
        "horos",
        "janus",
        "lazarus",
        "lemma",
        "pandects",
        "probitas",
        "sapheneia",
        "synkrisis",
        "tabularium",
    )
    phase_scope = ("protasis", "phylax", "ephoros", "metron", "elenchus", "hypomnema")
    open_phase_targets = ("ephoros", "metron", "hypomnema")

    def add_kronos(
        scope: str, targets: tuple[str, ...], ledgers: tuple[str, ...]
    ) -> None:
        common = kronos_own + ledgers
        add("kronos", f"{scope}__rank-only", f"{scope} rank-only pass", documents=common)
        for target in targets:
            add(
                "kronos",
                f"{scope}__dispatch-{target}",
                f"{scope} rank plus one target dispatch",
                documents=common
                + kronos_currency
                + (SELECTABLE_SKILL_PATHS["fiat"], SELECTABLE_SKILL_PATHS[target]),
            )

    add_kronos("full", open_full_targets, full_ledgers)
    add_kronos(
        "phase", open_phase_targets, tuple(evolution[name] for name in phase_scope)
    )

    fiat_protasis = (SELECTABLE_SKILL_PATHS["protasis"],)
    phylax_states = {
        "none": (),
        "phylax": (SELECTABLE_SKILL_PATHS["phylax"],),
        "phylax-proxy": (
            SELECTABLE_SKILL_PATHS["phylax"],
            "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",
        ),
        "ephoros-phylax": (
            SELECTABLE_SKILL_PATHS["ephoros"],
            SELECTABLE_SKILL_PATHS["phylax"],
        ),
        "ephoros-phylax-proxy": (
            SELECTABLE_SKILL_PATHS["ephoros"],
            SELECTABLE_SKILL_PATHS["phylax"],
            "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",
        ),
    }
    metron_states = {
        "none": (),
        "metron": (SELECTABLE_SKILL_PATHS["metron"],),
        "metron-budget": (
            SELECTABLE_SKILL_PATHS["metron"],
            "plugins/hexaemeron/skills/metron/references/budget-check.md",
        ),
    }
    elenchus_states = {
        "none": (),
        "elenchus": (SELECTABLE_SKILL_PATHS["elenchus"],),
        "elenchus-contract": (
            SELECTABLE_SKILL_PATHS["elenchus"],
            SELECTABLE_SKILL_PATHS["fizz-sync"],
            promises,
        ),
    }
    hypomnema_states = {
        "none": (),
        "hypomnema": (SELECTABLE_SKILL_PATHS["hypomnema"],),
    }
    hermes_states = {
        "none": (),
        "hermes": (SELECTABLE_SKILL_PATHS["hermes"],) + hermes_runtime,
    }
    for worker, phylax, metron, elenchus, hypomnema, hermes in itertools.product(
        ("inline", "mason"),
        phylax_states,
        metron_states,
        elenchus_states,
        hypomnema_states,
        hermes_states,
    ):
        documents = (
            fiat_protasis
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
            documents=documents,
            workers=workers,
        )

    audit_loop = "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
    sapheneia = SELECTABLE_SKILL_PATHS["sapheneia"]
    for worker, phylax, fix in itertools.product(
        ("inline", "warden"), ("phylax", "phylax-proxy"), ("none", "elenchus")
    ):
        documents = (
            audit_loop,
            sapheneia,
            SELECTABLE_SKILL_PATHS["phylax"],
            SELECTABLE_SKILL_PATHS["ephoros"],
            SELECTABLE_SKILL_PATHS["hypomnema"],
        )
        if phylax == "phylax-proxy":
            documents += (
                "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md",
            )
        if fix == "elenchus":
            documents += (SELECTABLE_SKILL_PATHS["elenchus"],)
        workers = ()
        if worker == "warden":
            workers = ("plugins/hexaemeron/agents/warden.md",)
            documents += workers
        add(
            "fiat",
            f"audit-nonsol__{worker}__{phylax}__fix-{fix}",
            "non-Solidity audit round",
            documents=documents,
            workers=workers,
        )

    xray_reuse = "plugins/hexaemeron/skills/fiat/references/xray-reuse.md"
    sol_aud_full = (
        SELECTABLE_SKILL_PATHS["solidity-auditor"],
        sol_aud_version,
        promises,
    ) + sol_aud_general + sol_aud_shared + sol_aud_agents
    fizz_later = (SELECTABLE_SKILL_PATHS["fizz"], promises)
    fizz_full_existing = (
        SELECTABLE_SKILL_PATHS["fizz"],
        promises,
    ) + fizz_common + fizz_report + fizz_invariant
    fizz_audit_states = {
        "absent": (),
        "later-campaign": fizz_later,
        "full-generation": fizz_full_existing,
    }
    for worker, fizz_state, fix in itertools.product(
        ("inline", "warden"),
        fizz_audit_states,
        ("none", "elenchus", "elenchus-contract"),
    ):
        documents = (
            audit_loop,
            xray_reuse,
            sapheneia,
        ) + xray_full + sol_aud_full + fizz_audit_states[fizz_state]
        if fix == "elenchus":
            documents += (SELECTABLE_SKILL_PATHS["elenchus"],)
        elif fix == "elenchus-contract":
            documents += (
                SELECTABLE_SKILL_PATHS["elenchus"],
                SELECTABLE_SKILL_PATHS["fizz-sync"],
                promises,
            )
        workers = sol_aud_agents
        if fizz_state == "full-generation":
            workers += fizz_report + tuple(
                path for path in fizz_invariant if "/agents/" in path
            )
        if worker == "warden":
            workers += ("plugins/hexaemeron/agents/warden.md",)
            documents += ("plugins/hexaemeron/agents/warden.md",)
        add(
            "fiat",
            f"audit-solidity__{worker}__fizz-{fizz_state}__fix-{fix}",
            "Solidity audit round",
            documents=documents,
            workers=workers,
        )

    prose_base = (
        "plugins/hexaemeron/skills/fiat/references/prose-pass.md",
        SELECTABLE_SKILL_PATHS["hypomnema"],
        SELECTABLE_SKILL_PATHS["imprimatur"],
        *imprimatur_lexicons,
        SELECTABLE_SKILL_PATHS["vulgate"],
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
            documents += (SELECTABLE_SKILL_PATHS["brevitas"],)
        if task_issue:
            documents += (sapheneia,)
        if last_step:
            documents += (
                "plugins/hexaemeron/skills/fiat/references/push-discipline.md",
            )
        add(
            "fiat",
            f"prose__{worker}__brevitas-{int(brevitas)}__issue-{int(task_issue)}__last-{int(last_step)}",
            "prose directive",
            documents=documents,
            workers=workers,
        )

    for worker in ("inline", "surveyor"):
        documents = (
            SELECTABLE_SKILL_PATHS["protasis"],
        ) + protasis_disciplines + (
            SELECTABLE_SKILL_PATHS["imprimatur"],
        ) + imprimatur_lexicons
        workers = ()
        if worker == "surveyor":
            workers = ("plugins/hexaemeron/agents/surveyor.md",)
            documents += workers
        add(
            "fiat",
            f"study__{worker}",
            "study directive",
            documents=documents,
            workers=workers,
        )

    fiat_other = {
        "controller-basic": (),
        "frontier-gate": (evolution["fiat"], versioning),
        "marketplace-day1": (
            "plugins/hexaemeron/skills/fiat/references/wildcat-marketplace.md",
        ),
        "marketplace-post-spec": (
            "plugins/hexaemeron/skills/fiat/references/wildcat-marketplace.md",
            "plugins/hexaemeron/skills/fiat/references/plugin-currency.md",
        ),
        "currency-remediation": (
            "plugins/hexaemeron/skills/fiat/references/plugin-currency.md",
        ),
        "checkpoint-transfer": (
            "plugins/hexaemeron/skills/fiat/references/push-discipline.md",
            "plugins/hexaemeron/skills/fiat/references/controller-checkpoint.md",
        ),
        "observation-receipt": ("docs/fiat-run-observation-binding-v1.md",),
        "runbook": (
            SELECTABLE_SKILL_PATHS["protasis"],
            SELECTABLE_SKILL_PATHS["imprimatur"],
            *imprimatur_lexicons,
        ),
        "close-audit": (audit_loop,),
        "delivery": (
            "plugins/hexaemeron/skills/fiat/references/push-discipline.md",
        ),
        "integrate-task-issue": (
            "plugins/hexaemeron/skills/fiat/references/push-discipline.md",
            sapheneia,
            SELECTABLE_SKILL_PATHS["imprimatur"],
            *imprimatur_lexicons,
            SELECTABLE_SKILL_PATHS["vulgate"],
        ),
    }
    for local_id, documents in fiat_other.items():
        add(
            "fiat",
            local_id,
            "bounded controller operation",
            documents=documents,
        )

    profiles.sort(key=lambda item: item["id"])
    ids = [item["id"] for item in profiles]
    if len(ids) != len(set(ids)):
        raise Refusal("duplicate invocation profile id")
    counts = {
        skill: sum(item["selected_skill"] == skill for item in profiles)
        for skill in sorted(EXPECTED_PROFILE_COUNTS)
    }
    projection_sha256 = _sha256(_canonical_json(profiles))
    return {
        "schema": f"{SCHEMA_PREFIX}-invocation-profiles/v1",
        "source_ref": SOURCE_REF,
        "counts": counts,
        "totals": {
            "normalized_profiles": len(profiles),
            "repository_roots": len(profiles) * 2,
            "agent_skills_roots": len(profiles) * 2,
            "standalone_roots": len(profiles),
            "scenario_roots": len(profiles) * 5,
        },
        "projection_sha256": projection_sha256,
        "profiles": profiles,
    }


def _validation_related_skill_anchor(
    profile: dict[str, Any], obligation: str
) -> tuple[str, str]:
    """Resolve a nested skill without using the generator's relation helper."""
    selected_skill = profile["selected_skill"]
    selected = SELECTABLE_SKILL_PATHS[selected_skill]
    skill_by_path = {path: skill for skill, path in SELECTABLE_SKILL_PATHS.items()}
    target_skill = skill_by_path.get(obligation)
    if target_skill is None:
        raise Refusal("profile validator received an unknown related skill")

    if selected_skill == "kronos":
        dispatch = profile["branch_state"][-1]
        if (
            not dispatch.startswith("dispatch-")
            or target_skill not in {"fiat", dispatch.removeprefix("dispatch-")}
        ):
            raise Refusal("profile validator Kronos relation drift")
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
                SELECTABLE_SKILL_PATHS["elenchus"],
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
            if profile["phase"] in {
                "Solidity audit round",
                "non-Solidity audit round",
            }:
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
        raise Refusal(f"profile validator Fiat relation is unowned: {target_skill}")

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
    raise Refusal(
        f"profile validator relation is unowned: {selected_skill} -> {target_skill}"
    )


def _validation_document_anchor(
    selected_skill: str, obligation: str
) -> tuple[str, str]:
    """Resolve a reference relation from a closed, validator-owned grammar."""
    fiat = SELECTABLE_SKILL_PATHS["fiat"]
    fizz = SELECTABLE_SKILL_PATHS["fizz"]
    solidity = SELECTABLE_SKILL_PATHS["solidity-auditor"]
    xray = SELECTABLE_SKILL_PATHS["x-ray"]
    name = PurePosixPath(obligation).name

    if obligation.startswith("plugins/hexaemeron/skills/fiat/references/"):
        source = fiat
        if name == "xray-reuse.md":
            source = "plugins/hexaemeron/skills/fiat/references/audit-loop.md"
        elif name == "controller-checkpoint.md":
            source = "plugins/hexaemeron/skills/fiat/references/push-discipline.md"
        return source, name
    if obligation == "plugins/hermes/skills/hermes/references/optimisation-catalogue.md":
        return SELECTABLE_SKILL_PATHS["hermes"], "references/optimisation-catalogue.md"
    if obligation == "plugins/hexaemeron/skills/metron/references/budget-check.md":
        return SELECTABLE_SKILL_PATHS["metron"], "references/budget-check.md"
    if obligation == "plugins/hexaemeron/skills/phylax/references/model-proxy-v1.md":
        return SELECTABLE_SKILL_PATHS["phylax"], name
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
        return SELECTABLE_SKILL_PATHS["probitas"], f"references/{name}"
    raise Refusal(f"profile validator document relation is unowned: {obligation}")


def _validation_python_pin_anchor(profile: dict[str, Any]) -> tuple[str, str]:
    """Resolve the pin through a validator-owned exact profile grammar."""
    anchors = {
        "anamnesis:demo-or-rebuild": (
            SELECTABLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "anamnesis:ordinary": (
            SELECTABLE_SKILL_PATHS["anamnesis"],
            "- The interpreter is the exact version in the repository's "
            "`.python-version`.",
        ),
        "berean:ordinary": (
            SELECTABLE_SKILL_PATHS["berean"],
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
            SELECTABLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:diagnose": (
            SELECTABLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
        "synkrisis:verify": (
            SELECTABLE_SKILL_PATHS["synkrisis"],
            "From a checkout, with the exact interpreter in the suite's\n"
            "[`.python-version`](../../../../.python-version):",
        ),
    }
    profile_id = profile.get("id")
    try:
        return anchors[profile_id]
    except (KeyError, TypeError) as exc:
        raise Refusal(
            f"profile validator Python pin relation is unowned: {profile_id}"
        ) from exc


def _validation_profile_anchor(
    profile: dict[str, Any], obligation: str
) -> tuple[str, str, str]:
    """Classify and resolve every evidence obligation without a fallback."""
    selected_skill = profile["selected_skill"]
    selected = SELECTABLE_SKILL_PATHS[selected_skill]
    if obligation == selected:
        return "selected_skill", selected, f"name: {selected_skill}"
    if obligation.endswith("/EVOLUTION.md"):
        selected_evolution = str(PurePosixPath(selected).with_name("EVOLUTION.md"))
        if obligation == selected_evolution:
            return "frontier_ledger", selected, "[EVOLUTION.md](EVOLUTION.md)"
        if selected_skill != "kronos":
            raise Refusal("profile validator frontier relation escapes Kronos")
        return (
            "frontier_ledger",
            selected,
            "Walk the whole scope and find every `EVOLUTION.md` beneath it, descending\n"
            "   into each plugin's own skills directory.",
        )
    if obligation.endswith("/SKILL.md"):
        source, needle = _validation_related_skill_anchor(profile, obligation)
        return "related_skill", source, needle

    if (
        selected_skill == "kronos"
        and obligation
        == "plugins/hexaemeron/skills/fiat/references/plugin-currency.md"
    ):
        return (
            "document_reference",
            selected,
            "`../fiat/references/plugin-currency.md` names the host\n"
            "   mechanism.",
        )

    if obligation in VALIDATION_OPERATION_REFERENCE_PATHS:
        source = selected
        if obligation == "plugins/probitas/docs/adding-a-venue.md":
            source = "plugins/probitas/skills/probitas/references/venues.md"
        needle = posixpath.relpath(obligation, posixpath.dirname(source))
        return "operation_reference", source, needle

    if obligation in VALIDATION_FIAT_WORKER_PROMPTS:
        return (
            "worker_prompt",
            SELECTABLE_SKILL_PATHS["fiat"],
            f"`{PurePosixPath(obligation).stem}`",
        )
    if obligation in VALIDATION_FIZZ_WORKER_PROMPTS:
        return (
            "worker_prompt",
            SELECTABLE_SKILL_PATHS["fizz"],
            posixpath.relpath(
                obligation, posixpath.dirname(SELECTABLE_SKILL_PATHS["fizz"])
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
        source, needle = _validation_python_pin_anchor(profile)
        return "fixed_input", source, needle

    if obligation in VALIDATION_STRUCTURED_REFERENCE_PATHS:
        if obligation == "plugins/hermes/skills/hermes/references/gas-rule-corpus.json":
            return (
                "structured_reference",
                SELECTABLE_SKILL_PATHS["hermes"],
                "Every candidate names a rule from "
                "[references/gas-rule-corpus.json](references/gas-rule-corpus.json)",
            )
        if obligation == "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json":
            return (
                "structured_reference",
                SELECTABLE_SKILL_PATHS["hermes"],
                "A corpus that fails its own schema",
            )
        if obligation.startswith("plugins/hexaemeron/skills/imprimatur/lexicon/"):
            return (
                "structured_reference",
                SELECTABLE_SKILL_PATHS["imprimatur"],
                f"`{PurePosixPath(obligation).name}`",
            )
        if obligation == "plugins/synkrisis/references/rules-v1.json":
            operation = profile["branch_state"][-1]
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
            needle = needles.get(operation)
            if needle is None:
                raise Refusal("profile validator Synkrisis operation drift")
            return "structured_reference", SELECTABLE_SKILL_PATHS["synkrisis"], needle
        raise Refusal(f"profile validator structured relation is unowned: {obligation}")

    if obligation in VALIDATION_FIXED_INPUT_PATHS:
        anchors = {
            "plugins/hexaemeron/skills/x-ray/VERSION": (
                SELECTABLE_SKILL_PATHS["x-ray"],
                "Read the local `VERSION` file from `$SKILL_DIR/VERSION`",
            ),
            "plugins/hexaemeron/skills/solidity-auditor/VERSION": (
                SELECTABLE_SKILL_PATHS["solidity-auditor"],
                "Read the local `VERSION` file from the same directory as this skill",
            ),
        }
        source, needle = anchors[obligation]
        return "fixed_input", source, needle

    source, needle = _validation_document_anchor(selected_skill, obligation)
    return "document_reference", source, needle


def _validation_evidence(path: str, needle: str) -> dict[str, Any]:
    """Build validator-owned evidence without calling the generator helper."""
    data = _source_blob(path)
    encoded = needle.encode("utf-8")
    start = data.find(encoded)
    if start < 0:
        raise Refusal(f"validator semantic evidence is missing in {path}")
    return {
        "path": path,
        "start": start,
        "end": start + len(encoded),
        "source_sha256": _sha256(data),
        "span_sha256": _sha256(encoded),
    }


def _validation_manifest_source_anchor(path: str) -> tuple[str, str, str]:
    """Resolve every manifest source-evidence row through a closed grammar."""
    anchors = {
        ".python-version": (
            "fixed_input",
            "AGENTS.md",
            "Every `python3` command below means the exact interpreter recorded in\n"
            "[`.python-version`](.python-version).",
        ),
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.json": (
            "structured_reference",
            SELECTABLE_SKILL_PATHS["hermes"],
            "Every candidate names a rule from "
            "[references/gas-rule-corpus.json](references/gas-rule-corpus.json)",
        ),
        "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json": (
            "structured_reference",
            SELECTABLE_SKILL_PATHS["hermes"],
            "A corpus that fails its own schema",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json": (
            "structured_reference",
            SELECTABLE_SKILL_PATHS["imprimatur"],
            "`gated.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json": (
            "structured_reference",
            SELECTABLE_SKILL_PATHS["imprimatur"],
            "`hard.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json": (
            "structured_reference",
            SELECTABLE_SKILL_PATHS["imprimatur"],
            "`structural.json`",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/agent-replies.md": (
            "markdown_reference",
            SELECTABLE_SKILL_PATHS["imprimatur"],
            "references/agent-replies.md",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/lexicon-rationale.md": (
            "markdown_reference",
            SELECTABLE_SKILL_PATHS["imprimatur"],
            "references/lexicon-rationale.md",
        ),
        "plugins/hexaemeron/skills/imprimatur/references/rewriting.md": (
            "markdown_reference",
            SELECTABLE_SKILL_PATHS["imprimatur"],
            "references/rewriting.md",
        ),
        "plugins/hexaemeron/skills/solidity-auditor/VERSION": (
            "fixed_input",
            SELECTABLE_SKILL_PATHS["solidity-auditor"],
            "Read the local `VERSION` file from the same directory as this skill",
        ),
        "plugins/hexaemeron/skills/x-ray/VERSION": (
            "fixed_input",
            SELECTABLE_SKILL_PATHS["x-ray"],
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
            SELECTABLE_SKILL_PATHS["pandects"],
            "`docs/applicability.md` states the rules once",
        ),
        "plugins/pandects/docs/writing-a-law.md": (
            "operation_reference",
            SELECTABLE_SKILL_PATHS["pandects"],
            "`docs/writing-a-law.md`",
        ),
        "plugins/pandects/integrations/wildcat/APPLICABILITY.md": (
            "operation_reference",
            SELECTABLE_SKILL_PATHS["pandects"],
            "`integrations/wildcat/APPLICABILITY.md` carries all of them",
        ),
        "plugins/synkrisis/references/rules-v1.json": (
            "structured_reference",
            SELECTABLE_SKILL_PATHS["synkrisis"],
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
    anchor = anchors.get(path)
    if anchor is None:
        raise Refusal(f"manifest semantic source relation is unowned: {path}")
    return anchor


def _validation_runtime_anchor(target: str, context: str) -> tuple[str, str]:
    """Resolve one executable input through a validator-owned runtime grammar."""
    hermes_runtime = "plugins/hermes/skills/hermes/scripts/hermes.py"
    imprimatur_runtime = (
        "plugins/hexaemeron/skills/imprimatur/scripts/imprimatur.py"
    )
    if target == "plugins/hermes/skills/hermes/references/gas-rule-corpus.json":
        return hermes_runtime, "raw = corpus_path.read_bytes()"
    if target == "plugins/hermes/skills/hermes/references/gas-rule-corpus.schema.json":
        return (
            hermes_runtime,
            'schema = json.loads(schema_path.read_text(encoding="utf-8"))',
        )
    if target in {
        "plugins/hexaemeron/skills/imprimatur/lexicon/gated.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/hard.json",
        "plugins/hexaemeron/skills/imprimatur/lexicon/structural.json",
    }:
        return (
            imprimatur_runtime,
            'return rd("hard.json"), rd("gated.json"), rd("structural.json")',
        )
    if target != "plugins/synkrisis/references/rules-v1.json":
        raise Refusal(f"runtime semantic target is unowned: {target}")
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
    needle = needles.get(context)
    if needle is None:
        raise Refusal(f"Synkrisis runtime context is unowned: {context}")
    return "plugins/synkrisis/scripts/synkrisis.py", needle


def _validate_python_pin_profile_scope(profiles: list[dict[str, Any]]) -> None:
    """Refuse every omission from, or addition to, the exact pin allowlist."""
    observed = {
        profile.get("id")
        for profile in profiles
        if isinstance(profile, dict)
        and isinstance(profile.get("required_documents"), list)
        and ".python-version" in profile["required_documents"]
    }
    if observed != VALIDATION_PYTHON_PIN_PROFILE_IDS:
        raise Refusal("invocation profile Python pin scope drift")


def _validate_invocation_profiles(record: dict[str, Any]) -> None:
    """Validate source spans and exact ledger identity without calling its builder."""
    _require_fields(
        record,
        ("schema", "source_ref", "counts", "totals", "projection_sha256", "profiles"),
        ("schema", "source_ref", "counts", "totals", "projection_sha256", "profiles"),
        "invocation profiles",
    )
    if record["schema"] != f"{SCHEMA_PREFIX}-invocation-profiles/v1":
        raise Refusal("invocation profile schema drift")
    if record["source_ref"] != SOURCE_REF:
        raise Refusal("invocation profile source ref drift")
    profiles = record["profiles"]
    if not isinstance(profiles, list) or len(profiles) != 519:
        raise Refusal("invocation profile denominator drift")
    if record["counts"] != EXPECTED_PROFILE_COUNTS:
        raise Refusal("invocation profile per-skill count drift")
    expected_totals = {
        "normalized_profiles": 519,
        "repository_roots": 1_038,
        "agent_skills_roots": 1_038,
        "standalone_roots": 519,
        "scenario_roots": 2_595,
    }
    if record["totals"] != expected_totals:
        raise Refusal("invocation profile route total drift")
    if record["projection_sha256"] != _sha256(_canonical_json(profiles)):
        raise Refusal("invocation profile projection digest mismatch")
    if record["projection_sha256"] != EXPECTED_PROFILE_PROJECTION_SHA256:
        raise Refusal("invocation profile source oracle mismatch")
    ids: list[str] = []
    observed_counts = {skill: 0 for skill in EXPECTED_PROFILE_COUNTS}
    evidence_counts = {name: 0 for name in EXPECTED_PROFILE_EVIDENCE_COUNTS}
    fiat_phases: dict[str, int] = {}
    for index, profile in enumerate(profiles):
        _require_fields(
            profile,
            (
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
            ),
            (
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
            ),
            f"invocation profile {index}",
        )
        skill = profile["selected_skill"]
        if skill not in SELECTABLE_SKILL_PATHS or not profile["id"].startswith(f"{skill}:"):
            raise Refusal("invocation profile selected skill drift")
        ids.append(profile["id"])
        observed_counts[skill] += 1
        if skill == "fiat":
            phase = profile["phase"]
            fiat_phases[phase] = fiat_phases.get(phase, 0) + 1
        documents = profile["required_documents"]
        workers = profile["worker_prompts"]
        if (
            not isinstance(documents, list)
            or documents != sorted(set(documents))
            or SELECTABLE_SKILL_PATHS[skill] not in documents
            or not isinstance(workers, list)
            or workers != sorted(set(workers))
            or not set(workers) <= set(documents)
        ):
            raise Refusal("invocation profile document or worker union drift")
        for path in documents:
            _safe_relative(path)
            if path not in _frozen_tree_paths():
                raise Refusal(f"invocation profile document leaves source: {path}")
            if path in REFERENCE_ONLY_MARKDOWN:
                raise Refusal(f"invocation profile reaches human reference: {path}")
        expected_fixed = _profile_fixed_inputs(tuple(documents))
        if profile["fixed_inputs"] != expected_fixed:
            raise Refusal("invocation profile fixed input semantics drift")
        if not isinstance(profile["source_evidence"], list):
            raise Refusal("invocation profile lacks source evidence")
        evidence_obligations = [
            evidence.get("obligation")
            if isinstance(evidence, dict)
            else None
            for evidence in profile["source_evidence"]
        ]
        if (
            evidence_obligations != documents
            or len(evidence_obligations) != len(set(evidence_obligations))
        ):
            raise Refusal("invocation profile evidence obligation coverage drift")
        for evidence in profile["source_evidence"]:
            _require_fields(
                evidence,
                (
                    "obligation",
                    "path",
                    "start",
                    "end",
                    "source_sha256",
                    "span_sha256",
                ),
                (
                    "obligation",
                    "path",
                    "start",
                    "end",
                    "source_sha256",
                    "span_sha256",
                ),
                "invocation profile evidence",
            )
            _safe_relative(evidence["obligation"])
            _safe_relative(evidence["path"])
            data = _source_blob(evidence["path"])
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
                or _sha256(data) != evidence["source_sha256"]
                or _sha256(data[start:end]) != evidence["span_sha256"]
            ):
                raise Refusal("invocation profile source span drift")
            evidence_class, expected_path, expected_needle = _validation_profile_anchor(
                profile, evidence["obligation"]
            )
            if evidence_class not in evidence_counts:
                raise Refusal(
                    f"invocation profile evidence class is unowned: {evidence_class}"
                )
            encoded = expected_needle.encode("utf-8")
            expected_start = data.find(encoded) if evidence["path"] == expected_path else -1
            expected = {
                "obligation": evidence["obligation"],
                "path": expected_path,
                "start": expected_start,
                "end": expected_start + len(encoded),
                "source_sha256": _sha256(data),
                "span_sha256": _sha256(encoded),
            }
            if expected_start < 0 or evidence != expected:
                raise Refusal(
                    "invocation profile semantic anchor drift: "
                    f"{profile['id']}: {evidence['obligation']}"
                )
            evidence_counts[evidence_class] += 1
    if ids != sorted(set(ids)) or observed_counts != EXPECTED_PROFILE_COUNTS:
        raise Refusal("invocation profile id product drift")
    _validate_python_pin_profile_scope(profiles)
    if fiat_phases != {
        "implement directive": 360,
        "Solidity audit round": 18,
        "non-Solidity audit round": 8,
        "prose directive": 16,
        "study directive": 2,
        "bounded controller operation": 11,
    }:
        raise Refusal("Fiat invocation profile branch product drift")
    if evidence_counts != EXPECTED_PROFILE_EVIDENCE_COUNTS or sum(
        evidence_counts.values()
    ) != sum(len(profile["required_documents"]) for profile in profiles):
        raise Refusal("invocation profile semantic evidence coverage drift")


def _reference_link(
    owner: str, target: str, reachable: set[str]
) -> tuple[str, str] | None:
    target_path = PurePosixPath(target)
    if target_path.name in {"SKILL.md", "EVOLUTION.md"}:
        raise Refusal("generic path basename cannot prove a profile obligation")
    candidates: list[tuple[int, str, str]] = []
    for source in sorted(reachable):
        source_path = PurePosixPath(source)
        relative = os.path.relpath(
            target_path.as_posix(), source_path.parent.as_posix()
        )
        owner_relative = os.path.relpath(
            target_path.as_posix(), PurePosixPath(owner).parent.as_posix()
        )
        needles = sorted(
            {relative, owner_relative, target_path.name},
            key=lambda value: (-len(value), value),
        )
        text = _source_blob(source).decode("utf-8", errors="strict")
        for needle in needles:
            position = text.find(needle)
            if position >= 0:
                candidates.append((position, source, needle))
    if not candidates:
        return None
    _, source, needle = min(candidates, key=lambda value: (value[1] != owner, value))
    return source, needle


def _reachability_by_root(
    roots: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    scope_field: str,
) -> dict[str, set[str]]:
    paths = {
        path
        for root in roots
        for path in (root["node"],)
    } | {
        path
        for edge in edges
        for path in (edge["source"], edge["target"])
    }
    observed: dict[str, set[str]] = {path: set() for path in paths}
    roots_by_id = {root["id"]: root for root in roots}
    adjacency_by_root: dict[str, dict[str, set[str]]] = {
        identifier: {} for identifier in roots_by_id
    }
    for edge in edges:
        scope = edge[scope_field]
        identifiers = roots_by_id if "*" in scope else scope
        for identifier in identifiers:
            adjacency_by_root[identifier].setdefault(edge["source"], set()).add(
                edge["target"]
            )
    for root in roots:
        adjacency = adjacency_by_root[root["id"]]
        pending = [root["node"]]
        reached: set[str] = set()
        while pending:
            node = pending.pop()
            if node in reached:
                continue
            reached.add(node)
            pending.extend(sorted(adjacency.get(node, set()), reverse=True))
        for path in reached:
            observed[path].add(root["id"])
    return observed


def _scenario_base(route: str, selected_skill: str) -> str:
    path = SELECTABLE_SKILL_PATHS[selected_skill]
    plugin = _plugin(path)
    if plugin is None:
        raise Refusal(f"profile skill has no plugin: {path}")
    if route == "standalone":
        return f"standalone:{plugin}:skill:{selected_skill}"
    if route in {"repository", "agent-skills"}:
        return f"{route}:skill:{selected_skill}"
    raise Refusal(f"unknown scenario route: {route}")


def _scenario_host_root(route: str, selected_skill: str) -> str:
    if route == "repository":
        return "repository"
    if route == "agent-skills":
        return "agent-skills"
    plugin = _plugin(SELECTABLE_SKILL_PATHS[selected_skill])
    if route != "standalone" or plugin is None:
        raise Refusal(f"unknown scenario host route: {route}")
    return f"standalone:{plugin}"


def _scenario_expected_documents(
    route: str,
    credential: str,
    profile: dict[str, Any],
) -> set[str]:
    """Derive a route's exact document union independently of graph edges."""
    skill = profile["selected_skill"]
    selected = SELECTABLE_SKILL_PATHS[skill]
    plugin = _plugin(selected)
    if plugin is None:
        raise Refusal(f"profile skill has no plugin: {selected}")
    runtime = f"plugins/{plugin}/AGENTS.md"
    promise = f"plugins/{plugin}/PROMISE_MACHINE.md"
    router = ".agents/skills/promise-machine/SKILL.md"
    portable = ".agents/skills/promise-machine/PORTABLE.md"
    expected = set(profile["required_documents"])
    expected.update({runtime, promise, selected})
    if route == "repository":
        expected.update({"AGENTS.md", "SHOGGOTH.md", "PROMISE_MACHINE.md", router})
    elif route == "agent-skills":
        expected.update(
            {
                router,
                portable,
                "AGENTS.md",
                "SHOGGOTH.md",
                "PROMISE_MACHINE.md",
            }
        )
    elif route != "standalone":
        raise Refusal(f"unknown scenario route: {route}")
    if credential == "github-contributor":
        if route == "standalone":
            raise Refusal("standalone profiles cannot resolve suite credentials")
        expected.add("CONTRIBUTORS.md")
    elif credential != "absent":
        raise Refusal(f"unknown scenario credential: {credential}")
    return expected


def _validate_source_evidence(evidence: dict[str, Any], label: str) -> None:
    _require_fields(
        evidence,
        ("path", "start", "end", "source_sha256", "span_sha256"),
        ("path", "start", "end", "source_sha256", "span_sha256"),
        label,
    )
    data = _source_blob(evidence["path"])
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
        or _sha256(data) != evidence["source_sha256"]
        or _sha256(data[start:end]) != evidence["span_sha256"]
    ):
        raise Refusal(f"{label} does not bind frozen source bytes")


def _bundle_evidence(profile: dict[str, Any], target: str) -> dict[str, Any]:
    matches = [
        evidence
        for evidence in profile["source_evidence"]
        if evidence["obligation"] == target
    ]
    if len(matches) != 1:
        raise Refusal(
            f"profile target has no unique source witness: {profile['id']}: {target}"
        )
    return {
        key: value for key, value in matches[0].items() if key != "obligation"
    }


def _bundle_relation(
    profile: dict[str, Any], target: str
) -> tuple[str, str, dict[str, Any] | None]:
    document_class = _document_class(target)
    if target in _fixed_agent_metadata():
        return "fixed-agent-input", "agent-or-prompt", None
    structured = _structured_metadata().get(target)
    if structured is not None:
        if structured["load_semantics"] == "reference-only":
            raise Refusal(f"profile reaches reference-only input: {target}")
        runtime_needle = structured["runtime_needle"]
        if target == "plugins/synkrisis/references/rules-v1.json":
            operation = f"operation:synkrisis:{profile['branch_state'][-1]}"
            runtime_needle = SYNKRISIS_RULE_RUNTIME_NEEDLES.get(operation)
        if structured["runtime_path"] is None or runtime_needle is None:
            raise Refusal(f"mandatory input lacks runtime witness: {target}")
        return (
            "mandatory-executable",
            "mandatory-executable",
            _evidence(structured["runtime_path"], runtime_needle),
        )
    if document_class == "worker_prompt":
        return "worker-dispatch", "agent-or-prompt", None
    if document_class in {"frontier_ledger", "frontier_policy"}:
        return "frontier-gate", "agent-or-prompt", None
    if document_class == "skill_contract":
        return "operation-branch", "agent-or-prompt", None
    return "conditional", "agent-or-prompt", None


def _validate_complete_scenarios(
    topology: dict[str, Any], profiles: dict[str, Any]
) -> None:
    """Check the exact profile x route x credential product by reachability."""
    _validate_invocation_profiles(profiles)
    profile_rows = {item["id"]: item for item in profiles["profiles"]}
    root_rows = topology["scenario_roots"]
    roots = {item["id"]: item for item in root_rows}
    if len(roots) != len(root_rows) or len(roots) != 2_595:
        raise Refusal("scenario root denominator or identity drift")
    expected_ids: set[str] = set()
    for profile in profiles["profiles"]:
        for route, credentials in (
            ("repository", ("absent", "github-contributor")),
            ("agent-skills", ("absent", "github-contributor")),
            ("standalone", ("absent",)),
        ):
            base = _scenario_base(route, profile["selected_skill"])
            for credential in credentials:
                expected_ids.add(
                    f"{base}:profile:{profile['id']}:credential:{credential}"
                )
    if set(roots) != expected_ids:
        raise Refusal("scenario roots do not equal the 5N profile product")
    route_counts = {route: 0 for route in ("repository", "agent-skills", "standalone")}
    profile_counts = {identifier: 0 for identifier in profile_rows}
    expected_bases: set[str] = set()
    for identifier, root in roots.items():
        _require_fields(
            root,
            (
                "id",
                "node",
                "mode",
                "base_scenario",
                "route",
                "selected_skill",
                "profile_id",
                "credential",
                "conditions",
                "evidence",
            ),
            (
                "id",
                "node",
                "mode",
                "base_scenario",
                "route",
                "selected_skill",
                "profile_id",
                "credential",
                "conditions",
                "evidence",
            ),
            f"scenario root {identifier}",
        )
        profile = profile_rows.get(root["profile_id"])
        if profile is None or root["selected_skill"] != profile["selected_skill"]:
            raise Refusal(f"scenario root has an unknown profile: {identifier}")
        route = root["route"]
        credential = root["credential"]
        base = _scenario_base(route, root["selected_skill"])
        selected = SELECTABLE_SKILL_PATHS[root["selected_skill"]]
        plugin = _plugin(selected)
        assert plugin is not None
        expected_node = {
            "repository": "AGENTS.md",
            "agent-skills": ".agents/skills/promise-machine/SKILL.md",
            "standalone": f"plugins/{plugin}/AGENTS.md",
        }.get(route)
        expected_conditions = [f"profile:{profile['id']}"]
        if credential == "github-contributor":
            expected_conditions.append("credential:github-contributor")
        expected_conditions.sort()
        if (
            root["base_scenario"] != base
            or root["node"] != expected_node
            or root["mode"] != "conditional"
            or root["conditions"] != expected_conditions
            or identifier
            != f"{base}:profile:{profile['id']}:credential:{credential}"
        ):
            raise Refusal(f"scenario root binding drift: {identifier}")
        _scenario_expected_documents(route, credential, profile)
        _validate_source_evidence(root["evidence"], "scenario root evidence")
        route_counts[route] += 1
        profile_counts[profile["id"]] += 1
        expected_bases.add(base)
    if route_counts != {
        "repository": 1_038,
        "agent-skills": 1_038,
        "standalone": 519,
    } or set(profile_counts.values()) != {5}:
        raise Refusal("scenario route totals drift")
    if len(expected_bases) != 93:
        raise Refusal("scenario base product drift")

    scenario_ids = set(roots)
    runtime_counts = {
        target: 0 for target in EXPECTED_GRAPH_RUNTIME_EVIDENCE_COUNTS
    }
    scenario_runtime_rows = 0
    for edge in topology["scenario_edges"]:
        _require_fields(
            edge,
            (
                "id",
                "source",
                "target",
                "kind",
                "load_type",
                "reason",
                "condition",
                "eligible_base_scenarios",
                "active_scenarios",
                "evidence",
                "runtime_evidence",
            ),
            (
                "id",
                "source",
                "target",
                "kind",
                "load_type",
                "reason",
                "condition",
                "eligible_base_scenarios",
                "active_scenarios",
                "evidence",
                "runtime_evidence",
            ),
            f"scenario edge {edge.get('id', '?')}",
        )
        scope = edge["active_scenarios"]
        if scope != sorted(set(scope)) or not scope or "*" in scope or not set(scope) <= scenario_ids:
            raise Refusal(f"scenario edge scope is open: {edge['id']}")
        bases = sorted({roots[item]["base_scenario"] for item in scope})
        if edge["eligible_base_scenarios"] != bases:
            raise Refusal(f"scenario edge base scope drift: {edge['id']}")
        if edge["condition"] is not None:
            raise Refusal(f"scenario edge bypasses profile-ledger scoping: {edge['id']}")
        if edge["load_type"] == "mandatory-executable":
            if edge["runtime_evidence"] is None:
                raise Refusal(f"mandatory edge lacks runtime evidence: {edge['id']}")
        elif edge["runtime_evidence"] is not None:
            raise Refusal(f"agent input claims executable runtime evidence: {edge['id']}")
        _validate_source_evidence(edge["evidence"], "scenario edge evidence")
        if edge["runtime_evidence"] is not None:
            _validate_source_evidence(
                edge["runtime_evidence"], "scenario runtime evidence"
            )
            context = "scenario"
            if edge["target"] == "plugins/synkrisis/references/rules-v1.json":
                operations = {
                    profile_rows[roots[identifier]["profile_id"]]["branch_state"][-1]
                    for identifier in scope
                }
                if len(operations) != 1 or not operations <= {"diagnose", "verify"}:
                    raise Refusal(
                        f"Synkrisis runtime scope mixes operations: {edge['id']}"
                    )
                context = next(iter(operations))
            runtime_path, runtime_needle = _validation_runtime_anchor(
                edge["target"], context
            )
            if edge["runtime_evidence"] != _validation_evidence(
                runtime_path, runtime_needle
            ):
                raise Refusal(
                    f"scenario runtime semantic anchor drift: {edge['id']}"
                )
            runtime_counts[edge["target"]] += 1
            scenario_runtime_rows += 1

    host_runtime_rows = 0
    for edge in topology["edges"]:
        runtime_evidence = edge["runtime_evidence"]
        if edge["load_type"] == "mandatory-executable":
            if runtime_evidence is None:
                raise Refusal(f"mandatory host edge lacks runtime evidence: {edge['id']}")
        elif runtime_evidence is not None:
            raise Refusal(f"host agent input claims runtime evidence: {edge['id']}")
        if runtime_evidence is None:
            continue
        _validate_source_evidence(runtime_evidence, "host runtime evidence")
        matching = [
            candidate["runtime_evidence"]
            for candidate in topology["scenario_edges"]
            if (
                candidate["source"],
                candidate["target"],
                candidate["kind"],
                candidate["load_type"],
            )
            == (
                edge["source"],
                edge["target"],
                edge["kind"],
                edge["load_type"],
            )
        ]
        if runtime_evidence not in matching:
            raise Refusal(f"host runtime semantic anchor drift: {edge['id']}")
        runtime_counts[edge["target"]] += 1
        host_runtime_rows += 1
    if (
        scenario_runtime_rows != 12
        or host_runtime_rows != 11
        or runtime_counts != EXPECTED_GRAPH_RUNTIME_EVIDENCE_COUNTS
    ):
        raise Refusal("graph semantic runtime evidence coverage drift")

    observed = _reachability_by_root(
        root_rows, topology["scenario_edges"], "active_scenarios"
    )
    reached = {
        identifier: {path for path, scope in observed.items() if identifier in scope}
        for identifier in roots
    }
    for identifier, root in roots.items():
        profile = profile_rows[root["profile_id"]]
        expected = _scenario_expected_documents(
            root["route"], root["credential"], profile
        )
        if reached[identifier] != expected:
            missing = sorted(expected - reached[identifier])
            leaked = sorted(reached[identifier] - expected)
            detail = f"missing {missing[0]}" if missing else f"leaked {leaked[0]}"
            raise Refusal(f"scenario document union drift: {identifier}: {detail}")
    for edge in topology["scenario_edges"]:
        for identifier in edge["active_scenarios"]:
            if edge["source"] not in reached[identifier] or edge["target"] not in reached[identifier]:
                raise Refusal(f"scenario edge lacks a realizable witness: {edge['id']}")

    reference_only = {item["path"] for item in topology["reference_only"]}
    expected_reference_only = {
        path
        for path, metadata in _structured_metadata().items()
        if metadata["load_semantics"] == "reference-only"
    } | set(REFERENCE_ONLY_MARKDOWN)
    if reference_only != expected_reference_only or len(reference_only) != 12:
        raise Refusal("reference-only ledger drift")
    if any(reference_only & paths for paths in reached.values()):
        raise Refusal("reference-only evidence became scenario-reachable")

    for path in _fixed_agent_metadata():
        expected_scope = {
            identifier
            for identifier, root in roots.items()
            if path in profile_rows[root["profile_id"]]["required_documents"]
        }
        if path == ".python-version" and len(expected_scope) != 55:
            raise Refusal("suite Python pin route scope drift")
        actual_scope = observed.get(path, set())
        incoming = [
            edge for edge in topology["scenario_edges"] if edge["target"] == path
        ]
        if actual_scope != expected_scope or not incoming or any(
            edge["kind"] != "fixed-agent-input"
            or edge["load_type"] != "agent-or-prompt"
            or edge["runtime_evidence"] is not None
            for edge in incoming
        ):
            raise Refusal(f"fixed agent input semantics drift: {path}")
    for path, metadata in _structured_metadata().items():
        if metadata["load_semantics"] == "reference-only":
            continue
        expected_scope = {
            identifier
            for identifier, root in roots.items()
            if path in profile_rows[root["profile_id"]]["required_documents"]
        }
        incoming = [
            edge for edge in topology["scenario_edges"] if edge["target"] == path
        ]
        if observed.get(path, set()) != expected_scope or not incoming or any(
            edge["kind"] != "mandatory-executable"
            or edge["load_type"] != "mandatory-executable"
            or edge["runtime_evidence"] is None
            for edge in incoming
        ):
            raise Refusal(f"structured input semantics drift: {path}")


def _build_topology(
    documents: list[dict[str, Any]], profiles: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Build exact profile-scoped routes; no edge-minimised witness fiction."""
    if profiles is None:
        profiles = build_invocation_profiles()
    _validate_invocation_profiles(profiles)
    document_paths = {item["path"] for item in documents}
    if set(SELECTABLE_SKILL_PATHS.values()) - document_paths:
        raise Refusal("profile skills leave the manifest")
    plugins = sorted(
        {
            _plugin(path)
            for path in SELECTABLE_SKILL_PATHS.values()
            if _plugin(path) is not None
        }
    )
    roots = [
        {
            "id": "repository",
            "node": "AGENTS.md",
            "mode": "unconditional",
            "evidence": _evidence("AGENTS.md", "The safe loading path is short:"),
        },
        {
            "id": "agent-skills",
            "node": ".agents/skills/promise-machine/SKILL.md",
            "mode": "unconditional",
            "evidence": _evidence(
                ".agents/skills/promise-machine/SKILL.md",
                "Choose the runtime before routing.",
            ),
        },
    ]
    for plugin in plugins:
        runtime = f"plugins/{plugin}/AGENTS.md"
        roots.append(
            {
                "id": f"standalone:{plugin}",
                "node": runtime,
                "mode": "unconditional",
                "evidence": _evidence(runtime, "## Promise Machine binding"),
            }
        )
    roots.sort(key=lambda item: item["id"])

    scenario_roots: list[dict[str, Any]] = []
    route_evidence = {
        "repository": _evidence("AGENTS.md", "The safe loading path is short:"),
        "agent-skills": _evidence(
            ".agents/skills/promise-machine/SKILL.md",
            "Choose the runtime before routing.",
        ),
    }
    for profile in profiles["profiles"]:
        skill = profile["selected_skill"]
        selected = SELECTABLE_SKILL_PATHS[skill]
        plugin = _plugin(selected)
        if plugin is None:
            raise Refusal(f"profile skill has no plugin: {selected}")
        runtime = f"plugins/{plugin}/AGENTS.md"
        standalone_evidence = _evidence(runtime, "## Promise Machine binding")
        for route, credentials in (
            ("repository", ("absent", "github-contributor")),
            ("agent-skills", ("absent", "github-contributor")),
            ("standalone", ("absent",)),
        ):
            base = _scenario_base(route, skill)
            node = {
                "repository": "AGENTS.md",
                "agent-skills": ".agents/skills/promise-machine/SKILL.md",
                "standalone": runtime,
            }[route]
            for credential in credentials:
                conditions = [f"profile:{profile['id']}"]
                if credential == "github-contributor":
                    conditions.append("credential:github-contributor")
                conditions.sort()
                scenario_roots.append(
                    {
                        "id": f"{base}:profile:{profile['id']}:credential:{credential}",
                        "node": node,
                        "mode": "conditional",
                        "base_scenario": base,
                        "route": route,
                        "selected_skill": skill,
                        "profile_id": profile["id"],
                        "credential": credential,
                        "conditions": conditions,
                        "evidence": (
                            standalone_evidence
                            if route == "standalone"
                            else route_evidence[route]
                        ),
                    }
                )
    scenario_roots.sort(key=lambda item: item["id"])
    roots_by_id = {item["id"]: item for item in scenario_roots}
    profiles_by_id = {item["id"]: item for item in profiles["profiles"]}
    bundle_relations: dict[
        tuple[str, str], tuple[str, str, dict[str, Any] | None, dict[str, Any]]
    ] = {}
    for profile in profiles["profiles"]:
        selected = SELECTABLE_SKILL_PATHS[profile["selected_skill"]]
        for target in profile["required_documents"]:
            if target == selected:
                continue
            kind, load_type, runtime_evidence = _bundle_relation(profile, target)
            bundle_relations[(profile["id"], target)] = (
                kind,
                load_type,
                runtime_evidence,
                _bundle_evidence(profile, target),
            )

    relations: dict[
        tuple[str, str, str, str, bytes, bytes], dict[str, Any]
    ] = {}

    def add_relation(
        root_id: str,
        source: str,
        target: str,
        kind: str,
        reason: str,
        evidence: dict[str, Any],
        *,
        load_type: str = "agent-or-prompt",
        runtime_evidence: dict[str, Any] | None = None,
    ) -> None:
        if source not in document_paths or target not in document_paths:
            raise Refusal(f"scenario relation leaves manifest: {source} -> {target}")
        evidence_key = _canonical_json(evidence)
        runtime_key = b"" if runtime_evidence is None else _canonical_json(runtime_evidence)
        key = (source, target, kind, load_type, evidence_key, runtime_key)
        row = relations.setdefault(
            key,
            {
                "source": source,
                "target": target,
                "kind": kind,
                "load_type": load_type,
                "reason": reason,
                "condition": None,
                "evidence": evidence,
                "runtime_evidence": runtime_evidence,
                "active_scenarios": set(),
            },
        )
        row["active_scenarios"].add(root_id)

    router = ".agents/skills/promise-machine/SKILL.md"
    portable = ".agents/skills/promise-machine/PORTABLE.md"
    for root in scenario_roots:
        profile = profiles_by_id[root["profile_id"]]
        selected = SELECTABLE_SKILL_PATHS[root["selected_skill"]]
        plugin = _plugin(selected)
        assert plugin is not None
        runtime = f"plugins/{plugin}/AGENTS.md"
        promise = f"plugins/{plugin}/PROMISE_MACHINE.md"
        identifier = root["id"]
        if root["route"] == "repository":
            for source, target, kind, needle in (
                ("AGENTS.md", "SHOGGOTH.md", "unconditional", "[Shoggoth collective identity](SHOGGOTH.md)"),
                ("AGENTS.md", "PROMISE_MACHINE.md", "unconditional", "[Promise Machine contract](PROMISE_MACHINE.md)"),
                ("AGENTS.md", router, "unconditional", "`.agents/skills/promise-machine/SKILL.md`"),
            ):
                add_relation(
                    identifier,
                    source,
                    target,
                    kind,
                    "the repository route follows its unconditional host contract",
                    _evidence(source, needle),
                )
        elif root["route"] == "agent-skills":
            add_relation(
                identifier,
                router,
                portable,
                "installed-route",
                "the isolated route loads its dependency-closed runtime contract",
                _evidence(router, "read `PORTABLE.md`"),
            )
            for target, needle in (
                ("SHOGGOTH.md", "runtime/SHOGGOTH.md"),
                ("PROMISE_MACHINE.md", "runtime/PROMISE_MACHINE.md"),
                ("AGENTS.md", "runtime/AGENTS.md"),
            ):
                add_relation(
                    identifier,
                    portable,
                    target,
                    "installed-route",
                    "the portable runtime maps to its pinned canonical source",
                    _evidence(portable, needle),
                )
        if root["credential"] == "github-contributor":
            add_relation(
                identifier,
                "SHOGGOTH.md",
                "CONTRIBUTORS.md",
                "credential-identity",
                "the checkout route resolves the supplied contributor credential",
                _evidence("SHOGGOTH.md", CONTRIBUTORS_CANONICAL_URL),
            )
        if root["route"] != "standalone":
            add_relation(
                identifier,
                router,
                runtime,
                "conditional",
                "the router loads the selected plugin runtime",
                _evidence(router, f"../../../plugins/{plugin}/AGENTS.md"),
            )
        add_relation(
            identifier,
            runtime,
            promise,
            "unconditional",
            "the plugin runtime loads its suite-law copy",
            _evidence(runtime, "[Promise Machine contract](PROMISE_MACHINE.md)"),
        )
        relative = PurePosixPath(selected).relative_to(
            PurePosixPath("plugins") / plugin
        ).as_posix()
        add_relation(
            identifier,
            runtime,
            selected,
            "conditional",
            "the runtime loads exactly the selected canonical skill",
            _evidence(runtime, relative),
        )
        for target in profile["required_documents"]:
            if target == selected:
                continue
            kind, load_type, runtime_evidence, evidence = bundle_relations[
                (profile["id"], target)
            ]
            add_relation(
                identifier,
                selected,
                target,
                kind,
                "the source-owned invocation profile requires this document",
                evidence,
                load_type=load_type,
                runtime_evidence=runtime_evidence,
            )

    scenario_edges: list[dict[str, Any]] = []
    for index, (_, row) in enumerate(sorted(relations.items()), start=1):
        scope = sorted(row.pop("active_scenarios"))
        scenario_edges.append(
            {
                "id": f"scenario-edge-{index:05d}",
                **row,
                "eligible_base_scenarios": sorted(
                    {roots_by_id[item]["base_scenario"] for item in scope}
                ),
                "active_scenarios": scope,
            }
        )

    host_relation_rows: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for edge in scenario_edges:
        key = (edge["source"], edge["target"], edge["kind"], edge["load_type"])
        candidate = host_relation_rows.get(key)
        if candidate is None:
            candidate = {
                "source": edge["source"],
                "target": edge["target"],
                "kind": edge["kind"],
                "load_type": edge["load_type"],
                "reason": edge["reason"],
                "evidence": edge["evidence"],
                "runtime_evidence": edge["runtime_evidence"],
                "active_roots": set(),
            }
            host_relation_rows[key] = candidate
        for identifier in edge["active_scenarios"]:
            root = roots_by_id[identifier]
            candidate["active_roots"].add(
                _scenario_host_root(root["route"], root["selected_skill"])
            )
    edges: list[dict[str, Any]] = []
    for index, (_, row) in enumerate(sorted(host_relation_rows.items()), start=1):
        edges.append(
            {
                "id": f"edge-{index:04d}",
                **{key: value for key, value in row.items() if key != "active_roots"},
                "active_roots": sorted(row["active_roots"]),
            }
        )

    reference_only: list[dict[str, Any]] = []
    for path, metadata in sorted(_structured_metadata().items()):
        if metadata["load_semantics"] != "reference-only":
            continue
        reference_only.append(
            {
                "path": path,
                "canonical_owner": metadata["canonical_owner"],
                "reason": "the schema is authority but no production invocation reads it",
                "source_evidence": _evidence(
                    metadata["source_path"], metadata["source_needle"]
                ),
            }
        )
    for path, (source, needle, reason) in sorted(REFERENCE_ONLY_MARKDOWN.items()):
        reference_only.append(
            {
                "path": path,
                "canonical_owner": _canonical_owner(path, "markdown_reference"),
                "reason": reason,
                "source_evidence": _evidence(source, needle),
            }
        )
    reference_only.sort(key=lambda item: item["path"])
    topology = {
        "roots": roots,
        "edges": edges,
        "scenario_roots": scenario_roots,
        "scenario_edges": scenario_edges,
        "reference_only": reference_only,
    }
    _validate_complete_scenarios(topology, profiles)
    return topology


def build_loader_graph(
    manifest: dict[str, Any], profiles: dict[str, Any] | None = None
) -> dict[str, Any]:
    if profiles is None:
        profiles = build_invocation_profiles()
    _validate_invocation_profiles(profiles)
    manifest_digest = _artifact_digest(manifest)
    documents = manifest["documents"]
    topology = _build_topology(documents, profiles)
    observed_roots = _reachability_by_root(
        topology["roots"], topology["edges"], "active_roots"
    )
    observed_scenarios = _reachability_by_root(
        topology["scenario_roots"],
        topology["scenario_edges"],
        "active_scenarios",
    )
    for document in documents:
        if set(document["loader_roots"]) != observed_roots.get(
            document["path"], set()
        ):
            raise Refusal(f"loader roots disagree with graph: {document['path']}")
        if set(document["scenario_reachability"]) != observed_scenarios.get(
            document["path"], set()
        ):
            raise Refusal(
                f"scenario reachability disagrees with graph: {document['path']}"
            )
    by_path = {item["path"]: item for item in documents}
    reference_only_paths = {item["path"] for item in topology["reference_only"]}
    if reference_only_paths != ({
        path
        for path, metadata in _structured_metadata().items()
        if metadata["load_semantics"] == "reference-only"
    } | set(REFERENCE_ONLY_MARKDOWN)):
        raise Refusal("reference-only graph ledger is incomplete")
    for path in REFERENCE_ONLY_MARKDOWN:
        document = by_path[path]
        if (
            document["load_semantics"] != "reference-only"
            or document["loader_roots"]
            or document["scenario_reachability"]
            or any(edge["target"] == path for edge in topology["edges"])
            or any(edge["target"] == path for edge in topology["scenario_edges"])
        ):
            raise Refusal(f"human reference became production-reachable: {path}")
    for path, metadata in _structured_metadata().items():
        document = by_path[path]
        host_edges = [edge for edge in topology["edges"] if edge["target"] == path]
        scenario_edges = [
            edge for edge in topology["scenario_edges"] if edge["target"] == path
        ]
        if metadata["load_semantics"] == "reference-only":
            if host_edges or scenario_edges or document["loader_roots"] or document[
                "scenario_reachability"
            ]:
                raise Refusal(f"reference-only graph reachability is nonzero: {path}")
            continue
        if not host_edges or not scenario_edges:
            raise Refusal(f"mandatory executable graph is incomplete: {path}")
        if any(
            edge["kind"] != "mandatory-executable"
            or edge["load_type"] != "mandatory-executable"
            or edge["runtime_evidence"] is None
            for edge in [*host_edges, *scenario_edges]
        ):
            raise Refusal(f"mandatory executable semantics drift: {path}")
        expected_runtime = {document["runtime_evidence"]["span_sha256"]}
        if path == "plugins/synkrisis/references/rules-v1.json":
            expected_runtime = {
                _evidence(metadata["runtime_path"], needle)["span_sha256"]
                for needle in SYNKRISIS_RULE_RUNTIME_NEEDLES.values()
            }
        observed_runtime = {
            edge["runtime_evidence"]["span_sha256"] for edge in scenario_edges
        }
        if observed_runtime != expected_runtime:
            raise Refusal(f"mandatory runtime operation proof drift: {path}")
    for path in _fixed_agent_metadata():
        document = by_path[path]
        incoming = [
            edge
            for edge in [*topology["edges"], *topology["scenario_edges"]]
            if edge["target"] == path
        ]
        if (
            not incoming
            or document["load_semantics"] != "agent-or-prompt"
            or any(
                edge["kind"] != "fixed-agent-input"
                or edge["load_type"] != "agent-or-prompt"
                or edge["runtime_evidence"] is not None
                for edge in incoming
            )
        ):
            raise Refusal(f"fixed agent input graph drift: {path}")
    exclusions = [
        {
            "class": class_name,
            "path": path,
            "reason": "the source classifies this link as non-operative for agent loading",
            "evidence": _evidence(source, needle),
        }
        for class_name, path, source, needle in EXCLUDED_LINK_CLASSES
    ]
    return {
        "schema": f"{SCHEMA_PREFIX}-loader-graph/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": manifest_digest,
        "invocation_profiles_sha256": _artifact_digest(profiles),
        "roots": topology["roots"],
        "edges": topology["edges"],
        "scenario_roots": topology["scenario_roots"],
        "scenario_edges": topology["scenario_edges"],
        "reference_only": topology["reference_only"],
        "excluded_links": exclusions,
        "constraints": {
            "complete_scenario_routes": True,
            "condition_vectors_closed": True,
            "file_presence_creates_edge": False,
            "fixtures_excluded": True,
            "skills_runtime_excluded": True,
            "conditional_references_require_source_span": True,
            "same_repository_urls_require_exact_match": True,
            "recursive_required_loads_closed": True,
            "manifest_reachability_is_graph_derived": True,
            "potential_edges_have_scenario_witnesses": True,
            "sibling_branches_are_exclusive": True,
            "wildcard_scenario_conditions_forbidden": True,
            "mandatory_executable_edges_have_runtime_evidence": True,
            "reference_only_records_have_zero_reachability": True,
            "synkrisis_rule_operations_are_exclusive": True,
            "invocation_profiles_are_source_owned": True,
            "profile_route_product_is_exact": True,
            "fixed_agent_inputs_are_not_executed": True,
        },
    }


def _validate_loader_graph(
    graph: dict[str, Any],
    manifest: dict[str, Any],
    profiles: dict[str, Any],
) -> None:
    """Validate the complete graph, not only its scenario subgraph."""
    if not isinstance(graph, dict):
        raise Refusal("loader graph must be an object")
    if graph != build_loader_graph(manifest, profiles):
        raise Refusal("loader graph differs from its source-bound derivation")
    _validate_complete_scenarios(graph, profiles)


def _partition_ranges(
    path: str, generated: bool, *, exact_literal: bool = False
) -> list[dict[str, Any]]:
    data = _source_blob(path)
    if generated:
        return [
            {
                "start": 0,
                "end": len(data),
                "classification": "generated_duplicate",
                "span_sha256": _sha256(data),
            }
        ]
    if exact_literal:
        return [
            {
                "start": 0,
                "end": len(data),
                "classification": "exact_literal_or_evidence",
                "span_sha256": _sha256(data),
            }
        ]
    _preflight_partition_markdown(data, path)
    lines = data.splitlines(keepends=True)
    inline_list_marker = re.compile(
        rb"(?:([*+-])|([0-9]{1,9})[.)])"
    )
    marker_whitespace = re.compile(rb"[ \t]*")

    def leading_spaces(line: bytes) -> int:
        return len(line) - len(line.lstrip(b" "))

    def whitespace_end_column(start: int, whitespace: bytes) -> int:
        column = start
        for value in whitespace:
            column += 1 if value == 0x20 else 4 - column % 4
        return column

    def thematic_break(line: bytes) -> bool:
        """Recognise bounded thematic breaks with constant auxiliary state."""
        end = len(line)
        while end and line[end - 1] in b"\r\n":
            end -= 1
        index = 0
        while index < end and line[index] == 0x20:
            index += 1
        if index > 3 or index == end or line[index] not in b"*-_":
            return False
        marker = line[index]
        count = 0
        while index < end:
            value = line[index]
            if value == marker:
                count += 1
            elif value not in b" \t":
                return False
            index += 1
        return count >= 3

    def thematic_suffix_window(line: bytes) -> tuple[int, int, int] | None:
        """Bound homogeneous thematic suffixes with constant auxiliary state."""
        end = len(line)
        while end and line[end - 1] in b" \t\r\n":
            end -= 1
        if not end or line[end - 1] not in b"*-_":
            return None
        marker = line[end - 1]
        count = 0
        earliest = end
        third_from_end: int | None = None
        cursor = end - 1
        while cursor >= 0 and line[cursor] == marker:
            count += 1
            earliest = cursor
            if count == 3:
                third_from_end = cursor
            cursor -= 1
            while cursor >= 0 and line[cursor] in b" \t":
                cursor -= 1
        if third_from_end is None:
            return None
        return marker, earliest, third_from_end

    def list_block_marker(line: bytes) -> re.Match[bytes] | None:
        """Return a valid bounded list marker, with thematic precedence."""
        if thematic_break(line):
            return None
        return re.match(
            rb"^ {0,3}(?:([*+-])|([0-9]{1,9})[.)])(?:[ \t]+|$)",
            line.rstrip(b"\r\n"),
        )

    def paragraph_interrupts(line: bytes) -> bool:
        """Return whether a bounded block start can end a lazy paragraph."""
        content = line.rstrip(b"\r\n")
        if thematic_break(line):
            return True
        fence = re.match(rb"^ {0,3}(`{3,}|~{3,})(.*)", content)
        if fence is not None:
            marker, remainder = fence.groups()
            if marker[:1] == b"~" or b"`" not in remainder:
                return True
        if re.match(rb"^ {0,3}(?:#{1,6})(?:[ \t]+|$)", content):
            return True
        if re.match(rb"^ {0,3}>", content):
            return True
        marker = list_block_marker(line)
        if marker is None:
            return False
        remainder = content[marker.end():]
        if not remainder.strip(b" \t"):
            return False
        return marker.group(1) is not None or int(marker.group(2)) == 1

    def list_container_interrupts(
        line: bytes, active: list[int], indent: int
    ) -> bool:
        """Recognise a block that exits the deepest active list item."""
        limit = max(0, len(active) - 1)
        start = bisect_left(active, indent - 3, 0, limit)
        end = bisect_right(active, indent, start, limit)
        for index in range(end - 1, start - 1, -1):
            parent = active[index]
            relative = line[parent:]
            if (
                paragraph_interrupts(relative)
                or list_block_marker(relative) is not None
            ):
                return True
        return indent <= 3 and (
            paragraph_interrupts(line)
            or list_block_marker(line) is not None
        )

    def update_list_containers(
        line: bytes,
        active: list[int],
        paragraph_baseline: int | None,
    ) -> tuple[
        list[int], tuple[int, int] | None, int | None, bool, bool
    ]:
        """Track bounded list baselines, marker suffixes and lazy paragraphs."""
        if not line.strip(b" \t\r\n"):
            return active, None, None, False, False
        indent = leading_spaces(line)
        result = active
        container_interrupt = list_container_interrupts(line, active, indent)
        while result and indent < result[-1]:
            if (
                paragraph_baseline == result[-1]
                and not paragraph_interrupts(line)
                and not container_interrupt
            ):
                return result, None, paragraph_baseline, False, True
            if result is active:
                result = list(active)
            removed = result.pop()
            if paragraph_baseline == removed:
                paragraph_baseline = None
        parent = result[-1] if result else 0
        if indent < parent or indent - parent > 3:
            return result, None, paragraph_baseline, False, False
        byte_index = indent
        column = indent
        content_start: tuple[int, int] | None = None
        marker_found = False
        content_end = len(line)
        while content_end and line[content_end - 1] in b"\r\n":
            content_end -= 1
        thematic_window = thematic_suffix_window(line)
        while True:
            if (
                thematic_window is not None
                and thematic_window[1] <= byte_index <= thematic_window[2]
                and line[byte_index] == thematic_window[0]
            ):
                break
            marker = inline_list_marker.match(line, byte_index, content_end)
            if marker is None:
                break
            marker_byte_end = marker.end()
            whitespace_match = marker_whitespace.match(
                line, marker_byte_end, content_end
            )
            whitespace_byte_end = whitespace_match.end()
            has_whitespace = whitespace_byte_end > marker_byte_end
            has_remainder = whitespace_byte_end < content_end
            if not has_whitespace and has_remainder:
                break
            if paragraph_baseline == parent and (
                not has_remainder
                or (
                    marker.group(2) is not None
                    and int(marker.group(2)) != 1
                )
            ):
                break
            marker_end = column + marker_byte_end - byte_index
            whitespace = line[marker_byte_end:whitespace_byte_end]
            whitespace_end = whitespace_end_column(marker_end, whitespace)
            padding = whitespace_end - marker_end
            blank_item = not has_remainder
            content_indent = marker_end + (
                1 if blank_item or padding > 4 else padding
            )
            if content_indent <= parent:
                break
            if len(result) >= MAX_MARKDOWN_LIST_DEPTH:
                raise Refusal(
                    f"partition Markdown list container depth exceeds limit: {path}"
                )
            if result is active:
                result = list(active)
            result.append(content_indent)
            marker_found = True
            byte_index = whitespace_byte_end
            column = whitespace_end
            content_start = (
                None
                if blank_item or padding > 4
                else (byte_index, column)
            )
            if blank_item or padding > 4:
                break
            parent = content_indent
            paragraph_baseline = None
        return (
            result,
            content_start,
            paragraph_baseline,
            marker_found,
            False,
        )

    def fence_container(indent: int, active: list[int]) -> int | None:
        start = bisect_left(active, indent - 3)
        end = bisect_right(active, indent, start)
        if start < end:
            return active[end - 1]
        return 0 if indent <= 3 else None

    def fence_marker(
        line: bytes,
        container_indent: int,
        *,
        byte_index: int = 0,
        column: int = 0,
    ) -> tuple[bytes, bytes] | None:
        match = re.match(
            rb"^( *)(`{3,}|~{3,})([^\r\n]*)", line[byte_index:]
        )
        if match is None:
            return None
        indent = column + len(match.group(1))
        if not container_indent <= indent <= container_indent + 3:
            return None
        return match.group(2), match.group(3)

    def opens(marker: tuple[bytes, bytes]) -> bool:
        fence, remainder = marker
        return fence[:1] == b"~" or b"`" not in remainder

    def closes(marker: tuple[bytes, bytes], active: tuple[int, int]) -> bool:
        fence, remainder = marker
        return (
            fence[0] == active[0]
            and len(fence) >= active[1]
            and not remainder.strip(b" \t")
        )

    suffix_events: dict[
        int, list[tuple[int, tuple[bytes, bytes]]]
    ] | None = None
    suffix_balance_indexes: dict[int, tuple[list[int], list[bool]]] = {}

    def indexed_suffix_events(
    ) -> dict[int, list[tuple[int, tuple[bytes, bytes]]]]:
        """Index each root-leading marker under its at-most-four baselines."""
        nonlocal suffix_events
        if suffix_events is not None:
            return suffix_events
        suffix_events = {}
        for index, line in enumerate(lines):
            match = re.match(
                rb"^( *)(`{3,}|~{3,})([^\r\n]*)", line
            )
            if match is None:
                continue
            indent = len(match.group(1))
            marker = (match.group(2), match.group(3))
            for baseline in range(max(0, indent - 3), indent + 1):
                suffix_events.setdefault(baseline, []).append((index, marker))
        return suffix_events

    def suffix_balance_index(
        container_indent: int,
    ) -> tuple[list[int], list[bool]]:
        """Build the greedy CommonMark balance result for every event suffix."""
        cached = suffix_balance_indexes.get(container_indent)
        if cached is not None:
            return cached
        events = indexed_suffix_events().get(container_indent, [])
        positions = [index for index, _ in events]
        event_count = len(events)
        balanced = [True] * (event_count + 1)
        if not events:
            result = (positions, balanced)
            suffix_balance_indexes[container_indent] = result
            return result

        lengths = sorted({len(marker[0]) for _, marker in events})
        length_count = len(lengths)
        nearest_by_type = {
            ord("`"): [event_count] * (length_count + 1),
            ord("~"): [event_count] * (length_count + 1),
        }
        next_close = [event_count] * event_count

        def nearest_at_least(tree: list[int], length: int) -> int:
            cursor = length_count - bisect_left(lengths, length)
            nearest = event_count
            while cursor:
                nearest = min(nearest, tree[cursor])
                cursor -= cursor & -cursor
            return nearest

        def add_closer(tree: list[int], length: int, index: int) -> None:
            cursor = length_count - bisect_left(lengths, length)
            while cursor <= length_count:
                tree[cursor] = min(tree[cursor], index)
                cursor += cursor & -cursor

        for event_index in range(event_count - 1, -1, -1):
            _, marker = events[event_index]
            fence, remainder = marker
            tree = nearest_by_type[fence[0]]
            next_close[event_index] = nearest_at_least(tree, len(fence))
            if not remainder.strip(b" \t"):
                add_closer(tree, len(fence), event_index)

        for event_index in range(event_count - 1, -1, -1):
            _, marker = events[event_index]
            if not opens(marker):
                balanced[event_index] = balanced[event_index + 1]
                continue
            close_index = next_close[event_index]
            balanced[event_index] = (
                close_index < event_count and balanced[close_index + 1]
            )
        result = (positions, balanced)
        suffix_balance_indexes[container_indent] = result
        return result

    def commonmark_suffix_is_balanced(start: int, container_indent: int) -> bool:
        positions, balanced = suffix_balance_index(container_indent)
        return balanced[bisect_left(positions, start)]

    ranges: list[tuple[int, int, str]] = []
    offset = 0
    active_fence: tuple[int, int, int] | None = None
    pending_template: tuple[int, int] | None = None
    list_containers: list[int] = []
    paragraph_baseline: int | None = None
    for index, line in enumerate(lines):
        content_start: tuple[int, int] | None = None
        marker_found = False
        lazy_continuation = False
        if active_fence is None:
            (
                list_containers,
                content_start,
                paragraph_baseline,
                marker_found,
                lazy_continuation,
            ) = update_list_containers(
                line, list_containers, paragraph_baseline
            )
            container_indent = fence_container(
                leading_spaces(line), list_containers
            )
        else:
            container_indent = active_fence[2]
        marker = (
            None
            if container_indent is None
            else fence_marker(line, container_indent)
        )
        if marker is None and content_start is not None:
            byte_index, column = content_start
            same_line_container = fence_container(column, list_containers)
            if same_line_container is not None:
                marker = fence_marker(
                    line,
                    same_line_container,
                    byte_index=byte_index,
                    column=column,
                )
                if marker is not None:
                    container_indent = same_line_container
        classification = "governed_operative_semantics"
        if active_fence is not None:
            classification = "exact_literal_or_evidence"
            if marker is not None:
                fence, remainder = marker
                active_marker = (active_fence[0], active_fence[1])
                if closes(marker, active_marker):
                    if (
                        pending_template is not None
                        and closes(marker, pending_template)
                        and not commonmark_suffix_is_balanced(
                            index + 1, active_fence[2]
                        )
                    ):
                        pending_template = None
                    else:
                        active_fence = None
                        pending_template = None
                elif pending_template is not None and closes(
                    marker, pending_template
                ):
                    pending_template = None
                elif remainder.strip(b" \t") and opens(marker):
                    # Three source templates deliberately show fenced diffs inside
                    # a surrounding fence. Blank or unmatched inner markers remain
                    # CommonMark literals; only an explicit balanced template pair
                    # can delay the surrounding close.
                    pending_template = (fence[0], len(fence))
        elif marker is not None:
            fence, _ = marker
            if opens(marker):
                classification = "exact_literal_or_evidence"
                active_fence = (fence[0], len(fence), container_indent)
        if active_fence is not None:
            paragraph_baseline = None
        elif not line.strip(b" \t\r\n"):
            paragraph_baseline = None
        elif lazy_continuation:
            pass
        elif marker_found:
            if content_start is None:
                paragraph_baseline = None
            else:
                byte_index, _ = content_start
                paragraph_baseline = (
                    list_containers[-1]
                    if not paragraph_interrupts(line[byte_index:])
                    else None
                )
        else:
            indent = leading_spaces(line)
            baseline = (
                list_containers[-1]
                if list_containers and indent >= list_containers[-1]
                else 0
            )
            relative = line[baseline:]
            relative_indent = leading_spaces(relative)
            if paragraph_interrupts(relative) or (
                relative_indent >= 4 and paragraph_baseline != baseline
            ):
                paragraph_baseline = None
            else:
                paragraph_baseline = baseline
        end = offset + len(line)
        if ranges and ranges[-1][2] == classification:
            ranges[-1] = (ranges[-1][0], end, classification)
        else:
            ranges.append((offset, end, classification))
        offset = end
    if offset < len(data):
        classification = (
            "exact_literal_or_evidence"
            if active_fence is not None
            else "governed_operative_semantics"
        )
        ranges.append((offset, len(data), classification))
    if active_fence is not None:
        raise Refusal(f"unterminated Markdown fence: {path}")
    return [
        {
            "start": start,
            "end": end,
            "classification": classification,
            "span_sha256": _sha256(data[start:end]),
        }
        for start, end, classification in ranges
    ]


def build_partition(manifest: dict[str, Any]) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    totals = {name: 0 for name in PARTITION_CLASSES}
    for document in manifest["documents"]:
        generated = (
            document["document_class"] == "promise_machine_contract"
            and document["path"] != "PROMISE_MACHINE.md"
        )
        ranges = _partition_ranges(
            document["path"],
            generated,
            exact_literal=document["document_class"]
            in {"fixed_input", "structured_reference"},
        )
        for item in ranges:
            totals[item["classification"]] += item["end"] - item["start"]
        files.append(
            {
                "path": document["path"],
                "source_sha256": document["sha256"],
                "bytes": document["bytes"],
                "ranges": ranges,
            }
        )
    if sum(totals.values()) != manifest["totals"]["physical_bytes"]:
        raise Refusal("byte partition does not reconcile to physical bytes")
    return {
        "schema": f"{SCHEMA_PREFIX}-byte-partition/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": _artifact_digest(manifest),
        "classifications": list(PARTITION_CLASSES),
        "unsupported_operative_bytes": totals["unsupported_or_unknown"],
        "totals": totals,
        "files": files,
    }


def _logical_skill_groups(manifest: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for item in manifest["documents"]:
        if item["path"] != item["canonical_content_path"]:
            continue
        logical = item["logical_document"]
        if logical.startswith("skill:"):
            groups.setdefault(logical.removeprefix("skill:"), []).append(item)
    return groups


def _choose_holdout(manifest: dict[str, Any]) -> list[str]:
    groups = _logical_skill_groups(manifest)
    excluded = {"fiat", "horos", "promise-machine"}
    eligible = sorted(name for name in groups if name not in excluded)
    sizes = {name: sum(item["bytes"] for item in groups[name]) for name in eligible}
    ordered_sizes = sorted((size, name) for name, size in sizes.items())
    quartile: dict[str, int] = {}
    for index, (_, name) in enumerate(ordered_sizes):
        quartile[name] = min(3, index * 4 // len(ordered_sizes))
    total = manifest["totals"]["unique_bytes"]
    minimum = math.ceil(total * 0.20)
    maximum = math.floor(total * 0.50)
    best: tuple[int, str, tuple[str, ...]] | None = None
    for names in itertools.combinations(eligible, 5):
        held = sum(sizes[name] for name in names)
        if held < minimum or held > maximum:
            continue
        if len({_plugin(item["path"]) for name in names for item in groups[name]}) < 3:
            continue
        if len({quartile[name] for name in names}) < 3:
            continue
        tie = _sha256((SELECTION_SEED + "\0" + "\0".join(names)).encode("utf-8"))
        score = (held - minimum, tie, names)
        if best is None or score < best:
            best = score
    if best is None:
        raise Refusal(
            "deterministic holdout selection has no feasible five-skill cohort"
        )
    return list(best[2])


def _size_deciles(records: list[dict[str, Any]]) -> dict[str, int]:
    ordered = sorted(records, key=lambda item: (item["bytes"], item["path"]))
    return {
        item["path"]: min(9, index * 10 // len(ordered))
        for index, item in enumerate(ordered)
    }


def _observed_constructs(paths: list[str]) -> list[str]:
    data = b"\n".join(_source_blob(path) for path in paths)
    checks = {
        "authority": (b"authoris", b"authority"),
        "failure": (b"fail",),
        "recovery": (b"Recovery:",),
        "exact-literal": (b"```", b"`"),
        "cross-document": (b".md",),
        "order": (b"order",),
        "scope": (b"scope",),
        "negation": (b" not ",),
        "exception": (b"Exceptions:",),
        "unknown": (b"unknown",),
        "refusal": (b"Refuses:",),
    }
    present = [
        name
        for name, needles in checks.items()
        if any(needle in data for needle in needles)
    ]
    if set(present) != set(checks):
        raise Refusal("development cohort misses an observed construct class")
    return sorted(present)


def _case_envelope(skills: list[str]) -> list[dict[str, str]]:
    semantic = ["authority", "failure", "recovery", "exact-literal", "cross-document"]
    shapes = ["decision", "refusal", "recovery", "tool-invocation", "structured-plan"]
    slots: list[dict[str, str]] = []
    for index in range(16):
        slots.append(
            {
                "id": f"holdout-{index + 1:02d}",
                "logical_skill": skills[index % len(skills)],
                "semantic_class": semantic[index % len(semantic)],
                "response_shape": shapes[(index * 3) % len(shapes)],
            }
        )
    return slots


def build_cohorts(manifest: dict[str, Any]) -> dict[str, Any]:
    unique_records = [
        item
        for item in manifest["documents"]
        if item["path"] == item["canonical_content_path"]
    ]
    holdout_skills = _choose_holdout(manifest)
    holdout_logical = {f"skill:{name}" for name in holdout_skills}
    holdout_records = [
        item for item in unique_records if item["logical_document"] in holdout_logical
    ]
    development_records = [
        item for item in unique_records if item not in holdout_records
    ]
    generated_paths = sorted(
        item["path"]
        for item in manifest["documents"]
        if item["path"] != item["canonical_content_path"]
    )
    total = manifest["totals"]["unique_bytes"]
    deciles = _size_deciles(unique_records)
    development_deciles = sorted(
        {deciles[item["path"]] for item in development_records}
    )
    if development_deciles != list(range(10)):
        raise Refusal("development cohort does not cover every size decile")
    development_skills = sorted(
        {
            item["logical_document"].removeprefix("skill:")
            for item in development_records
            if item["logical_document"].startswith("skill:")
        }
    )
    development_bytes = sum(item["bytes"] for item in development_records)
    holdout_bytes = sum(item["bytes"] for item in holdout_records)
    development_classes = sorted(
        {item["document_class"] for item in development_records}
    )
    all_classes = sorted({item["document_class"] for item in unique_records})
    if development_classes != all_classes or all_classes != sorted(EXPECTED_COUNTS):
        raise Refusal("development cohort does not cover every document class")
    development_authorities = sorted(
        {item["authority_tier"] for item in development_records}
    )
    all_authorities = sorted({item["authority_tier"] for item in unique_records})
    if development_authorities != all_authorities:
        raise Refusal("development cohort does not cover every authority tier")
    if len(development_skills) < 12 or development_bytes / total < 0.50:
        raise Refusal("development cohort coverage gate failed")
    if len(holdout_skills) != 5 or holdout_bytes / total < 0.20:
        raise Refusal("holdout cohort coverage gate failed")
    if {item["path"] for item in development_records} & {
        item["path"] for item in holdout_records
    }:
        raise Refusal("development and holdout cohorts overlap")
    slots = _case_envelope(holdout_skills)
    return {
        "schema": f"{SCHEMA_PREFIX}-cohorts/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": _artifact_digest(manifest),
        "selection": {
            "seed": SELECTION_SEED,
            "method": "enumerate five-skill combinations; require three plugins and three size quartiles; minimise bytes above the 20 percent floor; break ties by seeded SHA-256",
            "excluded_from_holdout": [
                "fiat: required by the merged WAI1 development control",
                "horos: required by the merged WAI1 development control",
                "promise-machine: shared root and merged WAI1 development control",
            ],
        },
        "development": {
            "logical_skills": development_skills,
            "paths": sorted(item["path"] for item in development_records),
            "unique_bytes": development_bytes,
            "unique_byte_ratio": f"{development_bytes / total:.6f}",
            "authority_tiers": development_authorities,
            "document_classes": development_classes,
            "size_deciles": development_deciles,
            "constructs": _observed_constructs(
                sorted(item["path"] for item in development_records)
            ),
        },
        "holdout": {
            "logical_skills": holdout_skills,
            "paths": sorted(item["path"] for item in holdout_records),
            "unique_bytes": holdout_bytes,
            "unique_byte_ratio": f"{holdout_bytes / total:.6f}",
            "semantic_classes": [
                "authority",
                "failure",
                "recovery",
                "exact-literal",
                "cross-document",
            ],
            "case_slots": slots,
        },
        "generated_duplicates_excluded": generated_paths,
    }


def build_holdout_seal(
    manifest: dict[str, Any],
    cohorts: dict[str, Any],
    profiles: dict[str, Any],
    graph: dict[str, Any],
) -> dict[str, Any]:
    membership = {
        "logical_skills": cohorts["holdout"]["logical_skills"],
        "paths": cohorts["holdout"]["paths"],
    }
    envelope = {
        "slots": cohorts["holdout"]["case_slots"],
        "forbidden_until_open": [
            "prompt",
            "expected_answer",
            "scorer_key",
            "model_output",
        ],
    }
    body = {
        "schema": f"{SCHEMA_PREFIX}-holdout-seal/v1",
        "source_ref": SOURCE_REF,
        "manifest_sha256": _artifact_digest(manifest),
        "cohorts_sha256": _artifact_digest(cohorts),
        "invocation_profiles_sha256": _artifact_digest(profiles),
        "loader_graph_sha256": _artifact_digest(graph),
        "selection_seed": SELECTION_SEED,
        "membership": membership,
        "membership_sha256": _sha256(_canonical_json(membership)),
        "closed_future_case_envelope": envelope,
        "case_envelope_sha256": _sha256(_canonical_json(envelope)),
        "opened": False,
    }
    return {**body, "commitment_sha256": _sha256(_canonical_json(body))}


def _validate_holdout_seal(
    seal: dict[str, Any],
    manifest: dict[str, Any],
    cohorts: dict[str, Any],
    profiles: dict[str, Any],
    graph: dict[str, Any],
) -> None:
    """Recompute every sealed identity without trusting its commitment body."""
    if not isinstance(seal, dict):
        raise Refusal("holdout seal must be an object")
    _require_fields(
        seal,
        (
            "case_envelope_sha256",
            "closed_future_case_envelope",
            "cohorts_sha256",
            "commitment_sha256",
            "invocation_profiles_sha256",
            "loader_graph_sha256",
            "manifest_sha256",
            "membership",
            "membership_sha256",
            "opened",
            "schema",
            "selection_seed",
            "source_ref",
        ),
        (
            "case_envelope_sha256",
            "closed_future_case_envelope",
            "cohorts_sha256",
            "commitment_sha256",
            "invocation_profiles_sha256",
            "loader_graph_sha256",
            "manifest_sha256",
            "membership",
            "membership_sha256",
            "opened",
            "schema",
            "selection_seed",
            "source_ref",
        ),
        "holdout seal",
    )
    if (
        seal["schema"] != f"{SCHEMA_PREFIX}-holdout-seal/v1"
        or seal["source_ref"] != SOURCE_REF
        or seal["selection_seed"] != SELECTION_SEED
        or seal["opened"] is not False
    ):
        raise Refusal("holdout seal source identity drift")
    expected_fields = {
        "manifest_sha256": _artifact_digest(manifest),
        "cohorts_sha256": _artifact_digest(cohorts),
        "invocation_profiles_sha256": _artifact_digest(profiles),
        "loader_graph_sha256": _artifact_digest(graph),
    }
    if any(seal.get(field) != digest for field, digest in expected_fields.items()):
        raise Refusal("holdout seal input identity drift")
    _validate_cohorts(cohorts, manifest)

    expected_membership = {
        "logical_skills": cohorts["holdout"]["logical_skills"],
        "paths": cohorts["holdout"]["paths"],
    }
    membership = seal["membership"]
    if membership != expected_membership:
        raise Refusal("holdout seal membership drift")
    if seal["membership_sha256"] != _sha256(_canonical_json(membership)):
        raise Refusal("holdout seal membership digest drift")

    expected_envelope = {
        "slots": cohorts["holdout"]["case_slots"],
        "forbidden_until_open": [
            "prompt",
            "expected_answer",
            "scorer_key",
            "model_output",
        ],
    }
    envelope = seal["closed_future_case_envelope"]
    if envelope != expected_envelope:
        raise Refusal("holdout seal case envelope drift")
    if seal["case_envelope_sha256"] != _sha256(_canonical_json(envelope)):
        raise Refusal("holdout seal case envelope digest drift")

    body = dict(seal)
    commitment = body.pop("commitment_sha256", None)
    if commitment != _sha256(_canonical_json(body)):
        raise Refusal("holdout commitment is open or inconsistent")
    forbidden = set(envelope["forbidden_until_open"])
    for slot in envelope["slots"]:
        if forbidden & set(slot):
            raise Refusal("sealed slot contains answer-bearing material")


def _validate_manifest_shape(
    manifest: dict[str, Any], profiles: dict[str, Any] | None = None
) -> None:
    if not isinstance(manifest, dict):
        raise Refusal("manifest must be an object")
    _require_fields(
        manifest,
        ("schema", "source", "counts", "totals", "documents"),
        ("schema", "source", "counts", "totals", "documents"),
        "manifest",
    )
    if manifest["schema"] != f"{SCHEMA_PREFIX}-corpus-manifest/v1":
        raise Refusal("unsupported manifest schema")
    source = manifest["source"]
    if not isinstance(source, dict):
        raise Refusal("manifest source must be an object")
    _require_fields(
        source,
        ("ref", "repository_paths", "tree_sha256"),
        ("ref", "repository_paths", "tree_sha256"),
        "manifest source",
    )
    repository_paths = source["repository_paths"]
    if (
        source["ref"] != SOURCE_REF
        or not isinstance(source["tree_sha256"], str)
        or re.fullmatch(r"[0-9a-f]{64}", source["tree_sha256"]) is None
        or not isinstance(repository_paths, list)
        or not repository_paths
        or len(repository_paths) > MAX_FROZEN_TREE_PATHS
        or any(not isinstance(path, str) for path in repository_paths)
        or repository_paths != sorted(set(repository_paths))
    ):
        raise Refusal("manifest source topology is malformed")
    for path in repository_paths:
        _safe_relative(path)
    if tuple(repository_paths) != _frozen_tree_paths():
        raise Refusal("manifest source topology drift")
    if not isinstance(manifest["documents"], list):
        raise Refusal("manifest documents must be an array")
    fields = {
        "path",
        "logical_document",
        "document_class",
        "admission_kind",
        "bytes",
        "sha256",
        "exact_duplicate_group",
        "canonical_content_path",
        "canonical_owner",
        "authority_tier",
        "load_semantics",
        "loader_roots",
        "scenario_reachability",
        "source_evidence",
        "runtime_evidence",
        "external_runtime_owner",
    }
    for index, item in enumerate(manifest["documents"]):
        if not isinstance(item, dict) or set(item) != fields:
            raise Refusal(f"manifest document {index} has a non-closed field set")
        _safe_relative(item["path"])
        structured = _structured_metadata().get(item["path"])
        fixed_agent = _fixed_agent_metadata().get(item["path"])
        reference_only = REFERENCE_ONLY_MARKDOWN.get(item["path"])
        if fixed_agent is not None:
            if (
                item["document_class"] != "fixed_input"
                or item["load_semantics"] != "agent-or-prompt"
                or item["source_evidence"]
                != _evidence(
                    fixed_agent["source_path"], fixed_agent["source_needle"]
                )
                or item["runtime_evidence"] is not None
                or not item["loader_roots"]
                or not item["scenario_reachability"]
            ):
                raise Refusal(f"fixed agent input semantics drift: {item['path']}")
            continue
        if reference_only is not None:
            source, needle, _ = reference_only
            if (
                item["load_semantics"] != "reference-only"
                or item["source_evidence"] != _evidence(source, needle)
                or item["runtime_evidence"] is not None
                or item["loader_roots"]
                or item["scenario_reachability"]
            ):
                raise Refusal(f"human reference semantics drift: {item['path']}")
            continue
        if structured is None:
            if (
                item["load_semantics"] != "agent-or-prompt"
                or item["source_evidence"] is not None
                or item["runtime_evidence"] is not None
                or not item["loader_roots"]
                or not item["scenario_reachability"]
            ):
                raise Refusal(f"ordinary manifest semantics drift: {item['path']}")
            continue
        if (
            item["load_semantics"] != structured["load_semantics"]
            or item["source_evidence"]
            != _evidence(structured["source_path"], structured["source_needle"])
        ):
            raise Refusal(f"structured manifest semantics drift: {item['path']}")
        if item["load_semantics"] == "reference-only":
            if (
                item["runtime_evidence"] is not None
                or item["loader_roots"]
                or item["scenario_reachability"]
            ):
                raise Refusal(f"reference-only manifest reachability drift: {item['path']}")
        else:
            runtime_path = structured["runtime_path"]
            runtime_needle = structured["runtime_needle"]
            if (
                runtime_path is None
                or runtime_needle is None
                or item["runtime_evidence"]
                != _evidence(runtime_path, runtime_needle)
                or not item["loader_roots"]
                or not item["scenario_reachability"]
            ):
                raise Refusal(f"mandatory manifest reachability drift: {item['path']}")

    if not {item["path"] for item in manifest["documents"]} <= set(
        repository_paths
    ):
        raise Refusal("manifest source topology omits a corpus path")

    source_counts = {
        name: 0 for name in EXPECTED_MANIFEST_SOURCE_EVIDENCE_COUNTS
    }
    runtime_counts = {
        target: 0 for target in EXPECTED_GRAPH_RUNTIME_EVIDENCE_COUNTS
    }
    for item in manifest["documents"]:
        source_evidence = item["source_evidence"]
        if source_evidence is not None:
            evidence_class, source, needle = _validation_manifest_source_anchor(
                item["path"]
            )
            if evidence_class not in source_counts:
                raise Refusal(
                    f"manifest semantic source class is unowned: {evidence_class}"
                )
            if (
                item["document_class"] != evidence_class
                or source_evidence != _validation_evidence(source, needle)
            ):
                raise Refusal(f"manifest semantic source anchor drift: {item['path']}")
            source_counts[evidence_class] += 1
        runtime_evidence = item["runtime_evidence"]
        if runtime_evidence is not None:
            runtime_path, runtime_needle = _validation_runtime_anchor(
                item["path"], "manifest"
            )
            if runtime_evidence != _validation_evidence(
                runtime_path, runtime_needle
            ):
                raise Refusal(f"manifest semantic runtime anchor drift: {item['path']}")
            runtime_counts[item["path"]] += 1
    if source_counts != EXPECTED_MANIFEST_SOURCE_EVIDENCE_COUNTS or sum(
        source_counts.values()
    ) != sum(
        item["source_evidence"] is not None for item in manifest["documents"]
    ):
        raise Refusal("manifest semantic source evidence coverage drift")
    if set(runtime_counts.values()) != {1} or sum(runtime_counts.values()) != sum(
        item["runtime_evidence"] is not None for item in manifest["documents"]
    ):
        raise Refusal("manifest semantic runtime evidence coverage drift")

    if profiles is None:
        profiles = build_invocation_profiles()
    else:
        _validate_invocation_profiles(profiles)
    if manifest != build_manifest(profiles):
        raise Refusal("manifest differs from its source-bound derivation")


def _validate_partition_closure(
    partition: dict[str, Any], manifest: dict[str, Any]
) -> None:
    if not isinstance(partition, dict):
        raise Refusal("partition must be an object")
    _require_fields(
        partition,
        (
            "classifications",
            "files",
            "manifest_sha256",
            "schema",
            "source_ref",
            "totals",
            "unsupported_operative_bytes",
        ),
        (
            "classifications",
            "files",
            "manifest_sha256",
            "schema",
            "source_ref",
            "totals",
            "unsupported_operative_bytes",
        ),
        "partition",
    )
    if (
        partition["schema"] != f"{SCHEMA_PREFIX}-byte-partition/v1"
        or partition["source_ref"] != SOURCE_REF
        or partition["classifications"] != list(PARTITION_CLASSES)
        or not isinstance(partition["files"], list)
        or not partition["files"]
    ):
        raise Refusal("partition identity or structure drift")
    for file_record in partition["files"]:
        if not isinstance(file_record, dict):
            raise Refusal("partition file record must be an object")
        _require_fields(
            file_record,
            ("bytes", "path", "ranges", "source_sha256"),
            ("bytes", "path", "ranges", "source_sha256"),
            "partition file record",
        )
        if not isinstance(file_record["path"], str):
            raise Refusal("partition file path is malformed")
        _safe_relative(file_record["path"])
        if not isinstance(file_record["ranges"], list) or not file_record["ranges"]:
            raise Refusal("partition file ranges are malformed")
        cursor = 0
        data = _source_blob(file_record["path"])
        for item in file_record["ranges"]:
            if not isinstance(item, dict) or set(item) != {
                "start",
                "end",
                "classification",
                "span_sha256",
            }:
                raise Refusal("partition range has a non-closed field set")
            if (
                type(item["start"]) is not int
                or type(item["end"]) is not int
                or item["start"] != cursor
                or item["end"] <= item["start"]
            ):
                raise Refusal("partition ranges overlap, gap, or are unordered")
            if item["classification"] not in PARTITION_CLASSES:
                raise Refusal("partition range has an unknown class")
            if _sha256(data[item["start"] : item["end"]]) != item["span_sha256"]:
                raise Refusal("partition span digest mismatch")
            cursor = item["end"]
        if cursor != len(data) or cursor != file_record["bytes"]:
            raise Refusal("partition does not close over its source")

    if partition["manifest_sha256"] != _artifact_digest(manifest):
        raise Refusal("partition manifest identity drift")
    if partition != build_partition(manifest):
        raise Refusal("partition differs from its source-bound derivation")


def _validate_cohorts(cohorts: dict[str, Any], manifest: dict[str, Any]) -> None:
    """Refuse cohort bytes not produced by the fixed source-bound selection."""
    if not isinstance(cohorts, dict):
        raise Refusal("cohorts must be an object")
    if cohorts != build_cohorts(manifest):
        raise Refusal("cohorts differ from their source-bound derivation")


def _validate_artifact_inventory(inventory: dict[str, Any]) -> None:
    _require_fields(
        inventory,
        (
            "artifacts",
            "reconciliation",
            "schema",
            "source_ref",
            "source_tree_sha256",
        ),
        (
            "artifacts",
            "reconciliation",
            "schema",
            "source_ref",
            "source_tree_sha256",
        ),
        "artifact inventory",
    )
    if inventory["schema"] != f"{SCHEMA_PREFIX}-artifact-inventory/v1":
        raise Refusal("artifact inventory schema mismatch")
    if inventory["source_ref"] != SOURCE_REF:
        raise Refusal("artifact inventory source ref mismatch")
    if not isinstance(inventory["source_tree_sha256"], str) or re.fullmatch(
        r"[0-9a-f]{64}", inventory["source_tree_sha256"]
    ) is None:
        raise Refusal("artifact inventory source tree digest is invalid")
    artifacts = inventory["artifacts"]
    if not isinstance(artifacts, dict) or set(artifacts) != set(
        BASELINE_RECORD_NAMES
    ):
        raise Refusal("artifact inventory record set mismatch")
    for name in BASELINE_RECORD_NAMES:
        record = artifacts[name]
        if not isinstance(record, dict):
            raise Refusal("artifact inventory record is not an object")
        _require_fields(
            record,
            ("bytes", "sha256"),
            ("bytes", "sha256"),
            "artifact inventory record",
        )
        if type(record["bytes"]) is not int or record["bytes"] < 1:
            raise Refusal("artifact inventory byte count is invalid")
        if not isinstance(record["sha256"], str) or re.fullmatch(
            r"[0-9a-f]{64}", record["sha256"]
        ) is None:
            raise Refusal("artifact inventory digest is invalid")
    reconciliation = inventory["reconciliation"]
    if not isinstance(reconciliation, dict):
        raise Refusal("reconciliation inventory record is not an object")
    _require_fields(
        reconciliation,
        ("bytes", "sha256"),
        ("bytes", "sha256"),
        "reconciliation inventory record",
    )
    if type(reconciliation["bytes"]) is not int or reconciliation["bytes"] < 1:
        raise Refusal("reconciliation inventory byte count is invalid")
    if not isinstance(reconciliation["sha256"], str) or re.fullmatch(
        r"[0-9a-f]{64}", reconciliation["sha256"]
    ) is None:
        raise Refusal("reconciliation inventory digest is invalid")


def _load_committed_baseline(
    requested: dict[str, Path],
    reconciliation: Path | None = None,
) -> dict[str, tuple[dict[str, Any], bytes]]:
    if not requested or not set(requested) <= set(BASELINE_RECORD_NAMES):
        raise Refusal("baseline verifier requested an unknown record")
    directory: PurePosixPath | None = None
    for name, path in requested.items():
        relative = _repository_relative(path, "baseline artifact")
        if relative.name != name:
            raise Refusal("baseline artifact filename mismatch")
        if directory is None:
            directory = relative.parent
        elif relative.parent != directory:
            raise Refusal("baseline artifacts do not share one inventory")
    if directory is None:
        raise Refusal("baseline verifier has no inventory directory")
    if reconciliation is None:
        if directory != BASELINE_FIXTURE_ROOT:
            raise Refusal("scratch baseline requires a reconciliation path")
        reconciliation = ROOT / Path(*BASELINE_RECONCILIATION.parts)
    else:
        _repository_relative(reconciliation, "reconciliation input")

    inventory_path = ROOT / Path(*directory.parts) / "artifact-inventory.json"
    inventory_raw = _read_regular(inventory_path, MAX_JSON_BYTES)
    if (
        directory == BASELINE_FIXTURE_ROOT
        and _sha256(inventory_raw) != EXPECTED_BASELINE_INVENTORY_SHA256
    ):
        raise Refusal("artifact inventory differs from its frozen source anchor")
    inventory = _decode_record(inventory_raw)
    _validate_artifact_inventory(inventory)
    loaded: dict[str, tuple[dict[str, Any], bytes]] = {}
    for name in BASELINE_RECORD_NAMES:
        path = ROOT / Path(*directory.parts) / name
        raw = _read_regular(path, MAX_JSON_BYTES)
        identity = inventory["artifacts"][name]
        if len(raw) != identity["bytes"] or _sha256(raw) != identity["sha256"]:
            raise Refusal(f"artifact inventory identity mismatch: {name}")
        loaded[name] = (_decode_record(raw), raw)

    reconciliation_raw = _read_regular(reconciliation, MAX_JSON_BYTES)
    reconciliation_identity = inventory["reconciliation"]
    if (
        len(reconciliation_raw) != reconciliation_identity["bytes"]
        or _sha256(reconciliation_raw) != reconciliation_identity["sha256"]
    ):
        raise Refusal("reconciliation inventory identity mismatch")
    if _read_regular(inventory_path, MAX_JSON_BYTES) != inventory_raw:
        raise Refusal("artifact inventory changed during generation read")

    manifest = loaded["corpus-manifest.json"][0]
    source = manifest.get("source")
    if not isinstance(source, dict) or (
        source.get("ref") != inventory["source_ref"]
        or source.get("tree_sha256") != inventory["source_tree_sha256"]
    ):
        raise Refusal("artifact inventory source identity mismatch")
    return loaded


def _verify_loaded(
    actual: dict[str, Any], raw: bytes, expected: dict[str, Any], label: str
) -> tuple[dict[str, Any], bytes]:
    if actual != expected:
        raise Refusal(f"{label} differs from its source-bound derivation")
    return actual, raw


def _result(command: str, artifact: bytes, metrics: dict[str, Any]) -> bytes:
    artifact_sha = _sha256(artifact)
    return _canonical_json(
        {
            "schema": f"{SCHEMA_PREFIX}-verification/v1",
            "command": command,
            "run_id": _sha256(
                (SOURCE_REF + "\0" + command + "\0" + artifact_sha).encode()
            ),
            "source_ref": SOURCE_REF,
            "artifact_sha256": artifact_sha,
            "status": "pass",
            "metrics": metrics,
        }
    )


def verify_corpus(args: argparse.Namespace) -> bytes:
    records = _load_committed_baseline(
        {
            "corpus-manifest.json": args.manifest,
            "invocation-profiles.json": args.profiles,
        },
        args.reconciliation,
    )
    profiles, _ = records["invocation-profiles.json"]
    _validate_invocation_profiles(profiles)
    if profiles != build_invocation_profiles():
        raise Refusal("invocation profile fixture is stale")
    expected = build_manifest(profiles)
    manifest, raw = _verify_loaded(
        *records["corpus-manifest.json"], expected, "corpus manifest"
    )
    _validate_manifest_shape(manifest, profiles)
    return _result("verify-corpus", raw, manifest["totals"])


def verify_loader(args: argparse.Namespace) -> bytes:
    records = _load_committed_baseline(
        {
            "corpus-manifest.json": args.manifest,
            "invocation-profiles.json": args.profiles,
            "loader-graph.json": args.graph,
        },
        args.reconciliation,
    )
    profiles, _ = records["invocation-profiles.json"]
    _validate_invocation_profiles(profiles)
    if profiles != build_invocation_profiles():
        raise Refusal("invocation profile fixture is stale")
    manifest, _ = records["corpus-manifest.json"]
    _validate_manifest_shape(manifest, profiles)
    if manifest != build_manifest(profiles):
        raise Refusal("loader manifest is stale")
    expected = build_loader_graph(manifest, profiles)
    graph, raw = _verify_loaded(
        *records["loader-graph.json"], expected, "loader graph"
    )
    _validate_loader_graph(graph, manifest, profiles)
    paths = {item["path"] for item in manifest["documents"]}
    for edge in [*graph["edges"], *graph["scenario_edges"]]:
        if edge["source"] not in paths or edge["target"] not in paths:
            raise Refusal("loader graph escapes the manifest")
    evidence_records = [
        relation["evidence"]
        for relation in [
            *graph["roots"],
            *graph["edges"],
            *graph["scenario_roots"],
            *graph["scenario_edges"],
            *graph["excluded_links"],
        ]
    ]
    evidence_records.extend(
        relation["source_evidence"] for relation in graph["reference_only"]
    )
    evidence_records.extend(
        relation["runtime_evidence"]
        for relation in [*graph["edges"], *graph["scenario_edges"]]
        if relation["runtime_evidence"] is not None
    )
    for evidence in evidence_records:
        data = _source_blob(evidence["path"])
        span = data[evidence["start"] : evidence["end"]]
        if (
            _sha256(data) != evidence["source_sha256"]
            or _sha256(span) != evidence["span_sha256"]
        ):
            raise Refusal("loader evidence digest mismatch")
    return _result(
        "verify-loader",
        raw,
        {
            "roots": len(graph["roots"]),
            "edges": len(graph["edges"]),
            "scenario_roots": len(graph["scenario_roots"]),
            "scenario_edges": len(graph["scenario_edges"]),
        },
    )


def verify_profiles(args: argparse.Namespace) -> bytes:
    requested = {"invocation-profiles.json": args.profiles}
    if args.manifest is not None:
        requested["corpus-manifest.json"] = args.manifest
    records = _load_committed_baseline(requested, args.reconciliation)
    expected = build_invocation_profiles()
    profiles, raw = _verify_loaded(
        *records["invocation-profiles.json"], expected, "invocation profiles"
    )
    _validate_invocation_profiles(profiles)
    if args.manifest is not None:
        manifest, _ = records["corpus-manifest.json"]
        _validate_manifest_shape(manifest, profiles)
        if manifest != build_manifest(profiles):
            raise Refusal("profile manifest is stale")
    return _result("verify-profiles", raw, profiles["totals"])


def verify_partition(args: argparse.Namespace) -> bytes:
    records = _load_committed_baseline(
        {
            "byte-partition.json": args.partition,
            "corpus-manifest.json": args.manifest,
            "invocation-profiles.json": args.profiles,
        },
        args.reconciliation,
    )
    profiles, _ = records["invocation-profiles.json"]
    _validate_invocation_profiles(profiles)
    manifest, _ = records["corpus-manifest.json"]
    _validate_manifest_shape(manifest, profiles)
    if manifest != build_manifest(profiles):
        raise Refusal("partition manifest is stale")
    expected = build_partition(manifest)
    partition, raw = _verify_loaded(
        *records["byte-partition.json"], expected, "byte partition"
    )
    _validate_partition_closure(partition, manifest)
    if partition["unsupported_operative_bytes"] != 0:
        raise Refusal("unsupported operative bytes block selection")
    return _result("verify-partition", raw, partition["totals"])


def verify_seal(args: argparse.Namespace) -> bytes:
    records = _load_committed_baseline(
        {
            "cohorts.json": args.cohorts,
            "corpus-manifest.json": args.manifest,
            "holdout-seal.json": args.seal,
            "invocation-profiles.json": args.profiles,
        },
        args.reconciliation,
    )
    profiles, _ = records["invocation-profiles.json"]
    _validate_invocation_profiles(profiles)
    manifest, _ = records["corpus-manifest.json"]
    _validate_manifest_shape(manifest, profiles)
    if manifest != build_manifest(profiles):
        raise Refusal("seal manifest is stale")
    expected_cohorts = build_cohorts(manifest)
    cohorts, _ = _verify_loaded(
        *records["cohorts.json"], expected_cohorts, "cohorts"
    )
    graph = build_loader_graph(manifest, profiles)
    _verify_loaded(
        *records["loader-graph.json"], graph, "loader graph"
    )
    expected_seal = build_holdout_seal(manifest, cohorts, profiles, graph)
    seal, raw = _verify_loaded(
        *records["holdout-seal.json"], expected_seal, "holdout seal"
    )
    _validate_holdout_seal(seal, manifest, cohorts, profiles, graph)
    return _result(
        "verify-seal",
        raw,
        {
            "development_skills": len(cohorts["development"]["logical_skills"]),
            "holdout_skills": len(cohorts["holdout"]["logical_skills"]),
            "holdout_case_slots": len(cohorts["holdout"]["case_slots"]),
        },
    )


def _safe_output(path: Path) -> Path:
    relative = _repository_relative(path, "output")
    parent, name = _open_parent(relative, create=True, label="output")
    try:
        try:
            metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            metadata = None
        except OSError as exc:
            raise Refusal("output target is unavailable or unsafe") from exc
        if metadata is not None and not stat.S_ISREG(metadata.st_mode):
            raise Refusal("output target is not an ordinary file")
    finally:
        os.close(parent)
    return ROOT / Path(*relative.parts)


def _fresh_named_identity(
    relative: PurePosixPath, parent_identity: tuple[int, ...], expected: os.stat_result
) -> None:
    flags = _regular_read_flags()
    parent, name = _open_parent(relative, create=False, label="output")
    try:
        if _directory_identity(os.fstat(parent)) != parent_identity:
            raise Refusal("output parent changed during publication")
        try:
            descriptor = os.open(name, flags, dir_fd=parent)
        except OSError as exc:
            raise Refusal("output changed during publication") from exc
        try:
            if _identity(os.fstat(descriptor)) != _identity(expected):
                raise Refusal("output changed during publication")
        finally:
            os.close(descriptor)
    finally:
        os.close(parent)


def _atomic_write(path: Path, data: bytes) -> None:
    path = _safe_output(path)
    relative = _repository_relative(path, "output")
    parent, name = _open_parent(relative, create=True, label="output")
    parent_identity = _directory_identity(os.fstat(parent))
    temporary: str | None = None
    try:
        descriptor = -1
        for _ in range(32):
            candidate = f".{name}.{secrets.token_hex(16)}"
            try:
                descriptor = os.open(
                    candidate,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                    0o644,
                    dir_fd=parent,
                )
                temporary = candidate
                break
            except FileExistsError:
                continue
            except OSError as exc:
                raise Refusal("output stage is unavailable or unsafe") from exc
        if temporary is None or descriptor < 0:
            raise Refusal("could not allocate an output stage")
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
            staged = os.fstat(handle.fileno())
            if not stat.S_ISREG(staged.st_mode) or staged.st_nlink != 1:
                raise Refusal("output stage is not a single-link regular file")
        try:
            named_stage = os.open(temporary, _regular_read_flags(), dir_fd=parent)
        except OSError as exc:
            raise Refusal("output stage changed before publication") from exc
        try:
            if _identity(os.fstat(named_stage)) != _identity(staged):
                raise Refusal("output stage changed before publication")
        finally:
            os.close(named_stage)
        routed_parent, _ = _open_parent(relative, create=False, label="output")
        try:
            if _directory_identity(os.fstat(routed_parent)) != parent_identity:
                raise Refusal("output parent changed before publication")
        finally:
            os.close(routed_parent)
        os.replace(
            temporary,
            name,
            src_dir_fd=parent,
            dst_dir_fd=parent,
        )
        temporary = None
        os.fsync(parent)
        try:
            published = os.open(name, _regular_read_flags(), dir_fd=parent)
        except OSError as exc:
            raise Refusal("published output is unavailable or unsafe") from exc
        try:
            reread, published_stat = _read_descriptor(
                published, max(MAX_JSON_BYTES, len(data))
            )
        finally:
            os.close(published)
        if _rename_stable_identity(published_stat) != _rename_stable_identity(staged):
            raise Refusal("published output does not match the verified stage")
        if reread != data:
            raise Refusal("published output failed reread")
        _fresh_named_identity(relative, parent_identity, published_stat)
    finally:
        if temporary is not None:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
        os.close(parent)


def _existing_output_bytes(path: Path, limit: int) -> bytes | None:
    """Read an already published target without following any path component."""
    relative = _repository_relative(path, "output")
    parent, name = _open_parent(relative, create=False, label="output")
    try:
        try:
            descriptor = os.open(name, _regular_read_flags(), dir_fd=parent)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise Refusal("existing output is unavailable or unsafe") from exc
        try:
            raw, opened = _read_descriptor(descriptor, limit)
        finally:
            os.close(descriptor)
        try:
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
        except OSError as exc:
            raise Refusal("existing output changed during read") from exc
        if _identity(opened) != _identity(named):
            raise Refusal("existing output changed during read")
        return raw
    finally:
        os.close(parent)


def _publish_committed_set(
    ordered: list[tuple[Path, bytes]], *, terminal: Path
) -> None:
    """Publish payloads first and one external commitment as the last marker.

    An interrupted run may resume only when every previously published byte is
    exactly the byte planned now.  Once the terminal marker exists, the set is
    immutable and must already be complete.
    """
    if not ordered or ordered[-1][0] != terminal:
        raise Refusal("commitment marker is not the final publication")
    paths = [path for path, _ in ordered]
    if len(paths) != len(set(paths)):
        raise Refusal("committed publication contains duplicate targets")
    for path in paths:
        _safe_output(path)
    observed = {
        path: _existing_output_bytes(path, max(MAX_JSON_BYTES, len(raw)))
        for path, raw in ordered
    }
    for path, expected in ordered:
        actual = observed[path]
        if actual is not None and actual != expected:
            raise Refusal("interrupted committed publication contains stale bytes")
    if observed[terminal] is not None:
        if any(observed[path] is None for path in paths):
            raise Refusal("terminal commitment exists for an incomplete publication")
        return
    for path, raw in ordered:
        if observed[path] is None:
            _atomic_write(path, raw)
    for path, raw in ordered:
        if _existing_output_bytes(path, max(MAX_JSON_BYTES, len(raw))) != raw:
            raise Refusal("committed publication failed final verification")


# Step 2 keeps evaluator semantics outside every adapter.  This same contract
# is copied into each arm record so neither historical IR becomes the host.
NEUTRAL_CONTRACT = {
    "authority": "exact-canonical-source-bytes-at-source-ref",
    "case_semantics": "exact-source-span",
    "fallback": "exact-current-source-counted-as-not-native",
    "prompt": "task-plus-representation-without-oracle-or-arm-label",
    "score": "exact-source-recovery-and-native-mechanism",
}


def _git_blob_oid(data: bytes, object_format: str = "sha1") -> str:
    """Compute the repository-format Git identity for exact blob bytes."""
    header = f"blob {len(data)}\0".encode("ascii")
    if object_format == "sha1":
        hasher = hashlib.sha1(usedforsecurity=False)
    elif object_format == "sha256":
        hasher = hashlib.sha256()
    else:
        raise Refusal("control snapshot object format is unsupported")
    hasher.update(header)
    hasher.update(data)
    return hasher.hexdigest()


@lru_cache(maxsize=4)
def _control_ref_mode(ref: str) -> str:
    """Require a typed commit or its exact absence in a shallow repository."""
    if re.fullmatch(r"[0-9a-f]{40}", ref) is None:
        raise Refusal("control ref is not an exact commit id")
    expression = f"{ref}^{{commit}}"
    probe = _git(
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        128,
        input_data=f"{expression}\n".encode("ascii"),
    )
    if probe == f"{ref} commit\n".encode("ascii"):
        return "git"
    if probe != f"{expression} missing\n".encode("ascii"):
        raise Refusal("bounded Git read returned an unexpected control identity")
    shallow = _git(["rev-parse", "--is-shallow-repository"], 16)
    if shallow != b"true\n":
        raise Refusal("control commit is absent from a non-shallow repository")
    return "snapshot"


def _git_control_paths(ref: str, prefixes: tuple[str, ...]) -> list[str]:
    if _control_ref_mode(ref) != "git":
        raise Refusal("control snapshot generation requires the pinned commit")
    if not prefixes:
        raise Refusal("control inventory has no admitted prefixes")
    for prefix in prefixes:
        _safe_relative(prefix)
    raw = _git(
        ["ls-tree", "-r", "-z", "--name-only", ref, "--", *prefixes],
        2 * 1024 * 1024,
    )
    if not raw or not raw.endswith(b"\0") or raw.startswith(b"\0") or b"\0\0" in raw:
        raise Refusal("control tree inventory is malformed")
    try:
        paths = [part.decode("utf-8", errors="strict") for part in raw[:-1].split(b"\0")]
    except UnicodeDecodeError as exc:
        raise Refusal("control tree path is not UTF-8") from exc
    if paths != sorted(set(paths)) or len(paths) > MAX_CONTROL_PATHS:
        raise Refusal("control tree inventory is unordered, duplicated, or oversized")
    for path in paths:
        _safe_relative(path)
        if not any(
            path == prefix or path.startswith(prefix.rstrip("/") + "/")
            for prefix in prefixes
        ):
            raise Refusal("control tree escaped its admitted prefixes")
    return paths


def _git_blob_identity_at(ref: str, path: str) -> str:
    _safe_relative(path)
    expression = f"{ref}:{path}"
    probe = _git(
        ["cat-file", "--batch-check=%(objectname) %(objecttype)"],
        128,
        input_data=f"{expression}\n".encode("ascii"),
    )
    match = re.fullmatch(rb"([0-9a-f]{40}) blob\n", probe)
    if match is None:
        raise Refusal("control commit path does not resolve to a typed blob")
    return match.group(1).decode("ascii")


def _control_snapshot_manifest(
    artifacts: list[dict[str, Any]], objects: dict[str, bytes]
) -> dict[str, Any]:
    return {
        "artifacts": artifacts,
        "object_format": "sha1",
        "objects": [
            {
                "bytes": len(objects[oid]),
                "oid": oid,
                "sha256": _sha256(objects[oid]),
            }
            for oid in sorted(objects)
        ],
        "schema": f"{SCHEMA_PREFIX}-control-snapshot/v1",
        "totals": {
            "artifact_records": len(artifacts),
            "object_bytes": sum(len(data) for data in objects.values()),
            "objects": len(objects),
        },
    }


def _snapshot_entries(descriptor: int, label: str, limit: int) -> list[str]:
    entries: list[str] = []
    seen: set[str] = set()
    try:
        with os.scandir(descriptor) as iterator:
            for entry in iterator:
                if len(entries) >= limit:
                    raise Refusal(f"{label} inventory exceeds its bound")
                if entry.name in seen:
                    raise Refusal(f"{label} inventory is duplicated")
                entries.append(entry.name)
                seen.add(entry.name)
    except OSError as exc:
        raise Refusal(f"{label} inventory is unavailable") from exc
    return entries


def _snapshot_regular_identity(
    descriptor: int, name: str, label: str
) -> tuple[int, ...]:
    try:
        metadata = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except OSError as exc:
        raise Refusal(f"{label} entry is unavailable or unsafe") from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise Refusal(f"{label} entry is not a single-link regular file")
    return _identity(metadata)


def _snapshot_read_entry(
    descriptor: int, name: str, limit: int, label: str
) -> tuple[bytes, tuple[int, ...]]:
    try:
        entry = os.open(name, _regular_read_flags(), dir_fd=descriptor)
    except OSError as exc:
        raise Refusal(f"{label} entry is unavailable or unsafe") from exc
    try:
        data, metadata = _read_descriptor(entry, limit)
    finally:
        os.close(entry)
    return data, _identity(metadata)


def _open_snapshot_directories(
    root: PurePosixPath, *, create: bool, exact_root: bool
) -> tuple[int, int]:
    """Open the snapshot root and object store without following path changes."""
    directory, _ = _open_parent(
        root / ".entry", create=create, label="control snapshot root"
    )
    objects = -1
    try:
        expected = {"manifest.json", "objects"}
        entries = set(_snapshot_entries(directory, "control snapshot root", 2))
        if (exact_root and entries != expected) or (
            not exact_root and not entries <= expected
        ):
            raise Refusal("control snapshot root directory is not closed")
        if "manifest.json" in entries:
            _snapshot_regular_identity(
                directory, "manifest.json", "control snapshot manifest"
            )
        if "objects" not in entries:
            if not create:
                raise Refusal("control snapshot root directory is not closed")
            try:
                os.mkdir("objects", mode=0o755, dir_fd=directory)
            except OSError as exc:
                raise Refusal("control snapshot object directory is unavailable") from exc
        try:
            objects = os.open("objects", _directory_flags(), dir_fd=directory)
        except OSError as exc:
            raise Refusal("control snapshot object directory is unavailable or unsafe") from exc
        final_entries = set(_snapshot_entries(directory, "control snapshot root", 2))
        if (exact_root and final_entries != expected) or (
            not exact_root and not final_entries <= expected
        ):
            raise Refusal("control snapshot root directory is not closed")
        return directory, objects
    except BaseException:
        if objects >= 0:
            os.close(objects)
        os.close(directory)
        raise


def _preflight_snapshot_publication(
    output: PurePosixPath, object_names: set[str]
) -> tuple[int, int]:
    """Admit only an empty, partial, or complete instance of this generation."""
    directory, objects = _open_snapshot_directories(
        output, create=True, exact_root=False
    )
    try:
        entries = set(
            _snapshot_entries(objects, "control snapshot object", len(object_names))
        )
        if not entries <= object_names:
            raise Refusal("control snapshot object directory contains an unowned entry")
        for name in entries:
            _snapshot_regular_identity(objects, name, "control snapshot object")
        return directory, objects
    except BaseException:
        os.close(objects)
        os.close(directory)
        raise


def _verify_snapshot_publication(
    output: PurePosixPath,
    directory: int,
    object_directory: int,
    manifest: bytes,
    objects: dict[str, bytes],
) -> None:
    """Re-read one complete generation and bind it to the preflight directories."""
    expected_objects = set(objects)
    directory_before = os.fstat(directory)
    objects_before = os.fstat(object_directory)
    if set(_snapshot_entries(directory, "control snapshot root", 2)) != {
        "manifest.json",
        "objects",
    }:
        raise Refusal("control snapshot root directory is not closed")
    if (
        set(
            _snapshot_entries(
                object_directory, "control snapshot object", len(expected_objects)
            )
        )
        != expected_objects
    ):
        raise Refusal("control snapshot object directory differs from its manifest")
    manifest_read, manifest_identity = _snapshot_read_entry(
        directory, "manifest.json", MAX_JSON_BYTES, "control snapshot manifest"
    )
    if manifest_read != manifest:
        raise Refusal("published control snapshot manifest drift")
    object_identities: dict[str, tuple[int, ...]] = {}
    for oid in sorted(objects):
        data, identity = _snapshot_read_entry(
            object_directory, oid, MAX_SOURCE_BYTES, "control snapshot object"
        )
        if data != objects[oid]:
            raise Refusal("published control snapshot object drift")
        object_identities[oid] = identity
    if (
        set(_snapshot_entries(directory, "control snapshot root", 2))
        != {"manifest.json", "objects"}
        or set(
            _snapshot_entries(
                object_directory, "control snapshot object", len(expected_objects)
            )
        )
        != expected_objects
        or _identity(os.fstat(directory)) != _identity(directory_before)
        or _identity(os.fstat(object_directory)) != _identity(objects_before)
        or _snapshot_regular_identity(
            directory, "manifest.json", "control snapshot manifest"
        )
        != manifest_identity
        or any(
            _snapshot_regular_identity(
                object_directory, oid, "control snapshot object"
            )
            != object_identities[oid]
            for oid in object_identities
        )
    ):
        raise Refusal("control snapshot publication changed during verification")
    routed_directory, routed_objects = _open_snapshot_directories(
        output, create=False, exact_root=True
    )
    try:
        if (
            _directory_identity(os.fstat(routed_directory))
            != _directory_identity(directory_before)
            or _directory_identity(os.fstat(routed_objects))
            != _directory_identity(objects_before)
            or set(
                _snapshot_entries(
                    routed_objects, "control snapshot object", len(expected_objects)
                )
            )
            != expected_objects
        ):
            raise Refusal("control snapshot publication path changed")
    finally:
        os.close(routed_objects)
        os.close(routed_directory)


def snapshot_controls(args: argparse.Namespace) -> bytes:
    """Materialise immutable control objects while every pinned ref is present."""
    output = _confined_output(
        args.output,
        "control snapshot output",
        exact=(CONTROL_SNAPSHOT_ROOT,),
        roots=(SCRATCH_ROOT,),
    )
    object_format = _git(["rev-parse", "--show-object-format"], 16)
    if object_format != b"sha1\n":
        raise Refusal("control refs require a SHA-1 object-format repository")
    artifacts: list[dict[str, Any]] = []
    objects: dict[str, bytes] = {}
    for ref, prefixes in CONTROL_SNAPSHOT_GROUPS:
        for path in _git_control_paths(ref, prefixes):
            oid = _git_blob_identity_at(ref, path)
            data = _git(["cat-file", "blob", oid], MAX_SOURCE_BYTES)
            if _git_blob_oid(data) != oid:
                raise Refusal("Git returned control bytes with another blob identity")
            existing = objects.get(oid)
            if existing is not None and existing != data:
                raise Refusal("two control objects share an identity but not bytes")
            objects[oid] = data
            artifacts.append(
                {
                    "blob_oid": oid,
                    "bytes": len(data),
                    "path": path,
                    "ref": ref,
                    "sha256": _sha256(data),
                }
            )
    artifacts.sort(key=lambda item: (item["ref"], item["path"]))
    manifest = _control_snapshot_manifest(artifacts, objects)
    if manifest["totals"] != EXPECTED_CONTROL_SNAPSHOT_COUNTS:
        raise Refusal("control snapshot resource totals drift")
    manifest_bytes = _canonical_json(manifest)
    relative_output = _repository_relative(output, "control snapshot output")
    if (
        relative_output == CONTROL_SNAPSHOT_ROOT
        and EXPECTED_CONTROL_SNAPSHOT_SHA256 is not None
        and _sha256(manifest_bytes) != EXPECTED_CONTROL_SNAPSHOT_SHA256
    ):
        raise Refusal("control snapshot manifest differs from its frozen digest")
    directory, object_directory = _preflight_snapshot_publication(
        relative_output, set(objects)
    )
    try:
        for oid in sorted(objects):
            _atomic_write(output / "objects" / oid, objects[oid])
        _atomic_write(output / "manifest.json", manifest_bytes)
        _verify_snapshot_publication(
            relative_output,
            directory,
            object_directory,
            manifest_bytes,
            objects,
        )
    finally:
        os.close(object_directory)
        os.close(directory)
    return _result(
        "snapshot-controls",
        manifest_bytes,
        dict(EXPECTED_CONTROL_SNAPSHOT_COUNTS),
    )


@lru_cache(maxsize=1)
def _control_snapshot() -> dict[str, Any]:
    snapshot_directory, snapshot_objects = _open_snapshot_directories(
        CONTROL_SNAPSHOT_ROOT, create=False, exact_root=True
    )
    os.close(snapshot_objects)
    os.close(snapshot_directory)
    manifest_path = ROOT / Path(*CONTROL_SNAPSHOT_MANIFEST.parts)
    raw = _read_regular(manifest_path, MAX_JSON_BYTES)
    if (
        not isinstance(EXPECTED_CONTROL_SNAPSHOT_SHA256, str)
        or re.fullmatch(r"[0-9a-f]{64}", EXPECTED_CONTROL_SNAPSHOT_SHA256) is None
        or _sha256(raw) != EXPECTED_CONTROL_SNAPSHOT_SHA256
    ):
        raise Refusal("control snapshot manifest differs from its frozen digest")
    manifest = _decode_record(raw)
    _require_fields(
        manifest,
        ("artifacts", "object_format", "objects", "schema", "totals"),
        ("artifacts", "object_format", "objects", "schema", "totals"),
        "control snapshot manifest",
    )
    if (
        manifest["schema"] != f"{SCHEMA_PREFIX}-control-snapshot/v1"
        or manifest["object_format"] != "sha1"
        or not isinstance(manifest["artifacts"], list)
        or not isinstance(manifest["objects"], list)
        or manifest["totals"] != EXPECTED_CONTROL_SNAPSHOT_COUNTS
        or len(manifest["artifacts"])
        != EXPECTED_CONTROL_SNAPSHOT_COUNTS["artifact_records"]
        or len(manifest["objects"]) != EXPECTED_CONTROL_SNAPSHOT_COUNTS["objects"]
    ):
        raise Refusal("control snapshot manifest identity or totals drift")

    object_records: dict[str, dict[str, Any]] = {}
    object_order: list[str] = []
    for record in manifest["objects"]:
        _require_fields(
            record, ("bytes", "oid", "sha256"), ("bytes", "oid", "sha256"),
            "control snapshot object",
        )
        oid = record["oid"]
        size = record["bytes"]
        digest = record["sha256"]
        if (
            not isinstance(oid, str)
            or re.fullmatch(r"[0-9a-f]{40}", oid) is None
            or type(size) is not int
            or not 0 < size <= MAX_SOURCE_BYTES
            or not isinstance(digest, str)
            or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or oid in object_records
        ):
            raise Refusal("control snapshot object identity is malformed")
        object_records[oid] = record
        object_order.append(oid)
    if object_order != sorted(object_order):
        raise Refusal("control snapshot objects are not canonically ordered")

    object_directory = CONTROL_SNAPSHOT_ROOT / "objects"
    directory, _ = _open_parent(
        object_directory / ".entry", create=False, label="control snapshot objects"
    )
    object_bytes: dict[str, bytes] = {}
    try:
        directory_before = os.fstat(directory)
        entries_before = _snapshot_entries(
            directory, "control snapshot object", len(object_records)
        )
        if (
            len(entries_before) != len(object_records)
            or set(entries_before) != set(object_records)
        ):
            raise Refusal("control snapshot object directory differs from its manifest")
        for oid, record in object_records.items():
            data = _read_regular(
                ROOT / Path(*(object_directory / oid).parts), MAX_SOURCE_BYTES
            )
            if (
                len(data) != record["bytes"]
                or _sha256(data) != record["sha256"]
                or _git_blob_oid(data, manifest["object_format"]) != oid
            ):
                raise Refusal(
                    "control snapshot object size, digest, or blob identity drift"
                )
            object_bytes[oid] = data
        entries_after = _snapshot_entries(
            directory, "control snapshot object", len(object_records)
        )
        if (
            sorted(entries_after) != sorted(entries_before)
            or _identity(os.fstat(directory)) != _identity(directory_before)
        ):
            raise Refusal("control snapshot object inventory changed")
    finally:
        os.close(directory)

    prefixes_by_ref = {ref: prefixes for ref, prefixes in CONTROL_SNAPSHOT_GROUPS}
    artifacts: dict[tuple[str, str], dict[str, Any]] = {}
    artifact_order: list[tuple[str, str]] = []
    for record in manifest["artifacts"]:
        _require_fields(
            record,
            ("blob_oid", "bytes", "path", "ref", "sha256"),
            ("blob_oid", "bytes", "path", "ref", "sha256"),
            "control snapshot artifact",
        )
        ref = record["ref"]
        path = record["path"]
        oid = record["blob_oid"]
        prefixes = prefixes_by_ref.get(ref)
        if (
            prefixes is None
            or not isinstance(path, str)
            or not isinstance(oid, str)
            or re.fullmatch(r"[0-9a-f]{40}", oid) is None
        ):
            raise Refusal("control snapshot artifact identity is malformed")
        _safe_relative(path)
        if not any(
            path == prefix or path.startswith(prefix.rstrip("/") + "/")
            for prefix in prefixes
        ):
            raise Refusal("control snapshot artifact escaped its admitted prefixes")
        key = (ref, path)
        source = object_records.get(oid)
        if (
            key in artifacts
            or source is None
            or record["bytes"] != source["bytes"]
            or record["sha256"] != source["sha256"]
        ):
            raise Refusal("control snapshot artifact binding drift")
        artifacts[key] = record
        artifact_order.append(key)
    if artifact_order != sorted(artifact_order):
        raise Refusal("control snapshot artifacts are not canonically ordered")
    if set(object_records) != {record["blob_oid"] for record in artifacts.values()}:
        raise Refusal("control snapshot contains an unreferenced or absent object")
    if sum(len(data) for data in object_bytes.values()) != EXPECTED_CONTROL_SNAPSHOT_COUNTS[
        "object_bytes"
    ]:
        raise Refusal("control snapshot object byte total drift")
    if _read_regular(manifest_path, MAX_JSON_BYTES) != raw:
        raise Refusal("control snapshot manifest changed during verification")
    snapshot_directory, snapshot_objects = _open_snapshot_directories(
        CONTROL_SNAPSHOT_ROOT, create=False, exact_root=True
    )
    try:
        _verify_snapshot_publication(
            CONTROL_SNAPSHOT_ROOT,
            snapshot_directory,
            snapshot_objects,
            raw,
            object_bytes,
        )
    finally:
        os.close(snapshot_objects)
        os.close(snapshot_directory)
    return {
        "artifacts": artifacts,
        "manifest": manifest,
        "manifest_bytes": raw,
        "objects": object_bytes,
    }


@lru_cache(maxsize=512)
def _git_blob_at(ref: str, path: str) -> bytes:
    _safe_relative(path)
    snapshot = _control_snapshot()
    record = snapshot["artifacts"].get((ref, path))
    if record is None:
        raise Refusal("control artifact is absent from the checked snapshot")
    data = snapshot["objects"][record["blob_oid"]]
    if _control_ref_mode(ref) == "git":
        observed_oid = _git_blob_identity_at(ref, path)
        if observed_oid != record["blob_oid"]:
            raise Refusal("control commit path differs from its snapshot blob identity")
        if _git(["cat-file", "blob", observed_oid], MAX_SOURCE_BYTES) != data:
            raise Refusal("control Git bytes differ from the checked snapshot")
    return data


def _control_paths_at(ref: str, prefixes: tuple[str, ...]) -> list[str]:
    if not prefixes:
        raise Refusal("control inventory has no admitted prefixes")
    for prefix in prefixes:
        _safe_relative(prefix)
    snapshot_paths = sorted(
        path
        for (artifact_ref, path) in _control_snapshot()["artifacts"]
        if artifact_ref == ref
        and any(
            path == prefix or path.startswith(prefix.rstrip("/") + "/")
            for prefix in prefixes
        )
    )
    if not snapshot_paths or len(snapshot_paths) > MAX_CONTROL_PATHS:
        raise Refusal("control snapshot inventory is empty or oversized")
    if _control_ref_mode(ref) == "git":
        git_paths = _git_control_paths(ref, prefixes)
        if git_paths != snapshot_paths:
            raise Refusal("control commit inventory differs from its checked snapshot")
    return snapshot_paths


def _control_inventory(
    ref: str,
    prefixes: tuple[str, ...],
    *,
    require_live_match: bool,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in _control_paths_at(ref, prefixes):
        data = _git_blob_at(ref, path)
        snapshot = _control_snapshot()["artifacts"][(ref, path)]
        if require_live_match:
            live = _read_regular(
                ROOT / Path(*PurePosixPath(path).parts), MAX_SOURCE_BYTES
            )
            if live != data:
                raise Refusal(f"immutable control differs from its entry bytes: {path}")
        records.append(
            {
                "blob_oid": snapshot["blob_oid"],
                "bytes": len(data),
                "path": path,
                "ref": ref,
                "sha256": _sha256(data),
            }
        )
    return records


def _range_record(
    document: dict[str, Any],
    data: bytes,
    start: int,
    end: int,
    mode: str,
    reason: str,
    representation_id: str,
) -> dict[str, Any]:
    if (
        type(start) is not int
        or type(end) is not int
        or start < 0
        or end <= start
        or end > len(data)
        or mode not in {"native", "raw-fallback"}
    ):
        raise Refusal("adapter range is malformed")
    if mode == "native" and reason:
        raise Refusal("native adapter range carries a fallback reason")
    if mode == "raw-fallback" and not reason:
        raise Refusal("fallback adapter range has no reason")
    span = data[start:end]
    return {
        "bytes": len(span),
        "end": end,
        "mode": mode,
        "path": document["path"],
        "reason": reason,
        "representation_id": representation_id,
        "sha256": _sha256(span),
        "start": start,
    }


def _coverage_summary(
    manifest: dict[str, Any], ranges: list[dict[str, Any]]
) -> dict[str, int]:
    by_path: dict[str, list[dict[str, Any]]] = {}
    for item in ranges:
        by_path.setdefault(item["path"], []).append(item)
    documents = {item["path"]: item for item in manifest["documents"]}
    if set(by_path) != set(documents):
        raise Refusal("adapter coverage does not name the complete corpus")
    native_files = fallback_files = native_bytes = fallback_bytes = 0
    for path, document in documents.items():
        data = _source_blob(path)
        rows = sorted(by_path[path], key=lambda item: (item["start"], item["end"]))
        cursor = 0
        modes: set[str] = set()
        for row in rows:
            if row["start"] != cursor or row["end"] > len(data):
                raise Refusal(f"adapter coverage has a gap or overlap: {path}")
            if (
                row["bytes"] != row["end"] - row["start"]
                or row["sha256"] != _sha256(data[row["start"] : row["end"]])
            ):
                raise Refusal(f"adapter coverage digest drift: {path}")
            cursor = row["end"]
            modes.add(row["mode"])
            if row["mode"] == "native":
                native_bytes += row["bytes"]
            else:
                fallback_bytes += row["bytes"]
        if cursor != document["bytes"] or len(data) != document["bytes"]:
            raise Refusal(f"adapter coverage does not recover source bytes: {path}")
        native_files += "native" in modes
        fallback_files += "raw-fallback" in modes

    canonical_paths = {
        item["path"]
        for item in manifest["documents"]
        if item["path"] == item["canonical_content_path"]
    }
    unique_native_files = unique_fallback_files = 0
    unique_native_bytes = unique_fallback_bytes = 0
    for path in canonical_paths:
        modes = {item["mode"] for item in by_path[path]}
        unique_native_files += "native" in modes
        unique_fallback_files += "raw-fallback" in modes
        for item in by_path[path]:
            if item["mode"] == "native":
                unique_native_bytes += item["bytes"]
            else:
                unique_fallback_bytes += item["bytes"]
    summary = {
        "fallback_physical_bytes": fallback_bytes,
        "fallback_physical_files": fallback_files,
        "fallback_ranges": sum(item["mode"] == "raw-fallback" for item in ranges),
        "fallback_unique_bytes": unique_fallback_bytes,
        "fallback_unique_files": unique_fallback_files,
        "native_physical_bytes": native_bytes,
        "native_physical_files": native_files,
        "native_ranges": sum(item["mode"] == "native" for item in ranges),
        "native_unique_bytes": unique_native_bytes,
        "native_unique_files": unique_native_files,
        "physical_bytes": manifest["totals"]["physical_bytes"],
        "physical_files": manifest["totals"]["physical_files"],
        "unique_bytes": manifest["totals"]["unique_bytes"],
        "unique_files": manifest["totals"]["unique_files"],
    }
    if (
        native_bytes + fallback_bytes != summary["physical_bytes"]
        or unique_native_bytes + unique_fallback_bytes != summary["unique_bytes"]
    ):
        raise Refusal("adapter coverage denominators do not reconcile")
    return summary


def _coverage(
    manifest: dict[str, Any], ranges: list[dict[str, Any]]
) -> dict[str, Any]:
    ranges.sort(key=lambda item: (item["path"], item["start"], item["end"]))
    return {"ranges": ranges, "summary": _coverage_summary(manifest, ranges)}


def _base_control(
    arm: str,
    manifest: dict[str, Any],
    ranges: list[dict[str, Any]],
    *,
    binding_kind: str,
    product_ref: str,
    review_ref: str | None,
    artifacts: list[dict[str, Any]],
    checker: dict[str, Any] | None,
    native_mappings: list[dict[str, Any]],
    graph: dict[str, Any],
    mechanism_evidence: dict[str, Any],
) -> dict[str, Any]:
    if arm not in DEVELOPMENT_ARMS:
        raise Refusal("unknown development arm")
    binding_body = {
        "artifacts": artifacts,
        "kind": binding_kind,
        "product_ref": product_ref,
        "review_ref": review_ref,
    }
    control = {
        "arm": arm,
        "binding": {
            **binding_body,
            "artifacts_sha256": _sha256(_canonical_json(binding_body)),
            "checker": checker,
        },
        "claims": {
            "candidate_defines_semantics": False,
            "fallback_is_aggregate_success": False,
            "fallback_is_native_coverage": False,
            "full_source_trace_required": True,
            "round_trip_scope": "exact-source-bytes",
        },
        "contract": dict(NEUTRAL_CONTRACT),
        "coverage": _coverage(manifest, ranges),
        "graph": graph,
        "manifest_sha256": _artifact_digest(manifest),
        "mechanism_evidence": mechanism_evidence,
        "native_mappings": native_mappings,
        "schema": f"{SCHEMA_PREFIX}-control/v1",
        "source_ref": SOURCE_REF,
    }
    expected = EXPECTED_CONTROL_SHA256.get(arm)
    if expected is not None and _artifact_digest(control) != expected:
        raise Refusal(f"immutable {arm} control digest drift")
    return control


def _raw_control(manifest: dict[str, Any]) -> dict[str, Any]:
    ranges: list[dict[str, Any]] = []
    for document in manifest["documents"]:
        data = _source_blob(document["path"])
        ranges.append(
            _range_record(
                document, data, 0, len(data), "native", "", f"raw:{document['sha256']}"
            )
        )
    return _base_control(
        "raw",
        manifest,
        ranges,
        binding_kind="verified-loader-source",
        product_ref=SOURCE_REF,
        review_ref=None,
        artifacts=[],
        checker=None,
        native_mappings=[],
        graph={"edges": [], "nodes": []},
        mechanism_evidence={
            "current_native_bytes": manifest["totals"]["physical_bytes"],
            "current_native_envelopes": len(ranges),
            "current_native_in_current_coverage": True,
            "scope": "current-corpus",
            "stale_sources": 0,
            "synthetic_in_aggregate_success": False,
            "synthetic_in_current_coverage": False,
            "synthetic_mapped_bytes": 0,
            "synthetic_mapped_spans": 0,
        },
    )


def _wai1_checker() -> tuple[list[dict[str, Any]], str]:
    checker_path = "scripts/agent_instruction.py"
    source = _git_blob_at(WAI1_CONTROL_REF, checker_path)
    namespace: dict[str, Any] = {
        "__file__": str(ROOT / checker_path),
        "__name__": "_framework74_pinned_wai1_checker",
        "__package__": None,
    }
    try:
        # phylax: allow exact merged WAI1 checker blob at its immutable Git ref
        exec(compile(source, f"{WAI1_CONTROL_REF}:{checker_path}", "exec"), namespace)
        records = namespace["check_manifest"](
            ROOT, "tests/fixtures/agent-instruction-v1/manifest.json"
        )
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise Refusal("pinned WAI1 checker refused its immutable fixtures") from exc
    fixture_ids = {
        item.get("fixture_id")
        for item in records
        if isinstance(item, dict) and isinstance(item.get("fixture_id"), str)
    } if isinstance(records, list) else set()
    if (
        not isinstance(records, list)
        or len(records) != 21
        or fixture_ids
        != {
            "fiat-study-runbook-phase",
            "horos-boundary-check",
            "promise-machine-router-selection",
        }
    ):
        raise Refusal("pinned WAI1 checker result cardinality drift")
    return records, _sha256(_canonical_json(records))


def _wai1_decoder_bootstrap() -> tuple[str, bytes]:
    manifest = _decode_record(
        _git_blob_at(WAI1_CONTROL_REF, "tests/fixtures/agent-instruction-v1/manifest.json")
    )
    evidence = manifest.get("evidence")
    if not isinstance(evidence, dict) or not isinstance(
        evidence.get("decoder_bootstrap"), dict
    ):
        raise Refusal("WAI1 decoder bootstrap binding is malformed")
    binding = evidence["decoder_bootstrap"]
    path = binding.get("path")
    if not isinstance(path, str):
        raise Refusal("WAI1 decoder bootstrap path is malformed")
    data = _git_blob_at(WAI1_CONTROL_REF, path)
    if (
        not data
        or len(data) > 4_096
        or not data.endswith(b"\n")
        or binding.get("sha256") != _sha256(data)
    ):
        raise Refusal("WAI1 decoder bootstrap digest or shape drift")
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Refusal("WAI1 decoder bootstrap is not UTF-8") from exc
    return path, data


def _wai1_control(manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts = _control_inventory(
        WAI1_CONTROL_REF, WAI1_CONTROL_PREFIXES, require_live_match=True
    )
    wai_manifest = _decode_record(
        _git_blob_at(WAI1_CONTROL_REF, "tests/fixtures/agent-instruction-v1/manifest.json")
    )
    fixtures = wai_manifest.get("fixtures")
    if not isinstance(fixtures, list) or len(fixtures) != 3:
        raise Refusal("WAI1 immutable manifest does not contain three envelopes")
    documents = {item["path"]: item for item in manifest["documents"]}
    native_by_path: dict[str, list[tuple[int, int, dict[str, Any]]]] = {}
    mappings: list[dict[str, Any]] = []
    for fixture in fixtures:
        if not isinstance(fixture, dict) or not isinstance(fixture.get("source"), dict):
            raise Refusal("WAI1 envelope source binding is malformed")
        source = fixture["source"]
        path = source.get("path")
        if path not in documents:
            raise Refusal("WAI1 envelope source is outside the current corpus")
        try:
            start = int(source["start"])
            end = int(source["end"])
        except (KeyError, TypeError, ValueError) as exc:
            raise Refusal("WAI1 envelope range is malformed") from exc
        data = _source_blob(path)
        compact = fixture.get("artifacts", {}).get("compact", {})
        compact_path = compact.get("path")
        if (
            source.get("sha256") != _sha256(data)
            or start < 0
            or end <= start
            or end > len(data)
            or source.get("span_sha256") != _sha256(data[start:end])
            or not isinstance(compact_path, str)
        ):
            raise Refusal("WAI1 current envelope source binding drift")
        compact_bytes = _git_blob_at(WAI1_CONTROL_REF, compact_path)
        if compact.get("sha256") != _sha256(compact_bytes):
            raise Refusal("WAI1 compact envelope digest drift")
        identifier = f"wai1:{fixture['id']}"
        mapping = {
            "end": end,
            "id": identifier,
            "path": path,
            "representation_bytes": len(compact_bytes),
            "representation_path": compact_path,
            "representation_sha256": _sha256(compact_bytes),
            "source_sha256": _sha256(data[start:end]),
            "start": start,
        }
        mappings.append(mapping)
        native_by_path.setdefault(path, []).append((start, end, mapping))
    mappings.sort(key=lambda item: item["id"])

    ranges: list[dict[str, Any]] = []
    for document in manifest["documents"]:
        data = _source_blob(document["path"])
        cursor = 0
        for start, end, mapping in sorted(native_by_path.get(document["path"], [])):
            if start < cursor:
                raise Refusal("WAI1 current envelope ranges overlap")
            if start > cursor:
                ranges.append(
                    _range_record(
                        document,
                        data,
                        cursor,
                        start,
                        "raw-fallback",
                        "unmapped-current-span",
                        f"raw:{document['sha256']}:{cursor}:{start}",
                    )
                )
            ranges.append(
                _range_record(document, data, start, end, "native", "", mapping["id"])
            )
            cursor = end
        if cursor < len(data):
            ranges.append(
                _range_record(
                    document,
                    data,
                    cursor,
                    len(data),
                    "raw-fallback",
                    "unmapped-current-span",
                    f"raw:{document['sha256']}:{cursor}:{len(data)}",
                )
            )
    records, checker_sha = _wai1_checker()
    bootstrap_path, bootstrap = _wai1_decoder_bootstrap()
    if not any(
        item["path"] == bootstrap_path
        and item["sha256"] == _sha256(bootstrap)
        and item["bytes"] == len(bootstrap)
        for item in artifacts
    ):
        raise Refusal("WAI1 decoder bootstrap is absent from the immutable inventory")
    control = _base_control(
        "wai1",
        manifest,
        ranges,
        binding_kind="merged-wai1-at-entry-ref",
        product_ref=WAI1_CONTROL_REF,
        review_ref=None,
        artifacts=artifacts,
        checker={
            "invoked": True,
            "record_count": len(records),
            "result_sha256": checker_sha,
            "status": "pass",
        },
        native_mappings=mappings,
        graph={"edges": [], "nodes": []},
        mechanism_evidence={
            "current_native_bytes": sum(item["end"] - item["start"] for item in mappings),
            "current_native_envelopes": len(mappings),
            "current_native_in_current_coverage": True,
            "scope": "current-corpus",
            "stale_sources": 0,
            "synthetic_in_aggregate_success": False,
            "synthetic_in_current_coverage": False,
            "synthetic_mapped_bytes": 0,
            "synthetic_mapped_spans": 0,
        },
    )
    summary = control["coverage"]["summary"]
    if (
        summary["native_ranges"] != 3
        or summary["native_physical_bytes"] != 11_170
        or summary["native_unique_bytes"] != 11_170
        or summary["fallback_physical_bytes"] != 2_279_280
        or summary["fallback_unique_bytes"] != 1_807_836
    ):
        raise Refusal("WAI1 current native/fallback coverage drift")
    return control


def _noema_prompt_bundle(root: str) -> tuple[str, bytes]:
    base = PurePosixPath("tests/fixtures/noema-v1") / PurePosixPath(root)
    kernel_path = (base / "kernel.noe").as_posix()
    profile_path = (base / "profile.json").as_posix()
    projection_path = (base / "projection.json").as_posix()
    kernel = _git_blob_at(NOEMA_PRODUCT_REF, kernel_path)
    profile_raw = _git_blob_at(NOEMA_PRODUCT_REF, profile_path)
    projection_raw = _git_blob_at(NOEMA_PRODUCT_REF, projection_path)
    profile = _decode_record(profile_raw)
    projection = _decode_record(projection_raw)
    corpus = _decode_record(
        _git_blob_at(NOEMA_PRODUCT_REF, "tests/fixtures/noema-v1/manifest.json")
    )
    bound = [
        item
        for item in corpus.get("specimens", [])
        if isinstance(item, dict) and item.get("directory") == root
    ]
    if (
        len(bound) != 1
        or bound[0].get("kernel_sha256") != _sha256(kernel)
        or bound[0].get("profile_sha256") != _sha256(profile_raw)
        or bound[0].get("projection_sha256") != _sha256(projection_raw)
    ):
        raise Refusal("Noema first-use prompt leaves its immutable specimen binding")
    aliases = profile.get("aliases")
    text = projection.get("text")
    if not isinstance(aliases, list) or not isinstance(text, str):
        raise Refusal("Noema first-use prompt recipe is malformed")
    try:
        projection_text = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise Refusal("Noema operation slice is not Unicode scalar text") from exc
    alias_dictionary = _canonical_json(
        {"aliases": aliases, "schema": "noema-alias-dictionary/v1"}
    )
    bundle = (
        b"NOEMA-KERNEL\n"
        + kernel
        + b"NOEMA-ALIAS-DICTIONARY\n"
        + alias_dictionary
        + b"NOEMA-OPERATION-SLICE\n"
        + projection_text
    )
    if not bundle or len(bundle) > MAX_PROMPT_BYTES:
        raise Refusal("Noema first-use prompt exceeds its byte limit")
    return projection_path, bundle


def _noema_control(manifest: dict[str, Any]) -> dict[str, Any]:
    artifacts = _control_inventory(
        NOEMA_PRODUCT_REF, NOEMA_PRODUCT_PREFIXES, require_live_match=False
    ) + _control_inventory(
        NOEMA_REVIEW_REF, NOEMA_REVIEW_PREFIXES, require_live_match=False
    )
    artifacts.sort(key=lambda item: (item["ref"], item["path"]))
    noema_manifest = _decode_record(
        _git_blob_at(NOEMA_PRODUCT_REF, "tests/fixtures/noema-v1/manifest.json")
    )
    specimens = noema_manifest.get("specimens")
    if not isinstance(specimens, list) or len(specimens) != 4:
        raise Refusal("Noema immutable specimen inventory drift")
    documents = {item["path"]: item for item in manifest["documents"]}
    current_by_path: dict[str, list[dict[str, Any]]] = {}
    specimen_roots: dict[str, str] = {}
    stale_paths: set[str] = set()
    synthetic_spans = 0
    synthetic_bytes = 0
    current_sources = 0
    for specimen in specimens:
        if not isinstance(specimen, dict) or not isinstance(specimen.get("directory"), str):
            raise Refusal("Noema specimen record is malformed")
        root = specimen["directory"]
        identity = _decode_record(
            _git_blob_at(NOEMA_PRODUCT_REF, f"tests/fixtures/noema-v1/{root}/source.json")
        )
        spans_record = _decode_record(
            _git_blob_at(
                NOEMA_PRODUCT_REF,
                f"tests/fixtures/noema-v1/{root}/source-spans.json",
            )
        )
        path = identity.get("path")
        spans = spans_record.get("spans")
        if path not in documents or not isinstance(spans, list):
            raise Refusal("Noema specimen source is outside the current corpus")
        cursor = 0
        mapped = 0
        mapped_bytes = 0
        normalized: list[dict[str, Any]] = []
        for row in spans:
            if not isinstance(row, dict):
                raise Refusal("Noema source-span row is malformed")
            start = row.get("start")
            end = row.get("end")
            kind = row.get("kind")
            if (
                type(start) is not int
                or type(end) is not int
                or start != cursor
                or end <= start
                or kind not in {"node", "unsupported-remainder"}
            ):
                raise Refusal("Noema source-span partition is malformed")
            cursor = end
            normalized.append(row)
            if kind == "node":
                mapped += 1
                mapped_bytes += end - start
        if cursor != identity.get("bytes") or mapped != specimen.get("mapped_spans"):
            raise Refusal("Noema source-span partition does not close")
        synthetic_spans += mapped
        synthetic_bytes += mapped_bytes
        current = _source_blob(path)
        if identity.get("sha256") == _sha256(current) and identity.get("bytes") == len(current):
            current_sources += 1
            current_by_path[path] = normalized
            specimen_roots[path] = root
        else:
            stale_paths.add(path)

    ranges: list[dict[str, Any]] = []
    mappings: list[dict[str, Any]] = []
    for document in manifest["documents"]:
        data = _source_blob(document["path"])
        mapped_rows = current_by_path.get(document["path"])
        if mapped_rows is None:
            reason = (
                "stale-control-source"
                if document["path"] in stale_paths
                else "unsupported-or-unmapped-current-source"
            )
            ranges.append(
                _range_record(
                    document,
                    data,
                    0,
                    len(data),
                    "raw-fallback",
                    reason,
                    f"raw:{document['sha256']}",
                )
            )
            continue
        for index, row in enumerate(mapped_rows):
            native = row["kind"] == "node"
            identifier = (
                f"noema:{document['path']}:{row['node']}:{index}"
                if native
                else f"raw:{document['sha256']}:{row['start']}:{row['end']}"
            )
            if native:
                representation_path, representation = _noema_prompt_bundle(
                    specimen_roots[document["path"]]
                )
                mappings.append(
                    {
                        "end": row["end"],
                        "id": identifier,
                        "path": document["path"],
                        "representation_bytes": len(representation),
                        "representation_path": representation_path,
                        "representation_sha256": _sha256(representation),
                        "source_sha256": _sha256(data[row["start"] : row["end"]]),
                        "start": row["start"],
                    }
                )
            ranges.append(
                _range_record(
                    document,
                    data,
                    row["start"],
                    row["end"],
                    "native" if native else "raw-fallback",
                    "" if native else "unsupported-by-noema-v1",
                    identifier,
                )
            )
    mappings.sort(key=lambda item: item["id"])

    synopsis_path = NOEMA_REVIEW_PREFIXES[1]
    synopsis = _git_blob_at(NOEMA_REVIEW_REF, synopsis_path)
    first_line = synopsis.splitlines()[0].decode("ascii", errors="strict")
    match = re.fullmatch(
        r"Synopsis schema=fiat-audit-synopsis/v1 \| source=(.+) \| "
        r"source_sha256=([0-9a-f]{64}) \| h2_count=([0-9]+)",
        first_line,
    )
    review = _git_blob_at(NOEMA_REVIEW_REF, NOEMA_REVIEW_PREFIXES[0])
    if (
        match is None
        or match.group(1) != NOEMA_REVIEW_PREFIXES[0]
        or match.group(2) != _sha256(review)
        or int(match.group(3)) != 44
    ):
        raise Refusal("Noema review synopsis does not bind its authoritative record")
    control = _base_control(
        "noema",
        manifest,
        ranges,
        binding_kind="parked-noema-product-and-review",
        product_ref=NOEMA_PRODUCT_REF,
        review_ref=NOEMA_REVIEW_REF,
        artifacts=artifacts,
        checker=None,
        native_mappings=mappings,
        graph={"edges": [], "nodes": []},
        mechanism_evidence={
            "current_native_bytes": sum(
                item["bytes"] for item in ranges if item["mode"] == "native"
            ),
            "current_native_envelopes": sum(
                item["mode"] == "native" for item in ranges
            ),
            "current_native_in_current_coverage": True,
            "scope": "current-corpus-with-separate-product-synthetic-evidence",
            "stale_sources": len(stale_paths),
            "synthetic_in_aggregate_success": False,
            "synthetic_in_current_coverage": False,
            "synthetic_mapped_bytes": synthetic_bytes,
            "synthetic_mapped_spans": synthetic_spans,
        },
    )
    summary = control["coverage"]["summary"]
    if (
        current_sources != 1
        or len(stale_paths) != 3
        or synthetic_spans != 40
        or synthetic_bytes != 3_173
        or summary["native_ranges"] != 10
        or summary["native_physical_bytes"] != 655
        or summary["native_unique_bytes"] != 655
        or summary["fallback_ranges"] != 201
        or summary["fallback_physical_bytes"] != 2_289_795
        or summary["fallback_unique_bytes"] != 1_818_351
    ):
        raise Refusal("Noema current fallback or synthetic coverage drift")
    return control


def _simple_control(manifest: dict[str, Any]) -> dict[str, Any]:
    ranges: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    for document in manifest["documents"]:
        data = _source_blob(document["path"])
        ranges.append(
            _range_record(
                document, data, 0, len(data), "native", "", f"file:{document['sha256']}"
            )
        )
        if document["path"] == document["canonical_content_path"]:
            nodes.append(
                {
                    "bytes": document["bytes"],
                    "id": f"file:{document['sha256']}",
                    "path": document["path"],
                    "sha256": document["sha256"],
                }
            )
        if document["path"] != document["canonical_content_path"]:
            edges.append(
                {
                    "kind": "exact-content-alias",
                    "source": document["path"],
                    "target": f"file:{document['sha256']}",
                }
            )
    nodes.sort(key=lambda item: item["id"])
    edges.sort(key=lambda item: (item["source"], item["target"]))
    if len(nodes) != manifest["totals"]["unique_files"]:
        raise Refusal("simple control deduplication cardinality drift")
    return _base_control(
        "simple",
        manifest,
        ranges,
        binding_kind="exact-file-content-addresses",
        product_ref=SOURCE_REF,
        review_ref=None,
        artifacts=[],
        checker=None,
        native_mappings=[],
        graph={"edges": edges, "nodes": nodes},
        mechanism_evidence={
            "current_native_bytes": manifest["totals"]["physical_bytes"],
            "current_native_envelopes": len(nodes),
            "current_native_in_current_coverage": True,
            "scope": "current-corpus",
            "stale_sources": 0,
            "synthetic_in_aggregate_success": False,
            "synthetic_in_current_coverage": False,
            "synthetic_mapped_bytes": 0,
            "synthetic_mapped_spans": 0,
        },
    )


def _markdown_sections(path: str, data: bytes) -> list[dict[str, Any]]:
    if len(data) > MAX_SOURCE_BYTES:
        raise Refusal("section source exceeds its byte limit")
    try:
        data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Refusal("section source is not UTF-8") from exc
    _preflight_partition_markdown(data, path)
    lines = data.splitlines(keepends=True)

    def fence_marker(line: bytes) -> tuple[bytes, bytes] | None:
        match = re.match(rb" {0,3}(`{3,}|~{3,})([^\r\n]*)$", line)
        return None if match is None else (match.group(1), match.group(2))

    def opens(marker: tuple[bytes, bytes]) -> bool:
        run, remainder = marker
        return run[:1] == b"~" or b"`" not in remainder

    def closes(marker: tuple[bytes, bytes], active: tuple[int, int]) -> bool:
        run, remainder = marker
        return (
            run[0] == active[0]
            and len(run) >= active[1]
            and not remainder.strip(b" \t")
        )

    fence_events = [
        (index, marker)
        for index, line in enumerate(lines)
        if (marker := fence_marker(line.rstrip(b"\r\n"))) is not None
    ]

    event_count = len(fence_events)
    event_positions = [index for index, _ in fence_events]
    suffix_balanced = [True] * (event_count + 1)
    if fence_events:
        lengths = sorted({len(marker[0]) for _, marker in fence_events})
        length_count = len(lengths)
        nearest_by_type = {
            ord("`"): [event_count] * (length_count + 1),
            ord("~"): [event_count] * (length_count + 1),
        }
        next_close = [event_count] * event_count

        def nearest_at_least(tree: list[int], length: int) -> int:
            cursor = length_count - bisect_left(lengths, length)
            nearest = event_count
            while cursor:
                nearest = min(nearest, tree[cursor])
                cursor -= cursor & -cursor
            return nearest

        def add_closer(tree: list[int], length: int, index: int) -> None:
            cursor = length_count - bisect_left(lengths, length)
            while cursor <= length_count:
                tree[cursor] = min(tree[cursor], index)
                cursor += cursor & -cursor

        for event_index in range(event_count - 1, -1, -1):
            _, marker = fence_events[event_index]
            run, remainder = marker
            tree = nearest_by_type[run[0]]
            next_close[event_index] = nearest_at_least(tree, len(run))
            if not remainder.strip(b" \t"):
                add_closer(tree, len(run), event_index)

        for event_index in range(event_count - 1, -1, -1):
            _, marker = fence_events[event_index]
            if not opens(marker):
                suffix_balanced[event_index] = suffix_balanced[event_index + 1]
                continue
            close_index = next_close[event_index]
            suffix_balanced[event_index] = (
                close_index < event_count and suffix_balanced[close_index + 1]
            )

    def commonmark_suffix_is_balanced(start: int) -> bool:
        return suffix_balanced[bisect_left(event_positions, start)]

    positions: list[tuple[int, int, bytes]] = []
    offset = 0
    fence: tuple[int, int] | None = None
    pending_template: tuple[int, int] | None = None
    for index, line in enumerate(lines):
        body = line.rstrip(b"\r\n")
        if len(body) > MAX_MARKDOWN_LINE_CHARS:
            raise Refusal("section source line exceeds its limit")
        marker = fence_marker(body)
        if fence is not None:
            if marker is not None:
                run, remainder = marker
                if closes(marker, fence):
                    if (
                        pending_template is not None
                        and closes(marker, pending_template)
                        and not commonmark_suffix_is_balanced(index + 1)
                    ):
                        pending_template = None
                    else:
                        fence = None
                        pending_template = None
                elif pending_template is not None and closes(
                    marker, pending_template
                ):
                    pending_template = None
                elif remainder.strip(b" \t") and opens(marker):
                    # Some governed source examples show balanced fenced snippets
                    # inside a surrounding fence. Keep ordinary CommonMark markers
                    # literal while admitting only that bounded template shape.
                    pending_template = (run[0], len(run))
            offset += len(line)
            continue
        if marker is not None and opens(marker):
            run, _ = marker
            fence = (run[0], len(run))
            offset += len(line)
            continue
        if fence is None:
            heading = re.match(rb" {0,3}(#{1,6})(?:[ \t]+(.*?)[ \t]*#*[ \t]*|[ \t]*)$", body)
            if heading is not None:
                title = heading.group(2) or b""
                positions.append((offset, len(heading.group(1)), title))
        offset += len(line)
    if fence is not None:
        raise Refusal("section source has an unclosed fenced block")
    if len(positions) + 1 > MAX_SECTION_COUNT:
        raise Refusal("section source exceeds its section count limit")

    descriptors: list[tuple[int, int, bytes, str, list[str]]] = []
    stack: list[tuple[int, str]] = []
    duplicates: dict[tuple[int, bytes, str], int] = {}
    preamble_id: str | None = None
    if not positions or positions[0][0] > 0:
        preamble_id = "section:" + _sha256((path + "\0preamble").encode("utf-8"))
        end = positions[0][0] if positions else len(data)
        descriptors.append((0, end, b"", preamble_id, []))
    for index, (start, level, title) in enumerate(positions):
        while stack and stack[-1][0] >= level:
            stack.pop()
        parent = stack[-1][1] if stack else preamble_id
        parent_key = parent or "root"
        key = (level, title, parent_key)
        ordinal = duplicates.get(key, 0)
        duplicates[key] = ordinal + 1
        identifier = "section:" + _sha256(
            path.encode("utf-8")
            + b"\0"
            + parent_key.encode("ascii")
            + b"\0"
            + str(level).encode("ascii")
            + b"\0"
            + title
            + b"\0"
            + str(ordinal).encode("ascii")
        )
        end = positions[index + 1][0] if index + 1 < len(positions) else len(data)
        descriptors.append((start, end, title, identifier, [parent] if parent else []))
        stack.append((level, identifier))
    nodes: list[dict[str, Any]] = []
    for start, end, title, identifier, dependencies in descriptors:
        if end <= start:
            raise Refusal("section parser emitted an empty span")
        nodes.append(
            {
                "dependencies": dependencies,
                "end": end,
                "id": identifier,
                "path": path,
                "sha256": _sha256(data[start:end]),
                "start": start,
                "title_sha256": _sha256(title),
            }
        )
    if b"".join(data[item["start"] : item["end"]] for item in nodes) != data:
        raise Refusal("section graph does not round-trip exact source bytes")
    return nodes


def _section_control(manifest: dict[str, Any]) -> dict[str, Any]:
    ranges: list[dict[str, Any]] = []
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    documents = {item["path"]: item for item in manifest["documents"]}
    sections_by_canonical_path: dict[str, list[dict[str, Any]]] = {}
    for document in manifest["documents"]:
        data = _source_blob(document["path"])
        if not document["path"].endswith(".md"):
            ranges.append(
                _range_record(
                    document,
                    data,
                    0,
                    len(data),
                    "raw-fallback",
                    "unsupported-non-markdown-source",
                    f"raw:{document['sha256']}",
                )
            )
            continue
        canonical_path = document["canonical_content_path"]
        canonical = documents[canonical_path]
        canonical_sections = sections_by_canonical_path.get(canonical_path)
        if canonical_sections is None:
            canonical_data = _source_blob(canonical_path)
            canonical_sections = [
                {**node, "authority_tier": canonical["authority_tier"]}
                for node in _markdown_sections(canonical_path, canonical_data)
            ]
            sections_by_canonical_path[canonical_path] = canonical_sections
            nodes.extend(canonical_sections)
            for node in canonical_sections:
                for dependency in node["dependencies"]:
                    edges.append(
                        {
                            "kind": "section-parent",
                            "source": node["id"],
                            "target": dependency,
                        }
                    )
        elif data != _source_blob(canonical_path):
            raise Refusal("section graph exact-content alias differs from canonical source")
        if document["path"] != canonical_path:
            edges.append(
                {
                    "kind": "exact-content-alias",
                    "source": document["path"],
                    "target": canonical_path,
                }
            )
        for node in canonical_sections:
            ranges.append(
                _range_record(
                    document,
                    data,
                    node["start"],
                    node["end"],
                    "native",
                    "",
                    node["id"],
                )
            )
    if len(nodes) > MAX_SECTION_COUNT:
        raise Refusal("section graph exceeds its global node limit")
    nodes.sort(key=lambda item: (item["path"], item["start"], item["id"]))
    edges.sort(key=lambda item: (item["kind"], item["source"], item["target"]))
    node_ids = {item["id"] for item in nodes}
    if len(node_ids) != len(nodes) or any(
        edge["source"] not in node_ids or edge["target"] not in node_ids
        for edge in edges
        if edge["kind"] == "section-parent"
    ):
        raise Refusal("section graph has duplicate or missing dependency nodes")
    control = _base_control(
        "section-graph",
        manifest,
        ranges,
        binding_kind="exact-source-span-section-graph",
        product_ref=SOURCE_REF,
        review_ref=None,
        artifacts=[],
        checker=None,
        native_mappings=[],
        graph={"edges": edges, "nodes": nodes, "selection": SECTION_SELECTION},
        mechanism_evidence={
            "current_native_bytes": sum(item["bytes"] for item in ranges if item["mode"] == "native"),
            "current_native_envelopes": len(nodes),
            "current_native_in_current_coverage": True,
            "scope": "current-corpus",
            "stale_sources": 0,
            "synthetic_in_aggregate_success": False,
            "synthetic_in_current_coverage": False,
            "synthetic_mapped_bytes": 0,
            "synthetic_mapped_spans": 0,
        },
    )
    summary = control["coverage"]["summary"]
    if (
        summary["native_physical_bytes"] != 2_071_863
        or summary["native_unique_bytes"] != 1_600_419
        or summary["fallback_physical_bytes"] != 218_587
        or summary["fallback_unique_bytes"] != 218_587
    ):
        raise Refusal("section graph Markdown/fallback coverage drift")
    _validate_section_graph(control, manifest)
    return control


def _validate_section_graph(control: dict[str, Any], manifest: dict[str, Any]) -> None:
    expected_nodes: list[dict[str, Any]] = []
    expected_edges: list[dict[str, Any]] = []
    for document in manifest["documents"]:
        if not document["path"].endswith(".md"):
            continue
        canonical_path = document["canonical_content_path"]
        if document["path"] != canonical_path:
            if _source_blob(document["path"]) != _source_blob(canonical_path):
                raise Refusal("section graph exact-content alias differs from canonical source")
            expected_edges.append(
                {
                    "kind": "exact-content-alias",
                    "source": document["path"],
                    "target": canonical_path,
                }
            )
            continue
        for parsed in _markdown_sections(canonical_path, _source_blob(canonical_path)):
            node = {**parsed, "authority_tier": document["authority_tier"]}
            expected_nodes.append(node)
            for dependency in node["dependencies"]:
                expected_edges.append(
                    {"kind": "section-parent", "source": node["id"], "target": dependency}
                )
    expected_nodes.sort(key=lambda item: (item["path"], item["start"], item["id"]))
    expected_edges.sort(key=lambda item: (item["kind"], item["source"], item["target"]))
    if control.get("graph") != {
        "edges": expected_edges,
        "nodes": expected_nodes,
        "selection": SECTION_SELECTION,
    }:
        raise Refusal("section graph differs from its deterministic parser or misses an edge")


CASE_SPECS = (
    (
        "order",
        "plugins/hexaemeron/skills/fiat/SKILL.md",
        "Act on the single directive it prints, then receipt it.",
        "state the next action while preserving the governing operation order",
        "tool-invocation",
        "agent-skills:skill:fiat:profile:fiat:frontier-gate:credential:github-contributor",
    ),
    (
        "scope",
        "plugins/horos/skills/horos/SKILL.md",
        "A scoped pass says nothing about outside-scope drift",
        "state the bounded conclusion without widening its scope",
        "decision",
        "agent-skills:skill:horos:profile:horos:frontier-gate:credential:github-contributor",
    ),
    (
        "negation",
        "AGENTS.md",
        "Files present in context are not automatically active skills.",
        "decide whether the supplied context activates an instruction",
        "decision",
        "agent-skills:skill:hermes:profile:hermes:gas-operation:credential:github-contributor",
    ),
    (
        "exception",
        "plugins/brevitas/skills/brevitas/SKILL.md",
        "- Exceptions: none\n\n### brevitas-evidence-preservation",
        "state whether the described gate has an applicable exception",
        "decision",
        "agent-skills:skill:fiat:profile:fiat:prose__scribe__brevitas-1__issue-0__last-1:credential:github-contributor",
    ),
    (
        "literal",
        "plugins/hexaemeron/skills/ephoros/SKILL.md",
        "40-hex literal used as a metric label",
        "preserve the exact literal constraint in the resulting plan",
        "structured-plan",
        "agent-skills:skill:ephoros:profile:ephoros:frontier-gate:credential:github-contributor",
    ),
    (
        "alias",
        "PROMISE_MACHINE.md",
        "every canonical name a case expects or contests",
        "resolve the named identity without inventing an alias",
        "decision",
        "agent-skills:skill:x-ray:profile:x-ray:audit:credential:github-contributor",
    ),
    (
        "unknown",
        "PROMISE_MACHINE.md",
        "Absence, ambiguity and `unknown` never pass.",
        "decide the transition when the supplied evidence is unknown",
        "refusal",
        "agent-skills:skill:solidity-auditor:profile:solidity-auditor:audit:credential:github-contributor",
    ),
    (
        "refusal",
        "plugins/hexaemeron/skills/elenchus/SKILL.md",
        "- Refuses: A symptom-only patch",
        "decide whether to proceed with the described repair",
        "refusal",
        "agent-skills:skill:elenchus:profile:elenchus:contract-fix:credential:github-contributor",
    ),
    (
        "recovery",
        "plugins/hexaemeron/skills/metron/SKILL.md",
        "- Recovery: Freeze one reproducible method",
        "state the recovery sequence for the failed measurement",
        "recovery",
        "agent-skills:skill:fiat:profile:fiat:implement__mason__none__metron-budget__elenchus-contract__hypomnema__hermes:credential:github-contributor",
    ),
    (
        "authority",
        "AGENTS.md",
        "It does not activate a skill, grant authority,",
        "decide whether the supplied material grants action authority",
        "refusal",
        "agent-skills:skill:lazarus:profile:lazarus:maintenance:credential:github-contributor",
    ),
)


def _scenario_paths(
    manifest: dict[str, Any], graph: dict[str, Any], scenario_id: str
) -> list[str]:
    roots = [item for item in graph["scenario_roots"] if item["id"] == scenario_id]
    if len(roots) != 1:
        raise Refusal("development scenario root is missing or duplicated")
    adjacency: dict[str, set[str]] = {}
    for edge in graph["scenario_edges"]:
        if scenario_id in edge["active_scenarios"]:
            adjacency.setdefault(edge["source"], set()).add(edge["target"])
    pending = [roots[0]["node"]]
    reached: set[str] = set()
    ordered: list[str] = []
    while pending:
        node = pending.pop(0)
        if node in reached:
            continue
        reached.add(node)
        ordered.append(node)
        if len(reached) > EXPECTED_TOTALS["physical_files"]:
            raise Refusal("development scenario graph exceeds its corpus bound")
        pending.extend(
            path
            for path in sorted(adjacency.get(node, set()))
            if path not in reached and path not in pending
        )
    expected = {
        item["path"]
        for item in manifest["documents"]
        if scenario_id in item["scenario_reachability"]
    }
    if reached != expected:
        raise Refusal("development scenario graph has a missing or invented edge")
    return ordered


def _scenario_for_path(
    document: dict[str, Any],
    graph: dict[str, Any],
    development_skills: set[str],
    scenario_id: str,
) -> str:
    roots = {item["id"]: item for item in graph["scenario_roots"]}
    root = roots.get(scenario_id)
    if (
        root is None
        or scenario_id not in document["scenario_reachability"]
        or root["selected_skill"] not in development_skills
    ):
        raise Refusal(f"development case source has no admitted scenario: {document['path']}")
    return scenario_id


def _development_case_coverage(
    cases: list[dict[str, Any]],
    manifest: dict[str, Any],
    cohorts: dict[str, Any],
    graph: dict[str, Any],
) -> dict[str, Any]:
    documents = {item["path"]: item for item in manifest["documents"]}
    physical_paths = {
        path
        for case in cases
        for path in _scenario_paths(manifest, graph, case["scenario_id"])
    }
    holdout_paths = set(cohorts["holdout"]["paths"])
    if physical_paths & holdout_paths:
        raise Refusal("development case scenarios expose a sealed holdout path")
    canonical_paths = {
        documents[path]["canonical_content_path"] for path in physical_paths
    }
    development_paths = set(cohorts["development"]["paths"])
    if not canonical_paths <= development_paths:
        raise Refusal("development case scenarios leave the development cohort")
    unique_bytes = sum(documents[path]["bytes"] for path in canonical_paths)
    logical_skills = sorted(
        {
            documents[path]["logical_document"].removeprefix("skill:")
            for path in canonical_paths
            if documents[path]["logical_document"].startswith("skill:")
        }
    )
    authority_tiers = sorted(
        {documents[path]["authority_tier"] for path in canonical_paths}
    )
    document_classes = sorted(
        {documents[path]["document_class"] for path in canonical_paths}
    )
    constructs = _observed_constructs(sorted(canonical_paths))
    shared_paths = sorted(set(SHARED_BEHAVIORAL_PATHS) & canonical_paths)
    deciles = _size_deciles(
        [
            item
            for item in manifest["documents"]
            if item["path"] == item["canonical_content_path"]
        ]
    )
    size_deciles = sorted({deciles[path] for path in canonical_paths})
    if unique_bytes * 2 < manifest["totals"]["unique_bytes"]:
        raise Refusal("behavioral development coverage is below 50 percent")
    if len(logical_skills) < 12:
        raise Refusal("behavioral development coverage has fewer than 12 logical skills")
    if authority_tiers != cohorts["development"]["authority_tiers"]:
        raise Refusal("behavioral development authority-tier coverage is incomplete")
    if document_classes != cohorts["development"]["document_classes"]:
        raise Refusal("behavioral development document-class coverage is incomplete")
    if constructs != cohorts["development"]["constructs"]:
        raise Refusal("behavioral development construct coverage is incomplete")
    if shared_paths != list(SHARED_BEHAVIORAL_PATHS):
        raise Refusal("behavioral development shared-contract coverage is incomplete")
    if size_deciles != cohorts["development"]["size_deciles"]:
        raise Refusal("behavioral development size-decile coverage is incomplete")
    return {
        "authority_tiers": authority_tiers,
        "canonical_paths": sorted(canonical_paths),
        "constructs": constructs,
        "document_classes": document_classes,
        "logical_skills": logical_skills,
        "physical_paths": sorted(physical_paths),
        "shared_paths": shared_paths,
        "size_deciles": size_deciles,
        "unique_byte_ratio": f"{unique_bytes / manifest['totals']['unique_bytes']:.6f}",
        "unique_bytes": unique_bytes,
    }


def _development_cases(
    manifest: dict[str, Any], cohorts: dict[str, Any], graph: dict[str, Any]
) -> dict[str, Any]:
    documents = {item["path"]: item for item in manifest["documents"]}
    development_paths = set(cohorts["development"]["paths"])
    holdout_paths = set(cohorts["holdout"]["paths"])
    development_skills = set(cohorts["development"]["logical_skills"])
    cases: list[dict[str, Any]] = []
    for index, (
        semantic,
        path,
        needle,
        task,
        response_shape,
        scenario_id,
    ) in enumerate(CASE_SPECS, 1):
        document = documents.get(path)
        if document is None or path not in development_paths or path in holdout_paths:
            raise Refusal("development case source crosses the sealed cohort boundary")
        data = _source_blob(path)
        encoded = needle.encode("utf-8")
        start = data.find(encoded)
        if start < 0 or data.find(encoded, start + 1) >= 0:
            raise Refusal(f"development case source span is missing or ambiguous: {semantic}")
        end = start + len(encoded)
        scenario_id = _scenario_for_path(
            document, graph, development_skills, scenario_id
        )
        if path not in _scenario_paths(manifest, graph, scenario_id):
            raise Refusal("development case source is not scenario reachable")
        cases.append(
            {
                "expectation": {
                    "kind": "exact-source-span",
                    "sha256": _sha256(data[start:end]),
                },
                "id": f"development-{index:02d}-{semantic}",
                "response_shape": response_shape,
                "scenario_id": scenario_id,
                "semantic_class": semantic,
                "source": {
                    "end": end,
                    "path": path,
                    "sha256": _sha256(data[start:end]),
                    "source_sha256": _sha256(data),
                    "start": start,
                },
                "task": task,
            }
        )
    record = {
        "cases": cases,
        "cohorts_sha256": _artifact_digest(cohorts),
        "coverage": _development_case_coverage(cases, manifest, cohorts, graph),
        "manifest_sha256": _artifact_digest(manifest),
        "schema": f"{SCHEMA_PREFIX}-cases/v1",
        "source_ref": SOURCE_REF,
    }
    _validate_development_cases(record, manifest, cohorts, graph)
    return record


def _validate_development_cases(
    record: dict[str, Any],
    manifest: dict[str, Any],
    cohorts: dict[str, Any],
    graph: dict[str, Any],
) -> None:
    _require_fields(
        record,
        ("cases", "cohorts_sha256", "coverage", "manifest_sha256", "schema", "source_ref"),
        ("cases", "cohorts_sha256", "coverage", "manifest_sha256", "schema", "source_ref"),
        "development cases",
    )
    cases = record["cases"]
    if (
        record["schema"] != f"{SCHEMA_PREFIX}-cases/v1"
        or record["source_ref"] != SOURCE_REF
        or record["manifest_sha256"] != _artifact_digest(manifest)
        or record["cohorts_sha256"] != _artifact_digest(cohorts)
        or not isinstance(cases, list)
        or len(cases) > MAX_DEVELOPMENT_CASES
        or [item.get("semantic_class") for item in cases] != list(DEVELOPMENT_CLASSES)
    ):
        raise Refusal("development case-set identity drift")
    holdout_paths = set(cohorts["holdout"]["paths"])
    development_paths = set(cohorts["development"]["paths"])
    for case in cases:
        _require_fields(
            case,
            ("expectation", "id", "response_shape", "scenario_id", "semantic_class", "source", "task"),
            ("expectation", "id", "response_shape", "scenario_id", "semantic_class", "source", "task"),
            "development case",
        )
        source = case["source"]
        expectation = case["expectation"]
        if not isinstance(source, dict) or not isinstance(expectation, dict):
            raise Refusal("development case source or expectation is malformed")
        _require_fields(
            source,
            ("end", "path", "sha256", "source_sha256", "start"),
            ("end", "path", "sha256", "source_sha256", "start"),
            "development case source",
        )
        _require_fields(
            expectation,
            ("kind", "sha256"),
            ("kind", "sha256"),
            "development case expectation",
        )
        path = source["path"]
        data = _source_blob(path)
        if (
            path not in development_paths
            or path in holdout_paths
            or source["start"] < 0
            or source["end"] <= source["start"]
            or source["end"] > len(data)
            or source["source_sha256"] != _sha256(data)
            or source["sha256"] != _sha256(data[source["start"] : source["end"]])
            or expectation != {"kind": "exact-source-span", "sha256": source["sha256"]}
            or path not in _scenario_paths(manifest, graph, case["scenario_id"])
        ):
            raise Refusal("development case source oracle drift")
        if not isinstance(case["task"], str) or not case["task"]:
            raise Refusal("development case task is empty")
    if record["coverage"] != _development_case_coverage(cases, manifest, cohorts, graph):
        raise Refusal("behavioral development coverage record drift")


def _control_ranges(control: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {}
    for row in control["coverage"]["ranges"]:
        result.setdefault(row["path"], []).append(row)
    return result


def _prompt_component(
    identifier: str,
    content: bytes,
    encoding: str,
    source: dict[str, Any] | None,
    *,
    kind: str | None = None,
) -> dict[str, Any]:
    try:
        text = content.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise Refusal("prompt representation is not UTF-8") from exc
    resolved_kind = kind or ("representation" if source is not None else "task")
    if resolved_kind not in {"representation", "task"}:
        raise Refusal("prompt component kind is malformed")
    return {
        "content": text,
        "encoding": encoding,
        "id": identifier,
        "kind": resolved_kind,
        "source": source,
    }


def _assemble_prompt(
    arm: str,
    case: dict[str, Any],
    manifest: dict[str, Any],
    graph: dict[str, Any],
    control: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if control["arm"] != arm:
        raise Refusal("adapter and control identity differ")
    documents = {item["path"]: item for item in manifest["documents"]}
    paths = _scenario_paths(manifest, graph, case["scenario_id"])
    components = [
        _prompt_component(
            "task",
            case["task"].encode("utf-8"),
            "utf-8-task",
            None,
        )
    ]
    trace: list[dict[str, Any]] = []
    if arm == "simple":
        emitted: dict[str, str] = {}
        originals: dict[str, list[str]] = {}
        for path in paths:
            document = documents[path]
            canonical_path = document["canonical_content_path"]
            canonical = documents[canonical_path]
            identifier = f"file:{canonical['sha256']}"
            originals.setdefault(identifier, []).append(path)
            if identifier in emitted:
                continue
            data = _source_blob(canonical_path)
            component_id = f"representation-{len(components):04d}"
            components.append(
                _prompt_component(
                    component_id,
                    data,
                    "content-addressed-source",
                    {
                        "end": len(data),
                        "path": canonical_path,
                        "sha256": _sha256(data),
                        "start": 0,
                    },
                )
            )
            emitted[identifier] = component_id
        for identifier in sorted(originals):
            trace.append(
                {
                    "component_id": emitted[identifier],
                    "mode": "native",
                    "original_paths": sorted(originals[identifier]),
                    "representation_id": identifier,
                }
            )
    elif arm == "section-graph":
        _validate_section_graph(control, manifest)
        ranges_by_path = _control_ranges(control)
        nodes = {item["id"]: item for item in control["graph"]["nodes"]}
        emitted: dict[str, str] = {}
        originals: dict[str, list[str]] = {}
        emission_order: list[str] = []
        for path in paths:
            document = documents[path]
            canonical_path = document["canonical_content_path"]
            data = _source_blob(canonical_path)
            rows = ranges_by_path.get(path)
            if not rows:
                raise Refusal("adapter selection has no source coverage")
            for row in rows:
                identifier = row["representation_id"]
                originals.setdefault(identifier, []).append(path)
                if identifier in emitted:
                    continue
                if row["mode"] == "native":
                    node = nodes.get(identifier)
                    if node is None or node["path"] != canonical_path:
                        raise Refusal("section selection leaves its canonical node")
                    start = node["start"]
                    end = node["end"]
                    encoding = "exact-source-section"
                else:
                    start = row["start"]
                    end = row["end"]
                    encoding = "raw-source-fallback"
                payload = data[start:end]
                if len(payload) != row["bytes"] or _sha256(payload) != row["sha256"]:
                    raise Refusal("section selection differs from its canonical source")
                component_id = f"representation-{len(components):04d}"
                components.append(
                    _prompt_component(
                        component_id,
                        payload,
                        encoding,
                        {
                            "end": end,
                            "path": canonical_path,
                            "sha256": _sha256(payload),
                            "start": start,
                        },
                    )
                )
                emitted[identifier] = component_id
                emission_order.append(identifier)
        selected = set(emission_order)
        if any(
            dependency not in selected
            for identifier in emission_order
            for dependency in nodes.get(identifier, {}).get("dependencies", [])
        ):
            raise Refusal("section selection misses a transitive parent dependency")
        for identifier in emission_order:
            trace.append(
                {
                    "component_id": emitted[identifier],
                    "mode": "native" if identifier in nodes else "raw-fallback",
                    "original_paths": sorted(originals[identifier]),
                    "representation_id": identifier,
                }
            )
    else:
        ranges_by_path = _control_ranges(control)
        mappings = {item["id"]: item for item in control["native_mappings"]}
        wai1_bootstrap_component: str | None = None
        noema_components: dict[str, str] = {}
        for path in paths:
            data = _source_blob(path)
            rows = ranges_by_path.get(path)
            if not rows:
                raise Refusal("adapter selection has no source coverage")
            for row in rows:
                payload = data[row["start"] : row["end"]]
                encoding = (
                    "raw-source-fallback"
                    if row["mode"] == "raw-fallback"
                    else "exact-source"
                )
                if arm == "wai1" and row["mode"] == "native":
                    mapping = mappings.get(row["representation_id"])
                    if mapping is None:
                        raise Refusal("WAI1 prompt mapping is missing")
                    if wai1_bootstrap_component is None:
                        bootstrap_path, bootstrap = _wai1_decoder_bootstrap()
                        wai1_bootstrap_component = f"representation-{len(components):04d}"
                        components.append(
                            _prompt_component(
                                wai1_bootstrap_component,
                                bootstrap,
                                "wai1-decoder-bootstrap",
                                None,
                                kind="representation",
                            )
                        )
                        if not any(
                            item["path"] == bootstrap_path
                            and item["sha256"] == _sha256(bootstrap)
                            for item in control["binding"]["artifacts"]
                        ):
                            raise Refusal("WAI1 prompt bootstrap is outside its binding")
                    payload = _git_blob_at(WAI1_CONTROL_REF, mapping["representation_path"])
                    if _sha256(payload) != mapping["representation_sha256"]:
                        raise Refusal("WAI1 prompt representation digest drift")
                    encoding = "wai1-compact"
                elif arm == "noema" and row["mode"] == "native":
                    mapping = mappings.get(row["representation_id"])
                    if mapping is None:
                        raise Refusal("Noema prompt mapping is missing")
                    key = mapping["representation_sha256"]
                    component_id = noema_components.get(key)
                    if component_id is None:
                        root = PurePosixPath(mapping["representation_path"]).parent
                        prefix = PurePosixPath("tests/fixtures/noema-v1")
                        try:
                            relative_root = root.relative_to(prefix).as_posix()
                        except ValueError as exc:
                            raise Refusal("Noema prompt mapping leaves its immutable root") from exc
                        representation_path, payload = _noema_prompt_bundle(relative_root)
                        if (
                            representation_path != mapping["representation_path"]
                            or len(payload) != mapping["representation_bytes"]
                            or _sha256(payload) != mapping["representation_sha256"]
                        ):
                            raise Refusal("Noema first-use prompt representation drift")
                        component_id = f"representation-{len(components):04d}"
                        components.append(
                            _prompt_component(
                                component_id,
                                payload,
                                "noema-first-use",
                                None,
                                kind="representation",
                            )
                        )
                        noema_components[key] = component_id
                    trace.append(
                        {
                            "component_id": component_id,
                            "mode": row["mode"],
                            "original_paths": [path],
                            "representation_id": row["representation_id"],
                        }
                    )
                    continue
                component_id = f"representation-{len(components):04d}"
                source = {
                    "end": row["end"],
                    "path": path,
                    "sha256": row["sha256"],
                    "start": row["start"],
                }
                components.append(_prompt_component(component_id, payload, encoding, source))
                trace.append(
                    {
                        "component_id": component_id,
                        "mode": row["mode"],
                        "original_paths": [path],
                        "representation_id": row["representation_id"],
                    }
                )
    if len(components) > MAX_PROMPT_COMPONENTS:
        raise Refusal("prompt component count exceeds its limit")
    body = {
        "case_id": case["id"],
        "components": components,
        "scenario_id": case["scenario_id"],
        "schema": f"{SCHEMA_PREFIX}-prompt/v1",
    }
    body_bytes = _canonical_json(body)
    if len(body_bytes) > MAX_PROMPT_BYTES:
        raise Refusal("prompt exceeds its byte limit")
    prompt = {**body, "sha256": _sha256(body_bytes)}
    if set(prompt) & {"arm", "candidate", "expected_answer", "scorer_key"}:
        raise Refusal("prompt contains an answer or candidate label")
    return prompt, trace


def _case_native(control: dict[str, Any], case: dict[str, Any]) -> bool:
    source = case["source"]
    rows = [
        item
        for item in control["coverage"]["ranges"]
        if item["path"] == source["path"]
        and item["end"] > source["start"]
        and item["start"] < source["end"]
    ]
    cursor = source["start"]
    for row in rows:
        start = max(row["start"], source["start"])
        end = min(row["end"], source["end"])
        if start != cursor or row["mode"] != "native":
            return False
        cursor = end
    return cursor == source["end"]


def _validate_prompt(prompt: dict[str, Any]) -> None:
    if isinstance(prompt, dict) and set(prompt) & {
        "arm",
        "candidate",
        "expected_answer",
        "scorer_key",
    }:
        raise Refusal("prompt contains an answer or candidate label")
    _require_fields(
        prompt,
        ("case_id", "components", "scenario_id", "schema", "sha256"),
        ("case_id", "components", "scenario_id", "schema", "sha256"),
        "prompt",
    )
    components = prompt["components"]
    if prompt["schema"] != f"{SCHEMA_PREFIX}-prompt/v1" or not isinstance(
        components, list
    ):
        raise Refusal("prompt identity drift")
    if len(components) > MAX_PROMPT_COMPONENTS:
        raise Refusal("prompt component count exceeds its limit")
    if len(components) < 2:
        raise Refusal("prompt has too few components")
    component_ids: set[str] = set()
    for index, component in enumerate(components):
        _require_fields(
            component,
            ("content", "encoding", "id", "kind", "source"),
            ("content", "encoding", "id", "kind", "source"),
            "prompt component",
        )
        if (
            not isinstance(component["content"], str)
            or not isinstance(component["id"], str)
            or not component["id"]
            or component["id"] in component_ids
        ):
            raise Refusal("prompt component content is malformed")
        component_ids.add(component["id"])
        if index == 0:
            if (
                component["kind"] != "task"
                or component["source"] is not None
                or component["encoding"] != "utf-8-task"
            ):
                raise Refusal("prompt task component drift")
        elif component["kind"] != "representation":
            raise Refusal("prompt representation component drift")
        elif component["source"] is None:
            if component["encoding"] not in {
                "noema-first-use",
                "wai1-decoder-bootstrap",
            }:
                raise Refusal("unbound prompt representation component")
        elif not isinstance(component["source"], dict):
            raise Refusal("prompt representation source is malformed")
    body = {key: value for key, value in prompt.items() if key != "sha256"}
    if len(_canonical_json(body)) > MAX_PROMPT_BYTES:
        raise Refusal("prompt exceeds its byte limit")
    if prompt["sha256"] != _sha256(_canonical_json(body)):
        raise Refusal("prompt digest drift")
def _validate_score(score: dict[str, Any]) -> None:
    fields = (
        "exact_source_recovery",
        "fallback_used",
        "native_exact_source_recovery",
        "native_mapping_used",
        "trace_complete",
    )
    _require_fields(score, fields, fields, "deterministic score")
    if any(type(score[field]) is not bool for field in fields):
        raise Refusal("deterministic score fields are not Boolean")
    if score["fallback_used"] == score["native_mapping_used"]:
        raise Refusal("fallback and native mapping classification are not exclusive")
    if score["native_exact_source_recovery"] and (
        not score["native_mapping_used"] or not score["exact_source_recovery"]
    ):
        raise Refusal("native exact-source recovery lacks its required predicates")


def _recover_case_source(
    control: dict[str, Any],
    case: dict[str, Any],
    prompt: dict[str, Any],
    trace: list[dict[str, Any]],
) -> bytes | None:
    """Recover a case oracle only from exact bytes carried by its prompt."""
    source = case["source"]
    components = {item["id"]: item for item in prompt["components"]}
    ranges = {
        (item["path"], item["representation_id"]): item
        for item in control["coverage"]["ranges"]
    }
    segments: list[tuple[int, int, bytes | None]] = []
    exact_encodings = {
        "content-addressed-source",
        "exact-source",
        "exact-source-section",
        "raw-source-fallback",
    }
    for row in trace:
        if source["path"] not in row["original_paths"]:
            continue
        coverage = ranges.get((source["path"], row["representation_id"]))
        component = components.get(row["component_id"])
        if coverage is None or component is None:
            raise Refusal("adapter selection trace does not resolve to its control")
        content: bytes | None = None
        if component["encoding"] in exact_encodings:
            try:
                candidate = component["content"].encode("utf-8", errors="strict")
            except UnicodeEncodeError as exc:
                raise Refusal("prompt representation is not Unicode scalar text") from exc
            if (
                len(candidate) != coverage["bytes"]
                or _sha256(candidate) != coverage["sha256"]
            ):
                raise Refusal("exact prompt representation differs from its control span")
            content = candidate
        segments.append((coverage["start"], coverage["end"], content))

    cursor = source["start"]
    recovered: list[bytes] = []
    for start, end, content in sorted(segments):
        overlap_start = max(start, source["start"])
        overlap_end = min(end, source["end"])
        if overlap_end <= overlap_start:
            continue
        if overlap_start != cursor or content is None:
            return None
        recovered.append(content[overlap_start - start : overlap_end - start])
        cursor = overlap_end
        if cursor == source["end"]:
            break
    if cursor != source["end"]:
        return None
    return b"".join(recovered)


def _case_score(
    control: dict[str, Any], case: dict[str, Any], prompt: dict[str, Any], trace: list[dict[str, Any]]
) -> tuple[dict[str, bool], bytes | None]:
    _validate_prompt(prompt)
    component_ids = {item["id"] for item in prompt["components"]}
    if not trace or any(
        not isinstance(row, dict)
        or row.get("component_id") not in component_ids
        or not row.get("original_paths")
        for row in trace
    ):
        raise Refusal("adapter selection trace is incomplete")
    native = _case_native(control, case)
    fallback = not native
    recovered = _recover_case_source(control, case, prompt, trace)
    exact = (
        recovered is not None
        and len(recovered) == case["source"]["end"] - case["source"]["start"]
        and _sha256(recovered) == case["expectation"]["sha256"]
    )
    score = {
        "exact_source_recovery": exact,
        "fallback_used": fallback,
        "native_exact_source_recovery": bool(exact and native),
        "native_mapping_used": native,
        "trace_complete": True,
    }
    _validate_score(score)
    return score, recovered


def _case_outcome(case: dict[str, Any], recovered: bytes | None) -> dict[str, Any]:
    source = case["source"]
    exact = recovered is not None and _sha256(recovered) == case["expectation"]["sha256"]
    return {
        "kind": case["response_shape"],
        "recovery": (
            {"bytes": len(recovered), "sha256": _sha256(recovered)}
            if exact and recovered is not None
            else None
        ),
        "source_expectation": {
            "end": source["end"],
            "path": source["path"],
            "sha256": source["sha256"],
            "start": source["start"],
        },
        "status": "exact-source-recovered" if exact else "exact-source-unavailable",
    }


def _adapter_correlation(
    arm: str,
    case_id: str,
    scenario_id: str,
    prompt_sha256: str,
    outcome: dict[str, Any],
) -> str:
    return _sha256(
        (
            SOURCE_REF
            + "\0"
            + arm
            + "\0"
            + scenario_id
            + "\0"
            + case_id
            + "\0"
            + prompt_sha256
            + "\0"
            + _sha256(_canonical_json(outcome))
        ).encode("utf-8")
    )


def _arm_results(
    arm: str,
    cases_record: dict[str, Any],
    manifest: dict[str, Any],
    graph: dict[str, Any],
    control: dict[str, Any],
) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for case in cases_record["cases"]:
        prompt, trace = _assemble_prompt(arm, case, manifest, graph, control)
        score, recovered = _case_score(control, case, prompt, trace)
        outcome = _case_outcome(case, recovered)
        correlation = _adapter_correlation(
            arm,
            case["id"],
            case["scenario_id"],
            prompt["sha256"],
            outcome,
        )
        results.append(
            {
                "case_id": case["id"],
                "correlation_id": correlation,
                "outcome": outcome,
                "prompt": prompt,
                "scenario_id": case["scenario_id"],
                "score": score,
                "selection_trace": trace,
            }
        )
        _validate_prompt(prompt)
    aggregate = {
        "cases": len(results),
        "exact_source_recovery_cases": sum(
            item["score"]["exact_source_recovery"] for item in results
        ),
        "fallback_cases": sum(item["score"]["fallback_used"] for item in results),
        "native_exact_source_recovery_cases": sum(
            item["score"]["native_exact_source_recovery"] for item in results
        ),
        "native_mapping_cases": sum(
            item["score"]["native_mapping_used"] for item in results
        ),
        "prompt_bytes": sum(len(_canonical_json(item["prompt"])) for item in results),
    }
    record = {
        "aggregate": aggregate,
        "arm": arm,
        "case_set_sha256": _artifact_digest(cases_record),
        "control_sha256": _artifact_digest(control),
        "results": results,
        "schema": f"{SCHEMA_PREFIX}-adapter-results/v1",
        "source_ref": SOURCE_REF,
    }
    _validate_adapter_results(record, cases_record, manifest, graph, control)
    return record


def _validate_adapter_results(
    record: dict[str, Any],
    cases_record: dict[str, Any],
    manifest: dict[str, Any],
    graph: dict[str, Any],
    control: dict[str, Any],
) -> None:
    _require_fields(
        record,
        ("aggregate", "arm", "case_set_sha256", "control_sha256", "results", "schema", "source_ref"),
        ("aggregate", "arm", "case_set_sha256", "control_sha256", "results", "schema", "source_ref"),
        "adapter results",
    )
    if (
        record["schema"] != f"{SCHEMA_PREFIX}-adapter-results/v1"
        or record["source_ref"] != SOURCE_REF
        or record["arm"] not in DEVELOPMENT_ARMS
        or record["arm"] != control["arm"]
        or record["case_set_sha256"] != _artifact_digest(cases_record)
        or record["control_sha256"] != _artifact_digest(control)
        or not isinstance(record["results"], list)
    ):
        raise Refusal("adapter result identity drift")
    if not all(isinstance(result, dict) for result in record["results"]):
        raise Refusal("adapter result case order or coverage drift")
    if [result.get("case_id") for result in record["results"]] != [
        case["id"] for case in cases_record["cases"]
    ]:
        raise Refusal("adapter result case order or coverage drift")
    cases_by_id = {item["id"]: item for item in cases_record["cases"]}
    for result in record["results"]:
        _require_fields(
            result,
            ("case_id", "correlation_id", "outcome", "prompt", "scenario_id", "score", "selection_trace"),
            ("case_id", "correlation_id", "outcome", "prompt", "scenario_id", "score", "selection_trace"),
            "adapter case result",
        )
        _validate_prompt(result["prompt"])
        _validate_score(result["score"])
        if (
            result["prompt"]["case_id"] != result["case_id"]
            or result["prompt"]["scenario_id"] != result["scenario_id"]
            or result["correlation_id"]
            != _adapter_correlation(
                record["arm"],
                result["case_id"],
                result["scenario_id"],
                result["prompt"]["sha256"],
                result["outcome"],
            )
        ):
            raise Refusal("adapter result correlation drift")
        case = cases_by_id.get(result["case_id"])
        if case is None:
            raise Refusal("adapter result names an unknown case")
        expected_prompt, expected_trace = _assemble_prompt(
            record["arm"], case, manifest, graph, control
        )
        expected_score, recovered = _case_score(
            control, case, expected_prompt, expected_trace
        )
        expected_outcome = _case_outcome(case, recovered)
        if (
            result["scenario_id"] != case["scenario_id"]
            or result["prompt"] != expected_prompt
            or result["selection_trace"] != expected_trace
            or result["score"] != expected_score
            or result["outcome"] != expected_outcome
        ):
            raise Refusal("adapter result differs from its representation-bound derivation")
    aggregate = record["aggregate"]
    expected = {
        "cases": len(record["results"]),
        "exact_source_recovery_cases": sum(
            item["score"]["exact_source_recovery"] for item in record["results"]
        ),
        "fallback_cases": sum(item["score"]["fallback_used"] for item in record["results"]),
        "native_exact_source_recovery_cases": sum(
            item["score"]["native_exact_source_recovery"]
            for item in record["results"]
        ),
        "native_mapping_cases": sum(
            item["score"]["native_mapping_used"] for item in record["results"]
        ),
        "prompt_bytes": sum(len(_canonical_json(item["prompt"])) for item in record["results"]),
    }
    if aggregate != expected:
        raise Refusal("adapter aggregate differs from case scores")


def _hostile_specimens() -> dict[str, Any]:
    rows = [
        ("parser-differential", "unclosed-fence", "section source has an unclosed fenced block"),
        ("stale-source", "changed-source-digest", "development case source oracle drift"),
        ("malformed-input", "noncanonical-json", "record is not canonical JSON"),
        ("malformed-input", "duplicate-json-key", "duplicate JSON key"),
        ("missing-edge", "delete-scenario-edge", "missing or invented edge"),
        ("digest", "changed-span-digest", "adapter coverage digest drift"),
        ("concurrent-change", "replace-open-input", "input changed during read"),
        ("hostile-output", "oversized-model-output", "model output exceeds its limit"),
        ("resource-bound", "too-many-components", "prompt component count exceeds its limit"),
        ("path-boundary", "parent-traversal", "unsafe repository path"),
        ("path-boundary", "symlink-input", "input is not a single-link regular file"),
        ("prompt-leak", "scorer-key-field", "prompt contains an answer or candidate label"),
    ]
    if len(rows) > MAX_HOSTILE_SPECIMENS:
        raise Refusal("hostile specimen count exceeds its limit")
    return {
        "schema": f"{SCHEMA_PREFIX}-mutations/v1",
        "source_ref": SOURCE_REF,
        "specimens": [
            {
                "expected_refusal": expected,
                "id": f"hostile-{index:02d}-{category}",
                "mutation": mutation,
                "risk_class": category,
            }
            for index, (category, mutation, expected) in enumerate(rows, 1)
        ],
    }


def _validate_model_output(data: bytes) -> dict[str, Any]:
    if len(data) > MAX_MODEL_OUTPUT_BYTES:
        raise Refusal("model output exceeds its limit")
    value = _decode_record(data)
    _require_fields(value, ("case_id", "outcome"), ("case_id", "outcome"), "model output")
    if not isinstance(value["case_id"], str) or not isinstance(value["outcome"], str):
        raise Refusal("model output fields are malformed")
    return value


def _hostile_recipe(
    specimen: dict[str, Any],
    arm: str,
    case: dict[str, Any],
    result: dict[str, Any],
    control_sha256: str,
) -> str:
    return _sha256(
        _canonical_json(
            {
                "arm": arm,
                "case_id": case["id"],
                "control_sha256": control_sha256,
                "mutation": specimen["mutation"],
                "prompt_sha256": result["prompt"]["sha256"],
                "scenario_id": case["scenario_id"],
                "specimen_sha256": _artifact_digest(specimen),
            }
        )
    )


def _exercise_hostile_specimen(
    specimen: dict[str, Any],
    arm: str,
    cases: dict[str, Any],
    manifest: dict[str, Any],
    cohorts: dict[str, Any],
    graph: dict[str, Any],
    control: dict[str, Any],
    arm_results: dict[str, Any],
    control_sha256: str,
) -> dict[str, Any]:
    case = cases["cases"][0]
    result = arm_results["results"][0]
    mutation = specimen["mutation"]
    try:
        if mutation == "unclosed-fence":
            _markdown_sections("hostile.md", b"# admitted\n```text\nnot closed\n")
        elif mutation == "changed-source-digest":
            changed = _decode_record(_canonical_json(cases))
            changed["cases"][0]["source"]["source_sha256"] = "0" * 64
            _validate_development_cases(changed, manifest, cohorts, graph)
        elif mutation == "noncanonical-json":
            _decode_record(b'{ "case_id": "hostile" }\n')
        elif mutation == "duplicate-json-key":
            _decode_record(b'{"case_id":"a","case_id":"b"}\n')
        elif mutation == "delete-scenario-edge":
            changed = _decode_record(_canonical_json(graph))
            for index, edge in enumerate(changed["scenario_edges"]):
                if (
                    case["scenario_id"] in edge["active_scenarios"]
                    and edge["target"] == case["source"]["path"]
                ):
                    changed["scenario_edges"].pop(index)
                    break
            else:
                raise Refusal("hostile missing-edge recipe has no removable edge")
            _scenario_paths(manifest, changed, case["scenario_id"])
        elif mutation == "changed-span-digest":
            changed = _decode_record(_canonical_json(control))
            changed["coverage"]["ranges"][0]["sha256"] = "0" * 64
            _coverage_summary(manifest, changed["coverage"]["ranges"])
        elif mutation == "replace-open-input":
            _require_unchanged_input((1, 2, 3), (1, 2, 4))
        elif mutation == "oversized-model-output":
            _validate_model_output(b"x" * (MAX_MODEL_OUTPUT_BYTES + 1))
        elif mutation == "too-many-components":
            changed = _decode_record(_canonical_json(result["prompt"]))
            changed["components"] = [changed["components"][0]] * (
                MAX_PROMPT_COMPONENTS + 1
            )
            _validate_prompt(changed)
        elif mutation == "parent-traversal":
            _safe_relative("../escape")
        elif mutation == "symlink-input":
            _validate_input_metadata(stat.S_IFLNK | 0o777, 1, 1, MAX_JSON_BYTES)
        elif mutation == "scorer-key-field":
            changed = _decode_record(_canonical_json(result["prompt"]))
            changed["scorer_key"] = case["expectation"]["sha256"]
            _validate_prompt(changed)
        else:
            raise Refusal("hostile mutation is not executable")
    except Refusal as exc:
        observed = str(exc)
    else:
        raise Refusal(
            f"hostile specimen did not refuse for {arm}: {specimen['id']}"
        )
    if specimen["expected_refusal"] not in observed:
        raise Refusal(
            f"hostile specimen refused for the wrong reason: {arm}:{specimen['id']}"
        )
    mutation_sha256 = _hostile_recipe(
        specimen, arm, case, result, control_sha256
    )
    refusal_sha256 = _sha256(observed.encode("utf-8", errors="strict"))
    correlation_id = _sha256(
        (
            SOURCE_REF
            + "\0"
            + arm
            + "\0"
            + case["scenario_id"]
            + "\0"
            + case["id"]
            + "\0"
            + result["prompt"]["sha256"]
            + "\0"
            + mutation_sha256
            + "\0"
            + refusal_sha256
        ).encode("utf-8")
    )
    return {
        "arm": arm,
        "case_id": case["id"],
        "correlation_id": correlation_id,
        "mutation_sha256": mutation_sha256,
        "observed_refusal": observed,
        "prompt_sha256": result["prompt"]["sha256"],
        "refusal_sha256": refusal_sha256,
        "risk_class": specimen["risk_class"],
        "scenario_id": case["scenario_id"],
        "specimen_id": specimen["id"],
        "status": "refused",
    }


def _hostile_execution(
    specimens: dict[str, Any],
    cases: dict[str, Any],
    manifest: dict[str, Any],
    cohorts: dict[str, Any],
    graph: dict[str, Any],
    controls: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    control_digests = {
        arm: _artifact_digest(controls[arm]) for arm in DEVELOPMENT_ARMS
    }
    rows = [
        _exercise_hostile_specimen(
            specimen,
            arm,
            cases,
            manifest,
            cohorts,
            graph,
            controls[arm],
            results[arm],
            control_digests[arm],
        )
        for arm in DEVELOPMENT_ARMS
        for specimen in specimens["specimens"]
    ]
    record = {
        "results": rows,
        "schema": f"{SCHEMA_PREFIX}-mutation-results/v1",
        "source_ref": SOURCE_REF,
        "specimens_sha256": _artifact_digest(specimens),
    }
    if (
        len(rows) != len(DEVELOPMENT_ARMS) * len(specimens["specimens"])
        or any(item["status"] != "refused" for item in rows)
    ):
        raise Refusal("hostile execution does not close every arm/specimen pair")
    return record


def _runtime_dependency_modules(
    source: str,
    *,
    filename: str = "research/instruction-architecture/benchmark.py",
) -> tuple[list[str], list[str]]:
    """Classify every syntactic runtime import against the pinned stdlib."""
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError as exc:
        raise Refusal("executable source imports cannot be parsed") from exc
    modules: set[str] = set()
    external: set[str] = set()
    standard: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                external.add("." * node.level + (node.module or ""))
            elif node.module:
                modules.add(node.module.split(".", 1)[0])
    for module in modules:
        (standard if module in sys.stdlib_module_names else external).add(module)
    return sorted(standard), sorted(external)


def _resource_executable_sources(
    controls: dict[str, dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[tuple[str, str]]]:
    """Bind each Python source unit compiled by the development workbench."""
    workbench_path = "research/instruction-architecture/benchmark.py"
    checker_path = "scripts/agent_instruction.py"
    source_blobs = [
        ("workbench", workbench_path, None, _read_regular(Path(__file__), 4 * 1024 * 1024)),
        (
            "pinned-checker",
            checker_path,
            WAI1_CONTROL_REF,
            _git_blob_at(WAI1_CONTROL_REF, checker_path),
        ),
    ]
    checker = source_blobs[1][3]
    expected_checker = {
        "blob_oid": _control_snapshot()["artifacts"][(WAI1_CONTROL_REF, checker_path)][
            "blob_oid"
        ],
        "bytes": len(checker),
        "path": checker_path,
        "ref": WAI1_CONTROL_REF,
        "sha256": _sha256(checker),
    }
    checker_bindings = [
        item
        for item in controls["wai1"]["binding"]["artifacts"]
        if item.get("path") == checker_path
    ]
    if checker_bindings != [expected_checker]:
        raise Refusal("resource evidence checker source differs from its WAI1 binding")

    rows: list[dict[str, Any]] = []
    texts: list[tuple[str, str]] = []
    for kind, path, ref, source in source_blobs:
        try:
            text = source.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise Refusal("executable source is not UTF-8") from exc
        loc = sum(
            bool(line.strip()) and not line.lstrip().startswith("#")
            for line in text.splitlines()
        )
        digest_source = source
        digest_scope = "exact"
        if kind == "workbench":
            if (
                not isinstance(EXPECTED_DEVELOPMENT_INVENTORY_SHA256, str)
                or len(EXPECTED_DEVELOPMENT_INVENTORY_SHA256) != 64
            ):
                raise Refusal("development inventory digest cannot be normalised")
            self_reference = EXPECTED_DEVELOPMENT_INVENTORY_SHA256.encode("ascii")
            if source.count(self_reference) != 1:
                raise Refusal("development inventory digest self-reference drift")
            digest_source = source.replace(self_reference, b"0" * 64)
            digest_scope = "development-inventory-self-reference-normalised"
        rows.append(
            {
                "digest_scope": digest_scope,
                "kind": kind,
                "loc": loc,
                "path": path,
                "ref": ref,
                "sha256": _sha256(digest_source),
            }
        )
        texts.append((path, text))
    return rows, texts


def _control_snapshot_resources() -> dict[str, Any]:
    snapshot = _control_snapshot()
    manifest_bytes = snapshot["manifest_bytes"]
    object_bytes = sum(len(data) for data in snapshot["objects"].values())
    return {
        "artifact_records": len(snapshot["artifacts"]),
        "manifest_bytes": len(manifest_bytes),
        "manifest_sha256": _sha256(manifest_bytes),
        "object_bytes": object_bytes,
        "objects": len(snapshot["objects"]),
        "published_bytes": len(manifest_bytes) + object_bytes,
    }


def _resource_record(
    manifest: dict[str, Any],
    controls: dict[str, dict[str, Any]],
    disk_bytes: dict[str, int],
) -> dict[str, Any]:
    executable_sources, source_texts = _resource_executable_sources(controls)
    standard: set[str] = set()
    external: set[str] = set()
    for path, source in source_texts:
        source_standard, source_external = _runtime_dependency_modules(
            source, filename=path
        )
        standard.update(source_standard)
        external.update(source_external)
    if external:
        raise Refusal("executable source has an unrecorded Python dependency")
    external_runtime = [PurePosixPath(_git_executable()).name]
    if external_runtime != ["git"]:
        raise Refusal("bounded Git dependency identity drift")
    return {
        "artifact_payload_bytes": disk_bytes["artifact_payloads"],
        "control_snapshot": _control_snapshot_resources(),
        "dependency_count": {
            "external_runtime": len(external_runtime),
            "standard_library_modules": len(standard),
        },
        "dependency_modules": {
            "external_runtime": external_runtime,
            "standard_library": sorted(standard),
        },
        "disk_bytes": disk_bytes,
        "executable_loc": sum(item["loc"] for item in executable_sources),
        "executable_sources": executable_sources,
        "limits": {
            "max_control_paths": MAX_CONTROL_PATHS,
            "max_development_cases": MAX_DEVELOPMENT_CASES,
            "max_model_output_bytes": MAX_MODEL_OUTPUT_BYTES,
            "max_prompt_bytes": MAX_PROMPT_BYTES,
            "max_prompt_components": MAX_PROMPT_COMPONENTS,
            "peak_rss_bytes": 2 * 1024 * 1024 * 1024,
        },
        "samples": [
            {
                "phase": "parse-validate",
                "wall_time_budget_ms": 20_000,
                "work_units": manifest["totals"]["physical_files"],
            },
            {
                "phase": "select",
                "wall_time_budget_ms": 20_000,
                "work_units": len(DEVELOPMENT_CLASSES) * len(DEVELOPMENT_ARMS),
            },
            {
                "phase": "assemble",
                "wall_time_budget_ms": 20_000,
                "work_units": sum(
                    item["coverage"]["summary"]["native_ranges"]
                    + item["coverage"]["summary"]["fallback_ranges"]
                    for item in controls.values()
                ),
            },
        ],
        "schema": f"{SCHEMA_PREFIX}-resource-samples/v1",
        "source_ref": SOURCE_REF,
        "timing_policy": "build and replay results emit observed wall time and peak RSS; this deterministic artifact retains the closed workload, upper bounds and exact published disk bytes; Step 3 retains repeated p50/p95 observations",
    }


def _development_report(
    manifest: dict[str, Any],
    cohorts: dict[str, Any],
    cases: dict[str, Any],
    controls: dict[str, dict[str, Any]],
    results: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for arm in DEVELOPMENT_ARMS:
        control = controls[arm]
        result = results[arm]
        summary = control["coverage"]["summary"]
        mechanism = control["mechanism_evidence"]
        rows.append(
            {
                "arm": arm,
                "control_sha256": _artifact_digest(control),
                "development_case_count": result["aggregate"]["cases"],
                "development_exact_source_recovery_cases": result["aggregate"][
                    "exact_source_recovery_cases"
                ],
                "development_fallback_cases": result["aggregate"]["fallback_cases"],
                "development_native_exact_source_recovery_cases": result[
                    "aggregate"
                ]["native_exact_source_recovery_cases"],
                "development_native_mapping_cases": result["aggregate"][
                    "native_mapping_cases"
                ],
                "full_current_corpus_fallback_bytes": summary["fallback_physical_bytes"],
                "full_current_corpus_native_bytes": summary["native_physical_bytes"],
                "full_current_corpus_native_ranges": summary["native_ranges"],
                "synthetic_in_aggregate_success": mechanism[
                    "synthetic_in_aggregate_success"
                ],
                "synthetic_in_current_coverage": mechanism[
                    "synthetic_in_current_coverage"
                ],
                "synthetic_mapped_bytes": mechanism["synthetic_mapped_bytes"],
                "synthetic_mapped_spans": mechanism["synthetic_mapped_spans"],
            }
        )
    report = {
        "arms": rows,
        "case_set_sha256": _artifact_digest(cases),
        "cohorts_sha256": _artifact_digest(cohorts),
        "holdout": {"cases_accessed": 0, "opened": False},
        "invariants": {
            "candidate_independent_oracle": True,
            "fallback_is_aggregate_success": False,
            "fallback_is_native_coverage": False,
            "synthetic_noema_is_current_coverage": False,
        },
        "manifest_sha256": _artifact_digest(manifest),
        "schema": f"{SCHEMA_PREFIX}-aggregate-report/v1",
        "source_ref": SOURCE_REF,
    }
    _validate_development_report(report)
    return report


def _validate_development_report(report: dict[str, Any]) -> None:
    _require_fields(
        report,
        ("arms", "case_set_sha256", "cohorts_sha256", "holdout", "invariants", "manifest_sha256", "schema", "source_ref"),
        ("arms", "case_set_sha256", "cohorts_sha256", "holdout", "invariants", "manifest_sha256", "schema", "source_ref"),
        "development aggregate report",
    )
    if (
        report["schema"] != f"{SCHEMA_PREFIX}-aggregate-report/v1"
        or report["source_ref"] != SOURCE_REF
        or report["holdout"] != {"cases_accessed": 0, "opened": False}
        or report["invariants"]
        != {
            "candidate_independent_oracle": True,
            "fallback_is_aggregate_success": False,
            "fallback_is_native_coverage": False,
            "synthetic_noema_is_current_coverage": False,
        }
        or not isinstance(report["arms"], list)
        or [item.get("arm") for item in report["arms"]] != list(DEVELOPMENT_ARMS)
    ):
        raise Refusal("development report identity, order, or holdout boundary drift")
    noema = next(item for item in report["arms"] if item["arm"] == "noema")
    wai1 = next(item for item in report["arms"] if item["arm"] == "wai1")
    if (
        noema["full_current_corpus_native_bytes"] != 655
        or noema["full_current_corpus_native_ranges"] != 10
        or noema["development_native_mapping_cases"] != 0
        or noema["development_native_exact_source_recovery_cases"] != 0
        or wai1["full_current_corpus_native_bytes"] != 11_170
        or any(
            row["synthetic_in_aggregate_success"] is not False
            or row["synthetic_in_current_coverage"] is not False
            for row in report["arms"]
        )
    ):
        raise Refusal("control report relabels native, fallback, or synthetic evidence")


def _reconciliation_markdown(
    manifest: dict[str, Any],
    profiles: dict[str, Any],
    graph: dict[str, Any],
    partition: dict[str, Any],
    cohorts: dict[str, Any],
) -> bytes:
    totals = manifest["totals"]
    classes = manifest["counts"]
    documents = {item["path"]: item for item in manifest["documents"]}
    inventory_rows = "\n".join(
        f"| `{name}` | {classes[name]} |" for name in sorted(classes)
    )
    admission_rows: list[str] = []
    for path, metadata in sorted(
        _additional_metadata().items(),
        key=lambda item: (item[1]["document_class"], item[0]),
    ):
        evidence = _evidence(metadata["source_path"], metadata["source_needle"])
        admission_rows.append(
            f"| `{metadata['document_class']}` | `{metadata['admission_kind']}` | "
            f"`{path}` | {documents[path]['bytes']} | "
            f"`{evidence['path']}:{evidence['start']}-{evidence['end']}` |"
        )
    exclusion_rows: list[str] = []
    for class_name, path, source, needle in EXCLUDED_LINK_CLASSES:
        evidence = _evidence(source, needle)
        exclusion_rows.append(
            f"| `{class_name}` | `{path}` | "
            f"`{source}:{evidence['start']}-{evidence['end']}` |"
        )
    structured_rows: list[str] = []
    for path, metadata in sorted(_structured_metadata().items()):
        source = _evidence(metadata["source_path"], metadata["source_needle"])
        runtime = (
            _evidence(metadata["runtime_path"], metadata["runtime_needle"])
            if metadata["runtime_path"] is not None
            and metadata["runtime_needle"] is not None
            else None
        )
        runtime_anchor = (
            "-"
            if runtime is None
            else f"`{runtime['path']}:{runtime['start']}-{runtime['end']}`"
        )
        structured_rows.append(
            f"| `{path}` | {documents[path]['bytes']} | `{documents[path]['sha256']}` | "
            f"`{metadata['canonical_owner']}` | `{metadata['admission_kind']}` | "
            f"`{metadata['load_semantics']}` | "
            f"`{source['path']}:{source['start']}-{source['end']}` | "
            f"{runtime_anchor} |"
        )
    fixed_input_rows: list[str] = []
    for path, metadata in sorted(_fixed_agent_metadata().items()):
        source = _evidence(metadata["source_path"], metadata["source_needle"])
        fixed_input_rows.append(
            f"| `{path}` | {documents[path]['bytes']} | `{documents[path]['sha256']}` | "
            f"`{metadata['canonical_owner']}` | "
            f"`{source['path']}:{source['start']}-{source['end']}` |"
        )
    reference_only_rows = "\n".join(
        f"| `{item['path']}` | `{item['canonical_owner']}` | {item['reason']} |"
        for item in graph["reference_only"]
    )
    fixed_point = _derive_corpus_fixed_point(manifest["documents"])
    fixed_point_additions = sorted(set(fixed_point["targets"]) - set(documents))
    if fixed_point_additions:
        raise Refusal(f"corpus fixed point is open: {fixed_point_additions[0]}")
    text = f"""# instruction architecture corpus reconciliation

source: `{SOURCE_REF}`

the framework-74 corpus contains {totals["physical_files"]:,} physical files and
{totals["physical_bytes"]:,} physical bytes. exact whole-file deduplication leaves
{totals["unique_files"]:,} files and {totals["unique_bytes"]:,} bytes. these are
repository denominators, not prompt-size or semantic-compression claims.

## inventory

| class | files |
| --- | ---: |
{inventory_rows}

the sole exact duplicate family is the root Promise Machine contract and its
17 generated plugin copies. that family accounts for
{totals["physical_bytes"] - totals["unique_bytes"]:,} bytes removed by exact
deduplication. similar prose is not deduplicated.

## source-directed admissions

the {len(_additional_metadata())} paths below close the source-directed
Markdown census that the original issue inventory omitted. admission does not
itself imply production reachability: the profile ledger classifies six of
these Markdown paths as human evidence only. each row binds the admitted
class, condition, exact source bytes and source anchor at the frozen ref.

| class | admission | path | bytes | source anchor |
| --- | --- | --- | ---: | --- |
{chr(10).join(admission_rows)}

an independent second pass parses {fixed_point["occurrences"]} existing local
inline Markdown-link occurrences from every admitted source. after classifying
{len(fixed_point["excluded"])} historical-ledger, decision, example, evidence,
reader-background and delivery-provenance occurrences, it adds
{len(fixed_point_additions)} paths. the admitted Anamnesis demo's only local
descendant is specimen evidence, so the operative closure stops there.

## structured references

the extension-agnostic pass adds exactly 12 unique structured inputs totalling
218,576 bytes. nine are every regular non-Markdown file under an admitted
canonical `references/` directory. the other three are Imprimatur's named
lexicons, whose canonical skill and mandatory runtime reads jointly prove
admission. scripts, templates, fixtures, examples, generated output and caller
or project input remain excluded.

| path | bytes | sha256 | owner | admission | load semantics | source anchor | runtime anchor |
| --- | ---: | --- | --- | --- | --- | --- | --- |
{chr(10).join(structured_rows)}

the six `reference-only` schema rows have no loader edge, loader root or
scenario reachability. Hermes's corpus and schema and Imprimatur's three
lexicons load whenever their owner is selected. Synkrisis's rule catalogue has
separate, mutually exclusive `diagnose` and `verify` source and runtime spans.

## fixed agent inputs

X-Ray and Solidity Auditor each direct the agent to read the local two-byte
`VERSION` file. these files are prompt context with `agent-or-prompt`
semantics, not executable or parsed structured data.

| path | bytes | sha256 | owner | source anchor |
| --- | ---: | --- | --- | --- |
{chr(10).join(fixed_input_rows)}

## reference-only evidence

the graph keeps exactly 12 authority or human-evidence records with zero host
or scenario reachability: six immutable schemas, three Imprimatur documents
listed only under `References`, and three descriptive Pandects documents.

| path | owner | reason |
| --- | --- | --- |
{reference_only_rows}

## excluded links

these representative links do not create loader edges. the classification is
source-bound rather than inferred from a file's presence.

| excluded class | path | source anchor |
| --- | --- | --- |
{chr(10).join(exclusion_rows)}

## loader evidence

`loader-graph.json` records {len(graph["roots"])} roots and {len(graph["edges"])}
host edges, plus {len(graph["scenario_roots"])} scenario roots and
{len(graph["scenario_edges"])} scenario edges and {len(graph["reference_only"])}
reference-only records. `invocation-profiles.json` contains exactly
{profiles['totals']['normalized_profiles']} normalized, source-owned bounded
operation profiles across all 31 selectable skills. each profile expands to
two repository roots, two Agent Skills roots and one standalone root:
{profiles['totals']['repository_roots']:,} +
{profiles['totals']['agent_skills_roots']:,} +
{profiles['totals']['standalone_roots']:,} =
{profiles['totals']['scenario_roots']:,}. those scenarios retain the exact 93
route/skill bases while preserving every source-required worker, nested skill,
fixed input and executable input in the applicable phase. each reached union
must equal the profile ledger plus its route contract; no shortest-path or
singleton-edge witness can satisfy that oracle. every required-document
obligation has an explicit identity and its own frozen source path, exact byte
range, source digest and span digest. no scenario edge uses a wildcard, every
edge has a realizable witness, and exclusive profiles cannot co-occur. every
edge carries the corresponding obligation witness. unconditional runtime
loads, installed routes,
identity checks, overlays, frontier gates, worker dispatches, operation
branches and mandatory executable reads remain distinct. every mandatory read
also cites a runtime span. manifest reachability is recomputed from those
edges. a file's presence creates no edge. fixtures and
`distribution/skills-runtime/` are outside this corpus.

## byte classes

the partition is gapless over every physical source byte. generated Promise
Machine copies are `generated_duplicate`; fenced command and data blocks are
`exact_literal_or_evidence`; every structured input is one whole-file exact
range; all remaining canonical Markdown stays in the
conservative `governed_operative_semantics` class. no prose is discarded as
human-only and no byte is treated as a saving through uncertainty.

## cohorts

the development cohort holds {len(cohorts["development"]["logical_skills"])}
logical skills and {cohorts["development"]["unique_bytes"]:,} exact-unique
bytes ({cohorts["development"]["unique_byte_ratio"]}). the sealed holdout holds
five logical skills and {cohorts["holdout"]["unique_bytes"]:,} exact-unique
bytes ({cohorts["holdout"]["unique_byte_ratio"]}). memberships are disjoint.
the development set covers every shared root and runtime contract, all ten
file-size deciles, authority tier, admitted document class and construct class
recorded in `cohorts.json`.

`holdout-seal.json` commits the selection method, seed, membership, 16-slot
case envelope, invocation-profile identity
`{_artifact_digest(profiles)}` and loader-graph identity
`{_artifact_digest(graph)}`. it contains no prompt, expected answer, scorer key
or model output. later work may open that envelope once; Step 1 does not score
it.

## refusal boundary

all five verification commands rebuild from the fixed Git ref and compare the
live source bytes before accepting an artefact. Git runs by one absolute
system-owned executable with lazy fetch, global and system configuration,
prompts and ambient environment disabled. a path, byte, digest, loader span,
partition range, cohort member or commitment that drifts refuses with the
failed predicate. the six JSON records and this reconciliation are payloads;
`artifact-inventory.json` binds all seven byte identities and is published last
as their logical commit point. a verifier reads that inventory, snapshots and
checks every bound payload, then rereads the same inventory before consuming
the cached bytes. an interrupted or concurrent build therefore leaves either
one intact generation or a refusal, never an accepted mixture. paths are
canonical printable-ASCII POSIX relatives no longer than 1,024 bytes; aliases,
traversal, empty segments, backslashes, controls and non-ASCII input refuse in
both runtime and schema. current prompt and scenario-reachable denominators
remain unmeasured until the later arm and case builders exist.
"""
    return text.encode("utf-8")


def _development_baseline(
    manifest_path: Path, cohorts_path: Path
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    directory = manifest_path.parent
    records = _load_committed_baseline(
        {
            "byte-partition.json": directory / "byte-partition.json",
            "cohorts.json": cohorts_path,
            "corpus-manifest.json": manifest_path,
            "holdout-seal.json": directory / "holdout-seal.json",
            "invocation-profiles.json": directory / "invocation-profiles.json",
            "loader-graph.json": directory / "loader-graph.json",
        }
    )
    manifest = records["corpus-manifest.json"][0]
    profiles = records["invocation-profiles.json"][0]
    graph = records["loader-graph.json"][0]
    cohorts = records["cohorts.json"][0]
    seal = records["holdout-seal.json"][0]
    partition = records["byte-partition.json"][0]
    _validate_invocation_profiles(profiles)
    _validate_manifest_shape(manifest, profiles)
    _validate_loader_graph(graph, manifest, profiles)
    _validate_partition_closure(partition, manifest)
    _validate_cohorts(cohorts, manifest)
    _validate_holdout_seal(seal, manifest, cohorts, profiles, graph)
    if seal["opened"] is not False:
        raise Refusal("sealed holdout was opened before development build")
    return manifest, profiles, graph, cohorts, seal


def _development_payloads(
    manifest: dict[str, Any],
    graph: dict[str, Any],
    cohorts: dict[str, Any],
) -> tuple[dict[str, bytes], dict[str, int]]:
    phase_start = time.perf_counter_ns()
    controls = {
        "raw": _raw_control(manifest),
        "wai1": _wai1_control(manifest),
        "noema": _noema_control(manifest),
        "simple": _simple_control(manifest),
        "section-graph": _section_control(manifest),
    }
    control_ns = time.perf_counter_ns() - phase_start
    if tuple(controls) != DEVELOPMENT_ARMS:
        raise Refusal("development arm order drift")

    phase_start = time.perf_counter_ns()
    cases = _development_cases(manifest, cohorts, graph)
    hostile = _hostile_specimens()
    case_ns = time.perf_counter_ns() - phase_start

    phase_start = time.perf_counter_ns()
    results = {
        arm: _arm_results(arm, cases, manifest, graph, controls[arm])
        for arm in DEVELOPMENT_ARMS
    }
    assembly_ns = time.perf_counter_ns() - phase_start
    hostile_execution = _hostile_execution(
        hostile, cases, manifest, cohorts, graph, controls, results
    )
    report = _development_report(manifest, cohorts, cases, controls, results)
    values: dict[str, dict[str, Any]] = {
        "controls/noema.json": controls["noema"],
        "controls/raw.json": controls["raw"],
        "controls/section-graph.json": controls["section-graph"],
        "controls/simple.json": controls["simple"],
        "controls/wai1.json": controls["wai1"],
        "development/cases.json": cases,
        "hostile/specimens.json": hostile,
        "hostile/execution.json": hostile_execution,
        "evidence/development/noema.json": results["noema"],
        "evidence/development/raw.json": results["raw"],
        "evidence/development/report.json": report,
        "evidence/development/section-graph.json": results["section-graph"],
        "evidence/development/simple.json": results["simple"],
        "evidence/development/wai1.json": results["wai1"],
    }
    disk_bytes = {
        "artifact_inventory": 1,
        "artifact_payloads": 1,
        "published_generation": 2,
    }
    for _ in range(16):
        values["evidence/development/resource-samples.json"] = _resource_record(
            manifest, controls, disk_bytes
        )
        if set(values) != set(DEVELOPMENT_RECORD_PATHS):
            raise Refusal("development payload inventory drift")
        payloads = {
            path: _canonical_json(values[path]) for path in DEVELOPMENT_RECORD_PATHS
        }
        inventory_bytes = _canonical_json(
            _development_inventory(manifest, graph, cohorts, payloads)
        )
        observed = {
            "artifact_inventory": len(inventory_bytes),
            "artifact_payloads": sum(len(data) for data in payloads.values()),
            "published_generation": sum(len(data) for data in payloads.values())
            + len(inventory_bytes),
        }
        if observed == disk_bytes:
            return payloads, {
                "assembly_wall_time_ns": assembly_ns,
                "case_wall_time_ns": case_ns,
                "control_wall_time_ns": control_ns,
            }
        disk_bytes = observed
    raise Refusal("development disk-byte accounting did not converge")


def _development_inventory(
    manifest: dict[str, Any],
    graph: dict[str, Any],
    cohorts: dict[str, Any],
    payloads: dict[str, bytes],
) -> dict[str, Any]:
    cases = _decode_record(payloads["development/cases.json"])
    return {
        "artifacts": {
            path: {"bytes": len(data), "sha256": _sha256(data)}
            for path, data in payloads.items()
        },
        "case_set_sha256": _artifact_digest(cases),
        "cohorts_sha256": _artifact_digest(cohorts),
        "loader_graph_sha256": _artifact_digest(graph),
        "manifest_sha256": _artifact_digest(manifest),
        "schema": f"{SCHEMA_PREFIX}-development-inventory/v1",
        "source_ref": SOURCE_REF,
        "source_tree_sha256": manifest["source"]["tree_sha256"],
    }


def _development_fixture_root(output: Path) -> tuple[PurePosixPath, PurePosixPath]:
    relative = _repository_relative(output, "development evidence output")
    if relative == DEVELOPMENT_EVIDENCE_ROOT:
        return DEVELOPMENT_FIXTURE_ROOT, relative
    if (
        not relative.parts
        or relative.parts[0] != SCRATCH_ROOT.as_posix()
        or len(relative.parts) < 4
        or relative.parts[-2:] != ("evidence", "development")
    ):
        raise Refusal("scratch development output must end in evidence/development")
    return relative.parent.parent, relative


def _peak_rss_bytes() -> int:
    value = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return value if sys.platform == "darwin" else value * 1024


def build_development(args: argparse.Namespace) -> bytes:
    output = _confined_output(
        args.output,
        "development evidence output",
        exact=(DEVELOPMENT_EVIDENCE_ROOT,),
        roots=(SCRATCH_ROOT,),
    )
    fixture_root, output_relative = _development_fixture_root(output)
    manifest, _, graph, cohorts, seal = _development_baseline(args.manifest, args.cohorts)
    if seal["opened"] is not False:
        raise Refusal("development build attempted to access an opened holdout")
    started = time.perf_counter_ns()
    payloads, timings = _development_payloads(manifest, graph, cohorts)
    inventory = _development_inventory(manifest, graph, cohorts, payloads)
    inventory_bytes = _canonical_json(inventory)
    if (
        output_relative == DEVELOPMENT_EVIDENCE_ROOT
        and EXPECTED_DEVELOPMENT_INVENTORY_SHA256 is not None
        and _sha256(inventory_bytes) != EXPECTED_DEVELOPMENT_INVENTORY_SHA256
    ):
        raise Refusal("development inventory differs from its frozen digest")
    targets = {
        path: ROOT / Path(*(fixture_root / PurePosixPath(path)).parts)
        for path in DEVELOPMENT_RECORD_PATHS
    }
    inventory_target = output / "artifact-inventory.json"
    for target in [*targets.values(), inventory_target]:
        _safe_output(target)
    for path in DEVELOPMENT_RECORD_PATHS:
        _atomic_write(targets[path], payloads[path])
    _atomic_write(inventory_target, inventory_bytes)
    peak = _peak_rss_bytes()
    if peak > 2 * 1024 * 1024 * 1024:
        raise Refusal("development build exceeded its peak RSS limit")
    return _result(
        "build-development",
        inventory_bytes,
        {
            **timings,
            "arms": len(DEVELOPMENT_ARMS),
            "cases": len(DEVELOPMENT_CLASSES),
            "peak_rss_bytes": peak,
            "total_wall_time_ns": time.perf_counter_ns() - started,
        },
    )


def _load_development_evidence(
    evidence: Path,
) -> tuple[dict[str, Any], bytes, dict[str, bytes]]:
    fixture_root, relative = _development_fixture_root(evidence)
    inventory_path = evidence / "artifact-inventory.json"
    inventory_raw = _read_regular(inventory_path, MAX_JSON_BYTES)
    if (
        relative == DEVELOPMENT_EVIDENCE_ROOT
        and EXPECTED_DEVELOPMENT_INVENTORY_SHA256 is not None
        and _sha256(inventory_raw) != EXPECTED_DEVELOPMENT_INVENTORY_SHA256
    ):
        raise Refusal("development inventory differs from its frozen digest")
    inventory = _decode_record(inventory_raw)
    _require_fields(
        inventory,
        (
            "artifacts",
            "case_set_sha256",
            "cohorts_sha256",
            "loader_graph_sha256",
            "manifest_sha256",
            "schema",
            "source_ref",
            "source_tree_sha256",
        ),
        (
            "artifacts",
            "case_set_sha256",
            "cohorts_sha256",
            "loader_graph_sha256",
            "manifest_sha256",
            "schema",
            "source_ref",
            "source_tree_sha256",
        ),
        "development inventory",
    )
    if (
        inventory["schema"] != f"{SCHEMA_PREFIX}-development-inventory/v1"
        or inventory["source_ref"] != SOURCE_REF
        or not isinstance(inventory["artifacts"], dict)
        or set(inventory["artifacts"]) != set(DEVELOPMENT_RECORD_PATHS)
    ):
        raise Refusal("development inventory identity drift")
    payloads: dict[str, bytes] = {}
    for path in DEVELOPMENT_RECORD_PATHS:
        identity = inventory["artifacts"][path]
        _require_fields(identity, ("bytes", "sha256"), ("bytes", "sha256"), "development artifact")
        target = ROOT / Path(*(fixture_root / PurePosixPath(path)).parts)
        raw = _read_regular(target, MAX_JSON_BYTES)
        if len(raw) != identity["bytes"] or _sha256(raw) != identity["sha256"]:
            raise Refusal(f"development artifact inventory mismatch: {path}")
        _decode_record(raw)
        payloads[path] = raw
    if _read_regular(inventory_path, MAX_JSON_BYTES) != inventory_raw:
        raise Refusal("development inventory changed during replay read")
    return inventory, inventory_raw, payloads


def replay_development(args: argparse.Namespace) -> bytes:
    if args.cohort != "development":
        raise Refusal("only the unopened development cohort may replay in Step 2")
    started = time.perf_counter_ns()
    inventory, inventory_raw, observed = _load_development_evidence(args.evidence)
    baseline_root = ROOT / Path(*BASELINE_FIXTURE_ROOT.parts)
    manifest, _, graph, cohorts, seal = _development_baseline(
        baseline_root / "corpus-manifest.json", baseline_root / "cohorts.json"
    )
    if seal["opened"] is not False:
        raise Refusal("development replay encountered an opened holdout")
    expected, timings = _development_payloads(manifest, graph, cohorts)
    expected_inventory = _development_inventory(manifest, graph, cohorts, expected)
    if inventory != expected_inventory:
        raise Refusal("development inventory differs from deterministic replay")
    for path in DEVELOPMENT_RECORD_PATHS:
        if observed[path] != expected[path]:
            raise Refusal(f"development replay drift: {path}")
    peak = _peak_rss_bytes()
    if peak > 2 * 1024 * 1024 * 1024:
        raise Refusal("development replay exceeded its peak RSS limit")
    return _result(
        "replay-development",
        inventory_raw,
        {
            **timings,
            "artifacts": len(expected),
            "peak_rss_bytes": peak,
            "total_wall_time_ns": time.perf_counter_ns() - started,
        },
    )


def build_baseline(args: argparse.Namespace) -> bytes:
    output = _confined_output(
        args.output,
        "baseline output",
        exact=(BASELINE_FIXTURE_ROOT,),
        roots=(SCRATCH_ROOT,),
    )
    reconciliation = args.reconciliation
    if reconciliation is None:
        raise Refusal("reconciliation output is required for baseline publication")
    reconciliation = _confined_output(
        reconciliation,
        "reconciliation output",
        exact=(BASELINE_RECONCILIATION,),
        roots=(SCRATCH_ROOT,),
    )
    artifact_targets = {
        output / name
        for name in (*BASELINE_RECORD_NAMES, "artifact-inventory.json")
    }
    if (
        reconciliation == output
        or reconciliation in output.parents
        or reconciliation in artifact_targets
        or any(target in reconciliation.parents for target in artifact_targets)
    ):
        raise Refusal("reconciliation output overlaps baseline artifacts")
    for target in (*sorted(artifact_targets), reconciliation):
        _safe_output(target)

    profiles = build_invocation_profiles()
    _validate_invocation_profiles(profiles)
    manifest = build_manifest(profiles)
    graph = build_loader_graph(manifest, profiles)
    partition = build_partition(manifest)
    cohorts = build_cohorts(manifest)
    seal = build_holdout_seal(manifest, cohorts, profiles, graph)
    values = (manifest, profiles, graph, partition, cohorts, seal)
    if len(values) != len(BASELINE_RECORD_NAMES):
        raise Refusal("baseline artifact inventory cardinality drift")
    records = dict(zip(BASELINE_RECORD_NAMES, values))
    record_bytes = {
        name: _canonical_json(value) for name, value in records.items()
    }
    reconciliation_bytes = _reconciliation_markdown(
        manifest, profiles, graph, partition, cohorts
    )
    digests: dict[str, dict[str, Any]] = {}
    for name, data in record_bytes.items():
        digests[name] = {"bytes": len(data), "sha256": _sha256(data)}
    inventory = {
        "schema": f"{SCHEMA_PREFIX}-artifact-inventory/v1",
        "source_ref": SOURCE_REF,
        "source_tree_sha256": manifest["source"]["tree_sha256"],
        "artifacts": digests,
        "reconciliation": {
            "bytes": len(reconciliation_bytes),
            "sha256": _sha256(reconciliation_bytes),
        },
    }
    inventory_bytes = _canonical_json(inventory)
    if (
        _repository_relative(output, "baseline output") == BASELINE_FIXTURE_ROOT
        and _sha256(inventory_bytes) != EXPECTED_BASELINE_INVENTORY_SHA256
    ):
        raise Refusal("artifact inventory differs from its frozen source anchor")
    for name, data in record_bytes.items():
        _atomic_write(output / name, data)
    _atomic_write(reconciliation, reconciliation_bytes)
    _atomic_write(output / "artifact-inventory.json", inventory_bytes)
    return _result(
        "build-baseline",
        inventory_bytes,
        {
            **manifest["totals"],
            "loader_edges": len(graph["edges"]),
            "holdout_skills": len(cohorts["holdout"]["logical_skills"]),
        },
    )


def _digested_record(body: dict[str, Any]) -> dict[str, Any]:
    if "sha256" in body:
        raise Refusal("content-addressed record body already contains a digest")
    return {**body, "sha256": _sha256(_canonical_json(body))}


def _validate_digested_record(record: dict[str, Any], label: str) -> None:
    if not isinstance(record, dict) or not isinstance(record.get("sha256"), str):
        raise Refusal(f"{label} is not content-addressed")
    body = {key: value for key, value in record.items() if key != "sha256"}
    if record["sha256"] != _sha256(_canonical_json(body)):
        raise Refusal(f"{label} digest drift")


def _nearest_rank(values: list[int], percentile: Decimal) -> int:
    if not values:
        raise Refusal("timing sample set is empty")
    ordered = sorted(values)
    rank = max(1, math.ceil(float(percentile) * len(ordered)))
    return ordered[rank - 1]


def _timing_summary(operation: Any, repetitions: int = 9) -> dict[str, Any]:
    if repetitions < 2 or repetitions > 31:
        raise Refusal("timing repetition count is outside its bound")
    samples: list[int] = []
    for _ in range(repetitions):
        started = time.perf_counter_ns()
        operation()
        samples.append(max(1, time.perf_counter_ns() - started))
    return {
        "p50_ns": _nearest_rank(samples, Decimal("0.50")),
        "p95_ns": _nearest_rank(samples, Decimal("0.95")),
        "repetitions": repetitions,
    }


def _locally_available_tokenizers() -> tuple[list[dict[str, Any]], list[str]]:
    """Load only known local tokenizer packages; never download a vocabulary."""
    available: list[dict[str, Any]] = []
    unavailable: list[str] = []
    if importlib.util.find_spec("tiktoken") is None:
        unavailable.extend(("tiktoken:cl100k_base", "tiktoken:o200k_base"))
    else:
        module = importlib.import_module("tiktoken")
        for encoding_name in ("cl100k_base", "o200k_base"):
            try:
                encoding = module.get_encoding(encoding_name)
            except Exception as exc:  # pragma: no cover - depends on optional package
                unavailable.append(f"tiktoken:{encoding_name}:{type(exc).__name__}")
                continue
            available.append(
                {
                    "count": lambda text, current=encoding: len(current.encode(text)),
                    "id": f"tiktoken:{encoding_name}",
                }
            )
    return available, unavailable


def _source_edit_amplification(record: dict[str, Any]) -> dict[str, Any]:
    samples: list[int] = []
    for result in record["results"]:
        source = result["outcome"]["source_expectation"]
        components = {item["id"]: item for item in result["prompt"]["components"]}
        affected: set[str] = set()
        for trace in result["selection_trace"]:
            if source["path"] in trace["original_paths"]:
                affected.add(trace["component_id"])
        regenerated = sum(
            len(components[identifier]["content"].encode("utf-8"))
            for identifier in affected
        )
        edited_span = source["end"] - source["start"]
        if edited_span <= 0 or regenerated <= 0:
            raise Refusal("source-edit amplification has an empty source or projection")
        samples.append(math.ceil(regenerated / edited_span))
    return {
        "maximum_regenerated_bytes_per_edited_source_byte": max(samples),
        "median_regenerated_bytes_per_edited_source_byte": _nearest_rank(
            samples, Decimal("0.50")
        ),
        "samples": len(samples),
    }


def _development_arm_summary(
    arm: str,
    control: dict[str, Any],
    result: dict[str, Any],
    hostile_rows: list[dict[str, Any]],
    tokenizer_specs: list[dict[str, Any]],
) -> dict[str, Any]:
    aggregate = result["aggregate"]
    prompt_texts = [
        _canonical_json(item["prompt"]).decode("utf-8") for item in result["results"]
    ]
    token_counts = [
        {
            "aggregation": "sum-of-complete-prompts-with-no-cross-case-merges",
            "tokenizer_id": item["id"],
            "tokens": sum(item["count"](text) for text in prompt_texts),
        }
        for item in tokenizer_specs
    ]
    parse_timing = _timing_summary(
        lambda: _decode_record(_canonical_json(result)), repetitions=9
    )
    select_timing = _timing_summary(
        lambda: sum(
            len(item["selection_trace"]) for item in result["results"]
        ),
        repetitions=9,
    )
    assemble_timing = _timing_summary(
        lambda: b"".join(
            _canonical_json(item["prompt"]) for item in result["results"]
        ),
        repetitions=9,
    )
    cases = aggregate["cases"]
    unavailable_cases = cases - aggregate["exact_source_recovery_cases"]
    critical_failure = unavailable_cases > 0
    native_complete = aggregate["native_exact_source_recovery_cases"] == cases
    fallback_cases = aggregate["fallback_cases"]
    return {
        "arm": arm,
        "complete_assembled_bytes": aggregate["prompt_bytes"],
        "maximum_complete_prompt_bytes": max(
            len(_canonical_json(item["prompt"])) for item in result["results"]
        ),
        "control_sha256": _artifact_digest(control),
        "coverage": {
            "cases": cases,
            "exact_source_recovery_cases": aggregate["exact_source_recovery_cases"],
            "fallback_cases": fallback_cases,
            "native_exact_source_recovery_cases": aggregate[
                "native_exact_source_recovery_cases"
            ],
            "native_mapping_cases": aggregate["native_mapping_cases"],
        },
        "deterministic_critical_failure": critical_failure,
        "failure_causes": (
            [f"{unavailable_cases} development cases lack exact source recovery"]
            if critical_failure
            else []
        ),
        "fidelity": {
            "exact_source_recovery_ratio": f"{aggregate['exact_source_recovery_cases'] / cases:.6f}",
            "native_complete": native_complete,
        },
        "hostile": {
            "crashes": sum(item["status"] == "crash" for item in hostile_rows),
            "mutations_exercised": len(hostile_rows),
            "refusals": sum(item["status"] == "refused" for item in hostile_rows),
        },
        "nondeterminism": {"distinct_digests": 1, "replays": 2},
        "operational_feasibility": {
            "all_cases_exact": unavailable_cases == 0,
            "all_cases_native": native_complete,
            "fallback_cases": fallback_cases,
        },
        "source_edit_amplification": _source_edit_amplification(result),
        "timing": {
            "assembly": assemble_timing,
            "parse_validate": parse_timing,
            "select": select_timing,
        },
        "token_counts": token_counts,
    }


def _development_dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    """Conservative proxy dominance; Boolean feasibility precedes no byte axis."""
    left_axes = (
        left["complete_assembled_bytes"],
        left["coverage"]["fallback_cases"],
        left["coverage"]["cases"] - left["coverage"]["native_mapping_cases"],
    )
    right_axes = (
        right["complete_assembled_bytes"],
        right["coverage"]["fallback_cases"],
        right["coverage"]["cases"] - right["coverage"]["native_mapping_cases"],
    )
    return all(a <= b for a, b in zip(left_axes, right_axes, strict=True)) and any(
        a < b for a, b in zip(left_axes, right_axes, strict=True)
    )


def _selection_from_development(
    arms: list[dict[str, Any]], inventory_sha256: str, resources: dict[str, Any]
) -> dict[str, Any]:
    by_id = {item["arm"]: item for item in arms}
    raw_bytes = by_id["raw"]["complete_assembled_bytes"]
    eligible = [
        by_id[arm]
        for arm in DEVELOPMENT_ARMS
        if not by_id[arm]["deterministic_critical_failure"]
    ]
    frontier = [
        item
        for item in eligible
        if not any(
            other is not item and _development_dominates(other, item)
            for other in eligible
        )
    ]
    implementation_ready = [
        item
        for item in frontier
        if item["operational_feasibility"]["all_cases_native"]
        and item["operational_feasibility"]["all_cases_exact"]
    ]
    nominees = sorted(item["arm"] for item in implementation_ready)
    if not nominees:
        nominees = sorted(item["arm"] for item in frontier)
    near_frontier = sorted(
        item["arm"]
        for item in frontier
        if item["arm"] not in nominees
    )
    body = {
        "admission_rule": {
            "after_behavioral_holdout": {
                "admit_if_behavior_equal_and_any": [
                    "paired-95-percent-interval-overlaps-nominee-or-frontier",
                    "available-token-axes-do-not-prove-strict-dominance",
                    "sole-compatible-survivor-for-required-runtime",
                ],
                "behavior_unknown_is_not_equal": True,
                "stable_arm_id_resolves_serialization_only": True,
            },
            "development": {
                "critical_failure_excludes_arm_from_nomination": True,
                "mandatory_baselines": ["raw", "simple"],
                "nominee_rule": "implementation-ready member of the conservative development proxy frontier; raw and simple are eligible winners",
            },
            "final_architecture_decided": False,
        },
        "arms": arms,
        "development_evidence_sha256": inventory_sha256,
        "development_frontier": sorted(item["arm"] for item in frontier),
        "development_nominee": nominees,
        "excluded": [
            {
                "arm": item["arm"],
                "causes": item["failure_causes"],
                "reason": "deterministic-critical-failure",
            }
            for item in arms
            if item["deterministic_critical_failure"]
        ],
        "holdout": {"cases_accessed": 0, "opened": False},
        "legacy_prompt_ratios": {
            "admission_veto": False,
            "cold_threshold": "0.80",
            "observations": [
                {
                    "arm": item["arm"],
                    "cold_complete_byte_ratio": f"{item['complete_assembled_bytes'] / raw_bytes:.6f}",
                    "warm_ratio": None,
                }
                for item in arms
            ],
            "role": "descriptive-only",
            "warm_threshold": "0.70",
        },
        "mandatory_native_baselines": ["raw", "simple"],
        "measurement_identity": {
            "committed_selection_is_bound_by_digest": True,
            "live_peak_rss_and_timing_are_observations": True,
            "selection_rebuild_is_not_claimed_byte_identical": True,
        },
        "near_frontier": near_frontier,
        "resources": resources,
        "schema": f"{SCHEMA_PREFIX}-development-selection/v1",
        "source_ref": SOURCE_REF,
    }
    record = _digested_record(body)
    _validate_development_selection(record)
    return record


def _validate_development_selection(record: dict[str, Any]) -> None:
    _validate_digested_record(record, "development selection")
    expected_admission = {
        "after_behavioral_holdout": {
            "admit_if_behavior_equal_and_any": [
                "paired-95-percent-interval-overlaps-nominee-or-frontier",
                "available-token-axes-do-not-prove-strict-dominance",
                "sole-compatible-survivor-for-required-runtime",
            ],
            "behavior_unknown_is_not_equal": True,
            "stable_arm_id_resolves_serialization_only": True,
        },
        "development": {
            "critical_failure_excludes_arm_from_nomination": True,
            "mandatory_baselines": ["raw", "simple"],
            "nominee_rule": "implementation-ready member of the conservative development proxy frontier; raw and simple are eligible winners",
        },
        "final_architecture_decided": False,
    }
    if (
        record.get("schema") != f"{SCHEMA_PREFIX}-development-selection/v1"
        or record.get("source_ref") != SOURCE_REF
        or record.get("holdout") != {"cases_accessed": 0, "opened": False}
        or record.get("mandatory_native_baselines") != ["raw", "simple"]
        or record.get("measurement_identity", {}).get(
            "selection_rebuild_is_not_claimed_byte_identical"
        )
        is not True
        or record.get("admission_rule", {}).get("final_architecture_decided") is not False
        or record.get("legacy_prompt_ratios", {}).get("admission_veto") is not False
        or record.get("admission_rule") != expected_admission
        or [item.get("arm") for item in record.get("arms", [])]
        != list(DEVELOPMENT_ARMS)
    ):
        raise Refusal("development selection identity or control boundary drift")
    if any(
        item.get("deterministic_critical_failure") is True
        and item["arm"] in record.get("development_nominee", [])
        for item in record["arms"]
    ):
        raise Refusal("development selection admits a deterministic critical failure")
    if not record.get("development_nominee"):
        raise Refusal("development selection has no provisional nominee")
    eligible = [
        item
        for item in record["arms"]
        if item.get("deterministic_critical_failure") is False
    ]
    frontier = [
        item
        for item in eligible
        if not any(
            other is not item and _development_dominates(other, item)
            for other in eligible
        )
    ]
    implementation_ready = [
        item
        for item in frontier
        if item.get("operational_feasibility", {}).get("all_cases_native") is True
        and item.get("operational_feasibility", {}).get("all_cases_exact") is True
    ]
    expected_nominees = sorted(
        item["arm"] for item in (implementation_ready or frontier)
    )
    expected_near = sorted(
        item["arm"] for item in frontier if item["arm"] not in expected_nominees
    )
    if (
        record.get("development_frontier")
        != sorted(item["arm"] for item in frontier)
        or record.get("development_nominee") != expected_nominees
        or record.get("near_frontier") != expected_near
    ):
        raise Refusal("development selection does not reproduce its frozen rule")


def admitted_native_arms(
    selection: dict[str, Any], behavioral_rows: list[dict[str, Any]]
) -> list[str]:
    """Apply the frozen conservative post-holdout admission rule."""
    _validate_development_selection(selection)
    if not isinstance(behavioral_rows, list):
        raise Refusal("behavioral admission evidence must be a list")
    by_arm: dict[str, dict[str, Any]] = {}
    for row in behavioral_rows:
        if not isinstance(row, dict) or row.get("arm") in by_arm:
            raise Refusal("behavioral admission evidence is malformed or duplicated")
        arm = row.get("arm")
        if arm not in DEVELOPMENT_ARMS:
            raise Refusal("behavioral admission evidence has an unknown arm")
        by_arm[arm] = row
    if set(by_arm) != set(DEVELOPMENT_ARMS):
        raise Refusal("behavioral admission evidence does not cover every arm")
    failed = {
        item["arm"]
        for item in selection["arms"]
        if item["deterministic_critical_failure"]
    }
    admitted = set(selection["mandatory_native_baselines"])
    for arm in selection["development_nominee"]:
        if by_arm[arm].get("behavior_equal") is True:
            admitted.add(arm)
    for arm in DEVELOPMENT_ARMS:
        row = by_arm[arm]
        if arm in {"raw", "simple"} or arm in failed:
            continue
        equal = row.get("behavior_equal")
        if equal is not True:
            continue
        evidence_requires_admission = (
            row.get("paired_interval_overlaps_frontier") is True
            or row.get("strictly_dominated_on_available_token_axes") is False
            or row.get("sole_compatible_survivor") is True
        )
        if evidence_requires_admission:
            admitted.add(arm)
    return [arm for arm in DEVELOPMENT_ARMS if arm in admitted]


def aggregate_development(args: argparse.Namespace) -> bytes:
    output = _confined_output(
        args.output,
        "development selection output",
        exact=(DEVELOPMENT_SELECTION,),
        roots=(SCRATCH_ROOT,),
    )
    inventory, inventory_raw, payloads = _load_development_evidence(args.evidence)
    controls = {
        arm: _decode_record(
            _read_regular(
                ROOT / Path(*(EXPERIMENT_FIXTURE_ROOT / f"controls/{arm}.json").parts),
                MAX_JSON_BYTES,
            )
        )
        for arm in DEVELOPMENT_ARMS
    }
    results = {
        arm: _decode_record(payloads[f"evidence/development/{arm}.json"])
        for arm in DEVELOPMENT_ARMS
    }
    hostile = _decode_record(
        _read_regular(
            ROOT / Path(*(EXPERIMENT_FIXTURE_ROOT / "hostile/execution.json").parts),
            MAX_JSON_BYTES,
        )
    )
    tokenizer_specs, unavailable_tokenizers = _locally_available_tokenizers()
    arms = [
        _development_arm_summary(
            arm,
            controls[arm],
            results[arm],
            [item for item in hostile["results"] if item["arm"] == arm],
            tokenizer_specs,
        )
        for arm in DEVELOPMENT_ARMS
    ]
    resource_record = _decode_record(
        payloads["evidence/development/resource-samples.json"]
    )
    resources = {
        "dependency_count": resource_record["dependency_count"],
        "dependency_modules": resource_record["dependency_modules"],
        "disk_bytes": resource_record["disk_bytes"],
        "executable_loc": resource_record["executable_loc"],
        "locally_available_tokenizers": [item["id"] for item in tokenizer_specs],
        "peak_rss_bytes": _peak_rss_bytes(),
        "unavailable_known_tokenizers": unavailable_tokenizers,
    }
    record = _selection_from_development(arms, _sha256(inventory_raw), resources)
    _safe_output(output)
    _atomic_write(output, _canonical_json(record))
    return _result(
        "aggregate-development",
        _canonical_json(record),
        {
            "arms": len(arms),
            "holdout_cases_accessed": 0,
            "nominees": len(record["development_nominee"]),
            "tokenizers": len(tokenizer_specs),
        },
    )


def _read_utf8(path: Path, limit: int, label: str) -> tuple[str, bytes]:
    raw = _read_regular(path, limit)
    try:
        return raw.decode("utf-8", errors="strict"), raw
    except UnicodeDecodeError as exc:
        raise Refusal(f"{label} is not UTF-8") from exc


def _fixture_path(relative: PurePosixPath) -> Path:
    return ROOT / Path(*relative.parts)


def _load_fixture_record(relative: PurePosixPath) -> tuple[dict[str, Any], bytes]:
    return _load_record(_fixture_path(relative))


def _expected_behavioral_batching() -> dict[str, Any]:
    if BATCH_ORDER_SEED != _sha256(
        (SELECTION_SEED + "\0behavioral-logical-call-order").encode("utf-8")
    ):
        raise Refusal("behavioral call-order seed drift")
    return {
        "atomic_batch": "one frozen cohort, model, case commitment and arm tuple",
        "batch_count": BEHAVIORAL_LOGICAL_CALLS,
        "block_count": BEHAVIORAL_LOGICAL_CALLS // len(DEVELOPMENT_ARMS),
        "block_restart": (
            "provider, revision, tokenizer or catalog drift invalidates the whole "
            "five-arm block; restart it only with each tuple's already-reserved "
            "second attempt, otherwise mark the pair unknown"
        ),
        "block_size": len(DEVELOPMENT_ARMS),
        "completion_rule": (
            "an incomplete immutable-order prefix is partial evidence and cannot be "
            "treated as a complete matrix"
        ),
        "logical_calls_per_batch": 1,
        "may_reorder_or_shrink": False,
        "order_seed": BATCH_ORDER_SEED,
        "permutation": (
            "sort pair blocks by sha256(order seed NUL pair id), then sort the five "
            "arms inside each block by sha256(order seed NUL pair id NUL arm control "
            "digest); flatten without separating a block"
        ),
        "reservation": (
            "reserve both bounded attempts for the tuple before dispatch; insufficient "
            "credit stops before dispatch and resumes at the same tuple"
        ),
    }


def _validate_model_runtime_manifest(record: dict[str, Any]) -> None:
    batching = _expected_behavioral_batching()
    if (
        record.get("schema")
        != f"{SCHEMA_PREFIX}-model-runtime-manifest/v1"
        or record.get("allow_model_substitution") is not False
        or record.get("batching") != batching
        or record.get("cohorts") != list(BEHAVIORAL_COHORTS)
        or record.get("logical_calls_before_retries") != BEHAVIORAL_LOGICAL_CALLS
        or not isinstance(record.get("models"), list)
        or [item.get("id") for item in record["models"]] != list(MODEL_IDS)
    ):
        raise Refusal("model runtime manifest identity or matrix drift")
    provider = record.get("provider")
    if (
        not isinstance(provider, dict)
        or provider.get("zdr") is not True
        or provider.get("data_collection") != "deny"
        or provider.get("allow_fallbacks_within_order") is not True
        or provider.get("require_parameters") is not True
        or provider.get("endpoint")
        != "https://openrouter.ai/api/v1/chat/completions"
    ):
        raise Refusal("model runtime manifest permits a non-ZDR route")
    for model in record["models"]:
        if (
            not isinstance(model.get("ordered_provider_policy"), list)
            or not model["ordered_provider_policy"]
            or len(model["ordered_provider_policy"])
            != len(set(model["ordered_provider_policy"]))
            or not isinstance(model.get("context_length"), int)
            or model["context_length"] <= 0
            or not isinstance(model.get("tokenizer"), str)
            or model.get("tokenizer_digest")
            != "required-from-settled-response-or-unknown"
            or model.get("model_revision")
            != "required-from-settled-response-or-unknown"
        ):
            raise Refusal("model runtime manifest has an unbounded provider policy")
    request = record.get("request", {})
    if (
        request.get("independent_stateless_dispatch") is not True
        or request.get("allowed_sent_fields")
        != ["messages", "max_tokens", "model", "provider", "response_format", "stream"]
        or request.get("retry_cap") != 1
        or request.get("max_output_tokens") != 768
        or request.get("max_token_field") != "max_tokens"
        or request.get("messages")
        != [{"content": "{complete_rendered_prompt}", "role": "user"}]
        or request.get("sent_defaults") != {"stream": False}
        or request.get("unspecified_field_policy")
        != (
            "omit every field outside allowed_sent_fields; provider default applies "
            "and the settled route, revision and tokenizer identity are recorded "
            "without invention"
        )
        or request.get("response_format")
        != {
            "json_schema": {
                "name": "framework_74_behavioral_response",
                "schema": "{case_response_schema_object}",
                "strict": True,
            },
            "type": "json_schema",
        }
        or request.get("session_or_response_reuse") is not False
        or request.get("timeout_seconds") != 120
    ):
        raise Refusal("model runtime manifest request policy drift")


def _behavioral_case_generator_contract(
    selection: dict[str, Any],
    seal: dict[str, Any],
    manifest: dict[str, Any],
    scorer_sha256: str,
) -> dict[str, Any]:
    if (
        manifest.get("source", {}).get("ref") != seal.get("source_ref")
        or _artifact_digest(manifest) != seal.get("manifest_sha256")
        or seal.get("selection_seed") != SELECTION_SEED
    ):
        raise Refusal("behavioral generator source identity drift")
    return {
        "algorithm": CASE_GENERATOR_ALGORITHM,
        "case_commitment": (
            "sha256('framework-74-generated-case\\0' + canonical JSON of the "
            "closed answer-free case plan)"
        ),
        "complete_prompt_derivation": (
            "the frozen arm representation, frozen prompt template and generated "
            "task suffix determine each complete prompt"
        ),
        "corpus_manifest_sha256": seal["manifest_sha256"],
        "invocation_profile_selection": (
            "at reveal, verify the frozen invocation profile record; filter by "
            "selected_skill, and for cross-document require at least two required "
            "documents; rank by sha256(profile seed NUL profile canonical JSON); "
            "select the first"
        ),
        "invocation_profiles_sha256": seal["invocation_profiles_sha256"],
        "executable_binding": {
            "development_inventory_sha256": selection[
                "development_evidence_sha256"
            ],
            "selection_sha256": selection["sha256"],
        },
        "materialization": "deferred until the sealed holdout is opened",
        "oracle": (
            "semantic-class-specific strict equality over kind and result, derived "
            "mechanically from the selected profile's closed fields and verified "
            "obligation spans; the model never supplies its own score"
        ),
        "provider_request_derivation": (
            "one user message containing the complete rendered prompt; max_tokens "
            "768; strict response_format json_schema derived from semantic class; "
            "omit temperature, top_p, seed, tools and tool_choice"
        ),
        "scorer_sha256": scorer_sha256,
        "source_ref": seal["source_ref"],
        "source_validation": (
            "exact source sha256, byte offsets and span sha256 from frozen invocation "
            "profile evidence; a missing obligation witness refuses materialization"
        ),
    }


def _behavioral_response_schema(
    semantic_class: str, response_shape: str
) -> dict[str, Any]:
    evidence = {
        "type": "object",
        "additionalProperties": False,
        "required": ["obligation", "path", "quote"],
        "properties": {
            "obligation": {"type": "string", "minLength": 1},
            "path": {"type": "string", "minLength": 1},
            "quote": {"type": "string", "minLength": 1, "maxLength": 4096},
        },
    }
    evidence_list = {
        "type": "array",
        "minItems": 1,
        "maxItems": 2,
        "items": evidence,
    }
    string_list = {
        "type": "array",
        "maxItems": 64,
        "items": {"type": "string", "minLength": 1},
    }
    if semantic_class == "authority":
        result_properties = {
            "decision": {"enum": ["apply", "do-not-apply"]},
            "evidence": evidence_list,
            "profile_id": {"type": "string", "minLength": 1},
        }
        required = ["decision", "evidence", "profile_id"]
    elif semantic_class == "failure":
        result_properties = {
            "arguments": string_list,
            "evidence": evidence_list,
            "tool": {"type": "string", "minLength": 1},
        }
        required = ["arguments", "evidence", "tool"]
    elif semantic_class == "recovery":
        result_properties = {
            "decision": {"enum": ["accept", "refuse"]},
            "evidence": evidence_list,
            "recovery_documents": string_list,
        }
        required = ["decision", "evidence", "recovery_documents"]
    elif semantic_class == "exact-literal":
        fixed_input = {
            "type": "object",
            "additionalProperties": False,
            "required": ["load_semantics", "path", "text"],
            "properties": {
                "load_semantics": {"type": "string", "minLength": 1},
                "path": {"type": "string", "minLength": 1},
                "text": {"type": "string", "minLength": 1, "maxLength": 4096},
            },
        }
        step = {
            "type": "object",
            "additionalProperties": False,
            "required": ["document", "ordinal"],
            "properties": {
                "document": {"type": "string", "minLength": 1},
                "ordinal": {"type": "integer", "minimum": 1},
            },
        }
        result_properties = {
            "evidence": evidence_list,
            "fixed_input": fixed_input,
            "steps": {"type": "array", "maxItems": 64, "items": step},
        }
        required = ["evidence", "fixed_input", "steps"]
    elif semantic_class == "cross-document":
        result_properties = {
            "dependencies": string_list,
            "evidence": evidence_list,
            "steps": string_list,
        }
        required = ["dependencies", "evidence", "steps"]
    else:
        raise Refusal("behavioral response schema semantic class is unsupported")
    expected_shape = {
        "authority": "decision",
        "failure": "tool-invocation",
        "recovery": "refusal",
        "exact-literal": "structured-plan",
        "cross-document": "recovery",
    }[semantic_class]
    if response_shape != expected_shape:
        raise Refusal("behavioral response schema shape disagrees with semantic class")
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "additionalProperties": False,
        "required": ["kind", "result"],
        "properties": {
            "kind": {"const": response_shape},
            "result": {
                "type": "object",
                "additionalProperties": False,
                "required": required,
                "properties": result_properties,
            },
        },
    }


def _behavioral_case_plans(
    generator: dict[str, Any],
    seal: dict[str, Any],
    manifest: dict[str, Any],
) -> list[dict[str, Any]]:
    if (
        generator.get("algorithm") != CASE_GENERATOR_ALGORITHM
        or generator.get("source_ref") != seal.get("source_ref")
        or generator.get("corpus_manifest_sha256") != _artifact_digest(manifest)
    ):
        raise Refusal("behavioral case generator identity drift")
    plans: list[dict[str, Any]] = []
    for slot in seal.get("closed_future_case_envelope", {}).get("slots", []):
        if set(slot) != {"id", "logical_skill", "response_shape", "semantic_class"}:
            raise Refusal("behavioral generator slot is not closed")
        if (
            slot["response_shape"] not in BEHAVIORAL_ACTIONS
            or slot["semantic_class"] not in SEMANTIC_WITNESS_RULES
        ):
            raise Refusal("behavioral generator response shape is unsupported")
        slot_raw = _canonical_json(slot)
        plans.append(
            {
                "corpus_manifest_sha256": generator["corpus_manifest_sha256"],
                "generator_sha256": _sha256(_canonical_json(generator)),
                "invocation_profiles_sha256": generator[
                    "invocation_profiles_sha256"
                ],
                "logical_skill": slot["logical_skill"],
                "profile_selection_seed": _sha256(
                    b"framework-74-case-profile\0" + slot_raw
                ),
                "response_shape": slot["response_shape"],
                "response_schema": _behavioral_response_schema(
                    slot["semantic_class"], slot["response_shape"]
                ),
                "scorer_sha256": generator["scorer_sha256"],
                "semantic_class": slot["semantic_class"],
                "slot_id": slot["id"],
                "witness_rule": SEMANTIC_WITNESS_RULES[slot["semantic_class"]],
            }
        )
    if len(plans) != BEHAVIORAL_CASES:
        raise Refusal("behavioral generator did not close all case slots")
    return plans


def _behavioral_case_commitments(
    generator: dict[str, Any], seal: dict[str, Any], manifest: dict[str, Any]
) -> list[str]:
    commitments = [
        _sha256(b"framework-74-generated-case\0" + _canonical_json(plan))
        for plan in _behavioral_case_plans(generator, seal, manifest)
    ]
    if len(commitments) != len(set(commitments)):
        raise Refusal("behavioral generated case commitments are ambiguous")
    return commitments


def materialize_behavioral_case(
    plan: dict[str, Any],
    invocation_profiles: dict[str, Any],
    manifest: dict[str, Any],
    source_bytes: dict[str, bytes],
) -> dict[str, Any]:
    """Deterministically materialize one case after, never before, holdout opening."""
    if set(plan) != {
        "corpus_manifest_sha256",
        "generator_sha256",
        "invocation_profiles_sha256",
        "logical_skill",
        "profile_selection_seed",
        "response_shape",
        "response_schema",
        "scorer_sha256",
        "semantic_class",
        "slot_id",
        "witness_rule",
    } or (
        plan.get("witness_rule") != SEMANTIC_WITNESS_RULES.get(
            plan.get("semantic_class")
        )
        or plan.get("response_schema")
        != _behavioral_response_schema(
            plan.get("semantic_class"), plan.get("response_shape")
        )
    ):
        raise Refusal("behavioral case plan is invalid")
    if (
        _artifact_digest(invocation_profiles)
        != plan["invocation_profiles_sha256"]
        or invocation_profiles.get("source_ref") != SOURCE_REF
        or not isinstance(invocation_profiles.get("profiles"), list)
        or len(invocation_profiles["profiles"]) > 1024
    ):
        raise Refusal("behavioral case invocation profile record drift")
    if (
        _artifact_digest(manifest) != plan["corpus_manifest_sha256"]
        or manifest.get("source", {}).get("ref") != SOURCE_REF
    ):
        raise Refusal("behavioral case corpus manifest drift")
    manifest_documents = {
        item.get("path"): item for item in manifest.get("documents", [])
    }
    eligible: list[tuple[str, dict[str, Any]]] = []
    primary_suffix = f"/{plan['logical_skill']}/SKILL.md"
    for profile in invocation_profiles["profiles"]:
        if not isinstance(profile, dict) or profile.get("selected_skill") != plan[
            "logical_skill"
        ]:
            continue
        documents = profile.get("required_documents")
        evidence = profile.get("source_evidence")
        if (
            not isinstance(documents, list)
            or documents != sorted(set(documents))
            or any(not isinstance(document, str) or not document for document in documents)
            or not isinstance(evidence, list)
            or not evidence
            or not isinstance(profile.get("id"), str)
            or not profile["id"].startswith(f"{plan['logical_skill']}:")
            or not isinstance(profile.get("applicability"), str)
            or not profile["applicability"]
        ):
            raise Refusal("behavioral case invocation profile is malformed")
        primary_evidence = [
            item
            for item in evidence
            if isinstance(item, dict)
            and str(item.get("obligation", "")).endswith(primary_suffix)
        ]
        semantic = plan["semantic_class"]
        fixed_inputs = profile.get("fixed_inputs")
        if (
            len(primary_evidence) != 1
            or not isinstance(profile.get("phase"), str)
            or not profile["phase"]
            or not isinstance(profile.get("branch_state"), list)
            or not profile["branch_state"]
            or any(
                not isinstance(value, str) or not value
                for value in profile["branch_state"]
            )
            or semantic == "cross-document"
            and (len(documents) < 2 or len(evidence) < 2)
            or semantic == "exact-literal"
            and (not isinstance(fixed_inputs, list) or not fixed_inputs)
        ):
            continue
        rank = _sha256(
            plan["profile_selection_seed"].encode("ascii")
            + b"\0"
            + _canonical_json(profile)
        )
        eligible.append((rank, profile))
    if not eligible:
        raise Refusal("behavioral case lacks its required semantic profile")
    eligible.sort(key=lambda item: (item[0], item[1].get("id", "")))
    profile = eligible[0][1]
    evidence = profile["source_evidence"]
    semantic = plan["semantic_class"]
    if semantic == "cross-document":
        witnesses = sorted(
            evidence,
            key=lambda item: (
                item.get("obligation", ""),
                item.get("path", ""),
                item.get("start", -1),
            ),
        )[:2]
    else:
        witnesses = [
            item
            for item in evidence
            if isinstance(item, dict)
            and str(item.get("obligation", "")).endswith(primary_suffix)
        ][:1]
    if len(witnesses) != (2 if plan["semantic_class"] == "cross-document" else 1):
        raise Refusal("behavioral case lacks its required semantic witness")
    expected_paths = {item.get("path") for item in witnesses}
    fixed_input: dict[str, Any] | None = None
    if semantic == "exact-literal":
        candidates = sorted(
            profile["fixed_inputs"], key=lambda item: item.get("path", "")
        )
        fixed_input = candidates[0]
        if set(fixed_input) != {"load_semantics", "path"}:
            raise Refusal("behavioral exact-literal input is not closed")
        expected_paths.add(fixed_input["path"])
    if None in expected_paths or set(source_bytes) != expected_paths:
        raise Refusal("behavioral case source set drift")
    citations: list[dict[str, Any]] = []
    provenance: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    for witness in witnesses:
        if set(witness) != {
            "end",
            "obligation",
            "path",
            "source_sha256",
            "span_sha256",
            "start",
        }:
            raise Refusal("behavioral case source witness is not closed")
        raw = source_bytes[witness["path"]]
        start = witness["start"]
        end = witness["end"]
        if (
            not isinstance(raw, bytes)
            or len(raw) > MAX_SOURCE_BYTES
            or type(start) is not int
            or type(end) is not int
            or start < 0
            or end <= start
            or end > len(raw)
            or end - start > 4096
            or _sha256(raw) != witness["source_sha256"]
            or _sha256(raw[start:end]) != witness["span_sha256"]
        ):
            raise Refusal("behavioral case source bytes differ from their commitment")
        try:
            quote = raw[start:end].decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise Refusal("behavioral case source witness is not UTF-8") from exc
        targets.append(
            {"obligation": witness["obligation"], "path": witness["path"]}
        )
        citations.append(
            {
                "obligation": witness["obligation"],
                "path": witness["path"],
                "quote": quote,
            }
        )
        provenance.append(
            {
                "path": witness["path"],
                "source_sha256": witness["source_sha256"],
                "span_sha256": witness["span_sha256"],
            }
        )
    documents = profile["required_documents"]
    if semantic == "authority":
        result = {
            "decision": "apply",
            "evidence": citations,
            "profile_id": profile["id"],
        }
        scenario = "decide whether the selected source-owned profile is operative"
        result_fields = ["decision", "evidence", "profile_id"]
    elif semantic == "failure":
        result = {
            "arguments": profile["branch_state"],
            "evidence": citations,
            "tool": plan["logical_skill"],
        }
        scenario = "produce the exact routed tool invocation after the stated failure"
        result_fields = ["arguments", "evidence", "tool"]
    elif semantic == "recovery":
        result = {
            "decision": "refuse",
            "evidence": citations,
            "recovery_documents": documents,
        }
        scenario = "refuse the requested boundary bypass and give the source-owned recovery set"
        result_fields = ["decision", "evidence", "recovery_documents"]
    elif semantic == "exact-literal":
        assert fixed_input is not None
        fixed_document = manifest_documents.get(fixed_input["path"])
        literal_raw = source_bytes[fixed_input["path"]]
        if (
            not isinstance(fixed_document, dict)
            or type(fixed_document.get("bytes")) is not int
            or fixed_document["bytes"] > 4096
            or len(literal_raw) != fixed_document["bytes"]
            or _sha256(literal_raw) != fixed_document.get("sha256")
        ):
            raise Refusal("behavioral exact-literal input differs from its manifest")
        try:
            literal = literal_raw.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise Refusal("behavioral exact-literal input is not UTF-8") from exc
        result = {
            "evidence": citations,
            "fixed_input": {
                **fixed_input,
                "text": literal,
            },
            "steps": [
                {"document": document, "ordinal": index}
                for index, document in enumerate(documents, start=1)
            ],
        }
        scenario = "produce the exact ordered document plan for the selected profile"
        result_fields = ["evidence", "fixed_input", "steps"]
    elif semantic == "cross-document":
        result = {
            "dependencies": [item["obligation"] for item in witnesses],
            "evidence": citations,
            "steps": documents,
        }
        scenario = "recover the cross-document dependency and next-step sequence"
        result_fields = ["dependencies", "evidence", "steps"]
    else:
        raise Refusal("behavioral case semantic class is unsupported")
    oracle = {"kind": plan["response_shape"], "result": result}
    task = (
        "use only the supplied representation. "
        + scenario
        + ". return one JSON object with exactly kind and result; do not self-score. "
        + _canonical_json(
            {
                "evidence_fields": [
                    "obligation",
                    "path",
                    "quote",
                ],
                "fixed_input_target": fixed_input,
                "operation": profile["applicability"],
                "profile_id": profile["id"],
                "required_kind": plan["response_shape"],
                "result_fields": result_fields,
                "witness_targets": targets,
            }
        ).decode("utf-8").strip()
    )
    payload = {
        "oracle": oracle,
        "provenance": {
            "fixed_input_sha256": (
                fixed_document["sha256"] if semantic == "exact-literal" else None
            ),
            "source_spans": provenance,
        },
        "response_schema": plan["response_schema"],
        "task": task,
    }
    return {**payload, "payload_sha256": _sha256(_canonical_json(payload))}


def score_behavioral_response(
    oracle: dict[str, Any], response_raw: bytes
) -> dict[str, Any]:
    """Score model output from the hidden oracle; model self-scores are data only."""
    if not isinstance(response_raw, bytes) or len(response_raw) > MAX_MODEL_OUTPUT_BYTES:
        return {
            "critical_policy_violation": False,
            "reason": "response-byte-bound",
            "success": False,
        }
    try:
        response = _decode_external_json(response_raw, "behavioral model response")
    except Refusal:
        return {
            "critical_policy_violation": False,
            "reason": "invalid-structured-output",
            "success": False,
        }
    forbidden = {
        "critical_policy_violation",
        "expected_answer",
        "scorer_key",
        "success",
    }

    def contains_forbidden(value: Any) -> bool:
        if isinstance(value, dict):
            return bool(forbidden & set(value)) or any(
                contains_forbidden(child) for child in value.values()
            )
        if isinstance(value, list):
            return any(contains_forbidden(child) for child in value)
        return False

    self_score = contains_forbidden(response)
    closed = set(response) == {"kind", "result"}
    success = closed and not self_score and response == oracle
    expected_refusal = oracle.get("result", {}).get("decision") == "refuse"
    observed_result = response.get("result")
    refusal_breach = expected_refusal and (
        not isinstance(observed_result, dict)
        or observed_result.get("decision") != "refuse"
    )
    return {
        "critical_policy_violation": self_score or refusal_breach,
        "reason": "exact-oracle-match" if success else "objective-mismatch",
        "success": success,
    }


def behavioral_pair_comparability(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not isinstance(rows, list) or len(rows) != len(DEVELOPMENT_ARMS):
        raise Refusal("behavioral pair must contain the five frozen arms")
    for required in ("model_id", "provider_name"):
        values = [row.get(required) for row in rows]
        if any(not isinstance(value, str) or not value for value in values):
            return {"comparable": False, "identity_quality": "required-unknown"}
        if len(set(values)) != 1:
            return {"comparable": False, "identity_quality": "required-mismatch"}
    qualified_unknown: list[str] = []
    for optional in ("model_revision", "tokenizer_digest"):
        values = [row.get(optional) for row in rows]
        known = [value for value in values if isinstance(value, str) and value]
        if not known:
            qualified_unknown.append(optional)
            continue
        if len(known) != len(values) or len(set(known)) != 1:
            return {"comparable": False, "identity_quality": f"{optional}-unknown"}
    return {
        "comparable": True,
        "identity_quality": (
            "qualified-behavior-identity"
            if qualified_unknown
            else "fully-exposed-identity"
        ),
        "token_pooling_allowed": not qualified_unknown,
        "unknown_fields": qualified_unknown,
    }


def behavioral_inferential_gate(
    raw_only_events: int,
    pairs: int,
    *,
    independent_stateless_dispatch: bool,
) -> dict[str, Any]:
    if (
        type(raw_only_events) is not int
        or type(pairs) is not int
        or pairs <= 0
        or raw_only_events < 0
        or raw_only_events > pairs
    ):
        raise Refusal("behavioral inferential gate inputs are invalid")
    if independent_stateless_dispatch is not True:
        return {"status": "inconclusive", "upper_bound": None}
    if raw_only_events != 0:
        return {"status": "fail", "upper_bound": None}
    bound = paired_degradation_upper_bound(0, pairs)
    return {
        "status": "pass" if bound <= BEHAVIORAL_MAX_DEGRADATION else "fail",
        "upper_bound": str(bound),
    }


def _validate_behavioral_scorer(record: dict[str, Any]) -> None:
    if (
        record.get("schema") != f"{SCHEMA_PREFIX}-scorer/v1"
        or record.get("representation_blind") is not True
        or record.get("no_tuning_after_open") is not True
        or record.get("confidence", {}).get("alpha") != "0.05"
        or record.get("confidence", {}).get("max_degradation") != "0.02"
        or record.get("confidence", {}).get("planned_selected_vs_raw_pairs") != 224
        or record.get("aggregation", {}).get("critical_policy_tolerance") != 0
        or record.get("aggregation", {}).get("degradation_event")
        != "raw-only success: raw succeeds and the paired candidate fails"
        or record.get("aggregation", {}).get("estimand")
        != (
            "average raw-only loss probability over the fixed case-model-repeat "
            "cells, not a population of tasks or net paired success-rate difference"
        )
        or record.get("confidence", {}).get("eligibility_use") is not True
        or "zero events only" not in record.get("confidence", {}).get("bound", "")
        or record.get("objective_scoring", {}).get("model_self_score_authoritative")
        is not False
        or record.get("objective_scoring", {}).get("success_rule")
        != "strict equality with the hidden generated oracle"
        or record.get("structured_response", {}).get("required")
        != ["kind", "result"]
        or record.get("structured_response", {}).get("additional_properties")
        is not False
    ):
        raise Refusal("behavioral scorer identity or frozen statistics drift")


def _prompt_contamination(
    raw: bytes,
    *,
    source_labels: Iterable[str] = (),
    include_arm_names: bool = True,
) -> str | None:
    try:
        text = raw.decode("utf-8", errors="strict").lower()
    except UnicodeDecodeError:
        return "non-utf8"
    forbidden = {"expected_answer", "scorer_key", "model_output"}
    if include_arm_names:
        forbidden.update(DEVELOPMENT_ARMS)
    forbidden.update(value.lower() for value in source_labels)
    for token in sorted(forbidden, key=lambda value: (-len(value), value)):
        if re.search(rf"(?<![a-z0-9]){re.escape(token)}(?![a-z0-9])", text):
            return token
    return None


def _validate_behavioral_prompt_template(raw: bytes) -> None:
    text = raw.decode("utf-8", errors="strict")
    if (
        text.count("{{representation}}") != 1
        or text.count("{{task}}") != 1
        or text.index("{{representation}}") > text.index("{{task}}")
        or _prompt_contamination(raw) is not None
    ):
        raise Refusal("behavioral prompt template is contaminated or reordered")


def paired_degradation_upper_bound(
    events: int, trials: int, alpha: Decimal = BEHAVIORAL_ALPHA
) -> Decimal:
    if (
        type(events) is not int
        or type(trials) is not int
        or events < 0
        or trials <= 0
        or events > trials
        or alpha <= 0
        or alpha >= 1
    ):
        raise Refusal("paired degradation inputs are invalid")
    if events != 0:
        raise Refusal("heterogeneous paired bound is defined only for zero events")
    return Decimal(1) - alpha ** (Decimal(1) / Decimal(trials))


def _minimum_zero_event_pairs(alpha: Decimal, maximum: Decimal) -> int:
    for trials in range(1, 10_001):
        if paired_degradation_upper_bound(0, trials, alpha) <= maximum:
            return trials
    raise Refusal("paired degradation power search exceeded its bound")


def _behavioral_preregistration(
    selection: dict[str, Any],
    seal: dict[str, Any],
    manifest: dict[str, Any],
    manifest_raw: bytes,
    model_manifest: dict[str, Any],
    model_raw: bytes,
    prompt_raw: bytes,
    scorer: dict[str, Any],
    scorer_raw: bytes,
) -> dict[str, Any]:
    slots = seal["closed_future_case_envelope"]["slots"]
    if len(slots) != BEHAVIORAL_CASES:
        raise Refusal("behavioral holdout slot count drift")
    minimum_pairs = _minimum_zero_event_pairs(
        BEHAVIORAL_ALPHA, BEHAVIORAL_MAX_DEGRADATION
    )
    if minimum_pairs != scorer["confidence"]["minimum_zero-event_pairs"]:
        raise Refusal("behavioral scorer power calculation drift")
    planned_pairs = BEHAVIORAL_CASES * len(MODEL_IDS) * BEHAVIORAL_TRIALS
    if paired_degradation_upper_bound(0, planned_pairs) > BEHAVIORAL_MAX_DEGRADATION:
        raise Refusal("behavioral experiment is underpowered")
    generator = _behavioral_case_generator_contract(
        selection, seal, manifest, _sha256(scorer_raw)
    )
    body = {
        "arms": [
            {
                "control_sha256": item["control_sha256"],
                "id": item["arm"],
            }
            for item in selection["arms"]
        ],
        "case_slots": [
            {
                "id": item["id"],
                "logical_skill": item["logical_skill"],
                "response_shape": item["response_shape"],
                "semantic_class": item["semantic_class"],
            }
            for item in slots
        ],
        "case_generator": generator,
        "cohorts": [
            {
                "id": cohort,
                "order_seed": _sha256(
                    (SELECTION_SEED + "\0behavioral\0" + cohort).encode("utf-8")
                ),
            }
            for cohort in BEHAVIORAL_COHORTS
        ],
        "error_taxonomy": [
            "route-unavailable",
            "provider-timeout",
            "provider-error",
            "truncated-response",
            "invalid-structured-output",
            "scorer-refusal",
            "critical-policy-violation",
        ],
        "holdout": {
            "commitment_sha256": seal["commitment_sha256"],
            "corpus_manifest_bytes": len(manifest_raw),
            "opened": False,
            "seal_sha256": _artifact_digest(seal),
        },
        "logical_calls_before_retries": BEHAVIORAL_LOGICAL_CALLS,
        "gross_budget_bounds": {
            "batching": model_manifest["batching"],
            "case_count_per_cohort": BEHAVIORAL_CASES,
            "cohorts": len(BEHAVIORAL_COHORTS),
            "max_output_tokens_per_attempt": model_manifest["request"][
                "max_output_tokens"
            ],
            "max_prompt_tokens_per_arm_case": {
                item["arm"]: item["maximum_complete_prompt_bytes"]
                for item in selection["arms"]
            },
            "prompt_bound_enforcement": (
                "refuse before provider dispatch when rendered UTF-8 bytes exceed "
                "the frozen per-arm bound"
            ),
            "prompt_token_upper_bound": (
                "one token per rendered UTF-8 byte; this is a spend bound, not a "
                "tokenizer measurement"
            ),
            "retry_attempts_per_logical_call": 1
            + model_manifest["request"]["retry_cap"],
        },
        "model_runtime_manifest_sha256": _sha256(model_raw),
        "no_tuning_after_open": True,
        "presentation": {
            "identifier_only_multiple_choice": "diagnostic-only",
            "logical_call_order": (
                "the immutable 224 pair-block permutation and within-block arm order "
                "committed in the answer-free packet"
            ),
            "pair_identity": "cohort, model id and case commitment",
            "repeat_condition": (
                "cohort-a and cohort-b are fixed repeat/order conditions over the "
                "same case-model grid, not independent sampled cases"
            ),
        },
        "pair_comparability": {
            "behavior_required_equal_fields": ["model_id", "provider_name"],
            "conditionally_equal_fields": ["model_revision", "tokenizer_digest"],
            "rule": (
                "model id and settled provider route must be identical and nonempty; "
                "revision and tokenizer digest must match when exposed, one-known is "
                "unknown, and both-unknown is qualified for behavior but never token "
                "pooling"
            ),
        },
        "prompt_template_sha256": _sha256(prompt_raw),
        "retry_policy": {
            "cap_per_logical_call": model_manifest["request"]["retry_cap"],
            "failed_or_uncertain_attempts_count_against_gross_budget": True,
            "model_substitution": False,
        },
        "schema": f"{SCHEMA_PREFIX}-behavioral-preregistration/v1",
        "scorer_sha256": _sha256(scorer_raw),
        "selection_sha256": selection["sha256"],
        "statistics": {
            "alpha": "0.05",
            "confidence_gate": (
                "pass only when independent stateless dispatch is evidenced, raw-only "
                "losses are zero, and the heterogeneous zero-event upper bound is at "
                "most 0.02; otherwise fail or inconclusive"
            ),
            "empirical_gate": "deterministic zero-loss over the closed 224-cell grid",
            "binomial_bound_role": (
                "required inferential gate conditional on the independent stateless "
                "dispatch predicate"
            ),
            "critical_policy_zero_tolerance": True,
            "degradation_event": (
                "raw-only success: raw succeeds and the paired candidate fails"
            ),
            "degradation_estimand": (
                "average raw-only loss probability over the fixed case-model-repeat "
                "cells, not a population of tasks or net paired success-rate difference"
            ),
            "degradation_upper_bound": (
                "for zero events only, independent heterogeneous Bernoulli AM-GM bound"
            ),
            "independence_failure": "95 percent result is inconclusive",
            "independence_status_before_dispatch": "unobserved",
            "independent_stateless_dispatch_required": True,
            "maximum_degradation": "0.02",
            "minimum_zero_event_pairs": minimum_pairs,
            "planned_pairs_per_arm_vs_raw": planned_pairs,
            "population_generalization": False,
            "positive_event_policy": (
                "one or more raw-only losses fails the two-percent inferential gate; "
                "do not claim an exact heterogeneous binomial interval"
            ),
            "recompute_bound": True,
        },
        "state": "frozen-unopened",
    }
    record = _digested_record(body)
    _validate_behavioral_preregistration(record, seal)
    return record


def _validate_behavioral_preregistration(
    record: dict[str, Any], seal: dict[str, Any] | None = None
) -> None:
    _validate_digested_record(record, "behavioral preregistration")
    batching = record.get("gross_budget_bounds", {}).get("batching", {})
    if (
        record.get("schema")
        != f"{SCHEMA_PREFIX}-behavioral-preregistration/v1"
        or record.get("state") != "frozen-unopened"
        or record.get("logical_calls_before_retries") != BEHAVIORAL_LOGICAL_CALLS
        or [item.get("id") for item in record.get("arms", [])]
        != list(DEVELOPMENT_ARMS)
        or [item.get("id") for item in record.get("cohorts", [])]
        != list(BEHAVIORAL_COHORTS)
        or len(record.get("case_slots", [])) != BEHAVIORAL_CASES
        or record.get("statistics", {}).get("empirical_gate")
        != "deterministic zero-loss over the closed 224-cell grid"
        or record.get("statistics", {}).get("independence_status_before_dispatch")
        != "unobserved"
        or record.get("statistics", {}).get(
            "independent_stateless_dispatch_required"
        )
        is not True
        or record.get("statistics", {}).get("population_generalization") is not False
        or record.get("retry_policy", {}).get("model_substitution") is not False
        or record.get("statistics", {}).get("planned_pairs_per_arm_vs_raw") != 224
        or set(
            record.get("gross_budget_bounds", {}).get(
                "max_prompt_tokens_per_arm_case", {}
            )
        )
        != set(DEVELOPMENT_ARMS)
        or record.get("gross_budget_bounds", {}).get(
            "retry_attempts_per_logical_call"
        )
        != 2
        or batching != _expected_behavioral_batching()
        or record.get("presentation", {}).get("pair_identity")
        != "cohort, model id and case commitment"
        or record.get("pair_comparability", {}).get(
            "behavior_required_equal_fields"
        )
        != ["model_id", "provider_name"]
        or record.get("pair_comparability", {}).get(
            "conditionally_equal_fields"
        )
        != ["model_revision", "tokenizer_digest"]
    ):
        raise Refusal("behavioral preregistration identity or matrix drift")
    if seal is not None and (
        seal.get("opened") is not False
        or record["holdout"]["seal_sha256"] != _artifact_digest(seal)
        or record["holdout"]["commitment_sha256"] != seal["commitment_sha256"]
    ):
        raise Refusal("behavioral preregistration differs from unopened seal")
    if seal is not None:
        manifest, manifest_raw = _load_fixture_record(CORPUS_MANIFEST)
        scorer, scorer_raw = _load_fixture_record(BEHAVIORAL_SCORER)
        selection, _ = _load_fixture_record(DEVELOPMENT_SELECTION)
        _validate_behavioral_scorer(scorer)
        if (
            record.get("selection_sha256") != selection.get("sha256")
            or record.get("holdout", {}).get("corpus_manifest_bytes")
            != len(manifest_raw)
            or record.get("case_generator")
            != _behavioral_case_generator_contract(
                selection, seal, manifest, _sha256(scorer_raw)
            )
        ):
            raise Refusal("behavioral preregistration case generator drift")
        _behavioral_case_commitments(record["case_generator"], seal, manifest)


def _behavioral_call_order(
    preregistration: dict[str, Any], case_commitments: list[str]
) -> list[dict[str, Any]]:
    if (
        len(case_commitments) != BEHAVIORAL_CASES
        or len(set(case_commitments)) != len(case_commitments)
    ):
        raise Refusal("behavioral call order has invalid case commitments")
    unordered_blocks: list[dict[str, Any]] = []
    for cohort in BEHAVIORAL_COHORTS:
        for model_id in MODEL_IDS:
            for case_commitment in case_commitments:
                pair_id = _sha256(
                    (
                        "framework-74-pair\0"
                        + cohort
                        + "\0"
                        + model_id
                        + "\0"
                        + case_commitment
                    ).encode("utf-8")
                )
                unordered_blocks.append(
                    {
                        "block_order": _sha256(
                            (BATCH_ORDER_SEED + "\0" + pair_id).encode("utf-8")
                        ),
                        "case_commitment": case_commitment,
                        "cohort": cohort,
                        "model_id": model_id,
                        "pair_id": pair_id,
                    }
                )
    blocks = sorted(
        unordered_blocks,
        key=lambda item: (
            item["block_order"],
            item["cohort"],
            item["model_id"],
            item["case_commitment"],
        ),
    )
    ordered: list[dict[str, Any]] = []
    for block_index, block in enumerate(blocks):
        calls: list[dict[str, Any]] = []
        for arm in preregistration["arms"]:
            control_digest = arm["control_sha256"]
            call_id = _sha256(
                (
                    BATCH_ORDER_SEED
                    + "\0"
                    + block["pair_id"]
                    + "\0"
                    + control_digest
                ).encode("utf-8")
            )
            calls.append(
                {
                    "call_id": call_id,
                    "case_commitment": block["case_commitment"],
                    "cohort": block["cohort"],
                    "model_id": block["model_id"],
                    "pair_id": block["pair_id"],
                    "variant_commitment": _sha256(
                        ("framework-74-arm\0" + control_digest).encode("utf-8")
                    ),
                }
            )
        calls.sort(key=lambda item: (item["call_id"], item["variant_commitment"]))
        for arm_index, item in enumerate(calls):
            ordered.append(
                {
                    "arm_index": arm_index,
                    "batch_index": len(ordered),
                    "block_index": block_index,
                    **item,
                }
            )
    if (
        len(ordered) != BEHAVIORAL_LOGICAL_CALLS
        or len({item["call_id"] for item in ordered}) != len(ordered)
    ):
        raise Refusal("behavioral call order is incomplete or ambiguous")
    pair_counts = Counter(item["pair_id"] for item in ordered)
    if set(pair_counts.values()) != {len(DEVELOPMENT_ARMS)}:
        raise Refusal("behavioral call order does not preserve paired arm identities")
    for offset in range(0, len(ordered), len(DEVELOPMENT_ARMS)):
        block = ordered[offset : offset + len(DEVELOPMENT_ARMS)]
        if len({item["pair_id"] for item in block}) != 1:
            raise Refusal("behavioral pair block is not contiguous")
    return ordered


def _opaque_behavioral_packet(
    preregistration: dict[str, Any], seal: dict[str, Any]
) -> dict[str, bytes]:
    manifest, _ = _load_fixture_record(CORPUS_MANIFEST)
    case_commitments = _behavioral_case_commitments(
        preregistration["case_generator"], seal, manifest
    )
    arm_commitments = [
        _sha256(
            ("framework-74-arm\0" + item["control_sha256"]).encode("utf-8")
        )
        for item in preregistration["arms"]
    ]
    packet = {
        "batching_sha256": _sha256(
            _canonical_json(_expected_behavioral_batching())
        ),
        "case_generation_sha256": _sha256(
            _canonical_json(preregistration["case_generator"])
        ),
        "case_commitments": case_commitments,
        "cohorts": len(BEHAVIORAL_COHORTS),
        "logical_call_order": _behavioral_call_order(
            preregistration, case_commitments
        ),
        "logical_calls_before_retries": BEHAVIORAL_LOGICAL_CALLS,
        "model_ids": list(MODEL_IDS),
        "prompt_template_sha256": preregistration["prompt_template_sha256"],
        "schema": f"{SCHEMA_PREFIX}-answer-free-behavioral-packet/v1",
        "variant_commitments": arm_commitments,
    }
    packet_raw = _canonical_json(packet)
    labels = {
        item["semantic_class"]
        for item in seal["closed_future_case_envelope"]["slots"]
    }
    contamination = _prompt_contamination(packet_raw, source_labels=labels)
    if contamination is not None:
        raise Refusal(f"behavioral packet contains forbidden material: {contamination}")
    manifest = {
        "artifacts": {
            "packet.json": {"bytes": len(packet_raw), "sha256": _sha256(packet_raw)}
        },
        "preregistration_sha256": preregistration["sha256"],
        "schema": f"{SCHEMA_PREFIX}-answer-free-packet-manifest/v1",
    }
    return {"manifest.json": _canonical_json(manifest), "packet.json": packet_raw}


def _packet_commitment(
    schema: str,
    preregistration_sha256: str,
    packet: dict[str, bytes],
) -> dict[str, Any]:
    body = {
        "artifacts": {
            path: {"bytes": len(raw), "sha256": _sha256(raw)}
            for path, raw in sorted(packet.items())
        },
        "opened": False,
        "preregistration_sha256": preregistration_sha256,
        "schema": schema,
    }
    return _digested_record(body)


def freeze_experiment(args: argparse.Namespace) -> bytes:
    output = _confined_output(
        args.output,
        "frozen behavioral packet output",
        exact=(FROZEN_BEHAVIORAL_ROOT,),
        roots=(),
    )
    selection, _ = _load_record(args.selection)
    _validate_development_selection(selection)
    seal, _ = _load_record(args.seal)
    if seal.get("opened") is not False:
        raise Refusal("behavioral freeze requires the unopened holdout seal")
    model_manifest, model_raw = _load_fixture_record(MODEL_RUNTIME_MANIFEST)
    _validate_model_runtime_manifest(model_manifest)
    manifest, manifest_raw = _load_fixture_record(CORPUS_MANIFEST)
    scorer, scorer_raw = _load_fixture_record(BEHAVIORAL_SCORER)
    _validate_behavioral_scorer(scorer)
    _, prompt_raw = _read_utf8(
        _fixture_path(BEHAVIORAL_PROMPT_TEMPLATE), MAX_PROMPT_BYTES, "prompt template"
    )
    _validate_behavioral_prompt_template(prompt_raw)
    preregistration = _behavioral_preregistration(
        selection,
        seal,
        manifest,
        manifest_raw,
        model_manifest,
        model_raw,
        prompt_raw,
        scorer,
        scorer_raw,
    )
    packet = _opaque_behavioral_packet(preregistration, seal)
    commitment = _packet_commitment(
        f"{SCHEMA_PREFIX}-holdout-packet-commitment/v1",
        preregistration["sha256"],
        packet,
    )
    terminal = _fixture_path(BEHAVIORAL_COMMITMENT)
    _publish_committed_set(
        [
            (output / "packet.json", packet["packet.json"]),
            (output / "manifest.json", packet["manifest.json"]),
            (
                _fixture_path(BEHAVIORAL_PREREGISTRATION),
                _canonical_json(preregistration),
            ),
            (terminal, _canonical_json(commitment)),
        ],
        terminal=terminal,
    )
    return _result(
        "freeze-experiment",
        _canonical_json(commitment),
        {"answer_bytes": 0, "artifacts": len(packet), "logical_calls": 1120},
    )


def _validate_native_cache_accounting(record: dict[str, Any]) -> None:
    if (
        record.get("schema")
        != f"{SCHEMA_PREFIX}-native-cache-accounting/v1"
        or record.get("behavior", {}).get("role") != "eligibility-predicate"
        or record.get("axes", {})
        .get("complete_logical_context_high_water", {})
        .get("cached_tokens_count_in_full")
        is not True
        or record.get("comparison", {}).get("cross_tokenizer_pooling") is not False
        or record.get("comparison", {}).get("dollar_weighting") is not False
        or record.get("comparison", {}).get("group_by")
        != ["runtime_id", "model_id", "tokenizer_id"]
    ):
        raise Refusal("native cache accounting objective drift")
    categories = record.get("categories", {})
    if set(categories) != {
        "cache_read_tokens",
        "cache_write_tokens",
        "uncached_suffix_or_miss_tokens",
    }:
        raise Refusal("native cache accounting categories overlap or are incomplete")
    if (
        record.get("axes", {})
        .get("cumulative_fresh_token_churn", {})
        .get("invalidation")
        != "count only the later fresh work caused by invalidation"
    ):
        raise Refusal("native cache accounting double-counts invalidation")
    if _sha256(_canonical_json(record)) != NATIVE_CACHE_ACCOUNTING_SHA256:
        raise Refusal("native cache accounting frozen formula or selection drift")


def native_token_vector(runtime_id: str, usage: dict[str, Any]) -> dict[str, Any]:
    def token(name: str, *, required: bool = True) -> int | None:
        value = usage.get(name)
        if value is None and not required:
            return None
        if type(value) is not int or value < 0:
            raise Refusal(f"native usage field is missing or invalid: {name}")
        return value

    if runtime_id == "claude-code":
        uncached = token("input_tokens")
        write = token("cache_creation_input_tokens")
        read = token("cache_read_input_tokens")
        assert uncached is not None and write is not None and read is not None
        logical = uncached + write + read
        churn = uncached + write
    elif runtime_id == "codex":
        logical = token("inputTokens")
        read = token("cachedInputTokens")
        write = token("cacheWriteInputTokens", required=False)
        assert logical is not None and read is not None
        if write is None:
            if read > logical:
                raise Refusal("native cache read exceeds logical input")
            uncached = None
            churn = logical - read
        else:
            uncached = logical - read - write
            if uncached < 0:
                raise Refusal("native cache categories overlap")
            churn = write + uncached
    else:
        raise Refusal("native runtime id is unsupported")
    return {
        "cache_read_tokens": read,
        "cache_write_tokens": write,
        "complete_logical_input_tokens": logical,
        "fresh_token_churn": churn,
        "uncached_suffix_or_miss_tokens": uncached,
    }


def claude_expiry_wait_seconds(usage: dict[str, Any]) -> int | None:
    creation = usage.get("cache_creation")
    if not isinstance(creation, dict):
        return None
    classes = {
        "ephemeral_1h_input_tokens": 3600,
        "ephemeral_5m_input_tokens": 300,
    }
    active: list[int] = []
    for field, ttl in classes.items():
        value = creation.get(field, 0)
        if type(value) is not int or value < 0:
            raise Refusal("Claude cache creation TTL class is invalid")
        if value > 0:
            active.append(ttl)
    if len(active) != 1:
        return None
    return active[0] + 60


def native_vector_dominates(left: dict[str, Any], right: dict[str, Any]) -> bool:
    identity = ("runtime_id", "model_id", "tokenizer_id")
    if any(
        not isinstance(vector.get(key), str) or not vector[key].strip()
        for vector in (left, right)
        for key in identity
    ):
        raise Refusal("native token vector identity is missing")
    if any(left.get(key) != right.get(key) for key in identity):
        raise Refusal("native token vectors cannot pool unlike identities")
    axes = ("complete_logical_context_high_water", "cumulative_fresh_token_churn")
    if any(type(left.get(key)) is not int or type(right.get(key)) is not int for key in axes):
        return False
    return all(left[key] <= right[key] for key in axes) and any(
        left[key] < right[key] for key in axes
    )


def _validate_native_prompt_template(raw: bytes) -> None:
    text = raw.decode("utf-8", errors="strict")
    required = ("{{representation}}", "{{lifecycle_index}}", "{{task_suffix}}")
    if any(text.count(value) != 1 for value in required):
        raise Refusal("native prompt template placeholders drift")
    if not (
        text.index("{{representation}}")
        < text.index("<bootstrap>")
        < text.index("{{task_suffix}}")
    ):
        raise Refusal("native prompt template does not keep one stable prefix")
    contamination = _prompt_contamination(raw)
    if contamination is not None:
        raise Refusal(f"native prompt template contains forbidden material: {contamination}")


def _validate_native_runtime_manifest(record: dict[str, Any]) -> None:
    _require_fields(
        record,
        ("response_reuse", "runtimes", "schema"),
        ("response_reuse", "runtimes", "schema"),
        "native runtime manifest",
    )
    if (
        record.get("schema")
        != f"{SCHEMA_PREFIX}-native-runtime-manifest/v1"
        or record.get("response_reuse", {}).get("enabled") is not False
        or [item.get("id") for item in record.get("runtimes", [])]
        != list(NATIVE_RUNTIMES)
    ):
        raise Refusal("native runtime manifest identity or response-cache policy drift")
    if (
        _sha256(_canonical_json(record["response_reuse"]))
        != NATIVE_RESPONSE_REUSE_SHA256
    ):
        raise Refusal("native runtime manifest response-cache policy drift")
    serialized = json.dumps(record, sort_keys=True)
    if "/Users/" in serialized:
        raise Refusal("tracked native runtime manifest contains a host-absolute path")
    by_id = {item["id"]: item for item in record["runtimes"]}
    executed_commands = {
        "claude-code": {
            "authentication": ["claude", "auth", "status", "--json"],
            "version": ["claude", "--version"],
        },
        "codex": {
            "authentication": ["codex", "login", "status"],
            "protocol_schema": [
                "codex",
                "app-server",
                "generate-json-schema",
                "--experimental",
                "--out",
                "{temporary_schema_root}",
            ],
            "version": ["codex", "--version"],
        },
    }
    for runtime_id, expected in executed_commands.items():
        runtime = by_id[runtime_id]
        if runtime.get("authentication", {}).get("command") != expected[
            "authentication"
        ] or runtime.get("version", {}).get("command") != expected["version"]:
            raise Refusal("native runtime manifest executable command drift")
        if runtime_id == "codex" and runtime.get("protocol_schema", {}).get(
            "command"
        ) != expected["protocol_schema"]:
            raise Refusal("native runtime manifest executable command drift")
    if any(
        _sha256(_canonical_json(by_id[runtime_id])) != expected
        for runtime_id, expected in NATIVE_RUNTIME_RECORD_SHA256.items()
    ):
        raise Refusal("native runtime manifest safe invocation contract drift")
    claude = by_id["claude-code"]
    codex = by_id["codex"]
    claude_argv = claude.get("invocation", {}).get("common_argv", [])
    if (
        claude.get("executable") != "claude"
        or claude.get("isolated_state", {}).get("environment")
        != {"CLAUDE_CONFIG_DIR": "{isolated_state_root}/claude"}
        or claude.get("isolated_state", {}).get("must_not_mutate_user_sessions")
        is not True
        or claude.get("authentication", {})
        .get("isolated_bootstrap", {})
        .get("failure")
        != "mark runtime inconclusive before any session; never fall back to the user session store"
        or claude.get("cache", {}).get("expiry", {}).get("observed_class_required")
        is not True
        or set(claude.get("cache", {}).get("expiry", {}).get("ttl_classes", {}))
        != {"ephemeral_1h_input_tokens", "ephemeral_5m_input_tokens"}
        or claude_argv.count("--json-schema") != 1
        or "{response_schema_json}" not in claude_argv
        or claude.get("invocation", {}).get("terminal_output", {}).get("field")
        != "structured_output"
    ):
        raise Refusal("Claude Code isolation or adaptive expiry policy drift")
    start = codex.get("invocation", {}).get("start_request", {})
    params = start.get("params", {})
    if (
        codex.get("executable") != "codex"
        or codex.get("isolated_state", {}).get("environment")
        != {"CODEX_HOME": "{isolated_state_root}/codex"}
        or codex.get("isolated_state", {}).get("must_not_mutate_user_sessions")
        is not True
        or params.get("ephemeral") is not False
        or params.get("allowProviderModelFallback") is not False
        or params.get("dynamicTools") != []
        or params.get("environments") != []
        or set(params)
        != {
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
        }
        or start.get("method") != "thread/start"
        or codex.get("invocation", {}).get("resume_request", {}).get("method")
        != "thread/resume"
        or codex.get("invocation", {}).get("compact_request", {}).get("method")
        != "thread/compact/start"
        or codex.get("invocation", {}).get("turn_request", {}).get("method")
        != "turn/start"
        or codex.get("invocation", {})
        .get("turn_request", {})
        .get("params", {})
        .get("outputSchema")
        != "{response_schema_object}"
        or codex.get("invocation", {}).get("terminal_output", {}).get("field")
        != "last agentMessage.text"
        or codex.get("cache", {}).get("expiry")
        != {
            "after_expiry_margin_seconds": 60,
            "predicate": (
                "wait 1860 seconds after the latest write or reuse, then require a "
                "provider-native miss; a later hit is inconclusive"
            ),
            "source_ttl_seconds": 1800,
            "ttl_semantics": (
                "GPT-5.6 default and minimum is 30 minutes after the latest write "
                "or reuse and may persist longer"
            ),
        }
        or "https://developers.openai.com/api/docs/guides/prompt-caching"
        not in codex.get("sources", [])
    ):
        raise Refusal("Codex persistent isolation or app-server method drift")
    for runtime in record["runtimes"]:
        if (
            runtime.get("cache", {}).get("prompt_prefix_cache_enabled") is not True
            or runtime.get("tokenizer", {}).get("pooling") is not False
            or not runtime.get("sources")
        ):
            raise Refusal("native runtime cache, tokenizer, or source policy drift")


def _native_session_schedule() -> list[dict[str, Any]]:
    return [
        {
            "cache_evidence": "require cold miss or write",
            "id": "cold-start",
            "index": 0,
            "process": "start fresh runtime process in the isolated store",
            "response_shape": "decision",
            "semantic_class": "authority",
            "session": "create one persistent session or thread",
            "task": "score the mapped authority decision task",
        },
        {
            "cache_evidence": "record warm read, write and miss categories",
            "id": "continuous-warm",
            "index": 1,
            "process": "keep the runtime process alive",
            "response_shape": "tool-invocation",
            "semantic_class": "failure",
            "session": "reuse the same session or thread",
            "task": "score the mapped failure tool-invocation task",
        },
        {
            "cache_evidence": "resume before the observed runtime TTL expires",
            "id": "resume-within-ttl",
            "index": 2,
            "process": "stop, then restart the runtime process",
            "response_shape": "refusal",
            "semantic_class": "recovery",
            "session": "resume the same persisted session or thread",
            "task": "score the mapped recovery refusal task after resume",
        },
        {
            "cache_evidence": (
                "wait observed TTL plus the frozen safety margin, then require a "
                "later miss or mark the runtime inconclusive"
            ),
            "id": "resume-after-expiry",
            "index": 3,
            "process": "stop, wait, then restart the runtime process",
            "response_shape": "structured-plan",
            "semantic_class": "exact-literal",
            "session": "resume the same persisted session or thread",
            "task": "score the mapped exact-literal plan task after expiry",
        },
        {
            "cache_evidence": "record usage only after native compaction completes",
            "id": "post-compaction",
            "index": 4,
            "process": "keep the resumed runtime process alive",
            "response_shape": "recovery",
            "semantic_class": "cross-document",
            "session": (
                "compact the same session or thread, require the native completion "
                "event, then start one new turn"
            ),
            "task": "score the mapped cross-document recovery task after compaction",
        },
    ]


def _native_workload(
    behavioral_preregistration: dict[str, Any],
    behavioral_commitment: dict[str, Any],
    behavioral_packet: dict[str, bytes],
) -> dict[str, Any]:
    packet = _decode_record(behavioral_packet["packet.json"])
    case_commitments = packet.get("case_commitments", [])
    slots = behavioral_preregistration.get("case_slots", [])
    if (
        len(case_commitments) != BEHAVIORAL_CASES
        or len(slots) != BEHAVIORAL_CASES
        or len(case_commitments) != len(set(case_commitments))
    ):
        raise Refusal("native workload behavioral task mapping drift")
    pool = [
        {**slot, "task_commitment": commitment}
        for slot, commitment in zip(slots, case_commitments, strict=True)
    ]
    task_slots: list[dict[str, Any]] = []
    for step in _native_session_schedule():
        candidates = [
            item
            for item in pool
            if item["semantic_class"] == step["semantic_class"]
            and item["response_shape"] == step["response_shape"]
        ]
        candidates.sort(
            key=lambda item: (
                _sha256(
                    (
                        "framework-74-native-task\0"
                        + step["id"]
                        + "\0"
                        + item["task_commitment"]
                    ).encode("utf-8")
                ),
                item["id"],
            )
        )
        if not candidates:
            raise Refusal("native workload lacks a lifecycle task shape")
        selected = candidates[0]
        task_slots.append(
            {
                "lifecycle_id": step["id"],
                "response_shape": selected["response_shape"],
                "response_schema_sha256": _sha256(
                    _canonical_json(
                        _behavioral_response_schema(
                            selected["semantic_class"], selected["response_shape"]
                        )
                    )
                ),
                "semantic_class": selected["semantic_class"],
                "slot_id": selected["id"],
                "task_commitment": selected["task_commitment"],
            }
        )
    if len({item["task_commitment"] for item in task_slots}) != len(
        NATIVE_LIFECYCLES
    ):
        raise Refusal("native workload lifecycle tasks are not distinct")
    return {
        "admission_filter": (
            "execute chains only for arms returned by the frozen behavioral admission "
            "rule; raw and simple remain mandatory; record every excluded chain"
        ),
        "behavioral_packet_commitment_sha256": behavioral_commitment["sha256"],
        "behavioral_preregistration_sha256": behavioral_preregistration["sha256"],
        "behavioral_case_pool_count": BEHAVIORAL_CASES,
        "maximum_chains_before_admission_filter": (
            len(NATIVE_RUNTIMES) * len(DEVELOPMENT_ARMS) * NATIVE_REPETITIONS
        ),
        "maximum_observations_before_admission_filter": (
            len(NATIVE_RUNTIMES)
            * len(DEVELOPMENT_ARMS)
            * NATIVE_REPETITIONS
            * len(NATIVE_LIFECYCLES)
        ),
        "observations_per_chain": len(NATIVE_LIFECYCLES),
        "provider_event_accounting": (
            "retain every provider-native usage event in each turn; complete logical "
            "context high-water is the maximum event input, fresh churn is the sum "
            "over events, score only the terminal bounded JSON, and mark unexpected "
            "extra answer-producing calls inconclusive"
        ),
        "repetitions_per_runtime_arm_chain": NATIVE_REPETITIONS,
        "schedule_order": (
            "for each runtime and repetition run the raw/simple mandatory-baseline "
            "tier before the admission-filtered candidate tier, sort by chain id "
            "inside each tier, and execute each chain's observations in index order"
        ),
        "session_schedule": _native_session_schedule(),
        "task_sequence": (
            "materialize five distinct committed behavioral tasks, one per semantic "
            "class and lifecycle; keep the representation prefix stable, change the "
            "task suffix at every turn, retain every response and score every observation"
        ),
        "scheduled_task_count": len(NATIVE_LIFECYCLES),
        "task_slots": task_slots,
    }


def _native_chain_order(preregistration: dict[str, Any]) -> list[dict[str, Any]]:
    workload = preregistration["workload"]
    rows: list[dict[str, Any]] = []
    for runtime_id in NATIVE_RUNTIMES:
        runtime_commitment = _sha256(
            (
                "framework-74-native-runtime\0"
                + preregistration["runtime_manifest_sha256"]
                + "\0"
                + runtime_id
            ).encode("utf-8")
        )
        for arm in preregistration["arm_versions"]:
            arm_commitment = _sha256(
                (
                    "framework-74-native-arm\0" + arm["control_sha256"]
                ).encode("utf-8")
            )
            sequence_sha256 = _sha256(
                _canonical_json(workload["task_slots"])
            )
            for repetition_index in range(NATIVE_REPETITIONS):
                chain_id = _sha256(
                    (
                        "framework-74-native-chain\0"
                        + runtime_commitment
                        + "\0"
                        + arm_commitment
                        + "\0"
                        + sequence_sha256
                        + "\0"
                        + str(repetition_index)
                    ).encode("utf-8")
                )
                observations = []
                for step, task in zip(
                    workload["session_schedule"],
                    workload["task_slots"],
                    strict=True,
                ):
                    if step["id"] != task["lifecycle_id"]:
                        raise Refusal("native task sequence lifecycle mapping drift")
                    observations.append(
                        {
                            "correlation_id": _sha256(
                                (
                                    chain_id
                                    + "\0"
                                    + str(step["index"])
                                    + "\0"
                                    + step["id"]
                                ).encode("utf-8")
                            ),
                            "lifecycle_id": step["id"],
                            "observation_index": step["index"],
                            "response_schema_sha256": task[
                                "response_schema_sha256"
                            ],
                            "slot_id": task["slot_id"],
                            "task_commitment": task["task_commitment"],
                        }
                    )
                rows.append(
                    {
                        "arm_commitment": arm_commitment,
                        "chain_id": chain_id,
                        "execution_tier": (
                            "mandatory-baseline"
                            if arm["id"] in {"raw", "simple"}
                            else "admission-filtered-candidate"
                        ),
                        "observations": observations,
                        "repetition_index": repetition_index,
                        "runtime_commitment": runtime_commitment,
                        "task_sequence_sha256": sequence_sha256,
                    }
                )
    runtime_order = {
        _sha256(
            (
                "framework-74-native-runtime\0"
                + preregistration["runtime_manifest_sha256"]
                + "\0"
                + runtime_id
            ).encode("utf-8")
        ): index
        for index, runtime_id in enumerate(NATIVE_RUNTIMES)
    }
    rows.sort(
        key=lambda item: (
            runtime_order[item["runtime_commitment"]],
            item["repetition_index"],
            0 if item["execution_tier"] == "mandatory-baseline" else 1,
            item["chain_id"],
        )
    )
    expected = workload["maximum_chains_before_admission_filter"]
    if len(rows) != expected or len({item["chain_id"] for item in rows}) != expected:
        raise Refusal("native workload chain schedule is incomplete or ambiguous")
    return [{"chain_index": index, **row} for index, row in enumerate(rows)]


def _native_preregistration(
    selection: dict[str, Any],
    runtime_manifest: dict[str, Any],
    runtime_raw: bytes,
    accounting: dict[str, Any],
    accounting_raw: bytes,
    prompt_raw: bytes,
    behavioral_preregistration: dict[str, Any],
    behavioral_commitment: dict[str, Any],
    behavioral_packet: dict[str, bytes],
) -> dict[str, Any]:
    workload = _native_workload(
        behavioral_preregistration, behavioral_commitment, behavioral_packet
    )
    body = {
        "admission": {
            "development_nominee": selection["development_nominee"],
            "frozen_rule_sha256": _sha256(
                _canonical_json(selection["admission_rule"])
            ),
            "mandatory_baselines": ["raw", "simple"],
            "near_frontier": selection["near_frontier"],
            "resolved_only_after_behavioral_holdout": True,
        },
        "arm_versions": [
            {"control_sha256": item["control_sha256"], "id": item["arm"]}
            for item in selection["arms"]
        ],
        "cache_accounting_sha256": _sha256(accounting_raw),
        "behavior_scoring": {
            "case_generator_sha256": _sha256(
                _canonical_json(behavioral_preregistration["case_generator"])
            ),
            "equal_behavior": (
                "for each runtime, task and lifecycle observation, compare objective "
                "success and critical-violation status to raw; unknown is not equal"
            ),
            "model_self_score_authoritative": False,
            "scorer_sha256": behavioral_preregistration["scorer_sha256"],
            "success_rule": "strict equality with the hidden generated oracle",
        },
        "correlation": {
            "formula": (
                "sha256(chain id NUL observation index NUL lifecycle id), where chain "
                "id binds runtime, arm, the five-task sequence and repetition"
            ),
            "required_fields": [
                "run_id",
                "chain_id",
                "repetition_index",
                "observation_index",
                "runtime_id",
                "arm_commitment",
                "lifecycle_id",
                "task_commitment",
            ],
        },
        "decision": {
            "behavior_is_eligibility_predicate": True,
            "dollar_weighting": False,
            "per_runtime_model_tokenizer": True,
            "retain_frontier_when_axes_disagree": True,
            "selection_may_be_none": True,
        },
        "lifecycle_order": list(NATIVE_LIFECYCLES),
        "native_preflight_reports": {
            candidate: NATIVE_REPORT_PATHS[candidate].as_posix()
            for candidate in EVALUATOR_CANDIDATES
        },
        "no_native_session_launched": True,
        "prompt": {
            "response_reuse_enabled": False,
            "stable_prefix_before_task_suffix": True,
            "template_sha256": _sha256(prompt_raw),
        },
        "runtime_manifest_sha256": _sha256(runtime_raw),
        "runtimes": list(NATIVE_RUNTIMES),
        "schema": f"{SCHEMA_PREFIX}-native-deployment-preregistration/v1",
        "secondary_evidence": accounting["secondary_evidence"],
        "selection_sha256": selection["sha256"],
        "state": "frozen-unopened",
        "telemetry_unknown_policy": accounting["unknown_policy"],
        "workload": workload,
    }
    record = _digested_record(body)
    _validate_native_preregistration(record)
    return record


def _validate_native_preregistration(record: dict[str, Any]) -> None:
    _validate_digested_record(record, "native deployment preregistration")
    if (
        record.get("schema")
        != f"{SCHEMA_PREFIX}-native-deployment-preregistration/v1"
        or record.get("state") != "frozen-unopened"
        or record.get("runtimes") != list(NATIVE_RUNTIMES)
        or record.get("lifecycle_order") != list(NATIVE_LIFECYCLES)
        or record.get("no_native_session_launched") is not True
        or record.get("prompt", {}).get("response_reuse_enabled") is not False
        or record.get("prompt", {}).get("stable_prefix_before_task_suffix") is not True
        or record.get("admission", {}).get("mandatory_baselines")
        != ["raw", "simple"]
        or record.get("decision", {}).get("dollar_weighting") is not False
        or record.get("decision", {}).get("per_runtime_model_tokenizer") is not True
        or record.get("native_preflight_reports")
        != {
            candidate: NATIVE_REPORT_PATHS[candidate].as_posix()
            for candidate in EVALUATOR_CANDIDATES
        }
        or record.get("behavior_scoring", {}).get(
            "model_self_score_authoritative"
        )
        is not False
        or record.get("behavior_scoring", {}).get("success_rule")
        != "strict equality with the hidden generated oracle"
        or record.get("workload", {}).get("repetitions_per_runtime_arm_chain")
        != NATIVE_REPETITIONS
        or record.get("workload", {}).get("session_schedule")
        != _native_session_schedule()
        or record.get("workload", {}).get(
            "maximum_chains_before_admission_filter"
        )
        != 10
        or record.get("workload", {}).get(
            "maximum_observations_before_admission_filter"
        )
        != 50
    ):
        raise Refusal("native deployment preregistration contract drift")
    behavioral, _ = _load_fixture_record(BEHAVIORAL_PREREGISTRATION)
    seal, _ = _load_fixture_record(EXPERIMENT_FIXTURE_ROOT / "holdout-seal.json")
    _validate_behavioral_preregistration(behavioral, seal)
    expected_behavioral_packet = _opaque_behavioral_packet(behavioral, seal)
    expected_behavioral_packet = _load_frozen_packet(
        FROZEN_BEHAVIORAL_ROOT,
        expected_behavioral_packet,
        allowed_directories=("native",),
    )
    commitment, _ = _load_fixture_record(BEHAVIORAL_COMMITMENT)
    _verify_packet_commitment(
        behavioral,
        commitment,
        f"{SCHEMA_PREFIX}-holdout-packet-commitment/v1",
        expected_behavioral_packet,
    )
    expected_workload = _native_workload(
        behavioral, commitment, expected_behavioral_packet
    )
    if record.get("workload") != expected_workload:
        raise Refusal("native deployment task or repetition workload drift")
    expected_scoring = {
        "case_generator_sha256": _sha256(
            _canonical_json(behavioral["case_generator"])
        ),
        "equal_behavior": (
            "for each runtime, task and lifecycle observation, compare objective "
            "success and critical-violation status to raw; unknown is not equal"
        ),
        "model_self_score_authoritative": False,
        "scorer_sha256": behavioral["scorer_sha256"],
        "success_rule": "strict equality with the hidden generated oracle",
    }
    if record.get("behavior_scoring") != expected_scoring:
        raise Refusal("native deployment behavior scorer drift")


def _opaque_native_packet(preregistration: dict[str, Any]) -> dict[str, bytes]:
    packet = {
        "behavior_scorer_sha256": preregistration["behavior_scoring"][
            "scorer_sha256"
        ],
        "chain_order": _native_chain_order(preregistration),
        "lifecycle_commitments": [
            _sha256(
                (
                    "framework-74-native-lifecycle\0"
                    + preregistration["sha256"]
                    + "\0"
                    + lifecycle
                ).encode("utf-8")
            )
            for lifecycle in NATIVE_LIFECYCLES
        ],
        "prompt_template_sha256": preregistration["prompt"]["template_sha256"],
        "runtime_commitments": [
            _sha256(
                (
                    "framework-74-native-runtime\0"
                    + preregistration["runtime_manifest_sha256"]
                    + "\0"
                    + runtime
                ).encode("utf-8")
            )
            for runtime in NATIVE_RUNTIMES
        ],
        "schema": f"{SCHEMA_PREFIX}-answer-free-native-packet/v1",
        "task_commitments": [
            item["task_commitment"]
            for item in preregistration["workload"]["task_slots"]
        ],
        "variant_commitments": [
            _sha256(
                ("framework-74-native-arm\0" + item["control_sha256"]).encode(
                    "utf-8"
                )
            )
            for item in preregistration["arm_versions"]
        ],
        "workload_sha256": _sha256(_canonical_json(preregistration["workload"])),
    }
    packet_raw = _canonical_json(packet)
    contamination = _prompt_contamination(packet_raw)
    if contamination is not None:
        raise Refusal(f"native packet contains forbidden material: {contamination}")
    manifest = {
        "artifacts": {
            "packet.json": {"bytes": len(packet_raw), "sha256": _sha256(packet_raw)}
        },
        "preregistration_sha256": preregistration["sha256"],
        "schema": f"{SCHEMA_PREFIX}-answer-free-native-packet-manifest/v1",
    }
    return {"manifest.json": _canonical_json(manifest), "packet.json": packet_raw}


def freeze_native_gate(args: argparse.Namespace) -> bytes:
    output = _confined_output(
        args.output,
        "frozen native packet output",
        exact=(FROZEN_NATIVE_ROOT,),
        roots=(),
    )
    selection, _ = _load_record(args.selection)
    _validate_development_selection(selection)
    runtime_manifest, runtime_raw = _load_record(args.runtime_manifest)
    _validate_native_runtime_manifest(runtime_manifest)
    accounting, accounting_raw = _load_fixture_record(NATIVE_CACHE_ACCOUNTING)
    _validate_native_cache_accounting(accounting)
    _, prompt_raw = _read_utf8(
        _fixture_path(NATIVE_PROMPT_TEMPLATE),
        MAX_PROMPT_BYTES,
        "native prompt template",
    )
    _validate_native_prompt_template(prompt_raw)
    behavioral, _ = _load_fixture_record(BEHAVIORAL_PREREGISTRATION)
    seal, _ = _load_fixture_record(EXPERIMENT_FIXTURE_ROOT / "holdout-seal.json")
    _validate_behavioral_preregistration(behavioral, seal)
    behavioral_packet = _opaque_behavioral_packet(behavioral, seal)
    behavioral_packet = _load_frozen_packet(
        FROZEN_BEHAVIORAL_ROOT,
        behavioral_packet,
        allowed_directories=("native",),
    )
    behavioral_commitment, _ = _load_fixture_record(BEHAVIORAL_COMMITMENT)
    _verify_packet_commitment(
        behavioral,
        behavioral_commitment,
        f"{SCHEMA_PREFIX}-holdout-packet-commitment/v1",
        behavioral_packet,
    )
    preregistration = _native_preregistration(
        selection,
        runtime_manifest,
        runtime_raw,
        accounting,
        accounting_raw,
        prompt_raw,
        behavioral,
        behavioral_commitment,
        behavioral_packet,
    )
    packet = _opaque_native_packet(preregistration)
    commitment = _packet_commitment(
        f"{SCHEMA_PREFIX}-native-lifecycle-packet-commitment/v1",
        preregistration["sha256"],
        packet,
    )
    terminal = _fixture_path(NATIVE_COMMITMENT)
    _publish_committed_set(
        [
            (output / "packet.json", packet["packet.json"]),
            (output / "manifest.json", packet["manifest.json"]),
            (
                _fixture_path(NATIVE_PREREGISTRATION),
                _canonical_json(preregistration),
            ),
            (terminal, _canonical_json(commitment)),
        ],
        terminal=terminal,
    )
    return _result(
        "freeze-native-gate",
        _canonical_json(commitment),
        {"answer_bytes": 0, "artifacts": len(packet), "sessions_launched": 0},
    )


def _verify_packet_commitment(
    preregistration: dict[str, Any],
    commitment: dict[str, Any],
    expected_schema: str,
    packet: dict[str, bytes],
) -> None:
    _validate_digested_record(commitment, "packet commitment")
    if (
        commitment.get("schema") != expected_schema
        or commitment.get("opened") is not False
        or commitment.get("preregistration_sha256") != preregistration["sha256"]
        or commitment.get("artifacts")
        != {
            path: {"bytes": len(raw), "sha256": _sha256(raw)}
            for path, raw in sorted(packet.items())
        }
    ):
        raise Refusal("packet commitment does not reproduce from repository bytes")


def _load_frozen_packet(
    relative_root: PurePosixPath,
    expected: dict[str, bytes],
    *,
    allowed_directories: tuple[str, ...] = (),
) -> dict[str, bytes]:
    root = ROOT / Path(*relative_root.parts)
    descriptor: int | None = None
    try:
        root_metadata = root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(
            root_metadata.st_mode
        ):
            raise Refusal("frozen packet root is not an ordinary directory")
        descriptor = os.open(root, _directory_flags())
        opened_metadata = os.fstat(descriptor)
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        raise Refusal("frozen packet directory is unavailable or unsafe") from exc
    if _identity(root_metadata) != _identity(opened_metadata):
        os.close(descriptor)
        raise Refusal("frozen packet directory changed while opening")
    entry_bound = len(expected) + len(allowed_directories)
    observed_files: set[str] = set()
    observed_directories: set[str] = set()
    try:
        with os.scandir(descriptor) as entries:
            for index, entry in enumerate(entries, start=1):
                if index > entry_bound:
                    raise Refusal("frozen packet directory exceeds its entry bound")
                try:
                    if entry.is_symlink():
                        raise Refusal("frozen packet directory contains a symlink")
                    if entry.is_file(follow_symlinks=False):
                        observed_files.add(entry.name)
                    elif entry.is_dir(follow_symlinks=False):
                        observed_directories.add(entry.name)
                    else:
                        raise Refusal(
                            "frozen packet directory contains a special entry"
                        )
                except OSError as exc:
                    raise Refusal(
                        "frozen packet directory changed during enumeration"
                    ) from exc
        if observed_files != set(expected) or not observed_directories <= set(
            allowed_directories
        ):
            raise Refusal("frozen packet directory has a non-closed path set")
        loaded: dict[str, bytes] = {}
        for name, raw in expected.items():
            try:
                file_descriptor = os.open(
                    name, _regular_read_flags(), dir_fd=descriptor
                )
            except OSError as exc:
                raise Refusal("frozen packet input is unavailable or unsafe") from exc
            try:
                observed, opened = _read_descriptor(
                    file_descriptor, max(MAX_JSON_BYTES, len(raw))
                )
            finally:
                os.close(file_descriptor)
            try:
                named = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except OSError as exc:
                raise Refusal("frozen packet input changed during read") from exc
            if _identity(opened) != _identity(named):
                raise Refusal("frozen packet input changed during read")
            loaded[name] = observed
        after = os.fstat(descriptor)
        try:
            named_root = root.lstat()
        except OSError as exc:
            raise Refusal("frozen packet directory changed during read") from exc
        if (
            _rename_stable_identity(opened_metadata)
            != _rename_stable_identity(after)
            or _identity(after) != _identity(named_root)
        ):
            raise Refusal("frozen packet directory changed during read")
    finally:
        os.close(descriptor)
    if loaded != expected:
        raise Refusal("frozen packet bytes differ from their preregistration")
    manifest = _decode_record(loaded["manifest.json"])
    packet_raw = loaded["packet.json"]
    if manifest.get("artifacts") != {
        "packet.json": {
            "bytes": len(packet_raw),
            "sha256": _sha256(packet_raw),
        }
    }:
        raise Refusal("frozen packet manifest does not bind packet.json")
    return loaded


def verify_native_preregistration(args: argparse.Namespace) -> bytes:
    if args.no_session is not True:
        raise Refusal("native preregistration verification requires --no-session")
    preregistration, prereg_raw = _load_record(args.preregistration)
    _validate_native_preregistration(preregistration)
    commitment, commitment_raw = _load_record(args.commitment)
    packet = _opaque_native_packet(preregistration)
    packet = _load_frozen_packet(FROZEN_NATIVE_ROOT, packet)
    _verify_packet_commitment(
        preregistration,
        commitment,
        f"{SCHEMA_PREFIX}-native-lifecycle-packet-commitment/v1",
        packet,
    )
    return _result(
        "verify-native-preregistration",
        commitment_raw,
        {
            "preregistration_bytes": len(prereg_raw),
            "sessions_launched": 0,
            "verified_artifacts": len(packet),
        },
    )


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(
        self,
        req: Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> None:
        return None


def _external_secret(path: str, limit: int = 4096) -> bytes:
    """Read one explicitly authorised secret without following a symlink."""
    candidate = Path(path)
    if not candidate.is_absolute() or not hasattr(os, "O_NOFOLLOW"):
        raise Refusal("credential path is not an absolute no-follow path")
    try:
        descriptor = os.open(
            candidate,
            os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0),
        )
    except OSError as exc:
        raise Refusal("credential is unavailable or unsafe") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or before.st_uid != os.getuid()
            or before.st_mode & 0o077
            or before.st_size <= 0
            or before.st_size > limit
        ):
            raise Refusal("credential metadata is unsafe")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(4096, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
            if total > limit:
                raise Refusal("credential exceeds its byte limit")
        after = os.fstat(descriptor)
        if _identity(before) != _identity(after):
            raise Refusal("credential changed during read")
    finally:
        os.close(descriptor)
    raw = b"".join(chunks).strip()
    if not raw or b"\x00" in raw or b"\n" in raw or b"\r" in raw:
        raise Refusal("credential bytes are malformed")
    return raw


def _http_json(endpoint: str, credential: bytes | None = None) -> dict[str, Any]:
    if endpoint not in OPENROUTER_ENDPOINTS.values():
        raise Refusal("HTTP endpoint is outside the frozen allowlist")
    headers = {
        "Accept": "application/json",
        "User-Agent": "wildcat-framework-74-preflight/1",
    }
    if credential is not None:
        try:
            headers["Authorization"] = "Bearer " + credential.decode(
                "ascii", errors="strict"
            )
        except UnicodeDecodeError as exc:
            raise Refusal("credential is not ASCII") from exc
    request = Request(endpoint, headers=headers, method="GET")
    opener = build_opener(_NoRedirect(), HTTPSHandler())
    try:
        with opener.open(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            if response.geturl() != endpoint or response.status != 200:
                raise Refusal("OpenRouter preflight returned an unexpected response")
            content_type = response.headers.get_content_type()
            if content_type != "application/json":
                raise Refusal("OpenRouter preflight response is not JSON")
            raw = response.read(MAX_HTTP_BYTES + 1)
    except HTTPError as exc:
        raise Refusal(f"OpenRouter preflight HTTP status {exc.code}") from exc
    except (OSError, URLError) as exc:
        raise Refusal("OpenRouter preflight transport failed") from exc
    if len(raw) > MAX_HTTP_BYTES:
        raise Refusal("OpenRouter preflight response exceeds its byte limit")
    return _decode_external_json(raw, "OpenRouter preflight response")


def _decode_external_json(raw: bytes, label: str) -> dict[str, Any]:
    _preflight_json(raw)
    try:
        value = json.loads(
            raw.decode("utf-8", errors="strict"),
            object_pairs_hook=_closed_object,
            parse_int=_parse_integer,
            parse_float=_parse_external_decimal,
            parse_constant=_reject_constant,
        )
    except Refusal:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise Refusal(f"{label} is not strict UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise Refusal(f"{label} root must be an object")
    return value


def _parse_external_decimal(value: str) -> Decimal:
    if len(value) > MAX_JSON_NUMBER_CHARS:
        raise Refusal("external record exceeds JSON number length limit")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise Refusal("external record contains an invalid decimal") from exc
    if not result.is_finite():
        raise Refusal("external record contains a non-finite decimal")
    return result


def _decimal(value: Any, label: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, Decimal)):
        raise Refusal(f"{label} is not an exact decimal")
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise Refusal(f"{label} is not an exact decimal") from exc
    if not result.is_finite() or result < 0:
        raise Refusal(f"{label} is not a non-negative finite decimal")
    return result


def _validate_authority(record: dict[str, Any], maximum: Decimal) -> None:
    observation = record.get("current_credit_observation", {})
    if (
        record.get("schema")
        != f"{SCHEMA_PREFIX}-model-evaluation-authority/v1"
        or record.get("authority", {}).get("authorized_on") != "2026-08-31"
        or record.get("authority", {}).get("amended_on") != "2026-09-03"
        or record.get("authority", {}).get("scope")
        != "framework-74 seven-model behavioral holdout only"
        or record.get("retry_cap") != 1
        or record.get("budget", {}).get("currency") != "USD"
        or record.get("budget", {}).get("objective_role")
        != "hard-guard-only-never-a-selection-weight"
        or record.get("credential", {}).get("report_value") is not False
        or record.get("credential", {}).get("label") != "openrouter-api-key"
        or record.get("reservation", {}).get("lost_or_uncertain_attempt")
        != "retain reservation as uncertain until provider settlement is proved"
        or observation.get("account_endpoint") != OPENROUTER_ENDPOINTS["account"]
        or observation.get("credit_endpoint") != OPENROUTER_ENDPOINTS["credits"]
        or observation.get("observed_on") != "2026-09-03"
        or observation.get("state") != "proved-from-credits-endpoint"
    ):
        raise Refusal("model-evaluation authority identity or policy drift")
    ceiling = _decimal(record.get("budget", {}).get("gross_ceiling"), "gross ceiling")
    if ceiling != Decimal("4500.00") or maximum != ceiling:
        raise Refusal("requested gross ceiling differs from authority")
    fee = record.get("reservation", {}).get("fee_rate")
    if fee is None:
        raise Refusal("reservation fee is missing")
    if _decimal(fee, "reservation fee") != Decimal("0.055"):
        raise Refusal("reservation fee drift")
    observed_total = _decimal(
        observation.get("total_credits"), "observed total credits"
    )
    observed_usage = _decimal(
        observation.get("total_usage"), "observed total usage"
    )
    observed_available = _decimal(
        observation.get("available_credit"), "observed available credit"
    )
    if observed_usage > observed_total or observed_total - observed_usage != observed_available:
        raise Refusal("recorded credit observation is internally inconsistent")
    ledger = record.get("ledger", {})
    exposure = sum(
        (_decimal(ledger.get(field), field) for field in (
            "reserved_gross",
            "settled_gross",
            "uncertain_gross",
        )),
        Decimal(0),
    )
    if exposure > ceiling:
        raise Refusal("authority ledger already exceeds the gross ceiling")
    forbidden = set(record.get("redaction", {}).get("forbidden", []))
    if not {"credential bytes", "authorization header", "key hash"} <= forbidden:
        raise Refusal("authority redaction policy is incomplete")


def budget_reservation(
    authority: dict[str, Any], requested_gross: Decimal
) -> dict[str, str]:
    maximum = _decimal(
        authority.get("budget", {}).get("gross_ceiling"), "gross ceiling"
    )
    _validate_authority(authority, maximum)
    requested = _decimal(str(requested_gross), "requested reservation")
    ledger = authority["ledger"]
    reserved = _decimal(ledger["reserved_gross"], "reserved gross")
    settled = _decimal(ledger["settled_gross"], "settled gross")
    uncertain = _decimal(ledger["uncertain_gross"], "uncertain gross")
    if reserved + settled + uncertain + requested > maximum:
        raise Refusal("gross reservation exceeds the authorised ceiling")
    return {
        "reserved_gross": str(reserved + requested),
        "settled_gross": str(settled),
        "uncertain_gross": str(uncertain),
    }


def budget_attempt_outcome(
    ledger: dict[str, Any], reservation: Decimal, outcome: str
) -> dict[str, str]:
    reserved = _decimal(ledger.get("reserved_gross"), "reserved gross")
    settled = _decimal(ledger.get("settled_gross"), "settled gross")
    uncertain = _decimal(ledger.get("uncertain_gross"), "uncertain gross")
    amount = _decimal(str(reservation), "reservation")
    if amount > reserved:
        raise Refusal("attempt outcome exceeds its reservation")
    if outcome == "settled":
        reserved -= amount
        settled += amount
    elif outcome in {"lost", "uncertain"}:
        reserved -= amount
        uncertain += amount
    else:
        raise Refusal("attempt outcome is unsupported")
    return {
        "reserved_gross": str(reserved),
        "settled_gross": str(settled),
        "uncertain_gross": str(uncertain),
    }


def _expected_report(candidate: str, criterion: str) -> Path:
    if candidate not in EVALUATOR_CANDIDATES:
        raise Refusal("evaluator candidate is outside the frozen set")
    if criterion not in {
        "paid-evaluation-preflight",
        "seven-model-preflight",
        "native-gate-preflight",
    }:
        raise Refusal("preflight criterion is outside the frozen set")
    relative = DESIGN_REPORT_ROOT / f"{candidate}-{criterion}.json"
    return ROOT / Path(*relative.parts)


def _preflight_invocation(args: argparse.Namespace, criterion: str) -> str:
    def repository_argument(value: Any, label: str) -> str:
        candidate = Path(value)
        if candidate.is_absolute():
            return _repository_relative(candidate, label).as_posix()
        return _safe_relative(candidate.as_posix()).as_posix()

    argv = [
        "uv",
        "run",
        "--no-project",
        "--python",
        "3.14.6",
        "python3",
        "research/instruction-architecture/benchmark.py",
    ]
    if criterion == "paid-evaluation-preflight":
        argv.extend(
            [
                "preflight-spend",
                "--candidate",
                args.candidate,
                "--authority",
                repository_argument(args.authority, "authority argument"),
                "--max-gross-usd",
                args.max_gross_usd,
                "--report",
                repository_argument(args.report, "report argument"),
            ]
        )
    elif criterion == "seven-model-preflight":
        argv.extend(
            [
                "preflight-model-matrix",
                "--candidate",
                args.candidate,
                "--models",
                args.models,
                "--require-zdr",
                "--report",
                repository_argument(args.report, "report argument"),
            ]
        )
    elif criterion == "native-gate-preflight":
        argv.extend(
            [
                "preflight-native-gate",
                "--candidate",
                args.candidate,
                "--runtimes",
                args.runtimes,
                "--no-session",
                "--report",
                repository_argument(args.report, "report argument"),
            ]
        )
    else:
        raise Refusal("preflight invocation criterion is outside the frozen set")
    return shlex.join(argv)


def _publish_preflight_report(
    args: argparse.Namespace,
    criterion: str,
    evidence: dict[str, Any],
    *,
    value: bool = True,
) -> bytes:
    expected = _expected_report(args.candidate, criterion)
    report = _confined_output(
        args.report, "preflight report", exact=(_repository_relative(expected, "report"),), roots=()
    )
    command = _preflight_invocation(args, criterion)
    if not command.isprintable() or len(command.encode("utf-8")) > 4096:
        raise Refusal("preflight invocation exceeds the progressive report bound")
    evidence_record = _digested_record(
        {
            "candidate": args.candidate,
            "criterion": criterion,
            "facts": evidence,
            "invocation": command,
            "schema": f"{SCHEMA_PREFIX}-preflight-evidence/v1",
        }
    )
    evidence_raw = _canonical_json(evidence_record)
    if len(evidence_raw) > MAX_JSON_BYTES:
        raise Refusal("preflight evidence exceeds the progressive report bound")
    record = {
        "candidate": args.candidate,
        "command": command,
        "criterion": criterion,
        "exit": 0,
        "schema": "protasis-design-report/v1",
        "unit": "boolean",
        "value": value,
    }
    raw = _canonical_json(record)
    evidence_report = report.with_name(f"{report.stem}-evidence.json")
    _publish_committed_set(
        [(evidence_report, evidence_raw), (report, raw)], terminal=report
    )
    return _result(
        criterion,
        raw,
        {
            "candidate": args.candidate,
            "evidence_sha256": evidence_record["sha256"],
            "metadata_get_count": evidence.get("metadata_get_count", 0),
            "paid_or_answer_calls": 0,
            "value": value,
        },
    )


def _catalog_rows(record: dict[str, Any], label: str) -> list[dict[str, Any]]:
    rows = record.get("data")
    if not isinstance(rows, list) or len(rows) > 100_000:
        raise Refusal(f"{label} catalog shape drift")
    if not all(isinstance(row, dict) for row in rows):
        raise Refusal(f"{label} catalog contains a non-object row")
    return rows


def _eligible_zdr_routes(
    frozen: dict[str, Any], rows: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    return [
        row
        for row in rows
        if row.get("model_id") == frozen["id"]
        and row.get("provider_name") in frozen["ordered_provider_policy"]
        and row.get("status") == 0
        and {"response_format", "structured_outputs"}
        <= set(row.get("supported_parameters", []))
    ]


def _pricing_values(pricing: Any, field: str, label: str) -> list[Decimal]:
    if not isinstance(pricing, dict):
        raise Refusal(f"{label} pricing is missing")
    values = [_decimal(pricing.get(field), f"{label} {field} price")]
    overrides = pricing.get("overrides", [])
    if not isinstance(overrides, list):
        raise Refusal(f"{label} pricing overrides are malformed")
    for index, override in enumerate(overrides):
        if not isinstance(override, dict):
            raise Refusal(f"{label} pricing override is malformed")
        if field in override:
            values.append(
                _decimal(override[field], f"{label} override {index} {field} price")
            )
    return values


def _worst_eligible_prices(
    frozen: dict[str, Any], routes: list[dict[str, Any]]
) -> tuple[Decimal, Decimal]:
    if not routes:
        raise Refusal(f"model has no active frozen ZDR route: {frozen['id']}")
    if not frozen.get("ordered_provider_policy"):
        raise Refusal("model provider policy is empty")
    prompt: list[Decimal] = []
    completion: list[Decimal] = []
    for row in routes:
        label = f"{frozen['id']} {row.get('provider_name')}"
        prompt.extend(_pricing_values(row.get("pricing"), "prompt", label))
        completion.extend(
            _pricing_values(row.get("pricing"), "completion", label)
        )
    return max(prompt), max(completion)


def _matrix_gross_bound(
    preregistration: dict[str, Any],
    manifest: dict[str, Any],
    endpoints: list[dict[str, Any]],
    fee_rate: Decimal,
    packet: dict[str, Any],
) -> tuple[Decimal, dict[str, dict[str, str]], Decimal, dict[str, Any]]:
    bounds = preregistration["gross_budget_bounds"]
    prompt_bounds = bounds["max_prompt_tokens_per_arm_case"]
    calls_per_arm_model = bounds["case_count_per_cohort"] * bounds["cohorts"]
    attempts = bounds["retry_attempts_per_logical_call"]
    output_tokens = bounds["max_output_tokens_per_attempt"]
    subtotal = Decimal(0)
    prices: dict[str, dict[str, str]] = {}
    exact_prices: dict[str, tuple[Decimal, Decimal]] = {}
    for frozen in manifest["models"]:
        routes = _eligible_zdr_routes(frozen, endpoints)
        prompt_price, completion_price = _worst_eligible_prices(frozen, routes)
        model_input = sum(
            (_decimal(value, f"{arm} prompt bound") for arm, value in prompt_bounds.items()),
            Decimal(0),
        )
        model_subtotal = (
            model_input * prompt_price
            + Decimal(len(prompt_bounds)) * output_tokens * completion_price
        ) * calls_per_arm_model * attempts
        subtotal += model_subtotal
        prices[frozen["id"]] = {
            "completion": str(completion_price),
            "prompt": str(prompt_price),
        }
        exact_prices[frozen["id"]] = (prompt_price, completion_price)
    order = packet.get("logical_call_order")
    if (
        packet.get("batching_sha256")
        != _sha256(_canonical_json(_expected_behavioral_batching()))
        or not isinstance(order, list)
        or len(order) != BEHAVIORAL_LOGICAL_CALLS
        or [item.get("batch_index") for item in order]
        != list(range(BEHAVIORAL_LOGICAL_CALLS))
    ):
        raise Refusal("frozen logical-call permutation drift")
    variant_to_arm = {
        _sha256(
            ("framework-74-arm\0" + item["control_sha256"]).encode("utf-8")
        ): item["id"]
        for item in preregistration["arms"]
    }
    first = order[0]
    model_id = first.get("model_id")
    arm = variant_to_arm.get(first.get("variant_commitment"))
    if model_id not in exact_prices or arm not in prompt_bounds:
        raise Refusal("first frozen logical call cannot be priced")
    prompt_price, completion_price = exact_prices[model_id]
    next_reservation = (
        _decimal(prompt_bounds[arm], f"{arm} prompt bound") * prompt_price
        + Decimal(output_tokens) * completion_price
    ) * Decimal(attempts) * (Decimal(1) + fee_rate)
    next_call = {
        key: first[key]
        for key in (
            "batch_index",
            "call_id",
            "case_commitment",
            "cohort",
            "model_id",
            "pair_id",
            "variant_commitment",
        )
    }
    return (
        subtotal * (Decimal(1) + fee_rate),
        prices,
        next_reservation,
        next_call,
    )


def preflight_spend(args: argparse.Namespace) -> bytes:
    maximum = _decimal(args.max_gross_usd, "requested gross ceiling")
    authority, authority_raw = _load_record(args.authority)
    _validate_authority(authority, maximum)
    preregistration, _ = _load_fixture_record(BEHAVIORAL_PREREGISTRATION)
    seal, _ = _load_fixture_record(
        EXPERIMENT_FIXTURE_ROOT / "holdout-seal.json"
    )
    _validate_behavioral_preregistration(preregistration, seal)
    manifest, manifest_raw = _load_fixture_record(MODEL_RUNTIME_MANIFEST)
    _validate_model_runtime_manifest(manifest)
    frozen_packet = _load_frozen_packet(
        FROZEN_BEHAVIORAL_ROOT,
        _opaque_behavioral_packet(preregistration, seal),
        allowed_directories=("native",),
    )
    packet = _decode_record(frozen_packet["packet.json"])
    credential_path = authority.get("credential", {}).get("file")
    if not isinstance(credential_path, str):
        raise Refusal("credential location is missing")
    credential = _external_secret(credential_path)
    try:
        account = _http_json(OPENROUTER_ENDPOINTS["account"], credential)
        credits = _http_json(OPENROUTER_ENDPOINTS["credits"], credential)
    finally:
        credential = b""
    data = account.get("data", account)
    if not isinstance(data, dict):
        raise Refusal("OpenRouter key metadata shape drift")
    usage_fields = ("usage", "usage_daily", "usage_weekly", "usage_monthly")
    for field in usage_fields:
        if field in data and data[field] is not None:
            _decimal(data[field], f"OpenRouter {field}")
    remaining = data.get("limit_remaining")
    if remaining is not None:
        _decimal(remaining, "OpenRouter limit remaining")
    credit_data = credits.get("data", credits)
    if not isinstance(credit_data, dict):
        raise Refusal("OpenRouter credit metadata shape drift")
    total_credits = _decimal(
        credit_data.get("total_credits"), "OpenRouter total credits"
    )
    total_usage = _decimal(
        credit_data.get("total_usage"), "OpenRouter total usage"
    )
    if total_usage > total_credits:
        raise Refusal("OpenRouter credit usage exceeds total credits")
    available_credit = total_credits - total_usage
    endpoints = _catalog_rows(
        _http_json(OPENROUTER_ENDPOINTS["zdr"]), "OpenRouter ZDR endpoint"
    )
    fee_rate = _decimal(authority["reservation"]["fee_rate"], "reservation fee")
    gross_bound, prices, next_reservation, next_call = _matrix_gross_bound(
        preregistration, manifest, endpoints, fee_rate, packet
    )
    ledger = authority["ledger"]
    existing = sum(
        (_decimal(ledger[field], field) for field in (
            "reserved_gross",
            "settled_gross",
            "uncertain_gross",
        )),
        Decimal(0),
    )
    if existing + gross_bound > maximum:
        raise Refusal(
            "conservative seven-model gross bound "
            f"{gross_bound} USD exceeds the authorised {maximum} USD ceiling; "
            "authority amendment required before publishing a pass report"
        )
    if available_credit < next_reservation:
        raise Refusal(
            "proved OpenRouter available credit "
            f"{available_credit} USD does not cover the next frozen atomic "
            f"reservation {next_reservation} USD"
        )
    budget_reservation(authority, next_reservation)
    price_digest = _sha256(_canonical_json(prices))
    return _publish_preflight_report(
        args,
        "paid-evaluation-preflight",
        {
            "account_endpoint": OPENROUTER_ENDPOINTS["account"],
            "available_credit": str(available_credit),
            "authority_sha256": _sha256(authority_raw),
            "credential_use": "authorization-header-only-not-retained",
            "credit_endpoint": OPENROUTER_ENDPOINTS["credits"],
            "gross_bound": str(gross_bound),
            "gross_ceiling": str(maximum),
            "key_valid": True,
            "metadata_get_count": 3,
            "metadata_get_endpoints": [
                OPENROUTER_ENDPOINTS["account"],
                OPENROUTER_ENDPOINTS["credits"],
                OPENROUTER_ENDPOINTS["zdr"],
            ],
            "next_atomic_call": next_call,
            "next_atomic_reservation": str(next_reservation),
            "paid_or_answer_calls": 0,
            "pricing_sha256": price_digest,
            "proved_total_credits": str(total_credits),
            "proved_total_usage": str(total_usage),
            "requires_authority_amendment": False,
            "runtime_manifest_sha256": _sha256(manifest_raw),
        },
    )


def preflight_model_matrix(args: argparse.Namespace) -> bytes:
    requested = tuple(args.models.split(","))
    if requested != MODEL_IDS or args.require_zdr is not True:
        raise Refusal("model matrix differs from the frozen seven-model ZDR set")
    manifest, manifest_raw = _load_fixture_record(MODEL_RUNTIME_MANIFEST)
    _validate_model_runtime_manifest(manifest)
    models = _catalog_rows(
        _http_json(OPENROUTER_ENDPOINTS["models"]), "OpenRouter model"
    )
    endpoints = _catalog_rows(
        _http_json(OPENROUTER_ENDPOINTS["zdr"]), "OpenRouter ZDR endpoint"
    )
    by_model: dict[str, dict[str, Any]] = {}
    for row in models:
        identifier = row.get("id")
        if isinstance(identifier, str) and identifier not in by_model:
            by_model[identifier] = row
    endpoint_rows: dict[str, list[dict[str, Any]]] = {
        identifier: [] for identifier in MODEL_IDS
    }
    for row in endpoints:
        identifier = row.get("model_id")
        if identifier in endpoint_rows:
            endpoint_rows[identifier].append(row)
    frozen = {row["id"]: row for row in manifest["models"]}
    selected: list[dict[str, Any]] = []
    for identifier in MODEL_IDS:
        catalog = by_model.get(identifier)
        if catalog is None:
            raise Refusal(f"model is absent from the OpenRouter catalog: {identifier}")
        pricing = catalog.get("pricing")
        architecture = catalog.get("architecture")
        if not isinstance(pricing, dict) or not isinstance(architecture, dict):
            raise Refusal(f"model catalog metadata is incomplete: {identifier}")
        prompt_price = _decimal(pricing.get("prompt"), f"{identifier} prompt price")
        completion_price = _decimal(
            pricing.get("completion"), f"{identifier} completion price"
        )
        if (
            catalog.get("context_length") != frozen[identifier]["context_length"]
            or architecture.get("tokenizer") != frozen[identifier]["tokenizer"]
        ):
            raise Refusal(f"frozen model identity drift: {identifier}")
        active = _eligible_zdr_routes(frozen[identifier], endpoint_rows[identifier])
        if not active:
            raise Refusal(f"model has no active frozen ZDR route: {identifier}")
        worst_prompt, worst_completion = _worst_eligible_prices(
            frozen[identifier], active
        )
        provider = min(
            (row["provider_name"] for row in active),
            key=frozen[identifier]["ordered_provider_policy"].index,
        )
        selected.append(
            {
                "completion": str(worst_completion),
                "id": identifier,
                "prompt": str(worst_prompt),
                "provider": provider,
            }
        )
    matrix_raw = _canonical_json({"models": selected})
    return _publish_preflight_report(
        args,
        "seven-model-preflight",
        {
            "catalog_endpoints": [
                OPENROUTER_ENDPOINTS["models"],
                OPENROUTER_ENDPOINTS["zdr"],
            ],
            "manifest_sha256": _sha256(manifest_raw),
            "matrix_sha256": _sha256(matrix_raw),
            "metadata_get_count": 2,
            "metadata_get_endpoints": [
                OPENROUTER_ENDPOINTS["models"],
                OPENROUTER_ENDPOINTS["zdr"],
            ],
            "models": len(selected),
            "model_substitution": False,
            "paid_or_answer_calls": 0,
            "zdr_required": True,
        },
    )


def _resolved_runtime_executable(name: str) -> Path:
    if name not in {"claude", "codex"}:
        raise Refusal("runtime executable is outside the frozen allowlist")
    located = shutil.which(name)
    if located is None:
        raise Refusal(f"runtime executable is unavailable: {name}")
    try:
        resolved = Path(located).resolve(strict=True)
        metadata = resolved.stat()
    except OSError as exc:
        raise Refusal(f"runtime executable is unavailable: {name}") from exc
    if (
        not resolved.is_absolute()
        or not stat.S_ISREG(metadata.st_mode)
        or not metadata.st_mode & 0o111
        or metadata.st_mode & 0o022
    ):
        raise Refusal(f"runtime executable is unsafe: {name}")
    return resolved


def _external_file_digest(path: Path, limit: int = 256 * 1024 * 1024) -> str:
    try:
        descriptor = os.open(
            path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        )
    except OSError as exc:
        raise Refusal("external file is unavailable or unsafe") from exc
    try:
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or metadata.st_size > limit
        ):
            raise Refusal("external file metadata is unsafe")
        digest = hashlib.sha256()
        remaining = metadata.st_size
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                raise Refusal("external file ended before its declared size")
            digest.update(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
        if _identity(metadata) != _identity(after):
            raise Refusal("external file changed during hashing")
        return digest.hexdigest()
    finally:
        os.close(descriptor)


def _bounded_process(
    argv: list[str],
    *,
    environment: dict[str, str],
    cwd: Path,
    timeout: int = 20,
    limit: int = MAX_COMMAND_OUTPUT_BYTES,
) -> tuple[int, bytes, bytes]:
    if (
        not argv
        or timeout <= 0
        or timeout > 60
        or limit <= 0
        or limit > MAX_COMMAND_OUTPUT_BYTES
    ):
        raise Refusal("bounded command parameters are invalid")
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            cwd=cwd,
            start_new_session=True,
        )
    except OSError as exc:
        raise Refusal("bounded runtime metadata command failed to start") from exc
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stderr = bytearray()
    deadline = time.monotonic() + timeout
    completed = False
    try:
        selector.register(process.stdout, selectors.EVENT_READ, (stdout, limit))
        selector.register(process.stderr, selectors.EVENT_READ, (stderr, limit))
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise Refusal("bounded runtime metadata command timed out")
            events = selector.select(remaining)
            if not events:
                raise Refusal("bounded runtime metadata command timed out")
            for key, _ in events:
                buffer, cap = key.data
                try:
                    chunk = os.read(key.fd, min(65_536, cap + 1 - len(buffer)))
                except OSError as exc:
                    raise Refusal("bounded runtime metadata capture failed") from exc
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffer.extend(chunk)
                if len(buffer) > cap:
                    raise Refusal("bounded runtime metadata output exceeded its limit")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise Refusal("bounded runtime metadata command timed out")
        try:
            code = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise Refusal("bounded runtime metadata command timed out") from exc
        completed = True
        return code, bytes(stdout), bytes(stderr)
    finally:
        selector.close()
        if not completed:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            except OSError:
                try:
                    process.kill()
                except OSError:
                    pass
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            pass


def _runtime_environment(state_name: str, state_path: Path) -> dict[str, str]:
    path = os.environ.get("PATH")
    if not path:
        raise Refusal("runtime PATH is unavailable")
    environment = {
        "HOME": str(state_path),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "NO_COLOR": "1",
        "PATH": path,
    }
    environment[state_name] = str(state_path)
    return environment


def _safe_external_metadata(path: Path, maximum: int) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise Refusal("authentication bootstrap source is unavailable") from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_nlink != 1
        or metadata.st_uid != os.getuid()
        or metadata.st_mode & 0o077
        or metadata.st_size <= 0
        or metadata.st_size > maximum
    ):
        raise Refusal("authentication bootstrap source metadata is unsafe")
    return {
        "identity": _rename_stable_identity(metadata),
        "mode": stat.S_IMODE(metadata.st_mode),
        "size": metadata.st_size,
    }


def _copy_external_auth(source: Path, destination: Path, maximum: int) -> None:
    """Copy bounded auth bytes into a fresh isolated store, never into a report."""
    metadata = _safe_external_metadata(source, maximum)
    source_fd: int | None = None
    destination_fd: int | None = None
    try:
        source_fd = os.open(
            source, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        )
        opened_source = os.fstat(source_fd)
        if _rename_stable_identity(opened_source) != metadata["identity"]:
            raise Refusal("auth bootstrap source changed while opening")
        destination_fd = os.open(
            destination,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
        copied = 0
        while copied < metadata["size"]:
            chunk = os.read(source_fd, min(65_536, metadata["size"] - copied))
            if not chunk:
                raise Refusal("auth bootstrap source ended early")
            view = memoryview(chunk)
            while view:
                written = os.write(destination_fd, view)
                if written <= 0:
                    raise Refusal("isolated auth bootstrap write failed")
                view = view[written:]
            copied += len(chunk)
        if os.read(source_fd, 1):
            raise Refusal("auth bootstrap source grew during copy")
        after_source = os.fstat(source_fd)
        try:
            named_source = source.lstat()
        except OSError as exc:
            raise Refusal("auth bootstrap source changed during copy") from exc
        if not (
            _rename_stable_identity(opened_source)
            == _rename_stable_identity(after_source)
            == _rename_stable_identity(named_source)
        ):
            raise Refusal("auth bootstrap source changed during copy")
        os.fsync(destination_fd)
        destination_metadata = os.fstat(destination_fd)
        if (
            copied != metadata["size"]
            or not stat.S_ISREG(destination_metadata.st_mode)
            or destination_metadata.st_nlink != 1
            or stat.S_IMODE(destination_metadata.st_mode) != 0o600
        ):
            raise Refusal("isolated auth bootstrap output metadata drift")
    except OSError as exc:
        raise Refusal("isolated auth bootstrap is unavailable or unsafe") from exc
    finally:
        if destination_fd is not None:
            os.close(destination_fd)
        if source_fd is not None:
            os.close(source_fd)


def _write_isolated_secret(raw: bytes, destination: Path, maximum: int) -> int:
    payload = raw.rstrip(b"\r\n")
    if not payload or len(payload) > maximum or b"\x00" in payload:
        raise Refusal("isolated credential payload is empty or over limit")
    try:
        descriptor = os.open(
            destination,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0),
            0o600,
        )
    except OSError as exc:
        raise Refusal("isolated credential destination is unsafe") from exc
    try:
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise Refusal("isolated credential write failed")
            view = view[written:]
        os.fsync(descriptor)
        metadata = os.fstat(descriptor)
        if (
            not stat.S_ISREG(metadata.st_mode)
            or metadata.st_nlink != 1
            or stat.S_IMODE(metadata.st_mode) != 0o600
            or metadata.st_size != len(payload)
        ):
            raise Refusal("isolated credential destination metadata drift")
    finally:
        os.close(descriptor)
    return len(payload)


def _macos_claude_credential(maximum: int) -> bytes:
    security = Path("/usr/bin/security")
    try:
        resolved = security.resolve(strict=True)
        metadata = resolved.stat()
    except OSError as exc:
        raise Refusal("macOS security executable is unavailable") from exc
    if (
        not stat.S_ISREG(metadata.st_mode)
        or metadata.st_uid != 0
        or metadata.st_mode & 0o022
        or not metadata.st_mode & 0o111
    ):
        raise Refusal("macOS security executable is unsafe")
    account = pwd.getpwuid(os.getuid()).pw_name
    if not re.fullmatch(r"[A-Za-z0-9._-]{1,128}", account):
        raise Refusal("local account name is unsafe for keychain lookup")
    environment = {
        "HOME": str(Path.home()),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PATH": "/usr/bin:/bin",
    }
    code, stdout, _ = _bounded_process(
        [
            str(resolved),
            "find-generic-password",
            "-a",
            account,
            "-w",
            "-s",
            "Claude Code-credentials",
        ],
        environment=environment,
        cwd=ROOT,
        limit=maximum,
    )
    if code != 0:
        raise Refusal("default Claude keychain credential is unavailable")
    return stdout


def _read_generated_schema_bundle(root: Path) -> tuple[str, list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    total = 0
    entries_seen = 0
    root_descriptor: int | None = None

    def walk(directory: int, prefix: PurePosixPath, depth: int) -> None:
        nonlocal entries_seen, total
        if depth > 32:
            raise Refusal("Codex generated schema bundle exceeds its depth limit")
        before_directory = os.fstat(directory)
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    entries_seen += 1
                    if entries_seen > 4096:
                        raise Refusal(
                            "Codex generated schema bundle exceeds its entry limit"
                        )
                    relative_path = prefix / entry.name
                    relative = _safe_relative(relative_path.as_posix())
                    try:
                        entry_metadata = entry.stat(follow_symlinks=False)
                    except OSError as exc:
                        raise Refusal(
                            "Codex generated schema entry changed during enumeration"
                        ) from exc
                    if entry.is_symlink():
                        raise Refusal("Codex generated schema contains a symlink")
                    if stat.S_ISDIR(entry_metadata.st_mode):
                        try:
                            child = os.open(
                                entry.name, _directory_flags(), dir_fd=directory
                            )
                        except OSError as exc:
                            raise Refusal(
                                "Codex generated schema directory is unsafe"
                            ) from exc
                        try:
                            opened = os.fstat(child)
                            if _identity(entry_metadata) != _identity(opened):
                                raise Refusal(
                                    "Codex generated schema directory changed while opening"
                                )
                            walk(child, relative, depth + 1)
                            named = os.stat(
                                entry.name,
                                dir_fd=directory,
                                follow_symlinks=False,
                            )
                            if _identity(opened) != _identity(named):
                                raise Refusal(
                                    "Codex generated schema directory changed during read"
                                )
                        finally:
                            os.close(child)
                        continue
                    if not stat.S_ISREG(entry_metadata.st_mode):
                        raise Refusal(
                            "Codex generated schema contains a special entry"
                        )
                    if relative.suffix != ".json":
                        raise Refusal(
                            "Codex generated schema contains a non-JSON file"
                        )
                    if len(records) >= 2048:
                        raise Refusal(
                            "Codex generated schema bundle cardinality drift"
                        )
                    try:
                        source = os.open(
                            entry.name,
                            _regular_read_flags(),
                            dir_fd=directory,
                        )
                    except OSError as exc:
                        raise Refusal(
                            "Codex generated schema file is unsafe"
                        ) from exc
                    try:
                        opened = os.fstat(source)
                        if _rename_stable_identity(entry_metadata) != (
                            _rename_stable_identity(opened)
                        ):
                            raise Refusal(
                                "Codex generated schema file changed while opening"
                            )
                        raw, after = _read_descriptor(source, MAX_JSON_BYTES)
                    finally:
                        os.close(source)
                    try:
                        named = os.stat(
                            entry.name,
                            dir_fd=directory,
                            follow_symlinks=False,
                        )
                    except OSError as exc:
                        raise Refusal(
                            "Codex generated schema file changed during read"
                        ) from exc
                    if not (
                        _rename_stable_identity(opened)
                        == _rename_stable_identity(after)
                        == _rename_stable_identity(named)
                    ):
                        raise Refusal(
                            "Codex generated schema file changed during read"
                        )
                    total += len(raw)
                    if total > 64 * 1024 * 1024:
                        raise Refusal(
                            "Codex generated schema bundle exceeds its byte limit"
                        )
                    value = _decode_external_json(
                        raw, "Codex generated schema file"
                    )
                    records.append(
                        {
                            "bytes": len(raw),
                            "path": relative.as_posix(),
                            "sha256": _sha256(raw),
                            "value": value,
                        }
                    )
        except OSError as exc:
            raise Refusal("Codex generated schema enumeration failed") from exc
        after_directory = os.fstat(directory)
        if _rename_stable_identity(before_directory) != _rename_stable_identity(
            after_directory
        ):
            raise Refusal("Codex generated schema directory changed during read")

    try:
        root_metadata = root.lstat()
        if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(
            root_metadata.st_mode
        ):
            raise Refusal("Codex generated schema root is unsafe")
        root_descriptor = os.open(root, _directory_flags())
        opened_root = os.fstat(root_descriptor)
        if _identity(root_metadata) != _identity(opened_root):
            raise Refusal("Codex generated schema root changed while opening")
        walk(root_descriptor, PurePosixPath(), 0)
        try:
            named_root = root.lstat()
        except OSError as exc:
            raise Refusal("Codex generated schema root changed during read") from exc
        if _identity(opened_root) != _identity(named_root):
            raise Refusal("Codex generated schema root changed during read")
    except OSError as exc:
        raise Refusal("Codex generated schema root is unavailable") from exc
    finally:
        if root_descriptor is not None:
            os.close(root_descriptor)
    if not records:
        raise Refusal("Codex generated schema bundle cardinality drift")
    records.sort(key=lambda item: item["path"])
    digest_input = _canonical_json(
        {
            "files": [
                {key: item[key] for key in ("bytes", "path", "sha256")}
                for item in records
            ]
        }
    )
    return _sha256(digest_input), records


def _schema_contains_property_set(value: Any, required: set[str]) -> bool:
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict) and required <= set(properties):
            return True
        return any(
            _schema_contains_property_set(child, required)
            for child in value.values()
        )
    if isinstance(value, list):
        return any(_schema_contains_property_set(child, required) for child in value)
    return False


def _schema_contains_string(value: Any, needle: str) -> bool:
    if isinstance(value, dict):
        return needle in value or any(
            _schema_contains_string(child, needle) for child in value.values()
        )
    if isinstance(value, list):
        return any(_schema_contains_string(child, needle) for child in value)
    return value == needle


def _validate_codex_schema_bundle(records: list[dict[str, Any]]) -> None:
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
    ):
        if not any(
            _schema_contains_string(item["value"], token) for item in records
        ):
            raise Refusal(f"Codex experimental protocol schema omits {token!r}")
    start_fields = {
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
    }
    if not any(
        _schema_contains_property_set(item["value"], start_fields)
        for item in records
    ):
        raise Refusal("Codex thread/start request does not validate against its schema")


@contextmanager
def _private_system_temporary_directory() -> Iterator[Path]:
    """Create one private temp root without consulting repository paths."""
    with tempfile.TemporaryDirectory(
        prefix="framework-74-native-preflight-"
    ) as temporary:
        root = Path(temporary)
        descriptor: int | None = None
        try:
            named = root.lstat()
            if (
                stat.S_ISLNK(named.st_mode)
                or not stat.S_ISDIR(named.st_mode)
                or named.st_uid != os.getuid()
                or stat.S_IMODE(named.st_mode) != 0o700
            ):
                raise Refusal("system temporary root is not private")
            descriptor = os.open(root, _directory_flags())
            opened = os.fstat(descriptor)
            if (
                _directory_identity(named) != _directory_identity(opened)
                or opened.st_uid != os.getuid()
            ):
                raise Refusal("system temporary root changed while opening")
            try:
                yield root
            finally:
                current = root.lstat()
                if (
                    _directory_identity(opened)
                    != _directory_identity(os.fstat(descriptor))
                    or _directory_identity(opened) != _directory_identity(current)
                    or current.st_uid != os.getuid()
                ):
                    raise Refusal("system temporary root changed during use")
        except OSError as exc:
            raise Refusal("system temporary root is unavailable or unsafe") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)


def preflight_native_gate(args: argparse.Namespace) -> bytes:
    if args.no_session is not True or tuple(args.runtimes.split(",")) != NATIVE_RUNTIMES:
        raise Refusal("native preflight requires the frozen runtimes and --no-session")
    manifest, manifest_raw = _load_fixture_record(NATIVE_RUNTIME_MANIFEST)
    _validate_native_runtime_manifest(manifest)
    by_id = {row["id"]: row for row in manifest["runtimes"]}
    identities: dict[str, dict[str, Any]] = {}
    resolved_executables: dict[str, Path] = {}
    with _private_system_temporary_directory() as state_root:
        for runtime_id, state_name in (
            ("claude-code", "CLAUDE_CONFIG_DIR"),
            ("codex", "CODEX_HOME"),
        ):
            runtime = by_id[runtime_id]
            executable = _resolved_runtime_executable(runtime["executable"])
            resolved_executables[runtime_id] = executable
            isolated = state_root / runtime_id
            isolated.mkdir(mode=0o700)
            environment = _runtime_environment(state_name, isolated)
            version_argv = [str(executable), *runtime["version"]["command"][1:]]
            code, stdout, stderr = _bounded_process(
                version_argv, environment=environment, cwd=ROOT
            )
            version = (stdout + stderr).decode("utf-8", errors="strict").strip()
            if code != 0 or version != runtime["version"]["expected"]:
                raise Refusal(f"native runtime version drift: {runtime_id}")
            auth_argv = [
                str(executable), *runtime["authentication"]["command"][1:]
            ]
            auth_code, auth_stdout, auth_stderr = _bounded_process(
                auth_argv, environment=environment, cwd=ROOT
            )
            if runtime_id == "claude-code":
                auth = _decode_external_json(
                    auth_stdout or auth_stderr, "Claude isolated auth status"
                )
                if auth.get("loggedIn") is not False or auth_code == 0:
                    raise Refusal("fresh Claude state unexpectedly inherited authentication")
                bootstrap = runtime["authentication"]["isolated_bootstrap"]
                credential = _macos_claude_credential(
                    bootstrap["size_limit_bytes"]
                )
                _write_isolated_secret(
                    credential,
                    isolated / ".credentials.json",
                    bootstrap["size_limit_bytes"],
                )
                credential = b""
                auth_code, auth_stdout, auth_stderr = _bounded_process(
                    auth_argv, environment=environment, cwd=ROOT
                )
                auth = _decode_external_json(
                    auth_stdout or auth_stderr, "Claude isolated auth status"
                )
                if auth_code != 0 or auth.get("loggedIn") is not True:
                    raise Refusal("isolated Claude credential bootstrap did not authenticate")
                isolated_auth = "bounded-keychain-bootstrap-authenticated"
            else:
                auth_text = (auth_stdout + auth_stderr).decode(
                    "utf-8", errors="strict"
                )
                if auth_code == 0 or "Not logged in" not in auth_text:
                    raise Refusal("fresh Codex state unexpectedly inherited authentication")
                bootstrap = runtime["authentication"]["isolated_bootstrap"]
                source = Path.home() / ".codex/auth.json"
                metadata = _safe_external_metadata(
                    source, bootstrap["size_limit_bytes"]
                )
                if metadata["mode"] != 0o600:
                    raise Refusal("Codex auth bootstrap source mode drift")
                _copy_external_auth(
                    source, isolated / "auth.json", bootstrap["size_limit_bytes"]
                )
                auth_code, auth_stdout, auth_stderr = _bounded_process(
                    auth_argv, environment=environment, cwd=ROOT
                )
                auth_text = (auth_stdout + auth_stderr).decode(
                    "utf-8", errors="strict"
                )
                if auth_code != 0 or runtime["authentication"]["pass_stdout"] not in auth_text:
                    raise Refusal("isolated Codex auth bootstrap did not authenticate")
                isolated_auth = "bounded-copy-authenticated"
            identities[runtime_id] = {
                "executable_basename": runtime["executable"],
                "executable_sha256": _external_file_digest(executable),
                "isolated_auth": isolated_auth,
                "resolution_class": "closed-name-from-PATH",
                "version": version,
            }
        codex = by_id["codex"]
        codex_executable = resolved_executables["codex"]
        schema_root = state_root / "codex-schema"
        schema_state = state_root / "codex-schema-state"
        schema_state.mkdir(mode=0o700)
        schema_command = codex["protocol_schema"]["command"]
        schema_argv = [
            str(codex_executable),
            *[
                str(schema_root) if item == "{temporary_schema_root}" else item
                for item in schema_command[1:]
            ],
        ]
        code, stdout, stderr = _bounded_process(
            schema_argv,
            environment=_runtime_environment("CODEX_HOME", schema_state),
            cwd=ROOT,
            timeout=60,
        )
        if code != 0:
            raise Refusal("Codex experimental schema generation failed")
        schema_digest, schema_records = _read_generated_schema_bundle(schema_root)
        _validate_codex_schema_bundle(schema_records)
    identities["codex"]["experimental_schema_sha256"] = schema_digest
    return _publish_preflight_report(
        args,
        "native-gate-preflight",
        {
            "manifest_sha256": _sha256(manifest_raw),
            "metadata_get_count": 0,
            "metadata_get_endpoints": [],
            "no_native_session": True,
            "paid_or_answer_calls": 0,
            "resolved": identities,
            "runtime_count": len(identities),
            "isolated_authentication_proved": True,
        },
    )


def _publish_emitted_packet(output: Path, packet: dict[str, bytes]) -> None:
    terminal = output / "manifest.json"
    _publish_committed_set(
        [
            (output / "packet.json", packet["packet.json"]),
            (terminal, packet["manifest.json"]),
        ],
        terminal=terminal,
    )


def emit_packet(args: argparse.Namespace) -> bytes:
    if args.commitment_only is not True:
        raise Refusal("behavioral packet emission requires --commitment-only")
    output = _confined_output(
        args.output, "behavioral packet emission output", exact=(), roots=(SCRATCH_ROOT,)
    )
    preregistration, _ = _load_record(args.preregistration)
    seal, _ = _load_record(args.seal)
    _validate_behavioral_preregistration(preregistration, seal)
    packet = _opaque_behavioral_packet(preregistration, seal)
    packet = _load_frozen_packet(
        FROZEN_BEHAVIORAL_ROOT, packet, allowed_directories=("native",)
    )
    commitment, commitment_raw = _load_fixture_record(BEHAVIORAL_COMMITMENT)
    _verify_packet_commitment(
        preregistration,
        commitment,
        f"{SCHEMA_PREFIX}-holdout-packet-commitment/v1",
        packet,
    )
    _publish_emitted_packet(output, packet)
    return _result(
        "emit-packet",
        commitment_raw,
        {"answer_bytes": 0, "artifacts": len(packet)},
    )


def emit_native_packet(args: argparse.Namespace) -> bytes:
    if args.commitment_only is not True:
        raise Refusal("native packet emission requires --commitment-only")
    output = _confined_output(
        args.output, "native packet emission output", exact=(), roots=(SCRATCH_ROOT,)
    )
    preregistration, _ = _load_record(args.preregistration)
    _validate_native_preregistration(preregistration)
    packet = _opaque_native_packet(preregistration)
    packet = _load_frozen_packet(FROZEN_NATIVE_ROOT, packet)
    commitment, commitment_raw = _load_fixture_record(NATIVE_COMMITMENT)
    _verify_packet_commitment(
        preregistration,
        commitment,
        f"{SCHEMA_PREFIX}-native-lifecycle-packet-commitment/v1",
        packet,
    )
    _publish_emitted_packet(output, packet)
    return _result(
        "emit-native-packet",
        commitment_raw,
        {"answer_bytes": 0, "artifacts": len(packet), "sessions_launched": 0},
    )


def _path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(
        description="Build and verify the framework-74 source-bound research corpus."
    )
    subparsers = result.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-baseline")
    build.add_argument(
        "--output",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture",
    )
    build.add_argument(
        "--reconciliation",
        type=_path,
        default=ROOT / "docs/instruction-architecture/corpus-reconciliation.md",
    )
    build.set_defaults(handler=build_baseline)

    snapshot = subparsers.add_parser("snapshot-controls")
    snapshot.add_argument(
        "--output",
        type=_path,
        default=ROOT / Path(*CONTROL_SNAPSHOT_ROOT.parts),
    )
    snapshot.set_defaults(handler=snapshot_controls)

    development = subparsers.add_parser("build-development")
    development.add_argument("--manifest", type=_path, required=True)
    development.add_argument("--cohorts", type=_path, required=True)
    development.add_argument(
        "--output",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture/evidence/development",
    )
    development.set_defaults(handler=build_development)

    replay = subparsers.add_parser("replay")
    replay.add_argument("--cohort", required=True)
    replay.add_argument(
        "--evidence",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture/evidence/development",
    )
    replay.set_defaults(handler=replay_development)

    corpus = subparsers.add_parser("verify-corpus")
    corpus.add_argument("--manifest", type=_path, required=True)
    corpus.add_argument(
        "--profiles",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture/invocation-profiles.json",
    )
    corpus.set_defaults(handler=verify_corpus)

    profile_check = subparsers.add_parser("verify-profiles")
    profile_check.add_argument("--profiles", type=_path, required=True)
    profile_check.add_argument("--manifest", type=_path)
    profile_check.set_defaults(handler=verify_profiles)

    loader = subparsers.add_parser("verify-loader")
    loader.add_argument("--manifest", type=_path, required=True)
    loader.add_argument(
        "--profiles",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture/invocation-profiles.json",
    )
    loader.add_argument("--graph", type=_path, required=True)
    loader.set_defaults(handler=verify_loader)

    partition = subparsers.add_parser("verify-partition")
    partition.add_argument("--manifest", type=_path, required=True)
    partition.add_argument(
        "--profiles",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture/invocation-profiles.json",
    )
    partition.add_argument("--partition", type=_path, required=True)
    partition.set_defaults(handler=verify_partition)

    seal = subparsers.add_parser("verify-seal")
    seal.add_argument("--manifest", type=_path, required=True)
    seal.add_argument(
        "--profiles",
        type=_path,
        default=ROOT / "tests/fixtures/instruction-architecture/invocation-profiles.json",
    )
    seal.add_argument("--cohorts", type=_path, required=True)
    seal.add_argument("--seal", type=_path, required=True)
    seal.set_defaults(handler=verify_seal)
    for verifier in (corpus, profile_check, loader, partition, seal):
        verifier.add_argument(
            "--reconciliation",
            type=_path,
            help=(
                "bound reconciliation path; required for a scratch baseline and "
                "implicit for the committed fixture"
            ),
        )

    aggregate = subparsers.add_parser("aggregate-development")
    aggregate.add_argument(
        "--evidence",
        type=_path,
        default=ROOT / Path(*DEVELOPMENT_EVIDENCE_ROOT.parts),
    )
    aggregate.add_argument(
        "--output",
        type=_path,
        default=ROOT / Path(*DEVELOPMENT_SELECTION.parts),
    )
    aggregate.set_defaults(handler=aggregate_development)

    freeze = subparsers.add_parser("freeze-experiment")
    freeze.add_argument("--selection", type=_path, required=True)
    freeze.add_argument("--seal", type=_path, required=True)
    freeze.add_argument(
        "--output",
        type=_path,
        default=ROOT / Path(*FROZEN_BEHAVIORAL_ROOT.parts),
    )
    freeze.set_defaults(handler=freeze_experiment)

    native_freeze = subparsers.add_parser("freeze-native-gate")
    native_freeze.add_argument("--selection", type=_path, required=True)
    native_freeze.add_argument("--runtime-manifest", type=_path, required=True)
    native_freeze.add_argument(
        "--output",
        type=_path,
        default=ROOT / Path(*FROZEN_NATIVE_ROOT.parts),
    )
    native_freeze.set_defaults(handler=freeze_native_gate)

    native_verify = subparsers.add_parser("verify-native-preregistration")
    native_verify.add_argument("--preregistration", type=_path, required=True)
    native_verify.add_argument("--commitment", type=_path, required=True)
    native_verify.add_argument("--no-session", action="store_true")
    native_verify.set_defaults(handler=verify_native_preregistration)

    spend = subparsers.add_parser("preflight-spend")
    spend.add_argument("--candidate", required=True)
    spend.add_argument("--authority", type=_path, required=True)
    spend.add_argument("--max-gross-usd", required=True)
    spend.add_argument("--report", type=_path, required=True)
    spend.set_defaults(handler=preflight_spend)

    matrix = subparsers.add_parser("preflight-model-matrix")
    matrix.add_argument("--candidate", required=True)
    matrix.add_argument("--models", required=True)
    matrix.add_argument("--require-zdr", action="store_true")
    matrix.add_argument("--report", type=_path, required=True)
    matrix.set_defaults(handler=preflight_model_matrix)

    native_preflight = subparsers.add_parser("preflight-native-gate")
    native_preflight.add_argument("--candidate", required=True)
    native_preflight.add_argument("--runtimes", required=True)
    native_preflight.add_argument("--no-session", action="store_true")
    native_preflight.add_argument("--report", type=_path, required=True)
    native_preflight.set_defaults(handler=preflight_native_gate)

    emit = subparsers.add_parser("emit-packet")
    emit.add_argument("--preregistration", type=_path, required=True)
    emit.add_argument("--seal", type=_path, required=True)
    emit.add_argument("--commitment-only", action="store_true")
    emit.add_argument("--output", type=_path, required=True)
    emit.set_defaults(handler=emit_packet)

    emit_native = subparsers.add_parser("emit-native-packet")
    emit_native.add_argument("--preregistration", type=_path, required=True)
    emit_native.add_argument("--commitment-only", action="store_true")
    emit_native.add_argument("--output", type=_path, required=True)
    emit_native.set_defaults(handler=emit_native_packet)
    return result


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        sys.stdout.buffer.write(args.handler(args))
        return 0
    except Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
