#!/usr/bin/env python3
"""Historical custody for recorded success-criteria observations.

The execution adapter owns one attempt.  This module owns the small amount of
history around those attempts: which joined descriptor set was active, which
source digests it described, and which amendments were allowed to follow it.
It is deliberately read-only.  A caller can build a candidate receipt, but a
receipt is admitted only after its previous bytes and completed descriptors
have been checked.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Callable, Iterable


SCHEMA = "protasis-success-criteria-receipts/v1"
VERSION_SCHEMA = "protasis-success-criteria-receipt-version/v1"
AMENDMENT_SCHEMA = "protasis-success-criteria-amendment/v1"
TERMINAL_SCHEMA = "protasis-success-criteria-terminal/v1"
JOIN_SCHEMA = "protasis-success-criteria-join/v1"
SHA256 = re.compile(r"^[0-9a-f]{64}$")
OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
MAX_VERSIONS = 500
MAX_ATTEMPTS = 512
MAX_RECEIPT_BYTES = 4 * 1024 * 1024


class Refusal(ValueError):
    """The historical receipt cannot be admitted without weakening custody."""


def canonical(value) -> bytes:
    try:
        return (json.dumps(value, ensure_ascii=True, sort_keys=True,
                           separators=(",", ":"), allow_nan=False) + "\n").encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise Refusal("receipt-json") from exc


def digest(value) -> str:
    """Digest a value's canonical JSON, or bytes when supplied."""
    if isinstance(value, bytes):
        data = value
    else:
        data = canonical(value)
    return hashlib.sha256(data).hexdigest()


def _sha(value, label):
    if not isinstance(value, str) or SHA256.fullmatch(value) is None:
        raise Refusal(label)
    return value


def _object_id(value, label):
    if not isinstance(value, str) or OBJECT_ID.fullmatch(value) is None:
        raise Refusal(label)
    return value


def _copy(value):
    try:
        return json.loads(canonical(value))
    except (TypeError, ValueError, RecursionError) as exc:
        raise Refusal("receipt-json") from exc


def _rows(join):
    if not isinstance(join, dict) or join.get("schema") != JOIN_SCHEMA:
        raise Refusal("join-schema")
    rows = join.get("criteria")
    if not isinstance(rows, list) or not rows:
        raise Refusal("join-criteria")
    if len(rows) > 128:
        raise Refusal("join-criteria-count")
    seen = set()
    result = []
    for row in rows:
        if not isinstance(row, dict):
            raise Refusal("join-row")
        identifier = row.get("id")
        if not isinstance(identifier, str) or not identifier or identifier in seen:
            raise Refusal("join-id")
        if type(row.get("step")) is not int or row["step"] < 1:
            raise Refusal("join-step")
        if not isinstance(row.get("claim"), str) or not row["claim"].strip():
            raise Refusal("join-claim")
        if not isinstance(row.get("command"), str) or not row["command"].strip():
            raise Refusal("join-command")
        if not isinstance(row.get("descriptor_sha256"), str):
            raise Refusal("join-descriptor-digest")
        _sha(row["descriptor_sha256"], "join-descriptor-digest")
        exit_record = row.get("exit")
        if not isinstance(exit_record, dict):
            raise Refusal("join-exit")
        if exit_record.get("command") != row["command"] or exit_record.get("step") != row["step"]:
            raise Refusal("join-exit-binding")
        if not isinstance(exit_record.get("command_sha256"), str):
            raise Refusal("join-command-digest")
        _sha(exit_record["command_sha256"], "join-command-digest")
        seen.add(identifier)
        result.append(row)
    return result


def validate_join(join):
    """Return a detached, strictly checked joined descriptor set."""
    rows = _rows(join)
    copy = _copy(join)
    _rows(copy)
    return copy


def join_digest(join) -> str:
    return digest(validate_join(join))


def _descriptor_identity(row):
    """Fields that cannot change after that descriptor has settled."""
    if not isinstance(row, dict):
        raise Refusal("descriptor-row")
    exit_record = row.get("exit")
    if not isinstance(exit_record, dict):
        raise Refusal("descriptor-exit")
    # ``offset`` and adapter ``source`` metadata locate the command in one
    # runbook revision; an unrelated amendment may move either without
    # changing the admitted descriptor.  The command, step and their digest
    # are the immutable Exit identity.
    exit_identity = (
        exit_record.get("step"),
        exit_record.get("command"),
        exit_record.get("command_sha256"),
    )
    return (
        row.get("id"), row.get("claim"), row.get("step"), row.get("command"),
        row.get("descriptor_sha256"),
        exit_identity,
    )


def descriptor_identity(row):
    """Public immutable projection used when an active row follows history."""
    return _descriptor_identity(row)


def descriptor_unchanged(left, right) -> bool:
    return _descriptor_identity(left) == _descriptor_identity(right)


def _completed_ids(attempts: Iterable[dict]) -> set[str]:
    result = set()
    for attempt in attempts:
        if not isinstance(attempt, dict):
            raise Refusal("attempt-record")
        if attempt.get("settled") is not True or attempt.get("status") != "settled":
            continue
        identifiers = attempt.get("criterion_ids")
        if not isinstance(identifiers, list) or not identifiers:
            raise Refusal("settled-attempt-criteria")
        for identifier in identifiers:
            if not isinstance(identifier, str) or not identifier:
                raise Refusal("settled-attempt-criteria")
            result.add(identifier)
    return result


def _index(join):
    return {row["id"]: row for row in _rows(join)}


def freeze_completed(prior_join, candidate_join, attempts) -> None:
    """Reject removal, reassignment or edits to an already settled row."""
    previous = _index(prior_join)
    candidate = _index(candidate_join)
    for identifier in sorted(_completed_ids(attempts)):
        old = previous.get(identifier)
        new = candidate.get(identifier)
        if old is None:
            raise Refusal("completed-descriptor-not-in-prior-join")
        if new is None:
            raise Refusal("completed-descriptor-removed")
        if _descriptor_identity(old) != _descriptor_identity(new):
            raise Refusal("completed-descriptor-changed")


def _version(join, study_sha256, runbook_sha256, *, kind="initial", amendment_sha256=None):
    _sha(study_sha256, "version-study-digest")
    _sha(runbook_sha256, "version-runbook-digest")
    result = {
        "schema": VERSION_SCHEMA,
        "kind": kind,
        "study_sha256": study_sha256,
        "runbook_sha256": runbook_sha256,
        "join": validate_join(join),
        "join_sha256": join_digest(join),
    }
    if amendment_sha256 is not None:
        result["amendment_sha256"] = _sha(amendment_sha256, "version-amendment-digest")
    return result


def new(admission: dict) -> dict:
    """Wrap an admitted Step 3 record in versioned historical custody."""
    if not isinstance(admission, dict):
        raise Refusal("admission-record")
    join = admission.get("join")
    study = _sha(admission.get("study_sha256"), "admission-study-digest")
    runbook = _sha(admission.get("runbook_sha256"), "admission-runbook-digest")
    result = {
        "schema": SCHEMA,
        "versions": [_version(join, study, runbook)],
        "amendments": [],
    }
    if len(canonical(result)) > MAX_RECEIPT_BYTES:
        raise Refusal("receipt-data-cap")
    return result


def history(receipt: dict) -> list[dict]:
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise Refusal("receipt-schema")
    if set(receipt) != {"schema", "versions", "amendments"}:
        raise Refusal("receipt-fields")
    versions = receipt.get("versions")
    amendments = receipt.get("amendments")
    if not isinstance(versions, list) or not versions or len(versions) > MAX_VERSIONS:
        raise Refusal("receipt-versions")
    if not isinstance(amendments, list) or len(amendments) != len(versions) - 1:
        raise Refusal("receipt-amendments")
    seen_amendments = set()
    checked = []
    for index, version in enumerate(versions):
        if not isinstance(version, dict) or version.get("schema") != VERSION_SCHEMA:
            raise Refusal("receipt-version")
        allowed_version_fields = {
            "schema", "kind", "study_sha256", "runbook_sha256",
            "join", "join_sha256",
        }
        if index > 0:
            allowed_version_fields.add("amendment_sha256")
        if set(version) != allowed_version_fields:
            raise Refusal("receipt-version-fields")
        join = validate_join(version.get("join"))
        if version.get("join_sha256") != join_digest(join):
            raise Refusal("receipt-version-join-digest")
        _sha(version.get("study_sha256"), "version-study-digest")
        _sha(version.get("runbook_sha256"), "version-runbook-digest")
        if index == 0:
            if version.get("kind") != "initial" or "amendment_sha256" in version:
                raise Refusal("receipt-initial-version")
        else:
            amendment = amendments[index - 1]
            if not isinstance(amendment, dict) or amendment.get("schema") != AMENDMENT_SCHEMA:
                raise Refusal("receipt-amendment")
            if set(amendment) != {
                "schema", "kind", "amendment_sha256", "prior_join_sha256",
                "new_join_sha256", "prior_runbook_sha256", "new_runbook_sha256",
                "new_study_sha256",
            }:
                raise Refusal("receipt-amendment-fields")
            if amendment.get("kind") not in {"study", "runbook"}:
                raise Refusal("receipt-amendment-kind")
            if version.get("kind") != amendment.get("kind"):
                raise Refusal("receipt-amendment-kind")
            amendment_digest = _sha(amendment.get("amendment_sha256"), "amendment-digest")
            if amendment_digest in seen_amendments:
                raise Refusal("duplicate-amendment-digest")
            seen_amendments.add(amendment_digest)
            if version.get("amendment_sha256") != amendment_digest:
                raise Refusal("receipt-amendment-binding")
            if amendment.get("prior_join_sha256") != checked[-1]["join_sha256"]:
                raise Refusal("amendment-prior-join")
            if amendment.get("new_join_sha256") != version["join_sha256"]:
                raise Refusal("amendment-new-join")
            if amendment.get("prior_runbook_sha256") != checked[-1]["runbook_sha256"]:
                raise Refusal("amendment-prior-runbook")
            if amendment.get("new_study_sha256") != version["study_sha256"]:
                raise Refusal("amendment-new-study")
            if amendment.get("new_runbook_sha256") != version["runbook_sha256"]:
                raise Refusal("amendment-new-runbook")
        checked.append({**version, "join": join})
    if len(canonical(receipt)) > MAX_RECEIPT_BYTES:
        raise Refusal("receipt-data-cap")
    return checked


def amend(receipt: dict, candidate_join: dict, *, study_sha256: str,
          runbook_sha256: str, amendment_sha256: str, attempts=(), kind="runbook") -> dict:
    """Return a checked candidate receipt for one source amendment.

    The caller writes source bytes and controller state only after this
    preflight succeeds.  Thus a completed descriptor refusal happens before
    mutation and a crash can safely replay the same candidate.
    """
    versions = history(receipt)
    if not isinstance(attempts, list):
        attempts = list(attempts)
    if len(attempts) > MAX_ATTEMPTS:
        raise Refusal("attempt-count")
    _sha(amendment_sha256, "amendment-digest")
    if any(item.get("amendment_sha256") == amendment_sha256
           for item in receipt.get("amendments", [])):
        raise Refusal("duplicate-amendment-digest")
    current = versions[-1]
    candidate = validate_join(candidate_join)
    freeze_completed(current["join"], candidate, attempts)
    amendment_record = {
        "schema": AMENDMENT_SCHEMA,
        "kind": kind,
        "amendment_sha256": amendment_sha256,
        "prior_join_sha256": current["join_sha256"],
        "new_join_sha256": join_digest(candidate),
        "prior_runbook_sha256": current["runbook_sha256"],
        "new_runbook_sha256": _sha(runbook_sha256, "amendment-runbook-digest"),
        "new_study_sha256": _sha(study_sha256, "amendment-study-digest"),
    }
    result = _copy(receipt)
    result["amendments"].append(amendment_record)
    result["versions"].append(_version(
        candidate, study_sha256, runbook_sha256, kind=kind,
        amendment_sha256=amendment_sha256,
    ))
    if len(canonical(result)) > MAX_RECEIPT_BYTES:
        raise Refusal("receipt-data-cap")
    return result


def version_for_attempt(receipt: dict, attempt: dict) -> dict:
    """Select the historical join named by an attempt's source digests."""
    if not isinstance(attempt, dict):
        raise Refusal("attempt-record")
    study = attempt.get("study_sha256")
    runbook = attempt.get("runbook_sha256")
    candidates = [item for item in history(receipt)
                  if item["study_sha256"] == study and item["runbook_sha256"] == runbook]
    if len(candidates) != 1:
        raise Refusal("attempt-source-version")
    return candidates[0]


def replay(receipt: dict, attempts: Iterable[dict], validator: Callable | None = None,
           **kwargs) -> list[dict]:
    """Replay all attempts against their historical joins without execution."""
    attempts = list(attempts)
    if len(attempts) > MAX_ATTEMPTS:
        raise Refusal("attempt-count")
    versions = history(receipt)
    if validator is None:
        validator = kwargs.pop("validate_result", None)
    if validator is None:
        raise Refusal("result-validator")
    observed = []
    for attempt in attempts:
        version = version_for_attempt(receipt, attempt)
        validator(attempt, version["join"], **kwargs)
        observed.append({
            "attempt_id": attempt.get("attempt_id"),
            "join_sha256": version["join_sha256"],
            "study_sha256": version["study_sha256"],
            "runbook_sha256": version["runbook_sha256"],
        })
    return observed


def settled_ids(receipt: dict, attempts: Iterable[dict], validator: Callable | None = None,
                **kwargs) -> set[str]:
    """Return only descriptors backed by a valid, settled historical result."""
    attempts = list(attempts)
    if validator is not None:
        replay(receipt, attempts, validator, **kwargs)
    result = set()
    for attempt in attempts:
        if attempt.get("settled") is True and attempt.get("status") == "settled":
            result.update(_completed_ids([attempt]))
    return result


def require_complete(receipt: dict, attempts: Iterable[dict], *, step=None,
                     validator: Callable | None = None, **kwargs) -> None:
    """Require every active descriptor (or one consuming step) to be settled."""
    versions = history(receipt)
    active = versions[-1]["join"]["criteria"]
    due = [row for row in active if step is None or row.get("step") == step]
    if not due:
        return
    settled = settled_ids(receipt, attempts, validator, **kwargs)
    missing = [row["id"] for row in due if row["id"] not in settled]
    if missing:
        raise Refusal("unmet-criteria:" + ",".join(missing))


def terminal(receipt: dict, attempts: Iterable[dict], *, run_id: str | None = None,
             validator: Callable | None = None, **kwargs) -> dict:
    """Build a final read-only receipt after all active descriptors settle."""
    attempts = list(attempts)
    if run_id is not None and (not isinstance(run_id, str) or not run_id):
        raise Refusal("terminal-run-id")
    require_complete(receipt, attempts, validator=validator, **kwargs)
    versions = history(receipt)
    result = {
        "schema": TERMINAL_SCHEMA,
        "receipt_sha256": digest(receipt),
        "active_join_sha256": versions[-1]["join_sha256"],
        "attempt_count": len(attempts),
        "run_id": run_id,
        "operation_ran": False,
    }
    if len(canonical(result)) > MAX_RECEIPT_BYTES:
        raise Refusal("terminal-data-cap")
    return result


def validate_terminal(result: dict, receipt: dict, attempts: Iterable[dict], *,
                      validator: Callable | None = None, **kwargs) -> dict:
    if not isinstance(result, dict) or result.get("schema") != TERMINAL_SCHEMA:
        raise Refusal("terminal-schema")
    if result.get("operation_ran") is not False:
        raise Refusal("terminal-operation")
    expected = terminal(receipt, attempts, run_id=result.get("run_id"),
                        validator=validator, **kwargs)
    if result != expected:
        raise Refusal("terminal-binding")
    return result


# Descriptive aliases keep the module convenient for controller and proof code.
validate_history = history
record_amendment = amend
replay_attempts = replay
finalize = terminal
