"""Reproduce labelled public specimens through the native release owners."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import shutil
import tempfile

if __package__:
    from .test_wildcat_v3_release import constructed_release
    from .wildcat_v3_fixtures import ACCOUNT, OTHER, log
else:
    from test_wildcat_v3_release import constructed_release
    from wildcat_v3_fixtures import ACCOUNT, OTHER, log

from tabularium_lib.core import canonical_json
from tabularium_lib import verifier
from tabularium_lib.wildcat_release import build_wildcat_canonical


VENUES = ("wildcat-v1", "wildcat-v2")
ROOTS = ("release", "registry-context/release")
EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


def release_id(venue, registry=False):
    """Return the fixed release name, including its constructed qualification."""
    if venue not in VENUES:
        raise ValueError("unknown public Wildcat specimen generation")
    return venue + ("-constructed-registry-context-v0" if registry else "-constructed-native-v0")


def build_main_release(base, venue, release_name):
    """Build into an absent root and discard the original synthetic inputs."""
    if venue not in VENUES:
        raise ValueError("unknown public Wildcat specimen generation")

    def add_unsupported(document, journal, plan):
        response = json.loads(journal["records"][0]["response"])
        raws = response["result"]
        raws.extend((
            log("Approval(address,address,uint256)", (ACCOUNT, OTHER), (9,), index=len(raws)),
            log("Unrecognized(uint256)", data=(4,), index=len(raws) + 1),
        ))
        journal["records"][0]["response"] = canonical_json(response).decode()

    with tempfile.TemporaryDirectory(prefix="tabularium-constructed-source-") as temporary:
        raw = constructed_release(Path(temporary).resolve(), venue, add_unsupported)
        build_wildcat_canonical(raw, Path(base), release_name)
    coverage = Path(base) / "coverage.json"
    verifier.verify(coverage)
    return coverage


def inventory(root):
    """Hash every regular release file; verification checks closed membership."""
    verifier.verify(Path(root) / "coverage.json")
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            data = path.read_bytes()
            result[path.relative_to(root).as_posix()] = {"bytes": len(data), "sha256": sha256(data).hexdigest()}
    return result


def observation(root):
    """Project bounded identities and disposition counts from verified bytes."""
    root = Path(root)
    verified = verifier.verify(root / "coverage.json")
    source = json.loads((root / "source.json").read_bytes())
    rows = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
    return {
        "release": verified.release,
        "raw_release_id": source["raw_release"]["release_id"],
        "rows": verified.rows,
        "schema_version": verified.schema_version,
        "canonical_sha256": verified.sha256,
        "scope_kind": source["scope"]["kind"],
        "native_logs": len(source["dispositions"]),
        "dispositions": dict(sorted(Counter(row["disposition"] for row in source["dispositions"]).items())),
        "actions": dict(sorted(Counter(row["action"] for row in rows).items())),
        "files": inventory(root),
    }


def build_pair(directory, venue):
    """Build two independent closed roots below an existing fixture folder."""
    if __package__:
        from .wildcat_v3_registry_fixture import build_registry_release
    else:
        from wildcat_v3_registry_fixture import build_registry_release
    directory = Path(directory)
    build_main_release(directory / "release", venue, release_id(venue))
    registry_parent = directory / "registry-context"
    registry_parent.mkdir()
    build_registry_release(registry_parent / "release", venue, release_id(venue, True))
    return {name: observation(directory / name) for name in ROOTS}


def compare_pair(published, rebuilt):
    """Require all release files and their bytes to match the published roots."""
    result = {}
    for name in ROOTS:
        expected = inventory(Path(published) / name)
        actual = inventory(Path(rebuilt) / name)
        if actual != expected:
            raise ValueError("rebuilt %s differs from the public specimen" % name)
        for relative in expected:
            published_bytes = (Path(published) / name / relative).read_bytes()
            rebuilt_bytes = (Path(rebuilt) / name / relative).read_bytes()
            if published_bytes != rebuilt_bytes:
                raise ValueError("rebuilt %s/%s bytes differ" % (name, relative))
        result[name] = observation(Path(rebuilt) / name)
    return result


def rebuild_example(venue):
    """Rebuild fresh, compare every file, move both roots, then verify offline."""
    published = EXAMPLES / (venue + "-v0")
    expected = json.loads((published / "expected.json").read_bytes())
    with tempfile.TemporaryDirectory(prefix="tabularium-" + venue + "-") as temporary:
        base = Path(temporary).resolve()
        original = base / "original"
        original.mkdir()
        built = build_pair(original, venue)
        if built != expected:
            raise ValueError("fresh fixture identities differ from expected.json")
        result = compare_pair(published, original)
        moved = base / "moved"
        moved.mkdir()
        for index, name in enumerate(ROOTS):
            target = moved / str(index)
            shutil.move(str(original / name), target)
            for path in target.rglob("*"):
                if path.is_file():
                    path.chmod(0o444)
            verifier.verify(target / "coverage.json")
        shutil.rmtree(original)
        for index in range(len(ROOTS)):
            verifier.verify(moved / str(index) / "coverage.json")
        print(canonical_json({"event": "wildcat.specimen.reproduced", "venue": venue,
                              "roots": {name: {key: result[name][key] for key in
                                        ("release", "rows", "native_logs", "canonical_sha256")}
                                        for name in ROOTS}}).decode())
    return 0
