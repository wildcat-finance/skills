"""Join an inventory and a workbook, and refuse to decide anything.

This is where a coverage number could be quietly widened, so nothing here
proposes a disposition and no path exists that would let one be inferred. The
dispositions are a separate human-owned artefact. This module checks that the
artefact accounts for the scoped set exactly once, that each disposition holds
what it claims to hold, and that it was written against the records in front of
it rather than earlier ones.

Since a generator now drafts entries into that artefact, an entry alone no
longer says a person decided anything. Only a confirmed entry is admitted as a
disposition. Every entry is checked whatever its confirmation says, so an
invalid draft refuses now rather than when somebody confirms it; an unconfirmed
one is then set aside, named in the record and left holding its item undisposed.

A confirmed entry also says whose judgement admitted it. It names a person in
`confirmed_by` and may name a `rule`, an id into the set's own `rules` table,
where that rule's text and the person who stated it are written once. A
confirmed entry naming nobody refuses before it is counted, because a boolean
anything with write access can flip is not a judgement. See ADR-003.

The closure ratio is the count of scoped items carrying one valid disposition
over the count of scoped items. It reaches one when the deciding is finished.
It never says anything passed. See ADR-001.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from . import schema as schema_lib

SCHEMA = "dokimasia-coverage/v1"
CLOSURE = "dokimasia-disposition-closure/v1"
DISPOSITIONS_SCHEMA = "dokimasia-dispositions/v1"

# ADR-001 fixes this set. A fifth state, a rename, or a changed meaning alters
# every scrutiny already recorded, so widening it needs its own decision record.
DISPOSITIONS = ("covered", "manual", "excluded")
NEEDS_REASON = ("manual", "excluded")

# A status nobody has acted on is not an oracle. `covered` claims something is
# held to a reviewed judgement, and a case sitting at this status carries none.
STATUS_FIELD = "Status"
UNREVIEWED_STATUS = "Not Run"

# A person's mark, and the only thing that admits an entry as a disposition.
# A generator writes it false and has no path that writes it true, so a drafted
# entry holds the ratio down exactly as an absent one does. See ADR-002.
CONFIRMED_FIELD = "confirmed"

# Attribution. A confirmed entry names the person whose judgement admits it,
# and may name one row of the set-level rules table. A rule row carries the
# rule's text and the person who stated it, so an entry confirmed under a rule
# names two people at most and one at least. The person is required and the
# rule is additional: a rule with no person would attribute a judgement to a
# sentence. See ADR-003.
CONFIRMED_BY_FIELD = "confirmed_by"
RULE_FIELD = "rule"
RULES_FIELD = "rules"
RULE_TEXT_FIELD = "text"
RULE_AUTHOR_FIELD = "stated_by"

MAX_DISPOSITIONS = 40_000
MAX_REASON_BYTES = 512
MAX_FILE_BYTES = 8 * 1024 * 1024

# The attribution caps. Each is a parameter of `reconcile` with one of these
# as its default, never a module-level value a caller lowers in place, which
# is the pattern S2-R1-01 and S3-R1-03 of the first run recorded. A person's
# name and a rule's text are strings a reviewer typed that reach the committed
# coverage record, so each is bounded where it enters.
MAX_PERSON_BYTES = 128
MAX_RULE_ID_BYTES = 64
MAX_RULE_TEXT_BYTES = MAX_REASON_BYTES
MAX_RULES = 256

# A rule id is one safe segment, the shape a label already takes under the
# declared evidence root, so an id can become a file name or a heading without
# a second check.
SAFE_RULE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class ReconcileError(Exception):
    """One named refusal while reconciling."""


def item_id(item: dict) -> str:
    """Stable identity for one inventory item: its kind and its source file."""
    return f"{item['kind']}:{item['source']}"


def case_id(case: dict) -> str:
    """Stable identity for one workbook case: its own identifier."""
    return f"case:{case['id']}"


def read_json(path: Path, max_bytes: int = MAX_FILE_BYTES) -> dict:
    """One bounded, non-symlink read of a JSON object."""
    if path.is_symlink():
        raise ReconcileError(f"{path.name} is a symlink")
    if not path.is_file():
        raise ReconcileError(f"{path.name} is not a regular file")
    size = path.stat().st_size
    if size > max_bytes:
        raise ReconcileError(
            f"{path.name} is {size} bytes, over the {max_bytes}-byte cap"
        )
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReconcileError(f"{path.name} is not readable as JSON: {error}") from error
    if not isinstance(loaded, dict):
        raise ReconcileError(f"{path.name} is not one JSON object")
    return loaded


def _require_shape(record: dict, label: str, collection: str, fields: tuple) -> None:
    """Refuse a record that is not the kind of record it was passed as.

    The verb takes operator-supplied paths, so a mistyped or truncated file is
    an ordinary mistake rather than an attack. Every other refusal in this
    plugin is named, and reaching a `KeyError` here would be the one place a
    caller got a stack trace instead.
    """
    entries = record.get(collection)
    if not isinstance(entries, list):
        raise ReconcileError(
            f"the {label} record holds no {collection} list, so it is not "
            f"a {label} record"
        )
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ReconcileError(
                f"{label} {collection}[{index}] is not an object"
            )
        missing = [name for name in fields if name not in entry]
        if missing:
            raise ReconcileError(
                f"{label} {collection}[{index}] is missing "
                + ", ".join(repr(name) for name in missing)
            )


def scoped_set(inventory: dict, workbook: dict) -> list[dict]:
    """Every item a disposition is owed for, from both sides, in a fixed order.

    Both sides are scoped. An inventory item with no case is the gap the tool
    exists to find, and a case matching no item is work spent on something the
    inventory does not know about; neither can be answered by leaving it out.
    """
    _require_shape(inventory, "inventory", "items", ("kind", "source"))
    _require_shape(workbook, "workbook", "cases", ("id", "sheet", "row", "fields"))
    scoped: list[dict] = []
    for item in inventory.get("items", []):
        scoped.append({
            "id": item_id(item),
            "side": "inventory",
            "kind": item["kind"],
            "source": item["source"],
            "url": item.get("url", ""),
        })
    for case in workbook.get("cases", []):
        scoped.append({
            "id": case_id(case),
            "side": "workbook",
            "kind": "case",
            "source": f"{case['sheet']}:{case['row']}",
            "url": "",
        })
    seen: set[str] = set()
    for entry in scoped:
        if entry["id"] in seen:
            raise ReconcileError(
                f"scoped item {entry['id']!r} appears twice, so a disposition "
                "could not be attached to one of them"
            )
        seen.add(entry["id"])
    if len(scoped) > MAX_DISPOSITIONS:
        raise ReconcileError(
            f"the scoped set holds more than the {MAX_DISPOSITIONS}-item cap"
        )
    return sorted(scoped, key=lambda entry: entry["id"])


def _check_currency(declared: dict, inventory: dict, workbook: dict) -> None:
    """Refuse a disposition set written against records that have since moved.

    A stale set is the failure that looks most like success: every item is
    accounted for, and the account is of a tree nobody is looking at now.
    """
    pairs = (
        ("inventory_sha256", inventory.get("inventory_sha256", "")),
        ("workbook_sha256", workbook.get("workbook_sha256", "")),
    )
    for field, current in pairs:
        recorded = declared.get(field, "")
        if not recorded:
            raise ReconcileError(f"the disposition set declares no {field}")
        if recorded != current:
            raise ReconcileError(
                f"the disposition set is stale: it names {field} {recorded}, "
                f"and the record in front of it is {current}"
            )


def _check_rules(
    declared: dict,
    max_rules: int,
    max_rule_id_bytes: int,
    max_rule_text_bytes: int,
    max_person_bytes: int,
) -> dict[str, dict]:
    """The set's rules table, checked row by row, or a named refusal.

    A table is optional: a set whose every confirmation was made individually
    declares none. A table that is present is checked in full before any entry
    is read, so a dangling `rule` id below refuses against a table that is
    known to be sound. A row nobody applies is not a defect; the record
    reports it as applied zero times, because a stated rule nobody used is
    information about the review rather than a fault in the file.
    """
    if RULES_FIELD not in declared:
        return {}
    table = declared[RULES_FIELD]
    if not isinstance(table, dict):
        raise ReconcileError(
            f"the disposition set's {RULES_FIELD!r} is "
            f"{type(table).__name__}, not an object keyed by rule id"
        )
    if len(table) > max_rules:
        raise ReconcileError(
            f"the {RULES_FIELD} table holds {len(table)} rows, over the "
            f"{max_rules}-row cap"
        )
    rules: dict[str, dict] = {}
    for rule_id, row in table.items():
        if len(rule_id.encode("utf-8")) > max_rule_id_bytes:
            raise ReconcileError(
                f"a rule id in the {RULES_FIELD} table is over the "
                f"{max_rule_id_bytes}-byte cap"
            )
        if not SAFE_RULE_ID.match(rule_id) or rule_id in (".", ".."):
            raise ReconcileError(
                f"rule id {rule_id!r} is not one safe segment"
            )
        if not isinstance(row, dict):
            raise ReconcileError(
                f"rule {rule_id!r} is {type(row).__name__}, not an object"
            )
        text = row.get(RULE_TEXT_FIELD, "")
        if not isinstance(text, str):
            raise ReconcileError(
                f"the {RULE_TEXT_FIELD!r} of rule {rule_id!r} is "
                f"{type(text).__name__}, not a string"
            )
        if len(text.encode("utf-8")) > max_rule_text_bytes:
            raise ReconcileError(
                f"the {RULE_TEXT_FIELD} of rule {rule_id!r} is over the "
                f"{max_rule_text_bytes}-byte cap"
            )
        if not text.strip():
            raise ReconcileError(
                f"rule {rule_id!r} carries no {RULE_TEXT_FIELD}, so nothing "
                "states what was applied"
            )
        author = row.get(RULE_AUTHOR_FIELD, "")
        if not isinstance(author, str):
            raise ReconcileError(
                f"the {RULE_AUTHOR_FIELD!r} of rule {rule_id!r} is "
                f"{type(author).__name__}, not a string"
            )
        if len(author.encode("utf-8")) > max_person_bytes:
            raise ReconcileError(
                f"the {RULE_AUTHOR_FIELD} of rule {rule_id!r} is over the "
                f"{max_person_bytes}-byte cap"
            )
        if not author.strip():
            raise ReconcileError(
                f"rule {rule_id!r} carries no {RULE_AUTHOR_FIELD}, so nothing "
                "states whose judgement it is"
            )
        rules[rule_id] = {RULE_TEXT_FIELD: text, RULE_AUTHOR_FIELD: author}
    return rules


def _check_attribution(
    entry: dict,
    target: str,
    confirmed: bool,
    rules: dict[str, dict],
    max_person_bytes: int,
) -> tuple[str, str | None]:
    """The person and the rule a confirmed entry names, or a named refusal.

    Absence is refused rather than defaulted, for the reason ADR-002 gave for
    `confirmed`: defaulting a person is the exact forgery attribution exists
    to make impossible. A set confirmed before this field existed therefore
    refuses on its first confirmed entry, naming the item and the field, and
    is attributed by a person rather than by this code.

    An unconfirmed entry may carry neither field. A draft that pre-names its
    confirmer would read as attributed the moment somebody flipped the boolean.
    """
    if not confirmed:
        for field in (CONFIRMED_BY_FIELD, RULE_FIELD):
            if field in entry:
                raise ReconcileError(
                    f"unconfirmed disposition on {target!r} carries {field!r}; "
                    "nobody has confirmed it, so nothing may say who did"
                )
        return "", None
    if CONFIRMED_BY_FIELD not in entry:
        raise ReconcileError(
            f"confirmed disposition on {target!r} carries no "
            f"{CONFIRMED_BY_FIELD!r} field, so nothing states whose judgement "
            "admits it"
        )
    person = entry[CONFIRMED_BY_FIELD]
    if not isinstance(person, str):
        raise ReconcileError(
            f"the {CONFIRMED_BY_FIELD!r} field on {target!r} is "
            f"{type(person).__name__}, not a string"
        )
    if len(person.encode("utf-8")) > max_person_bytes:
        raise ReconcileError(
            f"the {CONFIRMED_BY_FIELD} on {target!r} is over the "
            f"{max_person_bytes}-byte cap"
        )
    if not person.strip():
        raise ReconcileError(
            f"the {CONFIRMED_BY_FIELD!r} field on {target!r} is blank, so "
            "nothing states whose judgement admits it"
        )
    if RULE_FIELD not in entry:
        return person, None
    rule = entry[RULE_FIELD]
    if not isinstance(rule, str):
        raise ReconcileError(
            f"the {RULE_FIELD!r} field on {target!r} is "
            f"{type(rule).__name__}, not a string"
        )
    if rule not in rules:
        raise ReconcileError(
            f"confirmed disposition on {target!r} names rule {rule!r}, which "
            f"the {RULES_FIELD} table does not hold"
        )
    return person, rule


def reconcile(
    inventory: dict,
    workbook: dict,
    declared: dict,
    *,
    max_person_bytes: int = MAX_PERSON_BYTES,
    max_rule_id_bytes: int = MAX_RULE_ID_BYTES,
    max_rule_text_bytes: int = MAX_RULE_TEXT_BYTES,
    max_rules: int = MAX_RULES,
) -> dict:
    """The closed coverage record, or a named refusal.

    Nothing here decides a disposition. Every one is read from `declared`, and
    an item the reviewer did not answer for stays unanswered and holds the
    ratio below one.

    The four keyword caps bound the attribution strings a reviewer typed. Each
    defaults to the module value the record's `caps` block reports.
    """
    if declared.get("schema") != DISPOSITIONS_SCHEMA:
        raise ReconcileError(
            f"the disposition set declares schema {declared.get('schema')!r}, "
            f"not {DISPOSITIONS_SCHEMA!r}"
        )
    _check_currency(declared, inventory, workbook)
    rules = _check_rules(
        declared, max_rules, max_rule_id_bytes, max_rule_text_bytes, max_person_bytes
    )

    scoped = scoped_set(inventory, workbook)
    known = {entry["id"] for entry in scoped}
    side = {entry["id"]: entry["side"] for entry in scoped}
    cases = {case["id"]: case for case in workbook.get("cases", [])}

    assigned: dict[str, dict] = {}
    entries = declared.get("dispositions", [])
    if not isinstance(entries, list):
        raise ReconcileError("the disposition set holds no dispositions list")
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ReconcileError(f"dispositions[{index}] is not an object")
    if len(entries) > MAX_DISPOSITIONS:
        raise ReconcileError(
            f"the disposition set holds more than the {MAX_DISPOSITIONS}-item cap"
        )
    unconfirmed: list[dict] = []
    # Every item any entry answered for, confirmed or not. Kept as a set
    # beside the two lists because the duplicate check runs once per entry
    # and the declared cap admits 40,000 of them.
    answered: set[str] = set()
    # Who confirmed what, counted inside this one pass. A person and a rule
    # are each a dictionary increment, never a second walk of the entries.
    by_person: dict[str, int] = {}
    applied: dict[str, int] = {rule_id: 0 for rule_id in rules}
    individual = 0
    for entry in entries:
        target = entry.get("item", "")
        if target not in known:
            raise ReconcileError(
                f"disposition names {target!r}, which is not a scoped item"
            )
        if target in answered:
            raise ReconcileError(
                f"scoped item {target!r} carries two dispositions, so nothing "
                "states what was decided about it"
            )
        verdict = entry.get("disposition", "")
        if verdict not in DISPOSITIONS:
            raise ReconcileError(
                f"disposition {verdict!r} on {target!r} is not one of "
                + ", ".join(repr(name) for name in DISPOSITIONS)
            )
        reason = entry.get("reason", "")
        # The cap is declared over reasons, so it binds every reason, not only
        # the two states that are required to carry one.
        if len(reason.encode("utf-8")) > MAX_REASON_BYTES:
            raise ReconcileError(
                f"the reason on {target!r} is over the "
                f"{MAX_REASON_BYTES}-byte cap"
            )
        if verdict in NEEDS_REASON:
            if not reason.strip():
                raise ReconcileError(
                    f"{verdict} item {target!r} carries no reason, and an "
                    f"unexplained {verdict} is how a denominator shrinks quietly"
                )
            if entry.get("oracle", ""):
                # A row reading as both decided-by-a-person and held-to-a-case
                # states two different things about the same item.
                raise ReconcileError(
                    f"{verdict} item {target!r} also names an oracle; only a "
                    "covered item is held to one"
                )
        if verdict == "covered":
            if side[target] == "workbook":
                # An oracle is a workbook case, and `covered` asserts that
                # something is held to one. A case cannot be held to a case:
                # the case is the oracle. Left open, a row could name itself
                # and close the ratio on its own evidence.
                raise ReconcileError(
                    f"workbook case {target!r} cannot be covered; a case is an "
                    "oracle, not something held to one, so it takes manual or "
                    "excluded"
                )
            oracle = entry.get("oracle", "")
            if not oracle:
                raise ReconcileError(
                    f"covered item {target!r} names no oracle; nothing may be "
                    "marked covered without one"
                )
            if oracle not in cases:
                raise ReconcileError(
                    f"covered item {target!r} names oracle {oracle!r}, which "
                    "the workbook does not hold"
                )
            fields = cases[oracle]["fields"]
            if STATUS_FIELD not in fields:
                # Comparing against the unreviewed value alone would pass every
                # oracle in a workbook that has no status column at all, which
                # is the check failing open in exactly the direction that
                # widens coverage.
                raise ReconcileError(
                    f"covered item {target!r} names oracle {oracle!r}, which "
                    f"carries no {STATUS_FIELD} field; nothing states whether "
                    "anybody acted on it"
                )
            status = fields[STATUS_FIELD].strip()
            if not status:
                raise ReconcileError(
                    f"covered item {target!r} names oracle {oracle!r}, whose "
                    f"{STATUS_FIELD} is blank; nothing is held to it"
                )
            if status == UNREVIEWED_STATUS:
                raise ReconcileError(
                    f"covered item {target!r} names oracle {oracle!r}, whose "
                    f"status is {status!r}; nothing is held to it"
                )
        # Read last, so an entry that could never be valid refuses for the
        # thing that is wrong with it rather than for its confirmation. Every
        # entry is checked in full above; confirmation decides admission, not
        # validity.
        #
        # Absence is refused rather than defaulted. Defaulting false would
        # discard a set written before this field existed; defaulting true
        # would admit every draft a generator wrote. See ADR-002.
        if CONFIRMED_FIELD not in entry:
            raise ReconcileError(
                f"disposition on {target!r} carries no {CONFIRMED_FIELD!r} "
                "field, so nothing states whether a person agreed to it"
            )
        confirmed = entry[CONFIRMED_FIELD]
        if not isinstance(confirmed, bool):
            raise ReconcileError(
                f"the {CONFIRMED_FIELD!r} field on {target!r} is "
                f"{type(confirmed).__name__}, not a boolean"
            )
        # Read after the boolean, because attribution is a claim about a
        # confirmation and an unconfirmed entry has none to attribute.
        person, rule = _check_attribution(
            entry, target, confirmed, rules, max_person_bytes
        )
        decided = {
            "item": target,
            "disposition": verdict,
            "reason": reason,
            "oracle": entry.get("oracle", ""),
        }
        answered.add(target)
        if confirmed:
            assigned[target] = decided
            by_person[person] = by_person.get(person, 0) + 1
            if rule is None:
                individual += 1
            else:
                applied[rule] += 1
        else:
            unconfirmed.append(decided)

    unconfirmed.sort(key=lambda entry: entry["item"])
    # An unconfirmed entry answers for nothing, so its item is undisposed
    # exactly as an item with no entry at all is.
    undisposed = sorted(known - set(assigned))
    numerator = len(assigned)
    denominator = len(scoped)
    gaps = sorted(
        (assigned[key] for key in assigned if assigned[key]["disposition"] in NEEDS_REASON),
        key=lambda entry: entry["item"],
    )
    # Both sides in full. The join itself is made by the reviewer through the
    # oracle field, so what is unmatched is worked out below from what the
    # dispositions cite, never inferred here.
    inventory_ids = sorted(item_id(item) for item in inventory.get("items", []))
    case_ids = sorted(case_id(case) for case in workbook.get("cases", []))
    oracles = {a["oracle"] for a in assigned.values() if a["oracle"]}
    cited = {f"case:{name}" for name in oracles}

    return {
        "schema": SCHEMA,
        "closure": CLOSURE,
        "subject": {
            "inventory_sha256": inventory.get("inventory_sha256", ""),
            "workbook_sha256": workbook.get("workbook_sha256", ""),
        },
        "caps": {
            "dispositions": MAX_DISPOSITIONS,
            "reason_bytes": MAX_REASON_BYTES,
            "input_bytes": MAX_FILE_BYTES,
            "person_bytes": max_person_bytes,
            "rule_id_bytes": max_rule_id_bytes,
            "rule_text_bytes": max_rule_text_bytes,
            "rules": max_rules,
        },
        "vocabulary": list(DISPOSITIONS),
        "counts": {
            "scoped": denominator,
            "disposed": numerator,
            "unconfirmed": len(unconfirmed),
            "undisposed": len(undisposed),
            "inventory_items": len(inventory_ids),
            "workbook_cases": len(case_ids),
            "by_disposition": {
                name: sum(
                    1 for a in assigned.values() if a["disposition"] == name
                )
                for name in DISPOSITIONS
            },
        },
        "closure_ratio": {
            "numerator": numerator,
            "denominator": denominator,
            "value": (numerator / denominator) if denominator else 0.0,
            "closed": numerator == denominator and denominator > 0,
        },
        # Whose judgement the numerator is. `by_person` sums to `disposed`,
        # and so do `individual` and the applied counts together, so a reader
        # can reconcile the block against the ratio without trusting it.
        "confirmations": {
            "people": len(by_person),
            "by_person": {name: by_person[name] for name in sorted(by_person)},
            "by_rule": {
                rule_id: {
                    RULE_TEXT_FIELD: rules[rule_id][RULE_TEXT_FIELD],
                    RULE_AUTHOR_FIELD: rules[rule_id][RULE_AUTHOR_FIELD],
                    "applied": applied[rule_id],
                }
                for rule_id in sorted(rules)
            },
            "individual": individual,
        },
        "undisposed": undisposed,
        "unconfirmed": unconfirmed,
        "gaps": gaps,
        "unmatched": {
            "cases_no_item_cites": sorted(set(case_ids) - cited),
            "items_no_oracle_cites": sorted(
                key for key in inventory_ids
                if key not in assigned or not assigned[key]["oracle"]
            ),
        },
        "dispositions": [assigned[key] for key in sorted(assigned)],
    }


def canonical_bytes(record: dict) -> bytes:
    body = {key: value for key, value in record.items() if key != "subject"}
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def coverage_digest(record: dict) -> str:
    return hashlib.sha256(canonical_bytes(record)).hexdigest()


def fixture_root() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures" / "dispositions"


def check() -> list[str]:
    """Prove the contract this module claims, against committed fixtures."""
    failures: list[str] = []
    root = fixture_root()
    try:
        inventory = read_json(root / "inventory.json")
        workbook = read_json(root / "workbook.json")
    except ReconcileError as error:
        return [f"the reconcile fixtures are unreadable: {error}"]

    try:
        closed = reconcile(inventory, workbook, read_json(root / "closed.json"))
    except ReconcileError as error:
        return [f"the closed fixture did not reconcile: {error}"]

    ratio = closed["closure_ratio"]
    if not ratio["closed"]:
        failures.append("the closed fixture did not reach a closure ratio of one")
    if ratio["numerator"] != ratio["denominator"]:
        failures.append("the closed fixture's numerator and denominator disagree")
    if ratio["denominator"] != closed["counts"]["scoped"]:
        failures.append("the denominator is not the scoped count")
    if not closed["gaps"]:
        failures.append("the closed fixture records no gap, so reasons are untested")
    for gap in closed["gaps"]:
        if not gap["reason"]:
            failures.append(f"gap {gap['item']!r} carries no reason")

    # A drafted set answers for nothing until a person confirms it, and the
    # figures have to say so three ways: nothing disposed, every entry named
    # as unconfirmed, and every item still undisposed.
    try:
        drafted = reconcile(inventory, workbook, read_json(root / "all-unconfirmed.json"))
    except ReconcileError as error:
        return [f"the all-unconfirmed fixture did not reconcile: {error}"]
    if drafted["closure_ratio"]["numerator"] != 0:
        failures.append("an all-unconfirmed set disposed of something")
    if drafted["closure_ratio"]["closed"]:
        failures.append("an all-unconfirmed set closed the ratio")
    if drafted["counts"]["unconfirmed"] != len(drafted["unconfirmed"]):
        failures.append("the unconfirmed count and list disagree")
    if drafted["counts"]["unconfirmed"] != drafted["counts"]["scoped"]:
        failures.append("an all-unconfirmed set did not name every entry as unconfirmed")
    if drafted["counts"]["undisposed"] != drafted["counts"]["scoped"]:
        failures.append("an unconfirmed entry left its item out of the undisposed list")
    for entry in drafted["unconfirmed"]:
        if not entry["disposition"]:
            failures.append(f"unconfirmed {entry['item']!r} lost its drafted state")

    try:
        mixed = reconcile(inventory, workbook, read_json(root / "mixed-confirmation.json"))
    except ReconcileError as error:
        return [f"the mixed-confirmation fixture did not reconcile: {error}"]
    counts = mixed["counts"]
    if counts["disposed"] + counts["unconfirmed"] != counts["scoped"]:
        failures.append("disposed and unconfirmed do not add to the scoped set")
    if counts["disposed"] == 0 or counts["unconfirmed"] == 0:
        failures.append("the mixed fixture exercises only one side of confirmation")
    if counts["undisposed"] != counts["unconfirmed"]:
        failures.append("an unconfirmed entry was counted as answering for its item")

    # Whose judgement the numerator is. The block reconciles with `disposed`
    # three ways, a rule nobody applied reports zero, and every admitted entry
    # is attributed, because an unattributed one refuses before it is counted.
    for label, made in (("closed", closed), ("mixed", mixed)):
        block = made["confirmations"]
        disposed = made["counts"]["disposed"]
        if block["people"] != len(block["by_person"]):
            failures.append(f"the {label} fixture's people count is not its by_person size")
        if sum(block["by_person"].values()) != disposed:
            failures.append(f"the {label} fixture's by_person does not sum to disposed")
        applied = sum(row["applied"] for row in block["by_rule"].values())
        if block["individual"] + applied != disposed:
            failures.append(
                f"the {label} fixture's individual and applied counts do not sum to disposed"
            )
        if block["people"] < 2 or block["individual"] == 0 or applied == 0:
            failures.append(f"the {label} fixture exercises only one attribution shape")
        if not any(row["applied"] == 0 for row in block["by_rule"].values()):
            failures.append(f"the {label} fixture holds no rule applied to nothing")
        for rule_id, row in block["by_rule"].items():
            if not row[RULE_TEXT_FIELD].strip() or not row[RULE_AUTHOR_FIELD].strip():
                failures.append(f"rule {rule_id!r} reached the record without its text or author")
    if drafted["confirmations"] != {
        "people": 0,
        "by_person": {},
        "by_rule": {
            rule_id: {**row, "applied": 0}
            for rule_id, row in closed["confirmations"]["by_rule"].items()
        },
        "individual": 0,
    }:
        failures.append("an all-unconfirmed set attributed something to somebody")

    # A moved attribution is a moved record: the canonical digest covers the
    # block, so the same dispositions under a different name do not agree.
    renamed = read_json(root / "closed.json")
    for entry in renamed["dispositions"]:
        if entry.get(CONFIRMED_BY_FIELD):
            entry[CONFIRMED_BY_FIELD] = "Somebody Else"
            break
    if coverage_digest(reconcile(inventory, workbook, renamed)) == coverage_digest(closed):
        failures.append("a changed attribution left the coverage digest unchanged")

    # Each cap at its bound is admitted; one over it refuses below.
    for name in (
        "person-at-cap.json", "author-at-cap.json", "rule-text-at-cap.json",
        "rule-id-at-cap.json", "rules-at-cap.json",
    ):
        try:
            reconcile(inventory, workbook, read_json(root / name))
        except ReconcileError as error:
            failures.append(f"{name} sits at its cap and refused: {error}")

    hostile = {
        "confirmed-without-person.json": "carries no 'confirmed_by'",
        "blank-person.json": "is blank",
        "non-string-person.json": "not a string",
        "unknown-rule.json": "the rules table does not hold",
        "non-string-rule.json": "not a string",
        "rule-without-text.json": "carries no text",
        "rule-without-author.json": "carries no stated_by",
        "rules-not-object.json": "not an object",
        "unsafe-rule-id.json": "not one safe segment",
        "unconfirmed-with-person.json": "unconfirmed disposition",
        "unconfirmed-with-rule.json": "unconfirmed disposition",
        "prior-shape.json": "carries no 'confirmed_by'",
        "person-over-cap.json": "over the",
        "author-over-cap.json": "over the",
        "rule-text-over-cap.json": "over the",
        "rule-id-over-cap.json": "over the",
        "rules-over-cap.json": "over the",
        "missing-confirmed.json": "carries no 'confirmed'",
        "non-boolean-confirmed.json": "not a boolean",
        "unconfirmed-case-covered-by-itself.json": "cannot be covered",
        "no-disposition.json": "did not reach",
        "two-dispositions.json": "two dispositions",
        "absent-oracle.json": "the workbook does not hold",
        "unreviewed-oracle.json": "nothing is held to it",
        "covered-without-oracle.json": "names no oracle",
        "missing-reason.json": "carries no reason",
        "oversize-reason.json": "over the",
        "manual-with-oracle.json": "also names an oracle",
        "case-covered-by-itself.json": "cannot be covered",
        "stale-inventory.json": "stale",
        "stale-workbook.json": "stale",
        "unknown-item.json": "not a scoped item",
        "bad-vocabulary.json": "is not one of",
    }
    for name, expected in hostile.items():
        try:
            made = reconcile(inventory, workbook, read_json(root / name))
        except ReconcileError as refusal:
            if expected not in str(refusal):
                failures.append(f"{name} refused with {refusal!r}, not for {expected!r}")
            continue
        # A set that refuses nothing must at least fail to close.
        if name == "no-disposition.json":
            if made["closure_ratio"]["closed"]:
                failures.append(f"{name} closed; an unanswered item must hold it open")
            elif not made["undisposed"]:
                failures.append(f"{name} named no undisposed item")
        else:
            failures.append(f"{name} was accepted; it must refuse")

    twice = reconcile(inventory, workbook, read_json(root / "closed.json"))
    if coverage_digest(twice) != coverage_digest(closed):
        failures.append("two reconciles of the same inputs disagreed on the digest")
    # The schema says the record is closed. Enforce it rather than stating it.
    failures.extend(
        f"the coverage record breaches its schema: {line}"
        for line in schema_lib.check(closed)
    )
    return failures
