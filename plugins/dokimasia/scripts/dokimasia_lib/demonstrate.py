"""Run one complete scrutiny, and make a moved number explain itself.

A coverage figure that changes between two runs is worthless unless somebody
can say which of three things moved: the application, the reviewed workbook, or
this skill. The scrutiny record carries all three identities beside the result
for that reason, and `causes` compares two records and names the difference.

A number that moved with none of the three having moved is the failure this
exists to catch, and it is reported as unattributed rather than as a change.

The workbook is read where it lives. Its bytes are never written into a record
or committed: a scrutiny references cases by identifier, which is what a
coverage claim has to name, and carries no test step, expected result, comment
or evidence field from any row.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from . import inventory as inventory_lib
from . import reconcile as reconcile_lib
from . import workbook as workbook_lib

SCHEMA = "dokimasia-scrutiny/v1"

# Metron owns this. It is the budget the runbook states for one scrutiny; the
# observed duration is measured and recorded beside it, never substituted for
# it, so a later budget is set from evidence rather than from this number.
BUDGET_MS = 120_000

COMMIT = 40


class DemonstrationError(Exception):
    """One named refusal while demonstrating."""


def _short(digest: str) -> str:
    return digest[:12] if digest else ""


def scrutinise(
    app_root: Path,
    workbook_path: Path,
    version: str,
    application: dict,
    dispositions: dict | None = None,
) -> tuple[dict, dict]:
    """One scrutiny: compile, import, reconcile, and record what was examined.

    Returns the scrutiny record and the coverage record it wraps. The coverage
    record is the deterministic artefact that gets committed; the scrutiny
    record additionally carries the timing, which is measured and therefore
    moves between runs.
    """
    started = time.monotonic()

    items = inventory_lib.compile_inventory(app_root)
    inventory = inventory_lib.record(items, {"label": application.get("label", "")})

    log: list[dict] = []
    cases = workbook_lib.read_cases(workbook_path, sheet_log=log)
    workbook = workbook_lib.record(
        cases,
        {
            "label": workbook_path.name,
            "sha256": hashlib.sha256(workbook_path.read_bytes()).hexdigest(),
        },
        log,
    )

    declared = dispositions or {
        "schema": reconcile_lib.DISPOSITIONS_SCHEMA,
        "inventory_sha256": inventory["inventory_sha256"],
        "workbook_sha256": workbook["workbook_sha256"],
        "dispositions": [],
    }
    coverage = reconcile_lib.reconcile(inventory, workbook, declared)
    elapsed_ms = int((time.monotonic() - started) * 1000)

    commit = application.get("commit", "")
    if len(commit) != COMMIT or not all(c in "0123456789abcdef" for c in commit):
        raise DemonstrationError(
            f"the application commit {commit!r} is not a full 40-character "
            "object name; a scrutiny must pin what it examined"
        )

    scrutiny = {
        "schema": SCHEMA,
        "skill_version": version,
        "subject": {
            "application": {
                "label": application.get("label", ""),
                "commit": commit,
            },
            "workbook": workbook["subject"],
        },
        "examined": {
            "inventory_sha256": inventory["inventory_sha256"],
            "workbook_sha256": workbook["workbook_sha256"],
            "coverage_sha256": reconcile_lib.coverage_digest(coverage),
            "scoped": coverage["counts"]["scoped"],
            "inventory_items": coverage["counts"]["inventory_items"],
            "workbook_cases": coverage["counts"]["workbook_cases"],
        },
        "closure_ratio": coverage["closure_ratio"],
        "counts": coverage["counts"],
        "gaps": len(coverage["gaps"]),
        "undisposed": len(coverage["undisposed"]),
        "timing": {
            "observed_ms": elapsed_ms,
            "budget_ms": BUDGET_MS,
            "within_budget": elapsed_ms <= BUDGET_MS,
        },
    }
    return scrutiny, coverage


def _require_scrutiny(scrutiny: dict, label: str) -> None:
    """Refuse a record that is not a scrutiny record.

    Comparing two scrutinies means reading at least one of them off disk, so a
    truncated or hand-edited record is an ordinary mistake. Every other refusal
    in this plugin is named, and a `KeyError` here would be the one that is not.
    """
    for field in ("skill_version", "subject", "examined"):
        if field not in scrutiny:
            raise DemonstrationError(
                f"the {label} scrutiny record has no {field!r}, so it is not "
                "a scrutiny record"
            )
    subject = scrutiny["subject"]
    if not isinstance(subject, dict) or "application" not in subject:
        raise DemonstrationError(
            f"the {label} scrutiny record names no application"
        )
    if "commit" not in subject["application"]:
        raise DemonstrationError(
            f"the {label} scrutiny record's application has no commit, so a "
            "move could not be attributed to it"
        )
    if "coverage_sha256" not in scrutiny["examined"]:
        raise DemonstrationError(
            f"the {label} scrutiny record records no coverage digest, so "
            "nothing could be compared"
        )


def identity(scrutiny: dict) -> dict:
    """The three things whose movement can explain a moved result."""
    _require_scrutiny(scrutiny, "given")
    return {
        "application": scrutiny["subject"]["application"]["commit"],
        "workbook": scrutiny["subject"]["workbook"].get("sha256", ""),
        "skill": scrutiny["skill_version"],
    }


def causes(before: dict, after: dict) -> list[dict]:
    """Why the result moved, named one cause at a time.

    Study question 4. A moved coverage figure with none of the three
    identities moved is reported as unattributed, because a number nobody can
    explain is the thing this record exists to prevent.
    """
    _require_scrutiny(before, "earlier")
    _require_scrutiny(after, "later")
    was, now = identity(before), identity(after)
    found = [
        {
            "cause": name,
            "from": was[name],
            "to": now[name],
        }
        for name in ("application", "workbook", "skill")
        if was[name] != now[name]
    ]
    moved = (
        before["examined"]["coverage_sha256"] != after["examined"]["coverage_sha256"]
    )
    if moved and not found:
        found.append({
            "cause": "unattributed",
            "from": before["examined"]["coverage_sha256"],
            "to": after["examined"]["coverage_sha256"],
        })
    return found


def committed_scrutiny(scrutiny: dict) -> dict:
    """The scrutiny record as it is committed: everything but the timing.

    The coverage record beside it names the two digests it was built from and
    nothing about what built it, so on its own it cannot be attributed to an
    application commit or a skill version. Study question 4 needs that
    attribution to be machine-readable, not only stated in the prose, because
    the next release's comparison is a program reading this file.
    """
    body = {key: value for key, value in scrutiny.items() if key != "timing"}
    body["scrutiny_sha256"] = scrutiny_digest(scrutiny)
    return body


def canonical_bytes(scrutiny: dict) -> bytes:
    """Everything but the subject and the timing.

    Timing is measured, so including it would mean no two runs of the same
    inputs agreed on a digest.
    """
    body = {
        key: value for key, value in scrutiny.items()
        if key not in ("subject", "timing")
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")


def scrutiny_digest(scrutiny: dict) -> str:
    return hashlib.sha256(canonical_bytes(scrutiny)).hexdigest()


def render(scrutiny: dict, coverage: dict) -> str:
    """The scrutiny as prose a reader can check against the record beside it."""
    application = scrutiny["subject"]["application"]
    ratio = scrutiny["closure_ratio"]
    counts = scrutiny["counts"]
    examined = scrutiny["examined"]
    lines = [
        f"# Scrutiny of {application['label']}",
        "",
        "One scrutiny of one pinned commit against one reviewed workbook. This",
        "states what was examined and what carries no disposition. It does not",
        "state that anything passed.",
        "",
        "## What was examined",
        "",
        f"- Application: `{application['label']}` at `{application['commit']}`",
        f"- Workbook: `{scrutiny['subject']['workbook']['label']}`, "
        f"sha256 `{_short(scrutiny['subject']['workbook'].get('sha256', ''))}`",
        f"- Inventory digest: `{_short(examined['inventory_sha256'])}`",
        f"- Workbook digest: `{_short(examined['workbook_sha256'])}`",
        f"- Coverage digest: `{_short(examined['coverage_sha256'])}`",
        f"- Skill version: `dokimasia-v{scrutiny['skill_version']}`",
        "",
        "## The denominator",
        "",
        f"The scoped set holds **{counts['scoped']} items**: "
        f"{counts['inventory_items']} compiled from the application and "
        f"{counts['workbook_cases']} imported from the workbook.",
        "",
        "| Kind | Count |",
        "| --- | ---: |",
    ]
    kinds: dict[str, int] = {}
    for item in coverage["dispositions"] + [
        {"item": key} for key in coverage["undisposed"]
    ]:
        kinds[item["item"].split(":", 1)[0]] = kinds.get(
            item["item"].split(":", 1)[0], 0
        ) + 1
    for kind in sorted(kinds):
        lines.append(f"| `{kind}` | {kinds[kind]} |")
    lines += [
        "",
        "## Closure",
        "",
        f"- Numerator: **{ratio['numerator']}** items carrying one disposition",
        f"- Denominator: **{ratio['denominator']}** scoped items",
        f"- Ratio: **{ratio['value']:.4f}**",
        f"- Closed: **{'yes' if ratio['closed'] else 'no'}**",
        "",
    ]
    if ratio["closed"]:
        lines += [
            "Every scoped item carries a disposition. Nothing is unaccounted",
            "for. Nothing here says anything passed.",
            "",
        ]
    else:
        lines += [
            f"**{scrutiny['undisposed']} of {ratio['denominator']} scoped items "
            "carry no disposition.** Nobody has decided about them, so the",
            "ratio is open and the release has no coverage claim this record",
            "can support.",
            "",
            "This is the finding, not a failure of the run. The application",
            "contributes a denominator that did not exist before, and the",
            "workbook contributes rows nobody has joined to it.",
            "",
        ]
    lines += [
        "## Gaps",
        "",
    ]
    if coverage["gaps"]:
        lines += ["| Item | Disposition | Reason |", "| --- | --- | --- |"]
        for gap in coverage["gaps"]:
            lines.append(
                f"| `{gap['item']}` | `{gap['disposition']}` | {gap['reason']} |"
            )
    else:
        lines.append(
            "No item carries `manual` or `excluded`, so there is no reason list "
            "to review. That follows from the ratio above: nothing has been "
            "decided either way."
        )
    lines += [
        "",
        "## Neither side cites the other",
        "",
        f"- Application items no oracle is held to: "
        f"**{len(coverage['unmatched']['items_no_oracle_cites'])}**",
        f"- Workbook cases no item cites: "
        f"**{len(coverage['unmatched']['cases_no_item_cites'])}**",
        "",
        "The first is the uncovered application surface. The second is review",
        "effort the inventory does not know about.",
        "",
        "## Why a number here could move",
        "",
        "Three identities are recorded above: the application commit, the",
        "workbook digest and the skill version. A later scrutiny whose result",
        "differs names which of the three moved. A result that moved with none",
        "of them moved is reported as unattributed rather than as a change.",
        "",
    ]
    return "\n".join(lines) + "\n"


def fixture_root() -> Path:
    return Path(__file__).resolve().parents[2] / "tests" / "fixtures"


def check() -> list[str]:
    """Prove the contract this module claims, against committed fixtures."""
    failures: list[str] = []
    root = fixture_root()
    app = root / "app"
    workbooks = root / "workbooks"

    import importlib.util
    import tempfile

    spec = importlib.util.spec_from_file_location(
        "workbook_build", workbooks / "build.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    with tempfile.TemporaryDirectory() as raw:
        made = module.build_all(Path(raw))
        application = {"label": "tests/fixtures/app", "commit": "a" * 40}
        first, coverage = scrutinise(
            app, made["benign.xlsx"], "0.0.0-fixture", application
        )
        second, _ = scrutinise(
            app, made["benign.xlsx"], "0.0.0-fixture", application
        )

        if scrutiny_digest(first) != scrutiny_digest(second):
            failures.append("two scrutinies of the same inputs disagreed")
        if causes(first, second):
            failures.append(
                "two identical scrutinies reported a cause: "
                + json.dumps(causes(first, second))
            )
        if first["examined"]["scoped"] != coverage["counts"]["scoped"]:
            failures.append("the scrutiny and its coverage disagree on the scoped count")
        if first["closure_ratio"]["denominator"] != first["examined"]["scoped"]:
            failures.append("the denominator is not the scoped count")
        if not first["timing"]["within_budget"]:
            failures.append(
                f"the fixture scrutiny took {first['timing']['observed_ms']}ms, "
                f"over the {BUDGET_MS}ms budget"
            )

        # Each identity moving is reported as its own cause, and no other.
        for name, moved in (
            ("application", {**application, "commit": "b" * 40}),
            ("skill", application),
        ):
            other, _ = scrutinise(
                app,
                made["benign.xlsx"],
                "0.0.0-fixture" if name != "skill" else "9.9.9-fixture",
                moved,
            )
            named = [entry["cause"] for entry in causes(first, other)]
            if named != [name]:
                failures.append(
                    f"moving the {name} reported {named}, not exactly ['{name}']"
                )

        moved_workbook, _ = scrutinise(
            app, made["absolute-targets.xlsx"], "0.0.0-fixture", application
        )
        named = [entry["cause"] for entry in causes(first, moved_workbook)]
        if named != ["workbook"]:
            failures.append(
                f"moving the workbook reported {named}, not exactly ['workbook']"
            )

        # A result that moved with nothing moved must be reported, not hidden.
        forged = json.loads(json.dumps(first))
        forged["examined"]["coverage_sha256"] = "f" * 64
        named = [entry["cause"] for entry in causes(first, forged)]
        if named != ["unattributed"]:
            failures.append(
                f"an unexplained move reported {named}, not ['unattributed']"
            )

        prose = render(first, coverage)
        if application["commit"] not in prose:
            failures.append("the rendered scrutiny does not name the pinned commit")
        if str(first["closure_ratio"]["denominator"]) not in prose:
            failures.append("the rendered scrutiny does not state the denominator")
        if "never that anything passed" in prose and "passed" not in prose:
            failures.append("the rendered scrutiny lost its own boundary sentence")
    return failures
