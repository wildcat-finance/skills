#!/usr/bin/env python3
"""Demonstrate the Ethereum genesis empty-receipt fixture offline."""

from __future__ import annotations

from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib.util
from io import StringIO
from pathlib import Path
import shutil
import socket
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable
from unittest import mock


FIXTURE = Path(__file__).resolve(strict=True).parent
PLUGIN_ROOT = FIXTURE.parents[2]
REPOSITORY = PLUGIN_ROOT.parents[1]
ARIADNE = REPOSITORY / "plugins" / "ariadne" / "scripts" / "ariadne.py"
SCRIPTS = PLUGIN_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lazarus_lib.canonical import dump, dumps, load
from lazarus_lib.errors import LazarusError
from lazarus_lib.manifest import component_claim, fixture_digest, write_manifest
from lazarus_lib.release import RELEASE_NAME, release_digest, verify_release, write_release
from lazarus_lib.trieproof import EMPTY_TRIE_ROOT
from lazarus_lib.verifier import verify_fixture
from lazarus_lib.version import __version__


EMPTY_ROOT = "0x" + EMPTY_TRIE_ROOT.hex()
GENESIS_HASH = "0xd4e56740f876aef8c010b86a40d5f56745a118d0906a34e69aec8c0db1cb8fa3"
CORRELATION_ID = "ethereum-genesis-empty-receipts-v1-offline-demo"
STATEMENT_TYPE = "https://ariadne.wildcat.finance/state-fixture/v2"


def _ariadne_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("genesis_empty_ariadne", ARIADNE)
    if spec is None or spec.loader is None:
        raise AssertionError("Ariadne CLI could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _capture_statement(module: ModuleType, out: Path) -> None:
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        code = module.main(
            [
                "capture-state-fixture",
                "--fixture",
                str(FIXTURE),
                "--name",
                "ethereum-genesis-empty-receipts-v1",
                "--capture-tool",
                "lazarus",
                "--capture-version",
                __version__,
                "--capture-command",
                "lazarus",
                "--capture-command",
                "capture",
                "--first-capture-reason",
                "first checked empty receipt fixture",
                "--out",
                str(out),
            ]
        )
    if code != 0:
        raise AssertionError(f"Ariadne statement capture exited {code}")


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        data = path.read_bytes()
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(data)
    return digest.hexdigest()


def _refresh_component(root: Path, relative: str) -> None:
    manifest = load(root / "manifest.json")
    manifest["components"] = [
        component_claim(root, relative) if item["path"] == relative else item
        for item in manifest["components"]
    ]
    manifest["fixture_digest"] = fixture_digest(manifest)
    write_manifest(root, manifest)


def _mutate_root(root: Path) -> None:
    witness = load(root / "receipt-witness.json")
    witness["header"]["receipts_root"] = "0x" + "11" * 32
    dump(root / "receipt-witness.json", witness)
    _refresh_component(root, "receipt-witness.json")


def _mutate_shape(root: Path) -> None:
    witness = load(root / "receipt-witness.json")
    witness["target_receipt"] = {"transaction_index": "0x0"}
    dump(root / "receipt-witness.json", witness)
    _refresh_component(root, "receipt-witness.json")


def _mutate_count(root: Path) -> None:
    manifest = load(root / "manifest.json")
    manifest["evidence_counts"]["receipt_trie_proved"] = 1
    manifest["fixture_digest"] = fixture_digest(manifest)
    write_manifest(root, manifest)


def _mutate_digest(root: Path) -> None:
    path = root / "header.json"
    path.write_bytes(path.read_bytes() + b"\n")


def _expect_fixture_rejection(
    workspace: Path,
    label: str,
    change: Callable[[Path], None],
) -> str:
    mutated = workspace / f"mutated-{label}"
    shutil.copytree(FIXTURE, mutated)
    before = _tree_digest(mutated)
    change(mutated)
    if _tree_digest(mutated) == before:
        raise AssertionError(f"{label} mutation changed no fixture bytes")
    try:
        verify_fixture(mutated)
    except LazarusError:
        return "rejected"
    raise AssertionError(f"{label} mutation was accepted")


def _expect_release_rejection(workspace: Path, release: Path) -> str:
    mutated = workspace / "mutated-release"
    shutil.copytree(release, mutated)
    before = _tree_digest(mutated)
    document = load(mutated / RELEASE_NAME)
    document["verified"]["evidence_counts"]["receipt_trie_proved"] = 1
    document["release_digest"] = release_digest(document)
    dump(mutated / RELEASE_NAME, document)
    if _tree_digest(mutated) == before:
        raise AssertionError("release mutation changed no bytes")
    try:
        verify_release(mutated)
    except LazarusError:
        return "rejected"
    raise AssertionError("release mutation was accepted")


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("offline demonstration attempted a network connection")


def run_demo() -> dict[str, Any]:
    with mock.patch.object(socket.socket, "connect", side_effect=_deny_network), mock.patch.object(
        socket, "create_connection", side_effect=_deny_network
    ):
        fixture_report = verify_fixture(FIXTURE)
        relation = fixture_report["receipt_trie_proved"]
        if relation["mode"] != "empty":
            raise AssertionError("genesis receipt witness is not empty mode")
        if relation["computed_root"] != EMPTY_ROOT:
            raise AssertionError("genesis empty receipt root changed")
        if (relation["receipt_count"], relation["relations"]) != (0, 0):
            raise AssertionError("genesis empty receipt relation changed")

        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            statement = workspace / "statement.json"
            _capture_statement(_ariadne_module(), statement)
            statement_document = load(statement)
            release = workspace / "release"
            write_release(FIXTURE, statement, release)
            release_report = verify_release(release)
            release_version = load(release / RELEASE_NAME)["schema_version"]
            mutations = {
                "nonempty_root": _expect_fixture_rejection(
                    workspace, "nonempty-root", _mutate_root
                ),
                "mixed_shape": _expect_fixture_rejection(
                    workspace, "mixed-shape", _mutate_shape
                ),
                "count_inflation": _expect_fixture_rejection(
                    workspace, "count-inflation", _mutate_count
                ),
                "component_digest": _expect_fixture_rejection(
                    workspace, "component-digest", _mutate_digest
                ),
                "release": _expect_release_rejection(workspace, release),
            }

        return {
            "event": "ethereum_genesis_empty_receipt_demo",
            "correlation_id": CORRELATION_ID,
            "stage": "complete",
            "network": "denied",
            "block": {"number": "0x0", "hash": GENESIS_HASH},
            "relation": {
                "mode": relation["mode"],
                "receipts_root": relation["computed_root"],
                "receipt_count": relation["receipt_count"],
                "proved_relations": relation["relations"],
            },
            "evidence_counts": fixture_report["evidence_counts"],
            "versions": {
                "writer": __version__,
                "manifest": fixture_report["manifest"]["schema_version"],
                "statement": statement_document["predicateType"],
                "release": release_version,
            },
            "digests": {
                "fixture": fixture_report["fixture_digest"],
                "manifest": hashlib.sha256((FIXTURE / "manifest.json").read_bytes()).hexdigest(),
                "statement": release_report["statement_sha256"],
                "release": release_report["release_digest"],
            },
            "mutations": mutations,
        }


def main() -> int:
    print(dumps(run_demo()).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
