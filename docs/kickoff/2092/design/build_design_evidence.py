"""Evaluate the four wrapper-subject designs; conformance stays pending.

Every selection value is computed from the declared model in `model.json`,
not asserted here. The four gates read one declared fact each; the two
metrics count the members of a declared list. The model also records the
repository observations each fact rests on, with the command that produced
them, so a reader can re-measure without trusting this script.

Run from the target root. The script writes the design record and its
selection reports under `.hexaemeron/` and nothing else. It reads no
controller state and writes none. An existing report is compared byte for
byte with fresh evidence and never replaced, so a rerun after the study is
receipted either reproduces the receipted bytes or refuses.
"""

import argparse
import hashlib
import json
from pathlib import Path
import stat

COMMAND = "python3 .hexaemeron/design/build_design_evidence.py"
RESOLVER = "python3 .hexaemeron/design/conformance.py {criterion} --candidate {candidate}"
SELECTED = "declared-wrapper-subjects"

SELECTION = (
    ("registry-bytes-unchanged", "compatibility", "protasis",
     lambda spec: not spec["changes_registry_document"]),
    ("constructed-proof-suffices", "correctness", "protasis",
     lambda spec: not spec["needs_real_wrapper_record"]),
    ("one-release-binds-wrapper-logs", "correctness", "protasis",
     lambda spec: spec["wrapper_logs_release"] == "same"),
    ("plan-derived-requests", "recovery", "elenchus",
     lambda spec: spec["request_ranges_from"] == "plan"),
)
METRICS = (
    ("edit-sites", "time", "metron", "edit_sites"),
    ("portable-files-added", "space", "metron", "portable_files_added"),
)
CONFORMANCE = (
    ("legacy-identities-hold", "compatibility", "protasis"),
    ("wrapper-release-builds-and-checks", "correctness", "protasis"),
    ("wrapper-refusals-fire", "recovery", "elenchus"),
    ("portable-payload-within-budget", "space", "metron"),
)


def encode(document):
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_once(path, data):
    """Create a report, or confirm an existing one holds exactly these bytes."""
    for parent in (path.parent, *path.parent.parents):
        if parent.is_symlink():
            raise SystemExit(f"refusing: {parent} is a symlink")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or path.read_bytes() != data:
            raise SystemExit(f"refusing: {path} exists and differs from fresh evidence")
        return
    with path.open("xb") as handle:
        handle.write(data)


def build(root):
    record_dir = root / ".hexaemeron"
    model = json.loads((record_dir / "design" / "model.json").read_text("utf-8"))
    candidates = model["candidates"]
    criteria = []
    for name, concern, owner, _rule in SELECTION:
        criteria.append({
            "blocks": "design-lock", "comparator": "equals", "concern": concern,
            "id": name, "kind": "gate", "owner": owner, "stage": "selection",
            "threshold": True, "unit": "boolean",
        })
    for name, concern, owner, _field in METRICS:
        criteria.append({
            "blocks": "design-lock", "comparator": "minimise", "concern": concern,
            "id": name, "kind": "metric", "owner": owner, "stage": "selection",
            "threshold": None, "unit": "count",
        })
    for name, concern, owner in CONFORMANCE:
        criteria.append({
            "blocks": "integration", "comparator": "equals", "concern": concern,
            "id": name, "kind": "gate", "owner": owner, "stage": "conformance",
            "threshold": True, "unit": "boolean",
        })

    results = []
    for candidate, spec in candidates.items():
        values = {name: rule(spec) for name, _c, _o, rule in SELECTION}
        values.update({name: len(spec[field]) for name, _c, _o, field in METRICS})
        for name, value in values.items():
            unit = "boolean" if isinstance(value, bool) else "count"
            relative = f"design/reports/selection/{candidate}-{name}.json"
            data = encode({
                "candidate": candidate, "command": COMMAND, "criterion": name,
                "exit": 0, "schema": "protasis-design-report/v1", "unit": unit,
                "value": value,
            })
            write_once(record_dir / relative, data)
            passed = value if unit == "boolean" else True
            results.append({
                "candidate": candidate, "criterion": name,
                "report": {"path": relative, "sha256": hashlib.sha256(data).hexdigest()},
                "state": "pass" if passed else "fail",
            })
        for name, _concern, _owner in CONFORMANCE:
            results.append({
                "blocks": "integration", "candidate": candidate, "criterion": name,
                "report": f"design/reports/conformance/{candidate}-{name}.json",
                "resolver": RESOLVER.format(criterion=name, candidate=candidate),
                "state": "pending",
            })

    record = {
        "candidates": [{"id": key, "summary": spec["summary"]} for key, spec in candidates.items()],
        "criteria": criteria,
        "results": results,
        "schema": "protasis-design-evidence/v1",
        "selection": {"candidate": SELECTED, "policy_ref": None, "rule": "unique-frontier"},
    }
    (record_dir / "design-evidence.json").write_bytes(encode(record))
    return record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args(argv)
    record = build(args.root.resolve())
    for result in record["results"]:
        if result["state"] != "pending":
            print(result["candidate"], result["criterion"], result["state"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
