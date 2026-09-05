"""The front-door contract, and one specimen per refusal it makes.

Two rules govern everything below.

**Against the live tree, assert agreement and never a literal.** The live cases
ask whether `README.md` still satisfies the contract and whether the cards
still bind the records the tree actually holds. None of them names a count, a
digest or a claim id, because a plugin landing tomorrow moves all of those
together and no case here should notice.

**Against a specimen, assert exactly one deliberate break.** Every specimen
plants its own three-plugin tree with arbitrary ids that share nothing with
this repository, and differs from `clean.md` in one place. The placeholders in
a specimen are substituted from that planted tree, so a specimen carries the
shape of a front door rather than a frozen copy of one skill's evidence.

Nothing here executes a demonstration. The invariant CI job checks this
repository out and installs nothing, so a case that ran a demonstration whose
program imports a third-party package would pass on a developer's machine and
redden the branch. The checker reads files and computes; so does this suite,
and both stay inside the standard library.
"""

from __future__ import annotations

import ast
import hashlib
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))  # noqa: E402  (locates the checker)

import demonstrations  # noqa: E402
from shoggoth_topology import read as discover_topology  # noqa: E402

try:
    import check_public_front_door as front_door  # noqa: E402
except ModuleNotFoundError as error:  # the Elenchus parent has no Step 4 checker
    if error.name != "check_public_front_door":
        raise
    front_door = None


SPECIMENS = ROOT / "tests" / "fixtures" / "public-front-door"
HEADER_RE = re.compile(
    r'<!--\s*front-door-specimen:\s*expect="(?P<expect>[A-Za-z0-9]+)"'
    r'\s+reason="(?P<reason>[^"]+)"\s*-->'
)
PLACEHOLDER_RE = re.compile(r"\{\{(?P<kind>[a-z]+):(?P<name>[a-z-]+)\}\}")

# The specimen tree. Its ids are arbitrary; the phase host is deliberately
# absent so every plugin carries exactly one canonical skill and the topology
# reader's own defaults derive the tree without being told anything about it.
MEMBERS = (
    {"id": "lantern", "status": "real-data"},
    {"id": "thicket", "status": "real-data"},
    {"id": "quarry", "status": "mixed"},
)


def write(path: Path, body: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def record_for(root: Path, member: dict) -> dict:
    """Plant one governed skill and return the record its ledger carries."""

    plugin = member["id"]
    status = member["status"]
    directory = f"plugins/{plugin}/skills/{plugin}"
    write(root / directory / "EVOLUTION.md", "# ledger\n")
    write(root / directory / "SKILL.md", "# skill\n")

    line = f"{plugin}: the held specimen rebuilds"
    program = f"plugins/{plugin}/demo.py"
    program_digest = write(root / program, f'print("{line}")\n')
    held = f"plugins/{plugin}/specimens/held.json"
    held_digest = write(root / held, json.dumps({"held": plugin}) + "\n")

    sources = [
        {"id": "held", "class": "audit", "path": held, "sha256": held_digest},
        {
            "id": "program",
            "class": "repository",
            "path": program,
            "sha256": program_digest,
        },
    ]
    if status == "mixed":
        invented = f"plugins/{plugin}/specimens/invented.json"
        sources.append(
            {
                "id": "invented",
                "class": "fixture",
                "path": invented,
                "sha256": write(root / invented, json.dumps({"made": plugin}) + "\n"),
            }
        )

    current = "The held specimen rebuilds offline from preserved bytes."
    following = "Preserve a second specimen so the path is shown over two."
    record = {
        "schema": demonstrations.SCHEMA,
        "skill": plugin,
        "plugin": plugin,
        "status": status,
        "claim_id": f"{plugin}-held-specimen",
        "claim": f"The {plugin} specimen rebuilds offline from the preserved bytes.",
        "non_claim": (
            f"It does not establish that the {plugin} corpus is complete or that "
            "any recorded judgement is correct."
        ),
        "network": {"policy": "denied"},
        "timeout_seconds": 300,
        "sources": sources,
        "commands": [
            {"id": "run", "argv": ["python3", program], "expect_exit": 0}
        ],
        "observations": [f'run: line "{line}"'],
        "frontier": {
            "version": f"{plugin}-demo-v0.1.0",
            "status": "open",
            "revision": "second-preserved-specimen",
            "sha256": demonstrations.frontier_digest(
                "open", "second-preserved-specimen", current, following
            ),
            "current": current,
            "next": following,
        },
    }
    write(
        root / directory / demonstrations.LEDGER_NAME,
        "# Specimen demonstration ledger\n\n"
        f"{demonstrations.FENCE_OPEN}\n"
        f"{json.dumps(record, indent=2)}\n"
        f"{demonstrations.FENCE_CLOSE}\n",
    )
    return record


def plant(root: Path) -> dict[str, dict]:
    """Materialise the whole specimen repository and return its records."""

    records = {member["id"]: record_for(root, member) for member in MEMBERS}
    entries = [{"name": member["id"]} for member in MEMBERS]
    write(
        root / ".claude-plugin" / "marketplace.json",
        json.dumps(
            {
                "name": "specimen",
                "owner": "specimen",
                "plugins": [
                    {"name": entry["name"], "source": f"./plugins/{entry['name']}"}
                    for entry in entries
                ],
            },
            indent=2,
        )
        + "\n",
    )
    write(
        root / ".agents" / "plugins" / "marketplace.json",
        json.dumps(
            {
                "name": "specimen",
                "interface": "specimen",
                "plugins": [
                    {
                        "name": entry["name"],
                        "source": {
                            "source": "local",
                            "path": f"./plugins/{entry['name']}",
                        },
                    }
                    for entry in entries
                ],
            },
            indent=2,
        )
        + "\n",
    )
    # The committed schema, not a copy of it: a second schema in the fixture
    # tree would drift away from the one the checker enforces.
    write(
        root / demonstrations.SCHEMA_PATH,
        (ROOT / demonstrations.SCHEMA_PATH).read_text(encoding="utf-8"),
    )
    return records


def substitute(body: str, root: Path, records: dict[str, dict]) -> str:
    """Fill a specimen's placeholders from the tree that was actually planted."""

    counts = discover_topology(root).counts()

    def value(match: re.Match) -> str:
        kind, name = match.group("kind"), match.group("name")
        if kind == "count":
            return str(counts[front_door.COUNT_KEYS[name]])
        record = records[name]
        if kind == "digest":
            return demonstrations.record_digest(record)
        if kind == "claim":
            return record["claim_id"]
        if kind == "nonclaim":
            return record["non_claim"]
        if kind == "directory":
            return f"plugins/{name}/skills/{name}"
        if kind == "source":
            return front_door.preserved_sources(record)[0]
        if kind == "observed":
            return front_door.observation_display(
                demonstrations.parse_observation(
                    record["observations"][0], where=name
                )
            )
        raise AssertionError(f"unknown placeholder kind {kind!r}")

    return PLACEHOLDER_RE.sub(value, body)


def specimen_codes(name: str) -> list[str]:
    """Plant the specimen tree, install one specimen README, and check it."""

    body = (SPECIMENS / f"{name}.md").read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        records = plant(root)
        write(root / front_door.FRONT_DOOR, substitute(body, root, records))
        findings, _ = front_door.check(root)
    return [finding.code for finding in findings]


class EntryParentGuardTests(unittest.TestCase):
    """Each specimen is red before the checker it guards exists."""

    def test_every_specimen_declares_what_it_breaks(self):
        found = sorted(path.name for path in SPECIMENS.glob("*.md"))
        self.assertTrue(found, SPECIMENS)
        for name in found:
            header = HEADER_RE.search(
                (SPECIMENS / name).read_text(encoding="utf-8")
            )
            with self.subTest(specimen=name):
                self.assertIsNotNone(header, "specimen declares no expectation")
                self.assertIsNotNone(
                    front_door, f"{name} has no checker on the entry parent"
                )
                expect = header.group("expect")
                if expect != "clean":
                    self.assertIn(expect, front_door.REFUSALS)


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class SpecimenTests(unittest.TestCase):
    """One deliberate break each, against a tree that shares no id with this one."""

    def specimens(self):
        for path in sorted(SPECIMENS.glob("*.md")):
            header = HEADER_RE.search(path.read_text(encoding="utf-8"))
            yield path.stem, header.group("expect")

    def test_the_clean_specimen_holds_the_whole_contract(self):
        self.assertEqual(specimen_codes("clean"), [])

    def test_each_specimen_reports_the_refusal_it_names(self):
        for name, expect in self.specimens():
            if expect == "clean":
                continue
            with self.subTest(specimen=name):
                self.assertIn(expect, specimen_codes(name))

    def test_a_named_maintained_document_that_is_absent_fails_the_sweep(self):
        """Absence is a refusal, never a quiet skip.

        A sweep that reads whatever it finds reports nothing when the document
        it was meant to read is gone, and a reader cannot tell that from a
        clean result.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            plant(root)
            findings, events = front_door.check(root)
        self.assertEqual([finding.code for finding in findings], ["FD01"])
        self.assertEqual(events, [])

    def test_the_maintained_set_is_not_empty(self):
        """A sweep over an empty set passes while checking nothing."""
        self.assertTrue(front_door.MAINTAINED_DOCUMENTS)
        self.assertIn(front_door.FRONT_DOOR, front_door.MAINTAINED_DOCUMENTS)


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class LiveFrontDoorTests(unittest.TestCase):
    """Agreement against the delivered tree, with no literal in sight."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.findings, cls.events = front_door.check(ROOT)
        cls.records = demonstrations.load_records(ROOT)

    def test_the_front_door_holds_its_contract(self):
        self.assertEqual([str(finding) for finding in self.findings], [])

    def test_every_real_data_record_has_exactly_one_card(self):
        carded = [event["directory"] for event in self.events]
        expected = sorted(
            directory
            for directory, record in self.records.items()
            if record["status"] == "real-data"
        )
        self.assertEqual(sorted(carded), expected)
        self.assertEqual(len(carded), len(set(carded)))

    def test_every_card_binds_the_digest_the_ledger_now_hashes_to(self):
        for event in self.events:
            record = self.records[event["directory"]]
            with self.subTest(skill=event["skill"]):
                self.assertEqual(
                    event["digest"], demonstrations.record_digest(record)
                )
                self.assertEqual(event["claim_id"], record["claim_id"])
                self.assertEqual(event["status"], "real-data")

    def test_the_front_door_derives_every_count_it_claims(self):
        """The prose numbers come from the same reader the tree feeds.

        No expected value appears here. The topology reader refuses unless both
        marketplace manifests and tree discovery agree, so a passing claim
        rests on three sources rather than on somebody's memory.
        """
        text = front_door.read_document(ROOT, front_door.FRONT_DOOR)
        display = front_door.rendered(text)
        counts = discover_topology(ROOT).counts()
        claims = 0
        for marker in front_door.markers(text):
            if marker.kind != "count":
                continue
            claims += 1
            key = marker.attributes["key"]
            claim = front_door.COUNT_CLAIM_RE.match(display[marker.end:].lstrip())
            with self.subTest(key=key):
                self.assertIsNotNone(claim)
                self.assertEqual(
                    int(claim.group("number")), counts[front_door.COUNT_KEYS[key]]
                )
        self.assertEqual(claims, len(front_door.COUNT_KEYS))

    def test_no_count_claim_on_the_front_door_is_unmarked(self):
        text = front_door.read_document(ROOT, front_door.FRONT_DOOR)
        display = front_door.rendered(text)
        marked = set()
        for marker in front_door.markers(text):
            if marker.kind != "count":
                continue
            tail = display[marker.end:]
            marked.add(marker.end + (len(tail) - len(tail.lstrip())))
        unmarked = [
            claim.group(0)
            for claim in front_door.COUNT_CLAIM_RE.finditer(display)
            if claim.start() not in marked
        ]
        self.assertEqual(unmarked, [])

    def test_the_front_door_emits_one_bounded_event_per_card(self):
        captured = io.StringIO()
        with redirect_stdout(captured):
            self.assertEqual(front_door.main(["--root", str(ROOT)]), 0)
        emitted = [
            json.loads(line)
            for line in captured.getvalue().splitlines()
            if line.startswith("{")
        ]
        self.assertEqual(len(emitted), len(self.events))
        for event in emitted:
            with self.subTest(skill=event.get("skill")):
                self.assertEqual(
                    event["event"], "demonstration.public_claim.checked"
                )
                self.assertEqual(
                    set(event),
                    {
                        "claim_id",
                        "digest",
                        "directory",
                        "event",
                        "observed",
                        "skill",
                        "status",
                    },
                )

    def test_the_catalogue_holds_what_the_front_door_refuses_to_inline(self):
        display = front_door.rendered(
            front_door.read_document(ROOT, front_door.FRONT_DOOR)
        )
        targets = {target for _, target in front_door.link_targets(display)}
        governed = discover_topology(ROOT).governed
        linked = [
            directory
            for directory in governed
            if front_door.governed_home(directory) in targets
        ]
        self.assertLess(len(linked), len(governed))
        catalogue = (ROOT / "FUTUREPROOFING.md").read_text(encoding="utf-8")
        for directory in governed:
            with self.subTest(skill=directory.rsplit("/", 1)[-1]):
                self.assertIn(
                    f"({front_door.governed_home(directory)})", catalogue
                )


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class CheckerBoundaryTests(unittest.TestCase):
    """What the checker is allowed to do, asserted over its own source."""

    def test_the_checker_starts_no_subprocess_and_opens_no_socket(self):
        """Asserted over the parsed module, not over the prose describing it.

        A string search would fail on this file's own docstring, which says
        the checker starts no subprocess, and would pass on a call reached
        through an alias. The import graph and the call targets decide it.
        """
        tree = ast.parse(
            (ROOT / "scripts" / "check_public_front_door.py").read_text(
                encoding="utf-8"
            )
        )
        forbidden = {"subprocess", "socket", "urllib", "http", "ssl", "ctypes"}
        imported = set()
        called = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
            elif isinstance(node, ast.Call):
                called.add(ast.unparse(node.func))
        self.assertEqual(imported & forbidden, set())
        for target in (
            "os.system",
            "os.popen",
            "os.execv",
            "eval",
            "exec",
            "open",
            "os.write",
            "os.mkdir",
            "os.rename",
            "os.replace",
            "os.unlink",
        ):
            with self.subTest(call=target):
                self.assertNotIn(target, called)

    def test_every_declared_refusal_is_reachable_from_the_checker(self):
        source = (
            ROOT / "scripts" / "check_public_front_door.py"
        ).read_text(encoding="utf-8")
        for code in front_door.REFUSALS:
            with self.subTest(code=code):
                self.assertGreaterEqual(source.count(f'"{code}"'), 2)

    def test_the_refusal_prefix_stays_out_of_the_demonstration_namespace(self):
        """`Dnnn` belongs to the demonstration catalogue, which a parity test counts."""
        for code in front_door.REFUSALS:
            with self.subTest(code=code):
                self.assertNotRegex(code, r"^D[0-9]{3}$")
                self.assertNotIn(code, demonstrations.REFUSALS)


if __name__ == "__main__":
    unittest.main()
