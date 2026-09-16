"""Public synthetic producer fixture; only admission commands are native evidence."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "skills/fiat/scripts"
sys.path.insert(0, str(SCRIPTS))
from checkpoint_authority.canonical import canonical
from checkpoint_authority.coverage import ApprovedRun
from checkpoint_authority.native import NativeInput, NativePin
from checkpoint_authority.native_io import NativeTool
from checkpoint_authority.signatures import b64

FIXTURES = SCRIPTS.parent / "checkpoint-authority/native-fixture"


def fixture():
    value = json.loads((FIXTURES / "fixture.json").read_bytes())
    for name, digest in (("checkpoint.zip", value["outer_sha256"]),
                         ("independent-public-key.gpg", value["public_sha256"])):
        assert hashlib.sha256((FIXTURES / name).read_bytes()).hexdigest() == digest
    return value


def approval(*, first_step=1):
    value = fixture()
    # This is a test issuer reference, not an enrollment in a production journal.
    row = {"key": {"format": "openpgp-v4", "algorithm": "openpgp", "fingerprint": value["fingerprint"],
            "public": b64((FIXTURES / "independent-public-key.gpg").read_bytes())},
        "enrollment": {"type": "key-enrollment", "sha256": "a" * 64},
        "actor_id": 17, "first_step": first_step, "last_step": 2}
    return ApprovedRun(value["anchor_sha256"], value["initial_base"],
                       value["start_commit"], (canonical(row),))


def request(attempt="fixture-attempt"):
    value = fixture()
    return NativeInput(attempt, "fixture-lease", "fixture-candidate", value["outer_sha256"],
        value["snapshot_id"], value["controller_manifest_sha256"], value["carrier_length"])


def pin(source):
    paths = [("python", sys.executable), *((name, shutil.which(name))
              for name in ("git", "gpg", "gpgconf"))]
    tools = []
    for name, path in paths:
        if path is None:
            raise RuntimeError("fixture native tool unavailable")
        path = Path(path).resolve(strict=True)
        tools.append(NativeTool(name, str(path), hashlib.sha256(path.read_bytes()).hexdigest()))
    return NativePin(Path(source).resolve(strict=True), tuple(tools))
