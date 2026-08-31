#!/usr/bin/env python3
"""Dokimasia: what did a release leave unexamined?

The scaffold ships the command surface, the self-test behind it, and nothing
else. `selftest` proves that the packaging, the contract and the ledger agree
on one version, that the installed law copy has not drifted, and that every
unbuilt verb refuses. Every other verb refuses by name and says which runbook
step owes it, because a verb that returned zero here would read as a scrutiny
that found nothing to report.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dokimasia_lib import inventory as inventory_lib  # noqa: E402
from dokimasia_lib import paths as paths_lib  # noqa: E402

PLUGIN = Path(__file__).resolve().parents[1]
REPOSITORY = PLUGIN.parents[1]
SKILL = PLUGIN / "skills" / "dokimasia" / "SKILL.md"
LEDGER = PLUGIN / "skills" / "dokimasia" / "EVOLUTION.md"
INSTALLED_LAW = PLUGIN / "PROMISE_MACHINE.md"
ROOT_LAW = REPOSITORY / "PROMISE_MACHINE.md"

VERSION = "0.1.0"
CANDIDATE = "inventory-first"
CRITERION = "scaffold-contract-check"
REPORT_SCHEMA = "protasis-design-report/v1"
REPORT_COMMAND = (
    "python3 plugins/dokimasia/scripts/dokimasia.py selftest --report {report}"
)

# Every verb the completed design owes, and the runbook step that owes it.
UNBUILT_VERBS = {
    "workbook": (3, "Import a reviewed spreadsheet into a closed record."),
    "reconcile": (4, "Assign exactly one disposition to every scoped item."),
    "demonstrate": (5, "Run one complete scrutiny and emit its record."),
}

REPORT_BYTES_MAX = 64 * 1024
NOT_BUILT = 3
REFUSED = 2

FRONTMATTER_VERSION = re.compile(r'^  version: "(?P<value>[^"]+)"$', re.M)
LEDGER_VERSION = re.compile(r"^- Current version: `dokimasia-v(?P<value>[^`]+)`$", re.M)


class SelfTestError(Exception):
    """One named disagreement between the packaging and the contract."""


def read_text(path: Path) -> str:
    if not path.is_file() or path.is_symlink():
        raise SelfTestError(f"{path} is not a regular file")
    return path.read_text(encoding="utf-8")


def declared_versions() -> dict[str, str]:
    """Every place this plugin states a version, keyed by where it said it."""
    found: dict[str, str] = {}
    for host in (".claude-plugin", ".codex-plugin"):
        manifest = json.loads(read_text(PLUGIN / host / "plugin.json"))
        found[host] = manifest["version"]
    skill = FRONTMATTER_VERSION.search(read_text(SKILL))
    if skill is None:
        raise SelfTestError("the canonical contract declares no frontmatter version")
    found["SKILL.md"] = skill.group("value")
    ledger = LEDGER_VERSION.search(read_text(LEDGER))
    if ledger is None:
        raise SelfTestError("the ledger declares no current version")
    found["EVOLUTION.md"] = ledger.group("value")
    found["command"] = VERSION
    return found


def check_one_version() -> None:
    found = declared_versions()
    distinct = sorted(set(found.values()))
    if len(distinct) != 1:
        detail = ", ".join(f"{where}={value}" for where, value in sorted(found.items()))
        raise SelfTestError(f"the declared version differs: {detail}")


def check_installed_law() -> None:
    if read_text(INSTALLED_LAW) != read_text(ROOT_LAW):
        raise SelfTestError(
            f"{INSTALLED_LAW} is not byte-identical to the root law at {ROOT_LAW}"
        )


def check_every_unbuilt_verb_refuses() -> None:
    # Probe the real refusal path rather than the table, so a verb wired to
    # answer is caught here. Its diagnosis belongs to whoever called the verb,
    # not to the self-test, so the probe's stderr is discarded.
    for verb in UNBUILT_VERBS:
        with contextlib.redirect_stderr(io.StringIO()):
            observed = refuse(verb)
        if observed == 0:
            raise SelfTestError(f"the unbuilt verb {verb} answered instead of refusing")


def safe_report_path(supplied: str) -> Path:
    path = Path(supplied)
    if not path.is_absolute():
        path = Path.cwd() / path
    # Test the supplied path, not the resolved one. `resolve()` follows every
    # symlink it meets, so a check made after it can never see one: it would
    # read as a guard and refuse nothing.
    if path.is_symlink():
        raise SelfTestError(f"{supplied} is a symlink")
    resolved = path.resolve()
    if resolved.exists() and not resolved.is_file():
        raise SelfTestError(f"{supplied} exists and is not a regular file")
    return resolved


def write_report_bytes(path: Path, body: str) -> None:
    """Write any body to a checked path through a staging file."""
    if len(body.encode("utf-8")) > REPORT_BYTES_MAX * 64:
        raise SelfTestError("the record exceeds its declared byte cap")
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.parent / f".{path.name}.{os.getpid()}.tmp"
    staging.write_text(body, encoding="utf-8")
    os.replace(staging, path)


def write_report(path: Path, criterion: str = None, command: str = None) -> None:
    body = json.dumps(
        {
            "candidate": CANDIDATE,
            "command": command or REPORT_COMMAND.format(report=path),
            "criterion": criterion or CRITERION,
            "exit": 0,
            "schema": REPORT_SCHEMA,
            "unit": "boolean",
            "value": True,
        },
        indent=2,
        sort_keys=True,
    ) + "\n"
    if len(body.encode("utf-8")) > REPORT_BYTES_MAX:
        raise SelfTestError("the report exceeds its declared byte cap")
    path.parent.mkdir(parents=True, exist_ok=True)
    staging = path.parent / f".{path.name}.{os.getpid()}.tmp"
    staging.write_text(body, encoding="utf-8")
    os.replace(staging, path)


def selftest(report: str | None) -> int:
    try:
        check_one_version()
        check_installed_law()
        check_every_unbuilt_verb_refuses()
        if report is not None:
            write_report(safe_report_path(report))
    except (SelfTestError, OSError, ValueError, KeyError) as error:
        sys.stderr.write(f"dokimasia selftest refused: {error}\n")
        return REFUSED
    sys.stdout.write(
        f"dokimasia selftest: clean; dokimasia-v{VERSION}; "
        f"{len(UNBUILT_VERBS)} unbuilt verb(s) refuse\n"
    )
    return 0


def refuse(verb: str) -> int:
    step, description = UNBUILT_VERBS[verb]
    sys.stderr.write(
        f"dokimasia {verb} is not built yet: this is the scaffold "
        f"(dokimasia-v{VERSION}). {description} Step {step} of "
        f"plugins/dokimasia/docs/dokimasia-runbook.md owes it.\n"
    )
    return NOT_BUILT


INVENTORY_CANDIDATE = "inventory-first"
INVENTORY_CRITERION = "inventory-determinism"
FIXTURE_ROOT = PLUGIN / "tests" / "fixtures" / "app"


def inventory_command(root: str | None, report: str | None, check: bool) -> int:
    """Compile an inventory, or prove the compiler holds its own contract."""
    try:
        if check:
            failures = inventory_lib.check(paths_lib.declared_root(FIXTURE_ROOT))
            if failures:
                sys.stderr.write(
                    "dokimasia inventory --check failed:\n"
                    + "".join(f"  - {line}\n" for line in failures)
                )
                return REFUSED
            if report is not None:
                write_report(
                    safe_report_path(report),
                    INVENTORY_CRITERION,
                    "python3 plugins/dokimasia/scripts/dokimasia.py inventory --check",
                )
            sys.stdout.write(
                "dokimasia inventory: check clean; two compiles agree and "
                f"{len(inventory_lib.refusal_proofs())} declared refusals fired\n"
            )
            return 0
        if root is None:
            raise SelfTestError("inventory needs --root <checkout> or --check")
        resolved = paths_lib.declared_root(root)
        items = inventory_lib.compile_inventory(resolved)
        record_body = inventory_lib.record(items, {"label": str(root)})
        body = json.dumps(record_body, indent=2, sort_keys=True) + "\n"
        if report is not None:
            write_report_bytes(safe_report_path(report), body)
        else:
            sys.stdout.write(body)
        return 0
    except (SelfTestError, paths_lib.PathRefusal, inventory_lib.InventoryError,
            OSError, ValueError) as error:
        sys.stderr.write(f"dokimasia inventory refused: {error}\n")
        return REFUSED


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dokimasia",
        description=(
            "Compile a frontend's routes, actions and guards into a coverage "
            "denominator and reconcile a reviewed workbook against it. A "
            "scrutiny states what has no reviewed oracle, never that anything "
            "passed."
        ),
    )
    parser.add_argument(
        "--version", action="version", version=f"dokimasia {VERSION} (scaffold)"
    )
    subparsers = parser.add_subparsers(dest="verb")
    selftest_parser = subparsers.add_parser(
        "selftest", help="Prove the packaging, the contract and the ledger agree."
    )
    selftest_parser.add_argument("--report", default=None)
    inventory_parser = subparsers.add_parser(
        "inventory",
        help="Compile a pinned checkout into a closed, digest-bound inventory.",
    )
    inventory_parser.add_argument("--root", default=None)
    inventory_parser.add_argument("--report", default=None)
    inventory_parser.add_argument("--check", action="store_true")
    for verb, (step, description) in UNBUILT_VERBS.items():
        subparsers.add_parser(verb, help=f"{description} Not built; step {step} owes it.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.verb is None:
        parser.print_help()
        return 0
    if args.verb == "selftest":
        return selftest(args.report)
    if args.verb == "inventory":
        return inventory_command(args.root, args.report, args.check)
    return refuse(args.verb)


if __name__ == "__main__":
    raise SystemExit(main())
