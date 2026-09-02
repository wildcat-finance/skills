"""Deterministic in-toto statements for verified Probitas dossiers."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


STATEMENT_TYPE = "https://in-toto.io/Statement/v1"
PREDICATE_TYPE = "https://ariadne.wildcat.finance/probitas-dossier/v1"
MAX_STATEMENT_BYTES = 8 * 1024 * 1024

_SKILL = Path(__file__).resolve().parents[2] / "skills" / "probitas" / "SKILL.md"
_VERSION = re.compile(r'^  version: "([^"]+)"$', re.MULTILINE)


class StatementError(ValueError):
    """The verified inputs cannot be projected into a Probitas statement."""


def digest(data: bytes) -> dict[str, str]:
    """Return one in-toto SHA-256 digest for exact input bytes."""
    if not isinstance(data, bytes):
        raise StatementError("statement inputs must be bytes")
    return {"sha256": hashlib.sha256(data).hexdigest()}


def skill_version() -> str:
    """Read the canonical Probitas skill's declared behavioural version."""
    match = _VERSION.search(_SKILL.read_text(encoding="utf-8"))
    if match is None:
        raise StatementError("Probitas SKILL.md has no metadata version")
    return match.group(1)


def _passed_gate_results(results):
    results = list(results)
    if (
        len(results) != 5
        or [getattr(result, "number", None) for result in results]
        != [1, 2, 3, 4, 5]
        or any(not getattr(result, "passed", False) for result in results)
    ):
        raise StatementError(
            "all five gates must pass in gate order before a statement is emitted"
        )
    return results


def statement_for(dossier_bytes: bytes, evidence_bytes: bytes, results) -> dict:
    """Project exact checked bytes and passed gates into Statement v1."""
    results = _passed_gate_results(results)
    dossier_digest = digest(dossier_bytes)
    evidence_digest = digest(evidence_bytes)
    claims = [
        {
            "name": f"probitas gate {result.number} {result.name}",
            "subject": dossier_digest,
            "disposition": "passed",
        }
        for result in results
    ]
    return {
        "_type": STATEMENT_TYPE,
        "subject": [
            {"name": "dossier", "digest": dossier_digest},
            {"name": "evidence", "digest": evidence_digest},
        ],
        "predicateType": PREDICATE_TYPE,
        "predicate": {
            "dossier": {
                "digest": dossier_digest,
                "bytes": len(dossier_bytes),
            },
            "evidence": {
                "digest": evidence_digest,
                "bytes": len(evidence_bytes),
                "schema": 2,
            },
            "tool": {"name": "probitas", "version": skill_version()},
            "claims": claims,
            "commands": [],
        },
    }


def canonical_bytes(value) -> bytes:
    """Serialise JSON in the canonical form shared by statement emitters."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        + "\n"
    ).encode("utf-8")


def emit_statement(
    dossier_bytes: bytes,
    evidence_bytes: bytes,
    results,
    output: Path,
) -> dict:
    """Atomically write one canonical statement for an all-passing verify run."""
    statement = statement_for(dossier_bytes, evidence_bytes, results)
    body = canonical_bytes(statement)
    if len(body) > MAX_STATEMENT_BYTES:
        raise StatementError(
            "Probitas statement exceeds Ariadne's "
            f"{MAX_STATEMENT_BYTES}-byte input limit"
        )
    _atomic_write(Path(output), body)
    return statement


def _atomic_write(output: Path, body: bytes) -> None:
    descriptor = None
    temporary = None
    try:
        descriptor, temporary = tempfile.mkstemp(
            prefix=f".{output.name}.tmp-",
            dir=output.parent,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, output)
        temporary = None
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if temporary is not None:
            try:
                os.unlink(temporary)
            except FileNotFoundError:
                pass
