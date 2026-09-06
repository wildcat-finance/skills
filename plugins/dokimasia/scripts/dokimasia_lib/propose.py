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

Attribution is never drafted and always carried. ADR-003 puts a person on every
confirmed entry and lets it name a row of the set-level rules table, and this
module writes neither field on any branch: `DRAFT_FIELDS` is the whole of what
a draft carries, and the pre-write check refuses a set in which any entry a
draft produced holds more. An attributed entry is a confirmed one, so it is
touched and carried forward byte for byte; the rules table is copied forward
unchanged, including a row nobody applies. When either cannot be carried, the
regeneration refuses before the write and the reviewer's file is untouched.
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

# Everything a draft carries, and nothing else. The attribution fields ADR-003
# adds are named through the reconciler's constants rather than written here,
# so the drafting surface holds no literal that could become a value, and a
# test asserts that of the source.
DRAFT_FIELDS = frozenset(
    ("item", "disposition", "reason", "oracle", "confirmed", "proposed_sha256")
)
ATTRIBUTION_FIELDS = (reconcile_lib.CONFIRMED_BY_FIELD, reconcile_lib.RULE_FIELD)
RULES_FIELD = reconcile_lib.RULES_FIELD

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


def _attributed(entry: dict) -> bool:
    """Does this entry name a person or a rule?"""
    return any(field in entry for field in ATTRIBUTION_FIELDS)


def _carried_table(existing: dict) -> dict | None:
    """The existing set's rules table, copied forward unchanged, or None.

    A row nobody applies is carried too: a stated rule nobody used is
    information about the review, and the reconciler reports it as applied
    zero times rather than refusing it. A table that is not an object cannot
    be carried as a table, so the regeneration refuses rather than writing a
    set the reconciler would refuse.
    """
    if RULES_FIELD not in existing:
        return None
    table = existing[RULES_FIELD]
    if not isinstance(table, dict):
        raise ProposeError(
            f"the existing set's {RULES_FIELD} table is "
            f"{type(table).__name__}, not an object, so it cannot be carried "
            "forward"
        )
    return json.loads(json.dumps(table))


def _check_carried(entry: dict, target: str, table: dict | None) -> None:
    """Refuse an attributed entry the regenerated set could not stand behind.

    The rule an entry names has to be a row of the table travelling with it,
    or the regenerated set would name a rule nothing holds, which is the
    shape the reconciler refuses and the one a dropped table produced once.
    """
    rule = entry.get(reconcile_lib.RULE_FIELD)
    if rule is None:
        return
    if not isinstance(rule, str) or table is None or rule not in table:
        raise ProposeError(
            f"the existing set confirms {target!r} under rule {rule!r}, which "
            f"its {RULES_FIELD} table does not hold, so the attribution "
            "cannot be carried forward"
        )


def _check_drafted(record: dict, kept: dict[str, dict]) -> list[str]:
    """The breaches a set would carry into the reviewer's file, before the write.

    Two rules beyond the committed schema, which admits the attribution fields
    on any entry because it cannot state ADR-003's condition: an entry this
    module drafted carries exactly the draft fields, and an unconfirmed entry,
    drafted or carried, names nobody. Either breach means a draft has been
    attributed, which is the thing no generator may do.
    """
    breaches: list[str] = []
    for entry in record["dispositions"]:
        target = entry["item"]
        if target not in kept:
            extra = sorted(set(entry) - DRAFT_FIELDS)
            if extra:
                breaches.append(
                    f"drafted {target!r} carries {extra}, which no draft may"
                )
        if not entry.get("confirmed") and _attributed(entry):
            breaches.append(
                f"unconfirmed {target!r} names a person or a rule, and "
                "nobody has confirmed it"
            )
    return breaches


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
    table: dict | None = None
    attributed = 0
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
        table = _carried_table(existing)
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
                # The item left the scoped set. An attributed entry cannot be
                # carried to an item that no longer exists and is somebody's
                # recorded judgement, so it refuses by name for a person to
                # remove; any other touched entry is reported rather than
                # silently discarded, because somebody decided it.
                if _attributed(entry):
                    raise ProposeError(
                        f"the existing set attributes {target!r} to a person "
                        "and the item is no longer scoped, so the attribution "
                        "cannot be carried forward; remove the entry by hand"
                    )
                dropped.append(target)
                continue
            if _touched(entry):
                if _attributed(entry):
                    _check_carried(entry, target, table)
                    attributed += 1
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
    if table is not None:
        record[RULES_FIELD] = table
    # The set is validated before it reaches the reviewer's disk, so no
    # invalid set is ever written for somebody to read and trust.
    breaches = schema_lib.check(record) + _check_drafted(record, kept)
    if breaches:
        raise ProposeError(
            "the drafted set breaches its schema: " + "; ".join(breaches[:4])
        )
    counts = {
        "scoped": len(scoped),
        "preserved": len(kept),
        "attributed": attributed,
        "replaced": replaced,
        "added": added,
        "dropped": len(dropped),
        "dropped_items": sorted(dropped),
        "rule_rows": len(table) if table is not None else 0,
        "rules_carried": table is not None,
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
    failures.extend(_check_attribution_carried(root, inventory, workbook))
    return failures


def _moved(inventory: dict) -> dict:
    """The inventory with its last item gone and its digest moved."""
    moved = json.loads(json.dumps(inventory))
    moved["items"] = moved["items"][:-1]
    moved["inventory_sha256"] = hashlib.sha256(
        json.dumps(moved["items"], sort_keys=True).encode("utf-8")
    ).hexdigest()
    return moved


def _same(left: dict, right: dict) -> bool:
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def _check_attribution_carried(root: Path, inventory: dict, workbook: dict) -> list[str]:
    """ADR-003's regeneration clause, proved against the committed fixtures.

    An attributed entry and the rules table survive a regeneration byte for
    byte, against the same records and against a moved inventory; a
    regeneration that cannot carry either refuses; and no driven branch
    attributes a draft.
    """
    failures: list[str] = []
    try:
        existing = reconcile_lib.read_json(root / "regeneration-input.json")
        closed = reconcile_lib.read_json(root / "closed.json")
        unattributable = [
            reconcile_lib.read_json(root / name)
            for name in (
                "rules-not-object.json", "unknown-rule.json",
                "unconfirmed-with-person.json", "unconfirmed-with-rule.json",
            )
        ]
    except reconcile_lib.ReconcileError as error:
        return [f"the regeneration fixtures are unreadable: {error}"]

    attributed = {
        entry["item"]: entry for entry in existing["dispositions"]
        if _attributed(entry)
    }
    for label, records in (("the same inventory", inventory), ("a moved inventory", _moved(inventory))):
        again, counts = propose(records, workbook, existing)
        by_item = {entry["item"]: entry for entry in again["dispositions"]}
        for target, before in attributed.items():
            if target not in by_item or not _same(by_item[target], before):
                failures.append(
                    f"attributed {target!r} did not survive regeneration "
                    f"against {label} byte for byte"
                )
        if not _same(again.get(RULES_FIELD, {}), existing[RULES_FIELD]):
            failures.append(
                f"the {RULES_FIELD} table did not survive regeneration against "
                f"{label} byte for byte"
            )
        if counts["attributed"] != len(attributed) or counts["preserved"] < len(attributed):
            failures.append(
                f"regeneration against {label} counted {counts['attributed']} "
                f"attributed entries, not {len(attributed)}"
            )
        if counts["rule_rows"] != len(existing[RULES_FIELD]):
            failures.append(f"regeneration against {label} miscounted the table")
        for entry in again["dispositions"]:
            if entry["item"] not in attributed and set(entry) - DRAFT_FIELDS:
                failures.append(
                    f"regeneration against {label} attributed a draft for "
                    f"{entry['item']!r}"
                )
        try:
            made = reconcile_lib.reconcile(records, workbook, again)
        except reconcile_lib.ReconcileError as error:
            failures.append(f"the set regenerated against {label} refuses: {error}")
        else:
            if made["closure_ratio"]["numerator"] != len(attributed):
                failures.append(
                    f"the set regenerated against {label} disposed of "
                    f"{made['closure_ratio']['numerator']} items, not {len(attributed)}"
                )

    # The closed set carries only attributed entries and a table; the lead
    # this clause answers was a regeneration of exactly that shape dropping
    # the table and refusing downstream.
    again, counts = propose(inventory, workbook, closed)
    if not _same(again.get(RULES_FIELD, {}), closed[RULES_FIELD]):
        failures.append("a fully attributed set lost its table on regeneration")
    if counts["preserved"] != len(closed["dispositions"]) or counts["replaced"]:
        failures.append("a fully attributed set was not carried whole")
    try:
        reconcile_lib.reconcile(inventory, workbook, again)
    except reconcile_lib.ReconcileError as error:
        failures.append(f"a regenerated attributed set refuses: {error}")

    # An attributed entry whose item left the scoped set cannot be carried.
    try:
        propose(_moved(inventory), workbook, closed)
    except ProposeError as error:
        if "cannot be carried forward" not in str(error):
            failures.append(f"the wrong refusal for an unscoped attribution: {error}")
    else:
        failures.append("an attributed entry on an unscoped item was not refused")

    # Neither a table that is not one, nor a rule the table does not hold,
    # nor an unconfirmed entry naming a person or a rule, is carried.
    for record in unattributable:
        try:
            propose(inventory, workbook, record)
        except ProposeError:
            continue
        failures.append("a set whose attribution cannot be carried was regenerated")
    return failures
