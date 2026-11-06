#!/usr/bin/env python3
"""Regenerate the replay corpus manifest, and on request the signed positive history.

`--write` and `--check` regenerate or compare the manifest from the declared
source owners. `--history` signs a fresh positive history and its recorded
hostile refusal codes with ephemeral keys; run it only when the fixture must
change, because every regeneration produces new signatures and new digests.
"""
import ast
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "plugins/hexaemeron/skills/fiat/scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from checkpoint_authority.replay_conformance import ARIADNE_MODULE, FILES, HISTORY, HOSTILE, MANIFEST


def cases(root):
    found = []
    for module, path in (("test_checkpoint_authority_replay", "plugins/hexaemeron/tests/test_checkpoint_authority_replay.py"),
                         ("test_checkpoint_authority_replay_conformance", "plugins/hexaemeron/tests/test_checkpoint_authority_replay_conformance.py"),
                         (ARIADNE_MODULE, "plugins/ariadne/tests/test_checkpoint_authority.py")):
        tree = ast.parse((root / path).read_bytes())
        found.extend(module + "." + cls.name + "." + func.name for cls in tree.body
            if isinstance(cls, ast.ClassDef) for func in cls.body
            if isinstance(func, ast.FunctionDef) and func.name.startswith("test_"))
    return sorted(found)


def value(root):
    return {"schema": "checkpoint-authority-replay-corpus/v1", "criterion": "authority-replay",
        "cases": cases(root), "files": [{"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()} for path in FILES]}


def history():
    import checkpoint_authority_replay_fixture as fixture
    fixture.Signer.setUpClass()
    try:
        signer = fixture.Signer()
        built = fixture.History(signer)
        receipt, acceptance_id = built.accept("released-1")
        built.permit(receipt, acceptance_id)
        exported = fixture.export(built)
        hostile = fixture.hostile_codes(exported, signer.tools)
        reader = fixture.replay_history(exported, signer.tools, with_freshness=True)
        rows = reader.finish(presence=built.presence(reader))["accepted"]
        assert [row["current_eligibility"] for row in rows] == ["eligible"], rows
    finally:
        fixture.Signer.tearDownClass()
    return exported, hostile


def encoded(payload):
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()


if __name__ == "__main__":
    if sys.argv[1:] == ["--history"]:
        positive, hostile = history()
        (ROOT / HISTORY).write_bytes(encoded(positive))
        (ROOT / HOSTILE).write_bytes(encoded(hostile))
        print(json.dumps({"envelopes": len(positive["envelopes"]), "history_bytes": (ROOT / HISTORY).stat().st_size,
                          "hostile_cases": len(hostile["cases"])}))
    elif sys.argv[1:] == ["--write"]:
        (ROOT / MANIFEST).write_bytes(encoded(value(ROOT)))
    elif sys.argv[1:] == ["--check"]:
        if (ROOT / MANIFEST).read_bytes() != encoded(value(ROOT)): raise SystemExit("replay corpus drift")
    else: raise SystemExit("use --check, --write or --history")
