#!/usr/bin/env python3
"""Regenerate only the native fixture manifest from its declared source owners."""
import ast
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "skills/fiat/scripts"))
from checkpoint_authority.native_conformance import FILES, MANIFEST


def value(root):
    cases = []
    for name in ("test_checkpoint_authority_native", "test_checkpoint_authority_native_conformance"):
        tree = ast.parse((root / ("plugins/hexaemeron/tests/" + name + ".py")).read_bytes())
        cases.extend(name + "." + cls.name + "." + func.name for cls in tree.body
            if isinstance(cls, ast.ClassDef) for func in cls.body if isinstance(func, ast.FunctionDef) and func.name.startswith("test_"))
    cases.extend(("native_integration.test_actual_sequence_covers_four_commits_from_public_only_trust",
                  "native_integration.test_latest_step_key_approval_cannot_authorize_older_signed_commits"))
    capability = json.loads((root / FILES[0]).read_bytes())
    cases.extend("test_hexctl_checkpoint_archive." + row["test"] for row in capability["fixtures"])
    return {"schema": "checkpoint-authority-native-corpus/v1", "criterion": "native-boundary-coverage",
        "cases": sorted(cases), "files": [{"path": path, "sha256": hashlib.sha256((root / path).read_bytes()).hexdigest()} for path in FILES]}


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[3]
    payload = json.dumps(value(root), sort_keys=True, separators=(",", ":")).encode()
    if sys.argv[1:] == ["--write"]: (root / MANIFEST).write_bytes(payload)
    elif sys.argv[1:] == ["--check"]:
        if (root / MANIFEST).read_bytes() != payload: raise SystemExit("native corpus drift")
    else: raise SystemExit("use --check or --write")
