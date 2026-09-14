#!/usr/bin/env python3
"""Resolve one cell of the study and runbook link-gate design record.

Run it from the directory that holds design-evidence.json:

    python3 resolve.py --candidate <id> --criterion <id>
    python3 resolve.py --candidate <id> --criterion <id> --out <new file>
    python3 resolve.py --all

The first form prints the exact report bytes. The second also writes them to
a path that must not exist; the file is created exclusively and never
replaced. The third prints every value and writes nothing.

Every repository input is a Git blob at PINNED_COMMIT: the bundled Hypomnema
checker, the Fiat skill and the reviewed-span fixture. A value therefore
reproduces after later steps change the working tree. Probes run in a fresh
directory under <repository root>/tmp/, which is removed before exit, together
with tmp/ itself when this process created it.

Each candidate is an executable prototype of its receipt-time rule:

  declare-only                  refuse unless --skills names the link lint
  lint-in-place                 run the Hypomnema check where the artefact sits
  require-location-independent  load the bundled Hypomnema parser, refuse a
                                recognised link or runbook pointer that is
                                neither an absolute URL nor an in-page anchor,
                                then run the Hypomnema check

controller-surface-bytes is the source size of those prototypes. The third
loads Hypomnema's own parser rather than copying it, so that parser's bytes are
not counted. It estimates a controller change that has not been written; it is
not a measurement of that change. check-latency-ms is a median of timed runs,
includes that load, and varies between runs.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

PINNED_COMMIT = "485c90d3ad545b696584197f83d942c705988216"
HYPOMNEMA = "plugins/hexaemeron/skills/hypomnema/scripts/hypomnema.py"
FIAT_SKILL = "plugins/hexaemeron/skills/fiat/SKILL.md"
SPANS = "tests/fixtures/agent-instruction-v1/fiat-study-runbook-phase/source-spans.json"
REPORT_SCHEMA = "protasis-design-report/v1"
LINK_LINT = "hexaemeron:hypomnema"
DECLARED = ("hexaemeron:imprimatur", LINK_LINT)
UNDECLARED = ("hexaemeron:imprimatur",)
TIMED_RUNS = 21

# Where each probe artefact sits, relative to the probe's own root.
RECEIPT = ".hexaemeron/study.md"
SHALLOW = "docs/link-gate/study.md"
DEEP = "plugins/hexaemeron/docs/link-gate/study.md"

# The five citations the run that landed skills#1070 froze into its study.
SPECIMEN = "\n".join(
    ["# Specimen", ""]
    + [f"See [{name}](../{name}/SKILL.md) for its contract."
       for name in ("ephoros", "phylax", "metron", "elenchus", "hypomnema")]
) + "\n"

# Resolves from SHALLOW and not from DEEP, byte for byte as the retired run froze it.
DEPTH_SENSITIVE = (
    "# Specimen\n\n"
    "See [fiat](../../plugins/hexaemeron/skills/fiat/SKILL.md) for the loop.\n"
)

# The same citation, pinned to the starting commit.
CONFORMING = (
    "# Specimen\n\n"
    "See [fiat](https://github.com/wildcat-finance/skills/blob/"
    f"{PINNED_COMMIT}/plugins/hexaemeron/skills/fiat/SKILL.md) for the loop.\n"
)

CANDIDATES = ("declare-only", "lint-in-place", "require-location-independent")

# The one-sentence Fiat phase note each candidate would add after this anchor.
PHASE_NOTE_ANCHOR = b"skills that ran to the receipt."
PHASE_NOTES = {
    "declare-only": b" The receipt also refuses a --skills list that omits"
                    b" hexaemeron:hypomnema.",
    "lint-in-place": b" Both receipts also run the bundled Hypomnema link check"
                     b" over the artefact where it sits and refuse a non-zero"
                     b" exit before the digest is pinned.",
    "require-location-independent": b" Both receipts also refuse a link or"
                                    b" runbook pointer that is not an absolute"
                                    b" URL or an in-page anchor, then run the"
                                    b" bundled Hypomnema check, before the"
                                    b" digest is pinned.",
}
VERSION_LINE = (b'  version: "6.56.1"\n', b'  version: "6.57.1"\n')

# The Hypomnema names the location rule loads rather than re-deriving.
CHECKER_INTERFACE = ("LINK", "RUNBOOK", "suppressed", "_external", "_code_spans", "_within")


class Refusal(Exception):
    """A bounded refusal printed without a traceback."""


def git(root: Path, *argv: str) -> bytes:
    environment = dict(os.environ, GIT_NO_REPLACE_OBJECTS="1", GIT_TERMINAL_PROMPT="0")
    completed = subprocess.run(
        ["git", "-C", str(root), *argv],
        capture_output=True, timeout=60, env=environment, check=False,
    )
    if completed.returncode != 0:
        raise Refusal(f"git {argv[0]} failed with exit {completed.returncode}")
    return completed.stdout


def repository_root() -> Path:
    here = Path(__file__).resolve().parent
    top = git(here, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    return Path(top)


def blob(root: Path, path: str) -> bytes:
    return git(root, "cat-file", "blob", f"{PINNED_COMMIT}:{path}")


def run_link_check(checker: Path, artefact: Path, cwd: Path) -> int:
    """Run the bundled checker on one artefact and return its exit status."""
    completed = subprocess.run(
        [sys.executable, str(checker), str(artefact)],
        capture_output=True, timeout=120, cwd=cwd, check=False,
        env=dict(os.environ, NO_COLOR="1", PYTHONDONTWRITEBYTECODE="1"),
    )
    return completed.returncode


def load_checker_module(path: Path):
    """Load the bundled checker's parser, refusing a missing or changed interface."""
    try:
        spec = importlib.util.spec_from_file_location("bundled_hypomnema", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    except (Exception, SystemExit) as error:
        raise Refusal("the bundled link checker cannot be loaded") from error
    if not all(hasattr(module, name) for name in CHECKER_INTERFACE):
        raise Refusal("the bundled link checker no longer exposes its parser")
    return module


def location_dependent_pointers(hypomnema, text: str) -> list[tuple[int, str]]:
    """Recognised pointers whose target depends on the artefact's directory."""
    lines = text.splitlines()
    found = []
    in_fence = False
    for number, line in enumerate(lines, start=1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or hypomnema.suppressed(lines, number):
            continue
        links = list(hypomnema.LINK.finditer(line))
        pointers = list(hypomnema.RUNBOOK.finditer(line))
        spans = hypomnema._code_spans(line) if (links or pointers) else ()
        for match in links:
            target = match.group("target")
            if hypomnema._within(spans, match.start()):
                continue
            if target.startswith("#") or hypomnema._external(target):
                continue
            found.append((number, target))
        for match in pointers:
            target = match.group("path").strip("`\"'")
            if hypomnema._within(spans, match.start()) or hypomnema._external(target):
                continue
            found.append((number, target))
    return found


def gate_declare_only(probe, artefact: Path, declared) -> bool:
    return LINK_LINT in set(declared)


def gate_lint_in_place(probe, artefact: Path, declared) -> bool:
    return run_link_check(probe.checker, artefact, probe.root) == 0


def gate_require_location_independent(probe, artefact: Path, declared) -> bool:
    hypomnema = load_checker_module(probe.checker)
    text = artefact.read_text(encoding="utf-8")
    if location_dependent_pointers(hypomnema, text):
        return False
    return run_link_check(probe.checker, artefact, probe.root) == 0


GATES = {
    "declare-only": gate_declare_only,
    "lint-in-place": gate_lint_in_place,
    "require-location-independent": gate_require_location_independent,
}


class Probe:
    """A throwaway tree under <repository root>/tmp/, removed on exit."""

    def __init__(self, repository: Path) -> None:
        self.repository = repository
        self.scratch_parent = repository / "tmp"
        self.created_parent = False
        self.holder: Path | None = None
        self.hypomnema_source = blob(repository, HYPOMNEMA)
        self.skill_source = blob(repository, FIAT_SKILL)
        self.spans_source = blob(repository, SPANS)
        self.skill_sha256 = hashlib.sha256(self.skill_source).hexdigest()

    def __enter__(self) -> "Probe":
        if not self.scratch_parent.exists():
            self.scratch_parent.mkdir()
            self.created_parent = True
        self.holder = Path(tempfile.mkdtemp(prefix="link-gate-probe-", dir=self.scratch_parent))
        self.root = self.holder / "root"
        self.checker = self.holder / "checker" / "hypomnema.py"
        self.checker.parent.mkdir(parents=True)
        self.checker.write_bytes(self.hypomnema_source)
        target = self.root / FIAT_SKILL
        target.parent.mkdir(parents=True)
        target.write_bytes(self.skill_source)
        return self

    def __exit__(self, *exc) -> None:
        if self.holder is not None:
            shutil.rmtree(self.holder, ignore_errors=True)
        if self.created_parent:
            try:
                self.scratch_parent.rmdir()
            except OSError:
                pass

    def place(self, relative: str, body: str) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def decide(self, candidate: str, relative: str, body: str, declared) -> bool:
        artefact = self.place(relative, body)
        try:
            return GATES[candidate](self, artefact, declared)
        finally:
            artefact.unlink()


def catches_observed_defect(probe: Probe, candidate: str) -> int:
    """1 when the receipt refuses the frozen specimen where it is receipted."""
    return 0 if probe.decide(candidate, RECEIPT, SPECIMEN, DECLARED) else 1


def verdict_location_independent(probe: Probe, candidate: str) -> int:
    """1 when a link verdict on identical bytes is the same at two depths.

    A decision counts as a link verdict only if changing the link alone, at the
    same depth, changes it. A rule that never reads the artefact returns one
    decision everywhere and is not a verdict about links.
    """
    sensitive_shallow = probe.decide(candidate, SHALLOW, DEPTH_SENSITIVE, DECLARED)
    sensitive_deep = probe.decide(candidate, DEEP, DEPTH_SENSITIVE, DECLARED)
    conforming_shallow = probe.decide(candidate, SHALLOW, CONFORMING, DECLARED)
    conforming_deep = probe.decide(candidate, DEEP, CONFORMING, DECLARED)
    reads_links = (sensitive_shallow != conforming_shallow) or (sensitive_deep != conforming_deep)
    return 1 if reads_links and sensitive_shallow == sensitive_deep else 0


def reviewed_span_bytes_touched(probe: Probe, candidate: str) -> int:
    """Bytes inside any reviewed span that differ after the candidate's edit.

    The edit is the owed version line plus the candidate's phase note.
    """
    original = probe.skill_source
    if original.count(PHASE_NOTE_ANCHOR) != 1 or original.count(VERSION_LINE[0]) != 1:
        raise Refusal("pinned Fiat skill no longer carries exactly one edit anchor")
    at = original.index(PHASE_NOTE_ANCHOR) + len(PHASE_NOTE_ANCHOR)
    edited = original[:at] + PHASE_NOTES[candidate] + original[at:]
    edited = edited.replace(VERSION_LINE[0], VERSION_LINE[1], 1)
    spans = json.loads(probe.spans_source)
    if spans["source"]["sha256"] != probe.skill_sha256:
        raise Refusal("reviewed spans do not bind the pinned Fiat skill")
    positions = set()
    for span in spans["spans"]:
        positions.update(range(int(span["start"]), int(span["end"])))
    return sum(
        1 for index in positions
        if index >= len(edited) or edited[index] != original[index]
    )


def enforces_result_not_declaration(probe: Probe, candidate: str) -> int:
    """1 when the decision follows the check result and not the declared ids."""
    failing_but_declared = probe.decide(candidate, RECEIPT, SPECIMEN, DECLARED)
    passing_but_undeclared = probe.decide(candidate, RECEIPT, CONFORMING, UNDECLARED)
    return 1 if (not failing_but_declared and passing_but_undeclared) else 0


def controller_surface_bytes(probe: Probe, candidate: str) -> int:
    """Source bytes of the candidate's prototype rule; an estimate, not a diff."""
    def size(function) -> int:
        return len(inspect.getsource(function).encode("utf-8"))
    if candidate == "declare-only":
        return size(gate_declare_only)
    if candidate == "lint-in-place":
        return size(gate_lint_in_place) + size(run_link_check)
    return (
        size(gate_require_location_independent)
        + size(run_link_check)
        + size(location_dependent_pointers)
        + size(load_checker_module)
    )


def check_latency_ms(probe: Probe, candidate: str) -> int:
    """Median milliseconds of the full check over a conforming artefact."""
    artefact = probe.place(RECEIPT, CONFORMING)
    gate = GATES[candidate]
    try:
        gate(probe, artefact, DECLARED)
        samples = []
        for _ in range(TIMED_RUNS):
            started = time.perf_counter_ns()
            gate(probe, artefact, DECLARED)
            samples.append(time.perf_counter_ns() - started)
    finally:
        artefact.unlink()
    return int(statistics.median(samples) / 1_000_000 + 0.5)


CRITERIA = {
    "catches-observed-defect": ("count", catches_observed_defect),
    "verdict-location-independent": ("count", verdict_location_independent),
    "reviewed-span-bytes-touched": ("count", reviewed_span_bytes_touched),
    "enforces-result-not-declaration": ("count", enforces_result_not_declaration),
    "controller-surface-bytes": ("bytes", controller_surface_bytes),
    "check-latency-ms": ("milliseconds", check_latency_ms),
}


def report_bytes(candidate: str, criterion: str, value: int) -> bytes:
    report = {
        "schema": REPORT_SCHEMA,
        "candidate": candidate,
        "criterion": criterion,
        "value": value,
        "unit": CRITERIA[criterion][0],
        "command": f"python3 resolve.py --candidate {candidate} --criterion {criterion}",
        "exit": 0,
    }
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


def write_exclusively(path: Path, data: bytes) -> None:
    if os.path.lexists(path):
        raise Refusal(f"refusing to replace an existing path: {path}")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o644)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
        handle.flush()
        os.fsync(handle.fileno())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Resolve one link-gate design cell.")
    parser.add_argument("--candidate", choices=CANDIDATES)
    parser.add_argument("--criterion", choices=tuple(CRITERIA))
    parser.add_argument("--out", help="a new file to create; an existing path is refused")
    parser.add_argument("--all", action="store_true", help="print every value; write nothing")
    args = parser.parse_args(argv)
    if args.all:
        if args.candidate or args.criterion or args.out:
            parser.error("--all takes no other option")
    elif not (args.candidate and args.criterion):
        parser.error("--candidate and --criterion are required together")
    try:
        if args.out and os.path.lexists(args.out):
            raise Refusal(f"refusing to replace an existing path: {args.out}")
        repository = repository_root()
        git(repository, "cat-file", "-e", f"{PINNED_COMMIT}^{{commit}}")
        with Probe(repository) as probe:
            if args.all:
                for criterion, (_, measure) in CRITERIA.items():
                    for candidate in CANDIDATES:
                        print(f"{candidate:30} {criterion:32} {measure(probe, candidate)}")
                return 0
            value = CRITERIA[args.criterion][1](probe, args.candidate)
        data = report_bytes(args.candidate, args.criterion, value)
        sys.stdout.buffer.write(data)
        sys.stdout.flush()
        if args.out:
            write_exclusively(Path(args.out), data)
        return 0
    except (Refusal, OSError, subprocess.TimeoutExpired) as error:
        print(f"resolve.py: refused: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
