"""Build constructed fee specimens through the raw and canonical owners."""

from pathlib import Path
import shutil
import tempfile

from wildcat_fee_fixtures import VENUES, fee_raw_release
from wildcat_v3_public_fixtures import inventory, observation
from tabularium_lib import verifier
from tabularium_lib.wildcat_release import build_wildcat_canonical

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def build_fee_specimen(directory, venue):
    if venue not in VENUES:
        raise ValueError("unknown constructed fee generation")
    target = Path(directory) / "release"
    with tempfile.TemporaryDirectory(prefix="tabularium-constructed-fees-") as temporary:
        raw = fee_raw_release(Path(temporary).resolve(), venue)
        build_wildcat_canonical(raw, target, venue + "-constructed-fees-v0", "1.1.0")
    return observation(target)


def rebuild_fee_example(venue):
    import json
    published = EXAMPLES / (venue + "-fees-v0")
    expected = json.loads((published / "expected.json").read_bytes())
    with tempfile.TemporaryDirectory(prefix="tabularium-fees-rebuild-") as temporary:
        base = Path(temporary).resolve()
        actual = build_fee_specimen(base, venue)
        if actual != expected or inventory(base / "release") != inventory(published / "release"):
            raise ValueError("constructed fee specimen does not reproduce")
        for relative in expected["files"]:
            if (base / "release" / relative).read_bytes() != (published / "release" / relative).read_bytes():
                raise ValueError("constructed fee specimen bytes differ")
        moved = base / "moved"
        shutil.move(str(base / "release"), moved)
        for path in moved.rglob("*"):
            if path.is_file(): path.chmod(0o444)
        verifier.verify(moved / "coverage.json")
    return 0
