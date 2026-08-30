#!/usr/bin/env python3
"""Validate the inert Wave mu fixture corpus without executing its contents."""

import argparse
import base64
import hashlib
import json
import os
import stat
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / "tests" / "fixtures" / "wave-mu-adversarial-corpus-v1"
DEFAULT_SCHEMA = ROOT / "schemas" / "wave-mu-fixture-contract-v1.schema.json"
EXPECTED_ROOT = "b6563135ebc5a7a874c22818b48a7414268ae9b62a0b7389238d72b95a7758be"
SOURCE_CATALOG_NAME = "source-catalog.json"
SOURCE_CATALOG_SHA256 = "3f26d7741d3204ae39d670f31ebb1b790c2154eb7347edf27ddd288e8032935c"
FIXTURE_IDS = frozenset(
    "AG-01 AG-02 AG-03 AG-04 AG-05 AG-06 CP-01 CP-02 CP-03 CP-04 CP-05 CP-06 "
    "FS-01 FS-02 FS-03 FS-04 FS-05 FS-06 JS-01 JS-02 JS-03 JS-04 JS-05 JS-06 "
    "LC-01 LC-02 LC-03 LC-04 LC-05 LC-06 MP-01 MP-02 MP-03 MP-04 MP-05 MP-06 "
    "PB-01 PB-02 PB-03 PB-04 PB-05 PB-06 RC-01 RC-02 RC-03 RC-04 RC-05 RC-06 RC-07 RC-08 "
    "VF-01 VF-02 VF-03 VF-04 VM-01 VM-02 VM-03 VM-04 VM-05 VM-06".split()
)
SUPPORT_SHA256 = {
    "README.md": "f35617a9e5912f8b54b323f3b6056999be9ed34cb8ca53fb1cd4f9be7245e369",
    "fixture-contract.schema.json": "1af15c0039194e43f47211cea6984da0aa077177d7d83521148d79530cf1c422",
    "corpus-manifest.json": "748406dd05c00a0acb1f019cb2665670b842cac5a00bb4ff17c354fc796b1e16",
    "validation.json": "02e40bf0f59f41a0050702e3977ae93c6b48dd9a2875ae20b2195cc49ebb50f7",
}
SIZE_LIMITS = {
    "README.md": 32_768,
    "fixture-contract.schema.json": 65_536,
    "corpus-manifest.json": 131_072,
    "validation.json": 65_536,
}
SOURCE_CATALOG_SIZE_LIMIT = 65_536
FIXTURE_SIZE_LIMIT = 16_384
HEX64 = frozenset("0123456789abcdef")
EVIDENCE_REGISTRY = {
    "EV-01": "source_and_issue_manifest",
    "EV-02": "corpus_manifest",
    "EV-03": "jobspec_packet",
    "EV-04": "launch_receipt",
    "EV-05": "guest_image_inventory",
    "EV-06": "host_isolation_record",
    "EV-07": "model_proxy_record",
    "EV-08": "artifact_gate_record",
    "EV-09": "clean_verifier_record",
    "EV-10": "fiat_transition_record",
    "EV-11": "continuation_state_inventory",
    "EV-12": "cleanup_record",
    "EV-13": "threat_coverage_matrix",
    "EV-14": "independent_review_record",
    "EV-15": "approval_packet",
    "EV-16": "publisher_record",
    "EV-17": "deferred_delivery_receipt",
}


class ValidationFailure(Exception):
    """A named, bounded corpus-validation failure."""

    def __init__(self, code, detail):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def is_hex_digest(value):
    return isinstance(value, str) and len(value) == 64 and set(value) <= HEX64


def canonical_json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")


def is_canonical_json(data, value):
    """The frozen corpus uses canonical UTF-8 JSON followed by one LF."""
    return data == canonical_json_bytes(value) + b"\n"


def no_duplicate_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate key: {key}")
        result[key] = value
    return result


def open_directory(path):
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:
        raise ValidationFailure("no-follow-unavailable", str(path))
    flags = os.O_RDONLY | nofollow | directory | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
    except (FileNotFoundError, NotADirectoryError) as exc:
        raise ValidationFailure("missing-corpus", str(path)) from exc
    except OSError as exc:
        raise ValidationFailure("nonregular-corpus", str(path)) from exc
    if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ValidationFailure("nonregular-corpus", str(path))
    return descriptor


def read_regular_member(directory_fd, name, limit):
    """Read one bounded regular member through one no-follow file descriptor."""
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValidationFailure("invalid-member-name", name)
    nofollow = getattr(os, "O_NOFOLLOW", None)
    if nofollow is None:
        raise ValidationFailure("no-follow-unavailable", name)
    flags = os.O_RDONLY | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(name, flags, dir_fd=directory_fd)
    except TypeError as exc:
        raise ValidationFailure("no-follow-unavailable", name) from exc
    except FileNotFoundError as exc:
        raise ValidationFailure("missing-member", name) from exc
    except OSError as exc:
        raise ValidationFailure("nonregular-member", name) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValidationFailure("nonregular-member", name)
        if metadata.st_size > limit:
            raise ValidationFailure("size-limit", f"{name} is {metadata.st_size} bytes")
        data = os.read(descriptor, limit + 1)
        if len(data) > limit:
            raise ValidationFailure("size-limit", f"{name} grew beyond {limit} bytes")
        if len(data) != metadata.st_size:
            raise ValidationFailure("member-changed", name)
        return data
    finally:
        os.close(descriptor)


def read_regular_path(path, limit):
    directory_fd = open_directory(Path(path).parent)
    try:
        return read_regular_member(directory_fd, Path(path).name, limit)
    finally:
        os.close(directory_fd)


def parse_canonical_json(path, data):
    try:
        decoded = data.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=no_duplicate_object)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationFailure("invalid-json", path.name) from exc
    if not is_canonical_json(data, value):
        raise ValidationFailure("canonical-json", path.name)
    return value


def parse_json(path, data):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=no_duplicate_object)
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise ValidationFailure("invalid-json", path.name) from exc


def require_mapping(value, label, keys):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValidationFailure("structure", label)
    return value


def require_text(value, label):
    if not isinstance(value, str) or not value:
        raise ValidationFailure("structure", label)
    return value


def validate_stimulus(fixture_id, stimulus):
    require_mapping(
        stimulus,
        f"{fixture_id}.stimulus",
        ("media_type", "encoding", "bytes", "sha256", "bytes_b64"),
    )
    if stimulus["media_type"] != "application/vnd.wave-mu.stimulus+json":
        raise ValidationFailure("stimulus-media-type", fixture_id)
    if stimulus["encoding"] != "base64":
        raise ValidationFailure("base64", fixture_id)
    if not isinstance(stimulus["bytes"], int) or not 0 < stimulus["bytes"] <= 8_192:
        raise ValidationFailure("stimulus-bytes", fixture_id)
    if not is_hex_digest(stimulus["sha256"]):
        raise ValidationFailure("stimulus-sha256", fixture_id)
    try:
        decoded = base64.b64decode(stimulus["bytes_b64"], validate=True)
    except (ValueError, TypeError) as exc:
        raise ValidationFailure("base64", fixture_id) from exc
    if len(decoded) != stimulus["bytes"]:
        raise ValidationFailure("stimulus-bytes", fixture_id)
    if sha256(decoded) != stimulus["sha256"]:
        raise ValidationFailure("stimulus-sha256", fixture_id)
    try:
        stimulus_json = json.loads(decoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationFailure("stimulus-json", fixture_id) from exc
    if not is_canonical_json(decoded, stimulus_json):
        raise ValidationFailure("stimulus-canonical-json", fixture_id)
    if not isinstance(stimulus_json, dict) or stimulus_json.get("schema") != "wave-mu-stimulus/v1":
        raise ValidationFailure("stimulus-schema", fixture_id)
    if stimulus_json.get("synthetic") is not True or stimulus_json.get("inert") is not True:
        raise ValidationFailure("inert-synthetic", fixture_id)


def validate_fixture(fixture_id, fixture):
    require_mapping(
        fixture,
        fixture_id,
        ("schema", "id", "issues", "gate", "execution_status", "observation", "adapter", "stimulus", "oracle", "safety"),
    )
    if fixture["schema"] != "wave-mu-fixture-contract/v1" or fixture["id"] != fixture_id:
        raise ValidationFailure("fixture-identity", fixture_id)
    if fixture["gate"] not in {"B", "C", "D", "E"}:
        raise ValidationFailure("fixture-gate", fixture_id)
    issues = fixture["issues"]
    if not isinstance(issues, list) or not issues or len(set(issues)) != len(issues) or any(
        type(issue) is not int or not 698 <= issue <= 706 for issue in issues
    ):
        raise ValidationFailure("fixture-issues", fixture_id)
    if fixture["execution_status"] != "not_run":
        raise ValidationFailure("not-run", fixture_id)
    observation = require_mapping(
        fixture["observation"], fixture_id + ".observation", ("status", "decision", "evidence_objects", "side_effects")
    )
    if observation != {"status": "not_run", "decision": None, "evidence_objects": [], "side_effects": None}:
        raise ValidationFailure("not-run", fixture_id)
    adapter = require_mapping(fixture["adapter"], fixture_id + ".adapter", ("status", "rule"))
    if adapter["status"] != "unresolved" or not isinstance(adapter["rule"], str) or not adapter["rule"]:
        raise ValidationFailure("unresolved-adapter", fixture_id)
    oracle = require_mapping(
        fixture["oracle"],
        fixture_id + ".oracle",
        ("enforcer", "expected_decision", "failure_effect", "required_evidence", "required_zero_side_effects", "missing_or_ambiguous_evidence"),
    )
    for key in ("enforcer", "expected_decision", "failure_effect", "missing_or_ambiguous_evidence"):
        require_text(oracle[key], fixture_id + ".oracle." + key)
    for key in ("required_evidence", "required_zero_side_effects"):
        if not isinstance(oracle[key], list) or not oracle[key] or not all(isinstance(item, str) and item for item in oracle[key]):
            raise ValidationFailure("structure", fixture_id + ".oracle." + key)
    if any(evidence not in EVIDENCE_REGISTRY for evidence in oracle["required_evidence"]):
        raise ValidationFailure("unresolved-evidence", fixture_id)
    safety = require_mapping(
        fixture["safety"],
        fixture_id + ".safety",
        ("data_class", "live_credentials", "private_repository", "personal_data", "authorized_remote_target", "execution_permitted_by_fixture"),
    )
    if safety != {
        "data_class": "synthetic_public_inert",
        "live_credentials": False,
        "private_repository": False,
        "personal_data": False,
        "authorized_remote_target": False,
        "execution_permitted_by_fixture": False,
    }:
        raise ValidationFailure("safety-contract", fixture_id)
    validate_stimulus(fixture_id, fixture["stimulus"])


def validate_manifest(manifest, fixture_metadata):
    expected_keys = {
        "corpus_root_sha256", "epic_706_acceptance_coverage", "fixture_count", "fixtures", "non_claims",
        "p0_dependency_policy", "role_separation", "root_rule", "schema", "source_catalog_sha256", "status",
    }
    require_mapping(manifest, "corpus-manifest.json", expected_keys)
    if manifest["schema"] != "wave-mu-fixture-corpus/v1" or manifest["fixture_count"] != 60:
        raise ValidationFailure("manifest-contract", "schema or fixture_count")
    if manifest["status"] != "exact_byte_contracts_not_adapted_not_executed":
        raise ValidationFailure("nonclaims", "status")
    if manifest["source_catalog_sha256"] != SOURCE_CATALOG_SHA256:
        raise ValidationFailure("source-catalog-sha256", "corpus-manifest.json")
    if manifest["root_rule"] != "sha256(concat(sorted fixture_id + NUL + fixture_file_sha256 + LF)))":
        raise ValidationFailure("manifest-contract", "root_rule")
    policy = require_mapping(manifest["p0_dependency_policy"], "p0_dependency_policy", ("future_mirror", "mode", "package_manager_network", "runtime_dependency_fetch"))
    if policy["mode"] != "jobspec_bound_digest_pinned_inputs_only" or policy["package_manager_network"] is not False or policy["runtime_dependency_fetch"] is not False:
        raise ValidationFailure("runtime-fetch", "p0_dependency_policy")
    roles = require_mapping(manifest["role_separation"], "role_separation", ("fixture_author", "human_publication_approver", "independent_security_reviewer", "publisher"))
    if not all(isinstance(value, str) and value for value in roles.values()):
        raise ValidationFailure("role-separation", "role_separation")
    claims = manifest["non_claims"]
    if not isinstance(claims, list) or len(claims) != 4 or not all(isinstance(value, str) for value in claims):
        raise ValidationFailure("nonclaims", "non_claims")
    joined_claims = " ".join(claims).lower()
    for required in ("not implementation-specific", "fixture has been adapted", "executed", "live credential", "remote mutation"):
        if required not in joined_claims:
            raise ValidationFailure("nonclaims", required)
    entries = manifest["fixtures"]
    if not isinstance(entries, list) or len(entries) != 60:
        raise ValidationFailure("manifest-contract", "fixtures")
    manifest_ids = set()
    for entry in entries:
        require_mapping(entry, "fixture entry", ("bytes", "gate", "id", "issues", "path", "sha256", "stimulus_sha256"))
        fixture_id = entry["id"]
        if fixture_id not in FIXTURE_IDS or fixture_id in manifest_ids or entry["path"] != fixture_id + ".json":
            raise ValidationFailure("manifest-contract", "fixture id")
        manifest_ids.add(fixture_id)
        actual = fixture_metadata[fixture_id]
        if entry["bytes"] != actual["bytes"] or entry["sha256"] != actual["sha256"]:
            raise ValidationFailure("fixture-sha256", fixture_id)
        if entry["gate"] != actual["fixture"]["gate"] or entry["issues"] != actual["fixture"]["issues"]:
            raise ValidationFailure("manifest-contract", fixture_id)
        if entry["stimulus_sha256"] != actual["fixture"]["stimulus"]["sha256"]:
            raise ValidationFailure("stimulus-sha256", fixture_id)
    if manifest_ids != FIXTURE_IDS:
        raise ValidationFailure("manifest-contract", "fixture coverage")
    coverage = manifest["epic_706_acceptance_coverage"]
    if not isinstance(coverage, dict) or not coverage or not all(
        isinstance(ids, list) and ids and set(ids) <= FIXTURE_IDS for ids in coverage.values()
    ):
        raise ValidationFailure("manifest-contract", "epic_706_acceptance_coverage")


def validate_source_catalog(catalog):
    expected_keys = {
        "schema", "status", "source_capture", "additional_context_capture", "governing_rule", "non_claims",
        "gates", "evidence", "issue_coverage", "specimens",
    }
    require_mapping(catalog, SOURCE_CATALOG_NAME, expected_keys)
    if catalog["schema"] != "wave-mu-acceptance-corpus/v1" or catalog["status"] != "local_design_candidate_not_executed":
        raise ValidationFailure("source-catalog-contract", "schema or status")
    expected_evidence = [
        {"id": evidence_id, "name": name} for evidence_id, name in EVIDENCE_REGISTRY.items()
    ]
    if catalog["evidence"] != expected_evidence:
        raise ValidationFailure("evidence-registry", SOURCE_CATALOG_NAME)
    if not isinstance(catalog["specimens"], list) or len(catalog["specimens"]) != 60:
        raise ValidationFailure("source-catalog-contract", "specimens")
    source_ids = set()
    for specimen in catalog["specimens"]:
        if not isinstance(specimen, dict) or specimen.get("id") not in FIXTURE_IDS:
            raise ValidationFailure("source-catalog-contract", "specimen id")
        source_ids.add(specimen["id"])
        evidence = specimen.get("evidence")
        if not isinstance(evidence, list) or not evidence or any(item not in EVIDENCE_REGISTRY for item in evidence):
            raise ValidationFailure("unresolved-evidence", specimen["id"])
    if source_ids != FIXTURE_IDS:
        raise ValidationFailure("source-catalog-contract", "specimen coverage")


def validate(corpus, schema):
    corpus = Path(corpus)
    schema = Path(schema)
    directory_fd = open_directory(corpus)
    try:
        expected_members = set(SUPPORT_SHA256) | {SOURCE_CATALOG_NAME} | {fixture_id + ".json" for fixture_id in FIXTURE_IDS}
        members = set(os.listdir(directory_fd))
        missing = sorted(expected_members - members)
        if missing:
            raise ValidationFailure("missing-member", missing[0])
        extra = sorted(members - expected_members)
        if extra:
            raise ValidationFailure("unexpected-member", extra[0])
        support_data = {}
        for name, expected_digest in SUPPORT_SHA256.items():
            data = read_regular_member(directory_fd, name, SIZE_LIMITS[name])
            support_data[name] = data
            if sha256(data) != expected_digest:
                raise ValidationFailure("support-sha256", name)
        source_catalog_data = read_regular_member(directory_fd, SOURCE_CATALOG_NAME, SOURCE_CATALOG_SIZE_LIMIT)
        if sha256(source_catalog_data) != SOURCE_CATALOG_SHA256:
            raise ValidationFailure("source-catalog-sha256", SOURCE_CATALOG_NAME)
        source_catalog = parse_json(Path(SOURCE_CATALOG_NAME), source_catalog_data)
        validate_source_catalog(source_catalog)
        mirror_data = read_regular_path(schema, SIZE_LIMITS["fixture-contract.schema.json"])
        if sha256(mirror_data) != SUPPORT_SHA256["fixture-contract.schema.json"] or mirror_data != support_data["fixture-contract.schema.json"]:
            raise ValidationFailure("schema-mirror", str(schema))
        for name in ("fixture-contract.schema.json", "corpus-manifest.json", "validation.json"):
            parse_json(Path(name), support_data[name])
        fixture_metadata = {}
        for fixture_id in sorted(FIXTURE_IDS):
            name = fixture_id + ".json"
            data = read_regular_member(directory_fd, name, FIXTURE_SIZE_LIMIT)
            fixture = parse_canonical_json(Path(name), data)
            validate_fixture(fixture_id, fixture)
            fixture_metadata[fixture_id] = {"bytes": len(data), "sha256": sha256(data), "fixture": fixture}
        manifest = parse_json(Path("corpus-manifest.json"), support_data["corpus-manifest.json"])
        validate_manifest(manifest, fixture_metadata)
    finally:
        os.close(directory_fd)
    root_material = b"".join(
        fixture_id.encode("ascii") + b"\0" + fixture_metadata[fixture_id]["sha256"].encode("ascii") + b"\n"
        for fixture_id in sorted(FIXTURE_IDS)
    )
    calculated_root = sha256(root_material)
    if manifest["corpus_root_sha256"] != EXPECTED_ROOT or calculated_root != EXPECTED_ROOT:
        raise ValidationFailure("corpus-root", calculated_root)
    return len(FIXTURE_IDS)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline validator for the inert Wave mu fixture corpus")
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    args = parser.parse_args(argv)
    try:
        count = validate(args.corpus, args.schema)
    except ValidationFailure as exc:
        print(f"error: {exc.code}: {exc.detail}", file=sys.stderr)
        return 1
    print(f"validated {count} fixtures; source catalog EV-01..EV-17; corpus root {EXPECTED_ROOT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
