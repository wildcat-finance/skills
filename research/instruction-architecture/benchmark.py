#!/usr/bin/env python3
"""Source-bound workbench for framework-74 instruction architecture research.

Step 1 owns the corpus, loader, byte partition, and sealed cohort boundary.
Later steps extend this CLI without changing the authority of the Markdown
sources recorded here.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import secrets
import selectors
import signal
import stat
import subprocess
import sys
import time
from bisect import bisect_left, bisect_right
from functools import lru_cache
from typing import Any, Iterable


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
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
        raise Refusal("input is not a single-link regular file")
    if before.st_size > limit:
        raise Refusal("input exceeds byte limit")
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
    if _identity(before) != _identity(after):
        raise Refusal("input changed during read")
    return b"".join(chunks), after


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
            if _identity(os.fstat(current)) != _identity(after):
                raise Refusal("input changed during read")
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
    try:
        names = [
            item.decode("utf-8", errors="strict") for item in raw.split(b"\0") if item
        ]
    except UnicodeDecodeError as exc:
        raise Refusal("Git tree contains a non-UTF-8 path") from exc
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
        """Recognise the bounded thematic-break forms before list markers."""
        return re.fullmatch(
            rb" {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})",
            line.rstrip(b"\r\n"),
        ) is not None

    def thematic_suffix_starts(line: bytes) -> set[int]:
        """Find homogeneous thematic suffixes in one backward pass."""
        end = len(line)
        while end and line[end - 1] in b" \t\r\n":
            end -= 1
        if not end or line[end - 1] not in b"*-_":
            return set()
        marker = line[end - 1]
        positions: list[int] = []
        cursor = end - 1
        while cursor >= 0 and line[cursor] == marker:
            positions.append(cursor)
            cursor -= 1
            while cursor >= 0 and line[cursor] in b" \t":
                cursor -= 1
        return set(positions[2:])

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
        thematic_starts = thematic_suffix_starts(line)
        while True:
            if byte_index in thematic_starts:
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
