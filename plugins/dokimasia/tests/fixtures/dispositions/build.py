"""Build the disposition fixtures from the committed inventory and workbook.

The disposition sets bind to two digests, so they cannot be written by hand
without going stale the moment either fixture moves. This regenerates all of
them, including the ones that must refuse, from whatever those records say now.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[2]
sys.path.insert(0, str(PLUGIN / "scripts"))

from dokimasia_lib import inventory as inventory_lib  # noqa: E402
from dokimasia_lib import reconcile as reconcile_lib  # noqa: E402
from dokimasia_lib import workbook as workbook_lib  # noqa: E402

SCHEMA = reconcile_lib.DISPOSITIONS_SCHEMA

# Two fictitious reviewers and the rules they stated. Every confirmed entry in
# the closed fixture names one of them; the workbook rows are confirmed under
# a rule and the compiled items individually, so the record's confirmations
# block has both shapes to reconcile. One row is applied to nothing, because a
# stated rule nobody used is reported rather than refused. See ADR-003.
PERSON_ONE = "Reviewer One"
PERSON_TWO = "Reviewer Two"
ROW_RULE = "row-owner-walks-it"
UNUSED_RULE = "stated-and-applied-to-nothing"
RULES = {
    ROW_RULE: {
        "text": "the reviewer who wrote a row walks it",
        "stated_by": PERSON_TWO,
    },
    UNUSED_RULE: {
        "text": "a rule the table holds and no entry names",
        "stated_by": PERSON_ONE,
    },
}


def _records() -> tuple[dict, dict]:
    """The two sides, compiled from the committed fixtures."""
    items = inventory_lib.compile_inventory(PLUGIN / "tests" / "fixtures" / "app")
    inventory = inventory_lib.record(items, {"label": "tests/fixtures/app"})

    build_path = PLUGIN / "tests" / "fixtures" / "workbooks" / "build.py"
    import importlib.util

    spec = importlib.util.spec_from_file_location("workbook_build", build_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with tempfile.TemporaryDirectory() as raw:
        made = module.build_all(Path(raw))
        log: list[dict] = []
        cases = workbook_lib.read_cases(made["benign.xlsx"], sheet_log=log)
        workbook = workbook_lib.record(
            cases, {"label": "benign.xlsx", "sha256": "0" * 64}, log
        )
    return inventory, workbook


def _envelope(
    inventory: dict, workbook: dict, entries: list[dict], rules=RULES
) -> dict:
    body = {
        "schema": SCHEMA,
        "inventory_sha256": inventory["inventory_sha256"],
        "workbook_sha256": workbook["workbook_sha256"],
        "dispositions": entries,
    }
    if rules is not None:
        body["rules"] = json.loads(json.dumps(rules))
    return body


def _draft(entry: dict) -> dict:
    """The entry as a generator would have drafted it: unconfirmed, unattributed.

    An unconfirmed entry may carry neither attribution field, so every fixture
    that turns a confirmed entry back into a draft strips them here.
    """
    return {
        **{k: v for k, v in entry.items() if k not in ("confirmed_by", "rule")},
        "confirmed": False,
    }


def _closed_entries(inventory: dict, workbook: dict) -> list[dict]:
    """One valid disposition for every scoped item.

    A reviewed oracle is one whose status is not the unreviewed value, so the
    covered entries here cite the cases a person actually acted on.
    """
    reviewed = [
        case["id"] for case in workbook["cases"]
        if case["fields"].get("Status") != reconcile_lib.UNREVIEWED_STATUS
    ]
    entries: list[dict] = []
    for index, entry in enumerate(reconcile_lib.scoped_set(inventory, workbook)):
        target = entry["id"]
        if entry["side"] == "inventory" and entry["kind"] in ("route", "api"):
            entries.append({
                "item": target,
                "disposition": "covered",
                "oracle": reviewed[index % len(reviewed)],
                "confirmed": True,
                "confirmed_by": PERSON_ONE,
            })
        elif entry["kind"] == "guard":
            entries.append({
                "item": target,
                "disposition": "manual",
                "reason": "the gate is checked by a person against the access matrix",
                "confirmed": True,
                "confirmed_by": PERSON_ONE,
            })
        elif entry["kind"] == "action":
            entries.append({
                "item": target,
                "disposition": "excluded",
                "reason": "the action is exercised only through the routes above",
                "confirmed": True,
                "confirmed_by": PERSON_ONE,
            })
        else:
            entries.append({
                "item": target,
                "disposition": "manual",
                "reason": "the row is owned by the reviewer who wrote it",
                "confirmed": True,
                "confirmed_by": PERSON_TWO,
                "rule": ROW_RULE,
            })
    return entries


def build_all(directory: Path) -> dict[str, Path]:
    """Write every fixture and return the paths, keyed by file name."""
    directory.mkdir(parents=True, exist_ok=True)
    inventory, workbook = _records()
    made: dict[str, Path] = {}

    def write(name: str, body: dict) -> None:
        target = directory / name
        target.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n")
        made[name] = target

    write("inventory.json", inventory)
    write("workbook.json", workbook)

    closed = _closed_entries(inventory, workbook)
    write("closed.json", _envelope(inventory, workbook, closed))

    # One scoped item left unanswered. This must not refuse; it must fail to
    # close, because an unanswered item is a real state a run can be in.
    write("no-disposition.json", _envelope(inventory, workbook, closed[:-1]))

    write(
        "two-dispositions.json",
        _envelope(inventory, workbook, closed + [dict(closed[0])]),
    )

    reviewed_ids = [
        case["id"] for case in workbook["cases"]
        if case["fields"].get("Status") != reconcile_lib.UNREVIEWED_STATUS
    ]
    covered = next(e for e in closed if e["disposition"] == "covered")
    absent = [dict(e) for e in closed]
    absent[closed.index(covered)] = {**covered, "oracle": "ZZZ-99"}
    write("absent-oracle.json", _envelope(inventory, workbook, absent))

    unreviewed_ids = [
        case["id"] for case in workbook["cases"]
        if case["fields"].get("Status") == reconcile_lib.UNREVIEWED_STATUS
    ]
    stale_oracle = [dict(e) for e in closed]
    stale_oracle[closed.index(covered)] = {**covered, "oracle": unreviewed_ids[0]}
    write("unreviewed-oracle.json", _envelope(inventory, workbook, stale_oracle))

    bare = [dict(e) for e in closed]
    bare[closed.index(covered)] = {
        "item": covered["item"], "disposition": "covered", "confirmed": True,
        "confirmed_by": PERSON_ONE,
    }
    write("covered-without-oracle.json", _envelope(inventory, workbook, bare))

    manual = next(e for e in closed if e["disposition"] == "manual")
    unreasoned = [dict(e) for e in closed]
    unreasoned[closed.index(manual)] = {**manual, "reason": "   "}
    write("missing-reason.json", _envelope(inventory, workbook, unreasoned))

    stale_i = _envelope(inventory, workbook, closed)
    stale_i["inventory_sha256"] = "0" * 64
    write("stale-inventory.json", stale_i)

    stale_w = _envelope(inventory, workbook, closed)
    stale_w["workbook_sha256"] = "0" * 64
    write("stale-workbook.json", stale_w)

    write(
        "unknown-item.json",
        _envelope(inventory, workbook, closed + [{
            "item": "route:src/app/nowhere/page.tsx",
            "disposition": "excluded",
            "reason": "this item is not in the inventory",
            "confirmed": True,
            "confirmed_by": PERSON_ONE,
        }]),
    )

    oversize = [dict(e) for e in closed]
    oversize[closed.index(covered)] = {
        **covered, "reason": "x" * (reconcile_lib.MAX_REASON_BYTES + 1),
    }
    write("oversize-reason.json", _envelope(inventory, workbook, oversize))

    both = [dict(e) for e in closed]
    both[closed.index(manual)] = {**manual, "oracle": reviewed_ids[0]}
    write("manual-with-oracle.json", _envelope(inventory, workbook, both))

    circular = [dict(e) for e in closed]
    case_entry = next(
        e for e in closed if e["item"].startswith("case:")
    )
    circular[closed.index(case_entry)] = {
        "item": case_entry["item"],
        "disposition": "covered",
        "oracle": case_entry["item"].split(":", 1)[1],
        "confirmed": True,
        "confirmed_by": PERSON_ONE,
    }
    write("case-covered-by-itself.json", _envelope(inventory, workbook, circular))

    wrong = [dict(e) for e in closed]
    wrong[0] = {**closed[0], "disposition": "partial"}
    write("bad-vocabulary.json", _envelope(inventory, workbook, wrong))

    # Confirmation fixtures. ADR-002 makes `confirmed` the only thing that
    # admits an entry, so these cover the four states a set can be in and the
    # two ways the field itself can be wrong.
    drafted = [_draft(e) for e in closed]
    write("all-unconfirmed.json", _envelope(inventory, workbook, drafted))

    half = len(closed) // 2
    mixed = [
        e if index < half else _draft(e) for index, e in enumerate(closed)
    ]
    write("mixed-confirmation.json", _envelope(inventory, workbook, mixed))

    absent_field = [dict(e) for e in closed]
    absent_field[0] = {k: v for k, v in closed[0].items() if k != "confirmed"}
    write("missing-confirmed.json", _envelope(inventory, workbook, absent_field))

    not_boolean = [dict(e) for e in closed]
    not_boolean[0] = {**closed[0], "confirmed": "yes"}
    write("non-boolean-confirmed.json", _envelope(inventory, workbook, not_boolean))

    # A draft that could never be valid refuses now, not when somebody
    # confirms it: an unconfirmed entry is still checked in full.
    unconfirmed_circular = [dict(e) for e in closed]
    unconfirmed_circular[closed.index(case_entry)] = {
        "item": case_entry["item"],
        "disposition": "covered",
        "oracle": case_entry["item"].split(":", 1)[1],
        "confirmed": False,
    }
    write(
        "unconfirmed-case-covered-by-itself.json",
        _envelope(inventory, workbook, unconfirmed_circular),
    )

    # Attribution fixtures. ADR-003 requires a person on every confirmed
    # entry and resolves a rule against the set's own table, so these cover
    # each way the person, the rule or the table can be wrong, and each cap
    # at its bound and one over it.
    def with_first(**fields) -> list[dict]:
        replaced = [dict(e) for e in closed]
        replaced[0] = {**closed[0], **fields}
        return replaced

    def without_first(*fields) -> list[dict]:
        replaced = [dict(e) for e in closed]
        replaced[0] = {k: v for k, v in closed[0].items() if k not in fields}
        return replaced

    write(
        "confirmed-without-person.json",
        _envelope(inventory, workbook, without_first("confirmed_by")),
    )
    write(
        "blank-person.json",
        _envelope(inventory, workbook, with_first(confirmed_by="   ")),
    )
    write(
        "non-string-person.json",
        _envelope(inventory, workbook, with_first(confirmed_by=7)),
    )

    ruled = next(e for e in closed if e.get("rule") == ROW_RULE)
    unknown_rule = [dict(e) for e in closed]
    unknown_rule[closed.index(ruled)] = {**ruled, "rule": "no-such-rule"}
    write("unknown-rule.json", _envelope(inventory, workbook, unknown_rule))

    non_string_rule = [dict(e) for e in closed]
    non_string_rule[closed.index(ruled)] = {**ruled, "rule": 3}
    write("non-string-rule.json", _envelope(inventory, workbook, non_string_rule))

    def table(**changes) -> dict:
        rules = json.loads(json.dumps(RULES))
        for rule_id, row in changes.items():
            rules[rule_id] = row
        return rules

    write(
        "rule-without-text.json",
        _envelope(inventory, workbook, closed, table(**{
            ROW_RULE: {**RULES[ROW_RULE], "text": "  "},
        })),
    )
    write(
        "rule-without-author.json",
        _envelope(inventory, workbook, closed, table(**{
            ROW_RULE: {**RULES[ROW_RULE], "stated_by": ""},
        })),
    )
    write("rules-not-object.json", _envelope(inventory, workbook, closed, []))
    write(
        "unsafe-rule-id.json",
        _envelope(inventory, workbook, closed, table(**{"../escaped": RULES[ROW_RULE]})),
    )

    # A draft may not pre-name its confirmer: the entry is unconfirmed, and
    # the fields would read as attribution the moment the boolean flipped.
    write(
        "unconfirmed-with-person.json",
        _envelope(inventory, workbook, with_first(
            confirmed=False, confirmed_by=PERSON_ONE,
        )),
    )
    only_rule = [dict(e) for e in closed]
    only_rule[0] = {**_draft(closed[0]), "rule": ROW_RULE}
    write("unconfirmed-with-rule.json", _envelope(inventory, workbook, only_rule))

    # The shape a set confirmed under dokimasia-v2.1.0 has: no table, no
    # person on any entry, drafts first and confirmations after them. It must
    # refuse on its first confirmed entry, naming the item and the field,
    # rather than be defaulted to anybody.
    prior = [_draft(e) for e in closed[:half]] + [
        {k: v for k, v in e.items() if k not in ("confirmed_by", "rule")}
        for e in closed[half:]
    ]
    write("prior-shape.json", _envelope(inventory, workbook, prior, None))

    # Each cap at its bound reconciles; one byte or one row over refuses.
    at_person = "p" * reconcile_lib.MAX_PERSON_BYTES
    write(
        "person-at-cap.json",
        _envelope(inventory, workbook, with_first(confirmed_by=at_person)),
    )
    write(
        "person-over-cap.json",
        _envelope(inventory, workbook, with_first(confirmed_by=at_person + "p")),
    )
    write(
        "author-at-cap.json",
        _envelope(inventory, workbook, closed, table(**{
            ROW_RULE: {**RULES[ROW_RULE], "stated_by": at_person},
        })),
    )
    write(
        "author-over-cap.json",
        _envelope(inventory, workbook, closed, table(**{
            ROW_RULE: {**RULES[ROW_RULE], "stated_by": at_person + "p"},
        })),
    )
    at_text = "t" * reconcile_lib.MAX_RULE_TEXT_BYTES
    write(
        "rule-text-at-cap.json",
        _envelope(inventory, workbook, closed, table(**{
            ROW_RULE: {**RULES[ROW_RULE], "text": at_text},
        })),
    )
    write(
        "rule-text-over-cap.json",
        _envelope(inventory, workbook, closed, table(**{
            ROW_RULE: {**RULES[ROW_RULE], "text": at_text + "t"},
        })),
    )
    at_id = "r" * reconcile_lib.MAX_RULE_ID_BYTES
    for name, rule_id in (
        ("rule-id-at-cap.json", at_id),
        ("rule-id-over-cap.json", at_id + "r"),
    ):
        renamed = [
            {**e, "rule": rule_id} if e.get("rule") == ROW_RULE else dict(e)
            for e in closed
        ]
        rules = {rule_id: RULES[ROW_RULE], UNUSED_RULE: RULES[UNUSED_RULE]}
        write(name, _envelope(inventory, workbook, renamed, rules))
    for name, rows in (
        ("rules-at-cap.json", reconcile_lib.MAX_RULES),
        ("rules-over-cap.json", reconcile_lib.MAX_RULES + 1),
    ):
        rules = {
            f"rule-{index:04d}": {"text": f"rule number {index}", "stated_by": PERSON_ONE}
            for index in range(rows - len(RULES))
        }
        rules.update(json.loads(json.dumps(RULES)))
        write(name, _envelope(inventory, workbook, closed, rules))

    return made


if __name__ == "__main__":
    for name in sorted(build_all(HERE)):
        print(name)
