#!/usr/bin/env python3
"""Expose pending conformance operations without manufacturing a report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import stat


CANDIDATES = ("process-parent-runner", "manual-conformance", "typed-applicability")
OPERATIONS = {
    "applicability-parser": 2,
    "bounded-reader": 2,
    "frozen-controller-join": 3,
    "native-execution": 4,
    "bounded-execution": 4,
    "legacy-and-hostile-replay": 4,
}


class Refusal(Exception):
    """Carry a fixed refusal code without caller data or filesystem details."""


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise Refusal("invalid-arguments")


def check_report_slot(raw: str, root: Path) -> None:
    """Check a JSON operand under root/.hexaemeron/reports without writing it.

    Refuse occupied leaves, linked ancestors and unsupported path spellings.
    This inspection makes no concurrency claim; this scaffold never writes.
    """
    if (
        len(raw) > 1024
        or "\\" in raw
        or any(part in (".", "..") for part in raw.split("/"))
        or any(ord(char) < 32 or ord(char) > 126 for char in raw)
    ):
        raise Refusal("report-path-invalid")
    path = Path(raw)
    if path.is_absolute():
        try:
            path = path.relative_to(root)
        except ValueError:
            raise Refusal("report-path-invalid") from None
    parts = path.parts
    if (
        len(parts) < 3
        or parts[:2] != (".hexaemeron", "reports")
        or path.suffix != ".json"
        or any(re.fullmatch(r"[A-Za-z0-9_.-]+", part) is None for part in parts)
    ):
        raise Refusal("report-path-invalid")
    cursor = root
    for index, part in enumerate(parts):
        cursor = cursor / part
        try:
            mode = cursor.lstat().st_mode
        except FileNotFoundError:
            return
        except OSError:
            raise Refusal("report-path-unavailable") from None
        if index == len(parts) - 1:
            raise Refusal("report-exists")
        if not stat.S_ISDIR(mode):
            raise Refusal("report-path-invalid")


def main(argv: list[str] | None = None) -> int:
    """Return 2 and one bounded JSON refusal; no conformance operation runs."""
    parser = Parser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    parser.add_argument("--criterion", required=True, choices=tuple(OPERATIONS))
    parser.add_argument("--report", required=True)
    result = {
        "schema": "native-guard-admission-refusal/v1",
        "candidate": None,
        "criterion": None,
        "available_step": None,
        "report_written": False,
        "code": "invalid-arguments",
    }
    try:
        args = parser.parse_args(argv)
        result.update(
            candidate=args.candidate,
            criterion=args.criterion,
            available_step=OPERATIONS[args.criterion],
        )
        check_report_slot(args.report, Path.cwd())
        raise Refusal("operation-unavailable")
    except Refusal as error:
        result["code"] = str(error)
    except OSError:
        result["code"] = "report-path-unavailable"
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
