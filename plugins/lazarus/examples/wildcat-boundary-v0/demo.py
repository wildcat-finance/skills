#!/usr/bin/env python3
"""Verify the Wildcat boundary releases, refuse altered bytes, check committed digests.

Three subcommands, run from anywhere with no network:

    python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py mutations
    python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py verify-releases
    python3 plugins/lazarus/examples/wildcat-boundary-v0/demo.py verify-preserved

``mutations`` and ``verify-releases`` read the two Lazarus release trees named
by ``WILDCAT_BOUNDARY_V1_RELEASE`` and ``WILDCAT_BOUNDARY_V2_RELEASE`` and
write nothing inside either. ``mutations`` copies each fixture into a fresh
temporary directory, changes one storage value, one code byte and one receipt
byte in separate copies, and requires Lazarus ``verify`` to refuse each copy
twice: with the manifest untouched, where the component digest check refuses
it, and with the manifest re-sealed to the altered bytes, where the storage
proof, code hash or receipts-root check refuses it. It exits 0 only when all
twelve refusals name the expected check and both unchanged fixtures still
verify to the committed capture records. ``verify-releases`` runs Lazarus
``verify-release`` and Ariadne ``verify`` on both trees and holds each tree's
release document and statement to the committed copies. ``verify-preserved``
reads only the committed files beside this script and refuses an edited
digest, count or root. No tar is read, so each whole-archive digest is held
between the archive inventory and the handoff record that repeats it. It needs
neither variable; one that is set is read only to refuse a report path inside
the tree it names.

Each subcommand takes ``--report PATH`` to write its observations as JSON to a
path that must not exist yet, and refuses a path inside a release tree. Every
subprocess runs a pinned argument list without a shell. Nothing here proves
canonical-chain membership or provider independence; those claims stay false
in every record this example reads.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[1]
REPOSITORY = PLUGIN.parents[1]
LAZARUS = PLUGIN / "scripts" / "lazarus.py"
ARIADNE = REPOSITORY / "plugins" / "ariadne" / "scripts" / "ariadne.py"
if str(PLUGIN / "scripts") not in sys.path:
    sys.path.insert(0, str(PLUGIN / "scripts"))

from lazarus_lib.binding import CHECKS, IN_TOTO_STATEMENT_TYPE, STATE_FIXTURE_TYPE_V2  # noqa: E402
from lazarus_lib.canonical import dumps, loads  # noqa: E402
from lazarus_lib.manifest import fixture_digest  # noqa: E402
from lazarus_lib.release import release_digest  # noqa: E402

GENERATIONS = ("v1", "v2")
RELEASE_VARIABLES = {
    "v1": "WILDCAT_BOUNDARY_V1_RELEASE",
    "v2": "WILDCAT_BOUNDARY_V2_RELEASE",
}
REPORT_SCHEMA = "wildcat-boundary-demo-report/v1"
CAPTURE_RECORD_SCHEMA = "wildcat-boundary-capture-record/v1"
ARCHIVES_SCHEMA = "wildcat-boundary-archives/v1"
HANDOFF_SCHEMA = "wildcat-boundary-handoff/v1"
PLAN_FORMAT = "alexandria-capture-plan/v1"
EVIDENCE_KEYS = ("proof_backed", "header_bound", "recorded_rpc", "receipt_trie_proved")
RELEASE_ENTRIES = ("release.json", "statement.json", "fixture")
SUBPROCESS_TIMEOUT_SECONDS = 1800
MUTATIONS = ("storage-value", "code-byte", "receipt-byte")
# What Lazarus says when each altered copy is refused. With the manifest
# untouched the component digest check speaks first; re-sealed, the check
# that reads the altered bytes speaks. Either phrase in a pair is that check.
EXPECTED_REFUSALS = {
    ("storage-value", "untouched"): (
        "component-digest-mismatch", ("component digest mismatch: proofs.jsonl",),
    ),
    ("code-byte", "untouched"): (
        "component-digest-mismatch", ("component digest mismatch: proofs.jsonl",),
    ),
    ("receipt-byte", "untouched"): (
        "component-digest-mismatch", ("component digest mismatch: receipt-witness.json",),
    ),
    ("storage-value", "resealed"): (
        "storage-value-mismatch",
        (
            "storage value does not match proved slot",
            "proof-backed RPC storage value disagrees with proof",
        ),
    ),
    ("code-byte", "resealed"): (
        "code-hash-mismatch",
        (
            "captured code does not match the proved code hash",
            "proof-backed RPC code disagrees with proof",
        ),
    ),
    ("receipt-byte", "resealed"): (
        "receipts-root-mismatch", ("reconstructed receipt trie root mismatch",),
    ),
}
ESTABLISHES = {
    "mutations": (
        "For each estate, one storage value, one code byte and one receipt byte "
        "were each changed in a fresh copy of the release tree's fixture, and "
        "Lazarus verify refused every copy with the manifest untouched and again "
        "with the manifest re-sealed to the altered bytes, while an unchanged "
        "copy verified to the committed capture record's fixture digest."
    ),
    "verify-releases": (
        "Lazarus verify-release and Ariadne verify exited 0 on each release "
        "tree, and the tree's release document and statement are byte-identical "
        "to the committed copies."
    ),
    "verify-preserved": (
        "The committed capture records, statements, release documents, "
        "Alexandria plans, archive inventory and handoff record agree with one "
        "another on every digest, byte count, evidence count, block and root "
        "they share, and the recorded manifest and release identities recompute "
        "from their fields."
    ),
}
DOES_NOT_ESTABLISH = (
    "canonical-chain membership, provider independence, a value the map marks "
    "unsupported, or that any external archive still holds these bytes; "
    "verify-preserved reads no fixture byte and reruns no proof check"
)


class Refusal(Exception):
    """A precondition failed before any check ran."""


class CheckFailure(Exception):
    """A check ran and did not pass."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _refuse_constant(token: str):
    raise ValueError(f"non-finite number {token}")


def parse_json(data: bytes, label: str):
    try:
        return json.loads(data.decode("utf-8"), parse_constant=_refuse_constant)
    except (UnicodeDecodeError, ValueError) as exc:
        raise CheckFailure(f"{label} is not finite JSON: {exc}") from exc


def whole(value, label: str) -> int:
    """An integer that arrived as an integer: no boolean, float or string."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CheckFailure(f"{label} must be a non-negative whole number")
    return value


def hex_digest(value, label: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise CheckFailure(f"{label} must be a lowercase SHA-256 hex digest")
    return value


def regular_file(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise Refusal(f"{label} is a symlink")
    if not path.is_file():
        raise Refusal(f"{label} is not a regular file")
    return path


def real_directory(path: Path, label: str) -> Path:
    if path.is_symlink():
        raise Refusal(f"{label} is a symlink")
    if not path.is_dir():
        raise Refusal(f"{label} is not a directory")
    return path


def release_tree(generation: str, environment) -> Path:
    """The release tree a variable names, checked before anything reads it."""
    variable = RELEASE_VARIABLES[generation]
    value = environment.get(variable, "")
    if not value:
        raise Refusal(f"environment variable {variable} is unset")
    tree = real_directory(Path(value), f"{variable} release tree")
    for name in RELEASE_ENTRIES:
        entry = tree / name
        if entry.is_symlink():
            raise Refusal(f"{variable} release tree entry {name} is a symlink")
        if not entry.exists():
            raise Refusal(f"{variable} release tree has no {name}")
    real_directory(tree / "fixture", f"{variable} fixture")
    for entry in (tree / "fixture").iterdir():
        if entry.is_symlink():
            raise Refusal(f"{variable} fixture entry {entry.name} is a symlink")
    return tree


def fresh_report_path(raw: str | None, trees) -> Path | None:
    """A report path that does not exist and sits inside no release tree."""
    if raw is None:
        return None
    path = Path(raw)
    if path.is_symlink():
        raise Refusal("report path is a symlink")
    if path.exists():
        raise Refusal("report path already exists")
    parent = path.absolute().parent
    if not parent.is_dir():
        raise Refusal("report path has no parent directory")
    resolved = parent.resolve()
    for tree in trees:
        root = tree.resolve()
        if resolved == root or root in resolved.parents:
            raise Refusal("report path sits inside a release tree")
    return path


def write_report(path: Path | None, subcommand: str, observations, result: str, code: int):
    if path is None:
        return
    body = {
        "schema": REPORT_SCHEMA,
        "subcommand": subcommand,
        "result": result,
        "exit": code,
        "observations": observations,
        "establishes": ESTABLISHES[subcommand] if result == "pass" else "nothing; a check failed",
        "does_not_establish": DOES_NOT_ESTABLISH,
    }
    with open(path, "xb") as handle:
        handle.write(json.dumps(body, indent=1, sort_keys=True).encode("utf-8") + b"\n")


def run(argv) -> subprocess.CompletedProcess:
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.run(
        [str(item) for item in argv], capture_output=True, text=True, check=False,
        env=environment, timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )


def verify_fixture(path: Path):
    """Lazarus verify on one directory: the exit status and its last stderr line."""
    completed = run([sys.executable, LAZARUS, "verify", path])
    lines = completed.stderr.strip().splitlines()
    return completed.returncode, (lines[-1] if lines else "")


def emit(event: str, **fields) -> None:
    print(" ".join([event] + [f"{key}={value}" for key, value in fields.items()]))


# --- mutations ----------------------------------------------------------------


def _rewrite_first_proof_record(copy: Path, predicate, change):
    """Change one field of the first proof record ``predicate`` accepts.

    Records stay in Lazarus's canonical encoding, so the file differs from the
    original by the changed field alone.
    """
    path = copy / "proofs.jsonl"
    lines = path.read_bytes().split(b"\n")
    for index, line in enumerate(lines):
        if not line:
            continue
        record = loads(line)
        if predicate(record):
            detail = change(record)
            lines[index] = dumps(record)
            path.write_bytes(b"\n".join(lines))
            return detail
    raise CheckFailure("no proof record in the fixture carries the field to change")


def _flip_last_nibble(value: str) -> str:
    return value[:-1] + ("0" if value[-1] != "0" else "1")


def change_storage_value(copy: Path) -> dict:
    def change(record):
        item = record["storage_proof"][0]
        before = item["value"]
        item["value"] = _flip_last_nibble(before)
        return {
            "component": "proofs.jsonl", "address": record["address"],
            "slot": item["key"], "before": before, "after": item["value"],
        }

    return _rewrite_first_proof_record(copy, lambda record: bool(record.get("storage_proof")), change)


def change_code_byte(copy: Path) -> dict:
    def change(record):
        code = record["code"]
        flipped = int(code[-2:], 16) ^ 0x01
        record["code"] = code[:-2] + f"{flipped:02x}"
        return {
            "component": "proofs.jsonl", "address": record["address"],
            "code_bytes": (len(code) - 2) // 2, "byte_index": (len(code) - 2) // 2 - 1,
            "before": code[-2:], "after": record["code"][-2:],
        }

    return _rewrite_first_proof_record(
        copy, lambda record: isinstance(record.get("code"), str) and record["code"] not in ("", "0x"), change,
    )


def change_receipt_byte(copy: Path) -> dict:
    path = copy / "receipt-witness.json"
    witness = loads(path.read_bytes())
    index = int(witness["target_receipt"]["transaction_index"], 16)
    receipt = witness["receipts"][index]
    before = receipt["cumulative_gas_used"]
    receipt["cumulative_gas_used"] = hex(int(before, 16) ^ 0x01)
    path.write_bytes(dumps(witness) + b"\n")
    return {
        "component": "receipt-witness.json", "transaction_index": index,
        "field": "cumulative_gas_used", "before": before, "after": receipt["cumulative_gas_used"],
    }


CHANGES = {
    "storage-value": change_storage_value,
    "code-byte": change_code_byte,
    "receipt-byte": change_receipt_byte,
}


def reseal_manifest(copy: Path, component: str) -> None:
    """Point the manifest at the altered component so only a proof check can refuse it."""
    path = copy / "manifest.json"
    manifest = loads(path.read_bytes())
    data = (copy / component).read_bytes()
    for entry in manifest["components"]:
        if entry["path"] == component:
            entry["bytes"] = len(data)
            entry["sha256"] = sha256_bytes(data)
    manifest["fixture_digest"] = fixture_digest(manifest)
    path.write_bytes(dumps(manifest) + b"\n")


def mutation_observations(fixture: Path, generation: str, expected_digest: str | None) -> dict:
    """Copy, alter and verify; every copy lives in a temporary directory of its own."""
    work = Path(tempfile.mkdtemp(prefix=f"wildcat-boundary-{generation}-mutations-"))
    changes = []
    try:
        unchanged = work / "unchanged"
        shutil.copytree(fixture, unchanged, symlinks=True)
        code, last = verify_fixture(unchanged)
        digest = loads((unchanged / "manifest.json").read_bytes())["fixture_digest"]
        emit("unchanged", generation=generation, exit=code, fixture_digest=digest)
        if code != 0:
            raise CheckFailure(f"{generation}: the unchanged fixture does not verify: {last}")
        if expected_digest is not None and digest != expected_digest:
            raise CheckFailure(f"{generation}: the unchanged fixture is not the recorded one")
        shutil.rmtree(unchanged)
        for mutation in MUTATIONS:
            for manifest_state in ("untouched", "resealed"):
                copy = work / f"{mutation}-{manifest_state}"
                shutil.copytree(fixture, copy, symlinks=True)
                detail = CHANGES[mutation](copy)
                if manifest_state == "resealed":
                    reseal_manifest(copy, detail["component"])
                code, last = verify_fixture(copy)
                shutil.rmtree(copy)
                check, phrases = EXPECTED_REFUSALS[(mutation, manifest_state)]
                named = code != 0 and any(phrase in last for phrase in phrases)
                observation = {
                    "generation": generation, "change": mutation, "manifest": manifest_state,
                    "changed": detail, "exit": code, "refused": code != 0,
                    "check": check if named else "unexpected", "message": last,
                }
                changes.append(observation)
                emit(
                    "mutation", generation=generation, change=mutation, manifest=manifest_state,
                    exit=code, refused=str(code != 0).lower(), check=observation["check"],
                )
                if code == 0:
                    raise CheckFailure(f"{generation}: verify accepted the {mutation} copy with the manifest {manifest_state}")
                if not named:
                    raise CheckFailure(f"{generation}: the {mutation} copy was refused by an unexpected check: {last}")
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return {"generation": generation, "unchanged": {"exit": 0, "fixture_digest": digest}, "changes": changes}


def committed(example: Path, name: str) -> bytes:
    return regular_file(example / name, f"committed {name}").read_bytes()


def capture_record(example: Path, generation: str) -> dict:
    record = parse_json(committed(example, f"capture-{generation}.json"), f"capture-{generation}.json")
    if record.get("schema") != CAPTURE_RECORD_SCHEMA or record.get("generation") != generation:
        raise CheckFailure(f"capture-{generation}.json is not the {generation} capture record")
    return record


def cmd_mutations(args, environment) -> int:
    trees = {generation: release_tree(generation, environment) for generation in GENERATIONS}
    report = fresh_report_path(args.report, trees.values())
    observations = []
    result, code = "pass", 0
    try:
        for generation in GENERATIONS:
            expected = capture_record(HERE, generation)["fixture"]["fixture_digest"]
            observations.append(mutation_observations(trees[generation] / "fixture", generation, expected))
        refusals = sum(len(item["changes"]) for item in observations)
        emit("mutations", changes=refusals // 2, refusals=refusals, unchanged_verified=len(observations), result="pass")
    except CheckFailure as exc:
        result, code = "fail", 1
        print(f"demo: {exc}", file=sys.stderr)
    write_report(report, "mutations", observations, result, code)
    return code


# --- verify-releases ------------------------------------------------------------


def printed_field(stdout: str, key: str) -> str:
    for line in stdout.splitlines():
        if line.startswith(f"{key}: "):
            return line[len(key) + 2:].strip()
    return ""


def release_observation(generation: str, tree: Path, example: Path) -> dict:
    document = parse_json(committed(example, f"release-{generation}.json"), f"release-{generation}.json")
    for name, committed_name in (("release.json", f"release-{generation}.json"), ("statement.json", f"statement-{generation}.json")):
        if (tree / name).read_bytes() != committed(example, committed_name):
            raise CheckFailure(f"{generation}: the release tree's {name} differs from the committed {committed_name}")
    verified = run([sys.executable, LAZARUS, "verify-release", tree])
    observation = {
        "generation": generation,
        "verify_release_exit": verified.returncode,
        "release_digest": printed_field(verified.stdout, "release"),
        "fixture_digest": printed_field(verified.stdout, "fixture"),
    }
    emit("verify-release", generation=generation, exit=verified.returncode, release_digest=observation["release_digest"])
    if verified.returncode != 0:
        raise CheckFailure(f"{generation}: verify-release exited {verified.returncode}: {verified.stderr.strip()}")
    if observation["release_digest"] != document["release_digest"]:
        raise CheckFailure(f"{generation}: verify-release reports a release digest the committed document does not carry")
    if observation["fixture_digest"] != document["fixture"]["fixture_digest"]:
        raise CheckFailure(f"{generation}: verify-release reports a fixture digest the committed document does not carry")
    statement = run([sys.executable, ARIADNE, "verify", tree / "statement.json"])
    observation["ariadne_verify_exit"] = statement.returncode
    observation["statement_sha256"] = sha256_bytes((tree / "statement.json").read_bytes())
    emit("ariadne-verify", generation=generation, exit=statement.returncode)
    if statement.returncode != 0:
        raise CheckFailure(f"{generation}: ariadne verify exited {statement.returncode}: {statement.stderr.strip()}")
    return observation


def cmd_verify_releases(args, environment) -> int:
    trees = {generation: release_tree(generation, environment) for generation in GENERATIONS}
    report = fresh_report_path(args.report, trees.values())
    observations = []
    result, code = "pass", 0
    try:
        for generation in GENERATIONS:
            observations.append(release_observation(generation, trees[generation], HERE))
        emit("verify-releases", trees=len(observations), result="pass")
    except CheckFailure as exc:
        result, code = "fail", 1
        print(f"demo: {exc}", file=sys.stderr)
    write_report(report, "verify-releases", observations, result, code)
    return code


# --- verify-preserved -----------------------------------------------------------


def components_of(record: dict) -> dict:
    """Component path -> (bytes, sha256) from a capture record, manifest included."""
    entries = list(record["fixture"]["components"]) + [record["fixture"]["manifest"]]
    return {
        entry["path"]: (whole(entry["bytes"], f"{entry['path']} bytes"), hex_digest(entry["sha256"], f"{entry['path']} sha256"))
        for entry in entries
    }


def check_capture_record(record: dict, generation: str) -> dict:
    name = f"capture-{generation}.json"
    digest = hex_digest(record["fixture"]["fixture_digest"], f"{name} fixture digest")
    manifest = record["verify"]["manifest"]
    for label, value in (
        ("verify.fixture_digest", record["verify"]["fixture_digest"]),
        ("verify.manifest.fixture_digest", manifest["fixture_digest"]),
        ("capture.terminal_result.fixture_digest", record["capture"]["terminal_result"]["fixture_digest"]),
    ):
        if value != digest:
            raise CheckFailure(f"{name}: {label} differs from fixture.fixture_digest")
    if record["fixture"]["components"] != manifest["components"]:
        raise CheckFailure(f"{name}: fixture.components differ from the verified manifest's")
    counts = record["verify"]["evidence_counts"]
    if set(counts) != set(EVIDENCE_KEYS) or manifest["evidence_counts"] != counts:
        raise CheckFailure(f"{name}: evidence counts are not the four verified classes")
    for key in EVIDENCE_KEYS:
        whole(counts[key], f"{name} {key}")
    for entry in manifest["components"]:
        whole(entry["bytes"], f"{name} {entry['path']} bytes")
        hex_digest(entry["sha256"], f"{name} {entry['path']} sha256")
    if fixture_digest(manifest) != digest:
        raise CheckFailure(f"{name}: the recorded manifest does not recompute to fixture.fixture_digest")
    return {"generation": generation, "check": "capture-record", "file": name, "fixture_digest": digest}


def check_statement(example: Path, record: dict, generation: str, release: dict) -> dict:
    name = f"statement-{generation}.json"
    data = committed(example, name)
    digest = sha256_bytes(data)
    if digest != release["statement"]["sha256"]:
        raise CheckFailure(f"{name}: its SHA-256 is not the one release-{generation}.json records")
    statement = parse_json(data, name)
    if statement.get("_type") != IN_TOTO_STATEMENT_TYPE or statement.get("predicateType") != STATE_FIXTURE_TYPE_V2:
        raise CheckFailure(f"{name}: not an in-toto state-fixture/v2 statement")
    predicate = statement["predicate"]
    verify = record["verify"]
    if predicate["evidence"] != verify["evidence_counts"]:
        raise CheckFailure(f"{name}: evidence counts differ from the capture record's verify report")
    chain = predicate["chain"]
    expected_chain = {
        "chain_id": int(verify["manifest"]["chain_id"], 16),
        "block_number": int(verify["block_number"], 16),
        "block_hash": verify["block_hash"],
        "state_root": verify["state_root"],
        "receipts_root": verify["receipts_root"],
    }
    for key, value in expected_chain.items():
        if chain.get(key) != value:
            raise CheckFailure(f"{name}: chain.{key} differs from the capture record")
    components = components_of(record)
    del components["manifest.json"]
    listed = {
        subject["path"]: (whole(subject["bytes"], f"{name} {subject['path']} bytes"), subject["digest"]["sha256"])
        for subject in predicate["fixture_subjects"]
    }
    if listed != components:
        raise CheckFailure(f"{name}: fixture_subjects differ from the capture record's components")
    subject_digests = {subject["digest"]["sha256"] for subject in statement["subject"]}
    missing = {digest for _, digest in components.values()} - subject_digests
    if missing:
        raise CheckFailure(f"{name}: a component digest is not a subject of the statement")
    replay = predicate["replay"]
    if any(replay.get(key) is not False for key in ("reaches_network", "canonical_chain_claim", "provider_independence_claim")):
        raise CheckFailure(f"{name}: a replay claim is not false")
    return {"generation": generation, "check": "statement", "file": name, "sha256": digest}


def check_release_document(example: Path, record: dict, generation: str) -> dict:
    name = f"release-{generation}.json"
    release = parse_json(committed(example, name), name)
    if release["schema_version"] != 2 or release["statement"]["predicate_type"] != STATE_FIXTURE_TYPE_V2:
        raise CheckFailure(f"{name}: not a release-v2 over a state-fixture/v2 statement")
    if release["fixture"]["fixture_digest"] != record["fixture"]["fixture_digest"]:
        raise CheckFailure(f"{name}: fixture.fixture_digest differs from the capture record")
    verified = release["verified"]
    if verified["evidence_counts"] != record["verify"]["evidence_counts"]:
        raise CheckFailure(f"{name}: verified.evidence_counts differ from the capture record")
    if verified["block_hash"] != record["verify"]["block_hash"] or verified["receipts_root"] != record["verify"]["receipts_root"]:
        raise CheckFailure(f"{name}: verified block hash or receipts root differs from the capture record")
    if verified["canonical_chain_claim"] is not False:
        raise CheckFailure(f"{name}: canonical_chain_claim is not false")
    if list(release["binding"]["checks"]) != list(CHECKS):
        raise CheckFailure(f"{name}: binding.checks are not the eight release checks")
    if release_digest(release) != hex_digest(release["release_digest"], f"{name} release_digest"):
        raise CheckFailure(f"{name}: release_digest does not recompute from the document")
    return release, {"generation": generation, "check": "release-document", "file": name, "release_digest": release["release_digest"]}


def check_alexandria_plan(example: Path, record: dict, generation: str) -> dict:
    name = f"alexandria-plan-{generation}.json"
    plan = parse_json(committed(example, name), name)
    if plan.get("format") != PLAN_FORMAT or len(plan.get("captures", [])) != 1:
        raise CheckFailure(f"{name}: not one proof-backed-state capture plan")
    capture = plan["captures"][0]
    verify = record["verify"]
    if capture["evidence_class"] != "proof-backed-state":
        raise CheckFailure(f"{name}: evidence_class is not proof-backed-state")
    if capture["source"] != {"kind": "lazarus-fixture", "locator_class": "local-fixture", "reference": record["fixture"]["fixture_digest"]}:
        raise CheckFailure(f"{name}: source does not name the capture record's fixture digest")
    interval = capture["scope"]["interval"]
    if interval["block_hash"] != verify["block_hash"] or interval["block_number"] != str(int(verify["block_number"], 16)):
        raise CheckFailure(f"{name}: snapshot block differs from the capture record")
    if capture["chain"] != f"eip155:{int(verify['manifest']['chain_id'], 16)}":
        raise CheckFailure(f"{name}: chain differs from the capture record")
    if capture["scope"]["finality"] != "unknown" or capture["scope"]["kind"] != "subject-scoped":
        raise CheckFailure(f"{name}: scope is not an unknown-finality subject-scoped snapshot")
    paths = sorted(component["path"] for component in plan["components"])
    expected = sorted(f"fixture/{path}" for path in components_of(record))
    if paths != expected:
        raise CheckFailure(f"{name}: component paths are not the fixture's components and manifest")
    roles = {component["path"]: component["role"] for component in plan["components"]}
    if roles["fixture/manifest.json"] != "lazarus-manifest" or capture["component"] != next(
        component["name"] for component in plan["components"] if component["path"] == "fixture/manifest.json"
    ):
        raise CheckFailure(f"{name}: the capture does not name the manifest component")
    coverage = capture["coverage"]
    if whole(coverage["record_count"], f"{name} record_count") != len(record["fixture"]["components"]):
        raise CheckFailure(f"{name}: coverage record_count is not the component count")
    return {"generation": generation, "check": "alexandria-plan", "file": name, "subjects": len(capture["scope"]["subjects"])}


def check_archives(example: Path, records: dict, releases: dict, statements: dict) -> list:
    name = "archives.json"
    inventory = parse_json(committed(example, name), name)
    if inventory.get("schema") != ARCHIVES_SCHEMA:
        raise CheckFailure(f"{name}: schema is not {ARCHIVES_SCHEMA}")
    archives = inventory["archives"]
    seen = set()
    observations = []
    for archive in archives:
        generation = archive["generation"]
        record = records[generation]
        components = components_of(record)
        prefix = archive["name"].removesuffix(".tar")
        members = {
            member["path"]: (whole(member["bytes"], f"{name} {member['path']} bytes"), hex_digest(member["sha256"], f"{name} {member['path']} sha256"))
            for member in archive["members"]
        }
        if whole(archive["member_count"], f"{name} member_count") != len(members) or len(members) != len(archive["members"]):
            raise CheckFailure(f"{name}: {archive['name']} member_count disagrees with its member list")
        hex_digest(archive["sha256"], f"{name} {archive['name']} sha256")
        whole(archive["bytes"], f"{name} {archive['name']} bytes")
        if archive["fixture_digest"] != record["fixture"]["fixture_digest"]:
            raise CheckFailure(f"{name}: {archive['name']} names a fixture digest the capture record does not")
        if archive["contents"] == "lazarus-release":
            expected = {f"{prefix}/fixture/{path}": value for path, value in components.items()}
            expected[f"{prefix}/release.json"] = releases[generation]
            expected[f"{prefix}/statement.json"] = statements[generation]
            if archive["release_digest"] != releases[generation][2] or archive["statement_sha256"] != statements[generation][1]:
                raise CheckFailure(f"{name}: {archive['name']} names a release or statement identity the committed documents do not")
            expected = {path: value[:2] for path, value in expected.items()}
        elif archive["contents"] == "alexandria-release":
            expected = {}
            for value in components.values():
                size, digest = value
                expected[f"{prefix}/objects/sha256/{digest[:2]}/{digest}"] = (size, digest)
            manifest_path = f"{prefix}/manifest.json"
            if manifest_path not in members:
                raise CheckFailure(f"{name}: {archive['name']} has no manifest.json member")
            if archive["manifest_sha256"] != members[manifest_path][1]:
                raise CheckFailure(f"{name}: {archive['name']} manifest_sha256 is not its manifest member's digest")
            if archive["release_id"] != "sha256:" + hex_digest(archive["release_id"].removeprefix("sha256:"), f"{name} release_id"):
                raise CheckFailure(f"{name}: {archive['name']} release_id is not a sha256 identifier")
            expected[manifest_path] = members[manifest_path]
        else:
            raise CheckFailure(f"{name}: {archive['name']} has unknown contents")
        if members != expected:
            raise CheckFailure(f"{name}: {archive['name']} members differ from the committed digests")
        seen.add((generation, archive["contents"]))
        observations.append({"generation": generation, "check": "archive-inventory", "file": name, "archive": archive["name"], "members": len(members)})
    if seen != {(g, kind) for g in GENERATIONS for kind in ("lazarus-release", "alexandria-release")}:
        raise CheckFailure(f"{name}: not one Lazarus and one Alexandria archive per estate")
    return observations


def check_handoff(example: Path) -> list:
    """Hold handoff.json's archive rows to archives.json.

    verify-preserved reads no tar, so a whole-archive digest has nothing to
    recompute from; the handoff record repeats it, and the two committed
    copies hold each other. An edit to either is refused here.
    """
    name = "handoff.json"
    inventory_bytes = committed(example, "archives.json")
    archives = parse_json(inventory_bytes, "archives.json")["archives"]
    handoff = parse_json(committed(example, name), name)
    if handoff.get("schema") != HANDOFF_SCHEMA:
        raise CheckFailure(f"{name}: schema is not {HANDOFF_SCHEMA}")
    rows = handoff["archives"]
    if not isinstance(rows, list) or len(rows) != len(archives):
        raise CheckFailure(f"{name}: archive rows are not one per archives.json entry")
    observations = []
    for row, archive in zip(rows, archives):
        if row["name"] != archive["name"]:
            raise CheckFailure(f"{name}: archive rows are not in archives.json order")
        for key in ("generation", "contents"):
            if row[key] != archive[key]:
                raise CheckFailure(f"{name}: {row['name']} {key} differs from archives.json")
        for key, read in (("bytes", whole), ("member_count", whole), ("sha256", hex_digest)):
            if read(row[key], f"{name} {row['name']} {key}") != archive[key]:
                raise CheckFailure(f"{name}: {row['name']} {key} differs from archives.json")
        if not isinstance(row["proposed_source_id"], str) or not row["proposed_source_id"]:
            raise CheckFailure(f"{name}: {row['name']} has no proposed source id")
        observations.append({"generation": archive["generation"], "check": "handoff-record", "file": name, "archive": row["name"]})
    ids = [row["proposed_source_id"] for row in rows]
    if len(set(ids)) != len(ids) or handoff["proposed_source_ids"] != ids:
        raise CheckFailure(f"{name}: proposed_source_ids are not the archive rows' ids")
    if hex_digest(handoff["archives_json_sha256"], f"{name} archives_json_sha256") != sha256_bytes(inventory_bytes):
        raise CheckFailure(f"{name}: archives_json_sha256 is not the digest of archives.json")
    receipt = handoff["replication_receipt_sha256"]
    if receipt is None:
        reason = handoff.get("replication_receipt_reason")
        if not isinstance(reason, str) or not reason:
            raise CheckFailure(f"{name}: a null replication receipt needs its reason")
    else:
        hex_digest(receipt, f"{name} replication_receipt_sha256")
    return observations


def cmd_verify_preserved(args, environment) -> int:
    example = real_directory(Path(args.example) if args.example else HERE, "example directory")
    # Neither variable is required here, but a tree one names is still a tree
    # this script must not write into, so a set variable bounds the report path.
    named_trees = [Path(value) for value in (environment.get(v, "") for v in RELEASE_VARIABLES.values()) if value]
    report = fresh_report_path(args.report, named_trees)
    observations = []
    result, code = "pass", 0
    try:
        records, releases, statements = {}, {}, {}
        for generation in GENERATIONS:
            record = capture_record(example, generation)
            records[generation] = record
            observations.append(check_capture_record(record, generation))
            release, observation = check_release_document(example, record, generation)
            observations.append(observation)
            observations.append(check_statement(example, record, generation, release))
            observations.append(check_alexandria_plan(example, record, generation))
            release_bytes = committed(example, f"release-{generation}.json")
            statement_bytes = committed(example, f"statement-{generation}.json")
            releases[generation] = (len(release_bytes), sha256_bytes(release_bytes), release["release_digest"])
            statements[generation] = (len(statement_bytes), sha256_bytes(statement_bytes))
        observations.extend(check_archives(example, records, releases, statements))
        observations.extend(check_handoff(example))
        for observation in observations:
            emit("preserved", **{key: value for key, value in observation.items() if key != "check"}, check=observation["check"], result="pass")
        emit("verify-preserved", checks=len(observations), result="pass")
    except CheckFailure as exc:
        result, code = "fail", 1
        print(f"demo: {exc}", file=sys.stderr)
    write_report(report, "verify-preserved", observations, result, code)
    return code


# --- entry point ----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    subparsers = parser.add_subparsers(dest="subcommand", required=True)
    for name, handler in (
        ("mutations", cmd_mutations),
        ("verify-releases", cmd_verify_releases),
        ("verify-preserved", cmd_verify_preserved),
    ):
        sub = subparsers.add_parser(name)
        sub.add_argument("--report", help="write the observations as JSON to this path, which must not exist")
        if name == "verify-preserved":
            sub.add_argument("--example", help="check a copy of the example directory instead of this one")
        sub.set_defaults(handler=handler)
    return parser


def main(argv=None, environment=None) -> int:
    args = build_parser().parse_args(argv)
    environment = os.environ if environment is None else environment
    try:
        return args.handler(args, environment)
    except Refusal as exc:
        print(f"demo: refusing: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
