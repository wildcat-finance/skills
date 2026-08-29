"""Preserved chain reads, held by recomputed request keys.

Berean consumes read records in the Lazarus preservation shape: one JSONL
record per request, keyed by the digest of its canonical method and params,
with the outcome exactly a result or an error and the evidence class one of
the three the preserver assigned. Berean recomputes the key and keeps the
class; it never interprets a method's semantics and never restates recorded
RPC as anything stronger. All records in one reads file belong to one chain
and one block, the fixed-block model the release declares around them.
"""

from . import BereanError
from . import canonical
from . import digests
from . import jsonio

EVIDENCE_CLASSES = ("proof-backed", "header-bound", "recorded-rpc")
REQUIRED_FIELDS = ("schema_version", "request_key", "method", "params", "required", "evidence", "outcome")
OPTIONAL_FIELDS = ("name",)
MAX_RECORDS = 10000


def request_key(method, params):
    """The digest of the canonical request, the same spelling Lazarus uses."""
    jsonio.stated(method, "method")
    if not isinstance(params, list):
        raise BereanError("params is not a list")
    return digests.of_bytes(canonical.encode({"method": method, "params": params}))


def validate_record(record):
    if not isinstance(record, dict):
        raise BereanError("read record is not an object")
    for field in REQUIRED_FIELDS:
        if field not in record:
            raise BereanError(f"read record is missing {field}")
    unknown = [f for f in record if f not in REQUIRED_FIELDS + OPTIONAL_FIELDS]
    if unknown:
        raise BereanError(f"read record carries undeclared fields: {', '.join(sorted(unknown))}")
    if record["schema_version"] != 1:
        raise BereanError(f"read record schema_version is {record['schema_version']!r}, not 1")
    if not isinstance(record["required"], bool):
        raise BereanError("read record required is not a boolean")
    if record["evidence"] not in EVIDENCE_CLASSES:
        raise BereanError(f"unknown evidence class: {record['evidence']!r}")
    outcome = record["outcome"]
    if not isinstance(outcome, dict) or set(outcome) not in ({"result"}, {"error"}):
        raise BereanError("read outcome is not exactly a result or an error")
    if "error" in outcome:
        error = outcome["error"]
        if not isinstance(error, dict) or "code" not in error or "message" not in error:
            raise BereanError("read error outcome is missing code or message")
    expected = request_key(record["method"], record["params"])
    digests.check_hex(record["request_key"], "request_key")
    if record["request_key"] != expected:
        raise BereanError(
            f"request_key does not match the canonical request: {record['request_key']}"
        )
    return record


def load(path):
    """Read a reads file into a mapping keyed by request key.

    The file is sorted by request key with no duplicates, the same discipline
    the preserver writes with, so one spelling of the file exists.
    """
    import os

    if os.path.islink(path):
        raise BereanError(f"refusing symlink: {path}")
    if not os.path.isfile(path):
        raise BereanError(f"not a regular file: {path}")
    if os.stat(path).st_size > jsonio.MAX_JSON_BYTES:
        raise BereanError(f"reads file over the {jsonio.MAX_JSON_BYTES} byte ceiling")
    records = {}
    previous = None
    with open(path, "r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                raise BereanError(f"blank line in reads file at line {number}")
            record = validate_record(jsonio.loads(line, f"read record at line {number}"))
            key = record["request_key"]
            if key in records:
                raise BereanError(f"duplicate request_key at line {number}: {key}")
            if previous is not None and key < previous:
                raise BereanError(f"reads file is not sorted by request_key at line {number}")
            previous = key
            records[key] = record
    if not records:
        raise BereanError(f"reads file is empty: {path}")
    if len(records) > MAX_RECORDS:
        raise BereanError(f"reads file over the {MAX_RECORDS} record ceiling")
    return records
