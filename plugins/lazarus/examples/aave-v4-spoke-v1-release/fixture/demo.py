#!/usr/bin/env python3
"""Demonstrate the Aave v4 receipt-root relations without a provider."""

from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import ctypes
import errno
import hashlib
import importlib.util
from io import StringIO
import os
from pathlib import Path
import secrets
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any, Callable
from unittest import mock


FIXTURE = Path(__file__).resolve().parent
PLUGIN_ROOT = FIXTURE.parents[1]
REPOSITORY = PLUGIN_ROOT.parents[1]
SHIPPED_RELEASE = PLUGIN_ROOT / "examples" / "aave-v4-spoke-v1-release"
LEGACY_FIXTURE = PLUGIN_ROOT / "examples" / "aave-v4-spoke-v0"
LEGACY_RELEASE = PLUGIN_ROOT / "examples" / "aave-v4-spoke-v0-release"
ARIADNE = REPOSITORY / "plugins" / "ariadne" / "scripts" / "ariadne.py"
SCRIPTS = PLUGIN_ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from lazarus_lib.canonical import dump, dumps, load
from lazarus_lib.errors import IntegrityError, LazarusError, PathError
from lazarus_lib.manifest import (
    build_manifest,
    component_claim,
    fixture_digest,
    write_manifest,
)
from lazarus_lib.paths import read_confined_bytes
from lazarus_lib.records import (
    read_rpc_records,
    request_key,
    write_rpc_records,
)
from lazarus_lib.release import RELEASE_NAME, release_digest, verify_release, write_release
from lazarus_lib.verifier import verify_fixture
from lazarus_lib.version import __version__


BLOCK_NUMBER = "0x18ac22c"
BLOCK_HASH = "0x11e9be2ff9ff6a04319af0b04c24b95f3f1117c2df79f44f94d208857d01af07"
TARGET_SELECTOR = "0xdaa7ebd15335bf809ee414876846df98d40736e7d29e3eeaca8b434653b9313e"
RECEIPTS_ROOT = "0x7d3403cc37d77546db4005e06876a204372b0ef52a703cc88577a96dc4befb1a"
TARGET_INDEX = 0x3F
STATEMENT_TYPE = "https://ariadne.wildcat.finance/state-fixture/v2"
CORRELATION_ID = "aave-v4-spoke-v1-offline-demo"
SOURCE_FIXTURE = PLUGIN_ROOT / "tests" / "fixtures" / "aave-v4-receipt-proof-v1"
SOURCE_FIXTURE_DIGEST = (
    "a1007c769291b0ae4f3a9cf20ca8316ea05b63f10e78511d73c9eb29c3109d2d"
)
SOURCE_COMPONENTS = (
    "anchors.jsonl",
    "header.json",
    "plan.json",
    "proofs.jsonl",
    "receipt-witness.json",
    "rpc.jsonl",
)
FIXTURE_COMPONENTS = SOURCE_COMPONENTS + ("demo.py",)
PRODUCER_COMMAND = (
    "python3",
    "plugins/lazarus/examples/aave-v4-spoke-v1/demo.py",
    "build-fixture",
    "--out",
    "tmp/aave-v4-spoke-v1-rebuild",
)
LEGACY_DIGESTS = {
    "fixture": "986287699f6e327be412b1503b7dfacec34faeff77b3bbb763215f274dc6f59f",
    "manifest": "1be58bdeb2312b24ab7958fcdd7a5304a902d81ec7b6491d9cc5d7a0efff8bb3",
    "statement": "cb5cfae539f91d814dcee0ddddf13f4fb60a03f2b17c1b7581f330a8353438ef",
    "release": "de4eb122aa84c589bdd0c7370f43e01845d4b733bcf61599f6b9893d41c5be4e",
}


def _ariadne_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("aave_v4_spoke_v1_ariadne", ARIADNE)
    if spec is None or spec.loader is None:
        raise AssertionError("Ariadne CLI could not be loaded")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_ariadne(module: ModuleType, arguments: list[str]) -> None:
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(output):
        code = module.main(arguments)
    if code != 0:
        raise AssertionError(
            f"Ariadne stage {arguments[0]} exited {code}: {output.getvalue()}"
        )


def _capture_statement(module: ModuleType, fixture: Path, out: Path) -> None:
    command_arguments: list[str] = []
    for word in PRODUCER_COMMAND:
        if word.startswith("-"):
            command_arguments.append(f"--capture-command={word}")
        else:
            command_arguments.extend(("--capture-command", word))
    _run_ariadne(
        module,
        [
            "capture-state-fixture",
            "--fixture",
            str(fixture),
            "--name",
            "aave-v4-spoke-v1",
            "--capture-tool",
            "lazarus",
            "--capture-version",
            "0.2.0",
            *command_arguments,
            "--first-capture-reason",
            "first receipts-root-proved Aave v4 fixture",
            "--out",
            str(out),
        ],
    )
    _run_ariadne(module, ["verify", str(out)])


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _directory_identity(path: Path) -> tuple[int, int]:
    try:
        details = path.stat(follow_symlinks=False)
    except OSError:
        raise PathError("fixture output parent is unavailable") from None
    if not stat.S_ISDIR(details.st_mode):
        raise PathError("fixture output parent is not a directory")
    return details.st_dev, details.st_ino


def _output_exists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    except (OSError, ValueError):
        raise PathError("fixture output cannot be inspected") from None
    return True


def _require_same_parent(
    requested_parent: Path,
    resolved_parent: Path,
    identity: tuple[int, int],
) -> Path:
    try:
        current = requested_parent.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        raise PathError("fixture output parent changed during build") from None
    if current != resolved_parent or _directory_identity(current) != identity:
        raise PathError("fixture output parent changed during build")
    return current


def _open_directory(path: Path) -> int:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(path, flags)
    except OSError:
        raise PathError("fixture stage is unavailable") from None


def _open_directory_entry(directory_fd: int, name: str) -> int:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        return os.open(name, flags, dir_fd=directory_fd)
    except OSError:
        raise PathError("fixture stage is unavailable") from None


def _entry_identity(directory_fd: int, name: str) -> tuple[int, int] | None:
    try:
        details = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError:
        raise PathError("fixture stage is unavailable") from None
    if not stat.S_ISDIR(details.st_mode):
        raise PathError("fixture stage is unavailable")
    return details.st_dev, details.st_ino


def _make_directory_entry(
    directory_fd: int,
    prefix: str,
) -> tuple[str, tuple[int, int]]:
    """Create one private directory beneath an already pinned parent."""

    for _ in range(128):
        name = f"{prefix}{secrets.token_hex(8)}"
        created = False
        try:
            os.mkdir(name, mode=0o700, dir_fd=directory_fd)
            created = True
        except FileExistsError:
            continue
        except OSError:
            raise PathError("fixture stage cannot be created") from None
        try:
            descriptor = _open_directory_entry(directory_fd, name)
            try:
                details = os.fstat(descriptor)
                identity = (details.st_dev, details.st_ino)
            finally:
                os.close(descriptor)
            if _entry_identity(directory_fd, name) != identity:
                raise PathError("fixture stage identity changed during build")
            return name, identity
        except (OSError, PathError):
            if created:
                try:
                    os.rmdir(name, dir_fd=directory_fd)
                except OSError:
                    pass
            raise PathError("fixture stage is unavailable") from None
    raise PathError("fixture stage cannot be created")


def _write_new_component(directory_fd: int, name: str, data: bytes) -> None:
    """Write a new stage component without following or replacing an entry."""

    if not name or "/" in name or "\\" in name or name in {".", ".."}:
        raise PathError("fixture stage component name is unsafe")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    try:
        descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError:
        if descriptor is not None:
            try:
                os.close(descriptor)
            except OSError:
                pass
        raise PathError("fixture stage is unavailable") from None


def _clear_anchored_directory(
    directory_fd: int,
    *,
    depth: int = 0,
) -> None:
    """Remove bounded stage contents through their already-open directory."""

    if depth > 2:
        raise PathError("fixture stage cleanup exceeded its depth bound")
    try:
        with os.scandir(directory_fd) as scanned:
            names = sorted(entry.name for entry in scanned)
    except OSError:
        raise PathError("fixture stage cleanup failed") from None
    if len(names) > 16:
        raise PathError("fixture stage cleanup exceeded its entry bound")

    for name in names:
        try:
            details = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if stat.S_ISDIR(details.st_mode):
                identity = (details.st_dev, details.st_ino)
                child_fd = _open_directory_entry(directory_fd, name)
                try:
                    opened = os.fstat(child_fd)
                    if (opened.st_dev, opened.st_ino) != identity:
                        raise PathError("fixture stage identity changed during build")
                    _clear_anchored_directory(child_fd, depth=depth + 1)
                finally:
                    os.close(child_fd)
                if _entry_identity(directory_fd, name) != identity:
                    raise PathError("fixture stage identity changed during build")
                os.rmdir(name, dir_fd=directory_fd)
            else:
                os.unlink(name, dir_fd=directory_fd)
        except PathError:
            raise
        except OSError:
            raise PathError("fixture stage cleanup failed") from None


def _remove_anchored_tree(
    directory_fd: int,
    name: str,
    identity: tuple[int, int],
) -> None:
    current_identity = _entry_identity(directory_fd, name)
    if current_identity is None:
        return
    if current_identity != identity:
        raise PathError("fixture stage identity changed during build")
    quarantine = f"{name}.cleanup-{secrets.token_hex(8)}"
    try:
        _atomic_no_replace_in_directory(
            directory_fd,
            name,
            directory_fd,
            quarantine,
        )
    except PathError:
        raise PathError("fixture stage cleanup failed") from None
    quarantine_fd: int | None = None
    try:
        quarantine_fd = _open_directory_entry(directory_fd, quarantine)
        quarantined = os.fstat(quarantine_fd)
        if (quarantined.st_dev, quarantined.st_ino) != identity:
            raise PathError("fixture stage identity changed during build")
        _clear_anchored_directory(quarantine_fd)
    except PathError:
        try:
            _atomic_no_replace_in_directory(
                directory_fd,
                quarantine,
                directory_fd,
                name,
            )
        except PathError:
            pass
        raise
    finally:
        if quarantine_fd is not None:
            os.close(quarantine_fd)

    quarantined_identity = _entry_identity(directory_fd, quarantine)
    if quarantined_identity != identity:
        try:
            _atomic_no_replace_in_directory(
                directory_fd,
                quarantine,
                directory_fd,
                name,
            )
        except PathError:
            pass
        raise PathError("fixture stage identity changed during build")
    try:
        os.rmdir(quarantine, dir_fd=directory_fd)
    except OSError:
        raise PathError("fixture stage cleanup failed") from None


def _atomic_no_replace_in_directory(
    source_directory_fd: int,
    source_name: str,
    destination_directory_fd: int,
    destination_name: str,
) -> None:
    """Atomically publish entries held beneath open directories."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source_name)
    destination_bytes = os.fsencode(destination_name)
    if hasattr(libc, "renameat2"):
        renameat2 = libc.renameat2
        renameat2.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameat2.restype = ctypes.c_int
        result = renameat2(
            source_directory_fd,
            source_bytes,
            destination_directory_fd,
            destination_bytes,
            1,
        )
    elif hasattr(libc, "renameatx_np"):
        renameatx = libc.renameatx_np
        renameatx.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        renameatx.restype = ctypes.c_int
        result = renameatx(
            source_directory_fd,
            source_bytes,
            destination_directory_fd,
            destination_bytes,
            0x00000004,
        )
    else:
        raise PathError("platform has no atomic no-replace directory rename")
    if result == 0:
        return
    error = ctypes.get_errno()
    if error in (errno.EEXIST, errno.ENOTEMPTY):
        raise PathError("fixture output appeared before finalisation")
    raise PathError("fixture output cannot be finalised")


def build_fixture(output: str | Path) -> dict[str, Any]:
    """Materialise the published fixture from its pinned source components."""

    source_report = verify_fixture(SOURCE_FIXTURE)
    if source_report["fixture_digest"] != SOURCE_FIXTURE_DIGEST:
        raise IntegrityError("pinned aave-v4-receipt-proof-v1 fixture changed")
    source_claims = source_report["manifest"]["components"]
    if tuple(item["path"] for item in source_claims) != SOURCE_COMPONENTS:
        raise IntegrityError("pinned aave-v4-receipt-proof-v1 component inventory changed")

    requested = Path(output)
    if not requested.name or requested.name in {".", ".."}:
        raise PathError("fixture output must name a new directory")
    try:
        intended_destination = requested.resolve(strict=False)
    except (OSError, RuntimeError, ValueError):
        raise PathError("fixture output cannot be resolved") from None
    source_roots = (FIXTURE.resolve(), SOURCE_FIXTURE.resolve())
    for source_root in source_roots:
        if (
            intended_destination == source_root
            or source_root in intended_destination.parents
        ):
            raise PathError("fixture output cannot be inside a source fixture")

    parent_path = requested.parent
    created_parent = False
    try:
        parent = parent_path.resolve(strict=True)
    except FileNotFoundError:
        try:
            parent_path.mkdir(mode=0o700)
            created_parent = True
            parent = parent_path.resolve(strict=True)
        except OSError:
            if created_parent:
                try:
                    parent_path.rmdir()
                except OSError:
                    pass
            raise PathError("fixture output parent cannot be created") from None
    except OSError:
        raise PathError("fixture output parent cannot be resolved") from None
    if not parent.is_dir():
        raise PathError("fixture output parent is not a directory")
    parent_identity = _directory_identity(parent)
    destination = parent / requested.name
    if _output_exists(destination):
        raise PathError("fixture output already exists")
    for source_root in source_roots:
        if destination == source_root or source_root in destination.parents:
            if created_parent:
                try:
                    parent.rmdir()
                except OSError:
                    pass
            raise PathError("fixture output cannot be inside a source fixture")

    stage_parent_fd: int | None = None
    stage_fd: int | None = None
    fixture_fd: int | None = None
    stage_name: str | None = None
    stage_identity: tuple[int, int] | None = None
    fixture_identity: tuple[int, int] | None = None
    published = False
    cleanup_failed = False
    rollback_failed = False
    try:
        stage_parent_fd = _open_directory(parent)
        stage_parent_details = os.fstat(stage_parent_fd)
        if (stage_parent_details.st_dev, stage_parent_details.st_ino) != parent_identity:
            raise PathError("fixture output parent changed during build")
        _require_same_parent(parent_path, parent, parent_identity)
        stage_name, stage_identity = _make_directory_entry(
            stage_parent_fd,
            f".{destination.name}.stage-",
        )
        stage_fd = _open_directory_entry(stage_parent_fd, stage_name)
        stage_details = os.fstat(stage_fd)
        if (stage_details.st_dev, stage_details.st_ino) != stage_identity:
            raise PathError("fixture stage identity changed during build")
        try:
            os.mkdir("fixture", mode=0o700, dir_fd=stage_fd)
        except OSError:
            raise PathError("fixture stage is unavailable") from None
        fixture_identity = _entry_identity(stage_fd, "fixture")
        if fixture_identity is None:
            raise PathError("fixture stage is unavailable")
        fixture_fd = _open_directory_entry(stage_fd, "fixture")
        fixture_details = os.fstat(fixture_fd)
        if (fixture_details.st_dev, fixture_details.st_ino) != fixture_identity:
            raise PathError("fixture stage identity changed during build")
        _require_same_parent(parent_path, parent, parent_identity)
        for claim in source_claims:
            relative = claim["path"]
            data = read_confined_bytes(
                SOURCE_FIXTURE,
                relative,
                max_bytes=claim["bytes"],
            )
            if len(data) != claim["bytes"] or hashlib.sha256(data).hexdigest() != claim[
                "sha256"
            ]:
                raise IntegrityError(
                    "pinned aave-v4-receipt-proof-v1 source changed during build"
                )
            _require_same_parent(parent_path, parent, parent_identity)
            _write_new_component(fixture_fd, relative, data)
            _require_same_parent(parent_path, parent, parent_identity)
        _require_same_parent(parent_path, parent, parent_identity)
        copied_claims = [
            component_claim(fixture_fd, relative) for relative in SOURCE_COMPONENTS
        ]
        _require_same_parent(parent_path, parent, parent_identity)
        if copied_claims != source_claims:
            raise IntegrityError("pinned aave-v4-receipt-proof-v1 source changed during build")
        demo_bytes = read_confined_bytes(FIXTURE, "demo.py", max_bytes=1024 * 1024)
        _require_same_parent(parent_path, parent, parent_identity)
        _write_new_component(fixture_fd, "demo.py", demo_bytes)
        _require_same_parent(parent_path, parent, parent_identity)

        manifest = build_manifest(
            fixture_fd,
            FIXTURE_COMPONENTS,
            chain_id="0x1",
            block_number=BLOCK_NUMBER,
            block_hash=BLOCK_HASH,
        )
        _require_same_parent(parent_path, parent, parent_identity)
        write_manifest(fixture_fd, manifest)
        _require_same_parent(parent_path, parent, parent_identity)
        report = verify_fixture(fixture_fd)
        _require_same_parent(parent_path, parent, parent_identity)
        destination = parent / requested.name
        if _output_exists(destination):
            raise PathError("fixture output already exists")
        _atomic_no_replace_in_directory(
            stage_fd,
            "fixture",
            stage_parent_fd,
            destination.name,
        )
        try:
            _require_same_parent(parent_path, parent, parent_identity)
        except PathError:
            try:
                _remove_anchored_tree(
                    stage_parent_fd,
                    destination.name,
                    fixture_identity,
                )
            except PathError:
                rollback_failed = True
            raise
        published = True
        return report
    finally:
        if fixture_fd is not None:
            try:
                os.close(fixture_fd)
            except OSError:
                pass
        if stage_fd is not None:
            try:
                os.close(stage_fd)
            except OSError:
                pass
        if (
            stage_parent_fd is not None
            and stage_name is not None
            and stage_identity is not None
        ):
            try:
                _remove_anchored_tree(stage_parent_fd, stage_name, stage_identity)
            except PathError:
                cleanup_failed = True
        if not published and created_parent:
            try:
                parent.rmdir()
            except OSError:
                pass
        if stage_parent_fd is not None:
            try:
                os.close(stage_parent_fd)
            except OSError:
                pass
        if rollback_failed:
            raise PathError("fixture published output cleanup failed") from None
        if cleanup_failed:
            raise PathError("fixture stage cleanup failed") from None


def _run_producer_command(execution_root: Path) -> Path:
    """Run the exact argv recorded in the Ariadne statement."""

    launcher = execution_root / PRODUCER_COMMAND[1]
    launcher.parent.mkdir(parents=True)
    launcher.symlink_to(Path(__file__).resolve())
    fixture = execution_root / PRODUCER_COMMAND[-1]
    try:
        result = subprocess.run(
            list(PRODUCER_COMMAND),
            cwd=execution_root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        raise AssertionError("recorded fixture producer command could not run") from None
    if result.returncode != 0:
        raise AssertionError("recorded fixture producer command failed")
    return fixture


def _flip_last_hex(value: str) -> str:
    return value[:-1] + ("0" if value[-1] != "0" else "1")


def _flip_last_byte_hex(value: str) -> str:
    if not value.startswith("0x") or len(value) < 4 or len(value) % 2 != 0:
        raise AssertionError("mutation target is not a non-empty byte string")
    return value[:-2] + f"{int(value[-2:], 16) ^ 1:02x}"


def _refresh_component(root: Path, relative: str) -> None:
    manifest = load(root / "manifest.json")
    manifest["components"] = [
        component_claim(root, relative) if item["path"] == relative else item
        for item in manifest["components"]
    ]
    manifest["fixture_digest"] = fixture_digest(manifest)
    write_manifest(root, manifest)


def _mutate_witness(root: Path, change: Callable[[dict[str, Any]], None]) -> None:
    witness = load(root / "receipt-witness.json")
    change(witness)
    dump(root / "receipt-witness.json", witness)
    _refresh_component(root, "receipt-witness.json")


def _expect_fixture_rejection(
    workspace: Path,
    label: str,
    change: Callable[[Path], None],
) -> str:
    changed = workspace / f"mutated-{label}"
    shutil.copytree(FIXTURE, changed)
    change(changed)
    try:
        verify_fixture(changed)
    except LazarusError:
        return "rejected"
    raise AssertionError(f"{label} mutation was accepted")


def _receipt_mutation(root: Path) -> None:
    _mutate_witness(
        root,
        lambda witness: witness["receipts"][0].__setitem__("status", "0x0"),
    )


def _index_mutation(root: Path) -> None:
    _mutate_witness(
        root,
        lambda witness: witness["receipts"][TARGET_INDEX].__setitem__(
            "transaction_index", "0xbe"
        ),
    )


def _log_mutation(root: Path) -> None:
    def change(witness: dict[str, Any]) -> None:
        log = witness["receipts"][TARGET_INDEX]["logs"][0]
        # ephoros: allow receipt-witness field access is mutation evidence, not telemetry
        log["address"] = _flip_last_byte_hex(log["address"])

    _mutate_witness(root, change)


def _root_mutation(root: Path) -> None:
    def change(witness: dict[str, Any]) -> None:
        witness["header"]["receipts_root"] = _flip_last_hex(
            witness["header"]["receipts_root"]
        )

    _mutate_witness(root, change)


def _count_mutation(root: Path) -> None:
    manifest = load(root / "manifest.json")
    manifest["evidence_counts"]["receipt_trie_proved"] = 1
    manifest["fixture_digest"] = fixture_digest(manifest)
    write_manifest(root, manifest)


def _rewrite_recorded_target_hash(root: Path, transaction_hash: str) -> None:
    plan = load(root / "plan.json")
    header = load(root / "header.json")
    records = read_rpc_records(root / "rpc.jsonl")
    relation = plan["receipt_witness"]
    index = int(relation["target_transaction_index"], 16)
    header["rpc_result"]["transactions"][index] = transaction_hash

    request = next(
        item
        for item in plan["requests"]
        if item["name"] == relation["target_receipt_lookup_request"]
    )
    request["params"] = [transaction_hash]
    by_name = {record["name"]: record for record in records}
    target = by_name[relation["target_receipt_lookup_request"]]
    target["params"] = [transaction_hash]
    target["request_key"] = request_key(target["method"], target["params"])

    block_receipts = by_name[relation["block_receipts_request"]]["outcome"]["result"]
    for receipt in (block_receipts[index], target["outcome"]["result"]):
        receipt["transactionHash"] = transaction_hash
        for log in receipt["logs"]:
            log["transactionHash"] = transaction_hash
    filtered = by_name[relation["filtered_logs_request"]]["outcome"]["result"]
    for log in filtered:
        if int(log["transactionIndex"], 16) == index:
            log["transactionHash"] = transaction_hash

    dump(root / "plan.json", plan)
    dump(root / "header.json", header)
    write_rpc_records(root / "rpc.jsonl", records)
    for relative in ("plan.json", "header.json", "rpc.jsonl"):
        _refresh_component(root, relative)


def _hash_rewrite_evidence(workspace: Path, baseline: dict[str, Any]) -> str:
    rewritten = workspace / "coherent-hash-rewrite"
    shutil.copytree(FIXTURE, rewritten)
    _rewrite_recorded_target_hash(rewritten, "0x" + "aa" * 32)
    report = verify_fixture(rewritten)
    if report["receipts_root"] != baseline["receipts_root"]:
        raise AssertionError("recorded hash rewrite changed the receipt root")
    if report["receipt_trie_proved"] != baseline["receipt_trie_proved"]:
        raise AssertionError("recorded hash rewrite changed a proved relation")
    return "unchanged"


def _recorded_disagreement_evidence(workspace: Path) -> str:
    changed = workspace / "recorded-hash-disagreement"
    shutil.copytree(FIXTURE, changed)
    header = load(changed / "header.json")
    header["rpc_result"]["transactions"][TARGET_INDEX] = "0x" + "bb" * 32
    dump(changed / "header.json", header)
    _refresh_component(changed, "header.json")
    try:
        verify_fixture(changed)
    except LazarusError as error:
        words = str(error).lower()
        if "recorded rpc transaction hash disagreement" not in words:
            raise AssertionError("recorded-source disagreement reached the wrong gate") from error
        if "root" in words or "proved" in words:
            raise AssertionError("recorded-source disagreement was promoted") from error
        return "rejected-recorded-rpc"
    raise AssertionError("one-source recorded hash disagreement was accepted")


def _release_mutation_evidence(workspace: Path) -> str:
    changed = workspace / "mutated-release"
    shutil.copytree(SHIPPED_RELEASE, changed)
    document = load(changed / RELEASE_NAME)
    document["verified"]["receipts_root"] = _flip_last_hex(
        document["verified"]["receipts_root"]
    )
    dump(changed / RELEASE_NAME, document)
    try:
        verify_release(changed)
    except LazarusError:
        return "rejected"
    raise AssertionError("one-byte release mutation was accepted")


def _legacy_evidence() -> dict[str, str]:
    observed = {
        "fixture": verify_fixture(LEGACY_FIXTURE)["fixture_digest"],
        "manifest": hashlib.sha256(
            (LEGACY_FIXTURE / "manifest.json").read_bytes()
        ).hexdigest(),
        "statement": hashlib.sha256(
            (LEGACY_RELEASE / "statement.json").read_bytes()
        ).hexdigest(),
        "release": hashlib.sha256(
            (LEGACY_RELEASE / RELEASE_NAME).read_bytes()
        ).hexdigest(),
    }
    if observed != LEGACY_DIGESTS:
        raise AssertionError("historical Aave v4 spoke v0 bytes changed")
    return observed


def _deny_network(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("offline demonstration attempted a network connection")


def run_demo() -> dict[str, Any]:
    with mock.patch.object(socket.socket, "connect", side_effect=_deny_network), mock.patch.object(
        socket, "create_connection", side_effect=_deny_network
    ):
        fixture_report = verify_fixture(FIXTURE)
        release_report = verify_release(SHIPPED_RELEASE)
        relation = fixture_report["receipt_trie_proved"]
        if relation["computed_root"] != RECEIPTS_ROOT:
            raise AssertionError("Aave v4 receipt root changed")
        if (
            relation["receipt_count"],
            relation["target_transaction_index"],
            relation["target_log_count"],
            relation["filtered_log_count"],
            relation["relations"],
        ) != (177, "0x3f", 4, 2, 2):
            raise AssertionError("Aave v4 proved relation changed")
        if relation["transaction_hash_attribution"] != "recorded_rpc":
            raise AssertionError("transaction-hash attribution was promoted")

        ariadne = _ariadne_module()
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            producer_root = workspace / "producer-root"
            rebuilt_fixture = _run_producer_command(producer_root)
            if _tree_bytes(rebuilt_fixture) != _tree_bytes(FIXTURE):
                raise AssertionError("shipped fixture differs from a fresh build")
            statement_a = workspace / "statement-a.json"
            statement_b = workspace / "statement-b.json"
            _capture_statement(ariadne, rebuilt_fixture, statement_a)
            _capture_statement(ariadne, rebuilt_fixture, statement_b)
            if statement_a.read_bytes() != statement_b.read_bytes():
                raise AssertionError("state-fixture/v2 capture is not deterministic")
            if statement_a.read_bytes() != (SHIPPED_RELEASE / "statement.json").read_bytes():
                raise AssertionError("shipped statement differs from a fresh capture")

            release_a = workspace / "release-a"
            release_b = workspace / "release-b"
            write_release(rebuilt_fixture, statement_a, release_a)
            write_release(rebuilt_fixture, statement_b, release_b)
            if _tree_bytes(release_a) != _tree_bytes(release_b):
                raise AssertionError("release-v2 rebuild is not deterministic")
            if _tree_bytes(release_a) != _tree_bytes(SHIPPED_RELEASE):
                raise AssertionError("shipped release differs from a fresh rebuild")

            mutations = {
                "receipt": _expect_fixture_rejection(
                    workspace, "receipt", _receipt_mutation
                ),
                "index": _expect_fixture_rejection(
                    workspace, "index", _index_mutation
                ),
                "log": _expect_fixture_rejection(workspace, "log", _log_mutation),
                "root": _expect_fixture_rejection(
                    workspace, "root", _root_mutation
                ),
                "count": _expect_fixture_rejection(
                    workspace, "count", _count_mutation
                ),
                "release": _release_mutation_evidence(workspace),
            }
            hash_rewrite = _hash_rewrite_evidence(workspace, fixture_report)
            recorded_disagreement = _recorded_disagreement_evidence(workspace)

        statement_sha256 = release_report["statement_sha256"]
        return {
            "event": "aave_v4_receipt_proof_demo",
            "correlation_id": CORRELATION_ID,
            "stage": "complete",
            "network": "denied",
            "fixture_rebuild": "identical",
            "producer_command": list(PRODUCER_COMMAND),
            "block": {"number": BLOCK_NUMBER, "hash": BLOCK_HASH},
            "recorded_target_selector": TARGET_SELECTOR,
            "relation": {
                "receipts_root": relation["computed_root"],
                "receipt_count": relation["receipt_count"],
                "target_index": relation["target_transaction_index"],
                "target_log_count": relation["target_log_count"],
                "filtered_log_count": relation["filtered_log_count"],
                "proved_relations": relation["relations"],
                "transaction_hash_attribution": relation[
                    "transaction_hash_attribution"
                ],
            },
            "evidence_counts": fixture_report["evidence_counts"],
            "versions": {
                "writer": __version__,
                "manifest": fixture_report["manifest"]["schema_version"],
                "statement": STATEMENT_TYPE,
                "release": load(SHIPPED_RELEASE / RELEASE_NAME)["schema_version"],
            },
            "digests": {
                "fixture": fixture_report["fixture_digest"],
                "statement": statement_sha256,
                "release": release_report["release_digest"],
            },
            "mutations": mutations,
            "coherent_transaction_hash_rewrite": hash_rewrite,
            "recorded_hash_disagreement": recorded_disagreement,
            "legacy": _legacy_evidence(),
        }


def main(arguments: list[str] | None = None) -> int:
    words = list(sys.argv[1:] if arguments is None else arguments)
    if words:
        parser = argparse.ArgumentParser(
            description="Build the fixed Aave v4 fixture or run its offline demo."
        )
        commands = parser.add_subparsers(dest="command", required=True)
        builder = commands.add_parser(
            "build-fixture",
            help="materialise the byte-exact fixture from pinned local sources",
        )
        builder.add_argument("--out", required=True)
        release_verifier = commands.add_parser(
            "verify-release",
            help="verify the checked preservation release without network access",
        )
        release_verifier.add_argument("--release", required=True)
        parsed = parser.parse_args(words)
        if parsed.command == "build-fixture":
            try:
                report = build_fixture(parsed.out)
            except LazarusError as error:
                print(f"refused: {error}", file=sys.stderr)
                return 1
            print(
                dumps(
                    {
                        "event": "aave_v4_fixture_build",
                        "stage": "complete",
                        "fixture_digest": report["fixture_digest"],
                    }
                ).decode("utf-8")
            )
            return 0
        if parsed.command == "verify-release":
            try:
                report = verify_release(parsed.release)
            except LazarusError as error:
                print(f"refused: {error}", file=sys.stderr)
                return 1
            print(
                dumps(
                    {
                        "event": "aave_v4_release_verify",
                        "stage": "complete",
                        "fixture_digest": report["fixture_digest"],
                        "release_digest": report["release_digest"],
                    }
                ).decode("utf-8")
            )
            return 0
        raise AssertionError("unreachable Aave v4 command")
    print(dumps(run_demo()).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
