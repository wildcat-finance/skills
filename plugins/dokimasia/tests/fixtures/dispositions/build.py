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
            })
        elif entry["kind"] == "guard":
            entries.append({
                "item": target,
                "disposition": "manual",
                "reason": "the gate is checked by a person against the access matrix",
            })
        elif entry["kind"] == "action":
            entries.append({
                "item": target,
                "disposition": "excluded",
                "reason": "the action is exercised only through the routes above",
            })
        else:
            entries.append({
                "item": target,
                "disposition": "manual",
                "reason": "the row is owned by the reviewer who wrote it",
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
        "item": covered["item"], "disposition": "covered",
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
        }]),
    )

    wrong = [dict(e) for e in closed]
    wrong[0] = {**closed[0], "disposition": "partial"}
    write("bad-vocabulary.json", _envelope(inventory, workbook, wrong))

    return made


if __name__ == "__main__":
    for name in sorted(build_all(HERE)):
        print(name)
