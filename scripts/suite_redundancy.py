#!/usr/bin/env python3
"""Report which test files and test methods add no coverage of their own.

A test file's contribution to line coverage is exactly the set of source lines
its own tests executed, so removing the file removes exactly that set.  Per-test
attribution from one traced run therefore answers the same question as running
the suite once per file, at one run per suite rather than one per file.

The report is advisory.  Line coverage is insensitive to assertions: two tests
may execute identical lines and prove different properties, so a file that
covers nothing uniquely is a candidate for review and never a deletion.  The
converse is sound in the other direction - a file that uniquely covers a line
cannot be removed without losing that line - and that negative result is the
part of this report a reader can rely on.

Two states are reported separately from redundancy.  A test that drives its
subject through a subprocess registers no lines here, because the tracer is
in-process; so does a test whose subject is prose, a schema or a fixture rather
than Python.  Neither is evidence about the test.

    python3 scripts/suite_redundancy.py attribute --start tests --top . \
        --out reports/root.json
    python3 scripts/suite_redundancy.py report --attribution reports
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import glob
import json
import os
import sys
import unittest

MONITOR_IDS = (3, 4)
SCHEMA = "wildcat.suite-attribution.v1"
SELF = os.path.realpath(__file__)


def measured(root, filename, cache):
    """Return one repository-relative source path, or False to ignore it."""
    verdict = cache.get(filename)
    if verdict is None:
        real = os.path.realpath(filename) if filename else ""
        verdict = False
        if real != SELF and real.startswith(root) and real.endswith(".py"):
            relative = real[len(root):]
            parts = relative.split(os.sep)
            verdict = (
                "tests" not in parts
                and not parts[0].startswith(".")
                and not parts[-1].startswith("test_")
            )
            if verdict:
                verdict = relative
        cache[filename] = verdict
    return verdict


class Attributor:
    """Record, per running test, the source lines executed under it."""

    def __init__(self, root):
        self.root = os.path.realpath(root) + os.sep
        self.current = None
        self.monitor = sys.monitoring
        self.cache = {}
        self.tool = None

    def line(self, code, lineno):
        """Record one executed line and disable that location for this test."""
        target = self.current
        if target is not None:
            relative = measured(self.root, code.co_filename, self.cache)
            if relative:
                target.add(f"{relative}:{lineno}")
        return self.monitor.DISABLE

    def start(self):
        """Claim a free monitoring identity so a nested run cannot collide."""
        for candidate in MONITOR_IDS:
            if self.monitor.get_tool(candidate) is None:
                self.tool = candidate
                break
        if self.tool is None:
            raise RuntimeError("no free sys.monitoring tool identity")
        self.monitor.use_tool_id(self.tool, "suite-redundancy")
        self.monitor.register_callback(self.tool, self.monitor.events.LINE, self.line)
        self.monitor.set_events(self.tool, self.monitor.events.LINE)

    def stop(self):
        """Release the tool identity, leaving monitoring as it was found."""
        self.monitor.set_events(self.tool, 0)
        self.monitor.register_callback(self.tool, self.monitor.events.LINE, None)
        self.monitor.free_tool_id(self.tool)
        self.tool = None


class AttributingResult(unittest.TextTestResult):
    """Swap the attribution target at each test boundary."""

    attributor = None
    collected = None
    root = ""

    def owning_file(self, test):
        """Return the repository-relative path of the file declaring one test."""
        module = sys.modules.get(test.__class__.__module__)
        path = getattr(module, "__file__", None)
        if not path:
            return "<unknown>"
        real = os.path.realpath(path)
        prefix = self.root + os.sep
        return real[len(prefix):] if real.startswith(prefix) else real

    def startTest(self, test):
        """Give this test a fresh set and re-enable every disabled location."""
        super().startTest(test)
        self.attributor.current = set()
        self.attributor.monitor.restart_events()

    def stopTest(self, test):
        """Close this test's set and record it against its declaring file."""
        covered = self.attributor.current or set()
        self.attributor.current = None
        self.collected.append((self.owning_file(test), test.id(), covered))
        super().stopTest(test)


def signature(covered):
    """Hash one covered-line set stably, so separate suites can be compared."""
    if not covered:
        return ""
    digest = hashlib.sha256()
    for key in sorted(covered):
        digest.update(key.encode())
        digest.update(b"\n")
    return digest.hexdigest()[:16]


def attribute(start, top, root, methods):
    """Run one suite under the tracer and return its attribution payload."""
    sys.path.insert(0, os.path.realpath(top))
    suite = unittest.defaultTestLoader.discover(start, pattern="test_*.py",
                                                top_level_dir=top)
    attributor = Attributor(root)
    AttributingResult.attributor = attributor
    AttributingResult.collected = []
    AttributingResult.root = os.path.realpath(root)
    with open(os.devnull, "w", encoding="utf-8") as sink:
        runner = unittest.TextTestRunner(verbosity=0, resultclass=AttributingResult,
                                         stream=sink)
        attributor.start()
        try:
            result = runner.run(suite)
        finally:
            attributor.stop()

    payload = {"schema": SCHEMA, "start": start, "tests_run": result.testsRun,
               "failures": len(result.failures) + len(result.errors)}
    if methods:
        seen = {}
        for _, _, covered in AttributingResult.collected:
            for line in covered:
                seen[line] = seen.get(line, 0) + 1
        payload["methods"] = [
            {"file": source, "id": identifier, "covered": len(covered),
             "signature": signature(covered),
             "suite_unique": sorted(line for line in covered if seen[line] == 1)}
            for source, identifier, covered in AttributingResult.collected
        ]
    else:
        files = {}
        counts = {}
        for source, _, covered in AttributingResult.collected:
            files.setdefault(source, set()).update(covered)
            counts[source] = counts.get(source, 0) + 1
        payload["files"] = {
            source: {"tests": counts[source], "lines": sorted(lines)}
            for source, lines in files.items()
        }
    return payload


def load(directory):
    """Merge every attribution payload in one directory."""
    files = {}
    tests = {}
    methods = []
    for path in sorted(glob.glob(os.path.join(directory, "*.json"))):
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
        if payload.get("schema") != SCHEMA:
            continue
        for source, record in payload.get("files", {}).items():
            files.setdefault(source, set()).update(record["lines"])
            tests[source] = tests.get(source, 0) + record["tests"]
        methods.extend(payload.get("methods", []))
    return files, tests, methods


def classify(files, tests):
    """Sort test files into no-measured-source, no-unique and unique coverage."""
    owners = {}
    for source, lines in files.items():
        for line in lines:
            owners.setdefault(line, set()).add(source)

    rows = []
    for source, lines in sorted(files.items()):
        unique = {line for line in lines if owners[line] == {source}}
        if not lines:
            category = "no-measured-source"
        elif not unique:
            category = "no-unique-coverage"
        else:
            category = "unique-coverage"
        overlap = {}
        if category == "no-unique-coverage":
            for line in lines:
                for other in owners[line]:
                    if other != source:
                        overlap[other] = overlap.get(other, 0) + 1
        rows.append({"file": source, "tests": tests.get(source, 0),
                     "covered": len(lines), "unique": len(unique),
                     "category": category,
                     "covered_also_by": sorted(overlap.items(),
                                               key=lambda item: -item[1])[:3]})
    return rows, owners


def method_bodies(path):
    """Hash each function body in one file, ignoring its docstring."""
    shapes = {}
    try:
        with open(path, encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
    except (OSError, SyntaxError, ValueError):
        return shapes
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        statements = list(node.body)
        first = statements[0] if statements else None
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                and isinstance(first.value.value, str):
            statements = statements[1:]
        shape = "".join(ast.dump(statement, include_attributes=False)
                        for statement in statements)
        shapes[node.name] = hashlib.sha256(shape.encode()).hexdigest()[:16]
    return shapes


def duplicates(methods, owners):
    """Group test methods that cover the same lines and share a body shape."""
    shapes = {}
    for record in methods:
        if record["file"] not in shapes:
            shapes[record["file"]] = method_bodies(record["file"])
        record["body"] = shapes[record["file"]].get(record["id"].rsplit(".", 1)[-1], "")
        record["sole_coverage"] = sum(
            1 for line in record["suite_unique"]
            if owners.get(line, set()) == {record["file"]}
        )

    grouped = {}
    for record in methods:
        if record["signature"] and record["body"]:
            grouped.setdefault((record["signature"], record["body"]), []).append(record)
    return [rows for rows in grouped.values() if len(rows) > 1]


def render(rows, methods, groups, stream):
    """Print the report a reader acts on, counts before candidate lists."""
    counts = {}
    for row in rows:
        counts[row["category"]] = counts.get(row["category"], 0) + 1
    print(f"test files          {len(rows)}", file=stream)
    for key in sorted(counts):
        print(f"  {key:20} {counts[key]}", file=stream)
    if methods:
        empty = sum(1 for record in methods if record["covered"] == 0)
        sole = sum(1 for record in methods if record["sole_coverage"] > 0)
        print(f"test methods        {len(methods)}", file=stream)
        print(f"  no measured source   {empty}", file=stream)
        print(f"  sole coverer         {sole}", file=stream)
        print(f"  duplicate groups     {len(groups)}", file=stream)

    print("\nfiles with no unique coverage; review, do not delete on this alone",
          file=stream)
    for row in rows:
        if row["category"] != "no-unique-coverage":
            continue
        also = ", ".join(f"{os.path.basename(name)}({count})"
                         for name, count in row["covered_also_by"])
        print(f"  {row['tests']:4d} tests {row['covered']:6d} lines  {row['file']}",
              file=stream)
        print(f"       also covered by: {also}", file=stream)

    if groups:
        print("\nmethods sharing both a covered-line set and a body shape",
              file=stream)
        for rows_in_group in sorted(groups, key=lambda group: -len(group)):
            print(f"  {len(rows_in_group)}x {rows_in_group[0]['id']}", file=stream)
            for record in rows_in_group[1:]:
                print(f"      == {record['id']}", file=stream)


def parse(argv):
    """Parse one attribute or report invocation."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)

    run = commands.add_parser("attribute", help="trace one suite")
    run.add_argument("--start", required=True, help="discovery start directory")
    run.add_argument("--top", required=True, help="discovery top-level directory")
    run.add_argument("--out", required=True, help="attribution payload to write")
    run.add_argument("--root", default=os.getcwd(), help="repository root")
    run.add_argument("--methods", action="store_true",
                     help="attribute per test method rather than per file")

    read = commands.add_parser("report", help="classify traced attributions")
    read.add_argument("--attribution", required=True,
                      help="directory of attribution payloads")
    read.add_argument("--json", dest="json_out", help="write the rows as JSON")
    return parser.parse_args(argv)


def main(argv=None):
    """Run one subcommand and return its exit status."""
    arguments = parse(sys.argv[1:] if argv is None else argv)

    if arguments.command == "attribute":
        payload = attribute(arguments.start, arguments.top, arguments.root,
                            arguments.methods)
        with open(arguments.out, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)
        print(f"{arguments.start}: {payload['tests_run']} tests, "
              f"{payload['failures']} failed")
        return 1 if payload["failures"] else 0

    files, tests, methods = load(arguments.attribution)
    if not files and not methods:
        print("no attribution payloads found", file=sys.stderr)
        return 2
    rows, owners = classify(files, tests)
    groups = duplicates(methods, owners)
    render(rows, methods, groups, sys.stdout)
    if arguments.json_out:
        with open(arguments.json_out, "w", encoding="utf-8") as handle:
            json.dump({"files": rows, "methods": methods}, handle, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
