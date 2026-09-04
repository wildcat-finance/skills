"""Earn Alexandria proof-backed-state captures through Lazarus verification."""

from __future__ import annotations

import importlib
from pathlib import Path
import re
import shutil
import sys
import tempfile
from typing import NoReturn

from .canonical import load_bytes
from .errors import AlexandriaError
from .paths import validate_relative_path


EVIDENCE_CLASS = "proof-backed-state"
SOURCE_KIND = "lazarus-fixture"
MANIFEST_ROLE = "lazarus-manifest"
LOCATOR_CLASS = "local-fixture"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
UNAVAILABLE_REASON = (
    "the Lazarus verifier is unavailable; install "
    "plugins/lazarus/requirements.lock beside this checkout"
)


def _lazarus_api():
    plugins_root = Path(__file__).resolve().parents[3]
    lazarus_scripts = plugins_root / "lazarus" / "scripts"
    if not lazarus_scripts.is_dir():
        raise AlexandriaError(UNAVAILABLE_REASON)
    scripts_path = str(lazarus_scripts)
    if scripts_path not in sys.path:
        sys.path.insert(0, scripts_path)
    try:
        verifier = importlib.import_module("lazarus_lib.verifier")
        errors = importlib.import_module("lazarus_lib.errors")
    except ImportError as exc:
        raise AlexandriaError(UNAVAILABLE_REASON) from exc
    module_file = getattr(verifier, "__file__", None)
    if not isinstance(module_file, str):
        raise AlexandriaError("loaded Lazarus verifier has no local module path")
    try:
        Path(module_file).resolve().relative_to(lazarus_scripts.resolve())
    except ValueError as exc:
        raise AlexandriaError("loaded Lazarus verifier is outside the sibling plugin") from exc
    return verifier.verify_fixture, errors.LazarusError


def verify_proof_backed_captures(release_root, manifest) -> None:
    """Verify every proof-backed-state capture and refuse its nearest overclaim."""
    captures = [
        capture
        for capture in manifest["captures"]
        if capture["evidence_class"] == EVIDENCE_CLASS
    ]
    if not captures:
        return

    from .derivation import component_reader  # pylint: disable=import-outside-toplevel

    read_component = component_reader(release_root, manifest)
    components = {component["name"]: component for component in manifest["components"]}
    for capture in captures:
        try:
            _verify_capture(manifest, components, read_component, capture)
        except AlexandriaError as exc:
            prefix = _prefix(capture)
            if str(exc).startswith(prefix):
                raise
            raise AlexandriaError(prefix + str(exc)) from exc


def _verify_capture(manifest, components, read_component, capture) -> None:
    manifest_component = components[capture["component"]]
    if manifest_component["role"] != MANIFEST_ROLE:
        _refuse(capture, f"component role must be {MANIFEST_ROLE}")

    manifest_bytes = read_component(manifest_component["name"])
    lazarus_manifest = load_bytes(manifest_bytes, "Lazarus manifest")
    entries = _manifest_entries(capture, lazarus_manifest)
    mapped = _map_components(capture, entries, manifest["components"])
    verify_fixture, lazarus_error = _lazarus_api()

    temporary = Path(tempfile.mkdtemp(prefix="alexandria-lazarus-"))
    try:
        (temporary / "manifest.json").write_bytes(manifest_bytes)
        for entry, component in mapped:
            destination = temporary.joinpath(*Path(entry["path"]).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(read_component(component["name"]))
        try:
            report = verify_fixture(temporary)
        except lazarus_error as exc:
            _refuse(capture, f"Lazarus refused the fixture: {exc}")
        plan = load_bytes((temporary / "plan.json").read_bytes(), "verified Lazarus plan")
        _verify_binding(capture, report, plan)
    except OSError as exc:
        _refuse(capture, f"cannot reconstruct the Lazarus fixture: {exc}")
    finally:
        shutil.rmtree(temporary)


def _manifest_entries(capture, lazarus_manifest):
    if not isinstance(lazarus_manifest, dict) or "components" not in lazarus_manifest:
        _refuse(capture, "Lazarus manifest has no components list")
    entries = lazarus_manifest["components"]
    if not isinstance(entries, list):
        _refuse(capture, "Lazarus manifest components must be a list")

    paths = []
    for entry in entries:
        if not isinstance(entry, dict):
            _refuse(capture, "Lazarus manifest component must be an object")
        if set(entry) != {"path", "bytes", "sha256"}:
            _refuse(capture, "Lazarus manifest component fields are malformed")
        path = entry["path"]
        try:
            validate_relative_path(path, f"Lazarus component path {path!r}")
        except AlexandriaError as exc:
            _refuse(capture, str(exc))
        if path == "manifest.json":
            _refuse(capture, "Lazarus component path manifest.json lists the manifest itself")
        byte_count = entry["bytes"]
        if isinstance(byte_count, bool) or not isinstance(byte_count, int) or byte_count < 0:
            _refuse(capture, f"Lazarus component {path} has an invalid byte count")
        if not isinstance(entry["sha256"], str) or not SHA256_RE.fullmatch(entry["sha256"]):
            _refuse(capture, f"Lazarus component {path} has an invalid digest")
        paths.append(path)
    if len(paths) != len(set(paths)):
        _refuse(capture, "Lazarus manifest contains duplicate component paths")
    return entries


def _map_components(capture, entries, components):
    by_claim = {}
    for component in components:
        key = (component["sha256"], component["bytes"])
        by_claim.setdefault(key, []).append(component)
    for matches in by_claim.values():
        matches.sort(key=lambda item: item["name"])

    mapped = []
    for entry in entries:
        key = ("sha256:" + entry["sha256"], entry["bytes"])
        matches = by_claim.get(key, [])
        if not matches:
            _refuse(
                capture,
                f"release has no component for Lazarus fixture path {entry['path']}",
            )
        mapped.append((entry, matches[0]))
    return mapped


def _verify_binding(capture, report, plan) -> None:
    source = capture["source"]
    if source["kind"] != SOURCE_KIND:
        _refuse(capture, f"source kind must be {SOURCE_KIND}")
    if source["locator_class"] != LOCATOR_CLASS:
        _refuse(capture, f"source locator_class must be {LOCATOR_CLASS}")
    if source["reference"] != report["fixture_digest"]:
        _refuse(capture, "source reference does not match the Lazarus fixture digest")

    chain = f"eip155:{int(report['manifest']['chain_id'], 16)}"
    if capture["chain"] != chain:
        _refuse(capture, f"chain must match the proved fixture chain {chain}")

    interval = capture["scope"]["interval"]
    if interval["kind"] != "snapshot":
        _refuse(capture, "scope interval must be a snapshot")
    if "block_number" not in interval or "block_hash" not in interval:
        _refuse(capture, "snapshot must carry the proved block number and hash")
    block_number = str(int(report["block_number"], 16))
    if interval["block_number"] != block_number:
        _refuse(capture, f"block_number must match the proved block {block_number}")
    block_hash = report["block_hash"].lower()
    if interval["block_hash"] != block_hash:
        _refuse(capture, f"block_hash must match the proved block {block_hash}")

    if capture["scope"]["finality"] != "unknown":
        _refuse(
            capture,
            "finality must be unknown because Lazarus proves block binding but reports no finality class",
        )
    if capture["scope"]["kind"] != "subject-scoped":
        _refuse(
            capture,
            "scope must be subject-scoped because a finite proof set is not a full dataset",
        )

    targets = {
        f"{chain}:{target['address'].lower()}"
        for target in plan["proof_targets"]
    }
    for subject in capture["scope"]["subjects"]:
        if subject not in targets:
            _refuse(capture, f"subject {subject} is outside the fixture proof targets")


def _prefix(capture) -> str:
    return f"capture {capture['id']} proof-backed-state is not earned: "


def _refuse(capture, reason) -> NoReturn:
    raise AlexandriaError(_prefix(capture) + reason)
