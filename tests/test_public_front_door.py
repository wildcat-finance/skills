"""The maintained-surface contract, and one specimen per refusal it makes.

Two rules govern everything below.

**Against the live tree, assert agreement and never a literal.** The live cases
ask whether the swept pages still satisfy the contract, whether every count
they publish still agrees with what the tree derives, whether every
member-status sentence still describes the version its own ledger records, and
whether the cards still bind the records the tree actually holds. None of them
names a count, a digest, a claim id, a skill or a version, because a plugin
landing tomorrow and a release shipping tonight move all of those together and
no case here should notice.

**Against a specimen, assert exactly one deliberate break.** Every specimen
plants its own three-plugin tree with arbitrary ids that share nothing with
this repository. The whole swept set is planted around it, so a specimen for
one page is checked against a repository holding its contract everywhere else,
and each differs from the page this module plants in one place. The
placeholders in a specimen are substituted from that planted tree, so a
specimen carries the shape of a page rather than a frozen copy of one skill's
evidence.

Nothing here executes a demonstration. The `.github/workflows/repo.yml` job
checks this repository out and installs nothing, so a case that ran one whose
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
SPECIMENS_RELATIVE = "tests/fixtures/public-front-door"
SPECIMEN_BYTES = 262_144
# `document` is optional and defaults to the front door, because most specimens
# are front doors. A specimen for another swept page names it, and the planted
# tree supplies the rest of the set around it.
HEADER_RE = re.compile(
    r'<!--\s*front-door-specimen:\s*expect="(?P<expect>[A-Za-z0-9]+)"'
    r'\s+reason="(?P<reason>[^"]+)"'
    r'(?:\s+document="(?P<document>[^"]+)")?\s*-->'
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
# The version each planted ledger records. A status claim in the planted tree
# is bound to this, and a specimen that binds anything else is describing a
# release the ledger has left behind.
LEDGER_VERSION = "{plugin}-v1.0.0"
STALE_LEDGER_VERSION = "{plugin}-v0.1.0"
# The one frontier sentence each planted ledger records and each planted
# landing page quotes into its generated region. It holds a count claim and a
# member-status claim, so the clean sweep proves that a region exempts a claim
# its own ledger carries and the FD36 cases prove it exempts nothing else.
LEDGER_FRONTIER = (
    "The seed release holds 41 findings from three skills chosen by hand, "
    "and the compile path has not shipped."
)


def write(path: Path, body: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


def record_for(root: Path, member: dict) -> dict:
    """Plant one governed skill and return the record its ledger carries.

    `host` names the plugin when it is not the skill's own name, which is what
    the phase host looks like: one plugin shipping several governed skills.
    Every skill owes a ledger and a demonstration record wherever it sits.
    """

    plugin = member["id"]
    host = member.get("host", plugin)
    status = member["status"]
    directory = f"plugins/{host}/skills/{plugin}"
    # The ledger carries the one row the status rule reads. A bare `# ledger`
    # was enough while nothing asked a skill what version it was on.
    #
    # It also carries the frontier row a landing page quotes into its
    # marketplace block. The
    # live blocks are copied out of this row, so planting it is what lets the
    # clean run exercise the happy path of the rule that decides whether a
    # claim inside a generated region was derived or typed. It carries one
    # count claim and one member-status claim on purpose: both are exempt
    # there only because this ledger holds the sentence making them.
    write(
        root / directory / "EVOLUTION.md",
        "# LEDGER\n\n"
        f"- Current version: `{LEDGER_VERSION.format(plugin=plugin)}`\n"
        "- Frontier status: `open`\n"
        f"- Current frontier: {LEDGER_FRONTIER}\n",
    )
    write(root / directory / "SKILL.md", "# skill\n")

    line = f"{plugin}: the held specimen rebuilds"
    program = f"plugins/{host}/{plugin}-demo.py"
    program_digest = write(root / program, f'print("{line}")\n')
    held = f"plugins/{host}/specimens/{plugin}-held.json"
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
        invented = f"plugins/{host}/specimens/{plugin}-invented.json"
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
        "plugin": host,
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


# The rest of the swept set, as this tree holds it. Each one is short and each
# one satisfies the rules its page carries, so a specimen that replaces one of
# them is still the only break in the sweep. The `INSTALL.md` companion carries
# a pinned historical figure, which is what makes the clean run exercise the
# happy path of a rule whose whole point is refusing a rewrite.
COMPANIONS = {
    "INSTALL.md": """# INSTALLING THE SPECIMEN COLLECTIVE

## INSTALL

Add the specimen marketplace, then install the member that owns your task.

## A DATED MEASUREMENT

Measured on 2026-01-01 over one install: the update command left
<!-- front-door:historical captured="2026-01-01" figure="two" -->two plugins
pinned at their old commit. That figure describes that day and no other.
""",
    "FUTUREPROOFING.md": """# FUTUREPROOFING THE SPECIMEN COLLECTIVE

## THE CATALOGUE

Every member of this tree, what it holds today, and what is missing.

### LANTERN

It rebuilds the specimen it preserved and claims nothing further.
""",
    "SHOGGOTH.md": """# SPECIMEN COLLECTIVE IDENTITY

## WHAT THE NAME COVERS

The roster holds <!-- front-door:count key="members" -->{{count:members}}
members, derived from the tree rather than typed here.
""",
    "PROMISE_MACHINE.md": """# Specimen promise contract

## Governing principle

State what an operation establishes and what it does not.
""",
    "docs/how-to-help-shoggoth.md": """# HOW TO HELP THE SPECIMEN COLLECTIVE

## WAYS TO CONTRIBUTE

Preserve one specimen, or write the check that reads it.
""",
    "docs/fiat-in-plain-english.md": """# THE DELIVERY LOOP IN PLAIN ENGLISH

## THE SHORT VERSION

Study, runbook, build, audit, publish.
""",
    "docs/the-promise-machine-explained-properly.md": (
        """# THE SPECIMEN PROMISE CONTRACT, EXPLAINED

## WHAT A PROMISE CONTAINS

What it establishes, the evidence behind it, and what it refuses.
"""
    ),
    ".agents/skills/promise-machine/SKILL.md": """# Specimen router

## Select one runtime contract

Match the request to the narrowest member and read its contract in full.
""",
}
LANDING = """# {upper}

<!-- marketplace-context:start -->
## In one line

{name} holds one preserved specimen and rebuilds it offline.

**Current frontier.** {frontier}
<!-- marketplace-context:end -->

## WHAT IT SHIPS

<!-- front-door:status skill="{name}" version="{version}" -->
This version rebuilds the held specimen and claims nothing beyond it.
"""


def plant(root: Path) -> dict[str, dict]:
    """Materialise the whole specimen repository and return its records."""

    records = {member["id"]: record_for(root, member) for member in MEMBERS}
    for member in MEMBERS:
        name = member["id"]
        write(
            root / "plugins" / name / "README.md",
            LANDING.format(
                name=name,
                upper=name.upper(),
                version=LEDGER_VERSION.format(plugin=name),
                frontier=LEDGER_FRONTIER,
            ),
        )
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


def install(root: Path, records: dict[str, dict], overrides: dict[str, str]) -> None:
    """Write every swept document, with the named ones replaced.

    `clean.md` is the default front door, so a specimen for another page is
    checked against a repository that holds its contract everywhere else.
    """

    pages = {front_door.FRONT_DOOR: read_specimen("clean"), **COMPANIONS, **overrides}
    for relative, body in pages.items():
        write(root / relative, substitute(body, root, records))


def substitute(body: str, root: Path, records: dict[str, dict]) -> str:
    """Fill a specimen's placeholders from the tree that was actually planted."""

    counts = discover_topology(root).counts()

    def value(match: re.Match) -> str:
        kind, name = match.group("kind"), match.group("name")
        if kind == "count":
            return str(counts[front_door.COUNT_KEYS[name]])
        if kind == "version":
            return LEDGER_VERSION.format(plugin=name)
        if kind == "stale":
            return STALE_LEDGER_VERSION.format(plugin=name)
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


def document_codes(overrides: dict[str, str]) -> list[str]:
    """Plant the specimen tree, install the named documents, and check it.

    Every swept page exists in the planted tree. A specimen replaces one of
    them, which is what keeps a case about one refusal instead of about a
    half-built repository: absence is its own rule, and the sweep would report
    it once for every page the case forgot.
    """

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        records = plant(root)
        install(root, records, overrides)
        findings, _ = front_door.check(root)
    return [finding.code for finding in findings]


def body_codes(body: str) -> list[str]:
    """Plant the specimen tree, install this front door, and check it."""

    return document_codes({front_door.FRONT_DOOR: body})


def covered_by_a_region(spans, offset: int) -> bool:
    """Whether any generated region covers `offset`, whatever it exempts.

    The live cases below ask whether a claim is unmarked, and a claim inside a
    generated region is answered by the region rules instead. They read the
    span's two offsets rather than calling the checker's own `inside`, which
    now takes the rule being decided: these cases decide no single rule, and
    the checker stays the authority on what a region exempts. That authority is
    asserted by `test_the_front_door_holds_its_contract` and by the FD36 cases,
    so a region claim this helper waves past is still read somewhere.
    """

    return any(span[0] <= offset < span[1] for span in spans)


def read_no_follow(root: Path, relative: str) -> str:
    """Read one document the way the checker reads one, refusing a symlink.

    `Path.read_text()` follows a link where the checker's no-follow descriptor
    walk refuses one, so a link planted among the specimens would have been
    read here and refused there, and the suite would have been the more
    trusting of the two. Both sides now read through the same reader.
    """

    payload = demonstrations._read_regular_file(
        root, relative, maximum=SPECIMEN_BYTES, label=relative
    )
    return payload.decode("utf-8")


def read_specimen(name: str) -> str:
    return read_no_follow(ROOT, f"{SPECIMENS_RELATIVE}/{name}.md")


def specimen_header(name: str) -> re.Match:
    header = HEADER_RE.search(read_specimen(name))
    if header is None:
        raise AssertionError(f"{name} declares no expectation")
    return header


def specimen_document(name: str) -> str:
    """The swept page a specimen stands in for, defaulting to the front door."""

    return specimen_header(name).group("document") or front_door.FRONT_DOOR


def specimen_codes(name: str) -> list[str]:
    """Plant the specimen tree, install one specimen page, and check it."""

    return document_codes({specimen_document(name): read_specimen(name)})


def broken(old: str, new: str, *, count: int = 1) -> str:
    """`clean.md` with one substitution, refusing a silent no-op.

    The cases below carry their break inline rather than as another specimen
    file. A specimen is an input the checker reads; these are guards for rules
    the checker did not have, and keeping each one inside this module is what
    lets it be replayed against the commit's parent on its own.
    """

    body = read_specimen("clean")
    if body.count(old) != count:
        raise AssertionError(f"{old!r} appears {body.count(old)} times, not {count}")
    return body.replace(old, new, count)


FILLER = ("word " * 160).strip()

# One document per declared refusal, each provoking that refusal and nothing
# about the others. Counting a code's occurrences in the checker's source said
# only that somebody typed it twice; a regression that stopped a rule reaching
# its `_finding` call left that count untouched. These run the rule instead.
PROVOCATIONS = {
    # FD01 needs no front door at all, so it is the one entry with no body.
    "FD01": None,
    "FD02": lambda: broken(
        '  <img src="./assets/characters/shoggoth.png" width="1200"'
        ' alt="The Shoggoth collective">\n',
        "",
    ),
    "FD03": lambda: broken(
        "A synthetic front door for a synthetic tree. It holds",
        FILLER + "\nA synthetic front door for a synthetic tree. It holds",
    ),
    "FD04": lambda: broken(
        "## SO, YOU WANT TO BUILD GOD?", "## SO, YOU WANT TO BUILD"
    ),
    "FD05": lambda: broken(
        "Start at [how to help](./docs/how-to-help-shoggoth.md), which offers a"
        " small\nroute as well as the controlled one.",
        "Start somewhere else.",
    ),
    "FD06": lambda: broken(
        "## WHAT A RESULT MEANS", " ".join([FILLER] * 9) + "\n\n## WHAT A RESULT MEANS"
    ),
    "FD07": lambda: broken(
        "## WHAT A RESULT MEANS",
        "See [again](./FUTUREPROOFING.md).\n\n## WHAT A RESULT MEANS",
    ),
    "FD08": lambda: broken(
        "## WHAT A RESULT MEANS",
        "See [quarry](./plugins/quarry).\n\n## WHAT A RESULT MEANS",
    ),
    "FD09": lambda: broken(
        "The [Promise Machine contract](./PROMISE_MACHINE.md) is the shared law"
        " between",
        "The shared law between",
    ),
    "FD10": lambda: broken(
        "[The catalogue](./FUTUREPROOFING.md) lists every member, including the",
        "The catalogue lists every member, including the",
    ),
    "FD11": lambda: broken("## WHAT A RESULT MEANS", "## What a result means"),
    "FD12": lambda: broken(
        "## WHAT A RESULT MEANS",
        "![x](./plugins/lantern/art.png)\n\n## WHAT A RESULT MEANS",
    ),
    "FD13": lambda: broken(
        "Ask the Atlas for a number. Pick your harness. Finish what you start.",
        "Ask the Atlas.",
    ),
    "FD14": lambda: broken("<!-- front-door:aside -->\n", ""),
    "FD15": lambda: broken("## WHAT CAN IT DO?", "## WHAT CAN IT DO"),
    "FD16": lambda: broken(' digest="{{digest:lantern}}" -->', " -->"),
    "FD17": lambda: broken('skill="lantern" claim=', 'skill="nowhere" claim='),
    "FD18": lambda: broken('claim="{{claim:lantern}}"', 'claim="not-the-claim"'),
    "FD19": lambda: broken('digest="{{digest:lantern}}"', 'digest="' + "0" * 64 + '"'),
    "FD20": lambda: broken(
        'skill="thicket" claim="{{claim:thicket}}" digest="{{digest:thicket}}"',
        'skill="quarry" claim="{{claim:quarry}}" digest="{{digest:quarry}}"',
    ),
    "FD21": lambda: broken(
        "## WHAT A RESULT MEANS",
        "### LANTERN, AGAIN\n\n"
        '<!-- front-door:demo skill="lantern" claim="{{claim:lantern}}"'
        ' digest="{{digest:lantern}}" -->\n'
        "Run `python3 scripts/demonstrations.py run --record"
        " {{directory:lantern}} --report tmp/demo/l2.json`\n"
        "over the preserved `{{source:lantern}}` and it reports"
        " `{{observed:lantern}}`.\n{{nonclaim:lantern}}\n\n"
        "## WHAT A RESULT MEANS",
    ),
    "FD22": lambda: broken(
        "Run `python3 scripts/demonstrations.py run --record"
        " {{directory:lantern}} --report tmp/demo/lantern.json`",
        "Run it.",
    ),
    "FD23": lambda: broken(
        "over the preserved `{{source:lantern}}` and it reports",
        "over the preserved `nothing` and it reports",
    ),
    "FD24": lambda: broken(
        "and it reports `{{observed:lantern}}`.", "and it reports `nothing`."
    ),
    "FD25": lambda: broken("{{nonclaim:lantern}}\n", ""),
    "FD26": lambda: broken(
        '<!-- front-door:count key="domain" -->{{count:domain}} domain agents',
        '<!-- front-door:count key="domain" -->99 domain agents',
    ),
    "FD27": lambda: broken(
        '<!-- front-door:count key="domain" -->',
        '<!-- front-door:count key="bogus" -->',
    ),
    "FD28": lambda: broken(
        "## WHAT A RESULT MEANS",
        "There are 42 plugins here.\n\n## WHAT A RESULT MEANS",
    ),
    "FD29": lambda: broken(
        '<!-- front-door:count key="governed" -->{{count:governed}} governed'
        " skills in",
        '<!-- front-door:count key="plugins" -->{{count:plugins}} governed'
        " skills in",
    ),
    "FD30": lambda: broken(
        "## WHAT A RESULT MEANS",
        "<!-- contributors:start -->\n\n## WHAT A RESULT MEANS",
    ),
    # The last three break a page that is not the front door, so each is named
    # rather than built: the specimen file carries the page it stands in for,
    # and the planted tree supplies the rest of the sweep around it.
    "FD31": "rewritten-historical-figure",
    "FD32": "unbound-member-status",
    "FD33": "superseded-member-status",
    # These two break a page that is not the front door and still stay in this
    # module. A specimen is a fixture file rather than a test file, so it does
    # not travel to the detached parent with the case that reads it, and a
    # guard that cannot be replayed there proves nothing about what the fix
    # changed. A callable returning overrides names its own page instead.
    "FD34": lambda: broken(
        "## WHAT A RESULT MEANS",
        '<!-- front-door:historical captured="2026-01-01" figure="99" -->99'
        " plugins were counted.\n\n## WHAT A RESULT MEANS",
    ),
    "FD35": lambda: {
        "plugins/lantern/README.md": LANDING.format(
            name="lantern",
            upper="LANTERN",
            version="{{version:lantern}}",
            frontier=LEDGER_FRONTIER,
        ).replace('skill="lantern"', 'skill="thicket"')
    },
    "FD36": lambda: {
        "plugins/lantern/README.md": LANDING.format(
            name="lantern",
            upper="LANTERN",
            version="{{version:lantern}}",
            frontier=LEDGER_FRONTIER,
        ).replace(
            "lantern holds one preserved specimen and rebuilds it offline.",
            "lantern holds one preserved specimen and rebuilds it offline.\n\n"
            "**Current frontier.** The tree holds 99 plugins.",
        )
    },
    "FD37": lambda: {
        "plugins/lantern/README.md": LANDING.format(
            name="lantern",
            upper="LANTERN",
            version="{{version:lantern}}",
            frontier=LEDGER_FRONTIER,
        ).replace(
            "This version rebuilds the held specimen and claims nothing beyond it.",
            "{{stale:lantern}} has not shipped the rebuild path.",
        )
    },
}


class EntryParentGuardTests(unittest.TestCase):
    """Each specimen is red before the checker it guards exists."""

    def test_every_specimen_declares_what_it_breaks(self):
        found = sorted(path.stem for path in SPECIMENS.glob("*.md"))
        self.assertTrue(found, SPECIMENS)
        for name in found:
            header = HEADER_RE.search(read_specimen(name))
            with self.subTest(specimen=name):
                self.assertIsNotNone(header, "specimen declares no expectation")
                self.assertIsNotNone(
                    front_door, f"{name} has no checker on the entry parent"
                )
                expect = header.group("expect")
                if expect != "clean":
                    self.assertIn(expect, front_door.REFUSALS)

    def test_every_specimen_stands_in_for_a_swept_page(self):
        """A specimen for a page nothing reads guards nothing."""
        swept = {
            item.relative
            for item in front_door.maintained_documents(discover_topology(ROOT))
        } | {f"plugins/{member['id']}/README.md" for member in MEMBERS}
        for path in sorted(SPECIMENS.glob("*.md")):
            with self.subTest(specimen=path.stem):
                self.assertIn(specimen_document(path.stem), swept)


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class SpecimenTests(unittest.TestCase):
    """One deliberate break each, against a tree that shares no id with this one."""

    def specimens(self):
        for path in sorted(SPECIMENS.glob("*.md")):
            header = HEADER_RE.search(read_specimen(path.stem))
            yield path.stem, header.group("expect")

    def test_the_clean_specimen_holds_the_whole_contract(self):
        self.assertEqual(specimen_codes("clean"), [])

    def test_each_specimen_reports_the_refusal_it_names(self):
        for name, expect in self.specimens():
            if expect == "clean":
                continue
            with self.subTest(specimen=name):
                self.assertIn(expect, specimen_codes(name))

    def test_a_specimen_beyond_the_front_door_reports_only_its_own_break(self):
        """It differs from the page this suite plants in exactly one place.

        A front-door specimen may cascade, because moving one heading moves
        every position after it. These are short pages standing in for short
        pages, so a second code means the specimen has drifted away from the
        companion it was cut from and is no longer guarding what it says.
        """
        for name, expect in self.specimens():
            if expect == "clean" or specimen_document(name) == front_door.FRONT_DOOR:
                continue
            with self.subTest(specimen=name):
                self.assertEqual(specimen_codes(name), [expect])

    def test_each_named_document_that_is_absent_fails_the_sweep(self):
        """Absence is a refusal, never a quiet skip, for every swept page.

        A sweep that reads whatever it finds reports nothing when the document
        it was meant to read is gone, and a reader cannot tell that from a
        clean result. The case removes each page in turn rather than one of
        them, because a set is only as honest as its least-checked member.
        """
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            records = plant(root)
            install(root, records, {})
            swept = [
                item.relative
                for item in front_door.maintained_documents(discover_topology(root))
            ]
            self.assertEqual(front_door.check(root)[0], [])
            for relative in swept:
                with self.subTest(document=relative):
                    body = (root / relative).read_text(encoding="utf-8")
                    (root / relative).unlink()
                    findings, events = front_door.check(root)
                    self.assertEqual(
                        [finding.code for finding in findings], ["FD01"]
                    )
                    self.assertEqual(events, [])
                    self.assertIn(relative, str(findings[0]))
                    (root / relative).write_text(body, encoding="utf-8")

    def test_the_maintained_set_covers_the_named_pages_and_every_plugin(self):
        """A sweep over an empty set passes while checking nothing.

        The plugin half is derived rather than declared, so this asserts the
        relation instead of a number: one landing page per plugin the topology
        reader finds, and no plugin without one.
        """
        named = {item.relative for item in front_door.MAINTAINED_DOCUMENTS}
        self.assertIn(front_door.FRONT_DOOR, named)
        topology = discover_topology(ROOT)
        swept = front_door.maintained_documents(topology)
        self.assertEqual(
            {item.relative for item in swept} - named,
            {f"plugins/{plugin}/README.md" for plugin in topology.plugins},
        )
        self.assertTrue(
            all(item.rules for item in swept), "a page with no rules is not swept"
        )


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class AuditRoundOneTests(unittest.TestCase):
    """One case per rule the first audit round found the checker did not have.

    Each builds its own front door from `clean.md`, so each fails on the commit
    before the fix without needing a new file to travel with it.
    """

    def test_a_heading_only_inside_a_fence_is_not_a_heading(self):
        """Structure came from the fenced text, so code could stand in for it."""
        codes = body_codes(
            broken(
                "## SO, YOU WANT TO BUILD GOD?",
                "```text\n## SO, YOU WANT TO BUILD GOD?\n```",
            )
        )
        self.assertIn("FD04", codes)

    def test_a_shell_comment_inside_a_fence_is_not_a_sentence_case_heading(self):
        """The same blindness refused legitimate content in the other direction."""
        codes = body_codes(
            broken(
                "Run `python3 scripts/demonstrations.py run --record "
                "{{directory:lantern}} --report tmp/demo/lantern.json`",
                "```bash\n# rebuild the held specimen\ntrue\n```\nRun `python3 "
                "scripts/demonstrations.py run --record {{directory:lantern}} "
                "--report tmp/demo/lantern.json`",
            )
        )
        self.assertNotIn("FD11", codes)

    def test_two_cards_may_not_bind_one_record(self):
        """Set membership answered a different question from the contract's."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "### LANTERN REBUILDS ITS HELD SPECIMEN, AGAIN\n\n"
                '<!-- front-door:demo skill="lantern" claim="{{claim:lantern}}" '
                'digest="{{digest:lantern}}" -->\n'
                "Run `python3 scripts/demonstrations.py run --record "
                "{{directory:lantern}} --report tmp/demo/lantern-two.json`\n"
                "over the preserved `{{source:lantern}}` and it reports "
                "`{{observed:lantern}}`.\n{{nonclaim:lantern}}\n\n"
                "## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD21", codes)

    def test_a_marker_key_must_name_the_quantity_its_prose_names(self):
        """The number was right for the key and wrong for every reader."""
        codes = body_codes(
            broken(
                '<!-- front-door:count key="governed" -->{{count:governed}} '
                "governed skills in",
                '<!-- front-door:count key="plugins" -->{{count:plugins}} '
                "governed skills in",
            )
        )
        self.assertIn("FD29", codes)

    def test_a_count_claim_inside_an_all_caps_heading_is_read(self):
        """Every heading must be all caps, so a lower-case grammar saw none."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "## THE 99 GOVERNED SKILLS\n\nText.\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD28", codes)

    def test_a_count_claim_written_in_words_is_read(self):
        """A spelled-out number asserted a derived quantity and escaped."""
        codes = body_codes(
            broken(
                "A synthetic front door for a synthetic tree. It holds",
                "A synthetic front door holding thirty governed skills. It holds",
            )
        )
        self.assertIn("FD28", codes)

    def test_a_bare_topology_noun_carrying_a_number_is_read(self):
        """`domains` and `phases` were qualifiers with no noun to qualify."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "There are 42 domains here.\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD28", codes)

    def test_a_generated_region_that_is_never_closed_is_refused(self):
        """Deleting one marker exempted every heading below it."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "<!-- contributors:start -->\n\n## What a result means",
            )
        )
        self.assertIn("FD30", codes)
        self.assertIn("FD11", codes)

    def test_a_generated_region_may_not_reach_a_governed_heading(self):
        """Closing it and widening it did the same thing more quietly."""
        codes = body_codes(
            broken(
                "# THE SPECIMEN COLLECTIVE",
                "<!-- contributors:start -->\n\n# THE SPECIMEN COLLECTIVE",
            ).replace(
                "## THE REST OF THE COLLECTIVE",
                "<!-- contributors:end -->\n\n## The rest of the collective",
                1,
            )
        )
        self.assertIn("FD30", codes)
        self.assertIn("FD11", codes)

    def test_a_heading_with_no_letter_in_it_is_not_all_caps(self):
        """`## 2026` held no lower case because it held no case at all."""
        codes = body_codes(
            broken("## WHAT A RESULT MEANS", "## 2026\n\nText.\n\n## WHAT A RESULT MEANS")
        )
        self.assertIn("FD11", codes)

    def test_a_reference_style_image_is_an_image(self):
        """A second portrait reached the root through a definition."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "![Lantern][lantern-art]\n\n"
                "[lantern-art]: ./plugins/lantern/art.png\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD12", codes)

    def test_a_single_quoted_html_image_is_an_image(self):
        """The attribute pattern read one quoting style of two."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "<img src='./plugins/lantern/art.png' width='200'>\n\n"
                "## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD12", codes)

    def test_a_reference_style_link_counts_towards_unique_targets(self):
        """A route linked twice, once by reference, read as linked once."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "See [the catalogue][fp].\n\n[fp]: ./FUTUREPROOFING.md\n\n"
                "## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD07", codes)


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class AuditRoundTwoTests(unittest.TestCase):
    """One case per rule the second audit round found the checker did not have.

    Round one closed eight holes. These are the spellings its fixes did not
    reach: a fence delimiter indented the way CommonMark permits, a count claim
    with an adjective the closed qualifier list never learned, the shortcut
    reference form and the unquoted and upper-case HTML attribute, and a
    generated region widened around a heading the earlier rule did not name.
    """

    def test_an_indented_closing_fence_closes_the_fence(self):
        """The renderer closes there and the checker did not, so it blanked on."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "```text\nexample\n  ```\n## Sentence case below an indented"
                " closer\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD11", codes)

    def test_an_indented_opening_fence_opens_a_fence(self):
        """The other direction of the same blindness refuses fenced content."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "   ```text\n## Sentence case inside an indented fence\n   ```\n\n"
                "## WHAT A RESULT MEANS",
            )
        )
        self.assertNotIn("FD11", codes)

    def test_a_count_claim_with_an_unlisted_qualifier_is_read(self):
        """One adjective the closed list never learned hid the whole claim."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "There are 42 assorted plugins here.\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD28", codes)

    def test_a_singular_topology_noun_carrying_a_number_is_read(self):
        """`domains` and `phases` were read in the plural only."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "There is 1 domain here.\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD28", codes)

    def test_a_shortcut_reference_image_is_an_image(self):
        """`![label]` renders the image that `![alt][label]` renders."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "![lantern-art]\n\n[lantern-art]: ./plugins/lantern/art.png\n\n"
                "## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD12", codes)

    def test_a_shortcut_reference_link_counts_towards_unique_targets(self):
        """So does the link form of it."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "See [fp].\n\n[fp]: ./FUTUREPROOFING.md\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD07", codes)

    def test_an_unquoted_html_attribute_is_read(self):
        """HTML does not require the quotes the pattern required."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                "<img src=./plugins/lantern/art.png>\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD12", codes)

    def test_an_upper_case_html_tag_is_read(self):
        """HTML tag and attribute names are case-insensitive."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                '<A HREF="./FUTUREPROOFING.md">again</A>\n\n## WHAT A RESULT MEANS',
            )
        )
        self.assertIn("FD07", codes)

    def test_a_generated_region_may_cover_no_other_heading(self):
        """Naming three headings left every other one exemptible."""
        codes = body_codes(
            broken(
                "## THE REST OF THE COLLECTIVE",
                "<!-- contributors:start -->\n\n## The rest of the collective\n\n"
                "<!-- contributors:end -->",
            )
        )
        self.assertIn("FD30", codes)
        self.assertIn("FD11", codes)

    def test_a_second_region_boundary_is_not_a_region(self):
        """A repeated opening marker widened the span the first one opened."""
        codes = body_codes(
            broken(
                "## THE REST OF THE COLLECTIVE",
                "<!-- contributors:start -->\n\n<!-- contributors:start -->\n\n"
                "## The rest of the collective\n\n<!-- contributors:end -->",
            )
        )
        self.assertIn("FD30", codes)
        self.assertIn("FD11", codes)

    def test_a_region_marker_inside_a_fence_opens_no_region(self):
        """A marker shown as an example is not a boundary."""
        codes = body_codes(
            broken(
                "## THE REST OF THE COLLECTIVE",
                "```text\n<!-- contributors:start -->\n```\n\n"
                "## The rest of the collective\n\n<!-- contributors:end -->",
            )
        )
        self.assertIn("FD11", codes)

    def test_a_broken_region_is_refused_on_a_page_with_no_heading_rule(self):
        """The refusal used to belong to whichever rule happened to run.

        `generated_spans` was computed inside each rule and only the heading
        rule reported its refusals, so a page carrying counts but not headings
        could open a region and never close it and be told nothing. The claims
        below stayed checked, because a refused region is never applied, but
        FD30 was a declared refusal two swept pages could not report. The
        router contract is exactly such a page.
        """
        router = ".agents/skills/promise-machine/SKILL.md"
        item = next(
            entry
            for entry in front_door.MAINTAINED_DOCUMENTS
            if entry.relative == router
        )
        self.assertFalse(item.carries(front_door.HEADING_RULE))
        codes = document_codes(
            {
                router: COMPANIONS[router]
                + "\n<!-- marketplace-context:start -->\n\n"
                "The distribution exposes 99 governed skills.\n"
            }
        )
        self.assertIn("FD30", codes)
        self.assertIn("FD28", codes)

    def test_a_symlinked_specimen_is_refused_rather_than_followed(self):
        """The suite reads a specimen the way the checker reads a document."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            (root / "fixtures").mkdir()
            (root / "outside.md").write_text("planted\n", encoding="utf-8")
            (root / "fixtures" / "linked.md").symlink_to(root / "outside.md")
            with self.assertRaises(Exception) as caught:
                read_no_follow(root, "fixtures/linked.md")
        self.assertNotIsInstance(caught.exception, AssertionError)


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class StepFiveAuditRoundOneTests(unittest.TestCase):
    """One case per hole the step-5 audit found in the widened sweep.

    Two of the three new rule families arrived with an exemption nobody had to
    ask for. A `front-door:historical` marker took a number out of derivation
    on any swept page, so a live count claim could be published as a dated
    capture and never compared with the tree again. A generated region did the
    same for every count and status claim between two comment markers, on any
    page, whether or not that page's generator writes there. The member-status
    marker named a version and nothing joined it to the member the sentence was
    about. The rest are spellings: the status grammar read `yet` in one branch
    and not another, and could not see the contraction this repository's own
    voice mask calls normal.
    """

    def test_a_historical_marker_off_its_page_exempts_nothing(self):
        """A live count published as a dated capture escaped both count rules."""
        codes = body_codes(
            broken(
                "## WHAT A RESULT MEANS",
                '<!-- front-door:historical captured="2026-01-01" figure="99" -->'
                "99 plugins are installed.\n\n## WHAT A RESULT MEANS",
            )
        )
        self.assertIn("FD34", codes)
        self.assertIn("FD28", codes)

    def test_a_historical_marker_may_not_replace_a_count_marker(self):
        """Swapping the marker kind turned a derived claim into a literal."""
        codes = body_codes(
            broken(
                '<!-- front-door:count key="domain" -->{{count:domain}} domain agents',
                '<!-- front-door:historical captured="2026-01-01" figure="99" -->'
                "99 domain agents",
            )
        )
        self.assertIn("FD34", codes)
        self.assertIn("FD28", codes)

    def test_a_historical_marker_holds_on_the_page_that_records_the_capture(self):
        """The exemption is real where a dated measurement is real."""
        self.assertEqual(document_codes({}), [])

    def test_a_generated_region_governs_nothing_away_from_its_own_page(self):
        """Two comment markers around any prose exempted every claim in it."""
        codes = document_codes(
            {
                "SHOGGOTH.md": COMPANIONS["SHOGGOTH.md"]
                + "\n<!-- marketplace-context:start -->\n\n"
                "The tree holds 99 plugins and this version has not shipped.\n"
                "<!-- marketplace-context:end -->\n"
            }
        )
        self.assertIn("FD30", codes)
        self.assertIn("FD28", codes)
        self.assertIn("FD32", codes)

    def test_a_landing_status_marker_names_a_member_that_page_ships(self):
        """The marker's skill and the sentence's subject were unrelated."""
        codes = document_codes(
            {
                "plugins/lantern/README.md": LANDING.format(
                    name="lantern",
                    upper="LANTERN",
                    version="{{version:thicket}}",
                    frontier=LEDGER_FRONTIER,
                ).replace('skill="lantern"', 'skill="thicket"')
            }
        )
        self.assertIn("FD35", codes)

    def test_a_maintained_document_that_holds_nothing_is_refused(self):
        """An empty page satisfied every rule by carrying none of them."""
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            records = plant(root)
            install(root, records, {})
            (root / "plugins" / "quarry" / "README.md").write_text("", encoding="utf-8")
            findings, events = front_door.check(root)
        self.assertEqual([finding.code for finding in findings], ["FD01"])
        self.assertEqual(events, [])

    def test_the_status_grammar_reads_yet_in_every_branch(self):
        """`has not yet shipped` was read and `is not yet implemented` was not."""
        codes = document_codes(
            {
                "FUTUREPROOFING.md": COMPANIONS["FUTUREPROOFING.md"]
                + "\nThe compile path is not yet implemented.\n"
            }
        )
        self.assertIn("FD32", codes)

    def test_the_status_grammar_reads_a_contraction(self):
        """The house voice mask calls contractions normal; the rule could not."""
        codes = document_codes(
            {
                "FUTUREPROOFING.md": COMPANIONS["FUTUREPROOFING.md"]
                + "\nThe compile path hasn't shipped.\n"
            }
        )
        self.assertIn("FD32", codes)


def plant_phase_host(root: Path) -> None:
    """Add the one plugin that ships more than one governed skill.

    Round one narrowed a landing page's status marker to a member that page
    ships, and every plugin in the tree above ships exactly one, so the
    narrowing was never exercised against the shape it has to survive. The
    phase host ships ten in the live tree: a marker naming any of them
    satisfied "a member that page ships" while vouching for a claim about a
    different one, and binding a fast-moving member's status to a slow-moving
    sibling's ledger keeps a stale sentence current indefinitely.
    """

    # Both are planted `mixed`, so neither joins the front door's card set and
    # these cases stay about the status marker rather than about cards.
    for skill in ("fiat", "vulgate"):
        record_for(root, {"id": skill, "host": "hexaemeron", "status": "mixed"})
    write(
        root / "plugins" / "hexaemeron" / "README.md",
        "# HEXAEMERON\n\n## WHAT IT SHIPS\n\n"
        '<!-- front-door:status skill="fiat" version="fiat-v1.0.0" -->\n'
        "This version carries the delivery loop and claims nothing beyond it.\n",
    )
    for manifest, entry in (
        (".claude-plugin/marketplace.json", {"name": "hexaemeron", "source": "./plugins/hexaemeron"}),
        (
            ".agents/plugins/marketplace.json",
            {
                "name": "hexaemeron",
                "source": {"source": "local", "path": "./plugins/hexaemeron"},
            },
        ),
    ):
        path = root / manifest
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["plugins"].append(entry)
        write(path, json.dumps(payload, indent=2) + "\n")


def phase_host_codes(landing: str) -> list[str]:
    """Plant a tree that holds the phase host, then check one landing page."""

    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        records = plant(root)
        plant_phase_host(root)
        install(root, records, {"plugins/hexaemeron/README.md": landing})
        findings, _ = front_door.check(root)
    return [finding.code for finding in findings]


@unittest.skipIf(front_door is None, "Step 4 checker is absent on the entry parent")
class StepFiveAuditRoundTwoTests(unittest.TestCase):
    """The partial fixes round one left, and the two rules it wrote.

    Each case below was built as an attack on the round-one tree first and
    passed there, so every one of them names a claim that the sweep read and
    reported nothing about.
    """

    def test_a_historical_marker_names_a_date_the_page_records(self):
        """Naming the page left every number on it exemptible.

        The exemption was narrowed to the one page that records a dated
        capture, and then any number on that page could take it -- including a
        sentence saying the figure is current. The capture the marker names has
        to be one the reader can find.
        """
        codes = document_codes(
            {
                "INSTALL.md": COMPANIONS["INSTALL.md"]
                + "\n## WHAT SHIPS TODAY\n\nThe marketplace ships\n"
                '<!-- front-door:historical captured="2026-06-05" figure="99" -->99\n'
                "governed skills right now, and that number is current.\n"
            }
        )
        self.assertIn("FD34", codes)
        self.assertIn("FD28", codes)

    def test_a_historical_marker_captured_value_is_a_date(self):
        """`captured` was free text, so a dated capture needed no date."""
        for value in ("", "last summer", "2026"):
            with self.subTest(captured=value):
                codes = document_codes(
                    {
                        "INSTALL.md": COMPANIONS["INSTALL.md"].replace(
                            'captured="2026-01-01"', f'captured="{value}"'
                        )
                    }
                )
                self.assertIn("FD34", codes)
                self.assertIn("FD28", codes)

    def test_a_generated_region_exempts_only_a_count_its_ledger_carries(self):
        """Two comment markers still bought the exclusion on 18 landing pages.

        Round one refused a region declared away from its own page. On the page
        it belongs to, the region went on exempting every claim between its
        markers, and nothing in this repository writes those bytes.
        """
        codes = document_codes(
            {
                "plugins/lantern/README.md": LANDING.format(
                    name="lantern",
                    upper="LANTERN",
                    version="{{version:lantern}}",
                    frontier="The tree holds 99 plugins today.",
                )
            }
        )
        self.assertIn("FD36", codes)

    def test_a_generated_region_exempts_only_a_status_its_ledger_carries(self):
        codes = document_codes(
            {
                "plugins/lantern/README.md": LANDING.format(
                    name="lantern",
                    upper="LANTERN",
                    version="{{version:lantern}}",
                    frontier="The quarry compile path has not shipped.",
                )
            }
        )
        self.assertIn("FD36", codes)

    def test_a_generated_region_still_exempts_the_heading_its_owner_writes(self):
        """The heading is the marketplace's, and that half of it holds.

        `## In one line` is sentence case on every landing page in the tree.
        Scoping the exclusion to what each owner actually writes must not take
        that with it, or the fix trades one silent rule for a red one.
        """
        self.assertEqual(document_codes({}), [])

    def test_a_landing_marker_may_not_vouch_for_a_sibling_it_does_not_name(self):
        codes = phase_host_codes(
            "# HEXAEMERON\n\n## WHAT IT SHIPS\n\n"
            '<!-- front-door:status skill="vulgate" version="vulgate-v1.0.0" -->\n'
            "Fiat has not shipped its second controller, and this version of fiat\n"
            "does not ship one either.\n"
        )
        self.assertIn("FD35", codes)

    def test_a_landing_marker_may_vouch_for_a_sibling_its_prose_names(self):
        """A page may state a phase skill's status; it has to say which."""
        codes = phase_host_codes(
            "# HEXAEMERON\n\n## WHAT IT SHIPS\n\n"
            '<!-- front-door:status skill="vulgate" version="vulgate-v1.0.0" -->\n'
            "Vulgate has not shipped a second register, and this version does not\n"
            "ship one either.\n"
        )
        self.assertEqual(codes, [])

    def test_marked_prose_may_not_name_a_release_its_marker_does_not(self):
        """The marker was checked against the ledger and never against itself.

        A sentence naming a superseded release passed under a marker standing
        at the current one, which is the stale-status failure this whole rule
        exists for wearing a version number.
        """
        codes = document_codes(
            {
                "plugins/lantern/README.md": LANDING.format(
                    name="lantern",
                    upper="LANTERN",
                    version="{{version:lantern}}",
                    frontier=LEDGER_FRONTIER,
                ).replace(
                    "This version rebuilds the held specimen and claims nothing"
                    " beyond it.",
                    "{{stale:lantern}} has not shipped the rebuild path.",
                )
            }
        )
        self.assertIn("FD37", codes)

    def test_the_status_grammar_reads_the_conjugations_of_its_own_branches(self):
        """Twelve phrasings were silent; four were spellings of a live branch.

        The eight left over divided in two. These are conjugations of
        predicates the rule already names -- the passive, the past, `never` for
        `not`, and the adjective negating the same participle -- and a rule
        that reads `is not built` and not `was never built` is inconsistent
        rather than narrow.
        """
        for phrasing in (
            "has not been built",
            "has not been implemented",
            "was never built",
            "has never shipped",
            "was not implemented",
            "had not shipped",
            "remains unbuilt",
            "is unimplemented",
            "remain unimplemented",
        ):
            with self.subTest(phrasing=phrasing):
                codes = document_codes(
                    {
                        "FUTUREPROOFING.md": COMPANIONS["FUTUREPROOFING.md"]
                        + f"\nThe compile path {phrasing}.\n"
                    }
                )
                self.assertIn("FD32", codes)

    def test_the_status_grammar_reads_an_adverb_other_than_yet(self):
        """The adverb slot held one literal, so every other adverb escaped."""
        for phrasing in (
            "is not currently implemented",
            "has not so far shipped",
            "does not currently ship",
            "has not ever shipped",
        ):
            with self.subTest(phrasing=phrasing):
                codes = document_codes(
                    {
                        "FUTUREPROOFING.md": COMPANIONS["FUTUREPROOFING.md"]
                        + f"\nThe compile path {phrasing}.\n"
                    }
                )
                self.assertIn("FD32", codes)

    def test_the_heading_rule_is_exempted_only_for_two_named_contracts(self):
        """The exemption was visible in the code and pinned by no case.

        `test_the_maintained_set_covers_the_named_pages_and_every_plugin`
        asserts that each swept page carries some rule, so a third page could
        be given the contract rules and drop out of the house heading style
        with nothing reporting it. The set is named here instead.
        """
        documents = {
            item.relative: item
            for item in front_door.maintained_documents(discover_topology(ROOT))
        }
        exempt = sorted(
            relative
            for relative, item in documents.items()
            if not item.carries(front_door.HEADING_RULE)
        )
        self.assertEqual(
            exempt,
            [".agents/skills/promise-machine/SKILL.md", "PROMISE_MACHINE.md"],
        )
        self.assertTrue(
            all(item.carries(front_door.COUNT_RULE) for item in documents.values())
        )

    def test_the_heading_exemption_is_load_bearing_not_aesthetic(self):
        """A second checker pins those headings by exact sentence-case bytes.

        `PROMISE_MACHINE.md` is named in the study's own maintained set, so its
        exemption rests on the boundary clause rather than on the enumeration.
        This is the evidence behind that clause: upper-casing these headings
        reddens `python3 scripts/promise_machine.py check`, which is one of the
        step's own exit commands, so the two rules cannot both be satisfied.
        """
        promise_machine = (ROOT / "scripts" / "promise_machine.py").read_text(
            encoding="utf-8"
        )
        contract = (ROOT / "PROMISE_MACHINE.md").read_text(encoding="utf-8")
        pinned = re.findall(r'(?m)^    "(#{1,6} [^"]+)",$', promise_machine)
        self.assertTrue(pinned, "promise_machine.py pins no exact heading")
        sentence_case = [
            heading
            for heading in pinned
            if heading != heading.upper() and heading in contract
        ]
        self.assertTrue(
            sentence_case,
            "no pinned sentence-case heading occurs in PROMISE_MACHINE.md",
        )


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

    def test_the_maintained_surface_derives_every_count_it_claims(self):
        """The prose numbers come from the same reader the tree feeds.

        No expected value appears here. The topology reader refuses unless both
        marketplace manifests and tree discovery agree, so a passing claim
        rests on three sources rather than on somebody's memory.
        """
        topology = discover_topology(ROOT)
        counts = topology.counts()
        exercised = set()
        for item in front_door.maintained_documents(topology):
            if not item.carries(front_door.COUNT_RULE):
                continue
            text = front_door.read_document(ROOT, item.relative)
            display = front_door.rendered(text)
            for marker in front_door.markers(text):
                if marker.kind != "count":
                    continue
                key = marker.attributes["key"]
                exercised.add(key)
                claim, _ = front_door.claim_after(display, marker)
                with self.subTest(document=item.relative, key=key):
                    self.assertIsNotNone(claim)
                    self.assertEqual(
                        front_door.claim_number(claim.group("number")),
                        counts[front_door.COUNT_KEYS[key]],
                    )
        # Every declared key is used somewhere. A key nothing reaches is a
        # quantity the checker knows how to derive and nobody publishes, which
        # is how `members` sat underived while three pages carried it.
        self.assertEqual(exercised, set(front_door.COUNT_KEYS))

    def test_no_count_claim_on_the_maintained_surface_is_unmarked(self):
        topology = discover_topology(ROOT)
        unmarked = []
        for item in front_door.maintained_documents(topology):
            if not item.carries(front_door.COUNT_RULE):
                continue
            text = front_door.read_document(ROOT, item.relative)
            display = front_door.rendered(text)
            spans, _ = front_door.generated_spans(text)
            marked = set()
            for marker in front_door.markers(text):
                if marker.kind not in {"count", "historical"}:
                    continue
                marked.add(front_door.claim_after(display, marker)[1])
            unmarked += [
                (item.relative, claim.group(0))
                for claim in front_door.COUNT_CLAIM_RE.finditer(display)
                if claim.start() not in marked
                and not covered_by_a_region(spans, claim.start())
            ]
        self.assertEqual(unmarked, [])

    def test_no_maintained_page_describes_a_member_against_its_own_ledger(self):
        """The general rule, not the two sentences that provoked it.

        Every page that says what a member's current version does or does not
        do names the `EVOLUTION.md` version it describes, and that version is
        the one the ledger records now. Nothing here names a skill, a version
        or a sentence: a release moves both sides together, and a page that
        stops moving with them is what this case is for.
        """
        topology = discover_topology(ROOT)
        versions = {
            directory.rsplit("/", 1)[-1]: front_door.ledger_version(ROOT, directory)
            for directory in topology.governed
        }
        bound = 0
        for item in front_door.maintained_documents(topology):
            if not item.carries(front_door.STATUS_RULE):
                continue
            text = front_door.read_document(ROOT, item.relative)
            display = front_door.rendered(text)
            spans, _ = front_door.generated_spans(text)
            covered = set()
            for marker in front_door.markers(text):
                if marker.kind != "status":
                    continue
                bound += 1
                end = display.find("\n\n", marker.end)
                region = display[marker.end: len(display) if end < 0 else end]
                covered.update(
                    marker.end + claim.start()
                    for claim in front_door.STATUS_CLAIM_RE.finditer(region)
                )
                with self.subTest(document=item.relative):
                    self.assertEqual(
                        marker.attributes["version"],
                        versions[marker.attributes["skill"]],
                    )
            for claim in front_door.STATUS_CLAIM_RE.finditer(display):
                if covered_by_a_region(spans, claim.start()):
                    continue
                with self.subTest(document=item.relative, claim=claim.group(0)):
                    self.assertIn(claim.start(), covered)
        self.assertTrue(bound, "no maintained page states a member's version status")

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

    def test_every_declared_refusal_has_a_document_that_provokes_it(self):
        self.assertEqual(sorted(PROVOCATIONS), sorted(front_door.REFUSALS))

    def test_every_declared_refusal_is_reachable_from_the_checker(self):
        for code, build in PROVOCATIONS.items():
            with self.subTest(code=code):
                if build is None:
                    with tempfile.TemporaryDirectory() as raw:
                        root = Path(raw)
                        records = plant(root)
                        install(root, records, {})
                        (root / front_door.FRONT_DOOR).unlink()
                        reported = [
                            finding.code for finding in front_door.check(root)[0]
                        ]
                elif isinstance(build, str):
                    reported = specimen_codes(build)
                else:
                    built = build()
                    reported = (
                        document_codes(built)
                        if isinstance(built, dict)
                        else body_codes(built)
                    )
                self.assertIn(code, reported)

    def test_the_refusal_prefix_stays_out_of_the_demonstration_namespace(self):
        """`Dnnn` belongs to the demonstration catalogue, which a parity test counts."""
        for code in front_door.REFUSALS:
            with self.subTest(code=code):
                self.assertNotRegex(code, r"^D[0-9]{3}$")
                self.assertNotIn(code, demonstrations.REFUSALS)


if __name__ == "__main__":
    unittest.main()
