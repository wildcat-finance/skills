#!/usr/bin/env python3
"""Validate and evaluate the labelled-prose-v1 fixture."""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))
from imprimatur import build  # noqa: E402

SEED = "imprimatur-labelled-prose-v1"
HUMAN_CUTOFF = datetime(2025, 8, 1, tzinfo=timezone.utc)
TIERS = ("hard", "gated", "structural")
ORIGINS = ("human", "model_assisted")
GENRES = ("technical_documentation", "delivery_incident_report", "github_change_description")
DECISIONS = {"actionable", "licensed", "signal_only"}
SEVERITIES = {"critical", "high", "medium", "low"}
MODEL_MARKERS = (
    "wildcat-origin: shoggoth",
    "co-authored-by: shoggoth",
    "co-authored-by: claude opus 5",
    "co-authored-by: claude",
)


class EvaluationError(ValueError):
    pass


def sha256_bytes(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def read_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise EvaluationError(f"cannot read {path}: {exc}") from exc


def read_jsonl(path: Path) -> list[dict]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise EvaluationError(f"cannot read {path}: {exc}") from exc
    rows = []
    for number, line in enumerate(lines, 1):
        if not line.strip():
            raise EvaluationError(f"blank JSONL row at {path}:{number}")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise EvaluationError(f"invalid JSON at {path}:{number}: {exc}") from exc
        if not isinstance(value, dict):
            raise EvaluationError(f"row at {path}:{number} is not an object")
        rows.append(value)
    return rows


def canonical_json(value) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n"


def validate_schema(value, schema: dict, context: str) -> None:
    """Validate the JSON Schema subset used by this frozen fixture."""
    allowed_types = schema.get("type")
    if allowed_types is not None:
        if not isinstance(allowed_types, list):
            allowed_types = [allowed_types]
        predicates = {
            "object": lambda item: isinstance(item, dict),
            "array": lambda item: isinstance(item, list),
            "string": lambda item: isinstance(item, str),
            "integer": lambda item: isinstance(item, int) and not isinstance(item, bool),
            "number": lambda item: isinstance(item, (int, float)) and not isinstance(item, bool),
            "null": lambda item: item is None,
        }
        if not any(predicates[name](value) for name in allowed_types):
            raise EvaluationError(f"schema type mismatch at {context}: expected {allowed_types}")
    if "const" in schema and value != schema["const"]:
        raise EvaluationError(f"schema const mismatch at {context}")
    if "enum" in schema and value not in schema["enum"]:
        raise EvaluationError(f"schema enum mismatch at {context}: {value!r}")
    if isinstance(value, dict):
        required = set(schema.get("required", []))
        missing = required - set(value)
        if missing:
            raise EvaluationError(f"schema missing keys at {context}: {sorted(missing)}")
        properties = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            extra = set(value) - set(properties)
            if extra:
                raise EvaluationError(f"schema extra keys at {context}: {sorted(extra)}")
        if len(value) < schema.get("minProperties", 0):
            raise EvaluationError(f"schema too few properties at {context}")
        for key, item in value.items():
            if key in properties:
                validate_schema(item, properties[key], f"{context}/{key}")
    elif isinstance(value, list):
        if len(value) < schema.get("minItems", 0) or len(value) > schema.get("maxItems", len(value)):
            raise EvaluationError(f"schema array length mismatch at {context}")
        if schema.get("uniqueItems"):
            rendered = [json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value]
            if len(rendered) != len(set(rendered)):
                raise EvaluationError(f"schema duplicate array item at {context}")
        if "items" in schema:
            for index, item in enumerate(value):
                validate_schema(item, schema["items"], f"{context}/{index}")
    elif isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            raise EvaluationError(f"schema string too short at {context}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            raise EvaluationError(f"schema pattern mismatch at {context}: {value!r}")
        if schema.get("format") == "date-time":
            parse_timestamp(value)
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            raise EvaluationError(f"schema number below minimum at {context}")
        if "maximum" in schema and value > schema["maximum"]:
            raise EvaluationError(f"schema number above maximum at {context}")
        if "exclusiveMaximum" in schema and value >= schema["exclusiveMaximum"]:
            raise EvaluationError(f"schema number above exclusive maximum at {context}")


def verify_fixture_hashes(fixture: Path) -> None:
    """Bind the evaluated rows and schemas to both published digest seals."""
    seal = read_json(fixture / "annotation-seal.json")
    freeze = read_json(fixture / "candidate-freeze.json")
    direct = {
        "samples.jsonl": seal["samples_sha256"],
        "split.json": seal["split_sha256"],
        "blind-id-map.json": seal["hidden_id_map_sha256"],
    }
    for name, expected in direct.items():
        if sha256_bytes((fixture / name).read_bytes()) != expected:
            raise EvaluationError(f"annotation seal mismatch for {name}")
    for name, expected in seal["schema_sha256"].items():
        if sha256_bytes((fixture / "schemas" / name).read_bytes()) != expected:
            raise EvaluationError(f"annotation seal mismatch for schema {name}")
    for name, expected in freeze["fixture_hashes"].items():
        path = fixture / name
        if name == "annotation-packet.jsonl":
            if expected != seal["packet_sha256"]:
                raise EvaluationError("packet digest differs between published seals")
            continue
        if sha256_bytes(path.read_bytes()) != expected:
            raise EvaluationError(f"candidate freeze mismatch for {name}")
    for name, expected in freeze["schema_hashes"].items():
        if sha256_bytes((fixture / "schemas" / name).read_bytes()) != expected:
            raise EvaluationError(f"candidate freeze mismatch for schema {name}")
    if freeze["candidate_hashes"] != file_hashes():
        raise EvaluationError("candidate code or lexicon digest differs from freeze")


def normalized_text(text: str) -> str:
    text = unicodedata.normalize("NFKC", text).lower()
    text = re.sub(r"!\[([^]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[`*_>#~|]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def fivegrams(text: str) -> set[tuple[str, ...]]:
    words = re.findall(r"[a-z0-9]+(?:['-][a-z0-9]+)*", normalized_text(text))
    return {tuple(words[i:i + 5]) for i in range(max(0, len(words) - 4))}


def jaccard(left: str, right: str) -> float:
    a, b = fivegrams(left), fivegrams(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def ratio(numerator: int, denominator: int):
    return None if denominator == 0 else round(numerator / denominator, 6)


def f1(precision, recall):
    if precision is None or recall is None or precision + recall == 0:
        return None
    return round(2 * precision * recall / (precision + recall), 6)


def parse_timestamp(value: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (ValueError, AttributeError) as exc:
        raise EvaluationError(f"invalid timestamp {value!r}") from exc


def validate_annotation(text: str, label: dict, families: dict, context: str) -> None:
    required = {"tier", "family", "start_byte", "end_byte", "decision", "severity", "reason"}
    optional = {"evidence_start_byte", "evidence_end_byte"}
    if not required <= set(label) or not set(label) <= required | optional:
        raise EvaluationError(f"invalid annotation keys at {context}: {sorted(label)}")
    tier = label["tier"]
    if tier not in TIERS or label["family"] not in families[tier]:
        raise EvaluationError(f"invalid tier/family at {context}: {tier}/{label['family']}")
    if label["decision"] not in DECISIONS or label["severity"] not in SEVERITIES:
        raise EvaluationError(f"invalid decision/severity at {context}")
    if not isinstance(label["reason"], str) or not label["reason"].strip():
        raise EvaluationError(f"empty annotation reason at {context}")
    raw = text.encode("utf-8")
    start, end = label["start_byte"], label["end_byte"]
    if not isinstance(start, int) or not isinstance(end, int) or not (0 <= start < end <= len(raw)):
        raise EvaluationError(f"invalid byte range at {context}: {start}:{end}/{len(raw)}")
    try:
        raw[start:end].decode("utf-8")
    except UnicodeDecodeError as exc:
        raise EvaluationError(f"range splits UTF-8 codepoint at {context}") from exc
    has_evidence = "evidence_start_byte" in label or "evidence_end_byte" in label
    if has_evidence:
        es, ee = label.get("evidence_start_byte"), label.get("evidence_end_byte")
        if es is not None or ee is not None:
            if not isinstance(es, int) or not isinstance(ee, int) or not (0 <= es < ee <= len(raw)):
                raise EvaluationError(f"invalid evidence range at {context}")
            try:
                raw[es:ee].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise EvaluationError(f"evidence range splits UTF-8 at {context}") from exc


def load_fixture(fixture: Path) -> dict:
    samples = read_jsonl(fixture / "samples.jsonl")
    split = read_json(fixture / "split.json")
    labels = read_jsonl(fixture / "labels.jsonl")
    raw_a = read_jsonl(fixture / "raw-label-a.jsonl")
    raw_b = read_jsonl(fixture / "raw-label-b.jsonl")
    adjudication = read_jsonl(fixture / "adjudication.jsonl")
    id_map = read_json(fixture / "blind-id-map.json")
    return {
        "fixture": fixture,
        "samples": samples,
        "split": split,
        "labels": labels,
        "raw_a": raw_a,
        "raw_b": raw_b,
        "adjudication": adjudication,
        "id_map": id_map,
    }


def validate_fixture(data: dict) -> dict:
    fixture = data["fixture"]
    verify_fixture_hashes(fixture)
    schemas = {
        name: read_json(fixture / "schemas" / name)
        for name in (
            "sample.schema.json",
            "split.schema.json",
            "labels.schema.json",
            "raw-label.schema.json",
            "adjudication.schema.json",
        )
    }
    samples = data["samples"]
    if len(samples) != 64:
        raise EvaluationError(f"expected 64 samples, found {len(samples)}")
    sample_by_id = {}
    groups = defaultdict(list)
    normalized_hashes = set()
    for index, row in enumerate(samples, 1):
        validate_schema(row, schemas["sample.schema.json"], f"samples.jsonl:{index}")
        sample_id = row.get("sample_id")
        if not isinstance(sample_id, str) or not re.fullmatch(r"[HM]-(?:TD|DR|GH)-0[1-8]-0[1-4]", sample_id):
            raise EvaluationError(f"invalid internal sample id {sample_id!r}")
        if sample_id in sample_by_id:
            raise EvaluationError(f"duplicate sample id {sample_id}")
        sample_by_id[sample_id] = row
        groups[row["source_group_id"]].append(row)
        text = row["text"]
        if row["text_sha256"] != sha256_text(text.replace("\r\n", "\n").replace("\r", "\n")):
            raise EvaluationError(f"text digest mismatch for {sample_id}")
        norm_hash = sha256_text(normalized_text(text))
        if row["normalized_sha256"] != norm_hash or norm_hash in normalized_hashes:
            raise EvaluationError(f"normalized duplicate or digest mismatch for {sample_id}")
        normalized_hashes.add(norm_hash)
        if row["selection_seed"] != SEED or not 0 <= row["nearest_fivegram_jaccard"] < 0.80:
            raise EvaluationError(f"selection metadata invalid for {sample_id}")
        if row["origin"] == "human":
            if parse_timestamp(row["source_timestamp"]) >= HUMAN_CUTOFF:
                raise EvaluationError(f"human source is at or after cutoff: {sample_id}")
            if row["origin_evidence"].get("cutoff") != "2025-08-01T00:00:00Z":
                raise EvaluationError(f"human cutoff evidence mismatch: {sample_id}")
        elif row["origin"] == "model_assisted":
            if row["origin_evidence"].get("type") not in {
                "affirmative_shoggoth_commit_trailers", "affirmative_named_model_coauthor"
            }:
                raise EvaluationError(f"model origin is not affirmative: {sample_id}")
        else:
            raise EvaluationError(f"invalid origin for {sample_id}")
        if row["genre"] not in GENRES or row["default_branch_reachable"] is not True:
            raise EvaluationError(f"genre or reachability invalid for {sample_id}")
    if len(groups) != 16 or any(len(rows) != 4 for rows in groups.values()):
        raise EvaluationError("fixture must have 16 four-sample groups")
    for group_id, rows in groups.items():
        ordered = sorted(rows, key=lambda row: sha256_text(SEED + row["source_url"] + row["text"]))
        if [row["selection_rank_within_group"] for row in ordered] != [1, 2, 3, 4]:
            raise EvaluationError(f"selection order does not replay for {group_id}")
    if Counter(row["origin"] for row in samples) != Counter({"human": 32, "model_assisted": 32}):
        raise EvaluationError("origin balance is not 32/32")
    for index, left in enumerate(samples):
        for right in samples[index + 1:]:
            score = jaccard(left["text"], right["text"])
            if score >= 0.80:
                raise EvaluationError(f"sample duplicate leakage: {left['sample_id']} {right['sample_id']} {score}")

    split = data["split"]
    validate_schema(split, schemas["split.schema.json"], "split.json")
    calibration, holdout = set(split["calibration_samples"]), set(split["holdout_samples"])
    if len(calibration) != 32 or len(holdout) != 32 or calibration & holdout or calibration | holdout != set(sample_by_id):
        raise EvaluationError("invalid 32/32 sample split")
    cg, hg = set(split["calibration_groups"]), set(split["holdout_groups"])
    if len(cg) != 8 or len(hg) != 8 or cg & hg or cg | hg != set(groups):
        raise EvaluationError("invalid 8/8 group split")
    for sample_id, row in sample_by_id.items():
        expected = cg if sample_id in calibration else hg
        if row["source_group_id"] not in expected:
            raise EvaluationError(f"group leakage for {sample_id}")

    expected_calibration = []
    for origin in ORIGINS:
        candidates = []
        for group_id, rows in groups.items():
            if rows[0]["origin"] == origin:
                candidates.append({"group_id": group_id, "genre": rows[0]["genre"]})
        ordered = sorted(candidates, key=lambda row: sha256_text(SEED + "|split|" + row["group_id"]))
        options = []
        for combo in itertools.combinations(ordered, 4):
            remaining = [row for row in ordered if row not in combo]
            if len({row["genre"] for row in combo}) < 3 or len({row["genre"] for row in remaining}) < 3:
                continue
            genres = {row["genre"] for row in ordered}
            imbalance = sum(
                abs(sum(row["genre"] == genre for row in combo) - sum(row["genre"] == genre for row in remaining))
                for genre in genres
            )
            key = (imbalance, [sha256_text(SEED + "|combo|" + row["group_id"]) for row in combo])
            options.append((key, combo))
        expected_calibration.extend(row["group_id"] for row in min(options, key=lambda item: item[0])[1])
    if sorted(expected_calibration) != sorted(cg):
        raise EvaluationError("source-group split does not replay from the fixed seed")
    for part, ids in (("calibration", calibration), ("holdout", holdout)):
        rows = [sample_by_id[sample_id] for sample_id in ids]
        if Counter(row["origin"] for row in rows) != Counter({"human": 16, "model_assisted": 16}):
            raise EvaluationError(f"origin imbalance in {part}")
        for origin in ORIGINS:
            if {row["genre"] for row in rows if row["origin"] == origin} != set(GENRES):
                raise EvaluationError(f"genre gap in {part}/{origin}")

    mapping_rows = data["id_map"].get("mapping")
    if not isinstance(mapping_rows, list) or len(mapping_rows) != 64:
        raise EvaluationError("blind id map is not 64 rows")
    blind_to_internal = {}
    for index, row in enumerate(mapping_rows, 1):
        blind = row.get("blind_id")
        if blind != f"B-{index:03d}" or row.get("sample_id") not in sample_by_id:
            raise EvaluationError(f"invalid blind mapping row {index}")
        blind_to_internal[blind] = row["sample_id"]
    if len(set(blind_to_internal.values())) != 64:
        raise EvaluationError("blind mapping is not one-to-one")

    families = read_json(fixture / "schemas" / "annotation-packet.schema.json")
    del families  # Schema parses here; family membership comes from the sealed packet rules below.
    packet_rules = {
        "hard": {"structural_metaphor", "claude_tic", "hedge_pivot", "closer", "brochure", "consultant", "invented_confidence", "register_cosplay", "empty_hedge"},
        "gated": {"mathematical", "engineering", "intensifier", "spatial"},
        "structural": {"negation_correction", "concessive_pivot", "rhetorical_fragment", "heading_fragment", "false_range", "metacommentary", "reader_stage_direction", "fake_quote", "rule_of_three", "repeated_opener", "flat_sentence_length"},
    }
    label_by_id = {}
    if len(data["labels"]) != 64:
        raise EvaluationError("mapped labels must cover 64 samples")
    for index, row in enumerate(data["labels"], 1):
        validate_schema(row, schemas["labels.schema.json"], f"labels.jsonl:{index}")
        sample_id, blind = row.get("sample_id"), row.get("blind_id")
        if sample_id not in sample_by_id or blind_to_internal.get(blind) != sample_id or sample_id in label_by_id:
            raise EvaluationError(f"invalid mapped label row {sample_id}/{blind}")
        for number, label in enumerate(row.get("labels", []), 1):
            validate_annotation(sample_by_id[sample_id]["text"], label, packet_rules, f"labels/{sample_id}/{number}")
        label_by_id[sample_id] = row["labels"]

    raw_sets = {}
    for key in ("raw_a", "raw_b"):
        rows = data[key]
        if len(rows) != 64 or {row.get("sample_id") for row in rows} != set(blind_to_internal):
            raise EvaluationError(f"{key} does not cover every blind id")
        raw_sets[key] = {}
        annotators = {row.get("annotator_id") for row in rows}
        if len(annotators) != 1:
            raise EvaluationError(f"{key} has mixed annotator ids")
        for index, row in enumerate(rows, 1):
            validate_schema(row, schemas["raw-label.schema.json"], f"{key}:{index}")
            blind = row["sample_id"]
            for number, label in enumerate(row.get("annotations", []), 1):
                validate_annotation(sample_by_id[blind_to_internal[blind]]["text"], label, packet_rules, f"{key}/{blind}/{number}")
            raw_sets[key][blind] = row["annotations"]

    if {row["annotator_id"] for row in data["raw_a"]} == {row["annotator_id"] for row in data["raw_b"]}:
        raise EvaluationError("raw annotation sets must name distinct annotators")

    if len(data["adjudication"]) != 64 or {row.get("sample_id") for row in data["adjudication"]} != set(blind_to_internal):
        raise EvaluationError("adjudication does not cover every blind id")
    for index, row in enumerate(data["adjudication"], 1):
        validate_schema(row, schemas["adjudication.schema.json"], f"adjudication.jsonl:{index}")
        if not isinstance(row.get("disagreement_count"), int) or row["disagreement_count"] < 0:
            raise EvaluationError(f"invalid disagreement count for {row.get('sample_id')}")
        if not isinstance(row.get("adjudicator_reason"), str) or not row["adjudicator_reason"].strip():
            raise EvaluationError(f"missing adjudicator reason for {row.get('sample_id')}")
        mapped = label_by_id[blind_to_internal[row["sample_id"]]]
        if row.get("labels") != mapped:
            raise EvaluationError(f"mapped labels disagree with blind adjudication for {row['sample_id']}")

    return {
        "sample_by_id": sample_by_id,
        "labels_by_id": label_by_id,
        "blind_to_internal": blind_to_internal,
        "raw_a": raw_sets["raw_a"],
        "raw_b": raw_sets["raw_b"],
        "split": {"calibration": calibration, "holdout": holdout},
        "summary": {
            "samples": 64,
            "groups": 16,
            "origins": {origin: 32 for origin in ORIGINS},
            "split_samples": {"calibration": 32, "holdout": 32},
            "duplicate_threshold": 0.80,
            "max_saved_nearest_fivegram_jaccard": max(row["nearest_fivegram_jaccard"] for row in samples),
            "human_cutoff": "2025-08-01T00:00:00Z",
        },
    }


def token_ids(text: str, label: dict) -> set[int]:
    ids = set()
    for index, match in enumerate(re.finditer(r"[\w']+", text, flags=re.UNICODE)):
        start = len(text[:match.start()].encode("utf-8"))
        end = len(text[:match.end()].encode("utf-8"))
        if start < label["end_byte"] and end > label["start_byte"]:
            ids.add(index)
    return ids


def span_iou(text: str, left: dict, right: dict) -> float:
    if (left["start_byte"], left["end_byte"]) == (right["start_byte"], right["end_byte"]):
        return 1.0
    a, b = token_ids(text, left), token_ids(text, right)
    return len(a & b) / len(a | b) if a | b else 0.0


def match_spans(text: str, predicted: list[dict], gold: list[dict], *, require_decision: bool = False):
    candidates = []
    for pi, pred in enumerate(predicted):
        for gi, expected in enumerate(gold):
            if (pred["tier"], pred["family"]) != (expected["tier"], expected["family"]):
                continue
            if require_decision and pred.get("decision") != expected.get("decision"):
                continue
            overlap = span_iou(text, pred, expected)
            if overlap >= 0.50:
                candidates.append((overlap, pi, gi))
    used_pred, used_gold, matches = set(), set(), []
    for overlap, pi, gi in sorted(candidates, key=lambda row: (-row[0], row[1], row[2])):
        if pi in used_pred or gi in used_gold:
            continue
        used_pred.add(pi)
        used_gold.add(gi)
        matches.append({"predicted": pi, "gold": gi, "iou": round(overlap, 6)})
    return matches, used_pred, used_gold


def cohen_kappa(left: list[bool], right: list[bool]):
    if len(left) != len(right) or not left:
        raise EvaluationError("kappa inputs need the same non-zero denominator")
    total = len(left)
    observed = sum(a == b for a, b in zip(left, right)) / total
    pa, pb = sum(left) / total, sum(right) / total
    expected = pa * pb + (1 - pa) * (1 - pb)
    return None if expected == 1 else round((observed - expected) / (1 - expected), 6)


def agreement(validated: dict) -> dict:
    raw_a, raw_b = validated["raw_a"], validated["raw_b"]
    sample_by_id = validated["sample_by_id"]
    blind_to_internal = validated["blind_to_internal"]
    by_tier = {}
    all_a, all_b = [], []
    for tier in TIERS:
        a_binary, b_binary = [], []
        for blind in sorted(blind_to_internal):
            a_binary.append(any(label["tier"] == tier and label["decision"] == "actionable" for label in raw_a[blind]))
            b_binary.append(any(label["tier"] == tier and label["decision"] == "actionable" for label in raw_b[blind]))
        all_a.extend(a_binary)
        all_b.extend(b_binary)
        by_tier[tier] = {
            "denominator": 64,
            "a_positive": sum(a_binary),
            "b_positive": sum(b_binary),
            "kappa": cohen_kappa(a_binary, b_binary),
        }

    def span_result(tier=None):
        a_count = b_count = matched = 0
        for blind, sample_id in sorted(blind_to_internal.items()):
            a_labels = [label for label in raw_a[blind] if tier is None or label["tier"] == tier]
            b_labels = [label for label in raw_b[blind] if tier is None or label["tier"] == tier]
            matches, _, _ = match_spans(sample_by_id[sample_id]["text"], a_labels, b_labels, require_decision=True)
            a_count += len(a_labels)
            b_count += len(b_labels)
            matched += len(matches)
        return {
            "a_spans": a_count,
            "b_spans": b_count,
            "matched": matched,
            "f1": ratio(2 * matched, a_count + b_count),
        }

    return {
        "sample_by_tier": {
            "denominator": 192,
            "a_positive": sum(all_a),
            "b_positive": sum(all_b),
            "kappa": cohen_kappa(all_a, all_b),
            "by_tier": by_tier,
        },
        "raw_span": {
            **span_result(),
            "by_tier": {tier: span_result(tier) for tier in TIERS},
        },
    }


def line_col_to_bytes(text: str, line: int, col: int, term: str) -> tuple[int, int]:
    lines = text.splitlines(keepends=True)
    if line < 1 or line > len(lines):
        raise EvaluationError(f"prediction line outside text: {line}")
    char_start = sum(len(value) for value in lines[:line - 1]) + col - 1
    char_end = min(len(text), char_start + len(term))
    return len(text[:char_start].encode("utf-8")), len(text[:char_end].encode("utf-8"))


def predict(text: str) -> tuple[list[dict], list[dict]]:
    result = build(text)
    scored, signals = [], []
    for source, target, decision in ((result["hits"], scored, "actionable"), (result["signals"], signals, "signal_only")):
        for hit in source:
            start, end = line_col_to_bytes(text, hit["line"], hit["col"], hit["term"])
            target.append({
                "tier": hit["pass"],
                "family": hit["family"],
                "start_byte": start,
                "end_byte": end,
                "decision": decision,
                "severity": hit["severity"],
                "term": hit["term"],
            })
    return scored, signals


def coverage(validated: dict, sample_ids: set[str]) -> dict:
    output = {}
    for tier in TIERS:
        actionable_spans = positive_samples = 0
        by_origin = Counter()
        for sample_id in sample_ids:
            labels = [label for label in validated["labels_by_id"][sample_id] if label["tier"] == tier and label["decision"] == "actionable"]
            actionable_spans += len(labels)
            if labels:
                positive_samples += 1
                by_origin[validated["sample_by_id"][sample_id]["origin"]] += len(labels)
        output[tier] = {
            "actionable_spans": actionable_spans,
            "positive_samples": positive_samples,
            "negative_samples": len(sample_ids) - positive_samples,
            "actionable_by_origin": {origin: by_origin[origin] for origin in ORIGINS},
        }
    return output


def metric_block(validated: dict, sample_ids: Iterable[str], predictions: dict, *, tier: str, family: str | None = None) -> dict:
    ids = sorted(sample_ids)
    tp = fp = fn = tn = false_positive_samples = positive_samples = 0
    missed_critical = []
    for sample_id in ids:
        gold = [label for label in validated["labels_by_id"][sample_id] if label["tier"] == tier and label["decision"] == "actionable" and (family is None or label["family"] == family)]
        pred = [label for label in predictions[sample_id]["scored"] if label["tier"] == tier and (family is None or label["family"] == family)]
        matches, used_pred, used_gold = match_spans(validated["sample_by_id"][sample_id]["text"], pred, gold)
        tp += len(matches)
        fp += len(pred) - len(used_pred)
        fn += len(gold) - len(used_gold)
        if gold:
            positive_samples += 1
        elif not pred:
            tn += 1
        else:
            false_positive_samples += 1
        for index, label in enumerate(gold):
            if index not in used_gold and label["severity"] == "critical":
                missed_critical.append({"sample_id": sample_id, "family": label["family"], "start_byte": label["start_byte"], "end_byte": label["end_byte"]})
    precision = ratio(tp, tp + fp)
    recall = ratio(tp, tp + fn)
    return {
        "samples": len(ids), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "false_positive_samples": false_positive_samples,
        "positive_samples": positive_samples,
        "negative_samples": len(ids) - positive_samples,
        "precision": precision, "recall": recall, "f1": f1(precision, recall),
        "specificity": ratio(tn, tn + false_positive_samples),
        "gold_prevalence": ratio(positive_samples, len(ids)),
        "missed_critical": missed_critical,
    }


def evaluate(validated: dict, sample_ids: set[str]) -> dict:
    predictions = {}
    for sample_id in sorted(sample_ids):
        scored, signals = predict(validated["sample_by_id"][sample_id]["text"])
        predictions[sample_id] = {"scored": scored, "signals": signals}
    by_tier = {tier: metric_block(validated, sample_ids, predictions, tier=tier) for tier in TIERS}
    by_origin = {}
    for origin in ORIGINS:
        ids = {sample_id for sample_id in sample_ids if validated["sample_by_id"][sample_id]["origin"] == origin}
        by_origin[origin] = {tier: metric_block(validated, ids, predictions, tier=tier) for tier in TIERS}
    families = sorted({label["family"] for sample_id in sample_ids for label in validated["labels_by_id"][sample_id] if label["decision"] == "actionable"})
    by_family = {}
    for family in families:
        tier = next(label["tier"] for sample_id in sample_ids for label in validated["labels_by_id"][sample_id] if label["decision"] == "actionable" and label["family"] == family)
        by_family[family] = {"tier": tier, **metric_block(validated, sample_ids, predictions, tier=tier, family=family)}

    emitted = useful = 0
    for sample_id in sample_ids:
        gold = [label for label in validated["labels_by_id"][sample_id] if label["decision"] == "signal_only"]
        pred = predictions[sample_id]["signals"]
        matches, _, _ = match_spans(validated["sample_by_id"][sample_id]["text"], pred, gold, require_decision=True)
        emitted += len(pred)
        useful += len(matches)
    return {
        "by_tier": by_tier,
        "by_origin": by_origin,
        "by_family": by_family,
        "advisory": {"emitted": emitted, "useful": useful, "alert_yield": ratio(useful, emitted)},
        "prediction_counts": {
            "scored": sum(len(row["scored"]) for row in predictions.values()),
            "signals": sum(len(row["signals"]) for row in predictions.values()),
        },
    }


def file_hashes() -> dict:
    paths = [SCRIPT_DIR / "imprimatur.py", SKILL_ROOT / "lexicon" / "hard.json", SKILL_ROOT / "lexicon" / "gated.json", SKILL_ROOT / "lexicon" / "structural.json"]
    return {str(path.relative_to(SKILL_ROOT)): sha256_bytes(path.read_bytes()) for path in paths}


class GitHubReader:
    def __init__(self):
        self.cache = {}
        token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
        self.headers = {"Accept": "application/vnd.github+json", "User-Agent": "imprimatur-labelled-corpus-v1"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def get(self, url: str, *, json_value: bool = False):
        key = (url, json_value)
        if key not in self.cache:
            request = urllib.request.Request(url, headers=self.headers)
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    blob = response.read()
            except Exception as exc:
                raise EvaluationError(f"source request failed for {url}: {exc}") from exc
            self.cache[key] = json.loads(blob) if json_value else blob.decode("utf-8")
        return self.cache[key]


def message_paragraphs(message: str) -> list[tuple[int, str]]:
    clean = re.split(r"(?im)^\s*(?:co-authored-by|wildcat-origin|signed-off-by):", message)[0]
    output = []
    for ordinal, block in enumerate(re.split(r"\n\s*\n", clean), 1):
        prose = " ".join(line.strip() for line in block.splitlines()).strip()
        count = len(re.findall(r"\b[\w'-]+\b", prose))
        if 18 <= count <= 180:
            output.append((ordinal, prose))
    return output


def verify_sources(validated: dict) -> dict:
    reader = GitHubReader()
    compare_cache, commit_cache = {}, {}
    for sample_id, row in sorted(validated["sample_by_id"].items()):
        repository, commit = row["repository"], row["source_commit"]
        compare_key = (repository, commit, row["collection_head"])
        if compare_key not in compare_cache:
            url = f"https://api.github.com/repos/{repository}/compare/{commit}...{row['collection_head']}"
            value = reader.get(url, json_value=True)
            compare_cache[compare_key] = value.get("status") in {"ahead", "identical"}
        if not compare_cache[compare_key]:
            raise EvaluationError(f"source is not ancestor of pinned collection head: {sample_id}")
        commit_key = (repository, commit)
        if commit_key not in commit_cache:
            commit_cache[commit_key] = reader.get(
                f"https://api.github.com/repos/{repository}/commits/{commit}",
                json_value=True,
            )
        source_commit = commit_cache[commit_key]
        immutable_times = {
            parse_timestamp(source_commit["commit"]["author"]["date"]),
            parse_timestamp(source_commit["commit"]["committer"]["date"]),
        }
        if parse_timestamp(row["source_timestamp"]) not in immutable_times:
            raise EvaluationError(f"source timestamp mismatch: {sample_id}")
        if row["origin"] == "human" and any(value >= HUMAN_CUTOFF for value in immutable_times):
            raise EvaluationError(f"human source has an immutable timestamp at or after cutoff: {sample_id}")
        if row["source_object"] == "markdown_paragraph":
            path = urllib.parse.quote(row["source_path"])
            raw = reader.get(f"https://raw.githubusercontent.com/{repository}/{commit}/{path}")
            lines = raw.replace("\r\n", "\n").replace("\r", "\n").splitlines()
            text = " ".join(line.strip() for line in lines[row["source_start_line"] - 1:row["source_end_line"]])
        else:
            if row["source_start_line"] != row["source_end_line"]:
                raise EvaluationError(f"commit message range spans paragraphs: {sample_id}")
            paragraphs = dict(message_paragraphs(source_commit["commit"]["message"]))
            text = paragraphs.get(row["source_start_line"])
        if text != row["text"]:
            raise EvaluationError(f"immutable source text mismatch: {sample_id}")
        if row["origin"] == "model_assisted":
            evidence_commit = row["origin_evidence"]["commit"]
            key = (repository, evidence_commit)
            if key not in commit_cache:
                commit_cache[key] = reader.get(
                    f"https://api.github.com/repos/{repository}/commits/{evidence_commit}",
                    json_value=True,
                )
            message = commit_cache[key]["commit"]["message"].lower()
            if not any(marker in message for marker in MODEL_MARKERS):
                raise EvaluationError(f"affirmative model marker missing: {sample_id}")
    return {
        "verified_samples": 64,
        "verified_compare_objects": len(compare_cache),
        "verified_commits": len(commit_cache),
    }


def gate_report(agreement_result: dict, coverage_result: dict, metrics: dict | None) -> dict:
    gates = {
        "agreement_sample_by_tier_kappa_at_least_0_80": agreement_result["sample_by_tier"]["kappa"] is not None and agreement_result["sample_by_tier"]["kappa"] >= 0.80,
        "agreement_raw_span_f1_at_least_0_80": agreement_result["raw_span"]["f1"] is not None and agreement_result["raw_span"]["f1"] >= 0.80,
        "holdout_eight_actionable_per_tier": all(row["actionable_spans"] >= 8 for row in coverage_result.values()),
        "holdout_eight_negative_samples_per_tier": all(row["negative_samples"] >= 8 for row in coverage_result.values()),
    }
    if metrics is not None:
        tiers = metrics["by_tier"]
        gates.update({
            "hard_precision_1_00": tiers["hard"]["precision"] == 1.0,
            "hard_recall_1_00": tiers["hard"]["recall"] == 1.0,
            "gated_precision_at_least_0_90": tiers["gated"]["precision"] is not None and tiers["gated"]["precision"] >= 0.90,
            "gated_recall_at_least_0_90": tiers["gated"]["recall"] is not None and tiers["gated"]["recall"] >= 0.90,
            "structural_precision_at_least_0_90": tiers["structural"]["precision"] is not None and tiers["structural"]["precision"] >= 0.90,
            "structural_recall_at_least_0_90": tiers["structural"]["recall"] is not None and tiers["structural"]["recall"] >= 0.90,
            "no_missed_critical": not any(tier["missed_critical"] for tier in tiers.values()),
        })
        origin_gap_ok = True
        origin_gaps = {}
        for tier in TIERS:
            left, right = metrics["by_origin"]["human"][tier], metrics["by_origin"]["model_assisted"][tier]
            relevant_left = left["tp"] + left["fn"]
            relevant_right = right["tp"] + right["fn"]
            gap = None if left["f1"] is None or right["f1"] is None else round(abs(left["f1"] - right["f1"]), 6)
            origin_gaps[tier] = {"human_relevant": relevant_left, "model_assisted_relevant": relevant_right, "f1_gap": gap}
            if relevant_left >= 8 and relevant_right >= 8 and gap is not None and gap > 0.15:
                origin_gap_ok = False
        gates["no_origin_f1_gap_above_0_15_when_both_relevant_at_least_8"] = origin_gap_ok
        repeated = {}
        for family, row in metrics["by_family"].items():
            if row["fp"] >= 2 or row["fn"] >= 2:
                repeated[family] = {"fp": row["fp"], "fn": row["fn"]}
        gates["no_family_with_two_errors_same_direction"] = not repeated
        gates["origin_f1_gaps"] = origin_gaps
        gates["repeated_family_errors"] = repeated
    return gates


def report_for_split(fixture: Path, split_name: str, *, verify: bool = False, validate_only: bool = False) -> dict:
    data = load_fixture(fixture)
    validated = validate_fixture(data)
    agreement_result = agreement(validated)
    holdout_coverage = coverage(validated, validated["split"]["holdout"])
    selected_ids = set(validated["sample_by_id"]) if split_name == "all" else validated["split"][split_name]
    metrics = None if validate_only else evaluate(validated, selected_ids)
    output = {
        "schema_version": 1,
        "fixture": fixture.name,
        "provisional": True,
        "split": split_name,
        "fixture_validation": validated["summary"],
        "agreement": agreement_result,
        "coverage": {
            "calibration": coverage(validated, validated["split"]["calibration"]),
            "holdout": holdout_coverage,
        },
        "candidate_hashes": file_hashes(),
        "metrics": metrics,
        "gates": gate_report(agreement_result, holdout_coverage, metrics),
    }
    if verify:
        output["source_verification"] = verify_sources(validated)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, required=True)
    parser.add_argument("--split", choices=("calibration", "holdout", "all", "both"), default="all")
    parser.add_argument("--verify-sources", action="store_true")
    parser.add_argument("--validate-only", action="store_true", help="validate fixture and annotation evidence without running Imprimatur")
    parser.add_argument("--report", type=Path)
    parser.add_argument("--expect", type=Path, help="compare the generated report byte-for-byte with this file")
    args = parser.parse_args()
    try:
        fixture = args.fixture.resolve()
        if args.split == "both":
            report = {
                "schema_version": 1,
                "fixture": fixture.name,
                "provisional": True,
                "holdout_spent": not args.validate_only,
                "calibration": report_for_split(
                    fixture, "calibration", verify=args.verify_sources, validate_only=args.validate_only
                ),
                "holdout": report_for_split(
                    fixture, "holdout", verify=args.verify_sources, validate_only=args.validate_only
                ),
            }
        else:
            report = report_for_split(fixture, args.split, verify=args.verify_sources, validate_only=args.validate_only)
        rendered = canonical_json(report)
        if args.expect is not None and args.expect.read_text(encoding="utf-8") != rendered:
            raise EvaluationError(f"report differs from {args.expect}")
        if args.report is not None:
            args.report.write_text(rendered, encoding="utf-8")
        else:
            sys.stdout.write(rendered)
    except (EvaluationError, OSError, KeyError, IndexError, TypeError) as exc:
        sys.stderr.write(f"evaluate-labelled-corpus: {exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
