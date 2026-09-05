#!/usr/bin/env python3
"""Show that the Wave Delta reinstatement holds on disk.

The study's problem statement said an engineer handed one of the estate issues
reads a retired protocol decision, a study that says it no longer governs, and a
review that says do not start. This script checks that each of those is fixed,
and exits non-zero the moment one is not.

It reads files and runs two unittest modules with a fixed argument list. It
writes nothing, takes no path but --repo, and starts no shell.
"""

from __future__ import annotations

import argparse
import pathlib
import re
import subprocess
import sys

RETIRED = ("ADR-029", "ADR-030", "ADR-031", "ADR-032")
SUCCESSOR_RE = re.compile(r"^ADR-(0[7-9]\d)-")
BANNER_PHRASE = "no longer govern"
FORWARD_HEADING = "## Forward pointer"
PINNED_AMENDMENT = "## Amendment: Mandatory local checkpoint hand-off (2026-08-30)"
PINNED_CLAUSES = (
    "its current home is always the fixed\nlocal checkpoint store under `<origin>/.hexaemeron/checkpoints/`",
    "The producing agent owns the save after every successful `done push` and at an\nexhausted `audit-verdict` boundary",
    "This is an interim transport rule, not the distributed checkpoint framework.",
)
ESTATE_RECORD = "docs/wave-delta-issue-estate-2026-09-02.md"
ESTATE_ISSUES = tuple(str(n) for n in range(859, 868))
PINNED_TEST_MODULES = ("tests.test_decision_records", "tests.test_fiat_checkpoint_decision_record")


class Result:
    """One condition, its verdict and the evidence behind it."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.failures: list[str] = []
        self.evidence: list[str] = []

    def fail(self, why: str) -> None:
        self.failures.append(why)

    def note(self, what: str) -> None:
        self.evidence.append(what)

    @property
    def ok(self) -> bool:
        return not self.failures


def read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8")


def condition_successors(repo: pathlib.Path) -> Result:
    """Each retired record names exactly one standing successor."""
    result = Result("every retired decision has one standing successor")
    decisions = repo / "docs" / "decisions"
    if not decisions.is_dir():
        result.fail(f"{decisions} is not a directory")
        return result
    successors: dict[str, list[str]] = {number: [] for number in RETIRED}
    for path in sorted(decisions.glob("ADR-*.md")):
        if not SUCCESSOR_RE.match(path.name):
            continue
        text = read(path)
        head = text.split("## Context", 1)[0]
        for number in RETIRED:
            if number in head:
                successors[number].append(path.name)
    for number in RETIRED:
        named = successors[number]
        if len(named) != 1:
            result.fail(f"{number} is named by {len(named)} standing successor(s): {named}")
        else:
            result.note(f"{number} -> {named[0]}")
        matches = sorted(decisions.glob(f"{number}-*.md"))
        if len(matches) != 1:
            result.fail(f"{number} does not resolve to one file under {decisions}")
        elif "Retired" not in read(matches[0]).split("## Context", 1)[0]:
            result.fail(f"{matches[0].name} no longer reads as Retired")
    return result


def condition_adr_028(repo: pathlib.Path) -> Result:
    """ADR-028 stays Accepted and keeps its mandatory local hand-off amendment."""
    result = Result("ADR-028 is Accepted and its hand-off amendment is intact")
    matches = sorted((repo / "docs" / "decisions").glob("ADR-028-*.md"))
    if len(matches) != 1:
        result.fail("ADR-028 does not resolve to one file")
        return result
    text = read(matches[0])
    status = text.split("## Context", 1)[0]
    if "Accepted" not in status:
        result.fail("ADR-028's status no longer reads Accepted")
    else:
        result.note("status reads Accepted")
    if PINNED_AMENDMENT not in text:
        result.fail("the mandatory local hand-off amendment heading is gone")
        return result
    section = text.split(PINNED_AMENDMENT, 1)[1].split("\n## ", 1)[0]
    for clause in PINNED_CLAUSES:
        if clause not in section:
            result.fail(f"a pinned clause is missing or changed: {clause.splitlines()[0][:60]}")
    if result.ok:
        result.note(f"{len(PINNED_CLAUSES)} pinned clauses present verbatim")
    return result


def condition_banners(repo: pathlib.Path) -> Result:
    """No governing document disclaims itself, and every historical one points forward."""
    result = Result("no governing document carries a disclaiming banner")
    for path in sorted((repo / "docs").glob("*.md")):
        text = read(path)
        lines = text.splitlines()
        banner: list[str] = []
        for line in lines[1:]:
            if line.startswith(">"):
                banner.append(line)
            elif banner and not line.strip():
                break
            elif banner:
                break
        head = " ".join(line.lstrip("> ").strip() for line in banner)
        head = " ".join(head.split())
        if BANNER_PHRASE not in head:
            continue
        if FORWARD_HEADING not in text:
            result.fail(f"{path.name} disclaims itself and names no forward pointer")
        else:
            result.note(f"{path.name} is historical and points forward")
    return result


def condition_estate(repo: pathlib.Path) -> Result:
    """The estate's current verdict names the reinstatement."""
    result = Result("the estate's current verdict names the reinstatement")
    record = repo / ESTATE_RECORD
    if not record.is_file():
        result.fail(f"{ESTATE_RECORD} is missing")
        return result
    text = read(record)
    for number in ESTATE_ISSUES:
        if f"### Issue #{number}" not in text:
            result.fail(f"#{number} has no published block in the record")
    if "ADR-069" not in text:
        result.fail("no published block names ADR-069")
    rows = [line for line in text.splitlines() if line.startswith("| #")]
    if len(rows) != len(ESTATE_ISSUES):
        result.fail(f"the readback table holds {len(rows)} rows, not {len(ESTATE_ISSUES)}")
    elif any(not row.rstrip().endswith("| yes |") for row in rows):
        result.fail("a readback row does not record agreement")
    else:
        result.note(f"{len(rows)} readback rows, all agreeing")
    return result


def condition_pinned_tests(repo: pathlib.Path) -> Result:
    """The two pinned decision-record modules still pass."""
    result = Result("the pinned decision-record tests pass")
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", *PINNED_TEST_MODULES],
        cwd=str(repo),
        capture_output=True,
        text=True,
        shell=False,
        timeout=600,
    )
    if completed.returncode != 0:
        tail = completed.stderr.strip().splitlines()[-1:] or ["no output"]
        result.fail(f"{' '.join(PINNED_TEST_MODULES)} exited {completed.returncode}: {tail[0]}")
    else:
        result.note("both modules exited 0")
    return result


CONDITIONS = (
    condition_successors,
    condition_adr_028,
    condition_banners,
    condition_estate,
    condition_pinned_tests,
)


def run(repo: pathlib.Path) -> int:
    results = [condition(repo) for condition in CONDITIONS]
    for result in results:
        mark = "ok  " if result.ok else "FAIL"
        print(f"{mark} {result.name}")
        for note in result.evidence:
            print(f"       {note}")
        for failure in result.failures:
            print(f"       {failure}")
    failed = [result for result in results if not result.ok]
    print()
    if failed:
        print(f"{len(failed)} of {len(results)} conditions failed")
        return 1
    print(f"all {len(results)} conditions hold")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="check that the Wave Delta reinstatement holds")
    parser.add_argument("--repo", required=True, help="repository root to read")
    args = parser.parse_args(argv)
    repo = pathlib.Path(args.repo).resolve()
    if not (repo / "docs" / "decisions").is_dir():
        print(f"{repo} has no docs/decisions directory", file=sys.stderr)
        return 2
    return run(repo)


if __name__ == "__main__":
    raise SystemExit(main())
