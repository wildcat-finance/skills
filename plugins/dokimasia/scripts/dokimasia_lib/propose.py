"""Draft a disposition set a reviewer edits rather than authors from nothing.

The first scrutiny of a real release scoped 261 items and found none carrying a
disposition, because writing them meant 261 hand-authored entries. This module
writes the draft. It decides nothing: every entry it emits is unconfirmed, and
only a person's confirmation admits one as a disposition. See ADR-002.

`covered` is never drafted. That is not a rule applied at the end but the
absence of a code path: `DRAFTABLE` holds the two states this module can emit,
every branch below selects from it, and a test asserts both the module source
and every driven branch. `covered` asserts that a reviewed oracle exists and
something is held to it, which is a judgement about whether an oracle was any
good, and no tool makes it.

Regeneration is the ordinary case, because a frontend changes and the
denominator changes with it. An entry a person confirmed or edited is carried
forward byte for byte; only untouched drafts are replaced. An edit is found by
comparing an entry against the digest of the draft it came from, and an entry
carrying no such digest is treated as hand-written, because the conservative
reading of an unknown provenance is that a person wrote it.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from . import reconcile as reconcile_lib
from . import schema as schema_lib

SCHEMA = "dokimasia-dispositions/v1"

# The two states a draft may take. `covered` is absent by construction, not by
# a filter, so there is no branch to take and nothing to disable.
DRAFTABLE = ("manual", "excluded")

MAX_REASON_BYTES = reconcile_lib.MAX_REASON_BYTES
MAX_DISPOSITIONS = reconcile_lib.MAX_DISPOSITIONS

# One template per item kind. Each quotes only fields the record in front of it
# holds and asserts nothing about an outcome: no status, no result, no
# judgement. Every one opens with `drafted from`, so an entry nobody has edited
# is recognisable as a draft when read on its own, away from `confirmed`.
CASE_TEMPLATE = (
    "drafted from workbook row {sheet}:{row}, identifier {identifier}; "
    "a reviewer owns this row"
)
ITEM_TEMPLATE = "drafted from the compiled {kind} at {source}; no reviewed case cites it"
KIND_NAMES = {
    "route": "page route",
    "api": "API handler",
    "action": "server action",
    "guard": "guard",
}


class ProposeError(Exception):
    """One named refusal while drafting or regenerating a proposal."""


def entry_digest(entry: dict) -> str:
    """The digest of a drafted entry, over everything the generator decided.

    `confirmed` and `proposed_sha256` are excluded: a reviewer confirming an
    entry has not edited what it says, and the digest cannot cover itself.
    """
    body = {
        key: value for key, value in entry.items()
        if key not in ("confirmed", "proposed_sha256")
    }
    return hashlib.sha256(
        json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _reason_for(scoped: dict) -> str:
    """The drafted reason for one scoped item, from what its record says."""
    if scoped["side"] == "workbook":
        sheet, _, row = scoped["source"].rpartition(":")
        reason = CASE_TEMPLATE.format(
            sheet=sheet, row=row, identifier=scoped["id"].split(":", 1)[1]
        )
    else:
        reason = ITEM_TEMPLATE.format(
            kind=KIND_NAMES.get(scoped["kind"], scoped["kind"]),
            source=scoped["source"],
        )
    if not reason.strip():
        raise ProposeError(
            f"the template for {scoped['id']!r} produced an empty reason"
        )
    if len(reason.encode("utf-8")) > MAX_REASON_BYTES:
        raise ProposeError(
            f"the drafted reason for {scoped['id']!r} is over the "
            f"{MAX_REASON_BYTES}-byte cap"
        )
    return reason


def draft_entry(scoped: dict) -> dict:
    """One unconfirmed entry for one scoped item.

    A workbook case is drafted `manual`: it is a row a person wrote and walks,
    and nothing else can be said about it from the record alone.

    An inventory item is drafted `excluded`, which is the conservative
    direction. Drafting it `manual` would assert that a person owns it, which
    is the claim the reviewer is there to make. `excluded` asserts the weaker
    thing, that nothing in the reviewed workbook reaches it, and puts the item
    on the exclusion list, which ADR-001 says is the list a reviewer reads to
    audit the denominator. Both mistakes cost one edit; this one is louder.
    """
    state = "manual" if scoped["side"] == "workbook" else "excluded"
    if state not in DRAFTABLE:  # pragma: no cover - guards the table above
        raise ProposeError(f"{state!r} is not a state this module may draft")
    entry = {
        "item": scoped["id"],
        "disposition": state,
        "reason": _reason_for(scoped),
        "oracle": "",
        "confirmed": False,
    }
    entry["proposed_sha256"] = entry_digest(entry)
    return entry


def _touched(entry: dict) -> bool:
    """Did a person confirm or edit this entry?

    An entry with no recorded draft digest is treated as touched. It was either
    written by hand or produced before the field existed, and neither is
    something to overwrite.
    """
    if entry.get("confirmed"):
        return True
    recorded = entry.get("proposed_sha256")
    if not recorded:
        return True
    return entry_digest(entry) != recorded


def propose(
    inventory: dict,
    workbook: dict,
    existing: dict | None = None,
    skill_version: str | None = None,
) -> tuple[dict, dict]:
    """The drafted set and a count of what regeneration did to it.

    Refuses rather than writing anything when a touched entry cannot be carried
    forward, so a reviewer's file is never partly rewritten.
    """
    scoped = reconcile_lib.scoped_set(inventory, workbook)
    if len(scoped) > MAX_DISPOSITIONS:
        raise ProposeError(
            f"the scoped set holds more than the {MAX_DISPOSITIONS}-item cap"
        )
    known = {entry["id"] for entry in scoped}

    kept: dict[str, dict] = {}
    dropped: list[str] = []
    # Every item the existing set answered for, whatever became of the entry.
    # Checking `kept` and `dropped` alone would miss a duplicate between two
    # untouched drafts, which are in neither.
    seen: set[str] = set()
    if existing is not None:
        if existing.get("schema") != SCHEMA:
            raise ProposeError(
                f"the existing set declares schema {existing.get('schema')!r}, "
                f"not {SCHEMA!r}"
            )
        entries = existing.get("dispositions", [])
        if not isinstance(entries, list):
            raise ProposeError("the existing set holds no dispositions list")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ProposeError(f"existing dispositions[{index}] is not an object")
            target = entry.get("item", "")
            if not target:
                raise ProposeError(f"existing dispositions[{index}] names no item")
            if target in seen:
                raise ProposeError(
                    f"the existing set answers for {target!r} twice, so which "
                    "entry to carry forward is not stated"
                )
            seen.add(target)
            if target not in known:
                # The item left the scoped set. A touched entry is reported
                # rather than silently discarded, because somebody decided it.
                dropped.append(target)
                continue
            if _touched(entry):
                kept[target] = entry

    proposed: list[dict] = []
    replaced = 0
    added = 0
    # `seen` already holds every item the existing set answered for, so the
    # replaced-or-added decision is a set membership rather than a walk of
    # that list once per scoped item. The declared cap admits 40,000 entries
    # on each side, which is the same shape S2-R1-01 recorded in the
    # reconciler and is worth not reintroducing here.
    for scoped_entry in scoped:
        target = scoped_entry["id"]
        if target in kept:
            proposed.append(kept[target])
            continue
        proposed.append(draft_entry(scoped_entry))
        if existing is None:
            added += 1
        elif target in seen:
            replaced += 1
        else:
            added += 1

    record = {
        "schema": SCHEMA,
        "inventory_sha256": inventory.get("inventory_sha256", ""),
        "workbook_sha256": workbook.get("workbook_sha256", ""),
        "dispositions": proposed,
    }
    if skill_version:
        record["generated_by"] = skill_version
    # The set is validated before it reaches the reviewer's disk, so no
    # invalid set is ever written for somebody to read and trust.
    breaches = schema_lib.check(record)
    if breaches:
        raise ProposeError(
            "the drafted set breaches its schema: " + "; ".join(breaches[:4])
        )
    counts = {
        "scoped": len(scoped),
        "preserved": len(kept),
        "replaced": replaced,
        "added": added,
        "dropped": len(dropped),
        "dropped_items": sorted(dropped),
    }
    return record, counts


def write_set(record: dict, path: Path) -> None:
    """Stage beside the target and rename, so a killed run leaves one file."""
    if path.is_symlink():
        raise ProposeError(f"{path} is a symlink")
    if path.exists() and not path.is_file():
        raise ProposeError(f"{path} exists and is not a regular file")
    body = json.dumps(record, indent=2, sort_keys=True) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.parent / f".{path.name}.{os.getpid()}.tmp"
    staging.write_text(body, encoding="utf-8")
    os.replace(staging, path)


def fixture_root() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "dispositions"


def check() -> list[str]:
    """Prove this module's contract against the committed fixtures."""
    failures: list[str] = []
    root = fixture_root()
    try:
        inventory = reconcile_lib.read_json(root / "inventory.json")
        workbook = reconcile_lib.read_json(root / "workbook.json")
    except reconcile_lib.ReconcileError as error:
        return [f"the propose fixtures are unreadable: {error}"]

    drafted, counts = propose(inventory, workbook)
    scoped = reconcile_lib.scoped_set(inventory, workbook)
    if len(drafted["dispositions"]) != len(scoped):
        failures.append("the drafted set does not cover every scoped item")
    if counts["added"] != len(scoped) or counts["preserved"]:
        failures.append("a first draft reported something other than all new entries")

    states = {entry["disposition"] for entry in drafted["dispositions"]}
    if not states <= set(DRAFTABLE):
        failures.append(f"the drafted set emitted {sorted(states - set(DRAFTABLE))}")
    if any(entry["confirmed"] for entry in drafted["dispositions"]):
        failures.append("a drafted entry arrived confirmed")
    for entry in drafted["dispositions"]:
        if not entry["reason"].strip():
            failures.append(f"drafted {entry['item']!r} carries no reason")
        if entry["oracle"]:
            failures.append(f"drafted {entry['item']!r} names an oracle")

    # A drafted set answers for nothing until somebody confirms it.
    made = reconcile_lib.reconcile(inventory, workbook, drafted)
    if made["closure_ratio"]["numerator"] != 0:
        failures.append("a freshly drafted set disposed of something")
    if made["counts"]["unconfirmed"] != len(scoped):
        failures.append("the reconciler did not name every draft as unconfirmed")

    # A reviewer's edits survive a regeneration.
    edited = json.loads(json.dumps(drafted))
    edited["dispositions"][0]["confirmed"] = True
    edited["dispositions"][1]["reason"] = "a person wrote this instead"
    confirmed_bytes = json.dumps(edited["dispositions"][0], sort_keys=True)
    edited_bytes = json.dumps(edited["dispositions"][1], sort_keys=True)
    again, recount = propose(inventory, workbook, edited)
    by_item = {entry["item"]: entry for entry in again["dispositions"]}
    if json.dumps(by_item[edited["dispositions"][0]["item"]], sort_keys=True) != confirmed_bytes:
        failures.append("a confirmed entry did not survive regeneration")
    if json.dumps(by_item[edited["dispositions"][1]["item"]], sort_keys=True) != edited_bytes:
        failures.append("an edited entry did not survive regeneration")
    if recount["preserved"] != 2:
        failures.append(f"regeneration preserved {recount['preserved']} entries, not 2")
    if recount["replaced"] != len(scoped) - 2:
        failures.append("regeneration did not replace every untouched draft")

    # Two drafts of the same records agree.
    twice, _ = propose(inventory, workbook)
    if json.dumps(twice, sort_keys=True) != json.dumps(drafted, sort_keys=True):
        failures.append("two drafts of the same records disagreed")

    failures.extend(
        f"the drafted set breaches its schema: {line}"
        for line in schema_lib.check(drafted)
    )
    return failures
