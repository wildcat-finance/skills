#!/usr/bin/env python3
"""Metron budget check.

The mechanical subset of the skill: the part a file and a comparison can settle.
Everything else in SKILL.md stays a judgement, and nothing here measures anything.
A run arrives from whatever measured it, the same way `hexctl audit-round` takes a
lint exit the caller reports.

  check    compare a recorded run against the budgets and the baseline
  record   append a run to the ledger, and promote it to baseline when asked

A budget carries a limit and a variance, because SKILL.md asks for both. A limit
alone fails a run that is a fraction over on a noisy machine. A variance alone
never catches a value that was unacceptable from the day it was written.

Verdicts, one per declared budget:

  over-budget   worse than the limit                                fails
  regressed     worse than the baseline by more than the variance   fails
  neutral       inside the variance either way                      passes
  improved      better than the baseline by more than the variance  passes
  unmeasured    the run carries no value for a declared budget      fails
  undeclared    the run carries a value no budget declares          fails

The last two are the reason this is not a threshold script. A run that quietly
stops reporting a budget would otherwise pass, and a name nobody declared is
either a typo or a budget that was never written down.

Exit 0 when every verdict passes, 1 when any fails, 2 on a bad invocation or a
file that cannot be read.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
from pathlib import Path

MAX_BYTES = 4 * 1024 * 1024
"""These files are checked in beside the code, not fetched. A cap still keeps a
mistaken path from reading something enormous into memory."""

DIRECTIONS = ("lower_is_better", "higher_is_better")
"""Wall clock and bundle size are the first. Throughput and hit rate are the
second, and a check that assumed the first would call their improvement a
regression."""

REQUIRED = ("name", "unit", "limit", "variance", "direction")

PASSING = ("neutral", "improved")
FAILING = ("over-budget", "regressed", "unmeasured", "undeclared")


class BudgetError(ValueError):
    """A file that cannot be read as budgets, with the reason a caller can act on."""


def number(value) -> bool:
    """True for a finite real number this check will do arithmetic on.

    `bool` is excluded deliberately. Python makes `True` an integer, so a
    measurement of `true` would be compared against a limit and reported as a
    verdict.

    Non-finite is excluded for a sharper reason. Every comparison against `nan` is
    False, including `!=`, so a `nan` measurement does not fail a threshold: it
    falls through whichever branch happens to be tested last and is reported as
    whatever that branch says. An infinite limit means nothing ever exceeds it.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def refuse_constant(token: str):
    """Refuse the non-standard JSON constants at parse time.

    `json.loads` accepts `NaN`, `Infinity` and `-Infinity` by default, which are a
    Python extension rather than JSON. Refusing them here names the token, where
    catching them later could only say the value was not a number.
    """
    raise ValueError(f"{token} is not permitted; these files hold finite numbers")


def read_json(path: str, what: str):
    """A JSON document from disk, or a refusal naming what was being read."""
    where = Path(path)
    try:
        size = where.stat().st_size
    except OSError as error:
        raise BudgetError(f"cannot read {what} {path}: {error}")
    if size > MAX_BYTES:
        raise BudgetError(f"{what} {path} is larger than {MAX_BYTES} bytes")
    try:
        raw = where.read_bytes()
    except OSError as error:
        raise BudgetError(f"cannot read {what} {path}: {error}")
    try:
        return json.loads(raw.decode("utf-8"), parse_constant=refuse_constant)
    except (ValueError, UnicodeDecodeError) as error:
        raise BudgetError(f"{what} {path} is not readable JSON: {error}")


def load_budgets(path: str) -> list[dict]:
    """The declared budgets, in file order, with every field checked.

    Order is kept rather than sorted, because the file is reviewed by a person and
    the report should read the way the file does.
    """
    document = read_json(path, "budget file")
    if not isinstance(document, dict):
        raise BudgetError("budget file must hold an object")
    entries = document.get("budgets")
    if not isinstance(entries, list):
        raise BudgetError("budget file needs a budgets array")
    if not entries:
        raise BudgetError("budget file declares no budgets")

    budgets: list[dict] = []
    seen: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"budget {index + 1}"
        if not isinstance(entry, dict):
            raise BudgetError(f"{label} must be an object")
        absent = [field for field in REQUIRED if field not in entry]
        if absent:
            raise BudgetError(f"{label} is missing {', '.join(absent)}")
        name = entry["name"]
        if not isinstance(name, str) or not name.strip():
            raise BudgetError(f"{label} must name something")
        label = name
        if name in seen:
            raise BudgetError(f"budget {name} is declared twice")
        seen.add(name)
        if not isinstance(entry["unit"], str) or not entry["unit"].strip():
            raise BudgetError(f"{label} must state a unit")
        if not number(entry["limit"]):
            raise BudgetError(f"{label} limit must be a number, got {entry['limit']!r}")
        if entry["limit"] < 0:
            raise BudgetError(f"{label} limit must not be negative")
        variance = entry["variance"]
        if not number(variance):
            raise BudgetError(f"{label} variance must be a number, got {variance!r}")
        if not 0 <= variance < 1:
            raise BudgetError(
                f"{label} variance must be a fraction of the baseline from 0 up to "
                f"but not including 1, got {variance!r}"
            )
        if entry["direction"] not in DIRECTIONS:
            raise BudgetError(
                f"{label} direction must be one of {', '.join(DIRECTIONS)}, "
                f"got {entry['direction']!r}"
            )
        unknown = sorted(set(entry) - set(REQUIRED))
        if unknown:
            raise BudgetError(f"{label} carries unknown fields: {', '.join(unknown)}")
        budgets.append(dict(entry))
    return budgets


def load_measurements(path: str, what: str) -> dict:
    """A name-to-number mapping from a run or a baseline file.

    Two shapes read the same: the mapping on its own, or wrapped under
    `measurements` alongside whatever else the producer wanted to record. A
    document carrying both is refused rather than resolved, because taking the
    wrapped one drops the others in silence, and a dropped measurement is the
    difference between an `undeclared` verdict and no verdict at all.
    """
    document = read_json(path, what)
    if not isinstance(document, dict):
        raise BudgetError(f"{what} must hold an object of budget name to value")
    if "measurements" in document:
        stray = sorted(
            key for key, value in document.items()
            if key != "measurements" and number(value)
        )
        if stray:
            raise BudgetError(
                f"{what} carries measurements alongside a measurements block: "
                f"{', '.join(stray)}. Put every value inside the block, or none of "
                "them; taking one shape would drop the other without saying so"
            )
        values = document["measurements"]
    else:
        values = document
    if not isinstance(values, dict):
        raise BudgetError(f"{what} measurements must be an object")
    for name, value in sorted(values.items()):
        if not isinstance(name, str) or not name.strip():
            raise BudgetError(f"{what} names a budget with no name")
        if not number(value):
            raise BudgetError(f"{what} value for {name} must be a number, got {value!r}")
    return dict(values)


class Verdict:
    """One budget's outcome, with the numbers it was reached from."""

    def __init__(self, budget: dict, verdict: str, run=None, baseline=None,
                 margin=None, detail: str = ""):
        self.budget = budget
        self.verdict = verdict
        self.run = run
        self.baseline = baseline
        self.margin = margin
        self.detail = detail

    @property
    def name(self) -> str:
        return self.budget["name"] if isinstance(self.budget, dict) else str(self.budget)

    @property
    def failed(self) -> bool:
        return self.verdict in FAILING

    def line(self) -> str:
        mark = "FAIL" if self.failed else "ok"
        return f"{mark:4} {self.verdict:12} {self.name}  {self.detail}"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "verdict": self.verdict,
            "run": self.run,
            "baseline": self.baseline,
            "margin": self.margin,
            "detail": self.detail,
        }


def worse(value: float, than: float, direction: str) -> bool:
    """Whether `value` is on the bad side of `than` for this budget's direction."""
    if direction == "higher_is_better":
        return value < than
    return value > than


def drift(value: float, baseline: float, direction: str):
    """How far `value` moved from `baseline`, as a fraction, and which way.

    Returns the fraction of the baseline moved and True when the move is a
    regression. A baseline of zero has no fraction to be a proportion of, so the
    caller is told there is none rather than being handed a division.
    """
    if baseline == 0:
        return None, worse(value, baseline, direction)
    moved = abs(value - baseline) / abs(baseline)
    return moved, worse(value, baseline, direction)


def compare(budgets: list[dict], run: dict, baseline: dict) -> list[Verdict]:
    """One verdict per declared budget, plus one per undeclared measurement.

    Declared order first, so the report reads the way the budget file does, then any
    name the run carried that no budget declares.
    """
    verdicts: list[Verdict] = []
    for budget in budgets:
        name = budget["name"]
        if name not in run:
            verdicts.append(
                Verdict(budget, "unmeasured",
                        detail="the run carries no value for this budget")
            )
            continue
        value = run[name]
        unit = " " + budget["unit"]
        if worse(value, budget["limit"], budget["direction"]):
            verdicts.append(
                Verdict(budget, "over-budget", run=value,
                        baseline=baseline.get(name),
                        detail=f"{value}{unit} against a limit of {budget['limit']}{unit}")
            )
            continue
        if name not in baseline:
            verdicts.append(
                Verdict(budget, "neutral", run=value,
                        detail=f"{value}{unit}, inside the limit; no baseline to compare")
            )
            continue
        before = baseline[name]
        moved, regressed = drift(value, before, budget["direction"])
        variance = budget["variance"]
        if moved is None:
            # A zero baseline admits no proportion. Any move off it in the wrong
            # direction is a regression, and any other move is reported plainly.
            if regressed and value != before:
                verdicts.append(
                    Verdict(budget, "regressed", run=value, baseline=before,
                            detail=f"{before}{unit} to {value}{unit}; a zero baseline "
                                   "admits no variance")
                )
            else:
                verdicts.append(
                    Verdict(budget, "neutral", run=value, baseline=before,
                            detail=f"{before}{unit} to {value}{unit}")
                )
            continue
        moved_pct = f"{moved * 100:.1f}%"
        allowed = f"{variance * 100:.1f}%"
        if moved <= variance:
            verdicts.append(
                Verdict(budget, "neutral", run=value, baseline=before, margin=moved,
                        detail=f"{before}{unit} to {value}{unit}, {moved_pct} inside "
                               f"{allowed}; another sample")
            )
        elif regressed:
            verdicts.append(
                Verdict(budget, "regressed", run=value, baseline=before, margin=moved,
                        detail=f"{before}{unit} to {value}{unit}, {moved_pct} worse, "
                               f"past {allowed}")
            )
        else:
            verdicts.append(
                Verdict(budget, "improved", run=value, baseline=before, margin=moved,
                        detail=f"{before}{unit} to {value}{unit}, {moved_pct} better, "
                               f"past {allowed}")
            )

    declared = {budget["name"] for budget in budgets}
    for name in sorted(set(run) - declared):
        verdicts.append(
            Verdict({"name": name}, "undeclared", run=run[name],
                    detail="the run measures this and no budget declares it")
        )
    return verdicts


def report(verdicts: list[Verdict], style: str) -> str:
    if style == "json":
        return json.dumps(
            {
                "verdicts": [v.to_dict() for v in verdicts],
                "failed": [v.name for v in verdicts if v.failed],
                "ok": not any(v.failed for v in verdicts),
            },
            indent=2,
        )
    lines = [v.line() for v in verdicts]
    failed = [v for v in verdicts if v.failed]
    if failed:
        lines.append(
            f"{len(failed)} of {len(verdicts)} budget(s) failed: "
            + ", ".join(v.name for v in failed)
        )
    else:
        lines.append(f"{len(verdicts)} budget(s), none failed")
    return "\n".join(lines)


def append_ledger(path: str, entry: dict) -> None:
    """One JSON object per line, appended.

    A line at a time rather than a rewritten document, so a run recorded while
    another is being read cannot truncate what was already there. SKILL.md asks for
    a ledger that keeps the reverted attempts too, and an append-only file is the
    shape that cannot lose one.
    """
    where = Path(path)
    if where.parent and not where.parent.exists():
        raise BudgetError(f"cannot write the ledger: {where.parent} does not exist")
    try:
        with where.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
    except OSError as error:
        raise BudgetError(f"cannot write the ledger {path}: {error}")


def write_atomically(path: str, body: str) -> None:
    """Replace a file's contents, or leave them alone.

    The baseline is what every later comparison is measured against, so a write that
    dies partway is worse than one that never started: the previous value is gone and
    nothing says so. A temporary file in the same directory keeps the replace on one
    filesystem.
    """
    where = Path(path)
    directory = str(where.parent) if str(where.parent) else "."
    handle = tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=directory, prefix=".metron-", suffix=".tmp",
        delete=False,
    )
    try:
        with handle:
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(handle.name, path)
    except BaseException:
        try:
            os.unlink(handle.name)
        except OSError:
            pass
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Metron budget check.")
    sub = parser.add_subparsers(dest="command", required=True)

    look = sub.add_parser("check", help="compare a run against the budgets and baseline")
    look.add_argument("--budgets", required=True)
    look.add_argument("--run", required=True)
    look.add_argument("--baseline")
    look.add_argument("--format", choices=("text", "json"), default="text")

    keep = sub.add_parser("record", help="append a run to the ledger")
    keep.add_argument("--budgets", required=True)
    keep.add_argument("--run", required=True)
    keep.add_argument("--ledger", required=True)
    keep.add_argument("--baseline")
    keep.add_argument("--note")
    keep.add_argument("--promote", action="store_true",
                      help="write this run over the baseline")
    return parser


def promote_needs_baseline(args) -> None:
    if getattr(args, "promote", False) and not args.baseline:
        raise BudgetError("--promote needs --baseline to say which file to write")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "record":
            promote_needs_baseline(args)
        budgets = load_budgets(args.budgets)
        run = load_measurements(args.run, "run")
        baseline = load_measurements(args.baseline, "baseline") if args.baseline else {}
        verdicts = compare(budgets, run, baseline)
        if args.command == "record":
            append_ledger(
                args.ledger,
                {
                    "run": args.run,
                    "note": args.note,
                    "measurements": run,
                    "verdicts": [v.to_dict() for v in verdicts],
                },
            )
            if args.promote:
                try:
                    write_atomically(
                        args.baseline,
                        json.dumps({"measurements": run}, indent=2, sort_keys=True) + "\n",
                    )
                except OSError as error:
                    raise BudgetError(f"cannot write the baseline {args.baseline}: {error}")
    except BudgetError as error:
        print(f"metron: error: {error}", file=sys.stderr)
        return 2

    if args.command == "record":
        promoted = " and promoted to baseline" if args.promote else ""
        print(f"metron: recorded {len(run)} measurement(s) in {args.ledger}{promoted}")
        return 0

    print(report(verdicts, args.format))
    return 1 if any(v.failed for v in verdicts) else 0


if __name__ == "__main__":
    sys.exit(main())
