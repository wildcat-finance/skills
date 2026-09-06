"""The public front door and the demonstration path, proved as one relation.

Every part of this delivery has its own suite. `tests/test_shoggoth_topology.py`
asks whether the derivation is trustworthy, `tests/test_demonstrations.py`
whether the ledgers and the runner refuse what they say they refuse, and
`tests/test_public_front_door.py` whether each rule fires on its own specimen.
Each of those can be green while the joint is broken, because none of them
crosses from one component into the next.

This module asks the joined questions instead, and each one moves a real thing
in a scratch copy of the delivered tree rather than a fixture.

**Downgrade a record and the claim goes with it.** A card on `README.md` binds
a skill id, a claim id and the digest of the demonstration record it describes.
Changing that record's status from `real-data` to `mixed` must fail the check
on the card that binds it, and restoring the record must make the check pass
again. The status sits inside the fenced object the digest covers, so one edit
moves both, and the case asserts which rules fire rather than only that the
exit was non-zero.

**Land a nineteenth plugin and only the derived numbers move.** The prose
carries no plugin or skill count of its own; it carries markers, and the
numbers behind them come from discovery. A scratch tree with one more plugin
must move exactly the derived quantities, and regenerating only the numerals
those markers bind must return the whole swept surface to clean. Nothing else
in any document may need editing, which is asserted by masking the marked
numerals and requiring the rest of every page to be byte-identical.

**Run the public set and check it against the cards.** The four cards are
claims about what this repository can reproduce offline. The runner is what
reproduces them. This module executes the closed public set and asks whether
each card's bound digest, claim id and displayed result are the ones the run
actually produced.

Three narrower guards sit beside them: the committed Horos boundary against the
delivered tree, one spelling for the public-set selection everywhere a reader
can reach, and no topology literal in any shipped first-party document.

Two boundaries govern how this is done. Every scratch tree is built below a
temporary directory and never inside the repository, and a document in it is
replaced through a fresh file and `os.replace`, never opened for writing, so a
hard link into the repository cannot be written through. And the
`.github/workflows/repo.yml` job checks the tree out and installs nothing, so
the one case that executes demonstrations reuses
`tests.test_demonstrations.absent_dependencies`: the runner still refuses an
unsatisfiable dependency, and only this harness skips, only on a refusal whose
captured error names a module genuinely absent from this interpreter, and with
the module named in the skip.
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))  # noqa: E402  (locates the checker)

from shoggoth_topology import read as discover_topology  # noqa: E402

try:
    import demonstrations  # noqa: E402
except ModuleNotFoundError as error:  # the Elenchus parent has no Step 3 runner
    if error.name != "demonstrations":
        raise
    demonstrations = None

try:
    import check_public_front_door as front_door  # noqa: E402
except ModuleNotFoundError as error:  # the Elenchus parent has no Step 4 checker
    if error.name != "check_public_front_door":
        raise
    front_door = None

JOINED = front_door is not None and demonstrations is not None
RUNNER = demonstrations is not None and hasattr(demonstrations, "run_demonstrations")

# The plugin this module plants. The id is its own, shares nothing with the
# live tree, and is never asserted against a live identity: the point is that
# one more member moves the derived numbers, not which member it is.
PLANTED = "gnomon"

# The record downgraded by the round trip. Any real-data record would do; this
# one is named so the case reports the same card every run.
DOWNGRADED = "plugins/anamnesis/skills/anamnesis"

# The one spelling the runner exposes for the closed public set.
PUBLIC_SET_OPTION = "--public-set"
# A superseded spelling is derived rather than listed. An option whose name
# joins `public`, `registered` or `demo` to anything is the same selection
# under another name, which forbids every such spelling rather than the five
# somebody remembered. The pattern bounds that family and nothing wider, so on
# its own it would pass an alias spelled outside the family. What closes that
# is `test_the_run_subcommand_exposes_a_closed_option_surface`: the `run`
# option set is asserted whole, so a second selection cannot arrive under any
# spelling without a test naming it.
SELECTION_SHAPE_RE = re.compile(r"^--(?:public|registered|demo)(?:-[a-z0-9]+)*$")
OPTION_TOKEN_RE = re.compile(r"--[a-z][a-z0-9-]*")
RUNNER_PATH = "scripts/demonstrations.py"
# The runner invocation as a document writes it, across the backslash
# continuations a fenced command block uses. The interpreter is part of the
# pattern on purpose: `DEMONSTRATIONS.md` names the subcommand inside a code
# span while its prose names both selections in the sentence after it, and
# reading that as a command with no selection reported a document that is
# correct. A command a reader copies always carries the interpreter.
INVOCATION_RE = re.compile(
    r"python3\s+scripts/demonstrations\.py\s+run(?P<rest>(?:[^\n`]|\\\n)*)"
)

# The two committed copies of this delivery's own specification, excluded
# because their subject is this rule: a document that has to quote a forbidden
# spelling in order to forbid it would be reported for carrying it.
#
# The exclusion is defensive and today it excludes nothing. Neither copy names
# a superseded spelling; both name `--public-set` and no other. It is kept so
# that stating the rule in the specification stays possible without the sweep
# turning on the sentence that states it.
SPECIFICATION_COPIES = (
    "docs/shoggoth-public-front-door-runbook.md",
    "docs/shoggoth-public-front-door-study.md",
)

# The shipped first-party prose set, on the scope `tests/test_shipped_prose_lints.py`
# already settled: no historical record, no vendored suite, no generated
# runtime, no frozen eval corpus. The maintained public surface is added to it,
# because half of that surface sits under `docs/` and is current prose rather
# than a record of what was written at the time.
VENDORED = ("x-ray", "solidity-auditor", "fizz", "fizz-convert", "fizz-sync")
PORTABLE_RUNTIME = (".agents", "skills", "promise-machine", "runtime")

GIT_ENVIRONMENT_KEYS = (
    "GIT_DIR", "GIT_INDEX_FILE", "GIT_WORK_TREE", "GIT_OBJECT_DIRECTORY",
    "GIT_ALTERNATE_OBJECT_DIRECTORIES", "GIT_COMMON_DIR", "GIT_NAMESPACE",
    "GIT_PREFIX", "GIT_INTERNAL_SUPER_PREFIX",
)


def git_environment() -> dict[str, str]:
    """An environment no outer Git state can repoint.

    Git exports `GIT_DIR` and `GIT_INDEX_FILE` into anything it spawns, so a
    hook, a `bisect run` or a rebase `exec` line would make the listing below
    describe the outer repository instead of this one.
    """

    environment = dict(os.environ)
    for name in GIT_ENVIRONMENT_KEYS:
        environment.pop(name, None)
    return environment


def delivered_paths() -> list[str]:
    """Every path the delivered tree ships, tracked or newly added.

    `--others --exclude-standard` is what makes this the delivered tree rather
    than the last commit: a file added but not yet committed is part of what a
    reader would get, and a scratch tree built from `HEAD` alone would prove
    the guard against a tree nobody has.
    """

    listed = subprocess.run(  # phylax: allow subprocess: fixed argv git, no shell
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others",
         "--exclude-standard"],
        capture_output=True, check=True, env=git_environment(),
    ).stdout.split(b"\0")
    return [raw.decode("utf-8") for raw in listed if raw]


def shipped_markdown() -> list[str]:
    """Tracked Markdown this repository ships as its own current prose."""

    names = []
    for name in delivered_paths():
        if not name.endswith(".md") or not (ROOT / name).is_file():
            continue
        parts = Path(name).parts
        if parts[: len(PORTABLE_RUNTIME)] == PORTABLE_RUNTIME:
            continue
        if parts[0] in ("audit", "docs"):
            continue
        if "docs" in parts or "evals" in parts:
            continue
        if any(part in VENDORED for part in parts):
            continue
        if Path(name).stem in ("LICENSE", "NOTICE"):
            continue
        names.append(name)
    return names


def swept_documents(topology) -> list[str]:
    """The shipped prose plus the maintained public surface, in one order."""

    maintained = [
        item.relative for item in front_door.maintained_documents(topology)
    ]
    seen = dict.fromkeys(shipped_markdown() + maintained)
    return [name for name in seen if name not in SPECIFICATION_COPIES]


def plant_tree(destination: Path) -> None:
    """Materialise the delivered tree below `destination`.

    Hard links rather than copies: the checker only reads, the tree is 90 MiB,
    and a copy per case would put seconds on the suite for nothing. Every
    mutation below goes through `replace`, which swaps a directory entry and
    never opens an existing file for writing, so no link back into the
    repository is ever written through. A filesystem that will not link across
    the boundary falls back to a copy rather than skipping the file, because a
    scratch tree missing a document is a sweep that reports nothing.
    """

    for name in delivered_paths():
        source = ROOT / name
        if source.is_symlink() or not source.is_file():
            continue
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            os.link(source, target)
        except OSError:
            shutil.copy2(source, target)


def replace(path: Path, text: str) -> None:
    """Write `text` at `path` by swapping the directory entry."""

    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(path.name + ".staged")
    staged.write_text(text, encoding="utf-8")
    os.replace(staged, path)


def marked_number_spans(text: str) -> list[tuple[int, int, str]]:
    """Each numeral a `front-door:count` marker binds, and the key it names.

    Offsets are source offsets: `rendered` blanks a comment to spaces of its
    own length, so a position in the rendered view is the same position in the
    bytes on disk.
    """

    display = front_door.rendered(text)
    spans = []
    for marker in front_door.markers(text):
        if marker.kind != "count":
            continue
        key = marker.attributes.get("key", "")
        claim, offset = front_door.claim_after(display, marker)
        if claim is None or key not in front_door.COUNT_KEYS:
            continue
        spans.append(
            (offset + claim.start("number"), offset + claim.end("number"), key)
        )
    return spans


def masked(text: str) -> str:
    """The document with every marked numeral removed.

    Two pages that mask to the same bytes differ only where a marker binds a
    number to discovery. That is what "no literal needed editing" means, and it
    is checkable in a way that comparing two whole documents is not.
    """

    out = text
    for start, end, _key in sorted(marked_number_spans(text), reverse=True):
        out = out[:start] + "\x00" + out[end:]
    return out


def regenerate_counts(root: Path, counts: dict[str, int]) -> dict[str, str]:
    """Rewrite only the numeral each count marker binds, from discovery.

    This is the whole regeneration. It does not read a document's prose, decide
    what a sentence means, or touch a byte outside a marked numeral: the
    marker says which derived quantity the number is, and discovery says what
    that quantity currently is.
    """

    rewritten: dict[str, str] = {}
    topology = discover_topology(root)
    for item in front_door.maintained_documents(topology):
        path = root / item.relative
        text = path.read_text(encoding="utf-8")
        edits = [
            (start, end, str(counts[front_door.COUNT_KEYS[key]]))
            for start, end, key in marked_number_spans(text)
            if text[start:end] != str(counts[front_door.COUNT_KEYS[key]])
        ]
        if not edits:
            continue
        out = text
        for start, end, want in sorted(edits, reverse=True):
            out = out[:start] + want + out[end:]
        replace(path, out)
        rewritten[item.relative] = out
    return rewritten


class JoinedHarness(unittest.TestCase):
    """A scratch copy of the delivered tree, below a temporary directory."""

    def scratch(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="joined-front-door-")).resolve()
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        plant_tree(root)
        return root

    def codes(self, findings) -> list[str]:
        return sorted(finding.code for finding in findings)


@unittest.skipUnless(JOINED, "the joined path needs both the checker and the ledgers")
class StatusDowngradeRoundTripTests(JoinedHarness):
    """A downgraded record fails the card that binds it, and restoring passes."""

    def test_downgrading_one_record_fails_its_card_and_restoring_passes(self):
        root = self.scratch()
        findings, events = front_door.check(root)
        self.assertEqual(findings, [], "the scratch tree does not hold the contract")
        self.assertEqual(len(events), 4)

        ledger = root / DOWNGRADED / demonstrations.LEDGER_NAME
        original = ledger.read_text(encoding="utf-8")
        self.assertIn('"status": "real-data"', original)

        # `mixed` means a preserved source beside a constructed one, so the
        # downgrade carries the one component that makes the new status
        # admissible. Without it the record checker refuses the record outright
        # and no card rule ever runs, which the next case proves separately.
        component = root / "tmp" / "joined-downgrade" / "constructed-component.json"
        body = b'{"kind": "a constructed component"}\n'
        component.parent.mkdir(parents=True, exist_ok=True)
        component.write_bytes(body)
        relative = component.relative_to(root).as_posix()
        source = json.dumps(
            {
                "id": "constructed-component",
                "class": "fixture",
                "path": relative,
                "sha256": hashlib.sha256(body).hexdigest(),
            },
            indent=2,
        )
        opening = '  "sources": [\n'
        self.assertIn(opening, original)
        downgraded = original.replace('"status": "real-data"', '"status": "mixed"', 1)
        downgraded = downgraded.replace(
            opening,
            opening + "".join(f"    {line}\n" for line in source.splitlines())[:-1]
            + ",\n",
            1,
        )
        replace(ledger, downgraded)

        findings, _events = front_door.check(root)
        # Three rules, and each says a different thing. FD19 is the digest the
        # card bound, which moved because the status sits inside the object the
        # digest covers. FD20 is the card's own real-data claim against the
        # record's new status. FD21 is the set relation: the cards must be
        # exactly the real-data records, and this record is no longer one.
        self.assertEqual(self.codes(findings), ["FD19", "FD20", "FD21"])
        by_code = {finding.code: finding.message for finding in findings}
        self.assertIn(DOWNGRADED, by_code["FD19"])
        self.assertIn("now hashes to", by_code["FD19"])
        self.assertIn("'mixed'", by_code["FD20"])
        self.assertEqual(
            by_code["FD21"],
            f"{DOWNGRADED} carries a card and is not real-data",
        )

        replace(ledger, original)
        component.unlink()
        findings, events = front_door.check(root)
        self.assertEqual(findings, [], "restoring the record did not restore the claim")
        self.assertEqual(len(events), 4)

    def test_a_bare_status_flip_never_reaches_the_card_rules(self):
        """The downgrade is refused earlier still, by the record checker.

        None of the four real-data records names a constructed source, so a
        status flip on its own leaves a record that is not a valid `mixed` one.
        The claim cannot stand by that route either, and this is why the case
        above supplies the component rather than flipping one field.
        """

        root = self.scratch()
        ledger = root / DOWNGRADED / demonstrations.LEDGER_NAME
        original = ledger.read_text(encoding="utf-8")
        replace(ledger, original.replace('"status": "real-data"', '"status": "mixed"', 1))
        with self.assertRaises(demonstrations.DemonstrationError) as caught:
            front_door.check(root)
        self.assertTrue(str(caught.exception).startswith("D018"), caught.exception)


@unittest.skipUnless(JOINED, "the joined path needs both the checker and the ledgers")
class NineteenthPluginTests(JoinedHarness):
    """One more plugin moves the derived numbers and no literal at all."""

    def plant_plugin(self, root: Path) -> None:
        """Add one governed plugin to the scratch tree, everywhere it must appear.

        A plugin is a marketplace entry in both manifests, a landing page, and
        a skill carrying the two ledgers the contracts read. Planting fewer
        than all of those would be refused by the topology reader rather than
        counted, and the case would prove nothing about the counts.
        """

        base = root / "plugins" / PLANTED
        replace(
            base / "README.md",
            "# GNOMON\n\n## WHAT IT IS\n\nA member planted below a temporary "
            "directory so the derived numbers have something to move for.\n",
        )
        skill = base / "skills" / PLANTED
        replace(skill / "SKILL.md", "# Gnomon\n\nA planted skill.\n")
        replace(
            skill / "EVOLUTION.md",
            "# Gnomon evolution ledger\n\n"
            f"- Current version: `{PLANTED}-v0.1.0`\n"
            "- Frontier status: `open`\n",
        )
        revision = "a-first-demonstration"
        current = "Nothing executable exists for this planted member."
        following = "Build one executable demonstration over checkable inputs."
        record = {
            "schema": demonstrations.SCHEMA,
            "skill": PLANTED,
            "plugin": PLANTED,
            "status": "absent",
            "claim_id": f"{PLANTED}-planted-claim",
            "claim": "This planted member ships no executable demonstration.",
            "non_claim": "It establishes nothing about the repository it was planted in.",
            "network": {"policy": "denied"},
            "timeout_seconds": 300,
            "sources": [],
            "commands": [],
            "observations": [],
            "frontier": {
                "version": f"{PLANTED}-demo-v0.1.0",
                "status": "open",
                "revision": revision,
                "sha256": demonstrations.frontier_digest(
                    "open", revision, current, following
                ),
                "current": current,
                "next": following,
            },
        }
        replace(
            skill / demonstrations.LEDGER_NAME,
            "# Gnomon demonstration ledger\n\n"
            f"- Current demonstration version: `{PLANTED}-demo-v0.1.0`\n\n"
            f"{demonstrations.FENCE_OPEN}\n{json.dumps(record, indent=2)}\n"
            f"{demonstrations.FENCE_CLOSE}\n",
        )
        for relative, entry in (
            (".claude-plugin/marketplace.json",
             {"name": PLANTED, "source": f"./plugins/{PLANTED}"}),
            (".agents/plugins/marketplace.json",
             {"name": PLANTED,
              "source": {"source": "local", "path": f"./plugins/{PLANTED}"}}),
        ):
            path = root / relative
            manifest = json.loads(path.read_text(encoding="utf-8"))
            manifest["plugins"] = manifest["plugins"] + [entry]
            replace(path, json.dumps(manifest, indent=2) + "\n")

    def test_a_nineteenth_plugin_moves_only_the_derived_numbers(self):
        root = self.scratch()
        before = discover_topology(root)
        self.assertEqual(front_door.check(root)[0], [])
        self.assertNotIn(PLANTED, before.plugins)
        delivered = {
            item.relative: (root / item.relative).read_text(encoding="utf-8")
            for item in front_door.maintained_documents(before)
        }

        self.plant_plugin(root)
        after = discover_topology(root)

        # What moves. A plugin, its canonical entry skill, and therefore one
        # more governed skill. Named as relations to the tree before it, so a
        # nineteenth plugin landing in the repository for real moves both sides
        # of every comparison here and no literal appears.
        self.assertEqual(after.plugin_count, before.plugin_count + 1)
        self.assertEqual(after.governed_count, before.governed_count + 1)
        self.assertEqual(after.canonical_count, before.canonical_count + 1)
        self.assertEqual(set(after.plugins) - set(before.plugins), {PLANTED})
        self.assertEqual(
            set(after.canonical) - set(before.canonical),
            {f"plugins/{PLANTED}/skills/{PLANTED}"},
        )
        # What does not. The phase skills live under the phase host, so a new
        # plugin cannot add one, and its landing page joins the swept set
        # without any page being named anywhere.
        self.assertEqual(after.phase_count, before.phase_count)
        self.assertEqual(after.phase, before.phase)
        self.assertIn(
            f"plugins/{PLANTED}/README.md",
            [item.relative for item in front_door.maintained_documents(after)],
        )

        stale = front_door.check(root)[0]
        self.assertTrue(stale, "the planted plugin left every published count current")
        self.assertEqual(set(finding.code for finding in stale), {"FD26"})

        rewritten = regenerate_counts(root, after.counts())
        self.assertEqual(
            front_door.check(root)[0],
            [],
            "regenerating the marked numerals did not restore the contract",
        )

        # No literal needed editing. Every document the regeneration touched
        # masks to the bytes it had before, so nothing outside a marked numeral
        # changed; every document it did not touch is byte-identical; and the
        # check above is clean, so no unmarked number anywhere on the swept
        # surface needed to move either.
        for relative, original in delivered.items():
            with self.subTest(document=relative):
                now = (root / relative).read_text(encoding="utf-8")
                if relative in rewritten:
                    self.assertNotEqual(now, original)
                    self.assertEqual(masked(now), masked(original))
                else:
                    self.assertEqual(now, original)
        self.assertTrue(rewritten, "no document carried a marked count at all")


@unittest.skipUnless(RUNNER and front_door is not None, "the joined run needs the runner")
class PublicSetAgainstItsCardsTests(unittest.TestCase):
    """Each card names a record the public set actually reproduces."""

    def test_every_card_binds_a_record_the_public_set_reproduces(self):
        from tests.test_demonstrations import absent_dependencies

        records = demonstrations.load_records(ROOT)
        skills = {
            skill.directory: skill for skill in demonstrations.governed_skills(ROOT)
        }
        selected = demonstrations.select_records(
            records, skills, public_set=True, record_directory=None
        )
        work = Path(tempfile.mkdtemp(prefix="joined-public-set-")).resolve()
        self.addCleanup(shutil.rmtree, work, ignore_errors=True)
        output = io.StringIO()
        with redirect_stdout(output):
            code, payload = demonstrations.run_demonstrations(
                ROOT, selected, report=str(work / "public-set.json"),
                output_root=work, repeat=1,
                ceiling_ms=demonstrations.PUBLIC_SET_CEILING_MS,
                correlation_id="joined0",
                interpreter=demonstrations.require_pinned_interpreter(ROOT),
                mode="public-set",
            )
        if code != 0:
            absent = absent_dependencies(payload)
            if absent:
                self.skipTest(
                    "the public set needs modules this interpreter does not have: "
                    + "; ".join(f"{claim} needs {module}" for claim, module in absent)
                )
        self.assertEqual(code, 0, payload["refusals"])
        self.assertEqual(payload["status"], "verified")
        # A contract limit this run was measured against, not a speed claim.
        self.assertLessEqual(
            payload["aggregate_ms"], demonstrations.PUBLIC_SET_CEILING_MS
        )
        # One correlation id over the whole joined run, so an operator reading
        # the events can tell which run produced which report.
        events = [
            json.loads(line)
            for line in output.getvalue().splitlines()
            if line.startswith("{")
        ]
        self.assertTrue(events)
        self.assertEqual({event["correlation_id"] for event in events}, {"joined0"})

        reproduced = {entry["claim_id"]: entry for entry in payload["demonstrations"]}
        text = (ROOT / front_door.FRONT_DOOR).read_text(encoding="utf-8")
        display = front_door.rendered(text)
        cards = [marker for marker in front_door.markers(text) if marker.kind == "demo"]
        self.assertTrue(cards)
        by_skill = {
            directory.rsplit("/", 1)[-1]: directory
            for directory in discover_topology(ROOT).governed
        }
        for index, card in enumerate(cards):
            claim = card.attributes["claim"]
            with self.subTest(claim=claim):
                self.assertIn(
                    claim, reproduced,
                    "a card claims a demonstration the public set does not run",
                )
                entry = reproduced[claim]
                self.assertEqual(entry["result"], "verified")
                directory = by_skill[card.attributes["skill"]]
                # The digest the card binds is the digest of the record the
                # run reported, so the card, the ledger and the execution are
                # one relation rather than three that happen to agree.
                self.assertEqual(card.attributes["digest"], entry["record_sha256"])
                self.assertEqual(
                    card.attributes["digest"],
                    demonstrations.record_digest(records[directory]),
                )
                body = front_door.flat(
                    display[
                        card.end:
                        cards[index + 1].start if index + 1 < len(cards) else len(display)
                    ]
                )
                held = {
                    observed
                    for command in entry["repetitions"][0]["commands"]
                    for observed in command["observations"]
                }
                shown = [
                    observation
                    for observation in held
                    if front_door.flat(
                        front_door.observation_display(
                            demonstrations.parse_observation(
                                observation, where=directory
                            )
                        )
                    ) in body
                ]
                self.assertTrue(
                    shown,
                    f"the card displays none of the results {sorted(held)} the run held",
                )
                self.assertIn(front_door.flat(entry["non_claim"]), body)


class HorosBoundaryTests(unittest.TestCase):
    """The committed reading boundary describes the tree this step delivers."""

    def horos(self):
        sys.path.insert(
            0, str(ROOT / "plugins" / "horos" / "skills" / "horos" / "scripts")
        )
        import horos  # noqa: E402  (locates horos.py)

        return horos

    def scan(self, horos, root: Path):
        """The fresh scan's own output, read rather than discarded."""

        committed = horos.load_boundary(str(root))
        fresh = horos.boundary_document(
            horos.scan_tree(
                str(root),
                include_untracked=committed.get("universe") == "tracked+untracked",
            )
        )
        return committed, fresh

    def test_the_committed_boundary_matches_the_delivered_tree(self):
        horos = self.horos()
        committed, fresh = self.scan(horos, ROOT)
        drifted = [path for path, _ in horos.diff_boundary_documents(committed, fresh)]
        self.assertEqual(
            drifted, [],
            "regenerate with: python3 "
            "plugins/horos/skills/horos/scripts/horos.py scan . --write "
            "and again with --census",
        )

    def test_the_comparison_names_a_file_the_boundary_does_not_hold(self):
        """A guard that cannot fail is worth nothing.

        The case above is a comparison against a tree that agrees with the
        committed boundary, so nothing about it distinguishes a sound reading
        from one that discarded the scan and asserted an empty list.
        """

        horos = self.horos()
        committed, fresh = self.scan(horos, ROOT)
        invented = dict(fresh)
        entries = invented.get("entries")
        if not isinstance(entries, list) or not entries:
            self.skipTest("the boundary document holds no entry list to perturb")
        invented["entries"] = entries[:-1]
        drifted = [
            path for path, _ in horos.diff_boundary_documents(committed, invented)
        ]
        self.assertTrue(drifted, "the comparison reports nothing when an entry is gone")


@unittest.skipUnless(RUNNER, "the option surface needs the Step 3 runner")
class PublicSetOptionSpellingTests(unittest.TestCase):
    """One spelling for the public-set selection, everywhere a reader can reach."""

    def selection_options(self) -> list[str]:
        """Every option string the `run` subcommand exposes for the selection."""

        parser = demonstrations.build_parser()
        found = []
        for action in parser._subparsers._group_actions:  # the sub-command map
            runner = action.choices.get("run")
            if runner is None:
                continue
            for item in runner._actions:
                found.extend(
                    option for option in item.option_strings
                    if SELECTION_SHAPE_RE.match(option)
                )
        return sorted(found)

    def test_the_runner_exposes_exactly_one_public_set_spelling(self):
        self.assertEqual(self.selection_options(), [PUBLIC_SET_OPTION])

    def test_the_run_subcommand_exposes_a_closed_option_surface(self):
        """The rule above reads a family of names; this one reads all of them.

        `SELECTION_SHAPE_RE` recognises a second selection spelled `--public`,
        `--registered` or `--demo` anything. An alias spelled outside that
        family -- `--all-demos`, say -- is the same selection under a name the
        pattern cannot see, and both spelling cases would stay green. Asserting
        the whole option set closes that: a new option on `run` fails here
        whatever it is called, and whoever adds one has to say which of the two
        it is.
        """

        parser = demonstrations.build_parser()
        run = None
        for action in parser._subparsers._group_actions:  # the sub-command map
            run = run or action.choices.get("run")
        self.assertIsNotNone(run, "the runner exposes no `run` sub-command")
        self.assertEqual(
            sorted({option for item in run._actions for option in item.option_strings}),
            ["--help", "--output-root", "--public-set", "--record", "--repeat",
             "--report", "--root", "-h"],
        )

    def test_the_module_carries_no_second_spelling(self):
        source = (ROOT / RUNNER_PATH).read_text(encoding="utf-8")
        superseded = sorted(
            {
                token for token in OPTION_TOKEN_RE.findall(source)
                if SELECTION_SHAPE_RE.match(token) and token != PUBLIC_SET_OPTION
            }
        )
        self.assertEqual(superseded, [], f"{RUNNER_PATH} exposes {superseded}")

    def test_no_shipped_document_names_a_superseded_spelling(self):
        offences = []
        for relative in swept_documents(discover_topology(ROOT)):
            text = (ROOT / relative).read_text(encoding="utf-8")
            if RUNNER_PATH not in text:
                continue
            for token in OPTION_TOKEN_RE.findall(text):
                if SELECTION_SHAPE_RE.match(token) and token != PUBLIC_SET_OPTION:
                    offences.append(f"{relative}: {token}")
            for match in INVOCATION_RE.finditer(text):
                rest = match.group("rest")
                chosen = [
                    token for token in OPTION_TOKEN_RE.findall(rest)
                    if token in (PUBLIC_SET_OPTION, "--record")
                ]
                if not chosen:
                    offences.append(f"{relative}: a run naming no selection")
        self.assertEqual(sorted(set(offences)), [])

    def test_the_sweep_reports_a_reintroduced_spelling(self):
        """The sweep above is clean, so prove it is not clean by construction."""

        planted = "python3 scripts/demonstrations.py run --public-demo-set \\\n  --report tmp/x.json\n"
        tokens = [
            token for token in OPTION_TOKEN_RE.findall(planted)
            if SELECTION_SHAPE_RE.match(token) and token != PUBLIC_SET_OPTION
        ]
        self.assertEqual(tokens, ["--public-demo-set"])
        self.assertEqual(
            [
                token for token in OPTION_TOKEN_RE.findall(
                    INVOCATION_RE.search(planted).group("rest")
                )
                if token in (PUBLIC_SET_OPTION, "--record")
            ],
            [],
        )


@unittest.skipUnless(JOINED, "the literal sweep needs the derived counts")
class TopologyLiteralTests(unittest.TestCase):
    """No shipped first-party document carries a count the tree derives."""

    def literals(self, counts: dict[str, int], documents) -> list[str]:
        """Every unmarked count claim whose number is a derived quantity today.

        A number is a literal exactly when it is right only because the tree
        currently holds that value. Comparing against the live derivation is
        what makes that decidable: a marked claim is checked every run, and an
        unmarked one that happens to equal a derived count is the failure this
        whole delivery exists to remove.
        """

        found = []
        for relative, text in documents:
            display = front_door.rendered(text)
            exempt = set()
            for marker in front_door.markers(text):
                if marker.kind not in ("count", "historical"):
                    continue
                claim, offset = front_door.claim_after(display, marker)
                if claim is not None:
                    exempt.add(offset)
            for claim in front_door.COUNT_CLAIM_RE.finditer(display):
                if claim.start() in exempt:
                    continue
                number = front_door.claim_number(claim.group("number"))
                for key, quantity in front_door.COUNT_KEYS.items():
                    if counts[quantity] != number:
                        continue
                    if front_door.COUNT_NOUNS[key] in claim.group(0).lower():
                        found.append(
                            f"{relative}: {claim.group(0).strip()!r} restates the "
                            f"derived {key} count"
                        )
        return sorted(set(found))

    def documents(self):
        topology = discover_topology(ROOT)
        return topology, [
            (relative, (ROOT / relative).read_text(encoding="utf-8"))
            for relative in swept_documents(topology)
        ]

    def test_no_shipped_document_restates_a_derived_count(self):
        topology, documents = self.documents()
        self.assertEqual(self.literals(topology.counts(), documents), [])

    def test_the_sweep_names_the_literal_that_survived_a_landing_plugin(self):
        """Commit `67a01a6c` is the worked example, replayed as a specimen.

        That commit landed the eighteenth plugin, moved `README.md` and the
        portable contract from twenty-five members to twenty-six, and left
        `SHOGGOTH.md` saying twenty-five. The sentence is planted here at
        today's derived numbers, because a literal is only ever detectable
        against the tree that makes it wrong tomorrow.
        """

        topology, _documents = self.documents()
        counts = topology.counts()
        planted = (
            "The current roster has "
            f"{counts['governed']} members: {counts['canonical']} domain agents "
            f"and {counts['phase']} phase agents.\n"
        )
        found = self.literals(counts, [("SPECIMEN.md", planted)])
        self.assertEqual(len(found), 3, found)
        self.assertTrue(any("members" in item for item in found))
        self.assertTrue(any("domain" in item for item in found))
        self.assertTrue(any("phase" in item for item in found))


if __name__ == "__main__":
    unittest.main()
