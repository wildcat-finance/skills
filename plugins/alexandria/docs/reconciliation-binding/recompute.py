"""Compare both preserved Wildcat staging trees with their reconciliation checkpoints."""

import argparse
import hashlib
import importlib.util
from pathlib import Path
import sys


PLUGIN = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PLUGIN / "scripts"))
from alexandria_lib.canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes  # noqa: E402
from alexandria_lib.errors import AlexandriaError  # noqa: E402
from alexandria_lib.interval import MAX_JOURNAL_BYTES, Staging, read_regular  # noqa: E402
from alexandria_lib.paths import read_confined_file  # noqa: E402


def recompute(version, staging, archive):
    example = PLUGIN / "examples" / f"wildcat-v{version}-interval-v0"
    spec = importlib.util.spec_from_file_location(f"wildcat_v{version}", example / "demo.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    manifest = demo._checked_manifest()
    archive_bytes = read_regular(archive, "preserved archive", manifest["archive"]["bytes"])
    if (
        len(archive_bytes) != manifest["archive"]["bytes"]
        or hashlib.sha256(archive_bytes).hexdigest() != manifest["archive"]["sha256"]
    ):
        raise AlexandriaError(f"Wildcat V{version} archive differs from its staging manifest")
    del archive_bytes
    verified = demo.verify_staging_tree(staging, manifest)
    plan = demo._read(example / "plan.json", "interval plan")
    store = Staging(staging, plan)
    state = store.committed()
    checkpoint_bytes = read_confined_file(
        staging, "reconciliation/checkpoint.json", "reconcile checkpoint",
        max_bytes=MAX_CONTROL_BYTES,
    )
    checkpoint = load_bytes(checkpoint_bytes, "reconcile checkpoint")
    if checkpoint.get("plan_sha256") != store.digest:
        raise AlexandriaError(f"Wildcat V{version} reconcile checkpoint names another plan")
    digest = hashlib.sha256(canonical_bytes(state))
    for name in sorted(store.journal_names):
        data = read_confined_file(
            store.journals, f"{name}.jsonl", f"journal {name}", max_bytes=MAX_JOURNAL_BYTES,
        )
        digest.update(canonical_bytes({
            "name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        }))
    actual = digest.hexdigest()
    recorded = checkpoint.get("staging_sha256")
    return {
        "archive": manifest["archive"],
        "checkpoint_sha256": hashlib.sha256(checkpoint_bytes).hexdigest(),
        "journal_count": len(store.journal_names),
        "plan_sha256": store.digest,
        "recomputed_staging_sha256": actual,
        "recorded_staging_sha256": recorded,
        "staging": verified,
        "status": "absent" if recorded is None else "matched" if recorded == actual else "mismatch",
        "venue": f"wildcat-v{version}",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for version in (1, 2):
        parser.add_argument(f"--v{version}-staging", type=Path, required=True)
        parser.add_argument(f"--v{version}-archive", type=Path, required=True)
    args = parser.parse_args()
    try:
        records = [recompute(version, getattr(args, f"v{version}_staging"),
                             getattr(args, f"v{version}_archive")) for version in (1, 2)]
        result = {"format": "alexandria-wildcat-reconciliation-recomputation/v1", "records": records}
        sys.stdout.buffer.write(canonical_bytes(result))
        return int(any(record["status"] == "mismatch" for record in records))
    except (AlexandriaError, OSError) as error:
        print(f"wildcat-reconciliation: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
