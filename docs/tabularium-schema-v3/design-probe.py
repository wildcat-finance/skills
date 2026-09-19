#!/usr/bin/env python3
"""Selection-stage design probe for the Tabularium schema v3 study.

Writes one closed protasis-design-report/v1 object per candidate and
selection criterion under --output-dir. Every value is computed from the
tree at the study's starting commit plus one closed candidate declaration
table below; the declaration is the only place a candidate's plan enters.
"""

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "tabularium"
EXAMPLES = PLUGIN / "examples"
RELEASES = ("aave-v4-v0", "euler-v1-v0", "euler-v2-v0")
RELEASE_FILES = ("source.json", "capture.json", "events.jsonl", "coverage.json")
SCHEMA = "protasis-design-report/v1"

sys.path.insert(0, str(PLUGIN / "scripts"))
from tabularium_lib.adapters import aave_v4, euler_v1, euler_v2  # noqa: E402
from tabularium_lib import release_v2  # noqa: E402

ADAPTERS = (aave_v4, euler_v1, euler_v2)

# Closed candidate declarations. Field meanings:
#   forward_schema: which schema document shipped ledgers are validated against
#   changes_v0_bytes: the plan rewrites a committed v0 release file
#   v3_files: the plan commits canonical-event-v3.json and coverage-manifest-v3.json
#   v3_shipped_dirs: shipped release directories carrying schema_version 3
#   keeps_v2_read: verify still accepts a schema_version 2 release
CANDIDATES = {
    "superseding-releases": {
        "forward_schema": "v3",
        "changes_v0_bytes": False,
        "v3_files": True,
        "v3_shipped_dirs": ("aave-v4-v1", "euler-v1-v1", "euler-v2-v1"),
        "keeps_v2_read": True,
    },
    "in-place-migration": {
        "forward_schema": "v3",
        "changes_v0_bytes": True,
        "v3_files": True,
        "v3_shipped_dirs": RELEASES,
        "keeps_v2_read": False,
    },
    "repair-v2-only": {
        "forward_schema": "v2-corrected",
        "changes_v0_bytes": False,
        "v3_files": False,
        "v3_shipped_dirs": (),
        "keeps_v2_read": True,
    },
    "v3-without-shipped-examples": {
        "forward_schema": "v3",
        "changes_v0_bytes": False,
        "v3_files": True,
        "v3_shipped_dirs": (),
        "keeps_v2_read": True,
    },
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def load_rows(release):
    data = (EXAMPLES / release / "events.jsonl").read_bytes()
    return [json.loads(line) for line in data.split(b"\n") if line]


def tuple_table():
    """The closed adapter tuples the shipped code emits."""
    return [
        {
            "venue": m.ADAPTER,
            "adapter": m.ADAPTER,
            "adapter_version": m.ADAPTER_VERSION,
            "protocol_generation": m.PROTOCOL_GENERATION,
            "source_api": m.SOURCE_API,
            "evidence_class": release_v2.EVIDENCE_CLASSES[m.ADAPTER],
            "mapping_rules": sorted(rule for _, _, rule in m.MAPPINGS.values()),
        }
        for m in ADAPTERS
    ]


def forward_event_schema(kind):
    base = json.loads((PLUGIN / "schemas" / "canonical-event-v2.json").read_text())
    table = tuple_table()
    venues = [t["venue"] for t in table]
    props = base["properties"]
    props["venue"] = {"enum": venues}
    prov = props["provenance"]["properties"]
    prov["adapter"] = {"enum": venues}
    prov["adapter_version"] = {"enum": sorted({t["adapter_version"] for t in table})}
    prov["protocol_generation"] = {"enum": venues}
    prov["source_api"] = {"enum": sorted({t["source_api"] for t in table})}
    if kind == "v3":
        props["schema_version"] = {"const": 3}
        prov["mapping_rule"] = {"enum": sorted(r for t in table for r in t["mapping_rules"])}
        base["oneOf"] = [
            {
                "properties": {
                    "venue": {"const": t["venue"]},
                    "provenance": {
                        "properties": {
                            "adapter": {"const": t["adapter"]},
                            "adapter_version": {"const": t["adapter_version"]},
                            "protocol_generation": {"const": t["protocol_generation"]},
                            "source_api": {"const": t["source_api"]},
                            "mapping_rule": {"enum": t["mapping_rules"]},
                        }
                    },
                }
            }
            for t in table
        ]
    return base


def forward_coverage_schema(kind):
    base = json.loads((PLUGIN / "schemas" / "coverage-manifest-v2.json").read_text())
    table = tuple_table()
    venues = [t["venue"] for t in table]
    props = base["properties"]
    src = props["source"]["properties"]
    src["protocol_generation"] = {"enum": venues}
    src["source_api"] = {"enum": sorted({t["source_api"] for t in table})}
    src["evidence_class"] = {"enum": sorted({t["evidence_class"] for t in table})}
    adapter = props["versions"]["properties"]["adapter"]["properties"]
    adapter["name"] = {"enum": venues}
    adapter["version"] = {"enum": sorted({t["adapter_version"] for t in table})}
    if kind == "v3":
        props["schema_version"] = {"const": 3}
        props["versions"]["properties"]["event_schema"] = {"const": 3}
    return base


def rows_for(kind, rows):
    if kind == "v3":
        return [dict(row, schema_version=3) for row in rows]
    return rows


def manifest_for(kind, manifest):
    if kind == "v3":
        manifest = dict(manifest, schema_version=3)
        manifest["versions"] = dict(manifest["versions"], event_schema=3)
    return manifest


def emitted_values_admitted(decl):
    import jsonschema

    kind = decl["forward_schema"]
    ev = jsonschema.Draft202012Validator(forward_event_schema(kind))
    cv = jsonschema.Draft202012Validator(forward_coverage_schema(kind))
    jsonschema.Draft202012Validator.check_schema(forward_event_schema(kind))
    jsonschema.Draft202012Validator.check_schema(forward_coverage_schema(kind))
    checked = 0
    for release in RELEASES:
        for row in rows_for(kind, load_rows(release)):
            if list(ev.iter_errors(row)):
                return False, checked
            checked += 1
        manifest = json.loads((EXAMPLES / release / "coverage.json").read_text())
        if list(cv.iter_errors(manifest_for(kind, manifest))):
            return False, checked
        checked += 1
    return True, checked


def published_bytes_unchanged(decl):
    if not decl["changes_v0_bytes"]:
        return True
    # An in-place migration must rewrite schema_version, so the committed
    # canonical digest cannot survive. Show it rather than assert it.
    for release in RELEASES:
        committed = sha256((EXAMPLES / release / "events.jsonl").read_bytes())
        migrated = b"".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")).encode() + b"\n"
            for row in rows_for("v3", load_rows(release))
        )
        if sha256(migrated) == committed:
            return True
    return False


def added_example_bytes(decl):
    if decl["changes_v0_bytes"] or not decl["v3_shipped_dirs"]:
        return 0
    return sum(
        (EXAMPLES / release / name).stat().st_size
        for release in RELEASES
        for name in RELEASE_FILES
    )


def report(out_dir, candidate, criterion, unit, value, command):
    body = {
        "schema": SCHEMA,
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": unit,
        "command": command,
        "exit": 0,
    }
    path = out_dir / ("%s-%s.json" % (candidate, criterion))
    path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    command = "python3 %s --output-dir %s" % (Path(__file__).resolve(), out.resolve())
    summary = {"tuples": tuple_table(), "results": {}}
    for candidate, decl in CANDIDATES.items():
        admitted, checked = emitted_values_admitted(decl)
        values = {
            "emitted-values-admitted": ("boolean", admitted),
            "published-release-bytes-unchanged": ("boolean", published_bytes_unchanged(decl)),
            "v3-schema-files-declared": ("boolean", bool(decl["v3_files"])),
            "shipped-v3-ledgers": ("count", len(decl["v3_shipped_dirs"])),
            "legacy-v2-read-path": ("boolean", bool(decl["keeps_v2_read"])),
            "added-example-bytes": ("bytes", added_example_bytes(decl)),
        }
        summary["results"][candidate] = {k: v for k, (_, v) in values.items()}
        summary["results"][candidate]["documents_checked"] = checked
        for criterion, (unit, value) in values.items():
            report(out, candidate, criterion, unit, value, command)
    (out / "selection-observations.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(summary["results"], indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
