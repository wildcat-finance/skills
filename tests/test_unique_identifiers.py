"""Guard the values this repository treats as unique, each within its own scope.

Two concurrent runs that each need the next value of a shared counter both read
the current highest, both pick the same next one, and both land. Git raises no
conflict when the files they write have different names, because it compares
paths rather than the values inside them. ADR-012 reached the default branch that
way and stayed there for two days.

`tests/test_decision_records.py` closed that for decision records. This closes it
for the rest, and deliberately names the scope each value is unique within rather
than assuming that scope is the repository: plugin versions are unique per plugin
and six of them legitimately share `0.1.1`, so a repository-wide check there would
be wrong rather than strict.

There is no exception list anywhere in this module. One would grow every time
somebody found a check inconvenient.
"""

from __future__ import annotations

import collections
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unittest

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
COVERAGE = REPOSITORY_ROOT / "tests/promise_machine_coverage.json"
ROOT_CONTRACT = REPOSITORY_ROOT / "PROMISE_MACHINE.md"
PROMISE_HEADING_RE = re.compile(r"^###\s+(promise-[a-z0-9-]+)\s*$", re.M)
LEDGER_VERSION_RE = re.compile(r"\A`([a-z0-9-]+)-v(\d+\.\d+\.\d+)`\Z")


def git_env():
    """Git's own variables removed, so a call cannot reach another repository."""
    env = dict(os.environ)
    for name in ("GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY",
                 "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE",
                 "GIT_PREFIX", "GIT_INTERNAL_SUPER_PREFIX"):
        env.pop(name, None)
    return env


def file_on_ref(ref, relpath):
    """One file's text on a git ref, or None when the ref is unavailable.

    None means the comparison could not run. Callers report that rather than
    treating it as a pass, because a check that skips silently is worse than no
    check: it reads as evidence.
    """
    result = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
        ["git", "-C", str(REPOSITORY_ROOT), "show", f"{ref}:{relpath}"],
        capture_output=True, text=True, env=git_env(),
    )
    return result.stdout if result.returncode == 0 else None


def default_branch_ref():
    for ref in ("origin/main", "refs/remotes/origin/main", "main"):
        probe = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
            ["git", "-C", str(REPOSITORY_ROOT), "rev-parse", "--verify", "--quiet", ref],
            capture_output=True, text=True, env=git_env(),
        )
        if probe.returncode == 0:
            return ref
    return None


def declared_promises(text):
    return PROMISE_HEADING_RE.findall(text)


def coverage_document():
    return json.loads(COVERAGE.read_text(encoding="utf-8"))


def records_with(document, field):
    """Every object anywhere in the coverage file carrying `field`, with its location.

    The walk is recursive and blind to the shape of what holds a record, on
    purpose. Its predecessors read one level of named fields off each capability
    entry and skipped anything a list held, so `run_observation_capture.tests` --
    a list where the other capabilities use an object -- recorded a digest that
    no check recomputed. `tests/test_run_observation_capture.py` then drifted
    from its recorded bytes in 62a0cb87, which rebound nothing, and every check
    went on reporting clean until an unrelated re-pin sweep read the file.

    Reaching a record was conditional on two things beyond the record itself:
    the entry above it carrying a `promise_id`, which `run_observation_binding`
    does not, and the field holding it being an object rather than a list. A
    walker that has to be taught each new container is the honour system with
    extra steps, which is the failure the digest check below already names for
    hand-rolled per-capability tests.

    The location is returned as a dotted trail so a failure names the record
    rather than only the file, because two entries can bind one path.
    """
    found = []

    def walk(node, trail):
        if isinstance(node, dict):
            if field in node:
                found.append((".".join(trail) or "<root>", node))
            for name in sorted(node):
                walk(node[name], trail + [name])
        elif isinstance(node, list):
            for index, item in enumerate(node):
                walk(item, trail + [f"[{index}]"])

    walk(document, [])
    return found


def bound_promise_ids(document):
    """Every promise id the coverage file binds, from rows and capability keys."""
    bound = {row["promise_id"] for row in document.get("rows", [])}
    for _key, value in document.items():
        if isinstance(value, dict) and "promise_id" in value:
            bound.add(value["promise_id"])
    return bound


def ledgers():
    return sorted(REPOSITORY_ROOT.glob("plugins/**/EVOLUTION.md"))


def ledger_versions(text):
    """The version of every ledger row, in order, in either accepted form.

    Two row forms are in use. Most ledgers use a Markdown pipe table. Brevitas
    and Ephoros use the compact list form, `- \u0060name-vX.Y.Z\u0060 | axis | ...`,
    which the compact-history change introduced. A parser that read only tables
    would report those two ledgers as empty and every check over them would pass
    on nothing.
    """
    found = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("| "):
            body = stripped.strip("|")
        elif stripped.startswith("- `") and "|" in stripped:
            body = stripped[2:]
        else:
            continue
        cells = [c.strip() for c in body.split("|")]
        if cells:
            match = LEDGER_VERSION_RE.match(cells[0])
            if match:
                found.append(f"{match.group(1)}-v{match.group(2)}")
    return found


class PromiseIdentifiers(unittest.TestCase):
    """A promise id names one promise, and every promise is bound to evidence."""

    def test_no_two_coverage_entries_share_an_id(self):
        document = coverage_document()
        ids = [row["promise_id"] for row in document["rows"]]
        for _key, value in document.items():
            if isinstance(value, dict) and "promise_id" in value:
                ids.append(value["promise_id"])
        duplicates = sorted(k for k, n in collections.Counter(ids).items() if n > 1)
        self.assertEqual(
            duplicates, [],
            "two coverage entries claim one promise id, so one promise's evidence "
            f"silently stands in for another's: {duplicates}",
        )

    def test_every_contract_document_is_bound_to_evidence(self):
        """A shipped contract document with no coverage entry is unenforced.

        Not every declared promise needs a coverage entry: the first-party
        licence promise is enforced by `check --only licences` instead, and an
        earlier version of this test wrongly flagged it. What does need one is a
        capability that ships a versioned contract document under
        `docs/promise-machine/`, because that is the run-observation shape and
        the entry is what binds the runtime digest, the test selectors and the
        document digest. Without it the implementation can drift away from the
        document and nothing notices.
        """
        documents = sorted(
            path.relative_to(REPOSITORY_ROOT).as_posix()
            for path in (REPOSITORY_ROOT / "docs/promise-machine").glob("*-v[0-9]*.md")
        )
        self.assertTrue(documents, "no versioned contract documents found")
        bound = set()
        for value in coverage_document().values():
            if isinstance(value, dict):
                entry = value.get("documentation")
                if isinstance(entry, dict) and entry.get("path"):
                    bound.add(entry["path"])
        unbound = [doc for doc in documents if doc not in bound]
        self.assertEqual(
            unbound, [],
            "these contract documents are shipped and bound to no coverage entry, "
            "so nothing ties the implementation to the promise they state: "
            f"{unbound}",
        )

    def test_every_bound_capability_digest_matches_the_file_it_names(self):
        """Recompute every digest the register records, wherever it sits.

        The digests in a capability entry were once checked by a test written for
        that one capability: `test_run_observation_coverage_binds_the_exact_release_surface`
        covers run-observation and nothing covered contributor-ranking, so its
        entry could name any digest at all and every check still reported clean.
        Enforcement that depends on somebody remembering to write the next
        hand-rolled test is the honour system with extra steps.

        Replacing that with a walk over named object fields under a `promise_id`
        moved the same failure one level up rather than removing it. Nineteen of
        the register's 126 digests fell outside those two conditions, and
        seventeen were caught only because somebody had written the capability's
        own test after all: nine by `assert_bound_paths` in
        `tests/test_agent_instruction.py`, eight by
        `test_run_observation_binding_coverage_binds_the_exact_release_surface`
        in `tests/test_promise_machine_contract.py`.

        The remaining two were `run_observation_capture.tests`, whose capability
        test binds only its `reporter`. Zeroing both digests left the root suite
        green at 166d3e21, and one of them was already stale. skills#1205.

        `records_with` reaches a record by its own contents instead, so nothing
        in this file records a digest that goes unchecked, and
        `test_the_digest_walk_reaches_every_digest_the_register_records` is what
        holds that true.
        """
        checked, wrong = 0, []
        for trail, record in records_with(coverage_document(), "sha256"):
            # Capability entries name their file `path` and the runtime bindings
            # name it `source`. Both record a digest over whole file bytes, so
            # both are recomputed the same way.
            named, recorded = record.get("path") or record.get("source"), record["sha256"]
            if not isinstance(named, str) or not isinstance(recorded, str):
                wrong.append(f"{trail}: records a digest and names no file")
                continue
            target = REPOSITORY_ROOT / named
            if not target.is_file():
                wrong.append(f"{trail}: {named} is absent")
                continue
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
            checked += 1
            if actual != recorded:
                wrong.append(
                    f"{trail}: {named} is {actual[:12]} and the entry "
                    f"records {recorded[:12]}"
                )
        self.assertTrue(checked, "no digests were checked, so this proves nothing")
        self.assertEqual(
            wrong, [],
            "an entry records a digest that does not match the file it names, so "
            "the promise is bound to bytes that have changed. Nothing regenerates "
            "tests/promise_machine_coverage.json: recompute with `shasum -a 256 "
            "<path>` and write the value into the matching sha256, as the last "
            f"edit before you commit rather than the first: {wrong}",
        )

    def test_the_digest_walk_reaches_every_digest_the_register_records(self):
        """The check above proves nothing about a record it does not reach.

        That is not a hypothetical: reaching a record used to depend on the shape
        of the field holding it, and the digest that went stale was one the walk
        never visited, so its own count told it nothing was wrong.

        The count here is lexical rather than structural, so it does not share a
        traversal with the thing it is checking. A filter reinstated inside
        `records_with` narrows that walk and fails here, instead of quietly
        narrowing what the digest check covers.
        """
        recorded = COVERAGE.read_text(encoding="utf-8").count('"sha256"')
        reached = len(records_with(coverage_document(), "sha256"))
        self.assertEqual(
            reached, recorded,
            f"the digest walk reaches {reached} of the {recorded} digests "
            "tests/promise_machine_coverage.json records, so the difference is "
            "bound to bytes nothing recomputes",
        )

    def test_every_bound_capability_names_its_fixtures(self):
        missing = []
        for key, value in sorted(coverage_document().items()):
            if not isinstance(value, dict) or "promise_id" not in value:
                continue
            for fixture in value.get("fixtures", []) or []:
                # run_observation records fixtures as {path, sha256}; a bare
                # string would bind no digest, so both shapes are read and the
                # digest is checked wherever one is recorded.
                path = fixture.get("path") if isinstance(fixture, dict) else fixture
                if not path:
                    missing.append(f"{key}: a fixture entry names no path")
                    continue
                target = REPOSITORY_ROOT / path
                if not target.is_file():
                    missing.append(f"{key}: {path} is absent")
                    continue
                if isinstance(fixture, dict) and fixture.get("sha256"):
                    actual = hashlib.sha256(target.read_bytes()).hexdigest()
                    if actual != fixture["sha256"]:
                        missing.append(
                            f"{key}: {path} is {actual[:12]} and the entry records "
                            f"{fixture['sha256'][:12]}"
                        )
        self.assertEqual(missing, [], f"fixtures named but absent: {missing}")

    def test_every_bound_capability_selector_exists_in_its_test_file(self):
        """A selector naming no test binds the promise to nothing.

        Read through the same walk as the digests, and for the same reason: this
        read `value["tests"]` as an object under a `promise_id`, so two of the
        register's nine selector lists were never opened. A bogus selector
        planted in `run_observation_capture.tests[1]` left the root suite green
        at 166d3e21. The eleven selectors those two lists name all resolve, but
        nothing was checking that they did.

        An absent file is a failure here rather than a skip. It was a `continue`
        before, which reported a missing test file as a clean selector list.
        """
        stray = []
        for trail, record in records_with(coverage_document(), "selectors"):
            named = record.get("path")
            if not isinstance(named, str):
                stray.append(f"{trail}: records selectors and names no test file")
                continue
            target = REPOSITORY_ROOT / named
            if not target.is_file():
                stray.append(f"{trail}: {named} is absent")
                continue
            source = target.read_text(encoding="utf-8")
            for selector in record["selectors"] or []:
                if f"def {selector}(" not in source:
                    stray.append(f"{trail}: {selector} is not defined in {named}")
        self.assertEqual(stray, [], f"selectors naming no test: {stray}")

    def test_every_bound_capability_names_a_document_that_exists(self):
        missing = []
        for key, value in coverage_document().items():
            if not isinstance(value, dict) or "promise_id" not in value:
                continue
            for field in ("runtime", "documentation", "tests"):
                entry = value.get(field)
                if isinstance(entry, dict) and entry.get("path"):
                    if not (REPOSITORY_ROOT / entry["path"]).is_file():
                        missing.append(f"{key}.{field}: {entry['path']}")
        self.assertEqual(missing, [], f"bound paths that do not exist: {missing}")


class LedgerVersions(unittest.TestCase):
    """A version names one row of one skill's ledger.

    Scope matters here. Versions carry the skill's name, as `imprimatur-v1.1.0`,
    so two skills cannot collide. The collision is two runs advancing the same
    skill to the same version, which lands as two rows claiming one version.
    """

    def test_no_ledger_claims_a_version_twice(self):
        offenders = []
        for ledger in ledgers():
            versions = ledger_versions(ledger.read_text(encoding="utf-8"))
            for version, count in sorted(collections.Counter(versions).items()):
                if count > 1:
                    rel = ledger.relative_to(REPOSITORY_ROOT)
                    offenders.append(f"{rel}: {version} claimed {count} times")
        self.assertEqual(
            offenders, [],
            "a ledger claims one version on more than one row, which is what two "
            f"runs advancing the same skill produces: {offenders}",
        )

    def test_every_ledger_yields_at_least_one_version(self):
        """A parser that reads nothing would pass every check above it."""
        empty = [
            str(led.relative_to(REPOSITORY_ROOT))
            for led in ledgers()
            if not ledger_versions(led.read_text(encoding="utf-8"))
        ]
        self.assertEqual(empty, [], f"ledgers this parser could not read: {empty}")

    def test_no_ledger_row_reuses_a_version_already_on_the_default_branch(self):
        """The case a single-tree check cannot see.

        Two branches each add a row and each pick the same next version. Both
        merge, because the ledgers are the same file only if the skill is the
        same, and even then the rows differ textually.
        """
        ref = default_branch_ref()
        if ref is None:
            self.skipTest(
                "no local ref for the default branch, so this comparison could not "
                "run; fetch origin/main in CI to make this check effective"
            )
        offenders = []
        for ledger in ledgers():
            relative = ledger.relative_to(REPOSITORY_ROOT).as_posix()
            theirs = file_on_ref(ref, relative)
            if theirs is None:
                continue  # new ledger on this branch; nothing to collide with
            ours = ledger_versions(ledger.read_text(encoding="utf-8"))
            base = ledger_versions(theirs)
            added = [v for v in ours if v not in base]
            for version in added:
                if version in base:
                    offenders.append(f"{relative}: {version}")
        self.assertEqual(
            offenders, [],
            f"a ledger row reuses a version the default branch already has: {offenders}",
        )


if __name__ == "__main__":
    unittest.main()
