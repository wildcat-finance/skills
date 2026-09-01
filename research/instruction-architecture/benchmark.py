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
from functools import lru_cache
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
SOURCE_REF = "a2b634d8e039af988bf30c8316defccf70071d8d"
SCHEMA_PREFIX = "wildcat-instruction-architecture"
SELECTION_SEED = "framework-74-holdout-v1-2026-08-31"
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_GIT_OUTPUT = 4 * 1024 * 1024
MAX_SOURCE_BYTES = 2 * 1024 * 1024
MAX_JSON_DEPTH = 64
MAX_JSON_TOKENS = 100_000
MAX_JSON_NUMBER_CHARS = 640
EXPECTED_COUNTS = {
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
    "physical_files": 188,
    "physical_bytes": 2_290_439,
    "unique_files": 171,
    "unique_bytes": 1_818_995,
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
    "loader-graph.json",
    "byte-partition.json",
    "cohorts.json",
    "holdout-seal.json",
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
    parent, name = _open_parent(relative, create=False, label="input")
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
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


def _load_record(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular(path, MAX_JSON_BYTES)
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


def _git(arguments: list[str], limit: int = MAX_GIT_OUTPUT) -> bytes:
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
            stdin=subprocess.DEVNULL,
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


@lru_cache(maxsize=256)
def _source_object(path: str) -> bytes:
    _safe_relative(path)
    return _git(["cat-file", "blob", f"{SOURCE_REF}:{path}"], MAX_SOURCE_BYTES)


def _source_blob(path: str) -> bytes:
    blob = _source_object(path)
    live = _read_regular(ROOT / path, MAX_SOURCE_BYTES)
    if live != blob:
        raise Refusal(f"source drift: {path}")
    return blob


@lru_cache(maxsize=1)
def _frozen_tree_paths() -> tuple[str, ...]:
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
    return {
        "occurrences": markdown["occurrences"],
        "markdown_targets": markdown["targets"],
        "structured_targets": sorted(structured),
        "mandatory_executable_targets": sorted(mandatory_executable),
        "targets": sorted(set(markdown["targets"]) | structured),
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


def build_manifest() -> dict[str, Any]:
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
        provisional.append(
            {
                "path": path,
                "logical_document": _logical_document(path, document_class),
                "document_class": document_class,
                "admission_kind": (
                    structured["admission_kind"]
                    if structured is not None
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
                    else "agent-or-prompt"
                ),
                "loader_roots": [],
                "scenario_reachability": [],
                "source_evidence": (
                    _evidence(
                        structured["source_path"], structured["source_needle"]
                    )
                    if structured is not None
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
    if set(closure["mandatory_executable_targets"]) != {
        path
        for path, metadata in _structured_metadata().items()
        if metadata["load_semantics"] == "mandatory-executable"
    }:
        raise Refusal("mandatory executable semantics disagree with live anchors")
    topology = _build_topology(provisional)
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


def _reference_link(
    owner: str, target: str, reachable: set[str]
) -> tuple[str, str] | None:
    target_path = PurePosixPath(target)
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
    for root in roots:
        adjacency: dict[str, set[str]] = {}
        for edge in edges:
            scope = edge[scope_field]
            if "*" in scope or root["id"] in scope:
                adjacency.setdefault(edge["source"], set()).add(edge["target"])
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


def _validate_complete_scenarios(
    topology: dict[str, Any], skill_paths: dict[str, str]
) -> None:
    """Refuse incomplete routes, undeclared conditions, and branch unions."""
    router = ".agents/skills/promise-machine/SKILL.md"
    portable = ".agents/skills/promise-machine/PORTABLE.md"
    root_rows = topology["scenario_roots"]
    roots = {item["id"]: item for item in root_rows}
    if len(roots) != len(root_rows):
        raise Refusal("duplicate scenario root")
    scenario_ids = set(roots)
    known_conditions = {
        edge["condition"]
        for edge in topology["scenario_edges"]
        if edge["condition"] is not None
    }
    expected_templates: dict[str, dict[str, str]] = {}
    for name, path in skill_paths.items():
        plugin = _plugin(path)
        if plugin is None:
            raise Refusal(f"scenario skill has no plugin: {path}")
        runtime = f"plugins/{plugin}/AGENTS.md"
        expected_templates[f"agent-skills:skill:{name}"] = {
            "node": router,
            "route": "agent-skills",
            "selected_skill": name,
        }
        expected_templates[f"repository:skill:{name}"] = {
            "node": "AGENTS.md",
            "route": "repository",
            "selected_skill": name,
        }
        expected_templates[f"standalone:{plugin}:skill:{name}"] = {
            "node": runtime,
            "route": "standalone",
            "selected_skill": name,
        }
    for edge in topology["scenario_edges"]:
        scope = edge["active_scenarios"]
        if not scope or "*" in scope or not set(scope) <= scenario_ids:
            raise Refusal("scenario edge has a wildcard or unknown scope")
        eligible = set(edge["eligible_base_scenarios"])
        if not eligible or not eligible <= set(expected_templates):
            raise Refusal("scenario edge has an unknown base scope")
        condition = edge["condition"]
        expected_scope = {
            identifier
            for identifier, root in roots.items()
            if root["base_scenario"] in eligible
            and (condition is None or condition in root["conditions"])
        }
        if set(scope) != expected_scope:
            raise Refusal("scenario edge scope is not condition-complete")
        if condition is not None and any(
            condition not in roots[identifier]["conditions"] for identifier in scope
        ):
            raise Refusal("conditional scenario edge leaks outside its condition")
    for identifier, root in roots.items():
        conditions = root["conditions"]
        if conditions != sorted(set(conditions)):
            raise Refusal(f"scenario conditions are not closed and sorted: {identifier}")
        if not set(conditions) <= known_conditions:
            raise Refusal(f"scenario names an unknown condition: {identifier}")
        if (root["mode"] == "unconditional") != (not conditions):
            raise Refusal(f"scenario mode disagrees with its conditions: {identifier}")
        base = expected_templates.get(root["base_scenario"])
        if (
            base is None
            or root["node"] != base["node"]
            or root["route"] != base["route"]
            or root["selected_skill"] != base["selected_skill"]
        ):
            raise Refusal(f"scenario has an invalid base binding: {identifier}")
        if not conditions and identifier != root["base_scenario"]:
            raise Refusal(f"scenario aliases an unconditional base: {identifier}")
    observed = _reachability_by_root(
        root_rows,
        topology["scenario_edges"],
        "active_scenarios",
    )
    reached = {
        identifier: {path for path, scopes in observed.items() if identifier in scopes}
        for identifier in roots
    }
    synkrisis_rules = "plugins/synkrisis/references/rules-v1.json"
    synkrisis_edges = [
        edge
        for edge in topology["scenario_edges"]
        if edge["target"] == synkrisis_rules
    ]
    if {
        edge["condition"] for edge in synkrisis_edges
    } != set(SYNKRISIS_RULE_OPERATIONS) or any(
        edge["kind"] != "mandatory-executable"
        or edge["load_type"] != "mandatory-executable"
        for edge in synkrisis_edges
    ):
        raise Refusal("Synkrisis rule operations are not exact and exclusive")
    for identifier, root in roots.items():
        operations = set(root["conditions"]) & set(SYNKRISIS_RULE_OPERATIONS)
        if len(operations) > 1 or (
            operations and root["selected_skill"] != "synkrisis"
        ):
            raise Refusal(f"Synkrisis scenario unions rule operations: {identifier}")
        expected_rules = (
            root["selected_skill"] == "synkrisis" and len(operations) == 1
        )
        if (synkrisis_rules in reached[identifier]) != expected_rules:
            raise Refusal(f"Synkrisis rule reachability is inexact: {identifier}")
    for operation in SYNKRISIS_RULE_OPERATIONS:
        if not any(
            root["selected_skill"] == "synkrisis"
            and operation in root["conditions"]
            for root in roots.values()
        ):
            raise Refusal(f"Synkrisis rule operation has no scenario: {operation}")
    scribe = "plugins/hexaemeron/agents/scribe.md"
    scribe_scenarios = {
        identifier for identifier in roots if scribe in reached[identifier]
    }
    if not scribe_scenarios or any(
        roots[identifier]["selected_skill"] != "fiat"
        for identifier in scribe_scenarios
    ):
        raise Refusal("Scribe reachability is not an exact Fiat phase invocation")
    for target, metadata in _structured_metadata().items():
        if metadata["load_semantics"] != "mandatory-executable" or target == synkrisis_rules:
            continue
        owner_skill = _skill_name(metadata["canonical_owner"])
        for identifier, root in roots.items():
            applicable = root["selected_skill"] == owner_skill
            if owner_skill == "imprimatur":
                applicable = applicable or scribe in reached[identifier]
            if (target in reached[identifier]) != applicable:
                raise Refusal(
                    f"mandatory executable reachability is inexact: {identifier}: {target}"
                )
    runtimes = {
        f"plugins/{plugin}/AGENTS.md"
        for plugin in {
            _plugin(path) for path in skill_paths.values() if _plugin(path) is not None
        }
    }
    expected_base_ids: set[str] = set()
    for name, path in sorted(skill_paths.items()):
        plugin = _plugin(path)
        if plugin is None:
            raise Refusal(f"scenario skill has no plugin: {path}")
        runtime = f"plugins/{plugin}/AGENTS.md"
        promise = f"plugins/{plugin}/PROMISE_MACHINE.md"
        identifiers = {
            "agent-skills": f"agent-skills:skill:{name}",
            "repository": f"repository:skill:{name}",
            "standalone": f"standalone:{plugin}:skill:{name}",
        }
        expected_base_ids.update(identifiers.values())
        matching_ids = {
            identifier
            for identifier, root in roots.items()
            if root["base_scenario"] in identifiers.values()
        }
        selection = [
            edge
            for edge in topology["scenario_edges"]
            if edge["source"] == runtime and edge["target"] == path
        ]
        if (
            len(selection) != 1
            or selection[0]["condition"] is not None
            or set(selection[0]["active_scenarios"]) != matching_ids
        ):
            raise Refusal(f"scenario selection scope is incomplete: {path}")
        for route, base_identifier in identifiers.items():
            expected_node = {
                "agent-skills": router,
                "repository": "AGENTS.md",
                "standalone": runtime,
            }[route]
            route_ids = {
                identifier
                for identifier, root in roots.items()
                if root["base_scenario"] == base_identifier
            }
            if not route_ids or any(
                roots[identifier]["node"] != expected_node
                or roots[identifier]["route"] != route
                or roots[identifier]["selected_skill"] != name
                for identifier in route_ids
            ):
                raise Refusal(
                    f"scenario starts at the wrong host route: {base_identifier}"
                )
            for identifier in route_ids:
                required = {runtime, promise, path}
                forbidden = runtimes - {runtime}
                if route == "agent-skills":
                    required.update(
                        {
                            "AGENTS.md",
                            "SHOGGOTH.md",
                            "PROMISE_MACHINE.md",
                            router,
                            portable,
                        }
                    )
                elif route == "repository":
                    required.update(
                        {"AGENTS.md", "SHOGGOTH.md", "PROMISE_MACHINE.md", router}
                    )
                    forbidden.add(portable)
                else:
                    forbidden.update(
                        {
                            "AGENTS.md",
                            "SHOGGOTH.md",
                            "PROMISE_MACHINE.md",
                            router,
                            portable,
                        }
                    )
                missing = required - reached[identifier]
                leaked = forbidden & reached[identifier]
                if missing:
                    raise Refusal(
                        f"scenario omits required loader node: {identifier}: {min(missing)}"
                    )
                if leaked:
                    raise Refusal(
                        f"scenario crosses its route or selection: {identifier}: {min(leaked)}"
                    )
    covered_base_ids = {root["base_scenario"] for root in roots.values()}
    if covered_base_ids != expected_base_ids:
        raise Refusal("scenario roots omit the route/selection base product")

    for edge in topology["scenario_edges"]:
        witnesses = (
            set(edge["active_scenarios"])
            & observed[edge["source"]]
            & observed[edge["target"]]
        )
        if not witnesses:
            raise Refusal(f"scenario edge has no realizable witness: {edge['id']}")
    for identifier, root in roots.items():
        for condition in root["conditions"]:
            matches = [
                edge
                for edge in topology["scenario_edges"]
                if edge["condition"] == condition
                and identifier in edge["active_scenarios"]
                and edge["source"] in reached[identifier]
                and edge["target"] in reached[identifier]
            ]
            if not matches:
                raise Refusal(
                    f"scenario condition does not fire: {identifier}"
                )

    ariadne = skill_paths["ariadne"]
    ariadne_operations = {
        edge["condition"]
        for edge in topology["scenario_edges"]
        if edge["source"] == ariadne
        and edge["target"] in ARIADNE_OPERATION_CONDITIONS
    }
    for identifier, root in roots.items():
        count = len(set(root["conditions"]) & ariadne_operations)
        if count > 1 or (
            root["selected_skill"] == "ariadne" and count != 1
        ):
            raise Refusal(f"Ariadne scenario does not select one operation: {identifier}")

    kronos = skill_paths["kronos"]
    fiat = skill_paths["fiat"]
    versioning = "plugins/hexaemeron/skills/VERSIONING.md"
    kronos_ledger = "plugins/hexaemeron/skills/kronos/EVOLUTION.md"
    candidate_ledgers = {
        f"{prefix}/EVOLUTION.md"
        for prefix in FRONTIER_SKILLS
        if f"{prefix}/EVOLUTION.md" != kronos_ledger
    }
    kronos_base_ids = {
        root["base_scenario"]
        for root in roots.values()
        if root["selected_skill"] == "kronos"
    }
    kronos_scenario_ids = {
        identifier
        for identifier, root in roots.items()
        if root["selected_skill"] == "kronos"
    }
    ranking_evidence = _evidence(
        kronos,
        "Walk the whole scope and find every `EVOLUTION.md` beneath it",
    )
    host_ranking_edges = [
        edge
        for edge in topology["edges"]
        if edge["source"] == kronos and edge["target"] in candidate_ledgers
    ]
    if (
        len(candidate_ledgers) != 25
        or len(kronos_base_ids) != 3
        or len(kronos_scenario_ids) != 27
        or len(host_ranking_edges) != len(candidate_ledgers)
        or {edge["target"] for edge in host_ranking_edges} != candidate_ledgers
        or any(
            edge["kind"] != "frontier-gate"
            or edge["load_type"] != "agent-or-prompt"
            or edge["active_roots"] != ["*"]
            or edge["evidence"] != ranking_evidence
            for edge in host_ranking_edges
        )
    ):
        raise Refusal("Kronos host ranking scan is incomplete")
    scenario_ranking_edges = [
        edge
        for edge in topology["scenario_edges"]
        if edge["source"] == kronos and edge["target"] in candidate_ledgers
    ]
    if (
        len(scenario_ranking_edges) != len(candidate_ledgers)
        or {edge["target"] for edge in scenario_ranking_edges}
        != candidate_ledgers
        or any(
            edge["kind"] != "frontier-gate"
            or edge["load_type"] != "agent-or-prompt"
            or edge["condition"] is not None
            or set(edge["eligible_base_scenarios"]) != kronos_base_ids
            or set(edge["active_scenarios"]) != kronos_scenario_ids
            or edge["evidence"] != ranking_evidence
            for edge in scenario_ranking_edges
        )
    ):
        raise Refusal("Kronos scenario ranking scan is incomplete")
    for identifier in kronos_scenario_ids:
        if (
            reached[identifier] & candidate_ledgers != candidate_ledgers
            or versioning not in reached[identifier]
        ):
            raise Refusal(f"Kronos scenario omits ranking input: {identifier}")
    kronos_branches = [
        edge
        for edge in topology["scenario_edges"]
        if edge["source"] == kronos
        and edge["kind"] == "operation-branch"
        and edge["target"] in set(skill_paths.values())
    ]
    dispatch = next(edge for edge in kronos_branches if edge["target"] == fiat)
    for identifier, root in roots.items():
        fired = {
            edge["target"]
            for edge in kronos_branches
            if edge["condition"] in root["conditions"]
        }
        non_dispatch = fired - {fiat}
        selected_kronos = root["selected_skill"] == "kronos"
        if (
            len(non_dispatch) > 1
            or (non_dispatch and fiat not in fired)
            or (selected_kronos and (len(non_dispatch) != 1 or fiat not in fired))
        ):
            raise Refusal(f"Kronos scenario is not one dispatched target: {identifier}")
        if non_dispatch and dispatch["condition"] not in root["conditions"]:
            raise Refusal(f"Kronos scenario omits Fiat dispatch: {identifier}")


def _build_topology(documents: list[dict[str, Any]]) -> dict[str, Any]:
    document_paths = {item["path"] for item in documents}
    plugins = sorted(
        {
            _plugin(item["path"])
            for item in documents
            if item["document_class"] == "runtime_contract"
            and _plugin(item["path"]) is not None
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
        node = f"plugins/{plugin}/AGENTS.md"
        roots.append(
            {
                "id": f"standalone:{plugin}",
                "node": node,
                "mode": "unconditional",
                "evidence": _evidence(node, "## Promise Machine binding"),
            }
        )
    edges: list[dict[str, Any]] = []

    def add_edge(
        source: str,
        target: str,
        kind: str,
        reason: str,
        needle: str,
        *,
        evidence_path: str | None = None,
        active_roots: tuple[str, ...] = ("*",),
        load_type: str = "agent-or-prompt",
        runtime_path: str | None = None,
        runtime_needle: str | None = None,
    ) -> None:
        if source not in document_paths or target not in document_paths:
            raise Refusal("loader edge leaves the frozen corpus")
        if (runtime_path is None) != (runtime_needle is None):
            raise Refusal(f"incomplete loader runtime evidence: {source} -> {target}")
        if (load_type == "mandatory-executable") != (runtime_path is not None):
            raise Refusal(f"loader edge type disagrees with runtime: {source} -> {target}")
        if any(
            item["source"] == source and item["target"] == target for item in edges
        ):
            raise Refusal(f"duplicate loader edge: {source} -> {target}")
        edges.append(
            {
                "id": f"edge-{len(edges) + 1:03d}",
                "source": source,
                "target": target,
                "kind": kind,
                "load_type": load_type,
                "reason": reason,
                "active_roots": list(active_roots),
                "evidence": _evidence(evidence_path or source, needle),
                "runtime_evidence": (
                    _evidence(runtime_path, runtime_needle)
                    if runtime_path is not None and runtime_needle is not None
                    else None
                ),
            }
        )

    add_edge(
        "AGENTS.md",
        "SHOGGOTH.md",
        "unconditional",
        "the repository runtime loads the collective identity before routing",
        "[Shoggoth collective identity](SHOGGOTH.md)",
        active_roots=("repository", "agent-skills"),
    )
    if _same_repository_markdown_url(CONTRIBUTORS_CANONICAL_URL) != "CONTRIBUTORS.md":
        raise Refusal("canonical contributor URL did not resolve to the pinned path")
    add_edge(
        "SHOGGOTH.md",
        "CONTRIBUTORS.md",
        "credential-identity",
        "the identity contract conditionally resolves an existing credential to the canonical local roster",
        CONTRIBUTORS_CANONICAL_URL,
        active_roots=("repository", "agent-skills"),
    )
    add_edge(
        "AGENTS.md",
        "PROMISE_MACHINE.md",
        "unconditional",
        "the repository runtime requires the suite-wide law before selection",
        "[Promise Machine contract](PROMISE_MACHINE.md)",
        active_roots=("repository", "agent-skills"),
    )
    add_edge(
        "AGENTS.md",
        ".agents/skills/promise-machine/SKILL.md",
        "unconditional",
        "the repository runtime routes requests through the sole host-neutral entrypoint",
        "`.agents/skills/promise-machine/SKILL.md`",
        active_roots=("repository", "agent-skills"),
    )
    router = ".agents/skills/promise-machine/SKILL.md"
    add_edge(
        router,
        "AGENTS.md",
        "conditional",
        "the Agent Skills source-checkout path requires the root runtime before routing",
        "../../../AGENTS.md",
        active_roots=("repository",),
    )
    add_edge(
        router,
        "PROMISE_MACHINE.md",
        "conditional",
        "the Agent Skills source-checkout path loads the suite law",
        "../../../PROMISE_MACHINE.md",
        active_roots=("repository",),
    )
    portable = ".agents/skills/promise-machine/PORTABLE.md"
    add_edge(
        router,
        portable,
        "installed-route",
        "the isolated Agent Skills installation loads its dependency-closed runtime contract",
        "read `PORTABLE.md`",
        active_roots=("agent-skills",),
    )
    for target, needle in (
        ("SHOGGOTH.md", "runtime/SHOGGOTH.md"),
        ("PROMISE_MACHINE.md", "runtime/PROMISE_MACHINE.md"),
        ("AGENTS.md", "runtime/AGENTS.md"),
    ):
        add_edge(
            portable,
            target,
            "installed-route",
            "the installed contract maps a verified runtime copy to its pinned canonical source",
            needle,
            active_roots=("agent-skills",),
        )
    for plugin in plugins:
        runtime = f"plugins/{plugin}/AGENTS.md"
        add_edge(
            router,
            runtime,
            "conditional",
            "the router loads the runtime contract only when its selection row wins",
            f"../../../plugins/{plugin}/AGENTS.md",
            active_roots=("repository", "agent-skills"),
        )
        promise = f"plugins/{plugin}/PROMISE_MACHINE.md"
        add_edge(
            runtime,
            promise,
            "unconditional",
            "a standalone plugin runtime loads its generated suite-law copy",
            "[Promise Machine contract](PROMISE_MACHINE.md)",
        )
        skills = sorted(
            item["path"]
            for item in documents
            if item["document_class"] == "skill_contract"
            and _plugin(item["path"]) == plugin
        )
        for skill in skills:
            relative = (
                PurePosixPath(skill)
                .relative_to(PurePosixPath("plugins") / plugin)
                .as_posix()
            )
            add_edge(
                runtime,
                skill,
                "conditional",
                "the plugin selection table loads exactly the selected canonical skill",
                relative,
            )
    for path, metadata in sorted(_additional_metadata().items()):
        document_class = metadata["document_class"]
        if document_class in (
            "identity_contract",
            "identity_roster",
            "router_install_contract",
        ):
            continue
        source = metadata["source_path"]
        add_edge(
            source,
            path,
            metadata["edge_kind"],
            "the source-directed admission requires this Markdown load",
            metadata["source_needle"],
        )
    for prefix in FRONTIER_SKILLS:
        ledger = f"{prefix}/EVOLUTION.md"
        add_edge(
            ledger,
            "plugins/hexaemeron/skills/VERSIONING.md",
            "frontier-gate",
            "the admitted frontier ledger requires the shared versioning policy",
            "VERSIONING.md",
        )
    kronos_skill = "plugins/hexaemeron/skills/kronos/SKILL.md"
    for prefix in FRONTIER_SKILLS:
        ledger = f"{prefix}/EVOLUTION.md"
        if ledger == "plugins/hexaemeron/skills/kronos/EVOLUTION.md":
            continue
        add_edge(
            kronos_skill,
            ledger,
            "frontier-gate",
            "Kronos reads every governed non-Kronos frontier ledger before ranking",
            "Walk the whole scope and find every `EVOLUTION.md` beneath it",
        )
    references_by_owner: dict[str, list[str]] = {}
    for item in documents:
        if item["document_class"] == "markdown_reference":
            references_by_owner.setdefault(item["canonical_owner"], []).append(
                item["path"]
            )
    for owner, references in sorted(references_by_owner.items()):
        reachable = {owner}
        pending = set(references)
        while pending:
            progress = False
            for target in sorted(pending):
                link = _reference_link(owner, target, reachable)
                if link is None:
                    continue
                source, needle = link
                add_edge(
                    source,
                    target,
                    "conditional",
                    "the selected skill or an already linked reference directs this load",
                    needle,
                )
                reachable.add(target)
                pending.remove(target)
                progress = True
                break
            if not progress:
                raise Refusal(f"unproved reference loader edge: {sorted(pending)[0]}")
    reference_only: list[dict[str, Any]] = []
    for target, metadata in sorted(_structured_metadata().items()):
        if metadata["load_semantics"] == "reference-only":
            reference_only.append(
                {
                    "path": target,
                    "canonical_owner": metadata["canonical_owner"],
                    "reason": (
                        "the immutable schema is admitted as structured authority "
                        "but no mandatory default executable loads it"
                    ),
                    "source_evidence": _evidence(
                        metadata["source_path"], metadata["source_needle"]
                    ),
                }
            )
            continue
        runtime_path = metadata["runtime_path"]
        runtime_needle = metadata["runtime_needle"]
        if runtime_path is None or runtime_needle is None:
            raise Refusal(f"mandatory executable lacks runtime evidence: {target}")
        add_edge(
            metadata["canonical_owner"],
            target,
            "mandatory-executable",
            "the selected skill's mandatory default executable reads this frozen input",
            metadata["source_needle"],
            evidence_path=metadata["source_path"],
            load_type="mandatory-executable",
            runtime_path=runtime_path,
            runtime_needle=runtime_needle,
        )
    skill_paths: dict[str, str] = {}
    for item in documents:
        if item["document_class"] != "skill_contract":
            continue
        name = _skill_name(item["path"])
        if name in skill_paths:
            raise Refusal(f"duplicate scenario skill name: {name}")
        skill_paths[name] = item["path"]

    selectable_skills = {
        name: path for name, path in skill_paths.items() if path != router
    }
    scenario_roots: list[dict[str, Any]] = []
    skill_scenarios: dict[str, tuple[str, ...]] = {}
    plugin_scenarios: dict[str, list[str]] = {plugin: [] for plugin in plugins}
    route_scenarios: dict[str, list[str]] = {
        "repository": [],
        "agent-skills": [],
        "standalone": [],
    }
    for name, path in sorted(selectable_skills.items()):
        plugin = _plugin(path)
        if plugin is None or plugin not in plugin_scenarios:
            raise Refusal(f"scenario skill has no runtime contract: {path}")
        runtime = f"plugins/{plugin}/AGENTS.md"
        identifiers = (
            f"agent-skills:skill:{name}",
            f"repository:skill:{name}",
            f"standalone:{plugin}:skill:{name}",
        )
        skill_scenarios[name] = identifiers
        for route, identifier, node, evidence_path, needle in (
            (
                "agent-skills",
                identifiers[0],
                router,
                router,
                "Choose the runtime before routing.",
            ),
            (
                "repository",
                identifiers[1],
                "AGENTS.md",
                "AGENTS.md",
                "The safe loading path is short:",
            ),
            (
                "standalone",
                identifiers[2],
                runtime,
                runtime,
                "## Promise Machine binding",
            ),
        ):
            scenario_roots.append(
                {
                    "id": identifier,
                    "node": node,
                    "mode": "unconditional",
                    "base_scenario": identifier,
                    "route": route,
                    "selected_skill": name,
                    "conditions": [],
                    "evidence": _evidence(evidence_path, needle),
                }
            )
            route_scenarios[route].append(identifier)
            plugin_scenarios[plugin].append(identifier)
    scenario_roots.sort(key=lambda item: item["id"])
    base_scenario_ids = {item["id"] for item in scenario_roots}
    scenario_edges: list[dict[str, Any]] = []

    def add_scenario_edge(
        source: str,
        target: str,
        kind: str,
        reason: str,
        needle: str,
        *,
        evidence_path: str | None = None,
        active_scenarios: Iterable[str] = ("*",),
        conditioned: bool = True,
        condition_name: str | None = None,
        load_type: str = "agent-or-prompt",
        runtime_path: str | None = None,
        runtime_needle: str | None = None,
    ) -> None:
        if source not in document_paths or target not in document_paths:
            raise Refusal("scenario edge leaves the frozen corpus")
        if (runtime_path is None) != (runtime_needle is None):
            raise Refusal(f"incomplete scenario runtime evidence: {source} -> {target}")
        if (load_type == "mandatory-executable") != (runtime_path is not None):
            raise Refusal(f"scenario edge type disagrees with runtime: {source} -> {target}")
        scope = sorted(set(active_scenarios))
        if not scope or ("*" in scope and scope != ["*"]):
            raise Refusal("scenario edge has an invalid scope")
        if scope == ["*"]:
            scope = sorted(base_scenario_ids)
        if not set(scope) <= base_scenario_ids:
            raise Refusal("scenario edge names an unknown scenario")
        edge_id = f"scenario-edge-{len(scenario_edges) + 1:03d}"
        condition = None
        if conditioned:
            condition = condition_name or f"{kind}:{edge_id}:{target}"
        if any(
            item["source"] == source
            and item["target"] == target
            and item["condition"] == condition
            for item in scenario_edges
        ):
            raise Refusal(
                f"duplicate scenario edge: {source} -> {target}: {condition}"
            )
        scenario_edges.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "kind": kind,
                "load_type": load_type,
                "reason": reason,
                "condition": condition,
                "_base_scenarios": scope,
                "evidence": _evidence(evidence_path or source, needle),
                "runtime_evidence": (
                    _evidence(runtime_path, runtime_needle)
                    if runtime_path is not None and runtime_needle is not None
                    else None
                ),
            }
        )

    checkout_scenarios = (
        *route_scenarios["repository"],
        *route_scenarios["agent-skills"],
    )
    for source, target, kind, needle in (
        ("AGENTS.md", "SHOGGOTH.md", "unconditional", "SHOGGOTH.md"),
        ("SHOGGOTH.md", "CONTRIBUTORS.md", "credential-identity", "CONTRIBUTORS.md"),
        ("AGENTS.md", "PROMISE_MACHINE.md", "unconditional", "PROMISE_MACHINE.md"),
        ("AGENTS.md", router, "unconditional", router),
    ):
        add_scenario_edge(
            source,
            target,
            kind,
            "the shared scenario follows the source-directed load",
            needle,
            active_scenarios=checkout_scenarios,
            conditioned=kind == "credential-identity",
            condition_name=(
                "credential:github-contributor"
                if kind == "credential-identity"
                else None
            ),
        )
    add_scenario_edge(
        router,
        portable,
        "installed-route",
        "the isolated Agent Skills scenario loads its dependency-closed runtime contract",
        "PORTABLE.md",
        active_scenarios=route_scenarios["agent-skills"],
        conditioned=False,
    )
    for target, needle in (
        ("SHOGGOTH.md", "runtime/SHOGGOTH.md"),
        ("PROMISE_MACHINE.md", "runtime/PROMISE_MACHINE.md"),
        ("AGENTS.md", "runtime/AGENTS.md"),
    ):
        add_scenario_edge(
            portable,
            target,
            "installed-route",
            "the installed scenario maps a verified runtime copy to its pinned canonical source",
            needle,
            active_scenarios=route_scenarios["agent-skills"],
            conditioned=False,
        )
    for plugin in plugins:
        runtime = f"plugins/{plugin}/AGENTS.md"
        routed_scenarios = [
            identifier
            for identifier in plugin_scenarios[plugin]
            if not identifier.startswith("standalone:")
        ]
        add_scenario_edge(
            router,
            runtime,
            "conditional",
            "the route loads only the runtime contract for the selected skill",
            f"../../../plugins/{plugin}/AGENTS.md",
            active_scenarios=routed_scenarios,
            conditioned=False,
        )
        add_scenario_edge(
            runtime,
            f"plugins/{plugin}/PROMISE_MACHINE.md",
            "unconditional",
            "the plugin scenario loads its suite-law copy",
            "PROMISE_MACHINE.md",
            active_scenarios=plugin_scenarios[plugin],
            conditioned=False,
        )
    for name, path in sorted(selectable_skills.items()):
        plugin = _plugin(path)
        assert plugin is not None
        runtime = f"plugins/{plugin}/AGENTS.md"
        relative = (
            PurePosixPath(path)
            .relative_to(PurePosixPath("plugins") / plugin)
            .as_posix()
        )
        add_scenario_edge(
            runtime,
            path,
            "conditional",
            "the runtime loads exactly the selected canonical skill",
            relative,
            active_scenarios=skill_scenarios[name],
            conditioned=False,
        )
    owned_targets: dict[str, list[tuple[str, dict[str, str]]]] = {}
    for target, metadata in sorted(_additional_metadata().items()):
        if metadata["document_class"] in (
            "identity_contract",
            "identity_roster",
            "router_install_contract",
        ):
            continue
        owned_targets.setdefault(metadata["canonical_owner"], []).append(
            (target, metadata)
        )
    for owner, targets in sorted(owned_targets.items()):
        for target, metadata in targets:
            source = metadata["source_path"]
            if source != owner and source not in document_paths:
                raise Refusal(f"admission anchor leaves corpus: {source}")
            add_scenario_edge(
                source,
                target,
                metadata["edge_kind"],
                "the selected workflow follows its admitted source directive",
                metadata["source_needle"],
                condition_name=ARIADNE_OPERATION_CONDITIONS.get(target),
            )
    for ledger in (f"{prefix}/EVOLUTION.md" for prefix in FRONTIER_SKILLS):
        add_scenario_edge(
            ledger,
            "plugins/hexaemeron/skills/VERSIONING.md",
            "frontier-gate",
            "the frontier ledger requires the shared versioning policy",
            "VERSIONING.md",
            conditioned=False,
        )
    for owner, references in sorted(references_by_owner.items()):
        reachable = {owner}
        pending = set(references)
        while pending:
            for target in sorted(pending):
                link = _reference_link(owner, target, reachable)
                if link is None:
                    continue
                source, needle = link
                add_scenario_edge(
                    source,
                    target,
                    "conditional",
                    "the selected skill recursively follows a required reference",
                    needle,
                )
                reachable.add(target)
                pending.remove(target)
                break
            else:
                raise Refusal(
                    f"unproved scenario reference edge: {sorted(pending)[0]}"
                )

    for target, metadata in sorted(_structured_metadata().items()):
        if metadata["load_semantics"] == "reference-only":
            continue
        runtime_path = metadata["runtime_path"]
        runtime_needle = metadata["runtime_needle"]
        if runtime_path is None or runtime_needle is None:
            raise Refusal(f"mandatory executable lacks runtime evidence: {target}")
        conditions: tuple[str | None, ...] = (
            SYNKRISIS_RULE_OPERATIONS
            if target == "plugins/synkrisis/references/rules-v1.json"
            else (None,)
        )
        owner_skill = _skill_name(metadata["canonical_owner"])
        invocation_bases = set(skill_scenarios[owner_skill])
        if owner_skill == "imprimatur":
            invocation_bases.update(skill_scenarios["fiat"])
        for condition in conditions:
            scenario_runtime_needle = (
                SYNKRISIS_RULE_RUNTIME_NEEDLES[condition]
                if condition is not None
                else runtime_needle
            )
            scenario_source_needle = (
                SYNKRISIS_RULE_SOURCE_NEEDLES[condition]
                if condition is not None
                else metadata["source_needle"]
            )
            add_scenario_edge(
                metadata["canonical_owner"],
                target,
                "mandatory-executable",
                "the applicable operation's mandatory executable reads this frozen input",
                scenario_source_needle,
                evidence_path=metadata["source_path"],
                active_scenarios=invocation_bases,
                conditioned=condition is not None,
                condition_name=condition,
                load_type="mandatory-executable",
                runtime_path=runtime_path,
                runtime_needle=scenario_runtime_needle,
            )

    fiat = "plugins/hexaemeron/skills/fiat/SKILL.md"
    for name in ("protasis", "phylax", "ephoros", "metron", "elenchus", "hypomnema"):
        add_scenario_edge(
            fiat,
            skill_paths[name],
            "operation-branch",
            "Fiat delegates the named phase content contract",
            f"[{name}]",
        )
    for name in ("x-ray", "solidity-auditor", "fizz"):
        add_scenario_edge(
            fiat,
            skill_paths[name],
            "operation-branch",
            "Fiat conditionally loads the vendored security suite",
            f"`{name}`",
        )
    fizz = skill_paths["fizz"]
    add_scenario_edge(
        fizz,
        skill_paths["x-ray"],
        "operation-branch",
        "Fizz requires X-Ray before its analyzer fallback",
        "x-ray Acquisition Protocol",
    )
    kronos = skill_paths["kronos"]
    for prefix in FRONTIER_SKILLS:
        ledger = f"{prefix}/EVOLUTION.md"
        if ledger == "plugins/hexaemeron/skills/kronos/EVOLUTION.md":
            continue
        add_scenario_edge(
            kronos,
            ledger,
            "frontier-gate",
            "Kronos reads every governed non-Kronos frontier ledger before ranking",
            "Walk the whole scope and find every `EVOLUTION.md` beneath it",
            active_scenarios=skill_scenarios["kronos"],
            conditioned=False,
        )
    add_scenario_edge(
        kronos,
        fiat,
        "operation-branch",
        "Kronos dispatches an accepted selection through Fiat",
        "dispatches that exact job to Fiat",
        condition_name="nested-selection:kronos:dispatch-fiat",
    )
    for prefix in FRONTIER_SKILLS:
        target = f"{prefix}/SKILL.md"
        if target in (kronos, fiat):
            continue
        add_scenario_edge(
            kronos,
            target,
            "operation-branch",
            "Kronos reads the dynamically selected first-party skill",
            "Read the selected skill's canonical instructions",
            condition_name=f"nested-selection:kronos:target:{_skill_name(target)}",
        )
    scribe = "plugins/hexaemeron/agents/scribe.md"
    for name, needle in (("imprimatur", "imprimatur.py"), ("vulgate", "vulgate/SKILL.md")):
        add_scenario_edge(
            scribe,
            skill_paths[name],
            "operation-branch",
            "the prose worker loads its required mask",
            needle,
            conditioned=False,
        )
    warden = "plugins/hexaemeron/agents/warden.md"
    for name, needle in (
        ("x-ray", "x-ray/SKILL.md"),
        ("solidity-auditor", "solidity-auditor/SKILL.md"),
        ("fizz", "fizz/SKILL.md"),
        ("sapheneia", "sapheneia:sapheneia"),
    ):
        add_scenario_edge(
            warden,
            skill_paths[name],
            "operation-branch",
            "the audit worker follows its required review or filter contract",
            needle,
        )

    base_roots = list(scenario_roots)
    route_order = {"repository": 0, "agent-skills": 1, "standalone": 2}
    document_owner = {
        item["path"]: item["canonical_owner"] for item in documents
    }
    paths_by_base: dict[str, dict[str, list[dict[str, Any]]]] = {}
    for root in base_roots:
        adjacency: dict[str, list[dict[str, Any]]] = {}
        for edge in scenario_edges:
            if root["id"] in edge["_base_scenarios"]:
                adjacency.setdefault(edge["source"], []).append(edge)
        for rows in adjacency.values():
            rows.sort(key=lambda item: item["id"])
        paths: dict[str, list[dict[str, Any]]] = {root["node"]: []}
        pending = [root["node"]]
        cursor = 0
        while cursor < len(pending):
            node = pending[cursor]
            cursor += 1
            for edge in adjacency.get(node, []):
                if edge["target"] in paths:
                    continue
                paths[edge["target"]] = [*paths[node], edge]
                pending.append(edge["target"])
        paths_by_base[root["id"]] = paths

    kronos_dispatch = next(
        edge
        for edge in scenario_edges
        if edge["source"] == kronos and edge["target"] == fiat
    )
    kronos_target_conditions = {
        edge["condition"]
        for edge in scenario_edges
        if edge["source"] == kronos
        and edge["target"] in set(skill_paths.values()) - {fiat}
    }
    vectors_by_base: dict[str, set[tuple[str, ...]]] = {
        root["id"]: set() for root in base_roots
    }
    for edge in scenario_edges:
        condition = edge["condition"]
        if condition is None:
            continue
        candidates: list[
            tuple[tuple[int, int, int, int, str], dict[str, Any], list[dict[str, Any]]]
        ] = []
        desired_owner = document_owner.get(edge["target"], edge["source"])
        for root in base_roots:
            if root["id"] not in edge["_base_scenarios"]:
                continue
            path = paths_by_base[root["id"]].get(edge["source"])
            if path is None:
                continue
            path_conditions = {
                row["condition"] for row in path if row["condition"] is not None
            }
            selected_path = selectable_skills[root["selected_skill"]]
            priority = (
                selected_path != desired_owner,
                len(path_conditions),
                route_order[root["route"]],
                len(path),
                root["id"],
            )
            candidates.append((priority, root, path))
        if not candidates:
            raise Refusal(f"conditional scenario edge is unreachable: {edge['id']}")
        _, root, path = min(candidates, key=lambda item: item[0])
        vector = {
            row["condition"] for row in path if row["condition"] is not None
        }
        vector.add(condition)
        if vector & kronos_target_conditions:
            dispatch_condition = kronos_dispatch["condition"]
            if dispatch_condition is None:
                raise Refusal("Kronos dispatch edge is not conditional")
            vector.add(dispatch_condition)
        vectors_by_base[root["id"]].add(tuple(sorted(vector)))

    ariadne_skill = skill_paths["ariadne"]
    ariadne_operation_conditions = {
        edge["condition"]
        for edge in scenario_edges
        if edge["source"] == ariadne_skill
        and edge["target"]
        in {
            path
            for path, owner, _, _ in OPERATION_REFERENCES
            if owner == ariadne_skill
        }
    }
    canonical_ariadne_condition = min(ariadne_operation_conditions)
    canonical_kronos_target = min(kronos_target_conditions)
    dispatch_condition = kronos_dispatch["condition"]
    if dispatch_condition is None:
        raise Refusal("Kronos dispatch edge is not conditional")
    for root in base_roots:
        vectors = vectors_by_base[root["id"]]
        if root["selected_skill"] == "ariadne":
            normalised = set()
            for vector in vectors | {()}:
                conditions = set(vector)
                if not conditions & ariadne_operation_conditions:
                    conditions.add(canonical_ariadne_condition)
                normalised.add(tuple(sorted(conditions)))
            vectors_by_base[root["id"]] = normalised
        elif root["selected_skill"] == "kronos":
            normalised = set()
            for vector in vectors | {()}:
                conditions = set(vector)
                conditions.add(dispatch_condition)
                if not conditions & kronos_target_conditions:
                    conditions.add(canonical_kronos_target)
                normalised.add(tuple(sorted(conditions)))
            vectors_by_base[root["id"]] = normalised

    roots_by_id = {root["id"]: root for root in base_roots}
    scenario_roots = [
        root
        for root in base_roots
        if root["selected_skill"] not in {"ariadne", "kronos"}
    ]
    for base_identifier in sorted(vectors_by_base):
        base = roots_by_id[base_identifier]
        for index, conditions in enumerate(
            sorted(vectors_by_base[base_identifier]), start=1
        ):
            identifier = f"{base_identifier}:conditions:{index:03d}"
            scenario_roots.append(
                {
                    "id": identifier,
                    "node": base["node"],
                    "mode": "conditional",
                    "base_scenario": base_identifier,
                    "route": base["route"],
                    "selected_skill": base["selected_skill"],
                    "conditions": list(conditions),
                    "evidence": base["evidence"],
                }
            )
    scenario_roots.sort(key=lambda item: item["id"])
    for edge in scenario_edges:
        base_scope = sorted(set(edge.pop("_base_scenarios")))
        edge["eligible_base_scenarios"] = base_scope
        base_scope_set = set(base_scope)
        condition = edge["condition"]
        edge["active_scenarios"] = sorted(
            root["id"]
            for root in scenario_roots
            if root["base_scenario"] in base_scope_set
            and (condition is None or condition in root["conditions"])
        )
        if not edge["active_scenarios"]:
            raise Refusal(f"scenario edge has no declared invocation: {edge['id']}")
    topology = {
        "roots": roots,
        "edges": edges,
        "scenario_roots": scenario_roots,
        "scenario_edges": scenario_edges,
        "reference_only": reference_only,
    }
    _validate_complete_scenarios(topology, selectable_skills)
    return topology


def build_loader_graph(manifest: dict[str, Any]) -> dict[str, Any]:
    manifest_digest = _artifact_digest(manifest)
    documents = manifest["documents"]
    topology = _build_topology(documents)
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
    if reference_only_paths != {
        path
        for path, metadata in _structured_metadata().items()
        if metadata["load_semantics"] == "reference-only"
    }:
        raise Refusal("reference-only graph ledger is incomplete")
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
        expected_scenarios = (
            2 if path == "plugins/synkrisis/references/rules-v1.json" else 1
        )
        if len(host_edges) != 1 or len(scenario_edges) != expected_scenarios:
            raise Refusal(f"mandatory executable graph is incomplete: {path}")
        for edge in host_edges:
            if (
                edge["source"] != metadata["canonical_owner"]
                or edge["kind"] != "mandatory-executable"
                or edge["load_type"] != "mandatory-executable"
                or edge["evidence"] != document["source_evidence"]
                or edge["runtime_evidence"] != document["runtime_evidence"]
            ):
                raise Refusal(f"mandatory executable evidence drift: {path}")
        for edge in scenario_edges:
            expected_runtime = document["runtime_evidence"]
            expected_source = document["source_evidence"]
            if path == "plugins/synkrisis/references/rules-v1.json":
                condition = edge["condition"]
                if condition not in SYNKRISIS_RULE_RUNTIME_NEEDLES:
                    raise Refusal("Synkrisis scenario lacks operation runtime proof")
                expected_runtime = _evidence(
                    metadata["runtime_path"],
                    SYNKRISIS_RULE_RUNTIME_NEEDLES[condition],
                )
                expected_source = _evidence(
                    metadata["source_path"],
                    SYNKRISIS_RULE_SOURCE_NEEDLES[condition],
                )
            if (
                edge["source"] != metadata["canonical_owner"]
                or edge["kind"] != "mandatory-executable"
                or edge["load_type"] != "mandatory-executable"
                or edge["evidence"] != expected_source
                or edge["runtime_evidence"] != expected_runtime
            ):
                raise Refusal(f"mandatory scenario evidence drift: {path}")
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
        },
    }


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

    def fence_marker(line: bytes) -> tuple[bytes, bytes] | None:
        match = re.match(rb"^ {0,3}(`{3,}|~{3,})([^\r\n]*)", line)
        return None if match is None else (match.group(1), match.group(2))

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

    @lru_cache(maxsize=None)
    def commonmark_suffix_is_balanced(start: int) -> bool:
        active: tuple[int, int] | None = None
        for line in lines[start:]:
            marker = fence_marker(line)
            if marker is None:
                continue
            if active is not None:
                if closes(marker, active):
                    active = None
            elif opens(marker):
                fence, _ = marker
                active = (fence[0], len(fence))
        return active is None

    ranges: list[tuple[int, int, str]] = []
    offset = 0
    active_fence: tuple[int, int] | None = None
    pending_template: tuple[int, int] | None = None
    for index, line in enumerate(lines):
        marker = fence_marker(line)
        classification = "governed_operative_semantics"
        if active_fence is not None:
            classification = "exact_literal_or_evidence"
            if marker is not None:
                fence, remainder = marker
                if closes(marker, active_fence):
                    if (
                        pending_template is not None
                        and closes(marker, pending_template)
                        and not commonmark_suffix_is_balanced(index + 1)
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
                active_fence = (fence[0], len(fence))
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
            exact_literal=document["document_class"] == "structured_reference",
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
    manifest: dict[str, Any], cohorts: dict[str, Any]
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
        "selection_seed": SELECTION_SEED,
        "membership": membership,
        "membership_sha256": _sha256(_canonical_json(membership)),
        "closed_future_case_envelope": envelope,
        "case_envelope_sha256": _sha256(_canonical_json(envelope)),
        "opened": False,
    }
    return {**body, "commitment_sha256": _sha256(_canonical_json(body))}


def _validate_manifest_shape(manifest: dict[str, Any]) -> None:
    _require_fields(
        manifest,
        ("schema", "source", "counts", "totals", "documents"),
        ("schema", "source", "counts", "totals", "documents"),
        "manifest",
    )
    if manifest["schema"] != f"{SCHEMA_PREFIX}-corpus-manifest/v1":
        raise Refusal("unsupported manifest schema")
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


def _validate_partition_closure(partition: dict[str, Any]) -> None:
    for file_record in partition["files"]:
        cursor = 0
        data = _source_blob(file_record["path"])
        for item in file_record["ranges"]:
            if set(item) != {"start", "end", "classification", "span_sha256"}:
                raise Refusal("partition range has a non-closed field set")
            if item["start"] != cursor or item["end"] <= item["start"]:
                raise Refusal("partition ranges overlap, gap, or are unordered")
            if item["classification"] not in PARTITION_CLASSES:
                raise Refusal("partition range has an unknown class")
            if _sha256(data[item["start"] : item["end"]]) != item["span_sha256"]:
                raise Refusal("partition span digest mismatch")
            cursor = item["end"]
        if cursor != len(data) or cursor != file_record["bytes"]:
            raise Refusal("partition does not close over its source")


def _verify_exact(
    path: Path, expected: dict[str, Any], label: str
) -> tuple[dict[str, Any], bytes]:
    actual, raw = _load_record(path)
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
    expected = build_manifest()
    manifest, raw = _verify_exact(args.manifest, expected, "corpus manifest")
    _validate_manifest_shape(manifest)
    return _result("verify-corpus", raw, manifest["totals"])


def verify_loader(args: argparse.Namespace) -> bytes:
    manifest, _ = _load_record(args.manifest)
    _validate_manifest_shape(manifest)
    if manifest != build_manifest():
        raise Refusal("loader manifest is stale")
    expected = build_loader_graph(manifest)
    graph, raw = _verify_exact(args.graph, expected, "loader graph")
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


def verify_partition(args: argparse.Namespace) -> bytes:
    manifest, _ = _load_record(args.manifest)
    _validate_manifest_shape(manifest)
    if manifest != build_manifest():
        raise Refusal("partition manifest is stale")
    expected = build_partition(manifest)
    partition, raw = _verify_exact(args.partition, expected, "byte partition")
    _validate_partition_closure(partition)
    if partition["unsupported_operative_bytes"] != 0:
        raise Refusal("unsupported operative bytes block selection")
    return _result("verify-partition", raw, partition["totals"])


def verify_seal(args: argparse.Namespace) -> bytes:
    manifest, _ = _load_record(args.manifest)
    _validate_manifest_shape(manifest)
    if manifest != build_manifest():
        raise Refusal("seal manifest is stale")
    expected_cohorts = build_cohorts(manifest)
    cohorts, _ = _verify_exact(args.cohorts, expected_cohorts, "cohorts")
    expected_seal = build_holdout_seal(manifest, cohorts)
    seal, raw = _verify_exact(args.seal, expected_seal, "holdout seal")
    body = dict(seal)
    commitment = body.pop("commitment_sha256")
    if _sha256(_canonical_json(body)) != commitment or seal["opened"] is not False:
        raise Refusal("holdout commitment is open or inconsistent")
    forbidden = set(seal["closed_future_case_envelope"]["forbidden_until_open"])
    for slot in seal["closed_future_case_envelope"]["slots"]:
        if forbidden & set(slot):
            raise Refusal("sealed slot contains answer-bearing material")
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
    parent, name = _open_parent(relative, create=False, label="output")
    flags = os.O_RDONLY | os.O_NOFOLLOW
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
        try:
            named_stage = os.open(temporary, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
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
            published = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        except OSError as exc:
            raise Refusal("published output is unavailable or unsafe") from exc
        try:
            reread, published_stat = _read_descriptor(
                published, max(MAX_JSON_BYTES, len(data))
            )
        finally:
            os.close(published)
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

the {len(_additional_metadata())} paths below close the imperative and conditional agent-load directives
that the original issue census omitted. each row binds the admitted class,
condition, exact source bytes and source anchor at the frozen ref.

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
reference-only records. the scenarios cover the exact 93
base combinations of 31 selectable canonical skills and the repository,
isolated Agent Skills and standalone-plugin host routes. 87 bases admit a
zero-condition invocation; Ariadne and Kronos instead require an operation or
target-plus-Fiat vector on all three routes. Synkrisis adds exclusive
`diagnose` and `verify` vectors. conditional roots carry one closed,
sorted invocation vector. each starts at its real host entry, loads
only the selected plugin runtime and skill, and includes only descendants whose
conditions fire. no scenario edge uses a wildcard, every potential edge has a
realizable witness, and sibling Kronos targets or Ariadne operations do not
co-occur. every edge cites a source path, exact byte range,
source digest and span digest. unconditional runtime loads, installed routes,
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

`holdout-seal.json` commits the selection method, seed, membership and 16-slot
case envelope. it contains no prompt, expected answer, scorer key or model
output. later work may open that envelope once; Step 1 does not score it.

## refusal boundary

all four verification commands rebuild from the fixed Git ref and compare the
live source bytes before accepting an artefact. Git runs by one absolute
system-owned executable with lazy fetch, global and system configuration,
prompts and ambient environment disabled. a path, byte, digest, loader span,
partition range, cohort member or commitment that drifts refuses with the
failed predicate. paths are canonical printable-ASCII POSIX relatives no longer
than 1,024 bytes; aliases, traversal, empty segments, backslashes, controls and
non-ASCII input refuse in both runtime and schema. current prompt and
scenario-reachable denominators remain
unmeasured until the later arm and case builders exist.
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
    if reconciliation is not None:
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
    manifest = build_manifest()
    graph = build_loader_graph(manifest)
    partition = build_partition(manifest)
    cohorts = build_cohorts(manifest)
    seal = build_holdout_seal(manifest, cohorts)
    records = dict(
        zip(
            BASELINE_RECORD_NAMES,
            (manifest, graph, partition, cohorts, seal),
            strict=True,
        )
    )
    digests: dict[str, dict[str, Any]] = {}
    for name, value in records.items():
        data = _canonical_json(value)
        _atomic_write(output / name, data)
        digests[name] = {"bytes": len(data), "sha256": _sha256(data)}
    inventory = {
        "schema": f"{SCHEMA_PREFIX}-artifact-inventory/v1",
        "source_ref": SOURCE_REF,
        "source_tree_sha256": manifest["source"]["tree_sha256"],
        "artifacts": digests,
    }
    _atomic_write(output / "artifact-inventory.json", _canonical_json(inventory))
    if reconciliation is not None:
        _atomic_write(
            reconciliation,
            _reconciliation_markdown(manifest, graph, partition, cohorts),
        )
    return _result(
        "build-baseline",
        _canonical_json(inventory),
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
    corpus.set_defaults(handler=verify_corpus)

    loader = subparsers.add_parser("verify-loader")
    loader.add_argument("--manifest", type=_path, required=True)
    loader.add_argument("--graph", type=_path, required=True)
    loader.set_defaults(handler=verify_loader)

    partition = subparsers.add_parser("verify-partition")
    partition.add_argument("--manifest", type=_path, required=True)
    partition.add_argument("--partition", type=_path, required=True)
    partition.set_defaults(handler=verify_partition)

    seal = subparsers.add_parser("verify-seal")
    seal.add_argument("--manifest", type=_path, required=True)
    seal.add_argument("--cohorts", type=_path, required=True)
    seal.add_argument("--seal", type=_path, required=True)
    seal.set_defaults(handler=verify_seal)
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
