#!/usr/bin/env python3
"""Regenerate or check the released interoperability corpus and the release manifest.

`--write` derives the consumer bundle from the already committed positive
history without signing anything new, records the declared hostile release
cases, and then writes the interoperability manifest, the release manifest and
the consumer lock example in that order. It finishes by running every declared
hostile case against the finished tree and refusing a code that disagrees.
`--check` recomputes all six artefacts and compares their exact bytes.
"""
import ast
import base64
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins/hexaemeron/skills/fiat/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from checkpoint_authority import demo, release, verifier
from checkpoint_authority.canonical import canonical, digest
from checkpoint_authority.release_conformance import BUNDLE_FILES, FILES, MANIFEST

CRITERION = "released-interoperability"
SCHEMA = "checkpoint-authority-interoperability-corpus/v1"
CASE_MODULES = (
    ("test_checkpoint_authority_release",
     "plugins/hexaemeron/tests/test_checkpoint_authority_release.py"),
    ("test_checkpoint_authority_release_conformance",
     "plugins/hexaemeron/tests/test_checkpoint_authority_release_conformance.py"),
    ("test_checkpoint_network", "plugins/hexaemeron/tests/test_checkpoint_network.py"),
)
HOSTILE_CASES = (
    {"id": "mutable-authority-branch", "kind": "replace", "section": "authority",
     "field": "source_commit", "value": "main", "code": "mutable-source-reference"},
    {"id": "mutable-native-tag", "kind": "replace", "section": "native",
     "field": "source_commit", "value": "latest", "code": "mutable-source-reference"},
    {"id": "stale-release-manifest", "kind": "replace", "section": "authority",
     "field": "release_manifest_sha256", "value": "0" * 64, "code": "release-manifest-mismatch"},
    {"id": "mixed-artifact-component", "kind": "replace", "section": "authority",
     "field": "artifact_sha256", "value": "1" * 64, "code": "mixed-components"},
    {"id": "mixed-schema-set", "kind": "replace", "section": "authority",
     "field": "schema_set_sha256", "value": "2" * 64, "code": "mixed-components"},
    {"id": "mixed-verifier", "kind": "replace", "section": "authority",
     "field": "verifier_sha256", "value": "3" * 64, "code": "mixed-components"},
    {"id": "mixed-fixture-corpus", "kind": "replace", "section": "authority",
     "field": "fixture_corpus_sha256", "value": "4" * 64, "code": "mixed-components"},
    {"id": "unsupported-native-executable", "kind": "replace", "section": "native",
     "field": "executable_sha256", "value": "5" * 64, "code": "unsupported-native-pin"},
    {"id": "unsupported-native-profile", "kind": "replace", "section": "native",
     "field": "profile", "value": "native-0000000-openpgp-v1", "code": "unsupported-native-pin"},
    {"id": "unsupported-python-pin", "kind": "replace", "section": "tools",
     "field": "python", "value": "3.0.0", "code": "unsupported-python-pin"},
    {"id": "missing-authority-section", "kind": "remove", "section": None,
     "field": "authority", "value": None, "code": "lock-fields"},
    {"id": "extra-lock-field", "kind": "add", "section": None,
     "field": "trusted_after_all", "value": True, "code": "lock-fields"},
    {"id": "wrong-lock-schema", "kind": "replace", "section": None,
     "field": "schema", "value": "checkpoint-authority-protocol-lock/v2", "code": "lock-fields"},
    {"id": "wrong-protocol", "kind": "replace", "section": None,
     "field": "protocol", "value": "checkpoint-authority/v2", "code": "lock-fields"},
    {"id": "foreign-authority-commit", "kind": "replace", "section": "authority",
     "field": "source_commit", "value": "f" * 40, "code": "source-commit-mismatch"},
    {"id": "oversized-lock", "kind": "pad", "section": None, "field": "padding",
     "value": 17000, "code": "lock-limit"},
    {"id": "not-json", "kind": "bytes", "section": None, "field": "document",
     "value": "not a lock", "code": "invalid-json"},
)
"""One typed change each; `bytes` replaces the document and `pad` oversizes it."""


def hostile_cases():
    """The declared table plus the tool pin, whose valid shape comes from the tool profile."""
    profile = json.loads((ROOT / release.CORPUS / "tool-profile.json").read_bytes())
    version = profile["cosign"]["version"].split(".")
    raised = ".".join([str(int(version[0]) + 1), *version[1:]])
    return (*HOSTILE_CASES,
            {"id": "unsupported-cosign-pin", "kind": "replace", "section": "tools",
             "field": "cosign", "value": {"version": raised, "assets": profile["cosign"]["assets"]},
             "code": "unsupported-tool-pin"})


def _b64(text):
    return base64.b64decode(text.encode("ascii"), validate=True)


def _compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _indented(value):
    return (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()


def cases():
    found = []
    for module, path in CASE_MODULES:
        tree = ast.parse((ROOT / path).read_bytes())
        found.extend(module + "." + node.name + "." + function.name for node in tree.body
                     if isinstance(node, ast.ClassDef) for function in node.body
                     if isinstance(function, ast.FunctionDef) and function.name.startswith("test_"))
    return sorted(found)


def bundle():
    """Re-encode the committed history into the released consumer shapes; nothing is signed."""
    import checkpoint_authority_replay_fixture as fixture
    from test_checkpoint_authority_records import tools as pinned_tools
    history = fixture.load_history()
    expected = history["expected"]
    reader = fixture.replay_history(history, pinned_tools(), with_freshness=True)
    presence = {(sha, role): True for sha, _ in reader.copies
                for role in ("primary", "recovery")}
    result = reader.finish(presence=presence)
    lines = b"".join(_b64(text) + b"\n" for text in history["envelopes"])
    observations = sorted(({"sha256": sha, "role": role, "present": True}
                           for sha, role in presence),
                          key=lambda row: (row["sha256"], row["role"]))
    written = {
        demo.HISTORY: lines,
        demo.BOOTSTRAP: _compact({"schema": "checkpoint-authority-bootstrap/v1",
                                  **{key: history["bootstrap"][key] for key in
                                     ("environment", "service", "repository_id", "run_id", "roots")}}),
        demo.NATIVE: _compact({"schema": "checkpoint-authority-native-evidence/v1",
                               "results": [{"output_sha256": key, "result": row["result"],
                                            "producer": row["producer"]}
                                           for key, row in sorted(history["native"].items())]}),
        demo.FRESHNESS: _compact({"schema": "checkpoint-authority-freshness/v1",
                                  "challenge": history["freshness"]["challenge"],
                                  "now": history["freshness"]["now"],
                                  "policy_count": expected["policy_history"]["count"],
                                  "policy_tail": expected["policy_history"]["tail"],
                                  "decision_count": expected["decisions"]["count"],
                                  "decision_tail": expected["decisions"]["tail"]}),
        demo.PRESENCE: _compact({"schema": "checkpoint-authority-presence/v1",
                                 "observations": observations}),
        demo.EXPECTED: _compact({
            "schema": "checkpoint-authority-demonstration-expected/v1",
            "history_sha256": digest(lines), "records": result["records"], "bytes": result["bytes"],
            "head_sha256": result["head_sha256"], "accepted": len(result["accepted"]),
            "eligible": sum(row["current_eligibility"] == "eligible" for row in result["accepted"]),
            "historical_permits": result["historical_permits"],
            "result_sha256": digest(canonical(result, limit=verifier.LIMITS["output_bytes"]))}),
        demo.HOSTILE: _compact({"schema": "checkpoint-authority-release-hostile/v1",
                                "cases": [dict(case) for case in hostile_cases()]}),
    }
    return written


def manifest():
    return {"schema": SCHEMA, "criterion": CRITERION, "cases": cases(),
            "files": [{"path": path, "sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest()}
                      for path in FILES]}


def artefacts():
    """Every generated byte string keyed by its repository-relative path, in write order."""
    written = dict(bundle())
    for path, data in written.items():
        (ROOT / path).write_bytes(data)
    written[MANIFEST] = _compact(manifest())
    (ROOT / MANIFEST).write_bytes(written[MANIFEST])
    built = release.build(ROOT)
    written[release.MANIFEST] = release.encode(built)
    (ROOT / release.MANIFEST).write_bytes(written[release.MANIFEST])
    written[release.LOCK_EXAMPLE] = _indented(
        release.lock_example(written[release.MANIFEST], built))
    (ROOT / release.LOCK_EXAMPLE).write_bytes(written[release.LOCK_EXAMPLE])
    return written


def write():
    original = {path: (ROOT / path).read_bytes() if (ROOT / path).is_file() else None
                for path in (*BUNDLE_FILES, MANIFEST, release.MANIFEST, release.LOCK_EXAMPLE)}
    try:
        written = artefacts()
        rows = demo.hostile(ROOT, written[release.LOCK_EXAMPLE])
    except BaseException:
        for path, data in original.items():
            if data is None:
                (ROOT / path).unlink(missing_ok=True)
            else:
                (ROOT / path).write_bytes(data)
        raise
    print(json.dumps({"artefacts": len(written), "cases": len(manifest()["cases"]),
                      "files": len(FILES), "hostile_cases": len(rows),
                      "release_manifest_sha256": digest(written[release.MANIFEST])},
                     sort_keys=True))
    return 0


def recomputed():
    """Recompute every artefact from the committed tree without writing to it."""
    written = dict(bundle())
    written[MANIFEST] = _compact(manifest())
    built = release.build(ROOT)
    written[release.MANIFEST] = release.encode(built)
    written[release.LOCK_EXAMPLE] = _indented(
        release.lock_example((ROOT / release.MANIFEST).read_bytes(), built))
    return written


def check():
    rebuilt = recomputed()
    drift = sorted(path for path, data in rebuilt.items()
                   if not (ROOT / path).is_file() or (ROOT / path).read_bytes() != data)
    if drift:
        raise SystemExit("released interoperability corpus drift: " + " ".join(drift))
    return 0


if __name__ == "__main__":
    if sys.argv[1:] == ["--write"]:
        raise SystemExit(write())
    if sys.argv[1:] == ["--check"]:
        raise SystemExit(check())
    raise SystemExit("use --check or --write")
