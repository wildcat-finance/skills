#!/usr/bin/env python3
"""Admit Homologia inputs without executing either implementation.

`check` validates one closed manifest and its declared JSONL vector sets,
records their exact digests, and installs a canonical checked-inputs record.
The other verbs remain deliberately unavailable until their governed steps.
"""

from __future__ import annotations

import argparse
import errno
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
from pathlib import Path, PurePosixPath
from typing import Any, NamedTuple

VERSION = "1.1.0"
MANIFEST_SCHEMA = "homologia-manifest/v1"
CHECKED_SCHEMA = "homologia-checked-inputs/v1"

VERBS = {
    "check": "Validate a manifest, its vector sets and their expected-answer provenance.",
    "run-mirror": "Run one declared mirror over checked vectors and record its answers.",
    "compare": "Compare recorded answers against expected answers and write the verdict.",
    "render": "Render a verdict as a report, adding nothing the verdict does not carry.",
    "verify": "Recompute the verdict, its specimens and the report from the declared inputs.",
}

NOT_BUILT = 3
INPUT_REFUSED = 4
OUTPUT_REFUSED = 5

IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
INTEGER_RE = re.compile(r"^(?:0|-?[1-9][0-9]*)$")
UNSIGNED_INTEGER_RE = re.compile(r"^(?:0|[1-9][0-9]*)$")
ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
HASH_RE = re.compile(r"^0x[0-9a-fA-F]{64}$")
REVISION_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


class Limits(NamedTuple):
    max_vector_sets: int
    max_vectors_per_set: int
    max_file_bytes: int
    max_aggregate_bytes: int


DEFAULT_LIMITS = Limits(
    max_vector_sets=16,
    max_vectors_per_set=100_000,
    max_file_bytes=8 * 1024 * 1024,
    max_aggregate_bytes=64 * 1024 * 1024,
)


class FileRead(NamedTuple):
    path: Path
    data: bytes
    sha256: str
    device: int
    inode: int
    size: int
    mtime_ns: int


class CheckResult(NamedTuple):
    record: dict[str, Any]
    manifest_sha256: str
    output_sha256: str
    vector_set_count: int
    vector_count: int


class Refusal(Exception):
    """A stable, operator-actionable refusal at the checked-input boundary."""

    def __init__(self, code: str, subject: str, recovery: str):
        self.code = code
        self.subject = _bounded_subject(subject)
        self.recovery = recovery
        super().__init__(f"{code}: {self.subject}")


def _bounded_subject(value: object) -> str:
    text = str(value).replace("\n", " ").replace("\r", " ")
    return text if len(text) <= 256 else text[:253] + "..."


def _refuse(code: str, subject: object, recovery: str) -> None:
    raise Refusal(code, str(subject), recovery)


def _closed_object(
    value: object,
    *,
    required: set[str],
    optional: set[str] = frozenset(),
    subject: str,
    code: str = "HOM-CHECK-SHAPE",
) -> dict[str, Any]:
    if not isinstance(value, dict):
        _refuse(code, subject, "supply a JSON object with the documented fields")
    keys = set(value)
    if keys - required - optional or required - keys:
        _refuse(code, subject, "match the closed version-1 schema exactly")
    return value


def _identifier(value: object, subject: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER_RE.fullmatch(value):
        _refuse("HOM-CHECK-SHAPE", subject, "use a non-empty stable identifier")
    return value


def _text(value: object, subject: str, *, maximum: int = 256) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        _refuse("HOM-CHECK-SHAPE", subject, "supply a bounded non-empty string")
    return value


def _integer(value: object, subject: str, *, unsigned: bool = False) -> str:
    pattern = UNSIGNED_INTEGER_RE if unsigned else INTEGER_RE
    if not isinstance(value, str) or not pattern.fullmatch(value):
        _refuse(
            "HOM-CHECK-INTEGER",
            subject,
            "use a canonical base-10 integer string without padding, exponent or negative zero",
        )
    return value


def _lexical_parts(raw: object, subject: str) -> tuple[str, ...]:
    if not isinstance(raw, str) or not raw or len(raw) > 1024:
        _refuse("HOM-CHECK-PATH", subject, "use one bounded repository-relative path")
    if "\x00" in raw or "\\" in raw:
        _refuse("HOM-CHECK-PATH", subject, "use slash-separated repository-relative path syntax")
    pure = PurePosixPath(raw)
    pieces = tuple(raw.split("/"))
    if pure.is_absolute() or any(piece in {"", ".", ".."} for piece in pieces):
        _refuse("HOM-CHECK-PATH", subject, "remove absolute, empty, dot or parent path components")
    return pieces


def _reject_existing_symlinks(root: Path, path: Path, subject: str) -> None:
    try:
        relative = path.relative_to(root)
    except ValueError:
        _refuse("HOM-CHECK-PATH", subject, "keep the path inside its declared root")
    current = root
    for piece in relative.parts:
        current = current / piece
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            break
        except OSError:
            _refuse("HOM-CHECK-PATH", subject, "make every path component readable")
        if stat.S_ISLNK(metadata.st_mode):
            _refuse("HOM-CHECK-PATH", subject, "replace the symlink with a regular path")


def _safe_path(raw: object, *, base: Path, root: Path, subject: str) -> Path:
    pieces = _lexical_parts(raw, subject)
    candidate = base.joinpath(*pieces)
    _reject_existing_symlinks(root, candidate, subject)
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(base.resolve(strict=True))
        resolved.relative_to(root)
    except (FileNotFoundError, ValueError):
        _refuse("HOM-CHECK-PATH", subject, "keep the path beneath its declared directory")
    return candidate


def _safe_reference(raw: object, subject: str) -> str:
    return PurePosixPath(*_lexical_parts(raw, subject)).as_posix()


def _assert_named_identity(value: FileRead, subject: str) -> None:
    try:
        named = value.path.lstat()
    except OSError:
        _refuse("HOM-CHECK-PATH", subject, "restore the named regular file and retry")
    if stat.S_ISLNK(named.st_mode) or not stat.S_ISREG(named.st_mode):
        _refuse("HOM-CHECK-PATH", subject, "use one non-symlink regular file")
    if (
        named.st_dev != value.device
        or named.st_ino != value.inode
        or named.st_size != value.size
        or named.st_mtime_ns != value.mtime_ns
    ):
        _refuse("HOM-CHECK-PATH", subject, "stop replacing the named input while it is checked")


def _read_bounded_file(path: Path, *, limit: int, subject: str) -> FileRead:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        if error.errno in {errno.ELOOP, errno.ENOENT, errno.ENOTDIR}:
            _refuse("HOM-CHECK-PATH", subject, "supply one existing non-symlink regular file")
        _refuse("HOM-CHECK-READ", subject, "make the declared input readable and retry")

    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            _refuse("HOM-CHECK-PATH", subject, "use one non-symlink regular file")
        if before.st_size > limit:
            _refuse("HOM-CHECK-FILE-CAP", subject, f"reduce the file to at most {limit} bytes")
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(64 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        data = b"".join(chunks)
        if len(data) > limit:
            _refuse("HOM-CHECK-FILE-CAP", subject, f"reduce the file to at most {limit} bytes")
        after = os.fstat(descriptor)
        if (
            after.st_dev != before.st_dev
            or after.st_ino != before.st_ino
            or after.st_size != before.st_size
            or after.st_mtime_ns != before.st_mtime_ns
            or len(data) != after.st_size
        ):
            _refuse("HOM-CHECK-PATH", subject, "stop mutating the input while it is checked")
    except OSError:
        _refuse("HOM-CHECK-READ", subject, "make the declared input stable and readable")
    finally:
        os.close(descriptor)

    value = FileRead(
        path=path,
        data=data,
        sha256=hashlib.sha256(data).hexdigest(),
        device=before.st_dev,
        inode=before.st_ino,
        size=before.st_size,
        mtime_ns=before.st_mtime_ns,
    )
    _assert_named_identity(value, subject)
    return value


def _pairs_no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            _refuse("HOM-CHECK-JSON", key, "remove the duplicate JSON object key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    _refuse("HOM-CHECK-JSON", value, "replace non-finite JSON numbers with declared strings")


def _parse_json(data: bytes, subject: str) -> object:
    try:
        text = data.decode("utf-8", errors="strict")
        return json.loads(
            text,
            object_pairs_hook=_pairs_no_duplicates,
            parse_constant=_reject_constant,
        )
    except Refusal:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        _refuse("HOM-CHECK-JSON", subject, "supply strict UTF-8 JSON with no duplicate keys")


def _scale(value: object, subject: str) -> dict[str, Any]:
    scale = _closed_object(value, required={"id", "decimals"}, subject=subject)
    _identifier(scale["id"], f"{subject}.id")
    decimals = scale["decimals"]
    if isinstance(decimals, bool) or not isinstance(decimals, int) or not 0 <= decimals <= 255:
        _refuse("HOM-CHECK-SHAPE", f"{subject}.decimals", "use an integer from 0 through 255")
    return scale


def _tolerance(value: object, subject: str) -> dict[str, str]:
    tolerance = _closed_object(value, required={"absolute"}, subject=subject)
    _integer(tolerance["absolute"], f"{subject}.absolute", unsigned=True)
    return tolerance


def _validate_pair(value: object) -> dict[str, Any]:
    pair = _closed_object(value, required={"id", "chain", "mirror"}, subject="pair")
    _identifier(pair["id"], "pair.id")
    chain = _closed_object(
        pair["chain"], required={"id", "contract", "function"}, subject="pair.chain"
    )
    _integer(chain["id"], "pair.chain.id", unsigned=True)
    if not isinstance(chain["contract"], str) or not ADDRESS_RE.fullmatch(chain["contract"]):
        _refuse("HOM-CHECK-SHAPE", "pair.chain.contract", "use one 20-byte hexadecimal address")
    _text(chain["function"], "pair.chain.function")
    mirror = _closed_object(
        pair["mirror"], required={"id", "revision", "scale"}, subject="pair.mirror"
    )
    _identifier(mirror["id"], "pair.mirror.id")
    if not isinstance(mirror["revision"], str) or not REVISION_RE.fullmatch(mirror["revision"]):
        _refuse(
            "HOM-CHECK-SHAPE",
            "pair.mirror.revision",
            "pin the mirror as sha256 followed by 64 lowercase hexadecimal digits",
        )
    _scale(mirror["scale"], "pair.mirror.scale")
    return pair


def _validate_provenance(value: object, subject: str) -> dict[str, Any]:
    if not isinstance(value, dict) or not isinstance(value.get("class"), str):
        _refuse("HOM-CHECK-PROVENANCE", subject, "declare one closed provenance object")
    provenance_class = value["class"]
    if provenance_class == "proved":
        provenance = _closed_object(
            value,
            required={"class", "lazarus_artifact"},
            subject=subject,
            code="HOM-CHECK-PROVENANCE",
        )
        _safe_reference(provenance["lazarus_artifact"], f"{subject}.lazarus_artifact")
        return provenance
    if provenance_class == "recorded":
        provenance = _closed_object(
            value,
            required={"class", "chain_id", "block_number", "block_hash"},
            subject=subject,
            code="HOM-CHECK-PROVENANCE",
        )
        try:
            _integer(provenance["chain_id"], f"{subject}.chain_id", unsigned=True)
            _integer(provenance["block_number"], f"{subject}.block_number", unsigned=True)
        except Refusal:
            _refuse("HOM-CHECK-PROVENANCE", subject, "supply canonical chain and block identity")
        if not isinstance(provenance["block_hash"], str) or not HASH_RE.fullmatch(provenance["block_hash"]):
            _refuse("HOM-CHECK-PROVENANCE", subject, "supply one 32-byte hexadecimal block hash")
        return provenance
    if provenance_class == "asserted":
        provenance = _closed_object(
            value,
            required={"class", "author"},
            subject=subject,
            code="HOM-CHECK-PROVENANCE",
        )
        try:
            _text(provenance["author"], f"{subject}.author")
        except Refusal:
            _refuse("HOM-CHECK-PROVENANCE", subject, "name the author of the asserted answer")
        return provenance
    _refuse("HOM-CHECK-PROVENANCE", subject, "use proved, recorded or asserted")


def _validate_vector(
    value: object,
    *,
    set_id: str,
    position: int,
    declared_tolerance: dict[str, str] | None,
) -> dict[str, Any]:
    subject = f"vector_sets.{set_id}.vectors.{position}"
    vector = _closed_object(
        value,
        required={"id", "inputs", "expected"},
        optional={"tolerance"},
        subject=subject,
    )
    vector_id = _identifier(vector["id"], f"{subject}.id")
    inputs = vector["inputs"]
    if not isinstance(inputs, dict) or not inputs:
        _refuse("HOM-CHECK-SHAPE", f"{subject}.inputs", "supply at least one named integer input")
    for key, integer in inputs.items():
        _identifier(key, f"{subject}.inputs key")
        _integer(integer, f"{subject}.inputs.{key}")
    expected = _closed_object(
        vector["expected"], required={"integer", "provenance"}, subject=f"{subject}.expected"
    )
    _integer(expected["integer"], f"{subject}.expected.integer")
    _validate_provenance(expected["provenance"], f"{subject}.expected.provenance")
    if "tolerance" in vector:
        tolerance = _tolerance(vector["tolerance"], f"{subject}.tolerance")
        if declared_tolerance is None or tolerance != declared_tolerance:
            _refuse(
                "HOM-CHECK-TOLERANCE",
                vector_id,
                "remove the tolerance or make it exactly equal to its vector-set declaration",
            )
    return vector


def _parse_vectors(
    source: FileRead,
    *,
    set_id: str,
    declared_tolerance: dict[str, str] | None,
    limit: int,
) -> list[dict[str, Any]]:
    try:
        text = source.data.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _refuse("HOM-CHECK-JSON", set_id, "supply strict UTF-8 JSON Lines")
    lines = text.splitlines()
    if not lines:
        _refuse("HOM-CHECK-SHAPE", set_id, "supply at least one vector")
    if len(lines) > limit:
        _refuse("HOM-CHECK-VECTOR-CAP", set_id, f"reduce the set to at most {limit} vectors")
    vectors: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, line in enumerate(lines, start=1):
        if not line.strip():
            _refuse("HOM-CHECK-JSON", f"{set_id}:{position}", "remove blank JSONL records")
        vector = _validate_vector(
            _parse_json(line.encode("utf-8"), f"{set_id}:{position}"),
            set_id=set_id,
            position=position,
            declared_tolerance=declared_tolerance,
        )
        vector_id = vector["id"]
        if vector_id in seen:
            _refuse("HOM-CHECK-DUPLICATE", vector_id, "give every vector in the set a unique id")
        seen.add(vector_id)
        vectors.append(vector)
    return vectors


def _canonical_json(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
    ).encode("utf-8")


def _atomic_write(path: Path, data: bytes, *, root: Path, subject: str) -> None:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        _reject_existing_symlinks(root, path, subject)
        if path.exists() and not path.is_file():
            _refuse("HOM-CHECK-PATH", subject, "replace the output target with a regular file path")
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
        )
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass
    except Refusal:
        raise
    except OSError:
        _refuse("HOM-CHECK-OUTPUT", subject, "make the output directory writable and retry")


def check_manifest(
    manifest: str | Path,
    output: str | Path,
    *,
    root: Path | None = None,
    limits: Limits = DEFAULT_LIMITS,
) -> CheckResult:
    """Validate and atomically record one manifest.

    ``manifest`` and ``output`` are repository-relative. ``root`` defaults to
    the current directory. A refusal names its stable code, bounded subject and
    recovery action. Validation finishes before the destination is installed.
    """

    repository_root = (root or Path.cwd()).resolve(strict=True)
    if not repository_root.is_dir():
        _refuse("HOM-CHECK-PATH", repository_root, "use an existing repository directory")
    manifest_path = _safe_path(
        str(manifest), base=repository_root, root=repository_root, subject="manifest"
    )
    output_path = _safe_path(
        str(output), base=repository_root, root=repository_root, subject="output"
    )
    if output_path == manifest_path:
        _refuse("HOM-CHECK-PATH", "output", "choose a destination distinct from every input")
    manifest_source = _read_bounded_file(
        manifest_path, limit=limits.max_file_bytes, subject="manifest"
    )
    aggregate_bytes = manifest_source.size
    manifest_value = _closed_object(
        _parse_json(manifest_source.data, "manifest"),
        required={"schema", "pair", "vector_sets"},
        subject="manifest",
    )
    if manifest_value["schema"] != MANIFEST_SCHEMA:
        _refuse("HOM-CHECK-SHAPE", "manifest.schema", f"use {MANIFEST_SCHEMA}")
    pair = _validate_pair(manifest_value["pair"])
    descriptors = manifest_value["vector_sets"]
    if not isinstance(descriptors, list) or not descriptors:
        _refuse("HOM-CHECK-SHAPE", "manifest.vector_sets", "declare at least one vector set")
    if len(descriptors) > limits.max_vector_sets:
        _refuse(
            "HOM-CHECK-SET-CAP",
            "manifest.vector_sets",
            f"reduce the manifest to at most {limits.max_vector_sets} vector sets",
        )

    checked_sets: list[dict[str, Any]] = []
    sources = [manifest_source]
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    total_vectors = 0
    manifest_directory = manifest_path.parent
    for position, descriptor_value in enumerate(descriptors, start=1):
        descriptor = _closed_object(
            descriptor_value,
            required={"id", "path", "scale"},
            optional={"tolerance"},
            subject=f"manifest.vector_sets.{position}",
        )
        set_id = _identifier(descriptor["id"], f"manifest.vector_sets.{position}.id")
        if set_id in seen_ids:
            _refuse("HOM-CHECK-DUPLICATE", set_id, "give every vector set a unique id")
        seen_ids.add(set_id)
        descriptor_path = PurePosixPath(
            *_lexical_parts(descriptor["path"], f"vector_set.{set_id}.path")
        ).as_posix()
        if descriptor_path in seen_paths:
            _refuse("HOM-CHECK-DUPLICATE", descriptor_path, "declare each vector file once")
        seen_paths.add(descriptor_path)
        vector_path = _safe_path(
            descriptor_path,
            base=manifest_directory,
            root=repository_root,
            subject=f"vector_set.{set_id}.path",
        )
        if output_path == vector_path:
            _refuse("HOM-CHECK-PATH", "output", "choose a destination distinct from every input")
        set_scale = _scale(descriptor["scale"], f"vector_set.{set_id}.scale")
        if set_scale != pair["mirror"]["scale"]:
            _refuse("HOM-CHECK-SCALE", set_id, "make the set scale exactly equal to the mirror scale")
        declared_tolerance = None
        if "tolerance" in descriptor:
            declared_tolerance = _tolerance(
                descriptor["tolerance"], f"vector_set.{set_id}.tolerance"
            )
        source = _read_bounded_file(
            vector_path, limit=limits.max_file_bytes, subject=f"vector_set.{set_id}"
        )
        sources.append(source)
        aggregate_bytes += source.size
        if aggregate_bytes > limits.max_aggregate_bytes:
            _refuse(
                "HOM-CHECK-AGGREGATE-CAP",
                set_id,
                f"reduce declared input bytes to at most {limits.max_aggregate_bytes}",
            )
        vectors = _parse_vectors(
            source,
            set_id=set_id,
            declared_tolerance=declared_tolerance,
            limit=limits.max_vectors_per_set,
        )
        total_vectors += len(vectors)
        checked_set: dict[str, Any] = {
            "id": set_id,
            "scale": set_scale,
            "source": {
                "path": vector_path.relative_to(repository_root).as_posix(),
                "sha256": source.sha256,
            },
            "vector_count": len(vectors),
            "vectors": vectors,
        }
        if declared_tolerance is not None:
            checked_set["tolerance"] = declared_tolerance
        checked_sets.append(checked_set)

    for source in sources:
        _assert_named_identity(source, source.path.relative_to(repository_root).as_posix())
    record = {
        "manifest": {
            "path": manifest_path.relative_to(repository_root).as_posix(),
            "sha256": manifest_source.sha256,
        },
        "pair": pair,
        "schema": CHECKED_SCHEMA,
        "summary": {
            "vector_count": total_vectors,
            "vector_set_count": len(checked_sets),
        },
        "vector_sets": checked_sets,
    }
    output_bytes = _canonical_json(record)
    output_sha256 = hashlib.sha256(output_bytes).hexdigest()
    _atomic_write(
        output_path,
        output_bytes,
        root=repository_root,
        subject=output_path.relative_to(repository_root).as_posix(),
    )
    return CheckResult(
        record=record,
        manifest_sha256=manifest_source.sha256,
        output_sha256=output_sha256,
        vector_set_count=len(checked_sets),
        vector_count=total_vectors,
    )


def _emit(value: dict[str, Any]) -> None:
    print(json.dumps(value, sort_keys=True, separators=(",", ":")), file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="homologia",
        description=(
            "Compare one pinned on-chain computation with one pinned off-chain "
            "mirror over declared vectors. A verdict states agreement, never "
            "correctness."
        ),
    )
    parser.add_argument("--version", action="version", version=f"homologia {VERSION}")
    subparsers = parser.add_subparsers(dest="verb")
    check_parser = subparsers.add_parser("check", help=VERBS["check"])
    check_parser.add_argument("--manifest", required=True)
    check_parser.add_argument("--out", required=True)
    for verb in ("run-mirror", "compare", "render", "verify"):
        subparsers.add_parser(verb, help=VERBS[verb])
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.verb is None:
        parser.print_help()
        return 0
    if args.verb == "check":
        try:
            result = check_manifest(args.manifest, args.out)
        except Refusal as refusal:
            _emit(
                {
                    "code": refusal.code,
                    "event": "homologia_check_refused",
                    "recovery": refusal.recovery,
                    "subject": refusal.subject,
                }
            )
            return OUTPUT_REFUSED if refusal.code == "HOM-CHECK-OUTPUT" else INPUT_REFUSED
        _emit(
            {
                "event": "homologia_check_ok",
                "manifest_sha256": result.manifest_sha256,
                "output_sha256": result.output_sha256,
                "vector_count": result.vector_count,
                "vector_set_count": result.vector_set_count,
            }
        )
        return 0
    print(
        f"homologia {args.verb} is not built yet (homologia-v{VERSION}). "
        "See plugins/homologia/docs/homologia-runbook.md.",
        file=sys.stderr,
    )
    return NOT_BUILT


if __name__ == "__main__":
    raise SystemExit(main())
