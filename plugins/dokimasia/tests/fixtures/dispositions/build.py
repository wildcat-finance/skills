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


def _envelope(inventory: dict, workbook: dict, entries: list[dict]) -> dict:
    return {
        "schema": SCHEMA,
        "inventory_sha256": inventory["inventory_sha256"],
        "workbook_sha256": workbook["workbook_sha256"],
        "dispositions": entries,
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
            })
        elif entry["kind"] == "guard":
            entries.append({
                "item": target,
                "disposition": "manual",
                "reason": "the gate is checked by a person against the access matrix",
                "confirmed": True,
            })
        elif entry["kind"] == "action":
            entries.append({
                "item": target,
                "disposition": "excluded",
                "reason": "the action is exercised only through the routes above",
                "confirmed": True,
            })
        else:
            entries.append({
                "item": target,
                "disposition": "manual",
                "reason": "the row is owned by the reviewer who wrote it",
                "confirmed": True,
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
    }
    write("case-covered-by-itself.json", _envelope(inventory, workbook, circular))

    wrong = [dict(e) for e in closed]
    wrong[0] = {**closed[0], "disposition": "partial"}
    write("bad-vocabulary.json", _envelope(inventory, workbook, wrong))

    # Confirmation fixtures. ADR-002 makes `confirmed` the only thing that
    # admits an entry, so these cover the four states a set can be in and the
    # two ways the field itself can be wrong.
    drafted = [{**e, "confirmed": False} for e in closed]
    write("all-unconfirmed.json", _envelope(inventory, workbook, drafted))

    half = len(closed) // 2
    mixed = [
        {**e, "confirmed": index < half} for index, e in enumerate(closed)
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

    return made


if __name__ == "__main__":
    for name in sorted(build_all(HERE)):
        print(name)
