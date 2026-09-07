#!/usr/bin/env python3
"""Resolve one cell of the anamnesis-2 design record from the tree at this commit.

Usage, from the repository root:

    python3 .hexaemeron/reports/resolve.py <candidate> <criterion>

Every value is computed over the checked-out tree plus the candidate's declared
construction (which document holds the scope, which pilot tokens it moves, how
many corpora its acceptance rebuilds). Nothing here predicts an implementation
that does not exist; where a value follows from the candidate's definition, the
definition is data in this file and the report names this command.

The report is printed. It is written only to a path named by ``--out``, which
must not already exist, so a rerun from the committed copy can never replace a
receipted report under ``.hexaemeron/reports/``. The ``pilot-artefacts-rebuilt``
grep excludes ``plugins/anamnesis/docs`` and ``plugins/anamnesis/tests``: this
run's own records quote the pilot's tokens, and a guard pins them, without
either being one of the pilot artefacts the study enumerates, so counting them
would move the value every time a record or a guard is committed.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import statistics
import subprocess
import sys
import time

ROOT = os.getcwd()
PILOT = "plugins/anamnesis/specimens/pilot"
SCRIPT = "plugins/anamnesis/skills/anamnesis/scripts/anamnesis.py"
REPORTS = ".hexaemeron/reports"
SCHEMA = "protasis-design-report/v1"

# The estate corpus the study specifies: two sources, seventeen finding records.
ESTATE_RECORDS = 17
ESTATE_BOUNDS = (10, 40)
ESTATE_SOURCES = ["archive-verification-2026-08-31", "counterparty-history-2026-09-05"]

PILOT_SCOPE = {
    "id": "warden-seed-pilot",
    "preserves": "Warden audit rounds from three first-party skills as preserved at commit 1c1137898bce.",
    "sources": ["hexaemeron-audit-rounds", "pandects-audit-rounds", "tabularium-audit-rounds"],
    "records": {"minimum": 25, "maximum": 50},
}
# In the admission policy the source list already exists, so the scope there
# carries no `sources` list of its own.
PILOT_SCOPE_ADMISSION = {
    "id": PILOT_SCOPE["id"],
    "preserves": PILOT_SCOPE["preserves"],
    "records": dict(PILOT_SCOPE["records"]),
}

CANDIDATES = {
    "release-policy-scope": {
        "scope_home": "curation-policy",
        "scope_object": PILOT_SCOPE,
        "moves": ("curation-policy", "release-id", "program"),
        "corpora_rebuilt": 2,
        "ledgers": ["plugins/anamnesis/skills/anamnesis/EVOLUTION.md"],
        "extends_release_id": False,
    },
    "admission-policy-scope": {
        "scope_home": "admission-policy",
        "scope_object": PILOT_SCOPE_ADMISSION,
        "moves": ("admission-policy", "release-id", "program"),
        "corpora_rebuilt": 2,
        "ledgers": ["plugins/anamnesis/skills/anamnesis/EVOLUTION.md"],
        "extends_release_id": True,
    },
    "permanent-seed-record": {
        "scope_home": None,
        "scope_object": None,
        "moves": (),
        "corpora_rebuilt": 0,
        "ledgers": ["plugins/anamnesis/skills/anamnesis/EVOLUTION.md"],
        "extends_release_id": False,
    },
    "widen-constant": {
        "scope_home": None,
        "scope_object": None,
        "moves": ("program",),
        "corpora_rebuilt": 1,
        "ledgers": ["plugins/anamnesis/skills/anamnesis/EVOLUTION.md"],
        "extends_release_id": False,
    },
}


def load_anamnesis():
    spec = importlib.util.spec_from_file_location("anamnesis_resolver", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_json(path):
    with open(path, "rb") as handle:
        return json.load(handle)


def sha256_file(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def git_grep_files(token, scope="plugins/anamnesis"):
    completed = subprocess.run(
        [
            "git", "grep", "-l", "-F", token, "--", scope,
            ":(exclude)plugins/anamnesis/docs", ":(exclude)plugins/anamnesis/tests",
        ],
        capture_output=True, text=True, check=False,
    )
    return {line.strip() for line in completed.stdout.splitlines() if line.strip()}


def release_id_hashes_curation_policy():
    """Read release_id's body: does it hash canonical(policy), the curation policy?"""
    with open(SCRIPT, encoding="utf-8") as handle:
        source = handle.read()
    body = source.split("def release_id(", 1)[1].split("\ndef ", 1)[0]
    return "canonical(policy)" in body


def seed_bound_in_code():
    """The literal record bound sits in anamnesis.py at this commit."""
    with open(SCRIPT, encoding="utf-8") as handle:
        source = handle.read()
    return "25 <= record_count <= 50" in source


def criterion_release_id_declared_function(candidate):
    spec = CANDIDATES[candidate]
    if spec["scope_home"] is None:
        return False, "boolean"
    if spec["scope_home"] == "curation-policy":
        return release_id_hashes_curation_policy(), "boolean"
    # admission policy: not hashed at this commit; the candidate declares the extension.
    return bool(spec["extends_release_id"]), "boolean"


def criterion_scope_recorded_in_release(candidate):
    spec = CANDIDATES[candidate]
    if spec["scope_home"] is None:
        return False, "boolean"
    manifest = read_json(os.path.join(PILOT, "release/manifest.json"))
    component_digests = {c["sha256"] for c in manifest["components"]}
    component_paths = {c["path"] for c in manifest["components"]}
    if spec["scope_home"] == "curation-policy":
        return "policy.json" in component_paths and manifest["policy"] == read_json(
            os.path.join(PILOT, "release/policy.json")), "boolean"
    admission_digest = sha256_file(os.path.join(PILOT, "policy.json"))
    return admission_digest in component_digests, "boolean"


def criterion_estate_admissible(candidate):
    spec = CANDIDATES[candidate]
    an = load_anamnesis()
    if spec["scope_home"] is None:
        try:
            an.seed_scope(ESTATE_RECORDS)
        except an.Refusal:
            return False, "boolean"
        return True, "boolean"
    low, high = ESTATE_BOUNDS
    return low <= ESTATE_RECORDS <= high, "boolean"


def criterion_foreign_ledgers_touched(candidate):
    spec = CANDIDATES[candidate]
    completed = subprocess.run(
        ["git", "ls-files", "plugins/*/skills/*/EVOLUTION.md"],
        capture_output=True, text=True, check=True,
    )
    governed = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    governed -= {"plugins/anamnesis/skills/anamnesis/EVOLUTION.md"}
    touched = set(spec["ledgers"]) & governed
    return len(touched), "count"


def criterion_pilot_artefacts_rebuilt(candidate):
    spec = CANDIDATES[candidate]
    an = load_anamnesis()
    manifest = read_json(os.path.join(PILOT, "release/manifest.json"))
    curation = read_json(os.path.join(PILOT, "curation-policy.json"))
    policy_component = next(c for c in manifest["components"] if c["path"] == "policy.json")
    admission_digest = sha256_file(os.path.join(PILOT, "policy.json"))
    program_digest = sha256_file(SCRIPT)
    correlation = [an.correlation_id(admission_digest, s["id"]) for s in manifest["sources"]]
    tokens = {
        "curation-policy": [curation["version"], policy_component["sha256"]],
        "admission-policy": [admission_digest] + correlation,
        "release-id": [manifest["release_id"]],
        "program": [program_digest],
    }
    files = set()
    for move in spec["moves"]:
        for token in tokens[move]:
            files |= git_grep_files(token)
        if move == "admission-policy":
            files.add(os.path.join(PILOT, "policy.json"))
    return len(files), "count"


def criterion_policy_bytes_added(candidate):
    spec = CANDIDATES[candidate]
    if spec["scope_object"] is None:
        return 0, "bytes"
    an = load_anamnesis()
    if spec["scope_home"] == "curation-policy":
        policy = read_json(os.path.join(PILOT, "curation-policy.json"))
    else:
        policy = read_json(os.path.join(PILOT, "policy.json"))
    before = len(an.canonical(policy))
    with_scope = dict(policy)
    with_scope["scope"] = spec["scope_object"]
    return len(an.canonical(with_scope)) - before, "bytes"


def criterion_acceptance_check_ms(candidate):
    spec = CANDIDATES[candidate]
    an = load_anamnesis()
    samples = []
    for _ in range(5):
        started = time.perf_counter()
        an.verify_rebuild(PILOT)
        samples.append((time.perf_counter() - started) * 1000.0)
    per_corpus = statistics.median(samples)
    return int(round(per_corpus * spec["corpora_rebuilt"])), "milliseconds"


def criterion_scope_recovery_by_policy_edit(candidate):
    spec = CANDIDATES[candidate]
    in_code = seed_bound_in_code()
    if not in_code:
        raise SystemExit("the record bound is not where this resolver expects it")
    return spec["scope_home"] is not None, "boolean"


CRITERIA = {
    "release-id-declared-function": criterion_release_id_declared_function,
    "scope-recorded-in-release": criterion_scope_recorded_in_release,
    "estate-findings-admissible-without-widening": criterion_estate_admissible,
    "foreign-ledgers-touched": criterion_foreign_ledgers_touched,
    "pilot-artefacts-rebuilt": criterion_pilot_artefacts_rebuilt,
    "policy-bytes-added": criterion_policy_bytes_added,
    "acceptance-check-ms": criterion_acceptance_check_ms,
    "scope-recovery-by-policy-edit": criterion_scope_recovery_by_policy_edit,
}


def main(argv):
    out = None
    if len(argv) == 4 and argv[2] == "--out":
        argv, out = argv[:2], argv[3]
    if len(argv) != 2 or argv[0] not in CANDIDATES or argv[1] not in CRITERIA:
        print(__doc__, file=sys.stderr)
        return 2
    if out is not None and os.path.lexists(out):
        print(f"resolve.py: refusing to replace {out}", file=sys.stderr)
        return 2
    candidate, criterion = argv
    value, unit = CRITERIA[criterion](candidate)
    report = {
        "schema": SCHEMA,
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": unit,
        "command": f"python3 {REPORTS}/resolve.py {candidate} {criterion}",
        "exit": 0,
    }
    body = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if out is not None:
        with open(out, "x", encoding="utf-8") as handle:
            handle.write(body)
    print(body, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
