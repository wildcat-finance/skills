"""Stable address queries over a verified Alexandria index."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import re
import sqlite3

from .canonical import canonical_bytes
from .errors import AlexandriaError
from .index import SQLITE_INTEGER_MAX, close_index, inspect_index
from .release import CHAIN_RE


QUERY_FORMAT = "alexandria-address-query/v1"
ADDRESS_RE = re.compile(r"^0x[0-9a-f]{40}$")


def query(index_path, addresses, *, venues=(), chain=None, time_start=None, time_end=None):
    addresses = sorted({_address(item) for item in addresses})
    if not addresses:
        raise AlexandriaError("query requires at least one address")
    venues = sorted(set(venues))
    if chain is not None and (not isinstance(chain, str) or not CHAIN_RE.fullmatch(chain)):
        raise AlexandriaError("query chain must be a canonical eip155 id")
    time_start = _time(time_start, "from time")
    time_end = _time(time_end, "to time")
    if time_start is not None and time_end is not None and time_start > time_end:
        raise AlexandriaError("query from time is after its to time")

    checked = inspect_index(index_path)
    connection = checked["connection"]
    try:
        events = _rows(
            connection, "credit_events", addresses, venues, chain, time_start, time_end
        )
        observations = _rows(
            connection, "position_observations", addresses, venues, chain, time_start, time_end
        )
        coverage = _coverage(
            connection, addresses, venues, chain, time_start, time_end,
            events + observations,
        )
        release_ids = [
            row[0] for row in connection.execute(
                "SELECT release_id FROM releases WHERE active = 1 ORDER BY release_id"
            )
        ]
        return {
            "coverage": coverage,
            "events": events,
            "format": QUERY_FORMAT,
            "index": {
                "logical_digest": checked["logical_digest"],
                "release_ids": release_ids,
            },
            "observations": observations,
            "request": {
                "addresses": addresses,
                "chain": chain,
                "from_time": None if time_start is None else str(time_start),
                "to_time": None if time_end is None else str(time_end),
                "venues": venues,
            },
        }
    except sqlite3.Error as exc:
        raise AlexandriaError(f"SQLite query failed: {exc}") from exc
    finally:
        close_index(checked)


def query_bytes(*args, **kwargs):
    return canonical_bytes(query(*args, **kwargs))


def _rows(connection, table, addresses, venues, chain, time_start, time_end):
    clauses = ["r.active = 1", f"x.address IN ({','.join('?' for _ in addresses)})"]
    parameters = list(addresses)
    if venues:
        clauses.append(f"x.venue IN ({','.join('?' for _ in venues)})")
        parameters.extend(venues)
    if chain is not None:
        clauses.append("x.chain = ?")
        parameters.append(chain)
    if time_start is not None:
        clauses.append("x.observed_at IS NOT NULL AND x.observed_at >= ?")
        parameters.append(time_start)
    if time_end is not None:
        clauses.append("x.observed_at IS NOT NULL AND x.observed_at <= ?")
        parameters.append(time_end)
    sql = (
        "SELECT release_id, row_id, row_json FROM ("
        f"SELECT x.release_id, x.row_id, x.row_json, x.observed_at, "
        "x.block_number, x.venue, ROW_NUMBER() OVER ("
        "PARTITION BY x.row_id ORDER BY r.created_at DESC, x.release_id DESC"
        f") AS row_rank FROM {table} x "
        "JOIN releases r ON r.release_id = x.release_id WHERE "
        + " AND ".join(clauses)
        + ") WHERE row_rank = 1 "
        "ORDER BY observed_at, block_number, venue, row_id, release_id"
    )
    return [
        {
            "release_id": release_id,
            "row": json.loads(row_json),
            "row_id": row_id,
        }
        for release_id, row_id, row_json in connection.execute(sql, parameters)
    ]


def _coverage(connection, addresses, venues, chain, time_start, time_end, rows):
    clauses = ["r.active = 1"]
    parameters = []
    if venues:
        clauses.append(f"c.venue IN ({','.join('?' for _ in venues)})")
        parameters.extend(venues)
    captures = [
        (release_id, json.loads(capture_json), json.loads(mapping_json))
        for release_id, capture_json, mapping_json in connection.execute(
            "SELECT c.release_id, c.capture_json, c.mapping_json FROM captures c "
            "JOIN releases r ON r.release_id = c.release_id WHERE "
            + " AND ".join(clauses)
            + " ORDER BY c.venue, c.chain, c.release_id, c.capture_id",
            parameters,
        )
    ]
    if chain is None:
        keys = {(capture["venue"], capture["chain"]) for _, capture, _ in captures}
    else:
        keys = {(capture["venue"], chain) for _, capture, _ in captures}
    if venues:
        for venue in venues:
            chains = [chain] if chain is not None else sorted({
                capture["chain"] for _, capture, _ in captures if capture["venue"] == venue
            }) or [None]
            keys.update((venue, item) for item in chains)
    groups = []
    for venue, capture_chain in sorted(keys, key=lambda item: (item[0], item[1] or "")):
        matching = [
            (release_id, capture, mapping)
            for release_id, capture, mapping in captures
            if capture["venue"] == venue and capture["chain"] == capture_chain
        ]
        address_coverage = {
            address: any(
                _capture_covers(capture, mapping, address, time_start, time_end)
                for _, capture, mapping in matching
            )
            for address in addresses
        }
        any_scope = any(
            _scope_matches(capture, address)
            for _, capture, _ in matching
            for address in addresses
        )
        fully_covered = bool(matching) and all(address_coverage.values())
        status = "covered" if fully_covered else ("partial" if any_scope else "uncovered")
        row_count = sum(
            item["row"]["venue"] == venue and item["row"]["chain"] == capture_chain
            for item in rows
        )
        groups.append({
            "captures": [
                {
                    "capture": capture,
                    "mapping": mapping,
                    "release_id": release_id,
                    "source_release_id": _source_release(connection, release_id),
                }
                for release_id, capture, mapping in matching
            ],
            "chain": capture_chain,
            "empty_allowed": fully_covered,
            "records": row_count,
            "requested_addresses": address_coverage,
            "status": status,
            "venue": venue,
        })
    return groups


def _source_release(connection, release_id):
    return connection.execute(
        "SELECT source_release_id FROM releases WHERE release_id = ?", (release_id,)
    ).fetchone()[0]


def _capture_covers(capture, mapping, address, time_start, time_end):
    if capture["coverage"]["status"] != "complete":
        return False
    if mapping["coverage"]["unsupported_records"]:
        return False
    if not _scope_matches(capture, address):
        return False
    if time_start is None and time_end is None:
        return True
    interval = capture["scope"]["interval"]
    if interval["kind"] != "snapshot":
        return False
    if time_start is not None and time_end is None:
        return False
    snapshot = int(
        datetime.strptime(interval["observed_at"], "%Y-%m-%dT%H:%M:%SZ")
        .replace(tzinfo=timezone.utc)
        .timestamp()
    )
    return time_end is None or time_end <= snapshot


def _scope_matches(capture, address):
    scope = capture["scope"]
    if scope["kind"] == "full-dataset":
        return True
    account = f"{capture['chain']}:{address}"
    return account in scope["subjects"]


def _address(value):
    if not isinstance(value, str):
        raise AlexandriaError("query address must be text")
    value = value.strip().lower()
    if not ADDRESS_RE.fullmatch(value):
        raise AlexandriaError(f"query address is not a 20-byte EVM address: {value!r}")
    return value


def _time(value, label):
    if value is None:
        return None
    if isinstance(value, bool):
        raise AlexandriaError(f"{label} must be a non-negative integer")
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise AlexandriaError(f"{label} must be a non-negative integer") from exc
    if result < 0 or result > SQLITE_INTEGER_MAX or str(result) != str(value):
        raise AlexandriaError(f"{label} must be a canonical non-negative integer")
    return result
