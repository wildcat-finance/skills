"""Disposable SQLite index rebuilt from verified derived releases."""

from __future__ import annotations

import hashlib
from itertools import zip_longest
import json
import os
from pathlib import Path
import sqlite3
import tempfile

from .canonical import MAX_CONTROL_BYTES, canonical_bytes, load_bytes
from .derivation import EVENTS_PATH, MAX_DERIVED_BYTES, OBSERVATIONS_PATH
from .errors import AlexandriaError
from .paths import read_confined_file
from .release import sha256, validate_manifest, verify


INDEX_FORMAT = "alexandria-address-index/v1"
APPLICATION_ID = 1097627721
USER_VERSION = 1
SQLITE_INTEGER_MAX = (1 << 63) - 1
LOGICAL_COLUMNS = {
    # `path` is an operational reference, not logical index content. Querying
    # verifies it before use, while two catalogues of the same release remain
    # logically identical when built in different directories.
    "releases": (
        "release_id", "source_release_id", "manifest_sha256", "release_name",
        "created_at", "active", "manifest_json",
    ),
    "captures": (
        "release_id", "capture_id", "source_release_id", "component",
        "component_sha256", "venue", "chain", "evidence_class", "scope_kind",
        "capture_json", "mapping_json",
    ),
    "credit_events": (
        "release_id", "row_id", "source_release_id", "component",
        "component_sha256", "capture_id", "venue", "chain", "subject", "address",
        "event_family", "observed_at", "block_number", "row_json",
    ),
    "position_observations": (
        "release_id", "row_id", "source_release_id", "component",
        "component_sha256", "capture_id", "venue", "chain", "subject", "address",
        "property", "observed_at", "block_number", "row_json",
    ),
}


def rebuild(releases, output: Path) -> str:
    """Atomically replace an index with the logical contents of releases."""
    release_paths = [Path(item).absolute() for item in releases]
    if not release_paths:
        raise AlexandriaError("index requires at least one derived release")
    references = [_load_reference(path) for path in release_paths]
    superseded = _validate_reference_set(references, "index input")

    output = output.absolute()
    resolved_output = output.resolve(strict=False)
    for release_path in release_paths:
        try:
            resolved_output.relative_to(release_path.resolve(strict=True))
        except ValueError:
            continue
        raise AlexandriaError("index output must not be inside an input release")
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.is_symlink():
        raise AlexandriaError("index output must not be a symlink")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.tmp-", dir=output.parent
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        connection = sqlite3.connect(temporary)
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(_schema_sql())
            for reference in sorted(references, key=lambda item: item["release_id"]):
                path = reference["path"]
                _, manifest, events, observations = _load_release(path)
                if manifest["release_id"] != reference["release_id"]:
                    raise AlexandriaError(
                        f"index input release changed while it was read: {path}"
                    )
                active = int(
                    reference["release_id"] not in superseded
                    and reference["source_release_id"] not in superseded
                )
                _insert_release(connection, path, manifest, active)
                _insert_rows(connection, manifest, events, observations)
            _validate_active_duplicates(connection)
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("format", INDEX_FORMAT),
            )
            connection.execute(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                ("logical_digest", _logical_digest(connection)),
            )
            connection.commit()
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            if result != "ok":
                raise AlexandriaError(f"SQLite integrity check failed: {result}")
        finally:
            connection.close()
        checked = inspect_index(temporary)
        try:
            logical_digest = checked["logical_digest"]
        finally:
            close_index(checked)
        os.replace(temporary, output)
        return logical_digest
    except sqlite3.Error as exc:
        if temporary.exists():
            temporary.unlink()
        raise AlexandriaError(f"cannot rebuild SQLite index: {exc}") from exc
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise


def inspect_index(path: Path):
    """Open an index read-only and match it to every referenced release."""
    path = Path(path).absolute()
    if path.is_symlink() or not path.is_file():
        raise AlexandriaError("index must be a local SQLite file, not a symlink")
    connection = None
    try:
        connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
        connection.execute("PRAGMA query_only = ON")
        connection.execute("PRAGMA trusted_schema = OFF")
    except sqlite3.Error as exc:
        if connection is not None:
            connection.close()
        raise AlexandriaError(f"cannot open SQLite index: {exc}") from exc
    try:
        if connection.execute("PRAGMA application_id").fetchone()[0] != APPLICATION_ID:
            raise AlexandriaError("SQLite file is not an Alexandria index")
        if connection.execute("PRAGMA user_version").fetchone()[0] != USER_VERSION:
            raise AlexandriaError("Alexandria index schema version is unsupported")
        if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise AlexandriaError("SQLite index integrity check failed")
        _validate_schema(connection)
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise AlexandriaError("Alexandria index contains a broken foreign key")
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        if metadata.get("format") != INDEX_FORMAT:
            raise AlexandriaError("Alexandria index format is unsupported")
        expected = metadata.get("logical_digest")
        actual = _logical_digest(connection)
        if expected != actual:
            raise AlexandriaError("Alexandria index logical digest does not match")
        releases = connection.execute(
            "SELECT release_id, path FROM releases ORDER BY release_id"
        ).fetchall()
        if not releases:
            raise AlexandriaError("Alexandria index contains no releases")
        references = []
        for release_id, release_path in releases:
            if not isinstance(release_path, str):
                raise AlexandriaError(
                    f"index has a malformed release path for {release_id}"
                )
            try:
                manifest = _load_manifest(Path(release_path))
            except (AlexandriaError, OSError) as exc:
                raise AlexandriaError(
                    f"index has a stale release reference for {release_id}: {exc}"
                ) from exc
            actual_id = manifest["release_id"]
            if actual_id != release_id:
                raise AlexandriaError(f"index release reference changed for {release_id}")
            references.append(_reference(Path(release_path), manifest))
        superseded = _validate_reference_set(references, "index")
        for reference in sorted(references, key=lambda item: item["release_id"]):
            release_path = reference["path"]
            try:
                item = _load_release(release_path)
            except (AlexandriaError, OSError) as exc:
                raise AlexandriaError(
                    f"index has a stale release reference for "
                    f"{reference['release_id']}: {exc}"
                ) from exc
            if item[1]["release_id"] != reference["release_id"]:
                raise AlexandriaError(
                    f"index release changed while it was read: {reference['release_id']}"
                )
            active = int(
                reference["release_id"] not in superseded
                and reference["source_release_id"] not in superseded
            )
            _compare_release(connection, item, active)
        _validate_active_duplicates(connection)
        return {"connection": connection, "logical_digest": actual, "path": path}
    except sqlite3.Error as exc:
        connection.close()
        raise AlexandriaError(f"SQLite index is malformed: {exc}") from exc
    except Exception:
        connection.close()
        raise


def close_index(index):
    index["connection"].close()


def _load_release(path):
    release_id = verify(path)
    manifest_data = read_confined_file(
        path, "manifest.json", "manifest", max_bytes=MAX_CONTROL_BYTES
    )
    manifest = load_bytes(manifest_data, "manifest")
    if "derivation" not in manifest:
        raise AlexandriaError(f"index input {release_id} is not a derived release")
    events = _load_jsonl(path, EVENTS_PATH)
    observations = _load_jsonl(path, OBSERVATIONS_PATH)
    return path, manifest, events, observations


def _load_manifest(path):
    data = read_confined_file(
        path, "manifest.json", "manifest", max_bytes=MAX_CONTROL_BYTES
    )
    manifest = load_bytes(data, "manifest")
    validate_manifest(manifest)
    if canonical_bytes(manifest) != data:
        raise AlexandriaError("manifest is not canonical JSON")
    identity = dict(manifest)
    claimed = identity.pop("release_id")
    if sha256(canonical_bytes(identity)) != claimed:
        raise AlexandriaError("manifest release identity does not match its content")
    if "derivation" not in manifest:
        raise AlexandriaError(f"index input {claimed} is not a derived release")
    return manifest


def _load_reference(path):
    return _reference(path, _load_manifest(path))


def _reference(path, manifest):
    return {
        "path": path,
        "release_id": manifest["release_id"],
        "source_release_id": manifest["derivation"]["source_release_id"],
        "supersedes": tuple(
            manifest["release"].get("correction", {}).get("supersedes", [])
        ),
    }


def _validate_reference_set(references, label):
    ids = [reference["release_id"] for reference in references]
    if len(ids) != len(set(ids)):
        raise AlexandriaError(f"{label} contains a duplicate release")
    source_ids = [
        reference["source_release_id"] for reference in references
    ]
    if len(source_ids) != len(set(source_ids)):
        raise AlexandriaError(f"{label} contains competing views of one raw release")
    return {
        release_id
        for reference in references
        for release_id in reference["supersedes"]
    }


def _load_jsonl(root, path):
    data = read_confined_file(root, path, path, max_bytes=MAX_DERIVED_BYTES)
    rows = []
    for index, line in enumerate(data.splitlines(keepends=True)):
        rows.append(load_bytes(line, f"{path} row {index}"))
    return rows


def _schema_sql():
    path = Path(__file__).resolve().parents[2] / "schemas" / "address-index-v1.sql"
    return path.read_text(encoding="utf-8")


def _insert_release(connection, path, manifest, active):
    source_release_id = manifest["derivation"]["source_release_id"]
    connection.execute(
        "INSERT INTO releases VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            manifest["release_id"], source_release_id, str(path),
            _sha256(canonical_bytes(manifest)), manifest["release"]["name"],
            manifest["release"]["created_at"], active, _json(manifest),
        ),
    )
    mappings = {
        item["capture_id"]: item for item in manifest["derivation"]["mappings"]
    }
    for capture in manifest["captures"]:
        connection.execute(
            "INSERT INTO captures VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                manifest["release_id"], capture["id"], source_release_id,
                capture["component"], capture["component_sha256"], capture["venue"],
                capture["chain"], capture["evidence_class"], capture["scope"]["kind"],
                _json(capture), _json(mappings[capture["id"]]),
            ),
        )


def _insert_rows(connection, manifest, events, observations):
    release_id = manifest["release_id"]
    for row in events:
        provenance = row["provenance"]
        transaction = row.get("transaction", {})
        connection.execute(
            "INSERT INTO credit_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                release_id, row["id"], provenance["source_release_id"],
                provenance["component"], provenance["component_sha256"],
                provenance["capture_id"], row["venue"], row["chain"], row["subject"],
                row["subject"].rsplit(":", 1)[1], row["event_family"],
                _optional_integer(transaction.get("timestamp")),
                _optional_integer(transaction.get("block_number")), _json(row),
            ),
        )
    for row in observations:
        provenance = row["provenance"]
        boundary = row["observation"]["at"]
        connection.execute(
            "INSERT INTO position_observations VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                release_id, row["id"], provenance["source_release_id"],
                provenance["component"], provenance["component_sha256"],
                provenance["capture_id"], row["venue"], row["chain"], row["subject"],
                row["subject"].rsplit(":", 1)[1], row["observation"]["property"],
                _optional_integer(boundary.get("timestamp")),
                _optional_integer(boundary.get("block_number")), _json(row),
            ),
        )


def _logical_digest(connection):
    digest = hashlib.sha256()
    for table, selected in LOGICAL_COLUMNS.items():
        columns = list(selected)
        order = ", ".join(str(index + 1) for index in range(len(columns)))
        projection = ", ".join(columns)
        for row in connection.execute(f"SELECT {projection} FROM {table} ORDER BY {order}"):
            try:
                encoded = json.dumps(
                    list(row), ensure_ascii=False, separators=(",", ":")
                ).encode()
            except (TypeError, ValueError) as exc:
                raise AlexandriaError(
                    f"Alexandria index table {table} contains a non-JSON value"
                ) from exc
            digest.update(encoded)
            digest.update(b"\n")
    return "sha256:" + digest.hexdigest()


def _validate_schema(connection):
    expected = sqlite3.connect(":memory:")
    try:
        expected.executescript(_schema_sql())
        expected_objects = _schema_objects(expected)
    finally:
        expected.close()
    if _schema_objects(connection) != expected_objects:
        raise AlexandriaError("Alexandria index SQLite schema does not match v1")


def _schema_objects(connection):
    return connection.execute(
        "SELECT type, name, tbl_name, sql FROM sqlite_schema "
        "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
    ).fetchall()


def _compare_release(connection, loaded, active):
    """Match one database partition to one verified release."""
    release_path, manifest, events, observations = loaded
    expected = sqlite3.connect(":memory:")
    try:
        expected.execute("PRAGMA foreign_keys = ON")
        expected.executescript(_schema_sql())
        _insert_release(expected, release_path, manifest, active)
        _insert_rows(expected, manifest, events, observations)
        release_id = manifest["release_id"]
        for table, columns in LOGICAL_COLUMNS.items():
            projection = ", ".join(columns)
            order = ", ".join(str(index + 1) for index in range(len(columns)))
            sql = (
                f"SELECT {projection} FROM {table} WHERE release_id = ? "
                f"ORDER BY {order}"
            )
            missing = object()
            for actual_row, expected_row in zip_longest(
                connection.execute(sql, (release_id,)),
                expected.execute(sql, (release_id,)),
                fillvalue=missing,
            ):
                if actual_row != expected_row:
                    raise AlexandriaError(
                        "Alexandria index logical contents do not match its verified "
                        f"release {release_id}"
                    )
    finally:
        expected.close()


def _validate_active_duplicates(connection):
    for table in ("credit_events", "position_observations"):
        duplicates = connection.execute(
            f"SELECT x.row_id FROM {table} x "
            "JOIN releases r ON r.release_id = x.release_id "
            "WHERE r.active = 1 GROUP BY x.row_id HAVING COUNT(*) > 1 "
            "ORDER BY x.row_id"
        )
        for (row_id,) in duplicates:
            meanings = set()
            for (row_json,) in connection.execute(
                f"SELECT x.row_json FROM {table} x "
                "JOIN releases r ON r.release_id = x.release_id "
                "WHERE r.active = 1 AND x.row_id = ? ORDER BY x.release_id",
                (row_id,),
            ):
                row = json.loads(row_json)
                row.pop("id", None)
                row.pop("provenance", None)
                meanings.add(canonical_bytes(row))
            if len(meanings) != 1:
                raise AlexandriaError(
                    f"active releases disagree about {table} row {row_id}"
                )
    collision = connection.execute(
        "SELECT e.row_id FROM credit_events e "
        "JOIN releases er ON er.release_id = e.release_id "
        "JOIN position_observations o ON o.row_id = e.row_id "
        "JOIN releases orr ON orr.release_id = o.release_id "
        "WHERE er.active = 1 AND orr.active = 1 LIMIT 1"
    ).fetchone()
    if collision is not None:
        raise AlexandriaError(
            f"active event and observation share row id {collision[0]}"
        )


def _json(value):
    return canonical_bytes(value).decode("utf-8").rstrip("\n")


def _sha256(data):
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _optional_integer(value):
    if value is None:
        return None
    result = int(value)
    if result > SQLITE_INTEGER_MAX:
        raise AlexandriaError("row time or block value exceeds SQLite integer range")
    return result
